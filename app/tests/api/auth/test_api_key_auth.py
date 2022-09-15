import pytest
from flask import g
from werkzeug.exceptions import Unauthorized

from api.auth.api_key_auth import API_AUTH_USER, api_key_auth


def test_api_key_auth_success(app, api_auth_token):
    # Passing it the configured auth token successfully returns a user
    with app.app.app_context():  # So we can attach the user to the flask app
        user_map = api_key_auth(api_auth_token, None)

        assert user_map.get("uid") == API_AUTH_USER.user_id
        assert g.get("current_user") == API_AUTH_USER


def test_api_key_auth_invalid_token(api_auth_token):
    # If you pass it the wrong token
    with pytest.raises(
        Unauthorized,
        match="The server could not verify that you are authorized to access the URL requested",
    ):
        api_key_auth("not the right token", None)


def test_api_key_auth_no_configuration(monkeypatch):
    # Remove the API_AUTH_TOKEN env var if set in
    # your local environment
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    # If the auth token is not setup
    with pytest.raises(Unauthorized, match="Authentication is not setup"):
        api_key_auth("any token", None)
