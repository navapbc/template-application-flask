"""
Database adapter for Postgres database.
This module is an abstraction around the psycopg3 python postgres library. It
has methods for connecting to the database, and abstracts away the loading of
config and environment variables.
"""

import atexit
import os

import psycopg
from psycopg import rows
import psycopg_pool

from api import logging

# Re-export these types to restrict the API of this module
# to only the types we want to expose explicitly.
Connection = psycopg.Connection
Cursor = psycopg.Cursor
DBConnectionError = psycopg.OperationalError
kwargs_row = rows.kwargs_row

logger = logging.get_logger(__name__)


def init():
    """Initializes the database connection pool"""
    global pool
    print(get_conninfo())
    pool = psycopg_pool.ConnectionPool(get_conninfo(), open=False)

    # Open the connection pool when the app starts
    pool.open()

    # # Close the connection pool when the app shuts down
    atexit.register(pool.close)


def get_conninfo() -> str:
    """Gets a db connection info based on environment variables"""
    dbhost = os.getenv("DB_HOST")
    dbname = os.getenv("POSTGRES_DB")
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    sslmode = "allow" if ENVIRONMENT == "local" else "verify-full"

    return psycopg.conninfo.make_conninfo(
        host=dbhost,
        dbname=dbname,
        user=username,
        password=password,
        sslmode=sslmode,
    )


def get_connection() -> psycopg.Connection:
    """Gets a db connection
    Uses database credentials in environment variables to obtain a database
    connection.
    Usage:
      with get_connection() as conn:
        with conn.cursor() as cur:
          cur.execute("SELECT 1")
          result = cur.fetchall()
    """
    return pool.connection()


pool: psycopg_pool.ConnectionPool | None = None

__all__ = ["init", "get_connection", "Connection", "Cursor", "kwargs_row"]
