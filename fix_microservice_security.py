#!/usr/bin/env python3
"""
Fix security issues in all microservices
- Remove hardcoded secrets
- Fix CORS configurations
- Add environment variable validation
"""

import os
import re
from pathlib import Path

def fix_microservice_security(service_path: str, service_name: str):
    """Fix security issues in a microservice"""
    main_py_path = Path(service_path)
    
    if not main_py_path.exists():
        print(f"❌ {service_name}: main.py not found at {service_path}")
        return
    
    print(f"🔧 Fixing {service_name}...")
    
    # Read current content
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Fix hardcoded SECRET_KEY
    secret_pattern = r"app\.config\['SECRET_KEY'\]\s*=\s*['\"][^'\"]*['\"]"
    
    # Determine service secret env var name
    env_var_name = f"{service_name.upper().replace('-', '_')}_SERVICE_SECRET"
    
    security_fix = f"""# 🔐 SECURITY: Load secret from environment
SECRET_KEY = os.getenv('{env_var_name}')
if not SECRET_KEY:
    raise ValueError("{env_var_name} environment variable is required")
app.config['SECRET_KEY'] = SECRET_KEY"""
    
    content = re.sub(secret_pattern, security_fix, content)
    
    # Fix CORS configuration
    cors_patterns = [
        r'CORS\(app\)',
        r'CORS\(app,\s*origins="\*"[^)]*\)',
        r'CORS\(app,\s*origins=\["?\*"?\][^)]*\)'
    ]
    
    cors_fix = """# 🌐 CORS: Secure origins only
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])"""
    
    for pattern in cors_patterns:
        content = re.sub(pattern, cors_fix, content)
    
    # Ensure os import is present
    if 'import os' not in content:
        content = 'import os\n' + content
    
    # Write fixed content
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print(f"✅ {service_name}: Security fixes applied")

def main():
    """Fix security issues in all microservices"""
    print("🔐 FIXING MICROSERVICE SECURITY ISSUES")
    print("="*50)
    
    # Microservices to fix
    microservices = [
        ("microservices/obr_service/src/main.py", "obr"),
        ("microservices/da_service/src/main.py", "da"),
        ("microservices/ai_nlp_service/nlp_ai_service/src/main.py", "ai-nlp"),
        ("microservices/ai_vision_service/vision_ai_service/src/main.py", "ai-vision"),
        ("microservices/ai_analytics_service/analytics_ai_service/src/main.py", "ai-analytics"),
        ("microservices/ai_recommendation_service/recommendation_ai_service/src/main.py", "ai-recommendation")
    ]
    
    base_path = Path("/home/ubuntu/enterprise_system")
    
    for service_path, service_name in microservices:
        full_path = base_path / service_path
        fix_microservice_security(str(full_path), service_name)
    
    print("\n🎉 All microservice security fixes completed!")
    print("\n📝 Next steps:")
    print("1. Create .env file with all required secrets")
    print("2. Set environment variables before starting services")
    print("3. Test all services with new security configuration")

if __name__ == "__main__":
    main()

