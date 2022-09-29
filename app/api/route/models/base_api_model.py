from typing import ClassVar, Type

from marshmallow import Schema  # noqa: F401
from marshmallow_dataclass import dataclass as marshmallow_dataclass


@marshmallow_dataclass
class BaseApiModel:
    # Adding this to the base model helps
    # mypy recognize the .Schema that is dynamically
    # added by marshmallow_dataclass
    Schema: ClassVar[Type[Schema]] = Schema  # noqa: F811
