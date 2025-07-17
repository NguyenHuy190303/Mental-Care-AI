"""
Enterprise API Gateway for Mental Health Agent
Advanced rate limiting, request routing, authentication, and monitoring.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
from urllib.parse import urlparse

from fastapi import Request, Response, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session
from ..models.database import APIKey, Organization, RateLimitRule
from ..monitoring.logging_config import get_logger

logger = get_logger("enterprise.api_gateway")


class RateLimitType(str, Enum):
    """Rate limit types."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    CONCURRENT_REQUESTS = "concurrent_requests"


class AuthenticationType(str, Enum):
    """Authentication types."""
    API_KEY = "api_key"
    JWT_BEARER = "jwt_bearer"
    OAUTH2 = "oauth2"
    WEBHOOK_SIGNATURE = "webhook_signature"
    IP_WHITELIST = "ip_whitelist"


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    
    limit_type: RateLimitType
    limit: int
    window_seconds: int
    burst_limit: Optional[int] = None
    organization_id: Optional[str] = None
    api_key_id: Optional[str] = None


@dataclass
class APIGatewayConfig:
    """API Gateway configuration."""
    
    rate_limits: List[RateLimitConfig]
    authentication_types: List[AuthenticationType]
    allowed_origins: List[str]
    webhook_secret: Optional[str] = None
    ip_whitelist: List[str] = None
    request_timeout: int = 30
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes


class EnterpriseAPIGateway:
    """Enterprise API Gateway with advanced features."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize API Gateway."""
        self.redis = redis_client
        self.rate_limit_cache = {}
        self.api_key_cache = {}
        self.config_cache = {}
        
    async def create_api_key(
        self,
        organization_id: str,
        name: str,
        permissions: List[str],
        rate_limits: Optional[List[RateLimitConfig]] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create new API key for organization.
        
        Args:
            organization_id: Organization identifier
            name: API key name
            permissions: List of permissions
            rate_limits: Custom rate limits
            expires_at: Expiration date
            
        Returns:
            API key information
        """
        try:
            # Generate API key
            import secrets
            api_key = f"mha_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            async with get_db_session() as session:
                api_key_record = APIKey(
                    organization_id=organization_id,
                    name=name,
                    key_hash=key_hash,
                    permissions=permissions,
                    rate_limits=[rl.__dict__ for rl in (rate_limits or [])],
                    expires_at=expires_at,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    last_used=None,
                    usage_count=0
                )
                
                session.add(api_key_record)
                await session.commit()
                await session.refresh(api_key_record)
                
                logger.info(
                    f"API key created",
                    organization_id=organization_id,
                    api_key_id=api_key_record.id,
                    name=name
                )
                
                return {
                    "api_key": api_key,  # Only returned once
                    "api_key_id": api_key_record.id,
                    "name": name,
                    "permissions": permissions,
                    "created_at": api_key_record.created_at.isoformat(),
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
                
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise HTTPException(status_code=500, detail="API key creation failed")
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return key information.
        
        Args:
            api_key: API key to validate
            
        Returns:
            API key information if valid, None otherwise
        """
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Check cache first
            if key_hash in self.api_key_cache:
                cached_info = self.api_key_cache[key_hash]
                if cached_info.get("expires_at"):
                    expires_at = datetime.fromisoformat(cached_info["expires_at"])
                    if expires_at < datetime.utcnow():
                        del self.api_key_cache[key_hash]
                        return None
                return cached_info
            
            async with get_db_session() as session:
                api_key_record = await session.query(APIKey).filter(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True
                ).first()
                
                if not api_key_record:
                    return None
                
                # Check expiration
                if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
                    return None
                
                # Update usage
                api_key_record.last_used = datetime.utcnow()
                api_key_record.usage_count += 1
                await session.commit()
                
                key_info = {
                    "api_key_id": api_key_record.id,
                    "organization_id": api_key_record.organization_id,
                    "name": api_key_record.name,
                    "permissions": api_key_record.permissions,
                    "rate_limits": api_key_record.rate_limits,
                    "expires_at": api_key_record.expires_at.isoformat() if api_key_record.expires_at else None
                }
                
                # Cache for 5 minutes
                self.api_key_cache[key_hash] = key_info
                await self.redis.setex(f"api_key:{key_hash}", 300, json.dumps(key_info))
                
                return key_info
                
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def check_rate_limit(
        self,
        identifier: str,
        rate_limit_config: RateLimitConfig,
        request_tokens: int = 1
    ) -> Dict[str, Any]:
        """
        Check rate limit for identifier.
        
        Args:
            identifier: Rate limit identifier (API key, IP, user ID)
            rate_limit_config: Rate limit configuration
            request_tokens: Number of tokens for this request
            
        Returns:
            Rate limit status
        """
        try:
            cache_key = f"rate_limit:{identifier}:{rate_limit_config.limit_type.value}"
            
            # Get current usage
            current_usage = await self.redis.get(cache_key)
            current_usage = int(current_usage) if current_usage else 0
            
            # Check if limit exceeded
            if current_usage + request_tokens > rate_limit_config.limit:
                # Check burst limit if configured
                if rate_limit_config.burst_limit:
                    burst_key = f"burst:{cache_key}"
                    burst_usage = await self.redis.get(burst_key)
                    burst_usage = int(burst_usage) if burst_usage else 0
                    
                    if burst_usage + request_tokens <= rate_limit_config.burst_limit:
                        # Allow burst
                        await self.redis.incrby(burst_key, request_tokens)
                        await self.redis.expire(burst_key, 60)  # 1 minute burst window
                        
                        return {
                            "allowed": True,
                            "limit": rate_limit_config.limit,
                            "remaining": max(0, rate_limit_config.limit - current_usage - request_tokens),
                            "reset_time": time.time() + rate_limit_config.window_seconds,
                            "burst_used": True
                        }
                
                # Rate limit exceeded
                reset_time = await self.redis.ttl(cache_key)
                reset_time = time.time() + reset_time if reset_time > 0 else time.time() + rate_limit_config.window_seconds
                
                return {
                    "allowed": False,
                    "limit": rate_limit_config.limit,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "retry_after": reset_time - time.time()
                }
            
            # Update usage
            await self.redis.incrby(cache_key, request_tokens)
            await self.redis.expire(cache_key, rate_limit_config.window_seconds)
            
            return {
                "allowed": True,
                "limit": rate_limit_config.limit,
                "remaining": max(0, rate_limit_config.limit - current_usage - request_tokens),
                "reset_time": time.time() + rate_limit_config.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request on error (fail open)
            return {"allowed": True, "limit": 0, "remaining": 0, "reset_time": 0}
    
    async def authenticate_request(
        self,
        request: Request,
        auth_types: List[AuthenticationType]
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate request using configured authentication types.
        
        Args:
            request: HTTP request
            auth_types: Allowed authentication types
            
        Returns:
            Authentication information if successful
        """
        try:
            # Try API key authentication
            if AuthenticationType.API_KEY in auth_types:
                api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
                if api_key:
                    key_info = await self.validate_api_key(api_key)
                    if key_info:
                        return {
                            "auth_type": "api_key",
                            "organization_id": key_info["organization_id"],
                            "api_key_id": key_info["api_key_id"],
                            "permissions": key_info["permissions"]
                        }
            
            # Try JWT Bearer authentication
            if AuthenticationType.JWT_BEARER in auth_types:
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    # Validate JWT token (implement JWT validation)
                    user_info = await self._validate_jwt_token(token)
                    if user_info:
                        return {
                            "auth_type": "jwt_bearer",
                            "user_id": user_info["user_id"],
                            "organization_id": user_info.get("organization_id"),
                            "permissions": user_info.get("permissions", [])
                        }
            
            # Try webhook signature authentication
            if AuthenticationType.WEBHOOK_SIGNATURE in auth_types:
                signature = request.headers.get("X-Webhook-Signature")
                if signature:
                    is_valid = await self._validate_webhook_signature(request, signature)
                    if is_valid:
                        return {
                            "auth_type": "webhook_signature",
                            "verified": True
                        }
            
            # Try IP whitelist authentication
            if AuthenticationType.IP_WHITELIST in auth_types:
                client_ip = self._get_client_ip(request)
                if await self._check_ip_whitelist(client_ip):
                    return {
                        "auth_type": "ip_whitelist",
                        "client_ip": client_ip
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Request authentication failed: {e}")
            return None
    
    async def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token."""
        try:
            from ..auth.jwt_handler import verify_token
            payload = verify_token(token)
            return payload
        except Exception as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
    
    async def _validate_webhook_signature(
        self,
        request: Request,
        signature: str
    ) -> bool:
        """Validate webhook signature."""
        try:
            # Get webhook secret from configuration
            webhook_secret = "your-webhook-secret"  # Should be from config
            
            # Get request body
            body = await request.body()
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, f"sha256={expected_signature}")
            
        except Exception as e:
            logger.error(f"Webhook signature validation failed: {e}")
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _check_ip_whitelist(self, client_ip: str) -> bool:
        """Check if IP is in whitelist."""
        try:
            # Get IP whitelist from configuration
            whitelist = await self.redis.smembers("ip_whitelist")
            return client_ip.encode() in whitelist
        except Exception:
            return False
    
    async def log_request(
        self,
        request: Request,
        response: Response,
        auth_info: Optional[Dict[str, Any]],
        processing_time: float
    ):
        """Log API request for monitoring and analytics."""
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "processing_time": processing_time,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent"),
                "auth_type": auth_info.get("auth_type") if auth_info else None,
                "organization_id": auth_info.get("organization_id") if auth_info else None,
                "api_key_id": auth_info.get("api_key_id") if auth_info else None
            }
            
            # Store in Redis for real-time monitoring
            await self.redis.lpush("api_requests", json.dumps(log_data))
            await self.redis.ltrim("api_requests", 0, 9999)  # Keep last 10k requests
            
            # Log for permanent storage
            logger.info("API request", **log_data)
            
        except Exception as e:
            logger.error(f"Request logging failed: {e}")


class APIGatewayMiddleware(BaseHTTPMiddleware):
    """API Gateway middleware for FastAPI."""
    
    def __init__(self, app, gateway: EnterpriseAPIGateway, config: APIGatewayConfig):
        super().__init__(app)
        self.gateway = gateway
        self.config = config
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through API gateway."""
        start_time = time.time()
        
        try:
            # Check request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.config.max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
            
            # CORS check
            origin = request.headers.get("origin")
            if origin and origin not in self.config.allowed_origins and "*" not in self.config.allowed_origins:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Origin not allowed"}
                )
            
            # Authentication
            auth_info = await self.gateway.authenticate_request(
                request,
                self.config.authentication_types
            )
            
            if not auth_info and request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required"}
                )
            
            # Rate limiting
            if auth_info:
                identifier = auth_info.get("api_key_id") or auth_info.get("user_id") or self.gateway._get_client_ip(request)
                
                for rate_limit in self.config.rate_limits:
                    rate_limit_result = await self.gateway.check_rate_limit(
                        identifier,
                        rate_limit
                    )
                    
                    if not rate_limit_result["allowed"]:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Rate limit exceeded",
                                "limit": rate_limit_result["limit"],
                                "reset_time": rate_limit_result["reset_time"],
                                "retry_after": rate_limit_result.get("retry_after", 60)
                            },
                            headers={
                                "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                                "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                                "X-RateLimit-Reset": str(int(rate_limit_result["reset_time"])),
                                "Retry-After": str(int(rate_limit_result.get("retry_after", 60)))
                            }
                        )
            
            # Add auth info to request state
            request.state.auth_info = auth_info
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Log request
            processing_time = time.time() - start_time
            await self.gateway.log_request(request, response, auth_info, processing_time)
            
            return response
            
        except Exception as e:
            logger.error(f"API Gateway middleware error: {e}")
            processing_time = time.time() - start_time
            
            error_response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
            
            await self.gateway.log_request(request, error_response, None, processing_time)
            
            return error_response


# Global API gateway instance
api_gateway = None

async def get_api_gateway() -> EnterpriseAPIGateway:
    """Get API gateway instance."""
    global api_gateway
    if not api_gateway:
        redis_client = redis.from_url("redis://localhost:6379")
        api_gateway = EnterpriseAPIGateway(redis_client)
    return api_gateway
