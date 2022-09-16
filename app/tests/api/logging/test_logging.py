import json
import logging
import logging.config
import re
from contextlib import contextmanager

import pytest
from _pytest.logging import LogCaptureHandler
from flask import g

import api.logging
from api.logging.log_formatters import JsonFormatter


@pytest.fixture(autouse=True)
def reset_logging_for_pytest():
    """Reset the logging library so that later tests using caplog work correctly.

    Our logging initialization code api.util.logging.init(), which is used in many tests
    in this file, conflicts with pytest's caplog fixture.

    The result is that a test using caplog does not work if it runs after a test that uses
    api.util.logging.init(). It fails to log with "ValueError: I/O operation on closed
    file."

    This fixture resets enough of the logging configuration to make it work again.
    """

    # Copy the handlers for each logger.
    original_root_handlers = logging.root.handlers.copy()
    original_handlers = {}
    for name, logger in logging.root.manager.loggerDict.items():
        if hasattr(logger, "handlers"):
            original_handlers[name] = logger.handlers.copy()

    yield

    # Restore the handlers and enable log propagation for each logger.
    logging.root.handlers = original_root_handlers
    for name, logger in logging.root.manager.loggerDict.items():
        if hasattr(logger, "handlers"):
            logger.handlers = original_handlers.get(name, [])
        logger.propagate = True


class LogCaptureHandlerWithFormat(LogCaptureHandler):
    """
    Extends the LogCaptureHandler that already handles
    gathering log records, and additionally stores the formatted
    records so we can verify our formatting works as expected.
    """

    def __init__(self):
        super().__init__()
        self.formatted_records = []

    def emit(self, record):
        super().emit(record)
        self.formatted_records.append(self.format(record))


@contextmanager
def catch_logs(level: int, logger: logging.Logger) -> LogCaptureHandlerWithFormat:
    """Context manager that sets the level for capturing of logs.

    After the end of the 'with' statement the level is restored to its original value.

    :param level: The level.
    :param logger: The logger to update.
    """
    # See: https://github.com/pytest-dev/pytest/issues/3697
    # This works around an issue where logs without propagation don't get
    # seen by caplog by creating a handler attached directly to the logger
    handler = LogCaptureHandlerWithFormat()
    handler.formatter = JsonFormatter()  # Attach the JSON formatter so we can parse it back
    orig_level = logger.level
    logger.setLevel(level)
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.setLevel(orig_level)
        logger.removeHandler(handler)


def test_logging_init(caplog, monkeypatch):
    caplog.set_level(logging.INFO)
    # Unset formatters so caplog works correctly
    monkeypatch.setattr(logging.config, "dictConfig", lambda config: None)

    api.logging.init("test_logging_method")

    # The init method logs twice, verify both log messages are present in the expected format
    assert len(caplog.record_tuples) >= 2
    start_entry = caplog.record_tuples[0]
    invoked_as_entry = caplog.record_tuples[1]
    assert start_entry[0] == "api.logging"
    assert invoked_as_entry[0] == "api.logging"
    assert start_entry[1] == logging.INFO
    assert invoked_as_entry[1] == logging.INFO
    assert start_entry[2].startswith("start test_logging_method:")
    assert re.match(
        r"^start test_logging_method: \w+ [0-9.]+ \w+, hostname \S+, pid \d+, user \d+\(\w+\)$",
        start_entry[2],
    )
    assert re.match(r"^invoked as:", invoked_as_entry[2])


def test_log_message_with_exception():
    api.logging.init("test_logging_method")
    logger = api.logging.get_logger("api.logging.test_logging")

    with catch_logs(level=logging.INFO, logger=logger) as handler:

        try:
            raise Exception("example exception")
        except Exception:
            logger.exception(
                "test log message %s", "example_arg", extra={"key1": "value1", "key2": "value2"}
            )

        error_log_record = json.loads(handler.formatted_records[-1])

        assert error_log_record["message"] == "test log message example_arg"
        assert error_log_record["funcName"] == "test_log_message_with_exception"
        assert error_log_record["threadName"] == "MainThread"
        assert error_log_record["exc_text"].startswith("Traceback (most recent call last)")
        assert error_log_record["exc_text"].endswith("Exception: example exception")
        assert error_log_record["key1"] == "value1"
        assert error_log_record["key2"] == "value2"


def test_log_message_during_request(app, test_db_session):
    api.logging.init("test_logging_method")
    logger = api.logging.get_logger("api.logging.test_logging")

    with catch_logs(level=logging.INFO, logger=logger) as handler, app.app.test_request_context(
        "/fake-endpoint?name=Bob"
    ):
        g.db = test_db_session
        g.current_user_request_attributes = {"current_user.user_id": "abc123"}

        logger.info("this is a log message", extra={"key3": "value3", "pii_key": "123456789"})

        log_record = json.loads(handler.formatted_records[-1])
        assert log_record["funcName"] == "test_log_message_during_request"
        assert log_record["threadName"] == "MainThread"
        assert log_record["message"] == "this is a log message"
        assert log_record["request.method"] == "GET"
        assert log_record["request.path"] == "/fake-endpoint"
        assert log_record["key3"] == "value3"
        assert log_record["pii_key"] == "*********"
