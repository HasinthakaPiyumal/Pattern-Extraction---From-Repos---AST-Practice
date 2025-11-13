# Cluster 4

class MockExecutor(AgentExecutor):

    def execute_agents(self, command: State, agents: List[Agent]) -> List[Action]:
        return list(map(lambda agent: self.execute(command, agent), agents))

    @staticmethod
    def execute(command: State, agent: Agent) -> Action:
        action = agent.execute(command)
        if not action:
            action = Action()
        return action

def execute_agents(self, command: State, agents: List[Agent]) -> List[Action]:
    return list(map(lambda agent: self.execute(command, agent), agents))

def map_processes(processes) -> List[Process]:
    return list(map(lambda _: Process(name=_['name']), processes))

def obtain_last_processes(user_name):
    process_changes = []
    if PLATFORM not in ('zos', 'os390'):
        for process in PSUTIL.process_iter(attrs=['pid', 'name', 'username', 'create_time']):
            process_changes.append(process.info)
    else:
        pass
    porcess_changes = list(filter(lambda _: _['username'] == user_name, process_changes))
    porcess_changes.sort(key=lambda _: _['create_time'], reverse=True)
    return map_processes(process_changes[EXCLUDE_OWN_PROCESS:SIZE_PROCESS])

class ThreadExecutor(AgentExecutor):
    MAX_TIME_PLUGIN_EXECUTION = 4
    NUM_WORKERS = 4

    def execute_agents(self, command: State, agents: List[Agent]) -> List[Union[Action, List[Action]]]:
        with futures.ThreadPoolExecutor(max_workers=self.NUM_WORKERS) as executor:
            done, _ = futures.wait([executor.submit(plugin_instance.execute, command) for plugin_instance in agents], timeout=self.MAX_TIME_PLUGIN_EXECUTION)
            if not done:
                return []
            results = map(lambda future: future.result(), done)
            candidate_actions = list(filter(partial(is_not, None), results))
        return candidate_actions

def execute_agents(self, command: State, agents: List[Agent]) -> List[Union[Action, List[Action]]]:
    with futures.ThreadPoolExecutor(max_workers=self.NUM_WORKERS) as executor:
        done, _ = futures.wait([executor.submit(plugin_instance.execute, command) for plugin_instance in agents], timeout=self.MAX_TIME_PLUGIN_EXECUTION)
        if not done:
            return []
        results = map(lambda future: future.result(), done)
        candidate_actions = list(filter(partial(is_not, None), results))
    return candidate_actions

class ThreadAgentDatasourceExecutor(AgentDatasourceExecutor):
    NUM_WORKERS = 4

    def __init__(self):
        self.executor = futures.ThreadPoolExecutor(max_workers=self.NUM_WORKERS)

    def execute(self, load_agent, pkg_name):
        self.executor.submit(load_agent, pkg_name)

def __init__(self):
    self.executor = futures.ThreadPoolExecutor(max_workers=self.NUM_WORKERS)

def execute(self, load_agent, pkg_name):
    self.executor.submit(load_agent, pkg_name)

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

def preload_plugins(self):
    all_descriptors = self.all_plugins()
    installed_agents = list(filter(lambda value: value.installed, all_descriptors))
    for descriptor in installed_agents:
        self.start_agent(descriptor)
    logger.info('finish init')

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

def get_current_plugin_name(self, user_name: str) -> List[str]:
    selected_plugin = self.__get_selected_by_user(user_name)
    if selected_plugin is None:
        self.init_plugin_config(user_name)
        selected_plugin = self.__get_selected_by_user(user_name)
    if not selected_plugin:
        return []
    return list(map(lambda plugin: plugin.name, selected_plugin))

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

def __set_default_values__(self, args: dict, **kwargs) -> dict:
    for key in kwargs.keys():
        if key not in args:
            args[key] = kwargs[key]
    return args

def can_run_on_this_os(self) -> bool:
    """Returns True if this search provider can be used on the client OS
        """
    if not self.excludes:
        return True
    os_name: str = os.uname().sysname.lower()
    return os_name not in self.excludes

class OrchestratorProvider(ABC):

    def __init__(self, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource
        self.__current_orchestrator_name = None
        self.orchestrator_instances = {}

    def select_orchestrator(self, name: str):
        if name == self.__current_orchestrator_name:
            return
        if name in self.orchestrator_instances:
            self.__current_orchestrator_name = name
        elif self.get_orchestrator_instance(name):
            self.__current_orchestrator_name = name

    def get_current_orchestrator_name(self):
        if not self.__current_orchestrator_name:
            self.get_current_orchestrator()
        return self.__current_orchestrator_name

    def get_current_orchestrator(self):
        if not self.__current_orchestrator_name:
            self.__current_orchestrator_name = self.agent_datasource.get_current_orchestrator()
        if self.__current_orchestrator_name in self.orchestrator_instances:
            return self.orchestrator_instances[self.__current_orchestrator_name]
        return self.get_orchestrator_instance(self.__current_orchestrator_name)

    def get_orchestrator_instance(self, orchestrator_name: str):
        """
        Returns an instance of the requested orchestration pattern
        :param orchestrator_name: Orchestrator pattern package name
        :return: instantiated object of the orchestrator
        """
        orchestrator_mods = importlib.import_module(f'clai.server.orchestration.patterns.{orchestrator_name}.{orchestrator_name}', package=orchestrator_name)
        for _, class_member in inspect.getmembers(orchestrator_mods, inspect.isclass):
            if issubclass(class_member, Orchestrator) and class_member is not Orchestrator:
                class_member = class_member()
                self.orchestrator_instances[orchestrator_name] = class_member
                return class_member
        return None

    def all_orchestrator(self) -> List[OrchestratorDescriptor]:
        orchestrator_names = list(map(lambda value: value.name, pkg.iter_modules(self.get_path())))
        orchestrators = []
        for orchestrator in orchestrator_names:
            orchestrator_plugin = os.path.join(self.get_path()[0], orchestrator)
            orchestrator_descriptor = self.load_descriptors(orchestrator_plugin, orchestrator)
            if not orchestrator_descriptor.exclude:
                orchestrators.append(orchestrator_descriptor)
        return orchestrators

    @staticmethod
    def load_descriptors(path, name) -> OrchestratorDescriptor:
        file_path = os.path.join(path, 'manifest.properties')
        if os.path.exists(file_path):
            config_parser = configparser.ConfigParser()
            config_parser.read(file_path)
            exclude = False
            if config_parser.has_option('DEFAULT', 'exclude'):
                exclude = config_parser.getboolean('DEFAULT', 'exclude')
            description = ''
            if config_parser.has_option('DEFAULT', 'description'):
                description = config_parser.get('DEFAULT', 'description')
            return OrchestratorDescriptor(name=name, exclude=exclude, description=description)
        return OrchestratorDescriptor(name=name, exclude=False, description='')

    @staticmethod
    def get_path():
        return pattern.__path__

def get_orchestrator_instance(self, orchestrator_name: str):
    """
        Returns an instance of the requested orchestration pattern
        :param orchestrator_name: Orchestrator pattern package name
        :return: instantiated object of the orchestrator
        """
    orchestrator_mods = importlib.import_module(f'clai.server.orchestration.patterns.{orchestrator_name}.{orchestrator_name}', package=orchestrator_name)
    for _, class_member in inspect.getmembers(orchestrator_mods, inspect.isclass):
        if issubclass(class_member, Orchestrator) and class_member is not Orchestrator:
            class_member = class_member()
            self.orchestrator_instances[orchestrator_name] = class_member
            return class_member
    return None

def all_orchestrator(self) -> List[OrchestratorDescriptor]:
    orchestrator_names = list(map(lambda value: value.name, pkg.iter_modules(self.get_path())))
    orchestrators = []
    for orchestrator in orchestrator_names:
        orchestrator_plugin = os.path.join(self.get_path()[0], orchestrator)
        orchestrator_descriptor = self.load_descriptors(orchestrator_plugin, orchestrator)
        if not orchestrator_descriptor.exclude:
            orchestrators.append(orchestrator_descriptor)
    return orchestrators

def get_warmstart_data(profile, **kwargs):
    if profile.lower() == 'noop-always':
        result = get_noop_warmstart_data(**kwargs)
    elif profile.lower() == 'ignore-skill':
        result = get_ignore_skill_warmstart_data(**kwargs)
    elif profile.lower() == 'max-orchestrator':
        result = get_max_skill_warmstart_data(**kwargs)
    elif profile.lower() == 'preferred-skill':
        result = get_preferred_skill_warmstart_data(**kwargs)
    return result

def is_zos():
    return platform.system().lower() in ('z/os', 'os/390')

class ServerPendingActionsDatasource:

    def __init__(self):
        self.__pending_actions: Dict[str, List[PendingActions]] = {}

    def store_pending_actions(self, command_id: str, actions: List[Action], user_name: str) -> Action:
        actions_by_user = self.__find_pending_actions_by_user(user_name)
        actions_by_user.append(PendingActions(command_id, actions))
        return self.get_next_action(command_id, user_name)

    def get_next_action(self, command_id: str, user_name: str) -> Action:
        actions_by_user = self.__find_pending_actions_by_user(user_name)
        pending_actions = next(filter(lambda x: x.command_id == command_id, actions_by_user), None)
        return pending_actions.next()

    def __find_pending_actions_by_user(self, user_name: str) -> List[PendingActions]:
        if user_name not in self.__pending_actions:
            self.__pending_actions[user_name] = []
        return self.__pending_actions[user_name]

def store_pending_actions(self, command_id: str, actions: List[Action], user_name: str) -> Action:
    actions_by_user = self.__find_pending_actions_by_user(user_name)
    actions_by_user.append(PendingActions(command_id, actions))
    return self.get_next_action(command_id, user_name)

def get_next_action(self, command_id: str, user_name: str) -> Action:
    actions_by_user = self.__find_pending_actions_by_user(user_name)
    pending_actions = next(filter(lambda x: x.command_id == command_id, actions_by_user), None)
    return pending_actions.next()

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

def __store_info_by_user(self, message: State, user_name: str):
    messages_by_user = self.__find_messages_by_user(user_name)
    messages_by_user.append(message)

def get_last_messages(self, user_name: str):
    return self.__find_messages_by_user(user_name)

def get_last_message(self, user_name: str, offset: int=0) -> State:
    last_message = None
    messages_by_user = self.__find_messages_by_user(user_name)
    if messages_by_user and len(messages_by_user) > 1 + offset:
        last_message = messages_by_user[-2 - offset]
    return last_message

def find_message_stored(self, id_to_find: str, user_mame: str) -> Optional[State]:
    messages_by_user = self.__find_messages_by_user(user_mame)
    return next(filter(lambda x: x.command_id == id_to_find, messages_by_user), None)

