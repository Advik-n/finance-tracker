"""
Authentication Endpoints

Handles user registration, login, token refresh, and logout operations.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import ActiveUser, CurrentUser, DatabaseSession
from app.schemas.common import MessageResponse
from app.schemas.user import (
    ChangePasswordRequest,
    LoginResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
security = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
)
async def register(
    data: UserRegisterRequest,
    db: DatabaseSession,
) -> UserResponse:
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, mixed case, digit)
    - **full_name**: User's full name
    - **phone**: Optional phone number
    """
    auth_service = AuthService(db)
    user = await auth_service.register(data)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate with email and password to receive access tokens.",
)
async def login(
    data: UserLoginRequest,
    db: DatabaseSession,
) -> LoginResponse:
    """
    Authenticate user and return access/refresh tokens.

    - **email**: Registered email address
    - **password**: Account password
    - **remember_me**: Extended session (30 days refresh token)
    """
    auth_service = AuthService(db)
    return await auth_service.login(data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Exchange refresh token for new access/refresh token pair.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DatabaseSession,
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    - **refresh_token**: Valid refresh token from login
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_token(data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Invalidate current access token.",
)
async def logout(
    db: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> MessageResponse:
    """
    Logout current user by invalidating the access token.
    """
    if credentials:
        auth_service = AuthService(db)
        await auth_service.logout(credentials.credentials)

    return MessageResponse(message="Successfully logged out")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change the current user's password.",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> MessageResponse:
    """
    Change password for authenticated user.

    - **current_password**: Current account password
    - **new_password**: New password to set
    - **confirm_new_password**: Confirmation of new password
    """
    auth_service = AuthService(db)
    await auth_service.change_password(current_user, data)

    return MessageResponse(message="Password changed successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get profile information for the authenticated user.",
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Get the profile of the currently authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update profile",
    description="Update the authenticated user's profile information.",
)
async def update_profile(
    data: UserUpdateRequest,
    current_user: ActiveUser,
    db: DatabaseSession,
) -> UserResponse:
    """
    Update profile information for the current user.

    - **full_name**: New full name
    - **phone**: New phone number
    - **avatar_url**: New avatar URL
    """
    # Update user fields
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url

    await db.flush()
    await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
