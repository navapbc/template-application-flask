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
        from flask import current_app
        import api.adapters.db.flask_db as flask_db

        @app.route("/health")
        def health():
            db_client = flask_db.get_db(current_app)
    """
    return app.extensions[_FLASK_EXTENSION_KEY]
