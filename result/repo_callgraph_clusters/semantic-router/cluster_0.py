# Cluster 0

def replace_type_hints(file_path):
    with open(file_path, 'rb') as file:
        file_data = file.read()
    file_data = file_data.decode('utf-8', errors='ignore')
    file_data = re.sub('Dict\\[(\\w+), (\\w+)\\]\\s*\\|\\s*None', 'Optional[Dict[\\1, \\2]]', file_data)
    with open(file_path, 'w') as file:
        file.write(file_data)

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

class PineconeRecord(BaseModel):
    id: str = ''
    values: List[float]
    sparse_values: Optional[dict[str, list]] = None
    route: str
    utterance: str
    function_schema: str = '{}'
    metadata: Dict[str, Any] = {}

    def __init__(self, **data):
        """Initialize PineconeRecord.

        :param **data: Keyword arguments to pass to the BaseModel constructor.
        :type **data: dict
        """
        super().__init__(**data)
        clean_route = clean_route_name(self.route)
        utterance_id = hashlib.sha256(self.utterance.encode()).hexdigest()
        self.id = f'{clean_route}#{utterance_id}'
        self.metadata.update({'sr_route': self.route, 'sr_utterance': self.utterance, 'sr_function_schema': self.function_schema})

    def to_dict(self):
        """Convert PineconeRecord to a dictionary.

        :return: Dictionary representation of the PineconeRecord.
        :rtype: dict
        """
        d = {'id': self.id, 'values': self.values, 'metadata': self.metadata}
        if self.sparse_values:
            d['sparse_values'] = self.sparse_values
        return d

def __init__(self, **data):
    """Initialize PineconeRecord.

        :param **data: Keyword arguments to pass to the BaseModel constructor.
        :type **data: dict
        """
    super().__init__(**data)
    clean_route = clean_route_name(self.route)
    utterance_id = hashlib.sha256(self.utterance.encode()).hexdigest()
    self.id = f'{clean_route}#{utterance_id}'
    self.metadata.update({'sr_route': self.route, 'sr_utterance': self.utterance, 'sr_function_schema': self.function_schema})

class LocalEncoder(DenseEncoder):
    """Local encoder using sentence-transformers for efficient local embeddings."""
    name: str = 'BAAI/bge-small-en-v1.5'
    type: str = 'local'
    device: Optional[str] = None
    normalize_embeddings: bool = True
    batch_size: int = 32
    _model: Any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError('Please install sentence-transformers to use LocalEncoder. You can install it with: `pip install semantic-router[local]`')
        self._model = SentenceTransformer(self.name)
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

    def __call__(self, docs: List[str]) -> List[List[float]]:
        result = self._model.encode(docs, batch_size=self.batch_size, normalize_embeddings=self.normalize_embeddings, device=self.device)
        return result.tolist()

def __call__(self, docs: List[str]) -> List[List[float]]:
    result = self._model.encode(docs, batch_size=self.batch_size, normalize_embeddings=self.normalize_embeddings, device=self.device)
    return result.tolist()

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

class OpenAIEncoder(DenseEncoder):
    """OpenAI encoder class for generating embeddings using OpenAI API.

    The OpenAIEncoder class is a subclass of DenseEncoder and utilizes the OpenAI API
    to generate embeddings for given documents. It requires an OpenAI API key and
    supports customization of the score threshold for filtering or processing the embeddings.
    """
    _client: Optional[openai.Client] = PrivateAttr(default=None)
    _async_client: Optional[openai.AsyncClient] = PrivateAttr(default=None)
    dimensions: Union[int, NotGiven] = NotGiven()
    token_limit: int = 8192
    _token_encoder: Any = PrivateAttr()
    type: str = 'openai'
    max_retries: int = 3

    def __init__(self, name: Optional[str]=None, openai_base_url: Optional[str]=None, openai_api_key: Optional[str]=None, openai_org_id: Optional[str]=None, score_threshold: Optional[float]=None, dimensions: Union[int, NotGiven]=NotGiven(), max_retries: int=3):
        """Initialize the OpenAIEncoder.

        :param name: The name of the embedding model to use.
        :type name: str
        :param openai_base_url: The base URL for the OpenAI API.
        :type openai_base_url: str
        :param openai_api_key: The OpenAI API key.
        :type openai_api_key: str
        :param openai_org_id: The OpenAI organization ID.
        :type openai_org_id: str
        :param score_threshold: The score threshold for the embeddings.
        :type score_threshold: float
        :param dimensions: The dimensions of the embeddings.
        :type dimensions: int
        :param max_retries: The maximum number of retries for the OpenAI API call.
        :type max_retries: int
        """
        if name is None:
            name = EncoderDefault.OPENAI.value['embedding_model']
        if score_threshold is None and name in model_configs:
            set_score_threshold = model_configs[name].threshold
        elif score_threshold is None:
            logger.warning(f'Score threshold not set for model: {name}. Using default value.')
            set_score_threshold = 0.82
        else:
            set_score_threshold = score_threshold
        super().__init__(name=name, score_threshold=set_score_threshold)
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        base_url = openai_base_url or os.getenv('OPENAI_BASE_URL')
        openai_org_id = openai_org_id or os.getenv('OPENAI_ORG_ID')
        if api_key is None or api_key.strip() == '':
            raise ValueError("OpenAI API key cannot be 'None' or empty.")
        if max_retries is not None:
            self.max_retries = max_retries
        try:
            self._client = openai.Client(base_url=base_url, api_key=api_key, organization=openai_org_id)
            self._async_client = openai.AsyncClient(base_url=base_url, api_key=api_key, organization=openai_org_id)
        except Exception as e:
            raise ValueError(f'OpenAI API client failed to initialize. Error: {e}') from e
        self.dimensions = dimensions
        if name in model_configs:
            self.token_limit = model_configs[name].token_limit
        self._token_encoder = tiktoken.encoding_for_model(name)

    def __call__(self, docs: List[str], truncate: bool=True) -> List[List[float]]:
        """Encode a list of text documents into embeddings using OpenAI API.

        :param docs: List of text documents to encode.
        :param truncate: Whether to truncate the documents to token limit. If
            False and a document exceeds the token limit, an error will be
            raised.
        :return: List of embeddings for each document."""
        if self._client is None:
            raise ValueError('OpenAI client is not initialized.')
        embeds = None
        if truncate:
            docs = [self._truncate(doc) for doc in docs]
        for j in range(self.max_retries + 1):
            try:
                logger.debug(f'Creating embeddings for {len(docs)} docs')
                embeds = self._client.embeddings.create(input=docs, model=self.name, dimensions=self.dimensions)
                if embeds.data:
                    break
            except OpenAIError as e:
                logger.error('Exception occurred', exc_info=True)
                if self.max_retries != 0 and j < self.max_retries:
                    sleep(2 ** j)
                    logger.warning(f'Retrying in {2 ** j} seconds due to OpenAIError: {e}')
                else:
                    raise
            except Exception as e:
                logger.error(f'OpenAI API call failed. Error: {e}')
                raise ValueError(f'OpenAI API call failed. Error: {str(e)}') from e
        if not embeds or not isinstance(embeds, CreateEmbeddingResponse) or (not embeds.data):
            logger.info(f'Returned embeddings: {embeds}')
            raise ValueError('No embeddings returned.')
        embeddings = [embeds_obj.embedding for embeds_obj in embeds.data]
        return embeddings

    def _truncate(self, text: str) -> str:
        """Truncate a document to the token limit.

        :param text: The document to truncate.
        :type text: str
        :return: The truncated document.
        :rtype: str
        """
        tokens = self._token_encoder.encode_ordinary(text)
        if len(tokens) > self.token_limit:
            logger.warning(f'Document exceeds token limit: {len(tokens)} > {self.token_limit}\nTruncating document...')
            text = self._token_encoder.decode(tokens[:self.token_limit - 1])
            logger.info(f'Trunc length: {len(self._token_encoder.encode(text))}')
            return text
        return text

    async def acall(self, docs: List[str], truncate: bool=True) -> List[List[float]]:
        """Encode a list of text documents into embeddings using OpenAI API asynchronously.

        :param docs: List of text documents to encode.
        :param truncate: Whether to truncate the documents to token limit. If
            False and a document exceeds the token limit, an error will be
            raised.
        :return: List of embeddings for each document."""
        if self._async_client is None:
            raise ValueError('OpenAI async client is not initialized.')
        embeds = None
        if truncate:
            docs = [self._truncate(doc) for doc in docs]
        for j in range(self.max_retries + 1):
            try:
                embeds = await self._async_client.embeddings.create(input=docs, model=self.name, dimensions=self.dimensions)
                if embeds.data:
                    break
            except OpenAIError as e:
                logger.error('Exception occurred', exc_info=True)
                if self.max_retries != 0 and j < self.max_retries:
                    await asleep(2 ** j)
                    logger.warning(f'Retrying in {2 ** j} seconds due to OpenAIError: {e}')
                else:
                    raise
            except Exception as e:
                logger.error(f'OpenAI API call failed. Error: {e}')
                raise ValueError(f'OpenAI API call failed. Error: {e}') from e
        if not embeds or not isinstance(embeds, CreateEmbeddingResponse) or (not embeds.data):
            logger.info(f'Returned embeddings: {embeds}')
            raise ValueError('No embeddings returned.')
        embeddings = [embeds_obj.embedding for embeds_obj in embeds.data]
        return embeddings

def _truncate(self, text: str) -> str:
    """Truncate a document to the token limit.

        :param text: The document to truncate.
        :type text: str
        :return: The truncated document.
        :rtype: str
        """
    tokens = self._token_encoder.encode_ordinary(text)
    if len(tokens) > self.token_limit:
        logger.warning(f'Document exceeds token limit: {len(tokens)} > {self.token_limit}\nTruncating document...')
        text = self._token_encoder.decode(tokens[:self.token_limit - 1])
        logger.info(f'Trunc length: {len(self._token_encoder.encode(text))}')
        return text
    return text

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

def add(self, route: Route):
    """Add a route to the RouterConfig.

        :param route: The route to add.
        :type route: Route
        """
    self.routes.append(route)
    logger.info(f'Added route `{route.name}`')

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

def test_call_method(self, bedrock_encoder):
    response_content = json.dumps({'embedding': [0.1, 0.2, 0.3]})
    response_body = BytesIO(response_content.encode('utf-8'))
    mock_response = {'body': response_body}
    bedrock_encoder.client.invoke_model.return_value = mock_response
    result = bedrock_encoder(['test'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(item, list) for item in result)), 'Each item in result should be a list'
    assert result == [[0.1, 0.2, 0.3]], 'Embedding should be [0.1, 0.2, 0.3]'

def invoke_model_side_effect(*args, **kwargs):
    if not invoke_model_side_effect.expired_token_raised:
        invoke_model_side_effect.expired_token_raised = True
        raise ClientError(error_response, 'invoke_model')
    else:
        return {'body': BytesIO(json.dumps({'embedding': [0.1, 0.2, 0.3]}).encode('utf-8'))}

class TestBedrockEncoderWithCohere:

    def test_cohere_embedding_single_chunk(self, bedrock_encoder_with_cohere):
        response_content = json.dumps({'embeddings': [[0.1, 0.2, 0.3]]})
        response_body = BytesIO(response_content.encode('utf-8'))
        mock_response = {'body': response_body}
        bedrock_encoder_with_cohere.client.invoke_model.return_value = mock_response
        result = bedrock_encoder_with_cohere(['short test'])
        assert isinstance(result, list), 'Result should be a list'
        assert all((isinstance(item, list) for item in result)), 'Each item should be a list'
        assert result == [[0.1, 0.2, 0.3]], 'Expected embedding [0.1, 0.2, 0.3]'

    def test_cohere_input_type(self, bedrock_encoder_with_cohere):
        bedrock_encoder_with_cohere.input_type = 'different_type'
        response_content = json.dumps({'embeddings': [[0.1, 0.2, 0.3]]})
        response_body = BytesIO(response_content.encode('utf-8'))
        mock_response = {'body': response_body}
        bedrock_encoder_with_cohere.client.invoke_model.return_value = mock_response
        result = bedrock_encoder_with_cohere(['test with different input type'])
        assert isinstance(result, list), 'Result should be a list'
        assert result == [[0.1, 0.2, 0.3]], 'Expected specific embeddings'

def test_cohere_embedding_single_chunk(self, bedrock_encoder_with_cohere):
    response_content = json.dumps({'embeddings': [[0.1, 0.2, 0.3]]})
    response_body = BytesIO(response_content.encode('utf-8'))
    mock_response = {'body': response_body}
    bedrock_encoder_with_cohere.client.invoke_model.return_value = mock_response
    result = bedrock_encoder_with_cohere(['short test'])
    assert isinstance(result, list), 'Result should be a list'
    assert all((isinstance(item, list) for item in result)), 'Each item should be a list'
    assert result == [[0.1, 0.2, 0.3]], 'Expected embedding [0.1, 0.2, 0.3]'

def test_cohere_input_type(self, bedrock_encoder_with_cohere):
    bedrock_encoder_with_cohere.input_type = 'different_type'
    response_content = json.dumps({'embeddings': [[0.1, 0.2, 0.3]]})
    response_body = BytesIO(response_content.encode('utf-8'))
    mock_response = {'body': response_body}
    bedrock_encoder_with_cohere.client.invoke_model.return_value = mock_response
    result = bedrock_encoder_with_cohere(['test with different input type'])
    assert isinstance(result, list), 'Result should be a list'
    assert result == [[0.1, 0.2, 0.3]], 'Expected specific embeddings'

