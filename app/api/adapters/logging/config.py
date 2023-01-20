from typing import Any

from api.adapters.logging.log_formatters import HumanReadableFormatter, JsonFormatter


def get_logging_config(log_format: str) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {"handlers": ["console"], "level": "INFO"},
        "formatters": {
            "json": {"()": JsonFormatter},
            "human-readable": {"()": HumanReadableFormatter},
        },
        "handlers": {
            "console": {
                # Note the formatter specified here points
                # to the formatter specified above which
                # in turn points to the format classes
                "formatter": log_format,
                "class": "logging.StreamHandler",
                "level": "INFO",
            }
        },
        "loggers": {
            "alembic": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "werkzeug": {"handlers": ["console"], "level": "WARN", "propagate": False},
            "api": {"handlers": ["console"], "level": "INFO", "propagate": False},
            # Log DB pool connection invalidations and recycle events. At DEBUG
            # level includes all connection checkin/checkouts to the pool.
            #
            # https://docs.sqlalchemy.org/en/13/core/engines.html#configuring-logging
            "sqlalchemy.pool": {"handlers": ["console"], "level": "INFO", "propagate": False},
            # Log PostgreSQL NOTICE messages
            # https://docs.sqlalchemy.org/en/13/dialects/postgresql.html#notice-logging
            "sqlalchemy.dialects.postgresql": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
