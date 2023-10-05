"""Module for adding standard logging functionality to a FastAPI app.

This module configures an application's logger to add extra data
to all log messages. FastAPI application context data such as the
app name and request context data such as the request method, request url
rule, and query parameters are added to the log record.

This module also configures the FastAPI application to log every requests start and end.

Usage:
    import src.logger.fastapi_logger as fastapi_logger

    logger = logging.getLogger(__name__)
    app = create_app()

    fastapi_logger.init_app(logger, app)
"""
import logging
import time
import typing

import fastapi
import starlette_context

logger = logging.getLogger(__name__)
EXTRA_LOG_DATA_ATTR = "extra_log_data"


def init_app(app_logger: logging.Logger, app: fastapi.FastAPI) -> None:
    """Initialize the FastAPI app logger.

    Adds FastAPI app context data and FastAPI request context data
    to every log record using log filters.
    See https://docs.python.org/3/howto/logging-cookbook.html#using-filters-to-impart-contextual-information

    Also configures the app to log every non-404 request using the given logger.

    Usage:
        import src.logger.fastapi_logger as fastapi_logger

        logger = logging.getLogger(__name__)
        app = create_app()

        fastapi_logger.init_app(logger, app)
    """

    # Need to add filters to each of the handlers rather than to the logger itself, since
    # messages are passed directly to the ancestor loggers’ handlers bypassing any filters
    # set on the ancestors.
    # See https://docs.python.org/3/library/logging.html#logging.Logger.propagate
    for handler in app_logger.handlers:
        handler.addFilter(_add_request_context_info_to_log_record)

    _add_logging_middleware(app)

    logger.info("Initialized Fast API logger")


def _add_logging_middleware(app: fastapi.FastAPI) -> None:
    """
    Add middleware that runs before we start processing a request to add
    additional context to log messages and automatically log the start/end

    IMPORTANT: These are defined in the reverse-order that they execute
               as middleware work like a stack.
    """

    # Log the start/end of a request and include the timing.
    @app.middleware("http")
    async def log_start_and_end_of_request(
        request: fastapi.Request,
        call_next: typing.Callable[[fastapi.Request], typing.Awaitable[fastapi.Response]],
    ) -> fastapi.Response:
        request_start_time = time.perf_counter()

        logger.info("start request")
        response = await call_next(request)

        logger.info(
            "end request",
            extra={
                "response.status_code": response.status_code,
                "response.content_length": response.headers.get("content-length", None),
                "response.content_type": response.headers.get("content-type", None),
                "response.charset": response.charset,
                "response.time_ms": (time.perf_counter() - request_start_time) * 1000,
            },
        )
        return response

    # Add general information regarding the request (route, request ID, method) to all
    # log messages for the lifecycle of the request.
    @app.middleware("http")
    async def attach_request_context_info(
        request: fastapi.Request,
        call_next: typing.Callable[[fastapi.Request], typing.Awaitable[fastapi.Response]],
    ) -> fastapi.Response:
        # This will be added to all log messages for the rest of the request lifecycle
        data = {
            "app.name": request.app.title,
            "request.id": request.headers.get("x-amzn-requestid", ""),
            "request.method": request.method,
            "request.path": request.scope.get("path", ""),
            # Starlette does not resolve the URL rule (ie. the specific route) until after
            # middleware runs, so the url_rule cannot be added here, see: add_url_rule_to_request_context for where that happens
        }

        # Add query parameter data in the format request.query.<key> = <value>
        # For example, the query string ?foo=bar&baz=qux would be added as
        # request.query.foo = bar and request.query.baz = qux
        # PII should be kept out of the URL, as URLs are logged in access logs.
        # With that assumption, it is safe to log query parameters.
        for key, value in request.query_params.items():
            data[f"request.query.{key}"] = value

        add_extra_data_to_current_request_logs(data)

        return await call_next(request)


def add_url_rule_to_request_context(request: fastapi.Request) -> None:
    """
    Starlette, the underlying routing library that FastAPI does not determine the
    route that will handle a request until after all middleware run. This method instead
    relies on being used as a dependency (eg. FastAPI(dependencies=[Depends(add_url_rule_to_request_context)])
    which will make it always run for every route, but after all of the middlewares.

    See: https://github.com/encode/starlette/issues/685 which describes the issue in Starlette
    """
    url_rule = ""

    api_route = request.scope.get("route", None)
    if api_route:
        url_rule = api_route.path

    add_extra_data_to_current_request_logs({"request.url_rule": url_rule})


def _add_request_context_info_to_log_record(record: logging.LogRecord) -> bool:
    """Add request context data to the log record.

    If there is no request context, then do not add any data.
    """
    if not starlette_context.context.exists():
        return True

    extra_log_data: dict[str, str] = starlette_context.context.get(EXTRA_LOG_DATA_ATTR, {})
    record.__dict__.update(extra_log_data)

    return True


def add_extra_data_to_current_request_logs(
    data: dict[str, str | int | float | bool | None]
) -> None:
    """Add data to every log record for the current request."""
    assert starlette_context.context.exists(), "Must be in a request context"

    extra_log_data = starlette_context.context.get(EXTRA_LOG_DATA_ATTR, {})
    extra_log_data.update(data)
    starlette_context.context[EXTRA_LOG_DATA_ATTR] = extra_log_data
