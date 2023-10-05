import typing

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import text

import src.adapters.db as db
import src.adapters.db.fastapi_db as fastapi_db


# Define an isolated example FastAPI app fixture specific to this test module
# to avoid dependencies on any project-specific fixtures in conftest.py
@pytest.fixture
def example_app() -> FastAPI:
    app = FastAPI()
    db_client = db.PostgresDBClient()
    fastapi_db.register_db_client(db_client, app)
    return app


def test_get_db(example_app: FastAPI):
    @example_app.get("/hello")
    def hello(request: Request) -> dict:
        with fastapi_db.get_db_client(request.app).get_connection() as conn:
            return {"data": conn.scalar(text("SELECT 'hello, world'"))}

    response = TestClient(example_app).get("/hello")
    assert response.json() == {"data": "hello, world"}


def test_with_db_session_depends(example_app: FastAPI):
    @example_app.get("/hello")
    def hello(db_session: typing.Annotated[db.Session, Depends(fastapi_db.DbSessionDependency())]):
        with db_session.begin():
            return {"data": db_session.scalar(text("SELECT 'hello, world'"))}

    response = TestClient(example_app).get("/hello")
    assert response.json() == {"data": "hello, world"}


def test_with_db_session_depends_not_default_name(example_app: FastAPI):
    db_client = db.PostgresDBClient()
    fastapi_db.register_db_client(db_client, example_app, client_name="something_else")

    @example_app.get("/hello")
    def hello(
        db_session: typing.Annotated[
            db.Session, Depends(fastapi_db.DbSessionDependency(client_name="something_else"))
        ]
    ):
        with db_session.begin():
            return {"data": db_session.scalar(text("SELECT 'hello, world'"))}

    response = TestClient(example_app).get("/hello")
    assert response.json() == {"data": "hello, world"}
