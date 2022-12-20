import uuid
from datetime import date
from typing import Optional
from uuid import uuid4

import api.logging
from api.db.models.user_models import Role, RoleType, User
from api.route.api_context import ApiContext
from api.route.request import BaseRequestModel
from api.route.route_utils import get_or_404

logger = api.logging.get_logger(__name__)


class RoleParams(BaseRequestModel):
    type: RoleType


class UserParams(BaseRequestModel):
    id: Optional[uuid.UUID]
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    date_of_birth: date
    is_active: bool
    roles: Optional[list[RoleParams]]


class UserPatchParams(BaseRequestModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    date_of_birth: Optional[date]
    is_active: Optional[bool]
    roles: Optional[list[RoleParams]]


class UserResponse(UserParams):
    pass


def create_user(user_data: dict, api_context: ApiContext) -> User:

    user = User(**user_data)
    user.id = uuid4()

    if user.roles is not None:
        for role in user.roles:
            role.user_id = user.id

    api_context.db_session.add(user)
    api_context.db_session.flush()
    return user


def patch_user(user_id: str, patch_data: dict, api_context: ApiContext) -> User:
    user = get_or_404(api_context.db_session, User, user_id)

    for key, value in patch_data.items():

        if key == "roles":
            handle_role_patch(user, value, api_context)
            continue

        setattr(user, key, value)

    # Flush the changes to the DB and then
    # refresh to get the roles updated on
    # the user object that may have been changed
    api_context.db_session.flush()
    api_context.db_session.refresh(user)

    return user


def get_user(user_id: str, api_context: ApiContext) -> User:
    return get_or_404(api_context.db_session, User, user_id)


def handle_role_patch(
    user: User, request_roles: Optional[list[Role]], api_context: ApiContext
) -> None:
    # Because roles are a list, we need to handle them slightly different.
    # There are two scenarios possible:
    # 1. The roles match -> do nothing
    # 2. The roles don't match -> add/remove from the DB roles to make them match
    #
    # Matching is based purely off the role description at the moment
    # In a more thorough system, it might make sense to make a patch endpoint
    # that explicitly adds or removes a single role for a user at a time.

    # Shouldn't be called if None, but makes mypy happy
    if request_roles is None:
        return

    # We'll work with just the role description strings to avoid
    # comparing nested objects and values. As roles are unique in the
    # DB per user, any deduplicating this does is fine.
    if user.roles is not None:
        current_role_types = set([role.type for role in user.roles])
    else:
        current_role_types = set()

    request_role_types = set([role.type for role in request_roles])

    # If they match, do nothing
    if set(current_role_types) == set(request_role_types):
        return

    # Figure out which roles need to be deleted and added
    roles_to_delete = current_role_types - request_role_types
    roles_to_add = request_role_types - current_role_types

    # Go through existing roles and delete the ones that are no longer needed
    if user.roles:
        for current_user_role in user.roles:
            if current_user_role.type in roles_to_delete:
                api_context.db_session.delete(current_user_role)

    # Add any new roles
    for role_type in roles_to_add:
        user_role = Role(user_id=user.id, type=role_type)
        api_context.db_session.add(user_role)
