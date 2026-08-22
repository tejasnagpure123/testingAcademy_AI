"""
QABuddy.ai — Cross-Encoder Reranker
Uses bge-reranker-v2-m3 to rerank hybrid search candidates for precision.
Retrieves top-50 → reranks → returns top-5.
"""

from typing import List, Dict, Any, Tuple
from loguru import logger

_reranker = None


def get_reranker(model_name: str = "BAAI/bge-reranker-v2-m3"):
    """Load and cache the reranker model."""
    global _reranker

    if _reranker is not None:
        return _reranker

    # Prefer sentence_transformers CrossEncoder for stability across tokenizer versions
    try:
        from sentence_transformers import CrossEncoder
        from src.config.settings import settings
        device = "cuda" if settings.use_gpu else "cpu"
        logger.info(f"Loading CrossEncoder reranker: {model_name} on {device}...")
        _reranker = CrossEncoder(model_name, device=device)
        logger.info("CrossEncoder reranker loaded successfully")
        return _reranker
    except Exception as e:
        logger.warning(f"CrossEncoder initialization failed: {e}. Trying FlagReranker...")

    try:
        from FlagEmbedding import FlagReranker
        from src.config.settings import settings
        logger.info(f"Loading FlagReranker: {model_name}...")
        _reranker = FlagReranker(model_name, use_fp16=settings.use_gpu)
        logger.info("FlagReranker loaded successfully")
        return _reranker
    except Exception as e:
        logger.error(f"Failed to load reranker: {e}")
        return None


def rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
    model_name: str = "BAAI/bge-reranker-v2-m3",
) -> List[Dict[str, Any]]:
    """
    Rerank search candidates using a cross-encoder.

    Args:
        query: User's question
        candidates: List of search results from hybrid search
        top_k: Number of results to return after reranking
        model_name: Reranker model name

    Returns:
        Top-k reranked results with updated scores
    """
    if not candidates:
        return []

    reranker = get_reranker(model_name)

    if reranker is None:
        # Reranker not available — return top-k from original ranking
        logger.warning("Reranker not available, returning top-k from original search")
        return candidates[:top_k]

    # Prepare query-document pairs
    pairs = [(query, candidate["text"]) for candidate in candidates]

    try:
        # Check if CrossEncoder or FlagReranker
        if hasattr(reranker, "predict"):
            import numpy as np
            raw_scores = reranker.predict(pairs)
            # Sigmoid normalize logits to [0, 1]
            scores = 1 / (1 + np.exp(-raw_scores))
        else:
            scores = reranker.compute_score(pairs, normalize=True)

        # Handle single result case
        if isinstance(scores, (int, float)):
            scores = [scores]

        # Attach scores and sort
        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = float(scores[i])
            candidate["original_score"] = candidate.get("score", 0.0)

        # Sort by reranker score (descending)
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

        logger.info(
            f"Reranked {len(candidates)} candidates → top {top_k} "
            f"(best: {reranked[0]['rerank_score']:.3f})"
        )

        return reranked[:top_k]

    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        return candidates[:top_k]
