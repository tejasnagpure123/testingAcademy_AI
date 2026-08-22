"""
QABuddy.ai — Base Chunk Data Class
Shared Chunk dataclass used by all source-specific chunkers.
Centralising it here avoids duplicate definitions across chunker modules.
"""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """
    A single text chunk ready for embedding and indexing.

    Attributes:
        content: The text content to be embedded
        metadata: Arbitrary key-value metadata attached to this chunk
                  (source_type, source_file, title, language, etc.)
    """
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.content[:60].replace("\n", " ")
        return (
            f"Chunk(content='{preview}...', "
            f"source={self.metadata.get('source_type', '?')}, "
            f"title={self.metadata.get('title', '?')!r})"
        )
