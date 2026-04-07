"""
Security Configuration for Finance Tracker

Centralized security configuration with environment-aware defaults.
"""

import os
import secrets
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Environment(Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SecurityConfig:
    """Centralized security configuration.
    
    All security-related settings in one place for easy auditing.
    """
    
    # Environment
    environment: Environment = Environment.DEVELOPMENT
    
    # JWT Configuration
    jwt_secret_key: str = field(default_factory=lambda: os.getenv(
        "JWT_SECRET_KEY", 
        secrets.token_hex(32) if os.getenv("ENVIRONMENT") == "development" else ""
    ))
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    
    # Password Configuration
    password_bcrypt_rounds: int = 12
    password_min_length: int = 8
    password_max_failed_attempts: int = 5
    password_lockout_minutes: int = 30
    
    # Encryption Configuration
    encryption_master_key: str = field(default_factory=lambda: os.getenv(
        "ENCRYPTION_MASTER_KEY",
        secrets.token_hex(32) if os.getenv("ENVIRONMENT") == "development" else ""
    ))
    
    # Session Configuration
    session_timeout_minutes: int = 30
    session_absolute_timeout_hours: int = 24
    session_max_concurrent: int = 3
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_auth_per_minute: int = 5
    rate_limit_api_per_minute: int = 100
    
    # CORS Configuration
    cors_allowed_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5173",
    ] if os.getenv("ENVIRONMENT") == "development" else [])
    cors_allow_credentials: bool = True
    
    # Security Headers
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    csp_report_uri: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"
    ))
    
    # Audit Logging
    audit_log_enabled: bool = True
    audit_log_path: str = "/var/log/finance-tracker/audit"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate security configuration.
        
        Raises:
            ValueError: If configuration is insecure for production
        """
        if self.environment == Environment.PRODUCTION:
            # Require secure keys in production
            if not self.jwt_secret_key or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "JWT_SECRET_KEY must be set and at least 32 bytes in production"
                )
            
            if not self.encryption_master_key or len(self.encryption_master_key) < 32:
                raise ValueError(
                    "ENCRYPTION_MASTER_KEY must be set and at least 32 bytes in production"
                )
            
            # Require explicit CORS origins
            if not self.cors_allowed_origins:
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS must be explicitly set in production"
                )
            
            # Check for localhost in production
            for origin in self.cors_allowed_origins:
                if "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError(
                        f"Localhost origin not allowed in production: {origin}"
                    )
    
    @classmethod
    def from_environment(cls) -> "SecurityConfig":
        """Create configuration from environment variables.
        
        Returns:
            SecurityConfig instance
        """
        env = os.getenv("ENVIRONMENT", "development").lower()
        environment = Environment(env) if env in [e.value for e in Environment] else Environment.DEVELOPMENT
        
        return cls(
            environment=environment,
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
            jwt_refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            password_bcrypt_rounds=int(os.getenv("PASSWORD_BCRYPT_ROUNDS", "12")),
            password_max_failed_attempts=int(os.getenv("PASSWORD_MAX_FAILED_ATTEMPTS", "5")),
            password_lockout_minutes=int(os.getenv("PASSWORD_LOCKOUT_MINUTES", "30")),
            encryption_master_key=os.getenv("ENCRYPTION_MASTER_KEY", ""),
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "30")),
            session_max_concurrent=int(os.getenv("SESSION_MAX_CONCURRENT", "3")),
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            cors_allowed_origins=os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("CORS_ALLOWED_ORIGINS") else [],
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            audit_log_enabled=os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true",
        )


# Development configuration
DEVELOPMENT_CONFIG = SecurityConfig(
    environment=Environment.DEVELOPMENT,
    jwt_secret_key="dev-secret-key-do-not-use-in-production-32bytes!",
    encryption_master_key="dev-encryption-key-do-not-use-prod-32b!",
    cors_allowed_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ],
)

# Staging configuration
STAGING_CONFIG = SecurityConfig(
    environment=Environment.STAGING,
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
    encryption_master_key=os.getenv("ENCRYPTION_MASTER_KEY", ""),
    cors_allowed_origins=[
        "https://staging.financetracker.example.com",
    ],
    password_bcrypt_rounds=12,
    session_timeout_minutes=30,
)


def get_production_config() -> SecurityConfig:
    """Get production configuration from environment.
    
    Returns:
        SecurityConfig for production
        
    Raises:
        ValueError: If required environment variables are missing
    """
    return SecurityConfig.from_environment()


def get_config() -> SecurityConfig:
    """Get configuration based on current environment.
    
    Returns:
        Appropriate SecurityConfig instance
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return get_production_config()
    elif env == "staging":
        return STAGING_CONFIG
    else:
        return DEVELOPMENT_CONFIG
