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
            extra={"user_id": response.user_id},
        )
        return response_util.success_response(
            message="Success", data=response.dict(), status_code=201
        ).to_api_response()


# Update user
def user_patch() -> flask.Response:
    pass


# Get user
def user_get() -> flask.Response:
    pass
