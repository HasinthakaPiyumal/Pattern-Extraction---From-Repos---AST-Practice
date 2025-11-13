# Cluster 8

def remove_system_folder(path: str=None):
    if path is not None:
        default_system_destdir = '/'.join(path.split('/')[0:-1])
    else:
        default_system_destdir = os.path.join(os.path.expanduser('/opt/local/share'), 'clai')
    remove(default_system_destdir)

def clai_installed(rc_file_path):
    path = os.path.expanduser(rc_file_path)
    if os.path.isfile(path):
        line_to_search = 'export CLAI_PATH='
        print('searching %s' % line_to_search)
        lines = io.open(path, 'r', encoding='utf-8', errors='ignore').readlines()
        lines_found = list(filter(lambda line: line_to_search in line, lines))
        if lines_found:
            my_path = lines_found[0].replace(line_to_search, '').replace('\n', '').strip()
            return my_path
    return None

def read_users(bin_path):
    try:
        with open(bin_path + '/usersInstalled.json') as file:
            users = json.load(file)
            return users
    except:
        return []

def unregister_the_user(bin_path):
    users = read_users(bin_path)
    user_path = os.path.expanduser(get_rc_file())
    if user_path in users:
        users.remove(user_path)
    with open(bin_path + '/usersInstalled.json', 'w') as json_file:
        json.dump(users, json_file)
    return users

def remove_setup_file(rc_file_path):
    path = os.path.expanduser(rc_file_path)
    os.remove(path)

def remove_between(rc_file_path, start, end):
    path = os.path.expanduser(rc_file_path)
    if os.path.isfile(path):
        codeset = 'utf-8'
        lines = []
        if is_rw_with_EBCDIC(path):
            codeset = 'cp1047'
            newline = '\x85'
            for err_line in open(path, 'r', encoding=codeset, errors='ignore').readlines():
                right_line_list = err_line.split(newline)
                length = len(right_line_list)
                i = 0
                for right_line in right_line_list:
                    i = i + 1
                    if right_line or length != i:
                        lines.append(right_line + newline)
        else:
            lines = open(path, 'r', encoding=codeset, errors='ignore').readlines()
        remove_line = False
        lines_after_remove = []
        for line in lines:
            if line.strip() == start.strip():
                remove_line = True
            if not remove_line:
                lines_after_remove.append(line)
            if line.strip() == end.strip():
                remove_line = False
        io.open(path, 'w', encoding=codeset).writelines(lines_after_remove)

def clai_installed(path):
    expand_path = os.path.expanduser(path)
    return os.path.isfile(expand_path)

def binary_installed(path):
    return os.path.exists(path)

def mkdir(path):
    print('creating directory: %s' % path)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def read_users(bin_path):
    with open(bin_path + '/usersInstalled.json') as json_file:
        users = json.load(json_file)
        return users

def register_the_user(bin_path, system):
    users = read_users(bin_path)
    user_path = os.path.expanduser(get_rc_file(system))
    if user_path not in users:
        users.append(user_path)
    with open(bin_path + '/usersInstalled.json', 'w') as json_file:
        json.dump(users, json_file)

def create_rc_file_if_not_exist(system):
    rc_file_path = os.path.expanduser(get_rc_file(system))
    if not os.path.isfile(rc_file_path):
        open(rc_file_path, 'a').close()

def createInstallDir(directory):
    try:
        if not os.path.exists(directory):
            print(f'creating install directory: {directory}')
            os.makedirs(directory, exist_ok=True)
        else:
            print(f'Install directory already exists')
    except Exception as e:
        print(e)
        sys.exit(1)

def test_should_remove_when_not_commands():
    lines = []
    new_lines = __remove_clai_history__(lines, 'ls')
    assert new_lines == []

def test_should_remove_the_list_if_only_one_command():
    lines = ['ls']
    new_lines = __remove_clai_history__(lines, 'ls')
    assert new_lines == ['ls']

def test_should_remove_last_command_if_have_two_repeat():
    lines = ['pwd', 'ls', 'ls']
    new_lines = __remove_clai_history__(lines, 'ls')
    assert new_lines == ['pwd', 'ls']

def test_should_remove_nothing_if_have_only_the_command():
    lines = ['pwd', 'ls']
    new_lines = __remove_clai_history__(lines, 'ls')
    assert new_lines == ['pwd', 'ls']

def test_should_remove_dirty_until_the_command():
    lines = ['pwd', 'ls', 'pwd', 'cd']
    new_lines = __remove_clai_history__(lines, 'ls')
    assert new_lines == ['pwd', 'ls']

def test_should_not_remove_if_command_not_exist():
    lines = ['pwd', 'ls']
    new_lines = __remove_clai_history__(lines, 'ls -la')
    assert new_lines == ['pwd', 'ls']

def test_should_remove_dirt_if_it_is_the_first_comment():
    lines = ['clai', ':']
    new_lines = __remove_clai_history__(lines, 'clai')
    assert new_lines == ['clai']

def override_last_command(last_command):
    lines = read_history()
    if lines:
        new_last_line = lines[-1].rstrip() + last_command
        lines[-1] = new_last_line
    else:
        lines.append(last_command)
    io.open(get_history_file_name(), 'w').writelines(lines)

def restore_history(original_command: str):
    lines = read_history()
    new_lines = __remove_clai_history__(lines, original_command + '\n')
    io.open(get_history_file_name(), 'w').writelines(new_lines)

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

def __unselect_plugin_for_user(self, plugin_to_select, user_name):
    if user_name in self.__selected_plugin and plugin_to_select in self.__selected_plugin[user_name]:
        self.__selected_plugin[user_name].remove(plugin_to_select)

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

def debug(self, text):
    self.logger.debug(text)

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

def __read_equivalencies(self):
    logger.info('####### read equivalencies inside linuss ########')
    try:
        with open(self._config_path, 'r') as json_file:
            equivalencies = json.load(json_file)
    except Exception as e:
        logger.debug(f'Linuss Error: {e}')
        equivalencies = json.load({})
    return equivalencies

class QuestionDetection(object):

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

    def is_question(self, text):
        """
        A function to check if text is phrased as a question.

        Algorithm:
            1. Test if the text ends with "?". If yes, then it's a question.
            2. Test if the text contains any "WH" word tags (indicative of WH type of question)

        Args:
            text (str): a text to be tested

        Returns:
            (bool): True if the text is a question.
        """
        if text.endswith('?'):
            return True
        doc = self.nlp(text)
        for token in doc:
            if token.tag_ in self.WH_TAGS:
                return True
        return False

def __init__(self):
    self.nlp = spacy.load('en_core_web_sm')
    self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

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

def build_yaml(self):
    app_yaml = open(_path_to_yaml_temnplate, 'r').read()
    app_yaml = app_yaml.replace('{name}', self.name).replace('{tag}', self.tag).replace('{namespace}', self.namespace).replace('{protocol}', self.protocol).replace('{host_port}', self.host_port).replace('{local_port}', self.local_port)
    with open(_real_path + '/app.yaml', 'w') as f:
        f.write(app_yaml)
    self.yaml = app_yaml
    return Action(suggested_command=NOOP_COMMAND, description=self.yaml)

class QuestionDetection(object):

    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

    def is_question(self, text):
        if text.endswith('?'):
            return True
        doc = self.nlp(text)
        for token in doc:
            if token.tag_ in self.WH_TAGS:
                return True
        return False

def __init__(self):
    self.nlp = spacy.load('en_core_web_sm')
    self.WH_TAGS = ['WDT', 'WP', 'WP$', 'WRB']

class Datastore:

    def __init__(self):
        self.path = './data'
        self.transformer_func, self.vectors, self.commands = self.read()

    def read(self):
        with open(self.path + '/model/func.p', 'rb') as f:
            transformer_func = pickle.load(f)
        with open(self.path + '/model/vectors.p', 'rb') as f:
            vectors = pickle.load(f)
        with open(self.path + '/model/keys.p', 'rb') as f:
            commands = pickle.load(f)
        return (transformer_func, vectors, commands)

    def search(self, query, size=1):
        vector = self.transformer_func.transform([query])
        dist = cosine_similarity(self.vectors, vector).reshape(-1)
        return [(self.commands[i], dist[i]) for i in np.argsort(dist)[-size:]]

def read(self):
    with open(self.path + '/model/func.p', 'rb') as f:
        transformer_func = pickle.load(f)
    with open(self.path + '/model/vectors.p', 'rb') as f:
        vectors = pickle.load(f)
    with open(self.path + '/model/keys.p', 'rb') as f:
        commands = pickle.load(f)
    return (transformer_func, vectors, commands)

def load_manpages(print_every=1000.0) -> dict:
    logging.info('==================================')
    logging.info('Processing manpages')
    logging.info('==================================')
    documents = {}
    files = pathlib.Path('./data/manpages/').glob('*.txt')
    for idx, f in enumerate(files):
        with open(f, 'r') as fp:
            content = parse_manpage(fp.readlines())
            if content:
                documents[f.name.split('.txt')[0]] = content
        if idx % print_every == 0:
            msg = 'Finished processing {} manpages.'.format(idx)
            logging.info(msg)
    return documents

def save(func, vectors, keys):
    with open(absolute_path('./data/model/func.p'), 'wb') as fp:
        pickle.dump(func, fp)
    with open(absolute_path('./data/model/vectors.p'), 'wb') as fp:
        pickle.dump(vectors, fp)
    with open(absolute_path('./data/model/keys.p'), 'wb') as fp:
        pickle.dump(keys, fp)

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

def __log_debug__(self, message):
    logger.debug(f'{self.name}: {message}')

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

class MaxOrchestrator(Orchestrator):

    def __init__(self):
        super(MaxOrchestrator, self).__init__()
        self._config_path = os.path.join(Path(__file__).parent.absolute(), 'config.json')
        self.__read_config__()

    def __read_config__(self):
        with open(self._config_path, 'r') as fileobj:
            config = json.load(fileobj)
        self.threshold = config['threshold']

    def choose_action(self, command: State, agent_names: List[str], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Action]:
        """Choose an action for CLAI to respond with"""
        if not candidate_actions:
            return None
        confs = [self.__calculate_confidence__(action) for action in candidate_actions]
        idx_maxconf = np.argmax(confs)
        max_conf = confs[idx_maxconf]
        selected_candidate = candidate_actions[idx_maxconf]
        if force_response:
            return selected_candidate
        if max_conf >= self.threshold:
            return selected_candidate
        return None

def __read_config__(self):
    with open(self._config_path, 'r') as fileobj:
        config = json.load(fileobj)
    self.threshold = config['threshold']

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

def load_bandit_state(self):
    with open(self._bandit_config_filepath, 'r') as conf_file:
        bandit_config = json.load(conf_file)
    self._noop_confidence = bandit_config['noop_confidence']
    self._warm_start = bandit_config['warm_start']
    self._warm_start_type = bandit_config['warm_start_config']['type']
    self._warm_start_kwargs = bandit_config['warm_start_config']['kwargs']
    self._reward_match_threshold = bandit_config.get('reward_match_threshold', 0.7)

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

def __read_config(self):
    with open(self._config_path, 'r') as fileobj:
        config = json.load(fileobj)
    self.threshold = config['threshold']
    self.preferences = config['preferences']

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

def get_all_examples(self):
    """Returns all examples as a list of dicts."""
    return {k: v.as_dict() for k, v in self.examples.items()}

def is_rw_with_EBCDIC(file):
    is_EBCDIC = False
    file_path_complete = os.path.expanduser(file)
    if is_zos():
        if not os.path.exists(file_path_complete):
            is_EBCDIC = True
        else:
            cmd = 'chtag -p ' + file_path_complete + " | cut -d ' ' -f 2,6 "
            pfile = os.popen(cmd, 'r')
            output = pfile.read().strip()
            if output in ('untagged T=off', 'IBM-1047 T=off'):
                is_EBCDIC = True
            pfile.close()
    return is_EBCDIC

def append_to_file(file_path, value_to_append, codeset='utf-8'):
    file_path_complete = os.path.expanduser(file_path)
    print('append to file %s' % file_path_complete)
    with open(os.path.expanduser(file_path_complete), 'a+', encoding=codeset) as file:
        file.write(value_to_append)

def read_history():
    history_file_name = get_history_file_name()
    if os.path.isfile(history_file_name):
        return io.open(history_file_name, 'r', encoding='utf-8', errors='ignore').readlines()
    return []

class Anonymizer:

    def __init__(self, alternate_path: Optional[str]=None):
        self.__cache: Mapping[str, str] = None
        self.alternate_path = alternate_path

    def __get_config_path__(self):
        if self.alternate_path:
            return self.alternate_path
        base_dir = os.path.dirname(clai.tools.__file__)
        filename = os.path.join(base_dir, '../../anonymize.json')
        return filename

    def anonymize(self, key: str) -> str:
        if not self.__cache:
            self.__init_cache__()
        if key in self.__cache:
            return self.__cache[key]
        return self.__create_anonymize(key)

    def __init_cache__(self):
        path = self.__get_config_path__()
        if not os.path.exists(path):
            self.__cache = {}
            return
        with open(path) as verify_file:
            self.__cache = json.load(verify_file)

    def __create_anonymize(self, key: str) -> str:
        self.__cache[key] = str(uuid.uuid4())
        with open(self.__get_config_path__(), 'w+') as json_file:
            json.dump(self.__cache, json_file)
        return self.__cache[key]

def __init_cache__(self):
    path = self.__get_config_path__()
    if not os.path.exists(path):
        self.__cache = {}
        return
    with open(path) as verify_file:
        self.__cache = json.load(verify_file)

def __create_anonymize(self, key: str) -> str:
    self.__cache[key] = str(uuid.uuid4())
    with open(self.__get_config_path__(), 'w+') as json_file:
        json.dump(self.__cache, json_file)
    return self.__cache[key]

class ConfigStorage:

    def __init__(self, alternate_path: Optional[str]=None):
        self.alternate_path = alternate_path

    def get_config_path(self):
        if self.alternate_path:
            return self.alternate_path
        base_dir = os.path.dirname(clai.datasource.__file__)
        filename = os.path.join(base_dir, '../../configPlugins.json')
        return filename

    def read_all_user_config(self) -> PluginConfigJson:
        with open(self.get_config_path(), 'r') as json_file:
            loaded = json.load(json_file)
            config_for_all_users = PluginConfigJson(**loaded)
            return config_for_all_users

    def read_config(self, user_name: Optional[str]=None) -> PluginConfig:
        selected = None
        config_for_all_users = self.read_all_user_config()
        if user_name in config_for_all_users.selected:
            selected = config_for_all_users.selected[user_name]
        if not selected:
            if isinstance(config_for_all_users.default, str):
                selected = [config_for_all_users.default]
            else:
                selected = config_for_all_users.default
        return PluginConfig(selected=selected, default=config_for_all_users.default, default_orchestrator=config_for_all_users.default_orchestrator, installed=config_for_all_users.installed, report_enable=config_for_all_users.report_enable, user_install=config_for_all_users.user_install)

    def store_config(self, config: PluginConfig, user_name: str=None):
        current_config = self.read_all_user_config()
        with open(self.get_config_path(), 'w') as json_file:
            if user_name:
                current_config.selected[user_name] = config.selected
            current_config.installed = config.installed
            current_config.report_enable = config.report_enable
            current_config.orchestrator = config.orchestrator
            current_config.user_install = config.user_install
            json_as_string = str(current_config.json())
            json_file.write(json_as_string)

    def load_installed(self) -> List[str]:
        current_config = self.read_all_user_config()
        return current_config.installed

def read_all_user_config(self) -> PluginConfigJson:
    with open(self.get_config_path(), 'r') as json_file:
        loaded = json.load(json_file)
        config_for_all_users = PluginConfigJson(**loaded)
        return config_for_all_users

def read_config(self, user_name: Optional[str]=None) -> PluginConfig:
    selected = None
    config_for_all_users = self.read_all_user_config()
    if user_name in config_for_all_users.selected:
        selected = config_for_all_users.selected[user_name]
    if not selected:
        if isinstance(config_for_all_users.default, str):
            selected = [config_for_all_users.default]
        else:
            selected = config_for_all_users.default
    return PluginConfig(selected=selected, default=config_for_all_users.default, default_orchestrator=config_for_all_users.default_orchestrator, installed=config_for_all_users.installed, report_enable=config_for_all_users.report_enable, user_install=config_for_all_users.user_install)

def store_config(self, config: PluginConfig, user_name: str=None):
    current_config = self.read_all_user_config()
    with open(self.get_config_path(), 'w') as json_file:
        if user_name:
            current_config.selected[user_name] = config.selected
        current_config.installed = config.installed
        current_config.report_enable = config.report_enable
        current_config.orchestrator = config.orchestrator
        current_config.user_install = config.user_install
        json_as_string = str(current_config.json())
        json_file.write(json_as_string)

def load_installed(self) -> List[str]:
    current_config = self.read_all_user_config()
    return current_config.installed

