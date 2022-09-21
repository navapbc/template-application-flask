from datetime import date
import faker
from api.db.models.base import Base

from api.db.models.user_models import User

fake = faker.Faker()

base_request = {
    "first_name": fake.first_name(),
    "middle_name": fake.first_name(),
    "last_name": fake.last_name(),
    "date_of_birth": "2022-01-01",
    "phone_number": "123-456-7890",
    "is_active": True,
    "roles": [{"role_description":"Admin"}, {"role_description":"User"}]
}


def validate_all_match(key, request, response, db_record):
    if isinstance(request, list):
        # If comparing a list parameter, fetch all of the
        # values as a set so order won't matter.
        req_val = set([term[key] for term in request])
        response_val = set([term[key] for term in response])
        db_val = set([getattr(term, key) for term in db_record])

    else:
        req_val = request[key]
        response_val = response[key]
        db_val = getattr(db_record, key)

    if isinstance(db_val, date):
        db_val = db_val.isoformat()

    assert req_val == response_val
    assert req_val == db_val

def test_post_user_201(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 201

    results = test_db_session.query(User).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the request, response and DB model values all match
    validate_all_match("first_name", request, response_record, db_record)
    validate_all_match("middle_name", request, response_record, db_record)
    validate_all_match("last_name", request, response_record, db_record)
    validate_all_match("date_of_birth", request, response_record, db_record)
    validate_all_match("phone_number", request, response_record, db_record)
    validate_all_match("is_active", request, response_record, db_record)
    
    request_roles = request["roles"]
    response_roles = response_record["roles"]
    db_roles = db_record.roles
    assert 2 == len(request_roles) == len(response_roles) == len(db_roles)
    validate_all_match("role_description", request_roles, response_roles, db_roles)

def test_post_user_201_empty_array(client, api_auth_token, test_db_session):
    request = base_request | {"roles": []}
    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 201

    results = test_db_session.query(User).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the roles portion of the object also matches
    request_roles = request["roles"]
    response_roles = response_record["roles"]
    db_roles = db_record.roles
    assert 0 == len(request_roles) == len(response_roles) == len(db_roles)

def test_post_user_400_missing_required_fields(client, api_auth_token, test_db_session):
    # Send an empty post - should fail validation
    response = client.post("/v1/user", json={}, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    required_fields = ["first_name", "last_name", "phone_number", "date_of_birth", "is_active"]
    assert len(error_list) == len(
        required_fields
    ), f"Errored fields don't match expected for empty request {error_list}"
    for error in error_list:
        field, message, error_type = error["field"], error["message"], error["type"]
        assert field in required_fields
        assert "Field required" in message
        assert error_type == "value_error.missing"

    # Nothing added to DB
    results = test_db_session.query(User).all()
    assert len(results) == 0


def test_post_user_400_invalid_types(client, api_auth_token, test_db_session):
    request = {
        "first_name": 1,
        "middle_name": 2,
        "last_name": 3,
        "date_of_birth": 4,
        "phone_number": 5,
        "is_active": 6,
        "roles": 7,
    }
    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})
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
    results = test_db_session.query(User).all()
    assert len(results) == 0

def test_post_user_400_invalid_enums(client, api_auth_token, test_db_session):
    # Make the role a disallowed one
    request = base_request | {}
    request["roles"][0]["role_description"] = "Mime"
    request["roles"][1]["role_description"] = "Clown"

    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    # We expect the errors to be in a dict like:
    # {
    #   'field': 'roles.0.role_description',
    #   'message': "'Mime' is not one of ['User', 'Admin', 'Third Party']",
    #   'rule': ['User', 'Admin', 'Third Party'],
    #   'type': 'enum',
    #   'value': 'Mime'
    # }
    for error in error_list:
        field, message, error_type = (
            error["field"],
            error["message"],
            error["type"],
        )

        assert field.startswith("roles.") and field.endswith(".role_description")
        assert "is not one of" in message
        assert error_type == "enum"

def test_post_user_401_unauthorized_token(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post(
        "/v1/user", json=request, headers={"X-Auth": "incorrect token"}
    )
    assert response.status_code == 401

    # Verify the error message
    assert (
        "The server could not verify that you are authorized to access the URL requested"
        in response.get_json()["message"]
    )