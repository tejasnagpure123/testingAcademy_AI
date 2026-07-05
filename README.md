# AI Tester Blueprint 3.x

A practical, project-driven curriculum for QA engineers learning to use LLMs as a real testing tool — not a toy.
Each chapter pairs concept material with a hands-on project, a prompt template, and runnable code where applicable.

- **Author:** Pramod Dutta — Principal SDET
- **Website:** [The Testing Academy](https://thetestingacademy.com/)
- **LinkedIn:** [linkedin.com/in/pramoddutta](https://www.linkedin.com/in/pramoddutta/)

---

## Repository Layout

```
.
├── chapter_01_LLM_Basics/         How transformers and attention work
│   ├── attention_interactive.html
│   ├── attention_is_all_you_need.html
│   └── Notes.md
│
└── chapter_02_Prompt_Eng/         Prompt engineering for QA work
    ├── Anti_Hallucinations_Rules.md
    ├── Project1_TC_Gen/           Test case generation from a PRD/API doc
    │   ├── RICE-POT-TestCase-Prompt.md
    │   ├── RICE_POT_FRAMEWORK/
    │   ├── Restful-booker.pdf
    │   ├── Restful_Booker_API_Test_Cases.md
    │   └── output/
    ├── Project2_Selenium_Framework/   POM-based Selenium framework built from a prompt
    │   ├── Problem.md
    │   ├── SKILL.md                   RICE-POT prompt-builder skill
    │   ├── blank-template-rice-pot.md
    │   └── AdvanceSeleniumFramework/  Maven + TestNG + Selenium 4
    └── templates/                 Reusable prompt templates (RTCFR / RICE-POT)
        ├── 01_TestCaseGeneration_Prompt.md
        ├── 02_TestCases_from_prd
        ├── 03_API_Test_Generation.md
        ├── 04_Negative_TC_Only.md
        ├── 05_Secuirty_Test.md
        └── 06_Regression_Suite.md
```

---

## Chapter 01 — LLM Basics

Foundational material on how Large Language Models read text and decide what to output. The key idea: a model is not a database lookup — it weighs every token against every other token (attention) and predicts the next one.

**What's here:**
- `attention_is_all_you_need.html` — interactive walkthrough of the original Transformer paper concepts.
- `attention_interactive.html` — visualises self-attention so you can see why prompt phrasing changes outputs.
- `Notes.md` — short recap notes.

**Why a QA engineer should care:** the model's behaviour is deterministic-ish on a per-token level, but every word you add to a prompt shifts the attention weights. That is why structured prompt frameworks (next chapter) outperform free-form questions.

Open the HTML files locally in any browser — no build step.

---

## Chapter 02 — Prompt Engineering for QA

This chapter turns prompt engineering into a repeatable QA skill. Three pillars:

1. **Anti-hallucination rules** — guardrails so the model only uses provided input.
2. **RICE-POT framework** — a structured prompt template (Role, Instructions, Context, Example, Parameters, Output, Tone).
3. **Two projects + six templates** — applied on real artifacts (a PRD-style API doc and a Selenium framework build).

### Anti-Hallucination Rules (`Anti_Hallucinations_Rules.md`)

A drop-in `ROLE` block you prepend to any QA prompt. Forces the model to:
- Use only the inputs you provide (PRD, screenshots, API docs).
- Refuse to assume "typical" system behaviour.
- Output exactly `"Insufficient information to determine."` when an input is missing.
- Label inferred details as `"Inference (low confidence)"`.
- Produce a Verified Facts / Missing Info / Output / Self-Validation block.

Use this on every factual-generation prompt in this repo.

### Project 1 — Test Case Generation with RICE-POT

Goal: turn an API PDF (`Restful-booker.pdf`) into a CSV of enterprise-grade test cases.

- `RICE-POT-TestCase-Prompt.md` — the worked prompt. Targets `app.vwo.com` as the example product, but the structure transfers to any PRD/API doc.
- `RICE_POT_FRAMEWORK/RICE_POT.md` — explanation of each letter of the framework.
- `Restful-booker.pdf` + `Restful_Booker_API_Test_Cases.md` — input PDF and the generated test-case set.
- `output/deepseek_csv_20260524_0d9b7c.csv` — actual model output produced from the prompt.

**How to exercise it:**
1. Open `RICE-POT-TestCase-Prompt.md` in any AI tool (ChatGPT, Claude, Gemini, DeepSeek).
2. Attach `Restful-booker.pdf` (or your own PRD).
3. Confirm the output is CSV only, columns match the spec, and every test case traces back to the PDF.

### Project 2 — Selenium Framework from a Prompt

Goal: prove RICE-POT can build production code, not just test cases.

- `Problem.md` — the brief: "generate a Selenium framework from scratch with two page objects, production ready."
- `SKILL.md` — the RICE-POT prompt-builder skill definition. Tells the AI how to interview you, assemble the prompt, and deliver it copy-pasteable.
- `blank-template-rice-pot.md` — fill-in template with the recommended anti-hallucination Parameters block.
- `AdvanceSeleniumFramework/` — the actual output the framework generates:
  - Maven project, Java 11, Selenium 4.25, TestNG 7.10.
  - `LoginPage.java` — PageFactory POM with explicit waits, fluent API, no Thread.sleep.
  - `BaseTest.java` — driver lifecycle.
  - `ConfigReader.java` — `config.properties` loader.
  - `ValidLoginTest.java` / `InvalidLoginTest.java` — positive + negative TestNG cases.
  - `testng.xml` / `testng-smoke.xml` — full and smoke suites.

**Run it:**
```bash
cd chapter_02_Prompt_Eng/Project2_Selenium_Framework/AdvanceSeleniumFramework
mvn -q clean test-compile
mvn test                       # full suite
mvn test -DsuiteXmlFile=testng-smoke.xml   # smoke only
```

### Templates — RTCFR + RICE-POT (`templates/`)

Six copy-paste prompt templates for the most common QA tasks. Each follows the **RTCFR** shape — Role, Task, Constraints, Format, Requirements — which is the lightweight cousin of RICE-POT.

| # | File | Purpose |
|---|------|---------|
| 01 | `01_TestCaseGeneration_Prompt.md` | Basic test-case generation from free-form requirements. |
| 02 | `02_TestCases_from_prd` | Comprehensive PRD → test cases (functional, negative, boundary, edge). |
| 03 | `03_API_Test_Generation.md` | API endpoint test cases from API docs. |
| 04 | `04_Negative_TC_Only.md` | Negative-only suite — invalid inputs, auth violations, malformed data. |
| 05 | `05_Secuirty_Test.md` | OWASP-top-10-aligned security test cases. |
| 06 | `06_Regression_Suite.md` | Regression suite for a module with execution-time estimates. |

**Use any template:**
1. Open the file and copy the fenced block.
2. Replace `[FEATURE]` / `[PASTE REQUIREMENTS]` / `[PASTE PRD]` etc. with your input.
3. Paste into your AI tool. Keep the `CONSTRAINTS` block intact — that's what stops hallucination.

---

## Chapter 03 — B.L.A.S.T Framework (AI Test Plan Generator)

A full-stack project applying the **B.L.A.S.T Framework** to build an AI-powered Test Plan Generator.
- **B**lueprint: Defined the JSON data schema and discovery questions.
- **L**ink: Connected to the Jira API v2 and Groq LLM.
- **A**rchitect: 3-Layer architecture (Architecture SOPs, Navigation Router in FastAPI, Tools for atomic Python scripts).
- **S**tylize: A lightweight Vite React application with a premium glassmorphism UI.
- **T**rigger: Deployed the full stack to Vercel.

**What's here:**
- `Chapter003BlastFW/` — The complete source code.
- `Chapter003BlastFW/B.L.A.S.T.md` — The protocol instructions.
- `Chapter003BlastFW/api/` and `Chapter003BlastFW/tools/` — The Python backend.
- **Live Demo:** [https://testplannerbuddy.vercel.app](https://testplannerbuddy.vercel.app)

---

## Chapter 04 — AI Agents with n8n

This chapter introduces automation and AI Agents using n8n. As part of this chapter, a local-first Job Tracker application was created.

**What's here:**
- `Chapter004AIAgentsWithn8n/Project_Job_Tracker/` — A single-page React application scaffolded with Vite and Tailwind CSS.
- **Local Persistence:** Uses `idb` for browser IndexedDB storage without a backend.
- **Drag-and-Drop Kanban:** Wishlist, Applied, Follow-up, Interview, Offer, Rejected columns powered by `@dnd-kit`.
- **Features:** Modal for Adding/Editing Jobs, Export/Import JSON for backup, and Light/Dark mode.

---

## Chapter 05 — AI Agents with LangFlow

This chapter explores visual programming of AI Agents using LangFlow. As part of this chapter, a **Flaky Test Analyzer AI Agent** was built.

**What's here:**
- `Chapter005AIAgentsWithLangFlow/flaky_test_Analyzer_Ai_Agent/UI` — A React + Vite web UI providing a smooth frontend interface for the agent.
- **AI-Powered Flaky Test Detection:** The agent processes Playwright test results from multiple builds to accurately identify flaky vs. consistent failures.
- **LangFlow Backend Integration:** The React application seamlessly integrates with the LangFlow backend, utilizing a Vite proxy to prevent CORS issues and accurately applying tweaks using internal component IDs.

---

## Chapter 06 — RAG (Retrieval-Augmented Generation)

This chapter demystifies how to connect LLMs to private data using a local Vector Database and the LangChain ecosystem. As part of this chapter, a complete **RAG Explorer** web application was built.

**What's here:**
- `Chapter006Rag/Basic_Rag/` — A full-stack application (React frontend + Express/LangChain backend).
- **PDF Data Ingestion:** Automatically parses a complex PRD (Product Requirements Document), chunks the text, and generates mathematical embeddings using Ollama (`nomic-embed-text`).
- **Local Vector Search:** Stores the chunks into a local ChromaDB instance, allowing lightning-fast semantic search without cloud databases.
- **AI Answer Generation:** Retrieves relevant chunks and passes them to Groq's high-speed inference engine (`llama-3.3-70b-versatile`) to accurately answer questions based solely on the provided PDF.

---

## How to Use This Repo

You can read it linearly (chapter 01 → 02) or jump straight to a project:

- **"I want better test cases now."** → `chapter_02_Prompt_Eng/templates/01_TestCaseGeneration_Prompt.md` or `02_TestCases_from_prd`.
- **"I want to write tests from a PDF/API doc."** → `chapter_02_Prompt_Eng/Project1_TC_Gen/`.
- **"I want to scaffold a Selenium project."** → `chapter_02_Prompt_Eng/Project2_Selenium_Framework/SKILL.md`, then run the Maven project under `AdvanceSeleniumFramework/`.
- **"I want my model to stop making things up."** → `chapter_02_Prompt_Eng/Anti_Hallucinations_Rules.md`.

## Requirements

- Any modern LLM (Claude / GPT / Gemini / DeepSeek). No specific provider required.
- For Project 2 only: **JDK 11+** and **Maven 3.9+** to compile and run the Selenium framework.

## Previous Chapters

`a2eb280` — chapter 01 LLM basics with interactive attention visualisations.
`dfe2653` — chapter 02 prompt engineering with RICE-POT framework + Selenium project.

---

Made by [Pramod Dutta](https://thetestingacademy.com/) for The Testing Academy.
