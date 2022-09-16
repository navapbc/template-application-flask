from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, Optional

import connexion

import api.app as app
import api.db as db
from api.auth.api_key_auth import User


@dataclass
class ApiContext:
    """
    Container class for components that most
    API endpoints need, grouped so we can avoid
    the boilerplate of fetching all of these
    """

    request_body: Any
    current_user: Optional[User]
    db_session: db.scoped_session

    def get_log_extra(self) -> dict[str, Any]:
        """
        Utility method for getting params to attach to the log as
         `logger.info("msg", extra=api_context.get_log_extra())`
        """
        return {"user_id": self.current_user.user_id if self.current_user else None}


@contextmanager
def api_context_manager(is_user_expected: bool = True) -> Generator[ApiContext, None, None]:
    """
    API context manager for working with
    requests and processing them to the DB.

    Sets up the DB session, current user,
    and grabs the request body.
    """
    with app.db_session() as db_session:
        # Attach the request body if present
        if connexion.request.is_json:
            body = connexion.request.json
        else:
            body = {}

        # Current user is attached in api_key_auth.py
        # during authentication
        current_user = app.current_user(is_user_expected)

        yield ApiContext(body, current_user, db_session)
