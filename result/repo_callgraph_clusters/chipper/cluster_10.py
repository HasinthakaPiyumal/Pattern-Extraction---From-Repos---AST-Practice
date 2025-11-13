# Cluster 10

class Config:

    def __init__(self, base_url, api_key, timeout, verify_ssl, log_level, max_context_size, max_retries=3, retry_delay=1.0, model=None, index=None, streaming=False):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.log_level = log_level
        self.max_context_size = max_context_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.model = model
        self.index = index
        self.streaming = streaming
        if not self.api_key:
            raise ValueError('API key must be provided.')

def __init__(self, base_url, api_key, timeout, verify_ssl, log_level, max_context_size, max_retries=3, retry_delay=1.0, model=None, index=None, streaming=False):
    self.base_url = base_url
    self.api_key = api_key
    self.timeout = timeout
    self.verify_ssl = verify_ssl
    self.log_level = log_level
    self.max_context_size = max_context_size
    self.max_retries = max_retries
    self.retry_delay = retry_delay
    self.model = model
    self.index = index
    self.streaming = streaming
    if not self.api_key:
        raise ValueError('API key must be provided.')

class AsyncAPIClient:

    def __init__(self, config: Config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        self.max_retries = self.config.max_retries
        self.retry_delay = self.config.retry_delay

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30, enable_cleanup_closed=True, force_close=False)
        self.session = aiohttp.ClientSession(headers={'X-API-Key': self.config.api_key, 'Content-Type': 'application/json'}, timeout=aiohttp.ClientTimeout(total=self.config.timeout, connect=30.0, sock_read=90.0, sock_connect=30.0), connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and (not self.session.closed):
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, attempt: int=1, **kwargs) -> Dict[str, Any]:
        url = urljoin(self.config.base_url, endpoint)
        kwargs.setdefault('ssl', self.config.verify_ssl)
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                if method.upper() == 'HEAD':
                    return {}
                return await response.json()
        except asyncio.TimeoutError:
            self.logger.warning(f'Request timed out (attempt {attempt}/{self.max_retries})')
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * attempt)
                return await self._make_request(method, endpoint, attempt + 1, **kwargs)
            raise APIError('Request timed out after all retries')
        except aiohttp.ClientResponseError as e:
            if e.status == 429 and attempt < self.max_retries:
                retry_after = int(e.headers.get('Retry-After', self.retry_delay * 2))
                await asyncio.sleep(retry_after)
                return await self._make_request(method, endpoint, attempt + 1, **kwargs)
            raise APIError(f'API request failed: {str(e)}')
        except aiohttp.ClientError as e:
            if attempt < self.max_retries and isinstance(e, (aiohttp.ClientConnectorError, aiohttp.ServerDisconnectedError)):
                await asyncio.sleep(self.retry_delay * attempt)
                return await self._make_request(method, endpoint, attempt + 1, **kwargs)
            raise APIError(f'API request failed: {str(e)}')

    async def _stream_response(self, response: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        try:
            buffer = ''
            async for chunk in response.content.iter_chunks():
                chunk_data = chunk[0].decode('utf-8')
                buffer += chunk_data
                while '\n\n' in buffer:
                    message, buffer = buffer.split('\n\n', 1)
                    if message.startswith('data: '):
                        data = json.loads(message[6:])
                        if 'chunk' in data:
                            yield data['chunk']
                        elif 'message' in data and 'content' in data['message']:
                            yield data['message']['content']
                        elif 'error' in data:
                            raise APIError(data['error'])
                        if data.get('done', False):
                            return
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise APIError(f'Failed to decode stream: {str(e)}')

    async def query(self, query_text: str, conversation_context: List[Dict[str, str]]) -> Dict[str, Any]:
        messages = []
        for ctx in conversation_context:
            clean_content = ctx['content'].encode('utf-8', errors='ignore').decode('utf-8')
            messages.append({'role': ctx['role'], 'content': clean_content})
        clean_query = query_text.encode('utf-8', errors='ignore').decode('utf-8')
        messages.append({'role': 'user', 'content': clean_query})
        options = {k: v for k, v in {'model': self.config.model, 'index': self.config.index}.items() if v is not None}
        try:
            response = await self._make_request('POST', '/api/chat', json={'messages': messages, 'stream': False, 'options': options})
            if 'message' in response:
                return {'success': True, 'result': {'llm': {'replies': [response['message']['content']]}}}
            elif 'error' in response:
                raise APIError(response['error'])
            else:
                return response
        except APIError as e:
            self.logger.error(f'Query failed: {str(e)}')
            raise

    async def health_check(self) -> Dict[str, Any]:
        try:
            return await self._make_request('GET', '/health')
        except APIError as e:
            self.logger.error(f'Health check failed: {str(e)}')
            raise

def __init__(self, config: Config):
    self.config = config
    self.session: Optional[aiohttp.ClientSession] = None
    self.logger = logging.getLogger(__name__)
    self.max_retries = self.config.max_retries
    self.retry_delay = self.config.retry_delay

class ChatInterface:

    def __init__(self, config: Config):
        self.config = config
        self.theme = Theme({'user': 'green', 'assistant': 'blue', 'system': 'yellow', 'error': 'red'})
        self.console = Console(theme=self.theme, force_terminal=True)
        self.conversation_context: Deque[Dict[str, str]] = deque(maxlen=self.config.max_context_size)
        self.message_history: List[Message] = []
        self.commands = {'/quit': self._cmd_quit, '/clear': self._cmd_clear, '/history': self._cmd_history, '/help': self._cmd_help, '/context': self._cmd_context, '/model': self._cmd_model, '/index': self._cmd_index, '/settings': self._cmd_settings, '/retry': self._cmd_retry, '/stream': self._cmd_stream}
        self.last_query = None
        self.last_context = None

    async def _handle_query(self, user_input: str, context: list=None):
        if context is None:
            context = list(self.conversation_context)
        try:
            if self.config.streaming:
                self.display_message(Message('Steaming is not implemented!', MessageType.ERROR))
            else:
                await self._handle_non_streaming_query(user_input, context)
        except APIError as e:
            self.display_message(Message(f'Error: {str(e)}\nUse /retry to try again.', MessageType.ERROR))

    async def _handle_non_streaming_query(self, user_input: str, context: list):
        try:
            with self.console.status('[bold blue]Thinking...', spinner='dots'):
                response = await self.client.query(user_input, context)
                if 'error' in response:
                    raise APIError(response['error'])
                if response.get('success'):
                    result = response.get('result', {})
                    replies = result.get('llm', {}).get('replies', [])
                    if not replies:
                        self.display_message(Message('No response received', MessageType.ERROR))
                    else:
                        for reply in replies:
                            self.display_message(Message(reply, MessageType.ASSISTANT))
                else:
                    self.display_message(Message('Failed to get response', MessageType.ERROR))
        except APIError as e:
            raise e

    def display_welcome(self):
        welcome_text = '\n    Available commands:\n    * /help     - Show this help message\n    * /quit     - Exit the application\n    * /clear    - Clear the screen\n    * /history  - Show message history\n    * /context  - Adjust context size\n    * /model    - Set the model name\n    * /index    - Set the index name\n    * /settings - Show current settings\n    * /retry    - Retry last query\n    * /stream   - Toggle streaming mode\n\n    Type your message and press Enter to chat.\n    '
        self.console.print(Panel(Markdown(welcome_text), title=f'Chat CLI {APP_VERSION}.{BUILD_NUMBER}', border_style='blue'))

    def get_user_input(self) -> str:
        """Get input from the user with proper formatting."""
        try:
            return Prompt.ask('\n[bold green]You[/bold green]')
        except (KeyboardInterrupt, EOFError):
            self.console.print('\n[yellow]Input interrupted. Type /quit to exit.[/yellow]')
            return ''

    def display_message(self, message: Message):
        panel = Panel(Markdown(message.content), border_style=message.type.value, title=message.type.value.title(), title_align='left')
        self.console.print(panel)
        self.message_history.append(message)
        if message.type in [MessageType.USER, MessageType.ASSISTANT]:
            self.conversation_context.append({'role': message.type.value, 'content': message.content})

    async def run(self):
        try:
            async with AsyncAPIClient(self.config) as client:
                self.client = client
                health_status = await client.health_check()
                if health_status.get('status') != 'healthy':
                    raise APIError('API is not healthy')
                self.display_welcome()
                while True:
                    try:
                        user_input = self.get_user_input()
                        if user_input.startswith('/'):
                            should_continue = await self.process_command(user_input)
                            if not should_continue:
                                break
                            continue
                        user_message = Message(user_input, MessageType.USER)
                        self.display_message(user_message)
                        self.last_query = user_input
                        self.last_context = list(self.conversation_context)
                        await self._handle_query(user_input)
                    except asyncio.CancelledError:
                        self.console.print('[red]Operation cancelled[/red]')
                    except Exception as e:
                        self.console.print(f'Error processing message: {e}')
                        error_message = Message(f'Internal error: {str(e)}', MessageType.ERROR)
                        self.display_message(error_message)
        except Exception as e:
            self.console.print(f'[red]Fatal error: {str(e)}[/red]')

    async def _cmd_quit(self) -> bool:
        self.console.print('[blue]Goodbye![/blue]')
        return False

    async def _cmd_clear(self) -> bool:
        self.console.clear()
        self.display_welcome()
        return True

    async def _cmd_history(self) -> bool:
        if not self.message_history:
            self.console.print('[blue]No message history available.[/blue]')
            return True
        for msg in self.message_history[-10:]:
            self.console.print(f'[{msg.type.value}]{msg.content}[/{msg.type.value}]')
        return True

    async def _cmd_help(self) -> bool:
        self.display_welcome()
        return True

    async def _cmd_context(self) -> bool:
        new_size = IntPrompt.ask('[blue]Enter new context size[/blue]', default=self.config.max_context_size)
        self.conversation_context = deque(list(self.conversation_context), maxlen=new_size)
        self.config.max_context_size = new_size
        self.console.print(f'[blue]Context size updated to {new_size}[/blue]')
        return True

    async def _cmd_model(self) -> bool:
        current = self.config.model or 'default'
        new_model = Prompt.ask('[blue]Enter model name[/blue]', default=current)
        if new_model.lower() == 'default':
            self.config.model = None
            self.console.print('[blue]Model reset to default[/blue]')
        else:
            self.config.model = new_model
            self.console.print(f'[blue]Model updated to {new_model}[/blue]')
        return True

    async def _cmd_index(self) -> bool:
        current = self.config.index or 'default'
        new_index = Prompt.ask('[blue]Enter index name[/blue]', default=current)
        if new_index.lower() == 'default':
            self.config.index = None
            self.console.print('[blue]Index reset to default[/blue]')
        else:
            self.config.index = new_index
            self.console.print(f'[blue]Index updated to {new_index}[/blue]')
        return True

    async def _cmd_stream(self) -> bool:
        self.config.streaming = not self.config.streaming
        status = 'enabled' if self.config.streaming else 'disabled'
        self.console.print(f'[blue]Streaming mode {status}[/blue]')
        return True

    async def _cmd_settings(self) -> bool:
        self.console.print(Panel(f'Current Settings:\n- Model: {self.config.model or 'default'}\n- Index: {self.config.index or 'default'}\n- Context Size: {self.config.max_context_size}\n- Base URL: {self.config.base_url}\n- Max Retries: {self.config.max_retries}\n- Retry Delay: {self.config.retry_delay}s\n- Streaming: {('enabled' if self.config.streaming else 'disabled')}\n            ', title='Settings', border_style='blue'))
        return True

    async def _cmd_retry(self) -> bool:
        if not self.last_query:
            self.console.print('[red]No previous query to retry[/red]')
            return True
        self.console.print('[blue]Retrying last query...[/blue]')
        await self._handle_query(self.last_query, self.last_context)
        return True

    async def process_command(self, command: str) -> bool:
        cmd_func = self.commands.get(command.lower())
        if cmd_func:
            return await cmd_func()
        self.console.print(f'[blue]Unknown command: {command}[/blue]')
        return True

def __init__(self, config: Config):
    self.config = config
    self.theme = Theme({'user': 'green', 'assistant': 'blue', 'system': 'yellow', 'error': 'red'})
    self.console = Console(theme=self.theme, force_terminal=True)
    self.conversation_context: Deque[Dict[str, str]] = deque(maxlen=self.config.max_context_size)
    self.message_history: List[Message] = []
    self.commands = {'/quit': self._cmd_quit, '/clear': self._cmd_clear, '/history': self._cmd_history, '/help': self._cmd_help, '/context': self._cmd_context, '/model': self._cmd_model, '/index': self._cmd_index, '/settings': self._cmd_settings, '/retry': self._cmd_retry, '/stream': self._cmd_stream}
    self.last_query = None
    self.last_context = None

@dataclass
class PipelineConfig:
    provider: str
    embedding_model: str
    es_url: str
    es_index: str
    es_basic_auth_user: Optional[str] = None
    es_basic_auth_password: Optional[str] = None
    ollama_url: Optional[str] = None
    hf_api_key: Optional[str] = None

    def __post_init__(self):
        if self.provider not in [ModelProvider.OLLAMA, ModelProvider.HUGGINGFACE]:
            raise ValueError(f'Unsupported provider: {self.provider}')
        if self.provider == ModelProvider.OLLAMA and (not self.ollama_url):
            raise ValueError('Ollama URL is required when using Ollama provider')
        if self.provider == ModelProvider.HUGGINGFACE and (not self.hf_api_key):
            raise ValueError('HuggingFace API key is required when using HuggingFace provider')

def __post_init__(self):
    if self.provider not in [ModelProvider.OLLAMA, ModelProvider.HUGGINGFACE]:
        raise ValueError(f'Unsupported provider: {self.provider}')
    if self.provider == ModelProvider.OLLAMA and (not self.ollama_url):
        raise ValueError('Ollama URL is required when using Ollama provider')
    if self.provider == ModelProvider.HUGGINGFACE and (not self.hf_api_key):
        raise ValueError('HuggingFace API key is required when using HuggingFace provider')

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

class WebScraper:

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.base_url = config.base_url
        self.base_domain = urlparse(config.base_url).netloc
        self.output_dir = Path(config.output_dir) / self.base_domain
        self.visited_urls = set()
        self._403_encountered = False
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self._setup_logging()

    def _setup_logging(self):
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger = logging.getLogger(f'scraper_{self.base_domain}')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    def sanitize_filename(self, url: str) -> str:
        parsed_url = urlparse(url)
        path = parsed_url.path.replace(self.base_url, '')
        if not path or path == '/':
            path = 'index'
        path = path.lstrip('/').replace('/', '_')
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            param_parts = []
            for key in sorted(query_params.keys()):
                clean_key = re.sub('[^a-zA-Z0-9]+', '_', key).strip('_')
                values = sorted(query_params[key])
                for value in values:
                    clean_value = re.sub('[^a-zA-Z0-9]+', '_', value).strip('_')
                    if clean_value:
                        param_parts.append(f'{clean_key}_{clean_value}')
                    else:
                        param_parts.append(clean_key)
            if param_parts:
                path = f'{path}__' + '__'.join(param_parts)
        while '__' in path:
            path = path.replace('__', '_')
        path = re.sub('[<>:"/\\\\|?*]', '_', path)
        path = path.strip('_. ')
        if not path:
            path = 'index'
        return f'{path}.md'

    async def handle_403(self, url: str, attempt: int) -> None:
        if not self._403_encountered:
            self._403_encountered = True
            self.logger.warning('First 403 error encountered, reducing request rate')
            self.semaphore = asyncio.Semaphore(max(1, self.config.max_concurrent_requests // 2))
        delay = round(self.config.retry_403_delay * 2 ** attempt * (0.5 + random.random()), 2)
        self.logger.info(f'Received 403 for {url}, waiting {delay} seconds before retry')
        await asyncio.sleep(delay)

    async def fetch_page(self, session: aiohttp.ClientSession, url: str) -> Tuple[Optional[str], int]:
        async with self.semaphore:
            for attempt in range(self.config.max_retries):
                try:
                    if url.startswith('file://'):
                        path = urlparse(url).path
                        try:
                            with open(path, 'r', encoding='utf-8') as f:
                                return (f.read(), 200)
                        except Exception as e:
                            self.logger.error(f'Error reading local file {path}: {str(e)}')
                            return (None, -1)
                    timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                    await asyncio.sleep(random.uniform(self.config.min_delay, self.config.max_delay))
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            return (await response.text(), 200)
                        elif response.status == 403:
                            if attempt < self.config.max_403_retries:
                                await self.handle_403(url, attempt)
                                continue
                            else:
                                self.logger.error(f'Max 403 retries exceeded for {url}')
                                return (None, 403)
                        else:
                            self.logger.warning(f'Failed to fetch {url}, status code: {response.status}, attempt {attempt + 1}/{self.config.max_retries}')
                except Exception as e:
                    self.logger.error(f'Error fetching {url}: {str(e)}, attempt {attempt + 1}/{self.config.max_retries}')
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt * (0.5 + random.random()))
        return (None, -1)

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            sorted_params = []
            for key in sorted(query_params.keys()):
                values = sorted(query_params[key])
                for value in values:
                    sorted_params.append((key, value))
            new_query = urlencode(sorted_params)
            return f'{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}'
        return url

    def extract_links(self, html: str, current_url: str) -> List[str]:
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        valid_links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(current_url, href)
            parsed_url = urlparse(absolute_url)
            if parsed_url.netloc != self.base_domain or 'javascript:' in href or href.startswith('mailto:') or any((href.endswith(ext) for ext in self.config.excluded_extensions)):
                continue
            cleaned_url = absolute_url.split('#')[0]
            normalized_url = self.normalize_url(cleaned_url)
            if normalized_url not in self.visited_urls:
                valid_links.add(normalized_url)
        return list(valid_links)

    async def process_page(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        normalized_url = self.normalize_url(url)
        if normalized_url in self.visited_urls:
            return []
        self.visited_urls.add(normalized_url)
        self.logger.info(f'Processing {url}')
        html, status = await self.fetch_page(session, url)
        if not html:
            if status == 403:
                self.logger.warning(f'Skipping {url} due to persistent 403 error')
            return []
        content = trafilatura.extract(html, include_comments=False, include_tables=True, include_formatting=True)
        if content:
            filename = self.sanitize_filename(url)
            output_path = self.output_dir / filename
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.write(f'\n\nSource URL: {url}\n')
                self.logger.info(f'Saved content to {output_path}')
            except Exception as e:
                self.logger.error(f'Error saving content for {url}: {str(e)}')
        return self.extract_links(html, url)

    async def run(self):
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            urls_to_process = [self.base_url]
            while urls_to_process:
                batch_size = max(1, int(self.config.batch_size * (1 + random.uniform(-self.config.batch_size_variance, self.config.batch_size_variance))))
                urls_batch = random.sample(urls_to_process, min(batch_size, len(urls_to_process)))
                urls_to_process = [url for url in urls_to_process if url not in urls_batch]
                tasks = [self.process_page(session, url) for url in urls_batch]
                results = await asyncio.gather(*tasks)
                for new_urls in results:
                    random.shuffle(new_urls)
                    urls_to_process.extend([url for url in new_urls if url not in self.visited_urls])
                delay = self.config.delay_between_batches * (0.5 + random.random())
                await asyncio.sleep(delay)
        self.logger.info(f'Scraping completed. Processed {len(self.visited_urls)} pages.')

def _setup_logging(self):
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    self.logger = logging.getLogger(f'scraper_{self.base_domain}')
    self.logger.setLevel(logging.INFO)
    self.logger.addHandler(console_handler)

class EnvManager:

    def __init__(self, config: Optional[EnvManagerConfig]=None):
        self.console = Console(force_terminal=True, width=130)
        self.config = config or EnvManagerConfig()
        if self.config.debug:
            logger.setLevel(logging.DEBUG)
        self.styles = {'header': Style(color='bright_white', bold=True), 'key': Style(color='cyan', bold=True), 'value': Style(color='green'), 'type': Style(color='yellow'), 'description': Style(color='bright_black'), 'prompt': Style(color='bright_magenta', bold=True), 'error': Style(color='red', bold=True), 'success': Style(color='bright_green', bold=True), 'even_row': Style(bgcolor='grey7'), 'odd_row': Style()}

    def parse_type(self, value: str) -> Tuple[str, str]:
        if value.lower() in ('true', 'false'):
            return ('bool', value.lower())
        try:
            float(value)
            return ('float', value) if '.' in value else ('int', value)
        except ValueError:
            return ('string', value)

    def parse_env_file(self, file_path: Path) -> Dict[str, EnvVariable]:
        env_vars: Dict[str, EnvVariable] = {}
        pending_comments: List[str] = []
        for line in file_path.read_text().splitlines():
            line = line.strip()
            if not line:
                pending_comments = []
                continue
            if line.startswith('#'):
                if not re.match('^#\\s*[A-Za-z_][A-Za-z0-9_]*=', line):
                    comment = line[1:].strip()
                    if comment:
                        pending_comments.append(comment)
                continue
            match = re.match('^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
            if match:
                key, value = match.groups()
                value = value.strip('"').strip("'")
                var_type, processed_value = self.parse_type(value)
                description = None
                if pending_comments:
                    description = '\n'.join(pending_comments)
                env_vars[key] = EnvVariable(key=key, value=processed_value, description=description, var_type=var_type)
                pending_comments = []
        return env_vars

    def is_blocklisted(self, path: Path) -> bool:
        try:
            relative_path = path.relative_to(self.config.start_path)
            path_str = str(relative_path).replace('\\', '/')
            for blocklist_pattern in self.config.blocklist_paths:
                pattern = blocklist_pattern.replace('\\', '/')
                if path_str == pattern or path_str.startswith(f'{pattern}/') or f'/{pattern}/' in f'/{path_str}/':
                    return True
            return False
        except ValueError:
            return False

    def find_env_files(self) -> List[Path]:
        env_files = []
        for pattern in self.config.env_patterns:
            for path in self.config.start_path.rglob(pattern):
                if path.is_file() and (not any((path.match(exc) for exc in self.config.exclude_patterns))) and (not self.is_blocklisted(path)):
                    env_files.append(path)
        return sorted(env_files)

    def categorize_env_files(self, env_files: List[Path]) -> List[EnvFile]:
        categorized_files = []
        start_path = self.config.start_path.resolve()
        for idx, file_path in enumerate(env_files, 1):
            service = file_path.parent.name
            relative_depth = len(file_path.resolve().relative_to(start_path).parts) - 1
            categorized_files.append(EnvFile(path=file_path, service=service, index=idx, relative_depth=relative_depth))
        return sorted(categorized_files, key=lambda x: x.path.name)

    def display_env_files(self, env_files: List[EnvFile]) -> None:
        table = Table(show_header=True, header_style=self.styles['header'], box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1))
        table.add_column('#', style='bright_blue', justify='center', width=3, no_wrap=True)
        table.add_column('Service', style='bright_yellow', width=15, no_wrap=True)
        if self.config.show_full_path:
            table.add_column('Path', style='bright_white', overflow='fold')
        current_service = None
        for i, env_file in enumerate(env_files):
            row_style = self.styles['even_row'] if i % 2 == 0 else self.styles['odd_row']
            if current_service != env_file.service:
                current_service = env_file.service
            relative_path = env_file.path.relative_to(self.config.start_path)
            if self.config.show_full_path:
                table.add_row(str(env_file.index), Text(env_file.service.capitalize(), style=self.styles['key']), Text(str(relative_path), style=self.styles['value']), style=row_style)
            else:
                table.add_row(str(env_file.index), Text(env_file.service.capitalize(), style=self.styles['key']), style=row_style)
        self.console.print('\n')
        self.console.print(Panel(table, title='[bold]Environment Files[/bold]', border_style='bright_blue', padding=(0, 0)))

    def prompt_value(self, var: EnvVariable) -> Optional[str]:
        self.console.print('\n')
        panel = Panel(f'Type: [yellow]{var.var_type}[/yellow]\nCurrent: [green]{var.value}[/green]', title=f'[bold cyan]{var.key}[/bold cyan]', border_style='bright_blue', padding=(1, 2))
        self.console.print(panel)
        try:
            if var.var_type == 'bool':
                value = str(Confirm.ask(Text('New value', style=self.styles['prompt']), default=var.value.lower() == 'true')).lower()
            else:
                value = Prompt.ask(Text('New value', style=self.styles['prompt']), default=var.value, show_default=False)
                if value == var.value:
                    return None
        except KeyboardInterrupt:
            return None
        try:
            if var.var_type == 'int':
                int(value)
            elif var.var_type == 'float':
                float(value)
            return value
        except ValueError:
            if var.var_type in ('int', 'float'):
                self.console.print(Text(f'Invalid {var.var_type}', style=self.styles['error']))
                return self.prompt_value(var)
        return value

    def display_vars(self, env_vars: Dict[str, EnvVariable], file_path: Path) -> None:
        table = Table(show_header=True, header_style=self.styles['header'], box=box.SIMPLE_HEAD, expand=True, show_edge=False, padding=(0, 1))
        table.add_column('#', style='bright_blue', no_wrap=True)
        table.add_column('Key', style=self.styles['key'], overflow='fold')
        table.add_column('Value', style=self.styles['value'], overflow='fold')
        table.add_column('Type', style=self.styles['type'], no_wrap=True)
        table.add_column('Description', style=self.styles['description'], overflow='fold')
        for idx, var in enumerate(env_vars.values(), 1):
            row_style = self.styles['even_row'] if idx % 2 == 0 else self.styles['odd_row']
            table.add_row(str(idx), var.key, var.value, var.var_type, var.description or '', style=row_style)
        self.console.print('\n')
        self.console.print(Panel(table, title=f'[bold]{file_path.name}[/bold]', subtitle=f'[dim]{file_path.parent}[/dim]', border_style='bright_blue', padding=(0, 0)))

    def save_env_file(self, file_path: Path, env_vars: Dict[str, EnvVariable]) -> None:
        content = file_path.read_text()
        for key, var in env_vars.items():
            pattern = f'^{re.escape(key)}\\s*=\\s*[^\n]*$'
            replacement = f'{key}={var.value}'
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        file_path.write_text(content)
        self.console.print('\n')
        self.console.print(Panel(Text('✓ Changes saved successfully', style=self.styles['success']), border_style='bright_green', padding=(1, 1)))

    def run(self) -> None:
        try:
            while True:
                raw_env_files = self.find_env_files()
                if not raw_env_files:
                    raise FileNotFoundError('No .env files found')
                env_files = self.categorize_env_files(raw_env_files)
                self.display_env_files(env_files)
                selection = Prompt.ask(Text('\nSelect file to edit', style=self.styles['prompt']), default='1', show_default=True)
                if selection == '0':
                    break
                try:
                    selection = int(selection)
                    if not 1 <= selection <= len(env_files):
                        raise ValueError()
                except ValueError:
                    self.console.print(Text('Invalid selection', style=self.styles['error']))
                    continue
                selected_file = next((f.path for f in env_files if f.index == selection))
                env_vars = self.parse_env_file(selected_file)
                modified = False
                while True:
                    var_keys = list(env_vars.keys())
                    self.display_vars(env_vars, selected_file)
                    try:
                        var_selection = Prompt.ask(Text('\nVariable to edit (0 to finish)', style=self.styles['prompt']), default='0')
                        if var_selection == '0':
                            break
                        var_selection = int(var_selection)
                        if not 1 <= var_selection <= len(var_keys):
                            raise ValueError()
                        selected_key = var_keys[var_selection - 1]
                        selected_var = env_vars[selected_key]
                        new_value = self.prompt_value(selected_var)
                        if new_value is not None:
                            env_vars[selected_key].value = new_value
                            modified = True
                    except ValueError:
                        self.console.print(Text('Invalid selection', style=self.styles['error']))
                if modified and Confirm.ask(Text('\nSave changes?', style=self.styles['prompt'])):
                    self.save_env_file(selected_file, env_vars)
                    self.display_vars(env_vars, selected_file)
                else:
                    self.console.print(Panel(Text('Changes discarded', style='yellow'), border_style='yellow', padding=(1, 1)))
        except KeyboardInterrupt:
            self.console.print('\n')
            self.console.print(Panel(Text('Operation cancelled', style='yellow'), border_style='yellow', padding=(1, 1)))
        except Exception as e:
            logger.error(f'Error: {str(e)}')
            raise

def __init__(self, config: Optional[EnvManagerConfig]=None):
    self.console = Console(force_terminal=True, width=130)
    self.config = config or EnvManagerConfig()
    if self.config.debug:
        logger.setLevel(logging.DEBUG)
    self.styles = {'header': Style(color='bright_white', bold=True), 'key': Style(color='cyan', bold=True), 'value': Style(color='green'), 'type': Style(color='yellow'), 'description': Style(color='bright_black'), 'prompt': Style(color='bright_magenta', bold=True), 'error': Style(color='red', bold=True), 'success': Style(color='bright_green', bold=True), 'even_row': Style(bgcolor='grey7'), 'odd_row': Style()}

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

def __init__(self, es_url: str, es_index: str, es_basic_auth_user: str, es_basic_auth_password: str):
    self.logger = logging.getLogger(__name__)
    self.es_url = es_url
    self.es_index = es_index
    self.es_basic_auth_user = es_basic_auth_user
    self.es_basic_auth_password = es_basic_auth_password
    self.document_store = None

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

def __init__(self, ollama_url: str, allow_model_pull: bool):
    self.logger = logging.getLogger(__name__)
    self.ollama_url = ollama_url
    self.allow_model_pull = allow_model_pull

@dataclass
class QueryPipelineConfig:
    """Base configuration for all pipelines."""
    es_url: str
    provider: str = field(default=ModelProvider.OLLAMA)
    ollama_url: Optional[str] = None
    hf_api_key: Optional[str] = field(default_factory=_default_none)
    embedding_model: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    allow_model_pull: bool = field(default=True)
    es_index: Optional[str] = None
    es_top_k: Optional[int] = None
    es_num_candidates: Optional[int] = None
    es_basic_auth_user: Optional[str] = None
    es_basic_auth_password: Optional[str] = None
    enable_conversation_logs: Optional[bool] = True
    context_window: Optional[int] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    min_p: Optional[float] = None
    mirostat: Optional[int] = None
    mirostat_eta: Optional[float] = None
    mirostat_tau: Optional[float] = None
    repeat_last_n: Optional[int] = None
    repeat_penalty: Optional[float] = None
    num_predict: Optional[int] = None
    tfs_z: Optional[float] = None
    stop_sequence: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.provider == ModelProvider.HUGGINGFACE and (not self.hf_api_key):
            raise ValueError('HuggingFace API key is required when using HuggingFace provider')
        if self.provider not in [ModelProvider.OLLAMA, ModelProvider.HUGGINGFACE]:
            raise ValueError(f'Unsupported provider: {self.provider}')

def __post_init__(self):
    """Validate configuration after initialization."""
    if self.provider == ModelProvider.HUGGINGFACE and (not self.hf_api_key):
        raise ValueError('HuggingFace API key is required when using HuggingFace provider')
    if self.provider not in [ModelProvider.OLLAMA, ModelProvider.HUGGINGFACE]:
        raise ValueError(f'Unsupported provider: {self.provider}')

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

def __init__(self, config: QueryPipelineConfig, streaming_callback=None):
    self.logger = logging.getLogger(__name__)
    self.config = config
    self._streaming_callback = streaming_callback
    self.query_pipeline = None
    self._init_conversation_logger()
    self._init_document_store()
    self._init_model_manager()
    self.component_factory = PipelineComponentFactory(config, self.document_store, streaming_callback)

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

