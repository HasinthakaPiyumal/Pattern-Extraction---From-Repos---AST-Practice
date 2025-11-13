# Cluster 3

def generate_api_key():
    global SHARED_API_KEY
    if SHARED_API_KEY is None:
        SHARED_API_KEY = secrets.token_hex(32)
    return SHARED_API_KEY

def process_documents(args) -> List[Document]:
    logger.info('Starting document processing')
    blocklist = load_blocklist('./')
    processor = DocumentProcessor(base_path=args.path, file_extensions=args.extensions, blocklist=blocklist, split_by=args.split_by, split_length=args.split_length, split_overlap=args.split_overlap, split_threshold=args.split_threshold)
    documents = processor.process_files()
    logger.info(f'Processed {len(documents)} documents')
    return documents

class MetricsTracker:

    def __init__(self):
        self.metrics = {'total_documents': 0, 'successful_embeddings': 0, 'failed_embeddings': 0, 'avg_embedding_time': 0, 'total_tokens_used': 0}

    def update_embedding_metrics(self, execution_time: float):
        self.metrics['total_documents'] += 1
        self.metrics['successful_embeddings'] += 1
        n = self.metrics['successful_embeddings']
        current_avg = self.metrics['avg_embedding_time']
        self.metrics['avg_embedding_time'] = (current_avg * (n - 1) + execution_time) / n

    def log_metrics(self, logger):
        logger.info('\nEmbedding Metrics:')
        logger.info(f'- Total documents processed: {self.metrics['total_documents']}')
        logger.info(f'- Successful embeddings: {self.metrics['successful_embeddings']}')
        logger.info(f'- Failed embeddings: {self.metrics['failed_embeddings']}')
        logger.info(f'- Average embedding time per document: {self.metrics['avg_embedding_time']:.2f} seconds')

def log_metrics(self, logger):
    logger.info('\nEmbedding Metrics:')
    logger.info(f'- Total documents processed: {self.metrics['total_documents']}')
    logger.info(f'- Successful embeddings: {self.metrics['successful_embeddings']}')
    logger.info(f'- Failed embeddings: {self.metrics['failed_embeddings']}')
    logger.info(f'- Average embedding time per document: {self.metrics['avg_embedding_time']:.2f} seconds')

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

class DocumentProcessor:

    def __init__(self, base_path: str, file_extensions: List[str], blocklist: Set[str]=None, split_by: str='word', split_length: int=200, split_overlap: int=20, split_threshold: int=5, log_level: int=logging.INFO):
        self.base_path = Path(base_path)
        self.file_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in file_extensions]
        self.blocklist = blocklist or set()
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')
        self.logger.setLevel(log_level)
        config = {'base_path': str(self.base_path), 'file_extensions': self.file_extensions, 'blocklist': sorted(self.blocklist), 'split_by': split_by, 'split_length': split_length, 'split_overlap': split_overlap, 'split_threshold': split_threshold}
        self.logger.info('Document processor configuration: %s', json.dumps(config, indent=None))
        self.document_store = InMemoryDocumentStore()
        self.converter = TextFileToDocument(store_full_path=False)
        self.cleaner = DocumentCleaner(ascii_only=True, remove_empty_lines=True, remove_extra_whitespaces=True)
        self.splitter = DocumentSplitter(split_by=split_by, split_length=split_length, split_overlap=split_overlap, split_threshold=split_threshold)
        self.writer = DocumentWriter(document_store=self.document_store, policy=DuplicatePolicy.OVERWRITE)
        self.indexing_pipeline = Pipeline()
        self.indexing_pipeline.add_component(instance=self.converter, name='converter')
        self.indexing_pipeline.add_component(instance=self.cleaner, name='cleaner')
        self.indexing_pipeline.add_component(instance=self.splitter, name='splitter')
        self.indexing_pipeline.add_component(instance=self.writer, name='writer')
        self.indexing_pipeline.connect('converter.documents', 'cleaner.documents')
        self.indexing_pipeline.connect('cleaner.documents', 'splitter.documents')
        self.indexing_pipeline.connect('splitter.documents', 'writer.documents')

    def _build_tree_structure(self, files: List[Path]) -> Dict:
        tree = {}
        for file in sorted(files):
            relative_path = file.relative_to(self.base_path)
            parts = list(relative_path.parts)
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                if current is None:
                    current = {}
            if parts:
                current[parts[-1]] = None
        return tree

    def _print_tree(self, tree: Dict, prefix: str='', is_last: bool=True) -> List[str]:
        if tree is None:
            return []
        tree_lines = []
        items = list(tree.items() if isinstance(tree, dict) else [])
        for i, (name, subtree) in enumerate(items):
            is_last_item = i == len(items) - 1
            icon = '└── ' if is_last_item else '├── '
            tree_lines.append(f'{prefix}{icon}{name}')
            if isinstance(subtree, dict):
                extension = '    ' if is_last_item else '│   '
                subtree_lines = self._print_tree(subtree, prefix + extension, is_last_item)
                tree_lines.extend(subtree_lines)
        return tree_lines

    def _is_blocklisted(self, path: Path) -> bool:
        blocklisted_parts = [part for part in path.parts if part in self.blocklist]
        is_blocklisted = len(blocklisted_parts) > 0
        if is_blocklisted:
            self.logger.debug('Blocklisted path: %s (matched: %s)', path, blocklisted_parts)
        return is_blocklisted

    def _log_processing_summary(self, stats: ProcessingStats):
        """Log a summary of the processing results."""
        summary_lines = ['Processing Summary:', f'Files Processed: {stats.processed_files}', f'Total Documents: {stats.total_documents}', f'Split Documents: {stats.split_documents}', f'Failed Files: {stats.failed_files}', f'Skipped Files: {stats.skipped_files}', f'Blocklisted Files: {stats.blocklisted_files}']
        if stats.total_file_size > 0:
            size_mb = stats.total_file_size / (1024 * 1024)
            summary_lines.append(f'Total File Size: {size_mb:.2f} MB')
        for line in summary_lines:
            self.logger.info(line)

    def process_files(self):
        stats = ProcessingStats()
        self.logger.info('Starting document processing from base path: %s', self.base_path)
        self.logger.info('Active blocklist patterns: %s', sorted(self.blocklist))
        if not self.base_path.exists():
            self.logger.error('Base path not found: %s', self.base_path)
            return []
        self.logger.info('Starting file search...')
        files = []
        blocklisted_files = []
        blocklist_stats = {}
        current_directory = None
        for idx, ext in enumerate(self.file_extensions, 1):
            self.logger.info('Searching [%d/%d]: *%s', idx, len(self.file_extensions), ext)
            try:
                found_files = list(self.base_path.rglob(f'*{ext}'))
                current_found = len(found_files)
                if current_found > 0:
                    self.logger.info('Found %d files with extension %s', current_found, ext)
                valid_files = []
                blocklist_details = defaultdict(list)
                for file in found_files:
                    file_dir = file.parent
                    if file_dir != current_directory:
                        current_directory = file_dir
                        if self.logger.level <= logging.DEBUG:
                            self.logger.debug('Scanning: %s', file_dir.relative_to(self.base_path))
                    if self._is_blocklisted(file):
                        blocklist_reason = next((part for part in file.parts if part in self.blocklist))
                        blocklist_details[blocklist_reason].append(file)
                        blocklist_stats[blocklist_reason] = blocklist_stats.get(blocklist_reason, 0) + 1
                        stats.blocklisted_files += 1
                        blocklisted_files.append(file)
                    else:
                        valid_files.append(file)
                if blocklist_details:
                    self.logger.info('Blocklisted files:')
                    for reason, blocklisted in blocklist_details.items():
                        self.logger.info("  %d files in '%s' directories", len(blocklisted), reason)
                        if self.logger.level <= logging.DEBUG:
                            for bf in blocklisted[:5]:
                                self.logger.debug('    - %s', bf.relative_to(self.base_path))
                            if len(blocklisted) > 5:
                                self.logger.debug('    ... and %d more', len(blocklisted) - 5)
                files.extend(valid_files)
            except Exception as e:
                self.logger.error('Error searching for %s files: %s', ext, str(e))
                continue
        total_files = len(files)
        self.logger.info('Summary: Found %d files to process', total_files)
        if blocklist_stats:
            self.logger.info('Blocklist summary:')
            for pattern, count in sorted(blocklist_stats.items(), key=lambda x: x[1], reverse=True):
                self.logger.info("  %d files skipped due to '%s'", count, pattern)
        if files:
            self.logger.info('Files to be processed:')
            tree = self._build_tree_structure(files)
            tree_output = self._print_tree(tree)
            self.logger.info('.')
            for line in tree_output:
                self.logger.info(line)
            try:
                for file_path in files:
                    stats.total_file_size += file_path.stat().st_size
                self.indexing_pipeline.run({'converter': {'sources': files, 'meta': {'processed_at': datetime.now().isoformat()}}})
                stats.processed_files = len(files)
                stats.total_documents = len(self.document_store.filter_documents())
                stats.split_documents = stats.total_documents
                self._log_processing_summary(stats)
                return self.document_store.filter_documents()
            except Exception as e:
                stats.failed_files += 1
                self.logger.error('Error processing files: %s', str(e), exc_info=True)
                return []

def _log_processing_summary(self, stats: ProcessingStats):
    """Log a summary of the processing results."""
    summary_lines = ['Processing Summary:', f'Files Processed: {stats.processed_files}', f'Total Documents: {stats.total_documents}', f'Split Documents: {stats.split_documents}', f'Failed Files: {stats.failed_files}', f'Skipped Files: {stats.skipped_files}', f'Blocklisted Files: {stats.blocklisted_files}']
    if stats.total_file_size > 0:
        size_mb = stats.total_file_size / (1024 * 1024)
        summary_lines.append(f'Total File Size: {size_mb:.2f} MB')
    for line in summary_lines:
        self.logger.info(line)

def create_app():
    try:
        setup_all_routes(app)
        logger.info(f'Initialized Chipper API {APP_VERSION}.{BUILD_NUMBER}')
        return app
    except Exception as e:
        logger.error(f'Failed to initialize application: {e}', exc_info=True)
        raise

def init_middleware(app):
    setup_security_middleware(app)
    setup_request_logging_middleware(app)
    logger.info('Middleware initialized successfully')

def setup_ollama_proxy_routes(app):
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    proxy = OllamaProxy(ollama_url)
    OllamaRoutes(app, proxy)
    logger.info(f'Initialized Ollama proxy routes with Ollama URL: {ollama_url}')
    return proxy

class DocumentStoreManager:

    def __init__(self, es_url: str, es_index: str, es_basic_auth_user: str, es_basic_auth_password: str):
        self.logger = logging.getLogger(__name__)
        self.es_url = es_url
        self.es_index = es_index
        self.es_basic_auth_user = es_basic_auth_user
        self.es_basic_auth_password = es_basic_auth_password
        self.document_store = None

    def initialize_store(self) -> ElasticsearchDocumentStore:
        try:
            self.logger.info(f'Initializing Elasticsearch document store at {self.es_url}')
            params = {'hosts': self.es_url, 'index': self.es_index}
            if self.es_basic_auth_user and self.es_basic_auth_password and self.es_basic_auth_user.strip() and self.es_basic_auth_password.strip():
                params['basic_auth'] = (self.es_basic_auth_user, self.es_basic_auth_password)
            self.document_store = ElasticsearchDocumentStore(**params)
            doc_count = self.document_store.count_documents()
            self.logger.info(f"Document store initialized successfully. Index '{self.es_index}' contains {doc_count} documents")
            return self.document_store
        except elasticsearch.ConnectionError as e:
            self.logger.error(f'Failed to connect to Elasticsearch at {self.es_url}: {str(e)}', exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f'Failed to initialize document store: {str(e)}', exc_info=True)
            raise

def initialize_store(self) -> ElasticsearchDocumentStore:
    try:
        self.logger.info(f'Initializing Elasticsearch document store at {self.es_url}')
        params = {'hosts': self.es_url, 'index': self.es_index}
        if self.es_basic_auth_user and self.es_basic_auth_password and self.es_basic_auth_user.strip() and self.es_basic_auth_password.strip():
            params['basic_auth'] = (self.es_basic_auth_user, self.es_basic_auth_password)
        self.document_store = ElasticsearchDocumentStore(**params)
        doc_count = self.document_store.count_documents()
        self.logger.info(f"Document store initialized successfully. Index '{self.es_index}' contains {doc_count} documents")
        return self.document_store
    except elasticsearch.ConnectionError as e:
        self.logger.error(f'Failed to connect to Elasticsearch at {self.es_url}: {str(e)}', exc_info=True)
        raise
    except Exception as e:
        self.logger.error(f'Failed to initialize document store: {str(e)}', exc_info=True)
        raise

class PipelineComponentFactory:

    def __init__(self, config: QueryPipelineConfig, document_store: ElasticsearchDocumentStore, streaming_callback: Optional[Callable]=None):
        self.config = config
        self.document_store = document_store
        self.streaming_callback = streaming_callback
        self.logger = logging.getLogger(__name__)

    def create_embedder(self):
        self.logger.info(f'Initializing Text Embedder with model: {self.config.embedding_model}')
        if self.config.provider == ModelProvider.OLLAMA:
            embedder = OllamaTextEmbedder(model=self.config.embedding_model, url=self.config.ollama_url)
        elif self.config.provider == ModelProvider.HUGGINGFACE:
            if not self.config.hf_api_key:
                raise ValueError('HuggingFace API key is required for HuggingFace provider')
            embedder = HuggingFaceAPITextEmbedder(api_type='serverless_inference_api', api_params={'model': self.config.embedding_model}, token=Secret.from_token(self.config.hf_api_key))
        else:
            raise ValueError(f'Unsupported provider: {self.config.provider}')
        self.logger.info('Text Embedder initialized successfully')
        return embedder

    def create_retriever(self) -> ElasticsearchEmbeddingRetriever:
        """Create Elasticsearch retriever."""
        self.logger.info(f'Initializing Elasticsearch Retriever with top_k={self.config.es_top_k} and num_candidates={self.config.es_num_candidates}')
        retriever = ElasticsearchEmbeddingRetriever(document_store=self.document_store, top_k=self.config.es_top_k if self.config.es_top_k is not None and self.config.es_top_k > 0 else None, num_candidates=self.config.es_num_candidates if self.config.es_num_candidates is not None and self.config.es_num_candidates > 0 else None)
        self.logger.info('Elasticsearch Retriever initialized successfully')
        return retriever

    def create_chat_generator(self):
        """Create chat generator based on provider configuration."""
        self.logger.info(f'Initializing Generator with model: {self.config.model_name}')
        if self.config.provider == ModelProvider.OLLAMA:
            generation_kwargs = {}
            if self.config.temperature is not None:
                generation_kwargs['temperature'] = self.config.temperature
            if self.config.context_window is not None:
                generation_kwargs['context_length'] = self.config.context_window
            if self.config.seed is not None and self.config.seed > 0:
                generation_kwargs['seed'] = self.config.seed
            if self.config.top_k is not None:
                generation_kwargs['top_k'] = self.config.top_k
            if self.config.top_p is not None:
                generation_kwargs['top_p'] = self.config.top_p
            if self.config.min_p is not None:
                generation_kwargs['min_p'] = self.config.min_p
            if self.config.mirostat is not None:
                generation_kwargs['mirostat'] = self.config.mirostat
            if self.config.mirostat_eta is not None:
                generation_kwargs['mirostat_eta'] = self.config.mirostat_eta
            if self.config.mirostat_tau is not None:
                generation_kwargs['mirostat_tau'] = self.config.mirostat_tau
            if self.config.repeat_last_n is not None:
                generation_kwargs['repeat_last_n'] = self.config.repeat_last_n
            if self.config.repeat_penalty is not None:
                generation_kwargs['repeat_penalty'] = self.config.repeat_penalty
            if self.config.num_predict is not None:
                generation_kwargs['num_predict'] = self.config.num_predict
            if self.config.tfs_z is not None:
                generation_kwargs['tfs_z'] = self.config.tfs_z
            if self.config.stop_sequence:
                generation_kwargs['stop'] = self.config.stop_sequence
            logging.info(f'Generation kwargs: {generation_kwargs}')
            generator = OllamaChatGenerator(model=self.config.model_name, url=self.config.ollama_url, generation_kwargs=generation_kwargs, streaming_callback=self.streaming_callback, timeout=240)
        elif self.config.provider == ModelProvider.HUGGINGFACE:
            if not self.config.hf_api_key:
                raise ValueError('HuggingFace API key is required for HuggingFace provider')
            generator = HuggingFaceAPIChatGenerator(api_type='serverless_inference_api', api_params={'model': self.config.model_name, 'temperature': self.config.temperature, 'max_length': self.config.context_window, 'system_prompt': self.config.system_prompt}, token=Secret.from_token(self.config.hf_api_key), streaming_callback=self.streaming_callback)
        else:
            raise ValueError(f'Unsupported provider: {self.config.provider}')
        self.logger.info('Generator initialized successfully')
        return generator

def create_retriever(self) -> ElasticsearchEmbeddingRetriever:
    """Create Elasticsearch retriever."""
    self.logger.info(f'Initializing Elasticsearch Retriever with top_k={self.config.es_top_k} and num_candidates={self.config.es_num_candidates}')
    retriever = ElasticsearchEmbeddingRetriever(document_store=self.document_store, top_k=self.config.es_top_k if self.config.es_top_k is not None and self.config.es_top_k > 0 else None, num_candidates=self.config.es_num_candidates if self.config.es_num_candidates is not None and self.config.es_num_candidates > 0 else None)
    self.logger.info('Elasticsearch Retriever initialized successfully')
    return retriever

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

def __init__(self, app):
    self.app = app
    self.abort_flags = {}
    app.secret_key = secrets.token_hex(32)
    logger.info('Initialized SessionManager with new secret key')
    app.config.update(SESSION_COOKIE_SECURE=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=24))

    @app.before_request
    def validate_session():
        self._ensure_valid_session()

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

