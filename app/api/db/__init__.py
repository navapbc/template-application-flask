"""
Database module.

Usage:
    import api.db as db

    db_client = db.init_db()

    # non-ORM style usage
    with db_client.get_connection() as conn:
        conn.execute(...)

    # ORM style usage
    with db_client.get_session() as session:
        session.query(...)
        with session.begin():
            session.add(...)
"""

import os
import urllib.parse
from typing import Any, Optional

import psycopg2
import sqlalchemy
import sqlalchemy.pool as pool
from flask import Flask
from sqlalchemy.orm import session

import api.logging
from api.db.db_config import DbConfig, get_db_config

_FLASK_EXTENSION_KEY = "db"

# Re-export the Connection type that is returned by the get_connection() method
# to be used for type hints.
Connection = sqlalchemy.engine.Connection

# Re-export the Session type that is returned by the get_session() method
# to be used for type hints.
Session = session.Session

logger = api.logging.get_logger(__name__)


class DBClient:
    """Database connection manager.

    This class is used to manage database connections for the Flask app.
    It has methods for getting a new connection or session object.
    """

    _engine: sqlalchemy.engine.Engine

    def __init__(self) -> None:
        self._engine = _create_db_engine()

    def init_app(self, app: Flask) -> None:
        """Initialize the Flask app.

        Add the database to the Flask app's extensions so that it can be
        accessed by request handlers using the current app context.

        see get_db
        """
        app.extensions[_FLASK_EXTENSION_KEY] = self

    def get_connection(self) -> Connection:
        """Return a new database connection object.

        Use the connection to execute SQL queries without using the ORM.

        Usage:
            with db.get_connection() as conn:
                conn.execute(...)
        """
        return self._engine.connect()

    def get_session(self) -> Session:
        """Return a new session object.

        In general, only one session object should be created per request.

        If you want to automatically commit or rollback the session, use
        the session.begin() context manager.
        See https://docs.sqlalchemy.org/en/13/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it

        Example:
            with db.get_session() as session:
                with session.begin():
                    session.add(...)
                # session is automatically committed here
                # or rolled back if an exception is raised
        """
        return Session(bind=self._engine, expire_on_commit=False, autocommit=False)

    def check_db_connection(self) -> None:
        """Check that we can connect to the database and log some info about the connection."""
        logger.info("connecting to postgres db")
        with self.get_connection() as conn:
            conn_info = conn.connection.dbapi_connection.info  # type: ignore

            logger.info(
                "connected to postgres db",
                extra={
                    "dbname": conn_info.dbname,
                    "user": conn_info.user,
                    "host": conn_info.host,
                    "port": conn_info.port,
                    "options": conn_info.options,
                    "dsn_parameters": conn_info.dsn_parameters,
                    "protocol_version": conn_info.protocol_version,
                    "server_version": conn_info.server_version,
                },
            )
            verify_ssl(conn_info)

            # TODO add check_migrations_current to config
            # if check_migrations_current:
            #     have_all_migrations_run(engine)


def init(*, check_db_connection: bool = True) -> DBClient:
    db = DBClient()

    # Try connecting to the database immediately upon initialization
    # so that we can fail fast if the database is not available.
    # Checking the db connection on db init is disabled in tests.
    if check_db_connection:
        db.check_db_connection()
    return db


def get_db(app: Flask) -> DBClient:
    """Get the database connection for the given Flask app.

    Use this in request handlers to access the database from the active Flask app.

    Example:
        from flask import current_app, Response
        import api.db as db

        @app.route("/health")
        def health() -> Response:
            db_client = db.get_db(current_app)
    """
    return app.extensions[_FLASK_EXTENSION_KEY]


def verify_ssl(connection_info: Any) -> None:
    """Verify that the database connection is encrypted and log a warning if not."""
    if connection_info.ssl_in_use:
        logger.info(
            "database connection is using SSL: %s",
            ", ".join(
                name + " " + connection_info.ssl_attribute(name)
                for name in connection_info.ssl_attribute_names
            ),
        )
    else:
        logger.warning("database connection is not using SSL")


# TODO rename to create_db since the key interface is that it's something that responds
# to .connect() method. Doesn't really matter that it's an Engine class instance
def _create_db_engine(config: Optional[DbConfig] = None) -> sqlalchemy.engine.Engine:
    db_config: DbConfig = config if config is not None else get_db_config()

    # We want to be able to control the connection parameters for each
    # connection because for IAM authentication with RDS, short-lived tokens are
    # used as the password, and so we potentially need to generate a fresh token
    # for each connection.
    #
    # For more details on building connection pools, see the docs:
    # https://docs.sqlalchemy.org/en/13/core/pooling.html#constructing-a-pool
    def get_conn() -> Any:
        return psycopg2.connect(**get_connection_parameters(db_config))

    conn_pool = pool.QueuePool(get_conn, max_overflow=10, pool_size=20, timeout=3)

    # The URL only needs to specify the dialect, since the connection pool
    # handles the actual connections.
    #
    # (a SQLAlchemy Engine represents a Dialect+Pool)
    return sqlalchemy.create_engine(
        "postgresql://",
        pool=conn_pool,
        # FYI, execute many mode handles how SQLAlchemy handles doing a bunch of inserts/updates/deletes at once
        # https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#psycopg2-fast-execution-helpers
        executemany_mode="batch",
        hide_parameters=db_config.hide_sql_parameter_logs,
        # TODO: Don't think we need this as we aren't using JSON columns, but keeping for reference
        # json_serializer=lambda o: json.dumps(o, default=pydantic.json.pydantic_encoder),
    )


def get_connection_parameters(db_config: DbConfig) -> dict[str, Any]:
    connect_args = {}
    environment = os.getenv("ENVIRONMENT")
    if not environment:
        raise Exception("ENVIRONMENT is not set")

    if environment != "local":
        connect_args["sslmode"] = "require"

    return dict(
        host=db_config.host,
        dbname=db_config.name,
        user=db_config.username,
        password=db_config.password,
        port=db_config.port,
        options=f"-c search_path={db_config.db_schema}",
        connect_timeout=3,
        **connect_args,
    )


def make_connection_uri(config: DbConfig) -> str:
    """Construct PostgreSQL connection URI

    More details at:
    https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    """
    host = config.host
    db_name = config.name
    username = config.username
    password = urllib.parse.quote(config.password) if config.password else None
    schema = config.db_schema
    port = config.port

    netloc_parts = []

    if username and password:
        netloc_parts.append(f"{username}:{password}@")
    elif username:
        netloc_parts.append(f"{username}@")
    elif password:
        netloc_parts.append(f":{password}@")

    netloc_parts.append(host)

    if port:
        netloc_parts.append(f":{port}")

    netloc = "".join(netloc_parts)

    uri = f"postgresql://{netloc}/{db_name}?options=-csearch_path={schema}"

    return uri
