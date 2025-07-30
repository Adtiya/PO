"""
User models for the Enterprise AI System.
Includes User, UserProfile, and UserSession models.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .base import BaseModel


class User(BaseModel):
    """User model with authentication and profile information."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    username = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )
    
    password_hash = Column(
        String(255),
        nullable=False
    )
    
    # Profile fields
    first_name = Column(
        String(100),
        nullable=False
    )
    
    last_name = Column(
        String(100),
        nullable=False
    )
    
    display_name = Column(
        String(200),
        nullable=True
    )
    
    # Status fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    # Activity tracking
    last_login_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    last_activity_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    login_count = Column(
        Integer,
        default=0,
        nullable=False
    )
    
    # Security fields
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False
    )
    
    locked_until = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    password_changed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Verification tokens
    email_verification_token = Column(
        String(255),
        nullable=True,
        index=True
    )
    
    email_verification_expires = Column(
        DateTime,
        nullable=True
    )
    
    password_reset_token = Column(
        String(255),
        nullable=True,
        index=True
    )
    
    password_reset_expires = Column(
        DateTime,
        nullable=True
    )
    
    # Preferences
    timezone = Column(
        String(50),
        default="UTC",
        nullable=False
    )
    
    language = Column(
        String(10),
        default="en",
        nullable=False
    )
    
    preferences = Column(
        JSONB,
        nullable=True,
        default={}
    )
    
    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    user_resource_permissions = relationship(
        "UserResourcePermission",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email_active', 'email', 'is_active'),
        Index('idx_users_username_active', 'username', 'is_active'),
        Index('idx_users_last_activity', 'last_activity_at'),
        Index('idx_users_verification_token', 'email_verification_token'),
        Index('idx_users_reset_token', 'password_reset_token'),
    )
    
    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @hybrid_property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return email.lower()
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format."""
        if username is None:
            return None
        
        import re
        if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', username):
            raise ValueError("Username must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
        return username.lower()
    
    def set_password(self, password: str):
        """Set user password with hashing."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.password_hash = pwd_context.hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def verify_password(self, password: str) -> bool:
        """Verify user password."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.password_hash)
    
    def lock_account(self, duration_minutes: int = 30):
        """Lock user account for specified duration."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self):
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_login_attempt(self, success: bool, ip_address: str = None):
        """Record login attempt."""
        if success:
            self.last_login_at = datetime.utcnow()
            self.login_count += 1
            self.failed_login_attempts = 0
            self.locked_until = None
        else:
            self.failed_login_attempts += 1
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.lock_account(30)  # 30 minutes
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()


class UserProfile(BaseModel):
    """Extended user profile information."""
    
    __tablename__ = "user_profiles"
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Contact information
    phone = Column(
        String(20),
        nullable=True
    )
    
    address = Column(
        Text,
        nullable=True
    )
    
    city = Column(
        String(100),
        nullable=True
    )
    
    state = Column(
        String(100),
        nullable=True
    )
    
    country = Column(
        String(100),
        nullable=True
    )
    
    postal_code = Column(
        String(20),
        nullable=True
    )
    
    # Professional information
    job_title = Column(
        String(200),
        nullable=True
    )
    
    company = Column(
        String(200),
        nullable=True
    )
    
    department = Column(
        String(200),
        nullable=True
    )
    
    manager_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )
    
    # Personal information
    date_of_birth = Column(
        DateTime,
        nullable=True
    )
    
    bio = Column(
        Text,
        nullable=True
    )
    
    avatar_url = Column(
        String(500),
        nullable=True
    )
    
    # Social links
    social_links = Column(
        JSONB,
        nullable=True,
        default={}
    )
    
    # Custom fields
    custom_fields = Column(
        JSONB,
        nullable=True,
        default={}
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="profile"
    )
    
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
        remote_side="User.id"
    )


class UserSession(BaseModel):
    """User session tracking for authentication and security."""
    
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
    
    refresh_token = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )
    
    # Session information
    ip_address = Column(
        INET,
        nullable=True,
        index=True
    )
    
    user_agent = Column(
        Text,
        nullable=True
    )
    
    device_info = Column(
        JSONB,
        nullable=True,
        default={}
    )
    
    # Session lifecycle
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True
    )
    
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    
    # Security flags
    is_remember_me = Column(
        Boolean,
        default=False,
        nullable=False
    )
    
    logout_at = Column(
        DateTime,
        nullable=True
    )
    
    logout_reason = Column(
        String(100),
        nullable=True
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="sessions"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_expires', 'expires_at'),
        Index('idx_user_sessions_activity', 'last_activity_at'),
        Index('idx_user_sessions_ip', 'ip_address'),
    )
    
    @hybrid_property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, duration_hours: int = 24):
        """Extend session expiration."""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        self.last_activity_at = datetime.utcnow()
    
    def invalidate(self, reason: str = "logout"):
        """Invalidate session."""
        self.is_active = False
        self.logout_at = datetime.utcnow()
        self.logout_reason = reason

