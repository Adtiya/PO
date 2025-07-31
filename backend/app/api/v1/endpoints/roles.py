"""
Role management endpoints for the Enterprise AI System.
Provides CRUD operations for roles, role assignments, and role hierarchies.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import structlog
from datetime import datetime
import uuid

from app.middleware.rbac import (
    require_permission, RequirePermission, get_current_user_id
)
from app.services.role_manager import RoleManagerService
from app.services.rbac import RBACService
from app.core.exceptions import ValidationException, AuthorizationException

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RoleCreate(BaseModel):
    """Schema for creating a new role."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    role_type: str = Field(default='functional', pattern='^(system|organizational|functional|project)$')
    scope: Optional[str] = Field(None, max_length=100)
    parent_role_id: Optional[str] = None
    permissions: Optional[List[str]] = Field(default=[])
    max_users: Optional[int] = Field(None, gt=0)
    auto_assign_conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('name')
    def validate_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('parent_role_id')
    def validate_parent_role_id(cls, v):
        if v:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid parent role ID format')
        return v


class RoleUpdate(BaseModel):
    """Schema for updating a role."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    role_type: Optional[str] = Field(None, pattern='^(system|organizational|functional|project)$')
    scope: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    max_users: Optional[int] = Field(None, gt=0)
    auto_assign_conditions: Optional[Dict[str, Any]] = None


class RoleAssignment(BaseModel):
    """Schema for assigning a role to a user."""
    user_id: str
    role_id: str
    context: Optional[str] = Field(None, max_length=100)
    valid_until: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id', 'role_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v


class PermissionAssignment(BaseModel):
    """Schema for assigning a permission to a role."""
    role_id: str
    permission_id: str
    conditions: Optional[Dict[str, Any]] = Field(default={})
    valid_until: Optional[datetime] = None
    
    @validator('role_id', 'permission_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v


class RoleHierarchyCreate(BaseModel):
    """Schema for creating role hierarchy."""
    parent_role_id: str
    child_role_id: str
    inheritance_type: str = Field(default='full', pattern='^(full|partial|conditional)$')
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('parent_role_id', 'child_role_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v


class RoleResponse(BaseModel):
    """Schema for role response."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    role_type: str
    scope: Optional[str]
    is_active: bool
    is_system_role: bool
    parent_role_id: Optional[str]
    level: int
    max_users: Optional[int]
    auto_assign_conditions: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]


class UserRoleResponse(BaseModel):
    """Schema for user role assignment response."""
    id: str
    user_id: str
    role_id: str
    role_name: str
    role_display_name: str
    context: Optional[str]
    is_active: bool
    assigned_at: datetime
    valid_from: datetime
    valid_until: Optional[datetime]
    approval_status: str


class RolePermissionResponse(BaseModel):
    """Schema for role permission response."""
    id: str
    role_id: str
    permission_id: str
    permission_name: str
    permission_display_name: str
    is_active: bool
    granted_at: datetime
    valid_from: datetime
    valid_until: Optional[datetime]
    conditions: Dict[str, Any]


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_role_manager() -> RoleManagerService:
    """Get role manager service instance."""
    return RoleManagerService()


async def get_current_user_id_dep() -> str:
    """Get current user ID dependency."""
    # This would be implemented based on your auth system
    # For now, return a placeholder
    return "placeholder-user-id"


# ============================================================================
# ROLE CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=Dict[str, str])
@require_permission("roles.create")
async def create_role(
    role_data: RoleCreate,
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Create a new role."""
    try:
        role_id = await role_manager.create_role(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            role_type=role_data.role_type,
            scope=role_data.scope,
            parent_role_id=role_data.parent_role_id,
            created_by=current_user_id,
            permissions=role_data.permissions
        )
        
        logger.info(
            "Role created",
            role_id=role_id,
            role_name=role_data.name,
            created_by=current_user_id
        )
        
        return {"role_id": role_id, "message": "Role created successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Role creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create role")


@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role_type: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    _: None = RequirePermission("roles.read")
):
    """List roles with filtering and pagination."""
    try:
        from app.db.database import get_db_session
        from app.models import Role
        from sqlalchemy import and_, or_
        
        async with get_db_session() as session:
            query = session.query(Role).filter(Role.is_deleted == False)
            
            # Apply filters
            if role_type:
                query = query.filter(Role.role_type == role_type)
            if scope:
                query = query.filter(Role.scope == scope)
            if is_active is not None:
                query = query.filter(Role.is_active == is_active)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Role.name.ilike(search_term),
                        Role.display_name.ilike(search_term),
                        Role.description.ilike(search_term)
                    )
                )
            
            # Apply pagination
            roles = query.offset(skip).limit(limit).all()
            
            return [
                RoleResponse(
                    id=str(role.id),
                    name=role.name,
                    display_name=role.display_name,
                    description=role.description,
                    role_type=role.role_type,
                    scope=role.scope,
                    is_active=role.is_active,
                    is_system_role=role.is_system_role,
                    parent_role_id=str(role.parent_role_id) if role.parent_role_id else None,
                    level=role.level,
                    max_users=role.max_users,
                    auto_assign_conditions=role.auto_assign_conditions or {},
                    created_at=role.created_at,
                    updated_at=role.updated_at
                )
                for role in roles
            ]
            
    except Exception as e:
        logger.error("List roles failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list roles")


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    _: None = RequirePermission("roles.read")
):
    """Get a specific role by ID."""
    try:
        from app.db.database import get_db_session
        from app.models import Role
        
        async with get_db_session() as session:
            role = session.query(Role).filter(
                Role.id == uuid.UUID(role_id),
                Role.is_deleted == False
            ).first()
            
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            return RoleResponse(
                id=str(role.id),
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                role_type=role.role_type,
                scope=role.scope,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                parent_role_id=str(role.parent_role_id) if role.parent_role_id else None,
                level=role.level,
                max_users=role.max_users,
                auto_assign_conditions=role.auto_assign_conditions or {},
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error("Get role failed", error=str(e), role_id=role_id)
        raise HTTPException(status_code=500, detail="Failed to get role")


@router.put("/{role_id}", response_model=Dict[str, str])
@require_permission("roles.update")
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Update a role."""
    try:
        updates = role_data.dict(exclude_unset=True)
        
        success = await role_manager.update_role(
            role_id=role_id,
            updates=updates,
            updated_by=current_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Role not found")
        
        logger.info(
            "Role updated",
            role_id=role_id,
            updated_by=current_user_id
        )
        
        return {"message": "Role updated successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error("Role update failed", error=str(e), role_id=role_id)
        raise HTTPException(status_code=500, detail="Failed to update role")


@router.delete("/{role_id}", response_model=Dict[str, str])
@require_permission("roles.delete")
async def delete_role(
    role_id: str,
    force: bool = Query(False, description="Force delete even if role has active users"),
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Delete a role."""
    try:
        success = await role_manager.delete_role(
            role_id=role_id,
            deleted_by=current_user_id,
            force=force
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Role not found")
        
        logger.info(
            "Role deleted",
            role_id=role_id,
            deleted_by=current_user_id,
            force=force
        )
        
        return {"message": "Role deleted successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error("Role deletion failed", error=str(e), role_id=role_id)
        raise HTTPException(status_code=500, detail="Failed to delete role")


# ============================================================================
# ROLE ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/assignments", response_model=Dict[str, str])
@require_permission("roles.assign")
async def assign_role_to_user(
    assignment: RoleAssignment,
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Assign a role to a user."""
    try:
        assignment_id = await role_manager.assign_role_to_user(
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            assigned_by=current_user_id,
            context=assignment.context,
            valid_until=assignment.valid_until,
            conditions=assignment.conditions
        )
        
        logger.info(
            "Role assigned to user",
            assignment_id=assignment_id,
            user_id=assignment.user_id,
            role_id=assignment.role_id,
            assigned_by=current_user_id
        )
        
        return {"assignment_id": assignment_id, "message": "Role assigned successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Role assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to assign role")


@router.delete("/assignments/{user_id}/{role_id}", response_model=Dict[str, str])
@require_permission("roles.revoke")
async def revoke_role_from_user(
    user_id: str,
    role_id: str,
    context: Optional[str] = Query(None),
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Revoke a role from a user."""
    try:
        success = await role_manager.revoke_role_from_user(
            user_id=user_id,
            role_id=role_id,
            revoked_by=current_user_id,
            context=context
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Role assignment not found")
        
        logger.info(
            "Role revoked from user",
            user_id=user_id,
            role_id=role_id,
            revoked_by=current_user_id
        )
        
        return {"message": "Role revoked successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error("Role revocation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to revoke role")


@router.get("/assignments/user/{user_id}", response_model=List[UserRoleResponse])
async def get_user_roles(
    user_id: str,
    include_inactive: bool = Query(False),
    _: None = RequirePermission("roles.read")
):
    """Get all roles assigned to a user."""
    try:
        from app.db.database import get_db_session
        from app.models import UserRole, Role
        from sqlalchemy.orm import joinedload
        
        async with get_db_session() as session:
            query = session.query(UserRole).options(
                joinedload(UserRole.role)
            ).filter(
                UserRole.user_id == uuid.UUID(user_id),
                UserRole.is_deleted == False
            )
            
            if not include_inactive:
                query = query.filter(UserRole.is_active == True)
            
            user_roles = query.all()
            
            return [
                UserRoleResponse(
                    id=str(ur.id),
                    user_id=str(ur.user_id),
                    role_id=str(ur.role_id),
                    role_name=ur.role.name,
                    role_display_name=ur.role.display_name,
                    context=ur.context,
                    is_active=ur.is_active,
                    assigned_at=ur.assigned_at,
                    valid_from=ur.valid_from,
                    valid_until=ur.valid_until,
                    approval_status=ur.approval_status
                )
                for ur in user_roles
            ]
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error("Get user roles failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to get user roles")


# ============================================================================
# PERMISSION ASSIGNMENT ENDPOINTS
# ============================================================================

@router.post("/permissions", response_model=Dict[str, str])
@require_permission("permissions.assign")
async def assign_permission_to_role(
    assignment: PermissionAssignment,
    current_user_id: str = Depends(get_current_user_id_dep),
    role_manager: RoleManagerService = Depends(get_role_manager)
):
    """Assign a permission to a role."""
    try:
        assignment_id = await role_manager.assign_permission_to_role(
            role_id=assignment.role_id,
            permission_id=assignment.permission_id,
            granted_by=current_user_id,
            conditions=assignment.conditions,
            valid_until=assignment.valid_until
        )
        
        logger.info(
            "Permission assigned to role",
            assignment_id=assignment_id,
            role_id=assignment.role_id,
            permission_id=assignment.permission_id,
            granted_by=current_user_id
        )
        
        return {"assignment_id": assignment_id, "message": "Permission assigned successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Permission assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to assign permission")


@router.get("/{role_id}/permissions", response_model=List[RolePermissionResponse])
async def get_role_permissions(
    role_id: str,
    include_inherited: bool = Query(True),
    include_inactive: bool = Query(False),
    _: None = RequirePermission("roles.read")
):
    """Get all permissions assigned to a role."""
    try:
        from app.db.database import get_db_session
        from app.models import RolePermission, Permission, Role
        from sqlalchemy.orm import joinedload
        
        async with get_db_session() as session:
            # Get direct permissions
            query = session.query(RolePermission).options(
                joinedload(RolePermission.permission)
            ).filter(
                RolePermission.role_id == uuid.UUID(role_id),
                RolePermission.is_deleted == False
            )
            
            if not include_inactive:
                query = query.filter(RolePermission.is_active == True)
            
            role_permissions = query.all()
            
            permissions = [
                RolePermissionResponse(
                    id=str(rp.id),
                    role_id=str(rp.role_id),
                    permission_id=str(rp.permission_id),
                    permission_name=rp.permission.name,
                    permission_display_name=rp.permission.display_name,
                    is_active=rp.is_active,
                    granted_at=rp.granted_at,
                    valid_from=rp.valid_from,
                    valid_until=rp.valid_until,
                    conditions=rp.conditions or {}
                )
                for rp in role_permissions
            ]
            
            return permissions
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error("Get role permissions failed", error=str(e), role_id=role_id)
        raise HTTPException(status_code=500, detail="Failed to get role permissions")

