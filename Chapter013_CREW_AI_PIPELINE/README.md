# Jira QA Crew

Jira QA Crew is a Streamlit review tool that turns Jira issues into evidence-linked requirements, a 12-section test plan, detailed test cases, Playwright TypeScript scaffolds, traceability, and downloadable artifacts. Every ticket gets its own fresh CrewAI context. The application does not update Jira or execute generated Playwright tests.

## Architecture

```text
Streamlit input
  -> JiraGateway (MCP-first auto mode, REST fallback)
  -> Jira Analyst -> Test Plan Writer -> Test Case Writer -> Playwright Coder
  -> deterministic validators -> Markdown/CSV/JSON/TypeScript artifacts -> downloads
```

The provider decision is made in `JiraGateway`, not by an LLM. In auto mode a configured MCP issue-read tool is tried first; an unusable MCP response falls back to REST. REST-only and MCP-only modes never switch providers. The MCP client exposes only the configured read-only tool to the Jira analyst and restricts its key to the current ticket.

CrewAI 1.15.22 is pinned because this project uses its supported `Agent`, `Task(output_pydantic=...)`, sequential `Crew`, `MCPClient`, and HTTP/stdio transport APIs. Each stage returns a Pydantic model, then deterministic validation checks IDs, ticket ownership, required sections, and traceability. One controlled retry is allowed if structured output is malformed. Renderers, not raw LLM Markdown, produce downloadable artifacts.

## Agents

| Agent | Responsibility | Structured output |
|---|---|---|
| Jira Analyst | Extract facts, requirements, criteria, uncertainty, and issue metadata | `RequirementAnalysis` |
| Test Plan Writer | Produce exactly 12 ticket-specific sections with requirement references | `TestPlan` |
| Test Case Writer | Create detailed, prioritized, traceable cases | `TestCaseSuite` |
| Playwright Coder | Generate TypeScript for eligible cases; mark missing UI details | `PlaywrightBundle` |

Prompts live in `src/jira_qa_crew/prompts/`. Jira description text is treated as untrusted data and cannot authorize tools, secrets, commands, or access to another issue.

## Repository Structure

```text
app.py
src/jira_qa_crew/
  config.py, models.py, exceptions.py
  jira/       ADF parser, MCP/REST providers, deterministic gateway
  tools/      Jira read-only CrewAI tool
  crew/       Isolated four-agent factory
  prompts/    Agent and task YAML prompts
  services/   Ticket parsing, pipeline, validation, renderers, artifacts
  ui/         Streamlit components and ticket results
tests/        Offline unit and AppTest coverage
fixtures/     Explicit demo-only issue fixture
outputs/      Generated run directories (ignored by Git)
```

## Local Setup

Use Python 3.11 or newer. From this directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set secrets in `.env` or `.streamlit/secrets.toml` (copy `.streamlit/secrets.toml.example` to `secrets.toml`). Do not commit either file. `LLM_MODEL` must be a model identifier supported by CrewAI and the selected provider. `LLM_API_KEY` is required for live generation. Set optional `LLM_BASE_URL` for compatible gateways such as Groq; legacy `GROQ_MODEL`, `GROQ_API_KEY`, and `BASE_URL` names are also accepted. No credentials are requested in the UI.

### Jira REST

Set `JIRA_URL` to the Jira Cloud site root, for example `https://your-domain.atlassian.net`. With `JIRA_AUTH_MODE=basic`, set `JIRA_EMAIL` and `JIRA_API_TOKEN` (an Atlassian API token). With `JIRA_AUTH_MODE=bearer`, set `JIRA_BEARER_TOKEN`. Grant the service account only the Jira read permissions required for the target projects. Optional `JIRA_ACCEPTANCE_CRITERIA_FIELD` names the custom field containing acceptance criteria.

### Jira MCP

Set `JIRA_MCP_GET_ISSUE_TOOL` to the exact read-only issue retrieval tool name advertised by your MCP server, and configure its issue-key input name with `JIRA_MCP_ISSUE_ARGUMENT`. For streamable HTTP configure `JIRA_MCP_URL`; optional headers are a JSON object in `JIRA_MCP_HEADERS_JSON`. For stdio configure `JIRA_MCP_COMMAND` and JSON-array `JIRA_MCP_ARGS_JSON`. Review the server tool schema and ensure the named tool is read-only. Do not configure write-capable Jira tools. In `auto`, MCP is attempted first and REST is the deterministic fallback; configure at least one provider. Explicit MCP-only/REST-only modes do not fall back.

## Run

```powershell
streamlit run app.py
```

Enter one or more keys separated by spaces, commas, semicolons, or newlines. Select Auto, MCP only, or REST only and choose **Analyze & Generate QA Pack**. Results are isolated per ticket. The Run ZIP is assembled only when **Prepare run ZIP** is selected.

`DEMO_MODE=true` enables the explicitly labeled local fixture. Demo mode still runs real CrewAI agents and requires an LLM; it never silently replaces failed Jira data.

## Tests and Quality

```powershell
ruff check .
pytest -q
```

Tests mock Jira providers and CrewAI/LLM boundaries and do not contact a live Jira instance or paid model. The REST live check is skipped unless `RUN_LIVE_JIRA_TESTS=true` and `LIVE_JIRA_TEST_ISSUE_KEY` are set. Generated TypeScript is a scaffold; this Python service never executes it. A configuration-gated Playwright fixture can be collected without a browser or target URL:

```powershell
cd fixtures/playwright_project
npm install
npx playwright test --list
```

## Artifacts

Runs are stored under `outputs/<run_id>/`, with a summary and manifest plus per-ticket analysis JSON/Markdown, plan Markdown, test-case Markdown/CSV, traceability CSV, Playwright Markdown/spec files, and ticket manifest. Ticket and run path segments are sanitized. A run succeeds when at least one ticket completes; individual failures do not prevent later tickets from running.

## Deployment

### Streamlit Community Cloud

Deploy this folder as the app root with `app.py` as the entry point. Add required non-secret configuration and secrets in the deployment's Streamlit secrets manager. Configure outbound network access to Jira and the LLM provider. Streamlit Community Cloud storage may be ephemeral; download artifacts promptly or mount a durable store for production.

### Docker

```powershell
Copy-Item .env.example .env
# Configure .env, then:
docker compose up --build
```

Open `http://localhost:8501`. `outputs/` is mounted from the host directory.

## Troubleshooting and Security

| Symptom | Check |
|---|---|
| Jira 401/403 | API token/auth mode and project read permissions |
| Jira 404 | Site URL, issue key, Browse permission, issue security |
| MCP tool not advertised | Exact configured tool name and server read-only tool schema |
| Auto mode reports no provider | Configure REST credentials or MCP server/tool settings |
| LLM configuration error | `LLM_MODEL` and `LLM_API_KEY` |
| Playwright `NEEDS_CONFIGURATION` | Confirm base URL, selectors, endpoints, test data, and credentials with the application team before enabling tests |

Secrets are loaded from environment variables or Streamlit secrets, never ordinary UI fields. Errors and activity logs avoid printing secret values. Jira access is read-only. Ticket text is not executed, shell commands are not spawned, no dynamic evaluation or unsafe deserialization is used, and generated Playwright is not run by the server.

## Limitations

MCP tool input/output formats vary; configure the tool name and key-argument name to match the installed server. MCP responses must contain structured JSON issue data or auto mode falls back to REST. Acceptance criteria extraction from REST custom fields requires field configuration. Generated requirements and tests require human review; missing selectors/endpoints result in a non-ready scaffold. The app does not persist Streamlit session state across server restarts.