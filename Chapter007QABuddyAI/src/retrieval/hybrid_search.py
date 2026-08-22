"""
QABuddy.ai — Hybrid Search
High-level search interface: embeds query → hybrid search → returns ranked results.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from src.config.settings import settings
from src.ingestion.embedder import embed_query
from src.retrieval.vector_store import QdrantVectorStore


class HybridSearcher:
    """
    High-level hybrid search interface.
    Handles query embedding and vector store interaction.
    """

    def __init__(self, vector_store: QdrantVectorStore):
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 50,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search: embed query → dense + sparse search → RRF fusion.

        Args:
            query: User's question
            top_k: Number of candidates to retrieve
            source_filter: Optional source_type filter (e.g., "selenium_repo")

        Returns:
            List of search results, ranked by hybrid score
        """
        # Embed the query
        logger.debug(f"Embedding query: '{query[:80]}...'")
        query_embedding = embed_query(
            query,
            model_name=settings.embedding_model,
            use_gpu=settings.use_gpu,
        )

        # Perform hybrid search
        results = self.vector_store.hybrid_search(
            dense_vector=query_embedding.dense_vector,
            sparse_vector=query_embedding.sparse_vector,
            top_k=top_k,
            source_filter=source_filter,
        )

        logger.info(f"Hybrid search returned {len(results)} results for: '{query[:50]}...'")
        return results
