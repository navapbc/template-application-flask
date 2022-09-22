import os
from contextlib import contextmanager
from typing import Generator, Optional

import connexion
from flask import g
from werkzeug.exceptions import Unauthorized

import api.db as db
import api.logging
from api.auth.api_key_auth import User
from api.route.connexion_validators import get_custom_validator_map
from api.route.error_handlers import add_error_handlers_to_app

logger = api.logging.get_logger(__name__)


def create_app(
    check_migrations_current: bool = True,
    db_session_factory: Optional[db.scoped_session] = None,
    do_close_db: bool = True,
) -> connexion.FlaskApp:

    # Initialize the db
    if db_session_factory is None:
        db_session_factory = db.init(check_migrations_current=check_migrations_current)

    options = {"swagger_url": "/docs"}
    app = connexion.FlaskApp(__name__, specification_dir=get_project_root_dir(), options=options)
    add_error_handlers_to_app(app)

    app.add_api(
        "openapi.yml",
        strict_validation=True,
        validator_map=get_custom_validator_map(),
        validate_responses=True,
    )

    @app.app.before_request
    def push_db() -> None:
        # Attach the DB session factory
        # to the global Flask context
        g.db = db_session_factory
        g.connexion_flask_app = app

    @app.app.teardown_request
    def close_db(exception: Optional[Exception] = None) -> None:
        if not do_close_db:
            logger.debug("Not closing DB session")
            return

        try:
            logger.debug("Closing DB session")
            db = g.pop("db", None)

            if db is not None:
                db.remove()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    return app


def db_session_raw() -> db.scoped_session:
    """Get a plain SQLAlchemy Session."""
    session: db.scoped_session = g.get("db")
    if session is None:
        raise Exception("No database session available in application context")

    return session


@contextmanager
def db_session(close: bool = False) -> Generator[db.scoped_session, None, None]:
    """Get a SQLAlchemy Session wrapped in some transactional management.

    This commits session when done, rolls back transaction on exceptions,
    optionally closing the session (which disconnects any entities in the
    session, so be sure closing is what you want).
    """

    session = db_session_raw()
    with db.session_scope(session, close) as session_scoped:
        yield session_scoped


def current_user(is_user_expected: bool = True) -> Optional[User]:
    current = g.get("current_user")
    if is_user_expected and current is None:
        logger.error("No current user found for request")
        raise Unauthorized
    return current


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..")
