# Cluster 2

@unittest.skipIf(OS_NAME not in ('OS/390', 'Z/OS'), 'Test only valid on z/OS')
class MsgCodeAgentTest(unittest.TestCase):

    @classmethod
    def set_up_class(cls):
        _agent = MsgCodeAgent()
        cls.agent = _agent

    @classmethod
    def try_command(cls, command_and_args: List[str]) -> Action:
        result: CompletedProcess = subprocess.run(command_and_args, encoding='UTF8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        command: str = None
        if isinstance(result.args, list):
            command = ' '.join(result.args)
        else:
            command = result.args
        result_code: str = str(result.returncode)
        return cls.scaffold_command_response(command=command, result_code=result_code, stdout=result.stdout, stderr=result.stderr)

    @classmethod
    def scaffold_command_response(cls, **kwargs) -> Action:
        state = State(command_id='0', user_name='tester', command=kwargs['command'], result_code=kwargs['result_code'], stderr=kwargs['stderr'])
        print(f'Command: {kwargs['command']}')
        print(f'RetCode: {kwargs['result_code']}')
        print(f"stdout: '{kwargs['stdout']}'")
        print(f"stderr: '{kwargs['stderr']}'")
        print('===========================')
        action = cls.agent.post_execute(state=state)
        print('Input: {}'.format(state.command))
        print('===========================')
        print('Response: {}'.format(action.suggested_command))
        print('===========================')
        print('Explanation: {}'.format(action.description))
        return action

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_message_bad_cd(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            action = self.try_command(['cd', our_file.name])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
        self.assertEqual('Action: Reissue the service specifying a directory file.', lines[-2])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_message_bad_cat(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            file_that_isnt_there: str = our_file.name
        action = self.try_command(['cat', file_that_isnt_there])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I asked bpxmtext about that message:', lines[0])
        self.assertEqual('Action: The open service request cannot be processed. Correct the name or the', lines[-3])
        self.assertEqual('open flags and retry the operation.', lines[-2])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_unhelpful_message_1(self):
        self.agent.init_agent()
        action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDFDFDF')
        lines = action.description.strip().split('\n')
        self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

    @unittest.skip('Only for local testing')
    def test_bpxmtextable_unhelpful_message_2(self):
        self.agent.init_agent()
        action = self.scaffold_command_response(command=['not', 'a', 'real', 'command'], result_code=str(1), stdout='', stderr='IEB4223I 0xDFDF')
        lines = action.description.strip().split('\n')
        self.assertEqual(f"{Colorize.EMOJI_ROBOT}I couldn't find any help for message code 'IEB4223I'", lines[0])

    @unittest.skip('Only for local testing')
    def test_bad_cp(self):
        self.agent.init_agent()
        with tempfile.NamedTemporaryFile() as our_file:
            action = self.try_command(['cp', our_file.name, our_file.name])
        lines = action.description.strip().split('\n')
        self.assertEqual(f'{Colorize.EMOJI_ROBOT}I looked up FSUM8977 in the IBM KnowledgeCenter for you:', lines[0])
        self.assertEqual(f'{Colorize.INFO}Product: z/OS', lines[1])
        self.assertEqual('Topic: FSUM8977 ...', lines[2])

@classmethod
def try_command(cls, command_and_args: List[str]) -> Action:
    result: CompletedProcess = subprocess.run(command_and_args, encoding='UTF8', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    command: str = None
    if isinstance(result.args, list):
        command = ' '.join(result.args)
    else:
        command = result.args
    result_code: str = str(result.returncode)
    return cls.scaffold_command_response(command=command, result_code=result_code, stdout=result.stdout, stderr=result.stderr)

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

def __init__(self):
    self.agent_name = self.__class__.__name__
    self.ready = False
    self._save_basedir = os.path.join(BASEDIR, 'saved_agents')
    self._save_dirpath = os.path.join(self._save_basedir, self.agent_name)

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

def __init__(self):
    super(Linuss, self).__init__()
    self._config_path = os.path.join(Path(__file__).parent.absolute(), 'equivalencies.json')
    self.equivalencies = self.__read_equivalencies()

class NLC2CMD(Agent):

    def __init__(self):
        super(NLC2CMD, self).__init__()
        self.service = Service()

    def get_next_action(self, state: State) -> Action:
        command = state.command
        data, confidence = self.service(command)
        response = data['text']
        return Action(suggested_command=NOOP_COMMAND, execute=True, description=Colorize().info().append(response).to_console(), confidence=confidence)

def __init__(self):
    super(NLC2CMD, self).__init__()
    self.service = Service()

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

def __init__(self):
    config = configparser.ConfigParser()
    config.read(os.path.join(str(Path(__file__).parent.absolute()), 'config.ini'))
    self.stack_exchange_api = config['API'].get('stack_exchange_api')
    self.manpage_api = config['API'].get('manpage_api')

def search(self, query, service='stack_exchange', size=10):
    if service == 'stack_exchange':
        res = self.__call_stack_exchange_api__(query, size)
    elif service == 'manpages':
        res = self.__call_manpage_api__(query, size)
    else:
        raise AttributeError('Please select stack_exchange or manpage as a choice for service')
    return res

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

def __init__(self):
    super(HowDoIAgent, self).__init__()
    inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
    self.store = Datastore(inifile_path)
    self.questionIdentifier = QuestionDetection()

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

def __init__(self):
    super(MsgCodeAgent, self).__init__()
    inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
    self.store = Datastore(inifile_path)

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

def __init__(self):
    super(TELLINA, self).__init__()

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

def __init__(self):
    super(GITBOT, self).__init__()
    self.service = Service()

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

def __init__(self):
    super(DATAXPLORE, self).__init__()

class GPT3(Agent):

    def __init__(self):
        super(GPT3, self).__init__()
        self._gpt3_api = self.__init_gpt3_api__()

    def __init_gpt3_api__(self):
        current_directory = str(Path(__file__).parent.absolute())
        path_to_gpt3_key = os.path.join(current_directory, 'openai_api.key')
        path_to_gpt3_prompts = os.path.join(current_directory, 'prompt.json')
        gpt3_key = open(path_to_gpt3_key, 'r').read()
        gpt3_prompts = json.load(open(path_to_gpt3_prompts, 'r'))
        gpt3_api = GPT(temperature=0)
        gpt3_api.set_api_key(gpt3_key)
        for prompt in gpt3_prompts:
            ip, op = (prompt['input'], prompt['output'])
            example = Example(ip, op)
            gpt3_api.add_example(example)
        return gpt3_api

    def get_next_action(self, state: State) -> Action:
        command = state.command
        command = command[:1000]
        try:
            response = self._gpt3_api.get_top_reply(command, strip_output_suffix=True)
            response = response.strip()
            return Action(suggested_command=response, execute=False, description='Currently the GPT-3 skill does not provide an explanation. Got an idea? Contribute to CLAI!', confidence=0.0)
        except Exception as ex:
            return [{'text': 'Method failed with status ' + str(ex)}, 0.0]

def __init__(self):
    super(GPT3, self).__init__()
    self._gpt3_api = self.__init_gpt3_api__()

def __init_gpt3_api__(self):
    current_directory = str(Path(__file__).parent.absolute())
    path_to_gpt3_key = os.path.join(current_directory, 'openai_api.key')
    path_to_gpt3_prompts = os.path.join(current_directory, 'prompt.json')
    gpt3_key = open(path_to_gpt3_key, 'r').read()
    gpt3_prompts = json.load(open(path_to_gpt3_prompts, 'r'))
    gpt3_api = GPT(temperature=0)
    gpt3_api.set_api_key(gpt3_key)
    for prompt in gpt3_prompts:
        ip, op = (prompt['input'], prompt['output'])
        example = Example(ip, op)
        gpt3_api.add_example(example)
    return gpt3_api

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

def __init__(self):
    super(IBMCloud, self).__init__()
    self.exe = KubeExe()
    self.intents = ['deploy to kube', 'build yaml', 'run Dockerfile']

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

def __init__(self):
    super().__init__()
    self.refresh_observations()

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

def __init__(self):
    super(HelpMeAgent, self).__init__()
    inifile_path = os.path.join(str(Path(__file__).parent.absolute()), 'config.ini')
    self.store = Datastore(inifile_path)

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

def __init__(self):
    config = configparser.ConfigParser()
    config.read(os.path.join(str(Path(__file__).parent.absolute()), 'config.ini'))
    self.stack_exchange_api = config['API'].get('stack_exchange_api')
    self.manpage_api = config['API'].get('manpage_api')

def search(self, query, service='stack_exchange', size=10):
    if service == 'stack_exchange':
        res = self.__call_stack_exchange_api__(query, size)
    elif service == 'manpages':
        res = self.__call_manpage_api__(query, size)
    else:
        raise AttributeError('Please select stack_exchange or manpage as a choice for service')
    return res

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

def __init__(self):
    super(FixBot, self).__init__()
    pass

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

def __init__(self):
    self.path = './data'
    self.transformer_func, self.vectors, self.commands = self.read()

def absolute_path(relative_path):
    return os.path.join(_BASE_PATH, relative_path)

def parse_manpage(text: list) -> str:
    return ' '.join(identify_sections(text))

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

def __init__(self, name: str, description: str, section: dict):
    super().__init__(name, description, section)
    for variant in self.get_variants():
        if variant.name not in KCtype.__members__.keys():
            raise AttributeError(f"Invalid {self.name} search variant: '{variant.name}'")
    self.__log_debug__('z/OS KnowledgeCenter provider initialized')

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

def __init__(self, name: str, description: str, section: dict):
    super().__init__(name, description, section)
    self.__log_debug__('UNIX StackExchange provider initialized')

def get_printable_output(self, data: List[Dict]) -> str:
    lines = [f'Post: {data[0]['Content'][:384] + ' ...'}', f'Answer: {data[0]['Answer'][:256] + ' ...'}', f'Link: {data[0]['Url']}\n']
    return '\n'.join(lines)

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

def __init__(self, name: str, description: str, section: dict):
    super().__init__(name, description, section)
    self.__log_debug__('Manpages provider initialized')

class Datastore:
    apis: OrderedDict = {}

    def __init__(self, inifile_path: str):
        config = configparser.ConfigParser()
        config.read(inifile_path)
        for section in config.sections():
            if section == 'stack_exchange':
                self.apis[section] = StackExchange(section, 'Unix StackExchange forums', config[section])
            elif section == 'ibm_kc':
                self.apis[section] = KnowledgeCenter(section, 'IBM KnowledgeCenter', config[section])
            elif section == 'manpages':
                self.apis[section] = Manpages(section, 'manpages', config[section])
            else:
                raise AttributeError(f"Unsupported service type: '{section}'")
        logger.debug(f'Sections in {inifile_path}: {str(self.apis)}')

    def get_apis(self) -> OrderedDict:
        return self.apis

    def search(self, query, service='stack_exchange', size=10, **kwargs) -> List[Dict]:
        supported_services = self.apis.keys()
        if service in supported_services:
            service_provider = self.apis[service]
            res = service_provider.call(query, size, **kwargs)
        else:
            raise AttributeError(f'service must be one of: {str(supported_services)}')
        return res

def __init__(self, inifile_path: str):
    config = configparser.ConfigParser()
    config.read(inifile_path)
    for section in config.sections():
        if section == 'stack_exchange':
            self.apis[section] = StackExchange(section, 'Unix StackExchange forums', config[section])
        elif section == 'ibm_kc':
            self.apis[section] = KnowledgeCenter(section, 'IBM KnowledgeCenter', config[section])
        elif section == 'manpages':
            self.apis[section] = Manpages(section, 'manpages', config[section])
        else:
            raise AttributeError(f"Unsupported service type: '{section}'")
    logger.debug(f'Sections in {inifile_path}: {str(self.apis)}')

def search(self, query, service='stack_exchange', size=10, **kwargs) -> List[Dict]:
    supported_services = self.apis.keys()
    if service in supported_services:
        service_provider = self.apis[service]
        res = service_provider.call(query, size, **kwargs)
    else:
        raise AttributeError(f'service must be one of: {str(supported_services)}')
    return res

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

def __init__(self):
    self.orchestrator_name = self.__class__.__name__
    self._save_basedir = os.path.join(BASEDIR, 'saved_orchestrators')
    self._save_dirpath = os.path.join(self._save_basedir, self.orchestrator_name)
    self.noop_command = NOOP_COMMAND

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

def __init__(self):
    super(MaxOrchestrator, self).__init__()
    self._config_path = os.path.join(Path(__file__).parent.absolute(), 'config.json')
    self.__read_config__()

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

def __init__(self):
    super(PreferenceOrchestrator, self).__init__()
    self._config_path = os.path.join(Path(__file__).parent.absolute(), 'config.json')
    self.__read_config()

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

def __init__(self):
    super(Thresholder, self).__init__()
    self._threshold_pre = {}
    self._threshold_post = {}
    self._default_threshold = 0.2
    self.load_state()

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

def __new__(cls):
    if cls._instance is None:
        cls._instance = super(ActionRemoteStorage, cls).__new__(cls)
        cls._instance.init()
    return cls._instance

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

def __new__(cls, sync=False, anonymizer: Anonymizer=Anonymizer()):
    if cls._instance is None:
        cls._instance = super(StatsTracker, cls).__new__(cls)
        cls._instance.init(sync, anonymizer)
    return cls._instance

