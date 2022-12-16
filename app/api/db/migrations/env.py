import sys
from typing import Any

import sqlalchemy
from alembic import context

# Alembic cli seems to reset the path on load causing issues with local module imports.
# Workaround is to force set the path to the current run directory (top level api folder)
# See database migrations section in `api/README.md` for details about running migrations.
sys.path.insert(0, ".")  # noqa: E402

# Load env vars before anything further
from api.util.local import load_local_env_vars  # noqa: E402 isort:skip

load_local_env_vars()

import api.db as db  # noqa: E402 isort:skip
from api.db.models.base import Base  # noqa: E402 isort:skip
import api.logging  # noqa: E402 isort:skip

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Initialize logging
api.logging.init("migrations")

if not config.get_main_option("sqlalchemy.url"):
    uri = db.make_connection_uri(db.get_db_config())

    # Escape percentage signs in the URI.
    # https://alembic.sqlalchemy.org/en/latest/api/config.html#alembic.config.Config.set_main_option
    config.set_main_option("sqlalchemy.url", uri.replace("%", "%%"))

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(
    object: sqlalchemy.schema.SchemaItem, name: str, type_: str, reflected: bool, compare_to: Any
) -> bool:
    if type_ == "schema" and getattr(object, "schema", None) is not None:
        return False
    else:
        return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=False,
        include_object=include_object,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    url = config.get_main_option("sqlalchemy.url", "SQLAlchemy URL not set")
    connectable = sqlalchemy.create_engine(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=False,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
