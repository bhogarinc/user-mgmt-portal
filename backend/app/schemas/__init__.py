"""
Pydantic schemas for request/response validation.

This module exports all schema classes for use throughout the application.
"""

from app.schemas.base import (
    BaseSchema,
    BaseResponse,
    PaginationParams,
    PaginatedResponse,
    SortOrder,
)

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    UserListResponse,
    UserStatus,
    UserFilters,
)

from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenPayload,
    TokenPair,
    RefreshTokenRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)

from app.schemas.rbac import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissions,
    PermissionBase,
    PermissionResponse,
    UserRoleAssign,
    RolePermissionAssign,
)

from app.schemas.audit import (
    AuditLogBase,
    AuditLogResponse,
    AuditLogFilter,
    AuditEventType,
    AuditSeverity,
)

__all__ = [
    # Base
    "BaseSchema",
    "BaseResponse",
    "PaginationParams",
    "PaginatedResponse",
    "SortOrder",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "UserListResponse",
    "UserStatus",
    "UserFilters",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "TokenPayload",
    "TokenPair",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # RBAC
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "PermissionBase",
    "PermissionResponse",
    "UserRoleAssign",
    "RolePermissionAssign",
    # Audit
    "AuditLogBase",
    "AuditLogResponse",
    "AuditLogFilter",
    "AuditEventType",
    "AuditSeverity",
]