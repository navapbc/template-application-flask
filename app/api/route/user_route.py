from typing import Any

import flask

import api.logging as logging
import api.route.handler.user_handler as user_handler
import api.route.response as response_util
from api.route.api_context import api_context_manager

logger = logging.get_logger(__name__)


# Create user
def user_post() -> flask.Response:
    """
    POST /v1/user
    """
    logger.info("POST /v1/user")

    with api_context_manager() as api_context:

        response = user_handler.create_user(api_context)

        logger.info(
            "Successfully inserted user",
            extra=get_user_log_params(response),
        )
        return response_util.success_response(
            message="Success", data=response.dict(), status_code=201
        ).to_api_response()


# Update user
def user_patch(user_id: str) -> flask.Response:
    """
    PATCH /v1/user/:user_id
    """
    logger.info("PATCH /v1/user/:user_id")

    with api_context_manager() as api_context:
        response = user_handler.patch_user(user_id, api_context)

        logger.info(
            "Successfully patched user",
            extra=get_user_log_params(response),
        )

        return response_util.success_response(
            message="Success", data=response.dict(), status_code=200
        ).to_api_response()


# Get user
def user_get(user_id: str) -> flask.Response:
    """
    GET /v1/user/:user_id
    """
    logger.info("GET /v1/user/:user_id")

    with api_context_manager() as api_context:
        response = user_handler.get_user(user_id, api_context)

        logger.info(
            "Successfully fetched user",
            extra=get_user_log_params(response),
        )

        return response_util.success_response(
            message="Success", data=response.dict(), status_code=200
        ).to_api_response()


def get_user_log_params(user_response: user_handler.UserResponse) -> dict[str, Any]:
    return {"user_id": user_response.user_id}
