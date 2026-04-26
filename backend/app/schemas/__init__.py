"""Pydantic schemas for request/response validation.

This module exports all schema classes for use throughout the application.
Updated per LLD specifications.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserFilter,
)
from app.schemas.auth import (
    TokenPayload,
    TokenResponse,
    TokenRefresh,
    UserLogin,
    UserRegister,
    PasswordChange,
    PasswordResetRequest,
    PasswordReset,
    AuthUserResponse,
    LoginResponse,
)
from app.schemas.profile import (
    UserProfileBase,
    UserProfileUpdate,
    UserProfileResponse,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionBase,
    PermissionResponse,
    RolePermissionAssignment,
)
from app.schemas.common import (
    ApiResponse,
    ApiError,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "UserFilter",
    # Auth schemas
    "TokenPayload",
    "TokenResponse",
    "TokenRefresh",
    "UserLogin",
    "UserRegister",
    "PasswordChange",
    "PasswordResetRequest",
    "PasswordReset",
    "AuthUserResponse",
    "LoginResponse",
    # Profile schemas
    "UserProfileBase",
    "UserProfileUpdate",
    "UserProfileResponse",
    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "PermissionBase",
    "PermissionResponse",
    "RolePermissionAssignment",
    # Common schemas
    "ApiResponse",
    "ApiError",
    "PaginatedResponse",
    "PaginationParams",
]