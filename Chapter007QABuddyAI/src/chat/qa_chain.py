"""
QABuddy.ai — QA Chain
Full RAG chain: query → embed → hybrid search → rerank → generate cited answer.
This is the core pipeline that powers the chatbot.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

from src.config.settings import settings
from src.retrieval.hybrid_search import HybridSearcher
from src.retrieval.reranker import rerank
from src.chat.prompt_templates import SYSTEM_PROMPT, build_qa_prompt
from src.chat.llm_client import LLMClient


@dataclass
class QAResponse:
    """Response from the QA chain."""
    answer: str
    sources: List[Dict[str, Any]]
    query: str
    num_chunks_retrieved: int
    num_chunks_reranked: int


class QAChain:
    """
    Full RAG chain for QABuddy.ai.

    Flow:
    1. User asks a question
    2. Question is embedded (dense + sparse)
    3. Hybrid search retrieves top-50 candidates
    4. Cross-encoder reranks to top-5
    5. LLM generates a cited answer from the top-5 chunks
    """

    def __init__(
        self,
        searcher: HybridSearcher,
        llm_client: Optional[LLMClient] = None,
    ):
        self.searcher = searcher
        self.llm_client = llm_client or LLMClient()

    def ask(
        self,
        question: str,
        source_filter: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> QAResponse:
        """
        Ask a question and get a cited answer.

        Args:
            question: User's question
            source_filter: Optional filter by source_type
            chat_history: Optional conversation history for multi-turn

        Returns:
            QAResponse with answer, sources, and metadata
        """
        logger.info(f"QA Chain: Processing question: '{question[:80]}...'")

        # Step 1: Hybrid search
        search_results = self.searcher.search(
            query=question,
            top_k=settings.hybrid_search_top_k,
            source_filter=source_filter,
        )
        logger.info(f"  Step 1: Retrieved {len(search_results)} candidates")

        if not search_results:
            return QAResponse(
                answer="I couldn't find any relevant information in my knowledge base for your question. "
                       "Please try rephrasing or check if the relevant data has been ingested.",
                sources=[],
                query=question,
                num_chunks_retrieved=0,
                num_chunks_reranked=0,
            )

        # Step 2: Rerank
        reranked = rerank(
            query=question,
            candidates=search_results,
            top_k=settings.rerank_top_k,
            model_name=settings.reranker_model,
        )
        logger.info(f"  Step 2: Reranked to {len(reranked)} results")

        # Step 3: Build prompt
        user_prompt = build_qa_prompt(question, reranked)

        # Step 4: Generate answer
        logger.info("  Step 3: Generating answer...")
        answer = self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            chat_history=chat_history,
        )

        # Extract source references
        sources = [
            {
                "source_type": r.get("metadata", {}).get("source_type", ""),
                "source_file": r.get("metadata", {}).get("source_file", ""),
                "title": r.get("metadata", {}).get("title", ""),
                "ticket_key": r.get("metadata", {}).get("ticket_key", ""),
                "score": r.get("rerank_score", r.get("score", 0)),
            }
            for r in reranked
        ]

        logger.info(f"  Answer generated ({len(answer)} chars, {len(sources)} sources)")

        return QAResponse(
            answer=answer,
            sources=sources,
            query=question,
            num_chunks_retrieved=len(search_results),
            num_chunks_reranked=len(reranked),
        )
