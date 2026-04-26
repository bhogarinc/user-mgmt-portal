"""
User models for User Management Portal.

This module defines the database models for users, roles,
and related entities.

GitHub Issue: HLD-003
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, Integer,
    ForeignKey, Table, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.db.base_class import Base


# Association table for user_roles many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_by', UUID(as_uuid=True), ForeignKey('users.id'), nullable=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now()),
    Column('expires_at', DateTime(timezone=True), nullable=True)
)


class User(Base):
    """
    User model representing application users.
    
    Attributes:
        id: Unique identifier (UUID)
        email: Unique email address
        password_hash: Argon2id hashed password
        first_name: User's first name
        last_name: User's last name
        status: Account status (active, inactive, suspended, pending)
        email_verified: Whether email has been verified
        mfa_enabled: Whether MFA is enabled
        failed_login_attempts: Count of consecutive failed logins
        locked_until: Account lockout expiration
        roles: Associated roles
    """
    
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Account status
    status = Column(
        String(20),
        nullable=False,
        default='pending',
        index=True
    )
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret_encrypted = Column(Text, nullable=True)
    mfa_backup_codes = Column(ARRAY(String), nullable=True)
    
    # Security tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(INET, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    roles = relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='selectin'
    )
    profile = relationship('UserProfile', back_populates='user', uselist=False)
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')
    login_history = relationship('LoginHistory', back_populates='user', cascade='all, delete-orphan')
    
    @validates('email')
    def validate_email(self, key, email):
        """Normalize email address."""
        return email.lower().strip() if email else email
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status value."""
        allowed = ['active', 'inactive', 'suspended', 'pending']
        if status not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return status
    
    @property
    def full_name(self) -> str:
        """Return user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == 'active' and self.deleted_at is None
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def permissions(self) -> List[str]:
        """Get all permissions from assigned roles."""
        perms = set()
        for role in self.roles:
            perms.update(role.permissions_list)
        return list(perms)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"


class Role(Base):
    """
    Role model for RBAC.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Unique role name
        description: Role description
        permissions: JSON array of permission strings
        is_system: Whether role is system-defined (cannot be deleted)
        parent_role_id: Parent role for hierarchy
    """
    
    __tablename__ = 'roles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSONB, default=list, nullable=False)
    
    # Role hierarchy
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=True)
    
    # System role flag
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship(
        'User',
        secondary=user_roles,
        back_populates='roles'
    )
    parent_role = relationship('Role', remote_side=[id], backref='child_roles')
    
    @property
    def permissions_list(self) -> List[str]:
        """Get permissions as list."""
        return self.permissions or []
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UserProfile(Base):
    """
    Extended user profile information.
    
    Separated from User for optional/profile data that may not be
    frequently accessed.
    """
    
    __tablename__ = 'user_profiles'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # Profile data
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code
    
    # Preferences
    timezone = Column(String(50), default='UTC', nullable=False)
    locale = Column(String(10), default='en-US', nullable=False)
    notification_preferences = Column(JSONB, default=dict, nullable=False)
    
    # Custom fields
    custom_fields = Column(JSONB, default=dict, nullable=False)
    
    # Audit
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='profile')
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id})>"


class UserSession(Base):
    """
    Active user sessions for token management.
    """
    
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token information
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    refresh_token_hash = Column(String(64), nullable=True, unique=True, index=True)
    
    # Session metadata
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Device information
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class LoginHistory(Base):
    """
    User login history for audit and security monitoring.
    
    This table is partitioned by month for performance.
    """
    
    __tablename__ = 'login_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Login attempt details
    success = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String(100), nullable=True)
    
    # Request metadata
    ip_address = Column(INET, nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    
    # Geographic info (if available)
    country = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Timestamps
    login_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    logout_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='login_history')
    
    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, success={self.success})>"


# Indexes for performance
Index('ix_users_status_active', User.status, postgresql_where=User.deleted_at.is_(None))
Index('ix_users_created_at', User.created_at.desc())
Index('ix_user_sessions_expires_cleanup', UserSession.expires_at)
