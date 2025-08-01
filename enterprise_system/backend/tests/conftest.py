"""
Pytest configuration and shared fixtures for the Enterprise AI System tests.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock
import structlog

# Configure test logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.testing.LogCapture(),
    ],
    wrapper_class=structlog.testing.TestingLoggerFactory(),
    logger_factory=structlog.testing.TestingLoggerFactory(),
    cache_logger_on_first_use=True,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.filter_by.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.scalar.return_value = 0
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing."""
    redis_service = AsyncMock()
    redis_service.cache_get.return_value = None
    redis_service.cache_set.return_value = True
    redis_service.cache_clear_pattern.return_value = True
    return redis_service


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_deleted": False,
        "attributes": {
            "department": "engineering",
            "level": 5,
            "location": "office"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_role_data():
    """Sample role data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "test_role",
        "display_name": "Test Role",
        "description": "A test role for unit testing",
        "is_system_role": False,
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_permission_data():
    """Sample permission data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "test.permission",
        "display_name": "Test Permission",
        "description": "A test permission for unit testing",
        "resource_type": "document",
        "is_system_permission": False,
        "risk_level": "medium",
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_resource_data():
    """Sample resource data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "resource_type": "document",
        "resource_id": "doc-123",
        "name": "Test Document",
        "description": "A test document for unit testing",
        "owner_id": str(uuid.uuid4()),
        "parent_resource_id": None,
        "security_level": "internal",
        "attributes": {
            "classification": "internal",
            "department": "engineering",
            "project": "test-project"
        },
        "tags": ["test", "document"],
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_temporal_permission_data():
    """Sample temporal permission data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "permission_id": str(uuid.uuid4()),
        "resource_type": "document",
        "resource_id": "doc-123",
        "schedule_type": "fixed",
        "valid_from": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(hours=24),
        "time_zone": "UTC",
        "days_of_week": [],
        "time_ranges": [],
        "max_duration_minutes": None,
        "max_uses": None,
        "current_uses": 0,
        "conditions": {},
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_condition_data():
    """Sample condition data for testing."""
    return {
        "id": str(uuid.uuid4()),
        "name": "test_condition",
        "display_name": "Test Condition",
        "description": "A test condition for unit testing",
        "condition_type": "location",
        "condition_data": {
            "allowed_locations": ["office", "home"]
        },
        "is_global": True,
        "risk_level": "medium",
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def sample_context_data():
    """Sample context data for testing."""
    return {
        "ip_address": "192.168.1.100",
        "location": "office",
        "device_type": "laptop",
        "authentication_method": "sso",
        "risk_score": 25,
        "mfa_verified": True,
        "mfa_timestamp": datetime.utcnow(),
        "user_agent": "Mozilla/5.0 (Test Browser)",
        "session_id": str(uuid.uuid4())
    }


@pytest.fixture
def mock_user_model(sample_user_data):
    """Mock User model instance."""
    user = MagicMock()
    for key, value in sample_user_data.items():
        setattr(user, key, value)
    user.id = uuid.UUID(sample_user_data["id"])
    return user


@pytest.fixture
def mock_role_model(sample_role_data):
    """Mock Role model instance."""
    role = MagicMock()
    for key, value in sample_role_data.items():
        setattr(role, key, value)
    role.id = uuid.UUID(sample_role_data["id"])
    return role


@pytest.fixture
def mock_permission_model(sample_permission_data):
    """Mock Permission model instance."""
    permission = MagicMock()
    for key, value in sample_permission_data.items():
        setattr(permission, key, value)
    permission.id = uuid.UUID(sample_permission_data["id"])
    return permission


@pytest.fixture
def mock_resource_model(sample_resource_data):
    """Mock Resource model instance."""
    resource = MagicMock()
    for key, value in sample_resource_data.items():
        setattr(resource, key, value)
    resource.id = uuid.UUID(sample_resource_data["id"])
    return resource


@pytest.fixture
def mock_temporal_permission_model(sample_temporal_permission_data):
    """Mock TemporalPermission model instance."""
    temporal_permission = MagicMock()
    for key, value in sample_temporal_permission_data.items():
        setattr(temporal_permission, key, value)
    temporal_permission.id = uuid.UUID(sample_temporal_permission_data["id"])
    temporal_permission.user_id = uuid.UUID(sample_temporal_permission_data["user_id"])
    temporal_permission.permission_id = uuid.UUID(sample_temporal_permission_data["permission_id"])
    return temporal_permission


@pytest.fixture
def mock_condition_model(sample_condition_data):
    """Mock PermissionCondition model instance."""
    condition = MagicMock()
    for key, value in sample_condition_data.items():
        setattr(condition, key, value)
    condition.id = uuid.UUID(sample_condition_data["id"])
    return condition


# Test data collections
@pytest.fixture
def test_permissions_list():
    """List of test permissions for bulk operations."""
    return [
        {
            "name": "document.read",
            "display_name": "Read Documents",
            "resource_type": "document"
        },
        {
            "name": "document.write",
            "display_name": "Write Documents",
            "resource_type": "document"
        },
        {
            "name": "user.manage",
            "display_name": "Manage Users",
            "resource_type": "user"
        },
        {
            "name": "role.assign",
            "display_name": "Assign Roles",
            "resource_type": "role"
        }
    ]


@pytest.fixture
def test_roles_list():
    """List of test roles for bulk operations."""
    return [
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Can view documents"
        },
        {
            "name": "editor",
            "display_name": "Editor",
            "description": "Can edit documents"
        },
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full system access"
        }
    ]


@pytest.fixture
def test_conditions_list():
    """List of test conditions for bulk operations."""
    return [
        {
            "name": "office_only",
            "condition_type": "location",
            "condition_data": {"allowed_locations": ["office"]}
        },
        {
            "name": "business_hours",
            "condition_type": "time_range",
            "condition_data": {
                "time_ranges": [{"start": "09:00", "end": "17:00"}]
            }
        },
        {
            "name": "low_risk_only",
            "condition_type": "risk_score",
            "condition_data": {"max_risk_score": 30}
        }
    ]


# Async test helpers
@pytest.fixture
def async_mock():
    """Create an async mock function."""
    async def _async_mock(*args, **kwargs):
        return MagicMock()
    return _async_mock


@pytest.fixture
def async_context_manager():
    """Create an async context manager mock."""
    class AsyncContextManager:
        async def __aenter__(self):
            return MagicMock()
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    return AsyncContextManager()


# Performance test fixtures
@pytest.fixture
def performance_test_data():
    """Generate large datasets for performance testing."""
    return {
        "users": [
            {
                "id": str(uuid.uuid4()),
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "department": f"dept{i % 10}",
                "level": i % 5 + 1
            }
            for i in range(1000)
        ],
        "permissions": [
            {
                "id": str(uuid.uuid4()),
                "name": f"permission.{i}",
                "resource_type": f"resource{i % 20}"
            }
            for i in range(500)
        ],
        "resources": [
            {
                "id": str(uuid.uuid4()),
                "resource_type": f"resource{i % 20}",
                "resource_id": f"res-{i}",
                "security_level": ["public", "internal", "confidential"][i % 3]
            }
            for i in range(2000)
        ]
    }


# Error simulation fixtures
@pytest.fixture
def database_error():
    """Simulate database errors."""
    from sqlalchemy.exc import SQLAlchemyError
    return SQLAlchemyError("Database connection failed")


@pytest.fixture
def redis_error():
    """Simulate Redis errors."""
    from redis.exceptions import RedisError
    return RedisError("Redis connection failed")


@pytest.fixture
def validation_error():
    """Simulate validation errors."""
    from app.core.exceptions import ValidationException
    return ValidationException("Validation failed")


@pytest.fixture
def authorization_error():
    """Simulate authorization errors."""
    from app.core.exceptions import AuthorizationException
    return AuthorizationException("Access denied")


# Test environment configuration
@pytest.fixture(autouse=True)
def test_environment():
    """Configure test environment."""
    import os
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    yield
    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

