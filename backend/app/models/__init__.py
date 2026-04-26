"""SQLAlchemy ORM models for User Management Portal.

This module exports all model classes for use throughout the application.
Updated per LLD specifications.
"""

from app.models.base import BaseModel, Base
from app.models.user import User
from app.models.profile import UserProfile
from app.models.role import Role, Permission, user_roles, role_permissions
from app.models.session import UserSession
from app.models.audit_log import AuditLog

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # User
    "User",
    "UserProfile",
    # RBAC
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    # Auth
    "UserSession",
    # Audit
    "AuditLog",
]