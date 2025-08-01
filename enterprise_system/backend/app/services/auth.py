"""
Authentication service for the Enterprise AI System.
Handles user authentication, token management, and security operations.
"""

from typing import Optional, Dict, Any
import structlog
import hashlib
import secrets
import jwt
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.exceptions import AuthenticationException, ValidationException
from app.core.config import get_settings
from app.models.user import User
from app.models.auth import UserSession, PasswordResetToken, EmailVerificationToken

logger = structlog.get_logger(__name__)
settings = get_settings()

class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _generate_jwt_token(self, payload: Dict[str, Any], expires_delta: timedelta) -> str:
        """Generate JWT token with expiration."""
        expire = datetime.utcnow() + expires_delta
        payload.update({"exp": expire, "iat": datetime.utcnow()})
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _decode_jwt_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationException("Invalid token")
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user and return tokens."""
        try:
            # Find user by email
            result = await self.db.execute(select(User).filter(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                raise AuthenticationException("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                raise AuthenticationException("Account is deactivated")
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                raise AuthenticationException("Invalid email or password")
            
            # Generate tokens
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            refresh_token_expires = timedelta(days=self.refresh_token_expire_days)
            
            access_token_payload = {
                "user_id": str(user.id),
                "email": user.email,
                "type": "access"
            }
            
            refresh_token_payload = {
                "user_id": str(user.id),
                "email": user.email,
                "type": "refresh"
            }
            
            access_token = self._generate_jwt_token(access_token_payload, access_token_expires)
            refresh_token = self._generate_jwt_token(refresh_token_payload, refresh_token_expires)
            
            # Create user session
            session_token = secrets.token_urlsafe(32)
            session_expires = datetime.utcnow() + (refresh_token_expires if remember_me else access_token_expires)
            
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=session_expires,
                is_active=True,
                created_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow()
            )
            
            self.db.add(user_session)
            try:
                await self.db.commit()
            except Exception as db_error:
                await self.db.rollback()
                logger.error("Database commit failed during authentication", error=str(db_error), email=email)
                raise AuthenticationException("Authentication failed due to database error")
            
            logger.info("User authenticated successfully", user_id=str(user.id), email=email)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_verified": user.is_verified
                }
            }
            
        except (AuthenticationException, ValidationException):
            raise
        except Exception as e:
            logger.error("Authentication failed", error=str(e), email=email)
            raise AuthenticationException("Authentication failed")
    
    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        username: Optional[str] = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> str:
        """Register new user."""
        try:
            # Check if user already exists
            existing_user = self.db.query(User).filter(
                or_(User.email == email, User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    raise ValidationException("Email already registered")
                else:
                    raise ValidationException("Username already taken")
            
            # Generate username if not provided
            if not username:
                username = email.split("@")[0]
                counter = 1
                original_username = username
                while self.db.query(User).filter(User.username == username).first():
                    username = f"{original_username}{counter}"
                    counter += 1
            
            # Validate password strength
            if len(password) < 8:
                raise ValidationException("Password must be at least 8 characters long")
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False,  # Email verification required
                created_at=datetime.utcnow()
            )
            
            self.db.add(user)
            try:
                self.db.commit()
                self.db.refresh(user)
            except Exception as db_error:
                self.db.rollback()
                logger.error("Database commit failed during user registration", error=str(db_error), email=email)
                raise ValidationException("User registration failed due to database error")
            
            # Generate email verification token
            verification_token = EmailVerificationToken(
                user_id=user.id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                created_at=datetime.utcnow()
            )
            self.db.add(verification_token)
            try:
                self.db.commit()
            except Exception as db_error:
                self.db.rollback()
                logger.error("Database commit failed during verification token creation", error=str(db_error), email=email)
                raise ValidationException("User registration failed due to database error")
            
            logger.info("User registered successfully", user_id=str(user.id), email=email)
            
            return str(user.id)
            
        except (ValidationException, AuthenticationException):
            raise
        except Exception as e:
            logger.error("User registration failed", error=str(e), email=email)
            self.db.rollback()
            raise ValidationException("Registration failed")
    
    async def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode access token."""
        try:
            payload = self._decode_jwt_token(token)
            
            if payload.get("type") != "access":
                raise AuthenticationException("Invalid token type")
            
            return payload
            
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise AuthenticationException("Invalid token")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Generate new access token from refresh token."""
        try:
            payload = self._decode_jwt_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise AuthenticationException("Invalid token type")
            
            user_id = payload.get("user_id")
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise AuthenticationException("User not found or inactive")
            
            # Generate new access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            access_token_payload = {
                "user_id": str(user.id),
                "email": user.email,
                "type": "access"
            }
            
            access_token = self._generate_jwt_token(access_token_payload, access_token_expires)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error("Token refresh failed", error=str(e))
            raise AuthenticationException("Token refresh failed")
    
    async def logout_user(self, user_id: str, session_token: Optional[str] = None) -> bool:
        """Logout user and invalidate sessions."""
        try:
            query = self.db.query(UserSession).filter(UserSession.user_id == user_id)
            
            if session_token:
                query = query.filter(UserSession.session_token == session_token)
            
            sessions = query.all()
            
            for session in sessions:
                session.is_active = False
                session.logout_at = datetime.utcnow()
                session.logout_reason = "user_logout"
            
            self.db.commit()
            
            logger.info("User logged out successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Logout failed", error=str(e), user_id=user_id)
            return False
    
    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate password reset token."""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                # Don't reveal if email exists
                return None
            
            # Invalidate existing tokens
            existing_tokens = self.db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.is_used == False
                )
            ).all()
            
            for token in existing_tokens:
                token.is_used = True
                token.used_at = datetime.utcnow()
            
            # Create new token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=secrets.token_urlsafe(32),
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow()
            )
            
            self.db.add(reset_token)
            self.db.commit()
            
            logger.info("Password reset token generated", user_id=str(user.id))
            return reset_token.token
            
        except Exception as e:
            logger.error("Password reset token generation failed", error=str(e))
            return None
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password using token."""
        try:
            reset_token = self.db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if not reset_token or not reset_token.is_valid:
                raise AuthenticationException("Invalid or expired token")
            
            # Validate password strength
            if len(new_password) < 8:
                raise ValidationException("Password must be at least 8 characters long")
            
            # Update user password
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            if not user:
                raise AuthenticationException("User not found")
            
            user.password_hash = self._hash_password(new_password)
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.used_at = datetime.utcnow()
            
            # Invalidate all user sessions
            user_sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user.id
            ).all()
            
            for session in user_sessions:
                session.is_active = False
                session.logout_at = datetime.utcnow()
                session.logout_reason = "password_reset"
            
            self.db.commit()
            
            logger.info("Password reset successfully", user_id=str(user.id))
            return True
            
        except Exception as e:
            logger.error("Password reset failed", error=str(e))
            self.db.rollback()
            return False

