import dataclasses
from typing import Optional

import flask

from api.db.models.base import Base


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
class ApiResponse:
    """Base response model for all API responses."""

    message: str
    data: Optional[Base] = None
    status_code: int = 200
    warnings: list[ValidationErrorDetail] = dataclasses.field(default_factory=list)
    errors: list[ValidationErrorDetail] = dataclasses.field(default_factory=list)

    def as_flask_response(self) -> flask.Response:
        response = dataclasses.asdict(self)
        if self.data is not None:
            response["data"] = self.data.for_json()
        return flask.make_response(response, self.status_code)
