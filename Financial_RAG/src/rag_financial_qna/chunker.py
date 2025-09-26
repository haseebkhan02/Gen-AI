from langchain.schema import Document

def chunk_text(text, chunk_size=1000, overlap=100, metadata=None):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk_content = text[start:end]
        chunks.append(Document(page_content=chunk_content, metadata=metadata or {}))
        start += chunk_size - overlap
    return chunks
