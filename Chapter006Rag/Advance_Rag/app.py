from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import shutil
import json
import asyncio
from qdrant_client import QdrantClient
from FlagEmbedding import BGEM3FlagModel, FlagReranker
from groq import Groq
import openai

app = FastAPI(title="Advance RAG Explorer")

# Check if static dir exists
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Models placeholder - loaded lazily to save startup time
bge_m3_model = None
reranker_model = None
qdrant_client = None

def get_qdrant_client():
    global qdrant_client
    if not qdrant_client:
        qdrant_url = os.environ.get("QDRANT_URL")
        if qdrant_url:
            qdrant_client = QdrantClient(url=qdrant_url)
        else:
            qdrant_client = QdrantClient(path="qdrant_data")
    return qdrant_client

def load_models():
    global bge_m3_model, reranker_model
    if bge_m3_model is None:
        print("Loading BGEM3FlagModel...")
        bge_m3_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    if reranker_model is None:
        print("Loading BAAI/bge-reranker-v2-m3...")
        reranker_model = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/rag_architecture_explainer.html", response_class=HTMLResponse)
async def read_explainer():
    with open("rag_architecture_explainer.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = os.path.join("uploads", file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "message": "File uploaded successfully"}

@app.get("/ingest")
async def ingest(filename: str):
    async def event_generator():
        yield f"data: {json.dumps({'message': 'Starting ingestion process...', 'status': 'running'})}\n\n"
        
        file_path = os.path.join("uploads", filename)
        if not os.path.exists(file_path):
            yield f"data: {json.dumps({'message': 'File not found.', 'status': 'error'})}\n\n"
            return
            
        yield f"data: {json.dumps({'message': 'Loading Models (this may take a minute on first run)...', 'status': 'running'})}\n\n"
        # We use asyncio.to_thread for blocking operations
        await asyncio.to_thread(load_models)
        
        yield f"data: {json.dumps({'message': 'Running CLI ingest logic in background...', 'status': 'running'})}\n\n"
        
        # Simulating running the ingest.py logic (Since we built ingest.py as a CLI, we can just call its function or subprocess)
        import subprocess
        process = subprocess.Popen(
            ["python", "-u", "ingest.py", file_path, "--text-cols", "title,steps,expected,tags", "--meta-cols", "id,jira_id,priority,module"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        for line in process.stdout:
            yield f"data: {json.dumps({'message': line.strip(), 'status': 'running'})}\n\n"
            await asyncio.sleep(0.1)
            
        process.wait()
        if process.returncode == 0:
            yield f"data: {json.dumps({'message': 'Ingestion Complete!', 'status': 'complete'})}\n\n"
        else:
            yield f"data: {json.dumps({'message': 'Ingestion Failed.', 'status': 'error'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/chunks")
async def get_chunks():
    client = get_qdrant_client()
    try:
        # Get first 50 chunks for the explorer
        results = client.scroll(
            collection_name="vwo_test_cases",
            limit=50,
            with_payload=True,
            with_vectors=False
        )
        chunks = [{"id": str(p.id), "payload": p.payload} for p in results[0]]
        return {"chunks": chunks}
    except Exception as e:
        return {"chunks": [], "error": str(e)}

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat(request: ChatRequest):
    async def generate():
        try:
            yield f"data: {json.dumps({'stage': 'query', 'statusText': 'Query rewriting via Groq...', 'text': ''})}\n\n"
            await asyncio.sleep(0.5)
            
            # 1. Query Rewrite (Mocked here if no API Key)
            groq_key = os.environ.get("GROQ_API_KEY")
            rewrites = [request.query]
            if groq_key:
                try:
                    groq_client = Groq(api_key=groq_key)
                    completion = groq_client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "user", "content": f"Rewrite this query in 3 different ways to improve retrieval: {request.query}\nOutput only the rewrites, one per line."}],
                        temperature=0.3,
                        max_tokens=100
                    )
                    rewrites.extend([r.strip() for r in completion.choices[0].message.content.split('\n') if r.strip()])
                except Exception as e:
                    print(f"Groq rewrite failed: {e}")
            
            yield f"data: {json.dumps({'stage': 'search', 'statusText': 'Hybrid Search (Dense + Sparse)...', 'text': f'Rewrites generated: {len(rewrites)}\n'})}\n\n"
            await asyncio.to_thread(load_models)
            
            client = get_qdrant_client()
            all_results = []
            
            for q in rewrites[:3]: # limit to 3 rewrites max
                embeddings = bge_m3_model.encode([q], return_dense=True, return_sparse=True)
                dense_vec = embeddings['dense_vecs'][0].tolist()
                
                lex_weights = embeddings['lexical_weights'][0]
                indices = list(lex_weights.keys())
                values = list(lex_weights.values())
                
                # We would typically do a Reciprocal Rank Fusion of Sparse and Dense searches.
                # For simplicity here, we do a dense search to grab candidates.
                try:
                    res = client.query_points(
                        collection_name="vwo_test_cases",
                        query=dense_vec,
                        using="",
                        limit=10,
                        with_payload=True
                    )
                    all_results.extend(res.points)
                except Exception as e:
                    yield f"data: {json.dumps({'stage': 'search', 'statusText': 'Error in search', 'text': str(e)})}\n\n"
                    return
            
            # Deduplicate by ID
            unique_results = {r.id: r for r in all_results}.values()
            candidates = list(unique_results)
            
            yield f"data: {json.dumps({'stage': 'rerank', 'statusText': 'Cross-Encoder Re-ranking...', 'text': f'Found {len(candidates)} candidates. Re-ranking...\n'})}\n\n"
            
            pairs = []
            for c in candidates:
                # BGE Reranker expects pairs of (query, document)
                pairs.append([request.query, c.payload.get('text', '')])
                
            scores = reranker_model.compute_score(pairs)
            
            # Associate scores and sort by rerank score descending
            scored_candidates = []
            for i, c in enumerate(candidates):
                scored_candidates.append((scores[i], c))
                
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            top_k = [x[1] for x in scored_candidates[:4]] # TOP_K_RERANK = 4
            
            context = "\n\n".join([f"[Chunk {i+1}]: {c.payload.get('text', '')}" for i, c in enumerate(top_k)])
            
            yield f"data: {json.dumps({'stage': 'generate', 'statusText': 'Generating grounded answer...', 'text': 'Generating answer via OpenRouter...\n\n'})}\n\n"
            
            system_prompt = "You are a QA testing assistant. Answer the user's question based on the provided test case context. If they ask to generate a new test case, use the context as templates."
            
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if not openrouter_key:
                yield f"data: {json.dumps({'stage': 'generate', 'statusText': 'Complete', 'text': f'**MOCK LLM OUTPUT (No OpenRouter Key)**\n\nContext used:\n{context}'})}\n\n"
                return
                
            # Call OpenRouter (DeepSeek)
            or_client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key,
            )
            
            stream = or_client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {request.query}"}
                ],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'stage': 'generate', 'statusText': 'Generating...', 'text': chunk.choices[0].delta.content})}\n\n"

            yield f"data: {json.dumps({'stage': 'generate', 'statusText': 'Complete', 'text': '\n'})}\n\n"

        except Exception as e:
             yield f"data: {json.dumps({'stage': 'error', 'statusText': 'Failed', 'text': f'Error: {str(e)}'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    uvicorn.run(app, host="127.0.0.1", port=port)
