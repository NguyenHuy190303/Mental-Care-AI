"""
Middleware for rate limiting, input validation, and security.
"""

import time
import logging
import hashlib
from typing import Dict, Optional, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""
    
    def __init__(
        self,
        app,
        calls: int = 100,
        period: int = 60,
        per_user: bool = True,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed per period
            period: Time period in seconds
            per_user: Whether to apply rate limiting per user or globally
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.per_user = per_user
        self.exclude_paths = exclude_paths or ["/api/health", "/docs", "/redoc"]
        
        # Storage for rate limiting data
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.
        
        Args:
            request: HTTP request
            
        Returns:
            Client identifier string
        """
        if self.per_user:
            # Try to get user ID from token
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                # Create hash of token for privacy
                return hashlib.sha256(token.encode()).hexdigest()[:16]
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return client_ip
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """
        Check if client is rate limited.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        window_start = now - self.period
        
        # Get client's request history
        client_requests = self.requests[client_id]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= self.calls:
            return True
        
        # Add current request
        client_requests.append(now)
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.calls} per {self.period} seconds",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        client_requests = self.requests[client_id]
        remaining = max(0, self.calls - len(client_requests))
        
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.period))
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Input validation and sanitization middleware."""
    
    def __init__(
        self,
        app,
        max_content_length: int = 10 * 1024 * 1024,  # 10MB
        blocked_patterns: Optional[list] = None
    ):
        """
        Initialize input validation middleware.
        
        Args:
            app: FastAPI application
            max_content_length: Maximum request content length in bytes
            blocked_patterns: List of blocked patterns/keywords
        """
        super().__init__(app)
        self.max_content_length = max_content_length
        self.blocked_patterns = blocked_patterns or [
            "<script>", "javascript:", "data:text/html",
            "eval(", "exec(", "import os", "import sys"
        ]
    
    def _validate_content_length(self, request: Request) -> bool:
        """
        Validate request content length.
        
        Args:
            request: HTTP request
            
        Returns:
            True if valid, False otherwise
        """
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                return length <= self.max_content_length
            except ValueError:
                return False
        return True
    
    def _contains_blocked_patterns(self, content: str) -> bool:
        """
        Check if content contains blocked patterns.
        
        Args:
            content: Content to check
            
        Returns:
            True if blocked patterns found, False otherwise
        """
        content_lower = content.lower()
        return any(pattern.lower() in content_lower for pattern in self.blocked_patterns)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with input validation.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Validate content length
        if not self._validate_content_length(request):
            logger.warning(f"Request content too large: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request too large",
                    "message": f"Request content exceeds maximum size of {self.max_content_length} bytes"
                }
            )
        
        # For POST/PUT requests, validate body content
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8', errors='ignore')
                    
                    # Check for blocked patterns
                    if self._contains_blocked_patterns(body_str):
                        logger.warning(f"Blocked pattern detected in request: {request.url.path}")
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "error": "Invalid input",
                                "message": "Request contains potentially harmful content"
                            }
                        )
                
                # Recreate request with body for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except UnicodeDecodeError:
                logger.warning(f"Invalid encoding in request: {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid encoding",
                        "message": "Request body contains invalid characters"
                    }
                )
            except Exception as e:
                logger.error(f"Error validating request body: {e}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Validation error",
                        "message": "Failed to validate request content"
                    }
                )
        
        # Process request
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware."""
    
    def __init__(self, app):
        """
        Initialize security headers middleware.
        
        Args:
            app: FastAPI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware with sensitive data filtering."""
    
    def __init__(self, app, log_body: bool = False):
        """
        Initialize request logging middleware.
        
        Args:
            app: FastAPI application
            log_body: Whether to log request/response bodies
        """
        super().__init__(app)
        self.log_body = log_body
        self.sensitive_headers = {
            "authorization", "cookie", "x-api-key", "x-auth-token"
        }
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Sanitize sensitive headers for logging.
        
        Args:
            headers: Request headers
            
        Returns:
            Sanitized headers
        """
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        start_time = time.time()
        
        # Log request
        sanitized_headers = self._sanitize_headers(dict(request.headers))
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "headers": sanitized_headers,
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        return response
