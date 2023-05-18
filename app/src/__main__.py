#!/usr/bin/env python3

# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import logging
import os

from flask import Flask

import src.app
import src.config
import src.logging

logger = logging.getLogger(__package__)


def load_config() -> src.config.RootConfig:
    return src.config.load(environment_name=os.getenv("ENVIRONMENT", "local"), environ=os.environ)


def main() -> Flask:
    config = load_config()
    app = src.app.create_app(config)
    logger.info("loaded configuration", extra={"config": config})

    environment = config.app.environment

    # When running in a container, the host needs to be set to 0.0.0.0 so that the app can be
    # accessed from outside the container. See Dockerfile
    host = config.app.host
    port = config.app.port

    if __name__ != "main":
        return app

    logger.info(
        "Running API Application", extra={"environment": environment, "host": host, "port": port}
    )

    if config.app.environment == "local":
        # If python files are changed, the app will auto-reload
        # Note this doesn't have the OpenAPI yaml file configured at the moment
        app.run(
            host=host,
            port=port,
            debug=True,  # nosec B201
            load_dotenv=False,
            use_reloader=True,
            reloader_type="stat",
        )
    else:
        # Don't enable the reloader if non-local
        app.run(host=host, port=port, load_dotenv=False)

    return app


main()
