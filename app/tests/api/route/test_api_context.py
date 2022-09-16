import pytest
from flask import g

from api.route.api_context import api_context_manager


def test_get_api_context(app, test_db_session):
    # Verify that you can grab the API context
    # so long as the DB session & current user
    # are attached to the flask global
    with app.app.test_request_context():
        g.db = test_db_session
        g.current_user = "current user"

        with api_context_manager() as context_manager:
            assert context_manager.db_session == test_db_session
            assert context_manager.current_user == "current user"
            assert context_manager.request_body == {}  # the default


def test_get_api_context_no_current_request(app):
    # You can't get the DB session from the App if there
    # isn't a request ("g.db" gets set in a handler before the request starts)
    with app.app.app_context():
        # The app exists inside this block, but no request has started
        with pytest.raises(Exception, match="No database session available in application context"):
            with api_context_manager():
                # Need to call it like this so it actually fails
                pass


def test_get_api_context_no_current_app(app):
    # You can't get an API context if the app isn't running
    with pytest.raises(RuntimeError, match="Working outside of application context."):
        with api_context_manager():
            # Need to call it like this so it actually fails
            pass
