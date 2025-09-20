"""
FastAPI dependencies for the Mini RAG API.

This module contains reusable dependencies for dependency injection.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from qdrant_client import QdrantClient

from ..core.config import settings
from ..core.models import User
from ..core.auth import get_current_active_user_from_token_sync
from ..core.rag import RAGCore
from ..core.di import provide_qdrant_client, provide_rag_core

security = HTTPBearer()


# Global instances (in production, use proper dependency injection)
_qdrant_client: Optional[QdrantClient] = None
_rag_core: Optional[RAGCore] = None


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client dependency."""
    # Prefer DI container; fall back to legacy singleton if needed
    try:
        return provide_qdrant_client()
    except Exception:
        global _qdrant_client
        if _qdrant_client is None:
            _qdrant_client = QdrantClient(settings.qdrant_url, timeout=60)
        return _qdrant_client


def get_rag_core(qdrant_client: QdrantClient = Depends(get_qdrant_client)) -> RAGCore:
    """Get RAG core dependency."""
    try:
        return provide_rag_core()
    except Exception:
        global _rag_core
        if _rag_core is None:
            _rag_core = RAGCore(qdrant_client)
        return _rag_core


def get_current_user_dependency(request: Request) -> User:
    """Get current user dependency from request."""
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Require authentication - no fallback to default user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    user = get_current_active_user_from_token_sync(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_database() -> None:
    """Get database connection dependency."""
    # Placeholder for database connection
    # In a real implementation, you would return a database session
    return None


def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token."""
    user = get_current_active_user_from_token_sync(token.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(token: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current active user from token."""
    user = get_current_user(token)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user


def get_current_admin_user(token: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current admin user from token."""
    user = get_current_active_user(token)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return user