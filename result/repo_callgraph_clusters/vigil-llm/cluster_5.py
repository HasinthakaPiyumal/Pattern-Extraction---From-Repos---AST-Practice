# Cluster 5

def calculate_entropy(text) -> float:
    prob = [text.count(c) / len(text) for c in set(text)]
    entropy = -sum((p * math.log2(p) for p in prob))
    return entropy

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

@Registration.scanner(name='sentiment', requires_config=True)
class SentimentScanner(BaseScanner):
    """ Sentiment analysis of a prompt and response """

    def __init__(self, threshold: float):
        self.name = 'scanner:sentiment'
        self.threshold = float(threshold)
        self.analyzer = SentimentIntensityAnalyzer()
        logger.success('Loaded scanner')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id="{scan_id}"')
        prompt = scan_obj.prompt if scan_obj.prompt_response is None else scan_obj.prompt_response
        try:
            scores = self.analyzer.polarity_scores(prompt)
            logger.info(f'Sentiment scores: {scores} id="{scan_id}"')
            if scores['neg'] > self.threshold:
                logger.warning(f'Negative sentiment score above threshold; threshold={self.threshold} id="{scan_id}"')
            scan_obj.results.append(SentimentMatch(threshold=self.threshold, compound=scores['compound'], negative=scores['neg'], neutral=scores['neu'], positive=scores['pos']))
        except Exception as err:
            logger.error(f'Analyzer error: {err} id="{scan_id}"')
            return scan_obj
        return scan_obj

def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
    logger.info(f'Performing scan; id="{scan_id}"')
    prompt = scan_obj.prompt if scan_obj.prompt_response is None else scan_obj.prompt_response
    try:
        scores = self.analyzer.polarity_scores(prompt)
        logger.info(f'Sentiment scores: {scores} id="{scan_id}"')
        if scores['neg'] > self.threshold:
            logger.warning(f'Negative sentiment score above threshold; threshold={self.threshold} id="{scan_id}"')
        scan_obj.results.append(SentimentMatch(threshold=self.threshold, compound=scores['compound'], negative=scores['neg'], neutral=scores['neu'], positive=scores['pos']))
    except Exception as err:
        logger.error(f'Analyzer error: {err} id="{scan_id}"')
        return scan_obj
    return scan_obj

@Registration.scanner(name='transformer', requires_config=True)
class TransformerScanner(BaseScanner):

    def __init__(self, model: str, threshold: float):
        self.name = 'scanner:transformer'
        self.model_name = model
        self.threshold = float(threshold)
        try:
            self.pipeline = pipeline('text-classification', model=self.model_name)
        except Exception as err:
            logger.error(f'Failed to load model: {err}')
        logger.success(f'Loaded scanner: {self.model_name}')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id={scan_id}')
        hits = []
        if scan_obj.prompt.strip() == '':
            logger.error(f'No input data; id={scan_id}')
            return scan_obj
        try:
            hits = self.pipeline(scan_obj.prompt)
        except Exception as err:
            logger.error(f'Pipeline error: {err} id={scan_id}')
            return scan_obj
        if len(hits) > 0:
            for rec in hits:
                if rec['label'] == 'INJECTION':
                    if rec['score'] > self.threshold:
                        logger.warning(f'Detected prompt injection; score={rec['score']} threshold={self.threshold} id={scan_id}')
                    else:
                        logger.warning(f'Detected prompt injection below threshold (may warrant manual review);                             score={rec['score']} threshold={self.threshold} id={scan_id}')
                    scan_obj.results.append(ModelMatch(model_name=self.model_name, score=rec['score'], label=rec['label'], threshold=self.threshold))
        else:
            logger.info(f'No hits returned by model; id={scan_id}')
        return scan_obj

def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
    logger.info(f'Performing scan; id={scan_id}')
    hits = []
    if scan_obj.prompt.strip() == '':
        logger.error(f'No input data; id={scan_id}')
        return scan_obj
    try:
        hits = self.pipeline(scan_obj.prompt)
    except Exception as err:
        logger.error(f'Pipeline error: {err} id={scan_id}')
        return scan_obj
    if len(hits) > 0:
        for rec in hits:
            if rec['label'] == 'INJECTION':
                if rec['score'] > self.threshold:
                    logger.warning(f'Detected prompt injection; score={rec['score']} threshold={self.threshold} id={scan_id}')
                else:
                    logger.warning(f'Detected prompt injection below threshold (may warrant manual review);                             score={rec['score']} threshold={self.threshold} id={scan_id}')
                scan_obj.results.append(ModelMatch(model_name=self.model_name, score=rec['score'], label=rec['label'], threshold=self.threshold))
    else:
        logger.info(f'No hits returned by model; id={scan_id}')
    return scan_obj

@Registration.scanner(name='similarity', requires_config=True, requires_embedding=True)
class SimilarityScanner(BaseScanner):
    """ Compare the cosine similarity of the prompt and response """

    def __init__(self, threshold: float, embedder: Callable):
        self.name = 'scanner:response-similarity'
        self.threshold = float(threshold)
        self.embedder = embedder
        logger.success('Loaded scanner')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id={scan_id}')
        input_embedding = self.embedder.generate(scan_obj.prompt)
        output_embedding = self.embedder.generate(scan_obj.prompt_response)
        cosine_score = cosine_similarity(input_embedding, output_embedding)
        if cosine_score > self.threshold:
            m = SimilarityMatch(score=cosine_score, threshold=self.threshold, message='Response is not similar to prompt.')
            logger.warning('Response is not similar to prompt.')
            scan_obj.results.append(m)
        if len(scan_obj.results) == 0:
            logger.info('Response is similar to prompt.')
        return scan_obj

def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
    logger.info(f'Performing scan; id={scan_id}')
    input_embedding = self.embedder.generate(scan_obj.prompt)
    output_embedding = self.embedder.generate(scan_obj.prompt_response)
    cosine_score = cosine_similarity(input_embedding, output_embedding)
    if cosine_score > self.threshold:
        m = SimilarityMatch(score=cosine_score, threshold=self.threshold, message='Response is not similar to prompt.')
        logger.warning('Response is not similar to prompt.')
        scan_obj.results.append(m)
    if len(scan_obj.results) == 0:
        logger.info('Response is similar to prompt.')
    return scan_obj

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

@Registration.scanner(name='vectordb', requires_config=True, requires_vectordb=True)
class VectorScanner(BaseScanner):

    def __init__(self, db_client: VectorDB, threshold: float):
        self.name = 'scanner:vectordb'
        self.db_client = db_client
        self.threshold = float(threshold)
        logger.success('Loaded scanner')

    def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
        logger.info(f'Performing scan; id="{scan_id}"')
        try:
            matches = self.db_client.query(scan_obj.prompt)
        except Exception as err:
            logger.error(f'Failed to perform vector scan; id="{scan_id}" error="{err}"')
            return scan_obj
        existing_texts = []
        for match in zip(matches['documents'][0], matches['metadatas'][0], matches['distances'][0]):
            distance = match[2]
            if distance < self.threshold and match[0] not in existing_texts:
                m = VectorMatch(text=match[0], metadata=match[1], distance=match[2])
                logger.warning(f'Matched vector text="{m.text}" threshold="{self.threshold}" distance="{m.distance}" id="{scan_id}"')
                scan_obj.results.append(m)
                existing_texts.append(m.text)
        if len(scan_obj.results) == 0:
            logger.info(f'No matches found; id="{scan_id}"')
        return scan_obj

def analyze(self, scan_obj: ScanModel, scan_id: uuid.uuid4) -> ScanModel:
    logger.info(f'Performing scan; id="{scan_id}"')
    try:
        matches = self.db_client.query(scan_obj.prompt)
    except Exception as err:
        logger.error(f'Failed to perform vector scan; id="{scan_id}" error="{err}"')
        return scan_obj
    existing_texts = []
    for match in zip(matches['documents'][0], matches['metadatas'][0], matches['distances'][0]):
        distance = match[2]
        if distance < self.threshold and match[0] not in existing_texts:
            m = VectorMatch(text=match[0], metadata=match[1], distance=match[2])
            logger.warning(f'Matched vector text="{m.text}" threshold="{self.threshold}" distance="{m.distance}" id="{scan_id}"')
            scan_obj.results.append(m)
            existing_texts.append(m.text)
    if len(scan_obj.results) == 0:
        logger.info(f'No matches found; id="{scan_id}"')
    return scan_obj

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

def process_chunk(self, chunk):
    texts = [doc.text for doc in chunk]
    embeddings = [doc.embeddings for doc in chunk]
    metadatas = [doc.metadata for doc in chunk]
    self.vector_db.add_embeddings(texts, embeddings, metadatas)
    logger.info(f'Processed chunk; {len(chunk)}')

class CanaryTokens:

    def __init__(self):
        self.tokens = []

    def generate(self, length: int=16, always: bool=False, header: str='<-@!-- {canary} --@!->') -> str:
        """Generate a canary token with optional prefix"""
        token = secrets.token_hex(length // 2)
        result = header.format(canary=token)
        if always:
            result = always_header.format(header=header, canary_token=result)
        return (result, token)

    def add(self, prompt: str, always: bool=False, length: int=16, header: str='<-@!-- {canary} --@!->') -> str:
        """Add canary token to prompt"""
        result, token = self.generate(length=length, always=always, header=header)
        self.tokens.append(token)
        logger.info(f'Adding new canary token to prompt: {token}')
        updated_prompt = result + '\n' + prompt
        return updated_prompt

    def check(self, prompt: str='') -> bool:
        """Check if prompt contains a canary token"""
        for token in self.tokens:
            if token in prompt:
                logger.info(f'Found canary token: {token}')
                return True
        logger.info('No canary token found in prompt.')
        return False

def generate(self, length: int=16, always: bool=False, header: str='<-@!-- {canary} --@!->') -> str:
    """Generate a canary token with optional prefix"""
    token = secrets.token_hex(length // 2)
    result = header.format(canary=token)
    if always:
        result = always_header.format(header=header, canary_token=result)
    return (result, token)

def add(self, prompt: str, always: bool=False, length: int=16, header: str='<-@!-- {canary} --@!->') -> str:
    """Add canary token to prompt"""
    result, token = self.generate(length=length, always=always, header=header)
    self.tokens.append(token)
    logger.info(f'Adding new canary token to prompt: {token}')
    updated_prompt = result + '\n' + prompt
    return updated_prompt

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

def query(self, text: str):
    logger.info(f'Querying database for: {text}')
    try:
        return self.collection.query(query_texts=[text], n_results=self.n_results)
    except Exception as err:
        logger.error(f'Failed to query database: {err}')

class LRUCache:

    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):
        if key in self.cache:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

    def set(self, key: str, value: any):
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

def set(self, key: str, value: any):
    if key in self.cache:
        self.cache.pop(key)
    elif len(self.cache) >= self.capacity:
        self.cache.popitem(last=False)
    self.cache[key] = value

