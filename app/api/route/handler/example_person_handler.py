from datetime import date
from typing import Optional
from uuid import uuid4

from pydantic import UUID4

import api.logging
from api.db.models.example_person_models import ExamplePerson, ExamplePet
from api.route.api_context import ApiContext
from api.route.request import BaseRequestModel

logger = api.logging.get_logger(__name__)


class ExamplePetParams(BaseRequestModel):
    example_pet_id: Optional[UUID4]
    name: str
    species: str


class ExamplePersonParams(BaseRequestModel):
    example_person_id: Optional[UUID4]
    first_name: str
    middle_name: Optional[str]
    last_name: str
    phone_number: str
    date_of_birth: date
    is_real: bool
    pets: Optional[list[ExamplePetParams]]


class ExamplePersonResponse(ExamplePersonParams):
    pass


def create_example_person(api_context: ApiContext) -> ExamplePersonResponse:
    request = ExamplePersonParams.parse_obj(api_context.request_body)

    example_pets = []
    if request.pets:
        for pet in request.pets:
            example_pets.append(
                ExamplePet(example_pet_id=uuid4(), name=pet.name, species=pet.species)
            )

    example_person = ExamplePerson(
        example_person_id=uuid4(),
        first_name=request.first_name,
        middle_name=request.middle_name,
        last_name=request.last_name,
        phone_number=request.phone_number,
        date_of_birth=request.date_of_birth,
        pets=example_pets,
        is_real=request.is_real,
    )
    api_context.db_session.add(example_person)

    return ExamplePersonResponse.from_orm(example_person)
