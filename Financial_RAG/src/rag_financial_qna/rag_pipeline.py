import json
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline
from langchain.docstore.document import Document

def build_qa_chain(vectorstore):
    hf_pipeline = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        tokenizer="google/flan-t5-base",
        max_length=2048,
        truncation=True
    )

    llm = HuggingFacePipeline(pipeline=hf_pipeline)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

class SimpleAgent:
    def __init__(self, vectorstore):
        self.qa_chain = build_qa_chain(vectorstore)

    def needs_decompose(self, query):
        # optional: decide if you want to break down query into sub-queries
        return False

    def decompose(self, query):
        return [query]

    def retrieve_for_subquery(self, subquery, k=3):
        retrieved_docs = self.qa_chain.retriever.get_relevant_documents(
            subquery,
            allow_retriever_deprecation=True
        )
        return retrieved_docs[:k]



    def synthesize(self, query, retrieved):
        """
        Returns a JSON structure like:
        {
            "query": str,
            "answer": str,
            "reasoning": str,
            "sub_queries": [...],
            "sources": [{"company": ..., "year": ..., "excerpt": ..., "page": ...}]
        }
        """
        # For now, take top 3 retrieved documents as sources
        sources = []
        for doc in retrieved.get(query, []):
            metadata = doc.metadata
            sources.append({
                "file": metadata.get("file", ""),
                "chunk_id": metadata.get("chunk_id", ""),
                "excerpt": doc.page_content[:300]  # first 300 chars
            })

        # Get answer from LLM
        answer = self.qa_chain.invoke(query)

        # Build JSON
        output = {
            "query": query,
            "answer": answer.get("result") if isinstance(answer, dict) else str(answer),
            "reasoning": f"Retrieved {len(sources)} relevant document chunks from vectorstore",
            "sub_queries": [query],
            "sources": sources
        }
        return json.dumps(output, indent=2)
