"""
Temporal permissions service for the Enterprise AI System.
Handles time-based access control, schedules, and temporal permission evaluation.
"""

import uuid
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any, Set, Tuple
import structlog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, not_, func
import pytz
from croniter import croniter
import json

from app.db.database import get_db_session
from app.models import (
    User, TemporalPermission, Permission, Role, UserRole,
    Resource, UserResourcePermission, PermissionCondition
)
from app.core.exceptions import ValidationException, AuthorizationException
from app.services.redis import RedisService

logger = structlog.get_logger(__name__)


class TemporalPermissionService:
    """Service for temporal permission management and evaluation."""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.cache_ttl = 300  # 5 minutes
    
    # ============================================================================
    # TEMPORAL PERMISSION MANAGEMENT
    # ============================================================================
    
    async def create_temporal_permission(
        self,
        user_id: str,
        permission_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        schedule_type: str = 'fixed',
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        cron_expression: Optional[str] = None,
        time_zone: str = 'UTC',
        days_of_week: Optional[List[int]] = None,
        time_ranges: Optional[List[Dict[str, str]]] = None,
        max_duration_minutes: Optional[int] = None,
        max_uses: Optional[int] = None,
        conditions: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Create a new temporal permission."""
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
                
                # Validate permission
                permission = session.query(Permission).filter(
                    Permission.id == uuid.UUID(permission_id),
                    Permission.is_active == True,
                    Permission.is_deleted == False
                ).first()
                
                if not permission:
                    raise ValidationException("Permission not found")
                
                # Validate schedule
                if schedule_type == 'cron' and not cron_expression:
                    raise ValidationException("Cron expression required for cron schedule type")
                
                if schedule_type == 'fixed' and not (valid_from and valid_until):
                    raise ValidationException("Valid from and until dates required for fixed schedule")
                
                if cron_expression:
                    try:
                        # Validate cron expression
                        croniter(cron_expression)
                    except Exception:
                        raise ValidationException("Invalid cron expression")
                
                # Validate timezone
                try:
                    pytz.timezone(time_zone)
                except Exception:
                    raise ValidationException("Invalid timezone")
                
                # Create temporal permission
                temporal_permission = TemporalPermission(
                    user_id=user.id,
                    permission_id=permission.id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    schedule_type=schedule_type,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    cron_expression=cron_expression,
                    time_zone=time_zone,
                    days_of_week=days_of_week or [],
                    time_ranges=time_ranges or [],
                    max_duration_minutes=max_duration_minutes,
                    max_uses=max_uses,
                    conditions=conditions or {},
                    created_by=uuid.UUID(created_by) if created_by else None
                )
                
                session.add(temporal_permission)
                session.commit()
                
                # Invalidate cache
                await self._invalidate_temporal_permission_cache(user_id)
                
                logger.info(
                    "Temporal permission created",
                    temporal_permission_id=str(temporal_permission.id),
                    user_id=user_id,
                    permission_id=permission_id,
                    schedule_type=schedule_type,
                    created_by=created_by
                )
                
                return str(temporal_permission.id)
                
        except Exception as e:
            logger.error(
                "Temporal permission creation failed",
                error=str(e),
                user_id=user_id,
                permission_id=permission_id
            )
            raise
    
    async def update_temporal_permission(
        self,
        temporal_permission_id: str,
        updates: Dict[str, Any],
        updated_by: Optional[str] = None
    ) -> bool:
        """Update an existing temporal permission."""
        try:
            async with get_db_session() as session:
                temporal_permission = session.query(TemporalPermission).filter(
                    TemporalPermission.id == uuid.UUID(temporal_permission_id),
                    TemporalPermission.is_deleted == False
                ).first()
                
                if not temporal_permission:
                    raise ValidationException("Temporal permission not found")
                
                # Update fields
                allowed_fields = {
                    'schedule_type', 'valid_from', 'valid_until', 'cron_expression',
                    'time_zone', 'days_of_week', 'time_ranges', 'max_duration_minutes',
                    'max_uses', 'conditions', 'is_active'
                }
                
                for field, value in updates.items():
                    if field in allowed_fields:
                        setattr(temporal_permission, field, value)
                
                temporal_permission.updated_by = uuid.UUID(updated_by) if updated_by else None
                temporal_permission.updated_at = datetime.utcnow()
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_temporal_permission_cache(str(temporal_permission.user_id))
                
                logger.info(
                    "Temporal permission updated",
                    temporal_permission_id=temporal_permission_id,
                    updated_by=updated_by
                )
                
                return True
                
        except Exception as e:
            logger.error(
                "Temporal permission update failed",
                error=str(e),
                temporal_permission_id=temporal_permission_id
            )
            raise
    
    async def delete_temporal_permission(
        self,
        temporal_permission_id: str,
        deleted_by: Optional[str] = None
    ) -> bool:
        """Delete a temporal permission."""
        try:
            async with get_db_session() as session:
                temporal_permission = session.query(TemporalPermission).filter(
                    TemporalPermission.id == uuid.UUID(temporal_permission_id),
                    TemporalPermission.is_deleted == False
                ).first()
                
                if not temporal_permission:
                    raise ValidationException("Temporal permission not found")
                
                # Soft delete
                temporal_permission.soft_delete(uuid.UUID(deleted_by) if deleted_by else None)
                
                session.commit()
                
                # Invalidate cache
                await self._invalidate_temporal_permission_cache(str(temporal_permission.user_id))
                
                logger.info(
                    "Temporal permission deleted",
                    temporal_permission_id=temporal_permission_id,
                    deleted_by=deleted_by
                )
                
                return True
                
        except Exception as e:
            logger.error(
                "Temporal permission deletion failed",
                error=str(e),
                temporal_permission_id=temporal_permission_id
            )
            raise
    
    # ============================================================================
    # TEMPORAL PERMISSION EVALUATION
    # ============================================================================
    
    async def check_temporal_permission(
        self,
        user_id: str,
        permission_name: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        check_time: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if a user has temporal permission at a specific time."""
        try:
            check_time = check_time or datetime.utcnow()
            context = context or {}
            
            # Check cache first
            cache_key = f"temporal_permission:{user_id}:{permission_name}:{resource_type}:{resource_id}:{int(check_time.timestamp())}"
            cached_result = await self.redis_service.cache_get(cache_key)
            
            if cached_result:
                result_data = json.loads(cached_result)
                return result_data['has_permission'], result_data.get('reason')
            
            async with get_db_session() as session:
                # Get permission
                permission = session.query(Permission).filter(
                    Permission.name == permission_name,
                    Permission.is_active == True,
                    Permission.is_deleted == False
                ).first()
                
                if not permission:
                    return False, "Permission not found"
                
                # Get temporal permissions for user
                query = session.query(TemporalPermission).filter(
                    TemporalPermission.user_id == uuid.UUID(user_id),
                    TemporalPermission.permission_id == permission.id,
                    TemporalPermission.is_active == True,
                    TemporalPermission.is_deleted == False
                )
                
                # Filter by resource if specified
                if resource_type:
                    query = query.filter(
                        or_(
                            TemporalPermission.resource_type.is_(None),
                            TemporalPermission.resource_type == resource_type
                        )
                    )
                
                if resource_id:
                    query = query.filter(
                        or_(
                            TemporalPermission.resource_id.is_(None),
                            TemporalPermission.resource_id == resource_id
                        )
                    )
                
                temporal_permissions = query.all()
                
                # Check each temporal permission
                for temp_perm in temporal_permissions:
                    is_valid, reason = await self._evaluate_temporal_permission(
                        temp_perm, check_time, context
                    )
                    
                    if is_valid:
                        # Cache positive result for shorter time
                        result_data = {'has_permission': True, 'reason': reason}
                        await self.redis_service.cache_set(
                            cache_key, json.dumps(result_data), ttl=60
                        )
                        return True, reason
                
                # Cache negative result
                result_data = {'has_permission': False, 'reason': 'No valid temporal permission found'}
                await self.redis_service.cache_set(
                    cache_key, json.dumps(result_data), ttl=300
                )
                
                return False, "No valid temporal permission found"
                
        except Exception as e:
            logger.error(
                "Temporal permission check failed",
                error=str(e),
                user_id=user_id,
                permission=permission_name
            )
            return False, f"Error checking temporal permission: {str(e)}"
    
    async def _evaluate_temporal_permission(
        self,
        temp_perm: TemporalPermission,
        check_time: datetime,
        context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate a single temporal permission."""
        try:
            # Convert check_time to permission's timezone
            tz = pytz.timezone(temp_perm.time_zone)
            local_time = check_time.astimezone(tz)
            
            # Check usage limits
            if temp_perm.max_uses and temp_perm.current_uses >= temp_perm.max_uses:
                return False, "Maximum usage limit reached"
            
            # Check schedule type
            if temp_perm.schedule_type == 'fixed':
                return await self._check_fixed_schedule(temp_perm, check_time)
            
            elif temp_perm.schedule_type == 'recurring':
                return await self._check_recurring_schedule(temp_perm, local_time)
            
            elif temp_perm.schedule_type == 'cron':
                return await self._check_cron_schedule(temp_perm, local_time)
            
            elif temp_perm.schedule_type == 'conditional':
                return await self._check_conditional_schedule(temp_perm, local_time, context)
            
            else:
                return False, f"Unknown schedule type: {temp_perm.schedule_type}"
                
        except Exception as e:
            logger.error(
                "Temporal permission evaluation failed",
                error=str(e),
                temporal_permission_id=str(temp_perm.id)
            )
            return False, f"Error evaluating temporal permission: {str(e)}"
    
    async def _check_fixed_schedule(
        self,
        temp_perm: TemporalPermission,
        check_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """Check fixed schedule temporal permission."""
        if temp_perm.valid_from and check_time < temp_perm.valid_from:
            return False, "Permission not yet valid"
        
        if temp_perm.valid_until and check_time > temp_perm.valid_until:
            return False, "Permission has expired"
        
        return True, "Fixed schedule permission valid"
    
    async def _check_recurring_schedule(
        self,
        temp_perm: TemporalPermission,
        local_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """Check recurring schedule temporal permission."""
        # Check day of week
        if temp_perm.days_of_week:
            weekday = local_time.weekday()  # Monday = 0, Sunday = 6
            if weekday not in temp_perm.days_of_week:
                return False, "Not a valid day of week"
        
        # Check time ranges
        if temp_perm.time_ranges:
            current_time = local_time.time()
            
            for time_range in temp_perm.time_ranges:
                start_time = time.fromisoformat(time_range['start'])
                end_time = time.fromisoformat(time_range['end'])
                
                if start_time <= current_time <= end_time:
                    return True, "Recurring schedule permission valid"
            
            return False, "Not within valid time range"
        
        return True, "Recurring schedule permission valid"
    
    async def _check_cron_schedule(
        self,
        temp_perm: TemporalPermission,
        local_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """Check cron schedule temporal permission."""
        try:
            cron = croniter(temp_perm.cron_expression, local_time)
            
            # Check if current time matches cron expression
            # Allow for 1-minute window
            prev_time = cron.get_prev(datetime)
            next_time = cron.get_next(datetime)
            
            time_diff_prev = abs((local_time - prev_time).total_seconds())
            time_diff_next = abs((next_time - local_time).total_seconds())
            
            # If within 1 minute of a cron trigger time
            if min(time_diff_prev, time_diff_next) <= 60:
                # Check duration limit
                if temp_perm.max_duration_minutes:
                    if time_diff_prev <= temp_perm.max_duration_minutes * 60:
                        return True, "Cron schedule permission valid"
                    else:
                        return False, "Cron permission duration exceeded"
                
                return True, "Cron schedule permission valid"
            
            return False, "Not within cron schedule window"
            
        except Exception as e:
            logger.error("Cron schedule evaluation failed", error=str(e))
            return False, f"Cron evaluation error: {str(e)}"
    
    async def _check_conditional_schedule(
        self,
        temp_perm: TemporalPermission,
        local_time: datetime,
        context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Check conditional schedule temporal permission."""
        conditions = temp_perm.conditions or {}
        
        # Evaluate each condition
        for condition_type, condition_value in conditions.items():
            if condition_type == 'location':
                user_location = context.get('location')
                if user_location not in condition_value:
                    return False, f"Location {user_location} not allowed"
            
            elif condition_type == 'ip_range':
                user_ip = context.get('ip_address')
                if not self._check_ip_in_ranges(user_ip, condition_value):
                    return False, f"IP address {user_ip} not in allowed ranges"
            
            elif condition_type == 'device_type':
                device_type = context.get('device_type')
                if device_type not in condition_value:
                    return False, f"Device type {device_type} not allowed"
            
            elif condition_type == 'authentication_method':
                auth_method = context.get('authentication_method')
                if auth_method not in condition_value:
                    return False, f"Authentication method {auth_method} not allowed"
            
            elif condition_type == 'risk_score':
                risk_score = context.get('risk_score', 0)
                max_risk = condition_value.get('max_risk_score', 100)
                if risk_score > max_risk:
                    return False, f"Risk score {risk_score} exceeds maximum {max_risk}"
            
            elif condition_type == 'custom':
                # Custom condition evaluation
                if not await self._evaluate_custom_condition(condition_value, context):
                    return False, "Custom condition not met"
        
        return True, "Conditional schedule permission valid"
    
    def _check_ip_in_ranges(self, ip_address: str, ip_ranges: List[str]) -> bool:
        """Check if IP address is in allowed ranges."""
        try:
            import ipaddress
            
            if not ip_address:
                return False
            
            user_ip = ipaddress.ip_address(ip_address)
            
            for ip_range in ip_ranges:
                if '/' in ip_range:
                    # CIDR notation
                    network = ipaddress.ip_network(ip_range, strict=False)
                    if user_ip in network:
                        return True
                else:
                    # Single IP
                    if user_ip == ipaddress.ip_address(ip_range):
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _evaluate_custom_condition(
        self,
        condition: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate custom condition logic."""
        try:
            # Simple expression evaluator for custom conditions
            # In production, this should use a safe expression evaluator
            
            expression = condition.get('expression', '')
            variables = condition.get('variables', {})
            
            # Replace variables in expression with context values
            for var_name, var_path in variables.items():
                value = self._get_nested_value(context, var_path)
                expression = expression.replace(f'${var_name}', str(value))
            
            # Evaluate simple boolean expressions
            # This is a simplified implementation - use a proper expression evaluator in production
            if 'and' in expression:
                parts = expression.split(' and ')
                return all(self._evaluate_simple_expression(part.strip()) for part in parts)
            elif 'or' in expression:
                parts = expression.split(' or ')
                return any(self._evaluate_simple_expression(part.strip()) for part in parts)
            else:
                return self._evaluate_simple_expression(expression)
                
        except Exception as e:
            logger.error("Custom condition evaluation failed", error=str(e))
            return False
    
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
    
    def _evaluate_simple_expression(self, expression: str) -> bool:
        """Evaluate simple boolean expression."""
        try:
            # Simple comparison operators
            operators = ['>=', '<=', '==', '!=', '>', '<']
            
            for op in operators:
                if op in expression:
                    left, right = expression.split(op, 1)
                    left_val = left.strip().strip('"\'')
                    right_val = right.strip().strip('"\'')
                    
                    # Try to convert to numbers if possible
                    try:
                        left_val = float(left_val)
                        right_val = float(right_val)
                    except ValueError:
                        pass
                    
                    if op == '>=':
                        return left_val >= right_val
                    elif op == '<=':
                        return left_val <= right_val
                    elif op == '==':
                        return left_val == right_val
                    elif op == '!=':
                        return left_val != right_val
                    elif op == '>':
                        return left_val > right_val
                    elif op == '<':
                        return left_val < right_val
            
            # If no operator found, treat as boolean
            return expression.lower() in ['true', '1', 'yes']
            
        except Exception:
            return False
    
    # ============================================================================
    # TEMPORAL PERMISSION QUERIES
    # ============================================================================
    
    async def get_user_temporal_permissions(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """Get all temporal permissions for a user."""
        try:
            async with get_db_session() as session:
                query = session.query(TemporalPermission).options(
                    joinedload(TemporalPermission.permission)
                ).filter(
                    TemporalPermission.user_id == uuid.UUID(user_id),
                    TemporalPermission.is_deleted == False
                )
                
                if not include_expired:
                    current_time = datetime.utcnow()
                    query = query.filter(
                        or_(
                            TemporalPermission.valid_until.is_(None),
                            TemporalPermission.valid_until > current_time
                        )
                    )
                
                temporal_permissions = query.all()
                
                return [
                    {
                        "id": str(tp.id),
                        "permission_name": tp.permission.name,
                        "permission_display_name": tp.permission.display_name,
                        "resource_type": tp.resource_type,
                        "resource_id": tp.resource_id,
                        "schedule_type": tp.schedule_type,
                        "valid_from": tp.valid_from,
                        "valid_until": tp.valid_until,
                        "cron_expression": tp.cron_expression,
                        "time_zone": tp.time_zone,
                        "days_of_week": tp.days_of_week,
                        "time_ranges": tp.time_ranges,
                        "max_duration_minutes": tp.max_duration_minutes,
                        "max_uses": tp.max_uses,
                        "current_uses": tp.current_uses,
                        "conditions": tp.conditions,
                        "is_active": tp.is_active,
                        "created_at": tp.created_at,
                        "updated_at": tp.updated_at
                    }
                    for tp in temporal_permissions
                ]
                
        except Exception as e:
            logger.error(
                "Get user temporal permissions failed",
                error=str(e),
                user_id=user_id
            )
            return []
    
    async def get_expiring_permissions(
        self,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """Get permissions that will expire within specified hours."""
        try:
            async with get_db_session() as session:
                expiry_threshold = datetime.utcnow() + timedelta(hours=hours_ahead)
                
                temporal_permissions = session.query(TemporalPermission).options(
                    joinedload(TemporalPermission.permission),
                    joinedload(TemporalPermission.user)
                ).filter(
                    TemporalPermission.valid_until.isnot(None),
                    TemporalPermission.valid_until <= expiry_threshold,
                    TemporalPermission.valid_until > datetime.utcnow(),
                    TemporalPermission.is_active == True,
                    TemporalPermission.is_deleted == False
                ).all()
                
                return [
                    {
                        "id": str(tp.id),
                        "user_id": str(tp.user_id),
                        "user_email": tp.user.email,
                        "permission_name": tp.permission.name,
                        "permission_display_name": tp.permission.display_name,
                        "resource_type": tp.resource_type,
                        "resource_id": tp.resource_id,
                        "valid_until": tp.valid_until,
                        "hours_until_expiry": (tp.valid_until - datetime.utcnow()).total_seconds() / 3600
                    }
                    for tp in temporal_permissions
                ]
                
        except Exception as e:
            logger.error("Get expiring permissions failed", error=str(e))
            return []
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def _invalidate_temporal_permission_cache(self, user_id: str):
        """Invalidate temporal permission cache for a user."""
        patterns = [
            f"temporal_permission:{user_id}:*",
            f"permission:{user_id}:*"
        ]
        
        for pattern in patterns:
            await self.redis_service.cache_clear_pattern(pattern)


# Export commonly used items
__all__ = [
    "TemporalPermissionService"
]

