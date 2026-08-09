import argparse
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from FlagEmbedding import BGEM3FlagModel
import uuid
import os
import time

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
INGEST_BATCH = 16

def create_chunks(text, max_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_size
        chunks.append(text[start:end])
        start += max_size - overlap
    return chunks

def ingest(csv_path, text_cols, meta_cols, qdrant_url=None):
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from {csv_path}")

    print("Loading BGEM3FlagModel (dense + sparse)...")
    # Setting use_fp16=True can save memory, as requested in Troubleshooting
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True) 

    if qdrant_url:
        client = QdrantClient(url=qdrant_url)
    else:
        # local embedded
        os.makedirs("qdrant_data", exist_ok=True)
        client = QdrantClient(path="qdrant_data")

    collection_name = "vwo_test_cases"
    
    # Check if collection exists, if not create
    collections = client.get_collections().collections
    if collection_name not in [c.name for c in collections]:
        print(f"Creating collection {collection_name}...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            # Note: Qdrant supports sparse vectors separately via sparse_vectors_config, 
            # but for simplicity and bge-m3 compatibility, if we do hybrid search natively in Qdrant,
            # we need to set up sparse vectors. Let's do that.
            sparse_vectors_config={
                "sparse": {} # 'sparse' is the name of the sparse vector
            }
        )

    points = []
    total_chunks = 0
    
    print("Processing and chunking rows...")
    for index, row in df.iterrows():
        # Combine text cols
        text_content = " ".join([f"{col}: {row[col]}" for col in text_cols if pd.notna(row[col])])
        
        # Meta cols
        payload = {col: row[col] for col in meta_cols if pd.notna(row[col])}
        
        chunks = create_chunks(text_content)
        
        for chunk in chunks:
            payload_copy = payload.copy()
            payload_copy["text"] = chunk
            points.append(payload_copy)
            total_chunks += 1

    print(f"Total chunks created: {total_chunks}")
    
    print("Embedding and indexing batches...")
    for i in range(0, len(points), INGEST_BATCH):
        batch = points[i:i + INGEST_BATCH]
        texts = [p["text"] for p in batch]
        
        # Get embeddings
        embeddings = model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False)
        dense_vecs = embeddings['dense_vecs']
        lexical_weights = embeddings['lexical_weights'] # List of dicts {token_id: weight}
        
        qdrant_points = []
        for j, text in enumerate(texts):
            point_id = str(uuid.uuid4())
            dense = dense_vecs[j].tolist()
            
            # format lexical weights for qdrant
            indices = list(lexical_weights[j].keys())
            values = list(lexical_weights[j].values())
            
            # Create PointStruct
            qdrant_points.append(PointStruct(
                id=point_id,
                payload=batch[j],
                vector={
                    "": dense, # default dense vector
                    "sparse": {"indices": indices, "values": values}
                }
            ))
            
        client.upsert(
            collection_name=collection_name,
            points=qdrant_points
        )
        print(f"Ingested batch {i // INGEST_BATCH + 1} / {(len(points) + INGEST_BATCH - 1) // INGEST_BATCH}")

    print("Ingestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest CSV to Qdrant")
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("--text-cols", required=True, help="Comma-separated list of text columns")
    parser.add_argument("--meta-cols", required=True, help="Comma-separated list of metadata columns")
    args = parser.parse_args()
    
    text_cols = [c.strip() for c in args.text_cols.split(",")]
    meta_cols = [c.strip() for c in args.meta_cols.split(",")]
    
    qdrant_url = os.environ.get("QDRANT_URL")
    
    start_time = time.time()
    ingest(args.csv_path, text_cols, meta_cols, qdrant_url)
    print(f"Time taken: {time.time() - start_time:.2f} seconds")
