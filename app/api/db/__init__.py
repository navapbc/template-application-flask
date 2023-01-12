import contextlib
import os
import urllib.parse
from contextlib import contextmanager
from typing import Any, Generator, Optional

import psycopg2
import sqlalchemy
import sqlalchemy.pool as pool
from apiflask import APIFlask
from sqlalchemy import engine
from sqlalchemy.orm import scoped_session, session, sessionmaker

import api.logging
from api.db.db_config import DbConfig, get_db_config
from api.db.migrations.run import have_all_migrations_run

# Re-export the Connection type that is returned by the get_connection() method
# to be used for type hints.
Connection = engine.Connection

# Re-export the Engine type that is returned by the create_db_engine() method
Engine = engine.Engine

# Re-export the Session type that is returned by the get_session() method
# to be used for type hints.
Session = session.Session

logger = api.logging.get_logger(__name__)

_db_engine: Optional[Engine] = None


def init_db():
    global _db_engine
    _db_engine = create_db_engine()

    logger.info("connecting to postgres db")

    with get_connection() as conn:
        conn_info = conn.connection.dbapi_connection.info

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


def get_connection() -> engine.Connection:
    if _db_engine is None:
        raise Exception("_db_engine is not initialized. Did you call init_db?")
    return _db_engine.connect()


def get_session() -> Session:
    if _db_engine is None:
        raise Exception("_db_engine not initialized. Did you call init_db?")
    return Session(bind=_db_engine, expire_on_commit=False, autocommit=False)


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


# TODO rename to create_db since the key interface is that it's something that responds
# to .connect() method. Doesn't really matter that it's an Engine class instance
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
