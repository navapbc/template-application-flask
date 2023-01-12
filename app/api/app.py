import os
from typing import Optional

from apiflask import APIFlask
from flask import g
from werkzeug.exceptions import Unauthorized

import api.db
import api.logging
from api.auth.api_key_auth import User
from api.route.healthcheck import healthcheck_blueprint
from api.route.schemas import response_schema
from api.route.user_route import user_blueprint

logger = api.logging.get_logger(__name__)


def create_app(*, db: api.db.DBClient) -> APIFlask:
    app = APIFlask(__name__)
    db.init_app(app)
    configure_app(app)
    register_blueprints(app)
    return app


def current_user(is_user_expected: bool = True) -> Optional[User]:
    current = g.get("current_user")
    if is_user_expected and current is None:
        logger.error("No current user found for request")
        raise Unauthorized
    return current


def configure_app(app: APIFlask) -> None:
    # Modify the response schema to instead use the format of our ApiResponse class
    # which adds additional details to the object.
    # https://apiflask.com/schema/#base-response-schema-customization
    app.config["BASE_RESPONSE_SCHEMA"] = response_schema.ResponseSchema

    # Set a few values for the Swagger endpoint
    app.config["OPENAPI_VERSION"] = "3.0.3"

    # Set various general OpenAPI config values
    app.info = {
        "title": "Template Application Flask",
        "description": "Template API for a Flask Application",
        "contact": {
            "name": "Nava PBC Engineering",
            "url": "https://www.navapbc.com",
            "email": "engineering@navapbc.com",
        },
    }

    # Set the security schema and define the header param
    # where we expect the API token to reside.
    # See: https://apiflask.com/authentication/#use-external-authentication-library
    app.security_schemes = {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-Auth"}}


def register_blueprints(app: APIFlask) -> None:
    app.register_blueprint(healthcheck_blueprint)
    app.register_blueprint(user_blueprint)


def get_project_root_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..")
