import time

from sqlalchemy.orm import scoped_session

import api.logging

from . import user_models

logger = api.logging.get_logger(__name__)

__all__ = ["user_models"]


def init_lookup_tables(db_session: scoped_session) -> None:
    start_time = time.monotonic()
    user_models.sync_lookup_tables(db_session)
    logger.info("sync took %.2fs", time.monotonic() - start_time)
