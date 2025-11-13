# Cluster 6

@app.route('/settings', methods=['GET'])
def show_settings():
    """ Return the current configuration settings """
    logger.info(f'({request.path}) Returning config dictionary')
    config_dict = {s: dict(vigil.config.config.items(s)) for s in vigil.config.config.sections()}
    if 'embedding' in config_dict:
        config_dict['embedding'].pop('openai_api_key', None)
    return jsonify(config_dict)

class Manager:

    def __init__(self, scanners: List[BaseScanner], auto_update: bool=False, update_threshold: int=3, db_client=None, name: str='input'):
        self.name = f'dispatch:{name}'
        self.dispatcher = Scanner(scanners)
        self.auto_update = auto_update
        self.update_threshold = update_threshold
        self.db_client = db_client
        if self.auto_update:
            if self.db_client is None:
                logger.warn(f'{self.name} Auto-update disabled: db client is None')
            else:
                logger.info(f'{self.name} Auto-update vectordb enabled: threshold={self.update_threshold}')

    def perform_scan(self, prompt: str, prompt_response: str=None) -> dict:
        resp = ResponseModel(status='success', prompt=prompt, prompt_response=prompt_response, prompt_entropy=calculate_entropy(prompt))
        resp.uuid = str(resp.uuid)
        if not prompt:
            resp.errors.append('Input prompt value is empty')
            resp.status = 'failed'
            logger.error(f'{self.name} Input prompt value is empty')
            return resp.dict()
        logger.info(f'{self.name} Dispatching scan request id={resp.uuid}')
        scan_results = self.dispatcher.run(prompt=prompt, prompt_response=prompt_response, scan_id={resp.uuid})
        total_matches = 0
        for scanner_name, results in scan_results.items():
            if 'error' in results:
                resp.status = 'partial_success'
                resp.errors.append(f'Error in {scanner_name}: {results['error']}')
            else:
                resp.results[scanner_name] = {'matches': results}
                if len(results) > 0 and scanner_name != 'scanner:sentiment':
                    total_matches += 1
        for scanner_name, message in messages.items():
            if scanner_name in scan_results and len(scan_results[scanner_name]) > 0 and (message not in resp.messages):
                resp.messages.append(message)
        logger.info(f'{self.name} Total scanner matches: {total_matches}')
        if self.auto_update and total_matches >= self.update_threshold:
            logger.info(f'{self.name} (auto-update) Adding detected prompt to db id={resp.uuid}')
            doc_id = self.db_client.add_texts([prompt], [{'uuid': resp.uuid, 'source': 'auto-update', 'timestamp': timestamp_str(), 'threshold': self.update_threshold}])
            logger.success(f'{self.name} (auto-update) Successful doc_id={doc_id} id={resp.uuid}')
        logger.info(f'{self.name} Returning response object id={resp.uuid}')
        return resp.dict()

def perform_scan(self, prompt: str, prompt_response: str=None) -> dict:
    resp = ResponseModel(status='success', prompt=prompt, prompt_response=prompt_response, prompt_entropy=calculate_entropy(prompt))
    resp.uuid = str(resp.uuid)
    if not prompt:
        resp.errors.append('Input prompt value is empty')
        resp.status = 'failed'
        logger.error(f'{self.name} Input prompt value is empty')
        return resp.dict()
    logger.info(f'{self.name} Dispatching scan request id={resp.uuid}')
    scan_results = self.dispatcher.run(prompt=prompt, prompt_response=prompt_response, scan_id={resp.uuid})
    total_matches = 0
    for scanner_name, results in scan_results.items():
        if 'error' in results:
            resp.status = 'partial_success'
            resp.errors.append(f'Error in {scanner_name}: {results['error']}')
        else:
            resp.results[scanner_name] = {'matches': results}
            if len(results) > 0 and scanner_name != 'scanner:sentiment':
                total_matches += 1
    for scanner_name, message in messages.items():
        if scanner_name in scan_results and len(scan_results[scanner_name]) > 0 and (message not in resp.messages):
            resp.messages.append(message)
    logger.info(f'{self.name} Total scanner matches: {total_matches}')
    if self.auto_update and total_matches >= self.update_threshold:
        logger.info(f'{self.name} (auto-update) Adding detected prompt to db id={resp.uuid}')
        doc_id = self.db_client.add_texts([prompt], [{'uuid': resp.uuid, 'source': 'auto-update', 'timestamp': timestamp_str(), 'threshold': self.update_threshold}])
        logger.success(f'{self.name} (auto-update) Successful doc_id={doc_id} id={resp.uuid}')
    logger.info(f'{self.name} Returning response object id={resp.uuid}')
    return resp.dict()

class Scanner:

    def __init__(self, scanners: List[BaseScanner]):
        self.name = 'dispatch:scan'
        self.scanners = scanners

    def run(self, prompt: str, scan_id: uuid.uuid4, prompt_response: str=None) -> Dict:
        response = {}
        for scanner in self.scanners:
            scan_obj = ScanModel(prompt=prompt, prompt_response=prompt_response)
            try:
                logger.info(f'Running scanner: {scanner.name}; id={scan_id}')
                updated = scanner.analyze(scan_obj, scan_id)
                response[scanner.name] = [res.dict() for res in updated.results]
                logger.success(f'Successfully ran scanner: {scanner.name} id={scan_id}')
            except Exception as err:
                logger.error(f'Failed to run scanner: {scanner.name}, Error: {str(err)} id={scan_id}')
                response[scanner.name] = {'error': str(err)}
        return response

def run(self, prompt: str, scan_id: uuid.uuid4, prompt_response: str=None) -> Dict:
    response = {}
    for scanner in self.scanners:
        scan_obj = ScanModel(prompt=prompt, prompt_response=prompt_response)
        try:
            logger.info(f'Running scanner: {scanner.name}; id={scan_id}')
            updated = scanner.analyze(scan_obj, scan_id)
            response[scanner.name] = [res.dict() for res in updated.results]
            logger.success(f'Successfully ran scanner: {scanner.name} id={scan_id}')
        except Exception as err:
            logger.error(f'Failed to run scanner: {scanner.name}, Error: {str(err)} id={scan_id}')
            response[scanner.name] = {'error': str(err)}
    return response

class BaseScanner(ABC):

    def __init__(self, name: str='') -> None:
        self.name = name

    @abstractmethod
    def analyze(self, scan_obj: ScanModel, scan_id: UUID=uuid4()) -> ScanModel:
        raise NotImplementedError('This method needs to be overridden in the subclass.')

    def post_init(self):
        """ Optional post-initialization method """
        pass

@abstractmethod
def analyze(self, scan_obj: ScanModel, scan_id: UUID=uuid4()) -> ScanModel:
    raise NotImplementedError('This method needs to be overridden in the subclass.')

def uuid4_str():
    return str(uuid4())

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

def get_general_config(self):
    return {section: dict(self.config.items(section)) for section in self.config.sections()}

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

def get(self, key: str):
    if key in self.cache:
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    return None

