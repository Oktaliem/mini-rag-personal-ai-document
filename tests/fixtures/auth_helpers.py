"""
Authentication helpers for testing.

This module provides utilities for testing authentication-related functionality.
"""

from unittest.mock import Mock, patch
from typing import Dict, Any, Optional
import jwt
from datetime import datetime, timedelta


def create_test_token(username: str = "testuser", 
                     role: str = "user",
                     secret_key: str = "test-secret-key",
                     expires_delta: Optional[timedelta] = None) -> str:
    """Create a test JWT token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def create_expired_token(username: str = "testuser",
                        role: str = "user", 
                        secret_key: str = "test-secret-key") -> str:
    """Create an expired JWT token."""
    expire = datetime.utcnow() - timedelta(minutes=30)  # Expired 30 minutes ago
    
    to_encode = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow() - timedelta(hours=1)
    }
    
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def create_invalid_token() -> str:
    """Create an invalid JWT token."""
    return "invalid.token.here"


def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers for a token."""
    return {"Authorization": f"Bearer {token}"}


def mock_authenticated_user(username: str = "testuser",
                           role: str = "user",
                           is_active: bool = True):
    """Mock an authenticated user for testing."""
    return Mock(
        username=username,
        role=role,
        is_active=is_active,
        email=f"{username}@example.com",
        full_name=f"{username.title()} User"
    )


def mock_current_user_dependency(user=None):
    """Mock the get_current_user dependency."""
    if user is None:
        user = mock_authenticated_user()
    
    def mock_dependency():
        return user
    
    return mock_dependency


def mock_admin_user_dependency():
    """Mock the get_current_admin_user dependency."""
    admin_user = mock_authenticated_user(username="admin", role="admin")
    return mock_current_user_dependency(admin_user)


def mock_unauthorized_user():
    """Mock an unauthorized user (raises HTTPException)."""
    from fastapi import HTTPException, status
    
    def mock_dependency():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return mock_dependency


def mock_forbidden_user():
    """Mock a forbidden user (raises HTTPException)."""
    from fastapi import HTTPException, status
    
    def mock_dependency():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return mock_dependency


class MockPasswordHasher:
    """Mock password hasher for testing."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Mock password hashing."""
        return f"hashed_{password}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Mock password verification."""
        return hashed == f"hashed_{password}"


def create_test_user_data(username: str = "testuser",
                         password: str = "testpassword",
                         role: str = "user") -> Dict[str, Any]:
    """Create test user data."""
    return {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": f"{username.title()} User",
        "role": role
    }


def create_test_login_data(username: str = "testuser",
                          password: str = "testpassword") -> Dict[str, str]:
    """Create test login data."""
    return {
        "username": username,
        "password": password
    }
