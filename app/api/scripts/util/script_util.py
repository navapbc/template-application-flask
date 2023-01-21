# TODO use built in @flask.cli commands so that we can reuse flask app and no longer need this file
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

import api.adapters.db as db
import logging
from api.util.local import load_local_env_vars

logger = logging.getLogger(__name__)


@dataclass
class ScriptContext:
    db_session: db.Session


# TODO remove
@contextmanager
def script_context_manager() -> Generator[ScriptContext, None, None]:
    """
    Context manager for running a script
    that needs to access the DB. Initializes
    a few useful components like the DB connection,
    logging, and local environment variables (if local).
    """
    load_local_env_vars()
    logging.init(__package__)

    # TODO - Note this is really basic, but
    # it could a good place to fetch CLI args, initialize
    # metrics (eg. New Relic) and so on in a way that
    # helps prevent so much boilerplate code.

    db_client = db.init()
    db_client.check_db_connection()
    with db_client.get_session() as db_session:
        script_context = ScriptContext(db_session)
        yield script_context
    logger.info("Script complete")
