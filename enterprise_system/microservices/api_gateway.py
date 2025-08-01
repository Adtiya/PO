"""
Enterprise AI System - API Gateway
Centralized gateway for all microservices with load balancing, authentication, and routing
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import jwt
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'api-gateway-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Service Registry - Maps service names to their endpoints
SERVICE_REGISTRY = {
    "auth": {
        "name": "Authentication Service",
        "base_url": "http://localhost:8000",
        "health_endpoint": "/health",
        "status": "unknown"
    },
    "nlp": {
        "name": "AI NLP Service", 
        "base_url": "http://localhost:5002",
        "health_endpoint": "/health",
        "status": "unknown"
    },
    "vision": {
        "name": "AI Vision Service",
        "base_url": "http://localhost:5003", 
        "health_endpoint": "/health",
        "status": "unknown"
    },
    "analytics": {
        "name": "AI Analytics Service",
        "base_url": "http://localhost:5004",
        "health_endpoint": "/health", 
        "status": "unknown"
    },
    "recommendations": {
        "name": "AI Recommendation Service",
        "base_url": "http://localhost:5005",
        "health_endpoint": "/health",
        "status": "unknown"
    },
    "pi": {
        "name": "Profile/Identity Service",
        "base_url": "http://localhost:5001",
        "health_endpoint": "/health",
        "status": "unknown"
    }
}

# Request tracking for analytics
REQUEST_ANALYTICS = {
    "total_requests": 0,
    "requests_by_service": {},
    "requests_by_hour": {},
    "error_count": 0,
    "average_response_time": 0,
    "start_time": datetime.utcnow()
}

class LoadBalancer:
    """Simple round-robin load balancer for service instances"""
    
    def __init__(self):
        self.service_instances = {}
        self.current_index = {}
    
    def add_instance(self, service_name: str, instance_url: str):
        """Add a service instance"""
        if service_name not in self.service_instances:
            self.service_instances[service_name] = []
            self.current_index[service_name] = 0
        
        if instance_url not in self.service_instances[service_name]:
            self.service_instances[service_name].append(instance_url)
    
    def get_instance(self, service_name: str) -> Optional[str]:
        """Get next available instance using round-robin"""
        if service_name not in self.service_instances or not self.service_instances[service_name]:
            return None
        
        instances = self.service_instances[service_name]
        index = self.current_index[service_name]
        instance = instances[index]
        
        # Move to next instance
        self.current_index[service_name] = (index + 1) % len(instances)
        
        return instance

# Initialize load balancer
load_balancer = LoadBalancer()

# Add default instances
for service_name, config in SERVICE_REGISTRY.items():
    load_balancer.add_instance(service_name, config["base_url"])

def check_service_health():
    """Check health of all registered services"""
    for service_name, config in SERVICE_REGISTRY.items():
        try:
            response = requests.get(
                f"{config['base_url']}{config['health_endpoint']}", 
                timeout=5
            )
            if response.status_code == 200:
                config["status"] = "healthy"
                config["last_check"] = datetime.utcnow().isoformat()
            else:
                config["status"] = "unhealthy"
        except Exception as e:
            config["status"] = "unreachable"
            config["error"] = str(e)

def authenticate_request(f):
    """Decorator to authenticate requests using JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip authentication for health checks and public endpoints
        if request.endpoint in ['health_check', 'service_status', 'gateway_info']:
            return f(*args, **kwargs)
        
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No authorization token provided'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # For demo purposes, we'll accept any valid-looking JWT
            # In production, verify against your auth service
            if len(token) > 20:  # Simple validation
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid token format'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Token validation failed'}), 401
    
    return decorated

def log_request(service_name: str, response_time: float, status_code: int):
    """Log request for analytics"""
    REQUEST_ANALYTICS["total_requests"] += 1
    
    # Track by service
    if service_name not in REQUEST_ANALYTICS["requests_by_service"]:
        REQUEST_ANALYTICS["requests_by_service"][service_name] = 0
    REQUEST_ANALYTICS["requests_by_service"][service_name] += 1
    
    # Track by hour
    current_hour = datetime.utcnow().strftime('%Y-%m-%d %H:00')
    if current_hour not in REQUEST_ANALYTICS["requests_by_hour"]:
        REQUEST_ANALYTICS["requests_by_hour"][current_hour] = 0
    REQUEST_ANALYTICS["requests_by_hour"][current_hour] += 1
    
    # Track errors
    if status_code >= 400:
        REQUEST_ANALYTICS["error_count"] += 1
    
    # Update average response time
    total_requests = REQUEST_ANALYTICS["total_requests"]
    current_avg = REQUEST_ANALYTICS["average_response_time"]
    REQUEST_ANALYTICS["average_response_time"] = (
        (current_avg * (total_requests - 1) + response_time) / total_requests
    )

def proxy_request(service_name: str, path: str = ""):
    """Proxy request to appropriate microservice"""
    start_time = time.time()
    
    # Get service instance
    instance_url = load_balancer.get_instance(service_name)
    if not instance_url:
        return jsonify({"error": f"Service {service_name} not available"}), 503
    
    # Build target URL
    target_url = f"{instance_url}{path}"
    
    try:
        # Forward request
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args, timeout=30)
        elif request.method == 'POST':
            response = requests.post(
                target_url, 
                json=request.get_json(),
                params=request.args,
                timeout=30
            )
        elif request.method == 'PUT':
            response = requests.put(
                target_url,
                json=request.get_json(), 
                params=request.args,
                timeout=30
            )
        elif request.method == 'DELETE':
            response = requests.delete(target_url, params=request.args, timeout=30)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log request
        log_request(service_name, response_time, response.status_code)
        
        # Return response
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
    except requests.exceptions.Timeout:
        log_request(service_name, (time.time() - start_time) * 1000, 504)
        return jsonify({"error": "Service timeout"}), 504
    except requests.exceptions.ConnectionError:
        log_request(service_name, (time.time() - start_time) * 1000, 503)
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        log_request(service_name, (time.time() - start_time) * 1000, 500)
        return jsonify({"error": str(e)}), 500

# Gateway Routes

@app.route('/health')
def health_check():
    """Gateway health check"""
    check_service_health()
    
    healthy_services = sum(1 for config in SERVICE_REGISTRY.values() if config["status"] == "healthy")
    total_services = len(SERVICE_REGISTRY)
    
    return jsonify({
        "service": "API Gateway",
        "status": "healthy",
        "version": "2.0.0",
        "services_healthy": f"{healthy_services}/{total_services}",
        "uptime_seconds": (datetime.utcnow() - REQUEST_ANALYTICS["start_time"]).total_seconds(),
        "total_requests_handled": REQUEST_ANALYTICS["total_requests"],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/gateway/status')
def service_status():
    """Get status of all services"""
    check_service_health()
    return jsonify({
        "gateway": "API Gateway v2.0.0",
        "services": SERVICE_REGISTRY,
        "load_balancer": {
            "instances": load_balancer.service_instances,
            "current_index": load_balancer.current_index
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/gateway/analytics')
@authenticate_request
def gateway_analytics():
    """Get gateway analytics"""
    return jsonify({
        "analytics": REQUEST_ANALYTICS,
        "services": {name: config["status"] for name, config in SERVICE_REGISTRY.items()},
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/gateway/info')
def gateway_info():
    """Get gateway information"""
    return jsonify({
        "name": "Enterprise AI System API Gateway",
        "version": "2.0.0",
        "description": "Centralized gateway for all AI microservices",
        "features": [
            "Service Discovery and Registration",
            "Load Balancing with Round-Robin",
            "Request Authentication and Authorization", 
            "Request Logging and Analytics",
            "Health Monitoring",
            "Error Handling and Timeouts"
        ],
        "available_services": list(SERVICE_REGISTRY.keys()),
        "routing_patterns": {
            "/api/auth/*": "Authentication Service",
            "/api/nlp/*": "AI NLP Service",
            "/api/vision/*": "AI Vision Service", 
            "/api/analytics/*": "AI Analytics Service",
            "/api/recommendations/*": "AI Recommendation Service",
            "/api/pi/*": "Profile/Identity Service"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# Service Routing

@app.route('/api/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_auth(path):
    """Route to authentication service"""
    return proxy_request('auth', f'/api/v1/{path}')

@app.route('/api/nlp/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@authenticate_request
def route_nlp(path):
    """Route to NLP service"""
    return proxy_request('nlp', f'/api/nlp/{path}')

@app.route('/api/vision/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@authenticate_request
def route_vision(path):
    """Route to Vision service"""
    return proxy_request('vision', f'/api/vision/{path}')

@app.route('/api/analytics/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@authenticate_request
def route_analytics(path):
    """Route to Analytics service"""
    return proxy_request('analytics', f'/api/analytics/{path}')

@app.route('/api/recommendations/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@authenticate_request
def route_recommendations(path):
    """Route to Recommendations service"""
    return proxy_request('recommendations', f'/api/recommendations/{path}')

@app.route('/api/pi/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@authenticate_request
def route_pi(path):
    """Route to Profile/Identity service"""
    return proxy_request('pi', f'/api/{path}')

# Direct service health checks
@app.route('/api/<service_name>/health')
def service_health(service_name):
    """Get health of specific service"""
    if service_name not in SERVICE_REGISTRY:
        return jsonify({"error": "Service not found"}), 404
    
    return proxy_request(service_name, '/health')

# Catch-all route for undefined paths
@app.route('/api/<path:path>')
def catch_all(path):
    """Catch-all for undefined API paths"""
    return jsonify({
        "error": "Endpoint not found",
        "path": f"/api/{path}",
        "available_services": list(SERVICE_REGISTRY.keys()),
        "gateway_info": "/gateway/info"
    }), 404

if __name__ == '__main__':
    print("🚀 Starting Enterprise AI System API Gateway...")
    print("📊 Available Services:")
    for name, config in SERVICE_REGISTRY.items():
        print(f"   - {config['name']}: {config['base_url']}")
    print("🔗 Gateway URL: http://localhost:6000")
    print("📈 Analytics: http://localhost:6000/gateway/analytics")
    print("🏥 Health Check: http://localhost:6000/health")
    
    app.run(host='0.0.0.0', port=6000, debug=True)

