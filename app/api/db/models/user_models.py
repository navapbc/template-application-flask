from datetime import date
from typing import Optional
from uuid import UUID
import enum
from sqlalchemy import Boolean, Column, Date, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as postgresUUID
from sqlalchemy.orm import Mapped, relationship, scoped_session

import api.logging
from api.db.models.lookup import LookupTable

from .base import Base, TimestampMixin, uuid_gen

logger = api.logging.get_logger(__name__)

#################################
# Lookup Tables
#################################

class RoleEnum(enum.Enum):
    USER = 1
    ADMIN = 2
    THIRD_PARTY = 3
    FOURTH_ONE = 4



#################################
# Model Tables
#################################


class User(Base, TimestampMixin):
    __tablename__ = "user"

    user_id: Mapped[UUID] = Column(postgresUUID(as_uuid=True), primary_key=True, default=uuid_gen)

    first_name: str = Column(Text, nullable=False)
    middle_name: Optional[str] = Column(Text)
    last_name: str = Column(Text, nullable=False)
    phone_number: str = Column(Text, nullable=False)
    date_of_birth: date = Column(Date, nullable=False)
    is_active: bool = Column(Boolean, nullable=False)

    roles: Optional[list[RoleEnum]] = relationship("LkRole", secondary="link_user_role", uselist=True)

    primary_role: RoleEnum = Column(Enum(RoleEnum))
    another: RoleEnum = Column(Enum(RoleEnum))


class UserRole(Base, TimestampMixin):
    __tablename__ = "link_user_role"
    user_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True
    )

    user: User = relationship(User, overlaps="roles")
    role: RoleEnum = Column(Enum(RoleEnum))


def sync_lookup_tables(db_session: scoped_session) -> None:
    Role.sync_to_database(db_session)
    db_session.commit()
