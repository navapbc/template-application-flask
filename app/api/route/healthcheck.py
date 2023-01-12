from typing import Tuple

from apiflask import APIBlueprint
from flask import current_app
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
from api.db import DB
from api.route import response
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

    db: DB = current_app.extensions["db"]
    try:
        with db.get_session() as session:
            session.execute(text("SELECT 1 AS healthy")).first()
        return response.ApiResponse(message="Service healthy").asdict(), 200
    except Exception:
        logger.exception("Connection to DB failure")
        return response.ApiResponse(message="Service unavailable").asdict(), ServiceUnavailable.code
