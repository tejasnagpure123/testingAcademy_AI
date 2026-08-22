"""
QABuddy.ai — Log Chunker
Handles log-block chunking for Jenkins logs and test results.
Splits by build/stage boundaries, ensuring stack traces stay together.
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
        return len(text.split())


@dataclass
class Chunk:
    """A single chunk ready for embedding."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


MAX_LOG_CHUNK_TOKENS = 500
LOG_OVERLAP_TOKENS = 50


def chunk_log_blocks(parsed_log_blocks: list, max_tokens: int = MAX_LOG_CHUNK_TOKENS) -> List[Chunk]:
    """
    Chunk parsed log blocks. Each log block is typically already a logical unit.
    Oversized blocks are split further at line boundaries.

    Args:
        parsed_log_blocks: List of ParsedLogBlock objects
        max_tokens: Maximum tokens per chunk

    Returns:
        List of Chunk objects ready for embedding
    """
    chunks = []

    for block in parsed_log_blocks:
        token_count = count_tokens(block.content)

        base_meta = {
            **block.metadata,
            "source_file": block.file_path,
            "language": "log",
            "unit_type": block.block_type,
            "unit_name": f"log_block_{block.block_index}",
        }

        if token_count <= max_tokens:
            chunks.append(Chunk(
                content=block.content,
                metadata={
                    **base_meta,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "title": f"Jenkins Log: {block.block_type} (block {block.block_index})",
                },
            ))
        else:
            # Split large blocks at line boundaries with overlap
            sub_chunks = _split_log_block(block.content, max_tokens, LOG_OVERLAP_TOKENS)
            for i, sub_content in enumerate(sub_chunks):
                chunks.append(Chunk(
                    content=sub_content,
                    metadata={
                        **base_meta,
                        "chunk_index": i,
                        "total_chunks": len(sub_chunks),
                        "title": f"Jenkins Log: {block.block_type} (block {block.block_index}, part {i + 1})",
                    },
                ))

    logger.info(f"Created {len(chunks)} log chunks from {len(parsed_log_blocks)} log blocks")
    return chunks


def _split_log_block(content: str, max_tokens: int, overlap_tokens: int) -> List[str]:
    """Split a log block at line boundaries with overlap."""
    lines = content.split("\n")
    chunks = []
    current_lines = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line)

        if current_tokens + line_tokens > max_tokens and current_lines:
            chunks.append("\n".join(current_lines).strip())

            # Keep overlap lines
            overlap_lines = []
            overlap_t = 0
            for ol in reversed(current_lines):
                olt = count_tokens(ol)
                if overlap_t + olt > overlap_tokens:
                    break
                overlap_lines.insert(0, ol)
                overlap_t += olt

            current_lines = overlap_lines
            current_tokens = overlap_t

        current_lines.append(line)
        current_tokens += line_tokens

    if current_lines:
        chunks.append("\n".join(current_lines).strip())

    return [c for c in chunks if c]
