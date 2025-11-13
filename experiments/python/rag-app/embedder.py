"""
embedder.py

Provides an embedding abstraction with multiple backend implementations.

Design patterns used:
- Strategy: different embedding backends can be swapped at runtime.
- Factory (simple): helper to pick an embedder by name.
"""
from typing import List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from config import get_default_config


class Embedder(ABC):
    """Embedding backend interface."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for a list of texts."""


@dataclass
class GeminiEmbedder(Embedder):
    """Gemini embeddings via configured genai client."""

    model: str = "models/embedding-001"
    config = get_default_config()

    def embed(self, texts: List[str]) -> List[List[float]]:
        # genai client expects a single string or list depending on API.
        # Keep this minimal and tolerant of single-string calls.
        if not isinstance(texts, list):
            texts = [texts]
        client = self.config.genai
        # The exact API can vary; this mirrors earlier code's embed_content call.
        response = client.embed_content(model=self.model, content=texts)
        # response may be a mapping; try to extract 'embedding' or 'embeddings'
        if isinstance(response, dict) and "embedding" in response:
            return [response["embedding"]]
        return response.get("embeddings") or response.get("results") or []


class MockEmbedder(Embedder):
    """Simple deterministic mock embedder useful for tests or offline runs."""

    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for t in texts:
            # simple hash-based pseudo-embedding (not for production)
            v = [float((ord(c) % 97) / 97.0) for c in (t[:64] or "_")]
            embeddings.append(v)
        return embeddings


def get_embedder(name: str = "gemini") -> Embedder:
    name = (name or "").lower()
    if name == "mock":
        return MockEmbedder()
    # default
    return GeminiEmbedder()


def get_text_embedding(text: str, embedder_name: str = "gemini"):
    """Convenience wrapper for single-text embedding."""
    e = get_embedder(embedder_name)
    result = e.embed([text])
    return result[0] if result else []
