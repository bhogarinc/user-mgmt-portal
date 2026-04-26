"""
User-related Pydantic schemas.

Defines request/response models for user management operations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse, TimestampedSchema


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    LOCKED = "locked"


class UserBase(BaseSchema):
    """Base user schema with common fields."""
    
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="User email address",
        examples=["user@example.com"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Unique username (alphanumeric, underscore, hyphen)",
        examples=["johndoe"]
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name",
        examples=["John"]
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name",
        examples=["Doe"]
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account is active"
    )


class UserCreate(UserBase):
    """User creation request schema."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (8+ chars, uppercase, lowercase, digit, special)",
        examples=["SecurePass123!"]
    )
    role_ids: Optional[List[UUID]] = Field(
        default=None,
        description="IDs of roles to assign to the user"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        errors = []
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("Password must contain at least one digit")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append("Password must contain at least one special character")
        
        if errors:
            raise ValueError(f"Password validation failed: {'; '.join(errors)}")
        return v


class UserUpdate(BaseSchema):
    """User update request schema (all fields optional)."""
    
    model_config = ConfigDict(extra='forbid')
    
    email: Optional[EmailStr] = Field(default=None, max_length=255)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None


class UserInDB(UserBase, TimestampedSchema):
    """User schema as stored in database (internal use)."""
    
    id: UUID
    is_verified: bool
    is_superuser: bool
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login: Optional[datetime]
    email_verified_at: Optional[datetime]
    deleted_at: Optional[datetime]


class UserResponse(UserBase, TimestampedSchema):
    """User response schema for API responses."""
    
    id: UUID
    is_verified: bool
    last_login: Optional[datetime] = None
    full_name: str = Field(
        ...,
        description="Computed full name",
        examples=["John Doe"]
    )
    role_names: List[str] = Field(
        default_factory=list,
        description="Names of assigned roles"
    )
    
    @field_validator('full_name', mode='before')
    @classmethod
    def compute_full_name(cls, v, info):
        """Compute full name from first and last name."""
        if v:
            return v
        data = info.data
        first = data.get('first_name', '')
        last = data.get('last_name', '')
        return f"{first} {last}".strip()


class UserProfile(UserResponse):
    """Extended user profile with additional details."""
    
    roles: List['RoleSummary'] = Field(default_factory=list)
    permissions: List[str] = Field(
        default_factory=list,
        description="Flattened list of all permissions"
    )
    session_count: int = Field(
        default=0,
        description="Number of active sessions"
    )
    mfa_enabled: bool = Field(
        default=False,
        description="Whether MFA is enabled"
    )


class RoleSummary(BaseSchema):
    """Simplified role information for embedding."""
    
    id: UUID
    name: str
    description: Optional[str]


class UserFilters(BaseSchema):
    """User list filter parameters."""
    
    search: Optional[str] = Field(
        default=None,
        description="Search in email, username, first_name, last_name"
    )
    role: Optional[str] = Field(
        default=None,
        description="Filter by role name"
    )
    status: Optional[UserStatus] = Field(
        default=None,
        description="Filter by account status"
    )
    is_verified: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")


class UserListResponse(PaginatedResponse[UserResponse]):
    """Paginated list of users."""
    pass


class UserStats(BaseSchema):
    """User statistics."""
    
    total_users: int
    active_users: int
    pending_verification: int
    locked_accounts: int
    recent_registrations: int  # Last 30 days


# Resolve forward references
UserProfile.model_rebuild()