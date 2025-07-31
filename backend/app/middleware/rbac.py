"""
RBAC middleware and decorators for the Enterprise AI System.
Provides role-based access control integration with FastAPI.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
from typing import Optional, List, Dict, Any, Callable
from functools import wraps
import asyncio

from app.core.exceptions import AuthorizationException
from app.services.rbac import RBACService, PermissionChecker
from app.middleware.auth import get_current_user_id

logger = structlog.get_logger(__name__)
security = HTTPBearer()


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware for RBAC integration."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rbac_service = RBACService()
    
    async def dispatch(self, request: Request, call_next):
        """Add RBAC services to request state."""
        try:
            # Add RBAC services to request state
            request.state.rbac_service = self.rbac_service
            request.state.permission_checker = PermissionChecker(self.rbac_service)
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(
                "RBAC middleware error",
                error=str(e),
                path=request.url.path,
                exc_info=True
            )
            # Continue without RBAC services
            response = await call_next(request)
            return response


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_rbac_service() -> RBACService:
    """Get RBAC service instance."""
    return RBACService()


async def get_permission_checker(
    rbac_service: RBACService = Depends(get_rbac_service)
) -> PermissionChecker:
    """Get permission checker instance."""
    return PermissionChecker(rbac_service)


# ============================================================================
# AUTHORIZATION DECORATORS
# ============================================================================

def require_permission(
    permission: str,
    resource_type: Optional[str] = None,
    resource_id_param: Optional[str] = None
):
    """
    Decorator to require a specific permission for an endpoint.
    
    Args:
        permission: Name of the required permission
        resource_type: Type of resource (optional)
        resource_id_param: Name of the parameter containing resource ID (optional)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break
            
            if not request or not hasattr(request.state, 'user_id'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission
            permission_checker = getattr(request.state, 'permission_checker', None)
            if not permission_checker:
                permission_checker = PermissionChecker(RBACService())
            
            try:
                await permission_checker.require_permission(
                    request.state.user_id,
                    permission,
                    resource_type,
                    resource_id
                )
            except AuthorizationException as e:
                logger.warning(
                    "Permission denied",
                    user_id=request.state.user_id,
                    permission=permission,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    error=str(e)
                )
                raise HTTPException(status_code=403, detail=str(e))
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(
    permissions: List[str],
    resource_type: Optional[str] = None,
    resource_id_param: Optional[str] = None
):
    """
    Decorator to require any of the specified permissions for an endpoint.
    
    Args:
        permissions: List of permission names (user needs any one)
        resource_type: Type of resource (optional)
        resource_id_param: Name of the parameter containing resource ID (optional)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break
            
            if not request or not hasattr(request.state, 'user_id'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission
            permission_checker = getattr(request.state, 'permission_checker', None)
            if not permission_checker:
                permission_checker = PermissionChecker(RBACService())
            
            try:
                await permission_checker.require_any_permission(
                    request.state.user_id,
                    permissions,
                    resource_type,
                    resource_id
                )
            except AuthorizationException as e:
                logger.warning(
                    "Permission denied",
                    user_id=request.state.user_id,
                    permissions=permissions,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    error=str(e)
                )
                raise HTTPException(status_code=403, detail=str(e))
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_all_permissions(
    permissions: List[str],
    resource_type: Optional[str] = None,
    resource_id_param: Optional[str] = None
):
    """
    Decorator to require all of the specified permissions for an endpoint.
    
    Args:
        permissions: List of permission names (user needs all)
        resource_type: Type of resource (optional)
        resource_id_param: Name of the parameter containing resource ID (optional)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break
            
            if not request or not hasattr(request.state, 'user_id'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Check permission
            permission_checker = getattr(request.state, 'permission_checker', None)
            if not permission_checker:
                permission_checker = PermissionChecker(RBACService())
            
            try:
                await permission_checker.require_all_permissions(
                    request.state.user_id,
                    permissions,
                    resource_type,
                    resource_id
                )
            except AuthorizationException as e:
                logger.warning(
                    "Permission denied",
                    user_id=request.state.user_id,
                    permissions=permissions,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    error=str(e)
                )
                raise HTTPException(status_code=403, detail=str(e))
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator to require a specific role for an endpoint.
    
    Args:
        role_name: Name of the required role
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break
            
            if not request or not hasattr(request.state, 'user_id'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if user has role
            rbac_service = getattr(request.state, 'rbac_service', None)
            if not rbac_service:
                rbac_service = RBACService()
            
            try:
                # Check if user has the required role
                has_role = await _check_user_has_role(
                    rbac_service, request.state.user_id, role_name
                )
                
                if not has_role:
                    raise AuthorizationException(f"Role '{role_name}' required")
                
            except AuthorizationException as e:
                logger.warning(
                    "Role check failed",
                    user_id=request.state.user_id,
                    role=role_name,
                    error=str(e)
                )
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error("Role check error", error=str(e))
                raise HTTPException(status_code=500, detail="Authorization error")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_superuser():
    """Decorator to require superuser privileges."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if hasattr(arg, 'state'):
                    request = arg
                    break
            
            if not request:
                for value in kwargs.values():
                    if hasattr(value, 'state'):
                        request = value
                        break
            
            if not request or not hasattr(request.state, 'user'):
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check if user is superuser
            user = request.state.user
            if not getattr(user, 'is_superuser', False):
                logger.warning(
                    "Superuser access denied",
                    user_id=request.state.user_id
                )
                raise HTTPException(status_code=403, detail="Superuser privileges required")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# PERMISSION DEPENDENCY FUNCTIONS
# ============================================================================

class PermissionDependency:
    """Dependency class for permission checking in FastAPI endpoints."""
    
    def __init__(
        self,
        permission: str,
        resource_type: Optional[str] = None,
        resource_id_param: Optional[str] = None
    ):
        self.permission = permission
        self.resource_type = resource_type
        self.resource_id_param = resource_id_param
    
    async def __call__(
        self,
        request: Request,
        current_user_id: str = Depends(get_current_user_id),
        permission_checker: PermissionChecker = Depends(get_permission_checker)
    ):
        """Check permission as a dependency."""
        # Get resource ID from path parameters if specified
        resource_id = None
        if self.resource_id_param:
            resource_id = request.path_params.get(self.resource_id_param)
        
        try:
            await permission_checker.require_permission(
                current_user_id,
                self.permission,
                self.resource_type,
                resource_id
            )
        except AuthorizationException as e:
            logger.warning(
                "Permission dependency failed",
                user_id=current_user_id,
                permission=self.permission,
                resource_type=self.resource_type,
                resource_id=resource_id,
                error=str(e)
            )
            raise HTTPException(status_code=403, detail=str(e))


class RoleDependency:
    """Dependency class for role checking in FastAPI endpoints."""
    
    def __init__(self, role_name: str):
        self.role_name = role_name
    
    async def __call__(
        self,
        current_user_id: str = Depends(get_current_user_id),
        rbac_service: RBACService = Depends(get_rbac_service)
    ):
        """Check role as a dependency."""
        try:
            has_role = await _check_user_has_role(
                rbac_service, current_user_id, self.role_name
            )
            
            if not has_role:
                raise AuthorizationException(f"Role '{self.role_name}' required")
                
        except AuthorizationException as e:
            logger.warning(
                "Role dependency failed",
                user_id=current_user_id,
                role=self.role_name,
                error=str(e)
            )
            raise HTTPException(status_code=403, detail=str(e))


def RequirePermission(
    permission: str,
    resource_type: Optional[str] = None,
    resource_id_param: Optional[str] = None
):
    """Create a permission dependency for FastAPI endpoints."""
    return Depends(PermissionDependency(permission, resource_type, resource_id_param))


def RequireRole(role_name: str):
    """Create a role dependency for FastAPI endpoints."""
    return Depends(RoleDependency(role_name))


def RequireSuperuser():
    """Create a superuser dependency for FastAPI endpoints."""
    async def check_superuser(request: Request):
        if not hasattr(request.state, 'user'):
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user = request.state.user
        if not getattr(user, 'is_superuser', False):
            raise HTTPException(status_code=403, detail="Superuser privileges required")
    
    return Depends(check_superuser)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def check_permission_in_endpoint(
    request: Request,
    permission: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> bool:
    """Check permission within an endpoint function."""
    if not hasattr(request.state, 'user_id'):
        return False
    
    rbac_service = getattr(request.state, 'rbac_service', None)
    if not rbac_service:
        rbac_service = RBACService()
    
    return await rbac_service.check_permission(
        request.state.user_id,
        permission,
        resource_type,
        resource_id
    )


async def get_user_permissions_in_endpoint(
    request: Request,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> List[str]:
    """Get user permissions within an endpoint function."""
    if not hasattr(request.state, 'user_id'):
        return []
    
    rbac_service = getattr(request.state, 'rbac_service', None)
    if not rbac_service:
        rbac_service = RBACService()
    
    return await rbac_service.get_user_permissions(
        request.state.user_id,
        resource_type,
        resource_id
    )


async def check_user_has_role(
    request: Request,
    role_name: str
) -> bool:
    """Check if user has a specific role."""
    if not hasattr(request.state, 'user_id'):
        return False
    
    rbac_service = getattr(request.state, 'rbac_service', None)
    if not rbac_service:
        rbac_service = RBACService()
    
    return await _check_user_has_role(rbac_service, request.state.user_id, role_name)


async def _check_user_has_role(
    rbac_service: RBACService,
    user_id: str,
    role_name: str
) -> bool:
    """Internal function to check if user has a specific role."""
    try:
        from app.db.database import get_db_session
        from app.models import User, UserRole, Role
        import uuid
        
        async with get_db_session() as session:
            # Get user's active roles
            user_roles = session.query(UserRole).join(Role).filter(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.is_active == True,
                UserRole.is_deleted == False,
                Role.name == role_name.lower(),
                Role.is_active == True,
                Role.is_deleted == False
            ).all()
            
            # Check if any role assignment is valid
            for user_role in user_roles:
                if user_role.is_valid:
                    return True
            
            return False
            
    except Exception as e:
        logger.error(
            "Role check failed",
            user_id=user_id,
            role_name=role_name,
            error=str(e)
        )
        return False


# ============================================================================
# PERMISSION CONTEXT MANAGER
# ============================================================================

class PermissionContext:
    """Context manager for permission checking in complex operations."""
    
    def __init__(
        self,
        rbac_service: RBACService,
        user_id: str,
        permissions: List[str],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        self.rbac_service = rbac_service
        self.user_id = user_id
        self.permissions = permissions
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.granted_permissions = []
    
    async def __aenter__(self):
        """Check permissions on entry."""
        for permission in self.permissions:
            has_permission = await self.rbac_service.check_permission(
                self.user_id,
                permission,
                self.resource_type,
                self.resource_id
            )
            
            if has_permission:
                self.granted_permissions.append(permission)
            else:
                raise AuthorizationException(
                    f"Permission '{permission}' required"
                )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up on exit."""
        # Log permission usage
        logger.debug(
            "Permission context completed",
            user_id=self.user_id,
            permissions=self.granted_permissions,
            resource_type=self.resource_type,
            resource_id=self.resource_id
        )


# Export commonly used items
__all__ = [
    "RBACMiddleware",
    "require_permission",
    "require_any_permission", 
    "require_all_permissions",
    "require_role",
    "require_superuser",
    "RequirePermission",
    "RequireRole",
    "RequireSuperuser",
    "PermissionDependency",
    "RoleDependency",
    "check_permission_in_endpoint",
    "get_user_permissions_in_endpoint",
    "check_user_has_role",
    "PermissionContext",
    "get_rbac_service",
    "get_permission_checker"
]

