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


HUMAN_READABLE_FORMATTER_DEFAULT_MESSAGE_LENGTH = decodelog.DEFAULT_MESSAGE_LENGTH


class HumanReadableFormatter(logging.Formatter):
    """A logging formatter which formats each line
    as color-code human readable text
    """

    message_length: int

    def __init__(self, message_length: int = HUMAN_READABLE_FORMATTER_DEFAULT_MESSAGE_LENGTH):
        super().__init__()
        self.message_length = message_length

    def format(self, record: logging.LogRecord) -> str:
        return decodelog.format_line(
            datetime.utcfromtimestamp(record.created),
            record.name,
            record.funcName,
            record.levelname,
            record.msg,
            record.__dict__,
            message_length=self.message_length,
        )
