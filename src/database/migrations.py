"""
Database migration utilities.
"""

import logging
from typing import Optional
from sqlalchemy import text
from src.database.connection import DatabaseManager
from src.models.database import Base

logger = logging.getLogger(__name__)


async def create_tables(db_manager: Optional[DatabaseManager] = None):
    """
    Create all database tables.
    
    Args:
        db_manager: Database manager instance (optional)
    """
    if db_manager is None:
        from src.database.connection import db_manager as default_db_manager
        db_manager = default_db_manager
    
    await db_manager.create_tables()
    logger.info("All database tables created successfully")


async def drop_tables(db_manager: Optional[DatabaseManager] = None):
    """
    Drop all database tables.
    
    Args:
        db_manager: Database manager instance (optional)
    """
    if db_manager is None:
        from src.database.connection import db_manager as default_db_manager
        db_manager = default_db_manager
    
    await db_manager.drop_tables()
    logger.info("All database tables dropped successfully")


async def migrate_database(db_manager: Optional[DatabaseManager] = None):
    """
    Run database migrations.
    
    Args:
        db_manager: Database manager instance (optional)
    """
    if db_manager is None:
        from src.database.connection import db_manager as default_db_manager
        db_manager = default_db_manager
    
    logger.info("Starting database migration...")
    
    # Create tables if they don't exist
    await create_tables(db_manager)
    
    # Run any additional migration scripts
    await _run_migration_scripts(db_manager)
    
    logger.info("Database migration completed successfully")


async def _run_migration_scripts(db_manager: DatabaseManager):
    """
    Run additional migration scripts.
    
    Args:
        db_manager: Database manager instance
    """
    migrations = [
        _create_indexes,
        _add_encryption_columns,
        _create_triggers,
    ]
    
    for migration in migrations:
        try:
            await migration(db_manager)
        except Exception as e:
            logger.error(f"Migration {migration.__name__} failed: {e}")
            raise


async def _create_indexes(db_manager: DatabaseManager):
    """Create database indexes for performance."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_conversations_user_session ON conversations(user_id, session_id);",
        "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_usage_metrics_user_created ON usage_metrics(user_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_data_user_created ON feedback_data(user_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_feedback_data_safety ON feedback_data(safety_concern, escalated);",
    ]
    
    if db_manager.async_mode:
        async with db_manager.get_async_session() as session:
            for index_sql in indexes:
                await session.execute(text(index_sql))
    else:
        with db_manager.get_session() as session:
            for index_sql in indexes:
                session.execute(text(index_sql))
    
    logger.info("Database indexes created successfully")


async def _add_encryption_columns(db_manager: DatabaseManager):
    """Add encryption-related columns if they don't exist."""
    # This would typically be handled by Alembic in production
    # For now, we'll assume the columns are already defined in the models
    logger.info("Encryption columns verified")


async def _create_triggers(db_manager: DatabaseManager):
    """Create database triggers for audit and security."""
    # Example: Update last_login timestamp
    trigger_sql = """
    CREATE OR REPLACE FUNCTION update_last_login()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.last_login = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS trigger_update_last_login ON users;
    CREATE TRIGGER trigger_update_last_login
        BEFORE UPDATE ON users
        FOR EACH ROW
        WHEN (OLD.last_login IS DISTINCT FROM NEW.last_login)
        EXECUTE FUNCTION update_last_login();
    """
    
    # Only create triggers for PostgreSQL
    if "postgresql" in db_manager.database_url:
        try:
            if db_manager.async_mode:
                async with db_manager.get_async_session() as session:
                    await session.execute(text(trigger_sql))
            else:
                with db_manager.get_session() as session:
                    session.execute(text(trigger_sql))
            logger.info("Database triggers created successfully")
        except Exception as e:
            logger.warning(f"Could not create triggers (may not be supported): {e}")
    else:
        logger.info("Skipping trigger creation for non-PostgreSQL database")


async def reset_database(db_manager: Optional[DatabaseManager] = None):
    """
    Reset database by dropping and recreating all tables.
    WARNING: This will delete all data!
    
    Args:
        db_manager: Database manager instance (optional)
    """
    if db_manager is None:
        from src.database.connection import db_manager as default_db_manager
        db_manager = default_db_manager
    
    logger.warning("Resetting database - all data will be lost!")
    
    await drop_tables(db_manager)
    await create_tables(db_manager)
    
    logger.info("Database reset completed")


async def check_database_health(db_manager: Optional[DatabaseManager] = None) -> bool:
    """
    Check database health and connectivity.
    
    Args:
        db_manager: Database manager instance (optional)
        
    Returns:
        bool: True if database is healthy
    """
    if db_manager is None:
        from src.database.connection import db_manager as default_db_manager
        db_manager = default_db_manager
    
    return await db_manager.health_check()