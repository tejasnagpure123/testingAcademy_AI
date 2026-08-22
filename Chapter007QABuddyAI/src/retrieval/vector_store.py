"""
QABuddy.ai — Qdrant Vector Store
Manages the Qdrant collection: creation, upserting, and search operations.
Supports both dense and sparse vectors for hybrid retrieval.
"""

import uuid
from typing import List, Dict, Any, Optional
from loguru import logger

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    SparseVector,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.config.settings import settings
from src.ingestion.embedder import get_embedding_dimension


class QdrantVectorStore:
    """
    Wrapper around Qdrant for managing the QABuddy collection.
    Supports hybrid (dense + sparse) vector storage and retrieval.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.api_key = api_key or settings.qdrant_api_key
        self.collection_name = collection_name or settings.qdrant_collection

        # Initialize client — prefer local embedded mode if QDRANT_PATH is set
        qdrant_path = getattr(settings, "qdrant_path", None)
        if qdrant_path:
            import os
            from pathlib import Path as _Path
            _Path(qdrant_path).mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=qdrant_path)
            logger.info(f"Qdrant running in LOCAL EMBEDDED mode at path: {qdrant_path}")
        else:
            connect_kwargs = {"host": self.host, "port": self.port}
            if self.api_key:
                connect_kwargs["api_key"] = self.api_key
            self.client = QdrantClient(**connect_kwargs)
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

    def create_collection(self, recreate: bool = False) -> None:
        """
        Create the QABuddy collection with dense + sparse vector config.

        Args:
            recreate: If True, delete and recreate the collection
        """
        # Check if collection exists
        collections = [c.name for c in self.client.get_collections().collections]

        if self.collection_name in collections:
            if recreate:
                logger.warning(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return

        dim = get_embedding_dimension(settings.embedding_model)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=dim,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False),
                ),
            },
        )

        # Create payload indexes for filtering
        for field in ["source_type", "language", "unit_type", "ticket_key"]:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )

        logger.info(
            f"Created collection '{self.collection_name}' "
            f"(dense: {dim}d cosine, sparse: enabled)"
        )

    def upsert_chunks(
        self,
        chunks: list,
        embeddings: list,
        source_type: str,
        batch_size: int = 100,
    ) -> int:
        """
        Upsert chunks with their embeddings into Qdrant.

        Args:
            chunks: List of Chunk objects
            embeddings: List of EmbeddingResult objects (same order as chunks)
            source_type: Source type identifier
            batch_size: Number of points per upsert batch

        Returns:
            Number of points upserted
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have same length"
            )

        points = []
        for chunk, emb in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())

            # Build payload (all metadata + text content for retrieval display)
            payload = {
                **chunk.metadata,
                "source_type": source_type,
                "text": chunk.content,
            }

            # Build vectors
            vectors = {"dense": emb.dense_vector}

            # Build sparse vector if available
            sparse_vector = None
            if emb.sparse_vector:
                indices = list(emb.sparse_vector.keys())
                values = list(emb.sparse_vector.values())
                sparse_vector = {"sparse": SparseVector(indices=indices, values=values)}

            point = PointStruct(
                id=point_id,
                vector=vectors,
                payload=payload,
            )

            # Add sparse vector if available
            if sparse_vector:
                point.vector.update(sparse_vector)

            points.append(point)

        # Upsert in batches
        total = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
            )
            total += len(batch)
            if total % 500 == 0:
                logger.info(f"  Upserted {total}/{len(points)} points")

        logger.info(f"Upserted {total} points for {source_type}")
        return total

    def search_dense(
        self,
        query_vector: List[float],
        top_k: int = 50,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search using dense vector only.

        Args:
            query_vector: Dense query vector
            top_k: Number of results
            source_filter: Optional source_type filter

        Returns:
            List of search results with score, text, and metadata
        """
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=source_filter))]
            )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using="dense",
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        return self._format_query_results(results)

    def search_sparse(
        self,
        sparse_vector: Dict[int, float],
        top_k: int = 50,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search using sparse vector only (keyword/BM25-like).
        """
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=source_filter))]
            )

        indices = list(sparse_vector.keys())
        values = list(sparse_vector.values())

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=SparseVector(indices=indices, values=values),
            using="sparse",
            query_filter=query_filter,
            limit=top_k,
            with_payload=True,
        )

        return self._format_query_results(results)

    def hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Optional[Dict[int, float]] = None,
        top_k: int = 50,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining dense and sparse results with RRF.
        Uses Qdrant's query API with prefetch for server-side fusion.
        """
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=source_filter))]
            )

        if sparse_vector:
            indices = list(sparse_vector.keys())
            values = list(sparse_vector.values())

            # Use Qdrant's Query API with prefetch + RRF fusion
            try:
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    prefetch=[
                        qmodels.Prefetch(
                            query=dense_vector,
                            using="dense",
                            limit=top_k,
                            filter=query_filter,
                        ),
                        qmodels.Prefetch(
                            query=SparseVector(indices=indices, values=values),
                            using="sparse",
                            limit=top_k,
                            filter=query_filter,
                        ),
                    ],
                    query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
                    limit=top_k,
                    with_payload=True,
                )
                return self._format_query_results(results)
            except Exception as e:
                logger.warning(f"Hybrid query failed, falling back to dense-only: {e}")
                return self.search_dense(dense_vector, top_k, source_filter)
        else:
            # No sparse vector — fall back to dense-only
            return self.search_dense(dense_vector, top_k, source_filter)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            # vectors_count was removed in newer Qdrant versions; use indexed_vectors_count as fallback
            vectors_count = getattr(info, "indexed_vectors_count", None) or getattr(info, "vectors_count", None)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": vectors_count,
                "status": str(info.status),
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_by_source(self, source_type: str) -> None:
        """Delete all points for a specific source type."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="source_type", match=MatchValue(value=source_type))]
                )
            ),
        )
        logger.info(f"Deleted all points for source: {source_type}")

    # ─── Private Helpers ───────────────────────────────────────

    def _format_results(self, results) -> List[Dict[str, Any]]:
        """Format Qdrant search results into a standard dict format."""
        formatted = []
        for r in results:
            formatted.append({
                "id": str(r.id),
                "score": r.score,
                "text": r.payload.get("text", ""),
                "metadata": {k: v for k, v in r.payload.items() if k != "text"},
            })
        return formatted

    def _format_query_results(self, results) -> List[Dict[str, Any]]:
        """Format Qdrant query_points results."""
        formatted = []
        for r in results.points:
            formatted.append({
                "id": str(r.id),
                "score": r.score if hasattr(r, 'score') else 0.0,
                "text": r.payload.get("text", ""),
                "metadata": {k: v for k, v in r.payload.items() if k != "text"},
            })
        return formatted
