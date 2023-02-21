import logging
import re

import api.logging
import api.logging.formatters as formatters
import pytest


def _init_test_logger(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch, log_format="human-readable"
):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("LOG_FORMAT", log_format)
    api.logging.init("test_logging")


@pytest.fixture
def init_test_logger(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    _init_test_logger(caplog, monkeypatch)
    yield
    logging.root.handlers.clear()


@pytest.mark.parametrize(
    "log_format,expected_formatter",
    [
        ("human-readable", formatters.HumanReadableFormatter),
        ("json", formatters.JsonFormatter),
    ],
)
def test_init(caplog: pytest.LogCaptureFixture, monkeypatch, log_format, expected_formatter):
    caplog.set_level(logging.DEBUG)
    _init_test_logger(caplog, monkeypatch, log_format)

    records = caplog.records
    assert len(records) == 2
    assert re.match(
        r"^start test_logging: \w+ [0-9.]+ \w+, hostname \S+, pid \d+, user \d+\(\w+\)$",
        records[0].message,
    )
    assert re.match(r"^invoked as:", records[1].message)

    formatter_types = [type(handler.formatter) for handler in logging.root.handlers]
    assert expected_formatter in formatter_types


def test_log_exception(init_test_logger, caplog):
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


def test_mask_pii(init_test_logger, caplog: pytest.LogCaptureFixture):
    logger = logging.getLogger(__name__)

    logger.info("pii", extra={"foo": "bar", "tin": "123456789", "dashed-ssn": "123-45-6789"})

    assert len(caplog.records) == 1
    assert caplog.records[0].__dict__["tin"] == "*********"
    assert caplog.records[0].__dict__["dashed-ssn"] == "*********"
