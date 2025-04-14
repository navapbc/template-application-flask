import logging
from typing import Any, Optional, Tuple
from uuid import UUID

import src.adapters.db as db
from src.db.models.leave_program import (
    Appeal,
    Claim,
    ClaimStatus,
    Document,
    Payment,
)
from src.pagination.pagination import PaginationParams, get_pagination_info
from src.services.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class CreateClaimParams:
    def __init__(self, **kwargs: Any) -> None:
        self.claimant_id = kwargs["claimant_id"]
        self.employer_id = kwargs["employer_id"]
        self.leave_type = kwargs["leave_type"]
        self.leave_reason = kwargs["leave_reason"]
        self.start_date = kwargs["start_date"]
        self.end_date = kwargs["end_date"]
        self.weekly_hours = kwargs["weekly_hours"]
        self.weekly_benefit_amount = kwargs.get("weekly_benefit_amount")
        self.total_benefit_amount = kwargs.get("total_benefit_amount")


class PatchClaimParams:
    def __init__(self, **kwargs: Any) -> None:
        self.claimant_id = kwargs.get("claimant_id")
        self.employer_id = kwargs.get("employer_id")
        self.leave_type = kwargs.get("leave_type")
        self.leave_reason = kwargs.get("leave_reason")
        self.start_date = kwargs.get("start_date")
        self.end_date = kwargs.get("end_date")
        self.weekly_hours = kwargs.get("weekly_hours")
        self.weekly_benefit_amount = kwargs.get("weekly_benefit_amount")
        self.total_benefit_amount = kwargs.get("total_benefit_amount")


class CreateAppealParams:
    def __init__(self, **kwargs: Any) -> None:
        self.reason = kwargs["reason"]
        self.status = kwargs.get("status", "PENDING")


def create_claim(db_session: db.Session, params: CreateClaimParams) -> Claim:
    """
    Create a new claim
    """
    claim = Claim(
        claimant_id=params.claimant_id,
        employer_id=params.employer_id,
        leave_type=params.leave_type,
        leave_reason=params.leave_reason,
        start_date=params.start_date,
        end_date=params.end_date,
        weekly_hours=params.weekly_hours,
        weekly_benefit_amount=params.weekly_benefit_amount,
        total_benefit_amount=params.total_benefit_amount,
    )

    db_session.add(claim)
    db_session.commit()

    return claim


def patch_claim(db_session: db.Session, claim_id: UUID, params: PatchClaimParams) -> Claim:
    """
    Update a claim's information
    """
    claim = get_claim(db_session, claim_id)

    # Update basic fields
    for field in [
        "claimant_id",
        "employer_id",
        "leave_type",
        "leave_reason",
        "start_date",
        "end_date",
        "weekly_hours",
        "weekly_benefit_amount",
        "total_benefit_amount",
    ]:
        if hasattr(params, field) and getattr(params, field) is not None:
            setattr(claim, field, getattr(params, field))

    db_session.commit()

    return claim


def get_claim(db_session: db.Session, claim_id: UUID) -> Claim:
    """
    Get a claim by ID
    """
    claim = db_session.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise NotFoundError(f"Claim not found with ID: {claim_id}")
    return claim


def search_claim(db_session: db.Session, search_params: dict) -> Tuple[list[Claim], dict[str, Any]]:
    """
    Search for claims
    """
    query = db_session.query(Claim)

    # Apply filters
    if "claimant_id" in search_params:
        query = query.filter(Claim.claimant_id == search_params["claimant_id"])
    if "employer_id" in search_params:
        query = query.filter(Claim.employer_id == search_params["employer_id"])
    if "leave_type" in search_params:
        query = query.filter(Claim.leave_type == search_params["leave_type"])
    if "leave_reason" in search_params:
        query = query.filter(Claim.leave_reason == search_params["leave_reason"])
    if "status" in search_params:
        query = query.filter(Claim.status == search_params["status"])
    if "start_date" in search_params:
        query = query.filter(Claim.start_date >= search_params["start_date"])
    if "end_date" in search_params:
        query = query.filter(Claim.end_date <= search_params["end_date"])

    # Apply pagination
    pagination_params = PaginationParams.from_dict(search_params["paging"])
    query, pagination_info = get_pagination_info(query, pagination_params)

    # Execute query
    claims = query.all()

    return claims, pagination_info


def submit_claim(db_session: db.Session, claim_id: UUID) -> Claim:
    """
    Submit a claim for review
    """
    claim = get_claim(db_session, claim_id)

    # Validate claim can be submitted
    if claim.status != ClaimStatus.DRAFT:
        raise ValidationError(f"Cannot submit claim in status: {claim.status}")

    # Update status
    claim.status = ClaimStatus.SUBMITTED
    db_session.commit()

    return claim


def create_appeal(db_session: db.Session, claim_id: UUID, params: CreateAppealParams) -> Claim:
    """
    Create an appeal for a claim
    """
    claim = get_claim(db_session, claim_id)

    # Validate claim can be appealed
    if claim.status not in [ClaimStatus.DENIED, ClaimStatus.APPEALED]:
        raise ValidationError(f"Cannot appeal claim in status: {claim.status}")

    # Create appeal
    appeal = Appeal(
        claim_id=claim_id,
        reason=params.reason,
        status=params.status,
    )

    # Update claim status
    claim.status = ClaimStatus.APPEALED

    db_session.add(appeal)
    db_session.commit()

    return claim
