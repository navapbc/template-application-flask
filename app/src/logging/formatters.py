"""Log formatters for the API.

This module defines two formatters, JsonFormatter for machine-readable logs to
be used in production, and HumanReadableFormatter for human readable logs to
be used used during development.

See https://docs.python.org/3/library/logging.html#formatter-objects
"""
import pydantic
import pydantic.json
import json
import logging
from datetime import datetime

import src.logging.decodelog as decodelog



class JsonFormatter(logging.Formatter):
    """A logging formatter which formats each line as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        # logging.Formatter.format adds the `message` attribute to the LogRecord
        # see https://github.com/python/cpython/blob/main/Lib/logging/__init__.py#L690-L720
        super().format(record)

        x = json.dumps(record.__dict__, separators=(",", ":"), default=pydantic.json.pydantic_encoder)
        print("*"*50)
        print(record.__dict__)
        return x



HUMAN_READABLE_FORMATTER_DEFAULT_MESSAGE_WIDTH = decodelog.DEFAULT_MESSAGE_WIDTH


class HumanReadableFormatter(logging.Formatter):
    """A logging formatter which formats each line
    as color-code human readable text
    """

    message_width: int

    def __init__(self, message_width: int = HUMAN_READABLE_FORMATTER_DEFAULT_MESSAGE_WIDTH):
        super().__init__()
        self.message_width = message_width

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        return decodelog.format_line(
            datetime.utcfromtimestamp(record.created),
            record.name,
            record.funcName,
            record.levelname,
            message,
            record.__dict__,
            message_width=self.message_width,
        )
