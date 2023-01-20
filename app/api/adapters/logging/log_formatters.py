import json
import logging
from datetime import datetime

import api.adapters.logging.decodelog as decodelog
import api.util.string_utils as string_utils

# Attributes of LogRecord to exclude from the JSON formatted lines. An exclusion list approach is
# used so that all "extra" attributes can be included in a line.
EXCLUDE_ATTRIBUTES = {
    "args",
    "exc_info",
    "filename",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "pathname",
    "processName",
    "relativeCreated",
}


class JsonFormatter(logging.Formatter):
    """A logging formatter which formats each line as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        super(JsonFormatter, self).format(record)

        output = {
            key: string_utils.mask_pii_for_key(key, value)
            for key, value in record.__dict__.items()
            if key not in EXCLUDE_ATTRIBUTES and value is not None
        }

        return json.dumps(output, separators=(",", ":"))


class HumanReadableFormatter(logging.Formatter):
    """A logging formatter which formats each line
    as color-code human readable text
    """

    def format(self, record: logging.LogRecord) -> str:
        super(HumanReadableFormatter, self).format(record)

        extra = record.__dict__

        return decodelog.format_line(
            datetime.utcfromtimestamp(record.created),
            record.name,
            record.funcName,
            record.levelname,
            record.message,
            extra,
        )