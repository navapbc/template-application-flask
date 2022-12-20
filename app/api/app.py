import os
from contextlib import contextmanager
from typing import Generator, Optional

from apiflask import APIFlask
from flask import g
from werkzeug.exceptions import Unauthorized

import api.db as db
import api.logging
from api.auth.api_key_auth import User
from api.route.error_handlers import add_error_handlers_to_app
from api.route.healthcheck import healthcheck_blueprint
from api.route.schemas import response_schema
from api.route.user_route import user_blueprint

logger = api.logging.get_logger(__name__)


def create_app(
    check_migrations_current: bool = True,
    db_session_factory: Optional[db.scoped_session] = None,
    do_close_db: bool = True,
) -> APIFlask:

    # Initialize the db
    if db_session_factory is None:
        db_session_factory = db.init(check_migrations_current=check_migrations_current)

    app = APIFlask(__name__)

    # Add various configurations, and
    # adjustments to the application
    configure_app(app)
    add_error_handlers_to_app(app)
    register_blueprints(app)
    register_request_handlers(app, db_session_factory, do_close_db)

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


def configure_app(app: APIFlask) -> None:
    # Modify the response schema to instead use the format of our ApiResponse class
    # which adds additional details to the object.
    # https://apiflask.com/schema/#base-response-schema-customization
    app.config["BASE_RESPONSE_SCHEMA"] = response_schema.ResponseSchema

    # Set a few values for the Swagger endpoint
    app.config["OPENAPI_VERSION"] = "3.0.3"

    # Set various general OpenAPI config values
    app.info = {
        "title": "Template Application Flask",
        "description": "Template API for a Flask Application",
        "contact": {
            "name": "Nava PBC Engineering",
            "url": "https://www.navapbc.com",
            "email": "engineering@navapbc.com",
        },
    }

    # Set the security schema and define the header param
    # where we expect the API token to reside.
    # See: https://apiflask.com/authentication/#use-external-authentication-library
    app.security_schemes = {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-Auth"}}


def register_blueprints(app: APIFlask) -> None:
    app.register_blueprint(healthcheck_blueprint)
    app.register_blueprint(user_blueprint)


def register_request_handlers(
    app: APIFlask, db_session_factory: db.scoped_session, do_close_db: bool
) -> None:
    @app.before_request
    def push_db() -> None:
        # Attach the DB session factory
        # to the global Flask context
        g.db = db_session_factory

    @app.teardown_request
    def close_db(exception: Optional[BaseException] = None) -> None:
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


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..")
