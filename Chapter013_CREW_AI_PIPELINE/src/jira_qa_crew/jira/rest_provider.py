"""Jira Cloud REST provider with bounded retry and typed failures."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from jira_qa_crew.config import AppConfig
from jira_qa_crew.exceptions import (
    JiraAuthenticationError,
    JiraNotFoundError,
    JiraProviderError,
    JiraRateLimitError,
)
from jira_qa_crew.jira.adf import adf_to_text
from jira_qa_crew.models import JiraIssue

logger = logging.getLogger(__name__)


class JiraRestProvider:
    name = "REST"

    def __init__(self, config: AppConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    def _auth(self) -> tuple[tuple[str, str] | None, dict[str, str]]:
        if self.config.jira_auth_mode == "bearer":
            return None, {"Authorization": f"Bearer {self.config.jira_bearer_token}"}
        return (self.config.jira_email, self.config.jira_api_token), {}

    def health_check(self) -> bool:
        return bool(self.config.jira_url)

    def fetch_issue(self, issue_key: str) -> JiraIssue:
        url = (
            f"{self.config.jira_url.rstrip('/')}/rest/api/"
            f"{self.config.jira_api_version}/issue/{issue_key}"
        )
        fields = [
            "summary",
            "description",
            "reporter",
            "status",
            "priority",
            "issuetype",
            "labels",
            "components",
            "parent",
            "subtasks",
            "issuelinks",
        ]
        if self.config.jira_acceptance_criteria_field:
            fields.append(self.config.jira_acceptance_criteria_field)
        if self.config.jira_include_comments:
            fields.append("comment")
        auth, auth_headers = self._auth()
        headers = {"Accept": "application/json", **auth_headers}

        response = None
        retry_limit = min(max(self.config.pipeline_max_retries, 0), 3)
        for attempt in range(retry_limit + 1):
            try:
                response = self.session.get(
                    url,
                    auth=auth,
                    headers=headers,
                    params={"fields": ",".join(fields)},
                    timeout=min(self.config.jira_mcp_timeout_seconds, 60),
                )
            except requests.Timeout as error:
                if attempt == retry_limit:
                    raise JiraProviderError("Jira REST request timed out.") from error
                time.sleep(0.25 * (2**attempt))
                continue
            except requests.ConnectionError as error:
                if attempt == retry_limit:
                    raise JiraProviderError("Could not connect to Jira REST API.") from error
                time.sleep(0.25 * (2**attempt))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < retry_limit:
                    retry_after = response.headers.get("Retry-After", "")
                    try:
                        delay = min(float(retry_after), 4.0) if retry_after else 0.25 * (2**attempt)
                    except ValueError:
                        delay = 0.25 * (2**attempt)
                    time.sleep(delay)
                    continue
            break

        if response is None:
            raise JiraProviderError("Jira REST API returned no response.")
        if response.status_code in {401, 403}:
            raise JiraAuthenticationError(
                f"Jira REST API rejected credentials or permissions (HTTP {response.status_code})."
            )
        if response.status_code == 404:
            raise JiraNotFoundError(
                f"Jira issue {issue_key} was not found or is not visible to this account."
            )
        if response.status_code == 429:
            raise JiraRateLimitError("Jira REST API rate limit persisted after bounded retries.")
        try:
            response.raise_for_status()
            payload = response.json()
            return self._to_issue(payload, issue_key)
        except JiraProviderError:
            raise
        except (ValueError, KeyError, TypeError) as error:
            raise JiraProviderError("Jira REST API returned malformed issue data.") from error
        except requests.HTTPError as error:
            raise JiraProviderError(
                f"Jira REST API returned HTTP {response.status_code}."
            ) from error

    def _to_issue(self, payload: dict[str, Any], requested_key: str) -> JiraIssue:
        if not isinstance(payload, dict) or not isinstance(payload.get("fields"), dict):
            raise ValueError("Issue payload has no fields object")
        fields = payload["fields"]
        acceptance = ""
        custom_field = self.config.jira_acceptance_criteria_field
        if custom_field and fields.get(custom_field) is not None:
            value = fields[custom_field]
            acceptance = adf_to_text(value) if isinstance(value, (dict, list)) else str(value)
        comments = []
        if self.config.jira_include_comments:
            comment_items = (fields.get("comment") or {}).get("comments", [])
            comments = [
                adf_to_text(item.get("body"))
                for item in comment_items[: max(self.config.jira_max_comments, 0)]
            ]
        parent = fields.get("parent") or {}
        issue_links = fields.get("issuelinks") or []
        links = []
        for link in issue_links:
            other = link.get("outwardIssue") or link.get("inwardIssue") or {}
            if other.get("key"):
                links.append(other["key"])
        return JiraIssue(
            key=str(payload.get("key") or requested_key).upper(),
            summary=str(fields.get("summary") or "No summary"),
            description=adf_to_text(fields.get("description")) or "",
            issue_type=str((fields.get("issuetype") or {}).get("name") or "Unknown"),
            status=str((fields.get("status") or {}).get("name") or "Unknown"),
            priority=str((fields.get("priority") or {}).get("name") or "Unspecified"),
            labels=[str(value) for value in (fields.get("labels") or [])],
            components=[str(item.get("name", "")) for item in (fields.get("components") or [])],
            parent_key=parent.get("key"),
            subtasks=[
                str(item.get("key")) for item in (fields.get("subtasks") or []) if item.get("key")
            ],
            linked_issues=links,
            acceptance_criteria=acceptance,
            comments=comments,
            source="REST",
        )
