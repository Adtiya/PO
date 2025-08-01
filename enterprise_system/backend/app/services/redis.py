"""
Redis service for the Enterprise AI System.
Provides caching, session management, and rate limiting functionality.
"""

import json
import pickle
from typing import Any, Optional, Dict, List, Union
import structlog
import redis.asyncio as redis
from redis.asyncio import Redis
from datetime import datetime, timedelta

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RedisService:
    """Service for Redis operations including caching and session management."""
    
    def __init__(self):
        self._client: Optional[Redis] = None
        self._connection_pool = None
    
    async def get_client(self) -> Redis:
        """Get Redis client with connection pooling."""
        if self._client is None:
            try:
                # Create connection pool
                self._connection_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                
                # Create Redis client
                self._client = Redis(
                    connection_pool=self._connection_pool,
                    decode_responses=True
                )
                
                # Test connection
                await self._client.ping()
                logger.info("Redis connection established")
                
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                raise
        
        return self._client
    
    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
    
    # ============================================================================
    # BASIC OPERATIONS
    # ============================================================================
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set key-value pair with optional expiration."""
        try:
            client = await self.get_client()
            return await client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        try:
            client = await self.get_client()
            return await client.delete(*keys)
        except Exception as e:
            logger.error("Redis DELETE failed", keys=keys, error=str(e))
            return 0
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        try:
            client = await self.get_client()
            return await client.exists(*keys)
        except Exception as e:
            logger.error("Redis EXISTS failed", keys=keys, error=str(e))
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key."""
        try:
            client = await self.get_client()
            return await client.expire(key, seconds)
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        try:
            client = await self.get_client()
            return await client.ttl(key)
        except Exception as e:
            logger.error("Redis TTL failed", key=key, error=str(e))
            return -1
    
    # ============================================================================
    # JSON OPERATIONS
    # ============================================================================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key."""
        try:
            value = await self.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON", key=key, error=str(e))
            return None
        except Exception as e:
            logger.error("Redis GET JSON failed", key=key, error=str(e))
            return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None
    ) -> bool:
        """Set JSON value with optional expiration."""
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, ex=ex, px=px)
        except (TypeError, ValueError) as e:
            logger.error("Failed to encode JSON", key=key, error=str(e))
            return False
        except Exception as e:
            logger.error("Redis SET JSON failed", key=key, error=str(e))
            return False
    
    # ============================================================================
    # HASH OPERATIONS
    # ============================================================================
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        try:
            client = await self.get_client()
            return await client.hget(name, key)
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            return None
    
    async def hset(self, name: str, mapping: Dict[str, str]) -> int:
        """Set hash fields."""
        try:
            client = await self.get_client()
            return await client.hset(name, mapping=mapping)
        except Exception as e:
            logger.error("Redis HSET failed", name=name, error=str(e))
            return 0
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        try:
            client = await self.get_client()
            return await client.hgetall(name)
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        try:
            client = await self.get_client()
            return await client.hdel(name, *keys)
        except Exception as e:
            logger.error("Redis HDEL failed", name=name, keys=keys, error=str(e))
            return 0
    
    # ============================================================================
    # LIST OPERATIONS
    # ============================================================================
    
    async def lpush(self, name: str, *values: str) -> int:
        """Push values to left of list."""
        try:
            client = await self.get_client()
            return await client.lpush(name, *values)
        except Exception as e:
            logger.error("Redis LPUSH failed", name=name, error=str(e))
            return 0
    
    async def rpush(self, name: str, *values: str) -> int:
        """Push values to right of list."""
        try:
            client = await self.get_client()
            return await client.rpush(name, *values)
        except Exception as e:
            logger.error("Redis RPUSH failed", name=name, error=str(e))
            return 0
    
    async def lpop(self, name: str) -> Optional[str]:
        """Pop value from left of list."""
        try:
            client = await self.get_client()
            return await client.lpop(name)
        except Exception as e:
            logger.error("Redis LPOP failed", name=name, error=str(e))
            return None
    
    async def rpop(self, name: str) -> Optional[str]:
        """Pop value from right of list."""
        try:
            client = await self.get_client()
            return await client.rpop(name)
        except Exception as e:
            logger.error("Redis RPOP failed", name=name, error=str(e))
            return None
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get list range."""
        try:
            client = await self.get_client()
            return await client.lrange(name, start, end)
        except Exception as e:
            logger.error("Redis LRANGE failed", name=name, error=str(e))
            return []
    
    # ============================================================================
    # SET OPERATIONS
    # ============================================================================
    
    async def sadd(self, name: str, *values: str) -> int:
        """Add values to set."""
        try:
            client = await self.get_client()
            return await client.sadd(name, *values)
        except Exception as e:
            logger.error("Redis SADD failed", name=name, error=str(e))
            return 0
    
    async def srem(self, name: str, *values: str) -> int:
        """Remove values from set."""
        try:
            client = await self.get_client()
            return await client.srem(name, *values)
        except Exception as e:
            logger.error("Redis SREM failed", name=name, error=str(e))
            return 0
    
    async def smembers(self, name: str) -> set:
        """Get all set members."""
        try:
            client = await self.get_client()
            return await client.smembers(name)
        except Exception as e:
            logger.error("Redis SMEMBERS failed", name=name, error=str(e))
            return set()
    
    async def sismember(self, name: str, value: str) -> bool:
        """Check if value is in set."""
        try:
            client = await self.get_client()
            return await client.sismember(name, value)
        except Exception as e:
            logger.error("Redis SISMEMBER failed", name=name, error=str(e))
            return False
    
    # ============================================================================
    # SORTED SET OPERATIONS
    # ============================================================================
    
    async def zadd(self, name: str, mapping: Dict[str, float]) -> int:
        """Add members to sorted set."""
        try:
            client = await self.get_client()
            return await client.zadd(name, mapping)
        except Exception as e:
            logger.error("Redis ZADD failed", name=name, error=str(e))
            return 0
    
    async def zrem(self, name: str, *values: str) -> int:
        """Remove members from sorted set."""
        try:
            client = await self.get_client()
            return await client.zrem(name, *values)
        except Exception as e:
            logger.error("Redis ZREM failed", name=name, error=str(e))
            return 0
    
    async def zrange(
        self,
        name: str,
        start: int,
        end: int,
        withscores: bool = False
    ) -> List:
        """Get sorted set range."""
        try:
            client = await self.get_client()
            return await client.zrange(name, start, end, withscores=withscores)
        except Exception as e:
            logger.error("Redis ZRANGE failed", name=name, error=str(e))
            return []
    
    async def zcard(self, name: str) -> int:
        """Get sorted set cardinality."""
        try:
            client = await self.get_client()
            return await client.zcard(name)
        except Exception as e:
            logger.error("Redis ZCARD failed", name=name, error=str(e))
            return 0
    
    async def zremrangebyscore(self, name: str, min_score: float, max_score: float) -> int:
        """Remove sorted set members by score range."""
        try:
            client = await self.get_client()
            return await client.zremrangebyscore(name, min_score, max_score)
        except Exception as e:
            logger.error("Redis ZREMRANGEBYSCORE failed", name=name, error=str(e))
            return 0
    
    # ============================================================================
    # PIPELINE OPERATIONS
    # ============================================================================
    
    async def pipeline(self):
        """Create Redis pipeline for batch operations."""
        try:
            client = await self.get_client()
            return client.pipeline()
        except Exception as e:
            logger.error("Redis PIPELINE failed", error=str(e))
            return None
    
    # ============================================================================
    # UTILITY OPERATIONS
    # ============================================================================
    
    async def incr(self, name: str, amount: int = 1) -> int:
        """Increment key value."""
        try:
            client = await self.get_client()
            return await client.incr(name, amount)
        except Exception as e:
            logger.error("Redis INCR failed", name=name, error=str(e))
            return 0
    
    async def decr(self, name: str, amount: int = 1) -> int:
        """Decrement key value."""
        try:
            client = await self.get_client()
            return await client.decr(name, amount)
        except Exception as e:
            logger.error("Redis DECR failed", name=name, error=str(e))
            return 0
    
    async def info(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Get Redis server information."""
        try:
            client = await self.get_client()
            return await client.info(section)
        except Exception as e:
            logger.error("Redis INFO failed", error=str(e))
            return {}
    
    async def ping(self) -> bool:
        """Ping Redis server."""
        try:
            client = await self.get_client()
            response = await client.ping()
            return response == "PONG"
        except Exception as e:
            logger.error("Redis PING failed", error=str(e))
            return False
    
    # ============================================================================
    # CACHING UTILITIES
    # ============================================================================
    
    async def cache_get(self, key: str, default: Any = None) -> Any:
        """Get cached value with automatic JSON deserialization."""
        try:
            value = await self.get_json(key)
            return value if value is not None else default
        except Exception as e:
            logger.error("Cache GET failed", key=key, error=str(e))
            return default
    
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set cached value with automatic JSON serialization."""
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            return await self.set_json(key, value, ex=ttl)
        except Exception as e:
            logger.error("Cache SET failed", key=key, error=str(e))
            return False
    
    async def cache_delete(self, *keys: str) -> int:
        """Delete cached values."""
        return await self.delete(*keys)
    
    async def cache_clear_pattern(self, pattern: str) -> int:
        """Clear cache keys matching pattern."""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Cache clear pattern failed", pattern=pattern, error=str(e))
            return 0
    
    # ============================================================================
    # SESSION MANAGEMENT
    # ============================================================================
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Create user session."""
        try:
            ttl = ttl or settings.REDIS_SESSION_TTL
            session_data = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                **data
            }
            
            session_key = f"session:{session_id}"
            return await self.set_json(session_key, session_data, ex=ttl)
            
        except Exception as e:
            logger.error("Session creation failed", session_id=session_id, error=str(e))
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        try:
            session_key = f"session:{session_id}"
            return await self.get_json(session_key)
        except Exception as e:
            logger.error("Session get failed", session_id=session_id, error=str(e))
            return None
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: bool = True
    ) -> bool:
        """Update session data."""
        try:
            session_key = f"session:{session_id}"
            current_data = await self.get_json(session_key)
            
            if current_data is None:
                return False
            
            # Update data
            current_data.update(data)
            current_data["last_activity"] = datetime.utcnow().isoformat()
            
            # Set with or without extending TTL
            if extend_ttl:
                return await self.set_json(session_key, current_data, ex=settings.REDIS_SESSION_TTL)
            else:
                return await self.set_json(session_key, current_data)
                
        except Exception as e:
            logger.error("Session update failed", session_id=session_id, error=str(e))
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        try:
            session_key = f"session:{session_id}"
            result = await self.delete(session_key)
            return result > 0
        except Exception as e:
            logger.error("Session delete failed", session_id=session_id, error=str(e))
            return False


# Export commonly used items
__all__ = [
    "RedisService"
]

