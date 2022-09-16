import logging  # noqa: B1
import pathlib

import connexion
import pytest
from pydantic import Field, ValidationError

from api.route.connexion_validators import get_custom_validator_map
from api.route.error_handlers import (
    add_error_handlers_to_app,
    convert_pydantic_error_to_validation_exception,
    is_unexpected_validation_error,
    log_validation_error,
)
from api.route.request import BaseRequestModel
from api.route.response import (
    ValidationErrorDetail,
    ValidationException,
    error_response,
    success_response,
)

TEST_FOLDER = pathlib.Path(__file__).parent
INVALID_USER = {"first_name": 123, "interests": ["sports", "activity", "sports"]}
VALID_USER = {"first_name": "Jane", "last_name": "Smith", "interests": ["sports", "sketching"]}
MISSING_DATA_USER = {"first_name": "Foo"}


def post_user():
    """handler for test api (see 'test.yml' file in this directory)"""
    return success_response(message="Success", data=VALID_USER).to_api_response()


def get_user():
    """handler for test api (see 'test.yml' file in this directory)"""
    return error_response(message="Error", data=MISSING_DATA_USER).to_api_response()


def validate_invalid_response(response, message, field_prefix=""):
    assert response["status_code"] == 400
    assert response["message"] == message
    assert len(response["errors"]) == 4

    def filter_errors_by_field_value(field_name, value):
        return list(filter(lambda e: e[field_name] == value, response["errors"]))

    first_name_errors = filter_errors_by_field_value("field", f"{field_prefix}first_name")
    assert len(first_name_errors) == 1
    assert first_name_errors[0]["type"] == "type"
    assert first_name_errors[0]["rule"] == "string"

    last_name_errors = filter_errors_by_field_value("type", "required")
    assert len(last_name_errors) == 1
    assert last_name_errors[0]["rule"] == ["first_name", "last_name"]

    interests_errors = filter_errors_by_field_value("field", f"{field_prefix}interests")
    assert len(interests_errors) == 2
    assert interests_errors[0]["type"] == "maxItems"
    assert interests_errors[0]["rule"] == 2
    assert interests_errors[1]["type"] == "uniqueItems"
    assert interests_errors[1]["rule"]


# validate end to end
def test_request_response_validation():
    spec_file_path = TEST_FOLDER / "test_openapi.yml"

    validator_map = get_custom_validator_map()

    flask_app = connexion.FlaskApp("Test API")
    flask_app.add_api(
        spec_file_path, validator_map=validator_map, strict_validation=True, validate_responses=True
    )

    add_error_handlers_to_app(flask_app)

    client = flask_app.app.test_client()

    request_validation_error_response = client.post("/user", json=INVALID_USER).get_json()
    validate_invalid_response(request_validation_error_response, "Request Validation Error")

    request_validation_error_response_no_body = client.post("/user").get_json()

    assert request_validation_error_response_no_body.get("message") == "Request Validation Error"
    assert (
        request_validation_error_response_no_body.get("errors")[0]["message"]
        == "Missing request body"
    )

    success_response = client.post("/user", json=VALID_USER).get_json()

    request_validation_error_response_get_warnings = client.get(
        "/user", json=MISSING_DATA_USER
    ).get_json()
    assert request_validation_error_response_get_warnings.get("warnings", None) is None

    request_validation_error_response_no_warnings = client.post(
        "/user", json=MISSING_DATA_USER
    ).get_json()
    assert request_validation_error_response_no_warnings.get("warnings", None) is None

    assert success_response["message"] == "Success"
    assert success_response["data"] is not None
    assert success_response.get("data") is not None


def test_log_validation_error_aggregated_field(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    exception = ValidationException(
        [
            ValidationErrorDetail(
                rule="conditional",
                type="value_error",
                field="data.5.reasons.12.reason_qualifier",
                message="something something",
            )
        ],
        "Response Validation Error",
        {},
    )

    log_validation_error(exception, exception.errors[0])

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "log_validation_error",
            "ERROR",
            "Response Validation Error (field: data.<NUM>.reasons.<NUM>.reason_qualifier, type: value_error, rule: conditional)",
        )
    ]


def test_log_validation_error_unexpected_exception_handling(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    unexpected_exception = ValidationErrorDetail(
        rule="conditional",
        type="value_error",
        field="cents",
        message="something that might be PII",
    )

    expected_exception = ValidationErrorDetail(
        rule="anything", type="format", field="anything", message="something that might be PII 2"
    )

    errors = [unexpected_exception, expected_exception, unexpected_exception, expected_exception]

    exception = ValidationException(errors, "Request Validation Exception", {})

    for error in exception.errors:
        log_validation_error(exception, error, is_unexpected_validation_error)

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "log_validation_error",
            "ERROR",
            "Request Validation Exception (field: cents, type: value_error, rule: conditional)",
        ),
        (
            "log_validation_error",
            "INFO",
            "Request Validation Exception (field: anything, type: format, rule: anything)",
        ),
        (
            "log_validation_error",
            "ERROR",
            "Request Validation Exception (field: cents, type: value_error, rule: conditional)",
        ),
        (
            "log_validation_error",
            "INFO",
            "Request Validation Exception (field: anything, type: format, rule: anything)",
        ),
    ]


def test_validation_exceptions_logged_as_warnings_when_only_warn_is_true(caplog):
    caplog.set_level(logging.INFO)  # noqa: B1

    unexpected_exception = ValidationErrorDetail(
        rule="conditional",
        type="value_error",
        field="cents",
        message="something that might be PII",
    )
    errors = [unexpected_exception]
    exception = ValidationException(errors, "Response Validation Error", {})

    for error in exception.errors:
        # only_warn is set to True
        log_validation_error(exception, error, is_unexpected_validation_error, True)

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        (
            "log_validation_error",
            "WARNING",
            "Response Validation Error (field: cents, type: value_error, rule: conditional)",
        ),
    ]


class ExamplePydanticModel(BaseRequestModel):
    first_field: str = Field(max_length=5)
    second_field: str = Field(max_length=5)


class TestConvertPydanticErrorToValidationException:
    @pytest.fixture
    def validation_error_first_name(self):
        try:
            ExamplePydanticModel(first_field="abcdef", second_field="abcde")
        except ValidationError as e:
            return e

    @pytest.fixture
    def validation_error_multiple_issues(self):
        try:
            ExamplePydanticModel(first_field="abcdef", second_field="abcdef")
        except ValidationError as e:
            return e

    def test_validation_error_name_too_long(self, validation_error_first_name):
        validation_exception = convert_pydantic_error_to_validation_exception(
            validation_error_first_name
        )
        assert validation_exception is not None

        errors = validation_exception.errors
        error_detail = next((e for e in errors if e.field == "first_field"), None)

        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "first_field". Ensure this value has at most 5 characters.'
        )

    def test_validation_error_multiple_issues(self, validation_error_multiple_issues):
        validation_exception = convert_pydantic_error_to_validation_exception(
            validation_error_multiple_issues
        )
        assert validation_exception is not None

        errors = validation_exception.errors

        error_detail = next((e for e in errors if e.field == "first_field"), None)
        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "first_field". Ensure this value has at most 5 characters.'
        )

        error_detail = next((e for e in errors if e.field == "second_field"), None)
        assert error_detail is not None
        assert (
            error_detail.message
            == 'Error in field: "second_field". Ensure this value has at most 5 characters.'
        )
