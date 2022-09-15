from dataclasses import asdict, dataclass
from typing import Any, Optional, Type

import flask
from werkzeug.exceptions import HTTPException


@dataclass
class ValidationErrorDetail:
    type: str  # In the Mass code this is an enum, but lets keep it basic here
    message: str = ""
    rule: Optional[str] = None  # Also an enum in Mass
    field: Optional[str] = None
    value: Optional[str] = None  # Do not store PII data here, as it gets logged in some cases


class ValidationException(Exception):
    __slots__ = ["errors", "message", "data"]

    def __init__(
        self,
        errors: list[ValidationErrorDetail],
        message: str = "Invalid request",
        data: Optional[dict | list[dict]] = None,
    ):
        self.errors = errors
        self.message = message
        self.data = data or {}


@dataclass
class Response:
    status_code: int
    message: str
    data: None | dict | list[dict]
    warnings: Optional[list[ValidationErrorDetail]] = None
    errors: Optional[list[ValidationErrorDetail]] = None

    def to_dict(self) -> dict[str, Any]:
        return exclude_none(asdict(self))

    def to_api_response(self) -> flask.Response:
        return flask.make_response(flask.jsonify(self.to_dict()), self.status_code)


def exclude_none(obj: Any) -> Any:
    if not isinstance(obj, dict):
        return obj
    clean = {}
    for k, v in obj.items():
        if "data" == k:  # defer none exclusion of data payload to service layer
            clean[k] = v
        elif isinstance(v, dict):
            nested = exclude_none(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
        elif isinstance(v, list):
            clean[k] = list(map(exclude_none, v))
        elif v is not None:
            clean[k] = v
    return clean


def success_response(
    message: str,
    data: None | dict | list[dict] = None,
    warnings: Optional[list[ValidationErrorDetail]] = None,
    status_code: int = 200,
) -> Response:
    return Response(status_code=status_code, message=message, data=data, warnings=warnings)


def error_response(
    status_code: HTTPException | Type[HTTPException],
    message: str,
    errors: list[ValidationErrorDetail],
    data: Optional[dict | list[dict]] = None,
    warnings: Optional[list[ValidationErrorDetail]] = None,
) -> Response:
    code = status_code.code if status_code.code is not None else 400
    return Response(status_code=code, message=message, errors=errors, data=data, warnings=warnings)
