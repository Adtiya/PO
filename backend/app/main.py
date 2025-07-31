"""
Enterprise AI System - FastAPI Backend
Main application entry point with comprehensive middleware and routing.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import sync_engine, create_tables
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.audit import AuditMiddleware
from app.api.v1.api import api_router
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    RateLimitException
)

# Setup structured logging
logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Enterprise AI System backend")
    
    # Setup logging
    setup_logging()
    
    # Create database tables
    await create_tables()
    
    logger.info("Backend startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enterprise AI System backend")

# Create FastAPI application
app = FastAPI(
    title="Enterprise AI System API",
    description="Comprehensive enterprise AI platform with dynamic RBAC, analytics, and security features",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS Middleware - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware - Security
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Custom Middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

# Request ID and timing middleware
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Add request ID and timing information to all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Add request ID to response headers
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request completion
    logger.info(
        "Request completed",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Handle validation errors."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "details": exc.details if hasattr(exc, 'details') else None,
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "Authentication Error",
            "message": str(exc),
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    """Handle authorization errors."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "Authorization Error",
            "message": str(exc),
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Handle not found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": str(exc),
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Handle conflict errors."""
    return JSONResponse(
        status_code=409,
        content={
            "error": "Conflict",
            "message": str(exc),
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """Handle rate limit errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate Limit Exceeded",
            "message": str(exc),
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None,
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    request_id = getattr(request.state, 'request_id', None)
    
    logger.error(
        "Unhandled exception",
        request_id=request_id,
        exception=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "enterprise-ai-backend",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with database and external service status."""
    from app.services.health import HealthService
    
    health_service = HealthService()
    health_status = await health_service.get_detailed_health()
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    from app.services.metrics import MetricsService
    
    metrics_service = MetricsService()
    return Response(
        content=metrics_service.generate_metrics(),
        media_type="text/plain"
    )

# ============================================================================
# API ROUTES
# ============================================================================

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Enterprise AI System API",
        "version": "1.0.0",
        "description": "Comprehensive enterprise AI platform with dynamic RBAC",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "health_url": "/health",
        "api_prefix": "/api/v1"
    }

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use our custom logging
        access_log=False  # Disable uvicorn access logs (we handle this)
    )

