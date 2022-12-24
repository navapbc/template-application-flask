import dataclasses

from api.db.models.user_models import Role, User
from api.route.api_context import ApiContext
from api.route.schemas import user_schemas


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
# TODO: Use classes / objects as inputs to service methods
# https://github.com/navapbc/template-application-flask/issues/52
def create_user(request_user: user_schemas.RequestUser, api_context: ApiContext) -> User:
    user_schemas.UserSchema().validate(dataclasses.asdict(request_user))
    assert request_user.first_name is not None
    assert request_user.middle_name is not None
    assert request_user.last_name is not None
    assert request_user.phone_number is not None
    assert request_user.date_of_birth is not None
    assert request_user.is_active is not None
    assert request_user.roles is not None
    # TODO: move this code to service and/or persistence layer
    user = User(
        first_name=request_user.first_name,
        middle_name=request_user.middle_name,
        last_name=request_user.last_name,
        phone_number=request_user.phone_number,
        date_of_birth=request_user.date_of_birth,
        is_active=request_user.is_active,
        roles=[Role(type=role.type) for role in request_user.roles],
    )
    api_context.db_session.add(user)
    api_context.db_session.flush()
    return user
