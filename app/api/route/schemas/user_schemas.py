import dataclasses
from datetime import date
from typing import Any, Mapping

import marshmallow
from apiflask import fields
from marshmallow import fields as marshmallow_fields

from api.db.models.user_models import RoleType
from api.route.schemas.request_schema import RequestModel

##############
# Role Models
##############


@dataclasses.dataclass
class RequestRole(RequestModel):
    type: RoleType


class RoleSchema(marshmallow.Schema):
    type = marshmallow_fields.Enum(RoleType, description="The name of the role", by_value=True)

    # Output only fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Note that user_id is not included in the API schema since the role
    # will always be a nested fields of the API user

    @marshmallow.post_load
    def make_role(self, data: dict, **kwargs: dict) -> RequestRole:
        return RequestRole(**data)


##############
# User Models
##############


@dataclasses.dataclass
class CreateRequestUser(RequestModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    date_of_birth: date | None = None
    is_active: bool | None = None
    roles: list[RequestRole] | None = None


@dataclasses.dataclass
class PatchRequestUser:
    user: CreateRequestUser
    fields_to_patch: list[str]


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


class CreateUserSchema(UserSchema):
    @marshmallow.post_load
    def make_user(self, data: dict, **kwargs: dict) -> CreateRequestUser:
        return CreateRequestUser(**data)


class PatchUserSchema(UserSchema):
    @marshmallow.post_load
    def make_user(self, data: Mapping[str, Any], **kwargs: dict) -> PatchRequestUser:
        return PatchRequestUser(
            user=CreateRequestUser(**data),
            fields_to_patch=list(data.keys()),
        )
