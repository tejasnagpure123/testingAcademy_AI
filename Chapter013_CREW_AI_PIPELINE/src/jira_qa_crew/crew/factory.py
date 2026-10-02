"""Create an isolated, sequential four-agent CrewAI workflow per Jira ticket."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from crewai import LLM, Agent, Crew, Process, Task

from jira_qa_crew.config import AppConfig
from jira_qa_crew.jira.gateway import JiraGateway
from jira_qa_crew.models import (
    JiraIssue,
    PlaywrightBundle,
    RequirementAnalysis,
    TestCaseSuite,
    TestPlan,
)
from jira_qa_crew.tools.jira_tool import FetchJiraIssueTool

PROMPT_DIR = Path(__file__).parents[1] / "prompts"
ProgressCallback = Callable[[str, str, str], None]


def load_prompts() -> tuple[dict[str, Any], dict[str, Any]]:
    with (PROMPT_DIR / "agents.yaml").open(encoding="utf-8") as file:
        agents = yaml.safe_load(file)
    with (PROMPT_DIR / "tasks.yaml").open(encoding="utf-8") as file:
        tasks = yaml.safe_load(file)
    return agents, tasks


def create_crew(
    config: AppConfig,
    gateway: JiraGateway,
    ticket_key: str,
    integration_mode: str,
    issue_json: str,
    cached_issue: JiraIssue,
    progress: ProgressCallback,
    repair_feedback: str = "",
) -> Crew:
    agent_prompts, task_prompts = load_prompts()
    llm = LLM(
        model=config.llm_model,
        api_key=config.llm_api_key,
        base_url=config.llm_base_url or None,
        temperature=config.llm_temperature,
    )
    jira_tool = FetchJiraIssueTool(
        gateway=gateway,
        expected_key=ticket_key,
        integration_mode=integration_mode,
        cached_issue=cached_issue,
    )

    def make_agent(key: str, tools: list[Any] | None = None) -> Agent:
        prompt = agent_prompts[key]

        def step_callback(_step: Any) -> None:
            progress(key, "RUNNING", "Agent is processing its assigned stage.")

        return Agent(
            role=prompt["role"],
            goal=prompt["goal"],
            backstory=prompt["backstory"],
            llm=llm,
            tools=tools or [],
            step_callback=step_callback,
            max_iter=8,
            max_execution_time=config.pipeline_ticket_timeout_seconds,
            allow_delegation=False,
            verbose=False,
        )

    analyst = make_agent("jira_analyst", [jira_tool])
    planner = make_agent("test_plan_writer")
    case_writer = make_agent("test_case_writer")
    coder = make_agent("playwright_coder")

    def make_task(
        key: str, agent: Agent, output_model: type, context: list[Task] | None = None
    ) -> Task:
        prompt = task_prompts[key]
        description = prompt["description"]
        description = description.replace("{{issue_json}}", issue_json)
        if repair_feedback:
            description += (
                "\n\nControlled repair attempt: Correct these deterministic validation "
                f"failures: {repair_feedback}"
            )

        def completed(_output: Any) -> None:
            progress(key, "COMPLETED", "Structured output created.")

        return Task(
            description=description,
            expected_output=prompt["expected_output"],
            agent=agent,
            context=context or [],
            output_pydantic=output_model,
            callback=completed,
        )

    analysis_task = make_task("jira_analysis", analyst, RequirementAnalysis)
    plan_task = make_task("test_plan", planner, TestPlan, [analysis_task])
    cases_task = make_task(
        "test_cases", case_writer, TestCaseSuite, [analysis_task, plan_task]
    )
    playwright_task = make_task(
        "playwright", coder, PlaywrightBundle, [analysis_task, plan_task, cases_task]
    )
    return Crew(
        agents=[analyst, planner, case_writer, coder],
        tasks=[analysis_task, plan_task, cases_task, playwright_task],
        process=Process.sequential,
        verbose=False,
    )
