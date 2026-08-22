"""
QABuddy.ai — Transcript Parser
Parses meeting notes and transcript text files.
Handles speaker-labeled transcripts, plain text notes, and markdown.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ParsedTranscriptSegment:
    """A parsed segment from a meeting transcript."""
    content: str
    file_path: str
    segment_index: int
    speaker: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_transcript(file_path: str, source_type: str = "meeting_transcripts") -> List[ParsedTranscriptSegment]:
    """
    Parse a meeting transcript file into segments.

    Supports formats:
    - Speaker-labeled: "Speaker Name: text..."
    - Timestamped: "[00:01:23] Speaker: text..."
    - Plain text paragraphs

    Args:
        file_path: Path to the transcript file
        source_type: Source identifier

    Returns:
        List of ParsedTranscriptSegment objects
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Transcript file not found: {file_path}")
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []

    if not content.strip():
        return []

    # Detect format and parse accordingly
    if _is_speaker_labeled(content):
        segments = _parse_speaker_labeled(content, str(file_path), source_type)
    elif _is_timestamped(content):
        segments = _parse_timestamped(content, str(file_path), source_type)
    else:
        segments = _parse_paragraphs(content, str(file_path), source_type)

    # Merge consecutive segments from the same speaker
    segments = _merge_short_segments(segments)

    logger.info(f"Parsed {len(segments)} segments from {path.name}")
    return segments


def parse_transcript_directory(dir_path: str, source_type: str = "meeting_transcripts") -> List[ParsedTranscriptSegment]:
    """Parse all transcript files in a directory."""
    directory = Path(dir_path)
    if not directory.exists():
        return []

    all_segments = []
    for file_path in directory.rglob("*"):
        if file_path.suffix.lower() in (".txt", ".md", ".text", ".transcript"):
            segments = parse_transcript(str(file_path), source_type)
            all_segments.extend(segments)

    return all_segments


def _is_speaker_labeled(content: str) -> bool:
    """Check if content has speaker labels (e.g., 'Speaker: text')."""
    pattern = re.compile(r"^[A-Z][a-zA-Z\s]+:\s", re.MULTILINE)
    matches = pattern.findall(content[:2000])
    return len(matches) >= 3


def _is_timestamped(content: str) -> bool:
    """Check if content has timestamps (e.g., '[00:01:23]')."""
    pattern = re.compile(r"\[\d{1,2}:\d{2}(:\d{2})?\]")
    matches = pattern.findall(content[:2000])
    return len(matches) >= 3


def _parse_speaker_labeled(content: str, file_path: str, source_type: str) -> List[ParsedTranscriptSegment]:
    """Parse speaker-labeled transcript."""
    pattern = re.compile(r"^([A-Z][a-zA-Z\s]+):\s*(.*?)(?=^[A-Z][a-zA-Z\s]+:\s|\Z)", re.MULTILINE | re.DOTALL)
    segments = []

    for idx, match in enumerate(pattern.finditer(content)):
        speaker = match.group(1).strip()
        text = match.group(2).strip()

        if text:
            segments.append(ParsedTranscriptSegment(
                content=f"{speaker}: {text}",
                file_path=file_path,
                segment_index=idx,
                speaker=speaker,
                metadata={"source_type": source_type, "meeting_file": Path(file_path).stem},
            ))

    return segments


def _parse_timestamped(content: str, file_path: str, source_type: str) -> List[ParsedTranscriptSegment]:
    """Parse timestamped transcript."""
    # Remove timestamps
    cleaned = re.sub(r"\[\d{1,2}:\d{2}(:\d{2})?\]\s*", "", content)

    # Try to find speaker labels after removing timestamps
    if _is_speaker_labeled(cleaned):
        return _parse_speaker_labeled(cleaned, file_path, source_type)

    # Fall back to paragraph parsing
    return _parse_paragraphs(cleaned, file_path, source_type)


def _parse_paragraphs(content: str, file_path: str, source_type: str) -> List[ParsedTranscriptSegment]:
    """Parse plain text into paragraph-based segments."""
    paragraphs = re.split(r"\n\s*\n", content)
    segments = []

    for idx, para in enumerate(paragraphs):
        text = para.strip()
        if text and len(text) > 20:  # Skip very short paragraphs
            segments.append(ParsedTranscriptSegment(
                content=text,
                file_path=file_path,
                segment_index=idx,
                speaker="Unknown",
                metadata={"source_type": source_type, "meeting_file": Path(file_path).stem},
            ))

    return segments


def _merge_short_segments(
    segments: List[ParsedTranscriptSegment],
    min_length: int = 50,
) -> List[ParsedTranscriptSegment]:
    """Merge consecutive short segments from the same speaker."""
    if not segments:
        return []

    merged = [segments[0]]

    for seg in segments[1:]:
        prev = merged[-1]
        if (
            seg.speaker == prev.speaker
            and len(prev.content) < min_length
        ):
            # Merge into previous segment
            merged[-1] = ParsedTranscriptSegment(
                content=f"{prev.content}\n{seg.content}",
                file_path=prev.file_path,
                segment_index=prev.segment_index,
                speaker=prev.speaker,
                metadata=prev.metadata,
            )
        else:
            merged.append(seg)

    return merged
