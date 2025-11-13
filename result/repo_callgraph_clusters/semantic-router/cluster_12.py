# Cluster 12

class SparseEmbedding(BaseModel):
    """Sparse embedding interface. Primarily uses numpy operations for faster
    operations.
    """
    embedding: np.ndarray
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_compact_array(cls, array: np.ndarray):
        """Create a SparseEmbedding object from a compact array.

        :param array: A compact array.
        :type array: np.ndarray
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
        if array.ndim != 2 or array.shape[1] != 2:
            raise ValueError(f'Expected a 2D array with 2 columns, got a {array.ndim}D array with {array.shape[1]} columns. Column 0 should contain index positions, and column 1 should contain respective values.')
        return cls(embedding=array)

    @classmethod
    def from_vector(cls, vector: np.ndarray):
        """Consumes an array of sparse vectors containing zero-values.

        :param vector: A sparse vector.
        :type vector: np.ndarray
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
        if vector.ndim != 1:
            raise ValueError(f'Expected a 1D array, got a {vector.ndim}D array.')
        return cls.from_compact_array(np.array([np.arange(len(vector)), vector]).T)

    @classmethod
    def from_aurelio(cls, embedding: BM25SparseEmbedding):
        """Create a SparseEmbedding object from an AurelioSparseEmbedding object.

        :param embedding: An AurelioSparseEmbedding object.
        :type embedding: BM25SparseEmbedding
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
        arr = np.array([embedding.indices, embedding.values]).T
        return cls.from_compact_array(arr)

    @classmethod
    def from_dict(cls, sparse_dict: dict):
        """Create a SparseEmbedding object from a dictionary.

        :param sparse_dict: A dictionary of sparse values.
        :type sparse_dict: dict
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
        arr = np.array([list(sparse_dict.keys()), list(sparse_dict.values())]).T
        return cls.from_compact_array(arr)

    @classmethod
    def from_pinecone_dict(cls, sparse_dict: dict):
        """Create a SparseEmbedding object from a Pinecone dictionary.

        :param sparse_dict: A Pinecone dictionary.
        :type sparse_dict: dict
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
        arr = np.array([sparse_dict['indices'], sparse_dict['values']]).T
        return cls.from_compact_array(arr)

    def to_dict(self):
        """Convert a SparseEmbedding object to a dictionary.

        :return: A dictionary of sparse values.
        :rtype: dict
        """
        return {i: v for i, v in zip(self.embedding[:, 0].astype(int), self.embedding[:, 1])}

    def to_pinecone(self):
        """Convert a SparseEmbedding object to a Pinecone dictionary.

        :return: A Pinecone dictionary.
        :rtype: dict
        """
        return {'indices': self.embedding[:, 0].astype(int).tolist(), 'values': self.embedding[:, 1].tolist()}

    def items(self):
        """Return a list of (index, value) tuples from the SparseEmbedding object.

        :return: A list of (index, value) tuples.
        :rtype: list
        """
        return [(i, v) for i, v in zip(self.embedding[:, 0].astype(int), self.embedding[:, 1])]

@classmethod
def from_vector(cls, vector: np.ndarray):
    """Consumes an array of sparse vectors containing zero-values.

        :param vector: A sparse vector.
        :type vector: np.ndarray
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
    if vector.ndim != 1:
        raise ValueError(f'Expected a 1D array, got a {vector.ndim}D array.')
    return cls.from_compact_array(np.array([np.arange(len(vector)), vector]).T)

@classmethod
def from_aurelio(cls, embedding: BM25SparseEmbedding):
    """Create a SparseEmbedding object from an AurelioSparseEmbedding object.

        :param embedding: An AurelioSparseEmbedding object.
        :type embedding: BM25SparseEmbedding
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
    arr = np.array([embedding.indices, embedding.values]).T
    return cls.from_compact_array(arr)

@classmethod
def from_dict(cls, sparse_dict: dict):
    """Create a SparseEmbedding object from a dictionary.

        :param sparse_dict: A dictionary of sparse values.
        :type sparse_dict: dict
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
    arr = np.array([list(sparse_dict.keys()), list(sparse_dict.values())]).T
    return cls.from_compact_array(arr)

@classmethod
def from_pinecone_dict(cls, sparse_dict: dict):
    """Create a SparseEmbedding object from a Pinecone dictionary.

        :param sparse_dict: A Pinecone dictionary.
        :type sparse_dict: dict
        :return: A SparseEmbedding object.
        :rtype: SparseEmbedding
        """
    arr = np.array([sparse_dict['indices'], sparse_dict['values']]).T
    return cls.from_compact_array(arr)

class PretrainedTokenizer(BaseTokenizer):
    """Wrapper for HuggingFace tokenizers, representing a pretrained tokenizer (i.e. bert-base-uncased).
    Extends the :class:`semantic_router.tokenizers.BaseTokenizer` class.

    :param tokenizer: Binding for HuggingFace Rust tokenizers
    :type tokenizer: class:`tokenizers.Tokenizer`
    :param add_special_tokens: Whether to accept special tokens from the tokenizer (i.e. `[PAD]`)
    :type add_special_tokens: bool
    :param pad: Whether to pad the input to a consistent length (using `[PAD]` tokens)
    :type pad: bool
    :param model_ident: HuggingFace ID of the model (i.e. `bert-base-uncased`)
    :type model_ident: str
    """
    add_special_tokens: bool
    pad: bool
    model_ident: str

    def __init__(self, model_ident: str, custom_normalizer: Any=None, add_special_tokens: bool=False, pad: bool=True) -> None:
        """Constructor method"""
        if importlib.util.find_spec('tokenizers') is None:
            raise ImportError("The 'tokenizers' package is required for PretrainedTokenizer but not installed. Please install it with `pip install tokenizers`.")
        from tokenizers import Tokenizer
        super().__init__()
        self.add_special_tokens = add_special_tokens
        self.model_ident = model_ident
        self.tokenizer = Tokenizer.from_pretrained(model_ident)
        self.pad = pad
        if custom_normalizer:
            self.tokenizer.normalizer = custom_normalizer
        if pad:
            self.tokenizer.enable_padding(direction='right', pad_id=0)

    @property
    def vocab_size(self):
        """Returns the vocabulary size of the tokenizer

        :return: Vocabulary size of tokenizer
        :rtype: int
        """
        return self.tokenizer.get_vocab_size()

    @property
    def config(self) -> dict:
        """The tokenizer config

        :return: dictionary of tokenizer config
        :rtype: dict
        """
        return {'model_ident': self.model_ident, 'add_special_tokens': self.add_special_tokens, 'pad': self.pad}

    def tokenize(self, texts: str | list[str], pad: bool=True) -> np.ndarray:
        """Tokenizes a string or list of strings into a 2D :class:`numpy.ndarray` of token ids

        :param texts: Texts to be tokenized
        :type texts: str, list
        :param pad: unused here (configured in the constructor)
        :type pad: bool
        :return: 2D numpy array representing token ids
        :rtype: class:`numpy.ndarray`
        """
        if isinstance(texts, str):
            texts = [texts]
        encodings = self.tokenizer.encode_batch_fast(texts, add_special_tokens=self.add_special_tokens)
        return np.array([e.ids for e in encodings])

def tokenize(self, texts: str | list[str], pad: bool=True) -> np.ndarray:
    """Tokenizes a string or list of strings into a 2D :class:`numpy.ndarray` of token ids

        :param texts: Texts to be tokenized
        :type texts: str, list
        :param pad: unused here (configured in the constructor)
        :type pad: bool
        :return: 2D numpy array representing token ids
        :rtype: class:`numpy.ndarray`
        """
    if isinstance(texts, str):
        texts = [texts]
    encodings = self.tokenizer.encode_batch_fast(texts, add_special_tokens=self.add_special_tokens)
    return np.array([e.ids for e in encodings])

class LocalIndex(BaseIndex):
    type: str = 'local'
    metadata: Optional[np.ndarray] = Field(default=None, exclude=True)

    def __init__(self, **data):
        super().__init__(**data)
        if self.metadata is None:
            self.metadata = None
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs):
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
        """
        embeds = np.array(embeddings)
        routes_arr = np.array(routes)
        if isinstance(utterances[0], str):
            utterances_arr = np.array(utterances)
        else:
            utterances_arr = np.array(utterances, dtype=object)
        if self.index is None:
            self.index = embeds
            self.routes = routes_arr
            self.utterances = utterances_arr
            self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)
        else:
            self.index = np.concatenate([self.index, embeds])
            self.routes = np.concatenate([self.routes, routes_arr])
            self.utterances = np.concatenate([self.utterances, utterances_arr])
            if self.metadata is not None:
                self.metadata = np.concatenate([self.metadata, np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)])
            else:
                self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)

    def _remove_and_sync(self, routes_to_delete: dict) -> np.ndarray:
        """Remove and sync the index.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        :return: A numpy array of the removed route utterances.
        :rtype: np.ndarray
        """
        if self.index is None or self.routes is None or self.utterances is None:
            raise ValueError('Index, routes, or utterances are not populated.')
        route_utterances = np.array([self.routes, self.utterances]).T
        mask = np.ones(len(route_utterances), dtype=bool)
        for route, utterances in routes_to_delete.items():
            for utterance in utterances:
                mask &= ~((route_utterances[:, 0] == route) & (route_utterances[:, 1] == utterance))
        self.index = self.index[mask]
        self.routes = self.routes[mask]
        self.utterances = self.utterances[mask]
        if self.metadata is not None:
            self.metadata = self.metadata[mask]
        return route_utterances[~mask]

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the index.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects - LocalIndex now includes metadata if present.
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if self.routes is None or self.utterances is None:
            return []
        if include_metadata and self.metadata is not None:
            return [Utterance(route=route, utterance=utterance, function_schemas=None, metadata=metadata) for route, utterance, metadata in zip(self.routes, self.utterances, self.metadata)]
        else:
            return [Utterance.from_tuple(x) for x in zip(self.routes, self.utterances)]

    def describe(self) -> IndexConfig:
        """Describe the index.

        :return: An IndexConfig object.
        :rtype: IndexConfig
        """
        return IndexConfig(type=self.type, dimensions=self.index.shape[1] if self.index is not None else 0, vectors=self.index.shape[0] if self.index is not None else 0)

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None and self.routes is not None

    async def ais_ready(self) -> bool:
        """Checks if the index is ready to be used asynchronously.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None and self.routes is not None

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        if self.index is None or self.routes is None:
            raise ValueError('Index or routes are not populated.')
        if route_filter is not None:
            filtered_index = []
            filtered_routes = []
            for route, vec in zip(self.routes, self.index):
                if route in route_filter:
                    filtered_index.append(vec)
                    filtered_routes.append(route)
            if not filtered_routes:
                raise ValueError('No routes found matching the filter criteria.')
            sim = similarity_matrix(vector, np.array(filtered_index))
            scores, idx = top_scores(sim, top_k)
            route_names = [filtered_routes[i] for i in idx]
        else:
            sim = similarity_matrix(vector, self.index)
            scores, idx = top_scores(sim, top_k)
            route_names = [self.routes[i] for i in idx]
        return (scores, route_names)

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query and return top_k results.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        if self.index is None or self.routes is None:
            raise ValueError('Index or routes are not populated.')
        if route_filter is not None:
            filtered_index = []
            filtered_routes = []
            for route, vec in zip(self.routes, self.index):
                if route in route_filter:
                    filtered_index.append(vec)
                    filtered_routes.append(route)
            if not filtered_routes:
                raise ValueError('No routes found matching the filter criteria.')
            sim = similarity_matrix(vector, np.array(filtered_index))
            scores, idx = top_scores(sim, top_k)
            route_names = [filtered_routes[i] for i in idx]
        else:
            sim = similarity_matrix(vector, self.index)
            scores, idx = top_scores(sim, top_k)
            route_names = [self.routes[i] for i in idx]
        return (scores, route_names)

    def aget_routes(self):
        """Get all routes from the index.

        :return: A list of routes.
        :rtype: List[str]
        """
        logger.error('Sync remove is not implemented for LocalIndex.')

    def _write_config(self, config: ConfigParameter):
        """Write the config to the index.

        :param config: The config to write to the index.
        :type config: ConfigParameter
        """
        logger.warning('No config is written for LocalIndex.')

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

    async def adelete(self, route_name: str):
        """Delete all records of a specific route from the index. Note that this just points
        to the sync delete method as async makes no difference for the local computations
        of the LocalIndex.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        self.delete(route_name)

    def delete_index(self):
        """Deletes the index, effectively clearing it and setting it to None.

        :return: None
        :rtype: None
        """
        self.index = None
        self.routes = None
        self.utterances = None
        self.metadata = None

    async def adelete_index(self):
        """Deletes the index, effectively clearing it and setting it to None. Note that this just points
        to the sync delete_index method as async makes no difference for the local computations
        of the LocalIndex.

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

def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs):
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
        """
    embeds = np.array(embeddings)
    routes_arr = np.array(routes)
    if isinstance(utterances[0], str):
        utterances_arr = np.array(utterances)
    else:
        utterances_arr = np.array(utterances, dtype=object)
    if self.index is None:
        self.index = embeds
        self.routes = routes_arr
        self.utterances = utterances_arr
        self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)
    else:
        self.index = np.concatenate([self.index, embeds])
        self.routes = np.concatenate([self.routes, routes_arr])
        self.utterances = np.concatenate([self.utterances, utterances_arr])
        if self.metadata is not None:
            self.metadata = np.concatenate([self.metadata, np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)])
        else:
            self.metadata = np.array(metadata_list, dtype=object) if metadata_list else np.array([{} for _ in utterances], dtype=object)

def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
    """Search the index for the query and return top_k results.

        :param vector: The vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The routes to filter the search by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the query vector and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
    if self.index is None or self.routes is None:
        raise ValueError('Index or routes are not populated.')
    if route_filter is not None:
        filtered_index = []
        filtered_routes = []
        for route, vec in zip(self.routes, self.index):
            if route in route_filter:
                filtered_index.append(vec)
                filtered_routes.append(route)
        if not filtered_routes:
            raise ValueError('No routes found matching the filter criteria.')
        sim = similarity_matrix(vector, np.array(filtered_index))
        scores, idx = top_scores(sim, top_k)
        route_names = [filtered_routes[i] for i in idx]
    else:
        sim = similarity_matrix(vector, self.index)
        scores, idx = top_scores(sim, top_k)
        route_names = [self.routes[i] for i in idx]
    return (scores, route_names)

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

class VitEncoder(DenseEncoder):
    """Encoder for Vision Transformer models.

    This class provides functionality to encode images using a Vision Transformer
    model via Hugging Face. It supports various image processing and model initialization
    options.
    """
    name: str = 'google/vit-base-patch16-224'
    type: str = 'huggingface'
    processor_kwargs: Dict = {}
    model_kwargs: Dict = {}
    device: Optional[str] = None
    _processor: Any = PrivateAttr()
    _model: Any = PrivateAttr()
    _torch: Any = PrivateAttr()
    _T: Any = PrivateAttr()
    _Image: Any = PrivateAttr()

    def __init__(self, **data):
        """Initialize the VitEncoder.

        :param **data: Additional keyword arguments for the encoder.
        :type **data: dict
        """
        if data.get('score_threshold') is None:
            data['score_threshold'] = 0.5
        super().__init__(**data)
        self._processor, self._model = self._initialize_hf_model()

    def _initialize_hf_model(self):
        """Initialize the Hugging Face model.

        :return: The processor and model.
        :rtype: tuple
        """
        try:
            from transformers import ViTImageProcessor, ViTModel
        except ImportError:
            raise ImportError('Please install transformers to use VitEncoder. You can install it with: `pip install semantic-router[vision]`')
        try:
            import torch
            import torchvision.transforms as T
        except ImportError:
            raise ImportError('Please install Pytorch to use VitEncoder. You can install it with: `pip install semantic-router[vision]`')
        try:
            from PIL import Image
        except ImportError:
            raise ImportError('Please install PIL to use VitEncoder. You can install it with: `pip install semantic-router[vision]`')
        self._torch = torch
        self._Image = Image
        self._T = T
        processor = ViTImageProcessor.from_pretrained(self.name, **self.processor_kwargs)
        model = ViTModel.from_pretrained(self.name, **self.model_kwargs)
        self.device = self._get_device()
        model.to(self.device)
        return (processor, model)

    def _get_device(self) -> str:
        """Get the device to use for the model.

        :return: The device to use for the model.
        :rtype: str
        """
        if self.device:
            device = self.device
        elif self._torch.cuda.is_available():
            device = 'cuda'
        elif self._torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'
        return device

    def _process_images(self, images: List[Any]):
        """Process the images for the model.

        :param images: The images to process.
        :type images: List[Any]
        :return: The processed images.
        :rtype: Any
        """
        rgb_images = [self._ensure_rgb(img) for img in images]
        processed_images = self._processor(images=rgb_images, return_tensors='pt')
        processed_images = processed_images.to(self.device)
        return processed_images

    def _ensure_rgb(self, img: Any):
        """Ensure the image is in RGB format.

        :param img: The image to ensure is in RGB format.
        :type img: Any
        :return: The image in RGB format.
        :rtype: Any
        """
        rgbimg = self._Image.new('RGB', img.size)
        rgbimg.paste(img)
        return rgbimg

    def __call__(self, imgs: List[Any], batch_size: int=32) -> List[List[float]]:
        """Encode a list of images into embeddings using the Vision Transformer model.

        :param imgs: The images to encode.
        :type imgs: List[Any]
        :param batch_size: The batch size for encoding.
        :type batch_size: int
        :return: The embeddings for the images.
        :rtype: List[List[float]]
        """
        all_embeddings = []
        for i in range(0, len(imgs), batch_size):
            batch_imgs = imgs[i:i + batch_size]
            batch_imgs_transform = self._process_images(batch_imgs)
            with self._torch.no_grad():
                embeddings = self._model(**batch_imgs_transform).last_hidden_state[:, 0].cpu().tolist()
            all_embeddings.extend(embeddings)
        return all_embeddings

def _process_images(self, images: List[Any]):
    """Process the images for the model.

        :param images: The images to process.
        :type images: List[Any]
        :return: The processed images.
        :rtype: Any
        """
    rgb_images = [self._ensure_rgb(img) for img in images]
    processed_images = self._processor(images=rgb_images, return_tensors='pt')
    processed_images = processed_images.to(self.device)
    return processed_images

def __call__(self, imgs: List[Any], batch_size: int=32) -> List[List[float]]:
    """Encode a list of images into embeddings using the Vision Transformer model.

        :param imgs: The images to encode.
        :type imgs: List[Any]
        :param batch_size: The batch size for encoding.
        :type batch_size: int
        :return: The embeddings for the images.
        :rtype: List[List[float]]
        """
    all_embeddings = []
    for i in range(0, len(imgs), batch_size):
        batch_imgs = imgs[i:i + batch_size]
        batch_imgs_transform = self._process_images(batch_imgs)
        with self._torch.no_grad():
            embeddings = self._model(**batch_imgs_transform).last_hidden_state[:, 0].cpu().tolist()
        all_embeddings.extend(embeddings)
    return all_embeddings

class SparseEncoder(BaseModel):
    """An encoder that encodes documents into a sparse format."""
    name: str
    type: str = Field(default='base')
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        """Sparsely encode a list of documents. Documents can be any type, but the encoder must
        be built to handle that data type. Typically, these types are strings or
        arrays representing images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :return: The encoded documents.
        :rtype: List[SparseEmbedding]
        """
        raise NotImplementedError('Subclasses must implement this method')

    async def acall(self, docs: List[Any]) -> List[SparseEmbedding]:
        """Encode a list of documents asynchronously. Documents can be any type, but the
        encoder must be built to handle that data type. Typically, these types are
        strings or arrays representing images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :return: The encoded documents.
        :rtype: List[SparseEmbedding]
        """
        raise NotImplementedError('Subclasses must implement this method')

    def _array_to_sparse_embeddings(self, sparse_arrays: np.ndarray) -> List[SparseEmbedding]:
        """Consumes several sparse vectors containing zero-values and returns a compact
        array.

        :param sparse_arrays: The sparse arrays to compact.
        :type sparse_arrays: np.ndarray
        :return: The compact array.
        :rtype: List[SparseEmbedding]
        """
        if hasattr(sparse_arrays, 'to_dense'):
            sparse_arrays = sparse_arrays.to_dense().cpu().numpy()
        if sparse_arrays.ndim != 2:
            raise ValueError(f'Expected a 2D array, got a {sparse_arrays.ndim}D array.')
        coords = np.nonzero(sparse_arrays)
        if coords[0].size == 0:
            return [SparseEmbedding(embedding=np.empty((1, 2)))]
        compact_array = np.array([coords[0], coords[1], sparse_arrays[coords]]).T
        arr_range = range(compact_array[:, 0].max().astype(int) + 1)
        arrs = [compact_array[compact_array[:, 0] == i, :][:, 1:3] for i in arr_range]
        return [SparseEmbedding.from_compact_array(arr) for arr in arrs]

def _array_to_sparse_embeddings(self, sparse_arrays: np.ndarray) -> List[SparseEmbedding]:
    """Consumes several sparse vectors containing zero-values and returns a compact
        array.

        :param sparse_arrays: The sparse arrays to compact.
        :type sparse_arrays: np.ndarray
        :return: The compact array.
        :rtype: List[SparseEmbedding]
        """
    if hasattr(sparse_arrays, 'to_dense'):
        sparse_arrays = sparse_arrays.to_dense().cpu().numpy()
    if sparse_arrays.ndim != 2:
        raise ValueError(f'Expected a 2D array, got a {sparse_arrays.ndim}D array.')
    coords = np.nonzero(sparse_arrays)
    if coords[0].size == 0:
        return [SparseEmbedding(embedding=np.empty((1, 2)))]
    compact_array = np.array([coords[0], coords[1], sparse_arrays[coords]]).T
    arr_range = range(compact_array[:, 0].max().astype(int) + 1)
    arrs = [compact_array[compact_array[:, 0] == i, :][:, 1:3] for i in arr_range]
    return [SparseEmbedding.from_compact_array(arr) for arr in arrs]

class LiteLLMEncoder(DenseEncoder, AsymmetricDenseMixin):
    """LiteLLM encoder class for generating embeddings using LiteLLM.

    The LiteLLMEncoder class is a subclass of DenseEncoder and utilizes the LiteLLM SDK
    to generate embeddings for given documents. It supports all encoders supported by LiteLLM
    and supports customization of the score threshold for filtering or processing the embeddings.
    """
    type: str = 'litellm'

    def __init__(self, name: str | None=None, score_threshold: float | None=None, api_key: str | None=None):
        """Initialize the LiteLLMEncoder.

        :param name: The name of the embedding model to use. Must use LiteLLM naming
            convention (e.g. "openai/text-embedding-3-small" or "mistral/mistral-embed").
        :type name: str
        :param score_threshold: The score threshold for the embeddings.
        :type score_threshold: float
        """
        if name is None:
            name = 'openai/' + EncoderDefault.OPENAI.value['embedding_model']
        super().__init__(name=name, score_threshold=score_threshold if score_threshold is not None else 0.3)
        self.type, self.name = self.name.split('/', 1)
        if api_key is None:
            api_key = os.getenv(self.type.upper() + '_API_KEY')
        if api_key is None:
            raise ValueError('Expected API key via `api_key` parameter or `{self.type.upper()}_API_KEY` environment variable.')
        os.environ[self.type.upper() + '_API_KEY'] = api_key

    def __call__(self, docs: list[Any], **kwargs) -> list[list[float]]:
        """Encode a list of text documents into embeddings using LiteLLM.

        :param docs: List of text documents to encode.
        :return: List of embeddings for each document."""
        return self.encode_queries(docs, **kwargs)

    async def acall(self, docs: list[Any], **kwargs) -> list[list[float]]:
        """Encode a list of documents into embeddings using LiteLLM asynchronously.

        :param docs: List of documents to encode.
        :return: List of embeddings for each document."""
        return await self.aencode_queries(docs, **kwargs)

    def encode_queries(self, docs: list[str], **kwargs) -> list[list[float]]:
        try:
            embeds = litellm.embedding(input=docs, model=f'{self.type}/{self.name}', **kwargs)
            return litellm_to_list(embeds)
        except Exception as e:
            raise ValueError(f'{self.type.capitalize()} API call failed. Error: {e}') from e

    def encode_documents(self, docs: list[str], **kwargs) -> list[list[float]]:
        try:
            embeds = litellm.embedding(input=docs, model=f'{self.type}/{self.name}', **kwargs)
            return litellm_to_list(embeds)
        except Exception as e:
            raise ValueError(f'{self.type.capitalize()} API call failed. Error: {e}') from e

    async def aencode_queries(self, docs: list[str], **kwargs) -> list[list[float]]:
        try:
            embeds = await litellm.aembedding(input=docs, model=f'{self.type}/{self.name}', **kwargs)
            return litellm_to_list(embeds)
        except Exception as e:
            raise ValueError(f'{self.type.capitalize()} API call failed. Error: {e}') from e

    async def aencode_documents(self, docs: list[str], **kwargs) -> list[list[float]]:
        try:
            embeds = await litellm.aembedding(input=docs, model=f'{self.type}/{self.name}', **kwargs)
            return litellm_to_list(embeds)
        except Exception as e:
            raise ValueError(f'{self.type.capitalize()} API call failed. Error: {e}') from e

def __call__(self, docs: list[Any], **kwargs) -> list[list[float]]:
    """Encode a list of text documents into embeddings using LiteLLM.

        :param docs: List of text documents to encode.
        :return: List of embeddings for each document."""
    return self.encode_queries(docs, **kwargs)

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

def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
    return self.encode_queries(docs)

class AurelioSparseEncoder(SparseEncoder, AsymmetricSparseMixin):
    """Sparse encoder using Aurelio Platform's embedding API. Requires an API key from
    https://platform.aurelio.ai
    """
    model: Optional[Any] = None
    client: AurelioClient = Field(default_factory=AurelioClient, exclude=True)
    async_client: AsyncAurelioClient = Field(default_factory=AsyncAurelioClient, exclude=True)
    type: str = 'sparse'

    def __init__(self, name: str | None=None, api_key: Optional[str]=None):
        """Initialize the AurelioSparseEncoder.

        :param name: The name of the model to use.
        :type name: str | None
        :param api_key: The API key to use.
        :type api_key: str | None
        """
        if name is None:
            name = 'bm25'
        super().__init__(name=name)
        if api_key is None:
            api_key = os.getenv('AURELIO_API_KEY')
        if api_key is None:
            raise ValueError('AURELIO_API_KEY environment variable is not set.')
        self.client = AurelioClient(api_key=api_key)
        self.async_client = AsyncAurelioClient(api_key=api_key)

    def __call__(self, docs: list[str]) -> list[SparseEmbedding]:
        """Encode a list of queries using the Aurelio Platform embedding API. Documents
        must be strings, sparse encoders do not support other types.
        """
        return self.encode_queries(docs)

    def encode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
        res: EmbeddingResponse = self.client.embedding(input=docs, model=self.name, input_type='queries')
        embeds = [SparseEmbedding.from_aurelio(r.embedding) for r in res.data]
        return embeds

    def encode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
        res: EmbeddingResponse = self.client.embedding(input=docs, model=self.name, input_type='documents')
        embeds = [SparseEmbedding.from_aurelio(r.embedding) for r in res.data]
        return embeds

    async def aencode_queries(self, docs: List[str]) -> list[SparseEmbedding]:
        res: EmbeddingResponse = await self.async_client.embedding(input=docs, model=self.name, input_type='queries')
        embeds = [SparseEmbedding.from_aurelio(r.embedding) for r in res.data]
        return embeds

    async def aencode_documents(self, docs: List[str]) -> list[SparseEmbedding]:
        res: EmbeddingResponse = await self.async_client.embedding(input=docs, model=self.name, input_type='documents')
        embeds = [SparseEmbedding.from_aurelio(r.embedding) for r in res.data]
        return embeds

    async def acall(self, docs: list[str]) -> list[SparseEmbedding]:
        """Asynchronously encode a list of documents using the Aurelio Platform
        embedding API. Documents must be strings, sparse encoders do not support other
        types.

        :param docs: The documents to encode.
        :type docs: list[str]
        :param input_type:
        :type semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The encoded documents.
        :rtype: list[SparseEmbedding]
        """
        return await self.aencode_queries(docs)

    def fit(self, docs: List[str]):
        """Fit the encoder to a list of documents. AurelioSparseEncoder does not support
        fit yet.

        :param docs: The documents to fit the encoder to.
        :type docs: list[str]
        """
        raise NotImplementedError('AurelioSparseEncoder does not support fit.')

def __call__(self, docs: list[str]) -> list[SparseEmbedding]:
    """Encode a list of queries using the Aurelio Platform embedding API. Documents
        must be strings, sparse encoders do not support other types.
        """
    return self.encode_queries(docs)

class CLIPEncoder(DenseEncoder):
    """Multi-modal dense encoder for text and images using CLIP-type models via
    HuggingFace.

    :param name: The name of the model to use.
    :type name: str
    :param tokenizer_kwargs: Keyword arguments for the tokenizer.
    :type tokenizer_kwargs: Dict
    :param processor_kwargs: Keyword arguments for the processor.
    :type processor_kwargs: Dict
    :param model_kwargs: Keyword arguments for the model.
    :type model_kwargs: Dict
    :param device: The device to use for the model.
    :type device: Optional[str]
    :param _tokenizer: The tokenizer for the model.
    :type _tokenizer: Any
    :param _processor: The processor for the model.
    :type _processor: Any
    :param _model: The model.
    :type _model: Any
    :param _torch: The torch library.
    :type _torch: Any
    :param _Image: The PIL library.
    :type _Image: Any
    """
    name: str = 'openai/clip-vit-base-patch16'
    type: str = 'huggingface'
    tokenizer_kwargs: Dict = {}
    processor_kwargs: Dict = {}
    model_kwargs: Dict = {}
    device: Optional[str] = None
    _tokenizer: Any = PrivateAttr()
    _processor: Any = PrivateAttr()
    _model: Any = PrivateAttr()
    _torch: Any = PrivateAttr()
    _Image: Any = PrivateAttr()

    def __init__(self, **data):
        """Initialize the CLIPEncoder.

        :param **data: Keyword arguments for the encoder.
        :type **data: Dict
        """
        if data.get('score_threshold') is None:
            data['score_threshold'] = 0.2
        super().__init__(**data)
        self._tokenizer, self._processor, self._model = self._initialize_hf_model()

    def __call__(self, docs: List[Any], batch_size: int=32, normalize_embeddings: bool=True) -> List[List[float]]:
        """Encode a list of documents. Can handle both text and images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :param batch_size: The batch size for the encoding.
        :type batch_size: int
        :param normalize_embeddings: Whether to normalize the embeddings.
        :type normalize_embeddings: bool
        :returns: A list of embeddings.
        :rtype: List[List[float]]
        """
        all_embeddings = []
        if isinstance(docs[0], str):
            text = True
        else:
            text = False
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            if text:
                embeddings = self._encode_text(docs=batch_docs)
            else:
                embeddings = self._encode_image(images=batch_docs)
            if normalize_embeddings:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=0)
            embeddings = embeddings.tolist()
            all_embeddings.extend(embeddings)
        return all_embeddings

    def _initialize_hf_model(self):
        """Initialize the HuggingFace model.

        :returns: A tuple of the tokenizer, processor, and model.
        :rtype: Tuple[Any, Any, Any]
        """
        try:
            from transformers import CLIPModel, CLIPProcessor, CLIPTokenizerFast
        except ImportError:
            raise ImportError('Please install transformers to use CLIPEncoder. You can install it with: `pip install semantic-router[vision]`')
        try:
            import torch
        except ImportError:
            raise ImportError('Please install Pytorch to use CLIPEncoder. You can install it with: `pip install semantic-router[vision]`')
        try:
            from PIL import Image
        except ImportError:
            raise ImportError('Please install PIL to use HuggingFaceEncoder. You can install it with: `pip install semantic-router[vision]`')
        self._torch = torch
        self._Image = Image
        tokenizer = CLIPTokenizerFast.from_pretrained(self.name, **self.tokenizer_kwargs)
        processor = CLIPProcessor.from_pretrained(self.name)
        model = CLIPModel.from_pretrained(self.name, **self.model_kwargs)
        self.device = self._get_device()
        model.to(self.device)
        return (tokenizer, processor, model)

    def _get_device(self) -> str:
        """Get the device to use for the model. Returns either cuda, mps, or cpu.

        :returns: The device to use for the model.
        :rtype: str
        """
        if self.device:
            device = self.device
        elif self._torch.cuda.is_available():
            device = 'cuda'
        elif self._torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'
        return device

    def _encode_text(self, docs: List[str]) -> Any:
        """Encode a list of text documents.

        :param docs: The documents to encode.
        :type docs: List[str]
        :returns: The embeddings for the documents.
        :rtype: Any
        """
        inputs = self._tokenizer(docs, return_tensors='pt', padding=True, truncation=True).to(self.device)
        with self._torch.no_grad():
            embeds = self._model.get_text_features(**inputs)
            embeds = embeds.squeeze(0).cpu().detach().numpy()
        return embeds

    def _encode_image(self, images: List[Any]) -> Any:
        """Encode a list of image documents.

        :param images: The images to encode.
        :type images: List[Any]
        :returns: The embeddings for the images.
        :rtype: Any
        """
        rgb_images = [self._ensure_rgb(img) for img in images]
        inputs = self._processor(text=None, images=rgb_images, return_tensors='pt')['pixel_values'].to(self.device)
        with self._torch.no_grad():
            embeds = self._model.get_image_features(pixel_values=inputs)
            embeds = embeds.squeeze(0).cpu().detach().numpy()
        return embeds

    def _ensure_rgb(self, img: Any):
        """Ensure the image is in RGB format.

        :param img: The image to ensure is in RGB format.
        :type img: Any
        :returns: The image in RGB format.
        :rtype: Any
        """
        rgbimg = self._Image.new('RGB', img.size)
        rgbimg.paste(img)
        return rgbimg

def __call__(self, docs: List[Any], batch_size: int=32, normalize_embeddings: bool=True) -> List[List[float]]:
    """Encode a list of documents. Can handle both text and images.

        :param docs: The documents to encode.
        :type docs: List[Any]
        :param batch_size: The batch size for the encoding.
        :type batch_size: int
        :param normalize_embeddings: Whether to normalize the embeddings.
        :type normalize_embeddings: bool
        :returns: A list of embeddings.
        :rtype: List[List[float]]
        """
    all_embeddings = []
    if isinstance(docs[0], str):
        text = True
    else:
        text = False
    for i in range(0, len(docs), batch_size):
        batch_docs = docs[i:i + batch_size]
        if text:
            embeddings = self._encode_text(docs=batch_docs)
        else:
            embeddings = self._encode_image(images=batch_docs)
        if normalize_embeddings:
            embeddings = embeddings / np.linalg.norm(embeddings, axis=0)
        embeddings = embeddings.tolist()
        all_embeddings.extend(embeddings)
    return all_embeddings

def _encode_text(self, docs: List[str]) -> Any:
    """Encode a list of text documents.

        :param docs: The documents to encode.
        :type docs: List[str]
        :returns: The embeddings for the documents.
        :rtype: Any
        """
    inputs = self._tokenizer(docs, return_tensors='pt', padding=True, truncation=True).to(self.device)
    with self._torch.no_grad():
        embeds = self._model.get_text_features(**inputs)
        embeds = embeds.squeeze(0).cpu().detach().numpy()
    return embeds

def _encode_image(self, images: List[Any]) -> Any:
    """Encode a list of image documents.

        :param images: The images to encode.
        :type images: List[Any]
        :returns: The embeddings for the images.
        :rtype: Any
        """
    rgb_images = [self._ensure_rgb(img) for img in images]
    inputs = self._processor(text=None, images=rgb_images, return_tensors='pt')['pixel_values'].to(self.device)
    with self._torch.no_grad():
        embeds = self._model.get_image_features(pixel_values=inputs)
        embeds = embeds.squeeze(0).cpu().detach().numpy()
    return embeds

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

class BedrockEncoder(DenseEncoder):
    """Dense encoder using Amazon Bedrock embedding API. Requires an AWS Access Key ID
    and AWS Secret Access Key.

    The BedrockEncoder class is a subclass of DenseEncoder and utilizes the
    TextEmbeddingModel from the Amazon's Bedrock Platform to generate embeddings for
    given documents. It supports customization of the pre-trained model, score
    threshold, and region.

    Example usage:

    ```python
    from semantic_router.encoders.bedrock_encoder import BedrockEncoder

    encoder = BedrockEncoder(
        access_key_id="your-access-key-id",
        secret_access_key="your-secret-key",
        region="your-region"
    )
    embeddings = encoder(["document1", "document2"])
    ```
    """
    client: Any = None
    type: str = 'bedrock'
    input_type: Optional[str] = 'search_query'
    name: str
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: Optional[str] = None

    def __init__(self, name: str=EncoderDefault.BEDROCK.value['embedding_model'], input_type: Optional[str]='search_query', score_threshold: float=0.3, client: Optional[Any]=None, access_key_id: Optional[str]=None, secret_access_key: Optional[str]=None, session_token: Optional[str]=None, region: Optional[str]=None):
        """Initializes the BedrockEncoder.

        :param name: The name of the pre-trained model to use for embedding.
            If not provided, the default model specified in EncoderDefault will
            be used.
        :type name: str
        :param input_type: The type of input to use for the embedding.
            If not provided, the default input type specified in EncoderDefault will
            be used.
        :type input_type: str
        :param score_threshold: The threshold for similarity scores.
        :type score_threshold: float
        :param access_key_id: The AWS access key id for an IAM principle.
            If not provided, it will be retrieved from the access_key_id
            environment variable.
        :type access_key_id: str
        :param secret_access_key: The secret access key for an IAM principle.
            If not provided, it will be retrieved from the AWS_SECRET_KEY
            environment variable.
        :type secret_access_key: str
        :param session_token: The session token for an IAM principle.
            If not provided, it will be retrieved from the AWS_SESSION_TOKEN
            environment variable.
        :param region: The location of the Bedrock resources.
            If not provided, it will be retrieved from the AWS_REGION
            environment variable, defaulting to "us-west-1"
        :type region: str
        :raises ValueError: If the Bedrock Platform client fails to initialize.
        """
        super().__init__(name=name, score_threshold=score_threshold)
        self.input_type = input_type
        if client:
            self.client = client
        else:
            self.access_key_id = self.get_env_variable('AWS_ACCESS_KEY_ID', access_key_id)
            self.secret_access_key = self.get_env_variable('AWS_SECRET_ACCESS_KEY', secret_access_key)
            self.session_token = self.get_env_variable('AWS_SESSION_TOKEN', session_token)
            self.region = self.get_env_variable('AWS_DEFAULT_REGION', region, default='us-west-1')
            try:
                self.client = self._initialize_client(self.access_key_id, self.secret_access_key, self.session_token, self.region)
            except Exception as e:
                raise ValueError(f'Bedrock client failed to initialise. Error: {e}') from e

    def _initialize_client(self, access_key_id, secret_access_key, session_token, region):
        """Initializes the Bedrock client.

        :param access_key_id: The Amazon access key ID.
        :type access_key_id: str
        :param secret_access_key: The Amazon secret key.
        :type secret_access_key: str
        :param region: The location of the AI Platform resources.
        :type region: str
        :returns: An instance of the TextEmbeddingModel client.
        :rtype: Any
        :raises ImportError: If the required Bedrock libraries are not
            installed.
            ValueError: If the Bedrock client fails to initialize.
        """
        try:
            import boto3
        except ImportError:
            raise ImportError("Please install Amazon's Boto3 client library to use the BedrockEncoder. You can install them with: `pip install boto3`")
        access_key_id = access_key_id or os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY')
        region = region or os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        if access_key_id is None:
            raise ValueError("AWS access key ID cannot be 'None'.")
        if aws_secret_key is None:
            raise ValueError("AWS secret access key cannot be 'None'.")
        session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, aws_session_token=session_token)
        try:
            bedrock_client = session.client('bedrock-runtime', region_name=region)
        except Exception as err:
            raise ValueError(f'The Bedrock client failed to initialize. Error: {err}') from err
        return bedrock_client

    def __call__(self, docs: List[Union[str, Dict]], model_kwargs: Optional[Dict]=None) -> List[List[float]]:
        """Generates embeddings for the given documents.

        :param docs: A list of strings representing the documents to embed.
        :type docs: list[str]
        :param model_kwargs: A dictionary of model-specific inference parameters.
        :type model_kwargs: dict
        :returns: A list of lists, where each inner list contains the embedding values for a
            document.
        :rtype: list[list[float]]
        :raises ValueError: If the Bedrock Platform client is not initialized or if the
            API call fails.
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("Please install Amazon's Botocore client library to use the BedrockEncoder. You can install them with: `pip install botocore`")
        if self.client is None:
            raise ValueError('Bedrock client is not initialised.')
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                embeddings = []
                if self.name and 'amazon' in self.name:
                    for doc in docs:
                        embedding_body = {}
                        if isinstance(doc, dict):
                            embedding_body['inputText'] = doc.get('text')
                            embedding_body['inputImage'] = doc.get('image')
                        else:
                            embedding_body['inputText'] = doc
                        if model_kwargs:
                            embedding_body = embedding_body | model_kwargs
                        embedding_body = {k: v for k, v in embedding_body.items() if v}
                        embedding_body_payload: str = json.dumps(embedding_body)
                        response = self.client.invoke_model(body=embedding_body_payload, modelId=self.name, accept='application/json', contentType='application/json')
                        response_body = json.loads(response.get('body').read())
                        embeddings.append(response_body.get('embedding'))
                elif self.name and 'cohere' in self.name:
                    chunked_docs = self.chunk_strings(docs)
                    for chunk in chunked_docs:
                        chunk = {'texts': chunk, 'input_type': self.input_type}
                        if model_kwargs:
                            chunk = chunk | model_kwargs
                        chunk = json.dumps(chunk)
                        response = self.client.invoke_model(body=chunk, modelId=self.name, accept='*/*', contentType='application/json')
                        response_body = json.loads(response.get('body').read())
                        chunk_embeddings = response_body.get('embeddings')
                        embeddings.extend(chunk_embeddings)
                else:
                    raise ValueError('Unknown model name')
                return embeddings
            except ClientError as error:
                if attempt < max_attempts - 1:
                    if error.response['Error']['Code'] == 'ExpiredTokenException':
                        logger.warning('Session token has expired. Retrying initialisation.')
                        try:
                            self.session_token = os.getenv('AWS_SESSION_TOKEN')
                            self.client = self._initialize_client(self.access_key_id, self.secret_access_key, self.session_token, self.region)
                        except Exception as e:
                            raise ValueError(f'Bedrock client failed to reinitialise. Error: {e}') from e
                    sleep(2 ** attempt)
                    logger.warning(f'Retrying in {2 ** attempt} seconds...')
                raise ValueError(f'Retries exhausted, Bedrock call failed. Error: {error}') from error
            except Exception as e:
                raise ValueError(f'Bedrock call failed. Error: {e}') from e
        raise ValueError('Bedrock call failed to return embeddings.')

    def chunk_strings(self, strings, MAX_WORDS=20):
        """Breaks up a list of strings into smaller chunks.

        :param strings: A list of strings to be chunked.
        :type strings: list
        :param max_chunk_size: The maximum size of each chunk. Default is 20.
        :type max_chunk_size: int
        :returns: A list of lists, where each inner list contains a chunk of strings.
        :rtype: list[list[str]]
        """
        encoding = tiktoken.get_encoding('cl100k_base')
        chunked_strings = []
        for text in strings:
            encoded_text = encoding.encode(text)
            chunks = [encoding.decode(encoded_text[i:i + MAX_WORDS]) for i in range(0, len(encoded_text), MAX_WORDS)]
            chunked_strings.append(chunks)
        return chunked_strings

    @staticmethod
    def get_env_variable(var_name, provided_value, default=None):
        """Retrieves environment variable or uses a provided value.

        :param var_name: The name of the environment variable.
        :type var_name: str
        :param provided_value: The provided value to use if not None.
        :type provided_value: Optional[str]
        :param default: The default value if the environment variable is not set.
        :type default: Optional[str]
        :returns: The value of the environment variable or the provided/default value.
        :rtype: str
        :raises ValueError: If no value is provided and the environment variable is not set.
        """
        if provided_value is not None:
            return provided_value
        value = os.getenv(var_name, default)
        if value is None:
            if var_name == 'AWS_SESSION_TOKEN':
                return None
            raise ValueError(f'No {var_name} provided')
        return value

def __call__(self, docs: List[Union[str, Dict]], model_kwargs: Optional[Dict]=None) -> List[List[float]]:
    """Generates embeddings for the given documents.

        :param docs: A list of strings representing the documents to embed.
        :type docs: list[str]
        :param model_kwargs: A dictionary of model-specific inference parameters.
        :type model_kwargs: dict
        :returns: A list of lists, where each inner list contains the embedding values for a
            document.
        :rtype: list[list[float]]
        :raises ValueError: If the Bedrock Platform client is not initialized or if the
            API call fails.
        """
    try:
        from botocore.exceptions import ClientError
    except ImportError:
        raise ImportError("Please install Amazon's Botocore client library to use the BedrockEncoder. You can install them with: `pip install botocore`")
    if self.client is None:
        raise ValueError('Bedrock client is not initialised.')
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            embeddings = []
            if self.name and 'amazon' in self.name:
                for doc in docs:
                    embedding_body = {}
                    if isinstance(doc, dict):
                        embedding_body['inputText'] = doc.get('text')
                        embedding_body['inputImage'] = doc.get('image')
                    else:
                        embedding_body['inputText'] = doc
                    if model_kwargs:
                        embedding_body = embedding_body | model_kwargs
                    embedding_body = {k: v for k, v in embedding_body.items() if v}
                    embedding_body_payload: str = json.dumps(embedding_body)
                    response = self.client.invoke_model(body=embedding_body_payload, modelId=self.name, accept='application/json', contentType='application/json')
                    response_body = json.loads(response.get('body').read())
                    embeddings.append(response_body.get('embedding'))
            elif self.name and 'cohere' in self.name:
                chunked_docs = self.chunk_strings(docs)
                for chunk in chunked_docs:
                    chunk = {'texts': chunk, 'input_type': self.input_type}
                    if model_kwargs:
                        chunk = chunk | model_kwargs
                    chunk = json.dumps(chunk)
                    response = self.client.invoke_model(body=chunk, modelId=self.name, accept='*/*', contentType='application/json')
                    response_body = json.loads(response.get('body').read())
                    chunk_embeddings = response_body.get('embeddings')
                    embeddings.extend(chunk_embeddings)
            else:
                raise ValueError('Unknown model name')
            return embeddings
        except ClientError as error:
            if attempt < max_attempts - 1:
                if error.response['Error']['Code'] == 'ExpiredTokenException':
                    logger.warning('Session token has expired. Retrying initialisation.')
                    try:
                        self.session_token = os.getenv('AWS_SESSION_TOKEN')
                        self.client = self._initialize_client(self.access_key_id, self.secret_access_key, self.session_token, self.region)
                    except Exception as e:
                        raise ValueError(f'Bedrock client failed to reinitialise. Error: {e}') from e
                sleep(2 ** attempt)
                logger.warning(f'Retrying in {2 ** attempt} seconds...')
            raise ValueError(f'Retries exhausted, Bedrock call failed. Error: {error}') from error
        except Exception as e:
            raise ValueError(f'Bedrock call failed. Error: {e}') from e
    raise ValueError('Bedrock call failed to return embeddings.')

class RouterConfig:
    """Generates a RouterConfig object that can be used for initializing routers."""
    routes: List[Route] = Field(default_factory=list)
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, routes: List[Route]=[], encoder_type: str='openai', encoder_name: Optional[str]=None):
        """Initialize a RouterConfig object.

        :param routes: A list of routes.
        :type routes: List[Route]
        :param encoder_type: The type of encoder to use.
        :type encoder_type: str
        :param encoder_name: The name of the encoder to use.
        :type encoder_name: Optional[str]
        """
        self.encoder_type = encoder_type
        if encoder_name is None:
            for encode_type in EncoderType:
                if encode_type.value == self.encoder_type:
                    if self.encoder_type == EncoderType.HUGGINGFACE.value:
                        raise NotImplementedError('HuggingFace encoder not supported by RouterConfig yet.')
                    encoder_name = EncoderDefault[encode_type.name].value['embedding_model']
                    break
            logger.info(f'Using default {encoder_type} encoder: {encoder_name}')
        self.encoder_name = encoder_name
        self.routes = routes

    @classmethod
    def from_file(cls, path: str) -> 'RouterConfig':
        """Initialize a RouterConfig from a file. Expects a JSON or YAML file with file
        extension .json, .yaml, or .yml.

        :param path: The path to the file to load the RouterConfig from.
        :type path: str
        """
        logger.info(f'Loading route config from {path}')
        _, ext = os.path.splitext(path)
        with open(path, 'r') as f:
            if ext == '.json':
                layer = json.load(f)
            elif ext in ['.yaml', '.yml']:
                layer = yaml.safe_load(f)
            else:
                raise ValueError('Unsupported file type. Only .json and .yaml are supported')
            if not is_valid(json.dumps(layer)):
                raise Exception('Invalid config JSON or YAML')
            encoder_type = layer['encoder_type']
            encoder_name = layer['encoder_name']
            routes = []
            for route_data in layer['routes']:
                if 'llm' in route_data and route_data['llm'] is not None:
                    llm_data = route_data.pop('llm')
                    llm_module_path = llm_data['module']
                    llm_module = importlib.import_module(llm_module_path)
                    llm_class = getattr(llm_module, llm_data['class'])
                    llm = llm_class(name=llm_data['model'])
                    route_data['llm'] = llm
                route = Route(**route_data)
                routes.append(route)
            return cls(encoder_type=encoder_type, encoder_name=encoder_name, routes=routes)

    @classmethod
    def from_tuples(cls, route_tuples: List[Tuple[str, str, Optional[List[Dict[str, Any]]], Dict[str, Any]]], encoder_type: str='openai', encoder_name: Optional[str]=None):
        """Initialize a RouterConfig from a list of tuples of routes and
        utterances.

        :param route_tuples: A list of tuples, each containing a route name and an
            associated utterance.
        :type route_tuples: List[Tuple[str, str]]
        :param encoder_type: The type of encoder to use, defaults to "openai".
        :type encoder_type: str, optional
        :param encoder_name: The name of the encoder to use, defaults to None.
        :type encoder_name: Optional[str], optional
        """
        routes_dict: Dict[str, Route] = {}
        for route_name, utterance, function_schema, metadata in route_tuples:
            if route_name not in routes_dict:
                routes_dict[route_name] = Route(name=route_name, utterances=[utterance], function_schemas=function_schema, metadata=metadata)
            else:
                routes_dict[route_name].utterances.append(utterance)
        routes: List[Route] = []
        for route_name, route in routes_dict.items():
            routes.append(route)
        return cls(routes=routes, encoder_type=encoder_type, encoder_name=encoder_name)

    @classmethod
    def from_index(cls, index: BaseIndex, encoder_type: str='openai', encoder_name: Optional[str]=None):
        """Initialize a RouterConfig from a BaseIndex object.

        :param index: The index to initialize the RouterConfig from.
        :type index: BaseIndex
        :param encoder_type: The type of encoder to use, defaults to "openai".
        :type encoder_type: str, optional
        :param encoder_name: The name of the encoder to use, defaults to None.
        :type encoder_name: Optional[str], optional
        """
        remote_routes = index.get_utterances(include_metadata=True)
        return cls.from_tuples(route_tuples=[utt.to_tuple() for utt in remote_routes], encoder_type=encoder_type, encoder_name=encoder_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RouterConfig to a dictionary.

        :return: A dictionary representation of the RouterConfig.
        :rtype: Dict[str, Any]
        """
        return {'encoder_type': self.encoder_type, 'encoder_name': self.encoder_name, 'routes': [route.to_dict() for route in self.routes]}

    def to_file(self, path: str):
        """Save the routes to a file in JSON or YAML format.

        :param path: The path to save the RouterConfig to.
        :type path: str
        """
        logger.info(f'Saving route config to {path}')
        _, ext = os.path.splitext(path)
        if ext not in ['.json', '.yaml', '.yml']:
            raise ValueError('Unsupported file type. Only .json and .yaml are supported')
        dir_name = os.path.dirname(path)
        if dir_name and (not os.path.exists(dir_name)):
            os.makedirs(dir_name)
        with open(path, 'w') as f:
            if ext == '.json':
                json.dump(self.to_dict(), f, indent=4)
            elif ext in ['.yaml', '.yml']:
                yaml.safe_dump(self.to_dict(), f)

    def to_utterances(self) -> List[Utterance]:
        """Convert the routes to a list of Utterance objects.

        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        utterances = []
        for route in self.routes:
            utterances.extend([Utterance(route=route.name, utterance=x, function_schemas=route.function_schemas, metadata=route.metadata or {}) for x in route.utterances])
        return utterances

    def add(self, route: Route):
        """Add a route to the RouterConfig.

        :param route: The route to add.
        :type route: Route
        """
        self.routes.append(route)
        logger.info(f'Added route `{route.name}`')

    def get(self, name: str) -> Optional[Route]:
        """Get a route from the RouterConfig by name.

        :param name: The name of the route to get.
        :type name: str
        :return: The route if found, otherwise None.
        :rtype: Optional[Route]
        """
        for route in self.routes:
            if route.name == name:
                return route
        logger.error(f'Route `{name}` not found')
        return None

    def remove(self, name: str):
        """Remove a route from the RouterConfig by name.

        :param name: The name of the route to remove.
        :type name: str
        """
        if name not in [route.name for route in self.routes]:
            logger.error(f'Route `{name}` not found')
        else:
            self.routes = [route for route in self.routes if route.name != name]
            logger.info(f'Removed route `{name}`')

    def get_hash(self) -> ConfigParameter:
        """Get the hash of the RouterConfig. Used for syncing.

        :return: The hash of the RouterConfig.
        :rtype: ConfigParameter
        """
        layer = self.to_dict()
        return ConfigParameter(field='sr_hash', value=hashlib.sha256(json.dumps(layer).encode()).hexdigest())

def to_utterances(self) -> List[Utterance]:
    """Convert the routes to a list of Utterance objects.

        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
    utterances = []
    for route in self.routes:
        utterances.extend([Utterance(route=route.name, utterance=x, function_schemas=route.function_schemas, metadata=route.metadata or {}) for x in route.utterances])
    return utterances

def xq_reshape(xq: List[float] | np.ndarray) -> np.ndarray:
    """Reshape the query vector to be a 2D numpy array.

    :param xq: The query vector.
    :type xq: List[float] | np.ndarray
    :return: The reshaped query vector.
    :rtype: np.ndarray
    """
    if not isinstance(xq, np.ndarray):
        xq = np.array(xq)
    if len(xq.shape) == 1:
        xq = np.expand_dims(xq, axis=0)
    if xq.shape[0] != 1:
        raise ValueError(f'Expected (1, x) dimensional input for query, got {xq.shape}.')
    return xq

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

class HybridRouter(BaseRouter):
    """A hybrid layer that uses both dense and sparse embeddings to classify routes."""
    sparse_encoder: Optional[SparseEncoder] = Field(default=None)
    alpha: float = 0.3

    def __init__(self, encoder: DenseEncoder, sparse_encoder: Optional[SparseEncoder]=None, llm: Optional[BaseLLM]=None, routes: Optional[List[Route]]=None, index: Optional[HybridLocalIndex]=None, top_k: int=5, aggregation: str='mean', auto_sync: Optional[str]=None, alpha: float=0.3, init_async_index: bool=False):
        """Initialize the HybridRouter.

        :param encoder: The dense encoder to use.
        :type encoder: DenseEncoder
        :param sparse_encoder: The sparse encoder to use.
        :type sparse_encoder: Optional[SparseEncoder]
        """
        if index is None:
            logger.warning('No index provided. Using default HybridLocalIndex.')
            index = HybridLocalIndex()
        encoder = self._get_encoder(encoder=encoder)
        sparse_encoder = self._get_sparse_encoder(sparse_encoder=sparse_encoder)
        if isinstance(sparse_encoder, FittableMixin) and routes:
            sparse_encoder.fit(routes)
        super().__init__(encoder=encoder, sparse_encoder=sparse_encoder, llm=llm, routes=routes, index=index, top_k=top_k, aggregation=aggregation, auto_sync=auto_sync, init_async_index=init_async_index)
        self.alpha = alpha

    def _set_score_threshold(self):
        """Set the score threshold for the HybridRouter. Unlike the base router the
        encoder score threshold is not used directly. Instead, the dense encoder
        score threshold is multiplied by the alpha value, resulting in a lower
        score threshold. This is done to account for the difference in returned
        scores from the hybrid router.
        """
        if self.encoder.score_threshold is not None:
            self.score_threshold = self.encoder.score_threshold * self.alpha
            if self.score_threshold is None:
                logger.warning("No score threshold value found in encoder. Using the default 'None' value can lead to unexpected results.")

    def add(self, routes: List[Route] | Route):
        """Add a route to the local HybridRouter and index.

        :param route: The route to add.
        :type route: Route
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        self.routes.extend(routes)
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb, sparse_emb = self._encode(all_utterances, input_type='documents')
        self.index.add(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata, sparse_embeddings=sparse_emb)
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    async def aadd(self, routes: List[Route] | Route):
        """Add a route to the local HybridRouter and index asynchronously.

        :param routes: The route(s) to add.
        :type routes: List[Route] | Route
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        current_local_hash = self._get_hash()
        current_remote_hash = await self.index._async_read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        self.routes.extend(routes)
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb, sparse_emb = await self._async_encode(all_utterances, input_type='documents')
        await self.index.aadd(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata, sparse_embeddings=sparse_emb)
        if current_local_hash.value == current_remote_hash.value:
            await self._async_write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    def _execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse Encoder not initialised.')
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            self.index._remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            dense_emb, sparse_emb = self._encode(utterances_text, input_type='documents')
            self.index.add(embeddings=dense_emb.tolist(), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']], sparse_embeddings=sparse_emb)
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        self._write_hash()
        if isinstance(self.sparse_encoder, FittableMixin) and self.routes:
            self.sparse_encoder.fit(self.routes)

    def _get_index(self, index: Optional[BaseIndex]) -> BaseIndex:
        """Get the index.

        :param index: The index to get.
        :type index: Optional[BaseIndex]
        :return: The index.
        :rtype: BaseIndex
        """
        if index is None:
            logger.warning('No index provided. Using default HybridLocalIndex.')
            index = HybridLocalIndex()
        else:
            index = index
        return index

    def _get_sparse_encoder(self, sparse_encoder: Optional[SparseEncoder]) -> SparseEncoder:
        """Get the sparse encoder.

        :param sparse_encoder: The sparse encoder to get.
        :type sparse_encoder: Optional[SparseEncoder]
        :return: The sparse encoder.
        :rtype: Optional[SparseEncoder]
        """
        if sparse_encoder is None:
            logger.warning('No sparse_encoder provided. Using default BM25Encoder.')
            sparse_encoder = BM25Encoder()
        else:
            sparse_encoder = sparse_encoder
        return sparse_encoder

    def _encode(self, text: list[str], input_type: EncodeInputType) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Given some text, generates dense and sparse embeddings, then scales them
        using the chosen alpha value.

        :param text: List of texts to encode
        :type text: List[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: Tuple of dense and sparse embeddings
        """
        if self.sparse_encoder is None:
            raise ValueError('self.sparse_encoder is not set.')
        if isinstance(self.encoder, AsymmetricDenseMixin):
            match input_type:
                case 'queries':
                    dense_v = self.encoder.encode_queries(text)
                case 'documents':
                    dense_v = self.encoder.encode_documents(text)
        else:
            dense_v = self.encoder(text)
        xq_d = np.array(dense_v)
        if isinstance(self.sparse_encoder, AsymmetricSparseMixin):
            match input_type:
                case 'queries':
                    xq_s = self.sparse_encoder.encode_queries(text)
                case 'documents':
                    xq_s = self.sparse_encoder.encode_documents(text)
        else:
            xq_s = self.sparse_encoder(text)
        xq_d, xq_s = self._convex_scaling(dense=xq_d, sparse=xq_s)
        return (xq_d, xq_s)

    async def _async_encode(self, text: List[str], input_type: EncodeInputType) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Given some text, generates dense and sparse embeddings, then scales them
        using the chosen alpha value.

        :param text: The text to encode.
        :type text: List[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: A tuple of the dense and sparse embeddings.
        :rtype: tuple[np.ndarray, list[SparseEmbedding]]
        """
        if self.sparse_encoder is None:
            raise ValueError('self.sparse_encoder is not set.')
        if isinstance(self.encoder, AsymmetricDenseMixin):
            match input_type:
                case 'queries':
                    dense_coro = self.encoder.aencode_queries(text)
                case 'documents':
                    dense_coro = self.encoder.aencode_documents(text)
        else:
            dense_coro = self.encoder.acall(text)
        if isinstance(self.sparse_encoder, AsymmetricSparseMixin):
            match input_type:
                case 'queries':
                    sparse_coro = self.sparse_encoder.aencode_queries(text)
                case 'documents':
                    sparse_coro = self.sparse_encoder.aencode_documents(text)
        else:
            sparse_coro = self.sparse_encoder.acall(text)
        dense_vec, xq_s = await asyncio.gather(dense_coro, sparse_coro)
        xq_d = np.array(dense_vec)
        xq_d, xq_s = self._convex_scaling(dense=xq_d, sparse=xq_s)
        return (xq_d, xq_s)

    def __call__(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, simulate_static: bool=False, route_filter: Optional[List[str]]=None, limit: int | None=1, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> RouteChoice | list[RouteChoice]:
        """Call the HybridRouter.

        :param text: The text to encode.
        :type text: Optional[str]
        :param vector: The vector to encode.
        :type vector: Optional[List[float] | np.ndarray]
        :param simulate_static: Whether to simulate a static route.
        :type simulate_static: bool
        :param route_filter: The route filter to use.
        :type route_filter: Optional[List[str]]
        :param limit: The number of routes to return, defaults to 1. If set to None, no
            limit is applied and all routes are returned.
        :type limit: int | None
        :param sparse_vector: The sparse vector to use.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A RouteChoice or a list of RouteChoices.
        :rtype: RouteChoice | list[RouteChoice]
        """
        if not self.index.is_ready():
            raise ValueError('Index is not ready.')
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        potential_sparse_vector: List[SparseEmbedding] | None = None
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            xq_d = np.array(self.encoder([text]))
            xq_s = self.sparse_encoder([text])
            vector, potential_sparse_vector = self._convex_scaling(dense=xq_d, sparse=xq_s)
        vector = xq_reshape(vector)
        if sparse_vector is None:
            if text is None:
                raise ValueError('Either text or sparse_vector must be provided')
            sparse_vector = potential_sparse_vector[0] if potential_sparse_vector else None
        if sparse_vector is None:
            raise ValueError('Sparse vector is required for HybridLocalIndex.')
        scores, route_names = self.index.query(vector=vector[0], top_k=self.top_k, route_filter=route_filter, sparse_vector=sparse_vector)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(route_names, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        route_choices = self._pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)
        return route_choices

    async def acall(self, text: Optional[str]=None, vector: Optional[List[float] | np.ndarray]=None, limit: int | None=1, simulate_static: bool=False, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> RouteChoice | list[RouteChoice]:
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
        :param sparse_vector: The sparse vector to use.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: The route choice.
        :rtype: RouteChoice
        """
        if not await self.index.ais_ready():
            await self._async_init_index_state()
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        potential_sparse_vector: List[SparseEmbedding] | None = None
        if vector is None:
            if text is None:
                raise ValueError('Either text or vector must be provided')
            vector, potential_sparse_vector = await self._async_encode(text=[text], input_type='queries')
        vector = xq_reshape(xq=vector)
        if sparse_vector is None:
            if text is None:
                raise ValueError('Either text or sparse_vector must be provided')
            sparse_vector = potential_sparse_vector[0] if potential_sparse_vector else None
        scores, routes = await self.index.aquery(vector=vector[0], top_k=self.top_k, route_filter=route_filter, sparse_vector=sparse_vector)
        query_results = [{'route': d, 'score': s.item()} for d, s in zip(routes, scores)]
        scored_routes = self._score_routes(query_results=query_results)
        return await self._async_pass_routes(scored_routes=scored_routes, simulate_static=simulate_static, text=text, limit=limit)

    async def _async_execute_sync_strategy(self, strategy: Dict[str, Dict[str, List[Utterance]]]):
        """Executes the provided sync strategy, either deleting or upserting
        routes from the local and remote instances as defined in the strategy.

        :param strategy: The sync strategy to execute.
        :type strategy: Dict[str, Dict[str, List[Utterance]]]
        """
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        if strategy['remote']['delete']:
            data_to_delete = {}
            for utt_obj in strategy['remote']['delete']:
                data_to_delete.setdefault(utt_obj.route, []).append(utt_obj.utterance)
            await self.index._async_remove_and_sync(data_to_delete)
        if strategy['remote']['upsert']:
            utterances_text = [utt.utterance for utt in strategy['remote']['upsert']]
            await self.index.aadd(embeddings=await self.encoder.acall(docs=utterances_text), sparse_embeddings=await self.sparse_encoder.acall(docs=utterances_text), routes=[utt.route for utt in strategy['remote']['upsert']], utterances=utterances_text, function_schemas=[utt.function_schemas for utt in strategy['remote']['upsert']], metadata_list=[utt.metadata for utt in strategy['remote']['upsert']])
        if strategy['local']['delete']:
            self._local_delete(utterances=strategy['local']['delete'])
        if strategy['local']['upsert']:
            self._local_upsert(utterances=strategy['local']['upsert'])
        await self._async_write_hash()

    def _convex_scaling(self, dense: np.ndarray, sparse: list[SparseEmbedding]) -> tuple[np.ndarray, list[SparseEmbedding]]:
        """Convex scaling of the dense and sparse vectors.

        :param dense: The dense vector to scale.
        :type dense: np.ndarray
        :param sparse: The sparse vector to scale.
        :type sparse: list[SparseEmbedding]
        """
        sparse_dicts = [sparse_vec.to_dict() for sparse_vec in sparse]
        scaled_dense = np.array(dense) * self.alpha
        scaled_sparse = []
        for sparse_dict in sparse_dicts:
            scaled_sparse.append(SparseEmbedding.from_dict({k: v * (1 - self.alpha) for k, v in sparse_dict.items()}))
        return (scaled_dense, scaled_sparse)

    def fit(self, X: List[str], y: List[str], batch_size: int=500, max_iter: int=500, local_execution: bool=False):
        """Fit the HybridRouter.

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
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        if local_execution:
            from semantic_router.index.hybrid_local import HybridLocalIndex
            remote_utterances = self.index.get_utterances(include_metadata=True)
            routes = []
            utterances = []
            metadata = []
            for utterance in remote_utterances:
                routes.append(utterance.route)
                utterances.append(utterance.utterance)
                metadata.append(utterance.metadata)
            embeddings = self.encoder(utterances) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_documents(utterances)
            sparse_embeddings = self.sparse_encoder(utterances) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_documents(utterances)
            self.index = HybridLocalIndex()
            self.index.add(embeddings=embeddings, sparse_embeddings=sparse_embeddings, routes=routes, utterances=utterances, metadata_list=metadata)
        Xq_d: List[List[float]] = []
        Xq_s: List[SparseEmbedding] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
            emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
            Xq_d.extend(emb_d)
            Xq_s.extend(emb_s)
        best_acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
        best_thresholds = self.get_thresholds()
        for _ in (pbar := tqdm(range(max_iter), desc='Training')):
            pbar.set_postfix({'acc': round(best_acc, 2)})
            thresholds = threshold_random_search(route_layer=self, search_range=0.8)
            self._update_thresholds(route_thresholds=thresholds)
            acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
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
        if self.sparse_encoder is None:
            raise ValueError('Sparse encoder is not set.')
        Xq_d: List[List[float]] = []
        Xq_s: List[SparseEmbedding] = []
        for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
            emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
            emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
            Xq_d.extend(emb_d)
            Xq_s.extend(emb_s)
        accuracy = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
        return accuracy

    def _vec_evaluate(self, Xq_d: Union[List[float], Any], Xq_s: list[SparseEmbedding], y: List[str]) -> float:
        """Evaluate the accuracy of the route selection.

        :param Xq_d: The dense vectors to evaluate.
        :type Xq_d: Union[List[float], Any]
        :param Xq_s: The sparse vectors to evaluate.
        :type Xq_s: list[SparseEmbedding]
        :param y: The output data.
        :type y: List[str]
        :return: The accuracy of the route selection.
        :rtype: float
        """
        correct = 0
        for xq_d, xq_s, target_route in zip(Xq_d, Xq_s, y):
            route_choice = self(vector=xq_d, sparse_vector=xq_s, simulate_static=True)
            if isinstance(route_choice, list):
                route_name = route_choice[0].name
            else:
                route_name = route_choice.name
            if route_name == target_route:
                correct += 1
        accuracy = correct / len(Xq_d)
        return accuracy

def _encode(self, text: list[str], input_type: EncodeInputType) -> tuple[np.ndarray, list[SparseEmbedding]]:
    """Given some text, generates dense and sparse embeddings, then scales them
        using the chosen alpha value.

        :param text: List of texts to encode
        :type text: List[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: Tuple of dense and sparse embeddings
        """
    if self.sparse_encoder is None:
        raise ValueError('self.sparse_encoder is not set.')
    if isinstance(self.encoder, AsymmetricDenseMixin):
        match input_type:
            case 'queries':
                dense_v = self.encoder.encode_queries(text)
            case 'documents':
                dense_v = self.encoder.encode_documents(text)
    else:
        dense_v = self.encoder(text)
    xq_d = np.array(dense_v)
    if isinstance(self.sparse_encoder, AsymmetricSparseMixin):
        match input_type:
            case 'queries':
                xq_s = self.sparse_encoder.encode_queries(text)
            case 'documents':
                xq_s = self.sparse_encoder.encode_documents(text)
    else:
        xq_s = self.sparse_encoder(text)
    xq_d, xq_s = self._convex_scaling(dense=xq_d, sparse=xq_s)
    return (xq_d, xq_s)

def fit(self, X: List[str], y: List[str], batch_size: int=500, max_iter: int=500, local_execution: bool=False):
    """Fit the HybridRouter.

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
    if self.sparse_encoder is None:
        raise ValueError('Sparse encoder is not set.')
    if local_execution:
        from semantic_router.index.hybrid_local import HybridLocalIndex
        remote_utterances = self.index.get_utterances(include_metadata=True)
        routes = []
        utterances = []
        metadata = []
        for utterance in remote_utterances:
            routes.append(utterance.route)
            utterances.append(utterance.utterance)
            metadata.append(utterance.metadata)
        embeddings = self.encoder(utterances) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_documents(utterances)
        sparse_embeddings = self.sparse_encoder(utterances) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_documents(utterances)
        self.index = HybridLocalIndex()
        self.index.add(embeddings=embeddings, sparse_embeddings=sparse_embeddings, routes=routes, utterances=utterances, metadata_list=metadata)
    Xq_d: List[List[float]] = []
    Xq_s: List[SparseEmbedding] = []
    for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
        emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
        emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
        Xq_d.extend(emb_d)
        Xq_s.extend(emb_s)
    best_acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
    best_thresholds = self.get_thresholds()
    for _ in (pbar := tqdm(range(max_iter), desc='Training')):
        pbar.set_postfix({'acc': round(best_acc, 2)})
        thresholds = threshold_random_search(route_layer=self, search_range=0.8)
        self._update_thresholds(route_thresholds=thresholds)
        acc = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
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
    if self.sparse_encoder is None:
        raise ValueError('Sparse encoder is not set.')
    Xq_d: List[List[float]] = []
    Xq_s: List[SparseEmbedding] = []
    for i in tqdm(range(0, len(X), batch_size), desc='Generating embeddings'):
        emb_d = np.array(self.encoder(X[i:i + batch_size]) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(X[i:i + batch_size]))
        emb_s = self.sparse_encoder(X[i:i + batch_size]) if not isinstance(self.sparse_encoder, AsymmetricSparseMixin) else self.sparse_encoder.encode_queries(X[i:i + batch_size])
        Xq_d.extend(emb_d)
        Xq_s.extend(emb_s)
    accuracy = self._vec_evaluate(Xq_d=np.array(Xq_d), Xq_s=Xq_s, y=y)
    return accuracy

class SemanticRouter(BaseRouter):
    """A router that uses a dense encoder to encode routes and utterances."""

    def __init__(self, encoder: Optional[DenseEncoder]=None, llm: Optional[BaseLLM]=None, routes: Optional[List[Route]]=None, index: Optional[BaseIndex]=None, top_k: int=5, aggregation: str='mean', auto_sync: Optional[str]=None, init_async_index: bool=False):
        index = self._get_index(index=index)
        encoder = self._get_encoder(encoder=encoder)
        super().__init__(encoder=encoder, llm=llm, routes=routes if routes else [], index=index, top_k=top_k, aggregation=aggregation, auto_sync=auto_sync, init_async_index=init_async_index)

    def _encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Given some text, encode it.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The encoded text.
        :rtype: Any
        """
        match input_type:
            case 'queries':
                xq = np.array(self.encoder(text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(text))
            case 'documents':
                xq = np.array(self.encoder(text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_documents(text))
        return xq

    async def _async_encode(self, text: list[str], input_type: EncodeInputType) -> Any:
        """Given some text, encode it.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The encoded text.
        :rtype: Any
        """
        match input_type:
            case 'queries':
                xq = np.array(await (self.encoder.acall(docs=text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.aencode_queries(docs=text)))
            case 'documents':
                xq = np.array(await (self.encoder.acall(docs=text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.aencode_documents(docs=text)))
        return xq

    def add(self, routes: List[Route] | Route):
        """Add a route to the local SemanticRouter and index.

        :param route: The route to add.
        :type route: Route
        """
        current_local_hash = self._get_hash()
        current_remote_hash = self.index._read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb = self._encode(all_utterances, input_type='documents')
        self.index.add(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata)
        self.routes.extend(routes)
        if current_local_hash.value == current_remote_hash.value:
            self._write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

    async def aadd(self, routes: List[Route] | Route):
        """Asynchronously add a route to the local SemanticRouter and index.

        :param routes: The route(s) to add.
        :type routes: List[Route] | Route
        """
        if not await self.index.ais_ready():
            await self._async_init_index_state()
        current_local_hash = self._get_hash()
        current_remote_hash = await self.index._async_read_hash()
        if current_remote_hash.value == '':
            current_remote_hash = current_local_hash
        if isinstance(routes, Route):
            routes = [routes]
        route_names, all_utterances, all_function_schemas, all_metadata = self._extract_routes_details(routes, include_metadata=True)
        dense_emb = await self._async_encode(all_utterances, input_type='documents')
        await self.index.aadd(embeddings=dense_emb.tolist(), routes=route_names, utterances=all_utterances, function_schemas=all_function_schemas, metadata_list=all_metadata)
        self.routes.extend(routes)
        if current_local_hash.value == current_remote_hash.value:
            await self._async_write_hash()
        else:
            logger.warning(f'Local and remote route layers were not aligned. Remote hash not updated. Use `{self.__class__.__name__}.get_utterance_diff()` to see details.')

def _encode(self, text: list[str], input_type: EncodeInputType) -> Any:
    """Given some text, encode it.

        :param text: The text to encode.
        :type text: list[str]
        :param input_type: Specify whether encoding 'queries' or 'documents', used in asymmetric retrieval
        :type input_type: semantic_router.encoders.encode_input_type.EncodeInputType
        :return: The encoded text.
        :rtype: Any
        """
    match input_type:
        case 'queries':
            xq = np.array(self.encoder(text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_queries(text))
        case 'documents':
            xq = np.array(self.encoder(text) if not isinstance(self.encoder, AsymmetricDenseMixin) else self.encoder.encode_documents(text))
    return xq

class MockSymmetricSparseEncoder(SparseEncoder):

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    async def acall(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
    return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

class MockAsymmetricSparseEncoder(SparseEncoder, AsymmetricSparseMixin):

    def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    async def acall(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    def encode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    def encode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    async def aencode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

    async def aencode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
        return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

def __call__(self, docs: List[str]) -> List[SparseEmbedding]:
    return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

def encode_queries(self, docs: List[str]) -> List[SparseEmbedding]:
    return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

def encode_documents(self, docs: List[str]) -> List[SparseEmbedding]:
    return [SparseEmbedding(embedding=np.array([[0, 0.1], [1, 0.2]])) for _ in docs]

class TestBM25Encoder:

    def test_initialization(self, bm25_encoder):
        assert bm25_encoder._tokenizer is not None

    def test_fit(self, bm25_encoder, routes):
        bm25_encoder.fit(routes)
        assert bm25_encoder._tokenizer is not None

    def test_fit_with_strings(self, bm25_encoder):
        route_strings = ['test a', 'test b', 'test c']
        with pytest.raises(TypeError):
            bm25_encoder.fit(route_strings)

    def test_call_method(self, bm25_encoder):
        result = bm25_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sparse_emb.embedding, np.ndarray) for sparse_emb in result)), 'Each item in result should be an array'

    def test_call_method_no_docs_bm25_encoder(self, bm25_encoder):
        with pytest.raises(ValueError):
            bm25_encoder([])

    def test_call_method_no_word(self, bm25_encoder):
        result = bm25_encoder(['doc with fake word gta5jabcxyz'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sparse_emb.embedding, np.ndarray) for sparse_emb in result)), 'Each item in result should be an array'

    def test_call_method_with_uninitialized_model_or_mapping(self, bm25_encoder):
        bm25_encoder._tokenizer = None
        with pytest.raises(ValueError):
            bm25_encoder(['test'])

    def test_fit_with_uninitialized_model(self, bm25_encoder, routes):
        bm25_encoder._tokenizer = None
        with pytest.raises(ValueError):
            bm25_encoder.fit(routes)

    def test_encode_queries(self, bm25_encoder):
        queries = ['quick brown', 'lazy dog', 'hello world']
        results = bm25_encoder.encode_queries(queries)
        assert len(results) == len(queries)
        assert all([isinstance(result.embedding, np.ndarray) for result in results])

    def test_encode_queries_empty_list(self, bm25_encoder):
        with pytest.raises(ValueError, match='No documents provided for encoding'):
            bm25_encoder.encode_queries([])

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
    def test_encode_queries_unfitted(self):
        encoder = BM25Encoder(use_default_params=True)
        with pytest.raises(ValueError, match='Encoder not fitted'):
            encoder.encode_queries(['test query'])

    def test_encode_documents(self, bm25_encoder):
        documents = ['quick brown', 'lazy dog', 'hello world']
        results = bm25_encoder.encode_documents(documents)
        assert len(results) == len(documents)
        assert all([isinstance(result.embedding, np.ndarray) for result in results])

    def test_encode_documents_empty_list(self, bm25_encoder):
        with pytest.raises(ValueError, match='No documents provided for encoding'):
            bm25_encoder.encode_documents([])

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
    def test_encode_documents_unfitted(self):
        encoder = BM25Encoder(use_default_params=True)
        with pytest.raises(ValueError, match='Encoder not fitted'):
            encoder.encode_documents(['test document'])

    def test_encode_documents_batch_size(self, bm25_encoder):
        documents = ['quick brown', 'lazy dog', 'hello world', 'test document']
        batch_size = 2
        results = bm25_encoder.encode_documents(documents, batch_size=batch_size)
        assert len(results) == len(documents)
        assert all((isinstance(result.embedding, np.ndarray) for result in results))

def test_encode_queries(self, bm25_encoder):
    queries = ['quick brown', 'lazy dog', 'hello world']
    results = bm25_encoder.encode_queries(queries)
    assert len(results) == len(queries)
    assert all([isinstance(result.embedding, np.ndarray) for result in results])

def test_encode_queries_empty_list(self, bm25_encoder):
    with pytest.raises(ValueError, match='No documents provided for encoding'):
        bm25_encoder.encode_queries([])

def test_encode_documents(self, bm25_encoder):
    documents = ['quick brown', 'lazy dog', 'hello world']
    results = bm25_encoder.encode_documents(documents)
    assert len(results) == len(documents)
    assert all([isinstance(result.embedding, np.ndarray) for result in results])

def test_encode_documents_empty_list(self, bm25_encoder):
    with pytest.raises(ValueError, match='No documents provided for encoding'):
        bm25_encoder.encode_documents([])

def test_encode_documents_batch_size(self, bm25_encoder):
    documents = ['quick brown', 'lazy dog', 'hello world', 'test document']
    batch_size = 2
    results = bm25_encoder.encode_documents(documents, batch_size=batch_size)
    assert len(results) == len(documents)
    assert all((isinstance(result.embedding, np.ndarray) for result in results))

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

def test_fit(self, tfidf_encoder):
    routes = [Route(name='test_route', utterances=['some docs', 'and more docs', 'and even more docs'])]
    tfidf_encoder.fit(routes)
    assert tfidf_encoder.word_index != {}
    assert not np.array_equal(tfidf_encoder.idf, np.array([]))

@pytest.mark.parametrize('provider, model_in, model_name, api_key_env_var, encoder', matrix)
class TestEncoders:

    def test_initialization_with_api_key(self, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        enc = encoder(model_in)
        assert enc.name == model_name, 'Default name not set correctly'
        assert enc.type == provider, 'Default type/provider not set correctly'

    def test_initialization_without_api_key(self, monkeypatch, provider, model_in, model_name, api_key_env_var, encoder):
        monkeypatch.delenv(api_key_env_var, raising=False)
        with pytest.raises(ValueError):
            encoder()

    def test_call_method(self, mock_litellm, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        result = encoder(model_in)(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_returns_list_of_embeddings_for_valid_input(self, mock_litellm, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        result = encoder(model_in)(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_handles_multiple_inputs_correctly(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        mock_embed = litellm.EmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding'), Embedding(embedding=[0.4, 0.5, 0.6], index=1, object='embedding')])
        mocker.patch.object(litellm, 'embedding', return_value=mock_embed)
        result = encoder(model_in)(['test1', 'test2'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        litellm.embedding.assert_called_once()

    def test_call_method_raises_error_on_api_failure(self, mocker, provider, model_in, model_name, api_key_env_var, encoder):
        os.environ[api_key_env_var] = 'test_api_key'
        mocker.patch.object(litellm, 'embedding', side_effect=Exception('API call failed'))
        with pytest.raises(ValueError):
            encoder(model_in)(['test'])

def test_initialization_with_api_key(self, provider, model_in, model_name, api_key_env_var, encoder):
    os.environ[api_key_env_var] = 'test_api_key'
    enc = encoder(model_in)
    assert enc.name == model_name, 'Default name not set correctly'
    assert enc.type == provider, 'Default type/provider not set correctly'

@pytest.fixture
def test_index():
    return np.array([[3, 0, 0], [2, 1, 0], [0, 1, 0]])

def test_similarity_matrix__dimensionality():
    """Test that the similarity matrix is square."""
    xq = np.random.random((10,))
    index = np.random.random((100, 10))
    S = similarity_matrix(xq, index)
    assert S.shape == (100,)

def test_top_scores__is_sorted(test_index):
    """
    Test that the top_scores function returns a sorted list of scores.
    """
    xq = test_index[0]
    sim = similarity_matrix(xq, test_index)
    _, idx = top_scores(sim, 3)
    assert np.array_equal(idx, np.array([2, 1, 0]))

def test_top_scores__scores(test_index):
    """
    Test that for a known vector and a known index, the top_scores function
    returns exactly the expected scores.
    """
    xq = test_index[0]
    sim = similarity_matrix(xq, test_index)
    scores, _ = top_scores(sim, 3)
    assert np.allclose(scores, np.array([0.0, 0.89442719, 1.0]))

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

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
def test_bm25_scoring(self, bm25_encoder):
    vocab_size = bm25_encoder._tokenizer.vocab_size
    expected = np.array([[0.0, 0.0, 0.54575, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.18864, 0.0, 0.67897, 0.0]])
    q_e = np.stack([self._sparse_to_vector(v.embedding, vocab_size=vocab_size) for v in bm25_encoder.encode_queries(QUERIES)])
    d_e = np.stack([self._sparse_to_vector(v.embedding, vocab_size=vocab_size) for v in bm25_encoder.encode_documents(UTTERANCES)])
    scores = q_e @ d_e.T
    assert np.allclose(scores, expected, rtol=0.0001), expected

