from typing import Any

import marshmallow
from apiflask import fields


class ValidationErrorSchema(marshmallow.Schema):
    type = fields.String(description="The type of error")
    message = fields.String(description="The message to return")
    rule = fields.String(description="The rule that failed")
    field = fields.String(description="The field that failed")
    value = fields.String(description="The value that failed")


class ResponseSchema(marshmallow.Schema):
    message = fields.String(description="The message to return")
    data = fields.Field(description="The REST resource object", dump_default={})
    status_code = fields.Integer(description="The HTTP status code", dump_default=200)
    warnings = fields.List(fields.Nested(ValidationErrorSchema), dump_default=[])
    errors = fields.List(fields.Nested(ValidationErrorSchema), dump_default=[])
