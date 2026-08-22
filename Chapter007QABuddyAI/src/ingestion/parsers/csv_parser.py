"""
QABuddy.ai — CSV/XLSX Parser
Parses test case spreadsheets (CSV and XLSX) into structured records.
Each row becomes a self-contained, searchable text block.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

import pandas as pd
from loguru import logger


@dataclass
class ParsedTestCase:
    """A single parsed test case row from a spreadsheet."""
    content: str            # Combined text representation
    file_path: str
    row_index: int
    test_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# Common column name mappings (handles variations in column naming)
COLUMN_ALIASES = {
    "test_id": ["test_id", "tc_id", "testcase_id", "id", "test id", "tc id", "test case id", "s.no", "sr", "sr.no"],
    "module": ["module", "feature", "area", "component", "section"],
    "title": ["title", "test_name", "test case", "test case name", "summary", "test_case_name", "name", "description"],
    "priority": ["priority", "severity", "importance"],
    "type": ["type", "test_type", "category"],
    "preconditions": ["preconditions", "prerequisites", "pre-conditions", "setup"],
    "steps": ["steps", "test_steps", "procedure", "test steps", "actions"],
    "expected_result": ["expected_result", "expected", "expected result", "expected outcome", "expected_output"],
    "actual_result": ["actual_result", "actual", "actual result", "actual outcome"],
    "status": ["status", "result", "pass/fail", "execution_status"],
    "tags": ["tags", "labels", "keywords"],
    "assignee": ["assignee", "assigned_to", "tester", "owner"],
}


def parse_test_cases(file_path: str, source_type: str = "test_cases") -> List[ParsedTestCase]:
    """
    Parse a CSV or XLSX file containing test cases.

    Args:
        file_path: Path to the CSV/XLSX file
        source_type: Source identifier

    Returns:
        List of ParsedTestCase objects, one per row
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Test case file not found: {file_path}")
        return []

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, engine="openpyxl")
        elif path.suffix.lower() == ".csv":
            # Try multiple encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error(f"Could not read CSV with any encoding: {file_path}")
                return []
        else:
            logger.warning(f"Unsupported file format: {path.suffix}")
            return []
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []

    # Normalize column names
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]

    # Map columns to canonical names
    col_map = _resolve_columns(df.columns.tolist())
    logger.info(f"Resolved columns: {col_map}")

    parsed_cases = []
    for idx, row in df.iterrows():
        try:
            test_case = _row_to_test_case(row, idx, col_map, str(file_path), source_type)
            if test_case:
                parsed_cases.append(test_case)
        except Exception as e:
            logger.warning(f"Failed to parse row {idx} in {file_path}: {e}")

    logger.info(f"Parsed {len(parsed_cases)} test cases from {path.name}")
    return parsed_cases


def parse_test_cases_directory(dir_path: str, source_type: str = "test_cases") -> List[ParsedTestCase]:
    """Parse all CSV/XLSX files in a directory."""
    directory = Path(dir_path)
    if not directory.exists():
        logger.warning(f"Directory not found: {dir_path}")
        return []

    all_cases = []
    for file_path in directory.glob("*"):
        if file_path.suffix.lower() in (".csv", ".xlsx", ".xls"):
            cases = parse_test_cases(str(file_path), source_type)
            all_cases.extend(cases)

    return all_cases


def _resolve_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """Map actual column names to canonical names using aliases."""
    col_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        col_map[canonical] = None
        for alias in aliases:
            normalized = alias.strip().lower().replace(" ", "_")
            if normalized in columns:
                col_map[canonical] = normalized
                break
    return col_map


def _row_to_test_case(
    row: pd.Series,
    idx: int,
    col_map: Dict[str, Optional[str]],
    file_path: str,
    source_type: str,
) -> Optional[ParsedTestCase]:
    """Convert a DataFrame row to a ParsedTestCase."""

    def get_val(canonical: str) -> str:
        col = col_map.get(canonical)
        if col and col in row.index:
            val = row[col]
            if pd.notna(val):
                return str(val).strip()
        return ""

    # Build a combined text representation
    parts = []

    test_id = get_val("test_id") or f"ROW-{idx + 1}"
    parts.append(f"Test ID: {test_id}")

    title = get_val("title")
    if title:
        parts.append(f"Title: {title}")

    module = get_val("module")
    if module:
        parts.append(f"Module: {module}")

    priority = get_val("priority")
    if priority:
        parts.append(f"Priority: {priority}")

    tc_type = get_val("type")
    if tc_type:
        parts.append(f"Type: {tc_type}")

    preconditions = get_val("preconditions")
    if preconditions:
        parts.append(f"Preconditions: {preconditions}")

    steps = get_val("steps")
    if steps:
        parts.append(f"Steps: {steps}")

    expected = get_val("expected_result")
    if expected:
        parts.append(f"Expected Result: {expected}")

    status = get_val("status")
    if status:
        parts.append(f"Status: {status}")

    tags = get_val("tags")
    if tags:
        parts.append(f"Tags: {tags}")

    content = "\n".join(parts)

    # Skip rows with minimal content (likely header rows or empty)
    if len(content.strip()) < 20:
        return None

    metadata = {
        "source_type": source_type,
        "test_id": test_id,
        "module": module,
        "priority": priority,
        "status": status,
        "tags": tags,
    }

    return ParsedTestCase(
        content=content,
        file_path=file_path,
        row_index=idx,
        test_id=test_id,
        metadata=metadata,
    )
