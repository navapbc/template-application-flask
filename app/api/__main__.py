#!/usr/bin/env python3

# If __main__.py is present in a Python module, it will be executed by default
# if that module is executed, e.g., `python -m my.module`.
#
# https://docs.python.org/3/library/__main__.html

import api.app
import api.logging
import api.logging.audit
from api.app_config import AppConfig
from api.util.local import load_local_env_vars

logger = api.logging.get_logger(__package__)


def main() -> None:
    load_local_env_vars()
    app_config = AppConfig()

    api.logging.audit.init_security_logging()
    api.logging.init(__package__)

    app = api.app.create_app()
    environment = app_config.environment
    host = app_config.host
    port = app_config.port

    logger.info(
        "Running API Application", extra={"environment": environment, "host": host, "port": port}
    )

    if app_config.environment == "local":
        # If python files are changed, the app will auto-reload
        # Note this doesn't have the OpenAPI yaml file configured at the moment
        app.run(host=host, port=port, use_reloader=True, reloader_type="stat")
    else:
        # Don't enable the reloader if non-local
        app.run(host=host, port=port)


main()
