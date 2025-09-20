import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from io import BytesIO

from src.main import app
from src.core.models import User


class TestDocumentRoutes:
    def setup_method(self):
        self.client = TestClient(app)
        self.test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            is_active=True,
            role="user"
        )

    def test_upsert_documents_success(self):
        """Test successful document upsert"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.get_rag_core') as mock_rag:
            mock_user.return_value = self.test_user
            mock_rag.return_value.index_documents.return_value = {"indexed": 1, "message": "Success"}
            
            response = self.client.post("/upsert",
                headers={"Authorization": "Bearer fake_token"},
                json={"path": "/test/path"})
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "indexed" in data

    def test_upsert_documents_unauthorized(self):
        """Test document upsert without authentication"""
        response = self.client.post("/upsert",
            json={"path": "/test/path"})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upsert_documents_invalid_path(self):
        """Test document upsert with invalid path"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.get_rag_core') as mock_rag:
            mock_user.return_value = self.test_user
            mock_rag.return_value.index_documents.return_value = {"indexed": 0, "message": "No indexable docs"}
            
            response = self.client.post("/upsert",
                headers={"Authorization": "Bearer fake_token"},
                json={"path": "/nonexistent/path"})
            
            assert response.status_code == status.HTTP_200_OK

    def test_upload_files_success(self):
        """Test successful file upload"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user:
            mock_user.return_value = self.test_user
            
            # Create a test file
            test_file = BytesIO(b"test content")
            test_file.name = "test.txt"
            
            response = self.client.post("/files",
                headers={"Authorization": "Bearer fake_token"},
                files={"files": ("test.txt", test_file, "text/plain")})
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "saved" in data

    def test_upload_files_no_files(self):
        """Test file upload with no files"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user:
            mock_user.return_value = self.test_user
            
            response = self.client.post("/files",
                headers={"Authorization": "Bearer fake_token"})
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # Check for FastAPI validation error format
            error_detail = response.json()["detail"]
            assert any("Field required" in str(item) for item in error_detail)

    def test_upload_files_unsupported_format(self):
        """Test file upload with unsupported format"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user:
            mock_user.return_value = self.test_user
            
            # Create an unsupported file
            test_file = BytesIO(b"test content")
            test_file.name = "test.xyz"
            
            response = self.client.post("/files",
                headers={"Authorization": "Bearer fake_token"},
                files={"files": ("test.xyz", test_file, "application/octet-stream")})
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Unsupported extension" in response.json()["detail"]

    # Note: Document stats, collection status, and initialize endpoints don't exist in the current API
    # These tests are removed as they test non-existent functionality
