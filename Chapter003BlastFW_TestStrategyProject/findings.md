# Findings

## Research
- The `Test Strategy for Ecommerce Website.docx` provides a template that Groq will use to format its output.
- The `RICE-POT-TestCase-Prompt.md` provides strict rules and formatting instructions for Test Case generation.
- The `.env` file contains GROQ_KEY, JIRA_EMAIL, JIRA_TOKEN, and JIRA_URL.

## Discoveries
- Direct browser calls to Jira/Groq will fail due to CORS and will expose API keys.

## Constraints
- We must build a Next.js application to safely route API requests through a Node backend, solving CORS and security issues.
