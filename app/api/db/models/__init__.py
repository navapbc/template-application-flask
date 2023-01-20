import api.adapters.logging

from . import base, user_models

logger = api.adapters.logging.get_logger(__name__)

# Re-export metadata
# This is used by tests to create the test database.
metadata = base.metadata

__all__ = ["metadata", "user_models"]
