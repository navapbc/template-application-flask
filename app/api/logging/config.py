import logging
import os
import sys

import api.logging.formatters as formatters
import api.logging.pii as pii


def configure_logging() -> None:
    consoleHandler = logging.StreamHandler(sys.stdout)
    formatter = get_formatter()
    consoleHandler.setFormatter(formatter)
    consoleHandler.addFilter(pii.mask_pii)
    logging.root.addHandler(consoleHandler)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARN)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.dialects.postgresql").setLevel(logging.INFO)


def get_formatter() -> logging.Formatter:
    """Return the formatter used by the root logger."""
    log_format = os.getenv("LOG_FORMAT", "json")

    print("get_formatter")
    print(log_format)
    if log_format == "human-readable":
        return formatters.HumanReadableFormatter()
    return formatters.JsonFormatter()
