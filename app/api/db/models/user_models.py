import enum
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, ForeignKey, Text, Enum
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

import api.logging

from . import base

logger = api.logging.get_logger(__name__)


class RoleType(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(base.BaseModel, base.IdMixin, base.TimestampMixin):
    __tablename__ = "user"

    first_name: str = Column(Text, nullable=False)
    middle_name: Optional[str] = Column(Text)
    last_name: str = Column(Text, nullable=False)
    phone_number: str = Column(Text, nullable=False)
    date_of_birth: date = Column(Date, nullable=False)
    is_active: bool = Column(Boolean, nullable=False)

    role_assignments: Optional[list["Role"]] = relationship("RoleAssignment", back_populates="user")


class Role(base.BaseModel, base.TimestampMixin):
    __tablename__ = "role_assignment"
    user_id: Mapped[UUID] = Column(
        postgresql.UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    # Set native_enum=False to use store enum values as VARCHAR/TEXT.
    # This is more convenient and avoids needing create a new migration
    # when adding a new enum value.
    # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.Enum.params.native_enum
    # https://medium.com/swlh/postgresql-3-ways-to-replace-enum-305861e089bc
    type: str = Column(Enum(RoleType, native_enum=False), primary_key=True)
    user: User = relationship(User, back_populates="role_assignments")
