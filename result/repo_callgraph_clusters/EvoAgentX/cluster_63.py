# Cluster 63

class RagResult(BaseModule):
    """Represents a generic retrieval result."""
    corpus: Corpus = Field(description='Retrieved chunks.')
    scores: List[float] = Field(description='Similarity scores for each chunk.')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional result metadata.')

    def get_top_chunks(self, limit: int=None) -> List[Union[TextChunk, ImageChunk]]:
        """Get top chunks sorted by similarity score."""
        chunks = self.corpus.sort_by_similarity(reverse=True)
        return chunks[:limit] if limit else chunks

def get_top_chunks(self, limit: int=None) -> List[Union[TextChunk, ImageChunk]]:
    """Get top chunks sorted by similarity score."""
    chunks = self.corpus.sort_by_similarity(reverse=True)
    return chunks[:limit] if limit else chunks

