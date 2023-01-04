import dataclasses
from datetime import date
from typing import Optional

import apiflask
from sqlalchemy import orm

from api.db.models.user_models import Role, User
from api.route.api_context import ApiContext
from api.services.core.patch_params import Missing, fields_to_patch, missing
from api.services.users.create_user import RoleParams


@dataclasses.dataclass
class PatchUserParams:
    first_name: str | Missing = missing
    middle_name: str | Missing = missing
    last_name: str | Missing = missing
    phone_number: str | Missing = missing
    date_of_birth: date | Missing = missing
    is_active: bool | Missing = missing
    roles: list[RoleParams] | Missing = missing


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
# TODO: Use classes / objects as inputs to service methods
# https://github.com/navapbc/template-application-flask/issues/52
def patch_user(user_id: str, patch_user_params: PatchUserParams, api_context: ApiContext) -> User:
    # TODO: move this to service and/or persistence layer
    user = api_context.db_session.query(User).options(orm.selectinload(User.roles)).get(user_id)

    if user is None:
        # TODO move HTTP related logic out of service layer to controller layer and just return None from here
        # https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053754975
        raise apiflask.HTTPError(404, message=f"Could not find user with ID {user_id}")

    for key, value in fields_to_patch(patch_user_params):
        if key == "roles":
            _handle_role_patch(user, value, api_context)
            continue

        setattr(user, key, value)

    # Flush the changes to the DB and then
    # refresh to get the roles updated on
    # the user object that may have been changed
    api_context.db_session.flush()
    api_context.db_session.refresh(user)

    return user


def _handle_role_patch(
    user: User, request_roles: Optional[list[RoleParams]], api_context: ApiContext
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
        # TODO: instead, add to user.roles directly without user_id=user.id and let SQLAlchemy handle the foreign key assignment
        user_role = Role(user_id=user.id, type=role_type)
        api_context.db_session.add(user_role)
