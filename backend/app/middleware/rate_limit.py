"""
Rate limiting middleware for the Enterprise AI System.
Implements sliding window rate limiting with Redis backend.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
import time
import hashlib
from typing import Optional, Dict, Tuple
import asyncio

from app.core.config import settings
from app.core.exceptions import RateLimitException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window algorithm."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis_service = RedisService()
        
        # Rate limit configurations
        self.rate_limits = {
            # Global rate limits
            "global": {
                "requests_per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
                "burst": settings.RATE_LIMIT_BURST,
                "window_seconds": 60
            },
            
            # API specific rate limits
            "api": {
                "requests_per_minute": settings.API_RATE_LIMIT_PER_MINUTE,
                "burst": 20,
                "window_seconds": 60
            },
            
            # LLM specific rate limits
            "llm": {
                "requests_per_minute": settings.LLM_RATE_LIMIT_PER_MINUTE,
                "burst": 5,
                "window_seconds": 60
            },
            
            # Authentication endpoints
            "auth": {
                "requests_per_minute": 10,
                "burst": 3,
                "window_seconds": 60
            }
        }
        
        # Paths that are exempt from rate limiting
        self.exempt_paths = {
            "/health",
            "/health/detailed",
            "/metrics"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and apply rate limiting."""
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        try:
            # Check if path is exempt
            if request.url.path in self.exempt_paths:
                return await call_next(request)
            
            # Determine rate limit category
            category = self._get_rate_limit_category(request.url.path)
            
            # Get client identifier
            client_id = self._get_client_identifier(request)
            
            # Check rate limit
            allowed, retry_after = await self._check_rate_limit(
                client_id, category, request.url.path
            )
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    client_id=client_id,
                    category=category,
                    path=request.url.path,
                    retry_after=retry_after
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate Limit Exceeded",
                        "message": f"Too many requests. Try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                        "request_id": getattr(request.state, 'request_id', None)
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Category": category
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            await self._add_rate_limit_headers(response, client_id, category)
            
            return response
            
        except Exception as e:
            logger.error(
                "Rate limit middleware error",
                error=str(e),
                path=request.url.path,
                exc_info=True
            )
            # Continue without rate limiting on error
            return await call_next(request)
    
    def _get_rate_limit_category(self, path: str) -> str:
        """Determine rate limit category based on request path."""
        if path.startswith("/api/v1/auth/"):
            return "auth"
        elif path.startswith("/api/v1/llm/") or path.startswith("/api/v1/conversations/"):
            return "llm"
        elif path.startswith("/api/"):
            return "api"
        else:
            return "global"
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Use user ID if authenticated
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Use IP address for unauthenticated requests
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(
        self, 
        client_id: str, 
        category: str, 
        path: str
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limits using sliding window algorithm.
        Returns (allowed, retry_after_seconds).
        """
        config = self.rate_limits.get(category, self.rate_limits["global"])
        
        # Create Redis keys
        window_key = f"rate_limit:{category}:{client_id}:window"
        burst_key = f"rate_limit:{category}:{client_id}:burst"
        
        current_time = int(time.time())
        window_start = current_time - config["window_seconds"]
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = await self.redis_service.pipeline()
            
            # Remove old entries from sliding window
            await pipe.zremrangebyscore(window_key, 0, window_start)
            
            # Count current requests in window
            await pipe.zcard(window_key)
            
            # Get burst count
            await pipe.get(burst_key)
            
            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1] if len(results) > 1 else 0
            burst_count = int(results[2]) if len(results) > 2 and results[2] else 0
            
            # Check burst limit
            if burst_count >= config["burst"]:
                # Check if burst window has expired
                burst_ttl = await self.redis_service.ttl(burst_key)
                if burst_ttl > 0:
                    return False, burst_ttl
            
            # Check window limit
            if current_count >= config["requests_per_minute"]:
                # Calculate retry after based on oldest request in window
                oldest_request = await self.redis_service.zrange(
                    window_key, 0, 0, withscores=True
                )
                if oldest_request:
                    oldest_time = int(oldest_request[0][1])
                    retry_after = oldest_time + config["window_seconds"] - current_time
                    return False, max(1, retry_after)
                else:
                    return False, config["window_seconds"]
            
            # Allow request and record it
            await self._record_request(client_id, category, current_time, config)
            
            return True, 0
            
        except Exception as e:
            logger.error(
                "Rate limit check error",
                error=str(e),
                client_id=client_id,
                category=category
            )
            # Allow request on error
            return True, 0
    
    async def _record_request(
        self, 
        client_id: str, 
        category: str, 
        timestamp: int, 
        config: Dict
    ):
        """Record request in rate limit tracking."""
        window_key = f"rate_limit:{category}:{client_id}:window"
        burst_key = f"rate_limit:{category}:{client_id}:burst"
        
        try:
            pipe = await self.redis_service.pipeline()
            
            # Add request to sliding window
            request_id = f"{timestamp}:{hashlib.md5(f'{client_id}:{timestamp}'.encode()).hexdigest()[:8]}"
            await pipe.zadd(window_key, {request_id: timestamp})
            await pipe.expire(window_key, config["window_seconds"] + 10)  # Extra buffer
            
            # Increment burst counter
            await pipe.incr(burst_key)
            await pipe.expire(burst_key, 10)  # 10 second burst window
            
            await pipe.execute()
            
        except Exception as e:
            logger.error(
                "Failed to record request",
                error=str(e),
                client_id=client_id,
                category=category
            )
    
    async def _add_rate_limit_headers(
        self, 
        response: Response, 
        client_id: str, 
        category: str
    ):
        """Add rate limit information to response headers."""
        try:
            config = self.rate_limits.get(category, self.rate_limits["global"])
            window_key = f"rate_limit:{category}:{client_id}:window"
            
            # Get current usage
            current_count = await self.redis_service.zcard(window_key)
            remaining = max(0, config["requests_per_minute"] - current_count)
            
            # Calculate reset time
            current_time = int(time.time())
            reset_time = current_time + config["window_seconds"]
            
            # Add headers
            response.headers["X-RateLimit-Limit"] = str(config["requests_per_minute"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Category"] = category
            
        except Exception as e:
            logger.error(
                "Failed to add rate limit headers",
                error=str(e),
                client_id=client_id,
                category=category
            )


class TokenBucketRateLimit:
    """Token bucket rate limiting for specific operations."""
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
    
    async def check_limit(
        self,
        key: str,
        capacity: int,
        refill_rate: float,
        tokens_requested: int = 1
    ) -> Tuple[bool, float]:
        """
        Check token bucket rate limit.
        Returns (allowed, retry_after_seconds).
        """
        bucket_key = f"token_bucket:{key}"
        current_time = time.time()
        
        try:
            # Get current bucket state
            bucket_data = await self.redis_service.hgetall(bucket_key)
            
            if bucket_data:
                last_refill = float(bucket_data.get("last_refill", current_time))
                tokens = float(bucket_data.get("tokens", capacity))
            else:
                last_refill = current_time
                tokens = capacity
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            tokens_to_add = time_elapsed * refill_rate
            tokens = min(capacity, tokens + tokens_to_add)
            
            # Check if enough tokens available
            if tokens >= tokens_requested:
                # Consume tokens
                tokens -= tokens_requested
                
                # Update bucket state
                await self.redis_service.hset(bucket_key, {
                    "tokens": str(tokens),
                    "last_refill": str(current_time)
                })
                await self.redis_service.expire(bucket_key, 3600)  # 1 hour TTL
                
                return True, 0.0
            else:
                # Not enough tokens, calculate retry after
                tokens_needed = tokens_requested - tokens
                retry_after = tokens_needed / refill_rate
                
                return False, retry_after
                
        except Exception as e:
            logger.error(
                "Token bucket rate limit error",
                error=str(e),
                key=key
            )
            # Allow on error
            return True, 0.0


# ============================================================================
# RATE LIMIT DECORATORS
# ============================================================================

def rate_limit(
    requests_per_minute: int,
    burst: int = None,
    key_func: callable = None
):
    """Decorator for endpoint-specific rate limiting."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a dependency in FastAPI
            # For now, just call the original function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Export commonly used items
__all__ = [
    "RateLimitMiddleware",
    "TokenBucketRateLimit",
    "rate_limit"
]

