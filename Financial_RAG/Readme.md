# ===== README.md =====
# Short README (copy to README.md)

"""
Financial RAG Q&A with Agent Capabilities
=========================================

A focused Retrieval-Augmented Generation (RAG) system plus a simple agent that
answers financial queries about Google (GOOGL), Microsoft (MSFT), and NVIDIA
(NVDA) using their 10-K filings (2022-2024).

Features
- Optional SEC downloader for 10-K filings (scraper)
- Text extraction from PDFs/HTML
- Semantic chunking
- Embeddings via sentence-transformers
- Vector search using FAISS (in-memory)
- Simple rule-based agent for query decomposition + multi-step retrieval
- JSON output with sources

Run
1. pip install -r requirements.txt
2. Place 9 filings in data/raw/ (or run downloader)
3. python main.py --build
4. python main.py --query "Which company had the highest operating margin in 2023?"

Design decisions (brief)
- Embeddings: sentence-transformers/all-MiniLM-L6-v2 (fast, good quality)
- Chunking: sliding window by token approx (using simple word-based heuristics)
- Vector store: FAISS in-memory for simplicity
- Agent: function-based decomposition with patterns for comparative queries

"""
