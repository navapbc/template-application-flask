from typing import Tuple

from apiflask import APIBlueprint
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
from api import db
from api.route import response
from api.route.api_context import api_context_manager
from api.route.schemas import request_schema

logger = api.logging.get_logger(__name__)


class HealthcheckSchema(request_schema.OrderedSchema):
    message: str


healthcheck_blueprint = APIBlueprint("healthcheck", __name__, tag="Health")


@healthcheck_blueprint.get("/health")
@healthcheck_blueprint.output(HealthcheckSchema)
@healthcheck_blueprint.doc(responses=[200, ServiceUnavailable.code])
def health() -> Tuple[dict, int]:
    logger.info("GET /v1/health")

    try:
        result = db.session.execute(text("SELECT 1 AS healthy")).first()
        if not result or result[0] != 1:
            raise Exception("Connection to DB failure")

        return response.ApiResponse(message="Service healthy").asdict(), 200

    except Exception:
        logger.exception("Connection to DB failure")

        return response.ApiResponse(message="Service unavailable").asdict(), ServiceUnavailable.code
