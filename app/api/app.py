import os
from contextlib import contextmanager
from typing import Generator, Optional

import connexion
from flask import g
from werkzeug.exceptions import Unauthorized

import api.logging
from api.adapters import db
from api.auth.api_key_auth import User
from api.route.connexion_validators import get_custom_validator_map
from api.route.error_handlers import add_error_handlers_to_app

logger = api.logging.get_logger(__name__)


def create_app(
    check_migrations_current: bool = True,
    do_close_db: bool = True,
) -> connexion.FlaskApp:

    options = {"swagger_url": "/docs"}
    app = connexion.FlaskApp(__name__, specification_dir=get_project_root_dir(), options=options)
    add_error_handlers_to_app(app)

    db.init()

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
        g.db = db.get_connection()

    @app.app.teardown_request
    def close_db(exception: Optional[Exception] = None) -> None:
        if not do_close_db:
            logger.debug("Not closing DB session")
            return

        try:
            logger.debug("Closing DB session")
            db = g.pop("db", None)

            if db is not None:
                db.close()
        except Exception:
            logger.exception("Exception while closing DB session")
            pass

    return app


def current_user(is_user_expected: bool = True) -> Optional[User]:
    current = g.get("current_user")
    if is_user_expected and current is None:
        logger.error("No current user found for request")
        raise Unauthorized
    return current


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..")
