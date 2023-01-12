from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, Optional

from flask import request

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
        return {"user_id": self.current_user.id if self.current_user else None}
