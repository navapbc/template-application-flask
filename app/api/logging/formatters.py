"""Log formatters for the API.

This module defines two formatters, JsonFormatter for machine-readable logs to
be used in production, and HumanReadableFormatter for human readable logs to
be used used during development.

See https://docs.python.org/3/library/logging.html#formatter-objects
"""

import json
import logging
from datetime import datetime

import api.logging.decodelog as decodelog


class JsonFormatter(logging.Formatter):
    """A logging formatter which formats each line as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(record.__dict__, separators=(",", ":"))


class HumanReadableFormatter(logging.Formatter):
    """A logging formatter which formats each line
    as color-code human readable text
    """

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return decodelog.format_line(
            datetime.utcfromtimestamp(record.created),
            record.name,
            record.funcName,
            record.levelname,
            message,
            record.__dict__,
        )
