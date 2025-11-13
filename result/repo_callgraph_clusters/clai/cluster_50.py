# Cluster 50

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

def select_best_candidate(self, command: State, agent_list: List[Agent], candidate_actions: Optional[List[Union[Action, List[Action]]]], force_response: bool, pre_post_state: str) -> Optional[Union[Action, List[Action]]]:
    agent_names = [agent.agent_name for agent in agent_list]
    orchestrator = self.orchestrator_provider.get_current_orchestrator()
    suggested_command = orchestrator.choose_action(command=command, agent_names=agent_names, candidate_actions=candidate_actions, force_response=force_response, pre_post_state=pre_post_state)
    if not suggested_command:
        suggested_command = Action()
    return suggested_command

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

def __notify_orchestrator(self, current_pre: TerminalReplayMemory):
    if len(self._memory) > 1:
        previous_replay = self._memory.pop(0)
        orchestrator = self.orchestrator_provider.get_current_orchestrator()
        orchestrator.record_transition(previous_replay, current_pre)
        self.remote_storage.store(previous_replay.post_replay)

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

