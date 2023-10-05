import logging
import typing
import uuid
from typing import Any

import fastapi.exception_handlers
from fastapi import APIRouter

import src.adapters.db as db
import src.adapters.db.fastapi_db as fastapi_db
import src.api.users.user_schemas as user_schemas
import src.services.users as user_service
from src.auth.api_key_auth import verify_api_key
from src.db.models.user_models import User

logger = logging.getLogger(__name__)


user_router = APIRouter(tags=["user"], dependencies=[fastapi.Depends(verify_api_key)])


@user_router.post("/v1/users", status_code=201, response_model=user_schemas.UserModelOut)
def user_post(
    db_session: typing.Annotated[db.Session, fastapi.Depends(fastapi_db.DbSessionDependency())],
    user_model: user_schemas.UserModel,
) -> User:
    """
    POST /v1/users
    """
    logger.info(user_model)
    user = user_service.create_user(db_session, user_model)
    logger.info("Successfully inserted user", extra=get_user_log_params(user))
    return user


@user_router.patch("/v1/users/{user_id}", response_model=user_schemas.UserModelOut)
def user_patch(
    db_session: typing.Annotated[db.Session, fastapi.Depends(fastapi_db.DbSessionDependency())],
    user_id: uuid.UUID,
    patch_user_params: user_schemas.UserModelPatch,
) -> User:
    user = user_service.patch_user(db_session, user_id, patch_user_params)
    logger.info("Successfully patched user", extra=get_user_log_params(user))
    return user


@user_router.get("/v1/users/{user_id}", response_model=user_schemas.UserModelOut)
def user_get(
    db_session: typing.Annotated[db.Session, fastapi.Depends(fastapi_db.DbSessionDependency())],
    user_id: uuid.UUID,
) -> User:
    user = user_service.get_user(db_session, user_id)
    logger.info("Successfully fetched user", extra=get_user_log_params(user))
    return user


def get_user_log_params(user: User) -> dict[str, Any]:
    return {"user.id": user.id}
