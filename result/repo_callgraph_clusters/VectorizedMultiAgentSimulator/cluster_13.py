# Cluster 13

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

class EvaluationCallbacks(DefaultCallbacks):

    def on_episode_step(self, *, worker: RolloutWorker, base_env: BaseEnv, episode: MultiAgentEpisode, **kwargs):
        info = episode.last_info_for()
        for a_key in info.keys():
            for b_key in info[a_key]:
                try:
                    episode.user_data[f'{a_key}/{b_key}'].append(info[a_key][b_key])
                except KeyError:
                    episode.user_data[f'{a_key}/{b_key}'] = [info[a_key][b_key]]

    def on_episode_end(self, *, worker: RolloutWorker, base_env: BaseEnv, policies: Dict[str, Policy], episode: MultiAgentEpisode, **kwargs):
        info = episode.last_info_for()
        for a_key in info.keys():
            for b_key in info[a_key]:
                metric = np.array(episode.user_data[f'{a_key}/{b_key}'])
                episode.custom_metrics[f'{a_key}/{b_key}'] = np.sum(metric).item()

def on_episode_step(self, *, worker: RolloutWorker, base_env: BaseEnv, episode: MultiAgentEpisode, **kwargs):
    info = episode.last_info_for()
    for a_key in info.keys():
        for b_key in info[a_key]:
            try:
                episode.user_data[f'{a_key}/{b_key}'].append(info[a_key][b_key])
            except KeyError:
                episode.user_data[f'{a_key}/{b_key}'] = [info[a_key][b_key]]

def on_episode_end(self, *, worker: RolloutWorker, base_env: BaseEnv, policies: Dict[str, Policy], episode: MultiAgentEpisode, **kwargs):
    info = episode.last_info_for()
    for a_key in info.keys():
        for b_key in info[a_key]:
            metric = np.array(episode.user_data[f'{a_key}/{b_key}'])
            episode.custom_metrics[f'{a_key}/{b_key}'] = np.sum(metric).item()

class Viewer(object):

    def __init__(self, width, height, display=None, visible=True):
        display = get_display(display)
        self.width = width
        self.height = height
        self.window = pyglet.window.Window(width=width, height=height, display=display, visible=visible)
        self.window.on_close = self.window_closed_by_user
        self.geoms = []
        self.onetime_geoms = []
        self.transform = Transform()
        self.bounds = None
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(2.0)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def close(self):
        self.window.close()

    def window_closed_by_user(self):
        self.close()

    def set_bounds(self, left, right, bottom, top):
        assert right > left and top > bottom
        self.bounds = torch.tensor([left, right, bottom, top], device=left.device)
        scalex = self.width / (right - left)
        scaley = self.height / (top - bottom)
        self.transform = Transform(translation=(-left * scalex, -bottom * scaley), scale=(scalex, scaley))

    def add_geom(self, geom):
        self.geoms.append(geom)

    def add_onetime(self, geom):
        self.onetime_geoms.append(geom)

    def add_onetime_list(self, geoms):
        self.onetime_geoms.extend(geoms)

    def render(self, return_rgb_array=False):
        glClearColor(1, 1, 1, 1)
        self.window.clear()
        self.window.switch_to()
        self.window.dispatch_events()
        self.transform.enable()
        text_lines = []
        for geom in chain(self.geoms, self.onetime_geoms):
            if isinstance(geom, TextLine):
                text_lines.append(geom)
            else:
                geom.render()
        self.transform.disable()
        for text in text_lines:
            text.render()
        pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
        pyglet.gl.glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        arr = None
        if return_rgb_array:
            arr = self.get_array()
        self.window.flip()
        self.onetime_geoms = []
        return arr

    def get_array(self):
        buffer = pyglet.image.get_buffer_manager().get_color_buffer()
        image_data = buffer.get_image_data()
        arr = np.frombuffer(image_data.get_data(), dtype=np.uint8)
        arr = arr.reshape((buffer.height, buffer.width, 4))
        arr = arr[::-1, :, 0:3]
        return arr

def render(self, return_rgb_array=False):
    glClearColor(1, 1, 1, 1)
    self.window.clear()
    self.window.switch_to()
    self.window.dispatch_events()
    self.transform.enable()
    text_lines = []
    for geom in chain(self.geoms, self.onetime_geoms):
        if isinstance(geom, TextLine):
            text_lines.append(geom)
        else:
            geom.render()
    self.transform.disable()
    for text in text_lines:
        text.render()
    pyglet.gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
    pyglet.gl.glLoadIdentity()
    gluOrtho2D(0, self.width, 0, self.height)
    arr = None
    if return_rgb_array:
        arr = self.get_array()
    self.window.flip()
    self.onetime_geoms = []
    return arr

class Geom(object):

    def __init__(self):
        self._color = Color((0, 0, 0, 1.0))
        self.attrs = [self._color]

    def render(self):
        for attr in reversed(self.attrs):
            attr.enable()
        self.render1()
        for attr in self.attrs:
            attr.disable()

    def render1(self):
        raise NotImplementedError

    def add_attr(self, attr):
        self.attrs.append(attr)

    def set_color(self, r, g, b, alpha=1):
        self._color.vec4 = (r, g, b, alpha)

def render(self):
    for attr in reversed(self.attrs):
        attr.enable()
    self.render1()
    for attr in self.attrs:
        attr.disable()

class Compound(Geom):

    def __init__(self, gs):
        Geom.__init__(self)
        self.gs = gs
        for g in self.gs:
            g.attrs = [a for a in g.attrs if not isinstance(a, Color)]

    def render1(self):
        for g in self.gs:
            g.render()

def render1(self):
    for g in self.gs:
        g.render()

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

def get_agent_action_space(self, agent: Agent):
    if self.continuous_actions:
        return spaces.Box(low=np.array((-agent.action.u_range_tensor).tolist() + [0] * (self.world.dim_c if not agent.silent else 0), dtype=np.float32), high=np.array(agent.action.u_range_tensor.tolist() + [1] * (self.world.dim_c if not agent.silent else 0), dtype=np.float32), shape=(self.get_agent_action_size(agent),), dtype=np.float32)
    elif self.multidiscrete_actions:
        actions = agent.discrete_action_nvec + ([self.world.dim_c] if not agent.silent and self.world.dim_c != 0 else [])
        return spaces.MultiDiscrete(actions)
    else:
        return spaces.Discrete(math.prod(agent.discrete_action_nvec) * (self.world.dim_c if not agent.silent and self.world.dim_c != 0 else 1))

class VectorEnvWrapper(rllib.VectorEnv):
    """
    Vector environment wrapper for rllib
    """

    def __init__(self, env: Environment):
        assert not env.terminated_truncated, 'Rllib wrapper is not compatible with termination and truncation flags. Please set `terminated_truncated=False` in the VMAS environment.'
        self._env = env
        super().__init__(observation_space=self._env.observation_space, action_space=self._env.action_space, num_envs=self._env.num_envs)

    @property
    def env(self):
        return self._env

    def vector_reset(self) -> List[EnvObsType]:
        obs = TorchUtils.to_numpy(self._env.reset())
        return self._read_data(obs)[0]

    def reset_at(self, index: Optional[int]=None) -> EnvObsType:
        assert index is not None
        obs = self._env.reset_at(index)
        return self._read_data(obs, env_index=index)[0]

    def vector_step(self, actions: List[EnvActionType]) -> Tuple[List[EnvObsType], List[float], List[bool], List[EnvInfoDict]]:
        actions = self._action_list_to_tensor(actions)
        obs, rews, dones, infos = TorchUtils.to_numpy(self._env.step(actions))
        obs, infos, rews = self._read_data(obs, infos, rews)
        return (obs, rews, dones, infos)

    def seed(self, seed=None):
        return self._env.seed(seed)

    def try_render_at(self, index: Optional[int]=None, mode='human', agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
        """
        Render function for environment using pyglet

        On servers use mode="rgb_array" and set
        ```
        export DISPLAY=':99.0'
        Xvfb :99 -screen 0 1400x900x24 > /dev/null 2>&1 &
        ```

        :param mode: One of human or rgb_array
        :param index: Index of the environment to render
        :param agent_index_focus: If specified the camera will stay on the agent with this index.
                                  If None, the camera will stay in the center and zoom out to contain all agents
        :param visualize_when_rgb: Also run human visualization when mode=="rgb_array"
        :return: Rgb array or None, depending on the mode
        """
        if index is None:
            index = 0
        return self._env.render(mode=mode, env_index=index, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

    def get_sub_environments(self) -> List[Environment]:
        return [self._env]

    def _action_list_to_tensor(self, list_in: List) -> List:
        if len(list_in) == self.num_envs:
            actions = []
            for agent in self._env.agents:
                actions.append(torch.zeros(self.num_envs, self._env.get_agent_action_size(agent), device=self._env.device, dtype=torch.float32))
            for j in range(self.num_envs):
                assert len(list_in[j]) == self._env.n_agents, f'Expecting actions for {self._env.n_agents} agents, got {len(list_in[j])} actions'
                for i in range(self._env.n_agents):
                    act = torch.tensor(list_in[j][i], dtype=torch.float32, device=self._env.device)
                    if len(act.shape) == 0:
                        assert self._env.get_agent_action_size(self._env.agents[i]) == 1, f'Action of agent {i} in env {j} is supposed to be an scalar int'
                    else:
                        assert len(act.shape) == 1 and act.shape[0] == self._env.get_agent_action_size(self._env.agents[i]), f'Action of agent {i} in env {j} hase wrong shape: expected {self._env.get_agent_action_size(self._env.agents[i])}, got {act.shape[0]}'
                    actions[i][j] = act
            return actions
        else:
            raise TypeError('Input action is not in correct format')

    def _read_data(self, obs: Optional[OBS_TYPE], info: Optional[INFO_TYPE]=None, reward: Optional[REWARD_TYPE]=None, env_index: Optional[int]=None):
        if env_index is None:
            obs_list = []
            if info:
                info_list = []
            if reward:
                rew_list = []
            for env_index in range(self.num_envs):
                observations_processed, info_processed, reward_processed = self._get_data_at_env_index(env_index, obs, info, reward)
                obs_list.append(observations_processed)
                if info:
                    info_list.append(info_processed)
                if reward:
                    rew_list.append(reward_processed)
            return (obs_list, info_list if info else None, rew_list if reward else None)
        else:
            return self._get_data_at_env_index(env_index, obs, info, reward)

    def _get_data_at_env_index(self, env_index: int, obs: Optional[OBS_TYPE], info: Optional[INFO_TYPE]=None, reward: Optional[REWARD_TYPE]=None):
        assert len(obs) == self._env.n_agents
        total_rew = 0.0
        if info:
            new_info = {'rewards': {}}
        if isinstance(obs, Dict):
            new_obs = {}
            for agent_index, agent in enumerate(self._env.agents):
                new_obs[agent.name] = self._get_agent_data_at_env_index(env_index, obs[agent.name])
                if info:
                    new_info[agent.name] = self._get_agent_data_at_env_index(env_index, info[agent.name])
                if reward:
                    agent_rew = self._get_agent_data_at_env_index(env_index, reward[agent.name])
                    new_info['rewards'].update({agent_index: agent_rew})
                    total_rew += agent_rew
        elif isinstance(obs, List):
            new_obs = []
            for agent_index, agent in enumerate(self._env.agents):
                new_obs.append(self._get_agent_data_at_env_index(env_index, obs[agent_index]))
                if info:
                    new_info[agent.name] = self._get_agent_data_at_env_index(env_index, info[agent_index])
                if reward:
                    agent_rew = self._get_agent_data_at_env_index(env_index, reward[agent_index])
                    new_info['rewards'].update({agent_index: agent_rew})
                    total_rew += agent_rew
        else:
            raise ValueError(f'Unsupported obs type {obs}')
        return (new_obs, new_info if info else None, total_rew / self._env.n_agents if reward else None)

    def _get_agent_data_at_env_index(self, env_index: int, agent_data):
        if isinstance(agent_data, (ndarray, Tensor)):
            assert agent_data.shape[0] == self._env.num_envs
            if len(agent_data.shape) == 1 or (len(agent_data.shape) == 2 and agent_data.shape[1] == 1):
                return agent_data[env_index].item()
            elif isinstance(agent_data, Tensor):
                return agent_data[env_index].cpu().detach().numpy()
            else:
                return agent_data[env_index]
        elif isinstance(agent_data, Dict):
            return {key: self._get_agent_data_at_env_index(env_index, value) for key, value in agent_data.items()}
        else:
            raise ValueError(f'Unsupported data type {agent_data}')

def try_render_at(self, index: Optional[int]=None, mode='human', agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
    """
        Render function for environment using pyglet

        On servers use mode="rgb_array" and set
        ```
        export DISPLAY=':99.0'
        Xvfb :99 -screen 0 1400x900x24 > /dev/null 2>&1 &
        ```

        :param mode: One of human or rgb_array
        :param index: Index of the environment to render
        :param agent_index_focus: If specified the camera will stay on the agent with this index.
                                  If None, the camera will stay in the center and zoom out to contain all agents
        :param visualize_when_rgb: Also run human visualization when mode=="rgb_array"
        :return: Rgb array or None, depending on the mode
        """
    if index is None:
        index = 0
    return self._env.render(mode=mode, env_index=index, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

class BaseGymWrapper(ABC):

    def __init__(self, env: Environment, return_numpy: bool, vectorized: bool):
        self._env = env
        self.return_numpy = return_numpy
        self.dict_spaces = env.dict_spaces
        self.vectorized = vectorized

    @property
    def env(self):
        return self._env

    def _maybe_to_numpy(self, tensor):
        return TorchUtils.to_numpy(tensor) if self.return_numpy else tensor

    def _convert_output(self, data, item: bool=False):
        if not self.vectorized:
            data = extract_nested_with_index(data, index=0)
            if item:
                return data.item()
        return self._maybe_to_numpy(data)

    def _compress_infos(self, infos):
        if isinstance(infos, dict):
            return infos
        elif isinstance(infos, list):
            return {self._env.agents[i].name: info for i, info in enumerate(infos)}
        else:
            raise ValueError(f'Expected list or dictionary for infos but got {type(infos)}')

    def _convert_env_data(self, obs=None, rews=None, info=None, terminated=None, truncated=None, done=None):
        if self.dict_spaces:
            for agent in obs.keys():
                if obs is not None:
                    obs[agent] = self._convert_output(obs[agent])
                if info is not None:
                    info[agent] = self._convert_output(info[agent])
                if rews is not None:
                    rews[agent] = self._convert_output(rews[agent], item=True)
        else:
            for i in range(self._env.n_agents):
                if obs is not None:
                    obs[i] = self._convert_output(obs[i])
                if info is not None:
                    info[i] = self._convert_output(info[i])
                if rews is not None:
                    rews[i] = self._convert_output(rews[i], item=True)
        terminated = self._convert_output(terminated, item=True) if terminated is not None else None
        truncated = self._convert_output(truncated, item=True) if truncated is not None else None
        done = self._convert_output(done, item=True) if done is not None else None
        info = self._compress_infos(info) if info is not None else None
        return EnvData(obs=obs, rews=rews, terminated=terminated, truncated=truncated, done=done, info=info)

    def _action_list_to_tensor(self, list_in: List) -> List:
        assert len(list_in) == self._env.n_agents, f'Expecting actions for {self._env.n_agents} agents, got {len(list_in)} actions'
        dtype = torch.float32 if self._env.continuous_actions else torch.long
        return [torch.tensor(act, device=self._env.device, dtype=dtype).reshape(self._env.num_envs, self._env.get_agent_action_size(agent)) if not isinstance(act, torch.Tensor) else act.to(dtype=dtype, device=self._env.device).reshape(self._env.num_envs, self._env.get_agent_action_size(agent)) for agent, act in zip(self._env.agents, list_in)]

    @abstractmethod
    def step(self, action):
        raise NotImplementedError

    @abstractmethod
    def reset(self, *, seed: Optional[int]=None, options: Optional[dict]=None):
        raise NotImplementedError

    @abstractmethod
    def render(self, agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
        raise NotImplementedError

def _convert_env_data(self, obs=None, rews=None, info=None, terminated=None, truncated=None, done=None):
    if self.dict_spaces:
        for agent in obs.keys():
            if obs is not None:
                obs[agent] = self._convert_output(obs[agent])
            if info is not None:
                info[agent] = self._convert_output(info[agent])
            if rews is not None:
                rews[agent] = self._convert_output(rews[agent], item=True)
    else:
        for i in range(self._env.n_agents):
            if obs is not None:
                obs[i] = self._convert_output(obs[i])
            if info is not None:
                info[i] = self._convert_output(info[i])
            if rews is not None:
                rews[i] = self._convert_output(rews[i], item=True)
    terminated = self._convert_output(terminated, item=True) if terminated is not None else None
    truncated = self._convert_output(truncated, item=True) if truncated is not None else None
    done = self._convert_output(done, item=True) if done is not None else None
    info = self._compress_infos(info) if info is not None else None
    return EnvData(obs=obs, rews=rews, terminated=terminated, truncated=truncated, done=done, info=info)

class GymnasiumWrapper(gym.Env, BaseGymWrapper):
    metadata = Environment.metadata

    def __init__(self, env: Environment, return_numpy: bool=True, render_mode: str='human'):
        super().__init__(env, return_numpy=return_numpy, vectorized=False)
        assert env.num_envs == 1, 'GymnasiumEnv wrapper only supports singleton VMAS environment! For vectorized environments, use vectorized wrapper with `wrapper=gymnasium_vec`.'
        assert self._env.terminated_truncated, 'GymnasiumWrapper is only compatible with termination and truncation flags. Please set `terminated_truncated=True` in the VMAS environment.'
        self.observation_space = _convert_space(self._env.observation_space)
        self.action_space = _convert_space(self._env.action_space)
        self.render_mode = render_mode

    @property
    def unwrapped(self) -> Environment:
        return self._env

    def step(self, action):
        action = self._action_list_to_tensor(action)
        obs, rews, terminated, truncated, info = self._env.step(action)
        env_data = self._convert_env_data(obs=obs, rews=rews, info=info, terminated=terminated, truncated=truncated)
        return (env_data.obs, env_data.rews, env_data.terminated, env_data.truncated, env_data.info)

    def reset(self, *, seed: Optional[int]=None, options: Optional[dict]=None):
        if seed is not None:
            self._env.seed(seed)
        obs, info = self._env.reset_at(index=0, return_info=True)
        env_data = self._convert_env_data(obs=obs, info=info)
        return (env_data.obs, env_data.info)

    def render(self, agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
        return self._env.render(mode=self.render_mode, env_index=0, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

def render(self, agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
    return self._env.render(mode=self.render_mode, env_index=0, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

class GymnasiumVectorizedWrapper(gym.Env, BaseGymWrapper):
    metadata = Environment.metadata

    def __init__(self, env: Environment, return_numpy: bool=True, render_mode: str='human'):
        super().__init__(env, return_numpy=return_numpy, vectorized=True)
        self._num_envs = self._env.num_envs
        assert self._env.terminated_truncated, 'GymnasiumWrapper is only compatible with termination and truncation flags. Please set `terminated_truncated=True` in the VMAS environment.'
        self.single_observation_space = _convert_space(self._env.observation_space)
        self.single_action_space = _convert_space(self._env.action_space)
        self.observation_space = batch_space(self.single_observation_space, n=self._num_envs)
        self.action_space = batch_space(self.single_action_space, n=self._num_envs)
        self.render_mode = render_mode
        warnings.warn('The Gymnasium Vector wrapper currently does not have auto-resets or support partial resets.We warn you that by using this class, individual environments will not be reset when they are done and youwill only have access to global resets. We strongly suggest using the VMAS API unless your scenario does not implementthe `done` function and thus all sub-environments are done at the same time.')

    @property
    def unwrapped(self) -> Environment:
        return self._env

    def step(self, action):
        action = self._action_list_to_tensor(action)
        obs, rews, terminated, truncated, info = self._env.step(action)
        env_data = self._convert_env_data(obs=obs, rews=rews, info=info, terminated=terminated, truncated=truncated)
        return (env_data.obs, env_data.rews, env_data.terminated, env_data.truncated, env_data.info)

    def reset(self, *, seed: Optional[int]=None, options: Optional[dict]=None):
        if seed is not None:
            self._env.seed(seed)
        obs, info = self._env.reset(return_info=True)
        env_data = self._convert_env_data(obs=obs, info=info)
        return (env_data.obs, env_data.info)

    def render(self, agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
        return self._env.render(mode=self.render_mode, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

def render(self, agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
    return self._env.render(mode=self.render_mode, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

class GymWrapper(gym.Env, BaseGymWrapper):
    metadata = Environment.metadata

    def __init__(self, env: Environment, return_numpy: bool=True):
        super().__init__(env, return_numpy=return_numpy, vectorized=False)
        assert env.num_envs == 1, f'GymEnv wrapper is not vectorised, got env.num_envs: {env.num_envs}'
        assert not self._env.terminated_truncated, 'GymWrapper is not compatible with termination and truncation flags. Please set `terminated_truncated=False` in the VMAS environment.'
        self.observation_space = self._env.observation_space
        self.action_space = self._env.action_space

    @property
    def unwrapped(self) -> Environment:
        return self._env

    def step(self, action):
        action = self._action_list_to_tensor(action)
        obs, rews, done, info = self._env.step(action)
        env_data = self._convert_env_data(obs=obs, rews=rews, info=info, done=done)
        return (env_data.obs, env_data.rews, env_data.done, env_data.info)

    def reset(self, *, seed: Optional[int]=None, return_info: bool=False, options: Optional[dict]=None):
        if seed is not None:
            self._env.seed(seed)
        obs = self._env.reset_at(index=0)
        env_data = self._convert_env_data(obs=obs)
        return env_data.obs

    def render(self, mode='human', agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
        return self._env.render(mode=mode, env_index=0, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

def render(self, mode='human', agent_index_focus: Optional[int]=None, visualize_when_rgb: bool=False, **kwargs) -> Optional[np.ndarray]:
    return self._env.render(mode=mode, env_index=0, agent_index_focus=agent_index_focus, visualize_when_rgb=visualize_when_rgb, **kwargs)

def to_multidiscrete(action, nvec):
    action_multi = []
    for i in range(len(nvec)):
        n = math.prod(nvec[i + 1:])
        action_multi.append(action // n)
        action = action % n
    return torch.stack(action_multi, dim=-1)

