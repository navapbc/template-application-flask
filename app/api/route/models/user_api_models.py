import uuid
from datetime import date, datetime
from typing import Optional

import marshmallow
from apiflask import fields

from api.db.models.user_models import RoleEnum

##############
# Role Models
##############


class Role(marshmallow.Schema):
    role_description: str = fields.String(
        allowed_values=RoleEnum, description="The name of the role"
    )


class RoleIn(Role):
    pass


class RoleOut(Role):
    created_at: Optional[datetime] = fields.DateTime()
    updated_at: Optional[datetime] = fields.DateTime()


##############
# User Models
##############


class User(marshmallow.Schema):
    first_name: str = fields.String(description="The user's first name")
    middle_name: Optional[str] = fields.String(description="The user's middle name")
    last_name: str = fields.String(description="The user's last name")
    phone_number: str = fields.String(
        description="The user's phone number",
        example="123-456-7890",
        pattern=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$",
    )
    date_of_birth: date = fields.Date(description="The users date of birth")
    is_active: bool = fields.Boolean(description="Whether the user is active")


class UserIn(User):
    roles: list[Role] = fields.List(fields.Nested(RoleIn))


class UserOut(User):
    user_id: uuid.UUID = fields.UUID(description="The user's unique identifier")

    roles: list[RoleOut] = fields.List(fields.Nested(RoleOut))

    created_at: date = fields.DateTime()
    updated_at: date = fields.DateTime()


class UserPatchParams(UserIn):
    pass
