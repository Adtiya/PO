"""
Structured logging configuration for the Enterprise AI System.
Uses structlog for consistent, structured logging across the application.
"""

import logging
import logging.config
import sys
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor
import json
from datetime import datetime

from app.core.config import settings


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add timestamp to log events."""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add log level to log events."""
    event_dict["level"] = method_name.upper()
    return event_dict


def add_logger_name(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add logger name to log events."""
    event_dict["logger"] = logger.name
    return event_dict


def add_service_info(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add service information to log events."""
    event_dict["service"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def filter_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Filter sensitive data from log events."""
    sensitive_fields = {
        "password", "token", "secret", "key", "authorization",
        "cookie", "session", "api_key", "access_token", "refresh_token"
    }
    
    def _filter_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively filter sensitive data from dictionaries."""
        filtered = {}
        for key, value in data.items():
            if isinstance(key, str) and any(field in key.lower() for field in sensitive_fields):
                filtered[key] = "[REDACTED]"
            elif isinstance(value, dict):
                filtered[key] = _filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [_filter_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                filtered[key] = value
        return filtered
    
    # Filter the entire event dict
    for key, value in list(event_dict.items()):
        if isinstance(value, dict):
            event_dict[key] = _filter_dict(value)
        elif isinstance(key, str) and any(field in key.lower() for field in sensitive_fields):
            event_dict[key] = "[REDACTED]"
    
    return event_dict


def json_serializer(obj: Any) -> str:
    """Custom JSON serializer for log events."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(obj)


class RequestContextProcessor:
    """Processor to add request context to log events."""
    
    def __call__(self, logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
        """Add request context if available."""
        try:
            from contextvars import copy_context
            context = copy_context()
            
            # Try to get request ID from context
            request_id = context.get("request_id", None)
            if request_id:
                event_dict["request_id"] = request_id
            
            # Try to get user ID from context
            user_id = context.get("user_id", None)
            if user_id:
                event_dict["user_id"] = user_id
                
        except Exception:
            # If context is not available, continue without it
            pass
        
        return event_dict


def setup_logging():
    """Setup structured logging configuration."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Disable some noisy loggers
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").propagate = False
    
    # Configure processors based on log format
    processors: list[Processor] = [
        add_timestamp,
        add_log_level,
        add_logger_name,
        add_service_info,
        RequestContextProcessor(),
        filter_sensitive_data,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if settings.LOG_FORMAT.lower() == "json":
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer(serializer=json_serializer))
    else:
        # Human-readable output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure file logging if specified
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        if settings.LOG_FORMAT.lower() == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        logging.getLogger().addHandler(file_handler)


class LoggerMixin:
    """Mixin class to add structured logging to any class."""
    
    @property
    def logger(self):
        """Get a logger instance for this class."""
        return structlog.get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ):
        """Log user actions for audit purposes."""
        self.logger.info(
            "User action",
            event_type="user_action",
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
    
    def log_authentication_event(
        self,
        event_type: str,  # login, logout, failed_login, etc.
        user_id: str = None,
        email: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict[str, Any] = None
    ):
        """Log authentication events."""
        self.logger.info(
            "Authentication event",
            event_type="authentication",
            auth_event_type=event_type,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
    
    def log_permission_check(
        self,
        user_id: str,
        permission: str,
        resource_type: str = None,
        resource_id: str = None,
        granted: bool = False,
        reason: str = None
    ):
        """Log permission checks."""
        self.logger.info(
            "Permission check",
            event_type="permission_check",
            user_id=user_id,
            permission=permission,
            resource_type=resource_type,
            resource_id=resource_id,
            granted=granted,
            reason=reason
        )
    
    def log_data_access(
        self,
        user_id: str,
        data_type: str,
        operation: str,  # read, write, delete
        record_count: int = None,
        sensitive_data: bool = False,
        details: Dict[str, Any] = None
    ):
        """Log data access events."""
        self.logger.info(
            "Data access",
            event_type="data_access",
            user_id=user_id,
            data_type=data_type,
            operation=operation,
            record_count=record_count,
            sensitive_data=sensitive_data,
            details=details or {}
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,  # low, medium, high, critical
        description: str,
        user_id: str = None,
        ip_address: str = None,
        details: Dict[str, Any] = None
    ):
        """Log security events."""
        self.logger.warning(
            "Security event",
            event_type="security",
            security_event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {}
        )


# ============================================================================
# PERFORMANCE LOGGING
# ============================================================================

class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_api_performance(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        user_id: str = None,
        request_size: int = None,
        response_size: int = None
    ):
        """Log API performance metrics."""
        self.logger.info(
            "API performance",
            event_type="api_performance",
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            user_id=user_id,
            request_size=request_size,
            response_size=response_size
        )
    
    def log_database_performance(
        self,
        operation: str,
        table: str,
        execution_time_ms: float,
        rows_affected: int = None,
        query_type: str = None
    ):
        """Log database performance metrics."""
        self.logger.info(
            "Database performance",
            event_type="database_performance",
            operation=operation,
            table=table,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            query_type=query_type
        )
    
    def log_llm_performance(
        self,
        model_name: str,
        operation_type: str,
        response_time_ms: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float = None
    ):
        """Log LLM performance metrics."""
        self.logger.info(
            "LLM performance",
            event_type="llm_performance",
            model_name=model_name,
            operation_type=operation_type,
            response_time_ms=response_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost
        )


# Create global logger instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()

# Export commonly used items
__all__ = [
    "setup_logging",
    "get_logger",
    "LoggerMixin",
    "AuditLogger",
    "PerformanceLogger",
    "audit_logger",
    "performance_logger"
]

