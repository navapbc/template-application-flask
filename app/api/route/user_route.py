from typing import Any

from apiflask import APIBlueprint

import api.logging as logging
import api.route.handler.user_handler as user_handler
from api.auth.api_key_auth import api_key_auth
from api.db.models.user_models import User
from api.route import response
from api.route.api_context import api_context_manager
from api.route.schemas import user_schemas

logger = logging.get_logger(__name__)


user_blueprint = APIBlueprint("user", __name__, tag="User")


@user_blueprint.post("/v1/user")
@user_blueprint.input(user_schemas.UserSchema)
@user_blueprint.output(user_schemas.UserSchema, status_code=201)
@user_blueprint.auth_required(api_key_auth)
def user_post(user_input: dict) -> dict:
    """
    POST /v1/user
    """
    logger.info("POST /v1/user")

    with api_context_manager() as api_context:

        user = user_handler.create_user(user_input, api_context)

        logger.info(
            "Successfully inserted user",
            extra=get_user_log_params(user),
        )

        return response.ApiResponse(message="Success", data=user).asdict()


@user_blueprint.patch("/v1/user/<uuid:user_id>")
# Allow partial updates. partial=true means requests that are missing
# required fields will not be rejected.
# https://marshmallow.readthedocs.io/en/stable/quickstart.html#partial-loading
@user_blueprint.input(user_schemas.UserSchema(partial=True))
@user_blueprint.output(user_schemas.UserSchema)
@user_blueprint.auth_required(api_key_auth)
def user_patch(user_id: str, user_patch_params: dict) -> dict:
    logger.info("PATCH /v1/user/:user_id")

    with api_context_manager() as api_context:
        user = user_handler.patch_user(user_id, user_patch_params, api_context)

        logger.info(
            "Successfully patched user",
            extra=get_user_log_params(user),
        )

        return response.ApiResponse(message="Success", data=user).asdict()


@user_blueprint.get("/v1/user/<uuid:user_id>")
@user_blueprint.output(user_schemas.UserSchema)
@user_blueprint.auth_required(api_key_auth)
def user_get(user_id: str) -> dict:
    logger.info("GET /v1/user/:user_id")

    with api_context_manager() as api_context:
        user = user_handler.get_user(user_id, api_context)

        logger.info(
            "Successfully fetched user",
            extra=get_user_log_params(user),
        )

        return response.ApiResponse(message="Success", data=user).asdict()


def get_user_log_params(user_response: User) -> dict[str, Any]:
    return {"user_id": user_response.id}
