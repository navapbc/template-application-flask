"""Helper functions for testing database code."""
import contextlib
import logging
import os
import uuid

import pydantic.types

import src.adapters.db as db
from src.adapters.db.clients.postgres_config import PostgresDBConfig

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def create_isolated_db(db_config: PostgresDBConfig) -> db.DBClient:
    """
    Creates a temporary PostgreSQL schema and creates a database engine
    that connects to that schema. Drops the schema after the context manager
    exits.
    """

    # To improve test performance, don't check the database connection
    # when initializing the DB client.
    db_client = db.PostgresDBClient(db_config)
    with db_client.get_connection() as conn:
        _create_schema(conn, db_config.db_schema, db_config.username)
        try:
            yield db_client
        finally:
            _drop_schema(conn, db_config.db_schema)


def _create_schema(conn: db.Connection, schema_name: str, db_test_user: str):
    """Create a database schema."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def _drop_schema(conn: db.Connection, schema_name: str):
    """Drop a database schema."""
    conn.execute(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)
