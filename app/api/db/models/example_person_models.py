from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, Date, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as postgresUUID
from sqlalchemy.orm import Mapped, relationship

from .base import Base, TimestampMixin, uuid_gen


class ExamplePerson(Base, TimestampMixin):
    __tablename__ = "example_person"

    example_person_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), primary_key=True, default=uuid_gen
    )

    first_name: str = Column(Text, nullable=False)
    middle_name: Optional[str] = Column(Text)
    last_name: str = Column(Text, nullable=False)
    phone_number: str = Column(Text, nullable=False)
    date_of_birth: date = Column(Date, nullable=False)
    is_real: bool = Column(Boolean, nullable=False)

    pets: list["ExamplePet"] = relationship("ExamplePet", back_populates="pet_owner", uselist=True)


class ExamplePet(Base, TimestampMixin):
    __tablename__ = "example_pet"

    example_pet_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), primary_key=True, default=uuid_gen
    )

    name: str = Column(Text, nullable=False)
    species: str = Column(Text, nullable=False)
    pet_owner_id: Mapped[UUID] = Column(
        postgresUUID(as_uuid=True), ForeignKey("example_person.example_person_id"), index=True
    )

    pet_owner: ExamplePerson = relationship(ExamplePerson)
