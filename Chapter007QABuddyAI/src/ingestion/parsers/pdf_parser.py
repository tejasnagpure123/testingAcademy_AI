"""
QABuddy.ai — PDF Parser
Layout-aware PDF parsing using PyMuPDF (fitz).
Extracts text preserving structure: headings, tables, paragraphs.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from loguru import logger

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not installed. PDF parsing will not be available.")


@dataclass
class ParsedPDFSection:
    """A parsed section from a PDF document."""
    content: str
    file_path: str
    page_number: int
    section_title: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_pdf(file_path: str, source_type: str) -> List[ParsedPDFSection]:
    """
    Parse a PDF file into sections, preserving document structure.

    Args:
        file_path: Path to the PDF file
        source_type: Source identifier

    Returns:
        List of ParsedPDFSection objects
    """
    if fitz is None:
        logger.error("PyMuPDF is required for PDF parsing. Install with: pip install PyMuPDF")
        return []

    path = Path(file_path)
    if not path.exists():
        logger.warning(f"PDF file not found: {file_path}")
        return []

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {file_path}: {e}")
        return []

    sections = []
    current_section_title = path.stem
    current_section_text = []
    current_page = 1

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Extract text blocks with position info
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        for block in blocks:
            if block.get("type") != 0:  # Skip non-text blocks (images)
                continue

            for line in block.get("lines", []):
                line_text = ""
                is_heading = False
                max_font_size = 0

                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    font_size = span.get("size", 12)
                    font_flags = span.get("flags", 0)

                    if text:
                        line_text += text + " "
                        max_font_size = max(max_font_size, font_size)

                        # Detect headings: bold text or larger font size
                        if font_size > 13 or (font_flags & 2**4):  # Bold flag
                            is_heading = True

                line_text = line_text.strip()
                if not line_text:
                    continue

                # If we detect a heading, save the current section and start a new one
                if is_heading and len(line_text) < 200:
                    if current_section_text:
                        section_content = "\n".join(current_section_text).strip()
                        if section_content:
                            sections.append(ParsedPDFSection(
                                content=section_content,
                                file_path=str(file_path),
                                page_number=current_page,
                                section_title=current_section_title,
                                metadata={
                                    "source_type": source_type,
                                    "document_name": path.stem,
                                },
                            ))
                    current_section_title = line_text
                    current_section_text = [f"## {line_text}"]
                    current_page = page_num + 1
                else:
                    current_section_text.append(line_text)

        # Also extract tables from the page
        try:
            tables = page.find_tables()
            for table in tables:
                table_data = table.extract()
                table_text = _format_table(table_data)
                if table_text:
                    current_section_text.append(f"\n[Table]\n{table_text}\n")
        except Exception:
            pass  # Table extraction not available in older PyMuPDF versions

    # Save the last section
    if current_section_text:
        section_content = "\n".join(current_section_text).strip()
        if section_content:
            sections.append(ParsedPDFSection(
                content=section_content,
                file_path=str(file_path),
                page_number=current_page,
                section_title=current_section_title,
                metadata={
                    "source_type": source_type,
                    "document_name": path.stem,
                },
            ))

    doc.close()
    logger.info(f"Parsed {len(sections)} sections from {path.name}")
    return sections


def parse_pdf_directory(dir_path: str, source_type: str) -> List[ParsedPDFSection]:
    """Parse all PDF files in a directory."""
    directory = Path(dir_path)
    if not directory.exists():
        logger.warning(f"Directory not found: {dir_path}")
        return []

    all_sections = []
    for file_path in directory.rglob("*.pdf"):
        sections = parse_pdf(str(file_path), source_type)
        all_sections.extend(sections)

    return all_sections


def _format_table(table_data: List[List[str]]) -> str:
    """Format extracted table data into readable text."""
    if not table_data:
        return ""

    formatted_rows = []
    for row in table_data:
        cells = [str(cell).strip() if cell else "" for cell in row]
        if any(cells):
            formatted_rows.append(" | ".join(cells))

    return "\n".join(formatted_rows)
