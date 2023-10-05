import uuid

from fastapi import HTTPException
from sqlalchemy import orm

from src.adapters.db import Session
from src.db.models.user_models import User


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
def get_user(db_session: Session, user_id: uuid.UUID) -> User:
    # TODO: move this to service and/or persistence layer
    result = db_session.get(User, user_id, options=[orm.selectinload(User.roles)])

    if result is None:
        # TODO move HTTP related logic out of service layer to controller layer and just return None from here
        # https://github.com/navapbc/template-application-flask/pull/51#discussion_r1053754975
        raise HTTPException(status_code=404, detail=f"Could not find user with ID {user_id}")

    return result
