import logging
import re

import pytest

import api.logging


@pytest.fixture
def init_logger(caplog):
    caplog.set_level(logging.DEBUG)
    api.logging.init("test_logging")
    logger = logging.getLogger("test_logging")
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
    logger = logging.getLogger(__name__)

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


def test_mask_pii(init_logger, caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger(__name__)

    logger.info("pii", extra={"foo": "bar", "tin": "123456789", "dashed-ssn": "123-45-6789"})

    assert len(caplog.records) == 1
    assert caplog.records[0].__dict__["tin"] == "*********"
    assert caplog.records[0].__dict__["dashed-ssn"] == "*********"
