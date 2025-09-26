import os
import json
from bs4 import BeautifulSoup
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from rag_financial_qna.rag_pipeline import SimpleAgent
from rag_financial_qna.filing_processor import process_filings
from langchain_huggingface import HuggingFaceEmbeddings

input_dir = "data/raw"
output_dir = "data/processed"
vectorstore_dir = "data/vectorstore"
faiss_index_path = os.path.join(vectorstore_dir, "index.faiss")
faiss_pkl_path = os.path.join(vectorstore_dir, "index.pkl")

# --- Step 1: Process filings to extract text ---
if not os.listdir(output_dir):
    print("[INFO] Processing raw filings...")
    process_filings(input_dir, output_dir)
else:
    print("[INFO] Processed filings found, skipping extraction.")

"""# --- Step 2: Load processed filings and clean HTML ---
documents = []
for fname in os.listdir(output_dir):
    if fname.endswith(".json"):
        file_path = os.path.join(output_dir, fname)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                raw_text = " ".join(chunk["text"] for chunk in data if "text" in chunk)
                clean_text_content = BeautifulSoup(raw_text, "html.parser").get_text(separator=" ")
                documents.append(Document(page_content=clean_text_content))
        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")

if not documents:
    raise ValueError(f"No documents found in {output_dir}. Please check processed files.")"""

# --- Step 2: Load processed filings and clean HTML ---
documents = []
for fname in os.listdir(output_dir):
    if fname.endswith(".json"):
        file_path = os.path.join(output_dir, fname)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for i, chunk in enumerate(data):
                    if "text" in chunk:
                        text = chunk["text"]
                        # Remove XBRL page_content prefix and trailing quotes
                        if text.startswith("page_content="):
                            text = text[len("page_content="):]
                            text = text.strip("'\"")
                        # Remove extra newlines/tabs
                        text = " ".join(text.split())
                        documents.append(Document(
                            page_content=text,
                            metadata={
                                "file": fname,
                                "chunk_id": f"{fname}::{i}"
                            }
                        ))

        except Exception as e:
            print(f"[ERROR] Failed to process {file_path}: {e}")


# --- Step 3: Split documents into chunks ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100
)
chunks = text_splitter.split_documents(documents)

# --- Step 4: Create or load embeddings and vectorstore ---
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
    print("[INFO] Loading FAISS vectorstore from disk...")
    vectorstore = FAISS.load_local(vectorstore_dir, embedding_model, allow_dangerous_deserialization=True)
else:
    print("[INFO] Creating FAISS vectorstore...")
    vectorstore = FAISS.from_texts([chunk.page_content for chunk in chunks], embedding_model)
    vectorstore.save_local(vectorstore_dir)

# --- Step 5: Initialize RAG agent ---
agent = SimpleAgent(vectorstore)

# --- Step 6: Ask questions ---
print("\nRAG QnA system ready! Type your question (or 'exit' to quit).")
while True:
    query = input("\nEnter your question: ")
    if query.lower() == "exit":
        break

    # Use SimpleAgent's synthesize() to get JSON output
    subqueries = agent.decompose(query) if agent.needs_decompose(query) else [query]
    retrieved = {s: agent.retrieve_for_subquery(s, 3) for s in subqueries}
    response_json = agent.synthesize(query, retrieved)

    # Print formatted JSON
    print("\nResponse:\n", response_json)
