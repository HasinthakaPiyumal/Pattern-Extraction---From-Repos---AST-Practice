# Cluster 1

def check_ollama_availability(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or 11434
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except (socket.error, ValueError):
        return False

def check_external_ollama_requirement(gpu_profile: str) -> bool:
    system = platform.system()
    release = platform.release()
    log_info(f'Platform: {system}/{release}')
    log_info(f'GPU Profile: {gpu_profile}')
    is_darwin = system in ['Darwin']
    is_cpu_profile = gpu_profile == 'cpu'
    is_amd_linux = gpu_profile == 'amd-linux'
    requires_external = is_darwin or is_cpu_profile or is_amd_linux
    if requires_external:
        log_info(f'Using external Ollama server at {DEFAULT_EXTERNAL_OLLAMA_URL}')
        if not check_ollama_availability(DEFAULT_EXTERNAL_LOCAL_OLLAMA_URL):
            message = "Cannot connect to local Ollama server\n\n--------------------------------------------------------------------------------\n\nThe internal Ollama container is not supported on your platform.\nYou must install and run Ollama manually before using Chipper.\n\n1. Download and install Ollama from: https://ollama.com\n2. Start the Ollama service\n3. Ensure it's running at: " + DEFAULT_EXTERNAL_LOCAL_OLLAMA_URL + '\n\nNote: GPU support in Docker Desktop is currently only available\non Windows with the WSL2 backend\nor via the Linux NVIDIA Container Toolkit.\n\nYou can ignore this message if you are using an external\nOllama endpoint or HuggingFace inference service.\n\n--------------------------------------------------------------------------------\n\n'
            log_warning(message)
            return True
        return True
    is_wsl = 'microsoft' in release.lower()
    if is_wsl:
        log_info('WSL Linux detected')
    return False

def detect_gpu_profile():
    system = platform.system()
    if system == 'Darwin':
        log_info('Detected macOS system')
        return 'metal'
    try:
        subprocess.run(['nvidia-smi'], capture_output=True, check=True)
        log_info('Detected NVIDIA GPU')
        return 'nvidia'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if system == 'Linux':
        if Path('/dev/dri').exists() and Path('/dev/kfd').exists():
            log_info('Detected AMD GPU with ROCm support')
            return 'amd-linux'
    elif system == 'Windows':
        try:
            wmic_output = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], capture_output=True, text=True).stdout
            if 'AMD' in wmic_output or 'Radeon' in wmic_output:
                log_info('Detected AMD GPU')
                return 'amd'
        except Exception:
            pass
    log_warning('No GPU detected or unsupported GPU configuration')
    return 'cpu'

def has_example_api_key_set(env_file):
    try:
        with open(env_file, 'r') as file:
            content = file.read()
        return f'API_KEY={EXAMPLE_API_KEY}' in content
    except Exception as e:
        log_error(f'Failed to read {env_file}: {str(e)}')
        return False

def has_ollama_key(env_file):
    try:
        with open(env_file, 'r') as file:
            content = file.read()
        return f'OLLAMA_URL={DEFAULT_INTERNAL_OLLAMA_URL}' in content
    except Exception as e:
        log_error(f'Failed to read {env_file}: {str(e)}')
        return False

def update_env_file(env_file, updates):
    try:
        with open(env_file, 'r') as file:
            content = file.read()
        for key, value in updates.items():
            if f'{key}=' in content:
                if key == 'API_KEY':
                    content = content.replace(f'{key}={EXAMPLE_API_KEY}', f'{key}={value}')
                elif key == 'OLLAMA_URL':
                    lines = content.split('\n')
                    ollama_found = False
                    for i, line in enumerate(lines):
                        if line.startswith('OLLAMA_URL='):
                            lines[i] = f'OLLAMA_URL={value}'
                            ollama_found = True
                            break
                    if not ollama_found:
                        lines.append(f'OLLAMA_URL={value}')
                    content = '\n'.join(lines)
                else:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(f'{key}='):
                            lines[i] = f'{key}={value}'
                    content = '\n'.join(lines)
            else:
                content += f'\n{key}={value}'
        with open(env_file, 'w') as file:
            file.write(content)
        log_info(f'Updated {env_file}')
    except Exception as e:
        log_error(f'Failed to update {env_file}: {str(e)}')

def create_docker_env(profile):
    docker_dir = Path('docker')
    if not docker_dir.exists():
        docker_dir.mkdir(exist_ok=True)
        log_info('Created docker directory')
    docker_env = docker_dir / '.env'
    env_content = f'# Automatically generated Docker environment file\nCOMPOSE_PROFILES={profile}'
    try:
        with open(docker_env, 'w') as f:
            f.write(env_content)
        log_info(f'Created {docker_env} with profile configuration')
    except Exception as e:
        log_error(f'Failed to create {docker_env}: {str(e)}')

def clean_env_files():
    global SHARED_API_KEY, EXTERNAL_OLLAMA_URL
    SHARED_API_KEY = None
    EXTERNAL_OLLAMA_URL = None
    files_to_remove = ['.env', '.ragignore', '.systemprompt']
    docker_env = Path('docker/.env')
    if docker_env.exists():
        try:
            docker_env.unlink()
            log_info(f'Removed {docker_env}')
        except Exception as e:
            log_error(f'Failed to remove {docker_env}: {str(e)}')
    count = 0
    for pattern in files_to_remove:
        for file in Path('.').rglob(pattern):
            try:
                file.unlink()
                count += 1
                log_info(f'Removed {file}')
            except Exception as e:
                log_error(f'Failed to remove {file}: {str(e)}')
    if count > 0:
        log_info(f'Removed {count} file{('s' if count > 1 else '')}')
    else:
        log_info('No files found to remove')

def copy_example_files():
    example_mappings = {'.env.example': '.env', '.ragignore.example': '.ragignore', '.systemprompt.example': '.systemprompt'}
    found_files = []
    files_needing_update = []
    for example_pattern in example_mappings.keys():
        for example_file in Path('.').rglob(example_pattern):
            actual_file = example_file.with_name(example_mappings[example_pattern])
            found_files.append(actual_file)
            if not actual_file.exists():
                shutil.copy(example_file, actual_file)
                log_info(f'Created {actual_file} from {example_file}')
            if example_pattern == '.env.example' or has_example_api_key_set(str(actual_file)):
                files_needing_update.append(actual_file)
    return (found_files, files_needing_update)

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

def load_blocklist(base_path: str) -> Set[str]:
    blocklist_file = Path(base_path) / '.ragignore'
    default_blocklist = set()
    if blocklist_file.exists():
        try:
            with open(blocklist_file, 'r') as f:
                custom_blocklist = {line.strip() for line in f if line.strip() and (not line.startswith('#'))}
            logger.info(f'Loaded custom blocklist from .ragignore: {custom_blocklist}')
            return default_blocklist.union(custom_blocklist)
        except Exception as e:
            logger.warning(f'Error reading .ragignore file: {e}. Using default blocklist.')
            return default_blocklist
    else:
        logger.info('No .ragignore file found. Using default blocklist.')
        return default_blocklist

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

def load_systemprompt(base_path: str) -> str:
    default_prompt = ''
    env_var_name = 'SYSTEM_PROMPT'
    env_prompt = os.getenv(env_var_name)
    if env_prompt is not None and env_prompt.strip() != '':
        content = env_prompt.strip()
        logger.info(f"Using system prompt from '{env_var_name}' environment variable; content: '{content}'")
        return content
    file = Path(base_path) / '.systemprompt'
    if not file.exists():
        logger.info('No .systemprompt file found. Using default prompt.')
        return default_prompt
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            logger.warning('System prompt file is empty. Using default prompt.')
            return default_prompt
        logger.info(f"Successfully loaded system prompt from {file}; content: '{content}'")
        return content
    except Exception as e:
        logger.error(f'Error reading system prompt file: {e}')
        return default_prompt

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

def __init__(self, system_info: dict, log_dir: str='conversation_logs'):
    """Initialize the conversation logger.

        Args:
            system_info: Dictionary containing system information to be logged
            log_dir: Directory where conversation logs will be stored
        """
    self.log_dir = Path(log_dir)
    self.log_dir.mkdir(parents=True, exist_ok=True)
    self.system_info = system_info

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

def abort_chat(self, session_id: str):
    if session_id in self.abort_flags:
        self.abort_flags[session_id].set()
        logger.info(f'Chat aborted for session {session_id[:8]}...')

