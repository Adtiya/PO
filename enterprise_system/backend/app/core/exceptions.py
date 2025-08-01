"""
Custom exception classes for the Enterprise AI System.
Provides structured error handling with detailed information.
"""

from typing import Any, Dict, Optional, List


class BaseAPIException(Exception):
    """Base exception class for all API exceptions."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationException(BaseAPIException):
    """Raised when request validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.field_errors = field_errors or {}
        super().__init__(
            message=message,
            details={**(details or {}), "field_errors": self.field_errors},
            error_code="VALIDATION_ERROR"
        )


class AuthenticationException(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(BaseAPIException):
    """Raised when authorization fails."""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.required_permission = required_permission
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "required_permission": required_permission,
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundException(BaseAPIException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            error_code="NOT_FOUND"
        )


class ConflictException(BaseAPIException):
    """Raised when a request conflicts with current state."""
    
    def __init__(
        self,
        message: str = "Request conflicts with current state",
        conflicting_field: Optional[str] = None,
        conflicting_value: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.conflicting_field = conflicting_field
        self.conflicting_value = conflicting_value
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "conflicting_field": conflicting_field,
                "conflicting_value": conflicting_value
            },
            error_code="CONFLICT"
        )


class RateLimitException(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.retry_after = retry_after
        self.limit_type = limit_type
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "retry_after": retry_after,
                "limit_type": limit_type
            },
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ExternalServiceException(BaseAPIException):
    """Raised when external service call fails."""
    
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.service_name = service_name
        self.status_code = status_code
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "service_name": service_name,
                "status_code": status_code
            },
            error_code="EXTERNAL_SERVICE_ERROR"
        )


class DatabaseException(BaseAPIException):
    """Raised when database operation fails."""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        table: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.table = table
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "operation": operation,
                "table": table
            },
            error_code="DATABASE_ERROR"
        )


class FileProcessingException(BaseAPIException):
    """Raised when file processing fails."""
    
    def __init__(
        self,
        message: str = "File processing failed",
        filename: Optional[str] = None,
        file_type: Optional[str] = None,
        processing_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.filename = filename
        self.file_type = file_type
        self.processing_stage = processing_stage
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "filename": filename,
                "file_type": file_type,
                "processing_stage": processing_stage
            },
            error_code="FILE_PROCESSING_ERROR"
        )


class LLMException(BaseAPIException):
    """Raised when LLM operation fails."""
    
    def __init__(
        self,
        message: str = "LLM operation failed",
        model_name: Optional[str] = None,
        operation_type: Optional[str] = None,
        token_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.operation_type = operation_type
        self.token_count = token_count
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "model_name": model_name,
                "operation_type": operation_type,
                "token_count": token_count
            },
            error_code="LLM_ERROR"
        )


class ConfigurationException(BaseAPIException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.config_key = config_key
        self.expected_type = expected_type
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "config_key": config_key,
                "expected_type": expected_type
            },
            error_code="CONFIGURATION_ERROR"
        )


class SecurityException(BaseAPIException):
    """Raised when security violation is detected."""
    
    def __init__(
        self,
        message: str = "Security violation detected",
        violation_type: Optional[str] = None,
        severity: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.violation_type = violation_type
        self.severity = severity
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "violation_type": violation_type,
                "severity": severity
            },
            error_code="SECURITY_VIOLATION"
        )


class ComplianceException(BaseAPIException):
    """Raised when compliance violation is detected."""
    
    def __init__(
        self,
        message: str = "Compliance violation detected",
        framework: Optional[str] = None,
        requirement: Optional[str] = None,
        data_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.framework = framework
        self.requirement = requirement
        self.data_type = data_type
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "framework": framework,
                "requirement": requirement,
                "data_type": data_type
            },
            error_code="COMPLIANCE_VIOLATION"
        )


class BusinessLogicException(BaseAPIException):
    """Raised when business logic validation fails."""
    
    def __init__(
        self,
        message: str = "Business logic validation failed",
        rule: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.rule = rule
        self.context = context or {}
        
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "rule": rule,
                "context": self.context
            },
            error_code="BUSINESS_LOGIC_ERROR"
        )


# ============================================================================
# EXCEPTION UTILITIES
# ============================================================================

def create_validation_exception(errors: Dict[str, List[str]]) -> ValidationException:
    """Create a validation exception from field errors."""
    error_count = sum(len(field_errors) for field_errors in errors.values())
    message = f"Validation failed with {error_count} error(s)"
    return ValidationException(message=message, field_errors=errors)


def create_not_found_exception(
    resource_type: str,
    resource_id: str
) -> NotFoundException:
    """Create a not found exception for a specific resource."""
    message = f"{resource_type.title()} with ID '{resource_id}' not found"
    return NotFoundException(
        message=message,
        resource_type=resource_type,
        resource_id=resource_id
    )


def create_permission_denied_exception(
    permission: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> AuthorizationException:
    """Create a permission denied exception."""
    if resource_type and resource_id:
        message = f"Permission '{permission}' required for {resource_type} '{resource_id}'"
    elif resource_type:
        message = f"Permission '{permission}' required for {resource_type} resources"
    else:
        message = f"Permission '{permission}' required"
    
    return AuthorizationException(
        message=message,
        required_permission=permission,
        resource_type=resource_type,
        resource_id=resource_id
    )


def create_conflict_exception(
    field: str,
    value: str,
    resource_type: Optional[str] = None
) -> ConflictException:
    """Create a conflict exception for duplicate values."""
    if resource_type:
        message = f"{resource_type.title()} with {field} '{value}' already exists"
    else:
        message = f"Value '{value}' for field '{field}' already exists"
    
    return ConflictException(
        message=message,
        conflicting_field=field,
        conflicting_value=value
    )


# Export all exception classes
__all__ = [
    "BaseAPIException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "ExternalServiceException",
    "DatabaseException",
    "FileProcessingException",
    "LLMException",
    "ConfigurationException",
    "SecurityException",
    "ComplianceException",
    "BusinessLogicException",
    "create_validation_exception",
    "create_not_found_exception",
    "create_permission_denied_exception",
    "create_conflict_exception"
]

