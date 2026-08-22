"""
QABuddy.ai — Chunker Unit Tests
Tests for all source-specific chunkers.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.chunkers.code_chunker import chunk_code_units, Chunk
from src.ingestion.chunkers.row_chunker import chunk_test_case_rows
from src.ingestion.chunkers.ticket_chunker import chunk_jira_tickets
from src.ingestion.chunkers.recursive_chunker import chunk_text_sections, _recursive_split
from src.ingestion.chunkers.log_chunker import chunk_log_blocks


# ─── Mock Data Classes ──────────────────────────────────────

@dataclass
class MockCodeUnit:
    content: str
    file_path: str = "test/File.java"
    language: str = "java"
    unit_type: str = "method"
    unit_name: str = "testMethod"
    start_line: int = 1
    end_line: int = 10
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "selenium_repo"})


@dataclass
class MockTestCase:
    content: str = "Test ID: TC-001\nTitle: Login Test\nSteps: Open login page"
    file_path: str = "testdata.csv"
    row_index: int = 0
    test_id: str = "TC-001"
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "test_cases"})


@dataclass
class MockJiraTicket:
    content: str = "JIRA Ticket: QA-123\nSummary: Login button broken\nDescription: The login button fails on Chrome"
    ticket_key: str = "QA-123"
    summary: str = "Login button broken"
    status: str = "Open"
    priority: str = "High"
    ticket_type: str = "Bug"
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "jira_tickets"})


@dataclass
class MockTextSection:
    content: str = "This is a section about testing best practices."
    file_path: str = "docs/guide.md"
    section_index: int = 0
    section_title: str = "Testing Best Practices"
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "company_docs"})


@dataclass
class MockLogBlock:
    content: str = "Tests run: 10, Failures: 1\nFailed: LoginTest.testTimeout"
    file_path: str = "build_142.log"
    block_index: int = 0
    block_type: str = "test_result"
    metadata: Dict[str, Any] = field(default_factory=lambda: {"source_type": "jenkins_logs"})


# ─── Code Chunker Tests ─────────────────────────────────────

class TestCodeChunker:
    def test_single_method_fits_in_one_chunk(self):
        unit = MockCodeUnit(content="public void test() { assert true; }")
        chunks = chunk_code_units([unit])
        assert len(chunks) == 1
        assert "test" in chunks[0].content
        assert chunks[0].metadata["unit_type"] == "method"

    def test_multiple_units(self):
        units = [
            MockCodeUnit(content="public void test1() { }", unit_name="test1"),
            MockCodeUnit(content="public void test2() { }", unit_name="test2"),
        ]
        chunks = chunk_code_units(units)
        assert len(chunks) == 2

    def test_empty_input(self):
        chunks = chunk_code_units([])
        assert chunks == []

    def test_metadata_preserved(self):
        unit = MockCodeUnit(content="code")
        chunks = chunk_code_units([unit])
        assert chunks[0].metadata["source_type"] == "selenium_repo"
        assert chunks[0].metadata["language"] == "java"


# ─── Row Chunker Tests ──────────────────────────────────────

class TestRowChunker:
    def test_each_row_is_one_chunk(self):
        rows = [MockTestCase(test_id="TC-001"), MockTestCase(test_id="TC-002")]
        chunks = chunk_test_case_rows(rows)
        assert len(chunks) == 2
        assert chunks[0].metadata["unit_name"] == "TC-001"
        assert chunks[1].metadata["unit_name"] == "TC-002"

    def test_empty_input(self):
        assert chunk_test_case_rows([]) == []


# ─── Ticket Chunker Tests ───────────────────────────────────

class TestTicketChunker:
    def test_small_ticket_is_one_chunk(self):
        tickets = [MockJiraTicket()]
        chunks = chunk_jira_tickets(tickets)
        assert len(chunks) == 1
        assert chunks[0].metadata["ticket_key"] == "QA-123"

    def test_empty_input(self):
        assert chunk_jira_tickets([]) == []


# ─── Recursive Chunker Tests ────────────────────────────────

class TestRecursiveChunker:
    def test_short_section_no_split(self):
        sections = [MockTextSection(content="Short text.")]
        chunks = chunk_text_sections(sections, "company_docs")
        assert len(chunks) == 1

    def test_split_respects_boundaries(self):
        # Create text that's definitely longer than chunk size
        long_text = ("This is a paragraph about testing. " * 50 + "\n\n") * 10
        sections = [MockTextSection(content=long_text)]
        chunks = chunk_text_sections(sections, "company_docs", chunk_size=100)
        assert len(chunks) > 1

    def test_empty_input(self):
        assert chunk_text_sections([], "company_docs") == []

    def test_recursive_split_function(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        # With a very small target, should split
        chunks = _recursive_split(text, target_size=5, overlap=1)
        assert len(chunks) >= 2


# ─── Log Chunker Tests ──────────────────────────────────────

class TestLogChunker:
    def test_small_block_is_one_chunk(self):
        blocks = [MockLogBlock()]
        chunks = chunk_log_blocks(blocks)
        assert len(chunks) == 1
        assert chunks[0].metadata["unit_type"] == "test_result"

    def test_empty_input(self):
        assert chunk_log_blocks([]) == []
