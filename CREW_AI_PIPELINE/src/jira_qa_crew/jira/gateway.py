"""Deterministic MCP-first Jira routing with explicit REST fallback."""

from __future__ import annotations

import logging

from jira_qa_crew.config import AppConfig
from jira_qa_crew.exceptions import JiraProviderError
from jira_qa_crew.jira.base import JiraProvider
from jira_qa_crew.jira.mcp_provider import JiraMCPProvider
from jira_qa_crew.jira.rest_provider import JiraRestProvider
from jira_qa_crew.models import JiraIssue

logger = logging.getLogger(__name__)


class JiraGateway:
    def __init__(
        self,
        config: AppConfig,
        mcp_provider: JiraProvider | None = None,
        rest_provider: JiraProvider | None = None,
    ):
        self.config = config
        self.mcp = mcp_provider or JiraMCPProvider(config)
        self.rest = rest_provider or JiraRestProvider(config)

    def fetch_issue(self, issue_key: str, mode: str | None = None) -> JiraIssue:
        selected = (mode or self.config.jira_integration_mode).lower()
        if selected == "rest":
            return self._validate_issue(self.rest.fetch_issue(issue_key), issue_key, "REST")
        if selected == "mcp":
            return self._validate_issue(self.mcp.fetch_issue(issue_key), issue_key, "MCP")
        if selected != "auto":
            raise JiraProviderError("Integration mode must be auto, mcp, or rest.")

        try:
            return self._validate_issue(self.mcp.fetch_issue(issue_key), issue_key, "MCP")
        except Exception as mcp_error:
            logger.warning(
                "Jira MCP unavailable for %s (%s); trying Jira REST.",
                issue_key,
                type(mcp_error).__name__,
            )
            try:
                return self.rest.fetch_issue(issue_key)
            except Exception as rest_error:
                raise JiraProviderError(
                    f"Jira MCP and REST both failed for {issue_key}. "
                    f"MCP: {self._safe_message(mcp_error)} REST: {self._safe_message(rest_error)}"
                ) from rest_error

    @staticmethod
    def _safe_message(error: Exception) -> str:
        message = str(error)
        for secret in ("Bearer ",):
            if secret in message:
                return "credential details redacted"
        return message[:240]

    @staticmethod
    def _validate_issue(issue: JiraIssue, requested_key: str, provider: str) -> JiraIssue:
        if issue.key.upper() != requested_key.upper() or not issue.summary.strip():
            raise JiraProviderError(
                f"Jira {provider} returned an issue that failed ticket validation."
            )
        if issue.source != provider:
            raise JiraProviderError(f"Jira {provider} returned an inconsistent source label.")
        return issue
