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


def mask_pii(record: logging.LogRecord):
    record.__dict__ |= {
        key: _mask_pii_for_key(key, value)
        for key, value in record.__dict__.items()
        if key not in EXCLUDE_ATTRIBUTES and value is not None
    }
    return record


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


def _mask_pii_for_key(key: str, value: Optional[Any]) -> Any:
    """
    Mask the given value if it has the pattern of a tax identifier
    unless its key is one of the allowed values to avoid masking
    something that looks like an SSN but is known to be safe (like a timestamp)
    """
    if key in ALLOW_NO_MASK:
        return value
    return _mask_pii(value)


def _mask_pii(value: Optional[Any]) -> str:
    if TIN_RE.match(str(value)):
        return TIN_RE.sub("*********", str(value))
    return value
