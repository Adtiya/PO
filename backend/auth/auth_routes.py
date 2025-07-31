"""
Enterprise AI System - Authentication Routes
PhD-level implementation with comprehensive security features
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import re
from email_validator import validate_email, EmailNotValidError

from models.user import User, Role, UserSession
from database import get_db
from auth.jwt_handler import jwt_manager, create_auth_response, SecurityHeaders
from auth.rate_limiter import RateLimiter
from auth.input_validator import InputValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Initialize rate limiter
rate_limiter = RateLimiter()

# Initialize input validator
validator = InputValidator()


@auth_bp.route('/register', methods=['POST'])
@rate_limiter.limit("5 per minute")  # Prevent registration spam
def register():
    """
    User registration endpoint with comprehensive validation
    
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",  # Optional
        "department": "Engineering",  # Optional
        "job_title": "Software Engineer"  # Optional
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Request body must be valid JSON',
                'code': 'INVALID_JSON'
            }), 400
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'Validation Error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'code': 'MISSING_FIELDS',
                'missing_fields': missing_fields
            }), 400
        
        # Extract and validate data
        email = data['email'].strip().lower()
        password = data['password']
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()
        phone = data.get('phone', '').strip() if data.get('phone') else None
        department = data.get('department', '').strip() if data.get('department') else None
        job_title = data.get('job_title', '').strip() if data.get('job_title') else None
        
        # Validate email format
        try:
            validated_email = validate_email(email)
            email = validated_email.email
        except EmailNotValidError as e:
            return jsonify({
                'error': 'Validation Error',
                'message': f'Invalid email format: {str(e)}',
                'code': 'INVALID_EMAIL'
            }), 400
        
        # Validate password strength
        password_validation = User.validate_password_strength(password)
        if not password_validation['is_valid']:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Password does not meet security requirements',
                'code': 'WEAK_PASSWORD',
                'issues': password_validation['issues'],
                'recommendations': password_validation['recommendations']
            }), 400
        
        # Validate name fields
        name_validation = validator.validate_name_fields(first_name, last_name)
        if not name_validation['is_valid']:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Invalid name format',
                'code': 'INVALID_NAME',
                'issues': name_validation['issues']
            }), 400
        
        # Validate phone if provided
        if phone:
            phone_validation = validator.validate_phone(phone)
            if not phone_validation['is_valid']:
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Invalid phone number format',
                    'code': 'INVALID_PHONE',
                    'issues': phone_validation['issues']
                }), 400
            phone = phone_validation['formatted']
        
        # Database operations
        db = next(get_db())
        
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return jsonify({
                    'error': 'Validation Error',
                    'message': 'Email already registered',
                    'code': 'EMAIL_EXISTS'
                }), 409
            
            # Get default role (user)
            default_role = db.query(Role).filter(Role.name == 'user').first()
            if not default_role:
                # Create default role if it doesn't exist
                default_role = Role(
                    name='user',
                    description='Standard user role',
                    permissions='["read_profile", "update_profile"]'
                )
                db.add(default_role)
                db.flush()
            
            # Create new user
            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hashed_password=User.hash_password(password),
                phone=phone,
                department=department,
                job_title=job_title,
                role_id=default_role.id,
                is_active=True,
                is_verified=False  # Require email verification
            )
            
            # Generate verification token
            verification_token = new_user.generate_verification_token()
            
            db.add(new_user)
            db.commit()
            
            logger.info(f"New user registered: {email}")
            
            # Prepare response (exclude sensitive data)
            user_data = new_user.to_dict()
            
            return jsonify({
                'message': 'Registration successful',
                'user': user_data,
                'verification_required': True,
                'verification_token': verification_token,  # In production, send via email
                'code': 'REGISTRATION_SUCCESS'
            }), 201
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Database integrity error during registration: {str(e)}")
            return jsonify({
                'error': 'Registration Error',
                'message': 'Email already exists or database constraint violation',
                'code': 'INTEGRITY_ERROR'
            }), 409
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during registration: {str(e)}")
            return jsonify({
                'error': 'Registration Error',
                'message': 'Failed to create user account',
                'code': 'DATABASE_ERROR'
            }), 500
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limiter.limit("10 per minute")  # Prevent brute force attacks
def login():
    """
    User login endpoint with security features
    
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "remember_me": false  # Optional
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Request body must be valid JSON',
                'code': 'INVALID_JSON'
            }), 400
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({
                'error': 'Validation Error',
                'message': 'Email and password are required',
                'code': 'MISSING_CREDENTIALS'
            }), 400
        
        # Get client info for session tracking
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Database operations
        db = next(get_db())
        
        try:
            # Find user by email
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }), 401
            
            # Check if account is locked
            if user.is_account_locked():
                logger.warning(f"Login attempt on locked account: {email}")
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'Account is temporarily locked due to multiple failed login attempts',
                    'code': 'ACCOUNT_LOCKED',
                    'locked_until': user.account_locked_until.isoformat()
                }), 423
            
            # Check if account is active
            if not user.is_active:
                logger.warning(f"Login attempt on inactive account: {email}")
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'Account is deactivated',
                    'code': 'ACCOUNT_INACTIVE'
                }), 401
            
            # Verify password
            if not user.verify_password(password):
                # Increment failed login attempts
                user.increment_failed_login()
                db.commit()
                
                logger.warning(f"Failed login attempt for user: {email}")
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS',
                    'attempts_remaining': max(0, 5 - user.failed_login_attempts)
                }), 401
            
            # Reset failed login attempts on successful login
            user.reset_failed_login_attempts()
            
            # Get user role and permissions
            role_name = user.role.name if user.role else 'user'
            permissions = []
            if user.role and user.role.permissions:
                try:
                    import json
                    permissions = json.loads(user.role.permissions)
                except:
                    permissions = []
            
            # Prepare user data for token
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role_name,
                'permissions': permissions
            }
            
            # Create session record
            session_expires = datetime.utcnow() + timedelta(days=7 if remember_me else 1)
            user_session = UserSession(
                user_id=user.id,
                session_token=jwt_manager._generate_secret_key()[:32],
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=session_expires
            )
            
            db.add(user_session)
            db.commit()
            
            logger.info(f"Successful login for user: {email}")
            
            # Create authentication response
            auth_response = create_auth_response(user_data, "Login successful")
            auth_response['session_id'] = user_session.id
            
            # Add security headers
            response = jsonify(auth_response)
            return SecurityHeaders.add_security_headers(response), 200
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during login: {str(e)}")
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Login failed due to server error',
                'code': 'DATABASE_ERROR'
            }), 500
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    User logout endpoint - blacklist current token
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Authorization header required',
                'code': 'MISSING_TOKEN'
            }), 401
        
        token = jwt_manager.get_token_from_header(auth_header)
        if not token:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Invalid authorization header format',
                'code': 'INVALID_TOKEN_FORMAT'
            }), 401
        
        # Verify token before blacklisting
        payload = jwt_manager.verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Invalid or expired token',
                'code': 'INVALID_TOKEN'
            }), 401
        
        # Blacklist token
        jwt_manager.blacklist_token(token)
        
        # Deactivate session in database
        db = next(get_db())
        try:
            user_sessions = db.query(UserSession).filter(
                UserSession.user_id == payload['user_id'],
                UserSession.is_active == True
            ).all()
            
            for session in user_sessions:
                session.is_active = False
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error deactivating sessions: {str(e)}")
        finally:
            db.close()
        
        logger.info(f"User logged out: {payload.get('user_id')}")
        
        return jsonify({
            'message': 'Logout successful',
            'code': 'LOGOUT_SUCCESS'
        }), 200
    
    except Exception as e:
        logger.error(f"Unexpected error during logout: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@rate_limiter.limit("20 per minute")
def refresh_token():
    """
    Refresh access token using refresh token
    
    Expected JSON payload:
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    """
    try:
        data = request.get_json()
        if not data or not data.get('refresh_token'):
            return jsonify({
                'error': 'Validation Error',
                'message': 'Refresh token is required',
                'code': 'MISSING_REFRESH_TOKEN'
            }), 400
        
        refresh_token = data['refresh_token']
        
        # Verify refresh token
        payload = jwt_manager.verify_token(refresh_token, 'refresh')
        if not payload:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Invalid or expired refresh token',
                'code': 'INVALID_REFRESH_TOKEN'
            }), 401
        
        # Get user data from database
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == payload['user_id']).first()
            if not user or not user.is_active:
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'User not found or inactive',
                    'code': 'USER_NOT_FOUND'
                }), 401
            
            # Get updated user data
            role_name = user.role.name if user.role else 'user'
            permissions = []
            if user.role and user.role.permissions:
                try:
                    import json
                    permissions = json.loads(user.role.permissions)
                except:
                    permissions = []
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': role_name,
                'permissions': permissions
            }
            
            # Create new access token
            new_tokens = jwt_manager.refresh_access_token(refresh_token, user_data)
            if not new_tokens:
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'Failed to refresh token',
                    'code': 'REFRESH_FAILED'
                }), 401
            
            logger.info(f"Token refreshed for user: {user.id}")
            
            return jsonify({
                'message': 'Token refreshed successfully',
                'tokens': new_tokens,
                'user': {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role']
                }
            }), 200
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current user information from token
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Authorization header required',
                'code': 'MISSING_TOKEN'
            }), 401
        
        token = jwt_manager.get_token_from_header(auth_header)
        if not token:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Invalid authorization header format',
                'code': 'INVALID_TOKEN_FORMAT'
            }), 401
        
        # Verify token
        payload = jwt_manager.verify_token(token)
        if not payload:
            return jsonify({
                'error': 'Authentication Error',
                'message': 'Invalid or expired token',
                'code': 'INVALID_TOKEN'
            }), 401
        
        # Get user from database
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == payload['user_id']).first()
            if not user:
                return jsonify({
                    'error': 'Authentication Error',
                    'message': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 401
            
            return jsonify({
                'user': user.to_dict(),
                'permissions': payload.get('permissions', []),
                'role': payload.get('role', 'user')
            }), 200
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Unexpected error getting current user: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verify user email with verification token
    
    Expected JSON payload:
    {
        "token": "verification_token_here"
    }
    """
    try:
        data = request.get_json()
        if not data or not data.get('token'):
            return jsonify({
                'error': 'Validation Error',
                'message': 'Verification token is required',
                'code': 'MISSING_TOKEN'
            }), 400
        
        token = data['token']
        
        db = next(get_db())
        try:
            user = db.query(User).filter(User.verification_token == token).first()
            if not user:
                return jsonify({
                    'error': 'Verification Error',
                    'message': 'Invalid verification token',
                    'code': 'INVALID_TOKEN'
                }), 400
            
            # Mark user as verified
            user.is_verified = True
            user.verification_token = None
            db.commit()
            
            logger.info(f"Email verified for user: {user.email}")
            
            return jsonify({
                'message': 'Email verified successfully',
                'code': 'EMAIL_VERIFIED'
            }), 200
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {str(e)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'code': 'INTERNAL_ERROR'
        }), 500


# Error handlers
@auth_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'code': 'RATE_LIMIT_EXCEEDED'
    }), 429


@auth_bp.errorhandler(400)
def bad_request_handler(e):
    """Handle bad request errors"""
    return jsonify({
        'error': 'Bad Request',
        'message': 'Invalid request format or parameters',
        'code': 'BAD_REQUEST'
    }), 400

