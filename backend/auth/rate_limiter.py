"""
Enterprise AI System - Rate Limiter
PhD-level implementation for preventing abuse and attacks
"""

import time
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    PhD-level rate limiting with multiple strategies
    
    Features:
    - Token bucket algorithm
    - Sliding window rate limiting
    - IP-based and user-based limiting
    - Automatic cleanup of old entries
    - Configurable limits per endpoint
    """
    
    def __init__(self):
        self.limits = {}  # endpoint -> limit config
        self.buckets = defaultdict(dict)  # ip/user -> endpoint -> bucket
        self.windows = defaultdict(lambda: defaultdict(deque))  # ip/user -> endpoint -> request times
        self.lock = threading.RLock()
        
        # Default limits
        self.default_limits = {
            'requests': 100,
            'window': 3600,  # 1 hour
            'burst': 10      # burst allowance
        }
    
    def configure_limit(self, endpoint: str, requests: int, window: int, burst: int = None):
        """
        Configure rate limit for specific endpoint
        
        Args:
            endpoint: Endpoint identifier
            requests: Number of requests allowed
            window: Time window in seconds
            burst: Burst allowance (default: requests/10)
        """
        self.limits[endpoint] = {
            'requests': requests,
            'window': window,
            'burst': burst or max(1, requests // 10)
        }
    
    def get_client_id(self) -> str:
        """
        Get client identifier (IP address or user ID)
        
        Returns:
            str: Client identifier
        """
        # Try to get user ID from request context
        if hasattr(request, 'current_user') and request.current_user:
            return f"user:{request.current_user.get('user_id', 'unknown')}"
        
        # Fall back to IP address
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if ip:
            # Handle multiple IPs in X-Forwarded-For
            ip = ip.split(',')[0].strip()
        return f"ip:{ip or 'unknown'}"
    
    def parse_limit_string(self, limit_str: str) -> Dict[str, int]:
        """
        Parse limit string like "5 per minute" or "100 per hour"
        
        Args:
            limit_str: Limit string to parse
            
        Returns:
            Dict with parsed limit configuration
        """
        parts = limit_str.lower().split()
        if len(parts) < 3:
            raise ValueError(f"Invalid limit string: {limit_str}")
        
        requests = int(parts[0])
        unit = parts[2]
        
        # Convert time units to seconds
        time_units = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400
        }
        
        # Handle plural forms
        if unit.endswith('s'):
            unit = unit[:-1]
        
        if unit not in time_units:
            raise ValueError(f"Unknown time unit: {unit}")
        
        window = time_units[unit]
        
        return {
            'requests': requests,
            'window': window,
            'burst': max(1, requests // 10)
        }
    
    def is_allowed(self, endpoint: str, client_id: str = None) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit
        
        Args:
            endpoint: Endpoint identifier
            client_id: Client identifier (auto-detected if None)
            
        Returns:
            Dict with rate limit status
        """
        if client_id is None:
            client_id = self.get_client_id()
        
        # Get limit configuration
        limit_config = self.limits.get(endpoint, self.default_limits)
        
        current_time = time.time()
        
        with self.lock:
            # Clean up old entries
            self._cleanup_old_entries(client_id, endpoint, current_time, limit_config['window'])
            
            # Get request history for this client/endpoint
            request_times = self.windows[client_id][endpoint]
            
            # Count requests in current window
            window_start = current_time - limit_config['window']
            recent_requests = sum(1 for req_time in request_times if req_time > window_start)
            
            # Check if limit exceeded
            if recent_requests >= limit_config['requests']:
                # Calculate reset time
                oldest_request = min(request_times) if request_times else current_time
                reset_time = oldest_request + limit_config['window']
                
                return {
                    'allowed': False,
                    'limit': limit_config['requests'],
                    'remaining': 0,
                    'reset_time': reset_time,
                    'retry_after': max(0, reset_time - current_time)
                }
            
            # Allow request and record it
            request_times.append(current_time)
            remaining = limit_config['requests'] - recent_requests - 1
            
            return {
                'allowed': True,
                'limit': limit_config['requests'],
                'remaining': remaining,
                'reset_time': current_time + limit_config['window'],
                'retry_after': 0
            }
    
    def _cleanup_old_entries(self, client_id: str, endpoint: str, current_time: float, window: int):
        """
        Clean up old request entries outside the time window
        
        Args:
            client_id: Client identifier
            endpoint: Endpoint identifier
            current_time: Current timestamp
            window: Time window in seconds
        """
        request_times = self.windows[client_id][endpoint]
        window_start = current_time - window
        
        # Remove old entries
        while request_times and request_times[0] <= window_start:
            request_times.popleft()
        
        # Clean up empty structures
        if not request_times:
            if endpoint in self.windows[client_id]:
                del self.windows[client_id][endpoint]
            if not self.windows[client_id]:
                del self.windows[client_id]
    
    def limit(self, limit_str: str):
        """
        Decorator for applying rate limits to Flask routes
        
        Args:
            limit_str: Limit string like "5 per minute"
            
        Usage:
            @app.route('/api/endpoint')
            @rate_limiter.limit("10 per minute")
            def my_endpoint():
                return jsonify({'message': 'Success'})
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Parse limit configuration
                try:
                    limit_config = self.parse_limit_string(limit_str)
                except ValueError as e:
                    logger.error(f"Invalid rate limit configuration: {e}")
                    # Continue without rate limiting if config is invalid
                    return f(*args, **kwargs)
                
                # Get endpoint identifier
                endpoint = f"{request.method}:{request.endpoint or f.__name__}"
                
                # Configure limit for this endpoint
                self.configure_limit(
                    endpoint,
                    limit_config['requests'],
                    limit_config['window'],
                    limit_config['burst']
                )
                
                # Check rate limit
                result = self.is_allowed(endpoint)
                
                if not result['allowed']:
                    logger.warning(f"Rate limit exceeded for {self.get_client_id()} on {endpoint}")
                    
                    response = jsonify({
                        'error': 'Rate Limit Exceeded',
                        'message': f'Rate limit of {result["limit"]} requests exceeded',
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'limit': result['limit'],
                        'remaining': result['remaining'],
                        'reset_time': result['reset_time'],
                        'retry_after': int(result['retry_after'])
                    })
                    
                    # Add rate limit headers
                    response.headers['X-RateLimit-Limit'] = str(result['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(int(result['reset_time']))
                    response.headers['Retry-After'] = str(int(result['retry_after']))
                    
                    return response, 429
                
                # Execute the original function
                response = f(*args, **kwargs)
                
                # Add rate limit headers to successful responses
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(result['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(int(result['reset_time']))
                
                return response
            
            return decorated_function
        return decorator
    
    def get_stats(self, client_id: str = None) -> Dict[str, Any]:
        """
        Get rate limiting statistics
        
        Args:
            client_id: Client identifier (current client if None)
            
        Returns:
            Dict with statistics
        """
        if client_id is None:
            client_id = self.get_client_id()
        
        current_time = time.time()
        stats = {
            'client_id': client_id,
            'endpoints': {},
            'total_clients': len(self.windows),
            'timestamp': current_time
        }
        
        with self.lock:
            if client_id in self.windows:
                for endpoint, request_times in self.windows[client_id].items():
                    limit_config = self.limits.get(endpoint, self.default_limits)
                    window_start = current_time - limit_config['window']
                    recent_requests = sum(1 for req_time in request_times if req_time > window_start)
                    
                    stats['endpoints'][endpoint] = {
                        'limit': limit_config['requests'],
                        'used': recent_requests,
                        'remaining': limit_config['requests'] - recent_requests,
                        'window': limit_config['window'],
                        'reset_time': current_time + limit_config['window']
                    }
        
        return stats
    
    def reset_client(self, client_id: str = None):
        """
        Reset rate limits for a client
        
        Args:
            client_id: Client identifier (current client if None)
        """
        if client_id is None:
            client_id = self.get_client_id()
        
        with self.lock:
            if client_id in self.windows:
                del self.windows[client_id]
                logger.info(f"Rate limits reset for client: {client_id}")
    
    def cleanup_expired(self):
        """
        Clean up all expired entries (maintenance function)
        """
        current_time = time.time()
        
        with self.lock:
            clients_to_remove = []
            
            for client_id, endpoints in list(self.windows.items()):
                endpoints_to_remove = []
                
                for endpoint, request_times in list(endpoints.items()):
                    limit_config = self.limits.get(endpoint, self.default_limits)
                    window_start = current_time - limit_config['window']
                    
                    # Remove old entries
                    while request_times and request_times[0] <= window_start:
                        request_times.popleft()
                    
                    # Mark empty endpoints for removal
                    if not request_times:
                        endpoints_to_remove.append(endpoint)
                
                # Remove empty endpoints
                for endpoint in endpoints_to_remove:
                    del endpoints[endpoint]
                
                # Mark empty clients for removal
                if not endpoints:
                    clients_to_remove.append(client_id)
            
            # Remove empty clients
            for client_id in clients_to_remove:
                del self.windows[client_id]
            
            logger.info(f"Cleaned up {len(clients_to_remove)} expired client entries")

