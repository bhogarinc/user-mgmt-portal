"""
Custom exception classes for the application.

Provides structured error handling with HTTP status codes and error codes
for client-side error handling.
"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception.
    
    Attributes:
        status_code: HTTP status code to return
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional error context
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class AuthenticationError(AppException):
    """Authentication failed (invalid credentials, expired token)."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationError(AppException):
    """Authorization failed (insufficient permissions)."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class NotFoundError(AppException):
    """Resource not found."""
    
    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "id": resource_id}
        )


class ValidationError(AppException):
    """Request validation failed."""
    
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors} if errors else {}
        )


class ConflictError(AppException):
    """Resource conflict (duplicate email, etc.)."""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class RateLimitError(AppException):
    """Rate limit exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )
