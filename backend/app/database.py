"""
Database connection and session management.

This module provides SQLAlchemy engine creation, session management,
and dependency injection for database sessions in FastAPI endpoints.
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Create async engine for PostgreSQL
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    poolclass=NullPool if settings.is_testing else None,
)

# Create sync engine for migrations and sync operations
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync session factory for migrations
SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session for async operations
        
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Generator[Session, None, None]:
    """
    Get synchronous database session.
    
    Yields:
        Session: Database session for sync operations
        
    Usage:
        with get_sync_session() as session:
            session.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseSessionManager:
    """
    Context manager for database sessions with automatic cleanup.
    
    Provides a convenient way to handle database sessions
    with proper transaction management.
    """
    
    def __init__(self, session: AsyncSession = None):
        self.session = session or AsyncSessionLocal()
        self._committed = False
    
    async def __aenter__(self) -> AsyncSession:
        """Enter async context and return session."""
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context with proper cleanup."""
        try:
            if exc_type is not None:
                await self.session.rollback()
            elif not self._committed:
                await self.session.commit()
        finally:
            await self.session.close()
    
    async def commit(self):
        """Explicitly commit the transaction."""
        await self.session.commit()
        self._committed = True
    
    async def rollback(self):
        """Rollback the transaction."""
        await self.session.rollback()


# Convenience function for context manager usage
async def db_session() -> DatabaseSessionManager:
    """
    Get database session context manager.
    
    Returns:
        DatabaseSessionManager: Context manager for database session
        
    Example:
        async with db_session() as db:
            user = await db.get(User, user_id)
    """
    return DatabaseSessionManager()
