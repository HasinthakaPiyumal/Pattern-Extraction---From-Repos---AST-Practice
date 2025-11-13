# Cluster 5

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

@app.errorhandler(401)
def unauthorized_error(error):
    return ({'error': 'Unauthorized', 'message': str(error.description)}, 401, {'WWW-Authenticate': 'Bearer realm="API"'})

@app.errorhandler(403)
def forbidden_error(error):
    return ({'error': 'Forbidden', 'message': str(error.description)}, 403)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}', exc_info=True)
    return ({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}, 500)

@app.errorhandler(404)
def not_found_error(error):
    return ('', 404)

class OllamaRoutes:

    def __init__(self, app, proxy: OllamaProxy):
        self.app = app
        self.proxy = proxy
        self.register_routes()
        if BYPASS_OLLAMA_RAG:
            self.register_bypass_routes()

    def register_bypass_routes(self):

        @self.app.route('/api/chat', methods=['POST'])
        @require_api_key
        def chat():
            try:
                return self.proxy.chat()
            except Exception as e:
                logger.error(f'Error in chat endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

    def register_routes(self):

        @self.app.route('/api/generate', methods=['POST'])
        @require_api_key
        def generate():
            try:
                return self.proxy.generate()
            except Exception as e:
                logger.error(f'Error in generate endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/embeddings', methods=['POST'])
        @require_api_key
        def embeddings():
            try:
                return self.proxy.embeddings()
            except Exception as e:
                logger.error(f'Error in embeddings endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/embed', methods=['POST'])
        @require_api_key
        def embed():
            try:
                return self.proxy.embed()
            except Exception as e:
                logger.error(f'Error in embed endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/create', methods=['POST'])
        @require_api_key
        def create():
            try:
                return self.proxy.create()
            except Exception as e:
                logger.error(f'Error in create endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/show', methods=['POST'])
        @require_api_key
        def show():
            try:
                return self.proxy.show()
            except Exception as e:
                logger.error(f'Error in show endpoint: {e}')
                return ({'error': str(e)}, 500)

        @self.app.route('/api/copy', methods=['POST'])
        @require_api_key
        def copy():
            try:
                return self.proxy.copy()
            except Exception as e:
                logger.error(f'Error in copy endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/delete', methods=['DELETE'])
        @require_api_key
        def delete():
            try:
                return self.proxy.delete()
            except Exception as e:
                logger.error(f'Error in delete endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/pull', methods=['POST'])
        @require_api_key
        def pull():
            try:
                return self.proxy.pull()
            except Exception as e:
                logger.error(f'Error in pull endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/push', methods=['POST'])
        @require_api_key
        def push():
            try:
                return self.proxy.push()
            except Exception as e:
                logger.error(f'Error in push endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/blobs/<digest>', methods=['HEAD'])
        @require_api_key
        def check_blob(digest):
            try:
                return self.proxy.check_blob(digest)
            except Exception as e:
                logger.error(f'Error in check_blob endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/blobs/<digest>', methods=['POST'])
        @require_api_key
        def push_blob(digest):
            try:
                return self.proxy.push_blob(digest)
            except Exception as e:
                logger.error(f'Error in push_blob endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/tags', methods=['GET'])
        @require_api_key
        def list_local_models():
            try:
                return self.proxy.list_local_models()
            except Exception as e:
                logger.error(f'Error in list_local_models endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/ps', methods=['GET'])
        @require_api_key
        def list_running_models():
            try:
                return self.proxy.list_running_models()
            except Exception as e:
                logger.error(f'Error in list_running_models endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

        @self.app.route('/api/version', methods=['GET'])
        @require_api_key
        def version():
            try:
                return self.proxy.version()
            except Exception as e:
                logger.error(f'Error in version endpoint: {e}')
                return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/chat', methods=['POST'])
@require_api_key
def chat():
    try:
        return self.proxy.chat()
    except Exception as e:
        logger.error(f'Error in chat endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/embeddings', methods=['POST'])
@require_api_key
def embeddings():
    try:
        return self.proxy.embeddings()
    except Exception as e:
        logger.error(f'Error in embeddings endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/embed', methods=['POST'])
@require_api_key
def embed():
    try:
        return self.proxy.embed()
    except Exception as e:
        logger.error(f'Error in embed endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/create', methods=['POST'])
@require_api_key
def create():
    try:
        return self.proxy.create()
    except Exception as e:
        logger.error(f'Error in create endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/show', methods=['POST'])
@require_api_key
def show():
    try:
        return self.proxy.show()
    except Exception as e:
        logger.error(f'Error in show endpoint: {e}')
        return ({'error': str(e)}, 500)

@self.app.route('/api/delete', methods=['DELETE'])
@require_api_key
def delete():
    try:
        return self.proxy.delete()
    except Exception as e:
        logger.error(f'Error in delete endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/pull', methods=['POST'])
@require_api_key
def pull():
    try:
        return self.proxy.pull()
    except Exception as e:
        logger.error(f'Error in pull endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/push', methods=['POST'])
@require_api_key
def push():
    try:
        return self.proxy.push()
    except Exception as e:
        logger.error(f'Error in push endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/blobs/<digest>', methods=['HEAD'])
@require_api_key
def check_blob(digest):
    try:
        return self.proxy.check_blob(digest)
    except Exception as e:
        logger.error(f'Error in check_blob endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/blobs/<digest>', methods=['POST'])
@require_api_key
def push_blob(digest):
    try:
        return self.proxy.push_blob(digest)
    except Exception as e:
        logger.error(f'Error in push_blob endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/tags', methods=['GET'])
@require_api_key
def list_local_models():
    try:
        return self.proxy.list_local_models()
    except Exception as e:
        logger.error(f'Error in list_local_models endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/ps', methods=['GET'])
@require_api_key
def list_running_models():
    try:
        return self.proxy.list_running_models()
    except Exception as e:
        logger.error(f'Error in list_running_models endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/version', methods=['GET'])
@require_api_key
def version():
    try:
        return self.proxy.version()
    except Exception as e:
        logger.error(f'Error in version endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

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

def generate(self) -> Response:
    """Generate a completion for a given prompt."""
    return self._proxy_request('/api/generate', 'POST', stream=True)

class OllamaModelManager:

    def __init__(self, ollama_url: str, allow_model_pull: bool):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = ollama_url
        self.allow_model_pull = allow_model_pull

    def check_server_health(self):
        try:
            self.logger.info(f'Checking connectivity to Ollama server at {self.ollama_url}')
            health_response = requests.get(self.ollama_url)
            if health_response.status_code != 200:
                raise Exception('Ollama server connectivity check failed.')
            self.logger.info('Successfully connected to the Ollama server')
        except requests.ConnectionError as e:
            self.logger.error(f'Connection error while checking Ollama server: {str(e)}', exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f'Error during Ollama server connectivity check: {str(e)}', exc_info=True)
            raise

    def verify_and_pull_model(self, model_name: str) -> Generator[dict, None, None]:
        try:
            self.logger.info(f'Checking availability of model: {model_name}')
            yield {'type': 'model_status', 'status': 'checking', 'model': model_name}
            show_response = requests.post(f'{self.ollama_url}/api/show', json={'model': model_name})
            if show_response.status_code == 200:
                yield {'type': 'model_status', 'status': 'available', 'model': model_name}
                self.logger.info(f"Model '{model_name}' is already available locally")
                return
            if not self.allow_model_pull:
                error_msg = f"Model '{model_name}' not found locally and auto-pull is disabled"
                self.logger.error(error_msg)
                yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
                raise ModelNotFoundError(error_msg)
            yield from self._pull_model(model_name)
        except ModelNotFoundError:
            raise
        except Exception as e:
            error_msg = f'Failed to verify or pull model {model_name}: {str(e)}'
            self.logger.error(error_msg, exc_info=True)
            yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
            raise

    def _pull_model(self, model_name: str) -> Generator[dict, None, None]:
        self.logger.info(f"Model '{model_name}' not found locally, initiating pull...")
        yield {'type': 'model_status', 'status': 'pulling', 'model': model_name}
        last_percentage = -1
        pull_successful = False
        with requests.post(f'{self.ollama_url}/api/pull', json={'model': model_name}, stream=True) as response:
            if response.status_code != 200:
                error_msg = f'Model pull failed: {response.text}'
                self.logger.error(error_msg)
                yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
                raise Exception(error_msg)
            for line in response.iter_lines():
                if line:
                    progress = json.loads(line)
                    if 'total' in progress and 'completed' in progress:
                        progress_raw = progress['completed'] / progress['total']
                        current_percentage = int(progress_raw * 100)
                        if current_percentage > last_percentage:
                            yield {'type': 'model_status', 'status': 'progress', 'model': model_name, 'percentage': current_percentage}
                            last_percentage = current_percentage
                            if current_percentage == 100:
                                pull_successful = True
        if pull_successful:
            yield {'type': 'model_status', 'status': 'complete', 'model': model_name}
            self.logger.info(f"Model '{model_name}' pulled successfully")
        else:
            error_msg = f"Model '{model_name}' not found after pull attempt"
            self.logger.error(error_msg)
            yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
            raise Exception(error_msg)

def check_server_health(self):
    try:
        self.logger.info(f'Checking connectivity to Ollama server at {self.ollama_url}')
        health_response = requests.get(self.ollama_url)
        if health_response.status_code != 200:
            raise Exception('Ollama server connectivity check failed.')
        self.logger.info('Successfully connected to the Ollama server')
    except requests.ConnectionError as e:
        self.logger.error(f'Connection error while checking Ollama server: {str(e)}', exc_info=True)
        raise
    except Exception as e:
        self.logger.error(f'Error during Ollama server connectivity check: {str(e)}', exc_info=True)
        raise

def verify_and_pull_model(self, model_name: str) -> Generator[dict, None, None]:
    try:
        self.logger.info(f'Checking availability of model: {model_name}')
        yield {'type': 'model_status', 'status': 'checking', 'model': model_name}
        show_response = requests.post(f'{self.ollama_url}/api/show', json={'model': model_name})
        if show_response.status_code == 200:
            yield {'type': 'model_status', 'status': 'available', 'model': model_name}
            self.logger.info(f"Model '{model_name}' is already available locally")
            return
        if not self.allow_model_pull:
            error_msg = f"Model '{model_name}' not found locally and auto-pull is disabled"
            self.logger.error(error_msg)
            yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
            raise ModelNotFoundError(error_msg)
        yield from self._pull_model(model_name)
    except ModelNotFoundError:
        raise
    except Exception as e:
        error_msg = f'Failed to verify or pull model {model_name}: {str(e)}'
        self.logger.error(error_msg, exc_info=True)
        yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
        raise

def _pull_model(self, model_name: str) -> Generator[dict, None, None]:
    self.logger.info(f"Model '{model_name}' not found locally, initiating pull...")
    yield {'type': 'model_status', 'status': 'pulling', 'model': model_name}
    last_percentage = -1
    pull_successful = False
    with requests.post(f'{self.ollama_url}/api/pull', json={'model': model_name}, stream=True) as response:
        if response.status_code != 200:
            error_msg = f'Model pull failed: {response.text}'
            self.logger.error(error_msg)
            yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
            raise Exception(error_msg)
        for line in response.iter_lines():
            if line:
                progress = json.loads(line)
                if 'total' in progress and 'completed' in progress:
                    progress_raw = progress['completed'] / progress['total']
                    current_percentage = int(progress_raw * 100)
                    if current_percentage > last_percentage:
                        yield {'type': 'model_status', 'status': 'progress', 'model': model_name, 'percentage': current_percentage}
                        last_percentage = current_percentage
                        if current_percentage == 100:
                            pull_successful = True
    if pull_successful:
        yield {'type': 'model_status', 'status': 'complete', 'model': model_name}
        self.logger.info(f"Model '{model_name}' pulled successfully")
    else:
        error_msg = f"Model '{model_name}' not found after pull attempt"
        self.logger.error(error_msg)
        yield {'type': 'model_status', 'status': 'error', 'model': model_name, 'error': error_msg}
        raise Exception(error_msg)

class RAGQueryPipeline:
    template = [ChatMessage.from_system('\n        System prompt:\n        {{ system_prompt }}\n\n        {% if conversation %}\n        Previous conversation:\n        {% for message in conversation %}\n        {{ message.role }}: {{ message.content }}\n        {% endfor %}\n        {% endif %}\n\n        Context:\n        {% for document in documents %}\n            {{ document.content }}\n            Source: {{ document.meta.file_path }}\n        {% endfor %}\n\n        Question: {{ question }}?\n    ')]

    def initialize_and_check_models(self) -> Generator[dict, None, None]:
        """Verify model availability and health, pulling models if needed."""
        try:
            if self.config.provider == ModelProvider.OLLAMA:
                if not self.model_manager:
                    raise ValueError('Ollama model manager not initialized but provider is Ollama')
                self.model_manager.check_server_health()
                required_models = [self.config.model_name, self.config.embedding_model]
                for model_name in required_models:
                    yield from self.model_manager.verify_and_pull_model(model_name)
            else:
                yield {'type': 'model_status', 'status': 'success', 'message': 'Using HuggingFace provider'}
        except Exception as e:
            self.logger.error(f'Model initialization failed: {str(e)}', exc_info=True)
            yield {'type': 'model_status', 'status': 'error', 'error': str(e)}
            raise

    def __init__(self, config: QueryPipelineConfig, streaming_callback=None):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._streaming_callback = streaming_callback
        self.query_pipeline = None
        self._init_conversation_logger()
        self._init_document_store()
        self._init_model_manager()
        self.component_factory = PipelineComponentFactory(config, self.document_store, streaming_callback)

    def _init_conversation_logger(self):
        if self.config.enable_conversation_logs:
            self.conversation_logger = ConversationLogger(system_info={'provider': self.config.provider, 'elasticsearch': {'index': self.config.es_index, 'top_k': self.config.es_top_k, 'num_candidates': self.config.es_num_candidates}, 'model_params': {'temperature': self.config.temperature, 'top_k': self.config.top_k, 'top_p': self.config.top_p, 'min_p': self.config.min_p, 'seed': self.config.seed}})
        else:
            self.conversation_logger = None

    def _init_document_store(self):
        self.doc_store_manager = DocumentStoreManager(self.config.es_url, self.config.es_index, self.config.es_basic_auth_user, self.config.es_basic_auth_password)
        self.document_store = self.doc_store_manager.initialize_store()

    def _init_model_manager(self):
        self.model_manager = None
        if self.config.provider == ModelProvider.OLLAMA:
            self.model_manager = OllamaModelManager(self.config.ollama_url, self.config.allow_model_pull)

    def create_query_pipeline(self) -> Pipeline:
        """Initialize and configure the query pipeline components."""
        try:
            pipeline = Pipeline()
            embedder = self.component_factory.create_embedder()
            retriever = self.component_factory.create_retriever()
            llm_generator = self.component_factory.create_chat_generator()
            pipeline.add_component('embedder', embedder)
            pipeline.add_component('retriever', retriever)
            pipeline.add_component('prompt_builder', ChatPromptBuilder(template=self.template))
            pipeline.add_component('llm', llm_generator)
            pipeline.connect('embedder.embedding', 'retriever.query_embedding')
            pipeline.connect('retriever', 'prompt_builder.documents')
            pipeline.connect('prompt_builder.prompt', 'llm.messages')
            self.query_pipeline = pipeline
            return pipeline
        except Exception as e:
            self.logger.error(f'Pipeline creation failed: {str(e)}', exc_info=True)
            raise

    def run_query(self, query: str, conversation: List[dict]=None, print_response: bool=False) -> Optional[dict]:
        """Execute a query through the RAG pipeline."""
        if not self.query_pipeline:
            self.create_query_pipeline()
        try:
            pipeline_inputs = {'prompt_builder': {'conversation': conversation, 'question': query, 'system_prompt': self.config.system_prompt}, 'embedder': {'text': query}}
            response = self.query_pipeline.run(pipeline_inputs)
            response_text = response['llm']['replies'][0].text if response['llm']['replies'] else None
            if print_response and response_text:
                self.logger.info(f'Query: {query}')
                self.logger.info(f'Response: {response_text}')
            if self.conversation_logger:
                self.conversation_logger.log_conversation(query, response, conversation)
            return response_text
        except pydantic.ValidationError as ve:
            self.logger.warning(f'Pydantic validation error: {str(ve)}')
            return None
        except elasticsearch.BadRequestError as e:
            self.logger.error(f'Elasticsearch error: {str(e)}')
            raise
        except Exception as e:
            self.logger.error(f'Query execution failed: {str(e)}')
            raise

def initialize_and_check_models(self) -> Generator[dict, None, None]:
    """Verify model availability and health, pulling models if needed."""
    try:
        if self.config.provider == ModelProvider.OLLAMA:
            if not self.model_manager:
                raise ValueError('Ollama model manager not initialized but provider is Ollama')
            self.model_manager.check_server_health()
            required_models = [self.config.model_name, self.config.embedding_model]
            for model_name in required_models:
                yield from self.model_manager.verify_and_pull_model(model_name)
        else:
            yield {'type': 'model_status', 'status': 'success', 'message': 'Using HuggingFace provider'}
    except Exception as e:
        self.logger.error(f'Model initialization failed: {str(e)}', exc_info=True)
        yield {'type': 'model_status', 'status': 'error', 'error': str(e)}
        raise

def get_api_health() -> Dict[str, Any]:
    try:
        api_url = os.getenv('API_URL', 'http://localhost:8000')
        headers = {'X-API-Key': os.getenv('API_KEY', 'EXAMPLE_API_KEY')}
        response = requests.get(f'{api_url}/health', headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f'API health check failed: {str(e)}')
        return {'status': 'unhealthy', 'error': 'An internal error has occurred.'}

def make_api_request(endpoint: str, data: Dict, stream: bool=False) -> Any:
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    headers = {'Content-Type': 'application/json', 'X-API-Key': os.getenv('API_KEY', 'EXAMPLE_API_KEY')}
    try:
        response = requests.post(f'{api_url}{endpoint}', headers=headers, json=data, stream=stream, timeout=120)
        response.raise_for_status()
        return response
    except (ConnectionError, Timeout) as e:
        logger.error(f'Connection error: {str(e)}')
        raise
    except RequestException as e:
        logger.error(f'Request error: {str(e)}')
        raise

def generate():
    try:
        for chunk in api_response.iter_lines():
            if abort_flag.is_set():
                logger.info(f'Aborting stream for session {session_id[:8]}...')
                api_response.close()
                yield 'data: {"type": "abort", "content": "Request aborted"}\n\n'
                break
            if chunk:
                yield f'data: {chunk.decode()}\n\n'
    except Exception as e:
        logger.error(f'Stream error: {str(e)}')
        yield f'data: {{"error": "{str(e)}", "done": true}}\n\n'

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'500 error: {str(error)}')
    return ('', 500)

