class ServiceError(Exception):
    """Base class for service layer errors"""

    pass


class NotFoundError(ServiceError):
    """Raised when a requested resource is not found"""

    pass


class ValidationError(ServiceError):
    """Raised when input validation fails"""

    pass


class AuthorizationError(ServiceError):
    """Raised when a user is not authorized to perform an action"""

    pass
