from dataclasses import fields
from typing import Any, Iterable

from marshmallow_dataclass import dataclass as marshmallow_dataclass

import api.logging
from api.route.api_context import ApiContext
from api.route.models.base_api_model import BaseApiModel

logger = api.logging.get_logger(__name__)

PARAM_UNSET_IN_REQUEST: str = "PARAM_UNSET_IN_REQUEST"


@marshmallow_dataclass
class BaseRequestModel(BaseApiModel):
    def get_set_params(self, api_context: ApiContext) -> Iterable[tuple[str, Any]]:
        """
        Get an iterable that gives all params that
        were explicitly set in the request.

        This is necessary as dataclasses don't keep track
        of the parameters passed into them, and have to either
        be called with all parameters (which APIFlask defaults
        to be null for unset params) OR have defaults on the
        generated init function which would require a separate
        valid default for every type.

        Note that this does not handle recursively checking
        params inside of the request, and only top-level
        keys will be checked.
        """
        for field_item in fields(self):
            key = field_item.name

            if key not in api_context.request_body:
                continue

            yield key, getattr(self, key)
