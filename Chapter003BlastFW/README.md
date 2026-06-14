# AI Test Plan Generator (B.L.A.S.T Framework)

This project demonstrates a fully functional AI Test Plan Generator built following the **B.L.A.S.T framework** (Phase 0 to Phase 5). It fetches Jira issues (like `KAN-12`) and generates a comprehensive markdown test plan using Groq LLMs.

## Architecture (3-Layer Build)
- **Layer 1: Architecture** - Standard Operating Procedures (`architecture/`).
- **Layer 2: Navigation** - A lightweight FastAPI backend (`api/index.py` & `navigation/server.py`) that securely brokers requests without CORS issues.
- **Layer 3: Tools** - Atomic, deterministic Python scripts (`tools/`) for fetching Jira tickets and communicating with Groq.

## UI (Phase 4: Stylize)
A premium, dark-themed glassmorphism React application built with Vite.

## Live Deployment (Phase 5: Trigger)
Deployed to Vercel: [https://testplannerbuddy.vercel.app](https://testplannerbuddy.vercel.app)

## Local Development
1. Install dependencies: 
   ```bash
   npm install
   pip install -r requirements.txt
   ```
2. Set up your `.env` with `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN`, and `GROQ_KEY`.
3. Start backend: `python navigation/server.py`
4. Start frontend: `npm run dev`
