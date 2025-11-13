# Cluster 47

def test_should_return_any_action_when_everything_works_correctly(mocker):
    mocker.patch.object(ClaiClient, 'send', return_value=ANY_NO_ACTION, autospec=True)
    action = send_command(ANY_ID, ANY_USER, ANY_NO_ACTION.origin_command)
    assert action == ANY_NO_ACTION

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

@staticmethod
def __write(data, server_socket):
    if data.outb:
        logger.info(f'sending from client ${data.outb}')
        server_socket.send(data.outb)
        data.outb = b''

class ClaiClient:

    def __init__(self, host: str=LOCALHOST, port: int=DEFAULT_PORT, connector: ClientConnector=None):
        self.connector = connector
        if not connector:
            self.connector = SocketClientConnector(host=host, port=port)
        self.port = port
        self.host = host

    def send(self, message: StateDTO) -> Action:
        try:
            return self.connector.send(message)
        except Exception as exception:
            logger.info(f'error: {exception}')
            return Action(origin_command=message.command, suggested_command=message.command)

def send(self, message: StateDTO) -> Action:
    try:
        return self.connector.send(message)
    except Exception as exception:
        logger.info(f'error: {exception}')
        return Action(origin_command=message.command, suggested_command=message.command)

def send_files(command_id: str, user_name: str, files_values: FilesChangesValues):
    file_state = StateDTO(command_id=command_id, user_name=user_name, file_changes=files_values)
    clai_client = ClaiClient()
    clai_client.send(file_state)

def send_command_post_execute(command_id: str, user_name: str, result_code: str, stderr: str, processes: ProcessesValues, host: str=LOCALHOST, port: int=DEFAULT_PORT) -> Action:
    post_execute_state = StateDTO(command_id=command_id, user_name=user_name, result_code=result_code, stderr=stderr, processes=processes)
    clai_client = ClaiClient(host=host, port=port)
    return clai_client.send(post_execute_state)

def send_command(command_id: str, user_name: str, command_to_check: str, host: str=LOCALHOST, port: int=DEFAULT_PORT) -> Action:
    StateDTO.update_forward_refs()
    command_to_execute = StateDTO(command_id=command_id, user_name=user_name, command=command_to_check)
    clai_client = ClaiClient(host=host, port=port)
    return clai_client.send(command_to_execute)

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

@staticmethod
def serialize_message(data) -> State:
    StateDTO.update_forward_refs()
    dto = StateDTO(**json.loads(data))
    return State(command_id=dto.command_id, user_name=dto.user_name, command=dto.command, root=dto.root, processes=dto.processes, file_changes=dto.file_changes, network=dto.network, result_code=dto.result_code, stderr=dto.stderr)

def listen_client_sockets(self):
    self.connector.loop(self.process_message)
    self.remote_storage.wait()
    self.stats_tracker.wait()

def call_wa_skill(msg: str, name: str) -> List:
    wa_endpoint = services[name]
    try:
        response = requests.put(wa_endpoint, json={'text': msg}).json()
        if response['result'] == 'success':
            return (response['response']['output'], SUCCESS)
        else:
            return (response['result'], FAILURE)
    except Exception as ex:
        return ('Method failed with status ' + str(ex), FAILURE)

class Service:

    def __init__(self):
        self.state = {'ready_flag': False, 'threshold': 0.9, 'current_intent': None, 'current_branch': None, 'commit_details': None, 'has_done_add': False, 'has_done_commit': False}
        self.gh_session = requests.Session()
        self.gh_session.auth = (_github_username, _github_access_token)

    def __call__(self, *args, **kwargs):
        command = args[0]
        confidence = 0.0
        try:
            response = requests.post(_rasa_service, json={'text': command}).json()
            confidence = response['intent']['confidence']
            if confidence > self.state['threshold']:
                self.state['current_intent'] = response['intent']['name']
        except Exception as ex:
            print('Method failed with status ' + str(ex))
        if self.state['current_intent'] == 'commit':
            if not self.state['ready_flag']:
                self.state['ready_flag'] = True
                temp_description = 'Ready to {}. Press execute to continue.'.format(self.state['current_intent'])
                return [Action(suggested_command='git status | tee {}'.format(_path_to_log_file), execute=True, description=None, confidence=1.0), Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(temp_description).to_console(), confidence=1.0)]
        if command == 'execute':
            now = datetime.now()
            commit_message = now.strftime('%d/%m/%Y %H:%M:%S')
            stdout = open(_path_to_log_file).read().split('\n')
            commit_description = ''
            current_branch = None
            for line in stdout:
                if line.startswith('On branch'):
                    current_branch = line.split()[-1]
                if line.strip().startswith('modified:'):
                    commit_description += line.strip() + ' + '
            if commit_description:
                self.state['commit_details'] = commit_description
            if current_branch:
                self.state['current_branch'] = current_branch
            commit_description = self.state['commit_details']
            respond = Action(suggested_command='git commit -m "{}" -m "{}";'.format(commit_message, commit_description), execute=False, description=None, confidence=1.0)
            if self.state['has_done_add']:
                return respond
            else:
                return [Action(suggested_command='git add -A', execute=True, description='Adding untracked files...', confidence=1.0), respond]
        if self.state['current_intent'] == 'push':
            return Action(suggested_command='git push', execute=False, description=None, confidence=confidence)
        if self.state['current_intent'] == 'merge':
            merge_url = '{}/pulls'.format(_github_url)
            source = None
            target = 'master'
            for entity in response['entities']:
                if entity['entity'] == 'source':
                    source = entity['value']
                if entity['entity'] == 'target':
                    target = entity['value']
            if not source:
                source = self.state['current_branch']
            payload = {'title': 'Dummy PR from gitbot', 'body': 'Example from the `gitbot` screencast. This will not be merged.', 'head': source, 'base': target}
            ping_github = json.loads(self.gh_session.post(merge_url, json=payload).text)
            return Action(suggested_command=NOOP_COMMAND, execute=True, description='Success. Created PR {}'.format(ping_github['number']), confidence=confidence)
        if self.state['current_intent'] == 'comment':
            idx = 0
            comment = None
            for entity in response['entities']:
                if entity['entity'] == 'id':
                    idx = entity['value']
                if entity['entity'] == 'comment':
                    comment = entity['value']
            idx = command.split('<')[-1].split('>')[0]
            comment_url = '{}/issues/{}/comments'.format(_github_url, idx)
            payload = {'body': comment}
            ping_github = json.loads(self.gh_session.post(comment_url, json=payload).text)
            return Action(suggested_command=NOOP_COMMAND, execute=True, description='Success', confidence=confidence)

    def parse_command(self, command: str, stdout: str):
        if command.startswith('git checkout'):
            self.state['current_branch'] = None
        if command.startswith('git add'):
            self.state['has_done_add'] = True
        if command.startswith('commit'):
            self.state['has_done_add'] = False
            self.state['has_done_commit'] = True

def __init__(self):
    self.state = {'ready_flag': False, 'threshold': 0.9, 'current_intent': None, 'current_branch': None, 'commit_details': None, 'has_done_add': False, 'has_done_commit': False}
    self.gh_session = requests.Session()
    self.gh_session.auth = (_github_username, _github_access_token)

def get_plan_from_christian(domain: str, problem: str) -> list:
    try:
        data = parse.urlencode({'domain': domain, 'problem': problem}).encode()
        req = request.Request(_planning_domains, data=data)
        res = json.loads(request.urlopen(req).read())
        plan = [act['name'][1:-1].replace('-', '_') for act in res['result']['plan']]
        return plan
    except Exception as e:
        print(e)

class Provider:
    base_uri: str = ''
    excludes: list = []

    def __init__(self, name: str, description: str, section: dict):
        self.name = name
        self.description = description
        api_value: str = section.get('api')
        self.base_uri = api_value if api_value.endswith('/') else api_value + '/'
        if 'exclude' in section.keys():
            self.excludes = [excludeTarget.lower() for excludeTarget in section.get('exclude').split()]
        else:
            self.excludes = []
        if 'variants' in section.keys():
            self.variants = [variant.upper() for variant in section.get('variants').split()]
        else:
            self.variants = []

    def __str__(self) -> str:
        return self.description

    def __log_info__(self, message):
        logger.info(f'{self.name}: {message}')

    def __log_warning__(self, message):
        logger.warning(f'{self.name}: {message}')

    def __log_debug__(self, message):
        logger.debug(f'{self.name}: {message}')

    def __log_json__(self, data):
        output: List[str] = ['']
        getters: List[str] = []
        is_json_data: bool = False
        if isinstance(data, Request):
            output.append(f'{data.method} --> {data.url}')
            getters = ['files', 'data', 'json', 'params', 'auth', 'cookies', 'hooks']
        elif isinstance(data, Response):
            output.append(f'RESPONSE[{data.status_code}] <-- {data.url}')
            getters = ['apparent_encoding', 'cookies', 'elapsed', 'encoding', 'ok', 'status_code', 'reason', 'content']
        if data.headers.keys():
            output.append('.--[Headers]'.ljust(80, '-'))
            for key in data.headers.keys():
                if key == 'Content-Type':
                    if '/json' in data.headers[key]:
                        is_json_data = True
                line_header = f'|    {key}: '
                print_data: str = str(data.headers[key])
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
            output.append('`'.ljust(80, '-'))
        for method in getters:
            result = getattr(data, method)
            if method == 'content' and is_json_data:
                outstr = json.dumps(json.loads(result), indent=2)
                output.append(f'{method}: ' + outstr.replace('\n', '\n\t'))
            else:
                print_data: str = str(result)
                line_header = f'{method}: '
                if len(print_data) > 64:
                    print_data = f'{print_data[:50]} ... {print_data[-10:]}'
                output.append(f'{line_header}{print_data}')
        self.__log_info__('\n\t'.join(output))

    def __set_default_values__(self, args: dict, **kwargs) -> dict:
        for key in kwargs.keys():
            if key not in args:
                args[key] = kwargs[key]
        return args

    def __send_request__(self, method: str, uri: str, **kwargs) -> Response:
        kwargs = self.__set_default_values__(kwargs, headers={'Content-Type': 'application/json', 'Accept': '*/*'}, data=None, params=None)
        request: Request = Request(method, uri.rstrip('/'), headers=kwargs['headers'], data=kwargs['data'], params=kwargs['params'])
        self.__log_json__(request)
        session: Session = Session()
        response: Response = session.send(request=request.prepare())
        self.__log_json__(response)
        return response

    def __send_get_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='GET', uri=uri, **kwargs)

    def __send_post_request__(self, uri: str, **kwargs):
        return self.__send_request__(method='POST', uri=uri, **kwargs)

    def get_excludes(self) -> list:
        """Returns a list of operating systems that the search provider cannot
          be run from
        """
        return self.excludes

    def has_variants(self) -> bool:
        """Returns `True` if this search provider has more than one search
          variant
        """
        return len(self.variants) > 0

    def get_variants(self) -> list:
        """Returns a list of search variants supported by this search provider
        """
        return self.variants

    def can_run_on_this_os(self) -> bool:
        """Returns True if this search provider can be used on the client OS
        """
        if not self.excludes:
            return True
        os_name: str = os.uname().sysname.lower()
        return os_name not in self.excludes

    @abc.abstractclassmethod
    def extract_search_result(self, data: List[Dict]) -> str:
        """Given the result of an API search, extract the search result from it
        """
        pass

    @abc.abstractclassmethod
    def get_printable_output(self, data: List[Dict]) -> str:
        """Extract the result string from the data returned by an API search
        """
        pass

    @abc.abstractclassmethod
    def call(self, query: str, limit: int=1, **kwargs):
        """Perform a query on the API
        """
        pass

def __send_request__(self, method: str, uri: str, **kwargs) -> Response:
    kwargs = self.__set_default_values__(kwargs, headers={'Content-Type': 'application/json', 'Accept': '*/*'}, data=None, params=None)
    request: Request = Request(method, uri.rstrip('/'), headers=kwargs['headers'], data=kwargs['data'], params=kwargs['params'])
    self.__log_json__(request)
    session: Session = Session()
    response: Response = session.send(request=request.prepare())
    self.__log_json__(response)
    return response

class RLTKBandit(Orchestrator):

    def __init__(self):
        super(RLTKBandit, self).__init__()
        self._config_filepath = os.path.join(Path(__file__).parent.absolute(), 'config.yml')
        self._bandit_config_filepath = os.path.join(Path(__file__).parent.absolute(), 'bandit_config.json')
        self._noop_confidence = None
        self._agent = None
        self._n_actions = None
        self._action_order = None
        self._warm_start = None
        self._warm_start_type = None
        self._warm_start_kwargs = None
        self._reward_match_threshold = None
        self.load_bandit_state()
        self.load_state()
        self.warm_start_orchestrator()

    def load_bandit_state(self):
        with open(self._bandit_config_filepath, 'r') as conf_file:
            bandit_config = json.load(conf_file)
        self._noop_confidence = bandit_config['noop_confidence']
        self._warm_start = bandit_config['warm_start']
        self._warm_start_type = bandit_config['warm_start_config']['type']
        self._warm_start_kwargs = bandit_config['warm_start_config']['kwargs']
        self._reward_match_threshold = bandit_config.get('reward_match_threshold', 0.7)

    def get_orchestrator_state(self):
        state = {'agent': self._agent, 'action_order': self._action_order, 'warm_start': self._warm_start}
        return state

    def load_state(self):
        state = self.load()
        default_action_order = {self.noop_command: 0}
        self._agent = state.get('agent', None)
        if self._agent is None:
            self._agent = instantiate_from_file(self._config_filepath)
        self._action_order = state.get('action_order', None)
        if self._action_order is None:
            self._action_order = default_action_order
        self._n_actions = self._agent.num_actions
        self._warm_start = state.get('warm_start', self._warm_start)

    def warm_start_orchestrator(self):
        """
        Warm starts the orchestrator (pre-trains the weights) to suit a
        particular profile
        """

        def noop_setup():
            profile = 'noop-always'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'noop_position': 0}
            return (profile, kwargs)

        def ignore_skill_setup(skill_name):
            self.__add_to_action_order__(skill_name)
            profile = 'ignore-skill'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'skill_idx': self._action_order[skill_name]}
            return (profile, kwargs)

        def max_orchestrator_setup():
            profile = 'max-orchestrator'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions}
            return (profile, kwargs)

        def preferred_skill_orchestrator_setup(advantage_skill, disadvantage_skill):
            self.__add_to_action_order__(advantage_skill)
            self.__add_to_action_order__(disadvantage_skill)
            profile = 'preferred-skill'
            kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'advantage_skillidx': self._action_order[advantage_skill], 'disadvantage_skillidx': self._action_order[disadvantage_skill]}
            return (profile, kwargs)
        try:
            warm_start_methods = {'noop': noop_setup, 'ignore-skill': ignore_skill_setup, 'max-orchestrator': max_orchestrator_setup, 'preferred-skill': preferred_skill_orchestrator_setup}
            method = warm_start_methods[self._warm_start_type.lower()]
            profile, kwargs = method(**self._warm_start_kwargs)
            tids, contexts, arm_rewards = warm_start_datagen.get_warmstart_data(profile, **kwargs)
            self._agent.warm_start(tids, arm_rewards, contexts=contexts)
            self._warm_start = False
            self.save()
        except Exception as err:
            logger.warning('Exception in warm starting orchestrator. Error: ' + str(err))
            raise err

    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str):
        if not candidate_actions:
            return None
        if isinstance(candidate_actions, Action):
            candidate_actions = [candidate_actions]
        context = self.__build_context__(candidate_actions)
        action_idx = self._agent.choose(t_id=command.command_id, context=context, num_arms=1)
        suggested_action = self.__choose_action__(action_idx[0], candidate_actions)
        if suggested_action is None:
            suggested_action = Action(suggested_command=command.command)
        return suggested_action

    def __build_context__(self, candidate_actions: Optional[List[Union[Action, List[Action]]]]) -> np.array:
        context = [0.0] * self._n_actions
        noop_pos = self._action_order[self.noop_command]
        context[noop_pos] = self._noop_confidence
        for action in candidate_actions:
            self.__add_to_action_order__(action.agent_owner)
            pos = self._action_order[action.agent_owner]
            conf = self.__calculate_confidence__(action)
            context[pos] = conf
        return np.array(context, dtype=np.float)

    def __add_to_action_order__(self, agent_name):
        if agent_name in self._action_order:
            return
        max_action_order = max(self._action_order.values())
        self._action_order[agent_name] = max_action_order + 1

    def __choose_action__(self, action_idx: int, candidate_actions: Optional[List[Union[Action, List[Action]]]]):
        suggested_agent = None
        for agent_name, agent_idx in self._action_order.items():
            if agent_idx == action_idx:
                suggested_agent = agent_name
                break
        if suggested_agent == self.noop_command or suggested_agent is None:
            return None
        for action in candidate_actions:
            if action.agent_owner == suggested_agent:
                return action
        return None

    def record_transition(self, prev_state: TerminalReplayMemoryComplete, current_state_pre: TerminalReplayMemory):
        try:
            prev_state_pre = prev_state.pre_replay
            prev_state_post = prev_state.post_replay
            if prev_state_pre.command.action_suggested is None or prev_state_post.command.action_suggested is None or prev_state_post.command.action_suggested.suggested_command == self.noop_command:
                return
            reward = float(prev_state_post.command.suggested_executed)
            currently_executed_command = current_state_pre.command.command
            all_the_stuff_from_last_execution = prev_state_pre.command.action_suggested.suggested_command + prev_state_pre.command.action_suggested.description + prev_state_post.command.action_suggested.description
            base = set(currently_executed_command.split())
            reference = set(all_the_stuff_from_last_execution.split())
            match_score = len(base & reference) / len(base)
            reward += float(match_score > self._reward_match_threshold)
            self._agent.observe(prev_state.post_replay.command.command_id, reward)
        except Exception as err:
            logger.warning(f'Error in record_transition of bandit orchestrator. Error: {err}')

def load_state(self):
    state = self.load()
    default_action_order = {self.noop_command: 0}
    self._agent = state.get('agent', None)
    if self._agent is None:
        self._agent = instantiate_from_file(self._config_filepath)
    self._action_order = state.get('action_order', None)
    if self._action_order is None:
        self._action_order = default_action_order
    self._n_actions = self._agent.num_actions
    self._warm_start = state.get('warm_start', self._warm_start)

class Thresholder(Orchestrator):

    def __init__(self):
        super(Thresholder, self).__init__()
        self._threshold_pre = {}
        self._threshold_post = {}
        self._default_threshold = 0.2
        self.load_state()

    def get_orchestrator_state(self):
        state = {'threshold_pre': self._threshold_pre, 'threshold_post': self._threshold_post}
        return state

    def load_state(self):
        state = self.load()
        self._threshold_pre = state.get('threshold_pre', {})
        self._threshold_post = state.get('threshold_post', {})

    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Action]:
        if not candidate_actions:
            return None
        if isinstance(candidate_actions, Action):
            candidate_actions = [candidate_actions]
        max_confscore = float('-inf')
        best_action = None
        threshold_map = self._threshold_pre if pre_post_state == 'pre' else self._threshold_post
        for i, action in enumerate(candidate_actions):
            agent = agent_names[i]
            if agent not in threshold_map:
                threshold_map[agent] = self._default_threshold
            confidence = self.__calculate_confidence__(action)
            if confidence > threshold_map[agent] and confidence > max_confscore:
                max_confscore = confidence
                best_action = action
        return best_action

    def record_transition(self, prev_state: TerminalReplayMemoryComplete, current_state_pre: TerminalReplayMemory):
        prev_state_post = prev_state.post_replay
        if prev_state_post.command.action_suggested is None or prev_state_post.command.action_suggested.suggested_command == self.noop_command:
            return
        agent_executed = prev_state_post.command.action_suggested.agent_owner
        if prev_state_post.command.suggested_executed is True:
            self._threshold_pre[agent_executed] = self._threshold_pre.get(agent_executed, self._default_threshold) - 0.02
        else:
            self._threshold_pre[agent_executed] = self._threshold_pre.get(agent_executed, self._default_threshold) + 0.05
        self.save()

def load_state(self):
    state = self.load()
    self._threshold_pre = state.get('threshold_pre', {})
    self._threshold_post = state.get('threshold_post', {})

class GPT:
    """The main class for a user to interface with the OpenAI API.

    A user can add examples and set parameters of the API request.
    """

    def __init__(self, engine='davinci', temperature=0.5, max_tokens=100, input_prefix='input: ', input_suffix='\n', output_prefix='output: ', output_suffix='\n\n', append_output_prefix_to_query=False):
        self.examples = {}
        self.engine = engine
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.input_prefix = input_prefix
        self.input_suffix = input_suffix
        self.output_prefix = output_prefix
        self.output_suffix = output_suffix
        self.append_output_prefix_to_query = append_output_prefix_to_query
        self.stop = (output_suffix + input_prefix).strip()

    def set_api_key(self, key):
        """ Sets OpenAI API key """
        openai.api_key = key

    def add_example(self, ex):
        """Adds an example to the object.

        Example must be an instance of the Example class.
        """
        assert isinstance(ex, Example), 'Please create an Example object.'
        self.examples[ex.get_id()] = ex

    def delete_example(self, id):
        """Delete example with the specific id."""
        if id in self.examples:
            del self.examples[id]

    def get_example(self, id):
        """Get a single example."""
        return self.examples.get(id, None)

    def get_all_examples(self):
        """Returns all examples as a list of dicts."""
        return {k: v.as_dict() for k, v in self.examples.items()}

    def get_prime_text(self):
        """Formats all examples to prime the model."""
        return ''.join([self.format_example(ex) for ex in self.examples.values()])

    def get_engine(self):
        """Returns the engine specified for the API."""
        return self.engine

    def get_temperature(self):
        """Returns the temperature specified for the API."""
        return self.temperature

    def get_max_tokens(self):
        """Returns the max tokens specified for the API."""
        return self.max_tokens

    def craft_query(self, prompt):
        """Creates the query for the API request."""
        q = self.get_prime_text() + self.input_prefix + prompt + self.input_suffix
        if self.append_output_prefix_to_query:
            q = q + self.output_prefix
        return q

    def submit_request(self, prompt):
        """Calls the OpenAI API with the specified parameters."""
        response = openai.Completion.create(engine=self.get_engine(), prompt=self.craft_query(prompt), max_tokens=self.get_max_tokens(), temperature=self.get_temperature(), top_p=1, n=1, stream=False, stop=self.stop)
        return response

    def get_top_reply(self, prompt, strip_output_suffix=False):
        """Obtains the best result as returned by the API."""
        response = self.submit_request(prompt)
        response = response['choices'][0]['text']
        if strip_output_suffix:
            response = response[len(self.output_prefix):] if response.startswith(self.output_prefix) else response
        return response

    def format_example(self, ex):
        """Formats the input, output pair."""
        return self.input_prefix + ex.get_input() + self.input_suffix + self.output_prefix + ex.get_output() + self.output_suffix

def get_example(self, id):
    """Get a single example."""
    return self.examples.get(id, None)

def get_history_file_name():
    return os.environ.get('HISTFILE', os.path.expanduser('~/.bash_history'))

def execute_cmd(container, command):
    socket = container.exec_run(cmd='bash -l', stdin=True, tty=True, privileged=True, socket=True)
    wait_server_is_started()
    command_to_exec = command + '\n'
    socket.output._sock.send(command_to_exec.encode())
    data = read(socket)
    sleep(1)
    socket.output._sock.send(b'exit\n')
    return str(data)

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

def wait(self):
    if self.report_enable:
        self.queue.put(None)
        self.consumer_task.wait(timeout=3)

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

class StatsTracker:
    _instance = None
    manager = None
    queue = None
    pool = None
    consumer_stats = None
    anonymizer = None
    report_enable = None

    def __new__(cls, sync=False, anonymizer: Anonymizer=Anonymizer()):
        if cls._instance is None:
            cls._instance = super(StatsTracker, cls).__new__(cls)
            cls._instance.init(sync, anonymizer)
        return cls._instance

    def init(self, sync, anonymizer):
        if not sync:
            self.manager = mp.Manager()
            self.queue = self.manager.Queue()
            self.pool = mp.Pool(1)
            self.consumer_stats = None
        self.anonymizer = anonymizer
        self.report_enable = False

    @staticmethod
    def consumer(queue):
        while True:
            event = queue.get()
            if event is None:
                break
            logger.info(f'send_event: {event}')
            __send_event__(event)
            queue.task_done()
        logger.info('----STOP CONSUMING-----')

    def start(self, agent_datasource: AgentDatasource):
        logger.info(f'-Start tracker-')
        self.report_enable = agent_datasource.get_report_enable()
        if self.report_enable:
            self.consumer_stats = self.pool.map_async(self.consumer, (self.queue,))

    def wait(self):
        if self.report_enable:
            self.__store__(None)
            self.consumer_stats.wait(timeout=3)

    def log_activate_skills(self, user: str, skill_name: str):
        event = StatEvent(event_type='activate', user=self.anonymizer.anonymize(user), data={'skill': f'{skill_name}'})
        self.__store__(event)

    def log_deactivate_skills(self, user: str, skill_name: str):
        event = StatEvent(event_type='deactivate', user=self.anonymizer.anonymize(user), data={'skill': f'{skill_name}'})
        self.__store__(event)

    def log_install(self, user: str):
        if not self.report_enable:
            return
        event = StatEvent(event_type='install', user=self.anonymizer.anonymize(user), data={})
        __send_event__(event)

    def log_uninstall(self, user: str):
        if not self.report_enable:
            return
        event = StatEvent(event_type='uninstall', user=self.anonymizer.anonymize(user), data={})
        __send_event__(event)

    def __store__(self, event: StatEvent):
        if not self.report_enable:
            return
        try:
            logger.info(f'record stats -> {event}')
            self.queue.put(event)
        except Exception as err:
            logger.info(f'error sending: {err}')

@staticmethod
def consumer(queue):
    while True:
        event = queue.get()
        if event is None:
            break
        logger.info(f'send_event: {event}')
        __send_event__(event)
        queue.task_done()
    logger.info('----STOP CONSUMING-----')

def wait(self):
    if self.report_enable:
        self.__store__(None)
        self.consumer_stats.wait(timeout=3)

def log_activate_skills(self, user: str, skill_name: str):
    event = StatEvent(event_type='activate', user=self.anonymizer.anonymize(user), data={'skill': f'{skill_name}'})
    self.__store__(event)

def log_deactivate_skills(self, user: str, skill_name: str):
    event = StatEvent(event_type='deactivate', user=self.anonymizer.anonymize(user), data={'skill': f'{skill_name}'})
    self.__store__(event)

def log_install(self, user: str):
    if not self.report_enable:
        return
    event = StatEvent(event_type='install', user=self.anonymizer.anonymize(user), data={})
    __send_event__(event)

def log_uninstall(self, user: str):
    if not self.report_enable:
        return
    event = StatEvent(event_type='uninstall', user=self.anonymizer.anonymize(user), data={})
    __send_event__(event)

def __store__(self, event: StatEvent):
    if not self.report_enable:
        return
    try:
        logger.info(f'record stats -> {event}')
        self.queue.put(event)
    except Exception as err:
        logger.info(f'error sending: {err}')

class EmulatorDockerBridge:

    def __init__(self):
        self.manager = mp.Manager()
        self.queue = self.manager.Queue()
        self.queue_out = self.manager.Queue()
        self.pool = mp.Pool(1)
        self.consumer_messages = None
        self.emulator_docker_log_conector = EmulatorDockerLogConnector(mp.Pool(1), self.manager.Queue(), self.queue_out)

    def start(self):
        print(f'-Start docker bridge-')
        self.emulator_docker_log_conector.start()
        self.consumer_messages = self.pool.map_async(__consumer__, ((self.queue, self.emulator_docker_log_conector.log_queue, self.queue_out),))
        self.__internal_send__(DockerMessage(docker_command='start'))

    def stop_server(self):
        self.__internal_send__(DockerMessage(docker_command='request_stop'))
        self.consumer_messages.wait(timeout=3)

    def request_skills(self):
        self.__internal_send__(DockerMessage(docker_command='request_skills', message='clai skills'))

    def select_skill(self, skill_name):
        self.__internal_send__(DockerMessage(docker_command='select_skill', message=f'clai activate {skill_name}'))

    def unselect_skill(self, skill_name):
        self.__internal_send__(DockerMessage(docker_command='unselect_skill', message=f'clai deactivate {skill_name}'))

    def send_message(self, message: str):
        self.__internal_send__(DockerMessage(docker_command='send_message', message=message))

    def refresh_files(self):
        self.__internal_send__(DockerMessage(docker_command='refresh', message='clai reload'))

    def __internal_send__(self, event: DockerMessage):
        try:
            print(f'sending to queue -> {event}')
            self.queue.put(event)
        except Exception as err:
            print(f'error sending: {err}')

    def retrieve_message(self) -> Optional[DockerReply]:
        try:
            message = self.queue_out.get(block=False)
            return message
        except:
            return None

def start(self):
    print(f'-Start docker bridge-')
    self.emulator_docker_log_conector.start()
    self.consumer_messages = self.pool.map_async(__consumer__, ((self.queue, self.emulator_docker_log_conector.log_queue, self.queue_out),))
    self.__internal_send__(DockerMessage(docker_command='start'))

def stop_server(self):
    self.__internal_send__(DockerMessage(docker_command='request_stop'))
    self.consumer_messages.wait(timeout=3)

def request_skills(self):
    self.__internal_send__(DockerMessage(docker_command='request_skills', message='clai skills'))

def select_skill(self, skill_name):
    self.__internal_send__(DockerMessage(docker_command='select_skill', message=f'clai activate {skill_name}'))

def unselect_skill(self, skill_name):
    self.__internal_send__(DockerMessage(docker_command='unselect_skill', message=f'clai deactivate {skill_name}'))

def send_message(self, message: str):
    self.__internal_send__(DockerMessage(docker_command='send_message', message=message))

def refresh_files(self):
    self.__internal_send__(DockerMessage(docker_command='refresh', message='clai reload'))

def __internal_send__(self, event: DockerMessage):
    try:
        print(f'sending to queue -> {event}')
        self.queue.put(event)
    except Exception as err:
        print(f'error sending: {err}')

def retrieve_message(self) -> Optional[DockerReply]:
    try:
        message = self.queue_out.get(block=False)
        return message
    except:
        return None

def __start_docker():
    docker_client = docker.from_env()
    image = __get_image(docker_client)
    docker_container = docker_client.containers.run(image=image.id, detach=True)
    my_clai = Container(docker_container)
    wait_for_callable('Waiting for container to be ready', my_clai.ready)
    print(f'container run {my_clai.status} {my_clai.name}')
    return my_clai

def __consumer__(args):
    queue, log_queue, queue_out = args
    my_clai = None
    socket = None
    print('starting reading from the queue')
    while True:
        docker_message: DockerMessage = queue.get()
        if docker_message is None:
            break
        print(f'message_received: {docker_message.docker_command}:{docker_message.message}')
        if docker_message.docker_command == 'start':
            my_clai = __start_docker()
            log_queue.put(DockerMessage(docker_command='start_logger', message=my_clai.name))
        elif docker_message.docker_command == 'send_message' or docker_message.docker_command == 'request_skills' or docker_message.docker_command == 'unselect_skill' or (docker_message.docker_command == 'refresh') or (docker_message.docker_command == 'select_skill'):
            if my_clai:
                print(f'socket {socket}')
                if not socket:
                    socket = my_clai.exec_run(cmd='bash -l', stdin=True, tty=True, privileged=True, socket=True)
                    wait_server_is_started()
                if docker_message.docker_command == 'refresh':
                    copy_files(my_clai)
                command_to_exec = docker_message.message + '\n'
                socket.output._sock.send(command_to_exec.encode())
                stdout = read(socket)
                reply = None
                if docker_message.docker_command == 'request_skills' or docker_message.docker_command == 'unselect_skill':
                    reply = DockerReply(docker_reply='skills', message=stdout)
                elif docker_message.docker_command == 'send_message':
                    socket.output._sock.send('clai last-info\n'.encode())
                    info = read(socket)
                    reply = DockerReply(docker_reply='reply_message', message=stdout, info=info)
                if reply:
                    queue_out.put(reply)
        elif docker_message == 'request_stop':
            if my_clai:
                my_clai.kill()
                break
        queue.task_done()
    print('----STOP CONSUMING-----')

def __log_consumer__(args):
    queue, queue_out = args
    my_clai: Container = None
    socket = None
    print('starting reading the log queue')
    while True:
        docker_message: DockerMessage = queue.get()
        if docker_message.docker_command == 'start_logger':
            docker_client = docker.from_env()
            docker_container = docker_client.containers.get(docker_message.message)
            my_clai = Container(docker_container)
        if my_clai:
            if not socket:
                socket = my_clai.exec_run(cmd='bash -l', stdin=True, tty=True, privileged=True, socket=True)
                wait_server_is_started()
            socket.output._sock.send('clai "none" tail -f /var/tmp/app.log\n'.encode())
            read(socket, lambda chunk: queue_out.put(DockerReply(docker_reply='log', message=chunk)))
        queue.task_done()
        queue.put(DockerMessage(docker_command='log'))

class ClaiEmulator:

    def __init__(self, emulator_docker_bridge: EmulatorDockerBridge):
        self.presenter = EmulatorPresenter(emulator_docker_bridge, self.on_skills_ready, self.on_server_running, self.on_server_stopped)
        self.log_window = None

    def launch(self):
        self.root = tk.Tk()
        self.root.wait_visibility(self.root)
        self.title_font = Font(size=16, weight='bold')
        self.bold_font = Font(weight='bold')
        self.root.geometry('900x600')
        style = ttk.Style(self.root)
        style.configure('TLable', bg='black')
        self.add_toolbar(self.root)
        self.add_send_command_box(self.root)
        self.add_list_commands(self.root)
        self.root.protocol('WM_DELETE_WINDOW', lambda root=self.root: self.on_closing(root))
        self.root.createcommand('exit', lambda root=self.root: self.on_closing(root))
        self.root.mainloop()

    def on_closing(self, root):
        if messagebox.askokcancel('Quit', 'Do you want to quit?'):
            self.presenter.stop_server()
            root.destroy()

    def on_skills_ready(self, skills_as_array: List[str]):
        self.selected_skills_dropmenu.configure(state='active')
        self.selected_skills_dropmenu['menu'].delete(0, 'end')
        for skill in skills_as_array[1:-1]:
            name_skill, active = self.clear_text(skill)
            self.selected_skills_dropmenu['menu'].add_command(label=name_skill, command=tk._setit(self.selected_skills, name_skill))
            if active:
                self.presenter.current_active_skill = self.extract_skill_name(name_skill)[0]
                self.selected_skills.set(name_skill)

    def on_server_running(self):
        self.run_button.configure(image=self.stop_image)
        self.loading_text.set('Starting CLAI. It will take a while')
        self.__listen_messages()

    def on_server_stopped(self):
        self.run_button.configure(image=self.run_image)

    def on_skill_selected(self, *args):
        self.loading_text.set('')
        print(f'new skills {self.selected_skills.get()}')
        skill_name = self.extract_skill_name(self.selected_skills.get())[0]
        self.presenter.select_skill(skill_name)

    def add_detail_label(self, parent: ttk.Frame, title: str, text_value: str, side: str):
        row = ttk.Frame(parent)
        title_label = ttk.Label(parent, text=title, font=self.bold_font, anchor='n', padding=(10, 0, 0, 0))
        title_label.pack(side=side, fill=tk.BOTH)
        row_value = ttk.Label(parent, text=text_value, wraplength=250, anchor='nw')
        if side == tk.LEFT:
            row_value.pack(side=side, fill=tk.BOTH, expand=True)
        else:
            row_value.pack(side=side, fill=tk.BOTH, before=title_label)
        row.pack(side=side, fill=tk.BOTH, expand=True)

    def add_row(self, response: str, info: InfoDebug):
        response = self.clean_message(response)
        toggled_frame = ToggledFrame(self.frame, text=response, relief=tk.RAISED, borderwidth=1)
        toggled_frame.pack(fill='x', expand=1, pady=2, padx=2, anchor='n')
        first_row = ttk.Frame(toggled_frame.sub_frame)
        first_row.pack(fill='x', expand=True)
        self.add_detail_label(first_row, 'Original:', info.command, side=tk.LEFT)
        self.add_detail_label(first_row, 'Id:', info.command_id, side=tk.RIGHT)
        second_row = ttk.Frame(toggled_frame.sub_frame)
        second_row.pack(fill='x', expand=True)
        self.add_detail_label(second_row, 'Description:', self.remove_emoji(info.action_suggested.description), tk.LEFT)
        self.add_detail_label(second_row, 'Confidence:', f'{info.action_suggested.confidence}', tk.RIGHT)
        self.add_detail_label(second_row, 'Force:', f'{info.action_suggested.execute}', tk.RIGHT)
        third_row = ttk.Frame(toggled_frame.sub_frame)
        third_row.pack(fill='x', expand=True)
        self.add_detail_label(third_row, 'Agent:', text_value=info.action_suggested.agent_owner, side=tk.LEFT)
        self.add_detail_label(third_row, 'Sugestion:', text_value=info.action_suggested.suggested_command, side=tk.RIGHT)
        self.add_detail_label(third_row, 'Applied:', text_value=f'{info.already_processed}', side=tk.RIGHT)
        fourth_row = ttk.Frame(toggled_frame.sub_frame)
        fourth_row.pack(fill='x', expand=True)
        process_text = ','.join(list(map(lambda process: process.name, info.processes.last_processes)))
        self.add_detail_label(fourth_row, 'Processes:', text_value=f'{process_text}', side=tk.LEFT)
        post_title_frame = ttk.Frame(toggled_frame.sub_frame)
        post_title_frame.pack(fill='x', expand=True)
        ttk.Label(post_title_frame, text=f'Post execution', anchor='center', font=self.title_font).pack(side=tk.LEFT, padx=10, fill='x', expand=True)
        fifth_row = ttk.Frame(toggled_frame.sub_frame)
        fifth_row.pack(fill='x', expand=True)
        post_description = ''
        post_confidence = 0
        if info.action_post_suggested:
            post_description = info.action_post_suggested.description
            post_confidence = info.action_post_suggested.confidence
        self.add_detail_label(fifth_row, 'Description:', text_value=f'{self.remove_emoji(post_description)}', side=tk.LEFT)
        self.add_detail_label(fifth_row, 'Confidence:', text_value=f'{post_confidence}', side=tk.RIGHT)
        self.root.after(100, self.__scroll_down_after_create)

    def __scroll_down_after_create(self):
        self.canvas.yview_moveto(1.0)

    def add_send_command_box(self, root):
        button_bar_frame = tk.Frame(root, bd=1, relief=tk.RAISED)
        send_button = tk.Button(button_bar_frame, padx=10, text=u'✓', command=self.on_send_click)
        send_button.pack(side=tk.RIGHT, padx=5)
        self.text_input = tk.StringVar()
        send_edit_text = tk.Entry(button_bar_frame, textvariable=self.text_input)
        send_edit_text.bind('<Return>', self.on_enter)
        send_edit_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        button_bar_frame.pack(side=tk.BOTTOM, pady=2, fill=tk.X)

    def add_toolbar(self, root):
        toolbar = tk.Frame(root, bd=1, relief=tk.RAISED)
        self.add_play_button(toolbar)
        self.add_refresh_button(toolbar)
        self.add_log_button(toolbar)
        self.add_skills_selector(root, toolbar)
        self.add_loading_progress(toolbar)
        toolbar.pack(side=tk.TOP, fill=tk.X)

    def add_skills_selector(self, root, toolbar):
        label = ttk.Label(toolbar, text=u'Skills')
        label.pack(side=tk.LEFT, padx=2)
        self.selected_skills = tk.StringVar(root)
        self.selected_skills.set('')
        self.selected_skills.trace('w', self.on_skill_selected)
        self.selected_skills_dropmenu = tk.OptionMenu(toolbar, self.selected_skills, [])
        self.selected_skills_dropmenu.configure(state='disabled')
        self.selected_skills_dropmenu.pack(side=tk.LEFT, padx=2)

    def add_play_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        self.run_image = tk.PhotoImage(file=f'{path}/run.gif')
        self.stop_image = tk.PhotoImage(file=f'{path}/stop.gif')
        self.run_button = ttk.Button(toolbar, image=self.run_image, command=self.on_run_click)
        self.run_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_refresh_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        temp_image = Image.open(f'{path}/refresh.png')
        self.refresh_image = ImageTk.PhotoImage(temp_image)
        refresh_button = ttk.Button(toolbar, image=self.refresh_image, command=self.on_refresh_click)
        refresh_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_log_button(self, toolbar):
        path = os.path.dirname(os.path.abspath(__file__))
        temp_image = Image.open(f'{path}/log.png')
        self.log_image = ImageTk.PhotoImage(temp_image)
        log_button = ttk.Button(toolbar, image=self.log_image, command=self.open_log_window)
        log_button.pack(side=tk.LEFT, padx=2, pady=2)

    def add_loading_progress(self, toolbar):
        self.loading_text = tk.StringVar()
        loading_label = ttk.Label(toolbar, textvariable=self.loading_text)
        loading_label.pack(side=tk.LEFT, padx=2)

    def open_log_window(self):
        if not self.log_window:
            self.log_window = LogWindow(self.root, self.presenter)

    def on_enter(self, event):
        self.send_command(self.text_input.get())

    def on_send_click(self):
        self.send_command(self.text_input.get())

    @staticmethod
    def clean_message(text: str):
        text = text[text.find('\n'):]
        text = re.sub('[[0-9;]*m', '', text)
        return text[:text.find(']0;') - 3]

    def send_command(self, command):
        self.presenter.send_message(command)
        self.text_input.set('')

    def on_run_click(self):
        if not self.presenter.server_running:
            self.presenter.run_server()
        else:
            self.presenter.stop_server()

    def on_refresh_click(self):
        self.presenter.refresh_files()

    @staticmethod
    def on_configure(canvas):
        canvas.configure(scrollregion=canvas.bbox('all'))

    def canvas_resize(self, event, canvas):
        canvas_width = event.width
        canvas.itemconfig(self.canvas_frame, width=canvas_width)

    def add_list_commands(self, root):
        canvas = tk.Canvas(root, borderwidth=0)
        self.frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(root, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        self.canvas_frame = canvas.create_window((4, 4), window=self.frame, anchor='nw')
        canvas.bind('<Configure>', lambda event, canvas=canvas: self.canvas_resize(event, canvas))
        self.frame.bind('<Configure>', lambda event, canvas=canvas: self.on_configure(canvas))
        self.frame.bind_all('<MouseWheel>', lambda event, canvas=canvas: canvas.yview_scroll(-1 * event.delta, 'units'))
        self.canvas = canvas

    @staticmethod
    def clear_text(skill):
        active = '[x]' in skill
        skill_without_tick = skill.replace('[x]\x1b[32m ', '').replace('\x1b[0m', '').replace('[ ]', '').strip()
        return (skill_without_tick, active)

    @staticmethod
    def extract_skill_name(skill):
        installed = '(Installed)' in skill
        return (skill.replace('(Installed)', '').replace('(Not Installed)', '').strip(), installed)

    @staticmethod
    def remove_emoji(description):
        if not description:
            return ''
        char_list = [description[j] for j in range(len(description)) if ord(description[j]) in range(65536)]
        description = ''
        for char in char_list:
            description = description + char
        return description

    def __listen_messages(self):
        self.presenter.retrieve_messages(self.add_row)
        self.root.after(100, self.__listen_messages)

def on_enter(self, event):
    self.send_command(self.text_input.get())

def on_send_click(self):
    self.send_command(self.text_input.get())

