import csv
import os

import flask.testing
import pytest
from smart_open import open as smart_open

import api.adapters.db as db
import api.app as app_entry
import tests.api.db.models.factories as factories
from api.db import models
from api.db.models.user_models import User
from api.services.users.create_user_csv import USER_CSV_RECORD_HEADERS, create_user_csv
from api.util.file_util import list_files
from api.util.string_utils import blank_for_null
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
        UserFactory.create(first_name="A"),
        UserFactory.create(first_name="B"),
        UserFactory.create(first_name="C"),
    ]


def read_csv_records(file_path):
    with smart_open(file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        csv_rows = list(csv_reader)
        return csv_rows


def validate_csv_records(db_records, csv_records):

    assert len(csv_records) == len(db_records)

    # Sort the two lists by name and zip together for validation
    csv_records.sort(key=lambda record: record["User Name"])
    db_records.sort(key=lambda record: record.first_name)
    for csv_record, db_record in zip(csv_records, db_records):
        assert (
            csv_record[USER_CSV_RECORD_HEADERS.user_name]
            == f"{db_record.first_name} {db_record.last_name}"
        )
        assert csv_record[USER_CSV_RECORD_HEADERS.roles] == " ".join(
            [role.type for role in db_record.roles]
        )
        assert csv_record[USER_CSV_RECORD_HEADERS.is_user_active] == blank_for_null(
            db_record.is_active
        )


def test_create_user_csv_s3(
    cli_runner: flask.testing.FlaskCliRunner, prepopulated_users: list[User], mock_s3_bucket: str
):
    s3_filepath = f"s3://{mock_s3_bucket}/path/to/test.csv"

    cli_runner.invoke(
        args=[
            "user",
            "create-csv",
            "--dir",
            f"s3://{mock_s3_bucket}/path/to/",
            "--filename",
            "test.csv",
        ]
    )
    csv_rows = read_csv_records(s3_filepath)
    validate_csv_records(prepopulated_users, csv_rows)


def test_create_user_csv_local(
    cli_runner: flask.testing.FlaskCliRunner, prepopulated_users: list[User], tmp_path
):
    cli_runner.invoke(args=["user", "create-csv", "--dir", str(tmp_path), "--filename", "test.csv"])
    csv_rows = read_csv_records(os.path.join(tmp_path, "test.csv"))
    validate_csv_records(prepopulated_users, csv_rows)
