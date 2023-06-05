import pytest
from sqlalchemy import text

import src.adapters.db as db


def test_db_connection(db_client):
    # db_client = db.PostgresDBClient()
    with db_client.get_connection() as conn:
        assert conn.scalar(text("SELECT 1")) == 1


def test_check_db_connection(caplog, monkeypatch: pytest.MonkeyPatch, db_config):
    db_config = db_config.copy()
    db_config.check_connection_on_init = True
    db.PostgresDBClient(db_config)
    assert "database connection is not using SSL" in caplog.messages


def test_get_session(db_client):
    # db_client = db.PostgresDBClient()
    with db_client.get_session() as session:
        with session.begin():
            assert session.scalar(text("SELECT 1")) == 1
