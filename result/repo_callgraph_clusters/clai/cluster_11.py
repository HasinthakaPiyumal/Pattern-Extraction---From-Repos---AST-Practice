# Cluster 11

def stat_uninstall(bin_path):
    agent_datasource = AgentDatasource(config_storage=ConfigStorage(alternate_path=f'{bin_path}/configPlugins.json'))
    report_enable = agent_datasource.get_report_enable()
    stats_tracker = StatsTracker(sync=True, anonymizer=Anonymizer(alternate_path=f'{bin_path}/anonymize.json'))
    stats_tracker.report_enable = report_enable
    login = getpass.getuser()
    stats_tracker.log_uninstall(login)
    print('record uninstall')

def save_report_info(unassisted, agent_datasource, bin_path, demo_mode):
    enable_report = True
    if demo_mode:
        enable_report = False
    elif not unassisted:
        enable_report = ask_to_user('Would you like anonymously send debugging and usage informationto the CLAI team in order to help improve it?')
    agent_datasource.mark_report_enable(enable_report)
    stats_tracker = StatsTracker(sync=True, anonymizer=Anonymizer(alternate_path=f'{bin_path}/anonymize.json'))
    stats_tracker.report_enable = enable_report
    stats_tracker.log_install(getpass.getuser())

class ClaiUnselectCommandRunner(CommandRunner):
    UNSELECT_DIRECTIVE = 'clai deactivate'

    def __init__(self, config_storage: ConfigStorage, agent_datasource: AgentDatasource):
        self.config_storage = config_storage
        self.agent_datasource = agent_datasource
        self.stats_tracker = StatsTracker()

    def execute(self, state: State) -> Action:
        plugin_to_select = state.command.replace(f'{self.UNSELECT_DIRECTIVE}', '').strip()
        plugin_to_select = extract_quoted_agent_name(plugin_to_select)
        selected = self.agent_datasource.unselect_plugin(plugin_to_select, state.user_name)
        if selected:
            self.stats_tracker.log_deactivate_skills(state.user_name, plugin_to_select)
            plugins_config = self.config_storage.read_config(state.user_name)
            if plugins_config.selected is not None and selected.name in plugins_config.selected:
                plugins_config.selected.remove(selected.name)
            self.config_storage.store_config(plugins_config, state.user_name)
        action_to_return = create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())
        action_to_return.origin_command = state.command
        return action_to_return

def __init__(self, config_storage: ConfigStorage, agent_datasource: AgentDatasource):
    self.config_storage = config_storage
    self.agent_datasource = agent_datasource
    self.stats_tracker = StatsTracker()

class ClaiSelectCommandRunner(CommandRunner, PostCommandRunner):
    SELECT_DIRECTIVE = 'clai activate'

    def __init__(self, config_storage: ConfigStorage, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource
        self.config_storage = config_storage
        self.stats_tracker = StatsTracker()

    def execute(self, state: State) -> Action:
        plugin_to_select = state.command.replace(f'{self.SELECT_DIRECTIVE}', '').strip()
        plugin_to_select = extract_quoted_agent_name(plugin_to_select)
        agent_descriptor = self.agent_datasource.get_agent_descriptor(plugin_to_select)
        plugins_config = self.config_storage.read_config(None)
        if not agent_descriptor:
            return create_error_select(plugin_to_select)
        if agent_descriptor and (not agent_descriptor.installed):
            logger.info(f'installing dependencies of plugin {agent_descriptor.name}')
            command = f'$CLAI_PATH/fileExist.sh {agent_descriptor.pkg_name} $CLAI_PATH{(' --user' if plugins_config.user_install else '')}'
            action_selected_to_return = Action(suggested_command=command, execute=True)
        else:
            self.select_plugin(plugin_to_select, state)
            action_selected_to_return = Action(suggested_command=':', execute=True)
        action_selected_to_return.origin_command = state.command
        return action_selected_to_return

    def select_plugin(self, plugin_to_select, state):
        selected_plugin = self.agent_datasource.select_plugin(plugin_to_select, state.user_name)
        if selected_plugin:
            self.stats_tracker.log_activate_skills(state.user_name, plugin_to_select)
            plugins_config = self.config_storage.read_config(state.user_name)
            if plugins_config.selected is None:
                plugins_config.selected = [selected_plugin.name]
            elif selected_plugin.name not in plugins_config.selected:
                plugins_config.selected.append(selected_plugin.name)
            self.config_storage.store_config(plugins_config, state.user_name)
        return create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())

    def execute_post(self, state: State) -> Action:
        plugin_to_select = state.command.replace(f'{self.SELECT_DIRECTIVE}', '').strip()
        plugin_to_select = extract_quoted_agent_name(plugin_to_select)
        agent_descriptor = self.agent_datasource.get_agent_descriptor(plugin_to_select)
        if not agent_descriptor:
            return Action()
        if state.result_code == '0':
            self.agent_datasource.mark_plugins_as_installed(plugin_to_select, state.user_name)
            return self.select_plugin(plugin_to_select, state)
        return create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())

def __init__(self, config_storage: ConfigStorage, agent_datasource: AgentDatasource):
    self.agent_datasource = agent_datasource
    self.config_storage = config_storage
    self.stats_tracker = StatsTracker()

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

def init(self):
    self.manager = mp.Manager()
    self.queue = self.manager.Queue()
    self.consumer_task = None
    self.pool = mp.Pool(1)
    self.report_enable = False
    self.anonymizer = Anonymizer()

def start(self, agent_datasource: AgentDatasource):
    logger.info(f'-Start sender-')
    self.report_enable = agent_datasource.get_report_enable()
    if self.report_enable:
        self.consumer_task = self.pool.map_async(self.consumer, (self.queue,))

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

def init(self, sync, anonymizer):
    if not sync:
        self.manager = mp.Manager()
        self.queue = self.manager.Queue()
        self.pool = mp.Pool(1)
        self.consumer_stats = None
    self.anonymizer = anonymizer
    self.report_enable = False

def start(self, agent_datasource: AgentDatasource):
    logger.info(f'-Start tracker-')
    self.report_enable = agent_datasource.get_report_enable()
    if self.report_enable:
        self.consumer_stats = self.pool.map_async(self.consumer, (self.queue,))

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

def __init__(self):
    self.manager = mp.Manager()
    self.queue = self.manager.Queue()
    self.queue_out = self.manager.Queue()
    self.pool = mp.Pool(1)
    self.consumer_messages = None
    self.emulator_docker_log_conector = EmulatorDockerLogConnector(mp.Pool(1), self.manager.Queue(), self.queue_out)

class EmulatorDockerLogConnector:

    def __init__(self, pool, log_queue, queue_out):
        self.pool_log = pool
        self.consumer_log = None
        self.log_queue = log_queue
        self.queue_out = queue_out

    def start(self):
        self.consumer_log = self.pool_log.map_async(__log_consumer__, ((self.log_queue, self.queue_out),))

def start(self):
    self.consumer_log = self.pool_log.map_async(__log_consumer__, ((self.log_queue, self.queue_out),))

