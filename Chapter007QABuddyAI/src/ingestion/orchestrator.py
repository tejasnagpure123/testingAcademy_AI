"""
QABuddy.ai — Ingestion Orchestrator
Master controller that coordinates parsing → cleaning → chunking → embedding → indexing
for all 10 data sources.
"""

import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from src.config.settings import settings

# Parsers
from src.ingestion.parsers.code_parser import parse_code_repository
from src.ingestion.parsers.csv_parser import parse_test_cases_directory
from src.ingestion.parsers.pdf_parser import parse_pdf_directory
from src.ingestion.parsers.jira_parser import (
    fetch_jira_tickets, save_tickets_to_disk, load_tickets_from_disk,
)
from src.ingestion.parsers.transcript_parser import parse_transcript_directory
from src.ingestion.parsers.log_parser import parse_log_directory
from src.ingestion.parsers.text_parser import parse_text_directory

# Chunkers
from src.ingestion.chunkers.code_chunker import chunk_code_units
from src.ingestion.chunkers.row_chunker import chunk_test_case_rows
from src.ingestion.chunkers.ticket_chunker import chunk_jira_tickets
from src.ingestion.chunkers.recursive_chunker import chunk_text_sections
from src.ingestion.chunkers.log_chunker import chunk_log_blocks

# Cleaners
from src.ingestion.cleaners.code_cleaner import clean_code
from src.ingestion.cleaners.text_cleaner import clean_text
from src.ingestion.cleaners.log_cleaner import clean_log

# Embedder
from src.ingestion.embedder import embed_texts, get_embedding_dimension


class IngestionOrchestrator:
    """
    Coordinates the full ingestion pipeline for all data sources.

    Usage:
        orchestrator = IngestionOrchestrator(vector_store)
        stats = orchestrator.ingest_all()
    """

    def __init__(self, vector_store=None):
        """
        Args:
            vector_store: QdrantVectorStore instance for indexing
        """
        self.vector_store = vector_store
        self.stats: Dict[str, int] = {}

    def ingest_all(self, sources: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Ingest all (or specified) data sources.

        Args:
            sources: Optional list of source types to ingest. If None, ingests all.

        Returns:
            Dictionary of {source_type: num_chunks_indexed}
        """
        all_sources = {
            "selenium_repo": self._ingest_selenium,
            "playwright_repo": self._ingest_playwright,
            "test_cases": self._ingest_test_cases,
            "jira_tickets": self._ingest_jira,
            "company_docs": self._ingest_company_docs,
            "meeting_transcripts": self._ingest_transcripts,
            "lucid_charts": self._ingest_lucid_charts,
            "prd_docs": self._ingest_prd_docs,
            "jenkins_logs": self._ingest_jenkins_logs,
        }

        targets = sources or list(all_sources.keys())

        logger.info(f"Starting ingestion for {len(targets)} sources: {targets}")
        start_time = time.time()

        for source in targets:
            if source not in all_sources:
                logger.warning(f"Unknown source type: {source}, skipping")
                continue

            logger.info(f"\n{'=' * 60}")
            logger.info(f"Ingesting: {source}")
            logger.info(f"{'=' * 60}")

            try:
                count = all_sources[source]()
                self.stats[source] = count
                logger.info(f"✓ {source}: {count} chunks indexed")
            except Exception as e:
                logger.error(f"✗ Failed to ingest {source}: {e}")
                self.stats[source] = 0

        elapsed = time.time() - start_time
        total = sum(self.stats.values())
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Ingestion complete: {total} total chunks in {elapsed:.1f}s")
        logger.info(f"Stats: {self.stats}")
        logger.info(f"{'=' * 60}")

        return self.stats

    # ─── Source-Specific Ingestion Methods ───────────────────────

    def _ingest_selenium(self) -> int:
        """Ingest Selenium framework repository."""
        data_path = settings.get_data_path("selenium_repo")
        if not data_path.exists() or not any(data_path.iterdir()):
            logger.warning(f"No data found in {data_path}. Skipping Selenium repo.")
            return 0

        # Parse → Clean → Chunk
        parsed_units = parse_code_repository(str(data_path), "selenium_repo")
        for unit in parsed_units:
            unit.content = clean_code(unit.content, unit.language)
        chunks = chunk_code_units(parsed_units)

        return self._embed_and_index(chunks, "selenium_repo")

    def _ingest_playwright(self) -> int:
        """Ingest Playwright framework repository."""
        data_path = settings.get_data_path("playwright_repo")
        if not data_path.exists() or not any(data_path.iterdir()):
            logger.warning(f"No data found in {data_path}. Skipping Playwright repo.")
            return 0

        parsed_units = parse_code_repository(str(data_path), "playwright_repo")
        for unit in parsed_units:
            unit.content = clean_code(unit.content, unit.language)
        chunks = chunk_code_units(parsed_units)

        return self._embed_and_index(chunks, "playwright_repo")

    def _ingest_test_cases(self) -> int:
        """Ingest test case CSV/XLSX files."""
        data_path = settings.get_data_path("test_cases")
        if not data_path.exists():
            logger.warning(f"No data found in {data_path}. Skipping test cases.")
            return 0

        parsed_rows = parse_test_cases_directory(str(data_path), "test_cases")
        for row in parsed_rows:
            row.content = clean_text(row.content, expand_abbreviations=True)
        chunks = chunk_test_case_rows(parsed_rows)

        return self._embed_and_index(chunks, "test_cases")

    def _ingest_jira(self) -> int:
        """Ingest JIRA tickets — from API if configured, else from disk."""
        data_path = settings.get_data_path("jira_tickets")

        tickets = []

        # Try live JIRA API first
        if settings.jira_base_url and settings.jira_api_token:
            logger.info("Fetching tickets from JIRA API...")
            tickets = fetch_jira_tickets(
                base_url=settings.jira_base_url,
                email=settings.jira_email,
                api_token=settings.jira_api_token,
                jql=settings.jira_jql,
            )
            # Save to disk for offline access
            if tickets:
                save_tickets_to_disk(tickets, str(data_path))
            else:
                logger.info("JIRA API returned 0 tickets. Checking disk for local tickets...")
                tickets = load_tickets_from_disk(str(data_path), "jira_tickets")
        else:
            logger.info("JIRA API not configured. Loading from disk...")
            tickets = load_tickets_from_disk(str(data_path), "jira_tickets")

        if not tickets:
            logger.warning("No JIRA tickets found. Skipping.")
            return 0

        for ticket in tickets:
            ticket.content = clean_text(ticket.content, expand_abbreviations=True)
        chunks = chunk_jira_tickets(tickets)

        return self._embed_and_index(chunks, "jira_tickets")

    def _ingest_company_docs(self) -> int:
        """Ingest company PDF and Markdown documents."""
        data_path = settings.get_data_path("company_docs")
        if not data_path.exists():
            logger.warning(f"No data found in {data_path}. Skipping company docs.")
            return 0

        # Parse PDFs
        pdf_sections = parse_pdf_directory(str(data_path), "company_docs")

        # Parse Markdown / text files
        text_sections = parse_text_directory(str(data_path), "company_docs")

        all_sections = pdf_sections + text_sections

        for section in all_sections:
            section.content = clean_text(section.content, expand_abbreviations=True)

        chunks = chunk_text_sections(all_sections, source_type="company_docs")

        return self._embed_and_index(chunks, "company_docs")

    def _ingest_transcripts(self) -> int:
        """Ingest meeting transcripts."""
        data_path = settings.get_data_path("meeting_transcripts")
        if not data_path.exists():
            return 0

        parsed = parse_transcript_directory(str(data_path), "meeting_transcripts")
        for seg in parsed:
            seg.content = clean_text(seg.content, expand_abbreviations=True)

        chunks = chunk_text_sections(parsed, source_type="meeting_transcripts")

        return self._embed_and_index(chunks, "meeting_transcripts")

    def _ingest_lucid_charts(self) -> int:
        """Ingest Lucid chart text exports."""
        data_path = settings.get_data_path("lucid_charts")
        if not data_path.exists():
            return 0

        parsed = parse_text_directory(str(data_path), "lucid_charts")
        for section in parsed:
            section.content = clean_text(section.content, expand_abbreviations=True)

        chunks = chunk_text_sections(parsed, source_type="lucid_charts")

        return self._embed_and_index(chunks, "lucid_charts")

    def _ingest_prd_docs(self) -> int:
        """Ingest PRD/SRS/BRD/FRD PDF documents."""
        data_path = settings.get_data_path("prd_docs")
        if not data_path.exists():
            return 0

        pdf_sections = parse_pdf_directory(str(data_path), "prd_docs")
        text_sections = parse_text_directory(str(data_path), "prd_docs")
        all_sections = pdf_sections + text_sections

        for section in all_sections:
            section.content = clean_text(section.content, expand_abbreviations=True)

        chunks = chunk_text_sections(all_sections, source_type="prd_docs")

        return self._embed_and_index(chunks, "prd_docs")

    def _ingest_jenkins_logs(self) -> int:
        """Ingest Jenkins build logs and test results."""
        data_path = settings.get_data_path("jenkins_logs")
        if not data_path.exists():
            return 0

        parsed_blocks = parse_log_directory(str(data_path), "jenkins_logs")
        for block in parsed_blocks:
            block.content = clean_log(block.content)

        chunks = chunk_log_blocks(parsed_blocks)

        return self._embed_and_index(chunks, "jenkins_logs")

    # ─── Common Embedding & Indexing ────────────────────────────

    def _embed_and_index(self, chunks: list, source_type: str) -> int:
        """
        Embed chunks and store in vector database.

        Args:
            chunks: List of Chunk objects
            source_type: Source type identifier

        Returns:
            Number of chunks indexed
        """
        if not chunks:
            return 0

        # In dry-run mode, skip embedding and indexing
        if self.vector_store is None:
            logger.info(f"[DRY-RUN] Would embed and index {len(chunks)} chunks for {source_type}")
            return len(chunks)

        # Extract text content for embedding
        texts = [chunk.content for chunk in chunks]

        # Embed in batches
        logger.info(f"Embedding {len(texts)} chunks for {source_type}...")
        embeddings = embed_texts(
            texts,
            model_name=settings.embedding_model,
            use_gpu=settings.use_gpu,
            batch_size=settings.embedding_batch_size,
        )

        # Store in vector database
        logger.info(f"Indexing {len(embeddings)} vectors in Qdrant...")
        self.vector_store.upsert_chunks(chunks, embeddings, source_type)

        # Add ingestion timestamp to metadata
        timestamp = datetime.utcnow().isoformat() + "Z"
        for chunk in chunks:
            chunk.metadata["ingested_at"] = timestamp

        return len(chunks)
