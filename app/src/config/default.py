#
# Default configuration.
#
# This is the base layer of configuration. It is used if an environment does not override a value.
# Each environment may override individual values (see local.py, dev.py, prod.py, etc.).
#
# This configuration is also used when running tests (individual test cases may have code to use
# different configuration).
#

from src.adapters.db.clients.postgres_config import PostgresDBConfig
from src.app_config import AppConfig
from src.config import RootConfig
from src.logging.config import LoggingConfig, LoggingFormat


def default_config() -> RootConfig:
    return RootConfig(
        app=AppConfig(),
        database=PostgresDBConfig(),
        logging=LoggingConfig(
            format=LoggingFormat.json,
            level="INFO",
            enable_audit=True,
        ),
    )
