"""
Authentication middleware for the Enterprise AI System.
Handles JWT token validation and user context setup.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
from typing import Optional
import time

from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.services.auth import AuthService
from app.services.user import UserService

logger = structlog.get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for JWT token validation."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Paths that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/health/detailed",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/verify-email"
        }
        
        # Path prefixes that don't require authentication
        self.public_prefixes = {
            "/static/",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication."""
        start_time = time.time()
        
        try:
            # Check if path requires authentication
            if self._is_public_path(request.url.path):
                response = await call_next(request)
                return response
            
            # Extract and validate token
            token = self._extract_token(request)
            if not token:
                return self._create_auth_error_response(
                    "Authentication required",
                    request.state.request_id if hasattr(request.state, 'request_id') else None
                )
            
            # Create database session and services
            from app.db.database import get_sync_db
            db = next(get_sync_db())
            auth_service = AuthService(db)
            user_service = UserService(db)
            
            # Validate token and get user
            try:
                payload = await auth_service.verify_access_token(token)
                user_id = payload.get("user_id")
                
                if not user_id:
                    return self._create_auth_error_response(
                        "Invalid token payload",
                        request.state.request_id if hasattr(request.state, 'request_id') else None
                    )
                
                # Get user information
                user = await user_service.get_user_by_id(user_id)
                if not user:
                    return self._create_auth_error_response(
                        "User not found",
                        request.state.request_id if hasattr(request.state, 'request_id') else None
                    )
                
                if not user.is_active:
                    return self._create_auth_error_response(
                        "Account is disabled",
                        request.state.request_id if hasattr(request.state, 'request_id') else None
                    )
                
                # Add user context to request
                request.state.user = user
                request.state.user_id = user_id
                request.state.token_payload = payload
                
                # Update last activity (optional, can be removed for performance)
                # await user_service.update_last_activity(user_id)
                
                logger.debug(
                    "Authentication successful",
                    user_id=user_id,
                    email=user.email,
                    path=request.url.path
                )
                
            except AuthenticationException as e:
                return self._create_auth_error_response(
                    str(e),
                    request.state.request_id if hasattr(request.state, 'request_id') else None
                )
            except Exception as e:
                logger.error(
                    "Authentication error",
                    error=str(e),
                    path=request.url.path,
                    exc_info=True
                )
                return self._create_auth_error_response(
                    "Authentication failed",
                    request.state.request_id if hasattr(request.state, 'request_id') else None
                )
            
            # Process request
            response = await call_next(request)
            
            # Log authentication timing
            auth_time = (time.time() - start_time) * 1000
            logger.debug(
                "Authentication middleware completed",
                auth_time_ms=auth_time,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Authentication middleware error",
                error=str(e),
                path=request.url.path,
                exc_info=True
            )
            return self._create_auth_error_response(
                "Authentication system error",
                request.state.request_id if hasattr(request.state, 'request_id') else None
            )
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public and doesn't require authentication."""
        # Check exact matches
        if path in self.public_paths:
            return True
        
        # Check prefix matches
        for prefix in self.public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        # Check Authorization header
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        
        # Check cookie (fallback)
        token = request.cookies.get("access_token")
        if token:
            return token
        
        return None
    
    def _create_auth_error_response(self, message: str, request_id: Optional[str] = None) -> JSONResponse:
        """Create standardized authentication error response."""
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication Error",
                "message": message,
                "request_id": request_id
            },
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """Optional authentication middleware that sets user context if token is present."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.auth_service = AuthService()
        self.user_service = UserService()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and optionally validate authentication."""
        try:
            # Extract token
            token = self._extract_token(request)
            
            if token:
                try:
                    # Validate token and get user
                    payload = await self.auth_service.verify_access_token(token)
                    user_id = payload.get("sub")
                    
                    if user_id:
                        user = await self.user_service.get_user_by_id(user_id)
                        if user and user.is_active:
                            # Add user context to request
                            request.state.user = user
                            request.state.user_id = user_id
                            request.state.token_payload = payload
                            
                            # Update last activity
                            await self.user_service.update_last_activity(user_id)
                
                except Exception as e:
                    # Log but don't fail the request
                    logger.debug(
                        "Optional authentication failed",
                        error=str(e),
                        path=request.url.path
                    )
            
            # Process request regardless of authentication status
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(
                "Optional auth middleware error",
                error=str(e),
                path=request.url.path,
                exc_info=True
            )
            # Continue without authentication
            response = await call_next(request)
            return response
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        # Check Authorization header
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        
        # Check cookie (fallback)
        token = request.cookies.get("access_token")
        if token:
            return token
        
        return None


# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================

def get_current_user(request: Request):
    """Get current authenticated user from request state."""
    if not hasattr(request.state, 'user'):
        raise AuthenticationException("Authentication required")
    return request.state.user


def get_current_user_id(request: Request) -> str:
    """Get current authenticated user ID from request state."""
    if not hasattr(request.state, 'user_id'):
        raise AuthenticationException("Authentication required")
    return request.state.user_id


def get_optional_current_user(request: Request):
    """Get current user if authenticated, None otherwise."""
    return getattr(request.state, 'user', None)


def get_optional_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID if authenticated, None otherwise."""
    return getattr(request.state, 'user_id', None)


def get_token_payload(request: Request) -> dict:
    """Get JWT token payload from request state."""
    if not hasattr(request.state, 'token_payload'):
        raise AuthenticationException("Authentication required")
    return request.state.token_payload


# Export commonly used items
__all__ = [
    "AuthMiddleware",
    "OptionalAuthMiddleware",
    "get_current_user",
    "get_current_user_id",
    "get_optional_current_user",
    "get_optional_current_user_id",
    "get_token_payload"
]

