# Cluster 2

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

def __init__(self):
    self.pool = dict()
    return

class APromptsManager:

    def __init__(self):
        self.prompts = dict()
        self.storage = None
        self.collection = None
        return

    def Init(self, storage, collection):
        self.storage = storage
        self.collection = collection
        return

    def RegisterPrompts(self, promptClasses) -> str:
        for promptClass in promptClasses:
            if promptClass.PROMPT_NAME in self.prompts:
                return f'{promptClass.PROMPT_NAME} is already exist, please use another name.'
        try:
            self.storage.Store(self.collection + '_prompts', [json.dumps({'name': promptClass.PROMPT_NAME, 'desc': promptClass.PROMPT_DESCRIPTION, 'properties': promptClass.PROMPT_PROPERTIES}) for promptClass in promptClasses])
            for promptClass in promptClasses:
                self.prompts[promptClass.PROMPT_NAME] = promptClass
            if 'doc-reader' in self.prompts:
                self.prompts['article-digest'] = self.prompts['doc-reader']
            return ''
        except Exception as e:
            return f'STORE prompt to vecdb FAILED, there may be a problem with the vector database. Exception: {str(e)}'

    def __getitem__(self, promptName: str):
        return self.prompts[promptName]

    def __iter__(self):
        return iter(self.prompts)

def __init__(self):
    self.prompts = dict()
    self.storage = None
    self.collection = None
    return

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    parser.add_argument('--clusterURL', type=str, help='The weaviate cluster url.')
    parser.add_argument('--apiKey', type=str, help='The api key for this cluster.')
    parser.add_argument('--oaiKey', type=str, help='The OpenAI api key.')
    args = parser.parse_args()
    makeServer(AStorageWeaviate, {'clusterURL': args.clusterURL, 'apiKey': args.apiKey, 'oaiKey': args.oaiKey}, args.addr, ['ModuleInfo', 'Open', 'Reset', 'Store', 'Query', 'Recall']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(ADuckDuckGo, dict(), args.addr, ['ModuleInfo', 'DuckDuckGo', 'ScrollDown']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(AStorageVecDB, dict(), args.addr, ['ModuleInfo', 'Open', 'Reset', 'Store', 'Query', 'Recall']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(AComputer, dict(), args.addr, ['ModuleInfo', 'ScreenShot', 'LocateAndClick', 'LocateAndScroll', 'TypeWrite', 'ReadImage', 'WriteImage', 'WriteFile', 'Proxy'], atomicCall=False).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    parser.add_argument('--incontainer', action='store_true', help='Run in container. Please DO NOT turn on this switch on non-virtual machines, otherwise it will cause serious security risks.')
    args = parser.parse_args()
    makeServer(AScripter, {'incontainer': args.incontainer}, args.addr, ['ModuleInfo', 'PlatformInfo', 'CheckOutput', 'RunBash', 'RunPython', 'ScrollUp', 'Save2File']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(AStorageVecDB, dict(), args.addr, ['ModuleInfo', 'Open', 'Reset', 'Store', 'Query', 'Recall', 'Release']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(AArxiv, dict(), args.addr, ['ModuleInfo', 'ArxivSearch', 'ScrollDown'], atomicCall=False).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(ASpeech, dict(), args.addr, ['ModuleInfo', 'PrepareModel', 'Speech2Text', 'Text2Speech', 'GetAudio', 'Speak', 'SwitchTone', 'SetDevices']).Run()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    args = parser.parse_args()
    makeServer(AGoogle, dict(), args.addr, ['ModuleInfo', 'Google', 'ScrollDown']).Run()

class AWebBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(AWebBrowser, self).__init__(functions=functions)
        self.inited = False
        self.exit_stack = AsyncExitStack()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.urls = {}
        self.prompt = '\nThe text with links are enclosed in square brackets to highlight it. If you need to open the page linked to a certain text, please call GET-LINK<!|text: str, session: str|!> function to get the url, and then call BROWSE<!|url: str, session: str|!>. Please note that the text parameter of GET-LINK must exactly match the content in the square brackets (excluding the square brackets themselves).\nThe forms on the webpage have been listed in text format, and you can use the EXECUTE-JS<!|js_code: str, session: str|!> function to operate the form, such as entering text, clicking buttons, etc. Use triple quotes on your code. Example: \n!EXECUTE-JS<!|"""\ndocument.querySelector(\'form.mini-search input[name="query"]\').value = "hello world";\ndocument.querySelector(\'form.mini-search\').submit();\n""", "arxiv_session"|!>\n'
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.RunEventLoop, daemon=True)
        self.thread.start()

    def RunEventLoop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def RunCoroutine(self, coro, timeout=60):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            if not future.done():
                future.cancel()
            raise e

    async def AsyncInit(self):
        if self.inited:
            return (True, '')
        try:
            self.playwright = await self.exit_stack.enter_async_context(async_playwright())
            browser_args = []
            if os.path.exists('/.dockerenv'):
                browser_args.append('--no-sandbox')
            browser_instance = await self.playwright.chromium.launch(headless=True, args=browser_args)
            self.browser = await self.exit_stack.enter_async_context(browser_instance)
            context_instance = await self.browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36', viewport={'width': 1280, 'height': 800})
            self.context = await self.exit_stack.enter_async_context(context_instance)
            await self.context.route('**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf,eot}', lambda route: route.abort())
            self.page = await self.context.new_page()
            self.inited = True
            return (True, '')
        except Exception as e:
            await self.exit_stack.aclose()
            return (False, f'Browser initialization failed: {str(e)}\n{traceback.format_exc()}')

    def Init(self):
        return self.RunCoroutine(self.AsyncInit())

    async def AsyncBrowse(self, url):
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return 'Invalid URL. Please provide a complete URL starting with http:// or https://'
        except Exception:
            return 'Invalid URL format. Please check the URL and try again.'
        succ, msg = await self.AsyncInit()
        if not succ:
            raise Exception(msg)
        await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await self.page.wait_for_timeout(2000)
        content = await self.AsyncHtmlToMarkdown()
        self.LoadPage(content, 'TOP')
        return self() + self.prompt

    def Browse(self, url):
        return self.RunCoroutine(self.AsyncBrowse(url))

    def GetFullText(self):
        return self.txt if self.txt is not None else ''

    def GetLink(self, text):
        if text in self.urls:
            return self.urls[text]
        else:
            import difflib
            prompt = 'Please note that the text you use to query the URL should be the part enclosed in square brackets (excluding the square brackets themselves), otherwise the search will not yield results.'
            similars = '\n'.join(['[' + key + '](' + self.urls[key] + ')' for key in difflib.get_close_matches(text, self.urls, n=3)])
            if similars == '':
                return 'No url found on specified text. \n' + prompt
            else:
                return f'No exact match found, the most similar URLs are as follows:\n {similars} \n{prompt}'

    def ScrollDown(self):
        return super(AWebBrowser, self).ScrollDown() + self.prompt

    def ScrollUp(self):
        return super(AWebBrowser, self).ScrollUp() + self.prompt

    def SearchDown(self, query):
        return super(AWebBrowser, self).SearchDown(query) + self.prompt

    def SearchUp(self, query):
        return super(AWebBrowser, self).SearchUp(query) + self.prompt

    async def AsyncExecuteJS(self, js_code):
        succ, msg = await self.AsyncInit()
        if not succ:
            return msg
        try:
            if not self.page or self.page.is_closed():
                return 'No active page. Please browse to a URL first.'
            result = await self.page.evaluate(js_code)
            await self.page.wait_for_timeout(2000)
            content = await self.AsyncHtmlToMarkdown()
            result_str = 'JavaScript executed successfully.' if result is None else str(result)
            self.LoadPage(f'JS execution returned: {result_str}\n\n---\n\nThe current page content is as follows:\n\n{content}', 'TOP')
            return self() + self.prompt
        except Exception as e:
            return f'Error executing JavaScript: {str(e)}\n{traceback.format_exc()}'

    def ExecuteJS(self, js_code):
        return self.RunCoroutine(self.AsyncExecuteJS(js_code))

    def EnsureUnique(self, text):
        if not text or text.isspace():
            text = 'Link'
        text = re.sub('\\s+', ' ', text).strip()
        if not text:
            text = 'Link'
        ret = text
        while ret in self.urls:
            ret = text + ' |' + str(random.randint(0, 10000000))
        return ret

    async def AsyncHtmlToMarkdown(self):
        """Convert HTML to Markdown using JavaScript for DOM processing and Python for frame handling"""
        self.urls = {}
        result = await self.AsyncProcessPageAndFrames(self.page)
        return result

    async def AsyncProcessPageAndFrames(self, page_or_frame):
        """Process a page or frame and all its child frames recursively"""
        result = await page_or_frame.evaluate('() => {\n            // Helper function to clean text\n            function cleanText(text) {\n                return text ? text.replace(/\\s+/g, \' \').trim() : \'\';\n            }\n            \n            // Helper function to ensure element is visible\n            function isVisible(element) {\n                if (!element) return false;\n                \n                // Check computed style\n                const style = window.getComputedStyle(element);\n                if (style.display === \'none\' || style.visibility === \'hidden\' || style.opacity === \'0\') {\n                    return false;\n                }\n                \n                // Check dimensions\n                const rect = element.getBoundingClientRect();\n                if (rect.width === 0 || rect.height === 0) {\n                    return false;\n                }\n                \n                return true;\n            }\n            \n            // Process a form element\n            function processForm(form) {\n                let formInfo = [\'\\n\\n```\', \'Form:\'];\n                \n                // Extract form attributes\n                [\'action\', \'method\', \'name\', \'id\', \'class\'].forEach(attr => {\n                    if (form[attr]) {\n                        formInfo.push(`- ${attr.charAt(0).toUpperCase() + attr.slice(1)}: ${form[attr]}`);\n                    }\n                });\n                \n                // Build selector\n                let selector = \'form\';\n                if (form.id) selector = `form#${form.id}`;\n                else if (form.name) selector = `form[name=\'${form.name}\']`;\n                else if (form.className) {\n                    const className = form.className.split(\' \')[0];\n                    if (className) selector = `form.${className}`;\n                }\n                \n                formInfo.push(`- Selector: ${selector}`);\n                formInfo.push(\'\\nFields:\');\n                \n                // Process form fields\n                const fields = form.querySelectorAll(\'input, select, textarea, button\');\n                let fieldCount = 0;\n                \n                fields.forEach(field => {\n                    if (!isVisible(field)) return;\n                    \n                    fieldCount++;\n                    formInfo.push(`${fieldCount}. ${field.nodeName.charAt(0).toUpperCase() + field.nodeName.slice(1).toLowerCase()}:`);\n                    \n                    [\'type\', \'name\', \'id\', \'placeholder\', \'required\'].forEach(attr => {\n                        if (field[attr]) {\n                            formInfo.push(`   - ${attr.charAt(0).toUpperCase() + attr.slice(1)}: ${field[attr]}`);\n                        }\n                    });\n                    \n                    // Build field selector\n                    let fieldSelector = \'\';\n                    if (field.id) fieldSelector = `#${field.id}`;\n                    else if (field.name) fieldSelector = `${field.nodeName.toLowerCase()}[name=\'${field.name}\']`;\n                    else fieldSelector = `${selector} ${field.nodeName.toLowerCase()}`;\n                    if (field.type && !field.id && !field.name) fieldSelector += `[type=\'${field.type}\']`;\n                    \n                    formInfo.push(`   - Selector: ${fieldSelector}`);\n                    \n                    if (field.value) {\n                        formInfo.push(`   - Value: "${field.value}"`);\n                    }\n                    \n                    if (field.nodeName.toLowerCase() === \'select\') {\n                        formInfo.push(\'   - Options:\');\n                        for (const option of field.options) {\n                            formInfo.push(`     * Value: "${option.value}", Text: "${option.text}", Selected: ${option.selected}`);\n                        }\n                    }\n                    \n                    if (field.nodeName.toLowerCase() === \'button\') {\n                        formInfo.push(`   - Text: "${cleanText(field.textContent)}"`);\n                    }\n                });\n                \n                formInfo.push(\'```\\n\\n\');\n                return formInfo.join(\'\\n\');\n            }\n            \n            // Generate a unique ID\n            function generateUniqueId(prefix) {\n                return prefix + \'_\' + Date.now() + \'_\' + Math.random().toString(36).substring(2, 15);\n            }\n            \n            // Store for URL mappings and iframe positions\n            const urlMappings = {};\n            const iframePositions = [];\n            \n            // Process a node recursively\n            function processNode(node, strip = true, depth = 0) {\n                if (!node) return \'\';\n                \n                // Skip invisible elements\n                if (node.nodeType === Node.ELEMENT_NODE && !isVisible(node)) {\n                    return \'\';\n                }\n                \n                // Skip comments\n                if (node.nodeType === Node.COMMENT_NODE) {\n                    return \'\';\n                }\n                \n                // Skip script, style, etc.\n                if (node.nodeType === Node.ELEMENT_NODE) {\n                    const tagName = node.nodeName.toLowerCase();\n                    if ([\'script\', \'style\', \'noscript\', \'svg\', \'path\', \'meta\', \'link\'].includes(tagName)) {\n                        return \'\';\n                    }\n                }\n                \n                // Text node\n                if (node.nodeType === Node.TEXT_NODE) {\n                    const text = node.textContent || \'\';\n                    return strip ? cleanText(text) : text;\n                }\n                \n                // Element node\n                const tagName = node.nodeName.toLowerCase();\n                let result = \'\';\n                \n                // Process by tag type\n                switch (tagName) {\n                    case \'form\':\n                        return processForm(node);\n                        \n                    case \'li\':\n                        let liContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent && childContent.trim()) {\n                                liContent += childContent;\n                            }\n                        }\n                        return `- ${liContent.trim()}\\n`;\n                        \n                    case \'p\':\n                        let pContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent && childContent.trim()) {\n                                pContent += childContent;\n                            }\n                        }\n                        return `\\n\\n${pContent}\\n\\n`;\n                        \n                    case \'pre\':\n                        let preContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, false, depth + 1);\n                            if (childContent) {\n                                preContent += childContent;\n                            }\n                        }\n                        return `\\n\\n\\`\\`\\`\\n${preContent}\\n\\`\\`\\`\\n\\n`;\n                        \n                    case \'code\':\n                        let codeContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, false, depth + 1);\n                            if (childContent) {\n                                codeContent += childContent;\n                            }\n                        }\n                        return `\\`${codeContent}\\``;\n                        \n                    case \'h1\': case \'h2\': case \'h3\': case \'h4\': case \'h5\': case \'h6\':\n                        const level = parseInt(tagName.charAt(1));\n                        let headingContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                headingContent += childContent;\n                            }\n                        }\n                        return `\\n\\n${\'#\'.repeat(level)} ${headingContent.trim()}\\n`;\n                        \n                    case \'a\':\n                        const href = node.getAttribute(\'href\') || \'\';\n                        let linkContent = \'\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                linkContent += childContent;\n                            }\n                        }\n                        \n                        if (!linkContent) {\n                            linkContent = strip ? cleanText(node.textContent) : node.textContent;\n                        }\n                        \n                        if (linkContent && href) {\n                            // Create a unique ID for this link\n                            const linkId = generateUniqueId(\'link\');\n                            urlMappings[linkId] = {\n                                url: href,\n                                text: linkContent\n                            };\n                            return `[${linkContent}](${linkId})`;\n                        }\n                        return linkContent;\n                        \n                    case \'img\':\n                        const src = node.getAttribute(\'src\') || \'\';\n                        const alt = strip ? cleanText(node.getAttribute(\'alt\') || \'\') : (node.getAttribute(\'alt\') || \'\');\n                        \n                        if (src) {\n                            if (src.startsWith(\'data:\')) {\n                                return alt;\n                            }\n                            // Create a unique ID for this image\n                            const imgId = generateUniqueId(\'img\');\n                            urlMappings[imgId] = {\n                                url: src,\n                                text: alt || \'Image\'\n                            };\n                            return `\\n![${alt || \'Image\'}](${imgId})\\n`;\n                        }\n                        return alt;\n                        \n                    case \'video\':\n                        const videoSrc = node.getAttribute(\'src\') || \'\';\n                        if (videoSrc) {\n                            // Create a unique ID for this video\n                            const videoId = generateUniqueId(\'video\');\n                            urlMappings[videoId] = {\n                                url: videoSrc,\n                                text: \'Video\'\n                            };\n                            return `\\n\\n[Video](${videoId})\\n\\n`;\n                        }\n                        \n                        const sourceElement = node.querySelector(\'source\');\n                        if (sourceElement) {\n                            const sourceSrc = sourceElement.getAttribute(\'src\') || \'\';\n                            if (sourceSrc) {\n                                // Create a unique ID for this video source\n                                const sourceId = generateUniqueId(\'video\');\n                                urlMappings[sourceId] = {\n                                    url: sourceSrc,\n                                    text: \'Video\'\n                                };\n                                return `\\n\\n[Video](${sourceId})\\n\\n`;\n                            }\n                        }\n                        return \'\';\n                        \n                    case \'iframe\':\n                        const iframeSrc = node.getAttribute(\'src\') || \'\';\n                        if (iframeSrc) {\n                            // Create a placeholder for this iframe\n                            const iframeId = generateUniqueId(\'iframe\');\n                            const placeholder = `__IFRAME_PLACEHOLDER_${iframeId}__`;\n                            \n                            // Store iframe information for later processing\n                            iframePositions.push({\n                                id: iframeId,\n                                src: iframeSrc,\n                                placeholder: placeholder,\n                                name: node.getAttribute(\'name\') || node.getAttribute(\'id\') || \'Unnamed Frame\'\n                            });\n                            \n                            return placeholder;\n                        }\n                        return \'\';\n                        \n                    case \'ul\': case \'ol\':\n                        let listContent = \'\\n\\n\';\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                listContent += childContent;\n                            }\n                        }\n                        return listContent + \'\\n\\n\';\n                        \n                    case \'div\': case \'span\': case \'section\': case \'article\': case \'main\': case \'header\': case \'footer\':\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                result += childContent;\n                            }\n                        }\n                        break;\n                        \n                    default:\n                        for (const child of node.childNodes) {\n                            const childContent = processNode(child, strip, depth + 1);\n                            if (childContent) {\n                                result += childContent;\n                            }\n                        }\n                }\n                \n                return result;\n            }\n            \n            // Process the document body\n            const body = document.body;\n            const markdown = processNode(body, true, 0);\n            \n            return {\n                markdown: markdown,\n                urls: urlMappings,\n                iframes: iframePositions\n            };\n        }')
        markdown = result['markdown']
        urls = result['urls']
        iframes = result['iframes']
        for id, url_info in urls.items():
            url = url_info['url']
            text = url_info['text']
            unique_text = self.EnsureUnique(text)
            self.urls[unique_text] = urljoin(self.page.url, url)
            markdown = markdown.replace(f'[{text}]({id})', f'[{unique_text}]')
            markdown = markdown.replace(f'![{text}]({id})', f'![{unique_text}]({urljoin(self.page.url, url)})')
        for iframe in iframes:
            iframe_src = iframe['src']
            placeholder = iframe['placeholder']
            if not iframe_src:
                continue
            iframe_content = ''
            iframe_url = urljoin(self.page.url, iframe_src)
            for frame in page_or_frame.frames if hasattr(page_or_frame, 'frames') else page_or_frame.child_frames:
                if frame.url == iframe_src or frame.url == iframe_url:
                    try:
                        iframe_content = await self.AsyncProcessPageAndFrames(frame)
                        break
                    except Exception as e:
                        print(f'Error processing iframe: {str(e)}')
            if not iframe_content:
                iframe_content = f'[Iframe: {iframe_src}]'
            else:
                iframe_name = iframe['name']
                iframe_content = f'\n\n--- Frame: {iframe_name} ({iframe_src}) ---\n\n{iframe_content}\n\n--- End of Frame ---\n\n'
            markdown = markdown.replace(placeholder, iframe_content)
        return markdown

    async def AsyncDestroy(self):
        try:
            await self.exit_stack.aclose()
            self.inited = False
            self.playwright = None
            self.browser = None
            self.context = None
            self.page = None
            self.urls = {}
            return (True, 'Resources destroyed successfully')
        except Exception as e:
            return (False, f'Error during cleanup: {str(e)}\n{traceback.format_exc()}')

    def Destroy(self):
        result = self.RunCoroutine(self.AsyncDestroy())

        def shutdown_loop():
            for task in asyncio.all_tasks(self.loop):
                if not task.done():
                    task.cancel()
            self.loop.call_later(1, self.loop.stop)
        self.loop.call_soon_threadsafe(shutdown_loop)
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            print('Warning: Event loop thread did not terminate within timeout')
        return result

def Init(self):
    return self.RunCoroutine(self.AsyncInit())

def Browse(self, url):
    return self.RunCoroutine(self.AsyncBrowse(url))

def ExecuteJS(self, js_code):
    return self.RunCoroutine(self.AsyncExecuteJS(js_code))

def Destroy(self):
    result = self.RunCoroutine(self.AsyncDestroy())

    def shutdown_loop():
        for task in asyncio.all_tasks(self.loop):
            if not task.done():
                task.cancel()
        self.loop.call_later(1, self.loop.stop)
    self.loop.call_soon_threadsafe(shutdown_loop)
    self.thread.join(timeout=5)
    if self.thread.is_alive():
        print('Warning: Event loop thread did not terminate within timeout')
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--addr', type=str, help='The address where the service runs on.')
    parser.add_argument('--pdfOutputDir', type=str, default='', help='You can set it as a directory to store the OCR results of PDF files to avoid repeated OCR computation.')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmpdir:
        makeServer(ABrowser, {'pdfOutputDir': args.pdfOutputDir if '' != args.pdfOutputDir.strip() else tmpdir}, args.addr, ['ModuleInfo', 'Browse', 'Edit', 'ScrollDown', 'ScrollUp', 'SearchDown', 'SearchUp', 'GetFullText', 'GetLink', 'ExecuteJS', 'Replace', 'ReplaceAll', 'SaveTo', 'Destroy']).Run()

def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Ailice MCP Wrapper', epilog='\nExamples:\n  # SSE mode example\n  ailice_mcp_wrapper --addr localhost:59200 sse --server_url http://example:8000/sse\n  \n  # Stdio mode example\n  ailice_mcp_wrapper --addr localhost:59200 stdio python3 mcp_demo_echo.py\n  \n  # Stdio mode with environment variables\n  ailice_mcp_wrapper --addr localhost:59200 stdio python3 mcp_demo_echo.py --env PYTHONPATH=/path/to/modules --env DEBUG=1\n', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--addr', type=str, required=True, help='The address where the service runs on. This address will be given to Ailice, to connect to the service.')
    subparsers = parser.add_subparsers(dest='mode', help='Operation mode')
    sse_parser = subparsers.add_parser('sse', help='SSE mode', description='Run in SSE mode, connecting to an existing MCP server', epilog='Example: ailice_mcp_wrapper --addr localhost:59200 sse --server_url http://example:8000/sse')
    sse_parser.add_argument('--server_url', type=str, required=True, help='The url of MCP server.')
    stdio_parser = subparsers.add_parser('stdio', help='Stdio mode', description='Run in stdio mode, executing a local command', epilog='Example: ailice_mcp_wrapper --addr localhost:59200 stdio python3 mcp_demo_echo.py')
    stdio_parser.add_argument('cmd', help='The command to be executed.')
    stdio_parser.add_argument('cmd_args', nargs='*', help='Command arguments.')
    stdio_parser.add_argument('--env', action='append', dest='env_vars', metavar='KEY=VALUE', help='Set up env variables, the format should be: KEY=VALUE')
    args = parser.parse_args()
    if args.mode is None:
        parser.print_help()
        sys.exit(1)
    env = os.environ.copy()
    if args.mode == 'stdio' and args.env_vars:
        for env_var in args.env_vars:
            try:
                key, value = env_var.split('=', 1)
                env[key] = value
            except ValueError:
                print(f'Warning: Incorrect environment variable format: {env_var}, should be KEY=VALUE format.')
    try:
        if args.mode == 'stdio':
            serverParams = StdioServerParameters(command=args.cmd, args=args.cmd_args, env=env)
            kls, actions = MakeWrapper(serverParams=serverParams)
            server = makeServer(kls, {'serverParams': serverParams}, args.addr, ['ModuleInfo'] + actions)
        else:
            kls, actions = MakeWrapper(serverUrl=args.server_url)
            server = makeServer(kls, {'serverUrl': args.server_url}, args.addr, ['ModuleInfo'] + actions)
        print(f'We will run the MCP server next, you can use this address {args.addr} to load the wrapped ext-module and use the corresponding tools.')
        server.Run()
    except Exception as e:
        print(f'Error in main: {e}', traceback.print_tb(e.__traceback__))
    finally:
        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)
            loop_thread.join(timeout=5)

class ALLMPool:

    def __init__(self, config):
        self.pool = dict()
        self.config = config
        return

    def ParseID(self, id):
        split = id.find(':')
        return (id[:split], id[split + 1:])

    def Init(self, llmIDs: list[str]):
        MODEL_WRAPPER_MAP = {'AModelChatGPT': AModelChatGPT, 'AModelMistral': AModelMistral, 'AModelAnthropic': AModelAnthropic}
        if 0 == len(requirements):
            MODEL_WRAPPER_MAP['AModelCausalLM'] = AModelCausalLM
            MODEL_WRAPPER_MAP['AModelLLAMA'] = AModelCausalLM
        llmIDs = list(set([id for k, id in self.config.agentModelConfig.items()] + [id for id in llmIDs if '' != id])) if '' in llmIDs else llmIDs
        for id in llmIDs:
            modelType, modelName = self.ParseID(id)
            if 0 != len(requirements) and self.config.models[modelType]['modelWrapper'] in ['AModelCausalLM', 'AModelLLAMA']:
                print(f'The specified modelID {id} requires the installation of the following dependencies: {str(requirements)}. Please execute the following command to install: pip install {' '.join(requirements)}')
                sys.exit(0)
            if id not in self.pool:
                self.pool[id] = MODEL_WRAPPER_MAP[self.config.models[modelType]['modelWrapper']](modelType=modelType, modelName=modelName, config=self.config)
        return

    def GetModel(self, modelID: str, agentType: str):
        if '' == modelID:
            if 'DEFAULT' not in self.config.agentModelConfig:
                print('You did not configure a default modelID (agentModelConfig["DEFAULT"]), which makes config.json invalid and unable to start. Please update your configuration.')
                sys.exit(0)
            modelID = self.config.agentModelConfig.get(agentType, self.config.agentModelConfig['DEFAULT'])
        return self.pool[modelID]

def __init__(self, config):
    self.pool = dict()
    self.config = config
    return

