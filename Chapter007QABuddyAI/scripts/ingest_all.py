"""
QABuddy.ai — Full Ingestion Script
One-shot script to ingest all data sources into Qdrant.

Usage:
    python scripts/ingest_all.py                   # Ingest all sources
    python scripts/ingest_all.py --sources selenium_repo test_cases  # Specific sources
    python scripts/ingest_all.py --recreate        # Recreate collection first
    python scripts/ingest_all.py --dry-run         # Parse & chunk without indexing
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.config.settings import settings


def main():
    parser = argparse.ArgumentParser(description="QABuddy.ai — Data Ingestion")
    parser.add_argument(
        "--sources", nargs="+", default=None,
        help="Specific sources to ingest (e.g., selenium_repo test_cases)",
    )
    parser.add_argument(
        "--recreate", action="store_true",
        help="Delete and recreate the vector collection before ingesting",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and chunk data without embedding or indexing",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("QABuddy.ai — Full Data Ingestion")
    logger.info("=" * 60)

    start_time = time.time()

    # Initialize vector store (unless dry run)
    vector_store = None
    if not args.dry_run:
        from src.retrieval.vector_store import QdrantVectorStore

        logger.info(f"Connecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}...")
        vector_store = QdrantVectorStore()
        vector_store.create_collection(recreate=args.recreate)
        logger.info("✅ Qdrant ready")
    else:
        logger.info("🔍 DRY RUN mode — will parse & chunk but NOT embed/index")

    # Run ingestion
    from src.ingestion.orchestrator import IngestionOrchestrator

    orchestrator = IngestionOrchestrator(vector_store=vector_store)
    stats = orchestrator.ingest_all(sources=args.sources)

    # Print summary
    elapsed = time.time() - start_time
    total = sum(stats.values())

    logger.info("\n" + "=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    for source, count in stats.items():
        emoji = "✅" if count > 0 else "⬜"
        logger.info(f"  {emoji} {source}: {count} chunks")
    logger.info(f"\n  Total: {total} chunks in {elapsed:.1f}s")

    if args.dry_run:
        logger.info("\n  ⚠️  DRY RUN — nothing was indexed")
    else:
        # Verify
        if vector_store:
            info = vector_store.get_collection_info()
            logger.info(f"  📦 Qdrant collection: {info}")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
