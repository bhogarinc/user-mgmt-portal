"""
RBAC (Role-Based Access Control) Pydantic schemas.

Defines request/response models for roles and permissions.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse, TimestampedSchema


class PermissionBase(BaseSchema):
    """Base permission schema."""
    
    name: str = Field(
        ...,
        pattern=r'^[a-z_]+:[a-z_]+$',
        description="Permission name in format 'resource:action'",
        examples=["users:read"]
    )
    resource: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Resource being controlled",
        examples=["users"]
    )
    action: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Action being permitted",
        examples=["read"]
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Permission description"
    )


class PermissionResponse(PermissionBase):
    """Permission response schema."""
    
    id: UUID
    created_at: datetime


class PermissionGroup(BaseSchema):
    """Grouped permissions by resource."""
    
    resource: str
    permissions: List[PermissionResponse]


class RoleBase(BaseSchema):
    """Base role schema."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Unique role name",
        examples=["admin"]
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Role description"
    )


class RoleCreate(RoleBase):
    """Role creation request."""
    
    permission_ids: Optional[List[UUID]] = Field(
        default_factory=list,
        description="IDs of permissions to assign"
    )


class RoleUpdate(BaseSchema):
    """Role update request."""
    
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=500)
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(RoleBase, TimestampedSchema):
    """Role response schema."""
    
    id: UUID
    is_system_role: bool = Field(
        ...,
        description="Whether this is a protected system role"
    )
    permission_count: int = Field(
        default=0,
        description="Number of assigned permissions"
    )
    user_count: int = Field(
        default=0,
        description="Number of users with this role"
    )


class RoleWithPermissions(RoleResponse):
    """Role with full permission details."""
    
    permissions: List[PermissionResponse] = Field(default_factory=list)


class RoleSummary(BaseSchema):
    """Simplified role info for embedding."""
    
    id: UUID
    name: str
    description: Optional[str]


class RoleListResponse(PaginatedResponse[RoleResponse]):
    """Paginated list of roles."""
    pass


class PermissionListResponse(PaginatedResponse[PermissionResponse]):
    """Paginated list of permissions."""
    pass


class UserRoleAssign(BaseSchema):
    """Assign role to user request."""
    
    role_id: UUID = Field(..., description="Role to assign")
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for assignment (for audit)"
    )


class UserRoleRemove(BaseSchema):
    """Remove role from user request."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for removal (for audit)"
    )


class RolePermissionAssign(BaseSchema):
    """Assign permission to role request."""
    
    permission_id: UUID = Field(..., description="Permission to assign")


class RoleComparison(BaseSchema):
    """Compare two roles."""
    
    role_a_id: UUID
    role_b_id: UUID
    common_permissions: List[PermissionResponse]
    only_in_a: List[PermissionResponse]
    only_in_b: List[PermissionResponse]


class PermissionCheckRequest(BaseSchema):
    """Check if user has permission request."""
    
    permission: str = Field(
        ...,
        description="Permission to check (format: resource:action)"
    )


class PermissionCheckResponse(BaseSchema):
    """Permission check response."""
    
    has_permission: bool
    permission: str
    user_id: UUID


class BulkRoleAssignment(BaseSchema):
    """Bulk assign role to multiple users."""
    
    user_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    role_id: UUID
    reason: Optional[str] = None


class BulkRoleAssignmentResponse(BaseSchema):
    """Bulk assignment response."""
    
    success_count: int
    failed_count: int
    failures: List[dict] = Field(default_factory=list)