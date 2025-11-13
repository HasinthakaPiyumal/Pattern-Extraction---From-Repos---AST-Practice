# Cluster 0

def log_info(message):
    print(f'{Colors.GREEN}[INFO]{Colors.NC} {message}')

def log_warning(message):
    print(f'{Colors.YELLOW}[WARN]{Colors.NC} {message}')

def log_error(message):
    print(f'{Colors.RED}[ERROR]{Colors.NC} {message}')

class ApiMirrorTester:

    def __init__(self, Chipper_api_base: str, ollama_api_base: str='http://localhost:11434', verify_ssl: bool=True):
        self.Chipper_api_base = Chipper_api_base.rstrip('/')
        self.ollama_api_base = ollama_api_base.rstrip('/')
        self.verify_ssl = verify_ssl
        self.endpoints = [EndpointConfig(path='/api/generate', method='POST', sample_payload={'model': 'llama2', 'prompt': 'Why is the sky blue?', 'stream': False}), EndpointConfig(path='/api/chat', method='POST', sample_payload={'model': 'llama2', 'messages': [{'role': 'user', 'content': 'What is the capital of France?'}], 'stream': True}), EndpointConfig(path='/api/tags', method='GET'), EndpointConfig(path='/api/pull', method='POST', sample_payload={'name': 'llama2'})]

    async def test_endpoint(self, base_url: str, endpoint: EndpointConfig) -> ApiResponse:
        """Test a single endpoint and return its response."""
        print(f'\nTesting {base_url}{endpoint.path}...')
        url = f'{base_url}{endpoint.path}'
        headers = {'Content-Type': 'application/json'} if endpoint.sample_payload else {}
        connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.request(method=endpoint.method, url=url, json=endpoint.sample_payload, headers=headers) as response:
                if endpoint.path == '/api/chat' and endpoint.sample_payload.get('stream', False):
                    print(f'Reading streaming response from {base_url}...')
                    chunks = []
                    chunk_count = 0
                    async for line in response.content:
                        if line:
                            chunk = line.decode().strip()
                            if chunk:
                                try:
                                    parsed_chunk = json.loads(chunk)
                                    chunks.append(parsed_chunk)
                                    chunk_count += 1
                                    if chunk_count % 5 == 0:
                                        print(f'Received {chunk_count} chunks from {base_url}...')
                                except json.JSONDecodeError:
                                    print(f'Warning: Skipping invalid JSON chunk from {base_url}: {chunk[:100]}...')
                    body = chunks[-1] if chunks else {}
                    print(f'Completed streaming for {base_url}. Received {chunk_count} total chunks.')
                else:
                    body = await response.json()
                return ApiResponse(status=response.status, headers=dict(response.headers), body=body)

    def compare_responses(self, Chipper_response: ApiResponse, ollama_response: ApiResponse) -> tuple[float, List[str]]:
        match_score = 0
        differences = []
        if Chipper_response.status == ollama_response.status:
            match_score += 0.25
        else:
            differences.append(f'Status code mismatch: {Chipper_response.status} vs {ollama_response.status}')
        Chipper_content_type = Chipper_response.headers.get('content-type', '')
        ollama_content_type = ollama_response.headers.get('content-type', '')
        if Chipper_content_type == ollama_content_type:
            match_score += 0.25
        else:
            differences.append(f'Content-Type header mismatch: {Chipper_content_type} vs {ollama_content_type}')
        Chipper_keys = set(Chipper_response.body.keys())
        ollama_keys = set(ollama_response.body.keys())
        common_keys = Chipper_keys & ollama_keys
        structure_score = len(common_keys) / max(len(Chipper_keys), len(ollama_keys))
        match_score += structure_score * 0.5
        missing_keys = ollama_keys - Chipper_keys
        extra_keys = Chipper_keys - ollama_keys
        if missing_keys:
            differences.append(f'Missing fields: {', '.join(missing_keys)}')
        if extra_keys:
            differences.append(f'Extra fields: {', '.join(extra_keys)}')
        return (round(match_score, 2), differences)

    async def compare_apis(self) -> List[ComparisonResult]:
        """Compare Chipper API against the Ollama API for all endpoints."""
        print('\nStarting API comparison...')
        total_endpoints = len(self.endpoints)
        results = []
        for idx, endpoint in enumerate(self.endpoints, 1):
            print(f'\nTesting endpoint {idx}/{total_endpoints}: {endpoint.method} {endpoint.path}')
            try:
                print('\nTesting Chipper API endpoint...')
                Chipper_response = await self.test_endpoint(self.Chipper_api_base, endpoint)
                print('\nTesting Ollama API endpoint...')
                ollama_response = await self.test_endpoint(self.ollama_api_base, endpoint)
                match_score, differences = self.compare_responses(Chipper_response, ollama_response)
                results.append(ComparisonResult(endpoint=endpoint.path, method=endpoint.method, match_score=match_score, differences=differences, Chipper_response=Chipper_response, ollama_response=ollama_response))
            except Exception as e:
                results.append(ComparisonResult(endpoint=endpoint.path, method=endpoint.method, match_score=0.0, differences=[], error=str(e)))
        return results

    def print_results(self, results: List[ComparisonResult]):
        """Print the comparison results in a readable format."""
        print('\nAPI Comparison Results:')
        print('=' * 80)
        for result in results:
            print(f'\nEndpoint: {result.method} {result.endpoint}')
            print('-' * 40)
            if result.error:
                print(f'Error: {result.error}')
                continue
            print(f'Match Score: {result.match_score * 100}%')
            if result.differences:
                print('\nDifferences found:')
                for diff in result.differences:
                    print(f'- {diff}')
            else:
                print('\nNo differences found!')

def print_results(self, results: List[ComparisonResult]):
    """Print the comparison results in a readable format."""
    print('\nAPI Comparison Results:')
    print('=' * 80)
    for result in results:
        print(f'\nEndpoint: {result.method} {result.endpoint}')
        print('-' * 40)
        if result.error:
            print(f'Error: {result.error}')
            continue
        print(f'Match Score: {result.match_score * 100}%')
        if result.differences:
            print('\nDifferences found:')
            for diff in result.differences:
                print(f'- {diff}')
        else:
            print('\nNo differences found!')

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

def log_args(args):
    logger.info('Configuration:')
    config_dict = {'Elasticsearch URL': args.es_url, 'Ollama URL': args.ollama_url, 'Embedding Model': args.embedding_model, 'Document Path': args.path or 'Not specified', 'File Extensions': ', '.join(args.extensions), 'Debug Mode': args.debug}
    for key, value in config_dict.items():
        logger.info(f'{key}: {value}')

def show_welcome():
    RED = '\x1b[31m'
    YELLOW = '\x1b[33m'
    RESET = '\x1b[0m'
    print('\n', flush=True)
    print(f'{RED}', flush=True)
    print('        __    _                      ', flush=True)
    print('  _____/ /_  (_)___  ____  ___  _____', flush=True)
    print(' / ___/ __ \\/ / __ \\/ __ \\/ _ \\/ ___/', flush=True)
    print('/ /__/ / / / / /_/ / /_/ /  __/ /    ', flush=True)
    print('\\___/_/ /_/_/ .___/ .___/\\___/_/     ', flush=True)
    print('           /_/   /_/                 ', flush=True)
    print(f'{RESET}', flush=True)
    print(f'{YELLOW}       Chipper Embed {APP_VERSION}.{BUILD_NUMBER}', flush=True)
    print(f'{RESET}\n', flush=True)

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

def show_welcome():
    GREEN = '\x1b[32m'
    CYAN = '\x1b[36m'
    RESET = '\x1b[0m'
    print('\n', flush=True)
    print(f'{GREEN}', flush=True)
    print('        __    _                      ', flush=True)
    print('  _____/ /_  (_)___  ____  ___  _____', flush=True)
    print(' / ___/ __ \\/ / __ \\/ __ \\/ _ \\/ ___/', flush=True)
    print('/ /__/ / / / / /_/ / /_/ /  __/ /    ', flush=True)
    print('\\___/_/ /_/_/ .___/ .___/\\___/_/     ', flush=True)
    print('           /_/   /_/                 ', flush=True)
    print(f'{RESET}', flush=True)
    print(f'{CYAN}       Chipper Scrape {APP_VERSION}.{BUILD_NUMBER}', flush=True)
    print(f'{RESET}\n', flush=True)

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

def parse_type(self, value: str) -> Tuple[str, str]:
    if value.lower() in ('true', 'false'):
        return ('bool', value.lower())
    try:
        float(value)
        return ('float', value) if '.' in value else ('int', value)
    except ValueError:
        return ('string', value)

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

def show_welcome():
    PURPLE = '\x1b[35m'
    CYAN = '\x1b[36m'
    RESET = '\x1b[0m'
    print('\n', flush=True)
    print(f'{PURPLE}', flush=True)
    print('        __    _                      ', flush=True)
    print('  _____/ /_  (_)___  ____  ___  _____', flush=True)
    print(' / ___/ __ \\/ / __ \\/ __ \\/ _ \\/ ___/', flush=True)
    print('/ /__/ / / / / /_/ / /_/ /  __/ /    ', flush=True)
    print('\\___/_/ /_/_/ .___/ .___/\\___/_/     ', flush=True)
    print('           /_/   /_/                 ', flush=True)
    print(f'{RESET}', flush=True)
    print(f'{CYAN}       Chipper API {APP_VERSION}.{BUILD_NUMBER}', flush=True)
    print(f'{RESET}\n', flush=True)

def show_welcome():
    PURPLE = '\x1b[34m'
    CYAN = '\x1b[36m'
    RESET = '\x1b[0m'
    print('\n', flush=True)
    print(f'{PURPLE}', flush=True)
    print('        __    _                      ', flush=True)
    print('  _____/ /_  (_)___  ____  ___  _____', flush=True)
    print(' / ___/ __ \\/ / __ \\/ __ \\/ _ \\/ ___/', flush=True)
    print('/ /__/ / / / / /_/ / /_/ /  __/ /    ', flush=True)
    print('\\___/_/ /_/_/ .___/ .___/\\___/_/     ', flush=True)
    print('           /_/   /_/                 ', flush=True)
    print(f'{RESET}', flush=True)
    print(f'{CYAN}       Chipper Web {APP_VERSION}.{BUILD_NUMBER}', flush=True)
    print(f'{RESET}\n', flush=True)

