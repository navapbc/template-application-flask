from typing import Type, TypeVar
from uuid import UUID

from sqlalchemy.orm import scoped_session
from werkzeug.exceptions import NotFound

_T = TypeVar("_T")


def get_or_404(db_session: scoped_session, model: Type[_T], id: UUID | str | int) -> _T:
    """
    Utility method for fetching a single record from the DB by
    its primary key ID, and raising a NotFound exception if
    no such record exists.
    """
    result = db_session.query(model).get(id)

    if result is None:
        raise NotFound(description=f"Could not find {model.__name__} with ID {id}")

    return result
