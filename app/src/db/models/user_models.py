import enum
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.db.models.base import Base, IdMixin, TimestampMixin

logger = logging.getLogger(__name__)


class RoleType(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "user"

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        "Role", back_populates="user", cascade="all, delete", order_by="Role.type"
    )


class Role(Base, TimestampMixin):
    __tablename__ = "role"
    user_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    )

    # Set native_enum=False to use store enum values as VARCHAR/TEXT
    # With native_enum=True, alembic is unable to detect changes to the enum values and the generated
    # migrations are empty.
    # (See https://github.com/sqlalchemy/alembic/issues/278)
    #
    # Leaving create_constraint=False, since autogenerated migrations with check_constraint=True are
    # not yet functional
    # (See https://github.com/sqlalchemy/alembic/issues/363)
    #
    # https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.Enum.params.native_enum
    type: Mapped[RoleType] = mapped_column(Enum(RoleType, native_enum=False), primary_key=True)
    user: Mapped[User] = relationship(User, back_populates="roles")
