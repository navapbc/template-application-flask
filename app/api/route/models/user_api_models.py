import uuid
from datetime import date, datetime
from typing import Optional

from marshmallow_dataclass import dataclass as marshmallow_dataclass

from api.db.models.user_models import RoleEnum
from api.route.models.base_api_model import BaseApiModel
from api.route.models.param_schema import ParamFieldConfig, ParamSchema
from api.route.request import BaseRequestModel

##############
# Role Models
##############


@marshmallow_dataclass
class RoleBase(BaseApiModel):
    role_description: str = ParamFieldConfig(
        allowed_values=RoleEnum, description="The name of the role"
    ).build()


@marshmallow_dataclass
class RoleOut(RoleBase):
    created_at: Optional[datetime] = ParamSchema.datetime.build()
    updated_at: Optional[datetime] = ParamSchema.datetime.build()


##############
# User Models
##############


@marshmallow_dataclass
class UserBase(BaseApiModel):
    first_name: str = ParamSchema.first_name.build()
    middle_name: Optional[str] = ParamSchema.middle_name.build()
    last_name: str = ParamSchema.last_name.build()
    phone_number: str = ParamSchema.phone_number.build()
    date_of_birth: date = ParamSchema.date.build(description="The users date of birth")
    is_active: bool = ParamSchema.bool.build(description="Whether the user is active")


@marshmallow_dataclass
class UserIn(UserBase):
    roles: list[RoleBase]


@marshmallow_dataclass
class UserOut(UserBase):
    user_id: uuid.UUID = ParamSchema.uuid.build()

    roles: list[RoleOut]

    created_at: date = ParamSchema.datetime.build()
    updated_at: date = ParamSchema.datetime.build()


@marshmallow_dataclass
class UserPatchParams(BaseRequestModel):
    first_name: Optional[str] = ParamSchema.first_name.build()
    middle_name: Optional[str] = ParamSchema.middle_name.build()
    last_name: Optional[str] = ParamSchema.last_name.build()
    phone_number: Optional[str] = ParamSchema.phone_number.build()
    date_of_birth: Optional[date] = ParamSchema.date.build()
    is_active: Optional[bool] = ParamSchema.bool.build()
    roles: Optional[list[RoleBase]] = ParamFieldConfig().build()
