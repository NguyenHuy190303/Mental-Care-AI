"""
Main FastAPI application entry point for the Mental Health Agent.
"""

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

import sys
import os

# Configuration fallback
try:
    # Try to import from the config directory
    sys.path.insert(0, '/app')
    from config.settings import settings
    from config.logging import get_logger
except ImportError:
    # Create a minimal fallback configuration
    import logging

    class FallbackSettings:
        def __init__(self):
            # Application settings
            self.APP_NAME = os.getenv('APP_NAME', 'Sage Mental Health AI')
            self.APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
            self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
            self.DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
            self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

            # Database and other settings
            self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./sage.db')
            self.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-for-development')
            self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
            self.CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

    settings = FallbackSettings()

    def get_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Import API components
from .api.auth import router as auth_router
from .api.agent import router as agent_router, startup_agent
from .api.websocket import websocket_endpoint, get_connection_manager
from .api.monitoring import router as monitoring_router
from .api.feedback import router as feedback_router
from .api.validation import router as validation_router
from .api.patient_progress import router as patient_progress_router
from .api.enterprise import router as enterprise_router
from .api.enterprise import enterprise_router
from .api.middleware import (
    RateLimitMiddleware,
    InputValidationMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware
)
from .database import create_tables, check_database_health
from .monitoring import error_handler, health_monitor
from .monitoring.logging_config import setup_logging

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered comprehensive healthcare support system with scientific citations and evidence-based medical information",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add custom middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware, log_body=settings.DEBUG)
app.add_middleware(InputValidationMiddleware, max_content_length=10 * 1024 * 1024)
app.add_middleware(
    RateLimitMiddleware,
    calls=100,
    period=60,
    per_user=True,
    exclude_paths=["/api/health", "/docs", "/redoc", "/openapi.json"]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.render.com"]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing and trace ID."""
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add trace ID to request state
    request.state.trace_id = trace_id
    
    client_ip = request.client.host if request.client else None
    logger.info(
        f"Request started - {request.method} {str(request.url)} "
        f"(trace_id: {trace_id}, client_ip: {client_ip})"
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"Request completed - {request.method} {str(request.url)} "
            f"(status: {response.status_code}, time: {process_time:.3f}s, trace_id: {trace_id})"
        )
        
        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed - {request.method} {str(request.url)} "
            f"(error: {str(e)}, time: {process_time:.3f}s, trace_id: {trace_id})"
        )
        raise

# Include API routers
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(monitoring_router)
app.include_router(feedback_router)
app.include_router(validation_router)
app.include_router(patient_progress_router)
app.include_router(enterprise_router)

# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_chat(websocket: WebSocket, token: str, session_id: str = None):
    """WebSocket endpoint for real-time chat."""
    await websocket_endpoint(websocket, token, session_id)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    # Check database health
    db_healthy = await check_database_health()

    # Get connection stats
    connection_manager = get_connection_manager()
    active_connections = connection_manager.get_active_connections_count()

    status = "healthy" if db_healthy else "unhealthy"

    return {
        "status": status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "database": "healthy" if db_healthy else "unhealthy",
        "active_websocket_connections": active_connections,
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
    }

# Global exception handler with enhanced error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    trace_id = getattr(request.state, "trace_id", "unknown")

    try:
        # Use enhanced error handler
        error_response = await error_handler.handle_error(exc, request=request)

        return JSONResponse(
            status_code=500,
            content={
                "error": error_response.message,
                "error_code": error_response.error_code,
                "error_id": error_response.error_id,
                "trace_id": trace_id,
                "suggested_action": error_response.suggested_action,
                "emergency_resources": error_response.emergency_resources
            },
        )
    except Exception as handler_error:
        # Fallback if error handler fails
        logger.error(
            f"Error handler failed - error: {str(handler_error)}, "
            f"original_error: {str(exc)}, trace_id: {trace_id}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "trace_id": trace_id,
                "message": "An unexpected error occurred. Please try again later.",
            },
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    # Setup enhanced logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file="./logs/mental-health-agent.log",
        enable_console=True,
        enable_json=True,
        enable_sensitive_filter=True
    )

    logger.info(
        f"Application starting up - {settings.APP_NAME} v{settings.APP_VERSION} "
        f"(env: {settings.ENVIRONMENT}, debug: {settings.DEBUG})"
    )

    # Initialize database tables
    try:
        await create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Don't fail startup, but log the error

    # Initialize Mental Health Agent
    try:
        await startup_agent()
        logger.info("Mental Health Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Mental Health Agent: {e}")
        # Don't fail startup, but log the error

    # Start health monitoring
    try:
        import asyncio
        asyncio.create_task(health_monitor.start_monitoring())
        logger.info("Health monitoring started")
    except Exception as e:
        logger.error(f"Failed to start health monitoring: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Application shutting down")

    # Stop health monitoring
    try:
        health_monitor.stop_monitoring()
        logger.info("Health monitoring stopped")
    except Exception as e:
        logger.error(f"Failed to stop health monitoring: {e}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )