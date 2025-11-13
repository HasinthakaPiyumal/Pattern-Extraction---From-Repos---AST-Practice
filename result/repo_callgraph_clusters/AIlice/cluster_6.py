# Cluster 6

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

def SinkBuffer(self, channel: str, txt: str=None, action: str=''):
    if '>' == channel:
        if -1 == self.depth:
            self.queue.put({'message': '', 'role': '', 'action': '', 'msgType': ''})
    elif '<' == channel:
        return
    else:
        self.queue.put({'message': txt, 'role': channel, 'action': action, 'msgType': 'internal' if self.depth > 0 or self.ParseChannel(channel)[0] == 'SYSTEM' else 'user-ailice'})
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

def Get(self) -> str:
    self.continueEvent.wait()
    with self.lock:
        self.msgPrevious = self.msg
        self.msg = None
    return self.msgPrevious

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

def SinkQueue(self, channel: str, txt: str=None, action: str=''):
    self.queue.put((channel, txt, action))
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

def Text2Speech(self, txt: str) -> tuple[list, int]:
    global t2s
    if None == txt or '' == strip(txt):
        return ([1], 24000)
    audio, sr = t2s(txt)
    return (audio.tolist(), sr)

def Speak(self, txt: str):
    print('Speak(): ', txt)
    if None == txt or '' == strip(txt):
        return
    self.textQue.put(txt)
    self.inputDone = False
    return

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

