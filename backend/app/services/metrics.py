"""
Metrics service for the Enterprise AI System.
Provides Prometheus-compatible metrics for monitoring and alerting.
"""

import time
from typing import Dict, Any, Optional
import structlog
from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    CollectorRegistry, generate_latest,
    CONTENT_TYPE_LATEST
)

from app.core.config import settings

logger = structlog.get_logger(__name__)


class MetricsService:
    """Service for collecting and exposing application metrics."""
    
    def __init__(self):
        # Create custom registry to avoid conflicts
        self.registry = CollectorRegistry()
        
        # Initialize metrics
        self._init_http_metrics()
        self._init_database_metrics()
        self._init_auth_metrics()
        self._init_llm_metrics()
        self._init_business_metrics()
        self._init_system_metrics()
    
    def _init_http_metrics(self):
        """Initialize HTTP-related metrics."""
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.http_request_size = Histogram(
            'http_request_size_bytes',
            'HTTP request size in bytes',
            ['method', 'endpoint'],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )
        
        self.http_response_size = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint'],
            buckets=[100, 1000, 10000, 100000, 1000000],
            registry=self.registry
        )
    
    def _init_database_metrics(self):
        """Initialize database-related metrics."""
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.db_connections_total = Counter(
            'db_connections_total',
            'Total number of database connections created',
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )
        
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total number of database queries',
            ['operation', 'table', 'status'],
            registry=self.registry
        )
    
    def _init_auth_metrics(self):
        """Initialize authentication-related metrics."""
        self.auth_attempts_total = Counter(
            'auth_attempts_total',
            'Total number of authentication attempts',
            ['type', 'status'],
            registry=self.registry
        )
        
        self.auth_sessions_active = Gauge(
            'auth_sessions_active',
            'Number of active authentication sessions',
            registry=self.registry
        )
        
        self.auth_token_validations = Counter(
            'auth_token_validations_total',
            'Total number of token validations',
            ['status'],
            registry=self.registry
        )
        
        self.password_reset_requests = Counter(
            'password_reset_requests_total',
            'Total number of password reset requests',
            registry=self.registry
        )
    
    def _init_llm_metrics(self):
        """Initialize LLM-related metrics."""
        self.llm_requests_total = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['model', 'status'],
            registry=self.registry
        )
        
        self.llm_request_duration = Histogram(
            'llm_request_duration_seconds',
            'LLM request duration in seconds',
            ['model'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
            registry=self.registry
        )
        
        self.llm_tokens_used = Counter(
            'llm_tokens_used_total',
            'Total number of LLM tokens used',
            ['model', 'type'],
            registry=self.registry
        )
        
        self.llm_cost_total = Counter(
            'llm_cost_total',
            'Total LLM cost in USD',
            ['model'],
            registry=self.registry
        )
        
        self.llm_conversations_active = Gauge(
            'llm_conversations_active',
            'Number of active LLM conversations',
            registry=self.registry
        )
    
    def _init_business_metrics(self):
        """Initialize business-related metrics."""
        self.users_total = Gauge(
            'users_total',
            'Total number of users',
            ['status'],
            registry=self.registry
        )
        
        self.user_registrations = Counter(
            'user_registrations_total',
            'Total number of user registrations',
            ['source'],
            registry=self.registry
        )
        
        self.documents_processed = Counter(
            'documents_processed_total',
            'Total number of documents processed',
            ['type', 'status'],
            registry=self.registry
        )
        
        self.api_usage_by_user = Counter(
            'api_usage_by_user_total',
            'API usage by user',
            ['user_id', 'endpoint'],
            registry=self.registry
        )
    
    def _init_system_metrics(self):
        """Initialize system-related metrics."""
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        self.app_info.info({
            'version': settings.APP_VERSION,
            'environment': settings.ENVIRONMENT,
            'name': settings.APP_NAME
        })
        
        self.app_start_time = Gauge(
            'app_start_time_seconds',
            'Application start time in seconds since epoch',
            registry=self.registry
        )
        
        self.app_start_time.set_to_current_time()
        
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total number of rate limit hits',
            ['category', 'client_type'],
            registry=self.registry
        )
        
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total number of cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
    
    # ============================================================================
    # METRIC RECORDING METHODS
    # ============================================================================
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Record HTTP request metrics."""
        try:
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration_seconds)
            
            if request_size is not None:
                self.http_request_size.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request_size)
            
            if response_size is not None:
                self.http_response_size.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response_size)
                
        except Exception as e:
            logger.error("Failed to record HTTP metrics", error=str(e))
    
    def record_database_query(
        self,
        operation: str,
        table: str,
        duration_seconds: float,
        status: str = "success"
    ):
        """Record database query metrics."""
        try:
            self.db_queries_total.labels(
                operation=operation,
                table=table,
                status=status
            ).inc()
            
            self.db_query_duration.labels(
                operation=operation,
                table=table
            ).observe(duration_seconds)
            
        except Exception as e:
            logger.error("Failed to record database metrics", error=str(e))
    
    def record_auth_attempt(self, auth_type: str, status: str):
        """Record authentication attempt."""
        try:
            self.auth_attempts_total.labels(
                type=auth_type,
                status=status
            ).inc()
            
        except Exception as e:
            logger.error("Failed to record auth metrics", error=str(e))
    
    def record_llm_request(
        self,
        model: str,
        duration_seconds: float,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        status: str = "success"
    ):
        """Record LLM request metrics."""
        try:
            self.llm_requests_total.labels(
                model=model,
                status=status
            ).inc()
            
            self.llm_request_duration.labels(model=model).observe(duration_seconds)
            
            self.llm_tokens_used.labels(
                model=model,
                type="prompt"
            ).inc(prompt_tokens)
            
            self.llm_tokens_used.labels(
                model=model,
                type="completion"
            ).inc(completion_tokens)
            
            self.llm_cost_total.labels(model=model).inc(cost)
            
        except Exception as e:
            logger.error("Failed to record LLM metrics", error=str(e))
    
    def record_user_registration(self, source: str = "web"):
        """Record user registration."""
        try:
            self.user_registrations.labels(source=source).inc()
        except Exception as e:
            logger.error("Failed to record user registration metrics", error=str(e))
    
    def record_document_processing(self, doc_type: str, status: str):
        """Record document processing."""
        try:
            self.documents_processed.labels(
                type=doc_type,
                status=status
            ).inc()
        except Exception as e:
            logger.error("Failed to record document processing metrics", error=str(e))
    
    def record_rate_limit_hit(self, category: str, client_type: str):
        """Record rate limit hit."""
        try:
            self.rate_limit_hits.labels(
                category=category,
                client_type=client_type
            ).inc()
        except Exception as e:
            logger.error("Failed to record rate limit metrics", error=str(e))
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation."""
        try:
            self.cache_operations.labels(
                operation=operation,
                status=status
            ).inc()
        except Exception as e:
            logger.error("Failed to record cache metrics", error=str(e))
    
    # ============================================================================
    # GAUGE UPDATES
    # ============================================================================
    
    def update_active_connections(self, count: int):
        """Update active database connections gauge."""
        try:
            self.db_connections_active.set(count)
        except Exception as e:
            logger.error("Failed to update connection metrics", error=str(e))
    
    def update_active_sessions(self, count: int):
        """Update active sessions gauge."""
        try:
            self.auth_sessions_active.set(count)
        except Exception as e:
            logger.error("Failed to update session metrics", error=str(e))
    
    def update_active_conversations(self, count: int):
        """Update active conversations gauge."""
        try:
            self.llm_conversations_active.set(count)
        except Exception as e:
            logger.error("Failed to update conversation metrics", error=str(e))
    
    def update_user_counts(self, active_users: int, total_users: int):
        """Update user count gauges."""
        try:
            self.users_total.labels(status="active").set(active_users)
            self.users_total.labels(status="total").set(total_users)
        except Exception as e:
            logger.error("Failed to update user metrics", error=str(e))
    
    # ============================================================================
    # METRICS EXPORT
    # ============================================================================
    
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics output."""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error("Failed to generate metrics", error=str(e))
            return ""
    
    def get_content_type(self) -> str:
        """Get content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# ============================================================================
# METRICS DECORATORS
# ============================================================================

def track_time(metric_name: str, labels: Dict[str, str] = None):
    """Decorator to track execution time of functions."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                # Record metric (would need access to metrics service)
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Record error metric
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                # Record metric
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Record error metric
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ============================================================================
# GLOBAL METRICS INSTANCE
# ============================================================================

# Create global metrics service instance
metrics_service = MetricsService()

# Export commonly used items
__all__ = [
    "MetricsService",
    "metrics_service",
    "track_time"
]

