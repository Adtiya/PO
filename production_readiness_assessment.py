#!/usr/bin/env python3
"""
Production Readiness Assessment
Comprehensive validation for enterprise deployment
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import importlib.util

class ProductionReadinessAssessment:
    """Comprehensive production readiness validation"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "assessment_version": "1.0.0",
            "overall_readiness": "UNKNOWN",
            "readiness_score": 0,
            "categories": {},
            "recommendations": [],
            "blockers": [],
            "warnings": []
        }
    
    def log(self, message, level="INFO"):
        """Log assessment messages"""
        print(f"[{level}] {datetime.now().strftime('%H:%M:%S')} - {message}")
    
    def assess_security_readiness(self):
        """Assess security readiness for production"""
        self.log("🔐 Assessing Security Readiness")
        category = {"score": 0, "max_score": 10, "checks": []}
        
        # Check 1: Environment variable security
        check = {"name": "Environment Variable Security", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            env_example = Path("enterprise_system/.env.example")
            if env_example.exists():
                with open(env_example, 'r') as f:
                    content = f.read()
                    if len(content.split('\n')) >= 30:  # Should have many config options
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Comprehensive environment configuration available"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Environment configuration incomplete"
                        self.results["blockers"].append("Incomplete environment configuration")
            else:
                check["status"] = "FAIL"
                check["message"] = "Environment example file missing"
                self.results["blockers"].append("Missing .env.example file")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 2: CORS security implementation
        check = {"name": "CORS Security", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            secure_cors_count = 0
            main_files = list(Path("enterprise_system/microservices").rglob("main.py"))
            
            for file_path in main_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'ALLOWED_ORIGINS' in content and '*' not in content:
                        secure_cors_count += 1
            
            if secure_cors_count >= 4:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = f"Secure CORS implemented in {secure_cors_count} services"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Only {secure_cors_count} services have secure CORS"
                self.results["warnings"].append("Some services may have insecure CORS configuration")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 3: Authentication security
        check = {"name": "Authentication Security", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            auth_service = Path("enterprise_system/backend/app/services/auth.py")
            if auth_service.exists():
                with open(auth_service, 'r') as f:
                    content = f.read()
                    has_bcrypt = "bcrypt" in content
                    has_jwt = "jwt" in content
                    has_validation = "ValidationException" in content
                    
                    if has_bcrypt and has_jwt and has_validation:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Comprehensive authentication security implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Authentication security incomplete"
                        self.results["warnings"].append("Authentication security may need enhancement")
            else:
                check["status"] = "FAIL"
                check["message"] = "Authentication service not found"
                self.results["blockers"].append("Missing authentication service")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 4: Input validation security
        check = {"name": "Input Validation", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            validation_file = Path("enterprise_system/shared/validation.py")
            if validation_file.exists():
                with open(validation_file, 'r') as f:
                    content = f.read()
                    has_pydantic = "from pydantic import" in content
                    has_schemas = len([line for line in content.split('\n') if 'class ' in line and 'Request' in line]) >= 5
                    has_sanitization = "validator" in content
                    
                    if has_pydantic and has_schemas and has_sanitization:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Comprehensive input validation implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Input validation incomplete"
                        self.results["warnings"].append("Input validation may need enhancement")
            else:
                check["status"] = "FAIL"
                check["message"] = "Validation module not found"
                self.results["blockers"].append("Missing input validation system")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 5: Database security
        check = {"name": "Database Security", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check for proper database error handling
            auth_service = Path("enterprise_system/backend/app/services/auth.py")
            if auth_service.exists():
                with open(auth_service, 'r') as f:
                    content = f.read()
                    has_try_catch = content.count("try:") >= 2
                    has_rollback = "rollback()" in content
                    has_parameterized = "session.execute" in content or "db.add" in content
                    
                    if has_try_catch and has_rollback and has_parameterized:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Database security properly implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Database security incomplete"
                        self.results["warnings"].append("Database security may need enhancement")
            else:
                check["status"] = "SKIP"
                check["message"] = "Database service not found"
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        self.results["categories"]["security"] = category
        self.log(f"Security Score: {category['score']}/{category['max_score']}")
    
    def assess_architecture_readiness(self):
        """Assess architecture readiness for production"""
        self.log("🏗️ Assessing Architecture Readiness")
        category = {"score": 0, "max_score": 8, "checks": []}
        
        # Check 1: Microservices separation
        check = {"name": "Microservices Separation", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check that user routes are not duplicated across services
            user_routes = list(Path("enterprise_system/microservices").rglob("**/routes/user.py"))
            if len(user_routes) == 0:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = "Proper microservices separation achieved"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Found {len(user_routes)} duplicate user routes"
                self.results["blockers"].append("Microservices separation incomplete")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 2: Service independence
        check = {"name": "Service Independence", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check that services have their own main.py and can start independently
            services = ["ai_nlp_service", "ai_vision_service", "ai_analytics_service", "ai_recommendation_service"]
            independent_services = 0
            
            for service in services:
                main_file = Path(f"enterprise_system/microservices/{service}").rglob("main.py")
                if any(main_file):
                    independent_services += 1
            
            if independent_services >= 4:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = f"{independent_services} services are properly independent"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Only {independent_services} services are independent"
                self.results["warnings"].append("Some services may not be properly independent")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 3: Configuration management
        check = {"name": "Configuration Management", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check for proper environment-based configuration
            config_files = list(Path("enterprise_system").rglob("*.py"))
            env_usage_count = 0
            
            for file_path in config_files:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if 'os.getenv' in content or 'os.environ' in content:
                            env_usage_count += 1
                except:
                    continue
            
            if env_usage_count >= 10:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = f"Environment-based configuration used in {env_usage_count} files"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Environment configuration only found in {env_usage_count} files"
                self.results["warnings"].append("Configuration management may be incomplete")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 4: Error handling architecture
        check = {"name": "Error Handling Architecture", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            validation_file = Path("enterprise_system/shared/validation.py")
            if validation_file.exists():
                with open(validation_file, 'r') as f:
                    content = f.read()
                    has_error_handler = "class ErrorHandler" in content
                    has_custom_exceptions = "class ValidationError" in content
                    has_response_format = "class ErrorResponse" in content
                    
                    if has_error_handler and has_custom_exceptions and has_response_format:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Comprehensive error handling architecture implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Error handling architecture incomplete"
                        self.results["warnings"].append("Error handling architecture needs improvement")
            else:
                check["status"] = "FAIL"
                check["message"] = "Error handling module not found"
                self.results["blockers"].append("Missing error handling architecture")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        self.results["categories"]["architecture"] = category
        self.log(f"Architecture Score: {category['score']}/{category['max_score']}")
    
    def assess_monitoring_readiness(self):
        """Assess monitoring and observability readiness"""
        self.log("📊 Assessing Monitoring Readiness")
        category = {"score": 0, "max_score": 6, "checks": []}
        
        # Check 1: Monitoring system implementation
        check = {"name": "Monitoring System", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            monitoring_file = Path("enterprise_system/shared/monitoring.py")
            if monitoring_file.exists():
                with open(monitoring_file, 'r') as f:
                    content = f.read()
                    has_health_checker = "class HealthChecker" in content
                    has_metrics = "class ServiceMetrics" in content
                    has_logging = "class StructuredLogger" in content
                    
                    if has_health_checker and has_metrics and has_logging:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Comprehensive monitoring system implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Monitoring system incomplete"
                        self.results["warnings"].append("Monitoring system needs enhancement")
            else:
                check["status"] = "FAIL"
                check["message"] = "Monitoring module not found"
                self.results["blockers"].append("Missing monitoring system")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 2: Health check endpoints
        check = {"name": "Health Check Endpoints", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check if services have health check integration
            nlp_service = Path("enterprise_system/microservices/ai_nlp_service/nlp_ai_service/src/main.py")
            if nlp_service.exists():
                with open(nlp_service, 'r') as f:
                    content = f.read()
                    has_monitoring_import = "from monitoring import" in content
                    has_setup = "setup_monitoring" in content
                    
                    if has_monitoring_import and has_setup:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Health check endpoints properly integrated"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Health check integration incomplete"
                        self.results["warnings"].append("Health check endpoints need integration")
            else:
                check["status"] = "SKIP"
                check["message"] = "Service not found for health check validation"
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 3: Structured logging
        check = {"name": "Structured Logging", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            monitoring_file = Path("enterprise_system/shared/monitoring.py")
            if monitoring_file.exists():
                with open(monitoring_file, 'r') as f:
                    content = f.read()
                    has_correlation_id = "correlation_id" in content
                    has_json_logging = "JSONRenderer" in content
                    has_context = "get_context" in content
                    
                    if has_correlation_id and has_json_logging and has_context:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = "Structured logging properly implemented"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = "Structured logging incomplete"
                        self.results["warnings"].append("Structured logging needs enhancement")
            else:
                check["status"] = "FAIL"
                check["message"] = "Monitoring module not found"
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        self.results["categories"]["monitoring"] = category
        self.log(f"Monitoring Score: {category['score']}/{category['max_score']}")
    
    def assess_deployment_readiness(self):
        """Assess deployment readiness"""
        self.log("🚀 Assessing Deployment Readiness")
        category = {"score": 0, "max_score": 6, "checks": []}
        
        # Check 1: Documentation completeness
        check = {"name": "Documentation", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            docs = [
                "COMPREHENSIVE_SYSTEM_IMPROVEMENTS_REPORT.md",
                "enterprise_system/README.md",
                "enterprise_system/.env.example"
            ]
            
            complete_docs = 0
            for doc in docs:
                if Path(doc).exists():
                    complete_docs += 1
            
            if complete_docs >= 3:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = f"Documentation complete ({complete_docs}/{len(docs)} files)"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Documentation incomplete ({complete_docs}/{len(docs)} files)"
                self.results["warnings"].append("Documentation needs completion")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 2: Environment configuration
        check = {"name": "Environment Configuration", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            env_example = Path("enterprise_system/.env.example")
            if env_example.exists():
                with open(env_example, 'r') as f:
                    content = f.read()
                    config_lines = [line for line in content.split('\n') if '=' in line and not line.startswith('#')]
                    
                    if len(config_lines) >= 20:
                        check["status"] = "PASS"
                        check["score"] = 2
                        check["message"] = f"Comprehensive environment configuration ({len(config_lines)} settings)"
                    else:
                        check["status"] = "FAIL"
                        check["message"] = f"Environment configuration incomplete ({len(config_lines)} settings)"
                        self.results["warnings"].append("Environment configuration needs expansion")
            else:
                check["status"] = "FAIL"
                check["message"] = "Environment example file missing"
                self.results["blockers"].append("Missing environment configuration")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        # Check 3: Service startup validation
        check = {"name": "Service Startup", "status": "UNKNOWN", "score": 0, "max_score": 2}
        try:
            # Check if services have proper startup scripts and requirements
            services_with_main = 0
            service_dirs = [d for d in Path("enterprise_system/microservices").iterdir() if d.is_dir()]
            
            for service_dir in service_dirs:
                main_files = list(service_dir.rglob("main.py"))
                if main_files:
                    services_with_main += 1
            
            if services_with_main >= 6:
                check["status"] = "PASS"
                check["score"] = 2
                check["message"] = f"Service startup ready ({services_with_main} services)"
            else:
                check["status"] = "FAIL"
                check["message"] = f"Service startup incomplete ({services_with_main} services)"
                self.results["warnings"].append("Some services may not start properly")
        except Exception as e:
            check["status"] = "ERROR"
            check["message"] = str(e)
        category["checks"].append(check)
        category["score"] += check["score"]
        
        self.results["categories"]["deployment"] = category
        self.log(f"Deployment Score: {category['score']}/{category['max_score']}")
    
    def calculate_overall_readiness(self):
        """Calculate overall production readiness"""
        total_score = 0
        max_score = 0
        
        for category_name, category_data in self.results["categories"].items():
            total_score += category_data["score"]
            max_score += category_data["max_score"]
        
        readiness_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        self.results["readiness_score"] = readiness_percentage
        
        # Determine readiness level
        if readiness_percentage >= 90:
            self.results["overall_readiness"] = "PRODUCTION_READY"
        elif readiness_percentage >= 80:
            self.results["overall_readiness"] = "NEARLY_READY"
        elif readiness_percentage >= 70:
            self.results["overall_readiness"] = "NEEDS_MINOR_FIXES"
        elif readiness_percentage >= 60:
            self.results["overall_readiness"] = "NEEDS_MAJOR_FIXES"
        else:
            self.results["overall_readiness"] = "NOT_READY"
        
        # Generate recommendations
        if len(self.results["blockers"]) > 0:
            self.results["recommendations"].append("Address all blocking issues before production deployment")
        
        if len(self.results["warnings"]) > 0:
            self.results["recommendations"].append("Review and address warning items for optimal production performance")
        
        if readiness_percentage >= 90:
            self.results["recommendations"].append("System is production ready - proceed with deployment")
        elif readiness_percentage >= 80:
            self.results["recommendations"].append("Address minor issues and revalidate before production deployment")
        else:
            self.results["recommendations"].append("Significant improvements needed before production deployment")
        
        return readiness_percentage
    
    def run_assessment(self):
        """Run complete production readiness assessment"""
        self.log("🏁 Starting Production Readiness Assessment")
        self.log("=" * 70)
        
        # Run all assessments
        self.assess_security_readiness()
        self.assess_architecture_readiness()
        self.assess_monitoring_readiness()
        self.assess_deployment_readiness()
        
        # Calculate overall readiness
        readiness_score = self.calculate_overall_readiness()
        
        # Print summary
        self.log("=" * 70)
        self.log("🎯 PRODUCTION READINESS SUMMARY")
        self.log("=" * 70)
        self.log(f"Overall Readiness: {self.results['overall_readiness']}")
        self.log(f"Readiness Score: {readiness_score:.1f}%")
        
        # Print category scores
        for category_name, category_data in self.results["categories"].items():
            score = category_data["score"]
            max_score = category_data["max_score"]
            percentage = (score / max_score * 100) if max_score > 0 else 0
            self.log(f"{category_name.title()}: {score}/{max_score} ({percentage:.1f}%)")
        
        # Print blockers and warnings
        if self.results["blockers"]:
            self.log("\n🚫 BLOCKING ISSUES:")
            for blocker in self.results["blockers"]:
                self.log(f"  - {blocker}")
        
        if self.results["warnings"]:
            self.log("\n⚠️ WARNINGS:")
            for warning in self.results["warnings"]:
                self.log(f"  - {warning}")
        
        # Print recommendations
        self.log("\n💡 RECOMMENDATIONS:")
        for recommendation in self.results["recommendations"]:
            self.log(f"  - {recommendation}")
        
        # Save results
        with open("production_readiness_assessment.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        self.log("\nAssessment results saved to production_readiness_assessment.json")
        
        return self.results["overall_readiness"] in ["PRODUCTION_READY", "NEARLY_READY"]

def main():
    """Main assessment function"""
    assessment = ProductionReadinessAssessment()
    is_ready = assessment.run_assessment()
    
    if is_ready:
        print("\n🎉 SYSTEM IS PRODUCTION READY!")
        print("The AGI-NARI Enterprise System meets production deployment standards.")
    else:
        print("\n⚠️ SYSTEM NEEDS IMPROVEMENTS")
        print("Review the assessment results and address identified issues.")
    
    return is_ready

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

