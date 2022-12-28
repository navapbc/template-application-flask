from datetime import date
from typing import Any, Optional

from api.db.models.user_models import Role, RoleType, User

# TODO: add User here


# TODO: this should not live here
# TODO: dataclass?
# TODO: maybe extend User?
class UserPatchParams:
    # TODO: all of these should be Optional, yeah?
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    date_of_birth: date
    is_active: bool

    # TODO: fix this
    roles: Optional[list["Role"]]

    # TODO: this should be hidden somewhere else
    _fields_set: dict = None

    def __init__(self, data: dict):
        print("IN init")
        for key, value in data.items():
            setattr(self, key, value)

        self._fields_set = data

    # TODO: this should be hidden somewhere
    # TODO: add comments
    def get_set_params(self) -> dict:
        return self._fields_set
