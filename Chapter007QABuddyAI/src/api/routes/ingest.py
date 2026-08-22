"""
QABuddy.ai — Ingest Route
POST /api/ingest — Trigger data ingestion for specified sources.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger

from src.api.models import IngestRequest, IngestResponse

router = APIRouter()

_vector_store = None


def set_vector_store(vs):
    """Inject the vector store dependency."""
    global _vector_store
    _vector_store = vs


@router.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Trigger data ingestion.

    Runs the ingestion pipeline for the specified sources (or all sources if not specified).
    Optionally recreates the vector collection first.
    """
    if _vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    try:
        from src.ingestion.orchestrator import IngestionOrchestrator

        # Optionally recreate collection
        if request.recreate_collection:
            logger.warning("Recreating vector collection...")
            _vector_store.create_collection(recreate=True)

        orchestrator = IngestionOrchestrator(vector_store=_vector_store)
        stats = orchestrator.ingest_all(sources=request.sources)
        total = sum(stats.values())

        return IngestResponse(
            status="completed",
            stats=stats,
            total_chunks=total,
            message=f"Successfully ingested {total} chunks from {len(stats)} sources",
        )

    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
