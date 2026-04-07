"""
Authentication Schemas

Pydantic models for authentication-related request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload."""
    
    sub: str  # User ID
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    type: str  # Token type: access or refresh


class UserCreate(BaseModel):
    """Schema for user registration."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    
    
class UserResponse(BaseModel):
    """Schema for user response after registration/login."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordChange(BaseModel):
    """Schema for changing password while logged in."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class VerifyEmail(BaseModel):
    """Schema for email verification."""
    
    token: str
