# Cluster 41

class FaissStatsTool(Tool):
    """Tool for getting statistics about the FAISS vector database."""
    name: str = 'faiss_stats'
    description: str = 'Get statistics about the FAISS vector database or a specific corpus. Optionally provide a corpus_id to get stats for a specific corpus.'
    inputs: Dict[str, Dict[str, Any]] = {'corpus_id': {'type': 'string', 'description': 'Optional corpus ID to get statistics for. If not provided, returns global statistics'}}
    required: Optional[List[str]] = []

    def __init__(self, faiss_database: FaissDatabase=None):
        super().__init__()
        self.faiss_database = faiss_database

    def __call__(self, corpus_id: str=None) -> Dict[str, Any]:
        """Execute the stats operation."""
        return self.faiss_database.get_stats(corpus_id=corpus_id)

def __call__(self, corpus_id: str=None) -> Dict[str, Any]:
    """Execute the stats operation."""
    return self.faiss_database.get_stats(corpus_id=corpus_id)

class Corpus(BaseModule):
    """A generic collection of document chunks for RAG processing.

    Attributes:
        corpus_id (str): The unique id for corpus.
        chunks (List[Union[TextChunk, ImageChunk]]): List of chunks in the corpus.
        chunk_index (Dict[str, Union[TextChunk, ImageChunk]]): Index of chunks by chunk_id for fast lookup.
        metadata (Optional[IndexMetadata]): the metadata for this corpus.
    """

    def __init__(self, chunks: Optional[List[Union[TextChunk, ImageChunk]]]=None, corpus_id: Optional[str]=None, metadata: Optional[Union[IndexMetadata, Dict]]=None):
        corpus_id = uuid4() if corpus_id is None else corpus_id
        chunks = [] if chunks is None else chunks
        chunk_index = {} if chunks is None else {chunk.chunk_id: chunk for chunk in chunks}
        if metadata is None:
            metadata = {}
        elif isinstance(metadata, IndexMetadata):
            metadata = metadata.model_dump()
        super().__init__(corpus_id=corpus_id, chunks=chunks, chunk_index=chunk_index, metadata=metadata)

    def to_llama_nodes(self) -> List[BaseNode]:
        """Convert to list of LlamaIndex Nodes."""
        if not self.chunks:
            self.chunks = []
        return [chunk.to_llama_node() for chunk in self.chunks]

    @classmethod
    def from_llama_nodes(cls, nodes: List[BaseNode]) -> 'Corpus':
        """Create a Corpus from a list of LlamaIndex Nodes.

        Args:
            nodes (List[BaseNode]): The LlamaIndex Nodes to convert.

        Returns:
            Corpus: A new Corpus instance.
        """
        chunks = []
        for node in nodes:
            if isinstance(node, ImageNode):
                chunks.append(ImageChunk.from_llama_node(node))
            else:
                chunks.append(TextChunk.from_llama_node(node))
        return cls(chunks)

    def add_chunk(self, batch_chunk: Union[TextChunk, ImageChunk, List[Union[TextChunk, ImageChunk]]]):
        """Add a batch chunk to the corpus and update index."""
        if not isinstance(batch_chunk, list):
            batch_chunk = [batch_chunk]
        for chunk in batch_chunk:
            self.chunks.append(chunk)
            self.chunk_index[chunk.chunk_id] = chunk

    def get_chunk(self, chunk_id: str) -> Optional[Union[TextChunk, ImageChunk]]:
        """Retrieve a chunk by its ID."""
        return self.chunk_index.get(chunk_id)

    def remove_chunk(self, chunk_id: str):
        """Remove a chunk by its ID."""
        self.chunks = [chunk for chunk in self.chunks if chunk.chunk_id != chunk_id]
        self.chunk_index.pop(chunk_id, None)

    def filter_by_doc_id(self, doc_id: str) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by parent document ID."""
        return [chunk for chunk in self.chunks if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id == doc_id]

    def filter_by_similarity(self, threshold: float) -> List[Union[TextChunk, ImageChunk]]:
        """Filter chunks by similarity score."""
        return [chunk for chunk in self.chunks if chunk.metadata.similarity_score and chunk.metadata.similarity_score >= threshold]

    def sort_by_similarity(self, reverse: bool=True) -> List[Union[TextChunk, ImageChunk]]:
        """Sort chunks by similarity score (descending by default)."""
        return sorted([chunk for chunk in self.chunks if chunk.metadata.similarity_score is not None], key=lambda x: x.metadata.similarity_score, reverse=reverse)

    def to_dict(self, round_trip=False) -> Dict:
        """Convert corpus to dictionary for serialization."""
        return [self.model_dump(round_trip=round_trip)]

    def to_json(self, indent: int=2, round_trip=True) -> str:
        """Convert corpus to JSON string."""
        return json.dumps(self.to_dict(round_trip), indent=indent, ensure_ascii=False)

    def to_jsonl(self, output_path: str, indent: int=0):
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in self.chunks:
                json_str = chunk.to_json(indent=None)
                if '\n' in json_str:
                    print(f'Chunk {chunk.chunk_id} contains newlines in JSON, which may break JSONL format.')
                f.write(json_str + '\n')

    @classmethod
    def from_jsonl(cls, input_path: str, corpus_id: Optional[str]=None) -> 'Corpus':
        chunks = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                chunk_dict = json.loads(line.strip())
                metadata = ChunkMetadata.model_validate(chunk_dict['metadata'])
                chunk = Chunk(chunk_id=chunk_dict['chunk_id'], text=chunk_dict['text'], metadata=metadata, embedding=chunk_dict['embedding'], start_char_idx=chunk_dict['start_char_idx'], end_char_idx=chunk_dict['end_char_idx'], excluded_embed_metadata_keys=chunk_dict['excluded_embed_metadata_keys'], excluded_llm_metadata_keys=chunk_dict['excluded_llm_metadata_keys'], relationships={k: RelatedNodeInfo(**v) for k, v in chunk_dict['relationships'].items()})
                chunks.append(chunk)
        return cls(chunks=chunks, corpus_id=corpus_id)

    def __str__(self) -> str:
        stats = self.get_stats()
        return f'Corpus(chunks={stats['chunk_count']}, unique_docs={stats['unique_docs']}, avg_word_count={stats['avg_word_count']:.1f}, strategies={stats['strategies']})'

    def __repr__(self) -> str:
        return f'Corpus(chunks={len(self.chunks)}, chunk_index_keys={list(self.chunk_index.keys())})'

    def __len__(self) -> int:
        return len(self.chunks)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the corpus."""
        if not self.chunks:
            return {'chunk_count': 0, 'unique_docs': 0, 'avg_word_count': 0.0, 'strategies': set()}
        unique_docs = set()
        total_word_count = 0
        strategies = set()
        for chunk in self.chunks:
            if hasattr(chunk.metadata, 'doc_id') and chunk.metadata.doc_id:
                unique_docs.add(chunk.metadata.doc_id)
            if hasattr(chunk.metadata, 'word_count') and chunk.metadata.word_count:
                total_word_count += chunk.metadata.word_count
            if hasattr(chunk.metadata, 'chunking_strategy') and chunk.metadata.chunking_strategy:
                strategies.add(chunk.metadata.chunking_strategy)
        avg_word_count = total_word_count / len(self.chunks) if self.chunks else 0.0
        return {'chunk_count': len(self.chunks), 'unique_docs': len(unique_docs), 'avg_word_count': avg_word_count, 'strategies': strategies}

def __str__(self) -> str:
    stats = self.get_stats()
    return f'Corpus(chunks={stats['chunk_count']}, unique_docs={stats['unique_docs']}, avg_word_count={stats['avg_word_count']:.1f}, strategies={stats['strategies']})'

