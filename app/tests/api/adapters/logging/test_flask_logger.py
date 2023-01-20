import pytest
import sys
from flask import Flask

import api.adapters.logging as logging
import api.adapters.logging.flask_logger as flask_logger


@pytest.fixture
def logger(caplog):
    logger = logging.get_logger("test")
    logger.setLevel(logging.logging.DEBUG)
    logger.addHandler(logging.logging.StreamHandler(sys.stdout))
    yield logger
    caplog.clear()


@pytest.fixture
def app(logger):
    app = Flask("test_app_name")

    @app.get("/hello/<name>")
    def hello(name):
        logging.get_logger("test.hello").info(f"hello, {name}!")
        return "ok"

    flask_logger.init_app(logger, app)
    return app


def test_log_route(app: Flask, logger: logging.Logger, caplog: pytest.LogCaptureFixture):
    app.test_client().get("/hello/jane")

    # Assert that the log messages are present
    # There should be the route log message that is logged in the before_request handler
    # as part of every request, followed by the log message in the route handler itself.

    assert caplog.messages == ["GET /hello/<name>", "hello, jane!"]


def test_app_context_extra_attributes(
    app: Flask, logger: logging.Logger, caplog: pytest.LogCaptureFixture
):
    # Assert that the extra attributes related to the request context are present in all log records
    expected_extra = {
        "request.id": "",
        "request.method": "GET",
        "request.path": "/hello/jane",
        "request.url_rule": "/hello/<name>",
    }

    app.test_client().get("/hello/jane")

    assert len(caplog.records) == 2
    for record in caplog.records:
        _assert_dict_contains(record.__dict__, expected_extra)


def test_request_context_extra_attributes(
    app: Flask, logger: logging.Logger, caplog: pytest.LogCaptureFixture
):
    # Assert that extra attributes related to the app context are present in all log records
    expected_extra = {"app.name": "test_app_name"}

    app.test_client().get("/hello/jane")

    assert len(caplog.records) == 2
    for record in caplog.records:
        _assert_dict_contains(record.__dict__, expected_extra)


def _assert_dict_contains(d: dict, expected: dict) -> None:
    """Assert that d contains all the key-value pairs in expected.
    Do this by checking to see if adding `expected` to `d` leaves `d` unchanged.
    """
    assert d | expected == d
