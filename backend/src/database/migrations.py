"""
Database migration utilities.
"""

import logging
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.engine import Engine

from .connection import DatabaseManager
from ..models.database import Base

logger = logging.getLogger(__name__)


async def create_tables(db_manager: Optional[DatabaseManager] = None):
    """
    Create all database tables.
    
    Args:
        db_manager: Database manager instance (uses global if None)
    """
    if db_manager is None:
        from .connection import db_manager as global_db_manager
        db_manager = global_db_manager
    
    await db_manager.create_tables()
    logger.info("All database tables created successfully")


async def drop_tables(db_manager: Optional[DatabaseManager] = None):
    """
    Drop all database tables.
    
    Args:
        db_manager: Database manager instance (uses global if None)
    """
    if db_manager is None:
        from .connection import db_manager as global_db_manager
        db_manager = global_db_manager
    
    await db_manager.drop_tables()
    logger.info("All database tables dropped successfully")


async def migrate_database(db_manager: Optional[DatabaseManager] = None):
    """
    Run database migrations.
    
    Args:
        db_manager: Database manager instance (uses global if None)
    """
    if db_manager is None:
        from .connection import db_manager as global_db_manager
        db_manager = global_db_manager
    
    logger.info("Starting database migration...")
    
    # Create tables if they don't exist
    await create_tables(db_manager)
    
    # Run any additional migration scripts here
    await _run_migration_scripts(db_manager)
    
    logger.info("Database migration completed successfully")


async def _run_migration_scripts(db_manager: DatabaseManager):
    """
    Run additional migration scripts.
    
    Args:
        db_manager: Database manager instance
    """
    engine = db_manager.create_engine()
    
    if db_manager.async_mode:
        await _run_async_migrations(engine)
    else:
        _run_sync_migrations(engine)


async def _run_async_migrations(engine: AsyncEngine):
    """Run async migration scripts."""
    async with engine.begin() as conn:
        # Create indexes for better performance
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_session 
            ON conversations(user_id, session_id);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
            ON conversations(created_at);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_usage_metrics_created_at 
            ON usage_metrics(created_at);
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_data_safety_concern 
            ON feedback_data(safety_concern) WHERE safety_concern = true;
        """))
        
        logger.info("Database indexes created successfully")


def _run_sync_migrations(engine: Engine):
    """Run sync migration scripts."""
    with engine.begin() as conn:
        # Create indexes for better performance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_session 
            ON conversations(user_id, session_id);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
            ON conversations(created_at);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_usage_metrics_created_at 
            ON usage_metrics(created_at);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_feedback_data_safety_concern 
            ON feedback_data(safety_concern) WHERE safety_concern = true;
        """))
        
        logger.info("Database indexes created successfully")


async def check_database_health(db_manager: Optional[DatabaseManager] = None) -> bool:
    """
    Check database connectivity and health.
    
    Args:
        db_manager: Database manager instance (uses global if None)
        
    Returns:
        bool: True if database is healthy, False otherwise
    """
    if db_manager is None:
        from .connection import db_manager as global_db_manager
        db_manager = global_db_manager
    
    try:
        engine = db_manager.create_engine()
        
        if db_manager.async_mode:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
        else:
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
        
        logger.info("Database health check passed")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def reset_database(db_manager: Optional[DatabaseManager] = None):
    """
    Reset database by dropping and recreating all tables.
    
    WARNING: This will delete all data!
    
    Args:
        db_manager: Database manager instance (uses global if None)
    """
    if db_manager is None:
        from .connection import db_manager as global_db_manager
        db_manager = global_db_manager
    
    logger.warning("Resetting database - all data will be lost!")
    
    # Drop all tables
    await drop_tables(db_manager)
    
    # Recreate all tables
    await create_tables(db_manager)
    
    # Run migrations
    await _run_migration_scripts(db_manager)
    
    logger.info("Database reset completed successfully")
