import abc

import sqlalchemy
from sqlalchemy.orm import session


# Re-export the Connection type that is returned by the get_connection() method
# to be used for type hints.
Connection = sqlalchemy.engine.Connection

# Re-export the Session type that is returned by the get_session() method
# to be used for type hints.
Session = session.Session

class DbEngine(abc.ABC, metaclass=abc.ABCMeta):

    _engine: sqlalchemy.engine.Engine

    def __init__(self) -> None:
        self._engine = self._configure_engine()

    def get_connection(self) -> Connection:
        return self._engine.connect()
    
    def get_session(self) -> Session:
        return Session(bind=self._engine, expire_on_commit=False, autocommit=False)

    @abc.abstractmethod
    def _configure_engine(self) -> sqlalchemy.engine.Engine:
        raise NotImplementedError()

    @abc.abstractmethod
    def check_db_connection(self) -> None:
        raise NotImplementedError()
