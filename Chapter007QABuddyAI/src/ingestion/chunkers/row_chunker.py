"""
QABuddy.ai — Row Chunker
Handles row-level chunking for test cases from CSV/XLSX files.
Each test case row is already a self-contained chunk — no splitting needed.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Chunk:
    """A single chunk ready for embedding."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def chunk_test_case_rows(parsed_test_cases: list) -> List[Chunk]:
    """
    Convert parsed test case rows into chunks.
    Each row is one chunk — test cases are atomic units.

    Args:
        parsed_test_cases: List of ParsedTestCase objects

    Returns:
        List of Chunk objects ready for embedding
    """
    chunks = []

    for tc in parsed_test_cases:
        chunk = Chunk(
            content=tc.content,
            metadata={
                **tc.metadata,
                "source_file": tc.file_path,
                "language": "csv",
                "unit_type": "test_case",
                "unit_name": tc.test_id,
                "row_index": tc.row_index,
                "chunk_index": 0,
                "total_chunks": 1,
                "title": f"Test Case {tc.test_id}",
            },
        )
        chunks.append(chunk)

    logger.info(f"Created {len(chunks)} test case chunks from {len(parsed_test_cases)} rows")
    return chunks
