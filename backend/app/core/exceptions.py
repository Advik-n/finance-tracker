"""
Custom exceptions for the application.
"""

from typing import Any


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.errors = errors
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed", detail: str | None = None):
        super().__init__(message=message, status_code=401, detail=detail)


class AuthorizationError(AppException):
    """Authorization related errors."""

    def __init__(self, message: str = "Access denied", detail: str | None = None):
        super().__init__(message=message, status_code=403, detail=detail)


class NotFoundError(AppException):
    """Resource not found errors."""

    def __init__(self, message: str = "Resource not found", detail: str | None = None):
        super().__init__(message=message, status_code=404, detail=detail)


class ValidationError(AppException):
    """Validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message=message, status_code=422, errors=errors)


class ConflictError(AppException):
    """Conflict errors (e.g., duplicate resource)."""

    def __init__(self, message: str = "Resource conflict", detail: str | None = None):
        super().__init__(message=message, status_code=409, detail=detail)


class RateLimitError(AppException):
    """Rate limit exceeded errors."""

    def __init__(self, message: str = "Rate limit exceeded", detail: str | None = None):
        super().__init__(message=message, status_code=429, detail=detail)


class ServiceError(AppException):
    """External service errors."""

    def __init__(self, message: str = "Service unavailable", detail: str | None = None):
        super().__init__(message=message, status_code=503, detail=detail)


class FileUploadError(AppException):
    """File upload related errors."""

    def __init__(self, message: str = "File upload failed", detail: str | None = None):
        super().__init__(message=message, status_code=400, detail=detail)


class ParsingError(AppException):
    """File parsing errors."""

    def __init__(self, message: str = "File parsing failed", detail: str | None = None):
        super().__init__(message=message, status_code=400, detail=detail)
