"""
Audit log model for tracking system events.

Provides immutable audit trail for security and compliance.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """Audit log entry for tracking system events.
    
    This table is append-only. Records should never be updated or deleted.
    
    Attributes:
        id: Unique log entry ID
        timestamp: When the event occurred
        user_id: ID of user who performed the action (if authenticated)
        action: Type of action (CREATE, UPDATE, DELETE, LOGIN, etc.)
        resource_type: Type of resource affected (User, Role, etc.)
        resource_id: ID of affected resource
        details: JSON payload with action details
        ip_address: Client IP address
        user_agent: Client user agent string
        success: Whether the action succeeded
        error_message: Error details if action failed
    """
    
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )
    
    # When the event occurred
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # What action was performed
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # What resource was affected
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Action details
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Client information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Result
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action!r}, resource={self.resource_type!r}, user={self.user_id!r})>"
    
    @classmethod
    def create(
        cls,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> "AuditLog":
        """Factory method to create a new audit log entry.
        
        Args:
            action: Type of action performed
            resource_type: Type of resource affected
            resource_id: ID of affected resource
            user_id: ID of user who performed action
            details: Additional action details
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether action succeeded
            error_message: Error message if failed
            
        Returns:
            AuditLog: New audit log instance (not yet committed)
        """
        return cls(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
