"""
Comprehensive API Validation Schemas
Enterprise-grade input validation using Pydantic
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re

class ValidationError(Exception):
    """Custom validation error"""
    pass

class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    USER = "user"

class ServiceStatus(str, Enum):
    """Service status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

# Authentication Schemas
class LoginRequest(BaseModel):
    """Login request validation"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    remember_me: Optional[bool] = Field(False, description="Remember login session")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class RegisterRequest(BaseModel):
    """User registration validation"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    username: Optional[str] = Field(None, min_length=3, max_length=30, description="Username")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not re.match(r'^[a-zA-Z\s\-\']+$', v):
            raise ValueError('Names can only contain letters, spaces, hyphens, and apostrophes')
        return v

# User Management Schemas
class UserCreateRequest(BaseModel):
    """User creation request"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=30, description="Username")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    role: UserRole = Field(UserRole.USER, description="User role")
    is_active: Optional[bool] = Field(True, description="User active status")

class UserUpdateRequest(BaseModel):
    """User update request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

# AI Service Schemas
class NLPAnalysisRequest(BaseModel):
    """Natural Language Processing request"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
    analysis_type: Optional[str] = Field("comprehensive", description="Type of analysis")
    language: Optional[str] = Field("en", description="Text language")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()

class TextClassificationRequest(BaseModel):
    """Text classification request"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to classify")
    categories: List[str] = Field(..., min_items=2, max_items=20, description="Classification categories")
    
    @validator('categories')
    def validate_categories(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Categories must be unique')
        return v

class VisionAnalysisRequest(BaseModel):
    """Computer vision analysis request"""
    image_data: str = Field(..., description="Base64 encoded image data")
    analysis_type: Optional[str] = Field("comprehensive", description="Type of analysis")
    max_objects: Optional[int] = Field(10, ge=1, le=50, description="Maximum objects to detect")
    
    @validator('image_data')
    def validate_image_data(cls, v):
        if not v.startswith('data:image/'):
            raise ValueError('Invalid image data format')
        return v

class AnalyticsRequest(BaseModel):
    """Analytics request validation"""
    data: List[Dict[str, Any]] = Field(..., min_items=1, max_items=10000, description="Data for analysis")
    analysis_type: str = Field(..., description="Type of analytics")
    parameters: Optional[Dict[str, Any]] = Field({}, description="Analysis parameters")

class RecommendationRequest(BaseModel):
    """Recommendation request validation"""
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    item_ids: Optional[List[str]] = Field(None, description="Item IDs for recommendations")
    preferences: Optional[Dict[str, Any]] = Field({}, description="User preferences")
    max_recommendations: Optional[int] = Field(10, ge=1, le=100, description="Maximum recommendations")

# Response Schemas
class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="Error messages")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(False, description="Request success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class HealthCheckResponse(BaseModel):
    """Health check response"""
    service: str = Field(..., description="Service name")
    status: ServiceStatus = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")

# Validation Utilities
class RequestValidator:
    """Request validation utility class"""
    
    @staticmethod
    def validate_request(request_data: dict, schema_class: BaseModel) -> BaseModel:
        """Validate request data against schema"""
        try:
            return schema_class(**request_data)
        except Exception as e:
            raise ValidationError(f"Validation failed: {str(e)}")
    
    @staticmethod
    def validate_pagination(page: int = 1, limit: int = 10, max_limit: int = 100) -> tuple:
        """Validate pagination parameters"""
        if page < 1:
            raise ValidationError("Page must be greater than 0")
        if limit < 1:
            raise ValidationError("Limit must be greater than 0")
        if limit > max_limit:
            raise ValidationError(f"Limit cannot exceed {max_limit}")
        
        offset = (page - 1) * limit
        return offset, limit
    
    @staticmethod
    def validate_sort_params(sort_by: str, allowed_fields: List[str], order: str = "asc") -> tuple:
        """Validate sorting parameters"""
        if sort_by not in allowed_fields:
            raise ValidationError(f"Invalid sort field. Allowed: {', '.join(allowed_fields)}")
        if order.lower() not in ["asc", "desc"]:
            raise ValidationError("Order must be 'asc' or 'desc'")
        
        return sort_by, order.lower()

# Decorator for automatic validation
def validate_json(schema_class: BaseModel):
    """Decorator for automatic JSON validation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            try:
                if not request.is_json:
                    return jsonify(ErrorResponse(
                        error_code="INVALID_CONTENT_TYPE",
                        message="Content-Type must be application/json"
                    ).dict()), 400
                
                request_data = request.get_json()
                if not request_data:
                    return jsonify(ErrorResponse(
                        error_code="EMPTY_REQUEST",
                        message="Request body cannot be empty"
                    ).dict()), 400
                
                validated_data = RequestValidator.validate_request(request_data, schema_class)
                kwargs['validated_data'] = validated_data
                
                return func(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify(ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=str(e)
                ).dict()), 400
            except Exception as e:
                return jsonify(ErrorResponse(
                    error_code="INTERNAL_ERROR",
                    message="Internal server error"
                ).dict()), 500
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# Error handling utilities
class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> tuple:
        """Handle validation errors"""
        response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message=str(error)
        )
        return response.dict(), 400
    
    @staticmethod
    def handle_authentication_error(error: Exception) -> tuple:
        """Handle authentication errors"""
        response = ErrorResponse(
            error_code="AUTHENTICATION_ERROR",
            message="Authentication failed"
        )
        return response.dict(), 401
    
    @staticmethod
    def handle_authorization_error(error: Exception) -> tuple:
        """Handle authorization errors"""
        response = ErrorResponse(
            error_code="AUTHORIZATION_ERROR",
            message="Insufficient permissions"
        )
        return response.dict(), 403
    
    @staticmethod
    def handle_not_found_error(resource: str = "Resource") -> tuple:
        """Handle not found errors"""
        response = ErrorResponse(
            error_code="NOT_FOUND",
            message=f"{resource} not found"
        )
        return response.dict(), 404
    
    @staticmethod
    def handle_internal_error(error: Exception) -> tuple:
        """Handle internal server errors"""
        response = ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="Internal server error"
        )
        return response.dict(), 500

