import bisect
import uuid
from operator import attrgetter

from fastapi import HTTPException
from sqlalchemy import orm

from src.adapters.db import Session
from src.api.users.user_schemas import RoleModel, UserModelPatch
from src.db.models.user_models import Role, User


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
def patch_user(
    db_session: Session,
    user_id: uuid.UUID,
    patch_user_params: UserModelPatch,
) -> User:

    with db_session.begin():
        # TODO: move this to service and/or persistence layer
        user = db_session.get(User, user_id, options=[orm.selectinload(User.roles)])

        if user is None:
            # TODO move HTTP related logic out of service layer to controller layer and just return None from here
            # https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053754975
            raise HTTPException(status_code=404, detail=f"Could not find user with ID {user_id}")

        for key, value in patch_user_params.model_dump(exclude_unset=True).items():
            if key == "roles":
                _handle_role_patch(db_session, user, patch_user_params.roles)
                continue

            setattr(user, key, value)
    return user


def _handle_role_patch(db_session: Session, user: User, request_roles: list[RoleModel]) -> None:

    current_role_types = set([role.type for role in user.roles])
    request_role_types = set([role.type for role in request_roles])

    roles_to_delete = [role for role in user.roles if role.type not in request_role_types]

    roles_to_add = [
        Role(user_id=user.id, type=role_type)
        for role_type in request_role_types
        if role_type not in current_role_types
    ]

    # First delete any roles that are no longer in the request and remove the role
    # from the user.roles array
    for role in roles_to_delete:
        user.roles.remove(role)
        db_session.delete(role)

    # Then add any roles that are in the request but not in the user.roles array,
    # keeping the roles array sorted by role type
    for role in roles_to_add:
        bisect.insort(user.roles, role, key=attrgetter("type"))
