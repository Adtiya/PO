"""
RBAC service for the Enterprise AI System.
Provides comprehensive role-based access control with dynamic permissions,
resource-based authorization, and policy evaluation.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set, Tuple
import structlog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_

from app.db.database import get_db_session
from app.models import (
    User, Role, Permission, UserRole, RolePermission, RoleHierarchy,
    Resource, ResourcePermission, UserResourcePermission,
    PermissionCondition, TemporalPermission
)
from app.core.exceptions import AuthorizationException, ValidationException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class RBACService:
    """Service for role-based access control operations."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.cache_ttl = 300  # 5 minutes
    
    # ============================================================================
    # PERMISSION CHECKING
    # ============================================================================
    
    async def check_permission(
        self,
        user_id: str,
        permission_name: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: ID of the user
            permission_name: Name of the permission to check
            resource_type: Type of resource (optional)
            resource_id: ID of the resource (optional)
            context: Additional context for permission evaluation
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Check cache first
            cache_key = self._get_permission_cache_key(
                user_id, permission_name, resource_type, resource_id
            )
            cached_result = await self.redis_service.get(cache_key)
            if cached_result is not None:
                return cached_result == "true"
            
            # Get database session
            async with get_db_session() as session:
                result = await self._check_permission_db(
                    session, user_id, permission_name, resource_type, resource_id, context
                )
                
                # Cache result
                await self.redis_service.set(
                    cache_key, 
                    "true" if result else "false", 
                    ex=self.cache_ttl
                )
                
                return result
                
        except Exception as e:
            logger.error(
                "Permission check failed",
                user_id=user_id,
                permission=permission_name,
                resource_type=resource_type,
                resource_id=resource_id,
                error=str(e)
            )
            return False
    
    async def _check_permission_db(
        self,
        session: Session,
        user_id: str,
        permission_name: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check permission against database."""
        user_uuid = uuid.UUID(user_id)
        context = context or {}
        
        # Get user
        user = session.query(User).filter(
            User.id == user_uuid,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if not user:
            return False
        
        # Check superuser
        if user.is_superuser:
            return True
        
        # Get permission
        permission = session.query(Permission).filter(
            Permission.name == permission_name,
            Permission.is_active == True,
            Permission.is_deleted == False
        ).first()
        
        if not permission:
            return False
        
        # Check direct user-resource permissions
        if resource_type and resource_id:
            if await self._check_user_resource_permission(
                session, user_uuid, permission.id, resource_type, resource_id, context
            ):
                return True
        
        # Check role-based permissions
        if await self._check_role_based_permission(
            session, user_uuid, permission.id, resource_type, resource_id, context
        ):
            return True
        
        return False
    
    async def _check_user_resource_permission(
        self,
        session: Session,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        resource_type: str,
        resource_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check direct user-resource permissions."""
        # Get resource
        resource = session.query(Resource).filter(
            Resource.resource_type == resource_type,
            Resource.resource_id == resource_id,
            Resource.is_active == True,
            Resource.is_deleted == False
        ).first()
        
        if not resource:
            return False
        
        # Check direct permission
        user_permission = session.query(UserResourcePermission).filter(
            UserResourcePermission.user_id == user_id,
            UserResourcePermission.resource_id == resource.id,
            UserResourcePermission.permission_id == permission_id,
            UserResourcePermission.is_active == True,
            UserResourcePermission.is_deleted == False
        ).first()
        
        if user_permission and user_permission.is_valid:
            # Check conditions
            if await self._evaluate_permission_conditions(
                session, user_permission, context
            ):
                return True
        
        # Check inherited permissions from parent resources
        return await self._check_inherited_resource_permission(
            session, user_id, permission_id, resource, context
        )
    
    async def _check_inherited_resource_permission(
        self,
        session: Session,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        resource: Resource,
        context: Dict[str, Any]
    ) -> bool:
        """Check inherited permissions from parent resources."""
        if not resource.parent_resource_id:
            return False
        
        parent_resource = session.query(Resource).get(resource.parent_resource_id)
        if not parent_resource:
            return False
        
        # Check if permission is inheritable
        resource_permission = session.query(ResourcePermission).filter(
            ResourcePermission.resource_id == parent_resource.id,
            ResourcePermission.permission_id == permission_id,
            ResourcePermission.is_inheritable == True,
            ResourcePermission.is_active == True,
            ResourcePermission.is_deleted == False
        ).first()
        
        if not resource_permission:
            return False
        
        # Check user permission on parent resource
        user_permission = session.query(UserResourcePermission).filter(
            UserResourcePermission.user_id == user_id,
            UserResourcePermission.resource_id == parent_resource.id,
            UserResourcePermission.permission_id == permission_id,
            UserResourcePermission.is_active == True,
            UserResourcePermission.is_deleted == False
        ).first()
        
        if user_permission and user_permission.is_valid:
            if await self._evaluate_permission_conditions(
                session, user_permission, context
            ):
                return True
        
        # Recursively check parent's parent
        return await self._check_inherited_resource_permission(
            session, user_id, permission_id, parent_resource, context
        )
    
    async def _check_role_based_permission(
        self,
        session: Session,
        user_id: uuid.UUID,
        permission_id: uuid.UUID,
        resource_type: Optional[str],
        resource_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Check role-based permissions."""
        # Get user's active roles
        user_roles = session.query(UserRole).options(
            joinedload(UserRole.role)
        ).filter(
            UserRole.user_id == user_id,
            UserRole.is_active == True,
            UserRole.is_deleted == False
        ).all()
        
        valid_roles = [
            ur.role for ur in user_roles 
            if ur.is_valid and ur.role.is_active and not ur.role.is_deleted
        ]
        
        if not valid_roles:
            return False
        
        # Check each role for the permission
        for role in valid_roles:
            if await self._check_role_permission(
                session, role, permission_id, resource_type, resource_id, context
            ):
                return True
        
        return False
    
    async def _check_role_permission(
        self,
        session: Session,
        role: Role,
        permission_id: uuid.UUID,
        resource_type: Optional[str],
        resource_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Check if role has specific permission."""
        # Check direct role permission
        role_permission = session.query(RolePermission).filter(
            RolePermission.role_id == role.id,
            RolePermission.permission_id == permission_id,
            RolePermission.is_active == True,
            RolePermission.is_deleted == False
        ).first()
        
        if role_permission and role_permission.is_valid:
            # Check conditions
            if await self._evaluate_role_permission_conditions(
                session, role_permission, context
            ):
                return True
        
        # Check inherited permissions from parent roles
        return await self._check_inherited_role_permission(
            session, role, permission_id, resource_type, resource_id, context
        )
    
    async def _check_inherited_role_permission(
        self,
        session: Session,
        role: Role,
        permission_id: uuid.UUID,
        resource_type: Optional[str],
        resource_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """Check inherited permissions from parent roles."""
        if not role.parent_role_id:
            return False
        
        parent_role = session.query(Role).get(role.parent_role_id)
        if not parent_role or not parent_role.is_active or parent_role.is_deleted:
            return False
        
        return await self._check_role_permission(
            session, parent_role, permission_id, resource_type, resource_id, context
        )
    
    # ============================================================================
    # CONDITION EVALUATION
    # ============================================================================
    
    async def _evaluate_permission_conditions(
        self,
        session: Session,
        user_permission: UserResourcePermission,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate conditions for user resource permission."""
        # Check temporal constraints
        if not await self._check_temporal_constraints(
            session, user_resource_permission_id=user_permission.id
        ):
            return False
        
        # Check custom conditions
        conditions = session.query(PermissionCondition).filter(
            PermissionCondition.user_resource_permission_id == user_permission.id,
            PermissionCondition.is_active == True,
            PermissionCondition.is_deleted == False
        ).all()
        
        for condition in conditions:
            if not await self._evaluate_condition(condition, context):
                return False
        
        return True
    
    async def _evaluate_role_permission_conditions(
        self,
        session: Session,
        role_permission: RolePermission,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate conditions for role permission."""
        # Check temporal constraints
        if not await self._check_temporal_constraints(
            session, role_permission_id=role_permission.id
        ):
            return False
        
        # Check custom conditions
        conditions = session.query(PermissionCondition).filter(
            PermissionCondition.role_permission_id == role_permission.id,
            PermissionCondition.is_active == True,
            PermissionCondition.is_deleted == False
        ).all()
        
        for condition in conditions:
            if not await self._evaluate_condition(condition, context):
                return False
        
        return True
    
    async def _check_temporal_constraints(
        self,
        session: Session,
        user_resource_permission_id: Optional[uuid.UUID] = None,
        role_permission_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check temporal constraints for permission."""
        query = session.query(TemporalPermission).filter(
            TemporalPermission.is_active == True,
            TemporalPermission.is_deleted == False
        )
        
        if user_resource_permission_id:
            query = query.filter(
                TemporalPermission.user_resource_permission_id == user_resource_permission_id
            )
        elif role_permission_id:
            query = query.filter(
                TemporalPermission.role_permission_id == role_permission_id
            )
        else:
            return True
        
        temporal_permissions = query.all()
        
        if not temporal_permissions:
            return True
        
        current_time = datetime.utcnow()
        
        for temporal_permission in temporal_permissions:
            if temporal_permission.is_active_at(current_time):
                return True
        
        return False
    
    async def _evaluate_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a specific permission condition."""
        try:
            if condition.condition_type == 'time_based':
                return await self._evaluate_time_condition(condition, context)
            elif condition.condition_type == 'location_based':
                return await self._evaluate_location_condition(condition, context)
            elif condition.condition_type == 'attribute_based':
                return await self._evaluate_attribute_condition(condition, context)
            elif condition.condition_type == 'approval_based':
                return await self._evaluate_approval_condition(condition, context)
            elif condition.condition_type == 'quota_based':
                return await self._evaluate_quota_condition(condition, context)
            elif condition.condition_type == 'custom':
                return await self._evaluate_custom_condition(condition, context)
            else:
                logger.warning(
                    "Unknown condition type",
                    condition_type=condition.condition_type,
                    condition_id=str(condition.id)
                )
                return False
                
        except Exception as e:
            logger.error(
                "Condition evaluation failed",
                condition_id=str(condition.id),
                condition_type=condition.condition_type,
                error=str(e)
            )
            return False
    
    async def _evaluate_time_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate time-based condition."""
        # Implementation would check current time against condition parameters
        return True  # Placeholder
    
    async def _evaluate_location_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate location-based condition."""
        # Implementation would check user location against allowed locations
        return True  # Placeholder
    
    async def _evaluate_attribute_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate attribute-based condition."""
        # Implementation would check user/resource attributes
        return True  # Placeholder
    
    async def _evaluate_approval_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate approval-based condition."""
        # Implementation would check if required approvals are in place
        return True  # Placeholder
    
    async def _evaluate_quota_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate quota-based condition."""
        # Implementation would check usage quotas
        return True  # Placeholder
    
    async def _evaluate_custom_condition(
        self,
        condition: PermissionCondition,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate custom condition using expression evaluation."""
        # Implementation would evaluate custom expressions
        return True  # Placeholder
    
    # ============================================================================
    # BULK PERMISSION CHECKING
    # ============================================================================
    
    async def check_multiple_permissions(
        self,
        user_id: str,
        permissions: List[str],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """Check multiple permissions for a user."""
        results = {}
        
        for permission in permissions:
            results[permission] = await self.check_permission(
                user_id, permission, resource_type, resource_id, context
            )
        
        return results
    
    async def get_user_permissions(
        self,
        user_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> List[str]:
        """Get all permissions for a user."""
        try:
            async with get_db_session() as session:
                user_uuid = uuid.UUID(user_id)
                
                # Get user
                user = session.query(User).filter(
                    User.id == user_uuid,
                    User.is_active == True,
                    User.is_deleted == False
                ).first()
                
                if not user:
                    return []
                
                permissions = set()
                
                # Get permissions from roles
                user_roles = session.query(UserRole).options(
                    joinedload(UserRole.role).joinedload(Role.role_permissions).joinedload(RolePermission.permission)
                ).filter(
                    UserRole.user_id == user_uuid,
                    UserRole.is_active == True,
                    UserRole.is_deleted == False
                ).all()
                
                for user_role in user_roles:
                    if user_role.is_valid and user_role.role.is_active:
                        for role_permission in user_role.role.role_permissions:
                            if role_permission.is_valid and role_permission.permission.is_active:
                                permissions.add(role_permission.permission.name)
                
                # Get direct resource permissions
                if resource_type and resource_id:
                    resource = session.query(Resource).filter(
                        Resource.resource_type == resource_type,
                        Resource.resource_id == resource_id,
                        Resource.is_active == True,
                        Resource.is_deleted == False
                    ).first()
                    
                    if resource:
                        user_permissions = session.query(UserResourcePermission).options(
                            joinedload(UserResourcePermission.permission)
                        ).filter(
                            UserResourcePermission.user_id == user_uuid,
                            UserResourcePermission.resource_id == resource.id,
                            UserResourcePermission.is_active == True,
                            UserResourcePermission.is_deleted == False
                        ).all()
                        
                        for user_permission in user_permissions:
                            if user_permission.is_valid and user_permission.permission.is_active:
                                permissions.add(user_permission.permission.name)
                
                return list(permissions)
                
        except Exception as e:
            logger.error(
                "Get user permissions failed",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                error=str(e)
            )
            return []
    
    # ============================================================================
    # CACHE MANAGEMENT
    # ============================================================================
    
    def _get_permission_cache_key(
        self,
        user_id: str,
        permission_name: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> str:
        """Generate cache key for permission check."""
        key_parts = [
            "permission",
            user_id,
            permission_name
        ]
        
        if resource_type:
            key_parts.append(resource_type)
        if resource_id:
            key_parts.append(resource_id)
        
        return ":".join(key_parts)
    
    async def invalidate_user_permissions_cache(self, user_id: str):
        """Invalidate all cached permissions for a user."""
        pattern = f"permission:{user_id}:*"
        await self.redis_service.cache_clear_pattern(pattern)
    
    async def invalidate_resource_permissions_cache(
        self,
        resource_type: str,
        resource_id: str
    ):
        """Invalidate cached permissions for a resource."""
        pattern = f"permission:*:{resource_type}:{resource_id}"
        await self.redis_service.cache_clear_pattern(pattern)


# ============================================================================
# PERMISSION DECORATORS AND UTILITIES
# ============================================================================

class PermissionChecker:
    """Utility class for permission checking operations."""
    
    def __init__(self, rbac_service: RBACService):
        self.rbac_service = rbac_service
    
    async def require_permission(
        self,
        user_id: str,
        permission: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Require a specific permission, raise exception if not granted."""
        has_permission = await self.rbac_service.check_permission(
            user_id, permission, resource_type, resource_id, context
        )
        
        if not has_permission:
            raise AuthorizationException(
                f"Permission '{permission}' required",
                details={
                    "permission": permission,
                    "resource_type": resource_type,
                    "resource_id": resource_id
                }
            )
    
    async def require_any_permission(
        self,
        user_id: str,
        permissions: List[str],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Require any of the specified permissions."""
        for permission in permissions:
            has_permission = await self.rbac_service.check_permission(
                user_id, permission, resource_type, resource_id, context
            )
            if has_permission:
                return
        
        raise AuthorizationException(
            f"One of permissions {permissions} required",
            details={
                "permissions": permissions,
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )
    
    async def require_all_permissions(
        self,
        user_id: str,
        permissions: List[str],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Require all of the specified permissions."""
        for permission in permissions:
            has_permission = await self.rbac_service.check_permission(
                user_id, permission, resource_type, resource_id, context
            )
            if not has_permission:
                raise AuthorizationException(
                    f"All permissions {permissions} required, missing '{permission}'",
                    details={
                        "permissions": permissions,
                        "missing_permission": permission,
                        "resource_type": resource_type,
                        "resource_id": resource_id
                    }
                )


# Export commonly used items
__all__ = [
    "RBACService",
    "PermissionChecker"
]

