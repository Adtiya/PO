"""
Base model class for SQLAlchemy models.
Provides common fields and utilities for all models.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

Base = declarative_base()


class BaseModel(Base):
    """Base model class with common fields and methods."""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Audit fields
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    # Soft delete
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    deleted_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    # Metadata
    metadata_json = Column(
        Text,
        nullable=True,
        comment="JSON metadata for extensibility"
    )
    
    def to_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        """Convert model to dictionary."""
        exclude_fields = exclude_fields or set()
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: set = None):
        """Update model from dictionary."""
        exclude_fields = exclude_fields or {
            'id', 'created_at', 'created_by', 'is_deleted', 'deleted_at', 'deleted_by'
        }
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self, deleted_by: uuid.UUID = None):
        """Soft delete the record."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
    
    def restore(self):
        """Restore soft deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
    
    @classmethod
    def get_active_query(cls, session: Session):
        """Get query for active (non-deleted) records."""
        return session.query(cls).filter(cls.is_deleted == False)
    
    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Mixin for models that only need timestamp fields."""
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True
    )


class SoftDeleteMixin:
    """Mixin for models that need soft delete functionality."""
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        index=True
    )
    
    deleted_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    def soft_delete(self, deleted_by: uuid.UUID = None):
        """Soft delete the record."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by
    
    def restore(self):
        """Restore soft deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None


# Update Base to use the declarative base, not BaseModel
# Base = BaseModel  # This was wrong - BaseModel inherits from Base, not the other way around

