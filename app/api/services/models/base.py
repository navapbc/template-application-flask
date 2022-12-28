# Base class for handling input params for PATCH endpoints.
# Persist the original JSON input in _fields_set, so that
# we can determine which values were set by the user, and
# which were omitted.
class PatchParamsBase:
    _fields_set: dict = {}

    def __init__(self, **kwargs: dict):
        self._fields_set = kwargs

    def get_set_params(self) -> dict:
        return self._fields_set
