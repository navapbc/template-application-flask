from datetime import date, datetime
from typing import Optional

from pydantic import UUID4

from api.db.models.user_models import RoleEnum
from api.route.request import BaseRequestModel


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
