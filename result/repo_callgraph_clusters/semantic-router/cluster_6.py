# Cluster 6

class Utterance(BaseModel):
    """An utterance in a conversation, includes the route, utterance, function
    schemas, metadata, and diff tag.
    """
    route: str
    utterance: Union[str, Any]
    function_schemas: Optional[List[Dict]] = None
    metadata: dict = {}
    diff_tag: str = ' '

    @classmethod
    def from_tuple(cls, tuple_obj: Tuple):
        """Create an Utterance object from a tuple. The tuple must contain
        route and utterance as the first two elements. Then optionally
        function schemas and metadata as the third and fourth elements
        respectively. If this order is not followed an invalid Utterance
        object will be returned.

        :param tuple_obj: A tuple containing route, utterance, function schemas and metadata.
        :type tuple_obj: Tuple
        :return: An Utterance object.
        :rtype: Utterance
        """
        route, utterance = (tuple_obj[0], tuple_obj[1])
        function_schemas = tuple_obj[2] if len(tuple_obj) > 2 else None
        if isinstance(function_schemas, dict):
            function_schemas = [function_schemas]
        metadata = tuple_obj[3] if len(tuple_obj) > 3 else {}
        return cls(route=route, utterance=utterance, function_schemas=function_schemas, metadata=metadata)

    def to_tuple(self):
        """Convert an Utterance object to a tuple.

        :return: A tuple containing (route, utterance, function schemas, metadata).
        :rtype: Tuple
        """
        return (self.route, self.utterance, self.function_schemas, self.metadata)

    def to_str(self, include_metadata: bool=False):
        """Convert an Utterance object to a string. Used for comparisons during sync
        check operations.

        :param include_metadata: Whether to include metadata in the string.
        :type include_metadata: bool
        :return: A string representation of the Utterance object.
        :rtype: str
        """
        if include_metadata:
            if self.function_schemas is not None:
                function_schemas_sorted: List[str] | None = [json.dumps(schema, sort_keys=True) for schema in self.function_schemas]
            else:
                function_schemas_sorted = None
            metadata_sorted = json.dumps(self.metadata, sort_keys=True)
            return f'{self.route}: {self.utterance} | {function_schemas_sorted} | {metadata_sorted}'
        return f'{self.route}: {self.utterance}'

    def to_diff_str(self, include_metadata: bool=False):
        return f'{self.diff_tag} {self.to_str(include_metadata=include_metadata)}'

def to_diff_str(self, include_metadata: bool=False):
    return f'{self.diff_tag} {self.to_str(include_metadata=include_metadata)}'

class UtteranceDiff(BaseModel):
    """A list of Utterance objects that represent the differences between local and
    remote utterances.
    """
    diff: List[Utterance]

    @classmethod
    def from_utterances(cls, local_utterances: List[Utterance], remote_utterances: List[Utterance]):
        """Create a UtteranceDiff object from two lists of Utterance objects.

        :param local_utterances: A list of Utterance objects.
        :type local_utterances: List[Utterance]
        :param remote_utterances: A list of Utterance objects.
        :type remote_utterances: List[Utterance]
        """
        local_utterances_map = {x.to_str(include_metadata=True): x for x in local_utterances}
        remote_utterances_map = {x.to_str(include_metadata=True): x for x in remote_utterances}
        local_utterances_str = list(local_utterances_map.keys())
        local_utterances_str.sort()
        remote_utterances_str = list(remote_utterances_map.keys())
        remote_utterances_str.sort()
        differ = Differ()
        diff_obj = list(differ.compare(local_utterances_str, remote_utterances_str))
        utterance_diffs = []
        for line in diff_obj:
            utterance_str = line[2:]
            utterance_diff_tag = line[0]
            if utterance_diff_tag == '?':
                continue
            utterance = remote_utterances_map[utterance_str] if utterance_diff_tag == '+' else local_utterances_map[utterance_str]
            utterance.diff_tag = utterance_diff_tag
            utterance_diffs.append(utterance)
        return UtteranceDiff(diff=utterance_diffs)

    def to_utterance_str(self, include_metadata: bool=False) -> List[str]:
        """Outputs the utterance diff as a list of diff strings. Returns a list
        of strings showing what is different in the remote when compared to the
        local. For example:

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

        :param include_metadata: Whether to include metadata in the string.
        :type include_metadata: bool
        :return: A list of diff strings.
        :rtype: List[str]
        """
        return [x.to_diff_str(include_metadata=include_metadata) for x in self.diff]

    def get_tag(self, diff_tag: str) -> List[Utterance]:
        """Get all utterances with a given diff tag.

        :param diff_tag: The diff tag to filter by. Must be one of "+", "-", or " ".
        :type diff_tag: str
        :return: A list of Utterance objects.
        :rtype: List[Utterance]
        """
        if diff_tag not in ['+', '-', ' ']:
            raise ValueError("diff_tag must be one of '+', '-', or ' '")
        return [x for x in self.diff if x.diff_tag == diff_tag]

    def get_sync_strategy(self, sync_mode: str) -> dict:
        """Generates the optimal synchronization plan for local and remote instances.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :return: A dictionary describing the synchronization strategy.
        :rtype: dict
        """
        if sync_mode not in SYNC_MODES:
            raise ValueError(f'sync_mode must be one of {SYNC_MODES}')
        local_only = self.get_tag('-')
        local_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in local_only}
        remote_only = self.get_tag('+')
        remote_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in remote_only}
        local_and_remote = self.get_tag(' ')
        if sync_mode == 'error':
            if len(local_only) > 0 or len(remote_only) > 0:
                raise ValueError('There are utterances that exist in the local or remote instance that do not exist in the other instance. Please sync the routes before running this command.')
            else:
                return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': [], 'delete': []}}
        elif sync_mode == 'local':
            return {'remote': {'upsert': local_only, 'delete': remote_only}, 'local': {'upsert': [], 'delete': []}}
        elif sync_mode == 'remote':
            return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_only}}
        elif sync_mode == 'merge-force-local':
            local_route_names = set([utt.route for utt in local_only])
            local_route_utt_strs = set([utt.to_str() for utt in local_only])
            remote_to_keep = [utt for utt in remote_only if utt.route in local_route_names and utt.to_str() not in local_route_utt_strs]
            logger.info(f'local_only_mapper: {local_only_mapper}')
            remote_to_update = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_only if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
            remote_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_to_keep if utt.to_str() not in [x.to_str() for x in remote_to_update]]
            remote_to_delete = [utt for utt in remote_only if utt.route not in local_route_names]
            return {'remote': {'upsert': local_only + remote_to_update, 'delete': remote_to_delete}, 'local': {'upsert': remote_to_keep, 'delete': []}}
        elif sync_mode == 'merge-force-remote':
            remote_route_names = set([utt.route for utt in remote_only])
            remote_route_utt_strs = set([utt.to_str() for utt in remote_only])
            local_to_keep = [utt for utt in local_only if utt.route in remote_route_names and utt.to_str() not in remote_route_utt_strs]
            local_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=remote_only_mapper[utt.route][1], function_schemas=remote_only_mapper[utt.route][0]) for utt in local_to_keep]
            local_to_delete = [utt for utt in local_only if utt.route not in remote_route_names]
            return {'remote': {'upsert': local_to_keep, 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_to_delete}}
        elif sync_mode == 'merge':
            remote_only_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) if utt.route in local_only_mapper else utt for utt in remote_only]
            shared_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in local_and_remote if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
            return {'remote': {'upsert': local_only + shared_updated + remote_only_updated, 'delete': []}, 'local': {'upsert': remote_only_updated + shared_updated, 'delete': []}}
        else:
            raise ValueError(f'sync_mode must be one of {SYNC_MODES}')

@classmethod
def from_utterances(cls, local_utterances: List[Utterance], remote_utterances: List[Utterance]):
    """Create a UtteranceDiff object from two lists of Utterance objects.

        :param local_utterances: A list of Utterance objects.
        :type local_utterances: List[Utterance]
        :param remote_utterances: A list of Utterance objects.
        :type remote_utterances: List[Utterance]
        """
    local_utterances_map = {x.to_str(include_metadata=True): x for x in local_utterances}
    remote_utterances_map = {x.to_str(include_metadata=True): x for x in remote_utterances}
    local_utterances_str = list(local_utterances_map.keys())
    local_utterances_str.sort()
    remote_utterances_str = list(remote_utterances_map.keys())
    remote_utterances_str.sort()
    differ = Differ()
    diff_obj = list(differ.compare(local_utterances_str, remote_utterances_str))
    utterance_diffs = []
    for line in diff_obj:
        utterance_str = line[2:]
        utterance_diff_tag = line[0]
        if utterance_diff_tag == '?':
            continue
        utterance = remote_utterances_map[utterance_str] if utterance_diff_tag == '+' else local_utterances_map[utterance_str]
        utterance.diff_tag = utterance_diff_tag
        utterance_diffs.append(utterance)
    return UtteranceDiff(diff=utterance_diffs)

def get_sync_strategy(self, sync_mode: str) -> dict:
    """Generates the optimal synchronization plan for local and remote instances.

        :param sync_mode: The mode to sync the routes with the remote index.
        :type sync_mode: str
        :return: A dictionary describing the synchronization strategy.
        :rtype: dict
        """
    if sync_mode not in SYNC_MODES:
        raise ValueError(f'sync_mode must be one of {SYNC_MODES}')
    local_only = self.get_tag('-')
    local_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in local_only}
    remote_only = self.get_tag('+')
    remote_only_mapper = {utt.route: (utt.function_schemas, utt.metadata) for utt in remote_only}
    local_and_remote = self.get_tag(' ')
    if sync_mode == 'error':
        if len(local_only) > 0 or len(remote_only) > 0:
            raise ValueError('There are utterances that exist in the local or remote instance that do not exist in the other instance. Please sync the routes before running this command.')
        else:
            return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': [], 'delete': []}}
    elif sync_mode == 'local':
        return {'remote': {'upsert': local_only, 'delete': remote_only}, 'local': {'upsert': [], 'delete': []}}
    elif sync_mode == 'remote':
        return {'remote': {'upsert': [], 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_only}}
    elif sync_mode == 'merge-force-local':
        local_route_names = set([utt.route for utt in local_only])
        local_route_utt_strs = set([utt.to_str() for utt in local_only])
        remote_to_keep = [utt for utt in remote_only if utt.route in local_route_names and utt.to_str() not in local_route_utt_strs]
        logger.info(f'local_only_mapper: {local_only_mapper}')
        remote_to_update = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_only if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
        remote_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in remote_to_keep if utt.to_str() not in [x.to_str() for x in remote_to_update]]
        remote_to_delete = [utt for utt in remote_only if utt.route not in local_route_names]
        return {'remote': {'upsert': local_only + remote_to_update, 'delete': remote_to_delete}, 'local': {'upsert': remote_to_keep, 'delete': []}}
    elif sync_mode == 'merge-force-remote':
        remote_route_names = set([utt.route for utt in remote_only])
        remote_route_utt_strs = set([utt.to_str() for utt in remote_only])
        local_to_keep = [utt for utt in local_only if utt.route in remote_route_names and utt.to_str() not in remote_route_utt_strs]
        local_to_keep = [Utterance(route=utt.route, utterance=utt.utterance, metadata=remote_only_mapper[utt.route][1], function_schemas=remote_only_mapper[utt.route][0]) for utt in local_to_keep]
        local_to_delete = [utt for utt in local_only if utt.route not in remote_route_names]
        return {'remote': {'upsert': local_to_keep, 'delete': []}, 'local': {'upsert': remote_only, 'delete': local_to_delete}}
    elif sync_mode == 'merge':
        remote_only_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) if utt.route in local_only_mapper else utt for utt in remote_only]
        shared_updated = [Utterance(route=utt.route, utterance=utt.utterance, metadata=local_only_mapper[utt.route][1], function_schemas=local_only_mapper[utt.route][0]) for utt in local_and_remote if utt.route in local_only_mapper and (utt.metadata != local_only_mapper[utt.route][1] or utt.function_schemas != local_only_mapper[utt.route][0])]
        return {'remote': {'upsert': local_only + shared_updated + remote_only_updated, 'delete': []}, 'local': {'upsert': remote_only_updated + shared_updated, 'delete': []}}
    else:
        raise ValueError(f'sync_mode must be one of {SYNC_MODES}')

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

def delete_index(self):
    """Delete the index.

        :return: None
        :rtype: None
        """
    self.client.delete_index(self.index_name)
    self.index = None

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

def mock_encoder_call(utterances):
    mock_responses = {'Hello': [0.1, 0.2, 0.3], 'Hi': [0.4, 0.5, 0.6], 'Goodbye': [0.7, 0.8, 0.9], 'Bye': [1.0, 1.1, 1.2], 'Au revoir': [1.3, 1.4, 1.5], 'Asparagus': [-2.0, 1.0, 0.0]}
    return [mock_responses.get(u, [0.0, 0.0, 0.0]) for u in utterances]

class TestRouterConfig:

    def test_from_file_json(self, tmp_path):
        config_path = tmp_path / 'config.json'
        config_path.write_text(layer_json())
        layer_config = RouterConfig.from_file(str(config_path))
        assert layer_config.encoder_type == 'cohere'
        assert layer_config.encoder_name == 'embed-english-v3.0'
        assert len(layer_config.routes) == 2
        assert layer_config.routes[0].name == 'politics'

    def test_from_file_yaml(self, tmp_path):
        config_path = tmp_path / 'config.yaml'
        config_path.write_text(layer_yaml())
        layer_config = RouterConfig.from_file(str(config_path))
        assert layer_config.encoder_type == 'cohere'
        assert layer_config.encoder_name == 'embed-english-v3.0'
        assert len(layer_config.routes) == 2
        assert layer_config.routes[0].name == 'politics'

    def test_from_file_invalid_path(self):
        with pytest.raises(FileNotFoundError) as excinfo:
            RouterConfig.from_file('nonexistent_path.json')
        assert "[Errno 2] No such file or directory: 'nonexistent_path.json'" in str(excinfo.value)

    def test_from_file_unsupported_type(self, tmp_path):
        config_path = tmp_path / 'config.unsupported'
        config_path.write_text(layer_json())
        with pytest.raises(ValueError) as excinfo:
            RouterConfig.from_file(str(config_path))
        assert 'Unsupported file type' in str(excinfo.value)

    def test_from_file_invalid_config(self, tmp_path):
        invalid_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": "This should be a list, not a string"\n        }'
        config_path = tmp_path / 'invalid_config.json'
        with open(config_path, 'w') as file:
            file.write(invalid_config_json)
        with patch('semantic_router.routers.base.is_valid', return_value=False):
            with pytest.raises(Exception) as excinfo:
                RouterConfig.from_file(str(config_path))
            assert 'Invalid config JSON or YAML' in str(excinfo.value), 'Loading an invalid configuration should raise an exception.'

    def test_from_file_with_llm(self, tmp_path):
        llm_config_json = '\n        {\n            "encoder_type": "cohere",\n            "encoder_name": "embed-english-v3.0",\n            "routes": [\n                {\n                    "name": "llm_route",\n                    "utterances": ["tell me a joke", "say something funny"],\n                    "llm": {\n                        "module": "semantic_router.llms.base",\n                        "class": "BaseLLM",\n                        "model": "fake-model-v1"\n                    }\n                }\n            ]\n        }'
        config_path = tmp_path / 'config_with_llm.json'
        with open(config_path, 'w') as file:
            file.write(llm_config_json)
        layer_config = RouterConfig.from_file(str(config_path))
        assert isinstance(layer_config.routes[0].llm, BaseLLM), 'LLM should be instantiated and associated with the route based on the '
        'config'
        assert layer_config.routes[0].llm.name == 'fake-model-v1', "LLM instance should have the 'name' attribute set correctly"

    def test_init(self):
        layer_config = RouterConfig()
        assert layer_config.routes == []

    def test_to_file_json(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with patch('builtins.open', mock_open()) as mocked_open:
            layer_config.to_file('data/test_output.json')
            mocked_open.assert_called_once_with('data/test_output.json', 'w')

    def test_to_file_yaml(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with patch('builtins.open', mock_open()) as mocked_open:
            layer_config.to_file('data/test_output.yaml')
            mocked_open.assert_called_once_with('data/test_output.yaml', 'w')

    def test_to_file_invalid(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        with pytest.raises(ValueError):
            layer_config.to_file('test_output.txt')

    def test_from_file_invalid(self):
        with open('test.txt', 'w') as f:
            f.write('dummy content')
        with pytest.raises(ValueError):
            RouterConfig.from_file('test.txt')
        os.remove('test.txt')

    def test_to_dict(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.to_dict()['routes'] == [route.to_dict()]

    def test_add(self):
        route = Route(name='test', utterances=['utterance'])
        route2 = Route(name='test2', utterances=['utterance2'])
        layer_config = RouterConfig()
        layer_config.add(route)
        assert layer_config.routes == [route]
        layer_config.add(route2)
        assert layer_config.routes == [route, route2]

    def test_get(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.get('test') == route

    def test_get_not_found(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        assert layer_config.get('not_found') is None

    def test_remove(self):
        route = Route(name='test', utterances=['utterance'])
        layer_config = RouterConfig(routes=[route])
        layer_config.remove('test')
        assert layer_config.routes == []

    def test_setting_aggregation_methods(self, openai_encoder, routes):
        for agg in ['sum', 'mean', 'max']:
            route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
            assert route_layer.aggregation == agg

    def test_semantic_classify_multiple_routes_with_different_aggregation(self, openai_encoder, routes):
        route_scores = [{'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 2', 'score': 0.4}, {'route': 'Route 2', 'score': 0.6}, {'route': 'Route 2', 'score': 0.8}, {'route': 'Route 3', 'score': 0.1}, {'route': 'Route 3', 'score': 1.0}]
        for agg in ['sum', 'mean', 'max']:
            route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
            classification, score = route_layer._semantic_classify(route_scores)
            if agg == 'sum':
                assert classification == 'Route 1'
                assert score == [0.5, 0.5, 0.5, 0.5]
            elif agg == 'mean':
                assert classification == 'Route 2'
                assert score == [0.4, 0.6, 0.8]
            elif agg == 'max':
                assert classification == 'Route 3'
                assert score == [0.1, 1.0]

def test_setting_aggregation_methods(self, openai_encoder, routes):
    for agg in ['sum', 'mean', 'max']:
        route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
        assert route_layer.aggregation == agg

def test_semantic_classify_multiple_routes_with_different_aggregation(self, openai_encoder, routes):
    route_scores = [{'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 1', 'score': 0.5}, {'route': 'Route 2', 'score': 0.4}, {'route': 'Route 2', 'score': 0.6}, {'route': 'Route 2', 'score': 0.8}, {'route': 'Route 3', 'score': 0.1}, {'route': 'Route 3', 'score': 1.0}]
    for agg in ['sum', 'mean', 'max']:
        route_layer = SemanticRouter(encoder=openai_encoder, routes=routes, aggregation=agg)
        classification, score = route_layer._semantic_classify(route_scores)
        if agg == 'sum':
            assert classification == 'Route 1'
            assert score == [0.5, 0.5, 0.5, 0.5]
        elif agg == 'mean':
            assert classification == 'Route 2'
            assert score == [0.4, 0.6, 0.8]
        elif agg == 'max':
            assert classification == 'Route 3'
            assert score == [0.1, 1.0]

@pytest.mark.parametrize('router_cls,index_cls', [(router, index) for router in [HybridRouter, SemanticRouter] for index in [None] + get_test_indexes()])
class TestRouter:

    def test_query_parameter(self, router_cls, index_cls, routes_5, mocker):
        """Test that we return expected values in RouteChoice objects."""
        dense_encoder = MockSymmetricDenseEncoder(name='Dense Encoder')
        index = init_index(index_cls) if index_cls else None
        if router_cls == HybridRouter:
            sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
            router = router_cls(encoder=dense_encoder, sparse_encoder=sparse_encoder, routes=routes_5, index=index, auto_sync='local')
        else:
            router = router_cls(encoder=dense_encoder, routes=routes_5, index=index, auto_sync='local')
        _ = mocker.patch.object(router, '_score_routes', return_value=[('Route 1', 0.9, [0.1, 0.2, 0.3]), ('Route 2', 0.8, [0.4, 0.5, 0.6]), ('Route 3', 0.7, [0.7, 0.8, 0.9]), ('Route 4', 0.6, [1.0, 1.1, 1.2])])
        result = router('test query')
        assert result is not None
        assert isinstance(result, RouteChoice)
        assert result.name == 'Route 1'
        assert result.similarity_score == 0.9
        assert result.function_call is None

    def test_limit_parameter(self, router_cls, index_cls, routes_5, mocker):
        """Test that the limit parameter works correctly for sync router calls."""
        dense_encoder = MockSymmetricDenseEncoder(name='Dense Encoder')
        index = init_index(index_cls) if index_cls else None
        if router_cls == HybridRouter:
            sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
            router = router_cls(encoder=dense_encoder, sparse_encoder=sparse_encoder, routes=routes_5, index=index, auto_sync='local')
        else:
            router = router_cls(encoder=dense_encoder, routes=routes_5, index=index, auto_sync='local')
        _ = mocker.patch.object(router, '_score_routes', return_value=[('Route 1', 0.9, [0.1, 0.2, 0.3]), ('Route 2', 0.8, [0.4, 0.5, 0.6]), ('Route 3', 0.7, [0.7, 0.8, 0.9]), ('Route 4', 0.6, [1.0, 1.1, 1.2])])
        result = router('test query')
        assert result is not None
        assert isinstance(result, RouteChoice)
        result = router('test query', limit=2)
        assert result is not None
        assert len(result) == 2
        result = router('test query', limit=None)
        assert result is not None
        assert len(result) == 4

    def test_index_operations(self, router_cls, index_cls, routes, openai_encoder):
        """Test index-specific operations like add, delete, and sync."""
        if index_cls is None:
            pytest.skip('Test only for specific index implementations')
        index = init_index(index_cls)
        if router_cls == HybridRouter:
            sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
            router = router_cls(encoder=openai_encoder, sparse_encoder=sparse_encoder, routes=[], index=index, auto_sync='local')
        else:
            router = router_cls(encoder=openai_encoder, routes=[], index=index, auto_sync='local')
        assert len(router.index) == 0
        router.add(routes[0])
        assert len(router.index) == 2
        router.add(routes[1])
        assert len(router.index) == 5
        router.delete('Route 1')
        assert len(router.index) == 3
        router.index.delete_index()
        assert len(router.index) == 0

def test_query_parameter(self, router_cls, index_cls, routes_5, mocker):
    """Test that we return expected values in RouteChoice objects."""
    dense_encoder = MockSymmetricDenseEncoder(name='Dense Encoder')
    index = init_index(index_cls) if index_cls else None
    if router_cls == HybridRouter:
        sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
        router = router_cls(encoder=dense_encoder, sparse_encoder=sparse_encoder, routes=routes_5, index=index, auto_sync='local')
    else:
        router = router_cls(encoder=dense_encoder, routes=routes_5, index=index, auto_sync='local')
    _ = mocker.patch.object(router, '_score_routes', return_value=[('Route 1', 0.9, [0.1, 0.2, 0.3]), ('Route 2', 0.8, [0.4, 0.5, 0.6]), ('Route 3', 0.7, [0.7, 0.8, 0.9]), ('Route 4', 0.6, [1.0, 1.1, 1.2])])
    result = router('test query')
    assert result is not None
    assert isinstance(result, RouteChoice)
    assert result.name == 'Route 1'
    assert result.similarity_score == 0.9
    assert result.function_call is None

def test_limit_parameter(self, router_cls, index_cls, routes_5, mocker):
    """Test that the limit parameter works correctly for sync router calls."""
    dense_encoder = MockSymmetricDenseEncoder(name='Dense Encoder')
    index = init_index(index_cls) if index_cls else None
    if router_cls == HybridRouter:
        sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
        router = router_cls(encoder=dense_encoder, sparse_encoder=sparse_encoder, routes=routes_5, index=index, auto_sync='local')
    else:
        router = router_cls(encoder=dense_encoder, routes=routes_5, index=index, auto_sync='local')
    _ = mocker.patch.object(router, '_score_routes', return_value=[('Route 1', 0.9, [0.1, 0.2, 0.3]), ('Route 2', 0.8, [0.4, 0.5, 0.6]), ('Route 3', 0.7, [0.7, 0.8, 0.9]), ('Route 4', 0.6, [1.0, 1.1, 1.2])])
    result = router('test query')
    assert result is not None
    assert isinstance(result, RouteChoice)
    result = router('test query', limit=2)
    assert result is not None
    assert len(result) == 2
    result = router('test query', limit=None)
    assert result is not None
    assert len(result) == 4

def test_index_operations(self, router_cls, index_cls, routes, openai_encoder):
    """Test index-specific operations like add, delete, and sync."""
    if index_cls is None:
        pytest.skip('Test only for specific index implementations')
    index = init_index(index_cls)
    if router_cls == HybridRouter:
        sparse_encoder = MockSymmetricSparseEncoder(name='Sparse Encoder')
        router = router_cls(encoder=openai_encoder, sparse_encoder=sparse_encoder, routes=[], index=index, auto_sync='local')
    else:
        router = router_cls(encoder=openai_encoder, routes=[], index=index, auto_sync='local')
    assert len(router.index) == 0
    router.add(routes[0])
    assert len(router.index) == 2
    router.add(routes[1])
    assert len(router.index) == 5
    router.delete('Route 1')
    assert len(router.index) == 3
    router.index.delete_index()
    assert len(router.index) == 0

def mock_encoder_call(utterances):
    mock_responses = {'Hello': [0.1, 0.2, 0.3], 'Hi': [0.4, 0.5, 0.6], 'Goodbye': [0.7, 0.8, 0.9], 'Bye': [1.0, 1.1, 1.2], 'Au revoir': [1.3, 1.4, 1.5], 'Asparagus': [-2.0, 1.0, 0.0]}
    return [mock_responses.get(u, [0.3, 0.1, 0.2]) for u in utterances]

def include_metadata(index_cls):
    return INCLUDE_METADATA_MAP.get(index_cls, False)

@pytest.mark.parametrize('index_cls,router_cls', [(index, router) for index in get_test_indexes() for router in get_test_routers()])
class TestSemanticRouter:

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_initialization(self, openai_encoder, routes, index_cls, router_cls):
        index = init_index(index_cls, index_name=router_cls.__name__)
        _ = router_cls(encoder=openai_encoder, routes=routes, top_k=10, index=index, auto_sync='local')

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_second_initialization_sync(self, openai_encoder, routes, index_cls, router_cls):
        index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
        assert route_layer.is_synced()

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_second_initialization_not_synced(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        index = init_index(index_cls, index_name=router_cls.__name__)
        _ = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=index)
        assert route_layer.is_synced() is False

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_utterance_diff(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        index = init_index(index_cls, index_name=router_cls.__name__)
        _ = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
        route_layer_2 = router_cls(encoder=openai_encoder, routes=routes_2, index=index)
        diff = route_layer_2.get_utterance_diff(include_metadata=True)
        assert '+ Route 1: Hello | None | {"type": "default"}' in diff
        assert '+ Route 1: Hi | None | {"type": "default"}' in diff
        assert '- Route 1: Hello | None | {}' in diff
        assert '+ Route 2: Au revoir | None | {}' in diff
        assert '- Route 2: Hi | None | {}' in diff
        assert '+ Route 2: Bye | None | {}' in diff
        assert '+ Route 2: Goodbye | None | {}' in diff
        assert '+ Route 3: Boo | None | {}' in diff

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_auto_sync_local(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        if index_cls is PineconeIndex:
            pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
            _ = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index)
            route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
            assert route_layer.index.get_utterances(include_metadata=True) == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_auto_sync_remote(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        if index_cls is PineconeIndex:
            pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
            _ = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
            route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='remote')
            assert route_layer.index.get_utterances(include_metadata=True) == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_auto_sync_merge_force_local(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        if index_cls is PineconeIndex:
            pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
            route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='local')
            route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='merge-force-local')
            assert route_layer.is_synced()
            local_utterances = route_layer.index.get_utterances(include_metadata=False)
            local_utterances.sort(key=lambda x: x.to_str(include_metadata=False))
            assert local_utterances == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 1', utterance='Hi'), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_auto_sync_merge_force_remote(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        if index_cls is PineconeIndex:
            pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
            route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='local')
            assert route_layer.is_synced()
            r1_utterances = [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 3', utterance='Boo')]
            local_utterances = route_layer.index.get_utterances(include_metadata=True)
            local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
            assert local_utterances == r1_utterances
            route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='merge-force-remote')
            assert route_layer.is_synced()
            local_utterances = route_layer.index.get_utterances(include_metadata=True)
            local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
            assert local_utterances == [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi'), Utterance(route='Route 3', utterance='Boo')], 'The routes in the index should match the local routes'

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_sync(self, openai_encoder, index_cls, router_cls):
        route_layer = router_cls(encoder=openai_encoder, routes=[], index=init_index(index_cls, index_name=router_cls.__name__), auto_sync=None)
        route_layer.sync('remote')
        assert route_layer.is_synced()

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_auto_sync_merge(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        if index_cls is PineconeIndex:
            pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
            route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
            route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='merge')
            assert route_layer.is_synced()
            local_utterances = route_layer.index.get_utterances(include_metadata=True)
            local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
            assert local_utterances == [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi'), Utterance(route='Route 3', utterance='Boo')], 'The routes in the index should match the local routes'

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_sync_lock_prevents_concurrent_sync(self, openai_encoder, routes, routes_2, index_cls, router_cls):
        """Test that sync lock prevents concurrent synchronization operations"""
        index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=index, auto_sync='local')
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync=None)
        route_layer.index.lock(value=True)
        with pytest.raises(Exception):
            route_layer.sync('local')
        route_layer.index.lock(value=False)
        route_layer.sync('local')
        assert route_layer.is_synced()

    @pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
    def test_sync_lock_auto_releases(self, openai_encoder, routes, index_cls, router_cls):
        """Test that sync lock is automatically released after sync operations"""
        index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
        route_layer.sync('local')
        assert route_layer.is_synced()
        if index_cls is PineconeIndex:
            route_layer.index.client.delete_index(route_layer.index.index_name)

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_initialization(self, openai_encoder, routes, index_cls, router_cls):
    index = init_index(index_cls, index_name=router_cls.__name__)
    _ = router_cls(encoder=openai_encoder, routes=routes, top_k=10, index=index, auto_sync='local')

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_second_initialization_sync(self, openai_encoder, routes, index_cls, router_cls):
    index = init_index(index_cls, index_name=router_cls.__name__)
    route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
    assert route_layer.is_synced()

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_second_initialization_not_synced(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    index = init_index(index_cls, index_name=router_cls.__name__)
    _ = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
    route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=index)
    assert route_layer.is_synced() is False

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_utterance_diff(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    index = init_index(index_cls, index_name=router_cls.__name__)
    _ = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
    route_layer_2 = router_cls(encoder=openai_encoder, routes=routes_2, index=index)
    diff = route_layer_2.get_utterance_diff(include_metadata=True)
    assert '+ Route 1: Hello | None | {"type": "default"}' in diff
    assert '+ Route 1: Hi | None | {"type": "default"}' in diff
    assert '- Route 1: Hello | None | {}' in diff
    assert '+ Route 2: Au revoir | None | {}' in diff
    assert '- Route 2: Hi | None | {}' in diff
    assert '+ Route 2: Bye | None | {}' in diff
    assert '+ Route 2: Goodbye | None | {}' in diff
    assert '+ Route 3: Boo | None | {}' in diff

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_auto_sync_local(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    if index_cls is PineconeIndex:
        pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
        _ = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index)
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
        assert route_layer.index.get_utterances(include_metadata=True) == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_auto_sync_remote(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    if index_cls is PineconeIndex:
        pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
        _ = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='remote')
        assert route_layer.index.get_utterances(include_metadata=True) == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_auto_sync_merge_force_local(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    if index_cls is PineconeIndex:
        pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='local')
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='merge-force-local')
        assert route_layer.is_synced()
        local_utterances = route_layer.index.get_utterances(include_metadata=False)
        local_utterances.sort(key=lambda x: x.to_str(include_metadata=False))
        assert local_utterances == [Utterance(route='Route 1', utterance='Hello'), Utterance(route='Route 1', utterance='Hi'), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi')], 'The routes in the index should match the local routes'

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_auto_sync_merge_force_remote(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    if index_cls is PineconeIndex:
        pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='local')
        assert route_layer.is_synced()
        r1_utterances = [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 3', utterance='Boo')]
        local_utterances = route_layer.index.get_utterances(include_metadata=True)
        local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
        assert local_utterances == r1_utterances
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='merge-force-remote')
        assert route_layer.is_synced()
        local_utterances = route_layer.index.get_utterances(include_metadata=True)
        local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
        assert local_utterances == [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi'), Utterance(route='Route 3', utterance='Boo')], 'The routes in the index should match the local routes'

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_sync(self, openai_encoder, index_cls, router_cls):
    route_layer = router_cls(encoder=openai_encoder, routes=[], index=init_index(index_cls, index_name=router_cls.__name__), auto_sync=None)
    route_layer.sync('remote')
    assert route_layer.is_synced()

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_auto_sync_merge(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    if index_cls is PineconeIndex:
        pinecone_index = init_index(index_cls, index_name=router_cls.__name__)
        route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=pinecone_index, auto_sync='local')
        route_layer = router_cls(encoder=openai_encoder, routes=routes, index=pinecone_index, auto_sync='merge')
        assert route_layer.is_synced()
        local_utterances = route_layer.index.get_utterances(include_metadata=True)
        local_utterances.sort(key=lambda x: x.to_str(include_metadata=True))
        assert local_utterances == [Utterance(route='Route 1', utterance='Hello', metadata={'type': 'default'}), Utterance(route='Route 1', utterance='Hi', metadata={'type': 'default'}), Utterance(route='Route 2', utterance='Au revoir'), Utterance(route='Route 2', utterance='Bye'), Utterance(route='Route 2', utterance='Goodbye'), Utterance(route='Route 2', utterance='Hi'), Utterance(route='Route 3', utterance='Boo')], 'The routes in the index should match the local routes'

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_sync_lock_prevents_concurrent_sync(self, openai_encoder, routes, routes_2, index_cls, router_cls):
    """Test that sync lock prevents concurrent synchronization operations"""
    index = init_index(index_cls, index_name=router_cls.__name__)
    route_layer = router_cls(encoder=openai_encoder, routes=routes_2, index=index, auto_sync='local')
    route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync=None)
    route_layer.index.lock(value=True)
    with pytest.raises(Exception):
        route_layer.sync('local')
    route_layer.index.lock(value=False)
    route_layer.sync('local')
    assert route_layer.is_synced()

@pytest.mark.skipif(os.environ.get('PINECONE_API_KEY') is None, reason='Pinecone API key required')
def test_sync_lock_auto_releases(self, openai_encoder, routes, index_cls, router_cls):
    """Test that sync lock is automatically released after sync operations"""
    index = init_index(index_cls, index_name=router_cls.__name__)
    route_layer = router_cls(encoder=openai_encoder, routes=routes, index=index, auto_sync='local')
    route_layer.sync('local')
    assert route_layer.is_synced()
    if index_cls is PineconeIndex:
        route_layer.index.client.delete_index(route_layer.index.index_name)

@pytest.fixture
@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
def bm25_encoder():
    sparse_encoder = BM25Encoder(use_default_params=True)
    sparse_encoder.fit([Route(name='test_route', utterances=['The quick brown fox', 'jumps over the lazy dog', 'Hello, world!'])])
    return sparse_encoder

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

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
def test_encode_queries_unfitted(self):
    encoder = BM25Encoder(use_default_params=True)
    with pytest.raises(ValueError, match='Encoder not fitted'):
        encoder.encode_queries(['test query'])

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
def test_encode_documents_unfitted(self):
    encoder = BM25Encoder(use_default_params=True)
    with pytest.raises(ValueError, match='Encoder not fitted'):
        encoder.encode_documents(['test document'])

class TestClipEncoder:

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder__import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                CLIPEncoder()
        assert 'install transformers' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder__import_errors_torch(self):
        with patch.dict('sys.modules', {'torch': None}):
            with pytest.raises(ImportError) as error:
                CLIPEncoder()
        assert 'install Pytorch' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_initialization(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        assert clip_encoder.name == test_model_name
        assert clip_encoder.type == 'huggingface'
        assert clip_encoder.score_threshold == 0.2
        assert clip_encoder.device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_text(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        embeddings = clip_encoder(['hello', 'world'])
        assert len(embeddings) == 2
        assert len(embeddings[0]) == embed_dim

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_image(self, dummy_pil_image):
        clip_encoder = CLIPEncoder(name=test_model_name)
        encoded_images = clip_encoder([dummy_pil_image] * 3)
        assert len(encoded_images) == 3
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
        clip_encoder = CLIPEncoder(name=test_model_name)
        encoded_images = clip_encoder([dummy_pil_image, misshaped_pil_image])
        assert len(encoded_images) == 2
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_device(self):
        clip_encoder = CLIPEncoder(name=test_model_name)
        device = clip_encoder._model.device.type
        assert device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_clip_encoder_ensure_rgb(self, dummy_black_and_white_img):
        clip_encoder = CLIPEncoder(name=test_model_name)
        rgb_image = clip_encoder._ensure_rgb(dummy_black_and_white_img)
        assert rgb_image.mode == 'RGB'
        assert np.array(rgb_image).shape == (224, 224, 3)

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder_initialization(self):
    clip_encoder = CLIPEncoder(name=test_model_name)
    assert clip_encoder.name == test_model_name
    assert clip_encoder.type == 'huggingface'
    assert clip_encoder.score_threshold == 0.2
    assert clip_encoder.device == device

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder_call_text(self):
    clip_encoder = CLIPEncoder(name=test_model_name)
    embeddings = clip_encoder(['hello', 'world'])
    assert len(embeddings) == 2
    assert len(embeddings[0]) == embed_dim

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder_call_image(self, dummy_pil_image):
    clip_encoder = CLIPEncoder(name=test_model_name)
    encoded_images = clip_encoder([dummy_pil_image] * 3)
    assert len(encoded_images) == 3
    assert set(map(len, encoded_images)) == {embed_dim}

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
    clip_encoder = CLIPEncoder(name=test_model_name)
    encoded_images = clip_encoder([dummy_pil_image, misshaped_pil_image])
    assert len(encoded_images) == 2
    assert set(map(len, encoded_images)) == {embed_dim}

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_device(self):
    clip_encoder = CLIPEncoder(name=test_model_name)
    device = clip_encoder._model.device.type
    assert device == device

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_clip_encoder_ensure_rgb(self, dummy_black_and_white_img):
    clip_encoder = CLIPEncoder(name=test_model_name)
    rgb_image = clip_encoder._ensure_rgb(dummy_black_and_white_img)
    assert rgb_image.mode == 'RGB'
    assert np.array(rgb_image).shape == (224, 224, 3)

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

class TestVitEncoder:

    def test_vit_encoder__import_errors_transformers(self):
        with patch.dict('sys.modules', {'transformers': None}):
            with pytest.raises(ImportError) as error:
                VitEncoder()
        assert 'Please install transformers to use VitEncoder' in str(error.value)

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_initialization(self):
        vit_encoder = VitEncoder(name=test_model_name)
        assert vit_encoder.name == test_model_name
        assert vit_encoder.type == 'huggingface'
        assert vit_encoder.score_threshold == 0.5
        assert vit_encoder.device == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_call(self, dummy_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        encoded_images = vit_encoder([dummy_pil_image] * 3)
        assert len(encoded_images) == 3
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        encoded_images = vit_encoder([dummy_pil_image, misshaped_pil_image])
        assert len(encoded_images) == 2
        assert set(map(len, encoded_images)) == {embed_dim}

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_process_images_device(self, dummy_pil_image):
        vit_encoder = VitEncoder(name=test_model_name)
        imgs = vit_encoder._process_images([dummy_pil_image] * 3)['pixel_values']
        assert imgs.device.type == device

    @pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
    def test_vit_encoder_ensure_rgb(self, dummy_black_and_white_img):
        vit_encoder = VitEncoder(name=test_model_name)
        rgb_image = vit_encoder._ensure_rgb(dummy_black_and_white_img)
        assert rgb_image.mode == 'RGB'
        assert np.array(rgb_image).shape == (224, 224, 3)

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_vit_encoder_initialization(self):
    vit_encoder = VitEncoder(name=test_model_name)
    assert vit_encoder.name == test_model_name
    assert vit_encoder.type == 'huggingface'
    assert vit_encoder.score_threshold == 0.5
    assert vit_encoder.device == device

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_vit_encoder_call(self, dummy_pil_image):
    vit_encoder = VitEncoder(name=test_model_name)
    encoded_images = vit_encoder([dummy_pil_image] * 3)
    assert len(encoded_images) == 3
    assert set(map(len, encoded_images)) == {embed_dim}

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_vit_encoder_call_misshaped(self, dummy_pil_image, misshaped_pil_image):
    vit_encoder = VitEncoder(name=test_model_name)
    encoded_images = vit_encoder([dummy_pil_image, misshaped_pil_image])
    assert len(encoded_images) == 2
    assert set(map(len, encoded_images)) == {embed_dim}

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_vit_encoder_process_images_device(self, dummy_pil_image):
    vit_encoder = VitEncoder(name=test_model_name)
    imgs = vit_encoder._process_images([dummy_pil_image] * 3)['pixel_values']
    assert imgs.device.type == device

@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run')
def test_vit_encoder_ensure_rgb(self, dummy_black_and_white_img):
    vit_encoder = VitEncoder(name=test_model_name)
    rgb_image = vit_encoder._ensure_rgb(dummy_black_and_white_img)
    assert rgb_image.mode == 'RGB'
    assert np.array(rgb_image).shape == (224, 224, 3)

@pytest.mark.parametrize('index_cls,encoder_cls,router_cls', [(index, encoder, router) for index in get_test_indexes() for encoder in get_test_encoders() for router in get_test_routers()])
class TestIndexEncoders:

    def test_initialization(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local', top_k=10)
        score_threshold = route_layer.score_threshold
        if isinstance(route_layer, HybridRouter):
            assert score_threshold == encoder.score_threshold * route_layer.alpha
        else:
            assert score_threshold == encoder.score_threshold
        assert route_layer.top_k == 10

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_index_populated():
            assert len(route_layer.index) == 5
        check_index_populated()
        assert len(set(route_layer._get_route_names())) if route_layer._get_route_names() is not None else 0 == 2

    def test_initialization_different_encoders(self, encoder_cls, index_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, index=index)
        score_threshold = route_layer.score_threshold
        if isinstance(route_layer, HybridRouter):
            assert score_threshold == encoder.score_threshold * route_layer.alpha
        else:
            assert score_threshold == encoder.score_threshold

    def test_initialization_no_encoder(self, index_cls, encoder_cls, router_cls):
        route_layer_none = router_cls(encoder=None)
        score_threshold = route_layer_none.score_threshold
        if isinstance(route_layer_none, HybridRouter):
            assert score_threshold == 0.3 * route_layer_none.alpha
        else:
            assert score_threshold == 0.3

def test_initialization(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local', top_k=10)
    score_threshold = route_layer.score_threshold
    if isinstance(route_layer, HybridRouter):
        assert score_threshold == encoder.score_threshold * route_layer.alpha
    else:
        assert score_threshold == encoder.score_threshold
    assert route_layer.top_k == 10

    @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
    def check_index_populated():
        assert len(route_layer.index) == 5
    check_index_populated()
    assert len(set(route_layer._get_route_names())) if route_layer._get_route_names() is not None else 0 == 2

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_index_populated():
    assert len(route_layer.index) == 5

def test_initialization_different_encoders(self, encoder_cls, index_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, index=index)
    score_threshold = route_layer.score_threshold
    if isinstance(route_layer, HybridRouter):
        assert score_threshold == encoder.score_threshold * route_layer.alpha
    else:
        assert score_threshold == encoder.score_threshold

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_index_populated():
    route_layer.add(routes=routes)
    assert route_layer.index is not None
    assert len(route_layer.index.get_utterances()) == 5

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def delete_index():
    route_layer.index.delete_index()
    assert route_layer.index.get_utterances() == []

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_index_empty():
    assert route_layer.index.get_utterances() == []

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_index_populated1():
    assert route_layer.routes == [routes[0]]
    assert route_layer.index is not None
    assert len(route_layer.index.get_utterances()) == 2

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_index_populated2():
    assert route_layer.routes == [routes[0], routes[1]]
    assert len(route_layer.index.get_utterances()) == 5

def test_list_route_names(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

    @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
    def check_route_names():
        route_names = route_layer.list_route_names()
        assert set(route_names) == {route.name for route in routes}, 'The list of route names should match the names of the routes added.'
    check_route_names()

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_route_names():
    route_names = route_layer.list_route_names()
    assert set(route_names) == {route.name for route in routes}, 'The list of route names should match the names of the routes added.'

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def delete_route_by_name():
    route_to_delete = routes[0].name
    route_layer.delete(route_to_delete)
    assert route_to_delete not in route_layer.list_route_names(), 'The route should be deleted from the route layer.'
    for utterance in routes[0].utterances:
        assert utterance not in route_layer.index, "The route's utterances should be deleted from the index."

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_query_result():
    if router_cls is HybridRouter:
        query_result = route_layer(vector=vector, sparse_vector=sparse_vector).name
    else:
        query_result = route_layer(vector=vector).name
    assert query_result in ['Route 1', 'Route 2']

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

@retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
def check_raises_value_error():
    try:
        route_layer(text='Hello', route_filter=['Route 8']).name
    except ValueError:
        assert True

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

@pytest.mark.parametrize('index_cls,encoder_cls,router_cls', [(index, encoder, router) for index in [LocalIndex] for encoder in [OpenAIEncoder] for router in get_test_routers()])
class TestRouterOnly:

    def test_semantic_classify(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        classification, score = route_layer._semantic_classify([{'route': 'Route 1', 'score': 0.9}, {'route': 'Route 2', 'score': 0.1}])
        assert classification == 'Route 1'
        assert score == [0.9]

    def test_semantic_classify_multiple_routes(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        classification, score = route_layer._semantic_classify([{'route': 'Route 1', 'score': 0.9}, {'route': 'Route 2', 'score': 0.1}, {'route': 'Route 1', 'score': 0.8}])
        assert classification == 'Route 1'
        assert score == [0.9, 0.8]

    def test_query_no_text_dynamic_route(self, dynamic_routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=dynamic_routes, index=index)
        vector = encoder(['hello'])
        if router_cls is HybridRouter:
            sparse_vector = route_layer.sparse_encoder(['hello'])[0]
        with pytest.raises(ValueError):
            if router_cls is HybridRouter:
                route_layer(vector=vector, sparse_vector=sparse_vector)
            else:
                route_layer(vector=vector)

    def test_failover_score_threshold(self, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, index=index, auto_sync='local')
        if router_cls is HybridRouter:
            assert route_layer.score_threshold == 0.3 * route_layer.alpha
        else:
            assert route_layer.score_threshold == 0.3

    def test_json(self, routes, index_cls, encoder_cls, router_cls):
        temp = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
        try:
            temp_path = temp.name
            temp.close()
            encoder = encoder_cls()
            index = init_index(index_cls, index_name=encoder.__class__.__name__)
            route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
            route_layer.to_json(temp_path)
            assert os.path.exists(temp_path)
            route_layer_from_file = SemanticRouter.from_json(temp_path)
            assert route_layer_from_file.index is not None and route_layer_from_file._get_route_names() is not None
        finally:
            os.remove(temp_path)

    def test_yaml(self, routes, index_cls, encoder_cls, router_cls):
        temp = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
        try:
            temp_path = temp.name
            temp.close()
            encoder = encoder_cls()
            index = init_index(index_cls, index_name=encoder.__class__.__name__)
            route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
            route_layer.to_yaml(temp_path)
            assert os.path.exists(temp_path)
            route_layer_from_file = SemanticRouter.from_yaml(temp_path)
            assert route_layer_from_file.index is not None and route_layer_from_file._get_route_names() is not None
        finally:
            os.remove(temp_path)

    def test_config(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        layer_config = route_layer.to_config()
        assert layer_config.routes == route_layer.routes
        route_layer_from_config = SemanticRouter.from_config(layer_config, index)
        assert route_layer_from_config._get_route_names() == route_layer._get_route_names()
        if router_cls is HybridRouter:
            pass
        else:
            assert route_layer_from_config.score_threshold == route_layer.score_threshold

    def test_get_thresholds(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        if router_cls is HybridRouter:
            target = encoder.score_threshold * route_layer.alpha
            assert route_layer.get_thresholds() == {'Route 1': target, 'Route 2': target}
        else:
            assert route_layer.get_thresholds() == {'Route 1': 0.3, 'Route 2': 0.3}

    def test_with_multiple_routes_passing_threshold(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.set_threshold(threshold=0.0)
        results = route_layer(text='Hello', limit=2)
        assert len(results) == 2
        assert results[0].name == 'Route 1', f'Expected Route 1 in position 0, got {results}'
        assert results[1].name == 'Route 2', f'Expected Route 2 in position 1, got {results}'

    def test_with_no_routes_passing_threshold(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.set_threshold(threshold=1.0)
        results = route_layer(text='Hello', limit=None)
        assert results == RouteChoice()

    def test_with_no_query_results(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.set_threshold(threshold=0.5)
        results = route_layer(text='this should not be similar to anything', limit=None)
        assert results == RouteChoice()

    def test_with_unrecognized_route(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.set_threshold(threshold=0.5)
        query_results = [{'route': 'UnrecognizedRoute', 'score': 0.9}]
        results = route_layer._semantic_classify(query_results)
        assert results == ('UnrecognizedRoute', [0.9]), 'Semantic classify can return unrecognized routes'

    def test_set_aggregation_method_with_unsupported_value(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        unsupported_aggregation = 'unsupported_aggregation_method'
        with pytest.raises(ValueError, match=f"Unsupported aggregation method chosen: {unsupported_aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'."):
            route_layer._set_aggregation_method(unsupported_aggregation)

    def test_refresh_routes_not_implemented(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        with pytest.raises(NotImplementedError, match='This method has not yet been implemented.'):
            route_layer._refresh_routes()

    def test_update_threshold(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        route_name = 'Route 1'
        new_threshold = 0.8
        route_layer.update(name=route_name, threshold=new_threshold)
        updated_route = route_layer.get(route_name)
        assert updated_route.score_threshold == new_threshold, f'Expected threshold to be updated to {new_threshold}, but got {updated_route.score_threshold}'

    def test_update_non_existent_route(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        non_existent_route = 'Non-existent Route'
        with pytest.raises(ValueError, match=f"Route '{non_existent_route}' not found. Nothing updated."):
            route_layer.update(name=non_existent_route, threshold=0.7)

    def test_update_without_parameters(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        with pytest.raises(ValueError, match="At least one of 'threshold' or 'utterances' must be provided."):
            route_layer.update(name='Route 1')

    def test_update_utterances_not_implemented(self, routes, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index)
        with pytest.raises(NotImplementedError, match='The update method cannot be used for updating utterances yet.'):
            route_layer.update(name='Route 1', utterances=['New utterance'])

def test_semantic_classify(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    classification, score = route_layer._semantic_classify([{'route': 'Route 1', 'score': 0.9}, {'route': 'Route 2', 'score': 0.1}])
    assert classification == 'Route 1'
    assert score == [0.9]

def test_semantic_classify_multiple_routes(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    classification, score = route_layer._semantic_classify([{'route': 'Route 1', 'score': 0.9}, {'route': 'Route 2', 'score': 0.1}, {'route': 'Route 1', 'score': 0.8}])
    assert classification == 'Route 1'
    assert score == [0.9, 0.8]

def test_query_no_text_dynamic_route(self, dynamic_routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=dynamic_routes, index=index)
    vector = encoder(['hello'])
    if router_cls is HybridRouter:
        sparse_vector = route_layer.sparse_encoder(['hello'])[0]
    with pytest.raises(ValueError):
        if router_cls is HybridRouter:
            route_layer(vector=vector, sparse_vector=sparse_vector)
        else:
            route_layer(vector=vector)

def test_failover_score_threshold(self, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, index=index, auto_sync='local')
    if router_cls is HybridRouter:
        assert route_layer.score_threshold == 0.3 * route_layer.alpha
    else:
        assert route_layer.score_threshold == 0.3

def test_json(self, routes, index_cls, encoder_cls, router_cls):
    temp = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
    try:
        temp_path = temp.name
        temp.close()
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.to_json(temp_path)
        assert os.path.exists(temp_path)
        route_layer_from_file = SemanticRouter.from_json(temp_path)
        assert route_layer_from_file.index is not None and route_layer_from_file._get_route_names() is not None
    finally:
        os.remove(temp_path)

def test_yaml(self, routes, index_cls, encoder_cls, router_cls):
    temp = tempfile.NamedTemporaryFile(suffix='.yaml', delete=False)
    try:
        temp_path = temp.name
        temp.close()
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
        route_layer.to_yaml(temp_path)
        assert os.path.exists(temp_path)
        route_layer_from_file = SemanticRouter.from_yaml(temp_path)
        assert route_layer_from_file.index is not None and route_layer_from_file._get_route_names() is not None
    finally:
        os.remove(temp_path)

def test_config(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    layer_config = route_layer.to_config()
    assert layer_config.routes == route_layer.routes
    route_layer_from_config = SemanticRouter.from_config(layer_config, index)
    assert route_layer_from_config._get_route_names() == route_layer._get_route_names()
    if router_cls is HybridRouter:
        pass
    else:
        assert route_layer_from_config.score_threshold == route_layer.score_threshold

def test_get_thresholds(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    if router_cls is HybridRouter:
        target = encoder.score_threshold * route_layer.alpha
        assert route_layer.get_thresholds() == {'Route 1': target, 'Route 2': target}
    else:
        assert route_layer.get_thresholds() == {'Route 1': 0.3, 'Route 2': 0.3}

def test_with_multiple_routes_passing_threshold(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    route_layer.set_threshold(threshold=0.0)
    results = route_layer(text='Hello', limit=2)
    assert len(results) == 2
    assert results[0].name == 'Route 1', f'Expected Route 1 in position 0, got {results}'
    assert results[1].name == 'Route 2', f'Expected Route 2 in position 1, got {results}'

def test_with_no_routes_passing_threshold(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    route_layer.set_threshold(threshold=1.0)
    results = route_layer(text='Hello', limit=None)
    assert results == RouteChoice()

def test_with_no_query_results(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    route_layer.set_threshold(threshold=0.5)
    results = route_layer(text='this should not be similar to anything', limit=None)
    assert results == RouteChoice()

def test_with_unrecognized_route(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')
    route_layer.set_threshold(threshold=0.5)
    query_results = [{'route': 'UnrecognizedRoute', 'score': 0.9}]
    results = route_layer._semantic_classify(query_results)
    assert results == ('UnrecognizedRoute', [0.9]), 'Semantic classify can return unrecognized routes'

def test_set_aggregation_method_with_unsupported_value(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    unsupported_aggregation = 'unsupported_aggregation_method'
    with pytest.raises(ValueError, match=f"Unsupported aggregation method chosen: {unsupported_aggregation}. Choose either 'SUM', 'MEAN', or 'MAX'."):
        route_layer._set_aggregation_method(unsupported_aggregation)

def test_refresh_routes_not_implemented(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    with pytest.raises(NotImplementedError, match='This method has not yet been implemented.'):
        route_layer._refresh_routes()

def test_update_threshold(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    route_name = 'Route 1'
    new_threshold = 0.8
    route_layer.update(name=route_name, threshold=new_threshold)
    updated_route = route_layer.get(route_name)
    assert updated_route.score_threshold == new_threshold, f'Expected threshold to be updated to {new_threshold}, but got {updated_route.score_threshold}'

def test_update_non_existent_route(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    non_existent_route = 'Non-existent Route'
    with pytest.raises(ValueError, match=f"Route '{non_existent_route}' not found. Nothing updated."):
        route_layer.update(name=non_existent_route, threshold=0.7)

def test_update_without_parameters(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    with pytest.raises(ValueError, match="At least one of 'threshold' or 'utterances' must be provided."):
        route_layer.update(name='Route 1')

def test_update_utterances_not_implemented(self, routes, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index)
    with pytest.raises(NotImplementedError, match='The update method cannot be used for updating utterances yet.'):
        route_layer.update(name='Route 1', utterances=['New utterance'])

@pytest.mark.parametrize('index_cls,encoder_cls,router_cls', [(index, encoder, router) for index in get_test_indexes() for encoder in [OpenAIEncoder] for router in get_test_routers()])
class TestLayerFit:

    def test_eval(self, routes, test_data, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_is_ready():
            assert route_layer.index.is_ready()
        check_is_ready()
        X, y = zip(*test_data)
        route_layer.evaluate(X=list(X), y=list(y), batch_size=int(len(X) / 5))

    def test_fit(self, routes, test_data, index_cls, encoder_cls, router_cls):
        if index_cls is PineconeIndex:
            return
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_is_ready():
            assert route_layer.index.is_ready()
        check_is_ready()
        X, y = zip(*test_data)
        route_layer.fit(X=list(X), y=list(y), batch_size=int(len(X) / 5))

    def test_fit_local(self, routes, test_data, index_cls, encoder_cls, router_cls):
        encoder = encoder_cls()
        index = init_index(index_cls, index_name=encoder.__class__.__name__)
        route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

        @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
        def check_is_ready():
            assert route_layer.index.is_ready()
        check_is_ready()
        X, y = zip(*test_data)
        route_layer.fit(X=list(X), y=list(y), batch_size=int(len(X) / 5), local_execution=True)

def test_eval(self, routes, test_data, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

    @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
    def check_is_ready():
        assert route_layer.index.is_ready()
    check_is_ready()
    X, y = zip(*test_data)
    route_layer.evaluate(X=list(X), y=list(y), batch_size=int(len(X) / 5))

def test_fit(self, routes, test_data, index_cls, encoder_cls, router_cls):
    if index_cls is PineconeIndex:
        return
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

    @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
    def check_is_ready():
        assert route_layer.index.is_ready()
    check_is_ready()
    X, y = zip(*test_data)
    route_layer.fit(X=list(X), y=list(y), batch_size=int(len(X) / 5))

def test_fit_local(self, routes, test_data, index_cls, encoder_cls, router_cls):
    encoder = encoder_cls()
    index = init_index(index_cls, index_name=encoder.__class__.__name__)
    route_layer = router_cls(encoder=encoder, routes=routes, index=index, auto_sync='local')

    @retry(max_retries=RETRY_COUNT, delay=PINECONE_SLEEP)
    def check_is_ready():
        assert route_layer.index.is_ready()
    check_is_ready()
    X, y = zip(*test_data)
    route_layer.fit(X=list(X), y=list(y), batch_size=int(len(X) / 5), local_execution=True)

class TestOpenAIEncoder:

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_init_success(self, openai_encoder):
        assert openai_encoder._client is not None

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_dims(self, openai_encoder):
        embeddings = openai_encoder(['test document'])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1536

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_truncation(self, openai_encoder):
        openai_encoder([long_doc])

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_no_truncation(self, openai_encoder):
        with pytest.raises(OpenAIError) as _:
            openai_encoder([long_doc], truncate=False)

    @pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
    def test_openai_encoder_call_uninitialized_client(self, openai_encoder):
        openai_encoder._client = None
        with pytest.raises(ValueError) as e:
            openai_encoder(['test document'])
        assert 'OpenAI client is not initialized.' in str(e.value)

@pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
def test_openai_encoder_init_success(self, openai_encoder):
    assert openai_encoder._client is not None

@pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
def test_openai_encoder_dims(self, openai_encoder):
    embeddings = openai_encoder(['test document'])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1536

@pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
def test_openai_encoder_call_truncation(self, openai_encoder):
    openai_encoder([long_doc])

@pytest.mark.skipif(not has_valid_openai_api_key(), reason='OpenAI API key required')
def test_openai_encoder_call_no_truncation(self, openai_encoder):
    with pytest.raises(OpenAIError) as _:
        openai_encoder([long_doc], truncate=False)

@pytest.fixture
@pytest.mark.skipif(os.environ.get('RUN_HF_TESTS') is None, reason='Set RUN_HF_TESTS=1 to run. This test downloads models from Hugging Face which can time out in CI.')
def bm25_encoder():
    sparse_encoder = BM25Encoder(use_default_params=True)
    sparse_encoder.fit([Route(name='test_route', utterances=UTTERANCES)])
    return sparse_encoder

