import logging
from typing import Optional

import pydantic
from pydantic import Field

from src.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class PostgresDBConfig(PydanticBaseEnvConfig):
    check_connection_on_init: bool = Field(True, env="DB_CHECK_CONNECTION_ON_INIT")
    host: str = Field("localhost", env="DB_HOST")
    name: str = Field("main-db", env="POSTGRES_DB")
    username: str = Field("local_db_user", env="POSTGRES_USER")
    password: Optional[pydantic.types.SecretStr] = Field(None, env="POSTGRES_PASSWORD")
    db_schema: str = Field("public", env="DB_SCHEMA")
    port: int = Field(5432, env="DB_PORT")
    hide_sql_parameter_logs: bool = Field(True, env="HIDE_SQL_PARAMETER_LOGS")
    sslmode: str = "require"
