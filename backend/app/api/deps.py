"""
API Dependencies Module

Provides reusable dependencies for authentication, authorization,
database sessions, and other common request requirements.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token, verify_token_type
from app.database import AsyncSessionLocal, get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncSession:
    """
    Get database session dependency.
    This is the primary database dependency to use in routes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for database dependency
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    db: DatabaseSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        db: Database session
        credentials: HTTP Bearer credentials

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise credentials_exception

    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUser,
) -> User:
    """
    Get the current active user.
    Ensures the user account is active and not locked.

    Args:
        current_user: Current authenticated user

    Returns:
        Active User object

    Raises:
        HTTPException: If user is inactive or locked
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    if current_user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked",
        )

    return current_user


# Type alias for active user dependency
ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_verified_user(
    current_user: ActiveUser,
) -> User:
    """
    Get the current verified user.
    Ensures the user has verified their email.

    Args:
        current_user: Current active user

    Returns:
        Verified User object

    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )

    return current_user


# Type alias for verified user dependency
VerifiedUser = Annotated[User, Depends(get_current_verified_user)]


async def get_current_superuser(
    current_user: ActiveUser,
) -> User:
    """
    Get the current superuser.
    For admin-only endpoints.

    Args:
        current_user: Current active user

    Returns:
        Superuser object

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# Type aliases for cleaner dependency injection
DbSession = DatabaseSession
SuperUser = Annotated[User, Depends(get_current_superuser)]
