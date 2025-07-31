"""
Enterprise AI System - Input Validation
PhD-level implementation with comprehensive security validation
"""

import re
import phonenumbers
from typing import Dict, Any, List
from email_validator import validate_email, EmailNotValidError
import html
import bleach


class InputValidator:
    """
    PhD-level input validation with security-focused sanitization
    
    Features:
    - XSS prevention
    - SQL injection prevention
    - Input sanitization
    - Format validation
    - Length validation
    - Character set validation
    """
    
    def __init__(self):
        # Allowed HTML tags for rich text (very restrictive)
        self.allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
        self.allowed_attributes = {}
        
        # Common malicious patterns
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript URLs
            r'on\w+\s*=',                # Event handlers
            r'expression\s*\(',          # CSS expressions
            r'@import',                  # CSS imports
            r'<iframe[^>]*>',            # Iframes
            r'<object[^>]*>',            # Objects
            r'<embed[^>]*>',             # Embeds
            r'<link[^>]*>',              # Links
            r'<meta[^>]*>',              # Meta tags
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\b(OR|AND)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
            r'(--|#|/\*|\*/)',
            r'(\bxp_\w+)',
            r'(\bsp_\w+)',
        ]
    
    def sanitize_string(self, input_str: str, max_length: int = None) -> str:
        """
        Sanitize string input to prevent XSS and other attacks
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
        """
        if not isinstance(input_str, str):
            return ""
        
        # Trim whitespace
        sanitized = input_str.strip()
        
        # Limit length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # HTML escape
        sanitized = html.escape(sanitized)
        
        # Remove malicious patterns
        for pattern in self.malicious_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Additional XSS prevention
        sanitized = sanitized.replace('&lt;', '').replace('&gt;', '')
        
        return sanitized
    
    def sanitize_html(self, input_html: str) -> str:
        """
        Sanitize HTML content using bleach
        
        Args:
            input_html: HTML content to sanitize
            
        Returns:
            str: Sanitized HTML
        """
        if not isinstance(input_html, str):
            return ""
        
        return bleach.clean(
            input_html,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )
    
    def check_sql_injection(self, input_str: str) -> bool:
        """
        Check for potential SQL injection patterns
        
        Args:
            input_str: String to check
            
        Returns:
            bool: True if potential SQL injection detected
        """
        if not isinstance(input_str, str):
            return False
        
        for pattern in self.sql_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        
        return False
    
    def validate_email_format(self, email: str) -> Dict[str, Any]:
        """
        Validate email format and domain
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': False,
            'normalized': '',
            'issues': []
        }
        
        if not email or not isinstance(email, str):
            result['issues'].append('Email is required')
            return result
        
        # Basic sanitization
        email = self.sanitize_string(email.strip().lower(), 255)
        
        # Check for malicious content
        if self.check_sql_injection(email):
            result['issues'].append('Email contains invalid characters')
            return result
        
        try:
            # Use email-validator for comprehensive validation
            validated = validate_email(email)
            result['is_valid'] = True
            result['normalized'] = validated.email
        except EmailNotValidError as e:
            result['issues'].append(str(e))
        
        return result
    
    def validate_password_format(self, password: str) -> Dict[str, Any]:
        """
        Validate password format (not strength - that's in User model)
        
        Args:
            password: Password to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'issues': []
        }
        
        if not password or not isinstance(password, str):
            result['is_valid'] = False
            result['issues'].append('Password is required')
            return result
        
        # Check length
        if len(password) > 128:  # Reasonable maximum
            result['is_valid'] = False
            result['issues'].append('Password is too long (max 128 characters)')
        
        # Check for null bytes and control characters
        if '\x00' in password or any(ord(c) < 32 for c in password if c not in '\t\n\r'):
            result['is_valid'] = False
            result['issues'].append('Password contains invalid characters')
        
        return result
    
    def validate_name_fields(self, first_name: str, last_name: str) -> Dict[str, Any]:
        """
        Validate name fields
        
        Args:
            first_name: First name to validate
            last_name: Last name to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'issues': [],
            'sanitized': {
                'first_name': '',
                'last_name': ''
            }
        }
        
        # Validate first name
        if not first_name or not isinstance(first_name, str):
            result['is_valid'] = False
            result['issues'].append('First name is required')
        else:
            sanitized_first = self.sanitize_string(first_name, 50)
            
            # Check for valid name pattern (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized_first):
                result['is_valid'] = False
                result['issues'].append('First name contains invalid characters')
            elif len(sanitized_first) < 1:
                result['is_valid'] = False
                result['issues'].append('First name is too short')
            else:
                result['sanitized']['first_name'] = sanitized_first.title()
        
        # Validate last name
        if not last_name or not isinstance(last_name, str):
            result['is_valid'] = False
            result['issues'].append('Last name is required')
        else:
            sanitized_last = self.sanitize_string(last_name, 50)
            
            if not re.match(r"^[a-zA-Z\s\-'\.]+$", sanitized_last):
                result['is_valid'] = False
                result['issues'].append('Last name contains invalid characters')
            elif len(sanitized_last) < 1:
                result['is_valid'] = False
                result['issues'].append('Last name is too short')
            else:
                result['sanitized']['last_name'] = sanitized_last.title()
        
        return result
    
    def validate_phone(self, phone: str, region: str = 'US') -> Dict[str, Any]:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            region: Default region for parsing
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': False,
            'formatted': '',
            'issues': []
        }
        
        if not phone or not isinstance(phone, str):
            result['issues'].append('Phone number is required')
            return result
        
        # Sanitize input
        phone = self.sanitize_string(phone, 20)
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone, region)
            
            # Validate
            if phonenumbers.is_valid_number(parsed):
                result['is_valid'] = True
                result['formatted'] = phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.E164
                )
            else:
                result['issues'].append('Invalid phone number format')
                
        except phonenumbers.NumberParseException as e:
            if e.error_type == phonenumbers.NumberParseException.INVALID_COUNTRY_CODE:
                result['issues'].append('Invalid country code')
            elif e.error_type == phonenumbers.NumberParseException.NOT_A_NUMBER:
                result['issues'].append('Not a valid phone number')
            elif e.error_type == phonenumbers.NumberParseException.TOO_SHORT_NSN:
                result['issues'].append('Phone number is too short')
            elif e.error_type == phonenumbers.NumberParseException.TOO_LONG:
                result['issues'].append('Phone number is too long')
            else:
                result['issues'].append('Invalid phone number format')
        
        return result
    
    def validate_text_field(self, text: str, field_name: str, min_length: int = 0, max_length: int = 255, allow_html: bool = False) -> Dict[str, Any]:
        """
        Validate general text field
        
        Args:
            text: Text to validate
            field_name: Name of the field for error messages
            min_length: Minimum required length
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML content
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'sanitized': '',
            'issues': []
        }
        
        if not text or not isinstance(text, str):
            if min_length > 0:
                result['is_valid'] = False
                result['issues'].append(f'{field_name} is required')
            return result
        
        # Sanitize
        if allow_html:
            sanitized = self.sanitize_html(text)
        else:
            sanitized = self.sanitize_string(text, max_length)
        
        # Check length
        if len(sanitized) < min_length:
            result['is_valid'] = False
            result['issues'].append(f'{field_name} must be at least {min_length} characters')
        
        if len(sanitized) > max_length:
            result['is_valid'] = False
            result['issues'].append(f'{field_name} must be no more than {max_length} characters')
        
        # Check for SQL injection
        if self.check_sql_injection(sanitized):
            result['is_valid'] = False
            result['issues'].append(f'{field_name} contains invalid characters')
        
        result['sanitized'] = sanitized
        return result
    
    def validate_json_field(self, json_str: str, field_name: str) -> Dict[str, Any]:
        """
        Validate JSON field
        
        Args:
            json_str: JSON string to validate
            field_name: Name of the field for error messages
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'parsed': None,
            'issues': []
        }
        
        if not json_str:
            return result
        
        try:
            import json
            result['parsed'] = json.loads(json_str)
        except json.JSONDecodeError as e:
            result['is_valid'] = False
            result['issues'].append(f'{field_name} is not valid JSON: {str(e)}')
        except Exception as e:
            result['is_valid'] = False
            result['issues'].append(f'{field_name} validation error: {str(e)}')
        
        return result
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': False,
            'sanitized': '',
            'issues': []
        }
        
        if not url or not isinstance(url, str):
            result['issues'].append('URL is required')
            return result
        
        # Sanitize
        url = self.sanitize_string(url.strip(), 2048)
        
        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if url_pattern.match(url):
            result['is_valid'] = True
            result['sanitized'] = url
        else:
            result['issues'].append('Invalid URL format')
        
        return result
    
    def validate_integer(self, value: Any, field_name: str, min_value: int = None, max_value: int = None) -> Dict[str, Any]:
        """
        Validate integer field
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Dict with validation results
        """
        result = {
            'is_valid': True,
            'value': None,
            'issues': []
        }
        
        try:
            if isinstance(value, str):
                value = int(value)
            elif not isinstance(value, int):
                raise ValueError("Not an integer")
            
            if min_value is not None and value < min_value:
                result['is_valid'] = False
                result['issues'].append(f'{field_name} must be at least {min_value}')
            
            if max_value is not None and value > max_value:
                result['is_valid'] = False
                result['issues'].append(f'{field_name} must be no more than {max_value}')
            
            result['value'] = value
            
        except (ValueError, TypeError):
            result['is_valid'] = False
            result['issues'].append(f'{field_name} must be a valid integer')
        
        return result

