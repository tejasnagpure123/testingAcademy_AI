"""
QABuddy.ai — Parser Unit Tests
Tests for all source-specific parsers.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.parsers.code_parser import parse_code_repository, _parse_java, _parse_js_ts, _parse_python
from src.ingestion.parsers.csv_parser import parse_test_cases, _resolve_columns
from src.ingestion.parsers.text_parser import parse_text_file, _parse_markdown
from src.ingestion.parsers.transcript_parser import parse_transcript, _is_speaker_labeled
from src.ingestion.parsers.log_parser import parse_log_file, _classify_block


# ─── Code Parser Tests ──────────────────────────────────────

class TestCodeParser:
    """Tests for the AST-aware code parser."""

    def test_parse_java_method(self):
        java_code = '''
public class LoginTest {

    /**
     * Test valid login
     */
    public void testValidLogin() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("admin");
        driver.findElement(By.id("password")).sendKeys("pass123");
        driver.findElement(By.id("submit")).click();
        Assert.assertTrue(driver.getTitle().contains("Dashboard"));
    }

    public void testInvalidLogin() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("wrong");
        Assert.assertTrue(driver.getPageSource().contains("Invalid"));
    }
}
'''
        units = _parse_java(java_code, "LoginTest.java", "selenium_repo")
        assert len(units) >= 2
        assert any(u.unit_name == "testValidLogin" for u in units)
        assert any(u.unit_name == "testInvalidLogin" for u in units)
        assert all(u.language == "java" for u in units)

    def test_parse_js_function(self):
        js_code = '''
const { test, expect } = require('@playwright/test');

async function loginUser(page, username, password) {
    await page.goto('/login');
    await page.fill('#username', username);
    await page.fill('#password', password);
    await page.click('#submit');
}

test('should login successfully', async ({ page }) => {
    await loginUser(page, 'admin', 'pass123');
    await expect(page).toHaveTitle(/Dashboard/);
});
'''
        units = _parse_js_ts(js_code, "login.spec.js", "javascript", "playwright_repo")
        assert len(units) >= 1
        assert any(u.unit_name == "loginUser" for u in units)

    def test_parse_python_class(self):
        py_code = '''
class TestLogin:
    def setup_method(self):
        self.driver = webdriver.Chrome()

    def test_valid_login(self):
        self.driver.get("https://example.com")
        assert "Dashboard" in self.driver.title

    def teardown_method(self):
        self.driver.quit()
'''
        units = _parse_python(py_code, "test_login.py", "selenium_repo")
        assert len(units) >= 1
        assert any(u.unit_name == "TestLogin" for u in units)

    def test_parse_empty_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            units = parse_code_repository(tmpdir, "test")
            assert units == []

    def test_parse_nonexistent_repo(self):
        units = parse_code_repository("/nonexistent/path", "test")
        assert units == []


# ─── CSV Parser Tests ───────────────────────────────────────

class TestCsvParser:
    """Tests for the test case CSV/XLSX parser."""

    def test_resolve_columns(self):
        columns = ["test_id", "title", "steps", "expected_result", "status"]
        col_map = _resolve_columns(columns)
        assert col_map["test_id"] == "test_id"
        assert col_map["title"] == "title"
        assert col_map["steps"] == "steps"
        assert col_map["expected_result"] == "expected_result"
        assert col_map["status"] == "status"

    def test_resolve_columns_aliases(self):
        columns = ["tc_id", "test_case_name", "test_steps", "expected"]
        col_map = _resolve_columns(columns)
        assert col_map["test_id"] == "tc_id"
        assert col_map["title"] == "test_case_name"
        assert col_map["steps"] == "test_steps"
        assert col_map["expected_result"] == "expected"

    def test_parse_csv_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("test_id,title,steps,expected_result,status\n")
            f.write("TC-001,Login test,Open login page and enter credentials,User is logged in,Pass\n")
            f.write("TC-002,Logout test,Click logout button,User is logged out,Pass\n")
            f.name

        try:
            cases = parse_test_cases(f.name, "test_cases")
            assert len(cases) == 2
            assert cases[0].test_id == "TC-001"
            assert "Login test" in cases[0].content
            assert cases[1].test_id == "TC-002"
        finally:
            os.unlink(f.name)

    def test_parse_nonexistent_csv(self):
        cases = parse_test_cases("/nonexistent/file.csv", "test_cases")
        assert cases == []


# ─── Text Parser Tests ──────────────────────────────────────

class TestTextParser:
    """Tests for the text/markdown parser."""

    def test_parse_markdown_with_headings(self):
        md_content = """# Introduction
This is the intro section.

## Features
- Feature 1
- Feature 2

## Installation
Run pip install qabuddy.

### Requirements
Python 3.11+
"""
        sections = _parse_markdown(md_content, "test.md", "company_docs")
        assert len(sections) >= 3
        assert any("Introduction" in s.section_title for s in sections)
        assert any("Features" in s.section_title for s in sections)

    def test_parse_markdown_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("# Test Document\nThis is a test document with content.\n\n## Section 2\nMore content here.\n")
            fname = f.name

        try:
            sections = parse_text_file(fname, "company_docs")
            assert len(sections) >= 1
        finally:
            os.unlink(fname)

    def test_parse_nonexistent_file(self):
        sections = parse_text_file("/nonexistent/file.md", "company_docs")
        assert sections == []


# ─── Transcript Parser Tests ────────────────────────────────

class TestTranscriptParser:
    """Tests for the meeting transcript parser."""

    def test_detect_speaker_labeled(self):
        content = """Alice: Let's discuss the test plan.
Bob: I think we should add more smoke tests.
Alice: Agreed. What about the login flow?
Bob: We already have coverage there.
"""
        assert _is_speaker_labeled(content) is True

    def test_detect_non_speaker_text(self):
        content = """This is just a regular paragraph.
It doesn't have any speaker labels.
Just normal text content.
"""
        assert _is_speaker_labeled(content) is False

    def test_parse_speaker_transcript(self):
        content = """Alice: We need to fix the flaky login test.
Bob: I saw the Jenkins log, it's a timing issue.
Alice: Can you add an explicit wait there?
Bob: Sure, I'll push a fix today.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            fname = f.name

        try:
            segments = parse_transcript(fname, "meeting_transcripts")
            assert len(segments) >= 1
            assert any("Alice" in s.speaker or "Bob" in s.speaker for s in segments)
        finally:
            os.unlink(fname)


# ─── Log Parser Tests ───────────────────────────────────────

class TestLogParser:
    """Tests for the Jenkins log parser."""

    def test_classify_error_block(self):
        content = """java.lang.AssertionError: Expected true but got false
    at LoginTest.testValidLogin(LoginTest.java:42)
    at sun.reflect.NativeMethodAccessorImpl.invoke(...)
"""
        assert _classify_block(content) == "stack_trace"

    def test_classify_test_result(self):
        content = "Tests run: 42, Failures: 2, Errors: 0, Skipped: 3"
        assert _classify_block(content) == "test_result"

    def test_classify_build_info(self):
        content = "Started by user admin\nBuild #142 on agent-01"
        assert _classify_block(content) == "build_info"

    def test_parse_log_file(self):
        log_content = """Started by user admin
Running on agent-01
===========================
[INFO] Building project...
[INFO] Compiling sources
===========================
Tests run: 10, Failures: 1, Errors: 0
===========================
FAILED TESTS
LoginTest.testTimeout - java.lang.TimeoutException
    at org.openqa.selenium.support.ui.Wait(Wait.java:88)
===========================
BUILD FAILURE
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write(log_content)
            fname = f.name

        try:
            blocks = parse_log_file(fname, "jenkins_logs")
            assert len(blocks) >= 2
            assert any(b.block_type == "build_info" for b in blocks)
        finally:
            os.unlink(fname)
