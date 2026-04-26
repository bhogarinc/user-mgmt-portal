"""
Audit logging Pydantic schemas.

Defines request/response models for audit log operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse, TimestampedSchema


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    EMAIL_VERIFIED = "email_verified"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    USER_LOCKED = "user_locked"
    USER_UNLOCKED = "user_unlocked"
    
    # RBAC
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # Security
    ACCESS_DENIED = "access_denied"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SESSION_TERMINATED = "session_terminated"
    
    # System
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BACKUP_CREATED = "backup_created"
    EXPORT_GENERATED = "export_generated"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogBase(BaseSchema):
    """Base audit log schema."""
    
    event_type: AuditEventType = Field(..., description="Type of event")
    severity: AuditSeverity = Field(
        default=AuditSeverity.INFO,
        description="Event severity"
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description"
    )


class AuditLogCreate(AuditLogBase):
    """Create audit log entry."""
    
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    response_status: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AuditLogResponse(AuditLogBase):
    """Audit log response."""
    
    id: UUID
    timestamp: datetime
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    response_status: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AuditLogFilter(BaseSchema):
    """Audit log filter parameters."""
    
    event_type: Optional[AuditEventType] = None
    severity: Optional[AuditSeverity] = None
    user_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter events after this date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter events before this date"
    )
    ip_address: Optional[str] = None
    search: Optional[str] = Field(
        default=None,
        description="Search in description, error_message"
    )
    sort_by: str = Field(default="timestamp")
    sort_order: str = Field(default="desc")


class AuditLogListResponse(PaginatedResponse[AuditLogResponse]):
    """Paginated list of audit logs."""
    pass


class AuditStats(BaseSchema):
    """Audit log statistics."""
    
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_today: int
    events_this_week: int
    events_this_month: int
    top_users: List[Dict[str, Any]]


class AuditExportRequest(BaseSchema):
    """Export audit logs request."""
    
    filter: AuditLogFilter
    format: str = Field(
        default="csv",
        pattern=r'^(csv|json|xlsx)$',
        description="Export format"
    )


class AuditExportResponse(BaseSchema):
    """Audit export response."""
    
    download_url: str
    expires_at: datetime
    record_count: int


class AuditRetentionPolicy(BaseSchema):
    """Audit log retention policy."""
    
    retention_days: int = Field(
        ...,
        ge=30,
        le=3650,
        description="Days to retain audit logs"
    )
    archive_before_delete: bool = Field(
        default=True,
        description="Archive before deletion"
    )
    archive_location: Optional[str] = None


class AuditConfig(BaseSchema):
    """Audit configuration."""
    
    enabled_events: List[AuditEventType]
    excluded_paths: List[str]  # Paths to exclude from audit
    mask_fields: List[str]  # Fields to mask in logs
    retention_policy: AuditRetentionPolicy