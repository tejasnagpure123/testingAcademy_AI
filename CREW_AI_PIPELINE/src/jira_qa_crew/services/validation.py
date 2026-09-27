"""Deterministic schema, duplicate-ID, and traceability validation."""

from __future__ import annotations

import re

from jira_qa_crew.exceptions import OutputValidationError
from jira_qa_crew.models import (
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TestPlan,
)


def _unique_ids(identifiers: list[str], label: str) -> None:
    if len(identifiers) != len(set(identifiers)):
        raise OutputValidationError(f"Duplicate {label} identifiers were generated.")


def validate_analysis(analysis: RequirementAnalysis, ticket_key: str) -> None:
    if analysis.ticket_key.upper() != ticket_key.upper():
        raise OutputValidationError(
            "Requirement analysis ticket key does not match the requested issue."
        )
    requirement_ids = [
        item.identifier
        for item in analysis.functional_requirements + analysis.non_functional_requirements
    ]
    acceptance_ids = [item.identifier for item in analysis.acceptance_criteria]
    if any(not re.fullmatch(r"REQ-\d{3,}", value) for value in requirement_ids):
        raise OutputValidationError("Requirement IDs must use stable REQ-001 identifiers.")
    if any(not re.fullmatch(r"AC-\d{3,}", value) for value in acceptance_ids):
        raise OutputValidationError("Acceptance criteria IDs must use stable AC-001 identifiers.")
    _unique_ids(requirement_ids, "requirement")
    _unique_ids(acceptance_ids, "acceptance-criteria")
    for finding in (
        analysis.functional_requirements
        + analysis.non_functional_requirements
        + analysis.acceptance_criteria
    ):
        if finding.evidence.value == "EXPLICIT" and not finding.source_excerpt:
            raise OutputValidationError(
                f"Explicit finding {finding.identifier} needs a Jira source excerpt."
            )


def validate_plan(plan: TestPlan, analysis: RequirementAnalysis, ticket_key: str) -> None:
    if plan.ticket_key.upper() != ticket_key.upper():
        raise OutputValidationError("Test plan ticket key does not match the requested issue.")
    section_values = [
        plan.executive_summary,
        plan.test_objectives,
        plan.in_scope,
        plan.out_of_scope,
        plan.requirements_and_acceptance_criteria_coverage,
        plan.test_strategy_levels_and_types,
        plan.environment_tools_and_browsers,
        plan.test_data_requirements,
        plan.high_level_scenarios,
        plan.entry_and_exit_criteria,
        plan.risks_dependencies_assumptions_mitigations,
        plan.execution_defect_management_reporting_deliverables,
    ]
    if any(not value for value in section_values):
        raise OutputValidationError("The test plan must populate all 12 required sections.")
    known_ids = {
        item.identifier
        for item in (
            analysis.functional_requirements
            + analysis.non_functional_requirements
            + analysis.acceptance_criteria
        )
    }
    for scenario in plan.high_level_scenarios:
        references = scenario.requirement_ids + scenario.acceptance_criteria_ids
        if not references or any(reference not in known_ids for reference in references):
            raise OutputValidationError("Each scenario must reference known REQ/AC identifiers.")


def validate_suite(suite: TestCaseSuite, analysis: RequirementAnalysis, ticket_key: str) -> None:
    if suite.ticket_key.upper() != ticket_key.upper() or not suite.test_cases:
        raise OutputValidationError("Test-case suite is empty or belongs to a different ticket.")
    case_ids = [case.test_case_id for case in suite.test_cases]
    _unique_ids(case_ids, "test-case")
    if any(not re.fullmatch(rf"{re.escape(ticket_key)}-TC-\d{{3,}}", value) for value in case_ids):
        raise OutputValidationError(
            "Test-case IDs must use the current ticket key and TC-001 format."
        )
    known_ids = {
        item.identifier
        for item in (
            analysis.functional_requirements
            + analysis.non_functional_requirements
            + analysis.acceptance_criteria
        )
    }
    for case in suite.test_cases:
        if case.jira_key.upper() != ticket_key.upper():
            raise OutputValidationError("A test case references a different Jira ticket.")
        if not case.steps:
            raise OutputValidationError(f"Test case {case.test_case_id} has no steps.")
        if any(step.order != index for index, step in enumerate(case.steps, start=1)):
            raise OutputValidationError(
                f"Test case {case.test_case_id} steps must have contiguous order values."
            )
        references = case.requirement_ids + case.acceptance_criteria_ids
        if not references or any(reference not in known_ids for reference in references):
            raise OutputValidationError(
                f"Test case {case.test_case_id} has missing or unknown traceability IDs."
            )
    uncovered = {item.identifier for item in analysis.acceptance_criteria} - {
        identifier for case in suite.test_cases for identifier in case.acceptance_criteria_ids
    }
    if uncovered:
        raise OutputValidationError(
            f"Acceptance criteria have no test coverage: {', '.join(sorted(uncovered))}."
        )


def validate_playwright(bundle: PlaywrightBundle, suite: TestCaseSuite, ticket_key: str) -> None:
    if bundle.ticket_key.upper() != ticket_key.upper() or not bundle.files:
        raise OutputValidationError("Playwright bundle is empty or belongs to another ticket.")
    if bundle.readiness == "NEEDS_CONFIGURATION" and not bundle.missing_configuration:
        raise OutputValidationError(
            "NEEDS_CONFIGURATION requires explicit missing configuration details."
        )
    paths = [file.path for file in bundle.files]
    _unique_ids(paths, "Playwright file path")
    if any(not path.endswith(".ts") for path in paths):
        raise OutputValidationError("Playwright bundle files must be TypeScript (.ts) files.")
    if any("waitForTimeout(" in file.content for file in bundle.files):
        raise OutputValidationError("Generated Playwright code must not use page.waitForTimeout().")
    eligible_ids = {
        case.test_case_id
        for case in suite.test_cases
        if case.automation_candidate in {"Yes", "Partial"}
    }
    automated_ids = set(
        re.findall(
            r"\b[A-Z][A-Z0-9_]*-TC-\d{3,}\b",
            "\n".join(file.content for file in bundle.files),
        )
    )
    if not automated_ids.issubset(eligible_ids):
        raise OutputValidationError("Playwright code references a case not marked for automation.")


def coverage_matrix(analysis: RequirementAnalysis, suite: TestCaseSuite) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    cases = suite.test_cases
    for finding in (
        analysis.functional_requirements
        + analysis.non_functional_requirements
        + analysis.acceptance_criteria
    ):
        linked = [
            case
            for case in cases
            if finding.identifier in case.requirement_ids + case.acceptance_criteria_ids
        ]
        rows.append(
            {
                "requirement_id": finding.identifier,
                "evidence": finding.evidence.value,
                "test_cases": ", ".join(case.test_case_id for case in linked),
                "automated_tests": ", ".join(
                    case.test_case_id
                    for case in linked
                    if case.automation_candidate in {"Yes", "Partial"}
                ),
                "coverage_status": "COVERED" if linked else "ORPHAN_REQUIREMENT",
            }
        )
    return rows
