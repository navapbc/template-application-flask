#
# Multi-environment configuration expressed in Python.
#

import importlib
import logging
import pathlib

from src.adapters.db.clients.postgres_config import PostgresDBConfig
from src.app_config import AppConfig
from src.logging.config import LoggingConfig
from src.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class RootConfig(PydanticBaseEnvConfig):
    app: AppConfig
    database: PostgresDBConfig
    logging: LoggingConfig


def load(environment_name, environ=None) -> RootConfig:
    """Load the configuration for the given environment name."""
    logger.info("loading configuration", extra={"environment": environment_name})
    module = importlib.import_module(name=".env." + environment_name, package=__package__)
    config = module.config

    if environ:
        config.override_from_environment(environ)
    config.app.environment = environment_name

    return config


def load_all() -> dict[str, RootConfig]:
    """Load all environment configurations, to ensure they are valid. Used in tests."""
    directory = pathlib.Path(__file__).parent / "env"
    return {item.stem: load(str(item.stem)) for item in directory.glob("*.py")}
