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
        # Detect when new audit hooks are being added.
        "sys.addaudithook": (),
        # Detects any attempt to set the open_code hook.
        "cpython.PyFile_SetOpenCodeHook": (),
        # Detect dynamic execution of code objects. This only occurs for explicit
        # calls, and is not raised for normal function invocation.
        "exec": ("code_object",),
        # Detect when a file is about to be opened. path and mode are the usual
        # parameters to open if available, while flags is provided instead of
        # mode in some cases.
        "io.open": ("path", "mode", "flags"),
        # Detect when code is injecting trace functions. Because of the
        # implementation, exceptions raised from the hook will abort the
        # operation, but will not be raised in Python code. Note that
        # threading.setprofile eventually calls this function, so the event
        # will be audited for each thread.
        "sys.setprofile": (),
        # Detect when code is injecting trace functions. Because of the
        # implementation, exceptions raised from the hook will abort the
        # operation, but will not be raised in Python code. Note that
        # threading.settrace eventually calls this function, so the event will
        # be audited for each thread.
        "sys.settrace": (),
        # Detect monkey patching of types and objects. This event is raised for
        # the __class__ attribute and any attribute on type objects.
        "object.__setattr__": ("object", "attr", "value"),
        # Detect deletion of object attributes. This event is raised for any
        # attribute on type objects.
        "object.__delattr__": ("object", "attr"),
        # Detect imports and global name lookup when unpickling.
        "pickle.find_class": ("module_name", "global_name"),
        # Notifies hooks they are being cleaned up, mainly in case the event is
        # triggered unexpectedly. This event cannot be aborted.
        "sys._clearaudithooks": (),
        # Detect dynamic creation of code objects. This only occurs for direct
        # instantiation, and is not raised for normal compilation.
        "code.__new__": ("bytecode", "filename", "name"),
        # Detect dynamic creation of function objects. This only occurs for
        # direct instantiation, and is not raised for normal compilation.
        "function.__new__": ("code",),
        # Detect when native modules are used.
        "ctypes.dlopen": ("module_or_path",),
        # Collect information about specific symbols retrieved from native modules.
        "ctypes.dlsym": ("lib_object", "name"),
        # Detect when code is accessing arbitrary memory using ctypes.
        "ctypes.cdata": ("ptr_as_int",),
        # Detects creation of mmap objects. On POSIX, access may have been
        # calculated from the prot and flags arguments.
        "mmap.__new__": ("fileno", "map_size", "access", "offset"),
        # Detect when code is accessing frames directly.
        "sys._current_frames": (),
        # Detect access to network resources. The address is unmodified from the original call.
        "socket.address": ("socket", "address"),
        # Detects URL requests.
        "urllib.Request": ("url", "data", "headers", "method"),
    }

    if event_name not in EVENTS_TO_LOG:
        return

    arg_names = EVENTS_TO_LOG[event_name]
    log_audit_event(event_name, args, arg_names)


def log_audit_event(event_name: str, args: Sequence[Any], arg_names: Sequence[str]) -> None:
    """Log a message but only log recently repeated messages at intervals."""
    arg_keys = map(lambda arg_name: f"arg.{arg_name}", arg_names)
    arg_strings = map(str, args)
    extra = dict(zip(arg_keys, arg_strings))
    logger.log(AUDIT, event_name, extra=extra)


audit_message_count = api.util.collections.LeastRecentlyUsedDict()
