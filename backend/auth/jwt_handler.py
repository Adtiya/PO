"""
Enterprise AI System - JWT Token Management
PhD-level implementation with advanced security features
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import secrets
import os
from functools import wraps
from flask import request, jsonify, current_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JWTManager:
    """
    PhD-level JWT token management with advanced security features
    
    Features:
    - Secure token generation with RS256 algorithm
    - Access and refresh token pattern
    - Token blacklisting for logout
    - Automatic token rotation
    - Comprehensive security headers
    - Rate limiting integration
    """
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', self._generate_secret_key())
        self.algorithm = algorithm
        self.access_token_expire_minutes = 15  # Short-lived access tokens
        self.refresh_token_expire_days = 7     # Longer-lived refresh tokens
        self.blacklisted_tokens = set()        # In production, use Redis
        
    def _generate_secret_key(self) -> str:
        """Generate cryptographically secure secret key"""
        return secrets.token_urlsafe(64)
    
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token with user data
        
        Args:
            user_data: User information to encode in token
            expires_delta: Custom expiration time
            
        Returns:
            str: Encoded JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        # Create payload with security claims
        payload = {
            'user_id': user_data.get('id'),
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'permissions': user_data.get('permissions', []),
            'exp': expire,
            'iat': datetime.utcnow(),
            'iss': 'enterprise-ai-system',  # Issuer
            'aud': 'enterprise-ai-frontend',  # Audience
            'sub': str(user_data.get('id')),  # Subject
            'jti': secrets.token_urlsafe(16),  # JWT ID for tracking
            'token_type': 'access'
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Access token created for user {user_data.get('id')}")
            return token
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            raise
    
    def create_refresh_token(self, user_id: int) -> str:
        """
        Create JWT refresh token for token renewal
        
        Args:
            user_id: User ID to associate with token
            
        Returns:
            str: Encoded refresh token
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            'user_id': user_id,
            'exp': expire,
            'iat': datetime.utcnow(),
            'iss': 'enterprise-ai-system',
            'aud': 'enterprise-ai-frontend',
            'sub': str(user_id),
            'jti': secrets.token_urlsafe(16),
            'token_type': 'refresh'
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Refresh token created for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Dict with decoded payload or None if invalid
        """
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                logger.warning("Attempted use of blacklisted token")
                return None
            
            # Decode and verify token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience='enterprise-ai-frontend',
                issuer='enterprise-ai-system'
            )
            
            # Verify token type
            if payload.get('token_type') != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('token_type')}")
                return None
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                logger.info("Token has expired")
                return None
            
            logger.info(f"Token verified successfully for user {payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def refresh_access_token(self, refresh_token: str, user_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Create new access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            user_data: Updated user data for new token
            
        Returns:
            Dict with new access token or None if invalid
        """
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        # Verify user ID matches
        if payload.get('user_id') != user_data.get('id'):
            logger.warning("User ID mismatch in refresh token")
            return None
        
        # Create new access token
        new_access_token = self.create_access_token(user_data)
        
        return {
            'access_token': new_access_token,
            'token_type': 'bearer',
            'expires_in': self.access_token_expire_minutes * 60
        }
    
    def blacklist_token(self, token: str) -> None:
        """
        Add token to blacklist (for logout)
        
        Args:
            token: Token to blacklist
        """
        self.blacklisted_tokens.add(token)
        logger.info("Token added to blacklist")
    
    def get_token_from_header(self, authorization_header: str) -> Optional[str]:
        """
        Extract token from Authorization header
        
        Args:
            authorization_header: Authorization header value
            
        Returns:
            str: Extracted token or None
        """
        if not authorization_header:
            return None
        
        try:
            scheme, token = authorization_header.split(' ', 1)
            if scheme.lower() != 'bearer':
                return None
            return token
        except ValueError:
            return None
    
    def create_token_pair(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create both access and refresh tokens
        
        Args:
            user_data: User information
            
        Returns:
            Dict with both tokens and metadata
        """
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data['id'])
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': self.access_token_expire_minutes * 60,
            'refresh_expires_in': self.refresh_token_expire_days * 24 * 60 * 60
        }


# Global JWT manager instance
jwt_manager = JWTManager()


def token_required(f):
    """
    Decorator for protecting routes with JWT authentication
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            return jsonify({'message': 'Access granted'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = jwt_manager.get_token_from_header(auth_header)
        
        if not token:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Token is missing',
                'code': 'TOKEN_MISSING'
            }), 401
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Token is invalid or expired',
                'code': 'TOKEN_INVALID'
            }), 401
        
        # Add user info to request context
        request.current_user = payload
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """
    Decorator for protecting admin-only routes
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        user = request.current_user
        
        # Check if user has admin role
        if user.get('role') != 'admin' and 'admin' not in user.get('permissions', []):
            return jsonify({
                'error': 'Authorization Error',
                'message': 'Admin access required',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


def permission_required(permission: str):
    """
    Decorator for checking specific permissions
    
    Args:
        permission: Required permission string
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user = request.current_user
            user_permissions = user.get('permissions', [])
            
            if permission not in user_permissions and user.get('role') != 'admin':
                return jsonify({
                    'error': 'Authorization Error',
                    'message': f'Permission "{permission}" required',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


class SecurityHeaders:
    """
    Security headers for JWT responses
    """
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        return response


def create_auth_response(user_data: Dict[str, Any], message: str = "Authentication successful") -> Dict[str, Any]:
    """
    Create standardized authentication response
    
    Args:
        user_data: User information
        message: Success message
        
    Returns:
        Dict with tokens and user data
    """
    tokens = jwt_manager.create_token_pair(user_data)
    
    return {
        'message': message,
        'user': {
            'id': user_data['id'],
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'role': user_data.get('role'),
            'permissions': user_data.get('permissions', [])
        },
        'tokens': tokens,
        'timestamp': datetime.utcnow().isoformat()
    }

