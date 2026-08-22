# 🤖 QABuddy.ai — Enterprise Hybrid RAG for QA Engineers

> **One Question. One Grounded, Cited Answer.**  
> A self-hosted, multi-source Hybrid RAG (Retrieval-Augmented Generation) intelligence platform built for QA engineers — connecting your Selenium framework, Playwright framework, test case repositories, JIRA tickets, PRDs, Jenkins logs, and meeting transcripts.

---

## 📑 Table of Contents
1. [Overview & Target Impact](#-overview--target-impact)
2. [Step-by-Step Activities from Scratch](#-step-by-step-activities-from-scratch)
3. [Architecture & Technology Decisions](#-architecture--technology-decisions)
4. [Data Sources (10 Domains)](#-data-sources-10-domains)
5. [Prerequisites & Setup Guide](#-prerequisites--setup-guide)
6. [Starting the Application (Backend & Frontend)](#-starting-the-application-backend--frontend)
7. [How to Use the UI (Claude.ai Theme)](#-how-to-use-the-ui-claudeai-theme)
8. [API Reference & Programmatic Usage](#-api-reference--programmatic-usage)
9. [Running Automated Tests](#-running-automated-tests)
10. [Docker Deployment](#-docker-deployment)
11. [Project Directory Structure](#-project-directory-structure)

---

## 🎯 Overview & Target Impact

Traditional QA onboarding and test analysis suffer from fragmented knowledge across disparate systems (Git repos, test spreadsheets, JIRA, PDFs, logs). **QABuddy.ai** unifies these 10 data sources into a single searchable brain with hybrid dense + sparse retrieval, cross-encoder reranking, and grounded answers with strict file/ticket citations.

### Coverage & Productivity Impact
| Setup | Expected Test Coverage |
|:---|:---|
| GitHub Copilot + JIRA (MCP) | ~30–40% |
| **GitHub Copilot + QABuddy.ai (Hybrid RAG) + JIRA** | **~70–80%** |

### Key Use Cases
- 🚀 **Onboarding:** New QA engineers self-serve answers about framework architecture, conventions, and test setups.
- 📚 **Knowledge Brain:** Search across code, TestNG XML suites, Playwright configs, PRD specifications, and team sprint notes.
- 🔍 **Root Cause Analysis (RCA):** Correlate Jenkins build failure stack traces with recent JIRA tickets and code changes.
- 📝 **Test Design & Gap Analysis:** Generate test cases directly aligned with PRD requirements and existing regression suites.
- ⚡ **Flaky Test Management:** Retrieve flaky test history, retry policies, and annotations across frameworks.

---

## 🛠️ Step-by-Step Activities from Scratch

Here is the chronological breakdown of how QABuddy.ai was designed, engineered, and validated from scratch:

```
Step 1: Architecture & Model Selection (BGE-M3 + Qdrant + BGE-Reranker-v2 + Gemini)
   ↓
Step 2: 10 Data Source Folder Structure & Repository Cloning
   ↓
Step 3: Source-Appropriate Parsers & Preprocessing (AST, Pandas, PyMuPDF, JIRA, Logs)
   ↓
Step 4: Semantic Chunking Engine (Method-level, Row-level, Recursive prose, Log blocks)
   ↓
Step 5: Vector Store & Ingestion Orchestrator (Qdrant Embedded, Dense 1024d + Sparse Lexical)
   ↓
Step 6: Hybrid Retrieval & Cross-Encoder Reranker (RRF Fusion + Sigmoid Cross-Encoder)
   ↓
Step 7: QA Chain & LLM Generation (Strict citation formatting & anti-hallucination)
   ↓
Step 8: FastAPI Backend Development (/api/chat, /api/health, /api/ingest)
   ↓
Step 9: Streamlit UI with Claude.ai Theme (White/Cream #FAF8F5, Teal accents, Newsreader Serif)
   ↓
Step 10: Pytest Test Suite (51 unit & integration tests) & Live Autonomous Browser Testing
```

### Detailed Breakdown of Engineering Phases:

1. **Architecture & Technology Decisions:**
   - Evaluated open-source embedding models: selected **`BAAI/bge-m3`** for single-pass dense (1024d) + sparse (lexical weights) vectors.
   - Selected **`Qdrant`** as the vector database supporting native hybrid search with Reciprocal Rank Fusion (RRF) and local embedded mode (`qdrant_data/`) requiring zero Docker overhead.
   - Selected **`BAAI/bge-reranker-v2-m3`** via `sentence_transformers.CrossEncoder` to rerank top candidates for high precision.
   - Integrated **Google Gemini (`gemini-2.5-flash`)** as default LLM with seamless fallback to OpenAI (`gpt-4o-mini`).

2. **Data Directory & Repo Ingestion:**
   - Created numbered directories `data/01_selenium_framework/` through `data/10_jenkins_logs/`.
   - Built `scripts/clone_repos.py` to clone the advanced Java Selenium Framework and TypeScript Playwright Framework.

3. **Specialized Parsers & Cleaners:**
   - `code_parser.py`: Extracts classes, methods, POM functions, and XML test suites.
   - `csv_parser.py`: Maps canonical column aliases across test case spreadsheets (5,000 rows).
   - `jira_parser.py`: Connects to live JIRA REST API and parses offline Markdown/JSON tickets (`KAN-13.md`).
   - `pdf_parser.py`: Extracts structured text sections from PRDs using PyMuPDF.
   - `transcript_parser.py`: Groups speaker turns from sprint reviews and test planning meetings.
   - `log_parser.py`: Parses Jenkins logs into classified blocks (`build_info`, `stack_trace`, `test_result`).
   - `text_cleaner.py`: Expands 40+ QA domain abbreviations (POM, RTM, RCA, BRD, etc.).

4. **Chunking Engine:**
   - Code: Unit/Method level (up to 1,500 tokens, 0 overlap).
   - Test cases: 1 row = 1 atomic chunk.
   - JIRA tickets: Self-contained ticket units.
   - PRD / SRS: 1,000 tokens with 150 token overlap.
   - Transcripts & Company Docs: 600–800 tokens with paragraph awareness.
   - Jenkins Logs: Log block boundaries.

5. **Embedding & Indexing Pipeline:**
   - Implemented `src/ingestion/embedder.py` with dense + sparse encoding.
   - Implemented `src/retrieval/vector_store.py` for Qdrant payload indexing (`source_type`, `ticket_key`, `language`).
   - Ingested 462 core knowledge chunks into Qdrant in `qdrant_data/`.

6. **FastAPI Backend Server:**
   - Endpoints: `POST /api/chat`, `GET /api/health`, `POST /api/ingest`, `GET /`.
   - Complete with CORS, lifespan startup/shutdown, dependency injection, and Pydantic validation.

7. **Claude.ai Themed UI:**
   - Warm white and cream palette (`#FAF8F5`, `#F4EFE6`, `#FFFFFF`).
   - Typography: Google Fonts `Newsreader` (editorial serif) + `Plus Jakarta Sans` + `JetBrains Mono`.
   - Teal accents (`#0D9488`, `#0F766E`, `#F0FDFA`).
   - Interactive prompt starter cards, domain filtering dropdown, live system health cards, and cited knowledge source accordions.

8. **Testing & Live Browser Verification:**
   - Built 51 automated unit and integration tests (`100% pass rate`).
   - Performed live browser testing of the UI, verifying authentication, query execution, and cited answers.

---

## 🏗️ Architecture & Technology Decisions

```
Data Sources (10) ──► Ingestion Pipeline ──► Qdrant Vector DB ──► FastAPI Backend ──► Streamlit UI
                      - Parse & Clean         (Dense + Sparse)     (QA Chain + LLM)  (Claude.ai Theme)
                      - Chunk & Embed         Local Embedded       Gemini 2.5 Flash
                      - Tag Metadata          qdrant_data/
```

| Component | Technology | Rationale |
|:---|:---|:---|
| **Embedding Model** | `BAAI/bge-m3` | Produces dense (1024d) AND sparse lexical weights in one pass (no separate BM25 index needed). |
| **Vector DB** | `Qdrant` | Native dense + sparse hybrid search with server-side RRF fusion. Runs in embedded local mode. |
| **Reranker** | `BAAI/bge-reranker-v2-m3` | Cross-encoder that scores query-document pairs jointly with sigmoid normalization. |
| **LLM Provider** | Google Gemini 2.5 Flash | Fast, cost-efficient, 1M context window, low temperature (0.3) for grounded answers. |
| **Backend** | FastAPI + Uvicorn | Asynchronous Python REST API with OpenAPI documentation. |
| **Frontend UI** | Streamlit | Custom-styled Claude.ai warm cream/white aesthetic with teal accents. |

---

## 📂 Data Sources (10 Domains)

| # | Source | Directory | Format | Ingested |
|:--|:---|:---|:---|:---|
| 1 | Selenium Framework | `data/01_selenium_framework/` | Java Repo (POM, XML suites) | ✅ 69 chunks |
| 2 | Playwright Framework | `data/02_playwright_framework/` | TypeScript / JS Repo | ✅ 231 chunks |
| 3 | Test Cases | `data/03_test_cases/` | CSV / XLSX (`test_cases.csv`) | ✅ 5,000 rows |
| 4 | JIRA Tickets | `data/04_jira_tickets/` | REST API + Markdown (`KAN-13.md`) | ✅ 1 chunk |
| 5 | Company Docs | `data/05_company_docs/` | Markdown (`qa_framework_guide.md`) | ✅ 26 chunks |
| 6 | Figma Designs | `data/06_figma_designs/` | Figma Exports (Phase 2) | Ready |
| 7 | Meeting Transcripts | `data/07_meeting_transcripts/` | Text transcripts (Sprint reviews) | ✅ 70 chunks |
| 8 | Lucid Charts | `data/08_lucid_charts/` | Exported text | Ready |
| 9 | PRD / SRS Docs | `data/09_prd_srs_brd_frd/` | PDF (`VWO PRD.pdf`) | ✅ 55 chunks |
| 10 | Jenkins Logs | `data/10_jenkins_logs/` | Build logs (`build_*.log`) | ✅ 10 chunks |

---

## 🚀 Prerequisites & Setup Guide

### 1. Prerequisites
- **Python:** 3.11+ (Python 3.11 – 3.14 supported)
- **Git**
- **Google Gemini API Key** (or OpenAI API Key)

### 2. Installation

```bash
# Navigate to the Chapter007 directory
cd Chapter007QABuddyAI

# Install all dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (`.env`)
Create or edit `.env` in `Chapter007QABuddyAI/`:

```env
# --- LLM Provider ---
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash

# --- Qdrant Vector Database ---
QDRANT_COLLECTION_NAME=qabuddy
QDRANT_PATH=./qdrant_data

# --- Embedding & Reranking ---
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
USE_GPU=false
HYBRID_SEARCH_TOP_K=15
RERANK_TOP_K=5

# --- Security ---
APP_PASSWORD=qabuddy2026
```

### 4. Clone Repositories & Ingest Data

```bash
# Step A: Clone the framework repositories
python scripts/clone_repos.py

# Step B: Ingest all sources into Qdrant
python scripts/ingest_all.py --sources selenium_repo playwright_repo jira_tickets meeting_transcripts prd_docs jenkins_logs company_docs
```

---

## 🖥️ Starting the Application (Backend & Frontend)

### 1. Start the FastAPI Backend Server
Open a terminal in `Chapter007QABuddyAI/`:

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```
- **API URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **Health Endpoint:** `http://localhost:8000/api/health`

### 2. Start the Streamlit Chat UI
Open a second terminal in `Chapter007QABuddyAI/`:

```bash
python -m streamlit run src/ui/app.py --server.port 8501
```
- **Chat UI URL:** `http://localhost:8501`

---

## 🎨 How to Use the UI (Claude.ai Theme)

1. **Open the UI:** Navigate to `http://localhost:8501` in your browser.
2. **Login:** Enter the access password: `qabuddy2026` and click **Unlock QABuddy →**.
3. **Explore the Claude.ai Interface:**
   - **Warm Canvas:** Soft white & cream aesthetic with editorial serif typography.
   - **Sidebar Status:** Real-time indicator showing API health, Qdrant indexed chunk count (462 chunks), LLM provider, and embedding model.
   - **Knowledge Domain Filter:** Select *All Sources* or narrow down to a specific domain (e.g. `selenium_repo`, `jira_tickets`, `prd_docs`).
4. **Try Suggested Prompt Starters:**
   - 🧩 *Selenium BaseTest & DriverManager*
   - 📋 *KAN-13 Acceptance Criteria*
   - 🔍 *Analyze Jenkins Log Failure*
   - 🎭 *Playwright Headless Configuration*
5. **Ask Custom Questions:** Type in the chat input:
   - *"How do I initialize and tear down the WebDriver in the Selenium framework?"*
   - *"What are the functional requirements in ticket KAN-13?"*
   - *"What caused the test failure in the Jenkins build log? Explain the stack trace."*
6. **Inspect Citations:** Click on the **📚 Cited Knowledge Sources** expander under any response to see matching filenames, source types, and cross-encoder similarity scores.

---

## 🔌 API Reference & Programmatic Usage

### 1. Chat Completion (`POST /api/chat`)

```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "question": "How is the BaseTest class structured in our Selenium framework?",
       "source_filter": "selenium_repo"
     }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "question": "Explain how DriverManager handles WebDriver lifecycle.",
        "source_filter": None,
    },
)

data = response.json()
print("Answer:\n", data["answer"])
print("Cited Sources:", len(data["sources"]))
```

### 2. Health Check (`GET /api/health`)

```bash
curl "http://localhost:8000/api/health"
```

**Response:**
```json
{
  "status": "healthy",
  "qdrant_status": "connected",
  "collection_info": {
    "name": "qabuddy",
    "points_count": 462,
    "status": "green"
  },
  "llm_provider": "gemini",
  "embedding_model": "BAAI/bge-m3"
}
```

---

## 🧪 Running Automated Tests

Run the complete test suite covering parsers, chunkers, cleaners, vector store, and API models:

```bash
python -m pytest tests/ -v
```

**Test Output:**
```text
tests/test_chunkers.py::TestCodeChunker::test_single_method_fits_in_one_chunk PASSED
tests/test_chunkers.py::TestRowChunker::test_each_row_is_one_chunk PASSED
tests/test_parsers.py::TestCodeParser::test_parse_java_method PASSED
tests/test_parsers.py::TestLogParser::test_parse_log_file PASSED
tests/test_qa_chain.py::TestQAChainIntegration::test_chain_calls_search_then_rerank PASSED
tests/test_retrieval.py::TestPromptTemplates::test_build_qa_prompt PASSED
============================= 51 passed in 2.88s ==============================
```

---

## 🐳 Docker Deployment

To deploy QABuddy.ai in a self-hosted Docker environment:

```bash
# Build and run containers
docker compose -f docker/docker-compose.yml up -d

# Check status
docker compose -f docker/docker-compose.yml ps
```

Services started:
- **FastAPI Backend:** Port 8000
- **Streamlit Chat UI:** Port 8501
- **Qdrant Vector Database:** Port 6333

---

## 📁 Project Directory Structure

```
Chapter007QABuddyAI/
├── .env                              # Environment variables & API keys
├── .env.example                      # Example configuration template
├── README.md                         # Complete project documentation
├── PHASE1_PLAN.md                    # Phase 1 design & architecture plan
├── PHASE2_PLAN.md                    # Phase 2 auto-ingestion plan
├── requirements.txt                  # Python dependencies
├── pytest.ini                        # Pytest configuration
├── qdrant_data/                      # Local Qdrant embedded vector database
│   └── collection/                   # Persistent vector indexes
├── data/                             # 10 Data Source directories
│   ├── 01_selenium_framework/        # Java Selenium advance framework
│   ├── 02_playwright_framework/      # TypeScript Playwright framework
│   ├── 03_test_cases/                # 5,000 CSV test cases
│   ├── 04_jira_tickets/              # JIRA tickets (KAN-13.md)
│   ├── 05_company_docs/              # Markdown guides & standards
│   ├── 06_figma_designs/             # Figma design exports (Phase 2)
│   ├── 07_meeting_transcripts/       # Sprint review transcripts
│   ├── 08_lucid_charts/              # Lucid chart text exports
│   ├── 09_prd_srs_brd_frd/           # PDF PRD requirement documents
│   └── 10_jenkins_logs/              # Jenkins build failure logs
├── scripts/
│   ├── clone_repos.py                # Repo cloning script
│   ├── ingest_all.py                 # Master ingestion CLI
│   └── test_retrieval.py             # Retrieval quality benchmark
├── src/
│   ├── api/                          # FastAPI application
│   │   ├── main.py                   # App lifecycle & router setup
│   │   ├── models.py                 # Pydantic request/response schemas
│   │   └── routes/                   # chat.py, health.py, ingest.py
│   ├── chat/                         # Chat & LLM synthesis
│   │   ├── llm_client.py             # Gemini & OpenAI client wrapper
│   │   ├── prompt_templates.py       # QA prompt formatting with citations
│   │   └── qa_chain.py               # End-to-end RAG chain
│   ├── config/                       # Centralized settings
│   │   ├── settings.py               # Pydantic/dataclass configuration
│   │   └── glossary.json             # QA domain terminology glossary
│   ├── ingestion/                    # Parsing, cleaning, chunking
│   │   ├── cleaners/                 # Text & abbreviation expanders
│   │   ├── chunkers/                 # Code, row, ticket, prose, log chunkers
│   │   ├── parsers/                  # Code, CSV, JIRA, PDF, transcript, log parsers
│   │   ├── embedder.py               # BGE-M3 dense + sparse embedding
│   │   └── orchestrator.py           # Master multi-source orchestrator
│   ├── retrieval/                    # Search & Reranking
│   │   ├── vector_store.py           # Qdrant hybrid vector store wrapper
│   │   ├── hybrid_search.py          # Dense + sparse hybrid query engine
│   │   └── reranker.py               # Cross-encoder reranker
│   └── ui/                           # Frontend
│       └── app.py                    # Claude.ai themed Streamlit chat interface
├── tests/                            # Unit & Integration test suite
└── docker/                           # Dockerfiles & docker-compose config
```

---

Built with ❤️ for QA Engineers | **QABuddy.ai** — Powered by BGE-M3 + Qdrant + Gemini
