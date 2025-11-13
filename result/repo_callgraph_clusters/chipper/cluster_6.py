# Cluster 6

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

def _log_configuration(self):
    self.logger.info('\nEmbedding Pipeline Configuration:')
    config_dict = self.config.__dict__.copy()
    if config_dict.get('hf_api_key'):
        config_dict['hf_api_key'] = '****'
    for field_name, field_value in config_dict.items():
        self.logger.info(f'- {field_name}: {field_value}')

def get_token_from_header():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    return parts[1]

def format_stream_response(config: QueryPipelineConfig, content: str='', done: bool=False, done_reason: Optional[str]=None, images: Optional[List[str]]=None, tool_calls: Optional[List[Dict[str, Any]]]=None, **metrics) -> Dict[str, Any]:
    """Format streaming response according to Ollama-API specification."""
    response = {'model': config.model_name, 'created_at': datetime.now(timezone.utc).isoformat(), 'done': done}
    if not done:
        message = {'role': 'assistant', 'content': content}
        if images:
            message['images'] = images
        if tool_calls:
            message['tool_calls'] = tool_calls
        response['message'] = message
    else:
        if done_reason:
            response['done_reason'] = done_reason
        if done_reason == 'error':
            response['message'] = {'role': 'assistant', 'content': content}
        response.update({'total_duration': metrics.get('total_duration', 0), 'load_duration': metrics.get('load_duration', 0), 'prompt_eval_count': metrics.get('prompt_eval_count', 0), 'prompt_eval_duration': metrics.get('prompt_eval_duration', 0), 'eval_count': metrics.get('eval_count', 0), 'eval_duration': metrics.get('eval_duration', 0)})
    return response

def handle_streaming_response(config: QueryPipelineConfig, query: str, conversation: List[Dict[str, str]], format_schema: Optional[Dict[str, Any]]=None, options: Optional[Dict[str, Any]]=None) -> Response:
    q = queue.Queue()
    start_time = time.time_ns()
    prompt_start = None

    def streaming_callback(chunk):
        nonlocal prompt_start
        if prompt_start is None:
            prompt_start = time.time_ns()
        if chunk.content:
            if format_schema and chunk.is_final:
                try:
                    content = json.loads(chunk.content)
                    response_data = format_stream_response(config, json.dumps(content), done=True, done_reason='stop')
                except json.JSONDecodeError:
                    response_data = format_stream_response(config, 'Error: Failed to generate valid JSON response.', done=True, done_reason='error')
            else:
                response_data = format_stream_response(config, chunk.content, images=getattr(chunk, 'images', None), tool_calls=getattr(chunk, 'tool_calls', None))
            q.put(json.dumps(response_data) + '\n')
    rag = RAGQueryPipeline(config=config, streaming_callback=streaming_callback)

    def run_rag():
        try:
            load_start = time.time_ns()
            for status in rag.initialize_and_check_models():
                if (status_data := format_model_status(status, config)):
                    q.put(json.dumps(status_data) + '\n')
                if status.get('status') == 'error':
                    error_data = format_stream_response(config, f'Error: Model initialization failed - {status.get('error')}', done=True, done_reason='error')
                    q.put(json.dumps(error_data) + '\n')
                    return
            load_duration = time.time_ns() - load_start
            response_text = rag.run_query(query=query, conversation=conversation, print_response=DEBUG)
            end_time = time.time_ns()
            final_data = format_stream_response(config, done=True, done_reason='stop', total_duration=end_time - start_time, load_duration=load_duration, prompt_eval_count=len(conversation) + 1, prompt_eval_duration=end_time - (prompt_start or start_time), eval_count=len(response_text.split()) if response_text is not None else 0, eval_duration=end_time - (prompt_start or start_time))
            q.put(json.dumps(final_data) + '\n')
        except elasticsearch.BadRequestError as e:
            error_data = format_stream_response(config, content=f'Error: Embedding retriever error - {str(e)}', done=True, done_reason='error')
            q.put(json.dumps(error_data) + '\n')
        except Exception as e:
            error_data = format_stream_response(config, content=f'Error: {str(e)}', done=True, done_reason='error')
            logger.error(f'Error in RAG pipeline: {e}', exc_info=True)
            q.put(json.dumps(error_data) + '\n')
    thread = threading.Thread(target=run_rag, daemon=True)
    thread.start()

    def generate():
        while True:
            try:
                data = q.get(timeout=120)
                if data:
                    yield data
                if '"done": true' in data:
                    logger.info('Streaming completed.')
                    break
            except queue.Empty:
                yield (json.dumps({}) + '\n')
                logger.warning('Queue timeout. Sending heartbeat.')
            except Exception as e:
                logger.error(f'Streaming error: {e}')
                error_data = format_stream_response(config, 'Streaming error occurred.', done=True, done_reason='error')
                yield (json.dumps(error_data) + '\n')
                break
    return Response(stream_with_context(generate()), mimetype='application/x-ndjson', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'})

def streaming_callback(chunk):
    nonlocal prompt_start
    if prompt_start is None:
        prompt_start = time.time_ns()
    if chunk.content:
        if format_schema and chunk.is_final:
            try:
                content = json.loads(chunk.content)
                response_data = format_stream_response(config, json.dumps(content), done=True, done_reason='stop')
            except json.JSONDecodeError:
                response_data = format_stream_response(config, 'Error: Failed to generate valid JSON response.', done=True, done_reason='error')
        else:
            response_data = format_stream_response(config, chunk.content, images=getattr(chunk, 'images', None), tool_calls=getattr(chunk, 'tool_calls', None))
        q.put(json.dumps(response_data) + '\n')

def run_rag():
    try:
        load_start = time.time_ns()
        for status in rag.initialize_and_check_models():
            if (status_data := format_model_status(status, config)):
                q.put(json.dumps(status_data) + '\n')
            if status.get('status') == 'error':
                error_data = format_stream_response(config, f'Error: Model initialization failed - {status.get('error')}', done=True, done_reason='error')
                q.put(json.dumps(error_data) + '\n')
                return
        load_duration = time.time_ns() - load_start
        response_text = rag.run_query(query=query, conversation=conversation, print_response=DEBUG)
        end_time = time.time_ns()
        final_data = format_stream_response(config, done=True, done_reason='stop', total_duration=end_time - start_time, load_duration=load_duration, prompt_eval_count=len(conversation) + 1, prompt_eval_duration=end_time - (prompt_start or start_time), eval_count=len(response_text.split()) if response_text is not None else 0, eval_duration=end_time - (prompt_start or start_time))
        q.put(json.dumps(final_data) + '\n')
    except elasticsearch.BadRequestError as e:
        error_data = format_stream_response(config, content=f'Error: Embedding retriever error - {str(e)}', done=True, done_reason='error')
        q.put(json.dumps(error_data) + '\n')
    except Exception as e:
        error_data = format_stream_response(config, content=f'Error: {str(e)}', done=True, done_reason='error')
        logger.error(f'Error in RAG pipeline: {e}', exc_info=True)
        q.put(json.dumps(error_data) + '\n')

def generate():
    while True:
        try:
            data = q.get(timeout=120)
            if data:
                yield data
            if '"done": true' in data:
                logger.info('Streaming completed.')
                break
        except queue.Empty:
            yield (json.dumps({}) + '\n')
            logger.warning('Queue timeout. Sending heartbeat.')
        except Exception as e:
            logger.error(f'Streaming error: {e}')
            error_data = format_stream_response(config, 'Streaming error occurred.', done=True, done_reason='error')
            yield (json.dumps(error_data) + '\n')
            break

def handle_standard_response(config: QueryPipelineConfig, query: str, conversation: List[Dict[str, str]], format_schema: Optional[Dict[str, Any]]=None, options: Optional[Dict[str, Any]]=None) -> Response:
    start_time = time.time_ns()
    rag = RAGQueryPipeline(config=config)
    try:
        load_start = time.time_ns()
        for status in rag.initialize_and_check_models():
            if status.get('status') == 'error':
                raise Exception(f'Model initialization failed: {status.get('error')}')
        load_duration = time.time_ns() - load_start
        prompt_start = time.time_ns()
        result = rag.run_query(query=query, conversation=conversation, print_response=False)
        end_time = time.time_ns()
        response_content = result
        eval_count = len(response_content.split()) if response_content else 0
        response = {'model': config.model_name, 'created_at': datetime.now(timezone.utc).isoformat(), 'message': {'role': 'assistant', 'content': response_content}, 'done': True, 'done_reason': 'stop', 'total_duration': end_time - start_time, 'load_duration': load_duration, 'prompt_eval_count': len(conversation) + 1, 'prompt_eval_duration': end_time - prompt_start, 'eval_count': eval_count, 'eval_duration': end_time - prompt_start}
        logger.info(f'returning: {response}')
        return jsonify(response)
    except Exception as e:
        logger.error(f'Error in RAG pipeline: {e}', exc_info=True)
        error_response = {'model': config.model_name, 'created_at': datetime.now(timezone.utc).isoformat(), 'done': True, 'done_reason': 'error', 'error': 'An internal error has occurred. Please try again later.'}
        return jsonify(error_response)

def log_request_info(request):
    request_info = {'timestamp': datetime.utcnow().isoformat(), 'metadata': {'endpoint': request.endpoint, 'method': request.method, 'remote_addr': request.remote_addr, 'path': request.path}, 'headers': dict(request.headers), 'params': {'url': dict(request.args) if request.args else None, 'form': dict(request.form) if request.form else None, 'cookies': dict(request.cookies) if request.cookies else None}}
    if request.data:
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            try:
                request_info['body'] = request.get_json()
            except Exception as e:
                request_info['body'] = {'error': f'Failed to parse JSON body: {str(e)}', 'raw': request.data.decode('utf-8', errors='replace')}
        else:
            request_info['body'] = request.data.decode('utf-8', errors='replace')
    logger.info('Request: %s', json.dumps(request_info, indent=None, sort_keys=True))

@app.route('/api/chat', methods=['POST'])
@require_api_key
def chat():
    try:
        if DEBUG:
            log_request_info(request)
        data = request.get_json()
        if not data:
            logger.error('No JSON payload received.')
            abort(400, description='Invalid JSON payload.')
        messages = data.get('messages', [])
        if not messages:
            abort(400, description='No messages provided')
        model = None
        if not IGNORE_MODEL_REQUEST:
            model = data.get('model')
            if model and (not ALLOW_MODEL_CHANGE):
                abort(403, description='Model changes are not allowed')
        for message in messages:
            if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                abort(400, description='Invalid message format')
            if message['role'] != '' and message['role'] not in ['system', 'user', 'assistant', 'tool']:
                abort(400, description='Invalid message role')
        options = data.get('options', {})
        stream = data.get('stream', True)
        temperature = None
        top_k = None
        top_p = None
        seed = None
        if ALLOW_MODEL_PARAMETER_CHANGE:
            temperature = data.get('temperature', None)
            top_k = data.get('top_k', None)
            top_p = data.get('top_p', None)
            seed = data.get('seed', None)
        index = options.get('index')
        if index and (not ALLOW_INDEX_CHANGE):
            abort(403, description='Index changes are not allowed')
        for message in messages:
            if 'images' in message and (not isinstance(message['images'], list)):
                abort(400, description='Images must be provided as a list')
        config = create_pipeline_config(model=model, index=index, temperature=temperature, top_k=top_k, top_p=top_p, seed=seed)
        query = None
        for message in reversed(messages):
            content = message.get('content')
            if content:
                query = content
                break
        if not query:
            abort(400, description='No message with content found')
        conversation = messages[:-1] if len(messages) > 1 else []
        if stream:
            return handle_streaming_response(config, query, conversation)
        else:
            return handle_standard_response(config, query, conversation)
    except Exception as e:
        logger.error(f'Error processing chat request: {str(e)}', exc_info=True)
        abort(500, description='Internal Server Error.')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'service': 'chipper-api', 'version': APP_VERSION, 'build': BUILD_NUMBER, 'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

@app.route('/', methods=['GET'])
def root():
    return Response('Chipper is running', mimetype='text/plain')

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

@self.app.route('/api/generate', methods=['POST'])
@require_api_key
def generate():
    try:
        return self.proxy.generate()
    except Exception as e:
        logger.error(f'Error in generate endpoint: {e}')
        return ({'error': 'An internal error has occurred!'}, 500)

@self.app.route('/api/copy', methods=['POST'])
@require_api_key
def copy():
    try:
        return self.proxy.copy()
    except Exception as e:
        logger.error(f'Error in copy endpoint: {e}')
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

class SessionManager:

    def __init__(self, app):
        self.app = app
        self.abort_flags = {}
        app.secret_key = secrets.token_hex(32)
        logger.info('Initialized SessionManager with new secret key')
        app.config.update(SESSION_COOKIE_SECURE=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=24))

        @app.before_request
        def validate_session():
            self._ensure_valid_session()

    def get_abort_flag(self, session_id: str) -> Event:
        if session_id not in self.abort_flags:
            self.abort_flags[session_id] = Event()
        return self.abort_flags[session_id]

    def abort_chat(self, session_id: str):
        if session_id in self.abort_flags:
            self.abort_flags[session_id].set()
            logger.info(f'Chat aborted for session {session_id[:8]}...')

    def reset_abort_flag(self, session_id: str):
        if session_id in self.abort_flags:
            self.abort_flags[session_id] = Event()
            logger.debug(f'Reset abort flag for session {session_id[:8]}...')

    def get_session(self):
        self._ensure_valid_session()
        return session

    def get_session_setting(self, key: str, default=None):
        return session.get(key, default)

    def _ensure_valid_session(self):
        if 'session_id' not in session:
            logger.info('No session_id found - initializing new session')
            self._initialize_new_session()
        elif 'created_at' in session:
            created_at = datetime.fromisoformat(session['created_at'])
            if datetime.now() - created_at > timedelta(hours=24):
                logger.warning(f'Session expired (created: {created_at.isoformat()}) - initializing new session')
                self._initialize_new_session()
            else:
                logger.debug(f'Valid session found (id: {session['session_id'][:8]}...)')

    def _initialize_new_session(self):
        old_session_id = session.get('session_id', 'none')
        session.clear()
        new_session_id = secrets.token_urlsafe(32)
        session['session_id'] = new_session_id
        session['created_at'] = datetime.now().isoformat()
        session['messages'] = []
        logger.info(f'New session initialized: {old_session_id[:8]}... → {new_session_id[:8]}...')

    def get_chat_messages(self) -> List[Dict]:
        self._ensure_valid_session()
        return session.get('messages', [])

    def update_chat_messages(self, role: str, content: str, max_size: int):
        messages = self.get_chat_messages()
        messages.append({'role': role, 'content': content, 'timestamp': datetime.now().isoformat()})
        if len(messages) > max_size:
            messages = messages[-max_size:]
        session['messages'] = messages

    def clear_messages(self):
        if 'session_id' in session:
            session['messages'] = []

    def invalidate_session(self):
        if 'session_id' in session:
            session.clear()

@app.before_request
def validate_session():
    self._ensure_valid_session()

def get_session(self):
    self._ensure_valid_session()
    return session

def get_session_setting(self, key: str, default=None):
    return session.get(key, default)

def _initialize_new_session(self):
    old_session_id = session.get('session_id', 'none')
    session.clear()
    new_session_id = secrets.token_urlsafe(32)
    session['session_id'] = new_session_id
    session['created_at'] = datetime.now().isoformat()
    session['messages'] = []
    logger.info(f'New session initialized: {old_session_id[:8]}... → {new_session_id[:8]}...')

def get_chat_messages(self) -> List[Dict]:
    self._ensure_valid_session()
    return session.get('messages', [])

def update_chat_messages(self, role: str, content: str, max_size: int):
    messages = self.get_chat_messages()
    messages.append({'role': role, 'content': content, 'timestamp': datetime.now().isoformat()})
    if len(messages) > max_size:
        messages = messages[-max_size:]
    session['messages'] = messages

def invalidate_session(self):
    if 'session_id' in session:
        session.clear()

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return (jsonify({'error': 'Invalid JSON payload', 'done': True, 'done_reason': 'error'}), 400)
        session_id = session.get('session_id')
        abort_flag = session_manager.get_abort_flag(session_id)
        session_manager.reset_abort_flag(session_id)
        if data.get('stream', True):
            api_response = make_api_request('/api/chat', data, stream=True)

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
            return Response(stream_with_context(generate()), mimetype='application/x-ndjson', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'})
        else:
            logger.info('Processing non-streaming request')
            response = make_api_request('/api/chat', data)
            return response.json()
    except (ConnectionError, Timeout):
        return (jsonify({'error': 'Connection error', 'done': True, 'done_reason': 'error'}), 503)
    except RequestException as e:
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 500
        logger.error(f'RequestException: {str(e)}')
        return (jsonify({'error': 'An internal error has occurred', 'done': True, 'done_reason': 'error'}), status_code)

@app.route('/api/chat/abort', methods=['POST'])
def abort_chat():
    try:
        session_id = session.get('session_id')
        if not session_id:
            return (jsonify({'error': 'No active session'}), 400)
        session_manager.abort_chat(session_id)
        return jsonify({'status': 'success', 'message': 'Chat aborted'})
    except Exception as e:
        logger.error(f'Error aborting chat: {str(e)}', exc_info=True)
        return (jsonify({'error': 'An internal error has occurred'}), 500)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/assets/config', methods=['GET'])
def get_asset_config():
    return jsonify({'assetUrl': asset_config.asset_url, 'cacheTimeout': asset_config.cache_timeout, 'debugMode': asset_config.debug_assets, 'version': asset_config.asset_version})

@app.route('/health', methods=['GET'])
def health_check():
    api_health = get_api_health()
    current_time = datetime.now(timezone.utc).isoformat()
    response = {'service': 'chipper-web', 'version': APP_VERSION, 'build': BUILD_NUMBER, 'status': 'healthy', 'timestamp': current_time, 'api': api_health}
    if api_health.get('status') == 'unhealthy':
        response['status'] = 'degraded'
    return jsonify(response)

