#!/usr/bin/env python3
"""
Enterprise AI System - RBAC API Usage Examples
==============================================

This file contains practical examples of how to use the dynamic RBAC system APIs
for common enterprise scenarios and use cases.

Author: Manus AI
Version: 1.0.0
Date: 2025-07-31
"""

import requests
import json
import datetime
from typing import Dict, List, Optional, Any

class RBACAPIExamples:
    """Practical examples for using the RBAC API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000", admin_token: str = None):
        self.base_url = base_url
        self.admin_token = admin_token
        self.session = requests.Session()
        
        if admin_token:
            self.session.headers.update({"Authorization": f"Bearer {admin_token}"})

    def example_1_user_registration_and_role_assignment(self):
        """
        Example 1: Complete user onboarding with role assignment
        
        This example demonstrates:
        - User registration
        - Role assignment
        - Permission verification
        """
        print("🔧 Example 1: User Registration and Role Assignment")
        print("=" * 60)
        
        # Step 1: Register a new user
        new_user = {
            "username": "john_doe",
            "email": "john.doe@company.com",
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Analytics",
            "employee_id": "EMP001"
        }
        
        print("Step 1: Registering new user...")
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json=new_user
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 2: Assign role to user
        role_assignment = {
            "user_id": "john_doe",
            "role": "data_analyst",
            "assigned_by": "admin",
            "effective_date": datetime.datetime.now().isoformat(),
            "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
            "reason": "New employee onboarding"
        }
        
        print("Step 2: Assigning role to user...")
        response = self.session.post(
            f"{self.base_url}/api/v1/users/john_doe/roles",
            json=role_assignment
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 3: Verify user permissions
        print("Step 3: Verifying user permissions...")
        response = self.session.get(
            f"{self.base_url}/api/v1/users/john_doe/permissions"
        )
        print(f"Status: {response.status_code}")
        print(f"Permissions: {json.dumps(response.json(), indent=2)}")
        print()

    def example_2_temporal_access_control(self):
        """
        Example 2: Setting up time-based access control
        
        This example demonstrates:
        - Creating temporal permissions
        - Business hours restrictions
        - Weekend access controls
        """
        print("🕒 Example 2: Temporal Access Control")
        print("=" * 60)
        
        # Step 1: Create business hours access for financial data
        business_hours_permission = {
            "user_id": "john_doe",
            "resource": "financial_reports",
            "permission": "read",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
            "timezone": "America/New_York",
            "description": "Business hours access to financial reports"
        }
        
        print("Step 1: Creating business hours permission...")
        response = self.session.post(
            f"{self.base_url}/api/v1/temporal-permissions",
            json=business_hours_permission
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 2: Create emergency weekend access with approval
        weekend_permission = {
            "user_id": "john_doe",
            "resource": "financial_reports",
            "permission": "read",
            "start_time": "00:00:00",
            "end_time": "23:59:59",
            "days_of_week": [6, 7],  # Saturday and Sunday
            "timezone": "America/New_York",
            "requires_approval": True,
            "approver": "finance_manager",
            "description": "Emergency weekend access with manager approval"
        }
        
        print("Step 2: Creating weekend emergency access...")
        response = self.session.post(
            f"{self.base_url}/api/v1/temporal-permissions",
            json=weekend_permission
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 3: Test current access
        print("Step 3: Testing current access...")
        response = self.session.get(
            f"{self.base_url}/api/v1/resources/financial_reports/access",
            headers={"X-User-ID": "john_doe"}
        )
        print(f"Status: {response.status_code}")
        print(f"Access Result: {json.dumps(response.json(), indent=2)}")
        print()

    def example_3_conditional_access_policies(self):
        """
        Example 3: Context-aware conditional access
        
        This example demonstrates:
        - IP-based access restrictions
        - Device type requirements
        - Multi-factor authentication
        """
        print("🔐 Example 3: Conditional Access Policies")
        print("=" * 60)
        
        # Step 1: Create IP-restricted access for sensitive data
        ip_restriction_policy = {
            "user_id": "john_doe",
            "resource": "customer_pii",
            "permission": "read",
            "conditions": {
                "allowed_ip_ranges": [
                    "192.168.1.0/24",  # Office network
                    "10.0.0.0/8"       # VPN network
                ],
                "blocked_countries": ["CN", "RU", "KP"],
                "require_vpn": True
            },
            "description": "PII access restricted to office/VPN networks"
        }
        
        print("Step 1: Creating IP-restricted access policy...")
        response = self.session.post(
            f"{self.base_url}/api/v1/conditional-permissions",
            json=ip_restriction_policy
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 2: Create device-based access control
        device_policy = {
            "user_id": "john_doe",
            "resource": "admin_panel",
            "permission": "write",
            "conditions": {
                "allowed_device_types": ["desktop", "laptop"],
                "blocked_device_types": ["mobile", "tablet"],
                "require_managed_device": True,
                "min_os_version": {
                    "windows": "10.0.19041",
                    "macos": "11.0",
                    "linux": "20.04"
                }
            },
            "description": "Admin access restricted to managed desktop/laptop devices"
        }
        
        print("Step 2: Creating device-based access policy...")
        response = self.session.post(
            f"{self.base_url}/api/v1/conditional-permissions",
            json=device_policy
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # Step 3: Create MFA-required access
        mfa_policy = {
            "user_id": "john_doe",
            "resource": "financial_transactions",
            "permission": "write",
            "conditions": {
                "require_mfa": True,
                "mfa_methods": ["totp", "sms", "hardware_key"],
                "mfa_validity_minutes": 15,
                "max_concurrent_sessions": 1
            },
            "description": "Financial transactions require MFA"
        }
        
        print("Step 3: Creating MFA-required access policy...")
        response = self.session.post(
            f"{self.base_url}/api/v1/conditional-permissions",
            json=mfa_policy
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

    def example_4_role_hierarchy_management(self):
        """
        Example 4: Managing role hierarchies and inheritance
        
        This example demonstrates:
        - Creating role hierarchies
        - Permission inheritance
        - Role delegation
        """
        print("👥 Example 4: Role Hierarchy Management")
        print("=" * 60)
        
        # Step 1: Create a new role hierarchy
        roles_hierarchy = [
            {
                "name": "finance_director",
                "display_name": "Finance Director",
                "description": "Senior finance leadership role",
                "level": 1,
                "parent_role": None,
                "permissions": [
                    "finance:*",
                    "budget:approve",
                    "reports:all",
                    "users:manage_finance"
                ]
            },
            {
                "name": "finance_manager",
                "display_name": "Finance Manager",
                "description": "Finance team management role",
                "level": 2,
                "parent_role": "finance_director",
                "permissions": [
                    "finance:read",
                    "finance:write",
                    "budget:create",
                    "reports:department"
                ]
            },
            {
                "name": "finance_analyst",
                "display_name": "Finance Analyst",
                "description": "Financial analysis role",
                "level": 3,
                "parent_role": "finance_manager",
                "permissions": [
                    "finance:read",
                    "reports:create",
                    "analytics:access"
                ]
            }
        ]
        
        print("Step 1: Creating role hierarchy...")
        for role in roles_hierarchy:
            response = self.session.post(
                f"{self.base_url}/api/v1/roles",
                json=role
            )
            print(f"Created role '{role['name']}': Status {response.status_code}")
        print()
        
        # Step 2: Demonstrate permission inheritance
        print("Step 2: Checking permission inheritance...")
        response = self.session.get(
            f"{self.base_url}/api/v1/roles/finance_director/effective-permissions"
        )
        print(f"Finance Director effective permissions:")
        print(json.dumps(response.json(), indent=2))
        print()
        
        # Step 3: Create role delegation
        delegation = {
            "delegator": "finance_director",
            "delegate": "finance_manager",
            "permissions": ["budget:approve"],
            "start_date": datetime.datetime.now().isoformat(),
            "end_date": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat(),
            "reason": "Vacation coverage"
        }
        
        print("Step 3: Creating role delegation...")
        response = self.session.post(
            f"{self.base_url}/api/v1/roles/delegations",
            json=delegation
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

    def example_5_resource_based_access_control(self):
        """
        Example 5: Resource-level access control
        
        This example demonstrates:
        - Resource classification
        - Department-based access
        - Data sensitivity levels
        """
        print("📁 Example 5: Resource-Based Access Control")
        print("=" * 60)
        
        # Step 1: Create resource classifications
        resources = [
            {
                "name": "customer_database",
                "type": "database",
                "classification": "confidential",
                "department": "sales",
                "data_sensitivity": "high",
                "retention_period": "7_years",
                "access_controls": {
                    "encryption_required": True,
                    "audit_all_access": True,
                    "max_concurrent_users": 10
                }
            },
            {
                "name": "marketing_campaigns",
                "type": "application",
                "classification": "internal",
                "department": "marketing",
                "data_sensitivity": "medium",
                "retention_period": "3_years",
                "access_controls": {
                    "encryption_required": False,
                    "audit_all_access": False,
                    "max_concurrent_users": 50
                }
            },
            {
                "name": "public_website",
                "type": "website",
                "classification": "public",
                "department": "marketing",
                "data_sensitivity": "low",
                "retention_period": "1_year",
                "access_controls": {
                    "encryption_required": False,
                    "audit_all_access": False,
                    "max_concurrent_users": 1000
                }
            }
        ]
        
        print("Step 1: Creating resource classifications...")
        for resource in resources:
            response = self.session.post(
                f"{self.base_url}/api/v1/resources",
                json=resource
            )
            print(f"Created resource '{resource['name']}': Status {response.status_code}")
        print()
        
        # Step 2: Set department-based access rules
        access_rules = [
            {
                "resource": "customer_database",
                "department": "sales",
                "permissions": ["read", "write"],
                "conditions": {
                    "require_training": "data_protection_101",
                    "max_records_per_query": 1000
                }
            },
            {
                "resource": "customer_database",
                "department": "support",
                "permissions": ["read"],
                "conditions": {
                    "require_training": "customer_service_basics",
                    "max_records_per_query": 100,
                    "allowed_fields": ["name", "email", "phone", "support_tickets"]
                }
            }
        ]
        
        print("Step 2: Setting department-based access rules...")
        for rule in access_rules:
            response = self.session.post(
                f"{self.base_url}/api/v1/resources/{rule['resource']}/access-rules",
                json=rule
            )
            print(f"Created access rule: Status {response.status_code}")
        print()
        
        # Step 3: Test resource access
        print("Step 3: Testing resource access...")
        test_access = {
            "user_id": "john_doe",
            "resource": "customer_database",
            "action": "read",
            "context": {
                "department": "sales",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0..."
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/resources/access-check",
            json=test_access
        )
        print(f"Access check result:")
        print(json.dumps(response.json(), indent=2))
        print()

    def example_6_audit_and_compliance(self):
        """
        Example 6: Audit trails and compliance reporting
        
        This example demonstrates:
        - Access logging
        - Compliance reports
        - Security monitoring
        """
        print("📊 Example 6: Audit and Compliance")
        print("=" * 60)
        
        # Step 1: Query audit logs
        print("Step 1: Querying audit logs...")
        audit_query = {
            "start_date": (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(),
            "end_date": datetime.datetime.now().isoformat(),
            "user_id": "john_doe",
            "actions": ["login", "resource_access", "permission_change"],
            "resources": ["customer_database", "financial_reports"]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/audit/query",
            json=audit_query
        )
        print(f"Status: {response.status_code}")
        print(f"Audit logs: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Step 2: Generate compliance report
        print("Step 2: Generating compliance report...")
        compliance_request = {
            "report_type": "access_review",
            "period": "monthly",
            "departments": ["finance", "sales", "hr"],
            "include_sections": [
                "user_access_summary",
                "permission_changes",
                "failed_access_attempts",
                "privileged_access_usage"
            ]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/audit/compliance-report",
            json=compliance_request
        )
        print(f"Status: {response.status_code}")
        print(f"Report: {json.dumps(response.json(), indent=2)}")
        print()
        
        # Step 3: Set up security alerts
        print("Step 3: Setting up security alerts...")
        alert_config = {
            "alert_name": "suspicious_access_pattern",
            "conditions": {
                "failed_login_attempts": {"threshold": 5, "window_minutes": 15},
                "unusual_access_time": {"outside_business_hours": True},
                "geographic_anomaly": {"new_country": True},
                "privilege_escalation": {"role_change": True}
            },
            "actions": {
                "notify_security_team": True,
                "temporary_account_lock": True,
                "require_mfa_reset": True
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/audit/alerts",
            json=alert_config
        )
        print(f"Status: {response.status_code}")
        print(f"Alert configuration: {response.json()}")
        print()

    def example_7_bulk_operations(self):
        """
        Example 7: Bulk user and permission management
        
        This example demonstrates:
        - Bulk user import
        - Mass role assignments
        - Permission updates
        """
        print("📦 Example 7: Bulk Operations")
        print("=" * 60)
        
        # Step 1: Bulk user import
        print("Step 1: Bulk user import...")
        bulk_users = [
            {
                "username": f"user_{i:03d}",
                "email": f"user{i:03d}@company.com",
                "first_name": f"User",
                "last_name": f"{i:03d}",
                "department": "sales" if i % 2 == 0 else "marketing",
                "role": "basic_user"
            }
            for i in range(1, 11)
        ]
        
        response = self.session.post(
            f"{self.base_url}/api/v1/users/bulk-import",
            json={"users": bulk_users}
        )
        print(f"Status: {response.status_code}")
        print(f"Import result: {response.json()}")
        print()
        
        # Step 2: Bulk role assignment
        print("Step 2: Bulk role assignment...")
        role_assignments = {
            "assignments": [
                {
                    "user_id": f"user_{i:03d}",
                    "role": "data_analyst" if i <= 5 else "basic_user",
                    "effective_date": datetime.datetime.now().isoformat()
                }
                for i in range(1, 11)
            ]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/roles/bulk-assign",
            json=role_assignments
        )
        print(f"Status: {response.status_code}")
        print(f"Assignment result: {response.json()}")
        print()
        
        # Step 3: Bulk permission update
        print("Step 3: Bulk permission update...")
        permission_updates = {
            "updates": [
                {
                    "user_id": f"user_{i:03d}",
                    "permissions": {
                        "add": ["read_reports", "create_dashboards"],
                        "remove": ["admin_access"]
                    }
                }
                for i in range(1, 6)  # Only first 5 users
            ]
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/permissions/bulk-update",
            json=permission_updates
        )
        print(f"Status: {response.status_code}")
        print(f"Update result: {response.json()}")
        print()

    def run_all_examples(self):
        """Run all RBAC API examples"""
        print("🚀 Running All RBAC API Examples")
        print("=" * 80)
        print()
        
        examples = [
            self.example_1_user_registration_and_role_assignment,
            self.example_2_temporal_access_control,
            self.example_3_conditional_access_policies,
            self.example_4_role_hierarchy_management,
            self.example_5_resource_based_access_control,
            self.example_6_audit_and_compliance,
            self.example_7_bulk_operations
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                example()
                print(f"✅ Example {i} completed successfully")
            except Exception as e:
                print(f"❌ Example {i} failed: {str(e)}")
            print("-" * 80)
            print()

def main():
    """Main function to run RBAC API examples"""
    # Initialize with admin token (replace with actual token)
    admin_token = "your_admin_token_here"
    
    examples = RBACAPIExamples(admin_token=admin_token)
    examples.run_all_examples()

if __name__ == "__main__":
    main()

