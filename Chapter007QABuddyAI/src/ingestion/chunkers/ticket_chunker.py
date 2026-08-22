"""
QABuddy.ai — Ticket Chunker
Handles ticket-level chunking for JIRA tickets.
Each ticket is treated as an atomic chunk, with oversized tickets split logically.
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


MAX_TICKET_TOKENS = 1000


def chunk_jira_tickets(parsed_tickets: list, max_tokens: int = MAX_TICKET_TOKENS) -> List[Chunk]:
    """
    Convert parsed JIRA tickets into chunks.
    Each ticket is ideally one chunk. Oversized tickets (lots of comments) are split.

    Args:
        parsed_tickets: List of ParsedJiraTicket objects
        max_tokens: Max tokens per chunk

    Returns:
        List of Chunk objects ready for embedding
    """
    chunks = []

    for ticket in parsed_tickets:
        token_count = count_tokens(ticket.content)

        if token_count <= max_tokens:
            chunks.append(Chunk(
                content=ticket.content,
                metadata={
                    **ticket.metadata,
                    "source_file": ticket.ticket_key,
                    "language": "jira",
                    "unit_type": "ticket",
                    "unit_name": ticket.ticket_key,
                    "ticket_key": ticket.ticket_key,
                    "ticket_status": ticket.status,
                    "ticket_priority": ticket.priority,
                    "ticket_type": ticket.ticket_type,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "title": f"{ticket.ticket_key}: {ticket.summary}",
                },
            ))
        else:
            # Split: core ticket info as one chunk, comments as another
            sub_chunks = _split_large_ticket(ticket, max_tokens)
            chunks.extend(sub_chunks)

    logger.info(f"Created {len(chunks)} chunks from {len(parsed_tickets)} JIRA tickets")
    return chunks


def _split_large_ticket(ticket, max_tokens: int) -> List[Chunk]:
    """Split an oversized ticket into core info + comment chunks."""
    chunks = []
    base_metadata = {
        **ticket.metadata,
        "source_file": ticket.ticket_key,
        "language": "jira",
        "unit_type": "ticket",
        "unit_name": ticket.ticket_key,
        "ticket_key": ticket.ticket_key,
        "ticket_status": ticket.status,
        "ticket_priority": ticket.priority,
        "ticket_type": ticket.ticket_type,
    }

    # Split content at the Comments section
    if "\nComments" in ticket.content:
        parts = ticket.content.split("\nComments", 1)
        core_content = parts[0].strip()
        comments_content = f"JIRA Ticket: {ticket.ticket_key}\nComments{parts[1]}"
    else:
        # Just split by size
        lines = ticket.content.split("\n")
        mid = len(lines) // 2
        core_content = "\n".join(lines[:mid]).strip()
        comments_content = f"JIRA Ticket: {ticket.ticket_key} (continued)\n" + "\n".join(lines[mid:]).strip()

    # Core chunk
    chunks.append(Chunk(
        content=core_content,
        metadata={
            **base_metadata,
            "chunk_index": 0,
            "title": f"{ticket.ticket_key}: {ticket.summary}",
        },
    ))

    # Comments chunk (may need further splitting)
    if count_tokens(comments_content) <= max_tokens:
        chunks.append(Chunk(
            content=comments_content,
            metadata={
                **base_metadata,
                "chunk_index": 1,
                "title": f"{ticket.ticket_key}: Comments",
            },
        ))
    else:
        # Split comments further
        comment_lines = comments_content.split("\n")
        current = []
        current_tokens = 0

        for line in comment_lines:
            line_tokens = count_tokens(line)
            if current_tokens + line_tokens > max_tokens and current:
                chunks.append(Chunk(
                    content="\n".join(current).strip(),
                    metadata={
                        **base_metadata,
                        "chunk_index": len(chunks),
                        "title": f"{ticket.ticket_key}: Comments [part {len(chunks)}]",
                    },
                ))
                current = []
                current_tokens = 0
            current.append(line)
            current_tokens += line_tokens

        if current:
            chunks.append(Chunk(
                content="\n".join(current).strip(),
                metadata={
                    **base_metadata,
                    "chunk_index": len(chunks),
                    "title": f"{ticket.ticket_key}: Comments [part {len(chunks)}]",
                },
            ))

    # Set total_chunks
    for chunk in chunks:
        chunk.metadata["total_chunks"] = len(chunks)

    return chunks
