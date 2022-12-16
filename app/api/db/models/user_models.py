import enum
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship

import api.logging

from api.db.models.base import Base, IdMixin, TimestampMixin

logger = api.logging.get_logger(__name__)


class RoleType(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "user"

    first_name: str = Column(Text, nullable=False)
    middle_name: Optional[str] = Column(Text)
    last_name: str = Column(Text, nullable=False)
    phone_number: str = Column(Text, nullable=False)
    date_of_birth: date = Column(Date, nullable=False)
    is_active: bool = Column(Boolean, nullable=False)

    roles: Optional[list["Role"]] = relationship("Role", back_populates="user")


class Role(Base, TimestampMixin):
    __tablename__ = "role"
    user_id: Mapped[UUID] = Column(
        postgresql.UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True
    )
    # Set native_enum=False to use store enum values as VARCHAR/TEXT.
    # This is more convenient and avoids needing create a new migration
    # when adding a new enum value.
    # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.Enum.params.native_enum
    # https://medium.com/swlh/postgresql-3-ways-to-replace-enum-305861e089bc
    type: RoleType = Column(Enum(RoleType, native_enum=False), primary_key=True)
    user: User = relationship(User, back_populates="roles")
