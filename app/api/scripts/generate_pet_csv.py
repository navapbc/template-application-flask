import csv
import os
from dataclasses import asdict, dataclass

from smart_open import open as smart_open

import api.db as db
import api.logging
from api.db.models.example_person_models import ExamplePet
from api.scripts.util.script_util import script_context_manager
from api.util.datetime_util import utcnow

logger = api.logging.get_logger(__name__)


@dataclass
class PetCsvRecord:
    pet_name: str
    pet_species: str
    pet_owner_name: str
    is_pet_owner_real: str


PET_CSV_RECORD_HEADER = PetCsvRecord(
    pet_name="Pet Name",
    pet_species="Pet Species",
    pet_owner_name="Pet Owner",
    is_pet_owner_real="Does the pet owner actually exist?",
)


def create_pet_csv(db_session: db.scoped_session, output_file_path: str) -> None:
    # Get DB records
    example_pet_records = get_example_pet_records(db_session)

    csv_records = convert_example_pet_records_for_csv(example_pet_records)

    generate_csv_file(csv_records, output_file_path)


def get_example_pet_records(db_session: db.scoped_session) -> list[ExamplePet]:
    logger.info("Fetching example pet records from DB")
    example_pet_records = db_session.query(ExamplePet).all()

    record_count = len(example_pet_records)
    logger.info(
        "Found %s example pet records",
        record_count,
        extra={"example_pet_count": record_count},
    )

    return example_pet_records


def generate_csv_file(records: list[PetCsvRecord], output_file_path: str) -> None:
    logger.info("Generating example pet CSV at %s", output_file_path)

    # smart_open can write files to local & S3
    with smart_open(output_file_path, "w") as outbound_file:
        csv_writer = csv.DictWriter(
            outbound_file,
            fieldnames=list(asdict(PET_CSV_RECORD_HEADER).keys()),
            quoting=csv.QUOTE_ALL,
        )
        for record in records:
            csv_writer.writerow(asdict(record))

    logger.info("Successfully created example pet CSV at %s", output_file_path)


def convert_example_pet_records_for_csv(records: list[ExamplePet]) -> list[PetCsvRecord]:
    logger.info("Converting example pets to CSV format")
    out_records: list[PetCsvRecord] = []
    out_records.append(PET_CSV_RECORD_HEADER)

    for record in records:
        pet_owner = record.pet_owner
        pet_owner_name = " ".join([pet_owner.first_name, pet_owner.last_name])
        out_records.append(
            PetCsvRecord(
                pet_name=record.name,
                pet_species=record.species,
                pet_owner_name=pet_owner_name,
                is_pet_owner_real=str(pet_owner.is_real),
            )
        )

    return out_records


def main() -> None:
    # Initialize DB session / logging / env vars
    with script_context_manager() as script_context:
        # Build the path for the output file
        # This will create a file in the folder specified like:
        # s3://your-bucket/path/to/2022-09-09-12-00-00-example-pet.csv
        # The file path can be either S3 or local disk.
        output_path = os.getenv("PET_CSV_OUTPUT_PATH", None)
        if not output_path:
            raise Exception("Please specify an PET_CSV_OUTPUT_PATH env var")

        file_name = utcnow().strftime("%Y-%m-%d-%H-%M-%S") + "-example-pet.csv"
        output_file_path = os.path.join(output_path, file_name)

        create_pet_csv(script_context.db_session, output_file_path)
