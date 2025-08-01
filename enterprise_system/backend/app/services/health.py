"""
Health check service for the Enterprise AI System.
Provides comprehensive health monitoring for all system components.
"""

import asyncio
import time
from typing import Dict, Any, List
import structlog
import httpx
from datetime import datetime

from app.core.config import settings
from app.db.database import database_health_check
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class HealthService:
    """Service for comprehensive health monitoring."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.start_time = time.time()
    
    async def get_basic_health(self) -> Dict[str, Any]:
        """Get basic health status."""
        return {
            "status": "healthy",
            "service": "enterprise-ai-backend",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - self.start_time)
        }
    
    async def get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health status including all dependencies."""
        health_status = {
            "status": "healthy",
            "service": "enterprise-ai-backend",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - self.start_time),
            "checks": {}
        }
        
        # Run all health checks concurrently
        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_external_services(),
            self._check_system_resources(),
            return_exceptions=True
        )
        
        # Process check results
        check_names = ["database", "redis", "external_services", "system_resources"]
        overall_healthy = True
        
        for i, check_result in enumerate(checks):
            check_name = check_names[i]
            
            if isinstance(check_result, Exception):
                health_status["checks"][check_name] = {
                    "status": "unhealthy",
                    "error": str(check_result)
                }
                overall_healthy = False
            else:
                health_status["checks"][check_name] = check_result
                if check_result.get("status") != "healthy":
                    overall_healthy = False
        
        # Set overall status
        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        
        return health_status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            db_health = await database_health_check()
            check_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy" if db_health["database"] == "healthy" else "unhealthy",
                "response_time_ms": check_time,
                "details": db_health["details"]
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test basic Redis operations
            test_key = "health_check_test"
            test_value = str(int(time.time()))
            
            await self.redis_service.set(test_key, test_value, ex=60)
            retrieved_value = await self.redis_service.get(test_key)
            await self.redis_service.delete(test_key)
            
            check_time = (time.time() - start_time) * 1000
            
            if retrieved_value == test_value:
                # Get Redis info
                redis_info = await self.redis_service.info()
                
                return {
                    "status": "healthy",
                    "response_time_ms": check_time,
                    "details": {
                        "version": redis_info.get("redis_version"),
                        "connected_clients": redis_info.get("connected_clients"),
                        "used_memory": redis_info.get("used_memory_human"),
                        "uptime_seconds": redis_info.get("uptime_in_seconds")
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis read/write test failed"
                }
                
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity."""
        external_checks = {}
        overall_status = "healthy"
        
        # Check OpenAI API if configured
        if settings.OPENAI_API_KEY:
            try:
                openai_status = await self._check_openai_api()
                external_checks["openai"] = openai_status
                if openai_status["status"] != "healthy":
                    overall_status = "degraded"
            except Exception as e:
                external_checks["openai"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "degraded"
        
        # Check other external services from config
        for service_url in settings.EXTERNAL_SERVICES:
            try:
                service_name = self._extract_service_name(service_url)
                service_status = await self._check_http_service(service_url)
                external_checks[service_name] = service_status
                if service_status["status"] != "healthy":
                    overall_status = "degraded"
            except Exception as e:
                service_name = self._extract_service_name(service_url)
                external_checks[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = "degraded"
        
        return {
            "status": overall_status,
            "services": external_checks
        }
    
    async def _check_openai_api(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity."""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=settings.HEALTH_CHECK_TIMEOUT) as client:
                response = await client.get(
                    f"{settings.OPENAI_API_BASE}/models",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                )
            
            check_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": check_time
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": check_time
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_http_service(self, url: str) -> Dict[str, Any]:
        """Check HTTP service connectivity."""
        try:
            start_time = time.time()
            
            async with httpx.AsyncClient(timeout=settings.HEALTH_CHECK_TIMEOUT) as client:
                response = await client.get(url)
            
            check_time = (time.time() - start_time) * 1000
            
            if response.status_code < 400:
                return {
                    "status": "healthy",
                    "response_time_ms": check_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": check_time
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            import psutil
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                status = "degraded"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 80:
                status = "degraded"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 80:
                status = "degraded"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                "status": status,
                "warnings": warnings,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            }
            
        except ImportError:
            # psutil not available
            return {
                "status": "unknown",
                "error": "System monitoring not available (psutil not installed)"
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    def _extract_service_name(self, url: str) -> str:
        """Extract service name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.split('.')[0] if parsed.netloc else "unknown"
        except Exception:
            return "unknown"
    
    async def get_readiness_check(self) -> Dict[str, Any]:
        """Check if service is ready to accept traffic."""
        try:
            # Check critical dependencies
            db_check = await self._check_database()
            redis_check = await self._check_redis()
            
            ready = (
                db_check.get("status") == "healthy" and
                redis_check.get("status") == "healthy"
            )
            
            return {
                "ready": ready,
                "checks": {
                    "database": db_check,
                    "redis": redis_check
                }
            }
            
        except Exception as e:
            logger.error("Readiness check failed", error=str(e))
            return {
                "ready": False,
                "error": str(e)
            }
    
    async def get_liveness_check(self) -> Dict[str, Any]:
        """Check if service is alive and responding."""
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": int(time.time() - self.start_time)
        }


# ============================================================================
# HEALTH CHECK UTILITIES
# ============================================================================

class HealthCheckRegistry:
    """Registry for custom health checks."""
    
    def __init__(self):
        self._checks = {}
    
    def register(self, name: str, check_func: callable):
        """Register a custom health check."""
        self._checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        
        for name, check_func in self._checks.items():
            try:
                result = await check_func()
                results[name] = result
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return results


# Global health check registry
health_registry = HealthCheckRegistry()

# Export commonly used items
__all__ = [
    "HealthService",
    "HealthCheckRegistry",
    "health_registry"
]

