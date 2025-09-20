"""
Core RAG (Retrieval-Augmented Generation) business logic.

This module contains the core RAG operations and business rules.
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from fastapi import HTTPException

from .config import settings
from ..services.rag_service import RAGService
from ..services.document_service import DocumentService
from ..services.embedding_service import EmbeddingService


class RAGCore:
    """Core RAG business logic."""
    
    def __init__(self, qdrant_client: QdrantClient):
        self.rag_service = RAGService(qdrant_client)
        self.document_service = DocumentService()
        self.embedding_service = EmbeddingService(settings, qdrant_client)
    
    def initialize_collection(self, clear: bool = False) -> Dict[str, Any]:
        """Initialize the vector collection."""
        try:
            self.rag_service.ensure_collection(768, clear=clear)
            return {"status": "success", "message": "Collection initialized"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def index_documents(self, datapath: Optional[str] = None, clear: bool = False) -> Dict[str, Any]:
        """Index documents from a directory."""
        if datapath is None:
            datapath = settings.docs_dir
        
        try:
            result = self.rag_service.index_documents(datapath, clear=clear)
            return result
        except Exception as e:
            return {"indexed": 0, "message": f"Indexing failed: {str(e)}"}
    
    def ask_question(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Ask a question and get an answer."""
        try:
            result = self.rag_service.ask_question(query, top_k)
            return result
        except Exception as e:
            return {"answer": f"Error: {str(e)}", "sources": []}
    
    def ask_question_stream(self, query: str, top_k: Optional[int] = None) -> Any:
        """Ask a question and stream the answer."""
        try:
            return self.rag_service.ask_question_stream(query, top_k)
        except Exception as e:
            yield f"Error: {str(e)}".encode('utf-8')
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get the status of the vector collection."""
        try:
            info = self.rag_service.get_collection_info()
            return {"status": "success", **info}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def process_uploaded_files(self, files: List[Any]) -> Dict[str, Any]:
        """Process uploaded files."""
        try:
            result = self.document_service.process_uploaded_files(files)
            return result
        except HTTPException:
            # Re-raise HTTPExceptions to preserve status codes
            raise
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    
    def get_document_stats(self, datapath: Optional[str] = None) -> Dict[str, Any]:
        """Get document statistics."""
        if datapath is None:
            datapath = settings.docs_dir
        
        try:
            stats = self.document_service.get_document_stats(datapath)
            return {"status": "success", **stats}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate a query before processing."""
        if not query or not query.strip():
            return {"status": "error", "message": "Query cannot be empty"}
        
        if len(query.strip()) < 3:
            return {"status": "error", "message": "Query too short"}
        
        if len(query) > 1000:
            return {"status": "error", "message": "Query too long"}
        
        return {"status": "success", "message": "Query is valid"}
    
    def validate_top_k(self, top_k: Optional[int]) -> Dict[str, Any]:
        """Validate top_k parameter."""
        if top_k is None:
            return {"status": "success", "top_k": settings.top_k}
        
        if top_k < 1:
            return {"status": "error", "message": "top_k must be at least 1"}
        
        if top_k > 50:
            return {"status": "error", "message": "top_k cannot exceed 50"}
        
        return {"status": "success", "top_k": top_k}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            # Check Qdrant connection
            collection_info = self.rag_service.get_collection_info()
            
            # Check Ollama connection
            try:
                self.embedding_service.generate_embedding("test")
                ollama_status = "connected"
            except Exception:
                ollama_status = "disconnected"
            
            return {
                "status": "ok",
                "mode": "qdrant (persistent)",
                "ollama": settings.ollama_url,
                "qdrant": settings.qdrant_url,
                "documents_indexed": collection_info.get("points_count", 0),
                "message": "Running with Qdrant vector database",
                "ollama_status": ollama_status,
                "qdrant_status": "connected" if collection_info.get("status") == "active" else "disconnected"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }
