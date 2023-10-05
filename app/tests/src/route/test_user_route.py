import uuid

import faker
import pytest

from tests.src.util.parametrize_utils import powerset

fake = faker.Faker()


def get_base_request():
    return {
        "first_name": fake.first_name(),
        "middle_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": "2022-01-01",
        "phone_number": "123-456-7890",
        "is_active": True,
        "roles": [{"type": "ADMIN"}, {"type": "USER"}],
    }


@pytest.fixture
def base_request():
    return get_base_request()


@pytest.fixture
def created_user(client, api_auth_token, base_request):
    response = client.post("/v1/users", json=base_request, headers={"X-Auth": api_auth_token})
    return response.json()


test_create_and_get_user_data = [
    pytest.param([], id="empty roles"),
    pytest.param([{"type": "ADMIN"}, {"type": "USER"}], id="all roles"),
]


@pytest.mark.parametrize("roles", test_create_and_get_user_data)
def test_create_and_get_user(client, base_request, api_auth_token, roles):
    # Create a user
    request = {
        **base_request,
        "roles": roles,
    }
    post_response = client.post("/v1/users", json=request, headers={"X-Auth": api_auth_token})
    post_response_data = post_response.json()
    expected_response = {
        **request,
        "id": post_response_data["id"],
        "created_at": post_response_data["created_at"],
        "updated_at": post_response_data["updated_at"],
    }

    assert post_response.status_code == 201
    assert post_response_data == expected_response
    assert post_response_data["created_at"] is not None
    assert post_response_data["updated_at"] is not None

    # Get the user
    user_id = post_response.json()["id"]
    get_response = client.get(f"/v1/users/{user_id}", headers={"X-Auth": api_auth_token})

    assert get_response.status_code == 200

    get_response_data = get_response.json()
    assert get_response_data == expected_response


test_create_user_bad_request_data = [
    pytest.param(
        {},
        [
            {
                "input": {},
                "loc": ["body", "first_name"],
                "msg": "Field required",
                "type": "missing",
            },
            {"input": {}, "loc": ["body", "last_name"], "msg": "Field required", "type": "missing"},
            {
                "input": {},
                "loc": ["body", "phone_number"],
                "msg": "Field required",
                "type": "missing",
            },
            {
                "input": {},
                "loc": ["body", "date_of_birth"],
                "msg": "Field required",
                "type": "missing",
            },
            {"input": {}, "loc": ["body", "is_active"], "msg": "Field required", "type": "missing"},
            {"input": {}, "loc": ["body", "roles"], "msg": "Field required", "type": "missing"},
        ],
        id="missing all required fields",
    ),
    pytest.param(
        {
            "first_name": 1,
            "middle_name": 2,
            "last_name": 3,
            "date_of_birth": 4,
            "phone_number": 5,
            "is_active": 6,
            "roles": 7,
        },
        [
            {
                "input": 1,
                "loc": ["body", "first_name"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
            {
                "input": 2,
                "loc": ["body", "middle_name"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
            {
                "input": 3,
                "loc": ["body", "last_name"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
            {
                "input": 5,
                "loc": ["body", "phone_number"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
            {
                "input": 4,
                "loc": ["body", "date_of_birth"],
                "msg": "Datetimes provided to dates should have zero time - e.g. be exact " "dates",
                "type": "date_from_datetime_inexact",
            },
            {
                "input": 6,
                "loc": ["body", "is_active"],
                "msg": "Input should be a valid boolean, unable to interpret input",
                "type": "bool_parsing",
            },
            {
                "input": 7,
                "loc": ["body", "roles"],
                "msg": "Input should be a valid list",
                "type": "list_type",
            },
        ],
        id="invalid types",
    ),
    pytest.param(
        get_base_request() | {"roles": [{"type": "Mime"}, {"type": "Clown"}]},
        [
            {
                "ctx": {"expected": "'USER' or 'ADMIN'"},
                "input": "Mime",
                "loc": ["body", "roles", 0, "type"],
                "msg": "Input should be 'USER' or 'ADMIN'",
                "type": "enum",
            },
            {
                "ctx": {"expected": "'USER' or 'ADMIN'"},
                "input": "Clown",
                "loc": ["body", "roles", 1, "type"],
                "msg": "Input should be 'USER' or 'ADMIN'",
                "type": "enum",
            },
        ],
        id="invalid role type",
    ),
]


@pytest.mark.parametrize("request_data,expected_response_data", test_create_user_bad_request_data)
def test_create_user_bad_request(client, api_auth_token, request_data, expected_response_data):
    response = client.post("/v1/users", json=request_data, headers={"X-Auth": api_auth_token})
    assert response.status_code == 422

    response_data = response.json()["detail"]
    assert response_data == expected_response_data


def test_patch_user(client, api_auth_token, created_user):
    user_id = created_user["id"]
    patch_request = {"first_name": fake.first_name()}
    patch_response = client.patch(
        f"/v1/users/{user_id}", json=patch_request, headers={"X-Auth": api_auth_token}
    )
    patch_response_data = patch_response.json()
    expected_response_data = {
        **created_user,
        **patch_request,
        "updated_at": patch_response_data["updated_at"],
    }

    assert patch_response.status_code == 200
    assert patch_response_data == expected_response_data

    get_response = client.get(f"/v1/users/{user_id}", headers={"X-Auth": api_auth_token})
    get_response_data = get_response.json()

    assert get_response_data == expected_response_data


@pytest.mark.parametrize("initial_roles", powerset([{"type": "ADMIN"}, {"type": "USER"}]))
@pytest.mark.parametrize("updated_roles", powerset([{"type": "ADMIN"}, {"type": "USER"}]))
def test_patch_user_roles(client, base_request, api_auth_token, initial_roles, updated_roles):
    post_request = {
        **base_request,
        "roles": initial_roles,
    }
    created_user = client.post(
        "/v1/users", json=post_request, headers={"X-Auth": api_auth_token}
    ).json()
    user_id = created_user["id"]

    patch_request = {"roles": updated_roles}
    patch_response = client.patch(
        f"/v1/users/{user_id}", json=patch_request, headers={"X-Auth": api_auth_token}
    )
    patch_response_data = patch_response.json()
    expected_response_data = {
        **created_user,
        **patch_request,
        "updated_at": patch_response_data["updated_at"],
    }

    assert patch_response.status_code == 200
    assert patch_response_data == expected_response_data

    get_response = client.get(f"/v1/users/{user_id}", headers={"X-Auth": api_auth_token})
    get_response_data = get_response.json()

    assert get_response_data == expected_response_data


test_unauthorized_data = [
    pytest.param("post", "/v1/users", get_base_request(), id="post"),
    pytest.param("get", f"/v1/users/{uuid.uuid4()}", None, id="get"),
    pytest.param("patch", f"/v1/users/{uuid.uuid4()}", {}, id="patch"),
]


@pytest.mark.parametrize("method,url,body", test_unauthorized_data)
def test_unauthorized(client, method, url, body, api_auth_token):
    expected_message = (
        "The server could not verify that you are authorized to access the URL requested"
    )
    response = client.request(
        method=method, url=url, json=body, headers={"X-Auth": "incorrect token"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == expected_message


test_not_found_data = [
    pytest.param("get", None, id="get"),
    pytest.param("patch", {}, id="patch"),
]


@pytest.mark.parametrize("method,body", test_not_found_data)
def test_not_found(client, api_auth_token, method, body):
    user_id = uuid.uuid4()
    url = f"/v1/users/{user_id}"
    response = client.request(method=method, url=url, json=body, headers={"X-Auth": api_auth_token})

    assert response.status_code == 404
    assert response.json()["detail"] == f"Could not find user with ID {user_id}"
