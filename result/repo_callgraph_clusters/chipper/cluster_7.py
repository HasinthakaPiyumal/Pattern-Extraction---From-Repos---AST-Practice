# Cluster 7

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

def _is_blocklisted(self, path: Path) -> bool:
    blocklisted_parts = [part for part in path.parts if part in self.blocklist]
    is_blocklisted = len(blocklisted_parts) > 0
    if is_blocklisted:
        self.logger.debug('Blocklisted path: %s (matched: %s)', path, blocklisted_parts)
    return is_blocklisted

@app.before_request
def log_request_info():
    if request.path == '/' or request.path == '/health':
        return
    log_data = {'method': request.method, 'path': request.path, 'remote_addr': request.remote_addr, 'user_agent': request.headers.get('User-Agent'), 'request_id': request.headers.get('X-Request-ID')}
    logger.debug('Incoming request', extra=log_data)

class ConversationLogger:

    def __init__(self, system_info: dict, log_dir: str='conversation_logs'):
        """Initialize the conversation logger.

        Args:
            system_info: Dictionary containing system information to be logged
            log_dir: Directory where conversation logs will be stored
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.system_info = system_info

    def _serialize_chat_message(self, message: Union[ChatMessage, Dict[str, Any]]) -> Dict[str, Any]:
        """Serialize a ChatMessage object or dict into a consistent dictionary format.

        Args:
            message: ChatMessage object or dictionary to serialize

        Returns:
            Dictionary representation of the message
        """
        try:
            if isinstance(message, ChatMessage):
                return {'role': message.role.value if isinstance(message.role, ChatRole) else message.role, 'content': message.text, 'name': message.name, 'meta': message.meta}
            elif isinstance(message, dict):
                if 'llm' in message and 'replies' in message['llm']:
                    replies = message['llm']['replies']
                    if replies and isinstance(replies[0], ChatMessage):
                        return self._serialize_chat_message(replies[0])
                return message
            raise ValueError(f'Unsupported message type: {type(message)}')
        except Exception as e:
            return {'error': f'Serialization error: {str(e)}', 'content': str(message), 'type': str(type(message))}

    def log_conversation(self, query: str, response: Union[ChatMessage, Dict[str, Any]], conversation: List[ChatMessage]=None) -> None:
        """Log a conversation exchange to a JSON file.

        Args:
            query: The user's query string
            response: Response containing LLM replies (either ChatMessage or dict)
            conversation: Optional list of previous messages in the conversation
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'conversation_{timestamp}.json'
        try:
            response_meta = {}
            if isinstance(response, dict) and 'llm' in response:
                response_meta = response.get('llm', {}).get('meta', {})
            log_entry = {'timestamp': timestamp, 'query': query, 'system_info': self.system_info, 'response': {'llm': {'replies': [self._serialize_chat_message(response)], 'meta': response_meta}}, 'previous_conversation': [self._serialize_chat_message(msg) for msg in conversation or []]}
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            error_file = self.log_dir / f'error_{timestamp}.txt'
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f'Error logging conversation: {str(e)}\n')
                f.write(f'Query: {query}\n')
                f.write(f'Response type: {type(response)}\n')
                f.write(f'Response: {str(response)}\n')

def _serialize_chat_message(self, message: Union[ChatMessage, Dict[str, Any]]) -> Dict[str, Any]:
    """Serialize a ChatMessage object or dict into a consistent dictionary format.

        Args:
            message: ChatMessage object or dictionary to serialize

        Returns:
            Dictionary representation of the message
        """
    try:
        if isinstance(message, ChatMessage):
            return {'role': message.role.value if isinstance(message.role, ChatRole) else message.role, 'content': message.text, 'name': message.name, 'meta': message.meta}
        elif isinstance(message, dict):
            if 'llm' in message and 'replies' in message['llm']:
                replies = message['llm']['replies']
                if replies and isinstance(replies[0], ChatMessage):
                    return self._serialize_chat_message(replies[0])
            return message
        raise ValueError(f'Unsupported message type: {type(message)}')
    except Exception as e:
        return {'error': f'Serialization error: {str(e)}', 'content': str(message), 'type': str(type(message))}

def log_conversation(self, query: str, response: Union[ChatMessage, Dict[str, Any]], conversation: List[ChatMessage]=None) -> None:
    """Log a conversation exchange to a JSON file.

        Args:
            query: The user's query string
            response: Response containing LLM replies (either ChatMessage or dict)
            conversation: Optional list of previous messages in the conversation
        """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = self.log_dir / f'conversation_{timestamp}.json'
    try:
        response_meta = {}
        if isinstance(response, dict) and 'llm' in response:
            response_meta = response.get('llm', {}).get('meta', {})
        log_entry = {'timestamp': timestamp, 'query': query, 'system_info': self.system_info, 'response': {'llm': {'replies': [self._serialize_chat_message(response)], 'meta': response_meta}}, 'previous_conversation': [self._serialize_chat_message(msg) for msg in conversation or []]}
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        error_file = self.log_dir / f'error_{timestamp}.txt'
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f'Error logging conversation: {str(e)}\n')
            f.write(f'Query: {query}\n')
            f.write(f'Response type: {type(response)}\n')
            f.write(f'Response: {str(response)}\n')

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

def get_abort_flag(self, session_id: str) -> Event:
    if session_id not in self.abort_flags:
        self.abort_flags[session_id] = Event()
    return self.abort_flags[session_id]

def reset_abort_flag(self, session_id: str):
    if session_id in self.abort_flags:
        self.abort_flags[session_id] = Event()
        logger.debug(f'Reset abort flag for session {session_id[:8]}...')

