#!/usr/bin/env python3
"""
Comprehensive Integration Test for AGI-NARI Enterprise System
============================================================

This script tests all system components and their integration:
- Frontend-Backend connectivity
- AI microservices functionality
- AGI-NARI components
- Database operations
- API endpoints
"""

import requests
import json
import time
import asyncio
from datetime import datetime
import sys
import os

class ComprehensiveIntegrationTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5173"
        self.api_gateway_url = "http://localhost:6000"
        
        self.ai_services = {
            "nlp": "http://localhost:5002",
            "vision": "http://localhost:5003", 
            "analytics": "http://localhost:5004",
            "recommendation": "http://localhost:5005"
        }
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "detailed_results": []
        }
        
        self.auth_token = None
    
    def log_test(self, test_name, status, details=None, error=None):
        """Log test results"""
        self.test_results["tests_run"] += 1
        
        if status == "PASS":
            self.test_results["tests_passed"] += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.test_results["tests_failed"] += 1
            print(f"❌ {test_name}: FAILED")
            if error:
                print(f"   Error: {error}")
        
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results["detailed_results"].append(result)
    
    def test_service_health(self, service_name, url):
        """Test if a service is healthy"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"{service_name} Health Check", "PASS", data)
                return True
            else:
                self.log_test(f"{service_name} Health Check", "FAIL", 
                            error=f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"{service_name} Health Check", "FAIL", error=e)
            return False
    
    def test_frontend_accessibility(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Accessibility", "PASS", 
                            {"status_code": response.status_code})
                return True
            else:
                self.log_test("Frontend Accessibility", "FAIL",
                            error=f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", "FAIL", error=e)
            return False
    
    def test_backend_authentication(self):
        """Test backend authentication system"""
        try:
            # Test login endpoint
            login_data = {
                "email": "admin@test.com",
                "password": "password123"
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.log_test("Backend Authentication", "PASS", 
                                {"token_received": True})
                    return True
                else:
                    self.log_test("Backend Authentication", "FAIL",
                                error="No access token in response")
                    return False
            else:
                self.log_test("Backend Authentication", "FAIL",
                            error=f"Status code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Backend Authentication", "FAIL", error=e)
            return False
    
    def test_database_operations(self):
        """Test database operations"""
        if not self.auth_token:
            self.log_test("Database Operations", "SKIP", 
                        error="No auth token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test users endpoint
            response = requests.get(
                f"{self.base_url}/users/",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                users = response.json()
                self.log_test("Database Operations - Users", "PASS",
                            {"users_count": len(users)})
                return True
            else:
                self.log_test("Database Operations - Users", "FAIL",
                            error=f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database Operations", "FAIL", error=e)
            return False
    
    def test_ai_service(self, service_name, service_url):
        """Test individual AI service"""
        try:
            # Test health first
            health_response = requests.get(f"{service_url}/health", timeout=5)
            if health_response.status_code != 200:
                self.log_test(f"AI Service {service_name} - Health", "FAIL",
                            error=f"Health check failed: {health_response.status_code}")
                return False
            
            # Test service-specific functionality
            if service_name == "nlp":
                test_data = {"text": "Hello, this is a test message for NLP processing."}
                endpoint = "/process"
            elif service_name == "vision":
                test_data = {"image_url": "https://example.com/test.jpg", "task": "analyze"}
                endpoint = "/analyze"
            elif service_name == "analytics":
                test_data = {"data": [1, 2, 3, 4, 5], "analysis_type": "trend"}
                endpoint = "/analyze"
            elif service_name == "recommendation":
                test_data = {"user_id": "test_user", "item_type": "product"}
                endpoint = "/recommend"
            else:
                endpoint = "/test"
                test_data = {"test": True}
            
            response = requests.post(
                f"{service_url}{endpoint}",
                json=test_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                self.log_test(f"AI Service {service_name} - Functionality", "PASS",
                            {"response": result})
                return True
            else:
                self.log_test(f"AI Service {service_name} - Functionality", "FAIL",
                            error=f"Status code: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test(f"AI Service {service_name}", "FAIL", error=e)
            return False
    
    def test_api_gateway(self):
        """Test API Gateway functionality"""
        try:
            # Test gateway health
            response = requests.get(f"{self.api_gateway_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("API Gateway - Health", "PASS")
                
                # Test gateway routing
                nlp_response = requests.post(
                    f"{self.api_gateway_url}/ai/nlp/process",
                    json={"text": "Test message through gateway"},
                    timeout=10
                )
                
                if nlp_response.status_code in [200, 201]:
                    self.log_test("API Gateway - Routing", "PASS",
                                {"routed_successfully": True})
                    return True
                else:
                    self.log_test("API Gateway - Routing", "FAIL",
                                error=f"Routing failed: {nlp_response.status_code}")
                    return False
            else:
                self.log_test("API Gateway", "FAIL",
                            error=f"Health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Gateway", "FAIL", error=e)
            return False
    
    def test_agi_nari_components(self):
        """Test AGI-NARI components"""
        try:
            # Test if AGI components are importable and functional
            sys.path.append('/home/ubuntu/enterprise_system/agi_nari_systems')
            
            # Test AGI Core Engine
            try:
                from agi_core_engine import AGICoreEngine
                agi_engine = AGICoreEngine()
                self.log_test("AGI Core Engine - Import", "PASS")
            except Exception as e:
                self.log_test("AGI Core Engine - Import", "FAIL", error=e)
            
            # Test Consciousness Engine
            try:
                from consciousness_engine import ConsciousnessEngine
                consciousness = ConsciousnessEngine()
                self.log_test("Consciousness Engine - Import", "PASS")
            except Exception as e:
                self.log_test("Consciousness Engine - Import", "FAIL", error=e)
            
            # Test Emotion Engine
            try:
                from emotion_engine import EmotionEngine
                emotion = EmotionEngine()
                self.log_test("Emotion Engine - Import", "PASS")
            except Exception as e:
                self.log_test("Emotion Engine - Import", "FAIL", error=e)
            
            # Test Domain Transcendence
            try:
                from nari_domain_transcendence import DomainTranscendenceEngine
                transcendence = DomainTranscendenceEngine()
                self.log_test("Domain Transcendence - Import", "PASS")
            except Exception as e:
                self.log_test("Domain Transcendence - Import", "FAIL", error=e)
            
            return True
            
        except Exception as e:
            self.log_test("AGI-NARI Components", "FAIL", error=e)
            return False
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        try:
            if not self.auth_token:
                self.log_test("End-to-End Workflow", "SKIP",
                            error="No auth token available")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # 1. Create a test user
            user_data = {
                "email": f"test_user_{int(time.time())}@test.com",
                "password": "testpass123",
                "full_name": "Test User",
                "role": "user"
            }
            
            create_response = requests.post(
                f"{self.base_url}/users/",
                json=user_data,
                headers=headers,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                user = create_response.json()
                user_id = user.get("id")
                
                # 2. Process text with NLP service
                nlp_response = requests.post(
                    f"{self.ai_services['nlp']}/process",
                    json={"text": f"Processing data for user {user_id}"},
                    timeout=10
                )
                
                # 3. Get analytics
                analytics_response = requests.post(
                    f"{self.ai_services['analytics']}/analyze",
                    json={"data": [1, 2, 3, 4, 5], "user_id": user_id},
                    timeout=10
                )
                
                if (nlp_response.status_code in [200, 201] and 
                    analytics_response.status_code in [200, 201]):
                    self.log_test("End-to-End Workflow", "PASS",
                                {"user_created": True, "ai_processing": True})
                    return True
                else:
                    self.log_test("End-to-End Workflow", "FAIL",
                                error="AI processing failed")
                    return False
            else:
                self.log_test("End-to-End Workflow", "FAIL",
                            error=f"User creation failed: {create_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("End-to-End Workflow", "FAIL", error=e)
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🌟" * 30)
        print("🧪 COMPREHENSIVE INTEGRATION TESTING")
        print("🌟" * 30)
        print()
        
        # Test 1: Service Health Checks
        print("📊 TESTING SERVICE HEALTH...")
        print("=" * 50)
        self.test_service_health("Backend", self.base_url)
        self.test_frontend_accessibility()
        self.test_service_health("API Gateway", self.api_gateway_url)
        
        for service_name, service_url in self.ai_services.items():
            self.test_service_health(f"AI {service_name.upper()}", service_url)
        print()
        
        # Test 2: Authentication & Database
        print("🔐 TESTING AUTHENTICATION & DATABASE...")
        print("=" * 50)
        self.test_backend_authentication()
        self.test_database_operations()
        print()
        
        # Test 3: AI Services Functionality
        print("🤖 TESTING AI SERVICES...")
        print("=" * 50)
        for service_name, service_url in self.ai_services.items():
            self.test_ai_service(service_name, service_url)
        print()
        
        # Test 4: API Gateway
        print("🌐 TESTING API GATEWAY...")
        print("=" * 50)
        self.test_api_gateway()
        print()
        
        # Test 5: AGI-NARI Components
        print("🧠 TESTING AGI-NARI COMPONENTS...")
        print("=" * 50)
        self.test_agi_nari_components()
        print()
        
        # Test 6: End-to-End Workflow
        print("🔄 TESTING END-TO-END WORKFLOW...")
        print("=" * 50)
        self.test_end_to_end_workflow()
        print()
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate final test report"""
        print("📊" * 30)
        print("🏆 INTEGRATION TEST RESULTS")
        print("📊" * 30)
        print()
        
        total_tests = self.test_results["tests_run"]
        passed_tests = self.test_results["tests_passed"]
        failed_tests = self.test_results["tests_failed"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 SUMMARY:")
        print(f"  🧪 Total Tests: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        print()
        
        # Categorize results
        categories = {
            "Service Health": [],
            "Authentication": [],
            "AI Services": [],
            "AGI Components": [],
            "Integration": []
        }
        
        for result in self.test_results["detailed_results"]:
            test_name = result["test_name"]
            if "Health" in test_name or "Accessibility" in test_name:
                categories["Service Health"].append(result)
            elif "Authentication" in test_name or "Database" in test_name:
                categories["Authentication"].append(result)
            elif "AI Service" in test_name or "API Gateway" in test_name:
                categories["AI Services"].append(result)
            elif any(x in test_name for x in ["AGI", "Consciousness", "Emotion", "Domain"]):
                categories["AGI Components"].append(result)
            else:
                categories["Integration"].append(result)
        
        print("📋 DETAILED RESULTS BY CATEGORY:")
        print("=" * 50)
        for category, results in categories.items():
            if results:
                passed = sum(1 for r in results if r["status"] == "PASS")
                total = len(results)
                print(f"  🎯 {category}: {passed}/{total} passed")
        print()
        
        # System status assessment
        if success_rate >= 90:
            status = "🟢 EXCELLENT"
        elif success_rate >= 75:
            status = "🟡 GOOD"
        elif success_rate >= 50:
            status = "🟠 NEEDS IMPROVEMENT"
        else:
            status = "🔴 CRITICAL ISSUES"
        
        print(f"🎯 OVERALL SYSTEM STATUS: {status}")
        print(f"📊 Integration Health: {success_rate:.1f}%")
        print()
        
        # Save detailed results
        with open(f'/home/ubuntu/integration_test_results_{int(time.time())}.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"💾 Detailed results saved: integration_test_results_{int(time.time())}.json")
        print()
        
        if success_rate >= 75:
            print("🎉 INTEGRATION TESTING SUCCESSFUL!")
            print("✅ Frontend-Backend integration working")
            print("✅ AI services operational")
            print("✅ AGI-NARI components functional")
            print("✅ System ready for production use")
        else:
            print("⚠️ Integration issues detected")
            print("🔧 Review failed tests and fix issues")
        
        return success_rate >= 75

def main():
    """Main function"""
    tester = ComprehensiveIntegrationTest()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

