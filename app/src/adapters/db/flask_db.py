"""
This module has functionality to extend Flask with a database client.

To initialize this flask extension, call register_db_client() with an instance
of a Flask app and an instance of a DBClient.

Example:
    import src.adapters.db as db
    import src.adapters.db.flask_db as flask_db

    db_client = db.init_postgres_client()
    app = APIFlask(__name__)
    flask_db.register_db_client(db_client, app)

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

_DEFAULT_FLASK_EXTENSION_KEY = "db"


def register_db_client(
    db_client: DBClient, app: Flask, client_name: str = _DEFAULT_FLASK_EXTENSION_KEY
) -> None:
    """Initialize the Flask app.

    Add the database to the Flask app's extensions so that it can be
    accessed by request handlers using the current app context.

    If you use multiple DB clients, you can differentiate them by
    specifying a client_name.

    see get_db
    """
    app.extensions[client_name] = db_client


def get_db(app: Flask, client_name: str = _DEFAULT_FLASK_EXTENSION_KEY) -> DBClient:
    """Get the database connection for the given Flask app.

    Use this in request handlers to access the database from the active Flask app.

    Specify the same client_name as used in register_db_client to get the correct client

    Example:
        from flask import current_app
        import src.adapters.db.flask_db as flask_db

        @app.route("/health")
        def health():
            db_client = flask_db.get_db(current_app)
    """
    return app.extensions[client_name]


P = ParamSpec("P")
T = TypeVar("T")


def with_db_session(
    *, client_name: str = _DEFAULT_FLASK_EXTENSION_KEY
) -> Callable[[Callable[Concatenate[db.Session, P], T]], Callable[P, T]]:
    """Decorator for functions that need a database session.

    This decorator will create a new session object and pass it to the function
    as the first positional argument. A transaction is not started automatically.
    To start a transaction use db_session.begin()

    Usage:
        @with_db_session()
        def foo(db_session: db.Session):
            ...

        @with_db_session()
        def bar(db_session: db.Session, x, y):
            ...

        @with_db_session(client_name="not_the_primary_client")
        def fiz(db_session: db.Session, x, y, z):
            ...
    """

    def decorator_func(f: Callable[Concatenate[db.Session, P], T]) -> Callable[P, T]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with get_db(current_app, client_name=client_name).get_session() as session:
                return f(session, *args, **kwargs)

        return wrapper

    return decorator_func
