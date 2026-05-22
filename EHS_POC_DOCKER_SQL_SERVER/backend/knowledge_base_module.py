"""
Knowledge Base Module - EHS Policy RAG
Uses ChromaDB (in-memory/persistent) + sentence-transformers for embeddings.
Supports context-aware question answering over EHS policy documents.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EHSKnowledgeBase:
    """
    RAG system over EHS policy documents.
    Uses ChromaDB with local sentence-transformer embeddings (no API needed).
    Model: all-MiniLM-L6-v2 (~22MB, very fast on CPU)
    """

    COLLECTION_NAME = "ehs_policies"
    BASE_DIR = Path(__file__).resolve().parent.parent

    def __init__(
        self,
        persist_dir: str = str(BASE_DIR / "data" / "chroma_db"),
        policies_path: str = str(BASE_DIR / "knowledge_base" / "ehs_policies.json")
    ):
        self.persist_dir = persist_dir
        self.policies_path = policies_path
        self.client = None
        self.collection = None
        self.embedding_fn = None
        self._initialized = False
        self._setup()

    def _setup(self):
        """Initialize ChromaDB and load policies."""
        try:
            import os
            os.environ["ANONYMIZED_TELEMETRY"] = "False"
            import chromadb
            from chromadb.utils import embedding_functions

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

            # Use persistent client so data survives restarts
            self.client = chromadb.PersistentClient(path=self.persist_dir)

            # Use sentence-transformers for local embeddings (no API key needed)
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.COLLECTION_NAME, embedding_function=self.embedding_fn)
                existing_count = self.collection.count()
                logger.info(f"✅ Loaded existing KB with {existing_count} policies")
                if existing_count == 0:
                    logger.warning("Empty KB detected. Re-ingesting policies...")
                    self._ingest_policies()

                    # verify ingestion worked
                    new_count = self.collection.count()
                    logger.info(f"KB chunk count after ingest: {new_count}")
                    
            except Exception:
                self.collection = self.client.create_collection(name=self.COLLECTION_NAME, embedding_function=self.embedding_fn, metadata={"hnsw:space": "cosine"})
                self._ingest_policies()
            self._initialized = True

        except ImportError as e:
            logger.warning(f"⚠️ ChromaDB/sentence-transformers not installed: {e}. KB disabled.")
        except Exception as e:
            logger.error(f"❌ KB setup failed: {e}")

    def _ingest_policies(self):
        """Load policies from JSON and index into ChromaDB."""
        logger.info("🔥 Starting policy ingestion...")
        policies_file = Path(self.policies_path)
        if not policies_file.exists():
            logger.warning(f"Policies file not found: {self.policies_path}")
            return

        with open(policies_file) as f:
            policies = json.load(f)
        documents = []
        metadatas = []
        ids = []
        for policy in policies:
            # Create rich document text combining title + content
            logger.info(f"Indexing policy: {policy['id']}")
            doc_text = f"Policy: {policy['title']}\nCategory: {policy['category']}\n\nContent: {policy['content']}"

            # Store corrective actions as separate searchable chunks
            for i, action in enumerate(policy.get("corrective_actions", [])):
                action_text = f"Corrective action for {policy['title']}: {action}"
                documents.append(action_text)
                metadatas.append({
                    "policy_id": policy["id"],
                    "title": policy["title"],
                    "category": policy["category"],
                    "severity": policy["severity_if_violated"],
                    "chunk_type": "corrective_action"
                })
                ids.append(f"{policy['id']}_action_{i}")

            # Main policy content
            documents.append(doc_text)
            metadatas.append({
                "policy_id": policy["id"],
                "title": policy["title"],
                "category": policy["category"],
                "severity": policy["severity_if_violated"],
                "chunk_type": "policy_content"
            })
            ids.append(policy["id"])

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"✅ Indexed {len(policies)} policies ({len(documents)} chunks) into ChromaDB")

    def query(self, question: str, n_results: int = 4, category_filter: Optional[str] = None) -> dict:
        """
        Semantic search over EHS policies.
        Returns relevant policy chunks with metadata.
        """
        if not self._initialized or self.collection is None:
            return self._fallback_query(question)

        try:
            where = None
            if category_filter:
                where = {"category": {"$eq": category_filter}}

            collection_count = self.collection.count()
            if collection_count <= 0:
                logger.warning("Knowledge base is empty")
                return {
                    "query": question,
                    "results": [],
                    "total_results": 0,
                    "mode": "empty_kb"
                }

            safe_n_results = max(1, min(n_results, collection_count))

            results = self.collection.query(
                query_texts=[question],
                n_results=safe_n_results,
                where=where
            )

            hits = []
            for i, (doc, meta, dist) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                hits.append({
                    "rank": i + 1,
                    "policy_id": meta.get("policy_id"),
                    "title": meta.get("title"),
                    "category": meta.get("category"),
                    "severity": meta.get("severity"),
                    "chunk_type": meta.get("chunk_type"),
                    "content": doc,
                    "relevance_score": round(1 - dist, 4)  # cosine similarity
                })

            return {
                "query": question,
                "results": hits,
                "total_results": len(hits)
            }

        except Exception as e:
            logger.error(f"KB query error: {e}")
            return self._fallback_query(question)

    def get_policy_by_category(self, category: str) -> list[dict]:
        """Get all policies matching a category."""
        if not self._initialized:
            return []
        try:
            results = self.collection.get(
                where={"category": {"$eq": category}},
                include=["documents", "metadatas"]
            )
            return [
                {"content": doc, "metadata": meta}
                for doc, meta in zip(results["documents"], results["metadatas"])
                if meta.get("chunk_type") == "policy_content"
            ]
        except Exception as e:
            logger.error(f"Category query error: {e}")
            return []

    def get_all_categories(self) -> list[str]:
        """Return all unique policy categories."""
        try:
            policies_file = Path(self.policies_path)
            if policies_file.exists():
                with open(policies_file) as f:
                    policies = json.load(f)
                return list(set(p["category"] for p in policies))
        except Exception:
            pass
        # returning some dedfault policies list 
        return ["PPE", "Fire Safety", "Chemical Safety", "Electrical Safety", "Fall Protection",
                "Ergonomics", "Material Handling", "Housekeeping", "Incident Management", "Confined Space"]

    def _fallback_query(self, question: str) -> dict:
        """Simple keyword fallback when vector DB unavailable."""
        try:
            policies_file = Path(self.policies_path)
            if not policies_file.exists():
                return {"query": question, "results": [], "total_results": 0, "mode": "fallback_empty"}

            with open(policies_file) as f:
                policies = json.load(f)

            q_lower = question.lower()
            hits = []
            for policy in policies:
                score = 0
                for word in q_lower.split():
                    if len(word) > 3:
                        if word in policy["content"].lower():
                            score += 1
                        if word in policy["title"].lower():
                            score += 2
                        if word in policy["category"].lower():
                            score += 3
                if score > 0:
                    hits.append({
                        "policy_id": policy["id"],
                        "title": policy["title"],
                        "category": policy["category"],
                        "severity": policy["severity_if_violated"],
                        "chunk_type": "policy_content",
                        "content": policy["content"][:500] + "...",
                        "relevance_score": min(score / 10, 1.0)
                    })

            hits.sort(key=lambda x: x["relevance_score"], reverse=True)
            return {"query": question, "results": hits[:4], "total_results": len(hits), "mode": "keyword_fallback"}
        except Exception as e:
            return {"query": question, "results": [], "total_results": 0, "error": str(e)}

    def get_stats(self) -> dict:
        """Return KB statistics."""
        stats = {"initialized": self._initialized}
        if self._initialized and self.collection:
            stats["total_chunks"] = self.collection.count()
        try:
            with open(self.policies_path) as f:
                policies = json.load(f)
            stats["total_policies"] = len(policies)
            stats["categories"] = list(set(p["category"] for p in policies))
        except Exception:
            pass
        return stats
