import enum
from dataclasses import field

from apiflask.validators import OneOf, Regexp

from api.route.schemas.param_schema import ParamFieldConfig


def base_metadata():
    return {"metadata": {"metadata": {}}}


def validate_metadata_matches(actual: dict, expected: dict):
    actual_metadata = actual["metadata"]
    expected_metadata = expected["metadata"]

    assert actual_metadata.keys() == expected_metadata.keys()

    if "validate" in actual_metadata:
        # Validators are class objects, we'll be slightly
        # roundabout for testing those.
        for i, actual_validator in enumerate(actual_metadata["validate"]):
            expected_validator = expected_metadata["validate"][i]

            if isinstance(actual_validator, Regexp):
                assert isinstance(expected_validator, Regexp)
                assert actual_validator.regex == expected_validator.regex

            if isinstance(actual_validator, OneOf):
                assert isinstance(expected_validator, OneOf)
                assert actual_validator.choices == expected_validator.choices

    actual_inner_metadata = actual_metadata["metadata"]
    expected_inner_metadata = expected_metadata["metadata"]

    assert actual_inner_metadata.get("description") == expected_inner_metadata.get("description")
    assert actual_inner_metadata.get("example") == expected_inner_metadata.get("example")

    # Validate field can be called with these params
    field(**actual)


def test_build_text_fields():
    # Note we call _build() as we're testing
    # the parameters passed into the field() method

    # Setting no params is fine and just gets you
    # a fairly empty object that is valid to call field with
    params = ParamFieldConfig()._build()
    validate_metadata_matches(params, base_metadata())

    # Add an example and description override
    params = ParamFieldConfig()._build(example="example text", description="description text")
    expected_params = base_metadata()
    expected_params["metadata"]["metadata"]["example"] = "example text"
    expected_params["metadata"]["metadata"]["description"] = "description text"
    validate_metadata_matches(params, expected_params)

    # Add example and description as constructor params
    params = ParamFieldConfig(example="example text", description="description text")._build()
    validate_metadata_matches(params, expected_params)

    # Add both, override is used
    params = ParamFieldConfig(example="not used", description="not used")._build(
        example="example text", description="description text"
    )
    validate_metadata_matches(params, expected_params)


def test_build_regex():
    params = ParamFieldConfig(regex=r"$.")._build()
    expected_params = base_metadata()
    expected_params["metadata"]["validate"] = [Regexp(regex=r"$.")]
    validate_metadata_matches(params, expected_params)


def test_build_allowed_values_list():
    values = ["val1", "val2", "val3"]
    params = ParamFieldConfig(allowed_values=values)._build()
    expected_params = base_metadata()
    expected_params["metadata"]["validate"] = [OneOf(values)]
    validate_metadata_matches(params, expected_params)


def test_build_allowed_values_enum():
    # Verify that an enum works like the list above
    class TestEnum(enum.Enum):
        VALUE1 = "val1"
        VALUE2 = "val2"
        VALUE3 = "val3"

    params = ParamFieldConfig(allowed_values=TestEnum)._build()
    expected_params = base_metadata()
    expected_params["metadata"]["validate"] = [OneOf(["val1", "val2", "val3"])]
    validate_metadata_matches(params, expected_params)
