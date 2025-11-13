# Cluster 10

class Message(BaseModel):
    """A message in a conversation, includes the role and content fields."""
    role: str
    content: str

    def to_openai(self):
        """Convert the message to an OpenAI-compatible format."""
        if self.role.lower() not in ['user', 'assistant', 'system', 'tool']:
            raise ValueError("Role must be either 'user', 'assistant', 'system' or 'tool'")
        return {'role': self.role, 'content': self.content}

    def to_cohere(self):
        """Convert the message to a Cohere-compatible format."""
        return {'role': self.role, 'message': self.content}

    def to_llamacpp(self):
        """Convert the message to a LlamaCPP-compatible format."""
        return {'role': self.role, 'content': self.content}

    def to_mistral(self):
        """Convert the message to a Mistral-compatible format."""
        return {'role': self.role, 'content': self.content}

    def to_voyage(self):
        """Convert the message to a Voyage-compatible format."""
        return {'role': self.role, 'content': self.content}

    def to_jina(self):
        """Convert the message to a Jina-compatible format."""
        return {'role': self.role, 'content': self.content}

    def __str__(self):
        """Convert the message to a string."""
        return f'{self.role}: {self.content}'

def to_openai(self):
    """Convert the message to an OpenAI-compatible format."""
    if self.role.lower() not in ['user', 'assistant', 'system', 'tool']:
        raise ValueError("Role must be either 'user', 'assistant', 'system' or 'tool'")
    return {'role': self.role, 'content': self.content}

class TfidfEncoder(SparseEncoder, FittableMixin):
    idf: np.ndarray = np.array([])
    word_index: Dict = {}

    def __init__(self, name: str | None=None):
        if name is None:
            name = 'tfidf'
        super().__init__(name=name)
        self.word_index = {}
        self.idf = np.array([])

    def __call__(self, docs: List[str]) -> list[SparseEmbedding]:
        if len(self.word_index) == 0 or self.idf.size == 0:
            raise ValueError('Vectorizer is not initialized.')
        if len(docs) == 0:
            raise ValueError('No documents to encode.')
        docs = [self._preprocess(doc) for doc in docs]
        tf = self._compute_tf(docs)
        tfidf = tf * self.idf
        return self._array_to_sparse_embeddings(tfidf)

    async def acall(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.__call__(docs))

    def fit(self, routes: List[Route]):
        """Trains the encoder weights on the provided routes.

        :param routes: List of routes to train the encoder on.
        :type routes: List[Route]
        """
        self._fit_validate(routes=routes)
        docs = []
        for route in routes:
            for doc in route.utterances:
                docs.append(self._preprocess(doc))
        self.word_index = self._build_word_index(docs)
        if len(self.word_index) == 0:
            raise ValueError(f'Too little data to fit {self.__class__.__name__}.')
        self.idf = self._compute_idf(docs)

    def _fit_validate(self, routes: List[Route]):
        if not isinstance(routes, list) or not isinstance(routes[0], Route):
            raise TypeError('`routes` parameter must be a list of Route objects.')

    def _build_word_index(self, docs: List[str]) -> Dict:
        words = set()
        for doc in docs:
            for word in doc.split():
                words.add(word)
        word_index = {word: i for i, word in enumerate(words)}
        return word_index

    def _compute_tf(self, docs: List[str]) -> np.ndarray:
        if len(self.word_index) == 0:
            raise ValueError('Word index is not initialized.')
        tf = np.zeros((len(docs), len(self.word_index)))
        for i, doc in enumerate(docs):
            word_counts = Counter(doc.split())
            for word, count in word_counts.items():
                if word in self.word_index:
                    tf[i, self.word_index[word]] = count
        tf = tf / np.linalg.norm(tf, axis=1, keepdims=True)
        return tf

    def _compute_idf(self, docs: List[str]) -> np.ndarray:
        if len(self.word_index) == 0:
            raise ValueError('Word index is not initialized.')
        idf = np.zeros(len(self.word_index))
        for doc in docs:
            words = set(doc.split())
            for word in words:
                if word in self.word_index:
                    idf[self.word_index[word]] += 1
        idf = np.log(len(docs) / (idf + 1))
        return idf

    def _preprocess(self, doc: str) -> str:
        lowercased_doc = doc.lower()
        no_punctuation_doc = lowercased_doc.translate(str.maketrans('', '', string.punctuation))
        return no_punctuation_doc

def _preprocess(self, doc: str) -> str:
    lowercased_doc = doc.lower()
    no_punctuation_doc = lowercased_doc.translate(str.maketrans('', '', string.punctuation))
    return no_punctuation_doc

def init_index(index_cls, dimensions: int=3, namespace: str='', index_name: str | None=None, init_async_index: bool=False):
    """Initialize indexes for unit testing."""
    if index_cls is QdrantIndex:
        index_name = index_name or f'test_{uuid.uuid4().hex}'
        return QdrantIndex(index_name=index_name, init_async_index=init_async_index)
    if index_cls is PineconeIndex:
        index_name = f'test-{datetime.now().strftime('%Y%m%d%H%M%S')}' if not index_name else index_name
        index = index_cls(index_name=index_name, dimensions=dimensions, namespace=namespace, init_async_index=init_async_index, base_url=PINECONE_BASE_URL)
    elif index_cls is PostgresIndex:
        index = index_cls(index_name=index_name or 'test_index', index_prefix='', namespace=namespace, dimensions=dimensions, init_async_index=init_async_index)
    elif index_cls is None:
        return None
    else:
        index = index_cls(init_async_index=init_async_index)
    return index

def init_index(index_cls, dimensions: Optional[int]=3, namespace: Optional[str]='', init_async_index: bool=False, index_name: Optional[str]=None):
    """We use this function to initialize indexes with different names to avoid
    issues during testing.
    """
    if index_cls is PineconeIndex:
        if index_name:
            if not dimensions and 'OpenAIEncoder' in index_name:
                dimensions = 1536
            elif not dimensions and 'CohereEncoder' in index_name:
                dimensions = 1024
        index_name = TEST_ID if not index_name else f'{TEST_ID}-{index_name.lower()}'
        index = index_cls(index_name=index_name, dimensions=dimensions, namespace=namespace, init_async_index=init_async_index, base_url=PINECONE_BASE_URL)
    else:
        index = index_cls()
    return index

def init_index(index_cls, dimensions: Optional[int]=None, namespace: Optional[str]='', index_name: Optional[str]=None):
    """We use this function to initialize indexes with different names to avoid
    issues during testing.
    """
    if index_cls is PineconeIndex:
        if index_name:
            if not dimensions and 'OpenAIEncoder' in index_name:
                dimensions = 1536
            elif not dimensions and 'CohereEncoder' in index_name:
                dimensions = 1024
        index_name = TEST_ID if not index_name else f'{TEST_ID}-{index_name.lower()}'
        index = index_cls(index_name=index_name, dimensions=dimensions, namespace=namespace)
    elif index_cls is PostgresIndex:
        index = index_cls(index_name=index_name, index_prefix='', namespace=namespace)
    else:
        index = index_cls()
    return index

