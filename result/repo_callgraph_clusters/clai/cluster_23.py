# Cluster 23

def test_should_return_the_command_to_get_the_plugin_from_url_and_move_it_into_plugin_folder_server():
    agent_datasource = AgentDatasource()
    clai_install_command_runner = ClaiInstallCommandRunner(agent_datasource)
    command_to_execute = clai_install_command_runner.execute(CLAI_INSTALL_STATE_URL)
    dir_to_install = CLAI_INSTALL_STATE_URL.command.replace(f'{'clai install'}', '').strip()
    assert command_to_execute.suggested_command == f'cd $CLAI_PATH/clai/server/plugins && curl -O {dir_to_install}'

def test_should_return_the_command_to_get_the_plugin_from_route_and_move_it_into_plugin_folder_server(mocker):
    mock_exisit = mocker.patch('os.path.exists')
    mock_exisit.return_value = True
    mock_exisit = mocker.patch('os.path.isdir')
    mock_exisit.return_value = True
    agent_datasource = AgentDatasource()
    clai_install_command_runner = ClaiInstallCommandRunner(agent_datasource)
    command_to_execute = clai_install_command_runner.execute(CLAI_INSTALL_STATE_FOLDER)
    dir_to_install = CLAI_INSTALL_STATE_FOLDER.command.replace(f'{'clai install'}', '').strip()
    assert command_to_execute.suggested_command == f'cp -R {dir_to_install} $CLAI_PATH/clai/server/plugins'

def test_should_return_the_message_error_when_the_folder_doesnt_exist(mocker):
    mock_exisit = mocker.patch('os.path.exists')
    mock_exisit.return_value = False
    mock_exisit = mocker.patch('os.path.isdir')
    mock_exisit.return_value = False
    agent_datasource = AgentDatasource()
    clai_install_command_runner = ClaiInstallCommandRunner(agent_datasource)
    command_to_execute = clai_install_command_runner.execute(CLAI_INSTALL_STATE_FOLDER)
    dir_to_install = CLAI_INSTALL_STATE_FOLDER.command.replace(f'{'clai install'}', '').strip()
    assert command_to_execute.suggested_command == ':'
    assert command_to_execute.description == create_error_install(dir_to_install).description

class MockExecutor(AgentExecutor):

    def execute_agents(self, command: State, agents: List[Agent]) -> List[Action]:
        return list(map(lambda agent: self.execute(command, agent), agents))

    @staticmethod
    def execute(command: State, agent: Agent) -> Action:
        action = agent.execute(command)
        if not action:
            action = Action()
        return action

@staticmethod
def execute(command: State, agent: Agent) -> Action:
    action = agent.execute(command)
    if not action:
        action = Action()
    return action

def test_should_return_the_start_server_command_when_received_clai_start(mocker):
    with pytest.raises(SystemExit):
        mock_override_last_command = mocker.patch('clai.process_command.override_last_command')
        process_command(ANY_ID, ANY_USER, COMMAND_START_SERVER)
        mock_override_last_command.assert_called_once_with(f'\n{START_SERVER_COMMAND_TO_EXECUTE}\n')

def mock_input_console(mocker, value):
    mocker.patch('builtins.input', return_value=value)

@pytest.yield_fixture(scope='session', autouse=True)
def mock_executor():
    with mock.patch('clai.server.agent_runner.agent_executor', MockExecutor()) as _fixture:
        yield _fixture

class AgentRunner:

    def __init__(self, agent_datasource: AgentDatasource, orchestrator_provider: OrchestratorProvider):
        self.agent_datasource = agent_datasource
        self.orchestrator_provider = orchestrator_provider
        self.remote_storage = ActionRemoteStorage()
        self.orchestrator_storage = OrchestratorStorage(orchestrator_provider, self.remote_storage)
        self._pre_exec_id = 'pre'
        self._post_exec_id = 'post'

    def store_pre_orchestrator_memory(self, command: State, agent_list: List[Agent], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, suggested_command: Optional[Action]):
        agent_names = [agent.agent_name for agent in agent_list]
        state = TerminalReplayMemory(command, agent_names, candidate_actions, force_response, suggested_command)
        self.orchestrator_storage.store_pre(state)

    def store_post_orchestrator_memory(self, command: State, agent_list: List[Agent], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, suggested_command: Optional[Action]):
        agent_names = [agent.agent_name for agent in agent_list]
        state = TerminalReplayMemory(command, agent_names, candidate_actions, force_response, suggested_command)
        self.orchestrator_storage.store_post(state)

    def select_best_candidate(self, command: State, agent_list: List[Agent], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Union[Action, List[Action]]]:
        agent_names = [agent.agent_name for agent in agent_list]
        orchestrator = self.orchestrator_provider.get_current_orchestrator()
        suggested_command = orchestrator.choose_action(command=command, agent_names=agent_names, candidate_actions=candidate_actions, force_response=force_response, pre_post_state=pre_post_state)
        if not suggested_command:
            suggested_command = Action()
        return suggested_command

    def process(self, command: State, ignore_threshold: bool, force_agent: str=None) -> Optional[Union[Action, List[Action]]]:
        if force_agent:
            plugin_instances = self.agent_datasource.get_instances(command.user_name, force_agent)
            ignore_threshold = True
        else:
            plugin_instances = self.agent_datasource.get_instances(command.user_name)
        candidate_actions = agent_executor.execute_agents(command, plugin_instances)
        suggested_command = self.select_best_candidate(command, plugin_instances, candidate_actions, ignore_threshold, self._pre_exec_id)
        if not suggested_command:
            suggested_command = Action()
        self.store_pre_orchestrator_memory(command, plugin_instances, candidate_actions, ignore_threshold, suggested_command)
        if isinstance(suggested_command, Action):
            if not suggested_command.suggested_command:
                suggested_command.suggested_command = command.command
        else:
            for action in suggested_command:
                if not action.suggested_command:
                    action.suggested_command = command.command
        return suggested_command

    def process_post(self, command: State, ignore_threshold: bool) -> Optional[Action]:
        plugin_instances = self.agent_datasource.get_instances(command.user_name)
        candidate_actions = []
        for plugin_instance in plugin_instances:
            action_post_executed = plugin_instance.post_execute(command)
            action_post_executed.agent_owner = plugin_instance.agent_name
            if action_post_executed:
                candidate_actions.append(action_post_executed)
        suggested_command = self.select_best_candidate(command, plugin_instances, candidate_actions, ignore_threshold, self._post_exec_id)
        self.store_post_orchestrator_memory(command, plugin_instances, candidate_actions, ignore_threshold, suggested_command)
        if not suggested_command:
            suggested_command = Action()
        if not suggested_command.suggested_command:
            suggested_command.suggested_command = command.command
        return suggested_command

def process(self, command: State, ignore_threshold: bool, force_agent: str=None) -> Optional[Union[Action, List[Action]]]:
    if force_agent:
        plugin_instances = self.agent_datasource.get_instances(command.user_name, force_agent)
        ignore_threshold = True
    else:
        plugin_instances = self.agent_datasource.get_instances(command.user_name)
    candidate_actions = agent_executor.execute_agents(command, plugin_instances)
    suggested_command = self.select_best_candidate(command, plugin_instances, candidate_actions, ignore_threshold, self._pre_exec_id)
    if not suggested_command:
        suggested_command = Action()
    self.store_pre_orchestrator_memory(command, plugin_instances, candidate_actions, ignore_threshold, suggested_command)
    if isinstance(suggested_command, Action):
        if not suggested_command.suggested_command:
            suggested_command.suggested_command = command.command
    else:
        for action in suggested_command:
            if not action.suggested_command:
                action.suggested_command = command.command
    return suggested_command

def process_post(self, command: State, ignore_threshold: bool) -> Optional[Action]:
    plugin_instances = self.agent_datasource.get_instances(command.user_name)
    candidate_actions = []
    for plugin_instance in plugin_instances:
        action_post_executed = plugin_instance.post_execute(command)
        action_post_executed.agent_owner = plugin_instance.agent_name
        if action_post_executed:
            candidate_actions.append(action_post_executed)
    suggested_command = self.select_best_candidate(command, plugin_instances, candidate_actions, ignore_threshold, self._post_exec_id)
    self.store_post_orchestrator_memory(command, plugin_instances, candidate_actions, ignore_threshold, suggested_command)
    if not suggested_command:
        suggested_command = Action()
    if not suggested_command.suggested_command:
        suggested_command.suggested_command = command.command
    return suggested_command

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

def __process_command_ai(self, message) -> List[Action]:
    if message.command == STOP_COMMAND:
        self.server_status_datasource.running = False
        return [Action()]
    command_runner = self.command_runner_factory.provide_command_runner(message.command, self.agent_runner)
    action = command_runner.execute(message)
    if isinstance(action, Action):
        return [action]
    return action

class AgentDatasource:

    def __init__(self, config_storage: ConfigStorage=config):
        self.__selected_plugin: Dict[str, Optional[List[pkg.ModuleInfo]]] = {}
        self.__plugins: Dict[str, Agent] = {}
        self.num_workers = 4
        self.config_storage = config_storage
        self.current_orchestrator = None

    @staticmethod
    def get_path():
        return clai.server.plugins.__path__

    def preload_plugins(self):
        all_descriptors = self.all_plugins()
        installed_agents = list(filter(lambda value: value.installed, all_descriptors))
        for descriptor in installed_agents:
            self.start_agent(descriptor)
        logger.info('finish init')

    def start_agent(self, descriptor):
        agent_datasource_executor.execute(self.load_agent, descriptor.pkg_name)

    def load_agent(self, name: str):
        try:
            plugin = importlib.import_module(f'clai.server.plugins.{name}.{name}', package=name)
            importlib.invalidate_caches()
            plugin = importlib.reload(plugin)
            for _, class_member in inspect.getmembers(plugin, inspect.isclass):
                if issubclass(class_member, Agent) and class_member is not Agent:
                    member = class_member()
                    if not member:
                        member = ClaiIdentity()
                    self.__plugins[name] = member
                    member.init_agent()
                    member.ready = True
                    logger.info(f'{name} is ready')
        except Exception as ex:
            logger.info(f'load agent exception: {ex}')

    def get_instances(self, user_name: str, agent_to_select: str=None) -> List[Agent]:
        select_plugins_by_user = self.__get_selected_by_user(user_name)
        if select_plugins_by_user is None:
            self.init_plugin_config(user_name)
            select_plugins_by_user = self.__get_selected_by_user(user_name)
        if agent_to_select:
            agent_descriptor_selected = self.get_agent_descriptor(agent_to_select)
            if agent_descriptor_selected is None:
                return [ClaiIdentity()]
            select_plugins_by_user = list(filter(lambda value: value.name == agent_descriptor_selected.pkg_name, select_plugins_by_user))
        if agent_to_select:
            agent_descriptor_selected = self.get_agent_descriptor(agent_to_select)
            if agent_descriptor_selected is None:
                return [ClaiIdentity()]
            select_plugins_by_user = list(filter(lambda value: value.name == agent_descriptor_selected.pkg_name, select_plugins_by_user))
        agents = []
        for select_plugin_by_user in select_plugins_by_user:
            if select_plugin_by_user.name in self.__plugins:
                agent = self.__plugins[select_plugin_by_user.name]
                if agent.ready:
                    agents.append(agent)
        if not agents:
            agents.append(ClaiIdentity())
        return agents

    @staticmethod
    def load_descriptors(path, name) -> AgentDescriptor:
        file_path = os.path.join(path, 'manifest.properties')
        if os.path.exists(file_path):
            config_parser = configparser.ConfigParser()
            config_parser.read(file_path)
            default = z_default = False
            if config_parser.has_option('DEFAULT', 'default'):
                default = config_parser.getboolean('DEFAULT', 'default')
            if config_parser.has_option('DEFAULT', 'z_default'):
                z_default = config_parser.getboolean('DEFAULT', 'z_default')
            exclude = []
            if config_parser.has_option('DEFAULT', 'exclude'):
                exclude = config_parser.get('DEFAULT', 'exclude').lower().split()
            return AgentDescriptor(pkg_name=name, name=config_parser['DEFAULT']['name'], description=config_parser['DEFAULT']['description'], exclude=exclude, default=default, z_default=z_default)
        return AgentDescriptor(pkg_name=name, name=name)

    def get_report_enable(self) -> bool:
        plugins_config = self.config_storage.read_config(None)
        return plugins_config.report_enable

    def mark_report_enable(self, report_enable):
        plugins_config = self.config_storage.read_config(None)
        plugins_config.report_enable = report_enable
        self.config_storage.store_config(plugins_config, None)

    def mark_plugins_as_installed(self, name_plugin: str, user_name: Optional[str]):
        plugins_config = self.config_storage.read_config(user_name)
        if name_plugin not in plugins_config.installed:
            plugins_config.installed.append(name_plugin)
        self.config_storage.store_config(plugins_config, user_name)

    @staticmethod
    def filter_by_platform(agent_descriptors: List[AgentDescriptor]) -> List[AgentDescriptor]:
        os_name = os.uname().sysname.lower()
        return list(filter(lambda agent: os_name not in agent.exclude, agent_descriptors))

    def all_plugins(self) -> List[AgentDescriptor]:
        agent_descriptors = list((self.load_descriptors(os.path.join(importer.path, name), name) for importer, name, _ in pkg.iter_modules(self.get_path())))
        agent_descriptors = self.filter_by_platform(agent_descriptors)
        plugins_installed = self.config_storage.load_installed()
        for agent_descriptor in agent_descriptors:
            agent_descriptor.installed = agent_descriptor.name in plugins_installed
        logger.info(f'agents runned: {self.__plugins}')
        for agent_descriptor in agent_descriptors:
            if agent_descriptor.pkg_name in self.__plugins:
                logger.info(f'{agent_descriptor.pkg_name} is {self.__plugins[agent_descriptor.pkg_name].ready}')
                agent_descriptor.ready = self.__plugins[agent_descriptor.pkg_name].ready
            else:
                logger.info(f'{agent_descriptor.pkg_name} not iniciate.')
                agent_descriptor.ready = False
        return agent_descriptors

    def get_current_orchestrator(self) -> str:
        if not self.current_orchestrator:
            plugin_config = self.config_storage.read_config()
            self.current_orchestrator = plugin_config.default_orchestrator
            plugin_config.orchestrator = self.current_orchestrator
            self.config_storage.store_config(plugin_config)
        return self.current_orchestrator

    def select_orchestrator(self, orchestrator_name: str):
        plugin_config = self.config_storage.read_config()
        self.current_orchestrator = orchestrator_name
        plugin_config.orchestrator = self.current_orchestrator
        self.config_storage.store_config(config)

    def get_current_plugin_name(self, user_name: str) -> List[str]:
        selected_plugin = self.__get_selected_by_user(user_name)
        if selected_plugin is None:
            self.init_plugin_config(user_name)
            selected_plugin = self.__get_selected_by_user(user_name)
        if not selected_plugin:
            return []
        return list(map(lambda plugin: plugin.name, selected_plugin))

    def init_plugin_config(self, user_name: str) -> PluginConfig:
        plugin_config = self.config_storage.read_config(user_name)
        plugin_name = plugin_config.selected
        if not plugin_name:
            plugin_name = plugin_config.default
        for plugin_to_select in plugin_name:
            self.select_plugin(plugin_to_select, user_name)
        return plugin_config

    def get_agent_descriptor(self, plugin_to_select) -> Optional[AgentDescriptor]:
        all_plugins = self.all_plugins()
        for plugin in all_plugins:
            if plugin_to_select in (plugin.name, plugin.pkg_name):
                return plugin
        return None

    def select_plugin(self, plugin_to_select: str, user_name: str) -> Optional[pkg.ModuleInfo]:
        agent_descriptor_selected = self.get_agent_descriptor(plugin_to_select)
        if agent_descriptor_selected is None:
            return None
        for module in pkg.iter_modules(self.get_path()):
            if module.name == agent_descriptor_selected.pkg_name:
                self.__select_plugin_for_user(module, user_name)
                if agent_descriptor_selected.pkg_name not in self.__plugins:
                    self.start_agent(agent_descriptor_selected)
                return module
        return None

    def unselect_plugin(self, plugin_to_select: str, user_name: str) -> Optional[pkg.ModuleInfo]:
        agent_descriptor_selected = self.get_agent_descriptor(plugin_to_select)
        if agent_descriptor_selected is None:
            return None
        for module in pkg.iter_modules(self.get_path()):
            if module.name == agent_descriptor_selected.pkg_name:
                self.__unselect_plugin_for_user(module, user_name)
                return module
        return None

    def __select_plugin_for_user(self, plugin_to_select, user_name):
        if user_name in self.__selected_plugin:
            if plugin_to_select not in self.__selected_plugin[user_name]:
                self.__selected_plugin[user_name].append(plugin_to_select)
        else:
            self.__selected_plugin[user_name] = [plugin_to_select]

    def __unselect_plugin_for_user(self, plugin_to_select, user_name):
        if user_name in self.__selected_plugin and plugin_to_select in self.__selected_plugin[user_name]:
            self.__selected_plugin[user_name].remove(plugin_to_select)

    def __get_selected_by_user(self, user_name) -> Optional[List[pkg.ModuleInfo]]:
        if user_name in self.__selected_plugin:
            return self.__selected_plugin[user_name]
        return None

    def reload(self):
        self.__plugins.clear()
        self.preload_plugins()

def start_agent(self, descriptor):
    agent_datasource_executor.execute(self.load_agent, descriptor.pkg_name)

class Agent(ABC):

    def __init__(self):
        self.agent_name = self.__class__.__name__
        self.ready = False
        self._save_basedir = os.path.join(BASEDIR, 'saved_agents')
        self._save_dirpath = os.path.join(self._save_basedir, self.agent_name)

    def execute(self, state: State) -> Union[Action, List[Action]]:
        try:
            action_to_return = self.get_next_action(state)
        except:
            action_to_return = Action()
        if isinstance(action_to_return, list):
            for action in action_to_return:
                action.agent_owner = self.agent_name
        else:
            action_to_return.agent_owner = self.agent_name
        return action_to_return

    def post_execute(self, state: State) -> Action:
        """Provide a post execution"""
        return Action(origin_command=state.command)

    @abstractmethod
    def get_next_action(self, state: State) -> Union[Action, List[Action]]:
        """Provide next action to execute in the bash console"""

    def init_agent(self):
        """Add here all heavy task for initialize the """

    def get_agent_state(self) -> dict:
        """Returns the agent state to be saved for future loading"""
        return {}

    def __prepare_state_folder__(self):
        os.makedirs(self._save_dirpath, exist_ok=True)
        for file in os.listdir(self._save_dirpath):
            path = os.path.join(self._save_dirpath, file)
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)

    def save_agent(self) -> bool:
        """Saves agent state into persisting memory"""
        try:
            state = self.get_agent_state()
            if not state:
                return True
            self.__prepare_state_folder__()
            for var_name, var_val in state.items():
                with open('{}/{}.p'.format(self._save_dirpath, var_name), 'wb') as file:
                    pickle.dump(var_val, file)
        except Exception:
            return False
        else:
            return True

    def load_saved_state(self) -> dict:
        agent_state = {}
        filenames = []
        if os.path.exists(self._save_dirpath):
            filenames = [file for file in os.listdir(self._save_dirpath) if os.path.isfile(os.path.join(self._save_dirpath, file))]
        for filename in filenames:
            try:
                key = os.path.splitext(filename)[0]
                with open(os.path.join(self._save_dirpath, filename), 'rb') as file:
                    agent_state[key] = pickle.load(file)
            except:
                pass
        return agent_state

    def extract_name_without_extension(self, filename):
        return os.path.splitext(filename)[0]

    def __del__(self):
        self.save_agent()

def execute(self, state: State) -> Union[Action, List[Action]]:
    try:
        action_to_return = self.get_next_action(state)
    except:
        action_to_return = Action()
    if isinstance(action_to_return, list):
        for action in action_to_return:
            action.agent_owner = self.agent_name
    else:
        action_to_return.agent_owner = self.agent_name
    return action_to_return

class CommandRunnerFactory:

    def __init__(self, agent_datasource: AgentDatasource, config_storage: ConfigStorage, server_status_datasource: ServerStatusDatasource, orchestrator_provider: OrchestratorProvider):
        self.server_status_datasource = server_status_datasource
        self.clai_commands: Dict[str, CommandRunner] = {'skills': ClaiPluginsCommandRunner(agent_datasource), 'orchestrate': ClaiOrchestrateCommandRunner(orchestrator_provider), 'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'deactivate': ClaiUnselectCommandRunner(config_storage, agent_datasource), 'manual': ClaiPowerDisableCommandRunner(server_status_datasource), 'auto': ClaiPowerCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'reload': ClaiReloadCommandRunner(agent_datasource), 'help': ClaiHelpCommandRunner()}
        self.clai_post_commands: Dict[str, PostCommandRunner] = {'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource)}

    def provide_command_runner(self, command: str, selected_agent: AgentRunner) -> CommandRunner:
        if command.startswith(CLAI_COMMAND_NAME):
            clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
            return self.__get_clai_command_runner(clai_command_name, selected_agent)
        return AgentCommandRunner(selected_agent, self.server_status_datasource)

    def provide_post_command_runner(self, command: str, selected_agent: AgentRunner) -> PostCommandRunner:
        if command.startswith(CLAI_COMMAND_NAME):
            clai_command_name = command.replace(CLAI_COMMAND_NAME, '', 1).strip()
            return self.__get_clai_post_command_runner(clai_command_name, selected_agent)
        return AgentCommandRunner(selected_agent, self.server_status_datasource)

    def __get_clai_post_command_runner(self, clai_command_name: str, selected_agent: AgentRunner) -> PostCommandRunner:
        clai_post_commands_names = self.clai_post_commands.keys()
        commands_filtered = filter(clai_command_name.startswith, clai_post_commands_names)
        command_found = next(commands_filtered, None)
        if command_found:
            return self.clai_post_commands[command_found]
        return ClaiDelegateToAgentCommandRunner(AgentCommandRunner(selected_agent, self.server_status_datasource))

    def __get_clai_command_runner(self, clai_command_name: str, selected_agent: AgentRunner) -> CommandRunner:
        clai_commands_names = self.clai_commands.keys()
        commands_filtered = filter(clai_command_name.startswith, clai_commands_names)
        command_found = next(commands_filtered, None)
        if command_found:
            return self.clai_commands[command_found]
        return ClaiDelegateToAgentCommandRunner(AgentCommandRunner(selected_agent, self.server_status_datasource, ignore_threshold=True))

def __init__(self, agent_datasource: AgentDatasource, config_storage: ConfigStorage, server_status_datasource: ServerStatusDatasource, orchestrator_provider: OrchestratorProvider):
    self.server_status_datasource = server_status_datasource
    self.clai_commands: Dict[str, CommandRunner] = {'skills': ClaiPluginsCommandRunner(agent_datasource), 'orchestrate': ClaiOrchestrateCommandRunner(orchestrator_provider), 'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'deactivate': ClaiUnselectCommandRunner(config_storage, agent_datasource), 'manual': ClaiPowerDisableCommandRunner(server_status_datasource), 'auto': ClaiPowerCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'reload': ClaiReloadCommandRunner(agent_datasource), 'help': ClaiHelpCommandRunner()}
    self.clai_post_commands: Dict[str, PostCommandRunner] = {'activate': ClaiSelectCommandRunner(config_storage, agent_datasource), 'last-info': ClaiLastInfoCommandRunner(server_status_datasource), 'install': ClaiInstallCommandRunner(agent_datasource)}

class ClaiDelegateToAgentCommandRunner(CommandRunner, PostCommandRunner):

    def __init__(self, agent: AgentCommandRunner):
        self.agent = agent

    def execute(self, state: State) -> Action:
        command_to_check = state.command.replace(CLAI_COMMAND_NAME, '', 1).strip()
        state.command = command_to_check
        if not command_to_check.strip():
            return ClaiHelpCommandRunner().execute(state)
        if command_to_check.startswith('"'):
            possible_agents = command_to_check.split('"')[1::2]
            if possible_agents:
                agent_name = possible_agents[0]
                self.agent.force_agent = agent_name
                state.command = command_to_check.replace(f'"{agent_name}"', '', 1).strip()
        action = self.agent.execute(state)
        if not action:
            return ClaiHelpCommandRunner().execute(state)
        if isinstance(action, Action):
            if action.is_same_command() and (not action.description):
                return ClaiHelpCommandRunner().execute(state)
        if isinstance(action, List):
            diffent_actions = list(filter(lambda value: not value.is_same_action(), action))
            if not diffent_actions:
                return ClaiHelpCommandRunner().execute(state)
        return action

    def execute_post(self, state: State) -> Action:
        return self.agent.execute_post(state)

def execute(self, state: State) -> Action:
    command_to_check = state.command.replace(CLAI_COMMAND_NAME, '', 1).strip()
    state.command = command_to_check
    if not command_to_check.strip():
        return ClaiHelpCommandRunner().execute(state)
    if command_to_check.startswith('"'):
        possible_agents = command_to_check.split('"')[1::2]
        if possible_agents:
            agent_name = possible_agents[0]
            self.agent.force_agent = agent_name
            state.command = command_to_check.replace(f'"{agent_name}"', '', 1).strip()
    action = self.agent.execute(state)
    if not action:
        return ClaiHelpCommandRunner().execute(state)
    if isinstance(action, Action):
        if action.is_same_command() and (not action.description):
            return ClaiHelpCommandRunner().execute(state)
    if isinstance(action, List):
        diffent_actions = list(filter(lambda value: not value.is_same_action(), action))
        if not diffent_actions:
            return ClaiHelpCommandRunner().execute(state)
    return action

class Orchestrator(ABC):

    def __init__(self):
        self.orchestrator_name = self.__class__.__name__
        self._save_basedir = os.path.join(BASEDIR, 'saved_orchestrators')
        self._save_dirpath = os.path.join(self._save_basedir, self.orchestrator_name)
        self.noop_command = NOOP_COMMAND

    def get_orchestrator_state(self):
        """Returns the orchestrator state for persistence"""
        return {}

    @abstractmethod
    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Union[Action, List[Action]]]:
        """Choose an action and agent name for CLAI to respond with"""

    def record_transition(self, prev_state: TerminalReplayMemoryComplete, current_state_pre: TerminalReplayMemory) -> None:
        """
        Record terminal state transition to learn user behavior
        :param prev_state: Previous terminal state
        :param current_state_pre: Current terminal state pre-exec state
        :return: None
        """

    def save(self):
        """Save the orchestrator state"""
        return self.__save_orchestrator__()

    def load(self):
        """Load the orchestrator state"""
        return self.__load_saved_orchestrator__()

    def __prepare_state_folder__(self):
        os.makedirs(self._save_dirpath, exist_ok=True)
        for filename in os.listdir(self._save_dirpath):
            filepath = os.path.join(self._save_dirpath, filename)
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)

    def __save_orchestrator__(self) -> bool:
        """Saves agent state into persisting memory"""
        try:
            state = self.get_orchestrator_state()
            if not state:
                return True
            self.__prepare_state_folder__()
            for var_name, value in state.items():
                with open(f'{self._save_dirpath}/{var_name}.p', 'wb') as file:
                    pickle.dump(value, file)
        except Exception:
            return False
        else:
            return True

    def __load_saved_orchestrator__(self) -> dict:
        orchestrator_state = {}
        files = []
        if os.path.exists(self._save_dirpath):
            files = [file for file in os.listdir(self._save_dirpath) if os.path.isfile(os.path.join(self._save_dirpath, file))]
        for filename in files:
            try:
                key = os.path.splitext(filename)[0]
                with open(os.path.join(self._save_dirpath, filename), 'rb') as file:
                    orchestrator_state[key] = pickle.load(file)
            except:
                pass
        return orchestrator_state

    def __del__(self):
        self.save()

    @staticmethod
    def __calculate_confidence__(action_to_calculate: Union[Action, List[Action]]):
        if isinstance(action_to_calculate, Action):
            return action_to_calculate.confidence
        return action_to_calculate[0].confidence

@staticmethod
def __calculate_confidence__(action_to_calculate: Union[Action, List[Action]]):
    if isinstance(action_to_calculate, Action):
        return action_to_calculate.confidence
    return action_to_calculate[0].confidence

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

class Example:
    """Stores an input, output pair and formats it to prime the model."""

    def __init__(self, inp, out):
        self.input = inp
        self.output = out
        self._id = uuid.uuid4().hex

    def get_input(self):
        """Returns the input of the example."""
        return self.input

    def get_output(self):
        """Returns the intended output of the example."""
        return self.output

    def get_id(self):
        """Returns the unique ID of the example."""
        return self._id

    def as_dict(self):
        return {'input': self.get_input(), 'output': self.get_output(), 'id': self.get_id()}

def as_dict(self):
    return {'input': self.get_input(), 'output': self.get_output(), 'id': self.get_id()}

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

def add_example(self, ex):
    """Adds an example to the object.

        Example must be an instance of the Example class.
        """
    assert isinstance(ex, Example), 'Please create an Example object.'
    self.examples[ex.get_id()] = ex

def format_example(self, ex):
    """Formats the input, output pair."""
    return self.input_prefix + ex.get_input() + self.input_suffix + self.output_prefix + ex.get_output() + self.output_suffix

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
def __parse_actions__(candidate_actions: Optional[List[Union[Action, List[Action]]]]):
    if not candidate_actions:
        return []
    if isinstance(candidate_actions, Action):
        return [candidate_actions]
    return candidate_actions

