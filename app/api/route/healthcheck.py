import flask
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
import api.route.response as response_util
from api.route.api_context import api_context_manager
from api.adapters import db

logger = api.logging.get_logger(__name__)


def healthcheck_get() -> flask.Response:
    logger.info("GET /v1/healthcheck")

    try:
        with db.get_connection() as conn:
            conn.execute("SELECT 1 AS healthy")
            return response_util.success_response(message="Service healthy").to_api_response()
    except Exception:
        logger.exception("Connection to DB failure")
        return response_util.error_response(
            status_code=ServiceUnavailable, message="Service unavailable", errors=[]
        ).to_api_response()
