import logging
from typing import Optional

from pydantic import Field

from src.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class PostgresDBConfig(PydanticBaseEnvConfig):
    check_connection_on_init: bool = Field(True, env="DB_CHECK_CONNECTION_ON_INIT")
    host: str = Field("localhost", env="DB_HOST")
    name: str = Field("main-db", env="POSTGRES_DB")
    username: str = Field("local_db_user", env="POSTGRES_USER")
    password: Optional[str] = Field(..., env="POSTGRES_PASSWORD")
    db_schema: str = Field("public", env="DB_SCHEMA")
    port: str = Field("5432", env="DB_PORT")
    hide_sql_parameter_logs: bool = Field(True, env="HIDE_SQL_PARAMETER_LOGS")


def get_db_config() -> PostgresDBConfig:
    db_config = PostgresDBConfig()

    logger.info(
        "Constructed database configuration",
        extra={
            "host": db_config.host,
            "dbname": db_config.name,
            "username": db_config.username,
            "password": "***" if db_config.password is not None else None,
            "db_schema": db_config.db_schema,
            "port": db_config.port,
            "hide_sql_parameter_logs": db_config.hide_sql_parameter_logs,
        },
    )

    return db_config
