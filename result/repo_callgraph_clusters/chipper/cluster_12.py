# Cluster 12

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

def finalize(self):
    self.metrics_tracker.log_metrics(self.logger)

