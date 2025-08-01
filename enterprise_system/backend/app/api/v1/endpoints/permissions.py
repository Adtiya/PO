"""
Permission management endpoints for the Enterprise AI System.
Provides CRUD operations for permissions and permission checking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import structlog
from datetime import datetime
import uuid

from app.middleware.rbac import (
    require_permission, RequirePermission, get_rbac_service, get_permission_checker
)
from app.services.rbac import RBACService, PermissionChecker
from app.core.exceptions import ValidationException, AuthorizationException

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PermissionCreate(BaseModel):
    """Schema for creating a new permission."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., min_length=1, max_length=50)
    resource_type: Optional[str] = Field(None, max_length=50)
    action: str = Field(..., min_length=1, max_length=50)
    risk_level: str = Field(default='low', pattern='^(low|medium|high|critical)$')
    requires_approval: bool = Field(default=False)
    depends_on_permissions: Optional[List[str]] = Field(default=[])
    conflicts_with_permissions: Optional[List[str]] = Field(default=[])
    
    @validator('name')
    def validate_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Name must contain only letters, numbers, dots, hyphens, and underscores')
        return v.lower()


class PermissionUpdate(BaseModel):
    """Schema for updating a permission."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    resource_type: Optional[str] = Field(None, max_length=50)
    action: Optional[str] = Field(None, min_length=1, max_length=50)
    risk_level: Optional[str] = Field(None, pattern='^(low|medium|high|critical)$')
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None
    depends_on_permissions: Optional[List[str]] = None
    conflicts_with_permissions: Optional[List[str]] = None


class PermissionCheckRequest(BaseModel):
    """Schema for permission check request."""
    user_id: str
    permission: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id')
    def validate_user_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user ID format')
        return v


class BulkPermissionCheckRequest(BaseModel):
    """Schema for bulk permission check request."""
    user_id: str
    permissions: List[str]
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id')
    def validate_user_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user ID format')
        return v


class UserResourcePermissionCreate(BaseModel):
    """Schema for creating direct user-resource permission."""
    user_id: str
    resource_type: str
    resource_id: str
    permission_id: str
    grant_type: str = Field(default='direct', pattern='^(direct|inherited|delegated|temporary)$')
    valid_until: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id', 'permission_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    resource_type: Optional[str]
    action: str
    risk_level: str
    requires_approval: bool
    is_active: bool
    is_system_permission: bool
    depends_on_permissions: List[str]
    conflicts_with_permissions: List[str]
    created_at: datetime
    updated_at: Optional[datetime]


class PermissionCheckResponse(BaseModel):
    """Schema for permission check response."""
    user_id: str
    permission: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    has_permission: bool
    reason: Optional[str] = None


class BulkPermissionCheckResponse(BaseModel):
    """Schema for bulk permission check response."""
    user_id: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    permissions: Dict[str, bool]


class UserPermissionsResponse(BaseModel):
    """Schema for user permissions response."""
    user_id: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    permissions: List[str]


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_current_user_id_dep() -> str:
    """Get current user ID dependency."""
    # This would be implemented based on your auth system
    # For now, return a placeholder
    return "placeholder-user-id"


# ============================================================================
# PERMISSION CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=Dict[str, str])
@require_permission("permissions.create")
async def create_permission(
    permission_data: PermissionCreate,
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Create a new permission."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        
        async with get_db_session() as session:
            # Check if permission already exists
            existing_permission = session.query(Permission).filter(
                Permission.name == permission_data.name,
                Permission.is_deleted == False
            ).first()
            
            if existing_permission:
                raise ValidationException(f"Permission '{permission_data.name}' already exists")
            
            # Create new permission
            permission = Permission(
                name=permission_data.name,
                display_name=permission_data.display_name,
                description=permission_data.description,
                category=permission_data.category,
                resource_type=permission_data.resource_type,
                action=permission_data.action,
                risk_level=permission_data.risk_level,
                requires_approval=permission_data.requires_approval,
                depends_on_permissions=permission_data.depends_on_permissions or [],
                conflicts_with_permissions=permission_data.conflicts_with_permissions or [],
                created_by=uuid.UUID(current_user_id)
            )
            
            session.add(permission)
            session.commit()
            
            logger.info(
                "Permission created",
                permission_id=str(permission.id),
                permission_name=permission_data.name,
                created_by=current_user_id
            )
            
            return {"permission_id": str(permission.id), "message": "Permission created successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Permission creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create permission")


@router.get("/", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    _: None = RequirePermission("permissions.read")
):
    """List permissions with filtering and pagination."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        from sqlalchemy import and_, or_, select
        
        async with get_db_session() as session:
            query = select(Permission).where(Permission.is_deleted == False)
            
            # Apply filters
            if category:
                query = query.where(Permission.category == category)
            if resource_type:
                query = query.where(Permission.resource_type == resource_type)
            if action:
                query = query.where(Permission.action == action)
            if risk_level:
                query = query.where(Permission.risk_level == risk_level)
            if is_active is not None:
                query = query.where(Permission.is_active == is_active)
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    or_(
                        Permission.name.ilike(search_term),
                        Permission.display_name.ilike(search_term),
                        Permission.description.ilike(search_term)
                    )
                )
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            permissions_result = await session.execute(query)
            permissions = permissions_result.scalars().all()
            
            return [
                PermissionResponse(
                    id=str(perm.id),
                    name=perm.name,
                    display_name=perm.display_name,
                    description=perm.description,
                    category=perm.category,
                    resource_type=perm.resource_type,
                    action=perm.action,
                    risk_level=perm.risk_level,
                    requires_approval=perm.requires_approval,
                    is_active=perm.is_active,
                    is_system_permission=perm.is_system_permission,
                    depends_on_permissions=perm.depends_on_permissions or [],
                    conflicts_with_permissions=perm.conflicts_with_permissions or [],
                    created_at=perm.created_at,
                    updated_at=perm.updated_at
                )
                for perm in permissions
            ]
            
    except Exception as e:
        logger.error("List permissions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list permissions")


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission(
    permission_id: str,
    _: None = RequirePermission("permissions.read")
):
    """Get a specific permission by ID."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        
        async with get_db_session() as session:
            permission = session.query(Permission).filter(
                Permission.id == uuid.UUID(permission_id),
                Permission.is_deleted == False
            ).first()
            
            if not permission:
                raise HTTPException(status_code=404, detail="Permission not found")
            
            return PermissionResponse(
                id=str(permission.id),
                name=permission.name,
                display_name=permission.display_name,
                description=permission.description,
                category=permission.category,
                resource_type=permission.resource_type,
                action=permission.action,
                risk_level=permission.risk_level,
                requires_approval=permission.requires_approval,
                is_active=permission.is_active,
                is_system_permission=permission.is_system_permission,
                depends_on_permissions=permission.depends_on_permissions or [],
                conflicts_with_permissions=permission.conflicts_with_permissions or [],
                created_at=permission.created_at,
                updated_at=permission.updated_at
            )
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid permission ID format")
    except Exception as e:
        logger.error("Get permission failed", error=str(e), permission_id=permission_id)
        raise HTTPException(status_code=500, detail="Failed to get permission")


@router.put("/{permission_id}", response_model=Dict[str, str])
@require_permission("permissions.update")
async def update_permission(
    permission_id: str,
    permission_data: PermissionUpdate,
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Update a permission."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        
        async with get_db_session() as session:
            permission = session.query(Permission).filter(
                Permission.id == uuid.UUID(permission_id),
                Permission.is_deleted == False
            ).first()
            
            if not permission:
                raise HTTPException(status_code=404, detail="Permission not found")
            
            # Update permission fields
            updates = permission_data.dict(exclude_unset=True)
            allowed_fields = {
                'display_name', 'description', 'category', 'resource_type',
                'action', 'risk_level', 'requires_approval', 'is_active',
                'depends_on_permissions', 'conflicts_with_permissions'
            }
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(permission, field, value)
            
            permission.updated_by = uuid.UUID(current_user_id)
            permission.updated_at = datetime.utcnow()
            
            session.commit()
            
            logger.info(
                "Permission updated",
                permission_id=permission_id,
                updated_by=current_user_id
            )
            
            return {"message": "Permission updated successfully"}
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid permission ID format")
    except Exception as e:
        logger.error("Permission update failed", error=str(e), permission_id=permission_id)
        raise HTTPException(status_code=500, detail="Failed to update permission")


@router.delete("/{permission_id}", response_model=Dict[str, str])
@require_permission("permissions.delete")
async def delete_permission(
    permission_id: str,
    force: bool = Query(False, description="Force delete even if permission is in use"),
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Delete a permission."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission, RolePermission, UserResourcePermission
        
        async with get_db_session() as session:
            permission = session.query(Permission).filter(
                Permission.id == uuid.UUID(permission_id),
                Permission.is_deleted == False
            ).first()
            
            if not permission:
                raise HTTPException(status_code=404, detail="Permission not found")
            
            # Check if permission is system permission
            if permission.is_system_permission and not force:
                raise ValidationException("Cannot delete system permission")
            
            # Check if permission is in use
            role_permissions = session.query(RolePermission).filter(
                RolePermission.permission_id == permission.id,
                RolePermission.is_active == True,
                RolePermission.is_deleted == False
            ).count()
            
            user_permissions = session.query(UserResourcePermission).filter(
                UserResourcePermission.permission_id == permission.id,
                UserResourcePermission.is_active == True,
                UserResourcePermission.is_deleted == False
            ).count()
            
            if (role_permissions > 0 or user_permissions > 0) and not force:
                raise ValidationException(
                    f"Cannot delete permission in use by {role_permissions} roles and {user_permissions} user assignments"
                )
            
            # Soft delete permission
            permission.soft_delete(uuid.UUID(current_user_id))
            
            # Deactivate all assignments
            session.query(RolePermission).filter(
                RolePermission.permission_id == permission.id
            ).update({
                'is_active': False,
                'updated_at': datetime.utcnow(),
                'updated_by': uuid.UUID(current_user_id)
            })
            
            session.query(UserResourcePermission).filter(
                UserResourcePermission.permission_id == permission.id
            ).update({
                'is_active': False,
                'updated_at': datetime.utcnow(),
                'updated_by': uuid.UUID(current_user_id)
            })
            
            session.commit()
            
            logger.info(
                "Permission deleted",
                permission_id=permission_id,
                deleted_by=current_user_id
            )
            
            return {"message": "Permission deleted successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid permission ID format")
    except Exception as e:
        logger.error("Permission deletion failed", error=str(e), permission_id=permission_id)
        raise HTTPException(status_code=500, detail="Failed to delete permission")


# ============================================================================
# PERMISSION CHECKING ENDPOINTS
# ============================================================================

@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(
    check_request: PermissionCheckRequest,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check if a user has a specific permission."""
    try:
        has_permission = await rbac_service.check_permission(
            user_id=check_request.user_id,
            permission_name=check_request.permission,
            resource_type=check_request.resource_type,
            resource_id=check_request.resource_id,
            context=check_request.context
        )
        
        return PermissionCheckResponse(
            user_id=check_request.user_id,
            permission=check_request.permission,
            resource_type=check_request.resource_type,
            resource_id=check_request.resource_id,
            has_permission=has_permission,
            reason="Permission granted" if has_permission else "Permission denied"
        )
        
    except Exception as e:
        logger.error("Permission check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check permission")


@router.post("/check-bulk", response_model=BulkPermissionCheckResponse)
async def check_multiple_permissions(
    check_request: BulkPermissionCheckRequest,
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """Check multiple permissions for a user."""
    try:
        permissions_result = await rbac_service.check_multiple_permissions(
            user_id=check_request.user_id,
            permissions=check_request.permissions,
            resource_type=check_request.resource_type,
            resource_id=check_request.resource_id,
            context=check_request.context
        )
        
        return BulkPermissionCheckResponse(
            user_id=check_request.user_id,
            resource_type=check_request.resource_type,
            resource_id=check_request.resource_id,
            permissions=permissions_result
        )
        
    except Exception as e:
        logger.error("Bulk permission check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check permissions")


@router.get("/user/{user_id}", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    rbac_service: RBACService = Depends(get_rbac_service),
    _: None = RequirePermission("permissions.read")
):
    """Get all permissions for a user."""
    try:
        permissions = await rbac_service.get_user_permissions(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        return UserPermissionsResponse(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permissions=permissions
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error("Get user permissions failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Failed to get user permissions")


# ============================================================================
# DIRECT USER-RESOURCE PERMISSION ENDPOINTS
# ============================================================================

@router.post("/user-resource", response_model=Dict[str, str])
@require_permission("permissions.assign_direct")
async def create_user_resource_permission(
    permission_data: UserResourcePermissionCreate,
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Create a direct user-resource permission."""
    try:
        from app.db.database import get_db_session
        from app.models import UserResourcePermission, Resource, Permission, User
        
        async with get_db_session() as session:
            # Validate user
            user = session.query(User).filter(
                User.id == uuid.UUID(permission_data.user_id),
                User.is_active == True,
                User.is_deleted == False
            ).first()
            
            if not user:
                raise ValidationException("User not found")
            
            # Validate permission
            permission = session.query(Permission).filter(
                Permission.id == uuid.UUID(permission_data.permission_id),
                Permission.is_active == True,
                Permission.is_deleted == False
            ).first()
            
            if not permission:
                raise ValidationException("Permission not found")
            
            # Get or create resource
            resource = session.query(Resource).filter(
                Resource.resource_type == permission_data.resource_type,
                Resource.resource_id == permission_data.resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                # Create resource if it doesn't exist
                resource = Resource(
                    name=f"{permission_data.resource_type}:{permission_data.resource_id}",
                    resource_type=permission_data.resource_type,
                    resource_id=permission_data.resource_id,
                    created_by=uuid.UUID(current_user_id)
                )
                session.add(resource)
                session.flush()
            
            # Check if assignment already exists
            existing_assignment = session.query(UserResourcePermission).filter(
                UserResourcePermission.user_id == user.id,
                UserResourcePermission.resource_id == resource.id,
                UserResourcePermission.permission_id == permission.id,
                UserResourcePermission.is_deleted == False
            ).first()
            
            if existing_assignment:
                if existing_assignment.is_active:
                    raise ValidationException("User already has this permission on this resource")
                else:
                    # Reactivate existing assignment
                    existing_assignment.is_active = True
                    existing_assignment.grant_type = permission_data.grant_type
                    existing_assignment.valid_until = permission_data.valid_until
                    existing_assignment.conditions = permission_data.conditions
                    existing_assignment.granted_by = uuid.UUID(current_user_id)
                    existing_assignment.granted_at = datetime.utcnow()
                    
                    session.commit()
                    
                    return {"assignment_id": str(existing_assignment.id), "message": "Permission assigned successfully"}
            
            # Create new assignment
            user_permission = UserResourcePermission(
                user_id=user.id,
                resource_id=resource.id,
                permission_id=permission.id,
                grant_type=permission_data.grant_type,
                valid_until=permission_data.valid_until,
                conditions=permission_data.conditions,
                granted_by=uuid.UUID(current_user_id)
            )
            
            session.add(user_permission)
            session.commit()
            
            logger.info(
                "User resource permission created",
                assignment_id=str(user_permission.id),
                user_id=permission_data.user_id,
                resource_type=permission_data.resource_type,
                resource_id=permission_data.resource_id,
                permission_id=permission_data.permission_id,
                granted_by=current_user_id
            )
            
            return {"assignment_id": str(user_permission.id), "message": "Permission assigned successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("User resource permission creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create user resource permission")


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_permission_categories(
    _: None = RequirePermission("permissions.read")
):
    """Get all permission categories with counts."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        from sqlalchemy import func
        
        async with get_db_session() as session:
            categories = session.query(
                Permission.category,
                func.count(Permission.id).label('count')
            ).filter(
                Permission.is_active == True,
                Permission.is_deleted == False
            ).group_by(Permission.category).all()
            
            return [
                {
                    "category": category,
                    "count": count
                }
                for category, count in categories
            ]
            
    except Exception as e:
        logger.error("Get permission categories failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get permission categories")


@router.get("/actions", response_model=List[Dict[str, Any]])
async def get_permission_actions(
    category: Optional[str] = Query(None),
    _: None = RequirePermission("permissions.read")
):
    """Get all permission actions with counts."""
    try:
        from app.db.database import get_db_session
        from app.models import Permission
        from sqlalchemy import func
        
        async with get_db_session() as session:
            query = session.query(
                Permission.action,
                func.count(Permission.id).label('count')
            ).filter(
                Permission.is_active == True,
                Permission.is_deleted == False
            )
            
            if category:
                query = query.filter(Permission.category == category)
            
            actions = query.group_by(Permission.action).all()
            
            return [
                {
                    "action": action,
                    "count": count
                }
                for action, count in actions
            ]
            
    except Exception as e:
        logger.error("Get permission actions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get permission actions")