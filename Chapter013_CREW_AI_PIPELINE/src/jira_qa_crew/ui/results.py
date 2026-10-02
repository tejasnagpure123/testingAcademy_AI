"""Ticket results, filters, and artifact downloads."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from jira_qa_crew.models import TicketResult
from jira_qa_crew.services.artifacts import build_run_zip
from jira_qa_crew.services.validation import coverage_matrix


def render_run_results(run, output_dir: Path) -> None:
    counts = {
        status: sum(result.status == status for result in run.results)
        for status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED")
    }
    columns = st.columns(4)
    columns[0].metric("Tickets", len(run.results))
    columns[1].metric("Completed", counts["COMPLETED"])
    columns[2].metric("Warnings", counts["COMPLETED_WITH_WARNINGS"])
    columns[3].metric("Failed", counts["FAILED"])
    st.caption(f"Run {run.run_id} · Started {run.started_at} · Completed {run.completed_at}")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Ticket": result.ticket_key,
                    "Status": result.status,
                    "Provider": result.source,
                    "Started": result.started_at,
                    "Completed": result.completed_at,
                    "Automation": (
                        result.playwright.readiness if result.playwright else "Not generated"
                    ),
                    "Error": result.error or "",
                }
                for result in run.results
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    ticket_tabs = st.tabs([result.ticket_key for result in run.results]) if run.results else []
    for tab, result in zip(ticket_tabs, run.results, strict=True):
        with tab:
            _render_ticket(result)
    _render_zip_download(run, output_dir)


def _render_ticket(result: TicketResult) -> None:
    st.markdown(
        f"<div class='status-strip'>Provider: <b>{result.source}</b> · Status: "
        f"<b>{result.status}</b></div>",
        unsafe_allow_html=True,
    )
    if result.error:
        st.error(result.error)
    tabs = st.tabs(
        [
            "Requirements Analysis",
            "Test Plan",
            "Test Cases",
            "Playwright",
            "Traceability",
            "Run Details",
        ]
    )
    with tabs[0]:
        if result.analysis:
            st.markdown(_read_artifact(result, "requirements_analysis.md"))
            st.warning(
                "Missing information: "
                + ("; ".join(result.analysis.missing_information) or "None identified")
            )
        else:
            st.info("Requirements analysis was not completed.")
    with tabs[1]:
        st.markdown(_read_artifact(result, "test_plan.md") or "Test plan was not completed.")
    with tabs[2]:
        if result.suite:
            _render_test_case_table(result)
        else:
            st.info("Test cases were not completed.")
    with tabs[3]:
        if result.playwright:
            st.caption(f"Automation readiness: {result.playwright.readiness}")
            if result.playwright.missing_configuration:
                st.warning(
                    "Configuration needed: " + "; ".join(result.playwright.missing_configuration)
                )
            for file in result.playwright.files:
                st.code(file.content, language="typescript")
        else:
            st.info("Playwright automation was not completed.")
    with tabs[4]:
        if result.analysis and result.suite:
            rows = coverage_matrix(result.analysis, result.suite)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            covered = sum(row["coverage_status"] == "COVERED" for row in rows)
            st.metric("Traceability coverage", f"{covered}/{len(rows)}")
        else:
            st.info("Traceability is available after analysis and test-case generation.")
    with tabs[5]:
        details = {
            "Ticket": result.ticket_key,
            "Provider": result.source,
            "Status": result.status,
            "Started": result.started_at,
            "Completed": result.completed_at,
            "Artifacts": list(result.artifacts),
            "Error": result.error,
        }
        st.json(details)
        if result.issue:
            st.caption(
                f"Jira status: {result.issue.status} · Jira priority: {result.issue.priority}"
            )
    _render_ticket_downloads(result)


def _render_test_case_table(result: TicketResult) -> None:
    cases = [case.model_dump() for case in result.suite.test_cases]
    dataframe = pd.DataFrame(cases)
    search = st.text_input("Search test cases", key=f"search_{result.ticket_key}")
    columns = st.columns(4)
    priority = columns[0].selectbox(
        "Priority",
        ["All", *sorted(dataframe.priority.unique())],
        key=f"priority_{result.ticket_key}",
    )
    test_type = columns[1].selectbox(
        "Type",
        ["All", *sorted(dataframe.test_type.unique())],
        key=f"type_{result.ticket_key}",
    )
    automated = columns[2].selectbox(
        "Automation", ["All", "Yes", "No", "Partial"], key=f"auto_{result.ticket_key}"
    )
    requirement = columns[3].selectbox(
        "Requirement",
        [
            "All",
            *sorted({value for item in cases for value in item["requirement_ids"]}),
        ],
        key=f"req_{result.ticket_key}",
    )
    filtered = dataframe.copy()
    if priority != "All":
        filtered = filtered[filtered.priority == priority]
    if test_type != "All":
        filtered = filtered[filtered.test_type == test_type]
    if automated != "All":
        filtered = filtered[filtered.automation_candidate == automated]
    if requirement != "All":
        filtered = filtered[filtered.requirement_ids.apply(lambda values: requirement in values)]
    if search:
        filtered = filtered[
            filtered.astype(str).apply(
                lambda row: row.str.contains(search, case=False).any(), axis=1
            )
        ]
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    tags = sorted({tag for item in cases for tag in item["tags"]})
    if tags:
        selected_tags = st.multiselect("Tags", tags, key=f"tags_{result.ticket_key}")
        if selected_tags:
            st.dataframe(
                filtered[
                    filtered.tags.apply(lambda values: any(tag in values for tag in selected_tags))
                ],
                use_container_width=True,
                hide_index=True,
            )


def _render_ticket_downloads(result: TicketResult) -> None:
    if not result.artifacts:
        return
    st.markdown("#### Downloads")
    columns = st.columns(4)
    for index, (name, path) in enumerate(result.artifacts.items()):
        file_path = Path(path)
        if not file_path.exists():
            continue
        columns[index % len(columns)].download_button(
            f"Download {name}",
            data=file_path.read_bytes(),
            file_name=file_path.name,
            key=f"download_{result.ticket_key}_{index}",
        )


def _render_zip_download(run, output_dir: Path) -> None:
    if st.button("Prepare run ZIP", key=f"prepare_zip_{run.run_id}"):
        try:
            st.session_state[f"zip_{run.run_id}"] = build_run_zip(output_dir, run.run_id)
        except OSError as error:
            st.error(f"Could not create ZIP: {error}")
    zip_bytes = st.session_state.get(f"zip_{run.run_id}")
    if zip_bytes:
        st.download_button(
            "Download all artifacts (.zip)",
            zip_bytes,
            f"{run.run_id}.zip",
            "application/zip",
        )


def _read_artifact(result: TicketResult, filename: str) -> str:
    path = result.artifacts.get(filename)
    return Path(path).read_text(encoding="utf-8") if path and Path(path).exists() else ""
