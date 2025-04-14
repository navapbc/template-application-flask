import logging
from typing import Any

import src.adapters.db as db
import src.adapters.db.flask_db as flask_db
import src.api.response as response
import src.api.leave_program.claimant_schemas as claimant_schemas
import src.services.leave_program.claimant_service as claimant_service
from src.api.leave_program.claimant_blueprint import claimant_blueprint
from src.auth.api_key_auth import api_key_auth
from src.db.models.leave_program import Claimant

logger = logging.getLogger(__name__)


@claimant_blueprint.post("/v1/claimants")
@claimant_blueprint.input(claimant_schemas.ClaimantSchema, arg_name="claimant_params")
@claimant_blueprint.output(claimant_schemas.ClaimantSchema, status_code=201)
@claimant_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claimant_post(
    db_session: db.Session, claimant_params: claimant_service.CreateClaimantParams
) -> response.ApiResponse:
    """
    POST /v1/claimants
    Create a new claimant
    """
    claimant = claimant_service.create_claimant(db_session, claimant_params)
    logger.info("Successfully created claimant", extra=get_claimant_log_params(claimant))
    return response.ApiResponse(message="Success", data=claimant)


@claimant_blueprint.patch("/v1/claimants/<uuid:claimant_id>")
@claimant_blueprint.input(claimant_schemas.ClaimantSchema(partial=True), arg_name="patch_claimant_params")
@claimant_blueprint.output(claimant_schemas.ClaimantSchema)
@claimant_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claimant_patch(
    db_session: db.Session,
    claimant_id: str,
    patch_claimant_params: claimant_service.PatchClaimantParams,
) -> response.ApiResponse:
    """
    PATCH /v1/claimants/<claimant_id>
    Update a claimant's information
    """
    claimant = claimant_service.patch_claimant(db_session, claimant_id, patch_claimant_params)
    logger.info("Successfully patched claimant", extra=get_claimant_log_params(claimant))
    return response.ApiResponse(message="Success", data=claimant)


@claimant_blueprint.get("/v1/claimants/<uuid:claimant_id>")
@claimant_blueprint.output(claimant_schemas.ClaimantSchema)
@claimant_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claimant_get(db_session: db.Session, claimant_id: str) -> response.ApiResponse:
    """
    GET /v1/claimants/<claimant_id>
    Get a claimant's information
    """
    claimant = claimant_service.get_claimant(db_session, claimant_id)
    logger.info("Successfully fetched claimant", extra=get_claimant_log_params(claimant))
    return response.ApiResponse(message="Success", data=claimant)


@claimant_blueprint.post("/v1/claimants/search")
@claimant_blueprint.input(claimant_schemas.ClaimantSearchSchema, arg_name="search_params")
@claimant_blueprint.output(claimant_schemas.ClaimantSchema(many=True))
@claimant_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claimant_search(db_session: db.Session, search_params: dict) -> response.ApiResponse:
    """
    POST /v1/claimants/search
    Search for claimants
    """
    claimant_result, pagination_info = claimant_service.search_claimant(db_session, search_params)
    logger.info("Successfully searched claimants")
    return response.ApiResponse(message="Success", data=claimant_result, pagination_info=pagination_info)


def get_claimant_log_params(claimant: Claimant) -> dict[str, Any]:
    return {"claimant.id": claimant.id}
