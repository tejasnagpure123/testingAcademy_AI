"""Validated domain models exchanged between agents and renderers."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceClass(StrEnum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"
    MISSING = "MISSING"
    ASSUMPTION_REQUIRING_CONFIRMATION = "ASSUMPTION_REQUIRING_CONFIRMATION"


class JiraIssue(StrictModel):
    key: str
    summary: str
    description: str = ""
    issue_type: str = "Unknown"
    status: str = "Unknown"
    priority: str = "Unspecified"
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    parent_key: str | None = None
    subtasks: list[str] = Field(default_factory=list)
    linked_issues: list[str] = Field(default_factory=list)
    acceptance_criteria: str = ""
    comments: list[str] = Field(default_factory=list)
    source: Literal["MCP", "REST", "DEMO"]


class Finding(StrictModel):
    identifier: str
    text: str
    evidence: EvidenceClass
    source_excerpt: str = ""


class RequirementAnalysis(StrictModel):
    ticket_key: str
    summary: str
    issue_type: str
    status: str
    priority: str
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    parent_and_subtasks: list[str] = Field(default_factory=list)
    linked_issues: list[str] = Field(default_factory=list)
    functional_requirements: list[Finding] = Field(default_factory=list)
    non_functional_requirements: list[Finding] = Field(default_factory=list)
    acceptance_criteria: list[Finding] = Field(default_factory=list)
    business_rules: list[Finding] = Field(default_factory=list)
    dependencies: list[Finding] = Field(default_factory=list)
    constraints: list[Finding] = Field(default_factory=list)
    risks: list[Finding] = Field(default_factory=list)
    assumptions: list[Finding] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class TestScenario(StrictModel):
    title: str
    objective: str
    requirement_ids: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    test_type: str


class TestPlan(StrictModel):
    ticket_key: str
    executive_summary: str
    test_objectives: list[str]
    in_scope: list[str]
    out_of_scope: list[str]
    requirements_and_acceptance_criteria_coverage: list[str]
    test_strategy_levels_and_types: list[str]
    environment_tools_and_browsers: list[str]
    test_data_requirements: list[str]
    high_level_scenarios: list[TestScenario]
    entry_and_exit_criteria: list[str]
    risks_dependencies_assumptions_mitigations: list[str]
    execution_defect_management_reporting_deliverables: list[str]


class TestStep(StrictModel):
    """One ordered action and its observable result."""

    order: int = Field(ge=1)
    action: str
    expected_result: str


class TestCase(StrictModel):
    test_case_id: str
    jira_key: str
    requirement_ids: list[str] = Field(default_factory=list)
    acceptance_criteria_ids: list[str] = Field(default_factory=list)
    title: str
    objective: str
    priority: Literal["Critical", "High", "Medium", "Low"]
    test_type: str
    preconditions: list[str] = Field(default_factory=list)
    test_data: list[str] = Field(default_factory=list)
    steps: list[TestStep]
    expected_result: str
    automation_candidate: Literal["Yes", "No", "Partial"]
    automation_rationale: str
    tags: list[str] = Field(default_factory=list)
    assumptions_or_blockers: list[str] = Field(default_factory=list)


class TestCaseSuite(StrictModel):
    ticket_key: str
    test_cases: list[TestCase]


class PlaywrightFile(StrictModel):
    path: str
    content: str


class PlaywrightBundle(StrictModel):
    ticket_key: str
    readiness: Literal["READY", "NEEDS_CONFIGURATION"]
    missing_configuration: list[str] = Field(default_factory=list)
    files: list[PlaywrightFile]
    documentation: str


class TicketResult(StrictModel):
    ticket_key: str
    source: Literal["MCP", "REST", "DEMO", "UNKNOWN"] = "UNKNOWN"
    status: Literal["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED"]
    started_at: str = ""
    completed_at: str = ""
    issue: JiraIssue | None = None
    analysis: RequirementAnalysis | None = None
    plan: TestPlan | None = None
    suite: TestCaseSuite | None = None
    playwright: PlaywrightBundle | None = None
    artifacts: dict[str, str] = Field(default_factory=dict)
    error: str | None = None
