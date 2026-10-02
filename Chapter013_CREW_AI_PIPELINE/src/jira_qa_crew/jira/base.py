"""Jira provider protocol."""

from typing import Protocol

from jira_qa_crew.models import JiraIssue


class JiraProvider(Protocol):
    name: str

    def fetch_issue(self, issue_key: str) -> JiraIssue: ...

    def health_check(self) -> bool: ...
