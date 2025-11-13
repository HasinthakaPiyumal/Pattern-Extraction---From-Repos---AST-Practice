# Cluster 34

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

def CalcEmbeddings(self, txts: list[str]):
    global model, modelLock
    with modelLock:
        return np.array(model.embed(txts))

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

def Speech2Text(self, wav: list, sr: int) -> str:
    global s2t
    return s2t.recognize(audio_data_to_numpy((np.array(wav), sr)))

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

