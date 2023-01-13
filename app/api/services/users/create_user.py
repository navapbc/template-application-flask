from datetime import date
from typing import TypedDict

from api.db import Session
from api.db.models import user_models
from api.db.models.user_models import Role, User


class RoleParams(TypedDict):
    type: user_models.RoleType


class CreateUserParams(TypedDict):
    first_name: str
    middle_name: str
    last_name: str
    phone_number: str
    date_of_birth: date
    is_active: bool
    roles: list[RoleParams]


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
# TODO: Use classes / objects as inputs to service methods
# https://github.com/navapbc/template-application-flask/issues/52
def create_user(db_session: Session, user_params: CreateUserParams) -> User:
    # TODO: move this code to service and/or persistence layer
    user = User(
        # Convert nested object parameters to ORM objects then unpack the dictionary
        # of parameters as keyword arguments
        **{
            **user_params,
            "roles": [Role(type=role["type"]) for role in user_params["roles"]],
        }
    )
    db_session.add(user)
    return user
