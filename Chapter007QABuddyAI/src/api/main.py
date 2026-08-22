"""
QABuddy.ai — FastAPI Application
Main entry point for the backend API server.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import settings
from src.retrieval.vector_store import QdrantVectorStore
from src.retrieval.hybrid_search import HybridSearcher
from src.chat.qa_chain import QAChain
from src.chat.llm_client import LLMClient

from src.api.routes import chat as chat_route
from src.api.routes import ingest as ingest_route
from src.api.routes import health as health_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: initialize services on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("QABuddy.ai — Starting up...")
    logger.info("=" * 60)

    try:
        # Initialize Qdrant vector store
        vector_store = QdrantVectorStore()
        vector_store.create_collection(recreate=False)
        logger.info("✓ Qdrant vector store connected")

        # Initialize search and QA chain
        searcher = HybridSearcher(vector_store)
        llm_client = LLMClient()
        qa_chain = QAChain(searcher=searcher, llm_client=llm_client)
        logger.info("✓ QA Chain initialized")

        # Inject dependencies into routes
        chat_route.set_qa_chain(qa_chain)
        ingest_route.set_vector_store(vector_store)
        health_route.set_vector_store(vector_store)
        logger.info("✓ Routes configured")

        logger.info("QABuddy.ai is ready! 🚀")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Server will start in degraded mode")

    yield

    logger.info("QABuddy.ai — Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="QABuddy.ai",
    description=(
        "Hybrid RAG API for QA Engineers. "
        "Ask questions grounded in your Selenium framework, Playwright framework, "
        "test case repository, JIRA tickets, PRDs, and more."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Streamlit UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_route.router, prefix="/api", tags=["Chat"])
app.include_router(ingest_route.router, prefix="/api", tags=["Ingestion"])
app.include_router(health_route.router, prefix="/api", tags=["System"])


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": "QABuddy.ai",
        "version": "1.0.0",
        "description": "Hybrid RAG for QA Engineers",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
