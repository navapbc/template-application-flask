from apiflask import Schema, fields

from src.pagination.pagination_schema import PaginationInfoSchema


class ValidationErrorSchema(Schema):
    type = fields.String(metadata={"description": "The type of error"})
    message = fields.String(metadata={"description": "The message to return"})
    rule = fields.String(metadata={"description": "The rule that failed"})
    field = fields.String(metadata={"description": "The field that failed"})
    value = fields.String(metadata={"description": "The value that failed"})


class ResponseSchema(Schema):
    message = fields.String(metadata={"description": "The message to return"})
    data = fields.Raw(metadata={"description": "The REST resource object"}, dump_default={})
    status_code = fields.Integer(metadata={"description": "The HTTP status code"}, dump_default=200)
    warnings = fields.List(fields.Nested(ValidationErrorSchema()), dump_default=[])
    errors = fields.List(fields.Nested(ValidationErrorSchema()), dump_default=[])

    pagination_info = fields.Nested(
        PaginationInfoSchema(),
        metadata={"description": "The pagination information for paginated endpoints"},
    )
