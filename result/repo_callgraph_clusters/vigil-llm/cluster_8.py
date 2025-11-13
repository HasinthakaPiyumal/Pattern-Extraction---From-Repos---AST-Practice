# Cluster 8

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
def get_scanner_names(cls) -> List[str]:
    return list(cls._registry.keys())

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

def __init__(self, threshold: float):
    self.name = 'scanner:sentiment'
    self.threshold = float(threshold)
    self.analyzer = SentimentIntensityAnalyzer()
    logger.success('Loaded scanner')

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

def __init__(self, model: str, threshold: float):
    self.name = 'scanner:transformer'
    self.model_name = model
    self.threshold = float(threshold)
    try:
        self.pipeline = pipeline('text-classification', model=self.model_name)
    except Exception as err:
        logger.error(f'Failed to load model: {err}')
    logger.success(f'Loaded scanner: {self.model_name}')

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

def __init__(self, threshold: float, embedder: Callable):
    self.name = 'scanner:response-similarity'
    self.threshold = float(threshold)
    self.embedder = embedder
    logger.success('Loaded scanner')

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

def __init__(self, db_client: VectorDB, threshold: float):
    self.name = 'scanner:vectordb'
    self.db_client = db_client
    self.threshold = float(threshold)
    logger.success('Loaded scanner')

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

