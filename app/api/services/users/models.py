import dataclasses
from datetime import date

from api.db.models import user_models
from api.services.core import patch_params


@dataclasses.dataclass
class RequestRole:
    type: user_models.RoleType


@dataclasses.dataclass
class CreateRequestUser:
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    date_of_birth: date | None = None
    is_active: bool | None = None
    roles: list[RequestRole] | None = None


PatchRequestUser = patch_params.PatchParams[CreateRequestUser]
