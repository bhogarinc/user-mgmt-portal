"""
Application configuration management.

Uses Pydantic Settings for environment-based configuration with validation.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, PostgresDsn, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "User Management Portal"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", pattern=r"^(development|staging|production)$")
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32, description="Secret key for JWT signing")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    
    # Database
    DATABASE_URL: PostgresDsn = Field(..., description="PostgreSQL connection URL")
    DATABASE_POOL_SIZE: int = Field(default=10, ge=1, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=10, le=1000)
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    
    # Azure
    AZURE_APP_INSIGHTS_CONNECTION_STRING: Optional[str] = None
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse comma-separated allowed hosts."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently strong."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Uses lru_cache to avoid reloading settings on every call.
    
    Returns:
        Settings: Application settings instance
        
    Raises:
        ValidationError: If required environment variables are missing or invalid
    """
    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Configuration error: {e}") from e


# Export settings for easy import
settings = get_settings()
