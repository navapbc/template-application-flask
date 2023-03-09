"""Module for initializing logging configuration for the application.

There are two formatters for the log messages: human-readable and JSON.
The formatter that is used is determined by the environment variable
LOG_FORMAT. If the environment variable is not set, the JSON formatter
is used by default. See src.logging.formatters for more information.

The logger also adds a PII mask filter to the root logger. See
src.logging.pii for more information.

Usage:
    import src.logging

    with src.logging.Log("program name"):
        ...

Once the module has been initialized, the standard logging module can be
used to log messages:

Example:
    import logging

    logger = logging.getLogger(__name__)
    logger.info("message")
"""

import logging
import os
import platform
import pwd
import sys
from typing import Any, cast

import src.logging.config as config

logger = logging.getLogger(__name__)
_original_argv = tuple(sys.argv)


class Log:
    def __init__(self, program_name: str) -> None:
        self.stream_handler = config.configure_logging()
        log_program_info(program_name)

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        logging.root.removeHandler(self.stream_handler)


def log_program_info(program_name: str) -> None:
    logger.info(
        "start %s: %s %s %s, hostname %s, pid %i, user %i(%s)",
        program_name,
        platform.python_implementation(),
        platform.python_version(),
        platform.system(),
        platform.node(),
        os.getpid(),
        os.getuid(),
        pwd.getpwuid(os.getuid()).pw_name,
        extra={
            "hostname": platform.node(),
            "cpu_count": os.cpu_count(),
            # If mypy is run on a mac, it will throw a module has no attribute error, even though
            # we never actually access it with the conditional.
            #
            # However, we can't just silence this error, because on linux (e.g. CI/CD) that will
            # throw an unused “type: ignore” comment error. Casting to Any instead ensures this
            # passes regardless of where mypy is being run
            "cpu_usable": (
                len(cast(Any, os).sched_getaffinity(0))
                if "sched_getaffinity" in dir(os)
                else "unknown"
            ),
        },
    )
    logger.info("invoked as: %s", " ".join(_original_argv))
