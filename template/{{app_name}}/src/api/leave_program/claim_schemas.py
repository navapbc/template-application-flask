from apiflask import fields, validators
from marshmallow import fields as marshmallow_fields

from src.api.schemas import request_schema
from src.db.models.leave_program import (
    ClaimStatus,
    LeaveReason,
    LeaveType,
    PaymentMethod,
)
from src.pagination.pagination_schema import PaginationSchema, generate_sorting_schema


class DocumentSchema(request_schema.OrderedSchema):
    id = fields.UUID(dump_only=True)
    file_name = fields.String(required=True)
    file_size = fields.Integer(required=True)
    mime_type = fields.String(required=True)
    is_verified = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class PaymentSchema(request_schema.OrderedSchema):
    id = fields.UUID(dump_only=True)
    amount = fields.Decimal(places=2, required=True)
    payment_date = fields.Date(required=True)
    payment_method = fields.Enum(
        PaymentMethod,
        by_value=True,
        required=True,
    )
    status = fields.String(required=True)
    tax_withheld = fields.Decimal(places=2)
    other_adjustments = fields.Decimal(places=2)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AppealSchema(request_schema.OrderedSchema):
    id = fields.UUID(dump_only=True)
    reason = fields.String(required=True)
    status = fields.String(required=True)
    resolution_date = fields.Date()
    resolution_details = fields.String()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ClaimSchema(request_schema.OrderedSchema):
    id = fields.UUID(dump_only=True)
    claimant_id = fields.UUID(required=True)
    employer_id = fields.UUID(required=True)
    leave_type = fields.Enum(
        LeaveType,
        by_value=True,
        required=True,
        metadata={"description": "The type of leave being requested"},
    )
    leave_reason = fields.Enum(
        LeaveReason,
        by_value=True,
        required=True,
        metadata={"description": "The reason for the leave request"},
    )
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    status = fields.Enum(
        ClaimStatus,
        by_value=True,
        dump_only=True,
    )
    weekly_hours = fields.Decimal(
        places=2,
        required=True,
        metadata={"description": "The number of hours worked per week"},
    )
    weekly_benefit_amount = fields.Decimal(places=2)
    total_benefit_amount = fields.Decimal(places=2)

    # Relationships
    documents = fields.List(fields.Nested(DocumentSchema()))
    payments = fields.List(fields.Nested(PaymentSchema()))
    appeals = fields.List(fields.Nested(AppealSchema()))

    # Output only fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ClaimSearchSchema(request_schema.OrderedSchema):
    # Fields that you can search for claims by
    claimant_id = fields.UUID()
    employer_id = fields.UUID()
    leave_type = fields.Enum(LeaveType, by_value=True)
    leave_reason = fields.Enum(LeaveReason, by_value=True)
    status = fields.Enum(ClaimStatus, by_value=True)
    start_date = fields.Date()
    end_date = fields.Date()

    sorting = fields.Nested(generate_sorting_schema("ClaimSortingSchema")())
    paging = fields.Nested(PaginationSchema(), required=True)
