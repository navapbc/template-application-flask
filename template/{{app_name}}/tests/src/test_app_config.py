import os
from unittest import mock

from src.app_config import AppConfig


@mock.patch.dict(os.environ, {"host": '192.123.123.123', "port": '5190'})
def test_app_config_sets_values_from_environment():
	app_config = AppConfig()
	assert app_config.host == '192.123.123.123'
	assert app_config.port == 5190
