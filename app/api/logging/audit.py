#
# Application-level audit logging.
#
# See https://docs.python.org/3/library/audit_events.html
# https://docs.python.org/3/library/sys.html#sys.addaudithook
# https://www.python.org/dev/peps/pep-0578/
#

import logging
import sys
from typing import Any

import api.logging
import api.util.collections

logger = api.logging.get_logger(__name__)

AUDIT = 32

logging.addLevelName(AUDIT, "AUDIT")


def init() -> None:
    """Initialize the audit logging module to start
    logging security audit events."""
    sys.addaudithook(audit_hook)


IGNORE_AUDIT_EVENTS = {
    "builtins.id",
    "code.__new__",
    "compile",
    "exec",
    "import",
    "marshal.loads",
    "object.__getattr__",
    "object.__setattr__",
    "os.listdir",
    "os.scandir",
    "os.walk",
    "socket.__new__",
    "sys._current_frames",
    "sys._getframe",
    "sys.settrace",  # interferes with PyCharm debugger
}


def audit_hook(event_name: str, args: tuple[Any, ...]) -> None:
    if event_name in IGNORE_AUDIT_EVENTS:
        return
    if event_name == "open" and isinstance(args[0], str) and "/__pycache__/" in args[0]:
        # Python has a high rate of these events in normal operation.
        return
    if event_name == "os.chmod" and type(args[0]) is int:
        # Gunicorn generates a high volume of these events in normal operation (see workertmp.py)
        return
    if event_name == "open" and isinstance(args[0], str) and "/pytz/" in args[0]:
        # The pytz module generates a high volume of these events in normal operation.
        return

    audit_log(event_name, args)


def audit_log(event_name: str, args: tuple[Any, ...]) -> None:
    """Log a message but only log recently repeated messages at intervals."""
    key = (event_name, repr(args))
    count = audit_message_count[key] = audit_message_count[key] + 1
    if count <= 10 or (count <= 100 and (count % 10) == 0) or (count % 100) == 0:
        extra = {"audit.event_name": event_name, "count": count}
        for arg_index, arg in enumerate(args):
            extra["audit.args.%i" % arg_index] = arg
        logger.log(AUDIT, event_name, extra=extra)


audit_message_count = api.util.collections.LeastRecentlyUsedDict()
