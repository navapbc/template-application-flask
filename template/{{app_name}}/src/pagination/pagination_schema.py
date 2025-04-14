from typing import Any, Type

from apiflask import fields
from marshmallow import Schema


class PaginationSchema(Schema):
    """Schema for pagination parameters"""

    page = fields.Integer(
        required=True,
        validate=lambda x: x > 0,
        metadata={"description": "Page number (1-based)"},
    )
    page_size = fields.Integer(
        required=True,
        validate=lambda x: x > 0,
        metadata={"description": "Number of items per page"},
    )
    sort_by = fields.String(
        required=True,
        metadata={"description": "Field to sort by"},
    )
    sort_order = fields.String(
        required=True,
        validate=lambda x: x.lower() in ["asc", "desc"],
        metadata={"description": "Sort order (asc or desc)"},
    )


def generate_sorting_schema(schema_name: str) -> Type[Schema]:
    """
    Generate a schema for sorting parameters

    Args:
        schema_name: Name of the schema to generate

    Returns:
        A marshmallow Schema class for sorting parameters
    """

    class SortingSchema(Schema):
        field = fields.String(
            required=True,
            metadata={"description": "Field to sort by"},
        )
        order = fields.String(
            required=True,
            validate=lambda x: x.lower() in ["asc", "desc"],
            metadata={"description": "Sort order (asc or desc)"},
        )

    SortingSchema.__name__ = schema_name
    return SortingSchema


class PaginationInfoSchema(request_schema.OrderedSchema):
    # This is part of the response schema to provide all pagination information back to a user

    page_offset = fields.Integer(metadata={"description": "The page number that was fetched", "example": 1})
    page_size = fields.Integer(metadata={"description": "The size of the page fetched", "example": 25})
    total_records = fields.Integer(metadata={"description": "The total number of records fetchable", "example": 42})
    total_pages = fields.Integer(
        metadata={"description": "The total number of pages that can be fetched", "example": 2}
    )
    order_by = fields.String(metadata={"description": "The field that the records were sorted by", "example": "id"})
    sort_direction = fields.Enum(
        SortDirection,
        by_value=True,
        metadata={"description": "The direction the records are sorted"},
    )
