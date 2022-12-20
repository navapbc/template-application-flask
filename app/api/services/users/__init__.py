from datetime import date
from typing import Optional

from pydantic import UUID4

import api.logging
from api.db.models.user_models import RoleEnum
from api.route.request import BaseRequestModel

from .create_user import create_user
from .get_user import get_user
from .patch_user import patch_user

logger = api.logging.get_logger(__name__)


class RoleParams(BaseRequestModel):
    type: RoleType


class UserParams(BaseRequestModel):
    id: Optional[UUID4]
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
