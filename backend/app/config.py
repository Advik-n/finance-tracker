"""
Application Configuration using Pydantic Settings.
Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Finance Tracker"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finance_tracker",
        description="PostgreSQL database URL with asyncpg driver",
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=1)
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="your-super-secret-key-change-in-production",
        min_length=32,
        description="Secret key for JWT encoding/decoding",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1)

    # Security
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    bcrypt_rounds: int = 12

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # File Upload
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    allowed_upload_extensions: list[str] = [".pdf", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"]
    upload_dir: str = "uploads"

    # Encryption
    encryption_key: str = Field(
        default="your-32-byte-encryption-key-here!",
        min_length=32,
        description="Fernet encryption key for sensitive data",
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Feature Flags
    enable_ai_insights: bool = True
    enable_pdf_parsing: bool = True
    enable_ocr: bool = True

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def lockout_duration_seconds(self) -> int:
        """Get lockout duration in seconds."""
        return self.lockout_duration_minutes * 60


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache for singleton pattern.
    """
    return Settings()


settings = get_settings()
