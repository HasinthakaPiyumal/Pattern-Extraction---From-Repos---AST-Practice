# Cluster 11

def mpe_make_env(scenario_name):
    import mpe.multiagent.scenarios as scenarios
    from mpe.multiagent.environment import MultiAgentEnv
    scenario = scenarios.load(scenario_name + '.py').Scenario()
    world = scenario.make_world()
    env = MultiAgentEnv(world, scenario.reset_world, scenario.reward, scenario.observation)
    return env

def store_pickled_evaluation(name: str, evaluation: list):
    save_folder = f'{os.path.dirname(os.path.realpath(__file__))}/vmas_vs_mpe_graphs/pickled'
    file = f'{save_folder}/{name}.pkl'
    pickle.dump(evaluation, open(file, 'wb'))

def load_pickled_evaluation(name: str):
    save_folder = f'{os.path.dirname(os.path.realpath(__file__))}/vmas_vs_mpe_graphs/pickled'
    file = Path(f'{save_folder}/{name}.pkl')
    if file.is_file():
        return pickle.load(open(file, 'rb'))
    return None

def run_comparison(vmas_device: str, n_steps: int=100):
    device_name = get_device_name(vmas_device)
    mpe_times = []
    vmas_times = []
    low = 1
    high = 30000
    num = 100
    list_n_envs = np.linspace(low, high, num)
    figure_name = f'VMAS_vs_MPE_{n_steps}_steps_{device_name.lower().replace(' ', '_')}'
    figure_name_pkl = figure_name + f'_range_{low}_{high}_num_{num}'
    evaluation = load_pickled_evaluation(figure_name_pkl)
    if evaluation is None:
        for n_envs in list_n_envs:
            mpe_times.append(run_mpe_simple_spread(n_envs=n_envs, n_steps=n_steps))
            vmas_times.append(run_vmas_simple_spread(n_envs=n_envs, n_steps=n_steps, device=vmas_device))
        store_pickled_evaluation(name=figure_name_pkl, evaluation=[mpe_times, vmas_times])
    else:
        mpe_times = evaluation[0]
        vmas_times = evaluation[1]
    fig, ax = plt.subplots()
    ax.plot(list_n_envs, mpe_times, label='MPE')
    ax.plot(list_n_envs, vmas_times, label='VMAS')
    plt.xlabel('Number of parallel environments', fontsize=14)
    plt.ylabel('Seconds', fontsize=14)
    ax.legend(loc='upper left')
    fig.suptitle('VMAS vs MPE', fontsize=16)
    ax.set_title(f"Execution time of 'simple_spread' for {n_steps} steps on {device_name}", fontsize=8)
    save_folder = os.path.dirname(os.path.realpath(__file__))
    tikzplotlib.clean_figure()
    tikzplotlib.save(f'{save_folder}/vmas_vs_mpe_graphs/{figure_name}.tex')
    plt.savefig(f'{save_folder}/vmas_vs_mpe_graphs/{figure_name}.pdf')

def make_env(scenario: Union[str, BaseScenario], num_envs: int, device: DEVICE_TYPING='cpu', continuous_actions: bool=True, wrapper: Optional[Union[Wrapper, str]]=None, max_steps: Optional[int]=None, seed: Optional[int]=None, dict_spaces: bool=False, multidiscrete_actions: bool=False, clamp_actions: bool=False, grad_enabled: bool=False, terminated_truncated: bool=False, wrapper_kwargs: Optional[dict]=None, **kwargs):
    """Create a vmas environment.

    Args:
        scenario (Union[str, BaseScenario]): Scenario to load.
            Can be the name of a file in `vmas.scenarios` folder or a :class:`~vmas.simulator.scenario.BaseScenario` class,
        num_envs (int): Number of vectorized simulation environments. VMAS performs vectorized simulations using PyTorch.
            This argument indicates the number of vectorized environments that should be simulated in a batch. It will also
            determine the batch size of the environment.
        device (Union[str, int, torch.device], optional): Device for simulation. All the tensors created by VMAS
            will be placed on this device. Default is ``"cpu"``,
        continuous_actions (bool, optional): Whether to use continuous actions. If ``False``, actions
            will be discrete. The number of actions and their size will depend on the chosen scenario. Default is ``True``,
        wrapper (Union[Wrapper, str], optional): Wrapper class to use. For example, it can be
            ``"rllib"``, ``"gym"``, ``"gymnasium"``, ``"gymnasium_vec"``. Default is ``None``.
        max_steps (int, optional): Horizon of the task. Defaults to ``None`` (infinite horizon). Each VMAS scenario can
            be terminating or not. If ``max_steps`` is specified,
            the scenario is also terminated whenever this horizon is reached,
        seed (int, optional): Seed for the environment. Defaults to ``None``,
        dict_spaces (bool, optional):  Weather to use dictionaries spaces with format ``{"agent_name": tensor, ...}``
            for obs, rewards, and info instead of tuples. Defaults to ``False``: obs, rewards, info are tuples with length number of agents,
        multidiscrete_actions (bool, optional): Whether to use multidiscrete action spaces when ``continuous_actions=False``.
            Default is ``False``: the action space will be ``Discrete``, and it will be the cartesian product of the
            discrete action spaces available to an agent,
        clamp_actions (bool, optional): Weather to clamp input actions to their range instead of throwing
            an error when ``continuous_actions==True`` and actions are out of bounds,
        grad_enabled (bool, optional): If ``True`` the simulator will not call ``detach()`` on input actions and gradients can
            be taken from the simulator output. Default is ``False``.
        terminated_truncated (bool, optional): Weather to use terminated and truncated flags in the output of the step method (or single done).
            Default is ``False``.
        wrapper_kwargs (dict, optional): Keyword arguments to pass to the wrapper class. Default is ``{}``.
        **kwargs (dict, optional): Keyword arguments to pass to the :class:`~vmas.simulator.scenario.BaseScenario` class.

    Examples:
        >>> from vmas import make_env
        >>> env = make_env(
        ...     "waterfall",
        ...     num_envs=3,
        ...     num_agents=2,
        ... )
        >>> print(env.reset())


    """
    if isinstance(scenario, str):
        if not scenario.endswith('.py'):
            scenario += '.py'
        scenario = scenarios.load(scenario).Scenario()
    env = Environment(scenario, num_envs=num_envs, device=device, continuous_actions=continuous_actions, max_steps=max_steps, seed=seed, dict_spaces=dict_spaces, multidiscrete_actions=multidiscrete_actions, clamp_actions=clamp_actions, grad_enabled=grad_enabled, terminated_truncated=terminated_truncated, **kwargs)
    if wrapper is not None and isinstance(wrapper, str):
        wrapper = Wrapper[wrapper.upper()]
    if wrapper_kwargs is None:
        wrapper_kwargs = {}
    return wrapper.get_env(env, **wrapper_kwargs) if wrapper is not None else env

class InteractiveEnv:
    """
    Use this script to interactively play with scenarios

    You can change agent by pressing TAB
    You can reset the environment by pressing R
    You can control agent actions with the arrow keys and M/N (left/right control the first action, up/down control the second, M/N controls the third)
    If you have more than 1 agent, you can control another one with W,A,S,D and Q,E in the same way.
    and switch the agent with these controls using LSHIFT
    """

    def __init__(self, env: GymWrapper, control_two_agents: bool=False, display_info: bool=True, save_render: bool=False, render_name: str='interactive'):
        self.env = env
        self.control_two_agents = control_two_agents
        self.current_agent_index = 0
        self.current_agent_index2 = 1
        self.n_agents = self.env.unwrapped.n_agents
        self.agents = self.env.unwrapped.agents
        self.continuous = self.env.unwrapped.continuous_actions
        self.reset = False
        self.keys = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.keys2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.u = [0] * (3 if self.continuous else 2)
        self.u2 = [0] * (3 if self.continuous else 2)
        self.frame_list = []
        self.display_info = display_info
        self.save_render = save_render
        self.render_name = render_name
        if self.control_two_agents:
            assert self.n_agents >= 2, 'Control_two_agents is true but not enough agents in scenario'
        self.text_lines = []
        self.font_size = 15
        self.env.render()
        self.text_idx = len(self.env.unwrapped.text_lines)
        self._init_text()
        self.env.unwrapped.viewer.window.on_key_press = self._key_press
        self.env.unwrapped.viewer.window.on_key_release = self._key_release
        self._cycle()

    def _increment_selected_agent_index(self, index: int):
        index += 1
        if index == self.n_agents:
            index = 0
        return index

    def _cycle(self):
        total_rew = [0] * self.n_agents
        while True:
            if self.reset:
                if self.save_render:
                    save_video(self.render_name, self.frame_list, fps=1 / self.env.unwrapped.world.dt)
                self.env.reset()
                self.reset = False
                total_rew = [0] * self.n_agents
            if self.n_agents > 0:
                action_list = [[0.0] * agent.action_size for agent in self.agents]
                action_list[self.current_agent_index][:self.agents[self.current_agent_index].dynamics.needed_action_size] = self.u[:self.agents[self.current_agent_index].dynamics.needed_action_size]
            else:
                action_list = []
            if self.n_agents > 1 and self.control_two_agents:
                action_list[self.current_agent_index2][:self.agents[self.current_agent_index2].dynamics.needed_action_size] = self.u2[:self.agents[self.current_agent_index2].dynamics.needed_action_size]
            obs, rew, done, info = self.env.step(action_list)
            if self.display_info and self.n_agents > 0:
                obs_str = str(InteractiveEnv.format_obs(obs[self.current_agent_index]))
                message = f'\t\t{obs_str[len(obs_str) // 2:]}'
                self._write_values(0, message)
                message = f'Obs: {obs_str[:len(obs_str) // 2]}'
                self._write_values(1, message)
                message = f'Rew: {round(rew[self.current_agent_index], 3)}'
                self._write_values(2, message)
                total_rew = list(map(add, total_rew, rew))
                message = f'Total rew: {round(total_rew[self.current_agent_index], 3)}'
                self._write_values(3, message)
                message = f'Done: {done}'
                self._write_values(4, message)
                message = f'Selected: {self.env.unwrapped.agents[self.current_agent_index].name}'
                self._write_values(5, message)
            frame = self.env.render(mode='rgb_array' if self.save_render else 'human', visualize_when_rgb=True)
            if self.save_render:
                self.frame_list.append(frame)
            if done:
                self.reset = True

    def _init_text(self):
        from vmas.simulator import rendering
        for i in range(N_TEXT_LINES_INTERACTIVE):
            text_line = rendering.TextLine(y=(self.text_idx + i) * 40, font_size=self.font_size)
            self.env.unwrapped.viewer.add_geom(text_line)
            self.text_lines.append(text_line)

    def _write_values(self, index: int, message: str):
        self.text_lines[index].set_text(message)

    def _key_press(self, k, mod):
        from pyglet.window import key
        agent_range = self.agents[self.current_agent_index].action.u_range_tensor
        try:
            if k == key.LEFT:
                self.keys[0] = agent_range[0]
            elif k == key.RIGHT:
                self.keys[1] = agent_range[0]
            elif k == key.DOWN:
                self.keys[2] = agent_range[1]
            elif k == key.UP:
                self.keys[3] = agent_range[1]
            elif k == key.M:
                self.keys[4] = agent_range[2]
            elif k == key.N:
                self.keys[5] = agent_range[2]
            elif k == key.TAB:
                self.current_agent_index = self._increment_selected_agent_index(self.current_agent_index)
                if self.control_two_agents:
                    while self.current_agent_index == self.current_agent_index2:
                        self.current_agent_index = self._increment_selected_agent_index(self.current_agent_index)
            if self.control_two_agents:
                agent2_range = self.agents[self.current_agent_index2].action.u_range_tensor
                if k == key.A:
                    self.keys2[0] = agent2_range[0]
                elif k == key.D:
                    self.keys2[1] = agent2_range[0]
                elif k == key.S:
                    self.keys2[2] = agent2_range[1]
                elif k == key.W:
                    self.keys2[3] = agent2_range[1]
                elif k == key.E:
                    self.keys2[4] = agent2_range[2]
                elif k == key.Q:
                    self.keys2[5] = agent2_range[2]
                elif k == key.LSHIFT:
                    self.current_agent_index2 = self._increment_selected_agent_index(self.current_agent_index2)
                    while self.current_agent_index == self.current_agent_index2:
                        self.current_agent_index2 = self._increment_selected_agent_index(self.current_agent_index2)
        except IndexError:
            print('Action not available')
        if k == key.R:
            self.reset = True
        self.set_u()

    def _key_release(self, k, mod):
        from pyglet.window import key
        if k == key.LEFT:
            self.keys[0] = 0
        elif k == key.RIGHT:
            self.keys[1] = 0
        elif k == key.DOWN:
            self.keys[2] = 0
        elif k == key.UP:
            self.keys[3] = 0
        elif k == key.M:
            self.keys[4] = 0
        elif k == key.N:
            self.keys[5] = 0
        if self.control_two_agents:
            if k == key.A:
                self.keys2[0] = 0
            elif k == key.D:
                self.keys2[1] = 0
            elif k == key.S:
                self.keys2[2] = 0
            elif k == key.W:
                self.keys2[3] = 0
            elif k == key.E:
                self.keys2[4] = 0
            elif k == key.Q:
                self.keys2[5] = 0
        self.set_u()

    def set_u(self):
        if self.continuous:
            self.u = [self.keys[1] - self.keys[0], self.keys[3] - self.keys[2], self.keys[4] - self.keys[5]]
            self.u2 = [self.keys2[1] - self.keys2[0], self.keys2[3] - self.keys2[2], self.keys2[4] - self.keys2[5]]
        else:
            if np.sum(self.keys[:4]) >= 1:
                self.u[0] = np.argmax(self.keys[:4]) + 1
            else:
                self.u[0] = 0
            if np.sum(self.keys[4:]) >= 1:
                self.u[1] = np.argmax(self.keys[4:]) + 1
            else:
                self.u[1] = 0
            if np.sum(self.keys2[:4]) >= 1:
                self.u2[0] = np.argmax(self.keys2[:4]) + 1
            else:
                self.u2[0] = 0
            if np.sum(self.keys2[4:]) >= 1:
                self.u2[1] = np.argmax(self.keys2[4:]) + 1
            else:
                self.u2[1] = 0

    @staticmethod
    def format_obs(obs):
        if isinstance(obs, (Tensor, np.ndarray)):
            return list(np.around(obs.tolist(), decimals=2))
        elif isinstance(obs, Dict):
            return {key: InteractiveEnv.format_obs(value) for key, value in obs.items()}
        else:
            raise NotImplementedError(f'Invalid type of observation {obs}')

def _init_text(self):
    from vmas.simulator import rendering
    for i in range(N_TEXT_LINES_INTERACTIVE):
        text_line = rendering.TextLine(y=(self.text_idx + i) * 40, font_size=self.font_size)
        self.env.unwrapped.viewer.add_geom(text_line)
        self.text_lines.append(text_line)

def _write_values(self, index: int, message: str):
    self.text_lines[index].set_text(message)

def set_u(self):
    if self.continuous:
        self.u = [self.keys[1] - self.keys[0], self.keys[3] - self.keys[2], self.keys[4] - self.keys[5]]
        self.u2 = [self.keys2[1] - self.keys2[0], self.keys2[3] - self.keys2[2], self.keys2[4] - self.keys2[5]]
    else:
        if np.sum(self.keys[:4]) >= 1:
            self.u[0] = np.argmax(self.keys[:4]) + 1
        else:
            self.u[0] = 0
        if np.sum(self.keys[4:]) >= 1:
            self.u[1] = np.argmax(self.keys[4:]) + 1
        else:
            self.u[1] = 0
        if np.sum(self.keys2[:4]) >= 1:
            self.u2[0] = np.argmax(self.keys2[:4]) + 1
        else:
            self.u2[0] = 0
        if np.sum(self.keys2[4:]) >= 1:
            self.u2[1] = np.argmax(self.keys2[4:]) + 1
        else:
            self.u2[1] = 0

def load(name: str):
    pathname = None
    for dirpath, _, filenames in os.walk(osp.dirname(__file__)):
        if pathname is None:
            for filename in filenames:
                if name == filename or Path(name) == Path(dirpath) / Path(filename):
                    pathname = os.path.join(dirpath, filename)
                    break
    assert pathname is not None, f'{name} scenario not found.'
    spec = importlib.util.spec_from_file_location('', pathname)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Scenario(BaseScenario):
    """
    This scenario originally comes from the paper "Xu et al. - 2024 - A Sample Efficient and Generalizable Multi-Agent Reinforcement Learning Framework
    for Motion Planning" (https://arxiv.org/abs/2408.07644, see also its GitHub repo https://github.com/bassamlab/SigmaRL),
    which aims to design an MARL framework with efficient observation design to enable fast training and to empower agents the ability to generalize
    to unseen scenarios.

    Six observation design strategies are proposed in the paper. They correspond to six parameters in this file, and their default
    values are True. Setting them to False will impair the observation efficiency in the evaluation conducted in the paper.
        - is_ego_view: Whether to use ego view (otherwise bird view)
        - is_apply_mask: Whether to mask distant agents
        - is_observe_distance_to_agents: Whether to observe the distance to other agents
        - is_observe_distance_to_boundaries: Whether to observe the distance to labelet boundaries (otherwise the points on lanelet boundaries)
        - is_observe_distance_to_center_line: Whether to observe the distance to reference path (otherwise None)
        - is_observe_vertices: Whether to observe the vertices of other agents (otherwise center points)

    In addition, there are some commonly used parameters you may want to adjust to suit your case:
        - n_agents: Number of agents
        - dt: Sample time in seconds
        - map_type: One of {'1', '2', '3'}:
                         1: the entire map will be used
                         2: the entire map will be used ; besides, challenging initial state buffer will be recorded and used when resetting the envs (inspired
                         by Kaufmann et al. - Nature 2023 - Champion-level drone racing using deep reinforcement learning)
                         3: a specific part of the map (intersection, merge-in, or merge-out) will be used for each env when making or resetting it. You can control the probability of using each of them by the parameter `scenario_probabilities`. It is an array with three values. The first value corresponds to the probability of using intersection. The second and the third values correspond to merge-in and merge-out, respectively. If you only want to use one specific part of the map for all parallel envs, you can set the other two values to zero. For example, if you want to train a RL policy only for intersection, they can set `scenario_probabilities` to [1.0, 0.0, 0.0].
        - is_partial_observation: Whether to enable partial observation (to model partially observable MDP)
        - n_nearing_agents_observed: Number of nearing agents to be observed (consider limited sensor range)

        is_testing_mode: Testing mode is designed to test the learned policy.
                         In non-testing mode, once a collision occurs, all agents will be reset with random initial states.
                         To ensure these initial states are feasible, the initial positions are conservatively large (1.2*diagonalLengthOfAgent).
                         This ensures agents are initially safe and avoids putting agents in an immediate dangerous situation at the beginning of a new scenario.
                         During testing, only colliding agents will be reset, without changing the states of other agents, who are possibly interacting with other agents.
                         This may allow for more effective testing.

    For other parameters, see the class Parameter defined in this file.
    """

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.init_params(batch_dim, device, **kwargs)
        self.visualize_semidims = False
        world = self.init_world(batch_dim, device)
        self.init_agents(world)
        return world

    def init_params(self, batch_dim, device, **kwargs):
        self.world_x_dim = kwargs.pop('world_x_dim', 4.5)
        self.world_y_dim = kwargs.pop('world_y_dim', 4.0)
        self.agent_width = kwargs.pop('agent_width', 0.08)
        self.agent_length = kwargs.pop('agent_length', 0.16)
        self.l_f = kwargs.pop('l_f', self.agent_length / 2)
        self.l_r = kwargs.pop('l_r', self.agent_length - self.l_f)
        lane_width = kwargs.pop('lane_width', 0.15)
        r_p_normalizer = 100
        reward_progress = kwargs.pop('reward_progress', 10) / r_p_normalizer
        reward_vel = kwargs.pop('reward_vel', 5) / r_p_normalizer
        reward_reach_goal = kwargs.pop('reward_reach_goal', 0) / r_p_normalizer
        threshold_deviate_from_ref_path = kwargs.pop('threshold_deviate_from_ref_path', (lane_width - self.agent_width) / 2)
        threshold_reach_goal = kwargs.pop('threshold_reach_goal', self.agent_width / 2)
        threshold_change_steering = kwargs.pop('threshold_change_steering', 10)
        threshold_near_boundary_high = kwargs.pop('threshold_near_boundary_high', (lane_width - self.agent_width) / 2 * 0.9)
        threshold_near_boundary_low = kwargs.pop('threshold_near_boundary_low', 0)
        threshold_near_other_agents_c2c_high = kwargs.pop('threshold_near_other_agents_c2c_high', self.agent_length + self.agent_width)
        threshold_near_other_agents_c2c_low = kwargs.pop('threshold_near_other_agents_c2c_low', (self.agent_length + self.agent_width) / 2)
        threshold_no_reward_if_too_close_to_boundaries = kwargs.pop('threshold_no_reward_if_too_close_to_boundaries', self.agent_width / 10)
        threshold_no_reward_if_too_close_to_other_agents = kwargs.pop('threshold_no_reward_if_too_close_to_other_agents', self.agent_width / 6)
        self.resolution_factor = kwargs.pop('resolution_factor', 200)
        sample_interval_ref_path = kwargs.pop('sample_interval_ref_path', 2)
        max_ref_path_points = kwargs.pop('max_ref_path_points', 200)
        noise_level = kwargs.pop('noise_level', 0.2 * self.agent_width)
        n_stored_steps = kwargs.pop('n_stored_steps', 5)
        n_observed_steps = kwargs.pop('n_observed_steps', 1)
        self.render_origin = kwargs.pop('render_origin', [self.world_x_dim / 2, self.world_y_dim / 2])
        self.viewer_size = kwargs.pop('viewer_size', (int(self.world_x_dim * self.resolution_factor), int(self.world_y_dim * self.resolution_factor)))
        self.max_steering_angle = kwargs.pop('max_steering_angle', torch.deg2rad(torch.tensor(35, device=device, dtype=torch.float32)))
        self.max_speed = kwargs.pop('max_speed', 1.0)
        self.viewer_zoom = kwargs.pop('viewer_zoom', 1.44)
        parameters = Parameters(n_agents=kwargs.pop('n_agents', 20), is_partial_observation=kwargs.pop('is_partial_observation', True), is_testing_mode=kwargs.pop('is_testing_mode', False), is_visualize_short_term_path=kwargs.pop('is_visualize_short_term_path', True), map_type=kwargs.pop('map_type', '1'), n_nearing_agents_observed=kwargs.pop('n_nearing_agents_observed', 2), is_real_time_rendering=kwargs.pop('is_real_time_rendering', False), n_points_short_term=kwargs.pop('n_points_short_term', 3), dt=kwargs.pop('dt', 0.05), is_ego_view=kwargs.pop('is_ego_view', True), is_apply_mask=kwargs.pop('is_apply_mask', True), is_observe_vertices=kwargs.pop('is_observe_vertices', True), is_observe_distance_to_agents=kwargs.pop('is_observe_distance_to_agents', True), is_observe_distance_to_boundaries=kwargs.pop('is_observe_distance_to_boundaries', True), is_observe_distance_to_center_line=kwargs.pop('is_observe_distance_to_center_line', True), scenario_probabilities=kwargs.pop('scenario_probabilities', [1.0, 0.0, 0.0]), is_add_noise=kwargs.pop('is_add_noise', True), is_observe_ref_path_other_agents=kwargs.pop('is_observe_ref_path_other_agents', False), is_visualize_extra_info=kwargs.pop('is_visualize_extra_info', False), render_title=kwargs.pop('render_title', 'Multi-Agent Reinforcement Learning for Road Traffic (CPM Lab Scenario)'), n_steps_stored=kwargs.pop('n_steps_stored', 10), n_steps_before_recording=kwargs.pop('n_steps_before_recording', 10), n_points_nearing_boundary=kwargs.pop('n_points_nearing_boundary', 5))
        self.parameters = kwargs.pop('parameters', parameters)
        if self.parameters.map_type == '3':
            if self.parameters.scenario_probabilities[1] != 0 or self.parameters.scenario_probabilities[2] != 0:
                if self.parameters.n_agents > 5:
                    raise ValueError("For map_type '3', if the second or third value of scenario_probabilities is not zero, a maximum of 5 agents are allowed, as only a merge-in or a merge-out will be used.")
            elif self.parameters.n_agents > 10:
                raise ValueError("For map_type '3', if only the first value of scenario_probabilities is not zero, a maximum of 10 agents are allowed, as only an intersection will be used.")
        if self.parameters.n_nearing_agents_observed >= self.parameters.n_agents:
            raise ValueError('n_nearing_agents_observed must be less than n_agents')
        self.n_agents = self.parameters.n_agents
        self.timer = Timer(start=time.time(), end=0, step=torch.zeros(batch_dim, device=device, dtype=torch.int32), step_begin=time.time(), render_begin=0)
        map_file_path = kwargs.pop('map_file_path', None)
        if map_file_path is None:
            map_file_path = str(pathlib.Path(__file__).parent.parent / 'scenarios_data' / 'road_traffic' / 'road_traffic_cpm_lab.xml')
        self.map_data = get_map_data(map_file_path, device=device)
        reference_paths_all, reference_paths_intersection, reference_paths_merge_in, reference_paths_merge_out = get_reference_paths(self.map_data)
        if self.parameters.map_type in ('1', '2'):
            max_ref_path_points = max([ref_p['center_line'].shape[0] for ref_p in reference_paths_all]) + self.parameters.n_points_short_term * sample_interval_ref_path + 2
        else:
            max_ref_path_points = max([ref_p['center_line'].shape[0] for ref_p in reference_paths_intersection + reference_paths_merge_in + reference_paths_merge_out]) + self.parameters.n_points_short_term * sample_interval_ref_path + 2
        self.ref_paths_map_related = ReferencePathsMapRelated(long_term_all=reference_paths_all, long_term_intersection=reference_paths_intersection, long_term_merge_in=reference_paths_merge_in, long_term_merge_out=reference_paths_merge_out, point_extended_all=torch.zeros((len(reference_paths_all), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_intersection=torch.zeros((len(reference_paths_intersection), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_merge_in=torch.zeros((len(reference_paths_merge_in), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_merge_out=torch.zeros((len(reference_paths_merge_out), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), sample_interval=torch.tensor(sample_interval_ref_path, device=device, dtype=torch.int32))
        idx_broadcasting_entend = torch.arange(1, self.parameters.n_points_short_term * sample_interval_ref_path + 1, device=device, dtype=torch.int32).unsqueeze(1)
        for idx, i_path in enumerate(reference_paths_all):
            center_line_i = i_path['center_line']
            direction = center_line_i[-1] - center_line_i[-2]
            self.ref_paths_map_related.point_extended_all[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
        for idx, i_path in enumerate(reference_paths_intersection):
            center_line_i = i_path['center_line']
            direction = center_line_i[-1] - center_line_i[-2]
            self.ref_paths_map_related.point_extended_intersection[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
        for idx, i_path in enumerate(reference_paths_merge_in):
            center_line_i = i_path['center_line']
            direction = center_line_i[-1] - center_line_i[-2]
            self.ref_paths_map_related.point_extended_merge_in[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
        for idx, i_path in enumerate(reference_paths_merge_out):
            center_line_i = i_path['center_line']
            direction = center_line_i[-1] - center_line_i[-2]
            self.ref_paths_map_related.point_extended_merge_out[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
        self.ref_paths_agent_related = ReferencePathsAgentRelated(long_term=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), long_term_vec_normalized=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), left_boundary=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), right_boundary=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), entry=torch.zeros((batch_dim, self.n_agents, 2, 2), device=device, dtype=torch.float32), exit=torch.zeros((batch_dim, self.n_agents, 2, 2), device=device, dtype=torch.float32), is_loop=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), n_points_long_term=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), n_points_left_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), n_points_right_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), short_term=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32), short_term_indices=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_short_term), device=device, dtype=torch.int32), n_points_nearing_boundary=torch.tensor(self.parameters.n_points_nearing_boundary, device=device, dtype=torch.int32), nearing_points_left_boundary=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32), nearing_points_right_boundary=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32), scenario_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), path_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), point_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32))
        self.vertices = torch.zeros((batch_dim, self.n_agents, 5, 2), device=device, dtype=torch.float32)
        weighting_ref_directions = torch.linspace(1, 0.2, steps=self.parameters.n_points_short_term, device=device, dtype=torch.float32)
        weighting_ref_directions /= weighting_ref_directions.sum()
        self.rewards = Rewards(progress=torch.tensor(reward_progress, device=device, dtype=torch.float32), weighting_ref_directions=weighting_ref_directions, higth_v=torch.tensor(reward_vel, device=device, dtype=torch.float32), reach_goal=torch.tensor(reward_reach_goal, device=device, dtype=torch.float32))
        self.rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self.penalties = Penalties(deviate_from_ref_path=torch.tensor(-2 / 100, device=device, dtype=torch.float32), weighting_deviate_from_ref_path=self.map_data['mean_lane_width'] / 2, near_boundary=torch.tensor(-20 / 100, device=device, dtype=torch.float32), near_other_agents=torch.tensor(-20 / 100, device=device, dtype=torch.float32), collide_with_agents=torch.tensor(-100 / 100, device=device, dtype=torch.float32), collide_with_boundaries=torch.tensor(-100 / 100, device=device, dtype=torch.float32), change_steering=torch.tensor(-2 / 100, device=device, dtype=torch.float32), time=torch.tensor(5 / 100, device=device, dtype=torch.float32))
        self.observations = Observations(is_partial=torch.tensor(self.parameters.is_partial_observation, device=device, dtype=torch.bool), n_nearing_agents=torch.tensor(self.parameters.n_nearing_agents_observed, device=device, dtype=torch.int32), noise_level=torch.tensor(noise_level, device=device, dtype=torch.float32), n_stored_steps=torch.tensor(n_stored_steps, device=device, dtype=torch.int32), n_observed_steps=torch.tensor(n_observed_steps, device=device, dtype=torch.int32), nearing_agents_indices=torch.zeros((batch_dim, self.n_agents, self.parameters.n_nearing_agents_observed), device=device, dtype=torch.int32))
        if self.parameters.is_ego_view:
            self.observations.past_pos = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 2), device=device, dtype=torch.float32))
            self.observations.past_rot = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.float32))
            self.observations.past_vertices = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 4, 2), device=device, dtype=torch.float32))
            self.observations.past_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 2), device=device, dtype=torch.float32))
            self.observations.past_short_term_ref_points = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32))
            self.observations.past_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
            self.observations.past_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
        else:
            self.observations.past_pos = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 2), device=device, dtype=torch.float32))
            self.observations.past_rot = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
            self.observations.past_vertices = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 4, 2), device=device, dtype=torch.float32))
            self.observations.past_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 2), device=device, dtype=torch.float32))
            self.observations.past_short_term_ref_points = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32))
            self.observations.past_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
            self.observations.past_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
        self.observations.past_action_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_action_steering = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_distance_to_ref_path = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_distance_to_boundaries = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_distance_to_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_distance_to_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_distance_to_agents = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.float32))
        self.normalizers = Normalizers(pos=torch.tensor([self.agent_length * 10, self.agent_length * 10], device=device, dtype=torch.float32), pos_world=torch.tensor([self.world_x_dim, self.world_y_dim], device=device, dtype=torch.float32), v=torch.tensor(self.max_speed, device=device, dtype=torch.float32), rot=torch.tensor(2 * torch.pi, device=device, dtype=torch.float32), action_steering=self.max_steering_angle, action_vel=torch.tensor(self.max_speed, device=device, dtype=torch.float32), distance_lanelet=torch.tensor(lane_width * 3, device=device, dtype=torch.float32), distance_ref=torch.tensor(lane_width * 3, device=device, dtype=torch.float32), distance_agent=torch.tensor(self.agent_length * 10, device=device, dtype=torch.float32))
        self.distances = Distances(agents=torch.zeros(batch_dim, self.n_agents, self.n_agents, device=device, dtype=torch.float32), left_boundaries=torch.zeros((batch_dim, self.n_agents, 1 + 4), device=device, dtype=torch.float32), right_boundaries=torch.zeros((batch_dim, self.n_agents, 1 + 4), device=device, dtype=torch.float32), boundaries=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), ref_paths=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), closest_point_on_ref_path=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), closest_point_on_left_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), closest_point_on_right_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32))
        self.thresholds = Thresholds(reach_goal=torch.tensor(threshold_reach_goal, device=device, dtype=torch.float32), deviate_from_ref_path=torch.tensor(threshold_deviate_from_ref_path, device=device, dtype=torch.float32), near_boundary_low=torch.tensor(threshold_near_boundary_low, device=device, dtype=torch.float32), near_boundary_high=torch.tensor(threshold_near_boundary_high, device=device, dtype=torch.float32), near_other_agents_low=torch.tensor(threshold_near_other_agents_c2c_low, device=device, dtype=torch.float32), near_other_agents_high=torch.tensor(threshold_near_other_agents_c2c_high, device=device, dtype=torch.float32), change_steering=torch.tensor(threshold_change_steering, device=device, dtype=torch.float32).deg2rad(), no_reward_if_too_close_to_boundaries=torch.tensor(threshold_no_reward_if_too_close_to_boundaries, device=device, dtype=torch.float32), no_reward_if_too_close_to_other_agents=torch.tensor(threshold_no_reward_if_too_close_to_other_agents, device=device, dtype=torch.float32), distance_mask_agents=self.normalizers.pos[0])
        self.constants = Constants(env_idx_broadcasting=torch.arange(batch_dim, device=device, dtype=torch.int32).unsqueeze(-1), empty_action_vel=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), empty_action_steering=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), mask_pos=torch.tensor(1, device=device, dtype=torch.float32), mask_zero=torch.tensor(0, device=device, dtype=torch.float32), mask_one=torch.tensor(1, device=device, dtype=torch.float32), reset_agent_min_distance=torch.tensor((self.l_f + self.l_r) ** 2 + self.agent_width ** 2, device=device, dtype=torch.float32).sqrt() * 1.2)
        self.collisions = Collisions(with_agents=torch.zeros((batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.bool), with_lanelets=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), with_entry_segments=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), with_exit_segments=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool))
        self.initial_state_buffer = InitialStateBuffer(probability_record=torch.tensor(1.0, device=device, dtype=torch.float32), probability_use_recording=torch.tensor(kwargs.pop('probability_use_recording', 0.2), device=device, dtype=torch.float32), buffer=torch.zeros((100, self.n_agents, 8), device=device, dtype=torch.float32))
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.state_buffer = StateBuffer(buffer=torch.zeros((self.parameters.n_steps_before_recording, batch_dim, self.n_agents, 8), device=device, dtype=torch.float32))

    def init_world(self, batch_dim: int, device: torch.device):
        world = World(batch_dim, device, x_semidim=self.world_x_dim, y_semidim=self.world_y_dim, dt=self.parameters.dt)
        return world

    def init_agents(self, world, *kwargs):
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', shape=Box(length=self.l_f + self.l_r, width=self.agent_width), color=tuple(torch.rand(3, device=world.device, dtype=torch.float32).tolist()), collide=False, render_action=False, u_range=[self.max_speed, self.max_steering_angle], u_multiplier=[1, 1], max_speed=self.max_speed, dynamics=KinematicBicycle(world, width=self.agent_width, l_f=self.l_f, l_r=self.l_r, max_steering_angle=self.max_steering_angle, integration='rk4'))
            world.add_agent(agent)

    def reset_world_at(self, env_index: int=None, agent_index: int=None):
        """
        This function resets the world at the specified env_index and the specified agent_index.
        If env_index is given as None, the majority part of computation will be done in a vectorized manner.

        Args:
        :param env_index: index of the environment to reset. If None a vectorized reset should be performed
        :param agent_index: index of the agent to reset. If None all agents in the specified environment will be reset.
        """
        agents = self.world.agents
        is_reset_single_agent = agent_index is not None
        for env_i in [env_index] if env_index is not None else range(self.world.batch_dim):
            if env_i == 0:
                self.timer.start = time.time()
                self.timer.step_begin = time.time()
                self.timer.end = 0
            if not is_reset_single_agent:
                self.timer.step[env_i] = 0
            ref_paths_scenario, extended_points = self.reset_scenario_related_ref_paths(env_i, is_reset_single_agent, agent_index)
            if self.parameters.map_type == '2' and torch.rand(1) < self.initial_state_buffer.probability_use_recording and (self.initial_state_buffer.valid_size >= 1):
                is_use_state_buffer = True
                initial_state = self.initial_state_buffer.get_random()
                self.ref_paths_agent_related.scenario_id[env_i] = initial_state[:, self.initial_state_buffer.idx_scenario]
                self.ref_paths_agent_related.path_id[env_i] = initial_state[:, self.initial_state_buffer.idx_path]
                self.ref_paths_agent_related.point_id[env_i] = initial_state[:, self.initial_state_buffer.idx_point]
            else:
                is_use_state_buffer = False
                initial_state = None
            for i_agent in range(self.n_agents) if not is_reset_single_agent else agent_index.unsqueeze(0):
                ref_path, path_id = self.reset_init_state(env_i, i_agent, is_reset_single_agent, is_use_state_buffer, initial_state, ref_paths_scenario, agents)
                self.reset_agent_related_ref_path(env_i, i_agent, ref_path, path_id, extended_points)
            if env_index is None:
                if env_i == self.world.batch_dim - 1:
                    env_j = slice(None)
                else:
                    continue
            else:
                env_j = env_i
            for i_agent in range(self.n_agents) if not is_reset_single_agent else agent_index.unsqueeze(0):
                self.reset_init_distances_and_short_term_ref_path(env_j, i_agent, agents)
            mutual_distances = get_distances_between_agents(self=self, is_set_diagonal=True)
            self.distances.agents[env_j, :, :] = mutual_distances[env_j, :, :]
            self.collisions.with_agents[env_j, :, :] = False
            self.collisions.with_lanelets[env_j, :] = False
            self.collisions.with_entry_segments[env_j, :] = False
            self.collisions.with_exit_segments[env_j, :] = False
        self.state_buffer.reset()
        state_add = torch.cat((torch.stack([a.state.pos for a in agents], dim=1), torch.stack([a.state.rot for a in agents], dim=1), torch.stack([a.state.vel for a in agents], dim=1), self.ref_paths_agent_related.scenario_id[:].unsqueeze(-1), self.ref_paths_agent_related.path_id[:].unsqueeze(-1), self.ref_paths_agent_related.point_id[:].unsqueeze(-1)), dim=-1)
        self.state_buffer.add(state_add)

    def reset_scenario_related_ref_paths(self, env_i, is_reset_single_agent, agent_index):
        """
        Resets scenario-related reference paths and scenario IDs for the specified environment and agents.

        This function determines and sets the long-term reference paths based on the current map_type.
        If `is_reset_single_agent` is true, the current paths for the specified agent will be kept.

        Args:
            env_i (int): The index of the environment to reset.
            is_reset_single_agent (bool): Flag indicating whether only a single agent is being reset.
            agent_index (int or None): The index of the agent to reset. If None, all agents in
                                    the specified environment are reset.

        Returns:
            - ref_paths_scenario (list): The list of reference paths for the current scenario.
            - extended_points (tensor): [numOfRefPaths, numExtendedPoints, 2] The extended points for the current scenario.
        """
        if self.parameters.map_type in {'1', '2'}:
            ref_paths_scenario = self.ref_paths_map_related.long_term_all
            extended_points = self.ref_paths_map_related.point_extended_all
            self.ref_paths_agent_related.scenario_id[env_i, :] = 0
        else:
            if is_reset_single_agent:
                scenario_id = self.ref_paths_agent_related.scenario_id[env_i, agent_index]
            else:
                scenario_id = torch.multinomial(torch.tensor(self.parameters.scenario_probabilities, device=self.world.device, dtype=torch.float32), 1, replacement=True).item() + 1
                self.ref_paths_agent_related.scenario_id[env_i, :] = scenario_id
            if scenario_id == 1:
                ref_paths_scenario = self.ref_paths_map_related.long_term_intersection
                extended_points = self.ref_paths_map_related.point_extended_intersection
            elif scenario_id == 2:
                ref_paths_scenario = self.ref_paths_map_related.long_term_merge_in
                extended_points = self.ref_paths_map_related.point_extended_merge_in
            elif scenario_id == 3:
                ref_paths_scenario = self.ref_paths_map_related.long_term_merge_out
                extended_points = self.ref_paths_map_related.point_extended_merge_out
        return (ref_paths_scenario, extended_points)

    def reset_init_state(self, env_i, i_agent, is_reset_single_agent, is_use_state_buffer, initial_state, ref_paths_scenario, agents):
        """
        This function resets the initial position, rotation, and velocity for an agent based on the provided
        initial state buffer if it is used. Otherwise, it randomly generates initial states ensuring they
        are feasible and do not collide with other agents.
        """
        if is_use_state_buffer:
            path_id = initial_state[i_agent, self.initial_state_buffer.idx_path].int()
            ref_path = ref_paths_scenario[path_id]
            agents[i_agent].set_pos(initial_state[i_agent, 0:2], batch_index=env_i)
            agents[i_agent].set_rot(initial_state[i_agent, 2], batch_index=env_i)
            agents[i_agent].set_vel(initial_state[i_agent, 3:5], batch_index=env_i)
        else:
            is_feasible_initial_position_found = False
            while not is_feasible_initial_position_found:
                path_id = torch.randint(0, len(ref_paths_scenario), (1,)).item()
                self.ref_paths_agent_related.path_id[env_i, i_agent] = path_id
                ref_path = ref_paths_scenario[path_id]
                num_points = ref_path['center_line'].shape[0]
                if (self.parameters.scenario_probabilities[1] == 0) & (self.parameters.scenario_probabilities[2] == 0):
                    random_point_id = torch.randint(6, int(num_points / 2), (1,)).item()
                else:
                    random_point_id = torch.randint(3, num_points - 5, (1,)).item()
                self.ref_paths_agent_related.point_id[env_i, i_agent] = random_point_id
                position_start = ref_path['center_line'][random_point_id]
                agents[i_agent].set_pos(position_start, batch_index=env_i)
                if not is_reset_single_agent:
                    if i_agent == 0:
                        is_feasible_initial_position_found = True
                        continue
                    else:
                        positions = torch.stack([self.world.agents[i].state.pos[env_i] for i in range(i_agent + 1)])
                else:
                    positions = torch.stack([self.world.agents[i].state.pos[env_i] for i in range(self.n_agents)])
                diff_sq = (positions[i_agent, :] - positions) ** 2
                initial_mutual_distances_sq = torch.sum(diff_sq, dim=-1)
                initial_mutual_distances_sq[i_agent] = torch.max(initial_mutual_distances_sq) + 1
                min_distance_sq = torch.min(initial_mutual_distances_sq)
                is_feasible_initial_position_found = min_distance_sq >= self.constants.reset_agent_min_distance ** 2
            rot_start = ref_path['center_line_yaw'][random_point_id]
            vel_start_abs = torch.rand(1, dtype=torch.float32, device=self.world.device) * agents[i_agent].max_speed
            vel_start = torch.hstack([vel_start_abs * torch.cos(rot_start), vel_start_abs * torch.sin(rot_start)])
            agents[i_agent].set_rot(rot_start, batch_index=env_i)
            agents[i_agent].set_vel(vel_start, batch_index=env_i)
            return (ref_path, path_id)

    def reset_agent_related_ref_path(self, env_i, i_agent, ref_path, path_id, extended_points):
        """
        This function resets the agent-related reference paths and updates various related attributes
        for a specified agent in an environment.
        """
        n_points_long_term = ref_path['center_line'].shape[0]
        self.ref_paths_agent_related.long_term[env_i, i_agent, 0:n_points_long_term, :] = ref_path['center_line']
        self.ref_paths_agent_related.long_term[env_i, i_agent, n_points_long_term:n_points_long_term + self.parameters.n_points_short_term * self.ref_paths_map_related.sample_interval, :] = extended_points[path_id, :, :]
        self.ref_paths_agent_related.long_term[env_i, i_agent, n_points_long_term + self.parameters.n_points_short_term * self.ref_paths_map_related.sample_interval:, :] = extended_points[path_id, -1, :]
        self.ref_paths_agent_related.n_points_long_term[env_i, i_agent] = n_points_long_term
        self.ref_paths_agent_related.long_term_vec_normalized[env_i, i_agent, 0:n_points_long_term - 1, :] = ref_path['center_line_vec_normalized']
        self.ref_paths_agent_related.long_term_vec_normalized[env_i, i_agent, n_points_long_term - 1:n_points_long_term - 1 + self.parameters.n_points_short_term * self.ref_paths_map_related.sample_interval, :] = ref_path['center_line_vec_normalized'][-1, :]
        n_points_left_b = ref_path['left_boundary_shared'].shape[0]
        self.ref_paths_agent_related.left_boundary[env_i, i_agent, 0:n_points_left_b, :] = ref_path['left_boundary_shared']
        self.ref_paths_agent_related.left_boundary[env_i, i_agent, n_points_left_b:, :] = ref_path['left_boundary_shared'][-1, :]
        self.ref_paths_agent_related.n_points_left_b[env_i, i_agent] = n_points_left_b
        n_points_right_b = ref_path['right_boundary_shared'].shape[0]
        self.ref_paths_agent_related.right_boundary[env_i, i_agent, 0:n_points_right_b, :] = ref_path['right_boundary_shared']
        self.ref_paths_agent_related.right_boundary[env_i, i_agent, n_points_right_b:, :] = ref_path['right_boundary_shared'][-1, :]
        self.ref_paths_agent_related.n_points_right_b[env_i, i_agent] = n_points_right_b
        self.ref_paths_agent_related.entry[env_i, i_agent, 0, :] = ref_path['left_boundary_shared'][0, :]
        self.ref_paths_agent_related.entry[env_i, i_agent, 1, :] = ref_path['right_boundary_shared'][0, :]
        self.ref_paths_agent_related.exit[env_i, i_agent, 0, :] = ref_path['left_boundary_shared'][-1, :]
        self.ref_paths_agent_related.exit[env_i, i_agent, 1, :] = ref_path['right_boundary_shared'][-1, :]
        self.ref_paths_agent_related.is_loop[env_i, i_agent] = ref_path['is_loop']

    def reset_init_distances_and_short_term_ref_path(self, env_j, i_agent, agents):
        """
        This function calculates the distances from the agent's center of gravity (CG) to its reference path and boundaries,
        and computes the positions of the four vertices of the agent. It also determines the short-term reference paths
        for the agent based on the long-term reference paths and the agent's current position.
        """
        self.distances.ref_paths[env_j, i_agent], self.distances.closest_point_on_ref_path[env_j, i_agent] = get_perpendicular_distances(point=agents[i_agent].state.pos[env_j, :], polyline=self.ref_paths_agent_related.long_term[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[env_j, i_agent])
        center_2_left_b, self.distances.closest_point_on_left_b[env_j, i_agent] = get_perpendicular_distances(point=agents[i_agent].state.pos[env_j, :], polyline=self.ref_paths_agent_related.left_boundary[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_left_b[env_j, i_agent])
        self.distances.left_boundaries[env_j, i_agent, 0] = center_2_left_b - agents[i_agent].shape.width / 2
        center_2_right_b, self.distances.closest_point_on_right_b[env_j, i_agent] = get_perpendicular_distances(point=agents[i_agent].state.pos[env_j, :], polyline=self.ref_paths_agent_related.right_boundary[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_right_b[env_j, i_agent])
        self.distances.right_boundaries[env_j, i_agent, 0] = center_2_right_b - agents[i_agent].shape.width / 2
        self.vertices[env_j, i_agent] = get_rectangle_vertices(center=agents[i_agent].state.pos[env_j, :], yaw=agents[i_agent].state.rot[env_j, :], width=agents[i_agent].shape.width, length=agents[i_agent].shape.length, is_close_shape=True)
        for c_i in range(4):
            self.distances.left_boundaries[env_j, i_agent, c_i + 1], _ = get_perpendicular_distances(point=self.vertices[env_j, i_agent, c_i, :], polyline=self.ref_paths_agent_related.left_boundary[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_left_b[env_j, i_agent])
            self.distances.right_boundaries[env_j, i_agent, c_i + 1], _ = get_perpendicular_distances(point=self.vertices[env_j, i_agent, c_i, :], polyline=self.ref_paths_agent_related.right_boundary[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_right_b[env_j, i_agent])
        self.distances.boundaries[env_j, i_agent], _ = torch.min(torch.hstack((self.distances.left_boundaries[env_j, i_agent], self.distances.right_boundaries[env_j, i_agent])), dim=-1)
        self.ref_paths_agent_related.short_term[env_j, i_agent], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.long_term[env_j, i_agent], index_closest_point=self.distances.closest_point_on_ref_path[env_j, i_agent], n_points_to_return=self.parameters.n_points_short_term, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[env_j, i_agent], sample_interval=self.ref_paths_map_related.sample_interval, n_points_shift=1)
        if not self.parameters.is_observe_distance_to_boundaries:
            self.ref_paths_agent_related.nearing_points_left_boundary[env_j, i_agent], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.left_boundary[env_j, i_agent], index_closest_point=self.distances.closest_point_on_left_b[env_j, i_agent], n_points_to_return=self.parameters.n_points_nearing_boundary, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[env_j, i_agent], sample_interval=1, n_points_shift=1)
            self.ref_paths_agent_related.nearing_points_right_boundary[env_j, i_agent], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.right_boundary[env_j, i_agent], index_closest_point=self.distances.closest_point_on_right_b[env_j, i_agent], n_points_to_return=self.parameters.n_points_nearing_boundary, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[env_j, i_agent], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[env_j, i_agent], sample_interval=1, n_points_shift=1)

    def reward(self, agent: Agent):
        """
        Issue rewards for the given agent in all envs.
            Positive Rewards:
                Moving forward (become negative if the projection of the moving direction to its reference path is negative)
                Moving forward with high speed (become negative if the projection of the moving direction to its reference path is negative)
                Reaching goal (optional)

            Negative Rewards (penalties):
                Too close to lane boundaries
                Too close to other agents
                Deviating from reference paths
                Changing steering too quick
                Colliding with other agents
                Colliding with lane boundaries

        Args:
            agent: The agent for which the observation is to be generated.

        Returns:
            A tensor with shape [batch_dim].
        """
        self.rew[:] = 0
        agent_index = self.world.agents.index(agent)
        self.update_state_before_rewarding(agent, agent_index)
        latest_state = self.state_buffer.get_latest(n=1)
        move_vec = (agent.state.pos - latest_state[:, agent_index, 0:2]).unsqueeze(1)
        ref_points_vecs = self.ref_paths_agent_related.short_term[:, agent_index] - latest_state[:, agent_index, 0:2].unsqueeze(1)
        move_projected = torch.sum(move_vec * ref_points_vecs, dim=-1)
        move_projected_weighted = torch.matmul(move_projected, self.rewards.weighting_ref_directions)
        reward_movement = move_projected_weighted / (agent.max_speed * self.world.dt) * self.rewards.progress
        self.rew += reward_movement
        v_proj = torch.sum(agent.state.vel.unsqueeze(1) * ref_points_vecs, dim=-1).mean(-1)
        factor_moving_direction = torch.where(v_proj > 0, 1, 2)
        reward_vel = factor_moving_direction * v_proj / agent.max_speed * self.rewards.higth_v
        self.rew += reward_vel
        reward_goal = self.collisions.with_exit_segments[:, agent_index] * self.rewards.reach_goal
        self.rew += reward_goal
        penalty_close_to_lanelets = exponential_decreasing_fcn(x=self.distances.boundaries[:, agent_index], x0=self.thresholds.near_boundary_low, x1=self.thresholds.near_boundary_high) * self.penalties.near_boundary
        self.rew += penalty_close_to_lanelets
        mutual_distance_exp_fcn = exponential_decreasing_fcn(x=self.distances.agents[:, agent_index, :], x0=self.thresholds.near_other_agents_low, x1=self.thresholds.near_other_agents_high)
        penalty_close_to_agents = torch.sum(mutual_distance_exp_fcn, dim=1) * self.penalties.near_other_agents
        self.rew += penalty_close_to_agents
        self.rew += self.distances.ref_paths[:, agent_index] / self.penalties.weighting_deviate_from_ref_path * self.penalties.deviate_from_ref_path
        steering_current = self.observations.past_action_steering.get_latest(n=1)[:, agent_index]
        steering_past = self.observations.past_action_steering.get_latest(n=2)[:, agent_index]
        steering_change = torch.clamp((steering_current - steering_past).abs() * self.normalizers.action_steering - self.thresholds.change_steering, min=0)
        steering_change_reward_factor = steering_change / (2 * agent.u_range[1] - 2 * self.thresholds.change_steering)
        penalty_change_steering = steering_change_reward_factor * self.penalties.change_steering
        self.rew += penalty_change_steering
        is_collide_with_agents = self.collisions.with_agents[:, agent_index]
        penalty_collide_other_agents = is_collide_with_agents.any(dim=-1) * self.penalties.collide_with_agents
        self.rew += penalty_collide_other_agents
        is_collide_with_lanelets = self.collisions.with_lanelets[:, agent_index]
        penalty_collide_lanelet = is_collide_with_lanelets * self.penalties.collide_with_boundaries
        self.rew += penalty_collide_lanelet
        time_reward = torch.where(v_proj > 0, 1, -1) * agent.state.vel.norm(dim=-1) / agent.max_speed * self.penalties.time
        self.rew += time_reward
        self.update_state_after_rewarding(agent_index)
        return self.rew

    def update_state_before_rewarding(self, agent, agent_index):
        """Update some states (such as mutual distances between agents, vertices of each agent, and
        collision matrices) that will be used before rewarding agents.
        """
        if agent_index == 0:
            self.timer.step_begin = time.time()
            self.timer.step += 1
            self.distances.agents = get_distances_between_agents(self=self, is_set_diagonal=True)
            self.collisions.with_agents[:] = False
            self.collisions.with_lanelets[:] = False
            self.collisions.with_entry_segments[:] = False
            self.collisions.with_exit_segments[:] = False
            for a_i in range(self.n_agents):
                self.vertices[:, a_i] = get_rectangle_vertices(center=self.world.agents[a_i].state.pos, yaw=self.world.agents[a_i].state.rot, width=self.world.agents[a_i].shape.width, length=self.world.agents[a_i].shape.length, is_close_shape=True)
                for a_j in range(a_i + 1, self.n_agents):
                    collision_batch_index = interX(self.vertices[:, a_i], self.vertices[:, a_j], False)
                    self.collisions.with_agents[torch.nonzero(collision_batch_index), a_i, a_j] = True
                    self.collisions.with_agents[torch.nonzero(collision_batch_index), a_j, a_i] = True
                collision_with_left_boundary = interX(L1=self.vertices[:, a_i], L2=self.ref_paths_agent_related.left_boundary[:, a_i], is_return_points=False)
                collision_with_right_boundary = interX(L1=self.vertices[:, a_i], L2=self.ref_paths_agent_related.right_boundary[:, a_i], is_return_points=False)
                self.collisions.with_lanelets[collision_with_left_boundary | collision_with_right_boundary, a_i] = True
                if not self.ref_paths_agent_related.is_loop[:, a_i].any():
                    self.collisions.with_entry_segments[:, a_i] = interX(L1=self.vertices[:, a_i], L2=self.ref_paths_agent_related.entry[:, a_i], is_return_points=False)
                    self.collisions.with_exit_segments[:, a_i] = interX(L1=self.vertices[:, a_i], L2=self.ref_paths_agent_related.exit[:, a_i], is_return_points=False)
        self.distances.ref_paths[:, agent_index], self.distances.closest_point_on_ref_path[:, agent_index] = get_perpendicular_distances(point=agent.state.pos, polyline=self.ref_paths_agent_related.long_term[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[:, agent_index])
        center_2_left_b, self.distances.closest_point_on_left_b[:, agent_index] = get_perpendicular_distances(point=agent.state.pos[:, :], polyline=self.ref_paths_agent_related.left_boundary[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_left_b[:, agent_index])
        self.distances.left_boundaries[:, agent_index, 0] = center_2_left_b - agent.shape.width / 2
        center_2_right_b, self.distances.closest_point_on_right_b[:, agent_index] = get_perpendicular_distances(point=agent.state.pos[:, :], polyline=self.ref_paths_agent_related.right_boundary[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_right_b[:, agent_index])
        self.distances.right_boundaries[:, agent_index, 0] = center_2_right_b - agent.shape.width / 2
        for c_i in range(4):
            self.distances.left_boundaries[:, agent_index, c_i + 1], _ = get_perpendicular_distances(point=self.vertices[:, agent_index, c_i, :], polyline=self.ref_paths_agent_related.left_boundary[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_left_b[:, agent_index])
            self.distances.right_boundaries[:, agent_index, c_i + 1], _ = get_perpendicular_distances(point=self.vertices[:, agent_index, c_i, :], polyline=self.ref_paths_agent_related.right_boundary[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_right_b[:, agent_index])
        self.distances.boundaries[:, agent_index], _ = torch.min(torch.hstack((self.distances.left_boundaries[:, agent_index], self.distances.right_boundaries[:, agent_index])), dim=-1)

    def update_state_after_rewarding(self, agent_index):
        """Update some states (such as previous positions and short-term reference paths) after rewarding agents."""
        if agent_index == self.n_agents - 1:
            state_add = torch.cat((torch.stack([a.state.pos for a in self.world.agents], dim=1), torch.stack([a.state.rot for a in self.world.agents], dim=1), torch.stack([a.state.vel for a in self.world.agents], dim=1), self.ref_paths_agent_related.scenario_id[:].unsqueeze(-1), self.ref_paths_agent_related.path_id[:].unsqueeze(-1), self.ref_paths_agent_related.point_id[:].unsqueeze(-1)), dim=-1)
            self.state_buffer.add(state_add)
        self.ref_paths_agent_related.short_term[:, agent_index], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.long_term[:, agent_index], index_closest_point=self.distances.closest_point_on_ref_path[:, agent_index], n_points_to_return=self.parameters.n_points_short_term, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[:, agent_index], sample_interval=self.ref_paths_map_related.sample_interval)
        if not self.parameters.is_observe_distance_to_boundaries:
            self.ref_paths_agent_related.nearing_points_left_boundary[:, agent_index], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.left_boundary[:, agent_index], index_closest_point=self.distances.closest_point_on_left_b[:, agent_index], n_points_to_return=self.parameters.n_points_nearing_boundary, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[:, agent_index], sample_interval=1, n_points_shift=-2)
            self.ref_paths_agent_related.nearing_points_right_boundary[:, agent_index], _ = get_short_term_reference_path(polyline=self.ref_paths_agent_related.right_boundary[:, agent_index], index_closest_point=self.distances.closest_point_on_right_b[:, agent_index], n_points_to_return=self.parameters.n_points_nearing_boundary, device=self.world.device, is_polyline_a_loop=self.ref_paths_agent_related.is_loop[:, agent_index], n_points_long_term=self.ref_paths_agent_related.n_points_long_term[:, agent_index], sample_interval=1, n_points_shift=-2)

    def observation(self, agent: Agent):
        """
        Generate an observation for the given agent in all envs.

        Args:
            agent: The agent for which the observation is to be generated.

        Returns:
            The observation for the given agent in all envs, which consists of the observation of this agent itself and possibly the observation of its surrounding agents.
                The observation of this agent itself includes
                    position (in case of using bird view),
                    rotation (in case of using bird view),
                    velocity,
                    short-term reference path,
                    distance to its reference path (optional), and
                    lane boundaries (or distances to them).
                The observation of its surrounding agents includes their
                    vertices (or positions and rotations),
                    velocities,
                    distances to them (optional), and
                    reference paths (optional).
        """
        agent_index = self.world.agents.index(agent)
        self.update_observation_and_normalize(agent, agent_index)
        obs_other_agents = self.observe_other_agents(agent_index)
        obs_self = self.observe_self(agent_index)
        obs_self.append(obs_other_agents)
        obs_all = [o for o in obs_self if o is not None]
        obs = torch.hstack(obs_all)
        if self.parameters.is_add_noise:
            return obs + self.observations.noise_level * torch.rand_like(obs, device=self.world.device, dtype=torch.float32)
        else:
            return obs

    def update_observation_and_normalize(self, agent, agent_index):
        """Update observation and normalize them."""
        if agent_index == 0:
            positions_global = torch.stack([a.state.pos for a in self.world.agents], dim=0).transpose(0, 1)
            rotations_global = torch.stack([a.state.rot for a in self.world.agents], dim=0).transpose(0, 1).squeeze(-1)
            self.observations.past_distance_to_agents.add(self.distances.agents / self.normalizers.distance_lanelet)
            self.observations.past_distance_to_ref_path.add(self.distances.ref_paths / self.normalizers.distance_lanelet)
            self.observations.past_distance_to_left_boundary.add(torch.min(self.distances.left_boundaries, dim=-1)[0] / self.normalizers.distance_lanelet)
            self.observations.past_distance_to_right_boundary.add(torch.min(self.distances.right_boundaries, dim=-1)[0] / self.normalizers.distance_lanelet)
            self.observations.past_distance_to_boundaries.add(self.distances.boundaries / self.normalizers.distance_lanelet)
            if self.parameters.is_ego_view:
                pos_i_others = torch.zeros((self.world.batch_dim, self.n_agents, self.n_agents, 2), device=self.world.device, dtype=torch.float32)
                rot_i_others = torch.zeros((self.world.batch_dim, self.n_agents, self.n_agents), device=self.world.device, dtype=torch.float32)
                vel_i_others = torch.zeros((self.world.batch_dim, self.n_agents, self.n_agents, 2), device=self.world.device, dtype=torch.float32)
                ref_i_others = torch.zeros_like(self.observations.past_short_term_ref_points.get_latest())
                l_b_i_others = torch.zeros_like(self.observations.past_left_boundary.get_latest())
                r_b_i_others = torch.zeros_like(self.observations.past_right_boundary.get_latest())
                ver_i_others = torch.zeros_like(self.observations.past_vertices.get_latest())
                for a_i in range(self.n_agents):
                    pos_i = self.world.agents[a_i].state.pos
                    rot_i = self.world.agents[a_i].state.rot
                    pos_i_others[:, a_i] = transform_from_global_to_local_coordinate(pos_i=pos_i, pos_j=positions_global, rot_i=rot_i)
                    rot_i_others[:, a_i] = rotations_global - rot_i
                    for a_j in range(self.n_agents):
                        rot_rel = rot_i_others[:, a_i, a_j].unsqueeze(1)
                        vel_abs = torch.norm(self.world.agents[a_j].state.vel, dim=1).unsqueeze(1)
                        vel_i_others[:, a_i, a_j] = torch.hstack((vel_abs * torch.cos(rot_rel), vel_abs * torch.sin(rot_rel)))
                        ref_i_others[:, a_i, a_j] = transform_from_global_to_local_coordinate(pos_i=pos_i, pos_j=self.ref_paths_agent_related.short_term[:, a_j], rot_i=rot_i)
                        if not self.parameters.is_observe_distance_to_boundaries:
                            l_b_i_others[:, a_i, a_j] = transform_from_global_to_local_coordinate(pos_i=pos_i, pos_j=self.ref_paths_agent_related.nearing_points_left_boundary[:, a_j], rot_i=rot_i)
                            r_b_i_others[:, a_i, a_j] = transform_from_global_to_local_coordinate(pos_i=pos_i, pos_j=self.ref_paths_agent_related.nearing_points_right_boundary[:, a_j], rot_i=rot_i)
                        ver_i_others[:, a_i, a_j] = transform_from_global_to_local_coordinate(pos_i=pos_i, pos_j=self.vertices[:, a_j, 0:4, :], rot_i=rot_i)
                self.observations.past_pos.add(pos_i_others / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_rot.add(rot_i_others / self.normalizers.rot)
                self.observations.past_vel.add(vel_i_others / self.normalizers.v)
                self.observations.past_short_term_ref_points.add(ref_i_others / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_left_boundary.add(l_b_i_others / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_right_boundary.add(r_b_i_others / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_vertices.add(ver_i_others / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
            else:
                self.observations.past_pos.add(positions_global / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_vel.add(torch.stack([a.state.vel for a in self.world.agents], dim=1) / self.normalizers.v)
                self.observations.past_rot.add(rotations_global[:] / self.normalizers.rot)
                self.observations.past_vertices.add(self.vertices[:, :, 0:4, :] / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_short_term_ref_points.add(self.ref_paths_agent_related.short_term[:] / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_left_boundary.add(self.ref_paths_agent_related.nearing_points_left_boundary / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
                self.observations.past_right_boundary.add(self.ref_paths_agent_related.nearing_points_right_boundary / (self.normalizers.pos if self.parameters.is_ego_view else self.normalizers.pos_world))
            if agent.action.u is None:
                self.observations.past_action_vel.add(self.constants.empty_action_vel)
                self.observations.past_action_steering.add(self.constants.empty_action_steering)
            else:
                self.observations.past_action_vel.add(torch.stack([a.action.u[:, 0] for a in self.world.agents], dim=1) / self.normalizers.action_vel)
                self.observations.past_action_steering.add(torch.stack([a.action.u[:, 1] for a in self.world.agents], dim=1) / self.normalizers.action_steering)

    def observe_other_agents(self, agent_index):
        """Observe surrounding agents."""
        if self.observations.is_partial:
            nearing_agents_distances, nearing_agents_indices = torch.topk(self.distances.agents[:, agent_index], k=self.observations.n_nearing_agents, largest=False)
            if self.parameters.is_apply_mask:
                mask_nearing_agents_too_far = nearing_agents_distances >= self.thresholds.distance_mask_agents
            else:
                mask_nearing_agents_too_far = torch.zeros((self.world.batch_dim, self.parameters.n_nearing_agents_observed), device=self.world.device, dtype=torch.bool)
            indexing_tuple_1 = (self.constants.env_idx_broadcasting,) + ((agent_index,) if self.parameters.is_ego_view else ()) + (nearing_agents_indices,)
            obs_pos_other_agents = self.observations.past_pos.get_latest()[indexing_tuple_1]
            obs_pos_other_agents[mask_nearing_agents_too_far] = self.constants.mask_one
            obs_rot_other_agents = self.observations.past_rot.get_latest()[indexing_tuple_1]
            obs_rot_other_agents[mask_nearing_agents_too_far] = self.constants.mask_zero
            obs_vel_other_agents = self.observations.past_vel.get_latest()[indexing_tuple_1]
            obs_vel_other_agents[mask_nearing_agents_too_far] = self.constants.mask_zero
            obs_ref_path_other_agents = self.observations.past_short_term_ref_points.get_latest()[indexing_tuple_1]
            obs_ref_path_other_agents[mask_nearing_agents_too_far] = self.constants.mask_one
            obs_vertices_other_agents = self.observations.past_vertices.get_latest()[indexing_tuple_1]
            obs_vertices_other_agents[mask_nearing_agents_too_far] = self.constants.mask_one
            obs_distance_other_agents = self.observations.past_distance_to_agents.get_latest()[self.constants.env_idx_broadcasting, agent_index, nearing_agents_indices]
            obs_distance_other_agents[mask_nearing_agents_too_far] = self.constants.mask_one
        else:
            obs_pos_other_agents = self.observations.past_pos.get_latest()[:, agent_index]
            obs_rot_other_agents = self.observations.past_rot.get_latest()[:, agent_index]
            obs_vel_other_agents = self.observations.past_vel.get_latest()[:, agent_index]
            obs_ref_path_other_agents = self.observations.past_short_term_ref_points.get_latest()[:, agent_index]
            obs_vertices_other_agents = self.observations.past_vertices.get_latest()[:, agent_index]
            obs_distance_other_agents = self.observations.past_distance_to_agents.get_latest()[:, agent_index]
            obs_distance_other_agents[:, agent_index] = 0
        obs_pos_other_agents_flat = obs_pos_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_rot_other_agents_flat = obs_rot_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_vel_other_agents_flat = obs_vel_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_ref_path_other_agents_flat = obs_ref_path_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_vertices_other_agents_flat = obs_vertices_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_distance_other_agents_flat = obs_distance_other_agents.reshape(self.world.batch_dim, self.observations.n_nearing_agents, -1)
        obs_others_list = [obs_vertices_other_agents_flat if self.parameters.is_observe_vertices else torch.cat([obs_pos_other_agents_flat, obs_rot_other_agents_flat], dim=-1), obs_vel_other_agents_flat, obs_distance_other_agents_flat if self.parameters.is_observe_distance_to_agents else None, obs_ref_path_other_agents_flat if self.parameters.is_observe_ref_path_other_agents else None]
        obs_others_list = [o for o in obs_others_list if o is not None]
        obs_other_agents = torch.cat(obs_others_list, dim=-1).reshape(self.world.batch_dim, -1)
        return obs_other_agents

    def observe_self(self, agent_index):
        """Observe the given agent itself."""
        indexing_tuple_3 = (self.constants.env_idx_broadcasting,) + (agent_index,) + ((agent_index,) if self.parameters.is_ego_view else ())
        indexing_tuple_vel = (self.constants.env_idx_broadcasting,) + (agent_index,) + ((agent_index, 0) if self.parameters.is_ego_view else ())
        obs_self = [None if self.parameters.is_ego_view else self.observations.past_pos.get_latest()[indexing_tuple_3].reshape(self.world.batch_dim, -1), None if self.parameters.is_ego_view else self.observations.past_rot.get_latest()[indexing_tuple_3].reshape(self.world.batch_dim, -1), self.observations.past_vel.get_latest()[indexing_tuple_vel].reshape(self.world.batch_dim, -1), self.observations.past_short_term_ref_points.get_latest()[indexing_tuple_3].reshape(self.world.batch_dim, -1), self.observations.past_distance_to_ref_path.get_latest()[:, agent_index].reshape(self.world.batch_dim, -1) if self.parameters.is_observe_distance_to_center_line else None, self.observations.past_distance_to_left_boundary.get_latest()[:, agent_index].reshape(self.world.batch_dim, -1) if self.parameters.is_observe_distance_to_boundaries else self.observations.past_left_boundary.get_latest()[indexing_tuple_3].reshape(self.world.batch_dim, -1), self.observations.past_distance_to_right_boundary.get_latest()[:, agent_index].reshape(self.world.batch_dim, -1) if self.parameters.is_observe_distance_to_boundaries else self.observations.past_right_boundary.get_latest()[indexing_tuple_3].reshape(self.world.batch_dim, -1)]
        return obs_self

    def done(self):
        """
        This function computes the done flag for each env in a vectorized way.

        Testing mode is designed to test the learned policy. In testing mode, collisions do
        not terminate the current simulation; instead, the colliding agents (not all agents)
        will be reset. Besides, if `map_type` is "3", those agents who leave their entries
        or exits will be reset.
        """
        is_collision_with_agents = self.collisions.with_agents.view(self.world.batch_dim, -1).any(dim=-1)
        is_collision_with_lanelets = self.collisions.with_lanelets.any(dim=-1)
        if self.parameters.map_type == '2':
            if torch.rand(1) > 1 - self.initial_state_buffer.probability_record:
                for env_collide in torch.where(is_collision_with_agents)[0]:
                    self.initial_state_buffer.add(self.state_buffer.get_latest(n=self.parameters.n_steps_stored)[env_collide])
        if self.parameters.is_testing_mode:
            is_done = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.bool)
            agents_reset = self.collisions.with_agents.any(dim=-1) | self.collisions.with_lanelets | self.collisions.with_entry_segments | self.collisions.with_exit_segments
            agents_reset_indices = torch.where(agents_reset)
            for env_idx, agent_idx in zip(agents_reset_indices[0], agents_reset_indices[1]):
                self.reset_world_at(env_index=env_idx, agent_index=agent_idx)
        elif self.parameters.map_type == '3':
            is_done = is_collision_with_agents | is_collision_with_lanelets
            agents_reset = self.collisions.with_entry_segments | self.collisions.with_exit_segments
            agents_reset_indices = torch.where(agents_reset)
            for env_idx, agent_idx in zip(agents_reset_indices[0], agents_reset_indices[1]):
                if not is_done[env_idx]:
                    self.reset_world_at(env_index=env_idx, agent_index=agent_idx)
        else:
            is_done = is_collision_with_agents | is_collision_with_lanelets
        return is_done

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        """
        This function computes the info dict for "agent" in a vectorized way
        The returned dict should have a key for each info of interest and the corresponding value should
        be a tensor of shape (n_envs, info_size)

        Implementors can access the world at "self.world"

        To increase performance, tensors created should have the device set, like:
        torch.tensor(..., device=self.world.device)

        :param agent: Agent batch to compute info of
        :return: info: A dict with a key for each info of interest, and a tensor value  of shape (n_envs, info_size)
        """
        agent_index = self.world.agents.index(agent)
        is_action_empty = agent.action.u is None
        is_collision_with_agents = self.collisions.with_agents[:, agent_index].any(dim=-1)
        is_collision_with_lanelets = self.collisions.with_lanelets.any(dim=-1)
        info = {'pos': agent.state.pos / self.normalizers.pos_world, 'rot': angle_eliminate_two_pi(agent.state.rot) / self.normalizers.rot, 'vel': agent.state.vel / self.normalizers.v, 'act_vel': agent.action.u[:, 0] / self.normalizers.action_vel if not is_action_empty else self.constants.empty_action_vel[:, agent_index], 'act_steer': agent.action.u[:, 1] / self.normalizers.action_steering if not is_action_empty else self.constants.empty_action_steering[:, agent_index], 'ref': (self.ref_paths_agent_related.short_term[:, agent_index] / self.normalizers.pos_world).reshape(self.world.batch_dim, -1), 'distance_ref': self.distances.ref_paths[:, agent_index] / self.normalizers.distance_ref, 'distance_left_b': self.distances.left_boundaries[:, agent_index].min(dim=-1)[0] / self.normalizers.distance_lanelet, 'distance_right_b': self.distances.right_boundaries[:, agent_index].min(dim=-1)[0] / self.normalizers.distance_lanelet, 'is_collision_with_agents': is_collision_with_agents, 'is_collision_with_lanelets': is_collision_with_lanelets}
        return info

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        if self.parameters.is_real_time_rendering:
            if self.timer.step[0] == 0:
                pause_duration = 0
            else:
                pause_duration = self.world.dt - (time.time() - self.timer.render_begin)
            if pause_duration > 0:
                time.sleep(pause_duration)
            self.timer.render_begin = time.time()
        geoms = []
        for i in range(len(self.map_data['lanelets'])):
            lanelet = self.map_data['lanelets'][i]
            geom = rendering.PolyLine(v=lanelet['left_boundary'], close=False)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geom.set_color(*Color.BLACK.value)
            geoms.append(geom)
            geom = rendering.PolyLine(v=lanelet['right_boundary'], close=False)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geom.set_color(*Color.BLACK.value)
            geoms.append(geom)
        if self.parameters.is_visualize_extra_info:
            hight_a = -0.1
            hight_b = -0.2
            hight_c = -0.3
            geom = rendering.TextLine(text=self.parameters.render_title, x=0.05 * self.resolution_factor, y=(self.world.y_semidim + hight_a) * self.resolution_factor, font_size=14)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geoms.append(geom)
            geom = rendering.TextLine(text=f't: {self.timer.step[0] * self.parameters.dt:.2f} sec', x=0.05 * self.resolution_factor, y=(self.world.y_semidim + hight_b) * self.resolution_factor, font_size=14)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geoms.append(geom)
            geom = rendering.TextLine(text=f'n: {self.timer.step[0]}', x=0.05 * self.resolution_factor, y=(self.world.y_semidim + hight_c) * self.resolution_factor, font_size=14)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geoms.append(geom)
        for agent_i in range(self.n_agents):
            if self.parameters.is_visualize_short_term_path:
                geom = rendering.PolyLine(v=self.ref_paths_agent_related.short_term[env_index, agent_i], close=False)
                xform = rendering.Transform()
                geom.add_attr(xform)
                geom.set_color(*self.world.agents[agent_i].color)
                geoms.append(geom)
                for i_p in self.ref_paths_agent_related.short_term[env_index, agent_i]:
                    circle = rendering.make_circle(radius=0.01, filled=True)
                    xform = rendering.Transform()
                    circle.add_attr(xform)
                    xform.set_translation(i_p[0], i_p[1])
                    circle.set_color(*self.world.agents[agent_i].color)
                    geoms.append(circle)
            if not self.parameters.is_observe_distance_to_boundaries:
                geom = rendering.PolyLine(v=self.ref_paths_agent_related.nearing_points_left_boundary[env_index, agent_i], close=False)
                xform = rendering.Transform()
                geom.add_attr(xform)
                geom.set_color(*self.world.agents[agent_i].color)
                geoms.append(geom)
                for i_p in self.ref_paths_agent_related.nearing_points_left_boundary[env_index, agent_i]:
                    circle = rendering.make_circle(radius=0.01, filled=True)
                    xform = rendering.Transform()
                    circle.add_attr(xform)
                    xform.set_translation(i_p[0], i_p[1])
                    circle.set_color(*self.world.agents[agent_i].color)
                    geoms.append(circle)
                geom = rendering.PolyLine(v=self.ref_paths_agent_related.nearing_points_right_boundary[env_index, agent_i], close=False)
                xform = rendering.Transform()
                geom.add_attr(xform)
                geom.set_color(*self.world.agents[agent_i].color)
                geoms.append(geom)
                for i_p in self.ref_paths_agent_related.nearing_points_right_boundary[env_index, agent_i]:
                    circle = rendering.make_circle(radius=0.01, filled=True)
                    xform = rendering.Transform()
                    circle.add_attr(xform)
                    xform.set_translation(i_p[0], i_p[1])
                    circle.set_color(*self.world.agents[agent_i].color)
                    geoms.append(circle)
            geom = rendering.TextLine(text=f'{agent_i}', x=self.world.agents[agent_i].state.pos[env_index, 0] / self.world.x_semidim * self.viewer_size[0], y=self.world.agents[agent_i].state.pos[env_index, 1] / self.world.y_semidim * self.viewer_size[1], font_size=14)
            xform = rendering.Transform()
            geom.add_attr(xform)
            geoms.append(geom)
            if self.parameters.is_visualize_lane_boundary:
                if agent_i == 0:
                    geom = rendering.PolyLine(v=self.ref_paths_agent_related.left_boundary[env_index, agent_i], close=False)
                    xform = rendering.Transform()
                    geom.add_attr(xform)
                    geom.set_color(*self.world.agents[agent_i].color)
                    geoms.append(geom)
                    geom = rendering.PolyLine(v=self.ref_paths_agent_related.right_boundary[env_index, agent_i], close=False)
                    xform = rendering.Transform()
                    geom.add_attr(xform)
                    geom.set_color(*self.world.agents[agent_i].color)
                    geoms.append(geom)
                    geom = rendering.PolyLine(v=self.ref_paths_agent_related.entry[env_index, agent_i], close=False)
                    xform = rendering.Transform()
                    geom.add_attr(xform)
                    geom.set_color(*self.world.agents[agent_i].color)
                    geoms.append(geom)
                    geom = rendering.PolyLine(v=self.ref_paths_agent_related.exit[env_index, agent_i], close=False)
                    xform = rendering.Transform()
                    geom.add_attr(xform)
                    geom.set_color(*self.world.agents[agent_i].color)
                    geoms.append(geom)
        return geoms

def init_params(self, batch_dim, device, **kwargs):
    self.world_x_dim = kwargs.pop('world_x_dim', 4.5)
    self.world_y_dim = kwargs.pop('world_y_dim', 4.0)
    self.agent_width = kwargs.pop('agent_width', 0.08)
    self.agent_length = kwargs.pop('agent_length', 0.16)
    self.l_f = kwargs.pop('l_f', self.agent_length / 2)
    self.l_r = kwargs.pop('l_r', self.agent_length - self.l_f)
    lane_width = kwargs.pop('lane_width', 0.15)
    r_p_normalizer = 100
    reward_progress = kwargs.pop('reward_progress', 10) / r_p_normalizer
    reward_vel = kwargs.pop('reward_vel', 5) / r_p_normalizer
    reward_reach_goal = kwargs.pop('reward_reach_goal', 0) / r_p_normalizer
    threshold_deviate_from_ref_path = kwargs.pop('threshold_deviate_from_ref_path', (lane_width - self.agent_width) / 2)
    threshold_reach_goal = kwargs.pop('threshold_reach_goal', self.agent_width / 2)
    threshold_change_steering = kwargs.pop('threshold_change_steering', 10)
    threshold_near_boundary_high = kwargs.pop('threshold_near_boundary_high', (lane_width - self.agent_width) / 2 * 0.9)
    threshold_near_boundary_low = kwargs.pop('threshold_near_boundary_low', 0)
    threshold_near_other_agents_c2c_high = kwargs.pop('threshold_near_other_agents_c2c_high', self.agent_length + self.agent_width)
    threshold_near_other_agents_c2c_low = kwargs.pop('threshold_near_other_agents_c2c_low', (self.agent_length + self.agent_width) / 2)
    threshold_no_reward_if_too_close_to_boundaries = kwargs.pop('threshold_no_reward_if_too_close_to_boundaries', self.agent_width / 10)
    threshold_no_reward_if_too_close_to_other_agents = kwargs.pop('threshold_no_reward_if_too_close_to_other_agents', self.agent_width / 6)
    self.resolution_factor = kwargs.pop('resolution_factor', 200)
    sample_interval_ref_path = kwargs.pop('sample_interval_ref_path', 2)
    max_ref_path_points = kwargs.pop('max_ref_path_points', 200)
    noise_level = kwargs.pop('noise_level', 0.2 * self.agent_width)
    n_stored_steps = kwargs.pop('n_stored_steps', 5)
    n_observed_steps = kwargs.pop('n_observed_steps', 1)
    self.render_origin = kwargs.pop('render_origin', [self.world_x_dim / 2, self.world_y_dim / 2])
    self.viewer_size = kwargs.pop('viewer_size', (int(self.world_x_dim * self.resolution_factor), int(self.world_y_dim * self.resolution_factor)))
    self.max_steering_angle = kwargs.pop('max_steering_angle', torch.deg2rad(torch.tensor(35, device=device, dtype=torch.float32)))
    self.max_speed = kwargs.pop('max_speed', 1.0)
    self.viewer_zoom = kwargs.pop('viewer_zoom', 1.44)
    parameters = Parameters(n_agents=kwargs.pop('n_agents', 20), is_partial_observation=kwargs.pop('is_partial_observation', True), is_testing_mode=kwargs.pop('is_testing_mode', False), is_visualize_short_term_path=kwargs.pop('is_visualize_short_term_path', True), map_type=kwargs.pop('map_type', '1'), n_nearing_agents_observed=kwargs.pop('n_nearing_agents_observed', 2), is_real_time_rendering=kwargs.pop('is_real_time_rendering', False), n_points_short_term=kwargs.pop('n_points_short_term', 3), dt=kwargs.pop('dt', 0.05), is_ego_view=kwargs.pop('is_ego_view', True), is_apply_mask=kwargs.pop('is_apply_mask', True), is_observe_vertices=kwargs.pop('is_observe_vertices', True), is_observe_distance_to_agents=kwargs.pop('is_observe_distance_to_agents', True), is_observe_distance_to_boundaries=kwargs.pop('is_observe_distance_to_boundaries', True), is_observe_distance_to_center_line=kwargs.pop('is_observe_distance_to_center_line', True), scenario_probabilities=kwargs.pop('scenario_probabilities', [1.0, 0.0, 0.0]), is_add_noise=kwargs.pop('is_add_noise', True), is_observe_ref_path_other_agents=kwargs.pop('is_observe_ref_path_other_agents', False), is_visualize_extra_info=kwargs.pop('is_visualize_extra_info', False), render_title=kwargs.pop('render_title', 'Multi-Agent Reinforcement Learning for Road Traffic (CPM Lab Scenario)'), n_steps_stored=kwargs.pop('n_steps_stored', 10), n_steps_before_recording=kwargs.pop('n_steps_before_recording', 10), n_points_nearing_boundary=kwargs.pop('n_points_nearing_boundary', 5))
    self.parameters = kwargs.pop('parameters', parameters)
    if self.parameters.map_type == '3':
        if self.parameters.scenario_probabilities[1] != 0 or self.parameters.scenario_probabilities[2] != 0:
            if self.parameters.n_agents > 5:
                raise ValueError("For map_type '3', if the second or third value of scenario_probabilities is not zero, a maximum of 5 agents are allowed, as only a merge-in or a merge-out will be used.")
        elif self.parameters.n_agents > 10:
            raise ValueError("For map_type '3', if only the first value of scenario_probabilities is not zero, a maximum of 10 agents are allowed, as only an intersection will be used.")
    if self.parameters.n_nearing_agents_observed >= self.parameters.n_agents:
        raise ValueError('n_nearing_agents_observed must be less than n_agents')
    self.n_agents = self.parameters.n_agents
    self.timer = Timer(start=time.time(), end=0, step=torch.zeros(batch_dim, device=device, dtype=torch.int32), step_begin=time.time(), render_begin=0)
    map_file_path = kwargs.pop('map_file_path', None)
    if map_file_path is None:
        map_file_path = str(pathlib.Path(__file__).parent.parent / 'scenarios_data' / 'road_traffic' / 'road_traffic_cpm_lab.xml')
    self.map_data = get_map_data(map_file_path, device=device)
    reference_paths_all, reference_paths_intersection, reference_paths_merge_in, reference_paths_merge_out = get_reference_paths(self.map_data)
    if self.parameters.map_type in ('1', '2'):
        max_ref_path_points = max([ref_p['center_line'].shape[0] for ref_p in reference_paths_all]) + self.parameters.n_points_short_term * sample_interval_ref_path + 2
    else:
        max_ref_path_points = max([ref_p['center_line'].shape[0] for ref_p in reference_paths_intersection + reference_paths_merge_in + reference_paths_merge_out]) + self.parameters.n_points_short_term * sample_interval_ref_path + 2
    self.ref_paths_map_related = ReferencePathsMapRelated(long_term_all=reference_paths_all, long_term_intersection=reference_paths_intersection, long_term_merge_in=reference_paths_merge_in, long_term_merge_out=reference_paths_merge_out, point_extended_all=torch.zeros((len(reference_paths_all), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_intersection=torch.zeros((len(reference_paths_intersection), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_merge_in=torch.zeros((len(reference_paths_merge_in), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), point_extended_merge_out=torch.zeros((len(reference_paths_merge_out), self.parameters.n_points_short_term * sample_interval_ref_path, 2), device=device, dtype=torch.float32), sample_interval=torch.tensor(sample_interval_ref_path, device=device, dtype=torch.int32))
    idx_broadcasting_entend = torch.arange(1, self.parameters.n_points_short_term * sample_interval_ref_path + 1, device=device, dtype=torch.int32).unsqueeze(1)
    for idx, i_path in enumerate(reference_paths_all):
        center_line_i = i_path['center_line']
        direction = center_line_i[-1] - center_line_i[-2]
        self.ref_paths_map_related.point_extended_all[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
    for idx, i_path in enumerate(reference_paths_intersection):
        center_line_i = i_path['center_line']
        direction = center_line_i[-1] - center_line_i[-2]
        self.ref_paths_map_related.point_extended_intersection[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
    for idx, i_path in enumerate(reference_paths_merge_in):
        center_line_i = i_path['center_line']
        direction = center_line_i[-1] - center_line_i[-2]
        self.ref_paths_map_related.point_extended_merge_in[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
    for idx, i_path in enumerate(reference_paths_merge_out):
        center_line_i = i_path['center_line']
        direction = center_line_i[-1] - center_line_i[-2]
        self.ref_paths_map_related.point_extended_merge_out[idx, :] = center_line_i[-1] + idx_broadcasting_entend * direction
    self.ref_paths_agent_related = ReferencePathsAgentRelated(long_term=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), long_term_vec_normalized=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), left_boundary=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), right_boundary=torch.zeros((batch_dim, self.n_agents, max_ref_path_points, 2), device=device, dtype=torch.float32), entry=torch.zeros((batch_dim, self.n_agents, 2, 2), device=device, dtype=torch.float32), exit=torch.zeros((batch_dim, self.n_agents, 2, 2), device=device, dtype=torch.float32), is_loop=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), n_points_long_term=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), n_points_left_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), n_points_right_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), short_term=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32), short_term_indices=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_short_term), device=device, dtype=torch.int32), n_points_nearing_boundary=torch.tensor(self.parameters.n_points_nearing_boundary, device=device, dtype=torch.int32), nearing_points_left_boundary=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32), nearing_points_right_boundary=torch.zeros((batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32), scenario_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), path_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), point_id=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32))
    self.vertices = torch.zeros((batch_dim, self.n_agents, 5, 2), device=device, dtype=torch.float32)
    weighting_ref_directions = torch.linspace(1, 0.2, steps=self.parameters.n_points_short_term, device=device, dtype=torch.float32)
    weighting_ref_directions /= weighting_ref_directions.sum()
    self.rewards = Rewards(progress=torch.tensor(reward_progress, device=device, dtype=torch.float32), weighting_ref_directions=weighting_ref_directions, higth_v=torch.tensor(reward_vel, device=device, dtype=torch.float32), reach_goal=torch.tensor(reward_reach_goal, device=device, dtype=torch.float32))
    self.rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
    self.penalties = Penalties(deviate_from_ref_path=torch.tensor(-2 / 100, device=device, dtype=torch.float32), weighting_deviate_from_ref_path=self.map_data['mean_lane_width'] / 2, near_boundary=torch.tensor(-20 / 100, device=device, dtype=torch.float32), near_other_agents=torch.tensor(-20 / 100, device=device, dtype=torch.float32), collide_with_agents=torch.tensor(-100 / 100, device=device, dtype=torch.float32), collide_with_boundaries=torch.tensor(-100 / 100, device=device, dtype=torch.float32), change_steering=torch.tensor(-2 / 100, device=device, dtype=torch.float32), time=torch.tensor(5 / 100, device=device, dtype=torch.float32))
    self.observations = Observations(is_partial=torch.tensor(self.parameters.is_partial_observation, device=device, dtype=torch.bool), n_nearing_agents=torch.tensor(self.parameters.n_nearing_agents_observed, device=device, dtype=torch.int32), noise_level=torch.tensor(noise_level, device=device, dtype=torch.float32), n_stored_steps=torch.tensor(n_stored_steps, device=device, dtype=torch.int32), n_observed_steps=torch.tensor(n_observed_steps, device=device, dtype=torch.int32), nearing_agents_indices=torch.zeros((batch_dim, self.n_agents, self.parameters.n_nearing_agents_observed), device=device, dtype=torch.int32))
    if self.parameters.is_ego_view:
        self.observations.past_pos = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 2), device=device, dtype=torch.float32))
        self.observations.past_rot = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_vertices = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 4, 2), device=device, dtype=torch.float32))
        self.observations.past_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, 2), device=device, dtype=torch.float32))
        self.observations.past_short_term_ref_points = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32))
        self.observations.past_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
        self.observations.past_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
    else:
        self.observations.past_pos = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 2), device=device, dtype=torch.float32))
        self.observations.past_rot = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
        self.observations.past_vertices = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 4, 2), device=device, dtype=torch.float32))
        self.observations.past_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, 2), device=device, dtype=torch.float32))
        self.observations.past_short_term_ref_points = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_short_term, 2), device=device, dtype=torch.float32))
        self.observations.past_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
        self.observations.past_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.parameters.n_points_nearing_boundary, 2), device=device, dtype=torch.float32))
    self.observations.past_action_vel = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_action_steering = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_distance_to_ref_path = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_distance_to_boundaries = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_distance_to_left_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_distance_to_right_boundary = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents), device=device, dtype=torch.float32))
    self.observations.past_distance_to_agents = CircularBuffer(torch.zeros((n_stored_steps, batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.float32))
    self.normalizers = Normalizers(pos=torch.tensor([self.agent_length * 10, self.agent_length * 10], device=device, dtype=torch.float32), pos_world=torch.tensor([self.world_x_dim, self.world_y_dim], device=device, dtype=torch.float32), v=torch.tensor(self.max_speed, device=device, dtype=torch.float32), rot=torch.tensor(2 * torch.pi, device=device, dtype=torch.float32), action_steering=self.max_steering_angle, action_vel=torch.tensor(self.max_speed, device=device, dtype=torch.float32), distance_lanelet=torch.tensor(lane_width * 3, device=device, dtype=torch.float32), distance_ref=torch.tensor(lane_width * 3, device=device, dtype=torch.float32), distance_agent=torch.tensor(self.agent_length * 10, device=device, dtype=torch.float32))
    self.distances = Distances(agents=torch.zeros(batch_dim, self.n_agents, self.n_agents, device=device, dtype=torch.float32), left_boundaries=torch.zeros((batch_dim, self.n_agents, 1 + 4), device=device, dtype=torch.float32), right_boundaries=torch.zeros((batch_dim, self.n_agents, 1 + 4), device=device, dtype=torch.float32), boundaries=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), ref_paths=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), closest_point_on_ref_path=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), closest_point_on_left_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32), closest_point_on_right_b=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.int32))
    self.thresholds = Thresholds(reach_goal=torch.tensor(threshold_reach_goal, device=device, dtype=torch.float32), deviate_from_ref_path=torch.tensor(threshold_deviate_from_ref_path, device=device, dtype=torch.float32), near_boundary_low=torch.tensor(threshold_near_boundary_low, device=device, dtype=torch.float32), near_boundary_high=torch.tensor(threshold_near_boundary_high, device=device, dtype=torch.float32), near_other_agents_low=torch.tensor(threshold_near_other_agents_c2c_low, device=device, dtype=torch.float32), near_other_agents_high=torch.tensor(threshold_near_other_agents_c2c_high, device=device, dtype=torch.float32), change_steering=torch.tensor(threshold_change_steering, device=device, dtype=torch.float32).deg2rad(), no_reward_if_too_close_to_boundaries=torch.tensor(threshold_no_reward_if_too_close_to_boundaries, device=device, dtype=torch.float32), no_reward_if_too_close_to_other_agents=torch.tensor(threshold_no_reward_if_too_close_to_other_agents, device=device, dtype=torch.float32), distance_mask_agents=self.normalizers.pos[0])
    self.constants = Constants(env_idx_broadcasting=torch.arange(batch_dim, device=device, dtype=torch.int32).unsqueeze(-1), empty_action_vel=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), empty_action_steering=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.float32), mask_pos=torch.tensor(1, device=device, dtype=torch.float32), mask_zero=torch.tensor(0, device=device, dtype=torch.float32), mask_one=torch.tensor(1, device=device, dtype=torch.float32), reset_agent_min_distance=torch.tensor((self.l_f + self.l_r) ** 2 + self.agent_width ** 2, device=device, dtype=torch.float32).sqrt() * 1.2)
    self.collisions = Collisions(with_agents=torch.zeros((batch_dim, self.n_agents, self.n_agents), device=device, dtype=torch.bool), with_lanelets=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), with_entry_segments=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool), with_exit_segments=torch.zeros((batch_dim, self.n_agents), device=device, dtype=torch.bool))
    self.initial_state_buffer = InitialStateBuffer(probability_record=torch.tensor(1.0, device=device, dtype=torch.float32), probability_use_recording=torch.tensor(kwargs.pop('probability_use_recording', 0.2), device=device, dtype=torch.float32), buffer=torch.zeros((100, self.n_agents, 8), device=device, dtype=torch.float32))
    ScenarioUtils.check_kwargs_consumed(kwargs)
    self.state_buffer = StateBuffer(buffer=torch.zeros((self.parameters.n_steps_before_recording, batch_dim, self.n_agents, 8), device=device, dtype=torch.float32))

class AgentPolicy:

    def __init__(self, team: str, speed_strength=1.0, decision_strength=1.0, precision_strength=1.0, disabled: bool=False):
        self.team_name = team
        self.otherteam_name = 'Blue' if self.team_name == 'Red' else 'Red'
        self.speed_strength = speed_strength ** 2
        self.decision_strength = decision_strength
        self.precision_strength = precision_strength
        self.strength_multiplier = 25.0
        self.pos_lookahead = 0.01
        self.vel_lookahead = 0.01
        self.possession_lookahead = 0.5
        self.dribble_speed = 0.16 + 0.16 * speed_strength
        self.shooting_radius = 0.08
        self.shooting_angle = torch.pi / 2
        self.take_shot_angle = torch.pi / 4
        self.max_shot_dist = 0.5
        self.nsamples = 2
        self.sigma = 0.5
        self.replan_margin = 0.0
        self.initialised = False
        self.disabled = disabled

    def init(self, world):
        self.initialised = True
        self.world = world
        self.ball = self.world.ball
        if self.team_name == 'Red':
            self.teammates = self.world.red_agents
            self.opposition = self.world.blue_agents
            self.own_net = self.world.red_net
            self.target_net = self.world.blue_net
        elif self.team_name == 'Blue':
            self.teammates = self.world.blue_agents
            self.opposition = self.world.red_agents
            self.own_net = self.world.blue_net
            self.target_net = self.world.red_net
        self.team_color = self.teammates[0].color if len(self.teammates) > 0 else None
        self.enable_shooting = self.teammates[0].action_size == 4 if len(self.teammates) > 0 else False
        self.objectives = {agent: {'shot_power': torch.zeros(self.world.batch_dim, device=world.device), 'target_ang': torch.zeros(self.world.batch_dim, device=world.device), 'target_pos_rel': torch.zeros(self.world.batch_dim, self.world.dim_p, device=world.device), 'target_pos': torch.zeros(self.world.batch_dim, self.world.dim_p, device=world.device), 'target_vel': torch.zeros(self.world.batch_dim, self.world.dim_p, device=world.device), 'start_pos': torch.zeros(self.world.batch_dim, self.world.dim_p, device=world.device), 'start_vel': torch.zeros(self.world.batch_dim, self.world.dim_p, device=world.device)} for agent in self.teammates}
        self.agent_possession = {agent: torch.zeros(self.world.batch_dim, device=world.device, dtype=torch.bool) for agent in self.teammates}
        self.team_possession = torch.zeros(self.world.batch_dim, device=world.device, dtype=torch.bool)
        self.team_disps = {}

    def reset(self, env_index=Ellipsis):
        self.team_disps = {}
        for agent in self.teammates:
            self.objectives[agent]['shot_power'][env_index] = 0
            self.objectives[agent]['target_ang'][env_index] = 0
            self.objectives[agent]['target_pos_rel'][env_index] = torch.zeros(self.world.dim_p, device=self.world.device)
            self.objectives[agent]['target_pos'][env_index] = torch.zeros(self.world.dim_p, device=self.world.device)
            self.objectives[agent]['target_vel'][env_index] = torch.zeros(self.world.dim_p, device=self.world.device)
            self.objectives[agent]['start_pos'][env_index] = torch.zeros(self.world.dim_p, device=self.world.device)
            self.objectives[agent]['start_vel'][env_index] = torch.zeros(self.world.dim_p, device=self.world.device)

    def dribble_policy(self, agent):
        possession_mask = self.agent_possession[agent]
        self.dribble_to_goal(agent, env_index=possession_mask)
        move_mask = ~possession_mask
        best_pos = self.check_better_positions(agent, env_index=move_mask)
        self.go_to(agent, pos=best_pos, aggression=1.0, env_index=move_mask)

    def passing_policy(self, agent):
        possession_mask = self.agent_possession[agent]
        otheragent = None
        for a in self.teammates:
            if a != agent:
                otheragent = a
                break
        self.shoot(agent, otheragent.state.pos, env_index=possession_mask)
        move_mask = ~possession_mask
        best_pos = self.check_better_positions(agent, env_index=move_mask)
        self.go_to(agent, pos=best_pos, aggression=1.0, env_index=move_mask)

    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False

    def run(self, agent, world):
        if not self.disabled:
            if '0' in agent.name:
                self.team_disps = {}
                self.check_possession()
            self.dribble_policy(agent)
            control = self.get_action(agent)
            control = torch.clamp(control, min=-agent.u_range, max=agent.u_range)
            agent.action.u = control * agent.action.u_multiplier_tensor.unsqueeze(0).expand(*control.shape)
        else:
            agent.action.u = torch.zeros(self.world.batch_dim, agent.action_size, device=self.world.device, dtype=torch.float)

    def dribble_to_goal(self, agent, env_index=Ellipsis):
        self.dribble(agent, self.target_net.state.pos[env_index], env_index=env_index)

    def dribble(self, agent, pos, env_index=Ellipsis):
        self.update_dribble(agent, pos=pos, env_index=env_index)

    def update_dribble(self, agent, pos, env_index=Ellipsis):
        agent_pos = agent.state.pos[env_index]
        ball_pos = self.ball.state.pos[env_index]
        ball_disp = pos - ball_pos
        ball_dist = ball_disp.norm(dim=-1)
        direction = ball_disp / ball_dist[:, None]
        hit_vel = direction * self.dribble_speed
        start_vel = self.get_start_vel(ball_pos, hit_vel, agent_pos, aggression=0.0)
        start_vel_mag = start_vel.norm(dim=-1)
        offset = start_vel.clone()
        start_vel_mag_mask = start_vel_mag > 0
        offset[start_vel_mag_mask] /= start_vel_mag.unsqueeze(-1)[start_vel_mag_mask]
        new_direction = direction + 0.5 * offset
        new_direction /= new_direction.norm(dim=-1)[:, None]
        hit_pos = ball_pos - new_direction * (self.ball.shape.radius + agent.shape.radius) * 0.7
        self.go_to(agent, hit_pos, hit_vel, start_vel=start_vel, env_index=env_index)

    def shoot(self, agent, pos, env_index=Ellipsis):
        agent_pos = agent.state.pos
        ball_disp = self.ball.state.pos - agent_pos
        ball_dist = ball_disp.norm(dim=-1)
        within_range_mask = ball_dist <= self.shooting_radius
        target_disp = pos - agent_pos
        target_dist = target_disp.norm(dim=-1)
        ball_rel_angle = self.get_rel_ang(ang1=agent.state.rot, vec2=ball_disp)
        target_rel_angle = self.get_rel_ang(ang1=agent.state.rot, vec2=target_disp)
        ball_within_angle_mask = torch.abs(ball_rel_angle) < self.shooting_angle / 2
        rot_within_angle_mask = torch.abs(target_rel_angle) < self.take_shot_angle / 2
        shooting_mask = within_range_mask & ball_within_angle_mask & rot_within_angle_mask
        self.objectives[agent]['target_ang'][env_index] = torch.atan2(target_disp[:, 1], target_disp[:, 0])[env_index]
        self.dribble(agent, pos, env_index=env_index)
        self.objectives[agent]['shot_power'][:] = -1
        self.objectives[agent]['shot_power'][self.combine_mask(shooting_mask, env_index)] = torch.minimum(target_dist[shooting_mask] / self.max_shot_dist, torch.tensor(1.0))

    def combine_mask(self, mask, env_index):
        if env_index == Ellipsis:
            return mask
        elif env_index.shape[0] == self.world.batch_dim and env_index.dtype == torch.bool:
            return mask & env_index
        raise ValueError('Expected env_index to be : or boolean tensor')

    def go_to(self, agent, pos, vel=None, start_vel=None, aggression=1.0, env_index=Ellipsis):
        start_pos = agent.state.pos[env_index]
        if vel is None:
            vel = torch.zeros_like(pos)
        if start_vel is None:
            aggression = ((pos - start_pos).norm(dim=-1) > 0.1).float() * aggression
            start_vel = self.get_start_vel(pos, vel, start_pos, aggression=aggression)
        diff = (self.objectives[agent]['target_pos'][env_index] - pos).norm(dim=-1).unsqueeze(-1)
        if self.precision_strength != 1:
            exp_diff = torch.exp(-diff)
            pos += torch.randn(pos.shape, device=pos.device) * 10 * (1 - self.precision_strength) * (1 - exp_diff)
            vel += torch.randn(pos.shape, device=vel.device) * 10 * (1 - self.precision_strength) * (1 - exp_diff)
        self.objectives[agent]['target_pos_rel'][env_index] = pos - self.ball.state.pos[env_index]
        self.objectives[agent]['target_pos'][env_index] = pos
        self.objectives[agent]['target_vel'][env_index] = vel
        self.objectives[agent]['start_pos'][env_index] = start_pos
        self.objectives[agent]['start_vel'][env_index] = start_vel
        self.plot_traj(agent, env_index=env_index)

    def get_start_vel(self, pos, vel, start_pos, aggression=0.0):
        vel_mag = 1.0 * aggression + vel.norm(dim=-1) * (1 - aggression)
        goal_disp = pos - start_pos
        goal_dist = goal_disp.norm(dim=-1)
        vel_dir = vel.clone()
        vel_mag_great_0 = vel_mag > 0
        vel_dir[vel_mag_great_0] /= vel_mag[vel_mag_great_0, None]
        dist_behind_target = 0.6 * goal_dist
        target_pos = pos - vel_dir * dist_behind_target[:, None]
        target_disp = target_pos - start_pos
        target_dist = target_disp.norm(dim=1)
        start_vel_aug_dir = target_disp
        target_dist_great_0 = target_dist > 0
        start_vel_aug_dir[target_dist_great_0] /= target_dist[target_dist_great_0, None]
        start_vel = start_vel_aug_dir * vel_mag[:, None]
        return start_vel

    def get_action(self, agent, env_index=Ellipsis):
        curr_pos = agent.state.pos[env_index, :]
        curr_vel = agent.state.vel[env_index, :]
        des_curr_pos = Splines.hermite(self.objectives[agent]['start_pos'][env_index, :], self.objectives[agent]['target_pos'][env_index, :], self.objectives[agent]['start_vel'][env_index, :], self.objectives[agent]['target_vel'][env_index, :], u=min(self.pos_lookahead, 1), deriv=0)
        des_curr_vel = Splines.hermite(self.objectives[agent]['start_pos'][env_index, :], self.objectives[agent]['target_pos'][env_index, :], self.objectives[agent]['start_vel'][env_index, :], self.objectives[agent]['target_vel'][env_index, :], u=min(self.vel_lookahead, 1), deriv=1)
        des_curr_pos = torch.as_tensor(des_curr_pos, device=self.world.device)
        des_curr_vel = torch.as_tensor(des_curr_vel, device=self.world.device)
        movement_control = 0.5 * (des_curr_pos - curr_pos) + 0.5 * (des_curr_vel - curr_vel)
        movement_control *= self.speed_strength * self.strength_multiplier
        if agent.action_size == 2:
            return movement_control
        shooting_control = torch.zeros_like(movement_control)
        shooting_control[:, 1] = self.objectives[agent]['shot_power']
        rel_ang = self.get_rel_ang(ang1=self.objectives[agent]['target_ang'], ang2=agent.state.rot).squeeze(-1)
        shooting_control[:, 0] = torch.sin(rel_ang)
        shooting_control[rel_ang > torch.pi / 2, 0] = 1
        shooting_control[rel_ang < -torch.pi / 2, 0] = -1
        control = torch.cat([movement_control, shooting_control], dim=-1)
        return control

    def get_rel_ang(self, vec1=None, vec2=None, ang1=None, ang2=None):
        if vec1 is not None:
            ang1 = torch.atan2(vec1[:, 1], vec1[:, 0])
        if vec2 is not None:
            ang2 = torch.atan2(vec2[:, 1], vec2[:, 0])
        if ang1.dim() == 2:
            ang1 = ang1.squeeze(-1)
        if ang2.dim() == 2:
            ang2 = ang2.squeeze(-1)
        return (ang1 - ang2 + torch.pi) % (2 * torch.pi) - torch.pi

    def plot_traj(self, agent, env_index=0):
        for i, u in enumerate(torch.linspace(0, 1, len(self.world.traj_points[self.team_name][agent]))):
            pointi = self.world.traj_points[self.team_name][agent][i]
            posi = Splines.hermite(self.objectives[agent]['start_pos'][env_index, :], self.objectives[agent]['target_pos'][env_index, :], self.objectives[agent]['start_vel'][env_index, :], self.objectives[agent]['target_vel'][env_index, :], u=float(u), deriv=0)
            if env_index == Ellipsis or (isinstance(env_index, torch.Tensor) and env_index.dtype == torch.bool and torch.all(env_index)):
                pointi.set_pos(torch.as_tensor(posi, device=self.world.device), batch_index=None)
            elif isinstance(env_index, int):
                pointi.set_pos(torch.as_tensor(posi, device=self.world.device), batch_index=env_index)
            elif isinstance(env_index, list):
                for envi in env_index:
                    pointi.set_pos(torch.as_tensor(posi, device=self.world.device)[envi, :], batch_index=env_index[envi])
            elif isinstance(env_index, torch.Tensor) and env_index.dtype == torch.bool and torch.any(env_index):
                envs = torch.where(env_index)
                for i, envi in enumerate(envs):
                    pointi.set_pos(torch.as_tensor(posi, device=self.world.device)[i, :], batch_index=envi[0])

    def clamp_pos(self, pos, return_bool=False):
        orig_pos = pos.clone()
        agent_size = self.world.agent_size
        pitch_y = self.world.pitch_width / 2 - agent_size
        pitch_x = self.world.pitch_length / 2 - agent_size
        goal_y = self.world.goal_size / 2 - agent_size
        goal_x = self.world.goal_depth
        pos[:, Y] = torch.clamp(pos[:, Y], -pitch_y, pitch_y)
        inside_goal_y_mask = torch.abs(pos[:, Y]) < goal_y
        pos[~inside_goal_y_mask, X] = torch.clamp(pos[~inside_goal_y_mask, X], -pitch_x, pitch_x)
        pos[inside_goal_y_mask, X] = torch.clamp(pos[inside_goal_y_mask, X], -pitch_x - goal_x, pitch_x + goal_x)
        if return_bool:
            return torch.any(pos != orig_pos, dim=-1)
        else:
            return pos

    def check_possession(self):
        agents_pos = torch.stack([agent.state.pos for agent in self.teammates + self.opposition], dim=1)
        agents_vel = torch.stack([agent.state.vel for agent in self.teammates + self.opposition], dim=1)
        ball_pos = self.ball.state.pos
        ball_vel = self.ball.state.vel
        ball_disps = ball_pos[:, None, :] - agents_pos
        relvels = ball_vel[:, None, :] - agents_vel
        dists = (ball_disps + relvels * self.possession_lookahead).norm(dim=-1)
        mindist_team = torch.argmin(dists, dim=-1) < len(self.teammates)
        self.team_possession = mindist_team
        net_disps = self.target_net.state.pos[:, None, :] - agents_pos
        ball_dir = ball_disps / ball_disps.norm(dim=-1, keepdim=True)
        net_dir = net_disps / net_disps.norm(dim=-1, keepdim=True)
        side_dot_prod = (ball_dir * net_dir).sum(dim=-1)
        dists -= 0.5 * side_dot_prod * self.decision_strength
        if self.decision_strength != 1:
            dists += 0.5 * torch.randn(dists.shape, device=dists.device) * (1 - self.decision_strength) ** 2
        mindist_agents = torch.argmin(dists[:, :len(self.teammates)], dim=-1)
        for i, agent in enumerate(self.teammates):
            self.agent_possession[agent] = mindist_agents == i

    def check_better_positions(self, agent, env_index=Ellipsis):
        ball_pos = self.ball.state.pos[env_index]
        curr_target = self.objectives[agent]['target_pos_rel'][env_index] + ball_pos
        samples = torch.randn(ball_pos.shape[0], self.nsamples, self.world.dim_p, device=self.world.device) * self.sigma * (1 + 3 * (1 - self.decision_strength))
        samples[:, ::2] += ball_pos[:, None]
        samples[:, 1::2] += agent.state.pos[env_index, None]
        test_pos = torch.cat([curr_target[:, None, :], samples], dim=1)
        test_pos_shape = test_pos.shape
        test_pos = self.clamp_pos(test_pos.view(test_pos_shape[0] * test_pos_shape[1], test_pos_shape[2])).view(*test_pos_shape)
        values = self.get_pos_value(test_pos, agent=agent, env_index=env_index)
        values[:, 0] += self.replan_margin + 3 * (1 - self.decision_strength)
        highest_value = values.argmax(dim=1)
        best_pos = torch.gather(test_pos, dim=1, index=highest_value.unsqueeze(0).unsqueeze(-1).expand(-1, -1, self.world.dim_p))
        return best_pos[0]

    def get_pos_value(self, pos, agent, env_index=Ellipsis):
        ball_pos = self.ball.state.pos[env_index, None]
        target_net_pos = self.target_net.state.pos[env_index, None]
        own_net_pos = self.own_net.state.pos[env_index, None]
        ball_vec = ball_pos - pos
        ball_vec /= ball_vec.norm(dim=-1, keepdim=True)
        ball_vec[ball_vec.isnan()] = 0
        ball_dist = (pos - ball_pos).norm(dim=-1)
        ball_dist_value = torch.exp(-2 * ball_dist ** 4)
        net_vec = target_net_pos - pos
        net_vec /= net_vec.norm(dim=-1, keepdim=True)
        side_dot_prod = (ball_vec * net_vec).sum(dim=-1)
        side_value = torch.minimum(side_dot_prod + 1.25, torch.tensor(1, device=side_dot_prod.device))
        own_net_vec = own_net_pos - pos
        own_net_vec /= net_vec.norm(dim=-1, keepdim=True)
        defend_dot_prod = (ball_vec * -own_net_vec).sum(dim=-1)
        defend_value = torch.maximum(defend_dot_prod, torch.tensor(0, device=side_dot_prod.device))
        if len(self.teammates) > 1:
            agent_index = self.teammates.index(agent)
            team_disps = self.get_separations(teammate=True)
            team_disps = torch.cat([team_disps[:, 0:agent_index], team_disps[:, agent_index + 1:]], dim=1)
            team_dists = (team_disps[env_index, None] - pos[:, :, None]).norm(dim=-1)
            other_agent_value = -torch.exp(-5 * team_dists).norm(dim=-1) + 1
        else:
            other_agent_value = 0
        wall_disps = self.get_wall_separations(pos)
        wall_dists = wall_disps.norm(dim=-1)
        wall_value = -torch.exp(-8 * wall_dists).norm(dim=-1) + 1
        value = (wall_value + other_agent_value + ball_dist_value + side_value + defend_value) / 5
        if self.decision_strength != 1:
            value += torch.randn(value.shape, device=value.device) * (1 - self.decision_strength)
        return value

    def get_wall_separations(self, pos):
        top_wall_dist = -pos[..., Y] + self.world.pitch_width / 2
        bottom_wall_dist = pos[..., Y] + self.world.pitch_width / 2
        left_wall_dist = pos[..., X] + self.world.pitch_length / 2
        right_wall_dist = -pos[..., X] + self.world.pitch_length / 2
        vertical_wall_disp = torch.zeros(pos.shape, device=self.world.device)
        vertical_wall_disp[..., Y] = torch.minimum(top_wall_dist, bottom_wall_dist)
        horizontal_wall_disp = torch.zeros(pos.shape, device=self.world.device)
        horizontal_wall_disp[..., X] = torch.minimum(left_wall_dist, right_wall_dist)
        shape = vertical_wall_disp.shape
        vertical_wall_disp = vertical_wall_disp.view(shape[0] * shape[1], 2)
        mask = (bottom_wall_dist < top_wall_dist).view(shape[0] * shape[1])
        vertical_wall_disp[mask, Y] *= -1
        vertical_wall_disp = vertical_wall_disp.view(*shape)
        shape = horizontal_wall_disp.shape
        horizontal_wall_disp = horizontal_wall_disp.view(shape[0] * shape[1], 2)
        mask = (left_wall_dist < right_wall_dist).view(shape[0] * shape[1])
        horizontal_wall_disp[mask, X] *= -1
        horizontal_wall_disp = horizontal_wall_disp.view(*shape)
        return torch.stack([vertical_wall_disp, horizontal_wall_disp], dim=-2)

    def get_separations(self, teammate=False, opposition=False, vel=False):
        assert teammate or opposition, 'One of teammate or opposition must be True'
        key = (teammate, opposition, vel)
        if key in self.team_disps:
            return self.team_disps[key]
        disps = []
        if teammate:
            for otheragent in self.teammates:
                if vel:
                    agent_disp = otheragent.state.vel
                else:
                    agent_disp = otheragent.state.pos
                disps.append(agent_disp)
        if opposition:
            for otheragent in self.opposition:
                if vel:
                    agent_disp = otheragent.state.vel
                else:
                    agent_disp = otheragent.state.pos
                disps.append(agent_disp)
        out = torch.stack(disps, dim=1)
        self.team_disps[key] = out
        return out

def check_better_positions(self, agent, env_index=Ellipsis):
    ball_pos = self.ball.state.pos[env_index]
    curr_target = self.objectives[agent]['target_pos_rel'][env_index] + ball_pos
    samples = torch.randn(ball_pos.shape[0], self.nsamples, self.world.dim_p, device=self.world.device) * self.sigma * (1 + 3 * (1 - self.decision_strength))
    samples[:, ::2] += ball_pos[:, None]
    samples[:, 1::2] += agent.state.pos[env_index, None]
    test_pos = torch.cat([curr_target[:, None, :], samples], dim=1)
    test_pos_shape = test_pos.shape
    test_pos = self.clamp_pos(test_pos.view(test_pos_shape[0] * test_pos_shape[1], test_pos_shape[2])).view(*test_pos_shape)
    values = self.get_pos_value(test_pos, agent=agent, env_index=env_index)
    values[:, 0] += self.replan_margin + 3 * (1 - self.decision_strength)
    highest_value = values.argmax(dim=1)
    best_pos = torch.gather(test_pos, dim=1, index=highest_value.unsqueeze(0).unsqueeze(-1).expand(-1, -1, self.world.dim_p))
    return best_pos[0]

class BaseScenario(ABC):
    """Base class for scenarios.

    This is the class that scenarios inherit from.

    The methods that are **compulsory to instantiate** are:

    - :class:`make_world`
    - :class:`reset_world_at`
    - :class:`observation`
    - :class:`reward`

    The methods that are **optional to instantiate** are:

    - :class:`info`
    - :class:`extra_render`
    - :class:`process_action`
    - :class:`pre_step`
    - :class:`post_step`

    """

    def __init__(self):
        """Do not override."""
        self._world = None
        self.viewer_size = INITIAL_VIEWER_SIZE
        'The size of the rendering viewer window. This can be changed in the :class:`~make_world` function. '
        self.viewer_zoom = VIEWER_DEFAULT_ZOOM
        'The zoom of the rendering camera (a lower value means more zoom). This can be changed in the :class:`~make_world` function. '
        self.render_origin = (0.0, 0.0)
        'The origin of the rendering camera when ``agent_index_to_focus`` is None in the ``render()`` arguments. This can be changed in the :class:`~make_world` function. '
        self.plot_grid = False
        'Whether to plot a grid in the scenario rendering background. This can be changed in the :class:`~make_world` function. '
        self.grid_spacing = 0.1
        'If :class:`~plot_grid`, the distance between lines in the background grid. This can be changed in the :class:`~make_world` function. '
        self.visualize_semidims = True
        'Whether to display boundaries in dimension-limited environment. This can be changed in the :class:`~make_world` function. '

    @property
    def world(self):
        """The :class:`~vmas.simulator.core.World` associated toi this scenario."""
        assert self._world is not None, 'You first need to set `self._world` in the `make_world` method'
        return self._world

    def to(self, device: torch.device):
        """Casts the scenario to a different device.

        Args:
            device (Union[str, int, torch.device]): the device to cast to
        """
        for attr, value in self.__dict__.items():
            if isinstance(value, Tensor):
                self.__dict__[attr] = value.to(device)
        self.world.to(device)

    def env_make_world(self, batch_dim: int, device: torch.device, **kwargs) -> World:
        self._world = self.make_world(batch_dim, device, **kwargs)
        return self._world

    def env_reset_world_at(self, env_index: typing.Optional[int]):
        self.world.reset(env_index)
        self.reset_world_at(env_index)

    def env_process_action(self, agent: Agent):
        if agent.action_script is not None:
            agent.action_callback(self.world)
        self.process_action(agent)
        agent.dynamics.check_and_process_action()

    @abstractmethod
    def make_world(self, batch_dim: int, device: torch.device, **kwargs) -> World:
        """
        This function needs to be implemented when creating a scenario.
        In this function the user should instantiate the world and insert agents and landmarks in it.

        Args:
            batch_dim (int): the number of vecotrized environments.
            device (Union[str, int, torch.device], optional): the device of the environmemnt.
            kwargs (dict, optional): named arguments passed from environment creation

        Returns:
            :class:`~vmas.simulator.core.World` : the :class:`~vmas.simulator.core.World`
            instance which is automatically set in :class:`~world`.

        Examples:
            >>> from vmas.simulator.core import Agent, World, Landmark, Sphere, Box
            >>> from vmas.simulator.scenario import BaseScenario
            >>> from vmas.simulator.utils import Color
            >>> class Scenario(BaseScenario):
            >>>     def make_world(self, batch_dim: int, device: torch.device, **kwargs):
            ...         # Pass any kwargs you desire when creating the environment
            ...         n_agents = kwargs.get("n_agents", 5)
            ...
            ...         # Create world
            ...         world = World(batch_dim, device, dt=0.1, drag=0.25, dim_c=0)
            ...         # Add agents
            ...         for i in range(n_agents):
            ...             agent = Agent(
            ...                 name=f"agent {i}",
            ...                 collide=True,
            ...                 mass=1.0,
            ...                 shape=Sphere(radius=0.04),
            ...                 max_speed=None,
            ...                 color=Color.BLUE,
            ...                 u_range=1.0,
            ...             )
            ...             world.add_agent(agent)
            ...         # Add landmarks
            ...         for i in range(5):
            ...             landmark = Landmark(
            ...                 name=f"landmark {i}",
            ...                 collide=True,
            ...                 movable=False,
            ...                 shape=Box(length=0.3,width=0.1),
            ...                 color=Color.RED,
            ...             )
            ...             world.add_landmark(landmark)
            ...         return world
        """
        raise NotImplementedError()

    @abstractmethod
    def reset_world_at(self, env_index: Optional[int]=None):
        """Resets the world at the specified env_index.

        When a ``None`` index is passed, the world should make a vectorized (batched) reset.
        The ``entity.set_x()`` methods already have this logic integrated and will perform
        batched operations when index is ``None``.

        When this function is called, all entities have already had their state reset to zeros according to the ``env_index``.
        In this function you shoud change the values of the reset states according to your task.
        For example, some functions you might want to use are:

        - ``entity.set_pos()``,
        - ``entity.set_vel()``,
        - ``entity.set_rot()``,
        - ``entity.set_ang_vel()``.

        Implementors can access the world at :class:`world`.

        To increase performance, torch tensors should be created with the device already set, like:
        ``torch.tensor(..., device=self.world.device)``

        Args:
            env_index (int, otpional): index of the environment to reset. If ``None`` a vectorized reset should be performed.

        Spawning at fixed positions

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> import torch
            >>> class Scenario(BaseScenario):
            >>>     def reset_world_at(self, env_index)
            ...        for i, agent in enumerate(self.world.agents):
            ...            agent.set_pos(
            ...                torch.tensor(
            ...                     [-0.2 + 0.1 * i, 1.0],
            ...                     dtype=torch.float32,
            ...                     device=self.world.device,
            ...                ),
            ...                 batch_index=env_index,
            ...            )
            ...        for i, landmark in enumerate(self.world.landmarks):
            ...            landmark.set_pos(
            ...                torch.tensor(
            ...                     [0.2 if i % 2 else -0.2, 0.6 - 0.3 * i],
            ...                     dtype=torch.float32,
            ...                     device=self.world.device,
            ...                ),
            ...                 batch_index=env_index,
            ...            )
            ...            landmark.set_rot(
            ...                torch.tensor(
            ...                     [torch.pi / 4 if i % 2 else -torch.pi / 4],
            ...                     dtype=torch.float32,
            ...                     device=self.world.device,
            ...                ),
            ...                 batch_index=env_index,
            ...            )

        Spawning at random positions

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> from vmas.simulator.utils import ScenarioUtils
            >>> class Scenario(BaseScenario):
            >>>     def reset_world_at(self, env_index)
            >>>         ScenarioUtils.spawn_entities_randomly(
            ...             self.world.agents + self.world.landmarks,
            ...             self.world,
            ...             env_index,
            ...             min_dist_between_entities=0.02,
            ...             x_bounds=(-1.0,1.0),
            ...             y_bounds=(-1.0,1.0),
            ...         )

        """
        raise NotImplementedError()

    @abstractmethod
    def observation(self, agent: Agent) -> AGENT_OBS_TYPE:
        """This function computes the observations for ``agent`` in a vectorized way.

        The returned tensor should contain the observations for ``agent`` in all envs and should have
        shape ``(self.world.batch_dim, n_agent_obs)``, or be a dict with leaves following that shape.

        Implementors can access the world at :class:`world`.

        To increase performance, torch tensors should be created with the device already set, like:
        ``torch.tensor(..., device=self.world.device)``

        Args:
            agent (Agent): the agent to compute the observations for

        Returns:
             Union[torch.Tensor, Dict[str, torch.Tensor]]: the observation

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> import torch
            >>> class Scenario(BaseScenario):
            >>>     def observation(self, agent):
            ...         # get positions of all landmarks in this agent's reference frame
            ...         landmark_rel_poses = []
            ...         for landmark in self.world.landmarks:
            ...             landmark_rel_poses.append(landmark.state.pos - agent.state.pos)
            ...         return torch.cat([agent.state.pos, agent.state.vel, *landmark_rel_poses], dim=-1)

        You can also return observations in a dictionary

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> from vmas.simulator.utils import Color
            >>> class Scenario(BaseScenario):
            >>>     def observation(self, agent):
            ...         return {"pos": agent.state.pos, "vel": agent.state.vel}

        """
        raise NotImplementedError()

    @abstractmethod
    def reward(self, agent: Agent) -> AGENT_REWARD_TYPE:
        """This function computes the reward for ``agent`` in a vectorized way.

        The returned tensor should contain the reward for ``agent`` in all envs and should have
        shape ``(self.world.batch_dim)`` and dtype ``torch.float``.

        Implementors can access the world at :class:`world`.

        To increase performance, torch tensors should be created with the device already set, like:
        ``torch.tensor(..., device=self.world.device)``

        Args:
            agent (Agent): the agent to compute the reward for

        Returns:
             torch.Tensor: reward tensor of shape ``(self.world.batch_dim)``

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> import torch
            >>> class Scenario(BaseScenario):
            >>>     def reward(self, agent):
            ...         # reward every agent proportionally to distance from first landmark
            ...         rew = -torch.linalg.vector_norm(agent.state.pos - self.world.landmarks[0].state.pos, dim=-1)
            ...         return rew
        """
        raise NotImplementedError()

    def done(self) -> Tensor:
        """This function computes the done flag for each env in a vectorized way.

        The returned tensor should contain the ``done`` for all envs and should have
        shape ``(n_envs)`` and dtype ``torch.bool``.

        Implementors can access the world at :class:`world`.

        To increase performance, torch tensors should be created with the device already set, like:
        ``torch.tensor(..., device=self.world.device)``

        By default, this function returns all ``False`` s.

        The scenario can still be done if ``max_steps`` has been set at envirtonment construction.

        Returns:
            torch.Tensor: done tensor of shape ``(self.world.batch_dim)``

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> import torch
            >>> class Scenario(BaseScenario):
            >>>     def done(self):
            ...         # retrun done when all agents have battery level lower than a threshold
            ...         return torch.stack([a.battery_level < threshold for a in self.world.agents], dim=-1).all(-1)
        """
        return torch.tensor([False], device=self.world.device).expand(self.world.batch_dim)

    def info(self, agent: Agent) -> AGENT_INFO_TYPE:
        """This function computes the info dict for ``agent`` in a vectorized way.

        The returned dict should have a key for each info of interest and the corresponding value should
        be a tensor of shape ``(n_envs, info_size)``

        By default this function returns an empty dictionary.

        Implementors can access the world at :class:`world`.

        To increase performance, torch tensors should be created with the device already set, like:
        ``torch.tensor(..., device=self.world.device)``

        Args:
            agent (Agent): the agent to compute the info for

        Returns:
             Union[torch.Tensor, Dict[str, torch.Tensor]]: the info
        """
        return {}

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        """
        This function facilitates additional user/scenario-level rendering for a specific environment index.

        The returned list is a list of geometries. It is the user's responsibility to set attributes such as color,
        position and rotation.

        Args:
            env_index (int, optional): index of the environment to render. Defaults to ``0``.

        Returns: A list of geometries to render for the current time step.

        Examples:
            >>> from vmas.simulator.utils import Color
            >>> from vmas.simulator.scenario import BaseScenario
            >>> class Scenario(BaseScenario):
            >>>     def extra_render(self, env_index):
            >>>         from vmas.simulator import rendering
            >>>         color = Color.BLACK.value
            >>>         line = rendering.Line(
            ...            (self.world.agents[0].state.pos[env_index]),
            ...            (self.world.agents[1].state.pos[env_index]),
            ...            width=1,
            ...         )
            >>>         xform = rendering.Transform()
            >>>         line.add_attr(xform)
            >>>         line.set_color(*color)
            >>>         return [line]
        """
        return []

    def process_action(self, agent: Agent):
        """This function can be overridden to process the agent actions before the simulation step.

        It has access to the world through the :class:`world` attribute

        For example here you can manage additional actions before passing them to the dynamics.

        Args:
            agent (Agent): the agent process the action of

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> from vmas.simulator.utils import TorchUtils
            >>> class Scenario(BaseScenario):
            >>>     def process_action(self, agent):
            >>>         # Clamp square to circle
            >>>         agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, agent.u_range)
            >>>         # Can use a PID controller to turn velocity actions into forces
            >>>         # (e.g., from vmas.simulator.controllers.velocity_controller)
            >>>         agent.controller.process_force()
            >>>         return
        """
        return

    def pre_step(self):
        """This function can be overridden to perform any computation that has to happen before the simulation step.
        Its intended use is for computation that has to happen only once before the simulation step has accured.

        For example, you can store temporal data before letting the world step.

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> class Scenario(BaseScenario):
            >>>     def pre_step(self):
            >>>         for agent in self.world.agents:
            >>>             agent.prev_state = agent.state
            >>>         return
        """
        return

    def post_step(self):
        """This function can be overridden to perform any computation that has to happen after the simulation step.
        Its intended use is for computation that has to happen only once after the simulation step has accured.

        For example, you can store temporal sensor data in this function.

        Examples:
            >>> from vmas.simulator.scenario import BaseScenario
            >>> class Scenario(BaseScenario):
            >>>     def post_step(self):
            >>>         for agent in self.world.agents:
            >>>             # Let the sensor take a measurement
            >>>             measurements = agent.sensors[0].measure()
            >>>             # Store sensor data in agent.sensor_history
            >>>             agent.sensor_history.append(measurements)
            >>>         return
        """
        return

def env_make_world(self, batch_dim: int, device: torch.device, **kwargs) -> World:
    self._world = self.make_world(batch_dim, device, **kwargs)
    return self._world

class ScenarioUtils:

    @staticmethod
    def spawn_entities_randomly(entities, world, env_index: int, min_dist_between_entities: float, x_bounds: Tuple[int, int], y_bounds: Tuple[int, int], occupied_positions: Tensor=None, disable_warn: bool=False):
        batch_size = world.batch_dim if env_index is None else 1
        if occupied_positions is None:
            occupied_positions = torch.zeros((batch_size, 0, world.dim_p), device=world.device)
        for entity in entities:
            pos = ScenarioUtils.find_random_pos_for_entity(occupied_positions, env_index, world, min_dist_between_entities, x_bounds, y_bounds, disable_warn)
            occupied_positions = torch.cat([occupied_positions, pos], dim=1)
            entity.set_pos(pos.squeeze(1), batch_index=env_index)

    @staticmethod
    def find_random_pos_for_entity(occupied_positions: torch.Tensor, env_index: int, world, min_dist_between_entities: float, x_bounds: Tuple[int, int], y_bounds: Tuple[int, int], disable_warn: bool=False):
        batch_size = world.batch_dim if env_index is None else 1
        pos = None
        tries = 0
        while True:
            proposed_pos = torch.cat([torch.empty((batch_size, 1, 1), device=world.device, dtype=torch.float32).uniform_(*x_bounds), torch.empty((batch_size, 1, 1), device=world.device, dtype=torch.float32).uniform_(*y_bounds)], dim=2)
            if pos is None:
                pos = proposed_pos
            if occupied_positions.shape[1] == 0:
                break
            dist = torch.cdist(occupied_positions, pos)
            overlaps = torch.any((dist < min_dist_between_entities).squeeze(2), dim=1)
            if torch.any(overlaps, dim=0):
                pos[overlaps] = proposed_pos[overlaps]
            else:
                break
            tries += 1
            if tries > 50000 and (not disable_warn):
                warnings.warn('It is taking many iterations to spawn the entity, make sure the bounds or the min_dist_between_entities are not too tight to fit all entities.You can disable this warning by setting disable_warn=True')
        return pos

    @staticmethod
    def check_kwargs_consumed(dictionary_of_kwargs: Dict, warn: bool=True):
        if len(dictionary_of_kwargs) > 0:
            message = f'Scenario kwargs: {dictionary_of_kwargs} passed but not used by the scenario.'
            if warn:
                warnings.warn(message + ' This will turn into an error in future versions.')
            else:
                raise ValueError(message)

    @staticmethod
    def render_agent_indices(scenario, env_index: int, start_from: int=0, exclude: List=None) -> 'List[Geom]':
        from vmas.simulator import rendering
        aspect_r = scenario.viewer_size[X] / scenario.viewer_size[Y]
        if aspect_r > 1:
            dimensional_ratio = (aspect_r, 1)
        else:
            dimensional_ratio = (1, 1 / aspect_r)
        geoms = []
        for i, entity in enumerate(scenario.world.agents):
            if exclude is not None and entity in exclude:
                continue
            i = i + start_from
            line = rendering.TextLine(text=str(i), font_size=15, x=entity.state.pos[env_index, X] * scenario.viewer_size[X] / (scenario.viewer_zoom ** 2 * dimensional_ratio[X] * 2) + scenario.viewer_size[X] / 2, y=entity.state.pos[env_index, Y] * scenario.viewer_size[Y] / (scenario.viewer_zoom ** 2 * dimensional_ratio[Y] * 2) + scenario.viewer_size[Y] / 2)
            geoms.append(line)
        return geoms

    @staticmethod
    def plot_entity_rotation(entity, env_index: int, length: float=0.15) -> 'Geom':
        from vmas.simulator import rendering
        color = entity.color
        line = rendering.Line((0, 0), (length, 0), width=2)
        xform = rendering.Transform()
        xform.set_rotation(entity.state.rot[env_index])
        xform.set_translation(*entity.state.pos[env_index])
        line.add_attr(xform)
        line.set_color(*color)
        return line

@staticmethod
def render_agent_indices(scenario, env_index: int, start_from: int=0, exclude: List=None) -> 'List[Geom]':
    from vmas.simulator import rendering
    aspect_r = scenario.viewer_size[X] / scenario.viewer_size[Y]
    if aspect_r > 1:
        dimensional_ratio = (aspect_r, 1)
    else:
        dimensional_ratio = (1, 1 / aspect_r)
    geoms = []
    for i, entity in enumerate(scenario.world.agents):
        if exclude is not None and entity in exclude:
            continue
        i = i + start_from
        line = rendering.TextLine(text=str(i), font_size=15, x=entity.state.pos[env_index, X] * scenario.viewer_size[X] / (scenario.viewer_zoom ** 2 * dimensional_ratio[X] * 2) + scenario.viewer_size[X] / 2, y=entity.state.pos[env_index, Y] * scenario.viewer_size[Y] / (scenario.viewer_zoom ** 2 * dimensional_ratio[Y] * 2) + scenario.viewer_size[Y] / 2)
        geoms.append(line)
    return geoms

class Environment(TorchVectorizedObject):
    """
    The VMAS environment
    """
    metadata = {'render.modes': ['human', 'rgb_array'], 'runtime.vectorized': True}
    vmas_random_state = [torch.random.get_rng_state(), np.random.get_state(), random.getstate()]

    @local_seed(vmas_random_state)
    def __init__(self, scenario: BaseScenario, num_envs: int=32, device: DEVICE_TYPING='cpu', max_steps: Optional[int]=None, continuous_actions: bool=True, seed: Optional[int]=None, dict_spaces: bool=False, multidiscrete_actions: bool=False, clamp_actions: bool=False, grad_enabled: bool=False, terminated_truncated: bool=False, **kwargs):
        if multidiscrete_actions:
            assert not continuous_actions, 'When asking for multidiscrete_actions, make sure continuous_actions=False'
        self.scenario = scenario
        self.num_envs = num_envs
        TorchVectorizedObject.__init__(self, num_envs, torch.device(device))
        self.world = self.scenario.env_make_world(self.num_envs, self.device, **kwargs)
        self.agents = self.world.policy_agents
        self.n_agents = len(self.agents)
        self.max_steps = max_steps
        self.continuous_actions = continuous_actions
        self.dict_spaces = dict_spaces
        self.clamp_action = clamp_actions
        self.grad_enabled = grad_enabled
        self.terminated_truncated = terminated_truncated
        observations = self._reset(seed=seed)
        self.multidiscrete_actions = multidiscrete_actions
        self.action_space = self.get_action_space()
        self.observation_space = self.get_observation_space(observations)
        self.viewer = None
        self.headless = None
        self.visible_display = None
        self.text_lines = None

    @local_seed(vmas_random_state)
    def reset(self, seed: Optional[int]=None, return_observations: bool=True, return_info: bool=False, return_dones: bool=False):
        """
        Resets the environment in a vectorized way
        Returns observations for all envs and agents
        """
        return self._reset(seed=seed, return_observations=return_observations, return_info=return_info, return_dones=return_dones)

    @local_seed(vmas_random_state)
    def reset_at(self, index: int, return_observations: bool=True, return_info: bool=False, return_dones: bool=False):
        """
        Resets the environment at index
        Returns observations for all agents in that environment
        """
        return self._reset_at(index=index, return_observations=return_observations, return_info=return_info, return_dones=return_dones)

    @local_seed(vmas_random_state)
    def get_from_scenario(self, get_observations: bool, get_rewards: bool, get_infos: bool, get_dones: bool, dict_agent_names: Optional[bool]=None):
        """
        Get the environment data from the scenario

        Args:
            get_observations (bool): whether to return the observations
            get_rewards (bool): whether to return the rewards
            get_infos (bool): whether to return the infos
            get_dones (bool): whether to return the dones
            dict_agent_names (bool, optional): whether to return the information in a dictionary with agent names as keys
                or in a list

        Returns:
            The agents' data

        """
        return self._get_from_scenario(get_observations=get_observations, get_rewards=get_rewards, get_infos=get_infos, get_dones=get_dones, dict_agent_names=dict_agent_names)

    @local_seed(vmas_random_state)
    def seed(self, seed=None):
        """
        Sets the seed for the environment
        Args:
            seed (int, optional): Seed for the environment. Defaults to None.

        """
        return self._seed(seed=seed)

    @local_seed(vmas_random_state)
    def done(self):
        """
        Get the done flags for the scenario.

        Returns:
            Either terminated, truncated (if self.terminated_truncated==True) or terminated + truncated (if self.terminated_truncated==False)

        """
        return self._done()

    def _reset(self, seed: Optional[int]=None, return_observations: bool=True, return_info: bool=False, return_dones: bool=False):
        """
        Resets the environment in a vectorized way
        Returns observations for all envs and agents
        """
        if seed is not None:
            self._seed(seed)
        self.scenario.env_reset_world_at(env_index=None)
        self.steps = torch.zeros(self.num_envs, device=self.device)
        result = self._get_from_scenario(get_observations=return_observations, get_infos=return_info, get_rewards=False, get_dones=return_dones)
        return result[0] if result and len(result) == 1 else result

    def _reset_at(self, index: int, return_observations: bool=True, return_info: bool=False, return_dones: bool=False):
        """
        Resets the environment at index
        Returns observations for all agents in that environment
        """
        self._check_batch_index(index)
        self.scenario.env_reset_world_at(index)
        self.steps[index] = 0
        result = self._get_from_scenario(get_observations=return_observations, get_infos=return_info, get_rewards=False, get_dones=return_dones)
        return result[0] if result and len(result) == 1 else result

    def _get_from_scenario(self, get_observations: bool, get_rewards: bool, get_infos: bool, get_dones: bool, dict_agent_names: Optional[bool]=None):
        if not get_infos and (not get_dones) and (not get_rewards) and (not get_observations):
            return
        if dict_agent_names is None:
            dict_agent_names = self.dict_spaces
        obs = rewards = infos = terminated = truncated = dones = None
        if get_observations:
            obs = {} if dict_agent_names else []
        if get_rewards:
            rewards = {} if dict_agent_names else []
        if get_infos:
            infos = {} if dict_agent_names else []
        if get_rewards:
            for agent in self.agents:
                reward = self.scenario.reward(agent).clone()
                if dict_agent_names:
                    rewards.update({agent.name: reward})
                else:
                    rewards.append(reward)
        if get_observations:
            for agent in self.agents:
                observation = TorchUtils.recursive_clone(self.scenario.observation(agent))
                if dict_agent_names:
                    obs.update({agent.name: observation})
                else:
                    obs.append(observation)
        if get_infos:
            for agent in self.agents:
                info = TorchUtils.recursive_clone(self.scenario.info(agent))
                if dict_agent_names:
                    infos.update({agent.name: info})
                else:
                    infos.append(info)
        if self.terminated_truncated:
            if get_dones:
                terminated, truncated = self._done()
            result = [obs, rewards, terminated, truncated, infos]
        else:
            if get_dones:
                dones = self._done()
            result = [obs, rewards, dones, infos]
        return [data for data in result if data is not None]

    def _seed(self, seed=None):
        """
        Sets the seed for the environment
        Args:
            seed (int, optional): Seed for the environment. Defaults to None.

        """
        if seed is None:
            seed = 0
        torch.manual_seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        return [seed]

    @local_seed(vmas_random_state)
    def step(self, actions: Union[List, Dict]):
        """Performs a vectorized step on all sub environments using `actions`.

        Args:
            actions: Is a list on len 'self.n_agents' of which each element is a torch.Tensor of shape '(self.num_envs, action_size_of_agent)'.

        Returns:
            obs: List on len 'self.n_agents' of which each element is a torch.Tensor of shape '(self.num_envs, obs_size_of_agent)'
            rewards: List on len 'self.n_agents' of which each element is a torch.Tensor of shape '(self.num_envs)'
            dones: Tensor of len 'self.num_envs' of which each element is a bool
            infos: List on len 'self.n_agents' of which each element is a dictionary for which each key is a metric and the value is a tensor of shape '(self.num_envs, metric_size_per_agent)'

        Examples:
            >>> import vmas
            >>> env = vmas.make_env(
            ...     scenario="waterfall",  # can be scenario name or BaseScenario class
            ...     num_envs=32,
            ...     device="cpu",  # Or "cuda" for GPU
            ...     continuous_actions=True,
            ...     max_steps=None,  # Defines the horizon. None is infinite horizon.
            ...     seed=None,  # Seed of the environment
            ...     n_agents=3,  # Additional arguments you want to pass to the scenario
            ... )
            >>> obs = env.reset()
            >>> for _ in range(10):
            ...     obs, rews, dones, info = env.step(env.get_random_actions())

        """
        if isinstance(actions, Dict):
            actions_dict = actions
            actions = []
            for agent in self.agents:
                try:
                    actions.append(actions_dict[agent.name])
                except KeyError:
                    raise AssertionError(f"Agent '{agent.name}' not contained in action dict")
            assert len(actions_dict) == self.n_agents, f'Expecting actions for {self.n_agents}, got {len(actions_dict)} actions'
        assert len(actions) == self.n_agents, f'Expecting actions for {self.n_agents}, got {len(actions)} actions'
        for i in range(len(actions)):
            if not isinstance(actions[i], Tensor):
                actions[i] = torch.tensor(actions[i], dtype=torch.float32, device=self.device)
            if len(actions[i].shape) == 1:
                actions[i].unsqueeze_(-1)
            assert actions[i].shape[0] == self.num_envs, f'Actions used in input of env must be of len {self.num_envs}, got {actions[i].shape[0]}'
            assert actions[i].shape[1] == self.get_agent_action_size(self.agents[i]), f'Action for agent {self.agents[i].name} has shape {actions[i].shape[1]}, but should have shape {self.get_agent_action_size(self.agents[i])}'
        for i, agent in enumerate(self.agents):
            self._set_action(actions[i], agent)
        for agent in self.world.agents:
            self.scenario.env_process_action(agent)
        self.scenario.pre_step()
        self.world.step()
        self.scenario.post_step()
        self.steps += 1
        return self._get_from_scenario(get_observations=True, get_infos=True, get_rewards=True, get_dones=True)

    def _done(self):
        """
        Get the done flags for the scenario.

        Returns:
            Either terminated, truncated (if self.terminated_truncated==True) or terminated + truncated (if self.terminated_truncated==False)

        """
        terminated = self.scenario.done().clone()
        if self.max_steps is not None:
            truncated = self.steps >= self.max_steps
        else:
            truncated = None
        if self.terminated_truncated:
            if truncated is None:
                truncated = torch.zeros_like(terminated)
            return (terminated, truncated)
        else:
            if truncated is None:
                return terminated
            return terminated + truncated

    def get_action_space(self):
        if not self.dict_spaces:
            return spaces.Tuple([self.get_agent_action_space(agent) for agent in self.agents])
        else:
            return spaces.Dict({agent.name: self.get_agent_action_space(agent) for agent in self.agents})

    def get_observation_space(self, observations: Union[List, Dict]):
        if not self.dict_spaces:
            return spaces.Tuple([self.get_agent_observation_space(agent, observations[i]) for i, agent in enumerate(self.agents)])
        else:
            return spaces.Dict({agent.name: self.get_agent_observation_space(agent, observations[agent.name]) for agent in self.agents})

    def get_agent_action_size(self, agent: Agent):
        if self.continuous_actions:
            return agent.action.action_size + (self.world.dim_c if not agent.silent else 0)
        elif self.multidiscrete_actions:
            return agent.action_size + (1 if not agent.silent and self.world.dim_c != 0 else 0)
        else:
            return 1

    def get_agent_action_space(self, agent: Agent):
        if self.continuous_actions:
            return spaces.Box(low=np.array((-agent.action.u_range_tensor).tolist() + [0] * (self.world.dim_c if not agent.silent else 0), dtype=np.float32), high=np.array(agent.action.u_range_tensor.tolist() + [1] * (self.world.dim_c if not agent.silent else 0), dtype=np.float32), shape=(self.get_agent_action_size(agent),), dtype=np.float32)
        elif self.multidiscrete_actions:
            actions = agent.discrete_action_nvec + ([self.world.dim_c] if not agent.silent and self.world.dim_c != 0 else [])
            return spaces.MultiDiscrete(actions)
        else:
            return spaces.Discrete(math.prod(agent.discrete_action_nvec) * (self.world.dim_c if not agent.silent and self.world.dim_c != 0 else 1))

    def get_agent_observation_space(self, agent: Agent, obs: AGENT_OBS_TYPE):
        if isinstance(obs, Tensor):
            return spaces.Box(low=-np.float32('inf'), high=np.float32('inf'), shape=obs.shape[1:], dtype=np.float32)
        elif isinstance(obs, Dict):
            return spaces.Dict({key: self.get_agent_observation_space(agent, value) for key, value in obs.items()})
        else:
            raise NotImplementedError(f'Invalid type of observation {obs} for agent {agent.name}')

    @local_seed(vmas_random_state)
    def get_random_action(self, agent: Agent) -> torch.Tensor:
        """Returns a random action for the given agent.

        Args:
            agent (Agent): The agent to get the action for

        Returns:
            torch.tensor: the random actions tensor with shape ``(agent.batch_dim, agent.action_size)``

        """
        if self.continuous_actions:
            actions = []
            for action_index in range(agent.action_size):
                actions.append(torch.zeros(agent.batch_dim, device=agent.device, dtype=torch.float32).uniform_(-agent.action.u_range_tensor[action_index], agent.action.u_range_tensor[action_index]))
            if self.world.dim_c != 0 and (not agent.silent):
                for _ in range(self.world.dim_c):
                    actions.append(torch.zeros(agent.batch_dim, device=agent.device, dtype=torch.float32).uniform_(0, 1))
            action = torch.stack(actions, dim=-1)
        else:
            action_space = self.get_agent_action_space(agent)
            if self.multidiscrete_actions:
                actions = [torch.randint(low=0, high=action_space.nvec[action_index], size=(agent.batch_dim,), device=agent.device) for action_index in range(action_space.shape[0])]
                action = torch.stack(actions, dim=-1)
            else:
                action = torch.randint(low=0, high=action_space.n, size=(agent.batch_dim,), device=agent.device)
        return action

    def get_random_actions(self) -> Sequence[torch.Tensor]:
        """Returns random actions for all agents that you can feed to :meth:`step`

        Returns:
            Sequence[torch.tensor]: the random actions for the agents

        Examples:
            >>> import vmas
            >>> env = vmas.make_env(
            ...     scenario="waterfall",  # can be scenario name or BaseScenario class
            ...     num_envs=32,
            ...     device="cpu",  # Or "cuda" for GPU
            ...     continuous_actions=True,
            ...     max_steps=None,  # Defines the horizon. None is infinite horizon.
            ...     seed=None,  # Seed of the environment
            ...     n_agents=3,  # Additional arguments you want to pass to the scenario
            ... )
            >>> obs = env.reset()
            >>> for _ in range(10):
            ...     obs, rews, dones, info = env.step(env.get_random_actions())

        """
        return [self.get_random_action(agent) for agent in self.agents]

    def _check_discrete_action(self, action: Tensor, low: int, high: int, type: str):
        assert torch.all((action >= torch.tensor(low, device=self.device)) * (action < torch.tensor(high, device=self.device))), f'Discrete {type} actions are out of bounds, allowed int range [{low},{high})'

    def _set_action(self, action, agent):
        action = action.clone()
        if not self.grad_enabled:
            action = action.detach()
        action = action.to(self.device)
        assert not action.isnan().any()
        agent.action.u = torch.zeros(self.batch_dim, agent.action_size, device=self.device, dtype=torch.float32)
        assert action.shape[1] == self.get_agent_action_size(agent), f'Agent {agent.name} has wrong action size, got {action.shape[1]}, expected {self.get_agent_action_size(agent)}'
        if self.clamp_action and self.continuous_actions:
            physical_action = action[..., :agent.action_size]
            a_range = agent.action.u_range_tensor.unsqueeze(0).expand(physical_action.shape)
            physical_action = physical_action.clamp(-a_range, a_range)
            if self.world.dim_c > 0 and (not agent.silent):
                comm_action = action[..., agent.action_size:]
                action = torch.cat([physical_action, comm_action.clamp(0, 1)], dim=-1)
            else:
                action = physical_action
        action_index = 0
        if self.continuous_actions:
            physical_action = action[:, action_index:action_index + agent.action_size]
            action_index += self.world.dim_p
            assert not torch.any(torch.abs(physical_action) > agent.action.u_range_tensor), f'Physical actions of agent {agent.name} are out of its range {agent.u_range}'
            agent.action.u = physical_action.to(torch.float32)
        else:
            if not self.multidiscrete_actions:
                flat_action = action.squeeze(-1)
                actions = []
                nvec = list(agent.discrete_action_nvec) + ([self.world.dim_c] if not agent.silent and self.world.dim_c != 0 else [])
                for i in range(len(nvec)):
                    n = math.prod(nvec[i + 1:])
                    actions.append(flat_action // n)
                    flat_action = flat_action % n
                action = torch.stack(actions, dim=-1)
            for n in agent.discrete_action_nvec:
                physical_action = action[:, action_index]
                self._check_discrete_action(physical_action.unsqueeze(-1), low=0, high=n, type='physical')
                u_max = agent.action.u_range_tensor[action_index]
                if n % 2 != 0:
                    stay = physical_action == 0
                    decrement = (physical_action > 0) & (physical_action <= n // 2)
                    physical_action[stay] = n // 2
                    physical_action[decrement] -= 1
                agent.action.u[:, action_index] = physical_action / (n - 1) * (2 * u_max) - u_max
                action_index += 1
        agent.action.u *= agent.action.u_multiplier_tensor
        if agent.action.u_noise > 0:
            noise = torch.randn(*agent.action.u.shape, device=self.device, dtype=torch.float32) * agent.u_noise
            agent.action.u += noise
        if self.world.dim_c > 0 and (not agent.silent):
            if not self.continuous_actions:
                comm_action = action[:, action_index:]
                self._check_discrete_action(comm_action, 0, self.world.dim_c, 'communication')
                comm_action = comm_action.long()
                agent.action.c = torch.zeros(self.num_envs, self.world.dim_c, device=self.device, dtype=torch.float32)
                agent.action.c.scatter_(1, comm_action, 1)
            else:
                comm_action = action[:, action_index:]
                assert not torch.any(comm_action > 1) and (not torch.any(comm_action < 0)), 'Comm actions are out of range [0,1]'
                agent.action.c = comm_action
            if agent.c_noise > 0:
                noise = torch.randn(*agent.action.c.shape, device=self.device, dtype=torch.float32) * agent.c_noise
                agent.action.c += noise

    @local_seed(vmas_random_state)
    def render(self, mode='human', env_index=0, agent_index_focus: int=None, visualize_when_rgb: bool=False, plot_position_function: Callable=None, plot_position_function_precision: float=0.01, plot_position_function_range: Optional[Union[float, Tuple[float, float], Tuple[Tuple[float, float], Tuple[float, float]]]]=None, plot_position_function_cmap_range: Optional[Tuple[float, float]]=None, plot_position_function_cmap_alpha: Optional[float]=1.0, plot_position_function_cmap_name: Optional[str]='viridis'):
        """
        Render function for environment using pyglet

        On servers use mode="rgb_array" and set

        ```
        export DISPLAY=':99.0'
        Xvfb :99 -screen 0 1400x900x24 > /dev/null 2>&1 &
        ```

        :param mode: One of human or rgb_array
        :param env_index: Index of the environment to render
        :param agent_index_focus: If specified the camera will stay on the agent with this index. If None, the camera will stay in the center and zoom out to contain all agents
        :param visualize_when_rgb: Also run human visualization when mode=="rgb_array"
        :param plot_position_function: A function to plot under the rendering.
        The function takes a numpy array with shape (n_points, 2), which represents a set of x,y values to evaluate f over and plot it
        It should output either an array with shape (n_points, 1) which will be plotted as a colormap
        or an array with shape (n_points, 4), which will be plotted as RGBA values
        :param plot_position_function_precision: The precision to use for plotting the function
        :param plot_position_function_range: The position range to plot the function in.
        If float, the range for x and y is (-function_range, function_range)
        If Tuple[float, float], the range for x is (-function_range[0], function_range[0]) and y is (-function_range[1], function_range[1])
        If Tuple[Tuple[float, float], Tuple[float, float]], the first tuple is the x range and the second tuple is the y range
        :param plot_position_function_cmap_range: The range of the cmap in case plot_position_function outputs a single value
        :param plot_position_function_cmap_alpha: The alpha of the cmap in case plot_position_function outputs a single value
        :return: Rgb array or None, depending on the mode

        """
        self._check_batch_index(env_index)
        assert mode in self.metadata['render.modes'], f'Invalid mode {mode} received, allowed modes: {self.metadata['render.modes']}'
        if agent_index_focus is not None:
            assert 0 <= agent_index_focus < self.n_agents, f'Agent focus in rendering should be a valid agent index between 0 and {self.n_agents}, got {agent_index_focus}'
        shared_viewer = agent_index_focus is None
        aspect_ratio = self.scenario.viewer_size[X] / self.scenario.viewer_size[Y]
        headless = mode == 'rgb_array' and (not visualize_when_rgb)
        if self.visible_display is None:
            self.visible_display = not headless
            self.headless = headless
        else:
            assert self.visible_display is not headless
        if self.viewer is None:
            try:
                import pyglet
            except ImportError:
                raise ImportError("Cannot import pyg;et: you can install pyglet directly via 'pip install pyglet'.")
            try:
                pyglet.lib.load_library('EGL')
                from pyglet.libs.egl import egl, eglext
                num_devices = egl.EGLint()
                eglext.eglQueryDevicesEXT(0, None, byref(num_devices))
                assert num_devices.value > 0
            except (ImportError, AssertionError):
                self.headless = False
            pyglet.options['headless'] = self.headless
            self._init_rendering()
        if self.scenario.viewer_zoom <= 0:
            raise ValueError('Scenario viewer zoom must be > 0')
        zoom = self.scenario.viewer_zoom
        if aspect_ratio < 1:
            cam_range = torch.tensor([zoom, zoom / aspect_ratio], device=self.device)
        else:
            cam_range = torch.tensor([zoom * aspect_ratio, zoom], device=self.device)
        if shared_viewer:
            all_poses = torch.stack([agent.state.pos[env_index] for agent in self.world.agents], dim=0)
            max_agent_radius = max([agent.shape.circumscribed_radius() for agent in self.world.agents])
            viewer_size_fit = torch.stack([torch.max(torch.abs(all_poses[:, X] - self.scenario.render_origin[X])), torch.max(torch.abs(all_poses[:, Y] - self.scenario.render_origin[Y]))]) + 2 * max_agent_radius
            viewer_size = torch.maximum(viewer_size_fit / cam_range, torch.tensor(zoom, device=self.device))
            cam_range *= torch.max(viewer_size)
            self.viewer.set_bounds(-cam_range[X] + self.scenario.render_origin[X], cam_range[X] + self.scenario.render_origin[X], -cam_range[Y] + self.scenario.render_origin[Y], cam_range[Y] + self.scenario.render_origin[Y])
        else:
            pos = self.agents[agent_index_focus].state.pos[env_index]
            self.viewer.set_bounds(pos[X] - cam_range[X], pos[X] + cam_range[X], pos[Y] - cam_range[Y], pos[Y] + cam_range[Y])
        if self.scenario.visualize_semidims:
            self.plot_boundary()
        self._set_agent_comm_messages(env_index)
        if plot_position_function is not None:
            self.viewer.add_onetime(self.plot_function(plot_position_function, precision=plot_position_function_precision, plot_range=plot_position_function_range, cmap_range=plot_position_function_cmap_range, cmap_alpha=plot_position_function_cmap_alpha, cmap_name=plot_position_function_cmap_name))
        from vmas.simulator.rendering import Grid
        if self.scenario.plot_grid:
            grid = Grid(spacing=self.scenario.grid_spacing)
            grid.set_color(*vmas.simulator.utils.Color.BLACK.value, alpha=0.3)
            self.viewer.add_onetime(grid)
        self.viewer.add_onetime_list(self.scenario.extra_render(env_index))
        for entity in self.world.entities:
            self.viewer.add_onetime_list(entity.render(env_index=env_index))
        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def plot_boundary(self):
        if self.world.x_semidim is not None or self.world.y_semidim is not None:
            from vmas.simulator.rendering import Line
            from vmas.simulator.utils import Color
            infinite_value = 100
            x_semi = self.world.x_semidim if self.world.x_semidim is not None else infinite_value
            y_semi = self.world.y_semidim if self.world.y_semidim is not None else infinite_value
            color = Color.GRAY.value
            if self.world.x_semidim is not None and self.world.y_semidim is not None or self.world.y_semidim is not None:
                boundary_points = [(-x_semi, y_semi), (x_semi, y_semi), (x_semi, -y_semi), (-x_semi, -y_semi)]
            else:
                boundary_points = [(-x_semi, y_semi), (-x_semi, -y_semi), (x_semi, y_semi), (x_semi, -y_semi)]
            for i in range(0, len(boundary_points), 1 if self.world.x_semidim is not None and self.world.y_semidim is not None else 2):
                start = boundary_points[i]
                end = boundary_points[(i + 1) % len(boundary_points)]
                line = Line(start, end, width=0.7)
                line.set_color(*color)
                self.viewer.add_onetime(line)

    def plot_function(self, f, precision, plot_range, cmap_range, cmap_alpha, cmap_name):
        from vmas.simulator.rendering import render_function_util
        if plot_range is None:
            assert self.viewer.bounds is not None, 'Set viewer bounds before plotting'
            x_min, x_max, y_min, y_max = self.viewer.bounds.tolist()
            plot_range = ([x_min - precision, x_max - precision], [y_min - precision, y_max + precision])
        geom = render_function_util(f=f, precision=precision, plot_range=plot_range, cmap_range=cmap_range, cmap_alpha=cmap_alpha, cmap_name=cmap_name)
        return geom

    def _init_rendering(self):
        from vmas.simulator import rendering
        self.viewer = rendering.Viewer(*self.scenario.viewer_size, visible=self.visible_display)
        self.text_lines = []
        idx = 0
        if self.world.dim_c > 0:
            for agent in self.world.agents:
                if not agent.silent:
                    text_line = rendering.TextLine(y=idx * 40)
                    self.viewer.geoms.append(text_line)
                    self.text_lines.append(text_line)
                    idx += 1

    def _set_agent_comm_messages(self, env_index: int):
        if self.world.dim_c > 0:
            idx = 0
            for agent in self.world.agents:
                if not agent.silent:
                    assert agent.state.c is not None, 'Agent has no comm state but it should'
                    if self.continuous_actions:
                        word = '[' + ','.join([f'{comm:.2f}' for comm in agent.state.c[env_index]]) + ']'
                    else:
                        word = ALPHABET[torch.argmax(agent.state.c[env_index]).item()]
                    message = agent.name + ' sends ' + word + '   '
                    self.text_lines[idx].set_text(message)
                    idx += 1

    @override(TorchVectorizedObject)
    def to(self, device: DEVICE_TYPING):
        device = torch.device(device)
        self.scenario.to(device)
        super().to(device)

def _init_rendering(self):
    from vmas.simulator import rendering
    self.viewer = rendering.Viewer(*self.scenario.viewer_size, visible=self.visible_display)
    self.text_lines = []
    idx = 0
    if self.world.dim_c > 0:
        for agent in self.world.agents:
            if not agent.silent:
                text_line = rendering.TextLine(y=idx * 40)
                self.viewer.geoms.append(text_line)
                self.text_lines.append(text_line)
                idx += 1

def _set_agent_comm_messages(self, env_index: int):
    if self.world.dim_c > 0:
        idx = 0
        for agent in self.world.agents:
            if not agent.silent:
                assert agent.state.c is not None, 'Agent has no comm state but it should'
                if self.continuous_actions:
                    word = '[' + ','.join([f'{comm:.2f}' for comm in agent.state.c[env_index]]) + ']'
                else:
                    word = ALPHABET[torch.argmax(agent.state.c[env_index]).item()]
                message = agent.name + ' sends ' + word + '   '
                self.text_lines[idx].set_text(message)
                idx += 1

def scenario_names():
    scenarios = []
    scenarios_folder = Path(__file__).parent.parent / 'vmas' / 'scenarios'
    for path in scenarios_folder.glob('**/*.py'):
        if path.is_file() and (not path.name.startswith('__')):
            scenarios.append(path.stem)
    return scenarios

