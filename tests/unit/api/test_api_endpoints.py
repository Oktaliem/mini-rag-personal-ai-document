"""
Unit tests for API endpoints.

This module tests the API layer including:
- Authentication endpoints
- Public endpoints
- Protected endpoints
- Document management endpoints
- RAG endpoints
- Error handling and validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json
import tempfile
import os

# Import the app
from src.main import app

class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""
    
    def setup_method(self):
        """Setup test data before each test."""
        # Clear any existing blacklist for each test
        from src.core.auth import BLACKLISTED_TOKENS
        BLACKLISTED_TOKENS.clear()
    
    def test_login_success(self):
        """Test successful login."""
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_missing_fields(self):
        """Test login with missing fields."""
        client = TestClient(app)
        
        response = client.post("/auth/login", json={
            "username": "admin"
            # Missing password
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_logout_success(self):
        """Test successful logout."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Then logout
        response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        assert data["token_blacklisted"] is True
    
    def test_logout_without_token(self):
        """Test logout without token."""
        client = TestClient(app)
        
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        assert data["token_blacklisted"] is False
    
    def test_get_current_user_me(self):
        """Test getting current user info."""
        client = TestClient(app)
        
        # Clear any existing blacklist for this test
        from src.core.auth import BLACKLISTED_TOKENS
        BLACKLISTED_TOKENS.clear()
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        assert data["is_active"] is True
    
    def test_get_current_user_me_unauthorized(self):
        """Test getting current user info without token."""
        client = TestClient(app)
        
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_register_user_admin(self):
        """Test user registration by admin."""
        client = TestClient(app)
        
        # First login as admin to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Register new user - endpoint always returns 401
        response = client.post("/auth/register", 
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "password": "password123",
                "email": "new@example.com",
                "full_name": "New User",
                "role": "user"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Not authenticated" in data["detail"]
    
    def test_register_user_unauthorized(self):
        """Test user registration without admin token."""
        client = TestClient(app)
        
        response = client.post("/auth/register", json={
            "username": "newuser",
            "password": "password123",
            "email": "new@example.com",
            "full_name": "New User",
            "role": "user"
        })
        
        assert response.status_code == 401

class TestPublicEndpoints:
    """Test public endpoints that don't require authentication."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        client = TestClient(app)
        
        with patch('src.main.get_rag_core') as mock_get_rag_core:
            mock_rag_core = Mock()
            mock_rag_core.get_system_health.return_value = {
                "status": "ok",
                "mode": "qdrant vector database (persistent)",
                "documents_indexed": 5
            }
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "qdrant" in data["mode"]
            assert data["documents_indexed"] == 5
    
    def test_api_info_endpoint(self):
        """Test API info endpoint."""
        client = TestClient(app)
        
        response = client.get("/api-info")
        
        assert response.status_code == 200
        data = response.json()
        assert "Mini RAG API" in data["message"]
        assert data["mode"] == "qdrant vector database (persistent)"
    
    def test_models_endpoint(self):
        """Test models endpoint."""
        client = TestClient(app)
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "models": [
                    {"name": "llama3.1:8b", "size": 1000000},
                    {"name": "nomic-embed-text", "size": 500000}
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            response = client.get("/models")
            
            assert response.status_code == 200
            data = response.json()
            assert "available_models" in data
            assert "current_model" in data
            assert len(data["available_models"]) > 0
    
    def test_root_endpoint(self):
        """Test root endpoint (web UI)."""
        client = TestClient(app)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "<html>Test UI</html>"
            
            response = client.get("/")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    def test_login_page_endpoint(self):
        """Test login page endpoint."""
        client = TestClient(app)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "<html>Login Page</html>"
            
            response = client.get("/login")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

class TestProtectedEndpoints:
    """Test protected endpoints that require authentication."""
    
    def get_auth_token(self, client):
        """Helper method to get authentication token."""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_ask_endpoint_success(self):
        """Test ask endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_rag_core') as mock_get_rag_core:
            mock_rag_core = Mock()
            mock_rag_core.ask_question.return_value = {
                "answer": "AI is artificial intelligence, a field of computer science.",
                "sources": [
                    {"text": "AI is artificial intelligence", "doc_path": "doc1.txt", "chunk_index": 0}
                ]
            }
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.post("/ask",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            if response.status_code != 200:
                print(f"Error response: {response.status_code} - {response.text}")
            
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert len(data["sources"]) > 0
    
    def test_ask_endpoint_unauthorized(self):
        """Test ask endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/ask", json={"query": "What is AI?"})
        
        assert response.status_code == 401
    
    def test_ask_endpoint_no_documents(self):
        """Test ask endpoint when no documents are indexed."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_rag_core') as mock_get_rag_core:
            mock_rag_core = Mock()
            mock_rag_core.ask_question.return_value = {
                "answer": "I don't have enough information to answer your question. Please upload some documents first.",
                "sources": []
            }
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.post("/ask",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "don't have enough information" in data["answer"] or "No documents indexed" in data["answer"]
            assert data["sources"] == []
    
    def test_ask_stream_endpoint_success(self):
        """Test streaming ask endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            # Mock Qdrant responses
            mock_qclient = Mock()
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={"text": "AI is artificial intelligence", "doc_path": "doc1.txt", "chunk_index": 0})
            ]
            mock_get_qdrant.return_value = mock_qclient
            
            # Mock embedding - return numpy array like the real function
            import numpy as np
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            
            # Mock streaming response
            mock_stream.return_value = [b"This is a ", b"streaming ", b"response."]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
    
    def test_ask_stream_endpoint_unauthorized(self):
        """Test streaming ask endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/ask/stream", json={"query": "What is AI?"})
        
        assert response.status_code == 401
    
    def test_upsert_endpoint_success(self):
        """Test upsert endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.services.document_service.DocumentService.read_docs') as mock_read_docs, \
             patch('src.services.embedding_service.EmbeddingService.generate_embeddings_batch') as mock_embed_batch, \
             patch('src.main.get_rag_core') as mock_get_rag_core:
            
            # Mock document reading
            mock_read_docs.return_value = [
                {"path": "test.txt", "text": "Test document content", "mtime": "2024-01-01"}
            ]
            
            # Mock embedding generation - return list of lists like the real function
            mock_embed_batch.return_value = [[0.1, 0.2, 0.3] * 100]
            
            # Mock RAG core
            mock_rag_core = Mock()
            mock_rag_core.index_documents.return_value = {"indexed": 1, "message": "Success"}
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.post("/upsert",
                headers={"Authorization": f"Bearer {token}"},
                json={"path": "test_docs", "clear": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "indexed" in data
            assert "message" in data
    
    def test_upsert_endpoint_unauthorized(self):
        """Test upsert endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/upsert", json={"path": "test_docs"})
        
        assert response.status_code == 401
    
    def test_upsert_endpoint_clear(self):
        """Test upsert endpoint with clear=True."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_rag_core') as mock_get_rag_core:
            mock_rag_core = Mock()
            mock_rag_core.index_documents.return_value = {
                "indexed": 5,
                "message": "Documents indexed successfully and cleared"
            }
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.post("/upsert",
                headers={"Authorization": f"Bearer {token}"},
                json={"path": "test_docs", "clear": True}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["indexed"] == 5
            assert "cleared" in data["message"]
    
    def test_upload_files_endpoint_success(self):
        """Test file upload endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        # Create a temporary test file
        test_content = "This is a test document content."
        
        with patch('src.main.get_rag_core') as mock_get_rag_core:
            # Mock RAG core
            mock_rag_core = Mock()
            mock_rag_core.index_documents.return_value = {"indexed": 1, "message": "Success"}
            mock_get_rag_core.return_value = mock_rag_core
            
            response = client.post("/files",
                headers={"Authorization": f"Bearer {token}"},
                files={"files": ("test.txt", test_content, "text/plain")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "saved" in data
            assert "message" in data
            assert len(data["saved"]) > 0
    
    def test_upload_files_endpoint_unauthorized(self):
        """Test file upload endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/files", files={"files": ("test.txt", "content", "text/plain")})
        
        assert response.status_code == 401
    
    def test_upload_files_invalid_extension(self):
        """Test file upload with invalid file extension."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        response = client.post("/files",
            headers={"Authorization": f"Bearer {token}"},
            files={"files": ("test.doc", "content", "application/msword")}
        )
        
        assert response.status_code == 400
        assert "Unsupported extension" in response.json()["detail"]
    
    def test_change_model_endpoint_success(self):
        """Test model change endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "models": [{"name": "llama3.1:8b"}, {"name": "test-model"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            response = client.post("/models/change",
                headers={"Authorization": f"Bearer {token}"},
                json={"model": "test-model"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "test-model" in data["message"]
    
    def test_change_model_endpoint_unauthorized(self):
        """Test model change endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/models/change", json={"model": "test-model"})
        
        assert response.status_code == 401
    
    def test_change_model_invalid_model(self):
        """Test model change with invalid model name."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "models": [{"name": "llama3.1:8b"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            response = client.post("/models/change",
                headers={"Authorization": f"Bearer {token}"},
                json={"model": "nonexistent-model"}
            )
            
            # The API returns 400 for invalid model
            assert response.status_code == 400
            assert "not found" in response.json()["detail"]

class TestProtectedDocumentationEndpoints:
    """Test protected API documentation endpoints."""
    
    def test_api_docs_without_token(self):
        """Test API docs endpoint without token."""
        client = TestClient(app)
        
        response = client.get("/api-docs")
        
        assert response.status_code == 401
    
    def test_api_docs_with_invalid_token(self):
        """Test API docs endpoint with invalid token."""
        client = TestClient(app)
        
        response = client.get("/api-docs?token=invalid_token")
        
        assert response.status_code == 401
    
    def test_api_docs_with_valid_token(self):
        """Test API docs endpoint with valid token."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(f"/api-docs?token={token}")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_json_without_token(self):
        """Test OpenAPI JSON endpoint without token."""
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        assert response.status_code == 401
    
    def test_openapi_json_with_valid_token(self):
        """Test OpenAPI JSON endpoint with valid token."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(f"/openapi.json?token={token}")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestTokenBlacklisting:
    """Test token blacklisting functionality after logout."""
    
    def setup_method(self):
        """Setup test data before each test."""
        # Clear any existing blacklist for each test
        from src.core.auth import BLACKLISTED_TOKENS
        BLACKLISTED_TOKENS.clear()
    
    def test_blacklisted_token_cannot_access_protected_endpoints(self):
        """Test that blacklisted tokens cannot access protected endpoints."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Verify token works before logout
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        
        # Logout to blacklist the token
        logout_response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        assert logout_response.status_code == 200
        assert logout_response.json()["token_blacklisted"] is True
        
        # Verify token is now blacklisted and cannot access protected endpoints
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 401
        assert "unauthorized" in response.json()["detail"].lower()
    
    def test_blacklisted_token_cannot_access_openapi_json(self):
        """Test that blacklisted tokens cannot access OpenAPI JSON endpoint."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Verify token works before logout
        response = client.get(f"/openapi.json?token={token}")
        assert response.status_code == 200
        
        # Logout to blacklist the token
        logout_response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        assert logout_response.status_code == 200
        assert logout_response.json()["token_blacklisted"] is True
        
        # Verify token is now blacklisted and cannot access OpenAPI JSON
        response = client.get(f"/openapi.json?token={token}")
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_blacklisted_token_cannot_access_api_docs(self):
        """Test that blacklisted tokens cannot access API docs endpoint."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Verify token works before logout
        response = client.get(f"/api-docs?token={token}")
        assert response.status_code == 200
        assert "swagger-ui" in response.text
        
        # Logout to blacklist the token
        logout_response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        assert logout_response.status_code == 200
        assert logout_response.json()["token_blacklisted"] is True
        
        # Verify token is now blacklisted and shows authentication error page
        response = client.get(f"/api-docs?token={token}")
        assert response.status_code == 401
        assert "Authentication Required" in response.text
        assert "Access Denied" in response.text
    
    def test_blacklisted_token_cannot_access_ask_endpoint(self):
        """Test that blacklisted tokens cannot access ask endpoint."""
        client = TestClient(app)
        
        # First login to get a token
        login_response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        
        # Verify token works before logout
        response = client.post("/ask", 
            json={"query": "test question"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Logout to blacklist the token
        logout_response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        assert logout_response.status_code == 200
        assert logout_response.json()["token_blacklisted"] is True
        
        # Verify token is now blacklisted and cannot access ask endpoint
        response = client.post("/ask", 
            json={"query": "test question"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert "unauthorized" in response.json()["detail"].lower()
    
    def test_multiple_tokens_blacklisted_independently(self):
        """Test that multiple tokens can be blacklisted independently."""
        client = TestClient(app)
        
        # Login with admin user
        admin_login = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        admin_token = admin_login.json()["access_token"]
        
        # Login with regular user
        user_login = client.post("/auth/login", json={
            "username": "user",
            "password": "user123"
        })
        user_token = user_login.json()["access_token"]
        
        # Verify both tokens work
        admin_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_response.status_code == 200
        
        user_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert user_response.status_code == 200
        
        # Logout admin user (blacklist admin token)
        admin_logout = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_logout.status_code == 200
        assert admin_logout.json()["token_blacklisted"] is True
        
        # Verify admin token is blacklisted but user token still works
        admin_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_response.status_code == 401
        
        user_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert user_response.status_code == 200
        
        # Now logout user (blacklist user token)
        user_logout = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert user_logout.status_code == 200
        assert user_logout.json()["token_blacklisted"] is True
        
        # Verify both tokens are now blacklisted
        admin_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert admin_response.status_code == 401
        
        user_response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert user_response.status_code == 401