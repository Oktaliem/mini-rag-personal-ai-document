import pytest
from unittest.mock import MagicMock

from src.core.rag import RAGCore
from src.core.config import settings


def _make_core() -> RAGCore:
    # RAGCore requires a qdrant client instance; a simple mock is sufficient for validator tests
    qdrant_mock = MagicMock()
    return RAGCore(qdrant_mock)


class TestRAGCoreValidators:
    def test_validate_query_empty(self):
        core = _make_core()
        result = core.validate_query("")
        assert result["status"] == "error"
        assert "empty" in result["message"].lower()

    def test_validate_query_too_short(self):
        core = _make_core()
        result = core.validate_query("hi")
        assert result["status"] == "error"
        assert "short" in result["message"].lower()

    def test_validate_query_too_long(self):
        core = _make_core()
        result = core.validate_query("a" * 1001)
        assert result["status"] == "error"
        assert "long" in result["message"].lower()

    def test_validate_query_ok(self):
        core = _make_core()
        result = core.validate_query("hello world")
        assert result["status"] == "success"

    def test_validate_top_k_none_uses_default(self):
        core = _make_core()
        result = core.validate_top_k(None)
        assert result["status"] == "success"
        assert result["top_k"] == settings.top_k

    @pytest.mark.parametrize("value,ok", [(1, True), (6, True), (0, False), (51, False)])
    def test_validate_top_k_bounds(self, value: int, ok: bool):
        core = _make_core()
        result = core.validate_top_k(value)
        if ok:
            assert result["status"] == "success"
            assert result["top_k"] == value
        else:
            assert result["status"] == "error"

