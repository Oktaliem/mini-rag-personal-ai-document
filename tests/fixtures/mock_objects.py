"""
Mock objects and factories for testing.

This module provides mock objects and factory functions for creating test data.
"""

from unittest.mock import Mock, MagicMock
import numpy as np
from typing import List, Dict, Any
import tempfile
import os
from pathlib import Path


class MockOllamaResponse:
    """Mock Ollama API response."""
    
    def __init__(self, embedding: List[float] = None, response: str = None, done: bool = True):
        self.embedding = embedding or [0.1, 0.2, 0.3] * 100  # 300-dimensional
        self.response = response or "This is a mock response"
        self.done = done
    
    def json(self):
        if self.embedding:
            return {"embedding": self.embedding}
        else:
            return {"response": self.response, "done": self.done}
    
    def iter_lines(self):
        """Mock streaming response."""
        lines = [
            f'{{"response": "{self.response[:10]}", "done": false}}',
            f'{{"response": "{self.response[10:20]}", "done": false}}',
            f'{{"response": "{self.response[20:]}", "done": {str(self.done).lower()}}}'
        ]
        return [line.encode() for line in lines]
    
    def raise_for_status(self):
        pass


class MockQdrantClient:
    """Mock Qdrant client for testing."""
    
    def __init__(self):
        self.collections = {}
        self.points = {}
    
    def get_collections(self):
        """Mock get collections response."""
        mock_collections = []
        for name, collection in self.collections.items():
            mock_collection = Mock()
            mock_collection.name = name
            mock_collections.append(mock_collection)
        
        mock_response = Mock()
        mock_response.collections = mock_collections
        return mock_response
    
    def create_collection(self, collection_name: str, vectors_config: Dict):
        """Mock create collection."""
        self.collections[collection_name] = {
            "name": collection_name,
            "vectors_config": vectors_config
        }
        return Mock()
    
    def delete_collection(self, collection_name: str):
        """Mock delete collection."""
        if collection_name in self.collections:
            del self.collections[collection_name]
        return Mock()
    
    def upsert(self, collection_name: str, points: List[Dict]):
        """Mock upsert points."""
        if collection_name not in self.points:
            self.points[collection_name] = []
        self.points[collection_name].extend(points)
        return Mock()
    
    def search(self, collection_name: str, query_vector: List[float], limit: int = 10):
        """Mock search response."""
        # Return mock search results
        mock_results = []
        for i in range(min(limit, 3)):
            mock_result = Mock()
            mock_result.id = f"point_{i}"
            mock_result.score = 0.9 - (i * 0.1)
            mock_result.payload = {
                "text": f"Sample document text {i}",
                "doc_path": f"doc_{i}.txt"
            }
            mock_results.append(mock_result)
        
        mock_response = Mock()
        mock_response = mock_results
        return mock_response


class MockDatabaseManager:
    """Mock database manager for testing."""
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
    
    def get_user_by_username(self, username: str):
        """Mock get user by username."""
        return self.users.get(username)
    
    def create_user(self, user_data: Dict[str, Any]):
        """Mock create user."""
        username = user_data["username"]
        self.users[username] = user_data
        return user_data
    
    def update_user(self, username: str, user_data: Dict[str, Any]):
        """Mock update user."""
        if username in self.users:
            self.users[username].update(user_data)
            return self.users[username]
        return None
    
    def delete_user(self, username: str):
        """Mock delete user."""
        if username in self.users:
            del self.users[username]
            return True
        return False


def create_mock_embedding(dimensions: int = 300) -> np.ndarray:
    """Create a mock embedding vector."""
    return np.random.rand(dimensions).astype(np.float32)


def create_mock_document(text: str = "Sample document text", 
                        doc_path: str = "test.txt") -> Dict[str, Any]:
    """Create a mock document."""
    return {
        "text": text,
        "doc_path": doc_path,
        "metadata": {
            "source": "test",
            "type": "document"
        }
    }


def create_mock_user(username: str = "testuser", 
                    role: str = "user",
                    is_active: bool = True) -> Dict[str, Any]:
    """Create a mock user."""
    return {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": f"{username.title()} User",
        "password": "hashedpassword",
        "role": role,
        "is_active": is_active
    }


def create_temp_directory() -> str:
    """Create a temporary directory for testing."""
    return tempfile.mkdtemp()


def create_temp_files(directory: str, files: Dict[str, str]) -> List[str]:
    """Create temporary files in a directory."""
    created_files = []
    for filename, content in files.items():
        file_path = Path(directory) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        created_files.append(str(file_path))
    return created_files


def create_mock_request(headers: Dict[str, str] = None, 
                       json_data: Dict[str, Any] = None) -> Mock:
    """Create a mock FastAPI request."""
    mock_request = Mock()
    mock_request.headers = headers or {}
    mock_request.json = Mock(return_value=json_data or {})
    return mock_request


def create_mock_response(status_code: int = 200, 
                        json_data: Dict[str, Any] = None) -> Mock:
    """Create a mock FastAPI response."""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json = Mock(return_value=json_data or {})
    return mock_response
