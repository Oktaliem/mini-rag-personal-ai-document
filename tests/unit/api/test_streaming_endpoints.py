"""
Unit tests for streaming endpoints and functionality.

This module tests the streaming functionality including:
- /ask/stream endpoint
- stream_answer helper function
- Payload structure handling
- Authentication with streaming
- Error scenarios for streaming
- Regression tests for fixed issues
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json
import numpy as np
from io import BytesIO

# Import the app
from src.main import app


class TestStreamingEndpoints:
    """Test streaming endpoint functionality."""
    
    def setup_method(self):
        """Clear blacklisted tokens before each test."""
        from src.core.auth import BLACKLISTED_TOKENS, BLACKLISTED_REFRESH_TOKENS
        BLACKLISTED_TOKENS.clear()
        BLACKLISTED_REFRESH_TOKENS.clear()
    
    def get_auth_token(self, client):
        """Helper method to get authentication token."""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_ask_stream_endpoint_success(self):
        """Test successful streaming ask endpoint with authentication."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            # Mock Qdrant client and responses
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={"text": "AI is artificial intelligence", "doc_path": "doc1.txt", "chunk_index": 0})
            ]
            
            # Mock embedding - return numpy array like the real function
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            
            # Mock streaming response
            mock_stream.return_value = [b"This is a ", b"streaming ", b"response."]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            # Note: TestClient may not always include transfer-encoding header
            # The important thing is that the response is successful and has the right content type
    
    def test_ask_stream_endpoint_unauthorized(self):
        """Test streaming ask endpoint without authentication."""
        client = TestClient(app)
        
        response = client.post("/ask/stream", json={"query": "What is AI?"})
        
        assert response.status_code == 401
        assert "unauthorized" in response.json()["detail"].lower()
    
    def test_ask_stream_endpoint_no_documents(self):
        """Test streaming ask endpoint when no documents are indexed."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant:
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=0)
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            # Should return a message about no documents indexed
            content = response.text
            assert "No documents indexed" in content
    
    def test_ask_stream_endpoint_database_error(self):
        """Test streaming ask endpoint when database error occurs."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant:
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.side_effect = Exception("Database connection failed")
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            content = response.text
            assert "Database error" in content
    
    def test_ask_stream_endpoint_embedding_failure(self):
        """Test streaming ask endpoint when embedding fails."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_embed.side_effect = Exception("Embedding service unavailable")
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            content = response.text
            assert "Embedding failed" in content
    
    def test_ask_stream_endpoint_search_failure(self):
        """Test streaming ask endpoint when search fails."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_qclient.search.side_effect = Exception("Search service unavailable")
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            content = response.text
            assert "Search failed" in content
    
    def test_ask_stream_endpoint_no_relevant_results(self):
        """Test streaming ask endpoint when no relevant results found."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_qclient.search.return_value = []  # No results
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            content = response.text
            assert "No relevant information found" in content


class TestPayloadStructureHandling:
    """Test payload structure handling for different document formats."""
    
    def get_auth_token(self, client):
        """Helper method to get authentication token."""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_payload_with_chunk_index(self):
        """Test payload structure with chunk_index field (original format)."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={
                    "text": "AI is artificial intelligence", 
                    "doc_path": "doc1.txt", 
                    "chunk_index": 0
                })
            ]
            
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            # Verify stream_answer was called with correct chunk structure
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0]
            query, chunks = call_args
            assert query == "What is AI?"
            assert len(chunks) == 1
            assert chunks[0]["text"] == "AI is artificial intelligence"
            assert chunks[0]["doc_path"] == "doc1.txt"
            assert chunks[0]["chunk_index"] == 0
    
    def test_payload_without_chunk_index(self):
        """Test payload structure without chunk_index field (regression test)."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={
                    "text": "AI is artificial intelligence", 
                    "doc_path": "doc1.txt"
                    # No chunk_index field
                })
            ]
            
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            # Verify stream_answer was called with correct chunk structure
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0]
            query, chunks = call_args
            assert query == "What is AI?"
            assert len(chunks) == 1
            assert chunks[0]["text"] == "AI is artificial intelligence"
            assert chunks[0]["doc_path"] == "doc1.txt"
            assert "chunk_index" not in chunks[0]  # Should not be present
    
    def test_payload_with_missing_fields(self):
        """Test payload structure with missing text or doc_path fields."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={
                    "text": "AI is artificial intelligence"
                    # Missing doc_path
                })
            ]
            
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            # Verify stream_answer was called with correct chunk structure
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0]
            query, chunks = call_args
            assert query == "What is AI?"
            assert len(chunks) == 1
            assert chunks[0]["text"] == "AI is artificial intelligence"
            assert chunks[0]["doc_path"] == "unknown"  # Should default to "unknown"
    
    def test_payload_with_empty_text(self):
        """Test payload structure with empty text field."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={
                    "text": "",  # Empty text
                    "doc_path": "doc1.txt"
                })
            ]
            
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            # Verify stream_answer was called with correct chunk structure
            mock_stream.assert_called_once()
            call_args = mock_stream.call_args[0]
            query, chunks = call_args
            assert query == "What is AI?"
            assert len(chunks) == 1
            assert chunks[0]["text"] == ""  # Should preserve empty string
            assert chunks[0]["doc_path"] == "doc1.txt"


class TestStreamAnswerFunction:
    """Test the stream_answer helper function directly."""
    
    def test_stream_answer_basic_functionality(self):
        """Test basic stream_answer function functionality."""
        from src.main import stream_answer
        
        # Mock the requests.post call
        with patch('src.main.requests.post') as mock_post:
            # Mock the streaming response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.iter_lines.return_value = [
                '{"response": "Hello", "done": false}',
                '{"response": " world", "done": false}',
                '{"response": "!", "done": true}'
            ]
            mock_post.return_value.__enter__.return_value = mock_response
            
            # Test data
            query = "Test question"
            ctx_blocks = [
                {"text": "Test context", "doc_path": "test.txt"}
            ]
            
            # Call the function
            result = list(stream_answer(query, ctx_blocks))
            
            # Verify results
            assert len(result) == 3
            assert result[0] == b"Hello"
            assert result[1] == b" world"
            assert result[2] == b"!"
    
    def test_stream_answer_with_multiple_context_blocks(self):
        """Test stream_answer with multiple context blocks."""
        from src.main import stream_answer
        
        with patch('src.main.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.iter_lines.return_value = [
                '{"response": "Response", "done": true}'
            ]
            mock_post.return_value.__enter__.return_value = mock_response
            
            query = "Test question"
            ctx_blocks = [
                {"text": "Context 1", "doc_path": "doc1.txt"},
                {"text": "Context 2", "doc_path": "doc2.txt"},
                {"text": "Context 3", "doc_path": "doc3.txt", "chunk_index": 0}
            ]
            
            result = list(stream_answer(query, ctx_blocks))
            
            # Verify the request was made with proper context formatting
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0].endswith("/api/generate")
            
            # Check the JSON payload
            json_payload = call_args[1]["json"]
            assert json_payload["model"] is not None
            assert json_payload["stream"] is True
            assert "Context:" in json_payload["prompt"]
            assert "From doc1.txt: Context 1" in json_payload["prompt"]
            assert "From doc2.txt: Context 2" in json_payload["prompt"]
            assert "From doc3.txt: Context 3" in json_payload["prompt"]
            assert "Test question" in json_payload["prompt"]
    
    def test_stream_answer_handles_json_decode_error(self):
        """Test stream_answer handles JSON decode errors gracefully."""
        from src.main import stream_answer
        
        with patch('src.main.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.iter_lines.return_value = [
                '{"response": "Valid JSON", "done": false}',
                'Invalid JSON line',
                '{"response": "Another valid", "done": true}'
            ]
            mock_post.return_value.__enter__.return_value = mock_response
            
            query = "Test question"
            ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
            
            result = list(stream_answer(query, ctx_blocks))
            
            # Should skip invalid JSON and return valid responses
            assert len(result) == 2
            assert result[0] == b"Valid JSON"
            assert result[1] == b"Another valid"
    
    def test_stream_answer_handles_empty_response(self):
        """Test stream_answer handles empty response fields."""
        from src.main import stream_answer
        
        with patch('src.main.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.iter_lines.return_value = [
                '{"response": "", "done": false}',  # Empty response
                '{"response": "Valid response", "done": false}',
                '{"done": true}'  # No response field
            ]
            mock_post.return_value.__enter__.return_value = mock_response
            
            query = "Test question"
            ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
            
            result = list(stream_answer(query, ctx_blocks))
            
            # Should only return non-empty responses
            assert len(result) == 1
            assert result[0] == b"Valid response"


class TestStreamingRegressionTests:
    """Regression tests for issues that were fixed."""
    
    def get_auth_token(self, client):
        """Helper method to get authentication token."""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]
    
    def test_regression_keyerror_chunk_index(self):
        """Regression test for KeyError: 'chunk_index' issue."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            # This payload structure was causing the KeyError
            mock_qclient.search.return_value = [
                Mock(payload={
                    "text": "AI is artificial intelligence", 
                    "doc_path": "doc1.txt"
                    # Missing chunk_index - this was causing the error
                })
            ]
            
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            # This should not raise a KeyError anymore
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "What is AI?"}
            )
            
            assert response.status_code == 200
            # Verify the function completed successfully without KeyError
    
    def test_regression_syntax_errors(self):
        """Regression test to ensure syntax errors are fixed."""
        # This test ensures the module can be imported without syntax errors
        from src.main import app, stream_answer, embed_ollama, sha1_u64
        
        # Basic functionality tests
        assert app is not None
        assert callable(stream_answer)
        assert callable(embed_ollama)
        assert callable(sha1_u64)
        
        # Test sha1_u64 function
        result = sha1_u64("test")
        assert isinstance(result, int)
        assert result > 0
    
    def test_regression_authentication_flow(self):
        """Regression test for authentication flow with streaming."""
        client = TestClient(app)
        
        # Test that authentication is required
        response = client.post("/ask/stream", json={"query": "test"})
        assert response.status_code == 401
        
        # Test that valid authentication works
        token = self.get_auth_token(client)
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = []
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Test response"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test"}
            )
            
            assert response.status_code == 200
    
    def test_regression_streaming_response_format(self):
        """Regression test for proper streaming response format."""
        client = TestClient(app)
        token = self.get_auth_token(client)
        
        with patch('src.main.get_qdrant_client') as mock_get_qdrant, \
             patch('src.main.embed_ollama') as mock_embed, \
             patch('src.main.stream_answer') as mock_stream:
            
            mock_qclient = Mock()
            mock_get_qdrant.return_value = mock_qclient
            mock_qclient.get_collection.return_value = Mock(points_count=5)
            mock_qclient.search.return_value = [
                Mock(payload={"text": "test", "doc_path": "test.txt"})
            ]
            mock_embed.return_value = np.array([0.1, 0.2, 0.3] * 100, dtype=np.float32)
            mock_stream.return_value = [b"Chunk1", b"Chunk2", b"Chunk3"]
            
            response = client.post("/ask/stream",
                headers={"Authorization": f"Bearer {token}"},
                json={"query": "test"}
            )
            
            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]
            # Note: TestClient may not always include transfer-encoding header
            # The important thing is that the response is successful and has the right content type
            
            # Verify the response content
            content = response.text
            assert "Chunk1" in content
            assert "Chunk2" in content
            assert "Chunk3" in content
