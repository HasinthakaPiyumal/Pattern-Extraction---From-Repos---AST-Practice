# Cluster 51

def ask_to_user(text):
    print(Colorize().info().append(f'{text} ').append('(y/n)').to_console())
    while True:
        command_input = input()
        if command_input in ('y', 'yes'):
            return True
        if command_input in ('n', 'no'):
            return False
        print(Colorize().info().append('choose yes[y] or no[n]').to_console())

def expected_description(all_plugins, selected) -> str:
    text = 'Available Skills:\n'
    for plugin in all_plugins:
        if plugin.pkg_name in selected:
            text += Colorize().emoji(Colorize.EMOJI_CHECK).complete().append(f' {get_printable_name(plugin)}\n').to_console()
        else:
            text += Colorize().emoji(Colorize.EMOJI_BOX).append(f' {get_printable_name(plugin)}\n').to_console()
    return text

class DemoAgent(Agent):

    def get_next_action(self, state: State) -> Union[Action, List[Action]]:
        logger.info('This is my agent')
        if state.command == 'ls':
            return Action(suggested_command='ls -la', description='This is a demo sample that helps to execute the command in better way.', confidence=1)
        if state.command == 'pwd':
            return [Action(suggested_command='ls -la', description='This is a demo sample that helps to execute the command in better way.', confidence=1), Action(suggested_command='pwd -P', description='This is a demo sample that helps to execute the command in better way.', confidence=1)]
        if state.previous_execution and state.previous_execution.command == 'ls -4':
            return Action(suggested_command='ls -a', execute=True, confidence=1)
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        if state.command.startswith('ls') and state.result_code != '0':
            return Action(description=Colorize().append(f'Are you sure that this command is correct?({state.result_code})\n').warning().append(f'Try man ls for more info ').to_console(), confidence=1)
        return Action(suggested_command=state.command)

def get_next_action(self, state: State) -> Union[Action, List[Action]]:
    logger.info('This is my agent')
    if state.command == 'ls':
        return Action(suggested_command='ls -la', description='This is a demo sample that helps to execute the command in better way.', confidence=1)
    if state.command == 'pwd':
        return [Action(suggested_command='ls -la', description='This is a demo sample that helps to execute the command in better way.', confidence=1), Action(suggested_command='pwd -P', description='This is a demo sample that helps to execute the command in better way.', confidence=1)]
    if state.previous_execution and state.previous_execution.command == 'ls -4':
        return Action(suggested_command='ls -a', execute=True, confidence=1)
    return Action(suggested_command=state.command)

def post_execute(self, state: State) -> Action:
    if state.command.startswith('ls') and state.result_code != '0':
        return Action(description=Colorize().append(f'Are you sure that this command is correct?({state.result_code})\n').warning().append(f'Try man ls for more info ').to_console(), confidence=1)
    return Action(suggested_command=state.command)

def ask_user_prompt(command_to_execute: Action) -> Optional[str]:
    if command_to_execute.is_same_command():
        return command_to_execute.origin_command
    if command_to_execute.execute:
        return command_to_execute.suggested_command
    print(Colorize().emoji(Colorize.EMOJI_ROBOT).info().append('  Suggests: ').info().append(f'{command_to_execute.suggested_command} ').append('(y/n/e)').to_console())
    while True:
        command_input = input()
        if is_yes_command(command_input):
            return command_to_execute.suggested_command
        if is_not_command(command_input):
            return command_to_execute.origin_command
        if is_explain_command(command_input):
            print(Colorize().warning().append(f'Description: {command_to_execute.description}').to_console())
        print(Colorize().info().append('choose yes[y] or no[n] or explain[e]').to_console())

def process_command_from_user(command_id, user_name, command_to_check):
    command_to_execute = send_command(command_id=command_id, user_name=user_name, command_to_check=command_to_check)
    if command_to_execute.origin_command == STOP_COMMAND:
        print(Colorize().info().append('Clai has been stopped').to_console())
        return (NOOP_COMMAND, False)
    if command_to_execute.description and command_to_execute.suggested_command == ':':
        print(command_to_execute.description)
    command_accepted_by_the_user = ask_user_prompt(command_to_execute)
    return (command_accepted_by_the_user, command_to_execute.pending_actions)

def process_command(command_id, user_name, command_to_check):
    pending_commands = False
    if command_to_check == COMMAND_START_SERVER:
        command_accepted_by_the_user = START_SERVER_COMMAND_TO_EXECUTE
        print(Colorize().info().append('CLAI Starting. CLAI could take a while to start replying').to_console())
    elif command_to_check.strip() == COMMAND_BASE.strip():
        command_accepted_by_the_user = NOOP_COMMAND
        print(create_message_server_runing())
        print(create_message_help().description)
    else:
        command_accepted_by_the_user, pending_commands = process_command_from_user(command_id, user_name, command_to_check)
    override_last_command('\n' + command_accepted_by_the_user + '\n')
    if not pending_commands:
        sys.exit(1)

def create_error_install(name: str) -> Action:
    text = Colorize().warning().append(f'{name} is not a valid skill to add to the catalog. You need to write a folder or a valid url. \n').append('Example: clai install ./my_new_agent').to_console()
    return Action(suggested_command=':', description=text, execute=True)

def create_error_select(selected_plugin: str) -> Action:
    text = Colorize().warning().append(f"'{selected_plugin}' is not a valid skill name. ").append('To check available skills, issue:\n >> clai skills\n').append('Example:\n >> clai activate nlc2cmd').to_console()
    return Action(suggested_command=':', description=text, execute=True)

def create_orchestrator_list(selected_orchestrator: str, all_orchestrator: List[OrchestratorDescriptor], verbose_mode=False) -> Action:
    text = 'Available Orchestrators:\n'
    for orchestrator in all_orchestrator:
        if selected_orchestrator == orchestrator.name:
            text += Colorize().emoji(Colorize.EMOJI_CHECK).complete().append(f' {orchestrator.name}\n').to_console()
            if verbose_mode:
                text += Colorize().complete().append(f' {orchestrator.description}\n').to_console()
        else:
            text += Colorize().emoji(Colorize.EMOJI_BOX).append(f' {orchestrator.name}\n').to_console()
            if verbose_mode:
                text += Colorize().append(f' {orchestrator.description}\n').to_console()
    return Action(suggested_command=':', description=text, execute=True)

def create_message_list(selected_plugin: List[str], all_plugins: List[AgentDescriptor], verbose_mode=False) -> Action:
    text = 'Available Skills:\n'
    for plugin in all_plugins:
        if plugin.pkg_name in selected_plugin:
            text += Colorize().emoji(Colorize.EMOJI_CHECK).complete().append(f' {get_printable_name(plugin)}\n').to_console()
            if verbose_mode:
                text += Colorize().complete().append(f'{plugin.description}\n').to_console()
        else:
            text += Colorize().emoji(Colorize.EMOJI_BOX).append(f' {get_printable_name(plugin)}\n').to_console()
            if verbose_mode:
                text += Colorize().append(f'{plugin.description}\n').to_console()
    return Action(suggested_command=':', description=text, execute=True)

def create_message_server_runing() -> str:
    colorize = Colorize()
    if check_if_process_running():
        colorize.complete().append(f'The server is running')
    else:
        colorize.warning().append(f'The server is not running')
    return colorize.to_console()

def create_message_help() -> Action:
    text = Colorize().info().append('CLAI usage:\nclai [help] [skills [-v]] [orchestrate [name]] [activate [skill_name]] [deactivate [skill_name]] [manual | automatic] [install [name | url]] \n\nhelp           Print help and usage of clai.\nskills         List available skills. Use -v For a verbose description of each skill.\norchestrate    Activate the orchestrator by name. If name is empty, list available orchestrators.\nactivate       Activate the named skill.\ndeactivate     Deactivate the named skill.\nmanual         Disables automatic execution of commands without operator confirmation.\nauto           Enables automatic execution of commands without operator confirmation.\ninstall        Installs a new skill. The required argument may be a local file path\n               to a skill plugin folder, or it may be a URL to install a skill plugin \n               over a network connection.\n').to_console()
    return Action(suggested_command=':', description=text, execute=True)

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

def __select_plugin_for_user(self, plugin_to_select, user_name):
    if user_name in self.__selected_plugin:
        if plugin_to_select not in self.__selected_plugin[user_name]:
            self.__selected_plugin[user_name].append(plugin_to_select)
    else:
        self.__selected_plugin[user_name] = [plugin_to_select]

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

def post_execute(self, state: State) -> Action:
    """Provide a post execution"""
    return Action(origin_command=state.command)

class ClaiIdentity(Agent):

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

def get_next_action(self, state: State) -> Action:
    return Action(suggested_command=state.command)

class Logger:
    MAX_IN_MB = 100000000

    def __init__(self):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        log_file = os.getenv('CLAI_LOG_FILE', '/var/tmp/app.log')
        self.logger = logging.getLogger('clai_logger')
        self.logger.setLevel(logging.INFO)
        self.log_handler = handlers.RotatingFileHandler(log_file, mode='a', maxBytes=Logger.MAX_IN_MB, backupCount=10, encoding=None, delay=0)
        self.log_handler.setLevel(logging.INFO)
        self.log_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.log_handler)

    def info(self, text):
        self.logger.info(text)

    def warning(self, text):
        self.logger.warning(text)

    def debug(self, text):
        self.logger.debug(text)

def info(self, text):
    self.logger.info(text)

def warning(self, text):
    self.logger.warning(text)

class AgentCommandRunner(CommandRunner, PostCommandRunner):

    def __init__(self, agent_runner: AgentRunner, server_status_datasource: ServerStatusDatasource, ignore_threshold: bool=False):
        self.agent_runner = agent_runner
        self.server_status_datasource = server_status_datasource
        self.ignore_threshold = ignore_threshold
        self.force_agent = None

    def execute(self, state: State) -> Union[Action, List[Action]]:
        action = self.agent_runner.process(state, self.ignore_threshold, self.force_agent)
        if not action:
            action = Action()
        return action

    def execute_post(self, state: State) -> Action:
        action = self.agent_runner.process_post(state, self.ignore_threshold)
        if not action:
            action = Action()
        action.origin_command = state.command
        return action

def execute(self, state: State) -> Union[Action, List[Action]]:
    action = self.agent_runner.process(state, self.ignore_threshold, self.force_agent)
    if not action:
        action = Action()
    return action

def execute_post(self, state: State) -> Action:
    action = self.agent_runner.process_post(state, self.ignore_threshold)
    if not action:
        action = Action()
    action.origin_command = state.command
    return action

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

def execute(self, state: State) -> Action:
    return Action(suggested_command=':', execute=True, origin_command=state.command)

class ClaiHelpCommandRunner(CommandRunner):

    def execute(self, state: State) -> Action:
        return create_message_help()

def execute(self, state: State) -> Action:
    return create_message_help()

class ClaiReloadCommandRunner(CommandRunner):

    def __init__(self, agent_datasource: AgentDatasource):
        self.agent_datasource = agent_datasource

    def execute(self, state: State) -> Action:
        self.agent_datasource.reload()
        text = Colorize().complete().append('Plugins reloaded.\n').to_console()
        return Action(suggested_command=':', execute=True, description=text, origin_command=state.command)

def execute(self, state: State) -> Action:
    self.agent_datasource.reload()
    text = Colorize().complete().append('Plugins reloaded.\n').to_console()
    return Action(suggested_command=':', execute=True, description=text, origin_command=state.command)

class Linuss(Agent):

    def __init__(self):
        super(Linuss, self).__init__()
        self._config_path = os.path.join(Path(__file__).parent.absolute(), 'equivalencies.json')
        self.equivalencies = self.__read_equivalencies()

    def __read_equivalencies(self):
        logger.info('####### read equivalencies inside linuss ########')
        try:
            with open(self._config_path, 'r') as json_file:
                equivalencies = json.load(json_file)
        except Exception as e:
            logger.debug(f'Linuss Error: {e}')
            equivalencies = json.load({})
        return equivalencies

    def __build_suggestion(self, command, options, cmd_key) -> any:
        params: list[Tuple(str)] = []
        suggestion: str = None
        explanations: list[str] = []
        tokens: list[str] = command.split()
        idx = 0
        max_idx = len(tokens) - 1
        while idx <= max_idx:
            token: str = tokens[idx]
            if re.match('-([\\w_-]+)', token):
                if idx < max_idx and (not re.match('-([\\w_-]+)', tokens[idx + 1])):
                    next_token = tokens[idx + 1]
                    params.append((token[1:], next_token))
                    idx = idx + 1
                else:
                    params.append((token[1:], None))
            elif token != cmd_key:
                params.append((None, token))
            idx = idx + 1
        if '' in options:
            suggestion = self.equivalencies[cmd_key]['']['equivalent']
        else:
            suggestion = cmd_key
        for opt, arg in params:
            if opt is not None:
                if opt[0] == '-' or len(opt) == 1:
                    equivalency = self.__get_equavalency(opt, options, cmd_key)
                    if equivalency['equivalent']:
                        suggestion = f'{suggestion} {equivalency['equivalent']}'
                        if 'explanation' in equivalency:
                            explanations.append(equivalency['explanation'])
                    else:
                        explanations.append(f'The -{opt} flag is not available on USS')
                else:
                    for char in opt:
                        equivalency = self.__get_equavalency(char, options, cmd_key)
                        if equivalency['equivalent']:
                            suggestion = f'{suggestion} {equivalency['equivalent']}'
                            if 'explanation' in equivalency:
                                explanations.append(equivalency['explanation'])
                        else:
                            explanations.append(f'The -{char} flag is not available on USS')
            if arg is not None:
                suggestion = f'{suggestion} {arg}'
        if suggestion is not None:
            return Action(suggested_command=suggestion, confidence=1, description='\n'.join(explanations))
        else:
            return Action(suggested_command=NOOP_COMMAND, description=None)

    def __get_equavalency(self, target, options, cmd_key) -> dict:
        target = f'-{target}'
        for option in options:
            if option == '':
                pass
            elif re.search('{}'.format(option), target):
                return self.equivalencies[cmd_key][option]
        return {'equivalent': target}

    def get_next_action(self, state: State) -> Action:
        command = state.command
        for cmd in self.equivalencies:
            if command.startswith(cmd):
                return self.__build_suggestion(command, self.equivalencies[cmd], cmd)
        return Action(suggested_command=NOOP_COMMAND)

def __get_equavalency(self, target, options, cmd_key) -> dict:
    target = f'-{target}'
    for option in options:
        if option == '':
            pass
        elif re.search('{}'.format(option), target):
            return self.equivalencies[cmd_key][option]
    return {'equivalent': target}

class NLC2CMD(Agent):

    def __init__(self):
        super(NLC2CMD, self).__init__()
        self.service = Service()

    def get_next_action(self, state: State) -> Action:
        command = state.command
        data, confidence = self.service(command)
        response = data['text']
        return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)

def get_next_action(self, state: State) -> Action:
    command = state.command
    data, confidence = self.service(command)
    response = data['text']
    return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)

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

def __compute(*args):
    result.append(eval('wa_skills.' + args[0])(args[1]))

class HowDoIAgent(Agent):

    def __init__(self):
        super(HowDoIAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)
        self.questionIdentifier = QuestionDetection()

    def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
        src_tokens = set([x.lower().strip() for x in src_sequence.split()])
        tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
        return len(src_tokens & tgt_tokens) / len(src_tokens)

    def get_next_action(self, state: State) -> Action:
        logger.info('================== In HowDoI Bot:get_next_action ========================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        is_question = self.questionIdentifier.is_question(state.command)
        if not is_question:
            return Action(suggested_command=state.command, confidence=0.0)
        apis: OrderedDict = self.store.get_apis()
        helpWasFound = False
        for provider in apis:
            if provider == 'manpages':
                logger.info(f"Skipping search provider 'manpages'")
                continue
            thisAPI: Provider = apis[provider]
            if not thisAPI.can_run_on_this_os():
                logger.info(f"Skipping search provider '{provider}'")
                logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
                continue
            logger.info(f"Processing search provider '{provider}'")
            if thisAPI.has_variants():
                logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
                variants: List = thisAPI.get_variants()
            else:
                logger.info(f'==> Has no search variants')
                variants: List = [None]
            for variant in variants:
                if variant is not None:
                    logger.info(f"==> Searching variant '{variant}'")
                    data = self.store.search(state.command, service=provider, size=1, searchType=variant)
                else:
                    data = self.store.search(state.command, service=provider, size=1)
                if data:
                    logger.info(f'==> Success!!! Found a result in the {thisAPI}')
                    searchResult = thisAPI.extract_search_result(data)
                    manpages = self.store.search(searchResult, service='manpages', size=5)
                    if manpages:
                        logger.info('==> Success!!! found relevant manpages.')
                        command = manpages['commands'][-1]
                        confidence = manpages['dists'][-1]
                        logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                        suggested_command = 'man {}'.format(command)
                        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                        helpWasFound = True
                        break
            if helpWasFound:
                break
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
            confidence = 0.0
        return Action(suggested_command=suggested_command, description=description, confidence=confidence)

def get_next_action(self, state: State) -> Action:
    logger.info('================== In HowDoI Bot:get_next_action ========================')
    logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
    logger.info('============================================================================')
    is_question = self.questionIdentifier.is_question(state.command)
    if not is_question:
        return Action(suggested_command=state.command, confidence=0.0)
    apis: OrderedDict = self.store.get_apis()
    helpWasFound = False
    for provider in apis:
        if provider == 'manpages':
            logger.info(f"Skipping search provider 'manpages'")
            continue
        thisAPI: Provider = apis[provider]
        if not thisAPI.can_run_on_this_os():
            logger.info(f"Skipping search provider '{provider}'")
            logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
            continue
        logger.info(f"Processing search provider '{provider}'")
        if thisAPI.has_variants():
            logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
            variants: List = thisAPI.get_variants()
        else:
            logger.info(f'==> Has no search variants')
            variants: List = [None]
        for variant in variants:
            if variant is not None:
                logger.info(f"==> Searching variant '{variant}'")
                data = self.store.search(state.command, service=provider, size=1, searchType=variant)
            else:
                data = self.store.search(state.command, service=provider, size=1)
            if data:
                logger.info(f'==> Success!!! Found a result in the {thisAPI}')
                searchResult = thisAPI.extract_search_result(data)
                manpages = self.store.search(searchResult, service='manpages', size=5)
                if manpages:
                    logger.info('==> Success!!! found relevant manpages.')
                    command = manpages['commands'][-1]
                    confidence = manpages['dists'][-1]
                    logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                    suggested_command = 'man {}'.format(command)
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                    helpWasFound = True
                    break
        if helpWasFound:
            break
    if not helpWasFound:
        logger.info('Failure: Unable to be helpful')
        logger.info('============================================================================')
        suggested_command = NOOP_COMMAND
        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
        confidence = 0.0
    return Action(suggested_command=suggested_command, description=description, confidence=confidence)

class MsgCodeAgent(Agent):

    def __init__(self):
        super(MsgCodeAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        logger.info('==================== In zMsgCode Bot:post_execute ============================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        stderr = state.stderr.strip()
        matches = re.compile(REGEX_ZMSG).match(stderr)
        if matches is None:
            logger.info(f"No Z message ID found in '{stderr}'")
            return Action(suggested_command=state.command)
        logger.info(f"Analyzing error message '{matches[0]}'")
        msgid: str = matches[2]
        helpWasFound = False
        bpx_matches: List[str] = self.__search(matches[0], REGEX_BPX)
        if bpx_matches is not None:
            reason_code: str = bpx_matches[1]
            logger.info(f'==> Reason Code: {reason_code}')
            result: CompletedProcess = subprocess.run(['bpxmtext', reason_code], stdout=subprocess.PIPE)
            if result.returncode == 0:
                messageText = result.stdout.decode('UTF8')
                if self.__search(messageText, REGEX_BPX_BADANSWER) is None:
                    suggested_command = state.command
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I asked bpxmtext about that message:\n').info().append(messageText).warning().to_console()
                    helpWasFound = True
        if not helpWasFound:
            kc_api: Provider = self.store.get_apis()['ibm_kc']
            if kc_api is not None and kc_api.can_run_on_this_os():
                data = self.store.search(msgid, service='ibm_kc', size=1)
                if data:
                    logger.info(f'==> Success!!! Found information for msgid {msgid}')
                    suggested_command = state.command
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I looked up {msgid} in the IBM KnowledgeCenter for you:\n').info().append(kc_api.get_printable_output(data)).warning().to_console()
                    helpWasFound = True
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"I couldn't find any help for message code '{msgid}'\n").info().to_console()
        return Action(suggested_command=suggested_command, description=description, confidence=1.0)

    def __search(self, target: str, regex_list: List[str]) -> List[str]:
        """Check all possible regexes in a list, return the first match encountered"""
        for regex in regex_list:
            this_match = re.compile(regex).match(target)
            if this_match is not None:
                return this_match
        return None

def get_next_action(self, state: State) -> Action:
    return Action(suggested_command=state.command)

def post_execute(self, state: State) -> Action:
    logger.info('==================== In zMsgCode Bot:post_execute ============================')
    logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
    logger.info('============================================================================')
    if state.result_code == '0':
        return Action(suggested_command=state.command)
    stderr = state.stderr.strip()
    matches = re.compile(REGEX_ZMSG).match(stderr)
    if matches is None:
        logger.info(f"No Z message ID found in '{stderr}'")
        return Action(suggested_command=state.command)
    logger.info(f"Analyzing error message '{matches[0]}'")
    msgid: str = matches[2]
    helpWasFound = False
    bpx_matches: List[str] = self.__search(matches[0], REGEX_BPX)
    if bpx_matches is not None:
        reason_code: str = bpx_matches[1]
        logger.info(f'==> Reason Code: {reason_code}')
        result: CompletedProcess = subprocess.run(['bpxmtext', reason_code], stdout=subprocess.PIPE)
        if result.returncode == 0:
            messageText = result.stdout.decode('UTF8')
            if self.__search(messageText, REGEX_BPX_BADANSWER) is None:
                suggested_command = state.command
                description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I asked bpxmtext about that message:\n').info().append(messageText).warning().to_console()
                helpWasFound = True
    if not helpWasFound:
        kc_api: Provider = self.store.get_apis()['ibm_kc']
        if kc_api is not None and kc_api.can_run_on_this_os():
            data = self.store.search(msgid, service='ibm_kc', size=1)
            if data:
                logger.info(f'==> Success!!! Found information for msgid {msgid}')
                suggested_command = state.command
                description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I looked up {msgid} in the IBM KnowledgeCenter for you:\n').info().append(kc_api.get_printable_output(data)).warning().to_console()
                helpWasFound = True
    if not helpWasFound:
        logger.info('Failure: Unable to be helpful')
        logger.info('============================================================================')
        suggested_command = NOOP_COMMAND
        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"I couldn't find any help for message code '{msgid}'\n").info().to_console()
    return Action(suggested_command=suggested_command, description=description, confidence=1.0)

class TELLINA(Agent):

    def __init__(self):
        super(TELLINA, self).__init__()

    def get_next_action(self, state: State) -> Action:
        command = state.command
        try:
            endpoint_comeback = requests.post(tellina_endpoint, json={'command': command}).json()
            response = 'Try >> ' + endpoint_comeback['response']
            confidence = float(endpoint_comeback['confidence'])
            return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)
        except Exception as ex:
            return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

def get_next_action(self, state: State) -> Action:
    command = state.command
    try:
        endpoint_comeback = requests.post(tellina_endpoint, json={'command': command}).json()
        response = 'Try >> ' + endpoint_comeback['response']
        confidence = float(endpoint_comeback['confidence'])
        return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)
    except Exception as ex:
        return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

class GITBOT(Agent):

    def __init__(self):
        super(GITBOT, self).__init__()
        self.service = Service()
    ' pre execution processing '

    def get_next_action(self, state: State) -> Action:
        command = state.command
        return self.service(command)
    ' pre execution processing '

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            self.service.parse_command(state.command, stdout='')
        return Action(suggested_command=NOOP_COMMAND)

    def save_agent(self) -> bool:
        os.system('lsof -t -i tcp:{} | xargs kill'.format(_rasa_port_number))
        super().save_agent()

def get_next_action(self, state: State) -> Action:
    command = state.command
    return self.service(command)

def post_execute(self, state: State) -> Action:
    if state.result_code == '0':
        self.service.parse_command(state.command, stdout='')
    return Action(suggested_command=NOOP_COMMAND)

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

class DATAXPLORE(Agent):

    def __init__(self):
        super(DATAXPLORE, self).__init__()

    def get_next_action(self, state: State) -> Action:
        command = state.command
        try:
            logger.info('Command passed in dataxplore: ' + command)
            commandStr = str(command)
            commandTokenized = commandStr.split(' ')
            if len(commandTokenized) == 2:
                if commandTokenized[0] == 'summarize':
                    fileName = commandTokenized[1]
                    csvFile = fileName.split('.')
                    if len(csvFile) == 2:
                        if csvFile[1] == 'csv':
                            path = os.path.abspath(fileName)
                            data = pd.read_csv(path)
                            df = pd.DataFrame(data)
                            response = df.describe().to_string()
                        else:
                            response = 'We currently support only csv files. Please, Try >> clai dataxplore summarize csvFileLocation '
                    else:
                        response = 'Not a supported file format. Please, Try >> clai dataxplore summarize csvFileLocation '
                elif commandTokenized[0] == 'plot':
                    fileName = commandTokenized[1]
                    csvFile = fileName.split('.')
                    if len(csvFile) == 2:
                        if csvFile[1] == 'csv':
                            plt.close('all')
                            path = os.path.abspath(fileName)
                            data = pd.read_csv(path, index_col=0, parse_dates=True)
                            data.plot()
                            plt.savefig('/tmp/claifigure.png')
                            im = Image.open('/tmp/claifigure.png')
                            im.show()
                            response = 'Please, check the popup for figure.'
                        else:
                            response = 'We currently support only csv files. Please, Try >> clai dataxplore plot csvFileLocation '
                    else:
                        response = 'Not a supported file format. Please, Try >> clai dataxplore plot csvFileLocation '
                else:
                    response = 'Try >> clai dataxplore function fileLocation '
            else:
                response = 'Few parts missing. Please, Try >> clai dataxplore function fileLocation '
            confidence = 0.0
            return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)
        except Exception as ex:
            return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

def get_next_action(self, state: State) -> Action:
    command = state.command
    try:
        logger.info('Command passed in dataxplore: ' + command)
        commandStr = str(command)
        commandTokenized = commandStr.split(' ')
        if len(commandTokenized) == 2:
            if commandTokenized[0] == 'summarize':
                fileName = commandTokenized[1]
                csvFile = fileName.split('.')
                if len(csvFile) == 2:
                    if csvFile[1] == 'csv':
                        path = os.path.abspath(fileName)
                        data = pd.read_csv(path)
                        df = pd.DataFrame(data)
                        response = df.describe().to_string()
                    else:
                        response = 'We currently support only csv files. Please, Try >> clai dataxplore summarize csvFileLocation '
                else:
                    response = 'Not a supported file format. Please, Try >> clai dataxplore summarize csvFileLocation '
            elif commandTokenized[0] == 'plot':
                fileName = commandTokenized[1]
                csvFile = fileName.split('.')
                if len(csvFile) == 2:
                    if csvFile[1] == 'csv':
                        plt.close('all')
                        path = os.path.abspath(fileName)
                        data = pd.read_csv(path, index_col=0, parse_dates=True)
                        data.plot()
                        plt.savefig('/tmp/claifigure.png')
                        im = Image.open('/tmp/claifigure.png')
                        im.show()
                        response = 'Please, check the popup for figure.'
                    else:
                        response = 'We currently support only csv files. Please, Try >> clai dataxplore plot csvFileLocation '
                else:
                    response = 'Not a supported file format. Please, Try >> clai dataxplore plot csvFileLocation '
            else:
                response = 'Try >> clai dataxplore function fileLocation '
        else:
            response = 'Few parts missing. Please, Try >> clai dataxplore function fileLocation '
        confidence = 0.0
        return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)
    except Exception as ex:
        return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

class IBMCloud(Agent):

    def __init__(self):
        super(IBMCloud, self).__init__()
        self.exe = KubeExe()
        self.intents = ['deploy to kube', 'build yaml', 'run Dockerfile']

    def get_next_action(self, state: State) -> Action:
        if state.command in self.intents:
            self.exe.set_goal(state.command)
            plan = self.exe.get_plan()
            if plan:
                logger.info('####### log plan inside ibmcloud ########')
                logger.info(plan)
                action_list = []
                for action in plan:
                    action_object = self.exe.execute_action(action)
                    if action_object:
                        action_list.append(action_object)
                return action_list
            else:
                return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append('Sorry could not find a plan to help! :-(').to_console(), confidence=1.0)
        else:
            return Action(suggested_command=NOOP_COMMAND)

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            self.exe.parse_command(state.command, stdout='')
        return Action(suggested_command=NOOP_COMMAND)

def get_next_action(self, state: State) -> Action:
    if state.command in self.intents:
        self.exe.set_goal(state.command)
        plan = self.exe.get_plan()
        if plan:
            logger.info('####### log plan inside ibmcloud ########')
            logger.info(plan)
            action_list = []
            for action in plan:
                action_object = self.exe.execute_action(action)
                if action_object:
                    action_list.append(action_object)
            return action_list
        else:
            return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append('Sorry could not find a plan to help! :-(').to_console(), confidence=1.0)
    else:
        return Action(suggested_command=NOOP_COMMAND)

def post_execute(self, state: State) -> Action:
    if state.result_code == '0':
        self.exe.parse_command(state.command, stdout='')
    return Action(suggested_command=NOOP_COMMAND)

class KubeTracker:

    def __init__(self):
        self.domain = open(_path_to_domain_file, mode='r', encoding='utf-8-sig').read()
        self.template = open(_path_to_problem_template, mode='r', encoding='utf-8-sig').read()
        self.obs = []
        self.goal = None
        self.local_port = None
        self.host_port = None
        self.yaml = None
        self.namespace = None
        self.cluster_name = None
        self.protocol = None
        self.name = None
        self.tag = None
        self.image_to_remove = None

    def parse_command(self, command: str, stdout: str):
        if 'docker build' in command:
            temp = command.split(':')
            self.name = temp[0].split(' ')[-1]
            self.tag = temp[1].split(' ')[0]
            self.refresh_observations()
            self.add_observation('(docker-build)')
        elif 'docker run' in command:
            self.add_observation('(docker-run)')
        elif 'ibmcloud ks clusters' in command:
            lines = stdout.split('\n')
            flag = False
            for line in lines:
                if flag:
                    self.cluster_name = line.strip().split(' ')[0].strip()
                    break
                if line.startswith('Name'):
                    flag = True
        elif 'ibmcloud account show' in command:
            if 'PAYG' not in stdout:
                self.protocol = 'NodePort'
        elif 'ibmcloud cr namespaces' in command:
            self.namespace = re.findall('Namespace\\s+\\n\\w+', stdout)[0].strip().split('\n')[-1]
        else:
            pass

    def add_observation(self, obs: str):
        self.obs.append(obs)
        return self

    def get_observations(self) -> list:
        return self.obs

    def refresh_observations(self):
        self.obs = ['set-state']
        return self

    def set_goal(self, utterance: str):
        if utterance == 'deploy to kube':
            self.goal = '(deployed)'
        elif utterance == 'run Dockerfile':
            self.goal = '(docker_running)'
        elif utterance == 'build yaml':
            self.goal = '(known yaml)'
        else:
            pass
        return self

def add_observation(self, obs: str):
    self.obs.append(obs)
    return self

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

def docker_build(self):
    command = 'docker build -t {}:{} .'.format(self.name, self.tag)
    return Action(suggested_command=command, confidence=1.0, execute=False)

def docker_run(self):
    command = 'docker run -i -p {}:{} -d {}:{}'.format(self.host_port, self.local_port, self.name, self.tag)
    return Action(suggested_command=command, confidence=1.0)

def ibmcloud_login(self):
    command = 'ibmcloud login'
    return Action(suggested_command=command, confidence=1.0)

def ibmcloud_cr_login(self):
    command = 'ibmcloud cr login'
    return Action(suggested_command=command, confidence=1.0, execute=False)

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

def ibmcloud_delete_image(self):
    command = 'ibmcloud cr image-rm us.icr.io/{}/'.format(self.namespace, self.image_to_remove)
    return Action(suggested_command=command, confidence=1.0)

def check_account_free(self):
    command = 'ibmcloud account show'
    return Action(suggested_command=command, confidence=1.0, execute=False)

def check_account_paid(self):
    command = 'ibmcloud account show'
    return Action(suggested_command=command, confidence=1.0, execute=False)

def ask_protocol(self):
    description = 'Do you want to use NodePort protocol?'
    return Action(suggested_command=NOOP_COMMAND, description=description, confidence=1.0, execute=False)

def get_set_cluster_config(self):
    if not self.cluster_name:
        self.cluster_name = '<enter-cluster-name>'
    command = 'ibmcloud ks cluster-config {} | grep -e "export" | echo'.format(self.cluster_name)
    return Action(suggested_command=command, confidence=1.0)

def kube_deploy(self):
    command = 'kubectl apply -f {}'.format(_path_to_yaml_temnplate)
    return Action(suggested_command=command, confidence=1.0)

class HelpMeAgent(Agent):

    def __init__(self):
        super(HelpMeAgent, self).__init__()
        inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
        self.store = Datastore(inifile_path)

    def compute_simple_token_similarity(self, src_sequence, tgt_sequence):
        src_tokens = set([x.lower().strip() for x in src_sequence.split()])
        tgt_tokens = set([x.lower().strip() for x in tgt_sequence.split()])
        return len(src_tokens & tgt_tokens) / len(src_tokens)

    def compute_confidence(self, query, forum, manpage):
        """
        Computes the confidence based on query, stack-exchange post answer and manpage

        Algorithm:
            1. Compute token-wise similarity b/w query and forum text
            2. Compute token-wise similarity b/w forum text and manpage description
            3. Return product of two similarities


        Args:
            query (str): standard error captured in state variable
            forum (str): answer text from most relevant stack exchange post w.r.t query
            manpage (str): manpage description for most relevant manpage w.r.t. forum

        Returns:
             confidence (float): confidence on the returned manpage w.r.t. query
        """
        query_forum_similarity = self.compute_simple_token_similarity(query, forum[0]['Content'])
        forum_manpage_similarity = self.compute_simple_token_similarity(forum[0]['Answer'], manpage)
        confidence = query_forum_similarity * forum_manpage_similarity
        return confidence

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        logger.info('==================== In Helpme Bot:post_execute ============================')
        logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
        logger.info('============================================================================')
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        apis: OrderedDict = self.store.get_apis()
        helpWasFound = False
        for provider in apis:
            if provider == 'manpages':
                logger.info(f"Skipping search provider 'manpages'")
                continue
            thisAPI: Provider = apis[provider]
            if not thisAPI.can_run_on_this_os():
                logger.info(f"Skipping search provider '{provider}'")
                logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
                continue
            logger.info(f"Processing search provider '{provider}'")
            if thisAPI.has_variants():
                logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
                variants: List = thisAPI.get_variants()
            else:
                logger.info(f'==> Has no search variants')
                variants: List = [None]
            for variant in variants:
                if variant is not None:
                    logger.info(f"==> Searching variant '{variant}'")
                    data = self.store.search(state.stderr, service=provider, size=1, searchType=variant)
                else:
                    data = self.store.search(state.stderr, service=provider, size=1)
                if data:
                    apiString = str(thisAPI)
                    if variant is not None:
                        apiString = f"{apiString} '{variant}' variant"
                    logger.info(f'==> Success!!! Found a result in the {apiString}')
                    searchResult = thisAPI.extract_search_result(data)
                    manpages = self.store.search(searchResult, service='manpages', size=5)
                    if manpages:
                        logger.info('==> Success!!! found relevant manpages.')
                        command = manpages['commands'][-1]
                        confidence = manpages['dists'][-1]
                        confidence = 1.0
                        logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                        suggested_command = 'man {}'.format(command)
                        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                        helpWasFound = True
                        break
            if helpWasFound:
                break
        if not helpWasFound:
            logger.info('Failure: Unable to be helpful')
            logger.info('============================================================================')
            suggested_command = NOOP_COMMAND
            description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
            confidence = 0.0
        return Action(suggested_command=suggested_command, description=description, confidence=confidence)

def get_next_action(self, state: State) -> Action:
    return Action(suggested_command=state.command)

def post_execute(self, state: State) -> Action:
    logger.info('==================== In Helpme Bot:post_execute ============================')
    logger.info('State:\n\tCommand: {}\n\tError Code: {}\n\tStderr: {}'.format(state.command, state.result_code, state.stderr))
    logger.info('============================================================================')
    if state.result_code == '0':
        return Action(suggested_command=state.command)
    apis: OrderedDict = self.store.get_apis()
    helpWasFound = False
    for provider in apis:
        if provider == 'manpages':
            logger.info(f"Skipping search provider 'manpages'")
            continue
        thisAPI: Provider = apis[provider]
        if not thisAPI.can_run_on_this_os():
            logger.info(f"Skipping search provider '{provider}'")
            logger.info(f'==> Excluded on platforms: {str(thisAPI.get_excludes())}')
            continue
        logger.info(f"Processing search provider '{provider}'")
        if thisAPI.has_variants():
            logger.info(f'==> Has search variants: {str(thisAPI.get_variants())}')
            variants: List = thisAPI.get_variants()
        else:
            logger.info(f'==> Has no search variants')
            variants: List = [None]
        for variant in variants:
            if variant is not None:
                logger.info(f"==> Searching variant '{variant}'")
                data = self.store.search(state.stderr, service=provider, size=1, searchType=variant)
            else:
                data = self.store.search(state.stderr, service=provider, size=1)
            if data:
                apiString = str(thisAPI)
                if variant is not None:
                    apiString = f"{apiString} '{variant}' variant"
                logger.info(f'==> Success!!! Found a result in the {apiString}')
                searchResult = thisAPI.extract_search_result(data)
                manpages = self.store.search(searchResult, service='manpages', size=5)
                if manpages:
                    logger.info('==> Success!!! found relevant manpages.')
                    command = manpages['commands'][-1]
                    confidence = manpages['dists'][-1]
                    confidence = 1.0
                    logger.info('==> Command: {} \t Confidence:{}'.format(command, confidence))
                    suggested_command = 'man {}'.format(command)
                    description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f'I did little bit of Internet searching for you, ').append(f'and found this in the {thisAPI}:\n').info().append(thisAPI.get_printable_output(data)).warning().append('Do you want to try: man {}'.format(command)).to_console()
                    helpWasFound = True
                    break
        if helpWasFound:
            break
    if not helpWasFound:
        logger.info('Failure: Unable to be helpful')
        logger.info('============================================================================')
        suggested_command = NOOP_COMMAND
        description = Colorize().emoji(Colorize.EMOJI_ROBOT).append(f"Sorry. It looks like you have stumbled across a problem that even the Internet doesn't have answer to.\n").info().append(f'Have you tried turning it OFF and ON again. ;)').to_console()
        confidence = 0.0
    return Action(suggested_command=suggested_command, description=description, confidence=confidence)

class Voice(Agent):

    def __init__(self):
        super(Voice, self).__init__()
        self._api_filename = 'openai_api.key'
        self._priming_filename = 'priming.json'
        self._tmp_filepath = os.path.join(tempfile.gettempdir(), 'tts.mp3')
        self._gpt_api = self.__init_gpt_api__()
        self.__prime_gpt_model__()

    def __init_gpt_api__(self):
        curdir = str(Path(__file__).parent.absolute())
        key_filepath = os.path.join(curdir, self._api_filename)
        with open(key_filepath, 'r') as f:
            key = f.read()
        gpt_api = GPT()
        gpt_api.set_api_key(key)
        return gpt_api

    def __prime_gpt_model__(self):
        curdir = str(Path(__file__).parent.absolute())
        priming_filepath = os.path.join(curdir, self._priming_filename)
        with open(priming_filepath, 'r') as f:
            priming_examples = json.load(f)
        for priming_set in priming_examples:
            ip, op = (priming_set['input'], priming_set['output'])
            example = Example(ip, op)
            self._gpt_api.add_example(example)

    def summarize_output(self, state):
        stderr = str(state.stderr)
        prompt = stderr.split('\n')[0]
        gpt_summary = self._gpt_api.get_top_reply(prompt, strip_output_suffix=True)
        summary = f'error. {gpt_summary}'
        return summary

    def synthesize(self, text):
        """ Converts text to audio and saves to temp file """
        tts = gTTS(text, lang='en', lang_check=False)
        tts.save(self._tmp_filepath)

    def speak(self):
        subprocess.Popen(['nohup', 'ffplay', '-nodisp', '-autoexit', '-nostats', '-hide_banner', '-loglevel', 'warning', self._tmp_filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        text_to_speak = self.summarize_output(state)
        self.synthesize(text_to_speak)
        self.speak()
        return Action(suggested_command=NOOP_COMMAND, confidence=0.01)

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

def post_execute(self, state: State) -> Action:
    if state.result_code == '0':
        return Action(suggested_command=state.command)
    text_to_speak = self.summarize_output(state)
    self.synthesize(text_to_speak)
    self.speak()
    return Action(suggested_command=NOOP_COMMAND, confidence=0.01)

def get_next_action(self, state: State) -> Action:
    return Action(suggested_command=state.command)

class FixBot(Agent):
    """
    Fixes the last executed command by running it through the `thefuck` plugin
    """

    def __init__(self):
        super(FixBot, self).__init__()
        pass

    def get_next_action(self, state: State) -> Action:
        return Action(suggested_command=state.command)

    def post_execute(self, state: State) -> Action:
        if state.result_code == '0':
            return Action(suggested_command=state.command)
        cmd = str(state.command)
        stderr = str(state.stderr)
        try:
            settings.init()
            cmd = Command(cmd, stderr)
            cmd_corrected = get_corrected_commands(cmd)
            cmd_to_run = next(cmd_corrected).script
        except Exception:
            return Action(suggested_command=state.command, confidence=0.1)
        else:
            return Action(description=Colorize().info().append('Maybe you want to try: {}'.format(cmd_to_run)).to_console(), confidence=0.8)

def get_next_action(self, state: State) -> Action:
    return Action(suggested_command=state.command)

def post_execute(self, state: State) -> Action:
    if state.result_code == '0':
        return Action(suggested_command=state.command)
    cmd = str(state.command)
    stderr = str(state.stderr)
    try:
        settings.init()
        cmd = Command(cmd, stderr)
        cmd_corrected = get_corrected_commands(cmd)
        cmd_to_run = next(cmd_corrected).script
    except Exception:
        return Action(suggested_command=state.command, confidence=0.1)
    else:
        return Action(description=Colorize().info().append('Maybe you want to try: {}'.format(cmd_to_run)).to_console(), confidence=0.8)

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

def get_command_tldr(cmd):
    if not TLDR_AVAILABLE:
        return ''
    cmd_tldr = tldr.get_page(cmd)
    if cmd_tldr is None:
        return ''
    description = Colorize()
    for i, line in enumerate(cmd_tldr):
        line = line.rstrip().decode('utf-8')
        if i == 0:
            description.append('-' * 50 + '\n')
        if len(line) < 1:
            description.append('\n')
        elif line[0] == '#':
            line = line[1:]
            description.warning().append(line.strip() + '\n')
        elif line[0] == '>':
            line = ' ' + line[1:]
            description.normal().append(line.strip() + '\n')
        elif line[0] == '-':
            description.normal().append(line.strip() + '\n')
        elif line[0] == '`':
            line = ' ' + line[1:-1]
            description.info().append(line.strip() + '\n')
    description.normal().append('summary provided by tldr package\n')
    description.normal().append('-' * 50 + '\n')
    return description.to_console()

@app.route('/findManPage/', methods=['POST'])
def find_man_page():
    try:
        text = request.args.get('text', None)
        result_count = request.args.get('result_count', 1)
        result_count = int(result_count)
        if text is None:
            return
        result = _DATASTORE.search(text.strip(), result_count)
        commands = [x[0] for x in result]
        dists = [x[1] for x in result]
    except Exception as err:
        payload = {'result': 'error', 'message': str(err)}
    else:
        payload = {'status': 'success', 'commands': commands, 'dists': dists}
    finally:
        return jsonify(payload)

class KnowledgeCenter(Provider):

    def __init__(self, name: str, description: str, section: dict):
        super().__init__(name, description, section)
        for variant in self.get_variants():
            if variant.name not in KCtype.__members__.keys():
                raise AttributeError(f"Invalid {self.name} search variant: '{variant.name}'")
        self.__log_debug__('z/OS KnowledgeCenter provider initialized')

    def get_variants(self) -> List[KCtype]:
        """Override the default get_variants() method so that it instead returns
        a list of KCtype objects"""
        types = []
        for type_str in super().get_variants():
            types.append(KCtype[type_str])
        return types

    def call(self, query: str, limit: int=1, **kwargs):
        """Call the KnowledgeCenter search provider.  If no search variants
        were specified in the configuration file, we will default to searching
        the KnowledgeCenter documentation (ie: IBM publications) library"""
        kwargs = self.__set_default_values__(kwargs, search_type=KCtype.DOCUMENTATION, products=KCscope.ZOS_240, tags='bpx')
        self.__log_debug__(f'call(query={query}, limit={str(limit)}, **kwargs={str(kwargs)})')
        search_type: KCtype = kwargs['search_type']
        target: str = urljoin(self.base_uri, search_type.value)
        payload = {'query': query, 'offset': 0, 'limit': limit, 'tags': kwargs['tags']}
        products: KCscope = kwargs['products']
        if search_type in (KCtype.DOCUMENTATION, KCtype.TECHNOTES):
            payload['products'] = products.value
        request = self.__send_get_request__(target, params=payload)
        if request.status_code == 200:
            if request.json()['count'] > 0:
                if search_type == KCtype.DOCUMENTATION:
                    return request.json()['topics']
                return request.json()['results']
        return None

    def extract_search_result(self, data: List[Dict]) -> str:
        self.__log_debug__(f'extract_search_result() returns {data[0]['summary']}')
        return data[0]['summary']

    def get_printable_output(self, data: List[Dict]) -> str:
        if 'products' in data[0].keys():
            topic: Dict = data[0]
            product: Dict = topic['products'][0]
            lines = [f'Product: {product['label']}', f'Topic: {__clean__(topic['label'][:384] + ' ...')}', f'Answer: {__clean__(topic['summary'][:256] + ' ...')}', f'Tags: {str(topic['tags'])}', f'Link: https://www.ibm.com/support/knowledgecenter/{topic['href']}\n']
        else:
            result: Dict = data[0]
            lines = [f'Title: {__clean__(result['title'][:384] + ' ...')}', f'Answer: {__clean__(result['summary'][:256] + ' ...')}', f'Link: {result['link']}\n']
        self.__log_debug__(f'get_printable_output() returns {str(lines)}')
        return '\n'.join(lines)

def get_variants(self) -> List[KCtype]:
    """Override the default get_variants() method so that it instead returns
        a list of KCtype objects"""
    types = []
    for type_str in super().get_variants():
        types.append(KCtype[type_str])
    return types

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

def __log_info__(self, message):
    logger.info(f'{self.name}: {message}')

def __log_warning__(self, message):
    logger.warning(f'{self.name}: {message}')

class OrchestratorStorage:

    def __init__(self, orchestrator_provider: OrchestratorProvider, remote_storage: ActionRemoteStorage):
        self._memory: List[TerminalReplayMemoryComplete] = []
        self.orchestrator_provider = orchestrator_provider
        self.remote_storage = remote_storage

    def store_pre(self, replay_pre: TerminalReplayMemory):
        terminal_replay_complete = TerminalReplayMemoryComplete()
        terminal_replay_complete.pre_replay = replay_pre
        self._memory.append(terminal_replay_complete)
        self.__notify_orchestrator(replay_pre)

    def store_post(self, replay_post: TerminalReplayMemory):
        if self._memory:
            self._memory[-1].post_replay = replay_post

    def __notify_orchestrator(self, current_pre: TerminalReplayMemory):
        if len(self._memory) > 1:
            previous_replay = self._memory.pop(0)
            orchestrator = self.orchestrator_provider.get_current_orchestrator()
            orchestrator.record_transition(previous_replay, current_pre)
            self.remote_storage.store(previous_replay.post_replay)

def store_pre(self, replay_pre: TerminalReplayMemory):
    terminal_replay_complete = TerminalReplayMemoryComplete()
    terminal_replay_complete.pre_replay = replay_pre
    self._memory.append(terminal_replay_complete)
    self.__notify_orchestrator(replay_pre)

def print_complete(text):
    print(Colorize().complete().append(text).to_console())

def print_error(text):
    print(Colorize().warning().append(text).to_console())

def __send_event__(event: StatEvent):
    try:
        amplitude_logger = amplitude.AmplitudeLogger(api_key='cc826565c91ab899168235a2845db189')
        event_args = {'device_id': event.user, 'event_type': event.event_type, 'event_properties': event.data}
        event = amplitude_logger.create_event(**event_args)
        amplitude_logger.log_event(event)
    except Exception as ex:
        logger.info(f'error tracking event {ex}')

