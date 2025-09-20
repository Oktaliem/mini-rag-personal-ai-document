import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from src.main import app
from src.core.models import User, QuestionRequest, QuestionResponse


class TestRagRoutes:
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

    def test_ask_question_success(self):
        """Test successful question asking"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.get_rag_core') as mock_rag:
            mock_user.return_value = self.test_user
            mock_rag.return_value.ask_question.return_value = {
                "answer": "Test answer",
                "sources": ["doc1", "doc2"],
                "model_used": "llama3.1:8b"
            }
            
            response = self.client.post("/ask",
                headers={"Authorization": "Bearer fake_token"},
                json={"query": "What is this about?"})
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "answer" in data
            assert "sources" in data

    def test_ask_question_unauthorized(self):
        """Test asking question without authentication"""
        response = self.client.post("/ask",
            json={"query": "What is this about?"})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_ask_question_empty_query(self):
        """Test asking question with empty query"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.get_rag_core') as mock_rag:
            mock_user.return_value = self.test_user
            mock_rag.return_value.ask_question.return_value = {"answer": "Error: Query cannot be empty", "sources": []}
            
            response = self.client.post("/ask",
                headers={"Authorization": "Bearer fake_token"},
                json={"query": ""})
            
            assert response.status_code == status.HTTP_200_OK
            assert "Query cannot be empty" in response.json()["answer"]

    def test_ask_question_streaming_success(self):
        """Test successful streaming question asking"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.stream_answer') as mock_stream:
            mock_user.return_value = self.test_user
            
            # Mock streaming response
            def mock_stream_response():
                yield b'{"answer": "Test", "sources": []}\n'
                yield b'{"answer": " answer", "sources": []}\n'
            
            mock_stream.return_value = mock_stream_response()
            
            response = self.client.post("/ask/stream",
                headers={"Authorization": "Bearer fake_token"},
                json={"query": "What is this about?"})
            
            assert response.status_code == status.HTTP_200_OK

    def test_ask_question_streaming_error(self):
        """Test streaming question with error"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.stream_answer') as mock_stream:
            mock_user.return_value = self.test_user
            mock_stream.side_effect = Exception("Streaming error")
            
            # The exception will be raised during the request, so we expect it to fail
            try:
                response = self.client.post("/ask/stream",
                    headers={"Authorization": "Bearer fake_token"},
                    json={"query": "What is this about?"})
                # If we get here, the test should fail
                assert False, "Expected exception to be raised"
            except Exception as e:
                # This is expected - the streaming error should propagate
                assert "Streaming error" in str(e)

    # Note: /search endpoint doesn't exist in current API
    # These tests are removed as they test non-existent functionality

    def test_ask_question_rag_error(self):
        """Test question asking with RAG service error"""
        with patch('src.core.auth.get_current_user_from_token') as mock_user, \
             patch('src.main.get_rag_core') as mock_rag:
            mock_user.return_value = self.test_user
            mock_rag.return_value.ask_question.side_effect = Exception("RAG error")
            
            # The exception will be raised during the request, so we expect it to fail
            try:
                response = self.client.post("/ask",
                    headers={"Authorization": "Bearer fake_token"},
                    json={"query": "What is this about?"})
                # If we get here, the test should fail
                assert False, "Expected exception to be raised"
            except Exception as e:
                # This is expected - the RAG error should propagate
                assert "RAG error" in str(e)

    # Note: /search endpoint doesn't exist in current API
    # This test is removed as it tests non-existent functionality
