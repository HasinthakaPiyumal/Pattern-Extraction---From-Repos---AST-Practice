# Cluster 32

def get_version():
    """Gets the vmas version."""
    path = CWD / 'vmas' / '__init__.py'
    content = path.read_text()
    for line in content.splitlines():
        if line.startswith('__version__'):
            return line.strip().split()[-1].strip().strip('"')
    raise RuntimeError('bad version data in __init__.py')

def get_device_name(torch_device: str):
    if torch_device == 'cpu':
        if platform.system() == 'Darwin':
            return 'Apple M1 Pro'
        elif platform.system() == 'Windows':
            return platform.processor()
        elif platform.system() == 'Linux':
            command = 'cat /proc/cpuinfo'
            all_info = subprocess.check_output(command, shell=True).decode().strip()
            for line in all_info.split('\n'):
                if 'model name' in line:
                    return re.sub('.*model name.*:', '', line, 1)
        else:
            raise AssertionError()
    elif torch_device == 'cuda':
        return torch.cuda.get_device_name()
    else:
        raise AssertionError()

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.fixed_passage = kwargs.pop('fixed_passage', False)
        self.joint_length = kwargs.pop('joint_length', 0.52)
        self.random_start_angle = kwargs.pop('random_start_angle', False)
        self.random_goal_angle = kwargs.pop('random_goal_angle', False)
        self.observe_joint_angle = kwargs.pop('observe_joint_angle', False)
        self.joint_angle_obs_noise = kwargs.pop('joint_angle_obs_noise', 0.0)
        self.asym_package = kwargs.pop('asym_package', False)
        self.mass_ratio = kwargs.pop('mass_ratio', 1)
        self.mass_position = kwargs.pop('mass_position', 0.75)
        self.max_speed_1 = kwargs.pop('max_speed_1', None)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1)
        self.rot_shaping_factor = kwargs.pop('rot_shaping_factor', 1)
        self.collision_reward = kwargs.pop('collision_reward', 0)
        self.energy_reward_coeff = kwargs.pop('energy_reward_coeff', 0)
        self.obs_noise = kwargs.pop('obs_noise', 0.0)
        self.n_passages = kwargs.pop('n_passages', 3)
        self.middle_angle_180 = kwargs.pop('middle_angle_180', False)
        self.use_vel_controller = kwargs.pop('use_vel_controller', False)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert self.n_passages == 3 or self.n_passages == 4
        self.plot_grid = False
        self.visualize_semidims = False
        world = World(batch_dim, device, x_semidim=1, y_semidim=1, substeps=5 if not self.asym_package else 10, joint_force=700 if self.asym_package else 400, collision_force=2500 if self.asym_package else 1500, drag=0.25 if not self.asym_package else 0.15)
        if not self.observe_joint_angle:
            assert self.joint_angle_obs_noise == 0
        self.n_agents = 2
        self.middle_angle = torch.zeros((world.batch_dim, 1), device=world.device)
        self.agent_radius = 0.03333
        self.agent_radius_2 = 3 * self.agent_radius
        self.mass_radius = self.agent_radius * (2 / 3)
        self.passage_width = 0.2
        self.passage_length = 0.1476
        self.scenario_length = 2 + 2 * self.agent_radius
        self.n_boxes = int(self.scenario_length // self.passage_length)
        self.min_collision_distance = 0.005
        cotnroller_params = [2.0, 10, 1e-05]
        agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), u_range=1, obs_noise=self.obs_noise, render_action=True, f_range=10)
        agent.controller = VelocityController(agent, world, cotnroller_params, 'standard')
        world.add_agent(agent)
        agent = Agent(name='agent_1', shape=Sphere(self.agent_radius_2), u_range=1, mass=1 if self.asym_package else self.mass_ratio, max_speed=self.max_speed_1, obs_noise=self.obs_noise, render_action=True, f_range=10)
        agent.controller = VelocityController(agent, world, cotnroller_params, 'standard')
        world.add_agent(agent)
        self.joint = Joint(world.agents[0], world.agents[1], anchor_a=(0, 0), anchor_b=(0, 0), dist=self.joint_length, rotate_a=True, rotate_b=True, collidable=False, width=0, mass=1)
        world.add_joint(self.joint)
        if self.asym_package:

            def mass_collision_filter(e):
                return not isinstance(e.shape, Sphere)
            self.mass = Landmark(name='mass', shape=Sphere(radius=self.mass_radius), collide=True, movable=True, color=Color.BLACK, mass=self.mass_ratio, collision_filter=mass_collision_filter)
            world.add_landmark(self.mass)
            joint = Joint(self.mass, self.joint.landmark, anchor_a=(0, 0), anchor_b=(self.mass_position, 0), dist=0, rotate_a=True, rotate_b=True)
            world.add_joint(joint)
        self.goal = Landmark(name='joint_goal', shape=Line(length=self.joint_length), collide=False, color=Color.GREEN)
        world.add_landmark(self.goal)
        self.walls = []
        for i in range(4):
            wall = Landmark(name=f'wall {i}', collide=True, shape=Line(length=2 + self.agent_radius * 2), color=Color.BLACK)
            world.add_landmark(wall)
            self.walls.append(wall)
        self.create_passage_map(world)
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.rot_rew = self.pos_rew.clone()
        self.collision_rew = self.pos_rew.clone()
        self.energy_rew = self.pos_rew.clone()
        self.all_passed = torch.full((batch_dim,), False, device=device)
        return world

    def set_n_passages(self, val):
        if val == 4:
            self.middle_angle_180 = True
        elif val == 3:
            self.middle_angle_180 = False
        else:
            raise AssertionError()
        self.n_passages = val
        del self.world._landmarks[-self.n_boxes:]
        self.create_passage_map(self.world)
        self.reset_world_at()

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device)
        start_angle[start_angle >= 0.5] = torch.pi / 2
        start_angle[start_angle < 0.5] = -torch.pi / 2
        goal_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_goal_angle else torch.pi, torch.pi / 2 if self.random_goal_angle else torch.pi)
        bigger_radius = max(self.agent_radius, self.agent_radius_2)
        start_delta_x = self.joint_length / 2 * torch.cos(start_angle)
        start_delta_x_abs = start_delta_x.abs()
        min_x_start = -self.world.x_semidim + (bigger_radius + start_delta_x_abs)
        max_x_start = self.world.x_semidim - (bigger_radius + start_delta_x_abs)
        start_delta_y = self.joint_length / 2 * torch.sin(start_angle)
        start_delta_y_abs = start_delta_y.abs()
        min_y_start = -self.world.y_semidim + (bigger_radius + start_delta_y_abs)
        max_y_start = -2 * bigger_radius - self.passage_width / 2 - start_delta_y_abs
        goal_delta_x = self.joint_length / 2 * torch.cos(goal_angle)
        goal_delta_x_abs = goal_delta_x.abs()
        min_x_goal = -self.world.x_semidim + (bigger_radius + goal_delta_x_abs)
        max_x_goal = self.world.x_semidim - (bigger_radius + goal_delta_x_abs)
        goal_delta_y = self.joint_length / 2 * torch.sin(goal_angle)
        goal_delta_y_abs = goal_delta_y.abs()
        min_y_goal = 2 * bigger_radius + self.passage_width / 2 + goal_delta_y_abs
        max_y_goal = self.world.y_semidim - (bigger_radius + goal_delta_y_abs)
        joint_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
        goal_pos = torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1)
        self.goal.set_pos(goal_pos, batch_index=env_index)
        self.goal.set_rot(goal_angle, batch_index=env_index)
        agents = self.world.agents
        for i, agent in enumerate(agents):
            agent.controller.reset(env_index)
            if i == 0:
                agent.set_pos(joint_pos - torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
            else:
                agent.set_pos(joint_pos + torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        if self.asym_package:
            self.mass.set_pos(joint_pos + self.mass_position * torch.cat([start_delta_x, start_delta_y], dim=1) * (1 if agents[0] == self.world.agents[0] else -1), batch_index=env_index)
        self.spawn_passage_map(env_index)
        self.spawn_walls(env_index)
        if env_index is None:
            self.t = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.passed = torch.zeros((self.world.batch_dim,), device=self.world.device)
            self.joint.pos_shaping_pre = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.pass_center, dim=1) * self.pos_shaping_factor
            self.joint.pos_shaping_post = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
            self.joint.rot_shaping_pre = (get_line_angle_dist_0_360(self.joint.landmark.state.rot, self.middle_angle) if not self.middle_angle_180 else get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.middle_angle)) * self.rot_shaping_factor
        else:
            self.t[env_index] = 0
            self.passed[env_index] = 0
            self.joint.pos_shaping_pre[env_index] = torch.linalg.vector_norm(self.joint.landmark.state.pos[env_index] - self.pass_center[env_index]) * self.pos_shaping_factor
            self.joint.pos_shaping_post[env_index] = torch.linalg.vector_norm(self.joint.landmark.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor
            self.joint.rot_shaping_pre[env_index] = (get_line_angle_dist_0_360(self.joint.landmark.state.rot[env_index].unsqueeze(-1), self.middle_angle[env_index].unsqueeze(-1)) if not self.middle_angle_180 else get_line_angle_dist_0_180(self.joint.landmark.state.rot[env_index].unsqueeze(-1), self.middle_angle[env_index].unsqueeze(-1))) * self.rot_shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.t += 1
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.pos_rew[:] = 0
            self.rot_rew[:] = 0
            self.collision_rew[:] = 0
            self.energy_rew[:] = 0
            joint_passed = self.joint.landmark.state.pos[:, Y] > 0
            self.all_passed = (torch.stack([a.state.pos[:, Y] for a in self.world.agents], dim=1) > self.passage_width / 2).all(dim=1)
            joint_dist_to_closest_pass = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.pass_center, dim=1) * self.pos_shaping_factor
            joint_shaping = joint_dist_to_closest_pass * self.pos_shaping_factor
            self.pos_rew[~joint_passed] += (self.joint.pos_shaping_pre - joint_shaping)[~joint_passed]
            self.joint.pos_shaping_pre = joint_shaping
            joint_dist_to_goal = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1)
            joint_shaping = joint_dist_to_goal * self.pos_shaping_factor
            self.pos_rew[joint_passed] += (self.joint.pos_shaping_post - joint_shaping)[joint_passed]
            self.joint.pos_shaping_post = joint_shaping
            joint_dist_to_90_rot = get_line_angle_dist_0_360(self.joint.landmark.state.rot, self.middle_angle) if not self.middle_angle_180 else get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.middle_angle)
            joint_shaping = joint_dist_to_90_rot * self.rot_shaping_factor
            self.rot_rew += self.joint.rot_shaping_pre - joint_shaping
            self.joint.rot_shaping_pre = joint_shaping
            if self.collision_reward != 0:
                for a in self.world.agents + ([self.mass] if self.asym_package else []):
                    for passage in self.passages:
                        if passage.collide:
                            self.collision_rew[self.world.get_distance(a, passage) <= self.min_collision_distance] += self.collision_reward
                    for wall in self.walls:
                        self.collision_rew[self.world.get_distance(a, wall) <= self.min_collision_distance] += self.collision_reward
            if self.energy_reward_coeff != 0:
                self.energy_expenditure = torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * (a.u_range * a.u_multiplier) ** 2) for a in self.world.agents], dim=1).sum(-1)
                self.energy_rew = -self.energy_expenditure * self.energy_reward_coeff
            self.rew = self.pos_rew + self.rot_rew + self.collision_rew + self.energy_rew
        return self.rew

    def process_action(self, agent: Agent):
        if self.use_vel_controller:
            vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
            agent.controller.reset(vel_is_zero)
            agent.controller.process_force()

    def is_out_or_touching_perimeter(self, agent: Agent):
        is_out_or_touching_perimeter = torch.full((self.world.batch_dim,), False, device=self.world.device)
        is_out_or_touching_perimeter += agent.state.pos[:, X] >= self.world.x_semidim
        is_out_or_touching_perimeter += agent.state.pos[:, X] <= -self.world.x_semidim
        is_out_or_touching_perimeter += agent.state.pos[:, Y] >= self.world.y_semidim
        is_out_or_touching_perimeter += agent.state.pos[:, Y] <= -self.world.y_semidim
        return is_out_or_touching_perimeter

    def observation(self, agent: Agent):
        if self.observe_joint_angle:
            joint_angle = self.joint.landmark.state.rot
            angle_noise = torch.randn(*joint_angle.shape, device=self.world.device, dtype=torch.float32) * self.joint_angle_obs_noise if self.joint_angle_obs_noise else 0.0
            joint_angle += angle_noise
        observations = [agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos, agent.state.pos - self.big_passage_pos, agent.state.pos - self.small_passage_pos, angle_to_vector(self.goal.state.rot)] + ([angle_to_vector(joint_angle)] if self.observe_joint_angle else [])
        if self.obs_noise > 0:
            for i, obs in enumerate(observations):
                noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
                observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def done(self):
        return torch.all((torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) <= 0.01) * (get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot).unsqueeze(-1) <= 0.01), dim=1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        is_first = self.world.agents[0] == agent
        if is_first:
            just_passed = self.all_passed * (self.passed == 0)
            self.passed[just_passed] = 100
            self.info_stored = {'pos_rew': self.pos_rew, 'rot_rew': self.rot_rew, 'collision_rew': self.collision_rew, 'energy_rew': self.energy_rew, 'passed': just_passed.to(torch.int)}
        return self.info_stored

    def create_passage_map(self, world: World):
        self.passages = []
        self.collide_passages = []
        self.non_collide_passages = []

        def is_passage(i):
            return i < self.n_passages
        for i in range(self.n_boxes):
            passage = Landmark(name=f'passage {i}', collide=not is_passage(i), movable=False, shape=Box(length=self.passage_length, width=self.passage_width), color=Color.RED, collision_filter=lambda e: not isinstance(e.shape, Box))
            if not passage.collide:
                self.non_collide_passages.append(passage)
            else:
                self.collide_passages.append(passage)
            self.passages.append(passage)
            world.add_landmark(passage)

    def spawn_passage_map(self, env_index):
        if self.fixed_passage:
            big_passage_start_index = torch.full((self.world.batch_dim,) if env_index is None else (1,), 5, device=self.world.device)
            small_left_or_right = torch.full((self.world.batch_dim,) if env_index is None else (1,), 1, device=self.world.device)
        else:
            big_passage_start_index = torch.randint(0, self.n_boxes - 1, (self.world.batch_dim,) if env_index is None else (1,), device=self.world.device)
            small_left_or_right = torch.randint(0, 2, (self.world.batch_dim,) if env_index is None else (1,), device=self.world.device)
        small_left_or_right[big_passage_start_index > self.n_boxes - 1 - (self.n_passages + 1)] = 0
        small_left_or_right[big_passage_start_index < self.n_passages] = 1
        small_left_or_right[small_left_or_right == 0] -= 3
        small_left_or_right[small_left_or_right == 1] += 3

        def is_passage(i):
            is_pass = big_passage_start_index == i
            is_pass += big_passage_start_index == i - 1
            is_pass += big_passage_start_index + small_left_or_right == i
            if self.n_passages == 4:
                is_pass += big_passage_start_index + small_left_or_right == i - torch.sign(small_left_or_right)
            return is_pass

        def get_pos(i):
            pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2, 0.0], dtype=torch.float32, device=self.world.device).repeat(i.shape[0], 1)
            pos[:, X] += self.passage_length * i
            return pos
        for index, i in enumerate([big_passage_start_index, big_passage_start_index + 1, big_passage_start_index + small_left_or_right] + ([big_passage_start_index + small_left_or_right + torch.sign(small_left_or_right)] if self.n_passages == 4 else [])):
            self.non_collide_passages[index].is_rendering[:] = False
            self.non_collide_passages[index].set_pos(get_pos(i), batch_index=env_index)
        big_passage_pos = (get_pos(big_passage_start_index) + get_pos(big_passage_start_index + 1)) / 2
        small_passage_pos = get_pos(big_passage_start_index + small_left_or_right)
        pass_center = (big_passage_pos + small_passage_pos) / 2
        if env_index is None:
            self.small_left_or_right = small_left_or_right
            self.pass_center = pass_center
            self.big_passage_pos = big_passage_pos
            self.small_passage_pos = small_passage_pos
            self.middle_angle[small_left_or_right > 0] = torch.pi
            self.middle_angle[small_left_or_right < 0] = 0
        else:
            self.pass_center[env_index] = pass_center
            self.small_left_or_right[env_index] = small_left_or_right
            self.big_passage_pos[env_index] = big_passage_pos
            self.small_passage_pos[env_index] = small_passage_pos
            self.middle_angle[env_index] = 0 if small_left_or_right.item() < 0 else torch.pi
        i = torch.zeros((self.world.batch_dim,) if env_index is None else (1,), dtype=torch.int, device=self.world.device)
        for passage in self.collide_passages:
            is_pass = is_passage(i)
            while is_pass.any():
                i[is_pass] += 1
                is_pass = is_passage(i)
            passage.set_pos(get_pos(i), batch_index=env_index)
            i += 1

    def spawn_walls(self, env_index):
        for i, wall in enumerate(self.walls):
            wall.set_pos(torch.tensor([0.0 if i % 2 else self.world.x_semidim + self.agent_radius if i == 0 else -self.world.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.world.y_semidim + self.agent_radius if i == 1 else -self.world.y_semidim - self.agent_radius], device=self.world.device), batch_index=env_index)
            wall.set_rot(torch.tensor([torch.pi / 2 if not i % 2 else 0.0], device=self.world.device), batch_index=env_index)

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        color = self.goal.color
        if isinstance(color, torch.Tensor) and len(color.shape) > 1:
            color = color[env_index]
        goal_agent_1 = rendering.make_circle(self.agent_radius)
        xform = rendering.Transform()
        goal_agent_1.add_attr(xform)
        xform.set_translation(self.goal.state.pos[env_index][X] - self.joint_length / 2 * math.cos(self.goal.state.rot[env_index]), self.goal.state.pos[env_index][Y] - self.joint_length / 2 * math.sin(self.goal.state.rot[env_index]))
        goal_agent_1.set_color(*color)
        geoms.append(goal_agent_1)
        goal_agent_2 = rendering.make_circle(self.agent_radius)
        xform = rendering.Transform()
        goal_agent_2.add_attr(xform)
        xform.set_translation(self.goal.state.pos[env_index][X] + self.joint_length / 2 * math.cos(self.goal.state.rot[env_index]), self.goal.state.pos[env_index][Y] + self.joint_length / 2 * math.sin(self.goal.state.rot[env_index]))
        goal_agent_2.set_color(*color)
        geoms.append(goal_agent_2)
        return geoms

def set_n_passages(self, val):
    if val == 4:
        self.middle_angle_180 = True
    elif val == 3:
        self.middle_angle_180 = False
    else:
        raise AssertionError()
    self.n_passages = val
    del self.world._landmarks[-self.n_boxes:]
    self.create_passage_map(self.world)
    self.reset_world_at()

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

def done(self):
    if self.ai_blue_agents and self.ai_red_agents:
        self.reward(None)
    return self._done

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

def env_reset_world_at(self, env_index: typing.Optional[int]):
    self.world.reset(env_index)
    self.reset_world_at(env_index)

def _init_pyglet_device():
    available_devices = os.getenv('CUDA_VISIBLE_DEVICES')
    if available_devices is not None and len(available_devices) > 0:
        os.environ['PYGLET_HEADLESS_DEVICE'] = available_devices.split(',')[0] if len(available_devices) > 1 else available_devices

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

def add_joint(self, joint: Joint):
    assert self._substeps > 1, 'For joints, world substeps needs to be more than 1'
    if joint.landmark is not None:
        self.add_landmark(joint.landmark)
    for constraint in joint.joint_constraints:
        self._joints.update({frozenset({constraint.entity_a.name, constraint.entity_b.name}): constraint})

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

