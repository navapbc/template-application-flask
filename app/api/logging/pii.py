"""Mask PII from log records.

This module defines a filter that can be attached to a logger to mask PII
from log records. The filter is applied to all log records, and masks PII
that looks like social security numbers.

You can add the filter to a handler:

Example:
    import logging
    import api.logging.pii as pii

    handler = logging.StreamHandler()
    handler.addFilter(pii.mask_pii)
    logger = logging.getLogger(__name__)
    logger.addHandler(handler)

Or you can add the filter directly to a logger.
If adding the filter directly to a logger, take note that the filter
will not be called for child loggers.
See https://docs.python.org/3/library/logging.html#logging.Logger.propagate

Example:
    import logging
    import api.logging.pii as pii

    logger = logging.getLogger(__name__)
    logger.addFilter(pii.mask_pii)
"""

import logging
import re
from typing import Any, Optional

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


def mask_pii(record: logging.LogRecord) -> bool:
    record.__dict__ |= {
        key: _mask_pii_for_key(key, value)
        for key, value in record.__dict__.items()
        if key not in EXCLUDE_ATTRIBUTES and value is not None
    }
    return True


# Regular expression to match a tax identifier (SSN), 9 digits with optional dashes.
# Matches between word boundaries (\b), except when:
#  - Preceded by word character and dash (e.g. "ip-10-11-12-134")
#  - Followed by a dot and digit, for decimal numbers (e.g. 999000000.5)
# See https://docs.python.org/3/library/re.html#regular-expression-syntax
TIN_RE = re.compile(
    r"""
        \b          # word boundary
        (?<!\w-)    # not preceded by word character and dash
        (\d-?){8}   # digit then optional dash, 8 times
        \d          # last digit
        \b          # word boundary
        (?!\.\d)    # not followed by decimal point and digit (for decimal numbers)
    """,
    re.ASCII | re.VERBOSE,
)

ALLOW_NO_MASK = {
    "account_key",
    "count",
    "created",
    "hostname",
    "process",
    "thread",
}


def _mask_pii_for_key(key: str, value: Optional[Any]) -> Optional[Any]:
    """
    Mask the given value if it has the pattern of a tax identifier
    unless its key is one of the allowed values to avoid masking
    something that looks like an SSN but is known to be safe (like a timestamp)
    """
    if key in ALLOW_NO_MASK:
        return value
    return _mask_pii(value)


def _mask_pii(value: Optional[Any]) -> Optional[Any]:
    if TIN_RE.match(str(value)):
        return TIN_RE.sub("*********", str(value))
    return value
