import dataclasses
from typing import Type

import marshmallow

missing = marshmallow.missing

# Type of `missing` used for type annotations
Missing = Type[missing]


@dataclasses.dataclass
class RequestModel:
    """Base class for request models.

    Request models are used to define input schemas for
    API endpoints. They are used to store the request body after deserializing
    the request body.

    The RequestModel class is used as a base class for request models.
    It provides a `as_dict` method that can be used to convert the
    request model to a dictionary. This is useful to unpack the data to be
    passed into db model constructors. The reason this method exists even
    though dataclasses.asdict does something similar is because this method
    will exclude fields that are `missing` rather than include them with
    null values. This is useful to differentiate between a "PATCH {field: null}"
    request that is setting a field to null and a PATCH request that intends
    to leave the field unchanged while modifying other fields.
    """

    def as_dict(self) -> dict:
        """Convert the request model to a dictionary and exclude missing fields
        Recursively converts nested request models to dictionaries.
        """

        all_fields = dataclasses.asdict(self)
        result = {}
        for key, value in all_fields.items():
            if value is missing:
                continue
            if not isinstance(value, RequestModel):
                result[key] = value
                continue
            result[key] = value.as_dict()
        return result
