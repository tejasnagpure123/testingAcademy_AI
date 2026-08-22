"""
QABuddy.ai — Code Cleaner
Normalizes code content: strips excessive comments, normalizes whitespace,
preserves docstrings and meaningful comments.
"""

import re
from typing import Optional


def clean_code(content: str, language: str = "java") -> str:
    """
    Clean code content while preserving semantic meaning.

    Args:
        content: Raw code content
        language: Programming language

    Returns:
        Cleaned code content
    """
    if not content:
        return ""

    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Normalize whitespace (tabs to 4 spaces)
    content = content.replace("\t", "    ")

    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in content.split("\n")]
    content = "\n".join(lines)

    # Language-specific cleaning
    if language in ("java", "javascript", "typescript"):
        content = _clean_c_style(content)
    elif language == "python":
        content = _clean_python(content)

    return content.strip()


def _clean_c_style(content: str) -> str:
    """Clean C-style code (Java, JS, TS)."""
    # Remove single-line comments that are just separators (e.g., // ------)
    content = re.sub(r"//\s*[-=*]{5,}.*$", "", content, flags=re.MULTILINE)

    # Remove auto-generated comments (IDE boilerplate)
    content = re.sub(
        r"/\*\*?\s*\n\s*\*\s*Created by.*?\*/",
        "",
        content,
        flags=re.DOTALL,
    )

    # Remove TODO/FIXME/HACK comments (noise for retrieval)
    # Keep them as they may be relevant for QA
    # content = re.sub(r"//\s*(TODO|FIXME|HACK|XXX).*$", "", content, flags=re.MULTILINE)

    return content


def _clean_python(content: str) -> str:
    """Clean Python code."""
    # Remove separator comments
    content = re.sub(r"#\s*[-=*]{5,}.*$", "", content, flags=re.MULTILINE)

    return content
