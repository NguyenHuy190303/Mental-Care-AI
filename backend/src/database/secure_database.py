"""
Secure Database Configuration with Enhanced Security Controls
Addresses database security vulnerabilities and implements audit logging.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import hashlib
import json

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.event import listen
from sqlalchemy.engine import Engine
from sqlalchemy import text, event

from ..security.encryption import health_data_encryption
from ..monitoring.logging_config import get_logger

logger = get_logger("database.secure")


class DatabaseAuditLogger:
    """Database audit logging for compliance."""
    
    def __init__(self):
        """Initialize audit logger."""
        self.audit_log = get_logger("database.audit")
    
    def log_query(self, query: str, params: Dict[str, Any], user_id: Optional[str] = None):
        """Log database query for audit trail."""
        # Hash query to avoid logging sensitive data
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        
        audit_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'query_hash': query_hash,
            'query_type': self._get_query_type(query),
            'user_id': user_id,
            'param_count': len(params) if params else 0,
            'sensitive_tables': self._detect_sensitive_tables(query)
        }
        
        self.audit_log.info("Database query executed", **audit_data)
    
    def log_connection(self, connection_info: Dict[str, Any]):
        """Log database connection for monitoring."""
        self.audit_log.info("Database connection", **connection_info)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related database events."""
        security_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        self.audit_log.warning("Database security event", **security_data)
    
    def _get_query_type(self, query: str) -> str:
        """Determine query type from SQL."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('select'):
            return 'SELECT'
        elif query_lower.startswith('insert'):
            return 'INSERT'
        elif query_lower.startswith('update'):
            return 'UPDATE'
        elif query_lower.startswith('delete'):
            return 'DELETE'
        elif query_lower.startswith('create'):
            return 'CREATE'
        elif query_lower.startswith('drop'):
            return 'DROP'
        elif query_lower.startswith('alter'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def _detect_sensitive_tables(self, query: str) -> List[str]:
        """Detect if query involves sensitive tables."""
        sensitive_tables = [
            'user_interactions', 'users', 'feedback_entries',
            'safety_incidents', 'user_profiles', 'crisis_logs'
        ]
        
        query_lower = query.lower()
        detected = [table for table in sensitive_tables if table in query_lower]
        
        return detected


class SecureDatabaseManager:
    """Secure database manager with enhanced security controls."""
    
    def __init__(self):
        """Initialize secure database manager."""
        self.audit_logger = DatabaseAuditLogger()
        self.engine = None
        self.session_factory = None
        self.connection_pool_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'last_connection_time': None
        }
    
    async def initialize(self, database_url: str, **kwargs):
        """Initialize database with security configurations."""
        try:
            # Enhanced connection parameters for security
            connect_args = {
                'server_settings': {
                    'application_name': 'mental_health_agent',
                    'log_statement': 'all',  # Log all statements
                    'log_min_duration_statement': '1000',  # Log slow queries
                },
                'command_timeout': 30,
                'connect_timeout': 10,
            }
            
            # Create engine with secure connection pooling
            self.engine = create_async_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
                connect_args=connect_args,
                echo=False,  # Don't echo SQL in production
                **kwargs
            )
            
            # Set up event listeners for audit logging
            self._setup_event_listeners()
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Secure database manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Set up database event listeners for security monitoring."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections."""
            self.connection_pool_stats['total_connections'] += 1
            self.connection_pool_stats['last_connection_time'] = datetime.utcnow()
            
            self.audit_logger.log_connection({
                'event': 'connection_established',
                'total_connections': self.connection_pool_stats['total_connections']
            })
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool."""
            self.connection_pool_stats['active_connections'] += 1
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool."""
            self.connection_pool_stats['active_connections'] -= 1
        
        @event.listens_for(self.engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Handle connection invalidation."""
            self.connection_pool_stats['failed_connections'] += 1
            
            self.audit_logger.log_security_event('connection_invalidated', {
                'exception': str(exception) if exception else None,
                'failed_connections': self.connection_pool_stats['failed_connections']
            })
    
    @asynccontextmanager
    async def get_session(self, user_id: Optional[str] = None):
        """Get database session with audit logging."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self.session_factory()
        
        try:
            # Set session-level security parameters
            if user_id:
                await session.execute(
                    text("SET application_name = :app_name"),
                    {'app_name': f'mental_health_agent_user_{user_id}'}
                )
            
            yield session
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            
            self.audit_logger.log_security_event('transaction_rollback', {
                'user_id': user_id,
                'error': str(e)
            })
            
            raise
        finally:
            await session.close()
    
    async def execute_secure_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Execute query with security logging and validation."""
        try:
            # Validate query for security
            self._validate_query_security(query)
            
            # Log query for audit
            self.audit_logger.log_query(query, params or {}, user_id)
            
            async with self.get_session(user_id) as session:
                result = await session.execute(text(query), params or {})
                return result
                
        except Exception as e:
            self.audit_logger.log_security_event('query_execution_failed', {
                'user_id': user_id,
                'error': str(e),
                'query_type': self.audit_logger._get_query_type(query)
            })
            raise
    
    def _validate_query_security(self, query: str):
        """Validate query for security issues."""
        query_lower = query.lower().strip()
        
        # Check for dangerous operations
        dangerous_patterns = [
            'drop table', 'drop database', 'truncate table',
            'delete from users where', 'update users set',
            'grant ', 'revoke ', 'create user', 'alter user'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                raise ValueError(f"Potentially dangerous query pattern detected: {pattern}")
        
        # Check for SQL injection patterns
        injection_patterns = [
            "'; drop", "'; delete", "'; update",
            "union select", "or 1=1", "or '1'='1'"
        ]
        
        for pattern in injection_patterns:
            if pattern in query_lower:
                raise ValueError(f"Potential SQL injection detected: {pattern}")
    
    async def backup_sensitive_data(self, backup_path: str, encryption_key: str):
        """Create encrypted backup of sensitive data."""
        try:
            # This would implement secure backup with encryption
            # For now, just log the backup attempt
            
            self.audit_logger.log_security_event('backup_initiated', {
                'backup_path': backup_path,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # In production, implement:
            # 1. Export sensitive tables
            # 2. Encrypt backup with provided key
            # 3. Verify backup integrity
            # 4. Store backup securely
            
            logger.info(f"Secure backup initiated to {backup_path}")
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    async def rotate_database_credentials(self):
        """Rotate database credentials for security."""
        try:
            # This would implement credential rotation
            # For now, just log the rotation attempt
            
            self.audit_logger.log_security_event('credential_rotation_initiated', {
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # In production, implement:
            # 1. Generate new credentials
            # 2. Update database user
            # 3. Update application configuration
            # 4. Test new connection
            # 5. Revoke old credentials
            
            logger.info("Database credential rotation initiated")
            
        except Exception as e:
            logger.error(f"Credential rotation failed: {e}")
            raise
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            **self.connection_pool_stats,
            'pool_size': self.engine.pool.size() if self.engine else 0,
            'checked_out': self.engine.pool.checkedout() if self.engine else 0,
            'overflow': self.engine.pool.overflow() if self.engine else 0,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = time.time()
            
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'connection_stats': self.get_connection_stats()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_stats': self.get_connection_stats()
            }


# Global secure database manager
secure_db_manager = SecureDatabaseManager()


# Enhanced session dependency with security
async def get_secure_db_session(user_id: Optional[str] = None):
    """Get secure database session with audit logging."""
    async with secure_db_manager.get_session(user_id) as session:
        yield session
