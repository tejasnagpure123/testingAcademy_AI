"""
QABuddy.ai — BGE-M3 Embedder
Produces dense + sparse embeddings for hybrid search using BAAI/bge-m3.
Falls back to sentence-transformers for dense-only if FlagEmbedding is not available.
"""

import os
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from loguru import logger

# Lazy-loaded — heavy ML libraries are imported only when the model is first used
_USE_FLAG = None   # None = not yet determined
_model = None
BGEM3FlagModel = None
SentenceTransformer = None


@dataclass
class EmbeddingResult:
    """Result of embedding a text."""
    dense_vector: List[float]
    sparse_vector: Optional[Dict[int, float]] = None  # {token_id: weight}
    text: str = ""


def get_model(model_name: str = "BAAI/bge-m3", use_gpu: bool = False):
    """
    Load and cache the embedding model (lazy — only loads on first call).

    Args:
        model_name: HuggingFace model name
        use_gpu: Whether to use GPU acceleration
    """
    global _model, _USE_FLAG, BGEM3FlagModel, SentenceTransformer

    if _model is not None:
        return _model

    # Determine which library to use (only on first call)
    if _USE_FLAG is None:
        try:
            from FlagEmbedding import BGEM3FlagModel as _FE
            BGEM3FlagModel = _FE
            _USE_FLAG = True
            logger.info("FlagEmbedding available — will use full BGE-M3 hybrid mode (dense + sparse)")
        except ImportError:
            _USE_FLAG = False
            logger.warning("FlagEmbedding not installed. Falling back to sentence-transformers (dense-only).")
            try:
                from sentence_transformers import SentenceTransformer as _ST
                SentenceTransformer = _ST
            except ImportError:
                logger.error("Neither FlagEmbedding nor sentence-transformers installed!")

    device = "cuda" if use_gpu else "cpu"

    if _USE_FLAG and BGEM3FlagModel is not None:
        logger.info(f"Loading BGE-M3 via FlagEmbedding on {device}...")
        _model = BGEM3FlagModel(
            model_name,
            use_fp16=(device == "cuda"),
            device=device,
        )
        logger.info("BGE-M3 model loaded successfully (dense + sparse mode)")
    elif SentenceTransformer is not None:
        logger.info(f"Loading {model_name} via sentence-transformers on {device}...")
        _model = SentenceTransformer(model_name, device=device)
        logger.info("Model loaded (dense-only mode)")
    else:
        raise RuntimeError("No embedding library available. Install FlagEmbedding or sentence-transformers.")

    return _model


def embed_texts(
    texts: List[str],
    model_name: str = "BAAI/bge-m3",
    use_gpu: bool = False,
    batch_size: int = 32,
) -> List[EmbeddingResult]:
    """
    Embed a list of texts, producing dense and (optionally) sparse vectors.

    Args:
        texts: List of text strings to embed
        model_name: HuggingFace model name
        use_gpu: Whether to use GPU
        batch_size: Batch size for inference

    Returns:
        List of EmbeddingResult with dense_vector and sparse_vector
    """
    if not texts:
        return []

    model = get_model(model_name, use_gpu)
    results = []

    if _USE_FLAG:
        # FlagEmbedding: get dense + sparse vectors
        logger.info(f"Embedding {len(texts)} texts with BGE-M3 (dense + sparse)...")

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                output = model.encode(
                    batch,
                    return_dense=True,
                    return_sparse=True,
                    return_colbert_vecs=False,  # Skip ColBERT for storage efficiency
                )

                dense_vecs = output["dense_vecs"]
                sparse_output = output.get("lexical_weights", [])

                for j in range(len(batch)):
                    dense = dense_vecs[j].tolist() if hasattr(dense_vecs[j], 'tolist') else list(dense_vecs[j])

                    # Convert sparse weights to {token_id: weight} dict
                    sparse = None
                    if sparse_output and j < len(sparse_output):
                        sparse_raw = sparse_output[j]
                        if isinstance(sparse_raw, dict):
                            sparse = {int(k): float(v) for k, v in sparse_raw.items()}
                        elif hasattr(sparse_raw, 'items'):
                            sparse = {int(k): float(v) for k, v in sparse_raw.items()}

                    results.append(EmbeddingResult(
                        dense_vector=dense,
                        sparse_vector=sparse,
                        text=batch[j],
                    ))
            except Exception as e:
                logger.error(f"Embedding batch {i} failed: {e}")
                # Fall back to empty embeddings for this batch
                for text in batch:
                    results.append(EmbeddingResult(
                        dense_vector=[0.0] * 1024,  # BGE-M3 dimension
                        sparse_vector=None,
                        text=text,
                    ))

            if (i + batch_size) % (batch_size * 10) == 0:
                logger.info(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts")

    else:
        # sentence-transformers: dense only
        logger.info(f"Embedding {len(texts)} texts (dense-only mode)...")
        try:
            embeddings = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                normalize_embeddings=True,
            )

            for j, emb in enumerate(embeddings):
                dense = emb.tolist() if hasattr(emb, 'tolist') else list(emb)
                results.append(EmbeddingResult(
                    dense_vector=dense,
                    sparse_vector=None,
                    text=texts[j],
                ))
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            dim = 1024  # BGE-M3 dimension
            for text in texts:
                results.append(EmbeddingResult(
                    dense_vector=[0.0] * dim,
                    sparse_vector=None,
                    text=text,
                ))

    logger.info(f"Embedding complete: {len(results)} vectors generated")
    return results


def embed_query(
    query: str,
    model_name: str = "BAAI/bge-m3",
    use_gpu: bool = False,
) -> EmbeddingResult:
    """
    Embed a single query text.

    Args:
        query: Query string
        model_name: HuggingFace model name
        use_gpu: Whether to use GPU

    Returns:
        EmbeddingResult with dense and sparse vectors
    """
    results = embed_texts([query], model_name, use_gpu, batch_size=1)
    return results[0] if results else EmbeddingResult(dense_vector=[0.0] * 1024, text=query)


def get_embedding_dimension(model_name: str = "BAAI/bge-m3") -> int:
    """Get the dense embedding dimension for the model."""
    # Known dimensions
    known_dims = {
        "BAAI/bge-m3": 1024,
        "BAAI/bge-large-en-v1.5": 1024,
        "BAAI/bge-base-en-v1.5": 768,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
    }
    return known_dims.get(model_name, 1024)
