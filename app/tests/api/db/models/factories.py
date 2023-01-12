"""Factories for generating test data.

These factories are used to generate test data for the tests. They are
used both for generating in memory objects and for generating objects
that are persisted to the database.

The factories are based on the `factory_boy` library. See 
https://factoryboy.readthedocs.io/en/latest/ for more information.
"""
import os
from typing import Optional
import unittest.mock
from datetime import datetime

import factory
import factory.fuzzy
import faker
from sqlalchemy.orm import scoped_session

import api.db
import api.db.models.user_models as user_models
import api.util.datetime_util as datetime_util

_db_session: Optional[api.db.Session] = None

fake = faker.Faker()


def get_db_session() -> api.db.Session:
    # _db_session is only set in the pytest fixture `factories_session`
    # so that tests do not unintentionally write to the database.
    if _db_session is None:
        raise Exception(
            """Factory db_session is not initialized.

            If your tests don't need to cover database behavior, consider
            calling the `build()` method instead of `create()` on the factory to
            not persist the generated model.

            If running tests that actually need data in the DB, pull in the
            `factories_session` fixture to initialize the db_session.
            """
        )

    return _db_session


class Generators:
    Now = factory.LazyFunction(datetime.now)
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = scoped_session(get_db_session)
        sqlalchemy_session_persistence = "commit"


class RoleFactory(BaseFactory):
    class Meta:
        model = user_models.Role

    user_id = factory.LazyAttribute(lambda u: u.user.id)
    user = factory.SubFactory("tests.api.db.models.factories.UserFactory", roles=[])

    type = factory.Iterator([r.value for r in user_models.RoleType])


class UserFactory(BaseFactory):
    class Meta:
        model = user_models.User

    id = Generators.UuidObj
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = "123-456-7890"
    date_of_birth = factory.Faker("date_object")
    is_active = factory.Faker("boolean")

    roles = factory.RelatedFactoryList(RoleFactory, size=2, factory_related_name="user")
