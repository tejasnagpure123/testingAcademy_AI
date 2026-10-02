import sys
from datetime import UTC, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from jira_qa_crew.models import TicketResult
from jira_qa_crew.services.pipeline import PipelineRun

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_streamlit_initial_render():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    assert not app.exception
    assert any("Jira QA Crew" in title.value for title in app.title)
    assert any("Jira ticket IDs" in element.label for element in app.text_area)


def test_streamlit_empty_ticket_validation():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("at least one valid Jira issue key" in item.value for item in app.error)


def test_streamlit_renders_fixture_run_results():
    now = datetime.now(UTC).isoformat()
    run = PipelineRun(
        run_id="RUN-TEST",
        started_at=now,
        completed_at=now,
        results=[
            TicketResult(
                ticket_key="QA-FAILED",
                source="UNKNOWN",
                status="FAILED",
                error="Fixture-only failure state",
            )
        ],
    )
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
    app.session_state["qa_pipeline_run"] = run
    app.session_state["qa_pipeline_events"] = []
    app.run()
    assert not app.exception
    assert any("Fixture-only failure state" in item.value for item in app.error)
