"""
QABuddy.ai — Health Route
GET /api/health — System health check.
"""

from fastapi import APIRouter
from loguru import logger

from src.api.models import HealthResponse
from src.config.settings import settings

router = APIRouter()

_vector_store = None


def set_vector_store(vs):
    """Inject the vector store dependency."""
    global _vector_store
    _vector_store = vs


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Check system health: Qdrant connection, collection status, configuration.
    """
    qdrant_status = "disconnected"
    collection_info = {}

    if _vector_store is not None:
        try:
            collection_info = _vector_store.get_collection_info()
            qdrant_status = "connected"
        except Exception as e:
            qdrant_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if qdrant_status == "connected" else "degraded",
        qdrant_status=qdrant_status,
        collection_info=collection_info,
        llm_provider=settings.llm_provider,
        embedding_model=settings.embedding_model,
    )
