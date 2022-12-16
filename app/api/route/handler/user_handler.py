from typing import Optional
from uuid import uuid4

import api.logging
from api.db.models.user_models import User, UserRole
from api.route.api_context import ApiContext
from api.route.models.user_api_models import Role, UserIn, UserOut, UserPatchParams
from api.route.route_utils import get_or_404

logger = api.logging.get_logger(__name__)


def create_user(request: UserIn, api_context: ApiContext) -> UserOut:

    user = User(
        user_id=uuid4(),
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        is_active=request.is_active,
    )
    api_context.db_session.add(user)

    if request.roles is not None:
        user_roles = []
        for request_role in request.roles:
            user_roles.append(
                UserRole(user_id=user.user_id, role_description=request_role.role_description)
            )

        user.roles = user_roles

    api_context.db_session.flush()
    return UserOut(**UserOut.Schema().dump(user))


def patch_user(user_id: str, request: UserPatchParams, api_context: ApiContext) -> UserOut:
    user = get_or_404(api_context.db_session, User, user_id)

    for key, value in request.get_set_params(api_context):
        # Unfortunately there isn't a great way of determining
        # which values were explicitly set in the request other
        # than to look at the raw request JSON. Because the objects
        # get converted to dataclasses, all the values are "set" and
        # dataclasses don't keep track of the parameters
        if key not in api_context.request_body:
            continue

        if key == "roles":
            handle_role_patch(user, value, api_context)
            continue

        setattr(user, key, value)

    # Flush the changes to the DB and then
    # refresh to get the roles updated on
    # the user object that may have been changed
    api_context.db_session.flush()
    api_context.db_session.refresh(user)

    return UserOut(**UserOut.Schema().dump(user))


def get_user(user_id: str, api_context: ApiContext) -> UserOut:
    user = get_or_404(api_context.db_session, User, user_id)

    return UserOut(**UserOut.Schema().dump(user))


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

    if request_roles is None:
        return

    # We'll work with just the role description strings to avoid
    # comparing nested objects and values. As roles are unique in the
    # DB per user, any deduplicating this does is fine.
    if user.roles is not None:
        current_role_descriptions = set([role.role_description for role in user.roles])
    else:
        current_role_descriptions = set()

    request_role_descriptions = set([role.role_description for role in request_roles])

    # If they match, do nothing
    if set(current_role_descriptions) == set(request_role_descriptions):
        return

    # Figure out which roles need to be deleted and added
    roles_to_delete = current_role_descriptions - request_role_descriptions
    roles_to_add = request_role_descriptions - current_role_descriptions

    # Go through existing roles and delete the ones that are no longer needed
    if user.roles:
        for current_user_role in user.roles:
            if current_user_role.role_description in roles_to_delete:
                api_context.db_session.delete(current_user_role)

    # Add any new roles
    for role_description in roles_to_add:
        user_role = UserRole(user_id=user.user_id, role_description=role_description)
        api_context.db_session.add(user_role)
