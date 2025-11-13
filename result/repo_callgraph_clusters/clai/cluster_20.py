# Cluster 20

def get_base_path():
    root_path = os.getcwd()
    print(root_path)
    if 'test_integration' in root_path:
        return '../'
    return '.'

class SocketClientConnector(ClientConnector):

    def __init__(self, host: str, port: int):
        self.sel = selectors.DefaultSelector()
        self.host = host
        self.port = port
        self.uuid = uuid.uuid4()

    def send(self, message: StateDTO) -> Action:
        try:
            return self._internal_send(message)
        except Exception as error:
            logger.info(f'error {error}')
            logger.info(traceback.format_exc())
            return Action(origin_command=message.command, suggested_command=message.command)
        finally:
            self.close()

    def _internal_send(self, command_to_send):
        self.start_connections(self.host, int(self.port))
        self.write(command_to_send)
        action = self.read()
        if action:
            return action
        return Action(origin_command=command_to_send.command, suggested_command=command_to_send.command)

    def start_connections(self, host, port):
        server_address = (host, port)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setblocking(False)
        client_socket.connect_ex(server_address)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=self.uuid, outb=b'')
        self.sel.register(client_socket, events, data=data)

    def write(self, message: StateDTO):
        events = self.sel.select(timeout=5)
        key = events[0][0]
        client_socket = key.fileobj
        data = key.data
        self.sel.modify(client_socket, selectors.EVENT_WRITE, data)
        logger.info(f'echoing ${data}')
        data.outb = str(message.json())
        sent = client_socket.send(data.outb.encode('utf-8'))
        data.outb = data.outb[sent:]
        self.sel.modify(client_socket, selectors.EVENT_READ, data)

    def read(self) -> Optional[Action]:
        events = self.sel.select(timeout=6)
        if events and events[0]:
            key = events[0][0]
            client_socket = key.fileobj
            received_data = client_socket.recv(4024)
            if received_data:
                message = process_message(received_data)
                return message
        return None

    def close(self):
        self.sel.close()

def write(self, message: StateDTO):
    events = self.sel.select(timeout=5)
    key = events[0][0]
    client_socket = key.fileobj
    data = key.data
    self.sel.modify(client_socket, selectors.EVENT_WRITE, data)
    logger.info(f'echoing ${data}')
    data.outb = str(message.json())
    sent = client_socket.send(data.outb.encode('utf-8'))
    data.outb = data.outb[sent:]
    self.sel.modify(client_socket, selectors.EVENT_READ, data)

def read(self) -> Optional[Action]:
    events = self.sel.select(timeout=6)
    if events and events[0]:
        key = events[0][0]
        client_socket = key.fileobj
        received_data = client_socket.recv(4024)
        if received_data:
            message = process_message(received_data)
            return message
    return None

def close(self):
    self.sel.close()

class SocketServerConnector(ServerConnector):
    BUFFER_SIZE = 4024

    def __init__(self, server_status_datasource: ServerStatusDatasource):
        self.server_status_datasource = server_status_datasource
        self.sel = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def create_socket(self, host: str, port: int):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        logger.info(f'Listening {host} {port}')
        self.server_socket.setblocking(False)

    def loop(self, process_message: Callable[[bytes], Action]):
        self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)
        try:
            while self.server_status_datasource.running:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.__accept_wrapper(key.fileobj)
                    else:
                        self.__service_connection(key, mask, process_message)
            self.sel.unregister(self.server_socket)
            self.server_socket.close()
        except KeyboardInterrupt:
            logger.info('caught keyboard interrupt, exiting')
        finally:
            logger.info('server closed')
            self.sel.close()

    def __accept_wrapper(self, server_socket):
        connection, address = server_socket.accept()
        connection.setblocking(False)
        data = types.SimpleNamespace(addr=address, inb=b'', outb=b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(connection, events, data=data)

    def __service_connection(self, key, mask, process_message):
        fileobj = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            data = self.__read(data, fileobj, process_message)
        if mask & selectors.EVENT_WRITE:
            self.__write(data, fileobj)

    @staticmethod
    def __write(data, server_socket):
        if data.outb:
            logger.info(f'sending from client ${data.outb}')
            server_socket.send(data.outb)
            data.outb = b''

    def __read(self, data, server_socket, process_message):
        recv_data = b''
        chewing = True
        logger.info(f'receiving from client')
        while chewing:
            part = server_socket.recv(self.BUFFER_SIZE)
            recv_data += part
            if len(part) < self.BUFFER_SIZE:
                chewing = False
        if recv_data:
            logger.info(f'receiving from client ${recv_data}')
            action = process_message(recv_data)
            data.outb = str(action.json()).encode('utf8')
        else:
            self.sel.unregister(server_socket)
            server_socket.close()
        return data

def loop(self, process_message: Callable[[bytes], Action]):
    self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)
    try:
        while self.server_status_datasource.running:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    self.__accept_wrapper(key.fileobj)
                else:
                    self.__service_connection(key, mask, process_message)
        self.sel.unregister(self.server_socket)
        self.server_socket.close()
    except KeyboardInterrupt:
        logger.info('caught keyboard interrupt, exiting')
    finally:
        logger.info('server closed')
        self.sel.close()

def __read(self, data, server_socket, process_message):
    recv_data = b''
    chewing = True
    logger.info(f'receiving from client')
    while chewing:
        part = server_socket.recv(self.BUFFER_SIZE)
        recv_data += part
        if len(part) < self.BUFFER_SIZE:
            chewing = False
    if recv_data:
        logger.info(f'receiving from client ${recv_data}')
        action = process_message(recv_data)
        data.outb = str(action.json()).encode('utf8')
    else:
        self.sel.unregister(server_socket)
        server_socket.close()
    return data

def get_response(assistant_id: str, data: Dict) -> Dict:
    try:
        session_info = assistant.create_session(assistant_id=assistant_id).get_result()
        response = assistant.message(assistant_id=assistant_id, session_id=session_info['session_id'], input={'message_type': 'text', 'text': data['text'], 'options': {'alternate_intents': True}}).get_result()
        return json.dumps({'result': 'success', 'response': response})
    except Exception as e:
        return json.dumps({'result': str(e)})

class Datastore:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(str(Path(__file__).parent.absolute()), 'config.ini'))
        self.stack_exchange_api = config['API'].get('stack_exchange_api')
        self.manpage_api = config['API'].get('manpage_api')

    def __call_manpage_api__(self, query: str, limit: int=1):
        payload = {'text': query, 'result_count': limit}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(self.manpage_api, params=payload, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None

    def __call_stack_exchange_api__(self, query: str, limit: int=1):
        payload = {'text': query, 'limit': limit}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(self.stack_exchange_api, data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            return r.json()['hits']
        return None

    def search(self, query, service='stack_exchange', size=10):
        if service == 'stack_exchange':
            res = self.__call_stack_exchange_api__(query, size)
        elif service == 'manpages':
            res = self.__call_manpage_api__(query, size)
        else:
            raise AttributeError('Please select stack_exchange or manpage as a choice for service')
        return res

def __call_manpage_api__(self, query: str, limit: int=1):
    payload = {'text': query, 'result_count': limit}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self.manpage_api, params=payload, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def __call_stack_exchange_api__(self, query: str, limit: int=1):
    payload = {'text': query, 'limit': limit}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self.stack_exchange_api, data=json.dumps(payload), headers=headers)
    if r.status_code == 200:
        return r.json()['hits']
    return None

class Datastore:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(str(Path(__file__).parent.absolute()), 'config.ini'))
        self.stack_exchange_api = config['API'].get('stack_exchange_api')
        self.manpage_api = config['API'].get('manpage_api')

    def __call_manpage_api__(self, query: str, limit: int=1):
        payload = {'text': query, 'result_count': limit}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(self.manpage_api, params=payload, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None

    def __call_stack_exchange_api__(self, query: str, limit: int=1):
        payload = {'text': query, 'limit': limit}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(self.stack_exchange_api, data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            return r.json()['hits']
        return None

    def search(self, query, service='stack_exchange', size=10):
        if service == 'stack_exchange':
            res = self.__call_stack_exchange_api__(query, size)
        elif service == 'manpages':
            res = self.__call_manpage_api__(query, size)
        else:
            raise AttributeError('Please select stack_exchange or manpage as a choice for service')
        return res

def __call_manpage_api__(self, query: str, limit: int=1):
    payload = {'text': query, 'result_count': limit}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self.manpage_api, params=payload, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def __call_stack_exchange_api__(self, query: str, limit: int=1):
    payload = {'text': query, 'limit': limit}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self.stack_exchange_api, data=json.dumps(payload), headers=headers)
    if r.status_code == 200:
        return r.json()['hits']
    return None

class ManPageAgent(Agent):

    def __init__(self):
        super(ManPageAgent, self).__init__()
        self.question_detection_mod = QuestionDetection()
        self._config = None
        self._API_URL = None
        self.read_config()

    def read_config(self):
        curdir = str(Path(__file__).parent.absolute())
        config_path = os.path.join(curdir, 'config.json')
        with open(config_path, 'r') as f:
            self._config = json.load(f)
        self._API_URL = self._config['API_URL']

    def __call_api__(self, search_text):
        payload = {'text': search_text, 'result_count': 1}
        headers = {'Content-Type': 'application/json'}
        r = requests.post(self._API_URL, params=payload, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None

    def get_next_action(self, state: State) -> Action:
        cmd = state.command
        is_question = self.question_detection_mod.is_question(cmd)
        if not is_question:
            return Action(suggested_command=state.command, confidence=0.0)
        response = None
        try:
            response = self.__call_api__(cmd)
        except Exception:
            pass
        if response is None or response['status'] != 'success':
            return Action(suggested_command=state.command, confidence=0.0)
        command = response['commands'][-1]
        confidence = response['dists'][-1]
        try:
            cmd_tldr = tldr_wrapper.get_command_tldr(command)
        except Exception as err:
            print('Exception: ' + str(err))
            cmd_tldr = ''
        return Action(suggested_command='man {}'.format(command), confidence=confidence, description=cmd_tldr)

def __call_api__(self, search_text):
    payload = {'text': search_text, 'result_count': 1}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(self._API_URL, params=payload, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

class StackExchange(Provider):

    def __init__(self, name: str, description: str, section: dict):
        super().__init__(name, description, section)
        self.__log_debug__('UNIX StackExchange provider initialized')

    def call(self, query: str, limit: int=1, **kwargs):
        self.__log_debug__(f'call(query={query}, limit={str(limit)}), **kwargs={str(kwargs)})')
        payload = {'text': query, 'limit': limit}
        request = self.__send_post_request__(self.base_uri, data=json.dumps(payload))
        if request.status_code == 200:
            return request.json()['hits']
        return None

    def extract_search_result(self, data: List[Dict]) -> str:
        return data[0]['Answer']

    def get_printable_output(self, data: List[Dict]) -> str:
        lines = [f'Post: {data[0]['Content'][:384] + ' ...'}', f'Answer: {data[0]['Answer'][:256] + ' ...'}', f'Link: {data[0]['Url']}\n']
        return '\n'.join(lines)

def call(self, query: str, limit: int=1, **kwargs):
    self.__log_debug__(f'call(query={query}, limit={str(limit)}), **kwargs={str(kwargs)})')
    payload = {'text': query, 'limit': limit}
    request = self.__send_post_request__(self.base_uri, data=json.dumps(payload))
    if request.status_code == 200:
        return request.json()['hits']
    return None

class Manpages(Provider):

    def __init__(self, name: str, description: str, section: dict):
        super().__init__(name, description, section)
        self.__log_debug__('Manpages provider initialized')

    def call(self, query: str, limit: int=1, **kwargs):
        self.__log_debug__(f'call(query={query}, limit={str(limit)}), **kwargs={str(kwargs)})')
        payload = {'text': query, 'result_count': limit}
        request = self.__send_post_request__(self.base_uri, params=payload)
        if request.status_code == 200:
            return request.json()
        return None

    def extract_search_result(self, data: List[Dict]) -> str:
        pass

    def get_printable_output(self, data: List[Dict]) -> str:
        pass

def call(self, query: str, limit: int=1, **kwargs):
    self.__log_debug__(f'call(query={query}, limit={str(limit)}), **kwargs={str(kwargs)})')
    payload = {'text': query, 'result_count': limit}
    request = self.__send_post_request__(self.base_uri, params=payload)
    if request.status_code == 200:
        return request.json()
    return None

def read(socket, chunk_readed=None):
    data = ''
    try:
        socket.output._sock.recv(1)
        while True:
            data_bytes = socket.output._sock.recv(4096)
            if not data_bytes:
                break
            chunk = data_bytes.decode('utf8', errors='ignore')
            if chunk.endswith(']# '):
                if data:
                    break
            else:
                data += chunk
            if chunk_readed:
                chunk_readed(chunk)
            data = data[-MAX_SIZE_STDOUT:]
    except Exception as exception:
        print(f'error: {exception}')
    return data

class ActionRemoteStorage:
    _instance = None
    manager = None
    queue = None
    consumer_task = None
    pool = None
    report_enable = None
    anonymizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionRemoteStorage, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        self.manager = mp.Manager()
        self.queue = self.manager.Queue()
        self.consumer_task = None
        self.pool = mp.Pool(1)
        self.report_enable = False
        self.anonymizer = Anonymizer()

    @staticmethod
    def consumer(queue):
        while True:
            data = queue.get()
            if data is None:
                break
            logger.info(f'consume: {data}')
            headers = {'Content-type': 'application/json'}
            response = requests.post(url=URL_SERVER, data=data, headers=headers)
            logger.info(f'[Sent] {response.status_code} message {response.text}')
            queue.task_done()
        logger.info('----STOP CONSUMING-----')

    def start(self, agent_datasource: AgentDatasource):
        logger.info(f'-Start sender-')
        self.report_enable = agent_datasource.get_report_enable()
        if self.report_enable:
            self.consumer_task = self.pool.map_async(self.consumer, (self.queue,))

    def wait(self):
        if self.report_enable:
            self.queue.put(None)
            self.consumer_task.wait(timeout=3)

    def store(self, message: TerminalReplayMemory):
        if not self.report_enable:
            return
        try:
            command = message.command
            message_as_json = TerminalReplayMemoryApi(command=self.__parse_state__(command, self.anonymizer), agent_names=message.agent_names, candidate_actions=self.__parse_actions__(message.candidate_actions), force_response=str(message.force_response), suggested_command=self.__parse_actions__(message.suggested_command))
            logger.info(f'store -> {message.command.command_id}')
            message_to_send = RecordToSendApi(bashbot_info=message_as_json)
            self.queue.put(message_to_send.json())
        except Exception as err:
            logger.info(f'error sending: {err}')

    @staticmethod
    def __parse_state__(command: State, anonymizer: Anonymizer):
        command_api = StateApi()
        command_api.command_id = command.command_id
        command_api.user_name = anonymizer.anonymize(command.user_name)
        command_api.command = command.command
        command_api.root = command.root
        command_api.processes = command.processes
        command_api.file_changes = command.file_changes
        command_api.network = command.network
        command_api.result_code = command.result_code
        command_api.stderr = command.stderr
        return command_api

    @staticmethod
    def __parse_actions__(candidate_actions: Optional[List[Union[Action, List[Action]]]]):
        if not candidate_actions:
            return []
        if isinstance(candidate_actions, Action):
            return [candidate_actions]
        return candidate_actions

def store(self, message: TerminalReplayMemory):
    if not self.report_enable:
        return
    try:
        command = message.command
        message_as_json = TerminalReplayMemoryApi(command=self.__parse_state__(command, self.anonymizer), agent_names=message.agent_names, candidate_actions=self.__parse_actions__(message.candidate_actions), force_response=str(message.force_response), suggested_command=self.__parse_actions__(message.suggested_command))
        logger.info(f'store -> {message.command.command_id}')
        message_to_send = RecordToSendApi(bashbot_info=message_as_json)
        self.queue.put(message_to_send.json())
    except Exception as err:
        logger.info(f'error sending: {err}')

class EmulatorPresenter:

    def __init__(self, emulator_docker_bridge: EmulatorDockerBridge, on_skills_ready, on_server_running, on_server_stopped):
        self.server_running = False
        self.server_process = None
        self.current_active_skill = ''
        self.emulator_docker_bridge = emulator_docker_bridge
        self.on_skills_ready = on_skills_ready
        self.on_server_running = on_server_running
        self.on_server_stopped = on_server_stopped
        self.log_value = ''
        self.log_read = None

    @staticmethod
    def __get_base_path():
        root_path = os.getcwd()
        if 'bin' in root_path:
            return '../'
        return '.'

    def select_skill(self, skill_name: str):
        if skill_name == self.current_active_skill:
            return
        self._send_select(skill_name)
        self._send_unselect(self.current_active_skill)
        self.request_skills()

    def request_skills(self):
        self.emulator_docker_bridge.request_skills()

    def send_message(self, message):
        self.emulator_docker_bridge.send_message(message)

    def attach_log(self, chunked_read):
        self.log_read = chunked_read

    def _send_select(self, skill_name: str):
        self.emulator_docker_bridge.select_skill(skill_name)

    def _send_unselect(self, skill_name: str):
        self.emulator_docker_bridge.unselect_skill(skill_name)

    def run_server(self):
        self.emulator_docker_bridge.start()
        self.server_running = True
        self.on_server_running()
        self.request_skills()

    def stop_server(self):
        print(f'is server running {self.server_running}')
        if self.server_running:
            self.emulator_docker_bridge.stop_server()
            self.server_running = False
        self.on_server_stopped()

    def refresh_files(self):
        self.emulator_docker_bridge.refresh_files()

    def retrieve_messages(self, add_row):
        reply = self.emulator_docker_bridge.retrieve_message()
        if reply:
            if reply.docker_reply == 'skills':
                skills_as_array = reply.message.splitlines()
                self.on_skills_ready(skills_as_array[2:-1])
            elif reply.docker_reply == 'reply_message':
                info_as_string = reply.info[reply.info.index('{'):]
                info_as_string = info_as_string[:info_as_string.index('\n')]
                print(f'----> {info_as_string}')
                info = InfoDebug(**json.loads(info_as_string))
                add_row(reply.message, info)
            elif reply.docker_reply == 'log':
                self.log_value = self.extract_chunk_log(self.log_value, reply.message)
                if self.log_read:
                    self.log_read(self.log_value)
            else:
                print(f'-----> {reply.docker_reply} : {reply.message}')

    @staticmethod
    def extract_chunk_log(log_value, message):
        if not message:
            return ''
        log_as_list = log_value.split('\n')
        message_as_list = message.split('\n')
        new_log = []
        if log_as_list.__contains__(message_as_list[0]):
            index = log_as_list.index(message_as_list[0])
            new_log = message_as_list[len(log_as_list) - index - 1:]
        else:
            new_log = message_as_list
        return '\n'.join(new_log)

@staticmethod
def __get_base_path():
    root_path = os.getcwd()
    if 'bin' in root_path:
        return '../'
    return '.'

def get_base_path():
    root_path = os.getcwd()
    if 'bin' in root_path:
        return '../'
    return '.'

def __get_image(docker_client):
    path = get_base_path()
    print(f'Building {path}')
    try:
        image, logs = docker_client.images.build(path=path, dockerfile='./clai/emulator/docker/centos/Dockerfile', rm=True)
        for log in logs:
            print(log)
    except:
        traceback.print_exc()
    return image

def copy_files(my_clai):
    old_path = os.getcwd()
    print(f'Building {old_path}')
    srcpath = os.path.join(get_base_path(), 'clai', 'server', 'plugins')
    os.chdir(srcpath)
    tar = tarfile.open('temp.tar', mode='w')
    try:
        tar.add('.', recursive=True)
    finally:
        tar.close()
    data = open('temp.tar', 'rb').read()
    destdir = os.path.join(os.path.expanduser('/opt/local/share'), 'clai', 'bin', 'clai', 'server', 'plugins')
    my_clai._container.put_archive(destdir, data)
    os.chdir(old_path)
    print('Done the refresh')

