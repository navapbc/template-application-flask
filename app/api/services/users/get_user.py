from api.db.models.user_models import User
from api.route.api_context import ApiContext
from api.route.models.user import UserResponse
from api.route.route_utils import get_or_404


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
def get_user(user_id: str, api_context: ApiContext) -> UserResponse:
    user = get_or_404(api_context.db_session, User, user_id)

    return UserResponse.from_orm(user)
