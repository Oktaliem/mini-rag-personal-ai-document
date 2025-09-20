"""
RAG (Retrieval-Augmented Generation) API routes.

This module contains all RAG-related API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional, Iterable, Iterator

from ...core.models import User, QuestionRequest, QuestionResponse
from ...core.rag import RAGCore
from ...api.dependencies import get_current_user_dependency, get_rag_core

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
 ) -> QuestionResponse:
    """Ask a question and get an answer."""
    try:
        # Validate query
        query_validation = rag_core.validate_query(request.query)
        if query_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=query_validation["message"]
            )
        
        # Validate top_k
        top_k_validation = rag_core.validate_top_k(request.top_k)
        if top_k_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=top_k_validation["message"]
            )
        
        # Ask question
        result = rag_core.ask_question(request.query, top_k_validation["top_k"])
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            model_used="ollama",
            processing_time=0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.post("/ask/stream")
async def ask_question_stream(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> StreamingResponse:
    """Ask a question and stream the answer."""
    try:
        # Validate query
        query_validation = rag_core.validate_query(request.query)
        if query_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=query_validation["message"]
            )
        
        # Validate top_k
        top_k_validation = rag_core.validate_top_k(request.top_k)
        if top_k_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=top_k_validation["message"]
            )
        
        # Stream answer
        def generate() -> Iterator[bytes]:
            try:
                for chunk in rag_core.ask_question_stream(request.query, top_k_validation["top_k"]):
                    yield chunk
            except Exception as e:
                yield f"Error: {str(e)}".encode('utf-8')
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process streaming question: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str,
    top_k: Optional[int] = None,
    current_user: User = Depends(get_current_user_dependency),
    rag_core: RAGCore = Depends(get_rag_core)
) -> dict:
    """Search for similar documents."""
    try:
        # Validate query
        query_validation = rag_core.validate_query(query)
        if query_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=query_validation["message"]
            )
        
        # Validate top_k
        top_k_validation = rag_core.validate_top_k(top_k)
        if top_k_validation["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=top_k_validation["message"]
            )
        
        # Search documents
        similar_chunks = rag_core.rag_service.search_similar_chunks(query, top_k_validation["top_k"])
        
        return {
            "query": query,
            "results": similar_chunks,
            "count": len(similar_chunks)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}"
        )
