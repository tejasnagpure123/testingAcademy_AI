"""
QABuddy.ai — Code Chunker
Chunks parsed code units. Since the code parser already splits by class/method,
the chunker's job is to handle oversized units (split further) and add context headers.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:
        return len(text.split())  # Rough fallback


@dataclass
class Chunk:
    """A single chunk ready for embedding."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


MAX_CODE_CHUNK_TOKENS = 1500


def chunk_code_units(parsed_units: list, max_tokens: int = MAX_CODE_CHUNK_TOKENS) -> List[Chunk]:
    """
    Chunk parsed code units. Each unit is typically already a method/function.
    If a unit exceeds max_tokens, it's split at logical boundaries.

    Args:
        parsed_units: List of ParsedCodeUnit objects from the code parser
        max_tokens: Maximum tokens per chunk

    Returns:
        List of Chunk objects ready for embedding
    """
    chunks = []

    for unit in parsed_units:
        token_count = count_tokens(unit.content)

        # Build a context header
        header = _build_header(unit)

        if token_count <= max_tokens:
            # Unit fits in one chunk
            full_content = f"{header}\n\n{unit.content}" if header else unit.content
            chunks.append(Chunk(
                content=full_content,
                metadata={
                    **unit.metadata,
                    "source_file": unit.file_path,
                    "language": unit.language,
                    "unit_type": unit.unit_type,
                    "unit_name": unit.unit_name,
                    "start_line": unit.start_line,
                    "end_line": unit.end_line,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "title": f"{unit.unit_name} ({unit.unit_type})",
                },
            ))
        else:
            # Split oversized unit
            sub_chunks = _split_large_unit(unit, max_tokens, header)
            chunks.extend(sub_chunks)

    logger.info(f"Created {len(chunks)} code chunks from {len(parsed_units)} code units")
    return chunks


def _build_header(unit) -> str:
    """Build a context header for the code unit."""
    parts = []
    if unit.language:
        parts.append(f"Language: {unit.language}")
    if unit.file_path:
        parts.append(f"File: {unit.file_path}")
    if unit.unit_type and unit.unit_name:
        parts.append(f"{unit.unit_type.title()}: {unit.unit_name}")
    if hasattr(unit, 'metadata') and unit.metadata.get("class_name"):
        parts.append(f"Class: {unit.metadata['class_name']}")
    if hasattr(unit, 'metadata') and unit.metadata.get("signature"):
        parts.append(f"Signature: {unit.metadata['signature']}")

    return " | ".join(parts) if parts else ""


def _split_large_unit(unit, max_tokens: int, header: str) -> List[Chunk]:
    """Split an oversized code unit into smaller chunks at logical boundaries."""
    lines = unit.content.split("\n")
    chunks = []
    current_lines = []
    current_tokens = count_tokens(header) + 2  # Account for header

    for line in lines:
        line_tokens = count_tokens(line)

        if current_tokens + line_tokens > max_tokens and current_lines:
            # Save current chunk
            content = "\n".join(current_lines)
            full_content = f"{header}\n\n{content}" if header else content
            chunks.append(Chunk(
                content=full_content,
                metadata={
                    **unit.metadata,
                    "source_file": unit.file_path,
                    "language": unit.language,
                    "unit_type": unit.unit_type,
                    "unit_name": unit.unit_name,
                    "start_line": unit.start_line,
                    "end_line": unit.end_line,
                    "chunk_index": len(chunks),
                    "title": f"{unit.unit_name} ({unit.unit_type}) [part {len(chunks) + 1}]",
                },
            ))
            current_lines = []
            current_tokens = count_tokens(header) + 2

        current_lines.append(line)
        current_tokens += line_tokens

    # Save remaining lines
    if current_lines:
        content = "\n".join(current_lines)
        full_content = f"{header}\n\n{content}" if header else content
        chunks.append(Chunk(
            content=full_content,
            metadata={
                **unit.metadata,
                "source_file": unit.file_path,
                "language": unit.language,
                "unit_type": unit.unit_type,
                "unit_name": unit.unit_name,
                "start_line": unit.start_line,
                "end_line": unit.end_line,
                "chunk_index": len(chunks),
                "title": f"{unit.unit_name} ({unit.unit_type}) [part {len(chunks) + 1}]",
            },
        ))

    # Update total_chunks in metadata
    for chunk in chunks:
        chunk.metadata["total_chunks"] = len(chunks)

    return chunks
