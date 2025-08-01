"""
Conditional permissions endpoints for the Enterprise AI System.
Provides CRUD operations for condition-based permissions and policy management.
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
from app.services.conditional_permissions import (
    ConditionalPermissionService, ConditionType, ConditionOperator
)
from app.core.exceptions import ValidationException, AuthorizationException

logger = structlog.get_logger(__name__)
router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ConditionCreate(BaseModel):
    """Schema for creating a permission condition."""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    condition_type: str = Field(..., description="Type of condition")
    condition_data: Dict[str, Any] = Field(..., description="Condition configuration data")
    is_global: bool = Field(default=False, description="Whether condition can be used globally")
    risk_level: str = Field(default='medium', pattern='^(low|medium|high|critical)$')
    
    @validator('name')
    def validate_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Name must contain only letters, numbers, hyphens, and underscores')
        return v.lower()


class ConditionUpdate(BaseModel):
    """Schema for updating a permission condition."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    condition_data: Optional[Dict[str, Any]] = None
    is_global: Optional[bool] = None
    risk_level: Optional[str] = Field(None, pattern='^(low|medium|high|critical)$')
    is_active: Optional[bool] = None


class ConditionEvaluationRequest(BaseModel):
    """Schema for evaluating conditions."""
    conditions: List[Dict[str, Any]] = Field(..., description="List of conditions to evaluate")
    context: Dict[str, Any] = Field(..., description="Context data for evaluation")
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if v:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Invalid user ID format')
        return v


class ConditionTestRequest(BaseModel):
    """Schema for testing a single condition."""
    condition_type: str
    condition_data: Dict[str, Any]
    test_context: Dict[str, Any]


class ConditionResponse(BaseModel):
    """Schema for condition response."""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    condition_type: str
    condition_data: Dict[str, Any]
    is_global: bool
    risk_level: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class ConditionEvaluationResponse(BaseModel):
    """Schema for condition evaluation response."""
    all_conditions_met: bool
    failed_conditions: List[str]
    evaluation_context: Dict[str, Any]


class ConditionTestResponse(BaseModel):
    """Schema for condition test response."""
    condition_met: bool
    reason: str
    test_context: Dict[str, Any]


# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_conditional_permission_service() -> ConditionalPermissionService:
    """Get conditional permission service instance."""
    return ConditionalPermissionService()


async def get_current_user_id_dep() -> str:
    """Get current user ID dependency."""
    # This would be implemented based on your auth system
    # For now, return a placeholder
    return "placeholder-user-id"


# ============================================================================
# CONDITION CRUD ENDPOINTS
# ============================================================================

@router.post("/conditions", response_model=Dict[str, str])
@require_permission("conditions.create")
async def create_condition(
    condition_data: ConditionCreate,
    current_user_id: str = Depends(get_current_user_id_dep),
    conditional_service: ConditionalPermissionService = Depends(get_conditional_permission_service)
):
    """Create a new permission condition."""
    try:
        condition_id = await conditional_service.create_permission_condition(
            name=condition_data.name,
            display_name=condition_data.display_name,
            description=condition_data.description,
            condition_type=condition_data.condition_type,
            condition_data=condition_data.condition_data,
            is_global=condition_data.is_global,
            risk_level=condition_data.risk_level,
            created_by=current_user_id
        )
        
        logger.info(
            "Permission condition created",
            condition_id=condition_id,
            condition_name=condition_data.name,
            condition_type=condition_data.condition_type,
            created_by=current_user_id
        )
        
        return {
            "condition_id": condition_id,
            "message": "Permission condition created successfully"
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Permission condition creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create permission condition")


@router.get("/conditions", response_model=List[ConditionResponse])
async def list_conditions(
    condition_type: Optional[str] = Query(None),
    is_global: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    risk_level: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    conditional_service: ConditionalPermissionService = Depends(get_conditional_permission_service),
    _: None = RequirePermission("conditions.read")
):
    """List permission conditions with filtering."""
    try:
        conditions = await conditional_service.get_conditions(
            condition_type=condition_type,
            is_global=is_global,
            is_active=is_active
        )
        
        # Apply additional filters
        if risk_level:
            conditions = [c for c in conditions if c['risk_level'] == risk_level]
        
        if search:
            search_lower = search.lower()
            conditions = [
                c for c in conditions
                if search_lower in c['name'].lower() or
                   search_lower in c['display_name'].lower() or
                   (c['description'] and search_lower in c['description'].lower())
            ]
        
        return [
            ConditionResponse(**condition)
            for condition in conditions
        ]
        
    except Exception as e:
        logger.error("List conditions failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list conditions")


@router.get("/conditions/{condition_id}", response_model=ConditionResponse)
async def get_condition(
    condition_id: str,
    _: None = RequirePermission("conditions.read")
):
    """Get a specific condition by ID."""
    try:
        from app.db.database import get_db_session
        from app.models import PermissionCondition
        
        async with get_db_session() as session:
            condition = session.query(PermissionCondition).filter(
                PermissionCondition.id == uuid.UUID(condition_id),
                PermissionCondition.is_deleted == False
            ).first()
            
            if not condition:
                raise HTTPException(status_code=404, detail="Condition not found")
            
            return ConditionResponse(
                id=str(condition.id),
                name=condition.name,
                display_name=condition.display_name,
                description=condition.description,
                condition_type=condition.condition_type,
                condition_data=condition.condition_data,
                is_global=condition.is_global,
                risk_level=condition.risk_level,
                is_active=condition.is_active,
                created_at=condition.created_at,
                updated_at=condition.updated_at
            )
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid condition ID format")
    except Exception as e:
        logger.error("Get condition failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get condition")


@router.put("/conditions/{condition_id}", response_model=Dict[str, str])
@require_permission("conditions.update")
async def update_condition(
    condition_id: str,
    condition_data: ConditionUpdate,
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Update a permission condition."""
    try:
        from app.db.database import get_db_session
        from app.models import PermissionCondition
        
        async with get_db_session() as session:
            condition = session.query(PermissionCondition).filter(
                PermissionCondition.id == uuid.UUID(condition_id),
                PermissionCondition.is_deleted == False
            ).first()
            
            if not condition:
                raise HTTPException(status_code=404, detail="Condition not found")
            
            # Update condition fields
            updates = condition_data.dict(exclude_unset=True)
            allowed_fields = {
                'display_name', 'description', 'condition_data',
                'is_global', 'risk_level', 'is_active'
            }
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(condition, field, value)
            
            condition.updated_by = uuid.UUID(current_user_id)
            condition.updated_at = datetime.utcnow()
            
            session.commit()
            
            logger.info(
                "Permission condition updated",
                condition_id=condition_id,
                updated_by=current_user_id
            )
            
            return {"message": "Permission condition updated successfully"}
            
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid condition ID format")
    except Exception as e:
        logger.error("Condition update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update condition")


@router.delete("/conditions/{condition_id}", response_model=Dict[str, str])
@require_permission("conditions.delete")
async def delete_condition(
    condition_id: str,
    current_user_id: str = Depends(get_current_user_id_dep)
):
    """Delete a permission condition."""
    try:
        from app.db.database import get_db_session
        from app.models import PermissionCondition
        
        async with get_db_session() as session:
            condition = session.query(PermissionCondition).filter(
                PermissionCondition.id == uuid.UUID(condition_id),
                PermissionCondition.is_deleted == False
            ).first()
            
            if not condition:
                raise HTTPException(status_code=404, detail="Condition not found")
            
            # Soft delete condition
            condition.soft_delete(uuid.UUID(current_user_id))
            
            session.commit()
            
            logger.info(
                "Permission condition deleted",
                condition_id=condition_id,
                deleted_by=current_user_id
            )
            
            return {"message": "Permission condition deleted successfully"}
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid condition ID format")
    except Exception as e:
        logger.error("Condition deletion failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete condition")


# ============================================================================
# CONDITION EVALUATION ENDPOINTS
# ============================================================================

@router.post("/evaluate", response_model=ConditionEvaluationResponse)
async def evaluate_conditions(
    evaluation_request: ConditionEvaluationRequest,
    conditional_service: ConditionalPermissionService = Depends(get_conditional_permission_service)
):
    """Evaluate a list of conditions against the provided context."""
    try:
        all_met, failed_conditions = await conditional_service.evaluate_conditions(
            conditions=evaluation_request.conditions,
            context=evaluation_request.context,
            user_id=evaluation_request.user_id,
            resource_type=evaluation_request.resource_type,
            resource_id=evaluation_request.resource_id
        )
        
        return ConditionEvaluationResponse(
            all_conditions_met=all_met,
            failed_conditions=failed_conditions,
            evaluation_context=evaluation_request.context
        )
        
    except Exception as e:
        logger.error("Condition evaluation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to evaluate conditions")


@router.post("/test", response_model=ConditionTestResponse)
async def test_condition(
    test_request: ConditionTestRequest,
    conditional_service: ConditionalPermissionService = Depends(get_conditional_permission_service)
):
    """Test a single condition against test context."""
    try:
        condition_met, reason = await conditional_service._evaluate_single_condition(
            condition_type=test_request.condition_type,
            condition_data=test_request.condition_data,
            context=test_request.test_context
        )
        
        return ConditionTestResponse(
            condition_met=condition_met,
            reason=reason,
            test_context=test_request.test_context
        )
        
    except Exception as e:
        logger.error("Condition test failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to test condition")


# ============================================================================
# CONDITION TEMPLATES AND EXAMPLES
# ============================================================================

@router.get("/condition-types", response_model=List[Dict[str, Any]])
async def get_condition_types(
    _: None = RequirePermission("conditions.read")
):
    """Get available condition types with descriptions and examples."""
    try:
        condition_types = [
            {
                "type": ConditionType.LOCATION.value,
                "display_name": "Location-based",
                "description": "Restrict access based on user location",
                "example_data": {
                    "allowed_locations": ["office", "home", "branch_office"]
                },
                "required_context": ["location"]
            },
            {
                "type": ConditionType.TIME_RANGE.value,
                "display_name": "Time Range",
                "description": "Restrict access to specific time periods",
                "example_data": {
                    "time_ranges": [
                        {"start": "09:00", "end": "17:00"},
                        {"start": "19:00", "end": "21:00"}
                    ]
                },
                "required_context": ["current_time"]
            },
            {
                "type": ConditionType.IP_ADDRESS.value,
                "display_name": "IP Address",
                "description": "Restrict access based on IP address ranges",
                "example_data": {
                    "allowed_ip_ranges": ["192.168.1.0/24", "10.0.0.0/8", "203.0.113.1"]
                },
                "required_context": ["ip_address"]
            },
            {
                "type": ConditionType.DEVICE_TYPE.value,
                "display_name": "Device Type",
                "description": "Restrict access based on device type",
                "example_data": {
                    "allowed_device_types": ["desktop", "laptop", "mobile"]
                },
                "required_context": ["device_type"]
            },
            {
                "type": ConditionType.AUTHENTICATION_METHOD.value,
                "display_name": "Authentication Method",
                "description": "Require specific authentication methods",
                "example_data": {
                    "required_auth_methods": ["mfa", "sso", "certificate"]
                },
                "required_context": ["authentication_method"]
            },
            {
                "type": ConditionType.RISK_SCORE.value,
                "display_name": "Risk Score",
                "description": "Restrict access based on calculated risk score",
                "example_data": {
                    "max_risk_score": 50
                },
                "required_context": ["risk_score"]
            },
            {
                "type": ConditionType.USER_ATTRIBUTE.value,
                "display_name": "User Attribute",
                "description": "Check user profile attributes",
                "example_data": {
                    "attribute_name": "department",
                    "expected_value": "finance",
                    "operator": "equals"
                },
                "required_context": []
            },
            {
                "type": ConditionType.RESOURCE_ATTRIBUTE.value,
                "display_name": "Resource Attribute",
                "description": "Check resource metadata attributes",
                "example_data": {
                    "attribute_name": "classification",
                    "expected_value": "public",
                    "operator": "equals"
                },
                "required_context": []
            },
            {
                "type": ConditionType.CUSTOM_EXPRESSION.value,
                "display_name": "Custom Expression",
                "description": "Evaluate custom boolean expressions",
                "example_data": {
                    "expression": "$user_level >= 5 and $department == 'admin'",
                    "variables": {
                        "user_level": "user.level",
                        "department": "user.department"
                    }
                },
                "required_context": ["varies based on expression"]
            },
            {
                "type": ConditionType.APPROVAL_REQUIRED.value,
                "display_name": "Approval Required",
                "description": "Require approval before granting access",
                "example_data": {
                    "approval_workflow": "manager_approval",
                    "auto_approve_roles": ["admin", "supervisor"]
                },
                "required_context": ["approval_id", "approval_status"]
            },
            {
                "type": ConditionType.MFA_REQUIRED.value,
                "display_name": "MFA Required",
                "description": "Require multi-factor authentication",
                "example_data": {
                    "max_age_minutes": 30,
                    "required_factors": ["totp", "sms"]
                },
                "required_context": ["mfa_verified", "mfa_timestamp"]
            }
        ]
        
        return condition_types
        
    except Exception as e:
        logger.error("Get condition types failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get condition types")


@router.get("/operators", response_model=List[Dict[str, Any]])
async def get_condition_operators(
    _: None = RequirePermission("conditions.read")
):
    """Get available condition operators with descriptions."""
    try:
        operators = [
            {
                "operator": ConditionOperator.EQUALS.value,
                "display_name": "Equals",
                "description": "Value must be exactly equal",
                "example": "department == 'finance'"
            },
            {
                "operator": ConditionOperator.NOT_EQUALS.value,
                "display_name": "Not Equals",
                "description": "Value must not be equal",
                "example": "status != 'suspended'"
            },
            {
                "operator": ConditionOperator.IN.value,
                "display_name": "In List",
                "description": "Value must be in the provided list",
                "example": "role in ['admin', 'manager']"
            },
            {
                "operator": ConditionOperator.NOT_IN.value,
                "display_name": "Not In List",
                "description": "Value must not be in the provided list",
                "example": "department not in ['temp', 'contractor']"
            },
            {
                "operator": ConditionOperator.GREATER_THAN.value,
                "display_name": "Greater Than",
                "description": "Numeric value must be greater",
                "example": "experience_years > 5"
            },
            {
                "operator": ConditionOperator.LESS_THAN.value,
                "display_name": "Less Than",
                "description": "Numeric value must be less",
                "example": "risk_score < 50"
            },
            {
                "operator": ConditionOperator.GREATER_EQUAL.value,
                "display_name": "Greater or Equal",
                "description": "Numeric value must be greater or equal",
                "example": "clearance_level >= 3"
            },
            {
                "operator": ConditionOperator.LESS_EQUAL.value,
                "display_name": "Less or Equal",
                "description": "Numeric value must be less or equal",
                "example": "age <= 65"
            },
            {
                "operator": ConditionOperator.CONTAINS.value,
                "display_name": "Contains",
                "description": "String value must contain substring",
                "example": "email contains '@company.com'"
            },
            {
                "operator": ConditionOperator.NOT_CONTAINS.value,
                "display_name": "Not Contains",
                "description": "String value must not contain substring",
                "example": "username not contains 'test'"
            },
            {
                "operator": ConditionOperator.REGEX_MATCH.value,
                "display_name": "Regex Match",
                "description": "String value must match regex pattern",
                "example": "phone matches '^\\+1[0-9]{10}$'"
            },
            {
                "operator": ConditionOperator.BETWEEN.value,
                "display_name": "Between",
                "description": "Numeric value must be between two values",
                "example": "salary between [50000, 100000]"
            }
        ]
        
        return operators
        
    except Exception as e:
        logger.error("Get condition operators failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get condition operators")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics", response_model=Dict[str, Any])
async def get_conditions_analytics(
    _: None = RequirePermission("conditions.read")
):
    """Get analytics for permission conditions usage."""
    try:
        from app.db.database import get_db_session
        from app.models import PermissionCondition
        from sqlalchemy import func
        
        async with get_db_session() as session:
            # Count by condition type
            type_counts = session.query(
                PermissionCondition.condition_type,
                func.count(PermissionCondition.id).label('count')
            ).filter(
                PermissionCondition.is_deleted == False
            ).group_by(PermissionCondition.condition_type).all()
            
            # Count by risk level
            risk_counts = session.query(
                PermissionCondition.risk_level,
                func.count(PermissionCondition.id).label('count')
            ).filter(
                PermissionCondition.is_deleted == False
            ).group_by(PermissionCondition.risk_level).all()
            
            # Count active vs inactive
            status_counts = session.query(
                PermissionCondition.is_active,
                func.count(PermissionCondition.id).label('count')
            ).filter(
                PermissionCondition.is_deleted == False
            ).group_by(PermissionCondition.is_active).all()
            
            # Count global vs specific
            scope_counts = session.query(
                PermissionCondition.is_global,
                func.count(PermissionCondition.id).label('count')
            ).filter(
                PermissionCondition.is_deleted == False
            ).group_by(PermissionCondition.is_global).all()
            
            return {
                "condition_types": {
                    condition_type: count
                    for condition_type, count in type_counts
                },
                "risk_levels": {
                    risk_level: count
                    for risk_level, count in risk_counts
                },
                "status_distribution": {
                    "active": next((count for is_active, count in status_counts if is_active), 0),
                    "inactive": next((count for is_active, count in status_counts if not is_active), 0)
                },
                "scope_distribution": {
                    "global": next((count for is_global, count in scope_counts if is_global), 0),
                    "specific": next((count for is_global, count in scope_counts if not is_global), 0)
                },
                "total_conditions": sum(count for _, count in type_counts)
            }
            
    except Exception as e:
        logger.error("Get conditions analytics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get conditions analytics")

