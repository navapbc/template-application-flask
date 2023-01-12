"""
Database module.

It is recommended to import this module as `import api.db` rather than
`from api import db` in order to avoid confusion with instances of `DB`
which are named `db` by convention.

Example:
    import api.db

    db = api.db.init_db()

    # non-ORM style usage
    with db.get_connection() as conn:
        conn.execute(...)

    # ORM style usage
    with db.get_session() as session:
        session.query(...)
        with session.begin():
            session.add(...)

Alternatively, if you are only importing the module for type hints (and
to explicitly indicate dependencies), you can do `from api.db import DB`.

Example:
    from api.db import DB

    @app.route("/health")
    def health() -> Response:
        db: DB = app.extensions["db"]
        with db.get_connection() as conn:
            conn.execute(...)
"""

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


class DB:
    _engine: Engine

    def __init__(self) -> None:
        self._engine = _create_db_engine()

    def init_app(self, app: APIFlask) -> None:
        app.extensions["db"] = self

    def get_connection(self) -> Connection:
        return self._engine.connect()

    def get_session(self) -> Session:
        return Session(bind=self._engine, expire_on_commit=False, autocommit=False)

    def test_db_connection(self):
        logger.info("connecting to postgres db")
        with self.get_connection() as conn:
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


def init_db():
    return DB()


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
def _create_db_engine(config: Optional[DbConfig] = None) -> Engine:
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
