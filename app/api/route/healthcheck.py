from typing import Tuple

import marshmallow
from apiflask import APIBlueprint
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
from api.route import response
from api.route.api_context import api_context_manager

logger = api.logging.get_logger(__name__)


class HealthcheckSchema(marshmallow.Schema):
    message: str


healthcheck_blueprint = APIBlueprint("healthcheck", __name__, tag="Health")


@healthcheck_blueprint.get("/health")
@healthcheck_blueprint.output(HealthcheckSchema)
def health() -> Tuple[dict, int]:
    logger.info("GET /v1/health")

    try:
        with api_context_manager(is_user_expected=False) as api_context:
            result = api_context.db_session.execute(text("SELECT 1 AS healthy")).first()
            if not result or result[0] != 1:
                raise Exception("Connection to DB failure")

            return response.ApiResponse(message="Service healthy").as_flask_response()

    except Exception:
        logger.exception("Connection to DB failure")

        return response.ApiResponse(
            status_code=ServiceUnavailable.code, message="Service unavailable"
        ).as_flask_response()
