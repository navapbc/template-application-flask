from typing import Type

from apiflask import fields, validators

from src.api.schemas import request_schema
from src.pagination.pagination_models import SortDirection


class PaginationSchema(request_schema.OrderedSchema):
    page_size = fields.Integer(
        required=True,
        validate=validators.Range(min=1),
        metadata={"description": "The size of the page to fetch", "example": 25},
    )
    page_offset = fields.Integer(
        required=True,
        validate=[validators.Range(min=1)],
        metadata={"description": "The page number to fetch, starts counting from 1", "example": 1},
    )


def generate_sorting_schema(
    cls_name: str, order_by_fields: list[str] | None = None
) -> Type[request_schema.OrderedSchema]:
    """
    Generate a schema that describes the sorting for a pagination endpoint.

        cls_name will be what the model is named internally by Marshmallow and what OpenAPI shows.
        order_by_fields can be a list of fields that the endpoint allows you to sort the response by

    This is functionally equivalent to specifying your own class like so:

        class MySortingSchema(request_schema.OrderedSchema):
            order_by = fields.String(
                validate=[validators.OneOf(["id","created_at","updated_at"])],
                required=True,
                metadata={"description": "The field to sort the response by"}
            )
            sort_direction = fields.Enum(
                SortDirection,
                required=True,
                by_value=True,
                metadata={"description": "Whether to sort the response ascending or descending"},
        )
    """
    if order_by_fields is None:
        order_by_fields = ["id", "created_at", "updated_at"]

    ordering_schema_fields = {
        "order_by": fields.String(
            validate=[validators.OneOf(order_by_fields)],
            required=True,
            metadata={"description": "The field to sort the response by"},
        ),
        "sort_direction": fields.Enum(
            SortDirection,
            required=True,
            by_value=True,
            metadata={"description": "Whether to sort the response ascending or descending"},
        ),
    }
    return request_schema.OrderedSchema.from_dict(ordering_schema_fields, name=cls_name)  # type: ignore


class PaginationInfoSchema(request_schema.OrderedSchema):
    # This is part of the response schema to provide all pagination information back to a user

    page_offset = fields.Integer(
        metadata={"description": "The page number that was fetched", "example": 1}
    )
    page_size = fields.Integer(
        metadata={"description": "The size of the page fetched", "example": 25}
    )
    total_records = fields.Integer(
        metadata={"description": "The total number of records fetchable", "example": 42}
    )
    total_pages = fields.Integer(
        metadata={"description": "The total number of pages that can be fetched", "example": 2}
    )
    order_by = fields.String(
        metadata={"description": "The field that the records were sorted by", "example": "id"}
    )
    sort_direction = fields.Enum(
        SortDirection,
        by_value=True,
        metadata={"description": "The direction the records are sorted"},
    )
