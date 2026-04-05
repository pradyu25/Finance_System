"""
Custom exception hierarchy
===========================
All application-specific exceptions inherit from :class:`AppException` so
that a single FastAPI exception handler can produce consistent JSON error
responses across the entire codebase.
"""

from http import HTTPStatus


class AppException(Exception):
    """Base exception — do not raise directly; use the subclasses below."""

    status_code: int = 500
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.__class__.message
        super().__init__(self.message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""
    status_code = 404
    message = "Resource not found."


class UnauthorizedError(AppException):
    """Raised when authentication credentials are missing or invalid."""
    status_code = 401
    message = "Authentication required."


class ForbiddenError(AppException):
    """Raised when the authenticated user lacks the required role."""
    status_code = 403
    message = "You do not have permission to perform this action."


class ConflictError(AppException):
    """Raised when a uniqueness constraint is violated (e.g. duplicate email)."""
    status_code = 409
    message = "A resource with these details already exists."


class ValidationError(AppException):
    """Raised when business-rule validation fails (complements Pydantic)."""
    status_code = 422
    message = "Validation failed."


class BadRequestError(AppException):
    """Raised for generic bad client requests."""
    status_code = 400
    message = "Bad request."
