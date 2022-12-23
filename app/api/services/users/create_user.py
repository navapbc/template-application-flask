from uuid import uuid4

from api.db.models.user_models import User
from api.route.api_context import ApiContext
from api.route.schemas import user_schemas


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
# TODO: Use classes / objects as inputs to service methods
# https://github.com/navapbc/template-application-flask/issues/52
def create_user(request_user: user_schemas.RequestUser, api_context: ApiContext) -> User:
    # TODO: move this code to service and/or persistence layer
    user = User(**request_user.as_dict())
    user.id = uuid4()

    if user.roles is not None:
        for role in user.roles:
            role.user_id = user.id

    api_context.db_session.add(user)
    api_context.db_session.flush()
    return user
