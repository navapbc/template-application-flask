from datetime import date

import faker

from api.db.models.example_person_models import ExamplePerson

fake = faker.Faker()

base_request = {
    "first_name": fake.first_name(),
    "middle_name": fake.first_name(),
    "last_name": fake.last_name(),
    "date_of_birth": "2022-01-01",
    "phone_number": "123-456-7890",
    "is_real": False,
    "pets": [{"name": "Spot", "species": "Dog"}, {"name": "Fluffy", "species": "Cat"}],
}


def validate_all_match(key, request, response, db_record):
    req_val = request[key]
    response_val = response[key]
    db_val = getattr(db_record, key)

    if isinstance(db_val, date):
        db_val = db_val.isoformat()

    assert req_val == response_val
    assert req_val == db_val


def test_post_example_person_201(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post("/v1/example-person", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 201

    results = test_db_session.query(ExamplePerson).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the request, response and DB model values all match
    validate_all_match("first_name", request, response_record, db_record)
    validate_all_match("middle_name", request, response_record, db_record)
    validate_all_match("last_name", request, response_record, db_record)
    validate_all_match("date_of_birth", request, response_record, db_record)
    validate_all_match("phone_number", request, response_record, db_record)
    validate_all_match("is_real", request, response_record, db_record)

    # Verify the pets portion of the object also matches
    request_pets = request["pets"]
    response_pets = response_record["pets"]
    db_pets = db_record.pets
    assert len(request_pets) == len(response_pets) == len(db_pets)

    validate_all_match("name", request_pets[0], response_pets[0], db_pets[0])
    validate_all_match("species", request_pets[0], response_pets[0], db_pets[0])
    validate_all_match("name", request_pets[1], response_pets[1], db_pets[1])
    validate_all_match("species", request_pets[1], response_pets[1], db_pets[1])


def test_post_example_person_201_empty_array(client, api_auth_token, test_db_session):
    request = base_request | {"pets": []}
    response = client.post("/v1/example-person", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 201

    results = test_db_session.query(ExamplePerson).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the pets portion of the object also matches
    request_pets = request["pets"]
    response_pets = response_record["pets"]
    db_pets = db_record.pets
    assert 0 == len(request_pets) == len(response_pets) == len(db_pets)


def test_post_example_person_400_missing_required_fields(client, api_auth_token, test_db_session):
    # Send an empty post - should fail validation
    response = client.post("/v1/example-person", json={}, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    required_fields = ["first_name", "last_name", "phone_number", "date_of_birth", "is_real"]
    assert len(error_list) == len(
        required_fields
    ), f"Errored fields don't match expected for empty request {error_list}"
    for error in error_list:
        field, message, error_type = error["field"], error["message"], error["type"]
        assert field in required_fields
        assert "Field required" in message
        assert error_type == "value_error.missing"

    # Nothing added to DB
    results = test_db_session.query(ExamplePerson).all()
    assert len(results) == 0


def test_post_example_person_400_invalid_types(client, api_auth_token, test_db_session):
    request = {
        "first_name": 1,
        "middle_name": 2,
        "last_name": 3,
        "date_of_birth": 4,
        "phone_number": 5,
        "is_real": 6,
        "pets": 7,
    }
    response = client.post("/v1/example-person", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    # We expect the errors to be in a dict like:
    # {
    #   'field': 'first_name',
    #   'message': "1 is not of type 'string'",
    #   'rule': 'string',
    #   'type': 'type',
    #   'value': 'int'
    # }
    for error in error_list:
        field, message, error_type, incorrect_type = (
            error["field"],
            error["message"],
            error["type"],
            error["value"],
        )
        assert field in request
        assert "is not of type" in message
        assert error_type == "type"
        assert incorrect_type == str(type(request[field]).__name__)

    # Nothing added to DB
    results = test_db_session.query(ExamplePerson).all()
    assert len(results) == 0


def test_post_example_person_400_invalid_enums(client, api_auth_token, test_db_session):
    # Make the pet species a disallowed one
    request = base_request | {}
    request["pets"][0]["species"] = "Giraffe"
    request["pets"][1]["species"] = "Moth"

    response = client.post("/v1/example-person", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    # We expect the errors to be in a dict like:
    # {
    #   'field': 'pets.0.species',
    #   'message': "'Giraffe' is not one of ['Dog', 'Cat', 'Bird', 'Fish']",
    #   'rule': ['Dog', 'Cat', 'Bird', 'Fish'],
    #   'type': 'enum',
    #   'value': 'Giraffe'
    # }
    for error in error_list:
        field, message, error_type = (
            error["field"],
            error["message"],
            error["type"],
        )

        assert field.startswith("pets.") and field.endswith(".species")
        assert "is not one of" in message
        assert error_type == "enum"


def test_post_example_person_401_unauthorized_token(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post(
        "/v1/example-person", json=request, headers={"X-Auth": "incorrect token"}
    )
    assert response.status_code == 401

    # Verify the error message
    assert (
        "The server could not verify that you are authorized to access the URL requested"
        in response.get_json()["message"]
    )
