"""
Unit tests for authentication functionality.
Tests user creation, password hashing, and authentication logic.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.core.auth import (
    get_password_hash,
    verify_password,
    authenticate_user,
    create_access_token,
    initialize_default_users,
    USERS_DB
)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "test123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "test123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test failed password verification."""
        password = "test123"
        wrong_password = "wrong123"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestUserAuthentication:
    """Test user authentication logic."""
    
    def setup_method(self):
        """Setup test data before each test."""
        # Clear and reinitialize users for each test
        USERS_DB.clear()
        initialize_default_users()
    
    def test_authenticate_user_success_admin(self):
        """Test successful authentication for admin user."""
        user = authenticate_user("admin", "admin123")
        
        assert user is not None
        assert user.username == "admin"
        assert user.email == "admin@example.com"
        assert user.full_name == "Administrator"
        assert user.role == "admin"
        assert user.is_active is True
    
    def test_authenticate_user_success_user(self):
        """Test successful authentication for regular user."""
        user = authenticate_user("user", "user123")
        
        assert user is not None
        assert user.username == "user"
        assert user.email == "user@example.com"
        assert user.full_name == "Regular User"
        assert user.role == "user"
        assert user.is_active is True
    
    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        user = authenticate_user("admin", "wrongpassword")
        assert user is None
    
    def test_authenticate_user_nonexistent_user(self):
        """Test authentication with non-existent user."""
        user = authenticate_user("nonexistent", "password")
        assert user is None
    
    def test_authenticate_user_inactive_user(self):
        """Test authentication with inactive user."""
        # Create an inactive user
        USERS_DB["inactive_user"] = {
            "username": "inactive_user",
            "email": "inactive@example.com",
            "full_name": "Inactive User",
            "hashed_password": get_password_hash("password123"),
            "is_active": False,
            "role": "user"
        }
        
        user = authenticate_user("inactive_user", "password123")
        assert user is None


class TestTokenCreation:
    """Test JWT token creation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(data={"sub": "testuser"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiration(self):
        """Test access token creation with custom expiration."""
        from datetime import timedelta
        token = create_access_token(data={"sub": "testuser"}, expires_delta=timedelta(seconds=3600))
        
        assert token is not None
        assert isinstance(token, str)


class TestDefaultUserInitialization:
    """Test default user initialization."""
    
    def test_initialize_default_users(self):
        """Test that default users are properly initialized."""
        USERS_DB.clear()
        initialize_default_users()
        
        # Check that both default users exist
        assert "admin" in USERS_DB
        assert "user" in USERS_DB
        
        # Check admin user details
        admin = USERS_DB["admin"]
        assert admin["username"] == "admin"
        assert admin["email"] == "admin@example.com"
        assert admin["full_name"] == "Administrator"
        assert admin["role"] == "admin"
        assert admin["is_active"] is True
        assert "hashed_password" in admin
        
        # Check user details
        user = USERS_DB["user"]
        assert user["username"] == "user"
        assert user["email"] == "user@example.com"
        assert user["full_name"] == "Regular User"
        assert user["role"] == "user"
        assert user["is_active"] is True
        assert "hashed_password" in user
    
    def test_default_users_can_authenticate(self):
        """Test that default users can authenticate with correct passwords."""
        USERS_DB.clear()
        initialize_default_users()
        
        # Test admin authentication
        admin_user = authenticate_user("admin", "admin123")
        assert admin_user is not None
        assert admin_user.username == "admin"
        
        # Test user authentication
        regular_user = authenticate_user("user", "user123")
        assert regular_user is not None
        assert regular_user.username == "user"
    
    def test_default_users_cannot_authenticate_with_wrong_passwords(self):
        """Test that default users cannot authenticate with wrong passwords."""
        USERS_DB.clear()
        initialize_default_users()
        
        # Test admin with wrong password
        admin_user = authenticate_user("admin", "wrongpassword")
        assert admin_user is None
        
        # Test user with wrong password
        regular_user = authenticate_user("user", "wrongpassword")
        assert regular_user is None


if __name__ == "__main__":
    pytest.main([__file__])
