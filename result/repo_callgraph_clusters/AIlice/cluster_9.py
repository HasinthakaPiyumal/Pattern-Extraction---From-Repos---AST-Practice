# Cluster 9

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

def StoreConfig(self):
    userCfg = {'agentModelConfig': self.config.agentModelConfig, 'models': {providerName: {k: v for k, v in providerCfg.items() if k != 'modelList'} for providerName, providerCfg in self.config.models.items() if providerName not in ['default']}, 'temperature': self.config.temperature, 'contextWindowRatio': self.config.contextWindowRatio}
    config_path = self.GetPath(pathType='user_config')
    with open(config_path, 'w') as f:
        json.dump(userCfg, f, indent=2)
    logger.info(f'User configuration stored to {config_path}')
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

class KMsgQue:

    def __init__(self):
        self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
        self.depth = -1
        self.buffer = []
        self.queue = queue.Queue()
        return

    def ParseChannel(self, channel: str) -> tuple[str]:
        if channel in ['<', '>']:
            return (channel, '')
        l = channel.find('_')
        channelType, agentName = (channel[:l], channel[l + 1:])
        return (channelType, agentName)

    def SinkPrint(self, channel: str, txt: str=None, action: str=''):
        channelType, agentName = self.ParseChannel(channel)
        if 'open' == action:
            print(colored(channel + ': ', self.colorMap[channelType]), txt, end='', flush=True)
        elif 'append' == action:
            print(txt, end='', flush=True)
        elif 'close' == action:
            print(txt, end='', flush=True)
            print('')
        else:
            print(colored(channel + ': ', self.colorMap[channelType]), txt)
        return

    def SinkBuffer(self, channel: str, txt: str=None, action: str=''):
        if '>' == channel:
            if -1 == self.depth:
                self.queue.put({'message': '', 'role': '', 'action': '', 'msgType': ''})
        elif '<' == channel:
            return
        else:
            self.queue.put({'message': txt, 'role': channel, 'action': action, 'msgType': 'internal' if self.depth > 0 or self.ParseChannel(channel)[0] == 'SYSTEM' else 'user-ailice'})
        return

    def Load(self, messages: list):
        self.buffer = copy.deepcopy(messages)
        return

    def Get(self, timeout=None, getBuffer=False):
        if getBuffer:
            return copy.deepcopy(self.buffer)
        else:
            msg = self.queue.get(timeout=timeout)
            msg['isRoundEnd'] = self.depth == -1 and msg['role'] == ''
            if not msg['isRoundEnd']:
                self.buffer.append(msg)
            return msg

    def Receiver(self, channel: str, txt: str=None, action: str=''):
        braketMap = {'<': 1, '>': -1}
        self.depth += braketMap[channel] if channel in braketMap else 0
        channelType, _ = self.ParseChannel(channel)
        if channelType in ['ASSISTANT', 'SYSTEM']:
            self.SinkPrint(channel=channel, txt=txt, action=action)
        if channelType in ['ASSISTANT', 'SYSTEM', '>'] or ('USER' == channelType and self.depth == 0):
            self.SinkBuffer(channel=channel, txt=txt, action=action)
        return

def __init__(self):
    self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
    self.depth = -1
    self.buffer = []
    self.queue = queue.Queue()
    return

class TaskSession:
    states = ['init', 'ready', 'generating', 'interrupted', 'stopping']

    def __init__(self, sessionName, sessionPath, clientSecretFile, serverPublicFile):
        self.sessionName = sessionName
        self.title = None
        self.sessionPath = sessionPath
        self.clientSecretFile = str(clientSecretFile)
        self.serverPublicFile = str(serverPublicFile)
        self.config = None
        self.threadLLM = None
        self.clientPool = None
        self.processor = None
        self.llmPool = None
        self.messenger = None
        self.alogger = None
        self.stopFlag = False
        self.streamNum = 0
        self.machine = LockedMachine(model=self, states=TaskSession.states, initial='init')
        self.machine.add_transition(trigger='create', source='init', dest='ready')
        self.machine.add_transition(trigger='stop', source='*', dest='stopping')
        self.machine.add_transition(trigger='release', source='stopping', dest='init')
        self.machine.add_transition(trigger='upload', source=['ready', 'interrupted'], dest='=')
        self.machine.add_transition(trigger='input', source='ready', dest='generating')
        self.machine.add_transition(trigger='interrupt', source=['generating', 'interrupted'], dest='interrupted')
        self.machine.add_transition(trigger='sendmsg', source='interrupted', dest='generating')
        self.machine.add_transition(trigger='answered', source='generating', dest='ready')
        self.machine.add_transition(trigger='dump', source=['ready', 'stopping'], dest='=')
        self.machine.add_transition(trigger='desc', source='*', dest='=')
        self.machine.add_transition(trigger='stream', source='*', dest='=')
        self.methodLock = threading.RLock()
        logger.debug(f'TaskSession initialized: {sessionName}')
        return

    @atomic_transition('dump')
    def Save(self):
        if self.sessionPath is not None and self.processor is not None:
            try:
                history_path = os.path.join(self.sessionPath, 'ailice_history.json')
                with open(history_path, 'w') as f:
                    json.dump(self.processor.ToJson(), f, indent=2)
                logger.info(f'Saved history to {history_path}')
            except Exception as e:
                logger.error(f'TaskSession::Save() Exception: Dump history FAILED. {str(e)}', exc_info=True)
        return

    @atomic_transition('create')
    def Create(self, config):
        sessionName, sessionPath = (self.sessionName, self.sessionPath)
        self.config = config
        logger.info(f'Creating session {sessionName} at {sessionPath}')
        os.makedirs(sessionPath, exist_ok=True)
        os.makedirs(os.path.join(sessionPath, 'storage'), exist_ok=True)
        os.makedirs(os.path.join(sessionPath, 'uploads'), exist_ok=True)
        history = None
        p = os.path.join(sessionPath, 'ailice_history.json')
        if os.path.exists(p):
            with open(p, 'r') as f:
                if os.path.getsize(p) > 0:
                    history = json.load(f)
                    logger.info(f'Loaded history from {p}')
                else:
                    logger.info(f'Empty history file: {p}')
        self.CreateAilice(history=history)
        logger.info(f'Session {sessionName} created successfully')
        return

    def CreateAilice(self, history: typing.Optional[dict]=None):
        sessionName, sessionPath = (self.sessionName, self.sessionPath)
        self.clientPool = AClientPool()
        for i in range(5):
            try:
                self.clientPool.Init()
                logger.info('Client pool initialized successfully')
                break
            except Exception as e:
                if i == 4:
                    error_msg = f'It seems that some peripheral module services failed to start. EXCEPTION: {str(e)}'
                    logger.error(error_msg, exc_info=True)
                    if hasattr(e, 'tb'):
                        logger.error(e.tb)
                    else:
                        logger.error(traceback.format_exc())
                time.sleep(5)
                continue
        self.InitSpeech(self.clientPool)
        logger.info('Starting vector database. This may include downloading model weights.')
        storage = self.clientPool.GetClient(self.config.services['storage']['addr'])
        with storage.Timeout(-1):
            msg = storage.Open(os.path.join(sessionPath, 'storage'))
        logger.info(f'Storage response: {msg}')
        llmPool = ALLMPool(config=self.config)
        llmPool.Init([self.config.modelID])
        logger.info(f'LLM Pool initialized with model: {self.config.modelID}')
        promptsManager = APromptsManager()
        promptsManager.Init(storage=storage, collection=sessionName)
        promptsManager.RegisterPrompts([APromptChat, APromptMain, APromptSearchEngine, APromptResearcher, APromptCoder, APromptModuleCoder, APromptCoderProxy, APromptDocReader])
        logger.info('Prompts manager initialized and prompts registered')
        messenger = AMessenger()
        alogger = KMsgQue()
        alogger.Load(ExtractMessages(history, 0))
        processor = AProcessor(name='AIlice', modelID=self.config.modelID, promptName=self.config.prompt, llmPool=llmPool, promptsManager=promptsManager, services=self.clientPool, messenger=messenger, outputCB=alogger.Receiver, gasTank=AGasTank(100000000.0), config=self.config, collection=sessionName)
        moduleList = [self.config.services['arxiv']['addr'], self.config.services['google']['addr'], self.config.services['duckduckgo']['addr'], self.config.services['browser']['addr'], self.config.services['scripter']['addr'], self.config.services['computer']['addr']]
        if self.config.speechOn:
            moduleList.append(self.config.services['speech']['addr'])
        processor.RegisterModules(moduleList)
        logger.info(f'Processor initialized with {len(moduleList)} modules')
        if history is not None:
            processor.FromJson(history)
            self.title = history['conversation'][0]['msg'] if len(history['conversation']) > 0 else 'New Chat'
            logger.info(f'History Loaded.')
        self.processor = processor
        self.llmPool = llmPool
        self.messenger = messenger
        self.alogger = alogger
        logger.info(f'Session {sessionName} created successfully')
        return

    @atomic_transition('stop')
    def Stop(self):
        try:
            logger.info(f'Stopping session {self.sessionName}')
            self.stopFlag = True
            if self.threadLLM is not None and self.threadLLM.is_alive():
                logger.info('Stopping active LLM thread')
                self.messenger.Lock()
                self.messenger.Put('/stop')
                self.messenger.Unlock()
            logger.info(f'Session {str(self.sessionName)} stop triggered')
        except Exception as e:
            logger.error(f'Session {str(self.sessionName)} stop FAILED. {str(e)}\n\ntraceback: {traceback.format_exc()}')
            pass
        return

    @atomic_transition('release')
    def Release(self):
        try:
            logger.info(f'Releasing session {self.sessionName}')
            if self.threadLLM is not None and self.threadLLM.is_alive():
                logger.info(f'Thread is still alive while releasing session {self.sessionName}, TERMINATE NOW.')
                StopThread(self.threadLLM)
            if self.clientPool is not None:
                logger.info(f'Destroy client pool.')
                self.clientPool.Destroy()
            self.threadLLM = None
            self.processor = None
            self.llmPool = None
            self.messenger = None
            self.alogger = None
            self.config = None
            self.title = None
            logger.info(f'Session {str(self.sessionName)} released')
        except Exception as e:
            logger.error(f'Session {str(self.sessionName)} release FAILED. {str(e)}\n\ntraceback: {traceback.format_exc()}')
            pass
        return

    def IsStopped(self) -> bool:
        return (self.threadLLM is None or not self.threadLLM.is_alive()) and 0 == self.streamNum

    def InitSpeech(self, clientPool):
        if self.config.speechOn:
            import sounddevice as sd
            logger.info('Initializing speech module')
            self.speech = clientPool.GetClient(self.config.services['speech']['addr'])
            logger.info('Preparing speech recognition and TTS models. This may include downloading weight data.')
            with self.speech.Timeout(-1):
                self.speech.PrepareModel()
            logger.info('Speech module model preparation completed')
            if any([re.fullmatch('(cuda|cpu)(:(\\d+))?', s) == None for s in [self.config.ttsDevice, self.config.sttDevice]]):
                error_msg = 'The value of ttsDevice and sttDevice should be a valid cuda device, such as cuda, cuda:0, or cpu, the default is cpu.'
                logger.error(error_msg)
                exit(-1)
            else:
                self.speech.SetDevices({'tts': self.config.ttsDevice, 'stt': self.config.sttDevice})
                logger.info(f'Speech devices set: TTS={self.config.ttsDevice}, STT={self.config.sttDevice}')
        else:
            self.speech = None
            logger.debug('Speech module not enabled')
        return

    @atomic_transition('desc')
    def Description(self) -> dict[str, str]:
        logger.info(f'Get decription of session {self.sessionName}')
        return {'sessionName': self.sessionName, 'title': self.title, 'state': self.state}

    @atomic_transition('stream')
    def MsgStream(self) -> typing.Generator:
        if self.stopFlag:
            return
        self.streamNum += 1
        try:
            buffer = self.alogger.Get(getBuffer=True)
            if len(buffer) > 0:
                yield f'data: {json.dumps(buffer)}\n\n'
            while not self.stopFlag:
                try:
                    msg = self.alogger.Get(timeout=1)
                except Empty as e:
                    continue
                yield f'data: {json.dumps(msg)}\n\n'
        except Exception as e:
            error_msg = {'error': f'Stream error: {e}', 'type': 'error'}
            logger.error(f'Stream error: {e}', exc_info=True)
            yield f'data: {json.dumps(error_msg)}\n\n'
        finally:
            self.streamNum -= 1

    @atomic_transition('input')
    def Message(self, msg: str):
        logger.info(f'Chat request received in session {self.sessionName}')
        logger.debug(f'Message content: {msg[:50]}...' if len(msg) > 50 else f'Message content: {msg}')
        if self.title in [None, 'New Chat']:
            self.title = msg
        logger.info(f'Generating response for message in session {self.sessionName}')

        def response(msg: str):
            try:
                self.processor(msg)
            except Exception as e:
                pass
            finally:
                if 'generating' == self.state:
                    self.answered()
                self.Save()
        self.processor.SetGas(100000000.0)
        self.threadLLM = threading.Thread(target=response, args=(msg,))
        self.threadLLM.start()
        return

    @atomic_transition('upload')
    def UploadFile(self, fileName: str, fileData: bytes, contentType: str) -> str:
        filename = secure_filename(fileName)
        filepath = os.path.join(self.sessionPath, 'uploads', filename)
        with open(filepath, 'wb') as f:
            f.write(fileData)
        logger.info(f"{contentType} file '{filename}' uploaded to {filepath}")
        return filepath

    @atomic_transition('interrupt')
    def Interrupt(self):
        logger.info(f'Interrupting session {self.sessionName}')
        self.messenger.Lock()
        return

    @atomic_transition('sendmsg')
    def SendMsg(self, msg: str):
        logger.info(f'Sending message to session {self.sessionName}')
        logger.debug(f'Message content: {msg[:50]}...' if len(msg) > 50 else f'Message content: {msg}')
        self.messenger.Put(msg)
        self.messenger.Unlock()
        return

    def Proxy(self, href: str, method: str) -> typing.Generator:
        logger.debug(f'Proxy request for {href} with method {method}')
        var = self.processor.interpreter.env.get(href, None)
        if var and type(var).__name__ in ['AImage', 'AVideo']:
            logger.debug(f'Proxy request resolved as variable of type {type(var).__name__}')
            yield {'type': 'variable', 'data': var}
        else:
            logger.debug(f'Proxy request forwarded to computer module')
            computer = self.processor.services['computer']
            res = computer.Proxy(href, method)
            responseInfo = next(res)
            yield {'type': 'href', 'responseInfo': responseInfo}
            yield from res

@atomic_transition('dump')
def Save(self):
    if self.sessionPath is not None and self.processor is not None:
        try:
            history_path = os.path.join(self.sessionPath, 'ailice_history.json')
            with open(history_path, 'w') as f:
                json.dump(self.processor.ToJson(), f, indent=2)
            logger.info(f'Saved history to {history_path}')
        except Exception as e:
            logger.error(f'TaskSession::Save() Exception: Dump history FAILED. {str(e)}', exc_info=True)
    return

@atomic_transition('create')
def Create(self, config):
    sessionName, sessionPath = (self.sessionName, self.sessionPath)
    self.config = config
    logger.info(f'Creating session {sessionName} at {sessionPath}')
    os.makedirs(sessionPath, exist_ok=True)
    os.makedirs(os.path.join(sessionPath, 'storage'), exist_ok=True)
    os.makedirs(os.path.join(sessionPath, 'uploads'), exist_ok=True)
    history = None
    p = os.path.join(sessionPath, 'ailice_history.json')
    if os.path.exists(p):
        with open(p, 'r') as f:
            if os.path.getsize(p) > 0:
                history = json.load(f)
                logger.info(f'Loaded history from {p}')
            else:
                logger.info(f'Empty history file: {p}')
    self.CreateAilice(history=history)
    logger.info(f'Session {sessionName} created successfully')
    return

@atomic_transition('stop')
def Stop(self):
    try:
        logger.info(f'Stopping session {self.sessionName}')
        self.stopFlag = True
        if self.threadLLM is not None and self.threadLLM.is_alive():
            logger.info('Stopping active LLM thread')
            self.messenger.Lock()
            self.messenger.Put('/stop')
            self.messenger.Unlock()
        logger.info(f'Session {str(self.sessionName)} stop triggered')
    except Exception as e:
        logger.error(f'Session {str(self.sessionName)} stop FAILED. {str(e)}\n\ntraceback: {traceback.format_exc()}')
        pass
    return

@atomic_transition('release')
def Release(self):
    try:
        logger.info(f'Releasing session {self.sessionName}')
        if self.threadLLM is not None and self.threadLLM.is_alive():
            logger.info(f'Thread is still alive while releasing session {self.sessionName}, TERMINATE NOW.')
            StopThread(self.threadLLM)
        if self.clientPool is not None:
            logger.info(f'Destroy client pool.')
            self.clientPool.Destroy()
        self.threadLLM = None
        self.processor = None
        self.llmPool = None
        self.messenger = None
        self.alogger = None
        self.config = None
        self.title = None
        logger.info(f'Session {str(self.sessionName)} released')
    except Exception as e:
        logger.error(f'Session {str(self.sessionName)} release FAILED. {str(e)}\n\ntraceback: {traceback.format_exc()}')
        pass
    return

def IsStopped(self) -> bool:
    return (self.threadLLM is None or not self.threadLLM.is_alive()) and 0 == self.streamNum

@atomic_transition('desc')
def Description(self) -> dict[str, str]:
    logger.info(f'Get decription of session {self.sessionName}')
    return {'sessionName': self.sessionName, 'title': self.title, 'state': self.state}

@atomic_transition('stream')
def MsgStream(self) -> typing.Generator:
    if self.stopFlag:
        return
    self.streamNum += 1
    try:
        buffer = self.alogger.Get(getBuffer=True)
        if len(buffer) > 0:
            yield f'data: {json.dumps(buffer)}\n\n'
        while not self.stopFlag:
            try:
                msg = self.alogger.Get(timeout=1)
            except Empty as e:
                continue
            yield f'data: {json.dumps(msg)}\n\n'
    except Exception as e:
        error_msg = {'error': f'Stream error: {e}', 'type': 'error'}
        logger.error(f'Stream error: {e}', exc_info=True)
        yield f'data: {json.dumps(error_msg)}\n\n'
    finally:
        self.streamNum -= 1

@atomic_transition('input')
def Message(self, msg: str):
    logger.info(f'Chat request received in session {self.sessionName}')
    logger.debug(f'Message content: {msg[:50]}...' if len(msg) > 50 else f'Message content: {msg}')
    if self.title in [None, 'New Chat']:
        self.title = msg
    logger.info(f'Generating response for message in session {self.sessionName}')

    def response(msg: str):
        try:
            self.processor(msg)
        except Exception as e:
            pass
        finally:
            if 'generating' == self.state:
                self.answered()
            self.Save()
    self.processor.SetGas(100000000.0)
    self.threadLLM = threading.Thread(target=response, args=(msg,))
    self.threadLLM.start()
    return

@atomic_transition('upload')
def UploadFile(self, fileName: str, fileData: bytes, contentType: str) -> str:
    filename = secure_filename(fileName)
    filepath = os.path.join(self.sessionPath, 'uploads', filename)
    with open(filepath, 'wb') as f:
        f.write(fileData)
    logger.info(f"{contentType} file '{filename}' uploaded to {filepath}")
    return filepath

@atomic_transition('interrupt')
def Interrupt(self):
    logger.info(f'Interrupting session {self.sessionName}')
    self.messenger.Lock()
    return

@atomic_transition('sendmsg')
def SendMsg(self, msg: str):
    logger.info(f'Sending message to session {self.sessionName}')
    logger.debug(f'Message content: {msg[:50]}...' if len(msg) > 50 else f'Message content: {msg}')
    self.messenger.Put(msg)
    self.messenger.Unlock()
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

def __init__(self):
    self.lock = threading.Lock()
    self.continueEvent = threading.Event()
    self.continueEvent.set()
    self.msg = None
    self.msgPrevious = None
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

def __init__(self, obj, atomicAccess=True):
    self.obj = obj
    self.generators = {}
    self.lock = threading.Lock() if atomicAccess else nullcontext()

class AImage(BaseModel):
    data: Optional[bytes]
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    def __init__(self, **params):
        super().__init__(**params)
        if self.data and (not all([self.format, self.width, self.height])):
            meta = self.GetMeta()
            self.format = meta['format']
            self.width = meta['width']
            self.height = meta['height']
        return

    def GetMeta(self):
        if self.data:
            image = Image.open(io.BytesIO(self.data))
            return {'width': image.width, 'height': image.height, 'format': image.format}
        else:
            return {'width': 0, 'height': 0, 'format': None}

    def __str__(self) -> str:
        return f'< AImage object in {self.format} format. >'

    @classmethod
    def FromJson(cls, data):
        return cls(data=base64.b64decode(data['data'].encode('utf-8')))

    def ToJson(self):
        return {'type': 'AImage', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

    def Convert(self, format: str):
        if format == self.format or not self.data:
            return self
        imageBytes = io.BytesIO()
        image = Image.open(io.BytesIO(self.data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(imageBytes, format=format)
        return AImage(data=imageBytes.getvalue())

    def Standardize(self):
        return self.Convert(format='JPEG')

def GetMeta(self):
    if self.data:
        image = Image.open(io.BytesIO(self.data))
        return {'width': image.width, 'height': image.height, 'format': image.format}
    else:
        return {'width': 0, 'height': 0, 'format': None}

def ToJson(obj):
    return obj.ToJson() if hasattr(obj, 'ToJson') else {'type': type(obj).__name__, 'data': obj}

class ALogger:

    def __init__(self, speech):
        self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
        self.depth = -1
        self.speech = speech
        self.queue = queue.Queue()
        return

    def ParseChannel(self, channel: str) -> tuple[str]:
        if channel in ['<', '>']:
            return (channel, '')
        l = channel.find('_')
        channelType, agentName = (channel[:l], channel[l + 1:])
        return (channelType, agentName)

    def SinkPrint(self, channel: str, txt: str=None, action: str=''):
        channelType, agentName = self.ParseChannel(channel)
        if 'open' == action:
            print(colored(channel + ': ', self.colorMap[channelType]), txt, end='', flush=True)
        elif 'append' == action:
            print(txt, end='', flush=True)
        elif 'close' == action:
            print(txt, end='', flush=True)
            print('')
        else:
            print(colored(channel + ': ', self.colorMap[channelType]), txt)
        return

    def SinkSpeech(self, channel: str, txt: str=None, action: str=''):
        if self.speech:
            self.speech.Speak(txt)
        return

    def SinkQueue(self, channel: str, txt: str=None, action: str=''):
        self.queue.put((channel, txt, action))
        return

    def Receiver(self, channel: str, txt: str=None, action: str=''):
        braketMap = {'<': 1, '>': -1}
        self.depth += braketMap[channel] if channel in braketMap else 0
        channelType, _ = self.ParseChannel(channel)
        if channelType in ['ASSISTANT', 'SYSTEM']:
            self.SinkPrint(channel=channel, txt=txt, action=action)
        if config.speechOn and (channelType in ['ASSISTANT'] and 0 == self.depth):
            self.SinkSpeech(channel=channel, txt=txt, action=action)
        if channelType in ['ASSISTANT', 'SYSTEM', '<', '>'] or 0 >= self.depth:
            self.SinkQueue(channel=channel, txt=txt, action=action)
        return

def __init__(self, speech):
    self.colorMap = {'CONTEXT': 'blue', 'USER': 'green', 'ASSISTANT': 'green', 'SYSTEM': 'yellow', 'OUTPUT': 'green'}
    self.depth = -1
    self.speech = speech
    self.queue = queue.Queue()
    return

def LoadTXTFile(path: str) -> str:
    ret = ''
    with open(path, 'r') as file:
        ret += file.read()
    return ret

def generate_response(message):
    try:
        context[currentSession]['processor'].SetGas(amount=100000000.0)
        threadLLM = threading.Thread(target=context[currentSession]['processor'], args=(message,))
        threadLLM.start()
        depth = -1
        braketMap = {'<': 1, '>': -1}
        while True:
            channel, txt, action = context[currentSession]['logger'].queue.get()
            depth += braketMap.get(channel, 0)
            if -1 == depth and '>' == channel:
                threadLLM.join()
                with open(os.path.join(config.chatHistoryPath, currentSession, 'ailice_history.json'), 'w') as f:
                    json.dump(context[currentSession]['processor'].ToJson(), f, indent=2)
                return
            elif channel in ['<', '>']:
                continue
            msg = json.dumps({'message': txt, 'role': channel, 'action': action, 'msgType': 'internal' if depth > 0 else 'user-ailice'})
            yield f'data: {msg}\n\n'
    except Exception as e:
        app.logger.error(f'Error in generate_response: {e} {traceback.print_tb(e.__traceback__)}')
        yield f'data: Error occurred: {e}\n\n'

@app.route('/delete_history/<string:sessionName>', methods=['DELETE'])
def delete_history(sessionName):
    with lock:
        historyDir = os.path.join(config.chatHistoryPath, sessionName)
        if os.path.exists(historyDir):
            shutil.rmtree(historyDir)
            return ('', 204)
        else:
            return (jsonify({'error': 'History item not found'}), 404)

@app.route('/list_histories')
def list_histories():
    with lock:
        histories = []
        for d in os.listdir(config.chatHistoryPath):
            p = os.path.join(config.chatHistoryPath, d, 'ailice_history.json')
            if os.path.exists(p):
                with open(p, 'r') as f:
                    try:
                        content = json.load(f)
                    except Exception as e:
                        continue
                    if len(content.get('conversation', [])) > 0:
                        histories.append((d, content.get('conversation')[0]['msg']))
        return jsonify(sorted(histories, key=lambda x: os.path.getmtime(os.path.join(config.chatHistoryPath, x[0], 'ailice_history.json')), reverse=True))

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

class AScripter:

    def __init__(self, incontainer=False):
        self.incontainer = incontainer
        self.sessions = {}
        self.sessionsLock = threading.Lock()
        self.reader = threading.Thread(target=self.OutputReader, args=())
        self.reader.start()
        self.functions = {'SCROLLUP': '#scroll up the page: \nSCROLL-UP-TERM<!|session: str|!>'}
        return

    def ModuleInfo(self):
        return {'NAME': 'scripter', 'ACTIONS': {'PLATFORM-INFO': {'func': 'PlatformInfo', 'prompt': 'Get the platform information of the current code execution environment.', 'type': 'primary'}, 'BASH': {'func': 'RunBash', 'prompt': 'Create a bash execution environment and execute a bash script. A timeout error will occur for programs that have not been completed for a long time. Different calls to a BASH function are independent of each other. The state from previous calls, such as custom environment variables and the current directory, will not affect subsequent calls. Note that this means you might need to redefine some environment variables or re-enter certain directories in each BASH call.', 'type': 'primary'}, 'PYTHON': {'func': 'RunPython', 'prompt': 'Execute python code. Please note that you need to copy the complete code here, and you must not use references.', 'type': 'primary'}, 'CHECK-OUTPUT': {'func': 'CheckOutput', 'prompt': 'Obtain script execution output result.', 'type': 'supportive'}, 'SCROLL-UP-TERM': {'func': 'ScrollUp', 'prompt': 'Scroll up the results.', 'type': 'supportive'}, 'SAVE-TO-FILE': {'func': 'Save2File', 'prompt': 'Save text or code to file.', 'type': 'primary'}}}

    def GetSessionID(self) -> str:
        id = f'session-{str(random.randint(0, 99999999))}'
        while id in self.sessions:
            id = f'session-{str(random.randint(0, 99999999))}'
        return id

    def RunCMD(self, session: str, cmd: list[str], timeout: int=30):
        env = os.environ.copy()
        env['A_IN_CONTAINER'] = '1' if self.incontainer else '0'
        self.sessions[session]['proc'] = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        if os.name != 'nt':
            os.set_blocking(self.sessions[session]['proc'].stdout.fileno(), False)
        self.Wait(process=self.sessions[session]['proc'], timeout=timeout)
        return

    def Wait(self, process, timeout):
        t0 = time.time()
        while time.time() < t0 + timeout:
            if process.poll() is not None:
                return
            time.sleep(0.5)

    def CheckProcOutput(self, session: str) -> tuple[str, bool]:
        process = self.sessions[session]['proc']
        output = ''
        completed = False
        if process.poll() is not None:
            for i in range(2):
                remainingOutput = ''
                try:
                    remainingOutput = process.stdout.read()
                    break
                except TypeError as e:
                    time.sleep(1)
                    remainingOutput += str(e) if 1 == i else ''
                    continue
            if remainingOutput:
                output += remainingOutput
            completed = True
        else:
            while True:
                line = process.stdout.readline()
                if line:
                    output += line
                else:
                    break
        return (output, completed)

    def UpdateSession(self, session: str):
        try:
            output, completed = self.CheckProcOutput(session=session)
            self.sessions[session]['completed'] = completed
            self.sessions[session]['output'] += output
            p = '\nThe program takes longer to complete. You can use WAIT to wait for a while and then use CHECK-OUTPUT function to get new output.' if not completed else '\nExecution completed.'
        except Exception as e:
            p = f'Exception when check the output of program execution: {str(e)}\n {traceback.format_exc()}'
            print(p)
        finally:
            self.sessions[session]['pages'].LoadPage(self.sessions[session]['output'] + '\n\n---\n\n' + p, 'BOTTOM')

    def OutputReader(self):
        while True:
            with self.sessionsLock:
                for session in self.sessions:
                    if self.sessions[session]['completed']:
                        continue
                    self.UpdateSession(session)
            time.sleep(1.0)
        return

    def CheckOutput(self, session: str) -> str:
        with self.sessionsLock:
            return self.sessions[session]['pages']() + '\n\n' + f'Session name: "{session}"\n'

    def PlatformInfo(self) -> str:
        info = platform.uname()
        currentPath = os.getcwd()
        contents = os.listdir(currentPath)
        newline = '\n'
        return f'system: {info.system}, release: {info.release}, version: {info.version}, machine: {info.machine} current path: {currentPath} contents of current path: {(newline.join(contents) if len(contents) <= 32 else newline.join(contents[:32]) + '....[The tail content has been ignored. You can use BASH function to execute system commands to view the remaining content]')}'

    def RunBash(self, code: str) -> str:
        with self.sessionsLock:
            try:
                session = self.GetSessionID()
                self.sessions[session] = {'proc': None, 'pages': AScrollablePage(functions=self.functions), 'output': '', 'lock': threading.Lock()}
                self.RunCMD(session, ['bash', '-c', code])
            except Exception as e:
                self.sessions[session]['output'] += f'Exception: {str(e)}\n {traceback.format_exc()}'
            self.UpdateSession(session)
            return f'{self.sessions[session]['pages']()}\nNote that each BASH function execution is independent, so if you want to use the state from the current execution (current directory / custom environment variables, etc.) in subsequent BASH functions, you need to redefine them.\n\n\nSession name: "{session}"\n'

    def RunPython(self, code: str) -> str:
        with self.sessionsLock:
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as temp:
                temp.write(code)
                temp.flush()
                try:
                    session = self.GetSessionID()
                    self.sessions[session] = {'proc': None, 'pages': AScrollablePage(functions=self.functions), 'output': '', 'lock': threading.Lock()}
                    self.RunCMD(session, ['python3', '-u', temp.name])
                except Exception as e:
                    self.sessions[session]['output'] += f'Exception: {str(e)}\n {traceback.format_exc()}'
            self.UpdateSession(session)
            return self.sessions[session]['pages']() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollUp(self, session: str) -> str:
        with self.sessionsLock:
            return self.sessions[session]['pages'].ScrollUp() + '\n\n' + f'Session name: "{session}"\n'

    def Save2File(self, filePath: str, code: str) -> str:
        try:
            dirPath = os.path.dirname(filePath)
            if '' != dirPath:
                os.makedirs(dirPath, exist_ok=True)
            with open(filePath, 'w') as f:
                f.write(code)
            return f'The file contents has been written.'
        except Exception as e:
            return f'Exception encountered while writing to file. EXCEPTION: {str(e)}'

def __init__(self, incontainer=False):
    self.incontainer = incontainer
    self.sessions = {}
    self.sessionsLock = threading.Lock()
    self.reader = threading.Thread(target=self.OutputReader, args=())
    self.reader.start()
    self.functions = {'SCROLLUP': '#scroll up the page: \nSCROLL-UP-TERM<!|session: str|!>'}
    return

class AStorageVecDB:

    def __init__(self):
        self.dataLock = Lock()
        self.data = {'model': MODEL, 'file': FILE_NAME, 'collections': {}}
        self.dir = None
        self.buffers = {}
        self.buffersLock = Lock()
        self.stopEvent = Event()
        self.hippocampus = Thread(target=self.Hippocampus, args=())
        self.hippocampus.daemon = True
        self.hippocampus.start()
        self.query_cache = {}
        return

    def ModuleInfo(self):
        return {'NAME': 'storage', 'ACTIONS': {}}

    def CheckLength(self, content: Union[str, list[str]]):
        texts = [content] if type(content) != list else content
        return not any([len(t) > 512000 for t in texts])

    def CalcEmbeddings(self, txts: list[str]):
        global model, modelLock
        with modelLock:
            return np.array(model.embed(txts))

    def Hippocampus(self):
        while not self.stopEvent.is_set():
            with self.buffersLock:
                for collection in self.buffers:
                    if len(self.buffers[collection]['texts']) == 0:
                        continue
                    with self.buffers[collection]['lock']:
                        try:
                            embeddings = self.CalcEmbeddings(self.buffers[collection]['texts'])
                            with self.dataLock:
                                if collection not in self.data['collections']:
                                    self.data['collections'][collection] = dict()
                                for txt, emb in zip(self.buffers[collection]['texts'], embeddings):
                                    if txt not in self.data['collections'][collection]:
                                        self.data['collections'][collection][txt] = emb
                            self.Dump(self.dir)
                        except Exception as e:
                            print(f'Hippocampus Exception: {str(e)}')
                            continue
                        finally:
                            self.buffers[collection]['texts'] = []
            time.sleep(0.1)

    def Dump(self, dir):
        if dir is not None:
            with self.dataLock:
                with open(dir + '/vecdb', 'wb') as f:
                    pickle.dump(self.data, f)
        return

    def Load(self, dir):
        if os.path.exists(dir + '/vecdb'):
            try:
                with open(dir + '/vecdb', 'rb') as f:
                    loadedData = pickle.load(f)
                    with self.dataLock:
                        self.data = loadedData
            except Exception as e:
                print(f'Error loading data: {str(e)}')
        return

    def PrepareModel(self) -> str:
        global model, modelPath, modelLock
        ggufFile = hf_hub_download(repo_id=self.data['model'], filename=self.data['file'])
        with modelLock:
            if model and ggufFile == modelPath:
                return f'Embedding model {self.data['model']} has already been loaded.'
            if 'llama_cpp' == INFERENCE_ENGINE:
                model = Llama(model_path=ggufFile, embedding=True, n_gpu_layers=-1)
                modelPath = ggufFile
                return 'Embedding model has been loaded.'
            elif 'gpt4all' == INFERENCE_ENGINE:
                gpus = []
                try:
                    gpus = GPT4All.list_gpus()
                    device = gpus[0] if len(gpus) > 0 else 'cpu'
                except Exception as e:
                    device = 'cpu'
                model = Embed4All(ggufFile, device=device)
                modelPath = ggufFile
                return f'GPUs found on this device: {gpus}. Embedding model has been loaded on {device}.'
            else:
                return 'No inference engine was found. Please use one of the following commands to install: `pip install gpt4all` or `ailice_turbo`.'

    def Open(self, directory: str) -> str:
        try:
            if '' == directory.strip():
                self.dir = None
                r = self.PrepareModel()
                return f'{r}\nvector database has been switched to a non-persistent version. model: {self.data['model']}, gguf: {self.data['file']}'
            else:
                self.dir = directory
                self.Load(directory)
                r = self.PrepareModel()
                return f'{r}\nvector database under {directory} is opened. model: {self.data['model']}, gguf: {self.data['file']}'
        except Exception as e:
            print(f'Open() EXCEPTION. e: {str(e)}')
            raise e

    def Reset(self) -> str:
        with self.dataLock:
            self.data['collections'].clear()
            if self.dir is not None:
                self.Dump(self.dir)
        return 'vector database reseted.'

    def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
        try:
            print('collection: ', collection, '. store: ', content)
            if not self.CheckLength(content):
                print('input text is too long. (>512k)')
                return False
            with self.buffersLock:
                if collection not in self.buffers:
                    self.buffers[collection] = {'texts': [], 'lock': Lock()}
            texts = [content] if type(content) != list else content
            with self.buffers[collection]['lock']:
                self.buffers[collection]['texts'] += texts
        except Exception as e:
            print('store() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return False
        return True

    def Query(self, collection: str, clue: str='', keywords: list[str]=[], num_results: int=1) -> list[tuple[str, float]]:
        try:
            if not self.CheckLength(clue):
                print('input text is too long. (>512k)')
                return False
            with self.dataLock:
                if collection not in self.data['collections']:
                    return []
            timeoutOccurred = False
            startTime = time.time()
            while collection in self.buffers and len(self.buffers[collection]['texts']) > 0:
                if time.time() - startTime > self.queryTimeout:
                    print(f'Warning: Query timed out waiting for buffer to clear for collection {collection}')
                    timeoutOccurred = True
                    break
                time.sleep(0.1)
            with self.dataLock:
                if collection not in self.data['collections']:
                    return []
                results = [txt for txt, _ in self.data['collections'][collection].items()]
                for keyword in keywords:
                    results = [txt for txt in results if keyword in txt]
                if clue in ['', None]:
                    results = [(r, -1.0) for r in results]
                    return_results = results[:num_results] if num_results > 0 else results
                    if timeoutOccurred and return_results:
                        return_results.append(('__TIMEOUT_INCOMPLETE_RESULTS__', 0.0))
                    return return_results
                if clue in self.query_cache:
                    query = self.query_cache[clue]
                else:
                    query = self.CalcEmbeddings([clue])[0]
                    self.query_cache[clue] = query
                temp = [(txt, np.sum((self.data['collections'][collection][txt] - query) ** 2, axis=0)[()]) for txt in results]
                ret = sorted(temp, key=lambda x: x[1])[:num_results] if num_results > 0 else temp
                if timeoutOccurred and ret:
                    ret.append(('__TIMEOUT_INCOMPLETE_RESULTS__', 0.0))
            print('query: ', collection, '.', clue, ' -> ', ret)
            return ret
        except Exception as e:
            print('query() EXCEPTION: ', e, traceback.print_tb(e.__traceback__))
            return []

    def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
        return self.Query(collection=collection, clue=query, num_results=num_results)

    def Release(self):
        self.stopEvent.set()
        self.hippocampus.join(timeout=2)
        if self.dir is not None:
            self.Dump(self.dir)
        print('Vector database service released.')

def __init__(self):
    self.dataLock = Lock()
    self.data = {'model': MODEL, 'file': FILE_NAME, 'collections': {}}
    self.dir = None
    self.buffers = {}
    self.buffersLock = Lock()
    self.stopEvent = Event()
    self.hippocampus = Thread(target=self.Hippocampus, args=())
    self.hippocampus.daemon = True
    self.hippocampus.start()
    self.query_cache = {}
    return

def Dump(self, dir):
    if dir is not None:
        with self.dataLock:
            with open(dir + '/vecdb', 'wb') as f:
                pickle.dump(self.data, f)
    return

def Load(self, dir):
    if os.path.exists(dir + '/vecdb'):
        try:
            with open(dir + '/vecdb', 'rb') as f:
                loadedData = pickle.load(f)
                with self.dataLock:
                    self.data = loadedData
        except Exception as e:
            print(f'Error loading data: {str(e)}')
    return

class AArxiv:

    def __init__(self):
        self.sessions = {}
        self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-ARXIV<!|session: str|!>'}
        self.lock = threading.Lock()
        return

    def ModuleInfo(self):
        return {'NAME': 'arxiv', 'ACTIONS': {'ARXIV': {'func': 'ArxivSearch', 'prompt': 'Search arXiv for academic papers.\nParameters:\n- query (str): The search query. Construct queries with:\n    - Logical combinations: AND/OR/ANDNOT operators\n    - Field restrictions: Limit searches to specific fields using these options:\n        - \'ti\': Title\n        - \'au\': Author\n        - \'abs\': Abstract\n        - \'co\': Comment\n        - \'jr\': Journal Reference\n        - \'cat\': Subject Category\n        - \'rn\': Report Number\n        - \'id\': Id\n        - \'all\': All of the above\n\n- options (str): A JSON string with search parameters. Pass \'{}\' to use all default values.\n  - sort_by (optional, str): Sort criterion. Default: \'relevance\'. Options: \'relevance\', \'lastUpdatedDate\', \'submittedDate\'.\n  - sort_order (optional, str): Sort order. Default: \'descending\'. Options: \'ascending\', \'descending\'.\n  - max_results (optional, int): Number of results to return. Default: 10.\n  \nExamples:\nARXIV<!|query="transformer architecture", options=\'{"max_results": 5, "sort_by": "submittedDate"}\'|!>\nARXIV<!|query=\'cat:hep-ph ANDNOT ti:"quantum gravity"\', options=\'{"sort_by": "submittedDate", "sort_order": "descending", "max_results": 5}\'|!>', 'type': 'primary'}, 'SCROLL-DOWN-ARXIV': {'func': 'ScrollDown', 'prompt': 'Scroll down the results.', 'type': 'supportive'}}}

    def GetSessionID(self) -> str:
        with self.lock:
            id = f'session-{str(random.randint(0, 99999999))}'
            while id in self.sessions:
                id = f'session-{str(random.randint(0, 99999999))}'
            return id

    def ParseEntry(self, entry: arxiv.Result) -> dict:
        return {'arxiv_id': entry.entry_id.split('/')[-1], 'title': entry.title, 'authors': [author.name for author in entry.authors], 'summary': entry.summary.replace('\n', ' '), 'published_date': entry.published.isoformat(), 'pdf_url': entry.pdf_url}

    def FormatResults(self, results: list) -> str:
        if not results:
            return 'No search results were found. Please check if you used overly complex keywords or unsupported search syntax. Note that relaxing your search terms is an effective strategy when no valid search results are returned.'
        return '\n\n---\n\n'.join((f'Result {i + 1}:\n  ID: {r['arxiv_id']}\n  Title: {r['title']}\n  Authors: {', '.join(r['authors'])}\n  Summary: {r['summary']}\n  Published: {r['published_date']}\n  PDF URL: {r['pdf_url']}' for i, r in enumerate(results)))

    def ArxivSearch(self, query: str, options: str) -> str:
        try:
            try:
                opts = json.loads(options) if options else {}
            except json.JSONDecodeError:
                return 'Error: Invalid JSON format in options parameter.'
            sort_by = opts.get('sort_by', 'relevance')
            sort_order = opts.get('sort_order', 'descending')
            max_results = opts.get('max_results', 10)
            sort_criterion = {'relevance': arxiv.SortCriterion.Relevance, 'lastUpdatedDate': arxiv.SortCriterion.LastUpdatedDate, 'submittedDate': arxiv.SortCriterion.SubmittedDate}[sort_by]
            sort_order_enum = {'ascending': arxiv.SortOrder.Ascending, 'descending': arxiv.SortOrder.Descending}[sort_order]
            search = arxiv.Search(query=query, max_results=max_results, sort_by=sort_criterion, sort_order=sort_order_enum)
            ret = self.FormatResults([self.ParseEntry(r) for r in list(search.results())[:max_results]])
        except Exception as e:
            ret = f'arxiv exception: {str(e)}'
        session = self.GetSessionID()
        content = AScrollablePage(functions=self.functions)
        content.LoadPage(str(ret), 'TOP')
        with self.lock:
            self.sessions[session] = content
        return content() + '\n\n' + f'Session name: "{session}"\n'

    def ScrollDown(self, session: str) -> str:
        with self.lock:
            if session not in self.sessions:
                return 'Invalid session ID.'
            return self.sessions[session].ScrollDown() + '\n\n' + f'Session name: "{session}"\n'

def __init__(self):
    self.sessions = {}
    self.functions = {'SCROLLDOWN': '#scroll down the page: \nSCROLL-DOWN-ARXIV<!|session: str|!>'}
    self.lock = threading.Lock()
    return

class ASpeech:

    def __init__(self):
        self.textQue = queue.Queue(maxsize=100)
        self.audioQue = queue.Queue(maxsize=100)
        self.inputDone = True
        self.lock = threading.Lock()
        self.noTextLeft = True
        self.textProcessor = threading.Thread(target=self.ProcessText, daemon=True)
        self.textProcessor.start()
        self.audioProcessor = threading.Thread(target=self.ProcessAudio, daemon=True)
        self.audioProcessor.start()
        return

    def ModuleInfo(self):
        return {'NAME': 'speech', 'ACTIONS': {'SPEECH-TO-TEXT': {'func': 'Speech2Text', 'prompt': 'Speech to text.', 'type': 'primary'}, 'TEXT-TO-SPEECH': {'func': 'Text2Speech', 'prompt': 'Text to speech.', 'type': 'primary'}, 'GET-AUDIO': {'func': 'GetAudio', 'prompt': 'Get text input from microphone.', 'type': 'primary'}, 'SPEAK': {'func': 'Speak', 'prompt': 'Synthesize input text fragments into audio and play.', 'type': 'primary'}, 'SWITCH-TONE': {'func': 'SwitchTone', 'prompt': 'Switch the TTS system to a new tone.', 'type': 'primary'}}}

    def PrepareModel(self):
        global s2t, t2s
        if None in [t2s, s2t]:
            t2s = T2S_ChatTTS()
            s2t = S2T_WhisperLarge()
        return

    def SetDevices(self, deviceMap: dict[str, str]):
        global s2t, t2s
        if 'stt' in deviceMap:
            s2t.To(deviceMap['stt'])
        elif 'tts' in deviceMap:
            t2s.To(deviceMap['tts'])
        return

    def Speech2Text(self, wav: list, sr: int) -> str:
        global s2t
        return s2t.recognize(audio_data_to_numpy((np.array(wav), sr)))

    def Text2Speech(self, txt: str) -> tuple[list, int]:
        global t2s
        if None == txt or '' == strip(txt):
            return ([1], 24000)
        audio, sr = t2s(txt)
        return (audio.tolist(), sr)

    def GetAudio(self) -> str:
        global s2t
        self.inputDone = True
        with self.lock:
            ret = s2t()
        return ret

    def Speak(self, txt: str):
        print('Speak(): ', txt)
        if None == txt or '' == strip(txt):
            return
        self.textQue.put(txt)
        self.inputDone = False
        return

    def SwitchTone(self) -> str:
        global t2s
        return t2s.SwitchTone()

    def ProcessText(self):
        global t2s
        while True:
            self.noTextLeft = self.inputDone and self.textQue.empty()
            text = self.textQue.get()
            try:
                self.audioQue.put(t2s(text))
            except Exception as e:
                print('EXCEPTION in ProcessText(). continue. e: ', str(e))
                continue

    def ProcessAudio(self):
        while True:
            time.sleep(0.1)
            with self.lock:
                while not (self.inputDone and self.noTextLeft and self.audioQue.empty()):
                    audio, sr = self.audioQue.get()
                    sd.play(audio, sr)
                    sd.wait()

def __init__(self):
    self.textQue = queue.Queue(maxsize=100)
    self.audioQue = queue.Queue(maxsize=100)
    self.inputDone = True
    self.lock = threading.Lock()
    self.noTextLeft = True
    self.textProcessor = threading.Thread(target=self.ProcessText, daemon=True)
    self.textProcessor.start()
    self.audioProcessor = threading.Thread(target=self.ProcessAudio, daemon=True)
    self.audioProcessor.start()
    return

def SwitchTone(self) -> str:
    global t2s
    return t2s.SwitchTone()

class T2S_ChatTTS:

    def __init__(self):
        self.device = 'cpu'
        self.toneFile = os.path.join(appdirs.user_data_dir('ailice', 'Steven Lu'), 'speaker_tone')
        self.model = ChatTTS.Chat()
        succ = False
        for i in range(5):
            succ = self.model.load(compile=True, device=self.device)
            if succ:
                break
        if not succ:
            raise Exception('T2S_ChatTTS.__init__(): Load model FAILED, please retry.')
        if os.path.exists(self.toneFile):
            with open(self.toneFile, 'r') as f:
                self.rand_spk = f.read()
        else:
            self.SwitchTone()
        return

    def SwitchTone(self) -> str:
        self.rand_spk = self.model.sample_random_speaker()
        with open(self.toneFile, 'w') as f:
            f.write(self.rand_spk)
        return 'The new speaker tone has been created.'

    def To(self, device: str):
        if device == self.device:
            return
        self.model = ChatTTS.Chat()
        self.model.load(compile=True, device=device)
        self.device = device
        return

    def __call__(self, txt: str):
        params_infer_code = ChatTTS.Chat.InferCodeParams(spk_emb=self.rand_spk, temperature=0.3, top_P=0.7, top_K=20)
        params_refine_text = ChatTTS.Chat.RefineTextParams(prompt='[oral_2][laugh_0][break_6]')
        wavs = self.model.infer([txt], params_refine_text=params_refine_text, params_infer_code=params_infer_code)
        return (wavs[0], 24000)

def __init__(self):
    self.device = 'cpu'
    self.toneFile = os.path.join(appdirs.user_data_dir('ailice', 'Steven Lu'), 'speaker_tone')
    self.model = ChatTTS.Chat()
    succ = False
    for i in range(5):
        succ = self.model.load(compile=True, device=self.device)
        if succ:
            break
    if not succ:
        raise Exception('T2S_ChatTTS.__init__(): Load model FAILED, please retry.')
    if os.path.exists(self.toneFile):
        with open(self.toneFile, 'r') as f:
            self.rand_spk = f.read()
    else:
        self.SwitchTone()
    return

def To(self, device: str):
    if device == self.device:
        return
    self.model = ChatTTS.Chat()
    self.model.load(compile=True, device=device)
    self.device = device
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

def __init__(self, sr=16000):
    self.model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, onnx=False)
    self.sr = sr
    self.buffer = deque(maxlen=self.sr * 60)
    return

def build_prompt(question: str, files: Optional[Dict[str, str]]=None) -> str:
    """
    Build the complete prompt with system prompt and file information.
    
    Args:
        question: The question content
        files: Optional dict of {file_name: file_path}
    Returns:
        Complete prompt
    """
    system_prompt = 'System prompt: You are a general AI assistant. I will ask you a question. Report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]'
    prompt = f'{system_prompt}\n\n{question}'
    if files:
        prompt += '\n\nRelevant files for this task:'
        for fname, fpath in files.items():
            if not os.path.exists(fpath):
                logging.warning(f'File not found: {fpath}')
                continue
            prompt += f'\n- {fname}: {fpath}'
    return prompt

def evaluate_answer(model_answer: Union[str, float, List], ground_truth: Union[str, float, List]) -> float:
    """
    Evaluate a single answer against the ground truth.
    
    Args:
        model_answer: The normalized model answer
        ground_truth: The normalized ground truth
    Returns:
        1.0 for match, 0.0 otherwise
    """
    try:
        if isinstance(ground_truth, list) and isinstance(model_answer, list):
            return float(sorted(model_answer) == sorted(ground_truth))
        elif isinstance(ground_truth, (int, float)) and isinstance(model_answer, (int, float)):
            return float(abs(float(model_answer) - float(ground_truth)) < 1e-06)
        else:
            return float(str(model_answer).strip() == str(ground_truth).strip())
    except Exception as e:
        logging.error(f'Error in answer evaluation: {e}')
        return 0.0

def main():
    """
    Main function to run the GAIA evaluation
    """
    logging.info('Starting GAIA evaluation...')
    try:
        ds = load_dataset('gaia-benchmark/GAIA', '2023_all')
        logging.info(f'Loaded dataset with {len(ds['validation'])} validation entries')
    except Exception as e:
        logging.error(f'Failed to load dataset: {e}')
        return
    results = evaluate_agent(ds['validation'], chat_with_ailice)
    output_file = 'evaluation_results.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f'Results saved to {output_file}')
    except Exception as e:
        logging.error(f'Failed to save results: {e}')
    print('\nEvaluation Summary:')
    print(f'Overall Score: {results['overall_score']:.2%}')
    print(f'Level 1 Score: {results['level_1_score']:.2%}')
    print(f'Level 2 Score: {results['level_2_score']:.2%}')
    print(f'Level 3 Score: {results['level_3_score']:.2%}')

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

def ToJson(self):
    return {'name': self.name, 'modelID': self.modelID, 'agentType': self.prompt.PROMPT_NAME, 'prompt': self.prompt.ToJson() if hasattr(self.prompt, 'ToJson') else {}, 'interpreter': self.interpreter.ToJson(), 'conversation': self.conversation.ToJson(), 'collection': self.collection, 'modules': {k: {'addr': m['addr']} for k, m in self.modules.items()}, 'subProcessors': {k: p.ToJson() for k, p in self.subProcessors.items()}}

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

def ToJson(self) -> str:
    return [{'role': record['role'], 'time': record['time'], 'entry': record['entry'], 'msg': record['msg'], 'attachments': [{'type': a['type'], 'tag': a['tag'], 'content': ToJson(a['content'])} for a in record['attachments']]} for record in self.conversations]

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

def ToJson(self):
    return {'env': {k: ToJson(v) for k, v in self.env.items()}}

class AFormatterClaudeVision:

    def __init__(self, tokenizer=None, systemAsUser=False):
        self.systemAsUser = systemAsUser
        return

    def ProcessAttachements(self, a):
        if 'image' == a['type']:
            return [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': a['content'].ToJson()['data']}}]

    def BuildMsg(self, role: str, msg: str, attachments: list):
        roleMap = {'SYSTEM': 'system' if not self.systemAsUser else 'user', 'USER': 'user', 'ASSISTANT': 'assistant'}
        return {'role': roleMap[role], 'content': [{'type': 'text', 'text': msg}] + sum([self.ProcessAttachements(a) for a in attachments if a['type'] in ['image']], [])}

    def __call__(self, prompt0, conversations, encode=True, assistTag=True):
        ret = [{'role': 'system', 'content': [{'type': 'text', 'text': prompt0}]}] + [self.BuildMsg(c['role'], c['msg'], c['attachments']) for c in conversations]
        return (ret, TokenEstimatorOAI(conversations))

def ProcessAttachements(self, a):
    if 'image' == a['type']:
        return [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': a['content'].ToJson()['data']}}]

