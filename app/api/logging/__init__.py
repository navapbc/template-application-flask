import logging
import os
import platform
import pwd
import sys
from typing import Any, cast

import api.logging.config as config

logger = logging.getLogger(__name__)
_original_argv = tuple(sys.argv)


def init(program_name: str) -> None:
    # Determine which log formatter to use
    # based on the environment variable specified
    # Defaults to JSON
    config.configure_logging()

    log_program_info(program_name)


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
