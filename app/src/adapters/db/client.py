"""
This module contains the DBClient class, which is used to manage database connections

For usage information look at the package docstring in __init__.py

This module also contains lower level connection related functions such as
make_connection_uri that can be used outside of the application context such as for
database migrations.
"""
import logging

import sqlalchemy
from sqlalchemy.orm import session

from src.adapters.db.engine.db_engine import DbEngine

# Re-export the Connection type that is returned by the get_connection() method
# to be used for type hints.
Connection = sqlalchemy.engine.Connection

# Re-export the Session type that is returned by the get_session() method
# to be used for type hints.
Session = session.Session

logger = logging.getLogger(__name__)


class DBClient:
    """Database connection manager.

    This class is used to manage database connections for the Flask app.
    It has methods for getting a new connection or session object.
    """

    _db_engine: DbEngine
    _engine: sqlalchemy.engine.Engine

    def __init__(self, db_engine: DbEngine) -> None:
        self._db_engine = db_engine
        self._engine = db_engine.build_engine()

        # Try connecting to the database immediately upon initialization
        # so that we can fail fast if the database is not available.
        # Checking the db connection on db init is disabled in tests.
        if db_engine.check_connection_on_init:
            self.check_db_connection()

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
        logger.info("connecting to db")
        with self.get_connection() as conn:
            self._db_engine.check_db_connection(conn)


def init(db_engine: DbEngine) -> DBClient:
    return DBClient(db_engine)