# AI QA Architect Project

This project implements the B.L.A.S.T Framework to create a Test Strategy and Test Case Generator from Jira tickets.

## Project Structure
- `test-strategy-app/`: The Next.js web application for the UI and backend logic.
- `B.L.A.S.T.md`: Instructions for the framework followed to build this app.
- `Objective.md`: The core mission of the project.
- `RICE-POT-TestCase-Prompt.md` & `Test Strategy for Ecommerce Website.docx`: The templates used by the AI to generate the output.
- `task_plan.md`, `gemini.md`, `findings.md`, `progress.md`: Project memory docs tracking the agentic implementation.

## Live Deployment
The application has been successfully deployed to Vercel and is available at:
**[https://testnexus.vercel.app](https://testnexus.vercel.app)**

## Local Development
Navigate to `test-strategy-app` and run `npm install` followed by `npm run dev`.
Make sure you provide the correct environment variables in `test-strategy-app/.env.local`.
