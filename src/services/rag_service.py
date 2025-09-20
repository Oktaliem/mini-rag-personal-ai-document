"""
RAG (Retrieval-Augmented Generation) service.

This service handles embedding generation, vector search, and answer generation.
"""

import json
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Iterable
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from ..core.config import settings
from .embedding_service import EmbeddingService
from .document_service import DocumentService


class RAGService:
    """Service for RAG operations including embedding, search, and generation."""
    
    def __init__(self, qdrant_client: QdrantClient) -> None:
        self.qdrant_client = qdrant_client
        self.embedding_service = EmbeddingService(settings, qdrant_client)
        self.document_service = DocumentService()
        self.collection_name = settings.qdrant_collection
        self.top_k = settings.top_k
    
    def ensure_collection(self, dim: int, clear: bool = False) -> None:
        """Ensure the collection exists and has the right schema."""
        try:
            existing = {c.name for c in self.qdrant_client.get_collections().collections}
            if self.collection_name in existing and clear:
                self.qdrant_client.delete_collection(self.collection_name)
                existing.remove(self.collection_name)
            
            if self.collection_name not in existing:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
                )
                print(f"Created collection: {self.collection_name}")
            else:
                print(f"Using existing collection: {self.collection_name}")
        except Exception as e:
            print(f"Collection setup error: {e}")
            raise
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            raise ValueError("need at least one array to concatenate")
        
        embeddings: List[List[float]] = []
        for text in texts:
            embedding = self.embedding_service.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def index_documents(self, datapath: str, clear: bool = False) -> Dict[str, Any]:
        """Index documents from a directory into the vector database."""
        # Read documents
        docs = self.document_service.read_docs(datapath)
        if not docs:
            return {"indexed": 0, "message": f"No indexable docs under {datapath}"}
        
        # Clear collection if requested
        if clear:
            self.ensure_collection(768, clear=True)
            return {"indexed": 0, "message": "All data cleared"}
        else:
            self.ensure_collection(768)
        
        # Process documents
        all_chunks = []
        for doc in docs:
            chunks = self.document_service.chunk_words(doc["text"])
            for chunk_text in chunks:
                all_chunks.append({
                    "text": chunk_text,
                    "doc_path": doc["doc_path"],
                    "mtime": doc["mtime"]
                })
        
        if not all_chunks:
            return {"indexed": 0, "message": f"No text chunks created from {datapath}"}
        
        # Generate embeddings
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = self.embed_batch(texts)
        
        # Prepare points for Qdrant
        points: List[PointStruct] = []
        for i, (chunk, embedding) in enumerate(zip(all_chunks, embeddings)):
            point_id = self.document_service.sha1_u64(chunk["text"])
            # Ensure embedding is a List[float] for Qdrant client
            vector_list: List[float] = list(map(float, embedding))
            points.append(PointStruct(
                id=point_id,
                vector=vector_list,
                payload={
                    "text": chunk["text"],
                    "doc_path": chunk["doc_path"],
                    "mtime": chunk["mtime"]
                }
            ))
        
        # Upsert to Qdrant
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return {
            "indexed": len(points),
            "message": f"Indexed {len(points)} chunks in Qdrant"
        }
    
    def search_similar_chunks(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        if top_k is None:
            top_k = self.top_k
        
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Format results
        results: List[Dict[str, Any]] = []
        for result in search_results:
            payload = getattr(result, "payload", {}) or {}
            text_val = payload.get("text", "")
            doc_path_val = payload.get("doc_path", "")
            score_val = getattr(result, "score", 0.0)
            results.append({
                "text": text_val,
                "doc_path": doc_path_val,
                "score": score_val,
            })
        
        return results
    
    def generate_answer(self, query: str, context_blocks: List[Dict[str, Any]]) -> str:
        """Generate an answer using the LLM with context."""
        if not context_blocks:
            return "I don't have enough information to answer your question. Please upload some documents first."
        
        # Prepare context
        context_text = "\n\n".join([block["text"] for block in context_blocks])
        
        # Prepare prompt
        prompt = f"""Context:
{context_text}

Question: {query}

Answer:"""
        
        # Call Ollama
        response = requests.post(
            f"{settings.ollama_url}/api/generate",
            json={
                "model": settings.gen_model,
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "Sorry, I couldn't generate an answer.")
    
    def stream_answer(self, query: str, context_blocks: List[Dict[str, Any]]) -> Iterable[bytes]:
        """Stream an answer using the LLM with context."""
        print(f"DEBUG: stream_answer called with query: {query}, context_blocks: {len(context_blocks)}")
        if not context_blocks:
            print("DEBUG: No context blocks, yielding no info message")
            yield b"I don't have enough information to answer your question. Please upload some documents first."
            return
        
        # Format context more naturally (matching original implementation)
        context_parts = []
        for i, block in enumerate(context_blocks):
            source_info = f"From {block['doc_path']}: " if 'doc_path' in block else ""
            context_parts.append(f"{source_info}{block['text']}")
        ctx_str = "\n\n".join(context_parts)
        
        # System prompt (matching original)
        sys_prompt = (
            "You are a helpful, knowledgeable assistant. Answer questions naturally and conversationally, primarily using the information provided in the context. "
            "Write in a clear, human-friendly style that's easy to read and understand. "
            "When the context contains relevant information, use it to provide comprehensive answers. "
            "If asked to create tables or lists, you can do so when it helps organize information clearly. "
            "If the answer is not in the context, you can still provide helpful general knowledge or explain what you know about the topic. "
            "When referencing information, mention the source naturally in your response (e.g., 'According to the document...' or 'The source mentions...'). "
            "Be helpful and informative while staying conversational and natural."
        )
        
        # Prepare prompt (matching original format)
        prompt = (
            f"{sys_prompt}\n\nContext:\n{ctx_str}\n\n"
            f"Question: {query}\n"
            f"Please provide a helpful and informative answer:"
        )
        
        # Call Ollama with streaming (matching original implementation)
        print(f"DEBUG: Making request to Ollama at {settings.ollama_url}/api/generate")
        print(f"DEBUG: Using model: {settings.gen_model}")
        with requests.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": settings.gen_model, "prompt": prompt, "stream": True},
            stream=True,
        ) as resp:
            print(f"DEBUG: Ollama response status: {resp.status_code}")
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    print(f"DEBUG: Parsed JSON: {obj}")
                    if "response" in obj and obj["response"]:
                        print(f"DEBUG: Yielding response: {obj['response']}")
                        yield obj["response"].encode("utf-8")
                    if obj.get("done"):
                        print("DEBUG: Stream done, breaking")
                        break
                except Exception as e:
                    print(f"Error processing stream line: {e}")
                    continue
    
    def ask_question(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Ask a question and get an answer with sources."""
        # Search for relevant chunks
        similar_chunks = self.search_similar_chunks(query, top_k)
        
        # Generate answer
        answer = self.generate_answer(query, similar_chunks)
        
        # Prepare sources
        sources = [{"doc_path": chunk["doc_path"], "preview": chunk["text"][:120]} for chunk in similar_chunks]
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    def ask_question_stream(self, query: str, top_k: Optional[int] = None) -> Iterable[bytes]:
        """Ask a question and stream the answer."""
        print(f"DEBUG: ask_question_stream called with query: {query}, top_k: {top_k}")
        # Search for relevant chunks
        similar_chunks = self.search_similar_chunks(query, top_k)
        print(f"DEBUG: found {len(similar_chunks)} similar chunks")
        
        # Stream answer
        for chunk in self.stream_answer(query, similar_chunks):
            print(f"DEBUG: yielding chunk: {chunk!r}")
            yield chunk
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        try:
            collections = self.qdrant_client.get_collections()
            collection_info = None
            
            for collection in collections.collections:
                if collection.name == self.collection_name:
                    collection_info = collection
                    break
            
            if collection_info:
                # Get points count
                points_count = self.qdrant_client.count(self.collection_name)
                return {
                    "collection_name": self.collection_name,
                    "points_count": points_count.count,
                    "status": "active"
                }
            else:
                return {
                    "collection_name": self.collection_name,
                    "points_count": 0,
                    "status": "not_found"
                }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "points_count": 0,
                "status": f"error: {str(e)}"
            }
