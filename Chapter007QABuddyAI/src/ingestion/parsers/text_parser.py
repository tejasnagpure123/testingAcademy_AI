"""
QABuddy.ai — Text Parser
Generic parser for Markdown files, Lucid chart exports, and plain text documents.
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
import re
from loguru import logger


@dataclass
class ParsedTextSection:
    """A parsed section from a text/markdown document."""
    content: str
    file_path: str
    section_index: int
    section_title: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_text_file(file_path: str, source_type: str) -> List[ParsedTextSection]:
    """
    Parse a text or markdown file into sections.

    Args:
        file_path: Path to the text file
        source_type: Source identifier

    Returns:
        List of ParsedTextSection objects
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    ext = path.suffix.lower()

    if ext in (".md", ".markdown"):
        return _parse_markdown(content, str(file_path), source_type)
    else:
        return _parse_plain_text(content, str(file_path), source_type)


def parse_text_directory(dir_path: str, source_type: str) -> List[ParsedTextSection]:
    """Parse all text files in a directory."""
    directory = Path(dir_path)
    if not directory.exists():
        return []

    all_sections = []
    for file_path in directory.rglob("*"):
        if file_path.suffix.lower() in (".md", ".markdown", ".txt", ".text", ".rst"):
            sections = parse_text_file(str(file_path), source_type)
            all_sections.extend(sections)

    return all_sections


def _parse_markdown(content: str, file_path: str, source_type: str) -> List[ParsedTextSection]:
    """Parse markdown into heading-based sections."""
    # Split by headings (# ## ### etc.)
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(content))

    sections = []

    if matches:
        for i, match in enumerate(matches):
            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()
            start = match.start()

            # End is at the next heading or end of file
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(content)

            section_content = content[start:end].strip()

            if section_content and len(section_content) > 10:
                sections.append(ParsedTextSection(
                    content=section_content,
                    file_path=file_path,
                    section_index=i,
                    section_title=heading_text,
                    metadata={
                        "source_type": source_type,
                        "heading_level": heading_level,
                        "document_name": Path(file_path).stem,
                    },
                ))
    else:
        # No headings found — treat as single section
        sections.append(ParsedTextSection(
            content=content.strip(),
            file_path=file_path,
            section_index=0,
            section_title=Path(file_path).stem,
            metadata={
                "source_type": source_type,
                "document_name": Path(file_path).stem,
            },
        ))

    return sections


def _parse_plain_text(content: str, file_path: str, source_type: str) -> List[ParsedTextSection]:
    """Parse plain text into paragraph-based sections."""
    # Split by double newlines (paragraph boundaries)
    paragraphs = re.split(r"\n\s*\n", content)
    sections = []

    for i, para in enumerate(paragraphs):
        text = para.strip()
        if text and len(text) > 20:
            # Use first line as title (truncated)
            first_line = text.split("\n")[0][:80]

            sections.append(ParsedTextSection(
                content=text,
                file_path=file_path,
                section_index=i,
                section_title=first_line,
                metadata={
                    "source_type": source_type,
                    "document_name": Path(file_path).stem,
                },
            ))

    return sections
