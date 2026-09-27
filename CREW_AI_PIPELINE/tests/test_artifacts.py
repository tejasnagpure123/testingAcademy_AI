import json
import zipfile
from dataclasses import dataclass
from io import BytesIO

import pytest
from conftest import make_analysis, make_plan, make_suite

from jira_qa_crew.models import PlaywrightBundle, PlaywrightFile, TicketResult
from jira_qa_crew.services.artifacts import build_run_zip, write_ticket_artifacts
from jira_qa_crew.services.renderers import (
    test_cases_csv as render_test_cases_csv,
)
from jira_qa_crew.services.renderers import (
    test_plan_markdown as render_test_plan_markdown,
)
from jira_qa_crew.services.renderers import (
    traceability_csv,
)
from jira_qa_crew.services.validation import coverage_matrix


def make_ticket(key="QA-1"):
    result = TicketResult(
        ticket_key=key,
        source="REST",
        status="COMPLETED_WITH_WARNINGS",
        analysis=make_analysis(key),
        plan=make_plan(key),
        suite=make_suite(key),
        playwright=PlaywrightBundle(
            ticket_key=key,
            readiness="NEEDS_CONFIGURATION",
            missing_configuration=["Confirm login URL and stable field selectors."],
            files=[
                PlaywrightFile(
                    path=f"tests/{key.lower()}.spec.ts",
                    content=(
                        "import { test } from '@playwright/test';\n"
                        "test.skip('placeholder', async () => {});\n"
                    ),
                )
            ],
            documentation="Selectors require confirmation.",
        ),
    )
    return result


def test_renderers_include_plan_sections_traceability_and_csv():
    plan = render_test_plan_markdown(make_plan())
    assert len([line for line in plan.splitlines() if line.startswith("## ")]) == 12
    csv_text = render_test_cases_csv(make_suite())
    assert "QA-1-TC-001" in csv_text
    trace = traceability_csv(make_analysis(), make_suite())
    assert "AC-001" in trace and "COVERED" in trace
    assert coverage_matrix(make_analysis(), make_suite())[0]["coverage_status"] == "COVERED"


def test_artifact_tree_and_zip(tmp_path):
    ticket = make_ticket()
    ticket.artifacts = write_ticket_artifacts("RUN-TEST", ticket, tmp_path)
    expected = tmp_path / "RUN-TEST" / "QA-1" / "playwright" / "tests" / "qa-1.spec.ts"
    assert expected.exists()
    assert (
        json.loads((tmp_path / "RUN-TEST" / "QA-1" / "manifest.json").read_text())["source"]
        == "REST"
    )

    @dataclass
    class Run:
        run_id: str = "RUN-TEST"
        started_at: str = "start"
        completed_at: str = "end"
        results: list = None

    from jira_qa_crew.services.artifacts import write_run_artifacts

    run = Run(results=[ticket])
    write_run_artifacts(run, tmp_path)
    archive = zipfile.ZipFile(BytesIO(build_run_zip(tmp_path, "RUN-TEST")))
    assert "RUN-TEST/run_summary.md" in archive.namelist()
    assert "RUN-TEST/QA-1/test_plan.md" in archive.namelist()


def test_artifacts_reject_path_traversal(tmp_path):
    ticket = make_ticket("../ESCAPE")
    with pytest.raises(ValueError, match="Unsafe"):
        write_ticket_artifacts("RUN-TEST", ticket, tmp_path)
