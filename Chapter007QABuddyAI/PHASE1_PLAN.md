# QABuddy.ai — Phase 1 Build Plan & Implementation Summary

> **Status:** ✅ Complete  
> **Original Prompt:** [qabuddy-ai-build-prompt.md](./qabuddy-ai-build-prompt.md)

---

## Overview

Phase 1 builds the complete, end-to-end QABuddy.ai system — from raw data sources through to a deployed, chatbot accessible to QA engineers 24×7. Every component from data ingestion to the chat UI was designed, implemented, and tested in this phase.

---

## Step 1 — Architecture & Technology Decisions

Before writing any code, the following key decisions were made and justified:

### 1.1 Embedding Model: `BAAI/bge-m3`

| Decision | Reason |
|:--|:--|
| **BGE-M3** (open-source, HuggingFace) | Produces **both dense AND sparse vectors in one pass** — no need for a separate BM25 index |
| 1024-dimensional dense vector | High-quality semantic representation across multiple languages |
| Lexical weights (sparse) | Enables keyword-level matching for test case IDs, JIRA keys, method names |
| Runs on CPU | No GPU required for the DigitalOcean droplet deployment |

> **Why not OpenAI embeddings?** The constraint is open-source + self-hosted. BGE-M3 is the best open-source option for hybrid (dense + sparse) retrieval from a single model.

### 1.2 Vector Database: `Qdrant`

| Decision | Reason |
|:--|:--|
| **Qdrant** (open-source) | Native hybrid search: stores both dense and sparse vectors per point |
| RRF Fusion (Reciprocal Rank Fusion) | Server-side fusion of dense + sparse results — no client-side merging |
| Payload indexes | Enables filtering by `source_type`, `language`, `ticket_key` without full scan |
| Docker-deployable | One-command spin-up on any VPS/DigitalOcean droplet |

> **Why not FAISS or Chroma?** FAISS doesn't support sparse vectors natively. Chroma lacks native hybrid search and production-grade persistence for this scale.

### 1.3 Reranker: `BAAI/bge-reranker-v2-m3`

| Decision | Reason |
|:--|:--|
| Cross-encoder reranker | Scores query–document pairs jointly — much more accurate than bi-encoder score |
| Retrieve top-50 → Rerank → Return top-5 | Token-efficient: only 5 chunks sent to LLM, not 50 |
| FP16 inference | Halves memory footprint on CPU; still accurate |

### 1.4 LLM: Gemini 2.0 Flash (default) / GPT-4o-mini (alternative)

| Decision | Reason |
|:--|:--|
| Gemini 2.0 Flash | Fast, cheap, 1M context window — handles large code + ticket context |
| Switchable via env var | `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` — zero code changes |
| Temperature = 0.3 | Low temperature keeps answers factual and grounded |

### 1.5 Chunk Sizes Per Source Type

| Source | Chunk Size | Overlap | Rationale |
|:--|:--|:--|:--|
| Code (Java/TS/Python) | Method/class = 1 chunk (max 1,500 tokens) | 0 (logical boundary) | Code units are already semantically complete — splitting mid-method loses context |
| Test cases (CSV rows) | 1 row = 1 chunk (~200–400 tokens) | 0 | Each test case is atomic and self-contained |
| JIRA tickets | 1 ticket = 1 chunk (max 1,000 tokens) | 0 (split at Comments boundary) | Ticket + description must stay together for RCA queries |
| PRD / SRS docs | 1,000 tokens | 150 tokens | Long prose sections; overlap preserves context across chunk boundaries |
| Company docs / Markdown | 800 tokens | 120 tokens | Standard prose chunking with paragraph-aware splitting |
| Meeting transcripts | 600 tokens | 90 tokens | Speaker-turn aware segments; smaller for precision |
| Jenkins logs | 500 tokens | 50 tokens | Log blocks (build info, test results, stack traces) are short but dense |
| Lucid chart exports | 500 tokens | 50 tokens | Exported text is compact; smaller chunks = more precise retrieval |

---

## Step 2 — Folder Structure for 10 Data Sources

Created all 10 source directories under `data/`:

```
data/
├── 01_selenium_framework/      # Java Selenium framework repo (git clone)
├── 02_playwright_framework/    # TypeScript Playwright framework repo (git clone)
├── 03_test_cases/              # CSV / XLSX test cases (~5,000 rows)
│   └── sample_testcases.csv   # 30 demo test cases (all categories)
├── 04_jira_tickets/            # JSON files (fetched from JIRA API or saved here)
├── 05_company_docs/            # PDF + Markdown company documents
│   └── qa_framework_guide.md  # Demo framework guide document
├── 06_figma_designs/           # Phase 2 only — Figma exports
├── 07_meeting_transcripts/     # Plain text meeting notes / speaker-labeled transcripts
│   └── sprint15_planning_2026-08-20.txt  # Demo sprint planning transcript
├── 08_lucid_charts/            # Lucid chart text exports
├── 09_prd_srs_brd_frd/         # PDF requirement documents
└── 10_jenkins_logs/            # Jenkins build logs
    └── build_20260821_001.log  # Demo failed build log
```

> **Why numbered prefixes?** To preserve ingestion order and make the folder intent immediately clear to any engineer browsing the filesystem.

---

## Step 3 — Ingestion Pipeline: Parse → Clean → Chunk → Embed → Index

The pipeline handles 10 different source types with source-appropriate logic at every stage.

### 3.1 Parsers (`src/ingestion/parsers/`)

Each parser extracts text and metadata from its source format:

| Parser | File | What It Does |
|:--|:--|:--|
| **Code Parser** | `code_parser.py` | Regex-based AST-style parsing — extracts Java classes/methods, JS/TS functions, Python classes/functions as `ParsedCodeUnit` objects |
| **CSV Parser** | `csv_parser.py` | Reads CSV/XLSX via pandas; auto-detects column aliases (`test_id`/`tc_id`/`id`); builds a human-readable text block per row |
| **PDF Parser** | `pdf_parser.py` | PyMuPDF (fitz) extracts text block-by-block, detects headings via font size and bold flags, splits into `ParsedPDFSection` objects, also extracts tables |
| **Text Parser** | `text_parser.py` | Splits Markdown by `#`/`##`/`###` headings; splits plain text by double-newlines into paragraphs |
| **JIRA Parser** | `jira_parser.py` | Connects to JIRA REST API via `python-jira`; processes JQL query results; cleans Atlassian markup; saves to disk as JSON for offline access |
| **Transcript Parser** | `transcript_parser.py` | Detects speaker-labeled format (`Alice: ...`); groups turns into conversation segments |
| **Log Parser** | `log_parser.py` | Classifies log blocks as `build_info`, `test_result`, `stack_trace`, or `general`; splits at separator lines (`===`) |

### 3.2 Cleaners (`src/ingestion/cleaners/`)

Each cleaner normalises the extracted text before chunking:

| Cleaner | File | What It Does |
|:--|:--|:--|
| **Code Cleaner** | `code_cleaner.py` | Normalises tabs→4 spaces; collapses blank lines (max 2); preserves code structure |
| **Text Cleaner** | `text_cleaner.py` | Expands QA abbreviations (RTM→Requirements Traceability Matrix, RCA→Root Cause Analysis, POM→Page Object Model, etc.); strips boilerplate headers/footers; normalises whitespace |
| **Log Cleaner** | `log_cleaner.py` | Strips ANSI colour codes; removes Maven download noise (`Downloading: https://repo.maven.org/...`); normalises timestamps |

### 3.3 Chunkers (`src/ingestion/chunkers/`)

Each chunker converts parsed objects into `Chunk` objects ready for embedding:

| Chunker | File | Strategy |
|:--|:--|:--|
| **Code Chunker** | `code_chunker.py` | 1 method/class = 1 chunk with context header (`Language | File | Method`); oversized units split by line boundaries |
| **Row Chunker** | `row_chunker.py` | 1 test case row = 1 chunk; no splitting — test cases are atomic |
| **Ticket Chunker** | `ticket_chunker.py` | 1 ticket = 1 chunk; oversized tickets split at `Comments` boundary |
| **Recursive Chunker** | `recursive_chunker.py` | Recursive separator hierarchy: `\n\n` → `\n` → `. ` → ` `; respects paragraph/sentence boundaries; configurable per source type via `CHUNK_PROFILES` |
| **Log Chunker** | `log_chunker.py` | 1 classified log block = 1 chunk; oversized blocks split by line count |
| **Base** | `base.py` | Shared `Chunk` dataclass used by all chunkers |

### 3.4 Embedder (`src/ingestion/embedder.py`)

```
Input: List[str] (chunk text)
   │
   ▼
BGE-M3 (via FlagEmbedding, batched, batch_size=32)
   │
   ├── dense_vector: List[float] (1024 dimensions, cosine-normalized)
   └── sparse_vector: Dict[int, float] (token_id → weight, lexical weights)
   │
   ▼
Output: List[EmbeddingResult]
```

- Falls back to `sentence-transformers` (dense-only) if `FlagEmbedding` is not installed
- GPU support via `USE_GPU=true` env var
- Batch processing with progress logging every 10 batches

### 3.5 Ingestion Orchestrator (`src/ingestion/orchestrator.py`)

The master controller that wires all the above steps together for each of the 9 Phase 1 sources:

```
IngestionOrchestrator.ingest_all(sources=None)
    │
    ├── selenium_repo:    code_parser → code_cleaner → code_chunker
    ├── playwright_repo:  code_parser → code_cleaner → code_chunker
    ├── test_cases:       csv_parser  → text_cleaner → row_chunker
    ├── jira_tickets:     jira_parser → text_cleaner → ticket_chunker
    ├── company_docs:     pdf_parser + text_parser → text_cleaner → recursive_chunker
    ├── meeting_transcripts: transcript_parser → text_cleaner → recursive_chunker
    ├── lucid_charts:     text_parser → text_cleaner → recursive_chunker
    ├── prd_docs:         pdf_parser + text_parser → text_cleaner → recursive_chunker
    └── jenkins_logs:     log_parser → log_cleaner → log_chunker
    │
    └── _embed_and_index(chunks, source_type)
            │
            ├── embed_texts(texts) → List[EmbeddingResult]
            └── vector_store.upsert_chunks(chunks, embeddings, source_type)
```

---

## Step 4 — Vector Store: Qdrant with Hybrid Search

### 4.1 Collection Schema (`src/retrieval/vector_store.py`)

```
Collection: "qabuddy"
├── Dense vector:  "dense"  — 1024-dim, COSINE distance
├── Sparse vector: "sparse" — sparse index (BM25-style lexical weights)
└── Payload indexes: source_type, language, unit_type, ticket_key
```

### 4.2 Point Payload (what's stored per chunk)

```json
{
  "text": "public void testValidLogin() { ... }",
  "source_type": "selenium_repo",
  "source_file": "LoginTest.java",
  "title": "testValidLogin (method)",
  "language": "java",
  "unit_type": "method",
  "unit_name": "testValidLogin",
  "start_line": 35,
  "end_line": 48,
  "chunk_index": 0,
  "total_chunks": 1,
  "ingested_at": "2026-08-21T16:30:00Z"
}
```

### 4.3 Hybrid Search with RRF Fusion

```
Query: "How do I set up the Selenium base test class?"
    │
    ▼
embed_query(query) → {dense_vector: [...], sparse_vector: {token: weight}}
    │
    ▼
Qdrant query_points() with prefetch:
    ├── Prefetch 1: dense search (top-50 by cosine)
    └── Prefetch 2: sparse search (top-50 by lexical match)
    │
    ▼
RRF Fusion (server-side) → Unified ranked list (top-50)
    │
    ▼
bge-reranker-v2-m3 cross-encoder → Reranked top-5
    │
    ▼
LLM prompt with 5 cited chunks → Answer with [Source: file.java]
```

---

## Step 5 — Chat Layer: Prompt Templates + LLM Client + QA Chain

### 5.1 System Prompt (`src/chat/prompt_templates.py`)

The system prompt enforces:
- **Citation mandate:** every claim must reference `[Source: filename or ticket-ID]`
- **Grounding:** answer ONLY from the retrieved context — never hallucinate
- **QA-domain specificity:** references RTM, RCA, POM, test failure analysis, bug triage

### 5.2 Context Block Builder

For each reranked chunk, a structured header is prepended:
```
**Chunk 1** | Title: testValidLogin (method) | Source: LoginTest.java | Type: selenium_repo | Language: java
```java
public void testValidLogin() {
    driver.get("https://example.com/login");
    ...
}
```

### 5.3 LLM Client (`src/chat/llm_client.py`)

- Supports **Gemini** (`google-generativeai`) and **OpenAI** (`openai`) via a single interface
- Switched via `LLM_PROVIDER` environment variable — no code changes needed
- Supports **multi-turn chat history** — last 6 turns injected into the prompt
- Temperature: 0.3, max_tokens: 2048, top_p: 0.9

### 5.4 QA Chain (`src/chat/qa_chain.py`)

```
QAChain.ask(question, source_filter=None, chat_history=None)
    Step 1: HybridSearcher.search(question, top_k=50)
    Step 2: rerank(question, candidates, top_k=5)
    Step 3: build_qa_prompt(question, reranked_chunks)
    Step 4: LLMClient.generate(system_prompt, user_prompt)
    Step 5: Return QAResponse(answer, sources, query, num_retrieved, num_reranked)
```

---

## Step 6 — FastAPI Backend (`src/api/`)

### Endpoints

| Method | Path | Description |
|:--|:--|:--|
| `GET` | `/` | API info and links |
| `POST` | `/api/chat` | Ask a question → cited answer |
| `POST` | `/api/ingest` | Trigger data ingestion (background-ready) |
| `GET` | `/api/health` | System health: Qdrant status, collection info, LLM provider |
| `GET` | `/docs` | Interactive Swagger UI |

### Request / Response Models (`src/api/models.py`)

```python
ChatRequest:  question (str), source_filter (str|None), chat_history (list|None)
ChatResponse: answer, sources: [SourceReference], query, num_chunks_retrieved, num_chunks_reranked
IngestRequest:  sources (list|None), recreate_collection (bool)
IngestResponse: status, stats: {source: count}, total_chunks, message
HealthResponse: status, qdrant_status, collection_info, llm_provider, embedding_model
```

### Dependency Injection

Services are initialised at FastAPI startup (lifespan) and injected into routes:
```python
# On startup:
vector_store = QdrantVectorStore()
searcher = HybridSearcher(vector_store)
llm_client = LLMClient()
qa_chain = QAChain(searcher, llm_client)

# Injected into routes:
chat_route.set_qa_chain(qa_chain)
ingest_route.set_vector_store(vector_store)
health_route.set_vector_store(vector_store)
```

---

## Step 7 — Streamlit Chat UI (`src/ui/app.py`)

### Features

| Feature | Detail |
|:--|:--|
| Password authentication | Simple password gate (`APP_PASSWORD` env var, default: `qabuddy2026`) |
| Source filter | Dropdown to restrict search to a specific data source |
| Multi-turn conversation | Chat history sent with each request (last 6 turns) |
| Cited sources panel | Expandable `📚 Sources` panel showing source file, type, and rerank score |
| System status | Live health display: API status, Qdrant status, indexed chunk count |
| One-click ingestion | "Ingest All Sources" button triggers the full pipeline from the UI |
| Premium dark theme | Custom CSS with gradient background, glassmorphism source cards, score colour coding |

### Architecture

```
Browser (Streamlit)
    │  HTTP POST /api/chat
    ▼
FastAPI Backend (port 8000)
    │
    ▼
QA Chain (embed → search → rerank → generate)
    │
    ▼
Answer + Sources → UI renders with citations
```

---

## Step 8 — Docker Deployment (`docker/`)

### Services

```
docker compose up -d
    │
    ├── qdrant         (port 6333/6334) — Qdrant vector database with persistent storage
    ├── qabuddy-api    (port 8000)      — FastAPI backend
    ├── qabuddy-ui     (port 8501)      — Streamlit chat UI
    └── nginx          (port 80)        — Reverse proxy routing / to UI, /api to backend
```

### Multi-stage Dockerfile

```dockerfile
FROM python:3.11-slim AS base   # shared base with all dependencies
FROM base AS api                # uvicorn CMD
FROM base AS ui                 # streamlit CMD
```

### Health Check

```yaml
qdrant:
  healthcheck:
    test: curl -f http://localhost:6333/healthz
    interval: 30s
    retries: 3
```

`qabuddy-api` waits for Qdrant to be healthy before starting.

---

## Step 9 — Scripts

| Script | Purpose |
|:--|:--|
| `scripts/clone_repos.py` | Clones Selenium and Playwright repos into `data/01_selenium_framework/` and `data/02_playwright_framework/` using `git clone --depth 1` |
| `scripts/ingest_all.py` | One-shot ingestion: connects to Qdrant, runs full pipeline; supports `--sources`, `--recreate`, `--dry-run` flags |
| `scripts/test_retrieval.py` | Retrieval quality smoke test — asks 7 representative QA questions and checks if the correct source type appears in the top-5 results |

---

## Step 10 — Tests (`tests/`)

### Test Files

| File | What It Tests |
|:--|:--|
| `tests/conftest.py` | Shared pytest fixtures: mock vector store, mock LLM, sample search results, temporary CSV/MD/log/transcript files |
| `tests/test_parsers.py` | Unit tests for all 5 parsers: Java/JS/Python code parsing, CSV column resolution, Markdown section splitting, speaker detection in transcripts, log block classification |
| `tests/test_chunkers.py` | Unit tests for all 5 chunkers: single/multiple code units, row-per-test-case, ticket splitting, recursive splitting with overlap, log block chunking |
| `tests/test_qa_chain.py` | Integration tests for the QA chain (mocked): no-results path, search→rerank→generate flow, source_filter forwarding, text cleaning |
| `tests/test_retrieval.py` | Unit tests for prompt templates, QA response structure, API models (Pydantic validation), and settings defaults |

### Running Tests

```bash
# All unit tests (no Qdrant required)
pytest tests/ -v -m "not integration"

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Integration tests (requires running Qdrant + ingested data)
pytest tests/ -v -m integration
```

---

## Step 11 — Configuration (`src/config/`)

### Settings (`settings.py`)

All settings are loaded from environment variables with sensible defaults:

```python
# Key settings with defaults
llm_provider       = "gemini"
embedding_model    = "BAAI/bge-m3"
reranker_model     = "BAAI/bge-reranker-v2-m3"
qdrant_host        = "localhost"
qdrant_port        = 6333
hybrid_search_top_k = 50          # Candidates from hybrid search
rerank_top_k        = 5           # Final chunks after reranking
max_context_tokens  = 3000        # Max tokens sent to LLM
```

### QA Domain Glossary (`glossary.json`)

A JSON glossary of 40+ QA abbreviations and terms used by the text cleaner to expand acronyms:

```json
{
  "RTM": "Requirements Traceability Matrix",
  "RCA": "Root Cause Analysis",
  "POM": "Page Object Model",
  "BDD": "Behaviour-Driven Development",
  "CI": "Continuous Integration",
  ...
}
```

---

## Complete File Structure Created in Phase 1

```
Chapter007QABuddyAI/
├── data/                                    # 10 data source directories
│   ├── 01_selenium_framework/               # Git clone target
│   ├── 02_playwright_framework/             # Git clone target
│   ├── 03_test_cases/
│   │   └── sample_testcases.csv            # 30 demo test cases
│   ├── 04_jira_tickets/                     # JIRA JSON files (API fetched)
│   ├── 05_company_docs/
│   │   └── qa_framework_guide.md           # Demo company doc
│   ├── 06_figma_designs/                    # Phase 2 only
│   ├── 07_meeting_transcripts/
│   │   └── sprint15_planning_2026-08-20.txt
│   ├── 08_lucid_charts/
│   ├── 09_prd_srs_brd_frd/
│   └── 10_jenkins_logs/
│       └── build_20260821_001.log          # Demo failed build log
│
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── settings.py                     # Central config (env vars + defaults)
│   │   └── glossary.json                   # QA abbreviation glossary
│   ├── ingestion/
│   │   ├── parsers/
│   │   │   ├── code_parser.py              # Java, JS/TS, Python parser
│   │   │   ├── csv_parser.py               # CSV/XLSX test case parser
│   │   │   ├── pdf_parser.py               # PyMuPDF PDF parser
│   │   │   ├── text_parser.py              # Markdown + plain text parser
│   │   │   ├── jira_parser.py              # JIRA REST API parser
│   │   │   ├── transcript_parser.py        # Meeting transcript parser
│   │   │   └── log_parser.py               # Jenkins log parser
│   │   ├── chunkers/
│   │   │   ├── base.py                     # Shared Chunk dataclass
│   │   │   ├── code_chunker.py             # Method/class → chunks
│   │   │   ├── row_chunker.py              # 1 row = 1 chunk
│   │   │   ├── ticket_chunker.py           # 1 ticket = 1 chunk
│   │   │   ├── recursive_chunker.py        # Recursive paragraph splitter
│   │   │   └── log_chunker.py              # Log block chunker
│   │   ├── cleaners/
│   │   │   ├── code_cleaner.py             # Code normalisation
│   │   │   ├── text_cleaner.py             # Prose + glossary expansion
│   │   │   └── log_cleaner.py              # ANSI + noise removal
│   │   ├── embedder.py                     # BGE-M3 dense + sparse embedder
│   │   └── orchestrator.py                 # Master ingestion controller
│   ├── retrieval/
│   │   ├── vector_store.py                 # Qdrant CRUD + hybrid search
│   │   ├── hybrid_search.py                # High-level search interface
│   │   └── reranker.py                     # bge-reranker-v2-m3
│   ├── chat/
│   │   ├── prompt_templates.py             # System prompt + context builder
│   │   ├── llm_client.py                   # Gemini + OpenAI client
│   │   └── qa_chain.py                     # Full RAG chain
│   ├── api/
│   │   ├── main.py                         # FastAPI app + lifespan
│   │   ├── models.py                       # Pydantic request/response models
│   │   └── routes/
│   │       ├── chat.py                     # POST /api/chat
│   │       ├── ingest.py                   # POST /api/ingest
│   │       └── health.py                   # GET /api/health
│   └── ui/
│       └── app.py                          # Streamlit chat UI
│
├── scripts/
│   ├── clone_repos.py                      # git clone Selenium + Playwright repos
│   ├── ingest_all.py                       # Full ingestion script
│   └── test_retrieval.py                   # Retrieval quality smoke test
│
├── docker/
│   ├── Dockerfile                          # Multi-stage: base / api / ui targets
│   ├── docker-compose.yml                  # Qdrant + API + UI + Nginx
│   └── nginx.conf                          # Reverse proxy config
│
├── tests/
│   ├── conftest.py                         # Shared pytest fixtures
│   ├── test_parsers.py                     # Parser unit tests
│   ├── test_chunkers.py                    # Chunker unit tests
│   ├── test_qa_chain.py                    # QA chain integration tests
│   └── test_retrieval.py                   # Retrieval + API model tests
│
├── requirements.txt                        # All Python dependencies
├── pytest.ini                              # Test configuration + markers
├── pyproject.toml                          # Build system + Ruff + coverage config
├── Makefile                                # Developer convenience commands
├── .env.example                            # Environment variable template
├── .env                                    # Actual secrets (git-ignored)
├── README.md                               # Full setup and usage guide
├── PHASE1_PLAN.md                          # This document
└── PHASE2_PLAN.md                          # Phase 2 technical plan
```

---

## Quick Start (Phase 1)

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env: add GEMINI_API_KEY (or OPENAI_API_KEY), JIRA credentials if available

# 2. Install dependencies
pip install -r requirements.txt

# 3. Clone the framework repos
python scripts/clone_repos.py

# 4. Start Qdrant
docker run -d --name qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# 5. Ingest all data sources
python scripts/ingest_all.py

# 6. Start the API server
python -m src.api.main

# 7. Start the chat UI (new terminal)
streamlit run src/ui/app.py
# → Open http://localhost:8501, password: qabuddy2026

# 8. Or run everything via Docker Compose
cd docker && docker compose up -d --build
# → Open http://your-server-ip
```

---

## Phase 1 Completion Checklist

- [x] Architecture decisions documented and justified
- [x] 10 data source folder structure created
- [x] Sample demo data in 3 key source folders (test cases, company docs, Jenkins logs, meeting transcripts)
- [x] Code parser (Java / JS/TS / Python)
- [x] CSV/XLSX test case parser
- [x] PDF parser (PyMuPDF, layout-aware)
- [x] Text/Markdown parser
- [x] JIRA parser (REST API + disk persistence)
- [x] Meeting transcript parser (speaker-aware)
- [x] Jenkins log parser (classified blocks)
- [x] Code cleaner
- [x] Text cleaner with QA glossary expansion
- [x] Log cleaner (ANSI + Maven noise removal)
- [x] Code chunker (method/class-level)
- [x] Row chunker (test case rows)
- [x] Ticket chunker (JIRA tickets)
- [x] Recursive chunker (prose with configurable profiles per source)
- [x] Log chunker (classified blocks)
- [x] Shared `Chunk` base dataclass
- [x] BGE-M3 embedder (dense + sparse, FlagEmbedding + sentence-transformers fallback)
- [x] Qdrant vector store (create collection, upsert, hybrid search, RRF)
- [x] Cross-encoder reranker (bge-reranker-v2-m3)
- [x] Hybrid search interface
- [x] QA chain (embed → search → rerank → generate)
- [x] LLM client (Gemini + OpenAI, multi-turn)
- [x] QA-focused prompt templates with citation enforcement
- [x] FastAPI backend (3 routes: chat, ingest, health)
- [x] Pydantic request/response models
- [x] Streamlit chat UI with auth, source filter, citation display
- [x] Docker Compose deployment (Qdrant + API + UI + Nginx)
- [x] Multi-stage Dockerfile
- [x] `scripts/clone_repos.py`
- [x] `scripts/ingest_all.py` (with `--sources`, `--recreate`, `--dry-run`)
- [x] `scripts/test_retrieval.py` (retrieval quality smoke test)
- [x] Unit tests: parsers, chunkers, QA chain, retrieval, API models, settings
- [x] `tests/conftest.py` with shared fixtures
- [x] `pytest.ini` with markers and test config
- [x] `pyproject.toml` with build system and dev tools
- [x] `Makefile` with developer convenience commands
- [x] `.env.example` with all configurable variables
- [x] `README.md` with full setup guide

---

*Phase 1 is complete. See [PHASE2_PLAN.md](./PHASE2_PLAN.md) for the hourly auto-ingestion and Figma integration roadmap.*
