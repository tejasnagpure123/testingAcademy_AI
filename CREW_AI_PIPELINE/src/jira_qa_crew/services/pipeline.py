"""Per-ticket CrewAI orchestration with one repair attempt and partial results."""

from __future__ import annotations

import json
import logging
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from jira_qa_crew.config import AppConfig
from jira_qa_crew.crew.factory import create_crew
from jira_qa_crew.exceptions import OutputValidationError
from jira_qa_crew.jira.gateway import JiraGateway
from jira_qa_crew.models import (
    JiraIssue,
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TestPlan,
    TicketResult,
)
from jira_qa_crew.services.artifacts import write_run_artifacts, write_ticket_artifacts
from jira_qa_crew.services.validation import (
    validate_analysis,
    validate_plan,
    validate_playwright,
    validate_suite,
)

logger = logging.getLogger(__name__)
STAGES = ["jira_analysis", "test_plan", "test_cases", "playwright"]


@dataclass
class PipelineRun:
    run_id: str
    started_at: str
    completed_at: str = ""
    results: list[TicketResult] = field(default_factory=list)
    artifact_dir: str = ""


class QAPipeline:
    def __init__(self, config: AppConfig, gateway: JiraGateway | None = None):
        self.config = config
        self.gateway = gateway or JiraGateway(config)

    def run(
        self,
        tickets: list[str],
        integration_mode: str = "auto",
        progress: Callable[[str, str, str, str], None] | None = None,
        demo: bool = False,
    ) -> PipelineRun:
        if demo and not self.config.demo_mode:
            raise ValueError(
                "Demo data is unavailable unless DEMO_MODE=true is explicitly configured."
            )
        run_id = datetime.now(UTC).strftime("RUN-%Y%m%d-%H%M%S-") + secrets.token_hex(3).upper()
        run = PipelineRun(run_id=run_id, started_at=datetime.now(UTC).isoformat())
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        for ticket_key in tickets:
            result = self.run_ticket(ticket_key, integration_mode, run_id, progress, demo)
            run.results.append(result)
        run.completed_at = datetime.now(UTC).isoformat()
        run.artifact_dir = str(self.config.output_dir / run_id)
        write_run_artifacts(run, self.config.output_dir)
        return run

    def run_ticket(
        self,
        ticket_key: str,
        integration_mode: str,
        run_id: str,
        progress: Callable[[str, str, str, str], None] | None,
        demo: bool,
    ) -> TicketResult:
        result = TicketResult(
            ticket_key=ticket_key,
            status="FAILED",
            started_at=datetime.now(UTC).isoformat(),
        )

        def emit(stage: str, state: str, message: str) -> None:
            if progress:
                progress(ticket_key, stage, state, self._redact(message))

        analysis: RequirementAnalysis | None = None
        plan: TestPlan | None = None
        suite: TestCaseSuite | None = None
        bundle: PlaywrightBundle | None = None
        try:
            emit(
                "jira_analysis",
                "RUNNING",
                "Fetching Jira issue through configured provider gateway.",
            )
            issue = self._get_issue(ticket_key, integration_mode, demo)
            result.issue = issue
            result.source = issue.source
            result.status = "COMPLETED_WITH_WARNINGS"
            issue_json = issue.model_dump_json(indent=2)
            repair_feedback = ""

            for attempt in range(2):
                try:
                    crew = create_crew(
                        self.config,
                        self.gateway,
                        ticket_key,
                        integration_mode,
                        issue_json,
                        issue,
                        emit,
                        repair_feedback=repair_feedback,
                    )
                    crew_result = crew.kickoff(inputs={"issue_json": issue_json})
                    outputs = crew_result.tasks_output
                    analysis = self._output(outputs, 0, RequirementAnalysis)
                    validate_analysis(analysis, ticket_key)
                    plan = self._output(outputs, 1, TestPlan)
                    validate_plan(plan, analysis, ticket_key)
                    suite = self._output(outputs, 2, TestCaseSuite)
                    validate_suite(suite, analysis, ticket_key)
                    bundle = self._output(outputs, 3, PlaywrightBundle)
                    validate_playwright(bundle, suite, ticket_key)
                    break
                except (
                    OutputValidationError,
                    ValidationError,
                    AttributeError,
                    IndexError,
                    TypeError,
                ) as error:
                    if attempt:
                        raise OutputValidationError(
                            "Structured QA output remained invalid after one repair attempt: "
                            f"{error}"
                        ) from error
                    repair_feedback = str(error)[:1200]
                    emit(
                        "validation",
                        "WARNING",
                        "Output validation failed; starting the single repair attempt.",
                    )

            result.analysis = analysis
            result.plan = plan
            result.suite = suite
            result.playwright = bundle
            warnings = bool(bundle and bundle.readiness == "NEEDS_CONFIGURATION")
            result.status = "COMPLETED_WITH_WARNINGS" if warnings else "COMPLETED"
            result.artifacts = write_ticket_artifacts(run_id, result, self.config.output_dir)
            for stage in STAGES:
                emit(stage, "COMPLETED", "Validated stage output is ready.")
        except Exception as error:
            result.analysis = analysis
            result.plan = plan
            result.suite = suite
            result.playwright = bundle
            result.error = self._redact(str(error)) or type(error).__name__
            result.status = (
                "COMPLETED_WITH_WARNINGS" if any((analysis, plan, suite, bundle)) else "FAILED"
            )
            if result.status != "FAILED":
                try:
                    result.artifacts = write_ticket_artifacts(
                        run_id, result, self.config.output_dir
                    )
                except Exception:
                    logger.exception("Could not persist partial QA artifacts for %s.", ticket_key)
            emit("pipeline", "FAILED", result.error)
            logger.warning("Ticket %s failed (%s).", ticket_key, type(error).__name__)
        result.completed_at = datetime.now(UTC).isoformat()
        return result

    def _get_issue(self, ticket_key: str, mode: str, demo: bool) -> JiraIssue:
        if demo:
            project_root = Path(__file__).resolve().parents[3]
            fixture = project_root / "fixtures" / "demo_issue.json"
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            payload["key"] = ticket_key
            payload["source"] = "DEMO"
            return JiraIssue.model_validate(payload)
        return self.gateway.fetch_issue(ticket_key, mode=mode)

    @staticmethod
    def _output(outputs: list, index: int, model: type):
        value = outputs[index].pydantic
        if not isinstance(value, model):
            raise OutputValidationError(
                f"CrewAI stage {index + 1} did not produce {model.__name__}."
            )
        return value

    def _redact(self, text: str) -> str:
        for secret in (
            self.config.llm_api_key,
            self.config.jira_api_token,
            self.config.jira_bearer_token,
        ):
            if secret:
                text = text.replace(secret, "[REDACTED]")
        text = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[REDACTED]", text)
        return text[:2000]
