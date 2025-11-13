"""
Retriever module providing a small retrieval pipeline class.

Design notes:
- Retriever is a simple coordinator that queries the vector store,
  applies light post-processing and returns a single combined context
  or structured results depending on the need.
"""
from typing import List, Dict
from vector_store import get_default_store


class Retriever:
    """Simple retriever that returns relevant context for a query."""

    def __init__(self, store=None, top_k: int = 3):
        self.store = store or get_default_store()
        self.top_k = top_k

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """Return raw match dicts from the vector store.

        Each match typically contains `id`, `score`, and `metadata`.
        """
        k = top_k or self.top_k
        return self.store.search_similar(query, top_k=k)

    def retrieve_context(self, query: str, top_k: int = None) -> str:
        """Return combined text context suitable for prompting an LLM."""
        matches = self.retrieve(query, top_k=top_k)
        parts = []
        for m in matches:
            meta = m.get("metadata") or {}
            txt = meta.get("text") or meta.get("content") or ""
            if txt:
                parts.append(txt)
        return "\n".join(parts)


# convenience function for quick scripts
def retrieve_context(query: str, top_k: int = 3) -> str:
    return Retriever().retrieve_context(query, top_k=top_k)
