import pytest
from sqlalchemy import text

import src.adapters.db as db
from src.adapters.db.engine.postgres_engine import PostgresEngine


def test_db_connection(db_client):
    db_client = db.init(PostgresEngine())
    with db_client.get_connection() as conn:
        assert conn.scalar(text("SELECT 1")) == 1


def test_check_db_connection(caplog, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DB_CHECK_CONNECTION_ON_INIT", "True")
    db.init(PostgresEngine())
    assert "database connection is not using SSL" in caplog.messages


def test_get_session():
    db_client = db.init(PostgresEngine())
    with db_client.get_session() as session:
        with session.begin():
            assert session.scalar(text("SELECT 1")) == 1
