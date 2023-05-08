#!/usr/bin/env python3

# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import logging
import os

import src.app
import src.config
import src.logging
from src.app_config import AppConfig
from src.util.local import load_local_env_vars

logger = logging.getLogger(__package__)


def main() -> None:
    config = src.config.load(environment_name=os.getenv("ENVIRONMENT", "local"), environ=os.environ)

    app = src.app.create_app(config)
    logger.info("loaded configuration", extra={"config": config})

    all_configs = src.config.load_all()
    logger.info("loaded all", extra={"all_configs": all_configs})

    environment = config.app.environment

    # When running in a container, the host needs to be set to 0.0.0.0 so that the app can be
    # accessed from outside the container. See Dockerfile
    host = config.app.host
    port = config.app.port

    logger.info(
        "Running API Application", extra={"environment": environment, "host": host, "port": port}
    )

    if config.app.environment == "local":
        # If python files are changed, the app will auto-reload
        # Note this doesn't have the OpenAPI yaml file configured at the moment
        app.run(host=host, port=port, use_reloader=True, reloader_type="stat")
    else:
        # Don't enable the reloader if non-local
        app.run(host=host, port=port)


main()
