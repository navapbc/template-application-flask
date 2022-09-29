import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional, Type

from apiflask.validators import OneOf, Regexp, Validator

import api.logging

logger = api.logging.get_logger(__name__)

PARAM_UNSET_IN_REQUEST: str = "PARAM_UNSET_IN_REQUEST"


@dataclass
class ParamFieldConfig:
    example: Optional[str | bool | int] = None
    description: Optional[str] = None
    allowed_values: Optional[Iterable | Type[Enum]] = None
    regex: Optional[str] = None

    def build(self, **overrides: Any) -> Any:
        """
        Construct a call to the dataclass `field` function.
        Overrides allows you to override parameter defaults
        on a ParamFieldConfig object. For example, if you
        wanted to change just the description field

        Many of these parameters are passed through to the
        underlying Marshmallow logic that generates the
        OpenAPI docs. As this requires a bit of nested
        dictionaries, this method is a utility to help
        simplify that process. An example field might look
        like:

        ... = field(
            metadata = {
                "validate": [
                    RegExp("..."),
                    OneOf(["a", "b", "c"])
                    ], # See https://marshmallow.readthedocs.io/en/stable/marshmallow.validate.html#api-validators

                # a 2nd metadata object
                # inside of the first contains
                # additional fields
                "metadata": {
                    "example": "a",
                    "description": "description of the model"
                }
            }
        )
        """
        return field(**self._build(**overrides))

    def _build(self, **overrides: Any) -> dict[str, Any]:
        """
        Internal method for building out
        the params used by build()
        """
        params: dict[str, Any] = {}
        metadata: dict[str, Any] = {}
        validators: list[Validator] = self._validators()

        if validators:
            metadata["validate"] = validators

        inner_metadata = {}

        if (description := self._get_value("description", **overrides)) is not None:
            inner_metadata["description"] = description

        if (example := self._get_value("example", **overrides)) is not None:
            inner_metadata["example"] = example

        metadata["metadata"] = inner_metadata
        params["metadata"] = metadata

        return params

    def _get_value(self, key: str, **overrides: Any) -> Optional[Any]:
        if key in overrides:
            return overrides.get(key)

        return getattr(self, key, None)

    def _validators(self) -> list[Validator]:
        validators: list[Validator] = []

        if self.allowed_values is not None:
            if inspect.isclass(self.allowed_values) and issubclass(self.allowed_values, Enum):
                validators.append(OneOf([e.value for e in self.allowed_values]))  # type: ignore
            else:
                validators.append(OneOf(self.allowed_values))

        if self.regex:
            validators.append(Regexp(self.regex))

        return validators


class ParamSchema:
    first_name = ParamFieldConfig(example="Jane", description="first name of the person")
    middle_name = ParamFieldConfig(example="Anne", description="middle name of the person")
    last_name = ParamFieldConfig(example="Doe", description="last name of the person")
    phone_number = ParamFieldConfig(
        example="123-456-7890", regex=r"^([0-9]|\*){3}\-([0-9]|\*){3}\-[0-9]{4}$"
    )
    date = ParamFieldConfig(example="2022-01-15")
    datetime = ParamFieldConfig(example="2022-01-15T12:00:00.000000+00:00")
    uuid = ParamFieldConfig(example="2f0f58a0-fcad-465b-b474-ee6c961cd6e3")
    bool = ParamFieldConfig(example=True)
