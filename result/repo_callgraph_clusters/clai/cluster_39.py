# Cluster 39

def create_server_socket(host, port, websocket):
    if websocket:
        server = ClaiServer(connector=WebSocketServerConnector())
    else:
        server = ClaiServer()
    server.init_server()
    server.create_socket(host, port)
    server.listen_client_sockets()
    print(f'server created in host: {host} and port: {port}')

class ClaiServer:

    def __init__(self, server_status_datasource: ServerStatusDatasource=current_status_datasource, connector: ServerConnector=SocketServerConnector(current_status_datasource), agent_datasource=AgentDatasource()):
        self.connector = connector
        self.agent_datasource = agent_datasource
        self.server_status_datasource = server_status_datasource
        self.remote_storage = ActionRemoteStorage()
        self.message_handler = MessageHandler(server_status_datasource, agent_datasource=agent_datasource)
        self.stats_tracker = StatsTracker()

    def init_server(self):
        self.message_handler.init_server()
        self.server_status_datasource.running = True
        self.remote_storage.start(self.agent_datasource)
        self.stats_tracker.start(self.agent_datasource)

    @staticmethod
    def serialize_message(data) -> State:
        StateDTO.update_forward_refs()
        dto = StateDTO(**json.loads(data))
        return State(command_id=dto.command_id, user_name=dto.user_name, command=dto.command, root=dto.root, processes=dto.processes, file_changes=dto.file_changes, network=dto.network, result_code=dto.result_code, stderr=dto.stderr)

    def create_socket(self, host, port):
        self.connector.create_socket(host, port)

    def listen_client_sockets(self):
        self.connector.loop(self.process_message)
        self.remote_storage.wait()
        self.stats_tracker.wait()

    def process_message(self, received_data: bytes) -> Action:
        message = self.serialize_message(received_data)
        return self.message_handler.process_message(message)

def init_server(self):
    self.message_handler.init_server()
    self.server_status_datasource.running = True
    self.remote_storage.start(self.agent_datasource)
    self.stats_tracker.start(self.agent_datasource)

def create_socket(self, host, port):
    self.connector.create_socket(host, port)

class Service:

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):

        def __compute(*args):
            result.append(eval('wa_skills.' + args[0])(args[1]))
        msg = args[0]
        result = []
        threads = []
        for item in dir(wa_skills):
            if 'wa_skill_processor' in item:
                threads.append(threading.Thread(target=__compute, args=(item, msg)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return sorted(result, key=itemgetter(1), reverse=True)[0]

def __call__(self, *args, **kwargs):

    def __compute(*args):
        result.append(eval('wa_skills.' + args[0])(args[1]))
    msg = args[0]
    result = []
    threads = []
    for item in dir(wa_skills):
        if 'wa_skill_processor' in item:
            threads.append(threading.Thread(target=__compute, args=(item, msg)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(result, key=itemgetter(1), reverse=True)[0]

class PreferenceOrchestrator(Orchestrator):

    def __init__(self):
        super(PreferenceOrchestrator, self).__init__()
        self._config_path = os.path.join(Path(__file__).parent.absolute(), 'config.json')
        self.__read_config()

    def __read_config(self):
        with open(self._config_path, 'r') as fileobj:
            config = json.load(fileobj)
        self.threshold = config['threshold']
        self.preferences = config['preferences']

    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Action]:
        """Choose an action for CLAI to respond with"""
        if not candidate_actions:
            return None
        cache_candidates = []
        for action in candidate_actions:
            confidence = self.__calculate_confidence__(action)
            if confidence >= self.threshold:
                cache_candidates.append([action, confidence])
        cache_candidates = sorted(cache_candidates, key=lambda x: x[1], reverse=True)
        for candidate in cache_candidates:
            send_flag = True
            for preference in self.preferences:
                if candidate[0].agent_owner == preference[1]:
                    if preference[0] in [item[0].agent_owner for item in cache_candidates]:
                        send_flag = False
                        break
            if send_flag:
                return candidate[0]
        if force_response:
            if cache_candidates:
                return cache_candidates[0][0]
            return None
        return None

def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Action]:
    """Choose an action for CLAI to respond with"""
    if not candidate_actions:
        return None
    cache_candidates = []
    for action in candidate_actions:
        confidence = self.__calculate_confidence__(action)
        if confidence >= self.threshold:
            cache_candidates.append([action, confidence])
    cache_candidates = sorted(cache_candidates, key=lambda x: x[1], reverse=True)
    for candidate in cache_candidates:
        send_flag = True
        for preference in self.preferences:
            if candidate[0].agent_owner == preference[1]:
                if preference[0] in [item[0].agent_owner for item in cache_candidates]:
                    send_flag = False
                    break
        if send_flag:
            return candidate[0]
    if force_response:
        if cache_candidates:
            return cache_candidates[0][0]
        return None
    return None

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

def select_skill(self, skill_name: str):
    if skill_name == self.current_active_skill:
        return
    self._send_select(skill_name)
    self._send_unselect(self.current_active_skill)
    self.request_skills()

def request_skills(self):
    self.emulator_docker_bridge.request_skills()

def run_server(self):
    self.emulator_docker_bridge.start()
    self.server_running = True
    self.on_server_running()
    self.request_skills()

