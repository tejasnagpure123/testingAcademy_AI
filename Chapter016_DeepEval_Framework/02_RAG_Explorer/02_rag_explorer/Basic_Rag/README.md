# RAG Explorer

## Overview

The RAG (Retrieval-Augmented Generation) Explorer is a full-stack web application designed to demonstrate how an AI can read, index, and answer questions about a custom PDF document.

**The Problem:**
Large Language Models (LLMs) like ChatGPT are incredibly smart, but they don't know about *your* private company data (like your specific Product Requirement Documents). If you ask them a question about your private data, they will either hallucinate or say they don't know.

**The Solution (RAG):**
We built a pipeline that:
1. **Reads** your private PDF document.
2. **Chunks** it into smaller, bite-sized paragraphs.
3. **Embeds** those chunks (turns text into mathematical coordinates) using a local Ollama model (`nomic-embed-text`).
4. **Stores** them in a local Vector Database (ChromaDB).
5. When you ask a question, it **Retrieves** the most relevant chunks from the database based on mathematical similarity.
6. Finally, it sends both your question AND the relevant chunks to a powerful AI (Groq's Llama 3.3) so the AI can **Generate** a highly accurate answer based *only* on your private data!

## Features

- **End-to-End Pipeline Visualization:** The React UI lets you trigger the ingestion process and watch as it steps through reading, chunking, embedding, and storing.
- **Lightning Fast AI:** Uses Groq's insanely fast inference engine and Llama 3.3 70B for generating answers.
- **Local Data Privacy:** Text embedding and vector storage happen entirely locally on your machine using Ollama and ChromaDB.
- **Premium UI:** Features a modern, light-themed glassmorphism design for an excellent user experience.

## Getting Started

### Prerequisites
- Node.js (v18+)
- Python (with `chromadb` installed via pip)
- Ollama (with `nomic-embed-text` pulled)

### 1. Start the Database
Start your local ChromaDB server so the app has somewhere to store vectors:
```bash
python -m chromadb run --path ./chroma_data
```

### 2. Start the Backend
Navigate to the `backend` folder, install dependencies, and start the API server:
```bash
cd backend
npm install
node server.js
```

### 3. Start the Frontend
Navigate to the `frontend` folder, install dependencies, and start the React app:
```bash
cd frontend
npm install
npm run dev
```

### 4. Use the App
1. Open the UI in your browser (`http://localhost:5173`).
2. Click **Start Ingestion Pipeline** to process the PDF.
3. Once ingested, use the **Query & Retrieval** box to ask questions!
