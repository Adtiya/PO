"""
Integration tests for RBAC API endpoints.
Tests the complete flow from HTTP request to database operations.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestRBACEndpoints:
    """Integration tests for RBAC API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def mock_auth_middleware(self):
        """Mock authentication middleware."""
        with patch('app.middleware.auth.verify_token') as mock_verify:
            mock_verify.return_value = {
                "user_id": str(uuid.uuid4()),
                "email": "test@example.com",
                "roles": ["user"]
            }
            yield mock_verify
    
    def test_create_role_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        sample_role_data
    ):
        """Test successful role creation."""
        with patch('app.services.role_manager.RoleManagerService.create_role') as mock_create:
            mock_create.return_value = str(uuid.uuid4())
            
            role_data = {
                "name": sample_role_data["name"],
                "display_name": sample_role_data["display_name"],
                "description": sample_role_data["description"]
            }
            
            response = client.post(
                "/api/v1/roles/",
                headers=auth_headers,
                json=role_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "role_id" in data
            assert data["message"] == "Role created successfully"
    
    def test_create_role_validation_error(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test role creation with validation error."""
        invalid_role_data = {
            "name": "",  # Invalid empty name
            "display_name": "Test Role"
        }
        
        response = client.post(
            "/api/v1/roles/",
            headers=auth_headers,
            json=invalid_role_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_roles_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_roles_list
    ):
        """Test successful roles retrieval."""
        with patch('app.services.role_manager.RoleManagerService.get_roles') as mock_get:
            mock_get.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    "name": role["name"],
                    "display_name": role["display_name"],
                    "description": role["description"],
                    "is_system_role": False,
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                for role in test_roles_list
            ]
            
            response = client.get(
                "/api/v1/roles/",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(test_roles_list)
            assert all("name" in role for role in data)
    
    def test_get_role_by_id_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        sample_role_data
    ):
        """Test successful role retrieval by ID."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.get_role') as mock_get:
            mock_get.return_value = {
                "id": role_id,
                **sample_role_data
            }
            
            response = client.get(
                f"/api/v1/roles/{role_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == role_id
            assert data["name"] == sample_role_data["name"]
    
    def test_get_role_by_id_not_found(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test role retrieval when role not found."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.get_role') as mock_get:
            mock_get.return_value = None
            
            response = client.get(
                f"/api/v1/roles/{role_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 404
    
    def test_update_role_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful role update."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.update_role') as mock_update:
            mock_update.return_value = True
            
            update_data = {
                "display_name": "Updated Role Name",
                "description": "Updated description"
            }
            
            response = client.put(
                f"/api/v1/roles/{role_id}",
                headers=auth_headers,
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Role updated successfully"
    
    def test_delete_role_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful role deletion."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.delete_role') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(
                f"/api/v1/roles/{role_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Role deleted successfully"
    
    def test_assign_role_to_user_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful role assignment to user."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.assign_role_to_user') as mock_assign:
            mock_assign.return_value = True
            
            assignment_data = {
                "user_id": str(uuid.uuid4()),
                "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            response = client.post(
                f"/api/v1/roles/{role_id}/assign",
                headers=auth_headers,
                json=assignment_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Role assigned successfully"
    
    def test_revoke_role_from_user_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful role revocation from user."""
        role_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.revoke_role_from_user') as mock_revoke:
            mock_revoke.return_value = True
            
            response = client.delete(
                f"/api/v1/roles/{role_id}/users/{user_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Role revoked successfully"
    
    def test_assign_permission_to_role_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful permission assignment to role."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.assign_permission_to_role') as mock_assign:
            mock_assign.return_value = True
            
            assignment_data = {
                "permission_id": str(uuid.uuid4()),
                "conditions": []
            }
            
            response = client.post(
                f"/api/v1/roles/{role_id}/permissions",
                headers=auth_headers,
                json=assignment_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Permission assigned to role successfully"
    
    def test_get_role_permissions_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_permissions_list
    ):
        """Test successful retrieval of role permissions."""
        role_id = str(uuid.uuid4())
        
        with patch('app.services.role_manager.RoleManagerService.get_role_permissions') as mock_get:
            mock_get.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    "name": perm["name"],
                    "display_name": perm["display_name"],
                    "resource_type": perm["resource_type"],
                    "assigned_at": datetime.utcnow(),
                    "conditions": []
                }
                for perm in test_permissions_list
            ]
            
            response = client.get(
                f"/api/v1/roles/{role_id}/permissions",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(test_permissions_list)
    
    def test_create_permission_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        sample_permission_data
    ):
        """Test successful permission creation."""
        with patch('app.services.role_manager.RoleManagerService.create_permission') as mock_create:
            mock_create.return_value = str(uuid.uuid4())
            
            permission_data = {
                "name": sample_permission_data["name"],
                "display_name": sample_permission_data["display_name"],
                "description": sample_permission_data["description"],
                "resource_type": sample_permission_data["resource_type"]
            }
            
            response = client.post(
                "/api/v1/permissions/",
                headers=auth_headers,
                json=permission_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "permission_id" in data
            assert data["message"] == "Permission created successfully"
    
    def test_get_permissions_with_filters(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_permissions_list
    ):
        """Test permissions retrieval with filters."""
        with patch('app.services.role_manager.RoleManagerService.get_permissions') as mock_get:
            filtered_permissions = [p for p in test_permissions_list if p["resource_type"] == "document"]
            mock_get.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    **perm,
                    "is_system_permission": False,
                    "risk_level": "medium",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                for perm in filtered_permissions
            ]
            
            response = client.get(
                "/api/v1/permissions/?resource_type=document",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert all(perm["resource_type"] == "document" for perm in data)
    
    def test_check_user_permission_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test successful user permission check."""
        with patch('app.services.rbac.RBACService.check_permission') as mock_check:
            mock_check.return_value = (True, "User has permission through role assignment")
            
            check_data = {
                "user_id": str(uuid.uuid4()),
                "permission_name": "document.read",
                "resource_type": "document",
                "resource_id": "doc-123",
                "context": {
                    "location": "office",
                    "device_type": "laptop"
                }
            }
            
            response = client.post(
                "/api/v1/permissions/check",
                headers=auth_headers,
                json=check_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["has_permission"] is True
            assert "reason" in data
    
    def test_check_user_permission_denied(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test user permission check when access is denied."""
        with patch('app.services.rbac.RBACService.check_permission') as mock_check:
            mock_check.return_value = (False, "User does not have required permission")
            
            check_data = {
                "user_id": str(uuid.uuid4()),
                "permission_name": "admin.access",
                "context": {}
            }
            
            response = client.post(
                "/api/v1/permissions/check",
                headers=auth_headers,
                json=check_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["has_permission"] is False
            assert "reason" in data
    
    def test_bulk_permission_check_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_permissions_list
    ):
        """Test successful bulk permission check."""
        with patch('app.services.rbac.RBACService.bulk_check_permissions') as mock_bulk_check:
            permission_names = [p["name"] for p in test_permissions_list]
            mock_bulk_check.return_value = [
                {
                    "permission_name": perm_name,
                    "has_permission": i % 2 == 0,  # Alternate true/false
                    "reason": f"Test reason for {perm_name}"
                }
                for i, perm_name in enumerate(permission_names)
            ]
            
            check_data = {
                "user_id": str(uuid.uuid4()),
                "permission_names": permission_names,
                "context": {}
            }
            
            response = client.post(
                "/api/v1/permissions/bulk-check",
                headers=auth_headers,
                json=check_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == len(permission_names)
            assert all("permission_name" in result for result in data["results"])
    
    def test_get_user_permissions_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_permissions_list
    ):
        """Test successful retrieval of user permissions."""
        user_id = str(uuid.uuid4())
        
        with patch('app.services.rbac.RBACService.get_user_permissions') as mock_get:
            mock_get.return_value = [
                {
                    "permission_name": perm["name"],
                    "permission_display_name": perm["display_name"],
                    "resource_type": perm["resource_type"],
                    "source": "role",
                    "role_name": "test_role",
                    "granted_at": datetime.utcnow()
                }
                for perm in test_permissions_list
            ]
            
            response = client.get(
                f"/api/v1/permissions/user/{user_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(test_permissions_list)
            assert all("permission_name" in perm for perm in data)
    
    def test_get_user_roles_success(
        self,
        client,
        auth_headers,
        mock_auth_middleware,
        test_roles_list
    ):
        """Test successful retrieval of user roles."""
        user_id = str(uuid.uuid4())
        
        with patch('app.services.rbac.RBACService.get_user_roles') as mock_get:
            mock_get.return_value = [
                {
                    "role_name": role["name"],
                    "role_display_name": role["display_name"],
                    "assigned_at": datetime.utcnow(),
                    "assigned_by": str(uuid.uuid4()),
                    "valid_until": None,
                    "is_active": True
                }
                for role in test_roles_list
            ]
            
            response = client.get(
                f"/api/v1/roles/user/{user_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(test_roles_list)
            assert all("role_name" in role for role in data)
    
    def test_role_hierarchy_operations(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test role hierarchy creation and management."""
        parent_role_id = str(uuid.uuid4())
        child_role_id = str(uuid.uuid4())
        
        # Test create hierarchy
        with patch('app.services.role_manager.RoleManagerService.create_role_hierarchy') as mock_create:
            mock_create.return_value = True
            
            hierarchy_data = {
                "child_role_id": child_role_id
            }
            
            response = client.post(
                f"/api/v1/roles/{parent_role_id}/hierarchy",
                headers=auth_headers,
                json=hierarchy_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Role hierarchy created successfully"
        
        # Test get hierarchy
        with patch('app.services.role_manager.RoleManagerService.get_role_hierarchy') as mock_get:
            mock_get.return_value = {
                "parent_roles": [],
                "child_roles": [
                    {
                        "role_id": child_role_id,
                        "role_name": "child_role",
                        "role_display_name": "Child Role",
                        "created_at": datetime.utcnow()
                    }
                ]
            }
            
            response = client.get(
                f"/api/v1/roles/{parent_role_id}/hierarchy",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "parent_roles" in data
            assert "child_roles" in data
    
    def test_permission_analytics(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test permission analytics endpoint."""
        with patch('app.services.rbac.RBACService.get_permission_analytics') as mock_analytics:
            mock_analytics.return_value = {
                "total_permissions": 100,
                "active_permissions": 95,
                "permissions_by_resource_type": {
                    "document": 40,
                    "user": 25,
                    "role": 15,
                    "system": 20
                },
                "permissions_by_risk_level": {
                    "low": 60,
                    "medium": 30,
                    "high": 8,
                    "critical": 2
                },
                "most_assigned_permissions": [
                    {"name": "document.read", "assignment_count": 150},
                    {"name": "document.write", "assignment_count": 75},
                    {"name": "user.view", "assignment_count": 50}
                ]
            }
            
            response = client.get(
                "/api/v1/permissions/analytics",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_permissions" in data
            assert "permissions_by_resource_type" in data
            assert "permissions_by_risk_level" in data
    
    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/roles/")
        assert response.status_code == 401
        
        response = client.post("/api/v1/roles/", json={"name": "test"})
        assert response.status_code == 401
    
    def test_insufficient_permissions(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test access with insufficient permissions."""
        with patch('app.middleware.rbac.check_permission_in_endpoint') as mock_check:
            mock_check.return_value = False
            
            response = client.post(
                "/api/v1/roles/",
                headers=auth_headers,
                json={"name": "test_role", "display_name": "Test Role"}
            )
            
            assert response.status_code == 403
    
    def test_rate_limiting(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test rate limiting on API endpoints."""
        with patch('app.middleware.rate_limit.RateLimitMiddleware.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False  # Rate limit exceeded
            
            response = client.get(
                "/api/v1/roles/",
                headers=auth_headers
            )
            
            assert response.status_code == 429  # Too Many Requests
    
    def test_input_validation_edge_cases(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test input validation with edge cases."""
        # Test with very long strings
        long_string = "a" * 1000
        
        response = client.post(
            "/api/v1/roles/",
            headers=auth_headers,
            json={
                "name": long_string,
                "display_name": "Test Role"
            }
        )
        
        assert response.status_code == 422  # Validation error
        
        # Test with special characters
        response = client.post(
            "/api/v1/roles/",
            headers=auth_headers,
            json={
                "name": "test@#$%^&*()",
                "display_name": "Test Role"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_concurrent_requests(
        self,
        client,
        auth_headers,
        mock_auth_middleware
    ):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/api/v1/roles/", headers=auth_headers)
            results.append(response.status_code)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed (assuming proper mocking)
        assert len(results) == 10
        assert all(status in [200, 401, 403] for status in results)  # Expected status codes

