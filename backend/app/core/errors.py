"""
Error handling module for User Management Portal.

This module provides standardized error handling, custom exceptions,
and error response formatting for the application.

GitHub Issue: HLD-005
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class ErrorCode(Enum):
    """
    Standardized error codes for the User Management Portal.
    
    Format: {category}{sequence} = (code, http_status, message)
    
    Categories:
    - 1xxx: Authentication/Authorization
    - 2xxx: Validation
    - 3xxx: Resource
    - 4xxx: System
    """
    
    # 1xxx: Authentication/Authorization
    AUTH_INVALID_CREDENTIALS = (1001, 401, "Invalid email or password")
    AUTH_TOKEN_EXPIRED = (1002, 401, "Authentication token has expired")
    AUTH_TOKEN_INVALID = (1003, 401, "Invalid authentication token")
    AUTH_INSUFFICIENT_PERMISSIONS = (1004, 403, "Insufficient permissions for this operation")
    AUTH_ACCOUNT_LOCKED = (1005, 403, "Account is temporarily locked")
    AUTH_MFA_REQUIRED = (1006, 401, "Multi-factor authentication required")
    AUTH_MFA_INVALID = (1007, 401, "Invalid multi-factor authentication code")
    AUTH_SESSION_EXPIRED = (1008, 401, "Session has expired")
    
    # 2xxx: Validation
    VALIDATION_FAILED = (2001, 422, "Request validation failed")
    VALIDATION_REQUIRED_FIELD = (2002, 422, "Required field missing")
    VALIDATION_INVALID_FORMAT = (2003, 400, "Invalid data format")
    VALIDATION_INVALID_LENGTH = (2004, 400, "Field length invalid")
    VALIDATION_INVALID_RANGE = (2005, 400, "Value outside valid range")
    VALIDATION_INVALID_ENUM = (2006, 400, "Invalid value for field")
    
    # 3xxx: Resource
    USER_NOT_FOUND = (3001, 404, "User not found")
    ROLE_NOT_FOUND = (3002, 404, "Role not found")
    PERMISSION_NOT_FOUND = (3003, 404, "Permission not found")
    RESOURCE_NOT_FOUND = (3004, 404, "Resource not found")
    RESOURCE_CONFLICT = (3005, 409, "Resource conflict detected")
    RESOURCE_ALREADY_EXISTS = (3006, 409, "Resource already exists")
    RESOURCE_GONE = (3007, 410, "Resource has been permanently removed")
    
    # 4xxx: System
    DATABASE_ERROR = (4001, 500, "Database operation failed")
    DATABASE_CONNECTION_ERROR = (4002, 503, "Database connection failed")
    EXTERNAL_SERVICE_ERROR = (4003, 502, "External service unavailable")
    CACHE_ERROR = (4004, 503, "Cache service unavailable")
    RATE_LIMIT_EXCEEDED = (4005, 429, "Rate limit exceeded")
    INTERNAL_ERROR = (4006, 500, "Internal server error")
    SERVICE_UNAVAILABLE = (4007, 503, "Service temporarily unavailable")
    
    def __init__(self, code: int, http_status: int, message: str):
        self.code = code
        self.http_status = http_status
        self.message = message
    
    @property
    def category(self) -> str:
        """Get error category from code prefix."""
        categories = {
            '1': 'Authentication',
            '2': 'Validation',
            '3': 'Resource',
            '4': 'System'
        }
        return categories.get(str(self.code)[0], 'Unknown')


class ErrorDetails(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    constraint: Optional[str] = None
    provided: Optional[Any] = None
    required: Optional[Any] = None
    suggestions: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    code: int
    message: str
    category: str
    details: Optional[ErrorDetails] = None
    trace_id: str
    request_id: str
    timestamp: str
    path: str
    documentation_url: str
    retryable: bool = False


class UMPException(Exception):
    """
    Base exception for User Management Portal.
    
    Attributes:
        error_code: The ErrorCode enum value
        details: Additional error context
        sensitive: Whether to hide details in response
        retryable: Whether client should retry
    """
    
    def __init__(
        self,
        error_code: ErrorCode,
        details: Optional[Dict] = None,
        sensitive: bool = False,
        retryable: bool = False
    ):
        self.error_code = error_code
        self.details = details
        self.sensitive = sensitive
        self.retryable = retryable
        super().__init__(error_code.message)
    
    def to_response(self, trace_id: str, request_id: str, path: str) -> Dict:
        """Convert exception to standardized response format."""
        return {
            "error": {
                "code": self.error_code.code,
                "message": self.error_code.message if not self.sensitive else "An error occurred",
                "category": self.error_code.category,
                "details": self.details,
                "trace_id": trace_id,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat(),
                "path": path,
                "documentation_url": f"https://docs.ump.io/errors/{self.error_code.code}",
                "retryable": self.retryable
            }
        }


class AuthenticationError(UMPException):
    """Authentication-related errors."""
    pass


class ValidationError(UMPException):
    """Validation-related errors."""
    pass


class ResourceError(UMPException):
    """Resource-related errors."""
    pass


class SystemError(UMPException):
    """System-related errors."""
    pass


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
