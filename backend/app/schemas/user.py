"""
User Pydantic schemas for request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import BaseSchema, TimestampMixin


# ====================
# Request Schemas
# ====================


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
    )
    confirm_password: str = Field(..., description="Password confirmation")
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name",
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Phone number (optional)",
    )

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Extended session")


class ChangePasswordRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password",
    )
    confirm_new_password: str = Field(..., description="Confirm new password")

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


# ====================
# Response Schemas
# ====================


class UserResponse(BaseSchema, TimestampMixin):
    """Schema for user response (public info)."""

    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    last_login: datetime | None = None


class UserProfileResponse(UserResponse):
    """Extended user profile response."""

    transactions_count: int = 0
    budgets_count: int = 0
    categories_count: int = 0


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")


class LoginResponse(BaseModel):
    """Schema for login response."""

    user: UserResponse
    tokens: TokenResponse


class AuthResponse(BaseModel):
    """Generic authentication response."""

    message: str
    success: bool = True


class UserPreferences(BaseModel):
    """Schema for user preferences."""

    currency: str = Field(default="INR", max_length=3)
    language: str = Field(default="en", max_length=10)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    date_format: str = Field(default="DD/MM/YYYY", max_length=20)
    theme: str = Field(default="light", pattern="^(light|dark|system)$")
    notifications_enabled: bool = True
    email_reports: bool = True
    weekly_summary: bool = True
