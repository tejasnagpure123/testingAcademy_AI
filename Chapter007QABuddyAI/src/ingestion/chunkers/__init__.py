"""
QABuddy.ai — Chunkers Package
Exports the shared Chunk base class. Chunking functions use lazy imports
to avoid loading tiktoken at package import time during test collection.

To use a chunker, import it directly:
    from src.ingestion.chunkers.code_chunker import chunk_code_units
    from src.ingestion.chunkers.base import Chunk
"""

# Only import the lightweight base class eagerly — it has no external deps.
from src.ingestion.chunkers.base import Chunk

__all__ = [
    "Chunk",
    "chunk_code_units",
    "chunk_test_case_rows",
    "chunk_jira_tickets",
    "chunk_text_sections",
    "chunk_log_blocks",
    "CHUNK_PROFILES",
]

