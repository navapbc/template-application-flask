# Logging

This application uses the standard [Python logging library](https://docs.python.org/3/library/logging.config.html) with a few configurational updates in order to be easier to work with.

## Configurations
Log configurations can be found in [logging/__init__.py](/app/api/logging/__init__.py). Sevaral `loggers` are defined which adjust the log level of various libraries we depend on.

### Formatting
We have two separate ways of formatting the logs which are controlled by the `LOG_FORMAT` environment variable.

`json` (default) -> Produces JSON formatted logs which are machine-readable.
```json
{
    "name":"api.route.healthcheck",
    "levelname":"INFO",
    "funcName":"healthcheck_get",
    "created":"1663261542.0465896",
    "thread":"275144058624",
    "threadName":"Thread-2 (process_request_thread)",
    "process":"16",
    "message":"GET /v1/healthcheck",
    "request.method":"GET",
    "request.path":"/v1/healthcheck",
    "request.url_rule":"/v1/healthcheck",
    "request_id":""
}
```

`human-readable` -> Produces log messages with color formatting that are easier to parse.
TODO - add image once the new example endpoint is created.