from jira_qa_crew.models import (
    EvidenceClass,
    Finding,
    RequirementAnalysis,
    TestCase,
    TestCaseSuite,
    TestPlan,
    TestScenario,
    TestStep,
)


def make_analysis(ticket_key="QA-1"):
    return RequirementAnalysis(
        ticket_key=ticket_key,
        summary="Required fields must be validated",
        issue_type="Bug",
        status="Open",
        priority="Medium",
        functional_requirements=[
            Finding(
                identifier="REQ-001",
                text="Prevent an empty login submission.",
                evidence=EvidenceClass.EXPLICIT,
                source_excerpt="Expected: empty fields are blocked.",
            )
        ],
        acceptance_criteria=[
            Finding(
                identifier="AC-001",
                text="Show required-field messages for empty inputs.",
                evidence=EvidenceClass.EXPLICIT,
                source_excerpt="Expected: show inline validation.",
            )
        ],
        missing_information=["Confirmed login URL is not in the ticket."],
    )


def make_plan(ticket_key="QA-1"):
    return TestPlan(
        ticket_key=ticket_key,
        executive_summary="Verify required-field login validation.",
        test_objectives=["Confirm empty submissions are blocked."],
        in_scope=["Login form required-field validation."],
        out_of_scope=["Authentication service behavior."],
        requirements_and_acceptance_criteria_coverage=["REQ-001 and AC-001 are covered."],
        test_strategy_levels_and_types=["Focused UI functional validation."],
        environment_tools_and_browsers=[
            "Target login UI and supported browsers; exact environment is unconfirmed."
        ],
        test_data_requirements=["No credentials are needed for the empty-field case."],
        high_level_scenarios=[
            TestScenario(
                title="Submit empty form",
                objective="Verify required-field errors and block submission.",
                requirement_ids=["REQ-001"],
                acceptance_criteria_ids=["AC-001"],
                test_type="Negative",
            )
        ],
        entry_and_exit_criteria=[
            "Entry: test environment is available.",
            "Exit: all expected validation checks pass.",
        ],
        risks_dependencies_assumptions_mitigations=["Confirm selectors before automating."],
        execution_defect_management_reporting_deliverables=[
            "Record results and link failures to QA-1."
        ],
    )


def make_suite(ticket_key="QA-1"):
    return TestCaseSuite(
        ticket_key=ticket_key,
        test_cases=[
            TestCase(
                test_case_id=f"{ticket_key}-TC-001",
                jira_key=ticket_key,
                requirement_ids=["REQ-001"],
                acceptance_criteria_ids=["AC-001"],
                title="Empty login fields show required messages",
                objective="Ensure the login form is blocked when both inputs are empty.",
                priority="High",
                test_type="Negative",
                preconditions=["Login page is available."],
                test_data=["Email: empty", "Password: empty"],
                steps=[
                    TestStep(
                        order=1,
                        action="Submit without values.",
                        expected_result="Inline required messages appear.",
                    )
                ],
                expected_result="No login request is sent.",
                automation_candidate="Partial",
                automation_rationale="Automation is feasible after selectors are confirmed.",
                tags=["login", "validation"],
                assumptions_or_blockers=["Login URL and selectors require confirmation."],
            )
        ],
    )
