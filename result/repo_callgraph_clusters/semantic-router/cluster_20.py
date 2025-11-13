# Cluster 20

class PineconeIndex(BaseIndex):
    index_prefix: str = 'semantic-router--'
    api_key: Optional[str] = None
    index_name: str = 'index'
    dimensions: Union[int, None] = None
    metric: str = 'dotproduct'
    cloud: str = 'aws'
    region: str = 'us-east-1'
    host: str = ''
    client: Any = Field(default=None, exclude=True)
    index: Optional[Any] = Field(default=None, exclude=True)
    ServerlessSpec: Any = Field(default=None, exclude=True)
    namespace: Optional[str] = ''
    base_url: Optional[str] = None
    headers: dict[str, str] = {}
    index_host: Optional[str] = 'http://localhost:5080'
    init_async_index: bool = False

    def __init__(self, api_key: Optional[str]=None, index_name: str='index', dimensions: Optional[int]=None, metric: str='dotproduct', cloud: str='aws', region: str='us-east-1', host: str='', namespace: Optional[str]='', base_url: Optional[str]='https://api.pinecone.io', init_async_index: bool=False):
        """Initialize PineconeIndex.

        :param api_key: Pinecone API key.
        :type api_key: Optional[str]
        :param index_name: Name of the index.
        :type index_name: str
        :param dimensions: Dimensions of the index.
        :type dimensions: Optional[int]
        :param metric: Metric of the index.
        :type metric: str
        :param cloud: Cloud provider of the index.
        :type cloud: str
        :param region: Region of the index.
        :type region: str
        :param host: Host of the index.
        :type host: str
        :param namespace: Namespace of the index.
        :type namespace: Optional[str]
        :param base_url: Base URL of the Pinecone API.
        :type base_url: Optional[str]
        :param init_async_index: Whether to initialize the index asynchronously.
        :type init_async_index: bool
        """
        super().__init__()
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        if not self.api_key:
            raise ValueError('Pinecone API key is required.')
        self.headers = {'Api-Key': self.api_key, 'Content-Type': 'application/json', 'User-Agent': 'source_tag=semanticrouter'}
        if base_url is not None or os.getenv('PINECONE_API_BASE_URL'):
            logger.info('Using pinecone remote API.')
            if os.getenv('PINECONE_API_BASE_URL'):
                self.base_url = os.getenv('PINECONE_API_BASE_URL')
            else:
                self.base_url = base_url
        if self.base_url and 'api.pinecone.io' in self.base_url:
            self.headers['X-Pinecone-API-Version'] = '2024-07'
        self.index_name = index_name
        self.dimensions = dimensions
        self.metric = metric
        self.cloud = cloud
        self.region = region
        self.host = host
        if namespace == 'sr_config':
            raise ValueError("Namespace 'sr_config' is reserved for internal use.")
        self.namespace = namespace
        self.type = 'pinecone'
        logger.warning('Default region changed from us-west-2 to us-east-1 in v0.1.0.dev6')
        self.client = self._initialize_client(api_key=self.api_key)
        if not init_async_index:
            self.index = self._init_index()

    def _initialize_client(self, api_key: Optional[str]=None):
        """Initialize the Pinecone client.

        :param api_key: Pinecone API key.
        :type api_key: Optional[str]
        :return: Pinecone client.
        :rtype: Pinecone
        """
        try:
            from pinecone import Pinecone, ServerlessSpec
            self.ServerlessSpec = ServerlessSpec
        except ImportError:
            raise ImportError("Please install pinecone-client to use PineconeIndex. You can install it with: `pip install 'semantic-router[pinecone]'`")
        pinecone_args = {'api_key': api_key, 'source_tag': 'semanticrouter', 'host': self.base_url}
        if self.namespace:
            pinecone_args['namespace'] = self.namespace
        return Pinecone(**pinecone_args)

    def _calculate_index_host(self):
        """Calculate the index host. Used to differentiate between normal
        Pinecone and Pinecone Local instance.

        :return: None
        :rtype: None
        """
        if self.index_host and self.base_url:
            if 'api.pinecone.io' in self.base_url:
                if not self.index_host.startswith('http'):
                    self.index_host = f'https://{self.index_host}'
            elif 'http' not in self.index_host:
                self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
            elif not self.index_host.startswith('http://'):
                if 'localhost' in self.index_host:
                    self.index_host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.index_host.split(':')[-1]}'
                else:
                    self.index_host = f'http://{self.index_host}'

    def _init_index(self, force_create: bool=False) -> Union[Any, None]:
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        dimensions_given = self.dimensions is not None
        if self.index is None:
            index_exists = self.client.has_index(name=self.index_name)
            if dimensions_given and (not index_exists):
                self.client.create_index(name=self.index_name, dimension=self.dimensions, metric=self.metric, spec=self.ServerlessSpec(cloud=self.cloud, region=self.region))
                while not self.client.describe_index(self.index_name).status['ready']:
                    time.sleep(0.2)
                index = self.client.Index(self.index_name)
                self.index = index
                time.sleep(0.2)
            elif index_exists:
                self.index_host = self.client.describe_index(self.index_name).host
                self._calculate_index_host()
                index = self.client.Index(self.index_name, host=self.index_host)
                self.index = index
                self.dimensions = index.describe_index_stats()['dimension']
            elif force_create and (not dimensions_given):
                raise ValueError('Cannot create an index without specifying the dimensions.')
            else:
                logger.warning(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, self.cloud={self.cloud!r}, self.region={self.region!r}, self.host={self.host!r}, self.namespace={self.namespace!r}, force_create={force_create!r}')
                index = None
        else:
            index = self.index
        if self.index is not None and self.host == '':
            self.index_host = self.client.describe_index(self.index_name).host
            if self.index_host and self.base_url:
                self._calculate_index_host()
                index = self.client.Index(self.index_name, host=self.index_host)
                self.host = self.index_host
        return index

    async def _init_async_index(self, force_create: bool=False):
        """Initializing the index can be done after the object has been created
        to allow for the user to set the dimensions and other parameters.

        If the index doesn't exist and the dimensions are given, the index will
        be created. If the index exists, it will be returned. If the index doesn't
        exist and the dimensions are not given, the index will not be created and
        None will be returned.

        This method is used to initialize the index asynchronously.

        :param force_create: If True, the index will be created even if the
            dimensions are not given (which will raise an error).
        :type force_create: bool, optional
        """
        index_stats = None
        if self.dimensions is None:
            indexes = await self._async_list_indexes()
            index_names = [i['name'] for i in indexes['indexes']]
            index_exists = self.index_name in index_names
            if index_exists:
                index_stats = await self._async_describe_index(self.index_name)
                self.dimensions = index_stats['dimension']
            elif index_exists and (not force_create):
                logger.warning(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, self.cloud={self.cloud!r}, self.region={self.region!r}, self.host={self.host!r}, self.namespace={self.namespace!r}, force_create={force_create!r}')
            elif force_create:
                raise ValueError(f'Index could not be initialized. Init parameters: self.index_name={self.index_name!r}, self.dimensions={self.dimensions!r}, self.metric={self.metric!r}, ')
            else:
                raise NotImplementedError('Unexpected init conditions. Please report this issue in GitHub.')
        if self.dimensions:
            indexes = await self._async_list_indexes()
            index_names = [i['name'] for i in indexes['indexes']]
            index_exists = self.index_name in index_names
            if not index_exists:
                index_stats = await self._async_describe_index(self.index_name)
                index_status = index_stats.get('status', {})
                index_ready = index_status.get('ready', False) if isinstance(index_status, dict) else False
                if index_ready == 'true' or (isinstance(index_ready, bool) and index_ready):
                    self.index_host = index_stats['host']
                    self._calculate_index_host()
                    self.host = self.index_host
                    return index_stats
                else:
                    await self._async_create_index(name=self.index_name, dimension=self.dimensions, metric=self.metric, cloud=self.cloud, region=self.region)
                    index_ready = 'false'
                    while not (index_ready == 'true' or (isinstance(index_ready, bool) and index_ready)):
                        index_stats = await self._async_describe_index(self.index_name)
                        index_status = index_stats.get('status', {})
                        index_ready = index_status.get('ready', False) if isinstance(index_status, dict) else False
                        await asyncio.sleep(0.1)
                    self.index_host = index_stats['host']
                    self._calculate_index_host()
                    self.host = self.index_host
                    return index_stats
            else:
                index_stats = await self._async_describe_index(self.index_name)
                self.index_host = index_stats['host']
                self._calculate_index_host()
                self.host = self.index_host
                return index_stats
        if index_stats:
            self.index_host = index_stats['host']
            self._calculate_index_host()
            self.host = self.index_host
        else:
            self.host = ''

    def _batch_upsert(self, batch: List[Dict]):
        """Helper method for upserting a single batch of records.

        :param batch: The batch of records to upsert.
        :type batch: List[Dict]
        """
        if self.index is not None:
            self.index.upsert(vectors=batch, namespace=self.namespace)
        else:
            raise ValueError('Index is None, could not upsert.')

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[Optional[List[Dict[str, Any]]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=100, sparse_embeddings: Optional[Optional[List[SparseEmbedding]]]=None, **kwargs):
        """Add vectors to Pinecone in batches.

        :param embeddings: List of embeddings to upsert.
        :type embeddings: List[List[float]]
        :param routes: List of routes to upsert.
        :type routes: List[str]
        :param utterances: List of utterances to upsert.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to upsert.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to upsert.
        :type metadata_list: List[Dict[str, Any]]
        :param batch_size: Number of vectors to upsert in a single batch.
        :type batch_size: int, optional
        :param sparse_embeddings: List of sparse embeddings to upsert.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        if self.index is None:
            self.dimensions = self.dimensions or len(embeddings[0])
            self.index = self._init_index(force_create=True)
        vectors_to_upsert = build_records(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            self._batch_upsert(batch)

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[Optional[List[Dict[str, Any]]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=100, sparse_embeddings: Optional[Optional[List[SparseEmbedding]]]=None, **kwargs):
        """Add vectors to Pinecone in batches.

        :param embeddings: List of embeddings to upsert.
        :type embeddings: List[List[float]]
        :param routes: List of routes to upsert.
        :type routes: List[str]
        :param utterances: List of utterances to upsert.
        :type utterances: List[str]
        :param function_schemas: List of function schemas to upsert.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: List of metadata to upsert.
        :type metadata_list: List[Dict[str, Any]]
        :param batch_size: Number of vectors to upsert in a single batch.
        :type batch_size: int, optional
        :param sparse_embeddings: List of sparse embeddings to upsert.
        :type sparse_embeddings: Optional[List[SparseEmbedding]]
        """
        vectors_to_upsert = build_records(embeddings=embeddings, routes=routes, utterances=utterances, function_schemas=function_schemas, metadata_list=metadata_list, sparse_embeddings=sparse_embeddings)
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            await self._async_upsert(vectors=batch, namespace=self.namespace or '')

    def _remove_and_sync(self, routes_to_delete: dict):
        """Remove specified routes from index if they exist.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        """
        for route, utterances in routes_to_delete.items():
            remote_routes = self._get_routes_with_ids(route_name=route)
            ids_to_delete = [r['id'] for r in remote_routes if (r['route'], r['utterance']) in zip([route] * len(utterances), utterances)]
            if ids_to_delete and self.index:
                self.index.delete(ids=ids_to_delete, namespace=self.namespace)

    async def _async_remove_and_sync(self, routes_to_delete: dict):
        """Remove specified routes from index if they exist.

        This method is asyncronous.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        """
        for route, utterances in routes_to_delete.items():
            remote_routes = await self._async_get_routes_with_ids(route_name=route)
            ids_to_delete = [r['id'] for r in remote_routes if (r['route'], r['utterance']) in zip([route] * len(utterances), utterances)]
            if ids_to_delete and self.index:
                await self._async_delete(ids=ids_to_delete, namespace=self.namespace or '')

    def _get_route_ids(self, route_name: str):
        """Get the IDs of the routes in the index.

        :param route_name: Name of the route to get the IDs for.
        :type route_name: str
        :return: List of IDs of the routes.
        :rtype: list[str]
        """
        clean_route = clean_route_name(route_name)
        ids, _ = self._get_all(prefix=f'{clean_route}#')
        return ids

    async def _async_get_route_ids(self, route_name: str):
        """Get the IDs of the routes in the index.

        :param route_name: Name of the route to get the IDs for.
        :type route_name: str
        :return: List of IDs of the routes.
        :rtype: list[str]
        """
        clean_route = clean_route_name(route_name)
        ids, _ = await self._async_get_all(prefix=f'{clean_route}#')
        return ids

    def _get_routes_with_ids(self, route_name: str):
        """Get the routes with their IDs from the index.

        :param route_name: Name of the route to get the routes with their IDs for.
        :type route_name: str
        :return: List of routes with their IDs.
        :rtype: list[dict]
        """
        clean_route = clean_route_name(route_name)
        ids, metadata = self._get_all(prefix=f'{clean_route}#', include_metadata=True)
        route_tuples = []
        for id, data in zip(ids, metadata):
            route_tuples.append({'id': id, 'route': data['sr_route'], 'utterance': data['sr_utterance']})
        return route_tuples

    async def _async_get_routes_with_ids(self, route_name: str):
        """Get the routes with their IDs from the index.

        :param route_name: Name of the route to get the routes with their IDs for.
        :type route_name: str
        :return: List of routes with their IDs.
        :rtype: list[dict]
        """
        clean_route = clean_route_name(route_name)
        ids, metadata = await self._async_get_all(prefix=f'{clean_route}#', include_metadata=True)
        route_tuples = []
        for id, data in zip(ids, metadata):
            route_tuples.append({'id': id, 'route': data['sr_route'], 'utterance': data['sr_utterance']})
        return route_tuples

    def _get_all(self, prefix: Optional[str]=None, include_metadata: bool=False):
        """Retrieves all vector IDs from the Pinecone index using pagination.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        if self.index is None:
            raise ValueError('Index is None, could not retrieve vector IDs.')
        all_vector_ids = []
        metadata = []
        for ids in self.index.list(prefix=prefix, namespace=self.namespace):
            all_vector_ids.extend(ids)
            if include_metadata:
                for id in ids:
                    res_meta = self.index.fetch(ids=[id], namespace=self.namespace) if self.index else {}
                    metadata.extend([x['metadata'] for x in res_meta['vectors'].values()])
        return (all_vector_ids, metadata)

    def delete(self, route_name: str) -> list[str]:
        """Delete specified route from index if it exists. Returns the IDs of the vectors
        deleted.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        route_vec_ids = self._get_route_ids(route_name=route_name)
        if self.index is not None:
            logger.info('index is not None, deleting...')
            if self.base_url and 'api.pinecone.io' in self.base_url:
                self.index.delete(ids=route_vec_ids, namespace=self.namespace)
            else:
                response = requests.post(f'{self.index_host}/vectors/delete', json=DeleteRequest(ids=route_vec_ids, delete_all=True, namespace=self.namespace).model_dump(exclude_none=True), timeout=10)
                if response.status_code == 200:
                    logger.info(f'Deleted {len(route_vec_ids)} vectors from index {self.index_name}.')
                else:
                    error_message = response.text
                    raise Exception(f'Failed to delete vectors: {response.status_code} : {error_message}')
            return route_vec_ids
        else:
            raise ValueError('Index is None, could not delete.')

    async def adelete(self, route_name: str) -> list[str]:
        """Asynchronously delete specified route from index if it exists. Returns the IDs
        of the vectors deleted.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        route_vec_ids = await self._async_get_route_ids(route_name=route_name)
        await self._async_delete(ids=route_vec_ids, namespace=self.namespace or '')
        return route_vec_ids

    def delete_all(self):
        """Delete all routes from index if it exists.

        :return: None
        :rtype: None
        """
        if self.index is not None:
            self.index.delete(delete_all=True, namespace=self.namespace)
        else:
            raise ValueError('Index is None, could not delete.')

    def describe(self) -> IndexConfig:
        """Describe the index.

        :return: IndexConfig
        :rtype: IndexConfig
        """
        if self.index is not None:
            stats = self.index.describe_index_stats()
            return IndexConfig(type=self.type, dimensions=stats['dimension'], vectors=stats['namespaces'][self.namespace]['vector_count'])
        else:
            return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=0)

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return self.index is not None

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Search the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: An optional sparse vector to include in the query.
        :type sparse_vector: Optional[SparseEmbedding]
        :param kwargs: Additional keyword arguments for the query, including sparse_vector.
        :type kwargs: Any
        :return: A tuple containing an array of scores and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises ValueError: If the index is not populated.
        """
        if self.index is None:
            raise ValueError('Index is not populated.')
        query_vector_list = vector.tolist()
        if route_filter is not None:
            filter_query = {'sr_route': {'$in': route_filter}}
        else:
            filter_query = None
        if sparse_vector is not None:
            logger.error(f'sparse_vector exists:{sparse_vector}')
            if isinstance(sparse_vector, dict):
                sparse_vector = SparseEmbedding.from_dict(sparse_vector)
            if isinstance(sparse_vector, SparseEmbedding):
                sparse_vector = sparse_vector.to_pinecone()
        try:
            results = self.index.query(vector=[query_vector_list], sparse_vector=sparse_vector, top_k=top_k, filter=filter_query, include_metadata=True, namespace=self.namespace)
        except Exception:
            logger.error('retrying query with vector as str')
            results = self.index.query(vector=query_vector_list, sparse_vector=sparse_vector, top_k=top_k, filter=filter_query, include_metadata=True, namespace=self.namespace)
        scores = [result['score'] for result in results['matches']]
        route_names = [result['metadata']['sr_route'] for result in results['matches']]
        return (np.array(scores), route_names)

    def _read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        scope = scope or self.namespace
        if self.index is None:
            return ConfigParameter(field=field, value='', scope=scope)
        config_id = f'{field}#{scope}'
        config_record = self.index.fetch(ids=[config_id], namespace='sr_config')
        if config_record.get('vectors'):
            return ConfigParameter(field=field, value=config_record['vectors'][config_id]['metadata']['value'], created_at=config_record['vectors'][config_id]['metadata']['created_at'], scope=scope)
        else:
            logger.warning(f'Configuration for {field} parameter not found in index.')
            return ConfigParameter(field=field, value='', scope=scope)

    async def _async_read_config(self, field: str, scope: str | None=None) -> ConfigParameter:
        """Read a config parameter from the index asynchronously.

        :param field: The field to read.
        :type field: str
        :param scope: The scope to read.
        :type scope: str | None
        :return: The config parameter that was read.
        :rtype: ConfigParameter
        """
        scope = scope or self.namespace
        if self.index is None:
            return ConfigParameter(field=field, value='', scope=scope)
        config_id = f'{field}#{scope}'
        config_record = await self._async_fetch_metadata(vector_id=config_id, namespace='sr_config')
        if config_record:
            try:
                return ConfigParameter(field=field, value=config_record['value'], created_at=config_record['created_at'], scope=scope)
            except KeyError:
                raise ValueError(f'Found invalid config record during sync: {config_record}')
        else:
            logger.warning(f'Configuration for {field} parameter not found in index.')
            return ConfigParameter(field=field, value='', scope=scope)

    def _write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Method to write a config parameter to the remote Pinecone index.

        :param config: The config parameter to write to the index.
        :type config: ConfigParameter
        """
        config.scope = config.scope or self.namespace
        if self.index is None:
            raise ValueError('Index has not been initialized.')
        if self.dimensions is None:
            raise ValueError('Must set PineconeIndex.dimensions before writing config.')
        self.index.upsert(vectors=[config.to_pinecone(dimensions=self.dimensions)], namespace='sr_config')
        return config

    async def _async_write_config(self, config: ConfigParameter) -> ConfigParameter:
        """Method to write a config parameter to the remote Pinecone index.

        :param config: The config parameter to write to the index.
        :type config: ConfigParameter
        """
        config.scope = config.scope or self.namespace
        if self.dimensions is None:
            raise ValueError('Must set PineconeIndex.dimensions before writing config.')
        pinecone_config = config.to_pinecone(dimensions=self.dimensions)
        await self._async_upsert(vectors=[pinecone_config], namespace='sr_config')
        return config

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Asynchronously search the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param kwargs: Additional keyword arguments for the query, including sparse_vector.
        :type kwargs: Any
        :keyword sparse_vector: An optional sparse vector to include in the query.
        :type sparse_vector: Optional[dict]
        :return: A tuple containing an array of scores and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises ValueError: If the index is not populated.
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        query_vector_list = vector.tolist()
        if route_filter is not None:
            filter_query = {'sr_route': {'$in': route_filter}}
        else:
            filter_query = None
        sparse_vector_obj: dict[str, Any] | None = None
        if sparse_vector is not None:
            if isinstance(sparse_vector, dict):
                sparse_vector_obj = SparseEmbedding.from_dict(sparse_vector)
            if isinstance(sparse_vector, SparseEmbedding):
                sparse_vector_obj = sparse_vector.to_pinecone()
        results = await self._async_query(vector=query_vector_list, sparse_vector=sparse_vector_obj, namespace=self.namespace or '', filter=filter_query, top_k=top_k, include_metadata=True)
        scores = [result['score'] for result in results['matches']]
        route_names = [result['metadata']['sr_route'] for result in results['matches']]
        return (np.array(scores), route_names)

    async def aget_routes(self) -> list[tuple]:
        """Asynchronously get a list of route and utterance objects currently
        stored in the index.

        :return: A list of (route_name, utterance) objects.
        :rtype: List[Tuple]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        return await self._async_get_routes()

    def delete_index(self):
        """Delete the index.

        :return: None
        :rtype: None
        """
        self.client.delete_index(self.index_name)
        self.index = None

    async def adelete_index(self):
        """Asynchronously delete the index."""
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        if not self.base_url:
            raise ValueError('base_url is not set for PineconeIndex.')
        async with aiohttp.ClientSession() as session:
            async with session.delete(f'{self.base_url}/indexes/{self.index_name}', headers=self.headers) as response:
                res = await response.json(content_type=None)
                if response.status != 202:
                    raise Exception(f'Failed to delete index: {response.status}', res)
        self.host = ''
        return res

    async def _async_query(self, vector: list[float], sparse_vector: dict[str, Any] | None=None, namespace: str='', filter: Optional[dict]=None, top_k: int=5, include_metadata: bool=False):
        """Asynchronously query the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: list[float]
        :param sparse_vector: The sparse vector to search for.
        :type sparse_vector: dict[str, Any] | None
        :param namespace: The namespace to search for.
        :type namespace: str
        :param filter: The filter to search for.
        :type filter: Optional[dict]
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param include_metadata: Whether to include metadata in the results, defaults to False.
        :type include_metadata: bool, optional
        """
        params = {'vector': vector, 'sparse_vector': sparse_vector, 'namespace': namespace, 'filter': filter, 'top_k': top_k, 'include_metadata': include_metadata, 'topK': top_k, 'includeMetadata': include_metadata}
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        elif self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/query', json=params, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f'Error in query response: {error_text}')
                    return {}
                try:
                    return await response.json(content_type=None)
                except JSONDecodeError as e:
                    logger.error(f'JSON decode error: {e}')
                    return {}

    async def ais_ready(self, client_only: bool=False) -> bool:
        """Checks if class attributes exist to be used for async operations.

        :param client_only: Whether to check only the client attributes. If False
            attributes will be checked for both client and index operations. If True
            only attributes for client operations will be checked. Defaults to False.
        :type client_only: bool, optional
        :return: True if the class attributes exist, False otherwise.
        :rtype: bool
        """
        if not (self.cloud or self.region or self.base_url):
            return False
        if not client_only:
            if not (self.index_name and self.dimensions and self.metric and self.host and (self.host != '')):
                await self._init_async_index()
                if not (self.index_name and self.dimensions and self.metric and self.host and (self.host != '')):
                    return False
        return True

    async def _async_list_indexes(self):
        """Asynchronously lists all indexes within the current Pinecone project.

        :return: List of indexes.
        :rtype: list[dict]
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.base_url}/indexes', headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_upsert(self, vectors: list[dict], namespace: str=''):
        """Asynchronously upserts vectors into the index.

        :param vectors: The vectors to upsert.
        :type vectors: list[dict]
        :param namespace: The namespace to upsert the vectors into.
        :type namespace: str
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        params = {'vectors': vectors, 'namespace': namespace}
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/vectors/upsert', json=params, headers=self.headers) as response:
                res = await response.json(content_type=None)
                return res

    async def _async_create_index(self, name: str, dimension: int, cloud: str, region: str, metric: str='dotproduct'):
        """Asynchronously creates a new index in Pinecone.

        :param name: The name of the index to create.
        :type name: str
        :param dimension: The dimension of the index.
        :type dimension: int
        :param cloud: The cloud provider to create the index on.
        :type cloud: str
        :param region: The region to create the index in.
        :type region: str
        :param metric: The metric to use for the index, defaults to "dotproduct".
        :type metric: str, optional
        """
        params = {'name': name, 'dimension': dimension, 'metric': metric, 'spec': {'serverless': {'cloud': cloud, 'region': region}}, 'deletion_protection': 'disabled'}
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.base_url}/indexes', json=params, headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_delete(self, ids: list[str], namespace: str=''):
        """Asynchronously deletes vectors from the index.

        :param ids: The IDs of the vectors to delete.
        :type ids: list[str]
        :param namespace: The namespace to delete the vectors from.
        :type namespace: str
        """
        params = {'ids': ids, 'namespace': namespace}
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{self.host}/vectors/delete', json=params, headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_describe_index(self, name: str):
        """Asynchronously describes the index.

        :param name: The name of the index to describe.
        :type name: str
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.base_url}/indexes/{name}', headers=self.headers) as response:
                return await response.json(content_type=None)

    async def _async_get_all(self, prefix: Optional[str]=None, include_metadata: bool=False) -> tuple[list[str], list[dict]]:
        """Retrieves all vector IDs from the Pinecone index using pagination
        asynchronously.

        :param prefix: The prefix to filter the vectors by.
        :type prefix: Optional[str]
        :param include_metadata: Whether to include metadata in the response.
        :type include_metadata: bool
        :return: A tuple containing a list of vector IDs and a list of metadata dictionaries.
        :rtype: tuple[list[str], list[dict]]
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        all_vector_ids = []
        next_page_token = None
        if prefix:
            prefix_str = f'?prefix={prefix}'
        else:
            prefix_str = ''
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        list_url = f'{self.host}/vectors/list{prefix_str}'
        params: dict = {}
        if self.namespace:
            params['namespace'] = self.namespace
        metadata = []
        async with aiohttp.ClientSession() as session:
            while True:
                if next_page_token:
                    params['paginationToken'] = next_page_token
                async with session.get(list_url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f'Error fetching vectors: {error_text}')
                        break
                    response_data = await response.json(content_type=None)
                vector_ids = [vec['id'] for vec in response_data.get('vectors', [])]
                if not vector_ids:
                    break
                all_vector_ids.extend(vector_ids)
                if include_metadata:
                    metadata_tasks = [self._async_fetch_metadata(id) for id in vector_ids]
                    metadata_results = await asyncio.gather(*metadata_tasks)
                    metadata.extend(metadata_results)
                next_page_token = response_data.get('pagination', {}).get('next')
                if not next_page_token:
                    break
        return (all_vector_ids, metadata)

    async def _async_fetch_metadata(self, vector_id: str, namespace: str | None=None) -> dict:
        """Fetch metadata for a single vector ID asynchronously using the
        ClientSession.

        :param vector_id: The ID of the vector to fetch metadata for.
        :type vector_id: str
        :param namespace: The namespace to fetch metadata for.
        :type namespace: str | None
        :return: A dictionary containing the metadata for the vector.
        :rtype: dict
        """
        if not await self.ais_ready():
            raise ValueError('Async index is not initialized.')
        if self.base_url and 'api.pinecone.io' in self.base_url:
            if not self.host.startswith('http'):
                logger.error(f'host exists:{self.host}')
                self.host = f'https://{self.host}'
        elif self.host.startswith('localhost') and self.base_url:
            self.host = f'http://{self.base_url.split(':')[-2].strip('/')}:{self.host.split(':')[-1]}'
        url = f'{self.host}/vectors/fetch'
        params = {'ids': [vector_id]}
        if namespace:
            params['namespace'] = [namespace]
        elif self.namespace:
            params['namespace'] = [self.namespace]
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f'Error fetching metadata: {error_text}')
                    return {}
                try:
                    response_data = await response.json(content_type=None)
                except Exception as e:
                    logger.warning(f'No metadata found for vector {vector_id}: {e}')
                    return {}
                return response_data.get('vectors', {}).get(vector_id, {}).get('metadata', {})

    def __len__(self):
        """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        if self.index is None:
            logger.warning('Index is not initialized, returning 0')
            return 0
        namespace_stats = self.index.describe_index_stats()['namespaces'].get(self.namespace)
        if namespace_stats:
            return namespace_stats['vector_count']
        else:
            return 0

    async def alen(self):
        """Async version of __len__. Returns the total number of vectors in the index.
        If the index is not initialized, initializes it first or returns 0.

        :return: The total number of vectors.
        :rtype: int
        """
        if not await self.ais_ready():
            logger.warning('Index is not ready, returning 0')
            return 0
        namespace_stats = await self._async_describe_index_stats()
        if namespace_stats and 'namespaces' in namespace_stats:
            ns_stats = namespace_stats['namespaces'].get(self.namespace)
            if ns_stats:
                return ns_stats['vectorCount']
        return 0

    async def _async_describe_index_stats(self):
        """Async version of describe_index_stats.

        :return: Index statistics.
        :rtype: dict
        """
        url = f'{self.index_host}/describe_index_stats'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json={'namespace': self.namespace}, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                return await response.json()

def _remove_and_sync(self, routes_to_delete: dict):
    """Remove specified routes from index if they exist.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        """
    for route, utterances in routes_to_delete.items():
        remote_routes = self._get_routes_with_ids(route_name=route)
        ids_to_delete = [r['id'] for r in remote_routes if (r['route'], r['utterance']) in zip([route] * len(utterances), utterances)]
        if ids_to_delete and self.index:
            self.index.delete(ids=ids_to_delete, namespace=self.namespace)

def delete_all(self):
    """Delete all routes from index if it exists.

        :return: None
        :rtype: None
        """
    if self.index is not None:
        self.index.delete(delete_all=True, namespace=self.namespace)
    else:
        raise ValueError('Index is None, could not delete.')

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

def delete(self, route_name: str):
    """Delete records from the index.

        :param route_name: The name of the route to delete.
        :type route_name: str
        """
    from qdrant_client import models
    self.client.delete(self.index_name, points_selector=models.Filter(must=[models.FieldCondition(key=SR_ROUTE_PAYLOAD_KEY, match=models.MatchText(text=route_name))]))

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

@pytest.mark.parametrize('index_cls,encoder_cls,router_cls', [(index, encoder, router) for index in get_test_indexes() for encoder in [OpenAIEncoder] for router in get_test_routers()])
class TestSemanticRouter:

    def test_initialization_dynamic_route(self, dynamic_routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=dynamic_routes, index=index, auto_sync='local')
        score_threshold = route_layer.score_threshold
        if isinstance(route_layer, HybridRouter):
            assert score_threshold == encoder.score_threshold * route_layer.alpha
        else:
            assert score_threshold == encoder.score_threshold

    def test_add_single_utterance(self, routes, route_single_utterance, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.add(routes=route_single_utterance)
        score_threshold = route_layer.score_threshold
        if isinstance(route_layer, HybridRouter):
            assert score_threshold == encoder.score_threshold * route_layer.alpha
        else:
            assert score_threshold == encoder.score_threshold

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated():
            _ = route_layer('Hello')
            assert len(route_layer.index.get_utterances()) == 6
        check_index_populated()

    def test_init_and_add_single_utterance(self, route_single_utterance, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, index=index, auto_sync='local')
        if index_cls is PineconeIndex:
            time.sleep(PINECONE_SLEEP)
        route_layer.add(routes=route_single_utterance)
        score_threshold = route_layer.score_threshold
        if isinstance(route_layer, HybridRouter):
            assert score_threshold == encoder.score_threshold * route_layer.alpha
        else:
            assert score_threshold == encoder.score_threshold

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated():
            _ = route_layer('Hello')
            assert len(route_layer.index.get_utterances()) == 1
        check_index_populated()

    def test_delete_index(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def delete_index():
            route_layer.index.delete_index()
            assert route_layer.index.get_utterances() == []
        delete_index()

    def test_add_route(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=[], index=index, auto_sync='local')
        assert route_layer.routes == []

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_empty():
            assert route_layer.index.get_utterances() == []
        check_index_empty()
        route_layer.add(routes=routes[0])

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated1():
            assert route_layer.routes == [routes[0]]
            assert route_layer.index is not None
            assert len(route_layer.index.get_utterances()) == 2
        check_index_populated1()
        route_layer.add(routes=routes[1])

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated2():
            assert route_layer.routes == [routes[0], routes[1]]
            assert len(route_layer.index.get_utterances()) == 5
        check_index_populated2()

    def test_list_route_names(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_route_names():
            route_names = route_layer.list_route_names()
            assert set(route_names) == {route.name for route in routes}, 'The list of route names should match the names of the routes added.'
        check_route_names()

    def test_delete_route(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def delete_route_by_name():
            route_to_delete = routes[0].name
            route_layer.delete(route_to_delete)
            assert route_to_delete not in route_layer.list_route_names(), 'The route should be deleted from the route layer.'
            for utterance in routes[0].utterances:
                assert utterance not in route_layer.index, "The route's utterances should be deleted from the index."
        delete_route_by_name()

    def test_remove_route_not_found(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def delete_non_existent_route():
            non_existent_route = 'non-existent-route'
            route_layer.delete(non_existent_route)
        delete_non_existent_route()

    def test_add_multiple_routes(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated():
            route_layer.add(routes=routes)
            assert route_layer.index is not None
            assert len(route_layer.index.get_utterances()) == 5
        check_index_populated()

    def test_query_and_classification(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        encoder.score_threshold = 0.1
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local', aggregation='max')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_query_result():
            query_result = route_layer(text='Hello').name
            assert query_result in ['Route 1', 'Route 2']
        check_query_result()

    def test_query_filter(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        encoder.score_threshold = 0.1
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local', aggregation='max')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_raises_value_error():
            try:
                route_layer(text='Hello', route_filter=['Route 8']).name
            except ValueError:
                assert True
        check_raises_value_error()

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_query_result():
            query_result = route_layer(text='Hello', route_filter=['Route 1']).name
            assert query_result in ['Route 1']
        check_query_result()

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_namespace_pinecone_index(self, routes, index_cls, encoder_cls, router_cls):
        if index_cls is PineconeIndex:
            encoder = encoder_cls()
            encoder.score_threshold = 0.2
            index = init_index(index_cls, namespace='test', index_name=encoder.__class__.__name__)
            route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
            time.sleep(PINECONE_SLEEP)

            @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
            def check_query_result():
                query_result = route_layer(text='Hello', route_filter=['Route 1']).name
                assert query_result in ['Route 1']
            check_query_result()

            @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
            def delete_namespace():
                route_layer.index.index.delete(namespace='test', delete_all=True)
            delete_namespace()

    def test_query_with_no_index(self, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        route_layer = router_cls(encoder=encoder)
        with pytest.raises(ValueError):
            assert route_layer(text='Anything').name is None

    def test_query_with_vector(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        encoder.score_threshold = 0.1
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local', aggregation='max')
        vector = encoder(['hello'])
        if router_cls is HybridRouter:
            sparse_vector = route_layer.sparse_encoder(['hello'])[0]

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_query_result():
            if router_cls is HybridRouter:
                query_result = route_layer(vector=vector, sparse_vector=sparse_vector).name
            else:
                query_result = route_layer(vector=vector).name
            assert query_result in ['Route 1', 'Route 2']
        check_query_result()

    def test_query_with_no_text_or_vector(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        with pytest.raises(ValueError):
            route_layer()

    def test_is_ready(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_is_ready():
            assert route_layer.index.is_ready()
        check_is_ready()

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def delete_non_existent_route():
    non_existent_route = 'non-existent-route'
    route_layer.delete(non_existent_route)

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def delete_namespace():
    route_layer.index.index.delete(namespace='test', delete_all=True)

