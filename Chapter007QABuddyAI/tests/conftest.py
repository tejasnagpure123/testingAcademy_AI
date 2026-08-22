"""
QABuddy.ai — Pytest Configuration & Shared Fixtures
Provides lightweight fixtures so unit tests run without heavy ML dependencies.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

import pytest

# Ensure the project root is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ─── Environment Stubs ──────────────────────────────────────
# Set minimal env vars so settings loads without requiring a real .env
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("GEMINI_API_KEY", "test-key-stub")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("QDRANT_PORT", "6333")
os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-m3")
os.environ.setdefault("APP_PASSWORD", "qabuddy2026")


# ─── Mock Fixtures ──────────────────────────────────────────

@pytest.fixture
def sample_search_results() -> List[Dict[str, Any]]:
    """Minimal search result list for testing prompt templates and QA chain."""
    return [
        {
            "id": "uuid-001",
            "score": 0.92,
            "text": "public void testValidLogin() { driver.findElement(By.id('username')); }",
            "metadata": {
                "source_type": "selenium_repo",
                "source_file": "LoginTest.java",
                "title": "testValidLogin (method)",
                "language": "java",
                "unit_type": "method",
                "unit_name": "testValidLogin",
            },
        },
        {
            "id": "uuid-002",
            "score": 0.87,
            "text": "TC-001 | Login with valid credentials | Steps: Navigate to /login, Enter admin/pass123, Click Submit | Expected: Dashboard shown | Status: Pass",
            "metadata": {
                "source_type": "test_cases",
                "source_file": "testdata.csv",
                "title": "Test Case TC-001",
                "language": "csv",
                "unit_type": "test_case",
                "unit_name": "TC-001",
            },
        },
        {
            "id": "uuid-003",
            "score": 0.81,
            "text": "QA-456: Login button broken on Chrome 120\nStatus: Open\nPriority: High\nDescription: The login button fails intermittently on Chrome 120.",
            "metadata": {
                "source_type": "jira_tickets",
                "source_file": "QA-456",
                "title": "QA-456: Login button broken on Chrome 120",
                "language": "jira",
                "unit_type": "ticket",
                "ticket_key": "QA-456",
            },
        },
    ]


@pytest.fixture
def mock_vector_store():
    """Mock QdrantVectorStore that doesn't require a running Qdrant instance."""
    vs = MagicMock()
    vs.get_collection_info.return_value = {
        "name": "qabuddy",
        "points_count": 5000,
        "vectors_count": 5000,
        "status": "green",
    }
    vs.hybrid_search.return_value = []
    vs.search_dense.return_value = []
    vs.upsert_chunks.return_value = 10
    return vs


@pytest.fixture
def mock_searcher(mock_vector_store, sample_search_results):
    """Mock HybridSearcher that returns sample results."""
    from unittest.mock import MagicMock
    searcher = MagicMock()
    searcher.search.return_value = sample_search_results
    return searcher


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient that returns a canned answer without calling any API."""
    llm = MagicMock()
    llm.generate.return_value = (
        "The `testValidLogin` method in `LoginTest.java` performs a login check by "
        "locating the username field via `By.id('username')`. [Source: LoginTest.java]\n\n"
        "### Sources\n- LoginTest.java (selenium_repo)\n- TC-001 (test_cases)\n- QA-456 (jira_tickets)"
    )
    return llm


@pytest.fixture
def tmp_csv_file(tmp_path):
    """Create a temporary test case CSV file for parser tests."""
    csv_content = (
        "test_id,title,steps,expected_result,status\n"
        "TC-001,Login with valid credentials,"
        "Navigate to /login; Enter admin/pass123; Click Submit,"
        "Dashboard is displayed,Pass\n"
        "TC-002,Login with invalid credentials,"
        "Navigate to /login; Enter wrong/wrong; Click Submit,"
        "Error message is shown,Pass\n"
        "TC-003,Forgot password flow,"
        "Click Forgot Password; Enter email; Submit,"
        "Reset email is sent,Pass\n"
    )
    csv_file = tmp_path / "testdata.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    return str(csv_file)


@pytest.fixture
def tmp_markdown_file(tmp_path):
    """Create a temporary markdown document for text parser tests."""
    md_content = """# QA Framework Guide

## Introduction
This guide covers the basics of our QA automation framework built on Selenium.

## Page Object Model
The Page Object Model (POM) pattern separates test logic from UI interactions.
Each page gets its own class with element locators and action methods.

### BasePage
The `BasePage` class provides common methods shared across all page objects:
- `find_element(locator)` — waits for element visibility
- `click(locator)` — click with retry logic
- `type_text(locator, text)` — clear and type text

## Test Execution
Run all tests with: `mvn test -Dsurefire.failIfNoSpecifiedTests=false`

## Reporting
Test results are published to Jenkins and available at `/build/reports/`.
"""
    md_file = tmp_path / "qa_guide.md"
    md_file.write_text(md_content, encoding="utf-8")
    return str(md_file)


@pytest.fixture
def tmp_log_file(tmp_path):
    """Create a temporary Jenkins log file for log parser tests."""
    log_content = """Started by user jenkins-bot
Running on agent-linux-01
=============================================================
[INFO] Building QA Automation Suite 2.1.0-SNAPSHOT
[INFO] Compiling test sources...
=============================================================
Tests run: 142, Failures: 3, Errors: 1, Skipped: 5
=============================================================
FAILED TESTS:
  LoginTest.testValidLogin - java.lang.AssertionError: expected [Dashboard] but found [Error]
    at LoginTest.testValidLogin(LoginTest.java:54)
    at sun.reflect.NativeMethodAccessorImpl.invoke(Unknown Source)
  CheckoutTest.testPaymentFlow - java.lang.TimeoutException: Timed out after 30s
    at CheckoutTest.testPaymentFlow(CheckoutTest.java:88)
=============================================================
BUILD FAILURE
Total time: 4 min 12 s
Finished: FAILURE
"""
    log_file = tmp_path / "build_142.log"
    log_file.write_text(log_content, encoding="utf-8")
    return str(log_file)


@pytest.fixture
def tmp_transcript_file(tmp_path):
    """Create a temporary meeting transcript for transcript parser tests."""
    transcript_content = """Alice: Good morning! Let's talk about the flaky login test.
Bob: I saw it fail 3 times in the last 10 runs on Jenkins build 142.
Alice: What's the root cause? Is it timing?
Bob: Yes, it's a race condition. The submit button is clicked before the form validation JS runs.
Alice: We should add an explicit wait for the form to be ready.
Bob: I'll add `ExpectedConditions.elementToBeClickable` with a 10-second timeout.
Alice: Perfect. Also, can we add it to the smoke test suite once it's stable?
Bob: Absolutely. I'll create JIRA ticket QA-789 to track this.
"""
    transcript_file = tmp_path / "sprint_sync_2026_08.txt"
    transcript_file.write_text(transcript_content, encoding="utf-8")
    return str(transcript_file)
