"""
Enhanced Error Handler for Mental Health Agent
Provides comprehensive error handling, logging, and monitoring capabilities.
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import asyncio
from contextlib import asynccontextmanager

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None

from ..models.core import ErrorResponse
from ..database import get_db_session

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    AI_MODEL = "ai_model"
    SAFETY = "safety"
    PRIVACY = "privacy"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context information for error tracking."""
    
    def __init__(
        self,
        error_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        self.error_id = error_id
        self.user_id = user_id
        self.session_id = session_id
        self.request_id = request_id
        self.endpoint = endpoint
        self.method = method
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.additional_context = additional_context or {}
        self.timestamp = datetime.utcnow()


class MentalHealthError(Exception):
    """Base exception for Mental Health Agent specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None,
        suggested_action: Optional[str] = None,
        emergency_resources: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.context = context
        self.user_message = user_message or "An error occurred. Please try again."
        self.suggested_action = suggested_action
        self.emergency_resources = emergency_resources or []


class SafetyError(MentalHealthError):
    """Error related to safety violations or crisis situations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="SAFETY_VIOLATION",
            category=ErrorCategory.SAFETY,
            severity=ErrorSeverity.CRITICAL,
            emergency_resources=[
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741",
                "Emergency Services: 911"
            ],
            **kwargs
        )


class PrivacyError(MentalHealthError):
    """Error related to privacy or data protection violations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="PRIVACY_VIOLATION",
            category=ErrorCategory.PRIVACY,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class AIModelError(MentalHealthError):
    """Error related to AI model operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="AI_MODEL_ERROR",
            category=ErrorCategory.AI_MODEL,
            severity=ErrorSeverity.MEDIUM,
            user_message="I'm experiencing technical difficulties. Please try again or contact a mental health professional if you need immediate assistance.",
            **kwargs
        )


class DatabaseError(MentalHealthError):
    """Error related to database operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message="We're experiencing technical difficulties. Please try again in a moment.",
            **kwargs
        )


class ErrorHandler:
    """Enhanced error handler with monitoring and alerting capabilities."""
    
    def __init__(
        self,
        enable_sentry: bool = False,
        sentry_dsn: Optional[str] = None,
        enable_alerting: bool = True,
        alert_webhook_url: Optional[str] = None
    ):
        """
        Initialize error handler.
        
        Args:
            enable_sentry: Whether to enable Sentry error tracking
            sentry_dsn: Sentry DSN for error reporting
            enable_alerting: Whether to enable alerting for critical errors
            alert_webhook_url: Webhook URL for sending alerts
        """
        self.enable_sentry = enable_sentry
        self.enable_alerting = enable_alerting
        self.alert_webhook_url = alert_webhook_url
        self.error_counts = {}
        self.last_alert_times = {}
        
        # Initialize Sentry if enabled and available
        if enable_sentry and sentry_dsn and SENTRY_AVAILABLE:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=False),
                    SqlalchemyIntegration()
                ],
                traces_sample_rate=0.1,
                environment="production"
            )
            logger.info("Sentry error tracking initialized")
        
        logger.info("Error handler initialized")
    
    async def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """
        Handle an error with comprehensive logging and monitoring.
        
        Args:
            error: The exception that occurred
            context: Error context information
            request: FastAPI request object
            
        Returns:
            ErrorResponse object
        """
        # Generate error ID if not provided
        error_id = context.error_id if context else str(uuid.uuid4())
        
        # Extract context from request if available
        if request and not context:
            context = await self._extract_context_from_request(request, error_id)
        
        # Classify error
        if isinstance(error, MentalHealthError):
            mental_health_error = error
        else:
            mental_health_error = self._classify_generic_error(error, context)
        
        # Log error
        await self._log_error(mental_health_error, context)
        
        # Send to Sentry if enabled
        if self.enable_sentry:
            self._send_to_sentry(mental_health_error, context)
        
        # Check if alerting is needed
        if self.enable_alerting and mental_health_error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            await self._send_alert(mental_health_error, context)
        
        # Track error metrics
        self._track_error_metrics(mental_health_error)
        
        # Store error in database for analysis
        await self._store_error_in_database(mental_health_error, context)
        
        # Create error response
        return ErrorResponse(
            message=mental_health_error.user_message,
            error_code=mental_health_error.error_code,
            error_id=error_id,
            suggested_action=mental_health_error.suggested_action,
            emergency_resources=mental_health_error.emergency_resources
        )
    
    async def _extract_context_from_request(self, request: Request, error_id: str) -> ErrorContext:
        """Extract error context from FastAPI request."""
        return ErrorContext(
            error_id=error_id,
            user_id=getattr(request.state, 'user_id', None),
            session_id=getattr(request.state, 'session_id', None),
            request_id=getattr(request.state, 'request_id', None),
            endpoint=str(request.url.path),
            method=request.method,
            user_agent=request.headers.get('user-agent'),
            ip_address=request.client.host if request.client else None
        )
    
    def _classify_generic_error(self, error: Exception, context: Optional[ErrorContext]) -> MentalHealthError:
        """Classify a generic exception into a MentalHealthError."""
        error_message = str(error)
        
        # Database errors
        if any(keyword in error_message.lower() for keyword in ['database', 'connection', 'sql', 'postgres']):
            return DatabaseError(error_message, context=context)
        
        # AI model errors
        if any(keyword in error_message.lower() for keyword in ['openai', 'model', 'api', 'token']):
            return AIModelError(error_message, context=context)
        
        # HTTP errors
        if isinstance(error, HTTPException):
            if error.status_code == 401:
                category = ErrorCategory.AUTHENTICATION
            elif error.status_code == 403:
                category = ErrorCategory.AUTHORIZATION
            elif error.status_code == 422:
                category = ErrorCategory.VALIDATION
            else:
                category = ErrorCategory.SYSTEM
            
            return MentalHealthError(
                message=error_message,
                error_code=f"HTTP_{error.status_code}",
                category=category,
                severity=ErrorSeverity.MEDIUM,
                context=context
            )
        
        # Default classification
        return MentalHealthError(
            message=error_message,
            error_code="UNKNOWN_ERROR",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
    
    async def _log_error(self, error: MentalHealthError, context: Optional[ErrorContext]):
        """Log error with appropriate level and context."""
        log_data = {
            "error_id": context.error_id if context else "unknown",
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "message": error.message,
            "user_id": context.user_id if context else None,
            "session_id": context.session_id if context else None,
            "endpoint": context.endpoint if context else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Filter sensitive data
        filtered_log_data = self._filter_sensitive_data(log_data)
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {json.dumps(filtered_log_data)}")
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {json.dumps(filtered_log_data)}")
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {json.dumps(filtered_log_data)}")
        else:
            logger.info(f"Low severity error: {json.dumps(filtered_log_data)}")
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from logs."""
        sensitive_fields = ['password', 'token', 'key', 'secret', 'api_key']
        filtered_data = data.copy()
        
        for field in sensitive_fields:
            if field in filtered_data:
                filtered_data[field] = "[REDACTED]"
        
        return filtered_data
    
    def _send_to_sentry(self, error: MentalHealthError, context: Optional[ErrorContext]):
        """Send error to Sentry for tracking."""
        if not SENTRY_AVAILABLE:
            return

        try:
            with sentry_sdk.push_scope() as scope:
                if context:
                    scope.set_tag("error_category", error.category.value)
                    scope.set_tag("error_severity", error.severity.value)
                    scope.set_tag("error_code", error.error_code)
                    scope.set_user({
                        "id": context.user_id,
                        "session_id": context.session_id
                    })
                    scope.set_context("error_context", {
                        "endpoint": context.endpoint,
                        "method": context.method,
                        "user_agent": context.user_agent,
                        "ip_address": context.ip_address
                    })
                
                sentry_sdk.capture_exception(error)
        except Exception as e:
            logger.error(f"Failed to send error to Sentry: {e}")
    
    async def _send_alert(self, error: MentalHealthError, context: Optional[ErrorContext]):
        """Send alert for critical errors."""
        try:
            # Implement rate limiting for alerts
            alert_key = f"{error.category.value}_{error.error_code}"
            now = datetime.utcnow()
            
            if alert_key in self.last_alert_times:
                time_since_last = (now - self.last_alert_times[alert_key]).total_seconds()
                if time_since_last < 300:  # 5 minutes rate limit
                    return
            
            self.last_alert_times[alert_key] = now
            
            # Prepare alert data
            alert_data = {
                "error_id": context.error_id if context else "unknown",
                "severity": error.severity.value,
                "category": error.category.value,
                "error_code": error.error_code,
                "message": error.message,
                "timestamp": now.isoformat(),
                "user_id": context.user_id if context else None,
                "endpoint": context.endpoint if context else None
            }
            
            # Send webhook alert if configured
            if self.alert_webhook_url:
                await self._send_webhook_alert(alert_data)
            
            # Log alert
            logger.critical(f"ALERT SENT: {json.dumps(alert_data)}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send alert via webhook."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.alert_webhook_url,
                    json=alert_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Webhook alert failed with status {response.status}")
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def _track_error_metrics(self, error: MentalHealthError):
        """Track error metrics for monitoring."""
        metric_key = f"{error.category.value}_{error.severity.value}"
        
        if metric_key not in self.error_counts:
            self.error_counts[metric_key] = 0
        
        self.error_counts[metric_key] += 1
        
        # Log metrics periodically
        if sum(self.error_counts.values()) % 100 == 0:
            logger.info(f"Error metrics: {json.dumps(self.error_counts)}")
    
    async def _store_error_in_database(self, error: MentalHealthError, context: Optional[ErrorContext]):
        """Store error in database for analysis."""
        try:
            # This would store error details in database for analysis
            # Implementation depends on your database schema
            pass
        except Exception as e:
            logger.error(f"Failed to store error in database: {e}")
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get current error metrics."""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "last_alert_times": {k: v.isoformat() for k, v in self.last_alert_times.items()}
        }


# Global error handler instance
error_handler = ErrorHandler()


@asynccontextmanager
async def error_context(
    operation: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Context manager for error handling."""
    error_id = str(uuid.uuid4())
    context = ErrorContext(
        error_id=error_id,
        user_id=user_id,
        session_id=session_id,
        additional_context=additional_context or {}
    )
    
    try:
        yield context
    except Exception as e:
        error_response = await error_handler.handle_error(e, context)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


def handle_graceful_degradation(fallback_response: Any):
    """Decorator for graceful degradation on errors."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Graceful degradation triggered for {func.__name__}: {e}")
                return fallback_response
        return wrapper
    return decorator
