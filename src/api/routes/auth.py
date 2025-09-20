"""
Authentication API routes.

This module contains all authentication-related API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ...core.config import settings

from ...core.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_current_active_user, get_current_admin_user,
    get_current_active_user_from_token, blacklist_token,
    create_user, get_user_by_username,
)
from ...core.models import User, UserCreate, UserLogin, Token
from ...api.dependencies import get_current_user_dependency

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin) -> dict:
    """Login endpoint."""
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/logout")
async def logout(token: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Logout endpoint."""
    blacklist_token(token.credentials)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_me(current_user: User = Depends(get_current_user_dependency)) -> User:
    """Get current user information."""
    return current_user


@router.post("/register", response_model=User)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """Register a new user (admin only)."""
    try:
        new_user = create_user(user_data)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/users/{username}", response_model=User)
async def get_user(
    username: str,
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """Get user by username (admin only)."""
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{username}", response_model=User)
async def update_user(
    username: str,
    user_data: dict,
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """Update user (admin only)."""
    from ...core.auth import update_user as update_user_func
    
    updated_user = update_user_func(username, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.delete("/users/{username}")
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_admin_user)
) -> dict:
    """Delete user (admin only)."""
    from ...core.auth import delete_user as delete_user_func
    
    if delete_user_func(username):
        return {"message": f"User {username} deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
