# Chapter 06: RAG (Retrieval-Augmented Generation)

This chapter contains implementations of RAG applications, ranging from basic setups to advanced, production-ready pipelines.

## Projects in this Chapter

### 1. Basic RAG (`Basic_Rag`)
A standard RAG implementation demonstrating the core concepts of embedding documents and retrieving them using a vector database to augment LLM generation.

### 2. Advanced RAG Explorer (`Advance_Rag`)
A sophisticated, end-to-end RAG application built to handle a large corpus (5,000 VWO test cases).

**Key Advanced Techniques Used:**
- **Hybrid Retrieval**: Utilizes `BAAI/bge-m3` to extract both dense embeddings and sparse lexical weights, improving semantic and exact-keyword match accuracy.
- **Advanced Vector DB**: Uses **Qdrant** natively to handle multi-vector hybrid searches and metadata filtering.
- **Query Rewriting**: Leverages Groq to generate multiple query variations before retrieval to maximize search surface area.
- **Cross-Encoder Re-ranking**: Employs `BAAI/bge-reranker-v2-m3` to strictly evaluate and re-rank the retrieved candidates before passing them to the final LLM. 
  - *Note:* During implementation, the `FlagEmbedding` library was manually patched to natively support the latest `transformers` API (v5+), resolving deprecation errors related to `prepare_for_model` on Python 3.14.
- **Interactive UI**: A vanilla JS/HTML frontend with Server-Sent Events (SSE) to track the pipeline stages in real-time.

**To run the Advanced RAG:**
Navigate to `Advance_Rag`, activate the `.venv`, add your API keys to the `.env` file, and run `python app.py`.

### Other Folders
- `LangFlow`
- `n8n_BASIC_RAG`
