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
        self._fields_set = data

    def get_set_params(self) -> dict:
        return self._fields_set


# TODO: dataclass?
# TODO: maybe extend User?
class UserPatchParams(PatchParamsBase):
    # TODO: all of these should be Optional, yeah?
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    date_of_birth: date
    is_active: bool

    # TODO: fix this
    roles: Optional[list["Role"]]

    def __init__(self, data: dict):
        super().__init__(data)

        for key, value in data.items():
            setattr(self, key, value)
