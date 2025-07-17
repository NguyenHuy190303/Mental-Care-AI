"""
Monitoring package for the Mental Health Agent backend.
"""

from .error_handler import (
    ErrorHandler,
    MentalHealthError,
    SafetyError,
    PrivacyError,
    AIModelError,
    DatabaseError,
    ErrorSeverity,
    ErrorCategory,
    error_handler,
    error_context,
    handle_graceful_degradation
)
from .health_monitor import (
    HealthMonitor,
    HealthStatus,
    ComponentHealth,
    SystemMetrics,
    health_monitor
)

__all__ = [
    "ErrorHandler",
    "MentalHealthError",
    "SafetyError", 
    "PrivacyError",
    "AIModelError",
    "DatabaseError",
    "ErrorSeverity",
    "ErrorCategory",
    "error_handler",
    "error_context",
    "handle_graceful_degradation",
    "HealthMonitor",
    "HealthStatus",
    "ComponentHealth",
    "SystemMetrics",
    "health_monitor"
]
