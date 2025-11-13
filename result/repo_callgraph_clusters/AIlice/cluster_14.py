# Cluster 14

def FindRecords(prompt: str, selector, num: int, storage, collection) -> list:
    selector = (lambda x: True) if None == selector else selector
    res = []
    l = num
    while num < 0 or len(res) < num:
        l = l * 2
        rs = [json.loads(r) for r, _ in storage.Query(collection=collection, clue=prompt, num_results=l)]
        res = [r for r in rs if selector(r)]
        if num < 0 or len(rs) < l:
            break
    return res[:num] if num > 0 else res

class PatchOperation(BaseModel):
    op: Literal['replace', 'add', 'remove'] = Field(description='patch operation type.')
    path: List[Union[str, int]] = Field(description='target path represented in a list.')
    value: Optional[Any] = Field(None, description="new value. optional for 'remove' op.")

    @field_validator('path')
    @classmethod
    def validate_path_not_empty(cls, path: List[Union[str, int]]) -> List[Union[str, int]]:
        if not path:
            raise ValueError('The patch path should not be empty.')
        return path

    @model_validator(mode='after')
    def validate_value_for_operation(self) -> 'PatchOperation':
        if self.op in ['replace', 'add'] and self.value is None:
            raise ValueError(f"'{self.op}'The operation requires the 'value' field to be provided.")
        return self

@field_validator('path')
@classmethod
def validate_path_not_empty(cls, path: List[Union[str, int]]) -> List[Union[str, int]]:
    if not path:
        raise ValueError('The patch path should not be empty.')
    return path

@model_validator(mode='after')
def validate_value_for_operation(self) -> 'PatchOperation':
    if self.op in ['replace', 'add'] and self.value is None:
        raise ValueError(f"'{self.op}'The operation requires the 'value' field to be provided.")
    return self

def match_key(key, pattern):
    if isinstance(key, str) and isinstance(pattern, str):
        return key == pattern or '*' == pattern
    if isinstance(key, int) and isinstance(pattern, int):
        return key == pattern or -1 == pattern
    if isinstance(pattern, list):
        return any([match_key(key, p) for p in pattern])
    else:
        raise ValueError(f'Invalid type in path: {key}')

def check_path(path: List[Union[str, int]], allowed_path: List[Union[str, int]]) -> bool:

    def match_key(key, pattern):
        if isinstance(key, str) and isinstance(pattern, str):
            return key == pattern or '*' == pattern
        if isinstance(key, int) and isinstance(pattern, int):
            return key == pattern or -1 == pattern
        if isinstance(pattern, list):
            return any([match_key(key, p) for p in pattern])
        else:
            raise ValueError(f'Invalid type in path: {key}')
    if not match_key(path[0], allowed_path[0]):
        return False
    if len(allowed_path) == 1:
        return True
    if len(path) == 1 and len(allowed_path) > 1:
        return False
    return check_path(path[1:], allowed_path[1:])

class AiliceWebProviderConfig(BaseModel):
    modelWrapper: str
    apikey: Optional[str] = None
    baseURL: Optional[Union[AnyUrl, str]] = None
    modelList: dict[str, AiliceModelConfig]

    @field_validator('baseURL')
    def validate_base_url(cls, v):
        if v == '':
            return v
        return v

@field_validator('baseURL')
def validate_base_url(cls, v):
    if v == '':
        return v
    return v

def ReceiveMsg(conn):
    return json.loads(conn.recv().decode('utf-8'), cls=AJSONDecoder)

def validate_methods(cls, methodList=None, validateReturn=True):
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not name.startswith('_') and (methodList is None or name in methodList):
            setattr(cls, name, validate_call(method, validate_return=validateReturn and (not inspect.isgeneratorfunction(method))))
    return cls

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

def AddMethod(kls, methodName, methodMeta):
    signature = methodMeta['signature']
    is_generator = methodMeta['is_generator']
    newSignature = SignatureFromString(signature)

    def methodTemplate(self, *args, **kwargs):
        return self.RemoteCall(methodName, args, kwargs)
    methodTemplate.__is_generator__ = is_generator
    methodTemplate.__annotations__ = AnnotationsFromSignature(newSignature)
    methodTemplate.__signature__ = newSignature
    setattr(kls, methodName, methodTemplate)

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

def RemoteCall(self, funcName, args, kwargs):
    ret = self.Send({'clientID': self.clientID, 'function': funcName, 'args': args, 'kwargs': kwargs})
    if 'exception' in ret:
        raise ALightRPCException(ret['exception'])
    if isinstance(ret['ret'], dict) and 'generatorID' in ret['ret']:
        return RemoteGenerator(self, ret['ret']['generatorID'])
    return ret['ret']

def destroyClient(clientObj):
    if hasattr(clientObj, 'clientID') and clientObj.clientID is not None:
        try:
            clientObj.Send({'DEL': '', 'clientID': clientObj.clientID})
        except:
            pass
        clientObj.clientID = None

class AJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, bytes):
            return {'_type': 'bytes', 'value': base64.b64encode(obj).decode('utf-8')}
        elif isinstance(obj, AImage):
            return {'_type': 'AImage', 'value': obj.ToJson()}
        elif isinstance(obj, AImageLocation):
            return {'_type': 'AImageLocation', 'value': obj.ToJson()}
        elif isinstance(obj, AVideo):
            return {'_type': 'AVideo', 'value': obj.ToJson()}
        elif isinstance(obj, AVideoLocation):
            return {'_type': 'AVideoLocation', 'value': obj.ToJson()}
        elif isinstance(obj, pydantic.BaseModel):
            return {'_type': obj.__class__.__name__, 'value': obj.model_dump_json()}
        else:
            return super(AJSONEncoder, self).default(obj)

def default(self, obj):
    if isinstance(obj, bytes):
        return {'_type': 'bytes', 'value': base64.b64encode(obj).decode('utf-8')}
    elif isinstance(obj, AImage):
        return {'_type': 'AImage', 'value': obj.ToJson()}
    elif isinstance(obj, AImageLocation):
        return {'_type': 'AImageLocation', 'value': obj.ToJson()}
    elif isinstance(obj, AVideo):
        return {'_type': 'AVideo', 'value': obj.ToJson()}
    elif isinstance(obj, AVideoLocation):
        return {'_type': 'AVideoLocation', 'value': obj.ToJson()}
    elif isinstance(obj, pydantic.BaseModel):
        return {'_type': obj.__class__.__name__, 'value': obj.model_dump_json()}
    else:
        return super(AJSONEncoder, self).default(obj)

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

def ToJson(self):
    return {'type': 'AImage', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

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

def ToJson(self):
    return {'type': 'AVideo', 'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8') if self.data else self.data}

class ALoggerSection:

    def __init__(self, recv):
        self.recv = recv
        return

    def __enter__(self):
        self.recv('<')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.recv('>')
        return False

    def __call__(self, channel: str, txt: str=None, action: str=''):
        return self.recv(channel, txt, action)

def __enter__(self):
    self.recv('<')
    return self

def __exit__(self, exc_type, exc_value, traceback):
    self.recv('>')
    return False

def __call__(self, channel: str, txt: str=None, action: str=''):
    return self.recv(channel, txt, action)

class ALoggerMsg:

    def __init__(self, recv, channel):
        self.recv = recv
        self.channel = channel
        return

    def __enter__(self):
        self.recv(channel=self.channel, txt='', action='open')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.recv(channel=self.channel, txt='', action='close')
        return False

    def __call__(self, txt: str):
        return self.recv(channel=self.channel, txt=txt, action='append')

def __enter__(self):
    self.recv(channel=self.channel, txt='', action='open')
    return self

def __exit__(self, exc_type, exc_value, traceback):
    self.recv(channel=self.channel, txt='', action='close')
    return False

def __call__(self, txt: str):
    return self.recv(channel=self.channel, txt=txt, action='append')

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

def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
    return self.Query(collection=collection, clue=query, num_results=num_results)

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

def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
    return self.Query(collection=collection, clue=query, num_results=num_results)

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

def Recall(self, collection: str, query: str, num_results: int=1) -> list[tuple[str, float]]:
    return self.Query(collection=collection, clue=query, num_results=num_results)

class AScrollablePage:

    def __init__(self, functions: dict[str, str]):
        self.txt = None
        self.indivisibles = []
        self.currentIdx = None
        self.currentEnd = None
        self.functions = functions
        return

    def Clamp(self, x: int) -> int:
        r = 0 if x < 0 else x
        r = len(self.txt) if r > len(self.txt) else r
        return r

    def BoundCorrection(self, edge: int) -> int:
        for l, r in self.indivisibles:
            if l < edge and edge < r:
                return (l, r)
        return (edge, edge)

    def CalcWindow(self, pos: int, posType: str) -> tuple[int, int]:
        pos = self.Clamp(pos)
        delta = {'start': 0, 'mid': -STEP // 2, 'end': -STEP}
        start = pos + delta[posType]
        end = start + STEP
        start = self.Clamp(start)
        end = self.Clamp(end)
        lBound, rBound = (self.BoundCorrection(start), self.BoundCorrection(end))
        if 'start' == posType:
            return (start, rBound[0] if rBound[0] > start else rBound[1])
        elif 'end' == posType:
            return (lBound[1] if lBound[1] < end else lBound[0], end)
        elif 'mid' == posType:
            return (lBound[1], rBound[0]) if lBound[1] < rBound[0] else (lBound[0], rBound[1])

    def ConstructPrompt(self) -> str:
        ret = 'To avoid excessive consumption of context space due to lengthy content, we have paginated the entire content. This is just one page, to browse more content, please use the following function(s) for page navigation.\n'
        funcs = []
        if 'SCROLLDOWN' in self.functions and self.currentEnd < len(self.txt):
            funcs.append(self.functions['SCROLLDOWN'])
        if 'SCROLLUP' in self.functions and self.currentIdx > 0:
            funcs.append(self.functions['SCROLLUP'])
        if 'SEARCHDOWN' in self.functions and self.currentEnd < len(self.txt):
            funcs.append(self.functions['SEARCHDOWN'])
        if 'SEARCHUP' in self.functions and self.currentIdx > 0:
            funcs.append(self.functions['SEARCHUP'])
        pos = self.currentIdx
        prior = float(pos) / float(len(self.txt)) * 100 if len(self.txt) > 0 else 0.0
        remaining = float(len(self.txt) - self.currentEnd) / float(len(self.txt)) * 100 if len(self.txt) > 0 else 0.0
        return f'Prior: {prior:.1f}% / Remaining: {remaining:.1f}% \n\n' + (ret + '\n'.join(funcs) if len(funcs) > 0 else '')

    def LoadPage(self, txt: str, initPosition: str):
        self.txt = txt
        self.indivisibles = [(match.start(), match.end()) for match in re.finditer('!\\[([^\\]]*)\\]\\(([^)]+)\\)', self.txt)]
        self.currentIdx, self.currentEnd = {'TOP': self.CalcWindow(0, 'start'), 'BOTTOM': self.CalcWindow(len(txt), 'end')}[initPosition]
        return

    def ScrollDown(self) -> str:
        self.currentIdx, self.currentEnd = self.CalcWindow(self.currentEnd, 'start')
        return self()

    def ScrollUp(self) -> str:
        self.currentIdx, self.currentEnd = self.CalcWindow(self.currentIdx, 'end')
        return self()

    def SearchDown(self, query: str) -> str:
        loc = self.txt.lower().find(query.lower(), self.currentIdx)
        self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
        return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

    def SearchUp(self, query: str) -> str:
        loc = self.txt.lower().rfind(query.lower(), 0, self.currentIdx)
        self.currentIdx, self.currentEnd = self.CalcWindow(loc, 'mid') if -1 != loc else (self.currentIdx, self.currentEnd)
        return self() if -1 != loc else 'NOT FOUND. \nSince this is an exact match search for text fragments, you can try using shorter query phrases to increase the success rate.'

    def ReplaceText(self, replacement: str, replaceAll: bool=False):
        if replaceAll:
            self.txt = replacement
        else:
            self.txt = self.txt[:self.currentIdx] + replacement + self.txt[self.currentEnd:]
        return

    def __call__(self, prompt: bool=True) -> str:
        ret = self.txt[self.currentIdx:self.currentEnd]
        return f'\n\n---\n\n{ret}\n\n---\n\n{self.ConstructPrompt()}' if prompt else ret

def __call__(self, prompt: bool=True) -> str:
    ret = self.txt[self.currentIdx:self.currentEnd]
    return f'\n\n---\n\n{ret}\n\n---\n\n{self.ConstructPrompt()}' if prompt else ret

def AddActionMethod(kls, name: str, tool):

    async def async_action_method(self, jsonParam: str) -> str:
        try:
            return await self.session.call_tool(name, arguments=json.loads(jsonParam))
        except Exception as e:
            return json.dumps({'error': str(e)})

    def action_method(self, jsonParam: str) -> list:
        ret = asyncio.run_coroutine_threadsafe(async_action_method(self, jsonParam), loop).result()
        result = []
        for item in ret.content:
            if type(item) == mcp.types.TextContent:
                result.append(str(item))
            elif type(item) == mcp.types.ImageContent:
                result.append(AImage.FromJson({'data': item.data}))
            elif type(item) == mcp.types.EmbeddedResource:
                result.append('[Unsupported EmbeddedResource content]')
        return result
    action_method.__name__ = name
    action_method.__qualname__ = f'{kls.__name__}.{name}'
    setattr(kls, name, action_method)
    kls.MODULE_INFO['ACTIONS'][name] = {'func': name, 'prompt': ConstructPrompt(name, tool), 'type': 'primary'}
    return

def chat_with_ailice(message: str) -> str:
    data = {'message': message}
    headers = {'Content-Type': 'application/json'}
    response = requests.get('http://localhost:5000/new_chat', headers=headers)
    response = requests.post('http://localhost:5000/chat', json=data, headers=headers, stream=True)
    full_response = ''
    current_role = ''
    current_msg = ''
    ret = ''
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                line = line[6:]
            msg = json.loads(line)
            if 'open' == msg['action']:
                current_role = msg['role']
                current_msg = msg['message']
            elif 'append' == msg['action']:
                current_msg += msg['message']
            elif 'close' == msg['action']:
                current_msg += msg['message']
                print(colored(current_role, 'green'), ': ')
                print(current_msg)
            if 'user-ailice' == msg['msgType'] and 'ASSISTANT_AIlice' == msg['role']:
                ret += msg['message']
    return ret

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

def EvalVarRef(self, varName: str) -> Any:
    if varName in self.env:
        return self.env[varName]
    else:
        raise ValueError(f'Variable name {varName} NOT FOUND, did you mean to use a string "{varName}" but forgot the quotation marks?')

def CreateFormatter(formatterClsName: str, tokenizer, systemAsUser):
    formatterList = [obj for name, obj in inspect.getmembers(inspect.getmodule(inspect.currentframe())) if inspect.isclass(obj) and name.startswith('AFormatter')]
    for formatterCls in formatterList:
        if formatterClsName == formatterCls.__name__:
            return formatterCls(tokenizer=tokenizer, systemAsUser=systemAsUser)
    raise ValueError(f'{formatterClsName} is not a valid formatter class name.')

