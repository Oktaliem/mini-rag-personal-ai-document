"""
Main application entry point for Mini RAG API.

This module creates and configures the FastAPI application with all routes and middleware.
"""

from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import HTTPBearer
from typing import List, Dict, Any, Optional, Iterable
from pathlib import Path
from pydantic import BaseModel, Field
import json
import hashlib
import requests
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from .core.config import settings
from .api.dependencies import get_qdrant_client, get_rag_core
from .core.di import provide_qdrant_client, provide_rag_core
from .core.models import User

# Constants from original implementation
TOP_K = settings.top_k
COLLECTION = settings.qdrant_collection

# Security scheme
security = HTTPBearer(auto_error=False)

# Request models
class LoginRequest(BaseModel):
    username: str
    password: str

class AskRequest(BaseModel):
    query: str = Field(..., description="User question")
    top_k: Optional[int] = Field(None, description="How many chunks to retrieve")

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]] = Field(default_factory=list)

# Simple authentication for legacy compatibility
async def get_current_active_user(credentials = Depends(security)) -> User:
    """Get current authenticated user - requires authentication."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401, 
            detail="unauthorized: Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Import JWT validation from the original auth module
        from .core.auth import get_current_user_from_token
        user = get_current_user_from_token(credentials.credentials)
        if not user:
            raise HTTPException(status_code=401, detail="unauthorized: Could not validate credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="unauthorized: Could not validate credentials")

# Utility functions (from original implementation)
def sha1_u64(s: str) -> int:
    h = hashlib.sha1(s.encode("utf-8", errors="ignore")).digest()
    return int.from_bytes(h[:8], "big", signed=False)

def embed_ollama(text: str) -> np.ndarray:
    r = requests.post(f"{settings.ollama_url}/api/embeddings", json={"model": settings.emb_model, "prompt": text})
    r.raise_for_status()
    v = np.array(r.json()["embedding"], dtype="float32")
    v /= (np.linalg.norm(v) + 1e-12)  # cosine norm
    return v

# System prompt (from original implementation)
SYS = (
    "You are a helpful, knowledgeable assistant. Answer questions naturally and conversationally, primarily using the information provided in the context. "
    "Write in a clear, human-friendly style that's easy to read and understand. "
    "When the context contains relevant information, use it to provide comprehensive answers. "
    "If asked to create tables or lists, you can do so when it helps organize information clearly. "
    "If the answer is not in the context, you can still provide helpful general knowledge or explain what you know about the topic. "
    "When referencing information, mention the source naturally in your response (e.g., 'According to the document...' or 'The source mentions...'). "
    "Be helpful and informative while staying conversational and natural."
)

def stream_answer(query: str, ctx_blocks: List[Dict[str, Any]]) -> Iterable[bytes]:
    """Yields text chunks from Ollama's streaming API (exact original implementation)."""
    # Format context more naturally
    context_parts = []
    for i, block in enumerate(ctx_blocks):
        source_info = f"From {block['doc_path']}: " if 'doc_path' in block else ""
        context_parts.append(f"{source_info}{block['text']}")
    ctx_str = "\n\n".join(context_parts)
    prompt = (
        f"{SYS}\n\nContext:\n{ctx_str}\n\n"
        f"Question: {query}\n"
        f"Please provide a helpful and informative answer:"
    )
    with requests.post(
        f"{settings.ollama_url}/api/generate",
        json={"model": settings.gen_model, "prompt": prompt, "stream": True},
        stream=True,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "response" in obj and obj["response"]:
                    yield obj["response"].encode("utf-8")
                if obj.get("done"):
                    break
            except json.JSONDecodeError:
                continue

# Optional authentication for endpoints that should work without auth
async def get_current_user_optional(credentials = Depends(security)):
    """Get current user if authenticated, otherwise return default user."""
    if not credentials:
        return User(username="admin", role="admin", is_active=True)
    
    # For legacy compatibility, accept any valid token format
    return User(username="admin", role="admin", is_active=True)

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Mini RAG API - AI Document Assistant",
    docs_url=None,  # Disable default /docs
    redoc_url=None,  # Disable default /redoc
    openapi_url=None  # Disable default /openapi.json
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
_qdrant_client = None
_rag_core = None

def get_qdrant_client():
    """Get Qdrant client."""
    try:
        return provide_qdrant_client()
    except Exception:
        global _qdrant_client
        if _qdrant_client is None:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(settings.qdrant_url, timeout=60)
        return _qdrant_client

def get_rag_core():
    """Get RAG core."""
    try:
        return provide_rag_core()
    except Exception:
        global _rag_core
        if _rag_core is None:
            from .core.rag import RAGCore
            _rag_core = RAGCore(get_qdrant_client())
        return _rag_core

# Legacy endpoints for backward compatibility
@app.post("/upsert")
async def upsert_legacy(request: dict, current_user: User = Depends(get_current_active_user)):
    """Legacy upsert endpoint."""
    rag_core = get_rag_core()
    path = request.get("path")
    clear = request.get("clear", False)
    result = rag_core.index_documents(path, clear=clear)
    return result

@app.post("/ask")
async def ask_legacy(request: dict, current_user: User = Depends(get_current_active_user)):
    """Legacy ask endpoint."""
    rag_core = get_rag_core()
    query = request.get("query") or request.get("question", "")
    top_k = request.get("top_k")
    result = rag_core.ask_question(query, top_k)
    return result

@app.post("/ask/stream")
def ask_stream(req: AskRequest, current_user: User = Depends(get_current_active_user)):
    """Streaming ask endpoint (exact original implementation)."""
    k = req.top_k or TOP_K
    
    try:
        # Check if we have documents
        qclient = get_qdrant_client()
        collection_info = qclient.get_collection(COLLECTION)
        if collection_info.points_count == 0:
            def _noidx():
                yield b"No documents indexed. Use /upsert to index documents first."
            return StreamingResponse(_noidx(), media_type="text/plain")
    except Exception as e:
        error_msg = str(e)
        def _error():
            yield f"Database error: {error_msg}".encode("utf-8")
        return StreamingResponse(_error(), media_type="text/plain")

    # Embed the query
    try:
        query_emb = embed_ollama(req.query)
    except Exception as e:
        error_msg = str(e)
        def _error():
            yield f"Embedding failed: {error_msg}".encode("utf-8")
        return StreamingResponse(_error(), media_type="text/plain")

    # Search in Qdrant
    try:
        search_results = qclient.search(
            collection_name=COLLECTION,
            query_vector=query_emb.tolist(),
            limit=k,
            with_payload=True
        )
    except Exception as e:
        error_msg = str(e)
        def _error():
            yield f"Search failed: {error_msg}".encode("utf-8")
        return StreamingResponse(_error(), media_type="text/plain")

    if not search_results:
        def _noidx():
            yield b"No relevant information found."
        return StreamingResponse(_noidx(), media_type="text/plain")

    # Extract relevant chunks
    relevant_chunks = []
    for result in search_results:
        chunk = {
            "text": result.payload.get("text", ""),
            "doc_path": result.payload.get("doc_path", "unknown")
        }
        # Add chunk_index if it exists
        if "chunk_index" in result.payload:
            chunk["chunk_index"] = result.payload["chunk_index"]
        relevant_chunks.append(chunk)

    # Ensure the body is an iterator even if mocked as a list in tests
    body_iter = stream_answer(req.query, relevant_chunks)
    return StreamingResponse(iter(body_iter), media_type="text/plain")

@app.post("/files")
async def upload_files_legacy(background: BackgroundTasks, files: List[UploadFile] = File(...), current_user: User = Depends(get_current_active_user)):
    """Legacy file upload endpoint."""
    # Validate file extensions at endpoint level
    ALLOWED_EXTS = {".pdf", ".md", ".txt"}
    saved = []
    
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")
        
        # Save file
        dest = Path(settings.docs_dir) / file.filename
        dest.parent.mkdir(exist_ok=True)
        with dest.open("wb") as out:
            out.write(await file.read())
        saved.append(str(dest))
    
    # Index the uploaded files in the background
    def _bg_index(paths: List[str]):
        try:
            rag_core = get_rag_core()
            rag_core.index_documents(",".join(paths), clear=False)
        except Exception as e:
            print(f"Background indexing failed: {e}")
    
    background.add_task(_bg_index, saved)
    return {"saved": saved, "message": "Files uploaded. Indexing has started."}

@app.get("/models")
async def get_models_legacy():
    """Legacy models endpoint."""
    try:
        import requests
        response = requests.get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
        models_data = response.json()
        
        # Filter for text generation models (exclude embedding models)
        text_models = []
        for model in models_data.get("models", []):
            model_name = model.get("name", "")
            # Exclude embedding models and include common text generation models
            if not any(embed in model_name.lower() for embed in ["embed", "embedding"]):
                text_models.append({
                    "name": model_name,
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                    "details": model.get("details", {})
                })
        
        return {
            "available_models": text_models,
            "current_model": settings.gen_model,
            "embedding_model": settings.emb_model
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch models: {str(e)}",
            "available_models": [],
            "current_model": settings.gen_model,
            "embedding_model": settings.emb_model
        }

@app.post("/models/change")
async def change_model_legacy(request: dict, current_user: User = Depends(get_current_active_user)):
    """Legacy model change endpoint."""
    model = request.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Model name required")
    
    try:
        import requests
        # Verify the model exists by checking Ollama
        response = requests.get(f"{settings.ollama_url}/api/tags")
        response.raise_for_status()
        models_data = response.json()
        
        available_models = [model_item.get("name", "") for model_item in models_data.get("models", [])]
        
        if model not in available_models:
            raise HTTPException(
                status_code=400, 
                detail=f"Model '{model}' not found. Available models: {available_models}"
            )
        
        # Update the settings (in a real implementation, you'd persist this)
        settings.gen_model = model
        
        return {
            "message": f"Model changed to {model}",
            "current_model": model,
            "success": True
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to change model: {str(e)}")

# Authentication endpoints
@app.post("/auth/login")
async def login_legacy(request: LoginRequest):
    """Legacy login endpoint."""
    from .core.auth import authenticate_user, create_access_token
    
    user = authenticate_user(request.username, request.password)
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@app.post("/auth/logout")
async def logout_legacy(request: Request):
    """Legacy logout endpoint."""
    from fastapi.security.utils import get_authorization_scheme_param
    from .core.auth import blacklist_token
    
    # Extract token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer" and token:
            # Blacklist the token
            blacklist_token(token)
            return {"message": "Logged out successfully", "token_blacklisted": True}
    
    return {"message": "Logged out successfully", "token_blacklisted": False}

@app.get("/auth/me")
async def get_current_user_legacy(current_user: User = Depends(get_current_active_user)):
    """Legacy get current user endpoint."""
    return current_user

@app.post("/auth/register")
async def register_legacy(request: dict):
    """Legacy register endpoint."""
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    rag_core = get_rag_core()
    return rag_core.get_system_health()

# API info endpoint
@app.get("/api-info")
async def api_info():
    """API information endpoint."""
    return {
        "message": "Mini RAG API with Qdrant",
        "docs": "/docs",
        "health": "/health",
        "web_ui": "/",
        "mode": "qdrant vector database (persistent)"
    }

# API docs endpoint
@app.get("/api-docs", response_class=HTMLResponse)
async def get_protected_docs(token: str = None):
    """Protected API documentation - requires authentication"""
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.openapi.utils import get_openapi
    from fastapi import HTTPException
    
    try:
        # Validate token and get user
        from .core.auth import get_current_active_user_from_token
        current_user = await get_current_active_user_from_token(token)
    except HTTPException as e:
        # If authentication fails, return an error page instead of redirecting
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Required - Mini RAG API</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #e53e3e; background: #fed7d7; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 500px; }}
                .info {{ color: #2b6cb0; background: #bee3f8; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 500px; }}
            </style>
        </head>
        <body>
            <h1>🔒 Authentication Required</h1>
            <div class="error">
                <h2>Access Denied</h2>
                <p>{e.detail}</p>
            </div>
            <div class="info">
                <h3>How to Access API Documentation:</h3>
                <ol style="text-align: left; display: inline-block;">
                    <li>Go to the <a href="/">Mini RAG Web UI</a></li>
                    <li>Login with your credentials</li>
                    <li>Click the "Open API Docs" button</li>
                </ol>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=401)
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="Mini RAG API - Protected Documentation",
        routes=app.routes,
    )
    
    # Create custom Swagger UI HTML with proper token handling
    swagger_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>{app.title} - API Docs</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '/openapi.json?token={token}',
            dom_id: '#swagger-ui',
            layout: 'BaseLayout',
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            requestInterceptor: (request) => {{
                // Add token to all API requests
                if (request.url && !request.url.includes('token=')) {{
                    request.url = request.url + (request.url.includes('?') ? '&' : '?') + 'token={token}';
                }}
                return request;
            }}
        }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=swagger_html)

# Protected OpenAPI JSON endpoint
@app.get("/openapi.json")
async def get_openapi_json(token: str = None):
    """Protected OpenAPI JSON - requires authentication"""
    from fastapi.openapi.utils import get_openapi
    from fastapi import HTTPException
    
    try:
        # Validate token and get user
        from .core.auth import get_current_active_user_from_token
        current_user = await get_current_active_user_from_token(token)
    except HTTPException as e:
        # Return JSON error response for API calls
        raise HTTPException(status_code=401, detail=e.detail)
    
    return get_openapi(
        title=app.title,
        version=app.version,
        description="Mini RAG API - Protected Documentation",
        routes=app.routes,
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return {"message": "Mini RAG API", "version": settings.app_version}

# Login page endpoint
@app.get("/login")
async def login_page():
    """Login page endpoint."""
    try:
        with open("templates/login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Login</h1><p>Login page not found.</p>")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Initialize services
    qdrant_client = get_qdrant_client()
    rag_core = get_rag_core()
    
    # Ensure collection exists
    rag_core.initialize_collection()
    
    print(f"🚀 {settings.app_name} v{settings.app_version} started successfully!")
    print(f"📚 Documents directory: {settings.docs_dir}")
    print(f"🔍 Qdrant URL: {settings.qdrant_url}")
    print(f"🤖 Ollama URL: {settings.ollama_url}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 Mini RAG API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )