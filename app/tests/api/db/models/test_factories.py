from datetime import date

import pytest

from api.db.models.example_person_models import ExamplePet
from api.db.models.factories import ExamplePersonFactory, ExamplePetFactory

pet_params = {"name": "Spot", "species": "Dog"}

person_params = {
    "first_name": "Alvin",
    "middle_name": "Bob",
    "last_name": "Chester",
    "phone_number": "999-999-9999",
    "date_of_birth": date(2022, 1, 1),
    "is_real": False,
}


def validate_pet_record(pet, pet_expected_values=None, person_expected_values=None):
    # Grab the JSON of the record for easy access
    if pet_expected_values:
        pet_json = pet.for_json()
        assert pet.example_pet_id is not None
        for k, v in pet_expected_values.items():
            assert str(pet_json[k]) == str(v)

        if person_expected_values:
            person_json = pet.pet_owner.for_json()
            assert pet.pet_owner.example_person_id is not None
            for k, v in person_expected_values.items():
                assert str(person_json[k]) == str(v)
    else:
        # Otherwise just validate the values are set
        assert pet.example_pet_id is not None
        assert pet.name is not None
        assert pet.species is not None

        assert pet.pet_owner is not None
        assert pet.pet_owner.first_name is not None
        assert pet.pet_owner.last_name is not None
        assert pet.pet_owner.phone_number is not None
        assert pet.pet_owner.date_of_birth is not None
        assert pet.pet_owner.is_real is not None


def test_example_pet_factory_build():
    # Build doesn't use the DB

    # Build sets the values
    pet = ExamplePetFactory.build()
    validate_pet_record(pet)

    pet_owner = ExamplePersonFactory.build(**person_params)
    pet = ExamplePetFactory.build(**(pet_params | {"pet_owner": pet_owner}))
    validate_pet_record(pet, pet_params, person_params)


def test_factory_create_uninitialized_db_session(test_db_session):
    # DB factory access is disabled from tests unless you add the
    # 'initialize_factories_session' fixture.
    with pytest.raises(Exception, match="DB_FACTORIES_DISABLE_DB_ACCESS is set"):
        ExamplePetFactory.create()


def test_example_pet_factory_create(test_db_session, initialize_factories_session):
    # Create actually writes a record to the DB when run
    # so we'll check the DB directly as well.
    pet = ExamplePetFactory.create()
    validate_pet_record(pet)

    db_record = (
        test_db_session.query(ExamplePet)
        .filter(ExamplePet.example_pet_id == pet.example_pet_id)
        .one_or_none()
    )
    # Make certain the DB record matches the factory one.
    validate_pet_record(db_record, pet.for_json())

    pet_owner = ExamplePersonFactory.create(**person_params)
    pet = ExamplePetFactory.create(**(pet_params | {"pet_owner": pet_owner}))
    validate_pet_record(pet, pet_params, person_params)

    db_record = (
        test_db_session.query(ExamplePet)
        .filter(ExamplePet.example_pet_id == pet.example_pet_id)
        .one_or_none()
    )
    # Make certain the DB record matches the factory one.
    validate_pet_record(db_record, pet.for_json(), pet.pet_owner.for_json())

    # Make certain nullable fields can be overriden
    null_params = {"middle_name": None}
    pet_owner = ExamplePersonFactory.create(**null_params)
    pet = ExamplePetFactory.create(**(pet_params | {"pet_owner": pet_owner}))
    validate_pet_record(pet, pet_params, null_params)

    all_db_records = test_db_session.query(ExamplePet).all()
    assert len(all_db_records) == 3
