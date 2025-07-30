"""
Core configuration settings for the Enterprise AI System.
Uses Pydantic settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional, Union
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================
    
    APP_NAME: str = "Enterprise AI System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    PORT: int = Field(default=8000, env="PORT")
    
    # ============================================================================
    # DATABASE SETTINGS
    # ============================================================================
    
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/enterprise_ai",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    
    # ============================================================================
    # SECURITY SETTINGS
    # ============================================================================
    
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-key-change-in-production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWERCASE")
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    
    # Session settings
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=15, env="ACCOUNT_LOCKOUT_MINUTES")
    
    # ============================================================================
    # CORS AND SECURITY HEADERS
    # ============================================================================
    
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "*"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*"],
        env="ALLOWED_HOSTS"
    )
    
    # ============================================================================
    # REDIS SETTINGS
    # ============================================================================
    
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=300, env="REDIS_CACHE_TTL")  # 5 minutes
    REDIS_SESSION_TTL: int = Field(default=1800, env="REDIS_SESSION_TTL")  # 30 minutes
    
    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # API specific rate limits
    API_RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="API_RATE_LIMIT_PER_MINUTE")
    LLM_RATE_LIMIT_PER_MINUTE: int = Field(default=20, env="LLM_RATE_LIMIT_PER_MINUTE")
    LLM_RATE_LIMIT_TOKENS_PER_HOUR: int = Field(default=100000, env="LLM_RATE_LIMIT_TOKENS_PER_HOUR")
    
    # ============================================================================
    # LLM SETTINGS
    # ============================================================================
    
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", env="OPENAI_API_BASE")
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_DEFAULT_MODEL")
    OPENAI_MAX_TOKENS: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # LLM request timeouts
    LLM_REQUEST_TIMEOUT: int = Field(default=60, env="LLM_REQUEST_TIMEOUT")
    LLM_MAX_RETRIES: int = Field(default=3, env="LLM_MAX_RETRIES")
    
    # ============================================================================
    # FILE STORAGE SETTINGS
    # ============================================================================
    
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(default=104857600, env="MAX_UPLOAD_SIZE")  # 100MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Cloud storage settings
    STORAGE_PROVIDER: str = Field(default="local", env="STORAGE_PROVIDER")  # local, s3, gcs, azure
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_S3_BUCKET: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    
    # ============================================================================
    # LOGGING SETTINGS
    # ============================================================================
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json, text
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # ============================================================================
    # MONITORING AND METRICS
    # ============================================================================
    
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    HEALTH_CHECK_TIMEOUT: int = Field(default=5, env="HEALTH_CHECK_TIMEOUT")
    
    # External service URLs for health checks
    EXTERNAL_SERVICES: List[str] = Field(default=[], env="EXTERNAL_SERVICES")
    
    # ============================================================================
    # AUDIT AND COMPLIANCE
    # ============================================================================
    
    AUDIT_ENABLED: bool = Field(default=True, env="AUDIT_ENABLED")
    AUDIT_LOG_REQUESTS: bool = Field(default=True, env="AUDIT_LOG_REQUESTS")
    AUDIT_LOG_RESPONSES: bool = Field(default=False, env="AUDIT_LOG_RESPONSES")
    AUDIT_RETENTION_DAYS: int = Field(default=2555, env="AUDIT_RETENTION_DAYS")  # 7 years
    
    # Data masking
    DATA_MASKING_ENABLED: bool = Field(default=True, env="DATA_MASKING_ENABLED")
    PII_DETECTION_ENABLED: bool = Field(default=True, env="PII_DETECTION_ENABLED")
    
    # ============================================================================
    # BACKGROUND TASKS
    # ============================================================================
    
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # ============================================================================
    # EMAIL SETTINGS
    # ============================================================================
    
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    
    FROM_EMAIL: str = Field(default="noreply@enterprise.ai", env="FROM_EMAIL")
    FROM_NAME: str = Field(default="Enterprise AI System", env="FROM_NAME")
    
    # ============================================================================
    # VALIDATORS
    # ============================================================================
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def parse_file_types(cls, v):
        """Parse allowed file types from string or list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    @validator("EXTERNAL_SERVICES", pre=True)
    def parse_external_services(cls, v):
        """Parse external services from string or list."""
        if isinstance(v, str):
            return [service.strip() for service in v.split(",") if service.strip()]
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed_envs}")
        return v
    
    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT == "testing"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL."""
        if "postgresql+asyncpg://" in self.DATABASE_URL:
            return self.DATABASE_URL
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Ensure upload directory exists
upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(exist_ok=True)

