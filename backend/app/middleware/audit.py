"""
Audit middleware for the Enterprise AI System.
Logs requests, responses, and user actions for compliance and security.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
import time
import json
from typing import Optional, Dict, Any
import asyncio
from urllib.parse import urlparse, parse_qs

from app.core.config import settings
from app.core.logging import audit_logger, performance_logger

logger = structlog.get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive audit logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Paths to exclude from audit logging
        self.excluded_paths = {
            "/health",
            "/health/detailed",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        # Sensitive headers to redact
        self.sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token"
        }
        
        # Sensitive query parameters to redact
        self.sensitive_params = {
            "password",
            "token",
            "secret",
            "key",
            "api_key"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log audit information."""
        if not settings.AUDIT_ENABLED:
            return await call_next(request)
        
        start_time = time.time()
        
        # Skip audit logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Capture request information
        request_data = await self._capture_request_data(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Capture response information
        response_data = self._capture_response_data(response, response_time_ms)
        
        # Log audit event
        await self._log_audit_event(request, request_data, response_data)
        
        # Log performance metrics
        self._log_performance_metrics(request, response_data, response_time_ms)
        
        return response
    
    async def _capture_request_data(self, request: Request) -> Dict[str, Any]:
        """Capture request data for audit logging."""
        try:
            # Basic request information
            request_data = {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": self._sanitize_query_params(dict(request.query_params)),
                "headers": self._sanitize_headers(dict(request.headers)),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "content_length": request.headers.get("content-length")
            }
            
            # Add user information if available
            if hasattr(request.state, 'user_id'):
                request_data["user_id"] = request.state.user_id
            
            if hasattr(request.state, 'user'):
                request_data["user_email"] = request.state.user.email
            
            # Capture request body for specific endpoints (if enabled)
            if settings.AUDIT_LOG_REQUESTS and self._should_log_request_body(request):
                try:
                    body = await request.body()
                    if body:
                        # Try to parse as JSON
                        try:
                            body_data = json.loads(body.decode('utf-8'))
                            request_data["body"] = self._sanitize_request_body(body_data)
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # Store as base64 for binary data
                            import base64
                            request_data["body"] = {
                                "type": "binary",
                                "size": len(body),
                                "data": base64.b64encode(body[:1024]).decode('utf-8')  # First 1KB only
                            }
                except Exception as e:
                    logger.warning("Failed to capture request body", error=str(e))
            
            return request_data
            
        except Exception as e:
            logger.error("Failed to capture request data", error=str(e))
            return {"error": "Failed to capture request data"}
    
    def _capture_response_data(self, response: Response, response_time_ms: float) -> Dict[str, Any]:
        """Capture response data for audit logging."""
        try:
            response_data = {
                "status_code": response.status_code,
                "headers": self._sanitize_headers(dict(response.headers)),
                "response_time_ms": response_time_ms
            }
            
            # Add content length if available
            content_length = response.headers.get("content-length")
            if content_length:
                response_data["content_length"] = int(content_length)
            
            # Capture response body for specific cases (if enabled)
            if settings.AUDIT_LOG_RESPONSES and self._should_log_response_body(response):
                # Note: Response body capture is complex in ASGI middleware
                # This would require custom response handling
                pass
            
            return response_data
            
        except Exception as e:
            logger.error("Failed to capture response data", error=str(e))
            return {"error": "Failed to capture response data"}
    
    async def _log_audit_event(
        self, 
        request: Request, 
        request_data: Dict[str, Any], 
        response_data: Dict[str, Any]
    ):
        """Log comprehensive audit event."""
        try:
            # Determine event type based on request
            event_type = self._determine_event_type(request)
            
            # Get user context
            user_id = getattr(request.state, 'user_id', None)
            session_id = getattr(request.state, 'session_id', None)
            
            # Log the audit event
            audit_logger.log_user_action(
                user_id=user_id,
                action=f"{request.method} {request.url.path}",
                resource_type=self._extract_resource_type(request.url.path),
                resource_id=self._extract_resource_id(request.url.path),
                details={
                    "request": request_data,
                    "response": response_data,
                    "event_type": event_type
                },
                ip_address=request_data.get("client_ip"),
                user_agent=request_data.get("user_agent"),
                session_id=session_id
            )
            
        except Exception as e:
            logger.error("Failed to log audit event", error=str(e))
    
    def _log_performance_metrics(
        self, 
        request: Request, 
        response_data: Dict[str, Any], 
        response_time_ms: float
    ):
        """Log performance metrics."""
        try:
            user_id = getattr(request.state, 'user_id', None)
            
            performance_logger.log_api_performance(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=response_time_ms,
                status_code=response_data.get("status_code"),
                user_id=user_id,
                request_size=self._get_request_size(request),
                response_size=response_data.get("content_length")
            )
            
        except Exception as e:
            logger.error("Failed to log performance metrics", error=str(e))
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _get_request_size(self, request: Request) -> Optional[int]:
        """Get request size from headers."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass
        return None
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers by redacting sensitive information."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_query_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """Sanitize query parameters by redacting sensitive information."""
        sanitized = {}
        for key, value in params.items():
            if key.lower() in self.sensitive_params:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_request_body(self, body: Any) -> Any:
        """Sanitize request body by redacting sensitive information."""
        if isinstance(body, dict):
            sanitized = {}
            for key, value in body.items():
                if isinstance(key, str) and key.lower() in self.sensitive_params:
                    sanitized[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_request_body(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        self._sanitize_request_body(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(body, list):
            return [
                self._sanitize_request_body(item) if isinstance(item, dict) else item
                for item in body
            ]
        else:
            return body
    
    def _should_log_request_body(self, request: Request) -> bool:
        """Determine if request body should be logged."""
        # Log request body for specific endpoints
        sensitive_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/change-password"
        }
        
        # Don't log body for sensitive endpoints
        if request.url.path in sensitive_endpoints:
            return False
        
        # Log for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            return True
        
        return False
    
    def _should_log_response_body(self, response: Response) -> bool:
        """Determine if response body should be logged."""
        # Only log response body for error responses
        return response.status_code >= 400
    
    def _determine_event_type(self, request: Request) -> str:
        """Determine audit event type based on request."""
        path = request.url.path.lower()
        method = request.method.upper()
        
        if "/auth/" in path:
            if "login" in path:
                return "authentication"
            elif "logout" in path:
                return "authentication"
            elif "register" in path:
                return "user_registration"
            else:
                return "authentication"
        
        if method == "GET":
            return "data_access"
        elif method in ["POST", "PUT", "PATCH"]:
            return "data_modification"
        elif method == "DELETE":
            return "data_deletion"
        else:
            return "api_access"
    
    def _extract_resource_type(self, path: str) -> Optional[str]:
        """Extract resource type from URL path."""
        path_parts = path.strip("/").split("/")
        
        # Skip API version prefix
        if len(path_parts) > 2 and path_parts[0] == "api" and path_parts[1].startswith("v"):
            resource_part = path_parts[2] if len(path_parts) > 2 else None
        else:
            resource_part = path_parts[0] if path_parts else None
        
        # Map common resource types
        resource_mapping = {
            "users": "user",
            "roles": "role",
            "permissions": "permission",
            "conversations": "conversation",
            "messages": "message",
            "documents": "document",
            "analytics": "analytics",
            "audit": "audit"
        }
        
        return resource_mapping.get(resource_part, resource_part)
    
    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from URL path."""
        path_parts = path.strip("/").split("/")
        
        # Look for UUID-like patterns in path
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        for part in path_parts:
            if uuid_pattern.match(part):
                return part
        
        # Look for numeric IDs
        for part in path_parts:
            if part.isdigit():
                return part
        
        return None


# ============================================================================
# AUDIT EVENT HELPERS
# ============================================================================

class AuditEventLogger:
    """Helper class for logging specific audit events."""
    
    @staticmethod
    async def log_login_attempt(
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: str = None
    ):
        """Log login attempt."""
        event_type = "login_success" if success else "login_failure"
        
        audit_logger.log_authentication_event(
            event_type=event_type,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "success": success,
                "failure_reason": failure_reason
            }
        )
    
    @staticmethod
    async def log_permission_check(
        user_id: str,
        permission: str,
        resource_type: str,
        resource_id: str,
        granted: bool,
        reason: str = None
    ):
        """Log permission check result."""
        audit_logger.log_permission_check(
            user_id=user_id,
            permission=permission,
            resource_type=resource_type,
            resource_id=resource_id,
            granted=granted,
            reason=reason
        )
    
    @staticmethod
    async def log_data_access(
        user_id: str,
        operation: str,
        table_name: str,
        record_count: int = None,
        sensitive_data: bool = False
    ):
        """Log data access event."""
        audit_logger.log_data_access(
            user_id=user_id,
            data_type=table_name,
            operation=operation,
            record_count=record_count,
            sensitive_data=sensitive_data
        )
    
    @staticmethod
    async def log_security_event(
        event_type: str,
        severity: str,
        description: str,
        user_id: str = None,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ):
        """Log security event."""
        audit_logger.log_security_event(
            event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            details=details
        )


# Export commonly used items
__all__ = [
    "AuditMiddleware",
    "AuditEventLogger"
]

