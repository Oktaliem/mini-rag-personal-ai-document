"""
Document management API routes.

This module contains all document-related API endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from typing import List, Optional, Dict, Any

from ...core.models import User
from ...core.rag import RAGCore
from ...api.dependencies import get_current_user_dependency, get_rag_core

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upsert")
async def upsert_documents(
    path: Optional[str] = None,
    clear: bool = False,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> Dict[str, Any]:
    """Index documents from a directory."""
    try:
        result = rag_core.index_documents(path, clear=clear)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index documents: {str(e)}"
        )


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> Dict[str, Any]:
    """Upload and process files."""
    try:
        result = rag_core.process_uploaded_files(files)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload files: {str(e)}"
        )


@router.get("/stats")
async def get_document_stats(
    path: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> Dict[str, Any]:
    """Get document statistics."""
    try:
        result = rag_core.get_document_stats(path)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document stats: {str(e)}"
        )


@router.get("/collection/status")
async def get_collection_status(
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> Dict[str, Any]:
    """Get vector collection status."""
    try:
        result = rag_core.get_collection_status()
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection status: {str(e)}"
        )


@router.post("/collection/initialize")
async def initialize_collection(
    clear: bool = False,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> Dict[str, Any]:
    """Initialize the vector collection."""
    try:
        result = rag_core.initialize_collection(clear=clear)
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize collection: {str(e)}"
        )
