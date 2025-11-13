"""
RAG chain coordinator.

Provides a `RAGChain` class that encapsulates retrieval, prompt
construction, and invocation of a generative model.

This file uses the configured genai client from `config`.
"""
from dataclasses import dataclass
from typing import Optional
from config import get_default_config
from retriever import Retriever


@dataclass
class PromptManager:
    """Small helper to build a prompt from context and query."""

    instruction: str = (
        "You are an intelligent assistant. Use the context to answer the question concisely."
    )

    def build_prompt(self, query: str, context: str) -> str:
        return f"""{self.instruction}

Context:
{context}

Question:
{query}

Answer:
"""


@dataclass
class RAGChain:
    """Coordinator for a retrieval-augmented generation pipeline."""

    retriever: Optional[Retriever] = None
    config = get_default_config()
    prompt_manager: PromptManager = PromptManager()
    model_name: str = "gemini-2.5-pro"

    def __post_init__(self):
        if self.retriever is None:
            self.retriever = Retriever()

    def generate_answer(self, query: str, top_k: int = 3) -> str:
        """Retrieve context and generate an answer using Gemini.

        Returns the textual answer (str). Exceptions from the client bubble up.
        """
        context = self.retriever.retrieve_context(query, top_k=top_k)
        prompt = self.prompt_manager.build_prompt(query=query, context=context)

        genai = self.config.genai
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        # Response shape may vary; try to access `.text` or fall back.
        return getattr(response, "text", response.get("text") if isinstance(response, dict) else str(response))


if __name__ == "__main__":
    print("=== RAG Demo ===")
    q = input("Enter your question: ")
    chain = RAGChain()
    ans = chain.generate_answer(q)
    print("\n--- Answer ---")
    print(ans)
