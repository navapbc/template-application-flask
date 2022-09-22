from datetime import date, datetime

import pytest

from api.db.models.user_models import User
from tests.api.db.models.factories import UserFactory, UserRoleFactory

user_params = {
    "first_name": "Alvin",
    "middle_name": "Bob",
    "last_name": "Chester",
    "phone_number": "999-999-9999",
    "date_of_birth": date(2022, 1, 1),
    "is_active": False,
}


def validate_user_record(user: User, user_expected_values=None):
    if user_expected_values:
        assert user.user_id is not None
        for k, v in user_expected_values.items():
            user_v = getattr(user, k)
            if k == "roles":
                user_role_ids = set([role.role_id for role in user_v])
                expected_role_ids = set([role.role_id for role in v])
                assert user_role_ids == expected_role_ids
            else:
                if isinstance(user_v, datetime):
                    user_v = user_v.isoformat()

                assert str(user_v) == str(v)

    else:
        # Otherwise just validate the values are set
        assert user.user_id is not None
        assert user.first_name is not None
        assert user.last_name is not None
        assert user.phone_number is not None
        assert user.date_of_birth is not None
        assert user.is_active is not None
        assert user.roles is not None


def test_user_factory_build():
    # Build doesn't use the DB

    # Build sets the values
    user = UserFactory.build()
    validate_user_record(user)

    user = UserFactory.build(**user_params)
    validate_user_record(user, user_params)


def test_factory_create_uninitialized_db_session(test_db_session):
    # DB factory access is disabled from tests unless you add the
    # 'initialize_factories_session' fixture.
    with pytest.raises(Exception, match="DB_FACTORIES_DISABLE_DB_ACCESS is set"):
        UserFactory.create()


def test_user_factory_create(test_db_session, initialize_factories_session):
    # Create actually writes a record to the DB when run
    # so we'll check the DB directly as well.
    user = UserFactory.create()
    validate_user_record(user)

    db_record = test_db_session.query(User).filter(User.user_id == user.user_id).one_or_none()
    # Make certain the DB record matches the factory one.
    validate_user_record(db_record, user.for_json())

    user = UserFactory.create(**user_params)
    validate_user_record(user, user_params)

    db_record = test_db_session.query(User).filter(User.user_id == user.user_id).one_or_none()
    # Make certain the DB record matches the factory one.
    validate_user_record(db_record, db_record.for_json())

    # Make certain nullable fields can be overriden
    null_params = {"middle_name": None}
    user = UserFactory.create(**null_params)
    validate_user_record(user, null_params)

    all_db_records = test_db_session.query(User).all()
    assert len(all_db_records) == 3


def test_user_role_factory_create(test_db_session, initialize_factories_session):
    # Verify if you build a UserRole directly, it gets
    # a user attached to it with that single role
    user_role = UserRoleFactory.create()
    assert user_role.user is not None
    assert len(user_role.user.roles) == 1
