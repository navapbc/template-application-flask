import re
from typing import Any, Optional


def join_list(joining_list: Optional[list], join_txt: str = "\n") -> str:
    """
    Utility to join a list.

    Functionally equivalent to:
    "" if joining_list is None else "\n".join(joining_list)
    """
    if not joining_list:
        return ""

    return join_txt.join(joining_list)


def blank_for_null(value: Optional[Any]) -> str:
    """
    Utility to make a string blank if its null

    Functionally equivalent to

    ```"" if value is None else str(value)```
    """
    # If a value is blank
    if value is None:
        return ""
    return str(value)


#############################
# Masking Utilities
#############################

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


def mask_pii_for_key(key: str, value: Optional[Any]) -> str:
    """
    Mask the given value if it has the pattern of a tax identifier
    unless its key is one of the allowed values to avoid masking
    something that looks like an SSN but is known to be safe (like a timestamp)
    """
    if key in ALLOW_NO_MASK:
        return str(value)
    return mask_pii(value)


def mask_pii(value: Optional[Any]) -> str:
    return TIN_RE.sub("*********", str(value))
