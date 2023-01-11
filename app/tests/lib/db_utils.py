import contextlib
import uuid

from api import db
from api import logging

logger = logging.get_logger(__name__)


@contextlib.contextmanager
def test_db_schema(monkeypatch) -> db.Engine:
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

    db_engine = db.create_db_engine()
    create_schema(db_engine, schema_name)
    try:
        yield db_engine
    finally:
        drop_schema(db_engine, schema_name)


def create_schema(db_engine: db.Engine, schema_name: str):
    """Create a database schema."""
    db_test_user = db.get_db_config().username

    exec_sql(db_engine, f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def drop_schema(db_engine: db.Engine, schema_name: str):
    """Drop a database schema."""
    exec_sql(db_engine, f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)


def exec_sql(db_engine: db.Engine, sql: str):
    with db_engine.connect() as connection:
        connection.execute(sql)
