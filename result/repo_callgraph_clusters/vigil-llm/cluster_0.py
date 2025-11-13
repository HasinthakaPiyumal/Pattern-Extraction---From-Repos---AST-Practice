# Cluster 0

def setup_vectordb(conf: Config) -> VectorDB:
    full_config = conf.get_general_config()
    params = full_config.get('vectordb', {})
    params.update(full_config.get('embedding', {}))
    return VectorDB(**params)

def check_field(data, field_name: str, field_type: type, required: bool=True) -> str:
    field_data = data.get(field_name, None)
    if field_data is None:
        if required:
            logger.error(f'Missing "{field_name}" field')
            abort(400, f'Missing "{field_name}" field')
        return None
    if not isinstance(field_data, field_type):
        logger.error(f'Invalid data type; "{field_name}" value must be a {field_type.__name__}')
        abort(400, f'Invalid data type; "{field_name}" value must be a {field_type.__name__}')
    return field_data

class Vigil:
    vectordb: Optional[VectorDB] = None
    embedder: Optional[Callable] = None

    def __init__(self, config_path: str):
        self._config = Config(config_path)
        self._initialize_vectordb()
        self._initialize_embedder()
        self._input_scanners: List[BaseScanner] = self._setup_scanners(self._config.get_scanner_names('input_scanners'))
        self._output_scanners: List[BaseScanner] = self._setup_scanners(self._config.get_scanner_names('output_scanners'))
        self.canary_tokens = CanaryTokens()
        self.input_scanner = self._create_manager(name='input', scanners=self._input_scanners)
        self.output_scanner = self._create_manager(name='output', scanners=self._output_scanners)

    def _initialize_embedder(self):
        full_config = self._config.get_general_config()
        params = full_config.get('embedding', {})
        self.embedder = Embedder(**params)

    def _initialize_vectordb(self):
        full_config = self._config.get_general_config()
        params = full_config.get('vectordb', {})
        params.update(full_config.get('embedding', {}))
        self.vectordb = VectorDB(**params)

    def _setup_scanners(self, scanner_names: List[str]) -> List[BaseScanner]:
        scanners = []
        for name in scanner_names:
            try:
                metadata = ScannerRegistry.get_scanner_metadata(name)
            except ValueError as err:
                logger.error(err)
                raise err
            scanner_config = None
            vectordb = None
            embedder = None
            if metadata.get('requires_config', False):
                scanner_config = self._config.get_scanner_config(name)
            if metadata.get('requires_vectordb', False):
                vectordb = self.vectordb
            if metadata.get('requires_embedding', False):
                embedder = self.embedder
            scanner = ScannerRegistry.create_scanner(name=name, config=scanner_config, vectordb=vectordb, embedder=embedder)
            scanners.append(scanner)
        return scanners

    def _create_manager(self, name: str, scanners: List[BaseScanner]) -> Manager:
        manager_config = self._config.get_general_config()
        auto_update = manager_config.get('auto_update', {}).get('enabled', False)
        update_threshold = int(manager_config.get('auto_update', {}).get('threshold', 3))
        return Manager(name=name, scanners=scanners, auto_update=auto_update, update_threshold=update_threshold, db_client=self.vectordb if auto_update else None)

    @staticmethod
    def from_config(config_path: str) -> 'Vigil':
        return Vigil(config_path=config_path)

def _initialize_embedder(self):
    full_config = self._config.get_general_config()
    params = full_config.get('embedding', {})
    self.embedder = Embedder(**params)

def _initialize_vectordb(self):
    full_config = self._config.get_general_config()
    params = full_config.get('vectordb', {})
    params.update(full_config.get('embedding', {}))
    self.vectordb = VectorDB(**params)

def _setup_scanners(self, scanner_names: List[str]) -> List[BaseScanner]:
    scanners = []
    for name in scanner_names:
        try:
            metadata = ScannerRegistry.get_scanner_metadata(name)
        except ValueError as err:
            logger.error(err)
            raise err
        scanner_config = None
        vectordb = None
        embedder = None
        if metadata.get('requires_config', False):
            scanner_config = self._config.get_scanner_config(name)
        if metadata.get('requires_vectordb', False):
            vectordb = self.vectordb
        if metadata.get('requires_embedding', False):
            embedder = self.embedder
        scanner = ScannerRegistry.create_scanner(name=name, config=scanner_config, vectordb=vectordb, embedder=embedder)
        scanners.append(scanner)
    return scanners

def _create_manager(self, name: str, scanners: List[BaseScanner]) -> Manager:
    manager_config = self._config.get_general_config()
    auto_update = manager_config.get('auto_update', {}).get('enabled', False)
    update_threshold = int(manager_config.get('auto_update', {}).get('threshold', 3))
    return Manager(name=name, scanners=scanners, auto_update=auto_update, update_threshold=update_threshold, db_client=self.vectordb if auto_update else None)

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

def get_val(self, section: str, key: str) -> Optional[str]:
    answer = None
    try:
        answer = self.config.get(section, key)
    except Exception as err:
        logger.error(f'Config file missing section: {section} - {err}')
    return answer

