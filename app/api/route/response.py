import dataclasses
from typing import Any, Optional, Type

import flask
from werkzeug.exceptions import HTTPException

from api.route.models.base_api_model import BaseApiModel


@dataclasses.dataclass
class ValidationErrorDetail:
    type: str
    message: str = ""
    rule: Optional[str] = None
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


@dataclasses.dataclass
class Response:
    status_code: int
    message: str
    data: Optional[dict | list[dict] | BaseApiModel]
    warnings: list[ValidationErrorDetail] = dataclasses.field(default_factory=list)
    errors: list[ValidationErrorDetail] = dataclasses.field(default_factory=list)


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
    data: None | BaseApiModel = None,
    warnings: Optional[list[ValidationErrorDetail]] = None,
    status_code: int = 200,
) -> flask.Response:
    response_object = Response(
        status_code=status_code, message=message, data=data, warnings=warnings or []
    )
    return flask.make_response(dataclasses.asdict(response_object), status_code)


def error_response(
    status_code: HTTPException | Type[HTTPException],
    message: str,
    errors: list[ValidationErrorDetail],
    data: Optional[dict | list[dict]] = None,
    warnings: Optional[list[ValidationErrorDetail]] = None,
) -> flask.Response:
    code = status_code.code if status_code.code is not None else 400
    response_object = Response(
        status_code=code, message=message, errors=errors or [], data=data, warnings=warnings or []
    )
    return flask.make_response(dataclasses.asdict(response_object), code)
