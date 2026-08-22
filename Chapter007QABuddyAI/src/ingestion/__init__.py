"""
QABuddy.ai — Ingestion Package
Import orchestrator explicitly when needed:
    from src.ingestion.orchestrator import IngestionOrchestrator
Lazy import avoids loading heavy ML dependencies (FlagEmbedding, sentence-transformers)
at test collection time.
"""
# No eager imports here — use direct imports in your code.
