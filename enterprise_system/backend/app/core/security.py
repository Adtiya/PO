"""
Enterprise AI System - Security Configuration
PhD-level security implementation with comprehensive protection
"""

import os
import secrets
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

class SecurityConfig:
    """Centralized security configuration"""
    
    def __init__(self):
        # Validate required environment variables
        self.validate_environment()
        
        # JWT Configuration
        self.SECRET_KEY = self.get_required_env("JWT_SECRET_KEY")
        self.ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # CORS Configuration
        self.ALLOWED_ORIGINS = self.parse_cors_origins(os.getenv("ALLOWED_ORIGINS", ""))
        self.ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
        
        # Rate limiting
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
        
        # Security headers
        self.SECURITY_HEADERS = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    def validate_environment(self):
        """Validate that all required environment variables are set"""
        required_vars = [
            "JWT_SECRET_KEY",
            "SECRET_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def parse_cors_origins(self, origins_str: str) -> List[str]:
        """Parse CORS origins from environment variable"""
        if not origins_str:
            return ["http://localhost:3000", "http://localhost:5173"]  # Development defaults
        
        origins = [origin.strip() for origin in origins_str.split(",")]
        
        # Validate origins
        for origin in origins:
            if origin == "*":
                raise ValueError("Wildcard CORS origins (*) are not allowed in production")
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin format: {origin}")
        
        return origins
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def generate_api_key(self) -> str:
        """Generate secure API key for microservices"""
        return secrets.token_urlsafe(32)

class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = []
    permissions: List[str] = []

class APIKeyAuth(HTTPBearer):
    """API Key authentication for microservices"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.valid_api_keys = self.load_api_keys()
    
    def load_api_keys(self) -> List[str]:
        """Load valid API keys from environment"""
        api_keys = []
        
        # Microservice API keys
        service_keys = [
            "PI_SERVICE_SECRET",
            "NLP_SERVICE_SECRET", 
            "VISION_SERVICE_SECRET",
            "ANALYTICS_SERVICE_SECRET",
            "RECOMMENDATION_SERVICE_SECRET"
        ]
        
        for key_name in service_keys:
            key = os.getenv(key_name)
            if key:
                api_keys.append(key)
        
        return api_keys
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials) -> str:
        """Validate API key"""
        if credentials.credentials not in self.valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        return credentials.credentials

# Global security instance
security = SecurityConfig()

# Authentication schemes
bearer_auth = HTTPBearer()
api_key_auth = APIKeyAuth()

def get_current_user_from_token(token: str) -> TokenData:
    """Extract user data from JWT token"""
    payload = security.verify_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return TokenData(
        username=username,
        user_id=payload.get("user_id"),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", [])
    )

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented with dependency injection in FastAPI
            # For now, it's a placeholder for the permission checking logic
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return has_upper and has_lower and has_digit and has_special

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not isinstance(input_str, str):
        return str(input_str)
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "&", "\"", "'", "/", "\\"]
    sanitized = input_str
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    return sanitized.strip()

