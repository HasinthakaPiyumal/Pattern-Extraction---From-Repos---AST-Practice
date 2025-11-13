# Cluster 26

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

def info(self, agent: Agent) -> Dict[str, Tensor]:
    is_first = self.world.agents[0] == agent
    if is_first:
        just_passed = self.all_passed * (self.passed == 0)
        self.passed[just_passed] = 100
        self.info_stored = {'pos_rew': self.pos_rew, 'rot_rew': self.rot_rew, 'collision_rew': self.collision_rew, 'energy_rew': self.energy_rew, 'passed': just_passed.to(torch.int)}
    return self.info_stored

class StateBuffer(CircularBuffer):

    def __init__(self, buffer: torch.Tensor=None):
        """Initializes a circular buffer to store initial states."""
        super().__init__(buffer=buffer)
        self.idx_scenario = 5
        self.idx_path = 6
        self.idx_point = 7

def __init__(self, buffer: torch.Tensor=None):
    """Initializes a circular buffer to store initial states."""
    super().__init__(buffer=buffer)
    self.idx_scenario = 5
    self.idx_path = 6
    self.idx_point = 7

class InitialStateBuffer(CircularBuffer):

    def __init__(self, buffer: torch.Tensor=None, probability_record: torch.Tensor=None, probability_use_recording: torch.Tensor=None):
        """Initializes a circular buffer to store initial states."""
        super().__init__(buffer=buffer)
        self.probability_record = probability_record
        self.probability_use_recording = probability_use_recording
        self.idx_scenario = 5
        self.idx_path = 6
        self.idx_point = 7

    def get_random(self):
        """Returns a randomly selected recording from the buffer.

        Return:
            A randomly selected recording tensor. If the buffer is empty, returns None.
        """
        if self.valid_size == 0:
            return None
        else:
            random_index = torch.randint(0, self.valid_size, ())
            return self.buffer[random_index]

def __init__(self, buffer: torch.Tensor=None, probability_record: torch.Tensor=None, probability_use_recording: torch.Tensor=None):
    """Initializes a circular buffer to store initial states."""
    super().__init__(buffer=buffer)
    self.probability_record = probability_record
    self.probability_use_recording = probability_use_recording
    self.idx_scenario = 5
    self.idx_path = 6
    self.idx_point = 7

def get_map_data(map_file_path, device=None):
    """This function returns the map data."""
    if device is None:
        device = torch.device('cpu')
    tree = ET.parse(map_file_path)
    root = tree.getroot()
    lanelets = []
    intersection_info = []
    for child in root:
        if child.tag == 'lanelet':
            lanelets.append(parse_lanelet(child, device))
        elif child.tag == 'intersection':
            intersection_info = parse_intersections(child)
    mean_lane_width = torch.mean(torch.norm(torch.vstack([lanelets[i]['left_boundary'] for i in range(len(lanelets))]) - torch.vstack([lanelets[i]['right_boundary'] for i in range(len(lanelets))]), dim=1))
    map_data = {'lanelets': lanelets, 'intersection_info': intersection_info, 'mean_lane_width': mean_lane_width}
    return map_data

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.v_range = kwargs.pop('v_range', 0.5)
        self.a_range = kwargs.pop('a_range', 1)
        self.obs_noise = kwargs.pop('obs_noise', 0)
        self.box_agents = kwargs.pop('box_agents', False)
        self.linear_friction = kwargs.pop('linear_friction', 0.1)
        self.mirror_passage = kwargs.pop('mirror_passage', False)
        self.done_on_completion = kwargs.pop('done_on_completion', False)
        self.observe_rel_pos = kwargs.pop('observe_rel_pos', False)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1.0)
        self.final_reward = kwargs.pop('final_reward', 0.01)
        self.energy_reward_coeff = kwargs.pop('energy_rew_coeff', 0)
        self.agent_collision_penalty = kwargs.pop('agent_collision_penalty', 0)
        self.passage_collision_penalty = kwargs.pop('passage_collision_penalty', 0)
        self.obstacle_collision_penalty = kwargs.pop('obstacle_collision_penalty', 0)
        self.use_velocity_controller = kwargs.pop('use_velocity_controller', True)
        self.min_input_norm = kwargs.pop('min_input_norm', 0.08)
        self.dt_delay = kwargs.pop('dt_delay', 0)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.viewer_size = (1600, 700)
        controller_params = [2, 6, 0.002]
        self.f_range = self.a_range + self.linear_friction
        self.u_range = self.v_range if self.use_velocity_controller else self.f_range
        world = World(batch_dim, device, drag=0, dt=0.05, linear_friction=self.linear_friction, substeps=16 if self.box_agents else 5, collision_force=10000 if self.box_agents else 500)
        self.agent_radius = 0.16
        self.agent_box_length = 0.32
        self.agent_box_width = 0.24
        self.spawn_pos_noise = 0.02
        self.min_collision_distance = 0.005
        blue_agent = Agent(name='agent_0', rotatable=False, linear_friction=self.linear_friction, shape=Sphere(radius=self.agent_radius) if not self.box_agents else Box(length=self.agent_box_length, width=self.agent_box_width), u_range=self.u_range, f_range=self.f_range, v_range=self.v_range, render_action=True)
        if self.use_velocity_controller:
            blue_agent.controller = VelocityController(blue_agent, world, controller_params, 'standard')
        blue_goal = Landmark(name='goal_0', collide=False, shape=Sphere(radius=self.agent_radius / 2), color=Color.BLUE)
        blue_agent.goal = blue_goal
        world.add_agent(blue_agent)
        world.add_landmark(blue_goal)
        green_agent = Agent(name='agent_1', color=Color.GREEN, linear_friction=self.linear_friction, shape=Sphere(radius=self.agent_radius) if not self.box_agents else Box(length=self.agent_box_length, width=self.agent_box_width), rotatable=False, u_range=self.u_range, f_range=self.f_range, v_range=self.v_range, render_action=True)
        if self.use_velocity_controller:
            green_agent.controller = VelocityController(green_agent, world, controller_params, 'standard')
        green_goal = Landmark(name='goal_1', collide=False, shape=Sphere(radius=self.agent_radius / 2), color=Color.GREEN)
        green_agent.goal = green_goal
        world.add_agent(green_agent)
        world.add_landmark(green_goal)
        null_action = torch.zeros(world.batch_dim, world.dim_p, device=world.device)
        blue_agent.input_queue = [null_action.clone() for _ in range(self.dt_delay)]
        green_agent.input_queue = [null_action.clone() for _ in range(self.dt_delay)]
        self.spawn_map(world)
        for agent in world.agents:
            agent.energy_rew = torch.zeros(batch_dim, device=device)
            agent.agent_collision_rew = agent.energy_rew.clone()
            agent.obstacle_collision_rew = agent.agent_collision_rew.clone()
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.final_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        self.world.agents[0].set_pos(torch.tensor([-(self.scenario_length / 2 - self.agent_dist_from_wall), 0.0], dtype=torch.float32, device=self.world.device) + torch.zeros(self.world.dim_p, device=self.world.device).uniform_(-self.spawn_pos_noise, self.spawn_pos_noise), batch_index=env_index)
        if self.use_velocity_controller:
            self.world.agents[0].controller.reset(env_index)
        self.world.landmarks[0].set_pos(torch.tensor([self.scenario_length / 2 - self.goal_dist_from_wall, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        self.world.agents[1].set_pos(torch.tensor([self.scenario_length / 2 - self.agent_dist_from_wall, 0.0], dtype=torch.float32, device=self.world.device) + torch.zeros(self.world.dim_p, device=self.world.device).uniform_(-self.spawn_pos_noise, self.spawn_pos_noise), batch_index=env_index)
        if self.use_velocity_controller:
            self.world.agents[1].controller.reset(env_index)
        self.world.landmarks[1].set_pos(torch.tensor([-(self.scenario_length / 2 - self.goal_dist_from_wall), 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        self.reset_map(env_index)
        for agent in self.world.agents:
            if env_index is None:
                agent.shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.pos_shaping_factor
            else:
                agent.shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.pos_shaping_factor
        if env_index is None:
            self.goal_reached = torch.full((self.world.batch_dim,), False, device=self.world.device)
        else:
            self.goal_reached[env_index] = False

    def process_action(self, agent: Agent):
        if self.use_velocity_controller:
            agent.input_queue.append(agent.action.u.clone())
            agent.action.u = agent.input_queue.pop(0)
            agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, self.u_range)
            action_norm = torch.linalg.vector_norm(agent.action.u, dim=1)
            agent.action.u[action_norm < self.min_input_norm] = 0
            agent.vel_action = agent.action.u.clone()
            vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
            agent.controller.reset(vel_is_zero)
            agent.controller.process_force()

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        blue_agent = self.world.agents[0]
        green_agent = self.world.agents[-1]
        if is_first:
            self.pos_rew[:] = 0
            self.final_rew[:] = 0
            self.blue_distance = torch.linalg.vector_norm(blue_agent.state.pos - blue_agent.goal.state.pos, dim=1)
            self.green_distance = torch.linalg.vector_norm(green_agent.state.pos - green_agent.goal.state.pos, dim=1)
            self.blue_on_goal = self.blue_distance < blue_agent.goal.shape.radius
            self.green_on_goal = self.green_distance < green_agent.goal.shape.radius
            self.goal_reached = self.green_on_goal * self.blue_on_goal
            green_shaping = self.green_distance * self.pos_shaping_factor
            self.green_rew = green_agent.shaping - green_shaping
            green_agent.shaping = green_shaping
            blue_shaping = self.blue_distance * self.pos_shaping_factor
            self.blue_rew = blue_agent.shaping - blue_shaping
            blue_agent.shaping = blue_shaping
            self.pos_rew += self.blue_rew
            self.pos_rew += self.green_rew
            self.final_rew[self.goal_reached] = self.final_reward
        agent.agent_collision_rew[:] = 0
        agent.obstacle_collision_rew[:] = 0
        for a in self.world.agents:
            if a != agent:
                agent.agent_collision_rew[self.world.get_distance(agent, a) <= self.min_collision_distance] += self.agent_collision_penalty
        for landmark in self.world.landmarks:
            if self.world.collides(agent, landmark):
                if landmark in ([*self.passage_1, *self.passage_2] if self.mirror_passage is True else [*self.passage_1]):
                    penalty = self.passage_collision_penalty
                else:
                    penalty = self.obstacle_collision_penalty
                agent.obstacle_collision_rew[self.world.get_distance(agent, landmark) <= self.min_collision_distance] += penalty
        agent.energy_expenditure = torch.linalg.vector_norm(agent.action.u, dim=-1) / math.sqrt(self.world.dim_p * agent.f_range ** 2)
        agent.energy_rew = -agent.energy_expenditure * self.energy_reward_coeff
        return self.pos_rew + agent.obstacle_collision_rew + agent.agent_collision_rew + agent.energy_rew + self.final_rew

    def observation(self, agent: Agent):
        rel = []
        for a in self.world.agents:
            if a != agent:
                rel.append(agent.state.pos - a.state.pos)
        observations = [agent.state.pos, agent.state.vel]
        if self.observe_rel_pos:
            observations += rel
        if self.obs_noise > 0:
            for i, obs in enumerate(observations):
                noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
                observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def info(self, agent: Agent):
        return {'pos_rew': self.pos_rew, 'final_rew': self.final_rew, 'energy_rew': agent.energy_rew, 'agent_collision_rew': agent.agent_collision_rew, 'obstacle_collision_rew': agent.obstacle_collision_rew}

    def spawn_map(self, world: World):
        self.scenario_length = 5
        self.passage_length = 0.4
        self.passage_width = 0.48
        self.corridor_width = self.passage_length
        self.small_ceiling_length = self.scenario_length / 2 - self.passage_length / 2
        self.goal_dist_from_wall = self.agent_radius + 0.05
        self.agent_dist_from_wall = 0.5
        self.walls = []
        for i in range(2):
            landmark = Landmark(name=f'wall {i}', collide=True, shape=Line(length=self.corridor_width), color=Color.BLACK)
            self.walls.append(landmark)
            world.add_landmark(landmark)
        self.small_ceilings_1 = []
        for i in range(2):
            landmark = Landmark(name=f'ceil 1 {i}', collide=True, shape=Line(length=self.small_ceiling_length), color=Color.BLACK)
            self.small_ceilings_1.append(landmark)
            world.add_landmark(landmark)
        self.passage_1 = []
        for i in range(3):
            landmark = Landmark(name=f'ceil 2 {i}', collide=True, shape=Line(length=self.passage_length if i == 2 else self.passage_width), color=Color.BLACK)
            self.passage_1.append(landmark)
            world.add_landmark(landmark)
        if self.mirror_passage:
            self.small_ceilings_2 = []
            for i in range(2):
                landmark = Landmark(name=f'ceil 12 {i}', collide=True, shape=Line(length=self.small_ceiling_length), color=Color.BLACK)
                self.small_ceilings_2.append(landmark)
                world.add_landmark(landmark)
            self.passage_2 = []
            for i in range(3):
                landmark = Landmark(name=f'ceil 22 {i}', collide=True, shape=Line(length=self.passage_length if i == 2 else self.passage_width), color=Color.BLACK)
                self.passage_2.append(landmark)
                world.add_landmark(landmark)
        else:
            landmark = Landmark(name='floor', collide=True, shape=Line(length=self.scenario_length), color=Color.BLACK)
            self.floor = landmark
            world.add_landmark(landmark)

    def reset_map(self, env_index):
        for i, landmark in enumerate(self.walls):
            landmark.set_pos(torch.tensor([-self.scenario_length / 2 if i == 0 else self.scenario_length / 2, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        small_ceiling_pos = self.small_ceiling_length / 2 - self.scenario_length / 2
        for i, landmark in enumerate(self.small_ceilings_1):
            landmark.set_pos(torch.tensor([-small_ceiling_pos if i == 0 else small_ceiling_pos, self.passage_length / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        for i, landmark in enumerate(self.passage_1[:-1]):
            landmark.set_pos(torch.tensor([-self.passage_length / 2 if i == 0 else self.passage_length / 2, self.passage_length / 2 + self.passage_width / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        self.passage_1[-1].set_pos(torch.tensor([0, self.passage_length / 2 + self.passage_width], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        if self.mirror_passage:
            for i, landmark in enumerate(self.small_ceilings_2):
                landmark.set_pos(torch.tensor([-small_ceiling_pos if i == 0 else small_ceiling_pos, -self.passage_length / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            for i, landmark in enumerate(self.passage_2[:-1]):
                landmark.set_pos(torch.tensor([-self.passage_length / 2 if i == 0 else self.passage_length / 2, -self.passage_length / 2 - self.passage_width / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            self.passage_2[-1].set_pos(torch.tensor([0, -self.passage_length / 2 - self.passage_width], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        else:
            self.floor.set_pos(torch.tensor([0, -self.passage_length / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)

    def done(self):
        if self.done_on_completion:
            return self.goal_reached
        else:
            return torch.zeros_like(self.goal_reached)

def done(self):
    if self.done_on_completion:
        return self.goal_reached
    else:
        return torch.zeros_like(self.goal_reached)

class HeuristicPolicy(BaseHeuristicPolicy):

    def __init__(self, clf_epsilon=0.2, clf_slack=100.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clf_epsilon = clf_epsilon
        self.clf_slack = clf_slack

    def compute_action(self, observation: Tensor, u_range: Tensor) -> Tensor:
        """
        QP inputs:
        These values need to computed apriri based on observation before passing into QP

        V: Lyapunov function value
        lfV: Lie derivative of Lyapunov function
        lgV: Lie derivative of Lyapunov function
        CLF_slack: CLF constraint slack variable

        QP outputs:
        u: action
        CLF_slack: CLF constraint slack variable, 0 if CLF constraint is satisfied
        """
        import cvxpy as cp
        from cvxpylayers.torch import CvxpyLayer
        self.n_env = observation.shape[0]
        self.device = observation.device
        agent_pos = observation[:, :2]
        agent_vel = observation[:, 2:4]
        goal_pos = -1.0 * (observation[:, 4:6] - agent_pos)
        V_value = (agent_pos[:, X] - goal_pos[:, X]) ** 2 + 0.5 * (agent_pos[:, X] - goal_pos[:, X]) * agent_vel[:, X] + agent_vel[:, X] ** 2 + (agent_pos[:, Y] - goal_pos[:, Y]) ** 2 + 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) * agent_vel[:, Y] + agent_vel[:, Y] ** 2
        LfV_val = (2 * (agent_pos[:, X] - goal_pos[:, X]) + agent_vel[:, X]) * agent_vel[:, X] + (2 * (agent_pos[:, Y] - goal_pos[:, Y]) + agent_vel[:, Y]) * agent_vel[:, Y]
        LgV_vals = torch.stack([0.5 * (agent_pos[:, X] - goal_pos[:, X]) + 2 * agent_vel[:, X], 0.5 * (agent_pos[:, Y] - goal_pos[:, Y]) + 2 * agent_vel[:, Y]], dim=1)
        u = cp.Variable(2)
        V_param = cp.Parameter(1)
        lfV_param = cp.Parameter(1)
        lgV_params = cp.Parameter(2)
        clf_slack = cp.Variable(1)
        constraints = []
        qp_objective = cp.Minimize(cp.sum_squares(u) + self.clf_slack * clf_slack ** 2)
        constraints += [u <= u_range]
        constraints += [u >= -u_range]
        constraints += [lfV_param + lgV_params @ u + self.clf_epsilon * V_param + clf_slack <= 0]
        QP_problem = cp.Problem(qp_objective, constraints)
        QP_controller = CvxpyLayer(QP_problem, parameters=[V_param, lfV_param, lgV_params], variables=[u])
        CVXpylayer_parameters = [V_value.unsqueeze(1), LfV_val.unsqueeze(1), LgV_vals]
        action = QP_controller(*CVXpylayer_parameters, solver_args={'max_iters': 500})[0]
        return action

def __init__(self, clf_epsilon=0.2, clf_slack=100.0, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.clf_epsilon = clf_epsilon
    self.clf_slack = clf_slack

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_passages = kwargs.pop('n_passages', 1)
        self.fixed_passage = kwargs.pop('fixed_passage', True)
        self.joint_length = kwargs.pop('joint_length', 0.5)
        self.random_start_angle = kwargs.pop('random_start_angle', True)
        self.random_goal_angle = kwargs.pop('random_goal_angle', True)
        self.observe_joint_angle = kwargs.pop('observe_joint_angle', False)
        self.joint_angle_obs_noise = kwargs.pop('joint_angle_obs_noise', 0.0)
        self.asym_package = kwargs.pop('asym_package', True)
        self.mass_ratio = kwargs.pop('mass_ratio', 5)
        self.mass_position = kwargs.pop('mass_position', 0.75)
        self.max_speed_1 = kwargs.pop('max_speed_1', None)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1)
        self.rot_shaping_factor = kwargs.pop('rot_shaping_factor', 1)
        self.collision_reward = kwargs.pop('collision_reward', 0)
        self.energy_reward_coeff = kwargs.pop('energy_reward_coeff', 0)
        self.all_passed_rot = kwargs.pop('all_passed_rot', True)
        self.obs_noise = kwargs.pop('obs_noise', 0.0)
        self.use_controller = kwargs.pop('use_controller', False)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.plot_grid = True
        self.visualize_semidims = False
        world = World(batch_dim, device, x_semidim=1, y_semidim=1, substeps=7 if not self.asym_package else 10, joint_force=900 if self.asym_package else 400, collision_force=2500 if self.asym_package else 1500, drag=0.25 if not self.asym_package else 0.15)
        if not self.observe_joint_angle:
            assert self.joint_angle_obs_noise == 0
        self.middle_angle = torch.pi / 2
        self.n_agents = 2
        self.agent_radius = 0.03333
        self.mass_radius = self.agent_radius * (2 / 3)
        self.passage_width = 0.2
        self.passage_length = 0.1476
        self.scenario_length = 2 * world.x_semidim + 2 * self.agent_radius
        self.n_boxes = int(self.scenario_length // self.passage_length)
        self.min_collision_distance = 0.005
        assert 1 <= self.n_passages <= int(self.scenario_length // self.passage_length)
        cotnroller_params = [2.0, 10, 1e-05]
        agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), obs_noise=self.obs_noise, render_action=True, u_multiplier=0.8, f_range=0.8)
        agent.controller = VelocityController(agent, world, cotnroller_params, 'standard')
        world.add_agent(agent)
        agent = Agent(name='agent_1', shape=Sphere(self.agent_radius), mass=1 if self.asym_package else self.mass_ratio, color=Color.BLUE, max_speed=self.max_speed_1, obs_noise=self.obs_noise, render_action=True, u_multiplier=0.8, f_range=0.8)
        agent.controller = VelocityController(agent, world, cotnroller_params, 'standard')
        world.add_agent(agent)
        self.joint = Joint(world.agents[0], world.agents[1], anchor_a=(0, 0), anchor_b=(0, 0), dist=self.joint_length, rotate_a=True, rotate_b=True, collidable=True, width=0, mass=1)
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

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_start_angle else 0, torch.pi / 2 if self.random_start_angle else 0)
        goal_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_goal_angle else 0, torch.pi / 2 if self.random_goal_angle else 0)
        start_delta_x = self.joint_length / 2 * torch.cos(start_angle)
        start_delta_x_abs = start_delta_x.abs()
        min_x_start = -self.world.x_semidim + (self.agent_radius + start_delta_x_abs)
        max_x_start = self.world.x_semidim - (self.agent_radius + start_delta_x_abs)
        start_delta_y = self.joint_length / 2 * torch.sin(start_angle)
        start_delta_y_abs = start_delta_y.abs()
        min_y_start = -self.world.y_semidim + (self.agent_radius + start_delta_y_abs)
        max_y_start = -2 * self.agent_radius - self.passage_width / 2 - start_delta_y_abs
        goal_delta_x = self.joint_length / 2 * torch.cos(goal_angle)
        goal_delta_x_abs = goal_delta_x.abs()
        min_x_goal = -self.world.x_semidim + (self.agent_radius + goal_delta_x_abs)
        max_x_goal = self.world.x_semidim - (self.agent_radius + goal_delta_x_abs)
        goal_delta_y = self.joint_length / 2 * torch.sin(goal_angle)
        goal_delta_y_abs = goal_delta_y.abs()
        min_y_goal = 2 * self.agent_radius + self.passage_width / 2 + goal_delta_y_abs
        max_y_goal = self.world.y_semidim - (self.agent_radius + goal_delta_y_abs)
        joint_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
        goal_pos = torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1)
        self.goal.set_pos(goal_pos, batch_index=env_index)
        self.goal.set_rot(goal_angle, batch_index=env_index)
        order = torch.randperm(self.n_agents).tolist()
        agents = [self.world.agents[i] for i in order]
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
            self.passed = torch.zeros((self.world.batch_dim,), device=self.world.device)
            self.joint.pos_shaping_pre = torch.stack([torch.linalg.vector_norm(self.joint.landmark.state.pos - p.state.pos, dim=1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
            self.joint.pos_shaping_post = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
            self.joint.rot_shaping_pre = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.middle_angle) * self.rot_shaping_factor
            self.joint.rot_shaping_post = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot) * self.rot_shaping_factor
        else:
            self.passed[env_index] = 0
            self.joint.pos_shaping_pre[env_index] = torch.stack([torch.linalg.vector_norm(self.joint.landmark.state.pos[env_index] - p.state.pos[env_index]).unsqueeze(-1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
            self.joint.pos_shaping_post[env_index] = torch.linalg.vector_norm(self.joint.landmark.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor
            self.joint.rot_shaping_pre[env_index] = get_line_angle_dist_0_180(self.joint.landmark.state.rot[env_index], self.middle_angle) * self.rot_shaping_factor
            self.joint.rot_shaping_post[env_index] = get_line_angle_dist_0_180(self.joint.landmark.state.rot[env_index], self.goal.state.rot[env_index]) * self.rot_shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.pos_rew[:] = 0
            self.rot_rew[:] = 0
            self.collision_rew[:] = 0
            joint_passed = self.joint.landmark.state.pos[:, Y] > 0
            self.all_passed = (torch.stack([a.state.pos[:, Y] for a in self.world.agents], dim=1) > self.passage_width / 2).all(dim=1)
            joint_dist_to_closest_pass = torch.stack([torch.linalg.vector_norm(self.joint.landmark.state.pos - p.state.pos, dim=1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0]
            joint_shaping = joint_dist_to_closest_pass * self.pos_shaping_factor
            self.pos_rew[~joint_passed] += (self.joint.pos_shaping_pre - joint_shaping)[~joint_passed]
            self.joint.pos_shaping_pre = joint_shaping
            joint_dist_to_goal = torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1)
            joint_shaping = joint_dist_to_goal * self.pos_shaping_factor
            self.pos_rew[joint_passed] += (self.joint.pos_shaping_post - joint_shaping)[joint_passed]
            self.joint.pos_shaping_post = joint_shaping
            rot_passed = self.all_passed if self.all_passed_rot else joint_passed
            joint_dist_to_90_rot = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.middle_angle)
            joint_shaping = joint_dist_to_90_rot * self.rot_shaping_factor
            self.rot_rew[~rot_passed] += (self.joint.rot_shaping_pre - joint_shaping)[~rot_passed]
            self.joint.rot_shaping_pre = joint_shaping
            joint_dist_to_goal_rot = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot)
            joint_shaping = joint_dist_to_goal_rot * self.rot_shaping_factor
            self.rot_rew[rot_passed] += (self.joint.rot_shaping_post - joint_shaping)[rot_passed]
            self.joint.rot_shaping_post = joint_shaping
            for a in self.world.agents + ([self.mass] if self.asym_package else []):
                for passage in self.passages:
                    if passage.collide:
                        self.collision_rew[self.world.get_distance(a, passage) <= self.min_collision_distance] += self.collision_reward
                    for wall in self.walls:
                        self.collision_rew[self.world.get_distance(a, wall) <= self.min_collision_distance] += self.collision_reward
            for p in self.passages:
                if p.collide:
                    self.collision_rew[self.world.get_distance(p, self.joint.landmark) <= self.min_collision_distance] += self.collision_reward
            self.energy_expenditure = torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * a.f_range ** 2) for a in self.world.agents], dim=1).sum(-1)
            self.energy_rew = -self.energy_expenditure * self.energy_reward_coeff
            self.rew = self.pos_rew + self.rot_rew + self.collision_rew + self.energy_rew
        return self.rew

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
        passage_obs = []
        for passage in self.passages:
            if not passage.collide:
                passage_obs.append(agent.state.pos - passage.state.pos)
        observations = [agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos, *passage_obs, angle_to_vector(self.goal.state.rot)] + ([angle_to_vector(joint_angle)] if self.observe_joint_angle else [])
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def done(self):
        return torch.all((torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) <= 0.01) * (get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot).unsqueeze(-1) <= 0.01), dim=1)

    def process_action(self, agent: Agent):
        if self.use_controller:
            vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
            agent.controller.reset(vel_is_zero)
            agent.controller.process_force()

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

        def removed(i):
            return self.n_boxes // 2 - self.n_passages / 2 <= i < self.n_boxes // 2 + self.n_passages / 2
        for i in range(self.n_boxes):
            passage = Landmark(name=f'passage {i}', collide=not removed(i), movable=False, shape=Box(length=self.passage_length, width=self.passage_width), color=Color.RED, collision_filter=lambda e: not isinstance(e.shape, Box))
            if not passage.collide:
                self.non_collide_passages.append(passage)
            else:
                self.collide_passages.append(passage)
            self.passages.append(passage)
            world.add_landmark(passage)

        def joint_collides(e):
            if e in self.collide_passages and self.fixed_passage:
                return e.neighbour
            elif e in self.collide_passages:
                return True
            return False
        self.joint.landmark.collision_filter = joint_collides

    def spawn_passage_map(self, env_index):
        passage_indexes = []
        j = self.n_boxes // 2
        for i in range(self.n_passages):
            if self.fixed_passage:
                j += i * (-1 if i % 2 == 0 else 1)
                passage_index = torch.full((self.world.batch_dim,) if env_index is None else (1,), j, device=self.world.device)
            else:
                passage_index = torch.randint(0, self.n_boxes - 1, (self.world.batch_dim,) if env_index is None else (1,), device=self.world.device)
            passage_indexes.append(passage_index)

        def is_passage(i):
            is_pass = torch.full(i.shape, False, device=self.world.device)
            for index in passage_indexes:
                is_pass += i == index
            return is_pass

        def get_pos(i):
            pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2, 0.0], dtype=torch.float32, device=self.world.device).repeat(i.shape[0], 1)
            pos[:, X] += self.passage_length * i
            return pos
        for index, i in enumerate(passage_indexes):
            self.non_collide_passages[index].is_rendering[:] = False
            self.non_collide_passages[index].set_pos(get_pos(i), batch_index=env_index)
        i = torch.zeros((self.world.batch_dim,) if env_index is None else (1,), dtype=torch.int, device=self.world.device)
        for passage in self.collide_passages:
            is_pass = is_passage(i)
            while is_pass.any():
                i[is_pass] += 1
                is_pass = is_passage(i)
            passage.set_pos(get_pos(i), batch_index=env_index)
            if self.fixed_passage:
                passage.neighbour = (is_passage(i - 1) + is_passage(i + 1)).all()
            elif env_index is None:
                passage.neighbour = is_passage(i - 1) + is_passage(i + 1)
            else:
                passage.neighbour[env_index] = is_passage(i - 1) + is_passage(i + 1)
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

def info(self, agent: Agent) -> Dict[str, Tensor]:
    is_first = self.world.agents[0] == agent
    if is_first:
        just_passed = self.all_passed * (self.passed == 0)
        self.passed[just_passed] = 100
        self.info_stored = {'pos_rew': self.pos_rew, 'rot_rew': self.rot_rew, 'collision_rew': self.collision_rew, 'energy_rew': self.energy_rew, 'passed': just_passed.to(torch.int)}
    return self.info_stored

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

class RenderingCallbacks(DefaultCallbacks):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frames = []

    def on_episode_step(self, *, worker: RolloutWorker, base_env: BaseEnv, policies: Optional[Dict[PolicyID, Policy]]=None, episode: Episode, **kwargs) -> None:
        self.frames.append(base_env.vector_env.try_render_at(mode='rgb_array'))

    def on_episode_end(self, *, worker: RolloutWorker, base_env: BaseEnv, policies: Dict[PolicyID, Policy], episode: Episode, **kwargs) -> None:
        vid = np.transpose(self.frames, (0, 3, 1, 2))
        episode.media['rendering'] = wandb.Video(vid, fps=1 / base_env.vector_env.env.world.dt, format='mp4')
        self.frames = []

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.frames = []

def x_to_rgb_colormap(x: np.ndarray, low: float=None, high: float=None, alpha: float=1.0, cmap_name: str='viridis', cmap_res: int=10):
    from matplotlib import cm
    colormap = cm.get_cmap(cmap_name, cmap_res)(range(cmap_res))[:, :-1]
    if low is None:
        low = np.min(x)
    if high is None:
        high = np.max(x)
    x = np.clip(x, low, high)
    if high - low > 1e-05:
        x = (x - low) / (high - low) * (cmap_res - 1)
    x_c0_idx = np.floor(x).astype(int)
    x_c1_idx = np.ceil(x).astype(int)
    x_c0 = colormap[x_c0_idx, :]
    x_c1 = colormap[x_c1_idx, :]
    t = x - x_c0_idx
    rgb = t[:, None] * x_c1 + (1 - t)[:, None] * x_c0
    colors = np.concatenate([rgb, alpha * np.ones((rgb.shape[0], 1))], axis=-1)
    return colors

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
def where_from_index(env_index, new_value, old_value):
    mask = torch.zeros_like(old_value, dtype=torch.bool, device=old_value.device)
    mask[env_index] = True
    return torch.where(mask, new_value, old_value)

class TextLine(Geom):

    def __init__(self, text: str='', font_size: int=15, x: float=0.0, y: float=0.0):
        super().__init__()
        if pyglet.font.have_font('Courier'):
            font = 'Courier'
        elif pyglet.font.have_font('Secret Code'):
            font = 'Secret Code'
        else:
            font = None
        self.label = pyglet.text.Label(text, font_name=font, font_size=font_size, color=(0, 0, 0, 255), x=x, y=y, anchor_x='left', anchor_y='bottom')

    def render1(self):
        if self.label is not None:
            self.label.draw()

    def set_text(self, text, font_size: Optional[int]=None):
        self.label.text = text
        if font_size is not None:
            self.label.font_size = font_size

def __init__(self, text: str='', font_size: int=15, x: float=0.0, y: float=0.0):
    super().__init__()
    if pyglet.font.have_font('Courier'):
        font = 'Courier'
    elif pyglet.font.have_font('Secret Code'):
        font = 'Secret Code'
    else:
        font = None
    self.label = pyglet.text.Label(text, font_name=font, font_size=font_size, color=(0, 0, 0, 255), x=x, y=y, anchor_x='left', anchor_y='bottom')

class Point(Geom):

    def __init__(self):
        Geom.__init__(self)

    def render1(self):
        glBegin(GL_POINTS)
        glVertex3f(0.0, 0.0, 0.0)
        glEnd()

def __init__(self):
    Geom.__init__(self)

class Image(Geom):

    def __init__(self, img, x, y, scale):
        super().__init__()
        self.x = x
        self.y = y
        self.scale = scale
        img_shape = img.shape
        img = img.astype(np.uint8).reshape(-1)
        tex_data = (pyglet.gl.GLubyte * img.size)(*img)
        pyg_img = pyglet.image.ImageData(img_shape[1], img_shape[0], 'RGBA', tex_data, pitch=img_shape[1] * img_shape[2] * 1)
        self.img = pyg_img
        self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x, y=self.y, subpixel=True)
        self.sprite.update(scale=self.scale)

    def render1(self):
        self.sprite.draw()

def __init__(self, img, x, y, scale):
    super().__init__()
    self.x = x
    self.y = y
    self.scale = scale
    img_shape = img.shape
    img = img.astype(np.uint8).reshape(-1)
    tex_data = (pyglet.gl.GLubyte * img.size)(*img)
    pyg_img = pyglet.image.ImageData(img_shape[1], img_shape[0], 'RGBA', tex_data, pitch=img_shape[1] * img_shape[2] * 1)
    self.img = pyg_img
    self.sprite = pyglet.sprite.Sprite(img=self.img, x=self.x, y=self.y, subpixel=True)
    self.sprite.update(scale=self.scale)

class FilledPolygon(Geom):

    def __init__(self, v, draw_border: float=True):
        Geom.__init__(self)
        self.draw_border = draw_border
        self.v = v

    def render1(self):
        if len(self.v) == 4:
            glBegin(GL_QUADS)
        elif len(self.v) > 4:
            glBegin(GL_POLYGON)
        else:
            glBegin(GL_TRIANGLES)
        for p in self.v:
            glVertex3f(p[0], p[1], 0)
        glEnd()
        if self.draw_border:
            color = (self._color.vec4[0] * 0.5, self._color.vec4[1] * 0.5, self._color.vec4[2] * 0.5, self._color.vec4[3] * 0.5)
            glColor4f(*color)
            glBegin(GL_LINE_LOOP)
            for p in self.v:
                glVertex3f(p[0], p[1], 0)
            glEnd()

def __init__(self, v, draw_border: float=True):
    Geom.__init__(self)
    self.draw_border = draw_border
    self.v = v

class Compound(Geom):

    def __init__(self, gs):
        Geom.__init__(self)
        self.gs = gs
        for g in self.gs:
            g.attrs = [a for a in g.attrs if not isinstance(a, Color)]

    def render1(self):
        for g in self.gs:
            g.render()

def __init__(self, gs):
    Geom.__init__(self)
    self.gs = gs
    for g in self.gs:
        g.attrs = [a for a in g.attrs if not isinstance(a, Color)]

class PolyLine(Geom):

    def __init__(self, v, close):
        Geom.__init__(self)
        self.v = v
        self.close = close
        self.linewidth = LineWidth(1)
        self.add_attr(self.linewidth)

    def render1(self):
        glBegin(GL_LINE_LOOP if self.close else GL_LINE_STRIP)
        for p in self.v:
            glVertex3f(p[0], p[1], 0)
        glEnd()

    def set_linewidth(self, x):
        self.linewidth.stroke = x

def __init__(self, v, close):
    Geom.__init__(self)
    self.v = v
    self.close = close
    self.linewidth = LineWidth(1)
    self.add_attr(self.linewidth)

class Line(Geom):

    def __init__(self, start=(0.0, 0.0), end=(0.0, 0.0), width: float=1):
        Geom.__init__(self)
        self.start = start
        self.end = end
        self.linewidth = LineWidth(width)
        self.add_attr(self.linewidth)

    def set_linewidth(self, x):
        self.linewidth.stroke = x

    def render1(self):
        glBegin(GL_LINES)
        glVertex2f(*self.start)
        glVertex2f(*self.end)
        glEnd()

def __init__(self, start=(0.0, 0.0), end=(0.0, 0.0), width: float=1):
    Geom.__init__(self)
    self.start = start
    self.end = end
    self.linewidth = LineWidth(width)
    self.add_attr(self.linewidth)

class Grid(Geom):

    def __init__(self, spacing: float=0.1, length: float=50, width: float=0.5):
        Geom.__init__(self)
        self.spacing = spacing
        self.linewidth = LineWidth(width)
        self.length = length
        self.add_attr(self.linewidth)

    def set_linewidth(self, x):
        self.linewidth.stroke = x

    def render1(self):
        for point in np.arange(-self.length / 2, self.length / 2, self.spacing):
            glBegin(GL_LINES)
            glVertex2f(point, -self.length / 2)
            glVertex2f(point, self.length / 2)
            glEnd()
            glBegin(GL_LINES)
            glVertex2f(-self.length / 2, point)
            glVertex2f(self.length / 2, point)
            glEnd()

def __init__(self, spacing: float=0.1, length: float=50, width: float=0.5):
    Geom.__init__(self)
    self.spacing = spacing
    self.linewidth = LineWidth(width)
    self.length = length
    self.add_attr(self.linewidth)

class Box(Shape):

    def __init__(self, length: float=0.3, width: float=0.1, hollow: bool=False):
        super().__init__()
        assert length > 0, f'Length must be > 0, got {length}'
        assert width > 0, f'Width must be > 0, got {length}'
        self._length = length
        self._width = width
        self.hollow = hollow

    @property
    def length(self):
        return self._length

    @property
    def width(self):
        return self._width

    def get_delta_from_anchor(self, anchor: Tuple[float, float]) -> Tuple[float, float]:
        return (anchor[X] * self.length / 2, anchor[Y] * self.width / 2)

    def moment_of_inertia(self, mass: float):
        return 1 / 12 * mass * (self.length ** 2 + self.width ** 2)

    def circumscribed_radius(self):
        return math.sqrt((self.length / 2) ** 2 + (self.width / 2) ** 2)

    def get_geometry(self) -> 'Geom':
        from vmas.simulator import rendering
        l, r, t, b = (-self.length / 2, self.length / 2, self.width / 2, -self.width / 2)
        return rendering.make_polygon([(l, b), (l, t), (r, t), (r, b)])

def __init__(self, length: float=0.3, width: float=0.1, hollow: bool=False):
    super().__init__()
    assert length > 0, f'Length must be > 0, got {length}'
    assert width > 0, f'Width must be > 0, got {length}'
    self._length = length
    self._width = width
    self.hollow = hollow

class Sphere(Shape):

    def __init__(self, radius: float=0.05):
        super().__init__()
        assert radius > 0, f'Radius must be > 0, got {radius}'
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    def get_delta_from_anchor(self, anchor: Tuple[float, float]) -> Tuple[float, float]:
        delta = torch.tensor([anchor[X] * self.radius, anchor[Y] * self.radius]).to(torch.float32)
        delta_norm = torch.linalg.vector_norm(delta)
        if delta_norm > self.radius:
            delta /= delta_norm * self.radius
        return tuple(delta.tolist())

    def moment_of_inertia(self, mass: float):
        return 1 / 2 * mass * self.radius ** 2

    def circumscribed_radius(self):
        return self.radius

    def get_geometry(self) -> 'Geom':
        from vmas.simulator import rendering
        return rendering.make_circle(self.radius)

def __init__(self, radius: float=0.05):
    super().__init__()
    assert radius > 0, f'Radius must be > 0, got {radius}'
    self._radius = radius

class Line(Shape):

    def __init__(self, length: float=0.5):
        super().__init__()
        assert length > 0, f'Length must be > 0, got {length}'
        self._length = length
        self._width = 2

    @property
    def length(self):
        return self._length

    @property
    def width(self):
        return self._width

    def moment_of_inertia(self, mass: float):
        return 1 / 12 * mass * self.length ** 2

    def circumscribed_radius(self):
        return self.length / 2

    def get_delta_from_anchor(self, anchor: Tuple[float, float]) -> Tuple[float, float]:
        return (anchor[X] * self.length / 2, 0.0)

    def get_geometry(self) -> 'Geom':
        from vmas.simulator import rendering
        return rendering.Line((-self.length / 2, 0), (self.length / 2, 0), width=self.width)

def __init__(self, length: float=0.5):
    super().__init__()
    assert length > 0, f'Length must be > 0, got {length}'
    self._length = length
    self._width = 2

class EntityState(TorchVectorizedObject):

    def __init__(self):
        super().__init__()
        self._pos = None
        self._vel = None
        self._rot = None
        self._ang_vel = None

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert pos.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {pos.shape[0]}, expected {self._batch_dim}'
        if self._vel is not None:
            assert pos.shape == self._vel.shape, f'Position shape must match velocity shape, got {pos.shape} expected {self._vel.shape}'
        self._pos = pos.to(self._device)

    @property
    def vel(self):
        return self._vel

    @vel.setter
    def vel(self, vel: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert vel.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {vel.shape[0]}, expected {self._batch_dim}'
        if self._pos is not None:
            assert vel.shape == self._pos.shape, f'Velocity shape must match position shape, got {vel.shape} expected {self._pos.shape}'
        self._vel = vel.to(self._device)

    @property
    def ang_vel(self):
        return self._ang_vel

    @ang_vel.setter
    def ang_vel(self, ang_vel: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert ang_vel.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {ang_vel.shape[0]}, expected {self._batch_dim}'
        self._ang_vel = ang_vel.to(self._device)

    @property
    def rot(self):
        return self._rot

    @rot.setter
    def rot(self, rot: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert rot.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {rot.shape[0]}, expected {self._batch_dim}'
        self._rot = rot.to(self._device)

    def _reset(self, env_index: typing.Optional[int]):
        for attr_name in ['pos', 'rot', 'vel', 'ang_vel']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                if env_index is None:
                    self.__setattr__(attr_name, torch.zeros_like(attr))
                else:
                    self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))

    def zero_grad(self):
        for attr_name in ['pos', 'rot', 'vel', 'ang_vel']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                self.__setattr__(attr_name, attr.detach())

    def _spawn(self, dim_c: int, dim_p: int):
        self.pos = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
        self.vel = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
        self.rot = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)
        self.ang_vel = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)

def __init__(self):
    super().__init__()
    self._pos = None
    self._vel = None
    self._rot = None
    self._ang_vel = None

@pos.setter
def pos(self, pos: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert pos.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {pos.shape[0]}, expected {self._batch_dim}'
    if self._vel is not None:
        assert pos.shape == self._vel.shape, f'Position shape must match velocity shape, got {pos.shape} expected {self._vel.shape}'
    self._pos = pos.to(self._device)

@vel.setter
def vel(self, vel: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert vel.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {vel.shape[0]}, expected {self._batch_dim}'
    if self._pos is not None:
        assert vel.shape == self._pos.shape, f'Velocity shape must match position shape, got {vel.shape} expected {self._pos.shape}'
    self._vel = vel.to(self._device)

@ang_vel.setter
def ang_vel(self, ang_vel: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert ang_vel.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {ang_vel.shape[0]}, expected {self._batch_dim}'
    self._ang_vel = ang_vel.to(self._device)

@rot.setter
def rot(self, rot: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert rot.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {rot.shape[0]}, expected {self._batch_dim}'
    self._rot = rot.to(self._device)

def _reset(self, env_index: typing.Optional[int]):
    for attr_name in ['pos', 'rot', 'vel', 'ang_vel']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            if env_index is None:
                self.__setattr__(attr_name, torch.zeros_like(attr))
            else:
                self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))

def zero_grad(self):
    for attr_name in ['pos', 'rot', 'vel', 'ang_vel']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            self.__setattr__(attr_name, attr.detach())

class AgentState(EntityState):

    def __init__(self):
        super().__init__()
        self._c = None
        self._force = None
        self._torque = None

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert c.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {c.shape[0]}, expected {self._batch_dim}'
        self._c = c.to(self._device)

    @property
    def force(self):
        return self._force

    @force.setter
    def force(self, value):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert value.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {value.shape[0]}, expected {self._batch_dim}'
        self._force = value.to(self._device)

    @property
    def torque(self):
        return self._torque

    @torque.setter
    def torque(self, value):
        assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
        assert value.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {value.shape[0]}, expected {self._batch_dim}'
        self._torque = value.to(self._device)

    @override(EntityState)
    def _reset(self, env_index: typing.Optional[int]):
        for attr_name in ['c', 'force', 'torque']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                if env_index is None:
                    self.__setattr__(attr_name, torch.zeros_like(attr))
                else:
                    self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))
        super()._reset(env_index)

    @override(EntityState)
    def zero_grad(self):
        for attr_name in ['c', 'force', 'torque']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                self.__setattr__(attr_name, attr.detach())
        super().zero_grad()

    @override(EntityState)
    def _spawn(self, dim_c: int, dim_p: int):
        if dim_c > 0:
            self.c = torch.zeros(self.batch_dim, dim_c, device=self.device, dtype=torch.float32)
        self.force = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
        self.torque = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)
        super()._spawn(dim_c, dim_p)

def __init__(self):
    super().__init__()
    self._c = None
    self._force = None
    self._torque = None

@c.setter
def c(self, c: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert c.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {c.shape[0]}, expected {self._batch_dim}'
    self._c = c.to(self._device)

@force.setter
def force(self, value):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert value.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {value.shape[0]}, expected {self._batch_dim}'
    self._force = value.to(self._device)

@torque.setter
def torque(self, value):
    assert self._batch_dim is not None and self._device is not None, 'First add an entity to the world before setting its state'
    assert value.shape[0] == self._batch_dim, f'Internal state must match batch dim, got {value.shape[0]}, expected {self._batch_dim}'
    self._torque = value.to(self._device)

@override(EntityState)
def _reset(self, env_index: typing.Optional[int]):
    for attr_name in ['c', 'force', 'torque']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            if env_index is None:
                self.__setattr__(attr_name, torch.zeros_like(attr))
            else:
                self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))
    super()._reset(env_index)

@override(EntityState)
def zero_grad(self):
    for attr_name in ['c', 'force', 'torque']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            self.__setattr__(attr_name, attr.detach())
    super().zero_grad()

@override(EntityState)
def _spawn(self, dim_c: int, dim_p: int):
    if dim_c > 0:
        self.c = torch.zeros(self.batch_dim, dim_c, device=self.device, dtype=torch.float32)
    self.force = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
    self.torque = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)
    super()._spawn(dim_c, dim_p)

class Action(TorchVectorizedObject):

    def __init__(self, u_range: Union[float, Sequence[float]], u_multiplier: Union[float, Sequence[float]], u_noise: Union[float, Sequence[float]], action_size: int):
        super().__init__()
        self._u_noise = u_noise
        self._u_range = u_range
        self._u_multiplier = u_multiplier
        self.action_size = action_size
        self._u = None
        self._c = None
        self._u_range_tensor = None
        self._u_multiplier_tensor = None
        self._u_noise_tensor = None
        self._check_action_init()

    def _check_action_init(self):
        for attr in (self.u_multiplier, self.u_range, self.u_noise):
            if isinstance(attr, List):
                assert len(attr) == self.action_size, 'Action attributes u_... must be either a float or a list of floats (one per action) all with same length'

    @property
    def u(self):
        return self._u

    @u.setter
    def u(self, u: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
        assert u.shape[0] == self._batch_dim, f'Action must match batch dim, got {u.shape[0]}, expected {self._batch_dim}'
        self._u = u.to(self._device)

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c: Tensor):
        assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
        assert c.shape[0] == self._batch_dim, f'Action must match batch dim, got {c.shape[0]}, expected {self._batch_dim}'
        self._c = c.to(self._device)

    @property
    def u_range(self):
        return self._u_range

    @property
    def u_multiplier(self):
        return self._u_multiplier

    @property
    def u_noise(self):
        return self._u_noise

    @property
    def u_range_tensor(self):
        if self._u_range_tensor is None:
            self._u_range_tensor = self._to_tensor(self.u_range)
        return self._u_range_tensor

    @property
    def u_multiplier_tensor(self):
        if self._u_multiplier_tensor is None:
            self._u_multiplier_tensor = self._to_tensor(self.u_multiplier)
        return self._u_multiplier_tensor

    @property
    def u_noise_tensor(self):
        if self._u_noise_tensor is None:
            self._u_noise_tensor = self._to_tensor(self.u_noise)
        return self._u_noise_tensor

    def _to_tensor(self, value):
        return torch.tensor(value if isinstance(value, Sequence) else [value] * self.action_size, device=self.device, dtype=torch.float)

    def _reset(self, env_index: typing.Optional[int]):
        for attr_name in ['u', 'c']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                if env_index is None:
                    self.__setattr__(attr_name, torch.zeros_like(attr))
                else:
                    self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))

    def zero_grad(self):
        for attr_name in ['u', 'c']:
            attr = self.__getattribute__(attr_name)
            if attr is not None:
                self.__setattr__(attr_name, attr.detach())

def __init__(self, u_range: Union[float, Sequence[float]], u_multiplier: Union[float, Sequence[float]], u_noise: Union[float, Sequence[float]], action_size: int):
    super().__init__()
    self._u_noise = u_noise
    self._u_range = u_range
    self._u_multiplier = u_multiplier
    self.action_size = action_size
    self._u = None
    self._c = None
    self._u_range_tensor = None
    self._u_multiplier_tensor = None
    self._u_noise_tensor = None
    self._check_action_init()

@u.setter
def u(self, u: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
    assert u.shape[0] == self._batch_dim, f'Action must match batch dim, got {u.shape[0]}, expected {self._batch_dim}'
    self._u = u.to(self._device)

@c.setter
def c(self, c: Tensor):
    assert self._batch_dim is not None and self._device is not None, 'First add an agent to the world before setting its action'
    assert c.shape[0] == self._batch_dim, f'Action must match batch dim, got {c.shape[0]}, expected {self._batch_dim}'
    self._c = c.to(self._device)

def _reset(self, env_index: typing.Optional[int]):
    for attr_name in ['u', 'c']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            if env_index is None:
                self.__setattr__(attr_name, torch.zeros_like(attr))
            else:
                self.__setattr__(attr_name, TorchUtils.where_from_index(env_index, 0, attr))

def zero_grad(self):
    for attr_name in ['u', 'c']:
        attr = self.__getattribute__(attr_name)
        if attr is not None:
            self.__setattr__(attr_name, attr.detach())

class Entity(TorchVectorizedObject, Observable, ABC):

    def __init__(self, name: str, movable: bool=False, rotatable: bool=False, collide: bool=True, density: float=25.0, mass: float=1.0, shape: Shape=None, v_range: float=None, max_speed: float=None, color=Color.GRAY, is_joint: bool=False, drag: float=None, linear_friction: float=None, angular_friction: float=None, gravity: typing.Union[float, Tensor]=None, collision_filter: Callable[[Entity], bool]=lambda _: True):
        if shape is None:
            shape = Sphere()
        TorchVectorizedObject.__init__(self)
        Observable.__init__(self)
        self._name = name
        self._movable = movable
        self._rotatable = rotatable
        self._collide = collide
        self._density = density
        self._mass = mass
        self._max_speed = max_speed
        self._v_range = v_range
        self._color = color
        self._shape = shape
        self._is_joint = is_joint
        self._collision_filter = collision_filter
        self._state = EntityState()
        self._drag = drag
        self._linear_friction = linear_friction
        self._angular_friction = angular_friction
        if isinstance(gravity, Tensor):
            self._gravity = gravity
        else:
            self._gravity = torch.tensor(gravity, device=self.device, dtype=torch.float32) if gravity is not None else gravity
        self._goal = None
        self._render = None

    @TorchVectorizedObject.batch_dim.setter
    def batch_dim(self, batch_dim: int):
        TorchVectorizedObject.batch_dim.fset(self, batch_dim)
        self._state.batch_dim = batch_dim

    @property
    def is_rendering(self):
        if self._render is None:
            self.reset_render()
        return self._render

    def reset_render(self):
        self._render = torch.full((self.batch_dim,), True, device=self.device)

    def collides(self, entity: Entity):
        if not self.collide:
            return False
        return self._collision_filter(entity)

    @property
    def is_joint(self):
        return self._is_joint

    @property
    def mass(self):
        return self._mass

    @mass.setter
    def mass(self, mass: float):
        self._mass = mass

    @property
    def moment_of_inertia(self):
        return self.shape.moment_of_inertia(self.mass)

    @property
    def state(self):
        return self._state

    @property
    def movable(self):
        return self._movable

    @property
    def collide(self):
        return self._collide

    @property
    def shape(self):
        return self._shape

    @property
    def max_speed(self):
        return self._max_speed

    @property
    def v_range(self):
        return self._v_range

    @property
    def name(self):
        return self._name

    @property
    def rotatable(self):
        return self._rotatable

    @property
    def color(self):
        if isinstance(self._color, Color):
            return self._color.value
        return self._color

    @color.setter
    def color(self, color):
        self._color = color

    @property
    def goal(self):
        return self._goal

    @property
    def drag(self):
        return self._drag

    @property
    def linear_friction(self):
        return self._linear_friction

    @linear_friction.setter
    def linear_friction(self, value):
        self._linear_friction = value

    @property
    def gravity(self):
        return self._gravity

    @gravity.setter
    def gravity(self, value):
        self._gravity = value

    @property
    def angular_friction(self):
        return self._angular_friction

    @goal.setter
    def goal(self, goal: Entity):
        self._goal = goal

    @property
    def collision_filter(self):
        return self._collision_filter

    @collision_filter.setter
    def collision_filter(self, collision_filter: Callable[[Entity], bool]):
        self._collision_filter = collision_filter

    def _spawn(self, dim_c: int, dim_p: int):
        self.state._spawn(dim_c, dim_p)

    def _reset(self, env_index: int):
        self.state._reset(env_index)

    def zero_grad(self):
        self.state.zero_grad()

    def set_pos(self, pos: Tensor, batch_index: int):
        self._set_state_property(EntityState.pos, self.state, pos, batch_index)

    def set_vel(self, vel: Tensor, batch_index: int):
        self._set_state_property(EntityState.vel, self.state, vel, batch_index)

    def set_rot(self, rot: Tensor, batch_index: int):
        self._set_state_property(EntityState.rot, self.state, rot, batch_index)

    def set_ang_vel(self, ang_vel: Tensor, batch_index: int):
        self._set_state_property(EntityState.ang_vel, self.state, ang_vel, batch_index)

    def _set_state_property(self, prop, entity: EntityState, new: Tensor, batch_index: int):
        assert self.batch_dim is not None, f'Tried to set property of {self.name} without adding it to the world'
        self._check_batch_index(batch_index)
        new = new.to(self.device)
        if batch_index is None:
            if len(new.shape) > 1 and new.shape[0] == self.batch_dim:
                prop.fset(entity, new)
            else:
                prop.fset(entity, new.repeat(self.batch_dim, 1))
        else:
            value = prop.fget(entity)
            value[batch_index] = new
        self.notify_observers()

    @override(TorchVectorizedObject)
    def to(self, device: torch.device):
        super().to(device)
        self.state.to(device)

    def render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        if not self.is_rendering[env_index]:
            return []
        geom = self.shape.get_geometry()
        xform = rendering.Transform()
        geom.add_attr(xform)
        xform.set_translation(*self.state.pos[env_index])
        xform.set_rotation(self.state.rot[env_index])
        color = self.color
        if isinstance(color, torch.Tensor) and len(color.shape) > 1:
            color = color[env_index]
        geom.set_color(*color)
        return [geom]

def __init__(self, name: str, movable: bool=False, rotatable: bool=False, collide: bool=True, density: float=25.0, mass: float=1.0, shape: Shape=None, v_range: float=None, max_speed: float=None, color=Color.GRAY, is_joint: bool=False, drag: float=None, linear_friction: float=None, angular_friction: float=None, gravity: typing.Union[float, Tensor]=None, collision_filter: Callable[[Entity], bool]=lambda _: True):
    if shape is None:
        shape = Sphere()
    TorchVectorizedObject.__init__(self)
    Observable.__init__(self)
    self._name = name
    self._movable = movable
    self._rotatable = rotatable
    self._collide = collide
    self._density = density
    self._mass = mass
    self._max_speed = max_speed
    self._v_range = v_range
    self._color = color
    self._shape = shape
    self._is_joint = is_joint
    self._collision_filter = collision_filter
    self._state = EntityState()
    self._drag = drag
    self._linear_friction = linear_friction
    self._angular_friction = angular_friction
    if isinstance(gravity, Tensor):
        self._gravity = gravity
    else:
        self._gravity = torch.tensor(gravity, device=self.device, dtype=torch.float32) if gravity is not None else gravity
    self._goal = None
    self._render = None

def _spawn(self, dim_c: int, dim_p: int):
    self.state._spawn(dim_c, dim_p)

def _reset(self, env_index: int):
    self.state._reset(env_index)

def zero_grad(self):
    self.state.zero_grad()

@override(TorchVectorizedObject)
def to(self, device: torch.device):
    super().to(device)
    self.state.to(device)

class Landmark(Entity):

    def __init__(self, name: str, shape: Shape=None, movable: bool=False, rotatable: bool=False, collide: bool=True, density: float=25.0, mass: float=1.0, v_range: float=None, max_speed: float=None, color=Color.GRAY, is_joint: bool=False, drag: float=None, linear_friction: float=None, angular_friction: float=None, gravity: float=None, collision_filter: Callable[[Entity], bool]=lambda _: True):
        super().__init__(name, movable, rotatable, collide, density, mass, shape, v_range, max_speed, color, is_joint, drag, linear_friction, angular_friction, gravity, collision_filter)

def __init__(self, name: str, shape: Shape=None, movable: bool=False, rotatable: bool=False, collide: bool=True, density: float=25.0, mass: float=1.0, v_range: float=None, max_speed: float=None, color=Color.GRAY, is_joint: bool=False, drag: float=None, linear_friction: float=None, angular_friction: float=None, gravity: float=None, collision_filter: Callable[[Entity], bool]=lambda _: True):
    super().__init__(name, movable, rotatable, collide, density, mass, shape, v_range, max_speed, color, is_joint, drag, linear_friction, angular_friction, gravity, collision_filter)

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

def reset(self, env_index: int):
    for e in self.entities:
        e._reset(env_index)

def zero_grad(self):
    for e in self.entities:
        e.zero_grad()

@override(TorchVectorizedObject)
def to(self, device: torch.device):
    super().to(device)
    for e in self.entities:
        e.to(device)

class Sensor(ABC):

    def __init__(self, world: vmas.simulator.core.World):
        super().__init__()
        self._world = world
        self._agent: Union[vmas.simulator.core.Agent, None] = None

    @property
    def agent(self) -> Union[vmas.simulator.core.Agent, None]:
        return self._agent

    @agent.setter
    def agent(self, agent: vmas.simulator.core.Agent):
        self._agent = agent

    @abstractmethod
    def measure(self):
        raise NotImplementedError

    @abstractmethod
    def render(self, env_index: int=0) -> 'List[Geom]':
        raise NotImplementedError

    def to(self, device: torch.device):
        raise NotImplementedError

def __init__(self, world: vmas.simulator.core.World):
    super().__init__()
    self._world = world
    self._agent: Union[vmas.simulator.core.Agent, None] = None

class Lidar(Sensor):

    def __init__(self, world: vmas.simulator.core.World, angle_start: float=0.0, angle_end: float=2 * torch.pi, n_rays: int=8, max_range: float=1.0, entity_filter: Callable[[vmas.simulator.core.Entity], bool]=lambda _: True, render_color: Union[Color, Tuple[float, float, float]]=Color.GRAY, alpha: float=1.0, render: bool=True):
        super().__init__(world)
        if (angle_start - angle_end) % (torch.pi * 2) < 1e-05:
            angles = torch.linspace(angle_start, angle_end, n_rays + 1, device=self._world.device)[:n_rays]
        else:
            angles = torch.linspace(angle_start, angle_end, n_rays, device=self._world.device)
        self._angles = angles.repeat(self._world.batch_dim, 1)
        self._max_range = max_range
        self._last_measurement = None
        self._render = render
        self._entity_filter = entity_filter
        self._render_color = render_color
        self._alpha = alpha

    def to(self, device: torch.device):
        self._angles = self._angles.to(device)

    @property
    def entity_filter(self):
        return self._entity_filter

    @entity_filter.setter
    def entity_filter(self, entity_filter: Callable[[vmas.simulator.core.Entity], bool]):
        self._entity_filter = entity_filter

    @property
    def render_color(self):
        if isinstance(self._render_color, Color):
            return self._render_color.value
        return self._render_color

    @property
    def alpha(self):
        return self._alpha

    def measure(self, vectorized: bool=True):
        if not vectorized:
            dists = []
            for angle in self._angles.unbind(1):
                dists.append(self._world.cast_ray(self.agent, angle + self.agent.state.rot.squeeze(-1), max_range=self._max_range, entity_filter=self.entity_filter))
            measurement = torch.stack(dists, dim=1)
        else:
            measurement = self._world.cast_rays(self.agent, self._angles + self.agent.state.rot, max_range=self._max_range, entity_filter=self.entity_filter)
        self._last_measurement = measurement
        return measurement

    def set_render(self, render: bool):
        self._render = render

    def render(self, env_index: int=0) -> 'List[Geom]':
        if not self._render:
            return []
        from vmas.simulator import rendering
        geoms: List[rendering.Geom] = []
        if self._last_measurement is not None:
            for angle, dist in zip(self._angles.unbind(1), self._last_measurement.unbind(1)):
                angle = angle[env_index] + self.agent.state.rot.squeeze(-1)[env_index]
                ray = rendering.Line((0, 0), (dist[env_index], 0), width=0.05)
                xform = rendering.Transform()
                xform.set_translation(*self.agent.state.pos[env_index])
                xform.set_rotation(angle)
                ray.add_attr(xform)
                ray.set_color(r=0, g=0, b=0, alpha=self.alpha)
                ray_circ = rendering.make_circle(0.01)
                ray_circ.set_color(*self.render_color, alpha=self.alpha)
                xform = rendering.Transform()
                rot = torch.stack([torch.cos(angle), torch.sin(angle)], dim=-1)
                pos_circ = self.agent.state.pos[env_index] + rot * dist.unsqueeze(1)[env_index]
                xform.set_translation(*pos_circ)
                ray_circ.add_attr(xform)
                geoms.append(ray)
                geoms.append(ray_circ)
        return geoms

def to(self, device: torch.device):
    self._angles = self._angles.to(device)

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

@override(TorchVectorizedObject)
def to(self, device: DEVICE_TYPING):
    device = torch.device(device)
    self.scenario.to(device)
    super().to(device)

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

def __init__(self, env: Environment):
    assert not env.terminated_truncated, 'Rllib wrapper is not compatible with termination and truncation flags. Please set `terminated_truncated=False` in the VMAS environment.'
    self._env = env
    super().__init__(observation_space=self._env.observation_space, action_space=self._env.action_space, num_envs=self._env.num_envs)

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

def __init__(self, env: Environment, return_numpy: bool=True, render_mode: str='human'):
    super().__init__(env, return_numpy=return_numpy, vectorized=False)
    assert env.num_envs == 1, 'GymnasiumEnv wrapper only supports singleton VMAS environment! For vectorized environments, use vectorized wrapper with `wrapper=gymnasium_vec`.'
    assert self._env.terminated_truncated, 'GymnasiumWrapper is only compatible with termination and truncation flags. Please set `terminated_truncated=True` in the VMAS environment.'
    self.observation_space = _convert_space(self._env.observation_space)
    self.action_space = _convert_space(self._env.action_space)
    self.render_mode = render_mode

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

def __init__(self, env: Environment, return_numpy: bool=True):
    super().__init__(env, return_numpy=return_numpy, vectorized=False)
    assert env.num_envs == 1, f'GymEnv wrapper is not vectorised, got env.num_envs: {env.num_envs}'
    assert not self._env.terminated_truncated, 'GymWrapper is not compatible with termination and truncation flags. Please set `terminated_truncated=False` in the VMAS environment.'
    self.observation_space = self._env.observation_space
    self.action_space = self._env.action_space

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

def reset(self, index: Optional[int]=None):
    if index is None:
        self.accum_errs = torch.zeros((self.world.batch_dim, self.world.dim_p), device=self.world.device)
        self.prev_err = torch.zeros((self.world.batch_dim, self.world.dim_p), device=self.world.device)
    else:
        self.accum_errs = TorchUtils.where_from_index(index, 0.0, self.accum_errs)
        self.prev_err = TorchUtils.where_from_index(index, 0.0, self.prev_err)

def process_force(self):
    self.accum_errs = self.accum_errs.to(self.world.device)
    self.prev_err = self.prev_err.to(self.world.device)
    des_vel = self.agent.action.u
    cur_vel = self.agent.state.vel
    err = des_vel - cur_vel
    u = self.ctrl_gain * (err + self.integralError(err) + self.rateError(err))
    u *= self.agent.mass
    self.agent.action.u = u

class Drone(Dynamics):

    def __init__(self, world: vmas.simulator.core.World, I_xx: float=0.0081, I_yy: float=0.0081, I_zz: float=0.0142, integration: str='rk4'):
        super().__init__()
        assert integration in ('rk4', 'euler')
        self.integration = integration
        self.I_xx = I_xx
        self.I_yy = I_yy
        self.I_zz = I_zz
        self.world = world
        self.g = 9.81
        self.dt = world.dt
        self.reset()

    def reset(self, index: Union[Tensor, int]=None):
        if index is None:
            self.drone_state = torch.zeros(self.world.batch_dim, 12, device=self.world.device)
        else:
            self.drone_state = TorchUtils.where_from_index(index, 0.0, self.drone_state)

    def zero_grad(self):
        self.drone_state = self.drone_state.detach()

    def f(self, state, thrust_command, torque_command):
        phi = state[:, 0]
        theta = state[:, 1]
        psi = state[:, 2]
        p = state[:, 3]
        q = state[:, 4]
        r = state[:, 5]
        x_dot = state[:, 6]
        y_dot = state[:, 7]
        z_dot = state[:, 8]
        c_phi = torch.cos(phi)
        s_phi = torch.sin(phi)
        c_theta = torch.cos(theta)
        s_theta = torch.sin(theta)
        c_psi = torch.cos(psi)
        s_psi = torch.sin(psi)
        x_ddot = (c_phi * s_theta * c_psi + s_phi * s_psi) * thrust_command / self.agent.mass
        y_ddot = (c_phi * s_theta * s_psi - s_phi * c_psi) * thrust_command / self.agent.mass
        z_ddot = c_phi * c_theta * thrust_command / self.agent.mass - self.g
        p_dot = (torque_command[:, 0] - (self.I_yy - self.I_zz) * q * r) / self.I_xx
        q_dot = (torque_command[:, 1] - (self.I_zz - self.I_xx) * p * r) / self.I_yy
        r_dot = (torque_command[:, 2] - (self.I_xx - self.I_yy) * p * q) / self.I_zz
        return torch.stack([p, q, r, p_dot, q_dot, r_dot, x_ddot, y_ddot, z_ddot, x_dot, y_dot, z_dot], dim=-1)

    def needs_reset(self) -> Tensor:
        return torch.any(self.drone_state[:, :2].abs() > 30 * (torch.pi / 180), dim=-1)

    def euler(self, state, thrust, torque):
        return self.dt * self.f(state, thrust, torque)

    def runge_kutta(self, state, thrust, torque):
        k1 = self.f(state, thrust, torque)
        k2 = self.f(state + self.dt * k1 / 2, thrust, torque)
        k3 = self.f(state + self.dt * k2 / 2, thrust, torque)
        k4 = self.f(state + self.dt * k3, thrust, torque)
        return self.dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    @property
    def needed_action_size(self) -> int:
        return 4

    def process_action(self):
        u = self.agent.action.u
        thrust = u[:, 0]
        torque = u[:, 1:4]
        thrust += self.agent.mass * self.g
        self.drone_state[:, 9] = self.agent.state.pos[:, 0]
        self.drone_state[:, 10] = self.agent.state.pos[:, 1]
        self.drone_state[:, 2] = self.agent.state.rot[:, 0]
        if self.integration == 'euler':
            delta_state = self.euler(self.drone_state, thrust, torque)
        else:
            delta_state = self.runge_kutta(self.drone_state, thrust, torque)
        self.drone_state = self.drone_state + delta_state
        v_cur_x = self.agent.state.vel[:, 0]
        v_cur_y = self.agent.state.vel[:, 1]
        v_cur_angular = self.agent.state.ang_vel[:, 0]
        acceleration_x = (delta_state[:, 6] - v_cur_x * self.dt) / self.dt ** 2
        acceleration_y = (delta_state[:, 7] - v_cur_y * self.dt) / self.dt ** 2
        acceleration_angular = (delta_state[:, 5] - v_cur_angular * self.dt) / self.dt ** 2
        force_x = self.agent.mass * acceleration_x
        force_y = self.agent.mass * acceleration_y
        torque_yaw = self.agent.moment_of_inertia * acceleration_angular
        self.agent.state.force[:, vmas.simulator.utils.X] = force_x
        self.agent.state.force[:, vmas.simulator.utils.Y] = force_y
        self.agent.state.torque = torque_yaw.unsqueeze(-1)

def __init__(self, world: vmas.simulator.core.World, I_xx: float=0.0081, I_yy: float=0.0081, I_zz: float=0.0142, integration: str='rk4'):
    super().__init__()
    assert integration in ('rk4', 'euler')
    self.integration = integration
    self.I_xx = I_xx
    self.I_yy = I_yy
    self.I_zz = I_zz
    self.world = world
    self.g = 9.81
    self.dt = world.dt
    self.reset()

def reset(self, index: Union[Tensor, int]=None):
    if index is None:
        self.drone_state = torch.zeros(self.world.batch_dim, 12, device=self.world.device)
    else:
        self.drone_state = TorchUtils.where_from_index(index, 0.0, self.drone_state)

def zero_grad(self):
    self.drone_state = self.drone_state.detach()

class KinematicBicycle(Dynamics):

    def __init__(self, world: vmas.simulator.core.World, width: float, l_f: float, l_r: float, max_steering_angle: float, integration: str='rk4'):
        super().__init__()
        assert integration in ('rk4', 'euler'), "Integration method must be 'euler' or 'rk4'."
        self.width = width
        self.l_f = l_f
        self.l_r = l_r
        self.max_steering_angle = max_steering_angle
        self.dt = world.dt
        self.integration = integration
        self.world = world

    def f(self, state, steering_command, v_command):
        theta = state[:, 2]
        beta = torch.atan2(torch.tan(steering_command) * self.l_r / (self.l_f + self.l_r), torch.tensor(1, device=self.world.device))
        dx = v_command * torch.cos(theta + beta)
        dy = v_command * torch.sin(theta + beta)
        dtheta = v_command / (self.l_f + self.l_r) * torch.cos(beta) * torch.tan(steering_command)
        return torch.stack((dx, dy, dtheta), dim=1)

    def euler(self, state, steering_command, v_command):
        return self.dt * self.f(state, steering_command, v_command)

    def runge_kutta(self, state, steering_command, v_command):
        k1 = self.f(state, steering_command, v_command)
        k2 = self.f(state + self.dt * k1 / 2, steering_command, v_command)
        k3 = self.f(state + self.dt * k2 / 2, steering_command, v_command)
        k4 = self.f(state + self.dt * k3, steering_command, v_command)
        return self.dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    @property
    def needed_action_size(self) -> int:
        return 2

    def process_action(self):
        v_command = self.agent.action.u[:, 0]
        steering_command = self.agent.action.u[:, 1]
        steering_command = torch.clamp(steering_command, -self.max_steering_angle, self.max_steering_angle)
        state = torch.cat((self.agent.state.pos, self.agent.state.rot), dim=1)
        v_cur_x = self.agent.state.vel[:, 0]
        v_cur_y = self.agent.state.vel[:, 1]
        v_cur_angular = self.agent.state.ang_vel[:, 0]
        if self.integration == 'euler':
            delta_state = self.euler(state, steering_command, v_command)
        else:
            delta_state = self.runge_kutta(state, steering_command, v_command)
        acceleration_x = (delta_state[:, 0] - v_cur_x * self.dt) / self.dt ** 2
        acceleration_y = (delta_state[:, 1] - v_cur_y * self.dt) / self.dt ** 2
        acceleration_angular = (delta_state[:, 2] - v_cur_angular * self.dt) / self.dt ** 2
        force_x = self.agent.mass * acceleration_x
        force_y = self.agent.mass * acceleration_y
        torque = self.agent.moment_of_inertia * acceleration_angular
        self.agent.state.force[:, vmas.simulator.utils.X] = force_x
        self.agent.state.force[:, vmas.simulator.utils.Y] = force_y
        self.agent.state.torque = torque.unsqueeze(-1)

def __init__(self, world: vmas.simulator.core.World, width: float, l_f: float, l_r: float, max_steering_angle: float, integration: str='rk4'):
    super().__init__()
    assert integration in ('rk4', 'euler'), "Integration method must be 'euler' or 'rk4'."
    self.width = width
    self.l_f = l_f
    self.l_r = l_r
    self.max_steering_angle = max_steering_angle
    self.dt = world.dt
    self.integration = integration
    self.world = world

class DiffDrive(Dynamics):

    def __init__(self, world: vmas.simulator.core.World, integration: str='rk4'):
        super().__init__()
        assert integration == 'rk4' or integration == 'euler'
        self.dt = world.dt
        self.integration = integration
        self.world = world

    def f(self, state, u_command, ang_vel_command):
        theta = state[:, 2]
        dx = u_command * torch.cos(theta)
        dy = u_command * torch.sin(theta)
        dtheta = ang_vel_command
        return torch.stack((dx, dy, dtheta), dim=-1)

    def euler(self, state, u_command, ang_vel_command):
        return self.dt * self.f(state, u_command, ang_vel_command)

    def runge_kutta(self, state, u_command, ang_vel_command):
        k1 = self.f(state, u_command, ang_vel_command)
        k2 = self.f(state + self.dt * k1 / 2, u_command, ang_vel_command)
        k3 = self.f(state + self.dt * k2 / 2, u_command, ang_vel_command)
        k4 = self.f(state + self.dt * k3, u_command, ang_vel_command)
        return self.dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    @property
    def needed_action_size(self) -> int:
        return 2

    def process_action(self):
        u_command = self.agent.action.u[:, 0]
        ang_vel_command = self.agent.action.u[:, 1]
        state = torch.cat((self.agent.state.pos, self.agent.state.rot), dim=1)
        v_cur_x = self.agent.state.vel[:, 0]
        v_cur_y = self.agent.state.vel[:, 1]
        v_cur_angular = self.agent.state.ang_vel[:, 0]
        if self.integration == 'euler':
            delta_state = self.euler(state, u_command, ang_vel_command)
        else:
            delta_state = self.runge_kutta(state, u_command, ang_vel_command)
        acceleration_x = (delta_state[:, 0] - v_cur_x * self.dt) / self.dt ** 2
        acceleration_y = (delta_state[:, 1] - v_cur_y * self.dt) / self.dt ** 2
        acceleration_angular = (delta_state[:, 2] - v_cur_angular * self.dt) / self.dt ** 2
        force_x = self.agent.mass * acceleration_x
        force_y = self.agent.mass * acceleration_y
        torque = self.agent.moment_of_inertia * acceleration_angular
        self.agent.state.force[:, vmas.simulator.utils.X] = force_x
        self.agent.state.force[:, vmas.simulator.utils.Y] = force_y
        self.agent.state.torque = torque.unsqueeze(-1)

def __init__(self, world: vmas.simulator.core.World, integration: str='rk4'):
    super().__init__()
    assert integration == 'rk4' or integration == 'euler'
    self.dt = world.dt
    self.integration = integration
    self.world = world

