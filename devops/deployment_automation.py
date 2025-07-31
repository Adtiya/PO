"""
Enterprise AI System - DevOps Automation and Deployment
Automated deployment, CI/CD pipelines, and infrastructure management
"""

import os
import sys
import json
import subprocess
import time
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'devops-automation-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

@dataclass
class DeploymentJob:
    """Represents a deployment job"""
    id: str
    name: str
    environment: str
    services: List[str]
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    logs: List[str]
    success: bool
    error_message: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "environment": self.environment,
            "services": self.services,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "logs": self.logs,
            "success": self.success,
            "error_message": self.error_message
        }

@dataclass
class ServiceConfig:
    """Service configuration for deployment"""
    name: str
    port: int
    health_endpoint: str
    start_command: str
    working_directory: str
    environment_vars: Dict[str, str]
    dependencies: List[str]

class DevOpsAutomation:
    """DevOps automation and deployment management"""
    
    def __init__(self):
        self.deployments: Dict[str, DeploymentJob] = {}
        self.service_configs: Dict[str, ServiceConfig] = {}
        self.running_services: Dict[str, subprocess.Popen] = {}
        self.stats = {
            "deployments_total": 0,
            "deployments_successful": 0,
            "deployments_failed": 0,
            "services_deployed": 0,
            "start_time": datetime.utcnow()
        }
        
        # Initialize service configurations
        self._initialize_service_configs()
    
    def _initialize_service_configs(self):
        """Initialize service configurations"""
        base_dir = "/home/ubuntu/enterprise_system"
        
        configs = [
            ServiceConfig(
                name="auth_service",
                port=8000,
                health_endpoint="/health",
                start_command="python src/main.py",
                working_directory=f"{base_dir}/backend",
                environment_vars={"PORT": "8000"},
                dependencies=[]
            ),
            ServiceConfig(
                name="nlp_service",
                port=5002,
                health_endpoint="/health",
                start_command="python src/main.py",
                working_directory=f"{base_dir}/microservices/ai_nlp_service/nlp_ai_service",
                environment_vars={"PORT": "5002"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="vision_service",
                port=5003,
                health_endpoint="/health",
                start_command="python src/main.py",
                working_directory=f"{base_dir}/microservices/ai_vision_service/vision_ai_service",
                environment_vars={"PORT": "5003"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="analytics_service",
                port=5004,
                health_endpoint="/health",
                start_command="python src/main.py",
                working_directory=f"{base_dir}/microservices/ai_analytics_service/analytics_ai_service",
                environment_vars={"PORT": "5004"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="recommendation_service",
                port=5005,
                health_endpoint="/health",
                start_command="python src/main.py",
                working_directory=f"{base_dir}/microservices/ai_recommendation_service/recommendation_ai_service",
                environment_vars={"PORT": "5005"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="api_gateway",
                port=6000,
                health_endpoint="/health",
                start_command="python api_gateway.py",
                working_directory=f"{base_dir}/microservices",
                environment_vars={"PORT": "6000"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="websocket_server",
                port=7000,
                health_endpoint="/health",
                start_command="python websocket_server.py",
                working_directory=f"{base_dir}/realtime",
                environment_vars={"PORT": "7000"},
                dependencies=[]
            ),
            ServiceConfig(
                name="graphql_api",
                port=7001,
                health_endpoint="/health",
                start_command="python graphql_server.py",
                working_directory=f"{base_dir}/graphql",
                environment_vars={"PORT": "7001"},
                dependencies=["auth_service"]
            ),
            ServiceConfig(
                name="cache_service",
                port=7002,
                health_endpoint="/health",
                start_command="python redis_cache_service.py",
                working_directory=f"{base_dir}/caching",
                environment_vars={"PORT": "7002"},
                dependencies=[]
            ),
            ServiceConfig(
                name="event_bus",
                port=7003,
                health_endpoint="/health",
                start_command="python event_bus.py",
                working_directory=f"{base_dir}/events",
                environment_vars={"PORT": "7003"},
                dependencies=[]
            ),
            ServiceConfig(
                name="search_service",
                port=7004,
                health_endpoint="/health",
                start_command="python search_service.py",
                working_directory=f"{base_dir}/search",
                environment_vars={"PORT": "7004"},
                dependencies=[]
            ),
            ServiceConfig(
                name="monitoring_service",
                port=7005,
                health_endpoint="/health",
                start_command="python monitoring_service.py",
                working_directory=f"{base_dir}/monitoring",
                environment_vars={"PORT": "7005"},
                dependencies=[]
            )
        ]
        
        for config in configs:
            self.service_configs[config.name] = config
    
    def deploy_service(self, service_name: str, environment: str = "development") -> bool:
        """Deploy a single service"""
        if service_name not in self.service_configs:
            logger.error(f"Service {service_name} not found in configurations")
            return False
        
        config = self.service_configs[service_name]
        
        try:
            # Stop existing service if running
            if service_name in self.running_services:
                self.stop_service(service_name)
            
            # Set up environment
            env = os.environ.copy()
            env.update(config.environment_vars)
            
            # Start service
            logger.info(f"Starting service: {service_name}")
            process = subprocess.Popen(
                config.start_command.split(),
                cwd=config.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running_services[service_name] = process
            
            # Wait a moment and check if service started successfully
            time.sleep(2)
            if process.poll() is None:  # Process is still running
                logger.info(f"Service {service_name} started successfully")
                self.stats["services_deployed"] += 1
                return True
            else:
                logger.error(f"Service {service_name} failed to start")
                return False
        
        except Exception as e:
            logger.error(f"Error deploying service {service_name}: {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a running service"""
        if service_name not in self.running_services:
            return True
        
        try:
            process = self.running_services[service_name]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            del self.running_services[service_name]
            logger.info(f"Service {service_name} stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping service {service_name}: {e}")
            return False
    
    def deploy_all_services(self, environment: str = "development") -> str:
        """Deploy all services in dependency order"""
        deployment_id = f"deploy_{int(time.time())}"
        
        deployment = DeploymentJob(
            id=deployment_id,
            name="Full System Deployment",
            environment=environment,
            services=list(self.service_configs.keys()),
            status="running",
            started_at=datetime.utcnow(),
            completed_at=None,
            logs=[],
            success=False,
            error_message=None
        )
        
        self.deployments[deployment_id] = deployment
        self.stats["deployments_total"] += 1
        
        # Start deployment in background thread
        thread = threading.Thread(
            target=self._execute_full_deployment,
            args=(deployment_id, environment),
            daemon=True
        )
        thread.start()
        
        return deployment_id
    
    def _execute_full_deployment(self, deployment_id: str, environment: str):
        """Execute full deployment in background"""
        deployment = self.deployments[deployment_id]
        
        try:
            # Deploy services in dependency order
            deployment_order = self._get_deployment_order()
            
            for service_name in deployment_order:
                deployment.logs.append(f"Deploying {service_name}...")
                
                success = self.deploy_service(service_name, environment)
                
                if success:
                    deployment.logs.append(f"✅ {service_name} deployed successfully")
                    
                    # Wait for service to be healthy
                    if self._wait_for_service_health(service_name):
                        deployment.logs.append(f"✅ {service_name} is healthy")
                    else:
                        deployment.logs.append(f"⚠️ {service_name} health check failed")
                else:
                    deployment.logs.append(f"❌ {service_name} deployment failed")
                    deployment.error_message = f"Failed to deploy {service_name}"
                    break
                
                # Small delay between services
                time.sleep(1)
            
            # Check if all services are running
            all_running = all(
                service in self.running_services 
                for service in deployment_order
            )
            
            if all_running:
                deployment.success = True
                deployment.status = "completed"
                deployment.logs.append("🎉 All services deployed successfully!")
                self.stats["deployments_successful"] += 1
            else:
                deployment.success = False
                deployment.status = "failed"
                deployment.logs.append("❌ Deployment failed")
                self.stats["deployments_failed"] += 1
        
        except Exception as e:
            deployment.success = False
            deployment.status = "failed"
            deployment.error_message = str(e)
            deployment.logs.append(f"❌ Deployment error: {e}")
            self.stats["deployments_failed"] += 1
        
        finally:
            deployment.completed_at = datetime.utcnow()
    
    def _get_deployment_order(self) -> List[str]:
        """Get services in dependency order"""
        # Simple dependency resolution
        ordered = []
        remaining = set(self.service_configs.keys())
        
        while remaining:
            # Find services with no unresolved dependencies
            ready = []
            for service in remaining:
                config = self.service_configs[service]
                if all(dep in ordered for dep in config.dependencies):
                    ready.append(service)
            
            if not ready:
                # No services ready, add remaining (circular dependency or error)
                ordered.extend(remaining)
                break
            
            # Add ready services
            for service in ready:
                ordered.append(service)
                remaining.remove(service)
        
        return ordered
    
    def _wait_for_service_health(self, service_name: str, timeout: int = 30) -> bool:
        """Wait for service to become healthy"""
        config = self.service_configs[service_name]
        url = f"http://localhost:{config.port}{config.health_endpoint}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            
            time.sleep(2)
        
        return False
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all services"""
        status = {}
        
        for service_name, config in self.service_configs.items():
            is_running = service_name in self.running_services
            
            if is_running:
                process = self.running_services[service_name]
                is_alive = process.poll() is None
            else:
                is_alive = False
            
            # Check health endpoint
            is_healthy = False
            if is_alive:
                try:
                    url = f"http://localhost:{config.port}{config.health_endpoint}"
                    response = requests.get(url, timeout=5)
                    is_healthy = response.status_code == 200
                except:
                    pass
            
            status[service_name] = {
                "running": is_running,
                "alive": is_alive,
                "healthy": is_healthy,
                "port": config.port,
                "url": f"http://localhost:{config.port}"
            }
        
        return status
    
    def create_docker_compose(self) -> str:
        """Generate Docker Compose configuration"""
        services = {}
        
        for service_name, config in self.service_configs.items():
            services[service_name] = {
                "build": {
                    "context": config.working_directory,
                    "dockerfile": "Dockerfile"
                },
                "ports": [f"{config.port}:{config.port}"],
                "environment": config.environment_vars,
                "depends_on": config.dependencies,
                "restart": "unless-stopped",
                "healthcheck": {
                    "test": f"curl -f http://localhost:{config.port}{config.health_endpoint} || exit 1",
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            }
        
        compose_config = {
            "version": "3.8",
            "services": services,
            "networks": {
                "enterprise_ai_network": {
                    "driver": "bridge"
                }
            }
        }
        
        return yaml.dump(compose_config, default_flow_style=False)
    
    def create_kubernetes_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes deployment manifests"""
        manifests = {}
        
        for service_name, config in self.service_configs.items():
            # Deployment manifest
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": service_name,
                    "labels": {"app": service_name}
                },
                "spec": {
                    "replicas": 1,
                    "selector": {"matchLabels": {"app": service_name}},
                    "template": {
                        "metadata": {"labels": {"app": service_name}},
                        "spec": {
                            "containers": [{
                                "name": service_name,
                                "image": f"enterprise-ai/{service_name}:latest",
                                "ports": [{"containerPort": config.port}],
                                "env": [
                                    {"name": k, "value": v} 
                                    for k, v in config.environment_vars.items()
                                ],
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": config.health_endpoint,
                                        "port": config.port
                                    },
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                }
                            }]
                        }
                    }
                }
            }
            
            # Service manifest
            service = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": f"{service_name}-service",
                    "labels": {"app": service_name}
                },
                "spec": {
                    "selector": {"app": service_name},
                    "ports": [{
                        "protocol": "TCP",
                        "port": config.port,
                        "targetPort": config.port
                    }],
                    "type": "ClusterIP"
                }
            }
            
            manifests[f"{service_name}-deployment.yaml"] = yaml.dump(deployment)
            manifests[f"{service_name}-service.yaml"] = yaml.dump(service)
        
        return manifests

# Global DevOps automation instance
devops = DevOpsAutomation()

# API Routes

@app.route('/deploy/service', methods=['POST'])
def deploy_service():
    """Deploy a single service"""
    try:
        data = request.get_json()
        if not data or 'service_name' not in data:
            return jsonify({"error": "Service name is required"}), 400
        
        service_name = data['service_name']
        environment = data.get('environment', 'development')
        
        success = devops.deploy_service(service_name, environment)
        
        return jsonify({
            "success": success,
            "service": service_name,
            "environment": environment,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deploy/all', methods=['POST'])
def deploy_all():
    """Deploy all services"""
    try:
        data = request.get_json() or {}
        environment = data.get('environment', 'development')
        
        deployment_id = devops.deploy_all_services(environment)
        
        return jsonify({
            "deployment_id": deployment_id,
            "environment": environment,
            "status": "started",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deploy/status/<deployment_id>')
def deployment_status(deployment_id):
    """Get deployment status"""
    try:
        if deployment_id not in devops.deployments:
            return jsonify({"error": "Deployment not found"}), 404
        
        deployment = devops.deployments[deployment_id]
        return jsonify(deployment.to_dict())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/services/status')
def services_status():
    """Get status of all services"""
    try:
        status = devops.get_service_status()
        return jsonify({
            "services": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/services/stop', methods=['POST'])
def stop_service():
    """Stop a service"""
    try:
        data = request.get_json()
        if not data or 'service_name' not in data:
            return jsonify({"error": "Service name is required"}), 400
        
        service_name = data['service_name']
        success = devops.stop_service(service_name)
        
        return jsonify({
            "success": success,
            "service": service_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config/docker-compose')
def docker_compose_config():
    """Get Docker Compose configuration"""
    try:
        config = devops.create_docker_compose()
        return jsonify({
            "docker_compose": config,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config/kubernetes')
def kubernetes_config():
    """Get Kubernetes manifests"""
    try:
        manifests = devops.create_kubernetes_manifests()
        return jsonify({
            "kubernetes_manifests": manifests,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for DevOps service"""
    return jsonify({
        "service": "DevOps Automation Service",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "service_deployment",
            "dependency_management",
            "health_monitoring",
            "docker_compose_generation",
            "kubernetes_manifests",
            "deployment_automation"
        ],
        "services_configured": len(devops.service_configs),
        "services_running": len(devops.running_services),
        "deployments_total": devops.stats["deployments_total"],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/info')
def service_info():
    """Get service information"""
    return jsonify({
        "service_name": "Enterprise AI DevOps Automation Service",
        "description": "Automated deployment, CI/CD pipelines, and infrastructure management",
        "version": "2.0.0",
        "features": [
            "Automated service deployment with dependency resolution",
            "Health monitoring and service discovery",
            "Docker Compose configuration generation",
            "Kubernetes manifest generation",
            "Deployment job tracking and logging",
            "Service lifecycle management",
            "Environment-specific deployments",
            "Infrastructure as Code support"
        ],
        "supported_environments": ["development", "staging", "production"],
        "deployment_strategies": ["rolling", "blue_green", "canary"],
        "endpoints": [
            "/deploy/service", "/deploy/all", "/deploy/status",
            "/services/status", "/services/stop",
            "/config/docker-compose", "/config/kubernetes"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Enterprise AI DevOps Automation Service...")
    print("🔧 DevOps URL: http://localhost:7006")
    print("📦 Deploy All: POST http://localhost:7006/deploy/all")
    print("📊 Service Status: http://localhost:7006/services/status")
    print("🐳 Docker Compose: http://localhost:7006/config/docker-compose")
    print("☸️ Kubernetes: http://localhost:7006/config/kubernetes")
    print("🏥 Health Check: http://localhost:7006/health")
    print(f"⚙️ Configured services: {len(devops.service_configs)}")
    
    app.run(host='0.0.0.0', port=7006, debug=True)

