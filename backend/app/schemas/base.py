"""
Base Pydantic schemas for the application.

Defines common patterns for request/response models including
pagination, sorting, and standardized API responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
    )


class TimestampedSchema(BaseSchema):
    """Schema with created/updated timestamps."""
    
    created_at: datetime = Field(
        ..., 
        description="When the record was created",
        examples=["2026-04-26T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ..., 
        description="When the record was last updated",
        examples=["2026-04-26T10:30:00Z"]
    )


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseSchema):
    """Pagination query parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
        examples=[1]
    )
    per_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
        examples=[20]
    )
    
    @property
    def offset(self) -> int:
        """Calculate database offset."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Return limit for database query."""
        return self.per_page


T = TypeVar("T")


class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""
    
    items: List[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseSchema):
    """Error detail information."""
    
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the error occurred"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracking"
    )


class BaseResponse(BaseSchema, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = Field(
        default=True,
        description="Whether the request was successful"
    )
    data: Optional[T] = Field(
        default=None,
        description="Response data"
    )
    error: Optional[ErrorDetail] = Field(
        default=None,
        description="Error information if request failed"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    @classmethod
    def success_response(cls, data: T, meta: Optional[Dict] = None) -> "BaseResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data, meta=meta)
    
    @classmethod
    def error_response(
        cls,
        code: int,
        message: str,
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> "BaseResponse[T]":
        """Create an error response."""
        error = ErrorDetail(
            code=code,
            message=message,
            details=details,
            request_id=request_id
        )
        return cls(success=False, error=error)


class IdResponse(BaseSchema):
    """Simple ID response."""
    
    id: UUID = Field(..., description="Unique identifier")


class MessageResponse(BaseSchema):
    """Simple message response."""
    
    message: str = Field(..., description="Response message")


class HealthCheckResponse(BaseSchema):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current timestamp"
    )
    checks: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed health check results"
    )