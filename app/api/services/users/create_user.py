from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from pydantic import UUID4

import api.logging
from api.db.models.user_models import RoleEnum, User, UserRole
from api.route.api_context import ApiContext
from api.route.request import BaseRequestModel

logger = api.logging.get_logger(__name__)


class RoleParams(BaseRequestModel):
    role_description: RoleEnum
    created_at: Optional[datetime]


class UserParams(BaseRequestModel):
    user_id: Optional[UUID4]
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


def create_user(api_context: ApiContext) -> UserResponse:
    request = UserParams.parse_obj(api_context.request_body)

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

    return UserResponse.from_orm(user)
