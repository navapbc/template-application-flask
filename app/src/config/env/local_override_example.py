#
# Local overrides for local development environments.
#
# This file allows overrides to be set that you never want to be committed.
#
# To use this, copy to `local_override.py` and edit below.
#

from .local import config

# Example override:
config.logging.enable_audit = True
