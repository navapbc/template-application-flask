"""
This module has functionality to extend Flask with a database client.

To initialize this flask extension, call init_app() with an instance
of a Flask app and an instance of a DBClient.

Example:
    import src.adapters.db as db
    import src.adapters.db.flask_db as flask_db

    db_client = db.init()
    app = APIFlask(__name__)
    flask_db.init_app(db_client, app)

Then, in a request handler, use the with_db_session decorator to get a
new database session that lasts for the duration of the request.

Example:
    import src.adapters.db as db
    import src.adapters.db.flask_db as flask_db

    @app.route("/health")
    @flask_db.with_db_session
    def health(db_session: db.Session):
        with db_session.begin():
            ...


Alternatively, if you want to get the database client directly, use the get_db
function.

Example:
    from flask import current_app
    import src.adapters.db.flask_db as flask_db

    @app.route("/health")
    def health():
        db_client = flask_db.get_db(current_app)
        # db_client.get_connection() or db_client.get_session()
"""
from functools import wraps
from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

from flask import Flask, current_app

import src.adapters.db as db
from src.adapters.db.client import DBClient

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
        import src.adapters.db.flask_db as flask_db

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
    To start a transaction use db_session.begin()

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
