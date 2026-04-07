"""
User Management Endpoints

Handles user profile operations, preferences, and account management.
"""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID

from app.api.deps import DbSession, CurrentUser, SuperUser
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserPreferences,
    UserList,
)
from app.services.auth_service import AuthService


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    """
    Get current user's profile.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        UserResponse: User profile information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Update current user's profile.
    
    Args:
        user_data: Fields to update
        db: Database session
        current_user: Authenticated user
        
    Returns:
        UserResponse: Updated user profile
    """
    auth_service = AuthService(db)
    updated_user = await auth_service.update_user(
        user_id=current_user.id,
        data=user_data,
    )
    return updated_user


@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Get current user's preferences.
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        UserPreferences: User preference settings
    """
    auth_service = AuthService(db)
    return await auth_service.get_preferences(user_id=current_user.id)


@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences: UserPreferences,
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Update current user's preferences.
    
    Args:
        preferences: Preference settings to update
        db: Database session
        current_user: Authenticated user
        
    Returns:
        UserPreferences: Updated preferences
    """
    auth_service = AuthService(db)
    return await auth_service.update_preferences(
        user_id=current_user.id,
        preferences=preferences,
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    db: DbSession,
    current_user: CurrentUser,
):
    """
    Delete current user's account.
    
    This is a soft delete - account data is retained for 30 days
    before permanent deletion.
    
    Args:
        db: Database session
        current_user: Authenticated user
    """
    auth_service = AuthService(db)
    await auth_service.deactivate_user(user_id=current_user.id)


# Admin endpoints

@router.get("", response_model=UserList)
async def list_users(
    db: DbSession,
    current_user: SuperUser,
    page: int = 1,
    limit: int = 50,
):
    """
    List all users (admin only).
    
    Args:
        db: Database session
        current_user: Authenticated superuser
        page: Page number
        limit: Items per page
        
    Returns:
        UserList: Paginated list of users
    """
    auth_service = AuthService(db)
    return await auth_service.list_users(page=page, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: DbSession,
    current_user: SuperUser,
):
    """
    Get a specific user (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Authenticated superuser
        
    Returns:
        UserResponse: User profile
        
    Raises:
        HTTPException: 404 if user not found
    """
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DbSession,
    current_user: SuperUser,
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: User UUID
        db: Database session
        current_user: Authenticated superuser
        
    Raises:
        HTTPException: 404 if user not found
    """
    auth_service = AuthService(db)
    deleted = await auth_service.delete_user(user_id=user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
