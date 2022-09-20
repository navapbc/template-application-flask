import time

import api.logging

from . import example_person_models, user_models

logger = api.logging.get_logger(__name__)

__all__ = ["example_person_models", "user_models"]


def init_lookup_tables(db_session):
    start_time = time.monotonic()
    user_models.sync_lookup_tables(db_session)
    logger.info("sync took %.2fs", time.monotonic() - start_time)
