"""
QABuddy.ai — JIRA Parser
Fetches and parses JIRA tickets via REST API using JQL queries.
Each ticket becomes a self-contained document with all relevant fields.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger

try:
    from jira import JIRA
except ImportError:
    JIRA = None
    logger.warning("jira library not installed. Install with: pip install jira")


@dataclass
class ParsedJiraTicket:
    """A single parsed JIRA ticket."""
    content: str             # Full text representation
    ticket_key: str          # e.g., "QA-1234"
    summary: str
    status: str
    priority: str
    assignee: str
    reporter: str
    created: str
    updated: str
    ticket_type: str
    labels: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


def fetch_jira_tickets(
    base_url: str,
    email: str,
    api_token: str,
    jql: str,
    max_results: int = 1000,
    source_type: str = "jira_tickets",
) -> List[ParsedJiraTicket]:
    """
    Fetch tickets from JIRA using JQL and parse them into documents.

    Args:
        base_url: JIRA base URL (e.g., "https://company.atlassian.net")
        email: JIRA account email
        api_token: JIRA API token
        jql: JQL query string
        max_results: Maximum tickets to fetch
        source_type: Source identifier

    Returns:
        List of ParsedJiraTicket objects
    """
    if JIRA is None:
        logger.error("jira library is required. Install with: pip install jira")
        return []

    try:
        client = JIRA(
            server=base_url,
            basic_auth=(email, api_token),
        )
        logger.info(f"Connected to JIRA at {base_url}")
    except Exception as e:
        logger.error(f"Failed to connect to JIRA: {e}")
        return []

    tickets = []
    start_at = 0
    batch_size = 50

    while start_at < max_results:
        try:
            issues = client.search_issues(
                jql,
                startAt=start_at,
                maxResults=min(batch_size, max_results - start_at),
                expand="renderedFields",
                fields="summary,description,status,priority,assignee,reporter,"
                       "created,updated,issuetype,labels,components,comment",
            )
        except Exception as e:
            logger.error(f"JIRA search failed at offset {start_at}: {e}")
            break

        if not issues:
            break

        for issue in issues:
            try:
                ticket = _parse_issue(issue, base_url, source_type)
                tickets.append(ticket)
            except Exception as e:
                logger.warning(f"Failed to parse issue {issue.key}: {e}")

        start_at += len(issues)
        logger.info(f"Fetched {start_at} tickets so far...")

        if len(issues) < batch_size:
            break

    logger.info(f"Fetched and parsed {len(tickets)} JIRA tickets")
    return tickets


def _parse_issue(issue: Any, base_url: str, source_type: str) -> ParsedJiraTicket:
    """Parse a single JIRA issue into a ParsedJiraTicket."""
    fields = issue.fields

    # Extract fields safely
    summary = str(fields.summary or "")
    description = str(fields.description or "No description")
    status = str(fields.status) if fields.status else "Unknown"
    priority = str(fields.priority) if fields.priority else "None"
    assignee = str(fields.assignee) if fields.assignee else "Unassigned"
    reporter = str(fields.reporter) if fields.reporter else "Unknown"
    created = str(fields.created or "")
    updated = str(fields.updated or "")
    issue_type = str(fields.issuetype) if fields.issuetype else "Task"
    labels = list(fields.labels) if fields.labels else []
    components = [str(c) for c in fields.components] if fields.components else []

    # Extract comments
    comments = []
    if hasattr(fields, "comment") and fields.comment:
        for comment in fields.comment.comments:
            author = str(comment.author) if comment.author else "Unknown"
            body = str(comment.body or "")
            created_at = str(comment.created or "")
            comments.append(f"[{author} on {created_at}]: {body}")

    # Build full text representation
    parts = [
        f"JIRA Ticket: {issue.key}",
        f"Type: {issue_type}",
        f"Summary: {summary}",
        f"Status: {status}",
        f"Priority: {priority}",
        f"Assignee: {assignee}",
        f"Reporter: {reporter}",
        f"Created: {created}",
        f"Updated: {updated}",
    ]

    if labels:
        parts.append(f"Labels: {', '.join(labels)}")
    if components:
        parts.append(f"Components: {', '.join(components)}")

    parts.append(f"\nDescription:\n{_clean_jira_markup(description)}")

    if comments:
        parts.append(f"\nComments ({len(comments)}):")
        for comment in comments[-10:]:  # Last 10 comments to keep size reasonable
            parts.append(f"  {_clean_jira_markup(comment)}")

    content = "\n".join(parts)

    return ParsedJiraTicket(
        content=content,
        ticket_key=issue.key,
        summary=summary,
        status=status,
        priority=priority,
        assignee=assignee,
        reporter=reporter,
        created=created,
        updated=updated,
        ticket_type=issue_type,
        labels=labels,
        components=components,
        comments=comments,
        metadata={
            "source_type": source_type,
            "source_url": f"{base_url}/browse/{issue.key}",
            "ticket_key": issue.key,
            "status": status,
            "priority": priority,
            "issue_type": issue_type,
        },
    )


def save_tickets_to_disk(tickets: List[ParsedJiraTicket], output_dir: str) -> None:
    """Save parsed JIRA tickets to disk as JSON for offline access."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for ticket in tickets:
        file_path = out_path / f"{ticket.ticket_key}.json"
        data = {
            "ticket_key": ticket.ticket_key,
            "summary": ticket.summary,
            "status": ticket.status,
            "priority": ticket.priority,
            "assignee": ticket.assignee,
            "reporter": ticket.reporter,
            "created": ticket.created,
            "updated": ticket.updated,
            "ticket_type": ticket.ticket_type,
            "labels": ticket.labels,
            "components": ticket.components,
            "comments": ticket.comments,
            "content": ticket.content,
            "metadata": ticket.metadata,
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    logger.info(f"Saved {len(tickets)} tickets to {output_dir}")


def load_tickets_from_disk(input_dir: str, source_type: str = "jira_tickets") -> List[ParsedJiraTicket]:
    """Load previously saved JIRA tickets from disk (.json and .md files)."""
    dir_path = Path(input_dir)
    if not dir_path.exists():
        return []

    tickets = []
    # JSON ticket files
    for file_path in dir_path.glob("*.json"):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            tickets.append(ParsedJiraTicket(
                content=data["content"],
                ticket_key=data["ticket_key"],
                summary=data["summary"],
                status=data["status"],
                priority=data["priority"],
                assignee=data["assignee"],
                reporter=data["reporter"],
                created=data["created"],
                updated=data["updated"],
                ticket_type=data["ticket_type"],
                labels=data.get("labels", []),
                components=data.get("components", []),
                comments=data.get("comments", []),
                metadata=data.get("metadata", {"source_type": source_type}),
            ))
        except Exception as e:
            logger.warning(f"Failed to load ticket from {file_path}: {e}")

    # Markdown ticket files (e.g., KAN-13.md)
    for file_path in dir_path.glob("*.md"):
        try:
            text = file_path.read_text(encoding="utf-8")
            ticket_key = file_path.stem
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            summary = lines[0] if lines else ticket_key
            tickets.append(ParsedJiraTicket(
                content=text,
                ticket_key=ticket_key,
                summary=summary,
                status="Active",
                priority="Medium",
                assignee="Unassigned",
                reporter="QA",
                created=datetime.utcnow().strftime("%Y-%m-%d"),
                updated=datetime.utcnow().strftime("%Y-%m-%d"),
                ticket_type="Story",
                metadata={
                    "source_type": source_type,
                    "ticket_key": ticket_key,
                    "file_path": str(file_path),
                },
            ))
        except Exception as e:
            logger.warning(f"Failed to load MD ticket from {file_path}: {e}")

    logger.info(f"Loaded {len(tickets)} tickets from {input_dir}")
    return tickets


def _clean_jira_markup(text: str) -> str:
    """Clean JIRA/Atlassian markup to plain text."""
    import re

    if not text:
        return ""

    # Remove JIRA formatting
    text = re.sub(r"\{code[^}]*\}(.*?)\{code\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\{noformat\}(.*?)\{noformat\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\{color[^}]*\}(.*?)\{color\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\{quote\}(.*?)\{quote\}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"\[([^|]+)\|([^\]]+)\]", r"\1 (\2)", text)  # Links
    text = re.sub(r"\[~([^\]]+)\]", r"@\1", text)  # Mentions
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # Bold
    text = re.sub(r"_([^_]+)_", r"\1", text)  # Italic
    text = re.sub(r"\+([^+]+)\+", r"\1", text)  # Underline
    text = re.sub(r"-([^-]+)-", r"\1", text)  # Strikethrough
    text = re.sub(r"h[1-6]\.\s*", "", text)  # Headings
    text = re.sub(r"![\w.]+!", "", text)  # Images

    return text.strip()
