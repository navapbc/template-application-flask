import csv
import os

import pytest
from smart_open import open as smart_open
from api.db.models.user_models import User

from api.services.users.create_user_csv import USER_CSV_RECORD_HEADERS, create_user_csv
from api.util.file_util import list_files
from api.util.string_utils import blank_for_null
from tests.api.db.models.factories import UserFactory


@pytest.fixture
def tmp_file_path(tmp_path):
    return tmp_path / "example_file.csv"


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


def test_create_user_csv_s3(test_db_session, initialize_factories_session, mock_s3_bucket):
    s3_filepath = f"s3://{mock_s3_bucket}/path/to/test.csv"

    # To make validating these easier in the CSV, make the names consistent
    db_records = [
        UserFactory.create(first_name="A"),
        UserFactory.create(first_name="B"),
    ]

    create_user_csv(test_db_session, s3_filepath)
    csv_rows = read_csv_records(s3_filepath)
    validate_csv_records(db_records, csv_rows)

    # If we add another DB record it'll go in the file as well
    db_records.append(UserFactory.create(first_name="C"))
    create_user_csv(test_db_session, s3_filepath)
    csv_rows = read_csv_records(s3_filepath)
    validate_csv_records(db_records, csv_rows)

    assert "test.csv" in list_files(f"s3://{mock_s3_bucket}/path/to/")


def test_create_user_csv_local(
    test_db_session, initialize_factories_session, tmp_path, tmp_file_path
):
    # Same as above test, but verifying the file logic
    # works locally in addition to S3.
    db_records = [
        UserFactory.create(first_name="A"),
        UserFactory.create(first_name="B"),
    ]

    create_user_csv(test_db_session, tmp_file_path)
    csv_rows = read_csv_records(tmp_file_path)
    validate_csv_records(db_records, csv_rows)

    assert os.path.exists(tmp_file_path)
