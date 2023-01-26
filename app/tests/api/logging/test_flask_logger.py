import logging
import sys

import pytest
from flask import Flask

import api.logging.flask_logger as flask_logger
from tests.lib.assertions import assert_dict_contains


@pytest.fixture
def logger():
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger


@pytest.fixture
def app(logger):
    app = Flask("test_app_name")

    @app.get("/hello/<name>")
    def hello(name):
        logging.getLogger("test.hello").info(f"hello, {name}!")
        return "ok"

    flask_logger.init_app(logger, app)
    return app


@pytest.mark.parametrize(
    "route,expected_messages",
    [
        ("/hello/jane", ["GET /hello/<name>", "hello, jane!"]),
        ("/notfound", ["GET /notfound"]),
    ],
)
def test_log_route(
    app: Flask, logger: logging.Logger, caplog: pytest.LogCaptureFixture, route, expected_messages
):
    app.test_client().get(route)

    # Assert that the log messages are present
    # There should be the route log message that is logged in the before_request handler
    # as part of every request, followed by the log message in the route handler itself.

    assert caplog.messages == expected_messages


def test_app_context_extra_attributes(app: Flask, caplog: pytest.LogCaptureFixture):
    # Assert that extra attributes related to the app context are present in all log records
    expected_extra = {"app.name": "test_app_name"}

    app.test_client().get("/hello/jane")

    assert len(caplog.records) == 2
    for record in caplog.records:
        assert_dict_contains(record.__dict__, expected_extra)


def test_request_context_extra_attributes(app: Flask, caplog: pytest.LogCaptureFixture):
    # Assert that the extra attributes related to the request context are present in all log records
    expected_extra = {
        "request.id": "",
        "request.method": "GET",
        "request.path": "/hello/jane",
        "request.url_rule": "/hello/<name>",
        "request.query.up": "high",
        "request.query.down": "low",
    }

    app.test_client().get("/hello/jane?up=high&down=low")

    assert len(caplog.records) == 2
    for record in caplog.records:
        assert_dict_contains(record.__dict__, expected_extra)
