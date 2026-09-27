"""
CrewAI + Jira MCP: Auto-Generate Test Plans, Test Cases & Playwright Scripts
─────────────────────────────────────────────────────────────────────────────
Input  : A Jira ticket ID (e.g., https://tta-jira.atlassian.net/browse/KAN-12)
Output : test_plan.md, test_cases.md, playwright_tests.md

Pipeline:
  1. Jira Analyst       → fetches ticket via MCP - fallback to API, extracts requirements
  2. Test Plan Writer   → writes complete test plan (12 sections)
  3. Test Case Writer   → writes detailed test cases table
  4. Playwright Coder   → generates automation scripts"""
