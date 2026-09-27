"""Convert Atlassian Document Format nodes to readable plain text."""

from __future__ import annotations

from typing import Any


def adf_to_text(node: Any) -> str:
    if isinstance(node, list):
        return "".join(adf_to_text(child) for child in node)
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text", ""))
    if node_type in {"hardBreak", "rule"}:
        return "\n"
    if node_type == "mention":
        return str((node.get("attrs") or {}).get("text", ""))
    text = adf_to_text(node.get("content", []))
    if node_type in {"paragraph", "heading", "listItem", "blockquote", "codeBlock"} and text:
        return text + "\n"
    if node_type in {"bulletList", "orderedList"} and text:
        return text + "\n"
    return text
