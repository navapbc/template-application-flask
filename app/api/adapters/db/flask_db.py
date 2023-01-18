"""
This module functionality to extend Flask with a database client.

Usage:
    # initialization in Flask's create_app()

    import api.adapters.db as db
    import api.adapters.db.flask_db as flask_db

    app = APIFlask(__name__)
    flask_db.init_app(db_client, app)

    # in a request handler

    from flask import current_app
    import api.adapters.db.flask_db as flask_db

    @app.route("/health")
    def health():
        db_client = flask_db.get_db(current_app)
"""
from functools import wraps
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

from flask import Flask, current_app

import api.adapters.db as db
from api.adapters.db.client import DBClient

_FLASK_EXTENSION_KEY = "db"


def init_app(db_client: DBClient, app: Flask) -> None:
    """Initialize the Flask app.

    Add the database to the Flask app's extensions so that it can be
    accessed by request handlers using the current app context.

    see get_db
    """
    app.extensions[_FLASK_EXTENSION_KEY] = db_client


def get_db(app: Flask) -> DBClient:
    """Get the database connection for the given Flask app.

    Use this in request handlers to access the database from the active Flask app.

    Example:
        from flask import current_app
        import api.adapters.db.flask_db as flask_db

        @app.route("/health")
        def health():
            db_client = flask_db.get_db(current_app)
    """
    return app.extensions[_FLASK_EXTENSION_KEY]


P = ParamSpec("P")
T = TypeVar("T")


def with_db_session(f: Callable[Concatenate[db.Session, P], T]) -> Callable[P, T]:
    """Decorator for functions that need a database session.

    This decorator will create a new session object and pass it to the function
    as the first positional argument. A transaction is not started automatically.
    If you want to start to a transaction automatically, you can use
    with_db_session_transaction.

    Usage:
        @with_db_session
        def foo(db_session: db.Session):
            ...

        @with_db_session
        def bar(db_session: db.Session, x, y):
            ...
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        with get_db(current_app).get_session() as session:
            return f(session, *args, **kwargs)

    return wrapper
