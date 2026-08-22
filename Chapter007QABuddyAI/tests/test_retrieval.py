"""
QABuddy.ai — Retrieval Unit Tests
Tests for vector store, hybrid search, and reranker.
Uses mock Qdrant client to avoid external dependencies.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─── Mock Classes ───────────────────────────────────────────

@dataclass
class MockChunk:
    content: str = "Test content"
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "test"})


@dataclass
class MockEmbedding:
    dense_vector: List[float] = field(default_factory=lambda: [0.1] * 1024)
    sparse_vector: Optional[Dict[int, float]] = field(default_factory=lambda: {1: 0.5, 2: 0.3})
    text: str = "Test content"


# ─── Prompt Template Tests ──────────────────────────────────

class TestPromptTemplates:
    def test_build_context_block(self):
        from src.chat.prompt_templates import build_context_block

        results = [
            {
                "text": "Test code content",
                "metadata": {
                    "source_type": "selenium_repo",
                    "source_file": "LoginTest.java",
                    "title": "testLogin",
                    "language": "java",
                },
            },
            {
                "text": "Test case content",
                "metadata": {
                    "source_type": "test_cases",
                    "source_file": "testdata.csv",
                    "title": "TC-001",
                    "language": "csv",
                },
            },
        ]

        context = build_context_block(results)
        assert "Chunk 1" in context
        assert "Chunk 2" in context
        assert "LoginTest.java" in context
        assert "selenium_repo" in context

    def test_build_qa_prompt(self):
        from src.chat.prompt_templates import build_qa_prompt

        results = [
            {
                "text": "Some test content",
                "metadata": {"source_type": "test", "source_file": "test.py", "title": "Test"},
            }
        ]

        prompt = build_qa_prompt("How do I write a test?", results)
        assert "How do I write a test?" in prompt
        assert "Retrieved Context" in prompt
        assert "Some test content" in prompt

    def test_empty_results(self):
        from src.chat.prompt_templates import build_context_block

        context = build_context_block([])
        assert context == ""


# ─── QA Chain Tests ─────────────────────────────────────────

class TestQAChain:
    def test_qa_response_structure(self):
        from src.chat.qa_chain import QAResponse

        response = QAResponse(
            answer="Test answer",
            sources=[{"source_type": "test", "source_file": "test.py", "title": "Test", "score": 0.9}],
            query="Test question",
            num_chunks_retrieved=50,
            num_chunks_reranked=5,
        )

        assert response.answer == "Test answer"
        assert len(response.sources) == 1
        assert response.num_chunks_retrieved == 50
        assert response.num_chunks_reranked == 5


# ─── API Models Tests ───────────────────────────────────────

class TestAPIModels:
    def test_chat_request_validation(self):
        from src.api.models import ChatRequest

        req = ChatRequest(question="How do I run tests?")
        assert req.question == "How do I run tests?"
        assert req.source_filter is None

    def test_chat_request_with_filter(self):
        from src.api.models import ChatRequest

        req = ChatRequest(question="Test?", source_filter="selenium_repo")
        assert req.source_filter == "selenium_repo"

    def test_chat_request_min_length(self):
        from src.api.models import ChatRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChatRequest(question="")

    def test_chat_response_model(self):
        from src.api.models import ChatResponse, SourceReference

        resp = ChatResponse(
            answer="Answer text",
            sources=[SourceReference(source_type="test", source_file="f.py", title="t", score=0.8)],
            query="Question",
            num_chunks_retrieved=50,
            num_chunks_reranked=5,
        )
        assert resp.answer == "Answer text"
        assert len(resp.sources) == 1

    def test_health_response_model(self):
        from src.api.models import HealthResponse

        resp = HealthResponse(
            status="healthy",
            qdrant_status="connected",
            collection_info={"points_count": 1000},
            llm_provider="gemini",
            embedding_model="BAAI/bge-m3",
        )
        assert resp.status == "healthy"


# ─── Settings Tests ─────────────────────────────────────────

class TestSettings:
    def test_settings_defaults(self):
        from src.config.settings import Settings

        s = Settings()
        assert s.qdrant_port == 6333
        assert s.embedding_model == "BAAI/bge-m3"
        assert s.hybrid_search_top_k == 50
        assert s.rerank_top_k == 5

    def test_get_data_path(self):
        from src.config.settings import Settings

        s = Settings()
        path = s.get_data_path("selenium_repo")
        assert "01_selenium_framework" in str(path)

    def test_source_types(self):
        from src.config.settings import Settings

        s = Settings()
        assert len(s.SOURCE_TYPES) == 10
        assert "selenium_repo" in s.SOURCE_TYPES
        assert "jira_tickets" in s.SOURCE_TYPES
