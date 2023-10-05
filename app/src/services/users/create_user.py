from src.adapters.db import Session
from src.api.users.user_schemas import UserModel
from src.db.models.user_models import Role, User


# TODO: separate controller and service concerns
# https://github.com/navapbc/template-application-flask/issues/49#issue-1505008251
def create_user(db_session: Session, user_model: UserModel) -> User:
    with db_session.begin():
        # TODO: move this code to service and/or persistence layer
        user = User(
            first_name=user_model.first_name,
            middle_name=user_model.middle_name,
            last_name=user_model.last_name,
            phone_number=user_model.phone_number,
            date_of_birth=user_model.date_of_birth,
            is_active=user_model.is_active,
            roles=[Role(type=role.type) for role in user_model.roles],
        )
        db_session.add(user)
    return user
