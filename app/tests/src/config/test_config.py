#
# Tests for src.config.
#

import pydantic.error_wrappers
import pytest

from src import config
from src.config import load


def test_load_with_override():
    conf = load.load(
        environment_name="local", environ={"app_host": "test.host", "app_port": 999, "port": 888}
    )

    assert isinstance(conf, config.RootConfig)
    assert conf.app.host == "test.host"
    assert conf.app.port == 999


def test_load_with_invalid_override():
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        load.load(environment_name="local", environ={"app_port": "not_a_number"})


def test_load():
    conf = load.load(environment_name="local")

    assert isinstance(conf, config.RootConfig)
    assert conf.app.host == "127.0.0.1"


def test_load_invalid_environment_name():
    with pytest.raises(ModuleNotFoundError):
        load.load(environment_name="does_not_exist")


def test_load_all():
    """This test is important to confirm that all configurations are valid - otherwise we would
    not know until runtime in the appropriate environment."""

    all_configs = load.load_all()

    # We expect at least these configs to exist - there may be others too.
    assert all_configs.keys() >= {"local", "dev", "prod"}

    for value in all_configs.values():
        assert isinstance(value, config.RootConfig)

    # Make sure they are all different objects (prevent bugs where they overwrite by accidental
    # sharing).
    ids = {id(value) for value in all_configs.values()}
    assert len(ids) == len(all_configs)
