"""Streamlit entry point for Jira QA Crew."""

from __future__ import annotations

import logging
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from jira_qa_crew.config import AppConfig
from jira_qa_crew.exceptions import ConfigurationError
from jira_qa_crew.services.pipeline import STAGES, QAPipeline
from jira_qa_crew.services.tickets import parse_ticket_keys
from jira_qa_crew.ui.components import inject_theme, render_configuration_status
from jira_qa_crew.ui.results import render_run_results

APP_ROOT = Path(__file__).resolve().parent
load_dotenv(APP_ROOT / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

st.set_page_config(page_title="Jira QA Crew", page_icon="🧪", layout="wide")
inject_theme()
st.markdown("<div class='hero-kicker'>QA ARTIFACT GENERATION</div>", unsafe_allow_html=True)
st.title("Jira QA Crew")
st.markdown(
    "<p class='hero-subtitle'>Generate test plans, test cases, traceability, and "
    "Playwright automation directly from Jira.</p>",
    unsafe_allow_html=True,
)

try:
    config = AppConfig.load(secrets=st.secrets, env_file=APP_ROOT / ".env")
except ConfigurationError as error:
    st.error(str(error))
    st.stop()

with st.sidebar:
    render_configuration_status(config.redacted_status())
    st.caption(
        "Secrets are read from environment variables or Streamlit secrets and are never shown here."
    )
    st.divider()
    st.markdown("**Run limits**")
    st.caption(
        f"Maximum {config.pipeline_max_tickets} tickets · "
        f"{config.pipeline_ticket_timeout_seconds}s per-ticket budget"
    )

if "qa_pipeline_run" not in st.session_state:
    st.session_state.qa_pipeline_run = None
if "qa_pipeline_events" not in st.session_state:
    st.session_state.qa_pipeline_events = []

left, right = st.columns([3, 1])
with left:
    ticket_input = st.text_area(
        "Jira ticket IDs",
        height=118,
        placeholder="PROJ-123, PROJ-124\nPROJ-125",
        help="Separate ticket keys with commas, spaces, semicolons, or new lines.",
    )
with right:
    integration_choice = st.selectbox("Jira integration", ["Auto", "MCP only", "REST only"])
    integration_mode = {"Auto": "auto", "MCP only": "mcp", "REST only": "rest"}[integration_choice]
    with st.expander("Advanced settings"):
        st.caption(f"MCP transport: {config.jira_mcp_transport}")
        st.caption(f"REST API version: {config.jira_api_version}")
        st.caption(
            "Acceptance-criteria field: "
            f"{config.jira_acceptance_criteria_field or 'Not configured'}"
        )
        use_demo = False
        if config.demo_mode:
            use_demo = st.checkbox("Use explicitly enabled demo Jira fixture", value=False)
            st.warning(
                "Demo mode still uses the configured CrewAI LLM. "
                "It does not fall back automatically."
            )
        else:
            st.caption("Demo fixtures are disabled (DEMO_MODE=false).")

st.markdown("### Pipeline")
stage_columns = st.columns(4)
stage_labels = [
    "Jira Analyst",
    "Test Plan Writer",
    "Test Case Writer",
    "Playwright Coder",
]
stage_slots = {stage: stage_columns[index].empty() for index, stage in enumerate(STAGES)}
for stage, label in zip(STAGES, stage_labels, strict=True):
    stage_slots[stage].markdown(f"**Pending**  \n{label}")
progress_bar = st.progress(0, text="Waiting for a run")
activity_slot = st.empty()

if st.button("Analyze & Generate QA Pack", type="primary", use_container_width=True):
    try:
        parsed = parse_ticket_keys(
            ticket_input,
            pattern=config.jira_key_pattern,
            max_tickets=config.pipeline_max_tickets,
            max_chars=config.max_input_chars,
        )
        if parsed.duplicates:
            st.info("Duplicate keys ignored: " + ", ".join(parsed.duplicates))
        if parsed.invalid:
            st.warning(
                "Invalid keys will be skipped; valid keys continue: " + ", ".join(parsed.invalid)
            )
        if not parsed.keys:
            st.error("Enter at least one valid Jira issue key.")
            st.stop()
        config.validate_for_run(integration_mode)
    except (ValueError, ConfigurationError) as error:
        st.error(str(error))
        st.stop()

    completed_stages: set[tuple[str, str]] = set()
    st.session_state.qa_pipeline_events = []
    for key in parsed.keys:
        for stage, label in zip(STAGES, stage_labels, strict=True):
            stage_slots[stage].markdown(f"**Pending**  \n{label} · {key}")

    def on_progress(ticket: str, stage: str, state: str, message: str) -> None:
        stage_label = dict(zip(STAGES, stage_labels, strict=True)).get(
            stage, stage.replace("_", " ").title()
        )
        stage_state = state.upper()
        if stage in stage_slots:
            stage_slots[stage].markdown(f"**{stage_state}**  \n{stage_label} · {ticket}")
        if stage_state == "COMPLETED":
            completed_stages.add((ticket, stage))
        progress_bar.progress(
            min(len(completed_stages) / max(len(parsed.keys) * len(STAGES), 1), 1.0),
            text=f"Processing {ticket}",
        )
        st.session_state.qa_pipeline_events.append(
            {
                "ticket": ticket,
                "stage": stage_label,
                "state": stage_state,
                "message": message,
            }
        )
        activity_slot.caption(f"{ticket} · {stage_state} · {message}")

    try:
        pipeline = QAPipeline(config)
        run = pipeline.run(
            parsed.keys,
            integration_mode=integration_mode,
            progress=on_progress,
            demo=use_demo if config.demo_mode else False,
        )
        st.session_state.qa_pipeline_run = run
        progress_bar.progress(1.0, text="Run finished")
        if any(result.status != "FAILED" for result in run.results):
            st.success(f"Run finished · {run.run_id}")
        else:
            st.error(f"No ticket completed successfully · {run.run_id}")
    except Exception as error:
        st.error(f"Run could not start: {error}")

run = st.session_state.qa_pipeline_run
if run:
    st.divider()
    render_run_results(run, config.output_dir)
    with st.expander("Pipeline activity", expanded=False):
        st.dataframe(
            st.session_state.qa_pipeline_events,
            use_container_width=True,
            hide_index=True,
        )
