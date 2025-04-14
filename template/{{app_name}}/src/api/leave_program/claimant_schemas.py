from apiflask import fields, validators
from marshmallow import fields as marshmallow_fields

from src.api.schemas import request_schema
from src.db.models.leave_program import (
    CommunicationPreference,
    PaymentMethod,
)
from src.pagination.pagination_schema import PaginationSchema, generate_sorting_schema


class CommunicationPreferenceSchema(request_schema.OrderedSchema):
    type = marshmallow_fields.Enum(
        CommunicationPreference,
        by_value=True,
        metadata={"description": "The type of communication preference"},
    )


class ClaimantSchema(request_schema.OrderedSchema):
    id = fields.UUID(dump_only=True)
    first_name = fields.String(metadata={"description": "The claimant's first name"}, required=True)
    middle_name = fields.String(metadata={"description": "The claimant's middle name"})
    last_name = fields.String(metadata={"description": "The claimant's last name"}, required=True)
    date_of_birth = fields.Date(
        metadata={"description": "The claimant's date of birth"},
        required=True,
    )
    ssn = fields.String(
        required=True,
        validate=[validators.Regexp(r"^\d{3}-\d{2}-\d{4}$")],
        metadata={
            "description": "The claimant's social security number",
            "example": "123-45-6789",
        },
    )
    email = fields.Email(required=True)
    phone_number = fields.String(
        required=True,
        validate=[validators.Regexp(r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$")],
        metadata={
            "description": "The claimant's phone number",
            "example": "123-456-7890",
        },
    )

    # Address Information
    street_address = fields.String(required=True)
    city = fields.String(required=True)
    state = fields.String(required=True)
    zip_code = fields.String(
        required=True,
        validate=[validators.Regexp(r"^\d{5}(-\d{4})?$")],
        metadata={
            "description": "The claimant's zip code",
            "example": "12345-6789",
        },
    )

    # Account Settings
    is_id_verified = fields.Boolean(dump_only=True)
    communication_preferences = fields.List(
        fields.Nested(CommunicationPreferenceSchema()),
        required=True,
    )
    payment_method = fields.Enum(
        PaymentMethod,
        by_value=True,
        metadata={"description": "The claimant's preferred payment method"},
    )

    # Output only fields
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ClaimantSearchSchema(request_schema.OrderedSchema):
    # Fields that you can search for claimants by
    first_name = fields.String()
    last_name = fields.String()
    email = fields.Email()
    phone_number = fields.String(
        validate=[validators.Regexp(r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$")],
    )
    ssn = fields.String(
        validate=[validators.Regexp(r"^\d{3}-\d{2}-\d{4}$")],
    )
    is_id_verified = fields.Boolean()

    sorting = fields.Nested(generate_sorting_schema("ClaimantSortingSchema")())
    paging = fields.Nested(PaginationSchema(), required=True)
