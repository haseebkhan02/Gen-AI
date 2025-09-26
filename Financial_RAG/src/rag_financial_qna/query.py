import argparse, glob, os
from .preprocess import extract_text, chunk_text
from .rag_pipeline import SimpleAgent
from .utils import save_json
from langchain_huggingface import HuggingFaceEmbeddings
#from langchain.vectorstores import FAISS
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

def build_index(data_dir="data/processed", index_dir="data/vectorstore"):
    files = glob.glob(os.path.join(data_dir, '*'))
    docs = []
    for f in files:
        text = extract_text(f)
        chunks = chunk_text(text)
        for i, c in enumerate(chunks):
            # Extract company/year from filename (your downloaded HTMLs)
            basename = os.path.basename(f)  # e.g., goog-20211231.htm
            parts = basename.split('-')      # ["goog", "20211231.htm"]
            company = parts[0].upper()
            year = parts[1][:4] if len(parts) > 1 else ""

            docs.append(Document(
                page_content=c['text'],
                metadata={
                    'file': f,
                    'chunk_id': f"{os.path.basename(f)}::{i}",
                    'company': company,
                    'year': year,
                    'page': i+1  # optional page number
                }
            ))


    # create embeddings and FAISS index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = FAISS.from_documents(docs, embeddings)
    os.makedirs(index_dir, exist_ok=True)
    store.save_local(index_dir)

    # save metadata
    save_json(os.path.join(index_dir, 'metadatas.json'), [d.metadata for d in docs])
    return store

def load_vectorstore(index_dir="data/vectorstore"):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.load_local(index_dir, embeddings,allow_dangerous_deserialization=True)

def run_query(db_dir, query: str):
    store = load_vectorstore(db_dir)
    agent = SimpleAgent(store)
    subqs = agent.decompose(query) if agent.needs_decompose(query) else [query]
    retrieved = {s: agent.retrieve_for_subquery(s, 3) for s in subqs}
    result = agent.synthesize(query, retrieved)
    print(result)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--query", type=str)
    parser.add_argument("--db-dir", type=str, default="data/vectorstore")
    parser.add_argument("--data-dir", type=str, default="data/processed")
    args = parser.parse_args()

    if args.build:
        build_index(args.data_dir, args.db_dir)

    if args.query:
        run_query(args.db_dir, args.query)
