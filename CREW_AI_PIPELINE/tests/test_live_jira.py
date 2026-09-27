"""Opt-in Jira integration test; disabled during ordinary CI runs."""

import os

import pytest

from jira_qa_crew.config import AppConfig
from jira_qa_crew.jira.rest_provider import JiraRestProvider


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_JIRA_TESTS") != "true",
    reason="Set RUN_LIVE_JIRA_TESTS=true to enable live Jira integration checks.",
)
def test_live_jira_issue_read():
    issue_key = os.getenv("LIVE_JIRA_TEST_ISSUE_KEY", "").strip().upper()
    assert issue_key, "Set LIVE_JIRA_TEST_ISSUE_KEY for the opt-in test."
    config = AppConfig.load()
    issue = JiraRestProvider(config).fetch_issue(issue_key)
    assert issue.key == issue_key
    assert issue.source == "REST"
