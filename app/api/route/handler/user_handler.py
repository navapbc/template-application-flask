from datetime import date
from typing import Optional
from uuid import uuid4

from pydantic import UUID4

import api.logging
from api.db.models.user_models import Role, User, UserRole
from api.route.api_context import ApiContext
from api.route.request import BaseRequestModel

logger = api.logging.get_logger(__name__)


class RoleParams(BaseRequestModel):
    role_id: Optional[int]
    role_description: str


class UserParams(BaseRequestModel):
    user_id: Optional[UUID4]
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    date_of_birth: date
    is_active: bool
    roles: Optional[list[RoleParams]]


class UserResponse(UserParams):
    pass


def create_user(api_context: ApiContext) -> UserResponse:
    request = UserParams.parse_obj(api_context.request_body)

    roles = None
    if request.roles is not None:
        roles = []
        for request_role in request.roles:
            role = Role.get_instance(api_context.db_session, description=request_role.role_description)
            roles.append(role)

    user = User(
        user_id=uuid4(),
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        is_active=request.is_active,
        roles=roles
    )
    api_context.db_session.add(user)


    return UserResponse.from_orm(user)


def patch_user(user_id: str, api_context: ApiContext) -> UserResponse:
    pass
