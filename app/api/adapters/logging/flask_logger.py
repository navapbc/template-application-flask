import flask

import api.adapters.logging as logging


def init_app(app: flask.Flask) -> None:
    logging.get_logger(__name__).addFilter(AppContextFilter())
    logging.get_logger(__name__).addFilter(RequestContextFilter())


class AppContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not flask.has_app_context():
            return True

        assert flask.current_app is not None
        record.__dict__ |= _get_app_context_attributes(flask.current_app)

        return True


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not flask.has_request_context():
            return True

        assert flask.request is not None
        record.__dict__ |= _get_request_context_attributes(flask.request)

        return True


def _get_app_context_attributes(app: flask.Flask) -> dict:
    return {"app.name": app.name}


def _get_request_context_attributes(request: flask.Request) -> dict:
    return {
        "request.id": request.headers.get("x-amzn-requestid", ""),
        "request.method": request.method,
        "request.path": request.path,
        "request.url_rule": request.url_rule,
    }
