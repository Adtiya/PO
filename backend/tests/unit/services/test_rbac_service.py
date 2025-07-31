"""
Unit tests for the RBAC service.
Tests permission checking, role management, and authorization logic.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import structlog

from app.services.rbac import RBACService
from app.core.exceptions import ValidationException, AuthorizationException


class TestRBACService:
    """Test cases for RBACService."""
    
    @pytest.fixture
    def rbac_service(self, mock_redis_service):
        """Create RBAC service instance with mocked dependencies."""
        with patch('app.services.rbac.RedisService', return_value=mock_redis_service):
            return RBACService()
    
    @pytest.mark.asyncio
    async def test_check_permission_with_role_success(
        self, 
        rbac_service, 
        mock_db_session,
        mock_user_model,
        mock_role_model,
        mock_permission_model
    ):
        """Test successful permission check through role assignment."""
        # Setup mock data
        user_id = str(mock_user_model.id)
        permission_name = "document.read"
        
        # Mock database queries
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user query
            mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user_model
            
            # Mock permission query
            mock_permission_query = MagicMock()
            mock_permission_query.filter.return_value.first.return_value = mock_permission_model
            mock_db_session.query.side_effect = [
                mock_permission_query,  # Permission query
                MagicMock()  # User roles query
            ]
            
            # Mock user roles with permission
            mock_user_role = MagicMock()
            mock_user_role.role = mock_role_model
            mock_role_model.permissions = [mock_permission_model]
            
            mock_roles_query = MagicMock()
            mock_roles_query.options.return_value.filter.return_value.all.return_value = [mock_user_role]
            mock_db_session.query.side_effect = [
                mock_permission_query,
                mock_roles_query
            ]
            
            # Test permission check
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name
            )
            
            assert has_permission is True
            assert "role-based permission" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_permission_user_not_found(
        self,
        rbac_service,
        mock_db_session
    ):
        """Test permission check when user is not found."""
        user_id = str(uuid.uuid4())
        permission_name = "document.read"
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user not found
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name
            )
            
            assert has_permission is False
            assert "user not found" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_permission_permission_not_found(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model
    ):
        """Test permission check when permission is not found."""
        user_id = str(mock_user_model.id)
        permission_name = "nonexistent.permission"
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock permission not found
            mock_permission_query = MagicMock()
            mock_permission_query.filter.return_value.first.return_value = None
            mock_db_session.query.return_value = mock_permission_query
            
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name
            )
            
            assert has_permission is False
            assert "permission not found" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_permission_with_resource_success(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_permission_model,
        mock_resource_model
    ):
        """Test successful permission check with resource-specific permission."""
        user_id = str(mock_user_model.id)
        permission_name = "document.read"
        resource_type = "document"
        resource_id = "doc-123"
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock permission query
            mock_permission_query = MagicMock()
            mock_permission_query.filter.return_value.first.return_value = mock_permission_model
            
            # Mock resource permission query
            mock_resource_permission = MagicMock()
            mock_resource_permission.permission = mock_permission_model
            mock_resource_permission.resource = mock_resource_model
            
            mock_resource_query = MagicMock()
            mock_resource_query.options.return_value.filter.return_value.all.return_value = [mock_resource_permission]
            
            mock_db_session.query.side_effect = [
                mock_permission_query,
                MagicMock(),  # User roles query (empty)
                mock_resource_query  # Resource permissions query
            ]
            
            # Mock empty user roles
            mock_roles_query = MagicMock()
            mock_roles_query.options.return_value.filter.return_value.all.return_value = []
            
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name,
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            assert has_permission is True
            assert "resource-based permission" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_permission_cached_result(
        self,
        rbac_service,
        mock_redis_service
    ):
        """Test permission check returns cached result."""
        user_id = str(uuid.uuid4())
        permission_name = "document.read"
        
        # Mock cached result
        import json
        cached_result = json.dumps({
            "has_permission": True,
            "reason": "Cached permission result"
        })
        mock_redis_service.cache_get.return_value = cached_result
        
        has_permission, reason = await rbac_service.check_permission(
            user_id=user_id,
            permission_name=permission_name
        )
        
        assert has_permission is True
        assert reason == "Cached permission result"
        mock_redis_service.cache_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_permission_caches_result(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_permission_model,
        mock_redis_service
    ):
        """Test permission check caches the result."""
        user_id = str(mock_user_model.id)
        permission_name = "document.read"
        
        # Mock no cached result initially
        mock_redis_service.cache_get.return_value = None
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock permission found but no access
            mock_permission_query = MagicMock()
            mock_permission_query.filter.return_value.first.return_value = mock_permission_model
            
            # Mock empty user roles and resource permissions
            mock_empty_query = MagicMock()
            mock_empty_query.options.return_value.filter.return_value.all.return_value = []
            
            mock_db_session.query.side_effect = [
                mock_permission_query,
                mock_empty_query,  # User roles
                mock_empty_query   # Resource permissions
            ]
            
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name
            )
            
            assert has_permission is False
            mock_redis_service.cache_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_permissions_success(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_permission_model,
        mock_role_model
    ):
        """Test successful retrieval of user permissions."""
        user_id = str(mock_user_model.id)
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user query
            mock_user_query = MagicMock()
            mock_user_query.filter.return_value.first.return_value = mock_user_model
            
            # Mock user roles with permissions
            mock_user_role = MagicMock()
            mock_user_role.role = mock_role_model
            mock_role_model.permissions = [mock_permission_model]
            
            mock_roles_query = MagicMock()
            mock_roles_query.options.return_value.filter.return_value.all.return_value = [mock_user_role]
            
            # Mock resource permissions
            mock_resource_permission = MagicMock()
            mock_resource_permission.permission = mock_permission_model
            mock_resource_permission.resource_type = "document"
            mock_resource_permission.resource_id = "doc-123"
            
            mock_resource_query = MagicMock()
            mock_resource_query.options.return_value.filter.return_value.all.return_value = [mock_resource_permission]
            
            mock_db_session.query.side_effect = [
                mock_user_query,
                mock_roles_query,
                mock_resource_query
            ]
            
            permissions = await rbac_service.get_user_permissions(user_id)
            
            assert len(permissions) > 0
            assert any(p["permission_name"] == mock_permission_model.name for p in permissions)
    
    @pytest.mark.asyncio
    async def test_get_user_roles_success(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_role_model
    ):
        """Test successful retrieval of user roles."""
        user_id = str(mock_user_model.id)
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user roles
            mock_user_role = MagicMock()
            mock_user_role.role = mock_role_model
            mock_user_role.assigned_at = datetime.utcnow()
            mock_user_role.assigned_by = uuid.uuid4()
            
            mock_query = MagicMock()
            mock_query.options.return_value.filter.return_value.all.return_value = [mock_user_role]
            mock_db_session.query.return_value = mock_query
            
            roles = await rbac_service.get_user_roles(user_id)
            
            assert len(roles) == 1
            assert roles[0]["role_name"] == mock_role_model.name
    
    @pytest.mark.asyncio
    async def test_check_role_hierarchy_success(
        self,
        rbac_service,
        mock_db_session
    ):
        """Test successful role hierarchy checking."""
        parent_role_id = str(uuid.uuid4())
        child_role_id = str(uuid.uuid4())
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock role hierarchy
            mock_hierarchy = MagicMock()
            mock_hierarchy.parent_role_id = uuid.UUID(parent_role_id)
            mock_hierarchy.child_role_id = uuid.UUID(child_role_id)
            
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = mock_hierarchy
            mock_db_session.query.return_value = mock_query
            
            has_hierarchy = await rbac_service.check_role_hierarchy(
                parent_role_id, child_role_id
            )
            
            assert has_hierarchy is True
    
    @pytest.mark.asyncio
    async def test_check_role_hierarchy_not_found(
        self,
        rbac_service,
        mock_db_session
    ):
        """Test role hierarchy checking when hierarchy doesn't exist."""
        parent_role_id = str(uuid.uuid4())
        child_role_id = str(uuid.uuid4())
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock no hierarchy found
            mock_query = MagicMock()
            mock_query.filter.return_value.first.return_value = None
            mock_db_session.query.return_value = mock_query
            
            has_hierarchy = await rbac_service.check_role_hierarchy(
                parent_role_id, child_role_id
            )
            
            assert has_hierarchy is False
    
    @pytest.mark.asyncio
    async def test_get_effective_permissions_with_inheritance(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_permission_model,
        mock_role_model
    ):
        """Test getting effective permissions including inherited ones."""
        user_id = str(mock_user_model.id)
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock user with role
            mock_user_role = MagicMock()
            mock_user_role.role = mock_role_model
            mock_role_model.permissions = [mock_permission_model]
            
            # Mock parent role with additional permissions
            mock_parent_permission = MagicMock()
            mock_parent_permission.name = "admin.access"
            mock_parent_permission.display_name = "Admin Access"
            
            mock_parent_role = MagicMock()
            mock_parent_role.permissions = [mock_parent_permission]
            
            # Mock role hierarchy
            mock_hierarchy = MagicMock()
            mock_hierarchy.parent_role = mock_parent_role
            
            # Setup query mocks
            mock_user_query = MagicMock()
            mock_user_query.filter.return_value.first.return_value = mock_user_model
            
            mock_roles_query = MagicMock()
            mock_roles_query.options.return_value.filter.return_value.all.return_value = [mock_user_role]
            
            mock_hierarchy_query = MagicMock()
            mock_hierarchy_query.options.return_value.filter.return_value.all.return_value = [mock_hierarchy]
            
            mock_resource_query = MagicMock()
            mock_resource_query.options.return_value.filter.return_value.all.return_value = []
            
            mock_db_session.query.side_effect = [
                mock_user_query,
                mock_roles_query,
                mock_hierarchy_query,
                mock_resource_query
            ]
            
            permissions = await rbac_service.get_effective_permissions(user_id)
            
            assert len(permissions) >= 2  # Direct + inherited permissions
            permission_names = [p["permission_name"] for p in permissions]
            assert mock_permission_model.name in permission_names
            assert "admin.access" in permission_names
    
    @pytest.mark.asyncio
    async def test_permission_check_with_conditions(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        mock_permission_model,
        sample_context_data
    ):
        """Test permission check with conditional requirements."""
        user_id = str(mock_user_model.id)
        permission_name = "document.read"
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock permission with conditions
            mock_permission_model.conditions = [
                {
                    "condition_type": "location",
                    "condition_data": {"allowed_locations": ["office"]},
                    "operator": "and"
                }
            ]
            
            # Mock conditional permission service
            with patch('app.services.rbac.ConditionalPermissionService') as mock_conditional_service:
                mock_conditional_instance = mock_conditional_service.return_value
                mock_conditional_instance.evaluate_conditions.return_value = (True, [])
                
                # Setup other mocks
                mock_permission_query = MagicMock()
                mock_permission_query.filter.return_value.first.return_value = mock_permission_model
                
                mock_roles_query = MagicMock()
                mock_roles_query.options.return_value.filter.return_value.all.return_value = []
                
                mock_resource_query = MagicMock()
                mock_resource_query.options.return_value.filter.return_value.all.return_value = []
                
                mock_db_session.query.side_effect = [
                    mock_permission_query,
                    mock_roles_query,
                    mock_resource_query
                ]
                
                has_permission, reason = await rbac_service.check_permission(
                    user_id=user_id,
                    permission_name=permission_name,
                    context=sample_context_data
                )
                
                # Should fail because no direct permission granted
                assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_bulk_permission_check(
        self,
        rbac_service,
        mock_db_session,
        mock_user_model,
        test_permissions_list
    ):
        """Test bulk permission checking for multiple permissions."""
        user_id = str(mock_user_model.id)
        permission_names = [p["name"] for p in test_permissions_list]
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock all permissions found
            mock_permissions = []
            for perm_data in test_permissions_list:
                mock_perm = MagicMock()
                mock_perm.name = perm_data["name"]
                mock_perm.display_name = perm_data["display_name"]
                mock_permissions.append(mock_perm)
            
            mock_permission_query = MagicMock()
            mock_permission_query.filter.return_value.all.return_value = mock_permissions
            
            # Mock no user roles or resource permissions
            mock_empty_query = MagicMock()
            mock_empty_query.options.return_value.filter.return_value.all.return_value = []
            
            mock_db_session.query.side_effect = [
                mock_permission_query,
                mock_empty_query,  # User roles
                mock_empty_query   # Resource permissions
            ]
            
            results = await rbac_service.bulk_check_permissions(
                user_id=user_id,
                permission_names=permission_names
            )
            
            assert len(results) == len(permission_names)
            for result in results:
                assert "permission_name" in result
                assert "has_permission" in result
                assert "reason" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_database_error(
        self,
        rbac_service,
        database_error
    ):
        """Test error handling when database operations fail."""
        user_id = str(uuid.uuid4())
        permission_name = "document.read"
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.side_effect = database_error
            
            has_permission, reason = await rbac_service.check_permission(
                user_id=user_id,
                permission_name=permission_name
            )
            
            assert has_permission is False
            assert "error" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(
        self,
        rbac_service,
        mock_redis_service
    ):
        """Test cache invalidation for user permissions."""
        user_id = str(uuid.uuid4())
        
        await rbac_service._invalidate_user_permission_cache(user_id)
        
        # Should call cache clear with appropriate patterns
        mock_redis_service.cache_clear_pattern.assert_called()
        call_args = mock_redis_service.cache_clear_pattern.call_args_list
        
        # Check that user-specific patterns were cleared
        patterns_called = [call[0][0] for call in call_args]
        assert any(user_id in pattern for pattern in patterns_called)
    
    @pytest.mark.asyncio
    async def test_permission_inheritance_depth_limit(
        self,
        rbac_service,
        mock_db_session
    ):
        """Test that permission inheritance respects depth limits."""
        user_id = str(uuid.uuid4())
        
        with patch('app.services.rbac.get_db_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock deep role hierarchy (should be limited)
            mock_hierarchies = []
            for i in range(10):  # Create deep hierarchy
                mock_hierarchy = MagicMock()
                mock_hierarchy.parent_role = MagicMock()
                mock_hierarchy.parent_role.permissions = []
                mock_hierarchies.append(mock_hierarchy)
            
            mock_user_query = MagicMock()
            mock_user_query.filter.return_value.first.return_value = MagicMock()
            
            mock_roles_query = MagicMock()
            mock_roles_query.options.return_value.filter.return_value.all.return_value = []
            
            mock_hierarchy_query = MagicMock()
            mock_hierarchy_query.options.return_value.filter.return_value.all.return_value = mock_hierarchies
            
            mock_resource_query = MagicMock()
            mock_resource_query.options.return_value.filter.return_value.all.return_value = []
            
            mock_db_session.query.side_effect = [
                mock_user_query,
                mock_roles_query,
                mock_hierarchy_query,
                mock_resource_query
            ]
            
            permissions = await rbac_service.get_effective_permissions(user_id)
            
            # Should complete without infinite recursion
            assert isinstance(permissions, list)

