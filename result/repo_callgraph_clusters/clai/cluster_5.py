# Cluster 5

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

def synthesize(self, text):
    """ Converts text to audio and saves to temp file """
    tts = gTTS(text, lang='en', lang_check=False)
    tts.save(self._tmp_filepath)

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

def __del__(self):
    self.save()

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

