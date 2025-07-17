"""
API endpoints package for the Mental Health Agent backend.
"""

from .auth import router as auth_router
from .agent import router as agent_router, startup_agent
from .websocket import websocket_endpoint, get_connection_manager
from .monitoring import router as monitoring_router
from .feedback import router as feedback_router
from .validation import router as validation_router
from .middleware import (
    RateLimitMiddleware,
    InputValidationMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware
)

__all__ = [
    "auth_router",
    "agent_router",
    "startup_agent",
    "websocket_endpoint",
    "get_connection_manager",
    "monitoring_router",
    "feedback_router",
    "validation_router",
    "RateLimitMiddleware",
    "InputValidationMiddleware",
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware"
]