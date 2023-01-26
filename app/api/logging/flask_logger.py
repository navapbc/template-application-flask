"""Module for adding standard logging functionality to a Flask app.

This module configures an application's logger to add extra data
to all log messages. Flask application context data such as the
app name and request context data such as the request method, request url
rule, and query parameters are added to the log record.

This module also configures the Flask application to log every
non-404 request.

Usage:
    import api.logging.flask_logger as flask_logger

    logger = logging.getLogger(__name__)
    app = create_app()

    flask_logger.init_app(logger, app)
"""

import logging

import flask

EXTRA_LOG_DATA_ATTR = "extra_log_data"


def init_app(app_logger: logging.Logger, app: flask.Flask) -> None:
    """Initialize the Flask app logger.

    Adds Flask app context data and Flask request context data
    to every log record using log filters.
    See https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information

    Also configures the app to log every non-404 request using the given logger.

    Usage:
        import api.logging.flask_logger as flask_logger

        logger = logging.getLogger(__name__)
        app = create_app()

        flask_logger.init_app(logger, app)
    """
    # Need to add filters to each of the handlers rather than to the logger itself, since
    # messages are passed directly to the ancestor loggers’ handlers bypassing any filters
    # set on the ancestors.
    # See https://docs.python.org/3/library/logging.html#logging.Logger.propagate
    for handler in app_logger.handlers:
        handler.addFilter(_add_app_context_info_to_log_record)
        handler.addFilter(_add_request_context_info_to_log_record)

    # Add request context data to every log record for the current request
    # such as request id, request method, request path, and the matching Flask request url rule
    app.before_request(
        lambda: add_extra_data_to_current_request_logs(_get_request_context_info(flask.request))
    )

    # Use the app_logger to log every non-404 request before each request
    # See https://flask.palletsprojects.com/en/2.2.x/api/#flask.Flask.before_request
    app.before_request(lambda: _log_route(app_logger))

    app_logger.info("initialized flask logger")


def add_extra_data_to_current_request_logs(
    data: dict[str, str | int | float | bool | None]
) -> None:
    """Add data to every log record for the current request."""
    assert flask.has_request_context(), "Must be in a request context"

    extra_log_data = getattr(flask.g, EXTRA_LOG_DATA_ATTR, {})
    extra_log_data.update(data)
    setattr(flask.g, EXTRA_LOG_DATA_ATTR, extra_log_data)


def _log_route(logger: logging.Logger) -> None:
    """Log the route that is being requested.

    If there is no matching route, then do not log anything.
    """
    assert flask.request is not None
    request = flask.request
    if request.url_rule:
        logger.info(f"{request.method} {request.url_rule}")
    else:
        logger.info(f"{request.method} {request.path}")


def _add_app_context_info_to_log_record(record: logging.LogRecord) -> bool:
    """Add app context data to the log record.

    If there is no app context, then do not add any data.
    """
    if not flask.has_app_context():
        return True

    assert flask.current_app is not None
    record.__dict__ |= _get_app_context_info(flask.current_app)

    return True


def _add_request_context_info_to_log_record(record: logging.LogRecord) -> bool:
    """Add request context data to the log record.

    If there is no request context, then do not add any data.
    """
    if not flask.has_request_context():
        return True

    assert flask.request is not None
    extra_log_data: dict[str, str] = getattr(flask.g, EXTRA_LOG_DATA_ATTR, {})
    record.__dict__.update(extra_log_data)

    return True


def _get_app_context_info(app: flask.Flask) -> dict:
    return {"app.name": app.name}


def _get_request_context_info(request: flask.Request) -> dict:
    data = {
        "request.id": request.headers.get("x-amzn-requestid", ""),
        "request.method": request.method,
        "request.path": request.path,
        "request.url_rule": str(request.url_rule),
    }

    # Add query parameter data in the format request.query.<key> = <value>
    # For example, the query string ?foo=bar&baz=qux would be added as
    # request.query.foo = bar and request.query.baz = qux
    # PII should be kept out of the URL, as URLs are logged in access logs.
    # With that assumption, it is safe to log query parameters.
    for key, value in request.args.items():
        data[f"request.query.{key}"] = value
    return data
