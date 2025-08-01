#!/bin/bash

# Enterprise AI System - RBAC API Testing with cURL
# =================================================
# 
# This script provides comprehensive cURL examples for testing
# all aspects of the dynamic RBAC system.
#
# Author: Manus AI
# Version: 1.0.0
# Date: 2025-07-31

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_TOKEN=""
USER_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Helper function to make API calls
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local token="$4"
    local description="$5"
    
    echo
    log_info "Testing: $description"
    echo "Endpoint: $method $endpoint"
    
    if [ -n "$data" ]; then
        echo "Payload: $data"
    fi
    
    local curl_cmd="curl -s -X $method"
    
    if [ -n "$token" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    fi
    
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$BASE_URL$endpoint'"
    
    echo "Command: $curl_cmd"
    echo "Response:"
    
    local response=$(eval $curl_cmd)
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    
    echo "----------------------------------------"
}

# Test 1: System Health Check
test_health_check() {
    log_info "🏥 Test 1: System Health Check"
    
    api_call "GET" "/health" "" "" "Check system health"
    api_call "GET" "/api/v1/" "" "" "Check API info"
}

# Test 2: User Registration and Authentication
test_user_auth() {
    log_info "👤 Test 2: User Registration and Authentication"
    
    # Register admin user
    local admin_data='{
        "username": "test_admin",
        "email": "admin@test.com",
        "password": "AdminPass123!",
        "first_name": "Test",
        "last_name": "Admin",
        "role": "system_admin"
    }'
    
    api_call "POST" "/api/v1/auth/register" "$admin_data" "" "Register admin user"
    
    # Register regular user
    local user_data='{
        "username": "test_user",
        "email": "user@test.com", 
        "password": "UserPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "basic_user"
    }'
    
    api_call "POST" "/api/v1/auth/register" "$user_data" "" "Register regular user"
    
    # Login admin
    local admin_login='{
        "username": "test_admin",
        "password": "AdminPass123!"
    }'
    
    log_info "Logging in admin user..."
    local admin_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$admin_login" \
        "$BASE_URL/api/v1/auth/login")
    
    ADMIN_TOKEN=$(echo "$admin_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
    
    if [ -n "$ADMIN_TOKEN" ]; then
        log_success "Admin token obtained: ${ADMIN_TOKEN:0:20}..."
    else
        log_error "Failed to obtain admin token"
        echo "Response: $admin_response"
    fi
    
    # Login regular user
    local user_login='{
        "username": "test_user",
        "password": "UserPass123!"
    }'
    
    log_info "Logging in regular user..."
    local user_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$user_login" \
        "$BASE_URL/api/v1/auth/login")
    
    USER_TOKEN=$(echo "$user_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
    
    if [ -n "$USER_TOKEN" ]; then
        log_success "User token obtained: ${USER_TOKEN:0:20}..."
    else
        log_error "Failed to obtain user token"
        echo "Response: $user_response"
    fi
}

# Test 3: Role Management
test_role_management() {
    log_info "👥 Test 3: Role Management"
    
    # Create new role
    local role_data='{
        "name": "data_analyst",
        "display_name": "Data Analyst",
        "description": "Analyst role with data access permissions",
        "level": 3,
        "permissions": [
            "read_data",
            "create_reports",
            "view_analytics"
        ]
    }'
    
    api_call "POST" "/api/v1/roles" "$role_data" "$ADMIN_TOKEN" "Create data analyst role"
    
    # List all roles
    api_call "GET" "/api/v1/roles" "" "$ADMIN_TOKEN" "List all roles"
    
    # Get specific role
    api_call "GET" "/api/v1/roles/data_analyst" "" "$ADMIN_TOKEN" "Get data analyst role details"
    
    # Update role
    local role_update='{
        "description": "Updated: Data analyst with enhanced permissions",
        "permissions": [
            "read_data",
            "create_reports", 
            "view_analytics",
            "export_data"
        ]
    }'
    
    api_call "PUT" "/api/v1/roles/data_analyst" "$role_update" "$ADMIN_TOKEN" "Update data analyst role"
}

# Test 4: Permission Management
test_permission_management() {
    log_info "🔐 Test 4: Permission Management"
    
    # Create custom permission
    local permission_data='{
        "name": "access_financial_data",
        "display_name": "Access Financial Data",
        "description": "Permission to access financial datasets",
        "resource_type": "dataset",
        "actions": ["read", "export"]
    }'
    
    api_call "POST" "/api/v1/permissions" "$permission_data" "$ADMIN_TOKEN" "Create custom permission"
    
    # List all permissions
    api_call "GET" "/api/v1/permissions" "" "$ADMIN_TOKEN" "List all permissions"
    
    # Assign permission to user
    local permission_assignment='{
        "user_id": "test_user",
        "permission": "access_financial_data",
        "resource": "financial_reports",
        "granted_by": "test_admin"
    }'
    
    api_call "POST" "/api/v1/permissions/assign" "$permission_assignment" "$ADMIN_TOKEN" "Assign permission to user"
    
    # Check user permissions
    api_call "GET" "/api/v1/users/test_user/permissions" "" "$ADMIN_TOKEN" "Check user permissions"
}

# Test 5: Resource-Based Access Control
test_resource_access() {
    log_info "📁 Test 5: Resource-Based Access Control"
    
    # Create resource
    local resource_data='{
        "name": "customer_database",
        "type": "database",
        "classification": "confidential",
        "department": "sales",
        "owner": "test_admin"
    }'
    
    api_call "POST" "/api/v1/resources" "$resource_data" "$ADMIN_TOKEN" "Create customer database resource"
    
    # List resources
    api_call "GET" "/api/v1/resources" "" "$ADMIN_TOKEN" "List all resources"
    
    # Test resource access (should be denied for regular user)
    api_call "GET" "/api/v1/resources/customer_database/access" "" "$USER_TOKEN" "Test resource access (regular user)"
    
    # Test resource access (should be allowed for admin)
    api_call "GET" "/api/v1/resources/customer_database/access" "" "$ADMIN_TOKEN" "Test resource access (admin user)"
    
    # Grant resource access to user
    local access_grant='{
        "user_id": "test_user",
        "resource": "customer_database",
        "permissions": ["read"],
        "granted_by": "test_admin"
    }'
    
    api_call "POST" "/api/v1/resources/customer_database/grant-access" "$access_grant" "$ADMIN_TOKEN" "Grant resource access to user"
    
    # Test access again (should now be allowed)
    api_call "GET" "/api/v1/resources/customer_database/access" "" "$USER_TOKEN" "Test resource access after grant"
}

# Test 6: Temporal Permissions
test_temporal_permissions() {
    log_info "🕒 Test 6: Temporal Permissions"
    
    # Create temporal permission for business hours
    local temporal_data='{
        "user_id": "test_user",
        "resource": "financial_reports",
        "permission": "read",
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "days_of_week": [1, 2, 3, 4, 5],
        "timezone": "UTC",
        "description": "Business hours access to financial reports"
    }'
    
    api_call "POST" "/api/v1/temporal-permissions" "$temporal_data" "$ADMIN_TOKEN" "Create temporal permission"
    
    # List temporal permissions
    api_call "GET" "/api/v1/temporal-permissions" "" "$ADMIN_TOKEN" "List temporal permissions"
    
    # Check current access (depends on current time)
    api_call "GET" "/api/v1/temporal-permissions/check" "" "$USER_TOKEN" "Check current temporal access"
}

# Test 7: Conditional Permissions
test_conditional_permissions() {
    log_info "🔐 Test 7: Conditional Permissions"
    
    # Create conditional permission based on IP and device
    local conditional_data='{
        "user_id": "test_user",
        "resource": "admin_panel",
        "permission": "read",
        "conditions": {
            "allowed_ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"],
            "required_device_types": ["desktop", "laptop"],
            "require_mfa": true,
            "max_concurrent_sessions": 1
        },
        "description": "Conditional admin panel access"
    }'
    
    api_call "POST" "/api/v1/conditional-permissions" "$conditional_data" "$ADMIN_TOKEN" "Create conditional permission"
    
    # List conditional permissions
    api_call "GET" "/api/v1/conditional-permissions" "" "$ADMIN_TOKEN" "List conditional permissions"
    
    # Test conditional access with context
    local access_context='{
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0",
        "device_type": "desktop",
        "mfa_verified": true
    }'
    
    api_call "POST" "/api/v1/conditional-permissions/check" "$access_context" "$USER_TOKEN" "Check conditional access"
}

# Test 8: Audit and Logging
test_audit_logging() {
    log_info "📊 Test 8: Audit and Logging"
    
    # Get audit logs
    api_call "GET" "/api/v1/audit/logs?limit=10" "" "$ADMIN_TOKEN" "Get recent audit logs"
    
    # Get user-specific audit trail
    api_call "GET" "/api/v1/audit/users/test_user" "" "$ADMIN_TOKEN" "Get user audit trail"
    
    # Generate compliance report
    local report_request='{
        "report_type": "access_review",
        "start_date": "2025-07-01T00:00:00Z",
        "end_date": "2025-07-31T23:59:59Z",
        "users": ["test_user"],
        "include_failed_attempts": true
    }'
    
    api_call "POST" "/api/v1/audit/reports" "$report_request" "$ADMIN_TOKEN" "Generate compliance report"
}

# Test 9: User Management
test_user_management() {
    log_info "👤 Test 9: User Management"
    
    # List users
    api_call "GET" "/api/v1/users" "" "$ADMIN_TOKEN" "List all users"
    
    # Get user details
    api_call "GET" "/api/v1/users/test_user" "" "$ADMIN_TOKEN" "Get user details"
    
    # Update user
    local user_update='{
        "first_name": "Updated",
        "last_name": "User",
        "department": "analytics"
    }'
    
    api_call "PUT" "/api/v1/users/test_user" "$user_update" "$ADMIN_TOKEN" "Update user details"
    
    # Assign role to user
    local role_assignment='{
        "role": "data_analyst",
        "assigned_by": "test_admin",
        "effective_date": "2025-07-31T00:00:00Z"
    }'
    
    api_call "POST" "/api/v1/users/test_user/roles" "$role_assignment" "$ADMIN_TOKEN" "Assign role to user"
    
    # Get user roles
    api_call "GET" "/api/v1/users/test_user/roles" "" "$ADMIN_TOKEN" "Get user roles"
}

# Test 10: Error Handling and Edge Cases
test_error_handling() {
    log_info "⚠️ Test 10: Error Handling and Edge Cases"
    
    # Test unauthorized access
    api_call "GET" "/api/v1/users" "" "" "Unauthorized access (no token)"
    
    # Test invalid token
    api_call "GET" "/api/v1/users" "" "invalid_token" "Invalid token access"
    
    # Test non-existent resource
    api_call "GET" "/api/v1/users/non_existent_user" "" "$ADMIN_TOKEN" "Non-existent user"
    
    # Test invalid data format
    local invalid_data='{"invalid": "json" missing quote}'
    api_call "POST" "/api/v1/roles" "$invalid_data" "$ADMIN_TOKEN" "Invalid JSON data"
    
    # Test duplicate resource creation
    local duplicate_role='{
        "name": "data_analyst",
        "display_name": "Duplicate Role",
        "description": "This should fail"
    }'
    
    api_call "POST" "/api/v1/roles" "$duplicate_role" "$ADMIN_TOKEN" "Duplicate role creation"
}

# Main test runner
run_all_tests() {
    echo "🚀 Starting RBAC API Testing with cURL"
    echo "======================================"
    echo "Base URL: $BASE_URL"
    echo
    
    # Check if backend is running
    if ! curl -s "$BASE_URL/health" > /dev/null; then
        log_error "Backend is not running at $BASE_URL"
        log_info "Please start the backend service first:"
        log_info "cd /home/ubuntu/enterprise_system/backend && python3 run.py"
        exit 1
    fi
    
    log_success "Backend is running at $BASE_URL"
    
    # Run all tests
    test_health_check
    test_user_auth
    test_role_management
    test_permission_management
    test_resource_access
    test_temporal_permissions
    test_conditional_permissions
    test_audit_logging
    test_user_management
    test_error_handling
    
    echo
    log_success "🎉 All RBAC API tests completed!"
    echo
    echo "Summary:"
    echo "- Admin Token: ${ADMIN_TOKEN:0:20}..."
    echo "- User Token: ${USER_TOKEN:0:20}..."
    echo
    echo "You can use these tokens for further manual testing."
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -u, --url URL     Set base URL (default: http://localhost:8000)"
    echo "  -h, --help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0                           # Run with default settings"
    echo "  $0 -u http://api.example.com # Run with custom URL"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run the tests
run_all_tests

