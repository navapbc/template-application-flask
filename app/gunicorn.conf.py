import os

from src.app_config import AppConfig

app_config = AppConfig()

bind = app_config.host + ':' + str(app_config.port)
workers = len(os.sched_getaffinity(0)) * 2