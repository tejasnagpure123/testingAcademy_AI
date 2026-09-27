"""Normalize and validate user-entered Jira issue keys."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketParseResult:
    keys: list[str]
    duplicates: list[str]
    invalid: list[str]


def parse_ticket_keys(
    raw: str,
    pattern: str = r"^[A-Z][A-Z0-9_]*-\d+$",
    max_tickets: int = 20,
    max_chars: int = 5000,
) -> TicketParseResult:
    if len(raw) > max_chars:
        raise ValueError(f"Input exceeds the {max_chars}-character limit.")
    matcher = re.compile(pattern)
    keys: list[str] = []
    duplicates: list[str] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for item in re.split(r"[,;\s]+", raw.strip()):
        if not item:
            continue
        key = item.upper()
        if not matcher.fullmatch(key):
            invalid.append(item)
        elif key in seen:
            duplicates.append(key)
        else:
            seen.add(key)
            keys.append(key)
    if len(keys) > max_tickets:
        raise ValueError(f"At most {max_tickets} Jira tickets can be processed per run.")
    return TicketParseResult(keys=keys, duplicates=duplicates, invalid=invalid)
