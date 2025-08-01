"""
Enterprise AI System - Secure Redis Cache Service
Fixed security vulnerability: Replaced pickle with JSON serialization
"""

import json
import redis
import os
import logging
from typing import Any, Optional, Union
from datetime import timedelta

logger = logging.getLogger(__name__)

class SecureRedisCache:
    """Secure Redis cache service with JSON serialization"""
    
    def __init__(self):
        # 🔐 SECURITY: Load Redis config from environment
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        try:
            if redis_url and redis_url != 'redis://localhost:6379/0':
                self.redis_client = redis.from_url(redis_url)
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True  # Automatically decode responses
                )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connection established successfully")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            # Fallback to in-memory cache
            self._fallback_cache = {}
            self.redis_client = None
    
    def _serialize(self, value: Any) -> str:
        """🔐 SECURE: Serialize value to JSON (replaces unsafe pickle)"""
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error: {e}")
            return json.dumps({"error": "serialization_failed", "type": str(type(value))})
    
    def _deserialize(self, value: str) -> Any:
        """🔐 SECURE: Deserialize value from JSON (replaces unsafe pickle)"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Deserialization error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """Set a value in cache with optional expiration"""
        try:
            serialized_value = self._serialize(value)
            
            if self.redis_client:
                if expire:
                    if isinstance(expire, timedelta):
                        expire = int(expire.total_seconds())
                    return self.redis_client.setex(key, expire, serialized_value)
                else:
                    return self.redis_client.set(key, serialized_value)
            else:
                # Fallback to in-memory cache
                self._fallback_cache[key] = serialized_value
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def get(self, key: str) -> Any:
        """Get a value from cache"""
        try:
            if self.redis_client:
                serialized_value = self.redis_client.get(key)
            else:
                # Fallback to in-memory cache
                serialized_value = self._fallback_cache.get(key)
            
            if serialized_value is None:
                return None
            
            return self._deserialize(serialized_value)
            
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                # Fallback to in-memory cache
                if key in self._fallback_cache:
                    del self._fallback_cache[key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                # Fallback to in-memory cache
                return key in self._fallback_cache
                
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key"""
        try:
            if self.redis_client:
                return bool(self.redis_client.expire(key, seconds))
            else:
                # In-memory cache doesn't support expiration
                return True
                
        except Exception as e:
            logger.error(f"Cache expire error for key '{key}': {e}")
            return False
    
    def flush_all(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                return bool(self.redis_client.flushdb())
            else:
                # Fallback to in-memory cache
                self._fallback_cache.clear()
                return True
                
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "status": "connected"
                }
            else:
                return {
                    "status": "fallback_memory",
                    "keys_count": len(self._fallback_cache),
                    "memory_usage": "unknown"
                }
                
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

# Cache decorators for easy use
def cache_result(expire: Optional[int] = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, expire)
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Decorator to invalidate cache entries matching pattern"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # In a real implementation, you'd use Redis SCAN to find matching keys
            # For now, this is a placeholder
            logger.info(f"Cache invalidation requested for pattern: {pattern}")
            
            return result
        return wrapper
    return decorator

# Global cache instance
cache = SecureRedisCache()

# Health check function
def health_check() -> dict:
    """Check Redis cache health"""
    try:
        if cache.redis_client:
            cache.redis_client.ping()
            return {"status": "healthy", "service": "redis_cache"}
        else:
            return {"status": "fallback", "service": "memory_cache"}
    except Exception as e:
        return {"status": "unhealthy", "service": "redis_cache", "error": str(e)}

# Example usage functions
def cache_user_session(user_id: int, session_data: dict, expire_hours: int = 24):
    """Cache user session data"""
    cache_key = f"user_session:{user_id}"
    expire_seconds = expire_hours * 3600
    return cache.set(cache_key, session_data, expire_seconds)

def get_user_session(user_id: int) -> Optional[dict]:
    """Get user session data from cache"""
    cache_key = f"user_session:{user_id}"
    return cache.get(cache_key)

def cache_ai_response(prompt_hash: str, response: dict, expire_hours: int = 1):
    """Cache AI service responses"""
    cache_key = f"ai_response:{prompt_hash}"
    expire_seconds = expire_hours * 3600
    return cache.set(cache_key, response, expire_seconds)

def get_cached_ai_response(prompt_hash: str) -> Optional[dict]:
    """Get cached AI response"""
    cache_key = f"ai_response:{prompt_hash}"
    return cache.get(cache_key)

if __name__ == "__main__":
    # Test the secure cache service
    print("🧪 Testing Secure Redis Cache Service...")
    
    # Test basic operations
    test_key = "test_key"
    test_value = {"message": "Hello, secure cache!", "timestamp": "2025-07-31"}
    
    # Set value
    success = cache.set(test_key, test_value, 60)
    print(f"Set operation: {'✅ Success' if success else '❌ Failed'}")
    
    # Get value
    retrieved_value = cache.get(test_key)
    print(f"Get operation: {'✅ Success' if retrieved_value == test_value else '❌ Failed'}")
    
    # Get stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Health check
    health = health_check()
    print(f"Health check: {health}")
    
    print("🎉 Secure Redis Cache Service test completed!")

