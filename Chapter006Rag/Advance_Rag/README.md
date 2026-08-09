# Advanced RAG Explorer

## Overview
The Advanced RAG Explorer is an end-to-end teaching demo application built for The Testing Academy. It demonstrates how to scale a Basic RAG (Retrieval-Augmented Generation) application to handle a real-world corpus of 5,000 VWO test cases using advanced search and retrieval techniques.

## Architecture & Pipeline Logic

The system is built on a two-stage pipeline:

### 1. Ingestion Stage
- **Action**: Generates and embeds 5,000 realistic JIRA test cases into a vector database.
- **Logic**: 
  - A custom Python script (`generate_testcases.py`) programmatically generates 5,000 rows of test case data to avoid expensive LLM token limits.
  - The `ingest.py` script chunks this data and passes it through the **BAAI/bge-m3** embedding model.
  - Unlike basic RAG, `bge-m3` produces *both* **dense vectors** (for semantic meaning) and **sparse lexical weights** (for exact keyword matching).
  - These vectors, along with metadata payloads (tags, priorities, modules), are indexed natively into a local **Qdrant** Vector DB.

### 2. Retrieval & Chat Stage
- **Action**: Processes user queries, retrieves relevant test cases, re-ranks them, and generates an answer.
- **Logic**:
  - **Query Rewriting**: The user's query is sent to Groq to generate 3 alternative phrasings. This expands the search surface to catch synonyms.
  - **Hybrid Search**: We search the Qdrant database using the dense vectors of the rewritten queries to fetch a broad candidate list.
  - **Cross-Encoder Re-ranking**: We use the **BAAI/bge-reranker-v2-m3** model to evaluate the relevance of the `(Query, Chunk)` pairs. This step was custom-patched in this project to bypass deprecated tokenization methods (`prepare_for_model`) in modern `transformers` libraries, replacing it with native HF tokenization.
  - **Generation**: The top 4 re-ranked chunks are passed to **DeepSeek v4 Pro** via OpenRouter to generate a grounded, highly accurate final answer.

## UI Components
- Built with a Claude-inspired warm cream and coral theme using vanilla HTML, CSS, and JS.
- Features a **Two-Pane Layout**: The left pane tracks the live Server-Sent Events (SSE) of the RAG pipeline stages, while the right pane handles uploads, chunk exploration, and the chat interface.

## How to Run
1. Ensure your `.env` is populated with `GROQ_API_KEY` and `OPENROUTER_API_KEY`.
2. Activate the virtual environment: `.\.venv\Scripts\activate`
3. Run the application: `python app.py`
4. Visit `http://127.0.0.1:5050`
