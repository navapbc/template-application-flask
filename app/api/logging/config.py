import logging
import os
import sys

import api.logging.formatters as formatters
import api.logging.pii as pii
from api.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class LoggingConfig(PydanticBaseEnvConfig):
    log_format: str = "json"
    log_level: int = logging.INFO


def configure_logging() -> logging.Logger:
    """Configure logging for the application.

    Configures the root module logger to log to stdout.
    Adds a PII mask filter to the root logger.
    Also configures log levels third party packages.
    """

    config = LoggingConfig()

    # Loggers can be configured using config functions defined
    # in logging.config or by directly making calls to the main API
    # of the logging module (see https://docs.python.org/3/library/logging.config.html)
    # We opt to use the main API using functions like `addHandler` which is
    # non-destructive, i.e. it does not overwrite any existing handlers.
    # In contrast, logging.config.dictConfig() would overwrite any existing loggers.
    # This is important during testing, since fixtures like `caplog` add handlers that would
    # get overwritten if we call logging.config.dictConfig() during the scope of the test.
    consoleHandler = logging.StreamHandler(sys.stdout)
    formatter = get_formatter(config.log_format)
    consoleHandler.setFormatter(formatter)
    consoleHandler.addFilter(pii.mask_pii)
    logging.root.addHandler(consoleHandler)
    logging.root.setLevel(config.log_level)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARN)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.dialects.postgresql").setLevel(logging.INFO)
    return logging.root


def get_formatter(log_format: str) -> logging.Formatter:
    """Return the formatter used by the root logger.

    The formatter is determined by the environment variable LOG_FORMAT. If the
    environment variable is not set, the JSON formatter is used by default.
    """
    if log_format == "human-readable":
        return formatters.HumanReadableFormatter()
    return formatters.JsonFormatter()
