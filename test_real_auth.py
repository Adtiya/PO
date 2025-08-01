#!/usr/bin/env python3
"""
Enterprise AI System - Real Authentication Test
PhD-level comprehensive testing of authentication system
"""

import requests
import json
import time
import sys
from datetime import datetime

class AuthenticationTester:
    """
    Comprehensive authentication system tester
    """
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.access_token = None
        self.refresh_token = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Backend Health Check", True, "Backend is healthy and responsive")
                    return True
                else:
                    self.log_test("Backend Health Check", False, f"Backend status: {data.get('status')}")
                    return False
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Backend Health Check", False, error=str(e))
            return False
    
    def test_api_info(self):
        """Test API info endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/info", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                self.log_test("API Info", True, f"API v{data.get('version')} with {len(features)} features")
                return True
            else:
                self.log_test("API Info", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API Info", False, error=str(e))
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            # Test data
            user_data = {
                "email": f"testuser_{int(time.time())}@example.com",
                "password": "SecurePassword123!",
                "first_name": "Test",
                "last_name": "User",
                "phone": "+1234567890",
                "department": "Engineering",
                "job_title": "Software Engineer"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log_test("User Registration", True, f"User created: {data.get('user', {}).get('email')}")
                return True, user_data
            else:
                data = response.json()
                self.log_test("User Registration", False, f"HTTP {response.status_code}: {data.get('message', 'Unknown error')}")
                return False, None
                
        except Exception as e:
            self.log_test("User Registration", False, error=str(e))
            return False, None
    
    def test_user_login(self, user_data):
        """Test user login"""
        try:
            login_data = {
                "email": user_data["email"],
                "password": user_data["password"],
                "remember_me": False
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tokens = data.get('tokens', {})
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                
                self.log_test("User Login", True, f"Login successful, tokens received")
                return True
            else:
                data = response.json()
                self.log_test("User Login", False, f"HTTP {response.status_code}: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("User Login", False, error=str(e))
            return False
    
    def test_protected_endpoint(self):
        """Test protected endpoint with JWT token"""
        try:
            if not self.access_token:
                self.log_test("Protected Endpoint", False, "No access token available")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = self.session.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user = data.get('user', {})
                self.log_test("Protected Endpoint", True, f"User info retrieved: {user.get('email')}")
                return True
            else:
                data = response.json()
                self.log_test("Protected Endpoint", False, f"HTTP {response.status_code}: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("Protected Endpoint", False, error=str(e))
            return False
    
    def test_token_refresh(self):
        """Test token refresh"""
        try:
            if not self.refresh_token:
                self.log_test("Token Refresh", False, "No refresh token available")
                return False
            
            refresh_data = {
                "refresh_token": self.refresh_token
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json=refresh_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                new_token = data.get('tokens', {}).get('access_token')
                if new_token:
                    self.access_token = new_token
                    self.log_test("Token Refresh", True, "New access token received")
                    return True
                else:
                    self.log_test("Token Refresh", False, "No new token in response")
                    return False
            else:
                data = response.json()
                self.log_test("Token Refresh", False, f"HTTP {response.status_code}: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("Token Refresh", False, error=str(e))
            return False
    
    def test_ai_services(self):
        """Test AI services endpoints"""
        ai_tests = []
        
        # Test NLP service
        try:
            nlp_data = {"text": "This is a test of the NLP service for sentiment analysis."}
            response = self.session.post(
                f"{self.base_url}/api/v1/ai/nlp/analyze",
                json=nlp_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                sentiment = data.get('sentiment', {}).get('label', 'unknown')
                ai_tests.append(f"NLP: {sentiment} sentiment detected")
            else:
                ai_tests.append(f"NLP: HTTP {response.status_code}")
                
        except Exception as e:
            ai_tests.append(f"NLP: Error - {str(e)}")
        
        # Test Vision service
        try:
            vision_data = {"image_url": "https://example.com/test.jpg"}
            response = self.session.post(
                f"{self.base_url}/api/v1/ai/vision/analyze",
                json=vision_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                objects = len(data.get('objects', []))
                ai_tests.append(f"Vision: {objects} objects detected")
            else:
                ai_tests.append(f"Vision: HTTP {response.status_code}")
                
        except Exception as e:
            ai_tests.append(f"Vision: Error - {str(e)}")
        
        # Test Analytics service
        try:
            analytics_data = {"data": [1, 2, 3, 4, 5]}
            response = self.session.post(
                f"{self.base_url}/api/v1/ai/analytics/analyze",
                json=analytics_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                trends = len(data.get('trends', []))
                ai_tests.append(f"Analytics: {trends} trends identified")
            else:
                ai_tests.append(f"Analytics: HTTP {response.status_code}")
                
        except Exception as e:
            ai_tests.append(f"Analytics: Error - {str(e)}")
        
        # Test Recommendations service
        try:
            rec_data = {"user_id": 1, "item_type": "feature"}
            response = self.session.post(
                f"{self.base_url}/api/v1/ai/recommendations/get",
                json=rec_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                recs = len(data.get('recommendations', []))
                ai_tests.append(f"Recommendations: {recs} items suggested")
            else:
                ai_tests.append(f"Recommendations: HTTP {response.status_code}")
                
        except Exception as e:
            ai_tests.append(f"Recommendations: Error - {str(e)}")
        
        success = all("Error" not in test and "HTTP 4" not in test and "HTTP 5" not in test for test in ai_tests)
        self.log_test("AI Services", success, "; ".join(ai_tests))
        return success
    
    def test_logout(self):
        """Test user logout"""
        try:
            if not self.access_token:
                self.log_test("User Logout", False, "No access token available")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/logout",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("User Logout", True, "Logout successful")
                return True
            else:
                data = response.json()
                self.log_test("User Logout", False, f"HTTP {response.status_code}: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.log_test("User Logout", False, error=str(e))
            return False
    
    def test_password_validation(self):
        """Test password validation"""
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "short"
        ]
        
        validation_results = []
        
        for password in weak_passwords:
            try:
                user_data = {
                    "email": f"weakpass_{int(time.time())}@example.com",
                    "password": password,
                    "first_name": "Test",
                    "last_name": "User"
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/register",
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 400:
                    data = response.json()
                    if 'password' in data.get('message', '').lower() or data.get('code') == 'WEAK_PASSWORD':
                        validation_results.append(f"'{password}' correctly rejected")
                    else:
                        validation_results.append(f"'{password}' rejected for other reason")
                else:
                    validation_results.append(f"'{password}' incorrectly accepted")
                    
            except Exception as e:
                validation_results.append(f"'{password}' test error: {str(e)}")
        
        success = all("correctly rejected" in result for result in validation_results)
        self.log_test("Password Validation", success, "; ".join(validation_results))
        return success
    
    def run_comprehensive_test(self):
        """Run all authentication tests"""
        print("🧪 ENTERPRISE AI SYSTEM - AUTHENTICATION TEST SUITE")
        print("=" * 60)
        print()
        
        # Test backend connectivity
        if not self.test_backend_health():
            print("❌ Backend is not healthy. Stopping tests.")
            return False
        
        # Test API info
        self.test_api_info()
        
        # Test user registration and login flow
        reg_success, user_data = self.test_user_registration()
        if reg_success and user_data:
            login_success = self.test_user_login(user_data)
            
            if login_success:
                # Test protected endpoints
                self.test_protected_endpoint()
                
                # Test token refresh
                self.test_token_refresh()
                
                # Test logout
                self.test_logout()
        
        # Test AI services
        self.test_ai_services()
        
        # Test password validation
        self.test_password_validation()
        
        # Generate summary
        self.generate_summary()
        
        return True
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['error']}")
            print()
        
        # Overall assessment
        if success_rate >= 90:
            print("🎉 EXCELLENT: Authentication system is working excellently!")
        elif success_rate >= 75:
            print("✅ GOOD: Authentication system is mostly functional with minor issues.")
        elif success_rate >= 50:
            print("⚠️ FAIR: Authentication system has significant issues that need attention.")
        else:
            print("❌ POOR: Authentication system has major problems and needs immediate fixes.")
        
        print()
        print("🔒 PhD-Level Authentication System Test Complete")
        print(f"Timestamp: {datetime.now().isoformat()}")

def main():
    """Main test function"""
    print("Starting Enterprise AI System Authentication Tests...")
    print()
    
    # Test different backend URLs
    backend_urls = [
        "http://localhost:8001",
        "http://localhost:8000"
    ]
    
    for url in backend_urls:
        print(f"Testing backend at: {url}")
        tester = AuthenticationTester(url)
        
        try:
            # Quick connectivity test
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend found at {url}")
                tester.run_comprehensive_test()
                break
            else:
                print(f"❌ Backend at {url} returned HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to backend at {url}: {str(e)}")
    else:
        print("❌ No working backend found. Please ensure the backend is running.")
        return False
    
    return True

if __name__ == "__main__":
    main()

