# Cluster 4

def main():
    parser = argparse.ArgumentParser(description='Environment file setup utility')
    parser.add_argument('--clean', action='store_true', help='Remove all generated files')
    parser.add_argument('--docker-only', action='store_true', help='Only create Docker environment file')
    parser.add_argument('--ollama-url', help=f'URL for external Ollama server (default: {DEFAULT_INTERNAL_OLLAMA_URL})')
    args = parser.parse_args()
    if args.clean:
        clean_env_files()
        return 0
    global EXTERNAL_OLLAMA_URL
    EXTERNAL_OLLAMA_URL = args.ollama_url or os.environ.get('OLLAMA_URL') or DEFAULT_EXTERNAL_OLLAMA_URL
    generate_api_key()
    gpu_profile = detect_gpu_profile()
    create_docker_env(gpu_profile)
    use_external_ollama = check_external_ollama_requirement(gpu_profile)
    if args.docker_only:
        return 0
    log_info('Starting to search for example files...')
    found_env_files, files_needing_update = copy_example_files()
    if not found_env_files:
        log_error('No example .env files found!')
        return 1
    for env_file in files_needing_update:
        if str(env_file).endswith('.env'):
            updates = {}
            if has_example_api_key_set(str(env_file)):
                updates['API_KEY'] = SHARED_API_KEY
            if has_ollama_key(str(env_file)) and use_external_ollama:
                updates['OLLAMA_URL'] = EXTERNAL_OLLAMA_URL
            if updates:
                update_env_file(str(env_file), updates)
    log_info('Setup completed successfully!')
    return 0

def main():
    parser = argparse.ArgumentParser(description=f'Chat CLI {APP_VERSION}.{BUILD_NUMBER}')
    parser.add_argument('--host', default=os.getenv('API_HOST', '0.0.0.0'), help='API Host')
    parser.add_argument('--port', default=os.getenv('API_PORT', '8000'), help='API Port')
    parser.add_argument('--api_key', default=os.getenv('API_KEY'), help='API Key')
    parser.add_argument('--timeout', type=int, default=int(os.getenv('API_TIMEOUT', '120')), help='API Timeout')
    parser.add_argument('--verify_ssl', action='store_true', default=os.getenv('REQUIRE_SECURE', 'False').lower() == 'true', help='Verify SSL')
    parser.add_argument('--log_level', default=os.getenv('LOG_LEVEL', 'INFO'), help='Log Level')
    parser.add_argument('--max_context_size', type=int, default=int(os.getenv('MAX_CONTEXT_SIZE', '10')), help='Maximum Context Size')
    parser.add_argument('--model', default=os.getenv('MODEL_NAME'), help='Model name to use')
    parser.add_argument('--index', default=os.getenv('ES_INDEX'), help='Index to use')
    args = parser.parse_args()
    base_url = f'http://{args.host}:{args.port}'
    config = Config(base_url=base_url, api_key=args.api_key, timeout=args.timeout, verify_ssl=args.verify_ssl, log_level=args.log_level, max_context_size=args.max_context_size, max_retries=3, retry_delay=1.0, model=args.model, index=args.index, streaming=False)
    setup_logging(config.log_level)
    chat = ChatInterface(config)
    asyncio.run(chat.run())

def parse_args():
    parser = argparse.ArgumentParser(description=f'Chipper Embed CLI {APP_VERSION}.{BUILD_NUMBER}')
    parser.add_argument('--path', type=str, default='/app/data', help='Base path to process documents from')
    parser.add_argument('--extensions', type=str, nargs='+', default=['.txt', '.md', '.rst', '.log', '.csv', '.json', '.yaml', '.yml', '.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.php', '.py', '.pyx', '.pyi', '.ipynb', '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx', '.java', '.kt', '.gradle', '.cs', '.csproj', '.cshtml', '.rb', '.erb', '.rake', '.sh', '.bash', '.zsh', '.bat', '.cmd', '.ps1', '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh', '.scpt', '.scptd', '.applescript', '.xml', '.ini', '.conf', '.cfg', '.toml', '.qml', '.ui', '.rs', '.go', '.swift'], help='List of file extensions to process')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debug logging')
    parser.add_argument('--provider', type=str, default=None, choices=['ollama', 'hf'], help='Embedding provider')
    parser.add_argument('--es-url', type=str, default=os.getenv('ES_URL', 'http://localhost:9200'), help='URL for the Elasticsearch service')
    parser.add_argument('--es-index', type=str, default=os.getenv('ES_INDEX', 'default'), help='Index for the Elasticsearch service')
    parser.add_argument('--es-basic-auth-user', type=str, default=os.getenv('ES_BASIC_AUTH_USERNAME', ''), help='Username for the Elasticsearch service authentication')
    parser.add_argument('--es-basic-auth-password', type=str, default=os.getenv('ES_BASIC_AUTH_PASSWORD', ''), help='Password for the Elasticsearch service authentication')
    parser.add_argument('--ollama-url', type=str, default=os.getenv('OLLAMA_URL', 'http://localhost:11434'), help='URL for the Ollama service')
    parser.add_argument('--embedding-model', type=str, default=None, help='Model to use for embeddings')
    parser.add_argument('--split-by', type=str, default='word', choices=['word', 'sentence', 'passage', 'page', 'line'], help='Method to split text documents')
    parser.add_argument('--split-length', type=int, default=200, help='Number of units per split')
    parser.add_argument('--split-overlap', type=int, default=20, help='Number of units to overlap between splits')
    parser.add_argument('--split-threshold', type=int, default=5, help='Minimum length of split to keep')
    parser.add_argument('--stats', action='store_true', default=False, help='Enable statistics logging')
    args = parser.parse_args()
    return args

class DocumentEmbedder:

    def __init__(self, document_store: ElasticsearchDocumentStore, model_url: str, embedding_model: str, provider: str=ModelProvider.OLLAMA, hf_api_key: Optional[str]=None):
        self.logger = logging.getLogger(__name__)
        self.document_store = document_store
        self.model_url = model_url
        self.embedding_model = embedding_model
        self.provider = provider
        self.hf_api_key = hf_api_key
        self.embedding_pipeline = None
        self.embedding_dimension = None
        if self.provider == ModelProvider.HUGGINGFACE and (not self.hf_api_key):
            raise ValueError('HuggingFace API key is required when using HuggingFace provider')
        try:
            self._validate_or_set_embedding_dimension()
        except Exception as e:
            self.logger.debug(str(e))

    def create_embedding_pipeline(self) -> Optional[Pipeline]:
        try:
            self.logger.debug('Setting up embedding pipeline')
            embedding_pipeline = Pipeline()
            if self.provider == ModelProvider.OLLAMA:
                document_embedder = OllamaDocumentEmbedder(model=self.embedding_model, url=self.model_url)
            elif self.provider == ModelProvider.HUGGINGFACE:
                document_embedder = HuggingFaceAPIDocumentEmbedder(api_type='serverless_inference_api', api_params={'model': self.embedding_model}, token=Secret.from_token(self.hf_api_key))
            else:
                raise ValueError(f'Unsupported provider: {self.provider}')
            embedding_pipeline.add_component('embedder', document_embedder)
            writer = DocumentWriter(document_store=self.document_store, policy=DuplicatePolicy.OVERWRITE)
            embedding_pipeline.add_component('writer', writer)
            embedding_pipeline.connect('embedder', 'writer')
            self.embedding_pipeline = embedding_pipeline
            return embedding_pipeline
        except Exception as e:
            self.logger.debug(str(e))
            return None

    def get_embedding_dimension(self, text: str='test query') -> Optional[int]:
        if self.embedding_dimension is not None:
            return self.embedding_dimension
        try:
            if self.provider == ModelProvider.OLLAMA:
                text_embedder = OllamaTextEmbedder(model=self.embedding_model, url=self.model_url)
            else:
                text_embedder = HuggingFaceAPITextEmbedder(api_type='serverless_inference_api', api_params={'model': self.embedding_model}, token=Secret.from_token(self.hf_api_key))
            embedding = text_embedder.run(text=text)['embedding']
            self.embedding_dimension = len(embedding)
            self.logger.debug(str(self.embedding_dimension))
            return self.embedding_dimension
        except Exception as e:
            self.logger.debug(str(e))
            return None

    def _validate_or_set_embedding_dimension(self) -> None:
        try:
            docs = self.document_store._search_documents(size=1)
            if docs and len(docs) > 0 and hasattr(docs[0], 'embedding') and (docs[0].embedding is not None):
                self.embedding_dimension = len(docs[0].embedding)
                self.logger.debug(str(self.embedding_dimension))
        except Exception as e:
            self.logger.debug(str(e))

    def _validate_documents(self, documents: List[Document]) -> List[Document]:
        valid_documents = []
        for doc in documents:
            try:
                if isinstance(doc, Document) and hasattr(doc, 'content') and (doc.content is not None):
                    valid_documents.append(doc)
                else:
                    self.logger.debug(str(doc))
            except Exception as e:
                self.logger.debug(str(e))
        return valid_documents

    def embed_documents(self, documents: List[Document], clear_index: bool=False) -> Dict[str, Any]:
        if clear_index:
            self.logger.warning('Clearing all documents from the Elasticsearch index is not implemented yet.')
        embedding_result = {'success': False, 'documents_processed': 0, 'documents_failed': 0, 'error': None}
        if not documents:
            self.logger.debug('No documents provided for embedding')
            embedding_result['error'] = 'No documents provided'
            return embedding_result
        valid_documents = self._validate_documents(documents)
        if not valid_documents:
            self.logger.debug('No valid documents found after validation')
            embedding_result['error'] = 'No valid documents'
            embedding_result['documents_failed'] = len(documents)
            return embedding_result
        if not self.embedding_pipeline:
            self.embedding_pipeline = self.create_embedding_pipeline()
            if not self.embedding_pipeline:
                embedding_result['error'] = 'Failed to create embedding pipeline'
                embedding_result['documents_failed'] = len(valid_documents)
                return embedding_result
        try:
            self.logger.debug(f'Attempting to embed {len(valid_documents)} documents')
            self.embedding_pipeline.run({'embedder': {'documents': valid_documents}})
            embedding_result['success'] = True
            embedding_result['documents_processed'] = len(valid_documents)
            embedding_result['documents_failed'] = len(documents) - len(valid_documents)
        except Exception as e:
            self.logger.debug(str(e))
            embedding_result['error'] = str(e)
            embedding_result['documents_failed'] = len(valid_documents)
        return embedding_result

    def embed_files(self, file_paths: List[str], clear_index: bool=False) -> Dict[str, Any]:
        documents = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                doc_id = generate_document_id(file_path, content)
                doc = Document(id=doc_id, content=content, meta={'filename': os.path.basename(file_path)})
                documents.append(doc)
            except Exception as e:
                self.logger.debug(str(e))
        return self.embed_documents(documents, clear_index=clear_index)

def embed_documents(self, documents: List[Document], clear_index: bool=False) -> Dict[str, Any]:
    if clear_index:
        self.logger.warning('Clearing all documents from the Elasticsearch index is not implemented yet.')
    embedding_result = {'success': False, 'documents_processed': 0, 'documents_failed': 0, 'error': None}
    if not documents:
        self.logger.debug('No documents provided for embedding')
        embedding_result['error'] = 'No documents provided'
        return embedding_result
    valid_documents = self._validate_documents(documents)
    if not valid_documents:
        self.logger.debug('No valid documents found after validation')
        embedding_result['error'] = 'No valid documents'
        embedding_result['documents_failed'] = len(documents)
        return embedding_result
    if not self.embedding_pipeline:
        self.embedding_pipeline = self.create_embedding_pipeline()
        if not self.embedding_pipeline:
            embedding_result['error'] = 'Failed to create embedding pipeline'
            embedding_result['documents_failed'] = len(valid_documents)
            return embedding_result
    try:
        self.logger.debug(f'Attempting to embed {len(valid_documents)} documents')
        self.embedding_pipeline.run({'embedder': {'documents': valid_documents}})
        embedding_result['success'] = True
        embedding_result['documents_processed'] = len(valid_documents)
        embedding_result['documents_failed'] = len(documents) - len(valid_documents)
    except Exception as e:
        self.logger.debug(str(e))
        embedding_result['error'] = str(e)
        embedding_result['documents_failed'] = len(valid_documents)
    return embedding_result

def parse_args():
    parser = argparse.ArgumentParser(description=f'Chipper Web Scrape CLI {APP_VERSION}.{BUILD_NUMBER}')
    parser.add_argument('--base-url', default='https://localhost/', help='Base URL to scrape')
    parser.add_argument('--output-dir', default='data', help='Output directory for scraped data')
    parser.add_argument('--batch-size', type=int, default=5, help='Number of URLs to process in each batch')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between batches in seconds')
    return parser.parse_args()

def main():
    args = parse_args()
    asyncio.run(run_scrapers(args))

def setup_all_routes(app: Flask):
    try:
        if PROVIDER_IS_OLLAMA and ENABLE_OLLAMA_PROXY:
            setup_ollama_proxy_routes(app)
            logger.info('Ollama proxy routes registered successfully')
        if not BYPASS_OLLAMA_RAG or not PROVIDER_IS_OLLAMA:
            register_rag_chat_route(app)
            logger.info('Chat routes registered successfully: RAG and embedding enabled.')
        else:
            logger.warning('Chat routes bypassed! RAG is disabled, and embeddings will not be used.')
        register_health_routes(app)
        logger.info('Health check routes registered successfully')
    except Exception as e:
        logger.error(f'Error setting up routes: {e}', exc_info=True)
        raise

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

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f'404 error: {request.url}')
    return ('', 404)

def parse_args():
    parser = argparse.ArgumentParser(description='Web Client Application')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the application on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    return parser.parse_args()

