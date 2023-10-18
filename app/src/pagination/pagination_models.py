import dataclasses
from enum import StrEnum
from typing import Self

from pydantic import BaseModel

from src.pagination.paginator import Paginator


class SortDirection(StrEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class SortingParams(BaseModel):
    order_by: str
    sort_direction: SortDirection

    @property
    def is_ascending(self) -> bool:
        return self.sort_direction == SortDirection.ASCENDING


class PagingParams(BaseModel):
    page_size: int
    page_offset: int


class PaginationParams(BaseModel):
    sorting: SortingParams
    paging: PagingParams


@dataclasses.dataclass
class PaginationInfo:
    page_offset: int
    page_size: int

    order_by: str
    sort_direction: SortDirection

    total_records: int
    total_pages: int

    @classmethod
    def from_pagination_models(
        cls, pagination_params: PaginationParams, paginator: Paginator
    ) -> Self:
        return cls(
            page_offset=pagination_params.paging.page_offset,
            page_size=pagination_params.paging.page_size,
            order_by=pagination_params.sorting.order_by,
            sort_direction=pagination_params.sorting.sort_direction,
            total_records=paginator.total_records,
            total_pages=paginator.total_pages,
        )
