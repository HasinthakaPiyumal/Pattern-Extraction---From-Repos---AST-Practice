# Cluster 15

def split_file_commands(list_to_chunk: List, size_chunk: int):
    return [list_to_chunk[i:i + size_chunk] for i in range(0, len(list_to_chunk), size_chunk)]

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

def find_value(self, lines, message: State) -> Optional[int]:
    for i in reversed(range(len(lines))):
        if self.message_executed(lines[i], message):
            return i
    return None

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

def search(self, query, size=1):
    vector = self.transformer_func.transform([query])
    dist = cosine_similarity(self.vectors, vector).reshape(-1)
    return [(self.commands[i], dist[i]) for i in np.argsort(dist)[-size:]]

def identify_sections(sentences: list):
    sentences = [cleanup(sentence) for sentence in sentences]
    segments = []
    start_index = 0
    empty_sentence = 0
    for idx, sentence in enumerate(sentences):
        if not sentence:
            if empty_sentence >= 1:
                segments.append(sentences[start_index:idx])
                start_index = idx + 1
                empty_sentence = 0
            else:
                empty_sentence += 1
    sections = list()
    for segment in segments:
        sentences = list(filter(None, segment))
        if sentences:
            sections.append(' '.join([sentences for sentences in segment if sentences]))
    return sections

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

def ignore_skill_setup(skill_name):
    self.__add_to_action_order__(skill_name)
    profile = 'ignore-skill'
    kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'skill_idx': self._action_order[skill_name]}
    return (profile, kwargs)

def preferred_skill_orchestrator_setup(advantage_skill, disadvantage_skill):
    self.__add_to_action_order__(advantage_skill)
    self.__add_to_action_order__(disadvantage_skill)
    profile = 'preferred-skill'
    kwargs = {'n_points': 1000, 'context_size': self._n_actions, 'advantage_skillidx': self._action_order[advantage_skill], 'disadvantage_skillidx': self._action_order[disadvantage_skill]}
    return (profile, kwargs)

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

def get_noop_warmstart_data(n_points, context_size, noop_position):
    """ generates warm start data for noop behavior """
    confidence_vals = np.random.rand(n_points, context_size)
    data_tids = []
    data_contexts = []
    data_arm_rewards = []
    tid = 0
    for i in range(n_points):
        confs = confidence_vals[i]
        for arm in range(context_size):
            data_tids.append(f'warm-start-tid-{tid}')
            reward = 1.0 if arm == noop_position else -1.0
            data_contexts.append(confs)
            data_arm_rewards.append((arm, reward))
            tid += 1
    idxorder = np.random.permutation(n_points)
    data_tids = [data_tids[i] for i in idxorder]
    data_contexts = [data_contexts[i] for i in idxorder]
    data_arm_rewards = [data_arm_rewards[i] for i in idxorder]
    return (data_tids, np.array(data_contexts), data_arm_rewards)

def get_ignore_skill_warmstart_data(n_points, context_size, skill_idx):
    """ generates warm start data for always ignoring a skill behavior """
    confidence_vals = np.random.rand(n_points, context_size)
    data_tids = []
    data_contexts = []
    data_arm_rewards = []
    tid = 0
    for i in range(n_points):
        confs = confidence_vals[i]
        confs_sortidx = np.argsort(confs)
        max_confidx = confs_sortidx[-1]
        second_max_confidx = confs_sortidx[-2]
        reward = -1.0
        data_tids.append(f'warm-start-tid-{tid}')
        data_contexts.append(list(confs))
        data_arm_rewards.append((skill_idx, reward))
        tid += 1
        if max_confidx != skill_idx:
            reward = +1.0
            data_tids.append(f'warm-start-tid-{tid}')
            data_contexts.append(list(confs))
            data_arm_rewards.append((max_confidx, reward))
            tid += 1
        else:
            reward = +1.0
            data_tids.append(f'warm-start-tid-{tid}')
            data_contexts.append(list(confs))
            data_arm_rewards.append((second_max_confidx, reward))
            tid += 1
    idxorder = np.random.permutation(n_points)
    data_tids = [data_tids[i] for i in idxorder]
    data_contexts = [data_contexts[i] for i in idxorder]
    data_arm_rewards = [data_arm_rewards[i] for i in idxorder]
    return (data_tids, np.array(data_contexts), data_arm_rewards)

def get_max_skill_warmstart_data(n_points, context_size):
    """ generates warm start data for always ignoring a skill behavior """
    confidence_vals = np.random.rand(n_points, context_size)
    data_tids = []
    data_contexts = []
    data_arm_rewards = []
    tid = 0
    for i in range(n_points):
        confs = confidence_vals[i]
        maxidx = np.argmax(confs)
        for arm in range(context_size):
            data_tids.append(f'warm-start-tid-{tid}')
            reward = +1.0 if arm == maxidx else -1.0
            data_contexts.append(confs)
            data_arm_rewards.append((arm, reward))
            tid += 1
    idxorder = np.random.permutation(n_points)
    data_tids = [data_tids[i] for i in idxorder]
    data_contexts = [data_contexts[i] for i in idxorder]
    data_arm_rewards = [data_arm_rewards[i] for i in idxorder]
    return (data_tids, np.array(data_contexts), data_arm_rewards)

def get_preferred_skill_warmstart_data(n_points, context_size, advantage_skillidx, disadvantage_skillidx):
    """ generates warm start data to prefer one skill over another behavior """
    confidence_vals = np.random.rand(n_points, context_size)
    data_tids = []
    data_contexts = []
    data_arm_rewards = []
    tid = 0
    for i in range(n_points):
        confs = confidence_vals[i]
        confs_sorted_idx = np.argsort(confs)
        max_conf_idx = confs_sorted_idx[-1]
        second_max_conf_idx = confs_sorted_idx[-2]
        if max_conf_idx != disadvantage_skillidx and second_max_conf_idx != advantage_skillidx:
            reward = +1.0
            data_tids.append(f'warm-start-tid-{tid}')
            data_contexts.append(list(confs))
            data_arm_rewards.append((max_conf_idx, reward))
            tid += 1
        confs[disadvantage_skillidx], confs[max_conf_idx] = (confs[max_conf_idx], confs[disadvantage_skillidx])
        confs[advantage_skillidx], confs[second_max_conf_idx] = (confs[second_max_conf_idx], confs[advantage_skillidx])
        data_tids.append(f'warm-start-tid-{tid}')
        data_contexts.append(list(confs))
        data_arm_rewards.append((disadvantage_skillidx, -1.0))
        tid += 1
        data_tids.append(f'warm-start-tid-{tid}')
        data_contexts.append(list(confs))
        data_arm_rewards.append((advantage_skillidx, +1.0))
        tid += 1
    idxorder = np.random.permutation(n_points)
    data_tids = [data_tids[i] for i in idxorder]
    data_contexts = [data_contexts[i] for i in idxorder]
    data_arm_rewards = [data_arm_rewards[i] for i in idxorder]
    return (data_tids, np.array(data_contexts), data_arm_rewards)

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
def remove_emoji(description):
    if not description:
        return ''
    char_list = [description[j] for j in range(len(description)) if ord(description[j]) in range(65536)]
    description = ''
    for char in char_list:
        description = description + char
    return description

