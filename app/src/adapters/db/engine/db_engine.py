import abc

import sqlalchemy


class DbEngine(abc.ABC, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build_engine(self) -> sqlalchemy.engine.Engine:
        pass

    @abc.abstractmethod
    def check_db_connection(self, conn: sqlalchemy.engine.Connection) -> None:
        pass

    @property
    @abc.abstractmethod
    def check_connection_on_init(self) -> bool:
        pass
