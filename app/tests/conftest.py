import _pytest.monkeypatch
import boto3
import moto
import pytest
import sqlalchemy

import api.adapters.db as db
import api.adapters.logging as logging
import api.app as app_entry
import tests.api.db.models.factories as factories
from api.db import models
from tests.lib import db_testing

logger = logging.get_logger(__name__)

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
def db_client(monkeypatch_session) -> db.DBClient:
    """
    Creates an isolated database for the test session.

    Creates a new empty PostgreSQL schema, creates all tables in the new schema
    using SQLAlchemy, then returns a db.DB instance that can be used to
    get connections or sessions to this database schema. The schema is dropped
    after the test suite session completes.
    """

    with db_testing.create_isolated_db(monkeypatch_session) as db_client:
        models.metadata.create_all(bind=db_client.get_connection())
        yield db_client


@pytest.fixture(scope="function")
def isolated_db(monkeypatch) -> db.DBClient:
    """
    Creates an isolated database for the test function.

    Creates a new empty PostgreSQL schema, creates all tables in the new schema
    using SQLAlchemy, then returns a db.DB instance that can be used to
    get connections or sessions to this database schema. The schema is dropped
    after the test function completes.

    This is similar to the db fixture except the scope of the schema is the
    individual test rather the test session.
    """

    with db_testing.create_isolated_db(monkeypatch) as db:
        models.metadata.create_all(bind=db.get_connection())
        yield db


@pytest.fixture
def empty_schema(monkeypatch) -> db.DBClient:
    """
    Create a test schema, if it doesn't already exist, and drop it after the
    test completes.

    This is similar to the db fixture but does not create any tables in the
    schema. This is used by migration tests.
    """
    with db_testing.create_isolated_db(monkeypatch) as db:
        yield db


@pytest.fixture
def test_db_session(db_client: db.DBClient) -> db.Session:
    # Based on https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    with db_client.get_connection() as connection:
        trans = connection.begin()

        # Rather than call db.get_session() to create a new session with a new connection,
        # create a session bound to the existing connection that has a transaction manually start.
        # This allows the transaction to be rolled back after the test completes.
        with db.Session(bind=connection, autocommit=False, expire_on_commit=False) as session:
            session.begin_nested()

            @sqlalchemy.event.listens_for(session, "after_transaction_end")
            def restart_savepoint(session, transaction):
                if transaction.nested and not transaction._parent.nested:
                    session.begin_nested()

            yield session

        trans.rollback()


@pytest.fixture
def factories_db_session(monkeypatch, test_db_session) -> db.Session:
    monkeypatch.setattr(factories, "_db_session", test_db_session)
    logger.info("set factories db_session to %s", test_db_session)
    return test_db_session


@pytest.fixture
def isolated_db_factories_session(monkeypatch, isolated_db: db.DBClient) -> db.Session:
    with isolated_db.get_session() as session:
        monkeypatch.setattr(factories, "_db_session", session)
        logger.info("set factories db_session to %s", session)
        yield session


@pytest.fixture
def test_logger():
    return logging.init(__package__)


####################
# Test App & Client
####################


@pytest.fixture
def app(db_client, test_logger):
    return app_entry.create_app(db_client=db_client, app_logger=test_logger)


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
