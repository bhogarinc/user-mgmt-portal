"""
User service for business logic.

Encapsulates user-related operations and database interactions.
"""
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        role: Optional[str] = None
    ) -> tuple[List[User], int]:
        """Get multiple users with filtering and pagination.
        
        Returns:
            Tuple of (users list, total count)
        """
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply filters
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)
        
        if role:
            # Join with roles table for filtering
            query = query.join(User.roles).where(Role.name == role)
            count_query = count_query.join(User.roles).where(Role.name == role)
        
        if search:
            search_filter = (
                User.email.ilike(f"%{search}%") |
                User.full_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create(self, obj_in: UserCreate) -> User:
        """Create new user."""
        # Check for existing email
        existing = await self.get_by_email(obj_in.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Create user
        db_obj = User(
            email=obj_in.email.lower(),
            password_hash=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        
        # Assign role
        role_result = await self.db.execute(
            select(Role).where(Role.name == obj_in.role)
        )
        role = role_result.scalar_one_or_none()
        if role:
            db_obj.roles.append(role)
        
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def update(self, db_obj: User, obj_in: UserUpdate) -> User:
        """Update user."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
        if "email" in update_data:
            update_data["email"] = update_data["email"].lower()
            # Check for email conflict
            existing = await self.get_by_email(update_data["email"])
            if existing and existing.id != db_obj.id:
                raise ValueError("Email already in use")
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db_obj: User) -> None:
        """Soft delete user (deactivate)."""
        db_obj.is_active = False
        self.db.add(db_obj)
        await self.db.flush()
    
    async def hard_delete(self, db_obj: User) -> None:
        """Hard delete user from database."""
        await self.db.delete(db_obj)
        await self.db.flush()
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    async def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active
