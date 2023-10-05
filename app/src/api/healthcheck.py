import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

import src.adapters.db.fastapi_db as fastapi_db

logger = logging.getLogger(__name__)

healthcheck_router = APIRouter(tags=["healthcheck"])


class HealthcheckModel(BaseModel):
    message: str = Field(examples=["Service healthy"])


@healthcheck_router.get("/health")
def health(request: Request) -> HealthcheckModel:
    try:
        with fastapi_db.get_db_client(request.app).get_connection() as conn:
            assert conn.scalar(text("SELECT 1 AS healthy")) == 1
        return HealthcheckModel(message="Service healthy")
    except Exception as err:
        logger.exception("Connection to DB failure")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable"
        ) from err
