"""
Authentication endpoints for the Enterprise AI System.
Handles login, registration, token refresh, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
import structlog

from app.core.exceptions import AuthenticationException, ValidationException
from app.middleware.auth import get_current_user, get_current_user_id
from app.services.auth import AuthService
from app.services.user import UserService

logger = structlog.get_logger(__name__)
security = HTTPBearer()

router = APIRouter()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    username: Optional[str] = None

class RegisterResponse(BaseModel):
    message: str
    user_id: str
    email: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(),
    user_service: UserService = Depends()
):
    """Authenticate user and return access tokens."""
    try:
        # Get client information
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        # Authenticate user
        auth_result = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=client_ip,
            user_agent=user_agent,
            remember_me=request.remember_me
        )
        
        if not auth_result:
            raise AuthenticationException("Invalid email or password")
        
        # Get user information
        user = await user_service.get_user_by_id(auth_result["user_id"])
        if not user:
            raise AuthenticationException("User not found")
        
        return LoginResponse(
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"],
            expires_in=auth_result["expires_in"],
            user={
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            }
        )
        
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e), email=request.email)
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    http_request: Request,
    auth_service: AuthService = Depends(),
    user_service: UserService = Depends()
):
    """Register new user account."""
    try:
        # Get client information
        client_ip = http_request.client.host if http_request.client else "unknown"
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        # Register user
        user_id = await auth_service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return RegisterResponse(
            message="User registered successfully. Please check your email for verification.",
            user_id=str(user_id),
            email=request.email
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error("Registration failed", error=str(e), email=request.email)
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends()
):
    """Refresh access token using refresh token."""
    try:
        result = await auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            access_token=result["access_token"],
            expires_in=result["expires_in"]
        )
        
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends()
):
    """Logout user and invalidate tokens."""
    try:
        await auth_service.logout_user(current_user_id)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout failed", error=str(e), user_id=current_user_id)
        raise HTTPException(status_code=500, detail="Logout failed")

# ============================================================================
# PASSWORD MANAGEMENT
# ============================================================================

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends()
):
    """Change user password."""
    try:
        await auth_service.change_password(
            user_id=current_user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return {"message": "Password changed successfully"}
        
    except AuthenticationException:
        raise
    except ValidationException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user_id)
        raise HTTPException(status_code=500, detail="Password change failed")

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    http_request: Request,
    auth_service: AuthService = Depends()
):
    """Request password reset."""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        await auth_service.request_password_reset(
            email=request.email,
            ip_address=client_ip
        )
        
        return {"message": "Password reset instructions sent to your email"}
        
    except Exception as e:
        logger.error("Password reset request failed", error=str(e), email=request.email)
        # Don't reveal if email exists
        return {"message": "Password reset instructions sent to your email"}

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    http_request: Request,
    auth_service: AuthService = Depends()
):
    """Reset password using reset token."""
    try:
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        await auth_service.reset_password(
            token=request.token,
            new_password=request.new_password,
            ip_address=client_ip
        )
        
        return {"message": "Password reset successfully"}
        
    except AuthenticationException:
        raise
    except ValidationException:
        raise
    except Exception as e:
        logger.error("Password reset failed", error=str(e))
        raise HTTPException(status_code=500, detail="Password reset failed")

# ============================================================================
# EMAIL VERIFICATION
# ============================================================================

@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    auth_service: AuthService = Depends()
):
    """Verify email address using verification token."""
    try:
        await auth_service.verify_email(request.token)
        
        return {"message": "Email verified successfully"}
        
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Email verification failed")

@router.post("/resend-verification")
async def resend_verification(
    current_user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends()
):
    """Resend email verification."""
    try:
        await auth_service.resend_verification_email(current_user_id)
        
        return {"message": "Verification email sent"}
        
    except Exception as e:
        logger.error("Resend verification failed", error=str(e), user_id=current_user_id)
        raise HTTPException(status_code=500, detail="Failed to send verification email")

# ============================================================================
# USER INFO
# ============================================================================

@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_user),
    user_service: UserService = Depends()
):
    """Get current user information."""
    try:
        # Get detailed user information with roles and permissions
        user_details = await user_service.get_user_with_permissions(current_user.id)
        
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat(),
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "roles": user_details.get("roles", []),
            "permissions": user_details.get("permissions", [])
        }
        
    except Exception as e:
        logger.error("Get current user failed", error=str(e), user_id=str(current_user.id))
        raise HTTPException(status_code=500, detail="Failed to get user information")

