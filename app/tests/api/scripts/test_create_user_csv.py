import os
import os.path as path
import re

import flask.testing
import pytest
from pytest_lazyfixture import lazy_fixture
from smart_open import open as smart_open

import api.adapters.db as db
import api.app as app_entry
import tests.api.db.models.factories as factories
from api.db import models
from api.db.models.user_models import User
from tests.api.db.models.factories import UserFactory
from tests.lib import db_testing


@pytest.fixture
def isolated_db(monkeypatch) -> db.DBClient:
    """
    Creates an isolated database for the test function.

    Creates a new empty PostgreSQL schema, creates all tables in the new schema
    using SQLAlchemy, then returns a db.DB instance that can be used to
    get connections or sessions to this database schema. The schema is dropped
    after the test function completes.

    This is similar to the db fixture except the scope of the schema is the
    individual test rather the test session.
    """

    with db_testing.create_isolated_db(monkeypatch) as db:
        models.metadata.create_all(bind=db.get_connection())
        yield db


@pytest.fixture
def cli_runner(isolated_db) -> flask.testing.CliRunner:
    """Overrides cli_runner from conftest to run in an isolated db schema"""
    return app_entry.create_app().test_cli_runner()


@pytest.fixture
def isolated_db_factories_session(monkeypatch, isolated_db: db.DBClient) -> db.Session:
    with isolated_db.get_session() as session:
        monkeypatch.setattr(factories, "_db_session", session)
        yield session


@pytest.fixture
def prepopulated_users(isolated_db_factories_session) -> list[User]:
    return [
        UserFactory.create(first_name="Jon", last_name="Doe", is_active=True),
        UserFactory.create(first_name="Jane", last_name="Doe", is_active=False),
        UserFactory.create(
            first_name="Alby",
            last_name="Testin",
            is_active=True,
        ),
    ]


@pytest.fixture
def tmp_s3_folder(mock_s3_bucket):
    return f"s3://{mock_s3_bucket}/path/to/"


@pytest.mark.parametrize(
    "dir",
    [
        pytest.param(lazy_fixture("tmp_s3_folder"), id="write-to-s3"),
        pytest.param(lazy_fixture("tmp_path"), id="write-to-local"),
    ],
)
def test_create_user_csv(
    cli_runner: flask.testing.FlaskCliRunner, prepopulated_users: list[User], dir: str
):
    cli_runner.invoke(args=["user", "create-csv", "--dir", dir, "--filename", "test.csv"])
    output = smart_open(path.join(dir, "test.csv")).read()
    expected_output = open(
        path.join(path.dirname(__file__), "test_create_user_csv_expected.csv")
    ).read()
    assert output == expected_output


def test_default_filename(cli_runner: flask.testing.FlaskCliRunner, tmp_path: str):
    cli_runner.invoke(args=["user", "create-csv", "--dir", tmp_path])
    filenames = os.listdir(tmp_path)
    assert re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-user-roles.csv", filenames[0])
