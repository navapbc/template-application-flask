#!/usr/bin/env python3

# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import api.app
import api.logging
from api.app_config import AppConfig
from api.util.local import load_local_env_vars

logger = api.logging.get_logger(__package__)


def main() -> None:
    load_local_env_vars()
    app_config = AppConfig()

    api.logging.init(__package__)
    logger.info("Running API Application")

    app = api.app.create_app()

    if app_config.environment == "local":
        # If python files are changed, the app will auto-reload
        # Note this doesn't have the OpenAPI yaml file configured at the moment
        app.run(port=8080, use_reloader=True, reloader_type="stat")
    else:
        # Don't enable the reloader if non-local
        app.run(port=8080)


main()
