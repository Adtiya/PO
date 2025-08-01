#!/usr/bin/env python3
"""
Script to fix all auth endpoints to use proper dependency injection.
"""

import re

# Read the auth endpoints file
with open('/home/ubuntu/enterprise_system/backend/app/api/v1/endpoints/auth.py', 'r') as f:
    content = f.read()

# Replace all instances of service dependencies
replacements = [
    # Replace AuthService = Depends() with db: Session = Depends(get_sync_db)
    (r'auth_service: AuthService = Depends\(\)', 'db: Session = Depends(get_sync_db)'),
    (r'user_service: UserService = Depends\(\)', 'db: Session = Depends(get_sync_db)'),
    
    # Replace service usage patterns
    (r'auth_service\.', 'AuthService(db).'),
    (r'user_service\.', 'UserService(db).'),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Handle cases where both services are used - need to create instances
function_fixes = [
    # Fix register function
    (r'async def register\(\s*request: RegisterRequest,\s*http_request: Request,\s*db: Session = Depends\(get_sync_db\)\s*\):', 
     '''async def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_sync_db)
):'''),
    
    # Add service instantiation after function start
    (r'("""Register new user account\."""\s*try:\s*# Get client information)',
     '''"""Register new user account."""
    try:
        # Create service instances
        auth_service = AuthService(db)
        user_service = UserService(db)
        
        # Get client information'''),
]

for pattern, replacement in function_fixes:
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

# Write the fixed content back
with open('/home/ubuntu/enterprise_system/backend/app/api/v1/endpoints/auth.py', 'w') as f:
    f.write(content)

print("Fixed all auth endpoints!")

