import csv
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:
    from fastmcp import FastMCP  # type: ignore
    from fastmcp.exceptions import ToolError  # type: ignore

# Configure logging exclusively to stderr so stdout is reserved for stdio JSON-RPC
logger = logging.getLogger("vwo-testcases")
logger.setLevel(logging.INFO)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(stderr_handler)

mcp = FastMCP("vwo-testcases")

# Dataset schema definition
DATASET_SCHEMA: Dict[str, str] = {
    "id": "int",
    "jira_id": "str",
    "priority": "str",
    "module": "str",
    "tags": "str",
    "title": "str",
    "steps": "str",
    "expected": "str",
}

# In-memory stores loaded once at startup
TEST_CASES_DATA: List[Dict[str, Any]] = []
ID_LOOKUP_MAP: Dict[str, Dict[str, Any]] = {}
MODULE_LOOKUP_MAP: Dict[str, List[Dict[str, Any]]] = {}


def _resolve_csv_path() -> Path:
    """Resolve the test cases CSV file path from environment or relative directories."""
    env_path = os.getenv("VWO_TEST_CASES_CSV")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p

    candidates = [
        Path(__file__).resolve().parent / "vwo_5000_test_cases.csv",
        Path(__file__).resolve().parent / "test_cases.csv",
        Path(__file__).resolve().parent / "resource" / "test_cases.csv",
        Path(__file__).resolve().parent.parent / "resource" / "test_cases.csv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Could not locate vwo_5000_test_cases.csv or test_cases.csv. "
        "Set VWO_TEST_CASES_CSV environment variable with the file path."
    )


def _load_dataset() -> None:
    """Load the CSV dataset into memory once at startup."""
    csv_path = _resolve_csv_path()
    logger.info("Loading dataset from %s", csv_path)

    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV file at {csv_path} is empty or missing headers.")

        for row in reader:
            raw_id = row.get("id", "").strip()
            parsed_id: Any = int(raw_id) if raw_id.isdigit() else raw_id
            record: Dict[str, Any] = {
                "id": parsed_id,
                "jira_id": row.get("jira_id", "").strip(),
                "priority": row.get("priority", "").strip(),
                "module": row.get("module", "").strip(),
                "tags": row.get("tags", "").strip(),
                "title": row.get("title", "").strip(),
                "steps": row.get("steps", "").strip(),
                "expected": row.get("expected", "").strip(),
            }
            TEST_CASES_DATA.append(record)

            # Build fast lookup indexes
            ID_LOOKUP_MAP[str(record["id"]).lower()] = record
            if record["jira_id"]:
                ID_LOOKUP_MAP[record["jira_id"].lower()] = record

            mod_key = record["module"].lower()
            if mod_key not in MODULE_LOOKUP_MAP:
                MODULE_LOOKUP_MAP[mod_key] = []
            MODULE_LOOKUP_MAP[mod_key].append(record)

    logger.info("Successfully loaded %d test cases across %d modules", len(TEST_CASES_DATA), len(MODULE_LOOKUP_MAP))


# Execute data loading on startup
_load_dataset()


# ============================================================================
# TOOLS (Model-invoked actions with parameters and dynamic execution)
# ============================================================================

@mcp.tool()
def search_test_cases(query: str, module: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search test cases by text query across all fields with optional module filtering."""
    if not query.strip():
        raise ToolError("Search query cannot be empty.")
    if limit < 1:
        raise ToolError("Limit must be a positive integer greater than 0.")

    q_lower = query.strip().lower()
    m_lower = module.strip().lower() if module else None

    # Validate module if provided
    if m_lower and m_lower not in MODULE_LOOKUP_MAP:
        available = ", ".join(sorted(k.title() for k in MODULE_LOOKUP_MAP.keys()))
        raise ToolError(f"Module '{module}' not found. Available modules: {available}")

    source_pool = MODULE_LOOKUP_MAP[m_lower] if m_lower else TEST_CASES_DATA
    results: List[Dict[str, Any]] = []

    for tc in source_pool:
        searchable_content = f"{tc['id']} {tc['jira_id']} {tc['title']} {tc['steps']} {tc['expected']} {tc['tags']}".lower()
        if q_lower in searchable_content:
            results.append(tc)
            if len(results) >= limit:
                break

    return results


@mcp.tool()
def get_test_case(test_id: str) -> Dict[str, Any]:
    """Retrieve a single test case by its numeric ID or JIRA ID."""
    key = str(test_id).strip().lower()
    if not key:
        raise ToolError("Parameter test_id cannot be empty.")

    case = ID_LOOKUP_MAP.get(key)
    if not case:
        raise ToolError(f"Test case '{test_id}' not found. Provide a valid numeric ID (e.g. 1) or JIRA ID (e.g. VWO-1001).")

    return case


@mcp.tool()
def test_case_stats(group_by: str = "module") -> Dict[str, int]:
    """Calculate test case distribution counts grouped by module, priority, or tags."""
    field = group_by.strip().lower()
    valid_fields = {"module", "priority", "tags", "jira_id"}

    if field not in valid_fields:
        raise ToolError(f"Invalid group_by field '{group_by}'. Supported fields: {', '.join(sorted(valid_fields))}")

    counts: Dict[str, int] = {}
    for tc in TEST_CASES_DATA:
        raw_val = tc.get(field, "")
        if field == "tags" and raw_val:
            # Handle comma-separated tags
            for tag in str(raw_val).split(","):
                clean_tag = tag.strip()
                if clean_tag:
                    counts[clean_tag] = counts.get(clean_tag, 0) + 1
        else:
            val = str(raw_val).strip() if raw_val else "Unspecified"
            counts[val] = counts.get(val, 0) + 1

    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


# ============================================================================
# RESOURCES (Application-controlled context, addressed by URI)
# ============================================================================

@mcp.resource("testcases://schema")
def get_dataset_schema() -> Dict[str, str]:
    """Return the schema definition with column names and inferred data types."""
    return DATASET_SCHEMA


@mcp.resource("testcases://all")
def get_all_test_cases() -> List[Dict[str, Any]]:
    """Return the entire dataset of test cases in JSON format."""
    return TEST_CASES_DATA


@mcp.resource("testcases://module/{name}")
def get_cases_by_module(name: str) -> List[Dict[str, Any]]:
    """Return all test cases belonging to a specified module name."""
    mod_key = name.strip().lower()
    if mod_key not in MODULE_LOOKUP_MAP:
        available = ", ".join(sorted(k.title() for k in MODULE_LOOKUP_MAP.keys()))
        raise ValueError(f"Module '{name}' not found. Available modules: {available}")
    return MODULE_LOOKUP_MAP[mod_key]


# ============================================================================
# PROMPTS (User-invoked templates for LLM workflows)
# ============================================================================

@mcp.prompt()
def review_test_case(test_id: str) -> str:
    """Generate a structured prompt asking the LLM to review and critique a test case."""
    key = str(test_id).strip().lower()
    case = ID_LOOKUP_MAP.get(key)
    if not case:
        return f"Error: Test case with ID '{test_id}' was not found in dataset."

    return f"""Please perform a thorough QA review of the following test case:

---
**ID**: {case.get('id')}
**JIRA ID**: {case.get('jira_id')}
**Module**: {case.get('module')}
**Priority**: {case.get('priority')}
**Tags**: {case.get('tags')}
**Title**: {case.get('title')}

**Execution Steps**:
{case.get('steps')}

**Expected Result**:
{case.get('expected')}
---

Provide a structured assessment covering:
1. **Clarity & Reproducibility**: Are the steps unambiguous, sequential, and reproducible?
2. **Assertion Quality**: Is the expected result deterministic and verifiable?
3. **Boundary & Edge Cases**: What edge cases or negative scenarios are missing?
4. **Actionable Suggestions**: Specific rewritten steps or assertions to improve coverage.
"""


@mcp.prompt()
def generate_regression_suite(module: str) -> str:
    """Generate a prompt to construct an end-to-end regression test suite for a module."""
    mod_key = module.strip().lower()
    cases = MODULE_LOOKUP_MAP.get(mod_key)
    if not cases:
        available = ", ".join(sorted(k.title() for k in MODULE_LOOKUP_MAP.keys()))
        return f"Error: Module '{module}' not found. Available modules: {available}"

    high_priority = [c for c in cases if str(c.get("priority", "")).lower() in ("critical", "high")]
    sample_cases = cases[:15]

    cases_summary = "\n".join(
        f"- [{c.get('jira_id', c.get('id'))}] ({c.get('priority')}) {c.get('title')} | Tags: {c.get('tags')}"
        for c in sample_cases
    )

    return f"""You are a QA Lead creating a comprehensive Regression Test Suite for the '{module}' module.

Dataset Summary for '{module}':
- Total Test Cases Available: {len(cases)}
- Critical / High Priority Cases: {len(high_priority)}

Sample Test Cases in this module:
{cases_summary}

Please generate a structured regression test plan:
1. **Execution Order & Dependencies**: Group tests by sub-feature and define prerequisite sequencing.
2. **Smoke vs Full Regression**: Specify which subset should run as P0 smoke blockers vs full regression.
3. **Risk-Based Prioritization**: Highlight critical risk paths and automated candidate recommendations.
4. **Gap Analysis**: Recommend any missing integration or edge test cases for '{module}'.
"""


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    mcp.run()
