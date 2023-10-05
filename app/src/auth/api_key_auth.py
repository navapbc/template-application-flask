import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-Auth")


def verify_api_key(token: str = Security(API_KEY_HEADER)) -> str:
    # WARNING: this isn't really a production ready
    # auth approach. In reality the user object returned
    # here should be pulled from a DB or auth service, but
    # as there are several types of authentication, we are
    # keeping this pretty basic for the out-of-the-box approach
    expected_auth_token = os.getenv("API_AUTH_TOKEN", None)

    if not expected_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is not setup, please add an API_AUTH_TOKEN environment variable.",
        )

    if token != expected_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The server could not verify that you are authorized to access the URL requested",
        )

    return token
