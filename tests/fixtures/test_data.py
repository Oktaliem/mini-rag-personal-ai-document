"""
Test data fixtures for Mini RAG tests.

This module provides common test data used across different test modules.
"""

# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals.",
        "doc_path": "test_docs/ai_intro.txt",
        "metadata": {"source": "test", "type": "introduction"}
    },
    {
        "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed.",
        "doc_path": "test_docs/ml_basics.txt", 
        "metadata": {"source": "test", "type": "definition"}
    },
    {
        "text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data.",
        "doc_path": "test_docs/dl_overview.txt",
        "metadata": {"source": "test", "type": "overview"}
    }
]

# Sample questions for testing
SAMPLE_QUESTIONS = [
    "What is artificial intelligence?",
    "How does machine learning work?",
    "What is the difference between AI and ML?",
    "Explain deep learning concepts",
    "What are neural networks?"
]

# Sample answers for testing
SAMPLE_ANSWERS = [
    "Artificial intelligence is intelligence demonstrated by machines...",
    "Machine learning works by using algorithms that can learn from data...",
    "AI is the broader concept, while ML is a subset of AI...",
    "Deep learning uses neural networks with multiple layers...",
    "Neural networks are computing systems inspired by biological neural networks..."
]

# Sample embeddings (mock data)
SAMPLE_EMBEDDINGS = [
    [0.1, 0.2, 0.3] * 100,  # 300-dimensional vector
    [0.4, 0.5, 0.6] * 100,  # 300-dimensional vector
    [0.7, 0.8, 0.9] * 100,  # 300-dimensional vector
]

# Sample user data
SAMPLE_USERS = [
    {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "role": "user",
        "is_active": True
    },
    {
        "username": "admin",
        "email": "admin@example.com", 
        "full_name": "Admin User",
        "password": "admin123",
        "role": "admin",
        "is_active": True
    }
]

# Sample file content for testing
SAMPLE_FILE_CONTENT = {
    "test.txt": "This is a test document about artificial intelligence and machine learning.",
    "test.md": "# AI Overview\n\nThis document provides an overview of artificial intelligence concepts.",
    "test.pdf": "PDF content would be here in a real scenario."
}

# Sample API responses
SAMPLE_API_RESPONSES = {
    "login_success": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    },
    "ask_success": {
        "answer": "Based on the provided context, artificial intelligence is...",
        "sources": ["doc1.txt", "doc2.txt"],
        "model_used": "llama2"
    },
    "upload_success": {
        "message": "Files uploaded successfully",
        "files_processed": 2,
        "files_failed": 0
    }
}

# Sample error responses
SAMPLE_ERROR_RESPONSES = {
    "unauthorized": {
        "detail": "Not authenticated"
    },
    "forbidden": {
        "detail": "Not enough permissions"
    },
    "not_found": {
        "detail": "Resource not found"
    },
    "validation_error": {
        "detail": [
            {
                "loc": ["body", "username"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
}
