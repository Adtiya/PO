"""
Resource-based RBAC models for the Enterprise AI System.
Includes Resource, ResourcePermission, and advanced authorization models.
"""

import uuid
from datetime import datetime, time
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Time
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Resource(BaseModel):
    """Resource model for resource-based access control."""
    
    __tablename__ = "resources"
    
    # Basic resource information
    name = Column(
        String(200),
        nullable=False,
        index=True
    )
    
    resource_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource (e.g., 'document', 'project', 'api_endpoint')"
    )
    
    resource_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="External ID of the resource"
    )
    
    # Resource hierarchy
    parent_resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resources.id"),
        nullable=True,
        index=True
    )
    
    path = Column(
        String(1000),
        nullable=True,
        index=True,
        comment="Hierarchical path of the resource"
    )
    
    # Resource metadata
    display_name = Column(
        String(300),
        nullable=True
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    # Ownership
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    # Status and properties
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Security classification
    security_level = Column(
        ENUM(
            'public', 'internal', 'confidential', 'restricted', 'top_secret',
            name='security_level_enum'
        ),
        default='internal',
        nullable=False,
        index=True
    )
    
    # Resource attributes for policy evaluation
    attributes = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Resource attributes for policy-based access control"
    )
    
    # Tags for categorization
    tags = Column(
        ARRAY(String(50)),
        nullable=True,
        default=[],
        comment="Tags for resource categorization"
    )
    
    # Relationships
    parent_resource = relationship(
        "Resource",
        remote_side="Resource.id",
        back_populates="child_resources"
    )
    
    child_resources = relationship(
        "Resource",
        back_populates="parent_resource",
        cascade="all, delete-orphan"
    )
    
    owner = relationship(
        "User",
        foreign_keys=[owner_id]
    )
    
    resource_permissions = relationship(
        "ResourcePermission",
        back_populates="resource",
        cascade="all, delete-orphan"
    )
    
    user_resource_permissions = relationship(
        "UserResourcePermission",
        back_populates="resource",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('resource_type', 'resource_id', name='uq_resource_type_id'),
        Index('idx_resources_type_active', 'resource_type', 'is_active'),
        Index('idx_resources_owner_type', 'owner_id', 'resource_type'),
        Index('idx_resources_security_level', 'security_level'),
        Index('idx_resources_path', 'path'),
        Index('idx_resources_tags', 'tags', postgresql_using='gin'),
    )
    
    def get_full_path(self) -> str:
        """Get full hierarchical path of the resource."""
        if self.path:
            return self.path
        
        if self.parent_resource:
            parent_path = self.parent_resource.get_full_path()
            return f"{parent_path}/{self.name}"
        
        return self.name
    
    def is_child_of(self, parent_resource: 'Resource') -> bool:
        """Check if this resource is a child of the given parent."""
        if not self.parent_resource_id:
            return False
        
        if self.parent_resource_id == parent_resource.id:
            return True
        
        if self.parent_resource:
            return self.parent_resource.is_child_of(parent_resource)
        
        return False


class ResourcePermission(BaseModel):
    """Permissions that can be granted on resources."""
    
    __tablename__ = "resource_permissions"
    
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Permission configuration
    is_inheritable = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this permission is inherited by child resources"
    )
    
    is_delegatable = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether users can delegate this permission to others"
    )
    
    # Conditions and constraints
    conditions = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Conditions under which this permission applies"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Relationships
    resource = relationship(
        "Resource",
        back_populates="resource_permissions"
    )
    
    permission = relationship(
        "Permission",
        back_populates="resource_permissions"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('resource_id', 'permission_id', name='uq_resource_permission'),
        Index('idx_resource_permissions_resource', 'resource_id', 'is_active'),
        Index('idx_resource_permissions_permission', 'permission_id', 'is_active'),
    )


class UserResourcePermission(BaseModel):
    """Direct permissions granted to users on specific resources."""
    
    __tablename__ = "user_resource_permissions"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    resource_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Grant metadata
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    granted_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    # Permission type
    grant_type = Column(
        ENUM(
            'direct', 'inherited', 'delegated', 'temporary',
            name='grant_type_enum'
        ),
        default='direct',
        nullable=False,
        index=True
    )
    
    # Temporal constraints
    valid_from = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    valid_until = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Conditions and constraints
    conditions = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Conditions under which this permission is active"
    )
    
    # Delegation chain
    delegated_from = Column(
        UUID(as_uuid=True),
        ForeignKey("user_resource_permissions.id"),
        nullable=True,
        index=True,
        comment="Original permission this was delegated from"
    )
    
    # Relationships
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_resource_permissions"
    )
    
    resource = relationship(
        "Resource",
        back_populates="user_resource_permissions"
    )
    
    permission = relationship(
        "Permission",
        back_populates="user_resource_permissions"
    )
    
    granted_by_user = relationship(
        "User",
        foreign_keys=[granted_by]
    )
    
    delegated_from_permission = relationship(
        "UserResourcePermission",
        remote_side="UserResourcePermission.id"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'resource_id', 'permission_id', name='uq_user_resource_permission'),
        Index('idx_user_resource_permissions_user', 'user_id', 'is_active'),
        Index('idx_user_resource_permissions_resource', 'resource_id', 'is_active'),
        Index('idx_user_resource_permissions_permission', 'permission_id', 'is_active'),
        Index('idx_user_resource_permissions_validity', 'valid_from', 'valid_until'),
        Index('idx_user_resource_permissions_grant_type', 'grant_type'),
        CheckConstraint('valid_until IS NULL OR valid_until > valid_from', name='check_valid_dates'),
    )
    
    @hybrid_property
    def is_valid(self) -> bool:
        """Check if permission grant is currently valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            (self.valid_until is None or self.valid_until > now)
        )


class PermissionCondition(BaseModel):
    """Conditions that must be met for permissions to be active."""
    
    __tablename__ = "permission_conditions"
    
    # Reference to permission grant
    user_resource_permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_resource_permissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    role_permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("role_permissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Condition details
    condition_type = Column(
        ENUM(
            'time_based', 'location_based', 'attribute_based', 
            'approval_based', 'quota_based', 'custom',
            name='condition_type_enum'
        ),
        nullable=False,
        index=True
    )
    
    condition_name = Column(
        String(100),
        nullable=False
    )
    
    condition_expression = Column(
        Text,
        nullable=False,
        comment="Expression or rule that defines the condition"
    )
    
    condition_parameters = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Parameters for condition evaluation"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Evaluation metadata
    last_evaluated_at = Column(
        DateTime,
        nullable=True
    )
    
    last_evaluation_result = Column(
        Boolean,
        nullable=True
    )
    
    evaluation_count = Column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            '(user_resource_permission_id IS NOT NULL AND role_permission_id IS NULL) OR '
            '(user_resource_permission_id IS NULL AND role_permission_id IS NOT NULL)',
            name='check_single_permission_reference'
        ),
        Index('idx_permission_conditions_type', 'condition_type', 'is_active'),
    )


class TemporalPermission(BaseModel):
    """Time-based permission constraints and schedules."""
    
    __tablename__ = "temporal_permissions"
    
    # Reference to permission grant
    user_resource_permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_resource_permissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    role_permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("role_permissions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Time constraints
    time_zone = Column(
        String(50),
        default='UTC',
        nullable=False
    )
    
    # Daily time windows
    start_time = Column(
        Time,
        nullable=True,
        comment="Daily start time for permission"
    )
    
    end_time = Column(
        Time,
        nullable=True,
        comment="Daily end time for permission"
    )
    
    # Days of week (0=Monday, 6=Sunday)
    allowed_days = Column(
        ARRAY(Integer),
        nullable=True,
        comment="Days of week when permission is active"
    )
    
    # Date ranges
    start_date = Column(
        DateTime,
        nullable=True,
        comment="Start date for permission validity"
    )
    
    end_date = Column(
        DateTime,
        nullable=True,
        comment="End date for permission validity"
    )
    
    # Recurring patterns
    recurrence_pattern = Column(
        String(100),
        nullable=True,
        comment="Cron-like pattern for complex recurrence"
    )
    
    # Exclusions
    excluded_dates = Column(
        ARRAY(DateTime),
        nullable=True,
        comment="Specific dates when permission is not active"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            '(user_resource_permission_id IS NOT NULL AND role_permission_id IS NULL) OR '
            '(user_resource_permission_id IS NULL AND role_permission_id IS NOT NULL)',
            name='check_single_permission_reference'
        ),
        CheckConstraint(
            'start_time IS NULL OR end_time IS NULL OR start_time < end_time',
            name='check_time_order'
        ),
        CheckConstraint(
            'start_date IS NULL OR end_date IS NULL OR start_date < end_date',
            name='check_date_order'
        ),
        Index('idx_temporal_permissions_dates', 'start_date', 'end_date'),
        Index('idx_temporal_permissions_times', 'start_time', 'end_time'),
    )
    
    def is_active_at(self, check_time: datetime) -> bool:
        """Check if permission is active at the given time."""
        if not self.is_active:
            return False
        
        # Check date range
        if self.start_date and check_time < self.start_date:
            return False
        if self.end_date and check_time > self.end_date:
            return False
        
        # Check excluded dates
        if self.excluded_dates:
            check_date = check_time.date()
            for excluded_date in self.excluded_dates:
                if excluded_date.date() == check_date:
                    return False
        
        # Check day of week
        if self.allowed_days:
            weekday = check_time.weekday()  # 0=Monday, 6=Sunday
            if weekday not in self.allowed_days:
                return False
        
        # Check time of day
        if self.start_time and self.end_time:
            check_time_only = check_time.time()
            if not (self.start_time <= check_time_only <= self.end_time):
                return False
        
        return True

