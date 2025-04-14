import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base, IdMixin, TimestampMixin


class LeaveType(str, enum.Enum):
    CONTINUOUS = "CONTINUOUS"
    INTERMITTENT = "INTERMITTENT"
    REDUCED = "REDUCED"
    STAGGERED = "STAGGERED"


class LeaveReason(str, enum.Enum):
    PREGNANCY = "PREGNANCY"
    BONDING = "BONDING"
    MEDICAL = "MEDICAL"
    MILITARY = "MILITARY"
    DOMESTIC_VIOLENCE = "DOMESTIC_VIOLENCE"


class ClaimStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    APPEALED = "APPEALED"


class PaymentMethod(str, enum.Enum):
    DIRECT_DEPOSIT = "DIRECT_DEPOSIT"
    CHECK = "CHECK"


class CommunicationPreference(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PHONE = "PHONE"
    MAIL = "MAIL"


class Claimant(Base, IdMixin, TimestampMixin):
    __tablename__ = "claimant"

    # Personal Information
    first_name: Mapped[str]
    middle_name: Mapped[Optional[str]]
    last_name: Mapped[str]
    date_of_birth: Mapped[date]
    ssn: Mapped[str]  # Encrypted in database
    email: Mapped[str]
    phone_number: Mapped[str]

    # Address Information
    street_address: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    zip_code: Mapped[str]

    # Account Settings
    is_id_verified: Mapped[bool] = mapped_column(default=False)
    communication_preferences: Mapped[List["CommunicationPreference"]] = relationship(
        "CommunicationPreference", back_populates="claimant", cascade="all, delete"
    )
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        Enum(PaymentMethod, native_enum=False), nullable=True
    )
    bank_account_number: Mapped[Optional[str]]  # Encrypted in database
    bank_routing_number: Mapped[Optional[str]]  # Encrypted in database

    # Relationships
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="claimant", cascade="all, delete")
    employers: Mapped[List["Employer"]] = relationship("Employer", back_populates="claimant", cascade="all, delete")


class CommunicationPreference(Base, TimestampMixin):
    __tablename__ = "communication_preference"

    claimant_id: Mapped[UUID] = mapped_column(ForeignKey("claimant.id", ondelete="CASCADE"), primary_key=True)
    type: Mapped[CommunicationPreference] = mapped_column(
        Enum(CommunicationPreference, native_enum=False), primary_key=True
    )
    claimant: Mapped[Claimant] = relationship(Claimant, back_populates="communication_preferences")


class Employer(Base, IdMixin, TimestampMixin):
    __tablename__ = "employer"

    claimant_id: Mapped[UUID] = mapped_column(ForeignKey("claimant.id", ondelete="CASCADE"))
    name: Mapped[str]
    ein: Mapped[str]  # Encrypted in database
    start_date: Mapped[date]
    end_date: Mapped[Optional[date]]
    is_current: Mapped[bool]
    weekly_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    claimant: Mapped[Claimant] = relationship(Claimant, back_populates="employers")
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="employer")


class Claim(Base, IdMixin, TimestampMixin):
    __tablename__ = "claim"

    claimant_id: Mapped[UUID] = mapped_column(ForeignKey("claimant.id", ondelete="CASCADE"))
    employer_id: Mapped[UUID] = mapped_column(ForeignKey("employer.id", ondelete="CASCADE"))
    leave_type: Mapped[LeaveType] = mapped_column(Enum(LeaveType, native_enum=False))
    leave_reason: Mapped[LeaveReason] = mapped_column(Enum(LeaveReason, native_enum=False))
    start_date: Mapped[date]
    end_date: Mapped[date]
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus, native_enum=False), default=ClaimStatus.DRAFT)
    weekly_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    weekly_benefit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_benefit_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Relationships
    claimant: Mapped[Claimant] = relationship(Claimant, back_populates="claims")
    employer: Mapped[Employer] = relationship(Employer, back_populates="claims")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="claim", cascade="all, delete")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="claim", cascade="all, delete")
    appeals: Mapped[List["Appeal"]] = relationship("Appeal", back_populates="claim", cascade="all, delete")

    __table_args__ = (CheckConstraint("end_date >= start_date", name="check_dates_valid"),)


class Document(Base, IdMixin, TimestampMixin):
    __tablename__ = "document"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claim.id", ondelete="CASCADE"))
    file_name: Mapped[str]
    file_path: Mapped[str]  # Path to stored file
    file_size: Mapped[int]  # Size in bytes
    mime_type: Mapped[str]
    is_verified: Mapped[bool] = mapped_column(default=False)

    claim: Mapped[Claim] = relationship(Claim, back_populates="documents")


class Payment(Base, IdMixin, TimestampMixin):
    __tablename__ = "payment"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claim.id", ondelete="CASCADE"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payment_date: Mapped[date]
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod, native_enum=False))
    status: Mapped[str]  # e.g., "PENDING", "COMPLETED", "FAILED"
    tax_withheld: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    other_adjustments: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    claim: Mapped[Claim] = relationship(Claim, back_populates="payments")


class Appeal(Base, IdMixin, TimestampMixin):
    __tablename__ = "appeal"

    claim_id: Mapped[UUID] = mapped_column(ForeignKey("claim.id", ondelete="CASCADE"))
    reason: Mapped[str]
    status: Mapped[str]  # e.g., "PENDING", "UNDER_REVIEW", "RESOLVED"
    resolution_date: Mapped[Optional[date]]
    resolution_details: Mapped[Optional[str]]

    claim: Mapped[Claim] = relationship(Claim, back_populates="appeals")
