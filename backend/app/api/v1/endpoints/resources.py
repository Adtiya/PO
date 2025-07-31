"""
Resource management endpoints for the Enterprise AI System.
Provides CRUD operations for resources and resource-based permissions.
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
from app.services.resource_manager import ResourceManagerService
from app.services.rbac import RBACService
from app.core.exceptions import ValidationException, AuthorizationException

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ResourceCreate(BaseModel):
    """Schema for creating a new resource."""
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: str = Field(..., min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    owner_id: Optional[str] = None
    parent_resource_id: Optional[str] = None
    security_level: str = Field(default='internal', pattern='^(public|internal|confidential|restricted)$')
    attributes: Optional[Dict[str, Any]] = Field(default={})
    tags: Optional[List[str]] = Field(default=[])
    
    @validator('owner_id', 'parent_resource_id')
    def validate_uuid(cls, v):
        if v:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid UUID format')
        return v


class ResourceUpdate(BaseModel):
    """Schema for updating a resource."""
    name: Optional[str] = Field(None, max_length=200)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    owner_id: Optional[str] = None
    security_level: Optional[str] = Field(None, pattern='^(public|internal|confidential|restricted)$')
    attributes: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    
    @validator('owner_id')
    def validate_uuid(cls, v):
        if v:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid UUID format')
        return v


class ResourcePermissionConfig(BaseModel):
    """Schema for configuring resource permissions."""
    permission_id: str
    is_inheritable: bool = Field(default=True)
    is_delegatable: bool = Field(default=False)
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('permission_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid permission ID format')
        return v


class ResourcePermissionGrant(BaseModel):
    """Schema for granting resource permission to user."""
    user_id: str
    permission_name: str
    grant_type: str = Field(default='direct', pattern='^(direct|inherited|delegated|temporary)$')
    valid_until: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user ID format')
        return v


class ResourcePermissionCheck(BaseModel):
    """Schema for checking resource permission."""
    user_id: str
    permission_name: str
    context: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user ID format')
        return v


class ResourceResponse(BaseModel):
    """Schema for resource response."""
    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    resource_type: str
    resource_id: str
    path: str
    security_level: str
    is_active: bool
    is_public: bool
    owner_id: Optional[str]
    parent_resource_id: Optional[str]
    attributes: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]


class ResourceHierarchyResponse(BaseModel):
    """Schema for resource hierarchy response."""
    resource: ResourceResponse
    ancestors: List[ResourceResponse]
    descendants: List[Dict[str, Any]]


class ResourcePermissionResponse(BaseModel):
    """Schema for resource permission response."""
    permission_name: str
    permission_display_name: str
    grant_type: str
    source: str
    resource_path: str
    valid_until: Optional[datetime]
    conditions: Dict[str, Any]


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_resource_manager() -> ResourceManagerService:
    """Get resource manager service instance."""
    return ResourceManagerService()


async def get_current_user_id_dep() -> str:
    """Get current user ID dependency."""
    # This would be implemented based on your auth system
    # For now, return a placeholder
    return "placeholder-user-id"


# ============================================================================
# RESOURCE CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=Dict[str, str])
@require_permission("resources.create")
async def create_resource(
    resource_data: ResourceCreate,
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Create a new resource."""
    try:
        resource_id = await resource_manager.register_resource(
            resource_type=resource_data.resource_type,
            resource_id=resource_data.resource_id,
            name=resource_data.name,
            display_name=resource_data.display_name,
            description=resource_data.description,
            owner_id=resource_data.owner_id,
            parent_resource_id=resource_data.parent_resource_id,
            security_level=resource_data.security_level,
            attributes=resource_data.attributes,
            tags=resource_data.tags,
            created_by=current_user_id
        )
        
        logger.info(
            "Resource created",
            resource_id=resource_id,
            resource_type=resource_data.resource_type,
            external_id=resource_data.resource_id,
            created_by=current_user_id
        )
        
        return {"resource_id": resource_id, "message": "Resource created successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resource creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create resource")


@router.get("/", response_model=List[ResourceResponse])
async def list_resources(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource_type: Optional[str] = Query(None),
    security_level: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    _: None = RequirePermission("resources.read")
):
    """List resources with filtering and pagination."""
    try:
        from app.db.database import get_db_session
        from app.models import Resource
        from sqlalchemy import and_, or_, func
        
        async with get_db_session() as session:
            query = session.query(Resource).filter(Resource.is_deleted == False)
            
            # Apply filters
            if resource_type:
                query = query.filter(Resource.resource_type == resource_type)
            if security_level:
                query = query.filter(Resource.security_level == security_level)
            if owner_id:
                query = query.filter(Resource.owner_id == uuid.UUID(owner_id))
            if is_active is not None:
                query = query.filter(Resource.is_active == is_active)
            if is_public is not None:
                query = query.filter(Resource.is_public == is_public)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Resource.name.ilike(search_term),
                        Resource.display_name.ilike(search_term),
                        Resource.description.ilike(search_term),
                        Resource.resource_id.ilike(search_term)
                    )
                )
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                for tag in tag_list:
                    query = query.filter(Resource.tags.contains([tag]))
            
            # Apply pagination
            resources = query.offset(skip).limit(limit).all()
            
            return [
                ResourceResponse(
                    id=str(resource.id),
                    name=resource.name,
                    display_name=resource.display_name,
                    description=resource.description,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    path=resource.get_full_path(),
                    security_level=resource.security_level,
                    is_active=resource.is_active,
                    is_public=resource.is_public,
                    owner_id=str(resource.owner_id) if resource.owner_id else None,
                    parent_resource_id=str(resource.parent_resource_id) if resource.parent_resource_id else None,
                    attributes=resource.attributes or {},
                    tags=resource.tags or [],
                    created_at=resource.created_at,
                    updated_at=resource.updated_at
                )
                for resource in resources
            ]
            
    except Exception as e:
        logger.error("List resources failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list resources")


@router.get("/{resource_type}/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_type: str,
    resource_id: str,
    _: None = RequirePermission("resources.read")
):
    """Get a specific resource by type and ID."""
    try:
        from app.db.database import get_db_session
        from app.models import Resource
        
        async with get_db_session() as session:
            resource = session.query(Resource).filter(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            return ResourceResponse(
                id=str(resource.id),
                name=resource.name,
                display_name=resource.display_name,
                description=resource.description,
                resource_type=resource.resource_type,
                resource_id=resource.resource_id,
                path=resource.get_full_path(),
                security_level=resource.security_level,
                is_active=resource.is_active,
                is_public=resource.is_public,
                owner_id=str(resource.owner_id) if resource.owner_id else None,
                parent_resource_id=str(resource.parent_resource_id) if resource.parent_resource_id else None,
                attributes=resource.attributes or {},
                tags=resource.tags or [],
                created_at=resource.created_at,
                updated_at=resource.updated_at
            )
            
    except Exception as e:
        logger.error("Get resource failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get resource")


@router.put("/{resource_type}/{resource_id}", response_model=Dict[str, str])
@require_permission("resources.update")
async def update_resource(
    resource_type: str,
    resource_id: str,
    resource_data: ResourceUpdate,
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Update a resource."""
    try:
        # Get resource internal ID
        from app.db.database import get_db_session
        from app.models import Resource
        
        async with get_db_session() as session:
            resource = session.query(Resource).filter(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            updates = resource_data.dict(exclude_unset=True)
            
            success = await resource_manager.update_resource(
                resource_id=str(resource.id),
                updates=updates,
                updated_by=current_user_id
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            logger.info(
                "Resource updated",
                resource_type=resource_type,
                resource_id=resource_id,
                updated_by=current_user_id
            )
            
            return {"message": "Resource updated successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resource update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update resource")


@router.delete("/{resource_type}/{resource_id}", response_model=Dict[str, str])
@require_permission("resources.delete")
async def delete_resource(
    resource_type: str,
    resource_id: str,
    cascade: bool = Query(False, description="Delete child resources as well"),
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Delete a resource."""
    try:
        # Get resource internal ID
        from app.db.database import get_db_session
        from app.models import Resource
        
        async with get_db_session() as session:
            resource = session.query(Resource).filter(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            success = await resource_manager.delete_resource(
                resource_id=str(resource.id),
                deleted_by=current_user_id,
                cascade=cascade
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            logger.info(
                "Resource deleted",
                resource_type=resource_type,
                resource_id=resource_id,
                deleted_by=current_user_id,
                cascade=cascade
            )
            
            return {"message": "Resource deleted successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resource deletion failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete resource")


# ============================================================================
# RESOURCE HIERARCHY ENDPOINTS
# ============================================================================

@router.get("/{resource_type}/{resource_id}/hierarchy", response_model=ResourceHierarchyResponse)
async def get_resource_hierarchy(
    resource_type: str,
    resource_id: str,
    include_permissions: bool = Query(False),
    resource_manager: ResourceManagerService = Depends(get_resource_manager),
    _: None = RequirePermission("resources.read")
):
    """Get the complete hierarchy for a resource."""
    try:
        # Get resource internal ID
        from app.db.database import get_db_session
        from app.models import Resource
        
        async with get_db_session() as session:
            resource = session.query(Resource).filter(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            hierarchy = await resource_manager.get_resource_hierarchy(
                resource_id=str(resource.id),
                include_permissions=include_permissions
            )
            
            return ResourceHierarchyResponse(
                resource=ResourceResponse(**hierarchy["resource"]),
                ancestors=[ResourceResponse(**ancestor) for ancestor in hierarchy["ancestors"]],
                descendants=hierarchy["descendants"]
            )
            
    except Exception as e:
        logger.error("Get resource hierarchy failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get resource hierarchy")


# ============================================================================
# RESOURCE PERMISSION ENDPOINTS
# ============================================================================

@router.post("/{resource_type}/{resource_id}/permissions/configure", response_model=Dict[str, Any])
@require_permission("resources.configure_permissions")
async def configure_resource_permissions(
    resource_type: str,
    resource_id: str,
    permission_configs: List[ResourcePermissionConfig],
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Configure which permissions can be granted on a resource."""
    try:
        # Get resource internal ID
        from app.db.database import get_db_session
        from app.models import Resource
        
        async with get_db_session() as session:
            resource = session.query(Resource).filter(
                Resource.resource_type == resource_type,
                Resource.resource_id == resource_id,
                Resource.is_deleted == False
            ).first()
            
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")
            
            config_dicts = [config.dict() for config in permission_configs]
            
            configuration_ids = await resource_manager.configure_resource_permissions(
                resource_id=str(resource.id),
                permission_configs=config_dicts,
                configured_by=current_user_id
            )
            
            logger.info(
                "Resource permissions configured",
                resource_type=resource_type,
                resource_id=resource_id,
                configurations_count=len(configuration_ids),
                configured_by=current_user_id
            )
            
            return {
                "configuration_ids": configuration_ids,
                "message": f"Configured {len(configuration_ids)} permissions for resource"
            }
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resource permission configuration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to configure resource permissions")


@router.post("/{resource_type}/{resource_id}/permissions/grant", response_model=Dict[str, str])
@require_permission("resources.grant_permissions")
async def grant_resource_permission(
    resource_type: str,
    resource_id: str,
    grant_data: ResourcePermissionGrant,
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Grant a permission to a user on a resource."""
    try:
        permission_id = await resource_manager.grant_resource_permission(
            user_id=grant_data.user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission_name=grant_data.permission_name,
            grant_type=grant_data.grant_type,
            granted_by=current_user_id,
            valid_until=grant_data.valid_until,
            conditions=grant_data.conditions
        )
        
        logger.info(
            "Resource permission granted",
            permission_id=permission_id,
            user_id=grant_data.user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=grant_data.permission_name,
            granted_by=current_user_id
        )
        
        return {"permission_id": permission_id, "message": "Permission granted successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Resource permission grant failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to grant resource permission")


@router.delete("/{resource_type}/{resource_id}/permissions/{user_id}/{permission_name}", response_model=Dict[str, str])
@require_permission("resources.revoke_permissions")
async def revoke_resource_permission(
    resource_type: str,
    resource_id: str,
    user_id: str,
    permission_name: str,
    current_user_id: str = Depends(get_current_user_id_dep),
    resource_manager: ResourceManagerService = Depends(get_resource_manager)
):
    """Revoke a permission from a user on a resource."""
    try:
        success = await resource_manager.revoke_resource_permission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission_name=permission_name,
            revoked_by=current_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Permission assignment not found")
        
        logger.info(
            "Resource permission revoked",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission=permission_name,
            revoked_by=current_user_id
        )
        
        return {"message": "Permission revoked successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error("Resource permission revocation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to revoke resource permission")


@router.post("/{resource_type}/{resource_id}/permissions/check", response_model=Dict[str, bool])
async def check_resource_permission(
    resource_type: str,
    resource_id: str,
    check_data: ResourcePermissionCheck,
    rbac_service: RBACService = Depends()
):
    """Check if a user has a specific permission on a resource."""
    try:
        has_permission = await rbac_service.check_permission(
            user_id=check_data.user_id,
            permission_name=check_data.permission_name,
            resource_type=resource_type,
            resource_id=resource_id,
            context=check_data.context
        )
        
        return {
            "has_permission": has_permission,
            "user_id": check_data.user_id,
            "permission": check_data.permission_name,
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        
    except Exception as e:
        logger.error("Resource permission check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check resource permission")


@router.get("/{resource_type}/{resource_id}/permissions/user/{user_id}", response_model=List[ResourcePermissionResponse])
async def get_user_resource_permissions(
    resource_type: str,
    resource_id: str,
    user_id: str,
    resource_manager: ResourceManagerService = Depends(get_resource_manager),
    _: None = RequirePermission("resources.read_permissions")
):
    """Get all permissions a user has on a resource including inherited ones."""
    try:
        permissions = await resource_manager.get_inherited_permissions(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        return [
            ResourcePermissionResponse(**perm)
            for perm in permissions
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error("Get user resource permissions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user resource permissions")


# ============================================================================
# RESOURCE ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/types", response_model=List[Dict[str, Any]])
async def get_resource_types(
    _: None = RequirePermission("resources.read")
):
    """Get all resource types with counts."""
    try:
        from app.db.database import get_db_session
        from app.models import Resource
        from sqlalchemy import func
        
        async with get_db_session() as session:
            types = session.query(
                Resource.resource_type,
                func.count(Resource.id).label('count')
            ).filter(
                Resource.is_active == True,
                Resource.is_deleted == False
            ).group_by(Resource.resource_type).all()
            
            return [
                {
                    "resource_type": resource_type,
                    "count": count
                }
                for resource_type, count in types
            ]
            
    except Exception as e:
        logger.error("Get resource types failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get resource types")


@router.get("/security-levels", response_model=List[Dict[str, Any]])
async def get_security_levels(
    _: None = RequirePermission("resources.read")
):
    """Get all security levels with counts."""
    try:
        from app.db.database import get_db_session
        from app.models import Resource
        from sqlalchemy import func
        
        async with get_db_session() as session:
            levels = session.query(
                Resource.security_level,
                func.count(Resource.id).label('count')
            ).filter(
                Resource.is_active == True,
                Resource.is_deleted == False
            ).group_by(Resource.security_level).all()
            
            return [
                {
                    "security_level": security_level,
                    "count": count
                }
                for security_level, count in levels
            ]
            
    except Exception as e:
        logger.error("Get security levels failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get security levels")

