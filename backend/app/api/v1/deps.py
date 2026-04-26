"""
API dependencies for User Management Portal.

This module provides FastAPI dependencies for authentication,
authorization, and common request handling.

GitHub Issue: HLD-001, HLD-004
"""

from typing import Generator, Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import JWTManager, PermissionChecker
from app.core.errors import ErrorCode, UMPException
from app.models.user import User


# Security scheme for JWT tokens
security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        Authenticated User model
        
    Raises:
        UMPException: If authentication fails
    """
    if credentials is None:
        raise UMPException(ErrorCode.AUTH_TOKEN_INVALID)
    
    token = credentials.credentials
    
    try:
        payload = JWTManager.decode_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise UMPException(ErrorCode.AUTH_TOKEN_INVALID)
        
        # Get user from database
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        
        if user is None:
            raise UMPException(ErrorCode.USER_NOT_FOUND)
        
        if not user.is_active:
            raise UMPException(ErrorCode.AUTH_ACCOUNT_LOCKED)
        
        # Store user info in request state for logging
        request.state.user_id = str(user.id)
        request.state.user_role = user.roles[0].name if user.roles else None
        
        return user
        
    except UMPException:
        raise
    except Exception:
        raise UMPException(ErrorCode.AUTH_TOKEN_INVALID)


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify account is active."""
    if not current_user.is_active:
        raise UMPException(ErrorCode.AUTH_ACCOUNT_LOCKED)
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory for permission checking.
    
    Example:
        @app.get("/admin/users")
        async def list_users(
            user: User = Depends(require_permissions(["user:read"]))
        ):
            return {"users": []}
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_permissions = current_user.permissions
        
        if not PermissionChecker.require_permissions(user_permissions, required_permissions):
            raise UMPException(ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS)
        
        return current_user
    
    return permission_checker


def require_role(required_role: str):
    """Dependency factory for role checking."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        user_roles = [role.name for role in current_user.roles]
        
        if required_role not in user_roles:
            raise UMPException(ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS)
        
        return current_user
    
    return role_checker


# Common permission combinations
require_admin = require_permissions(["user:read", "user:write"])
require_user_read = require_permissions(["user:read"])
require_user_write = require_permissions(["user:write"])
require_role_read = require_permissions(["role:read"])
require_audit_read = require_permissions(["audit:read"])


async def get_pagination_params(
    skip: int = 0,
    limit: int = 100
) -> dict:
    """Get pagination parameters with validation."""
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 1
    if limit > 1000:
        limit = 1000
    
    return {"skip": skip, "limit": limit}
