"""
Caching layer for RAG system using Redis.
"""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CacheManager:
    """Base cache manager interface."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError


class MemoryCache(CacheManager):
    """In-memory cache implementation for development/testing."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries to store
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, datetime] = {}
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, data in self.cache.items():
            if data.get("expires_at") and now > data["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full."""
        if len(self.cache) >= self.max_size:
            # Sort by access time and remove oldest
            sorted_keys = sorted(
                self.access_times.items(),
                key=lambda x: x[1]
            )
            keys_to_remove = [k for k, _ in sorted_keys[:len(sorted_keys) // 4]]
            
            for key in keys_to_remove:
                if key in self.cache:
                    del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        self._cleanup_expired()
        
        if key in self.cache:
            data = self.cache[key]
            if data.get("expires_at") and datetime.utcnow() > data["expires_at"]:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return None
            
            self.access_times[key] = datetime.utcnow()
            return data["value"]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in memory cache."""
        self._cleanup_expired()
        self._evict_lru()
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
        
        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        }
        self.access_times[key] = datetime.utcnow()
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
        return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        """Clear all memory cache entries."""
        self.cache.clear()
        self.access_times.clear()
        return True


class RedisCache(CacheManager):
    """Redis cache implementation for production."""
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        prefix: str = "mental_health:",
        encoding: str = "utf-8"
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
            encoding: String encoding
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required for RedisCache")
        
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.prefix = prefix
        self.encoding = encoding
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding=self.encoding,
                decode_responses=True
            )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            client = await self._get_client()
            value = await client.get(self._make_key(key))
            
            if value is not None:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in Redis cache."""
        try:
            client = await self._get_client()
            serialized_value = json.dumps(value, default=str)
            
            if ttl > 0:
                await client.setex(self._make_key(key), ttl, serialized_value)
            else:
                await client.set(self._make_key(key), serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            client = await self._get_client()
            result = await client.delete(self._make_key(key))
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            client = await self._get_client()
            result = await client.exists(self._make_key(key))
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries with prefix."""
        try:
            client = await self._get_client()
            keys = await client.keys(f"{self.prefix}*")
            
            if keys:
                await client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


class CachedRAGSearchTool:
    """RAG Search Tool with caching capabilities."""
    
    def __init__(
        self,
        rag_tool,
        cache_manager: CacheManager,
        cache_ttl: int = 3600,
        enable_caching: bool = True
    ):
        """
        Initialize cached RAG search tool.
        
        Args:
            rag_tool: Base RAG search tool
            cache_manager: Cache manager instance
            cache_ttl: Cache time-to-live in seconds
            enable_caching: Whether to enable caching
        """
        self.rag_tool = rag_tool
        self.cache_manager = cache_manager
        self.cache_ttl = cache_ttl
        self.enable_caching = enable_caching
    
    def _make_cache_key(self, query: str, **kwargs) -> str:
        """Create cache key from query and parameters."""
        # Create a hash of the query and parameters for consistent keys
        key_data = {
            "query": query,
            **kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"rag_search:{key_hash}"
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        include_low_confidence: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search with caching.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            include_low_confidence: Include low confidence results
            filters: Search filters
            
        Returns:
            Search results
        """
        if not self.enable_caching:
            return await self.rag_tool.search(
                query=query,
                max_results=max_results,
                include_low_confidence=include_low_confidence,
                filters=filters
            )
        
        # Create cache key
        cache_key = self._make_cache_key(
            query=query,
            max_results=max_results,
            include_low_confidence=include_low_confidence,
            filters=filters or {}
        )
        
        # Try to get from cache
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for query: {query}")
            return cached_result
        
        # Cache miss - perform search
        logger.debug(f"Cache miss for query: {query}")
        result = await self.rag_tool.search(
            query=query,
            max_results=max_results,
            include_low_confidence=include_low_confidence,
            filters=filters
        )
        
        # Store in cache
        await self.cache_manager.set(cache_key, result, self.cache_ttl)
        
        return result
    
    async def get_authoritative_sources(
        self,
        topic: str,
        max_sources: int = 5
    ) -> List[Any]:
        """Get authoritative sources with caching."""
        if not self.enable_caching:
            return await self.rag_tool.get_authoritative_sources(topic, max_sources)
        
        cache_key = self._make_cache_key(
            query=f"authoritative:{topic}",
            max_sources=max_sources
        )
        
        cached_result = await self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        result = await self.rag_tool.get_authoritative_sources(topic, max_sources)
        await self.cache_manager.set(cache_key, result, self.cache_ttl)
        
        return result


def create_cache_manager(use_redis: bool = None) -> CacheManager:
    """
    Create appropriate cache manager based on environment.
    
    Args:
        use_redis: Force Redis usage (None for auto-detect)
        
    Returns:
        Cache manager instance
    """
    if use_redis is None:
        # Auto-detect based on environment
        use_redis = (
            REDIS_AVAILABLE and 
            os.getenv("REDIS_URL") is not None and
            os.getenv("ENVIRONMENT", "development") == "production"
        )
    
    if use_redis and REDIS_AVAILABLE:
        logger.info("Using Redis cache")
        return RedisCache()
    else:
        logger.info("Using memory cache")
        return MemoryCache()


# Global cache manager instance
cache_manager = create_cache_manager()
