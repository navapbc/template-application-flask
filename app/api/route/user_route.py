from typing import Any

import flask
from apiflask import APIBlueprint

import api.logging as logging
import api.route.handler.user_handler as user_handler
import api.route.response as response_util
from api.auth.api_key_auth import api_key_auth
from api.route.api_context import api_context_manager
from api.route.models.user_api_models import UserIn, UserOut, UserPatchParams

logger = logging.get_logger(__name__)


user_blueprint = APIBlueprint("user", __name__, tag="User")


@user_blueprint.post("/v1/user")
@user_blueprint.input(UserIn.Schema)
@user_blueprint.output(UserOut.Schema)
@user_blueprint.auth_required(api_key_auth)
def user_post(user: UserIn) -> flask.Response:
    """
    POST /v1/user
    """
    logger.info("POST /v1/user")

    with api_context_manager() as api_context:

        response = user_handler.create_user(user, api_context)

        logger.info(
            "Successfully inserted user",
            extra=get_user_log_params(response),
        )
        return response_util.success_response(
            message="Success", data=response, status_code=201
        ).to_api_response()


@user_blueprint.patch("/v1/user/<uuid:user_id>")
@user_blueprint.input(UserPatchParams.Schema)
@user_blueprint.output(UserOut.Schema)
@user_blueprint.auth_required(api_key_auth)
def user_patch(user_id: str, user_patch_params: UserPatchParams) -> flask.Response:
    logger.info("PATCH /v1/user/:user_id")

    with api_context_manager() as api_context:
        response = user_handler.patch_user(user_id, user_patch_params, api_context)

        logger.info(
            "Successfully patched user",
            extra=get_user_log_params(response),
        )

        return response_util.success_response(
            message="Success", data=response, status_code=200
        ).to_api_response()


@user_blueprint.get("/v1/user/<uuid:user_id>")
@user_blueprint.output(UserOut.Schema)
@user_blueprint.auth_required(api_key_auth)
def user_get(user_id: str) -> flask.Response:
    logger.info("GET /v1/user/:user_id")

    with api_context_manager() as api_context:
        response = user_handler.get_user(user_id, api_context)

        logger.info(
            "Successfully fetched user",
            extra=get_user_log_params(response),
        )

        return response_util.success_response(
            message="Success", data=response, status_code=200
        ).to_api_response()


def get_user_log_params(user_response: UserOut) -> dict[str, Any]:
    return {"user_id": user_response.user_id}
