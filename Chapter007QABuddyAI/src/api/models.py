"""
QABuddy.ai — Pydantic Models
Request/response schemas for the FastAPI endpoints.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ─── Request Models ─────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""
    question: str = Field(..., description="The user's question", min_length=1, max_length=2000)
    source_filter: Optional[str] = Field(
        None,
        description="Optional filter by source_type (e.g., 'selenium_repo', 'jira_tickets')",
    )
    chat_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Previous conversation turns: [{'role': 'user'|'assistant', 'content': '...'}]",
    )


class IngestRequest(BaseModel):
    """Request body for the /api/ingest endpoint."""
    sources: Optional[List[str]] = Field(
        None,
        description="List of source types to ingest. If null, ingests all.",
    )
    recreate_collection: bool = Field(
        False,
        description="If true, deletes and recreates the vector collection before ingesting",
    )


# ─── Response Models ────────────────────────────────────────

class SourceReference(BaseModel):
    """A source citation in a response."""
    source_type: str
    source_file: str
    title: str
    ticket_key: Optional[str] = ""
    score: float = 0.0


class ChatResponse(BaseModel):
    """Response body from the /api/chat endpoint."""
    answer: str
    sources: List[SourceReference]
    query: str
    num_chunks_retrieved: int
    num_chunks_reranked: int


class IngestResponse(BaseModel):
    """Response body from the /api/ingest endpoint."""
    status: str
    stats: Dict[str, int]
    total_chunks: int
    message: str


class HealthResponse(BaseModel):
    """Response body from the /api/health endpoint."""
    status: str
    qdrant_status: str
    collection_info: Dict[str, Any]
    llm_provider: str
    embedding_model: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
