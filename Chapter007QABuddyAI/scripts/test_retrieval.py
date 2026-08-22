"""
QABuddy.ai — Retrieval Quality Test Script
Quick smoke test to verify hybrid search and reranking quality.

Usage:
    python scripts/test_retrieval.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.config.settings import settings
from src.retrieval.vector_store import QdrantVectorStore
from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.reranker import rerank


# Test questions with expected source types
TEST_QUESTIONS = [
    {
        "question": "How do I set up the Selenium base test class?",
        "expected_sources": ["selenium_repo"],
    },
    {
        "question": "Show me all login-related test cases",
        "expected_sources": ["test_cases", "selenium_repo"],
    },
    {
        "question": "What were the recent bugs in the checkout flow?",
        "expected_sources": ["jira_tickets"],
    },
    {
        "question": "What does the PRD say about user authentication?",
        "expected_sources": ["prd_docs", "company_docs"],
    },
    {
        "question": "How to run tests in headless mode with Playwright?",
        "expected_sources": ["playwright_repo"],
    },
    {
        "question": "Why is test TC-2041 flaky?",
        "expected_sources": ["jenkins_logs", "test_cases"],
    },
    {
        "question": "What is the Page Object Model pattern in our framework?",
        "expected_sources": ["selenium_repo", "playwright_repo", "company_docs"],
    },
]


def main():
    logger.info("=" * 60)
    logger.info("QABuddy.ai — Retrieval Quality Test")
    logger.info("=" * 60)

    # Connect to Qdrant
    try:
        vector_store = QdrantVectorStore()
        info = vector_store.get_collection_info()
        logger.info(f"Connected to Qdrant: {info}")

        if info.get("points_count", 0) == 0:
            logger.warning("Collection is empty! Run ingestion first: python scripts/ingest_all.py")
            return
    except Exception as e:
        logger.error(f"Cannot connect to Qdrant: {e}")
        logger.info("Make sure Qdrant is running (docker run -p 6333:6333 qdrant/qdrant)")
        return

    searcher = HybridSearcher(vector_store)

    # Run test questions
    passed = 0
    total = len(TEST_QUESTIONS)

    for i, test in enumerate(TEST_QUESTIONS, 1):
        question = test["question"]
        expected = test["expected_sources"]

        logger.info(f"\n--- Test {i}/{total} ---")
        logger.info(f"Q: {question}")
        logger.info(f"Expected sources: {expected}")

        try:
            # Search
            results = searcher.search(query=question, top_k=20)

            if not results:
                logger.warning("  No results found!")
                continue

            # Rerank
            reranked = rerank(query=question, candidates=results, top_k=5)

            # Check source types
            found_sources = set()
            for r in reranked:
                source = r.get("metadata", {}).get("source_type", "unknown")
                found_sources.add(source)

            # Display top results
            for j, r in enumerate(reranked[:3], 1):
                meta = r.get("metadata", {})
                score = r.get("rerank_score", r.get("score", 0))
                source = meta.get("source_type", "?")
                title = meta.get("title", "?")
                text_preview = r.get("text", "")[:100]
                logger.info(f"  [{j}] score={score:.3f} | {source} | {title}")
                logger.info(f"      {text_preview}...")

            # Check if any expected source was found
            match = bool(found_sources & set(expected))
            if match:
                logger.info(f"  ✅ PASS — found: {found_sources & set(expected)}")
                passed += 1
            else:
                logger.warning(f"  ❌ FAIL — found: {found_sources}, expected: {expected}")

        except Exception as e:
            logger.error(f"  Error: {e}")

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Results: {passed}/{total} passed ({100 * passed / total:.0f}%)")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
