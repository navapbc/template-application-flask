#
# Configuration for local development environments.
#
# This file only contains overrides (differences) from the defaults in default.py.
#

import pydantic.types

from .. import default

config = default.default_config()

config.database.password = pydantic.types.SecretStr("secret123")
config.database.hide_sql_parameter_logs = False
config.logging.format = "human_readable"
config.logging.enable_audit = False
