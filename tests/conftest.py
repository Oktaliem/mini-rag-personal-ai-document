"""
Test configuration and fixtures for Mini RAG tests.

This module provides shared fixtures and configuration for all test modules
in the refactored test structure.
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

# Set test environment variables
os.environ["OLLAMA_URL"] = "http://localhost:11434"
os.environ["GEN_MODEL"] = "llama3.1:8b"
os.environ["EMB_MODEL"] = "nomic-embed-text"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["QDRANT_COLLECTION"] = "test_rag_chunks"
os.environ["DOCS_DIR"] = "test_docs"
os.environ["CHUNK_SIZE"] = "800"
os.environ["CHUNK_OVERLAP"] = "120"
os.environ["TOP_K"] = "6"

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API responses."""
    return {
        "response": "This is a test response from the AI model.",
        "done": True
    }

@pytest.fixture
def mock_embedding():
    """Mock embedding vector."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500-dimensional vector

@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client."""
    mock_client = Mock()
    mock_client.get_collections.return_value = Mock()
    mock_client.get_collection.return_value = Mock(points_count=0)
    mock_client.search.return_value = []
    mock_client.upsert.return_value = Mock()
    mock_client.delete_collection.return_value = Mock()
    return mock_client

@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "path": "test_doc1.txt",
            "text": "This is a test document about artificial intelligence and machine learning.",
            "mtime": "2024-01-01T00:00:00Z"
        },
        {
            "path": "test_doc2.txt", 
            "text": "This document discusses natural language processing and text analysis techniques.",
            "mtime": "2024-01-02T00:00:00Z"
        }
    ]

@pytest.fixture
def test_user():
    """Test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "role": "user"
    }

@pytest.fixture
def test_admin():
    """Test admin user data."""
    return {
        "username": "admin",
        "email": "admin@example.com", 
        "full_name": "Administrator",
        "is_active": True,
        "role": "admin"
    }