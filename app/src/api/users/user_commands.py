import logging
import os.path as path
from typing import Optional

import click

import src.adapters.db as db
import src.adapters.db.flask_db as flask_db
from src.db.models.user_models import sync_all
import src.services.users as user_service
from src.api.users.user_blueprint import user_blueprint
from src.util.datetime_util import utcnow

from src.db.migrations.run import up

logger = logging.getLogger(__name__)

user_blueprint.cli.help = "User commands"


@user_blueprint.cli.command("create-csv", help="Create a CSV of all users and their roles")
@flask_db.with_db_session()
@click.option(
    "--dir",
    default=".",
    help="Directory to save output file in. Can be an S3 path (e.g. 's3://bucketname/folder/') Defaults to current directory ('.').",
)
@click.option(
    "--filename",
    default=None,
    help="Filename to save output file as. Defaults to '[timestamp]-user-roles.csv.",
)
def create_csv(db_session: db.Session, dir: str, filename: Optional[str]) -> None:
    if filename is None:
        filename = utcnow().strftime("%Y-%m-%d-%H-%M-%S") + "-user-roles.csv"
    filepath = path.join(dir, filename)
    user_service.create_user_csv(db_session, filepath)



@user_blueprint.cli.command("migrate-db-up", help="dummy thing")
@flask_db.with_db_session()
def migrate_db(db_session: db.Session) -> None:
    up()

    with db_session.begin():
        sync_all(db_session)