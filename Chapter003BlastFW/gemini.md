# Project Constitution

## Data Schemas

### Input Payload
```json
{
  "jiraUrl": "string",
  "jiraEmail": "string",
  "jiraToken": "string",
  "issueId": "string (default: KAN-12)",
  "groqKey": "string"
}
```

### Output Payload
```json
{
  "status": "success | error",
  "issueData": {
    "summary": "string",
    "description": "string"
  },
  "testPlanMarkdown": "string"
}
```

## Behavioral Rules
- Generate the test plan using native AI knowledge.
- Must use GROQ for the LLM connection.
- The UI must be a lightweight React application prioritizing rich aesthetics.
- Must strictly follow the B.L.A.S.T. framework principles.

## Architectural Invariants
- 3-Layer Build Architecture (Architecture, Navigation, Tools).
- LLMs are probabilistic; business logic must be deterministic.
- If logic changes, update the SOP before updating the code.
- Deterministic scripts must go in `tools/` and be atomic/testable.
- Environment variables/tokens must be stored in `.env`.
- Use `.tmp/` for intermediate file operations.
