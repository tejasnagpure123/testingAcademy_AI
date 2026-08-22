"""
QABuddy.ai — Log Cleaner
Cleans Jenkins logs: strips ANSI codes, normalizes timestamps,
removes noise while preserving actionable information.
"""

import re


# ANSI escape code pattern
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# Timestamp patterns
TIMESTAMP_PATTERNS = [
    re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?\s*"),  # ISO 8601
    re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.\d]*\s*"),   # Common log format
    re.compile(r"\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]\s*"),      # Bracketed timestamp
]

# Noisy patterns that add no retrieval value
NOISE_PATTERNS = [
    re.compile(r"^\s*\+\s*$", re.MULTILINE),                    # Maven progress indicators
    re.compile(r"^Downloading:\s+https?://.*$", re.MULTILINE),  # Maven download logs
    re.compile(r"^Downloaded:\s+https?://.*$", re.MULTILINE),
    re.compile(r"^Progress \(\d+\):\s+.*$", re.MULTILINE),     # Progress updates
    re.compile(r"^\s*\[INFO\]\s*$", re.MULTILINE),               # Empty INFO lines
]


def clean_log(content: str, preserve_timestamps: bool = False) -> str:
    """
    Clean Jenkins log content.

    Args:
        content: Raw log content
        preserve_timestamps: If True, keeps timestamps (useful for time-based queries)

    Returns:
        Cleaned log content
    """
    if not content:
        return ""

    # Remove ANSI color codes
    content = ANSI_RE.sub("", content)

    # Normalize line endings
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Optionally simplify timestamps
    if not preserve_timestamps:
        for pattern in TIMESTAMP_PATTERNS:
            content = pattern.sub("", content)

    # Remove noise patterns
    for pattern in NOISE_PATTERNS:
        content = pattern.sub("", content)

    # Remove excessive blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove leading/trailing whitespace per line
    lines = [line.rstrip() for line in content.split("\n")]

    # Remove completely empty lines at the start/end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return "\n".join(lines)
