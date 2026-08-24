# VWO Test Cases FastMCP Server

A production-grade Model Context Protocol (MCP) server built with **FastMCP** in Python that exposes **Tools**, **Resources**, and **Prompts** over a dataset of 5,000 manual QA test cases.

---

## 1. Architecture Overview

| MCP Primitive | Name / URI | Intent / Purpose |
| :--- | :--- | :--- |
| **Tool** | `search_test_cases` | Search cases across titles, steps, expected outcomes, tags, and IDs with module filter. |
| **Tool** | `get_test_case` | Fetch a single test case by numeric ID (e.g. `1`) or JIRA ID (e.g. `VWO-1001`). |
| **Tool** | `test_case_stats` | Return aggregate counts grouped by `module`, `priority`, or `tags`. |
| **Resource** | `testcases://schema` | Read-only dataset schema definition with data types. |
| **Resource** | `testcases://all` | Read-only full dataset of 5,000 test cases (JSON). |
| **Resource (Template)** | `testcases://module/{name}` | Dynamic URI returning all test cases for a specified module. |
| **Prompt** | `review_test_case` | Template prompting LLM to review test case clarity, assertions, and edge cases. |
| **Prompt** | `generate_regression_suite` | Template prompting LLM to construct a prioritized regression test suite for a module. |

---

## 2. Prerequisites & Installation

- **Python 3.11+**
- **uv** (fast Python package manager)

```bash
# Clone or navigate to the server folder
cd Chapter010MCP_Creation_VIBE/testcase-creator-mcp

# Sync environment dependencies using uv
uv sync
```

---

## 3. Running the Server

### Direct stdio execution
```bash
uv run python server.py
```

### Running with optional dataset path override
```bash
# Windows PowerShell
$env:VWO_TEST_CASES_CSV="d:\Study\TestingAcademy_AI_Blueprint\Chapter010MCP_Creation_VIBE\resource\test_cases.csv"
uv run python server.py

# macOS / Linux / Bash
export VWO_TEST_CASES_CSV="/path/to/vwo_5000_test_cases.csv"
uv run python server.py
```

---

## 4. Inspecting with MCP Inspector

Test and interact with all tools, resources, and prompts interactively:

```bash
npx @modelcontextprotocol/inspector uv --directory "d:/Study/TestingAcademy_AI_Blueprint/Chapter010MCP_Creation_VIBE/testcase-creator-mcp" run python server.py
```

Or using the FastMCP CLI:

```bash
uv run mcp dev server.py
```

---

## 5. Claude Desktop Integration

Add the server to your `claude_desktop_config.json`:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "vwo-testcases": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/Study/TestingAcademy_AI_Blueprint/Chapter010MCP_Creation_VIBE/testcase-creator-mcp",
        "run",
        "python",
        "server.py"
      ],
      "env": {
        "VWO_TEST_CASES_CSV": "d:/Study/TestingAcademy_AI_Blueprint/Chapter010MCP_Creation_VIBE/testcase-creator-mcp/vwo_5000_test_cases.csv"
      }
    }
  }
}
```

---

## 6. Verification

Run the test suite to verify all MCP primitives:

```bash
uv run python -c "from server import search_test_cases, get_test_case, test_case_stats; print('Search:', len(search_test_cases('checkout', limit=2))); print('Get:', get_test_case('1')['jira_id']); print('Stats:', test_case_stats('priority'))"
```