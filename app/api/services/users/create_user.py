from uuid import uuid4

from api.db.models.user_models import Role, User
from api.route.api_context import ApiContext
from api.route.models.user import UserParams, UserResponse


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
def create_user(api_context: ApiContext) -> UserResponse:
    request = UserParams.parse_obj(api_context.request_body)

    user = User(
        id=uuid4(),
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        is_active=request.is_active,
    )
    api_context.db_session.add(user)

    if request.roles is not None:
        user.roles = [Role(user_id=user.id, type=role.type) for role in request.roles]

    return UserResponse.from_orm(user)
