import dataclasses


@dataclasses.dataclass
class RequestModel:
    """Base class for request models.

    Request models are used to define input schemas for
    API endpoints. They are used to store the request body after deserializing
    the request body.
    """

    pass
