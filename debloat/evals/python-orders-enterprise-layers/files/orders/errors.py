class OrderError(Exception):
    """Base class for order errors."""

    pass


class ValidationError(OrderError):
    """Raised when an order is invalid."""

    pass


class NotFoundError(OrderError):
    """Raised when an order does not exist."""

    pass


class ConflictError(OrderError):
    """Raised when two orders conflict."""

    pass
