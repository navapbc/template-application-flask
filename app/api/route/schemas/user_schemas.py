from typing import Any

import marshmallow
from apiflask import fields
from marshmallow import fields as marshmallow_fields

from api.db.models.user_models import Role, RoleType, User
from api.models.user import UserPatchParams

##############
# Role Models
##############


class RoleSchema(marshmallow.Schema):
    type = marshmallow_fields.Enum(RoleType, description="The name of the role", by_value=True)

    # Output only fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @marshmallow.post_load
    def make_role(self, data: dict, **kwargs: dict[str, Any]) -> Role:
        return Role(**data)


##############
# User Models
##############


class UserSchema(marshmallow.Schema):
    id = fields.UUID(dump_only=True)
    first_name = fields.String(description="The user's first name", required=True)
    middle_name = fields.String(description="The user's middle name")
    last_name = fields.String(description="The user's last name", required=True)
    phone_number = fields.String(
        description="The user's phone number",
        example="123-456-7890",
        required=True,
        pattern=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$",
    )
    date_of_birth = fields.Date(
        description="The users date of birth",
        required=True,
    )
    is_active = fields.Boolean(
        description="Whether the user is active",
        required=True,
    )
    roles = fields.List(fields.Nested(RoleSchema), required=True)

    # Output only fields in addition to id field
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserPostParamsSchema(UserSchema):
    @marshmallow.post_load
    def make_user_post_params(self, data: dict, **kwargs: dict[str, Any]) -> User:
        return User.create_from_data(data)


# re-use the UserSchema instead of defining those again
# but use a different post_load
class UserPatchParamsSchema(UserSchema):
    @marshmallow.post_load
    def make_user_patch_params(self, data: dict, **kwargs: dict[str, Any]) -> UserPatchParams:
        return UserPatchParams(data)
