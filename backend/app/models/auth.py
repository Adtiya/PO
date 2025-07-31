"""
Authentication and authorization models for the Enterprise AI System.
Includes Role, Permission, and relationship models for RBAC.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class Role(BaseModel):
    """Role model for RBAC system."""
    
    __tablename__ = "roles"
    
    # Basic role information
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    display_name = Column(
        String(200),
        nullable=False
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    # Role properties
    is_system_role = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Hierarchy support
    parent_role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=True,
        index=True
    )
    
    level = Column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )
    
    # Role metadata
    role_type = Column(
        ENUM(
            'system', 'organizational', 'functional', 'project',
            name='role_type_enum'
        ),
        default='functional',
        nullable=False,
        index=True
    )
    
    scope = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Scope of the role (e.g., 'global', 'department', 'project')"
    )
    
    # Configuration
    max_users = Column(
        Integer,
        nullable=True,
        comment="Maximum number of users that can have this role"
    )
    
    auto_assign_conditions = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Conditions for automatic role assignment"
    )
    
    # Relationships
    parent_role = relationship(
        "Role",
        remote_side="Role.id",
        back_populates="child_roles"
    )
    
    child_roles = relationship(
        "Role",
        back_populates="parent_role",
        cascade="all, delete-orphan"
    )
    
    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    role_permissions = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    
    parent_hierarchies = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.parent_role_id",
        back_populates="parent_role",
        cascade="all, delete-orphan"
    )
    
    child_hierarchies = relationship(
        "RoleHierarchy",
        foreign_keys="RoleHierarchy.child_role_id",
        back_populates="child_role",
        cascade="all, delete-orphan"
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_roles_name_active', 'name', 'is_active'),
        Index('idx_roles_type_scope', 'role_type', 'scope'),
        Index('idx_roles_parent_level', 'parent_role_id', 'level'),
        CheckConstraint('level >= 0', name='check_role_level_positive'),
        CheckConstraint('max_users IS NULL OR max_users > 0', name='check_max_users_positive'),
    )
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate role name format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Role name must contain only letters, numbers, hyphens, and underscores")
        return name.lower()
    
    def get_all_permissions(self, session) -> List['Permission']:
        """Get all permissions for this role including inherited ones."""
        from sqlalchemy.orm import joinedload
        
        # Direct permissions
        direct_permissions = session.query(Permission).join(
            RolePermission
        ).filter(
            RolePermission.role_id == self.id,
            RolePermission.is_active == True
        ).all()
        
        # Inherited permissions from parent roles
        inherited_permissions = []
        if self.parent_role_id:
            parent_role = session.query(Role).get(self.parent_role_id)
            if parent_role:
                inherited_permissions = parent_role.get_all_permissions(session)
        
        # Combine and deduplicate
        all_permissions = {p.id: p for p in direct_permissions + inherited_permissions}
        return list(all_permissions.values())
    
    def has_permission(self, session, permission_name: str) -> bool:
        """Check if role has a specific permission."""
        permissions = self.get_all_permissions(session)
        return any(p.name == permission_name for p in permissions)


class Permission(BaseModel):
    """Permission model for RBAC system."""
    
    __tablename__ = "permissions"
    
    # Basic permission information
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    display_name = Column(
        String(200),
        nullable=False
    )
    
    description = Column(
        Text,
        nullable=True
    )
    
    # Permission categorization
    category = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Permission category (e.g., 'user', 'content', 'admin')"
    )
    
    resource_type = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of resource this permission applies to"
    )
    
    action = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Action this permission allows (e.g., 'read', 'write', 'delete')"
    )
    
    # Permission properties
    is_system_permission = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Risk and compliance
    risk_level = Column(
        ENUM(
            'low', 'medium', 'high', 'critical',
            name='risk_level_enum'
        ),
        default='low',
        nullable=False,
        index=True
    )
    
    requires_approval = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Dependencies
    depends_on_permissions = Column(
        JSONB,
        nullable=True,
        default=[],
        comment="List of permission IDs this permission depends on"
    )
    
    conflicts_with_permissions = Column(
        JSONB,
        nullable=True,
        default=[],
        comment="List of permission IDs this permission conflicts with"
    )
    
    # Relationships
    role_permissions = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )
    
    resource_permissions = relationship(
        "ResourcePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )
    
    user_resource_permissions = relationship(
        "UserResourcePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_permissions_name_active', 'name', 'is_active'),
        Index('idx_permissions_category_action', 'category', 'action'),
        Index('idx_permissions_resource_action', 'resource_type', 'action'),
        Index('idx_permissions_risk_level', 'risk_level'),
    )
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate permission name format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            raise ValueError("Permission name must contain only letters, numbers, dots, hyphens, and underscores")
        return name.lower()


class UserRole(BaseModel):
    """Association between users and roles with additional metadata."""
    
    __tablename__ = "user_roles"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Assignment metadata
    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    assigned_at = Column(
        DateTime,
        default=datetime.utcnow,
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
    
    # Context and conditions
    context = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Context in which this role applies (e.g., 'project:123')"
    )
    
    conditions = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Additional conditions for role activation"
    )
    
    # Approval workflow
    approval_status = Column(
        ENUM(
            'pending', 'approved', 'rejected', 'auto_approved',
            name='approval_status_enum'
        ),
        default='auto_approved',
        nullable=False,
        index=True
    )
    
    approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    approved_at = Column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_roles"
    )
    
    role = relationship(
        "Role",
        back_populates="user_roles"
    )
    
    assigned_by_user = relationship(
        "User",
        foreign_keys=[assigned_by]
    )
    
    approved_by_user = relationship(
        "User",
        foreign_keys=[approved_by]
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'context', name='uq_user_role_context'),
        Index('idx_user_roles_user_active', 'user_id', 'is_active'),
        Index('idx_user_roles_role_active', 'role_id', 'is_active'),
        Index('idx_user_roles_validity', 'valid_from', 'valid_until'),
        Index('idx_user_roles_approval', 'approval_status'),
        CheckConstraint('valid_until IS NULL OR valid_until > valid_from', name='check_valid_dates'),
    )
    
    @hybrid_property
    def is_valid(self) -> bool:
        """Check if role assignment is currently valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.approval_status == 'approved' and
            self.valid_from <= now and
            (self.valid_until is None or self.valid_until > now)
        )


class RolePermission(BaseModel):
    """Association between roles and permissions with conditions."""
    
    __tablename__ = "role_permissions"
    
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
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
        comment="Conditions under which this permission is granted"
    )
    
    resource_constraints = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Constraints on resources this permission applies to"
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
    
    # Relationships
    role = relationship(
        "Role",
        back_populates="role_permissions"
    )
    
    permission = relationship(
        "Permission",
        back_populates="role_permissions"
    )
    
    granted_by_user = relationship(
        "User",
        foreign_keys=[granted_by]
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
        Index('idx_role_permissions_role_active', 'role_id', 'is_active'),
        Index('idx_role_permissions_permission_active', 'permission_id', 'is_active'),
        Index('idx_role_permissions_validity', 'valid_from', 'valid_until'),
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


class RoleHierarchy(BaseModel):
    """Role hierarchy relationships for inheritance."""
    
    __tablename__ = "role_hierarchies"
    
    parent_role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    child_role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Hierarchy metadata
    depth = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Depth of inheritance (1 = direct child)"
    )
    
    inheritance_type = Column(
        ENUM(
            'full', 'partial', 'conditional',
            name='inheritance_type_enum'
        ),
        default='full',
        nullable=False
    )
    
    # Conditions for inheritance
    inheritance_conditions = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Conditions under which inheritance applies"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Relationships
    parent_role = relationship(
        "Role",
        foreign_keys=[parent_role_id],
        back_populates="parent_hierarchies"
    )
    
    child_role = relationship(
        "Role",
        foreign_keys=[child_role_id],
        back_populates="child_hierarchies"
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('parent_role_id', 'child_role_id', name='uq_role_hierarchy'),
        Index('idx_role_hierarchies_parent', 'parent_role_id', 'is_active'),
        Index('idx_role_hierarchies_child', 'child_role_id', 'is_active'),
        Index('idx_role_hierarchies_depth', 'depth'),
        CheckConstraint('parent_role_id != child_role_id', name='check_no_self_reference'),
        CheckConstraint('depth > 0', name='check_positive_depth'),
    )



class UserSession(BaseModel):
    """User session tracking for authentication."""
    
    __tablename__ = "user_sessions"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    session_token = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Session metadata
    ip_address = Column(
        String(45),  # IPv6 support
        nullable=True,
        index=True
    )
    
    user_agent = Column(
        Text,
        nullable=True
    )
    
    # Session timing
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Session status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Device information
    device_info = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Device and browser information"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="user_sessions"
    )
    
    # Constraints
    __table_args__ = (
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_expires', 'expires_at'),
        Index('idx_user_sessions_activity', 'last_activity_at'),
        CheckConstraint('expires_at > created_at', name='check_session_expiry'),
    )
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()


class PasswordResetToken(BaseModel):
    """Password reset token for secure password recovery."""
    
    __tablename__ = "password_reset_tokens"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    token = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Token timing
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Token status
    is_used = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    used_at = Column(
        DateTime,
        nullable=True
    )
    
    # Security metadata
    ip_address = Column(
        String(45),
        nullable=True,
        index=True
    )
    
    used_ip_address = Column(
        String(45),
        nullable=True
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="password_reset_tokens"
    )
    
    # Constraints
    __table_args__ = (
        Index('idx_password_reset_user', 'user_id', 'is_used'),
        Index('idx_password_reset_expires', 'expires_at'),
        CheckConstraint('expires_at > created_at', name='check_token_expiry'),
    )
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @hybrid_property
    def is_valid(self) -> bool:
        """Check if token is valid for use."""
        return not self.is_used and not self.is_expired


class EmailVerificationToken(BaseModel):
    """Email verification token for account activation."""
    
    __tablename__ = "email_verification_tokens"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    token = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Token timing
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    # Token status
    is_used = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    used_at = Column(
        DateTime,
        nullable=True
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="email_verification_tokens"
    )
    
    # Constraints
    __table_args__ = (
        Index('idx_email_verification_user', 'user_id', 'is_used'),
        Index('idx_email_verification_expires', 'expires_at'),
        CheckConstraint('expires_at > created_at', name='check_token_expiry'),
    )
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @hybrid_property
    def is_valid(self) -> bool:
        """Check if token is valid for use."""
        return not self.is_used and not self.is_expired

