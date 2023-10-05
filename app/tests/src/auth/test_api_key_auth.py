import pytest
from fastapi import HTTPException

from src.auth.api_key_auth import verify_api_key


def test_verify_api_key_invalid_token(api_auth_token):
    # If you pass it the wrong token
    with pytest.raises(HTTPException):
        verify_api_key("not the right token")


def test_verify_api_key_no_configuration(monkeypatch):
    # Remove the API_AUTH_TOKEN env var if set in
    # your local environment
    monkeypatch.delenv("API_AUTH_TOKEN", raising=False)
    # If the auth token is not setup
    with pytest.raises(HTTPException):
        verify_api_key("any token")
