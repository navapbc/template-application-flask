"""
Configuration file for the Gunicorn server used to run the application in production environments.

Attributes:
    bind(str): The socket to bind. Formatted as '0.0.0.0:$PORT'.
    workers(int): The number of worker processes for handling requests.
    threads(int): The number of threads per worker for handling requests.

For more information, see https://docs.gunicorn.org/en/stable/configure.html
"""

import os

from src.app_config import AppConfig

app_config = AppConfig()

bind = app_config.host + ':' + str(app_config.port)
# Calculates the number of usable cores and doubles it. The recommended number
# of workers per core is two. However, adjusting task resources or number of
# workers may be necessary if they are timing out and crashing.
# https://docs.gunicorn.org/en/latest/design.html#how-many-workers
workers = len(os.sched_getaffinity(0)) * 2
threads = 4
