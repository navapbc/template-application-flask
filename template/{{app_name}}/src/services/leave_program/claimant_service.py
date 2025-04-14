import logging
from typing import Any, Optional, Tuple
from uuid import UUID

import src.adapters.db as db
from src.db.models.leave_program import Claimant, CommunicationPreference
from src.pagination.pagination import PaginationParams, get_pagination_info
from src.services.exceptions import NotFoundError

logger = logging.getLogger(__name__)


class CreateClaimantParams:
    def __init__(self, **kwargs: Any) -> None:
        self.first_name = kwargs["first_name"]
        self.middle_name = kwargs.get("middle_name")
        self.last_name = kwargs["last_name"]
        self.date_of_birth = kwargs["date_of_birth"]
        self.ssn = kwargs["ssn"]
        self.email = kwargs["email"]
        self.phone_number = kwargs["phone_number"]
        self.street_address = kwargs["street_address"]
        self.city = kwargs["city"]
        self.state = kwargs["state"]
        self.zip_code = kwargs["zip_code"]
        self.communication_preferences = kwargs["communication_preferences"]
        self.payment_method = kwargs.get("payment_method")
        self.bank_account_number = kwargs.get("bank_account_number")
        self.bank_routing_number = kwargs.get("bank_routing_number")


class PatchClaimantParams:
    def __init__(self, **kwargs: Any) -> None:
        self.first_name = kwargs.get("first_name")
        self.middle_name = kwargs.get("middle_name")
        self.last_name = kwargs.get("last_name")
        self.date_of_birth = kwargs.get("date_of_birth")
        self.ssn = kwargs.get("ssn")
        self.email = kwargs.get("email")
        self.phone_number = kwargs.get("phone_number")
        self.street_address = kwargs.get("street_address")
        self.city = kwargs.get("city")
        self.state = kwargs.get("state")
        self.zip_code = kwargs.get("zip_code")
        self.communication_preferences = kwargs.get("communication_preferences")
        self.payment_method = kwargs.get("payment_method")
        self.bank_account_number = kwargs.get("bank_account_number")
        self.bank_routing_number = kwargs.get("bank_routing_number")


def create_claimant(db_session: db.Session, params: CreateClaimantParams) -> Claimant:
    """
    Create a new claimant
    """
    claimant = Claimant(
        first_name=params.first_name,
        middle_name=params.middle_name,
        last_name=params.last_name,
        date_of_birth=params.date_of_birth,
        ssn=params.ssn,
        email=params.email,
        phone_number=params.phone_number,
        street_address=params.street_address,
        city=params.city,
        state=params.state,
        zip_code=params.zip_code,
        payment_method=params.payment_method,
        bank_account_number=params.bank_account_number,
        bank_routing_number=params.bank_routing_number,
    )

    # Add communication preferences
    for pref_type in params.communication_preferences:
        claimant.communication_preferences.append(CommunicationPreference(type=pref_type["type"]))

    db_session.add(claimant)
    db_session.commit()

    return claimant


def patch_claimant(db_session: db.Session, claimant_id: UUID, params: PatchClaimantParams) -> Claimant:
    """
    Update a claimant's information
    """
    claimant = get_claimant(db_session, claimant_id)

    # Update basic fields
    for field in [
        "first_name",
        "middle_name",
        "last_name",
        "date_of_birth",
        "ssn",
        "email",
        "phone_number",
        "street_address",
        "city",
        "state",
        "zip_code",
        "payment_method",
        "bank_account_number",
        "bank_routing_number",
    ]:
        if hasattr(params, field) and getattr(params, field) is not None:
            setattr(claimant, field, getattr(params, field))

    # Update communication preferences if provided
    if params.communication_preferences is not None:
        # Clear existing preferences
        claimant.communication_preferences = []
        # Add new preferences
        for pref_type in params.communication_preferences:
            claimant.communication_preferences.append(CommunicationPreference(type=pref_type["type"]))

    db_session.commit()

    return claimant


def get_claimant(db_session: db.Session, claimant_id: UUID) -> Claimant:
    """
    Get a claimant by ID
    """
    claimant = db_session.query(Claimant).filter(Claimant.id == claimant_id).first()
    if not claimant:
        raise NotFoundError(f"Claimant not found with ID: {claimant_id}")
    return claimant


def search_claimant(db_session: db.Session, search_params: dict) -> Tuple[list[Claimant], dict[str, Any]]:
    """
    Search for claimants
    """
    query = db_session.query(Claimant)

    # Apply filters
    if "first_name" in search_params:
        query = query.filter(Claimant.first_name.ilike(f"%{search_params['first_name']}%"))
    if "last_name" in search_params:
        query = query.filter(Claimant.last_name.ilike(f"%{search_params['last_name']}%"))
    if "email" in search_params:
        query = query.filter(Claimant.email.ilike(f"%{search_params['email']}%"))
    if "phone_number" in search_params:
        query = query.filter(Claimant.phone_number.ilike(f"%{search_params['phone_number']}%"))
    if "ssn" in search_params:
        query = query.filter(Claimant.ssn.ilike(f"%{search_params['ssn']}%"))
    if "is_id_verified" in search_params:
        query = query.filter(Claimant.is_id_verified == search_params["is_id_verified"])

    # Apply pagination
    pagination_params = PaginationParams.from_dict(search_params["paging"])
    query, pagination_info = get_pagination_info(query, pagination_params)

    # Execute query
    claimants = query.all()

    return claimants, pagination_info
