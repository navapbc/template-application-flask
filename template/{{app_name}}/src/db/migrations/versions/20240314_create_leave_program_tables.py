"""create leave program tables

Revision ID: 20240314_create_leave_program_tables
Revises:
Create Date: 2024-03-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20240314_create_leave_program_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE leave_type AS ENUM ('CONTINUOUS', 'INTERMITTENT', 'REDUCED', 'STAGGERED')")
    op.execute("CREATE TYPE leave_reason AS ENUM ('PREGNANCY', 'BONDING', 'MEDICAL', 'MILITARY', 'DOMESTIC_VIOLENCE')")
    op.execute("CREATE TYPE claim_status AS ENUM ('DRAFT', 'SUBMITTED', 'PENDING', 'APPROVED', 'DENIED', 'APPEALED')")
    op.execute("CREATE TYPE payment_method AS ENUM ('DIRECT_DEPOSIT', 'CHECK')")
    op.execute("CREATE TYPE communication_preference AS ENUM ('EMAIL', 'SMS', 'PHONE', 'MAIL')")

    # Create claimant table
    op.create_table(
        "claimant",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.Text(), nullable=False),
        sa.Column("middle_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("ssn", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("phone_number", sa.Text(), nullable=False),
        sa.Column("street_address", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("zip_code", sa.Text(), nullable=False),
        sa.Column("is_id_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("payment_method", postgresql.ENUM("DIRECT_DEPOSIT", "CHECK", name="payment_method"), nullable=True),
        sa.Column("bank_account_number", sa.Text(), nullable=True),
        sa.Column("bank_routing_number", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create communication_preference table
    op.create_table(
        "communication_preference",
        sa.Column("claimant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type", postgresql.ENUM("EMAIL", "SMS", "PHONE", "MAIL", name="communication_preference"), nullable=False
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claimant_id"], ["claimant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("claimant_id", "type"),
    )

    # Create employer table
    op.create_table(
        "employer",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claimant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("ein", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("weekly_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claimant_id"], ["claimant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create claim table
    op.create_table(
        "claim",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claimant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "leave_type",
            postgresql.ENUM("CONTINUOUS", "INTERMITTENT", "REDUCED", "STAGGERED", name="leave_type"),
            nullable=False,
        ),
        sa.Column(
            "leave_reason",
            postgresql.ENUM("PREGNANCY", "BONDING", "MEDICAL", "MILITARY", "DOMESTIC_VIOLENCE", name="leave_reason"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "SUBMITTED", "PENDING", "APPROVED", "DENIED", "APPEALED", name="claim_status"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("weekly_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("weekly_benefit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_benefit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claimant_id"], ["claimant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["employer.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date >= start_date", name="check_dates_valid"),
    )

    # Create document table
    op.create_table(
        "document",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create payment table
    op.create_table(
        "payment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment_method", postgresql.ENUM("DIRECT_DEPOSIT", "CHECK", name="payment_method"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("tax_withheld", sa.Numeric(10, 2), nullable=True),
        sa.Column("other_adjustments", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create appeal table
    op.create_table(
        "appeal",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("resolution_date", sa.Date(), nullable=True),
        sa.Column("resolution_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claim.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table("appeal")
    op.drop_table("payment")
    op.drop_table("document")
    op.drop_table("claim")
    op.drop_table("employer")
    op.drop_table("communication_preference")
    op.drop_table("claimant")

    # Drop enums
    op.execute("DROP TYPE appeal_status")
    op.execute("DROP TYPE payment_method")
    op.execute("DROP TYPE claim_status")
    op.execute("DROP TYPE leave_reason")
    op.execute("DROP TYPE leave_type")
    op.execute("DROP TYPE communication_preference")
