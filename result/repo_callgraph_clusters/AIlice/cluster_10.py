# Cluster 10

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

def response(msg: str):
    try:
        self.processor(msg)
    except Exception as e:
        pass
    finally:
        if 'generating' == self.state:
            self.answered()
        self.Save()

def finetune(modelID, dataset: str, dataDir: str, epochs: int, maxWindow: int, outDir: str, logDir: str):
    config.Initialize(needOpenaiGPTKey=False)
    modelType, modelName = (modelID[:modelID.find(':')], modelID[modelID.find(':') + 1:])
    ds = load_dataset(dataset, maxWindow=maxWindow, data_dir=dataDir)
    tokenizer = transformers.AutoTokenizer.from_pretrained(modelName, truncation=True, max_length=maxWindow, add_special_tokens=True, add_bos_token=False, add_eos_token=False, legacy=False)
    tokenizer.pad_token = tokenizer.unk_token
    quant_config = transformers.BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
    model = transformers.AutoModelForCausalLM.from_pretrained(modelName, quantization_config=quant_config, device_map='auto')
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    def tokenizeOpenorca(batch):
        concatenatedSamples = [f'<|im_start|>system\n{system_prompt}\n<|im_end|>\n<|im_start|>user\n{question}\n<|im_end|>\n<|im_start|>assistant\n{response}\n<|im_end|>' for system_prompt, question, response in zip(batch['system_prompt'], batch['question'], batch['response'])]
        tokenizedInputs = tokenizer(concatenatedSamples, padding=True, truncation=True, max_length=maxWindow, return_tensors='pt')
        return tokenizedInputs

    def tokenizeAIlice(batch):
        modelCfg = config.models[modelType]['modelList'][modelName]
        formatter = CreateFormatter(modelCfg['formatter'], tokenizer=None, systemAsUser=modelCfg['systemAsUser'])
        concatenatedSamples = [formatter(prompt0='', conversations=[{'role': role, 'msg': msg} for role, msg in zip(conv['role'], conv['msg'])], encode=False, assistTag=False)[0] for conv in batch['conversations']]
        tokenizedInputs = tokenizer(concatenatedSamples, padding=True, truncation=True, max_length=maxWindow, return_tensors='pt')
        return tokenizedInputs
    trainData = ds['train'].map(tokenizeAIlice, batched=True, num_proc=32, remove_columns=['conversations'])
    trainData = trainData.add_column('labels', trainData['input_ids'])
    trainData = trainData.with_format('torch')
    validData = ds['validation'].map(tokenizeAIlice, batched=True, num_proc=32, remove_columns=['conversations'])
    validData = validData.add_column('labels', validData['input_ids'])
    validData = validData.with_format('torch')
    loraConfig = LoraConfig(r=LORA_R, lora_alpha=LORA_ALPHA, target_modules=LORA_TARGET_MODULES, lora_dropout=LORA_DROPOUT, bias='none', task_type='CAUSAL_LM')
    model = get_peft_model(model, loraConfig)
    model.print_trainable_parameters()
    trainingArguments = transformers.TrainingArguments(per_device_train_batch_size=MICRO_BATCH_SIZE, gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS, warmup_ratio=0.1, num_train_epochs=epochs, learning_rate=LEARNING_RATE, fp16=True, logging_steps=10, optim='paged_adamw_8bit', evaluation_strategy='no', save_strategy='steps', eval_steps=50, save_steps=50, output_dir=outDir, save_total_limit=3, load_best_model_at_end=False, report_to='tensorboard', logging_dir=logDir)
    collator = MyDataCollatorWithPadding(tokenizer=tokenizer, return_tensors='pt', padding=True)
    trainer = transformers.Trainer(model=model, train_dataset=trainData, eval_dataset=validData, args=trainingArguments, data_collator=collator)
    model.config.use_cache = False
    model = torch.compile(model)
    trainer.train()
    model.save_pretrained(outDir)

def tokenizeOpenorca(batch):
    concatenatedSamples = [f'<|im_start|>system\n{system_prompt}\n<|im_end|>\n<|im_start|>user\n{question}\n<|im_end|>\n<|im_start|>assistant\n{response}\n<|im_end|>' for system_prompt, question, response in zip(batch['system_prompt'], batch['question'], batch['response'])]
    tokenizedInputs = tokenizer(concatenatedSamples, padding=True, truncation=True, max_length=maxWindow, return_tensors='pt')
    return tokenizedInputs

def tokenizeAIlice(batch):
    modelCfg = config.models[modelType]['modelList'][modelName]
    formatter = CreateFormatter(modelCfg['formatter'], tokenizer=None, systemAsUser=modelCfg['systemAsUser'])
    concatenatedSamples = [formatter(prompt0='', conversations=[{'role': role, 'msg': msg} for role, msg in zip(conv['role'], conv['msg'])], encode=False, assistTag=False)[0] for conv in batch['conversations']]
    tokenizedInputs = tokenizer(concatenatedSamples, padding=True, truncation=True, max_length=maxWindow, return_tensors='pt')
    return tokenizedInputs

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

def PrepareModel(self):
    self.tokenizer = AutoTokenizer.from_pretrained(self.data['tokenizer'])
    self.model = AutoModel.from_pretrained(self.data['model'], trust_remote_code=True)
    self.model.eval()
    return

class S2T_WhisperLarge:

    def __init__(self):
        self.device = 'cpu'
        self.processor = WhisperProcessor.from_pretrained('openai/whisper-large-v3')
        self.model = WhisperForConditionalGeneration.from_pretrained('openai/whisper-large-v3').to(self.device)
        self.model.config.forced_decoder_ids = None
        self.audio = AudioSourceSileroVAD()
        return

    def To(self, device: str):
        self.model = self.model.to(device)
        self.device = device
        return

    def __call__(self):
        said = ''
        while said == '':
            print('listening...')
            audio, sr = self.audio.get()
            print('got audio. processing...')
            try:
                said = self.recognize(audio_data_to_numpy((audio, sr), sr=16000))
                print('audio recognized: ', said)
            except Exception as e:
                print('Exception: ' + str(e))
                continue
        return said

    def recognize(self, audio):
        input_features = self.processor(audio, sampling_rate=16000, return_tensors='pt').input_features
        predicted_ids = self.model.generate(input_features.to(self.device))
        transcription = self.processor.batch_decode(predicted_ids.cpu(), skip_special_tokens=True)
        return transcription[0]

def __init__(self):
    self.device = 'cpu'
    self.processor = WhisperProcessor.from_pretrained('openai/whisper-large-v3')
    self.model = WhisperForConditionalGeneration.from_pretrained('openai/whisper-large-v3').to(self.device)
    self.model.config.forced_decoder_ids = None
    self.audio = AudioSourceSileroVAD()
    return

def To(self, device: str):
    self.model = self.model.to(device)
    self.device = device
    return

def recognize(self, audio):
    input_features = self.processor(audio, sampling_rate=16000, return_tensors='pt').input_features
    predicted_ids = self.model.generate(input_features.to(self.device))
    transcription = self.processor.batch_decode(predicted_ids.cpu(), skip_special_tokens=True)
    return transcription[0]

class AModelChatGPT:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = self.config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update({'max_tokens': 4096} if 'vision' in self.modelName else {})
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='ChatGPT/InputTokens', amount=prompt[1])
            with openai.OpenAI(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
                for chunk in client.chat.completions.create(model=self.modelName, messages=prompt[0], stream=True, timeout=60, **extras):
                    text += chunk.choices[0].delta.content or ''
                    if endchecker(text):
                        break
                    sentences = [x for x in sentences_split(text[currentPosition:])]
                    if 2 <= len(sentences) and '' != sentences[0].strip():
                        gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(sentences[0]) // 4)
                        proc(txt=sentences[0])
                        currentPosition += len(sentences[0])
        except openai.AuthenticationError as e:
            msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
            print('\n\n', msg)
            print('\n\nException:\n', str(e))
            os._exit(1)
        gasTank.Consume(resourceType='ChatGPT/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def __init__(self, modelType: str, modelName: str, config):
    self.tokenizer = None
    self.modelType = modelType
    self.modelName = modelName
    self.config = config
    self.modelCfg = self.config.models[modelType]['modelList'][modelName]
    self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
    self.contextWindow = self.modelCfg['contextWindow']
    return

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

def LoadModel_Default(self, modelName: str):
    self.tokenizer = transformers.AutoTokenizer.from_pretrained(modelName, use_fast=False, legacy=False, force_download=False, resume_download=True)
    self.model = transformers.AutoModelForCausalLM.from_pretrained(modelName, device_map='auto', low_cpu_mem_usage=True, quantization_config=self.configMap[self.config.quantization], attn_implementation='flash_attention_2' if self.config.flashAttention2 else None, max_memory=self.config.maxMemory, force_download=False, resume_download=True)
    return

class AModelAnthropic:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='Anthropic/InputTokens', amount=prompt[1])
            with anthropic.Anthropic(api_key=self.config.models[self.modelType]['apikey'], base_url=self.config.models[self.modelType]['baseURL']) as client:
                with client.messages.stream(model=self.modelName, max_tokens=4096, system=prompt[0][0]['content'], messages=prompt[0][1:], timeout=60, **extras) as stream:
                    for delta in stream.text_stream:
                        text += delta
                        if endchecker(text):
                            break
                        sentences = [x for x in sentences_split(text[currentPosition:])]
                        if 2 <= len(sentences) and '' != sentences[0].strip():
                            gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(sentences[0]) // 4)
                            proc(txt=sentences[0])
                            currentPosition += len(sentences[0])
        except anthropic.AuthenticationError as e:
            msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
            print('\n\n', msg)
            print('\n\nException:\n', str(e))
            os._exit(1)
        gasTank.Consume(resourceType='Anthropic/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def __init__(self, modelType: str, modelName: str, config):
    self.tokenizer = None
    self.modelType = modelType
    self.modelName = modelName
    self.config = config
    self.modelCfg = config.models[modelType]['modelList'][modelName]
    self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
    self.contextWindow = self.modelCfg['contextWindow']
    return

class AModelMistral:

    def __init__(self, modelType: str, modelName: str, config):
        self.tokenizer = None
        self.modelType = modelType
        self.modelName = modelName
        self.config = config
        self.modelCfg = config.models[modelType]['modelList'][modelName]
        self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
        self.contextWindow = self.modelCfg['contextWindow']
        return

    def Generate(self, prompt: tuple[list[dict[str, str]], int], proc: callable, endchecker: callable, temperature: float, gasTank) -> str:
        currentPosition = 0
        text = ''
        extras = {}
        extras.update(self.modelCfg.get('args', {}))
        extras.update({'temperature': temperature} if None != temperature else {})
        try:
            gasTank.Consume(resourceType='Mistral/InputTokens', amount=prompt[1])
            with Mistral(api_key=self.config.models[self.modelType]['apikey']) as client:
                for chunk in client.chat.stream(model=self.modelName, messages=prompt[0], timeout_ms=60000, **extras):
                    text += chunk.data.choices[0].delta.content or ''
                    if endchecker(text):
                        break
                    sentences = [x for x in sentences_split(text[currentPosition:])]
                    if 2 <= len(sentences) and '' != sentences[0].strip():
                        gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(sentences[0]) // 4)
                        proc(txt=sentences[0])
                        currentPosition += len(sentences[0])
        except models.sdkerror.SDKError as e:
            if 'Unauthorized' in e.body:
                msg = colored('The program encountered an authorization error. Please check your API key:', 'yellow') + colored(f'\n\n{self.modelType}: ', 'green') + colored(f"'{self.config.models[self.modelType]['apikey']}'\n\n", 'blue') + colored("If it's incorrect, append '--resetApiKey' to the command parameters you are using to restart ailice and reset the API key.", 'yellow')
                print('\n\n', msg)
                print('\n\nException:\n', str(e))
                os._exit(1)
            else:
                raise
        gasTank.Consume(resourceType='Mistral/OutputTokens', amount=len(text[currentPosition:]) // 4)
        proc(txt=text[currentPosition:])
        return text

def __init__(self, modelType: str, modelName: str, config):
    self.tokenizer = None
    self.modelType = modelType
    self.modelName = modelName
    self.config = config
    self.modelCfg = config.models[modelType]['modelList'][modelName]
    self.formatter = CreateFormatter(self.modelCfg['formatter'], tokenizer=self.tokenizer, systemAsUser=self.modelCfg['systemAsUser'])
    self.contextWindow = self.modelCfg['contextWindow']
    return

