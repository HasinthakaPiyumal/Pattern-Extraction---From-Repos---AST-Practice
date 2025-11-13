# Cluster 2

def setup_logging(log_level):
    logging.basicConfig(level=log_level, format='%(message)s', handlers=[RichHandler(rich_tracebacks=True)])

class RAGEmbedder:

    def __init__(self, provider_name: str=None, embedding_model: str=None, es_url: str=None, es_index: str=None, es_basic_auth_user: str=None, es_basic_auth_password: str=None, ollama_url: str=None, hf_api_key: str=None):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        provider_name = provider_name or os.getenv('PROVIDER', 'ollama')
        provider = ModelProvider.OLLAMA
        if provider_name.lower() == 'hf':
            provider = ModelProvider.HUGGINGFACE
        if not embedding_model:
            if provider == ModelProvider.HUGGINGFACE:
                embedding_model = os.getenv('HF_EMBEDDING_MODEL_NAME')
            else:
                embedding_model = os.getenv('EMBEDDING_MODEL_NAME')
        self.logger.info(f'EMBEDDING MODEL:{embedding_model}')
        self.config = PipelineConfig(provider=provider, embedding_model=embedding_model, es_url=es_url or os.getenv('ES_URL'), es_index=es_index or os.getenv('ES_INDEX'), es_basic_auth_user=es_basic_auth_user or os.getenv('ES_BASIC_AUTH_USERNAME'), es_basic_auth_password=es_basic_auth_password or os.getenv('ES_BASIC_AUTH_PASSWORD'), ollama_url=ollama_url or os.getenv('OLLAMA_URL'), hf_api_key=hf_api_key or os.getenv('HF_API_KEY'))
        self._log_configuration()
        self.document_store = self._initialize_document_store()
        if self.config.provider == ModelProvider.OLLAMA:
            self._initialize_ollama()
        self.metrics_tracker = MetricsTracker()

    def _log_configuration(self):
        self.logger.info('\nEmbedding Pipeline Configuration:')
        config_dict = self.config.__dict__.copy()
        if config_dict.get('hf_api_key'):
            config_dict['hf_api_key'] = '****'
        for field_name, field_value in config_dict.items():
            self.logger.info(f'- {field_name}: {field_value}')

    def _check_ollama_health(self):
        try:
            self.logger.info(f'Checking connectivity to Ollama server at {self.config.ollama_url}')
            health_response = requests.get(self.config.ollama_url)
            if health_response.status_code == 200:
                self.logger.info('Successfully connected to the Ollama server')
            else:
                self.logger.error(f'Failed to connect to the Ollama server. Status code: {health_response.status_code}')
                raise Exception('Ollama server connectivity check failed.')
        except Exception as e:
            self.logger.error(f'Error during Ollama server connectivity check: {str(e)}', exc_info=True)
            raise

    def _initialize_ollama(self):
        try:
            self._check_ollama_health()
            self.logger.info(f'Checking embedding model: {self.config.embedding_model}')
            show_response = requests.post(f'{self.config.ollama_url}/api/show', json={'model': self.config.embedding_model})
            if show_response.status_code != 200:
                self.logger.info(f"Pulling model '{self.config.embedding_model}'...")
                pull_response = requests.post(f'{self.config.ollama_url}/api/pull', json={'model': self.config.embedding_model})
                if pull_response.status_code == 200:
                    self.logger.info(f"Embedding model '{self.config.embedding_model}' pulled successfully.")
                else:
                    self.logger.error(f'Failed to pull embedding model: {pull_response.text}')
                    raise Exception(f'Embedding model pull failed: {pull_response.text}')
            else:
                self.logger.info(f"Embedding model '{self.config.embedding_model}' is already available.")
        except Exception as e:
            self.logger.error(f'Failed to verify or pull embedding model: {str(e)}', exc_info=True)
            raise

    def _initialize_document_store(self) -> ElasticsearchDocumentStore:
        try:
            params = {'hosts': self.config.es_url, 'index': self.config.es_index}
            if self.config.es_basic_auth_user and self.config.es_basic_auth_password and self.config.es_basic_auth_user.strip() and self.config.es_basic_auth_password.strip():
                params['basic_auth'] = (self.config.es_basic_auth_user, self.config.es_basic_auth_password)
            document_store = ElasticsearchDocumentStore(**params)
            doc_count = document_store.count_documents()
            self.logger.info(f'Document store initialized successfully with {doc_count} documents')
            return document_store
        except Exception as e:
            self.logger.error(f'Failed to initialize document store: {str(e)}', exc_info=True)
            raise

    def embed_documents(self, documents: List[Document]) -> None:
        start_time = datetime.now()
        total_chars = sum((len(doc.content) for doc in documents))
        self.logger.info('Starting document embedding process:')
        self.logger.info(f'- Total documents: {len(documents)}')
        self.logger.info(f'- Total characters: {total_chars}')
        try:
            embedder = DocumentEmbedder(document_store=self.document_store, model_url=self.config.ollama_url, embedding_model=self.config.embedding_model, provider=self.config.provider, hf_api_key=self.config.hf_api_key)
            embedder.embed_documents(documents)
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info('Document embedding completed:')
            self.logger.info(f'- Execution time: {execution_time:.2f} seconds')
            self.logger.info(f'- Average time per document: {execution_time / len(documents):.2f} seconds')
            self.metrics_tracker.update_embedding_metrics(execution_time)
        except Exception as e:
            self.logger.error(f'Document embedding failed: {str(e)}', exc_info=True)
            self.metrics_tracker.metrics['failed_embeddings'] += 1
            raise

    def finalize(self):
        self.metrics_tracker.log_metrics(self.logger)

def __init__(self, provider_name: str=None, embedding_model: str=None, es_url: str=None, es_index: str=None, es_basic_auth_user: str=None, es_basic_auth_password: str=None, ollama_url: str=None, hf_api_key: str=None):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    self.logger = logging.getLogger(__name__)
    provider_name = provider_name or os.getenv('PROVIDER', 'ollama')
    provider = ModelProvider.OLLAMA
    if provider_name.lower() == 'hf':
        provider = ModelProvider.HUGGINGFACE
    if not embedding_model:
        if provider == ModelProvider.HUGGINGFACE:
            embedding_model = os.getenv('HF_EMBEDDING_MODEL_NAME')
        else:
            embedding_model = os.getenv('EMBEDDING_MODEL_NAME')
    self.logger.info(f'EMBEDDING MODEL:{embedding_model}')
    self.config = PipelineConfig(provider=provider, embedding_model=embedding_model, es_url=es_url or os.getenv('ES_URL'), es_index=es_index or os.getenv('ES_INDEX'), es_basic_auth_user=es_basic_auth_user or os.getenv('ES_BASIC_AUTH_USERNAME'), es_basic_auth_password=es_basic_auth_password or os.getenv('ES_BASIC_AUTH_PASSWORD'), ollama_url=ollama_url or os.getenv('OLLAMA_URL'), hf_api_key=hf_api_key or os.getenv('HF_API_KEY'))
    self._log_configuration()
    self.document_store = self._initialize_document_store()
    if self.config.provider == ModelProvider.OLLAMA:
        self._initialize_ollama()
    self.metrics_tracker = MetricsTracker()

def main():
    blocklist = os.getenv('ENV_MANAGER_BLOCKLIST', '').split(',')
    config = EnvManagerConfig(debug=os.getenv('ENV_MANAGER_DEBUG', '').lower() == 'true', show_full_path=os.getenv('ENV_MANAGER_SHOW_PATH', '').lower() == 'true', blocklist_paths=[p for p in blocklist if p] if blocklist else EnvManagerConfig.blocklist_paths.default_factory())
    manager = EnvManager(config)
    manager.run()

def get_server_config():
    return {'host': os.getenv('HOST', '0.0.0.0'), 'port': int(os.getenv('PORT', '8000')), 'debug': os.getenv('DEBUG', 'False').lower() == 'true'}

@wraps(f)
def decorated_function(*args, **kwargs):
    require_api_key = os.getenv('REQUIRE_API_KEY', 'true')
    require_api_key = require_api_key.lower() == 'true'
    if not require_api_key:
        return f(*args, **kwargs)
    api_key = request.headers.get('X-API-Key')
    bearer_token = get_token_from_header()
    if not (api_key or bearer_token) or (api_key and api_key != API_KEY) or (bearer_token and bearer_token != API_KEY):
        logger.warning(f'Invalid authentication attempt from {request.remote_addr}')
        abort(401, description='Invalid or missing authentication')
    return f(*args, **kwargs)

@app.before_request
def before_request():
    logger.info(f'Request {request.method} {request.path} from {request.remote_addr}')
    if os.getenv('REQUIRE_SECURE', 'False').lower() == 'true' and (not request.is_secure):
        logger.warning(f'Insecure request attempt from {request.remote_addr}')
        abort(403, description='HTTPS required')

@app.after_request
def after_request(response):
    response.headers.update({'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'X-XSS-Protection': '1; mode=block', 'Content-Security-Policy': "default-src 'self'", 'Referrer-Policy': 'strict-origin-when-cross-origin'})
    if os.getenv('ENABLE_CORS', 'False').lower() == 'true':
        allowed_origins = os.getenv('CORS_ALLOWED_ORIGINS', '*')
        response.headers['Access-Control-Allow-Origin'] = allowed_origins
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
    return response

def get_env_value(key: str, converter: Optional[Callable]=None, default: Optional[str]=None) -> Any:
    """Get and convert environment variable value with optional default."""
    value = os.getenv(key)
    if value is None:
        return None
    if converter:
        try:
            return converter(default if value == '' else value)
        except (ValueError, TypeError):
            return None
    return value

def get_provider_specific_config() -> dict[str, Any]:
    """Get provider-specific configuration."""
    provider = ModelProvider.HUGGINGFACE if os.getenv(EnvKeys.PROVIDER, 'ollama').lower() == 'hf' else ModelProvider.OLLAMA
    config = {'provider': provider, 'model_name': os.getenv(EnvKeys.HF_MODEL_NAME if provider == ModelProvider.HUGGINGFACE else EnvKeys.MODEL_NAME), 'embedding_model': os.getenv(EnvKeys.HF_EMBEDDING_MODEL if provider == ModelProvider.HUGGINGFACE else EnvKeys.EMBEDDING_MODEL), 'system_prompt': SYSTEM_PROMPT_VALUE}
    if provider == ModelProvider.HUGGINGFACE:
        config['hf_api_key'] = os.getenv(EnvKeys.HF_API_KEY)
    elif (ollama_url := os.getenv(EnvKeys.OLLAMA_URL)):
        config['ollama_url'] = ollama_url
    return config

def get_elasticsearch_config(index: Optional[str]=None) -> dict[str, Any]:
    """Get Elasticsearch configuration if enabled."""
    if not (es_url := os.getenv(EnvKeys.ES_URL)):
        return {}
    config = {'es_url': es_url, 'es_index': index or os.getenv(EnvKeys.ES_INDEX), 'es_basic_auth_user': os.getenv(EnvKeys.ES_BASIC_AUTH_USER), 'es_basic_auth_password': os.getenv(EnvKeys.ES_BASIC_AUTH_PASSWORD)}
    for env_key, default in [(EnvKeys.ES_TOP_K, '5'), (EnvKeys.ES_NUM_CANDIDATES, '-1')]:
        if (value := get_env_value(env_key, int, default)):
            config[env_key.lower()] = value
    return config

def create_pipeline_config(model: Optional[str]=None, index: Optional[str]=None, temperature: Optional[float]=None, top_k: Optional[int]=None, top_p: Optional[float]=None, min_p: Optional[float]=None, repeat_last_n: Optional[int]=None, repeat_penalty: Optional[float]=None, num_predict: Optional[int]=None, tfs_z: Optional[float]=None, context_window: Optional[int]=None, seed: Optional[int]=None, **additional_params: Dict[str, Any]) -> QueryPipelineConfig:
    """Create pipeline configuration from environment variables with optional parameter overrides."""
    config = get_provider_specific_config()
    if model:
        config['model_name'] = model
    params = GenerationParams()
    for param in params.__annotations__:
        env_key, converter, default = getattr(params, param)
        if (value := get_env_value(env_key, converter, default)):
            config[param] = value
    generation_params = {'temperature': temperature, 'top_k': top_k, 'top_p': top_p, 'min_p': min_p, 'repeat_last_n': repeat_last_n, 'repeat_penalty': repeat_penalty, 'num_predict': num_predict, 'tfs_z': tfs_z, 'context_window': context_window, 'seed': seed}
    config.update({k: v for k, v in generation_params.items() if v is not None})
    config.update(additional_params)
    if (mirostat := get_env_value('MIROSTAT', int)):
        config['mirostat'] = mirostat
        for param in ['MIROSTAT_ETA', 'MIROSTAT_TAU']:
            if (value := get_env_value(param, float)):
                config[param.lower()] = value
    if (allow_pull := os.getenv(EnvKeys.ALLOW_MODEL_PULL)):
        config['allow_model_pull'] = allow_pull.lower() == 'true'
    if (value := os.getenv(EnvKeys.ENABLE_CONVERSATION_LOGS)):
        config['enable_conversation_logs'] = value.lower() == 'true'
    if (stop_sequence := os.getenv('STOP_SEQUENCE')):
        config['stop_sequence'] = stop_sequence
    config.update(get_elasticsearch_config(index))
    logger.info('\nPipeline Configuration:')
    for key, value in sorted(config.items()):
        if any((sensitive in key.lower() for sensitive in ['password', 'key', 'auth'])):
            logger.info(f'  {key}: ****')
        else:
            logger.info(f'  {key}: {value}')
    return QueryPipelineConfig(**config)

def format_model_status(status: Dict[str, Any], config: QueryPipelineConfig) -> Optional[Dict[str, Any]]:
    """Format model status updates for streaming response."""
    model = status.get('model', 'unknown')
    status_type = status.get('status')
    if status_type == 'pulling':
        content = f'Starting to download model {model}...'
    elif status_type == 'progress':
        percentage = status.get('percentage', 0)
        content = f'Downloading model {model}: `{percentage}%` complete'
    elif status_type == 'complete':
        content = f'Successfully downloaded model {model}'
    elif status_type == 'error' and 'pull' in status.get('error', '').lower():
        error_msg = status.get('error', 'Unknown error')
        content = f'Error downloading model {model}: {error_msg}'
    else:
        return None
    content += '\n'
    return format_stream_response(config, content=content)

class OllamaProxy:
    """
    A proxy class for interacting with the Ollama API.

    This class provides methods for all Ollama API endpoints, handling both streaming
    and non-streaming responses, and managing various model operations.
    Ref: https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(self, base_url: Optional[str]=None):
        """
        Initialize the OllamaProxy with a base URL.

        Args:
            base_url: The base URL for the Ollama API. Defaults to environment variable
                     OLLAMA_URL or 'http://localhost:11434'
        """
        self.base_url = base_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')

    def _proxy_request(self, path: str, method: str='GET', stream: bool=False) -> Response:
        """
        Make a proxied request to the Ollama API.

        Args:
            path: The API endpoint path
            method: The HTTP method to use
            stream: Whether to stream the response

        Returns:
            A Flask Response object
        """
        url = f'{self.base_url}{path}'
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'transfer-encoding']}
        data = request.get_data() if method != 'GET' else None
        try:
            response = requests.request(method=method, url=url, headers=headers, data=data, stream=stream)
            if stream:
                return self._handle_streaming_response(response)
            return self._handle_standard_response(response)
        except Exception as e:
            logger.error(f'Error proxying request to Ollama: {str(e)}', exc_info=True)
            return Response(json.dumps({'error': 'An internal error has occurred.'}), status=500, mimetype='application/json')

    def _handle_streaming_response(self, response: requests.Response) -> Response:
        """Handle streaming responses from the Ollama API."""

        def generate():
            try:
                for chunk in response.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk
            except Exception as e:
                logger.error(f'Error streaming response: {str(e)}', exc_info=True)
                yield json.dumps({'error': 'An internal error has occurred.'}).encode()
        response_headers = {'Content-Type': response.headers.get('Content-Type', 'application/json')}
        return Response(stream_with_context(generate()), status=response.status_code, headers=response_headers)

    def _handle_standard_response(self, response: requests.Response) -> Response:
        """Handle non-streaming responses from the Ollama API."""
        return Response(response.content, status=response.status_code, headers={'Content-Type': response.headers.get('Content-Type', 'application/json')})

    def generate(self) -> Response:
        """Generate a completion for a given prompt."""
        return self._proxy_request('/api/generate', 'POST', stream=True)

    def chat(self) -> Response:
        """Generate the next message in a chat conversation."""
        return self._proxy_request('/api/chat', 'POST', stream=True)

    def embeddings(self) -> Response:
        """Generate embeddings (legacy endpoint)."""
        return self._proxy_request('/api/embeddings', 'POST')

    def embed(self) -> Response:
        """Generate embeddings from a model."""
        return self._proxy_request('/api/embed', 'POST')

    def create(self) -> Response:
        """Create a model."""
        return self._proxy_request('/api/create', 'POST', stream=True)

    def show(self) -> Response:
        """Show model information."""
        return self._proxy_request('/api/show', 'POST')

    def copy(self) -> Response:
        """Copy a model."""
        return self._proxy_request('/api/copy', 'POST')

    def delete(self) -> Response:
        """Delete a model."""
        return self._proxy_request('/api/delete', 'DELETE')

    def pull(self) -> Response:
        """Pull a model from the Ollama library."""
        return self._proxy_request('/api/pull', 'POST', stream=True)

    def push(self) -> Response:
        """Push a model to the Ollama library."""
        return self._proxy_request('/api/push', 'POST', stream=True)

    def check_blob(self, digest: str) -> Response:
        """Check if a blob exists."""
        return self._proxy_request(f'/api/blobs/{digest}', 'HEAD')

    def push_blob(self, digest: str) -> Response:
        """Push a blob to the server."""
        return self._proxy_request(f'/api/blobs/{digest}', 'POST')

    def list_local_models(self) -> Response:
        """List models available locally."""
        return self._proxy_request('/api/tags', 'GET')

    def list_running_models(self) -> Response:
        """List models currently loaded in memory."""
        return self._proxy_request('/api/ps', 'GET')

    def version(self) -> Response:
        """Get the Ollama version."""
        return self._proxy_request('/api/version', 'GET')

def __init__(self, base_url: Optional[str]=None):
    """
        Initialize the OllamaProxy with a base URL.

        Args:
            base_url: The base URL for the Ollama API. Defaults to environment variable
                     OLLAMA_URL or 'http://localhost:11434'
        """
    self.base_url = base_url or os.getenv('OLLAMA_URL', 'http://localhost:11434')

class AssetConfig:

    def __init__(self):
        self.asset_url = os.getenv('ASSET_URL', '/static')
        self.cache_timeout = int(os.getenv('ASSET_CACHE_TIMEOUT', '31536000'))
        self.debug_assets = os.getenv('ASSET_DEBUG', 'False').lower() == 'true'
        self.asset_version = os.getenv('ASSET_VERSION', self._generate_version())

    def _generate_version(self) -> str:
        return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]

    def get_asset_url(self, filename: str) -> str:
        if self.debug_assets:
            timestamp = datetime.now().timestamp()
            return f'{self.asset_url}/{filename}?t={timestamp}'
        return f'{self.asset_url}/{filename}?v={self.asset_version}'

def __init__(self):
    self.asset_url = os.getenv('ASSET_URL', '/static')
    self.cache_timeout = int(os.getenv('ASSET_CACHE_TIMEOUT', '31536000'))
    self.debug_assets = os.getenv('ASSET_DEBUG', 'False').lower() == 'true'
    self.asset_version = os.getenv('ASSET_VERSION', self._generate_version())

