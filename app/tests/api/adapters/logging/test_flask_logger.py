import pytest
import sys
from flask import Flask

import api.adapters.logging as logging
import api.adapters.logging.flask_logger as flask_logger


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def logger():
    logger = logging.get_logger("test")
    logger.setLevel(logging.logging.DEBUG)
    logger.addHandler(logging.logging.StreamHandler(sys.stdout))
    return logger


def test_flask_logger(app: Flask, logger: logging.Logger, caplog: pytest.LogCaptureFixture):
    flask_logger.init_app(logger, app)
    assert caplog.messages == ["initialized flask logger"]
    caplog.clear()

    @app.get("/hello/<name>")
    def hello(name):
        logging.get_logger("test.hello").info(f"hello, {name}!")
        return "ok"

    app.test_client().get("/hello/jane")

    assert caplog.messages == ["GET /hello/<name>", "hello, jane!"]
