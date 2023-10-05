import logging

import fastapi
import fastapi.params
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette_context.middleware import RawContextMiddleware

import src.adapters.db as db
import src.adapters.db.fastapi_db as fastapi_db
import src.logger
import src.logger.fastapi_logger as fastapi_logger
from src.api.healthcheck import healthcheck_router
from src.api.index import index_router
from src.api.users.user_routes import user_router
from src.app_config import AppConfig

logger = logging.getLogger(__name__)


def create_app() -> fastapi.FastAPI:
    src.logger.init(__package__)

    app = fastapi.FastAPI(
        # Fields which appear on the OpenAPI docs
        # title appears at the top of the OpenAPI page as well attached to all logs as "app.name"
        title="Template Application FastAPI",
        description="Template for a FastAPI Application",
        contact={
            "name": "Nava PBC Engineering",
            "url": "https://www.navapbc.com",
            "email": "engineering@navapbc.com",
        },
        # Global dependencies of every API endpoint
        dependencies=get_global_dependencies(),
    )

    fastapi_logger.init_app(logging.root, app)

    configure_exception_handling(app)

    db_client = db.PostgresDBClient()
    fastapi_db.register_db_client(db_client, app)

    register_routers(app)

    # Add this middleware last so that every other middleware has access to the context
    # object we use to pass logging information around with. Middlewares work like a stack so
    # the last one added is the first one executed.
    app.add_middleware(RawContextMiddleware)

    logger.info("Creating app")
    return app


def get_global_dependencies() -> list[fastapi.params.Depends]:
    return [fastapi.Depends(fastapi_logger.add_url_rule_to_request_context)]


def register_routers(app: fastapi.FastAPI) -> None:
    app.include_router(index_router)
    app.include_router(healthcheck_router)
    app.include_router(user_router)


def configure_exception_handling(app: fastapi.FastAPI) -> None:

    # Pydantic v2 by default returns a URL for each validation error pointing to their documentation
    # which makes the errors overly verbose. We trim that out here before returning the error.
    # See: https://fastapi.tiangolo.com/tutorial/handling-errors/?h=handlin#override-request-validation-exceptions
    #
    # If you would like to modify the format of the errors from Pydantic, you can restructure the response object here.
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: fastapi.Request, exc: RequestValidationError
    ) -> JSONResponse:
        # This matches the default request validation handler, but excludes the URL from the validation error.
        return JSONResponse(
            status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": jsonable_encoder(exc.errors(), exclude={"url"})},
        )

    # TODO - do this a bit better, this is to prevent PII from being logged
    #      - should open a ticket against FastAPI as this looks like a relatively recent change:
    #      - https://github.com/tiangolo/fastapi/pull/10078
    def override_method(self: ResponseValidationError) -> str:
        return f"{len(self._errors)} validation errors:\n"

    ResponseValidationError.__str__ = override_method  # type: ignore


if __name__ == "__main__":
    app_config = AppConfig()

    uvicorn_params: dict = {
        "host": app_config.host,
        "port": app_config.port,
        "factory": True,
        "app_dir": "src/",
    }
    if app_config.use_reloader:
        uvicorn_params["reload"] = True
    else:
        uvicorn_params["workers"] = 4

    uvicorn.run("app:create_app", **uvicorn_params)
