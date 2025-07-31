"""
Main API router for the Enterprise AI System.
Aggregates all API endpoints under version 1.
"""

from fastapi import APIRouter, Request

from app.api.v1.endpoints import (
    auth, users, roles, permissions, conversations, 
    documents, analytics, audit, resources,
    temporal_permissions, conditional_permissions
)

api_router = APIRouter()

# Authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# RBAC endpoints
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])

# Advanced RBAC endpoints
api_router.include_router(temporal_permissions.router, prefix="/temporal-permissions", tags=["temporal-permissions"])
api_router.include_router(conditional_permissions.router, prefix="/conditional-permissions", tags=["conditional-permissions"])

# LLM and conversation endpoints
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

# Document management endpoints
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Analytics endpoints
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

# Audit endpoints
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])


@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# API information endpoint
@api_router.get("/", tags=["API Info"])
async def api_info(request: Request):
    """Get API information and available endpoints."""
    return {
        "name": "Enterprise AI System API",
        "version": "1.0.0",
        "description": "Comprehensive enterprise AI platform with dynamic RBAC",
        "environment": settings.ENVIRONMENT,
        "endpoints": {
            "authentication": "/api/v1/auth",
            "users": "/api/v1/users",
            "roles": "/api/v1/roles",
            "permissions": "/api/v1/permissions",
            "conversations": "/api/v1/conversations",
            "documents": "/api/v1/documents",
            "analytics": "/api/v1/analytics",
            "audit": "/api/v1/audit"
        },
        "documentation": {
            "swagger_ui": "/docs" if settings.ENVIRONMENT != "production" else None,
            "redoc": "/redoc" if settings.ENVIRONMENT != "production" else None,
            "openapi_spec": "/openapi.json" if settings.ENVIRONMENT != "production" else None
        },
        "health_check": "/health",
        "metrics": "/metrics"
    }

