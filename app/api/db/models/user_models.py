from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as postgresUUID
from sqlalchemy.orm import Mapped, relationship, scoped_session

import api.logging
from api.db.models.lookup import LookupTable

from .base import Base, TimestampMixin, uuid_gen

logger = api.logging.get_logger(__name__)

#################################
# Lookup Tables
#################################


class LkRole(Base, TimestampMixin):
    __tablename__ = "lk_role"
    role_id: int = Column(Integer, primary_key=True, autoincrement=True)
    role_description: str = Column(Text, nullable=False)

    def __init__(self, role_id: int, role_description: str):
        self.role_id = role_id
        self.role_description = role_description


class Role(LookupTable):
    model = LkRole
    column_names = ("role_id", "role_description")

    USER = LkRole(1, "User")
    ADMIN = LkRole(2, "Admin")
    THIRD_PARTY = LkRole(3, "Third Party")


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

    roles: Optional[list["Role"]] = relationship("LkRole", secondary="link_user_role", uselist=True)


class UserRole(Base, TimestampMixin):
    __tablename__ = "link_user_role"
    user_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), ForeignKey("user.user_id"), primary_key=True
    )
    role_id: int = Column(Integer, ForeignKey("lk_role.role_id"), primary_key=True)

    user: User = relationship(User, overlaps="roles")
    role: Role = relationship(LkRole, overlaps="roles")


def sync_lookup_tables(db_session: scoped_session) -> None:
    Role.sync_to_database(db_session)
    db_session.commit()
