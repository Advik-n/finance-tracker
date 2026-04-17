"""
Authentication Service

Handles user authentication, registration, and account management.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import load_only
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_token_type,
)
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    LoginResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
    UserPreferences,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication operations.

    Handles user CRUD, authentication, and account management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email address

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .options(
                load_only(
                    User.id,
                    User.email,
                    User.password_hash,
                    User.full_name,
                    User.phone,
                    User.avatar_url,
                    User.is_active,
                    User.is_verified,
                    User.is_superuser,
                    User.failed_login_attempts,
                    User.locked_until,
                    User.password_changed_at,
                    User.created_at,
                    User.updated_at,
                    User.last_login,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def register(self, data: UserRegisterRequest) -> User:
        """
        Register a new user.

        Args:
            data: Registration data

        Returns:
            Created User object

        Raises:
            ConflictError: If email already exists
        """
        # Check if email exists
        existing = await self.get_user_by_email(data.email)
        if existing:
            raise ConflictError(
                message="Email already registered",
                detail="An account with this email address already exists",
            )

        # Create user
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            is_active=True,
            is_verified=False,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(f"User registered: {user.email}")
        return user

    async def login(self, data: UserLoginRequest) -> LoginResponse:
        """
        Authenticate user and return tokens.

        Args:
            data: Login credentials

        Returns:
            Login response with user and tokens

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user
        user = await self.get_user_by_email(data.email)

        if not user:
            raise AuthenticationError(
                message="Invalid credentials",
                detail="Email or password is incorrect",
            )

        # Check if account is locked
        if user.is_locked:
            raise AuthenticationError(
                message="Account locked",
                detail=f"Account is locked. Please try again later.",
            )

        # Verify password
        if not verify_password(data.password, user.password_hash):
            # Increment failed attempts
            user.increment_failed_attempts()

            # Lock account if too many failures
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    seconds=settings.lockout_duration_seconds
                )
                logger.warning(f"Account locked due to failed attempts: {user.email}")

            await self.db.flush()

            raise AuthenticationError(
                message="Invalid credentials",
                detail="Email or password is incorrect",
            )

        # Check if account is active
        if not user.is_active:
            raise AuthenticationError(
                message="Account disabled",
                detail="Your account has been disabled. Please contact support.",
            )

        # Reset failed attempts and update last login
        user.reset_failed_attempts()
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)  # Reload user attributes after flush

        # Generate tokens
        tokens = self._generate_tokens(user, extended=data.remember_me)

        logger.info(f"User logged in: {user.email}")

        return LoginResponse(
            user=self._to_user_response(user),
            tokens=tokens,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New token pair

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        payload = decode_token(refresh_token)

        if not payload:
            raise AuthenticationError(
                message="Invalid token",
                detail="Refresh token is invalid or expired",
            )

        if not verify_token_type(payload, "refresh"):
            raise AuthenticationError(
                message="Invalid token type",
                detail="Expected refresh token",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError(
                message="Invalid token payload",
                detail="User ID not found in token",
            )

        # Verify user exists and is active
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise AuthenticationError(
                message="Invalid user ID",
                detail="User ID in token is not valid",
            )

        user = await self.get_user_by_id(user_uuid)

        if not user or not user.is_active:
            raise AuthenticationError(
                message="User not found",
                detail="User associated with this token no longer exists or is inactive",
            )

        # Generate new tokens
        return self._generate_tokens(user)

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """
        Change user password.

        Args:
            user: Current user
            data: Password change data

        Raises:
            ValidationError: If current password is incorrect
        """
        # Verify current password
        if not verify_password(data.current_password, user.password_hash):
            raise ValidationError(
                message="Invalid password",
                errors=[{"field": "current_password", "message": "Current password is incorrect"}],
            )

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"Password changed for user: {user.email}")

    async def logout(self, token: str) -> None:
        """
        Logout user by blacklisting token.
        In production, this would add the token to a Redis blacklist.

        Args:
            token: Access token to invalidate
        """
        # In production, add token to Redis blacklist with TTL
        logger.info("User logged out (token invalidation placeholder)")

    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdateRequest
    ) -> Optional[User]:
        """
        Update user profile.

        Args:
            user_id: User UUID
            data: Fields to update

        Returns:
            Updated User object
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user_id: UUID) -> bool:
        """
        Deactivate user account (soft delete).

        Args:
            user_id: User UUID

        Returns:
            True if successful
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.flush()
        return True

    # ====================
    # Private Methods
    # ====================

    def _generate_tokens(self, user: User, extended: bool = False) -> TokenResponse:
        """Generate access and refresh tokens for user."""
        token_data = {"sub": str(user.id), "email": user.email}

        access_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        refresh_expires = timedelta(days=settings.jwt_refresh_token_expire_days)

        if extended:
            refresh_expires = timedelta(days=30)  # Extended session

        access_token = create_access_token(token_data, access_expires)
        refresh_token = create_refresh_token(token_data, refresh_expires)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_expires.total_seconds()),
        )

    def _to_user_response(self, user: User) -> UserResponse:
        """Convert User model to response schema."""
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
