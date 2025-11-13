# Cluster 12

@app.route('/get_announcement', methods=['GET'])
def get_announcement():
    logger.debug('Announcement requested')
    return jsonify({'announcement': ''})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list_agent_type', methods=['GET'])
def list_agent_type():
    logger.debug('Agent type list requested')
    return jsonify(['main', 'researcher', 'search-engine', 'coder-proxy', 'coder', 'doc-reader', 'module-coder', 'chat'])

@app.route('/current_session', methods=['GET'])
def current_session():
    logger.debug('Current session requested')
    try:
        return jsonify(context.CurrentSession().Description())
    except AWExceptionSessionNotExist as e:
        return jsonify({})

@app.route('/stream', methods=['GET'])
def stream():
    logger.info(f'Message stream acquired')
    try:
        return Response(context.CurrentSession().MsgStream(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Access-Control-Allow-Origin': '*'})
    except AWExceptionSessionNotExist as e:
        return (jsonify({'error': 'Session not found'}), 404)

@app.route('/message', methods=['POST'])
def message():
    message = request.form.get('message', '')
    if 'files_for_perception[]' in request.files:
        message = f'{message}\n\n<!-- The following audio/video/image files are marked with extended markdown syntax for your analysis -->'
        files_for_perception = request.files.getlist('files_for_perception[]')
        for file in files_for_perception:
            if file and file.filename:
                file_path = context.CurrentSession().UploadFile(file.filename, file.read(), file.content_type)
                message = f'{message}\n\n![{file_path}]({file_path})'
    if 'files_for_processing[]' in request.files:
        message = f'{message}\n\n<!-- Here are other attached files. To make the agent actually read the file content (not just see the path), mark it with extended markdown syntax. Check file size first to avoid consuming too many tokens on large files. -->\n\nAttached files:'
        files_for_processing = request.files.getlist('files_for_processing[]')
        for file in files_for_processing:
            if file and file.filename:
                file_path = context.CurrentSession().UploadFile(file.filename, file.read(), file.content_type)
                message = f'{message}\n\ntype: {file.content_type}   length: {file.content_length}   path: {file_path}'
    logger.info(f'Chat message received')
    logger.debug(f'Message content: {message[:50]}{('...' if len(message) > 50 else '')}\nfiles_for_perception: {(len(files_for_perception) if 'files_for_perception' in locals() else 0)}\nfiles_for_processing: {(len(files_for_processing) if 'files_for_processing' in locals() else 0)}')
    context.CurrentSession().Message(message)
    return ('', 204)

@app.route('/new_chat')
def new_chat():
    session_name = context.NewSession()
    logger.info(f"New chat session '{session_name}' created")
    return jsonify(context.CurrentSession().Description())

@app.route('/load_history')
def load_history():
    session_name = request.args.get('name')
    logger.info(f"Loading chat history '{session_name}'")
    context.LoadSession(session_name)
    return jsonify(context.CurrentSession().Description())

@app.route('/get_history')
def get_history():
    session_name = request.args.get('name')
    logger.info(f"Getting chat history '{session_name}'")
    return jsonify(context.GetSession(session_name))

@app.route('/delete_history/<string:sessionName>', methods=['DELETE'])
def delete_history(sessionName):
    if context.DeleteSession(sessionName):
        logger.info(f"Chat history '{sessionName}' deleted")
        return ('', 204)
    else:
        logger.warning(f"Failed to delete chat history '{sessionName}': History not found")
        return (jsonify({'error': 'History item not found'}), 404)

@app.route('/list_histories')
def list_histories():
    logger.debug(f'Listing chat histories')
    return jsonify(context.ListSessions())

@app.route('/interrupt', methods=['POST'])
def interrupt():
    context.CurrentSession().Interrupt()
    logger.info(f'Chat interrupted by user')
    return jsonify({'status': 'interrupted'})

@app.route('/sendmsg', methods=['POST'])
def sendmsg():
    message = request.form.get('message', '')
    if 'files_for_perception[]' in request.files:
        message = f'{message}\n\n<!-- The following audio/video/image files are marked with extended markdown syntax for your analysis -->'
        files_for_perception = request.files.getlist('files_for_perception[]')
        for file in files_for_perception:
            if file and file.filename:
                file_path = context.CurrentSession().UploadFile(file.filename, file.read(), file.content_type)
                message = f'{message}\n\n![{file_path}]({file_path})'
    if 'files_for_processing[]' in request.files:
        message = f'{message}\n\n<!-- Here are other attached files. To make the agent actually read the file content (not just see the path), mark it with extended markdown syntax. Check file size first to avoid consuming too many tokens on large files. -->\n\nAttached files:'
        files_for_processing = request.files.getlist('files_for_processing[]')
        for file in files_for_processing:
            if file and file.filename:
                file_path = context.CurrentSession().UploadFile(file.filename, file.read(), file.content_type)
                message = f'{message}\n\ntype: {file.content_type}   length: {file.content_length}   path: {file_path}'
    context.CurrentSession().SendMsg(message)
    logger.info(f'Message sent')
    logger.debug(f'Message content: {message[:50]}{('...' if len(message) > 50 else '')}\nfiles_for_perception: {(len(files_for_perception) if 'files_for_perception' in locals() else 0)}\nfiles_for_processing: {(len(files_for_processing) if 'files_for_processing' in locals() else 0)}')
    return jsonify({'status': 'message sent', 'message': message})

@app.route('/get_settings', methods=['POST'])
def get_settings():
    patches = request.get_json().get('patches')
    logger.debug(f'Settings requested')
    return jsonify({'schema': context.Setup(patches, apply=False)})

@app.route('/update_settings', methods=['POST'])
def update_settings():
    patches = request.get_json().get('patches')
    logger.info(f'Settings updated')
    return jsonify({'schema': context.Setup(patches, apply=True)})

@app.route('/proxy', methods=['GET', 'HEAD'])
def proxy():
    href = unquote(request.args.get('href'))
    logger.debug(f'Proxy request for {href}')
    res = context.CurrentSession().Proxy(href, request.method)
    meta = next(res)
    if 'variable' == meta['type']:
        with tempfile.NamedTemporaryFile(mode='bw', delete=True) as temp:
            temp.write(meta['data'].data)
            temp.flush()
            if request.method == 'HEAD':
                response = make_response('')
                response.headers['Content-Type'] = {'AImage': 'image/jpeg', 'AVideo': 'video/mp4'}[type(meta['data']).__name__]
            else:
                response = send_file(os.path.abspath(temp.name))
    else:
        try:
            responseInfo = meta['responseInfo']

            def gen():
                yield from res
            contentType = responseInfo['headers'].get('Content-Type', '')
            response = Response(gen(), status=responseInfo['status_code'], content_type=contentType)
            for key, value in responseInfo['headers'].items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
            if contentType.lower() in ('image/svg+xml', 'application/svg+xml'):
                response.headers['Content-Type'] = 'image/svg+xml'
                response.headers['Content-Disposition'] = 'inline'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = '*'
        except requests.exceptions.RequestException as e:
            error_msg = f'Error fetching the URL: {e}'
            logger.error(error_msg)
            return (error_msg, 500)
    isLocalFile = os.path.exists(href) if href.startswith('/') or href.startswith('file://') or ':/' in href else False
    if isLocalFile:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        response.headers['Cache-Control'] = 'public, max-age=60'
    return response

def get_all_model_options(models):
    model_options = []
    for provider_name, provider in models.items():
        if provider.get('apikey', None) in ['', None]:
            continue
        for model_name in provider['modelList'].keys():
            model_id = f'{provider_name}:{model_name}'
            model_options.append({'value': model_id, 'label': model_id})
    return sorted(model_options, key=lambda x: x['value'])

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

def ConvertVideoFormat(bytesSrc, format):
    videoSrc = av.open(io.BytesIO(bytesSrc))
    if format == videoSrc.format:
        return bytesSrc.getvalue()
    bytesDst = io.BytesIO()
    videoDst = av.open(bytesDst, mode='w', format=format)
    streamSrc = videoSrc.streams.video[0]
    streamDst = videoDst.add_stream('libx264', rate=streamSrc.average_rate)
    streamDst.width = streamSrc.width
    streamDst.height = streamSrc.height
    streamDst.pix_fmt = 'yuv420p'
    for frame in videoSrc.decode(video=0):
        for packet in streamDst.encode(frame):
            videoDst.mux(packet)
    for packet in streamDst.encode():
        videoDst.mux(packet)
    videoSrc.close()
    videoDst.close()
    bytesDst.seek(0)
    return bytesDst.getvalue()

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

def Convert(self, format: str):
    if format == self.format or not self.data:
        return self
    imageBytes = io.BytesIO()
    image = Image.open(io.BytesIO(self.data))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image.save(imageBytes, format=format)
    return AImage(data=imageBytes.getvalue())

class AImageLocation(BaseModel):
    urlOrPath: str

    def IsURL(self, ident: str) -> bool:
        return urlparse(ident).scheme != ''

    def GetImage(self, ident: str, proxy=None) -> Image:
        if proxy is None:
            if self.IsURL(ident):
                response = requests.get(ident)
                imageBytes = io.BytesIO(response.content)
                return Image.open(imageBytes)
            else:
                return Image.open(ident)
        else:
            response = proxy(ident, 'GET')
            _ = next(response)
            imageBytes = io.BytesIO()
            for chunk in response:
                imageBytes.write(chunk)
            return Image.open(imageBytes)

    @classmethod
    def FromJson(cls, data):
        return cls(urlOrPath=data['urlOrPath'])

    def ToJson(self):
        return {'type': 'AImageLocation', 'urlOrPath': self.urlOrPath}

    def Standardize(self, proxy=None):
        image = self.GetImage(self.urlOrPath, proxy)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        imageByte = io.BytesIO()
        image.save(imageByte, format='JPEG')
        return AImage(data=imageByte.getvalue())

def IsURL(self, ident: str) -> bool:
    return urlparse(ident).scheme != ''

def GetImage(self, ident: str, proxy=None) -> Image:
    if proxy is None:
        if self.IsURL(ident):
            response = requests.get(ident)
            imageBytes = io.BytesIO(response.content)
            return Image.open(imageBytes)
        else:
            return Image.open(ident)
    else:
        response = proxy(ident, 'GET')
        _ = next(response)
        imageBytes = io.BytesIO()
        for chunk in response:
            imageBytes.write(chunk)
        return Image.open(imageBytes)

def Standardize(self, proxy=None):
    image = self.GetImage(self.urlOrPath, proxy)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    imageByte = io.BytesIO()
    image.save(imageByte, format='JPEG')
    return AImage(data=imageByte.getvalue())

class AVideo(BaseModel):
    data: Optional[bytes]
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None

    def __init__(self, **params):
        super().__init__(**params)
        if self.data and (not all([self.format, self.width, self.height, self.fps])):
            meta = self.GetMeta()
            self.format = meta['format']
            self.width = meta['width']
            self.height = meta['height']
            self.fps = meta['fps']
        return

    def GetMeta(self):
        ret = {'width': 0, 'height': 0, 'fps': 0, 'format': None}
        if self.data:
            video = av.open(io.BytesIO(self.data))
            stream = next((s for s in video.streams if s.type == 'video'), None)
            if stream is not None:
                ret = {'width': stream.codec_context.width, 'height': stream.codec_context.height, 'fps': stream.average_rate, 'format': video.format}
            video.close()
        return ret

    def __str__(self) -> str:
        return f'< AVideo object in {self.format} format. >'

    @classmethod
    def FromJson(cls, data):
        return cls(data=base64.b64decode(data['data'].encode('utf-8')))

    def ToJson(self):
        return {'type': 'AVideo', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

    def Standardize(self):
        return AVideo(data=ConvertVideoFormat(self.data, 'mp4')) if self.data else self

def GetMeta(self):
    ret = {'width': 0, 'height': 0, 'fps': 0, 'format': None}
    if self.data:
        video = av.open(io.BytesIO(self.data))
        stream = next((s for s in video.streams if s.type == 'video'), None)
        if stream is not None:
            ret = {'width': stream.codec_context.width, 'height': stream.codec_context.height, 'fps': stream.average_rate, 'format': video.format}
        video.close()
    return ret

class AVideoLocation(BaseModel):
    urlOrPath: str

    def IsURL(self, ident: str) -> bool:
        return urlparse(ident).scheme != ''

    def GetVideo(self, ident: str, proxy=None):
        if proxy is None:
            if self.IsURL(ident):
                response = requests.get(ident)
                videoBytes = io.BytesIO(response.content)
                return videoBytes.getvalue()
            else:
                with open(ident, 'rb') as f:
                    videoBytes = io.BytesIO(f.read())
                    return videoBytes.getvalue()
        else:
            response = proxy(ident, 'GET')
            _ = next(response)
            videoBytes = io.BytesIO()
            for chunk in response:
                videoBytes.write(chunk)
            return videoBytes.getvalue()

    @classmethod
    def FromJson(cls, data):
        return cls(urlOrPath=data['urlOrPath'])

    def ToJson(self):
        return {'type': 'AVideoLocation', 'urlOrPath': self.urlOrPath}

    def Standardize(self, proxy=None):
        return AVideo(data=ConvertVideoFormat(self.GetVideo(self.urlOrPath, proxy), 'mp4'))

def IsURL(self, ident: str) -> bool:
    return urlparse(ident).scheme != ''

def GetVideo(self, ident: str, proxy=None):
    if proxy is None:
        if self.IsURL(ident):
            response = requests.get(ident)
            videoBytes = io.BytesIO(response.content)
            return videoBytes.getvalue()
        else:
            with open(ident, 'rb') as f:
                videoBytes = io.BytesIO(f.read())
                return videoBytes.getvalue()
    else:
        response = proxy(ident, 'GET')
        _ = next(response)
        videoBytes = io.BytesIO()
        for chunk in response:
            videoBytes.write(chunk)
        return videoBytes.getvalue()

@app.route('/')
def index():
    with lock:
        return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    with lock:
        message = request.get_json().get('message', '')
        return Response(generate_response(message), mimetype='text/event-stream')

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    with lock:
        if 'audio' not in request.files:
            return (jsonify({'error': 'No audio file provided'}), 400)
        audio = request.files['audio']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio.filename))
        audio.save(filepath)
        if config.speechOn:
            audio_data, sample_rate = librosa.load(filepath)
            message = speech.Speech2Text(audio_data.tolist(), sample_rate)
        else:
            message = f'![audio]({str(filepath)})'
        return Response(generate_response(f'{message}'), mimetype='text/event-stream')

@app.route('/upload_image', methods=['POST'])
def upload_image():
    with lock:
        if 'image' not in request.files:
            return (jsonify({'error': 'No image file provided'}), 400)
        image = request.files['image']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename))
        image.save(filepath)
        return Response(generate_response(f'![image]({str(filepath)})'), mimetype='text/event-stream')

@app.route('/new_chat')
def new_chat():
    with lock:
        sessionName = 'ailice_' + str(int(time.time()))
        LoadSession(sessionName=sessionName)
        return jsonify({'sessionName': sessionName})

@app.route('/load_history')
def load_history():
    with lock:
        sessionName = request.args.get('name')
        needLoading = sessionName != currentSession
        if needLoading:
            LoadSession(sessionName=sessionName)
        historyPath = os.path.join(config.chatHistoryPath, sessionName, 'ailice_history.json')
        if os.path.exists(historyPath):
            with open(historyPath, 'r') as f:
                data = json.load(f)
                conversations = [(f'{conv['role']}_{data['name']}', conv['msg']) for conv in data['conversation']]
        else:
            conversations = []
        return jsonify(conversations)

@app.route('/interrupt', methods=['POST'])
def interrupt():
    global context
    context[currentSession]['messenger'].Lock()
    return jsonify({'status': 'interrupted'})

@app.route('/sendmsg', methods=['POST'])
def sendmsg():
    global context
    msg = request.get_json().get('message', '')
    context[currentSession]['messenger'].Put(msg)
    context[currentSession]['messenger'].Unlock()
    return jsonify({'status': 'message sent', 'message': msg})

@app.route('/proxy', methods=['GET', 'HEAD'])
def proxy():
    href = unquote(request.args.get('href'))
    var = context[currentSession]['processor'].interpreter.env.get(href, None)
    if var and type(var).__name__ in ['AImage', 'AVideo']:
        with tempfile.NamedTemporaryFile(mode='bw', delete=True) as temp:
            temp.write(var.data)
            temp.flush()
            if request.method == 'HEAD':
                response = make_response('')
                response.headers['Content-Type'] = {'AImage': 'image/jpeg', 'AVideo': 'video/mp4'}[type(var).__name__]
            else:
                response = send_file(os.path.abspath(temp.name))
    else:
        computer = context[currentSession]['processor'].services.GetClient(config.services['computer']['addr'])
        try:
            r = computer.Proxy(href, request.method)
            responseInfo = next(r)

            def gen():
                yield from r
            contentType = responseInfo['headers'].get('Content-Type', '')
            response = Response(gen(), status=responseInfo['status_code'], content_type=contentType)
            for key, value in responseInfo['headers'].items():
                if key.lower() not in ('content-encoding', 'content-length', 'transfer-encoding', 'connection'):
                    response.headers[key] = value
            if contentType.lower() in ('image/svg+xml', 'application/svg+xml'):
                response.headers['Content-Type'] = 'image/svg+xml'
                response.headers['Content-Disposition'] = 'inline'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = '*'
        except requests.exceptions.RequestException as e:
            return (f'Error fetching the URL: {e}', 500)
    isLocalFile = os.path.exists(href) if href.startswith('/') or href.startswith('file://') or ':/' in href else False
    if isLocalFile:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        response.headers['Cache-Control'] = 'public, max-age=60'
    return response

class AStorageWeaviate:

    def __init__(self, clusterURL, apiKey, oaiKey):
        self.clusterURL = clusterURL
        self.apiKey = apiKey
        self.oaiKey = oaiKey
        self.client = None
        return

    def __del__(self):
        self.client.close()
        return

    def ModuleInfo(self):
        return {'NAME': 'storage', 'ACTIONS': {}}

    def Open(self, directory: str) -> str:
        try:
            self.client = weaviate.connect_to_wcs(cluster_url=self.clusterURL, auth_credentials=weaviate.auth.AuthApiKey(self.apiKey), headers={'X-OpenAI-Api-Key': self.oaiKey})
        except Exception as e:
            print(f'Open() EXCEPTION. e: {str(e)}')
            return f'Open() EXCEPTION. e: {str(e)}'

    def Store(self, collection: str, content: Union[str, list[str]]) -> bool:
        try:
            print('collection: ', collection, '. store: ', content)
            if not self.client.collections.exists(collection):
                print(f'create a new collection: {collection}')
                self.client.collections.create(name=collection, vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(), generative_config=wvc.config.Configure.Generative.openai())
            self.client.collections.get(collection).data.insert_many([{'text': content}] if type(content) != list else [{'text': t} for t in content])
        except Exception as e:
            print('store() EXCEPTION: ', e)
            return False
        return True

    def Query(self, collection: str, clue: str, num_results: int=1) -> list[tuple[str, float]]:
        try:
            response = self.client.collections.get(collection).query.near_text(query=clue, limit=num_results)
            ret = None
            if 0 < len(response.objects):
                ret = [(r.properties['text'], r.metadata.distance) for r in response.objects]
            print('query: ', collection, '.', clue, ' -> ', ret)
            return ret
        except Exception as e:
            print('query() EXCEPTION: ', e)
            return []

    def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
        return self.Query(collection=collection, clue=query, num_results=num_results)

def __del__(self):
    self.client.close()
    return

class AComputer:

    def __init__(self):
        self.lock = threading.Lock()
        if 0 == len(requirements):
            self.clicks = {'click': pyautogui.click, 'double-click': pyautogui.doubleClick, 'right-click': pyautogui.rightClick, 'middle': pyautogui.middleClick}
            self.reader = easyocr.Reader(['en'])
        return

    def ModuleInfo(self):
        return {'NAME': 'computer', 'ACTIONS': {'SCREENSHOT': {'func': 'ScreenShot', 'prompt': 'Take a screenshot of the current screen.', 'type': 'primary'}, 'LOCATEANDCLICK': {'func': 'LocateAndClick', 'prompt': "Locate the control containing a piece of text on the screenshot and click on it. clickType is a string, and its value can only be one of 'click', 'double-click', 'right-click' or 'middle'.", 'type': 'primary'}, 'LOCATEANDSCROLL': {'func': 'LocateAndScroll', 'prompt': 'Move to the position marked by the text and scroll the mouse wheel.', 'type': 'primary'}, 'TYPEWRITE': {'func': 'TypeWrite', 'prompt': 'Simulate keyboard input for the string. Please ensure that the focus has been moved to the location where input is expected.', 'type': 'primary'}, 'READ-IMAGE': {'func': 'ReadImage', 'prompt': 'Read the content of an image file into a variable.', 'type': 'primary'}, 'WRITE-IMAGE': {'func': 'WriteImage', 'prompt': 'Write a variable of image type into a file.', 'type': 'primary'}}}

    def Locate(self, txt: str):
        image = ImageGrab.grab()
        results = self.reader.readtext(numpy.array(image.convert('L')), slope_ths=0.0, ycenter_ths=0.0, width_ths=0.0)
        for detection in results:
            bbox = detection[0]
            text = detection[1]
            if txt in text:
                x, y = (int((bbox[0][0] + bbox[2][0]) * 0.5), int((bbox[0][1] + bbox[2][1]) * 0.5))
                return (x, y, text)
        return None

    def ScreenShot(self) -> AImage:
        with self.lock:
            imageByte = io.BytesIO()
            ImageGrab.grab().save(imageByte, format='JPEG')
            return AImage(data=imageByte.getvalue())

    def LocateAndClick(self, txt: str, clickType: str) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            if clickType not in self.clicks:
                return f"LOCATEANDCLICK ERROR. clickType: {clickType} can only be one of 'click', 'double-click', 'right-click' or 'middle'."
            ret = self.Locate(txt)
            if None != ret:
                x, y, text = ret
                pyautogui.moveTo(x, y, duration=0.5)
                self.clicks[clickType]()
                return f"'''{text}''' at {x},{y} is clicked."
            else:
                return f"'''{txt}''' not found. It may be because the text has been segmented into different boxes by the OCR software. Please try a shorter and distinctive substring."

    def LocateAndScroll(self, txt: str, clicks: float) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            ret = self.Locate(txt)
            if None != ret:
                x, y, text = ret
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.scroll(clicks)
                return f'The mouse wheel has scrolled {clicks} times.'
            else:
                return f"'''{txt}''' not found. It may be because the text has been segmented into different boxes by the OCR software. Please try a shorter and distinctive substring."

    def TypeWrite(self, txt: str) -> str:
        with self.lock:
            if 0 != len(requirements):
                return f'python package(s) {[x for x in requirements]} not found. Please install it before using this feature.'
            pyautogui.typewrite(txt)
            return f"'''{txt}''' the string has already been typed."

    def ReadImage(self, path: str) -> AImage:
        try:
            return AImageLocation(urlOrPath=path).Standardize()
        except Exception as e:
            print('ReadImage() excetption: ', e)
        return AImage(data=None)

    def WriteImage(self, image: AImage, path: str) -> str:
        try:
            Image.open(io.BytesIO(image.data)).save(path)
            return f'The image has been written to {path}.'
        except Exception as e:
            print('WriteImage() excetption: ', e)
            return f'WriteImage() excetption: {str(e)}'
        return

    def WriteFile(self, data: bytes, path: str) -> str:
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, 'wb') as file:
                file.write(data)
            return f'The file has been written to {path}.'
        except Exception as e:
            print('WriteFile() excetption: ', e)
            return f'WriteFile() excetption: {str(e)}'
        return

    def Proxy(self, href: str, method: str, headers: dict={}, body: dict={}, params: dict={}) -> typing.Generator:
        if os.path.exists(href):
            filePath = os.path.abspath(href)
            fileSize = os.path.getsize(filePath)
            fileName = os.path.basename(filePath)
            contentType, encoding = mimetypes.guess_type(filePath)
            if contentType is None:
                contentType = 'application/octet-stream'
            startByte = 0
            endByte = fileSize - 1
            statusCode = 200
            if headers and 'Range' in headers:
                rangeHeader = headers['Range']
                rangeMatch = re.match('bytes=(\\d+)-(\\d*)', rangeHeader)
                if rangeMatch:
                    startByte = int(rangeMatch.group(1))
                    if rangeMatch.group(2):
                        endByte = min(int(rangeMatch.group(2)), fileSize - 1)
                    statusCode = 206
            responseHeaders = {'Content-Type': contentType, 'Content-Length': str(endByte - startByte + 1), 'Accept-Ranges': 'bytes', 'Content-Disposition': f"""inline; filename="{urllib.parse.quote(fileName)}"; filename*=UTF-8''{urllib.parse.quote(fileName)}""", 'Last-Modified': datetime.datetime.fromtimestamp(os.stat(filePath).st_mtime, tz=datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}
            if statusCode == 206:
                responseHeaders['Content-Range'] = f'bytes {startByte}-{endByte}/{fileSize}'
            responseInfo = {'status_code': statusCode, 'headers': responseHeaders}
            yield responseInfo
            if method.upper() != 'HEAD':

                def content_generator():
                    with open(filePath, 'rb') as file:
                        if startByte > 0:
                            file.seek(startByte)
                        bytesToRead = endByte - startByte + 1
                        bytesRead = 0
                        while bytesRead < bytesToRead:
                            chunkSize = min(262144, bytesToRead - bytesRead)
                            chunk = file.read(chunkSize)
                            if not chunk:
                                break
                            bytesRead += len(chunk)
                            yield chunk
                yield from content_generator()
        else:
            req = requests.request(method=method, url=href, headers=headers, data=body, params=params, stream=True)
            responseInfo = {'status_code': req.status_code, 'headers': dict(req.headers)}
            yield responseInfo
            if method.upper() != 'HEAD':

                def content_generator():
                    try:
                        for chunk in req.iter_content(chunk_size=262144):
                            if chunk:
                                yield chunk
                    finally:
                        req.close()
                yield from content_generator()

def Locate(self, txt: str):
    image = ImageGrab.grab()
    results = self.reader.readtext(numpy.array(image.convert('L')), slope_ths=0.0, ycenter_ths=0.0, width_ths=0.0)
    for detection in results:
        bbox = detection[0]
        text = detection[1]
        if txt in text:
            x, y = (int((bbox[0][0] + bbox[2][0]) * 0.5), int((bbox[0][1] + bbox[2][1]) * 0.5))
            return (x, y, text)
    return None

def ScreenShot(self) -> AImage:
    with self.lock:
        imageByte = io.BytesIO()
        ImageGrab.grab().save(imageByte, format='JPEG')
        return AImage(data=imageByte.getvalue())

def ReadImage(self, path: str) -> AImage:
    try:
        return AImageLocation(urlOrPath=path).Standardize()
    except Exception as e:
        print('ReadImage() excetption: ', e)
    return AImage(data=None)

def WriteImage(self, image: AImage, path: str) -> str:
    try:
        Image.open(io.BytesIO(image.data)).save(path)
        return f'The image has been written to {path}.'
    except Exception as e:
        print('WriteImage() excetption: ', e)
        return f'WriteImage() excetption: {str(e)}'
    return

def content_generator():
    try:
        for chunk in req.iter_content(chunk_size=262144):
            if chunk:
                yield chunk
    finally:
        req.close()

class ATextBrowser(AScrollablePage):

    def __init__(self, functions: dict[str, str]):
        super(ATextBrowser, self).__init__(functions=functions)
        self.path = None
        self.prompt = '\nThe document is in editable mode. You can edit the content using the following functions:\n#Replace the matching content within the current page. When regexMode==True, you can use regular expressions to represent the pattern and replacement. This function is a simple wrapper for re.sub() in this mode. When regexMode==False, pattern and replacement represent literal strings. Use triple quotes to represent pattern and replacement.\nREPLACE<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Replace all matching content in the entire document. The parameters are the same as REPLACE.\nREPLACE-ALL<!|pattern: str, replacement: str, regexMode: bool, session: str|!> -> str\n#Save the modified content to a file. If the dstPath parameter is an empty string, save it to the original file.\nSAVETO<!|dstPath: str, session: str|!> -> str\n\nExample:\n!REPLACE<!|"""Hello World!""", """Hello Python!""", False, "session_example"|!>\n!SAVETO<!|"", "session_example"|!>\n'
        return

    def Browse(self, url: str) -> str:
        parsedURL = urlparse(url)
        if parsedURL.scheme in ['file', ''] and '' == parsedURL.netloc:
            try:
                with open(parsedURL.path, 'r', encoding='utf-8') as f:
                    self.LoadPage(f.read(), 'TOP')
                    self.path = None
                    return self()
            except Exception as e:
                self.LoadPage(f'Exception: {str(e)}.', 'BOTTOM')
                return self()
        else:
            response = requests.get(url)
            if response.status_code != 200:
                return f'Error: can not download text file. HTTP err code: {response.status_code}'
            if 'text' not in response.headers.get('Content-Type', ''):
                return 'The url returned non-text content and cannot be browsed.'
            self.LoadPage(response.content, 'TOP')
            return self()

    def Edit(self, path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.LoadPage(f.read(), 'TOP')
                self.path = path
                return self() + self.prompt
        except Exception as e:
            self.LoadPage(f'Exception: {str(e)}.', 'BOTTOM')
            return self()

    def Replace(self, pattern: str, replacement: str, regexMode: bool) -> str:
        if regexMode:
            textNew = re.sub(pattern, replacement, self(prompt=False))
        else:
            textNew = self(prompt=False).replace(pattern, replacement)
        msg = 'Pattern NOT FOUND in current visible page. Please check: 1. If the pattern you entered is correct, such as whether you forgot to properly escape characters within the quotes. 2. Ensure that the content to be replaced is within the currently visible page (you can use the SEARCHDOWN/SEARCHUP to locate it, or directly use the REPLACE-ALL to replace all matching content).\n\n'
        if self(prompt=False) != textNew or '' == pattern:
            msg = 'The matching contents has been replaced. \n\n'
        self.ReplaceText(textNew, replaceAll=False)
        return msg + self() + self.prompt

    def ReplaceAll(self, pattern: str, replacement: str, regexMode: bool) -> str:
        if regexMode:
            textNew = re.sub(pattern, replacement, self.txt)
        else:
            textNew = self.txt.replace(pattern, replacement)
        msg = 'Pattern NOT FOUND in the entire document. Please check if the pattern you entered is correct, such as whether you forgot to properly escape characters within the quotes.\n\n'
        if self.txt != textNew or '' == pattern:
            msg = 'The matching contents has been replaced. \n\n'
        self.ReplaceText(textNew, replaceAll=True)
        return msg + self() + self.prompt

    def SaveTo(self, dstPath: str) -> str:
        try:
            dstPath = self.path if dstPath.strip() == '' and self.path != None else dstPath
            d = os.path.dirname(dstPath)
            if d.strip() != '':
                os.makedirs(d, exist_ok=True)
            with open(dstPath, 'w') as f:
                f.write(self.txt)
            return f'File {dstPath} saved.'
        except Exception as e:
            return f'Failed to save file {dstPath}, Exception: {str(e)}'

    def GetFullText(self) -> str:
        return self.txt if self.txt != None else ''

    def ScrollDown(self) -> str:
        return super(ATextBrowser, self).ScrollDown() + (self.prompt if self.path else '')

    def ScrollUp(self) -> str:
        return super(ATextBrowser, self).ScrollUp() + (self.prompt if self.path else '')

    def SearchDown(self, query: str) -> str:
        return super(ATextBrowser, self).SearchDown(query) + (self.prompt if self.path else '')

    def SearchUp(self, query: str) -> str:
        return super(ATextBrowser, self).SearchUp(query) + (self.prompt if self.path else '')

    def Destroy(self):
        return

def Browse(self, url: str) -> str:
    parsedURL = urlparse(url)
    if parsedURL.scheme in ['file', ''] and '' == parsedURL.netloc:
        try:
            with open(parsedURL.path, 'r', encoding='utf-8') as f:
                self.LoadPage(f.read(), 'TOP')
                self.path = None
                return self()
        except Exception as e:
            self.LoadPage(f'Exception: {str(e)}.', 'BOTTOM')
            return self()
    else:
        response = requests.get(url)
        if response.status_code != 200:
            return f'Error: can not download text file. HTTP err code: {response.status_code}'
        if 'text' not in response.headers.get('Content-Type', ''):
            return 'The url returned non-text content and cannot be browsed.'
        self.LoadPage(response.content, 'TOP')
        return self()

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

def ToHttps(self, url: str) -> str:
    if not urlparse(url).scheme:
        url = 'https://' + url
    return url

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

class AFormatterGPTVision:

    def __init__(self, tokenizer=None, systemAsUser=False):
        self.systemAsUser = systemAsUser
        return

    def ProcessAttachements(self, a):
        if 'image' == a['type']:
            return [{'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{a['content'].ToJson()['data']}'}}]
        elif 'video' == a['type']:
            numFrames = 10
            video = av.open(io.BytesIO(a['content'].data))
            frameIndices = [int(i * video.streams.video[0].frames / (numFrames - 1)) for i in range(numFrames)]
            ret = []
            for index in frameIndices:
                video.seek(index)
                frame = next(video.decode(video=0)).to_image()
                bytesDst = io.BytesIO()
                frame.save(bytesDst, format='JPEG')
                image = AImage(data=bytesDst.getvalue())
                ret.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image.Standardize().ToJson()['data']}'}})
            video.close()
            return ret

    def BuildMsg(self, role: str, msg: str, attachments: list):
        roleMap = {'SYSTEM': 'system' if not self.systemAsUser else 'user', 'USER': 'user', 'ASSISTANT': 'assistant'}
        return {'role': roleMap[role], 'content': [{'type': 'text', 'text': msg}] + sum([self.ProcessAttachements(a) for a in attachments if a['type'] in ['image', 'video']], [])}

    def __call__(self, prompt0, conversations, encode=True, assistTag=True):
        ret = [{'role': 'system', 'content': [{'type': 'text', 'text': prompt0}]}] + [self.BuildMsg(c['role'], c['msg'], c['attachments']) for c in conversations]
        return (ret, TokenEstimatorOAI(conversations))

def ProcessAttachements(self, a):
    if 'image' == a['type']:
        return [{'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{a['content'].ToJson()['data']}'}}]
    elif 'video' == a['type']:
        numFrames = 10
        video = av.open(io.BytesIO(a['content'].data))
        frameIndices = [int(i * video.streams.video[0].frames / (numFrames - 1)) for i in range(numFrames)]
        ret = []
        for index in frameIndices:
            video.seek(index)
            frame = next(video.decode(video=0)).to_image()
            bytesDst = io.BytesIO()
            frame.save(bytesDst, format='JPEG')
            image = AImage(data=bytesDst.getvalue())
            ret.append({'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image.Standardize().ToJson()['data']}'}})
        video.close()
        return ret

