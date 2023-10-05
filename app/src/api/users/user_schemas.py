from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.db.models import user_models


class RoleModel(BaseModel):
    type: user_models.RoleType


class UserModel(BaseModel):

    first_name: str
    middle_name: str | None = None
    last_name: str
    phone_number: str = Field(
        pattern=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$", examples=["123-456-7890"]
    )
    date_of_birth: date
    is_active: bool
    roles: list[RoleModel]


UNSET: Any = None


class UserModelPatch(UserModel):
    # TODO - this is unfortunately what we need to do for PATCH to work
    #        and is making me think PATCH should just not be used in favor of PUT endpoints
    #        which may also be simpler for front-ends as well.
    #
    #        Ideas:
    #           - Just go with a PUT endpoint
    #           - Make this how the main model works, merge the two
    #           - Be fine with duplication?
    #
    first_name: str = UNSET
    # middle_initial does not need to be redefined
    last_name: str = UNSET
    phone_number: str = Field(
        pattern=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$",
        examples=["123-456-7890"],
        default=UNSET,
    )
    date_of_birth: date = UNSET
    is_active: bool = UNSET
    roles: list[RoleModel] = UNSET


class UserModelOut(UserModel):
    id: UUID

    created_at: datetime
    updated_at: datetime
