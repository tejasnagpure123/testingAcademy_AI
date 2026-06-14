# Project Constitution

## Data Schemas
**Input (Frontend to Backend)**
```json
{ "jiraId": "string (e.g., KAN-13)" }
```

**Output (Backend to Frontend)**
```json
{ "content": "string (Markdown)", "error": "string (optional)" }
```

## Behavioral Rules
- Do not invent features or stray from the PRD/Jira data.
- Adhere strictly to the `Test Strategy for Ecommerce Website.docx` template.
- Adhere strictly to the `RICE-POT-TestCase-Prompt.md` rules.

## Architectural Invariants
- 3-layer architecture: Architecture, Navigation, Tools.
- Next.js application will handle both UI and backend proxying to Jira/Groq.
