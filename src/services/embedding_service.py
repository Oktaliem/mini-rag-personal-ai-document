"""
Embedding service for document vectorization.
Handles text embedding generation using Ollama.
"""

import requests
import numpy as np
from typing import List, Dict, Any, Optional, Sequence, cast
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from ..core.config import Settings
from ..core.models import DocumentChunk


class EmbeddingService:
    """Service for handling document embeddings."""
    
    def __init__(self, settings: Settings, qdrant_client: Optional[QdrantClient] = None) -> None:
        self.settings = settings
        self.ollama_url = settings.ollama_url
        self.embedding_model = settings.embedding_model
        self.qdrant_client = qdrant_client or QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection
        
        # Collection will be created by RAGService
        # self._ensure_collection_exists()
    
    def _ensure_collection_exists(self) -> None:
        """Ensure the Qdrant collection exists."""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # nomic-embed-text embedding size
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise Exception(f"Failed to ensure collection exists: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using Ollama."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data["embedding"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")
        except KeyError as e:
            raise Exception(f"Invalid embedding response format: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def store_chunks(self, chunks: List[DocumentChunk]) -> bool:
        """Store document chunks with embeddings in Qdrant."""
        try:
            points = []
            for chunk in chunks:
                # Generate embedding if not provided
                if not chunk.embedding:
                    chunk.embedding = self.generate_embedding(chunk.content)
                
                point = PointStruct(
                    id=chunk.id,
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "source": chunk.source,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index
                    }
                )
                points.append(point)
            
            # Upsert points to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to store chunks: {str(e)}")
    
    def search_similar_chunks(
        self, 
        query: str, 
        top_k: int = 6,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build filter if provided
            query_filter: Optional[Filter] = None
            if filter_conditions:
                conditions: List[FieldCondition] = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    # Qdrant expects a list for 'must'
                    query_filter = Filter(must=conditions)  # type: ignore[arg-type]
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter
            )
            
            # Format results
            results: List[Dict[str, Any]] = []
            for hit in search_result:
                raw_payload = getattr(hit, "payload", None)
                payload: Dict[str, Any] = cast(Dict[str, Any], raw_payload or {})
                result: Dict[str, Any] = {
                    "id": getattr(hit, "id", None),
                    "score": getattr(hit, "score", 0.0),
                    "content": payload.get("content", ""),
                    "metadata": payload.get("metadata", {}),
                    "source": payload.get("source", ""),
                    "page_number": payload.get("page_number"),
                    "chunk_index": payload.get("chunk_index", 0),
                }
                results.append(result)
            
            return results
        except Exception as e:
            raise Exception(f"Failed to search similar chunks: {str(e)}")
    
    def delete_document_chunks(self, source: str) -> bool:
        """Delete all chunks for a specific document source."""
        try:
            # Create filter for the source
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            )
            
            # Delete points matching the filter
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=query_filter
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete document chunks: {str(e)}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection."""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            size_val: Optional[int] = None
            try:
                vectors_cfg = collection_info.config.params.vectors
                if isinstance(vectors_cfg, dict):
                    raw_size = vectors_cfg.get("size")
                    if isinstance(raw_size, int):
                        size_val = raw_size
                    elif isinstance(raw_size, (str, bytes)):
                        try:
                            size_val = int(raw_size)
                        except Exception:
                            size_val = None
                else:
                    s = getattr(vectors_cfg, "size", None)
                    if isinstance(s, int):
                        size_val = s
            except Exception:
                size_val = None

            return {
                "name": size_val,
                "vectors_count": getattr(collection_info, "vectors_count", 0),
                "indexed_vectors_count": getattr(collection_info, "indexed_vectors_count", 0),
                "points_count": getattr(collection_info, "points_count", 0),
                "segments_count": getattr(collection_info, "segments_count", 0),
                "status": getattr(collection_info, "status", None),
            }
        except Exception as e:
            raise Exception(f"Failed to get collection info: {str(e)}")
    
    def clear_collection(self) -> bool:
        """Clear all data from the collection."""
        try:
            self.qdrant_client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            return True
        except Exception as e:
            raise Exception(f"Failed to clear collection: {str(e)}")
