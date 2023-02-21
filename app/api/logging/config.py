import logging
import sys

import api.logging.audit
import api.logging.formatters as formatters
import api.logging.pii as pii
from api.util.env_config import PydanticBaseEnvConfig

logger = logging.getLogger(__name__)


class HumanReadableFormatterConfig(PydanticBaseEnvConfig):
    message_width: int = formatters.HUMAN_READABLE_FORMATTER_DEFAULT_MESSAGE_WIDTH


class LoggingConfig(PydanticBaseEnvConfig):
    format = "json"
    level = "INFO"
    enable_audit = True
    human_readable_formatter = HumanReadableFormatterConfig()

    class Config:
        env_prefix = "log_"
        env_nested_delimiter = "__"


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
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = get_formatter(config)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(pii.mask_pii)
    logging.root.addHandler(console_handler)
    logging.root.setLevel(config.level)

    if config.enable_audit:
        api.logging.audit.init()

    # Configure loggers for third party packages
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARN)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.dialects.postgresql").setLevel(logging.INFO)

    return logging.root


def get_formatter(config: LoggingConfig) -> logging.Formatter:
    """Return the formatter used by the root logger.

    The formatter is determined by the environment variable LOG_FORMAT. If the
    environment variable is not set, the JSON formatter is used by default.
    """
    if config.format == "human-readable":
        return get_human_readable_formatter(config.human_readable_formatter)
    return formatters.JsonFormatter()


def get_human_readable_formatter(
    config: HumanReadableFormatterConfig,
) -> formatters.HumanReadableFormatter:
    """Return the human readable formatter used by the root logger."""
    return formatters.HumanReadableFormatter(message_width=config.message_width)
