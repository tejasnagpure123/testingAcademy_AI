"""Deterministic Markdown, CSV, and JSON artifact rendering."""

from __future__ import annotations

import csv
import io
import json

from jira_qa_crew.models import RequirementAnalysis, TestCaseSuite, TestPlan, TicketResult
from jira_qa_crew.services.validation import coverage_matrix


def requirements_markdown(analysis: RequirementAnalysis) -> str:
    lines = [
        f"# Requirements Analysis: {analysis.ticket_key}",
        "",
        f"**Summary:** {analysis.summary}",
        "",
    ]
    metadata = [
        ("Issue type", analysis.issue_type),
        ("Status", analysis.status),
        ("Priority", analysis.priority),
        ("Labels", ", ".join(analysis.labels) or "None"),
        ("Components", ", ".join(analysis.components) or "None"),
        ("Parent / subtasks", ", ".join(analysis.parent_and_subtasks) or "None"),
        ("Linked issues", ", ".join(analysis.linked_issues) or "None"),
    ]
    lines.extend(f"- **{label}:** {value}" for label, value in metadata)
    groups = [
        ("Functional Requirements", analysis.functional_requirements),
        ("Non-Functional Requirements", analysis.non_functional_requirements),
        ("Acceptance Criteria", analysis.acceptance_criteria),
        ("Business Rules", analysis.business_rules),
        ("Dependencies", analysis.dependencies),
        ("Constraints", analysis.constraints),
        ("Risks", analysis.risks),
        ("Assumptions", analysis.assumptions),
    ]
    for heading, findings in groups:
        lines.extend(["", f"## {heading}"])
        if not findings:
            lines.append("- None identified from the available Jira information.")
        for finding in findings:
            lines.append(f"- **{finding.identifier}** [{finding.evidence.value}]: {finding.text}")
            if finding.source_excerpt:
                lines.append(f"  - Jira evidence: {finding.source_excerpt}")
    for heading, values in (
        ("Missing Information", analysis.missing_information),
        ("Open Questions", analysis.open_questions),
    ):
        lines.extend(["", f"## {heading}"])
        lines.extend(f"- {value}" for value in values or ["None identified."])
    return "\n".join(lines) + "\n"


def test_plan_markdown(plan: TestPlan) -> str:
    sections = [
        ("Executive Summary", plan.executive_summary),
        ("Test Objectives", plan.test_objectives),
        ("In Scope", plan.in_scope),
        ("Out of Scope", plan.out_of_scope),
        (
            "Requirements and Acceptance-Criteria Coverage",
            plan.requirements_and_acceptance_criteria_coverage,
        ),
        ("Test Strategy, Levels, and Test Types", plan.test_strategy_levels_and_types),
        ("Test Environment, Tools, and Browser Coverage", plan.environment_tools_and_browsers),
        ("Test Data Requirements", plan.test_data_requirements),
        ("High-Level Test Scenarios", plan.high_level_scenarios),
        ("Entry and Exit Criteria", plan.entry_and_exit_criteria),
        (
            "Risks, Dependencies, Assumptions, and Mitigations",
            plan.risks_dependencies_assumptions_mitigations,
        ),
        (
            "Execution, Defect Management, Reporting, and Deliverables",
            plan.execution_defect_management_reporting_deliverables,
        ),
    ]
    lines = [f"# Test Plan: {plan.ticket_key}"]
    for index, (heading, value) in enumerate(sections, start=1):
        lines.extend(["", f"## {index}. {heading}"])
        if isinstance(value, str):
            lines.append(value)
        elif heading == "High-Level Test Scenarios":
            for scenario in value:
                trace = ", ".join(scenario.requirement_ids + scenario.acceptance_criteria_ids)
                lines.append(
                    f"- **{scenario.title}** ({scenario.test_type}; {trace}): {scenario.objective}"
                )
        else:
            lines.extend(f"- {item}" for item in value)
    return "\n".join(lines) + "\n"


def test_cases_markdown(suite: TestCaseSuite) -> str:
    lines = [f"# Test Cases: {suite.ticket_key}"]
    for case in suite.test_cases:
        lines.extend(
            [
                "",
                f"## {case.test_case_id}: {case.title}",
                f"- **Priority:** {case.priority}",
                f"- **Type:** {case.test_type}",
                f"- **Requirements:** {', '.join(case.requirement_ids) or 'None'}",
                f"- **Acceptance criteria:** {', '.join(case.acceptance_criteria_ids) or 'None'}",
                f"- **Automation:** {case.automation_candidate} ({case.automation_rationale})",
                f"- **Objective:** {case.objective}",
                "- **Preconditions:** " + ("; ".join(case.preconditions) or "None"),
                "- **Test data:** " + ("; ".join(case.test_data) or "None"),
                "- **Steps:**",
            ]
        )
        lines.extend(
            f"  {step.order}. {step.action} Expected: {step.expected_result}" for step in case.steps
        )
        lines.extend(
            [
                f"- **Expected result:** {case.expected_result}",
                f"- **Tags:** {', '.join(case.tags)}",
            ]
        )
        if case.assumptions_or_blockers:
            lines.append(f"- **Assumptions / blockers:** {'; '.join(case.assumptions_or_blockers)}")
    return "\n".join(lines) + "\n"


def test_cases_csv(suite: TestCaseSuite) -> str:
    buffer = io.StringIO(newline="")
    fields = [
        "test_case_id",
        "jira_key",
        "requirement_ids",
        "acceptance_criteria_ids",
        "title",
        "objective",
        "priority",
        "test_type",
        "preconditions",
        "test_data",
        "steps",
        "expected_result",
        "automation_candidate",
        "automation_rationale",
        "tags",
        "assumptions_or_blockers",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for case in suite.test_cases:
        row = case.model_dump()
        for key in (
            "requirement_ids",
            "acceptance_criteria_ids",
            "preconditions",
            "test_data",
            "tags",
            "assumptions_or_blockers",
        ):
            row[key] = " | ".join(row[key])
        row["steps"] = json.dumps(row["steps"], ensure_ascii=False)
        writer.writerow(row)
    return buffer.getvalue()


def traceability_csv(analysis: RequirementAnalysis, suite: TestCaseSuite) -> str:
    buffer = io.StringIO(newline="")
    fields = ["requirement_id", "evidence", "test_cases", "automated_tests", "coverage_status"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(coverage_matrix(analysis, suite))
    return buffer.getvalue()


def playwright_markdown(ticket: TicketResult) -> str:
    bundle = ticket.playwright
    if not bundle:
        return (
            f"# Playwright: {ticket.ticket_key}\n\nNo validated Playwright bundle was produced.\n"
        )
    lines = [f"# Playwright Tests: {ticket.ticket_key}", "", f"**Readiness:** {bundle.readiness}"]
    if bundle.missing_configuration:
        lines.extend(
            ["", "## Configuration Needed", *[f"- {item}" for item in bundle.missing_configuration]]
        )
    lines.extend(["", bundle.documentation])
    for file in bundle.files:
        lines.extend(["", f"## `{file.path}`", "```typescript", file.content, "```"])
    return "\n".join(lines) + "\n"


def ticket_manifest(ticket: TicketResult, file_names: list[str]) -> dict:
    return {
        "ticket_key": ticket.ticket_key,
        "status": ticket.status,
        "source": ticket.source,
        "automation_readiness": ticket.playwright.readiness if ticket.playwright else None,
        "artifacts": file_names,
        "error": ticket.error,
    }
