# Cluster 16

def similarity_matrix(xq: np.ndarray, index: np.ndarray) -> np.ndarray:
    """Compute the similarity scores between a query vector and a set of vectors.

    :param xq: A query vector (1d ndarray)
    :param index: A set of vectors.
    :return: The similarity between the query vector and the set of vectors.
    :rtype: np.ndarray
    """
    index_norm = norm(index, axis=1)
    xq_norm = norm(xq.T)
    sim = np.dot(index, xq.T) / (index_norm * xq_norm)
    return sim

def top_scores(sim: np.ndarray, top_k: int=5) -> Tuple[np.ndarray, np.ndarray]:
    """Get the top scores and indices from a similarity matrix.

    :param sim: A similarity matrix.
    :param top_k: The number of top scores to get.
    :return: The top scores and indices.
    :rtype: Tuple[np.ndarray, np.ndarray]
    """
    top_k = min(top_k, sim.shape[0])
    idx = np.argpartition(sim, -top_k)[-top_k:]
    scores = sim[idx]
    return (scores, idx)

class HybridLocalIndex(LocalIndex):
    type: str = 'hybrid_local'
    sparse_index: Optional[list[dict]] = None
    route_names: Optional[np.ndarray] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.metadata = None

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], sparse_embeddings: Optional[List[SparseEmbedding]]=None, **kwargs):
        """Add embeddings to the index.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        :param sparse_embeddings: List of sparse embeddings to add to the index.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        if sparse_embeddings is None:
            raise ValueError('Sparse embeddings are required for HybridLocalIndex.')
        if function_schemas is not None:
            logger.warning('Function schemas are not supported for HybridLocalIndex.')
        if metadata_list:
            logger.warning('Metadata is not supported for HybridLocalIndex.')
        embeds = np.array(embeddings)
        routes_arr = np.array(routes)
        if isinstance(utterances[0], str):
            utterances_arr = np.array(utterances)
        else:
            utterances_arr = np.array(utterances, dtype=object)
        if self.index is None or self.sparse_index is None:
            self.index = embeds
            self.sparse_index = [x.to_dict() for x in sparse_embeddings]
            self.routes = routes_arr
            self.utterances = utterances_arr
            self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)
        else:
            self.index = np.concatenate([self.index, embeds])
            self.sparse_index.extend([x.to_dict() for x in sparse_embeddings])
            self.routes = np.concatenate([self.routes, routes_arr])
            self.utterances = np.concatenate([self.utterances, utterances_arr])
            if self.metadata is not None:
                self.metadata = np.concatenate([self.metadata, np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)])
            else:
                self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], sparse_embeddings: Optional[List[SparseEmbedding]]=None, **kwargs):
        """Add embeddings to the index - note that this is not truly async as it is a
        local index and there is no sense to make this method async. Instead, it will
        call the sync `add` method.

        :param embeddings: List of embeddings to add to the index.
        :type embeddings: List[List[float]]
        :param routes: List of routes to add to the index.
        :type routes: List[str]
        :param utterances: List of utterances to add to the index.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to add to the index.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to add to the index.
        :type metadata_list: List[Dict[str, Any]]
        :param sparse_embeddings: List of sparse embeddings to add to the index.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        self.add(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the index.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects - HybridLocalIndex doesn't include metadata so
        this parameter is ignored.
        :type include_metadata: bool
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.routes is None or self.utterances is None:
            return []
        if include_metadata and self.metadata is not None:
            return [Utterance(route=route, utterance=utterance, function_schemas=None, metadata=metadata) for route, utterance, metadata in zip(self.routes, self.utterances, self.metadata)]
        else:
            return [Utterance.from_tuple(x) for x in zip(self.routes, self.utterances)]

    def _sparse_dot_product(self, vec_a: dict[int, float], vec_b: dict[int, float]) -> float:
        """Calculate the dot product of two sparse vectors.

        :param vec_a: The first sparse vector.
        :type vec_a: dict[int, float]
        :param vec_b: The second sparse vector.
        :type vec_b: dict[int, float]
        :return: The dot product of the two sparse vectors.
        :rtype: float
        """
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = (vec_b, vec_a)
        return sum((vec_a[i] * vec_b.get(i, 0) for i in vec_a))

    def _sparse_index_dot_product(self, vec_a: dict[int, float]) -> list[float]:
        """Calculate the dot product of a sparse vector and a list of sparse vectors.

        :param vec_a: The sparse vector.
        :type vec_a: dict[int, float]
        :return: A list of dot products.
        :rtype: list[float]
        """
        if self.sparse_index is None:
            raise ValueError('self.sparse_index is not populated.')
        dot_products = [self._sparse_dot_product(vec_a, vec_b) for vec_b in self.sparse_index]
        return dot_products

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: The sparse vector to search for, must be provided.
        :type sparse_vector: dict[int, float]
        """
        if route_filter:
            raise ValueError('Route filter is not supported for HybridLocalIndex.')
        xq_d = vector.copy()
        if isinstance(sparse_vector, SparseEmbedding):
            xq_s = sparse_vector.to_dict()
        elif isinstance(sparse_vector, dict):
            xq_s = sparse_vector
        else:
            raise ValueError('Sparse vector must be a SparseEmbedding or dict.')
        if self.index is not None and self.sparse_index is not None:
            index_norm = norm(self.index, axis=1)
            xq_d_norm = norm(xq_d)
            sim_d = np.squeeze(np.dot(self.index, xq_d.T)) / (index_norm * xq_d_norm)
            sim_s = np.array(self._sparse_index_dot_product(xq_s))
            total_sim = sim_d + sim_s
            top_k = min(top_k, total_sim.shape[0])
            idx = np.argpartition(total_sim, -top_k)[-top_k:]
            scores = total_sim[idx]
            route_names = self.routes[idx] if self.routes is not None else []
            return (scores, route_names)
        else:
            logger.warning('Index or sparse index is not populated.')
            return (np.array([]), [])

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results. This method calls the
        sync `query` method as everything uses numpy computations which is CPU-bound
        and so no benefit can be gained from making this async.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: The sparse vector to search for, must be provided.
        :type sparse_vector: dict[int, float]
        """
        return self.query(vector=vector, top_k=top_k, route_filter=route_filter, sparse_vector=sparse_vector)

    def aget_routes(self):
        """Get all routes from the index.

        :return: A list of routes.
        :rtype: List[str]
        """
        logger.error(f'Sync remove is not implemented for {self.__class__.__name__}.')

    def _write_config(self, config: ConfigParameter):
        """Write the config to the index.

        :param config: The config to write to the index.
        :type config: ConfigParameter
        """
        logger.warning(f'No config is written for {self.__class__.__name__}.')

    def delete(self, route_name: str):
        """Delete all records of a specific route from the index.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        if self.index is not None and self.routes is not None and (self.utterances is not None):
            delete_idx = self._get_indices_for_route(route_name=route_name)
            self.index = np.delete(self.index, delete_idx, axis=0)
            self.routes = np.delete(self.routes, delete_idx, axis=0)
            self.utterances = np.delete(self.utterances, delete_idx, axis=0)
            if self.metadata is not None:
                self.metadata = np.delete(self.metadata, delete_idx, axis=0)
        else:
            raise ValueError('Attempted to delete route records but either index, routes or utterances is None.')

    def delete_index(self):
        """Deletes the index, effectively clearing it and setting it to None.

        :return: None
        :rtype: None
        """
        self.index = None
        self.routes = None
        self.utterances = None
        self.metadata = None

    def _get_indices_for_route(self, route_name: str):
        """Gets an array of indices for a specific route.

        :param route_name: The name of the route to get indices for.
        :type route_name: str
        :return: An array of indices for the route.
        :rtype: np.ndarray
        """
        if self.routes is None:
            raise ValueError('Routes are not populated.')
        idx = [i for i, route in enumerate(self.routes) if route == route_name]
        return idx

    def __len__(self):
        if self.index is not None:
            return self.index.shape[0]
        else:
            return 0

def _sparse_dot_product(self, vec_a: dict[int, float], vec_b: dict[int, float]) -> float:
    """Calculate the dot product of two sparse vectors.

        :param vec_a: The first sparse vector.
        :type vec_a: dict[int, float]
        :param vec_b: The second sparse vector.
        :type vec_b: dict[int, float]
        :return: The dot product of the two sparse vectors.
        :rtype: float
        """
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = (vec_b, vec_a)
    return sum((vec_a[i] * vec_b.get(i, 0) for i in vec_a))

def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
    """Search the index for the query and return top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: The sparse vector to search for, must be provided.
        :type sparse_vector: dict[int, float]
        """
    if route_filter:
        raise ValueError('Route filter is not supported for HybridLocalIndex.')
    xq_d = vector.copy()
    if isinstance(sparse_vector, SparseEmbedding):
        xq_s = sparse_vector.to_dict()
    elif isinstance(sparse_vector, dict):
        xq_s = sparse_vector
    else:
        raise ValueError('Sparse vector must be a SparseEmbedding or dict.')
    if self.index is not None and self.sparse_index is not None:
        index_norm = norm(self.index, axis=1)
        xq_d_norm = norm(xq_d)
        sim_d = np.squeeze(np.dot(self.index, xq_d.T)) / (index_norm * xq_d_norm)
        sim_s = np.array(self._sparse_index_dot_product(xq_s))
        total_sim = sim_d + sim_s
        top_k = min(top_k, total_sim.shape[0])
        idx = np.argpartition(total_sim, -top_k)[-top_k:]
        scores = total_sim[idx]
        route_names = self.routes[idx] if self.routes is not None else []
        return (scores, route_names)
    else:
        logger.warning('Index or sparse index is not populated.')
        return (np.array([]), [])

class DenseEncoder(BaseModel):
    name: str
    score_threshold: Optional[float] = None
    type: str = Field(default='base')
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    @field_validator('score_threshold')
    def set_score_threshold(cls, v: float | None) -> float | None:
        """Set the score threshold. If None, the score threshold is not used.

        :param v: The score threshold.
        :type v: float | None
        :return: The score threshold.
        :rtype: float | None
        """
        return float(v) if v is not None else None

    def __call__(self, docs: List[Any]) -> List[List[float]]:
        """Encode a list of documents. Documents can be any type, but the encoder must
        be built to handle that data type. Typically, these types are strings or
        arrays representing images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :return: The encoded documents.
        :rtype: List[List[float]]
        """
        raise NotImplementedError('Subclasses must implement this method')

    async def acall(self, docs: List[Any]) -> List[List[float]]:
        """Encode a list of documents asynchronously. Documents can be any type, but the
        encoder must be built to handle that data type. Typically, these types are
        strings or arrays representing images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :return: The encoded documents.
        :rtype: List[List[float]]
        """
        raise NotImplementedError('Subclasses must implement this method')

@field_validator('score_threshold')
def set_score_threshold(cls, v: float | None) -> float | None:
    """Set the score threshold. If None, the score threshold is not used.

        :param v: The score threshold.
        :type v: float | None
        :return: The score threshold.
        :rtype: float | None
        """
    return float(v) if v is not None else None

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

def __call__(self, docs: List[str]) -> list[SparseEmbedding]:
    if len(self.word_index) == 0 or self.idf.size == 0:
        raise ValueError('Vectorizer is not initialized.')
    if len(docs) == 0:
        raise ValueError('No documents to encode.')
    docs = [self._preprocess(doc) for doc in docs]
    tf = self._compute_tf(docs)
    tfidf = tf * self.idf
    return self._array_to_sparse_embeddings(tfidf)

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

class BM25Encoder(SparseEncoder, FittableMixin, AsymmetricSparseMixin):
    """BM25Encoder, running a vectorized version of ATIRE BM25 algorithm

    Concept:
    - BM25 uses scoring between queries & corpus to retrieve the most relevant documents ∈ corpus
    - most vector databases (VDB) store embedded documents and score them versus received queries for retrieval
    - we need to break up the BM25 formula into `encode_queries` and `encode_documents`, with the latter to be stored in VDB
    - dot product of `encode_queries(q)` and `encode_documents([D_0, D_1, ...])` is the BM25 score of the documents `[D_0, D_1, ...]` for the given query `q`
    - we train a BM25 encoder's normalization parameters on a sufficiently large corpus to capture target language distribution
    - these trained parameter allow us to balance TF & IDF of query & documents for retrieval (read more on how BM25 fixes issues with TF-IDF)

    ATIRE Paper: https://www.cs.otago.ac.nz/research/student-publications/atire-opensource.pdf
    Pinecone Implementation: https://github.com/pinecone-io/pinecone-text/blob/8399f9ff28c4652766c35165c0db9b0eff309077/pinecone_text/sparse/bm25_encoder.py

    :param k1: normalizer parameter that limits how much a single query term `q_i ∈ q` can affect score for document `D_n`
    :type k1: float
    :param b: normalizer parameter that balances the effect of a single document length compared to the average document length
    :type b: float
    :param corpus_size: number of documents in the trained corpus
    :type corpus_size: int, optional
    :param _avg_doc_len: float representing the average document length in the trained corpus
    :type _avg_doc_len: float, optional
    :param _documents_containing_word: (1, tokenizer.vocab_size) shaped array, denoting how many documents contain `token ∈ vocab`
    :type _documents_containing_word: class:`numpy.ndarray`, optional

    """
    type: str = 'sparse'
    k1: float = 1.5
    b: float = 0.75
    corpus_size: int | None = None
    _tokenizer: BaseTokenizer | None
    _avg_doc_len: np.float64 | float | None
    _documents_containing_word: np.ndarray | None

    def __init__(self, tokenizer: BaseTokenizer | None=None, name: str | None=None, k1: float=1.5, b: float=0.75, corpus_size: int | None=None, avg_doc_len: float | None=None, use_default_params: bool=True) -> None:
        if name is None:
            name = 'bm25'
        super().__init__(name=name)
        self.k1 = k1
        self.b = b
        self.corpus_size = corpus_size
        self._avg_doc_len = np.float64(avg_doc_len) if avg_doc_len else None
        if use_default_params and (not tokenizer):
            logger.info('Initializing default BM25 model parameters.')
            self._tokenizer = PretrainedTokenizer('google-bert/bert-base-uncased')
        elif tokenizer is not None:
            self._tokenizer = tokenizer
        else:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')

    def _fit_validate(self, routes: List[Route]):
        if not isinstance(routes, list) or not isinstance(routes[0], Route):
            raise TypeError('`routes` parameter must be a list of Route objects.')

    def fit(self, routes: List[Route]) -> 'BM25Encoder':
        """Trains the encoder weights on the provided routes.

        :param routes: List of routes to train the encoder on.
        :type routes: List[Route]
        """
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        self._fit_validate(routes)
        utterances = [utterance for route in routes for utterance in route.utterances]
        utterance_ids = self._tokenizer.tokenize(utterances, pad=True)
        corpus = self._tf(utterance_ids)
        self.corpus_size = len(utterances)
        doc_lengths = corpus.sum(axis=1)
        self._avg_doc_len = doc_lengths.mean()
        documents_containing_word = np.atleast_2d((corpus > 0).sum(axis=0))
        documents_containing_word[:, 0] *= 0
        self._documents_containing_word = documents_containing_word
        return self

    def _tf(self, docs: np.ndarray) -> np.ndarray:
        """Returns term frequency of query terms in trained corpus

        :param docs: 2D shaped array of each document's token ids
        :type docs: numpy.ndarray
        :return: Matrix where value @ (m, n) represents how many times token id `n` appears in document `m`
        :rtype: numpy.ndarray
        """
        if self._tokenizer is None:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')
        vocab_size = self._tokenizer.vocab_size
        bincount = partial(np.bincount, minlength=vocab_size)
        tf = np.apply_along_axis(bincount, 1, docs)
        tf[:, 0] *= 0
        return tf

    def _df(self, queries: np.ndarray) -> np.ndarray:
        """Returns the amount of times each token in the query appears in trained corpus

        This is done in a faster, vectorized way, instead of looping through each query

        :param queries: 2D shaped array of each query token ids
        :type queries: numpy.ndarray
        :return: Matrix where value @ (m, n) represents how many times token id `n` in query `m` appears in the trained corpus
        :rtype: numpy.ndarray
        """
        if self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. `BM25Encoder.fit` a corpus, or `BM25Encoder.load` a pretrained encoder.')
        if self._tokenizer is None:
            raise ValueError('Tokenizer not provided. Provide a tokenizer or set `use_default_params` to True')
        n = queries.shape[0]
        row_indices = np.arange(n)[:, None]
        mask = np.zeros((n, self._tokenizer.vocab_size), dtype=bool)
        mask[row_indices, queries] = True
        query_df = mask * self._documents_containing_word
        return query_df

    def encode_queries(self, queries: list[str]) -> list[SparseEmbedding]:
        """Returns BM25 scores for queries using precomputed corpus scores.

        :param queries: List of queries to encode
        :type queries: list
        :return: BM25 scores for each query against the corpus
        :rtype: list[SparseEmbedding]
        """
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        if queries == []:
            raise ValueError('No documents provided for encoding')
        queries_ids = self._tokenizer.tokenize(queries)
        df = self._df(queries_ids)
        N = self.corpus_size
        df = df + np.where(df > 0, 0.5, 0)
        idf = np.divide(N + 1, df, out=np.zeros_like(df), where=df != 0)
        idf = np.log(idf, out=np.zeros_like(df), where=df != 0)
        idf_norm = np.divide(idf, idf.sum(axis=1)[:, np.newaxis], out=np.zeros_like(idf), where=idf != 0)
        return self._array_to_sparse_embeddings(idf_norm)

    def encode_documents(self, documents: list[str], batch_size: int | None=None) -> list[SparseEmbedding]:
        """Returns document term frequency normed by itself & average trained corpus length
        (This is the right-hand side of the BM25 equation, which gets matmul-ed with the query IDF component)

        LaTeX: $\\frac{f(d_i, D)}{f(d_i, D) + k_1 \\times (1 - b + b \\times \\frac{|D|}{avgdl})}$
        where:
            f(d_i, D) is frequency of term `d_i ∈ D`
            |D| is the document length
            avgdl is average document length in trained corpus

        :param documents: List of queries to encode
        :type documents: list
        :return: Encoded queries (as either sparse or dict)
        :rtype: list[SparseEmbedding]
        """
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        if not self._tokenizer:
            raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
        if documents == []:
            raise ValueError('No documents provided for encoding')
        batch_size = batch_size or len(documents)
        queries_ids = self._tokenizer.tokenize(documents, pad=True)
        tf = self._tf(queries_ids)
        tf_sum = tf.sum(axis=1)
        tf_normed = tf / (self.k1 * (1.0 - self.b * self.b * (tf_sum[:, np.newaxis] / self._avg_doc_len)) + tf)
        return self._array_to_sparse_embeddings(tf_normed)

    def model(self, docs: List[str]) -> list[SparseEmbedding]:
        """Encode documents using BM25, with different encoding for queries vs documents to be indexed.

        :param docs: List of documents to encode
        :param is_query: If True, use query encoding, else use document encoding
        :return: List of sparse embeddings
        """
        if not self._tokenizer:
            raise ValueError('Encoder not fitted. `BM25.index` a corpus, or `BM25.load` a pretrained encoder.')
        if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
            raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
        return self.encode_queries(docs)

    async def aencode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.encode_queries(docs))

    async def aencode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.encode_documents(docs))

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        return self.encode_queries(docs)

    async def acall(self, docs: List[Any]) -> List[SparseEmbedding]:
        return await asyncio.to_thread(lambda: self.__call__(docs))

def fit(self, routes: List[Route]) -> 'BM25Encoder':
    """Trains the encoder weights on the provided routes.

        :param routes: List of routes to train the encoder on.
        :type routes: List[Route]
        """
    if not self._tokenizer:
        raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
    self._fit_validate(routes)
    utterances = [utterance for route in routes for utterance in route.utterances]
    utterance_ids = self._tokenizer.tokenize(utterances, pad=True)
    corpus = self._tf(utterance_ids)
    self.corpus_size = len(utterances)
    doc_lengths = corpus.sum(axis=1)
    self._avg_doc_len = doc_lengths.mean()
    documents_containing_word = np.atleast_2d((corpus > 0).sum(axis=0))
    documents_containing_word[:, 0] *= 0
    self._documents_containing_word = documents_containing_word
    return self

def encode_queries(self, queries: list[str]) -> list[SparseEmbedding]:
    """Returns BM25 scores for queries using precomputed corpus scores.

        :param queries: List of queries to encode
        :type queries: list
        :return: BM25 scores for each query against the corpus
        :rtype: list[SparseEmbedding]
        """
    if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
        raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
    if not self._tokenizer:
        raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
    if queries == []:
        raise ValueError('No documents provided for encoding')
    queries_ids = self._tokenizer.tokenize(queries)
    df = self._df(queries_ids)
    N = self.corpus_size
    df = df + np.where(df > 0, 0.5, 0)
    idf = np.divide(N + 1, df, out=np.zeros_like(df), where=df != 0)
    idf = np.log(idf, out=np.zeros_like(df), where=df != 0)
    idf_norm = np.divide(idf, idf.sum(axis=1)[:, np.newaxis], out=np.zeros_like(idf), where=idf != 0)
    return self._array_to_sparse_embeddings(idf_norm)

def encode_documents(self, documents: list[str], batch_size: int | None=None) -> list[SparseEmbedding]:
    """Returns document term frequency normed by itself & average trained corpus length
        (This is the right-hand side of the BM25 equation, which gets matmul-ed with the query IDF component)

        LaTeX: $\\frac{f(d_i, D)}{f(d_i, D) + k_1 \\times (1 - b + b \\times \\frac{|D|}{avgdl})}$
        where:
            f(d_i, D) is frequency of term `d_i ∈ D`
            |D| is the document length
            avgdl is average document length in trained corpus

        :param documents: List of queries to encode
        :type documents: list
        :return: Encoded queries (as either sparse or dict)
        :rtype: list[SparseEmbedding]
        """
    if self.corpus_size is None or self._avg_doc_len is None or self._documents_containing_word is None:
        raise ValueError('Encoder not fitted. Please `.fit` the model on a provided corpus or load a pretrained encoder')
    if not self._tokenizer:
        raise ValueError('BM25 encoder not initialized. Provide a tokenizer or set `use_default_params` to True')
    if documents == []:
        raise ValueError('No documents provided for encoding')
    batch_size = batch_size or len(documents)
    queries_ids = self._tokenizer.tokenize(documents, pad=True)
    tf = self._tf(queries_ids)
    tf_sum = tf.sum(axis=1)
    tf_normed = tf / (self.k1 * (1.0 - self.b * self.b * (tf_sum[:, np.newaxis] / self._avg_doc_len)) + tf)
    return self._array_to_sparse_embeddings(tf_normed)

class HuggingFaceEncoder(DenseEncoder):
    """HuggingFace encoder class for local embedding models. Models can be trained and
    loaded from private repositories, or from the Huggingface Hub. The class supports
    customization of the score threshold for filtering or processing the embeddings.

    Example usage:

    ```python
    from semantic_router.encoders import HuggingFaceEncoder

    encoder = HuggingFaceEncoder(
        name="sentence-transformers/all-MiniLM-L6-v2",
        device="cuda"
    )
    embeddings = encoder(["document1", "document2"])
    ```
    """
    name: str = 'sentence-transformers/all-MiniLM-L6-v2'
    type: str = 'huggingface'
    tokenizer_kwargs: Dict = {}
    model_kwargs: Dict = {}
    device: Optional[str] = None
    _tokenizer: Any = PrivateAttr()
    _model: Any = PrivateAttr()
    _torch: Any = PrivateAttr()

    def __init__(self, **data):
        if data.get('score_threshold') is None:
            data['score_threshold'] = 0.5
        super().__init__(**data)
        self._tokenizer, self._model = self._initialize_hf_model()

    def _initialize_hf_model(self):
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except (ImportError, RuntimeError, ModuleNotFoundError):
            raise ImportError('Please install transformers to use HuggingFaceEncoder. You can install it with: `pip install semantic-router[local]`')
        self._torch = torch
        tokenizer = AutoTokenizer.from_pretrained(self.name, **self.tokenizer_kwargs)
        model = AutoModel.from_pretrained(self.name, **self.model_kwargs)
        if self.device:
            model.to(self.device)
        else:
            device = 'cuda' if self._torch.cuda.is_available() else 'cpu'
            model.to(device)
            self.device = device
        return (tokenizer, model)

    def __call__(self, docs: List[str], batch_size: int=32, normalize_embeddings: bool=True, pooling_strategy: str='mean') -> List[List[float]]:
        """Encode a list of documents into embeddings using the local Hugging Face model.

        :param docs: A list of documents to encode.
        :type docs: List[str]
        :param batch_size: The batch size for encoding.
        """
        all_embeddings = []
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            encoded_input = self._tokenizer(batch_docs, padding=True, truncation=True, return_tensors='pt').to(self.device)
            with self._torch.no_grad():
                model_output = self._model(**encoded_input)
            if pooling_strategy == 'mean':
                embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            elif pooling_strategy == 'max':
                embeddings = self._max_pooling(model_output, encoded_input['attention_mask'])
            else:
                raise ValueError("Invalid pooling_strategy. Please use 'mean' or 'max'.")
            if normalize_embeddings:
                embeddings = self._torch.nn.functional.normalize(embeddings, p=2, dim=1)
            embeddings = embeddings.tolist()
            all_embeddings.extend(embeddings)
        return all_embeddings

    def _mean_pooling(self, model_output, attention_mask):
        """Perform mean pooling on the token embeddings.

        :param model_output: The output of the model.
        :type model_output: torch.Tensor
        :param attention_mask: The attention mask.
        """
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return self._torch.sum(token_embeddings * input_mask_expanded, 1) / self._torch.clamp(input_mask_expanded.sum(1), min=1e-09)

    def _max_pooling(self, model_output, attention_mask):
        """Perform max pooling on the token embeddings.

        :param model_output: The output of the model.
        :type model_output: torch.Tensor
        :param attention_mask: The attention mask.
        """
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        token_embeddings[input_mask_expanded == 0] = -1000000000.0
        return self._torch.max(token_embeddings, 1)[0]

def _mean_pooling(self, model_output, attention_mask):
    """Perform mean pooling on the token embeddings.

        :param model_output: The output of the model.
        :type model_output: torch.Tensor
        :param attention_mask: The attention mask.
        """
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return self._torch.sum(token_embeddings * input_mask_expanded, 1) / self._torch.clamp(input_mask_expanded.sum(1), min=1e-09)

def _max_pooling(self, model_output, attention_mask):
    """Perform max pooling on the token embeddings.

        :param model_output: The output of the model.
        :type model_output: torch.Tensor
        :param attention_mask: The attention mask.
        """
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    token_embeddings[input_mask_expanded == 0] = -1000000000.0
    return self._torch.max(token_embeddings, 1)[0]

class LocalSparseEncoder(SparseEncoder):
    """Local sparse encoder using sentence-transformers' SparseEncoder (e.g., SPLADE, CSR) for efficient local sparse embeddings."""
    name: str = 'naver/splade-v3'
    type: str = 'sparse_local'
    device: Optional[str] = None
    batch_size: int = 32
    _model: Any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from sentence_transformers import SparseEncoder as STSparseEncoder
        except ImportError:
            raise ImportError('Please install sentence-transformers >=v5 to use SparseSentenceTransformerEncoder. You can install it with: `pip install sentence-transformers`')
        self._model = STSparseEncoder(self.name)
        if self.device:
            self._model.to(self.device)
        else:
            import torch
            if torch.cuda.is_available():
                self.device = 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = 'mps'
            else:
                self.device = 'cpu'
            self._model.to(self.device)

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        sparse_embeddings = self._model.encode(docs, batch_size=self.batch_size)
        return self._array_to_sparse_embeddings(sparse_embeddings)

def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
    sparse_embeddings = self._model.encode(docs, batch_size=self.batch_size)
    return self._array_to_sparse_embeddings(sparse_embeddings)

class BaseRouter(BaseModel):
    """Base class for all routers."""
    encoder: DenseEncoder = Field(default_factory=OpenAIEncoder)
    sparse_encoder: Optional[SparseEncoder] = Field(default=None)
    index: BaseIndex = Field(default_factory=BaseIndex)
    score_threshold: Optional[float] = Field(default=None)
    routes: List[Route] = Field(default_factory=list)
    llm: Optional[BaseLLM] = None
    top_k: int = 5
    aggregation: str = 'mean'
    aggregation_method: Optional[Callable] = None
    auto_sync: Optional[str] = None
    init_async_index: bool = False
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, encoder: Optional[DenseEncoder]=None, sparse_encoder: Optional[SparseEncoder]=None, llm: Optional[BaseLLM]=None, routes: Optional[List[Route]]=None, index: Optional[BaseIndex]=None, top_k: int=5, aggregation: str='mean', auto_sync: Optional[str]=None, init_async_index: bool=False):
        """Initialize a BaseRouter object. Expected to be used as a base class only,
        not directly instantiated.

        :param encoder: The encoder to use.
        :type encoder: Optional[DenseEncoder]
        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        :param llm: The LLM to use.
        :type llm: Optional[BaseLLM]
        :param routes: The routes to use.
        :type routes: Optional[List[Route]]
        :param index: The index to use.
        :type index: Optional[BaseIndex]
        :param top_k: The number of routes to return.
        :type top_k: int
        :param aggregation: The aggregation method to use.
        :type aggregation: str
        :param auto_sync: The auto sync mode to use.
        :type auto_sync: Optional[str]
        """
        routes = routes.copy() if routes else []
        super().__init__(encoder=encoder, sparse_encoder=sparse_encoder, llm=llm, routes=routes, index=index, top_k=top_k, aggregation=aggregation, auto_sync=auto_sync)
        self.encoder = self._get_encoder(encoder=encoder)
        self.sparse_encoder = self._get_sparse_encoder(sparse_encoder=sparse_encoder)
        self.llm = llm
        self.routes = routes
        self.index = self._get_index(index=index)
        self._set_score_threshold()
        self.top_k = top_k
        if self.top_k < 1:
            raise ValueError(f'top_k needs to be >= 1, but was: {self.top_k}.')
        self.aggregation = aggregation
        if self.aggregation not in ['sum', 'mean', 'max']:
            raise ValueError(f"Unsupported aggregation method chosen: {aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'.")
        self.aggregation_method = self._set_aggregation_method(self.aggregation)
        if isinstance(self.index, PostgresIndex):
            self.auto_sync = 'local'
        else:
            self.auto_sync = auto_sync
        for route in self.routes:
            if route.score_threshold is None:
                route.score_threshold = self.score_threshold
        if not init_async_index:
            self._init_index_state()

    def _get_index(self, index: Optional[BaseIndex]) -> BaseIndex:
        """Get the index to use.

        :param index: The index to use.
        :type index: Optional[BaseIndex]
        :return: The index to use.
        :rtype: BaseIndex
        """
        if index is None:
            logger.warning('No index provided. Using default LocalIndex.')
            index = LocalIndex()
        else:
            index = index
        return index

    def _get_encoder(self, encoder: Optional[DenseEncoder]) -> DenseEncoder:
        """Get the dense encoder to be used for creating dense vector embeddings.

        :param encoder: The encoder to use.
        :type encoder: Optional[DenseEncoder]
        :return: The encoder to use.
        :rtype: DenseEncoder
        """
        if encoder is None:
            logger.warning('No encoder provided. Using default OpenAIEncoder.')
            encoder = OpenAIEncoder()
        else:
            encoder = encoder
        return encoder

    def _get_sparse_encoder(self, sparse_encoder: Optional[SparseEncoder]) -> Optional[SparseEncoder]:
        """Get the sparse encoder to be used for creating sparse vector embeddings.

        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        :return: The sparse encoder to use.
        :rtype: Optional[SparseEncoder]
        """
        if sparse_encoder is None:
            return None
        raise NotImplementedError(f'Sparse encoder not implemented for {self.__class__.__name__}')

    def _init_index_state(self):
        """Initializes an index (where required) and runs auto_sync if active."""
        if self.index.dimensions is None:
            dims = len(self.encoder(['test'])[0])
            self.index.dimensions = dims
        if isinstance(self.index, PineconeIndex) or isinstance(self.index, PostgresIndex):
            self.index.index = self.index._init_index(force_create=True)
        if self.auto_sync:
            local_utterances = self.to_config().to_utterances()
            remote_utterances = self.index.get_utterances(include_metadata=True)
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
            sync_strategy = diff.get_sync_strategy(self.auto_sync)
            self._execute_sync_strategy(sync_strategy)

    async def _async_init_index_state(self):
        """Asynchronously initializes an index (where required) and runs auto_sync if active."""
        if self.index is None or self.index.dimensions is None:
            dims = len(self.encoder(['test'])[0])
            self.index.dimensions = dims
        if isinstance(self.index, PineconeIndex) or isinstance(self.index, PostgresIndex):
            await self.index._init_async_index(force_create=True)
        if self.auto_sync:
            local_utterances = self.to_config().to_utterances()
            remote_utterances = await self.index.aget_utterances(include_metadata=True)
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
            sync_strategy = diff.get_sync_strategy(self.auto_sync)
            await self._async_execute_sync_strategy(sync_strategy)

    def _set_score_threshold(self):
        """Set the score threshold for the layer based on the encoder
        score threshold.

        When no score threshold is used a default `None` value
        is used, which means that a route will always be returned when
        the layer is called."""
        if self.encoder.score_threshold is not None:
            self.score_threshold = self.encoder.score_threshold
            if self.score_threshold is None:
                logger.warning("No score threshold value found in encoder. Using the default 'None' value can lead to unexpected results.")

    def check_for_matching_routes(self, top_class: str) -> Optional[Route]:
        """Check for a matching route in the routes list.

        :param top_class: The top class to check for.
        :type top_class: str
        :return: The matching route if found, otherwise None.
        :rtype: Optional[Route]
        """
        matching_route = next((route for route in self.routes if route.name == top_class), None)
        if matching_route is None:
            logger.error(f'No route found with name {top_class}. Check to see if any Routes have been defined.')
            return None
        return matching_route

    def __call__(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, simulate_static: bool=False, route_filter: Optional[List[str]]=None, limit: int | None=1) -> RouteChoice | List[RouteChoice]:
        """Call the router to get a route choice.

        :param text: The text to route.
        :type text: Optional[str]
        :param vector: The vector to route.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | List[RouteChoice]
        """
        if not self.index.is_ready():
            raise ValueError('Index is not ready.')
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector = self._encode(text=[text], input_type='queries')
        vector = xq_reshape(vector)
        scores, routes = self.index.query(vector=vector[0], top_k=self.top_k, route_filter=route_filter)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return self._pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    def _pass_routes(self, scored_routes: List[Tuple[str, float, List[float]]], simulate_static: bool, text: Optional[str], limit: int | None) -> RouteChoice | list[RouteChoice]:
        """Returns a list of RouteChoice objects that passed the thresholds set.

        :param scored_routes: The scored routes to pass.
        :type scored_routes: List[Tuple[str, float, List[float]]]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param text: The text to route.
        :type text: Optional[str]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | list[RouteChoice]
        """
        passed_routes: list[RouteChoice] = []
        for route_name, total_score, scores in scored_routes:
            route = self.check_for_matching_routes(top_class=route_name)
            if route is None:
                continue
            if (current_threshold := (route.score_threshold if route.score_threshold is not None else self.score_threshold)):
                passed = total_score >= current_threshold
            else:
                passed = True
            if passed and route is not None and (not simulate_static):
                if route.function_schemas and text is None:
                    raise ValueError('Route has a function schema, but no text was provided.')
                if route.function_schemas and (not isinstance(route.llm, BaseLLM)):
                    if not self.llm:
                        logger.warning('No LLM provided for dynamic route, will use OpenAI LLM default. Ensure API key is set in OPENAI_API_KEY environment variable.')
                        self.llm = OpenAILLM()
                        route.llm = self.llm
                    else:
                        route.llm = self.llm
                route_choice = route(query=text)
                if route_choice is not None and route_choice.similarity_score is None:
                    route_choice.similarity_score = total_score
                passed_routes.append(route_choice)
            elif passed and route is not None and simulate_static:
                passed_routes.append(RouteChoice(name=route.name, function_call=None, similarity_score=None))
            if limit is None:
                continue
            if len(passed_routes) >= limit:
                if limit == 1:
                    return passed_routes[0]
                else:
                    return passed_routes
        if len(passed_routes) == 1:
            return passed_routes[0]
        elif len(passed_routes) > 1:
            return passed_routes
        else:
            return RouteChoice()

    async def _async_pass_routes(self, scored_routes: List[Tuple[str, float, List[float]]], simulate_static: bool, text: Optional[str], limit: int | None) -> RouteChoice | list[RouteChoice]:
        """Returns a list of RouteChoice objects that passed the thresholds set. Runs any
        dynamic route calls asynchronously. If there are no dynamic routes this method is
        equivalent to _pass_routes.

        :param scored_routes: The scored routes to pass.
        :type scored_routes: List[Tuple[str, float, List[float]]]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param text: The text to route.
        :type text: Optional[str]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :return: The route choice.
        :rtype: RouteChoice | list[RouteChoice]
        """
        passed_routes: list[RouteChoice] = []
        for route_name, total_score, scores in scored_routes:
            route = self.check_for_matching_routes(top_class=route_name)
            if route is None:
                continue
            if (current_threshold := (route.score_threshold if route.score_threshold is not None else self.score_threshold)):
                passed = total_score >= current_threshold
            else:
                passed = True
            if passed and route is not None and (not simulate_static):
                if route.function_schemas and text is None:
                    raise ValueError('Route has a function schema, but no text was provided.')
                if route.function_schemas and (not isinstance(route.llm, BaseLLM)):
                    if not self.llm:
                        logger.warning('No LLM provided for dynamic route, will use OpenAI LLM default. Ensure API key is set in OPENAI_API_KEY environment variable.')
                        self.llm = OpenAILLM()
                        route.llm = self.llm
                    else:
                        route.llm = self.llm
                route_choice = await route.acall(query=text)
                if route_choice is not None and route_choice.similarity_score is None:
                    route_choice.similarity_score = total_score
                passed_routes.append(route_choice)
            elif passed and route is not None and simulate_static:
                passed_routes.append(RouteChoice(name=route.name, function_call=None, similarity_score=None))
            if limit is None:
                continue
            if len(passed_routes) >= limit:
                if limit == 1:
                    return passed_routes[0]
                else:
                    return passed_routes
        if len(passed_routes) == 1:
            return passed_routes[0]
        elif len(passed_routes) > 1:
            return passed_routes
        else:
            return RouteChoice()

    async def acall(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, limit: int | None=1, simulate_static: bool=False, route_filter: Optional[List[str]]=None) -> RouteChoice | list[RouteChoice]:
        """Asynchronously call the router to get a route choice.

        :param text: The text to route.
        :type text: Optional[str]
        :param vector: The vector to route.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route (ie avoid dynamic route
            LLM calls during fit or evaluate).
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if not await self.index.ais_ready():
            await self._async_init_index_state()
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector = await self._async_encode(text=[text], input_type='queries')
        vector = xq_reshape(vector)
        scores, routes = await self.index.aquery(vector=vector[0], top_k=self.top_k, route_filter=route_filter)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return await self._async_pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    def _index_ready(self) -> bool:
        """Method to check if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        if self.index.index is None or self.routes is None:
            return False
        if isinstance(self.index, QdrantIndex):
            info = self.index.describe()
            if info.vectors == 0:
                return False
        return True

    def sync(self, sync_mode: str, force: bool=False, wait: int=0) -> List[str]:
        """Runs a sync of the local routes with the remote index.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :param force: Whether to force the sync even if the local and remote
            hashes already match. Defaults to False.
        :type force: bool, optional
        :param wait: The number of seconds to wait for the index to be unlocked
        before proceeding with the sync. If set to 0, will raise an error if
        index is already locked/unlocked.
        :type wait: int
        :return: A list of diffs describing the addressed differences between
            the local and remote route layers.
        :rtype: List[str]
        """
        if not force and self.is_synced():
            logger.warning('Local and remote route layers are already synchronized.')
            local_utterances = self.to_config().to_utterances()
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=local_utterances)
            return diff.to_utterance_str()
        try:
            diff_utt_str: list[str] = []
            _ = self.index.lock(value=True, wait=wait)
            try:
                local_utterances = self.to_config().to_utterances()
                remote_utterances = self.index.get_utterances(include_metadata=True)
                diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
                sync_strategy = diff.get_sync_strategy(sync_mode=sync_mode)
                self._execute_sync_strategy(sync_strategy)
                diff_utt_str = diff.to_utterance_str()
            except Exception as e:
                logger.error(f'Failed to create diff: {e}')
                raise e
            finally:
                _ = self.index.lock(value=False)
        except Exception as e:
            logger.error(f'Failed to lock index for sync: {e}')
            raise e
        return diff_utt_str

    async def async_sync(self, sync_mode: str, force: bool=False, wait: int=0) -> List[str]:
        """Runs a sync of the local routes with the remote index.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :param force: Whether to force the sync even if the local and remote
            hashes already match. Defaults to False.
        :type force: bool, optional
        :param wait: The number of seconds to wait for the index to be unlocked
        before proceeding with the sync. If set to 0, will raise an error if
        index is already locked/unlocked.
        :type wait: int
        :return: A list of diffs describing the addressed differences between
            the local and remote route layers.
        :rtype: List[str]
        """
        if not force and await self.async_is_synced():
            logger.warning('Local and remote route layers are already synchronized.')
            local_utterances = self.to_config().to_utterances()
            diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=local_utterances)
            return diff.to_utterance_str()
        try:
            diff_utt_str: list[str] = []
            _ = await self.index.alock(value=True, wait=wait)
            try:
                local_utterances = self.to_config().to_utterances()
                remote_utterances = await self.index.aget_utterances(include_metadata=True)
                diff = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
                sync_strategy = diff.get_sync_strategy(sync_mode=sync_mode)
                await self._async_execute_sync_strategy(sync_strategy)
                diff_utt_str = diff.to_utterance_str()
            except Exception as e:
                logger.error(f'Failed to create diff: {e}')
                raise e
            finally:
                _ = await self.index.alock(value=False)
        except Exception as e:
            logger.error(f'Failed to lock index for sync: {e}')
            raise e
        return diff_utt_str

    def _execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            self.index._remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            self.index.add(embeddings=self.encoder(utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        self._write_hash()

    async def _async_execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            await self.index._async_remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            await self.index.aadd(embeddings=await self.encoder.acall(docs=utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        await self._async_write_hash()

    def _local_upsert(self, utterances: List[Utterance]):
        """Adds new routes to the SemanticRouter.

        :param utterances: The utterances to add to the local SemanticRouter.
        :type utterances: List[Utterance]
        """
        new_routes = {route.name: route for route in self.routes}
        for utt_obj in utterances:
            if utt_obj.route not in new_routes.keys():
                new_routes[utt_obj.route] = Route(name=utt_obj.route, utterances=[utt_obj.utterance], function_schemas=utt_obj.function_schemas, metadata=utt_obj.metadata)
            else:
                if utt_obj.utterance not in new_routes[utt_obj.route].utterances:
                    new_routes[utt_obj.route].utterances.append(utt_obj.utterance)
                new_routes[utt_obj.route].function_schemas = utt_obj.function_schemas
                new_routes[utt_obj.route].metadata = utt_obj.metadata
        self.routes = list(new_routes.values())

    def _local_delete(self, utterances: List[Utterance]):
        """Deletes routes from the local SemanticRouter.

        :param utterances: The utterances to delete from the local SemanticRouter.
        :type utterances: List[Utterance]
        """
        route_dict: dict[str, List[str]] = {}
        for utt in utterances:
            route_dict.setdefault(utt.route, []).append(utt.utterance)
        new_routes = []
        for route in self.routes:
            if route.name in route_dict.keys():
                new_utterances = list(set(route.utterances) - set(route_dict[route.name]))
                if len(new_utterances) == 0:
                    continue
                else:
                    new_routes.append(Route(name=route.name, utterances=new_utterances, function_schemas=route.function_schemas, metadata=route.metadata))
            else:
                new_routes.append(route)
        self.routes = new_routes

    def __str__(self):
        return f'{self.__class__.__name__}(encoder={self.encoder}, score_threshold={self.score_threshold}, routes={self.routes})'

    @classmethod
    def from_json(cls, file_path: str):
        """Load a RouterConfig from a JSON file.

        :param file_path: The path to the JSON file.
        :type file_path: str
        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        config = RouterConfig.from_file(file_path)
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from JSON.')

    @classmethod
    def from_yaml(cls, file_path: str):
        """Load a RouterConfig from a YAML file.

        :param file_path: The path to the YAML file.
        :type file_path: str
        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        config = RouterConfig.from_file(file_path)
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from YAML.')

    @classmethod
    def from_config(cls, config: RouterConfig, index: Optional[BaseIndex]=None):
        """Create a Router from a RouterConfig object.

        :param config: The RouterConfig object.
        :type config: RouterConfig
        :param index: The index to use.
        :type index: Optional[BaseIndex]
        """
        encoder = AutoEncoder(type=config.encoder_type, name=config.encoder_name).model
        if isinstance(encoder, DenseEncoder):
            return cls(encoder=encoder, routes=config.routes, index=index)
        else:
            raise ValueError(f'{type(encoder)} not supported for loading from config.')

    def add(self, routes: List[Route] | Route):
        """Add a route to the local SemanticRouter and index.

        :param route: The route to add.
        :type route: Route
        """
        raise NotImplementedError('This method must be implemented by subclasses.')

    async def aadd(self, routes: List[Route] | Route):
        """Add a route to the local SemanticRouter and index asynchronously.

        :param route: The route to add.
        :type route: Route
        """
        logger.warning('Async method not implemented.')
        return self.add(routes)

    def list_route_names(self) -> List[str]:
        return [route.name for route in self.routes]

    def update(self, name: str, threshold: Optional[float]=None, utterances: Optional[List[str]]=None):
        """Updates the route specified in name. Allows the update of
        threshold and/or utterances. If no values are provided via the
        threshold or utterances parameters, those fields are not updated.
        If neither field is provided raises a ValueError.

        The name must exist within the local SemanticRouter, if not a
        KeyError will be raised.

        :param name: The name of the route to update.
        :type name: str
        :param threshold: The threshold to update.
        :type threshold: Optional[float]
        :param utterances: The utterances to update.
        :type utterances: Optional[List[str]]
        """
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if threshold is None and utterances is None:
            raise ValueError("At least one of 'threshold' or 'utterances' must be provided.")
        if utterances:
            raise NotImplementedError('The update method cannot be used for updating utterances yet.')
        route = self.get(name)
        if route:
            if threshold:
                old_threshold = route.score_threshold
                route.score_threshold = threshold
                logger.info(f"Updated threshold for route '{route.name}' from {old_threshold} to {threshold}")
        else:
            raise ValueError(f"Route '{name}' not found. Nothing updated.")
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def delete(self, route_name: str):
        """Deletes a route given a specific route name.

        :param route_name: the name of the route to be deleted
        :type str:
        """
        if self.index._is_locked():
            raise ValueError('Index is locked. Cannot delete route.')
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if route_name not in [route.name for route in self.routes]:
            err_msg = f'Route `{route_name}` not found in {self.__class__.__name__}'
            logger.warning(err_msg)
            try:
                self.index.delete(route_name=route_name)
            except Exception as e:
                logger.error(f'Failed to delete route from the index: {e}')
        else:
            self.routes = [route for route in self.routes if route.name != route_name]
            self.index.delete(route_name=route_name)
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    async def adelete(self, route_name: str):
        """Deletes a route given a specific route name asynchronously.

        :param route_name: the name of the route to be deleted
        :type str:
        """
        if await self.index._ais_locked():
            raise ValueError('Index is locked. Cannot delete route.')
        current_local_hash = self._get_hash()
        current_remote_hash = await self.index._async_read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if route_name not in [route.name for route in self.routes]:
            err_msg = f'Route `{route_name}` not found in {self.__class__.__name__}'
            logger.warning(err_msg)
            try:
                await self.index.adelete(route_name=route_name)
            except Exception as e:
                logger.error(f'Failed to delete route from the index: {e}')
        else:
            self.routes = [route for route in self.routes if route.name != route_name]
            await self.index.adelete(route_name=route_name)
        if current_local_hash.value == current_remote_hash.value:
            await self._async_write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def _refresh_routes(self):
        """Pulls out the latest routes from the index.

        Not yet implemented for BaseRouter.
        """
        raise NotImplementedError('This method has not yet been implemented.')
        route_mapping = {route.name: route for route in self.routes}
        index_routes = self.index.get_utterances()
        new_routes_names = []
        new_routes = []
        for route_name, utterance in index_routes:
            if route_name in route_mapping:
                if route_name not in new_routes_names:
                    existing_route = route_mapping[route_name]
                    new_routes.append(existing_route)
                new_routes.append(Route(name=route_name, utterances=[utterance]))
            route = route_mapping[route_name]
            self.routes.append(route)

    def _get_hash(self) -> ConfigParameter:
        """Get the hash of the current routes.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        return config.get_hash()

    def _write_hash(self) -> ConfigParameter:
        """Write the hash of the current routes to the index.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        hash_config = config.get_hash()
        self.index._write_config(config=hash_config)
        return hash_config

    async def _async_write_hash(self) -> ConfigParameter:
        """Write the hash of the current routes to the index asynchronously.

        :return: The hash of the current routes.
        :rtype: ConfigParameter
        """
        config = self.to_config()
        hash_config = config.get_hash()
        await self.index._async_write_config(config=hash_config)
        return hash_config

    def is_synced(self) -> bool:
        """Check if the local and remote route layer instances are
        synchronized.

        :return: True if the local and remote route layers are synchronized,
            False otherwise.
        :rtype: bool
        """
        local_hash = self._get_hash()
        remote_hash = self.index._read_hash()
        if local_hash.value == remote_hash.value:
            return True
        else:
            return False

    async def async_is_synced(self) -> bool:
        """Check if the local and remote route layer instances are
        synchronized asynchronously.

        :return: True if the local and remote route layers are synchronized,
            False otherwise.
        :rtype: bool
        """
        local_hash = self._get_hash()
        remote_hash = await self.index._async_read_hash()
        if local_hash.value == remote_hash.value:
            return True
        else:
            return False

    def get_utterance_diff(self, include_metadata: bool=False) -> List[str]:
        """Get the difference between the local and remote utterances. Returns
        a list of strings showing what is different in the remote when compared
        to the local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the diff.
        :type include_metadata: bool
        :return: A list of strings showing the difference between the local and remote
            utterances.
        :rtype: List[str]
        """
        remote_utterances = self.index.get_utterances(include_metadata=include_metadata)
        local_utterances = self.to_config().to_utterances()
        diff_obj = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
        return diff_obj.to_utterance_str(include_metadata=include_metadata)

    async def aget_utterance_diff(self, include_metadata: bool=False) -> List[str]:
        """Get the difference between the local and remote utterances asynchronously.
        Returns a list of strings showing what is different in the remote when
        compared to the local. For example:

        ["  route1: utterance1",
         "  route1: utterance2",
         "- route2: utterance3",
         "- route2: utterance4"]

        Tells us that the remote is missing "route2: utterance3" and "route2:
        utterance4", which do exist locally. If we see:

        ["  route1: utterance1",
         "  route1: utterance2",
         "+ route2: utterance3",
         "+ route2: utterance4"]

        This diff tells us that the remote has "route2: utterance3" and
        "route2: utterance4", which do not exist locally.

        :param include_metadata: Whether to include metadata in the diff.
        :type include_metadata: bool
        :return: A list of strings showing the difference between the local and remote
            utterances.
        :rtype: List[str]
        """
        remote_utterances = await self.index.aget_utterances(include_metadata=include_metadata)
        local_utterances = self.to_config().to_utterances()
        diff_obj = UtteranceDiff.from_utterances(local_utterances=local_utterances, remote_utterances=remote_utterances)
        return diff_obj.to_utterance_str(include_metadata=include_metadata)

    def _extract_routes_details(self, routes: List[Route], include_metadata: bool=False) -> Tuple:
        """Extract the routes details.

        :param routes: The routes to extract the details from.
        :type routes: List[Route]
        :param include_metadata: Whether to include metadata in the details.
        :type include_metadata: bool
        :return: A tuple of the route names, utterances, and function schemas.
        """
        route_names = [route.name for route in routes for _ in route.utterances]
        utterances = [utterance for route in routes for utterance in route.utterances]
        function_schemas = [route.function_schemas[0] if route.function_schemas and len(route.function_schemas) > 0 else {} for route in routes for _ in route.utterances]
        if include_metadata:
            metadata = [route.metadata for route in routes for _ in route.utterances]
            return (route_names, utterances, function_schemas, metadata)
        return (route_names, utterances, function_schemas)

    def _encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Generates embeddings for a given text.

        Must be implemented by a subclass.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The embeddings of the text.
        :rtype: Any
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    async def _async_encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Asynchronously generates embeddings for a given text.

        Must be implemented by a subclass.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The embeddings of the text.
        :rtype: Any
        """
        raise NotImplementedError('This method should be implemented by subclasses.')

    def _set_aggregation_method(self, aggregation: str='sum'):
        """Set the aggregation method.

        :param aggregation: The aggregation method to use.
        :type aggregation: str
        :return: The aggregation method.
        :rtype: Callable
        """
        if aggregation == 'sum':
            return lambda x: sum(x)
        elif aggregation == 'mean':
            return lambda x: np.mean(x)
        elif aggregation == 'max':
            return lambda x: max(x)
        else:
            raise ValueError(f"Unsupported aggregation method chosen: {aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'.")

    def _score_routes(self, query_results: list[dict]) -> list[tuple[str, float, list[float]]]:
        """Score the routes based on the query results.

        :param query_results: The query results to score.
        :type query_results: List[Dict]
        :return: A tuple of routes, their total scores, and their individual scores.
        """
        scores_by_class = self.group_scores_by_class(query_results)
        if self.aggregation_method is None:
            raise ValueError('self.aggregation_method is not set.')
        total_scores = [(route, self.aggregation_method(scores), scores) for route, scores in scores_by_class.items()]
        total_scores.sort(key=lambda x: x[1], reverse=True)
        return total_scores

    @deprecated('Direct use of `_semantic_classify` is deprecated. Use `__call__` or `acall` instead.')
    def _semantic_classify(self, query_results: List[Dict]) -> Tuple[str, List[float]]:
        """Classify the query results into a single class based on the highest total score.
        If no classification is found, return an empty string and an empty list.

        :param query_results: The query results to classify. Expected format is a list of
        dictionaries with "route" and "score" keys.
        :type query_results: List[Dict]
        :return: A tuple containing the top class and its associated scores.
        :rtype: Tuple[str, List[float]]
        """
        top_class, top_score, scores = self._score_routes(query_results)[0]
        if top_class is not None:
            return (str(top_class), scores)
        else:
            logger.warning('No classification found for semantic classifier.')
            return ('', [])

    def get(self, name: str) -> Optional[Route]:
        """Get a route by name.

        :param name: The name of the route to get.
        :type name: str
        :return: The route.
        :rtype: Optional[Route]
        """
        for route in self.routes:
            if route.name == name:
                return route
        logger.error(f'Route `{name}` not found')
        return None

    def group_scores_by_class(self, query_results: List[Dict]) -> Dict[str, List[float]]:
        """Group the scores by class.

        :param query_results: The query results to group. Expected format is a list of
        dictionaries with "route" and "score" keys.
        :type query_results: List[Dict]
        :return: A dictionary of route names and their associated scores.
        :rtype: Dict[str, List[float]]
        """
        scores_by_class: Dict[str, List[float]] = {}
        for result in query_results:
            score = result['score']
            route = result['route']
            if route in scores_by_class:
                scores_by_class[route].append(score)
            else:
                scores_by_class[route] = [score]
        return scores_by_class

    def _update_thresholds(self, route_thresholds: Optional[Dict[str, float]]=None):
        """Update the score thresholds for each route using a dictionary of
        route names and thresholds.

        :param route_thresholds: A dictionary of route names and thresholds.
        :type route_thresholds: Dict[str, float] | None
        """
        if route_thresholds:
            for route, threshold in route_thresholds.items():
                self.set_threshold(threshold=threshold, route_name=route)

    def set_threshold(self, threshold: float, route_name: str | None=None):
        """Set the score threshold for a specific route or all routes. A `threshold` of 0.0
        will mean that the route will be returned no matter how low it scores whereas
        a threshold of 1.0 will mean that a route must contain an exact utterance match
        to be returned.

        :param threshold: The threshold to set.
        :type threshold: float
        :param route_name: The name of the route to set the threshold for. If None, the
        threshold will be set for all routes.
        :type route_name: str | None
        """
        if route_name is None:
            for route in self.routes:
                route.score_threshold = threshold
            self.score_threshold = threshold
        else:
            route_get: Route | None = self.get(route_name)
            if route_get is not None:
                route_get.score_threshold = threshold
            else:
                logger.error(f'Route `{route_name}` not found')

    def to_config(self) -> RouterConfig:
        """Convert the router to a RouterConfig object.

        :return: The RouterConfig object.
        :rtype: RouterConfig
        """
        return RouterConfig(encoder_type=self.encoder.type, encoder_name=self.encoder.name, routes=self.routes)

    def to_json(self, file_path: str):
        """Convert the router to a JSON file.

        :param file_path: The path to the JSON file.
        :type file_path: str
        """
        config = self.to_config()
        config.to_file(file_path)

    def to_yaml(self, file_path: str):
        """Convert the router to a YAML file.

        :param file_path: The path to the YAML file.
        :type file_path: str
        """
        config = self.to_config()
        config.to_file(file_path)

    def get_thresholds(self) -> Dict[str, float]:
        """Get the score thresholds for each route.

        :return: A dictionary of route names and their associated thresholds.
        :rtype: Dict[str, float]
        """
        thresholds = {route.name: route.score_threshold or self.score_threshold or 0.0 for route in self.routes}
        return thresholds

    def fit(self, X: List[str], y: List[str], batch_size: int=500, max_iter: int=500, local_execution: bool=False):
        """Fit the router to the data. Works best with a large number of examples for each
        route and with many `None` utterances.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for fitting.
        :type batch_size: int
        :param max_iter: The maximum number of iterations to use for fitting.
        :type max_iter: int
        :param local_execution: Whether to execute the fitting locally.
        :type local_execution: bool
        """
        original_index = self.index
        if local_execution:
            from semantic_router.index.local import LocalIndex
            remote_utterances = self.index.get_utterances(include_metadata=True)
            routes = []
            utterances = []
            metadata = []
            for utterance in remote_utterances:
                routes.append(utterance.route)
                utterances.append(utterance.utterance)
                metadata.append(utterance.metadata)
            embeddings = self.encoder(utterances)
            self.index = LocalIndex()
            self.index.add(embeddings=embeddings, routes=routes, utterances=utterances, metadata_list=metadata)
        Xq: List[List[float]] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb = np.array(self.encoder(X[i:i + batch_size]))
            Xq.extend(emb)
        best_acc = self._vec_evaluate(Xq_d=np.array(Xq), y=y)
        best_thresholds = self.get_thresholds()
        for _ in (pbar := tqdm(range(max_iter), desc='Training')):
            pbar.set_postfix({'acc': round(best_acc, 2)})
            thresholds = threshold_random_search(route_layer=self, search_range=0.8)
            self._update_thresholds(route_thresholds=thresholds)
            acc = self._vec_evaluate(Xq_d=Xq, y=y)
            if acc > best_acc:
                best_acc = acc
                best_thresholds = thresholds
        self._update_thresholds(route_thresholds=best_thresholds)
        if local_execution:
            self.index = original_index

    def evaluate(self, X: List[str], y: List[str], batch_size: int=500) -> float:
        """Evaluate the accuracy of the route selection.

        :param X: The input data.
        :type X: List[str]
        :param y: The output data.
        :type y: List[str]
        :param batch_size: The batch size to use for evaluation.
        :type batch_size: int
        :return: The accuracy of the route selection.
        :rtype: float
        """
        Xq: List[List[float]] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb = np.array(self.encoder(X[i:i + batch_size]))
            Xq.extend(emb)
        accuracy = self._vec_evaluate(Xq_d=np.array(Xq), y=y)
        return accuracy

    def _vec_evaluate(self, Xq_d: Union[List[float], Any], y: List[str], **kwargs) -> float:
        """Evaluate the accuracy of the route selection.

        :param Xq_d: The input data.
        :type Xq_d: Union[List[float], Any]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
        correct = 0
        for xq, target_route in zip(Xq_d, y):
            route_choice = self(vector=xq, simulate_static=True)
            if isinstance(route_choice, list):
                route_name = route_choice[0].name
            else:
                route_name = route_choice.name
            if route_name == target_route:
                correct += 1
        accuracy = correct / len(Xq_d)
        return accuracy

    def _get_route_names(self) -> List[str]:
        """Get the names of the routes.

        :return: The names of the routes.
        :rtype: List[str]
        """
        return [route.name for route in self.routes]

    @deprecated('Use `__call__` or `acall` with `limit=None` instead.')
    def _semantic_classify_multiple_routes(self, query_results: list[dict]) -> list[dict]:
        """Classify the query results into a list of routes.

        :param query_results: The query results to classify.
        :type query_results: List[Dict]
        :return: Most similar results with scores.
        :rtype list[dict]:
        """
        raise NotImplementedError('This method has been deprecated. Use `__call__` or `acall` with `limit=None` instead.')

def _set_aggregation_method(self, aggregation: str='sum'):
    """Set the aggregation method.

        :param aggregation: The aggregation method to use.
        :type aggregation: str
        :return: The aggregation method.
        :rtype: Callable
        """
    if aggregation == 'sum':
        return lambda x: sum(x)
    elif aggregation == 'mean':
        return lambda x: np.mean(x)
    elif aggregation == 'max':
        return lambda x: max(x)
    else:
        raise ValueError(f"Unsupported aggregation method chosen: {aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'.")

class TestBaseTokenizer:

    def test_abstract_methods(self):

        class ConcreteTokenizer(BaseTokenizer):
            pass
        tokenizer = ConcreteTokenizer()
        with pytest.raises(NotImplementedError):
            _ = tokenizer.vocab_size
        with pytest.raises(NotImplementedError):
            _ = tokenizer.config
        with pytest.raises(NotImplementedError):
            tokenizer.tokenize('test')

    def test_save_load(self):

        class ConcreteTokenizer(BaseTokenizer):

            def __init__(self, test_param) -> None:
                self.test_param = test_param
                super().__init__()

            @property
            def vocab_size(self):
                return 100

            @property
            def config(self):
                return {'test_param': self.test_param}

            def tokenize(self, texts, pad=True):
                pass
        with tempfile.NamedTemporaryFile(suffix='.json') as tmp:
            tokenizer = ConcreteTokenizer(test_param='value')
            tokenizer.save(tmp.name)
            loaded = ConcreteTokenizer.load(tmp.name)
            assert isinstance(loaded, ConcreteTokenizer)
            with open(tmp.name) as f:
                saved_config = json.load(f)
            assert saved_config == {'test_param': 'value'}

def test_abstract_methods(self):

    class ConcreteTokenizer(BaseTokenizer):
        pass
    tokenizer = ConcreteTokenizer()
    with pytest.raises(NotImplementedError):
        _ = tokenizer.vocab_size
    with pytest.raises(NotImplementedError):
        _ = tokenizer.config
    with pytest.raises(NotImplementedError):
        tokenizer.tokenize('test')

class TestPretrainedTokenizer:

    @pytest.fixture
    def tokenizer(self):
        return PretrainedTokenizer('google-bert/bert-base-uncased')

    def test_initialization(self, tokenizer):
        assert tokenizer.model_ident == 'google-bert/bert-base-uncased'
        assert tokenizer.add_special_tokens is False
        assert tokenizer.pad is True

    def test_vocab_size(self, tokenizer):
        assert isinstance(tokenizer.vocab_size, int)
        assert tokenizer.vocab_size > 0

    def test_config(self, tokenizer):
        config = tokenizer.config
        assert isinstance(config, dict)
        assert 'model_ident' in config
        assert 'add_special_tokens' in config
        assert 'pad' in config

    def test_tokenize_single_text(self, tokenizer):
        text = 'Hello world'
        tokens = tokenizer.tokenize(text)
        assert isinstance(tokens, np.ndarray)
        assert tokens.ndim == 2
        assert tokens.shape[0] == 1
        assert tokens.shape[1] > 0

    def test_tokenize_multiple_texts(self, tokenizer):
        texts = ['Hello world', 'Testing tokenization']
        tokens = tokenizer.tokenize(texts)
        assert isinstance(tokens, np.ndarray)
        assert tokens.ndim == 2
        assert tokens.shape[0] == 2

    def test_save_load_cycle(self, tokenizer):
        with tempfile.NamedTemporaryFile(suffix='.json') as tmp:
            tokenizer.save(tmp.name)
            loaded = PretrainedTokenizer.load(tmp.name)
            assert isinstance(loaded, PretrainedTokenizer)
            assert loaded.model_ident == tokenizer.model_ident
            assert loaded.add_special_tokens == tokenizer.add_special_tokens
            assert loaded.pad == tokenizer.pad

def test_tokenize_single_text(self, tokenizer):
    text = 'Hello world'
    tokens = tokenizer.tokenize(text)
    assert isinstance(tokens, np.ndarray)
    assert tokens.ndim == 2
    assert tokens.shape[0] == 1
    assert tokens.shape[1] > 0

def test_tokenize_multiple_texts(self, tokenizer):
    texts = ['Hello world', 'Testing tokenization']
    tokens = tokenizer.tokenize(texts)
    assert isinstance(tokens, np.ndarray)
    assert tokens.ndim == 2
    assert tokens.shape[0] == 2

class TestTfidfEncoder:

    def test_initialization(self, tfidf_encoder):
        assert tfidf_encoder.word_index == {}
        assert (tfidf_encoder.idf == np.array([])).all()

    def test_fit(self, tfidf_encoder):
        routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
        tfidf_encoder.fit(routes)
        assert tfidf_encoder.word_index != {}
        assert not np.array_equal(tfidf_encoder.idf, np.array([]))

    def test_call_method(self, tfidf_encoder):
        routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
        tfidf_encoder.fit(routes)
        result = tfidf_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sparse_emb.embedding, np.ndarray) for sparse_emb in result)), 'Each item in result should be an array'

    def test_call_method_no_docs_tfidf_encoder(self, tfidf_encoder):
        with pytest.raises(ValueError):
            tfidf_encoder([])

    def test_call_method_no_word(self, tfidf_encoder):
        routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
        tfidf_encoder.fit(routes)
        result = tfidf_encoder(['doc with fake word gta5jabcxyz'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sparse_emb.embedding, np.ndarray) for sparse_emb in result)), 'Each item in result should be an array'

    def test_fit_with_strings(self, tfidf_encoder):
        routes = ['test a', 'test b', 'test c']
        with pytest.raises(TypeError):
            tfidf_encoder.fit(routes)

    def test_call_method_with_uninitialized_model(self, tfidf_encoder):
        with pytest.raises(ValueError):
            tfidf_encoder(['test'])

    def test_compute_tf_no_word_index(self, tfidf_encoder):
        with pytest.raises(ValueError, match='Word index is not initialized.'):
            tfidf_encoder._compute_tf(['some docs'])

    def test_compute_tf_with_word_in_word_index(self, tfidf_encoder):
        routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
        tfidf_encoder.fit(routes)
        tf = tfidf_encoder._compute_tf(['some docs'])
        assert tf.shape == (1, len(tfidf_encoder.word_index))

    def test_compute_idf_no_word_index(self, tfidf_encoder):
        with pytest.raises(ValueError, match='Word index is not initialized.'):
            tfidf_encoder._compute_idf(['some docs'])

def test_compute_tf_no_word_index(self, tfidf_encoder):
    with pytest.raises(ValueError, match='Word index is not initialized.'):
        tfidf_encoder._compute_tf(['some docs'])

def test_compute_tf_with_word_in_word_index(self, tfidf_encoder):
    routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
    tfidf_encoder.fit(routes)
    tf = tfidf_encoder._compute_tf(['some docs'])
    assert tf.shape == (1, len(tfidf_encoder.word_index))

def test_compute_idf_no_word_index(self, tfidf_encoder):
    with pytest.raises(ValueError, match='Word index is not initialized.'):
        tfidf_encoder._compute_idf(['some docs'])

class TestHuggingFaceEncoder:

    def test_huggingface_encoder_import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                HuggingFaceEncoder()
        assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

    def test_huggingface_encoder_import_errors_torch(self):
        with patch.dict('sys.modules', {'torch': None}):
            with pytest.raises(ImportError) as error:
                HuggingFaceEncoder()
        assert 'Please install transformers to use HuggingFaceEncoder' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_mean_pooling(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        test_docs = ['This is a test', 'This is another test']
        embeddings = encoder(test_docs, pooling_strategy='mean')
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_docs)
        assert all((isinstance(embedding, list) for embedding in embeddings))
        assert all((len(embedding) > 0 for embedding in embeddings))

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_max_pooling(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        test_docs = ['This is a test', 'This is another test']
        embeddings = encoder(test_docs, pooling_strategy='max')
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_docs)
        assert all((isinstance(embedding, list) for embedding in embeddings))
        assert all((len(embedding) > 0 for embedding in embeddings))

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_huggingface_encoder_normalized_embeddings(self):
        encoder = HuggingFaceEncoder(name=test_model_name)
        docs = ['This is a test document.', 'Another test document.']
        unnormalized_embeddings = encoder(docs, normalize_embeddings=False)
        normalized_embeddings = encoder(docs, normalize_embeddings=True)
        assert len(unnormalized_embeddings) == len(normalized_embeddings)
        for unnormalized, normalized in zip(unnormalized_embeddings, normalized_embeddings):
            norm_unnormalized = np.linalg.norm(unnormalized, ord=2)
            norm_normalized = np.linalg.norm(normalized, ord=2)
            assert np.isclose(norm_normalized, 1.0)
            np.testing.assert_allclose(normalized, np.divide(unnormalized, norm_unnormalized), rtol=1e-05, atol=1e-05)

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_huggingface_encoder_normalized_embeddings(self):
    encoder = HuggingFaceEncoder(name=test_model_name)
    docs = ['This is a test document.', 'Another test document.']
    unnormalized_embeddings = encoder(docs, normalize_embeddings=False)
    normalized_embeddings = encoder(docs, normalize_embeddings=True)
    assert len(unnormalized_embeddings) == len(normalized_embeddings)
    for unnormalized, normalized in zip(unnormalized_embeddings, normalized_embeddings):
        norm_unnormalized = np.linalg.norm(unnormalized, ord=2)
        norm_normalized = np.linalg.norm(normalized, ord=2)
        assert np.isclose(norm_normalized, 1.0)
        np.testing.assert_allclose(normalized, np.divide(unnormalized, norm_unnormalized), rtol=1e-05, atol=1e-05)

def test_similarity_matrix__is_norm_max(ident_vector):
    """
    Using identical vectors should yield a maximum similarity of 1
    """
    index = np.repeat(np.atleast_2d(ident_vector), 3, axis=0)
    sim = similarity_matrix(ident_vector, index)
    assert sim.max() == 1.0

def test_similarity_matrix__is_norm_min(ident_vector):
    """
    Using orthogonal vectors should yield a minimum similarity of 0
    """
    orth_v = np.roll(np.atleast_2d(ident_vector), 1)
    index = np.repeat(orth_v, 3, axis=0)
    sim = similarity_matrix(ident_vector, index)
    assert sim.min() == 0.0

class TestBM25Encoder:

    def _sparse_to_vector(self, sparse_embedding, vocab_size):
        """Re-constructs the full (sparse_embedding.shape[0], vocab_size) array"""
        return (np.eye(vocab_size)[sparse_embedding[:, 0].astype(np.uint).tolist()] * np.atleast_2d(sparse_embedding[:, 1]).T).sum(axis=0)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
    def test_bm25_scoring(self, bm25_encoder):
        vocab_size = bm25_encoder._tokenizer.vocab_size
        expected = np.array([[0.0, 0.0, 0.54575, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.18864, 0.0, 0.67897, 0.0]])
        q_e = np.stack([self._sparse_to_vector(v.embedding, vocab_size=vocab_size) for v in bm25_encoder.encode_queries(QUERIES)])
        d_e = np.stack([self._sparse_to_vector(v.embedding, vocab_size=vocab_size) for v in bm25_encoder.encode_documents(UTTERANCES)])
        scores = q_e @ d_e.T
        assert np.allclose(scores, expected, rtol=0.0001), expected

def _sparse_to_vector(self, sparse_embedding, vocab_size):
    """Re-constructs the full (sparse_embedding.shape[0], vocab_size) array"""
    return (np.eye(vocab_size)[sparse_embedding[:, 0].astype(np.uint).tolist()] * np.atleast_2d(sparse_embedding[:, 1]).T).sum(axis=0)

