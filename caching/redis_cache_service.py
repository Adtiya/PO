"""
Enterprise AI System - Redis Caching Service
Provides intelligent caching for improved performance and scalability
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import redis
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import zlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'redis-cache-service-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Redis configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "decode_responses": False,  # We'll handle encoding ourselves
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True
}

class IntelligentCache:
    """Intelligent caching system with Redis backend"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "start_time": datetime.utcnow()
        }
        self.connect_redis()
    
    def connect_redis(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(**REDIS_CONFIG)
            # Test connection
            self.redis_client.ping()
            print("✅ Connected to Redis server")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("🔄 Using in-memory fallback cache")
            self.redis_client = None
            self.fallback_cache = {}
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"enterprise_ai:{namespace}:{key}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Use pickle for Python objects, compress with zlib
            serialized = pickle.dumps(data)
            compressed = zlib.compress(serialized)
            return compressed
        except Exception as e:
            raise ValueError(f"Failed to serialize data: {e}")
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            # Decompress and unpickle
            decompressed = zlib.decompress(data)
            deserialized = pickle.loads(decompressed)
            return deserialized
        except Exception as e:
            raise ValueError(f"Failed to deserialize data: {e}")
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.redis_client:
                # Redis backend
                data = self.redis_client.get(cache_key)
                if data is not None:
                    self.cache_stats["hits"] += 1
                    return self._deserialize_data(data)
                else:
                    self.cache_stats["misses"] += 1
                    return None
            else:
                # Fallback in-memory cache
                if cache_key in self.fallback_cache:
                    entry = self.fallback_cache[cache_key]
                    if entry["expires_at"] > datetime.utcnow():
                        self.cache_stats["hits"] += 1
                        return entry["data"]
                    else:
                        del self.fallback_cache[cache_key]
                
                self.cache_stats["misses"] += 1
                return None
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            print(f"Cache get error: {e}")
            return None
    
    def set(self, namespace: str, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL (time to live) in seconds"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.redis_client:
                # Redis backend
                serialized_data = self._serialize_data(value)
                result = self.redis_client.setex(cache_key, ttl, serialized_data)
                if result:
                    self.cache_stats["sets"] += 1
                    return True
                return False
            else:
                # Fallback in-memory cache
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                self.fallback_cache[cache_key] = {
                    "data": value,
                    "expires_at": expires_at
                }
                self.cache_stats["sets"] += 1
                return True
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.redis_client:
                # Redis backend
                result = self.redis_client.delete(cache_key)
                if result > 0:
                    self.cache_stats["deletes"] += 1
                    return True
                return False
            else:
                # Fallback in-memory cache
                if cache_key in self.fallback_cache:
                    del self.fallback_cache[cache_key]
                    self.cache_stats["deletes"] += 1
                    return True
                return False
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(cache_key))
            else:
                if cache_key in self.fallback_cache:
                    entry = self.fallback_cache[cache_key]
                    if entry["expires_at"] > datetime.utcnow():
                        return True
                    else:
                        del self.fallback_cache[cache_key]
                return False
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        try:
            if self.redis_client:
                pattern = self._generate_key(namespace, "*")
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    self.cache_stats["deletes"] += deleted
                    return deleted
                return 0
            else:
                # Fallback in-memory cache
                prefix = self._generate_key(namespace, "")
                keys_to_delete = [k for k in self.fallback_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
                self.cache_stats["deletes"] += len(keys_to_delete)
                return len(keys_to_delete)
                
        except Exception as e:
            self.cache_stats["errors"] += 1
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        uptime = (datetime.utcnow() - self.cache_stats["start_time"]).total_seconds()
        
        stats = {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "uptime_seconds": uptime,
            "backend": "redis" if self.redis_client else "in_memory",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add Redis-specific stats if available
        if self.redis_client:
            try:
                redis_info = self.redis_client.info()
                stats["redis_info"] = {
                    "used_memory": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_commands_processed": redis_info.get("total_commands_processed"),
                    "keyspace_hits": redis_info.get("keyspace_hits"),
                    "keyspace_misses": redis_info.get("keyspace_misses")
                }
            except:
                pass
        
        return stats

# Global cache instance
cache = IntelligentCache()

# Cache strategies for different data types
CACHE_STRATEGIES = {
    "ai_nlp_results": {"ttl": 1800, "namespace": "nlp"},  # 30 minutes
    "ai_vision_results": {"ttl": 3600, "namespace": "vision"},  # 1 hour
    "ai_analytics_results": {"ttl": 900, "namespace": "analytics"},  # 15 minutes
    "recommendations": {"ttl": 1800, "namespace": "recommendations"},  # 30 minutes
    "user_profiles": {"ttl": 3600, "namespace": "users"},  # 1 hour
    "system_metrics": {"ttl": 300, "namespace": "metrics"},  # 5 minutes
    "api_responses": {"ttl": 600, "namespace": "api"}  # 10 minutes
}

def generate_cache_key(data: Dict) -> str:
    """Generate deterministic cache key from data"""
    # Create hash of sorted data
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

# API Routes

@app.route('/cache/get', methods=['POST'])
def cache_get():
    """Get value from cache"""
    try:
        data = request.get_json()
        if not data or 'namespace' not in data or 'key' not in data:
            return jsonify({"error": "Namespace and key are required"}), 400
        
        namespace = data['namespace']
        key = data['key']
        
        value = cache.get(namespace, key)
        
        return jsonify({
            "found": value is not None,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/set', methods=['POST'])
def cache_set():
    """Set value in cache"""
    try:
        data = request.get_json()
        if not data or 'namespace' not in data or 'key' not in data or 'value' not in data:
            return jsonify({"error": "Namespace, key, and value are required"}), 400
        
        namespace = data['namespace']
        key = data['key']
        value = data['value']
        ttl = data.get('ttl', 3600)
        
        success = cache.set(namespace, key, value, ttl)
        
        return jsonify({
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/delete', methods=['POST'])
def cache_delete():
    """Delete value from cache"""
    try:
        data = request.get_json()
        if not data or 'namespace' not in data or 'key' not in data:
            return jsonify({"error": "Namespace and key are required"}), 400
        
        namespace = data['namespace']
        key = data['key']
        
        success = cache.delete(namespace, key)
        
        return jsonify({
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/exists', methods=['POST'])
def cache_exists():
    """Check if key exists in cache"""
    try:
        data = request.get_json()
        if not data or 'namespace' not in data or 'key' not in data:
            return jsonify({"error": "Namespace and key are required"}), 400
        
        namespace = data['namespace']
        key = data['key']
        
        exists = cache.exists(namespace, key)
        
        return jsonify({
            "exists": exists,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/clear', methods=['POST'])
def cache_clear():
    """Clear namespace or specific keys"""
    try:
        data = request.get_json()
        if not data or 'namespace' not in data:
            return jsonify({"error": "Namespace is required"}), 400
        
        namespace = data['namespace']
        
        deleted_count = cache.clear_namespace(namespace)
        
        return jsonify({
            "deleted_count": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/smart-cache', methods=['POST'])
def smart_cache():
    """Intelligent caching based on data type"""
    try:
        data = request.get_json()
        if not data or 'data_type' not in data or 'data' not in data:
            return jsonify({"error": "Data type and data are required"}), 400
        
        data_type = data['data_type']
        cache_data = data['data']
        operation = data.get('operation', 'get')  # get, set, delete
        
        if data_type not in CACHE_STRATEGIES:
            return jsonify({"error": f"Unknown data type: {data_type}"}), 400
        
        strategy = CACHE_STRATEGIES[data_type]
        namespace = strategy['namespace']
        ttl = strategy['ttl']
        
        # Generate cache key from data
        cache_key = generate_cache_key(cache_data)
        
        if operation == 'get':
            value = cache.get(namespace, cache_key)
            return jsonify({
                "found": value is not None,
                "value": value,
                "cache_key": cache_key,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif operation == 'set':
            if 'result' not in data:
                return jsonify({"error": "Result is required for set operation"}), 400
            
            result = data['result']
            success = cache.set(namespace, cache_key, result, ttl)
            
            return jsonify({
                "success": success,
                "cache_key": cache_key,
                "ttl": ttl,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        elif operation == 'delete':
            success = cache.delete(namespace, cache_key)
            return jsonify({
                "success": success,
                "cache_key": cache_key,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        else:
            return jsonify({"error": f"Unknown operation: {operation}"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cache/stats')
def cache_stats():
    """Get cache statistics"""
    try:
        stats = cache.get_stats()
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for cache service"""
    return jsonify({
        "service": "Redis Cache Service",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "intelligent_caching",
            "namespace_management",
            "ttl_support",
            "compression",
            "fallback_cache",
            "cache_statistics"
        ],
        "backend": "redis" if cache.redis_client else "in_memory",
        "cache_strategies": list(CACHE_STRATEGIES.keys()),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/info')
def service_info():
    """Get service information"""
    return jsonify({
        "service_name": "Enterprise AI Redis Cache Service",
        "description": "Intelligent caching service for improved performance and scalability",
        "version": "2.0.0",
        "features": [
            "Redis backend with in-memory fallback",
            "Intelligent cache key generation",
            "Data compression and serialization",
            "Namespace-based organization",
            "TTL (Time To Live) support",
            "Cache statistics and monitoring",
            "Smart caching strategies by data type"
        ],
        "endpoints": [
            "/cache/get",
            "/cache/set", 
            "/cache/delete",
            "/cache/exists",
            "/cache/clear",
            "/cache/smart-cache",
            "/cache/stats"
        ],
        "cache_strategies": CACHE_STRATEGIES,
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Enterprise AI Redis Cache Service...")
    print("📦 Cache Service URL: http://localhost:7002")
    print("📊 Cache Statistics: http://localhost:7002/cache/stats")
    print("🏥 Health Check: http://localhost:7002/health")
    print("🔧 Backend:", "Redis" if cache.redis_client else "In-Memory Fallback")
    
    app.run(host='0.0.0.0', port=7002, debug=True)

