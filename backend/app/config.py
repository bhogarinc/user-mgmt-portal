"""
Application configuration management using Pydantic Settings.

This module provides centralized configuration management with
environment variable support and validation.
"""

from typing import List, Optional
from functools import lru_cache
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All sensitive values should be provided via environment variables
    or .env file. Default values are provided for non-sensitive settings.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="User Management Portal", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(alias="SECRET_KEY")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    
    # Database Settings
    database_url: str = Field(alias="DATABASE_URL")
    database_url_sync: str = Field(alias="DATABASE_URL_SYNC")
    
    # JWT Settings
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # Email Settings
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(alias="SMTP_USER")
    smtp_password: str = Field(alias="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, alias="SMTP_TLS")
    email_from: str = Field(alias="EMAIL_FROM")
    email_from_name: str = Field(default="User Management Portal", alias="EMAIL_FROM_NAME")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    
    # File Upload Settings
    max_upload_size: int = Field(default=5_242_880, alias="MAX_UPLOAD_SIZE")  # 5MB
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    allowed_image_types: str = Field(
        default="image/jpeg,image/png,image/webp", alias="ALLOWED_IMAGE_TYPES"
    )
    
    # Pagination Settings
    default_page_size: int = Field(default=20, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, alias="MAX_PAGE_SIZE")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, alias="RATE_LIMIT_WINDOW")
    
    # CORS Settings
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    
    @validator("cors_origins")
    def parse_cors_origins(cls, v: str) -> str:
        """Validate CORS origins format."""
        if not v:
            return "http://localhost:3000"
        return v
    
    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_allowed_image_types_list(self) -> List[str]:
        """Parse allowed image types into list."""
        return [t.strip() for t in self.allowed_image_types.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures settings are loaded only once
    and reused across the application.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()
