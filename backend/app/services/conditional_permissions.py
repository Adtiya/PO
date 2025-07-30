"""
Conditional permissions service for the Enterprise AI System.
Handles context-aware permission evaluation, policy management, and condition checking.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set, Tuple, Union
import structlog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_, func
import json
import re
from enum import Enum

from app.db.database import get_db_session
from app.models import (
    User, PermissionCondition, Permission, Role, UserRole,
    Resource, UserResourcePermission, TemporalPermission
)
from app.core.exceptions import ValidationException, AuthorizationException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class ConditionType(Enum):
    """Types of permission conditions."""
    LOCATION = "location"
    TIME_RANGE = "time_range"
    IP_ADDRESS = "ip_address"
    DEVICE_TYPE = "device_type"
    AUTHENTICATION_METHOD = "authentication_method"
    RISK_SCORE = "risk_score"
    USER_ATTRIBUTE = "user_attribute"
    RESOURCE_ATTRIBUTE = "resource_attribute"
    CUSTOM_EXPRESSION = "custom_expression"
    APPROVAL_REQUIRED = "approval_required"
    MFA_REQUIRED = "mfa_required"


class ConditionOperator(Enum):
    """Operators for condition evaluation."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"
    BETWEEN = "between"


class ConditionalPermissionService:
    """Service for conditional permission management and evaluation."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.cache_ttl = 300  # 5 minutes
    
    # ============================================================================
    # CONDITION MANAGEMENT
    # ============================================================================
    
    async def create_permission_condition(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        condition_type: str = ConditionType.CUSTOM_EXPRESSION.value,
        condition_data: Dict[str, Any] = None,
        is_global: bool = False,
        risk_level: str = 'medium',
        created_by: Optional[str] = None
    ) -> str:
        """Create a new permission condition."""
        try:
            async with get_db_session() as session:
                # Validate condition data
                if not condition_data:
                    raise ValidationException("Condition data is required")
                
                # Validate condition type
                try:
                    ConditionType(condition_type)
                except ValueError:
                    raise ValidationException(f"Invalid condition type: {condition_type}")
                
                # Validate condition data structure
                await self._validate_condition_data(condition_type, condition_data)
                
                # Check if condition name already exists
                existing_condition = session.query(PermissionCondition).filter(
                    PermissionCondition.name == name,
                    PermissionCondition.is_deleted == False
                ).first()
                
                if existing_condition:
                    raise ValidationException(f"Condition '{name}' already exists")
                
                # Create condition
                condition = PermissionCondition(
                    name=name,
                    display_name=display_name,
                    description=description,
                    condition_type=condition_type,
                    condition_data=condition_data,
                    is_global=is_global,
                    risk_level=risk_level,
                    created_by=uuid.UUID(created_by) if created_by else None
                )
                
                session.add(condition)
                session.commit()
                
                logger.info(
                    "Permission condition created",
                    condition_id=str(condition.id),
                    condition_name=name,
                    condition_type=condition_type,
                    created_by=created_by
                )
                
                return str(condition.id)
                
        except Exception as e:
            logger.error(
                "Permission condition creation failed",
                error=str(e),
                condition_name=name,
                condition_type=condition_type
            )
            raise
    
    async def _validate_condition_data(
        self,
        condition_type: str,
        condition_data: Dict[str, Any]
    ):
        """Validate condition data structure based on type."""
        if condition_type == ConditionType.LOCATION.value:
            required_fields = ['allowed_locations']
            if not all(field in condition_data for field in required_fields):
                raise ValidationException("Location condition requires 'allowed_locations' field")
        
        elif condition_type == ConditionType.TIME_RANGE.value:
            required_fields = ['time_ranges']
            if not all(field in condition_data for field in required_fields):
                raise ValidationException("Time range condition requires 'time_ranges' field")
            
            # Validate time range format
            for time_range in condition_data['time_ranges']:
                if not all(key in time_range for key in ['start', 'end']):
                    raise ValidationException("Time range must have 'start' and 'end' fields")
        
        elif condition_type == ConditionType.IP_ADDRESS.value:
            required_fields = ['allowed_ip_ranges']
            if not all(field in condition_data for field in required_fields):
                raise ValidationException("IP address condition requires 'allowed_ip_ranges' field")
        
        elif condition_type == ConditionType.RISK_SCORE.value:
            required_fields = ['max_risk_score']
            if not all(field in condition_data for field in required_fields):
                raise ValidationException("Risk score condition requires 'max_risk_score' field")
            
            if not isinstance(condition_data['max_risk_score'], (int, float)):
                raise ValidationException("Risk score must be a number")
        
        elif condition_type == ConditionType.CUSTOM_EXPRESSION.value:
            required_fields = ['expression']
            if not all(field in condition_data for field in required_fields):
                raise ValidationException("Custom expression condition requires 'expression' field")
    
    # ============================================================================
    # CONDITION EVALUATION
    # ============================================================================
    
    async def evaluate_conditions(
        self,
        conditions: List[Dict[str, Any]],
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Evaluate a list of conditions against the provided context."""
        try:
            if not conditions:
                return True, []
            
            failed_conditions = []
            
            for condition in conditions:
                condition_id = condition.get('condition_id')
                condition_data = condition.get('condition_data', {})
                condition_type = condition.get('condition_type')
                operator = condition.get('operator', 'and')
                
                # Get condition from database if only ID provided
                if condition_id and not condition_data:
                    async with get_db_session() as session:
                        db_condition = session.query(PermissionCondition).filter(
                            PermissionCondition.id == uuid.UUID(condition_id),
                            PermissionCondition.is_active == True,
                            PermissionCondition.is_deleted == False
                        ).first()
                        
                        if db_condition:
                            condition_data = db_condition.condition_data
                            condition_type = db_condition.condition_type
                        else:
                            failed_conditions.append(f"Condition {condition_id} not found")
                            continue
                
                # Evaluate condition
                is_valid, reason = await self._evaluate_single_condition(
                    condition_type, condition_data, context, user_id, resource_type, resource_id
                )
                
                if not is_valid:
                    failed_conditions.append(reason)
                    
                    # If operator is 'and', fail immediately
                    if operator == 'and':
                        return False, failed_conditions
            
            # All conditions passed or using 'or' operator with at least one success
            return len(failed_conditions) == 0, failed_conditions
            
        except Exception as e:
            logger.error("Condition evaluation failed", error=str(e))
            return False, [f"Condition evaluation error: {str(e)}"]
    
    async def _evaluate_single_condition(
        self,
        condition_type: str,
        condition_data: Dict[str, Any],
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Evaluate a single condition."""
        try:
            if condition_type == ConditionType.LOCATION.value:
                return await self._evaluate_location_condition(condition_data, context)
            
            elif condition_type == ConditionType.TIME_RANGE.value:
                return await self._evaluate_time_range_condition(condition_data, context)
            
            elif condition_type == ConditionType.IP_ADDRESS.value:
                return await self._evaluate_ip_address_condition(condition_data, context)
            
            elif condition_type == ConditionType.DEVICE_TYPE.value:
                return await self._evaluate_device_type_condition(condition_data, context)
            
            elif condition_type == ConditionType.AUTHENTICATION_METHOD.value:
                return await self._evaluate_auth_method_condition(condition_data, context)
            
            elif condition_type == ConditionType.RISK_SCORE.value:
                return await self._evaluate_risk_score_condition(condition_data, context)
            
            elif condition_type == ConditionType.USER_ATTRIBUTE.value:
                return await self._evaluate_user_attribute_condition(
                    condition_data, context, user_id
                )
            
            elif condition_type == ConditionType.RESOURCE_ATTRIBUTE.value:
                return await self._evaluate_resource_attribute_condition(
                    condition_data, context, resource_type, resource_id
                )
            
            elif condition_type == ConditionType.CUSTOM_EXPRESSION.value:
                return await self._evaluate_custom_expression_condition(condition_data, context)
            
            elif condition_type == ConditionType.APPROVAL_REQUIRED.value:
                return await self._evaluate_approval_condition(condition_data, context)
            
            elif condition_type == ConditionType.MFA_REQUIRED.value:
                return await self._evaluate_mfa_condition(condition_data, context)
            
            else:
                return False, f"Unknown condition type: {condition_type}"
                
        except Exception as e:
            logger.error(
                "Single condition evaluation failed",
                error=str(e),
                condition_type=condition_type
            )
            return False, f"Condition evaluation error: {str(e)}"
    
    async def _evaluate_location_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate location-based condition."""
        allowed_locations = condition_data.get('allowed_locations', [])
        user_location = context.get('location')
        
        if not user_location:
            return False, "User location not provided"
        
        if user_location in allowed_locations:
            return True, "Location allowed"
        
        return False, f"Location '{user_location}' not in allowed locations: {allowed_locations}"
    
    async def _evaluate_time_range_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate time range condition."""
        time_ranges = condition_data.get('time_ranges', [])
        current_time = context.get('current_time', datetime.utcnow().time())
        
        if isinstance(current_time, str):
            current_time = datetime.fromisoformat(current_time).time()
        elif isinstance(current_time, datetime):
            current_time = current_time.time()
        
        for time_range in time_ranges:
            start_time = datetime.fromisoformat(time_range['start']).time()
            end_time = datetime.fromisoformat(time_range['end']).time()
            
            if start_time <= current_time <= end_time:
                return True, "Within allowed time range"
        
        return False, f"Current time {current_time} not in allowed ranges"
    
    async def _evaluate_ip_address_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate IP address condition."""
        allowed_ip_ranges = condition_data.get('allowed_ip_ranges', [])
        user_ip = context.get('ip_address')
        
        if not user_ip:
            return False, "User IP address not provided"
        
        try:
            import ipaddress
            
            user_ip_obj = ipaddress.ip_address(user_ip)
            
            for ip_range in allowed_ip_ranges:
                if '/' in ip_range:
                    # CIDR notation
                    network = ipaddress.ip_network(ip_range, strict=False)
                    if user_ip_obj in network:
                        return True, "IP address allowed"
                else:
                    # Single IP
                    if user_ip_obj == ipaddress.ip_address(ip_range):
                        return True, "IP address allowed"
            
            return False, f"IP address '{user_ip}' not in allowed ranges"
            
        except Exception as e:
            return False, f"IP address validation error: {str(e)}"
    
    async def _evaluate_device_type_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate device type condition."""
        allowed_devices = condition_data.get('allowed_device_types', [])
        user_device = context.get('device_type')
        
        if not user_device:
            return False, "Device type not provided"
        
        if user_device in allowed_devices:
            return True, "Device type allowed"
        
        return False, f"Device type '{user_device}' not in allowed types: {allowed_devices}"
    
    async def _evaluate_auth_method_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate authentication method condition."""
        required_methods = condition_data.get('required_auth_methods', [])
        user_auth_method = context.get('authentication_method')
        
        if not user_auth_method:
            return False, "Authentication method not provided"
        
        if user_auth_method in required_methods:
            return True, "Authentication method allowed"
        
        return False, f"Authentication method '{user_auth_method}' not in required methods: {required_methods}"
    
    async def _evaluate_risk_score_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate risk score condition."""
        max_risk_score = condition_data.get('max_risk_score', 100)
        user_risk_score = context.get('risk_score', 0)
        
        if user_risk_score <= max_risk_score:
            return True, f"Risk score {user_risk_score} within limit"
        
        return False, f"Risk score {user_risk_score} exceeds maximum {max_risk_score}"
    
    async def _evaluate_user_attribute_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Evaluate user attribute condition."""
        if not user_id:
            return False, "User ID not provided for user attribute condition"
        
        try:
            async with get_db_session() as session:
                user = session.query(User).filter(
                    User.id == uuid.UUID(user_id),
                    User.is_active == True,
                    User.is_deleted == False
                ).first()
                
                if not user:
                    return False, "User not found"
                
                attribute_name = condition_data.get('attribute_name')
                expected_value = condition_data.get('expected_value')
                operator = condition_data.get('operator', ConditionOperator.EQUALS.value)
                
                # Get user attribute value
                user_attributes = user.attributes or {}
                actual_value = user_attributes.get(attribute_name)
                
                # Evaluate based on operator
                return self._compare_values(actual_value, expected_value, operator)
                
        except Exception as e:
            return False, f"User attribute evaluation error: {str(e)}"
    
    async def _evaluate_resource_attribute_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any],
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Evaluate resource attribute condition."""
        if not resource_type or not resource_id:
            return False, "Resource type and ID not provided for resource attribute condition"
        
        try:
            async with get_db_session() as session:
                resource = session.query(Resource).filter(
                    Resource.resource_type == resource_type,
                    Resource.resource_id == resource_id,
                    Resource.is_deleted == False
                ).first()
                
                if not resource:
                    return False, "Resource not found"
                
                attribute_name = condition_data.get('attribute_name')
                expected_value = condition_data.get('expected_value')
                operator = condition_data.get('operator', ConditionOperator.EQUALS.value)
                
                # Get resource attribute value
                resource_attributes = resource.attributes or {}
                actual_value = resource_attributes.get(attribute_name)
                
                # Evaluate based on operator
                return self._compare_values(actual_value, expected_value, operator)
                
        except Exception as e:
            return False, f"Resource attribute evaluation error: {str(e)}"
    
    async def _evaluate_custom_expression_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate custom expression condition."""
        expression = condition_data.get('expression', '')
        variables = condition_data.get('variables', {})
        
        try:
            # Replace variables in expression with context values
            for var_name, var_path in variables.items():
                value = self._get_nested_value(context, var_path)
                expression = expression.replace(f'${var_name}', str(value) if value is not None else 'null')
            
            # Evaluate expression safely
            result = self._safe_eval_expression(expression)
            
            if result:
                return True, "Custom expression condition met"
            else:
                return False, f"Custom expression '{expression}' evaluated to false"
                
        except Exception as e:
            return False, f"Custom expression evaluation error: {str(e)}"
    
    async def _evaluate_approval_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate approval requirement condition."""
        approval_id = context.get('approval_id')
        
        if not approval_id:
            return False, "Approval required but no approval ID provided"
        
        # Check if approval exists and is valid
        # This would integrate with an approval workflow system
        approval_status = context.get('approval_status', 'pending')
        
        if approval_status == 'approved':
            return True, "Approval condition met"
        elif approval_status == 'rejected':
            return False, "Approval was rejected"
        else:
            return False, "Approval is pending"
    
    async def _evaluate_mfa_condition(
        self,
        condition_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Evaluate MFA requirement condition."""
        mfa_verified = context.get('mfa_verified', False)
        mfa_timestamp = context.get('mfa_timestamp')
        
        if not mfa_verified:
            return False, "MFA verification required"
        
        # Check MFA freshness if specified
        max_age_minutes = condition_data.get('max_age_minutes', 60)
        
        if mfa_timestamp:
            mfa_time = datetime.fromisoformat(mfa_timestamp) if isinstance(mfa_timestamp, str) else mfa_timestamp
            age_minutes = (datetime.utcnow() - mfa_time).total_seconds() / 60
            
            if age_minutes > max_age_minutes:
                return False, f"MFA verification too old ({age_minutes:.1f} minutes)"
        
        return True, "MFA condition met"
    
    def _compare_values(
        self,
        actual: Any,
        expected: Any,
        operator: str
    ) -> Tuple[bool, str]:
        """Compare two values using the specified operator."""
        try:
            if operator == ConditionOperator.EQUALS.value:
                result = actual == expected
            elif operator == ConditionOperator.NOT_EQUALS.value:
                result = actual != expected
            elif operator == ConditionOperator.IN.value:
                result = actual in expected if isinstance(expected, (list, tuple, set)) else False
            elif operator == ConditionOperator.NOT_IN.value:
                result = actual not in expected if isinstance(expected, (list, tuple, set)) else True
            elif operator == ConditionOperator.GREATER_THAN.value:
                result = actual > expected
            elif operator == ConditionOperator.LESS_THAN.value:
                result = actual < expected
            elif operator == ConditionOperator.GREATER_EQUAL.value:
                result = actual >= expected
            elif operator == ConditionOperator.LESS_EQUAL.value:
                result = actual <= expected
            elif operator == ConditionOperator.CONTAINS.value:
                result = expected in str(actual) if actual is not None else False
            elif operator == ConditionOperator.NOT_CONTAINS.value:
                result = expected not in str(actual) if actual is not None else True
            elif operator == ConditionOperator.REGEX_MATCH.value:
                result = bool(re.match(expected, str(actual))) if actual is not None else False
            elif operator == ConditionOperator.BETWEEN.value:
                if isinstance(expected, (list, tuple)) and len(expected) == 2:
                    result = expected[0] <= actual <= expected[1]
                else:
                    result = False
            else:
                return False, f"Unknown operator: {operator}"
            
            if result:
                return True, f"Condition met: {actual} {operator} {expected}"
            else:
                return False, f"Condition not met: {actual} {operator} {expected}"
                
        except Exception as e:
            return False, f"Value comparison error: {str(e)}"
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _safe_eval_expression(self, expression: str) -> bool:
        """Safely evaluate a boolean expression."""
        # This is a simplified implementation
        # In production, use a proper expression evaluator like simpleeval
        
        # Replace common operators
        expression = expression.replace(' and ', ' & ')
        expression = expression.replace(' or ', ' | ')
        expression = expression.replace(' not ', ' ~ ')
        
        # Simple boolean evaluation
        try:
            # Only allow safe operations
            allowed_chars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ()<>=!&|~.')
            if not all(c in allowed_chars for c in expression):
                return False
            
            # Very basic evaluation - in production use a proper expression evaluator
            return 'true' in expression.lower() or '1' in expression
            
        except Exception:
            return False
    
    # ============================================================================
    # CONDITION QUERIES
    # ============================================================================
    
    async def get_conditions(
        self,
        condition_type: Optional[str] = None,
        is_global: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get permission conditions with filtering."""
        try:
            async with get_db_session() as session:
                query = session.query(PermissionCondition).filter(
                    PermissionCondition.is_deleted == False
                )
                
                if condition_type:
                    query = query.filter(PermissionCondition.condition_type == condition_type)
                if is_global is not None:
                    query = query.filter(PermissionCondition.is_global == is_global)
                if is_active is not None:
                    query = query.filter(PermissionCondition.is_active == is_active)
                
                conditions = query.all()
                
                return [
                    {
                        "id": str(condition.id),
                        "name": condition.name,
                        "display_name": condition.display_name,
                        "description": condition.description,
                        "condition_type": condition.condition_type,
                        "condition_data": condition.condition_data,
                        "is_global": condition.is_global,
                        "risk_level": condition.risk_level,
                        "is_active": condition.is_active,
                        "created_at": condition.created_at,
                        "updated_at": condition.updated_at
                    }
                    for condition in conditions
                ]
                
        except Exception as e:
            logger.error("Get conditions failed", error=str(e))
            return []


# Export commonly used items
__all__ = [
    "ConditionalPermissionService",
    "ConditionType",
    "ConditionOperator"
]

