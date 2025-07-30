"""
Role management service for the Enterprise AI System.
Handles role creation, assignment, hierarchy management, and role-based operations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set, Tuple
import structlog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_, func

from app.db.database import get_db_session
from app.models import (
    User, Role, Permission, UserRole, RolePermission, RoleHierarchy,
    Resource, ResourcePermission, UserResourcePermission
)
from app.core.exceptions import ValidationException, AuthorizationException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class RoleManagerService:
    """Service for role management operations."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.cache_ttl = 300  # 5 minutes
    
    # ============================================================================
    # ROLE MANAGEMENT
    # ============================================================================
    
    async def create_role(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        role_type: str = 'functional',
        scope: Optional[str] = None,
        parent_role_id: Optional[str] = None,
        created_by: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> str:
        """Create a new role."""
        try:
            async with get_db_session() as session:
                # Validate role name uniqueness
                existing_role = session.query(Role).filter(
                    Role.name == name.lower(),
                    Role.is_deleted == False
                ).first()
                
                if existing_role:
                    raise ValidationException(f"Role '{name}' already exists")
                
                # Validate parent role if specified
                parent_role = None
                level = 0
                if parent_role_id:
                    parent_role = session.query(Role).filter(
                        Role.id == uuid.UUID(parent_role_id),
                        Role.is_active == True,
                        Role.is_deleted == False
                    ).first()
                    
                    if not parent_role:
                        raise ValidationException("Parent role not found")
                    
                    level = parent_role.level + 1
                
                # Create role
                role = Role(
                    name=name.lower(),
                    display_name=display_name,
                    description=description,
                    role_type=role_type,
                    scope=scope,
                    parent_role_id=uuid.UUID(parent_role_id) if parent_role_id else None,
                    level=level,
                    created_by=uuid.UUID(created_by) if created_by else None
                )
                
                session.add(role)
                session.flush()  # Get the role ID
                
                # Add permissions if specified
                if permissions:
                    await self._assign_permissions_to_role(
                        session, role.id, permissions, created_by
                    )
                
                # Create hierarchy entry if parent exists
                if parent_role:
                    await self._create_role_hierarchy(session, parent_role.id, role.id)
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_role_cache(str(role.id))
                
                logger.info(
                    "Role created",
                    role_id=str(role.id),
                    role_name=name,
                    created_by=created_by
                )
                
                return str(role.id)
                
        except Exception as e:
            logger.error("Role creation failed", error=str(e), role_name=name)
            raise
    
    async def update_role(
        self,
        role_id: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """Update an existing role."""
        try:
            async with get_db_session() as session:
                role = session.query(Role).filter(
                    Role.id == uuid.UUID(role_id),
                    Role.is_deleted == False
                ).first()
                
                if not role:
                    raise ValidationException("Role not found")
                
                # Validate name uniqueness if name is being updated
                if 'name' in updates:
                    existing_role = session.query(Role).filter(
                        Role.name == updates['name'].lower(),
                        Role.id != role.id,
                        Role.is_deleted == False
                    ).first()
                    
                    if existing_role:
                        raise ValidationException(f"Role name '{updates['name']}' already exists")
                
                # Update role fields
                allowed_fields = {
                    'display_name', 'description', 'role_type', 'scope',
                    'is_active', 'max_users', 'auto_assign_conditions'
                }
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        setattr(role, field, value)
                    elif field == 'name':
                        role.name = value.lower()
                
                role.updated_by = uuid.UUID(updated_by) if updated_by else None
                role.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_role_cache(role_id)
                
                logger.info(
                    "Role updated",
                    role_id=role_id,
                    updated_by=updated_by
                )
                
                return True
                
        except Exception as e:
            logger.error("Role update failed", error=str(e), role_id=role_id)
            raise
    
    async def delete_role(
        self,
        role_id: str,
        deleted_by: Optional[str] = None,
        force: bool = False
    ) -> bool:
        """Delete a role (soft delete by default)."""
        try:
            async with get_db_session() as session:
                role = session.query(Role).filter(
                    Role.id == uuid.UUID(role_id),
                    Role.is_deleted == False
                ).first()
                
                if not role:
                    raise ValidationException("Role not found")
                
                # Check if role is system role
                if role.is_system_role and not force:
                    raise ValidationException("Cannot delete system role")
                
                # Check if role has active users
                active_users = session.query(UserRole).filter(
                    UserRole.role_id == role.id,
                    UserRole.is_active == True,
                    UserRole.is_deleted == False
                ).count()
                
                if active_users > 0 and not force:
                    raise ValidationException(
                        f"Cannot delete role with {active_users} active users"
                    )
                
                # Soft delete role
                role.soft_delete(uuid.UUID(deleted_by) if deleted_by else None)
                
                # Deactivate all user role assignments
                session.query(UserRole).filter(
                    UserRole.role_id == role.id
                ).update({
                    'is_active': False,
                    'updated_at': datetime.utcnow(),
                    'updated_by': uuid.UUID(deleted_by) if deleted_by else None
                })
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_role_cache(role_id)
                
                logger.info(
                    "Role deleted",
                    role_id=role_id,
                    deleted_by=deleted_by
                )
                
                return True
                
        except Exception as e:
            logger.error("Role deletion failed", error=str(e), role_id=role_id)
            raise
    
    # ============================================================================
    # ROLE ASSIGNMENT
    # ============================================================================
    
    async def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        assigned_by: Optional[str] = None,
        context: Optional[str] = None,
        valid_until: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assign a role to a user."""
        try:
            async with get_db_session() as session:
                # Validate user
                user = session.query(User).filter(
                    User.id == uuid.UUID(user_id),
                    User.is_active == True,
                    User.is_deleted == False
                ).first()
                
                if not user:
                    raise ValidationException("User not found")
                
                # Validate role
                role = session.query(Role).filter(
                    Role.id == uuid.UUID(role_id),
                    Role.is_active == True,
                    Role.is_deleted == False
                ).first()
                
                if not role:
                    raise ValidationException("Role not found")
                
                # Check if assignment already exists
                existing_assignment = session.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role.id,
                    UserRole.context == context,
                    UserRole.is_deleted == False
                ).first()
                
                if existing_assignment:
                    if existing_assignment.is_active:
                        raise ValidationException("User already has this role")
                    else:
                        # Reactivate existing assignment
                        existing_assignment.is_active = True
                        existing_assignment.assigned_by = uuid.UUID(assigned_by) if assigned_by else None
                        existing_assignment.assigned_at = datetime.utcnow()
                        existing_assignment.valid_until = valid_until
                        existing_assignment.conditions = conditions or {}
                        existing_assignment.approval_status = 'auto_approved'
                        
                        session.commit()
                        
                        await self._invalidate_user_roles_cache(user_id)
                        
                        return str(existing_assignment.id)
                
                # Check role capacity
                if role.max_users:
                    current_users = session.query(UserRole).filter(
                        UserRole.role_id == role.id,
                        UserRole.is_active == True,
                        UserRole.is_deleted == False
                    ).count()
                    
                    if current_users >= role.max_users:
                        raise ValidationException(
                            f"Role has reached maximum capacity of {role.max_users} users"
                        )
                
                # Create new assignment
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    assigned_by=uuid.UUID(assigned_by) if assigned_by else None,
                    context=context,
                    valid_until=valid_until,
                    conditions=conditions or {},
                    approval_status='auto_approved'  # TODO: Implement approval workflow
                )
                
                session.add(user_role)
                session.commit()
                
                # Invalidate cache
                await self._invalidate_user_roles_cache(user_id)
                
                logger.info(
                    "Role assigned to user",
                    user_id=user_id,
                    role_id=role_id,
                    assignment_id=str(user_role.id),
                    assigned_by=assigned_by
                )
                
                return str(user_role.id)
                
        except Exception as e:
            logger.error(
                "Role assignment failed",
                error=str(e),
                user_id=user_id,
                role_id=role_id
            )
            raise
    
    async def revoke_role_from_user(
        self,
        user_id: str,
        role_id: str,
        revoked_by: Optional[str] = None,
        context: Optional[str] = None
    ) -> bool:
        """Revoke a role from a user."""
        try:
            async with get_db_session() as session:
                user_role = session.query(UserRole).filter(
                    UserRole.user_id == uuid.UUID(user_id),
                    UserRole.role_id == uuid.UUID(role_id),
                    UserRole.context == context,
                    UserRole.is_active == True,
                    UserRole.is_deleted == False
                ).first()
                
                if not user_role:
                    raise ValidationException("Role assignment not found")
                
                # Deactivate assignment
                user_role.is_active = False
                user_role.updated_by = uuid.UUID(revoked_by) if revoked_by else None
                user_role.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_user_roles_cache(user_id)
                
                logger.info(
                    "Role revoked from user",
                    user_id=user_id,
                    role_id=role_id,
                    revoked_by=revoked_by
                )
                
                return True
                
        except Exception as e:
            logger.error(
                "Role revocation failed",
                error=str(e),
                user_id=user_id,
                role_id=role_id
            )
            raise
    
    # ============================================================================
    # PERMISSION MANAGEMENT
    # ============================================================================
    
    async def assign_permission_to_role(
        self,
        role_id: str,
        permission_id: str,
        granted_by: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        valid_until: Optional[datetime] = None
    ) -> str:
        """Assign a permission to a role."""
        try:
            async with get_db_session() as session:
                # Validate role
                role = session.query(Role).filter(
                    Role.id == uuid.UUID(role_id),
                    Role.is_active == True,
                    Role.is_deleted == False
                ).first()
                
                if not role:
                    raise ValidationException("Role not found")
                
                # Validate permission
                permission = session.query(Permission).filter(
                    Permission.id == uuid.UUID(permission_id),
                    Permission.is_active == True,
                    Permission.is_deleted == False
                ).first()
                
                if not permission:
                    raise ValidationException("Permission not found")
                
                # Check if assignment already exists
                existing_assignment = session.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                    RolePermission.is_deleted == False
                ).first()
                
                if existing_assignment:
                    if existing_assignment.is_active:
                        raise ValidationException("Role already has this permission")
                    else:
                        # Reactivate existing assignment
                        existing_assignment.is_active = True
                        existing_assignment.granted_by = uuid.UUID(granted_by) if granted_by else None
                        existing_assignment.granted_at = datetime.utcnow()
                        existing_assignment.conditions = conditions or {}
                        existing_assignment.valid_until = valid_until
                        
                        session.commit()
                        
                        await self._invalidate_role_cache(role_id)
                        
                        return str(existing_assignment.id)
                
                # Create new assignment
                role_permission = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                    granted_by=uuid.UUID(granted_by) if granted_by else None,
                    conditions=conditions or {},
                    valid_until=valid_until
                )
                
                session.add(role_permission)
                session.commit()
                
                # Invalidate cache
                await self._invalidate_role_cache(role_id)
                
                logger.info(
                    "Permission assigned to role",
                    role_id=role_id,
                    permission_id=permission_id,
                    assignment_id=str(role_permission.id),
                    granted_by=granted_by
                )
                
                return str(role_permission.id)
                
        except Exception as e:
            logger.error(
                "Permission assignment failed",
                error=str(e),
                role_id=role_id,
                permission_id=permission_id
            )
            raise
    
    async def revoke_permission_from_role(
        self,
        role_id: str,
        permission_id: str,
        revoked_by: Optional[str] = None
    ) -> bool:
        """Revoke a permission from a role."""
        try:
            async with get_db_session() as session:
                role_permission = session.query(RolePermission).filter(
                    RolePermission.role_id == uuid.UUID(role_id),
                    RolePermission.permission_id == uuid.UUID(permission_id),
                    RolePermission.is_active == True,
                    RolePermission.is_deleted == False
                ).first()
                
                if not role_permission:
                    raise ValidationException("Permission assignment not found")
                
                # Deactivate assignment
                role_permission.is_active = False
                role_permission.updated_by = uuid.UUID(revoked_by) if revoked_by else None
                role_permission.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_role_cache(role_id)
                
                logger.info(
                    "Permission revoked from role",
                    role_id=role_id,
                    permission_id=permission_id,
                    revoked_by=revoked_by
                )
                
                return True
                
        except Exception as e:
            logger.error(
                "Permission revocation failed",
                error=str(e),
                role_id=role_id,
                permission_id=permission_id
            )
            raise
    
    # ============================================================================
    # ROLE HIERARCHY
    # ============================================================================
    
    async def create_role_hierarchy(
        self,
        parent_role_id: str,
        child_role_id: str,
        inheritance_type: str = 'full',
        conditions: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a role hierarchy relationship."""
        try:
            async with get_db_session() as session:
                return await self._create_role_hierarchy(
                    session,
                    uuid.UUID(parent_role_id),
                    uuid.UUID(child_role_id),
                    inheritance_type,
                    conditions
                )
                
        except Exception as e:
            logger.error(
                "Role hierarchy creation failed",
                error=str(e),
                parent_role_id=parent_role_id,
                child_role_id=child_role_id
            )
            raise
    
    async def _create_role_hierarchy(
        self,
        session: Session,
        parent_role_id: uuid.UUID,
        child_role_id: uuid.UUID,
        inheritance_type: str = 'full',
        conditions: Optional[Dict[str, Any]] = None
    ) -> str:
        """Internal method to create role hierarchy."""
        # Validate roles
        parent_role = session.query(Role).get(parent_role_id)
        child_role = session.query(Role).get(child_role_id)
        
        if not parent_role or not child_role:
            raise ValidationException("Parent or child role not found")
        
        # Check for circular dependency
        if await self._would_create_circular_dependency(
            session, parent_role_id, child_role_id
        ):
            raise ValidationException("Would create circular dependency")
        
        # Create hierarchy entry
        hierarchy = RoleHierarchy(
            parent_role_id=parent_role_id,
            child_role_id=child_role_id,
            depth=1,
            inheritance_type=inheritance_type,
            inheritance_conditions=conditions or {}
        )
        
        session.add(hierarchy)
        session.commit()
        
        # Update child role's parent reference
        child_role.parent_role_id = parent_role_id
        child_role.level = parent_role.level + 1
        
        session.commit()
        
        # Invalidate cache
        await self._invalidate_role_cache(str(parent_role_id))
        await self._invalidate_role_cache(str(child_role_id))
        
        return str(hierarchy.id)
    
    async def _would_create_circular_dependency(
        self,
        session: Session,
        parent_role_id: uuid.UUID,
        child_role_id: uuid.UUID
    ) -> bool:
        """Check if creating hierarchy would create circular dependency."""
        # Check if parent is already a descendant of child
        descendants = await self._get_role_descendants(session, child_role_id)
        return parent_role_id in descendants
    
    async def _get_role_descendants(
        self,
        session: Session,
        role_id: uuid.UUID
    ) -> Set[uuid.UUID]:
        """Get all descendant roles of a given role."""
        descendants = set()
        
        # Get direct children
        children = session.query(RoleHierarchy).filter(
            RoleHierarchy.parent_role_id == role_id,
            RoleHierarchy.is_active == True,
            RoleHierarchy.is_deleted == False
        ).all()
        
        for child in children:
            descendants.add(child.child_role_id)
            # Recursively get descendants
            child_descendants = await self._get_role_descendants(
                session, child.child_role_id
            )
            descendants.update(child_descendants)
        
        return descendants
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def _assign_permissions_to_role(
        self,
        session: Session,
        role_id: uuid.UUID,
        permission_names: List[str],
        granted_by: Optional[str] = None
    ):
        """Assign multiple permissions to a role."""
        for permission_name in permission_names:
            permission = session.query(Permission).filter(
                Permission.name == permission_name,
                Permission.is_active == True,
                Permission.is_deleted == False
            ).first()
            
            if permission:
                role_permission = RolePermission(
                    role_id=role_id,
                    permission_id=permission.id,
                    granted_by=uuid.UUID(granted_by) if granted_by else None
                )
                session.add(role_permission)
    
    async def _invalidate_role_cache(self, role_id: str):
        """Invalidate role-related cache entries."""
        patterns = [
            f"role:{role_id}:*",
            f"permission:*:role:{role_id}",
            f"user_roles:*"
        ]
        
        for pattern in patterns:
            await self.redis_service.cache_clear_pattern(pattern)
    
    async def _invalidate_user_roles_cache(self, user_id: str):
        """Invalidate user roles cache."""
        patterns = [
            f"user_roles:{user_id}",
            f"permission:{user_id}:*"
        ]
        
        for pattern in patterns:
            await self.redis_service.cache_clear_pattern(pattern)


# Export commonly used items
__all__ = [
    "RoleManagerService"
]

