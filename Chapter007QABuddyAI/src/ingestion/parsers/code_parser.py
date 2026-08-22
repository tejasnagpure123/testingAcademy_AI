"""
QABuddy.ai — Code Parser
AST-aware parsing for Java (Selenium) and JavaScript/TypeScript (Playwright) source files.
Extracts classes, methods, and functions as logical units.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ParsedCodeUnit:
    """A single parsed code unit (class, method, function, or file-level block)."""
    content: str
    file_path: str
    language: str
    unit_type: str  # "class", "method", "function", "module"
    unit_name: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# File extensions to language mapping
LANGUAGE_MAP = {
    ".java": "java",
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".xml": "xml",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".properties": "properties",
    ".cfg": "config",
    ".ini": "config",
    ".gradle": "groovy",
}

# Files/dirs to skip during parsing
SKIP_PATTERNS = {
    "node_modules", ".git", "__pycache__", ".idea", ".vscode",
    "target", "build", "dist", ".gradle", "venv", ".env",
    "package-lock.json", "yarn.lock",
}


def parse_code_repository(repo_path: str, source_type: str) -> List[ParsedCodeUnit]:
    """
    Parse an entire code repository into logical code units.

    Args:
        repo_path: Path to the repository root directory
        source_type: Source identifier (e.g., "selenium_repo")

    Returns:
        List of ParsedCodeUnit objects
    """
    repo = Path(repo_path)
    if not repo.exists():
        logger.warning(f"Repository path does not exist: {repo_path}")
        return []

    parsed_units = []
    for file_path in repo.rglob("*"):
        # Skip directories and excluded patterns
        if file_path.is_dir():
            continue
        if any(skip in file_path.parts for skip in SKIP_PATTERNS):
            continue

        ext = file_path.suffix.lower()
        if ext not in LANGUAGE_MAP:
            continue

        language = LANGUAGE_MAP[ext]
        try:
            units = _parse_file(file_path, language, source_type)
            parsed_units.extend(units)
            logger.debug(f"Parsed {len(units)} units from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")

    logger.info(f"Parsed {len(parsed_units)} code units from {repo_path}")
    return parsed_units


def _parse_file(file_path: Path, language: str, source_type: str) -> List[ParsedCodeUnit]:
    """Parse a single file into code units based on language."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Cannot read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    rel_path = str(file_path)

    if language == "java":
        return _parse_java(content, rel_path, source_type)
    elif language in ("javascript", "typescript"):
        return _parse_js_ts(content, rel_path, language, source_type)
    elif language == "python":
        return _parse_python(content, rel_path, source_type)
    elif language in ("xml", "yaml", "json", "properties", "config", "groovy"):
        # Config files: treat as a single unit
        return [ParsedCodeUnit(
            content=content,
            file_path=rel_path,
            language=language,
            unit_type="config",
            unit_name=file_path.name,
            start_line=1,
            end_line=content.count("\n") + 1,
            metadata={"source_type": source_type},
        )]

    return []


def _parse_java(content: str, file_path: str, source_type: str) -> List[ParsedCodeUnit]:
    """
    Parse Java file into class-level and method-level units.
    Uses regex-based approach for robustness without tree-sitter dependency.
    """
    units = []
    lines = content.split("\n")

    # Regex patterns for Java constructs
    class_pattern = re.compile(
        r"^\s*(public|private|protected)?\s*(abstract|static|final)?\s*class\s+(\w+)",
        re.MULTILINE,
    )
    method_pattern = re.compile(
        r"^\s*(public|private|protected)\s+(static\s+)?"
        r"(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+[^{]+)?\{",
        re.MULTILINE,
    )

    # Extract methods with brace-matching
    method_matches = list(method_pattern.finditer(content))

    if method_matches:
        for match in method_matches:
            method_name = match.group(4)
            start_pos = match.start()
            start_line = content[:start_pos].count("\n") + 1

            # Find matching closing brace
            end_pos = _find_matching_brace(content, match.end() - 1)
            if end_pos == -1:
                end_pos = len(content)
            end_line = content[:end_pos].count("\n") + 1

            method_content = content[start_pos:end_pos + 1]

            # Include docstring/comment above the method
            doc_start = _find_preceding_comment(content, start_pos)
            if doc_start < start_pos:
                method_content = content[doc_start:end_pos + 1]
                start_line = content[:doc_start].count("\n") + 1

            units.append(ParsedCodeUnit(
                content=method_content.strip(),
                file_path=file_path,
                language="java",
                unit_type="method",
                unit_name=method_name,
                start_line=start_line,
                end_line=end_line,
                metadata={
                    "source_type": source_type,
                    "class_name": _extract_class_name(content, start_pos),
                    "signature": match.group(0).strip().rstrip("{").strip(),
                },
            ))
    else:
        # No methods found — treat entire file as one unit
        units.append(ParsedCodeUnit(
            content=content,
            file_path=file_path,
            language="java",
            unit_type="module",
            unit_name=Path(file_path).stem,
            start_line=1,
            end_line=len(lines),
            metadata={"source_type": source_type},
        ))

    return units


def _parse_js_ts(
    content: str, file_path: str, language: str, source_type: str
) -> List[ParsedCodeUnit]:
    """
    Parse JavaScript/TypeScript files into function/class units.
    """
    units = []
    lines = content.split("\n")

    # Patterns for JS/TS constructs
    func_patterns = [
        # Named functions: function name(...) {
        re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", re.MULTILINE),
        # Arrow functions: const name = (...) => {
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>", re.MULTILINE),
        # Class methods: async name(...) {
        re.compile(r"^\s+(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{", re.MULTILINE),
        # Class declarations
        re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.MULTILINE),
    ]

    # Collect all function/class positions
    matches = []
    for pattern in func_patterns:
        for match in pattern.finditer(content):
            matches.append((match.start(), match.group(1), match))

    # Sort by position
    matches.sort(key=lambda x: x[0])

    if matches:
        for i, (start_pos, name, match) in enumerate(matches):
            start_line = content[:start_pos].count("\n") + 1

            # Find the block boundary
            brace_pos = content.find("{", match.end())
            if brace_pos != -1:
                end_pos = _find_matching_brace(content, brace_pos)
                if end_pos == -1:
                    # Fall back to next function start
                    end_pos = matches[i + 1][0] - 1 if i + 1 < len(matches) else len(content)
            else:
                # Arrow function without braces — take till next match or end of line
                next_start = matches[i + 1][0] if i + 1 < len(matches) else len(content)
                end_pos = next_start - 1

            end_line = content[:end_pos + 1].count("\n") + 1
            func_content = content[start_pos:end_pos + 1]

            # Include preceding comments
            doc_start = _find_preceding_comment(content, start_pos)
            if doc_start < start_pos:
                func_content = content[doc_start:end_pos + 1]
                start_line = content[:doc_start].count("\n") + 1

            units.append(ParsedCodeUnit(
                content=func_content.strip(),
                file_path=file_path,
                language=language,
                unit_type="function",
                unit_name=name,
                start_line=start_line,
                end_line=end_line,
                metadata={"source_type": source_type},
            ))
    else:
        # No functions found — treat entire file as one unit
        units.append(ParsedCodeUnit(
            content=content,
            file_path=file_path,
            language=language,
            unit_type="module",
            unit_name=Path(file_path).stem,
            start_line=1,
            end_line=len(lines),
            metadata={"source_type": source_type},
        ))

    return units


def _parse_python(content: str, file_path: str, source_type: str) -> List[ParsedCodeUnit]:
    """Parse Python files into class/function units using indentation-based detection."""
    units = []
    lines = content.split("\n")

    # Patterns for Python constructs
    patterns = [
        (re.compile(r"^class\s+(\w+)"), "class"),
        (re.compile(r"^(?:async\s+)?def\s+(\w+)"), "function"),
    ]

    # Find all top-level and class-level definitions
    definitions = []
    for i, line in enumerate(lines):
        for pattern, unit_type in patterns:
            match = pattern.match(line)
            if match:
                definitions.append((i, match.group(1), unit_type))

    if definitions:
        for idx, (start_line, name, unit_type) in enumerate(definitions):
            # End at the next same-or-higher-level definition, or end of file
            if idx + 1 < len(definitions):
                end_line = definitions[idx + 1][0] - 1
                # Skip trailing blank lines
                while end_line > start_line and not lines[end_line].strip():
                    end_line -= 1
            else:
                end_line = len(lines) - 1

            func_content = "\n".join(lines[start_line:end_line + 1])

            units.append(ParsedCodeUnit(
                content=func_content.strip(),
                file_path=file_path,
                language="python",
                unit_type=unit_type,
                unit_name=name,
                start_line=start_line + 1,
                end_line=end_line + 1,
                metadata={"source_type": source_type},
            ))
    else:
        units.append(ParsedCodeUnit(
            content=content,
            file_path=file_path,
            language="python",
            unit_type="module",
            unit_name=Path(file_path).stem,
            start_line=1,
            end_line=len(lines),
            metadata={"source_type": source_type},
        ))

    return units


# ─── Helper Functions ───────────────────────────────────────────────


def _find_matching_brace(content: str, open_pos: int) -> int:
    """Find the position of the matching closing brace."""
    if open_pos >= len(content) or content[open_pos] != "{":
        return -1

    depth = 0
    in_string = False
    string_char = None

    for i in range(open_pos, len(content)):
        ch = content[i]

        # Handle string literals
        if ch in ('"', "'", "`") and (i == 0 or content[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_char = ch
            elif ch == string_char:
                in_string = False
                string_char = None
            continue

        if in_string:
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i

    return -1


def _find_preceding_comment(content: str, pos: int) -> int:
    """Find the start of a comment/docstring block immediately preceding the given position."""
    # Walk backwards from pos to find comment start
    lines_before = content[:pos].split("\n")
    if not lines_before:
        return pos

    comment_start = pos
    for line in reversed(lines_before[:-1]):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*") or stripped.startswith("#"):
            comment_start -= len(line) + 1  # +1 for newline
        elif stripped.startswith("/**"):
            comment_start -= len(line) + 1
        elif stripped == "":
            # Allow one blank line between comment and code
            comment_start -= len(line) + 1
        else:
            break

    return max(0, comment_start)


def _extract_class_name(content: str, method_pos: int) -> str:
    """Extract the class name that contains the given method position."""
    class_pattern = re.compile(r"class\s+(\w+)")
    last_class = ""
    for match in class_pattern.finditer(content):
        if match.start() < method_pos:
            last_class = match.group(1)
        else:
            break
    return last_class
