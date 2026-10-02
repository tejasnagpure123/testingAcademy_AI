"""Safe per-run artifact persistence and on-demand ZIP generation."""

from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from jira_qa_crew.models import TicketResult
from jira_qa_crew.services.renderers import (
    playwright_markdown,
    requirements_markdown,
    test_cases_csv,
    test_cases_markdown,
    test_plan_markdown,
    ticket_manifest,
    traceability_csv,
)


def _safe_segment(value: str) -> str:
    if "/" in value or "\\" in value or value in {".", ".."}:
        raise ValueError("Unsafe artifact path segment.")
    segment = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    if segment in {"", ".", ".."}:
        raise ValueError("Unsafe artifact path segment.")
    return segment


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return str(path)


def write_ticket_artifacts(run_id: str, ticket: TicketResult, output_dir: Path) -> dict[str, str]:
    run_path = output_dir / _safe_segment(run_id)
    ticket_path = run_path / _safe_segment(ticket.ticket_key)
    artifacts: dict[str, str] = {}
    if ticket.analysis:
        artifacts["requirements_analysis.md"] = _write(
            ticket_path / "requirements_analysis.md",
            requirements_markdown(ticket.analysis),
        )
        artifacts["requirements_analysis.json"] = _write(
            ticket_path / "requirements_analysis.json",
            ticket.analysis.model_dump_json(indent=2),
        )
    if ticket.plan:
        artifacts["test_plan.md"] = _write(
            ticket_path / "test_plan.md", test_plan_markdown(ticket.plan)
        )
    if ticket.suite:
        artifacts["test_cases.md"] = _write(
            ticket_path / "test_cases.md", test_cases_markdown(ticket.suite)
        )
        artifacts["test_cases.csv"] = _write(
            ticket_path / "test_cases.csv", test_cases_csv(ticket.suite)
        )
    if ticket.analysis and ticket.suite:
        artifacts["traceability_matrix.csv"] = _write(
            ticket_path / "traceability_matrix.csv",
            traceability_csv(ticket.analysis, ticket.suite),
        )
    if ticket.playwright:
        artifacts["playwright_tests.md"] = _write(
            ticket_path / "playwright_tests.md", playwright_markdown(ticket)
        )
        for generated in ticket.playwright.files:
            relative = PurePosixPath(generated.path)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(
                    "Generated Playwright paths may not escape the ticket artifact folder."
                )
            parts = [_safe_segment(part) for part in relative.parts]
            if not parts or not parts[-1].endswith(".ts"):
                raise ValueError("Generated Playwright files must use a .ts path.")
            artifacts[f"playwright/{'/'.join(parts)}"] = _write(
                ticket_path.joinpath("playwright", *parts), generated.content
            )
    manifest = ticket_manifest(ticket, sorted(artifacts))
    artifacts["manifest.json"] = _write(
        ticket_path / "manifest.json",
        json.dumps(manifest, indent=2, ensure_ascii=False),
    )
    return artifacts


def write_run_artifacts(run, output_dir: Path) -> None:
    run_path = output_dir / _safe_segment(run.run_id)
    run_path.mkdir(parents=True, exist_ok=True)
    counts = {
        status: sum(result.status == status for result in run.results)
        for status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED")
    }
    lines = [
        f"# Jira QA Crew Run {run.run_id}",
        "",
        f"- Started: {run.started_at}",
        f"- Completed: {run.completed_at}",
        f"- Tickets: {len(run.results)}",
        f"- Completed: {counts['COMPLETED']}",
        f"- Completed with warnings: {counts['COMPLETED_WITH_WARNINGS']}",
        f"- Failed: {counts['FAILED']}",
        "",
        "| Ticket | Status | Source | Automation | Error |",
        "|---|---|---|---|---|",
    ]
    for result in run.results:
        readiness = result.playwright.readiness if result.playwright else "Not generated"
        error = (result.error or "").replace("|", "\\|")
        lines.append(
            f"| {result.ticket_key} | {result.status} | {result.source} | {readiness} | {error} |"
        )
    (run_path / "run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "run_id": run.run_id,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "counts": counts,
        "tickets": [ticket_manifest(result, sorted(result.artifacts)) for result in run.results],
        "artifact_index": [
            str(Path(path).relative_to(output_dir))
            for result in run.results
            for path in result.artifacts.values()
            if Path(path).exists()
        ],
    }
    (run_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def build_run_zip(output_dir: Path, run_id: str) -> bytes:
    run_path = output_dir / _safe_segment(run_id)
    if not run_path.is_dir():
        raise FileNotFoundError("Run artifacts do not exist.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in run_path.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(run_path.parent))
    return buffer.getvalue()
