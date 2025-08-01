#!/usr/bin/env python3
"""
Enterprise AI System - Dynamic RBAC Testing Suite
=================================================

This comprehensive testing suite validates all aspects of the dynamic RBAC system,
including role hierarchies, temporal permissions, conditional access, and resource-based controls.

Author: Manus AI
Version: 1.0.0
Date: 2025-07-31
"""

import requests
import json
import time
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"

@dataclass
class TestCase:
    name: str
    description: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    payload: Optional[Dict[str, Any]]
    expected_status: int
    expected_response: Optional[Dict[str, Any]]
    result: Optional[TestResult] = None
    actual_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class RBACTestSuite:
    """Comprehensive RBAC Testing Suite for Enterprise AI System"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_tokens = {}
        self.test_results = []
        self.test_users = {}
        self.test_roles = {}
        self.test_resources = {}
        
    def setup_test_environment(self):
        """Set up test environment with users, roles, and resources"""
        logger.info("Setting up test environment...")
        
        # Test users with different roles
        self.test_users = {
            "admin": {
                "username": "test_admin",
                "email": "admin@test.com",
                "password": "AdminPass123!",
                "role": "system_admin"
            },
            "manager": {
                "username": "test_manager", 
                "email": "manager@test.com",
                "password": "ManagerPass123!",
                "role": "department_manager"
            },
            "analyst": {
                "username": "test_analyst",
                "email": "analyst@test.com", 
                "password": "AnalystPass123!",
                "role": "data_analyst"
            },
            "user": {
                "username": "test_user",
                "email": "user@test.com",
                "password": "UserPass123!",
                "role": "basic_user"
            }
        }
        
        # Test roles with hierarchical structure
        self.test_roles = {
            "system_admin": {
                "name": "System Administrator",
                "description": "Full system access",
                "level": 1,
                "parent_role": None,
                "permissions": ["*"]
            },
            "department_manager": {
                "name": "Department Manager",
                "description": "Department-level management access",
                "level": 2,
                "parent_role": "system_admin",
                "permissions": ["read_all", "write_department", "manage_users"]
            },
            "data_analyst": {
                "name": "Data Analyst",
                "description": "Data analysis and reporting access",
                "level": 3,
                "parent_role": "department_manager",
                "permissions": ["read_data", "create_reports", "view_analytics"]
            },
            "basic_user": {
                "name": "Basic User",
                "description": "Basic system access",
                "level": 4,
                "parent_role": "data_analyst",
                "permissions": ["read_own", "update_profile"]
            }
        }
        
        # Test resources for resource-based access control
        self.test_resources = {
            "financial_data": {
                "name": "Financial Data",
                "type": "dataset",
                "classification": "confidential",
                "department": "finance"
            },
            "user_profiles": {
                "name": "User Profiles",
                "type": "database",
                "classification": "internal",
                "department": "hr"
            },
            "analytics_dashboard": {
                "name": "Analytics Dashboard",
                "type": "application",
                "classification": "internal",
                "department": "analytics"
            }
        }

    def register_test_users(self):
        """Register all test users"""
        logger.info("Registering test users...")
        
        for user_type, user_data in self.test_users.items():
            test_case = TestCase(
                name=f"Register {user_type} user",
                description=f"Register test user with {user_data['role']} role",
                endpoint="/api/v1/auth/register",
                method="POST",
                headers={"Content-Type": "application/json"},
                payload={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "first_name": user_data["username"].split('_')[0].title(),
                    "last_name": user_data["username"].split('_')[1].title() if '_' in user_data["username"] else "User"
                },
                expected_status=201,
                expected_response={"message": "User registered successfully"}
            )
            
            result = self.execute_test_case(test_case)
            self.test_results.append(result)

    def authenticate_test_users(self):
        """Authenticate all test users and store tokens"""
        logger.info("Authenticating test users...")
        
        for user_type, user_data in self.test_users.items():
            test_case = TestCase(
                name=f"Authenticate {user_type} user",
                description=f"Login test user {user_data['username']}",
                endpoint="/api/v1/auth/login",
                method="POST",
                headers={"Content-Type": "application/json"},
                payload={
                    "email": user_data["email"],
                    "password": user_data["password"]
                },
                expected_status=200,
                expected_response={"access_token": "string", "token_type": "bearer"}
            )
            
            result = self.execute_test_case(test_case)
            
            if result.result == TestResult.PASS and result.actual_response:
                self.auth_tokens[user_type] = result.actual_response.get("access_token")
                logger.info(f"Stored auth token for {user_type}")
            
            self.test_results.append(result)

    def test_role_hierarchy(self):
        """Test role hierarchy and inheritance"""
        logger.info("Testing role hierarchy...")
        
        # Test role creation with hierarchy
        hierarchy_tests = [
            {
                "role": "system_admin",
                "user": "admin",
                "should_access": ["financial_data", "user_profiles", "analytics_dashboard"]
            },
            {
                "role": "department_manager", 
                "user": "manager",
                "should_access": ["user_profiles", "analytics_dashboard"],
                "should_deny": ["financial_data"]
            },
            {
                "role": "data_analyst",
                "user": "analyst", 
                "should_access": ["analytics_dashboard"],
                "should_deny": ["financial_data", "user_profiles"]
            },
            {
                "role": "basic_user",
                "user": "user",
                "should_access": [],
                "should_deny": ["financial_data", "user_profiles", "analytics_dashboard"]
            }
        ]
        
        for test in hierarchy_tests:
            # Test allowed access
            for resource in test.get("should_access", []):
                test_case = TestCase(
                    name=f"Role hierarchy - {test['role']} access to {resource}",
                    description=f"Test that {test['role']} can access {resource}",
                    endpoint=f"/api/v1/resources/{resource}/access",
                    method="GET",
                    headers={"Authorization": f"Bearer {self.auth_tokens[test['user']]}"},
                    payload=None,
                    expected_status=200,
                    expected_response={"access": "granted"}
                )
                
                result = self.execute_test_case(test_case)
                self.test_results.append(result)
            
            # Test denied access
            for resource in test.get("should_deny", []):
                test_case = TestCase(
                    name=f"Role hierarchy - {test['role']} denied access to {resource}",
                    description=f"Test that {test['role']} is denied access to {resource}",
                    endpoint=f"/api/v1/resources/{resource}/access",
                    method="GET", 
                    headers={"Authorization": f"Bearer {self.auth_tokens[test['user']]}"},
                    payload=None,
                    expected_status=403,
                    expected_response={"error": "Access denied"}
                )
                
                result = self.execute_test_case(test_case)
                self.test_results.append(result)

    def test_temporal_permissions(self):
        """Test time-based access control"""
        logger.info("Testing temporal permissions...")
        
        # Create temporal permission for business hours access
        current_time = datetime.datetime.now()
        business_start = current_time.replace(hour=9, minute=0, second=0)
        business_end = current_time.replace(hour=17, minute=0, second=0)
        
        temporal_permission = {
            "user_id": "test_analyst",
            "resource": "financial_data",
            "permission": "read",
            "start_time": business_start.isoformat(),
            "end_time": business_end.isoformat(),
            "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
            "timezone": "UTC"
        }
        
        # Create temporal permission
        test_case = TestCase(
            name="Create temporal permission",
            description="Create time-based access permission for analyst",
            endpoint="/api/v1/temporal-permissions",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_tokens['admin']}",
                "Content-Type": "application/json"
            },
            payload=temporal_permission,
            expected_status=201,
            expected_response={"message": "Temporal permission created"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test access during business hours
        if business_start <= current_time <= business_end and current_time.weekday() < 5:
            test_case = TestCase(
                name="Temporal access - business hours",
                description="Test access during allowed business hours",
                endpoint="/api/v1/resources/financial_data/access",
                method="GET",
                headers={"Authorization": f"Bearer {self.auth_tokens['analyst']}"},
                payload=None,
                expected_status=200,
                expected_response={"access": "granted", "reason": "temporal_permission"}
            )
        else:
            test_case = TestCase(
                name="Temporal access - outside business hours",
                description="Test access outside allowed business hours",
                endpoint="/api/v1/resources/financial_data/access",
                method="GET",
                headers={"Authorization": f"Bearer {self.auth_tokens['analyst']}"},
                payload=None,
                expected_status=403,
                expected_response={"error": "Access denied", "reason": "outside_allowed_time"}
            )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)

    def test_conditional_permissions(self):
        """Test context-aware conditional access"""
        logger.info("Testing conditional permissions...")
        
        # Create conditional permission based on location and device
        conditional_permission = {
            "user_id": "test_manager",
            "resource": "user_profiles",
            "permission": "write",
            "conditions": {
                "ip_range": ["192.168.1.0/24", "10.0.0.0/8"],
                "device_type": ["desktop", "laptop"],
                "user_agent_pattern": ".*Chrome.*",
                "mfa_required": True,
                "max_concurrent_sessions": 1
            }
        }
        
        # Create conditional permission
        test_case = TestCase(
            name="Create conditional permission",
            description="Create context-aware permission for manager",
            endpoint="/api/v1/conditional-permissions",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_tokens['admin']}",
                "Content-Type": "application/json"
            },
            payload=conditional_permission,
            expected_status=201,
            expected_response={"message": "Conditional permission created"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test access with valid conditions
        test_case = TestCase(
            name="Conditional access - valid conditions",
            description="Test access with valid IP and device conditions",
            endpoint="/api/v1/resources/user_profiles/access",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_tokens['manager']}",
                "Content-Type": "application/json",
                "X-Real-IP": "192.168.1.100",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0"
            },
            payload={
                "action": "write",
                "mfa_token": "123456",
                "device_fingerprint": "desktop_chrome_windows"
            },
            expected_status=200,
            expected_response={"access": "granted", "reason": "conditional_permission"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test access with invalid conditions
        test_case = TestCase(
            name="Conditional access - invalid IP",
            description="Test access denial with invalid IP address",
            endpoint="/api/v1/resources/user_profiles/access",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_tokens['manager']}",
                "Content-Type": "application/json",
                "X-Real-IP": "203.0.113.1",  # Invalid IP
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0"
            },
            payload={
                "action": "write",
                "mfa_token": "123456",
                "device_fingerprint": "desktop_chrome_windows"
            },
            expected_status=403,
            expected_response={"error": "Access denied", "reason": "invalid_ip_address"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)

    def test_resource_based_access(self):
        """Test resource-level access control"""
        logger.info("Testing resource-based access control...")
        
        # Test different resource types and classifications
        resource_tests = [
            {
                "resource": "financial_data",
                "classification": "confidential",
                "allowed_roles": ["system_admin"],
                "denied_roles": ["department_manager", "data_analyst", "basic_user"]
            },
            {
                "resource": "user_profiles", 
                "classification": "internal",
                "allowed_roles": ["system_admin", "department_manager"],
                "denied_roles": ["data_analyst", "basic_user"]
            },
            {
                "resource": "analytics_dashboard",
                "classification": "internal", 
                "allowed_roles": ["system_admin", "department_manager", "data_analyst"],
                "denied_roles": ["basic_user"]
            }
        ]
        
        for resource_test in resource_tests:
            # Test allowed access
            for role in resource_test["allowed_roles"]:
                user_type = next(k for k, v in self.test_users.items() if v["role"] == role)
                
                test_case = TestCase(
                    name=f"Resource access - {role} to {resource_test['resource']}",
                    description=f"Test {role} access to {resource_test['classification']} resource",
                    endpoint=f"/api/v1/resources/{resource_test['resource']}",
                    method="GET",
                    headers={"Authorization": f"Bearer {self.auth_tokens[user_type]}"},
                    payload=None,
                    expected_status=200,
                    expected_response={"resource": resource_test["resource"], "access": "granted"}
                )
                
                result = self.execute_test_case(test_case)
                self.test_results.append(result)
            
            # Test denied access
            for role in resource_test["denied_roles"]:
                user_type = next(k for k, v in self.test_users.items() if v["role"] == role)
                
                test_case = TestCase(
                    name=f"Resource denial - {role} to {resource_test['resource']}",
                    description=f"Test {role} denial to {resource_test['classification']} resource",
                    endpoint=f"/api/v1/resources/{resource_test['resource']}",
                    method="GET",
                    headers={"Authorization": f"Bearer {self.auth_tokens[user_type]}"},
                    payload=None,
                    expected_status=403,
                    expected_response={"error": "Access denied", "reason": "insufficient_permissions"}
                )
                
                result = self.execute_test_case(test_case)
                self.test_results.append(result)

    def test_permission_inheritance(self):
        """Test permission inheritance through role hierarchy"""
        logger.info("Testing permission inheritance...")
        
        # Test that higher-level roles inherit permissions from lower levels
        inheritance_tests = [
            {
                "parent_role": "system_admin",
                "child_role": "department_manager",
                "inherited_permissions": ["read_all", "write_department", "manage_users"]
            },
            {
                "parent_role": "department_manager",
                "child_role": "data_analyst", 
                "inherited_permissions": ["read_data", "create_reports", "view_analytics"]
            },
            {
                "parent_role": "data_analyst",
                "child_role": "basic_user",
                "inherited_permissions": ["read_own", "update_profile"]
            }
        ]
        
        for test in inheritance_tests:
            parent_user = next(k for k, v in self.test_users.items() if v["role"] == test["parent_role"])
            
            for permission in test["inherited_permissions"]:
                test_case = TestCase(
                    name=f"Permission inheritance - {test['parent_role']} has {permission}",
                    description=f"Test that {test['parent_role']} inherits {permission} from {test['child_role']}",
                    endpoint=f"/api/v1/permissions/check",
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {self.auth_tokens[parent_user]}",
                        "Content-Type": "application/json"
                    },
                    payload={
                        "permission": permission,
                        "resource": "any"
                    },
                    expected_status=200,
                    expected_response={"has_permission": True, "source": "inherited"}
                )
                
                result = self.execute_test_case(test_case)
                self.test_results.append(result)

    def test_dynamic_role_assignment(self):
        """Test dynamic role assignment and updates"""
        logger.info("Testing dynamic role assignment...")
        
        # Test role assignment
        test_case = TestCase(
            name="Dynamic role assignment",
            description="Assign new role to existing user",
            endpoint="/api/v1/users/test_user/roles",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_tokens['admin']}",
                "Content-Type": "application/json"
            },
            payload={
                "role": "data_analyst",
                "effective_date": datetime.datetime.now().isoformat(),
                "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
            },
            expected_status=200,
            expected_response={"message": "Role assigned successfully"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test access with new role
        test_case = TestCase(
            name="Access with new role",
            description="Test access after role assignment",
            endpoint="/api/v1/resources/analytics_dashboard/access",
            method="GET",
            headers={"Authorization": f"Bearer {self.auth_tokens['user']}"},
            payload=None,
            expected_status=200,
            expected_response={"access": "granted", "role": "data_analyst"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test role revocation
        test_case = TestCase(
            name="Dynamic role revocation",
            description="Revoke role from user",
            endpoint="/api/v1/users/test_user/roles/data_analyst",
            method="DELETE",
            headers={"Authorization": f"Bearer {self.auth_tokens['admin']}"},
            payload=None,
            expected_status=200,
            expected_response={"message": "Role revoked successfully"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)

    def test_audit_and_logging(self):
        """Test audit trail and access logging"""
        logger.info("Testing audit and logging...")
        
        # Test audit log retrieval
        test_case = TestCase(
            name="Audit log retrieval",
            description="Retrieve audit logs for user actions",
            endpoint="/api/v1/audit/logs",
            method="GET",
            headers={"Authorization": f"Bearer {self.auth_tokens['admin']}"},
            payload=None,
            expected_status=200,
            expected_response={"logs": "array", "total": "number"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)
        
        # Test specific user audit trail
        test_case = TestCase(
            name="User audit trail",
            description="Retrieve audit trail for specific user",
            endpoint="/api/v1/audit/users/test_analyst",
            method="GET",
            headers={"Authorization": f"Bearer {self.auth_tokens['admin']}"},
            payload=None,
            expected_status=200,
            expected_response={"user": "test_analyst", "actions": "array"}
        )
        
        result = self.execute_test_case(test_case)
        self.test_results.append(result)

    def execute_test_case(self, test_case: TestCase) -> TestCase:
        """Execute a single test case"""
        try:
            url = f"{self.base_url}{test_case.endpoint}"
            
            if test_case.method == "GET":
                response = self.session.get(url, headers=test_case.headers)
            elif test_case.method == "POST":
                response = self.session.post(url, headers=test_case.headers, json=test_case.payload)
            elif test_case.method == "PUT":
                response = self.session.put(url, headers=test_case.headers, json=test_case.payload)
            elif test_case.method == "DELETE":
                response = self.session.delete(url, headers=test_case.headers)
            else:
                test_case.result = TestResult.FAIL
                test_case.error_message = f"Unsupported HTTP method: {test_case.method}"
                return test_case
            
            test_case.actual_response = response.json() if response.content else {}
            
            # Check status code
            if response.status_code == test_case.expected_status:
                test_case.result = TestResult.PASS
                logger.info(f"✅ PASS: {test_case.name}")
            else:
                test_case.result = TestResult.FAIL
                test_case.error_message = f"Expected status {test_case.expected_status}, got {response.status_code}"
                logger.error(f"❌ FAIL: {test_case.name} - {test_case.error_message}")
                
        except requests.exceptions.RequestException as e:
            test_case.result = TestResult.FAIL
            test_case.error_message = f"Request failed: {str(e)}"
            logger.error(f"❌ FAIL: {test_case.name} - {test_case.error_message}")
        except Exception as e:
            test_case.result = TestResult.FAIL
            test_case.error_message = f"Unexpected error: {str(e)}"
            logger.error(f"❌ FAIL: {test_case.name} - {test_case.error_message}")
        
        return test_case

    def run_all_tests(self):
        """Run the complete RBAC test suite"""
        logger.info("🚀 Starting RBAC Test Suite...")
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Core authentication tests
            self.register_test_users()
            self.authenticate_test_users()
            
            # RBAC feature tests
            self.test_role_hierarchy()
            self.test_temporal_permissions()
            self.test_conditional_permissions()
            self.test_resource_based_access()
            self.test_permission_inheritance()
            self.test_dynamic_role_assignment()
            self.test_audit_and_logging()
            
            # Generate report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {str(e)}")
            raise

    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t.result == TestResult.PASS])
        failed_tests = len([t for t in self.test_results if t.result == TestResult.FAIL])
        skipped_tests = len([t for t in self.test_results if t.result == TestResult.SKIP])
        
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "test_suite": "Dynamic RBAC System",
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "pass_rate": f"{pass_rate:.2f}%"
            },
            "test_results": []
        }
        
        for test in self.test_results:
            report["test_results"].append({
                "name": test.name,
                "description": test.description,
                "result": test.result.value,
                "endpoint": test.endpoint,
                "method": test.method,
                "expected_status": test.expected_status,
                "actual_response": test.actual_response,
                "error_message": test.error_message
            })
        
        # Save report to file
        with open("/home/ubuntu/rbac_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Test Report Generated:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {failed_tests}")
        logger.info(f"   Pass Rate: {pass_rate:.2f}%")
        
        return report

def main():
    """Main function to run RBAC tests"""
    # Initialize test suite
    test_suite = RBACTestSuite()
    
    # Run all tests
    test_suite.run_all_tests()
    
    print("🎉 RBAC Test Suite completed! Check rbac_test_report.json for detailed results.")

if __name__ == "__main__":
    main()

