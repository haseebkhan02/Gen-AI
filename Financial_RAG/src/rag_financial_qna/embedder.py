import os
import argparse
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def build_embeddings(input_dir: str, db_dir: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    os.makedirs(db_dir, exist_ok=True)

    model = SentenceTransformer(model_name)
    texts = []
    metadata = []

    # Read all processed files
    for fname in os.listdir(input_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(input_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            print(f"Processing {fname}, {len(chunks)} chunks")
            for chunk in chunks:
                if isinstance(chunk, dict) and "text" in chunk:
                    texts.append(chunk["text"])
                    metadata.append({"source": fname, "chunk_id": chunk.get("id")})
                else:
                    texts.append(str(chunk))
                    metadata.append({"source": fname})



    if not texts:
        print("No processed chunks found.")
        return

    # Encode embeddings
    embeddings = model.encode(texts, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save index + metadata
    faiss.write_index(index, os.path.join(db_dir, "index.faiss"))
    with open(os.path.join(db_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Stored {len(texts)} chunks in vectorstore: {db_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, help="Directory with processed filings")
    parser.add_argument("--db-dir", required=True, help="Directory to store FAISS index and metadata")
    args = parser.parse_args()

    build_embeddings(args.input_dir, args.db_dir)
