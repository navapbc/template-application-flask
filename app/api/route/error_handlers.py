import re
import sys
from types import TracebackType
from typing import Callable, Optional, Tuple

import connexion
import pydantic
from flask import Response
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)

import api.logging
from api.route.response import ValidationErrorDetail, ValidationException, error_response

logger = api.logging.get_logger(__name__)


def add_error_handlers_to_app(connexion_app: connexion.FlaskApp) -> None:
    connexion_app.add_error_handler(ValidationException, validation_request_handler)
    connexion_app.add_error_handler(pydantic.ValidationError, handle_pydantic_validation_error)

    # These are all handled with the same generic exception handler to make them uniform in structure.
    connexion_app.add_error_handler(NotFound, http_exception_handler)
    connexion_app.add_error_handler(HTTPException, http_exception_handler)
    connexion_app.add_error_handler(Forbidden, http_exception_handler)
    connexion_app.add_error_handler(Unauthorized, http_exception_handler)

    # Override the default internal server error handler to prevent Flask
    # from using logging.error with a generic message. We want to log
    # the original exception.
    #
    # We handle all 500s here but only expect InternalServerError instances,
    # as indicated by the documentation. Calling out InternalServerError explicitly
    # here would not override the default internal server error handler.
    #
    connexion_app.add_error_handler(500, internal_server_error_handler)


def http_exception_handler(http_exception: HTTPException) -> Response:
    return error_response(
        status_code=http_exception, message=str(http_exception.description), errors=[]
    ).to_api_response()


def internal_server_error_handler(error: InternalServerError) -> Response:
    # Use the original exception if it exists.
    exception = error.original_exception or error

    logger.exception(str(exception), extra={"error.class": type(exception).__name__})

    return http_exception_handler(error)


def validation_request_handler(validation_exception: ValidationException) -> Response:
    for error in validation_exception.errors:
        log_validation_error(validation_exception, error, is_unexpected_validation_error)

    return error_response(
        status_code=BadRequest,
        message=validation_exception.message,
        errors=validation_exception.errors,
        data=validation_exception.data,
    ).to_api_response()


def handle_pydantic_validation_error(exception: pydantic.ValidationError) -> Response:
    return validation_request_handler(convert_pydantic_error_to_validation_exception(exception))


# Some pydantic errors aren't of a format we like
pydantic_error_type_map = {"value_error.date": "date"}


def convert_pydantic_error_to_validation_exception(
    exception: pydantic.ValidationError,
) -> ValidationException:
    errors = []

    for e in exception.errors():
        err_type = e["type"]
        if err_type in pydantic_error_type_map:
            err_type = pydantic_error_type_map[err_type]

        err_field = e["loc"][0]
        err_message = e["msg"]

        errors.append(
            ValidationErrorDetail(
                type=err_type,
                message=f'Error in field: "{err_field}". {err_message.capitalize()}.',
                rule=None,
                field=".".join(str(loc) for loc in e["loc"]),
            )
        )

    return ValidationException(errors=errors, message="Request Validation Error", data={})


UNEXPECTED_ERROR_TYPES = {"enum", "type"}


def is_unexpected_validation_error(error: ValidationErrorDetail) -> bool:
    return (
        error.type in UNEXPECTED_ERROR_TYPES
        or error.type.startswith("type_error")
        or error.type.startswith("value_error")
    )


def log_validation_error(
    validation_exception: ValidationException,
    error: ValidationErrorDetail,
    unexpected_error_check_func: Optional[Callable[[ValidationErrorDetail], bool]] = None,
    only_warn: bool = False,
) -> None:
    # Create a readable message for the individual error.
    # Do not use the error's actual message since it may include PII.
    #
    # Note that the field is modified in the message so array-based fields can be aggregated, e.g.
    #
    #   error.field: data.0.absence_periods.12.reason_qualifier_two
    #   aggregated_field: data.<NUM>.absence_periods.<NUM>.reason_qualifier_two
    #
    aggregated_field = error.field

    if aggregated_field:
        aggregated_field = re.sub(r"\.\d+\.", ".<NUM>.", aggregated_field)

    message = "%s (field: %s, type: %s, rule: %s)" % (
        validation_exception.message,
        aggregated_field,
        error.type,
        error.rule,
    )

    log_attributes = {
        "error.class": "ValidationException",
        "error.type": error.type,
        "error.rule": error.rule,
        "error.field": error.field,
        "error.value": error.value,
    }

    if unexpected_error_check_func and not unexpected_error_check_func(error):
        logger.info(message, extra=log_attributes)
    else:
        # Log explicit errors in the case of unexpected validation errors.
        info = sys.exc_info()
        info_with_readable_msg: BaseException | Tuple[type, BaseException, Optional[TracebackType]]

        if info[0] is None:
            exc = Exception(message)
            info_with_readable_msg = (type(exc), exc, exc.__traceback__)
        else:
            info_with_readable_msg = (info[0], Exception(message), info[2])

        if only_warn:
            logger.warning(message, extra=log_attributes, exc_info=info_with_readable_msg)
        else:
            logger.error(message, extra=log_attributes, exc_info=info_with_readable_msg)
