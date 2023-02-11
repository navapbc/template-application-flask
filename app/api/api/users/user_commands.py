from typing import Optional
import click
import logging
import os.path as path

import api.adapters.db as db
import api.adapters.db.flask_db as flask_db
import api.services.users as user_service
from api.api.users.user_blueprint import user_blueprint
from api.util.datetime_util import utcnow

logger = logging.getLogger(__name__)

user_blueprint.cli.help = "User commands"


@user_blueprint.cli.command("create-csv", help="Create a CSV of all users and their roles")
@flask_db.with_db_session
@click.option("--dir", default=".")
@click.option("--filename", default=None)
def create_csv(db_session: db.Session, dir: str, filename: str):
    if filename is None:
        filename = utcnow().strftime("%Y-%m-%d-%H-%M-%S") + "-user-roles.csv"
    filepath = path.join(dir, filename)
    user_service.create_user_csv(db_session, filepath)
