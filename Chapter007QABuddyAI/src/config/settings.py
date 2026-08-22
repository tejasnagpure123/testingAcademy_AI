"""
QABuddy.ai — Central Configuration
All settings are loaded from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project root is two levels up from this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class Settings:
    """Application-wide settings loaded from environment variables."""

    # --- LLM ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- Qdrant ---
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION_NAME", "qabuddy")
    # Local embedded mode: set QDRANT_PATH to a directory path to use embedded Qdrant (no Docker needed)
    qdrant_path: str = os.getenv("QDRANT_PATH", str(PROJECT_ROOT / "qdrant_data"))

    # --- Embedding ---
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    reranker_model: str = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    use_gpu: bool = os.getenv("USE_GPU", "false").lower() == "true"
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))

    # --- JIRA ---
    jira_base_url: str = os.getenv("JIRA_BASE_URL", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_jql: str = os.getenv("JIRA_JQL", "project = QA ORDER BY updated DESC")

    # --- Data Paths ---
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("DATA_DIR", "data"))
    selenium_repo_url: str = os.getenv(
        "SELENIUM_REPO_URL",
        "https://github.com/PramodDutta/ATB13xSeleniumAdvanceFramework",
    )
    playwright_repo_url: str = os.getenv(
        "PLAYWRIGHT_REPO_URL",
        "https://github.com/PramodDutta/Advance-Playwright-Framework",
    )

    # --- Application ---
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    ui_port: int = int(os.getenv("UI_PORT", "8501"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Auth ---
    app_password: str = os.getenv("APP_PASSWORD", "qabuddy2026")

    # --- Retrieval ---
    hybrid_search_top_k: int = int(os.getenv("HYBRID_SEARCH_TOP_K", "15"))  # Candidates from hybrid search (15 for fast CPU rerank)
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "5"))                 # Final chunks after reranking
    max_context_tokens: int = 3000       # Max tokens sent to LLM

    # --- Chunking defaults (overridden per source type) ---
    default_chunk_size: int = 800        # tokens
    default_chunk_overlap: int = 120     # tokens

    # --- Source type identifiers ---
    SOURCE_TYPES: dict = field(default_factory=lambda: {
        "selenium_repo": "01_selenium_framework",
        "playwright_repo": "02_playwright_framework",
        "test_cases": "03_test_cases",
        "jira_tickets": "04_jira_tickets",
        "company_docs": "05_company_docs",
        "figma_designs": "06_figma_designs",
        "meeting_transcripts": "07_meeting_transcripts",
        "lucid_charts": "08_lucid_charts",
        "prd_docs": "09_prd_srs_brd_frd",
        "jenkins_logs": "10_jenkins_logs",
    })

    def get_data_path(self, source_type: str) -> Path:
        """Get the absolute path for a source type's data directory."""
        folder_name = self.SOURCE_TYPES.get(source_type, source_type)
        return self.data_dir / folder_name

    @property
    def glossary_path(self) -> Path:
        """Path to the QA domain glossary."""
        return Path(__file__).parent / "glossary.json"


# Singleton instance
settings = Settings()
