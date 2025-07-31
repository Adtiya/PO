"""
User service for the Enterprise AI System.
Handles user management operations and profile management.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import structlog

from app.models.user import User, UserProfile
from app.models.auth import UserRole, Role, Permission
from app.core.exceptions import ValidationException, AuthenticationException

logger = structlog.get_logger(__name__)

class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            return user
        except Exception as e:
            logger.error("Failed to get user by ID", error=str(e), user_id=user_id)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            return user
        except Exception as e:
            logger.error("Failed to get user by email", error=str(e), email=email)
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            user = self.db.query(User).filter(User.username == username).first()
            return user
        except Exception as e:
            logger.error("Failed to get user by username", error=str(e), username=username)
            return None
    
    async def get_user_with_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user with roles and permissions."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Get user roles
            user_roles = self.db.query(UserRole).join(Role).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active == True,
                    Role.is_active == True
                )
            ).all()
            
            roles = []
            permissions = set()
            
            for user_role in user_roles:
                role = user_role.role
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "display_name": role.display_name,
                    "description": role.description
                })
                
                # Get role permissions
                role_permissions = role.get_all_permissions(self.db)
                for perm in role_permissions:
                    permissions.add(perm.name)
            
            return {
                "roles": roles,
                "permissions": list(permissions)
            }
            
        except Exception as e:
            logger.error("Failed to get user with permissions", error=str(e), user_id=user_id)
            return {"roles": [], "permissions": []}
    
    async def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        **kwargs
    ) -> User:
        """Create a new user."""
        try:
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                **kwargs
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info("User created successfully", user_id=str(user.id), email=email)
            return user
            
        except Exception as e:
            logger.error("Failed to create user", error=str(e), email=email)
            self.db.rollback()
            raise ValidationException("Failed to create user")
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info("User updated successfully", user_id=user_id)
            return user
            
        except Exception as e:
            logger.error("Failed to update user", error=str(e), user_id=user_id)
            self.db.rollback()
            return None
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = False
            self.db.commit()
            
            logger.info("User deactivated", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to deactivate user", error=str(e), user_id=user_id)
            self.db.rollback()
            return False
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_active = True
            self.db.commit()
            
            logger.info("User activated", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to activate user", error=str(e), user_id=user_id)
            self.db.rollback()
            return False
    
    async def verify_user_email(self, user_id: str) -> bool:
        """Mark user email as verified."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            self.db.commit()
            
            logger.info("User email verified", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to verify user email", error=str(e), user_id=user_id)
            self.db.rollback()
            return False
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """List users with filtering and pagination."""
        try:
            query = self.db.query(User)
            
            if search:
                search_filter = or_(
                    User.email.ilike(f"%{search}%"),
                    User.username.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%")
                )
                query = query.filter(search_filter)
            
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            users = query.offset(skip).limit(limit).all()
            return users
            
        except Exception as e:
            logger.error("Failed to list users", error=str(e))
            return []
        return None
    
    async def update_last_activity(self, user_id: str) -> bool:
        """Update user's last activity timestamp."""
        # TODO: Implement last activity update
        return True
    
    async def get_user_with_permissions(self, user_id: str) -> Dict[str, Any]:
        """Get user with roles and permissions."""
        # TODO: Implement user with permissions retrieval
        return {
            "roles": [],
            "permissions": []
        }

