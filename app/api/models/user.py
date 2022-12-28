# base class for handling params for PATCH endpoints
# persist the original JSON dict in _fields_set, so
# that we can determine which values were set by the user
class PatchParamsBase:
    _fields_set: dict = None

    def __init__(self, **kwargs: dict):
        self._fields_set = kwargs

    def get_set_params(self) -> dict:
        return self._fields_set


# inherit from PatchParamsBase, to set params in a dict
class UserPatchParams(PatchParamsBase):
    pass
