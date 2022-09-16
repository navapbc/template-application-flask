import flask
from sqlalchemy import text
from werkzeug.exceptions import ServiceUnavailable

import api.logging
import api.route.response as response_util
from api.route.api_context import api_context_manager

logger = api.logging.get_logger(__name__)


def healthcheck_get() -> flask.Response:
    logger.info("GET /v1/healthcheck")

    try:
        with api_context_manager(is_user_expected=False) as api_context:
            result = api_context.db_session.execute(text("SELECT 1 AS healthy")).first()
            if not result or result[0] != 1:
                raise Exception("Connection to DB failure")

            return response_util.success_response(message="Service healthy").to_api_response()

    except Exception:
        logger.exception("Connection to DB failure")

        return response_util.error_response(
            status_code=ServiceUnavailable, message="Service unavailable", errors=[]
        ).to_api_response()
