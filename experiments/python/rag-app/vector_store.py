"""
Vector store facade that wraps Pinecone interactions.

Provides a `VectorStore` class implementing a small repository API.
This makes it easy to swap backends or add caching later.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import uuid
import logging

from config import get_default_config
from embedder import get_embedder


@dataclass
class VectorStore:
    """Vector store wrapper around Pinecone index.

    Usage:
        store = VectorStore()
        store.add_document(text, metadata={})
        matches = store.search_similar(query, top_k=5)
    """

    config_name: str = "default"
    embedder_name: str = "gemini"

    def __post_init__(self):
        self.config = get_default_config()
        self.index = self.config.index
        self.embedder = get_embedder(self.embedder_name)
        self.logger = logging.getLogger("VectorStore")

    def add_document(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a document with an embedding and return its id."""
        vector = self.embedder.embed([text])[0]
        doc_id = str(uuid.uuid4())
        try:
            self.index.upsert(vectors=[{"id": doc_id, "values": vector, "metadata": metadata or {"text": text}}])
            self.logger.info("Document added %s", doc_id)
        except Exception as e:
            self.logger.exception("Failed to add document: %s", e)
            raise
        return doc_id

    def search_similar(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Return the top-k most similar documents (list of match dicts).

        The returned format follows the previous code (list of matches with metadata).
        """
        query_vector = self.embedder.embed([query])[0]
        try:
            results = self.index.query(vector=query_vector, top_k=top_k, include_metadata=True)
            matches = results.get("matches", [])
        except Exception as e:
            self.logger.exception("Search failed: %s", e)
            matches = []
        return matches


# module-level default store for quick usage
_DEFAULT_STORE: Optional[VectorStore] = None


def get_default_store() -> VectorStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = VectorStore()
    return _DEFAULT_STORE


def add_document(text: str, metadata: dict = None) -> str:
    return get_default_store().add_document(text, metadata)


def search_similar(query: str, top_k: int = 3):
    return get_default_store().search_similar(query, top_k)
