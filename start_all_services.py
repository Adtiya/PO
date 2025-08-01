#!/usr/bin/env python3
"""
Comprehensive Service Startup Script for AGI-NARI Enterprise System
==================================================================

This script starts all services in the correct order and monitors their health.
"""

import subprocess
import time
import requests
import json
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import threading

class ServiceManager:
    def __init__(self):
        self.services = {}
        self.startup_order = [
            "backend",
            "frontend", 
            "api_gateway",
            "ai_nlp",
            "ai_vision",
            "ai_analytics",
            "ai_recommendation"
        ]
        
        self.service_configs = {
            "backend": {
                "command": ["python", "run.py"],
                "cwd": "/home/ubuntu/enterprise_system/backend",
                "port": 8000,
                "health_url": "http://localhost:8000/health",
                "startup_time": 5
            },
            "frontend": {
                "command": ["pnpm", "dev"],
                "cwd": "/home/ubuntu/enterprise_system/enterprise-ai-frontend", 
                "port": 5174,
                "health_url": "http://localhost:5174",
                "startup_time": 10
            },
            "api_gateway": {
                "command": ["python", "api_gateway.py"],
                "cwd": "/home/ubuntu/enterprise_system/microservices",
                "port": 6000,
                "health_url": "http://localhost:6000/health",
                "startup_time": 3
            },
            "ai_nlp": {
                "command": ["python", "nlp_ai_service/src/main.py"],
                "cwd": "/home/ubuntu/enterprise_system/microservices/ai_nlp_service",
                "port": 5002,
                "health_url": "http://localhost:5002/health",
                "startup_time": 5
            },
            "ai_vision": {
                "command": ["python", "vision_ai_service/src/main.py"],
                "cwd": "/home/ubuntu/enterprise_system/microservices/ai_vision_service",
                "port": 5003,
                "health_url": "http://localhost:5003/health",
                "startup_time": 5
            },
            "ai_analytics": {
                "command": ["python", "analytics_ai_service/src/main.py"],
                "cwd": "/home/ubuntu/enterprise_system/microservices/ai_analytics_service",
                "port": 5004,
                "health_url": "http://localhost:5004/health",
                "startup_time": 5
            },
            "ai_recommendation": {
                "command": ["python", "recommendation_ai_service/src/main.py"],
                "cwd": "/home/ubuntu/enterprise_system/microservices/ai_recommendation_service",
                "port": 5005,
                "health_url": "http://localhost:5005/health",
                "startup_time": 5
            }
        }
    
    def start_service(self, service_name):
        """Start a single service"""
        config = self.service_configs[service_name]
        
        print(f"🚀 Starting {service_name}...")
        
        try:
            # Change to service directory
            os.chdir(config["cwd"])
            
            # Start the service
            process = subprocess.Popen(
                config["command"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.services[service_name] = {
                "process": process,
                "config": config,
                "status": "starting"
            }
            
            # Wait for startup
            time.sleep(config["startup_time"])
            
            # Check health
            if self.check_health(service_name):
                self.services[service_name]["status"] = "healthy"
                print(f"✅ {service_name} started successfully on port {config['port']}")
                return True
            else:
                self.services[service_name]["status"] = "unhealthy"
                print(f"❌ {service_name} failed to start properly")
                return False
                
        except Exception as e:
            print(f"❌ Error starting {service_name}: {e}")
            self.services[service_name]["status"] = "error"
            return False
    
    def check_health(self, service_name):
        """Check if a service is healthy"""
        config = self.service_configs[service_name]
        
        try:
            response = requests.get(config["health_url"], timeout=5)
            return response.status_code == 200
        except:
            # For frontend, just check if port is responding
            if service_name == "frontend":
                try:
                    response = requests.get(config["health_url"], timeout=5)
                    return True
                except:
                    return False
            return False
    
    def start_all_services(self):
        """Start all services in order"""
        print("🌟" * 30)
        print("🚀 STARTING AGI-NARI ENTERPRISE SYSTEM")
        print("🌟" * 30)
        print()
        
        success_count = 0
        
        for service_name in self.startup_order:
            if self.start_service(service_name):
                success_count += 1
            print()
        
        print("📊 STARTUP SUMMARY:")
        print("=" * 50)
        print(f"✅ Services Started: {success_count}/{len(self.startup_order)}")
        print(f"📈 Success Rate: {(success_count/len(self.startup_order)*100):.1f}%")
        print()
        
        # Display service status
        print("🔍 SERVICE STATUS:")
        print("=" * 50)
        for service_name, service_info in self.services.items():
            config = service_info["config"]
            status = service_info["status"]
            
            status_emoji = {
                "healthy": "✅",
                "unhealthy": "❌", 
                "starting": "🔄",
                "error": "💥"
            }.get(status, "❓")
            
            print(f"  {status_emoji} {service_name.upper()}: {status} (Port {config['port']})")
        
        print()
        return success_count == len(self.startup_order)
    
    def get_service_urls(self):
        """Get all service URLs"""
        urls = {}
        for service_name, config in self.service_configs.items():
            if service_name == "frontend":
                urls[service_name] = f"http://localhost:{config['port']}"
            else:
                urls[service_name] = config["health_url"]
        return urls

def main():
    """Main function"""
    manager = ServiceManager()
    
    # Start all services
    success = manager.start_all_services()
    
    if success:
        print("🎉 ALL SERVICES STARTED SUCCESSFULLY!")
        print()
        print("🌐 SERVICE URLS:")
        print("=" * 50)
        urls = manager.get_service_urls()
        for service_name, url in urls.items():
            print(f"  🔗 {service_name.upper()}: {url}")
        print()
        print("🚀 System ready for testing!")
    else:
        print("⚠️ Some services failed to start. Check logs for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

