from uuid import uuid4

import api.logging
from api.db.models.user_models import User, UserRole
from api.route.api_context import ApiContext
from api.services.model import UserParams, UserResponse

logger = api.logging.get_logger(__name__)


def create_user(api_context: ApiContext) -> UserResponse:
    request = UserParams.parse_obj(api_context.request_body)

    user = User(
        user_id=uuid4(),
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        is_active=request.is_active,
    )
    api_context.db_session.add(user)

    if request.roles is not None:
        user_roles = []
        for request_role in request.roles:
            user_roles.append(
                UserRole(user_id=user.user_id, role_description=request_role.role_description)
            )

        user.roles = user_roles

    return UserResponse.from_orm(user)
