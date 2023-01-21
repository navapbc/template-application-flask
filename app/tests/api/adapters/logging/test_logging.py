import json
from logging import INFO, DEBUG
import re

import pytest

import api.adapters.logging as logging
from api.adapters.logging.log_formatters import JsonFormatter


@pytest.fixture
def init_logger(caplog):
    caplog.set_level(DEBUG)
    logger: logging.Logger = logging.init("test_logging")
    yield
    logger.root.handlers.clear()


@pytest.fixture
def init_json_logger(monkeypatch, caplog: pytest.LogCaptureFixture):
    caplog.set_level(DEBUG)
    logger: logging.Logger = logging.init("test_logging")
    yield
    logger.root.handlers.clear()


def test_init(init_logger, caplog: pytest.LogCaptureFixture):
    records = caplog.get_records("setup")
    assert len(records) == 2
    assert re.match(
        r"^start test_logging: \w+ [0-9.]+ \w+, hostname \S+, pid \d+, user \d+\(\w+\)$",
        records[0].message,
    )
    assert re.match(r"^invoked as:", records[1].message)


def test_log_exception(init_logger, caplog):
    logger = logging.get_logger(__name__)

    try:
        raise Exception("example exception")
    except Exception:
        logger.exception(
            "test log message %s", "example_arg", extra={"key1": "value1", "key2": "value2"}
        )

    last_record: logging.LogRecord = caplog.records[-1]

    assert last_record.message == "test log message example_arg"
    assert last_record.funcName == "test_log_exception"
    assert last_record.threadName == "MainThread"
    assert last_record.exc_text.startswith("Traceback (most recent call last)")
    assert last_record.exc_text.endswith("Exception: example exception")
    assert last_record.__dict__["key1"] == "value1"
    assert last_record.__dict__["key2"] == "value2"
