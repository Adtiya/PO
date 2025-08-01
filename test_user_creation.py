#!/usr/bin/env python3
"""
Test script to debug user creation issues.
"""

import sys
import os
sys.path.append('/home/ubuntu/enterprise_system/backend')

from app.db.database import get_sync_db
from app.services.auth import AuthService
from app.models.user import User
import traceback

async def test_user_creation():
    """Test user creation directly."""
    try:
        # Get database session
        db = next(get_sync_db())
        print("✅ Database connection successful")
        
        # Create auth service
        auth_service = AuthService(db)
        print("✅ AuthService created")
        
        # Test user creation
        print("🔄 Testing user creation...")
        
        user_id = await auth_service.register_user(
            email="test@example.com",
            password="SecurePass123!",
            first_name="Test",
            last_name="User"
        )
        
        print(f"✅ User created successfully with ID: {user_id}")
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            print(f"✅ User verified in database: {user.email}")
        else:
            print("❌ User not found in database")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_user_creation())

