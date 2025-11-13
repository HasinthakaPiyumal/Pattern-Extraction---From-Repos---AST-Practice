# Cluster 7

def InitServer():
    os.makedirs(f'{config.chatHistoryPath}/logs', exist_ok=True)
    handler = RotatingFileHandler(f'{config.chatHistoryPath}/logs/app.log', maxBytes=1000000, backupCount=5)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    logger.info(f'Flask app logger configured to write to {config.chatHistoryPath}/logs/app.log')
    return

def get_process_logger(process_name=None):
    if process_name is None:
        process_name = f'{multiprocessing.current_process().name}_{os.getpid()}'
    log_format = '%(asctime)s.%(msecs)03d|%(levelname)s|%(thread)d|%(threadName)s|%(name)s|%(filename)s:%(lineno)d|%(funcName)s|%(message)s'
    logger_name = f'ailice.{process_name}'
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    LOG_DIR = os.path.join(appdirs.user_log_dir('ailice', 'Steven Lu'), 'logs')
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, f'ailice_{process_name}.log')
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger

def GenerateCertificates(baseDir, name):
    keysDir = os.path.join(baseDir, name)
    os.makedirs(keysDir, exist_ok=True)
    publicFile, secretFile = zmq.auth.create_certificates(keysDir, name)
    return (publicFile, secretFile)

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

def CreateSocket(self):
    socket = self.context.socket(zmq.DEALER)
    socket.setsockopt(zmq.HEARTBEAT_IVL, 2000)
    socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 10000)
    socket.connect(self.WORKERS_ADDR)
    return socket

def makeClient(url, returnClass=False, clientPrivateKeyPath=None, serverPublicKeyPath=None, validateReturn=True, timeout=300 * 1000, retries=3):
    clientPrivateKeyPath = clientPrivateKeyPath or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates/client/client.key_secret')
    serverPublicKeyPath = serverPublicKeyPath or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certificates/server/server.key')
    enableSecurity = os.path.exists(serverPublicKeyPath) and os.path.exists(clientPrivateKeyPath)
    if enableSecurity:
        print('lightRPC client encryption ENABLED.')
        clientPublic, clientSecret = zmq.auth.load_certificate(clientPrivateKeyPath)
        serverPublic, _ = zmq.auth.load_certificate(serverPublicKeyPath)

    class RemoteGenerator:

        def __init__(self, client, generatorID):
            self.client = client
            self.generatorID = generatorID

        def __iter__(self):
            return self

        def __next__(self):
            ret = self.client.Send({'NEXT': '', 'clientID': self.client.clientID, 'generatorID': self.generatorID})
            if 'exception' in ret:
                raise ALightRPCException(ret['exception'])
            if ret['finished']:
                raise StopIteration
            return ret['ret']

    class GenesisRPCClientTemplate(object):

        def __init__(self):
            self.url = url
            self.context = context
            self.enableSecurity = enableSecurity
            self.timeout = timeout
            self.retries = retries
            if self.enableSecurity:
                self.clientPublic, self.clientSecret, self.serverPublic = (clientPublic, clientSecret, serverPublic)
            ret = self.Send({'CREATE': ''})
            if 'exception' in ret:
                raise ALightRPCException(ret['exception'])
            self.clientID = ret['clientID']
            return

        def Send(self, msg):
            for attempt in range(self.retries):
                try:
                    with self.context.socket(zmq.REQ) as socket:
                        if self.enableSecurity:
                            socket.setsockopt(zmq.CURVE_PUBLICKEY, self.clientPublic)
                            socket.setsockopt(zmq.CURVE_SECRETKEY, self.clientSecret)
                            socket.setsockopt(zmq.CURVE_SERVERKEY, self.serverPublic)
                        socket.setsockopt(zmq.CONNECT_TIMEOUT, 10000)
                        socket.setsockopt(zmq.HEARTBEAT_IVL, 2000)
                        socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 10000)
                        socket.setsockopt(zmq.RCVTIMEO, self.timeout)
                        socket.setsockopt(zmq.SNDTIMEO, self.timeout)
                        socket.connect(self.url)
                        SendMsg(socket, msg)
                        return ReceiveMsg(socket)
                except zmq.Again:
                    if attempt == self.retries - 1:
                        raise TimeoutError(f'RPC call timeout after {self.retries} retries')
                    continue
                except Exception as e:
                    if attempt == self.retries - 1:
                        raise
                    continue

        def RemoteCall(self, funcName, args, kwargs):
            ret = self.Send({'clientID': self.clientID, 'function': funcName, 'args': args, 'kwargs': kwargs})
            if 'exception' in ret:
                raise ALightRPCException(ret['exception'])
            if isinstance(ret['ret'], dict) and 'generatorID' in ret['ret']:
                return RemoteGenerator(self, ret['ret']['generatorID'])
            return ret['ret']

        @contextmanager
        def Timeout(self, timeoutTemp=-1):
            try:
                t = self.timeout
                self.timeout = timeoutTemp
                yield self
            finally:
                self.timeout = t
    with context.socket(zmq.REQ) as socket:
        if enableSecurity:
            socket.setsockopt(zmq.CURVE_PUBLICKEY, clientPublic)
            socket.setsockopt(zmq.CURVE_SECRETKEY, clientSecret)
            socket.setsockopt(zmq.CURVE_SERVERKEY, serverPublic)
        socket.setsockopt(zmq.CONNECT_TIMEOUT, 10000)
        socket.setsockopt(zmq.SNDTIMEO, 10000)
        socket.setsockopt(zmq.RCVTIMEO, 10000)
        socket.connect(url)
        SendMsg(socket, {'GET_META': ''})
        ret = ReceiveMsg(socket)
    for funcName, methodMeta in ret['META']['methods'].items():
        AddMethod(GenesisRPCClientTemplate, funcName, methodMeta)
    return validate_methods(GenesisRPCClientTemplate, None, validateReturn) if returnClass else validate_methods(GenesisRPCClientTemplate, None, validateReturn)()

class GenesisRPCClientTemplate(object):

    def __init__(self):
        self.url = url
        self.context = context
        self.enableSecurity = enableSecurity
        self.timeout = timeout
        self.retries = retries
        if self.enableSecurity:
            self.clientPublic, self.clientSecret, self.serverPublic = (clientPublic, clientSecret, serverPublic)
        ret = self.Send({'CREATE': ''})
        if 'exception' in ret:
            raise ALightRPCException(ret['exception'])
        self.clientID = ret['clientID']
        return

    def Send(self, msg):
        for attempt in range(self.retries):
            try:
                with self.context.socket(zmq.REQ) as socket:
                    if self.enableSecurity:
                        socket.setsockopt(zmq.CURVE_PUBLICKEY, self.clientPublic)
                        socket.setsockopt(zmq.CURVE_SECRETKEY, self.clientSecret)
                        socket.setsockopt(zmq.CURVE_SERVERKEY, self.serverPublic)
                    socket.setsockopt(zmq.CONNECT_TIMEOUT, 10000)
                    socket.setsockopt(zmq.HEARTBEAT_IVL, 2000)
                    socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 10000)
                    socket.setsockopt(zmq.RCVTIMEO, self.timeout)
                    socket.setsockopt(zmq.SNDTIMEO, self.timeout)
                    socket.connect(self.url)
                    SendMsg(socket, msg)
                    return ReceiveMsg(socket)
            except zmq.Again:
                if attempt == self.retries - 1:
                    raise TimeoutError(f'RPC call timeout after {self.retries} retries')
                continue
            except Exception as e:
                if attempt == self.retries - 1:
                    raise
                continue

    def RemoteCall(self, funcName, args, kwargs):
        ret = self.Send({'clientID': self.clientID, 'function': funcName, 'args': args, 'kwargs': kwargs})
        if 'exception' in ret:
            raise ALightRPCException(ret['exception'])
        if isinstance(ret['ret'], dict) and 'generatorID' in ret['ret']:
            return RemoteGenerator(self, ret['ret']['generatorID'])
        return ret['ret']

    @contextmanager
    def Timeout(self, timeoutTemp=-1):
        try:
            t = self.timeout
            self.timeout = timeoutTemp
            yield self
        finally:
            self.timeout = t

def Send(self, msg):
    for attempt in range(self.retries):
        try:
            with self.context.socket(zmq.REQ) as socket:
                if self.enableSecurity:
                    socket.setsockopt(zmq.CURVE_PUBLICKEY, self.clientPublic)
                    socket.setsockopt(zmq.CURVE_SECRETKEY, self.clientSecret)
                    socket.setsockopt(zmq.CURVE_SERVERKEY, self.serverPublic)
                socket.setsockopt(zmq.CONNECT_TIMEOUT, 10000)
                socket.setsockopt(zmq.HEARTBEAT_IVL, 2000)
                socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 10000)
                socket.setsockopt(zmq.RCVTIMEO, self.timeout)
                socket.setsockopt(zmq.SNDTIMEO, self.timeout)
                socket.connect(self.url)
                SendMsg(socket, msg)
                return ReceiveMsg(socket)
        except zmq.Again:
            if attempt == self.retries - 1:
                raise TimeoutError(f'RPC call timeout after {self.retries} retries')
            continue
        except Exception as e:
            if attempt == self.retries - 1:
                raise
            continue

def InitServer():
    os.makedirs(f'{config.chatHistoryPath}/logs', exist_ok=True)
    handler = RotatingFileHandler(f'{config.chatHistoryPath}/logs/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
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

def SwitchTone(self) -> str:
    self.rand_spk = self.model.sample_random_speaker()
    with open(self.toneFile, 'w') as f:
        f.write(self.rand_spk)
    return 'The new speaker tone has been created.'

