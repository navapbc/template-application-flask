from flask import Flask

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
        from flask import current_app, Response
        import api.adapters.db as db

        @app.route("/health")
        def health() -> Response:
            db_client = db.get_db(current_app)
    """
    return app.extensions[_FLASK_EXTENSION_KEY]
