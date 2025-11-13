# Cluster 35

def is_user_install(bin_path):
    plugins_config = ConfigStorage(alternate_path=f'{bin_path}/configPlugins.json').read_config(None).user_install
    return plugins_config

def install_plugins(install_path, user_install):
    agent_datasource = AgentDatasource(config_storage=ConfigStorage(alternate_path=f'{install_path}/configPlugins.json'))
    plugins = agent_datasource.all_plugins()
    for plugin in plugins:
        default = z_default = False
        if PLATFORM in ('zos', 'os390'):
            z_default = plugin.z_default
        else:
            default = plugin.default
        if default or z_default:
            installed = install_plugins_dependencies(install_path, plugin.pkg_name, user_install)
            if installed:
                agent_datasource.mark_plugins_as_installed(plugin.name, None)
    return agent_datasource

def mark_user_flag(bin_path: str, value: bool):
    config_storage = ConfigStorage(alternate_path=f'{bin_path}/configPlugins.json')
    plugins_config = config_storage.read_config(None)
    plugins_config.user_install = value
    config_storage.store_config(plugins_config, None)

def install_orchestration(bin_path):
    agent_datasource = AgentDatasource(config_storage=ConfigStorage(alternate_path=f'{bin_path}/configPlugins.json'))
    orchestrator_provider = OrchestratorProvider(agent_datasource)
    all_orchestrators = orchestrator_provider.all_orchestrator()
    for orchestrator in all_orchestrators:
        install_orchestration_dependencies(bin_path, orchestrator.name)

def pytest_generate_tests(metafunc):
    if 'command' in metafunc.fixturenames:
        commands = getattr(metafunc.cls, 'get_commands_to_execute')(metafunc.cls)
        commands_expected = getattr(metafunc.cls, 'get_commands_expected')(metafunc.cls)
        metafunc.parametrize(['command', 'command_expected'], list(zip(commands, commands_expected)))

class TerminalReplayMemory:

    def __init__(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, suggested_command: Optional[Action]):
        self.command = deepcopy(command)
        self.agent_names = agent_names
        self.candidate_actions = deepcopy(candidate_actions)
        self.force_response = force_response
        self.suggested_command = deepcopy(suggested_command)

def __init__(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, suggested_command: Optional[Action]):
    self.command = deepcopy(command)
    self.agent_names = agent_names
    self.candidate_actions = deepcopy(candidate_actions)
    self.force_response = force_response
    self.suggested_command = deepcopy(suggested_command)

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

def __init__(self, server_status_datasource: ServerStatusDatasource, agent_datasource: AgentDatasource):
    self.agent_datasource = agent_datasource
    orchestrator_provider = OrchestratorProvider(agent_datasource)
    self.agent_runner = AgentRunner(self.agent_datasource, orchestrator_provider)
    self.server_status_datasource = server_status_datasource
    self.server_pending_actions_datasource = ServerPendingActionsDatasource()
    self.command_runner_factory = CommandRunnerFactory(self.agent_datasource, config_storage, self.server_status_datasource, orchestrator_provider)

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

class ClaiPluginsCommandRunner(CommandRunner):
    __VERBOSE_MODE = '-v'

    def __init__(self, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource

    def execute(self, state: State) -> Action:
        action_to_return = create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins(), self.__VERBOSE_MODE in state.command)
        action_to_return.origin_command = state.command
        return action_to_return

def execute(self, state: State) -> Action:
    action_to_return = create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins(), self.__VERBOSE_MODE in state.command)
    action_to_return.origin_command = state.command
    return action_to_return

class ClaiOrchestrateCommandRunner(CommandRunner):
    SELECT_DIRECTIVE = 'clai orchestrate'
    __VERBOSE_MODE = '-v'

    def __init__(self, orchestrator_provider: OrchestratorProvider):
        self.orchestrator_provider = orchestrator_provider

    def execute(self, state: State) -> Action:
        orchestrator_to_select = state.command.replace(f'{self.SELECT_DIRECTIVE}', '').strip()
        verbose = False
        if self.__VERBOSE_MODE in orchestrator_to_select:
            verbose = True
            orchestrator_to_select = ''
        else:
            orchestrator_to_select = extract_quoted_agent_name(orchestrator_to_select)
        if orchestrator_to_select:
            self.orchestrator_provider.select_orchestrator(orchestrator_to_select)
        return create_orchestrator_list(self.orchestrator_provider.get_current_orchestrator_name(), self.orchestrator_provider.all_orchestrator(), verbose)

def execute(self, state: State) -> Action:
    orchestrator_to_select = state.command.replace(f'{self.SELECT_DIRECTIVE}', '').strip()
    verbose = False
    if self.__VERBOSE_MODE in orchestrator_to_select:
        verbose = True
        orchestrator_to_select = ''
    else:
        orchestrator_to_select = extract_quoted_agent_name(orchestrator_to_select)
    if orchestrator_to_select:
        self.orchestrator_provider.select_orchestrator(orchestrator_to_select)
    return create_orchestrator_list(self.orchestrator_provider.get_current_orchestrator_name(), self.orchestrator_provider.all_orchestrator(), verbose)

class ClaiInstallCommandRunner(CommandRunner, PostCommandRunner):
    INSTALL_PLUGIN_DIRECTIVE = 'clai install'

    def __init__(self, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource

    @staticmethod
    def __move_plugin__(dir_to_install: str) -> Action:
        if dir_to_install.startswith('http') or dir_to_install.startswith('https'):
            cmd = f'cd $CLAI_PATH/clai/server/plugins && curl -O {dir_to_install}'
            return Action(suggested_command=cmd, execute=True)
        if not os.path.exists(dir_to_install) or not os.path.isdir(dir_to_install):
            return create_error_install(dir_to_install)
        plugin_name = dir_to_install.split('/')[-1]
        logger.info(f'installing plugin name {plugin_name}')
        cmd = f'cp -R {dir_to_install} $CLAI_PATH/clai/server/plugins'
        return Action(suggested_command=cmd, execute=True)

    def execute(self, state: State) -> Action:
        dir_to_install = state.command.replace(f'{self.INSTALL_PLUGIN_DIRECTIVE}', '').strip()
        logger.info(f'trying to install ${dir_to_install}')
        return self.__move_plugin__(dir_to_install)

    def execute_post(self, state: State) -> Action:
        if state.result_code == '0' and state.action_suggested.suggested_command != ':':
            return create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())
        return Action()

def execute(self, state: State) -> Action:
    dir_to_install = state.command.replace(f'{self.INSTALL_PLUGIN_DIRECTIVE}', '').strip()
    logger.info(f'trying to install ${dir_to_install}')
    return self.__move_plugin__(dir_to_install)

def execute_post(self, state: State) -> Action:
    if state.result_code == '0' and state.action_suggested.suggested_command != ':':
        return create_message_list(self.agent_datasource.get_current_plugin_name(state.user_name), self.agent_datasource.all_plugins())
    return Action()

class KubeExe(KubeTracker):

    def __init__(self):
        super().__init__()
        self.refresh_observations()

    def get_plan(self) -> list:
        problem = copy.deepcopy(self.template).replace('<GOAL>', self.goal)
        plan = get_plan_from_pr2plan(domain=self.domain, problem=problem, obs=self.get_observations())
        return plan

    def execute_action(self, action: str) -> str:
        try:
            command = getattr(self, action.replace('-', '_'))()
            if command:
                return command
        except Exception as e:
            print(e)

    def set_state(self):
        if not self.host_port:
            self.host_port = '8085'
        if not self.name:
            self.name = 'app'
        if not self.tag:
            self.tag = 'v1'
        return None

    def docker_build(self):
        command = 'docker build -t {}:{} .'.format(self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def dockerfile_read(self):
        with open('Dockerfile', 'r') as f:
            dockerfile_contents = f.read()
        self.local_port = re.findall('EXPOSE\\s[0-9]+', dockerfile_contents)[0].strip().split(' ')[-1].strip()
        return None

    def docker_run(self):
        command = 'docker run -i -p {}:{} -d {}:{}'.format(self.host_port, self.local_port, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0)

    def ibmcloud_login(self):
        command = 'ibmcloud login'
        return Action(suggested_command=command, confidence=1.0)

    def ibmcloud_cr_login(self):
        command = 'ibmcloud cr login'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def get_namespace(self):
        command = 'ibmcloud cr namespaces'
        return None

    def docker_tag_for_ibmcloud(self):
        if not self.namespace:
            self.namespace = '<enter-namespace>'
        command = 'docker tag {}:{} us.icr.io/{}/{}:{}'.format(self.name, self.tag, self.namespace, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def docker_push(self):
        if not self.namespace:
            self.namespace = '<enter-namespace>'
        command = 'docker push us.icr.io/{}/{}:{}'.format(self.namespace, self.name, self.tag)
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def list_images(self):
        command = 'ibmcloud cr image-list'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def get_image_name_to_delete(self):
        return None

    def ibmcloud_delete_image(self):
        command = 'ibmcloud cr image-rm us.icr.io/{}/'.format(self.namespace, self.image_to_remove)
        return Action(suggested_command=command, confidence=1.0)

    def check_account_free(self):
        command = 'ibmcloud account show'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def check_account_paid(self):
        command = 'ibmcloud account show'
        return Action(suggested_command=command, confidence=1.0, execute=False)

    def set_protocol(self):
        return None

    def ask_protocol(self):
        description = 'Do you want to use NodePort protocol?'
        return Action(suggested_command=NOOP_COMMAND, description=description, confidence=1.0, execute=False)

    def build_yaml(self):
        app_yaml = open(_path_to_yaml_temnplate, 'r').read()
        app_yaml = app_yaml.replace('{name}', self.name).replace('{tag}', self.tag).replace('{namespace}', self.namespace).replace('{protocol}', self.protocol).replace('{host_port}', self.host_port).replace('{local_port}', self.local_port)
        with open(_real_path + '/app.yaml', 'w') as f:
            f.write(app_yaml)
        self.yaml = app_yaml
        return Action(suggested_command=NOOP_COMMAND, description=self.yaml)

    def get_set_cluster_config(self):
        if not self.cluster_name:
            self.cluster_name = '<enter-cluster-name>'
        command = 'ibmcloud ks cluster-config {} | grep -e "export" | echo'.format(self.cluster_name)
        return Action(suggested_command=command, confidence=1.0)

    def kube_deploy(self):
        command = 'kubectl apply -f {}'.format(_path_to_yaml_temnplate)
        return Action(suggested_command=command, confidence=1.0)

def get_plan(self) -> list:
    problem = copy.deepcopy(self.template).replace('<GOAL>', self.goal)
    plan = get_plan_from_pr2plan(domain=self.domain, problem=problem, obs=self.get_observations())
    return plan

def execute_action(self, action: str) -> str:
    try:
        command = getattr(self, action.replace('-', '_'))()
        if command:
            return command
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

@staticmethod
def clear_text(skill):
    active = '[x]' in skill
    skill_without_tick = skill.replace('[x]\x1b[32m ', '').replace('\x1b[0m', '').replace('[ ]', '').strip()
    return (skill_without_tick, active)

@staticmethod
def extract_skill_name(skill):
    installed = '(Installed)' in skill
    return (skill.replace('(Installed)', '').replace('(Not Installed)', '').strip(), installed)

