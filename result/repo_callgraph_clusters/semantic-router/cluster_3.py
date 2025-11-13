# Cluster 3

class Route(BaseModel):
    """A route for the semantic router.

    :param name: The name of the route.
    :type name: str
    :param utterances: The utterances of the route.
    :type utterances: Union[List[str], List[Any]]
    :param description: The description of the route.
    :type description: Optional[str]
    :param function_schemas: The function schemas of the route.
    :type function_schemas: Optional[List[Dict[str, Any]]]
    :param llm: The LLM to use.
    :type llm: Optional[BaseLLM]
    :param score_threshold: The score threshold of the route.
    :type score_threshold: Optional[float]
    :param metadata: The metadata of the route.
    :type metadata: Optional[Dict[str, Any]]
    """
    name: str
    utterances: Union[List[str], List[Any]]
    description: Optional[str] = None
    function_schemas: Optional[List[Dict[str, Any]]] = None
    llm: Optional[BaseLLM] = None
    score_threshold: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    def __call__(self, query: Optional[str]=None) -> RouteChoice:
        """Call the route. If dynamic routes have been provided the query must have been
        provided and the llm attribute must be set.

        :param query: The query to pass to the route.
        :type query: Optional[str]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if self.function_schemas:
            if not self.llm:
                raise ValueError('LLM is required for dynamic routes. Please ensure the `llm` attribute is set.')
            elif query is None:
                raise ValueError('Query is required for dynamic routes. Please ensure the `query` argument is passed.')
            try:
                extracted_inputs = self.llm.extract_function_inputs(query=query, function_schemas=self.function_schemas)
                func_call = extracted_inputs
            except Exception:
                logger.error('Error extracting function inputs', exc_info=True)
                func_call = None
        else:
            func_call = None
        return RouteChoice(name=self.name, function_call=func_call)

    async def acall(self, query: Optional[str]=None) -> RouteChoice:
        """Asynchronous call the route. If dynamic routes have been provided the query
        must have been provided and the llm attribute must be set.

        :param query: The query to pass to the route.
        :type query: Optional[str]
        :return: The route choice.
        :rtype: RouteChoice
        """
        if self.function_schemas:
            if not self.llm:
                raise ValueError('LLM is required for dynamic routes. Please ensure the `llm` attribute is set.')
            elif query is None:
                raise ValueError('Query is required for dynamic routes. Please ensure the `query` argument is passed.')
            try:
                extracted_inputs = await self.llm.async_extract_function_inputs(query=query, function_schemas=self.function_schemas)
                func_call = extracted_inputs
            except Exception:
                logger.error('Error extracting function inputs', exc_info=True)
                func_call = None
        else:
            func_call = None
        return RouteChoice(name=self.name, function_call=func_call)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the route to a dictionary.

        :return: The dictionary representation of the route.
        :rtype: Dict[str, Any]
        """
        data = self.dict()
        if self.llm is not None:
            data['llm'] = {'module': self.llm.__module__, 'class': self.llm.__class__.__name__, 'model': self.llm.name}
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create a Route object from a dictionary.

        :param data: The dictionary to create the route from.
        :type data: Dict[str, Any]
        :return: The created route.
        :rtype: Route
        """
        return cls(**data)

    @classmethod
    def from_dynamic_route(cls, llm: BaseLLM, entities: List[Union[BaseModel, Callable]], route_name: str):
        """Generate a dynamic Route object from a list of functions or Pydantic models
        using an LLM.

        :param llm: The LLM to use.
        :type llm: BaseLLM
        :param entities: The entities to use.
        :type entities: List[Union[BaseModel, Callable]]
        :param route_name: The name of the route.
        """
        schemas = function_call.get_schema_list(items=entities)
        dynamic_route = cls._generate_dynamic_route(llm=llm, function_schemas=schemas, route_name=route_name)
        dynamic_route.function_schemas = schemas
        return dynamic_route

    @classmethod
    def _parse_route_config(cls, config: str) -> str:
        """Parse the route config from the LLM output using regex. Expects the output
        content to be wrapped in <config></config> tags.

        :param config: The LLM output.
        :type config: str
        :return: The parsed route config.
        :rtype: str
        """
        config_pattern = '<config>(.*?)</config>'
        match = re.search(config_pattern, config, re.DOTALL)
        if match:
            config_content = match.group(1).strip()
            return config_content
        else:
            raise ValueError('No <config></config> tags found in the output.')

    @classmethod
    def _generate_dynamic_route(cls, llm: BaseLLM, function_schemas: List[Dict[str, Any]], route_name: str):
        """Generate a dynamic Route object from a list of function schemas using an LLM.

        :param llm: The LLM to use.
        :type llm: BaseLLM
        :param function_schemas: The function schemas to use.
        :type function_schemas: List[Dict[str, Any]]
        :param route_name: The name of the route.
        """
        formatted_schemas = '\n'.join([json.dumps(schema, indent=4) for schema in function_schemas])
        prompt = f'\n        You are tasked to generate a single JSON configuration for multiple function schemas. \n        Each function schema should contribute five example utterances. \n        Please follow the template below, no other tokens allowed:\n\n        <config>\n        {{\n            "name": "{route_name}",\n            "utterances": [\n                "<example_utterance_1>",\n                "<example_utterance_2>",\n                "<example_utterance_3>",\n                "<example_utterance_4>",\n                "<example_utterance_5>"]\n        }}\n        </config>\n\n        Only include the "name" and "utterances" keys in your answer.\n        The "name" should match the provided route name and the "utterances"\n        should comprise a list of 5 example phrases for each function schema that could be used to invoke\n        the functions. Use real values instead of placeholders.\n\n        Input schemas:\n        {formatted_schemas}\n        '
        llm_input = [Message(role='user', content=prompt)]
        output = llm(llm_input)
        if not output:
            raise Exception('No output generated for dynamic route')
        route_config = cls._parse_route_config(config=output)
        if is_valid(route_config):
            route_config_dict = json.loads(route_config)
            route_config_dict['llm'] = llm
            return Route.from_dict(route_config_dict)
        raise Exception('No config generated')

@classmethod
def from_dict(cls, data: Dict[str, Any]):
    """Create a Route object from a dictionary.

        :param data: The dictionary to create the route from.
        :type data: Dict[str, Any]
        :return: The created route.
        :rtype: Route
        """
    return cls(**data)

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

class BaseTokenizer:
    """Abstract Tokenizer class"""

    @property
    def vocab_size(self) -> int:
        """Returns the vocabulary size of the tokenizer

        :return: Vocabulary size of tokenizer
        :rtype: int
        """
        raise NotImplementedError

    @property
    def config(self) -> dict:
        """The tokenizer config

        :return: dictionary of tokenizer config
        :rtype: dict
        """
        raise NotImplementedError

    def save(self, path: str | Path) -> None:
        """Saves the configuration of the tokenizer

        Saves these files:
        - tokenizer.json: saved configuration of the tokenizer

        :param path: Path to save the tokenizer to
        :type path: str, :class:`pathlib.Path`
        """
        if isinstance(path, str):
            path = Path(path)
        with open(path, 'w') as fp:
            json.dump(self.config, fp)

    @classmethod
    def load(cls, path: str | Path) -> 'BaseTokenizer':
        """Returns a :class:`bm25_engine.tokenizer.BaseTokenizer` object from saved configuration

        Requires these files:
        - tokenizer.json: saved configuration of the tokenizer

        :param path: Path to load the tokenizer from
        :type path: str, :class:`pathlib.Path`
        :returns: Configured BaseTokenizer
        :rtype: BaseTokenizer
        """
        if isinstance(path, str):
            path = Path(path)
        with open(path) as fp:
            config = json.load(fp)
        return cls(**config)

    def tokenize(self, texts: str | list[str], pad: bool=True) -> np.ndarray:
        raise NotImplementedError

def save(self, path: str | Path) -> None:
    """Saves the configuration of the tokenizer

        Saves these files:
        - tokenizer.json: saved configuration of the tokenizer

        :param path: Path to save the tokenizer to
        :type path: str, :class:`pathlib.Path`
        """
    if isinstance(path, str):
        path = Path(path)
    with open(path, 'w') as fp:
        json.dump(self.config, fp)

@classmethod
def load(cls, path: str | Path) -> 'BaseTokenizer':
    """Returns a :class:`bm25_engine.tokenizer.BaseTokenizer` object from saved configuration

        Requires these files:
        - tokenizer.json: saved configuration of the tokenizer

        :param path: Path to load the tokenizer from
        :type path: str, :class:`pathlib.Path`
        :returns: Configured BaseTokenizer
        :rtype: BaseTokenizer
        """
    if isinstance(path, str):
        path = Path(path)
    with open(path) as fp:
        config = json.load(fp)
    return cls(**config)

class LlamaCppLLM(BaseLLM):
    """LLM for LlamaCPP. Enables fully local LLM use, helpful for local implementation of
    dynamic routes.
    """
    llm: Any
    grammar: Optional[Any] = None
    _llama_cpp: Any = PrivateAttr()

    def __init__(self, llm: Any, name: str='llama.cpp', temperature: float=0.2, max_tokens: Optional[int]=200, grammar: Optional[Any]=None):
        """Initialize the LlamaCPPLLM.

        :param llm: The LLM to use.
        :type llm: Any
        :param name: The name of the LLM.
        :type name: str
        :param temperature: The temperature of the LLM.
        :type temperature: float
        :param max_tokens: The maximum number of tokens to generate.
        :type max_tokens: Optional[int]
        :param grammar: The grammar to use.
        :type grammar: Optional[Any]
        """
        super().__init__(name=name, llm=llm, temperature=temperature, max_tokens=max_tokens, grammar=grammar)
        try:
            import llama_cpp
        except ImportError:
            raise ImportError("Please install LlamaCPP to use Llama CPP llm. You can install it with: `pip install 'semantic-router[local]'`")
        self._llama_cpp = llama_cpp
        self.llm = llm
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.grammar = grammar

    def __call__(self, messages: List[Message]) -> str:
        """Call the LlamaCPPLLM.

        :param messages: The messages to pass to the LlamaCPPLLM.
        :type messages: List[Message]
        :return: The response from the LlamaCPPLLM.
        :rtype: str
        """
        try:
            completion = self.llm.create_chat_completion(messages=[m.to_llamacpp() for m in messages], temperature=self.temperature, max_tokens=self.max_tokens, grammar=self.grammar, stream=False)
            assert isinstance(completion, dict)
            output = completion['choices'][0]['message']['content']
            if not output:
                raise Exception('No output generated')
            return output
        except Exception as e:
            logger.error(f'LLM error: {e}')
            raise

    @contextmanager
    def _grammar(self):
        """Context manager for the grammar.

        :return: The grammar.
        :rtype: Any
        """
        grammar_path = Path(__file__).parent.joinpath('grammars', 'json.gbnf')
        assert grammar_path.exists(), f'{grammar_path}\ndoes not exist'
        try:
            self.grammar = self._llama_cpp.LlamaGrammar.from_file(grammar_path)
            yield
        finally:
            self.grammar = None

    def extract_function_inputs(self, query: str, function_schemas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract the function inputs from the query.

        :param query: The query to extract the function inputs from.
        :type query: str
        :param function_schemas: The function schemas to extract the function inputs from.
        :type function_schemas: List[Dict[str, Any]]
        :return: The function inputs.
        :rtype: List[Dict[str, Any]]
        """
        with self._grammar():
            return super().extract_function_inputs(query=query, function_schemas=function_schemas)

@contextmanager
def _grammar(self):
    """Context manager for the grammar.

        :return: The grammar.
        :rtype: Any
        """
    grammar_path = Path(__file__).parent.joinpath('grammars', 'json.gbnf')
    assert grammar_path.exists(), f'{grammar_path}\ndoes not exist'
    try:
        self.grammar = self._llama_cpp.LlamaGrammar.from_file(grammar_path)
        yield
    finally:
        self.grammar = None

class FunctionSchema:
    """Class that consumes a function and can return a schema required by
    different LLMs for function calling.
    """
    name: str = Field(description='The name of the function')
    description: str = Field(description='The description of the function')
    signature: str = Field(description='The signature of the function')
    output: str = Field(description='The output of the function')
    parameters: List[Parameter] = Field(description='The parameters of the function')

    def __init__(self, function: Union[Callable, BaseModel]):
        """Initialize the FunctionSchema.

        :param function: The function to consume.
        :type function: Union[Callable, BaseModel]
        """
        self.function = function
        if callable(function):
            self._process_function(function)
        elif isinstance(function, BaseModel):
            raise NotImplementedError('Pydantic BaseModel not implemented yet.')
        else:
            raise TypeError('Function must be a Callable or BaseModel')

    def _process_function(self, function: Callable):
        """Process the function to get the name, description, signature, and output.

        :param function: The function to process.
        :type function: Callable
        """
        self.name = function.__name__
        self.description = str(inspect.getdoc(function))
        self.signature = str(inspect.signature(function))
        self.output = str(inspect.signature(function).return_annotation)
        parameters = []
        for param in inspect.signature(function).parameters.values():
            parameters.append(Parameter(name=param.name, type=param.annotation.__name__, default=param.default, required=False if param.default is param.empty else True))
        self.parameters = parameters

    def to_ollama(self):
        """Convert the FunctionSchema to an Ollama-compatible function schema dictionary.

        :return: The function schema in dictionary format.
        :rtype: Dict[str, Any]
        """
        schema_dict = {'type': 'function', 'function': {'name': self.name, 'description': self.description, 'parameters': {'type': 'object', 'properties': {param.name: {'description': param.description if isinstance(param.description, str) else None, 'type': self._ollama_type_mapping(param.type)} for param in self.parameters}, 'required': [param.name for param in self.parameters if param.required]}}}
        return schema_dict

    def _ollama_type_mapping(self, param_type: str) -> str:
        """Map the parameter type to an Ollama-compatible type.

        :param param_type: The type of the parameter.
        :type param_type: str
        :return: The Ollama-compatible type.
        :rtype: str
        """
        if param_type == 'int':
            return 'number'
        elif param_type == 'float':
            return 'number'
        elif param_type == 'str':
            return 'string'
        elif param_type == 'bool':
            return 'boolean'
        else:
            return 'object'

def __init__(self, function: Union[Callable, BaseModel]):
    """Initialize the FunctionSchema.

        :param function: The function to consume.
        :type function: Union[Callable, BaseModel]
        """
    self.function = function
    if callable(function):
        self._process_function(function)
    elif isinstance(function, BaseModel):
        raise NotImplementedError('Pydantic BaseModel not implemented yet.')
    else:
        raise TypeError('Function must be a Callable or BaseModel')

def to_ollama(self):
    """Convert the FunctionSchema to an Ollama-compatible function schema dictionary.

        :return: The function schema in dictionary format.
        :rtype: Dict[str, Any]
        """
    schema_dict = {'type': 'function', 'function': {'name': self.name, 'description': self.description, 'parameters': {'type': 'object', 'properties': {param.name: {'description': param.description if isinstance(param.description, str) else None, 'type': self._ollama_type_mapping(param.type)} for param in self.parameters}, 'required': [param.name for param in self.parameters if param.required]}}}
    return schema_dict

class PostgresIndex(BaseIndex):
    """Postgres implementation of Index."""
    connection_string: Optional[str] = None
    index_prefix: str = 'semantic_router_'
    index_name: str = 'index'
    metric: Metric = Metric.COSINE
    namespace: Optional[str] = ''
    conn: Optional['psycopg.Connection'] = None
    async_conn: Optional['psycopg.AsyncConnection'] = None
    type: str = 'postgres'
    index_type: IndexType = IndexType.FLAT
    init_async_index: bool = False

    def __init__(self, connection_string: Optional[str]=None, index_prefix: str='semantic_router_', index_name: str='index', metric: Metric=Metric.COSINE, namespace: Optional[str]='', dimensions: int | None=None, init_async_index: bool=False):
        """Initializes the Postgres index with the specified parameters.

        :param connection_string: The connection string for the PostgreSQL database.
        :type connection_string: Optional[str]
        :param index_prefix: The prefix for the index table name.
        :type index_prefix: str
        :param index_name: The name of the index table.
        :type index_name: str
        :param dimensions: The number of dimensions for the vectors.
        :type dimensions: int
        :param metric: The metric used for vector comparisons.
        :type metric: Metric
        :param namespace: An optional namespace for the index.
        :type namespace: Optional[str]
        :param init_async_index: Whether to initialize the index asynchronously.
        :type init_async_index: bool
        """
        if not _psycopg_installed:
            raise ImportError("Please install psycopg to use PostgresIndex. You can install it with: `pip install 'semantic-router[postgres]'`")
        super().__init__()
        if index_prefix:
            logger.warning('`index_prefix` is deprecated and will be removed in 0.2.0')
        if connection_string or (connection_string := os.getenv('POSTGRES_CONNECTION_STRING')):
            pass
        else:
            required_env_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB']
            missing = [var for var in required_env_vars if not os.getenv(var)]
            if missing:
                raise ValueError(f'Missing required environment variables for Postgres connection: {', '.join(missing)}')
            connection_string = f'postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}'
        self.connection_string = connection_string
        self.index = self
        self.index_prefix = index_prefix
        self.index_name = index_name
        self.dimensions = dimensions
        self.metric = metric
        self.namespace = namespace
        self.init_async_index = init_async_index
        self.conn = None
        self.async_conn = None

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
        if not self.connection_string:
            raise ValueError('No `self.connection_string` attribute set')
        self.conn = psycopg.connect(conninfo=self.connection_string)
        if not self.has_connection():
            raise ValueError('Index has not established a connection to Postgres')
        dimensions_given = self.dimensions is not None
        if not dimensions_given:
            raise ValueError('Dimensions are required for PostgresIndex')
        table_name = self._get_table_name()
        if not self._check_embeddings_dimensions():
            raise ValueError(f'The length of the vector embeddings in the existing table {table_name} does not match the expected dimensions of {self.dimensions}.')
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"\n                    CREATE EXTENSION IF NOT EXISTS vector;\n                    CREATE TABLE IF NOT EXISTS {table_name} (\n                        id VARCHAR(255) PRIMARY KEY,\n                        route VARCHAR(255),\n                        utterance TEXT,\n                        vector VECTOR({self.dimensions})\n                    );\n                    COMMENT ON COLUMN {table_name}.vector IS '{self.dimensions}';\n                    ")
                self.conn.commit()
            self._create_route_index()
            self._create_index()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise
        return self

    async def _init_async_index(self, force_create: bool=False) -> Union[Any, None]:
        logging.warning('[DEBUG] Entering _init_async_index for PostgresIndex')
        if self.async_conn is None:
            if not self.connection_string:
                raise ValueError('No `self.connection_string` attribute set')
            logging.warning(f'[DEBUG] Connecting async to Postgres with: {self.connection_string}')
            self.async_conn = await psycopg.AsyncConnection.connect(self.connection_string)
            logging.warning(f'[DEBUG] Async connection established: {self.async_conn}')
        if self.dimensions is None and (not force_create):
            logging.warning('[DEBUG] No dimensions and not force_create, returning None from _init_async_index')
            return None
        if self.dimensions is None:
            raise ValueError('Dimensions are required for PostgresIndex')
        table_name = self._get_table_name()
        logging.warning(f'[DEBUG] Table name for async index: {table_name}')
        if not await self._async_check_embeddings_dimensions():
            raise ValueError(f'The length of the vector embeddings in the existing table {table_name} does not match the expected dimensions of {self.dimensions}.')
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established a connection to async Postgres')
        try:
            async with self.async_conn.cursor() as cur:
                logging.warning(f'[DEBUG] Creating extension/table for {table_name}')
                await cur.execute(f"\n                    CREATE EXTENSION IF NOT EXISTS vector;\n                    CREATE TABLE IF NOT EXISTS {table_name} (\n                        id VARCHAR(255) PRIMARY KEY,\n                        route VARCHAR(255),\n                        utterance TEXT,\n                        vector VECTOR({self.dimensions})\n                    );\n                    COMMENT ON COLUMN {table_name}.vector IS '{self.dimensions}';\n                    ")
                await self.async_conn.commit()
                await self._async_create_route_index()
                await self._async_create_index()
                logging.warning(f'[DEBUG] Finished async index/table creation for {table_name}')
        except Exception as e:
            logging.warning(f'[DEBUG] Exception in _init_async_index: {e}')
            await self.async_conn.rollback()
            raise e
        logging.warning('[DEBUG] Exiting _init_async_index for PostgresIndex')
        return self

    def _get_table_name(self) -> str:
        """
        Returns the name of the table for the index.

        :return: The table name.
        :rtype: str
        """
        return f'{self.index_prefix}{self.index_name}'

    def _get_metric_operator(self) -> str:
        """Returns the PostgreSQL operator for the specified metric.

        :return: The PostgreSQL operator.
        :rtype: str
        """
        return MetricPgVecOperatorMap[self.metric.value].value

    def _get_score_query(self, embeddings_str: str) -> str:
        """Creates the select statement required to return the embeddings distance.

        :param embeddings_str: The string representation of the embeddings.
        :type embeddings_str: str
        :return: The SQL query part for scoring.
        :rtype: str
        """
        operator = self._get_metric_operator()
        if self.metric == Metric.COSINE:
            return f'1 - (vector {operator} {embeddings_str}) AS score'
        elif self.metric == Metric.DOTPRODUCT:
            return f'(vector {operator} {embeddings_str}) * -1 AS score'
        elif self.metric == Metric.EUCLIDEAN:
            return f'vector {operator} {embeddings_str} AS score'
        elif self.metric == Metric.MANHATTAN:
            return f'vector {operator} {embeddings_str} AS score'
        else:
            raise ValueError(f'Unsupported metric: {self.metric}')

    def _get_vector_operator(self) -> str:
        if self.metric == Metric.COSINE:
            return 'vector_cosine_ops'
        elif self.metric == Metric.DOTPRODUCT:
            return 'vector_ip_ops'
        elif self.metric == Metric.EUCLIDEAN:
            return 'vector_l2_ops'
        elif self.metric == Metric.MANHATTAN:
            return 'vector_l1_ops'
        else:
            raise ValueError(f'Unsupported metric: {self.metric}')

    def _create_route_index(self) -> None:
        """Creates a index on the route column."""
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute(f'CREATE INDEX IF NOT EXISTS {table_name}_route_idx ON {table_name} USING btree (route);')
                self.conn.commit()
        except psycopg.errors.DuplicateTable:
            if self.conn is not None:
                self.conn.rollback()
            pass
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_create_route_index(self) -> None:
        """Asynchronously creates an index on the route column."""
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established a connection to async Postgres')
        try:
            async with self.async_conn.cursor() as cur:
                await cur.execute(f'CREATE INDEX IF NOT EXISTS {table_name}_route_idx ON {table_name} USING btree (route);')
            await self.async_conn.commit()
        except psycopg.errors.DuplicateTable:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            pass
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    def _create_index(self) -> None:
        """Creates an index on the vector column based on index_type."""
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        opclass = self._get_vector_operator()
        try:
            with self.conn.cursor() as cur:
                if self.index_type == IndexType.HNSW:
                    cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING hnsw (vector {opclass});\n                        ')
                elif self.index_type == IndexType.IVFFLAT:
                    cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 100);\n                        ')
                elif self.index_type == IndexType.FLAT:
                    cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 1);\n                        ')
                self.conn.commit()
        except psycopg.errors.DuplicateTable:
            if self.conn is not None:
                self.conn.rollback()
            pass
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_create_index(self) -> None:
        """Asynchronously creates an index on the vector column based on index_type."""
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established a connection to async Postgres')
        opclass = self._get_vector_operator()
        try:
            async with self.async_conn.cursor() as cur:
                if self.index_type == IndexType.HNSW:
                    await cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING hnsw (vector {opclass});\n                        ')
                elif self.index_type == IndexType.IVFFLAT:
                    await cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 100);\n                        ')
                elif self.index_type == IndexType.FLAT:
                    await cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 1);\n                        ')
            await self.async_conn.commit()
        except psycopg.errors.DuplicateTable:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            pass
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    @deprecated('Use _init_index or sync methods such as `auto_sync` (read more https://docs.aurelio.ai/semantic-router/user-guide/features/sync). This method will be removed in 0.2.0')
    def setup_index(self) -> None:
        """Sets up the index by creating the table and vector extension if they do not exist.

        :raises ValueError: If the existing table's vector dimensions do not match the expected dimensions.
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not self._check_embeddings_dimensions():
            raise ValueError(f'The length of the vector embeddings in the existing table {table_name} does not match the expected dimensions of {self.dimensions}.')
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        with self.conn.cursor() as cur:
            cur.execute(f"\n                CREATE EXTENSION IF NOT EXISTS vector;\n                CREATE TABLE IF NOT EXISTS {table_name} (\n                    id VARCHAR(255) PRIMARY KEY,\n                    route VARCHAR(255),\n                    utterance TEXT,\n                    vector VECTOR({self.dimensions})\n                );\n                COMMENT ON COLUMN {table_name}.vector IS '{self.dimensions}';\n                ")
            self.conn.commit()
        self._create_route_index()
        self._create_index()

    def _check_embeddings_dimensions(self) -> bool:
        """Checks if the length of the vector embeddings in the table matches the expected
        dimensions, or if no table exists.

        :return: True if the dimensions match or the table does not exist, False otherwise.
        :rtype: bool
        :raises ValueError: If the vector column comment does not contain a valid integer.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}');")
                fetch_result = cur.fetchone()
                exists = fetch_result[0] if fetch_result else None
                if not exists:
                    return True
                cur.execute(f"SELECT col_description('{table_name}'::regclass, attnum) AS column_comment\n                        FROM pg_attribute\n                        WHERE attrelid = '{table_name}'::regclass\n                        AND attname='vector'")
                result = cur.fetchone()
                dimension_comment = result[0] if result else None
                if dimension_comment:
                    try:
                        vector_length = int(dimension_comment.split()[-1])
                        return vector_length == self.dimensions
                    except ValueError:
                        raise ValueError("The 'vector' column comment does not contain a valid integer.")
                else:
                    raise ValueError("No comment found for the 'vector' column.")
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_check_embeddings_dimensions(self) -> bool:
        """Asynchronously checks if the vector embedding dimensions match the expected ones.

        Returns True if dimensions match or table does not exist, False otherwise.

        :return: True if the dimensions match or the table does not exist, False otherwise.
        :rtype: bool
        :raises ValueError: If the vector column comment does not contain a valid integer.
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established a connection to async Postgres')
        try:
            async with self.async_conn.cursor() as cur:
                await cur.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}');")
                fetch_result = await cur.fetchone()
                exists = fetch_result[0] if fetch_result else None
                if not exists:
                    return True
                await cur.execute(f"SELECT col_description('{table_name}'::regclass, attnum) AS column_comment\n                        FROM pg_attribute\n                        WHERE attrelid = '{table_name}'::regclass\n                        AND attname = 'vector';")
                result = await cur.fetchone()
                dimension_comment = result[0] if result else None
                if dimension_comment:
                    try:
                        vector_length = int(dimension_comment.split()[-1])
                        return vector_length == self.dimensions
                    except ValueError:
                        raise ValueError("The 'vector' column comment does not contain a valid integer.")
                else:
                    raise ValueError("No comment found for the 'vector' column.")
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs) -> None:
        """Adds records to the index.

        :param embeddings: A list of vector embeddings to add.
        :type embeddings: List[List[float]]
        :param routes: A list of route names corresponding to the embeddings.
        :type routes: List[str]
        :param utterances: A list of utterances corresponding to the embeddings.
        :type utterances: List[Any]
        :param function_schemas: A list of function schemas corresponding to the embeddings.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: A list of metadata corresponding to the embeddings.
        :type metadata_list: List[Dict[str, Any]]
        :raises ValueError: If the vector embeddings being added do not match the expected dimensions.
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        new_embeddings_length = len(embeddings[0])
        if new_embeddings_length != self.dimensions:
            raise ValueError(f'The vector embeddings being added are of length {new_embeddings_length}, which does not match the expected dimensions of {self.dimensions}.')
        records = [PostgresIndexRecord(vector=vector, route=route, utterance=utterance) for vector, route, utterance in zip(embeddings, routes, utterances)]
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.executemany(f'INSERT INTO {table_name} (id, route, utterance, vector) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING', [(record.id, record.route, record.utterance, record.vector) for record in records])
                self.conn.commit()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def aadd(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], batch_size: int=100, **kwargs) -> None:
        """
        Asynchronously adds records to the index in batches.

        :param embeddings: A list of vector embeddings to add.
        :param routes: A list of route names corresponding to the embeddings.
        :param utterances: A list of utterances corresponding to the embeddings.
        :param function_schemas: (Optional) List of function schemas.
        :param metadata_list: (Optional) List of metadata dictionaries.
        :param batch_size: Number of records per batch insert.
        :raises ValueError: If the vector embeddings don't match expected dimensions.
        :raises TypeError: If connection is not an async Postgres connection.
        """
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        table_name = self._get_table_name()
        new_embeddings_length = len(embeddings[0])
        if new_embeddings_length != self.dimensions:
            raise ValueError(f'The vector embeddings being added are of length {new_embeddings_length}, which does not match the expected dimensions of {self.dimensions}.')
        try:
            async with self.async_conn.cursor() as cur:
                for i in range(0, len(embeddings), batch_size):
                    batch_embeddings = embeddings[i:i + batch_size]
                    batch_routes = routes[i:i + batch_size]
                    batch_utterances = utterances[i:i + batch_size]
                    values = [(str(uuid.uuid4()), route, utterance, vector) for route, utterance, vector in zip(batch_routes, batch_utterances, batch_embeddings)]
                    await cur.executemany(f'INSERT INTO {table_name} (id, route, utterance, vector) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING', values)
                await self.async_conn.commit()
        except Exception:
            await self.async_conn.rollback()
            raise

    def delete(self, route_name: str) -> None:
        """Deletes records with the specified route name.

        :param route_name: The name of the route to delete records for.
        :type route_name: str
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table_name} WHERE route = '{route_name}'")
                self.conn.commit()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def adelete(self, route_name: str) -> list[str]:
        """Asynchronously delete specified route from index if it exists. Returns the IDs
        of the vectors deleted.

        :param route_name: Name of the route to delete.
        :type route_name: str
        :return: List of IDs of the vectors deleted.
        :rtype: list[str]
        """
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        table_name = self._get_table_name()
        try:
            async with self.async_conn.cursor() as cur:
                await cur.execute(f'SELECT id FROM {table_name} WHERE route = %s', (route_name,))
                result = await cur.fetchall()
                deleted_ids = [row[0] for row in result]
                await cur.execute(f'DELETE FROM {table_name} WHERE route = %s', (route_name,))
                await self.async_conn.commit()
                return deleted_ids
        except Exception:
            await self.async_conn.rollback()
            raise

    def describe(self) -> IndexConfig:
        """Describes the index by returning its type, dimensions, and total vector count.

        :return: An IndexConfig object containing the index's type, dimensions, and total vector count.
        :rtype: IndexConfig
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.Connection):
            logger.warning('Index has not established a connection to Postgres')
            return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=0)
        try:
            with self.async_conn.cursor() as cur:
                cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                result = cur.fetchone()
                count = result[0] if result is not None else 0
                return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=count)
        except Exception:
            if self.async_conn is not None:
                self.async_conn.rollback()
            raise

    def is_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return isinstance(self.conn, psycopg.Connection)

    async def ais_ready(self) -> bool:
        """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
        return isinstance(self.async_conn, psycopg.AsyncConnection)

    def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Searches the index for the query vector and returns the top_k results.

        :param vector: The query vector.
        :type vector: np.ndarray
        :param top_k: The number of top results to return.
        :type top_k: int
        :param route_filter: Optional list of routes to filter the results by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: Optional sparse vector to filter the results by.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the scores and routes of the top_k results.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                filter_query = f' AND route = ANY(ARRAY{route_filter})' if route_filter else ''
                vector_str = f"'[{','.join(map(str, vector.tolist()))}]'"
                score_query = self._get_score_query(vector_str)
                operator = self._get_metric_operator()
                query = f'SELECT route, {score_query} FROM {table_name} WHERE true{filter_query} ORDER BY vector {operator} {vector_str} LIMIT {top_k}'
                cur.execute(query)
                results = cur.fetchall()
                return (np.array([result[1] for result in results]), [result[0] for result in results])
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def aquery(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
        """Asynchronously search the index for the query vector and return the top_k results.

        :param vector: The query vector to search for.
        :type vector: np.ndarray
        :param top_k: The number of top results to return, defaults to 5.
        :type top_k: int, optional
        :param route_filter: A list of route names to filter the search results, defaults to None.
        :type route_filter: Optional[List[str]], optional
        :param sparse_vector: An optional sparse vector to include in the query.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing an array of scores and a list of route names.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        try:
            async with self.async_conn.cursor() as cur:
                filter_query = f' AND route = ANY(ARRAY{route_filter})' if route_filter else ''
                vector_str = f"'[{','.join(map(str, vector.tolist()))}]'"
                score_query = self._get_score_query(vector_str)
                operator = self._get_metric_operator()
                query = f'SELECT route, {score_query} FROM {table_name} WHERE true{filter_query} ORDER BY vector {operator} {vector_str} LIMIT {top_k}'
                await cur.execute(query)
                results = await cur.fetchall()
                return (np.array([result[1] for result in results]), [result[0] for result in results])
        except Exception:
            await self.async_conn.rollback()
            raise

    def _get_route_ids(self, route_name: str):
        """Retrieves all vector IDs for a specific route.

        :param route_name: The name of the route to retrieve IDs for.
        :type route_name: str
        :return: A list of vector IDs.
        :rtype: List[str]
        """
        clean_route = clean_route_name(route_name)
        try:
            ids, _ = self._get_all(route_name=f'{clean_route}')
            return ids
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_get_route_ids(self, route_name: str) -> list[str]:
        """Get the IDs of the routes in the index asynchronously.

        :param route_name: Name of the route to get the IDs for.
        :type route_name: str
        :return: List of IDs of the routes.
        :rtype: list[str]
        """
        clean_route = clean_route_name(route_name)
        try:
            ids, _ = await self._async_get_all(route_name=f'{clean_route}')
            return ids
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    def _get_all(self, route_name: Optional[str]=None, include_metadata: bool=False):
        """Retrieves all vector IDs and optionally metadata from the Postgres index.

        :param route_name: Optional route name to filter the results by.
        :type route_name: Optional[str]
        :param include_metadata: Whether to include metadata in the results.
        :type include_metadata: bool
        :return: A tuple containing the list of vector IDs and optionally metadata.
        :rtype: Tuple[List[str], List[Dict]]
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            query = 'SELECT id'
            if include_metadata:
                query += ', route, utterance'
            query += f' FROM {table_name}'
            if route_name:
                query += f" WHERE route LIKE '{route_name}%'"
            all_vector_ids = []
            metadata = []
            with self.conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                for row in results:
                    all_vector_ids.append(row[0])
                    if include_metadata:
                        metadata.append({'sr_route': row[1], 'sr_utterance': row[2]})
            return (all_vector_ids, metadata)
        except psycopg.errors.UndefinedTable:
            if self.conn is not None:
                self.conn.rollback()
            return ([], [])
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_get_all(self, route_name: Optional[str]=None, include_metadata: bool=False) -> Tuple[List[str], List[Dict]]:
        """Retrieves all vector IDs and optionally metadata from the Postgres index asynchronously.

        :param route_name: Optional route name to filter the results by.
        :type route_name: Optional[str]
        :param include_metadata: Whether to include metadata in the results.
        :type include_metadata: bool
        :return: A tuple containing the list of vector IDs and optionally metadata.
        :rtype: Tuple[List[str], List[Dict]]
        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established a connection to async Postgres')
        try:
            query = 'SELECT id'
            if include_metadata:
                query += ', route, utterance'
            query += f' FROM {table_name}'
            if route_name:
                query += f" WHERE route LIKE '{route_name}%'"
            all_vector_ids = []
            metadata = []
            async with self.async_conn.cursor() as cur:
                await cur.execute(query)
                results = await cur.fetchall()
                for row in results:
                    all_vector_ids.append(row[0])
                    if include_metadata:
                        metadata.append({'sr_route': row[1], 'sr_utterance': row[2]})
            return (all_vector_ids, metadata)
        except psycopg.errors.UndefinedTable:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            return ([], [])
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    def _remove_and_sync(self, routes_to_delete: dict):
        """
        Remove embeddings in a routes syncing process from the Postgres index.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        :return: List of (route, utterance) tuples that were removed.
        """
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        table_name = self._get_table_name()
        removed = []
        try:
            with self.conn.cursor() as cur:
                for route, utterances in routes_to_delete.items():
                    for utterance in utterances:
                        cur.execute(f'SELECT route, utterance FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
                        result = cur.fetchone()
                        if result:
                            removed.append(result)
                        cur.execute(f'DELETE FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
            self.conn.commit()
            return removed
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def _async_remove_and_sync(self, routes_to_delete: dict) -> list[tuple[str, str]]:
        """Remove specified routes from index if they exist.

        This method is asynchronous.

        :param routes_to_delete: Routes to delete.
        :type routes_to_delete: dict
        :return: List of (route, utterance) tuples that were removed.
        :rtype: list[tuple[str, str]]
        """
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        table_name = self._get_table_name()
        removed = []
        try:
            async with self.async_conn.cursor() as cur:
                for route, utterances in routes_to_delete.items():
                    for utterance in utterances:
                        await cur.execute(f'SELECT route, utterance FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
                        result = await cur.fetchone()
                        if result:
                            removed.append(result)
                        await cur.execute(f'DELETE FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
            await self.async_conn.commit()
            return removed
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    def delete_all(self):
        """Deletes all records from the Postgres index.

        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute(f'DELETE FROM {table_name}')
                self.conn.commit()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    def delete_index(self) -> None:
        """Deletes the entire table for the index.

        :raises TypeError: If the database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            raise TypeError('Index has not established a connection to Postgres')
        try:
            with self.conn.cursor() as cur:
                cur.execute('\n                    SELECT pg_terminate_backend(pid)\n                    FROM pg_stat_activity\n                    WHERE datname = current_database()\n                      AND pid <> pg_backend_pid();\n                    ')
                self.conn.commit()
                cur.execute(f'DROP TABLE IF EXISTS {table_name}')
                self.conn.commit()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise

    async def adelete_index(self) -> None:
        """Asynchronously delete the entire table for the index.

        :raises TypeError: If the async database connection is not established.
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        try:
            async with self.async_conn.cursor() as cur:
                await cur.execute(f'DROP TABLE IF EXISTS {table_name}')
                await self.async_conn.commit()
        except Exception:
            if self.async_conn is not None:
                await self.async_conn.rollback()
            raise

    async def aget_routes(self) -> list[tuple]:
        """Asynchronously get a list of route and utterance objects currently
        stored in the index.

        :return: A list of (route_name, utterance) objects.
        :rtype: List[Tuple]
        :raises TypeError: If the database connection is not established.
        """
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            raise TypeError('Index has not established an async connection to Postgres')
        return await self._async_get_routes()

    def _write_config(self, config: ConfigParameter):
        """Write the config to the index.

        :param config: The config to write to the index.
        :type config: ConfigParameter
        """
        logger.warning('No config is written for PostgresIndex.')

    def __len__(self):
        """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        """
        table_name = self._get_table_name()
        if not isinstance(self.conn, psycopg.Connection):
            logger.warning('Index has not established a connection to Postgres, returning 0')
            return 0
        with self.conn.cursor() as cur:
            try:
                cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = cur.fetchone()
                if count is None:
                    return 0
                return count[0]
            except psycopg.errors.UndefinedTable:
                logger.warning('Table does not exist, returning 0')
                return 0

    async def alen(self):
        """Async version of __len__. Returns the total number of vectors in the index.

        :return: The total number of vectors.
        :rtype: int
        """
        table_name = self._get_table_name()
        if not isinstance(self.async_conn, psycopg.AsyncConnection):
            logger.warning('Index has not established an async connection to Postgres, returning 0')
            return 0
        async with self.async_conn.cursor() as cur:
            try:
                await cur.execute(f'SELECT COUNT(*) FROM {table_name}')
                count = await cur.fetchone()
                if count is None:
                    return 0
                return count[0]
            except psycopg.errors.UndefinedTable:
                logger.warning('Table does not exist, returning 0')
                return 0

    def close(self):
        """Closes the psycopg connection if it exists."""
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception as e:
                logger.warning(f'Error closing Postgres connection: {e}')
            self.conn = None

    def __del__(self):
        self.close()

    def has_connection(self) -> bool:
        """Returns True if there is an active and valid psycopg connection, otherwise False."""
        if self.conn is None or self.conn.closed:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT 1;')
                cur.fetchone()
            return True
        except Exception:
            return False
    'Configuration for the Pydantic BaseModel.'
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

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
    if not self.connection_string:
        raise ValueError('No `self.connection_string` attribute set')
    self.conn = psycopg.connect(conninfo=self.connection_string)
    if not self.has_connection():
        raise ValueError('Index has not established a connection to Postgres')
    dimensions_given = self.dimensions is not None
    if not dimensions_given:
        raise ValueError('Dimensions are required for PostgresIndex')
    table_name = self._get_table_name()
    if not self._check_embeddings_dimensions():
        raise ValueError(f'The length of the vector embeddings in the existing table {table_name} does not match the expected dimensions of {self.dimensions}.')
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute(f"\n                    CREATE EXTENSION IF NOT EXISTS vector;\n                    CREATE TABLE IF NOT EXISTS {table_name} (\n                        id VARCHAR(255) PRIMARY KEY,\n                        route VARCHAR(255),\n                        utterance TEXT,\n                        vector VECTOR({self.dimensions})\n                    );\n                    COMMENT ON COLUMN {table_name}.vector IS '{self.dimensions}';\n                    ")
            self.conn.commit()
        self._create_route_index()
        self._create_index()
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise
    return self

def _get_score_query(self, embeddings_str: str) -> str:
    """Creates the select statement required to return the embeddings distance.

        :param embeddings_str: The string representation of the embeddings.
        :type embeddings_str: str
        :return: The SQL query part for scoring.
        :rtype: str
        """
    operator = self._get_metric_operator()
    if self.metric == Metric.COSINE:
        return f'1 - (vector {operator} {embeddings_str}) AS score'
    elif self.metric == Metric.DOTPRODUCT:
        return f'(vector {operator} {embeddings_str}) * -1 AS score'
    elif self.metric == Metric.EUCLIDEAN:
        return f'vector {operator} {embeddings_str} AS score'
    elif self.metric == Metric.MANHATTAN:
        return f'vector {operator} {embeddings_str} AS score'
    else:
        raise ValueError(f'Unsupported metric: {self.metric}')

def _create_route_index(self) -> None:
    """Creates a index on the route column."""
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute(f'CREATE INDEX IF NOT EXISTS {table_name}_route_idx ON {table_name} USING btree (route);')
            self.conn.commit()
    except psycopg.errors.DuplicateTable:
        if self.conn is not None:
            self.conn.rollback()
        pass
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def _create_index(self) -> None:
    """Creates an index on the vector column based on index_type."""
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    opclass = self._get_vector_operator()
    try:
        with self.conn.cursor() as cur:
            if self.index_type == IndexType.HNSW:
                cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING hnsw (vector {opclass});\n                        ')
            elif self.index_type == IndexType.IVFFLAT:
                cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 100);\n                        ')
            elif self.index_type == IndexType.FLAT:
                cur.execute(f'\n                        CREATE INDEX IF NOT EXISTS {table_name}_vector_idx ON {table_name} USING ivfflat (vector {opclass}) WITH (lists = 1);\n                        ')
            self.conn.commit()
    except psycopg.errors.DuplicateTable:
        if self.conn is not None:
            self.conn.rollback()
        pass
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

@deprecated('Use _init_index or sync methods such as `auto_sync` (read more https://docs.aurelio.ai/semantic-router/user-guide/features/sync). This method will be removed in 0.2.0')
def setup_index(self) -> None:
    """Sets up the index by creating the table and vector extension if they do not exist.

        :raises ValueError: If the existing table's vector dimensions do not match the expected dimensions.
        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not self._check_embeddings_dimensions():
        raise ValueError(f'The length of the vector embeddings in the existing table {table_name} does not match the expected dimensions of {self.dimensions}.')
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    with self.conn.cursor() as cur:
        cur.execute(f"\n                CREATE EXTENSION IF NOT EXISTS vector;\n                CREATE TABLE IF NOT EXISTS {table_name} (\n                    id VARCHAR(255) PRIMARY KEY,\n                    route VARCHAR(255),\n                    utterance TEXT,\n                    vector VECTOR({self.dimensions})\n                );\n                COMMENT ON COLUMN {table_name}.vector IS '{self.dimensions}';\n                ")
        self.conn.commit()
    self._create_route_index()
    self._create_index()

def _check_embeddings_dimensions(self) -> bool:
    """Checks if the length of the vector embeddings in the table matches the expected
        dimensions, or if no table exists.

        :return: True if the dimensions match or the table does not exist, False otherwise.
        :rtype: bool
        :raises ValueError: If the vector column comment does not contain a valid integer.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}');")
            fetch_result = cur.fetchone()
            exists = fetch_result[0] if fetch_result else None
            if not exists:
                return True
            cur.execute(f"SELECT col_description('{table_name}'::regclass, attnum) AS column_comment\n                        FROM pg_attribute\n                        WHERE attrelid = '{table_name}'::regclass\n                        AND attname='vector'")
            result = cur.fetchone()
            dimension_comment = result[0] if result else None
            if dimension_comment:
                try:
                    vector_length = int(dimension_comment.split()[-1])
                    return vector_length == self.dimensions
                except ValueError:
                    raise ValueError("The 'vector' column comment does not contain a valid integer.")
            else:
                raise ValueError("No comment found for the 'vector' column.")
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def add(self, embeddings: List[List[float]], routes: List[str], utterances: List[str], function_schemas: Optional[List[Dict[str, Any]]]=None, metadata_list: List[Dict[str, Any]]=[], **kwargs) -> None:
    """Adds records to the index.

        :param embeddings: A list of vector embeddings to add.
        :type embeddings: List[List[float]]
        :param routes: A list of route names corresponding to the embeddings.
        :type routes: List[str]
        :param utterances: A list of utterances corresponding to the embeddings.
        :type utterances: List[Any]
        :param function_schemas: A list of function schemas corresponding to the embeddings.
        :type function_schemas: Optional[List[Dict[str, Any]]]
        :param metadata_list: A list of metadata corresponding to the embeddings.
        :type metadata_list: List[Dict[str, Any]]
        :raises ValueError: If the vector embeddings being added do not match the expected dimensions.
        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    new_embeddings_length = len(embeddings[0])
    if new_embeddings_length != self.dimensions:
        raise ValueError(f'The vector embeddings being added are of length {new_embeddings_length}, which does not match the expected dimensions of {self.dimensions}.')
    records = [PostgresIndexRecord(vector=vector, route=route, utterance=utterance) for vector, route, utterance in zip(embeddings, routes, utterances)]
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.executemany(f'INSERT INTO {table_name} (id, route, utterance, vector) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING', [(record.id, record.route, record.utterance, record.vector) for record in records])
            self.conn.commit()
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def delete(self, route_name: str) -> None:
    """Deletes records with the specified route name.

        :param route_name: The name of the route to delete records for.
        :type route_name: str
        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table_name} WHERE route = '{route_name}'")
            self.conn.commit()
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def describe(self) -> IndexConfig:
    """Describes the index by returning its type, dimensions, and total vector count.

        :return: An IndexConfig object containing the index's type, dimensions, and total vector count.
        :rtype: IndexConfig
        """
    table_name = self._get_table_name()
    if not isinstance(self.async_conn, psycopg.Connection):
        logger.warning('Index has not established a connection to Postgres')
        return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=0)
    try:
        with self.async_conn.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM {table_name}')
            result = cur.fetchone()
            count = result[0] if result is not None else 0
            return IndexConfig(type=self.type, dimensions=self.dimensions or 0, vectors=count)
    except Exception:
        if self.async_conn is not None:
            self.async_conn.rollback()
        raise

def is_ready(self) -> bool:
    """Checks if the index is ready to be used.

        :return: True if the index is ready, False otherwise.
        :rtype: bool
        """
    return isinstance(self.conn, psycopg.Connection)

def query(self, vector: np.ndarray, top_k: int=5, route_filter: Optional[List[str]]=None, sparse_vector: dict[int, float] | SparseEmbedding | None=None) -> Tuple[np.ndarray, List[str]]:
    """Searches the index for the query vector and returns the top_k results.

        :param vector: The query vector.
        :type vector: np.ndarray
        :param top_k: The number of top results to return.
        :type top_k: int
        :param route_filter: Optional list of routes to filter the results by.
        :type route_filter: Optional[List[str]]
        :param sparse_vector: Optional sparse vector to filter the results by.
        :type sparse_vector: dict[int, float] | SparseEmbedding | None
        :return: A tuple containing the scores and routes of the top_k results.
        :rtype: Tuple[np.ndarray, List[str]]
        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            filter_query = f' AND route = ANY(ARRAY{route_filter})' if route_filter else ''
            vector_str = f"'[{','.join(map(str, vector.tolist()))}]'"
            score_query = self._get_score_query(vector_str)
            operator = self._get_metric_operator()
            query = f'SELECT route, {score_query} FROM {table_name} WHERE true{filter_query} ORDER BY vector {operator} {vector_str} LIMIT {top_k}'
            cur.execute(query)
            results = cur.fetchall()
            return (np.array([result[1] for result in results]), [result[0] for result in results])
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def _get_all(self, route_name: Optional[str]=None, include_metadata: bool=False):
    """Retrieves all vector IDs and optionally metadata from the Postgres index.

        :param route_name: Optional route name to filter the results by.
        :type route_name: Optional[str]
        :param include_metadata: Whether to include metadata in the results.
        :type include_metadata: bool
        :return: A tuple containing the list of vector IDs and optionally metadata.
        :rtype: Tuple[List[str], List[Dict]]
        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        query = 'SELECT id'
        if include_metadata:
            query += ', route, utterance'
        query += f' FROM {table_name}'
        if route_name:
            query += f" WHERE route LIKE '{route_name}%'"
        all_vector_ids = []
        metadata = []
        with self.conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            for row in results:
                all_vector_ids.append(row[0])
                if include_metadata:
                    metadata.append({'sr_route': row[1], 'sr_utterance': row[2]})
        return (all_vector_ids, metadata)
    except psycopg.errors.UndefinedTable:
        if self.conn is not None:
            self.conn.rollback()
        return ([], [])
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def _remove_and_sync(self, routes_to_delete: dict):
    """
        Remove embeddings in a routes syncing process from the Postgres index.

        :param routes_to_delete: Dictionary of routes to delete.
        :type routes_to_delete: dict
        :return: List of (route, utterance) tuples that were removed.
        """
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    table_name = self._get_table_name()
    removed = []
    try:
        with self.conn.cursor() as cur:
            for route, utterances in routes_to_delete.items():
                for utterance in utterances:
                    cur.execute(f'SELECT route, utterance FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
                    result = cur.fetchone()
                    if result:
                        removed.append(result)
                    cur.execute(f'DELETE FROM {table_name} WHERE route = %s AND utterance = %s', (route, utterance))
        self.conn.commit()
        return removed
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def delete_all(self):
    """Deletes all records from the Postgres index.

        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute(f'DELETE FROM {table_name}')
            self.conn.commit()
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def delete_index(self) -> None:
    """Deletes the entire table for the index.

        :raises TypeError: If the database connection is not established.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        raise TypeError('Index has not established a connection to Postgres')
    try:
        with self.conn.cursor() as cur:
            cur.execute('\n                    SELECT pg_terminate_backend(pid)\n                    FROM pg_stat_activity\n                    WHERE datname = current_database()\n                      AND pid <> pg_backend_pid();\n                    ')
            self.conn.commit()
            cur.execute(f'DROP TABLE IF EXISTS {table_name}')
            self.conn.commit()
    except Exception:
        if self.conn is not None:
            self.conn.rollback()
        raise

def __len__(self):
    """Returns the total number of vectors in the index. If the index is not initialized
        returns 0.

        :return: The total number of vectors.
        """
    table_name = self._get_table_name()
    if not isinstance(self.conn, psycopg.Connection):
        logger.warning('Index has not established a connection to Postgres, returning 0')
        return 0
    with self.conn.cursor() as cur:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cur.fetchone()
            if count is None:
                return 0
            return count[0]
        except psycopg.errors.UndefinedTable:
            logger.warning('Table does not exist, returning 0')
            return 0

def has_connection(self) -> bool:
    """Returns True if there is an active and valid psycopg connection, otherwise False."""
    if self.conn is None or self.conn.closed:
        return False
    try:
        with self.conn.cursor() as cur:
            cur.execute('SELECT 1;')
            cur.fetchone()
        return True
    except Exception:
        return False

def litellm_to_list(embeds: litellm.EmbeddingResponse) -> list[list[float]]:
    """Convert a LiteLLM embedding response to a list of embeddings.

    :param embeds: The LiteLLM embedding response.
    :return: A list of embeddings.
    """
    if not embeds or not isinstance(embeds, litellm.EmbeddingResponse) or (not embeds.data):
        raise ValueError('No embeddings found in LiteLLM embedding response.')
    return [x['embedding'] for x in embeds.data]

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

def _fit_validate(self, routes: List[Route]):
    if not isinstance(routes, list) or not isinstance(routes[0], Route):
        raise TypeError('`routes` parameter must be a list of Route objects.')

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

def _fit_validate(self, routes: List[Route]):
    if not isinstance(routes, list) or not isinstance(routes[0], Route):
        raise TypeError('`routes` parameter must be a list of Route objects.')

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

def test_vocab_size(self, tokenizer):
    assert isinstance(tokenizer.vocab_size, int)
    assert tokenizer.vocab_size > 0

def test_config(self, tokenizer):
    config = tokenizer.config
    assert isinstance(config, dict)
    assert 'model_ident' in config
    assert 'add_special_tokens' in config
    assert 'pad' in config

def test_save_load_cycle(self, tokenizer):
    with tempfile.NamedTemporaryFile(suffix='.json') as tmp:
        tokenizer.save(tmp.name)
        loaded = PretrainedTokenizer.load(tmp.name)
        assert isinstance(loaded, PretrainedTokenizer)
        assert loaded.model_ident == tokenizer.model_ident
        assert loaded.add_special_tokens == tokenizer.add_special_tokens
        assert loaded.pad == tokenizer.pad

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

def test_initialization_no_encoder(self, index_cls, encoder_cls, router_cls):
    route_layer_none = router_cls(encoder=None)
    score_threshold = route_layer_none.score_threshold
    if isinstance(route_layer_none, HybridRouter):
        assert score_threshold == 0.3 * route_layer_none.alpha
    else:
        assert score_threshold == 0.3

