import apiflask
from sqlalchemy import orm

from api.db.models.user_models import User
from api.route.api_context import ApiContext


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
# TODO: Use classes / objects as inputs to service methods
# https://github.com/navapbc/template-application-flask/issues/52
def get_user(user_id: str, api_context: ApiContext) -> User:
    # TODO: move this to service and/or persistence layer
    result = api_context.db_session.query(User).options(orm.selectinload(User.roles)).get(user_id)

    if result is None:
        # TODO move HTTP related logic out of service layer to controller layer and just return None from here
        # https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053754975
        raise apiflask.HTTPError(404, message=f"Could not find user with ID {user_id}")

    return result
