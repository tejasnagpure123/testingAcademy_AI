from crewai import Agent, Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv
import argparse
import os
from pathlib import Path
import requests

load_dotenv(Path(__file__).with_name(".env"))

model_name = os.getenv("GROQ_MODEL", "").strip()
api_key = os.getenv("GROQ_API_KEY")
base_url = os.getenv("BASE_URL")

missing_settings = [
    name
    for name, value in (
        ("GROQ_MODEL", model_name),
        ("GROQ_API_KEY", api_key),
        ("BASE_URL", base_url),
    )
    if not value
]
if missing_settings:
    raise RuntimeError(
        f"Missing required settings in .env: {', '.join(missing_settings)}"
    )

model_name = model_name.strip()
if model_name.lower().startswith("openai/openai/"):
    pass
elif model_name.lower().startswith("openai/"):
    model_name = f"openai/{model_name}"
else:
    model_name = f"openai/openai/{model_name}"

groq_llm = LLM(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)


"""QA bug-triage crew: classify impact, investigate causes, and plan tests."""


def _adf_to_text(node):
    if isinstance(node, list):
        return "".join(_adf_to_text(child) for child in node)
    if not isinstance(node, dict):
        return ""

    if node.get("type") == "text":
        return node.get("text", "")
    if node.get("type") == "hardBreak":
        return "\n"

    text = _adf_to_text(node.get("content", []))
    if node.get("type") in {"paragraph", "heading", "listItem"} and text:
        return text + "\n"
    return text


def fetch_jira_ticket(issue_key):
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_TOKEN")
    jira_url = (
        os.getenv("JIRA_URL", "https://tta-jira.atlassian.net").strip().rstrip("/")
    )
    if jira_url.endswith("/browse"):
        jira_url = jira_url[:-7]
    if not jira_email or not jira_token:
        raise RuntimeError("JIRA_EMAIL and JIRA_TOKEN must be configured in .env")
    if not jira_url.startswith(("https://", "http://")):
        raise RuntimeError(
            "JIRA_URL must be a Jira site URL, such as https://example.atlassian.net"
        )

    try:
        response = requests.get(
            f"{jira_url}/rest/api/3/issue/{issue_key}",
            auth=(jira_email, jira_token),
            headers={"Accept": "application/json"},
            params={
                "fields": "summary,description,reporter,status,priority,issuetype,labels,components"
            },
            timeout=30,
        )
    except requests.Timeout as error:
        raise RuntimeError(
            "Timed out connecting to Jira. Check network access and JIRA_URL."
        ) from error
    except requests.ConnectionError as error:
        raise RuntimeError(
            "Could not connect to Jira. Check network access and JIRA_URL."
        ) from error

    if response.status_code in {401, 403}:
        raise RuntimeError(
            f"Jira returned HTTP {response.status_code}. Verify JIRA_EMAIL, JIRA_TOKEN, "
            "and the account's Jira permissions."
        )
    if response.status_code == 404:
        raise RuntimeError(
            f"Jira could not find {issue_key} on {jira_url}, or the configured account cannot view it. "
            "Verify the issue key, Jira site URL, project Browse permission, and any issue security settings."
        )
    response.raise_for_status()
    issue = response.json()
    fields = issue["fields"]
    description = _adf_to_text(fields.get("description")) or "No description provided."
    reporter = (fields.get("reporter") or {}).get("displayName", "Unknown")
    status = (fields.get("status") or {}).get("name", "Unknown")
    priority = (fields.get("priority") or {}).get("name", "Unspecified")
    issue_type = (fields.get("issuetype") or {}).get("name", "Unknown")
    components = (
        ", ".join(component["name"] for component in fields.get("components", []))
        or "Unspecified"
    )

    return f"""Issue: {issue['key']} ({issue_type})
Summary: {fields.get('summary', 'No summary')}
Status: {status}
Reported priority: {priority}
Reporter: {reporter}
Components: {components}

Description:
{description.strip()}"""


bug_Analyst = Agent(
    role="QA Defect Triage Analyst",
    goal=(
        "Own the defect classification decision: assess user impact, severity, "
        "priority, and category from the report without proposing root causes or tests."
    ),
    backstory=(
        "You specialize in evidence-based QA intake. You distinguish severity from "
        "priority, treat reporter assessments as inputs rather than facts, and do "
        "not invent affected-user counts, business losses, or system behavior. "
        "You explicitly mark unknowns and explain which missing facts could change "
        "the classification."
    ),
    llm=groq_llm,
    verbose=True,
    allow_delegation=False,
)

root_cause_agent = Agent(
    role="Software Root-Cause Investigator",
    goal=(
        "Investigate causal explanations for the defect. Separate observed facts "
        "from ranked hypotheses and give concrete checks that can confirm or reject them."
    ),
    backstory=(
        "You investigate software failures across browser, API, service, data, "
        "configuration, and deployment layers. A symptom or release correlation "
        "is not proof. You never label a cause confirmed without supporting runtime "
        "or code evidence, and recommend the highest-value first diagnostic check."
    ),
    llm=groq_llm,
    verbose=True,
    allow_delegation=False,
)

test_recommender = Agent(
    role="QA Test Design Engineer",
    goal=(
        "Turn the defect and investigation findings into executable verification, "
        "regression, and edge-case tests; do not reclassify severity or speculate on cause."
    ),
    backstory=(
        "You are a senior SDET who produces precise, observable test cases. "
        "For web defects you use Playwright with TypeScript, assert user-visible "
        "behavior and relevant network side effects, and avoid brittle selectors "
        "or invented application endpoints."
    ),
    llm=groq_llm,
    verbose=True,
    allow_delegation=False,
)

triage_task = Task(
    description="""Triage the Jira bug report using only the supplied evidence.

{bug_report}

Return these sections:
1. Severity (P0-P4) and evidence-based rationale
2. Defect category and affected component (mark unknown if not provided)
3. User/business impact, separating known impact from unverified assumptions
4. Recommended response priority and why; do not treat Jira's current priority as proof
5. Key unknowns that could change the assessment

Do not diagnose root cause or write test cases; those belong to the other specialists.""",
    expected_output="A structured triage report with justified severity, category, impact, priority, and explicit unknowns.",
    agent=bug_Analyst,
)


root_cause_task = Task(
    description="""Investigate plausible causes using the Jira report and triage output.

{bug_report}

Return:
1. Observed facts from the report
2. Up to three ranked root-cause hypotheses, each labeled unconfirmed and tied to supporting/missing evidence
3. Likely system layer(s), with confidence
4. Minimal steps and first logs/telemetry to inspect to confirm or reject each hypothesis

Do not present a hypothesis as a confirmed root cause and do not repeat the severity assessment.""",
    expected_output="A fact-versus-hypothesis RCA with ranked causes, confidence, and discriminating investigation steps.",
    agent=root_cause_agent,
    context=[triage_task],
)

test_task = Task(
    description="""Design tests from the Jira report, triage, and RCA outputs.

{bug_report}
Return:
1. One focused fix-verification scenario with setup, action, and assertions
2. Three to five regression cases, each with expected behavior
3. Relevant boundary/negative cases
4. A concise Playwright TypeScript example using resilient selectors; identify selectors/endpoints that need confirmation instead of inventing them
5. State whether load/performance testing is justified by the evidence

Use only evidence in the Jira report and prior task outputs. Do not invent measurements, API timings, endpoints, selectors, or application behavior; mark them as unknown and needing confirmation. In any Playwright example that waits for a response caused by an action, establish the response wait before triggering the action.

Keep this a test-design report: do not repeat triage or claim the suspected cause is proven.""",
    expected_output="An actionable test plan with verification, regression and edge cases, plus a Playwright TypeScript approach.",
    agent=test_recommender,
    context=[triage_task, root_cause_task],
)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch a Jira issue and run the three-agent QA bug triage crew."
    )
    parser.add_argument("issue_key", help="Jira issue key, for example KAN-16")
    arguments = parser.parse_args()
    issue_key = arguments.issue_key

    bug_report = fetch_jira_ticket(issue_key)
    crew = Crew(
        agents=[bug_Analyst, root_cause_agent, test_recommender],
        tasks=[triage_task, root_cause_task, test_task],
        process=Process.sequential,
        verbose=True,
    )

    print(f"Fetched Jira issue {issue_key}:\n{bug_report}")
    print("\nStarting three-agent QA bug triage")
    result = crew.kickoff(inputs={"bug_report": bug_report})

    report_headings = [
        "Agent 1: QA Defect Triage Analyst",
        "Agent 2: Software Root-Cause Investigator",
        "Agent 3: QA Test Design Engineer",
    ]
    for index, heading in enumerate(report_headings):
        task_output = result.tasks_output[index]
        report_text = getattr(task_output, "raw", str(task_output))
        print(f"\n{'=' * 72}\n{heading}\n{'=' * 72}\n{report_text}")


if __name__ == "__main__":
    main()
