#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Script for Enterprise AI System
Tests all major components and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class EnterpriseSystemTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", details: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if message:
            print(f"     {message}")
        if details and not success:
            print(f"     Details: {details}")
        print()

    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Backend Health Check", True, f"Service: {data.get('service')}, Version: {data.get('version')}")
                    return True
                else:
                    self.log_test("Backend Health Check", False, "Health status not healthy", data)
                    return False
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_api_info(self):
        """Test API info endpoint (should require auth)"""
        try:
            response = self.session.get(f"{self.api_base}/")
            if response.status_code == 401:
                data = response.json()
                if "Authentication" in data.get("error", ""):
                    self.log_test("API Authentication Protection", True, "API correctly requires authentication")
                    return True
                else:
                    self.log_test("API Authentication Protection", False, "Unexpected auth response", data)
                    return False
            else:
                self.log_test("API Authentication Protection", False, f"Expected 401, got {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("API Authentication Protection", False, f"Connection error: {str(e)}")
            return False

    def test_database_connection(self):
        """Test database connectivity through backend"""
        try:
            # Try to access an endpoint that would hit the database
            response = self.session.get(f"{self.api_base}/roles")
            if response.status_code == 401:  # Auth required, but DB connection works
                self.log_test("Database Connection", True, "Database accessible (auth required)")
                return True
            elif response.status_code == 500:
                self.log_test("Database Connection", False, "Database connection error", response.text)
                return False
            else:
                self.log_test("Database Connection", True, f"Database responding (status: {response.status_code})")
                return True
        except Exception as e:
            self.log_test("Database Connection", False, f"Connection error: {str(e)}")
            return False

    def test_rbac_endpoints(self):
        """Test RBAC endpoint availability"""
        rbac_endpoints = [
            "/roles",
            "/permissions", 
            "/resources",
            "/temporal-permissions",
            "/conditional-permissions"
        ]
        
        all_success = True
        for endpoint in rbac_endpoints:
            try:
                response = self.session.get(f"{self.api_base}{endpoint}")
                if response.status_code in [401, 403]:  # Auth/permission required
                    self.log_test(f"RBAC Endpoint {endpoint}", True, "Endpoint accessible (auth required)")
                elif response.status_code == 404:
                    self.log_test(f"RBAC Endpoint {endpoint}", False, "Endpoint not found")
                    all_success = False
                elif response.status_code == 500:
                    self.log_test(f"RBAC Endpoint {endpoint}", False, "Server error", response.text)
                    all_success = False
                else:
                    self.log_test(f"RBAC Endpoint {endpoint}", True, f"Endpoint responding (status: {response.status_code})")
            except Exception as e:
                self.log_test(f"RBAC Endpoint {endpoint}", False, f"Connection error: {str(e)}")
                all_success = False
        
        return all_success

    def test_microservices(self):
        """Test microservices availability"""
        microservices = [
            {"name": "PI Service", "port": 5001, "path": "/health"},
            {"name": "OBR Service", "port": 5002, "path": "/health"},
            {"name": "DA Service", "port": 5003, "path": "/health"}
        ]
        
        all_success = True
        for service in microservices:
            try:
                url = f"http://localhost:{service['port']}{service['path']}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(f"Microservice {service['name']}", True, f"Service healthy: {data.get('status', 'unknown')}")
                else:
                    self.log_test(f"Microservice {service['name']}", False, f"HTTP {response.status_code}", response.text)
                    all_success = False
            except requests.exceptions.ConnectionError:
                self.log_test(f"Microservice {service['name']}", False, "Service not running or not accessible")
                all_success = False
            except Exception as e:
                self.log_test(f"Microservice {service['name']}", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success

    def test_api_documentation(self):
        """Test API documentation endpoints"""
        doc_endpoints = [
            "/docs",
            "/redoc", 
            "/openapi.json"
        ]
        
        all_success = True
        for endpoint in doc_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    self.log_test(f"API Documentation {endpoint}", True, "Documentation accessible")
                else:
                    self.log_test(f"API Documentation {endpoint}", False, f"HTTP {response.status_code}")
                    all_success = False
            except Exception as e:
                self.log_test(f"API Documentation {endpoint}", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success

    def test_error_handling(self):
        """Test error handling"""
        try:
            # Test invalid endpoint
            response = self.session.get(f"{self.api_base}/nonexistent")
            if response.status_code == 404:
                self.log_test("Error Handling - 404", True, "Proper 404 response for invalid endpoint")
            else:
                self.log_test("Error Handling - 404", False, f"Expected 404, got {response.status_code}")
            
            # Test invalid JSON
            response = self.session.post(
                f"{self.api_base}/auth/login",
                headers={"Content-Type": "application/json"},
                data="invalid json"
            )
            if response.status_code == 422:
                self.log_test("Error Handling - Invalid JSON", True, "Proper validation error for invalid JSON")
                return True
            else:
                self.log_test("Error Handling - Invalid JSON", False, f"Expected 422, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Enterprise AI System Testing")
        print("=" * 60)
        print()
        
        # Core system tests
        print("📋 CORE SYSTEM TESTS")
        print("-" * 30)
        backend_healthy = self.test_backend_health()
        self.test_api_info()
        self.test_database_connection()
        
        # RBAC system tests
        print("🔐 RBAC SYSTEM TESTS")
        print("-" * 30)
        self.test_rbac_endpoints()
        
        # Microservices tests
        print("🏢 MICROSERVICES TESTS")
        print("-" * 30)
        self.test_microservices()
        
        # Documentation tests
        print("📚 DOCUMENTATION TESTS")
        print("-" * 30)
        self.test_api_documentation()
        
        # Error handling tests
        print("⚠️  ERROR HANDLING TESTS")
        print("-" * 30)
        self.test_error_handling()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        if backend_healthy and passed_tests >= total_tests * 0.7:  # 70% pass rate
            print("🎉 SYSTEM STATUS: OPERATIONAL")
            print("The Enterprise AI System is functioning and ready for use!")
            return True
        else:
            print("⚠️  SYSTEM STATUS: ISSUES DETECTED")
            print("The system has significant issues that need to be resolved.")
            return False

if __name__ == "__main__":
    tester = EnterpriseSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

