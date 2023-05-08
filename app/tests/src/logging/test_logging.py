import logging
import re

import pytest

import src.logging
import src.logging.formatters as formatters
from src.logging.config import LoggingConfig, LoggingFormat
from tests.lib.assertions import assert_dict_contains


@pytest.fixture
def init_test_logger(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    caplog.set_level(logging.DEBUG)
    logging_config = LoggingConfig(format=LoggingFormat.human_readable)
    with src.logging.init("test_logging", logging_config):
        yield


@pytest.mark.parametrize(
    "log_format,expected_formatter",
    [
        ("human_readable", formatters.HumanReadableFormatter),
        ("json", formatters.JsonFormatter),
    ],
)
def test_init(caplog: pytest.LogCaptureFixture, monkeypatch, log_format, expected_formatter):
    caplog.set_level(logging.DEBUG)
    logging_config = LoggingConfig(format=log_format)

    with src.logging.init("test_logging", logging_config):

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


@pytest.mark.parametrize(
    "args,extra,expected",
    [
        pytest.param(
            ("ssn: 123456789",),
            None,
            {"message": "ssn: *********"},
            id="pii in msg",
        ),
        pytest.param(
            ("pii",),
            {"foo": "bar", "tin": "123456789", "dashed-ssn": "123-45-6789"},
            {
                "message": "pii",
                "foo": "bar",
                "tin": "*********",
                "dashed-ssn": "*********",
            },
            id="pii in extra",
        ),
        pytest.param(
            ("%s %s", "text", "123456789"),
            None,
            {"message": "text *********"},
            id="pii in interpolation args",
        ),
    ],
)
def test_mask_pii(init_test_logger, caplog: pytest.LogCaptureFixture, args, extra, expected):
    logger = logging.getLogger(__name__)

    logger.info(*args, extra=extra)

    assert len(caplog.records) == 1
    assert_dict_contains(caplog.records[0].__dict__, expected)
