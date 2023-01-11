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
from api.db import models
from tests.lib import db_utils

logger = api.logging.get_logger(__name__)

####################
# Test DB session
####################


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="session")
def monkeypatch_session(request):
    """
    Create a monkeypatch instance that can be used to
    monkeypatch global environment, objects, and attributes
    for the duration the test session.
    """
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


# From https://github.com/pytest-dev/pytest/issues/363
@pytest.fixture(scope="module")
def monkeypatch_module(request):
    mpatch = _pytest.monkeypatch.MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def test_db(monkeypatch_session):
    """
    Creates a test schema, directly creating all tables with SQLAlchemy. Schema
    is dropped after the test completes.
    """

    with db_utils.test_db_schema(monkeypatch_session) as db_engine:
        models.metadata.create_all(bind=db_engine)
        yield db_engine


@pytest.fixture
def empty_schema(monkeypatch):
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.

    The monkeypatch setup of the test_db_schema fixture causes this issues
    so copied here with that adjusted
    """
    return db_utils.test_db_schema(monkeypatch)


@pytest.fixture
def test_db_session(test_db):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = api.db.Session(bind=connection, autocommit=False, expire_on_commit=False)

    session.begin_nested()

    @sqlalchemy.event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session

    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def test_db_session_isolated(test_db_isolated):
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    connection = test_db.connect()
    trans = connection.begin()
    session = api.db.Session(bind=connection, autocommit=False, expire_on_commit=False)

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

    import tests.api.db.models.factories as factories

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
    return app.test_client()


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
