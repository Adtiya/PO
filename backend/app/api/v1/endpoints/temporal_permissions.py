"""
Temporal permissions endpoints for the Enterprise AI System.
Provides CRUD operations for time-based permissions and schedules.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import structlog
from datetime import datetime, timedelta
import uuid

from app.middleware.rbac import (
    require_permission, RequirePermission, get_current_user_id
)
from app.services.temporal_permissions import TemporalPermissionService
from app.core.exceptions import ValidationException, AuthorizationException

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TemporalPermissionCreate(BaseModel):
    """Schema for creating a temporal permission."""
    user_id: str
    permission_id: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    schedule_type: str = Field(..., regex='^(fixed|recurring|cron|conditional)$')
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    cron_expression: Optional[str] = None
    time_zone: str = Field(default='UTC')
    days_of_week: Optional[List[int]] = Field(default=[], description="0=Monday, 6=Sunday")
    time_ranges: Optional[List[Dict[str, str]]] = Field(default=[])
    max_duration_minutes: Optional[int] = Field(None, gt=0)
    max_uses: Optional[int] = Field(None, gt=0)
    conditions: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id', 'permission_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid UUID format')
        return v
    
    @validator('days_of_week')
    def validate_days_of_week(cls, v):
        if v and any(day < 0 or day > 6 for day in v):
            raise ValueError('Days of week must be between 0 (Monday) and 6 (Sunday)')
        return v
    
    @validator('time_ranges')
    def validate_time_ranges(cls, v):
        if v:
            for time_range in v:
                if not all(key in time_range for key in ['start', 'end']):
                    raise ValueError('Time range must have start and end times')
        return v


class TemporalPermissionUpdate(BaseModel):
    """Schema for updating a temporal permission."""
    schedule_type: Optional[str] = Field(None, regex='^(fixed|recurring|cron|conditional)$')
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    cron_expression: Optional[str] = None
    time_zone: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    time_ranges: Optional[List[Dict[str, str]]] = None
    max_duration_minutes: Optional[int] = Field(None, gt=0)
    max_uses: Optional[int] = Field(None, gt=0)
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemporalPermissionCheck(BaseModel):
    """Schema for checking temporal permission."""
    user_id: str
    permission_name: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    check_time: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = Field(default={})
    
    @validator('user_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid user ID format')
        return v


class TemporalPermissionResponse(BaseModel):
    """Schema for temporal permission response."""
    id: str
    user_id: str
    permission_name: str
    permission_display_name: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    schedule_type: str
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    cron_expression: Optional[str]
    time_zone: str
    days_of_week: List[int]
    time_ranges: List[Dict[str, str]]
    max_duration_minutes: Optional[int]
    max_uses: Optional[int]
    current_uses: int
    conditions: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class TemporalPermissionCheckResponse(BaseModel):
    """Schema for temporal permission check response."""
    user_id: str
    permission_name: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    check_time: datetime
    has_permission: bool
    reason: Optional[str]


class ExpiringPermissionResponse(BaseModel):
    """Schema for expiring permission response."""
    id: str
    user_id: str
    user_email: str
    permission_name: str
    permission_display_name: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    valid_until: datetime
    hours_until_expiry: float


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_temporal_permission_service() -> TemporalPermissionService:
    """Get temporal permission service instance."""
    return TemporalPermissionService()


async def get_current_user_id_dep() -> str:
    """Get current user ID dependency."""
    # This would be implemented based on your auth system
    # For now, return a placeholder
    return "placeholder-user-id"


# ============================================================================
# TEMPORAL PERMISSION CRUD ENDPOINTS
# ============================================================================

@router.post("/", response_model=Dict[str, str])
@require_permission("temporal_permissions.create")
async def create_temporal_permission(
    permission_data: TemporalPermissionCreate,
    current_user_id: str = Depends(get_current_user_id_dep),
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service)
):
    """Create a new temporal permission."""
    try:
        temporal_permission_id = await temporal_service.create_temporal_permission(
            user_id=permission_data.user_id,
            permission_id=permission_data.permission_id,
            resource_type=permission_data.resource_type,
            resource_id=permission_data.resource_id,
            schedule_type=permission_data.schedule_type,
            valid_from=permission_data.valid_from,
            valid_until=permission_data.valid_until,
            cron_expression=permission_data.cron_expression,
            time_zone=permission_data.time_zone,
            days_of_week=permission_data.days_of_week,
            time_ranges=permission_data.time_ranges,
            max_duration_minutes=permission_data.max_duration_minutes,
            max_uses=permission_data.max_uses,
            conditions=permission_data.conditions,
            created_by=current_user_id
        )
        
        logger.info(
            "Temporal permission created",
            temporal_permission_id=temporal_permission_id,
            user_id=permission_data.user_id,
            permission_id=permission_data.permission_id,
            schedule_type=permission_data.schedule_type,
            created_by=current_user_id
        )
        
        return {
            "temporal_permission_id": temporal_permission_id,
            "message": "Temporal permission created successfully"
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Temporal permission creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create temporal permission")


@router.get("/user/{user_id}", response_model=List[TemporalPermissionResponse])
async def get_user_temporal_permissions(
    user_id: str,
    include_expired: bool = Query(False),
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service),
    _: None = RequirePermission("temporal_permissions.read")
):
    """Get all temporal permissions for a user."""
    try:
        permissions = await temporal_service.get_user_temporal_permissions(
            user_id=user_id,
            include_expired=include_expired
        )
        
        return [
            TemporalPermissionResponse(**perm)
            for perm in permissions
        ]
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        logger.error("Get user temporal permissions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user temporal permissions")


@router.put("/{temporal_permission_id}", response_model=Dict[str, str])
@require_permission("temporal_permissions.update")
async def update_temporal_permission(
    temporal_permission_id: str,
    permission_data: TemporalPermissionUpdate,
    current_user_id: str = Depends(get_current_user_id_dep),
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service)
):
    """Update a temporal permission."""
    try:
        updates = permission_data.dict(exclude_unset=True)
        
        success = await temporal_service.update_temporal_permission(
            temporal_permission_id=temporal_permission_id,
            updates=updates,
            updated_by=current_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Temporal permission not found")
        
        logger.info(
            "Temporal permission updated",
            temporal_permission_id=temporal_permission_id,
            updated_by=current_user_id
        )
        
        return {"message": "Temporal permission updated successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid temporal permission ID format")
    except Exception as e:
        logger.error("Temporal permission update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update temporal permission")


@router.delete("/{temporal_permission_id}", response_model=Dict[str, str])
@require_permission("temporal_permissions.delete")
async def delete_temporal_permission(
    temporal_permission_id: str,
    current_user_id: str = Depends(get_current_user_id_dep),
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service)
):
    """Delete a temporal permission."""
    try:
        success = await temporal_service.delete_temporal_permission(
            temporal_permission_id=temporal_permission_id,
            deleted_by=current_user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Temporal permission not found")
        
        logger.info(
            "Temporal permission deleted",
            temporal_permission_id=temporal_permission_id,
            deleted_by=current_user_id
        )
        
        return {"message": "Temporal permission deleted successfully"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid temporal permission ID format")
    except Exception as e:
        logger.error("Temporal permission deletion failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete temporal permission")


# ============================================================================
# TEMPORAL PERMISSION CHECKING ENDPOINTS
# ============================================================================

@router.post("/check", response_model=TemporalPermissionCheckResponse)
async def check_temporal_permission(
    check_data: TemporalPermissionCheck,
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service)
):
    """Check if a user has temporal permission at a specific time."""
    try:
        check_time = check_data.check_time or datetime.utcnow()
        
        has_permission, reason = await temporal_service.check_temporal_permission(
            user_id=check_data.user_id,
            permission_name=check_data.permission_name,
            resource_type=check_data.resource_type,
            resource_id=check_data.resource_id,
            check_time=check_time,
            context=check_data.context
        )
        
        return TemporalPermissionCheckResponse(
            user_id=check_data.user_id,
            permission_name=check_data.permission_name,
            resource_type=check_data.resource_type,
            resource_id=check_data.resource_id,
            check_time=check_time,
            has_permission=has_permission,
            reason=reason
        )
        
    except Exception as e:
        logger.error("Temporal permission check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to check temporal permission")


@router.get("/expiring", response_model=List[ExpiringPermissionResponse])
async def get_expiring_permissions(
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours ahead to check for expiring permissions"),
    temporal_service: TemporalPermissionService = Depends(get_temporal_permission_service),
    _: None = RequirePermission("temporal_permissions.read")
):
    """Get permissions that will expire within specified hours."""
    try:
        expiring_permissions = await temporal_service.get_expiring_permissions(
            hours_ahead=hours_ahead
        )
        
        return [
            ExpiringPermissionResponse(**perm)
            for perm in expiring_permissions
        ]
        
    except Exception as e:
        logger.error("Get expiring permissions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get expiring permissions")


# ============================================================================
# SCHEDULE VALIDATION ENDPOINTS
# ============================================================================

@router.post("/validate-cron", response_model=Dict[str, Any])
async def validate_cron_expression(
    cron_data: Dict[str, str],
    _: None = RequirePermission("temporal_permissions.create")
):
    """Validate a cron expression and show next execution times."""
    try:
        from croniter import croniter
        from datetime import datetime
        
        cron_expression = cron_data.get('cron_expression')
        time_zone = cron_data.get('time_zone', 'UTC')
        
        if not cron_expression:
            raise HTTPException(status_code=400, detail="Cron expression is required")
        
        try:
            import pytz
            tz = pytz.timezone(time_zone)
            base_time = datetime.now(tz)
            
            cron = croniter(cron_expression, base_time)
            
            # Get next 5 execution times
            next_times = []
            for _ in range(5):
                next_time = cron.get_next(datetime)
                next_times.append(next_time.isoformat())
            
            return {
                "valid": True,
                "cron_expression": cron_expression,
                "time_zone": time_zone,
                "next_executions": next_times,
                "message": "Cron expression is valid"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "cron_expression": cron_expression,
                "error": str(e),
                "message": "Invalid cron expression"
            }
            
    except Exception as e:
        logger.error("Cron validation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to validate cron expression")


@router.post("/validate-schedule", response_model=Dict[str, Any])
async def validate_schedule(
    schedule_data: Dict[str, Any],
    _: None = RequirePermission("temporal_permissions.create")
):
    """Validate a complete schedule configuration."""
    try:
        schedule_type = schedule_data.get('schedule_type')
        
        if schedule_type == 'fixed':
            valid_from = schedule_data.get('valid_from')
            valid_until = schedule_data.get('valid_until')
            
            if not valid_from or not valid_until:
                return {
                    "valid": False,
                    "message": "Fixed schedule requires valid_from and valid_until dates"
                }
            
            valid_from_dt = datetime.fromisoformat(valid_from.replace('Z', '+00:00'))
            valid_until_dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
            
            if valid_from_dt >= valid_until_dt:
                return {
                    "valid": False,
                    "message": "valid_from must be before valid_until"
                }
            
            duration = valid_until_dt - valid_from_dt
            
            return {
                "valid": True,
                "schedule_type": schedule_type,
                "duration_hours": duration.total_seconds() / 3600,
                "message": "Fixed schedule is valid"
            }
        
        elif schedule_type == 'recurring':
            days_of_week = schedule_data.get('days_of_week', [])
            time_ranges = schedule_data.get('time_ranges', [])
            
            if not days_of_week and not time_ranges:
                return {
                    "valid": False,
                    "message": "Recurring schedule requires days_of_week or time_ranges"
                }
            
            return {
                "valid": True,
                "schedule_type": schedule_type,
                "days_count": len(days_of_week),
                "time_ranges_count": len(time_ranges),
                "message": "Recurring schedule is valid"
            }
        
        elif schedule_type == 'cron':
            cron_expression = schedule_data.get('cron_expression')
            
            if not cron_expression:
                return {
                    "valid": False,
                    "message": "Cron schedule requires cron_expression"
                }
            
            # Validate cron expression
            try:
                from croniter import croniter
                croniter(cron_expression)
                
                return {
                    "valid": True,
                    "schedule_type": schedule_type,
                    "cron_expression": cron_expression,
                    "message": "Cron schedule is valid"
                }
                
            except Exception as e:
                return {
                    "valid": False,
                    "message": f"Invalid cron expression: {str(e)}"
                }
        
        else:
            return {
                "valid": False,
                "message": f"Unknown schedule type: {schedule_type}"
            }
            
    except Exception as e:
        logger.error("Schedule validation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to validate schedule")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/usage", response_model=Dict[str, Any])
async def get_temporal_permissions_analytics(
    days_back: int = Query(30, ge=1, le=365),
    _: None = RequirePermission("temporal_permissions.read")
):
    """Get analytics for temporal permissions usage."""
    try:
        from app.db.database import get_db_session
        from app.models import TemporalPermission
        from sqlalchemy import func
        
        async with get_db_session() as session:
            # Get temporal permissions created in the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Count by schedule type
            schedule_type_counts = session.query(
                TemporalPermission.schedule_type,
                func.count(TemporalPermission.id).label('count')
            ).filter(
                TemporalPermission.created_at >= cutoff_date,
                TemporalPermission.is_deleted == False
            ).group_by(TemporalPermission.schedule_type).all()
            
            # Count active vs inactive
            status_counts = session.query(
                TemporalPermission.is_active,
                func.count(TemporalPermission.id).label('count')
            ).filter(
                TemporalPermission.created_at >= cutoff_date,
                TemporalPermission.is_deleted == False
            ).group_by(TemporalPermission.is_active).all()
            
            # Count expiring soon (next 7 days)
            expiring_soon = session.query(func.count(TemporalPermission.id)).filter(
                TemporalPermission.valid_until.isnot(None),
                TemporalPermission.valid_until <= datetime.utcnow() + timedelta(days=7),
                TemporalPermission.valid_until > datetime.utcnow(),
                TemporalPermission.is_active == True,
                TemporalPermission.is_deleted == False
            ).scalar()
            
            return {
                "period_days": days_back,
                "schedule_types": {
                    schedule_type: count
                    for schedule_type, count in schedule_type_counts
                },
                "status_distribution": {
                    "active": next((count for is_active, count in status_counts if is_active), 0),
                    "inactive": next((count for is_active, count in status_counts if not is_active), 0)
                },
                "expiring_soon_count": expiring_soon or 0,
                "total_permissions": sum(count for _, count in schedule_type_counts)
            }
            
    except Exception as e:
        logger.error("Get temporal permissions analytics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get temporal permissions analytics")

