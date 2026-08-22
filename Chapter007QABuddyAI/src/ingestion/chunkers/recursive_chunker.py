"""
QABuddy.ai — Recursive Text Chunker
Handles recursive splitting of prose documents (PDFs, PRDs, meeting transcripts, etc.)
with configurable chunk size and overlap.
"""

from typing import List, Dict, Any, Optional
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


# Chunk size profiles per source type
CHUNK_PROFILES = {
    "company_docs": {"chunk_size": 800, "overlap": 120},
    "meeting_transcripts": {"chunk_size": 600, "overlap": 90},
    "lucid_charts": {"chunk_size": 500, "overlap": 50},
    "prd_docs": {"chunk_size": 1000, "overlap": 150},
    "default": {"chunk_size": 800, "overlap": 120},
}

# Split hierarchy: try each separator in order
SEPARATORS = [
    "\n\n",       # Paragraph boundaries (strongest)
    "\n",         # Line breaks
    ". ",         # Sentence boundaries
    "? ",
    "! ",
    "; ",
    ", ",
    " ",          # Word boundaries (weakest)
]


def chunk_text_sections(
    parsed_sections: list,
    source_type: str = "default",
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
) -> List[Chunk]:
    """
    Chunk parsed text sections using recursive splitting.

    Args:
        parsed_sections: List of parsed section objects (ParsedPDFSection, ParsedTextSection, etc.)
        source_type: Source type for chunk size profile selection
        chunk_size: Override chunk size in tokens
        overlap: Override overlap in tokens

    Returns:
        List of Chunk objects ready for embedding
    """
    profile = CHUNK_PROFILES.get(source_type, CHUNK_PROFILES["default"])
    target_size = chunk_size or profile["chunk_size"]
    target_overlap = overlap or profile["overlap"]

    all_chunks = []

    for section in parsed_sections:
        content = section.content
        token_count = count_tokens(content)

        # Base metadata from the section
        base_meta = {}
        if hasattr(section, 'metadata'):
            base_meta = dict(section.metadata)
        if hasattr(section, 'file_path'):
            base_meta["source_file"] = section.file_path
        if hasattr(section, 'section_title'):
            base_meta["section_title"] = section.section_title
        if hasattr(section, 'page_number'):
            base_meta["page_number"] = section.page_number

        if token_count <= target_size:
            # Section fits in one chunk
            title = base_meta.get("section_title", "")
            all_chunks.append(Chunk(
                content=content,
                metadata={
                    **base_meta,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "title": title,
                    "source_type": source_type,
                },
            ))
        else:
            # Recursive split
            sub_chunks = _recursive_split(content, target_size, target_overlap)
            for i, sub_content in enumerate(sub_chunks):
                title = base_meta.get("section_title", "")
                all_chunks.append(Chunk(
                    content=sub_content,
                    metadata={
                        **base_meta,
                        "chunk_index": i,
                        "total_chunks": len(sub_chunks),
                        "title": f"{title} [part {i + 1}]" if len(sub_chunks) > 1 else title,
                        "source_type": source_type,
                    },
                ))

    logger.info(
        f"Created {len(all_chunks)} chunks from {len(parsed_sections)} sections "
        f"(target: {target_size} tokens, overlap: {target_overlap} tokens)"
    )
    return all_chunks


def _recursive_split(
    text: str,
    target_size: int,
    overlap: int,
    separators: Optional[List[str]] = None,
) -> List[str]:
    """
    Recursively split text at the best available separator.

    Tries separators in order of preference (paragraph > line > sentence > word).
    """
    if separators is None:
        separators = SEPARATORS

    if count_tokens(text) <= target_size:
        return [text.strip()] if text.strip() else []

    # Find the best separator (first one that actually splits the text)
    best_sep = " "  # fallback
    for sep in separators:
        if sep in text:
            best_sep = sep
            break

    # Split at the best separator
    parts = text.split(best_sep)

    # Merge small parts into chunks of approximately target_size tokens
    chunks = []
    current_parts = []
    current_tokens = 0

    for part in parts:
        part_tokens = count_tokens(part)

        if current_tokens + part_tokens > target_size and current_parts:
            # Save current chunk
            chunk_text = best_sep.join(current_parts).strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Start new chunk with overlap
            overlap_parts = _get_overlap_parts(current_parts, best_sep, overlap)
            current_parts = overlap_parts + [part]
            current_tokens = sum(count_tokens(p) for p in current_parts)
        else:
            current_parts.append(part)
            current_tokens += part_tokens

    # Save remaining
    if current_parts:
        chunk_text = best_sep.join(current_parts).strip()
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


def _get_overlap_parts(parts: List[str], sep: str, overlap_tokens: int) -> List[str]:
    """Get the trailing parts that form the overlap window."""
    overlap_parts = []
    tokens = 0

    for part in reversed(parts):
        part_tokens = count_tokens(part)
        if tokens + part_tokens > overlap_tokens:
            break
        overlap_parts.insert(0, part)
        tokens += part_tokens

    return overlap_parts
