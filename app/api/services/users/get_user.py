from datetime import date, datetime
from typing import Optional

from pydantic import UUID4

import api.logging
from api.db.models.user_models import RoleEnum, User
from api.route.api_context import ApiContext
from api.route.request import BaseRequestModel
from api.route.route_utils import get_or_404

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


def get_user(user_id: str, api_context: ApiContext) -> UserResponse:
    user = get_or_404(api_context.db_session, User, user_id)

    return UserResponse.from_orm(user)
