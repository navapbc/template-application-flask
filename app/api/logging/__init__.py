import logging
import os
import platform
import pwd
import sys
from typing import Any, cast

import api.logging.formatters as formatters
import api.logging.pii as pii

logger = logging.getLogger(__name__)
original_argv = tuple(sys.argv)


def init(program_name: str) -> None:
    # Determine which log formatter to use
    # based on the environment variable specified
    # Defaults to JSON
    consoleHandler = logging.StreamHandler(sys.stdout)
    formatter = get_formatter()
    consoleHandler.setFormatter(formatter)
    consoleHandler.addFilter(pii.mask_pii)
    logging.root.addHandler(consoleHandler)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.WARN)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.dialects.postgresql").setLevel(logging.INFO)

    log_program_info(program_name)


def log_program_info(program_name: str):
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
    logger.info("invoked as: %s", " ".join(original_argv))


def get_formatter() -> logging.Formatter:
    """Return the formatter used by the root logger."""
    log_format = os.getenv("LOG_FORMAT", "json")

    print("get_formatter")
    print(log_format)
    if log_format == "human-readable":
        return formatters.HumanReadableFormatter()
    return formatters.JsonFormatter()
