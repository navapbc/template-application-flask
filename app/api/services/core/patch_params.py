import dataclasses
from typing import Generic, TypeVar

ResourceType = TypeVar("ResourceType")


@dataclasses.dataclass
class PatchParams(Generic[ResourceType]):
    """Parameters for patching a resource."""

    resource: ResourceType
    fields_to_patch: list[str]
