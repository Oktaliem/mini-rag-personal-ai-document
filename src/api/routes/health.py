"""
Health check and system information API routes.

This module contains health check and system information endpoints.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from ...core.rag import RAGCore
from ...api.dependencies import get_rag_core

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(rag_core: RAGCore = Depends(get_rag_core)) -> dict:
    """Health check endpoint."""
    return rag_core.get_system_health()


@router.get("/api-info")
async def api_info() -> dict:
    """API information endpoint."""
    return {
        "message": "Mini RAG API",
        "version": "2.0.0",
        "docs_endpoint": "/api-docs",
        "health_endpoint": "/health"
    }


@router.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Root endpoint - serve the web UI."""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Mini RAG API</h1><p>Web UI not found. Please check the templates directory.</p>",
            status_code=404
        )


@router.get("/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    """Login page endpoint."""
    try:
        with open("templates/login.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Login</h1><p>Login page not found. Please check the templates directory.</p>",
            status_code=404
        )
