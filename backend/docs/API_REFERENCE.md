# Enterprise AI System - RBAC API Reference

**Version:** 1.0.0  
**Author:** Manus AI  
**Last Updated:** January 2024

## Table of Contents

1. [Authentication](#authentication)
2. [Role Management](#role-management)
3. [Permission Management](#permission-management)
4. [Resource Management](#resource-management)
5. [Temporal Permissions](#temporal-permissions)
6. [Conditional Permissions](#conditional-permissions)
7. [User Management](#user-management)
8. [Analytics and Reporting](#analytics-and-reporting)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

## Base URL

All API endpoints are relative to the base URL:
```
https://api.enterprise-ai.example.com/api/v1
```

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### POST /auth/login

Authenticate a user and receive access tokens.

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "secure_password",
    "mfa_code": "123456",
    "remember_me": false
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "permissions": ["document.read", "user.view"],
    "roles": ["data_analyst"]
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `423 Locked`: Account locked due to failed attempts
- `429 Too Many Requests`: Rate limit exceeded

### POST /auth/refresh

Refresh an access token using a refresh token.

**Request Body:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### POST /auth/logout

Invalidate the current session and tokens.

**Response (200 OK):**
```json
{
    "message": "Successfully logged out"
}
```

### GET /auth/me

Get current user information.

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "roles": [
        {
            "role_id": "role-uuid",
            "name": "data_analyst",
            "display_name": "Data Analyst"
        }
    ],
    "permissions": ["document.read", "user.view"],
    "last_login": "2024-01-15T14:30:00Z"
}
```

## Role Management

### POST /roles/

Create a new role.

**Required Permission:** `role.create`

**Request Body:**
```json
{
    "name": "data_scientist",
    "display_name": "Data Scientist",
    "description": "Advanced data analysis and machine learning",
    "is_system_role": false,
    "parent_roles": ["data_analyst"],
    "attributes": {
        "department": "analytics",
        "level": "senior"
    }
}
```

**Response (200 OK):**
```json
{
    "role_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Role created successfully",
    "created_at": "2024-01-15T14:30:00Z"
}
```

**Validation Rules:**
- `name`: 3-50 characters, alphanumeric and underscores only
- `display_name`: 3-100 characters
- `description`: Optional, max 500 characters
- `parent_roles`: Must be valid existing role IDs

### GET /roles/

Retrieve roles with optional filtering and pagination.

**Required Permission:** `role.read`

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `is_system_role` (boolean): Filter by system role status
- `search` (string): Search in name and description
- `parent_role_id` (UUID): Filter by parent role
- `limit` (integer): Maximum results (default: 50, max: 1000)
- `offset` (integer): Pagination offset (default: 0)
- `sort_by` (string): Sort field (name, created_at, updated_at)
- `sort_order` (string): Sort direction (asc, desc)

**Response (200 OK):**
```json
{
    "roles": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "data_scientist",
            "display_name": "Data Scientist",
            "description": "Advanced data analysis and machine learning",
            "is_system_role": false,
            "is_active": true,
            "user_count": 25,
            "permission_count": 15,
            "parent_roles": ["data_analyst"],
            "child_roles": [],
            "created_at": "2024-01-15T14:30:00Z",
            "updated_at": "2024-01-15T14:30:00Z",
            "created_by": "admin-user-id"
        }
    ],
    "total_count": 1,
    "limit": 50,
    "offset": 0,
    "has_more": false
}
```

### GET /roles/{role_id}

Retrieve a specific role by ID.

**Required Permission:** `role.read`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "data_scientist",
    "display_name": "Data Scientist",
    "description": "Advanced data analysis and machine learning",
    "is_system_role": false,
    "is_active": true,
    "attributes": {
        "department": "analytics",
        "level": "senior"
    },
    "permissions": [
        {
            "permission_id": "perm-uuid",
            "name": "data.analyze",
            "display_name": "Analyze Data",
            "assigned_at": "2024-01-15T14:30:00Z",
            "conditions": []
        }
    ],
    "parent_roles": [
        {
            "role_id": "parent-role-uuid",
            "name": "data_analyst",
            "display_name": "Data Analyst"
        }
    ],
    "child_roles": [],
    "user_assignments": 25,
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "created_by": "admin-user-id"
}
```

### PUT /roles/{role_id}

Update an existing role.

**Required Permission:** `role.update`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Request Body:**
```json
{
    "display_name": "Senior Data Scientist",
    "description": "Lead data science initiatives and mentor junior staff",
    "is_active": true,
    "attributes": {
        "department": "analytics",
        "level": "lead"
    }
}
```

**Response (200 OK):**
```json
{
    "message": "Role updated successfully",
    "updated_at": "2024-01-15T15:30:00Z"
}
```

### DELETE /roles/{role_id}

Soft delete a role (marks as deleted but preserves audit trail).

**Required Permission:** `role.delete`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Query Parameters:**
- `force` (boolean): Hard delete if true (requires `role.delete.force` permission)

**Response (200 OK):**
```json
{
    "message": "Role deleted successfully",
    "deleted_at": "2024-01-15T15:30:00Z"
}
```

### POST /roles/{role_id}/assign

Assign a role to a user.

**Required Permission:** `role.assign`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Request Body:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "valid_from": "2024-01-15T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z",
    "conditions": [
        {
            "condition_id": "condition-uuid",
            "operator": "and"
        }
    ],
    "reason": "Promotion to senior role",
    "approval_required": false
}
```

**Response (200 OK):**
```json
{
    "assignment_id": "assignment-uuid",
    "message": "Role assigned successfully",
    "assigned_at": "2024-01-15T15:30:00Z",
    "requires_approval": false
}
```

### DELETE /roles/{role_id}/users/{user_id}

Revoke a role from a user.

**Required Permission:** `role.revoke`

**Path Parameters:**
- `role_id` (UUID): Role identifier
- `user_id` (UUID): User identifier

**Query Parameters:**
- `reason` (string): Reason for revocation

**Response (200 OK):**
```json
{
    "message": "Role revoked successfully",
    "revoked_at": "2024-01-15T15:30:00Z"
}
```

### GET /roles/user/{user_id}

Get all roles assigned to a specific user.

**Required Permission:** `role.read` or `user.read.own` (if requesting own roles)

**Path Parameters:**
- `user_id` (UUID): User identifier

**Query Parameters:**
- `include_inherited` (boolean): Include roles from hierarchy (default: true)
- `include_expired` (boolean): Include expired assignments (default: false)

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "roles": [
        {
            "assignment_id": "assignment-uuid",
            "role_id": "role-uuid",
            "role_name": "data_scientist",
            "role_display_name": "Data Scientist",
            "assignment_type": "direct",
            "assigned_at": "2024-01-15T14:30:00Z",
            "assigned_by": "admin-user-id",
            "valid_from": "2024-01-15T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "is_active": true,
            "conditions": []
        }
    ],
    "total_count": 1
}
```

### POST /roles/{role_id}/permissions

Assign a permission to a role.

**Required Permission:** `role.permission.assign`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Request Body:**
```json
{
    "permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "conditions": [
        {
            "condition_id": "condition-uuid",
            "operator": "and"
        }
    ],
    "valid_from": "2024-01-15T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z"
}
```

**Response (200 OK):**
```json
{
    "assignment_id": "assignment-uuid",
    "message": "Permission assigned to role successfully",
    "assigned_at": "2024-01-15T15:30:00Z"
}
```

### GET /roles/{role_id}/permissions

Get all permissions assigned to a role.

**Required Permission:** `role.read`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Query Parameters:**
- `include_inherited` (boolean): Include permissions from parent roles (default: true)

**Response (200 OK):**
```json
{
    "role_id": "550e8400-e29b-41d4-a716-446655440000",
    "permissions": [
        {
            "assignment_id": "assignment-uuid",
            "permission_id": "perm-uuid",
            "permission_name": "data.analyze",
            "permission_display_name": "Analyze Data",
            "resource_type": "dataset",
            "assignment_type": "direct",
            "assigned_at": "2024-01-15T14:30:00Z",
            "valid_from": "2024-01-15T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "conditions": [],
            "risk_level": "medium"
        }
    ],
    "total_count": 1
}
```

### POST /roles/{role_id}/hierarchy

Create a role hierarchy relationship.

**Required Permission:** `role.hierarchy.manage`

**Path Parameters:**
- `role_id` (UUID): Parent role identifier

**Request Body:**
```json
{
    "child_role_id": "550e8400-e29b-41d4-a716-446655440000",
    "inheritance_type": "full",
    "conditions": []
}
```

**Response (200 OK):**
```json
{
    "hierarchy_id": "hierarchy-uuid",
    "message": "Role hierarchy created successfully",
    "created_at": "2024-01-15T15:30:00Z"
}
```

### GET /roles/{role_id}/hierarchy

Get role hierarchy information.

**Required Permission:** `role.read`

**Path Parameters:**
- `role_id` (UUID): Role identifier

**Query Parameters:**
- `depth` (integer): Maximum hierarchy depth to retrieve (default: 5)

**Response (200 OK):**
```json
{
    "role_id": "550e8400-e29b-41d4-a716-446655440000",
    "parent_roles": [
        {
            "role_id": "parent-role-uuid",
            "role_name": "senior_analyst",
            "role_display_name": "Senior Analyst",
            "hierarchy_level": 1,
            "inheritance_type": "full"
        }
    ],
    "child_roles": [
        {
            "role_id": "child-role-uuid",
            "role_name": "junior_scientist",
            "role_display_name": "Junior Data Scientist",
            "hierarchy_level": 1,
            "inheritance_type": "limited"
        }
    ],
    "effective_permissions": [
        {
            "permission_name": "data.read",
            "source": "inherited",
            "source_role": "senior_analyst"
        }
    ]
}
```

## Permission Management

### POST /permissions/

Create a new permission.

**Required Permission:** `permission.create`

**Request Body:**
```json
{
    "name": "document.export",
    "display_name": "Export Documents",
    "description": "Ability to export documents in various formats",
    "resource_type": "document",
    "risk_level": "medium",
    "is_system_permission": false,
    "approval_required": false,
    "attributes": {
        "category": "data_access",
        "compliance_level": "internal"
    }
}
```

**Response (200 OK):**
```json
{
    "permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Permission created successfully",
    "created_at": "2024-01-15T14:30:00Z"
}
```

### GET /permissions/

Retrieve permissions with filtering and pagination.

**Required Permission:** `permission.read`

**Query Parameters:**
- `resource_type` (string): Filter by resource type
- `risk_level` (string): Filter by risk level (low, medium, high, critical)
- `is_active` (boolean): Filter by active status
- `is_system_permission` (boolean): Filter by system permission status
- `search` (string): Search in name and description
- `category` (string): Filter by permission category
- `limit` (integer): Maximum results (default: 50, max: 1000)
- `offset` (integer): Pagination offset

**Response (200 OK):**
```json
{
    "permissions": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "document.export",
            "display_name": "Export Documents",
            "description": "Ability to export documents in various formats",
            "resource_type": "document",
            "risk_level": "medium",
            "is_system_permission": false,
            "is_active": true,
            "approval_required": false,
            "usage_count": 150,
            "role_assignments": 5,
            "user_assignments": 25,
            "created_at": "2024-01-15T14:30:00Z",
            "updated_at": "2024-01-15T14:30:00Z"
        }
    ],
    "total_count": 1,
    "limit": 50,
    "offset": 0
}
```

### GET /permissions/{permission_id}

Retrieve a specific permission by ID.

**Required Permission:** `permission.read`

**Path Parameters:**
- `permission_id` (UUID): Permission identifier

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "document.export",
    "display_name": "Export Documents",
    "description": "Ability to export documents in various formats",
    "resource_type": "document",
    "risk_level": "medium",
    "is_system_permission": false,
    "is_active": true,
    "approval_required": false,
    "attributes": {
        "category": "data_access",
        "compliance_level": "internal"
    },
    "dependencies": [
        {
            "permission_id": "dep-perm-uuid",
            "permission_name": "document.read",
            "dependency_type": "required"
        }
    ],
    "conflicts": [],
    "usage_statistics": {
        "total_checks": 1500,
        "successful_checks": 1350,
        "failed_checks": 150,
        "avg_check_time_ms": 2.5
    },
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

### POST /permissions/check

Check if a user has a specific permission.

**Required Permission:** `permission.check` or `user.permission.check.own` (for own permissions)

**Request Body:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permission_name": "document.read",
    "resource_type": "document",
    "resource_id": "doc-123",
    "context": {
        "location": "office",
        "device_type": "laptop",
        "ip_address": "192.168.1.100",
        "authentication_method": "sso",
        "risk_score": 25,
        "mfa_verified": true,
        "session_id": "session-uuid"
    },
    "check_inheritance": true,
    "check_temporal": true,
    "check_conditions": true
}
```

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permission_name": "document.read",
    "resource_type": "document",
    "resource_id": "doc-123",
    "has_permission": true,
    "reason": "User has permission through role assignment: data_analyst",
    "source": "role",
    "source_details": {
        "role_name": "data_analyst",
        "assignment_type": "direct",
        "inherited_from": null
    },
    "conditions_met": true,
    "temporal_valid": true,
    "risk_assessment": {
        "risk_level": "low",
        "risk_score": 25,
        "risk_factors": []
    },
    "check_time": "2024-01-15T14:30:00Z",
    "cache_hit": false,
    "check_duration_ms": 2.5
}
```

### POST /permissions/bulk-check

Check multiple permissions for a user in a single request.

**Required Permission:** `permission.check`

**Request Body:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permission_names": [
        "document.read",
        "document.write",
        "document.delete"
    ],
    "resource_type": "document",
    "resource_id": "doc-123",
    "context": {
        "location": "office",
        "device_type": "laptop"
    }
}
```

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "resource_type": "document",
    "resource_id": "doc-123",
    "results": [
        {
            "permission_name": "document.read",
            "has_permission": true,
            "reason": "User has permission through role assignment",
            "source": "role"
        },
        {
            "permission_name": "document.write",
            "has_permission": true,
            "reason": "User has permission through resource grant",
            "source": "resource"
        },
        {
            "permission_name": "document.delete",
            "has_permission": false,
            "reason": "User does not have required permission",
            "source": null
        }
    ],
    "check_time": "2024-01-15T14:30:00Z",
    "total_checks": 3,
    "successful_checks": 2,
    "failed_checks": 1
}
```

### GET /permissions/user/{user_id}

Get all permissions for a specific user.

**Required Permission:** `permission.read` or `user.permission.read.own` (for own permissions)

**Path Parameters:**
- `user_id` (UUID): User identifier

**Query Parameters:**
- `include_inherited` (boolean): Include inherited permissions (default: true)
- `include_resource_specific` (boolean): Include resource-specific permissions (default: true)
- `resource_type` (string): Filter by resource type
- `source` (string): Filter by permission source (role, resource, direct)

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permissions": [
        {
            "permission_id": "perm-uuid",
            "permission_name": "document.read",
            "permission_display_name": "Read Documents",
            "resource_type": "document",
            "source": "role",
            "source_details": {
                "role_name": "data_analyst",
                "role_id": "role-uuid",
                "assignment_type": "direct"
            },
            "granted_at": "2024-01-15T14:30:00Z",
            "valid_from": "2024-01-15T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "conditions": [],
            "risk_level": "low"
        }
    ],
    "total_count": 1,
    "summary": {
        "by_source": {
            "role": 15,
            "resource": 5,
            "direct": 2
        },
        "by_risk_level": {
            "low": 18,
            "medium": 3,
            "high": 1,
            "critical": 0
        }
    }
}
```

### GET /permissions/analytics

Get permission usage analytics and statistics.

**Required Permission:** `permission.analytics`

**Query Parameters:**
- `time_range` (string): Time range for analytics (1h, 24h, 7d, 30d, 90d)
- `resource_type` (string): Filter by resource type
- `risk_level` (string): Filter by risk level

**Response (200 OK):**
```json
{
    "summary": {
        "total_permissions": 150,
        "active_permissions": 145,
        "system_permissions": 25,
        "custom_permissions": 125
    },
    "usage_statistics": {
        "total_checks": 50000,
        "successful_checks": 47500,
        "failed_checks": 2500,
        "avg_check_time_ms": 2.8,
        "cache_hit_rate": 0.85
    },
    "permissions_by_resource_type": {
        "document": 60,
        "user": 30,
        "role": 20,
        "system": 25,
        "dataset": 15
    },
    "permissions_by_risk_level": {
        "low": 90,
        "medium": 40,
        "high": 15,
        "critical": 5
    },
    "most_used_permissions": [
        {
            "permission_name": "document.read",
            "usage_count": 15000,
            "success_rate": 0.98
        },
        {
            "permission_name": "user.view",
            "usage_count": 8000,
            "success_rate": 0.95
        }
    ],
    "least_used_permissions": [
        {
            "permission_name": "system.debug",
            "usage_count": 5,
            "success_rate": 1.0
        }
    ],
    "time_range": "7d",
    "generated_at": "2024-01-15T14:30:00Z"
}
```

## Resource Management

### POST /resources/

Register a new resource in the system.

**Required Permission:** `resource.create`

**Request Body:**
```json
{
    "resource_type": "document",
    "resource_id": "doc-123",
    "name": "Financial Report Q4 2024",
    "description": "Quarterly financial analysis and projections",
    "owner_id": "550e8400-e29b-41d4-a716-446655440000",
    "parent_resource_id": "project-456",
    "security_level": "confidential",
    "attributes": {
        "department": "finance",
        "classification": "confidential",
        "project": "q4-analysis",
        "retention_period": "7_years"
    },
    "tags": ["finance", "quarterly", "report", "2024"],
    "metadata": {
        "file_size": 2048576,
        "file_type": "pdf",
        "created_by_system": "financial_reporting"
    }
}
```

**Response (200 OK):**
```json
{
    "resource_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Resource registered successfully",
    "registered_at": "2024-01-15T14:30:00Z"
}
```

### GET /resources/{resource_type}/{resource_id}

Retrieve resource information and metadata.

**Required Permission:** `resource.read` or resource-specific read permission

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "resource_type": "document",
    "resource_id": "doc-123",
    "name": "Financial Report Q4 2024",
    "description": "Quarterly financial analysis and projections",
    "owner_id": "owner-user-uuid",
    "owner_name": "John Smith",
    "parent_resource": {
        "resource_type": "project",
        "resource_id": "project-456",
        "name": "Q4 Analysis Project"
    },
    "child_resources": [
        {
            "resource_type": "document",
            "resource_id": "doc-124",
            "name": "Supporting Data"
        }
    ],
    "security_level": "confidential",
    "attributes": {
        "department": "finance",
        "classification": "confidential",
        "project": "q4-analysis"
    },
    "tags": ["finance", "quarterly", "report"],
    "permissions": [
        {
            "permission_name": "document.read",
            "user_count": 15,
            "role_count": 3
        }
    ],
    "access_statistics": {
        "total_accesses": 150,
        "unique_users": 25,
        "last_accessed": "2024-01-15T13:45:00Z"
    },
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

### PUT /resources/{resource_type}/{resource_id}

Update resource information and metadata.

**Required Permission:** `resource.update` or resource-specific update permission

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Request Body:**
```json
{
    "name": "Financial Report Q4 2024 - Final",
    "description": "Final quarterly financial analysis and projections",
    "security_level": "confidential",
    "attributes": {
        "status": "final",
        "approved_by": "cfo-user-uuid"
    },
    "tags": ["finance", "quarterly", "report", "final"]
}
```

**Response (200 OK):**
```json
{
    "message": "Resource updated successfully",
    "updated_at": "2024-01-15T15:30:00Z"
}
```

### DELETE /resources/{resource_type}/{resource_id}

Delete a resource and its associated permissions.

**Required Permission:** `resource.delete` or resource-specific delete permission

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Query Parameters:**
- `cascade` (boolean): Delete child resources (default: false)
- `force` (boolean): Force delete even with active permissions (default: false)

**Response (200 OK):**
```json
{
    "message": "Resource deleted successfully",
    "deleted_at": "2024-01-15T15:30:00Z",
    "cascade_deleted": 3
}
```

### POST /resources/{resource_type}/{resource_id}/permissions/grant

Grant a permission to a user on a specific resource.

**Required Permission:** `resource.permission.grant` or resource ownership

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Request Body:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permission_name": "document.read",
    "grant_type": "direct",
    "valid_from": "2024-01-15T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z",
    "conditions": [
        {
            "condition_id": "condition-uuid",
            "operator": "and"
        }
    ],
    "reason": "Project collaboration access",
    "notify_user": true
}
```

**Response (200 OK):**
```json
{
    "grant_id": "grant-uuid",
    "message": "Permission granted successfully",
    "granted_at": "2024-01-15T15:30:00Z",
    "notification_sent": true
}
```

### DELETE /resources/{resource_type}/{resource_id}/permissions/revoke

Revoke a permission from a user on a specific resource.

**Required Permission:** `resource.permission.revoke` or resource ownership

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Query Parameters:**
- `user_id` (UUID): User identifier
- `permission_name` (string): Permission name
- `reason` (string): Reason for revocation

**Response (200 OK):**
```json
{
    "message": "Permission revoked successfully",
    "revoked_at": "2024-01-15T15:30:00Z"
}
```

### GET /resources/{resource_type}/{resource_id}/permissions/user/{user_id}

Get all permissions a user has on a specific resource.

**Required Permission:** `resource.permission.read` or resource ownership

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier
- `user_id` (UUID): User identifier

**Response (200 OK):**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "resource_type": "document",
    "resource_id": "doc-123",
    "permissions": [
        {
            "permission_name": "document.read",
            "permission_display_name": "Read Document",
            "grant_type": "direct",
            "granted_at": "2024-01-15T14:30:00Z",
            "granted_by": "owner-user-uuid",
            "valid_from": "2024-01-15T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "conditions": [],
            "is_active": true
        }
    ],
    "inherited_permissions": [
        {
            "permission_name": "document.view",
            "source": "parent_resource",
            "source_resource": "project-456"
        }
    ],
    "effective_permissions": [
        "document.read",
        "document.view"
    ]
}
```

### GET /resources/{resource_type}/{resource_id}/hierarchy

Get resource hierarchy information.

**Required Permission:** `resource.read`

**Path Parameters:**
- `resource_type` (string): Type of resource
- `resource_id` (string): Resource identifier

**Query Parameters:**
- `depth` (integer): Maximum hierarchy depth (default: 5)
- `direction` (string): Hierarchy direction (up, down, both) (default: both)

**Response (200 OK):**
```json
{
    "resource_type": "document",
    "resource_id": "doc-123",
    "ancestors": [
        {
            "resource_type": "project",
            "resource_id": "project-456",
            "name": "Q4 Analysis Project",
            "level": 1
        },
        {
            "resource_type": "portfolio",
            "resource_id": "portfolio-789",
            "name": "Financial Portfolio",
            "level": 2
        }
    ],
    "descendants": [
        {
            "resource_type": "attachment",
            "resource_id": "att-001",
            "name": "Supporting Chart",
            "level": 1
        }
    ],
    "siblings": [
        {
            "resource_type": "document",
            "resource_id": "doc-124",
            "name": "Supporting Data"
        }
    ]
}
```

## Temporal Permissions

### POST /temporal-permissions/

Create a new temporal permission.

**Required Permission:** `temporal_permission.create`

**Request Body:**
```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "permission_id": "permission-uuid",
    "resource_type": "document",
    "resource_id": "doc-123",
    "schedule_type": "recurring",
    "valid_from": "2024-01-15T00:00:00Z",
    "valid_until": "2024-12-31T23:59:59Z",
    "time_zone": "America/New_York",
    "days_of_week": [0, 1, 2, 3, 4],
    "time_ranges": [
        {
            "start": "09:00",
            "end": "17:00"
        }
    ],
    "cron_expression": null,
    "max_duration_minutes": 480,
    "max_uses": 100,
    "conditions": {
        "location": ["office", "home"],
        "device_type": ["laptop", "desktop"]
    },
    "approval_required": false,
    "reason": "Business hours access for project work"
}
```

**Response (200 OK):**
```json
{
    "temporal_permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Temporal permission created successfully",
    "created_at": "2024-01-15T14:30:00Z",
    "next_valid_time": "2024-01-16T09:00:00Z"
}
```

### GET /temporal-permissions/

Retrieve temporal permissions with filtering.

**Required Permission:** `temporal_permission.read`

**Query Parameters:**
- `user_id` (UUID): Filter by user
- `permission_id` (UUID): Filter by permission
- `resource_type` (string): Filter by resource type
- `schedule_type` (string): Filter by schedule type
- `is_active` (boolean): Filter by active status
- `expiring_within` (string): Filter by expiration time (1h, 24h, 7d, 30d)

**Response (200 OK):**
```json
{
    "temporal_permissions": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user-uuid",
            "user_name": "John Doe",
            "permission_name": "document.read",
            "resource_type": "document",
            "resource_id": "doc-123",
            "schedule_type": "recurring",
            "valid_from": "2024-01-15T00:00:00Z",
            "valid_until": "2024-12-31T23:59:59Z",
            "time_zone": "America/New_York",
            "days_of_week": [0, 1, 2, 3, 4],
            "time_ranges": [
                {
                    "start": "09:00",
                    "end": "17:00"
                }
            ],
            "current_uses": 25,
            "max_uses": 100,
            "is_currently_valid": true,
            "next_valid_time": "2024-01-16T09:00:00Z",
            "next_invalid_time": "2024-01-15T17:00:00Z",
            "created_at": "2024-01-15T14:30:00Z"
        }
    ],
    "total_count": 1
}
```

### POST /temporal-permissions/check

Check if a temporal permission is valid at a specific time.

**Required Permission:** `temporal_permission.check`

**Request Body:**
```json
{
    "temporal_permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "check_time": "2024-01-15T14:30:00Z",
    "time_zone": "America/New_York",
    "context": {
        "location": "office",
        "device_type": "laptop"
    }
}
```

**Response (200 OK):**
```json
{
    "temporal_permission_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_valid": true,
    "check_time": "2024-01-15T14:30:00Z",
    "reason": "Within valid time range and conditions met",
    "time_constraints": {
        "within_date_range": true,
        "within_time_range": true,
        "within_day_of_week": true,
        "within_usage_limit": true
    },
    "conditions_met": true,
    "remaining_uses": 75,
    "next_valid_time": "2024-01-16T09:00:00Z",
    "expires_at": "2024-01-15T17:00:00Z"
}
```

### GET /temporal-permissions/expiring

Get temporal permissions that will expire within a specified timeframe.

**Required Permission:** `temporal_permission.read`

**Query Parameters:**
- `within` (string): Time range (1h, 24h, 7d, 30d) (default: 24h)
- `user_id` (UUID): Filter by user
- `permission_name` (string): Filter by permission
- `include_expired` (boolean): Include already expired permissions (default: false)

**Response (200 OK):**
```json
{
    "expiring_permissions": [
        {
            "temporal_permission_id": "temp-perm-uuid",
            "user_id": "user-uuid",
            "user_name": "John Doe",
            "permission_name": "document.read",
            "resource_type": "document",
            "resource_id": "doc-123",
            "expires_at": "2024-01-15T17:00:00Z",
            "time_until_expiry": "2h 30m",
            "auto_renewal": false,
            "notification_sent": true
        }
    ],
    "total_count": 1,
    "within_timeframe": "24h"
}
```

### PUT /temporal-permissions/{temporal_permission_id}

Update an existing temporal permission.

**Required Permission:** `temporal_permission.update`

**Path Parameters:**
- `temporal_permission_id` (UUID): Temporal permission identifier

**Request Body:**
```json
{
    "valid_until": "2025-01-31T23:59:59Z",
    "max_uses": 200,
    "time_ranges": [
        {
            "start": "08:00",
            "end": "18:00"
        }
    ],
    "conditions": {
        "location": ["office", "home", "branch_office"]
    }
}
```

**Response (200 OK):**
```json
{
    "message": "Temporal permission updated successfully",
    "updated_at": "2024-01-15T15:30:00Z",
    "next_valid_time": "2024-01-16T08:00:00Z"
}
```

### DELETE /temporal-permissions/{temporal_permission_id}

Delete a temporal permission.

**Required Permission:** `temporal_permission.delete`

**Path Parameters:**
- `temporal_permission_id` (UUID): Temporal permission identifier

**Response (200 OK):**
```json
{
    "message": "Temporal permission deleted successfully",
    "deleted_at": "2024-01-15T15:30:00Z"
}
```

## Conditional Permissions

### POST /conditional-permissions/conditions

Create a new permission condition.

**Required Permission:** `condition.create`

**Request Body:**
```json
{
    "name": "office_access_only",
    "display_name": "Office Access Only",
    "description": "Restricts access to office locations during business hours",
    "condition_type": "location",
    "condition_data": {
        "allowed_locations": ["office", "branch_office"],
        "blocked_locations": ["home", "public"]
    },
    "operator": "and",
    "is_global": true,
    "risk_level": "medium",
    "approval_required": false,
    "attributes": {
        "category": "location_security",
        "compliance_requirement": "data_protection"
    }
}
```

**Response (200 OK):**
```json
{
    "condition_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Condition created successfully",
    "created_at": "2024-01-15T14:30:00Z"
}
```

### GET /conditional-permissions/conditions

Retrieve permission conditions with filtering.

**Required Permission:** `condition.read`

**Query Parameters:**
- `condition_type` (string): Filter by condition type
- `risk_level` (string): Filter by risk level
- `is_global` (boolean): Filter by global conditions
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name and description

**Response (200 OK):**
```json
{
    "conditions": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "office_access_only",
            "display_name": "Office Access Only",
            "description": "Restricts access to office locations",
            "condition_type": "location",
            "condition_data": {
                "allowed_locations": ["office", "branch_office"]
            },
            "operator": "and",
            "is_global": true,
            "risk_level": "medium",
            "usage_count": 25,
            "success_rate": 0.95,
            "created_at": "2024-01-15T14:30:00Z"
        }
    ],
    "total_count": 1
}
```

### POST /conditional-permissions/evaluate

Evaluate a set of conditions against provided context.

**Required Permission:** `condition.evaluate`

**Request Body:**
```json
{
    "conditions": [
        {
            "condition_id": "550e8400-e29b-41d4-a716-446655440000",
            "operator": "and"
        },
        {
            "condition_id": "another-condition-uuid",
            "operator": "or"
        }
    ],
    "context": {
        "location": "office",
        "ip_address": "192.168.1.100",
        "device_type": "laptop",
        "authentication_method": "sso",
        "risk_score": 25,
        "mfa_verified": true,
        "mfa_timestamp": "2024-01-15T14:25:00Z",
        "user_agent": "Mozilla/5.0...",
        "session_id": "session-uuid",
        "time_of_access": "2024-01-15T14:30:00Z"
    },
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**
```json
{
    "evaluation_result": true,
    "conditions_met": true,
    "failed_conditions": [],
    "evaluation_details": [
        {
            "condition_id": "condition-uuid",
            "condition_name": "office_access_only",
            "result": true,
            "reason": "User location matches allowed locations",
            "operator": "and"
        }
    ],
    "risk_assessment": {
        "overall_risk_score": 25,
        "risk_level": "low",
        "risk_factors": []
    },
    "evaluation_time": "2024-01-15T14:30:00Z",
    "evaluation_duration_ms": 1.2
}
```

### GET /conditional-permissions/conditions/{condition_id}

Retrieve a specific condition by ID.

**Required Permission:** `condition.read`

**Path Parameters:**
- `condition_id` (UUID): Condition identifier

**Response (200 OK):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "office_access_only",
    "display_name": "Office Access Only",
    "description": "Restricts access to office locations during business hours",
    "condition_type": "location",
    "condition_data": {
        "allowed_locations": ["office", "branch_office"],
        "blocked_locations": ["home", "public"],
        "validation_rules": {
            "require_exact_match": true,
            "case_sensitive": false
        }
    },
    "operator": "and",
    "is_global": true,
    "risk_level": "medium",
    "approval_required": false,
    "usage_statistics": {
        "total_evaluations": 1000,
        "successful_evaluations": 950,
        "failed_evaluations": 50,
        "avg_evaluation_time_ms": 1.5
    },
    "associated_permissions": [
        {
            "permission_name": "document.read",
            "usage_count": 500
        }
    ],
    "created_at": "2024-01-15T14:30:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

### POST /conditional-permissions/test

Test condition evaluation with sample data.

**Required Permission:** `condition.test`

**Request Body:**
```json
{
    "condition_definition": {
        "condition_type": "time_range",
        "condition_data": {
            "time_ranges": [
                {
                    "start": "09:00",
                    "end": "17:00"
                }
            ],
            "time_zone": "America/New_York",
            "days_of_week": [0, 1, 2, 3, 4]
        }
    },
    "test_contexts": [
        {
            "time_of_access": "2024-01-15T14:30:00Z",
            "time_zone": "America/New_York"
        },
        {
            "time_of_access": "2024-01-15T20:30:00Z",
            "time_zone": "America/New_York"
        }
    ]
}
```

**Response (200 OK):**
```json
{
    "test_results": [
        {
            "context_index": 0,
            "result": true,
            "reason": "Within business hours",
            "evaluation_time_ms": 0.8
        },
        {
            "context_index": 1,
            "result": false,
            "reason": "Outside business hours",
            "evaluation_time_ms": 0.6
        }
    ],
    "summary": {
        "total_tests": 2,
        "passed_tests": 1,
        "failed_tests": 1,
        "success_rate": 0.5,
        "avg_evaluation_time_ms": 0.7
    }
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information in JSON format.

### Error Response Format

```json
{
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "User does not have required permission",
        "details": {
            "required_permission": "role.create",
            "user_permissions": ["role.read", "user.view"],
            "resource_type": "role",
            "resource_id": null
        },
        "timestamp": "2024-01-15T14:30:00Z",
        "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
        "path": "/api/v1/roles/",
        "method": "POST"
    }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request validation failed |
| 401 | `AUTHENTICATION_REQUIRED` | Authentication token required |
| 401 | `INVALID_TOKEN` | Authentication token is invalid or expired |
| 403 | `PERMISSION_DENIED` | User lacks required permission |
| 403 | `RESOURCE_ACCESS_DENIED` | Access to specific resource denied |
| 404 | `RESOURCE_NOT_FOUND` | Requested resource does not exist |
| 409 | `RESOURCE_CONFLICT` | Resource already exists or conflict detected |
| 422 | `UNPROCESSABLE_ENTITY` | Request data is invalid |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### Validation Errors

Validation errors include detailed field-level information:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {
            "field_errors": [
                {
                    "field": "name",
                    "message": "Name must be between 3 and 50 characters",
                    "code": "LENGTH_CONSTRAINT"
                },
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "code": "FORMAT_INVALID"
                }
            ]
        }
    }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability.

### Rate Limit Headers

All responses include rate limit information in headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
X-RateLimit-Window: 3600
```

### Rate Limit Tiers

| User Type | Requests per Hour | Burst Limit |
|-----------|-------------------|-------------|
| Anonymous | 100 | 10 |
| Authenticated | 1000 | 50 |
| Premium | 5000 | 100 |
| Admin | 10000 | 200 |

### Rate Limit Exceeded Response

```json
{
    "error": {
        "code": "RATE_LIMIT_EXCEEDED",
        "message": "Rate limit exceeded",
        "details": {
            "limit": 1000,
            "window_seconds": 3600,
            "retry_after_seconds": 300
        }
    }
}
```

---

*This API reference is maintained by the Manus AI development team. For additional support or questions, please refer to the main documentation or contact the system administrators.*

