"""
Comprehensive Monitoring and Health Check System
Enterprise-grade monitoring, logging, and health checks
"""

import os
import time
import psutil
import logging
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import uuid

class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class LogLevel(str, Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    response_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    request_count: int
    error_count: int
    avg_response_time: float
    uptime_seconds: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class StructuredLogger:
    """Structured logging with correlation IDs"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.correlation_id = None
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger(service_name)
        
        # Set log level
        logging.basicConfig(level=getattr(logging, log_level.upper()))
    
    def set_correlation_id(self, correlation_id: str = None):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id or str(uuid.uuid4())
        return self.correlation_id
    
    def _get_context(self, **kwargs):
        """Get logging context with correlation ID"""
        context = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        if self.correlation_id:
            context["correlation_id"] = self.correlation_id
        return context
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **self._get_context(**kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **self._get_context(**kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **self._get_context(**kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **self._get_context(**kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **self._get_context(**kwargs))

class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.logger = StructuredLogger(f"{service_name}-health")
    
    def check_system_resources(self) -> HealthCheck:
        """Check system resource usage"""
        try:
            start_time = time.time()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 85:
                status = HealthStatus.DEGRADED
                issues.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High disk usage: {disk.percent}%")
            
            response_time = (time.time() - start_time) * 1000
            
            message = "System resources healthy" if status == HealthStatus.HEALTHY else f"Issues: {', '.join(issues)}"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check system resources: {str(e)}",
                response_time_ms=0.0
            )
    
    def check_database_connection(self, db_connection=None) -> HealthCheck:
        """Check database connectivity"""
        try:
            start_time = time.time()
            
            if db_connection is None:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNKNOWN,
                    message="Database connection not provided",
                    response_time_ms=0.0
                )
            
            # Try a simple query
            if hasattr(db_connection, 'execute'):
                result = db_connection.execute('SELECT 1')
                result.fetchone()
            elif hasattr(db_connection, 'session'):
                db_connection.session.execute('SELECT 1')
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                details={"connection_type": type(db_connection).__name__},
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time
            )
    
    def check_external_service(self, service_url: str, timeout: int = 5) -> HealthCheck:
        """Check external service connectivity"""
        try:
            import requests
            start_time = time.time()
            
            response = requests.get(service_url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = "External service healthy"
            elif response.status_code < 500:
                status = HealthStatus.DEGRADED
                message = f"External service returned {response.status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"External service error: {response.status_code}"
            
            return HealthCheck(
                name=f"external_service_{service_url}",
                status=status,
                message=message,
                details={"status_code": response.status_code, "url": service_url},
                response_time_ms=response_time
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                name=f"external_service_{service_url}",
                status=HealthStatus.UNHEALTHY,
                message=f"External service check failed: {str(e)}",
                details={"url": service_url},
                response_time_ms=response_time
            )
    
    def get_service_metrics(self) -> ServiceMetrics:
        """Get comprehensive service metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Service metrics
            uptime = time.time() - self.start_time
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
            
            return ServiceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                request_count=self.request_count,
                error_count=self.error_count,
                avg_response_time=avg_response_time,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            self.logger.error("Failed to get service metrics", error=str(e))
            return ServiceMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                request_count=self.request_count,
                error_count=self.error_count,
                avg_response_time=0.0,
                uptime_seconds=time.time() - self.start_time
            )
    
    def record_request(self, response_time_ms: float, is_error: bool = False):
        """Record request metrics"""
        self.request_count += 1
        if is_error:
            self.error_count += 1
        
        self.response_times.append(response_time_ms)
        
        # Keep only last 1000 response times for memory efficiency
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def comprehensive_health_check(self, db_connection=None, external_services=None) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = []
        
        # System resources check
        checks.append(self.check_system_resources())
        
        # Database check
        if db_connection:
            checks.append(self.check_database_connection(db_connection))
        
        # External services check
        if external_services:
            for service_url in external_services:
                checks.append(self.check_external_service(service_url))
        
        # Determine overall status
        statuses = [check.status for check in checks]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get metrics
        metrics = self.get_service_metrics()
        
        return {
            "service": self.service_name,
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "response_time_ms": check.response_time_ms
                }
                for check in checks
            ],
            "metrics": {
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "disk_usage": metrics.disk_usage,
                "request_count": metrics.request_count,
                "error_count": metrics.error_count,
                "error_rate": (metrics.error_count / metrics.request_count * 100) if metrics.request_count > 0 else 0.0,
                "avg_response_time_ms": metrics.avg_response_time,
                "uptime_seconds": metrics.uptime_seconds
            }
        }

# Flask middleware for request tracking
def create_monitoring_middleware(health_checker: HealthChecker, logger: StructuredLogger):
    """Create Flask middleware for request monitoring"""
    
    def monitoring_middleware(app):
        @app.before_request
        def before_request():
            from flask import request, g
            g.start_time = time.time()
            g.correlation_id = logger.set_correlation_id()
            logger.info("Request started", 
                       method=request.method, 
                       path=request.path,
                       remote_addr=request.remote_addr)
        
        @app.after_request
        def after_request(response):
            from flask import g
            if hasattr(g, 'start_time'):
                response_time = (time.time() - g.start_time) * 1000
                is_error = response.status_code >= 400
                
                health_checker.record_request(response_time, is_error)
                
                logger.info("Request completed",
                           status_code=response.status_code,
                           response_time_ms=response_time,
                           is_error=is_error)
            
            return response
        
        return app
    
    return monitoring_middleware

# Utility functions
def setup_monitoring(app, service_name: str, db_connection=None, external_services=None):
    """Setup comprehensive monitoring for Flask app"""
    
    # Initialize components
    health_checker = HealthChecker(service_name)
    logger = StructuredLogger(service_name)
    
    # Apply middleware
    monitoring_middleware = create_monitoring_middleware(health_checker, logger)
    monitoring_middleware(app)
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        from flask import jsonify
        health_data = health_checker.comprehensive_health_check(
            db_connection=db_connection,
            external_services=external_services
        )
        
        status_code = 200
        if health_data['status'] == HealthStatus.UNHEALTHY.value:
            status_code = 503
        elif health_data['status'] == HealthStatus.DEGRADED.value:
            status_code = 200  # Still serving requests
        
        return jsonify(health_data), status_code
    
    # Add metrics endpoint
    @app.route('/metrics')
    def metrics():
        from flask import jsonify
        metrics_data = health_checker.get_service_metrics()
        return jsonify({
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "cpu_usage": metrics_data.cpu_usage,
                "memory_usage": metrics_data.memory_usage,
                "disk_usage": metrics_data.disk_usage,
                "request_count": metrics_data.request_count,
                "error_count": metrics_data.error_count,
                "error_rate": (metrics_data.error_count / metrics_data.request_count * 100) if metrics_data.request_count > 0 else 0.0,
                "avg_response_time_ms": metrics_data.avg_response_time,
                "uptime_seconds": metrics_data.uptime_seconds
            }
        })
    
    return health_checker, logger

