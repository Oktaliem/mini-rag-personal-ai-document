"""
API tests for authentication endpoints.
Tests login, logout, and token validation endpoints.
"""
import pytest
import json
from fastapi.testclient import TestClient
from src.main import app


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def setup_method(self):
        """Setup test data before each test."""
        # Clear any existing blacklist for each test
        from src.core.auth import BLACKLISTED_TOKENS
        BLACKLISTED_TOKENS.clear()
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_login_success_admin(self, client):
        """Test successful login for admin user."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800  # 30 minutes
        assert len(data["access_token"]) > 0
    
    def test_login_success_user(self, client):
        """Test successful login for regular user."""
        response = client.post(
            "/auth/login",
            json={"username": "user", "password": "user123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert len(data["access_token"]) > 0
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_login_missing_username(self, client):
        """Test login with missing username."""
        response = client.post(
            "/auth/login",
            json={"password": "admin123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_missing_password(self, client):
        """Test login with missing password."""
        response = client.post(
            "/auth/login",
            json={"username": "admin"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_empty_credentials(self, client):
        """Test login with empty credentials."""
        response = client.post(
            "/auth/login",
            json={"username": "", "password": ""}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_login_invalid_json(self, client):
        """Test login with invalid JSON."""
        response = client.post(
            "/auth/login",
            data="invalid json"
        )
        
        assert response.status_code == 422
    
    def test_get_current_user_success(self, client):
        """Test getting current user with valid token."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Use token to get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["email"] == "admin@example.com"
        assert data["full_name"] == "Administrator"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "hashed_password" not in data  # Password should not be returned
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_missing_token(self, client):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_wrong_token_format(self, client):
        """Test getting current user with wrong token format."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Basic invalid_token"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_logout_success(self, client):
        """Test successful logout."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]
    
    def test_logout_invalid_token(self, client):
        """Test logout with invalid token."""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # The legacy logout endpoint doesn't require authentication
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]
    
    def test_logout_missing_token(self, client):
        """Test logout without token."""
        response = client.post("/auth/logout")
        
        # The legacy logout endpoint doesn't require authentication
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Logged out successfully" in data["message"]
    
    def test_token_expiration_handling(self, client):
        """Test that expired tokens are properly handled."""
        # This test would require mocking time or using a very short expiration
        # For now, we'll test that the endpoint exists and returns proper format
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert login_response.status_code == 200
        token_data = login_response.json()
        assert "expires_in" in token_data
        assert token_data["expires_in"] == 1800  # 30 minutes
    
    def test_multiple_user_sessions(self, client):
        """Test that multiple users can login simultaneously."""
        # Login as admin
        admin_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert admin_response.status_code == 200
        admin_token = admin_response.json()["access_token"]
        
        # Login as user
        user_response = client.post(
            "/auth/login",
            json={"username": "user", "password": "user123"}
        )
        assert user_response.status_code == 200
        user_token = user_response.json()["access_token"]
        
        # Verify both tokens are different
        assert admin_token != user_token
        
        # Verify both users can access their own data
        admin_me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert admin_me.status_code == 200
        assert admin_me.json()["username"] == "admin"
        
        user_me = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert user_me.status_code == 200
        assert user_me.json()["username"] == "user"


if __name__ == "__main__":
    pytest.main([__file__])
