import os
import unittest.mock
from datetime import datetime

import factory
import factory.fuzzy
import faker

import api.db as db
import api.db.models.user_models as user_models
import api.util.datetime_util as datetime_util

db_session = None

fake = faker.Faker()


def get_db_session() -> db.scoped_session:
    global db_session

    if os.getenv("DB_FACTORIES_DISABLE_DB_ACCESS", "0") == "1":
        alert_db_session = unittest.mock.MagicMock()
        alert_db_session.add.side_effect = Exception(
            """DB_FACTORIES_DISABLE_DB_ACCESS is set, refusing database action.

            If your tests don't need to cover database behavior, consider
            calling the `build()` method instead of `create()` on the factory to
            not persist the generated model.

            If running tests that actually need data in the DB, pull in the
            `initialize_factories_session` fixture.

            If running factories outside of the tests and you see this, unset
            the DB_FACTORIES_DISABLE_DB_ACCESS env var.
            """
        )
        return alert_db_session

    if db_session is None:
        db_session = db.init()

    return db_session


Session = db.scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())  # type: ignore


class Generators:
    Now = factory.LazyFunction(datetime.now)
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class RoleAssignmentFactory(BaseFactory):
    class Meta:
        model = user_models.RoleAssignment

    user_id = factory.LazyAttribute(lambda u: u.user.id)
    user = factory.SubFactory("tests.api.db.models.factories.UserFactory", roles=[])

    role = factory.Iterator([r.value for r in user_models.RoleEnum])


class UserFactory(BaseFactory):
    class Meta:
        model = user_models.User

    id = Generators.UuidObj
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = "123-456-7890"
    date_of_birth = factory.Faker("date_object")
    is_active = factory.Faker("boolean")

    roles = factory.RelatedFactoryList(RoleAssignmentFactory, size=2, factory_related_name="user")
