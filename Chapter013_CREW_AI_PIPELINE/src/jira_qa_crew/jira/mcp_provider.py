"""CrewAI MCPClient provider restricted to one configured issue-read tool."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from crewai.mcp import MCPClient
from crewai.mcp.transports import HTTPTransport, StdioTransport

from jira_qa_crew.config import AppConfig
from jira_qa_crew.exceptions import JiraProviderError
from jira_qa_crew.jira.adf import adf_to_text
from jira_qa_crew.models import JiraIssue

logger = logging.getLogger(__name__)


class JiraMCPProvider:
    name = "MCP"

    def __init__(self, config: AppConfig):
        self.config = config

    def _transport(self):
        if self.config.jira_mcp_transport == "streamable_http":
            return HTTPTransport(
                self.config.jira_mcp_url,
                headers=self.config.mcp_headers(),
                streamable=True,
            )
        if self.config.jira_mcp_transport == "stdio":
            import os

            return StdioTransport(
                command=self.config.jira_mcp_command,
                args=self.config.mcp_args(),
                env=dict(os.environ),
            )
        raise JiraProviderError("JIRA_MCP_TRANSPORT must be streamable_http or stdio.")

    def health_check(self) -> bool:
        try:
            asyncio.run(self._check_tool())
            return True
        except Exception as error:
            logger.warning("Jira MCP health check failed (%s).", type(error).__name__)
            return False

    async def _check_tool(self) -> None:
        client = MCPClient(
            self._transport(),
            connect_timeout=self.config.jira_mcp_timeout_seconds,
            execution_timeout=self.config.jira_mcp_timeout_seconds,
            discovery_timeout=self.config.jira_mcp_timeout_seconds,
            max_retries=1,
        )
        try:
            tools = await client.list_tools()
            if not any(tool.get("name") == self.config.jira_mcp_get_issue_tool for tool in tools):
                raise JiraProviderError("Configured Jira MCP issue-read tool was not advertised.")
        finally:
            await client.disconnect()

    def fetch_issue(self, issue_key: str) -> JiraIssue:
        try:
            return asyncio.run(self._fetch_issue(issue_key))
        except JiraProviderError:
            raise
        except Exception as error:
            logger.warning("Jira MCP issue fetch failed (%s).", type(error).__name__)
            raise JiraProviderError("Jira MCP could not return a usable issue.") from error

    async def _fetch_issue(self, issue_key: str) -> JiraIssue:
        client = MCPClient(
            self._transport(),
            connect_timeout=self.config.jira_mcp_timeout_seconds,
            execution_timeout=self.config.jira_mcp_timeout_seconds,
            discovery_timeout=self.config.jira_mcp_timeout_seconds,
            max_retries=1,
        )
        try:
            tools = await client.list_tools()
            tool_name = self.config.jira_mcp_get_issue_tool
            if not any(tool.get("name") == tool_name for tool in tools):
                raise JiraProviderError("Configured Jira MCP issue-read tool was not advertised.")
            result = await client.call_tool_result(
                tool_name,
                {self.config.jira_mcp_issue_argument: issue_key},
            )
            if getattr(result, "isError", False):
                raise JiraProviderError("Jira MCP issue-read tool returned an error.")
            payload = self._parse_result(result)
            return self._to_issue(payload, issue_key)
        finally:
            await client.disconnect()

    @staticmethod
    def _parse_result(result: Any) -> dict[str, Any]:
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, dict):
            return structured
        content = getattr(result, "content", None)
        if isinstance(content, dict):
            return content
        texts = [getattr(item, "text", "") for item in (content or [])]
        for text in texts:
            try:
                parsed = json.loads(text)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(parsed, dict):
                return parsed
        raise JiraProviderError(
            "Jira MCP returned no structured issue data; REST fallback is required."
        )

    def _to_issue(self, payload: dict[str, Any], requested_key: str) -> JiraIssue:
        issue = payload.get("issue", payload)
        if not isinstance(issue, dict):
            raise JiraProviderError("Jira MCP returned malformed issue data.")
        fields = issue.get("fields", issue)
        if not isinstance(fields, dict) or not fields.get("summary"):
            raise JiraProviderError("Jira MCP response is missing issue summary fields.")
        description_value = fields.get("description", "")
        description = (
            adf_to_text(description_value)
            if isinstance(description_value, (dict, list))
            else str(description_value or "")
        )
        criteria_field = self.config.jira_acceptance_criteria_field or "acceptanceCriteria"
        acceptance = fields.get(criteria_field, "")
        acceptance = (
            adf_to_text(acceptance)
            if isinstance(acceptance, (dict, list))
            else str(acceptance or "")
        )
        comments = []
        if self.config.jira_include_comments and isinstance(fields.get("comments"), list):
            comments = [
                adf_to_text(comment.get("body", comment))
                for comment in fields["comments"][: max(self.config.jira_max_comments, 0)]
            ]
        return JiraIssue(
            key=str(issue.get("key") or payload.get("key") or requested_key).upper(),
            summary=str(fields["summary"]),
            description=description,
            issue_type=str((fields.get("issuetype") or {}).get("name", "Unknown")),
            status=str((fields.get("status") or {}).get("name", "Unknown")),
            priority=str((fields.get("priority") or {}).get("name", "Unspecified")),
            labels=[str(item) for item in fields.get("labels", [])],
            components=[str(item.get("name", "")) for item in fields.get("components", [])],
            parent_key=(fields.get("parent") or {}).get("key"),
            subtasks=[str(item["key"]) for item in fields.get("subtasks", []) if item.get("key")],
            acceptance_criteria=acceptance,
            comments=comments,
            source="MCP",
        )
