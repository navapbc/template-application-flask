from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

import api.db as db
import api.logging
from api.util.local import load_local_env_vars

logger = api.logging.get_logger(__name__)


@dataclass
class ScriptContext:
    db_session: db.scoped_session


@contextmanager
def script_context_manager() -> Generator[ScriptContext, None, None]:
    """
    Context manager for running a script
    that needs to access the DB. Initializes
    a few useful components like the DB connection,
    logging, and local environment variables (if local).
    """
    load_local_env_vars()
    api.logging.init(__package__)

    # TODO - Note this is really basic, but
    # it could a good place to fetch CLI args, initialize
    # metrics (eg. New Relic) and so on in a way that
    # helps prevent so much boilerplate code.

    logger.info("Connecting to DB")
    with db.session_scope(db.init(), close=True) as db_session:
        script_context = ScriptContext(db_session)

        yield script_context

    logger.info("Script complete")
