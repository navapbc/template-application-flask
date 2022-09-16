import logging.config  # noqa: B1
import os
import uuid

import _pytest.monkeypatch
import boto3
import moto
import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import api.app as app_entry
import api.db
import api.logging

logger = api.logging.get_logger(__name__)

####################
# Test DB session
####################


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="session")
def monkeypatch_session(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="module")
def monkeypatch_module(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


def exec_sql_admin(sql):
    db_admin_config = api.db.get_db_config()
    engine = api.db.create_db_engine(db_admin_config)
    with engine.connect() as connection:
        connection.execute(sql)


def db_schema_create(schema_name):
    """Create a database schema."""
    db_config = api.db.get_db_config()
    db_test_user = db_config.username

    exec_sql_admin(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {db_test_user};")
    logger.info("create schema %s", schema_name)


def db_schema_drop(schema_name):
    """Drop a database schema."""
    exec_sql_admin(f"DROP SCHEMA {schema_name} CASCADE;")
    logger.info("drop schema %s", schema_name)


@pytest.fixture(scope="session")
def test_db_schema(monkeypatch_session):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.
    """
    schema_name = f"test_schema_{uuid.uuid4().int}"

    monkeypatch_session.setenv("DB_SCHEMA", schema_name)
    monkeypatch_session.setenv("POSTGRES_DB", "main-db")
    monkeypatch_session.setenv("POSTGRES_USER", "local_db_user")
    monkeypatch_session.setenv("POSTGRES_PASSWORD", "secret123")
    monkeypatch_session.setenv("ENVIRONMENT", "local")

    db_schema_create(schema_name)
    try:
        yield schema_name
    finally:
        db_schema_drop(schema_name)


@pytest.fixture(scope="session")
def test_db(test_db_schema):
    """
    Creates a test schema, directly creating all tables with SQLAlchemy. Schema
    is dropped after the test completes.
    """

    # not used directly, but loads models into Base
    from api.db.models.base import Base

    engine = api.db.create_db_engine()
    Base.metadata.create_all(bind=engine)

    db_session = api.db.init()
    db_session.close()
    db_session.remove()

    return engine


@pytest.fixture
def test_db_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = api.db.scoped_session(
        sessionmaker(bind=connection, autocommit=False, expire_on_commit=False)
    )

    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture(autouse=True, scope="session")
def set_no_db_factories_alert():
    """By default, ensure factories do not attempt to access the database.

    The tests that need generated models to actually hit the database can pull
    in the `initialize_factories_session` fixture to their test case to enable
    factory writes to the database.
    """
    os.environ["DB_FACTORIES_DISABLE_DB_ACCESS"] = "1"


@pytest.fixture
def initialize_factories_session(monkeypatch, test_db_session):
    monkeypatch.delenv("DB_FACTORIES_DISABLE_DB_ACCESS")

    import api.db.models.factories as factories

    logger.info("set factories db_session to %s", test_db_session)
    factories.db_session = test_db_session


####################
# Logging
####################


@pytest.fixture
def logging_fix(monkeypatch):
    """Disable the application custom logging setup

    Needed if the code under test calls api.util.logging.init() so that
    tests using the caplog fixture don't break.
    """
    monkeypatch.setattr(logging.config, "dictConfig", lambda config: None)  # noqa: B1


####################
# Test App & Client
####################


@pytest.fixture
def app(test_db_session):
    return app_entry.create_app(
        check_migrations_current=False, db_session_factory=test_db_session, do_close_db=False
    )


@pytest.fixture
def client(app):
    return app.app.test_client()


@pytest.fixture
def api_auth_token(monkeypatch):
    auth_token = "abcd1234"
    monkeypatch.setenv("API_AUTH_TOKEN", auth_token)
    return auth_token


####################
# AWS Mock Fixtures
####################


@pytest.fixture
def reset_aws_env_vars(monkeypatch):
    # Reset the env vars so you can't accidentally connect
    # to a real AWS account if you were doing some local testing
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def mock_s3(reset_aws_env_vars):
    with moto.mock_s3():
        yield boto3.resource("s3")


@pytest.fixture
def mock_s3_bucket_resource(mock_s3):
    bucket = mock_s3.Bucket("test_bucket")
    bucket.create()
    yield bucket


@pytest.fixture
def mock_s3_bucket(mock_s3_bucket_resource):
    yield mock_s3_bucket_resource.name
