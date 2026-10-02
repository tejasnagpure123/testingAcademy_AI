from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from conftest import make_analysis, make_plan, make_suite

from jira_qa_crew.config import AppConfig
from jira_qa_crew.crew.factory import create_crew
from jira_qa_crew.exceptions import JiraProviderError, OutputValidationError
from jira_qa_crew.jira.adf import adf_to_text
from jira_qa_crew.jira.gateway import JiraGateway
from jira_qa_crew.jira.mcp_provider import JiraMCPProvider
from jira_qa_crew.jira.rest_provider import JiraRestProvider
from jira_qa_crew.models import JiraIssue, TicketResult
from jira_qa_crew.services.pipeline import QAPipeline
from jira_qa_crew.services.tickets import parse_ticket_keys
from jira_qa_crew.services.validation import (
    validate_analysis,
    validate_plan,
    validate_suite,
)
from jira_qa_crew.tools.jira_tool import FetchJiraIssueTool


def issue(key="QA-1", source="REST"):
    return JiraIssue(key=key, summary="Sample", source=source)


def test_ticket_parse_normalize_duplicates_and_invalid():
    parsed = parse_ticket_keys("qa-1, QA-2; qa-1\nnot-a-ticket")
    assert parsed.keys == ["QA-1", "QA-2"]
    assert parsed.duplicates == ["QA-1"]
    assert parsed.invalid == ["not-a-ticket"]


def test_ticket_parser_enforces_size_and_count():
    with pytest.raises(ValueError, match="character"):
        parse_ticket_keys("QA-1", max_chars=2)
    with pytest.raises(ValueError, match="At most"):
        parse_ticket_keys("QA-1 QA-2", max_tickets=1)


def test_adf_to_text_handles_nested_content_and_breaks():
    document = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "hardBreak"},
                    {"type": "text", "text": "Jira"},
                ],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Item"}],
                            }
                        ],
                    }
                ],
            },
        ],
    }
    assert "Hello\nJira" in adf_to_text(document)
    assert "Item" in adf_to_text(document)


def test_gateway_auto_uses_mcp_when_valid():
    mcp = Mock()
    mcp.fetch_issue.return_value = issue(source="MCP")
    rest = Mock()
    result = JiraGateway(AppConfig(), mcp, rest).fetch_issue("QA-1", "auto")
    assert result.source == "MCP"
    rest.fetch_issue.assert_not_called()


def test_gateway_auto_falls_back_to_rest_on_mcp_failure():
    mcp = Mock()
    mcp.fetch_issue.side_effect = JiraProviderError("unavailable")
    rest = Mock()
    rest.fetch_issue.return_value = issue()
    assert JiraGateway(AppConfig(), mcp, rest).fetch_issue("QA-1", "auto").source == "REST"
    rest.fetch_issue.assert_called_once_with("QA-1")


def test_gateway_rest_only_never_calls_mcp():
    mcp, rest = Mock(), Mock()
    rest.fetch_issue.return_value = issue()
    JiraGateway(AppConfig(), mcp, rest).fetch_issue("QA-1", "rest")
    mcp.fetch_issue.assert_not_called()


def test_gateway_mcp_only_never_calls_rest():
    mcp, rest = Mock(), Mock()
    mcp.fetch_issue.return_value = issue(source="MCP")
    JiraGateway(AppConfig(), mcp, rest).fetch_issue("QA-1", "mcp")
    rest.fetch_issue.assert_not_called()


def test_gateway_reports_both_provider_failures():
    mcp, rest = Mock(), Mock()
    mcp.fetch_issue.side_effect = JiraProviderError("mcp down")
    rest.fetch_issue.side_effect = JiraProviderError("rest down")
    with pytest.raises(JiraProviderError, match="both failed"):
        JiraGateway(AppConfig(), mcp, rest).fetch_issue("QA-1", "auto")


def test_rest_maps_jira_adf_issue_response():
    config = AppConfig(jira_url="https://jira.example", jira_email="a", jira_api_token="b")
    provider = JiraRestProvider(config)
    mapped = provider._to_issue(
        {
            "key": "QA-1",
            "fields": {
                "summary": "Login validation",
                "description": {
                    "type": "doc",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Details"}],
                        }
                    ],
                },
                "issuetype": {"name": "Bug"},
                "status": {"name": "Open"},
                "priority": {"name": "High"},
                "labels": ["auth"],
                "components": [{"name": "Web"}],
                "parent": {"key": "QA-0"},
                "subtasks": [{"key": "QA-2"}],
                "issuelinks": [{"outwardIssue": {"key": "QA-3"}}],
            },
        },
        "QA-1",
    )
    assert mapped.description.strip() == "Details"
    assert mapped.parent_key == "QA-0"
    assert mapped.subtasks == ["QA-2"]
    assert mapped.linked_issues == ["QA-3"]


def test_mcp_issue_response_parser_accepts_structured_json():
    payload = {"key": "QA-1", "fields": {"summary": "Read-only issue"}}
    parsed = JiraMCPProvider(AppConfig())._to_issue(payload, "QA-1")
    assert parsed.source == "MCP"
    assert parsed.summary == "Read-only issue"


def test_analyst_tool_is_limited_to_current_ticket():
    gateway = Mock()
    tool = FetchJiraIssueTool(gateway=gateway, expected_key="QA-1", cached_issue=issue())
    assert "Access denied" in tool._run("OTHER-2")
    gateway.fetch_issue.assert_not_called()
    assert '"key": "QA-1"' in tool._run("QA-1")


def test_crew_factory_builds_four_sequential_agents_with_jira_only_for_analyst():
    config = AppConfig(llm_model="openai/gpt-4o-mini", llm_api_key="test-key")
    crew = create_crew(
        config,
        Mock(),
        "QA-1",
        "rest",
        "{}",
        issue(),
        lambda *_args: None,
    )
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4
    assert crew.process.value == "sequential"
    assert len(crew.agents[0].tools) == 1
    assert all(not agent.tools for agent in crew.agents[1:])


def test_analysis_plan_and_suite_traceability():
    analysis, plan, suite = make_analysis(), make_plan(), make_suite()
    validate_analysis(analysis, "QA-1")
    validate_plan(plan, analysis, "QA-1")
    validate_suite(suite, analysis, "QA-1")
    suite.test_cases[0].acceptance_criteria_ids = []
    with pytest.raises(OutputValidationError, match="no test coverage"):
        validate_suite(suite, analysis, "QA-1")


def test_demo_requires_explicit_configuration(tmp_path: Path):
    pipeline = QAPipeline(AppConfig(output_dir=tmp_path, demo_mode=False), gateway=Mock())
    with pytest.raises(ValueError, match="DEMO_MODE=true"):
        pipeline.run(["QA-1"], demo=True)


def test_pipeline_secret_redaction():
    config = AppConfig(llm_api_key="llm-secret", jira_api_token="jira-secret")
    pipeline = QAPipeline(config, gateway=Mock())
    message = pipeline._redact("Failed with llm-secret and Bearer jira-secret")
    assert "llm-secret" not in message
    assert "jira-secret" not in message
    assert "[REDACTED]" in message


def test_partial_multi_ticket_run_continues_after_failure(tmp_path: Path):
    gateway = Mock()
    gateway.fetch_issue.side_effect = [
        JiraProviderError("first ticket unavailable"),
        issue("QA-2"),
    ]
    pipeline = QAPipeline(AppConfig(output_dir=tmp_path), gateway=gateway)
    pipeline.run_ticket = Mock(
        side_effect=[
            TicketResult(ticket_key="QA-1", source="REST", status="FAILED", error="failed"),
            TicketResult(ticket_key="QA-2", source="REST", status="FAILED", error="failed"),
        ]
    )
    run = pipeline.run(["QA-1", "QA-2"], integration_mode="rest")
    assert [result.ticket_key for result in run.results] == ["QA-1", "QA-2"]
    assert pipeline.run_ticket.call_count == 2


def test_demo_fixture_pipeline_writes_artifacts_and_zip(tmp_path: Path, monkeypatch):
    import zipfile
    from io import BytesIO

    from jira_qa_crew.models import PlaywrightBundle, PlaywrightFile
    from jira_qa_crew.services import pipeline as pipeline_module
    from jira_qa_crew.services.artifacts import build_run_zip

    generated = [
        make_analysis("DEMO-1"),
        make_plan("DEMO-1"),
        make_suite("DEMO-1"),
        PlaywrightBundle(
            ticket_key="DEMO-1",
            readiness="NEEDS_CONFIGURATION",
            missing_configuration=["Confirm the login URL and stable selectors."],
            files=[
                PlaywrightFile(
                    path="tests/demo-1.spec.ts",
                    content=(
                        "import { test } from '@playwright/test';\n"
                        "test.skip('needs setup', async () => {});\n"
                    ),
                )
            ],
            documentation="Generated scaffold requires UI configuration.",
        ),
    ]

    class FakeCrew:
        def kickoff(self, inputs):
            return SimpleNamespace(
                tasks_output=[SimpleNamespace(pydantic=item) for item in generated]
            )

    monkeypatch.setattr(
        pipeline_module,
        "create_crew",
        lambda *_args, **_kwargs: FakeCrew(),
    )
    config = AppConfig(
        output_dir=tmp_path,
        demo_mode=True,
        llm_model="openai/gpt-4o-mini",
        llm_api_key="test-key",
    )
    run = QAPipeline(config, gateway=Mock()).run(["DEMO-1"], demo=True)

    assert run.results[0].status == "COMPLETED_WITH_WARNINGS"
    assert run.results[0].source == "DEMO"
    assert (tmp_path / run.run_id / "DEMO-1" / "test_plan.md").exists()
    assert (tmp_path / run.run_id / "run_summary.md").exists()
    archive = zipfile.ZipFile(BytesIO(build_run_zip(tmp_path, run.run_id)))
    assert f"{run.run_id}/DEMO-1/playwright/tests/demo-1.spec.ts" in archive.namelist()
