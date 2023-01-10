import os
import urllib.parse
from contextlib import contextmanager
from typing import Any, Generator, Optional

import flask_sqlalchemy
import psycopg2
import sqlalchemy.pool as pool
from apiflask import APIFlask
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker, session

import api.logging
from api.db.db_config import DbConfig, get_db_config
from api.db.migrations.run import have_all_migrations_run

# Re-export the Session type that is returned by the get_session() method
# to be used for type hints.
Session = session.Session

logger = api.logging.get_logger(__name__)

# The flask_sqlalchemy.SQLAlchemy instance.
# _db.session is the scoped_session instance that is automatically scoped to
# the current request. The type of _db.session `type(_db.session)` is
# `scoped_session`, which we re-export as `Session``.
_db: flask_sqlalchemy.SQLAlchemy


def init2(
    flask_app: APIFlask,
    config: Optional[DbConfig] = None,
):
    global _db

    db_config: DbConfig = config if config is not None else get_db_config()

    flask_app.config["SQLALCHEMY_DATABASE_URI"] = make_connection_uri(db_config)
    flask_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        # FYI, execute many mode handles how SQLAlchemy handles doing a bunch of inserts/updates/deletes at once
        # https://docs.sqlalchemy.org/en/14/dialects/postgresql.html#psycopg2-fast-execution-helpers
        "executemany_mode": "batch",
        "hide_parameters": db_config.hide_sql_parameter_logs,
        # TODO: Don't think we need this as we aren't using JSON columns, but keeping for reference
        # json_serializer=lambda o: json.dumps(o, default=pydantic.json.pydantic_encoder),
    }

    # create the extension
    _db = flask_sqlalchemy.SQLAlchemy(
        # Override the default naming of constraints
        # to use suffixes instead:
        # https://stackoverflow.com/questions/4107915/postgresql-default-constraint-names/4108266#4108266
        metadata=MetaData(
            naming_convention={
                "ix": "%(column_0_label)s_idx",
                "uq": "%(table_name)s_%(column_0_name)s_uniq",
                "ck": "%(table_name)s_`%(constraint_name)s_check`",
                "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
                "pk": "%(table_name)s_pkey",
            }
        ),
        session_options={
            "autocommit": False,
            "expire_on_commit": False,
        },
    )

    # initialize the Flask app with the Flask-SQLAlchemy extension
    _db.init_app(flask_app)


def init(
    config: Optional[DbConfig] = None,
    check_migrations_current: bool = False,
) -> scoped_session:
    logger.info("connecting to postgres db")

    engine = create_db_engine(config)
    conn = engine.connect()

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

    # Explicitly commit sessions — usually with session_scope. Also disable expiry on commit,
    # as we don't need to be strict on consistency within our routes. Once we've retrieved data
    # from the database, we shouldn't make any extra requests to the db when grabbing existing
    # attributes.
    session_factory = scoped_session(
        sessionmaker(autocommit=False, expire_on_commit=False, bind=engine)
    )

    if check_migrations_current:
        have_all_migrations_run(engine)

    engine.dispose()

    return session_factory


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


def create_db_engine(config: Optional[DbConfig] = None) -> Engine:
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
    return create_engine(
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


@contextmanager
def session_scope(
    session: scoped_session, close: bool = False
) -> Generator[scoped_session, None, None]:
    """Provide a transactional scope around a series of operations.

    See https://docs.sqlalchemy.org/en/13/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
    """

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if close:
            session.close()


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


def get_session() -> Session:
    # _db.session is a scoped_session. Calling `_db.session` returns the
    # current Session i.e. the session for the current Flask request
    # see https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/api/#flask_sqlalchemy.SQLAlchemy.session
    # and https://docs.sqlalchemy.org/en/20/orm/contextual.html
    return _db.session()
