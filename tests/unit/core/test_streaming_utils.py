"""
Unit tests for streaming utility functions.

This module tests the utility functions used in streaming functionality:
- sha1_u64 function
- embed_ollama function
- SYS prompt constant
- stream_answer function logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import hashlib
import requests

# Import the functions from main
from src.main import sha1_u64, embed_ollama, SYS, stream_answer


class TestSha1U64Function:
    """Test the sha1_u64 utility function."""
    
    def test_sha1_u64_basic_functionality(self):
        """Test basic sha1_u64 functionality."""
        result = sha1_u64("test")
        assert isinstance(result, int)
        assert result > 0
    
    def test_sha1_u64_consistency(self):
        """Test that sha1_u64 returns consistent results."""
        result1 = sha1_u64("test")
        result2 = sha1_u64("test")
        assert result1 == result2
    
    def test_sha1_u64_different_inputs(self):
        """Test that sha1_u64 returns different results for different inputs."""
        result1 = sha1_u64("test1")
        result2 = sha1_u64("test2")
        assert result1 != result2
    
    def test_sha1_u64_empty_string(self):
        """Test sha1_u64 with empty string."""
        result = sha1_u64("")
        assert isinstance(result, int)
        assert result >= 0
    
    def test_sha1_u64_unicode_string(self):
        """Test sha1_u64 with unicode string."""
        result = sha1_u64("测试")
        assert isinstance(result, int)
        assert result > 0
    
    def test_sha1_u64_special_characters(self):
        """Test sha1_u64 with special characters."""
        result = sha1_u64("!@#$%^&*()")
        assert isinstance(result, int)
        assert result > 0
    
    def test_sha1_u64_long_string(self):
        """Test sha1_u64 with long string."""
        long_string = "a" * 1000
        result = sha1_u64(long_string)
        assert isinstance(result, int)
        assert result > 0


class TestEmbedOllamaFunction:
    """Test the embed_ollama utility function."""
    
    @patch('src.main.requests.post')
    def test_embed_ollama_success(self, mock_post):
        """Test successful embed_ollama call."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100 dimensions
        }
        mock_post.return_value = mock_response
        
        result = embed_ollama("test text")
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 100
        assert np.allclose(np.linalg.norm(result), 1.0, atol=1e-6)  # Should be normalized
    
    @patch('src.main.requests.post')
    def test_embed_ollama_http_error(self, mock_post):
        """Test embed_ollama with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP 500")
        mock_post.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            embed_ollama("test text")
    
    @patch('src.main.requests.post')
    def test_embed_ollama_network_error(self, mock_post):
        """Test embed_ollama with network error."""
        mock_post.side_effect = requests.ConnectionError("Connection failed")
        
        with pytest.raises(requests.ConnectionError):
            embed_ollama("test text")
    
    @patch('src.main.requests.post')
    def test_embed_ollama_empty_embedding(self, mock_post):
        """Test embed_ollama with empty embedding response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"embedding": []}
        mock_post.return_value = mock_response
        
        result = embed_ollama("test text")
        
        # Should return an empty numpy array
        assert isinstance(result, np.ndarray)
        assert len(result) == 0
    
    @patch('src.main.requests.post')
    def test_embed_ollama_normalization(self, mock_post):
        """Test that embed_ollama properly normalizes vectors."""
        # Create a non-normalized embedding
        embedding = [1.0, 2.0, 3.0, 4.0, 5.0] * 20  # 100 dimensions
        norm = np.linalg.norm(embedding)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"embedding": embedding}
        mock_post.return_value = mock_response
        
        result = embed_ollama("test text")
        
        # Should be normalized to unit length
        assert np.allclose(np.linalg.norm(result), 1.0, atol=1e-6)
        # Should be proportional to original
        assert np.allclose(result * norm, np.array(embedding, dtype=np.float32))


class TestSysPromptConstant:
    """Test the SYS prompt constant."""
    
    def test_sys_prompt_exists(self):
        """Test that SYS prompt constant exists and is a string."""
        assert isinstance(SYS, str)
        assert len(SYS) > 0
    
    def test_sys_prompt_content(self):
        """Test that SYS prompt contains expected content."""
        assert "helpful" in SYS.lower()
        assert "assistant" in SYS.lower()
        assert "context" in SYS.lower()
        assert "question" in SYS.lower()
    
    def test_sys_prompt_formatting(self):
        """Test that SYS prompt is properly formatted."""
        # Should not have excessive whitespace
        assert not SYS.startswith(" ")
        assert not SYS.endswith(" ")
        # Should be a reasonable length
        assert 100 < len(SYS) < 2000


class TestStreamAnswerFunction:
    """Test the stream_answer function in detail."""
    
    @patch('src.main.requests.post')
    def test_stream_answer_basic_streaming(self, mock_post):
        """Test basic streaming functionality."""
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
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
        
        result = list(stream_answer(query, ctx_blocks))
        
        assert len(result) == 3
        assert result[0] == b"Hello"
        assert result[1] == b" world"
        assert result[2] == b"!"
    
    @patch('src.main.requests.post')
    def test_stream_answer_context_formatting(self, mock_post):
        """Test that context is properly formatted in the prompt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = ['{"response": "Done", "done": true}']
        mock_post.return_value.__enter__.return_value = mock_response
        
        query = "What is AI?"
        ctx_blocks = [
            {"text": "AI is artificial intelligence", "doc_path": "doc1.txt"},
            {"text": "Machine learning is a subset of AI", "doc_path": "doc2.txt", "chunk_index": 1}
        ]
        
        list(stream_answer(query, ctx_blocks))
        
        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check the JSON payload
        json_payload = call_args[1]["json"]
        prompt = json_payload["prompt"]
        
        # Should contain the system prompt
        assert SYS in prompt
        # Should contain context section
        assert "Context:" in prompt
        # Should contain the formatted context blocks
        assert "From doc1.txt: AI is artificial intelligence" in prompt
        assert "From doc2.txt: Machine learning is a subset of AI" in prompt
        # Should contain the question
        assert "What is AI?" in prompt
        # Should contain the instruction
        assert "Please provide a helpful and informative answer:" in prompt
    
    @patch('src.main.requests.post')
    def test_stream_answer_context_without_doc_path(self, mock_post):
        """Test context formatting when doc_path is missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = ['{"response": "Done", "done": true}']
        mock_post.return_value.__enter__.return_value = mock_response
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context"}]  # No doc_path
        
        list(stream_answer(query, ctx_blocks))
        
        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_payload = call_args[1]["json"]
        prompt = json_payload["prompt"]
        
        # Should contain the context without "From" prefix
        assert "Test context" in prompt
        assert "From" not in prompt
    
    @patch('src.main.requests.post')
    def test_stream_answer_handles_json_errors(self, mock_post):
        """Test that stream_answer handles JSON parsing errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = [
            '{"response": "Valid", "done": false}',
            'Invalid JSON line',
            '{"response": "Another valid", "done": true}'
        ]
        mock_post.return_value.__enter__.return_value = mock_response
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
        
        result = list(stream_answer(query, ctx_blocks))
        
        # Should skip invalid JSON and return valid responses
        assert len(result) == 2
        assert result[0] == b"Valid"
        assert result[1] == b"Another valid"
    
    @patch('src.main.requests.post')
    def test_stream_answer_handles_empty_responses(self, mock_post):
        """Test that stream_answer handles empty response fields."""
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
    
    @patch('src.main.requests.post')
    def test_stream_answer_http_error(self, mock_post):
        """Test that stream_answer handles HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP 500")
        mock_post.return_value.__enter__.return_value = mock_response
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
        
        with pytest.raises(requests.HTTPError):
            list(stream_answer(query, ctx_blocks))
    
    @patch('src.main.requests.post')
    def test_stream_answer_network_error(self, mock_post):
        """Test that stream_answer handles network errors."""
        mock_post.side_effect = requests.ConnectionError("Connection failed")
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
        
        with pytest.raises(requests.ConnectionError):
            list(stream_answer(query, ctx_blocks))
    
    @patch('src.main.requests.post')
    def test_stream_answer_request_parameters(self, mock_post):
        """Test that stream_answer makes the request with correct parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = ['{"response": "Done", "done": true}']
        mock_post.return_value.__enter__.return_value = mock_response
        
        query = "Test question"
        ctx_blocks = [{"text": "Test context", "doc_path": "test.txt"}]
        
        list(stream_answer(query, ctx_blocks))
        
        # Verify the request parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL
        assert call_args[0][0].endswith("/api/generate")
        
        # Check parameters
        assert call_args[1]["stream"] is True
        
        # Check JSON payload
        json_payload = call_args[1]["json"]
        assert "model" in json_payload
        assert "prompt" in json_payload
        assert json_payload["stream"] is True
