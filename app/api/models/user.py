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

    # override dataclass init method, so that we can call PatchParamsBase init first
    def __init__(self, **kwargs):
        print("IN UserPatchParams __init__")

        super().__init__(kwargs)

        self.first_name = kwargs["first_name"] if "first_name" in kwargs else None
        self.middle_name = kwargs["middle_name"] if "middle_name" in kwargs else None
        self.last_name = kwargs["last_name"] if "last_name" in kwargs else None
        self.phone_number = kwargs["phone_number"] if "phone_number" in kwargs else None
        self.date_of_birth = kwargs["date_of_birth"] if "date_of_birth" in kwargs else None
        self.is_active = kwargs["is_active"] if "is_active" in kwargs else None
