"""
QABuddy.ai — Parsers Package
Documents the available parsers. Imports are intentionally kept lazy
(not executed at package import time) to avoid loading heavy dependencies
(pandas, loguru, jira) during test collection.

To use a parser, import it directly:
    from src.ingestion.parsers.code_parser import parse_code_repository
    from src.ingestion.parsers.csv_parser import parse_test_cases
"""

# Lazy import registry — do NOT eagerly import here.
# The orchestrator imports parsers by name; tests import them directly.
# This avoids hanging pytest collection due to pandas/jira/PyMuPDF loading.

__all__ = [
    "parse_code_repository",
    "parse_test_cases",
    "parse_test_cases_directory",
    "parse_pdf",
    "parse_pdf_directory",
    "parse_text_file",
    "parse_text_directory",
    "fetch_jira_tickets",
    "save_tickets_to_disk",
    "load_tickets_from_disk",
    "parse_transcript",
    "parse_transcript_directory",
    "parse_log_file",
    "parse_log_directory",
]

