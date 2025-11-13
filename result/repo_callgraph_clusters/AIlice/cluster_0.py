# Cluster 0

def detect_hardware():
    hardwares = []
    try:
        subprocess.run(['nvidia-smi'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        hardwares.append('cuda')
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        subprocess.run(['rocminfo'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        hardwares.append('rocm')
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        subprocess.run(['vulkaninfo'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        hardwares.append('vulkan')
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return hardwares

def StartServices():
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if process.info['cmdline'] and 'ailice.modules' in ' '.join(process.info['cmdline']):
                print(f'killing proc with PID {process.info['pid']}')
                process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    for serviceName, cfg in config.services.items():
        if 'speech' == serviceName and (not config.speechOn):
            continue
        if 'cmd' not in cfg or '' == cfg['cmd'].strip():
            print(f"{serviceName}'s cmd is not configured and will attempt to connect {cfg['addr']} directly.")
            continue
        p = subprocess.Popen(cfg['cmd'], shell=True, cwd=None, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(p)
        print(serviceName, ' started.')
    signal.signal(signal.SIGINT, TerminateSubprocess)
    signal.signal(signal.SIGTERM, TerminateSubprocess)

def GenerateRE4ObjectExpr(typePairs, typeName: str, faultTolerance: bool=False) -> str:
    reMap = {k: v for k, v in ARegexMap.items()}
    reMap['str'] = f'(?:.*?(?=\\|{typeName}>))' if faultTolerance and 1 == len(typePairs) and ('str' == typePairs[0][1]) else ARegexMap['str']
    patternArgs = '\\s*,\\s*'.join([f"""(?:({arg}|\\"{arg}\\"|\\'{arg}\\')\\s*[:=]\\s*)?(?P<{arg}>({reMap[tp]}))""" for arg, tp in typePairs])
    return f'<(?:{typeName})\\|\\s*{patternArgs}\\s*\\|(?:{typeName})>'

def ConstructOptPrompt(func, low: int, high: int, maxLen: int) -> tuple[str, int, int]:
    prompt = None
    n = None
    while low <= high:
        mid = (low + high) // 2
        p, length = func(mid)
        if length < maxLen:
            n = mid
            prompt = p
            low = mid + 1
        else:
            high = mid - 1
    return (prompt, n, length)

class UserContext:
    states = ['init', 'ready', 'released']
    settings = ['agentModelConfig', 'models', 'temperature', 'contextWindowRatio']
    allowedPathes = [['agentModelConfig'], ['models', ['oai', 'groq', 'openrouter', 'apipie', 'deepseek', 'mistral', 'anthropic'], 'apikey'], ['temperature'], ['contextWindowRatio']]

    def __init__(self, userID: str):
        self.userID = userID
        self.config = AConfig()
        self.currentSession = None
        self.context = dict()
        self.speech = None
        self.methodLock = threading.RLock()
        self.machine = LockedMachine(model=self, states=UserContext.states, initial='init')
        self.machine.add_transition(trigger='create', source='init', dest='ready')
        self.machine.add_transition(trigger='release', source='*', dest='released')
        self.machine.add_transition(trigger='session_call', source='ready', dest='ready')
        self.serverPublicFile = None
        self.serverSecretFile = None
        self.serverPublicFile = None
        self.serverSecretFile = None
        logger.debug(f'UserContext initialized for user ID: {userID}')
        return

    def GetPath(self, pathType: str='', sessionName: str=''):
        pathes = {'': '', 'user_config': 'user_config.json', 'certificates': 'certificates', 'sessions': 'sessions', 'session': f'sessions/{sessionName}', 'history': f'sessions/{sessionName}/ailice_history.json'}
        return os.path.join(self.config.chatHistoryPath, str(self.userID), pathes[pathType])

    def StoreConfig(self):
        userCfg = {'agentModelConfig': self.config.agentModelConfig, 'models': {providerName: {k: v for k, v in providerCfg.items() if k != 'modelList'} for providerName, providerCfg in self.config.models.items() if providerName not in ['default']}, 'temperature': self.config.temperature, 'contextWindowRatio': self.config.contextWindowRatio}
        config_path = self.GetPath(pathType='user_config')
        with open(config_path, 'w') as f:
            json.dump(userCfg, f, indent=2)
        logger.info(f'User configuration stored to {config_path}')
        return

    def UpdateConfig(self, updatedConfig):
        logger.info(f'Updating configuration for user {self.userID}')
        if 'agentModelConfig' in updatedConfig:
            self.config.agentModelConfig = updatedConfig['agentModelConfig']
            logger.debug('Updated agentModelConfig')
        if 'models' in updatedConfig:
            updateModels = {providerName: providerCfg for providerName, providerCfg in updatedConfig['models'].items() if providerName not in ['default']}
            for providerName in updateModels:
                updateModels[providerName]['modelList'] = self.config.models[providerName]['modelList']
            self.config.models.update(updateModels)
            logger.debug(f'Updated models configuration for providers: {list(updateModels.keys())}')
        if 'temperature' in updatedConfig:
            self.config.temperature = float(updatedConfig['temperature'])
            logger.debug(f'Updated temperature to {self.config.temperature}')
        if 'contextWindowRatio' in updatedConfig:
            self.config.contextWindowRatio = float(updatedConfig['contextWindowRatio'])
            logger.debug(f'Updated contextWindowRatio to {self.config.contextWindowRatio}')
        return

    def InitConfig(self):
        logger.info(f'Initializing configuration for user {self.userID}')
        self.config.__dict__.update(copy.deepcopy(global_config.ToJson()))
        configFile = self.GetPath(pathType='user_config')
        userConfig = {}
        if os.path.exists(configFile):
            with open(configFile, 'r') as f:
                userConfig = json.load(f)
                logger.info(f'Loaded user configuration from {configFile}')
        else:
            logger.info(f'No user configuration found at {configFile}, using defaults')
        self.UpdateConfig(userConfig)
        return

    @atomic_transition('create')
    def Create(self):
        logger.info(f'Creating user context for user {self.userID}')
        os.makedirs(self.GetPath(), exist_ok=True)
        os.makedirs(self.GetPath('sessions'), exist_ok=True)
        self.InitConfig()
        self.serverPublicFile, self.serverSecretFile = GenerateCertificates(self.GetPath(pathType='certificates'), 'server')
        self.clientPublicFile, self.clientSecretFile = GenerateCertificates(self.GetPath(pathType='certificates'), 'client')
        logger.info('Certificates generated')
        return

    @atomic_transition('release')
    def Release(self):
        logger.info(f'Releasing user context for user {self.userID}')
        for sessionName, session in self.context.items():
            logger.info(f'Releasing session {sessionName}')
            session.Stop()
            cleaner.AddSessionToGC(sessionName, session)
        self.context.clear()
        return

    @atomic_transition('session_call')
    def Setup(self, patches: list, apply=False) -> dict:
        updatedConfig = self.config.__dict__
        if patches is not None and type(patches) is list and (len(patches) > 0):
            logger.info(f'Setting up user context with patches: {patches}')
            try:
                validatedPatches = validate_patches(patches=patches)
                logger.debug('Patches validated')
            except Exception as e:
                logger.error(f'Setup() Exception: Invalid patches input. {patches}', exc_info=True)
                raise AWExceptionIllegalInput()
            if not all([any([check_path(p['path'], pattern) for pattern in UserContext.allowedPathes]) for p in patches]):
                logger.error(f'Setup() Exception. Invalid path input: {patches}')
                raise AWExceptionIllegalInput()
            updatedConfig = apply_patches(self.config.__dict__, validatedPatches)
            logger.debug('Patches applied to configuration')
            try:
                AiliceWebConfig.model_validate({k: v for k, v in updatedConfig.items() if k in UserContext.settings})
                logger.debug('Configuration validated')
            except Exception as e:
                logger.error(f'Configuration validation failed: {str(e)}', exc_info=True)
                raise
            for k, v in updatedConfig.items():
                if 'agentModelConfig' == k:
                    modelIDs = [f'{modelType}:{model}' for modelType in self.config.models for model in self.config.models[modelType]['modelList']]
                    if any([mid not in modelIDs for agentType, mid in v.items()]):
                        logger.error(f'Setup() Exception. Invalid modelID input: {patches}')
                        raise AWExceptionIllegalInput()
            if apply:
                self.UpdateConfig(updatedConfig)
                self.StoreConfig()
                for sessionName, session in self.context.items():
                    logger.info(f'Releasing session {sessionName} due to configuration update')
                    session.Stop()
                    cleaner.AddSessionToGC(sessionName, session)
                self.context.clear()
                sessionName = self.currentSession
                self.currentSession = None
                if sessionName is not None:
                    logger.info(f'Reloading current session {sessionName}')
                    self.Load(sessionName)
        ret = {}
        for k in UserContext.settings:
            if k == 'models':
                ret[k] = {provider: {'modelWrapper': providerCfg['modelWrapper'], 'apikey': None, 'baseURL': None, 'modelList': providerCfg['modelList']} if provider in ['default'] else providerCfg for provider, providerCfg in (self.config.__dict__[k].items() if apply else updatedConfig[k].items())}
            else:
                ret[k] = self.config.__dict__[k] if apply else updatedConfig[k]
        logger.debug('Settings schema built')
        return build_settings_schema(ret)

    @atomic_transition('session_call')
    def CurrentSession(self):
        if not self.currentSession:
            logger.warning(f'No current session for user {self.userID}')
            raise AWExceptionSessionNotExist()
        logger.debug(f'Returning current session {self.currentSession}')
        return self.context[self.currentSession]

    def Load(self, sessionName: str):
        logger.info(f'Loading session {sessionName} for user {self.userID}')
        try:
            if sessionName == self.currentSession:
                logger.info(f'Session {sessionName} already loaded, return now.')
                return
            logger.info(f'Release session {self.currentSession} at {self.GetPath(pathType='session', sessionName=self.currentSession)}')
            if self.currentSession in self.context:
                self.context[self.currentSession].Stop()
                cleaner.AddSessionToGC(self.currentSession, self.context[self.currentSession])
                self.context.pop(self.currentSession)
            self.currentSession = None
            sessionPath = self.GetPath(pathType='session', sessionName=sessionName)
            logger.info(f'Creating new TaskSession for {sessionName} at {sessionPath}')
            if cleaner.IsSessionInGC(sessionName) and (not time.sleep(5)) and cleaner.IsSessionInGC(sessionName):
                raise AWExceptionSessionBusy()
            self.context[sessionName] = TaskSession(sessionName, sessionPath, self.clientSecretFile, self.serverPublicFile)
            self.context[sessionName].Create(config=self.config)
            self.currentSession = sessionName
            logger.info(f'Session {sessionName} loaded successfully')
        except Exception as e:
            logger.error(f'Exception loading session {sessionName}: {str(e)}, currentSession: {self.currentSession}', exc_info=True)
            if hasattr(e, 'tb'):
                logger.error(e.tb)
            if sessionName in self.context:
                logger.info(f'Cleaning up failed session {sessionName}')
                self.context[sessionName].Stop()
                cleaner.AddSessionToGC(sessionName, self.context[sessionName])
                self.context.pop(sessionName)
                raise e
        return

    @atomic_transition('session_call')
    def NewSession(self) -> str:
        sessionName = 'ailice_' + str(int(time.time()))
        logger.info(f'Creating new session {sessionName} for user {self.userID}')
        self.Load(sessionName=sessionName)
        return sessionName

    @atomic_transition('session_call')
    def LoadSession(self, sessionName: str):
        logger.info(f'Loading session history for {sessionName}')
        sessions_dir = self.GetPath(pathType='sessions')
        if sessionName not in os.listdir(sessions_dir):
            logger.error(f'Session {sessionName} not found in {sessions_dir}')
            raise AWExceptionSessionNotExist()
        needLoading = sessionName != self.currentSession
        if needLoading:
            logger.info(f'Session {sessionName} is not current, loading it')
            self.Load(sessionName=sessionName)
        return

    @atomic_transition('session_call')
    def GetSession(self, sessionName: str):
        logger.info(f'Getting session history for {sessionName}')
        sessions_dir = self.GetPath(pathType='sessions')
        if sessionName not in os.listdir(sessions_dir):
            logger.error(f'Session {sessionName} not found in {sessions_dir}')
            raise AWExceptionSessionNotExist()

        def historyFilter(data):
            conversations = [(f'{conv['role']}_{data['name']}', conv['msg']) for conv in data['conversation']]
            ret = {'conversation': conversations}
            if 'subProcessors' in data:
                ret['subProcessors'] = {agentName: historyFilter(subProcessor) for agentName, subProcessor in data['subProcessors'].items()}
            else:
                ret['subProcessors'] = {}
            return ret
        historyPath = self.GetPath(pathType='history', sessionName=sessionName)
        if os.path.exists(historyPath):
            with open(historyPath, 'r') as f:
                data = json.load(f)
                conversations = historyFilter(data)
                logger.info(f'Got {len(conversations)} conversation entries from {historyPath}')
        else:
            logger.info(f'No history file found at {historyPath}, returning empty conversation')
            conversations = {}
        return conversations

    @atomic_transition('session_call')
    def DeleteSession(self, sessionName: str) -> bool:
        logger.info(f'Deleting session {sessionName} for user {self.userID}')
        if sessionName in self.context:
            logger.info(f'Releasing active session {sessionName}')
            self.context[sessionName].Stop()
            cleaner.AddSessionToGC(sessionName, self.context[sessionName])
            self.context.pop(sessionName)
            self.currentSession = None if sessionName == self.currentSession else self.currentSession
        sessions_dir = self.GetPath(pathType='sessions')
        if sessionName not in os.listdir(sessions_dir):
            logger.warning(f'Session {sessionName} not found in {sessions_dir}')
            return False
        historyDir = self.GetPath(pathType='session', sessionName=sessionName)
        shutil.rmtree(historyDir)
        logger.info(f'Deleted session directory {historyDir}')
        return True

    @atomic_transition('session_call')
    def ListSessions(self):
        logger.info(f'Listing sessions for user {self.userID}')
        histories = []
        sessions_dir = self.GetPath(pathType='sessions')
        for d in os.listdir(sessions_dir):
            p = self.GetPath(pathType='history', sessionName=d)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                with open(p, 'r') as f:
                    try:
                        content = json.load(f)
                        if len(content.get('conversation', [])) > 0:
                            histories.append((d, content.get('conversation')[0]['msg']))
                    except Exception as e:
                        logger.error(f'Error loading history file {p}: {str(e)}', exc_info=True)
                        continue
        sorted_histories = sorted(histories, key=lambda x: os.path.getmtime(self.GetPath(pathType='history', sessionName=x[0])), reverse=True)
        logger.info(f'Found {len(sorted_histories)} sessions')
        return sorted_histories

def historyFilter(data):
    conversations = [(f'{conv['role']}_{data['name']}', conv['msg']) for conv in data['conversation']]
    ret = {'conversation': conversations}
    if 'subProcessors' in data:
        ret['subProcessors'] = {agentName: historyFilter(subProcessor) for agentName, subProcessor in data['subProcessors'].items()}
    else:
        ret['subProcessors'] = {}
    return ret

class SessionCleaner:

    def __init__(self, max_workers=5):
        self.pendingGCPool = {}
        self.poolLock = threading.Lock()
        self.gcThread = threading.Thread(target=self.GCThread, daemon=True)
        self.gcThread.start()
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='SessionReleaser')
        logger.info(f'SessionCleaner initialized with {max_workers} release workers and GC thread started')
        return

    def AddSessionToGC(self, sessionName, session):
        with self.poolLock:
            self.pendingGCPool[sessionName] = session
            logger.info(f"Session '{sessionName}' added to GC pool")

    def IsSessionInGC(self, sessionName):
        with self.poolLock:
            return sessionName in self.pendingGCPool

    def ReleaseSession(self, session):
        session._release_flag = True
        try:
            session.Release()
        finally:
            session._release_flag = False
        return

    def GCThread(self):
        while True:
            try:
                inactiveList = []
                with self.poolLock:
                    for sessionName, session in self.pendingGCPool.items():
                        if session.state == 'init':
                            inactiveList.append(sessionName)
                        elif not getattr(session, '_release_flag', False) and session.IsStopped():
                            self.executor.submit(self.ReleaseSession, session)
                    for sessionName in inactiveList:
                        self.pendingGCPool.pop(sessionName)
                        logger.info(f"Session '{sessionName}' removed from GC pool")
                if len(inactiveList) > 0:
                    logger.info(f'{len(inactiveList)} sessions released. GCPool size: {len(self.pendingGCPool)}')
                time.sleep(1)
            except Exception as e:
                logger.error(f'Unexpected exception in GCThread: {str(e)}')
        return

def GCThread(self):
    while True:
        try:
            inactiveList = []
            with self.poolLock:
                for sessionName, session in self.pendingGCPool.items():
                    if session.state == 'init':
                        inactiveList.append(sessionName)
                    elif not getattr(session, '_release_flag', False) and session.IsStopped():
                        self.executor.submit(self.ReleaseSession, session)
                for sessionName in inactiveList:
                    self.pendingGCPool.pop(sessionName)
                    logger.info(f"Session '{sessionName}' removed from GC pool")
            if len(inactiveList) > 0:
                logger.info(f'{len(inactiveList)} sessions released. GCPool size: {len(self.pendingGCPool)}')
            time.sleep(1)
        except Exception as e:
            logger.error(f'Unexpected exception in GCThread: {str(e)}')
    return

def build_agent_models_schema(agent_model_config, models):
    model_options = get_all_model_options(models)
    rows = []
    for agent, model in agent_model_config.items():
        rows.append({'cells': [agent, {'type': 'formGroup', 'label': '', 'id': f'agent-model-{agent}', 'inputType': 'select', 'value': model, 'path': ['agentModelConfig', agent], 'options': model_options, 'disabled': False}, {'type': 'button', 'text': 'Remove', 'className': 'remove-button', 'disabled': False, 'onClick': f"removeAgentType('{agent}')"}]})
    defaultLLM = agent_model_config.get('DEFAULT', 'openrouter:qwen-2.5-72b-instruct' if len(model_options) == 0 or 'openrouter:qwen-2.5-72b-instruct' in model_options else model_options[0])
    return {'type': 'section', 'title': 'Agent Model Configuration', 'description': 'Configure which model each agent type should use. \nNote: Set up the provider\'s API key in "Model Providers" first to use their models.', 'disabled': False, 'content': [{'type': 'button', 'text': 'Add Agent Type', 'className': 'add-button', 'icon': '+', 'disabled': False, 'onClick': f"addNewAgentType('{defaultLLM}')"}, {'type': 'table', 'columns': ['Agent Type', 'Model', 'Actions'], 'disabled': False, 'rows': rows}]}

def build_providers_schema(models):
    content = [{'type': 'button', 'text': 'Add Provider', 'className': 'add-button', 'icon': '+', 'disabled': True, 'onClick': 'addNewProvider()'}]
    for provider_name, provider_config in models.items():
        buildin_providers = ['openrouter', 'apipie', 'anthropic', 'oai', 'mistral', 'deepseek', 'groq']
        isDefault = provider_name == 'default'
        disabled = provider_name in buildin_providers
        provider_card = {'type': 'card', 'id': f'provider-{provider_name}', 'title': provider_name, 'removable': not (disabled or isDefault), 'collapsible': True, 'disabled': False, 'onRemove': f"removeProvider('{provider_name}')", 'content': [{'type': 'formRow', 'disabled': False, 'content': [{'type': 'formGroup', 'id': f'provider-{provider_name}-wrapper', 'label': 'Model Wrapper', 'inputType': 'select', 'value': provider_config['modelWrapper'], 'path': ['models', provider_name, 'modelWrapper'], 'options': [{'value': 'AModelChatGPT', 'label': 'openai'}], 'disabled': isDefault}] + ([{'type': 'formGroup', 'id': f'provider-{provider_name}-apikey', 'label': 'API Key', 'inputType': 'password', 'value': provider_config['apikey'], 'path': ['models', provider_name, 'apikey'], 'disabled': isDefault}] if 'apikey' in provider_config else []) + ([{'type': 'formGroup', 'id': f'provider-{provider_name}-baseurl', 'label': 'Base URL', 'inputType': 'text', 'value': provider_config['baseURL'], 'path': ['models', provider_name, 'baseURL'], 'disabled': isDefault}] if 'baseURL' in provider_config else [])}]}
        content.append(provider_card)
    return {'type': 'section', 'title': 'Model Providers Configuration', 'description': 'Configure API keys for model providers.', 'disabled': False, 'content': content}

def build_models_section(provider_name, model_list, disabled):
    content = [{'type': 'button', 'text': 'Add Model', 'className': 'add-button', 'icon': '+', 'disabled': True, 'onClick': f"addNewModel('{provider_name}')"}]
    for model_name, model_config in model_list.items():
        model_card = {'type': 'card', 'id': f'model-{provider_name}-{model_name}', 'title': model_name, 'removable': not disabled, 'collapsible': True, 'disabled': False, 'onRemove': f"removeModel('{provider_name}', '{model_name}')", 'content': [{'type': 'formRow', 'disabled': False, 'content': [{'type': 'formGroup', 'id': f'model-{provider_name}-{model_name}-formatter', 'label': 'Formatter', 'inputType': 'select', 'value': model_config['formatter'], 'path': ['models', provider_name, 'modelList', model_name, 'formatter'], 'options': [{'value': 'AFormatterGPT', 'path': [], 'label': 'chat only'}, {'value': 'AFormatterGPTVision', 'path': [], 'label': 'vision'}], 'disabled': disabled}, {'type': 'formGroup', 'id': f'model-{provider_name}-{model_name}-contextwindow', 'label': 'Context Window', 'inputType': 'number', 'value': model_config['contextWindow'], 'path': ['models', provider_name, 'modelList', model_name, 'contextWindow'], 'disabled': disabled}]}, {'type': 'checkbox', 'id': f'model-{provider_name}-{model_name}-systemasuser', 'label': 'System As User', 'checked': model_config['systemAsUser'], 'disabled': disabled}]}
        content.append(model_card)
    return {'type': 'section', 'id': f'provider-{provider_name}-models-section', 'title': 'Models', 'disabled': False, 'content': content}

@wraps(func)
def wrapper(self, *args, **kwargs):
    if not hasattr(self, 'methodLock'):
        raise AttributeError('Object has no methodLock attribute')
    with self.methodLock:
        if getattr(self, f'may_{action}')():
            try:
                ret = func(self, *args, **kwargs)
                getattr(self, action)()
            except Exception as e:
                raise e
            return ret
        else:
            logger.error(f"Method '{func.__name__}' cannot be called in state '{self.state}'")
            raise AWExceptionNotReadyForOperation(f"Method '{func.__name__}' cannot be called in state '{self.state}'. ")

def GetThreadID(thread):
    if not thread.is_alive():
        raise threading.ThreadError('The thread is not active')
    for tid, tobj in threading._active.items():
        if tobj is thread:
            return tid
    raise AssertionError('Could not find thread ID')

def ExtractMessages(history: dict, depth: int) -> list:
    if history is None:
        return []
    messages = [{'message': r['msg'], 'role': f'{r['role']}_{history['name']}', 'action': '', 'msgType': 'internal' if depth > 0 else 'user-ailice', 'time': r['time']} for r in history['conversation']]
    for _, p in history['subProcessors'].items():
        messages += ExtractMessages(p, depth + 1)
    return sorted(messages, key=lambda x: x['time'])

class AClientPool:

    def __init__(self):
        self.pool = dict()
        return

    def Init(self):
        for serviceName, cfg in config.services.items():
            if not config.speechOn and 'speech' == serviceName:
                continue
            try:
                self.pool[cfg['addr']] = {'name': serviceName, 'client': makeClient(url=cfg['addr'], clientPrivateKeyPath=cfg.get('clientPrivateKeyPath', None), serverPublicKeyPath=cfg.get('serverPublicKeyPath', None))}
            except Exception as e:
                print(f'Connecting module {serviceName} FAILED. You can try running the module manually and observe its error messages. EXCEPTION: {str(e)}')
                raise e
        return

    def GetClient(self, moduleAddr: str, clientPrivateKeyPath=None, serverPublicKeyPath=None):
        if moduleAddr not in self.pool:
            self.pool[moduleAddr] = {'client': makeClient(url=moduleAddr, clientPrivateKeyPath=clientPrivateKeyPath, serverPublicKeyPath=serverPublicKeyPath)}
            self.pool[moduleAddr]['name'] = self.pool[moduleAddr]['client'].ModuleInfo()['NAME']
        return self.pool[moduleAddr]['client']

    def __getitem__(self, key: str):
        for addr, client in self.pool.items():
            if key == client['name']:
                return client['client']
        return None

    def Destroy(self):
        for _, client in self.pool.items():
            destroy = getattr(client['client'], 'Destroy', None)
            if callable(destroy):
                try:
                    destroy()
                    destroyClient(client['client'])
                except Exception as e:
                    print(f'AClientPool.Destroy Exception: {str(e)}')
                    continue
        self.pool.clear()
        return

def Init(self):
    for serviceName, cfg in config.services.items():
        if not config.speechOn and 'speech' == serviceName:
            continue
        try:
            self.pool[cfg['addr']] = {'name': serviceName, 'client': makeClient(url=cfg['addr'], clientPrivateKeyPath=cfg.get('clientPrivateKeyPath', None), serverPublicKeyPath=cfg.get('serverPublicKeyPath', None))}
        except Exception as e:
            print(f'Connecting module {serviceName} FAILED. You can try running the module manually and observe its error messages. EXCEPTION: {str(e)}')
            raise e
    return

def GetClient(self, moduleAddr: str, clientPrivateKeyPath=None, serverPublicKeyPath=None):
    if moduleAddr not in self.pool:
        self.pool[moduleAddr] = {'client': makeClient(url=moduleAddr, clientPrivateKeyPath=clientPrivateKeyPath, serverPublicKeyPath=serverPublicKeyPath)}
        self.pool[moduleAddr]['name'] = self.pool[moduleAddr]['client'].ModuleInfo()['NAME']
    return self.pool[moduleAddr]['client']

def __getitem__(self, key: str):
    for addr, client in self.pool.items():
        if key == client['name']:
            return client['client']
    return None

def Destroy(self):
    for _, client in self.pool.items():
        destroy = getattr(client['client'], 'Destroy', None)
        if callable(destroy):
            try:
                destroy()
                destroyClient(client['client'])
            except Exception as e:
                print(f'AClientPool.Destroy Exception: {str(e)}')
                continue
    self.pool.clear()
    return

class AConfig:

    def __init__(self):
        self.configFile = None
        self.modelID = ''
        self.agentModelConfig = {'DEFAULT': 'openrouter:z-ai/glm-4.5', 'search-engine': 'openrouter:qwen/qwen-2.5-72b-instruct'}
        self.prompt = 'main'
        self.chatHistoryPath = appdirs.user_data_dir('ailice', 'Steven Lu')
        self.certificate = ''
        self.expose = False
        self.maxMemory = {}
        self.quantization = None
        self.models = {'oai': {'modelWrapper': 'AModelChatGPT', 'apikey': None, 'baseURL': None, 'modelList': {'gpt-5-2025-08-07': {'formatter': 'AFormatterGPTVision', 'contextWindow': 400000, 'systemAsUser': False, 'args': {}}, 'gpt-5-mini-2025-08-07': {'formatter': 'AFormatterGPTVision', 'contextWindow': 400000, 'systemAsUser': False, 'args': {}}, 'gpt-5-nano-2025-08-07': {'formatter': 'AFormatterGPTVision', 'contextWindow': 400000, 'systemAsUser': False, 'args': {}}, 'gpt-5-chat-latest': {'formatter': 'AFormatterGPTVision', 'contextWindow': 400000, 'systemAsUser': False, 'args': {}}, 'gpt-oss-120b': {'formatter': 'AFormatterGPT', 'contextWindow': 131072, 'systemAsUser': False, 'args': {}}, 'gpt-oss-20b': {'formatter': 'AFormatterGPT', 'contextWindow': 131072, 'systemAsUser': False, 'args': {}}, 'o3-deep-research-2025-06-26': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'o4-mini-deep-research-2025-06-26': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'o3-pro-2025-06-10': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'o3-2025-04-16': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'o4-mini-2025-04-16': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'o1-pro-2025-03-19': {'formatter': 'AFormatterGPTVision', 'contextWindow': 200000, 'systemAsUser': False, 'args': {}}, 'gpt-4.1-2025-04-14': {'formatter': 'AFormatterGPTVision', 'contextWindow': 1047576, 'systemAsUser': False, 'args': {}}, 'gpt-4.1-mini-2025-04-14': {'formatter': 'AFormatterGPTVision', 'contextWindow': 1047576, 'systemAsUser': False, 'args': {}}, 'gpt-4.1-nano-2025-04-14': {'formatter': 'AFormatterGPTVision', 'contextWindow': 1047576, 'systemAsUser': False, 'args': {}}, 'o1-preview': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'o1-preview-2024-09-12': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'o1-mini': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'o1-mini-2024-09-12': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'o3-mini': {'formatter': 'AFormatterGPT', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'o3-mini-2025-01-31': {'formatter': 'AFormatterGPT', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'gpt-4o': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'gpt-4o-2024-05-13': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'gpt-4o-2024-08-06': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'chatgpt-4o-latest': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'gpt-4o-mini': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'gpt-4o-mini-2024-07-18': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': True, 'args': {}}, 'gpt-4-turbo': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4-turbo-2024-04-09': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4-0125-preview': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4-turbo-preview': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4-1106-preview': {'formatter': 'AFormatterGPT', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4-vision-preview': {'formatter': 'AFormatterGPTVision', 'contextWindow': 128000, 'systemAsUser': False, 'args': {}}, 'gpt-4': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}, 'gpt-4-32k': {'formatter': 'AFormatterGPT', 'contextWindow': 32768, 'systemAsUser': False, 'args': {}}, 'gpt-4-0613': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}, 'gpt-4-32k-0613': {'formatter': 'AFormatterGPT', 'contextWindow': 32768, 'systemAsUser': False, 'args': {}}, 'gpt-4-0314': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}, 'gpt-4-32k-0314': {'formatter': 'AFormatterGPT', 'contextWindow': 32768, 'systemAsUser': False, 'args': {}}}}, 'groq': {'modelWrapper': 'AModelChatGPT', 'apikey': None, 'baseURL': 'https://api.groq.com/openai/v1', 'modelList': {'llama3-8b-8192': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}, 'llama3-70b-8192': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}, 'llama2-70b-4096': {'formatter': 'AFormatterGPT', 'contextWindow': 4096, 'systemAsUser': False, 'args': {}}, 'mixtral-8x7b-32768': {'formatter': 'AFormatterGPT', 'contextWindow': 32768, 'systemAsUser': False, 'args': {}}, 'gemma-7b-it': {'formatter': 'AFormatterGPT', 'contextWindow': 8192, 'systemAsUser': False, 'args': {}}}}, 'openrouter': {'modelWrapper': 'AModelChatGPT', 'apikey': None, 'baseURL': 'https://openrouter.ai/api/v1', 'modelList': {}}, 'apipie': {'modelWrapper': 'AModelChatGPT', 'apikey': None, 'baseURL': 'https://apipie.ai/v1/', 'modelList': {}}, 'deepseek': {'modelWrapper': 'AModelChatGPT', 'apikey': None, 'baseURL': 'https://api.deepseek.com', 'modelList': {'deepseek-chat': {'formatter': 'AFormatterGPT', 'contextWindow': 64000, 'systemAsUser': False, 'args': {}}, 'deepseek-reasoner': {'formatter': 'AFormatterGPT', 'contextWindow': 64000, 'systemAsUser': False, 'args': {}}}}, 'mistral': {'modelWrapper': 'AModelMistral', 'apikey': None, 'modelList': {'mistral-small-latest': {'formatter': 'AFormatterGPT', 'contextWindow': 32764, 'systemAsUser': True, 'args': {}}, 'mistral-medium-latest': {'formatter': 'AFormatterGPT', 'contextWindow': 32764, 'systemAsUser': True, 'args': {}}, 'mistral-large-latest': {'formatter': 'AFormatterGPT', 'contextWindow': 32764, 'systemAsUser': True, 'args': {}}}}, 'anthropic': {'modelWrapper': 'AModelAnthropic', 'apikey': None, 'baseURL': None, 'modelList': {'claude-instant-1.2': {'formatter': 'AFormatterGPT', 'contextWindow': 100000, 'systemAsUser': True, 'args': {}}, 'claude-2.0': {'formatter': 'AFormatterGPT', 'contextWindow': 100000, 'systemAsUser': True, 'args': {}}, 'claude-2.1': {'formatter': 'AFormatterGPT', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-sonnet-20240229': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-opus-20240229': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-5-sonnet-20240620': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-5-sonnet-20241022': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-5-haiku-20241022': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-3-7-sonnet-20250219': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-sonnet-4-20250514': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-opus-4-20250514': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}, 'claude-opus-4-1-20250805': {'formatter': 'AFormatterClaudeVision', 'contextWindow': 200000, 'systemAsUser': True, 'args': {}}}}}
        self.temperature = 0.0
        self.flashAttention2 = False
        self.speechOn = False
        self.ttsDevice = 'cpu'
        self.sttDevice = 'cpu'
        self.contextWindowRatio = 0.6
        if 'nt' == os.name:
            self.services = {'storage': {'cmd': 'python -m ailice.modules.AStorageVecDB --addr=tcp://127.0.0.1:59001', 'addr': 'tcp://127.0.0.1:59001', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'browser': {'cmd': 'python -m ailice.modules.ABrowser --addr=tcp://127.0.0.1:59002', 'addr': 'tcp://127.0.0.1:59002', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'arxiv': {'cmd': 'python -m ailice.modules.AArxiv --addr=tcp://127.0.0.1:59003', 'addr': 'tcp://127.0.0.1:59003', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'google': {'cmd': 'python -m ailice.modules.AGoogle --addr=tcp://127.0.0.1:59004', 'addr': 'tcp://127.0.0.1:59004', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'duckduckgo': {'cmd': 'python -m ailice.modules.ADuckDuckGo --addr=tcp://127.0.0.1:59005', 'addr': 'tcp://127.0.0.1:59005', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'scripter': {'cmd': 'python -m ailice.modules.AScripter --addr=tcp://127.0.0.1:59000', 'addr': 'tcp://127.0.0.1:59000', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'speech': {'cmd': 'python -m ailice.modules.ASpeech --addr=tcp://127.0.0.1:59006', 'addr': 'tcp://127.0.0.1:59006', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'computer': {'cmd': 'python -m ailice.modules.AComputer --addr=tcp://127.0.0.1:59007', 'addr': 'tcp://127.0.0.1:59007', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}}
        else:
            self.services = {'storage': {'cmd': 'python3 -m ailice.modules.AStorageVecDB --addr=ipc:///tmp/AIliceStorage.ipc', 'addr': 'ipc:///tmp/AIliceStorage.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'browser': {'cmd': 'python3 -m ailice.modules.ABrowser --addr=ipc:///tmp/ABrowser.ipc', 'addr': 'ipc:///tmp/ABrowser.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'arxiv': {'cmd': 'python3 -m ailice.modules.AArxiv --addr=ipc:///tmp/AArxiv.ipc', 'addr': 'ipc:///tmp/AArxiv.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'google': {'cmd': 'python3 -m ailice.modules.AGoogle --addr=ipc:///tmp/AGoogle.ipc', 'addr': 'ipc:///tmp/AGoogle.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'duckduckgo': {'cmd': 'python3 -m ailice.modules.ADuckDuckGo --addr=ipc:///tmp/ADuckDuckGo.ipc', 'addr': 'ipc:///tmp/ADuckDuckGo.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'scripter': {'cmd': 'python3 -m ailice.modules.AScripter --addr=tcp://127.0.0.1:59000', 'addr': 'tcp://127.0.0.1:59000', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'speech': {'cmd': 'python3 -m ailice.modules.ASpeech --addr=ipc:///tmp/ASpeech.ipc', 'addr': 'ipc:///tmp/ASpeech.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}, 'computer': {'cmd': 'python3 -m ailice.modules.AComputer --addr=ipc:///tmp/AComputer.ipc', 'addr': 'ipc:///tmp/AComputer.ipc', 'clientPrivateKeyPath': None, 'serverPublicKeyPath': None}}
        return

    def InitCfg(self, provider, baseURL):
        try:
            response = requests.get(f'{baseURL}/models')
            response.raise_for_status()
            json = response.json()
            for model in json['data']:
                if provider == 'apipie':
                    formatter = {'llm': 'AFormatterGPT', 'vision': 'AFormatterGPTVision'}.get(model['type'], None)
                    if formatter is None or model['max_tokens'] is None:
                        continue
                    self.models[provider]['modelList'][model['id']] = {'formatter': formatter, 'contextWindow': int(model['max_tokens']), 'systemAsUser': True, 'args': {'extra_headers': {'HTTP-Referer': 'https://github.com/myshell-ai/AIlice', 'X-Title': 'Ailice'}}}
                else:
                    formatter = {'text->text': 'AFormatterGPT', 'text+image->text': 'AFormatterGPTVision'}.get(model['architecture']['modality'], None)
                    if formatter is None:
                        continue
                    self.models[provider]['modelList'][model['id']] = {'formatter': formatter, 'contextWindow': int(model['context_length']), 'systemAsUser': True, 'args': {'extra_headers': {'HTTP-Referer': 'https://github.com/myshell-ai/AIlice', 'X-Title': 'Ailice'}}}
        except Exception as e:
            print(f'InitCfg() FAILED, skip this part and do not set it again. EXCEPTION: {str(e)}')
        return

    def Initialize(self, configFile: str):
        self.configFile = configFile
        print(colored('********************** Initialize *****************************', 'yellow'))
        print(f'config.json is located at {self.configFile}')
        providers = {'openrouter': 'https://openrouter.ai/api/v1', 'apipie': 'https://apipie.ai/v1'}
        for provider, base_url in providers.items():
            self.InitCfg(provider, base_url)
        try:
            os.makedirs(os.path.dirname(self.configFile))
        except OSError as e:
            pass
        oldDict = self.Load(self.configFile)
        self.Update(oldDict)
        self.Store(self.configFile)
        print(colored('********************** End of Initialization *****************************', 'yellow'))
        return

    def Check4Update(self, modelID, reset):
        modelIDs = [modelID] if '' != modelID else list(self.agentModelConfig.values())
        setList = []
        for id in modelIDs:
            modelType = id[:id.find(':')]
            modelName = id[id.find(':') + 1:]
            if modelType not in self.models or modelName not in self.models[modelType]['modelList']:
                print(f"The specified model ID '{id}' was not found in the configuration; you need to configure it in '{self.configFile}' beforehand.")
                sys.exit(0)
            if 'apikey' in self.models[modelType] and self.models[modelType]['apikey'] is None or (reset and modelType not in setList):
                key = input(colored(f'Your {modelType} api-key (or press Enter to keep current setting): ', 'green'))
                if 1 < len(key):
                    self.models[modelType]['apikey'] = key
                    self.Store(self.configFile)
                    setList.append(modelType)
        return

    def Update(self, cfgDict: dict):
        self.__dict__ = self.Merge('', self.__dict__, cfgDict)
        return

    def Merge(self, key, template, reference):
        if type(template) == dict and type(reference) == dict:
            if key in ['models', 'modelList']:
                return {k: self.Merge(k, template[k], reference[k]) if k in template and k in reference else v for k, v in {**reference, **template}.items()}
            elif key in ['agentModelConfig', 'services']:
                return reference
            else:
                return {k: self.Merge(k, v, reference[k]) if k in reference else v for k, v in template.items()}
        elif key == 'configFile':
            return template
        else:
            return reference

    def ToJson(self):
        return {k: v for k, v in self.__dict__.items() if k != 'configFile'}

    def Load(self, configFile: str) -> dict:
        if not os.path.exists(configFile):
            print(f"config.json not found, let's create a new one: '{configFile}'.")
            self.Store(configFile)
        with open(configFile, 'r') as f:
            return json.load(f)

    def Store(self, configFile: str):
        with open(configFile, 'w') as f:
            json.dump(self.ToJson(), f, indent=2)
        return

def Update(self, cfgDict: dict):
    self.__dict__ = self.Merge('', self.__dict__, cfgDict)
    return

def Merge(self, key, template, reference):
    if type(template) == dict and type(reference) == dict:
        if key in ['models', 'modelList']:
            return {k: self.Merge(k, template[k], reference[k]) if k in template and k in reference else v for k, v in {**reference, **template}.items()}
        elif key in ['agentModelConfig', 'services']:
            return reference
        else:
            return {k: self.Merge(k, v, reference[k]) if k in reference else v for k, v in template.items()}
    elif key == 'configFile':
        return template
    else:
        return reference

def ToJson(self):
    return {k: v for k, v in self.__dict__.items() if k != 'configFile'}

class AMessenger:

    def __init__(self):
        self.lock = threading.Lock()
        self.continueEvent = threading.Event()
        self.continueEvent.set()
        self.msg = None
        self.msgPrevious = None
        return

    def Get(self) -> str:
        self.continueEvent.wait()
        with self.lock:
            self.msgPrevious = self.msg
            self.msg = None
        return self.msgPrevious

    def GetPreviousMsg(self) -> str:
        return self.msgPrevious

    def Lock(self):
        self.continueEvent.clear()
        return

    def Put(self, msg: str):
        with self.lock:
            self.msg = msg if '' != msg.strip() else None

    def Unlock(self):
        self.continueEvent.set()
        return

def Lock(self):
    self.continueEvent.clear()
    return

class GeneratorStorage:

    def __init__(self, obj, atomicAccess=True):
        self.obj = obj
        self.generators = {}
        self.lock = threading.Lock() if atomicAccess else nullcontext()

    def SaveGenerator(self, generatorID, gen):
        self.generators[generatorID] = gen

    def GetGenerator(self, generatorID):
        return self.generators[generatorID]

    def __getattr__(self, name):
        return getattr(self.obj, name)

def __getattr__(self, name):
    return getattr(self.obj, name)

def SignatureFromString(sig_str: str) -> inspect.Signature:
    funcDefNode = ast.parse(f'def f{sig_str}:\n    pass', mode='exec').body[0]

    def BuildArg(arg, kind):
        annotation = BuildTypeFromAST(arg.annotation, TYPE_NAMESPACE) if arg.annotation else inspect.Parameter.empty
        return inspect.Parameter(name=arg.arg, kind=kind, annotation=annotation)
    parameters = []
    for arg in funcDefNode.args.args:
        parameters.append(BuildArg(arg, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    if funcDefNode.args.vararg:
        parameters.append(BuildArg(funcDefNode.args.vararg, inspect.Parameter.VAR_POSITIONAL))
    if funcDefNode.args.kwarg:
        parameters.append(BuildArg(funcDefNode.args.kwarg, inspect.Parameter.VAR_KEYWORD))
    defaults = funcDefNode.args.defaults
    if defaults:
        offset = len(parameters) - len(defaults)
        for i, default in enumerate(defaults):
            try:
                defaultValue = ast.literal_eval(default)
            except (ValueError, SyntaxError):
                defaultValue = inspect.Parameter.empty
            parameters[offset + i] = parameters[offset + i].replace(default=defaultValue)
    returnAnnotation = BuildTypeFromAST(funcDefNode.returns, TYPE_NAMESPACE) if funcDefNode.returns else inspect.Parameter.empty
    return inspect.Signature(parameters=parameters, return_annotation=returnAnnotation)

def BuildArg(arg, kind):
    annotation = BuildTypeFromAST(arg.annotation, TYPE_NAMESPACE) if arg.annotation else inspect.Parameter.empty
    return inspect.Parameter(name=arg.arg, kind=kind, annotation=annotation)

def BuildTypeFromAST(node, namespace):
    if isinstance(node, ast.Name):
        if node.id not in namespace:
            raise TypeError(f'BuildTypeFromAST(): Unsupported type {str(node.id)}.')
        return namespace[node.id]
    elif isinstance(node, ast.Attribute):
        attrChain = []
        current = node
        while isinstance(current, ast.Attribute):
            attrChain.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            attrChain.append(current.id)
        attrChain.reverse()
        baseModule = namespace.get(attrChain[0], None)
        if baseModule is None:
            if attrChain[:3] == ['ailice', 'common', 'ADataType']:
                baseModule = importlib.import_module(attrChain[0])
            else:
                raise TypeError(f'BuildTypeFromAST(): Unsupported type {str(attrChain)}.')
        currentObj = baseModule
        for i in range(1, len(attrChain)):
            currentObj = getattr(currentObj, attrChain[i])
        return currentObj
    elif isinstance(node, ast.Subscript):
        container = BuildTypeFromAST(node.value, namespace)
        args = node.slice
        if isinstance(args, ast.Tuple):
            type_args = [BuildTypeFromAST(arg, namespace) for arg in args.elts]
            return container[tuple(type_args)]
        else:
            type_arg = BuildTypeFromAST(args, namespace)
            return container[type_arg]
    elif isinstance(node, ast.Tuple):
        return tuple((BuildTypeFromAST(elt, namespace) for elt in node.elts))
    elif isinstance(node, ast.Constant) and node.value is None:
        return None
    else:
        raise TypeError(f'BuildTypeFromAST(): Unsupported type {str(node)}.')

def AnnotationsFromSignature(signature: inspect.Signature) -> dict:
    annotations = {}
    for param_name, param in signature.parameters.items():
        if param.annotation is not inspect.Parameter.empty:
            annotations[param_name] = param.annotation
    if signature.return_annotation is not inspect.Parameter.empty:
        annotations['return'] = signature.return_annotation
    return annotations

class DatasetAIliceTrace(GeneratorBasedBuilder):
    VERSION = datasets.Version('1.0.0')

    def __init__(self, maxWindow: int, **kwargs):
        super().__init__(**kwargs)
        self.maxWindow = maxWindow
        return

    def _info(self):
        return DatasetInfo(description='AIlice trace dataset', features=Features({'conversations': Sequence({'role': Value('string'), 'msg': Value('string')})}), supervised_keys=None)

    def _split_generators(self, dl_manager):
        return [SplitGenerator(name=Split.TRAIN, gen_kwargs={'datasetDir': dl_manager.manual_dir, 'datasetType': 'train'}), SplitGenerator(name=Split.VALIDATION, gen_kwargs={'datasetDir': dl_manager.manual_dir, 'datasetType': 'validation'})]

    def _generate_examples(self, datasetDir, datasetType):
        idx = -1
        directoryPath = Path(datasetDir)
        for jsonFile in directoryPath.glob('*.json'):
            with jsonFile.open('r', encoding='utf-8') as f:
                data = json.load(f)
                convs = self.ExtractConversations(data)
                left, right = {'train': (0, int(0.8 * len(convs))), 'validation': (int(0.8 * len(convs)), len(convs))}[datasetType]
                for conv in convs[left:right]:
                    for convPiece in self.Split(conv):
                        idx += 1
                        yield (idx, {'conversations': convPiece})

    def ExtractConversations(self, trace):
        convs = []
        agentTrace = trace
        convs.append(agentTrace['conversations'])
        if 'subProcessors' in agentTrace:
            for subAgent in agentTrace['subProcessors']:
                convs += self.ExtractConversations(agentTrace['subProcessors'][subAgent])
        return convs

    def Split(self, conv):
        ret = [[]]
        currentLen = 0
        for c in conv:
            currentLen += len(f'{c['role']}: {c['msg']}')
            if currentLen // 4 >= self.maxWindow:
                ret.append([c])
                currentLen = 0
            else:
                ret[-1].append(c)
        return ret

def ExtractConversations(self, trace):
    convs = []
    agentTrace = trace
    convs.append(agentTrace['conversations'])
    if 'subProcessors' in agentTrace:
        for subAgent in agentTrace['subProcessors']:
            convs += self.ExtractConversations(agentTrace['subProcessors'][subAgent])
    return convs

def Split(self, conv):
    ret = [[]]
    currentLen = 0
    for c in conv:
        currentLen += len(f'{c['role']}: {c['msg']}')
        if currentLen // 4 >= self.maxWindow:
            ret.append([c])
            currentLen = 0
        else:
            ret[-1].append(c)
    return ret

class AStorageVecDB:

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.data = {'tokenizer': TOKENIZER, 'model': MODEL, 'collections': {}}
        self.dir = None
        return

    def ModuleInfo(self):
        return {'NAME': 'storage', 'ACTIONS': {}}

    def CalcEmbeddings(self, txts: list[str]):
        encodedInput = self.tokenizer(txts, padding=True, truncation=True, return_tensors='pt')
        with torch.no_grad():
            modelOutput = self.model(**encodedInput)
        tokenEmbeddings = modelOutput[0]
        inputMaskExpanded = encodedInput['attention_mask'].unsqueeze(-1).expand(tokenEmbeddings.size()).float()
        embeddings = torch.sum(tokenEmbeddings * inputMaskExpanded, 1) / torch.clamp(inputMaskExpanded.sum(1), min=1e-09)
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings

    def Dump(self, dir):
        if None != dir:
            with open(dir + '/vecdb', 'wb') as f:
                pickle.dump(self.data, f)
        return

    def Load(self, dir):
        if os.path.exists(dir + '/vecdb'):
            with open(dir + '/vecdb', 'rb') as f:
                self.data = pickle.load(f)
        return

    def PrepareModel(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.data['tokenizer'])
        self.model = AutoModel.from_pretrained(self.data['model'], trust_remote_code=True)
        self.model.eval()
        return

    def Open(self, directory: str) -> str:
        try:
            if '' == directory.strip():
                self.dir = None
                self.PrepareModel()
                return f'vector database has been switched to a non-persistent version. tokenizer: {self.data['tokenizer']}, model: {self.data['model']}'
            else:
                self.dir = directory
                self.Load(directory)
                self.PrepareModel()
                return f'vector database under {directory} is opened. tokenizer: {self.data['tokenizer']}, model: {self.data['model']}'
        except Exception as e:
            print(f'Open() EXCEPTION. e: {str(e)}')
            raise e

    def Reset(self) -> str:
        self.data['collections'].clear()
        return 'vector database reseted.'

    def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
        try:
            print('collection: ', collection, '. store: ', content)
            if collection not in self.data['collections']:
                self.data['collections'][collection] = dict()
            texts = [content] if type(content) != list else content
            embeddings = self.CalcEmbeddings(texts)
            for txt, emb in zip(texts, embeddings):
                if txt not in self.data['collections'][collection]:
                    self.data['collections'][collection][txt] = emb
            self.Dump(self.dir)
        except Exception as e:
            print('store() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return False
        return True

    def Query(self, collection: str, clue: str='', keywords: list[str]=[], num_results: int=1) -> list[tuple[str, float]]:
        try:
            if collection not in self.data['collections']:
                return []
            results = [txt for txt, _ in self.data['collections'][collection].items()]
            for keyword in keywords:
                results = [txt for txt in results if keyword in txt]
            if clue in ['', None]:
                results = [(r, -1.0) for r in results]
                return results[:num_results] if num_results > 0 else results
            query = self.CalcEmbeddings([clue])[0]
            temp = [(txt, torch.sum((self.data['collections'][collection][txt] - query) ** 2, dim=0).item()) for txt in results]
            ret = sorted(temp, key=lambda x: x[1])[:num_results] if num_results > 0 else temp
            print('query: ', collection, '.', clue, ' -> ', ret)
            return ret
        except Exception as e:
            print('query() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return []

    def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
        return self.Query(collection=collection, clue=query, num_results=num_results)

def Reset(self) -> str:
    self.data['collections'].clear()
    return 'vector database reseted.'

class ABrowser:

    def __init__(self, pdfOutputDir: str):
        self.pdfOutputDir = pdfOutputDir
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-BROWSER<!|session: str|!>', 'SCROLLUP': '#scroll up the page: \nSCROLL-UP-BROWSER<!|session: str|!>', 'SEARCHDOWN': '#search the content downward and jumps the page to the next matching point(Just like the F3 key normally does): \nSEARCH-DOWN-BROWSER<!|query: str, session: str|!>', 'SEARCHUP': '#search the content upward and jumps the page to the next matching point: \nSEARCH-UP-BROWSER<!|query: str, session: str|!>'}
        self.prompt = 'The browser is running in headless mode, mouse and keyboard operations are not supported. All operations on the page must be accomplished using the functions listed after the page content.'
        return

    def ModuleInfo(self):
        return {'NAME': 'browser', 'ACTIONS': {'BROWSE': {'func': 'Browse', 'prompt': "Open any PDFs, web pages in headless mode to retrieve their content. The 'url' parameter can be either a URL or a local path. You need to give the page a name(the session parameter). You can reuse this session to open new url/path.", 'type': 'primary'}, 'BROWSE-EDIT': {'func': 'Edit', 'prompt': 'Browse and edit any text document (including code files with various extensions) in headless mode. You need to give the page a name(the session parameter). You can reuse this session to open new file.', 'type': 'primary'}, 'SCROLL-DOWN-BROWSER': {'func': 'ScrollDown', 'prompt': 'Scroll down the page.', 'type': 'supportive'}, 'SCROLL-UP-BROWSER': {'func': 'ScrollUp', 'prompt': 'Scroll up the page.', 'type': 'supportive'}, 'SEARCH-DOWN-BROWSER': {'func': 'SearchDown', 'prompt': 'Search content downward from the current location.', 'type': 'supportive'}, 'SEARCH-UP-BROWSER': {'func': 'SearchUp', 'prompt': 'Search content upward from the current location.', 'type': 'supportive'}, 'GET-LINK': {'func': 'GetLink', 'prompt': 'Get the url on the specified text fragment. The text needs to be one of those text fragments enclosed by square brackets on the page (excluding the square brackets themselves).', 'type': 'supportive'}, 'EXECUTE-JS': {'func': 'ExecuteJS', 'prompt': 'Execute js code on the current web page, especially suitable for form operations such as entering text, clicking buttons, etc. Use triple quotes on your code.', 'type': 'supportive'}, 'REPLACE': {'func': 'Replace', 'prompt': 'Replace the matching content within the current page. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.', 'type': 'supportive'}, 'REPLACE-ALL': {'func': 'ReplaceAll', 'prompt': 'Replace all matching content in the entire document. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.', 'type': 'supportive'}, 'SAVETO': {'func': 'SaveTo', 'prompt': 'Save the modified content to a file. If the dstPath parameter is an empty string, save it to the original file.', 'type': 'supportive'}}}

    def ParseURL(self, txt: str) -> str:
        extractor = URLExtract()
        urls = extractor.find_urls(txt)
        if 0 == len(urls):
            print('ParseURL: no url provided. ', txt)
            return None
        else:
            url = urls[0]
        return url

    def ParsePath(self, txt: str) -> str:
        pattern = '^(\\/.*|[^\\/].*)$'
        matches = re.findall(pattern, txt)
        if not matches:
            print('ParsePath: no path provided. ', txt)
            return None
        else:
            return matches[0].strip()

    def GetLocation(self, txt: str) -> tuple[str, str]:
        url = self.ParseURL(txt)
        if url is not None:
            return (self.ToHttps(url), None)
        path = self.ParsePath(txt)
        if path is not None:
            return (None, path)
        return (None, None)

    def ToHttps(self, url: str) -> str:
        if not urlparse(url).scheme:
            url = 'https://' + url
        return url

    def URLIsPDF(self, url: str) -> bool:
        response = requests.head(url, allow_redirects=True)
        contentType = response.headers.get('content-type')
        return 'pdf' in contentType if contentType else False

    def PathIsPDF(self, path: str) -> bool:
        return path[-4:] == '.pdf'

    def Browse(self, url: str, session: str) -> str:
        try:
            if session in self.sessions:
                self.sessions[session].Destroy()
                self.sessions.pop(session)
            url, path = self.GetLocation(url)
            if url is not None:
                if self.URLIsPDF(url):
                    self.sessions[session] = APDFBrowser(self.pdfOutputDir, functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(url) + '\n\n' + f'Session name: "{session}"\n'
                else:
                    self.sessions[session] = AWebBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(url) + '\n\n' + f'Session name: "{session}"\n'
            elif path is not None:
                if os.path.isdir(path):
                    self.sessions[session] = AFileBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
                elif self.PathIsPDF(path):
                    self.sessions[session] = APDFBrowser(self.pdfOutputDir, functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
                else:
                    self.sessions[session] = ATextBrowser(functions=self.functions)
                    return self.prompt + '\n\n' + self.sessions[session].Browse(path) + '\n\n' + f'Session name: "{session}"\n'
            else:
                return 'No URL/Path found in input string. Please check your input. '
        except Exception as e:
            print('EXCEPTION. e: ', str(e))
            return f'Browser Exception. please check your url input. EXCEPTION: {str(e)}\n{traceback.format_exc()}'

    def ExecuteJS(self, js_code: str, session: str) -> str:
        return self.sessions[session].ExecuteJS(js_code) if hasattr(self.sessions[session], 'ExecuteJS') else 'ExecuteJS not supported in current browser.'

    def Edit(self, path: str, session: str) -> str:
        try:
            if session in self.sessions:
                self.sessions[session].Destroy()
                self.sessions.pop(session)
            self.sessions[session] = ATextBrowser(functions=self.functions)
            return self.prompt + '\n\n' + self.sessions[session].Edit(path) + '\n\n' + f'Session name: "{session}"\n'
        except Exception as e:
            print('EXCEPTION. e: ', str(e))
            return f'Browser Exception. please check your path input. EXCEPTION: {str(e)}\n{traceback.format_exc()}'
        return

    def GetFullText(self, session: str) -> str:
        return self.sessions[session].GetFullText() if session in self.sessions else f'ERROR: Invalid session name: {session}'

    def ScrollDown(self, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollUp(self, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

    def SearchDown(self, query: str, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].SearchDown(query=query) + '\n\n' + f'Session name: "{session}"\n'

    def SearchUp(self, query: str, session: str) -> str:
        return self.prompt + '\n\n' + self.sessions[session].SearchUp(query=query) + '\n\n' + f'Session name: "{session}"\n'

    def GetLink(self, text: str, session: str) -> str:
        return self.sessions[session].GetLink(text) if hasattr(self.sessions[session], 'GetLink') else 'GetLink not supported in current browser.'

    def Replace(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
        return self.sessions[session].Replace(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'Replace') else 'Replace not supported in current browser.'

    def ReplaceAll(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
        return self.sessions[session].ReplaceAll(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'ReplaceAll') else 'ReplaceAll not supported in current browser.'

    def SaveTo(self, dstPath: str, session: str) -> str:
        return self.sessions[session].SaveTo(dstPath) if hasattr(self.sessions[session], 'SaveTo') else 'SaveTo not supported in current browser.'

    def Destroy(self):
        for _, session in self.sessions.items():
            destroy = getattr(session, 'Destroy', None)
            if callable(destroy):
                destroy()
        self.sessions.clear()
        self.computer = None
        self.scripter = None
        return

def Destroy(self):
    for _, session in self.sessions.items():
        destroy = getattr(session, 'Destroy', None)
        if callable(destroy):
            destroy()
    self.sessions.clear()
    self.computer = None
    self.scripter = None
    return

class AudioSourceSileroVAD:

    def __init__(self, sr=16000):
        self.model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, onnx=False)
        self.sr = sr
        self.buffer = deque(maxlen=self.sr * 60)
        return

    def get(self):
        get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks = self.utils
        chunk_samples = 512
        vad_iterator = VADIterator(self.model)
        wav = []
        with sd.InputStream(samplerate=self.sr, channels=1, blocksize=chunk_samples, dtype=np.float32) as stream:
            currentTime = 0.0
            while True:
                audio_chunk, overflowed = stream.read(chunk_samples)
                audio_chunk = audio_chunk.reshape((chunk_samples,))
                self.buffer.append(list(audio_chunk))
                currentTime += float(len(audio_chunk)) / float(self.sr)
                startTime, endTime = (0.0, 0.0)
                speech_dict = vad_iterator(audio_chunk, return_seconds=True)
                if speech_dict:
                    if 'start' in speech_dict:
                        print('<---', flush=True)
                        startTime = speech_dict['start']
                    elif 'end' in speech_dict:
                        print('--->')
                        endTime = speech_dict['end']
                        frm = -int((currentTime - startTime) * self.sr // chunk_samples) - 3
                        to = -int((currentTime - endTime) * self.sr // chunk_samples)
                        wav = sum(list(self.buffer)[frm:to], [])
                        vad_iterator.reset_states()
                        self.buffer.clear()
                        return (np.array(wav), self.sr)

def get(self):
    get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks = self.utils
    chunk_samples = 512
    vad_iterator = VADIterator(self.model)
    wav = []
    with sd.InputStream(samplerate=self.sr, channels=1, blocksize=chunk_samples, dtype=np.float32) as stream:
        currentTime = 0.0
        while True:
            audio_chunk, overflowed = stream.read(chunk_samples)
            audio_chunk = audio_chunk.reshape((chunk_samples,))
            self.buffer.append(list(audio_chunk))
            currentTime += float(len(audio_chunk)) / float(self.sr)
            startTime, endTime = (0.0, 0.0)
            speech_dict = vad_iterator(audio_chunk, return_seconds=True)
            if speech_dict:
                if 'start' in speech_dict:
                    print('<---', flush=True)
                    startTime = speech_dict['start']
                elif 'end' in speech_dict:
                    print('--->')
                    endTime = speech_dict['end']
                    frm = -int((currentTime - startTime) * self.sr // chunk_samples) - 3
                    to = -int((currentTime - endTime) * self.sr // chunk_samples)
                    wav = sum(list(self.buffer)[frm:to], [])
                    vad_iterator.reset_states()
                    self.buffer.clear()
                    return (np.array(wav), self.sr)

class AProcessor:

    def __init__(self, name, modelID, promptName, llmPool, promptsManager, services, messenger, outputCB, gasTank, config, collection=None):
        self.name = name
        self.modelID = modelID
        self.llmPool = llmPool
        self.llm = llmPool.GetModel(modelID, promptName)
        self.promptsManager = promptsManager
        self.services = services
        self.messenger = messenger
        self.interpreter = AInterpreter(messenger)
        self.conversation = AConversations(proxy=services['computer'].Proxy)
        self.subProcessors = dict()
        self.modules = {}
        self.outputCB = outputCB
        self.gasTank = gasTank
        self.config = config
        self.collection = 'ailice' + str(time.time()) if collection is None else collection
        self.RegisterModules([config.services['storage']['addr']])
        self.interpreter.RegisterAction('CALL', {'func': self.EvalCall})
        self.interpreter.RegisterAction('RESPOND', {'func': self.EvalRespond})
        self.interpreter.RegisterAction('RETURN', {'func': self.Return})
        self.interpreter.RegisterAction('STORE', {'func': self.EvalStore})
        self.interpreter.RegisterAction('QUERY', {'func': self.EvalQuery})
        self.interpreter.RegisterAction('WAIT', {'func': self.EvalWait})
        self.interpreter.RegisterAction('DEFINE-CODE-VARS', {'func': self.DefineCodeVars})
        self.interpreter.RegisterAction('LOADEXTMODULE', {'func': self.LoadExtModule})
        self.interpreter.RegisterAction('LOADEXTPROMPT', {'func': self.LoadExtPrompt})
        self.prompt = promptsManager[promptName](processor=self, storage=self.modules['storage']['module'], collection=self.collection, conversations=self.conversation, formatter=self.llm.formatter, config=self.config, outputCB=self.outputCB)
        self.result = 'None.'
        self.modules['storage']['module'].Store(self.collection + '_functions', json.dumps({'module': 'core', 'action': 'LOADEXTMODULE', 'signature': 'LOADEXTMODULE<!|addr: str|!> -> str', 'prompt': 'Load the ext-module and get the list of callable functions in it. addr is a service address in the format protocol://ip:port.', 'type': 'primary'}))
        self.modules['storage']['module'].Store(self.collection + '_functions', json.dumps({'module': 'core', 'action': 'LOADEXTPROMPT', 'signature': 'LOADEXTPROMPT<!|path: str|!> -> str', 'prompt': 'Load ext-prompt from the path pointing to python source code file, which include available new agent type.', 'type': 'primary'}))
        return

    def RegisterAction(self, nodeType: str, action: dict):
        self.interpreter.RegisterAction(nodeType, action)
        return

    def RegisterModules(self, moduleAddrs):
        ret = []
        modules = {}
        funcList = []
        actions = {}
        for moduleAddr in moduleAddrs:
            module = self.services.GetClient(moduleAddr)
            if not hasattr(module, 'ModuleInfo') or not callable(getattr(module, 'ModuleInfo')):
                raise Exception('EXCEPTION: ModuleInfo() not found in module.')
            info = module.ModuleInfo()
            if 'NAME' not in info:
                raise Exception("EXCEPTION: 'NAME' is not found in module info.")
            if 'ACTIONS' not in info:
                raise Exception("EXCEPTION: 'ACTIONS' is not found in module info.")
            modules[info['NAME']] = {'addr': moduleAddr, 'module': module}
            for actionName, actionMeta in info['ACTIONS'].items():
                sig = actionName + str(inspect.signature(getattr(module, actionMeta['func']))).replace('(', '<!|').replace(')', '|!>')
                ret.append({'action': actionName, 'signature': sig, 'prompt': actionMeta['prompt']})
                actions[actionName] = {'func': self.CreateActionCB(actionName, module, actionMeta['func'])}
                funcList.append(json.dumps({'module': info['NAME'], 'action': actionName, 'signature': sig, 'prompt': actionMeta['prompt'], 'type': actionMeta['type']}))
        self.modules.get('storage', modules.get('storage', None))['module'].Store(self.collection + '_functions', funcList)
        for actionName, action in actions.items():
            self.RegisterAction(nodeType=actionName, action=action)
        self.modules.update(modules)
        return ret

    def CreateActionCB(self, actionName, module, actionFunc):
        func = getattr(module, actionFunc)

        def callback(*args, **kwargs):
            return func(*args, **kwargs)
        newSignature = inspect.Signature(parameters=[inspect.Parameter(name=t.name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=t.annotation) for p, t in inspect.signature(func).parameters.items()], return_annotation=inspect.signature(func).return_annotation)
        callback.__signature__ = newSignature
        return callback

    def GetPromptName(self) -> str:
        return self.prompt.PROMPT_NAME

    def SetGas(self, amount: int):
        self.gasTank.Set(amount)
        return

    def Prepare(self):
        self.RegisterModules(set(self.services.pool) - set([d['addr'] for name, d in self.modules.items()]))
        for nodeType, action in self.prompt.GetActions().items():
            self.interpreter.RegisterAction(nodeType, action)
        for nodeType, patterns in self.prompt.GetPatterns().items():
            for p in patterns:
                self.interpreter.RegisterPattern(nodeType, p['re'], p['isEntry'])
        self.interpreter.RegisterPattern('_FUNCTION_CALL_DEFAULT', FUNCTION_CALL_DEFAULT, True, True, 99999999)
        self.interpreter.RegisterAction('_FUNCTION_CALL_DEFAULT', {'func': self.EvalFunctionCallDefault, 'noEval': ['funcName', 'paras']})
        return

    def SaveMsg(self, role: str, msg: str, storeMsg: str=None, logMsg: str=None, logger=None, entry: bool=False):
        self.conversation.Add(role=role, msg=msg, env=self.interpreter.env, entry=entry)
        if storeMsg:
            self.EvalStore(storeMsg)
        if logMsg and logger:
            logger(f'{role}_{self.name}', logMsg)
        return

    def __call__(self, txt: str) -> str:
        self.SaveMsg(role='USER', msg=txt, storeMsg=txt, entry=True)
        with ALoggerSection(recv=self.outputCB) as loggerSection:
            loggerSection(f'USER_{self.name}', txt)
            while True:
                self.Prepare()
                prompt = self.prompt.BuildPrompt()
                try:
                    with ALoggerMsg(recv=self.outputCB, channel='ASSISTANT_' + self.name) as loggerMsg:
                        ret = self.llm.Generate(prompt, proc=loggerMsg, endchecker=self.interpreter.EndChecker, temperature=self.config.temperature, gasTank=self.gasTank)
                except Exception as e:
                    ret = f'An exception was encountered while generating the reply message. EXCEPTION:\n\n{str(e)}'
                    self.SaveMsg(role='ASSISTANT', msg=ret, storeMsg=ret)
                    raise e
                ret = 'System notification: The empty output was detected, which is usually caused by an agent error. You can urge it to resolve this issue and return meaningful information.' if '' == ret.strip() else ret
                self.SaveMsg(role='ASSISTANT', msg=ret, storeMsg=ret)
                self.result = ret
                try:
                    msg = self.messenger.GetPreviousMsg()
                    if str == type(msg) and '/stop' == msg.strip():
                        raise AExceptionStop()
                    elif msg != None:
                        resp = f'Interruption. Reminder from super user: {msg}'
                        self.SaveMsg(role='SYSTEM', msg=resp, storeMsg=resp, logMsg=resp, logger=loggerSection)
                        continue
                    resp = self.interpreter.EvalEntries(ret)
                    if '' != resp:
                        self.interpreter.EvalVar(varName='returned_content_in_last_function_call', content=resp)
                        m = 'This is a system-generated message. Since the function call in your previous message has returned information, the response to this message will be handled by the backend system instead of the user. Meanwhile, your previous message has been marked as private and has not been sent to the user. Function returned: {' + resp + "}\n\nThe returned text has been automatically saved to variable 'returned_content_in_last_function_call' for quick reference."
                        self.SaveMsg(role='SYSTEM', msg=m, storeMsg='Function returned: {' + resp + '}', logMsg=resp, logger=loggerSection)
                    else:
                        return self.result
                except AExceptionStop as e:
                    resp = 'Interruption. The task was terminated by the superuser.'
                    self.SaveMsg(role='SYSTEM', msg=resp, storeMsg=resp, logMsg=resp, logger=loggerSection)
                    resp = "I will stop here due to the superuser's request to terminate the task."
                    self.SaveMsg(role='ASSISTANT', msg=resp, storeMsg=resp, logMsg=resp, logger=loggerSection)
                    raise e

    def EvalCall(self, agentType: str, agentName: str, msg: str) -> str:
        if agentType not in self.promptsManager:
            return f'CALL FAILED. specified agentType {agentType} does not exist. This may be caused by using an agent type that does not exist or by getting the parameters in the wrong order.'
        if agentName not in self.subProcessors or agentType != self.subProcessors[agentName].GetPromptName():
            self.subProcessors[agentName] = AProcessor(name=agentName, modelID=self.modelID, promptName=agentType, llmPool=self.llmPool, promptsManager=self.promptsManager, services=self.services, messenger=self.messenger, outputCB=self.outputCB, gasTank=self.gasTank, config=self.config, collection=self.collection)
            self.subProcessors[agentName].RegisterModules([self.modules[moduleName]['addr'] for moduleName in self.modules])
        notifications = ''
        for varName in self.interpreter.env:
            if varName in msg:
                newName = self.subProcessors[agentName].interpreter.CreateVar(self.interpreter.env[varName], varName, dynamicSuffix=True)
                notifications += f'\n\nSystem notification: Variable `{varName}` detected in this msg. Content auto-retrieved from agent `{self.name}` and stored in {newName}.'
        resp = f'Agent {agentName} returned: {self.subProcessors[agentName](msg + notifications)}'
        notifications = ''
        for varName in self.subProcessors[agentName].interpreter.env:
            if varName in resp:
                newName = self.interpreter.CreateVar(self.subProcessors[agentName].interpreter.env[varName], varName, dynamicSuffix=True)
                notifications += f'\n\nSystem notification: Variable `{varName}` detected in this msg. Content auto-retrieved from agent `{agentName}` and stored in {newName}.'
        return resp + notifications

    def EvalRespond(self, message: str) -> str:
        self.result = message
        return ''

    def EvalStore(self, txt: str):
        self.modules['storage']['module'].Store(self.collection, txt)
        return

    def EvalQuery(self, query: str) -> str:
        res = self.modules['storage']['module'].Recall(collection=self.collection, query=query)
        return f'QUERY_RESULT=[{res}]'

    def Return(self) -> str:
        return ''

    def EvalWait(self, duration: int) -> str:
        time.sleep(duration)
        return f'Waiting is over. It has been {duration} seconds.'

    def DefineCodeVars(self) -> str:
        matches = re.findall('```(\\w*)\\n([\\s\\S]*?)```', self.conversation.GetConversations(frm=-1)[1]['msg'])
        vars = []
        for language, code in matches:
            varName = f'code_{language}_{str(random.randint(0, 10000))}'
            self.interpreter.env[varName] = code
            vars.append(varName)
        if 0 < len(vars):
            return f'\nSystem notification: The code snippets within the triple backticks in last message have been saved as variables, in accordance with their order in the text, the variable names are as follows: {vars}\n'
        else:
            return '\nSystem notification: No code snippet found. Are you sure you wrapped them with triple backticks?'

    def LoadExtModule(self, addr: str) -> str:
        try:
            ret = self.RegisterModules([addr])
            prompts = []
            for r in ret:
                self.interpreter.RegisterPattern(nodeType=r['action'], pattern=GenerateRE4FunctionCalling(r['signature'], faultTolerance=False), isEntry=True)
                prompts.append(f'{r['signature']}: {r['prompt']}')
            ret = '\n'.join(prompts)
        except Exception as e:
            ret = f'Exception: {str(e)}'
        return ret

    def LoadExtPrompt(self, path: str) -> str:
        ret = ''
        try:
            alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
            symbol = ''.join([secrets.choice(alphabet) for i in range(32)])
            moduleName = 'APrompt_' + symbol
            spec = importlib.util.spec_from_file_location(moduleName, path)
            promptModule = importlib.util.module_from_spec(spec)
            sys.modules[moduleName] = promptModule
            spec.loader.exec_module(promptModule)
            ret += self.promptsManager.RegisterPrompts([promptModule.APrompt])
            if '' == ret:
                ret += f'Prompt module {promptModule.APrompt.PROMPT_NAME} has been loaded. Its description information is as follows:\n{promptModule.APrompt.PROMPT_DESCRIPTION}'
        except Exception as e:
            ret = f'Exception: {str(e)}'
        return ret

    def EvalFunctionCallDefault(self, funcName: str, paras: str) -> str:
        if funcName not in self.interpreter.actions:
            return f"Error: Function call detected, but function name '{funcName}' does not exist."
        else:
            return f"Error: The function call to '{funcName}' failed, please check whether the number and type of parameters are correct. For example, the session name/agent type/url need to be of str type, and the str type needs to be enclosed in quotation marks, proper escaping may be necessary when quotation marks appear in strings, etc."

    def EnvSummary(self) -> str:
        return '\n'.join([f'{varName}: {type(var).__name__}  {str(var)[:50]}{('...[The remaining content is not shown]' if len(str(var)) > 50 else '')}' for varName, var in self.interpreter.env.items()]) + ('\nTo save context space, only the first fifty characters of each variable are shown here. You can use the PRINT function to view its complete contents.' if self.interpreter.env else '')

    def FromJson(self, data):
        self.name = data['name']
        self.interpreter.FromJson(data['interpreter'])
        self.conversation.FromJson(data['conversation'])
        self.collection = data['collection']
        for k, m in data['modules'].items():
            if k not in self.modules:
                try:
                    self.RegisterModules([m['addr']])
                except Exception as e:
                    print(f'FromJson(): RegisterModules FAILED on {k}: {m['addr']}')
                    continue
        self.prompt = self.promptsManager[data['agentType']](processor=self, storage=self.modules['storage']['module'], collection=self.collection, conversations=self.conversation, formatter=self.llm.formatter, config=self.config, outputCB=self.outputCB)
        if hasattr(self.prompt, 'FromJson'):
            self.prompt.FromJson(data['prompt'])
        for agentName, state in data['subProcessors'].items():
            self.subProcessors[agentName] = AProcessor(name=agentName, modelID=self.modelID, promptName=state['agentType'], llmPool=self.llmPool, promptsManager=self.promptsManager, services=self.services, messenger=self.messenger, outputCB=self.outputCB, gasTank=self.gasTank, config=self.config, collection=self.collection)
            self.subProcessors[agentName].RegisterModules([self.modules[m]['addr'] for m in self.modules])
            self.subProcessors[agentName].FromJson(state)
        return

    def ToJson(self):
        return {'name': self.name, 'modelID': self.modelID, 'agentType': self.prompt.PROMPT_NAME, 'prompt': self.prompt.ToJson() if hasattr(self.prompt, 'ToJson') else {}, 'interpreter': self.interpreter.ToJson(), 'conversation': self.conversation.ToJson(), 'collection': self.collection, 'modules': {k: {'addr': m['addr']} for k, m in self.modules.items()}, 'subProcessors': {k: p.ToJson() for k, p in self.subProcessors.items()}}

def RegisterModules(self, moduleAddrs):
    ret = []
    modules = {}
    funcList = []
    actions = {}
    for moduleAddr in moduleAddrs:
        module = self.services.GetClient(moduleAddr)
        if not hasattr(module, 'ModuleInfo') or not callable(getattr(module, 'ModuleInfo')):
            raise Exception('EXCEPTION: ModuleInfo() not found in module.')
        info = module.ModuleInfo()
        if 'NAME' not in info:
            raise Exception("EXCEPTION: 'NAME' is not found in module info.")
        if 'ACTIONS' not in info:
            raise Exception("EXCEPTION: 'ACTIONS' is not found in module info.")
        modules[info['NAME']] = {'addr': moduleAddr, 'module': module}
        for actionName, actionMeta in info['ACTIONS'].items():
            sig = actionName + str(inspect.signature(getattr(module, actionMeta['func']))).replace('(', '<!|').replace(')', '|!>')
            ret.append({'action': actionName, 'signature': sig, 'prompt': actionMeta['prompt']})
            actions[actionName] = {'func': self.CreateActionCB(actionName, module, actionMeta['func'])}
            funcList.append(json.dumps({'module': info['NAME'], 'action': actionName, 'signature': sig, 'prompt': actionMeta['prompt'], 'type': actionMeta['type']}))
    self.modules.get('storage', modules.get('storage', None))['module'].Store(self.collection + '_functions', funcList)
    for actionName, action in actions.items():
        self.RegisterAction(nodeType=actionName, action=action)
    self.modules.update(modules)
    return ret

def CreateActionCB(self, actionName, module, actionFunc):
    func = getattr(module, actionFunc)

    def callback(*args, **kwargs):
        return func(*args, **kwargs)
    newSignature = inspect.Signature(parameters=[inspect.Parameter(name=t.name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=t.annotation) for p, t in inspect.signature(func).parameters.items()], return_annotation=inspect.signature(func).return_annotation)
    callback.__signature__ = newSignature
    return callback

def callback(*args, **kwargs):
    return func(*args, **kwargs)

def EnvSummary(self) -> str:
    return '\n'.join([f'{varName}: {type(var).__name__}  {str(var)[:50]}{('...[The remaining content is not shown]' if len(str(var)) > 50 else '')}' for varName, var in self.interpreter.env.items()]) + ('\nTo save context space, only the first fifty characters of each variable are shown here. You can use the PRINT function to view its complete contents.' if self.interpreter.env else '')

class AConversations:

    def __init__(self, proxy):
        self.proxy = proxy
        self.conversations: list[dict] = []
        return

    def Add(self, role: str, msg: str, env: dict[str, Any], entry: bool=False):
        msg = '<EMPTY MSG>' if '' == msg else msg
        record = {'role': role, 'time': time.time(), 'entry': entry, 'msg': msg, 'attachments': []}
        if role in ['USER', 'SYSTEM']:
            matches = re.findall('```(\\w*)\\n([\\s\\S]*?)```', msg)
            vars = []
            for language, code in matches:
                varName = f'code_{language}_{str(random.randint(0, 10000))}'
                env[varName] = code
                vars.append(varName)
            if 0 < len(vars):
                record['msg'] += f'\nSystem notification: The code snippets within the triple backticks in this message have been saved as variables, in accordance with their order in the text, the variable names are as follows: {vars}\n'
            matches = [m for m in re.findall('(!\\[([^\\]]*?)\\]\\((.*?)\\)(?:<([a-zA-Z0-9_\\-&]+)>)?)', msg)]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.ProcessMultimodalTags, m, param, label, env) for m, txt, param, label in matches]
                for future, match in zip(concurrent.futures.as_completed(futures), matches):
                    try:
                        m, txt, param, label = match
                        result = future.result()
                        if isinstance(result, Exception):
                            msgNew = msg.replace(m, f'{m}\n(System notification: Unable to get multimodal content: {e})')
                            record['msg'] = msgNew
                        elif None != result:
                            record['attachments'].append(result)
                    except Exception as e:
                        record['msg'] += f'\nSystem notification: Exception encountered while processing multimodal tags: {str(e)}'
        self.conversations.append(record)
        return

    def ProcessMultimodalTags(self, m, param, label, env):
        if '&' == label:
            if '' == param or param not in env:
                raise ValueError(f'variable name ({param}) not defined.')
            return {'type': typeInfo[type(env[param])]['modal'], 'tag': m, 'content': env[param].Standardize()}
        elif '' != label:
            targetType = [t for t in typeInfo if t.__name__ == label]
            if 0 == len(targetType):
                raise ValueError(f'modal type: {label} not found. supported modal type list: {[str(t.__name__) for t in typeInfo]}. please check your input.')
            else:
                return {'type': typeInfo[targetType[0]]['modal'], 'tag': m, 'content': targetType[0](param).Standardize()}
        else:
            mimeType = GuessMediaType(param)
            if 'image' in mimeType:
                return {'type': 'image', 'tag': m, 'content': AImageLocation(urlOrPath=param).Standardize(self.proxy)}
            elif 'video' in mimeType:
                return {'type': 'video', 'tag': m, 'content': AVideoLocation(urlOrPath=param).Standardize(self.proxy)}
            return

    def LatestEntry(self):
        for i in range(len(self.conversations)):
            if self.conversations[-i - 1]['entry']:
                break
        return -(i + 1) // 2 if 'ASSISTANT' == self.conversations[-1]['role'] else (-i - 2) // 2

    def GetConversations(self, frm=0):
        s = 2 * frm if frm >= 0 or 'ASSISTANT' == self.conversations[-1]['role'] else 2 * frm + 1
        return self.conversations[s:]

    def __len__(self):
        return (len(self.conversations) + 1) // 2

    def FromJson(self, data):

        def AddRecord(role, time, entry, msg, attachments):
            self.conversations.append({'role': role, 'time': time, 'entry': entry, 'msg': msg, 'attachments': attachments})
        for i in range(0, len(data)):
            d = data[i]
            if i > 0:
                assert not {d['role'], data[i - 1]['role']} <= {'ASSISTANT'}, f'Consecutive ASSISTANT messages were found in conversations. {str(d)}, {str(data[i - 1])}'
                if {d['role'], data[i - 1]['role']} <= {'USER', 'SYSTEM'}:
                    AddRecord('ASSISTANT', None, False, '<EMPTY MSG>', [])
            AddRecord(d['role'], d.get('time', None), d.get('entry', None), d['msg'] if '' != d['msg'] else '<EMPTY MSG>', [{'type': a['type'], 'tag': a.get('tag', None), 'content': FromJson(a['content'])} for a in d['attachments']])
        if len(data) > 0 and data[-1]['role'] in ['USER', 'SYSTEM']:
            AddRecord('ASSISTANT', None, False, '<EMPTY MSG>', [])
        return

    def ToJson(self) -> str:
        return [{'role': record['role'], 'time': record['time'], 'entry': record['entry'], 'msg': record['msg'], 'attachments': [{'type': a['type'], 'tag': a['tag'], 'content': ToJson(a['content'])} for a in record['attachments']]} for record in self.conversations]

def AddRecord(role, time, entry, msg, attachments):
    self.conversations.append({'role': role, 'time': time, 'entry': entry, 'msg': msg, 'attachments': attachments})

class AInterpreter:

    def __init__(self, messenger):
        self.actions = {}
        self.patterns = []
        self.env = {}
        self.messenger = messenger
        self.RegisterPattern('_STR', f'(?P<txt>({ARegexMap['str']}))', False)
        self.RegisterPattern('_INT', f'(?P<txt>({ARegexMap['int']}))', False)
        self.RegisterPattern('_FLOAT', f'(?P<txt>({ARegexMap['float']}))', False)
        self.RegisterPattern('_BOOL', f'(?P<txt>({ARegexMap['bool']}))', False)
        self.RegisterPattern('_VAR', VAR_DEF, True)
        self.RegisterPattern('_PRINT', GenerateRE4FunctionCalling('PRINT<!|txt: str|!> -> str', faultTolerance=True), True)
        self.RegisterAction('_PRINT', {'func': self.EvalPrint})
        self.RegisterPattern('_VAR_REF', f'(?P<varName>({ARegexMap['ref']}))', False)
        self.RegisterPattern('_EXPR_CAT', f'(?P<expr>({ARegexMap['expr_cat']}))', False)
        for dataType in typeInfo:
            if not typeInfo[dataType]['tag']:
                continue
            self.RegisterPattern(f'_EXPR_OBJ_{dataType.__name__}', GenerateRE4ObjectExpr([(fieldName, fieldInfo.annotation.__name__) for fieldName, fieldInfo in dataType.model_fields.items()], dataType.__name__, faultTolerance=True), False)
            self.RegisterAction(f'_EXPR_OBJ_{dataType.__name__}', {'func': self.CreateObjCB(dataType)})
        self.RegisterPattern('_EXPR_OBJ_DEFAULT', EXPR_OBJ, False)
        self.RegisterAction('_EXPR_OBJ_DEFAULT', {'func': self.EvalObjDefault, 'noEval': ['typeBra', 'typeKet']})
        return

    def RegisterAction(self, nodeType: str, action: dict):
        signature = inspect.signature(action['func'])
        if not all([param.annotation != inspect.Parameter.empty for param in signature.parameters.values()]):
            print('Need annotations in registered function. node type: ', nodeType)
            exit()
        self.actions[nodeType] = {k: v for k, v in action.items()}
        self.actions[nodeType]['signature'] = signature
        return

    def RegisterPattern(self, nodeType: str, pattern: str, isEntry: bool, noTrunc: bool=False, priority: int=0):
        p = {'nodeType': nodeType, 're': pattern, 'isEntry': isEntry, 'noTrunc': noTrunc, 'priority': priority}
        if pattern not in [p['re'] for p in self.patterns]:
            loc = 0
            for loc in range(0, len(self.patterns)):
                if self.patterns[loc]['priority'] > priority:
                    break
            self.patterns.insert(loc, p)
        return

    def CreateVar(self, content: Any, basename: str, dynamicSuffix: bool=True) -> str:
        if dynamicSuffix and basename not in self.env:
            varName = basename
        else:
            varName = f'{basename}_{type(content).__name__}_{str(random.randint(0, 999999))}'
        self.env[varName] = content
        return varName

    def EndChecker(self, txt: str) -> bool:
        endPatterns = [p['re'] for p in self.patterns if p['isEntry'] and (not p['noTrunc']) and (HasReturnValue(self.actions[p['nodeType']]) if p['nodeType'] in self.actions else False)]
        return any([bool(re.findall(pattern, txt, re.DOTALL)) for pattern in endPatterns]) or None != self.messenger.Get()

    def GetEntryPatterns(self) -> dict[str, str]:
        return [(p['nodeType'], p['re']) for p in self.patterns if p['isEntry']]

    def Parse(self, txt: str) -> tuple[str, dict[str, str]]:
        for p in self.patterns:
            m = re.fullmatch(p['re'], txt, re.DOTALL)
            if m:
                return (p['nodeType'], m.groupdict())
        return (None, None)

    def CallWithTextArgs(self, nodeType, txtArgs) -> Any:
        action = self.actions[nodeType]
        signature = action['signature']
        if set(txtArgs.keys()) != set(signature.parameters.keys()):
            return 'The function call failed because the arguments did not match. txtArgs.keys(): ' + str(txtArgs.keys()) + '. func params: ' + str(signature.parameters.keys())
        paras = dict()
        for k, v in txtArgs.items():
            paras[k] = v if k in action.get('noEval', []) else self.Eval(v)
            if type(paras[k]) != signature.parameters[k].annotation:
                raise TypeError(f'parameter {k} should be of type {signature.parameters[k].annotation.__name__}, but got {type(paras[k]).__name__}.')
        return action['func'](**paras)

    def Eval(self, txt: str) -> Any:
        nodeType, paras = self.Parse(txt)
        if None == nodeType:
            return txt
        elif '_STR' == nodeType:
            return self.EvalStr(txt)
        elif '_INT' == nodeType:
            return int(txt)
        elif '_FLOAT' == nodeType:
            return float(txt)
        elif '_BOOL' == nodeType:
            return {'true': True, 'false': False}[txt.strip().lower()]
        elif '_VAR' == nodeType:
            return self.EvalVar(varName=paras['varName'], content=self.Eval(paras['content']))
        elif '_VAR_REF' == nodeType:
            return self.EvalVarRef(txt)
        elif '_EXPR_CAT' == nodeType:
            return self.EvalExprCat(txt)
        else:
            return self.CallWithTextArgs(nodeType, paras)

    def ParseEntries(self, txt_input: str) -> list[str]:
        ms = {}
        for nodeType, pattern in self.GetEntryPatterns():
            for match in re.finditer(pattern, txt_input, re.DOTALL):
                ms[match.start(), match.end()] = match
        matches = sorted(list(ms.values()), key=lambda match: match.start())
        ret = []
        for match in matches:
            isSubstring = any((m.start() <= match.start() and m.end() >= match.end() and (m is not match) for m in matches))
            if not isSubstring:
                ret.append(match.group(0))
        return ret

    def EvalEntries(self, txt: str) -> str:
        scripts = self.ParseEntries(txt)
        resp = ''
        try:
            for script in scripts:
                r = self.Eval(script)
                r = self.ConvertToText(r)
                if r not in ['', None]:
                    resp += r + '\n\n'
        except SyntaxError as e:
            resp += f'EXCEPTION: {str(e)}\n{traceback.format_exc()}\n'
            if 'unterminated string literal' in str(e):
                resp += 'Please check if there are any issues with your string syntax. For instance, are you using a newline within a single-quoted string? Or should you use triple quotes to avoid error-prone escape sequences?'
        except AExceptionStop as e:
            raise e
        except AExceptionOutofGas as e:
            resp += 'The current task has run out of gas and has been terminated. Please ask the user to help recharge gas.'
        except Exception as e:
            resp += f'EXCEPTION: {str(e)}\n{(e.tb if hasattr(e, 'tb') else traceback.format_exc())}'
        return resp

    def EvalStr(self, txt: str) -> str:
        return ast.literal_eval(txt)

    def EvalVarRef(self, varName: str) -> Any:
        if varName in self.env:
            return self.env[varName]
        else:
            raise ValueError(f'Variable name {varName} NOT FOUND, did you mean to use a string "{varName}" but forgot the quotation marks?')

    def EvalVar(self, varName: str, content: Any):
        self.env[varName] = content
        return

    def EvalExprCat(self, expr: str) -> str:
        pattern = f'{ARegexMap['str']}|{ARegexMap['ref']}'
        ret = ''
        for match in re.finditer(pattern, expr):
            ret += self.Eval(match.group(0))
        return ret

    def EvalObjDefault(self, typeBra: str, args: str, typeKet: str) -> Any:
        if typeBra != typeKet:
            raise ValueError(f'The left and right types in braket should be the same. But in fact the left side is ({typeBra}), and the right side is ({typeKet}). Please correct your syntax.')
        if typeBra not in [t.__name__ for t in typeInfo.keys()] + ['&', '!']:
            raise ValueError(f'The specified object type ({typeBra}) is not supported. Please check your input.')
        if '!' == typeBra.strip():
            return args
        elif '&' == typeBra.strip():
            return self.env.get(args.strip())
        else:
            raise ValueError(f'It looks like you are trying to create an object of type ({typeBra}), but syntax parsing fails for unrecognized reasons. Please check your syntax.')

    def EvalPrint(self, txt: str) -> str:
        return txt

    def CreateObjCB(self, dataType):

        def callback(*args, **kwargs):
            return dataType(*args, **kwargs)
        newSignature = inspect.Signature(parameters=[inspect.Parameter(name=t.name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=t.annotation) for p, t in inspect.signature(dataType.__init__).parameters.items() if t.name != 'self'], return_annotation=dataType)
        callback.__signature__ = newSignature
        return callback

    def ConvertToText(self, r) -> str:
        if type(r) == str or r is None:
            return r
        elif type(r) in typeInfo:
            varName = self.CreateVar(content=r, basename='ret')
            return f'![Returned data is stored to variable: {varName} := {str(r)}]({varName})<&>'
        elif type(r) == list:
            return f'{str([self.ConvertToText(item) for item in r])}'
        elif type(r) == tuple:
            return f'{str((self.ConvertToText(item) for item in r))}'
        elif type(r) == dict:
            res = {k: self.ConvertToText(v) for k, v in r.items()}
            return f'{str(res)}'
        else:
            return str(r)

    def ToJson(self):
        return {'env': {k: ToJson(v) for k, v in self.env.items()}}

    def FromJson(self, data):
        self.env = {k: FromJson(v) for k, v in data['env'].items()}
        return

def EvalStr(self, txt: str) -> str:
    return ast.literal_eval(txt)

def CreateObjCB(self, dataType):

    def callback(*args, **kwargs):
        return dataType(*args, **kwargs)
    newSignature = inspect.Signature(parameters=[inspect.Parameter(name=t.name, kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=t.annotation) for p, t in inspect.signature(dataType.__init__).parameters.items() if t.name != 'self'], return_annotation=dataType)
    callback.__signature__ = newSignature
    return callback

def FromJson(self, data):
    self.env = {k: FromJson(v) for k, v in data['env'].items()}
    return

