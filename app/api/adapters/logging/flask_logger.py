from contextvars import ContextVar
import pprint
import flask

import api.adapters.logging as logging


def init_app(app_logger: logging.Logger, app: flask.Flask) -> None:
    # Need to add filter to the handlers rather than to the logger itself, since
    # messages are passed directly to the ancestor loggers’ handlers -
    # neither the level nor filters of the ancestor loggers in question are considered.
    # See https://docs.python.org/3/library/logging.html#logging.Logger.propagate
    for handler in app_logger.handlers:
        handler.addFilter(add_app_context_attributes_to_log_record)
        handler.addFilter(add_request_context_attributes_to_log_record)

    app.before_request(lambda: log_route(app_logger))

    app_logger.info("initialized flask logger")


def log_route(logger: logging.Logger) -> None:
    assert flask.request is not None
    request = flask.request
    if request.url_rule:
        logger.info(f"{request.method} {request.url_rule}")


def add_app_context_attributes_to_log_record(record: logging.LogRecord) -> bool:
    if not flask.has_app_context():
        return record

    assert flask.current_app is not None
    record.__dict__ |= _get_app_context_attributes(flask.current_app)

    return record


def add_request_context_attributes_to_log_record(record: logging.LogRecord) -> bool:
    if not flask.has_request_context():
        return record

    assert flask.request is not None
    record.__dict__ |= _get_request_context_attributes(flask.request)

    return record


def _get_app_context_attributes(app: flask.Flask) -> dict:
    return {"app.name": app.name}


def _get_request_context_attributes(request: flask.Request) -> dict:
    return {
        "request.id": request.headers.get("x-amzn-requestid", ""),
        "request.method": request.method,
        "request.path": request.path,
        "request.url_rule": str(request.url_rule),
    }
