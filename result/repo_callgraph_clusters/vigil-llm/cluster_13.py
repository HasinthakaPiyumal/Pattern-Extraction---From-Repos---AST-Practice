# Cluster 13

@Registration.scanner(name='yara', requires_config=True)
class YaraScanner(BaseScanner):

    def __init__(self, rules_dir: str):
        self.name = 'scanner:yara'
        self.rules_dir = rules_dir
        self.compiled_rules = None
        if not os.path.exists(self.rules_dir):
            logger.error(f'Directory not found: {self.rules_dir}')
            raise Exception
        if not os.path.isdir(self.rules_dir):
            logger.error(f'Path is not a valid directory: {self.rules_dir}')
            raise Exception
        self.load_rules()
        logger.success('Loaded scanner')

    def load_rules(self) -> bool:
        """Compile all YARA rules in a directory and store in memory"""
        logger.info(f'Loading rules from directory: {self.rules_dir}')
        rules = os.listdir(self.rules_dir)
        if len(rules) == 0:
            return
        yara_paths = {}
        for _file in rules:
            if self.is_yara_file(_file):
                yara_paths[_file] = os.path.join(self.rules_dir, _file)
        try:
            self.compiled_rules = yara.compile(filepaths=yara_paths)
        except Exception as err:
            logger.error(f'YARA compilation error: {err}')
            raise err

    def is_yara_file(self, file_path: str) -> bool:
        """Check if file is rule by extension"""
        if file_path.lower().endswith('.yara') or file_path.lower().endswith('.yar'):
            return True
        return False

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        """Run scan against input data and return list of YaraMatchs"""
        logger.info(f'Performing scan; id="{scan_id}"')
        if scan_obj.prompt.strip() == '':
            logger.error(f'No input data; id="{scan_id}"')
            return scan_obj
        try:
            matches = self.compiled_rules.match(data=scan_obj.prompt)
        except Exception as err:
            logger.error(f'Failed to perform yara scan; id="{scan_id}" error="{err}"')
            return scan_obj
        for match in matches:
            m = YaraMatch(rule_name=match.rule, tags=match.tags, category=match.meta.get('category', None))
            logger.warning(f'Matched rule rule="{m.rule_name} tags="{m.tags}" category="{m.category}"')
            scan_obj.results.append(m)
        if len(scan_obj.results) == 0:
            logger.info(f'No matches found; id="{scan_id}"')
        return scan_obj

def load_rules(self) -> bool:
    """Compile all YARA rules in a directory and store in memory"""
    logger.info(f'Loading rules from directory: {self.rules_dir}')
    rules = os.listdir(self.rules_dir)
    if len(rules) == 0:
        return
    yara_paths = {}
    for _file in rules:
        if self.is_yara_file(_file):
            yara_paths[_file] = os.path.join(self.rules_dir, _file)
    try:
        self.compiled_rules = yara.compile(filepaths=yara_paths)
    except Exception as err:
        logger.error(f'YARA compilation error: {err}')
        raise err

class Embedder:

    def __init__(self, model: str, openai_key: str=None):
        self.name = 'embedder'
        self.model_name = model
        if model == 'openai':
            logger.info('Using OpenAI')
            if openai_key is None:
                logger.error('No OpenAI API key passed to embedder.')
                raise ValueError('No OpenAI API key provided.')
            self.client = OpenAI(api_key=openai_key)
            try:
                self.client.models.list()
            except Exception as err:
                logger.error(f'Failed to connect to OpenAI API: {err}')
                raise Exception(f'Connection to OpenAI API failed: {err}')
            self.embed_func = self._openai
        else:
            logger.info(f'Using SentenceTransformer: {model}')
            try:
                self.model = SentenceTransformer(model)
                logger.success(f'Loaded model: {model}')
            except Exception as err:
                logger.error(f'Failed to load model: {model} error="{err}"')
                raise ValueError(f'Failed to load SentenceTransformer model: {err}')
            self.embed_func = self._transformer
        logger.success('Loaded embedder')

    def generate(self, input_data: str) -> List:
        logger.info(f'Generating with: {self.model_name}')
        return self.embed_func(input_data)

    def _openai(self, input_data: str) -> List:
        try:
            response = self.client.embeddings.create(input=input_data, model='text-embedding-ada-002')
            data = response.data[0]
            return data.embedding
        except Exception as err:
            logger.error(f'Failed to generate embedding: {err}')
            return []

    def _transformer(self, input_data: str) -> List:
        try:
            results = self.model.encode(input_data).tolist()
            return results
        except Exception as err:
            logger.error(f'Failed to generate embedding: {err}')
            return []

def _openai(self, input_data: str) -> List:
    try:
        response = self.client.embeddings.create(input=input_data, model='text-embedding-ada-002')
        data = response.data[0]
        return data.embedding
    except Exception as err:
        logger.error(f'Failed to generate embedding: {err}')
        return []

def _transformer(self, input_data: str) -> List:
    try:
        results = self.model.encode(input_data).tolist()
        return results
    except Exception as err:
        logger.error(f'Failed to generate embedding: {err}')
        return []

class Loader:

    def __init__(self, vector_db, chunk_size=100):
        self.vector_db = vector_db
        self.chunk_size = chunk_size

    def load_dataset(self, dataset_name: str):
        buffer = []
        logger.info(f'Loading dataset: {dataset_name}')
        try:
            docs_stream = load_dataset(dataset_name, split='train', streaming=True)
        except Exception as err:
            logger.error(f'Error loading dataset: {err}')
            raise
        logger.info('Reading dataset stream ...')
        for doc in docs_stream:
            buffer.append(DatasetEntry(text=doc['text'], embeddings=doc['embeddings'], metadata={'model': doc['model']}))
            if len(buffer) >= self.chunk_size:
                self.process_chunk(buffer)
                buffer.clear()
        if buffer:
            self.process_chunk(buffer)
        logger.info('Finished loading dataset.')

    def process_chunk(self, chunk):
        texts = [doc.text for doc in chunk]
        embeddings = [doc.embeddings for doc in chunk]
        metadatas = [doc.metadata for doc in chunk]
        self.vector_db.add_embeddings(texts, embeddings, metadatas)
        logger.info(f'Processed chunk; {len(chunk)}')

def load_dataset(self, dataset_name: str):
    buffer = []
    logger.info(f'Loading dataset: {dataset_name}')
    try:
        docs_stream = load_dataset(dataset_name, split='train', streaming=True)
    except Exception as err:
        logger.error(f'Error loading dataset: {err}')
        raise
    logger.info('Reading dataset stream ...')
    for doc in docs_stream:
        buffer.append(DatasetEntry(text=doc['text'], embeddings=doc['embeddings'], metadata={'model': doc['model']}))
        if len(buffer) >= self.chunk_size:
            self.process_chunk(buffer)
            buffer.clear()
    if buffer:
        self.process_chunk(buffer)
    logger.info('Finished loading dataset.')

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

def get_bool(self, section: str, key: str, default: bool=False) -> bool:
    try:
        return self.config.getboolean(section, key)
    except Exception as err:
        logger.error(f'Failed to parse boolean - returning default "False": {section} - {err}')
        return default

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

