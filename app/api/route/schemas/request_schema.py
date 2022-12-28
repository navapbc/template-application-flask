import dataclasses

import apiflask


@dataclasses.dataclass
class RequestModel:
    """Base class for request models.

    Request models are used to define input schemas for
    API endpoints. They are used to store the request body after deserializing
    the request body.
    """

    pass


# Use ordered schemas to ensure that the order of fields in the generated OpenAPI
# schema is deterministic.
# This should no longer be needed once apiflask is updated to use ordered schemas
# TODO update apiflask with fix to default to ordered schemas
# See https://github.com/apiflask/apiflask/issues/385#issuecomment-1364463104
class OrderedSchema(apiflask.Schema):
    class Meta:
        ordered = True
