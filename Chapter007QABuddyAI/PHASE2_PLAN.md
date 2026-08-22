# QABuddy.ai — Phase 2 Plan: Auto-Ingestion & Figma Integration

> **Status:** Plan Only — Do Not Build Yet  
> **Triggered by:** Section 6 of [qabuddy-ai-build-prompt.md](./qabuddy-ai-build-prompt.md)

---

## Overview

Phase 2 adds two capabilities on top of the Phase 1 foundation:

1. **Hourly Auto-Ingestion** — detect and re-index new test cases, commits, documents every hour
2. **Figma Design Ingestion** — parse ER diagrams, wireframes, and user guides via the Figma API + Vision model

---

## Feature 1: Hourly Auto-Ingestion

### Problem

Phase 1 ingestion is a one-shot operation. Every time a new test case is added to `testdata.csv`, a commit is pushed to the Selenium/Playwright repos, or a new JIRA ticket is created, the data in Qdrant is stale until someone manually re-runs `python scripts/ingest_all.py`.

### Solution: Change-Detection + Incremental Re-indexing

Instead of re-ingesting everything every hour (expensive), we track what has changed and only re-index the new/modified content.

### Implementation Architecture

```
Every Hour (cron)
       │
       ▼
 ChangeDetector.scan()
       │
       ├── Git repos: git log --since="1 hour ago" → new commits
       ├── CSV/XLSX: file mtime vs. last_ingested_at metadata
       ├── PDF/MD docs: file mtime vs. last_ingested_at
       ├── JIRA: JQL with updatedDate >= -1h
       └── Jenkins logs: glob new .log files by mtime
       │
       ▼
 IngestDelta(changed_sources)
       │
       ▼
 Delete stale points → Re-embed → Re-index
       │
       ▼
 Update ingestion_state.json (timestamps per source)
```

### Files to Create

| File | Purpose |
|:--|:--|
| `src/ingestion/change_detector.py` | Scans each source for changes since last ingestion |
| `src/ingestion/ingestion_state.py` | Reads/writes `ingestion_state.json` — stores last ingestion timestamps |
| `scripts/auto_ingest.py` | Runs the delta ingestion loop, called by cron/scheduler |
| `docker/Dockerfile.scheduler` | Lightweight container running the auto-ingest script on a cron schedule |

### Change Detection Strategy Per Source

| Source | Change Signal | Mechanism |
|:--|:--|:--|
| Selenium/Playwright repos | New commits | `git log --since` |
| Test cases (CSV/XLSX) | File modified time | `os.path.getmtime` vs `last_ingested_at` |
| JIRA tickets | `updated` field | JQL: `updated >= -1h` |
| Company docs / PRDs / Transcripts | File modified time | `os.path.getmtime` |
| Jenkins logs | New log files | Glob new `.log` files since last run |
| Lucid chart exports | File modified time | `os.path.getmtime` |

### Deployment on DigitalOcean/VPS

Add a cron entry to the `qabuddy-api` container or a dedicated scheduler container:

```bash
# /etc/cron.d/qabuddy-autoingestion
0 * * * * root cd /app && python scripts/auto_ingest.py >> /var/log/qabuddy_ingestion.log 2>&1
```

Or use `APScheduler` inside the FastAPI app as a background task:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(run_delta_ingestion, "interval", hours=1, id="auto_ingest")
scheduler.start()
```

### State Management

`ingestion_state.json` tracks the last-ingested timestamp per source:

```json
{
  "selenium_repo": {
    "last_ingested_at": "2026-08-21T12:00:00Z",
    "last_commit_sha": "abc123def456",
    "chunks_indexed": 2847
  },
  "test_cases": {
    "last_ingested_at": "2026-08-21T12:00:00Z",
    "files_indexed": ["sample_testcases.csv"],
    "chunks_indexed": 5000
  },
  "jira_tickets": {
    "last_ingested_at": "2026-08-21T12:00:00Z",
    "tickets_indexed": 1243
  }
}
```

### Key Design Decisions

> [!IMPORTANT]
> **Incremental vs. Full Re-index**: For code repos, we only re-index files touched by new commits (using `git diff --name-only`). For JIRA, we use `updated >= -1h` JQL. For CSV files, if the file changed at all, we re-index the whole file (since rows may have been deleted or reordered).

> [!NOTE]
> **Deduplication**: Before upserting new chunks, we delete all existing chunks for the changed source file (by `source_file` metadata filter). This ensures stale chunks are replaced and prevents duplicates.

---

## Feature 2: Figma Design Ingestion

### Problem

Figma contains valuable product context: ER diagrams, user flow wireframes, and UX specifications. QA engineers need to be able to ask questions like:
- *"What does the checkout flow wireframe show?"*
- *"What are the database entities in the ER diagram?"*
- *"What is the intended UX for the onboarding flow?"*

### Solution: Figma API + Vision Model Captioning

Since Figma frames are visual, we use a two-step pipeline:
1. **Export** frames as PNG via the Figma REST API
2. **Caption** each frame using a Vision-capable LLM (Gemini Vision or GPT-4o-mini)
3. **Embed and index** the resulting text descriptions

### Implementation Architecture

```
Figma API
    │
    ├── GET /v1/files/:file_id/nodes?ids=...
    │       → Get list of named frames/pages
    │
    └── GET /v1/images/:file_id?ids=...&format=png
            → Download frame as PNG
                    │
                    ▼
            Vision LLM (Gemini 2.0 Flash or GPT-4o)
                "Describe this diagram..."
                    │
                    ▼
            ParsedFigmaFrame(caption, frame_name, frame_id)
                    │
                    ▼
            Embed caption → Index in Qdrant
```

### Files to Create

| File | Purpose |
|:--|:--|
| `src/ingestion/parsers/figma_parser.py` | Fetches Figma frames and captions them with Vision LLM |
| `data/06_figma_designs/README.md` | Instructions: add Figma file IDs to configure |
| `.env` additions | `FIGMA_API_TOKEN`, `FIGMA_FILE_IDS` |

### Figma Parser Implementation Plan

```python
class FigmaParser:
    def __init__(self, api_token: str, vision_llm: LLMClient):
        self.api_token = api_token
        self.vision_llm = vision_llm

    def parse_figma_file(self, file_id: str) -> List[ParsedFigmaFrame]:
        """Fetch all frames and generate text captions for each."""
        frames = self._get_frames(file_id)
        images = self._export_as_png(file_id, frame_ids=[f.id for f in frames])
        
        captions = []
        for frame, image_bytes in zip(frames, images):
            caption = self._caption_with_vision(frame.name, image_bytes)
            captions.append(ParsedFigmaFrame(
                content=caption,
                frame_id=frame.id,
                frame_name=frame.name,
                file_id=file_id,
                metadata={"source_type": "figma_designs", "frame_name": frame.name},
            ))
        return captions

    def _caption_with_vision(self, frame_name: str, image_bytes: bytes) -> str:
        """Send frame image to Vision LLM for captioning."""
        prompt = f"""You are analyzing a Figma design frame named '{frame_name}'.
Describe it in detail for a QA engineer, covering:
1. Layout and key UI components visible
2. User flows or interactions shown
3. Any data entities, relationships, or schemas visible (for ER diagrams)
4. Any labels, field names, or text visible in the design
Be specific and thorough. This description will be indexed in a QA knowledge base."""
        return self.vision_llm.generate_with_image(prompt, image_bytes)
```

### Configuration

```bash
# .env additions for Phase 2
FIGMA_API_TOKEN=your-figma-personal-access-token
FIGMA_FILE_IDS=file_id_1,file_id_2,file_id_3
FIGMA_INCLUDE_PAGES=wireframes,ER diagrams,user flows
```

### Chunking Strategy for Figma

| Item | Chunk Size | Overlap | Rationale |
|:--|:--|:--|:--|
| ER diagram captions | 800 tokens | 100 | Entities and relationships need full context |
| Wireframe captions | 600 tokens | 80 | One screen = one chunk, minimal overlap |
| User guide frames | 1000 tokens | 150 | Multi-step flows need more context |

---

## Phase 2 Deployment Impact

### New Environment Variables

```bash
# Auto-ingestion
AUTO_INGEST_ENABLED=true
AUTO_INGEST_INTERVAL_HOURS=1
INGESTION_STATE_PATH=/app/data/ingestion_state.json

# Figma
FIGMA_API_TOKEN=your-token
FIGMA_FILE_IDS=file1,file2
```

### New Requirements

```
# Phase 2 additions to requirements.txt
apscheduler>=3.10.0          # Background job scheduler
aiofiles>=23.2.0              # Async file I/O for change detector
httpx>=0.27.0                  # Async Figma API client (already in test deps)
Pillow>=10.3.0                 # Image handling for Figma frames
```

### Docker Changes

```yaml
# docker-compose.yml additions for Phase 2
qabuddy-scheduler:
  build:
    context: ..
    dockerfile: docker/Dockerfile
    target: api
  container_name: qabuddy-scheduler
  command: python scripts/auto_ingest.py --daemon
  depends_on:
    qdrant:
      condition: service_healthy
  env_file: ../.env
  volumes:
    - ../data:/app/data
  restart: unless-stopped
```

---

## Timeline Estimate

| Task | Effort |
|:--|:--|
| `ChangeDetector` + `IngestionState` | 1 day |
| `auto_ingest.py` script | 0.5 day |
| APScheduler integration in FastAPI | 0.5 day |
| `FigmaParser` + Vision LLM captioning | 2 days |
| Docker scheduler container | 0.5 day |
| Testing + validation | 1 day |
| **Total Phase 2 effort** | **~5.5 days** |

---

*Phase 2 will be built after Phase 1 is validated in production with real data.*
