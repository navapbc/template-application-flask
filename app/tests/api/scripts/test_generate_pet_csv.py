import csv
import os

import pytest
from smart_open import open as smart_open

from api.db.models.factories import ExamplePetFactory
from api.scripts.generate_pet_csv import PET_CSV_RECORD_HEADER, create_pet_csv
from api.util.file_util import list_files
from api.util.string_utils import blank_for_null


@pytest.fixture
def tmp_file_path(tmp_path):
    return tmp_path / "example_file.csv"


def read_csv_records(file_path):
    with smart_open(file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        csv_rows = list(csv_reader)
        return csv_rows


def validate_csv_records(db_records, csv_records, test_db_session):
    assert len(csv_records) == len(db_records)

    # Sort the two lists by first name and zip together for validation
    csv_records.sort(key=lambda record: record["Pet Name"])
    db_records.sort(key=lambda record: record.name)
    for csv_record, db_record in zip(csv_records, db_records):
        assert csv_record[PET_CSV_RECORD_HEADER.pet_name] == db_record.name
        assert csv_record[PET_CSV_RECORD_HEADER.pet_species] == db_record.species
        assert (
            csv_record[PET_CSV_RECORD_HEADER.pet_owner_name]
            == f"{db_record.pet_owner.first_name} {db_record.pet_owner.last_name}"
        )
        assert csv_record[PET_CSV_RECORD_HEADER.is_pet_owner_real] == blank_for_null(
            db_record.pet_owner.is_real
        )


def test_generate_pet_csv_s3(test_db_session, initialize_factories_session, mock_s3_bucket):
    s3_filepath = f"s3://{mock_s3_bucket}/path/to/test.csv"
    # To make validating these easier in the CSV, make the names consistent
    db_records = [ExamplePetFactory.create(name="A"), ExamplePetFactory(name="B")]

    create_pet_csv(test_db_session, s3_filepath)
    csv_rows = read_csv_records(s3_filepath)
    validate_csv_records(db_records, csv_rows, test_db_session)

    # If we add another DB record with the same pet owner, it'll go in the file as well
    db_records.append(ExamplePetFactory.create(name="C", pet_owner=db_records[0].pet_owner))
    create_pet_csv(test_db_session, s3_filepath)
    csv_rows = read_csv_records(s3_filepath)
    validate_csv_records(db_records, csv_rows, test_db_session)

    assert "test.csv" in list_files(f"s3://{mock_s3_bucket}/path/to/")


def test_generate_pet_csv_local(
    test_db_session, initialize_factories_session, tmp_path, tmp_file_path
):
    # Same as above test, but verifying the file logic
    # works locally in addition to S3.
    db_records = [ExamplePetFactory.create(name="A"), ExamplePetFactory(name="B")]

    create_pet_csv(test_db_session, tmp_file_path)
    csv_rows = read_csv_records(tmp_file_path)
    validate_csv_records(db_records, csv_rows, test_db_session)

    assert os.path.exists(tmp_file_path)
