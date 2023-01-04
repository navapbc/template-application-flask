import dataclasses
from typing import Any, Iterator, Tuple


class Missing:
    """The type of `missing`
    `missing` is a singleton sentinel value to indicate that a field was not set.
    """

    pass


# A singleton sentinel value to indicate that a field was not set.
# This is used to differentiate between a field that was set to None and a
# field that was not set at all.
missing = Missing()


def fields_to_patch(obj: Any) -> Iterator[Tuple[str, Any]]:
    """Yield (name, value) pairs for all fields in `obj` that are not `missing`"""
    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if value is not missing:
            yield field.name, getattr(obj, field.name)
