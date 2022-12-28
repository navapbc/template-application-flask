from dataclasses import dataclass
from datetime import date
from typing import Optional

from api.db.models.user_models import Role

# TODO: add User here

# base class for handling params for PATCH endpoints
# persist the original JSON dict in _fields_set, so
# that we can determine which values were set by the user
class PatchParamsBase:
    _fields_set: dict = None

    def __init__(self, data: dict):
        print("IN PatchParamsBase __init__")
        self._fields_set = data

    def get_set_params(self) -> dict:
        return self._fields_set


@dataclass
class UserPatchParams(PatchParamsBase):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = None

    # TODO: fix this
    roles: Optional[list["Role"]] = None

    def load_stuff(self, data: dict):
        print("IN UserPatchParams load_stuff")
        super().__init__(data)
