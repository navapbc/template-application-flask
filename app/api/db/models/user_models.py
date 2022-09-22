import enum
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as postgresUUID
from sqlalchemy.orm import Mapped, relationship

import api.logging

from .base import Base, TimestampMixin, uuid_gen

logger = api.logging.get_logger(__name__)


class RoleEnum(str, enum.Enum):
    USER = "User"
    ADMIN = "Admin"
    THIRD_PARTY = "Third Party"


class User(Base, TimestampMixin):
    __tablename__ = "user"

    user_id: Mapped[UUID] = Column(postgresUUID(as_uuid=True), primary_key=True, default=uuid_gen)

    first_name: str = Column(Text, nullable=False)
    middle_name: Optional[str] = Column(Text)
    last_name: str = Column(Text, nullable=False)
    phone_number: str = Column(Text, nullable=False)
    date_of_birth: date = Column(Date, nullable=False)
    is_active: bool = Column(Boolean, nullable=False)

    roles: Optional[list["UserRole"]] = relationship(
        "UserRole", uselist=True, back_populates="user"
    )


class UserRole(Base, TimestampMixin):
    __tablename__ = "user_role"
    user_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True
    )
    role_description: str = Column(Text, primary_key=True, nullable=False, index=True)

    user: User = relationship(User, back_populates="roles")
