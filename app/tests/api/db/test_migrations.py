import logging  # noqa: B1

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from alembic.script.revision import MultipleHeads
from alembic.util.exc import CommandError

import api.db
from api.db.migrations.run import alembic_cfg
from tests.lib import db_utils


def test_only_single_head_revision_in_migrations():
    script = ScriptDirectory.from_config(alembic_cfg)

    try:
        # This will raise if there are multiple heads
        script.get_current_head()
        multihead_situation = False
    except CommandError as e:
        # re-raise anything not expected
        if not isinstance(e.__cause__, MultipleHeads):
            raise

        multihead_situation = True

    # raising assertion error here instead of in `except` block to avoid pytest
    # printing the huge stacktrace of the multi-head exception, which in this
    # case we don't really care about the details, just using it as a flag
    if multihead_situation:
        raise AssertionError(
            "Multi-head migration issue: run `make db-migrate-merge-heads` to resolve"
        )


@pytest.fixture
def test_db_isolated(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.

    The monkeypatch setup of the test_db_schema fixture causes this issues
    so copied here with that adjusted
    """
    return db_utils.mock_db(monkeypatch)


def test_db_setup_via_alembic_migration(test_db_isolated, logging_fix, caplog):
    caplog.set_level(logging.INFO)  # noqa: B1
    command.upgrade(alembic_cfg, "head")
    # Verify the migration ran by checking the logs
    assert "Running upgrade" in caplog.text


def test_db_init_with_migrations(test_db_isolated):
    # Verify the DB session works after initializing the migrations
    db_session = api.db.init()

    db_session.close()
    db_session.remove()
