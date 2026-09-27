"""Read-only Jira issue tool constrained to the current ticket."""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from jira_qa_crew.jira.gateway import JiraGateway


class FetchJiraIssueInput(BaseModel):
    issue_key: str = Field(description="The Jira key currently being analyzed")


class FetchJiraIssueTool(BaseTool):
    name: str = "fetch_jira_issue"
    description: str = "Read the current Jira issue using the configured read-only Jira gateway."
    args_schema: type[BaseModel] = FetchJiraIssueInput
    _gateway: JiraGateway = PrivateAttr()
    _expected_key: str = PrivateAttr()
    _integration_mode: str = PrivateAttr()
    _cached_issue: Any = PrivateAttr(default=None)

    def __init__(
        self,
        gateway: JiraGateway,
        expected_key: str,
        integration_mode: str = "auto",
        cached_issue: Any = None,
    ):
        super().__init__()
        self._gateway = gateway
        self._expected_key = expected_key
        self._integration_mode = integration_mode
        self._cached_issue = cached_issue

    def _run(self, issue_key: str) -> str:
        if issue_key.strip().upper() != self._expected_key.upper():
            return (
                "Access denied: this tool is restricted to the Jira issue currently "
                "being processed."
            )
        issue = self._cached_issue or self._gateway.fetch_issue(
            issue_key.strip().upper(), mode=self._integration_mode
        )
        return issue.model_dump_json(indent=2)
