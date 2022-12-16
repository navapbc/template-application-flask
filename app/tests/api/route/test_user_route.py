from datetime import date

import faker

from api.db.models.user_models import User
from tests.api.db.models.factories import UserFactory

fake = faker.Faker()

base_request = {
    "first_name": fake.first_name(),
    "middle_name": fake.first_name(),
    "last_name": fake.last_name(),
    "date_of_birth": "2022-01-01",
    "phone_number": "123-456-7890",
    "is_active": True,
    "roles": [{"type": "ADMIN"}, {"type": "USER"}],
}


def validate_all_match(request, response, db_record):
    for k in base_request.keys():
        if k == "roles":
            request_roles = request["roles"] if request else None
            response_roles = response["roles"] if response else None
            db_roles = db_record.roles if db_record else None
            validate_param_match("type", request_roles, response_roles, db_roles)
        else:
            validate_param_match(k, request, response, db_record)


def validate_param_match(key, request, response, db_record):
    if isinstance(response, list):
        # If comparing a list parameter, fetch all of the
        # values as a set so order won't matter.
        req_val = set([term[key] for term in request]) if request else None
        response_val = set([term[key] for term in response]) if response else None
        db_val = set([getattr(term, key) for term in db_record]) if db_record else None

    else:
        req_val = request[key] if request else None
        response_val = response[key] if response else None
        db_val = getattr(db_record, key) if db_record else None

    if isinstance(db_val, date):
        db_val = db_val.isoformat()

    if request is not None:
        assert req_val == response_val
        assert req_val == db_val

    assert response_val == db_val


def test_post_user_201(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 201

    results = test_db_session.query(User).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the request, response and DB model values all match
    validate_all_match(request, response_record, db_record)


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
    request = base_request | {"roles": [{"type": "Mime"}, {"type": "Clown"}]}

    response = client.post("/v1/user", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 400

    error_list = response.get_json()["errors"]
    # We expect the errors to be in a dict like:
    # {
    #   'field': 'roles.0.role',
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

        assert field.startswith("roles.") and field.endswith(".role")
        assert "is not one of" in message
        assert error_type == "enum"


def test_post_user_401_unauthorized_token(client, api_auth_token, test_db_session):
    request = base_request | {}
    response = client.post("/v1/user", json=request, headers={"X-Auth": "incorrect token"})
    assert response.status_code == 401

    # Verify the error message
    assert (
        "The server could not verify that you are authorized to access the URL requested"
        in response.get_json()["message"]
    )


def test_get_user_200(client, api_auth_token, test_db_session, initialize_factories_session):
    user = UserFactory.create()
    response = client.get(f"/v1/user/{user.id}", headers={"X-Auth": api_auth_token})

    assert response.status_code == 200
    response_record = response.get_json()["data"]

    validate_all_match(None, response_record, user)


def test_get_user_401_unauthorized_token(
    client, api_auth_token, test_db_session, initialize_factories_session
):
    user = UserFactory.create()
    response = client.get(f"/v1/user/{user.id}", headers={"X-Auth": "incorrect token"})

    assert response.status_code == 401
    # Verify the error message
    assert (
        "The server could not verify that you are authorized to access the URL requested"
        in response.get_json()["message"]
    )


def test_get_user_404_user_not_found(client, api_auth_token, test_db_session):
    response = client.get(
        "/v1/user/cd1dcc81-2759-461b-8c09-9ba9be669bf9", headers={"X-Auth": api_auth_token}
    )

    assert response.status_code == 404
    # Verify the error message
    assert "Could not find User with ID" in response.get_json()["message"]


def test_patch_user_200(client, api_auth_token, test_db_session, initialize_factories_session):
    user = UserFactory.create(first_name="NotSomethingFakerWillGenerate")
    request = base_request | {}
    response = client.patch(f"/v1/user/{user.id}", json=request, headers={"X-Auth": api_auth_token})

    assert response.status_code == 200

    results = test_db_session.query(User).all()
    assert len(results) == 1
    db_record = results[0]
    response_record = response.get_json()["data"]

    # Verify the request, response and DB model values all match
    validate_all_match(request, response_record, db_record)

    # Verify it is the same user that we created
    # but that the name did in fact change
    assert user.id == db_record.user_id
    assert db_record.first_name != "NotSomethingFakerWillGenerate"


def test_patch_user_200_roles(
    client, api_auth_token, test_db_session, initialize_factories_session
):
    # testing that the role change logic specifically works
    # Create a user with no roles
    user = UserFactory.create(roles=[])

    # Add two roles
    request = {"roles": [{"type": "ADMIN"}, {"type": "USER"}]}
    response = client.patch(f"/v1/user/{user.id}", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 200

    response_roles = response.get_json()["data"]["roles"]
    assert set(["ADMIN", "USER"]) == set([role["role"] for role in response_roles])

    # Remove a role
    request = {"roles": [{"type": "ADMIN"}]}
    response = client.patch(f"/v1/user/{user.id}", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 200

    response_roles = response.get_json()["data"]["roles"]
    assert set(["ADMIN"]) == set([role["role"] for role in response_roles])

    # Remove all roles
    request = {"roles": []}
    response = client.patch(f"/v1/user/{user.id}", json=request, headers={"X-Auth": api_auth_token})
    assert response.status_code == 200

    response_roles = response.get_json()["data"]["roles"]
    assert set() == set([role["role"] for role in response_roles])


def test_patch_user_401_unauthorized_token(
    client, api_auth_token, test_db_session, initialize_factories_session
):
    user = UserFactory.create()
    response = client.patch(f"/v1/user/{user.id}", json={}, headers={"X-Auth": "incorrect token"})

    assert response.status_code == 401
    # Verify the error message
    assert (
        "The server could not verify that you are authorized to access the URL requested"
        in response.get_json()["message"]
    )


def test_patch_user_404_user_not_found(client, api_auth_token, test_db_session):
    response = client.patch(
        "/v1/user/cd1dcc81-2759-461b-8c09-9ba9be669bf9",
        json={},
        headers={"X-Auth": api_auth_token},
    )

    assert response.status_code == 404
    # Verify the error message
    assert "Could not find User with ID" in response.get_json()["message"]
