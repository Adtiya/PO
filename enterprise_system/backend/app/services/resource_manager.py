"""
Resource management service for the Enterprise AI System.
Handles resource registration, hierarchy management, and resource-based permissions.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Tuple
import structlog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_, func

from app.db.database import get_db_session
from app.models import (
    User, Resource, ResourcePermission, UserResourcePermission,
    Permission, Role, UserRole
)
from app.core.exceptions import ValidationException, AuthorizationException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class ResourceManagerService:
    """Service for resource management operations."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.cache_ttl = 300  # 5 minutes
    
    # ============================================================================
    # RESOURCE MANAGEMENT
    # ============================================================================
    
    async def register_resource(
        self,
        resource_type: str,
        resource_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        owner_id: Optional[str] = None,
        parent_resource_id: Optional[str] = None,
        security_level: str = 'internal',
        attributes: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Register a new resource in the system."""
        try:
            async with get_db_session() as session:
                # Check if resource already exists
                existing_resource = session.query(Resource).filter(
                    Resource.resource_type == resource_type,
                    Resource.resource_id == resource_id,
                    Resource.is_deleted == False
                ).first()
                
                if existing_resource:
                    raise ValidationException(
                        f"Resource {resource_type}:{resource_id} already exists"
                    )
                
                # Validate parent resource if specified
                parent_resource = None
                if parent_resource_id:
                    parent_resource = session.query(Resource).filter(
                        Resource.id == uuid.UUID(parent_resource_id),
                        Resource.is_active == True,
                        Resource.is_deleted == False
                    ).first()
                    
                    if not parent_resource:
                        raise ValidationException("Parent resource not found")
                
                # Validate owner if specified
                if owner_id:
                    owner = session.query(User).filter(
                        User.id == uuid.UUID(owner_id),
                        User.is_active == True,
                        User.is_deleted == False
                    ).first()
                    
                    if not owner:
                        raise ValidationException("Owner not found")
                
                # Create resource
                resource = Resource(
                    name=name or f"{resource_type}:{resource_id}",
                    display_name=display_name,
                    description=description,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    owner_id=uuid.UUID(owner_id) if owner_id else None,
                    parent_resource_id=uuid.UUID(parent_resource_id) if parent_resource_id else None,
                    security_level=security_level,
                    attributes=attributes or {},
                    tags=tags or [],
                    created_by=uuid.UUID(created_by) if created_by else None
                )
                
                session.add(resource)
                session.flush()  # Get the resource ID
                
                # Set hierarchical path
                if parent_resource:
                    parent_path = parent_resource.get_full_path()
                    resource.path = f"{parent_path}/{resource.name}"
                else:
                    resource.path = resource.name
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_resource_cache(str(resource.id))
                
                logger.info(
                    "Resource registered",
                    resource_id=str(resource.id),
                    resource_type=resource_type,
                    external_id=resource_id,
                    created_by=created_by
                )
                
                return str(resource.id)
                
        except Exception as e:
            logger.error(
                "Resource registration failed",
                error=str(e),
                resource_type=resource_type,
                resource_id=resource_id
            )
            raise
    
    async def update_resource(
        self,
        resource_id: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """Update an existing resource."""
        try:
            async with get_db_session() as session:
                resource = session.query(Resource).filter(
                    Resource.id == uuid.UUID(resource_id),
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    raise ValidationException("Resource not found")
                
                # Update resource fields
                allowed_fields = {
                    'name', 'display_name', 'description', 'owner_id',
                    'security_level', 'attributes', 'tags', 'is_active', 'is_public'
                }
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        if field == 'owner_id' and value:
                            value = uuid.UUID(value)
                        setattr(resource, field, value)
                
                resource.updated_by = uuid.UUID(updated_by) if updated_by else None
                resource.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_resource_cache(resource_id)
                
                logger.info(
                    "Resource updated",
                    resource_id=resource_id,
                    updated_by=updated_by
                )
                
                return True
                
        except Exception as e:
            logger.error("Resource update failed", error=str(e), resource_id=resource_id)
            raise
    
    async def delete_resource(
        self,
        resource_id: str,
        deleted_by: Optional[str] = None,
        cascade: bool = False
    ) -> bool:
        """Delete a resource (soft delete by default)."""
        try:
            async with get_db_session() as session:
                resource = session.query(Resource).filter(
                    Resource.id == uuid.UUID(resource_id),
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    raise ValidationException("Resource not found")
                
                # Check for child resources
                child_resources = session.query(Resource).filter(
                    Resource.parent_resource_id == resource.id,
                    Resource.is_active == True,
                    Resource.is_deleted == False
                ).count()
                
                if child_resources > 0 and not cascade:
                    raise ValidationException(
                        f"Cannot delete resource with {child_resources} child resources"
                    )
                
                # Soft delete resource
                resource.soft_delete(uuid.UUID(deleted_by) if deleted_by else None)
                
                # Cascade delete child resources if requested
                if cascade and child_resources > 0:
                    child_resources_list = session.query(Resource).filter(
                        Resource.parent_resource_id == resource.id,
                        Resource.is_deleted == False
                    ).all()
                    
                    for child in child_resources_list:
                        child.soft_delete(uuid.UUID(deleted_by) if deleted_by else None)
                
                # Deactivate all permissions on this resource
                session.query(UserResourcePermission).filter(
                    UserResourcePermission.resource_id == resource.id
                ).update({
                    'is_active': False,
                    'updated_at': datetime.utcnow(),
                    'updated_by': uuid.UUID(deleted_by) if deleted_by else None
                })
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_resource_cache(resource_id)
                
                logger.info(
                    "Resource deleted",
                    resource_id=resource_id,
                    deleted_by=deleted_by,
                    cascade=cascade
                )
                
                return True
                
        except Exception as e:
            logger.error("Resource deletion failed", error=str(e), resource_id=resource_id)
            raise
    
    # ============================================================================
    # RESOURCE PERMISSION MANAGEMENT
    # ============================================================================
    
    async def configure_resource_permissions(
        self,
        resource_id: str,
        permission_configs: List[Dict[str, Any]],
        configured_by: Optional[str] = None
    ) -> List[str]:
        """Configure which permissions can be granted on a resource."""
        try:
            async with get_db_session() as session:
                # Validate resource
                resource = session.query(Resource).filter(
                    Resource.id == uuid.UUID(resource_id),
                    Resource.is_active == True,
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    raise ValidationException("Resource not found")
                
                created_configs = []
                
                for config in permission_configs:
                    permission_id = config.get('permission_id')
                    is_inheritable = config.get('is_inheritable', True)
                    is_delegatable = config.get('is_delegatable', False)
                    conditions = config.get('conditions', {})
                    
                    # Validate permission
                    permission = session.query(Permission).filter(
                        Permission.id == uuid.UUID(permission_id),
                        Permission.is_active == True,
                        Permission.is_deleted == False
                    ).first()
                    
                    if not permission:
                        logger.warning(
                            "Permission not found, skipping",
                            permission_id=permission_id
                        )
                        continue
                    
                    # Check if configuration already exists
                    existing_config = session.query(ResourcePermission).filter(
                        ResourcePermission.resource_id == resource.id,
                        ResourcePermission.permission_id == permission.id,
                        ResourcePermission.is_deleted == False
                    ).first()
                    
                    if existing_config:
                        # Update existing configuration
                        existing_config.is_inheritable = is_inheritable
                        existing_config.is_delegatable = is_delegatable
                        existing_config.conditions = conditions
                        existing_config.is_active = True
                        existing_config.updated_by = uuid.UUID(configured_by) if configured_by else None
                        existing_config.updated_at = datetime.utcnow()
                        
                        created_configs.append(str(existing_config.id))
                    else:
                        # Create new configuration
                        resource_permission = ResourcePermission(
                            resource_id=resource.id,
                            permission_id=permission.id,
                            is_inheritable=is_inheritable,
                            is_delegatable=is_delegatable,
                            conditions=conditions,
                            created_by=uuid.UUID(configured_by) if configured_by else None
                        )
                        
                        session.add(resource_permission)
                        session.flush()
                        
                        created_configs.append(str(resource_permission.id))
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_resource_cache(resource_id)
                
                logger.info(
                    "Resource permissions configured",
                    resource_id=resource_id,
                    configurations_count=len(created_configs),
                    configured_by=configured_by
                )
                
                return created_configs
                
        except Exception as e:
            logger.error(
                "Resource permission configuration failed",
                error=str(e),
                resource_id=resource_id
            )
            raise
    
    async def grant_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission_name: str,
        grant_type: str = 'direct',
        granted_by: Optional[str] = None,
        valid_until: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> str:
        """Grant a specific permission to a user on a resource."""
        try:
            async with get_db_session() as session:
                # Get or create resource
                resource = await self._get_or_create_resource(
                    session, resource_type, resource_id, granted_by
                )
                
                # Validate user
                user = session.query(User).filter(
                    User.id == uuid.UUID(user_id),
                    User.is_active == True,
                    User.is_deleted == False
                ).first()
                
                if not user:
                    raise ValidationException("User not found")
                
                # Validate permission
                permission = session.query(Permission).filter(
                    Permission.name == permission_name,
                    Permission.is_active == True,
                    Permission.is_deleted == False
                ).first()
                
                if not permission:
                    raise ValidationException(f"Permission '{permission_name}' not found")
                
                # Check if permission can be granted on this resource
                resource_permission = session.query(ResourcePermission).filter(
                    ResourcePermission.resource_id == resource.id,
                    ResourcePermission.permission_id == permission.id,
                    ResourcePermission.is_active == True,
                    ResourcePermission.is_deleted == False
                ).first()
                
                if not resource_permission:
                    # Auto-create resource permission configuration
                    resource_permission = ResourcePermission(
                        resource_id=resource.id,
                        permission_id=permission.id,
                        is_inheritable=True,
                        is_delegatable=False,
                        created_by=uuid.UUID(granted_by) if granted_by else None
                    )
                    session.add(resource_permission)
                    session.flush()
                
                # Check if user already has this permission
                existing_permission = session.query(UserResourcePermission).filter(
                    UserResourcePermission.user_id == user.id,
                    UserResourcePermission.resource_id == resource.id,
                    UserResourcePermission.permission_id == permission.id,
                    UserResourcePermission.is_deleted == False
                ).first()
                
                if existing_permission:
                    if existing_permission.is_active:
                        raise ValidationException(
                            "User already has this permission on this resource"
                        )
                    else:
                        # Reactivate existing permission
                        existing_permission.is_active = True
                        existing_permission.grant_type = grant_type
                        existing_permission.valid_until = valid_until
                        existing_permission.conditions = conditions or {}
                        existing_permission.granted_by = uuid.UUID(granted_by) if granted_by else None
                        existing_permission.granted_at = datetime.utcnow()
                        
                        session.commit()
                        
                        await self._invalidate_user_resource_permissions_cache(
                            user_id, resource_type, resource_id
                        )
                        
                        return str(existing_permission.id)
                
                # Create new permission grant
                user_permission = UserResourcePermission(
                    user_id=user.id,
                    resource_id=resource.id,
                    permission_id=permission.id,
                    grant_type=grant_type,
                    valid_until=valid_until,
                    conditions=conditions or {},
                    granted_by=uuid.UUID(granted_by) if granted_by else None
                )
                
                session.add(user_permission)
                session.commit()
                
                # Invalidate cache
                await self._invalidate_user_resource_permissions_cache(
                    user_id, resource_type, resource_id
                )
                
                logger.info(
                    "Resource permission granted",
                    permission_id=str(user_permission.id),
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    permission=permission_name,
                    granted_by=granted_by
                )
                
                return str(user_permission.id)
                
        except Exception as e:
            logger.error(
                "Resource permission grant failed",
                error=str(e),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission=permission_name
            )
            raise
    
    async def revoke_resource_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        permission_name: str,
        revoked_by: Optional[str] = None
    ) -> bool:
        """Revoke a specific permission from a user on a resource."""
        try:
            async with get_db_session() as session:
                # Get resource
                resource = session.query(Resource).filter(
                    Resource.resource_type == resource_type,
                    Resource.resource_id == resource_id,
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    raise ValidationException("Resource not found")
                
                # Get permission
                permission = session.query(Permission).filter(
                    Permission.name == permission_name,
                    Permission.is_active == True,
                    Permission.is_deleted == False
                ).first()
                
                if not permission:
                    raise ValidationException(f"Permission '{permission_name}' not found")
                
                # Find and revoke permission
                user_permission = session.query(UserResourcePermission).filter(
                    UserResourcePermission.user_id == uuid.UUID(user_id),
                    UserResourcePermission.resource_id == resource.id,
                    UserResourcePermission.permission_id == permission.id,
                    UserResourcePermission.is_active == True,
                    UserResourcePermission.is_deleted == False
                ).first()
                
                if not user_permission:
                    raise ValidationException("Permission assignment not found")
                
                # Deactivate permission
                user_permission.is_active = False
                user_permission.updated_by = uuid.UUID(revoked_by) if revoked_by else None
                user_permission.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_user_resource_permissions_cache(
                    user_id, resource_type, resource_id
                )
                
                logger.info(
                    "Resource permission revoked",
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    permission=permission_name,
                    revoked_by=revoked_by
                )
                
                return True
                
        except Exception as e:
            logger.error(
                "Resource permission revocation failed",
                error=str(e),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                permission=permission_name
            )
            raise
    
    # ============================================================================
    # RESOURCE HIERARCHY AND INHERITANCE
    # ============================================================================
    
    async def get_resource_hierarchy(
        self,
        resource_id: str,
        include_permissions: bool = False
    ) -> Dict[str, Any]:
        """Get the complete hierarchy for a resource."""
        try:
            async with get_db_session() as session:
                resource = session.query(Resource).filter(
                    Resource.id == uuid.UUID(resource_id),
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    raise ValidationException("Resource not found")
                
                # Get ancestors
                ancestors = []
                current_resource = resource
                while current_resource.parent_resource_id:
                    parent = session.query(Resource).get(current_resource.parent_resource_id)
                    if parent and parent.is_active and not parent.is_deleted:
                        ancestors.append(self._resource_to_dict(parent, include_permissions, session))
                    current_resource = parent
                
                # Get descendants
                descendants = await self._get_resource_descendants(
                    session, resource.id, include_permissions
                )
                
                return {
                    "resource": self._resource_to_dict(resource, include_permissions, session),
                    "ancestors": list(reversed(ancestors)),  # Root first
                    "descendants": descendants
                }
                
        except Exception as e:
            logger.error(
                "Get resource hierarchy failed",
                error=str(e),
                resource_id=resource_id
            )
            raise
    
    async def get_inherited_permissions(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ) -> List[Dict[str, Any]]:
        """Get all permissions a user has on a resource including inherited ones."""
        try:
            async with get_db_session() as session:
                # Get resource
                resource = session.query(Resource).filter(
                    Resource.resource_type == resource_type,
                    Resource.resource_id == resource_id,
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    return []
                
                permissions = []
                
                # Get direct permissions
                direct_permissions = session.query(UserResourcePermission).options(
                    joinedload(UserResourcePermission.permission)
                ).filter(
                    UserResourcePermission.user_id == uuid.UUID(user_id),
                    UserResourcePermission.resource_id == resource.id,
                    UserResourcePermission.is_active == True,
                    UserResourcePermission.is_deleted == False
                ).all()
                
                for perm in direct_permissions:
                    if perm.is_valid:
                        permissions.append({
                            "permission_name": perm.permission.name,
                            "permission_display_name": perm.permission.display_name,
                            "grant_type": perm.grant_type,
                            "source": "direct",
                            "resource_path": resource.get_full_path(),
                            "valid_until": perm.valid_until,
                            "conditions": perm.conditions
                        })
                
                # Get inherited permissions from parent resources
                current_resource = resource
                while current_resource.parent_resource_id:
                    parent_resource = session.query(Resource).get(current_resource.parent_resource_id)
                    if not parent_resource or not parent_resource.is_active or parent_resource.is_deleted:
                        break
                    
                    # Get inheritable permissions on parent resource
                    parent_permissions = session.query(UserResourcePermission).options(
                        joinedload(UserResourcePermission.permission)
                    ).join(ResourcePermission).filter(
                        UserResourcePermission.user_id == uuid.UUID(user_id),
                        UserResourcePermission.resource_id == parent_resource.id,
                        UserResourcePermission.is_active == True,
                        UserResourcePermission.is_deleted == False,
                        ResourcePermission.is_inheritable == True,
                        ResourcePermission.is_active == True,
                        ResourcePermission.is_deleted == False
                    ).all()
                    
                    for perm in parent_permissions:
                        if perm.is_valid:
                            permissions.append({
                                "permission_name": perm.permission.name,
                                "permission_display_name": perm.permission.display_name,
                                "grant_type": "inherited",
                                "source": "inherited",
                                "resource_path": parent_resource.get_full_path(),
                                "valid_until": perm.valid_until,
                                "conditions": perm.conditions
                            })
                    
                    current_resource = parent_resource
                
                return permissions
                
        except Exception as e:
            logger.error(
                "Get inherited permissions failed",
                error=str(e),
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id
            )
            return []
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def _get_or_create_resource(
        self,
        session: Session,
        resource_type: str,
        resource_id: str,
        created_by: Optional[str] = None
    ) -> Resource:
        """Get existing resource or create a new one."""
        resource = session.query(Resource).filter(
            Resource.resource_type == resource_type,
            Resource.resource_id == resource_id,
            Resource.is_deleted == False
        ).first()
        
        if not resource:
            resource = Resource(
                name=f"{resource_type}:{resource_id}",
                resource_type=resource_type,
                resource_id=resource_id,
                created_by=uuid.UUID(created_by) if created_by else None
            )
            session.add(resource)
            session.flush()
        
        return resource
    
    async def _get_resource_descendants(
        self,
        session: Session,
        resource_id: uuid.UUID,
        include_permissions: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all descendant resources recursively."""
        descendants = []
        
        # Get direct children
        children = session.query(Resource).filter(
            Resource.parent_resource_id == resource_id,
            Resource.is_active == True,
            Resource.is_deleted == False
        ).all()
        
        for child in children:
            child_dict = self._resource_to_dict(child, include_permissions, session)
            
            # Recursively get child's descendants
            child_descendants = await self._get_resource_descendants(
                session, child.id, include_permissions
            )
            child_dict["children"] = child_descendants
            
            descendants.append(child_dict)
        
        return descendants
    
    def _resource_to_dict(
        self,
        resource: Resource,
        include_permissions: bool = False,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Convert resource to dictionary representation."""
        result = {
            "id": str(resource.id),
            "name": resource.name,
            "display_name": resource.display_name,
            "description": resource.description,
            "resource_type": resource.resource_type,
            "resource_id": resource.resource_id,
            "path": resource.get_full_path(),
            "security_level": resource.security_level,
            "is_active": resource.is_active,
            "is_public": resource.is_public,
            "owner_id": str(resource.owner_id) if resource.owner_id else None,
            "parent_resource_id": str(resource.parent_resource_id) if resource.parent_resource_id else None,
            "attributes": resource.attributes,
            "tags": resource.tags,
            "created_at": resource.created_at,
            "updated_at": resource.updated_at
        }
        
        if include_permissions and session:
            # Get available permissions for this resource
            resource_permissions = session.query(ResourcePermission).options(
                joinedload(ResourcePermission.permission)
            ).filter(
                ResourcePermission.resource_id == resource.id,
                ResourcePermission.is_active == True,
                ResourcePermission.is_deleted == False
            ).all()
            
            result["available_permissions"] = [
                {
                    "permission_id": str(rp.permission.id),
                    "permission_name": rp.permission.name,
                    "permission_display_name": rp.permission.display_name,
                    "is_inheritable": rp.is_inheritable,
                    "is_delegatable": rp.is_delegatable,
                    "conditions": rp.conditions
                }
                for rp in resource_permissions
            ]
        
        return result
    
    async def _invalidate_resource_cache(self, resource_id: str):
        """Invalidate resource-related cache entries."""
        patterns = [
            f"resource:{resource_id}:*",
            f"permission:*:*:{resource_id}",
            f"user_resource_permissions:*"
        ]
        
        for pattern in patterns:
            await self.redis_service.cache_clear_pattern(pattern)
    
    async def _invalidate_user_resource_permissions_cache(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str
    ):
        """Invalidate user resource permissions cache."""
        patterns = [
            f"permission:{user_id}:*:{resource_type}:{resource_id}",
            f"user_resource_permissions:{user_id}:{resource_type}:{resource_id}"
        ]
        
        for pattern in patterns:
            await self.redis_service.cache_clear_pattern(pattern)


# Export commonly used items
__all__ = [
    "ResourceManagerService"
]

