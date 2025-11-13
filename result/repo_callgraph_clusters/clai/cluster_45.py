# Cluster 45

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

class MessageHandler:

    def __init__(self, server_status_datasource: ServerStatusDatasource, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource
        orchestrator_provider = OrchestratorProvider(agent_datasource)
        self.agent_runner = AgentRunner(self.agent_datasource, orchestrator_provider)
        self.server_status_datasource = server_status_datasource
        self.server_pending_actions_datasource = ServerPendingActionsDatasource()
        self.command_runner_factory = CommandRunnerFactory(self.agent_datasource, config_storage, self.server_status_datasource, orchestrator_provider)

    def init_server(self):
        self.agent_datasource.preload_plugins()

    def process_post_command(self, message: State) -> Action:
        message = self.complete_history(message)
        command_runner = self.command_runner_factory.provide_post_command_runner(message.command, self.agent_runner)
        action = command_runner.execute_post(message)
        if not action:
            action = Action()
        action.origin_command = message.command
        return action

    def __process_command_ai(self, message) -> List[Action]:
        if message.command == STOP_COMMAND:
            self.server_status_datasource.running = False
            return [Action()]
        command_runner = self.command_runner_factory.provide_command_runner(message.command, self.agent_runner)
        action = command_runner.execute(message)
        if isinstance(action, Action):
            return [action]
        return action

    def __process_command(self, message: State) -> Action:
        if not message.is_already_processed():
            message.previous_execution = self.server_status_datasource.get_last_message(message.user_name)
            actions = self.__process_command_ai(message)
            message.mark_as_processed()
            logger.info(f'after setting info: {message.is_already_processed()}')
            self.server_status_datasource.store_info(message)
            action = self.server_pending_actions_datasource.store_pending_actions(message.command_id, actions, message.user_name)
        else:
            logger.info(f'we have pending action')
            action = self.server_pending_actions_datasource.get_next_action(message.command_id, message.user_name)
        if action is None:
            action = Action(suggested_command=message.command, origin_command=message.command, execute=False)
        action.origin_command = message.command
        if message.is_post_process():
            message.action_post_suggested = action
        else:
            message.action_suggested = action
        self.server_status_datasource.store_info(message)
        action.execute = action.execute or self.server_status_datasource.is_power()
        return action

    def process_message(self, message: State) -> Action:
        try:
            message = self.server_status_datasource.store_info(message)
            if message.is_post_process():
                message = self.server_status_datasource.find_message_stored(message.command_id, message.user_name)
                return self.process_post_command(message)
            if message.is_command():
                return self.__process_command(message)
        except Exception as ex:
            logger.info(f'error processing message {ex}')
            logger.info(traceback.format_exc())
        return Action(origin_command=message.command)

    def find_value(self, lines, message: State) -> Optional[int]:
        for i in reversed(range(len(lines))):
            if self.message_executed(lines[i], message):
                return i
        return None

    def complete_history(self, message: State):
        lines = read_history()
        index = self.find_value(lines, message)
        if index:
            last_values = lines[index:]
            message.values_executed = last_values
            if message.action_suggested.suggested_command and message.action_suggested.suggested_command in last_values[0]:
                message.suggested_executed = True
        else:
            message.values_executed = []
            message.suggested_executed = False
        return self.server_status_datasource.store_info(message)

    @staticmethod
    def message_executed(command_executed: str, message):
        if message is None or message.action_suggested is None:
            return True
        action_suggested = message.action_suggested.suggested_command
        return message.command in command_executed or (action_suggested and action_suggested in command_executed)

def __process_command(self, message: State) -> Action:
    if not message.is_already_processed():
        message.previous_execution = self.server_status_datasource.get_last_message(message.user_name)
        actions = self.__process_command_ai(message)
        message.mark_as_processed()
        logger.info(f'after setting info: {message.is_already_processed()}')
        self.server_status_datasource.store_info(message)
        action = self.server_pending_actions_datasource.store_pending_actions(message.command_id, actions, message.user_name)
    else:
        logger.info(f'we have pending action')
        action = self.server_pending_actions_datasource.get_next_action(message.command_id, message.user_name)
    if action is None:
        action = Action(suggested_command=message.command, origin_command=message.command, execute=False)
    action.origin_command = message.command
    if message.is_post_process():
        message.action_post_suggested = action
    else:
        message.action_suggested = action
    self.server_status_datasource.store_info(message)
    action.execute = action.execute or self.server_status_datasource.is_power()
    return action

def process_message(self, message: State) -> Action:
    try:
        message = self.server_status_datasource.store_info(message)
        if message.is_post_process():
            message = self.server_status_datasource.find_message_stored(message.command_id, message.user_name)
            return self.process_post_command(message)
        if message.is_command():
            return self.__process_command(message)
    except Exception as ex:
        logger.info(f'error processing message {ex}')
        logger.info(traceback.format_exc())
    return Action(origin_command=message.command)

def complete_history(self, message: State):
    lines = read_history()
    index = self.find_value(lines, message)
    if index:
        last_values = lines[index:]
        message.values_executed = last_values
        if message.action_suggested.suggested_command and message.action_suggested.suggested_command in last_values[0]:
            message.suggested_executed = True
    else:
        message.values_executed = []
        message.suggested_executed = False
    return self.server_status_datasource.store_info(message)

def process_message(data: str) -> Action:
    return Action(**json.loads(data))

class ClaiLastInfoCommandRunner(CommandRunner, PostCommandRunner):
    LAST_DIRECTIVE_DIRECTIVE = 'clai last-info'

    def __init__(self, server_status_datasource: ServerStatusDatasource):
        self.server_status_datasource = server_status_datasource

    def execute(self, state: State) -> Action:
        return Action(suggested_command=':', execute=True, origin_command=state.command)

    def execute_post(self, state: State) -> Action:
        offset_last = state.command.replace(f'{self.LAST_DIRECTIVE_DIRECTIVE}', '').strip()
        if not offset_last:
            offset_last = '0'
        if not offset_last.isdigit():
            offset_last = '0'
        offset_last_as_int = int(offset_last)
        last_message = self.server_status_datasource.get_last_message(state.user_name, offset=offset_last_as_int)
        if not last_message:
            return Action()
        info_to_show = InfoDebug(command_id=last_message.command_id, user_name=last_message.user_name, command=last_message.command, root=last_message.root, processes=last_message.processes, file_changes=last_message.file_changes, network=last_message.network, result_code=last_message.result_code, stderr=last_message.stderr, already_processed=last_message.already_processed, action_suggested=last_message.action_suggested)
        return Action(description=str(info_to_show.json()))

def execute_post(self, state: State) -> Action:
    offset_last = state.command.replace(f'{self.LAST_DIRECTIVE_DIRECTIVE}', '').strip()
    if not offset_last:
        offset_last = '0'
    if not offset_last.isdigit():
        offset_last = '0'
    offset_last_as_int = int(offset_last)
    last_message = self.server_status_datasource.get_last_message(state.user_name, offset=offset_last_as_int)
    if not last_message:
        return Action()
    info_to_show = InfoDebug(command_id=last_message.command_id, user_name=last_message.user_name, command=last_message.command, root=last_message.root, processes=last_message.processes, file_changes=last_message.file_changes, network=last_message.network, result_code=last_message.result_code, stderr=last_message.stderr, already_processed=last_message.already_processed, action_suggested=last_message.action_suggested)
    return Action(description=str(info_to_show.json()))

@app.route('/')
def hello():
    return 'Welcome to the router for the WA instances for the nlc2cmd skill in CLAI.'

@app.route('/tarbot', methods=['GET', 'POST', 'PUT'])
def tarbot():
    return get_response(assistant_id=config['skills'][inspect.stack()[0][3]], data=json.loads(request.get_data().decode('utf-8')))

@app.route('/grepbot', methods=['GET', 'POST', 'PUT'])
def grepbot():
    return get_response(assistant_id=config['skills'][inspect.stack()[0][3]], data=json.loads(request.get_data().decode('utf-8')))

@app.route('/zosbot', methods=['GET', 'POST', 'PUT'])
def zosbot():
    return get_response(assistant_id=config['skills'][inspect.stack()[0][3]], data=json.loads(request.get_data().decode('utf-8')))

@app.route('/')
def hello():
    print('Application running!')
    return 'Hello World!'

@app.route('/', methods=['GET'])
def homepage():
    return 'Agent up'

class ServerStatusDatasource:

    def __init__(self):
        self.__power = False
        self.__messages_store: Dict[str, deque] = {}
        self.running = False

    def __store_info_by_user(self, message: State, user_name: str):
        messages_by_user = self.__find_messages_by_user(user_name)
        messages_by_user.append(message)

    def __find_messages_by_user(self, user_name: str):
        if user_name not in self.__messages_store:
            self.__messages_store[user_name] = deque(maxlen=50)
        return self.__messages_store[user_name]

    def set_power(self, power: bool):
        self.__power = power

    def is_power(self):
        return self.__power

    def get_last_messages(self, user_name: str):
        return self.__find_messages_by_user(user_name)

    def get_last_message(self, user_name: str, offset: int=0) -> State:
        last_message = None
        messages_by_user = self.__find_messages_by_user(user_name)
        if messages_by_user and len(messages_by_user) > 1 + offset:
            last_message = messages_by_user[-2 - offset]
        return last_message

    def store_info(self, message: State) -> State:
        stored_message = self.find_message_stored(message.command_id, message.user_name)
        if stored_message is not None:
            stored_message.merge(message)
            return stored_message
        self.__store_info_by_user(message, message.user_name)
        return message

    def find_message_stored(self, id_to_find: str, user_mame: str) -> Optional[State]:
        messages_by_user = self.__find_messages_by_user(user_mame)
        return next(filter(lambda x: x.command_id == id_to_find, messages_by_user), None)

def store_info(self, message: State) -> State:
    stored_message = self.find_message_stored(message.command_id, message.user_name)
    if stored_message is not None:
        stored_message.merge(message)
        return stored_message
    self.__store_info_by_user(message, message.user_name)
    return message

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

