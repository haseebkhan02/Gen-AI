from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import os

# Choose embedding model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load or create FAISS index
if os.path.exists("faiss_index"):
    db = FAISS.load_local("faiss_index", embeddings)
else:
    documents = []
    for file in os.listdir("data/raw"):
        if file.endswith(".txt"):
            with open(f"data/raw/{file}", "r", encoding="utf-8") as f:
                documents.append(f.read())
    # Wrap text in Document objects
    documents_objs = [Document(page_content=text) for text in documents]
    db = FAISS.from_documents(documents_objs, embeddings)
    db.save_local("faiss_index")
