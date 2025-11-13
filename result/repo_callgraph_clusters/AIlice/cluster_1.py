# Cluster 1

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hardware', type=str, default=None, help='Specify preferred hardware, options include: cuda/rocm/vulkan.')
    kwargs = vars(parser.parse_args())
    hardwares = detect_hardware()
    print(f'Detected {'/'.join(hardwares)} support.')
    if kwargs['hardware'] is None and len(hardwares) > 0:
        hardware = hardwares[0]
    elif kwargs['hardware'] in hardwares:
        hardware = kwargs['hardware']
    if hardware == 'cuda':
        os.environ['CMAKE_ARGS'] = '-DGGML_CUDA=on -DLLAVA_BUILD=off'
        print('Using CUDA for installation.')
    elif hardware == 'rocm':
        os.environ['CMAKE_ARGS'] = '-DGGML_HIPBLAS=on -DLLAVA_BUILD=off'
        print('Using HIPBLAS for installation.')
    elif hardware == 'vulkan':
        os.environ['CMAKE_ARGS'] = '-DGGML_VULKAN=on -DLLAVA_BUILD=off'
        print('Using Vulkan for installation.')
    else:
        print('No compatible hardware detected. Exiting.')
        sys.exit(0)
    os.environ['FORCE_CMAKE'] = '1'
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'llama-cpp-python', '--force-reinstall', '--upgrade', '--no-cache-dir'])

def TerminateSubprocess(signum=None, frame=None):
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    sys.exit(0)

def GetInput(speech) -> str:
    if config.speechOn:
        print(colored('USER: ', 'green'), end='', flush=True)
        inp = speech.GetAudio()
        print(inp, end='', flush=True)
        print('')
    else:
        inp = input(colored('USER: ', 'green'))
    return inp

def mainLoop(session: str):
    print(colored('In order to simplify installation and usage, we have set local execution as the default behavior, which means AI has complete control over the local environment. To prevent irreversible losses due to potential AI errors, you may consider one of the following two methods: the first one, run AIlice in a virtual machine; the second one, install Docker, use the provided Dockerfile to build an image and container, and modify the relevant configurations in config.json. For detailed instructions, please refer to the documentation.', 'red'))
    print(colored('If you find that ailice is running slowly or experiencing high CPU usage, please run `ailice_turbo` to install GPU acceleration support.', 'green'))
    if '' != session.strip():
        sessionPath = os.path.join(config.chatHistoryPath, session)
        storagePath = os.path.join(sessionPath, 'storage')
        historyPath = os.path.join(sessionPath, 'ailice_history.json')
        os.makedirs(sessionPath, exist_ok=True)
        os.makedirs(storagePath, exist_ok=True)
    else:
        storagePath = ''
    clientPool = AClientPool()
    StartServices()
    for i in range(5):
        try:
            clientPool.Init()
            break
        except Exception as e:
            if i == 4:
                print(f'It seems that some peripheral module services failed to start. EXCEPTION: {str(e)}')
                print(e.tb) if hasattr(e, 'tb') else traceback.print_tb(e.__traceback__)
                exit(-1)
            time.sleep(5)
            continue
    print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
    print('We now start the vector database. Note that this may include downloading the model weights, so it may take some time.')
    storage = clientPool.GetClient(config.services['storage']['addr'])
    with storage.Timeout(-1):
        msg = storage.Open(storagePath)
    print(msg)
    print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
    if config.speechOn:
        speech = clientPool.GetClient(config.services['speech']['addr'])
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        print('The speech module is preparing speech recognition and TTS models, which may include the work of downloading weight data, so it may take a long time.')
        with speech.Timeout(-1):
            speech.PrepareModel()
        print('The speech module model preparation work is completed.')
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        if any([re.fullmatch('(cuda|cpu)(:(\\d+))?', s) == None for s in [config.ttsDevice, config.sttDevice]]):
            print('the value of ttsDevice and sttDevice should be a valid cuda device, such as cuda, cuda:0, or cpu, the default is cpu.')
            exit(-1)
        else:
            speech.SetDevices({'tts': config.ttsDevice, 'stt': config.sttDevice})
    else:
        speech = None
    timestamp = str(int(time.time()))
    collection = 'ailice_' + timestamp
    promptsManager = APromptsManager()
    promptsManager.Init(storage=storage, collection=collection)
    promptsManager.RegisterPrompts([APromptChat, APromptMain, APromptSearchEngine, APromptResearcher, APromptCoder, APromptModuleCoder, APromptCoderProxy, APromptDocReader])
    llmPool = ALLMPool(config=config)
    llmPool.Init([config.modelID])
    logger = ALogger(speech=None)
    processor = AProcessor(name='AIlice', modelID=config.modelID, promptName=config.prompt, llmPool=llmPool, promptsManager=promptsManager, services=clientPool, messenger=AMessenger(), outputCB=logger.Receiver, gasTank=AGasTank(100000000.0), config=config, collection=collection)
    moduleList = [serviceCfg['addr'] for serviceName, serviceCfg in config.services.items()]
    if not config.speechOn:
        moduleList.remove(config.services['speech']['addr'])
    processor.RegisterModules(moduleList)
    if '' != session.strip():
        if os.path.exists(historyPath):
            with open(historyPath, 'r') as f:
                processor.FromJson(json.load(f))
    while True:
        if '' != session.strip():
            with open(historyPath, 'w') as f:
                json.dump(processor.ToJson(), f, indent=2)
        inpt = GetInput(speech)
        processor.SetGas(100000000.0)
        try:
            processor(inpt)
        except Exception as e:
            continue
    return

def main():
    config.Initialize(configFile=os.path.join(appdirs.user_config_dir('ailice', 'Steven Lu'), 'config.json'))
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelID', type=str, default=config.modelID, help='modelID specifies the model. There are two modes for model configuration. In the first mode, the model is uniformly specified by modelID. In the second mode, different types of agents will run on different models. When this parameter is an empty string (unspecified), the second mode will be used automatically, i.e., the models configured individually for different agents under the agentModelConfig field in config.json will be used. The currently supported models can be seen in config.json. Default: %(default)s')
    parser.add_argument('--quantization', type=str, default=config.quantization, help='quantization is the quantization option, you can choose 4bit or 8bit. Default: %(default)s')
    parser.add_argument('--maxMemory', type=dict, default=config.maxMemory, help='maxMemory is the memory video memory capacity constraint, the format when set is like "{0:"23GiB", 1:"24GiB", "cpu": "64GiB"}". Default: %(default)s')
    parser.add_argument('--prompt', type=str, default=config.prompt, help='prompt specifies the prompt to be executed, which is the type of agent. Default: %(default)s')
    parser.add_argument('--temperature', type=float, default=config.temperature, help='temperature sets the temperature parameter of LLM reasoning. Default: %(default)s')
    parser.add_argument('--flashAttention2', type=bool, default=config.flashAttention2, help='flashAttention2 is the switch to enable flash attention 2 to speed up inference. It may have a certain impact on output quality. Default: %(default)s')
    parser.add_argument('--contextWindowRatio', type=float, default=config.contextWindowRatio, help='contextWindowRatio is a user-specified proportion coefficient, which determines the proportion of the upper limit of the prompt length constructed during inference to the LLM context window in some cases. Default: %(default)s')
    parser.add_argument('--speechOn', type=bool, default=config.speechOn, help='speechOn is the switch to enable voice conversation. Please note that the voice dialogue is currently not smooth yet. Default: %(default)s')
    parser.add_argument('--ttsDevice', type=str, default=config.ttsDevice, help='ttsDevice specifies the computing device used by the text-to-speech model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--sttDevice', type=str, default=config.sttDevice, help='sttDevice specifies the computing device used by the speech-to-text model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--resetApiKey', action='store_true', help="Whether to reset the model's API key after startup.")
    parser.add_argument('--chatHistoryPath', type=str, default=config.chatHistoryPath, help='chatHistoryPath is used to specify the chat history storage path. Default: %(default)s')
    parser.add_argument('--session', type=str, default='', help='session is used to specify the session storage path, if the directory is not empty, the conversation history stored in that directory will be loaded and updated. Default: %(default)s')
    kwargs = vars(parser.parse_args())
    config.Check4Update(kwargs['modelID'], kwargs['resetApiKey'])
    config.Update(kwargs)
    try:
        mainLoop(session=kwargs['session'])
    except Exception as e:
        print(f'Encountered an exception, AIlice is exiting: {str(e)}')
        print(e.tb) if hasattr(e, 'tb') else traceback.print_tb(e.__traceback__)
        TerminateSubprocess()
        raise

def GenerateRE4FunctionCalling(signature: str, faultTolerance: bool=False) -> str:
    pattern = '([a-zA-Z0-9_\\-]+)<!\\|((?:\\w+\\s*:\\s*[\\w,\\. ]+)*)\\|!>((?:\\s*->\\s*)([\\w\\.]+))?'
    matches = re.search(pattern, signature)
    if matches is None:
        print('signature invalid. exit. ', signature)
        exit()
    funcName, args, retType = (matches[1], matches[2], matches[4])
    pattern = '(\\w+)\\s*:\\s*(\\w+)'
    typePairs = re.findall(pattern, args)
    reMap = {k: v for k, v in ARegexMap.items()}
    reMap['str'] = '(.*?(?=(?:\\s*)\\|!>))' if faultTolerance and 1 == len(typePairs) and ('str' == typePairs[0][1]) else ARegexMap['str']
    refOrcatOrObj = f'{reMap['ref']}|{reMap['expr_cat']}|(?:<([a-zA-Z0-9_&!]+)\\|(?:.*?)\\|([a-zA-Z0-9_&!]+)>)'
    patternArgs = '\\s*,\\s*'.join([f"""(?:({arg}|\\"{arg}\\"|\\'{arg}\\')\\s*[:=]\\s*)?(?P<{arg}>({(reMap[tp] + '|' if tp in reMap else '')}{refOrcatOrObj}))""" for arg, tp in typePairs])
    return f'!{funcName}<!\\|\\s*{patternArgs}\\s*\\|!>'

def Init():
    StartServices()
    logger.info('Services started')
    context.Create()
    InitServer()
    return

def main():
    config.Initialize(configFile=AILICE_CONFIG)
    logger.info('Configuration initialized')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelID', type=str, default=config.modelID, help='modelID specifies the model. There are two modes for model configuration. In the first mode, the model is uniformly specified by modelID. In the second mode, different types of agents will run on different models. When this parameter is an empty string (unspecified), the second mode will be used automatically, i.e., the models configured individually for different agents under the agentModelConfig field in config.json will be used. The currently supported models can be seen in config.json. Default: %(default)s')
    parser.add_argument('--quantization', type=str, default=config.quantization, help='quantization is the quantization option, you can choose 4bit or 8bit. Default: %(default)s')
    parser.add_argument('--maxMemory', type=dict, default=config.maxMemory, help='maxMemory is the memory video memory capacity constraint, the format when set is like "{0:"23GiB", 1:"24GiB", "cpu": "64GiB"}". Default: %(default)s')
    parser.add_argument('--prompt', type=str, default=config.prompt, help='prompt specifies the prompt to be executed, which is the type of agent. Default: %(default)s')
    parser.add_argument('--temperature', type=float, default=config.temperature, help='temperature sets the temperature parameter of LLM reasoning. Default: %(default)s')
    parser.add_argument('--flashAttention2', type=bool, default=config.flashAttention2, help='flashAttention2 is the switch to enable flash attention 2 to speed up inference. It may have a certain impact on output quality. Default: %(default)s')
    parser.add_argument('--contextWindowRatio', type=float, default=config.contextWindowRatio, help='contextWindowRatio is a user-specified proportion coefficient, which determines the proportion of the upper limit of the prompt length constructed during inference to the LLM context window in some cases. Default: %(default)s')
    parser.add_argument('--speechOn', type=bool, default=config.speechOn, help='speechOn is the switch to enable voice conversation. Please note that the voice dialogue is currently not smooth yet. Default: %(default)s')
    parser.add_argument('--ttsDevice', type=str, default=config.ttsDevice, help='ttsDevice specifies the computing device used by the text-to-speech model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--sttDevice', type=str, default=config.sttDevice, help='sttDevice specifies the computing device used by the speech-to-text model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--resetApiKey', action='store_true', help="Whether to reset the model's API key after startup.")
    parser.add_argument('--chatHistoryPath', type=str, default=config.chatHistoryPath, help='chatHistoryPath is used to specify the chat history storage path. Default: %(default)s')
    parser.add_argument('--certificate', type=str, default=config.certificate, help='Certificate settings for the web interface. The simplest option is an empty string, which will use the HTTP protocol for the UI web page. Setting it to \'adhoc\' will use a self-generated certificate, providing encryption for the data flow between the UI and server, but it requires dismissing browser security warnings. The most secure method is to apply for a certificate and set this parameter to \'{"cert": "your_cert.pem", "key": "your_key.pem")\'. Default: %(default)s')
    parser.add_argument('--expose', type=bool, default=False, help='Whether to provide public access. Default: %(default)s')
    parser.add_argument('--logLevel', type=str, default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: %(default)s')
    kwargs = vars(parser.parse_args())
    log_level = getattr(logging, kwargs['logLevel'].upper(), logging.INFO)
    logger.setLevel(log_level)
    logger.info(f'Log level set to {kwargs['logLevel']}')
    config.Check4Update(kwargs['modelID'], kwargs['resetApiKey'])
    config.Update(kwargs)
    logger.info(f'Configuration updated with command line arguments')
    try:
        Init()
        if kwargs['certificate'] == '':
            ssl_context = None
            logger.info('Starting server with HTTP (no SSL)')
        elif kwargs['certificate'] == 'adhoc':
            ssl_context = 'adhoc'
            logger.info('Starting server with self-signed certificate')
        else:
            try:
                certCfg = json.loads(kwargs['certificate'])
                ssl_context = (certCfg['cert'], certCfg['key'])
                logger.info(f'Starting server with certificate: {certCfg['cert']} and key: {certCfg['key']}')
            except Exception as e:
                error_msg = 'The certificate configuration you entered could not be recognized. Please set it according to the following format: {"cert": "your_cert.pem", "key": "your_key.pem")'
                logger.error(f'{error_msg}. Error: {str(e)}')
                print(error_msg)
                sys.exit(0)
        host = '0.0.0.0' if kwargs['expose'] else '127.0.0.1'
        port = 5000
        logger.info(f'Starting Flask server on {host}:{port}')
        app.run(debug=False, ssl_context=ssl_context, host=host, port=port)
    except Exception as e:
        error_msg = f'Encountered an exception, AIlice is exiting: {str(e)}'
        logger.critical(error_msg, exc_info=True)
        print(error_msg)
        if hasattr(e, 'tb'):
            print(e.tb)
        else:
            traceback.print_tb(e.__traceback__)
        TerminateSubprocess()
        raise

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

def Receiver(self, channel: str, txt: str=None, action: str=''):
    braketMap = {'<': 1, '>': -1}
    self.depth += braketMap[channel] if channel in braketMap else 0
    channelType, _ = self.ParseChannel(channel)
    if channelType in ['ASSISTANT', 'SYSTEM']:
        self.SinkPrint(channel=channel, txt=txt, action=action)
    if channelType in ['ASSISTANT', 'SYSTEM', '>'] or ('USER' == channelType and self.depth == 0):
        self.SinkBuffer(channel=channel, txt=txt, action=action)
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

def SendMsg(conn, msg):
    try:
        conn.send(json.dumps(msg, cls=AJSONEncoder).encode('utf-8'))
    except Exception as e:
        print('Exception: ', str(e))
        traceback.print_tb(e.__traceback__)
    return

class GenesisRPCServer(object):

    def __init__(self, objCls, objArgs, url, APIList, serverPrivateKeyPath=None, clientPublicKeysDir=None, validateReturn=True, atomicCall=True):
        global auth, authLock
        self.objCls = validate_methods(objCls, APIList, validateReturn)
        self.objArgs = objArgs
        self.url = url
        self.objPool = dict()
        self.objPoolLock = threading.Lock()
        self.APIList = APIList
        self.atomicCall = atomicCall
        self.context = context
        self.domain = str(uuid.uuid4())
        self.WORKERS_ADDR = f'inproc://workers-{self.domain}'
        self.receiver = self.context.socket(zmq.ROUTER)
        if serverPrivateKeyPath is None:
            serverPrivateKeyPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates/server/server.key_secret')
            clientPublicKeysDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates/client/')
            if not os.path.exists(clientPublicKeysDir):
                clientPublicKeysDir = None
        self.enableSecurity = os.path.exists(serverPrivateKeyPath)
        if self.enableSecurity:
            print('lightRPC server encryption ENABLED.')
            with authLock:
                if auth is None:
                    auth = ThreadAuthenticator(context)
                    auth.start()
                auth.configure_curve(domain=self.domain, location=zmq.auth.CURVE_ALLOW_ANY if clientPublicKeysDir is None else clientPublicKeysDir)
            serverPublic, serverSecret = zmq.auth.load_certificate(serverPrivateKeyPath)
            self.receiver.setsockopt_string(zmq.ZAP_DOMAIN, self.domain)
            self.receiver.setsockopt(zmq.CURVE_PUBLICKEY, serverPublic)
            self.receiver.setsockopt(zmq.CURVE_SECRETKEY, serverSecret)
            self.receiver.setsockopt(zmq.CURVE_SERVER, True)
        self.receiver.bind(url)
        self.dealer = self.context.socket(zmq.DEALER)
        self.dealer.bind(self.WORKERS_ADDR)
        return

    def Run(self):
        try:
            for i in range(16):
                thread = threading.Thread(target=self.Worker, name='RPC-Worker-%d' % (i + 1))
                thread.daemon = True
                thread.start()
            zmq.device(zmq.QUEUE, self.receiver, self.dealer)
        except Exception as e:
            print('GenesisRPCServer:Run() FATAL EXCEPTION. ', self.url, ', ', str(e))
            sys.exit(1)
        finally:
            self.receiver.close()
            self.dealer.close()

    def CreateSocket(self):
        socket = self.context.socket(zmq.DEALER)
        socket.setsockopt(zmq.HEARTBEAT_IVL, 2000)
        socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 10000)
        socket.connect(self.WORKERS_ADDR)
        return socket

    def Worker(self):
        socket = self.CreateSocket()
        while True:
            try:
                frames = socket.recv_multipart()
                if len(frames) >= 3:
                    clientIdentity = frames[0]
                    delimiter = frames[1]
                    msgData = frames[2]
                    msg = json.loads(msgData.decode('utf-8'), cls=AJSONDecoder)
                    ret = None
                    try:
                        if 'clientID' in msg and msg['clientID'] not in self.objPool:
                            ret = {'exception': str(KeyError(f'clientID {msg['clientID']} not exist.'))}
                        elif 'GET_META' in msg:
                            methods = inspect.getmembers(self.objCls, predicate=lambda x: inspect.isfunction(x) and x.__name__ in self.APIList)
                            ret = {'META': {'methods': {methodName: {'signature': str(inspect.signature(method)), 'is_generator': inspect.isgeneratorfunction(method)} for methodName, method in methods}}}
                        elif 'CREATE' in msg:
                            with self.objPoolLock:
                                newID = str(secrets.token_hex(64))
                                self.objPool[newID] = GeneratorStorage(self.objCls(**self.objArgs), self.atomicCall)
                            ret = {'clientID': newID}
                        elif 'DEL' in msg:
                            with self.objPoolLock:
                                if msg['clientID'] in self.objPool:
                                    del self.objPool[msg['clientID']]
                                ret = {}
                        elif 'NEXT' in msg:
                            with self.objPoolLock:
                                storageObj = self.objPool[msg['clientID']]
                            try:
                                with storageObj.lock:
                                    ret = {'ret': next(storageObj.GetGenerator(msg['generatorID'])), 'finished': False}
                            except StopIteration:
                                ret = {'ret': None, 'finished': True}
                        else:
                            with self.objPoolLock:
                                storageObj = self.objPool[msg['clientID']]
                            with storageObj.lock:
                                result = getattr(storageObj, msg['function'])(*msg['args'], **msg['kwargs'])
                            if inspect.isgenerator(result):
                                generatorID = str(id(result))
                                with self.objPoolLock:
                                    self.objPool[msg['clientID']].SaveGenerator(generatorID, result)
                                ret = {'ret': {'generatorID': generatorID}}
                            else:
                                ret = {'ret': result}
                    except Exception as e:
                        e.tb = ''.join(traceback.format_tb(e.__traceback__))
                        ret = {'exception': f'{str(e)}\n\n{e.tb}'}
                        traceback.print_tb(e.__traceback__)
                        print('Exception. msg:', str(msg), '. Except:', str(e))
                    if ret is not None:
                        responseData = json.dumps(ret, cls=AJSONEncoder).encode('utf-8')
                        socket.send_multipart([clientIdentity, delimiter, responseData])
                else:
                    print(f'Warning: Received unexpected frame count: {len(frames)}')
            except Exception as e:
                print('Worker exception:', str(e))
                traceback.print_tb(e.__traceback__)
                socket.close()
                socket = self.CreateSocket()
                continue

def Run(self):
    try:
        for i in range(16):
            thread = threading.Thread(target=self.Worker, name='RPC-Worker-%d' % (i + 1))
            thread.daemon = True
            thread.start()
        zmq.device(zmq.QUEUE, self.receiver, self.dealer)
    except Exception as e:
        print('GenesisRPCServer:Run() FATAL EXCEPTION. ', self.url, ', ', str(e))
        sys.exit(1)
    finally:
        self.receiver.close()
        self.dealer.close()

def FromJson(data):
    typeMap = {'AImage': AImage, 'AImageLocation': AImageLocation, 'AVideo': AVideo, 'AVideoLocation': AVideoLocation}
    if data['type'] in typeMap:
        return typeMap[data['type']].FromJson(data)
    else:
        return data['data']

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

def Init():
    print(colored('In order to simplify installation and usage, we have set local execution as the default behavior, which means AI has complete control over the local environment. To prevent irreversible losses due to potential AI errors, you may consider one of the following two methods: the first one, run AIlice in a virtual machine; the second one, install Docker, use the provided Dockerfile to build an image and container, and modify the relevant configurations in config.json. For detailed instructions, please refer to the documentation.', 'red'))
    print(colored('If you find that ailice is running slowly or experiencing high CPU usage, please run `ailice_turbo` to install GPU acceleration support.', 'green'))
    StartServices()
    InitServer()
    return

def InitSpeech(clientPool):
    global speech
    if config.speechOn:
        import sounddevice as sd
        speech = clientPool.GetClient(config.services['speech']['addr'])
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        print('The speech module is preparing speech recognition and TTS models, which may include the work of downloading weight data, so it may take a long time.')
        with speech.Timeout(-1):
            speech.PrepareModel()
        print('The speech module model preparation work is completed.')
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        if any([re.fullmatch('(cuda|cpu)(:(\\d+))?', s) == None for s in [config.ttsDevice, config.sttDevice]]):
            print('the value of ttsDevice and sttDevice should be a valid cuda device, such as cuda, cuda:0, or cpu, the default is cpu.')
            exit(-1)
        else:
            speech.SetDevices({'tts': config.ttsDevice, 'stt': config.sttDevice})
    else:
        speech = None
    return

def LoadSession(sessionName: str):
    global context, currentSession
    try:
        if sessionName in context:
            currentSession = sessionName
            return
        sessionPath = os.path.join(config.chatHistoryPath, sessionName)
        os.makedirs(sessionPath, exist_ok=True)
        os.makedirs(os.path.join(sessionPath, 'storage'), exist_ok=True)
        app.config['UPLOAD_FOLDER'] = f'{str(sessionPath)}/uploads'
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        clientPool = AClientPool()
        for i in range(5):
            try:
                clientPool.Init()
                break
            except Exception as e:
                if i == 4:
                    print(f'It seems that some peripheral module services failed to start. EXCEPTION: {str(e)}')
                    print(e.tb) if hasattr(e, 'tb') else traceback.print_tb(e.__traceback__)
                time.sleep(5)
                continue
        InitSpeech(clientPool)
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        print('We now start the vector database. Note that this may include downloading the model weights, so it may take some time.')
        storage = clientPool.GetClient(config.services['storage']['addr'])
        with storage.Timeout(-1):
            msg = storage.Open(os.path.join(sessionPath, 'storage'))
        print(msg)
        print(colored('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', 'green'))
        llmPool = ALLMPool(config=config)
        llmPool.Init([config.modelID])
        promptsManager = APromptsManager()
        promptsManager.Init(storage=storage, collection=sessionName)
        promptsManager.RegisterPrompts([APromptChat, APromptMain, APromptSearchEngine, APromptResearcher, APromptCoder, APromptModuleCoder, APromptCoderProxy, APromptDocReader])
        messenger = AMessenger()
        logger = ALogger(speech=None)
        processor = AProcessor(name='AIlice', modelID=config.modelID, promptName=config.prompt, llmPool=llmPool, promptsManager=promptsManager, services=clientPool, messenger=messenger, outputCB=logger.Receiver, gasTank=AGasTank(100000000.0), config=config, collection=sessionName)
        moduleList = [serviceCfg['addr'] for serviceName, serviceCfg in config.services.items()]
        if not config.speechOn:
            moduleList.remove(config.services['speech']['addr'])
        processor.RegisterModules(moduleList)
        p = os.path.join(sessionPath, 'ailice_history.json')
        if os.path.exists(p):
            with open(p, 'r') as f:
                processor.FromJson(json.load(f))
        context[sessionName] = {'processor': processor, 'llmPool': llmPool, 'messenger': messenger, 'logger': logger}
        currentSession = sessionName
    except Exception as e:
        print('Exception: ', str(e))
        print(e.tb) if hasattr(e, 'tb') else traceback.print_tb(e.__traceback__)
        exit(-1)
    return

def main():
    config.Initialize(configFile=os.path.join(appdirs.user_config_dir('ailice', 'Steven Lu'), 'config.json'))
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelID', type=str, default=config.modelID, help='modelID specifies the model. There are two modes for model configuration. In the first mode, the model is uniformly specified by modelID. In the second mode, different types of agents will run on different models. When this parameter is an empty string (unspecified), the second mode will be used automatically, i.e., the models configured individually for different agents under the agentModelConfig field in config.json will be used. The currently supported models can be seen in config.json. Default: %(default)s')
    parser.add_argument('--quantization', type=str, default=config.quantization, help='quantization is the quantization option, you can choose 4bit or 8bit. Default: %(default)s')
    parser.add_argument('--maxMemory', type=dict, default=config.maxMemory, help='maxMemory is the memory video memory capacity constraint, the format when set is like "{0:"23GiB", 1:"24GiB", "cpu": "64GiB"}". Default: %(default)s')
    parser.add_argument('--prompt', type=str, default=config.prompt, help='prompt specifies the prompt to be executed, which is the type of agent. Default: %(default)s')
    parser.add_argument('--temperature', type=float, default=config.temperature, help='temperature sets the temperature parameter of LLM reasoning. Default: %(default)s')
    parser.add_argument('--flashAttention2', type=bool, default=config.flashAttention2, help='flashAttention2 is the switch to enable flash attention 2 to speed up inference. It may have a certain impact on output quality. Default: %(default)s')
    parser.add_argument('--contextWindowRatio', type=float, default=config.contextWindowRatio, help='contextWindowRatio is a user-specified proportion coefficient, which determines the proportion of the upper limit of the prompt length constructed during inference to the LLM context window in some cases. Default: %(default)s')
    parser.add_argument('--speechOn', type=bool, default=config.speechOn, help='speechOn is the switch to enable voice conversation. Please note that the voice dialogue is currently not smooth yet. Default: %(default)s')
    parser.add_argument('--ttsDevice', type=str, default=config.ttsDevice, help='ttsDevice specifies the computing device used by the text-to-speech model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--sttDevice', type=str, default=config.sttDevice, help='sttDevice specifies the computing device used by the speech-to-text model. You can set it to "cuda" if there is enough video memory. Default: %(default)s')
    parser.add_argument('--resetApiKey', action='store_true', help="Whether to reset the model's API key after startup.")
    parser.add_argument('--chatHistoryPath', type=str, default=config.chatHistoryPath, help='chatHistoryPath is used to specify the chat history storage path. Default: %(default)s')
    parser.add_argument('--certificate', type=str, default=config.certificate, help='Certificate settings for the web interface. The simplest option is an empty string, which will use the HTTP protocol for the UI web page. Setting it to \'adhoc\' will use a self-generated certificate, providing encryption for the data flow between the UI and server, but it requires dismissing browser security warnings. The most secure method is to apply for a certificate and set this parameter to \'{"cert": "your_cert.pem", "key": "your_key.pem")\'. Default: %(default)s')
    parser.add_argument('--expose', type=bool, default=False, help='Whether to provide public access. Default: %(default)s')
    kwargs = vars(parser.parse_args())
    config.Check4Update(kwargs['modelID'], kwargs['resetApiKey'])
    config.Update(kwargs)
    try:
        Init()
        if kwargs['certificate'] == '':
            ssl_context = None
        elif kwargs['certificate'] == 'adhoc':
            ssl_context = 'adhoc'
        else:
            try:
                certCfg = json.loads(kwargs['certificate'])
                ssl_context = (certCfg['cert'], certCfg['key'])
            except Exception as e:
                print('The certificate configuration you entered could not be recognized. Please set it according to the following format: {"cert": "your_cert.pem", "key": "your_key.pem")')
                sys.exit(0)
        app.run(debug=False, ssl_context=ssl_context, host='0.0.0.0' if kwargs['expose'] else '127.0.0.1', port=5000)
    except Exception as e:
        print(f'Encountered an exception, AIlice is exiting: {str(e)}')
        print(e.tb) if hasattr(e, 'tb') else traceback.print_tb(e.__traceback__)
        TerminateSubprocess()
        raise

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

def Release(self):
    self.stopEvent.set()
    self.hippocampus.join(timeout=2)
    if self.dir is not None:
        self.Dump(self.dir)
    print('Vector database service released.')

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

def ExecuteJS(self, js_code: str, session: str) -> str:
    return self.sessions[session].ExecuteJS(js_code) if hasattr(self.sessions[session], 'ExecuteJS') else 'ExecuteJS not supported in current browser.'

def GetLink(self, text: str, session: str) -> str:
    return self.sessions[session].GetLink(text) if hasattr(self.sessions[session], 'GetLink') else 'GetLink not supported in current browser.'

def Replace(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
    return self.sessions[session].Replace(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'Replace') else 'Replace not supported in current browser.'

def ReplaceAll(self, pattern: str, replacement: str, regexMode: bool, session: str) -> str:
    return self.sessions[session].ReplaceAll(pattern, replacement, regexMode) if hasattr(self.sessions[session], 'ReplaceAll') else 'ReplaceAll not supported in current browser.'

def SaveTo(self, dstPath: str, session: str) -> str:
    return self.sessions[session].SaveTo(dstPath) if hasattr(self.sessions[session], 'SaveTo') else 'SaveTo not supported in current browser.'

class AMCPWrapper:
    MODULE_INFO = {'NAME': serverParams.args[0] if serverParams is not None else serverUrl, 'ACTIONS': {}}

    def __init__(self, serverParams=None, serverUrl=None):
        self.serverParams = serverParams
        self.serverUrl = serverUrl
        self.exit_stack = None
        self.stdio = None
        self.write = None
        self.session = None
        asyncio.run_coroutine_threadsafe(self.initialize(), loop).result()
        return

    def __del__(self):
        if hasattr(self, 'exit_stack') and self.exit_stack:
            try:
                asyncio.run_coroutine_threadsafe(self.close(), loop).result()
            except Exception as e:
                print(f'Error closing resources: {e}')

    async def initialize(self):
        self.exit_stack = AsyncExitStack()
        if self.serverParams is not None:
            self.MODULE_INFO['NAME'] = self.serverParams.args[0]
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(self.serverParams))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
        elif self.serverUrl is not None:
            self.MODULE_INFO['NAME'] = self.serverUrl
            streams = await self.exit_stack.enter_async_context(sse_client(url=self.serverUrl))
            self.session = await self.exit_stack.enter_async_context(ClientSession(*streams))
        await self.session.initialize()

    async def close(self):
        if self.exit_stack:
            await self.exit_stack.aclose()

    def ModuleInfo(self):
        return self.MODULE_INFO

def __del__(self):
    if hasattr(self, 'exit_stack') and self.exit_stack:
        try:
            asyncio.run_coroutine_threadsafe(self.close(), loop).result()
        except Exception as e:
            print(f'Error closing resources: {e}')

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

def EvalStore(self, txt: str):
    self.modules['storage']['module'].Store(self.collection, txt)
    return

def EvalWait(self, duration: int) -> str:
    time.sleep(duration)
    return f'Waiting is over. It has been {duration} seconds.'

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

def RegisterAction(self, nodeType: str, action: dict):
    signature = inspect.signature(action['func'])
    if not all([param.annotation != inspect.Parameter.empty for param in signature.parameters.values()]):
        print('Need annotations in registered function. node type: ', nodeType)
        exit()
    self.actions[nodeType] = {k: v for k, v in action.items()}
    self.actions[nodeType]['signature'] = signature
    return

def Parse(self, txt: str) -> tuple[str, dict[str, str]]:
    for p in self.patterns:
        m = re.fullmatch(p['re'], txt, re.DOTALL)
        if m:
            return (p['nodeType'], m.groupdict())
    return (None, None)

class AModelCausalLM:

    def __init__(self, modelType: str, modelName: str, config):
        self.modelType = modelType
        self.config = config
        self.tokenizer = None
        self.model = None
        self.configMap = {'': None, None: None, '4bit': transformers.BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16), '8bit': transformers.BitsAndBytesConfig(load_in_8bit=True)}
        self.LoadModel(modelName)
        if modelType not in config.models or modelName not in config.models[modelType]['modelList']:
            print(f'LLM {modelType}:{modelName} not supported yet.')
            exit(-1)
        modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=modelCfg['systemAsUser'])
        self.contextWindow = modelCfg['contextWindow']
        return

    def LoadModel(self, modelName: str):
        if 'peft' == self.modelType:
            self.LoadModel_PEFT(modelName=modelName)
        else:
            self.LoadModel_Default(modelName=modelName)
        return

    def LoadModel_Default(self, modelName: str):
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(modelName, use_fast=False, legacy=False, force_download=False, resume_download=True)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(modelName, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory, force_download=False, resume_download=True)
        return

    def LoadModel_PEFT(self, modelName: str):
        if not PEFT_INSTALLED:
            print('peft not installed. Please install it with the following command: pip install -e .[finetuning]')
            sys.exit()
        peftConfig = PeftConfig.from_pretrained(modelName)
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(peftConfig.base_model_name_or_path, use_fast=False)
        self.model = transformers.AutoModelForCausalLM.from_pretrained(peftConfig.base_model_name_or_path, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory)
        self.model = PeftModel.from_pretrained(self.model, modelName)
        return

    def Generate(self, prompt: str, proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        predictedIDs = torch.tensor([prompt[0]]).cuda()
        generatedIDs = None
        pastKeyValues = None
        currentPosition = 0
        text = ''
        gasTank.Consume(resourceType='HFCausalLM/InputTokens', amount=predictedIDs.shape[1])
        for _ in range(4096):
            with torch.no_grad():
                outputs = self.model(input_ids=predictedIDs, past_key_values=pastKeyValues, use_cache=True)
            logits = outputs.logits
            pastKeyValues = outputs.past_key_values
            if temperature > 1e-09:
                scaledLogits = logits / temperature
                probs = torch.nn.functional.softmax(scaledLogits, dim=-1)
                predictedIDs = torch.multinomial(probs[:, -1, :], 1)
            else:
                predictedIDs = torch.argmax(logits[..., -1, :], dim=-1, keepdim=True)
            gasTank.Consume(resourceType='HFCausalLM/OutputTokens', amount=predictedIDs.shape[1])
            generatedIDs = predictedIDs if None == generatedIDs else torch.cat((generatedIDs, predictedIDs), dim=-1)
            text = self.tokenizer.decode(generatedIDs[0].cpu().numpy(), skip_special_tokens=True)
            if predictedIDs.item() == self.tokenizer.eos_token_id or endchecker(text):
                break
            sentences = [x for x in sentences_split(text[currentPosition:])]
            if 2 <= len(sentences) and '' != sentences[0].strip():
                proc(txt=sentences[0])
                currentPosition += len(sentences[0])
        proc(txt=text[currentPosition:])
        return text

def LoadModel_PEFT(self, modelName: str):
    if not PEFT_INSTALLED:
        print('peft not installed. Please install it with the following command: pip install -e .[finetuning]')
        sys.exit()
    peftConfig = PeftConfig.from_pretrained(modelName)
    self.tokenizer = transformers.AutoTokenizer.from_pretrained(peftConfig.base_model_name_or_path, use_fast=False)
    self.model = transformers.AutoModelForCausalLM.from_pretrained(peftConfig.base_model_name_or_path, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory)
    self.model = PeftModel.from_pretrained(self.model, modelName)
    return

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

def GetModel(self, modelID: str, agentType: str):
    if '' == modelID:
        if 'DEFAULT' not in self.config.agentModelConfig:
            print('You did not configure a default modelID (agentModelConfig["DEFAULT"]), which makes config.json invalid and unable to start. Please update your configuration.')
            sys.exit(0)
        modelID = self.config.agentModelConfig.get(agentType, self.config.agentModelConfig['DEFAULT'])
    return self.pool[modelID]

