"""
Centralized configuration and client initialization.

Implements a simple Singleton-style `Config` so other modules can
import and reuse configured clients (Gemini, Pinecone) and settings.
"""
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv
import google.generativeai as genai
from pinecone import Pinecone

load_dotenv()


@dataclass
class Config:
	"""Application configuration and initialized clients.

	Note: this class is intentionally lightweight and not thread-safe.
	It's meant for simple scripts and demos. For production, consider
	more robust configuration management.
	"""
	gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
	pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
	pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "rag-demo")
	log_level: str = os.getenv("RAG_LOG_LEVEL", "INFO")

	# clients (initialized on first access)
	_genai = None
	_pinecone = None
	_pinecone_index = None

	def __post_init__(self):
		logging.basicConfig(level=getattr(logging, self.log_level.upper(), logging.INFO))

	@property
	def genai(self):
		if self._genai is None:
			genai.configure(api_key=self.gemini_api_key)
			self._genai = genai
		return self._genai

	@property
	def pinecone(self):
		if self._pinecone is None:
			self._pinecone = Pinecone(api_key=self.pinecone_api_key)
		return self._pinecone

	@property
	def index(self):
		if self._pinecone_index is None:
			self._pinecone_index = self.pinecone.Index(self.pinecone_index_name)
		return self._pinecone_index


# module-level default config instance for convenience
DEFAULT_CONFIG = Config()


def get_default_config() -> Config:
	"""Return the shared default configuration instance."""
	return DEFAULT_CONFIG
