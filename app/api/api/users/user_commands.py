import logging
import os

import api.adapters.db as db
import api.adapters.db.flask_db as flask_db
import api.services.users as user_service
from api.api.users.user_blueprint import user_blueprint
from api.util.datetime_util import utcnow

logger = logging.getLogger(__name__)

user_blueprint.cli.help = "User commands"


@user_blueprint.cli.command("create-csv", help="Create a CSV of all users and their roles")
@flask_db.with_db_session
def create_csv(db_session: db.Session):
    # Build the path for the output file
    # This will create a file in the folder specified like:
    # s3://your-bucket/path/to/2022-09-09-12-00-00-user-roles.csv
    # The file path can be either S3 or local disk.
    output_path = os.getenv("USER_ROLE_CSV_OUTPUT_PATH", None)
    if not output_path:
        raise Exception("Please specify an USER_ROLE_CSV_OUTPUT_PATH env var")

    file_name = utcnow().strftime("%Y-%m-%d-%H-%M-%S") + "-user-roles.csv"
    output_file_path = os.path.join(output_path, file_name)

    user_service.create_user_csv(db_session, output_file_path)
