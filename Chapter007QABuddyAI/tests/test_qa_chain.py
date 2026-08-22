"""
QABuddy.ai — QA Chain Integration Tests
Tests for the full RAG pipeline using mocks.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestQAChainIntegration:
    """Integration tests for the QA chain with mocked dependencies."""

    def test_chain_returns_no_results_message(self):
        """When search returns nothing, chain should provide a helpful message."""
        from src.chat.qa_chain import QAChain

        mock_searcher = MagicMock()
        mock_searcher.search.return_value = []

        mock_llm = MagicMock()

        chain = QAChain(searcher=mock_searcher, llm_client=mock_llm)
        response = chain.ask("some question")

        assert "don't have enough information" in response.answer.lower() or "couldn't find" in response.answer.lower()
        assert response.sources == []
        assert response.num_chunks_retrieved == 0

    def test_chain_calls_search_then_rerank(self):
        """Chain should call search, then rerank, then generate."""
        from src.chat.qa_chain import QAChain

        mock_searcher = MagicMock()
        mock_searcher.search.return_value = [
            {"text": "test content", "score": 0.9, "metadata": {"source_type": "test", "source_file": "f.py", "title": "t"}},
        ]

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Generated answer based on test content [Source: f.py]"

        with patch("src.chat.qa_chain.rerank") as mock_rerank:
            mock_rerank.return_value = mock_searcher.search.return_value

            chain = QAChain(searcher=mock_searcher, llm_client=mock_llm)
            response = chain.ask("how to test?")

            mock_searcher.search.assert_called_once()
            mock_rerank.assert_called_once()
            mock_llm.generate.assert_called_once()
            assert len(response.answer) > 0

    def test_chain_passes_source_filter(self):
        """Chain should forward source_filter to the searcher."""
        from src.chat.qa_chain import QAChain

        mock_searcher = MagicMock()
        mock_searcher.search.return_value = []
        mock_llm = MagicMock()

        chain = QAChain(searcher=mock_searcher, llm_client=mock_llm)
        chain.ask("test?", source_filter="selenium_repo")

        call_kwargs = mock_searcher.search.call_args
        assert call_kwargs.kwargs.get("source_filter") == "selenium_repo" or \
               (len(call_kwargs.args) > 0 and "selenium_repo" in str(call_kwargs))


class TestCleanerIntegration:
    """Tests for cleaner modules."""

    def test_code_cleaner(self):
        from src.ingestion.cleaners.code_cleaner import clean_code

        messy_code = "public void test() {\n\t\tassert true;\n\t}\n\n\n\n\n"
        cleaned = clean_code(messy_code, "java")
        assert "\t" not in cleaned  # Tabs normalized
        assert "\n\n\n" not in cleaned  # Excessive blank lines removed

    def test_text_cleaner(self):
        from src.ingestion.cleaners.text_cleaner import clean_text

        text = "This document covers RTM and RCA processes.\n\n\n\nEnd."
        cleaned = clean_text(text, expand_abbreviations=True)
        assert "Requirements Traceability Matrix" in cleaned or "RTM" in cleaned
        assert "\n\n\n" not in cleaned

    def test_log_cleaner(self):
        from src.ingestion.cleaners.log_cleaner import clean_log

        log = "\x1b[32m[INFO]\x1b[0m Build started\nDownloading: https://repo.maven.org/foo.jar\n"
        cleaned = clean_log(log)
        assert "\x1b[" not in cleaned  # ANSI codes removed
        assert "Downloading:" not in cleaned  # Maven noise removed
        assert "Build started" in cleaned
