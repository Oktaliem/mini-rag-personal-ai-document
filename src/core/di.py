"""
Simple dependency injection provider for application services.

This module offers a minimal container to register and resolve
singleton dependencies in a test-friendly way.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, TypeVar, Any

from .config import settings

T = TypeVar("T")


class Provider:
    """A tiny DI provider supporting lazy singletons and overrides."""

    def __init__(self) -> None:
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}

    def register_singleton(self, key: str, factory: Callable[[], T]) -> None:
        self._factories[key] = factory

    def set_instance(self, key: str, instance: Any) -> None:
        self._singletons[key] = instance

    def get(self, key: str) -> Any:
        if key in self._singletons:
            return self._singletons[key]
        factory = self._factories.get(key)
        if factory is None:
            raise KeyError(f"No factory registered for dependency '{key}'")
        instance = factory()
        self._singletons[key] = instance
        return instance


_provider: Optional[Provider] = None


def get_provider() -> Provider:
    global _provider
    if _provider is None:
        _provider = Provider()
        _register_defaults(_provider)
    return _provider


def reset_provider() -> None:
    """Reset the global provider (useful in tests)."""
    global _provider
    _provider = None


def _register_defaults(provider: Provider) -> None:
    """Register default application dependencies."""
    from qdrant_client import QdrantClient
    from .rag import RAGCore

    provider.register_singleton(
        "qdrant_client",
        lambda: QdrantClient(settings.qdrant_url, timeout=60),
    )

    def _rag_core_factory() -> RAGCore:
        qclient = provider.get("qdrant_client")
        return RAGCore(qclient)

    provider.register_singleton("rag_core", _rag_core_factory)


# Convenience typed getters
def provide_qdrant_client() -> Any:
    return get_provider().get("qdrant_client")


def provide_rag_core() -> Any:
    return get_provider().get("rag_core")


