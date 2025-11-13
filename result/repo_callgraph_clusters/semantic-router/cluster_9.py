# Cluster 9

class QdrantIndex(BaseIndex):
    """The name of the collection to use"""
    index_name: str = Field(default=DEFAULT_COLLECTION_NAME, description=f"Name of the Qdrant collection.Default: '{DEFAULT_COLLECTION_NAME}'")
    location: Optional[str] = Field(default=':memory:', description="If ':memory:' - use an in-memory Qdrant instance.Used as 'url' value otherwise")
    url: Optional[str] = Field(default=None, description='Qualified URL of the Qdrant instance.Optional[scheme], host, Optional[port], Optional[prefix]')
    port: Optional[int] = Field(default=6333, description='Port of the REST API interface.')
    grpc_port: int = Field(default=6334, description='Port of the gRPC interface.')
    prefer_grpc: Optional[bool] = Field(default=None, description='Whether to use gPRC interface whenever possible in methods')
    https: Optional[bool] = Field(default=None, description='Whether to use HTTPS(SSL) protocol.')
    api_key: Optional[str] = Field(default=None, description='API key for authentication in Qdrant Cloud.')
    prefix: Optional[str] = Field(default=None, description='Prefix to the REST URL path. Example: `http://localhost:6333/some/prefix/{qdrant-endpoint}`.')
    timeout: Optional[int] = Field(default=None, description='Timeout for REST and gRPC API requests.')
    host: Optional[str] = Field(default=None, description="Host name of Qdrant service.If url and host are None, set to 'localhost'.")
    path: Optional[str] = Field(default=None, description='Persistence path for Qdrant local')
    grpc_options: Optional[Dict[str, Any]] = Field(default=None, description='Options to be passed to the low-level GRPC client, if used.')
    dimensions: Union[int, None] = Field(default=None, description='Embedding dimensions.Defaults to the embedding length of the configured encoder.')
    metric: Metric = Field(default=Metric.COSINE, description='Distance metric to use for similarity search.')
    config: Optional[Dict[str, Any]] = Field(default={}, description='Collection options passed to `QdrantClient#create_collection`.')
    client: Any = Field(default=None, exclude=True)
    aclient: Any = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type = 'qdrant'
        self.client, self.aclient = self._initialize_clients()

    def _initialize_clients(self):
        """Initialize the clients for the Qdrant index.

        :return: A tuple of the sync and async clients.
        :rtype: Tuple[QdrantClient, Optional[AsyncQdrantClient]]
        """
        try:
            from qdrant_client import AsyncQdrantClient, QdrantClient
            sync_client = QdrantClient(location=self.location, url=self.url, port=self.port, grpc_port=self.grpc_port, prefer_grpc=self.prefer_grpc, https=self.https, api_key=self.api_key, prefix=self.prefix, timeout=self.timeout, host=self.host, path=self.path, grpc_options=self.grpc_options)
            async_client: Optional[AsyncQdrantClient] = None
            if all([self.location != ':memory:', self.path is None]):
                async_client = AsyncQdrantClient(location=self.location, url=self.url, port=self.port, grpc_port=self.grpc_port, prefer_grpc=self.prefer_grpc, https=self.https, api_key=self.api_key, prefix=self.prefix, timeout=self.timeout, host=self.host, path=self.path, grpc_options=self.grpc_options)
            return (sync_client, async_client)
        except ImportError as e:
            raise ImportError("Please install 'qdrant-client' to use QdrantIndex.You can install it with: `pip install 'semantic-router[qdrant]'`") from e

    def _init_collection(self) -> None:
        """Initialize the collection for the Qdrant index.

        :return: None
        :rtype: None
        """
        from qdrant_client import QdrantClient, models
        self.client: QdrantClient
        if not self.client.collection_exists(self.index_name):
            if not self.dimensions:
                raise ValueError('Cannot create a collection without specifying the dimensions.')
            self.client.create_collection(collection_name=self.index_name, vectors_config=models.VectorParams(size=self.dimensions, distance=self.convert_metric(self.metric)), **self.config)

    def _remove_and_sync(self, routes_to_delete: dict):
        """Remove and sync the index.

        :param routes_to_delete: The routes to delete.
        :type routes_to_delete: dict
        """
        logger.error('Sync remove is not implemented for QdrantIndex.')

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=DEFAULT_UPLOAD_BATCH_SIZE, **kwargs):
        """Add records to the index.

        :param embeddings: The embeddings to add.
        :type embeddings: List[List[float]]
        :param routes: The routes to add.
        :type routes: List[str]
        :param utterances: The utterances to add.
        :type utterances: List[str]
        :param function_schemas: The function schemas to add.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: The metadata to add.
        :type metadata_list: List[Dict[str, Any]]
        :param batch_size: The batch size to use for the upload.
        :type batch_size: int
        """
        self.dimensions = self.dimensions or len(embeddings[0])
        self._init_collection()
        ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{route}:{utterance}')) for route, utterance in zip(routes, utterances)]
        if not metadata_list or len(metadata_list) != len(utterances):
            metadata_list = [{} for _ in utterances]
        payloads = [{SR_ROUTE_PAYLOAD_KEY: route, SR_UTTERANCE_PAYLOAD_KEY: utterance, 'metadata': metadata if metadata is not None else {}} for route, utterance, metadata in zip(routes, utterances, metadata_list)]
        self.client.upload_collection(self.index_name, vectors=embeddings, payload=payloads, ids=ids, batch_size=batch_size)

    def get_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Gets a list of route and utterance objects currently stored in the index.

        :param include_metadata: Whether to include function schemas and metadata in
        the returned Utterance objects - QdrantIndex does not currently support this
        parameter so it is ignored. If required for your use-case please reach out to
        semantic-router maintainers on GitHub via an issue or PR.
        :type include_metadata: bool
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if not self.client.collection_exists(self.index_name):
            return []
        from qdrant_client import grpc
        results = []
        next_offset = None
        stop_scrolling = False
        try:
            while not stop_scrolling:
                records, next_offset = self.client.scroll(self.index_name, limit=SCROLL_SIZE, offset=next_offset, with_payload=True)
                stop_scrolling = next_offset is None or (isinstance(next_offset, grpc.PointId) and next_offset.num == 0 and (next_offset.uuid == ''))
                results.extend(records)
            utterances: List[Utterance] = [Utterance(route=x.payload[SR_ROUTE_PAYLOAD_KEY], utterance=x.payload[SR_UTTERANCE_PAYLOAD_KEY], function_schemas=None, metadata=x.payload.get('metadata', {})) for x in results]
        except ValueError as e:
            logger.warning(f'Index likely empty, error: {e}')
            return []
        return utterances

    def delete(self, route_name: str):
        """Delete records from the index.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
        from qdrant_client import models
        self.client.delete(self.index_name, points_selector=models.Filter(must=[models.FieldCondition(key=SR_ROUTE_PAYLOAD_KEY, match=models.MatchText(text=route_name))]))

    def describe(self) -> IndexConfig:
        """Describe the index.

        :return: The index configuration.
        :rtype: IndexConfig
        """
        collection_info = self.client.get_collection(self.index_name)
        return IndexConfig(type=self.type, dimensions=collection_info.config.params.vectors.size, vectors=collection_info.points_count)

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.client.collection_exists(self.index_name)

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Query the index.

        :param vector: The vector to query.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The route filter to apply.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to query.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple of the scores and route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        from qdrant_client import QdrantClient, models
        self.client: QdrantClient
        filter = None
        if route_filter is not None:
            filter = models.Filter(must=[models.FieldCondition(key=SR_ROUTE_PAYLOAD_KEY, match=models.MatchAny(any=route_filter))])
        results = self.client.query_points(self.index_name, query=vector, limit=top_k, with_payload=True, query_filter=filter)
        scores = [result.score for result in results.points]
        route_names = [result.payload[SR_ROUTE_PAYLOAD_KEY] for result in results.points]
        return (np.array(scores), route_names)

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Asynchronously query the index.

        :param vector: The vector to query.
        :type vector: np.ndarray
        :param top_k: The number of results to return.
        :type top_k: int
        :param route_filter: The route filter to apply.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: The sparse vector to query.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple of the scores and route names.
        :rtype: Tuple[np.ndarray, List[str]]
        """
        from qdrant_client import AsyncQdrantClient, models
        self.aclient: Optional[AsyncQdrantClient]
        if self.aclient is None:
            logger.warning('Cannot use async query with an in-memory Qdrant instance')
            return self.query(vector, top_k, route_filter)
        filter = None
        if route_filter is not None:
            filter = models.Filter(must=[models.FieldCondition(key=SR_ROUTE_PAYLOAD_KEY, match=models.MatchAny(any=route_filter))])
        results = await self.aclient.query_points(self.index_name, query=vector, limit=top_k, with_payload=True, query_filter=filter)
        scores = [result.score for result in results.points]
        route_names = [result.payload[SR_ROUTE_PAYLOAD_KEY] for result in results.points]
        return (np.array(scores), route_names)

    def aget_routes(self):
        """Asynchronously get all routes from the index.

        :return: A list of routes.
        :rtype: List[str]
        """
        logger.error('Sync remove is not implemented for QdrantIndex.')

    def delete_index(self):
        """Delete the index.

        :return: None
        :rtype: None
        """
        self.client.delete_collection(self.index_name)

    def convert_metric(self, metric: Metric):
        """Convert the metric to a Qdrant distance metric.

        :param metric: The metric to convert.
        :type metric: Metric
        :return: The converted metric.
        :rtype: Distance
        """
        from qdrant_client.models import Distance
        mapping = {Metric.COSINE: Distance.COSINE, Metric.EUCLIDEAN: Distance.EUCLID, Metric.DOTPRODUCT: Distance.DOT, Metric.MANHATTAN: Distance.MANHATTAN}
        if metric not in mapping:
            raise ValueError(f'Unsupported Qdrant similarity metric: {metric}')
        return mapping[metric]

    def _init_config_collection(self):
        """Ensure the config collection exists."""
        from qdrant_client import models
        if not self.client.collection_exists('sr_config'):
            self.client.create_collection(collection_name='sr_config', vectors_config=models.VectorParams(size=1, distance=self.convert_metric(self.metric)))

    def _config_point_id(self, field: str, scope: str | None=None) -> str:
        """Generate a deterministic UUID string for config/hash/lock points."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{field}#{scope or self.index_name}'))

    def _write_config(self, config: ConfigParameter):
        """Write a config parameter to the Qdrant config collection."""
        self._init_config_collection()
        from qdrant_client import models
        point_id = self._config_point_id(config.field, config.scope)
        payload = {'field': config.field, 'scope': config.scope or self.index_name, 'value': config.value, 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        self.client.upsert(collection_name='sr_config', points=[models.PointStruct(id=point_id, vector=[0.0], payload=payload)])
        return config

    def _read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the Qdrant config collection."""
        self._init_config_collection()
        point_id = self._config_point_id(field, scope)
        res = self.client.retrieve(collection_name='sr_config', ids=[point_id], with_payload=True)
        if res:
            payload = res[0].payload
            return ConfigParameter(field=payload.get('field', field), value=payload.get('value', ''), created_at=payload.get('created_at'), scope=payload.get('scope', scope or self.index_name))
        else:
            logger.warning(f'Configuration for {field} parameter not found in Qdrant.')
            return ConfigParameter(field=field, value='', scope=scope or self.index_name)

    async def _async_write_config(self, config: ConfigParameter):
        self._init_config_collection()
        from qdrant_client import models
        point_id = self._config_point_id(config.field, config.scope)
        payload = {'field': config.field, 'scope': config.scope or self.index_name, 'value': config.value, 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        if self.aclient is None:
            return self._write_config(config)
        await self.aclient.upsert(collection_name='sr_config', points=[models.PointStruct(id=point_id, vector=[0.0], payload=payload)])
        return config

    async def _async_read_config(self, field: str, scope: str | None=None):
        self._init_config_collection()
        point_id = self._config_point_id(field, scope)
        if self.aclient is None:
            return self._read_config(field, scope)
        res = await self.aclient.retrieve(collection_name='sr_config', ids=[point_id], with_payload=True)
        if res:
            payload = res[0].payload
            return ConfigParameter(field=payload.get('field', field), value=payload.get('value', ''), created_at=payload.get('created_at'), scope=payload.get('scope', scope or self.index_name))
        else:
            logger.warning(f'Configuration for {field} parameter not found in Qdrant.')
            return ConfigParameter(field=field, value='', scope=scope or self.index_name)

    def __len__(self):
        """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        try:
            return self.client.get_collection(self.index_name).points_count
        except ValueError as e:
            logger.warning(f'No collection found, {e}')
            return 0

    async def adelete(self, route_name: str) -> list[str]:
        """Asynchronously delete records from the index by route name.

        :param route_name: The name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted (empty list, as Qdrant does not return IDs).
        :rtype: list[str]
        """
        from qdrant_client import models
        if self.aclient is None:
            logger.warning('Cannot use async delete with an in-memory Qdrant instance; falling back to sync delete.')
            self.delete(route_name)
            return []
        await self.aclient.delete(self.index_name, points_selector=models.Filter(must=[models.FieldCondition(key=SR_ROUTE_PAYLOAD_KEY, match=models.MatchText(text=route_name))]))
        return []

    async def adelete_index(self):
        """Asynchronously delete the index (collection) from Qdrant.

        :return: None
        :rtype: None
        """
        if self.aclient is None:
            logger.warning('Cannot use async delete_index with an in-memory Qdrant instance; falling back to sync delete_index.')
            self.delete_index()
            return
        await self.aclient.delete_collection(self.index_name)

    async def ais_ready(self) -> bool:
        """Checks if the index is ready to be used asynchronously."""
        if self.aclient is None:
            return False
        try:
            return await self.aclient.collection_exists(self.index_name)
        except Exception as e:
            logger.warning(f'Async QdrantIndex readiness check failed: {e}')
            return False

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=DEFAULT_UPLOAD_BATCH_SIZE, **kwargs):
        """Asynchronously add records to the index, including metadata in the payload."""
        self.dimensions = self.dimensions or len(embeddings[0])
        if self.aclient is None:
            logger.warning('Cannot use async add with an in-memory Qdrant instance; falling back to sync add.')
            return self.add(embeddings, routes, utterances, function_schemas, metadata_list, batch_size, **kwargs)
        if not metadata_list or len(metadata_list) != len(utterances):
            metadata_list = [{} for _ in utterances]
        payloads = [{SR_ROUTE_PAYLOAD_KEY: route, SR_UTTERANCE_PAYLOAD_KEY: utterance, 'metadata': metadata if metadata is not None else {}} for route, utterance, metadata in zip(routes, utterances, metadata_list)]
        ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, f'{route}:{utterance}')) for route, utterance in zip(routes, utterances)]
        await self.aclient.upload_collection(self.index_name, vectors=embeddings, payload=payloads, ids=ids, batch_size=batch_size)

    async def aget_utterances(self, include_metadata: bool=False) -> List[Utterance]:
        """Asynchronously gets a list of route and utterance objects currently stored in the index, including metadata."""
        if self.aclient is None:
            logger.warning('Cannot use async get_utterances with an in-memory Qdrant instance; falling back to sync get_utterances.')
            return self.get_utterances(include_metadata=include_metadata)
        from qdrant_client import grpc
        results = []
        next_offset = None
        stop_scrolling = False
        try:
            while not stop_scrolling:
                records, next_offset = await self.aclient.scroll(self.index_name, limit=SCROLL_SIZE, offset=next_offset, with_payload=True)
                stop_scrolling = next_offset is None or (isinstance(next_offset, grpc.PointId) and next_offset.num == 0 and (next_offset.uuid == ''))
                results.extend(records)
            utterances: List[Utterance] = [Utterance(route=x.payload[SR_ROUTE_PAYLOAD_KEY], utterance=x.payload[SR_UTTERANCE_PAYLOAD_KEY], function_schemas=None, metadata=x.payload.get('metadata', {})) for x in results]
        except ValueError as e:
            logger.warning(f'Index likely empty, error: {e}')
            return []
        return utterances

def _initialize_clients(self):
    """Initialize the clients for the Qdrant index.

        :return: A tuple of the sync and async clients.
        :rtype: Tuple[QdrantClient, Optional[AsyncQdrantClient]]
        """
    try:
        from qdrant_client import AsyncQdrantClient, QdrantClient
        sync_client = QdrantClient(location=self.location, url=self.url, port=self.port, grpc_port=self.grpc_port, prefer_grpc=self.prefer_grpc, https=self.https, api_key=self.api_key, prefix=self.prefix, timeout=self.timeout, host=self.host, path=self.path, grpc_options=self.grpc_options)
        async_client: Optional[AsyncQdrantClient] = None
        if all([self.location != ':memory:', self.path is None]):
            async_client = AsyncQdrantClient(location=self.location, url=self.url, port=self.port, grpc_port=self.grpc_port, prefer_grpc=self.prefer_grpc, https=self.https, api_key=self.api_key, prefix=self.prefix, timeout=self.timeout, host=self.host, path=self.path, grpc_options=self.grpc_options)
        return (sync_client, async_client)
    except ImportError as e:
        raise ImportError("Please install 'qdrant-client' to use QdrantIndex.You can install it with: `pip install 'semantic-router[qdrant]'`") from e

class FastEmbedEncoder(DenseEncoder):
    """Dense encoder that uses local FastEmbed to embed documents. Supports text only.
    Requires the fastembed package which can be installed with `pip install 'semantic-router[fastembed]'`

    :param name: The name of the embedding model to use.
    :param max_length: The maximum length of the input text.
    :param cache_dir: The directory to cache the embedding model.
    :param threads: The number of threads to use for the embedding.
    """
    type: str = 'fastembed'
    name: str = 'BAAI/bge-small-en-v1.5'
    max_length: int = 512
    cache_dir: Optional[str] = None
    threads: Optional[int] = None
    _client: Any = PrivateAttr()

    def __init__(self, score_threshold: float=0.5, **data):
        """Initialize the FastEmbed encoder.

        :param score_threshold: The threshold for the score of the embedding.
        :type score_threshold: float
        """
        super().__init__(score_threshold=score_threshold, **data)
        self._client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the FastEmbed library. Requires the fastembed package."""
        try:
            from fastembed import TextEmbedding
        except ImportError:
            raise ImportError("Please install fastembed to use FastEmbedEncoder. You can install it with: `pip install 'semantic-router[fastembed]'`")
        embedding_args = {'model_name': self.name, 'max_length': self.max_length, 'cache_dir': self.cache_dir, 'threads': self.threads}
        embedding_args = {k: v for k, v in embedding_args.items() if v is not None}
        embedding = TextEmbedding(**embedding_args)
        return embedding

    def __call__(self, docs: List[str]) -> List[List[float]]:
        """Embed a list of documents. Supports text only.

        :param docs: The documents to embed.
        :type docs: List[str]
        :raise ValueError: If the embedding fails.
        :return: The vector embeddings of the documents.
        :rtype: List[List[float]]
        """
        try:
            embeds: List[np.ndarray] = list(self._client.embed(docs))
            embeddings: List[List[float]] = [e.tolist() for e in embeds]
            return embeddings
        except Exception as e:
            raise ValueError(f'FastEmbed embed failed. Error: {e}') from e

def _initialize_client(self):
    """Initialize the FastEmbed library. Requires the fastembed package."""
    try:
        from fastembed import TextEmbedding
    except ImportError:
        raise ImportError("Please install fastembed to use FastEmbedEncoder. You can install it with: `pip install 'semantic-router[fastembed]'`")
    embedding_args = {'model_name': self.name, 'max_length': self.max_length, 'cache_dir': self.cache_dir, 'threads': self.threads}
    embedding_args = {k: v for k, v in embedding_args.items() if v is not None}
    embedding = TextEmbedding(**embedding_args)
    return embedding

def test_is_valid_with_valid_json():
    valid_json = '{"name": "test_route", "utterances": ["hello", "hi"]}'
    assert is_valid(valid_json) is True

def test_is_valid_with_missing_keys():
    invalid_json = '{"name": "test_route"}'
    with patch('semantic_router.route.logger') as mock_logger:
        assert is_valid(invalid_json) is False
        mock_logger.warning.assert_called_once()

def test_is_valid_with_valid_json_list():
    valid_json_list = '[{"name": "test_route1", "utterances": ["hello"]}, {"name": "test_route2", "utterances": ["hi"]}]'
    assert is_valid(valid_json_list) is True

def test_is_valid_with_invalid_json_list():
    invalid_json_list = '[{"name": "test_route1"}, {"name": "test_route2", "utterances": ["hi"]}]'
    with patch('semantic_router.route.logger') as mock_logger:
        assert is_valid(invalid_json_list) is False
        mock_logger.warning.assert_called_once()

def test_is_valid_with_invalid_json():
    invalid_json = '{"name": "test_route", "utterances": ["hello", "hi" invalid json}'
    with patch('semantic_router.route.logger') as mock_logger:
        assert is_valid(invalid_json) is False
        mock_logger.error.assert_called_once()

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

class TestBedrockEncoder:

    def test_initialisation_with_default_values(self, bedrock_encoder):
        assert bedrock_encoder.input_type == 'search_query', 'Default input type not set correctly'
        assert bedrock_encoder.region == 'us-west-2', 'Region should be initialised'

    def test_initialisation_with_custom_values(self, mocker):
        name = 'custom_model'
        score_threshold = 0.5
        input_type = 'custom_input'
        bedrock_encoder = BedrockEncoder(name=name, score_threshold=score_threshold, input_type=input_type, access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.name == name, 'Custom name not set correctly'
        assert bedrock_encoder.region == 'us-west-2', 'Custom region not set correctly'
        assert bedrock_encoder.score_threshold == score_threshold, 'Custom score threshold not set correctly'
        assert bedrock_encoder.input_type == input_type, 'Custom input type not set correctly'

    def test_initialisation_with_session_token(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        bedrock_encoder = BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.session_token == 'fake_token', 'Session token not set correctly'

    def test_initialisation_with_missing_access_key(self, mocker):
        mocker.patch.dict(os.environ, {'AWS_ACCESS_KEY_ID': 'env_id'})
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        bedrock_encoder = BedrockEncoder(access_key_id=None, secret_access_key='fake_secret', session_token='fake_token', region='us-west-2')
        assert bedrock_encoder.access_key_id == 'env_id', 'Access key ID not set correctly from environment variable'

    def test_missing_access_key_id(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id=None, secret_access_key='fake_secret')

    def test_missing_secret_access_key(self, mocker):
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client')
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id='fake_id', secret_access_key=None)

    def test_initialisation_missing_env_variables(self, mocker):
        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id=None, secret_access_key=None, session_token=None, region=None)

    def test_failed_client_initialisation(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', side_effect=Exception('Initialization failed'))
        with pytest.raises(ValueError):
            BedrockEncoder(access_key_id='fake_id', secret_access_key='fake_secret')

    def test_call_method(self, bedrock_encoder):
        response_content = json.dumps({'embedding': [0.1, 0.2, 0.3]})
        response_body = BytesIO(response_content.encode('utf-8'))
        mock_response = {'body': response_body}
        bedrock_encoder.client.invoke_model.return_value = mock_response
        result = bedrock_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(item, list) for item in result)), 'Each item in result should be a list'
        assert result == [[0.1, 0.2, 0.3]], 'Embedding should be [0.1, 0.2, 0.3]'

    def test_call_with_expired_token(self, mocker, bedrock_encoder):
        from botocore.exceptions import ClientError
        error_response = {'Error': {'Code': 'ExpiredTokenException'}}
        mocker.patch('semantic_router.encoders.bedrock.BedrockEncoder._initialize_client', return_value=None)

        def invoke_model_side_effect(*args, **kwargs):
            if not invoke_model_side_effect.expired_token_raised:
                invoke_model_side_effect.expired_token_raised = True
                raise ClientError(error_response, 'invoke_model')
            else:
                return {'body': BytesIO(json.dumps({'embedding': [0.1, 0.2, 0.3]}).encode('utf-8'))}
        invoke_model_side_effect.expired_token_raised = False
        bedrock_encoder.client.invoke_model.side_effect = invoke_model_side_effect
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])
        bedrock_encoder._initialize_client.assert_called_once_with(bedrock_encoder.access_key_id, bedrock_encoder.secret_access_key, None, bedrock_encoder.region)

    def test_raises_value_error_if_call_to_bedrock_fails(self, bedrock_encoder):
        bedrock_encoder.client.invoke_model.side_effect = Exception('Bedrock call failed.')
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_call_with_unknown_model_name(self, bedrock_encoder):
        bedrock_encoder.name = 'unknown_model'
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_chunking_functionality(self, bedrock_encoder):
        docs = ['This is a long text that needs to be chunked properly.']
        chunked_docs = bedrock_encoder.chunk_strings(docs, MAX_WORDS=5)
        assert isinstance(chunked_docs, list), 'Chunked result should be a list'
        assert len(chunked_docs[0]) > 1, 'Document should be chunked into multiple parts'
        assert all((isinstance(chunk, str) for chunk in chunked_docs[0])), 'Chunks should be strings'

    def test_get_env_variable(self):
        var_name = 'TEST_ENV_VAR'
        default_value = 'default'
        os.environ[var_name] = 'env_value'
        assert BedrockEncoder.get_env_variable(var_name, None) == 'env_value'
        assert BedrockEncoder.get_env_variable(var_name, None, default_value) == 'env_value'
        assert BedrockEncoder.get_env_variable('NON_EXISTENT_VAR', None, default_value) == default_value

    def test_get_env_variable_missing(self):
        with pytest.raises(ValueError):
            BedrockEncoder.get_env_variable('MISSING_VAR', None)

    def test_uninitialised_client(self, bedrock_encoder):
        bedrock_encoder.client = None
        with pytest.raises(ValueError):
            bedrock_encoder(['test'])

    def test_missing_env_variables(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        with pytest.raises(ValueError):
            BedrockEncoder()

def test_chunking_functionality(self, bedrock_encoder):
    docs = ['This is a long text that needs to be chunked properly.']
    chunked_docs = bedrock_encoder.chunk_strings(docs, MAX_WORDS=5)
    assert isinstance(chunked_docs, list), 'Chunked result should be a list'
    assert len(chunked_docs[0]) > 1, 'Document should be chunked into multiple parts'
    assert all((isinstance(chunk, str) for chunk in chunked_docs[0])), 'Chunks should be strings'

class TestLocalSparseEncoder:

    def test_sparse_local_encoder(self):
        encoder = LocalSparseEncoder(name='naver/splade-cocondenser-ensembledistil')
        test_docs = ['This is a test', 'This is another test']
        embeddings = encoder(test_docs)
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_docs)
        assert all((isinstance(embedding, SparseEmbedding) for embedding in embeddings))

def test_sparse_local_encoder(self):
    encoder = LocalSparseEncoder(name='naver/splade-cocondenser-ensembledistil')
    test_docs = ['This is a test', 'This is another test']
    embeddings = encoder(test_docs)
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(test_docs)
    assert all((isinstance(embedding, SparseEmbedding) for embedding in embeddings))

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

def test_initialization(self, tfidf_encoder):
    assert tfidf_encoder.word_index == {}
    assert (tfidf_encoder.idf == np.array([])).all()

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

class TestGoogleEncoder:

    def test_initialization_with_project_id(self, google_encoder):
        assert google_encoder.client is not None, 'Client should be initialized'
        assert google_encoder.name == 'textembedding-gecko@003', 'Default name not set correctly'

    def test_initialization_without_project_id(self, mocker, monkeypatch):
        monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
        with pytest.raises(ValueError):
            GoogleEncoder()

    def test_call_method(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_returns_list_of_embeddings_for_valid_input(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_handles_multiple_inputs_correctly(self, google_encoder, mocker):
        mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False)), TextEmbedding(values=[0.4, 0.5, 0.6], statistics=TextEmbeddingStatistics(token_count=6, truncated=False))]
        mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
        result = google_encoder(['test1', 'test2'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
        google_encoder.client.get_embeddings.assert_called_once()

    def test_raises_value_error_if_project_id_is_none(self, mocker, monkeypatch):
        monkeypatch.delenv('GOOGLE_PROJECT_ID', raising=False)
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained')
        with pytest.raises(ValueError):
            GoogleEncoder()

    def test_raises_value_error_if_google_client_fails_to_initialize(self, mocker):
        mocker.patch('google.cloud.aiplatform.init', side_effect=Exception('Failed to initialize client'))
        with pytest.raises(ValueError):
            GoogleEncoder(project_id='test_project_id')

    def test_raises_value_error_if_google_client_is_not_initialized(self, mocker):
        mocker.patch('google.cloud.aiplatform.init')
        mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', return_value=None)
        encoder = GoogleEncoder(project_id='test_project_id')
        with pytest.raises(ValueError):
            encoder(['test'])

    def test_call_method_raises_error_on_api_failure(self, google_encoder, mocker):
        mocker.patch.object(google_encoder.client, 'get_embeddings', side_effect=GoogleAPICallError('API call failed'))
        with pytest.raises(ValueError):
            google_encoder(['test'])

def test_call_method(self, google_encoder, mocker):
    mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
    mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
    result = google_encoder(['test'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
    google_encoder.client.get_embeddings.assert_called_once()

def test_returns_list_of_embeddings_for_valid_input(self, google_encoder, mocker):
    mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False))]
    mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
    result = google_encoder(['test'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
    google_encoder.client.get_embeddings.assert_called_once()

def test_handles_multiple_inputs_correctly(self, google_encoder, mocker):
    mock_embeddings = [TextEmbedding(values=[0.1, 0.2, 0.3], statistics=TextEmbeddingStatistics(token_count=5, truncated=False)), TextEmbedding(values=[0.4, 0.5, 0.6], statistics=TextEmbeddingStatistics(token_count=6, truncated=False))]
    mocker.patch.object(google_encoder.client, 'get_embeddings', return_value=mock_embeddings)
    result = google_encoder(['test1', 'test2'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(sublist, list) for sublist in result)), 'Each item in result should be a list'
    google_encoder.client.get_embeddings.assert_called_once()

def test_call_method_raises_error_on_api_failure(self, google_encoder, mocker):
    mocker.patch.object(google_encoder.client, 'get_embeddings', side_effect=GoogleAPICallError('API call failed'))
    with pytest.raises(ValueError):
        google_encoder(['test'])

