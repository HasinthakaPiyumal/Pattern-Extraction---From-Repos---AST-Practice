# Cluster 10

def test_should_active_the_power_mode_when_use_the_command_clai_power(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), mock_agent)
    action = message_handler.process_message(clai_power_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.description == 'You have enabled the auto mode'
    assert action.origin_command == 'clai auto'
    assert action.execute
    assert message_handler.server_status_datasource.is_power()

def test_should_desactive_the_power_mode_when_use_the_command_clai_power_disable(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), mock_agent)
    message_handler.server_status_datasource.set_power(True)
    action = message_handler.process_message(clai_power_disabled_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.description == 'You have enable the manual mode'
    assert not message_handler.server_status_datasource.is_power()

def test_should_not_change_power_variable_when_active_power_mode_and_it_already_active(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), mock_agent)
    message_handler.server_status_datasource.set_power(True)
    action = message_handler.process_message(clai_power_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.description == 'You have the auto mode already enable, use clai manual to deactivate it'
    assert message_handler.server_status_datasource.is_power()

def test_should_not_change_power_variable_when_active_power_mode_and_it_already_disable(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), mock_agent)
    action = message_handler.process_message(clai_power_disabled_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.description == 'You have manual mode already enable, use clai auto to activate it'
    assert not message_handler.server_status_datasource.is_power()

def test_should_have_action_execute_true_when_power_mode_is_active(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), mock_agent)
    message_handler.process_message(clai_power_state())
    action = message_handler.process_message(ANY_COMMAND_MESSAGE)
    assert action.origin_command == ANY_COMMAND_MESSAGE.command
    assert action.execute

def test_should_return_a_valid_action_when_socket_crash(mocker):
    mocker.patch.object(SocketClientConnector, 'send', side_effect=socket.error(), autospec=True)
    action = send_command(ANY_ID, ANY_USER, ANY_NO_ACTION.origin_command)
    assert action == ANY_NO_ACTION

def test_should_return_the_original_command_when_read_throw_exception(mocker):
    mocker.patch.object(ClientConnector, 'send', side_effect=socket.error(), autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, ANY_INPUT_COMMAND)
    assert command_to_execute == ANY_INPUT_COMMAND

def test_should_not_print_the_suggested_dialog_when_suggested_is_the_same(mocker):
    spy_print(mocker)
    mocker.patch.object(ClaiClient, 'send', return_value=ANY_NO_ACTION, autospec=True)
    process_command_from_user(ANY_ID, ANY_USER, ANY_NO_ACTION.origin_command)
    assert print.call_count == 0

def test_should_print_the_suggested_dialog_when_suggested_is_different(mocker):
    spy_print(mocker)
    mock_input_console(mocker, 'n')
    mocker.patch.object(ClaiClient, 'send', return_value=SUGGESTED_ACTION, autospec=True)
    process_command_from_user(ANY_ID, ANY_USER, ANY_INPUT_COMMAND)
    assert print.call_count == 1

def test_should_not_print_the_suggested_dialog_when_suggested_is_different_and_execute_is_enable(mocker):
    spy_print(mocker)
    mocker.patch.object(ClaiClient, 'send', return_value=EXECUTABLE_ACTION, autospec=True)
    process_command_from_user(ANY_ID, ANY_USER, ANY_NO_ACTION.origin_command)
    assert print.call_count == 0

def test_should_not_print_the_suggested_dialog_when_the_action_only_contains_original_command(mocker):
    spy_print(mocker)
    mocker.patch.object(ClaiClient, 'send', return_value=BASIC_ACTION, autospec=True)
    process_command_from_user(ANY_ID, ANY_USER, ANY_INPUT_COMMAND)
    assert print.call_count == 0

def test_should_not_print_the_suggested_dialog_when_suggested_command_is_empty(mocker):
    spy_print(mocker)
    empty_suggested_command = Action(origin_command=ANY_INPUT_COMMAND, suggested_command='')
    mocker.patch.object(ClaiClient, 'send', return_value=empty_suggested_command, autospec=True)
    process_command_from_user(ANY_ID, ANY_USER, ANY_INPUT_COMMAND)
    assert print.call_count == 0

def test_should_return_the_original_command_when_the_command_is_the_same(mocker):
    mocker.patch.object(ClaiClient, 'send', return_value=ANY_NO_ACTION, autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, ANY_NO_ACTION.origin_command)
    assert command_to_execute == ANY_NO_ACTION.origin_command

def test_should_return_the_suggested_command_when_the_user_press_yes(mocker):
    mock_input_console(mocker, 'y')
    mocker.patch.object(ClaiClient, 'send', return_value=SUGGESTED_ACTION, autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, SUGGESTED_ACTION.origin_command)
    assert command_to_execute == SUGGESTED_ACTION.suggested_command

def test_should_return_the_original_command_when_the_user_press_no(mocker):
    mock_input_console(mocker, 'n')
    mocker.patch.object(ClaiClient, 'send', return_value=SUGGESTED_ACTION, autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, SUGGESTED_ACTION.origin_command)
    assert command_to_execute == SUGGESTED_ACTION.origin_command

def test_should_return_the_suggested_command_when_the_action_execute_true(mocker):
    mocker.patch.object(ClaiClient, 'send', return_value=EXECUTABLE_ACTION, autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, EXECUTABLE_ACTION.origin_command)
    assert command_to_execute == EXECUTABLE_ACTION.suggested_command

def test_should_return_the_original_command_when_the_action_not_contains_suggestion(mocker):
    mocker.patch.object(ClaiClient, 'send', return_value=BASIC_ACTION, autospec=True)
    command_to_execute, _ = process_command_from_user(ANY_ID, ANY_USER, BASIC_ACTION.origin_command)
    assert command_to_execute == BASIC_ACTION.origin_command

def test_should_return_the_list_of_plugins_with_default_selected_when_the_server_received_plugins_no_selected(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=NO_SELECTED, autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(clai_plugins_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == 'clai skills'
    assert action.execute
    assert action.description == expected_description(ALL_PLUGINS, NO_SELECTED.default)

def test_should_return_the_list_of_plugins_with_selected_when_the_server_received_plugins(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    agent_selected = 'nlc2cmd'
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    mocker.patch.object(ConfigStorage, 'read_all_user_config', return_value=None, autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=[agent_selected], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(clai_plugins_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == 'clai skills'
    assert action.execute
    assert action.description == expected_description(ALL_PLUGINS, agent_selected)

def test_should_return_the_list_without_any_selected_plugin_when_default_doesnt_exist(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(default='', default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(clai_plugins_state())
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == 'clai skills'
    assert action.execute
    assert action.description == expected_description(ALL_PLUGINS, '')

def test_should_return_the_install_command_when_the_new_plugin_is_not_installed_yet(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['nlc2cmd'], default_orchestrator='max_orchestrator'), autospec=True)
    mocker.patch.object(ConfigStorage, 'store_config', return_value=None, autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    select_agent = clai_select_state('nlc2cmd')
    action = message_handler.process_message(select_agent)
    assert action.suggested_command == '$CLAI_PATH/fileExist.sh nlc2cmd $CLAI_PATH'
    assert action.origin_command == select_agent.command
    assert message_handler.agent_datasource.get_current_plugin_name(select_agent.user_name) == ['nlc2cmd']

def test_should_return_the_list_with_the_new_selected_values_if_exists_and_is_installed(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    mocker.patch.object(ConfigStorage, 'store_config', return_value=None, autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS_WITH_TAR_INSTALLED, autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    select_agent = clai_select_state('nlc2cmd')
    action = message_handler.process_message(select_agent)
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == select_agent.command
    assert action.execute
    assert message_handler.agent_datasource.get_current_plugin_name(select_agent.user_name) == ['nlc2cmd']

def test_should_return_an_error_when_agent_doesnt_exist(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['nlc2cmd'], default_orchestrator='max_orchestrator'), autospec=True)
    mocker.patch.object(ConfigStorage, 'store_config', return_value=None, autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    select_agent = clai_select_state('wrong_agent')
    action = message_handler.process_message(select_agent)
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == select_agent.command
    assert action.execute
    assert action.description == create_error_select('wrong_agent').description
    assert message_handler.agent_datasource.get_current_plugin_name(select_agent.user_name) == ['nlc2cmd']

def test_should_return_an_error_when_selected_is_empty(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mocker.patch.object(AgentDatasource, 'all_plugins', return_value=ALL_PLUGINS, autospec=True)
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['nlc2cmd'], default_orchestrator='max_orchestrator'), autospec=True)
    mocker.patch.object(ConfigStorage, 'store_config', return_value=None, autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    select_agent = clai_select_state('')
    action = message_handler.process_message(select_agent)
    assert action.suggested_command == NOOP_COMMAND
    assert action.origin_command == select_agent.command
    assert action.execute
    assert action.description == create_error_select('').description
    assert message_handler.agent_datasource.get_current_plugin_name(select_agent.user_name) == ['nlc2cmd']

def test_should_return_the_action_from_selected_agent_when_the_command_goes_to_the_agent_and_threshold_is_ok(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    action_to_execute = Action(suggested_command='command', confidence=1.0)
    mock_agent.execute.return_value = action_to_execute
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(command_state())
    assert action.suggested_command == action_to_execute.suggested_command
    assert action.origin_command == command_state().command
    assert not action.execute
    assert not action.description

def test_should_return_empty_action_from_selected_agent_when_the_command_goes_to_the_agent_and_not_confidence(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    action_to_execute = Action(suggested_command='command', confidence=0.1)
    mock_agent.execute.return_value = action_to_execute
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(command_state())
    assert action.suggested_command is action.origin_command
    assert action.origin_command == command_state().command
    assert not action.execute
    assert not action.description

def test_should_return_the_suggestion_from_agent_ignoring_confidence_if_is_clai_command(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    action_to_execute = Action(suggested_command='command', confidence=0.0)
    mock_agent.execute.return_value = action_to_execute
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(COMMAND_AGENT_STATE)
    assert action.suggested_command == action_to_execute.suggested_command
    assert action.origin_command == command_state().command
    assert not action.execute
    assert not action.description

def test_should_return_the_suggestion_from_agent_ignoring_confidence_if_is_name_agent_command(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    action_to_execute = Action(suggested_command='command', confidence=0.0)
    mock_agent.execute.return_value = action_to_execute
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(COMMAND_NAME_AGENT_STATE)
    assert action.suggested_command == action_to_execute.suggested_command
    assert action.origin_command == command_state().command
    assert not action.execute
    assert not action.description

def test_should_return_valid_action_if_the_select_agent_return_none(mocker):
    mock_agent = create_mock_agent()
    mocker.patch.object(AgentDatasource, 'get_instances', return_value=[mock_agent], autospec=True)
    mock_agent.execute.return_value = None
    mocker.patch.object(ConfigStorage, 'read_config', return_value=PluginConfig(selected=['demo_agent'], default_orchestrator='max_orchestrator'), autospec=True)
    message_handler = MessageHandler(ServerStatusDatasource(), AgentDatasource())
    action = message_handler.process_message(command_state())
    assert action.suggested_command is action.origin_command
    assert action.origin_command == command_state().command
    assert not action.execute
    assert not action.description

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

def __init__(self, agent_datasource: AgentDatasource, orchestrator_provider: OrchestratorProvider):
    self.agent_datasource = agent_datasource
    self.orchestrator_provider = orchestrator_provider
    self.remote_storage = ActionRemoteStorage()
    self.orchestrator_storage = OrchestratorStorage(orchestrator_provider, self.remote_storage)
    self._pre_exec_id = 'pre'
    self._post_exec_id = 'post'

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

def __init__(self, server_status_datasource: ServerStatusDatasource=current_status_datasource, connector: ServerConnector=SocketServerConnector(current_status_datasource), agent_datasource=AgentDatasource()):
    self.connector = connector
    self.agent_datasource = agent_datasource
    self.server_status_datasource = server_status_datasource
    self.remote_storage = ActionRemoteStorage()
    self.message_handler = MessageHandler(server_status_datasource, agent_datasource=agent_datasource)
    self.stats_tracker = StatsTracker()

def process_message(self, received_data: bytes) -> Action:
    message = self.serialize_message(received_data)
    return self.message_handler.process_message(message)

class ClaiPowerCommandRunner(CommandRunner):

    def __init__(self, server_status_datasource: ServerStatusDatasource):
        self.server_status_datasource = server_status_datasource

    def execute(self, state: State) -> Action:
        if self.server_status_datasource.is_power():
            text = 'You have the auto mode already enable, use clai manual to deactivate it'
        else:
            self.server_status_datasource.set_power(True)
            text = 'You have enabled the auto mode'
        return Action(origin_command=state.command, suggested_command=NOOP_COMMAND, description=text, execute=True)

def execute(self, state: State) -> Action:
    if self.server_status_datasource.is_power():
        text = 'You have the auto mode already enable, use clai manual to deactivate it'
    else:
        self.server_status_datasource.set_power(True)
        text = 'You have enabled the auto mode'
    return Action(origin_command=state.command, suggested_command=NOOP_COMMAND, description=text, execute=True)

class ClaiPowerDisableCommandRunner(CommandRunner):

    def __init__(self, server_status_datasource: ServerStatusDatasource):
        self.server_status_datasource = server_status_datasource

    def execute(self, state: State) -> Action:
        if not self.server_status_datasource.is_power():
            text = 'You have manual mode already enable, use clai auto to activate it'
        else:
            self.server_status_datasource.set_power(False)
            text = 'You have enable the manual mode'
        return Action(suggested_command=NOOP_COMMAND, origin_command=state.command, description=text, execute=True)

def execute(self, state: State) -> Action:
    if not self.server_status_datasource.is_power():
        text = 'You have manual mode already enable, use clai auto to activate it'
    else:
        self.server_status_datasource.set_power(False)
        text = 'You have enable the manual mode'
    return Action(suggested_command=NOOP_COMMAND, origin_command=state.command, description=text, execute=True)

