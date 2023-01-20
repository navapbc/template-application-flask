"""Helper functions for testing database code."""
import contextlib
import uuid

import api.adapters.db as db
import api.adapters.logging as logging
from api.adapters.db.config import get_db_config

logger = logging.get_logger(__name__)


@contextlib.contextmanager
def create_isolated_db(monkeypatch) -> None:
    """
    Creates a temporary PostgreSQL schema and creates a database engine
    that connects to that schema. Drops the schema after the context manager
    exits.
    """
    schema_name = f"test_schema_{uuid.uuid4().int}"
    monkeypatch.setenv("DB_SCHEMA", schema_name)
    monkeypatch.setenv("POSTGRES_DB", "main-db")
    monkeypatch.setenv("POSTGRES_USER", "local_db_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret123")
    monkeypatch.setenv("ENVIRONMENT", "local")

    # To improve test performance, don't check the database connection
    # when initializing the DB client.
    db_client = db.init(check_db_connection=False)
    with db_client.get_connection() as conn:
        _create_schema(conn, schema_name)
        try:
            yield db_client
        finally:
            _drop_schema(conn, schema_name)


def _create_schema(conn: db.Connection, schema_name: str):
    """Create a database schema."""
    db_test_user = get_db_config().username

    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def _drop_schema(conn: db.Connection, schema_name: str):
    """Drop a database schema."""
    conn.execute(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)
