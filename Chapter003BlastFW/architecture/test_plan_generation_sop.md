# SOP: Test Plan Generation

## Goal
Generate a comprehensive Test Plan from a Jira ticket using Groq LLM.

## Inputs
- Jira URL
- Jira Email
- Jira Token
- Issue ID (e.g. KAN-12)
- Groq API Key

## Tool Logic
1. `navigation/server.py` receives inputs from React UI.
2. Calls `tools/jira_connection.py` to fetch issue details.
3. Calls `tools/test_plan_creator.py` with issue details to generate the test plan.
4. Returns the result to UI.

## Edge Cases
- Invalid credentials: Return HTTP 401/403.
- Jira issue not found: Return HTTP 404.
- Groq failure: Return HTTP 500.
