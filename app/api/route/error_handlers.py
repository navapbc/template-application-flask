from typing import Tuple

from apiflask import APIFlask
from apiflask.exceptions import HTTPError, ResponseHeaderType

import api.logging

logger = api.logging.get_logger(__name__)


def add_error_handlers_to_app(app: APIFlask) -> None:
    # See: https://apiflask.com/error-handling/ for additional configuration options

    @app.error_processor
    def error_formatter(error: HTTPError) -> Tuple[dict, int, ResponseHeaderType]:
        # This method leaves errors entirely unmodified
        # and exists as a template for if you wish to modify
        # the format of error responses.
        # Note that if you change this format, you'll
        # also need to specify the error schema so
        # OpenAPI will provide the correct format:
        # https://apiflask.com/error-handling/#update-the-openapi-schema-of-error-responses
        return (
            {"status_code": error.status_code, "message": error.message, "detail": error.detail},
            error.status_code,
            error.headers,
        )
