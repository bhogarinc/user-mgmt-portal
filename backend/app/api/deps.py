"""
FastAPI dependencies for authentication and common functionality.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_access_token, TokenData
from app.db.session import get_db
from app.models.user import User
from app.services.user_service import UserService

# Security scheme for Swagger UI
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user instance
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.sub)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is temporarily locked"
        )
    
    # Store user info in request state for logging
    request.state.user_id = user.id
    request.state.user_email = user.email
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with verified status check.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User: Active and verified user
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


def require_roles(*allowed_roles: str):
    """Create dependency for role-based access control.
    
    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            user: User = Depends(require_roles("admin"))
        ):
            ...
    
    Args:
        *allowed_roles: Variable list of allowed role names
        
    Returns:
        Callable: Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.primary_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# Common role-based dependencies
require_admin = require_roles("admin")
require_manager = require_roles("admin", "manager")
require_user = require_roles("admin", "manager", "user")


async def get_pagination_params(
    page: int = 1,
    page_size: int = 20
) -> dict:
    """Get pagination parameters with validation.
    
    Args:
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        dict: Pagination parameters
    """
    return {
        "page": max(1, page),
        "page_size": min(max(1, page_size), 100),  # Cap at 100
        "offset": (max(1, page) - 1) * min(max(1, page_size), 100)
    }


class CommonDependencies:
    """Container for common dependencies."""
    
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        user: Optional[User] = Depends(get_current_user)
    ):
        self.db = db
        self.user = user
        self.user_service = UserService(db)
