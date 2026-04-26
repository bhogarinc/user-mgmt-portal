"""
Authentication-related Pydantic schemas.

Defines request/response models for authentication operations including
login, registration, token management, and password reset.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    """User login request."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User password",
        examples=["SecurePass123!"]
    )
    remember_me: bool = Field(
        default=False,
        description="Whether to extend session duration"
    )


class TokenPayload(BaseSchema):
    """JWT token payload structure."""
    
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    type: str = Field(..., description="Token type (access/refresh)")
    iat: datetime = Field(..., description="Issued at timestamp")
    exp: datetime = Field(..., description="Expiration timestamp")
    jti: Optional[str] = Field(default=None, description="JWT ID")


class TokenPair(BaseSchema):
    """Access and refresh token pair."""
    
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIs..."]
    )
    refresh_token: str = Field(
        ...,
        description="Opaque refresh token",
        examples=["dGhpcyBpcyBhIHJlZnJlc2g..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[900]
    )


class LoginResponse(BaseSchema):
    """Successful login response."""
    
    tokens: TokenPair
    user: UserResponse


class RegisterRequest(BaseSchema):
    """User registration request."""
    
    email: EmailStr = Field(
        ...,
        max_length=255,
        description="Email address",
        examples=["newuser@example.com"]
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Unique username",
        examples=["newuser"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8+ chars, uppercase, lowercase, digit, special)",
        examples=["SecurePass123!"]
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
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("one digit")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append("one special character")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v


class RefreshTokenRequest(BaseSchema):
    """Token refresh request."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
        examples=["dGhpcyBpcyBhIHJlZnJlc2g..."]
    )


class PasswordChangeRequest(BaseSchema):
    """Password change request (authenticated user)."""
    
    current_password: str = Field(
        ...,
        description="Current password"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )
    confirm_password: str = Field(
        ...,
        description="Confirm new password"
    )
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure new password and confirmation match."""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password complexity."""
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("one digit")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append("one special character")
        
        if errors:
            raise ValueError(f"New password must contain: {', '.join(errors)}")
        return v


class PasswordResetRequest(BaseSchema):
    """Password reset request (forgot password)."""
    
    email: EmailStr = Field(
        ...,
        description="Registered email address"
    )


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation."""
    
    token: str = Field(
        ...,
        description="Password reset token from email"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password"
    )
    confirm_password: str = Field(
        ...,
        description="Confirm new password"
    )
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match."""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class VerifyEmailRequest(BaseSchema):
    """Email verification request."""
    
    token: str = Field(
        ...,
        description="Email verification token"
    )


class ResendVerificationRequest(BaseSchema):
    """Resend verification email request."""
    
    email: EmailStr = Field(
        ...,
        description="Email address to verify"
    )


class AuthStatusResponse(BaseSchema):
    """Authentication status response."""
    
    is_authenticated: bool
    user: Optional[UserResponse] = None
    permissions: List[str] = Field(default_factory=list)


class SessionInfo(BaseSchema):
    """Active session information."""
    
    id: UUID
    ip_address: str
    user_agent: Optional[str]
    location: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    is_current: bool = Field(
        default=False,
        description="Whether this is the current session"
    )


class LogoutRequest(BaseSchema):
    """Logout request with optional session control."""
    
    logout_all: bool = Field(
        default=False,
        description="Logout from all devices"
    )