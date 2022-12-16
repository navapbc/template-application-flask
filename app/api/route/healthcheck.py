import flask
import marshmallow
from apiflask import APIBlueprint
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
import api.route.response as response_util
from api.route.api_context import api_context_manager

logger = api.logging.get_logger(__name__)


class HealthOut(marshmallow.Schema):
    message: str


healthcheck_blueprint = APIBlueprint("healthcheck", __name__, tag="Health")


@healthcheck_blueprint.get("/health")
@healthcheck_blueprint.output(HealthOut)
def health() -> flask.Response:
    logger.info("GET /v1/health")

    try:
        with api_context_manager(is_user_expected=False) as api_context:
            result = api_context.db_session.execute(text("SELECT 1 AS healthy")).first()
            if not result or result[0] != 1:
                raise Exception("Connection to DB failure")

            return response_util.success_response(message="Service healthy")

    except Exception:
        logger.exception("Connection to DB failure")

        return response_util.error_response(
            status_code=ServiceUnavailable, message="Service unavailable", errors=[]
        )
