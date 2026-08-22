"""
QABuddy.ai — Text Cleaner
Normalizes text content: handles Unicode, expands abbreviations using the
QA domain glossary, cleans up formatting artifacts.
"""

import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


# Load glossary once at module level
_glossary = None


def _load_glossary() -> Dict:
    """Lazy-load the QA domain glossary."""
    global _glossary
    if _glossary is None:
        glossary_path = Path(__file__).parent.parent.parent / "config" / "glossary.json"
        if glossary_path.exists():
            try:
                _glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
                logger.debug(f"Loaded glossary with {len(_glossary.get('abbreviations', {}))} abbreviations")
            except Exception as e:
                logger.warning(f"Failed to load glossary: {e}")
                _glossary = {"abbreviations": {}, "synonyms": {}, "domain_terms": []}
        else:
            _glossary = {"abbreviations": {}, "synonyms": {}, "domain_terms": []}
    return _glossary


def clean_text(content: str, expand_abbreviations: bool = True) -> str:
    """
    Clean and normalize text content.

    Args:
        content: Raw text content
        expand_abbreviations: Whether to expand QA domain abbreviations

    Returns:
        Cleaned text content
    """
    if not content:
        return ""

    # Normalize Unicode
    content = unicodedata.normalize("NFKC", content)

    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove leading/trailing whitespace per line
    lines = [line.strip() for line in content.split("\n")]
    content = "\n".join(lines)

    # Remove common PDF artifacts
    content = _clean_pdf_artifacts(content)

    # Remove URLs that are very long (data URIs, base64)
    content = re.sub(r"data:[a-zA-Z/]+;base64,[A-Za-z0-9+/=]{50,}", "[DATA_URI]", content)

    # Expand abbreviations for better retrieval
    if expand_abbreviations:
        content = _expand_abbreviations(content)

    # Remove excessive whitespace within lines
    content = re.sub(r"[ \t]{3,}", "  ", content)

    return content.strip()


def _clean_pdf_artifacts(content: str) -> str:
    """Remove common PDF extraction artifacts."""
    # Remove page numbers
    content = re.sub(r"^\s*Page \d+(\s+of\s+\d+)?\s*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"^\s*\d+\s*$", "", content, flags=re.MULTILINE)

    # Remove repeated header/footer patterns (same text appearing every ~page)
    # This is a heuristic — look for short lines that repeat
    lines = content.split("\n")
    if len(lines) > 20:
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if 5 < len(stripped) < 80:  # Typical header/footer length
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        # Remove lines that appear 3+ times (likely headers/footers)
        repeated = {line for line, count in line_counts.items() if count >= 3}
        if repeated:
            lines = [line for line in lines if line.strip() not in repeated]
            content = "\n".join(lines)

    # Remove ligature artifacts
    content = content.replace("ﬁ", "fi").replace("ﬂ", "fl")
    content = content.replace("ﬀ", "ff").replace("ﬃ", "ffi")

    return content


def _expand_abbreviations(content: str) -> str:
    """
    Expand QA domain abbreviations so both forms are searchable.
    E.g., 'RTM' becomes 'RTM (Requirements Traceability Matrix)'
    Only expands on first occurrence to avoid bloat.
    """
    glossary = _load_glossary()
    abbreviations = glossary.get("abbreviations", {})

    expanded = set()  # Track already expanded abbreviations

    for abbr, full_form in abbreviations.items():
        if abbr in expanded:
            continue

        # Only expand standalone abbreviations (word boundaries)
        pattern = rf"\b{re.escape(abbr)}\b"
        match = re.search(pattern, content)
        if match:
            # Only expand first occurrence
            replacement = f"{abbr} ({full_form})"
            content = re.sub(pattern, replacement, content, count=1)
            expanded.add(abbr)

    return content
