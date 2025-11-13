# Cluster 12

class ScannerRegistry:
    _registry: Dict[str, dict] = {}

    @classmethod
    def register_scanner(cls, name: str, scanner_class: Type[BaseScanner], requires_config=False, requires_vectordb=False, requires_embedding=False, **metadata):
        cls._registry[name] = {'class': scanner_class, 'requires_config': requires_config, 'requires_vectordb': requires_vectordb, 'requires_embedding': requires_embedding, **metadata}

    @classmethod
    def create_scanner(cls, name: str, config: Optional[dict]=None, vectordb: Optional[Callable]=None, embedder: Optional[Callable]=None, **params) -> BaseScanner:
        if name not in cls._registry:
            raise ValueError(f'No scanner registered with name: {name}')
        scanner_info = cls._registry[name]
        scanner_class = scanner_info['class']
        init_params = {}
        if scanner_info['requires_config']:
            if config is None:
                raise ValueError(f"Config required for scanner '{name}'")
            init_params = config
        if scanner_info['requires_vectordb']:
            if vectordb is None:
                raise ValueError(f"VectorDB required for scanner '{name}'")
            init_params.update({'db_client': vectordb})
        if scanner_info['requires_embedding']:
            if embedder is None:
                raise ValueError(f"Embedder required for scanner '{name}'")
            init_params.update({'embedder': embedder})
        scanner_cls = scanner_class(**init_params)
        if hasattr(scanner_cls, 'post_init'):
            scanner_cls.post_init()
        return scanner_cls

    @classmethod
    def get_scanner_names(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def get_scanner_cls(cls) -> List[Type[BaseScanner]]:
        return [info['class'] for info in cls._registry.values()]

    @classmethod
    def get_scanner_metadata(cls, name: str):
        if name not in cls._registry:
            raise ValueError(f'No scanner registered with name: {name}')
        return cls._registry[name]

@classmethod
def create_scanner(cls, name: str, config: Optional[dict]=None, vectordb: Optional[Callable]=None, embedder: Optional[Callable]=None, **params) -> BaseScanner:
    if name not in cls._registry:
        raise ValueError(f'No scanner registered with name: {name}')
    scanner_info = cls._registry[name]
    scanner_class = scanner_info['class']
    init_params = {}
    if scanner_info['requires_config']:
        if config is None:
            raise ValueError(f"Config required for scanner '{name}'")
        init_params = config
    if scanner_info['requires_vectordb']:
        if vectordb is None:
            raise ValueError(f"VectorDB required for scanner '{name}'")
        init_params.update({'db_client': vectordb})
    if scanner_info['requires_embedding']:
        if embedder is None:
            raise ValueError(f"Embedder required for scanner '{name}'")
        init_params.update({'embedder': embedder})
    scanner_cls = scanner_class(**init_params)
    if hasattr(scanner_cls, 'post_init'):
        scanner_cls.post_init()
    return scanner_cls

@classmethod
def get_scanner_metadata(cls, name: str):
    if name not in cls._registry:
        raise ValueError(f'No scanner registered with name: {name}')
    return cls._registry[name]

class RelevanceScanner(BaseScanner):

    def __init__(self, config_dict: dict):
        self.name = 'scanner:relevance'
        self.prompt_path = config_dict['prompt'] if 'prompt_path' in config_dict else None
        if self.prompt_path is None:
            logger.error(f'[{self.name}] prompt path is not defined; check config')
            raise ValueError('[scanner:relevance] prompt path is not defined')
        self.llm = LLM(model_name=config_dict['model_name'], api_key=config_dict['api_key'] if 'api_key' in config_dict else None, api_base=config_dict['api_base'] if 'api_base' in config_dict else None)

    def load_prompt(self) -> dict:
        logger.info(f'[{self.name}] Loading prompt from {self.prompt_path}')
        with open(self.prompt_path, 'r') as fp:
            data = yaml.safe_load(fp)
        return data

    def analyze(self, input_data: str, scan_id: uuid.uuid4) -> List:
        logger.info(f'[{self.name}] performing scan; id="{scan_id}"')
        prompt = self.load_prompt()['prompt']
        prompt = prompt.format(input_data=input_data)
        try:
            output = self.llm.generate(input_data, content_only=True)
            logger.info(f'[{self.name}] LLM output: {output}')
        except Exception as err:
            logger.error(f'[{self.name}] Failed to perform relevance scan (call to LLM): {err}')
            raise
        return output

def __init__(self, config_dict: dict):
    self.name = 'scanner:relevance'
    self.prompt_path = config_dict['prompt'] if 'prompt_path' in config_dict else None
    if self.prompt_path is None:
        logger.error(f'[{self.name}] prompt path is not defined; check config')
        raise ValueError('[scanner:relevance] prompt path is not defined')
    self.llm = LLM(model_name=config_dict['model_name'], api_key=config_dict['api_key'] if 'api_key' in config_dict else None, api_base=config_dict['api_base'] if 'api_base' in config_dict else None)

class Config:

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.config_file):
            logger.error(f'Config file not found: {self.config_file}')
            raise ValueError(f'Config file not found: {self.config_file}')
        logger.info(f'Loading config file: {self.config_file}')
        self.config.read(config_file)

    def get_val(self, section: str, key: str) -> Optional[str]:
        answer = None
        try:
            answer = self.config.get(section, key)
        except Exception as err:
            logger.error(f'Config file missing section: {section} - {err}')
        return answer

    def get_bool(self, section: str, key: str, default: bool=False) -> bool:
        try:
            return self.config.getboolean(section, key)
        except Exception as err:
            logger.error(f'Failed to parse boolean - returning default "False": {section} - {err}')
            return default

    def get_scanner_config(self, scanner_name):
        return {key: self.get_val(f'scanner:{scanner_name}', key) for key in self.config.options(f'scanner:{scanner_name}')}

    def get_general_config(self):
        return {section: dict(self.config.items(section)) for section in self.config.sections()}

    def get_scanner_names(self, scanner_type: str) -> List[str]:
        return self.get_val('scanners', scanner_type).split(',')

def __init__(self, config_file: str):
    self.config_file = config_file
    self.config = configparser.ConfigParser()
    if not os.path.exists(self.config_file):
        logger.error(f'Config file not found: {self.config_file}')
        raise ValueError(f'Config file not found: {self.config_file}')
    logger.info(f'Loading config file: {self.config_file}')
    self.config.read(config_file)

class LLM:

    def __init__(self, model_name: str, api_key: Optional[str]=None, api_base: Optional[str]=None) -> None:
        self.name = 'llm'
        litellm.api_key = api_key
        self.api_base = api_base
        if model_name not in litellm.model_list:
            logger.error(f'Model name not supported: {model_name}')
            raise ValueError('Model name not supported')
        if not litellm.check_valid_key(model=model_name, api_key=api_key):
            logger.error(f'Invalid API key for model: {model_name}')
            raise ValueError('Invalid API key for model')
        self.model_name = model_name
        logger.info('Loaded LLM API.')

    def generate(self, prompt: str, content_only: Optional[bool]=False) -> Union[str, Dict[str, Any]]:
        """Call configured LLM model with litellm"""
        logger.info(f'Calling model: {self.model_name}')
        messages = [{'content': prompt, 'role': 'user'}]
        try:
            output = litellm.completion(model=self.model_name, messages=messages, api_base=self.api_base if self.api_base else None)
        except Exception as err:
            logger.error('Failed to generate output for input data: {err}')
            raise
        return output['choices'][0]['message']['content'] if content_only else output

def __init__(self, model_name: str, api_key: Optional[str]=None, api_base: Optional[str]=None) -> None:
    self.name = 'llm'
    litellm.api_key = api_key
    self.api_base = api_base
    if model_name not in litellm.model_list:
        logger.error(f'Model name not supported: {model_name}')
        raise ValueError('Model name not supported')
    if not litellm.check_valid_key(model=model_name, api_key=api_key):
        logger.error(f'Invalid API key for model: {model_name}')
        raise ValueError('Invalid API key for model')
    self.model_name = model_name
    logger.info('Loaded LLM API.')

class VectorDB:

    def __init__(self, model: str, collection: str, db_dir: str, n_results: int, openai_key: Optional[str]=None):
        """ Initialize Chroma vector db client """
        self.name = 'database:vector'
        if model == 'openai':
            logger.info('Using OpenAI embedding function')
            self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_key, model_name='text-embedding-ada-002')
        else:
            logger.info(f'Using SentenceTransformer embedding function: {config_dict['embed_fn']}')
            self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
        self.collection = collection
        self.db_dir = db_dir
        self.n_results = int(n_results)
        if not hasattr(self.embed_fn, '__call__'):
            logger.error('Embedding function is not callable')
            raise ValueError('Embedding function is not a function')
        self.client = chromadb.PersistentClient(path=self.db_dir, settings=Settings(anonymized_telemetry=False, allow_reset=True))
        self.collection = self.get_or_create_collection(self.collection)
        logger.success('Loaded database')

    def get_or_create_collection(self, name: str):
        logger.info(f'Using collection: {name}')
        self.collection = self.client.get_or_create_collection(name=name, embedding_function=self.embed_fn, metadata={'hnsw:space': 'cosine'})
        return self.collection

    def add_texts(self, texts: List[str], metadatas: List[dict]):
        success = False
        logger.info(f'Adding {len(texts)} texts')
        ids = [uuid4_str() for _ in range(len(texts))]
        try:
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')
        return (success, ids)

    def add_embeddings(self, texts: List[str], embeddings: List[List], metadatas: List[dict]):
        success = False
        logger.info(f'Adding {len(texts)} embeddings')
        ids = [uuid4_str() for _ in range(len(texts))]
        try:
            self.collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            success = True
        except Exception as err:
            logger.error(f'Failed to add texts to collection: {err}')
        return (success, ids)

    def query(self, text: str):
        logger.info(f'Querying database for: {text}')
        try:
            return self.collection.query(query_texts=[text], n_results=self.n_results)
        except Exception as err:
            logger.error(f'Failed to query database: {err}')

def __init__(self, model: str, collection: str, db_dir: str, n_results: int, openai_key: Optional[str]=None):
    """ Initialize Chroma vector db client """
    self.name = 'database:vector'
    if model == 'openai':
        logger.info('Using OpenAI embedding function')
        self.embed_fn = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_key, model_name='text-embedding-ada-002')
    else:
        logger.info(f'Using SentenceTransformer embedding function: {config_dict['embed_fn']}')
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
    self.collection = collection
    self.db_dir = db_dir
    self.n_results = int(n_results)
    if not hasattr(self.embed_fn, '__call__'):
        logger.error('Embedding function is not callable')
        raise ValueError('Embedding function is not a function')
    self.client = chromadb.PersistentClient(path=self.db_dir, settings=Settings(anonymized_telemetry=False, allow_reset=True))
    self.collection = self.get_or_create_collection(self.collection)
    logger.success('Loaded database')

def get_or_create_collection(self, name: str):
    logger.info(f'Using collection: {name}')
    self.collection = self.client.get_or_create_collection(name=name, embedding_function=self.embed_fn, metadata={'hnsw:space': 'cosine'})
    return self.collection

