"""
Database connection management for PostgreSQL.
"""

import os
import logging
from typing import Optional, AsyncGenerator
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager, contextmanager

from ..models.database import Base

logger = logging.getLogger(__name__)


def get_database_url(async_mode: bool = False) -> str:
    """
    Get database URL from environment variables.
    
    Args:
        async_mode: Whether to return async database URL
        
    Returns:
        Database URL string
    """
    # Default to SQLite for development if PostgreSQL not configured
    postgres_url = os.getenv("DATABASE_URL")
    
    if postgres_url:
        if async_mode and not postgres_url.startswith("postgresql+asyncpg://"):
            # Convert to async URL
            postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://")
        return postgres_url
    
    # Fallback to SQLite for development
    sqlite_url = os.getenv("SQLITE_URL", "sqlite:///./data/mental_health.db")
    if async_mode:
        sqlite_url = sqlite_url.replace("sqlite://", "sqlite+aiosqlite://")
    
    return sqlite_url


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self, database_url: Optional[str] = None, async_mode: bool = True):
        """
        Initialize database manager.
        
        Args:
            database_url: Database URL (if None, will be read from environment)
            async_mode: Whether to use async database operations
        """
        self.database_url = database_url or get_database_url(async_mode)
        self.async_mode = async_mode
        self._engine: Optional[Engine | AsyncEngine] = None
        self._session_factory = None
        
    def create_engine(self) -> Engine | AsyncEngine:
        """Create database engine."""
        if self._engine is not None:
            return self._engine
            
        if self.async_mode:
            self._engine = create_async_engine(
                self.database_url,
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )
        else:
            # For SQLite in development
            connect_args = {}
            if "sqlite" in self.database_url:
                connect_args = {"check_same_thread": False}
                
            self._engine = create_engine(
                self.database_url,
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
                connect_args=connect_args,
                poolclass=StaticPool if "sqlite" in self.database_url else None,
            )
            
        return self._engine
    
    def create_session_factory(self):
        """Create session factory."""
        if self._session_factory is not None:
            return self._session_factory
            
        engine = self.create_engine()
        
        if self.async_mode:
            self._session_factory = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            self._session_factory = sessionmaker(
                bind=engine, autocommit=False, autoflush=False
            )
            
        return self._session_factory
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session context manager.
        
        Yields:
            AsyncSession: Database session
        """
        if not self.async_mode:
            raise ValueError("DatabaseManager not configured for async mode")
            
        session_factory = self.create_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @contextmanager
    def get_sync_session(self) -> Session:
        """
        Get synchronous database session context manager.
        
        Yields:
            Session: Database session
        """
        if self.async_mode:
            raise ValueError("DatabaseManager configured for async mode")
            
        session_factory = self.create_session_factory()
        session = session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def create_tables(self):
        """Create all database tables."""
        if self.async_mode:
            engine = self.create_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        else:
            engine = self.create_engine()
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
    
    async def drop_tables(self):
        """Drop all database tables."""
        if self.async_mode:
            engine = self.create_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        else:
            engine = self.create_engine()
            Base.metadata.drop_all(bind=engine)
            logger.info("Database tables dropped successfully")
    
    async def close(self):
        """Close database connections."""
        if self._engine:
            if self.async_mode:
                await self._engine.dispose()
            else:
                self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with db_manager.get_async_session() as session:
        yield session


async def check_database_health() -> bool:
    """
    Check database connectivity and health.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with db_manager.get_async_session() as session:
            # Simple query to check connectivity
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
