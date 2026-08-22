"""
QABuddy.ai — Log Parser
Parses Jenkins build logs and test result files.
Splits logs into logical blocks by build/stage boundaries, preserving stack traces.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ParsedLogBlock:
    """A parsed block from a Jenkins log or test result file."""
    content: str
    file_path: str
    block_index: int
    block_type: str  # "build_info", "test_result", "error", "stack_trace", "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


# Patterns that indicate log block boundaries
BLOCK_BOUNDARY_PATTERNS = [
    re.compile(r"^={3,}", re.MULTILINE),                    # === separators
    re.compile(r"^-{3,}", re.MULTILINE),                    # --- separators
    re.compile(r"^\[Pipeline\]", re.MULTILINE),              # Jenkins pipeline steps
    re.compile(r"^Started by", re.MULTILINE),                # Build start
    re.compile(r"^Finished:", re.MULTILINE),                 # Build finish
    re.compile(r"^Running on", re.MULTILINE),                # Agent info
    re.compile(r"^Stage:", re.MULTILINE),                    # Stage markers
    re.compile(r"^\[INFO\] ----", re.MULTILINE),             # Maven separators
    re.compile(r"^BUILD (SUCCESS|FAILURE)", re.MULTILINE),   # Build result
    re.compile(r"^Tests run:", re.MULTILINE),                # Test summary
    re.compile(r"^FAILED TESTS", re.MULTILINE),              # Failed tests section
]

# Patterns to detect error/failure blocks
ERROR_PATTERNS = [
    re.compile(r"(?:Exception|Error|FAILURE|FAILED|ERROR)", re.IGNORECASE),
    re.compile(r"at [\w.]+\([\w.]+:\d+\)"),  # Java stack trace
    re.compile(r"Traceback \(most recent call last\)"),  # Python stack trace
    re.compile(r"AssertionError|AssertionFailure"),
]

# ANSI color code pattern
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def parse_log_file(file_path: str, source_type: str = "jenkins_logs") -> List[ParsedLogBlock]:
    """
    Parse a Jenkins log file into logical blocks.

    Args:
        file_path: Path to the log file
        source_type: Source identifier

    Returns:
        List of ParsedLogBlock objects
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Log file not found: {file_path}")
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    # Clean ANSI codes
    content = ANSI_PATTERN.sub("", content)

    # Split into logical blocks
    blocks = _split_into_blocks(content, str(file_path), source_type)

    logger.info(f"Parsed {len(blocks)} log blocks from {path.name}")
    return blocks


def parse_log_directory(dir_path: str, source_type: str = "jenkins_logs") -> List[ParsedLogBlock]:
    """Parse all log files in a directory."""
    directory = Path(dir_path)
    if not directory.exists():
        return []

    all_blocks = []
    for file_path in directory.rglob("*"):
        if file_path.suffix.lower() in (".log", ".txt", ".text", ".out", ".xml"):
            blocks = parse_log_file(str(file_path), source_type)
            all_blocks.extend(blocks)

    return all_blocks


def _split_into_blocks(content: str, file_path: str, source_type: str) -> List[ParsedLogBlock]:
    """Split log content into logical blocks based on boundary patterns."""
    lines = content.split("\n")
    blocks = []
    current_block = []
    current_start = 0

    for i, line in enumerate(lines):
        is_boundary = any(pattern.search(line) for pattern in BLOCK_BOUNDARY_PATTERNS)

        if is_boundary and current_block:
            # Save current block
            block_content = "\n".join(current_block).strip()
            if block_content and len(block_content) > 20:
                block_type = _classify_block(block_content)
                blocks.append(ParsedLogBlock(
                    content=block_content,
                    file_path=file_path,
                    block_index=len(blocks),
                    block_type=block_type,
                    metadata={
                        "source_type": source_type,
                        "log_file": Path(file_path).stem,
                        "has_error": block_type in ("error", "stack_trace"),
                    },
                ))
            current_block = [line]
            current_start = i
        else:
            current_block.append(line)

    # Save last block
    if current_block:
        block_content = "\n".join(current_block).strip()
        if block_content and len(block_content) > 20:
            block_type = _classify_block(block_content)
            blocks.append(ParsedLogBlock(
                content=block_content,
                file_path=file_path,
                block_index=len(blocks),
                block_type=block_type,
                metadata={
                    "source_type": source_type,
                    "log_file": Path(file_path).stem,
                    "has_error": block_type in ("error", "stack_trace"),
                },
            ))

    # If no boundaries found, split by size
    if len(blocks) <= 1 and len(content) > 2000:
        blocks = _split_by_size(content, file_path, source_type)

    return blocks


def _split_by_size(content: str, file_path: str, source_type: str, max_lines: int = 50) -> List[ParsedLogBlock]:
    """Fall back to splitting by line count when no boundaries are found."""
    lines = content.split("\n")
    blocks = []

    for i in range(0, len(lines), max_lines):
        chunk = lines[i:i + max_lines]
        block_content = "\n".join(chunk).strip()
        if block_content:
            block_type = _classify_block(block_content)
            blocks.append(ParsedLogBlock(
                content=block_content,
                file_path=file_path,
                block_index=len(blocks),
                block_type=block_type,
                metadata={
                    "source_type": source_type,
                    "log_file": Path(file_path).stem,
                    "has_error": block_type in ("error", "stack_trace"),
                },
            ))

    return blocks


def _classify_block(content: str) -> str:
    """Classify a log block by its content."""
    content_lower = content.lower()

    if "traceback" in content_lower or re.search(r"at [\w.]+\([\w.]+:\d+\)", content):
        return "stack_trace"

    if "tests run:" in content_lower or "test result" in content_lower:
        return "test_result"

    if "started by" in content_lower or "build #" in content_lower:
        return "build_info"

    if any(pattern.search(content) for pattern in ERROR_PATTERNS):
        return "error"

    return "general"
