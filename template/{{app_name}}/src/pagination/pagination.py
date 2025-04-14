from dataclasses import dataclass
from typing import Any, Tuple

from sqlalchemy.orm import Query


@dataclass
class PaginationParams:
    """Parameters for pagination"""

    page: int
    page_size: int
    sort_by: str
    sort_order: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaginationParams":
        """Create PaginationParams from a dictionary"""
        return cls(
            page=data["page"],
            page_size=data["page_size"],
            sort_by=data["sort_by"],
            sort_order=data["sort_order"],
        )


def get_pagination_info(query: Query, params: PaginationParams) -> Tuple[Query, dict[str, Any]]:
    """
    Apply pagination to a query and return pagination info

    Args:
        query: The SQLAlchemy query to paginate
        params: Pagination parameters

    Returns:
        Tuple of (paginated query, pagination info)
    """
    # Apply sorting
    if params.sort_order.lower() == "desc":
        query = query.order_by(getattr(query.column_descriptions[0]["entity"], params.sort_by).desc())
    else:
        query = query.order_by(getattr(query.column_descriptions[0]["entity"], params.sort_by).asc())

    # Apply pagination
    total = query.count()
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)

    # Calculate pagination info
    total_pages = (total + params.page_size - 1) // params.page_size

    pagination_info = {
        "page": params.page,
        "page_size": params.page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": params.page < total_pages,
        "has_previous": params.page > 1,
    }

    return query, pagination_info
