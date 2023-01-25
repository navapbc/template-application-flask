#
# Application-level audit logging.
#
# See https://docs.python.org/3/library/audit_events.html
# https://docs.python.org/3/library/sys.html#sys.addaudithook
# https://www.python.org/dev/peps/pep-0578/
#

import logging
import sys
from typing import Any, Sequence

import api.logging
import api.util.collections

logger = api.logging.get_logger(__name__)

AUDIT = 32

logging.addLevelName(AUDIT, "AUDIT")


def init() -> None:
    """Initialize the audit logging module to start
    logging security audit events."""
    sys.addaudithook(handle_audit_event)


def handle_audit_event(event_name: str, args: tuple[Any, ...]) -> None:
    # Define events to log and the arguments to log for each event.
    # For more information about these events and what they mean, see https://peps.python.org/pep-0578/#suggested-audit-hook-locations
    # For the full list of auditable events, see https://docs.python.org/3/library/audit_events.html
    # Define this variable locally so it can't be modified by other modules.
    #
    # Events from the suggested audit hook locations in PEP 578 that we aren't logging:
    #
    # compile and import
    #     Detects when code is being compiled or imported.
    #
    #     Why we aren't logging:
    #     Logging as part of regular imports is too noisy.
    #
    # sys._getframe
    #     Detects when code is accessing frames directly.
    #
    #     Why we aren't logging:
    #     The logging module itself calls getFrame
    #     (see https://github.com/python/cpython/blob/bd7903967cd2a19ebc842dd1cce75f60a18aef02/Lib/logging/__init__.py#L170)
    #     so logging on this event would trigger an infinite loop unless
    #     logging._srcfile is set to None
    #     See https://github.com/python/cpython/blob/bd7903967cd2a19ebc842dd1cce75f60a18aef02/Lib/logging/__init__.py#L179-L189
    #
    # object.__getattr__
    #     Detect access to restricted attributes. This event is raised for any built-in members
    #     that are marked as restricted, and members that may allow bypassing imports.
    #
    #     Why we aren't logging:
    #     The logging module itself accesses frame.f_code.co_filename
    #     (see https://github.com/python/cpython/blob/bd7903967cd2a19ebc842dd1cce75f60a18aef02/Lib/logging/__init__.py#L202)
    #     which calls object.__getattr__ under the hood
    #     (see https://github.com/python/cpython/blob/main/Objects/frameobject.c#L89-L95)
    #

    EVENTS_TO_LOG = {
        # Detect dynamic execution of code objects. This only occurs for explicit
        # calls, and is not raised for normal function invocation.
        "exec": ("code_object",),
        # Detect when a file is about to be opened. path and mode are the usual
        # parameters to open if available, while flags is provided instead of
        # mode in some cases.
        "open": ("path", "mode", "flags"),
        # Detect access to network resources. The address is unmodified from the original call.
        "socket.connect": ("socket", "address"),
        # Detect when new audit hooks are being added.
        "sys.addaudithook": (),
        # Detects URL requests.
        "urllib.Request": ("url", "data", "headers", "method"),
    }

    if event_name not in EVENTS_TO_LOG:
        return

    arg_names = EVENTS_TO_LOG[event_name]
    log_audit_event(event_name, args, arg_names)


def log_audit_event(event_name: str, args: Sequence[Any], arg_names: Sequence[str]) -> None:
    """Log a message but only log recently repeated messages at intervals."""
    extra = {f"audit.args.{arg_name}": arg for arg_name, arg in zip(arg_names, args)}
    logger.log(AUDIT, event_name, extra=extra)


audit_message_count = api.util.collections.LeastRecentlyUsedDict()
