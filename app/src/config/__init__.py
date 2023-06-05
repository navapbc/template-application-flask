#
# Multi-environment configuration expressed in Python.
#

from src.adapters.db.clients.postgres_config import PostgresDBConfig
from src.app_config import AppConfig
from src.logging.config import LoggingConfig
from src.util.env_config import PydanticBaseEnvConfig


class RootConfig(PydanticBaseEnvConfig):
    app: AppConfig
    database: PostgresDBConfig
    logging: LoggingConfig
