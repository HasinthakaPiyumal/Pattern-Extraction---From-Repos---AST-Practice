# Cluster 42

def run_mpe_simple_spread(n_envs: int, n_steps: int):
    n_envs = int(n_envs)
    n_steps = int(n_steps)
    n_agents = 3
    envs = [mpe_make_env('simple_spread') for _ in range(n_envs)]
    simple_shared_action = [0, 1, 0, 0, 0]
    [env.reset() for env in envs]
    init_time = time.time()
    for _ in range(n_steps):
        for env_idx in range(n_envs):
            actions = []
            for _ in range(n_agents):
                actions.append(simple_shared_action)
            envs[env_idx].step(actions)
    total_time = time.time() - init_time
    return total_time

def run_vmas_simple_spread(n_envs: int, n_steps: int, device: str):
    n_envs = int(n_envs)
    n_steps = int(n_steps)
    n_agents = 3
    env = vmas.make_env('simple_spread', device=device, num_envs=n_envs, continuous_actions=False, n_agents=n_agents)
    simple_shared_action = [2]
    env.reset()
    init_time = time.time()
    for _ in range(n_steps):
        actions = []
        for _ in range(n_agents):
            actions.append(torch.tensor(simple_shared_action, device=device).repeat(n_envs, 1))
        env.step(actions)
    total_time = time.time() - init_time
    return total_time

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

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_agents = kwargs.pop('n_agents', 5)
        self.n_targets = kwargs.pop('n_targets', 7)
        self.x_semidim = kwargs.pop('x_semidim', 1)
        self.y_semidim = kwargs.pop('y_semidim', 1)
        self._min_dist_between_entities = kwargs.pop('min_dist_between_entities', 0.2)
        self._lidar_range = kwargs.pop('lidar_range', 0.35)
        self._covering_range = kwargs.pop('covering_range', 0.25)
        self.use_agent_lidar = kwargs.pop('use_agent_lidar', False)
        self.n_lidar_rays_entities = kwargs.pop('n_lidar_rays_entities', 15)
        self.n_lidar_rays_agents = kwargs.pop('n_lidar_rays_agents', 12)
        self._agents_per_target = kwargs.pop('agents_per_target', 2)
        self.targets_respawn = kwargs.pop('targets_respawn', True)
        self.shared_reward = kwargs.pop('shared_reward', False)
        self.agent_collision_penalty = kwargs.pop('agent_collision_penalty', 0)
        self.covering_rew_coeff = kwargs.pop('covering_rew_coeff', 1.0)
        self.time_penalty = kwargs.pop('time_penalty', 0)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self._comms_range = self._lidar_range
        self.min_collision_distance = 0.005
        self.agent_radius = 0.05
        self.target_radius = self.agent_radius
        self.viewer_zoom = 1
        self.target_color = Color.GREEN
        world = World(batch_dim, device, x_semidim=self.x_semidim, y_semidim=self.y_semidim, collision_force=500, substeps=2, drag=0.25)
        entity_filter_agents: Callable[[Entity], bool] = lambda e: e.name.startswith('agent')
        entity_filter_targets: Callable[[Entity], bool] = lambda e: e.name.startswith('target')
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', collide=True, shape=Sphere(radius=self.agent_radius), sensors=[Lidar(world, n_rays=self.n_lidar_rays_entities, max_range=self._lidar_range, entity_filter=entity_filter_targets, render_color=Color.GREEN)] + ([Lidar(world, angle_start=0.05, angle_end=2 * torch.pi + 0.05, n_rays=self.n_lidar_rays_agents, max_range=self._lidar_range, entity_filter=entity_filter_agents, render_color=Color.BLUE)] if self.use_agent_lidar else []))
            agent.collision_rew = torch.zeros(batch_dim, device=device)
            agent.covering_reward = agent.collision_rew.clone()
            world.add_agent(agent)
        self._targets = []
        for i in range(self.n_targets):
            target = Landmark(name=f'target_{i}', collide=True, movable=False, shape=Sphere(radius=self.target_radius), color=self.target_color)
            world.add_landmark(target)
            self._targets.append(target)
        self.covered_targets = torch.zeros(batch_dim, self.n_targets, device=device)
        self.shared_covering_rew = torch.zeros(batch_dim, device=device)
        return world

    def reset_world_at(self, env_index: int=None):
        placable_entities = self._targets[:self.n_targets] + self.world.agents
        if env_index is None:
            self.all_time_covered_targets = torch.full((self.world.batch_dim, self.n_targets), False, device=self.world.device)
        else:
            self.all_time_covered_targets[env_index] = False
        ScenarioUtils.spawn_entities_randomly(entities=placable_entities, world=self.world, env_index=env_index, min_dist_between_entities=self._min_dist_between_entities, x_bounds=(-self.world.x_semidim, self.world.x_semidim), y_bounds=(-self.world.y_semidim, self.world.y_semidim))
        for target in self._targets[self.n_targets:]:
            target.set_pos(self.get_outside_pos(env_index), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        is_last = agent == self.world.agents[-1]
        if is_first:
            self.time_rew = torch.full((self.world.batch_dim,), self.time_penalty, device=self.world.device)
            self.agents_pos = torch.stack([a.state.pos for a in self.world.agents], dim=1)
            self.targets_pos = torch.stack([t.state.pos for t in self._targets], dim=1)
            self.agents_targets_dists = torch.cdist(self.agents_pos, self.targets_pos)
            self.agents_per_target = torch.sum((self.agents_targets_dists < self._covering_range).type(torch.int), dim=1)
            self.covered_targets = self.agents_per_target >= self._agents_per_target
            self.shared_covering_rew[:] = 0
            for a in self.world.agents:
                self.shared_covering_rew += self.agent_reward(a)
            self.shared_covering_rew[self.shared_covering_rew != 0] /= 2
        agent.collision_rew[:] = 0
        for a in self.world.agents:
            if a != agent:
                agent.collision_rew[self.world.get_distance(a, agent) < self.min_collision_distance] += self.agent_collision_penalty
        if is_last:
            if self.targets_respawn:
                occupied_positions_agents = [self.agents_pos]
                for i, target in enumerate(self._targets):
                    occupied_positions_targets = [o.state.pos.unsqueeze(1) for o in self._targets if o is not target]
                    occupied_positions = torch.cat(occupied_positions_agents + occupied_positions_targets, dim=1)
                    pos = ScenarioUtils.find_random_pos_for_entity(occupied_positions, env_index=None, world=self.world, min_dist_between_entities=self._min_dist_between_entities, x_bounds=(-self.world.x_semidim, self.world.x_semidim), y_bounds=(-self.world.y_semidim, self.world.y_semidim))
                    target.state.pos[self.covered_targets[:, i]] = pos[self.covered_targets[:, i]].squeeze(1)
            else:
                self.all_time_covered_targets += self.covered_targets
                for i, target in enumerate(self._targets):
                    target.state.pos[self.covered_targets[:, i]] = self.get_outside_pos(None)[self.covered_targets[:, i]]
        covering_rew = agent.covering_reward if not self.shared_reward else self.shared_covering_rew
        return agent.collision_rew + covering_rew + self.time_rew

    def get_outside_pos(self, env_index):
        return torch.empty((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device).uniform_(-1000 * self.world.x_semidim, -10 * self.world.x_semidim)

    def agent_reward(self, agent):
        agent_index = self.world.agents.index(agent)
        agent.covering_reward[:] = 0
        targets_covered_by_agent = self.agents_targets_dists[:, agent_index] < self._covering_range
        num_covered_targets_covered_by_agent = (targets_covered_by_agent * self.covered_targets).sum(dim=-1)
        agent.covering_reward += num_covered_targets_covered_by_agent * self.covering_rew_coeff
        return agent.covering_reward

    def observation(self, agent: Agent):
        lidar_1_measures = agent.sensors[0].measure()
        return torch.cat([agent.state.pos, agent.state.vel, lidar_1_measures] + ([agent.sensors[1].measure()] if self.use_agent_lidar else []), dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        info = {'covering_reward': agent.covering_reward if not self.shared_reward else self.shared_covering_rew, 'collision_rew': agent.collision_rew, 'targets_covered': self.covered_targets.sum(-1)}
        return info

    def done(self):
        return self.all_time_covered_targets.all(dim=-1)

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms: List[Geom] = []
        for target in self._targets:
            range_circle = rendering.make_circle(self._covering_range, filled=False)
            xform = rendering.Transform()
            xform.set_translation(*target.state.pos[env_index])
            range_circle.add_attr(xform)
            range_circle.set_color(*self.target_color.value)
            geoms.append(range_circle)
        for i, agent1 in enumerate(self.world.agents):
            for j, agent2 in enumerate(self.world.agents):
                if j <= i:
                    continue
                agent_dist = torch.linalg.vector_norm(agent1.state.pos - agent2.state.pos, dim=-1)
                if agent_dist[env_index] <= self._comms_range:
                    color = Color.BLACK.value
                    line = rendering.Line(agent1.state.pos[env_index], agent2.state.pos[env_index], width=1)
                    xform = rendering.Transform()
                    line.add_attr(xform)
                    line.set_color(*color)
                    geoms.append(line)
        return geoms

def done(self):
    return self.all_time_covered_targets.all(dim=-1)

class Scenario(BaseScenario):

    def init_params(self, **kwargs):
        self.viewer_size = kwargs.pop('viewer_size', (1200, 800))
        self.n_blue_agents = kwargs.pop('n_blue_agents', 3)
        self.n_red_agents = kwargs.pop('n_red_agents', 3)
        self.ai_red_agents = kwargs.pop('ai_red_agents', True)
        self.ai_blue_agents = kwargs.pop('ai_blue_agents', False)
        self.physically_different = kwargs.pop('physically_different', False)
        self.spawn_in_formation = kwargs.pop('spawn_in_formation', False)
        self.only_blue_formation = kwargs.pop('only_blue_formation', True)
        self.formation_agents_per_column = kwargs.pop('formation_agents_per_column', 2)
        self.randomise_formation_indices = kwargs.pop('randomise_formation_indices', False)
        self.formation_noise = kwargs.pop('formation_noise', 0.2)
        self.n_traj_points = kwargs.pop('n_traj_points', 0)
        self.ai_speed_strength = kwargs.pop('ai_strength', 1.0)
        self.ai_decision_strength = kwargs.pop('ai_decision_strength', 1.0)
        self.ai_precision_strength = kwargs.pop('ai_precision_strength', 1.0)
        self.disable_ai_red = kwargs.pop('disable_ai_red', False)
        self.agent_size = kwargs.pop('agent_size', 0.025)
        self.goal_size = kwargs.pop('goal_size', 0.35)
        self.goal_depth = kwargs.pop('goal_depth', 0.1)
        self.pitch_length = kwargs.pop('pitch_length', 3.0)
        self.pitch_width = kwargs.pop('pitch_width', 1.5)
        self.ball_mass = kwargs.pop('ball_mass', 0.25)
        self.ball_size = kwargs.pop('ball_size', 0.02)
        self.u_multiplier = kwargs.pop('u_multiplier', 0.1)
        self.enable_shooting = kwargs.pop('enable_shooting', False)
        self.u_rot_multiplier = kwargs.pop('u_rot_multiplier', 0.0003)
        self.u_shoot_multiplier = kwargs.pop('u_shoot_multiplier', 0.6)
        self.shooting_radius = kwargs.pop('shooting_radius', 0.08)
        self.shooting_angle = kwargs.pop('shooting_angle', torch.pi / 2)
        self.max_speed = kwargs.pop('max_speed', 0.15)
        self.ball_max_speed = kwargs.pop('ball_max_speed', 0.3)
        self.dense_reward = kwargs.pop('dense_reward', True)
        self.pos_shaping_factor_ball_goal = kwargs.pop('pos_shaping_factor_ball_goal', 10.0)
        self.pos_shaping_factor_agent_ball = kwargs.pop('pos_shaping_factor_agent_ball', 0.1)
        self.distance_to_ball_trigger = kwargs.pop('distance_to_ball_trigger', 0.4)
        self.scoring_reward = kwargs.pop('scoring_reward', 100.0)
        self.observe_teammates = kwargs.pop('observe_teammates', True)
        self.observe_adversaries = kwargs.pop('observe_adversaries', True)
        self.dict_obs = kwargs.pop('dict_obs', False)
        if kwargs.pop('dense_reward_ratio', None) is not None:
            raise ValueError('dense_reward_ratio in football is deprecated, please use `dense_reward` which is a bool that turns on/off the dense reward')
        ScenarioUtils.check_kwargs_consumed(kwargs)

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.init_params(**kwargs)
        self.visualize_semidims = False
        world = self.init_world(batch_dim, device)
        self.init_agents(world)
        self.init_ball(world)
        self.init_background()
        self.init_walls(world)
        self.init_goals(world)
        self.init_traj_pts(world)
        self.left_goal_pos = torch.tensor([-self.pitch_length / 2 - self.ball_size / 2, 0], device=device, dtype=torch.float)
        self.right_goal_pos = -self.left_goal_pos
        self._done = torch.zeros(batch_dim, device=device, dtype=torch.bool)
        self._sparse_reward_blue = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self._sparse_reward_red = self._sparse_reward_blue.clone()
        self._render_field = True
        self.min_agent_dist_to_ball_blue = None
        self.min_agent_dist_to_ball_red = None
        self._reset_agent_range = torch.tensor([self.pitch_length / 2, self.pitch_width], device=device)
        self._reset_agent_offset_blue = torch.tensor([-self.pitch_length / 2 + self.agent_size, -self.pitch_width / 2], device=device)
        self._reset_agent_offset_red = torch.tensor([-self.agent_size, -self.pitch_width / 2], device=device)
        self._agents_rel_pos_to_ball = None
        return world

    def reset_world_at(self, env_index: int=None):
        self.reset_agents(env_index)
        self.reset_ball(env_index)
        self.reset_walls(env_index)
        self.reset_goals(env_index)
        self.reset_controllers(env_index)
        if env_index is None:
            self._done[:] = False
        else:
            self._done[env_index] = False

    def init_world(self, batch_dim: int, device: torch.device):
        world = World(batch_dim, device, dt=0.1, drag=0.05, x_semidim=self.pitch_length / 2 + self.goal_depth - self.agent_size, y_semidim=self.pitch_width / 2 - self.agent_size, substeps=2)
        world.agent_size = self.agent_size
        world.pitch_width = self.pitch_width
        world.pitch_length = self.pitch_length
        world.goal_size = self.goal_size
        world.goal_depth = self.goal_depth
        return world

    def init_agents(self, world):
        self.blue_color = (0.22, 0.49, 0.72)
        self.red_color = (0.89, 0.1, 0.11)
        self.red_controller = AgentPolicy(team='Red', disabled=self.disable_ai_red, speed_strength=self.ai_speed_strength[1] if isinstance(self.ai_speed_strength, tuple) else self.ai_speed_strength, precision_strength=self.ai_precision_strength[1] if isinstance(self.ai_precision_strength, tuple) else self.ai_precision_strength, decision_strength=self.ai_decision_strength[1] if isinstance(self.ai_decision_strength, tuple) else self.ai_decision_strength) if self.ai_red_agents else None
        self.blue_controller = AgentPolicy(team='Blue', speed_strength=self.ai_speed_strength[0] if isinstance(self.ai_speed_strength, tuple) else self.ai_speed_strength, precision_strength=self.ai_precision_strength[0] if isinstance(self.ai_precision_strength, tuple) else self.ai_precision_strength, decision_strength=self.ai_decision_strength[0] if isinstance(self.ai_decision_strength, tuple) else self.ai_decision_strength) if self.ai_blue_agents else None
        blue_agents = []
        if self.physically_different:
            blue_agents = self.get_physically_different_agents()
            for agent in blue_agents:
                world.add_agent(agent)
        else:
            for i in range(self.n_blue_agents):
                agent = Agent(name=f'agent_blue_{i}', shape=Sphere(radius=self.agent_size), action_script=self.blue_controller.run if self.ai_blue_agents else None, u_multiplier=[self.u_multiplier, self.u_multiplier] if not self.enable_shooting else [self.u_multiplier, self.u_multiplier, self.u_rot_multiplier, self.u_shoot_multiplier], max_speed=self.max_speed, dynamics=Holonomic() if not self.enable_shooting else HolonomicWithRotation(), action_size=2 if not self.enable_shooting else 4, color=self.blue_color, alpha=1)
                world.add_agent(agent)
                blue_agents.append(agent)
        self.blue_agents = blue_agents
        world.blue_agents = blue_agents
        red_agents = []
        for i in range(self.n_red_agents):
            agent = Agent(name=f'agent_red_{i}', shape=Sphere(radius=self.agent_size), action_script=self.red_controller.run if self.ai_red_agents else None, u_multiplier=[self.u_multiplier, self.u_multiplier] if not self.enable_shooting or self.ai_red_agents else [self.u_multiplier, self.u_multiplier, self.u_rot_multiplier, self.u_shoot_multiplier], max_speed=self.max_speed, dynamics=Holonomic() if not self.enable_shooting or self.ai_red_agents else HolonomicWithRotation(), action_size=2 if not self.enable_shooting or self.ai_red_agents else 4, color=self.red_color, alpha=1)
            world.add_agent(agent)
            red_agents.append(agent)
        self.red_agents = red_agents
        world.red_agents = red_agents
        for agent in self.blue_agents + self.red_agents:
            agent.ball_within_angle = torch.zeros(world.batch_dim, device=agent.device, dtype=torch.bool)
            agent.ball_within_range = torch.zeros(world.batch_dim, device=agent.device, dtype=torch.bool)
            agent.shoot_force = torch.zeros(world.batch_dim, 2, device=agent.device, dtype=torch.float32)

    def get_physically_different_agents(self):
        assert self.n_blue_agents == 5, 'Physical differences only for 5 agents'

        def attacker(i):
            attacker_shoot_multiplier_decrease = -0.2
            attacker_multiplier_increase = 0.1
            attacker_speed_increase = 0.05
            attacker_radius_decrease = -0.005
            return Agent(name=f'agent_blue_{i}', shape=Sphere(radius=self.agent_size + attacker_radius_decrease), action_script=self.blue_controller.run if self.ai_blue_agents else None, u_multiplier=[self.u_multiplier + attacker_multiplier_increase, self.u_multiplier + attacker_multiplier_increase] if not self.enable_shooting else [self.u_multiplier + attacker_multiplier_increase, self.u_multiplier + attacker_multiplier_increase, self.u_rot_multiplier, self.u_shoot_multiplier + attacker_shoot_multiplier_decrease], max_speed=self.max_speed + attacker_speed_increase, dynamics=Holonomic() if not self.enable_shooting else HolonomicWithRotation(), action_size=2 if not self.enable_shooting else 4, color=self.blue_color, alpha=1)

        def defender(i):
            return Agent(name=f'agent_blue_{i}', shape=Sphere(radius=self.agent_size), action_script=self.blue_controller.run if self.ai_blue_agents else None, u_multiplier=[self.u_multiplier, self.u_multiplier] if not self.enable_shooting else [self.u_multiplier, self.u_multiplier, self.u_rot_multiplier, self.u_shoot_multiplier], max_speed=self.max_speed, dynamics=Holonomic() if not self.enable_shooting else HolonomicWithRotation(), action_size=2 if not self.enable_shooting else 4, color=self.blue_color, alpha=1)

        def goal_keeper(i):
            goalie_shoot_multiplier_increase = 0.2
            goalie_radius_increase = 0.01
            goalie_speed_decrease = -0.1
            goalie_multiplier_decrease = -0.05
            return Agent(name=f'agent_blue_{i}', shape=Sphere(radius=self.agent_size + goalie_radius_increase), action_script=self.blue_controller.run if self.ai_blue_agents else None, u_multiplier=[self.u_multiplier + goalie_multiplier_decrease, self.u_multiplier + goalie_multiplier_decrease] if not self.enable_shooting else [self.u_multiplier + goalie_multiplier_decrease, self.u_multiplier + goalie_multiplier_decrease, self.u_rot_multiplier + goalie_shoot_multiplier_increase, self.u_shoot_multiplier], max_speed=self.max_speed + goalie_speed_decrease, dynamics=Holonomic() if not self.enable_shooting else HolonomicWithRotation(), action_size=2 if not self.enable_shooting else 4, color=self.blue_color, alpha=1)
        agents = [attacker(0), attacker(1), defender(2), defender(3), goal_keeper(4)]
        return agents

    def reset_agents(self, env_index: int=None):
        if self.spawn_in_formation:
            self._spawn_formation(self.blue_agents, True, env_index)
            if not self.only_blue_formation:
                self._spawn_formation(self.red_agents, False, env_index)
        else:
            for agent in self.blue_agents:
                pos = self._get_random_spawn_position(blue=True, env_index=env_index)
                agent.set_pos(pos, batch_index=env_index)
        if self.spawn_in_formation and self.only_blue_formation or not self.spawn_in_formation:
            for agent in self.red_agents:
                pos = self._get_random_spawn_position(blue=False, env_index=env_index)
                agent.set_pos(pos, batch_index=env_index)
                agent.set_rot(torch.tensor([torch.pi], device=self.world.device, dtype=torch.float32), batch_index=env_index)

    def _spawn_formation(self, agents, blue, env_index):
        if self.randomise_formation_indices:
            order = torch.randperm(len(agents)).tolist()
            agents = [agents[i] for i in order]
        agent_index = 0
        endpoint = -(self.pitch_length / 2 + self.goal_depth) * (1 if blue else -1)
        for x in torch.linspace(0, endpoint, len(agents) // self.formation_agents_per_column + 3):
            if agent_index >= len(agents):
                break
            if x == 0 or x == endpoint:
                continue
            agents_this_column = agents[agent_index:agent_index + self.formation_agents_per_column]
            n_agents_this_column = len(agents_this_column)
            for y in torch.linspace(self.pitch_width / 2, -self.pitch_width / 2, n_agents_this_column + 2):
                if y == -self.pitch_width / 2 or y == self.pitch_width / 2:
                    continue
                pos = torch.tensor([x, y], device=self.world.device, dtype=torch.float32)
                if env_index is None:
                    pos = pos.expand(self.world.batch_dim, self.world.dim_p)
                agents[agent_index].set_pos(pos + (torch.rand((self.world.dim_p,) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device) - 0.5) * self.formation_noise, batch_index=env_index)
                agent_index += 1

    def _get_random_spawn_position(self, blue, env_index):
        return torch.rand((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device) * self._reset_agent_range + (self._reset_agent_offset_blue if blue else self._reset_agent_offset_red)

    def reset_controllers(self, env_index: int=None):
        if self.red_controller is not None:
            if not self.red_controller.initialised:
                self.red_controller.init(self.world)
            self.red_controller.reset(env_index)
        if self.blue_controller is not None:
            if not self.blue_controller.initialised:
                self.blue_controller.init(self.world)
            self.blue_controller.reset(env_index)

    def init_ball(self, world):
        ball = Agent(name='Ball', shape=Sphere(radius=self.ball_size), action_script=ball_action_script, max_speed=self.ball_max_speed, mass=self.ball_mass, alpha=1, color=Color.BLACK)
        ball.pos_rew_blue = torch.zeros(world.batch_dim, device=world.device, dtype=torch.float32)
        ball.pos_rew_red = ball.pos_rew_blue.clone()
        ball.pos_rew_agent_blue = ball.pos_rew_blue.clone()
        ball.pos_rew_agent_red = ball.pos_rew_red.clone()
        ball.kicking_action = torch.zeros(world.batch_dim, world.dim_p, device=world.device, dtype=torch.float32)
        world.add_agent(ball)
        world.ball = ball
        self.ball = ball

    def reset_ball(self, env_index: int=None):
        if not self.ai_blue_agents:
            min_agent_dist_to_ball_blue = self.get_closest_agent_to_ball(self.blue_agents, env_index)
            if env_index is None:
                self.min_agent_dist_to_ball_blue = min_agent_dist_to_ball_blue
            else:
                self.min_agent_dist_to_ball_blue[env_index] = min_agent_dist_to_ball_blue
        if not self.ai_red_agents:
            min_agent_dist_to_ball_red = self.get_closest_agent_to_ball(self.red_agents, env_index)
            if env_index is None:
                self.min_agent_dist_to_ball_red = min_agent_dist_to_ball_red
            else:
                self.min_agent_dist_to_ball_red[env_index] = min_agent_dist_to_ball_red
        if env_index is None:
            if not self.ai_blue_agents:
                self.ball.pos_shaping_blue = torch.linalg.vector_norm(self.ball.state.pos - self.right_goal_pos, dim=-1) * self.pos_shaping_factor_ball_goal
                self.ball.pos_shaping_agent_blue = self.min_agent_dist_to_ball_blue * self.pos_shaping_factor_agent_ball
            if not self.ai_red_agents:
                self.ball.pos_shaping_red = torch.linalg.vector_norm(self.ball.state.pos - self.left_goal_pos, dim=-1) * self.pos_shaping_factor_ball_goal
                self.ball.pos_shaping_agent_red = self.min_agent_dist_to_ball_red * self.pos_shaping_factor_agent_ball
            if self.enable_shooting:
                self.ball.kicking_action[:] = 0.0
        else:
            if not self.ai_blue_agents:
                self.ball.pos_shaping_blue[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.right_goal_pos) * self.pos_shaping_factor_ball_goal
                self.ball.pos_shaping_agent_blue[env_index] = self.min_agent_dist_to_ball_blue[env_index] * self.pos_shaping_factor_agent_ball
            if not self.ai_red_agents:
                self.ball.pos_shaping_red[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.left_goal_pos) * self.pos_shaping_factor_ball_goal
                self.ball.pos_shaping_agent_red[env_index] = self.min_agent_dist_to_ball_red[env_index] * self.pos_shaping_factor_agent_ball
            if self.enable_shooting:
                self.ball.kicking_action[env_index] = 0.0

    def get_closest_agent_to_ball(self, team, env_index):
        pos = torch.stack([a.state.pos for a in team], dim=-2)
        ball_pos = self.ball.state.pos.unsqueeze(-2)
        if isinstance(env_index, int):
            pos = pos[env_index].unsqueeze(0)
            ball_pos = ball_pos[env_index].unsqueeze(0)
        dist = torch.cdist(pos, ball_pos)
        dist = dist.squeeze(-1)
        min_dist = dist.min(dim=-1)[0]
        if isinstance(env_index, int):
            min_dist = min_dist.squeeze(0)
        return min_dist

    def init_background(self):
        self.background = Landmark(name='Background', collide=False, movable=False, shape=Box(length=self.pitch_length, width=self.pitch_width), color=Color.GREEN)
        self.centre_circle_outer = Landmark(name='Centre Circle Outer', collide=False, movable=False, shape=Sphere(radius=self.goal_size / 2), color=Color.WHITE)
        self.centre_circle_inner = Landmark(name='Centre Circle Inner', collide=False, movable=False, shape=Sphere(self.goal_size / 2 - 0.02), color=Color.GREEN)
        centre_line = Landmark(name='Centre Line', collide=False, movable=False, shape=Line(length=self.pitch_width - 2 * self.agent_size), color=Color.WHITE)
        right_line = Landmark(name='Right Line', collide=False, movable=False, shape=Line(length=self.pitch_width - 2 * self.agent_size), color=Color.WHITE)
        left_line = Landmark(name='Left Line', collide=False, movable=False, shape=Line(length=self.pitch_width - 2 * self.agent_size), color=Color.WHITE)
        top_line = Landmark(name='Top Line', collide=False, movable=False, shape=Line(length=self.pitch_length - 2 * self.agent_size), color=Color.WHITE)
        bottom_line = Landmark(name='Bottom Line', collide=False, movable=False, shape=Line(length=self.pitch_length - 2 * self.agent_size), color=Color.WHITE)
        self.background_entities = [self.background, self.centre_circle_outer, self.centre_circle_inner, centre_line, right_line, left_line, top_line, bottom_line]

    def render_field(self, render: bool):
        self._render_field = render
        self.left_top_wall.is_rendering[:] = render
        self.left_bottom_wall.is_rendering[:] = render
        self.right_top_wall.is_rendering[:] = render
        self.right_bottom_wall.is_rendering[:] = render

    def init_walls(self, world):
        self.right_top_wall = Landmark(name='Right Top Wall', collide=True, movable=False, shape=Line(length=self.pitch_width / 2 - self.agent_size - self.goal_size / 2), color=Color.WHITE)
        world.add_landmark(self.right_top_wall)
        self.left_top_wall = Landmark(name='Left Top Wall', collide=True, movable=False, shape=Line(length=self.pitch_width / 2 - self.agent_size - self.goal_size / 2), color=Color.WHITE)
        world.add_landmark(self.left_top_wall)
        self.right_bottom_wall = Landmark(name='Right Bottom Wall', collide=True, movable=False, shape=Line(length=self.pitch_width / 2 - self.agent_size - self.goal_size / 2), color=Color.WHITE)
        world.add_landmark(self.right_bottom_wall)
        self.left_bottom_wall = Landmark(name='Left Bottom Wall', collide=True, movable=False, shape=Line(length=self.pitch_width / 2 - self.agent_size - self.goal_size / 2), color=Color.WHITE)
        world.add_landmark(self.left_bottom_wall)

    def reset_walls(self, env_index: int=None):
        for landmark in self.world.landmarks:
            if landmark.name == 'Left Top Wall':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2, self.pitch_width / 4 + self.goal_size / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Left Bottom Wall':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2, -self.pitch_width / 4 - self.goal_size / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Right Top Wall':
                landmark.set_pos(torch.tensor([self.pitch_length / 2, self.pitch_width / 4 + self.goal_size / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Right Bottom Wall':
                landmark.set_pos(torch.tensor([self.pitch_length / 2, -self.pitch_width / 4 - self.goal_size / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)

    def init_goals(self, world):
        right_goal_back = Landmark(name='Right Goal Back', collide=True, movable=False, shape=Line(length=self.goal_size), color=Color.WHITE)
        world.add_landmark(right_goal_back)
        left_goal_back = Landmark(name='Left Goal Back', collide=True, movable=False, shape=Line(length=self.goal_size), color=Color.WHITE)
        world.add_landmark(left_goal_back)
        right_goal_top = Landmark(name='Right Goal Top', collide=True, movable=False, shape=Line(length=self.goal_depth), color=Color.WHITE)
        world.add_landmark(right_goal_top)
        left_goal_top = Landmark(name='Left Goal Top', collide=True, movable=False, shape=Line(length=self.goal_depth), color=Color.WHITE)
        world.add_landmark(left_goal_top)
        right_goal_bottom = Landmark(name='Right Goal Bottom', collide=True, movable=False, shape=Line(length=self.goal_depth), color=Color.WHITE)
        world.add_landmark(right_goal_bottom)
        left_goal_bottom = Landmark(name='Left Goal Bottom', collide=True, movable=False, shape=Line(length=self.goal_depth), color=Color.WHITE)
        world.add_landmark(left_goal_bottom)
        blue_net = Landmark(name='Blue Net', collide=False, movable=False, shape=Box(length=self.goal_depth, width=self.goal_size), color=(0.5, 0.5, 0.5, 0.5))
        world.add_landmark(blue_net)
        red_net = Landmark(name='Red Net', collide=False, movable=False, shape=Box(length=self.goal_depth, width=self.goal_size), color=(0.5, 0.5, 0.5, 0.5))
        world.add_landmark(red_net)
        self.blue_net = blue_net
        self.red_net = red_net
        world.blue_net = blue_net
        world.red_net = red_net

    def reset_goals(self, env_index: int=None):
        for landmark in self.world.landmarks:
            if landmark.name == 'Left Goal Back':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2 - self.goal_depth + self.agent_size, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Right Goal Back':
                landmark.set_pos(torch.tensor([self.pitch_length / 2 + self.goal_depth - self.agent_size, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Left Goal Top':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2 - self.goal_depth / 2 + self.agent_size, self.goal_size / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Left Goal Bottom':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2 - self.goal_depth / 2 + self.agent_size, -self.goal_size / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Right Goal Top':
                landmark.set_pos(torch.tensor([self.pitch_length / 2 + self.goal_depth / 2 - self.agent_size, self.goal_size / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Right Goal Bottom':
                landmark.set_pos(torch.tensor([self.pitch_length / 2 + self.goal_depth / 2 - self.agent_size, -self.goal_size / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Red Net':
                landmark.set_pos(torch.tensor([self.pitch_length / 2 + self.goal_depth / 2 - self.agent_size / 2, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            elif landmark.name == 'Blue Net':
                landmark.set_pos(torch.tensor([-self.pitch_length / 2 - self.goal_depth / 2 + self.agent_size / 2, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)

    def init_traj_pts(self, world):
        world.traj_points = {'Red': {}, 'Blue': {}}
        if self.ai_red_agents:
            for i, agent in enumerate(world.red_agents):
                world.traj_points['Red'][agent] = []
                for j in range(self.n_traj_points):
                    pointj = Landmark(name='Red {agent} Trajectory {pt}'.format(agent=i, pt=j), collide=False, movable=False, shape=Sphere(radius=0.01), color=Color.GRAY)
                    world.add_landmark(pointj)
                    world.traj_points['Red'][agent].append(pointj)
        if self.ai_blue_agents:
            for i, agent in enumerate(world.blue_agents):
                world.traj_points['Blue'][agent] = []
                for j in range(self.n_traj_points):
                    pointj = Landmark(name='Blue {agent} Trajectory {pt}'.format(agent=i, pt=j), collide=False, movable=False, shape=Sphere(radius=0.01), color=Color.GRAY)
                    world.add_landmark(pointj)
                    world.traj_points['Blue'][agent].append(pointj)

    def process_action(self, agent: Agent):
        if agent is self.ball:
            return
        blue = agent in self.blue_agents
        if agent.action_script is None and (not blue):
            agent.action.u[..., X] = -agent.action.u[..., X]
            if self.enable_shooting:
                agent.action.u[..., 2] = -agent.action.u[..., 2]
        if self.enable_shooting and agent.action_script is None:
            agents_exclude_ball = [a for a in self.world.agents if a is not self.ball]
            if self._agents_rel_pos_to_ball is None:
                self._agents_rel_pos_to_ball = torch.stack([self.ball.state.pos - a.state.pos for a in agents_exclude_ball], dim=1)
                self._agent_dist_to_ball = torch.linalg.vector_norm(self._agents_rel_pos_to_ball, dim=-1)
                self._agents_closest_to_ball = self._agent_dist_to_ball == self._agent_dist_to_ball.min(dim=-1, keepdim=True)[0]
            agent_index = agents_exclude_ball.index(agent)
            rel_pos = self._agents_rel_pos_to_ball[:, agent_index]
            agent.ball_within_range = self._agent_dist_to_ball[:, agent_index] <= self.shooting_radius
            rel_pos_angle = torch.atan2(rel_pos[:, Y], rel_pos[:, X])
            a = (agent.state.rot.squeeze(-1) - rel_pos_angle + torch.pi) % (2 * torch.pi) - torch.pi
            agent.ball_within_angle = (-self.shooting_angle / 2 <= a) * (a <= self.shooting_angle / 2)
            shoot_force = torch.zeros(self.world.batch_dim, 2, device=self.world.device, dtype=torch.float32)
            shoot_force[..., X] = agent.action.u[..., -1] * 2.67 * self.u_shoot_multiplier
            shoot_force = TorchUtils.rotate_vector(shoot_force, agent.state.rot)
            agent.shoot_force = shoot_force
            shoot_force = torch.where((agent.ball_within_angle * agent.ball_within_range * self._agents_closest_to_ball[:, agent_index]).unsqueeze(-1), shoot_force, 0.0)
            self.ball.kicking_action += shoot_force
            agent.action.u = agent.action.u[:, :-1]

    def pre_step(self):
        if self.enable_shooting:
            self._agents_rel_pos_to_ball = None
            self.ball.action.u += self.ball.kicking_action
            self.ball.kicking_action[:] = 0

    def reward(self, agent: Agent):
        if agent is None or agent == self.world.agents[0]:
            over_right_line = self.ball.state.pos[:, X] > self.pitch_length / 2 + self.ball_size / 2
            over_left_line = self.ball.state.pos[:, X] < -self.pitch_length / 2 - self.ball_size / 2
            goal_mask = (self.ball.state.pos[:, Y] <= self.goal_size / 2) * (self.ball.state.pos[:, Y] >= -self.goal_size / 2)
            blue_score = over_right_line * goal_mask
            red_score = over_left_line * goal_mask
            self._sparse_reward_blue = self.scoring_reward * blue_score - self.scoring_reward * red_score
            self._sparse_reward_red = -self._sparse_reward_blue
            self._done = blue_score | red_score
            self._dense_reward_blue = 0
            self._dense_reward_red = 0
            if self.dense_reward and agent is not None:
                if not self.ai_blue_agents:
                    self._dense_reward_blue = self.reward_ball_to_goal(blue=True) + self.reward_all_agent_to_ball(blue=True)
                if not self.ai_red_agents:
                    self._dense_reward_red = self.reward_ball_to_goal(blue=False) + self.reward_all_agent_to_ball(blue=False)
        blue = agent in self.blue_agents
        if blue:
            reward = self._sparse_reward_blue + self._dense_reward_blue
        else:
            reward = self._sparse_reward_red + self._dense_reward_red
        return reward

    def reward_ball_to_goal(self, blue: bool):
        if blue:
            self.ball.distance_to_goal_blue = torch.linalg.vector_norm(self.ball.state.pos - self.right_goal_pos, dim=-1)
            distance_to_goal = self.ball.distance_to_goal_blue
        else:
            self.ball.distance_to_goal_red = torch.linalg.vector_norm(self.ball.state.pos - self.left_goal_pos, dim=-1)
            distance_to_goal = self.ball.distance_to_goal_red
        pos_shaping = distance_to_goal * self.pos_shaping_factor_ball_goal
        if blue:
            self.ball.pos_rew_blue = self.ball.pos_shaping_blue - pos_shaping
            self.ball.pos_shaping_blue = pos_shaping
            pos_rew = self.ball.pos_rew_blue
        else:
            self.ball.pos_rew_red = self.ball.pos_shaping_red - pos_shaping
            self.ball.pos_shaping_red = pos_shaping
            pos_rew = self.ball.pos_rew_red
        return pos_rew

    def reward_all_agent_to_ball(self, blue: bool):
        min_dist_to_ball = self.get_closest_agent_to_ball(team=self.blue_agents if blue else self.red_agents, env_index=None)
        if blue:
            self.min_agent_dist_to_ball_blue = min_dist_to_ball
        else:
            self.min_agent_dist_to_ball_red = min_dist_to_ball
        pos_shaping = min_dist_to_ball * self.pos_shaping_factor_agent_ball
        ball_moving = torch.linalg.vector_norm(self.ball.state.vel, dim=-1) > 1e-06
        agent_close_to_goal = min_dist_to_ball < self.distance_to_ball_trigger
        if blue:
            self.ball.pos_rew_agent_blue = torch.where(agent_close_to_goal + ball_moving, 0.0, self.ball.pos_shaping_agent_blue - pos_shaping)
            self.ball.pos_shaping_agent_blue = pos_shaping
            pos_rew_agent = self.ball.pos_rew_agent_blue
        else:
            self.ball.pos_rew_agent_red = torch.where(agent_close_to_goal + ball_moving, 0.0, self.ball.pos_shaping_agent_red - pos_shaping)
            self.ball.pos_shaping_agent_red = pos_shaping
            pos_rew_agent = self.ball.pos_rew_agent_red
        return pos_rew_agent

    def observation(self, agent: Agent, agent_pos=None, agent_rot=None, agent_vel=None, agent_force=None, teammate_poses=None, teammate_forces=None, teammate_vels=None, adversary_poses=None, adversary_forces=None, adversary_vels=None, ball_pos=None, ball_vel=None, ball_force=None, blue=None, env_index=Ellipsis):
        if blue:
            assert agent in self.blue_agents
        else:
            blue = agent in self.blue_agents
        if not blue:
            my_team, other_team = (self.red_agents, self.blue_agents)
            goal_pos = self.left_goal_pos
        else:
            my_team, other_team = (self.blue_agents, self.red_agents)
            goal_pos = self.right_goal_pos
        actual_adversary_poses = []
        actual_adversary_forces = []
        actual_adversary_vels = []
        if self.observe_adversaries:
            for a in other_team:
                actual_adversary_poses.append(a.state.pos[env_index])
                actual_adversary_vels.append(a.state.vel[env_index])
                actual_adversary_forces.append(a.state.force[env_index])
        actual_teammate_poses = []
        actual_teammate_forces = []
        actual_teammate_vels = []
        if self.observe_teammates:
            for a in my_team:
                if a != agent:
                    actual_teammate_poses.append(a.state.pos[env_index])
                    actual_teammate_vels.append(a.state.vel[env_index])
                    actual_teammate_forces.append(a.state.force[env_index])
        obs = self.observation_base(agent.state.pos[env_index] if agent_pos is None else agent_pos, agent.state.rot[env_index] if agent_rot is None else agent_rot, agent.state.vel[env_index] if agent_vel is None else agent_vel, agent.state.force[env_index] if agent_force is None else agent_force, goal_pos=goal_pos, ball_pos=self.ball.state.pos[env_index] if ball_pos is None else ball_pos, ball_vel=self.ball.state.vel[env_index] if ball_vel is None else ball_vel, ball_force=self.ball.state.force[env_index] if ball_force is None else ball_force, adversary_poses=actual_adversary_poses if adversary_poses is None else adversary_poses, adversary_forces=actual_adversary_forces if adversary_forces is None else adversary_forces, adversary_vels=actual_adversary_vels if adversary_vels is None else adversary_vels, teammate_poses=actual_teammate_poses if teammate_poses is None else teammate_poses, teammate_forces=actual_teammate_forces if teammate_forces is None else teammate_forces, teammate_vels=actual_teammate_vels if teammate_vels is None else teammate_vels, blue=blue)
        return obs

    def observation_base(self, agent_pos, agent_rot, agent_vel, agent_force, teammate_poses, teammate_forces, teammate_vels, adversary_poses, adversary_forces, adversary_vels, ball_pos, ball_vel, ball_force, goal_pos, blue: bool):
        input = [agent_pos, agent_rot, agent_vel, agent_force, ball_pos, ball_vel, ball_force, goal_pos, teammate_poses, teammate_forces, teammate_vels, adversary_poses, adversary_forces, adversary_vels]
        for o in input:
            if isinstance(o, Tensor) and len(o.shape) > 1:
                batch_dim = o.shape[0]
                break
        for j in range(len(input)):
            if isinstance(input[j], Tensor):
                if len(input[j].shape) == 1:
                    input[j] = input[j].unsqueeze(0).expand(batch_dim, *input[j].shape)
                input[j] = input[j].clone()
            else:
                o = input[j]
                for i in range(len(o)):
                    if len(o[i].shape) == 1:
                        o[i] = o[i].unsqueeze(0).expand(batch_dim, *o[i].shape)
                    o[i] = o[i].clone()
        agent_pos, agent_rot, agent_vel, agent_force, ball_pos, ball_vel, ball_force, goal_pos, teammate_poses, teammate_forces, teammate_vels, adversary_poses, adversary_forces, adversary_vels = input
        if not blue:
            for tensor in [agent_pos, agent_vel, agent_force, ball_pos, ball_vel, ball_force, goal_pos] + teammate_poses + teammate_forces + teammate_vels + adversary_poses + adversary_forces + adversary_vels:
                tensor[..., X] = -tensor[..., X]
            agent_rot = agent_rot - torch.pi
        obs = {'obs': [agent_force, agent_pos - ball_pos, agent_vel - ball_vel, ball_pos - goal_pos, ball_vel, ball_force], 'pos': [agent_pos - goal_pos], 'vel': [agent_vel]}
        if self.enable_shooting:
            obs['obs'].append(agent_rot)
        if self.observe_adversaries and len(adversary_poses):
            obs['adversaries'] = []
            for adversary_pos, adversary_force, adversary_vel in zip(adversary_poses, adversary_forces, adversary_vels):
                obs['adversaries'].append(torch.cat([agent_pos - adversary_pos, agent_vel - adversary_vel, adversary_vel, adversary_force], dim=-1))
            obs['adversaries'] = [torch.stack(obs['adversaries'], dim=-2) if self.dict_obs else torch.cat(obs['adversaries'], dim=-1)]
        if self.observe_teammates:
            obs['teammates'] = []
            for teammate_pos, teammate_force, teammate_vel in zip(teammate_poses, teammate_forces, teammate_vels):
                obs['teammates'].append(torch.cat([agent_pos - teammate_pos, agent_vel - teammate_vel, teammate_vel, teammate_force], dim=-1))
            obs['teammates'] = [torch.stack(obs['teammates'], dim=-2) if self.dict_obs else torch.cat(obs['teammates'], dim=-1)]
        for key, value in obs.items():
            obs[key] = torch.cat(value, dim=-1)
        if self.dict_obs:
            return obs
        else:
            return torch.cat(list(obs.values()), dim=-1)

    def done(self):
        if self.ai_blue_agents and self.ai_red_agents:
            self.reward(None)
        return self._done

    def _compute_coverage(self, blue: bool, env_index=None):
        team = self.blue_agents if blue else self.red_agents
        pos = torch.stack([a.state.pos for a in team], dim=-2)
        avg_point = pos.mean(-2).unsqueeze(-2)
        if isinstance(env_index, int):
            pos = pos[env_index].unsqueeze(0)
            avg_point = avg_point[env_index].unsqueeze(0)
        dist = torch.cdist(pos, avg_point)
        dist = dist.squeeze(-1)
        max_dist = dist.max(dim=-1)[0]
        if isinstance(env_index, int):
            max_dist = max_dist.squeeze(0)
        return max_dist

    def info(self, agent: Agent):
        blue = agent in self.blue_agents
        info = {'sparse_reward': self._sparse_reward_blue if blue else self._sparse_reward_red, 'ball_goal_pos_rew': self.ball.pos_rew_blue if blue else self.ball.pos_rew_red, 'all_agent_ball_pos_rew': self.ball.pos_rew_agent_blue if blue else self.ball.pos_rew_agent_red, 'ball_pos': self.ball.state.pos, 'dist_ball_to_goal': (self.ball.pos_shaping_blue if blue else self.ball.pos_shaping_red) / self.pos_shaping_factor_ball_goal}
        if blue and self.min_agent_dist_to_ball_blue is not None:
            info['min_agent_dist_to_ball'] = self.min_agent_dist_to_ball_blue
            info['touching_ball'] = self.min_agent_dist_to_ball_blue <= self.agent_size + self.ball_size + 0.01
        elif not blue and self.min_agent_dist_to_ball_red is not None:
            info['min_agent_dist_to_ball'] = self.min_agent_dist_to_ball_red
            info['touching_ball'] = self.min_agent_dist_to_ball_red <= self.agent_size + self.ball_size + 0.01
        return info

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        from vmas.simulator.rendering import Geom
        geoms: List[Geom] = self._get_background_geoms(self.background_entities) if self._render_field else self._get_background_geoms(self.background_entities[3:])
        geoms += ScenarioUtils.render_agent_indices(self, env_index, start_from=1, exclude=self.red_agents + [self.ball])
        if self.enable_shooting:
            for agent in self.blue_agents:
                color = agent.color
                if agent.ball_within_angle[env_index] and agent.ball_within_range[env_index]:
                    color = Color.PINK.value
                sector = rendering.make_circle(radius=self.shooting_radius, angle=self.shooting_angle, filled=True)
                xform = rendering.Transform()
                xform.set_rotation(agent.state.rot[env_index])
                xform.set_translation(*agent.state.pos[env_index])
                sector.add_attr(xform)
                sector.set_color(*color, alpha=agent._alpha / 2)
                geoms.append(sector)
                shoot_intensity = torch.linalg.vector_norm(agent.shoot_force[env_index]) / (self.u_shoot_multiplier * 2)
                l, r, t, b = (0, self.shooting_radius * shoot_intensity, self.agent_size / 2, -self.agent_size / 2)
                line = rendering.make_polygon([(l, b), (l, t), (r, t), (r, b)])
                xform = rendering.Transform()
                xform.set_rotation(agent.state.rot[env_index])
                xform.set_translation(*agent.state.pos[env_index])
                line.add_attr(xform)
                line.set_color(*color, alpha=agent._alpha)
                geoms.append(line)
        return geoms

    def _get_background_geoms(self, objects):

        def _get_geom(entity, pos, rot=0.0):
            from vmas.simulator import rendering
            geom = entity.shape.get_geometry()
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(*pos)
            xform.set_rotation(rot)
            color = entity.color
            geom.set_color(*color)
            return geom
        geoms = []
        for landmark in objects:
            if landmark.name == 'Centre Line':
                geoms.append(_get_geom(landmark, [0.0, 0.0], torch.pi / 2))
            elif landmark.name == 'Right Line':
                geoms.append(_get_geom(landmark, [self.pitch_length / 2 - self.agent_size, 0.0], torch.pi / 2))
            elif landmark.name == 'Left Line':
                geoms.append(_get_geom(landmark, [-self.pitch_length / 2 + self.agent_size, 0.0], torch.pi / 2))
            elif landmark.name == 'Top Line':
                geoms.append(_get_geom(landmark, [0.0, self.pitch_width / 2 - self.agent_size]))
            elif landmark.name == 'Bottom Line':
                geoms.append(_get_geom(landmark, [0.0, -self.pitch_width / 2 + self.agent_size]))
            else:
                geoms.append(_get_geom(landmark, [0, 0]))
        return geoms

def reset_controllers(self, env_index: int=None):
    if self.red_controller is not None:
        if not self.red_controller.initialised:
            self.red_controller.init(self.world)
        self.red_controller.reset(env_index)
    if self.blue_controller is not None:
        if not self.blue_controller.initialised:
            self.blue_controller.init(self.world)
        self.blue_controller.reset(env_index)

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

def dribble_to_goal(self, agent, env_index=Ellipsis):
    self.dribble(agent, self.target_net.state.pos[env_index], env_index=env_index)

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

class HeuristicPolicy(BaseHeuristicPolicy):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookahead = 0.0
        self.start_vel_dist_from_target_ratio = 0.5
        self.start_vel_behind_ratio = 0.5
        self.start_vel_mag = 1.0
        self.hit_vel_mag = 1.0
        self.package_radius = 0.15 / 2
        self.agent_radius = -0.02
        self.dribble_slowdown_dist = 0.0
        self.speed = 0.95

    def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
        self.n_env = observation.shape[0]
        self.device = observation.device
        agent_pos = observation[:, :2]
        package_pos = observation[:, 6:8] + agent_pos
        goal_pos = -observation[:, 4:6] + package_pos
        control = self.dribble(agent_pos, package_pos, goal_pos)
        control *= self.speed * u_range
        return torch.clamp(control, -u_range, u_range)

    def dribble(self, agent_pos, package_pos, goal_pos, agent_vel=None):
        package_disp = goal_pos - package_pos
        ball_dist = package_disp.norm(dim=-1)
        direction = package_disp / ball_dist[:, None]
        hit_pos = package_pos - direction * (self.package_radius + self.agent_radius)
        hit_vel = direction * self.hit_vel_mag
        start_vel = self.get_start_vel(hit_pos, hit_vel, agent_pos, self.start_vel_mag * 2)
        slowdown_mask = ball_dist <= self.dribble_slowdown_dist
        hit_vel[slowdown_mask, :] *= ball_dist[slowdown_mask, None] / self.dribble_slowdown_dist
        return self.get_action(target_pos=hit_pos, target_vel=hit_vel, curr_pos=agent_pos, curr_vel=agent_vel, start_vel=start_vel)

    def hermite(self, p0, p1, p0dot, p1dot, u=0.0, deriv=0):
        u = u.reshape((-1,))
        U = torch.stack([self.nPr(3, deriv) * u ** max(0, 3 - deriv), self.nPr(2, deriv) * u ** max(0, 2 - deriv), self.nPr(1, deriv) * u ** max(0, 1 - deriv), self.nPr(0, deriv) * u ** 0], dim=1).float()
        A = torch.tensor([[2.0, -2.0, 1.0, 1.0], [-3.0, 3.0, -2.0, -1.0], [0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0]], device=U.device)
        P = torch.stack([p0, p1, p0dot, p1dot], dim=1)
        ans = U[:, None, :] @ A[None, :, :] @ P
        ans = ans.squeeze(1)
        return ans

    def nPr(self, n, r):
        if r > n:
            return 0
        ans = 1
        for k in range(n, max(1, n - r), -1):
            ans = ans * k
        return ans

    def get_start_vel(self, pos, vel, start_pos, start_vel_mag):
        start_vel_mag = torch.as_tensor(start_vel_mag, device=self.device).view(-1)
        goal_disp = pos - start_pos
        goal_dist = goal_disp.norm(dim=-1)
        vel_mag = vel.norm(dim=-1)
        vel_dir = vel.clone()
        vel_dir[vel_mag > 0] /= vel_mag[vel_mag > 0, None]
        goal_dir = goal_disp / goal_dist[:, None]
        vel_dir_normal = torch.stack([-vel_dir[:, 1], vel_dir[:, 0]], dim=1)
        dot_prod = (goal_dir * vel_dir_normal).sum(dim=1)
        vel_dir_normal[dot_prod > 0, :] *= -1
        dist_behind_target = self.start_vel_dist_from_target_ratio * goal_dist
        point_dir = -vel_dir * self.start_vel_behind_ratio + vel_dir_normal * (1 - self.start_vel_behind_ratio)
        target_pos = pos + point_dir * dist_behind_target[:, None]
        target_disp = target_pos - start_pos
        target_dist = target_disp.norm(dim=1)
        start_vel_aug_dir = target_disp
        start_vel_aug_dir[target_dist > 0] /= target_dist[target_dist > 0, None]
        start_vel = start_vel_aug_dir * start_vel_mag[:, None]
        return start_vel

    def get_action(self, target_pos, target_vel=None, start_pos=None, start_vel=None, curr_pos=None, curr_vel=None):
        if curr_pos is None:
            curr_pos = torch.zeros(target_pos.shape, device=self.device)
        if curr_vel is None:
            curr_vel = torch.zeros(target_pos.shape, device=self.device)
        if start_pos is None:
            start_pos = curr_pos
        if target_vel is None:
            target_vel = torch.zeros(target_pos.shape, device=self.device)
        if start_vel is None:
            start_vel = self.get_start_vel(target_pos, target_vel, start_pos, self.start_vel_mag * 2)
        u_start = torch.ones(curr_pos.shape[0], device=self.device) * self.lookahead
        des_curr_pos = self.hermite(start_pos, target_pos, start_vel, target_vel, u=u_start, deriv=0)
        des_curr_vel = self.hermite(start_pos, target_pos, start_vel, target_vel, u=u_start, deriv=1)
        des_curr_pos = torch.as_tensor(des_curr_pos, device=self.device)
        des_curr_vel = torch.as_tensor(des_curr_vel, device=self.device)
        control = 0.5 * (des_curr_pos - curr_pos) + 0.5 * (des_curr_vel - curr_vel)
        return control

def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
    self.n_env = observation.shape[0]
    self.device = observation.device
    agent_pos = observation[:, :2]
    package_pos = observation[:, 6:8] + agent_pos
    goal_pos = -observation[:, 4:6] + package_pos
    control = self.dribble(agent_pos, package_pos, goal_pos)
    control *= self.speed * u_range
    return torch.clamp(control, -u_range, u_range)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        """
        Drone example scenario
        Run this file to try it out.

        You can control the three input torques using left/right arrows, up/down arrows, and m/n.
        """
        self.plot_grid = True
        self.n_agents = kwargs.pop('n_agents', 2)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device, substeps=10)
        for i in range(self.n_agents):
            agent = Agent(name=f'drone_{i}', collide=True, render_action=True, u_range=[1e-05, 1e-05, 1e-05], u_multiplier=[1, 1, 1], action_size=3, dynamics=Drone(world, integration='rk4'))
            world.add_agent(agent)
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

    def reward(self, agent: Agent):
        return torch.zeros(self.world.batch_dim, device=self.world.device)

    def process_action(self, agent: Agent):
        torque = agent.action.u
        thrust = torch.full((self.world.batch_dim, 1), agent.mass * agent.dynamics.g, device=self.world.device)
        agent.action.u = torch.cat([thrust, torque], dim=-1)

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel]
        return torch.cat(observations, dim=-1)

    def done(self):
        return torch.any(torch.stack([agent.dynamics.needs_reset() for agent in self.world.agents], dim=-1), dim=-1)

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        geoms: List[Geom] = []
        for agent in self.world.agents:
            geoms.append(ScenarioUtils.plot_entity_rotation(agent, env_index, length=0.1))
        return geoms

def done(self):
    return torch.any(torch.stack([agent.dynamics.needs_reset() for agent in self.world.agents], dim=-1), dim=-1)

def env_creator(config: Dict):
    env = make_env(scenario=config['scenario_name'], num_envs=config['num_envs'], device=config['device'], continuous_actions=config['continuous_actions'], wrapper=Wrapper.RLLIB, max_steps=config['max_steps'], **config['scenario_config'])
    return env

def use_vmas_env(render: bool=False, save_render: bool=False, num_envs: int=32, n_steps: int=100, random_action: bool=False, device: str='cpu', scenario_name: str='waterfall', continuous_actions: bool=True, visualize_render: bool=True, dict_spaces: bool=True, **kwargs):
    """Example function to use a vmas environment

    Args:
        continuous_actions (bool): Whether the agents have continuous or discrete actions
        scenario_name (str): Name of scenario
        device (str): Torch device to use
        render (bool): Whether to render the scenario
        save_render (bool):  Whether to save render of the scenario
        num_envs (int): Number of vectorized environments
        n_steps (int): Number of steps before returning done
        random_action (bool): Use random actions or have all agents perform the down action
        visualize_render (bool, optional): Whether to visualize the render. Defaults to ``True``.
        dict_spaces (bool, optional): Weather to return obs, rewards, and infos as dictionaries with agent names.
            By default, they are lists of len # of agents
        kwargs (dict, optional): Keyword arguments to pass to the scenario

    Returns:

    """
    assert not (save_render and (not render)), 'To save the video you have to render it'
    env = make_env(scenario=scenario_name, num_envs=num_envs, device=device, continuous_actions=continuous_actions, dict_spaces=dict_spaces, wrapper=None, seed=None, **kwargs)
    frame_list = []
    init_time = time.time()
    step = 0
    for _ in range(n_steps):
        step += 1
        print(f'Step {step}')
        dict_actions = random.choice([True, False])
        actions = {} if dict_actions else []
        for agent in env.agents:
            if not random_action:
                action = _get_deterministic_action(agent, continuous_actions, env)
            else:
                action = env.get_random_action(agent)
            if dict_actions:
                actions.update({agent.name: action})
            else:
                actions.append(action)
        obs, rews, dones, info = env.step(actions)
        if render:
            frame = env.render(mode='rgb_array', agent_index_focus=None, visualize_when_rgb=visualize_render)
            if save_render:
                frame_list.append(frame)
    total_time = time.time() - init_time
    print(f'It took: {total_time}s for {n_steps} steps of {num_envs} parallel environments on device {device} for {scenario_name} scenario.')
    if render and save_render:
        save_video(scenario_name, frame_list, fps=1 / env.scenario.world.dt)

def run_heuristic(scenario_name: str, heuristic: Type[BaseHeuristicPolicy]=RandomPolicy, n_steps: int=200, n_envs: int=32, env_kwargs: dict=None, render: bool=False, save_render: bool=False, device: str='cpu'):
    assert not (save_render and (not render)), 'To save the video you have to render it'
    if env_kwargs is None:
        env_kwargs = {}
    policy = heuristic(continuous_action=True)
    env = make_env(scenario=scenario_name, num_envs=n_envs, device=device, continuous_actions=True, wrapper=None, **env_kwargs)
    frame_list = []
    init_time = time.time()
    step = 0
    obs = env.reset()
    total_reward = 0
    for _ in range(n_steps):
        step += 1
        actions = [None] * len(obs)
        for i in range(len(obs)):
            actions[i] = policy.compute_action(obs[i], u_range=env.agents[i].u_range)
        obs, rews, dones, info = env.step(actions)
        rewards = torch.stack(rews, dim=1)
        global_reward = rewards.mean(dim=1)
        mean_global_reward = global_reward.mean(dim=0)
        total_reward += mean_global_reward
        if render:
            frame_list.append(env.render(mode='rgb_array', agent_index_focus=None, visualize_when_rgb=True))
    total_time = time.time() - init_time
    if render and save_render:
        save_video(scenario_name, frame_list, 1 / env.scenario.world.dt)
    print(f'It took: {total_time}s for {n_steps} steps of {n_envs} parallel environments on device {device}\nThe average total reward was {total_reward}')

class TorchUtils:

    @staticmethod
    def clamp_with_norm(tensor: Tensor, max_norm: float):
        norm = torch.linalg.vector_norm(tensor, dim=-1)
        new_tensor = tensor / norm.unsqueeze(-1) * max_norm
        cond = (norm > max_norm).unsqueeze(-1).expand(tensor.shape)
        tensor = torch.where(cond, new_tensor, tensor)
        return tensor

    @staticmethod
    def rotate_vector(vector: Tensor, angle: Tensor):
        if len(angle.shape) == len(vector.shape):
            angle = angle.squeeze(-1)
        assert vector.shape[:-1] == angle.shape
        assert vector.shape[-1] == 2
        cos = torch.cos(angle)
        sin = torch.sin(angle)
        return torch.stack([vector[..., X] * cos - vector[..., Y] * sin, vector[..., X] * sin + vector[..., Y] * cos], dim=-1)

    @staticmethod
    def cross(vector_a: Tensor, vector_b: Tensor):
        return (vector_a[..., X] * vector_b[..., Y] - vector_a[..., Y] * vector_b[..., X]).unsqueeze(-1)

    @staticmethod
    def compute_torque(f: Tensor, r: Tensor) -> Tensor:
        return TorchUtils.cross(r, f)

    @staticmethod
    def to_numpy(data: Union[Tensor, Dict[str, Tensor], List[Tensor]]):
        if isinstance(data, Tensor):
            return data.cpu().detach().numpy()
        elif isinstance(data, Dict):
            return {key: TorchUtils.to_numpy(value) for key, value in data.items()}
        elif isinstance(data, Sequence):
            return [TorchUtils.to_numpy(value) for value in data]
        else:
            raise NotImplementedError(f'Invalid type of data {data}')

    @staticmethod
    def recursive_clone(value: Union[Dict[str, Tensor], Tensor]):
        if isinstance(value, Tensor):
            return value.clone()
        else:
            return {key: TorchUtils.recursive_clone(val) for key, val in value.items()}

    @staticmethod
    def recursive_require_grad_(value: Union[Dict[str, Tensor], Tensor, List[Tensor]]):
        if isinstance(value, Tensor) and torch.is_floating_point(value):
            value.requires_grad_(True)
        elif isinstance(value, Dict):
            for val in value.values():
                TorchUtils.recursive_require_grad_(val)
        else:
            for val in value:
                TorchUtils.recursive_require_grad_(val)

    @staticmethod
    def where_from_index(env_index, new_value, old_value):
        mask = torch.zeros_like(old_value, dtype=torch.bool, device=old_value.device)
        mask[env_index] = True
        return torch.where(mask, new_value, old_value)

@staticmethod
def recursive_require_grad_(value: Union[Dict[str, Tensor], Tensor, List[Tensor]]):
    if isinstance(value, Tensor) and torch.is_floating_point(value):
        value.requires_grad_(True)
    elif isinstance(value, Dict):
        for val in value.values():
            TorchUtils.recursive_require_grad_(val)
    else:
        for val in value:
            TorchUtils.recursive_require_grad_(val)

class Agent(Entity):

    def __init__(self, name: str, shape: Shape=None, movable: bool=True, rotatable: bool=True, collide: bool=True, density: float=25.0, mass: float=1.0, f_range: float=None, max_f: float=None, t_range: float=None, max_t: float=None, v_range: float=None, max_speed: float=None, color=Color.BLUE, alpha: float=0.5, obs_range: float=None, obs_noise: float=None, u_noise: Union[float, Sequence[float]]=0.0, u_range: Union[float, Sequence[float]]=1.0, u_multiplier: Union[float, Sequence[float]]=1.0, action_script: Callable[[Agent, World], None]=None, sensors: List[Sensor]=None, c_noise: float=0.0, silent: bool=True, adversary: bool=False, drag: float=None, linear_friction: float=None, angular_friction: float=None, gravity: float=None, collision_filter: Callable[[Entity], bool]=lambda _: True, render_action: bool=False, dynamics: Dynamics=None, action_size: int=None, discrete_action_nvec: List[int]=None):
        super().__init__(name, movable, rotatable, collide, density, mass, shape, v_range, max_speed, color, is_joint=False, drag=drag, linear_friction=linear_friction, angular_friction=angular_friction, gravity=gravity, collision_filter=collision_filter)
        if obs_range == 0.0:
            assert sensors is None, f'Blind agent cannot have sensors, got {sensors}'
        if action_size is not None and discrete_action_nvec is not None:
            if action_size != len(discrete_action_nvec):
                raise ValueError(f'action_size {action_size} is inconsistent with discrete_action_nvec {discrete_action_nvec}')
        if discrete_action_nvec is not None:
            if not all((n > 1 for n in discrete_action_nvec)):
                raise ValueError(f'All values in discrete_action_nvec must be greater than 1, got {discrete_action_nvec}')
        self._obs_range = obs_range
        self._obs_noise = obs_noise
        self._f_range = f_range
        self._max_f = max_f
        self._t_range = t_range
        self._max_t = max_t
        self._action_script = action_script
        self._sensors = []
        if sensors is not None:
            [self.add_sensor(sensor) for sensor in sensors]
        self._c_noise = c_noise
        self._silent = silent
        self._render_action = render_action
        self._adversary = adversary
        self._alpha = alpha
        self.dynamics = dynamics if dynamics is not None else Holonomic()
        if action_size is not None:
            self.action_size = action_size
        elif discrete_action_nvec is not None:
            self.action_size = len(discrete_action_nvec)
        else:
            self.action_size = self.dynamics.needed_action_size
        if discrete_action_nvec is None:
            self.discrete_action_nvec = [3] * self.action_size
        else:
            self.discrete_action_nvec = discrete_action_nvec
        self.dynamics.agent = self
        self._action = Action(u_range=u_range, u_multiplier=u_multiplier, u_noise=u_noise, action_size=self.action_size)
        self._state = AgentState()

    def add_sensor(self, sensor: Sensor):
        sensor.agent = self
        self._sensors.append(sensor)

    @Entity.batch_dim.setter
    def batch_dim(self, batch_dim: int):
        Entity.batch_dim.fset(self, batch_dim)
        self._action.batch_dim = batch_dim

    @property
    def action_script(self) -> Callable[[Agent, World], None]:
        return self._action_script

    def action_callback(self, world: World):
        self._action_script(self, world)
        if self._silent or world.dim_c == 0:
            assert self._action.c is None, f'Agent {self.name} should not communicate but action script communicates'
        assert self._action.u is not None, f'Action script of {self.name} should set u action'
        assert self._action.u.shape[1] == self.action_size, f'Scripted action of agent {self.name} has wrong shape'
        assert ((self._action.u / self.action.u_multiplier_tensor).abs() <= self.action.u_range_tensor).all(), f'Scripted physical action of {self.name} is out of range'

    @property
    def u_range(self):
        return self.action.u_range

    @property
    def obs_noise(self):
        return self._obs_noise if self._obs_noise is not None else 0

    @property
    def action(self) -> Action:
        return self._action

    @property
    def u_multiplier(self):
        return self.action.u_multiplier

    @property
    def max_f(self):
        return self._max_f

    @property
    def f_range(self):
        return self._f_range

    @property
    def max_t(self):
        return self._max_t

    @property
    def t_range(self):
        return self._t_range

    @property
    def silent(self):
        return self._silent

    @property
    def sensors(self) -> List[Sensor]:
        return self._sensors

    @property
    def u_noise(self):
        return self.action.u_noise

    @property
    def c_noise(self):
        return self._c_noise

    @property
    def adversary(self):
        return self._adversary

    @override(Entity)
    def _spawn(self, dim_c: int, dim_p: int):
        if dim_c == 0:
            assert self.silent, f'Agent {self.name} must be silent when world has no communication'
        if self.silent:
            dim_c = 0
        super()._spawn(dim_c, dim_p)

    @override(Entity)
    def _reset(self, env_index: int):
        self.action._reset(env_index)
        self.dynamics.reset(env_index)
        super()._reset(env_index)

    def zero_grad(self):
        self.action.zero_grad()
        self.dynamics.zero_grad()
        super().zero_grad()

    @override(Entity)
    def to(self, device: torch.device):
        super().to(device)
        self.action.to(device)
        for sensor in self.sensors:
            sensor.to(device)

    @override(Entity)
    def render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms = super().render(env_index)
        if len(geoms) == 0:
            return geoms
        for geom in geoms:
            geom.set_color(*self.color, alpha=self._alpha)
        if self._sensors is not None:
            for sensor in self._sensors:
                geoms += sensor.render(env_index=env_index)
        if self._render_action and self.state.force is not None:
            velocity = rendering.Line(self.state.pos[env_index], self.state.pos[env_index] + self.state.force[env_index] * 10 * self.shape.circumscribed_radius(), width=2)
            velocity.set_color(*self.color)
            geoms.append(velocity)
        return geoms

def action_callback(self, world: World):
    self._action_script(self, world)
    if self._silent or world.dim_c == 0:
        assert self._action.c is None, f'Agent {self.name} should not communicate but action script communicates'
    assert self._action.u is not None, f'Action script of {self.name} should set u action'
    assert self._action.u.shape[1] == self.action_size, f'Scripted action of agent {self.name} has wrong shape'
    assert ((self._action.u / self.action.u_multiplier_tensor).abs() <= self.action.u_range_tensor).all(), f'Scripted physical action of {self.name} is out of range'

class World(TorchVectorizedObject):

    def __init__(self, batch_dim: int, device: torch.device, dt: float=0.1, substeps: int=1, drag: float=DRAG, linear_friction: float=LINEAR_FRICTION, angular_friction: float=ANGULAR_FRICTION, x_semidim: float=None, y_semidim: float=None, dim_c: int=0, collision_force: float=COLLISION_FORCE, joint_force: float=JOINT_FORCE, torque_constraint_force: float=TORQUE_CONSTRAINT_FORCE, contact_margin: float=0.001, gravity: Tuple[float, float]=(0.0, 0.0)):
        assert batch_dim > 0, f'Batch dim must be greater than 0, got {batch_dim}'
        super().__init__(batch_dim, device)
        self._agents = []
        self._landmarks = []
        self._x_semidim = x_semidim
        self._y_semidim = y_semidim
        self._dim_p = 2
        self._dim_c = dim_c
        self._dt = dt
        self._substeps = substeps
        self._sub_dt = self._dt / self._substeps
        self._drag = drag
        self._gravity = torch.tensor(gravity, device=self.device, dtype=torch.float32)
        self._linear_friction = linear_friction
        self._angular_friction = angular_friction
        self._collision_force = collision_force
        self._joint_force = joint_force
        self._contact_margin = contact_margin
        self._torque_constraint_force = torque_constraint_force
        self._joints = {}
        self._collidable_pairs = [{Sphere, Sphere}, {Sphere, Box}, {Sphere, Line}, {Line, Line}, {Line, Box}, {Box, Box}]
        self.entity_index_map = {}

    def add_agent(self, agent: Agent):
        """Only way to add agents to the world"""
        agent.batch_dim = self._batch_dim
        agent.to(self._device)
        agent._spawn(dim_c=self._dim_c, dim_p=self.dim_p)
        self._agents.append(agent)

    def add_landmark(self, landmark: Landmark):
        """Only way to add landmarks to the world"""
        landmark.batch_dim = self._batch_dim
        landmark.to(self._device)
        landmark._spawn(dim_c=self.dim_c, dim_p=self.dim_p)
        self._landmarks.append(landmark)

    def add_joint(self, joint: Joint):
        assert self._substeps > 1, 'For joints, world substeps needs to be more than 1'
        if joint.landmark is not None:
            self.add_landmark(joint.landmark)
        for constraint in joint.joint_constraints:
            self._joints.update({frozenset({constraint.entity_a.name, constraint.entity_b.name}): constraint})

    def reset(self, env_index: int):
        for e in self.entities:
            e._reset(env_index)

    def zero_grad(self):
        for e in self.entities:
            e.zero_grad()

    @property
    def agents(self) -> List[Agent]:
        return self._agents

    @property
    def landmarks(self) -> List[Landmark]:
        return self._landmarks

    @property
    def x_semidim(self):
        return self._x_semidim

    @property
    def dt(self):
        return self._dt

    @property
    def y_semidim(self):
        return self._y_semidim

    @property
    def dim_p(self):
        return self._dim_p

    @property
    def dim_c(self):
        return self._dim_c

    @property
    def joints(self):
        return self._joints.values()

    @property
    def entities(self) -> List[Entity]:
        return self._landmarks + self._agents

    @property
    def policy_agents(self) -> List[Agent]:
        return [agent for agent in self._agents if agent.action_script is None]

    @property
    def scripted_agents(self) -> List[Agent]:
        return [agent for agent in self._agents if agent.action_script is not None]

    def _cast_ray_to_box(self, box: Entity, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        """
        Inspired from https://tavianator.com/2011/ray_box.html
        Computes distance of ray originating from pos at angle to a box and sets distance to
        max_range if there is no intersection.
        """
        assert ray_origin.ndim == 2 and ray_direction.ndim == 1
        assert ray_origin.shape[0] == ray_direction.shape[0]
        assert isinstance(box.shape, Box)
        pos_origin = ray_origin - box.state.pos
        pos_aabb = TorchUtils.rotate_vector(pos_origin, -box.state.rot)
        ray_dir_world = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        ray_dir_aabb = TorchUtils.rotate_vector(ray_dir_world, -box.state.rot)
        tx1 = (-box.shape.length / 2 - pos_aabb[:, X]) / ray_dir_aabb[:, X]
        tx2 = (box.shape.length / 2 - pos_aabb[:, X]) / ray_dir_aabb[:, X]
        tx = torch.stack([tx1, tx2], dim=-1)
        tmin, _ = torch.min(tx, dim=-1)
        tmax, _ = torch.max(tx, dim=-1)
        ty1 = (-box.shape.width / 2 - pos_aabb[:, Y]) / ray_dir_aabb[:, Y]
        ty2 = (box.shape.width / 2 - pos_aabb[:, Y]) / ray_dir_aabb[:, Y]
        ty = torch.stack([ty1, ty2], dim=-1)
        tymin, _ = torch.min(ty, dim=-1)
        tymax, _ = torch.max(ty, dim=-1)
        tmin, _ = torch.max(torch.stack([tmin, tymin], dim=-1), dim=-1)
        tmax, _ = torch.min(torch.stack([tmax, tymax], dim=-1), dim=-1)
        intersect_aabb = tmin.unsqueeze(1) * ray_dir_aabb + pos_aabb
        intersect_world = TorchUtils.rotate_vector(intersect_aabb, box.state.rot) + box.state.pos
        collision = (tmax >= tmin) & (tmin > 0.0)
        dist = torch.linalg.norm(ray_origin - intersect_world, dim=1)
        dist[~collision] = max_range
        return dist

    def _cast_rays_to_box(self, box_pos, box_rot, box_length, box_width, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        """
        Inspired from https://tavianator.com/2011/ray_box.html
        Computes distance of ray originating from pos at angle to a box and sets distance to
        max_range if there is no intersection.
        """
        batch_size = ray_origin.shape[:-1]
        assert batch_size[0] == self.batch_dim
        assert ray_origin.shape[-1] == 2
        assert ray_direction.shape[:-1] == batch_size
        assert box_pos.shape[:-2] == batch_size
        assert box_pos.shape[-1] == 2
        assert box_rot.shape[:-1] == batch_size
        assert box_width.shape[:-1] == batch_size
        assert box_length.shape[:-1] == batch_size
        num_angles = ray_direction.shape[-1]
        n_boxes = box_pos.shape[-2]
        ray_origin = ray_origin.unsqueeze(-2).unsqueeze(-2).expand(*batch_size, n_boxes, num_angles, 2)
        box_pos_expanded = box_pos.unsqueeze(-2).expand(*batch_size, n_boxes, num_angles, 2)
        ray_direction = ray_direction.unsqueeze(-2).expand(*batch_size, n_boxes, num_angles)
        box_rot_expanded = box_rot.unsqueeze(-1).expand(*batch_size, n_boxes, num_angles)
        box_width_expanded = box_width.unsqueeze(-1).expand(*batch_size, n_boxes, num_angles)
        box_length_expanded = box_length.unsqueeze(-1).expand(*batch_size, n_boxes, num_angles)
        pos_origin = ray_origin - box_pos_expanded
        pos_aabb = TorchUtils.rotate_vector(pos_origin, -box_rot_expanded)
        ray_dir_world = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        ray_dir_aabb = TorchUtils.rotate_vector(ray_dir_world, -box_rot_expanded)
        tx1 = (-box_length_expanded / 2 - pos_aabb[..., X]) / ray_dir_aabb[..., X]
        tx2 = (box_length_expanded / 2 - pos_aabb[..., X]) / ray_dir_aabb[..., X]
        tx = torch.stack([tx1, tx2], dim=-1)
        tmin, _ = torch.min(tx, dim=-1)
        tmax, _ = torch.max(tx, dim=-1)
        ty1 = (-box_width_expanded / 2 - pos_aabb[..., Y]) / ray_dir_aabb[..., Y]
        ty2 = (box_width_expanded / 2 - pos_aabb[..., Y]) / ray_dir_aabb[..., Y]
        ty = torch.stack([ty1, ty2], dim=-1)
        tymin, _ = torch.min(ty, dim=-1)
        tymax, _ = torch.max(ty, dim=-1)
        tmin, _ = torch.max(torch.stack([tmin, tymin], dim=-1), dim=-1)
        tmax, _ = torch.min(torch.stack([tmax, tymax], dim=-1), dim=-1)
        intersect_aabb = tmin.unsqueeze(-1) * ray_dir_aabb + pos_aabb
        intersect_world = TorchUtils.rotate_vector(intersect_aabb, box_rot_expanded) + box_pos_expanded
        collision = (tmax >= tmin) & (tmin > 0.0)
        dist = torch.linalg.norm(ray_origin - intersect_world, dim=-1)
        dist[~collision] = max_range
        return dist

    def _cast_ray_to_sphere(self, sphere: Entity, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        ray_dir_world = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        test_point_pos = sphere.state.pos
        line_rot = ray_direction
        line_length = max_range
        line_pos = ray_origin + ray_dir_world * (line_length / 2)
        closest_point = _get_closest_point_line(line_pos, line_rot.unsqueeze(-1), line_length, test_point_pos, limit_to_line_length=False)
        d = test_point_pos - closest_point
        d_norm = torch.linalg.vector_norm(d, dim=1)
        ray_intersects = d_norm < sphere.shape.radius
        a = sphere.shape.radius ** 2 - d_norm ** 2
        m = torch.sqrt(torch.where(a > 0, a, 1e-08))
        u = test_point_pos - ray_origin
        u1 = closest_point - ray_origin
        u_dot_ray = (u * ray_dir_world).sum(-1)
        sphere_is_in_front = u_dot_ray > 0.0
        dist = torch.linalg.vector_norm(u1, dim=1) - m
        dist[~(ray_intersects & sphere_is_in_front)] = max_range
        return dist

    def _cast_rays_to_sphere(self, sphere_pos, sphere_radius, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        batch_size = ray_origin.shape[:-1]
        assert batch_size[0] == self.batch_dim
        assert ray_origin.shape[-1] == 2
        assert ray_direction.shape[:-1] == batch_size
        assert sphere_pos.shape[:-2] == batch_size
        assert sphere_pos.shape[-1] == 2
        assert sphere_radius.shape[:-1] == batch_size
        num_angles = ray_direction.shape[-1]
        n_spheres = sphere_pos.shape[-2]
        ray_origin = ray_origin.unsqueeze(-2).unsqueeze(-2).expand(*batch_size, n_spheres, num_angles, 2)
        sphere_pos_expanded = sphere_pos.unsqueeze(-2).expand(*batch_size, n_spheres, num_angles, 2)
        ray_direction = ray_direction.unsqueeze(-2).expand(*batch_size, n_spheres, num_angles)
        sphere_radius_expanded = sphere_radius.unsqueeze(-1).expand(*batch_size, n_spheres, num_angles)
        ray_dir_world = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        line_rot = ray_direction.unsqueeze(-1)
        line_length = max_range
        line_pos = ray_origin + ray_dir_world * (line_length / 2)
        closest_point = _get_closest_point_line(line_pos, line_rot, line_length, sphere_pos_expanded, limit_to_line_length=False)
        d = sphere_pos_expanded - closest_point
        d_norm = torch.linalg.vector_norm(d, dim=-1)
        ray_intersects = d_norm < sphere_radius_expanded
        a = sphere_radius_expanded ** 2 - d_norm ** 2
        m = torch.sqrt(torch.where(a > 0, a, 1e-08))
        u = sphere_pos_expanded - ray_origin
        u1 = closest_point - ray_origin
        u_dot_ray = (u * ray_dir_world).sum(-1)
        sphere_is_in_front = u_dot_ray > 0.0
        dist = torch.linalg.vector_norm(u1, dim=-1) - m
        dist[~(ray_intersects & sphere_is_in_front)] = max_range
        return dist

    def _cast_ray_to_line(self, line: Entity, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        """
        Inspired by https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/565282#565282
        Computes distance of ray originating from pos at angle to a line and sets distance to
        max_range if there is no intersection.
        """
        assert ray_origin.ndim == 2 and ray_direction.ndim == 1
        assert ray_origin.shape[0] == ray_direction.shape[0]
        assert isinstance(line.shape, Line)
        p = line.state.pos
        r = torch.stack([torch.cos(line.state.rot.squeeze(1)), torch.sin(line.state.rot.squeeze(1))], dim=-1) * line.shape.length
        q = ray_origin
        s = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        rxs = TorchUtils.cross(r, s)
        t = TorchUtils.cross(q - p, s / rxs)
        u = TorchUtils.cross(q - p, r / rxs)
        d = torch.linalg.norm(u * s, dim=-1)
        perpendicular = rxs == 0.0
        above_line = t > 0.5
        below_line = t < -0.5
        behind_line = u < 0.0
        d[perpendicular.squeeze(-1)] = max_range
        d[above_line.squeeze(-1)] = max_range
        d[below_line.squeeze(-1)] = max_range
        d[behind_line.squeeze(-1)] = max_range
        return d

    def _cast_rays_to_line(self, line_pos, line_rot, line_length, ray_origin: Tensor, ray_direction: Tensor, max_range: float):
        """
        Inspired by https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/565282#565282
        Computes distance of ray originating from pos at angle to a line and sets distance to
        max_range if there is no intersection.
        """
        batch_size = ray_origin.shape[:-1]
        assert batch_size[0] == self.batch_dim
        assert ray_origin.shape[-1] == 2
        assert ray_direction.shape[:-1] == batch_size
        assert line_pos.shape[:-2] == batch_size
        assert line_pos.shape[-1] == 2
        assert line_rot.shape[:-1] == batch_size
        assert line_length.shape[:-1] == batch_size
        num_angles = ray_direction.shape[-1]
        n_lines = line_pos.shape[-2]
        ray_origin = ray_origin.unsqueeze(-2).unsqueeze(-2).expand(*batch_size, n_lines, num_angles, 2)
        line_pos_expanded = line_pos.unsqueeze(-2).expand(*batch_size, n_lines, num_angles, 2)
        ray_direction = ray_direction.unsqueeze(-2).expand(*batch_size, n_lines, num_angles)
        line_rot_expanded = line_rot.unsqueeze(-1).expand(*batch_size, n_lines, num_angles)
        line_length_expanded = line_length.unsqueeze(-1).expand(*batch_size, n_lines, num_angles)
        r = torch.stack([torch.cos(line_rot_expanded), torch.sin(line_rot_expanded)], dim=-1) * line_length_expanded.unsqueeze(-1)
        q = ray_origin
        s = torch.stack([torch.cos(ray_direction), torch.sin(ray_direction)], dim=-1)
        rxs = TorchUtils.cross(r, s)
        t = TorchUtils.cross(q - line_pos_expanded, s / rxs)
        u = TorchUtils.cross(q - line_pos_expanded, r / rxs)
        d = torch.linalg.norm(u * s, dim=-1)
        perpendicular = rxs == 0.0
        above_line = t > 0.5
        below_line = t < -0.5
        behind_line = u < 0.0
        d[perpendicular.squeeze(-1)] = max_range
        d[above_line.squeeze(-1)] = max_range
        d[below_line.squeeze(-1)] = max_range
        d[behind_line.squeeze(-1)] = max_range
        return d

    def cast_ray(self, entity: Entity, angles: Tensor, max_range: float, entity_filter: Callable[[Entity], bool]=lambda _: False):
        pos = entity.state.pos
        assert pos.ndim == 2 and angles.ndim == 1
        assert pos.shape[0] == angles.shape[0]
        dists = [torch.full((self.batch_dim,), fill_value=max_range, device=self.device)]
        for e in self.entities:
            if entity is e or not entity_filter(e):
                continue
            assert e.collides(entity) and entity.collides(e), 'Rays are only casted among collidables'
            if isinstance(e.shape, Box):
                d = self._cast_ray_to_box(e, pos, angles, max_range)
            elif isinstance(e.shape, Sphere):
                d = self._cast_ray_to_sphere(e, pos, angles, max_range)
            elif isinstance(e.shape, Line):
                d = self._cast_ray_to_line(e, pos, angles, max_range)
            else:
                raise RuntimeError(f'Shape {e.shape} currently not handled by cast_ray')
            dists.append(d)
        dist, _ = torch.min(torch.stack(dists, dim=-1), dim=-1)
        return dist

    def cast_rays(self, entity: Entity, angles: Tensor, max_range: float, entity_filter: Callable[[Entity], bool]=lambda _: False):
        pos = entity.state.pos
        dists = torch.full_like(angles, fill_value=max_range, device=self.device).unsqueeze(-1)
        boxes = []
        spheres = []
        lines = []
        for e in self.entities:
            if entity is e or not entity_filter(e):
                continue
            assert e.collides(entity) and entity.collides(e), 'Rays are only casted among collidables'
            if isinstance(e.shape, Box):
                boxes.append(e)
            elif isinstance(e.shape, Sphere):
                spheres.append(e)
            elif isinstance(e.shape, Line):
                lines.append(e)
            else:
                raise RuntimeError(f'Shape {e.shape} currently not handled by cast_ray')
        if len(boxes):
            pos_box = []
            rot_box = []
            length_box = []
            width_box = []
            for box in boxes:
                pos_box.append(box.state.pos)
                rot_box.append(box.state.rot)
                length_box.append(torch.tensor(box.shape.length, device=self.device))
                width_box.append(torch.tensor(box.shape.width, device=self.device))
            pos_box = torch.stack(pos_box, dim=-2)
            rot_box = torch.stack(rot_box, dim=-2)
            length_box = torch.stack(length_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            width_box = torch.stack(width_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            dist_boxes = self._cast_rays_to_box(pos_box, rot_box.squeeze(-1), length_box, width_box, pos, angles, max_range)
            dists = torch.cat([dists, dist_boxes.transpose(-1, -2)], dim=-1)
        if len(spheres):
            pos_s = []
            radius_s = []
            for s in spheres:
                pos_s.append(s.state.pos)
                radius_s.append(torch.tensor(s.shape.radius, device=self.device))
            pos_s = torch.stack(pos_s, dim=-2)
            radius_s = torch.stack(radius_s, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            dist_spheres = self._cast_rays_to_sphere(pos_s, radius_s, pos, angles, max_range)
            dists = torch.cat([dists, dist_spheres.transpose(-1, -2)], dim=-1)
        if len(lines):
            pos_l = []
            rot_l = []
            length_l = []
            for line in lines:
                pos_l.append(line.state.pos)
                rot_l.append(line.state.rot)
                length_l.append(torch.tensor(line.shape.length, device=self.device))
            pos_l = torch.stack(pos_l, dim=-2)
            rot_l = torch.stack(rot_l, dim=-2)
            length_l = torch.stack(length_l, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            dist_lines = self._cast_rays_to_line(pos_l, rot_l.squeeze(-1), length_l, pos, angles, max_range)
            dists = torch.cat([dists, dist_lines.transpose(-1, -2)], dim=-1)
        dist, _ = torch.min(dists, dim=-1)
        return dist

    def get_distance_from_point(self, entity: Entity, test_point_pos, env_index: int=None):
        self._check_batch_index(env_index)
        if isinstance(entity.shape, Sphere):
            delta_pos = entity.state.pos - test_point_pos
            dist = torch.linalg.vector_norm(delta_pos, dim=-1)
            return_value = dist - entity.shape.radius
        elif isinstance(entity.shape, Box):
            closest_point = _get_closest_point_box(entity.state.pos, entity.state.rot, entity.shape.width, entity.shape.length, test_point_pos)
            distance = torch.linalg.vector_norm(test_point_pos - closest_point, dim=-1)
            return_value = distance - LINE_MIN_DIST
        elif isinstance(entity.shape, Line):
            closest_point = _get_closest_point_line(entity.state.pos, entity.state.rot, entity.shape.length, test_point_pos)
            distance = torch.linalg.vector_norm(test_point_pos - closest_point, dim=-1)
            return_value = distance - LINE_MIN_DIST
        else:
            raise RuntimeError('Distance not computable for given entity')
        if env_index is not None:
            return_value = return_value[env_index]
        return return_value

    def get_distance(self, entity_a: Entity, entity_b: Entity, env_index: int=None):
        a_shape = entity_a.shape
        b_shape = entity_b.shape
        if isinstance(a_shape, Sphere) and isinstance(b_shape, Sphere):
            dist = self.get_distance_from_point(entity_a, entity_b.state.pos, env_index)
            return_value = dist - b_shape.radius
        elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Sphere)):
            box, sphere = (entity_a, entity_b) if isinstance(entity_b.shape, Sphere) else (entity_b, entity_a)
            dist = self.get_distance_from_point(box, sphere.state.pos, env_index)
            return_value = dist - sphere.shape.radius
            is_overlapping = self.is_overlapping(entity_a, entity_b)
            return_value[is_overlapping] = -1
        elif isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Line) and isinstance(entity_a.shape, Sphere)):
            line, sphere = (entity_a, entity_b) if isinstance(entity_b.shape, Sphere) else (entity_b, entity_a)
            dist = self.get_distance_from_point(line, sphere.state.pos, env_index)
            return_value = dist - sphere.shape.radius
        elif isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Line):
            point_a, point_b = _get_closest_points_line_line(entity_a.state.pos, entity_a.state.rot, entity_a.shape.length, entity_b.state.pos, entity_b.state.rot, entity_b.shape.length)
            dist = torch.linalg.vector_norm(point_a - point_b, dim=1)
            return_value = dist - LINE_MIN_DIST
        elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Line) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Line)):
            box, line = (entity_a, entity_b) if isinstance(entity_b.shape, Line) else (entity_b, entity_a)
            point_box, point_line = _get_closest_line_box(box.state.pos, box.state.rot, box.shape.width, box.shape.length, line.state.pos, line.state.rot, line.shape.length)
            dist = torch.linalg.vector_norm(point_box - point_line, dim=1)
            return_value = dist - LINE_MIN_DIST
        elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Box):
            point_a, point_b = _get_closest_box_box(entity_a.state.pos, entity_a.state.rot, entity_a.shape.width, entity_a.shape.length, entity_b.state.pos, entity_b.state.rot, entity_b.shape.width, entity_b.shape.length)
            dist = torch.linalg.vector_norm(point_a - point_b, dim=-1)
            return_value = dist - LINE_MIN_DIST
        else:
            raise RuntimeError('Distance not computable for given entities')
        return return_value

    def is_overlapping(self, entity_a: Entity, entity_b: Entity, env_index: int=None):
        a_shape = entity_a.shape
        b_shape = entity_b.shape
        self._check_batch_index(env_index)
        if isinstance(a_shape, Sphere) and isinstance(b_shape, Sphere) or (isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Line) and isinstance(entity_a.shape, Sphere))) or (isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Line)) or (isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Line) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Line))) or (isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Box)):
            return self.get_distance(entity_a, entity_b, env_index) < 0
        elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Sphere)):
            box, sphere = (entity_a, entity_b) if isinstance(entity_b.shape, Sphere) else (entity_b, entity_a)
            closest_point = _get_closest_point_box(box.state.pos, box.state.rot, box.shape.width, box.shape.length, sphere.state.pos)
            distance_sphere_closest_point = torch.linalg.vector_norm(sphere.state.pos - closest_point, dim=-1)
            distance_sphere_box = torch.linalg.vector_norm(sphere.state.pos - box.state.pos, dim=-1)
            distance_closest_point_box = torch.linalg.vector_norm(box.state.pos - closest_point, dim=-1)
            dist_min = sphere.shape.radius + LINE_MIN_DIST
            return_value = (distance_sphere_box < distance_closest_point_box) + (distance_sphere_closest_point < dist_min)
        else:
            raise RuntimeError('Overlap not computable for give entities')
        if env_index is not None:
            return_value = return_value[env_index]
        return return_value

    def step(self):
        self.entity_index_map = {e: i for i, e in enumerate(self.entities)}
        for substep in range(self._substeps):
            self.forces_dict = {e: torch.zeros(self._batch_dim, self._dim_p, device=self.device, dtype=torch.float32) for e in self.entities}
            self.torques_dict = {e: torch.zeros(self._batch_dim, 1, device=self.device, dtype=torch.float32) for e in self.entities}
            for entity in self.entities:
                if isinstance(entity, Agent):
                    self._apply_action_force(entity)
                    self._apply_action_torque(entity)
                self._apply_friction_force(entity)
                self._apply_gravity(entity)
            self._apply_vectorized_enviornment_force()
            for entity in self.entities:
                self._integrate_state(entity, substep)
        if self._dim_c > 0:
            for agent in self._agents:
                self._update_comm_state(agent)

    def _apply_action_force(self, agent: Agent):
        if agent.movable:
            if agent.max_f is not None:
                agent.state.force = TorchUtils.clamp_with_norm(agent.state.force, agent.max_f)
            if agent.f_range is not None:
                agent.state.force = torch.clamp(agent.state.force, -agent.f_range, agent.f_range)
            self.forces_dict[agent] = self.forces_dict[agent] + agent.state.force

    def _apply_action_torque(self, agent: Agent):
        if agent.rotatable:
            if agent.max_t is not None:
                agent.state.torque = TorchUtils.clamp_with_norm(agent.state.torque, agent.max_t)
            if agent.t_range is not None:
                agent.state.torque = torch.clamp(agent.state.torque, -agent.t_range, agent.t_range)
            self.torques_dict[agent] = self.torques_dict[agent] + agent.state.torque

    def _apply_gravity(self, entity: Entity):
        if entity.movable:
            if not (self._gravity == 0.0).all():
                self.forces_dict[entity] = self.forces_dict[entity] + entity.mass * self._gravity
            if entity.gravity is not None:
                self.forces_dict[entity] = self.forces_dict[entity] + entity.mass * entity.gravity

    def _apply_friction_force(self, entity: Entity):

        def get_friction_force(vel, coeff, force, mass):
            speed = torch.linalg.vector_norm(vel, dim=-1)
            static = speed == 0
            static_exp = static.unsqueeze(-1).expand(vel.shape)
            if not isinstance(coeff, Tensor):
                coeff = torch.full_like(force, coeff, device=self.device)
            coeff = coeff.expand(force.shape)
            friction_force_constant = coeff * mass
            friction_force = -(vel / torch.where(static, 1e-08, speed).unsqueeze(-1)) * torch.minimum(friction_force_constant, vel.abs() / self._sub_dt * mass)
            friction_force = torch.where(static_exp, 0.0, friction_force)
            return friction_force
        if entity.linear_friction is not None:
            self.forces_dict[entity] = self.forces_dict[entity] + get_friction_force(entity.state.vel, entity.linear_friction, self.forces_dict[entity], entity.mass)
        elif self._linear_friction > 0:
            self.forces_dict[entity] = self.forces_dict[entity] + get_friction_force(entity.state.vel, self._linear_friction, self.forces_dict[entity], entity.mass)
        if entity.angular_friction is not None:
            self.torques_dict[entity] = self.torques_dict[entity] + get_friction_force(entity.state.ang_vel, entity.angular_friction, self.torques_dict[entity], entity.moment_of_inertia)
        elif self._angular_friction > 0:
            self.torques_dict[entity] = self.torques_dict[entity] + get_friction_force(entity.state.ang_vel, self._angular_friction, self.torques_dict[entity], entity.moment_of_inertia)

    def _apply_vectorized_enviornment_force(self):
        s_s = []
        l_s = []
        b_s = []
        l_l = []
        b_l = []
        b_b = []
        joints = []
        for a, entity_a in enumerate(self.entities):
            for b, entity_b in enumerate(self.entities):
                if b <= a:
                    continue
                joint = self._joints.get(frozenset({entity_a.name, entity_b.name}), None)
                if joint is not None:
                    joints.append(joint)
                    if joint.dist == 0:
                        continue
                if not self.collides(entity_a, entity_b):
                    continue
                if isinstance(entity_a.shape, Sphere) and isinstance(entity_b.shape, Sphere):
                    s_s.append((entity_a, entity_b))
                elif isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Line) and isinstance(entity_a.shape, Sphere)):
                    line, sphere = (entity_a, entity_b) if isinstance(entity_b.shape, Sphere) else (entity_b, entity_a)
                    l_s.append((line, sphere))
                elif isinstance(entity_a.shape, Line) and isinstance(entity_b.shape, Line):
                    l_l.append((entity_a, entity_b))
                elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Sphere) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Sphere)):
                    box, sphere = (entity_a, entity_b) if isinstance(entity_b.shape, Sphere) else (entity_b, entity_a)
                    b_s.append((box, sphere))
                elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Line) or (isinstance(entity_b.shape, Box) and isinstance(entity_a.shape, Line)):
                    box, line = (entity_a, entity_b) if isinstance(entity_b.shape, Line) else (entity_b, entity_a)
                    b_l.append((box, line))
                elif isinstance(entity_a.shape, Box) and isinstance(entity_b.shape, Box):
                    b_b.append((entity_a, entity_b))
                else:
                    raise AssertionError()
        self._vectorized_joint_constraints(joints)
        self._sphere_sphere_vectorized_collision(s_s)
        self._sphere_line_vectorized_collision(l_s)
        self._line_line_vectorized_collision(l_l)
        self._box_sphere_vectorized_collision(b_s)
        self._box_line_vectorized_collision(b_l)
        self._box_box_vectorized_collision(b_b)

    def update_env_forces(self, entity_a, f_a, t_a, entity_b, f_b, t_b):
        if entity_a.movable:
            self.forces_dict[entity_a] = self.forces_dict[entity_a] + f_a
        if entity_a.rotatable:
            self.torques_dict[entity_a] = self.torques_dict[entity_a] + t_a
        if entity_b.movable:
            self.forces_dict[entity_b] = self.forces_dict[entity_b] + f_b
        if entity_b.rotatable:
            self.torques_dict[entity_b] = self.torques_dict[entity_b] + t_b

    def _vectorized_joint_constraints(self, joints):
        if len(joints):
            pos_a = []
            pos_b = []
            pos_joint_a = []
            pos_joint_b = []
            dist = []
            rotate = []
            rot_a = []
            rot_b = []
            joint_rot = []
            for joint in joints:
                entity_a = joint.entity_a
                entity_b = joint.entity_b
                pos_joint_a.append(joint.pos_point(entity_a))
                pos_joint_b.append(joint.pos_point(entity_b))
                pos_a.append(entity_a.state.pos)
                pos_b.append(entity_b.state.pos)
                dist.append(torch.tensor(joint.dist, device=self.device))
                rotate.append(torch.tensor(joint.rotate, device=self.device))
                rot_a.append(entity_a.state.rot)
                rot_b.append(entity_b.state.rot)
                joint_rot.append(torch.tensor(joint.fixed_rotation, device=self.device).unsqueeze(-1).expand(self.batch_dim, 1) if isinstance(joint.fixed_rotation, float) else joint.fixed_rotation)
            pos_a = torch.stack(pos_a, dim=-2)
            pos_b = torch.stack(pos_b, dim=-2)
            pos_joint_a = torch.stack(pos_joint_a, dim=-2)
            pos_joint_b = torch.stack(pos_joint_b, dim=-2)
            rot_a = torch.stack(rot_a, dim=-2)
            rot_b = torch.stack(rot_b, dim=-2)
            dist = torch.stack(dist, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            rotate_prior = torch.stack(rotate, dim=-1)
            rotate = rotate_prior.unsqueeze(0).expand(self.batch_dim, -1).unsqueeze(-1)
            joint_rot = torch.stack(joint_rot, dim=-2)
            force_a_attractive, force_b_attractive = self._get_constraint_forces(pos_joint_a, pos_joint_b, dist_min=dist, attractive=True, force_multiplier=self._joint_force)
            force_a_repulsive, force_b_repulsive = self._get_constraint_forces(pos_joint_a, pos_joint_b, dist_min=dist, attractive=False, force_multiplier=self._joint_force)
            force_a = force_a_attractive + force_a_repulsive
            force_b = force_b_attractive + force_b_repulsive
            r_a = pos_joint_a - pos_a
            r_b = pos_joint_b - pos_b
            torque_a_rotate = TorchUtils.compute_torque(force_a, r_a)
            torque_b_rotate = TorchUtils.compute_torque(force_b, r_b)
            torque_a_fixed, torque_b_fixed = self._get_constraint_torques(rot_a, rot_b + joint_rot, force_multiplier=self._torque_constraint_force)
            torque_a = torch.where(rotate, torque_a_rotate, torque_a_rotate + torque_a_fixed)
            torque_b = torch.where(rotate, torque_b_rotate, torque_b_rotate + torque_b_fixed)
            for i, joint in enumerate(joints):
                self.update_env_forces(joint.entity_a, force_a[:, i], torque_a[:, i], joint.entity_b, force_b[:, i], torque_b[:, i])

    def _sphere_sphere_vectorized_collision(self, s_s):
        if len(s_s):
            pos_s_a = []
            pos_s_b = []
            radius_s_a = []
            radius_s_b = []
            for s_a, s_b in s_s:
                pos_s_a.append(s_a.state.pos)
                pos_s_b.append(s_b.state.pos)
                radius_s_a.append(torch.tensor(s_a.shape.radius, device=self.device))
                radius_s_b.append(torch.tensor(s_b.shape.radius, device=self.device))
            pos_s_a = torch.stack(pos_s_a, dim=-2)
            pos_s_b = torch.stack(pos_s_b, dim=-2)
            radius_s_a = torch.stack(radius_s_a, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            radius_s_b = torch.stack(radius_s_b, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            force_a, force_b = self._get_constraint_forces(pos_s_a, pos_s_b, dist_min=radius_s_a + radius_s_b, force_multiplier=self._collision_force)
            for i, (entity_a, entity_b) in enumerate(s_s):
                self.update_env_forces(entity_a, force_a[:, i], 0, entity_b, force_b[:, i], 0)

    def _sphere_line_vectorized_collision(self, l_s):
        if len(l_s):
            pos_l = []
            pos_s = []
            rot_l = []
            radius_s = []
            length_l = []
            for line, sphere in l_s:
                pos_l.append(line.state.pos)
                pos_s.append(sphere.state.pos)
                rot_l.append(line.state.rot)
                radius_s.append(torch.tensor(sphere.shape.radius, device=self.device))
                length_l.append(torch.tensor(line.shape.length, device=self.device))
            pos_l = torch.stack(pos_l, dim=-2)
            pos_s = torch.stack(pos_s, dim=-2)
            rot_l = torch.stack(rot_l, dim=-2)
            radius_s = torch.stack(radius_s, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            length_l = torch.stack(length_l, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            closest_point = _get_closest_point_line(pos_l, rot_l, length_l, pos_s)
            force_sphere, force_line = self._get_constraint_forces(pos_s, closest_point, dist_min=radius_s + LINE_MIN_DIST, force_multiplier=self._collision_force)
            r = closest_point - pos_l
            torque_line = TorchUtils.compute_torque(force_line, r)
            for i, (entity_a, entity_b) in enumerate(l_s):
                self.update_env_forces(entity_a, force_line[:, i], torque_line[:, i], entity_b, force_sphere[:, i], 0)

    def _line_line_vectorized_collision(self, l_l):
        if len(l_l):
            pos_l_a = []
            pos_l_b = []
            rot_l_a = []
            rot_l_b = []
            length_l_a = []
            length_l_b = []
            for l_a, l_b in l_l:
                pos_l_a.append(l_a.state.pos)
                pos_l_b.append(l_b.state.pos)
                rot_l_a.append(l_a.state.rot)
                rot_l_b.append(l_b.state.rot)
                length_l_a.append(torch.tensor(l_a.shape.length, device=self.device))
                length_l_b.append(torch.tensor(l_b.shape.length, device=self.device))
            pos_l_a = torch.stack(pos_l_a, dim=-2)
            pos_l_b = torch.stack(pos_l_b, dim=-2)
            rot_l_a = torch.stack(rot_l_a, dim=-2)
            rot_l_b = torch.stack(rot_l_b, dim=-2)
            length_l_a = torch.stack(length_l_a, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            length_l_b = torch.stack(length_l_b, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            point_a, point_b = _get_closest_points_line_line(pos_l_a, rot_l_a, length_l_a, pos_l_b, rot_l_b, length_l_b)
            force_a, force_b = self._get_constraint_forces(point_a, point_b, dist_min=LINE_MIN_DIST, force_multiplier=self._collision_force)
            r_a = point_a - pos_l_a
            r_b = point_b - pos_l_b
            torque_a = TorchUtils.compute_torque(force_a, r_a)
            torque_b = TorchUtils.compute_torque(force_b, r_b)
            for i, (entity_a, entity_b) in enumerate(l_l):
                self.update_env_forces(entity_a, force_a[:, i], torque_a[:, i], entity_b, force_b[:, i], torque_b[:, i])

    def _box_sphere_vectorized_collision(self, b_s):
        if len(b_s):
            pos_box = []
            pos_sphere = []
            rot_box = []
            length_box = []
            width_box = []
            not_hollow_box = []
            radius_sphere = []
            for box, sphere in b_s:
                pos_box.append(box.state.pos)
                pos_sphere.append(sphere.state.pos)
                rot_box.append(box.state.rot)
                length_box.append(torch.tensor(box.shape.length, device=self.device))
                width_box.append(torch.tensor(box.shape.width, device=self.device))
                not_hollow_box.append(torch.tensor(not box.shape.hollow, device=self.device))
                radius_sphere.append(torch.tensor(sphere.shape.radius, device=self.device))
            pos_box = torch.stack(pos_box, dim=-2)
            pos_sphere = torch.stack(pos_sphere, dim=-2)
            rot_box = torch.stack(rot_box, dim=-2)
            length_box = torch.stack(length_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            width_box = torch.stack(width_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            not_hollow_box_prior = torch.stack(not_hollow_box, dim=-1)
            not_hollow_box = not_hollow_box_prior.unsqueeze(0).expand(self.batch_dim, -1)
            radius_sphere = torch.stack(radius_sphere, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            closest_point_box = _get_closest_point_box(pos_box, rot_box, width_box, length_box, pos_sphere)
            inner_point_box = closest_point_box
            d = torch.zeros_like(radius_sphere, device=self.device, dtype=torch.float)
            if not_hollow_box_prior.any():
                inner_point_box_hollow, d_hollow = _get_inner_point_box(pos_sphere, closest_point_box, pos_box)
                cond = not_hollow_box.unsqueeze(-1).expand(inner_point_box.shape)
                inner_point_box = torch.where(cond, inner_point_box_hollow, inner_point_box)
                d = torch.where(not_hollow_box, d_hollow, d)
            force_sphere, force_box = self._get_constraint_forces(pos_sphere, inner_point_box, dist_min=radius_sphere + LINE_MIN_DIST + d, force_multiplier=self._collision_force)
            r = closest_point_box - pos_box
            torque_box = TorchUtils.compute_torque(force_box, r)
            for i, (entity_a, entity_b) in enumerate(b_s):
                self.update_env_forces(entity_a, force_box[:, i], torque_box[:, i], entity_b, force_sphere[:, i], 0)

    def _box_line_vectorized_collision(self, b_l):
        if len(b_l):
            pos_box = []
            pos_line = []
            rot_box = []
            rot_line = []
            length_box = []
            width_box = []
            not_hollow_box = []
            length_line = []
            for box, line in b_l:
                pos_box.append(box.state.pos)
                pos_line.append(line.state.pos)
                rot_box.append(box.state.rot)
                rot_line.append(line.state.rot)
                length_box.append(torch.tensor(box.shape.length, device=self.device))
                width_box.append(torch.tensor(box.shape.width, device=self.device))
                not_hollow_box.append(torch.tensor(not box.shape.hollow, device=self.device))
                length_line.append(torch.tensor(line.shape.length, device=self.device))
            pos_box = torch.stack(pos_box, dim=-2)
            pos_line = torch.stack(pos_line, dim=-2)
            rot_box = torch.stack(rot_box, dim=-2)
            rot_line = torch.stack(rot_line, dim=-2)
            length_box = torch.stack(length_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            width_box = torch.stack(width_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            not_hollow_box_prior = torch.stack(not_hollow_box, dim=-1)
            not_hollow_box = not_hollow_box_prior.unsqueeze(0).expand(self.batch_dim, -1)
            length_line = torch.stack(length_line, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            point_box, point_line = _get_closest_line_box(pos_box, rot_box, width_box, length_box, pos_line, rot_line, length_line)
            inner_point_box = point_box
            d = torch.zeros_like(length_line, device=self.device, dtype=torch.float)
            if not_hollow_box_prior.any():
                inner_point_box_hollow, d_hollow = _get_inner_point_box(point_line, point_box, pos_box)
                cond = not_hollow_box.unsqueeze(-1).expand(inner_point_box.shape)
                inner_point_box = torch.where(cond, inner_point_box_hollow, inner_point_box)
                d = torch.where(not_hollow_box, d_hollow, d)
            force_box, force_line = self._get_constraint_forces(inner_point_box, point_line, dist_min=LINE_MIN_DIST + d, force_multiplier=self._collision_force)
            r_box = point_box - pos_box
            r_line = point_line - pos_line
            torque_box = TorchUtils.compute_torque(force_box, r_box)
            torque_line = TorchUtils.compute_torque(force_line, r_line)
            for i, (entity_a, entity_b) in enumerate(b_l):
                self.update_env_forces(entity_a, force_box[:, i], torque_box[:, i], entity_b, force_line[:, i], torque_line[:, i])

    def _box_box_vectorized_collision(self, b_b):
        if len(b_b):
            pos_box = []
            pos_box2 = []
            rot_box = []
            rot_box2 = []
            length_box = []
            width_box = []
            not_hollow_box = []
            length_box2 = []
            width_box2 = []
            not_hollow_box2 = []
            for box, box2 in b_b:
                pos_box.append(box.state.pos)
                rot_box.append(box.state.rot)
                length_box.append(torch.tensor(box.shape.length, device=self.device))
                width_box.append(torch.tensor(box.shape.width, device=self.device))
                not_hollow_box.append(torch.tensor(not box.shape.hollow, device=self.device))
                pos_box2.append(box2.state.pos)
                rot_box2.append(box2.state.rot)
                length_box2.append(torch.tensor(box2.shape.length, device=self.device))
                width_box2.append(torch.tensor(box2.shape.width, device=self.device))
                not_hollow_box2.append(torch.tensor(not box2.shape.hollow, device=self.device))
            pos_box = torch.stack(pos_box, dim=-2)
            rot_box = torch.stack(rot_box, dim=-2)
            length_box = torch.stack(length_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            width_box = torch.stack(width_box, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            not_hollow_box_prior = torch.stack(not_hollow_box, dim=-1)
            not_hollow_box = not_hollow_box_prior.unsqueeze(0).expand(self.batch_dim, -1)
            pos_box2 = torch.stack(pos_box2, dim=-2)
            rot_box2 = torch.stack(rot_box2, dim=-2)
            length_box2 = torch.stack(length_box2, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            width_box2 = torch.stack(width_box2, dim=-1).unsqueeze(0).expand(self.batch_dim, -1)
            not_hollow_box2_prior = torch.stack(not_hollow_box2, dim=-1)
            not_hollow_box2 = not_hollow_box2_prior.unsqueeze(0).expand(self.batch_dim, -1)
            point_a, point_b = _get_closest_box_box(pos_box, rot_box, width_box, length_box, pos_box2, rot_box2, width_box2, length_box2)
            inner_point_a = point_a
            d_a = torch.zeros_like(length_box, device=self.device, dtype=torch.float)
            if not_hollow_box_prior.any():
                inner_point_box_hollow, d_hollow = _get_inner_point_box(point_b, point_a, pos_box)
                cond = not_hollow_box.unsqueeze(-1).expand(inner_point_a.shape)
                inner_point_a = torch.where(cond, inner_point_box_hollow, inner_point_a)
                d_a = torch.where(not_hollow_box, d_hollow, d_a)
            inner_point_b = point_b
            d_b = torch.zeros_like(length_box2, device=self.device, dtype=torch.float)
            if not_hollow_box2_prior.any():
                inner_point_box2_hollow, d_hollow2 = _get_inner_point_box(point_a, point_b, pos_box2)
                cond = not_hollow_box2.unsqueeze(-1).expand(inner_point_b.shape)
                inner_point_b = torch.where(cond, inner_point_box2_hollow, inner_point_b)
                d_b = torch.where(not_hollow_box2, d_hollow2, d_b)
            force_a, force_b = self._get_constraint_forces(inner_point_a, inner_point_b, dist_min=d_a + d_b + LINE_MIN_DIST, force_multiplier=self._collision_force)
            r_a = point_a - pos_box
            r_b = point_b - pos_box2
            torque_a = TorchUtils.compute_torque(force_a, r_a)
            torque_b = TorchUtils.compute_torque(force_b, r_b)
            for i, (entity_a, entity_b) in enumerate(b_b):
                self.update_env_forces(entity_a, force_a[:, i], torque_a[:, i], entity_b, force_b[:, i], torque_b[:, i])

    def collides(self, a: Entity, b: Entity) -> bool:
        if not a.collides(b) or not b.collides(a) or a is b:
            return False
        a_shape = a.shape
        b_shape = b.shape
        if not a.movable and (not a.rotatable) and (not b.movable) and (not b.rotatable):
            return False
        if not {a_shape.__class__, b_shape.__class__} in self._collidable_pairs:
            return False
        if not (torch.linalg.vector_norm(a.state.pos - b.state.pos, dim=-1) <= a.shape.circumscribed_radius() + b.shape.circumscribed_radius()).any():
            return False
        return True

    def _get_constraint_forces(self, pos_a: Tensor, pos_b: Tensor, dist_min, force_multiplier: float, attractive: bool=False) -> Tensor:
        min_dist = 1e-06
        delta_pos = pos_a - pos_b
        dist = torch.linalg.vector_norm(delta_pos, dim=-1)
        sign = -1 if attractive else 1
        k = self._contact_margin
        penetration = torch.logaddexp(torch.tensor(0.0, dtype=torch.float32, device=self.device), (dist_min - dist) * sign / k) * k
        force = sign * force_multiplier * delta_pos / torch.where(dist > 0, dist, 1e-08).unsqueeze(-1) * penetration.unsqueeze(-1)
        force = torch.where((dist < min_dist).unsqueeze(-1), 0.0, force)
        if not attractive:
            force = torch.where((dist > dist_min).unsqueeze(-1), 0.0, force)
        else:
            force = torch.where((dist < dist_min).unsqueeze(-1), 0.0, force)
        return (force, -force)

    def _get_constraint_torques(self, rot_a: Tensor, rot_b: Tensor, force_multiplier: float=TORQUE_CONSTRAINT_FORCE) -> Tensor:
        min_delta_rot = 1e-09
        delta_rot = rot_a - rot_b
        abs_delta_rot = torch.linalg.vector_norm(delta_rot, dim=-1).unsqueeze(-1)
        k = 1
        penetration = k * (torch.exp(abs_delta_rot / k) - 1)
        torque = force_multiplier * delta_rot.sign() * penetration
        torque = torch.where(abs_delta_rot < min_delta_rot, 0.0, torque)
        return (-torque, torque)

    def _integrate_state(self, entity: Entity, substep: int):
        if entity.movable:
            if substep == 0:
                if entity.drag is not None:
                    entity.state.vel = entity.state.vel * (1 - entity.drag)
                else:
                    entity.state.vel = entity.state.vel * (1 - self._drag)
            accel = self.forces_dict[entity] / entity.mass
            entity.state.vel = entity.state.vel + accel * self._sub_dt
            if entity.max_speed is not None:
                entity.state.vel = TorchUtils.clamp_with_norm(entity.state.vel, entity.max_speed)
            if entity.v_range is not None:
                entity.state.vel = entity.state.vel.clamp(-entity.v_range, entity.v_range)
            new_pos = entity.state.pos + entity.state.vel * self._sub_dt
            entity.state.pos = torch.stack([new_pos[..., X].clamp(-self._x_semidim, self._x_semidim) if self._x_semidim is not None else new_pos[..., X], new_pos[..., Y].clamp(-self._y_semidim, self._y_semidim) if self._y_semidim is not None else new_pos[..., Y]], dim=-1)
        if entity.rotatable:
            if substep == 0:
                if entity.drag is not None:
                    entity.state.ang_vel = entity.state.ang_vel * (1 - entity.drag)
                else:
                    entity.state.ang_vel = entity.state.ang_vel * (1 - self._drag)
            entity.state.ang_vel = entity.state.ang_vel + self.torques_dict[entity] / entity.moment_of_inertia * self._sub_dt
            entity.state.rot = entity.state.rot + entity.state.ang_vel * self._sub_dt

    def _update_comm_state(self, agent):
        if not agent.silent:
            agent.state.c = agent.action.c

    @override(TorchVectorizedObject)
    def to(self, device: torch.device):
        super().to(device)
        for e in self.entities:
            e.to(device)

@property
def joints(self):
    return self._joints.values()

def _apply_gravity(self, entity: Entity):
    if entity.movable:
        if not (self._gravity == 0.0).all():
            self.forces_dict[entity] = self.forces_dict[entity] + entity.mass * self._gravity
        if entity.gravity is not None:
            self.forces_dict[entity] = self.forces_dict[entity] + entity.mass * entity.gravity

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

def _maybe_to_numpy(self, tensor):
    return TorchUtils.to_numpy(tensor) if self.return_numpy else tensor

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

class VelocityController:
    """
    Implements PID controller for velocity targets found in agent.action.u.
    Two forms of the PID controller are implemented: standard, and parallel. The controller takes 3 params, which
    are interpreted differently based on the form.
    > Standard form: ctrl_params=[gain, intg_ts, derv_ts]
                        intg_ts: rise time for integrator (err will be tolerated for this interval)
                        derv_ts: seek time for derivative (err is predicted over this interval)
                        These are specified in 1/dt scale (0.5 means 0.5/0.1==5sec)
    > Parallel form: ctrl_params=[kP, kI, kD]
                        kI and kD have no simple physical meaning, but are related to standard form params.
                        intg_ts = kP/kI and kD/kP = derv_ts
    """

    def __init__(self, agent: vmas.simulator.core.Agent, world: vmas.simulator.core.World, ctrl_params=(1, 0, 0), pid_form='standard'):
        self.agent = agent
        self.world = world
        self.dt = world.dt
        self.ctrl_gain = ctrl_params[0]
        if pid_form == 'standard':
            self.integralTs = ctrl_params[1]
            self.derivativeTs = ctrl_params[2]
        elif pid_form == 'parallel':
            if ctrl_params[1] == 0:
                self.integralTs = 0.0
            else:
                self.integralTs = self.ctrl_gain / ctrl_params[1]
            self.derivativeTs = ctrl_params[2] / self.ctrl_gain
        else:
            raise Exception('PID form is either standard or parallel.')
        if self.integralTs == 0:
            self.use_integrator = False
        else:
            self.use_integrator = True
            fmax = min(self.agent.max_f, self.agent.f_range, key=lambda x: x if x is not None else math.inf)
            if fmax is not None:
                self.integrator_windup_cutoff = 0.5 * fmax * self.integralTs / (self.dt * self.ctrl_gain)
            else:
                self.integrator_windup_cutoff = None
                warnings.warn('Force limits not specified. Integrator can wind up!')
        self.reset()

    def reset(self, index: Optional[int]=None):
        if index is None:
            self.accum_errs = torch.zeros((self.world.batch_dim, self.world.dim_p), device=self.world.device)
            self.prev_err = torch.zeros((self.world.batch_dim, self.world.dim_p), device=self.world.device)
        else:
            self.accum_errs = TorchUtils.where_from_index(index, 0.0, self.accum_errs)
            self.prev_err = TorchUtils.where_from_index(index, 0.0, self.prev_err)

    def integralError(self, err):
        if not self.use_integrator:
            return 0
        self.accum_errs += self.dt * err
        if self.integrator_windup_cutoff is not None:
            self.accum_errs = self.accum_errs.clamp(-self.integrator_windup_cutoff, self.integrator_windup_cutoff)
        return 1.0 / self.integralTs * self.accum_errs

    def rateError(self, err):
        e = self.derivativeTs * (err - self.prev_err) / self.dt
        self.prev_err = err
        return e

    def process_force(self):
        self.accum_errs = self.accum_errs.to(self.world.device)
        self.prev_err = self.prev_err.to(self.world.device)
        des_vel = self.agent.action.u
        cur_vel = self.agent.state.vel
        err = des_vel - cur_vel
        u = self.ctrl_gain * (err + self.integralError(err) + self.rateError(err))
        u *= self.agent.mass
        self.agent.action.u = u

def integralError(self, err):
    if not self.use_integrator:
        return 0
    self.accum_errs += self.dt * err
    if self.integrator_windup_cutoff is not None:
        self.accum_errs = self.accum_errs.clamp(-self.integrator_windup_cutoff, self.integrator_windup_cutoff)
    return 1.0 / self.integralTs * self.accum_errs

def random_nvecs(count, l_min=2, l_max=6, n_min=2, n_max=6, seed=0):
    random.seed(seed)
    return [[random.randint(n_min, n_max) for _ in range(random.randint(l_min, l_max))] for _ in range(count)]

def test_all_scenarios_included():
    from vmas import debug_scenarios, mpe_scenarios, scenarios
    assert sorted(scenario_names()) == sorted(scenarios + mpe_scenarios + debug_scenarios)

@pytest.mark.parametrize('scenario', scenario_names())
@pytest.mark.parametrize('continuous_actions', [True, False])
def test_use_vmas_env(scenario, continuous_actions, dict_spaces=True, num_envs=10, n_steps=10):
    render = True
    if sys.platform.startswith('win32'):
        render = False
    use_vmas_env(render=render, save_render=False, visualize_render=False, random_action=True, device='cpu', scenario_name=scenario, continuous_actions=continuous_actions, num_envs=num_envs, n_steps=n_steps, dict_spaces=dict_spaces)

@pytest.mark.parametrize('scenario', scenario_names())
def test_multi_discrete_actions(scenario, num_envs=10, n_steps=10):
    env = make_env(scenario=scenario, num_envs=num_envs, seed=0, multidiscrete_actions=True, continuous_actions=False)
    for _ in range(n_steps):
        env.step(env.get_random_actions())

@pytest.mark.parametrize('scenario', scenario_names())
@pytest.mark.parametrize('multidiscrete_actions', [True, False])
def test_discrete_action_nvec(scenario, multidiscrete_actions, num_envs=10, n_steps=5):
    env = make_env(scenario=scenario, num_envs=num_envs, seed=0, multidiscrete_actions=multidiscrete_actions, continuous_actions=False)
    if type(env.scenario).process_action is not vmas.simulator.scenario.BaseScenario.process_action:
        pytest.skip('Scenario uses a custom process_action method.')
    random.seed(0)
    for agent in env.world.agents:
        agent.discrete_action_nvec = [random.randint(2, 6) for _ in range(agent.action_size)]
    env.action_space = env.get_action_space()

    def to_multidiscrete(action, nvec):
        action_multi = []
        for i in range(len(nvec)):
            n = math.prod(nvec[i + 1:])
            action_multi.append(action // n)
            action = action % n
        return torch.stack(action_multi, dim=-1)

    def full_nvec(agent, world):
        return list(agent.discrete_action_nvec) + ([world.dim_c] if not agent.silent and world.dim_c != 0 else [])
    for _ in range(n_steps):
        actions = env.get_random_actions()
        for a_batch, s in zip(actions, env.action_space.spaces):
            for a in a_batch:
                assert a.numpy() in s
        env.step(actions)
        if not multidiscrete_actions:
            actions = [to_multidiscrete(a.squeeze(-1), full_nvec(agent, env.world)) for a, agent in zip(actions, env.world.policy_agents)]
        for i_a, agent in enumerate(env.world.policy_agents):
            for i, n in enumerate(agent.discrete_action_nvec):
                a = actions[i_a][:, i]
                u = agent.action.u[:, i]
                U = agent.action.u_range_tensor[i]
                k = agent.action.u_multiplier_tensor[i]
                for aj, uj in zip(a, u):
                    assert aj in range(n), f'discrete action {aj} not in [0,{n - 1}] (n={n}, U={U}, k={k})'
                    if n % 2 != 0:
                        assert aj != 0 or uj == 0, f'discrete action {aj} maps to control {uj} (n={n}), U={U}, k={k})'
                        assert (aj < 1 or aj > n // 2) or torch.isclose(uj / k, 2 * U * (aj - 1) / (n - 1) - U), f'discrete action {aj} maps to control {uj} (n={n}, U={U}, k={k})'
                        assert aj <= n // 2 or torch.isclose(uj / k, 2 * U * (aj / (n - 1)) - U), f'discrete action {aj} maps to control {uj} (n={n}), U={U}, k={k})'
                    else:
                        assert torch.isclose(uj / k, 2 * U * (aj / (n - 1)) - U), f'discrete action {aj} maps to control {uj} (n={n}), U={U}, k={k})'

def full_nvec(agent, world):
    return list(agent.discrete_action_nvec) + ([world.dim_c] if not agent.silent and world.dim_c != 0 else [])

@pytest.mark.parametrize('nvecs', list(zip(random_nvecs(10, seed=0), random_nvecs(10, seed=42))))
def test_discrete_action_nvec_discrete_to_multi(nvecs, scenario='transport', num_envs=10, n_steps=5):
    kwargs = {'scenario': scenario, 'num_envs': num_envs, 'seed': 0, 'continuous_actions': False}
    env = make_env(**kwargs, multidiscrete_actions=False)
    env_multi = make_env(**kwargs, multidiscrete_actions=True)
    if type(env.scenario).process_action is not vmas.simulator.scenario.BaseScenario.process_action:
        pytest.skip('Scenario uses a custom process_action method.')

    def set_nvec(agent, nvec):
        agent.action_size = len(nvec)
        agent.discrete_action_nvec = nvec
        agent.action.action_size = agent.action_size
    random.seed(0)
    for agent, agent_multi, nvec in zip(env.world.policy_agents, env_multi.world.policy_agents, nvecs):
        set_nvec(agent, nvec)
        set_nvec(agent_multi, nvec)
    env.action_space = env.get_action_space()
    env_multi.action_space = env.get_action_space()

    def full_nvec(agent, world):
        return list(agent.discrete_action_nvec) + ([world.dim_c] if not agent.silent and world.dim_c != 0 else [])

    def full_action_size(agent, world):
        return len(full_nvec(agent, world))
    for _ in range(n_steps):
        actions_multi = env_multi.get_random_actions()
        prodss = [[math.prod(full_nvec(agent, env.world)[i + 1:]) for i in range(full_action_size(agent, env.world))] for agent in env.world.policy_agents]
        actions = [(a_multi * torch.tensor(prods)).sum(dim=1) for a_multi, prods in zip(actions_multi, prodss)]
        env_multi.step(actions_multi)
        env.step(actions)
        for agent, agent_multi, action, action_multi in zip(env.world.policy_agents, env_multi.world.policy_agents, actions, actions_multi):
            U = agent.action.u_range_tensor
            k = agent.action.u_multiplier_tensor
            for u, u_multi, a, a_multi in zip(agent.action.u, agent_multi.action.u, action, action_multi):
                assert torch.allclose(u, u_multi), f'{u} != {u_multi} (nvec={agent.discrete_action_nvec}, a={a}, a_multi={a_multi}, U={U}, k={k})'

def full_action_size(agent, world):
    return len(full_nvec(agent, world))

@pytest.mark.parametrize('scenario', scenario_names())
def test_non_dict_spaces_actions(scenario, num_envs=10, n_steps=10):
    env = make_env(scenario=scenario, num_envs=num_envs, seed=0, continuous_actions=True, dict_spaces=False)
    for _ in range(n_steps):
        env.step(env.get_random_actions())

@pytest.mark.parametrize('scenario', scenario_names())
def test_partial_reset(scenario, num_envs=10, n_steps=10):
    env = make_env(scenario=scenario, num_envs=num_envs, seed=0)
    env_index = 0
    for _ in range(n_steps):
        env.step(env.get_random_actions())
        env.reset_at(env_index)
        env_index += 1
        if env_index >= num_envs:
            env_index = 0

@pytest.mark.parametrize('scenario', scenario_names())
def test_global_reset(scenario, num_envs=10, n_steps=10):
    env = make_env(scenario=scenario, num_envs=num_envs, seed=0)
    for step in range(n_steps):
        env.step(env.get_random_actions())
        if step == n_steps // 2:
            env.reset()

@pytest.mark.parametrize('scenario', vmas.scenarios + vmas.mpe_scenarios)
def test_vmas_differentiable(scenario, n_steps=10, n_envs=10):
    if scenario == 'football' or scenario == 'simple_crypto' or scenario == 'road_traffic':
        pytest.skip()
    env = make_env(scenario=scenario, num_envs=n_envs, continuous_actions=True, seed=0, grad_enabled=True)
    for step in range(n_steps):
        actions = []
        for agent in env.agents:
            action = env.get_random_action(agent)
            action.requires_grad_(True)
            if step == 0:
                first_action = action
            actions.append(action)
        obs, rews, dones, info = env.step(actions)
    loss = obs[-1].mean() + rews[-1].mean()
    grad = torch.autograd.grad(loss, first_action)

def test_seeding():
    env = make_env(scenario='balance', num_envs=2, seed=0)
    env.seed(0)
    random_obs = env.reset()[0][0, 0]
    env.seed(0)
    assert random_obs == env.reset()[0][0, 0]
    env.seed(0)
    torch.manual_seed(1)
    assert random_obs == env.reset()[0][0, 0]
    torch.manual_seed(0)
    random_obs = torch.randn(1)
    torch.manual_seed(0)
    env.seed(1)
    env.reset()
    assert random_obs == torch.randn(1)

def get_obs(env):
    rollout_obs = []
    for _ in range(n_steps):
        obs, _, _, _ = env.step(env.get_random_actions())
        obs = torch.stack(obs, dim=-1)
        rollout_obs.append(obs)
    return torch.stack(rollout_obs, dim=-1)

def test_vectorized_lidar(n_envs=12, n_steps=15):

    def get_obs(env):
        rollout_obs = []
        for _ in range(n_steps):
            obs, _, _, _ = env.step(env.get_random_actions())
            obs = torch.stack(obs, dim=-1)
            rollout_obs.append(obs)
        return torch.stack(rollout_obs, dim=-1)
    env_vec_lidar = make_env(scenario='pollock', num_envs=n_envs, seed=0, lidar=True, vectorized_lidar=True)
    obs_vec_lidar = get_obs(env_vec_lidar)
    env_non_vec_lidar = make_env(scenario='pollock', num_envs=n_envs, seed=0, lidar=True, vectorized_lidar=False)
    obs_non_vec_lidar = get_obs(env_non_vec_lidar)
    assert torch.allclose(obs_vec_lidar, obs_non_vec_lidar)

class TestNavigation:

    def setUp(self, n_envs, n_agents) -> None:
        self.continuous_actions = True
        self.env = make_env(scenario='navigation', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [1])
    def test_heuristic(self, n_agents, n_envs=5):
        self.setUp(n_envs=n_envs, n_agents=n_agents)
        policy = HeuristicPolicy(continuous_action=self.continuous_actions, clf_epsilon=0.4, clf_slack=100.0)
        obs = self.env.reset()
        all_done = torch.zeros(n_envs, dtype=torch.bool)
        while not all_done.all():
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].action.u_range_tensor)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            if dones.any():
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

def setUp(self, n_envs, n_agents) -> None:
    self.continuous_actions = True
    self.env = make_env(scenario='navigation', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [1])
def test_heuristic(self, n_agents, n_envs=5):
    self.setUp(n_envs=n_envs, n_agents=n_agents)
    policy = HeuristicPolicy(continuous_action=self.continuous_actions, clf_epsilon=0.4, clf_slack=100.0)
    obs = self.env.reset()
    all_done = torch.zeros(n_envs, dtype=torch.bool)
    while not all_done.all():
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].action.u_range_tensor)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        if dones.any():
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

class TestTransport:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.n_agents = kwargs.get('n_agents', 4)
        self.n_packages = kwargs.get('n_packages', 1)
        self.package_width = kwargs.get('package_width', 0.15)
        self.package_length = kwargs.get('package_length', 0.15)
        self.package_mass = kwargs.get('package_mass', 50)
        self.continuous_actions = True
        self.env = make_env(scenario='transport', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
        self.env.seed(0)

    def test_not_passing_through_packages(self, n_agents=1, n_envs=4):
        self.setup_env(n_agents=n_agents, n_envs=n_envs)
        for _ in range(10):
            obs = self.env.reset()
            for _ in range(100):
                obs_agent = obs[0]
                assert (torch.linalg.vector_norm(obs_agent[:, 6:8], dim=1) > self.env.agents[0].shape.radius).all()
                action_agent = torch.clamp(obs_agent[:, 6:8], min=-self.env.agents[0].u_range, max=self.env.agents[0].u_range)
                action_agent /= torch.linalg.vector_norm(action_agent, dim=1).unsqueeze(-1)
                action_agent *= self.env.agents[0].u_range
                obs, rews, dones, _ = self.env.step([action_agent])

    @pytest.mark.parametrize('n_agents', [6])
    def test_heuristic(self, n_agents, n_envs=4):
        self.setup_env(n_agents=n_agents, n_envs=n_envs)
        policy = transport.HeuristicPolicy(self.continuous_actions)
        obs = self.env.reset()
        all_done = torch.zeros(n_envs, dtype=torch.bool)
        while not all_done.all():
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            if dones.any():
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

def setup_env(self, n_envs, **kwargs) -> None:
    self.n_agents = kwargs.get('n_agents', 4)
    self.n_packages = kwargs.get('n_packages', 1)
    self.package_width = kwargs.get('package_width', 0.15)
    self.package_length = kwargs.get('package_length', 0.15)
    self.package_mass = kwargs.get('package_mass', 50)
    self.continuous_actions = True
    self.env = make_env(scenario='transport', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
    self.env.seed(0)

def test_not_passing_through_packages(self, n_agents=1, n_envs=4):
    self.setup_env(n_agents=n_agents, n_envs=n_envs)
    for _ in range(10):
        obs = self.env.reset()
        for _ in range(100):
            obs_agent = obs[0]
            assert (torch.linalg.vector_norm(obs_agent[:, 6:8], dim=1) > self.env.agents[0].shape.radius).all()
            action_agent = torch.clamp(obs_agent[:, 6:8], min=-self.env.agents[0].u_range, max=self.env.agents[0].u_range)
            action_agent /= torch.linalg.vector_norm(action_agent, dim=1).unsqueeze(-1)
            action_agent *= self.env.agents[0].u_range
            obs, rews, dones, _ = self.env.step([action_agent])

@pytest.mark.parametrize('n_agents', [6])
def test_heuristic(self, n_agents, n_envs=4):
    self.setup_env(n_agents=n_agents, n_envs=n_envs)
    policy = transport.HeuristicPolicy(self.continuous_actions)
    obs = self.env.reset()
    all_done = torch.zeros(n_envs, dtype=torch.bool)
    while not all_done.all():
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        if dones.any():
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

class TestWheel:

    def setup_env(self, n_envs, n_agents, **kwargs) -> None:
        self.desired_velocity = kwargs.get('desired_velocity', 0.1)
        self.continuous_actions = True
        self.n_envs = 15
        self.env = make_env(scenario='wheel', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents, **kwargs)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [2, 10])
    def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
        line_length = 2
        self.setup_env(n_agents=n_agents, line_length=line_length, n_envs=n_envs)
        policy = wheel.HeuristicPolicy(self.continuous_actions)
        obs = self.env.reset()
        for _ in range(n_steps):
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)

def setup_env(self, n_envs, n_agents, **kwargs) -> None:
    self.desired_velocity = kwargs.get('desired_velocity', 0.1)
    self.continuous_actions = True
    self.n_envs = 15
    self.env = make_env(scenario='wheel', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents, **kwargs)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [2, 10])
def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
    line_length = 2
    self.setup_env(n_agents=n_agents, line_length=line_length, n_envs=n_envs)
    policy = wheel.HeuristicPolicy(self.continuous_actions)
    obs = self.env.reset()
    for _ in range(n_steps):
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)

class TestDispersion:

    def setup_env(self, n_agents: int, share_reward: bool, penalise_by_time: bool, n_envs) -> None:
        self.n_agents = n_agents
        self.share_reward = share_reward
        self.penalise_by_time = penalise_by_time
        self.continuous_actions = True
        self.env = make_env(scenario='dispersion', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=self.n_agents, share_reward=self.share_reward, penalise_by_time=self.penalise_by_time)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [1, 5, 10])
    def test_heuristic(self, n_agents, n_envs=4):
        self.setup_env(n_agents=n_agents, share_reward=False, penalise_by_time=False, n_envs=n_envs)
        all_done = torch.full((n_envs,), False)
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs, n_agents)
        while not all_done.all():
            actions = []
            idx = 0
            for i in range(n_agents):
                obs_agent = obs[i]
                obs_idx = 4 + idx
                action_agent = torch.clamp(obs_agent[:, obs_idx:obs_idx + 2], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                idx += 3
                actions.append(action_agent)
            obs, rews, dones, _ = self.env.step(actions)
            for i in range(n_agents):
                total_rew[:, i] += rews[i]
            if dones.any():
                assert torch.equal(total_rew[dones].sum(-1).to(torch.long), torch.full((dones.sum(),), n_agents))
                total_rew[dones] = 0
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

    @pytest.mark.parametrize('n_agents', [1, 5, 10, 20])
    def test_heuristic_share_reward(self, n_agents, n_envs=4):
        self.setup_env(n_agents=n_agents, share_reward=True, penalise_by_time=False, n_envs=n_envs)
        all_done = torch.full((n_envs,), False)
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs, n_agents)
        while not all_done.all():
            actions = []
            idx = 0
            for i in range(n_agents):
                obs_agent = obs[i]
                obs_idx = 4 + idx
                action_agent = torch.clamp(obs_agent[:, obs_idx:obs_idx + 2], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                idx += 3
                actions.append(action_agent)
            obs, rews, dones, _ = self.env.step(actions)
            for i in range(n_agents):
                total_rew[:, i] += rews[i]
            if dones.any():
                assert torch.equal(total_rew[dones], torch.full((dones.sum(), n_agents), n_agents).to(torch.float))
                total_rew[dones] = 0
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

def setup_env(self, n_agents: int, share_reward: bool, penalise_by_time: bool, n_envs) -> None:
    self.n_agents = n_agents
    self.share_reward = share_reward
    self.penalise_by_time = penalise_by_time
    self.continuous_actions = True
    self.env = make_env(scenario='dispersion', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=self.n_agents, share_reward=self.share_reward, penalise_by_time=self.penalise_by_time)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [1, 5, 10])
def test_heuristic(self, n_agents, n_envs=4):
    self.setup_env(n_agents=n_agents, share_reward=False, penalise_by_time=False, n_envs=n_envs)
    all_done = torch.full((n_envs,), False)
    obs = self.env.reset()
    total_rew = torch.zeros(self.env.num_envs, n_agents)
    while not all_done.all():
        actions = []
        idx = 0
        for i in range(n_agents):
            obs_agent = obs[i]
            obs_idx = 4 + idx
            action_agent = torch.clamp(obs_agent[:, obs_idx:obs_idx + 2], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            idx += 3
            actions.append(action_agent)
        obs, rews, dones, _ = self.env.step(actions)
        for i in range(n_agents):
            total_rew[:, i] += rews[i]
        if dones.any():
            assert torch.equal(total_rew[dones].sum(-1).to(torch.long), torch.full((dones.sum(),), n_agents))
            total_rew[dones] = 0
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

@pytest.mark.parametrize('n_agents', [1, 5, 10, 20])
def test_heuristic_share_reward(self, n_agents, n_envs=4):
    self.setup_env(n_agents=n_agents, share_reward=True, penalise_by_time=False, n_envs=n_envs)
    all_done = torch.full((n_envs,), False)
    obs = self.env.reset()
    total_rew = torch.zeros(self.env.num_envs, n_agents)
    while not all_done.all():
        actions = []
        idx = 0
        for i in range(n_agents):
            obs_agent = obs[i]
            obs_idx = 4 + idx
            action_agent = torch.clamp(obs_agent[:, obs_idx:obs_idx + 2], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            idx += 3
            actions.append(action_agent)
        obs, rews, dones, _ = self.env.step(actions)
        for i in range(n_agents):
            total_rew[:, i] += rews[i]
        if dones.any():
            assert torch.equal(total_rew[dones], torch.full((dones.sum(), n_agents), n_agents).to(torch.float))
            total_rew[dones] = 0
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

class TestDiscovery:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.env = make_env(scenario='discovery', num_envs=n_envs, device='cpu', **kwargs)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [1, 4])
    @pytest.mark.parametrize('agent_lidar', [True, False])
    def test_heuristic(self, n_agents, agent_lidar, n_steps=50, n_envs=4):
        self.setup_env(n_agents=n_agents, n_envs=n_envs, use_agent_lidar=agent_lidar)
        policy = discovery.HeuristicPolicy(True)
        obs = self.env.reset()
        for _ in range(n_steps):
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)

def setup_env(self, n_envs, **kwargs) -> None:
    self.env = make_env(scenario='discovery', num_envs=n_envs, device='cpu', **kwargs)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [1, 4])
@pytest.mark.parametrize('agent_lidar', [True, False])
def test_heuristic(self, n_agents, agent_lidar, n_steps=50, n_envs=4):
    self.setup_env(n_agents=n_agents, n_envs=n_envs, use_agent_lidar=agent_lidar)
    policy = discovery.HeuristicPolicy(True)
    obs = self.env.reset()
    for _ in range(n_steps):
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)

class TestDropout:

    def setup_env(self, n_agents: int, num_envs: int, energy_coeff: float=DEFAULT_ENERGY_COEFF) -> None:
        self.n_agents = n_agents
        self.energy_coeff = energy_coeff
        self.continuous_actions = True
        self.n_envs = num_envs
        self.env = make_env(scenario='dropout', num_envs=num_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=self.n_agents, energy_coeff=self.energy_coeff)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [1, 5])
    def test_heuristic(self, n_agents, n_envs=4):
        self.setup_env(n_agents=n_agents, num_envs=n_envs)
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs)
        current_min = float('inf')
        best_i = None
        for i in range(n_agents):
            obs_agent = obs[i]
            if torch.linalg.vector_norm(obs_agent[:, -3:-1], dim=1)[0] < current_min:
                current_min = torch.linalg.vector_norm(obs_agent[:, -3:-1], dim=1)[0]
                best_i = i
        done = False
        while not done:
            obs_agent = obs[best_i]
            action_agent = torch.clamp(obs_agent[:, -3:-1], min=-self.env.agents[best_i].u_range, max=self.env.agents[best_i].u_range)
            actions = []
            other_agents_action = torch.zeros(self.env.num_envs, self.env.world.dim_p)
            for j in range(self.n_agents):
                if best_i != j:
                    actions.append(other_agents_action)
                else:
                    actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            for j in range(self.n_agents):
                assert torch.equal(new_rews[0], new_rews[j])
            total_rew += new_rews[0]
            assert (total_rew[dones] > 0).all()
            done = dones.any()

    @pytest.mark.parametrize('n_agents', [1, 5])
    def test_one_random_agent_can_do_it(self, n_agents, n_steps=50, n_envs=4):
        self.setup_env(n_agents=n_agents, num_envs=n_envs)
        for i in range(self.n_agents):
            obs = self.env.reset()
            total_rew = torch.zeros(self.env.num_envs)
            for _ in range(n_steps):
                obs_agent = obs[i]
                action_agent = torch.clamp(obs_agent[:, -3:-1], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                actions = []
                other_agents_action = torch.zeros(self.env.num_envs, self.env.world.dim_p)
                for j in range(self.n_agents):
                    if i != j:
                        actions.append(other_agents_action)
                    else:
                        actions.append(action_agent)
                obs, new_rews, dones, _ = self.env.step(actions)
                for j in range(self.n_agents):
                    assert torch.equal(new_rews[0], new_rews[j])
                total_rew += new_rews[0]
                assert (total_rew[dones] > 0).all()
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)
                total_rew[dones] = 0

    @pytest.mark.parametrize('n_agents', [5, 10])
    def test_all_agents_cannot_do_it(self, n_agents):
        assert self.all_agents(DEFAULT_ENERGY_COEFF, n_agents) < 0
        assert self.all_agents(0, n_agents) > 0

    def all_agents(self, energy_coeff: float, n_agents: int, n_steps=100, n_envs=4):
        rewards = []
        self.setup_env(n_agents=n_agents, energy_coeff=energy_coeff, num_envs=n_envs)
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs)
        for _ in range(n_steps):
            actions = []
            for i in range(self.n_agents):
                obs_i = obs[i]
                action_i = torch.clamp(obs_i[:, -3:-1], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                actions.append(action_i)
            obs, new_rews, dones, _ = self.env.step(actions)
            for j in range(self.n_agents):
                assert torch.equal(new_rews[0], new_rews[j])
            total_rew += new_rews[0]
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)
            if dones.any():
                rewards.append(total_rew[dones].clone())
            total_rew[dones] = 0
        return sum([rew.mean().item() for rew in rewards]) / len(rewards)

def setup_env(self, n_agents: int, num_envs: int, energy_coeff: float=DEFAULT_ENERGY_COEFF) -> None:
    self.n_agents = n_agents
    self.energy_coeff = energy_coeff
    self.continuous_actions = True
    self.n_envs = num_envs
    self.env = make_env(scenario='dropout', num_envs=num_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=self.n_agents, energy_coeff=self.energy_coeff)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [1, 5])
def test_heuristic(self, n_agents, n_envs=4):
    self.setup_env(n_agents=n_agents, num_envs=n_envs)
    obs = self.env.reset()
    total_rew = torch.zeros(self.env.num_envs)
    current_min = float('inf')
    best_i = None
    for i in range(n_agents):
        obs_agent = obs[i]
        if torch.linalg.vector_norm(obs_agent[:, -3:-1], dim=1)[0] < current_min:
            current_min = torch.linalg.vector_norm(obs_agent[:, -3:-1], dim=1)[0]
            best_i = i
    done = False
    while not done:
        obs_agent = obs[best_i]
        action_agent = torch.clamp(obs_agent[:, -3:-1], min=-self.env.agents[best_i].u_range, max=self.env.agents[best_i].u_range)
        actions = []
        other_agents_action = torch.zeros(self.env.num_envs, self.env.world.dim_p)
        for j in range(self.n_agents):
            if best_i != j:
                actions.append(other_agents_action)
            else:
                actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        for j in range(self.n_agents):
            assert torch.equal(new_rews[0], new_rews[j])
        total_rew += new_rews[0]
        assert (total_rew[dones] > 0).all()
        done = dones.any()

@pytest.mark.parametrize('n_agents', [1, 5])
def test_one_random_agent_can_do_it(self, n_agents, n_steps=50, n_envs=4):
    self.setup_env(n_agents=n_agents, num_envs=n_envs)
    for i in range(self.n_agents):
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs)
        for _ in range(n_steps):
            obs_agent = obs[i]
            action_agent = torch.clamp(obs_agent[:, -3:-1], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            actions = []
            other_agents_action = torch.zeros(self.env.num_envs, self.env.world.dim_p)
            for j in range(self.n_agents):
                if i != j:
                    actions.append(other_agents_action)
                else:
                    actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            for j in range(self.n_agents):
                assert torch.equal(new_rews[0], new_rews[j])
            total_rew += new_rews[0]
            assert (total_rew[dones] > 0).all()
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)
            total_rew[dones] = 0

@pytest.mark.parametrize('n_agents', [5, 10])
def test_all_agents_cannot_do_it(self, n_agents):
    assert self.all_agents(DEFAULT_ENERGY_COEFF, n_agents) < 0
    assert self.all_agents(0, n_agents) > 0

def all_agents(self, energy_coeff: float, n_agents: int, n_steps=100, n_envs=4):
    rewards = []
    self.setup_env(n_agents=n_agents, energy_coeff=energy_coeff, num_envs=n_envs)
    obs = self.env.reset()
    total_rew = torch.zeros(self.env.num_envs)
    for _ in range(n_steps):
        actions = []
        for i in range(self.n_agents):
            obs_i = obs[i]
            action_i = torch.clamp(obs_i[:, -3:-1], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            actions.append(action_i)
        obs, new_rews, dones, _ = self.env.step(actions)
        for j in range(self.n_agents):
            assert torch.equal(new_rews[0], new_rews[j])
        total_rew += new_rews[0]
        for env_index, done in enumerate(dones):
            if done:
                self.env.reset_at(env_index)
        if dones.any():
            rewards.append(total_rew[dones].clone())
        total_rew[dones] = 0
    return sum([rew.mean().item() for rew in rewards]) / len(rewards)

class TestBalance:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.n_agents = kwargs.get('n_agents', 4)
        self.continuous_actions = True
        self.env = make_env(scenario='balance', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [2, 5])
    def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
        self.setup_env(n_agents=n_agents, random_package_pos_on_line=False, n_envs=n_envs)
        policy = balance.HeuristicPolicy(self.continuous_actions)
        obs = self.env.reset()
        prev_package_dist_to_goal = obs[0][:, 8:10]
        for _ in range(n_steps):
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                package_dist_to_goal = obs_agent[:, 8:10]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            assert (torch.linalg.vector_norm(package_dist_to_goal, dim=-1) <= torch.linalg.vector_norm(prev_package_dist_to_goal, dim=-1)).all()
            prev_package_dist_to_goal = package_dist_to_goal

def setup_env(self, n_envs, **kwargs) -> None:
    self.n_agents = kwargs.get('n_agents', 4)
    self.continuous_actions = True
    self.env = make_env(scenario='balance', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [2, 5])
def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
    self.setup_env(n_agents=n_agents, random_package_pos_on_line=False, n_envs=n_envs)
    policy = balance.HeuristicPolicy(self.continuous_actions)
    obs = self.env.reset()
    prev_package_dist_to_goal = obs[0][:, 8:10]
    for _ in range(n_steps):
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            package_dist_to_goal = obs_agent[:, 8:10]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        assert (torch.linalg.vector_norm(package_dist_to_goal, dim=-1) <= torch.linalg.vector_norm(prev_package_dist_to_goal, dim=-1)).all()
        prev_package_dist_to_goal = package_dist_to_goal

class TestWaterfall:

    def setUp(self, n_envs, n_agents) -> None:
        self.continuous_actions = True
        self.env = make_env(scenario='waterfall', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents)
        self.env.seed(0)

    def test_heuristic(self, n_agents=5, n_envs=4, n_steps=50):
        self.setUp(n_envs=n_envs, n_agents=n_agents)
        obs = self.env.reset()
        for _ in range(n_steps):
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = torch.clamp(obs_agent[:, -2:], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, _, _ = self.env.step(actions)

def setUp(self, n_envs, n_agents) -> None:
    self.continuous_actions = True
    self.env = make_env(scenario='waterfall', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, n_agents=n_agents)
    self.env.seed(0)

def test_heuristic(self, n_agents=5, n_envs=4, n_steps=50):
    self.setUp(n_envs=n_envs, n_agents=n_agents)
    obs = self.env.reset()
    for _ in range(n_steps):
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = torch.clamp(obs_agent[:, -2:], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, _, _ = self.env.step(actions)

class TestGiveWay:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.continuous_actions = True
        self.env = make_env(scenario='give_way', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
        self.env.seed(0)

    def test_heuristic(self, n_envs=4):
        self.setup_env(mirror_passage=False, n_envs=n_envs)
        all_done = torch.full((n_envs,), False)
        obs = self.env.reset()
        u_range = self.env.agents[0].u_range
        total_rew = torch.zeros((n_envs,))
        while not (total_rew > 17).all():
            obs_agent = obs[0]
            if (obs[1][:, :1] < 0).all():
                action_1 = torch.tensor([u_range / 2, -u_range]).repeat(n_envs, 1)
            else:
                action_1 = torch.tensor([u_range / 2, u_range]).repeat(n_envs, 1)
            action_2 = torch.tensor([-u_range / 3, 0]).repeat(n_envs, 1)
            obs, rews, dones, _ = self.env.step([action_1, action_2])
            for rew in rews:
                total_rew += rew
            if dones.any():
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

def setup_env(self, n_envs, **kwargs) -> None:
    self.continuous_actions = True
    self.env = make_env(scenario='give_way', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
    self.env.seed(0)

def test_heuristic(self, n_envs=4):
    self.setup_env(mirror_passage=False, n_envs=n_envs)
    all_done = torch.full((n_envs,), False)
    obs = self.env.reset()
    u_range = self.env.agents[0].u_range
    total_rew = torch.zeros((n_envs,))
    while not (total_rew > 17).all():
        obs_agent = obs[0]
        if (obs[1][:, :1] < 0).all():
            action_1 = torch.tensor([u_range / 2, -u_range]).repeat(n_envs, 1)
        else:
            action_1 = torch.tensor([u_range / 2, u_range]).repeat(n_envs, 1)
        action_2 = torch.tensor([-u_range / 3, 0]).repeat(n_envs, 1)
        obs, rews, dones, _ = self.env.step([action_1, action_2])
        for rew in rews:
            total_rew += rew
        if dones.any():
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

class TestReverseTransport:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.n_agents = kwargs.get('n_agents', 4)
        self.package_width = kwargs.get('package_width', 0.6)
        self.package_length = kwargs.get('package_length', 0.6)
        self.package_mass = kwargs.get('package_mass', 50)
        self.continuous_actions = True
        self.env = make_env(scenario='reverse_transport', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [5])
    def test_heuristic(self, n_agents, n_envs=4):
        self.setup_env(n_agents=n_agents, n_envs=n_envs)
        obs = self.env.reset()
        all_done = torch.full((n_envs,), False)
        while not all_done.all():
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = torch.clamp(-obs_agent[:, -2:], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            if dones.any():
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

def setup_env(self, n_envs, **kwargs) -> None:
    self.n_agents = kwargs.get('n_agents', 4)
    self.package_width = kwargs.get('package_width', 0.6)
    self.package_length = kwargs.get('package_length', 0.6)
    self.package_mass = kwargs.get('package_mass', 50)
    self.continuous_actions = True
    self.env = make_env(scenario='reverse_transport', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [5])
def test_heuristic(self, n_agents, n_envs=4):
    self.setup_env(n_agents=n_agents, n_envs=n_envs)
    obs = self.env.reset()
    all_done = torch.full((n_envs,), False)
    while not all_done.all():
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = torch.clamp(-obs_agent[:, -2:], min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        if dones.any():
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    self.env.reset_at(env_index)

class TestFootball:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.continuous_actions = True
        self.env = make_env(scenario='football', num_envs=n_envs, device='cpu', continuous_actions=True, **kwargs)
        self.env.seed(0)

    @pytest.mark.skipif(sys.platform.startswith('win32'), reason='Test does not work on windows')
    def test_ai_vs_random(self, n_envs=4, n_agents=3, scoring_reward=1):
        self.setup_env(n_red_agents=n_agents, n_blue_agents=n_agents, ai_red_agents=True, ai_blue_agents=False, dense_reward=False, n_envs=n_envs, scoring_reward=scoring_reward)
        all_done = torch.full((n_envs,), False)
        obs = self.env.reset()
        total_rew = torch.zeros(self.env.num_envs, n_agents)
        with tqdm(total=n_envs) as pbar:
            while not all_done.all():
                pbar.update(all_done.sum().item() - pbar.n)
                actions = []
                for _ in range(n_agents):
                    actions.append(torch.rand(n_envs, 2))
                obs, rews, dones, _ = self.env.step(actions)
                for i in range(n_agents):
                    total_rew[:, i] += rews[i]
                if dones.any():
                    actual_rew = -scoring_reward * n_agents
                    assert torch.equal(total_rew[dones].sum(-1).to(torch.long), torch.full((dones.sum(),), actual_rew, dtype=torch.long))
                    total_rew[dones] = 0
                    all_done += dones
                    for env_index, done in enumerate(dones):
                        if done:
                            self.env.reset_at(env_index)

def setup_env(self, n_envs, **kwargs) -> None:
    self.continuous_actions = True
    self.env = make_env(scenario='football', num_envs=n_envs, device='cpu', continuous_actions=True, **kwargs)
    self.env.seed(0)

@pytest.mark.skipif(sys.platform.startswith('win32'), reason='Test does not work on windows')
def test_ai_vs_random(self, n_envs=4, n_agents=3, scoring_reward=1):
    self.setup_env(n_red_agents=n_agents, n_blue_agents=n_agents, ai_red_agents=True, ai_blue_agents=False, dense_reward=False, n_envs=n_envs, scoring_reward=scoring_reward)
    all_done = torch.full((n_envs,), False)
    obs = self.env.reset()
    total_rew = torch.zeros(self.env.num_envs, n_agents)
    with tqdm(total=n_envs) as pbar:
        while not all_done.all():
            pbar.update(all_done.sum().item() - pbar.n)
            actions = []
            for _ in range(n_agents):
                actions.append(torch.rand(n_envs, 2))
            obs, rews, dones, _ = self.env.step(actions)
            for i in range(n_agents):
                total_rew[:, i] += rews[i]
            if dones.any():
                actual_rew = -scoring_reward * n_agents
                assert torch.equal(total_rew[dones].sum(-1).to(torch.long), torch.full((dones.sum(),), actual_rew, dtype=torch.long))
                total_rew[dones] = 0
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        self.env.reset_at(env_index)

class TestPassage:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.n_passages = kwargs.get('n_passages', 4)
        self.continuous_actions = True
        self.env = make_env(scenario='passage', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
        self.env.seed(0)

    def test_heuristic(self, n_envs=4):
        self.setup_env(n_passages=1, shared_reward=True, n_envs=4)
        obs = self.env.reset()
        agent_switched = torch.full((5, n_envs), False)
        all_done = torch.full((n_envs,), False)
        while not all_done.all():
            actions = []
            for i in range(5):
                obs_agent = obs[i]
                dist_to_passage = obs_agent[:, 6:8]
                dist_to_goal = obs_agent[:, 4:6]
                dist_to_passage_is_close = torch.linalg.vector_norm(dist_to_passage, dim=1) <= 0.025
                action_agent = torch.clamp(2 * dist_to_passage, min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
                agent_switched[i] += dist_to_passage_is_close
                action_agent[agent_switched[i]] = torch.clamp(2 * dist_to_goal, min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)[agent_switched[i]]
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)
            if dones.any():
                all_done += dones
                for env_index, done in enumerate(dones):
                    if done:
                        agent_switched[:, env_index] = False
                        self.env.reset_at(env_index)

def setup_env(self, n_envs, **kwargs) -> None:
    self.n_passages = kwargs.get('n_passages', 4)
    self.continuous_actions = True
    self.env = make_env(scenario='passage', num_envs=n_envs, device='cpu', continuous_actions=self.continuous_actions, **kwargs)
    self.env.seed(0)

def test_heuristic(self, n_envs=4):
    self.setup_env(n_passages=1, shared_reward=True, n_envs=4)
    obs = self.env.reset()
    agent_switched = torch.full((5, n_envs), False)
    all_done = torch.full((n_envs,), False)
    while not all_done.all():
        actions = []
        for i in range(5):
            obs_agent = obs[i]
            dist_to_passage = obs_agent[:, 6:8]
            dist_to_goal = obs_agent[:, 4:6]
            dist_to_passage_is_close = torch.linalg.vector_norm(dist_to_passage, dim=1) <= 0.025
            action_agent = torch.clamp(2 * dist_to_passage, min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)
            agent_switched[i] += dist_to_passage_is_close
            action_agent[agent_switched[i]] = torch.clamp(2 * dist_to_goal, min=-self.env.agents[i].u_range, max=self.env.agents[i].u_range)[agent_switched[i]]
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)
        if dones.any():
            all_done += dones
            for env_index, done in enumerate(dones):
                if done:
                    agent_switched[:, env_index] = False
                    self.env.reset_at(env_index)

class TestFlocking:

    def setup_env(self, n_envs, **kwargs) -> None:
        self.env = make_env(scenario='flocking', num_envs=n_envs, device='cpu', **kwargs)
        self.env.seed(0)

    @pytest.mark.parametrize('n_agents', [1, 5])
    def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
        self.setup_env(n_agents=n_agents, n_envs=n_envs)
        policy = flocking.HeuristicPolicy(True)
        obs = self.env.reset()
        for _ in range(n_steps):
            actions = []
            for i in range(n_agents):
                obs_agent = obs[i]
                action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
                actions.append(action_agent)
            obs, new_rews, dones, _ = self.env.step(actions)

def setup_env(self, n_envs, **kwargs) -> None:
    self.env = make_env(scenario='flocking', num_envs=n_envs, device='cpu', **kwargs)
    self.env.seed(0)

@pytest.mark.parametrize('n_agents', [1, 5])
def test_heuristic(self, n_agents, n_steps=50, n_envs=4):
    self.setup_env(n_agents=n_agents, n_envs=n_envs)
    policy = flocking.HeuristicPolicy(True)
    obs = self.env.reset()
    for _ in range(n_steps):
        actions = []
        for i in range(n_agents):
            obs_agent = obs[i]
            action_agent = policy.compute_action(obs_agent, self.env.agents[i].u_range)
            actions.append(action_agent)
        obs, new_rews, dones, _ = self.env.step(actions)

@pytest.mark.parametrize('scenario', TEST_SCENARIOS)
@pytest.mark.parametrize('return_numpy', [True, False])
@pytest.mark.parametrize('continuous_actions', [True, False])
@pytest.mark.parametrize('dict_space', [True, False])
def test_gymnasium_wrapper(scenario, return_numpy, continuous_actions, dict_space, max_steps=10):
    env = make_env(scenario=scenario, num_envs=1, device='cpu', continuous_actions=continuous_actions, dict_spaces=dict_space, wrapper='gymnasium', terminated_truncated=True, wrapper_kwargs={'return_numpy': return_numpy}, max_steps=max_steps)
    assert len(env.observation_space) == env.unwrapped.n_agents, 'Expected one observation per agent'
    assert len(env.action_space) == env.unwrapped.n_agents, 'Expected one action per agent'
    if dict_space:
        assert isinstance(env.observation_space, gym.spaces.Dict), 'Expected Dict observation space'
        assert isinstance(env.action_space, gym.spaces.Dict), 'Expected Dict action space'
        obs_shapes = {k: obs_space.shape for k, obs_space in env.observation_space.spaces.items()}
    else:
        assert isinstance(env.observation_space, gym.spaces.Tuple), 'Expected Tuple observation space'
        assert isinstance(env.action_space, gym.spaces.Tuple), 'Expected Tuple action space'
        obs_shapes = [obs_space.shape for obs_space in env.observation_space.spaces]
    assert isinstance(env.unwrapped, Environment), 'The unwrapped attribute of the Gym wrapper should be a VMAS Environment'
    obss, info = env.reset()
    _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
    assert isinstance(info, dict), f'Expected info to be a dictionary but got {type(info)}'
    for _ in range(max_steps):
        actions = [env.unwrapped.get_random_action(agent).numpy() for agent in env.unwrapped.agents]
        obss, rews, terminated, truncated, info = env.step(actions)
        _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
        assert len(rews) == env.unwrapped.n_agents, 'Expected one reward per agent'
        if not dict_space:
            assert isinstance(rews, list), f'Expected list of rewards but got {type(rews)}'
            rew_values = rews
        else:
            assert isinstance(rews, dict), f'Expected dictionary of rewards but got {type(rews)}'
            rew_values = list(rews.values())
        assert all((isinstance(rew, float) for rew in rew_values)), f'Expected float rewards but got {type(rew_values[0])}'
        assert isinstance(terminated, bool), f'Expected bool for terminated but got {type(terminated)}'
        assert isinstance(truncated, bool), f'Expected bool for truncated but got {type(truncated)}'
        assert isinstance(info, dict), f'Expected info to be a dictionary but got {type(info)}'
    assert truncated, 'Expected done to be True after 100 steps'

@pytest.mark.parametrize('scenario', TEST_SCENARIOS)
@pytest.mark.parametrize('return_numpy', [True, False])
@pytest.mark.parametrize('continuous_actions', [True, False])
@pytest.mark.parametrize('dict_space', [True, False])
@pytest.mark.parametrize('num_envs', [1, 10])
def test_gymnasium_wrapper(scenario, return_numpy, continuous_actions, dict_space, num_envs, max_steps=10):
    env = make_env(scenario=scenario, num_envs=num_envs, device='cpu', continuous_actions=continuous_actions, dict_spaces=dict_space, wrapper='gymnasium_vec', terminated_truncated=True, wrapper_kwargs={'return_numpy': return_numpy}, max_steps=max_steps)
    assert isinstance(env.unwrapped, Environment), 'The unwrapped attribute of the Gym wrapper should be a VMAS Environment'
    assert len(env.observation_space) == env.unwrapped.n_agents, 'Expected one observation per agent'
    assert len(env.action_space) == env.unwrapped.n_agents, 'Expected one action per agent'
    if dict_space:
        assert isinstance(env.observation_space, gym.spaces.Dict), 'Expected Dict observation space'
        assert isinstance(env.action_space, gym.spaces.Dict), 'Expected Dict action space'
        obs_shapes = {k: obs_space.shape for k, obs_space in env.observation_space.spaces.items()}
    else:
        assert isinstance(env.observation_space, gym.spaces.Tuple), 'Expected Tuple observation space'
        assert isinstance(env.action_space, gym.spaces.Tuple), 'Expected Tuple action space'
        obs_shapes = [obs_space.shape for obs_space in env.observation_space.spaces]
    obss, info = env.reset()
    _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
    assert isinstance(info, dict), f'Expected info to be a dictionary but got {type(info)}'
    for _ in range(max_steps):
        actions = [env.unwrapped.get_random_action(agent).numpy() for agent in env.unwrapped.agents]
        obss, rews, terminated, truncated, info = env.step(actions)
        _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
        assert len(rews) == env.unwrapped.n_agents, 'Expected one reward per agent'
        if not dict_space:
            assert isinstance(rews, list), f'Expected list of rewards but got {type(rews)}'
            rew_values = rews
        else:
            assert isinstance(rews, dict), f'Expected dictionary of rewards but got {type(rews)}'
            rew_values = list(rews.values())
        if return_numpy:
            assert all((isinstance(rew, np.ndarray) for rew in rew_values)), f'Expected np.array rewards but got {type(rew_values[0])}'
        else:
            assert all((isinstance(rew, torch.Tensor) for rew in rew_values)), f'Expected torch tensor rewards but got {type(rew_values[0])}'
        if return_numpy:
            assert isinstance(terminated, np.ndarray), f'Expected np.array for terminated but got {type(terminated)}'
            assert isinstance(truncated, np.ndarray), f'Expected np.array for truncated but got {type(truncated)}'
        else:
            assert isinstance(terminated, torch.Tensor), f'Expected torch tensor for terminated but got {type(terminated)}'
            assert isinstance(truncated, torch.Tensor), f'Expected torch tensor for truncated but got {type(truncated)}'
        assert isinstance(info, dict), f'Expected info to be a dictionary but got {type(info)}'
    assert all(truncated), 'Expected done to be True after 100 steps'

@pytest.mark.parametrize('scenario', TEST_SCENARIOS)
@pytest.mark.parametrize('return_numpy', [True, False])
@pytest.mark.parametrize('continuous_actions', [True, False])
@pytest.mark.parametrize('dict_space', [True, False])
def test_gym_wrapper(scenario, return_numpy, continuous_actions, dict_space, max_steps=10):
    env = make_env(scenario=scenario, num_envs=1, device='cpu', continuous_actions=continuous_actions, dict_spaces=dict_space, wrapper='gym', wrapper_kwargs={'return_numpy': return_numpy}, max_steps=max_steps)
    assert len(env.observation_space) == env.unwrapped.n_agents, 'Expected one observation per agent'
    assert len(env.action_space) == env.unwrapped.n_agents, 'Expected one action per agent'
    if dict_space:
        assert isinstance(env.observation_space, gym.spaces.Dict), 'Expected Dict observation space'
        assert isinstance(env.action_space, gym.spaces.Dict), 'Expected Dict action space'
        obs_shapes = {k: obs_space.shape for k, obs_space in env.observation_space.spaces.items()}
    else:
        assert isinstance(env.observation_space, gym.spaces.Tuple), 'Expected Tuple observation space'
        assert isinstance(env.action_space, gym.spaces.Tuple), 'Expected Tuple action space'
        obs_shapes = [obs_space.shape for obs_space in env.observation_space.spaces]
    assert isinstance(env.unwrapped, Environment), 'The unwrapped attribute of the Gym wrapper should be a VMAS Environment'
    obss = env.reset()
    _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
    for _ in range(max_steps):
        actions = [env.unwrapped.get_random_action(agent).numpy() for agent in env.unwrapped.agents]
        obss, rews, done, info = env.step(actions)
        _check_obs_type(obss, obs_shapes, dict_space, return_numpy=return_numpy)
        assert len(rews) == env.unwrapped.n_agents, 'Expected one reward per agent'
        if not dict_space:
            assert isinstance(rews, list), f'Expected list of rewards but got {type(rews)}'
            rew_values = rews
        else:
            assert isinstance(rews, dict), f'Expected dictionary of rewards but got {type(rews)}'
            rew_values = list(rews.values())
        assert all((isinstance(rew, float) for rew in rew_values)), f'Expected float rewards but got {type(rew_values[0])}'
        assert isinstance(done, bool), f'Expected bool for done but got {type(done)}'
        assert isinstance(info, dict), f'Expected info to be a dictionary but got {type(info)}'
    assert done, 'Expected done to be True after 100 steps'

