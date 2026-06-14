# AI QA Architect (Test Strategy & Test Case Builder)

A Next.js application that automatically generates comprehensive Test Strategies and Test Cases directly from Jira tickets using the Groq AI API (`llama-3.3-70b-versatile`).

## Features
- **Strategy Generation:** Maps Jira Issue context directly into a pre-defined enterprise Test Strategy `.docx` template format.
- **Test Case Creation:** Leverages the strict RICE-POT prompt methodology to generate traceable test cases based on the Jira descriptions.
- **Glassmorphism UI:** Built with Tailwind CSS v4, dark mode, and dynamic components.

## Setup
1. Clone the repository.
2. Add a `.env.local` file with the following:
   ```env
   GROQ_KEY=your_groq_key
   JIRA_EMAIL=your_email
   JIRA_TOKEN=your_jira_token
   JIRA_URL=https://your_jira.atlassian.net/
   ```
3. Run `npm install` and `npm run dev`.

## Deployment
Deployed on Vercel at [https://testnexus.vercel.app](https://testnexus.vercel.app).
