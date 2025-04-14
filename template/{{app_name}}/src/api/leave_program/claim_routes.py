import logging
from typing import Any

import src.adapters.db as db
import src.adapters.db.flask_db as flask_db
import src.api.response as response
import src.api.leave_program.claim_schemas as claim_schemas
import src.services.leave_program.claim_service as claim_service
from src.api.leave_program.claim_blueprint import claim_blueprint
from src.auth.api_key_auth import api_key_auth
from src.db.models.leave_program import Claim

logger = logging.getLogger(__name__)


@claim_blueprint.post("/v1/claims")
@claim_blueprint.input(claim_schemas.ClaimSchema, arg_name="claim_params")
@claim_blueprint.output(claim_schemas.ClaimSchema, status_code=201)
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_post(db_session: db.Session, claim_params: claim_service.CreateClaimParams) -> response.ApiResponse:
    """
    POST /v1/claims
    Create a new claim
    """
    claim = claim_service.create_claim(db_session, claim_params)
    logger.info("Successfully created claim", extra=get_claim_log_params(claim))
    return response.ApiResponse(message="Success", data=claim)


@claim_blueprint.patch("/v1/claims/<uuid:claim_id>")
@claim_blueprint.input(claim_schemas.ClaimSchema(partial=True), arg_name="patch_claim_params")
@claim_blueprint.output(claim_schemas.ClaimSchema)
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_patch(
    db_session: db.Session,
    claim_id: str,
    patch_claim_params: claim_service.PatchClaimParams,
) -> response.ApiResponse:
    """
    PATCH /v1/claims/<claim_id>
    Update a claim's information
    """
    claim = claim_service.patch_claim(db_session, claim_id, patch_claim_params)
    logger.info("Successfully patched claim", extra=get_claim_log_params(claim))
    return response.ApiResponse(message="Success", data=claim)


@claim_blueprint.get("/v1/claims/<uuid:claim_id>")
@claim_blueprint.output(claim_schemas.ClaimSchema)
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_get(db_session: db.Session, claim_id: str) -> response.ApiResponse:
    """
    GET /v1/claims/<claim_id>
    Get a claim's information
    """
    claim = claim_service.get_claim(db_session, claim_id)
    logger.info("Successfully fetched claim", extra=get_claim_log_params(claim))
    return response.ApiResponse(message="Success", data=claim)


@claim_blueprint.post("/v1/claims/search")
@claim_blueprint.input(claim_schemas.ClaimSearchSchema, arg_name="search_params")
@claim_blueprint.output(claim_schemas.ClaimSchema(many=True))
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_search(db_session: db.Session, search_params: dict) -> response.ApiResponse:
    """
    POST /v1/claims/search
    Search for claims
    """
    claim_result, pagination_info = claim_service.search_claim(db_session, search_params)
    logger.info("Successfully searched claims")
    return response.ApiResponse(message="Success", data=claim_result, pagination_info=pagination_info)


@claim_blueprint.post("/v1/claims/<uuid:claim_id>/submit")
@claim_blueprint.output(claim_schemas.ClaimSchema)
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_submit(db_session: db.Session, claim_id: str) -> response.ApiResponse:
    """
    POST /v1/claims/<claim_id>/submit
    Submit a claim for review
    """
    claim = claim_service.submit_claim(db_session, claim_id)
    logger.info("Successfully submitted claim", extra=get_claim_log_params(claim))
    return response.ApiResponse(message="Success", data=claim)


@claim_blueprint.post("/v1/claims/<uuid:claim_id>/appeal")
@claim_blueprint.input(claim_schemas.AppealSchema, arg_name="appeal_params")
@claim_blueprint.output(claim_schemas.ClaimSchema)
@claim_blueprint.auth_required(api_key_auth)
@flask_db.with_db_session()
def claim_appeal(
    db_session: db.Session, claim_id: str, appeal_params: claim_service.CreateAppealParams
) -> response.ApiResponse:
    """
    POST /v1/claims/<claim_id>/appeal
    Appeal a claim decision
    """
    claim = claim_service.create_appeal(db_session, claim_id, appeal_params)
    logger.info("Successfully created appeal", extra=get_claim_log_params(claim))
    return response.ApiResponse(message="Success", data=claim)


def get_claim_log_params(claim: Claim) -> dict[str, Any]:
    return {"claim.id": claim.id}
