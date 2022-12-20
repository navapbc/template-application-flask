from typing import Any

import marshmallow
from apiflask import fields

from api.db.models.user_models import RoleEnum, User, UserRole
from api.route.schemas.base_api_model import BaseApiSchema

##############
# Role Models
##############


class RoleSchema(BaseApiSchema):
    role_description = fields.String(allowed_values=RoleEnum, description="The name of the role")

    # Output only fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @marshmallow.post_load
    def make_role(self, data: dict, **kwargs: dict[str, Any]) -> UserRole:
        return UserRole(**data)


##############
# User Models
##############


class UserSchema(BaseApiSchema):
    user_id = fields.UUID(dump_only=True)
    first_name = fields.String(description="The user's first name")
    middle_name = fields.String(description="The user's middle name")
    last_name = fields.String(description="The user's last name")
    phone_number = fields.String(
        description="The user's phone number",
        example="123-456-7890",
        pattern=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$",
    )
    date_of_birth = fields.Date(description="The users date of birth")
    is_active = fields.Boolean(description="Whether the user is active")
    roles = fields.List(fields.Nested(RoleSchema))

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @marshmallow.post_load
    def make_user(self, data: dict, **kwargs: dict[str, Any]) -> User:
        return User(**data)
