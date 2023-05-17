#
# Configuration for local development environments.
#
# This file only contains overrides (differences) from the defaults in default.py.
#

import pydantic.types

from .. import default
from src.logging.config import LoggingFormat

config = default.default_config()

config.database.password = pydantic.types.SecretStr("secret123")
config.database.hide_sql_parameter_logs = False
config.database.sslmode = "prefer"
config.logging.format = LoggingFormat.human_readable
config.logging.enable_audit = False
