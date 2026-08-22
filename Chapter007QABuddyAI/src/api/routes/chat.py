"""
QABuddy.ai — Chat Route
POST /api/chat — Ask a question and get a cited answer.
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.api.models import ChatRequest, ChatResponse, SourceReference

router = APIRouter()

# These will be injected at app startup
_qa_chain = None


def set_qa_chain(qa_chain):
    """Inject the QA chain dependency."""
    global _qa_chain
    _qa_chain = qa_chain


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask QABuddy a question.

    The question is processed through the full RAG pipeline:
    1. Hybrid search (dense + sparse) for top-50 candidates
    2. Cross-encoder reranking to top-5
    3. LLM generates a cited answer

    Optionally filter by source_type (e.g., "selenium_repo", "jira_tickets").
    """
    if _qa_chain is None:
        raise HTTPException(status_code=503, detail="QA Chain not initialized")

    try:
        logger.info(f"Chat request: '{request.question[:80]}...'")

        response = _qa_chain.ask(
            question=request.question,
            source_filter=request.source_filter,
            chat_history=request.chat_history,
        )

        return ChatResponse(
            answer=response.answer,
            sources=[
                SourceReference(**s) for s in response.sources
            ],
            query=response.query,
            num_chunks_retrieved=response.num_chunks_retrieved,
            num_chunks_reranked=response.num_chunks_reranked,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
