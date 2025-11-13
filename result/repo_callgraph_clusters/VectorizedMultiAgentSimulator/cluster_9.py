# Cluster 9

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.random_start_angle = kwargs.pop('random_start_angle', True)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1)
        self.collision_reward = kwargs.pop('collision_reward', -10)
        self.max_speed_1 = kwargs.pop('max_speed_1', None)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.n_agents = 2
        self.wall_length = 2
        self.agent_spacing = 0.5
        self.agent_radius = 0.03
        self.ball_radius = self.agent_radius
        world = World(batch_dim, device, substeps=15, joint_force=900, collision_force=1500)
        agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), u_multiplier=1, mass=1)
        world.add_agent(agent)
        agent = Agent(name='agent_1', shape=Sphere(self.agent_radius), u_multiplier=1, mass=1, max_speed=self.max_speed_1)
        world.add_agent(agent)
        self.goal = Landmark(name='goal', shape=Sphere(radius=self.ball_radius), collide=False, color=Color.GREEN)
        world.add_landmark(self.goal)
        self.ball = Landmark(name='ball', shape=Sphere(radius=self.ball_radius), collide=True, movable=True)
        world.add_landmark(self.ball)
        self.joints = []
        for i in range(2):
            self.joints.append(Joint(world.agents[i], self.ball, anchor_a=(0, 0), anchor_b=(0, 0), dist=self.agent_spacing / 2, rotate_a=True, rotate_b=True, collidable=False, width=0, mass=1))
            world.add_joint(self.joints[i])
        self.build_path_line(world)
        self.pos_rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self.collision_rew = self.pos_rew.clone()
        self.collided = torch.full((world.batch_dim,), False, device=device)
        return world

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 + torch.pi / 3 if self.random_start_angle else 0, torch.pi / 2 - torch.pi / 3 if self.random_start_angle else 0)
        start_delta_x = self.agent_spacing / 2 * torch.cos(start_angle)
        min_x_start = -self.agent_radius
        max_x_start = self.agent_radius
        start_delta_y = self.agent_spacing / 2 * torch.sin(start_angle)
        min_y_start = -self.wall_length / 2 + 2 * self.agent_radius
        max_y_start = -self.agent_radius
        min_x_goal = min_x_start
        max_x_goal = max_x_start
        min_y_goal = -min_y_start
        max_y_goal = -max_x_start
        ball_position = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
        goal_pos = torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1)
        self.goal.set_pos(goal_pos, batch_index=env_index)
        self.ball.set_pos(ball_position, batch_index=env_index)
        for i, agent in enumerate(self.world.agents):
            agent.set_pos(ball_position + torch.cat([start_delta_x, start_delta_y], dim=1) * (-1 if i == 0 else 1), batch_index=env_index)
        for i, joint in enumerate(self.joints):
            joint.landmark.set_pos(ball_position + torch.cat([start_delta_x, start_delta_y], dim=1) / 2 * (-1 if i == 0 else 1), batch_index=env_index)
            joint.landmark.set_rot(start_angle + (torch.pi if i == 1 else 0), batch_index=env_index)
        self.spawn_path_line(env_index)
        if env_index is None:
            self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
            self.collided[:] = False
        else:
            self.pos_shaping[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor
            self.collided[env_index] = False

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.pos_rew[:] = 0
            self.collision_rew[:] = 0
            self.collided[:] = False
            dist_to_goal = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1)
            pos_shaping = dist_to_goal * self.pos_shaping_factor
            self.pos_rew += self.pos_shaping - pos_shaping
            self.pos_shaping = pos_shaping
            for collidable in self.world.agents + [self.ball]:
                for entity in self.walls + self.floors:
                    is_overlap = self.world.is_overlapping(collidable, entity)
                    self.collision_rew[is_overlap] += self.collision_reward
                    self.collided += is_overlap
            self.rew = self.pos_rew + self.collision_rew
        return self.rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos], dim=-1)

    def done(self):
        return (torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) <= 0.01) + self.collided

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'collision_rew': self.collision_rew}

    def build_path_line(self, world: World):
        self.walls = []
        for i in range(2):
            self.walls.append(Landmark(name=f'wall {i}', collide=True, shape=Line(length=self.wall_length), color=Color.BLACK))
            world.add_landmark(self.walls[i])
        self.floors = []
        for i in range(2):
            self.floors.append(Landmark(name=f'floor {i}', collide=True, shape=Line(length=self.agent_spacing / 2), color=Color.BLACK))
            world.add_landmark(self.floors[i])

    def spawn_path_line(self, env_index):
        for i, wall in enumerate(self.walls):
            wall.set_pos(torch.tensor([self.agent_spacing / 4 * (-1 if i == 0 else 1), 0.0], device=self.world.device), batch_index=env_index)
            wall.set_rot(torch.tensor(torch.pi / 2, device=self.world.device), batch_index=env_index)
        for i, floor in enumerate(self.floors):
            floor.set_pos(torch.tensor([0, self.wall_length / 2 * (-1 if i == 0 else 1)], device=self.world.device), batch_index=env_index)

def reset_world_at(self, env_index: int=None):
    start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 + torch.pi / 3 if self.random_start_angle else 0, torch.pi / 2 - torch.pi / 3 if self.random_start_angle else 0)
    start_delta_x = self.agent_spacing / 2 * torch.cos(start_angle)
    min_x_start = -self.agent_radius
    max_x_start = self.agent_radius
    start_delta_y = self.agent_spacing / 2 * torch.sin(start_angle)
    min_y_start = -self.wall_length / 2 + 2 * self.agent_radius
    max_y_start = -self.agent_radius
    min_x_goal = min_x_start
    max_x_goal = max_x_start
    min_y_goal = -min_y_start
    max_y_goal = -max_x_start
    ball_position = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
    goal_pos = torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1)
    self.goal.set_pos(goal_pos, batch_index=env_index)
    self.ball.set_pos(ball_position, batch_index=env_index)
    for i, agent in enumerate(self.world.agents):
        agent.set_pos(ball_position + torch.cat([start_delta_x, start_delta_y], dim=1) * (-1 if i == 0 else 1), batch_index=env_index)
    for i, joint in enumerate(self.joints):
        joint.landmark.set_pos(ball_position + torch.cat([start_delta_x, start_delta_y], dim=1) / 2 * (-1 if i == 0 else 1), batch_index=env_index)
        joint.landmark.set_rot(start_angle + (torch.pi if i == 1 else 0), batch_index=env_index)
    self.spawn_path_line(env_index)
    if env_index is None:
        self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
        self.collided[:] = False
    else:
        self.pos_shaping[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor
        self.collided[env_index] = False

def spawn_path_line(self, env_index):
    for i, wall in enumerate(self.walls):
        wall.set_pos(torch.tensor([self.agent_spacing / 4 * (-1 if i == 0 else 1), 0.0], device=self.world.device), batch_index=env_index)
        wall.set_rot(torch.tensor(torch.pi / 2, device=self.world.device), batch_index=env_index)
    for i, floor in enumerate(self.floors):
        floor.set_pos(torch.tensor([0, self.wall_length / 2 * (-1 if i == 0 else 1)], device=self.world.device), batch_index=env_index)

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

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_passages = kwargs.pop('n_passages', 1)
        self.fixed_passage = kwargs.pop('fixed_passage', False)
        self.random_start_angle = kwargs.pop('random_start_angle', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert 1 <= self.n_passages <= 20
        self.pos_shaping_factor = 1
        self.collision_reward = -0.06
        self.n_agents = 2
        self.agent_spacing = 0.5
        self.agent_radius = 0.03333
        self.ball_radius = self.agent_radius
        self.passage_width = 0.2
        self.passage_length = 0.103
        self.visualize_semidims = False
        world = World(batch_dim, device, x_semidim=1, y_semidim=1, drag=0, linear_friction=0.0)
        for i in range(2):
            agent = Agent(name=f'agent_{i}', shape=Sphere(self.agent_radius), u_multiplier=0.7, mass=2, drag=0.25)
            world.add_agent(agent)
        self.goal = Landmark(name='goal', shape=Sphere(radius=self.ball_radius), collide=False, color=Color.GREEN)
        world.add_landmark(self.goal)
        self.ball = Landmark(name='ball', shape=Sphere(radius=self.ball_radius), collide=True, movable=True, mass=1, color=Color.BLACK, linear_friction=0.02)
        world.add_landmark(self.ball)
        self.create_passage_map(world)
        self.pos_rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self.collision_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_start_angle else -torch.pi / 2, torch.pi / 2 if self.random_start_angle else -torch.pi / 2)
        start_delta_x = self.agent_spacing / 2 * torch.cos(start_angle)
        start_delta_x_abs = start_delta_x.abs()
        min_x_start = -self.world.x_semidim + (self.agent_radius + start_delta_x_abs)
        max_x_start = self.world.x_semidim - (self.agent_radius + start_delta_x_abs)
        start_delta_y = self.agent_spacing / 2 * torch.sin(start_angle)
        start_delta_y_abs = start_delta_y.abs()
        min_y_start = -self.world.y_semidim + (self.agent_radius + start_delta_y_abs)
        max_y_start = -2 * self.agent_radius - self.passage_width / 2 - start_delta_y_abs
        min_x_goal = -self.world.x_semidim + self.agent_radius
        max_x_goal = self.world.x_semidim - self.agent_radius
        min_y_goal = 2 * self.agent_radius + self.passage_width / 2
        max_y_goal = self.world.y_semidim - self.agent_radius
        ball_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
        self.ball.set_pos(ball_pos, batch_index=env_index)
        for i, agent in enumerate(self.world.agents):
            if i == 0:
                agent.set_pos(ball_pos - torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
            else:
                agent.set_pos(ball_pos + torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        self.goal.set_pos(torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1), batch_index=env_index)
        self.spawn_passage_map(env_index)
        if env_index is None:
            self.ball.pos_shaping_pre = torch.stack([torch.linalg.vector_norm(self.ball.state.pos - p.state.pos, dim=1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
            self.ball.pos_shaping_post = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
        else:
            self.ball.pos_shaping_pre[env_index] = torch.stack([torch.linalg.vector_norm(self.ball.state.pos[env_index] - p.state.pos[env_index]).unsqueeze(-1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
            self.ball.pos_shaping_post[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.pos_rew[:] = 0
            self.collision_rew[:] = 0
            ball_passed = self.ball.state.pos[:, Y] > 0
            ball_dist_to_closest_pass = torch.stack([torch.linalg.vector_norm(self.ball.state.pos - p.state.pos, dim=1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0]
            ball_shaping = ball_dist_to_closest_pass * self.pos_shaping_factor
            self.pos_rew[~ball_passed] += (self.ball.pos_shaping_pre - ball_shaping)[~ball_passed]
            self.ball.pos_shaping_pre = ball_shaping
            ball_dist_to_goal = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1)
            ball_shaping = ball_dist_to_goal * self.pos_shaping_factor
            self.pos_rew[ball_passed] += (self.ball.pos_shaping_post - ball_shaping)[ball_passed]
            self.ball.pos_shaping_post = ball_shaping
            for a in self.world.agents:
                for passage in self.passages:
                    if passage.collide:
                        self.collision_rew[self.world.is_overlapping(a, passage)] += self.collision_reward
            for p in self.passages:
                if p.collide:
                    self.collision_rew[self.world.is_overlapping(p, self.ball)] += self.collision_reward
            self.rew = self.pos_rew + self.collision_rew
        return self.rew

    def observation(self, agent: Agent):
        passage_obs = []
        for passage in self.passages:
            if not passage.collide:
                passage_obs.append(agent.state.pos - passage.state.pos)
        return torch.cat([agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos, agent.state.pos - self.ball.state.pos, *passage_obs], dim=-1)

    def done(self):
        return (torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) <= 0.01) + (-self.world.x_semidim + self.ball_radius >= self.ball.state.pos[:, X]) + (self.ball.state.pos[:, X] >= self.world.x_semidim - self.ball_radius) + (-self.world.y_semidim + self.ball_radius >= self.ball.state.pos[:, Y]) + (self.ball.state.pos[:, Y] >= self.world.y_semidim - self.ball_radius)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'collision_rew': self.collision_rew}

    def create_passage_map(self, world: World):
        self.passages = []
        n_boxes = int((2 * world.x_semidim + 2 * self.agent_radius) // self.passage_length)

        def removed(i):
            return n_boxes // 2 - self.n_passages / 2 <= i < n_boxes // 2 + self.n_passages / 2
        for i in range(n_boxes):
            passage = Landmark(name=f'passage {i}', collide=not removed(i), movable=False, shape=Box(length=self.passage_length, width=self.passage_width), color=Color.RED, collision_filter=lambda e: not isinstance(e.shape, Box))
            self.passages.append(passage)
            world.add_landmark(passage)

    def spawn_passage_map(self, env_index):
        if not self.fixed_passage:
            order = torch.randperm(len(self.passages)).tolist()
            self.passages_to_place = [self.passages[i] for i in order]
        else:
            self.passages_to_place = self.passages
        for i, passage in enumerate(self.passages_to_place):
            if not passage.collide:
                passage.is_rendering[:] = False
            passage.neighbour = False
            try:
                passage.neighbour += not self.passages_to_place[i - 1].collide
            except IndexError:
                pass
            try:
                passage.neighbour += not self.passages_to_place[i + 1].collide
            except IndexError:
                pass
            pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2 + self.passage_length * i, 0.0], dtype=torch.float32, device=self.world.device)
            passage.neighbour *= passage.collide
            passage.set_pos(pos, batch_index=env_index)

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        for i in range(4):
            geom = Line(length=2 + self.agent_radius * 2).get_geometry()
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(0.0 if i % 2 else self.world.x_semidim + self.agent_radius if i == 0 else -self.world.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.world.x_semidim + self.agent_radius if i == 1 else -self.world.x_semidim - self.agent_radius)
            xform.set_rotation(torch.pi / 2 if not i % 2 else 0.0)
            color = Color.BLACK.value
            if isinstance(color, torch.Tensor) and len(color.shape) > 1:
                color = color[env_index]
            geom.set_color(*color)
            geoms.append(geom)
        return geoms

def reset_world_at(self, env_index: int=None):
    start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_start_angle else -torch.pi / 2, torch.pi / 2 if self.random_start_angle else -torch.pi / 2)
    start_delta_x = self.agent_spacing / 2 * torch.cos(start_angle)
    start_delta_x_abs = start_delta_x.abs()
    min_x_start = -self.world.x_semidim + (self.agent_radius + start_delta_x_abs)
    max_x_start = self.world.x_semidim - (self.agent_radius + start_delta_x_abs)
    start_delta_y = self.agent_spacing / 2 * torch.sin(start_angle)
    start_delta_y_abs = start_delta_y.abs()
    min_y_start = -self.world.y_semidim + (self.agent_radius + start_delta_y_abs)
    max_y_start = -2 * self.agent_radius - self.passage_width / 2 - start_delta_y_abs
    min_x_goal = -self.world.x_semidim + self.agent_radius
    max_x_goal = self.world.x_semidim - self.agent_radius
    min_y_goal = 2 * self.agent_radius + self.passage_width / 2
    max_y_goal = self.world.y_semidim - self.agent_radius
    ball_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
    self.ball.set_pos(ball_pos, batch_index=env_index)
    for i, agent in enumerate(self.world.agents):
        if i == 0:
            agent.set_pos(ball_pos - torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        else:
            agent.set_pos(ball_pos + torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
    self.goal.set_pos(torch.cat([(min_x_goal - max_x_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_goal, (min_y_goal - max_y_goal) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_goal], dim=1), batch_index=env_index)
    self.spawn_passage_map(env_index)
    if env_index is None:
        self.ball.pos_shaping_pre = torch.stack([torch.linalg.vector_norm(self.ball.state.pos - p.state.pos, dim=1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
        self.ball.pos_shaping_post = torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) * self.pos_shaping_factor
    else:
        self.ball.pos_shaping_pre[env_index] = torch.stack([torch.linalg.vector_norm(self.ball.state.pos[env_index] - p.state.pos[env_index]).unsqueeze(-1) for p in self.passages if not p.collide], dim=1).min(dim=1)[0] * self.pos_shaping_factor
        self.ball.pos_shaping_post[env_index] = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.goal.state.pos[env_index]) * self.pos_shaping_factor

def spawn_passage_map(self, env_index):
    if not self.fixed_passage:
        order = torch.randperm(len(self.passages)).tolist()
        self.passages_to_place = [self.passages[i] for i in order]
    else:
        self.passages_to_place = self.passages
    for i, passage in enumerate(self.passages_to_place):
        if not passage.collide:
            passage.is_rendering[:] = False
        passage.neighbour = False
        try:
            passage.neighbour += not self.passages_to_place[i - 1].collide
        except IndexError:
            pass
        try:
            passage.neighbour += not self.passages_to_place[i + 1].collide
        except IndexError:
            pass
        pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2 + self.passage_length * i, 0.0], dtype=torch.float32, device=self.world.device)
        passage.neighbour *= passage.collide
        passage.set_pos(pos, batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 0)
        self.speed_shaping_factor = kwargs.pop('speed_shaping_factor', 1)
        self.dist_shaping_factor = kwargs.pop('dist_shaping_factor', 0)
        self.joints = kwargs.pop('joints', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.n_agents = 2
        self.desired_speed = 1
        self.desired_radius = 0.5
        self.agent_spacing = 0.4
        self.agent_radius = 0.03
        self.ball_radius = 2 * self.agent_radius
        world = World(batch_dim, device, substeps=15 if self.joints else 5, joint_force=900 if self.joints else JOINT_FORCE, collision_force=1500 if self.joints else 400, drag=0)
        agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), drag=0.25)
        world.add_agent(agent)
        agent = Agent(name='agent_1', shape=Sphere(self.agent_radius), drag=0.25)
        world.add_agent(agent)
        self.ball = Landmark(name='ball', shape=Sphere(radius=self.ball_radius), collide=True, movable=True, linear_friction=0.04)
        world.add_landmark(self.ball)
        if self.joints:
            self.joints = []
            for i in range(self.n_agents):
                self.joints.append(Joint(world.agents[i], self.ball, anchor_a=(0, 0), anchor_b=(0, 0), dist=self.agent_spacing / 2, rotate_a=True, rotate_b=True, collidable=False, width=0, mass=1))
                world.add_joint(self.joints[i])
        self.pos_rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self.speed_rew = self.pos_rew.clone()
        self.dist_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        ball_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.desired_radius, self.desired_radius)
        self.ball.set_pos(ball_pos, batch_index=env_index)
        order = torch.randperm(self.n_agents).tolist()
        agents = [self.world.agents[i] for i in order]
        for i, agent in enumerate(agents):
            agent_pos = ball_pos.clone()
            agent_pos[:, X] += self.agent_spacing / 2 * (-1 if i == 0 else 1)
            agent.set_pos(agent_pos, batch_index=env_index)
        if env_index is None:
            self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos - self.get_closest_point_circle(self.ball.state.pos), dim=1) ** 0.5 * self.pos_shaping_factor
            self.speed_shaping = (self.desired_speed - torch.linalg.vector_norm(self.ball.state.vel, dim=1)).abs() * self.speed_shaping_factor
            self.dist_shaping = torch.stack([torch.linalg.vector_norm(a.state.pos - self.ball.state.pos, dim=1) for a in self.world.agents], dim=1).sum(dim=1) * self.dist_shaping_factor
        else:
            self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.get_closest_point_circle(self.ball.state.pos)[env_index]) ** 0.5 * self.pos_shaping_factor
            self.speed_shaping[env_index] = (self.desired_speed - torch.linalg.vector_norm(self.ball.state.vel[env_index])).abs() * self.speed_shaping_factor
            self.dist_shaping[env_index] = torch.stack([torch.linalg.vector_norm(a.state.pos[env_index] - self.ball.state.pos[env_index]).unsqueeze(-1) for a in self.world.agents], dim=1).sum(dim=1) * self.dist_shaping_factor

    def reward(self, agent: Agent):
        pos_shaping = torch.linalg.vector_norm(self.ball.state.pos - self.get_closest_point_circle(self.ball.state.pos), dim=1) ** 0.5 * self.pos_shaping_factor
        self.pos_rew = self.pos_shaping - pos_shaping
        self.pos_shaping = pos_shaping
        speed = torch.linalg.vector_norm(self.ball.state.vel, dim=1)
        speed_shaping = (self.desired_speed - speed).abs() * self.speed_shaping_factor
        self.speed_rew = self.speed_shaping - speed_shaping
        self.speed_shaping = speed_shaping
        dist_shaping = torch.stack([torch.linalg.vector_norm(a.state.pos - self.ball.state.pos, dim=1) for a in self.world.agents], dim=1).sum(dim=1) * self.dist_shaping_factor
        self.dist_rew = self.dist_shaping - dist_shaping
        self.dist_shaping = dist_shaping
        return self.pos_rew + self.speed_rew + self.dist_rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, agent.state.pos - self.ball.state.pos, agent.state.pos], dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'speed_rew': self.speed_rew, 'dist_rew': self.dist_rew}

    def get_closest_point_circle(self, pos: Tensor):
        pos_norm = torch.linalg.vector_norm(pos, dim=1)
        agent_pos_normalized = pos / pos_norm.unsqueeze(-1)
        agent_pos_normalized *= self.desired_radius
        return torch.nan_to_num(agent_pos_normalized)

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        color = Color.BLACK.value
        circle = rendering.make_circle(self.desired_radius, filled=False)
        xform = rendering.Transform()
        circle.add_attr(xform)
        xform.set_translation(0, 0)
        circle.set_color(*color)
        geoms.append(circle)
        return geoms

def reset_world_at(self, env_index: int=None):
    ball_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.desired_radius, self.desired_radius)
    self.ball.set_pos(ball_pos, batch_index=env_index)
    order = torch.randperm(self.n_agents).tolist()
    agents = [self.world.agents[i] for i in order]
    for i, agent in enumerate(agents):
        agent_pos = ball_pos.clone()
        agent_pos[:, X] += self.agent_spacing / 2 * (-1 if i == 0 else 1)
        agent.set_pos(agent_pos, batch_index=env_index)
    if env_index is None:
        self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos - self.get_closest_point_circle(self.ball.state.pos), dim=1) ** 0.5 * self.pos_shaping_factor
        self.speed_shaping = (self.desired_speed - torch.linalg.vector_norm(self.ball.state.vel, dim=1)).abs() * self.speed_shaping_factor
        self.dist_shaping = torch.stack([torch.linalg.vector_norm(a.state.pos - self.ball.state.pos, dim=1) for a in self.world.agents], dim=1).sum(dim=1) * self.dist_shaping_factor
    else:
        self.pos_shaping = torch.linalg.vector_norm(self.ball.state.pos[env_index] - self.get_closest_point_circle(self.ball.state.pos)[env_index]) ** 0.5 * self.pos_shaping_factor
        self.speed_shaping[env_index] = (self.desired_speed - torch.linalg.vector_norm(self.ball.state.vel[env_index])).abs() * self.speed_shaping_factor
        self.dist_shaping[env_index] = torch.stack([torch.linalg.vector_norm(a.state.pos[env_index] - self.ball.state.pos[env_index]).unsqueeze(-1) for a in self.world.agents], dim=1).sum(dim=1) * self.dist_shaping_factor

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.u_range = kwargs.pop('u_range', 0.5)
        self.a_range = kwargs.pop('a_range', 1)
        self.obs_noise = kwargs.pop('obs_noise', 0)
        self.box_agents = kwargs.pop('box_agents', False)
        self.linear_friction = kwargs.pop('linear_friction', 0.1)
        self.min_input_norm = kwargs.pop('min_input_norm', 0.08)
        self.comms_range = kwargs.pop('comms_range', 5)
        self.shared_rew = kwargs.pop('shared_rew', True)
        self.n_agents = kwargs.pop('n_agents', 4)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1)
        self.final_reward = kwargs.pop('final_reward', 0.01)
        self.agent_collision_penalty = kwargs.pop('agent_collision_penalty', -0.1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.viewer_zoom = 1.7
        controller_params = [2, 6, 0.002]
        self.n_agents = 4
        self.f_range = self.a_range + self.linear_friction
        world = World(batch_dim, device, drag=0, dt=0.1, linear_friction=self.linear_friction, substeps=16 if self.box_agents else 5, collision_force=10000 if self.box_agents else 500)
        self.agent_radius = 0.16
        self.agent_box_length = 0.32
        self.agent_box_width = 0.24
        self.min_collision_distance = 0.005
        self.colors = [Color.GREEN, Color.BLUE, Color.RED, Color.GRAY]
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', rotatable=False, linear_friction=self.linear_friction, shape=Sphere(radius=self.agent_radius) if not self.box_agents else Box(length=self.agent_box_length, width=self.agent_box_width), u_range=self.u_range, f_range=self.f_range, render_action=True, color=self.colors[i])
            agent.controller = VelocityController(agent, world, controller_params, 'standard')
            goal = Landmark(name=f'goal {i}', collide=False, shape=Sphere(radius=self.agent_radius / 2), color=self.colors[i])
            agent.goal = goal
            agent.pos_rew = torch.zeros(batch_dim, device=device)
            agent.agent_collision_rew = agent.pos_rew.clone()
            world.add_agent(agent)
            world.add_landmark(goal)
        self.spawn_map(world)
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.final_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        for i, agent in enumerate(self.world.agents):
            agent.controller.reset(env_index)
            next_i = (i + 1) % self.n_agents
            if i in [0, 2]:
                agent.set_pos(torch.tensor([(self.scenario_length / 2 - self.agent_dist_from_wall) * (-1 if i == 0 else 1), 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                self.world.agents[next_i].goal.set_pos(torch.tensor([(self.scenario_length / 2 - self.goal_dist_from_wall) * (-1 if i == 0 else 1), 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            else:
                agent.set_pos(torch.tensor([0.0, (self.scenario_length / 2 - self.agent_dist_from_wall) * (1 if i == 1 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                self.world.agents[next_i].goal.set_pos(torch.tensor([0.0, (self.scenario_length / 2 - self.goal_dist_from_wall) * (1 if i == 1 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        for agent in self.world.agents:
            if env_index is None:
                agent.shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.pos_shaping_factor
            else:
                agent.shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.pos_shaping_factor
        self.reset_map(env_index)
        if env_index is None:
            self.reached_goal = torch.full((self.world.batch_dim,), False, device=self.world.device)
        else:
            self.reached_goal[env_index] = False

    def process_action(self, agent: Agent):
        agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, self.u_range)
        action_norm = torch.linalg.vector_norm(agent.action.u, dim=1)
        agent.action.u[action_norm < self.min_input_norm] = 0
        agent.vel_action = agent.action.u.clone()
        vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
        agent.controller.reset(vel_is_zero)
        agent.controller.process_force()

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.pos_rew[:] = 0
            self.final_rew[:] = 0
            for a in self.world.agents:
                a.distance_to_goal = torch.linalg.vector_norm(a.state.pos - a.goal.state.pos, dim=-1)
                a.on_goal = a.distance_to_goal < a.goal.shape.radius
                pos_shaping = a.distance_to_goal * self.pos_shaping_factor
                a.pos_rew = a.shaping - pos_shaping if self.pos_shaping_factor != 0 else -a.distance_to_goal * 0.0001
                a.shaping = pos_shaping
                self.pos_rew += a.pos_rew
            self.all_goal_reached = torch.all(torch.stack([a.on_goal for a in self.world.agents], dim=-1), dim=-1)
            self.final_rew[self.all_goal_reached] = self.final_reward
            self.reached_goal += self.all_goal_reached
        agent.agent_collision_rew[:] = 0
        for a in self.world.agents:
            if a != agent:
                agent.agent_collision_rew[self.world.get_distance(agent, a) <= self.min_collision_distance] += self.agent_collision_penalty
        return (self.pos_rew if self.shared_rew else agent.pos_rew) + agent.agent_collision_rew + self.final_rew

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel, agent.state.pos - agent.goal.state.pos, torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=-1).unsqueeze(-1)]
        if self.obs_noise > 0:
            for i, obs in enumerate(observations):
                noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
                observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def info(self, agent: Agent):
        return {'pos_rew': self.pos_rew if self.shared_rew else agent.pos_rew, 'final_rew': self.final_rew, 'agent_collision_rew': agent.agent_collision_rew}

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms: List[Geom] = []
        for i, agent1 in enumerate(self.world.agents):
            for j, agent2 in enumerate(self.world.agents):
                if j <= i:
                    continue
                agent_dist = torch.linalg.vector_norm(agent1.state.pos - agent2.state.pos, dim=-1)
                if agent_dist[env_index] <= self.comms_range:
                    color = Color.BLACK.value
                    line = rendering.Line(agent1.state.pos[env_index], agent2.state.pos[env_index], width=1)
                    xform = rendering.Transform()
                    line.add_attr(xform)
                    line.set_color(*color)
                    geoms.append(line)
        return geoms

    def spawn_map(self, world: World):
        self.scenario_length = 5
        self.scenario_width = 0.4
        self.long_wall_length = self.scenario_length / 2 - self.scenario_width / 2
        self.short_wall_length = self.scenario_width
        self.goal_dist_from_wall = self.agent_radius + 0.05
        self.agent_dist_from_wall = 0.5
        self.long_walls = []
        for i in range(8):
            landmark = Landmark(name=f'wall {i}', collide=True, shape=Line(length=self.long_wall_length), color=Color.BLACK)
            self.long_walls.append(landmark)
            world.add_landmark(landmark)
        self.short_walls = []
        for i in range(4):
            landmark = Landmark(name=f'short wall {i}', collide=True, shape=Line(length=self.short_wall_length), color=Color.BLACK)
            self.short_walls.append(landmark)
            world.add_landmark(landmark)

    def reset_map(self, env_index):
        for i, landmark in enumerate(self.short_walls):
            if i < 2:
                landmark.set_pos(torch.tensor([-self.scenario_length / 2 if i % 2 == 0 else self.scenario_length / 2, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            else:
                landmark.set_pos(torch.tensor([0.0, -self.scenario_length / 2 if i % 2 == 0 else self.scenario_length / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        long_wall_pos = self.long_wall_length / 2 - self.scenario_length / 2
        for i, landmark in enumerate(self.long_walls):
            if i < 4:
                landmark.set_pos(torch.tensor([long_wall_pos * (1 if i < 2 else -1), self.scenario_width / 2 * (-1 if i % 2 == 0 else 1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            else:
                landmark.set_pos(torch.tensor([self.scenario_width / 2 * (-1 if i % 2 == 0 else 1), long_wall_pos * (1 if i < 6 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
                landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)

def reset_world_at(self, env_index: int=None):
    for i, agent in enumerate(self.world.agents):
        agent.controller.reset(env_index)
        next_i = (i + 1) % self.n_agents
        if i in [0, 2]:
            agent.set_pos(torch.tensor([(self.scenario_length / 2 - self.agent_dist_from_wall) * (-1 if i == 0 else 1), 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            self.world.agents[next_i].goal.set_pos(torch.tensor([(self.scenario_length / 2 - self.goal_dist_from_wall) * (-1 if i == 0 else 1), 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        else:
            agent.set_pos(torch.tensor([0.0, (self.scenario_length / 2 - self.agent_dist_from_wall) * (1 if i == 1 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            self.world.agents[next_i].goal.set_pos(torch.tensor([0.0, (self.scenario_length / 2 - self.goal_dist_from_wall) * (1 if i == 1 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
    for agent in self.world.agents:
        if env_index is None:
            agent.shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.pos_shaping_factor
        else:
            agent.shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.pos_shaping_factor
    self.reset_map(env_index)
    if env_index is None:
        self.reached_goal = torch.full((self.world.batch_dim,), False, device=self.world.device)
    else:
        self.reached_goal[env_index] = False

def observation(self, agent: Agent):
    observations = [agent.state.pos, agent.state.vel, agent.state.pos - agent.goal.state.pos, torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=-1).unsqueeze(-1)]
    if self.obs_noise > 0:
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs + noise
    return torch.cat(observations, dim=-1)

def reset_map(self, env_index):
    for i, landmark in enumerate(self.short_walls):
        if i < 2:
            landmark.set_pos(torch.tensor([-self.scenario_length / 2 if i % 2 == 0 else self.scenario_length / 2, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        else:
            landmark.set_pos(torch.tensor([0.0, -self.scenario_length / 2 if i % 2 == 0 else self.scenario_length / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)
    long_wall_pos = self.long_wall_length / 2 - self.scenario_length / 2
    for i, landmark in enumerate(self.long_walls):
        if i < 4:
            landmark.set_pos(torch.tensor([long_wall_pos * (1 if i < 2 else -1), self.scenario_width / 2 * (-1 if i % 2 == 0 else 1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        else:
            landmark.set_pos(torch.tensor([self.scenario_width / 2 * (-1 if i % 2 == 0 else 1), long_wall_pos * (1 if i < 6 else -1)], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            landmark.set_rot(torch.tensor([torch.pi / 2], dtype=torch.float32, device=self.world.device), batch_index=env_index)

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

def is_passage(i):
    is_pass = big_passage_start_index == i
    is_pass += big_passage_start_index == i - 1
    is_pass += big_passage_start_index + small_left_or_right == i
    if self.n_passages == 4:
        is_pass += big_passage_start_index + small_left_or_right == i - torch.sign(small_left_or_right)
    return is_pass

def spawn_walls(self, env_index):
    for i, wall in enumerate(self.walls):
        wall.set_pos(torch.tensor([0.0 if i % 2 else self.world.x_semidim + self.agent_radius if i == 0 else -self.world.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.world.y_semidim + self.agent_radius if i == 1 else -self.world.y_semidim - self.agent_radius], device=self.world.device), batch_index=env_index)
        wall.set_rot(torch.tensor([torch.pi / 2 if not i % 2 else 0.0], device=self.world.device), batch_index=env_index)

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

def get_short_term_reference_path(polyline: torch.Tensor, index_closest_point: torch.Tensor, n_points_to_return: int, device=None, is_polyline_a_loop: torch.Tensor=False, n_points_long_term: torch.Tensor=None, sample_interval: int=2, n_points_shift: int=1):
    """
    Args:
        polyline:                   [batch_size, num_points, 2] or [num_points, 2]. In the case of the latter, batch_dim is deemed as 1.
        index_closest_point:        [batch_size, 1] or [1] or []. In the case of the latter, batch_dim is deemed as 1.
        n_points_to_return:         [1] or []. In the case of the latter, batch_dim is deemed as 1.
        is_polyline_a_loop:         [batch_size] or []. In the case of the latter, batch_dim is deemed as 1.
        n_points_long_term:         [batch_size] or []. In the case of the latter, batch_dim is deemed as 1.
        sample_interval:            Sample interval to match specific purposes;
                                    set to 2 when using this function to get the short-term reference path;
                                    set to 1 when using this function to get the nearing boundary points.
        n_points_shift:             Number of points to be shifted to match specific purposes;
                                    set to 1 when using this function to get the short-term reference path to "force" the first point of the short-term reference path being in front of the agent;
                                    set to -2 when using this function to get the nearing boundary points to consider the points behind the agent.
    """
    if polyline.ndim == 2:
        polyline = polyline.unsqueeze(0)
    if index_closest_point.ndim == 1:
        index_closest_point = index_closest_point.unsqueeze(1)
    elif index_closest_point.ndim == 0:
        index_closest_point = index_closest_point.unsqueeze(0).unsqueeze(1)
    if is_polyline_a_loop.ndim == 0:
        is_polyline_a_loop = is_polyline_a_loop.unsqueeze(0)
    if n_points_long_term.ndim == 0:
        n_points_long_term = n_points_long_term.unsqueeze(0)
    if device is None:
        device = torch.device('cpu')
    batch_size = index_closest_point.shape[0]
    future_points_idx = torch.arange(n_points_to_return, device=device) * sample_interval + index_closest_point + n_points_shift
    if n_points_long_term is None:
        n_points_long_term = polyline.shape[-2]
    for env_i in range(batch_size):
        n_long_term_point = n_points_long_term[env_i]
        if is_polyline_a_loop[env_i]:
            future_points_idx[env_i] = torch.where(future_points_idx[env_i] >= n_long_term_point - 1, (future_points_idx[env_i] + 1) % n_long_term_point, future_points_idx[env_i])
    short_term_path = polyline[torch.arange(batch_size, device=device, dtype=torch.int).unsqueeze(1), future_points_idx]
    return (short_term_path, future_points_idx)

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

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_agents = kwargs.pop('n_agents', 3)
        self.shared_rew = kwargs.pop('shared_rew', True)
        self.comms_range = kwargs.pop('comms_range', 0.0)
        self.lidar_range = kwargs.pop('lidar_range', 0.2)
        self.agent_radius = kwargs.pop('agent_radius', 0.025)
        self.xdim = kwargs.pop('xdim', 1)
        self.ydim = kwargs.pop('ydim', 1)
        self.grid_spacing = kwargs.pop('grid_spacing', 0.05)
        self.n_gaussians = kwargs.pop('n_gaussians', 3)
        self.cov = kwargs.pop('cov', 0.05)
        self.collisions = kwargs.pop('collisions', True)
        self.spawn_same_pos = kwargs.pop('spawn_same_pos', False)
        self.norm = kwargs.pop('norm', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert not (self.spawn_same_pos and self.collisions)
        assert self.xdim / self.grid_spacing % 1 == 0 and self.ydim / self.grid_spacing % 1 == 0
        self.covs = [self.cov] * self.n_gaussians if isinstance(self.cov, float) else self.cov
        assert len(self.covs) == self.n_gaussians
        self.plot_grid = False
        self.visualize_semidims = False
        self.n_x_cells = int(2 * self.xdim / self.grid_spacing)
        self.n_y_cells = int(2 * self.ydim / self.grid_spacing)
        self.max_pdf = torch.zeros((batch_dim,), device=device, dtype=torch.float32)
        self.alpha_plot: float = 0.5
        self.agent_xspawn_range = 0 if self.spawn_same_pos else self.xdim
        self.agent_yspawn_range = 0 if self.spawn_same_pos else self.ydim
        self.x_semidim = self.xdim - self.agent_radius
        self.y_semidim = self.ydim - self.agent_radius
        world = World(batch_dim, device, x_semidim=self.x_semidim, y_semidim=self.y_semidim)
        entity_filter_agents: Callable[[Entity], bool] = lambda e: isinstance(e, Agent)
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', render_action=True, collide=self.collisions, shape=Sphere(radius=self.agent_radius), sensors=[Lidar(world, angle_start=0.05, angle_end=2 * torch.pi + 0.05, n_rays=12, max_range=self.lidar_range, entity_filter=entity_filter_agents)] if self.collisions else None)
            world.add_agent(agent)
        self.sampled = torch.zeros((batch_dim, self.n_x_cells, self.n_y_cells), device=device, dtype=torch.bool)
        self.locs = [torch.zeros((batch_dim, world.dim_p), device=device, dtype=torch.float32) for _ in range(self.n_gaussians)]
        self.cov_matrices = [torch.tensor([[cov, 0], [0, cov]], dtype=torch.float32, device=device).expand(batch_dim, world.dim_p, world.dim_p) for cov in self.covs]
        return world

    def reset_world_at(self, env_index: int=None):
        for i in range(len(self.locs)):
            x = torch.zeros((1,) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.xdim, self.xdim)
            y = torch.zeros((1,) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.ydim, self.ydim)
            new_loc = torch.cat([x, y], dim=-1)
            if env_index is None:
                self.locs[i] = new_loc
            else:
                self.locs[i][env_index] = new_loc
        self.gaussians = [MultivariateNormal(loc=loc, covariance_matrix=cov_matrix) for loc, cov_matrix in zip(self.locs, self.cov_matrices)]
        if env_index is None:
            self.max_pdf[:] = 0
            self.sampled[:] = False
        else:
            self.max_pdf[env_index] = 0
            self.sampled[env_index] = False
        self.nomrlize_pdf(env_index=env_index)
        for agent in self.world.agents:
            agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.agent_xspawn_range, self.agent_xspawn_range), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.agent_yspawn_range, self.agent_yspawn_range)], dim=-1), batch_index=env_index)
            agent.sample = self.sample(agent.state.pos, norm=self.norm)

    def sample(self, pos, update_sampled_flag: bool=False, norm: bool=True):
        out_of_bounds = (pos[:, X] < -self.xdim) + (pos[:, X] > self.xdim) + (pos[:, Y] < -self.ydim) + (pos[:, Y] > self.ydim)
        pos[:, X].clamp_(-self.world.x_semidim, self.world.x_semidim)
        pos[:, Y].clamp_(-self.world.y_semidim, self.world.y_semidim)
        index = pos / self.grid_spacing
        index[:, X] += self.n_x_cells / 2
        index[:, Y] += self.n_y_cells / 2
        index = index.to(torch.long)
        v = torch.stack([gaussian.log_prob(pos).exp() for gaussian in self.gaussians], dim=-1).sum(-1)
        if norm:
            v = v / self.max_pdf
        sampled = self.sampled[torch.arange(self.world.batch_dim), index[:, 0], index[:, 1]]
        v[sampled + out_of_bounds] = 0
        if update_sampled_flag:
            self.sampled[torch.arange(self.world.batch_dim), index[:, 0], index[:, 1]] = True
        return v

    def sample_single_env(self, pos, env_index, norm: bool=True):
        pos = pos.view(-1, self.world.dim_p)
        out_of_bounds = (pos[:, X] < -self.xdim) + (pos[:, X] > self.xdim) + (pos[:, Y] < -self.ydim) + (pos[:, Y] > self.ydim)
        pos[:, X].clamp_(-self.x_semidim, self.x_semidim)
        pos[:, Y].clamp_(-self.y_semidim, self.y_semidim)
        index = pos / self.grid_spacing
        index[:, X] += self.n_x_cells / 2
        index[:, Y] += self.n_y_cells / 2
        index = index.to(torch.long)
        pos = pos.unsqueeze(1).expand(pos.shape[0], self.world.batch_dim, 2)
        v = torch.stack([gaussian.log_prob(pos).exp() for gaussian in self.gaussians], dim=-1).sum(-1)[:, env_index]
        if norm:
            v = v / self.max_pdf[env_index]
        sampled = self.sampled[env_index, index[:, 0], index[:, 1]]
        v[sampled + out_of_bounds] = 0
        return v

    def nomrlize_pdf(self, env_index: int=None):
        xpoints = torch.arange(-self.xdim, self.xdim, self.grid_spacing, device=self.world.device)
        ypoints = torch.arange(-self.ydim, self.ydim, self.grid_spacing, device=self.world.device)
        if env_index is not None:
            ygrid, xgrid = torch.meshgrid(ypoints, xpoints, indexing='ij')
            pos = torch.stack((xgrid, ygrid), dim=-1).reshape(-1, 2)
            sample = self.sample_single_env(pos, env_index, norm=False)
            self.max_pdf[env_index] = sample.max()
        else:
            for x in xpoints:
                for y in ypoints:
                    pos = torch.tensor([x, y], device=self.world.device, dtype=torch.float32).repeat(self.world.batch_dim, 1)
                    sample = self.sample(pos, norm=False)
                    self.max_pdf = torch.maximum(self.max_pdf, sample)

    def reward(self, agent: Agent) -> Tensor:
        is_first = self.world.agents.index(agent) == 0
        if is_first:
            for a in self.world.agents:
                a.sample = self.sample(a.state.pos, update_sampled_flag=True, norm=self.norm)
            self.sampling_rew = torch.stack([a.sample for a in self.world.agents], dim=-1).sum(-1)
        return self.sampling_rew if self.shared_rew else agent.sample

    def observation(self, agent: Agent) -> Tensor:
        observations = [agent.state.pos, agent.state.vel, agent.sensors[0].measure()]
        for delta in [[self.grid_spacing, 0], [-self.grid_spacing, 0], [0, self.grid_spacing], [0, -self.grid_spacing], [-self.grid_spacing, -self.grid_spacing], [self.grid_spacing, -self.grid_spacing], [-self.grid_spacing, self.grid_spacing], [self.grid_spacing, self.grid_spacing]]:
            pos = agent.state.pos + torch.tensor(delta, device=self.world.device, dtype=torch.float32)
            sample = self.sample(pos, update_sampled_flag=False).unsqueeze(-1)
            observations.append(sample)
        return torch.cat(observations, dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'agent_sample': agent.sample}

    def density_for_plot(self, env_index):

        def f(x):
            sample = self.sample_single_env(torch.tensor(x, dtype=torch.float32, device=self.world.device), env_index=env_index)
            return sample
        return f

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        from vmas.simulator.rendering import render_function_util
        geoms = [render_function_util(f=self.density_for_plot(env_index=env_index), plot_range=(self.xdim, self.ydim), cmap_alpha=self.alpha_plot)]
        for i, agent1 in enumerate(self.world.agents):
            for j, agent2 in enumerate(self.world.agents):
                if j <= i:
                    continue
                agent_dist = torch.linalg.vector_norm(agent1.state.pos - agent2.state.pos, dim=-1)
                if agent_dist[env_index] <= self.comms_range:
                    color = Color.BLACK.value
                    line = rendering.Line(agent1.state.pos[env_index], agent2.state.pos[env_index], width=1)
                    xform = rendering.Transform()
                    line.add_attr(xform)
                    line.set_color(*color)
                    geoms.append(line)
        for i in range(4):
            geom = Line(length=2 * ((self.ydim if i % 2 == 0 else self.xdim) - self.agent_radius) + self.agent_radius * 2).get_geometry()
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(0.0 if i % 2 else self.x_semidim + self.agent_radius if i == 0 else -self.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.y_semidim + self.agent_radius if i == 1 else -self.y_semidim - self.agent_radius)
            xform.set_rotation(torch.pi / 2 if not i % 2 else 0.0)
            color = Color.BLACK.value
            if isinstance(color, torch.Tensor) and len(color.shape) > 1:
                color = color[env_index]
            geom.set_color(*color)
            geoms.append(geom)
        return geoms

def reset_world_at(self, env_index: int=None):
    for i in range(len(self.locs)):
        x = torch.zeros((1,) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.xdim, self.xdim)
        y = torch.zeros((1,) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.ydim, self.ydim)
        new_loc = torch.cat([x, y], dim=-1)
        if env_index is None:
            self.locs[i] = new_loc
        else:
            self.locs[i][env_index] = new_loc
    self.gaussians = [MultivariateNormal(loc=loc, covariance_matrix=cov_matrix) for loc, cov_matrix in zip(self.locs, self.cov_matrices)]
    if env_index is None:
        self.max_pdf[:] = 0
        self.sampled[:] = False
    else:
        self.max_pdf[env_index] = 0
        self.sampled[env_index] = False
    self.nomrlize_pdf(env_index=env_index)
    for agent in self.world.agents:
        agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.agent_xspawn_range, self.agent_xspawn_range), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.agent_yspawn_range, self.agent_yspawn_range)], dim=-1), batch_index=env_index)
        agent.sample = self.sample(agent.state.pos, norm=self.norm)

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

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        n_obstacles = kwargs.pop('n_obstacles', 5)
        self._min_dist_between_entities = kwargs.pop('min_dist_between_entities', 0.15)
        self.n_lidar_rays = kwargs.pop('n_lidar_rays', 12)
        self.collision_reward = kwargs.pop('collision_reward', -0.1)
        self.dist_shaping_factor = kwargs.pop('dist_shaping_factor', 1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.plot_grid = True
        self.desired_distance = 0.1
        self.min_collision_distance = 0.005
        self.x_dim = 1
        self.y_dim = 1
        world = World(batch_dim, device, collision_force=400, substeps=5)
        self._target = Agent(name='target', collide=True, color=Color.GREEN, render_action=True, action_script=self.action_script_creator())
        world.add_agent(self._target)
        goal_entity_filter: Callable[[Entity], bool] = lambda e: not isinstance(e, Agent)
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', collide=True, sensors=[Lidar(world, n_rays=self.n_lidar_rays, max_range=0.2, entity_filter=goal_entity_filter)], render_action=True)
            agent.collision_rew = torch.zeros(batch_dim, device=device)
            agent.dist_rew = agent.collision_rew.clone()
            world.add_agent(agent)
        self.obstacles = []
        for i in range(n_obstacles):
            obstacle = Landmark(name=f'obstacle_{i}', collide=True, movable=False, shape=Sphere(radius=0.1), color=Color.RED)
            world.add_landmark(obstacle)
            self.obstacles.append(obstacle)
        return world

    def action_script_creator(self):

        def action_script(agent, world):
            t = self.t / 30
            agent.action.u = torch.stack([torch.cos(t), torch.sin(t)], dim=1)
        return action_script

    def reset_world_at(self, env_index: int=None):
        target_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32)
        target_pos[:, Y] = -self.y_dim
        self._target.set_pos(target_pos, batch_index=env_index)
        ScenarioUtils.spawn_entities_randomly(self.obstacles + self.world.policy_agents, self.world, env_index, self._min_dist_between_entities, x_bounds=(-self.x_dim, self.x_dim), y_bounds=(-self.y_dim, self.y_dim), occupied_positions=target_pos.unsqueeze(1))
        for agent in self.world.policy_agents:
            if env_index is None:
                agent.distance_shaping = (torch.stack([torch.linalg.vector_norm(agent.state.pos - a.state.pos, dim=-1) for a in self.world.agents if a != agent], dim=1) - self.desired_distance).pow(2).mean(-1) * self.dist_shaping_factor
            else:
                agent.distance_shaping[env_index] = (torch.stack([torch.linalg.vector_norm(agent.state.pos[env_index] - a.state.pos[env_index]) for a in self.world.agents if a != agent], dim=0) - self.desired_distance).pow(2).mean(-1) * self.dist_shaping_factor
        if env_index is None:
            self.t = torch.zeros(self.world.batch_dim, device=self.world.device)
        else:
            self.t[env_index] = 0

    def reward(self, agent: Agent):
        is_first = self.world.policy_agents.index(agent) == 0
        if is_first:
            self.t += 1
            if self.collision_reward != 0:
                for a in self.world.policy_agents:
                    a.collision_rew[:] = 0
                for i, a in enumerate(self.world.agents):
                    for j, b in enumerate(self.world.agents):
                        if j <= i:
                            continue
                        collision = self.world.get_distance(a, b) <= self.min_collision_distance
                        if a.action_script is None:
                            a.collision_rew[collision] += self.collision_reward
                        if b.action_script is None:
                            b.collision_rew[collision] += self.collision_reward
        agents_dist_shaping = (torch.stack([torch.linalg.vector_norm(agent.state.pos - a.state.pos, dim=-1) for a in self.world.agents if a != agent], dim=1) - self.desired_distance).pow(2).mean(-1) * self.dist_shaping_factor
        agent.dist_rew = agent.distance_shaping - agents_dist_shaping
        agent.distance_shaping = agents_dist_shaping
        return agent.collision_rew + agent.dist_rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, agent.state.pos - self._target.state.pos, agent.sensors[0].measure()], dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        info = {'agent_collision_rew': agent.collision_rew, 'agent_distance_rew': agent.dist_rew}
        return info

def reset_world_at(self, env_index: int=None):
    target_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32)
    target_pos[:, Y] = -self.y_dim
    self._target.set_pos(target_pos, batch_index=env_index)
    ScenarioUtils.spawn_entities_randomly(self.obstacles + self.world.policy_agents, self.world, env_index, self._min_dist_between_entities, x_bounds=(-self.x_dim, self.x_dim), y_bounds=(-self.y_dim, self.y_dim), occupied_positions=target_pos.unsqueeze(1))
    for agent in self.world.policy_agents:
        if env_index is None:
            agent.distance_shaping = (torch.stack([torch.linalg.vector_norm(agent.state.pos - a.state.pos, dim=-1) for a in self.world.agents if a != agent], dim=1) - self.desired_distance).pow(2).mean(-1) * self.dist_shaping_factor
        else:
            agent.distance_shaping[env_index] = (torch.stack([torch.linalg.vector_norm(agent.state.pos[env_index] - a.state.pos[env_index]) for a in self.world.agents if a != agent], dim=0) - self.desired_distance).pow(2).mean(-1) * self.dist_shaping_factor
    if env_index is None:
        self.t = torch.zeros(self.world.batch_dim, device=self.world.device)
    else:
        self.t[env_index] = 0

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.plot_grid = False
        self.n_agents = kwargs.pop('n_agents', 4)
        self.collisions = kwargs.pop('collisions', True)
        self.world_spawning_x = kwargs.pop('world_spawning_x', 1)
        self.world_spawning_y = kwargs.pop('world_spawning_y', 1)
        self.enforce_bounds = kwargs.pop('enforce_bounds', False)
        self.agents_with_same_goal = kwargs.pop('agents_with_same_goal', 1)
        self.split_goals = kwargs.pop('split_goals', False)
        self.observe_all_goals = kwargs.pop('observe_all_goals', False)
        self.lidar_range = kwargs.pop('lidar_range', 0.35)
        self.agent_radius = kwargs.pop('agent_radius', 0.1)
        self.comms_range = kwargs.pop('comms_range', 0)
        self.n_lidar_rays = kwargs.pop('n_lidar_rays', 12)
        self.shared_rew = kwargs.pop('shared_rew', True)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1)
        self.final_reward = kwargs.pop('final_reward', 0.01)
        self.agent_collision_penalty = kwargs.pop('agent_collision_penalty', -1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.min_distance_between_entities = self.agent_radius * 2 + 0.05
        self.min_collision_distance = 0.005
        if self.enforce_bounds:
            self.x_semidim = self.world_spawning_x
            self.y_semidim = self.world_spawning_y
        else:
            self.x_semidim = None
            self.y_semidim = None
        assert 1 <= self.agents_with_same_goal <= self.n_agents
        if self.agents_with_same_goal > 1:
            assert not self.collisions, 'If agents share goals they cannot be collidables'
        if self.split_goals:
            assert self.n_agents % 2 == 0 and self.agents_with_same_goal == self.n_agents // 2, 'Splitting the goals is allowed when the agents are even and half the team has the same goal'
        world = World(batch_dim, device, substeps=2, x_semidim=self.x_semidim, y_semidim=self.y_semidim)
        known_colors = [(0.22, 0.49, 0.72), (1.0, 0.5, 0), (0.3, 0.69, 0.29), (0.97, 0.51, 0.75), (0.6, 0.31, 0.64), (0.89, 0.1, 0.11), (0.87, 0.87, 0)]
        colors = torch.randn((max(self.n_agents - len(known_colors), 0), 3), device=device)
        entity_filter_agents: Callable[[Entity], bool] = lambda e: isinstance(e, Agent)
        for i in range(self.n_agents):
            color = known_colors[i] if i < len(known_colors) else colors[i - len(known_colors)]
            agent = Agent(name=f'agent_{i}', collide=self.collisions, color=color, shape=Sphere(radius=self.agent_radius), render_action=True, sensors=[Lidar(world, n_rays=self.n_lidar_rays, max_range=self.lidar_range, entity_filter=entity_filter_agents)] if self.collisions else None)
            agent.pos_rew = torch.zeros(batch_dim, device=device)
            agent.agent_collision_rew = agent.pos_rew.clone()
            world.add_agent(agent)
            goal = Landmark(name=f'goal {i}', collide=False, color=color)
            world.add_landmark(goal)
            agent.goal = goal
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.final_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, self.min_distance_between_entities, (-self.world_spawning_x, self.world_spawning_x), (-self.world_spawning_y, self.world_spawning_y))
        occupied_positions = torch.stack([agent.state.pos for agent in self.world.agents], dim=1)
        if env_index is not None:
            occupied_positions = occupied_positions[env_index].unsqueeze(0)
        goal_poses = []
        for _ in self.world.agents:
            position = ScenarioUtils.find_random_pos_for_entity(occupied_positions=occupied_positions, env_index=env_index, world=self.world, min_dist_between_entities=self.min_distance_between_entities, x_bounds=(-self.world_spawning_x, self.world_spawning_x), y_bounds=(-self.world_spawning_y, self.world_spawning_y))
            goal_poses.append(position.squeeze(1))
            occupied_positions = torch.cat([occupied_positions, position], dim=1)
        for i, agent in enumerate(self.world.agents):
            if self.split_goals:
                goal_index = int(i // self.agents_with_same_goal)
            else:
                goal_index = 0 if i < self.agents_with_same_goal else i
            agent.goal.set_pos(goal_poses[goal_index], batch_index=env_index)
            if env_index is None:
                agent.pos_shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.pos_shaping_factor
            else:
                agent.pos_shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.pos_shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.pos_rew[:] = 0
            self.final_rew[:] = 0
            for a in self.world.agents:
                self.pos_rew += self.agent_reward(a)
                a.agent_collision_rew[:] = 0
            self.all_goal_reached = torch.all(torch.stack([a.on_goal for a in self.world.agents], dim=-1), dim=-1)
            self.final_rew[self.all_goal_reached] = self.final_reward
            for i, a in enumerate(self.world.agents):
                for j, b in enumerate(self.world.agents):
                    if i <= j:
                        continue
                    if self.world.collides(a, b):
                        distance = self.world.get_distance(a, b)
                        a.agent_collision_rew[distance <= self.min_collision_distance] += self.agent_collision_penalty
                        b.agent_collision_rew[distance <= self.min_collision_distance] += self.agent_collision_penalty
        pos_reward = self.pos_rew if self.shared_rew else agent.pos_rew
        return pos_reward + self.final_rew + agent.agent_collision_rew

    def agent_reward(self, agent: Agent):
        agent.distance_to_goal = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=-1)
        agent.on_goal = agent.distance_to_goal < agent.goal.shape.radius
        pos_shaping = agent.distance_to_goal * self.pos_shaping_factor
        agent.pos_rew = agent.pos_shaping - pos_shaping
        agent.pos_shaping = pos_shaping
        return agent.pos_rew

    def observation(self, agent: Agent):
        goal_poses = []
        if self.observe_all_goals:
            for a in self.world.agents:
                goal_poses.append(agent.state.pos - a.goal.state.pos)
        else:
            goal_poses.append(agent.state.pos - agent.goal.state.pos)
        return torch.cat([agent.state.pos, agent.state.vel] + goal_poses + ([agent.sensors[0]._max_range - agent.sensors[0].measure()] if self.collisions else []), dim=-1)

    def done(self):
        return torch.stack([torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=-1) < agent.shape.radius for agent in self.world.agents], dim=-1).all(-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew if self.shared_rew else agent.pos_rew, 'final_rew': self.final_rew, 'agent_collisions': agent.agent_collision_rew}

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms: List[Geom] = []
        for i, agent1 in enumerate(self.world.agents):
            for j, agent2 in enumerate(self.world.agents):
                if j <= i:
                    continue
                agent_dist = torch.linalg.vector_norm(agent1.state.pos - agent2.state.pos, dim=-1)
                if agent_dist[env_index] <= self.comms_range:
                    color = Color.BLACK.value
                    line = rendering.Line(agent1.state.pos[env_index], agent2.state.pos[env_index], width=1)
                    xform = rendering.Transform()
                    line.add_attr(xform)
                    line.set_color(*color)
                    geoms.append(line)
        return geoms

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, self.min_distance_between_entities, (-self.world_spawning_x, self.world_spawning_x), (-self.world_spawning_y, self.world_spawning_y))
    occupied_positions = torch.stack([agent.state.pos for agent in self.world.agents], dim=1)
    if env_index is not None:
        occupied_positions = occupied_positions[env_index].unsqueeze(0)
    goal_poses = []
    for _ in self.world.agents:
        position = ScenarioUtils.find_random_pos_for_entity(occupied_positions=occupied_positions, env_index=env_index, world=self.world, min_dist_between_entities=self.min_distance_between_entities, x_bounds=(-self.world_spawning_x, self.world_spawning_x), y_bounds=(-self.world_spawning_y, self.world_spawning_y))
        goal_poses.append(position.squeeze(1))
        occupied_positions = torch.cat([occupied_positions, position], dim=1)
    for i, agent in enumerate(self.world.agents):
        if self.split_goals:
            goal_index = int(i // self.agents_with_same_goal)
        else:
            goal_index = 0 if i < self.agents_with_same_goal else i
        agent.goal.set_pos(goal_poses[goal_index], batch_index=env_index)
        if env_index is None:
            agent.pos_shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.pos_shaping_factor
        else:
            agent.pos_shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.pos_shaping_factor

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        self.package_width = kwargs.pop('package_width', 0.6)
        self.package_length = kwargs.pop('package_length', 0.6)
        self.package_mass = kwargs.pop('package_mass', 50)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.shaping_factor = 100
        world = World(batch_dim, device, contact_margin=0.006, substeps=5, collision_force=500)
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(0.03), u_multiplier=0.5)
            world.add_agent(agent)
        goal = Landmark(name='goal', collide=False, shape=Sphere(radius=0.09), color=Color.LIGHT_GREEN)
        world.add_landmark(goal)
        self.package = Landmark(name=f'package {i}', collide=True, movable=True, mass=self.package_mass, shape=Box(length=self.package_length, width=self.package_width, hollow=True), color=Color.RED)
        self.package.goal = goal
        world.add_landmark(self.package)
        return world

    def reset_world_at(self, env_index: int=None):
        package_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0)
        self.package.set_pos(package_pos, batch_index=env_index)
        for agent in self.world.agents:
            agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.package_length / 2 + agent.shape.radius, self.package_length / 2 - agent.shape.radius), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.package_width / 2 + agent.shape.radius, self.package_width / 2 - agent.shape.radius)], dim=1) + package_pos, batch_index=env_index)
        self.package.goal.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        if env_index is None:
            self.package.global_shaping = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1) * self.shaping_factor
            self.package.on_goal = torch.zeros(self.world.batch_dim, dtype=torch.bool, device=self.world.device)
        else:
            self.package.global_shaping[env_index] = torch.linalg.vector_norm(self.package.state.pos[env_index] - self.package.goal.state.pos[env_index]) * self.shaping_factor
            self.package.on_goal[env_index] = False

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            self.package.dist_to_goal = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1)
            self.package.on_goal = self.world.is_overlapping(self.package, self.package.goal)
            self.package.color = torch.tensor(Color.RED.value, device=self.world.device, dtype=torch.float32).repeat(self.world.batch_dim, 1)
            self.package.color[self.package.on_goal] = torch.tensor(Color.GREEN.value, device=self.world.device, dtype=torch.float32)
            package_shaping = self.package.dist_to_goal * self.shaping_factor
            self.rew[~self.package.on_goal] += self.package.global_shaping[~self.package.on_goal] - package_shaping[~self.package.on_goal]
            self.package.global_shaping = package_shaping
            self.rew[~self.package.on_goal] += self.package.global_shaping[~self.package.on_goal] - package_shaping[~self.package.on_goal]
            self.package.global_shaping = package_shaping
        return self.rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, self.package.state.vel, self.package.state.pos - agent.state.pos, self.package.state.pos - self.package.goal.state.pos], dim=-1)

    def done(self):
        return self.package.on_goal

def reset_world_at(self, env_index: int=None):
    package_pos = torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0)
    self.package.set_pos(package_pos, batch_index=env_index)
    for agent in self.world.agents:
        agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.package_length / 2 + agent.shape.radius, self.package_length / 2 - agent.shape.radius), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.package_width / 2 + agent.shape.radius, self.package_width / 2 - agent.shape.radius)], dim=1) + package_pos, batch_index=env_index)
    self.package.goal.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    if env_index is None:
        self.package.global_shaping = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1) * self.shaping_factor
        self.package.on_goal = torch.zeros(self.world.batch_dim, dtype=torch.bool, device=self.world.device)
    else:
        self.package.global_shaping[env_index] = torch.linalg.vector_norm(self.package.state.pos[env_index] - self.package.goal.state.pos[env_index]) * self.shaping_factor
        self.package.on_goal[env_index] = False

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        self.line_length = kwargs.pop('line_length', 2)
        line_mass = kwargs.pop('line_mass', 30)
        self.desired_velocity = kwargs.pop('desired_velocity', 0.05)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device)
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', u_multiplier=0.6, shape=Sphere(0.03))
            world.add_agent(agent)
        self.line = Landmark(name='line', collide=True, rotatable=True, shape=Line(length=self.line_length), mass=line_mass, color=Color.BLACK)
        world.add_landmark(self.line)
        center = Landmark(name='center', shape=Sphere(radius=0.02), collide=False, color=Color.BLACK)
        world.add_landmark(center)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        self.line.set_rot(torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2, torch.pi / 2), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = (self.line.state.ang_vel.abs() - self.desired_velocity).abs()
        return -self.rew

    def observation(self, agent: Agent):
        line_end_1 = torch.cat([self.line_length / 2 * torch.cos(self.line.state.rot), self.line_length / 2 * torch.sin(self.line.state.rot)], dim=1)
        line_end_2 = -line_end_1
        return torch.cat([agent.state.pos, agent.state.vel, self.line.state.pos - agent.state.pos, line_end_1 - agent.state.pos, line_end_2 - agent.state.pos, self.line.state.rot % torch.pi, self.line.state.ang_vel.abs(), (self.line.state.ang_vel.abs() - self.desired_velocity).abs()], dim=-1)

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    self.line.set_rot(torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2, torch.pi / 2), batch_index=env_index)

class HeuristicPolicy(BaseHeuristicPolicy):

    def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
        assert self.continuous_actions is True, 'Heuristic for continuous actions only'
        index_line_extrema = 6
        pos_agent = observation[:, :2]
        pos_end2_agent = observation[:, index_line_extrema + 2:index_line_extrema + 4]
        pos_end2 = pos_end2_agent + pos_agent
        pos_end2_shifted = TorchUtils.rotate_vector(pos_end2, torch.tensor(torch.pi / 4, device=observation.device).expand(pos_end2.shape[0]))
        pos_end2_shifted_agent = pos_end2_shifted - pos_agent
        action_agent = torch.clamp(pos_end2_shifted_agent, min=-u_range, max=u_range)
        return action_agent

def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
    assert self.continuous_actions is True, 'Heuristic for continuous actions only'
    index_line_extrema = 6
    pos_agent = observation[:, :2]
    pos_end2_agent = observation[:, index_line_extrema + 2:index_line_extrema + 4]
    pos_end2 = pos_end2_agent + pos_agent
    pos_end2_shifted = TorchUtils.rotate_vector(pos_end2, torch.tensor(torch.pi / 4, device=observation.device).expand(pos_end2.shape[0]))
    pos_end2_shifted_agent = pos_end2_shifted - pos_agent
    action_agent = torch.clamp(pos_end2_shifted_agent, min=-u_range, max=u_range)
    return action_agent

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

def is_passage(i):
    is_pass = torch.full(i.shape, False, device=self.world.device)
    for index in passage_indexes:
        is_pass += i == index
    return is_pass

def spawn_walls(self, env_index):
    for i, wall in enumerate(self.walls):
        wall.set_pos(torch.tensor([0.0 if i % 2 else self.world.x_semidim + self.agent_radius if i == 0 else -self.world.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.world.y_semidim + self.agent_radius if i == 1 else -self.world.y_semidim - self.agent_radius], device=self.world.device), batch_index=env_index)
        wall.set_rot(torch.tensor([torch.pi / 2 if not i % 2 else 0.0], device=self.world.device), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.plot_grid = True
        self.viewer_zoom = 2
        self.vel_shaping_factor = kwargs.pop('vel_shaping_factor', 1)
        self.dist_shaping_factor = kwargs.pop('dist_shaping_factor', 1)
        self.wind_shaping_factor = kwargs.pop('wind_shaping_factor', 1)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 0)
        self.rot_shaping_factor = kwargs.pop('rot_shaping_factor', 0)
        self.energy_shaping_factor = kwargs.pop('energy_shaping_factor', 0)
        self.observe_rel_pos = kwargs.pop('observe_rel_pos', False)
        self.observe_rel_vel = kwargs.pop('observe_rel_vel', False)
        self.observe_pos = kwargs.pop('observe_pos', True)
        self.use_controller = kwargs.pop('use_controller', True)
        self.wind = torch.tensor([0, -kwargs.pop('wind', 2)], device=device, dtype=torch.float32).expand(batch_dim, 2)
        self.v_range = kwargs.pop('v_range', 0.5)
        self.desired_vel = kwargs.pop('desired_vel', self.v_range)
        self.f_range = kwargs.pop('f_range', 100)
        controller_params = [1.5, 0.6, 0.002]
        self.u_range = self.v_range if self.use_controller else self.f_range
        self.cover_angle_tolerance = kwargs.pop('cover_angle_tolerance', 1)
        self.horizon = kwargs.pop('horizon', 200)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.desired_distance = 1
        self.grid_spacing = self.desired_distance
        world = World(batch_dim, device, drag=0, linear_friction=0.1)
        self.desired_vel = torch.tensor([0.0, self.desired_vel], device=device, dtype=torch.float32)
        self.max_pos = self.horizon * world.dt * self.desired_vel[Y]
        self.desired_pos = 10.0
        self.n_agents = 2
        self.big_agent = Agent(name='agent_0', render_action=True, shape=Sphere(radius=0.05), u_range=self.u_range, v_range=self.v_range, f_range=self.f_range, gravity=self.wind)
        self.big_agent.controller = VelocityController(self.big_agent, world, controller_params, 'standard')
        world.add_agent(self.big_agent)
        self.small_agent = Agent(name='agent_1', render_action=True, shape=Sphere(radius=0.03), u_range=self.u_range, v_range=self.v_range, f_range=self.f_range, gravity=self.wind)
        self.small_agent.controller = VelocityController(self.small_agent, world, controller_params, 'standard')
        world.add_agent(self.small_agent)
        for agent in world.agents:
            agent.wind_rew = torch.zeros(batch_dim, device=device)
            agent.vel_rew = agent.wind_rew.clone()
            agent.energy_rew = agent.wind_rew.clone()
        self.dist_rew = torch.zeros(batch_dim, device=device)
        self.rot_rew = self.dist_rew.clone()
        self.vel_reward = self.dist_rew.clone()
        self.pos_rew = self.dist_rew.clone()
        self.t = self.dist_rew.clone()
        return world

    def set_wind(self, wind):
        self.wind = torch.tensor([0, -wind], device=self.world.device, dtype=torch.float32).expand(self.world.batch_dim, self.world.dim_p)
        self.big_agent.gravity = self.wind
        self.small_agent.gravity = self.wind

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 8, torch.pi / 8)
        start_delta_x = self.desired_distance / 2 * torch.cos(start_angle)
        start_delta_y = self.desired_distance / 2 * torch.sin(start_angle)
        order = torch.randperm(self.n_agents).tolist()
        agents = [self.world.agents[i] for i in order]
        for i, agent in enumerate(agents):
            agent.controller.reset(env_index)
            if i == 0:
                agent.set_pos(-torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
            else:
                agent.set_pos(torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
            if env_index is None:
                agent.vel_shaping = torch.linalg.vector_norm(agent.state.vel - self.desired_vel, dim=-1) * self.vel_shaping_factor
                agent.energy_shaping = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
                agent.wind_shaping = torch.linalg.vector_norm(agent.gravity, dim=-1) * self.wind_shaping_factor
            else:
                agent.vel_shaping[env_index] = torch.linalg.vector_norm(agent.state.vel[env_index] - self.desired_vel) * self.vel_shaping_factor
                agent.energy_shaping[env_index] = 0
                agent.wind_shaping[env_index] = torch.linalg.vector_norm(agent.gravity[env_index]) * self.wind_shaping_factor
        if env_index is None:
            self.t = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.int)
            self.distance_shaping = (torch.linalg.vector_norm(self.small_agent.state.pos - self.big_agent.state.pos, dim=-1) - self.desired_distance).abs() * self.dist_shaping_factor
            self.pos_shaping = (torch.maximum(self.big_agent.state.pos[:, Y], self.small_agent.state.pos[:, Y]) - self.desired_pos).abs() * self.pos_shaping_factor
            self.rot_shaping = get_line_angle_dist_0_180(self.get_agents_angle(), 0) * self.rot_shaping_factor
        else:
            self.t[env_index] = 0
            self.distance_shaping[env_index] = (torch.linalg.vector_norm(self.small_agent.state.pos[env_index] - self.big_agent.state.pos[env_index]) - self.desired_distance).abs() * self.dist_shaping_factor
            self.pos_shaping[env_index] = (torch.maximum(self.big_agent.state.pos[env_index, Y], self.small_agent.state.pos[env_index, Y]) - self.desired_pos).abs() * self.pos_shaping_factor
            self.rot_shaping[env_index] = get_line_angle_dist_0_180(self.get_agents_angle()[env_index], 0) * self.rot_shaping_factor

    def process_action(self, agent: Agent):
        if self.use_controller:
            agent.controller.process_force()

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.t += 1
            self.set_friction()
            distance_shaping = (torch.linalg.vector_norm(self.small_agent.state.pos - self.big_agent.state.pos, dim=-1) - self.desired_distance).abs() * self.dist_shaping_factor
            self.dist_rew = self.distance_shaping - distance_shaping
            self.distance_shaping = distance_shaping
            rot_shaping = get_line_angle_dist_0_180(self.get_agents_angle(), 0) * self.rot_shaping_factor
            self.rot_rew = self.rot_shaping - rot_shaping
            self.rot_shaping = rot_shaping
            pos_shaping = (torch.maximum(self.big_agent.state.pos[:, Y], self.small_agent.state.pos[:, Y]) - self.desired_pos).abs() * self.pos_shaping_factor
            self.pos_rew = self.pos_shaping - pos_shaping
            self.pos_shaping = pos_shaping
            for a in self.world.agents:
                vel_shaping = torch.linalg.vector_norm(a.state.vel - self.desired_vel, dim=-1) * self.vel_shaping_factor
                a.vel_rew = a.vel_shaping - vel_shaping
                a.vel_shaping = vel_shaping
            self.vel_reward = torch.stack([a.vel_rew for a in self.world.agents], dim=1).mean(-1)
            for a in self.world.agents:
                energy_shaping = torch.linalg.vector_norm(a.action.u, dim=-1) * self.energy_shaping_factor
                a.energy_rew = a.energy_shaping - energy_shaping
                a.energy_rew[self.t < 10] = 0
                a.energy_shaping = energy_shaping
            self.energy_rew = torch.stack([a.energy_rew for a in self.world.agents], dim=1).mean(-1)
            for a in self.world.agents:
                wind_shaping = torch.linalg.vector_norm(a.gravity, dim=-1) * self.wind_shaping_factor
                a.wind_rew = a.wind_shaping - wind_shaping
                a.wind_rew[self.t < 5] = 0
                a.wind_shaping = wind_shaping
            self.wind_rew = torch.stack([a.wind_rew for a in self.world.agents], dim=1).mean(-1)
        return self.dist_rew + self.vel_reward + self.rot_rew + self.energy_rew + self.wind_rew + self.pos_rew

    def set_friction(self):
        dist_to_goal_angle = (get_line_angle_dist_0_360(self.get_agents_angle(), torch.tensor([-torch.pi / 2], device=self.world.device).expand(self.world.batch_dim, 1)) + 1).clamp(max=self.cover_angle_tolerance).unsqueeze(-1) + (1 - self.cover_angle_tolerance)
        dist_to_goal_angle = (dist_to_goal_angle - 1 + self.cover_angle_tolerance) / self.cover_angle_tolerance
        self.big_agent.gravity = self.wind * dist_to_goal_angle

    def observation(self, agent: Agent):
        observations = []
        if self.observe_pos:
            observations.append(agent.state.pos)
        observations.append(agent.state.vel)
        if self.observe_rel_pos:
            for a in self.world.agents:
                if a != agent:
                    observations.append(a.state.pos - agent.state.pos)
        if self.observe_rel_vel:
            for a in self.world.agents:
                if a != agent:
                    observations.append(a.state.vel - agent.state.vel)
        return torch.cat(observations, dim=-1)

    def get_agents_angle(self):
        return torch.atan2(self.big_agent.state.pos[:, Y] - self.small_agent.state.pos[:, Y], self.big_agent.state.pos[:, X] - self.small_agent.state.pos[:, X]).unsqueeze(-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'dist_rew': self.dist_rew, 'rot_rew': self.rot_rew, 'pos_rew': self.pos_rew, 'agent_wind_rew': agent.wind_rew, 'agent_vel_rew': agent.vel_rew, 'agent_energy_rew': agent.energy_rew, 'delta_vel_to_goal': torch.linalg.vector_norm(agent.state.vel - self.desired_vel, dim=-1)}

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms = []
        color = Color.BLACK.value
        circle = rendering.Line((-self.desired_distance / 2, 0), (self.desired_distance / 2, 0), width=1)
        xform = rendering.Transform()
        xform.set_translation(*(self.big_agent.state.pos[env_index] + self.small_agent.state.pos[env_index]) / 2)
        xform.set_rotation(self.get_agents_angle()[env_index])
        circle.add_attr(xform)
        circle.set_color(*color)
        geoms.append(circle)
        color = Color.RED.value
        circle = rendering.Line((-self.desired_distance / 2, 0), (self.desired_distance / 2, 0), width=1)
        xform = rendering.Transform()
        xform.set_translation(0.0, self.max_pos)
        circle.add_attr(xform)
        circle.set_color(*color)
        geoms.append(circle)
        return geoms

def set_wind(self, wind):
    self.wind = torch.tensor([0, -wind], device=self.world.device, dtype=torch.float32).expand(self.world.batch_dim, self.world.dim_p)
    self.big_agent.gravity = self.wind
    self.small_agent.gravity = self.wind

def reset_world_at(self, env_index: int=None):
    start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 8, torch.pi / 8)
    start_delta_x = self.desired_distance / 2 * torch.cos(start_angle)
    start_delta_y = self.desired_distance / 2 * torch.sin(start_angle)
    order = torch.randperm(self.n_agents).tolist()
    agents = [self.world.agents[i] for i in order]
    for i, agent in enumerate(agents):
        agent.controller.reset(env_index)
        if i == 0:
            agent.set_pos(-torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        else:
            agent.set_pos(torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        if env_index is None:
            agent.vel_shaping = torch.linalg.vector_norm(agent.state.vel - self.desired_vel, dim=-1) * self.vel_shaping_factor
            agent.energy_shaping = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            agent.wind_shaping = torch.linalg.vector_norm(agent.gravity, dim=-1) * self.wind_shaping_factor
        else:
            agent.vel_shaping[env_index] = torch.linalg.vector_norm(agent.state.vel[env_index] - self.desired_vel) * self.vel_shaping_factor
            agent.energy_shaping[env_index] = 0
            agent.wind_shaping[env_index] = torch.linalg.vector_norm(agent.gravity[env_index]) * self.wind_shaping_factor
    if env_index is None:
        self.t = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.int)
        self.distance_shaping = (torch.linalg.vector_norm(self.small_agent.state.pos - self.big_agent.state.pos, dim=-1) - self.desired_distance).abs() * self.dist_shaping_factor
        self.pos_shaping = (torch.maximum(self.big_agent.state.pos[:, Y], self.small_agent.state.pos[:, Y]) - self.desired_pos).abs() * self.pos_shaping_factor
        self.rot_shaping = get_line_angle_dist_0_180(self.get_agents_angle(), 0) * self.rot_shaping_factor
    else:
        self.t[env_index] = 0
        self.distance_shaping[env_index] = (torch.linalg.vector_norm(self.small_agent.state.pos[env_index] - self.big_agent.state.pos[env_index]) - self.desired_distance).abs() * self.dist_shaping_factor
        self.pos_shaping[env_index] = (torch.maximum(self.big_agent.state.pos[env_index, Y], self.small_agent.state.pos[env_index, Y]) - self.desired_pos).abs() * self.pos_shaping_factor
        self.rot_shaping[env_index] = get_line_angle_dist_0_180(self.get_agents_angle()[env_index], 0) * self.rot_shaping_factor

def set_friction(self):
    dist_to_goal_angle = (get_line_angle_dist_0_360(self.get_agents_angle(), torch.tensor([-torch.pi / 2], device=self.world.device).expand(self.world.batch_dim, 1)) + 1).clamp(max=self.cover_angle_tolerance).unsqueeze(-1) + (1 - self.cover_angle_tolerance)
    dist_to_goal_angle = (dist_to_goal_angle - 1 + self.cover_angle_tolerance) / self.cover_angle_tolerance
    self.big_agent.gravity = self.wind * dist_to_goal_angle

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        self.energy_coeff = kwargs.pop('energy_coeff', DEFAULT_ENERGY_COEFF)
        self.start_same_point = kwargs.pop('start_same_point', False)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.agent_radius = 0.05
        self.goal_radius = 0.03
        world = World(batch_dim, device)
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', collide=False, shape=Sphere(radius=self.agent_radius))
            world.add_agent(agent)
        goal = Landmark(name='goal', collide=False, shape=Sphere(radius=self.goal_radius), color=Color.GREEN)
        world.add_landmark(goal)
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.energy_rew = self.pos_rew.clone()
        self._done = torch.zeros(batch_dim, device=device, dtype=torch.bool)
        return world

    def reset_world_at(self, env_index: int=None):
        if self.start_same_point:
            for agent in self.world.agents:
                agent.set_pos(torch.zeros((1, 2) if env_index is not None else (self.world.batch_dim, 2), device=self.world.device, dtype=torch.float), batch_index=env_index)
            ScenarioUtils.spawn_entities_randomly(self.world.landmarks, self.world, env_index, self.goal_radius + self.agent_radius + 0.01, x_bounds=(-1, 1), y_bounds=(-1, 1), occupied_positions=torch.zeros(1 if env_index is not None else self.world.batch_dim, 1, 2, device=self.world.device, dtype=torch.float))
        else:
            ScenarioUtils.spawn_entities_randomly(self.world.policy_agents + self.world.landmarks, self.world, env_index, self.goal_radius + self.agent_radius + 0.01, x_bounds=(-1, 1), y_bounds=(-1, 1))
        for landmark in self.world.landmarks:
            if env_index is None:
                landmark.eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
                landmark.reset_render()
                self._done[:] = False
            else:
                landmark.eaten[env_index] = False
                landmark.is_rendering[env_index] = True
                self._done[env_index] = False

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        is_last = agent == self.world.agents[-1]
        if is_first:
            self.any_eaten = self._done = torch.any(torch.stack([torch.linalg.vector_norm(a.state.pos - self.world.landmarks[0].state.pos, dim=1) < a.shape.radius + self.world.landmarks[0].shape.radius for a in self.world.agents], dim=1), dim=-1)
        self.pos_rew[:] = 0
        self.pos_rew[self.any_eaten * ~self.world.landmarks[0].eaten] = 1
        if is_last:
            self.world.landmarks[0].eaten[self.any_eaten] = True
            self.world.landmarks[0].is_rendering[self.any_eaten] = False
        if is_first:
            self.energy_rew = self.energy_coeff * -torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * (a.u_range * a.u_multiplier) ** 2) for a in self.world.agents], dim=1).sum(-1)
        rew = self.pos_rew + self.energy_rew
        return rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, self.world.landmarks[0].state.pos - agent.state.pos, self.world.landmarks[0].eaten.unsqueeze(-1)], dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        info = {'pos_rew': self.pos_rew, 'energy_rew': self.energy_rew}
        return info

    def done(self):
        return self._done

def reset_world_at(self, env_index: int=None):
    if self.start_same_point:
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, 2) if env_index is not None else (self.world.batch_dim, 2), device=self.world.device, dtype=torch.float), batch_index=env_index)
        ScenarioUtils.spawn_entities_randomly(self.world.landmarks, self.world, env_index, self.goal_radius + self.agent_radius + 0.01, x_bounds=(-1, 1), y_bounds=(-1, 1), occupied_positions=torch.zeros(1 if env_index is not None else self.world.batch_dim, 1, 2, device=self.world.device, dtype=torch.float))
    else:
        ScenarioUtils.spawn_entities_randomly(self.world.policy_agents + self.world.landmarks, self.world, env_index, self.goal_radius + self.agent_radius + 0.01, x_bounds=(-1, 1), y_bounds=(-1, 1))
    for landmark in self.world.landmarks:
        if env_index is None:
            landmark.eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
            landmark.reset_render()
            self._done[:] = False
        else:
            landmark.eaten[env_index] = False
            landmark.is_rendering[env_index] = True
            self._done[env_index] = False

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_passages = kwargs.pop('n_passages', 1)
        self.shared_reward = kwargs.pop('shared_reward', False)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert self.n_passages >= 1 and self.n_passages <= 20
        self.shaping_factor = 100
        self.n_agents = 5
        self.agent_radius = 0.03333
        self.agent_spacing = 0.1
        self.passage_width = 0.2
        self.passage_length = 0.103
        self.visualize_semidims = False
        world = World(batch_dim, device, x_semidim=1, y_semidim=1)
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(self.agent_radius), u_multiplier=0.7)
            world.add_agent(agent)
            goal = Landmark(name=f'goal {i}', collide=False, shape=Sphere(radius=self.agent_radius), color=Color.LIGHT_GREEN)
            agent.goal = goal
            world.add_landmark(goal)
        for i in range(int((2 * world.x_semidim + 2 * self.agent_radius) // self.passage_length)):
            removed = i < self.n_passages
            passage = Landmark(name=f'passage {i}', collide=not removed, movable=False, shape=Box(length=self.passage_length, width=self.passage_width), color=Color.RED, collision_filter=lambda e: not isinstance(e.shape, Box))
            world.add_landmark(passage)
        return world

    def reset_world_at(self, env_index: int=None):
        central_agent_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), 1 - (3 * self.agent_radius + self.agent_spacing)), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), -(3 * self.agent_radius + self.agent_spacing) - self.passage_width / 2)], dim=1)
        central_goal_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), 1 - (3 * self.agent_radius + self.agent_spacing)), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(3 * self.agent_radius + self.agent_spacing + self.passage_width / 2, 1 - (3 * self.agent_radius + self.agent_spacing))], dim=1)
        order = torch.randperm(self.n_agents).tolist()
        agents = [self.world.agents[i] for i in order]
        goals = [self.world.landmarks[i] for i in order]
        for i, goal in enumerate(goals):
            if i == self.n_agents - 1:
                goal.set_pos(central_goal_pos, batch_index=env_index)
            else:
                goal.set_pos(central_goal_pos + torch.tensor([[0.0 if i % 2 else self.agent_spacing if i == 0 else -self.agent_spacing, 0.0 if not i % 2 else self.agent_spacing if i == 1 else -self.agent_spacing]], device=self.world.device), batch_index=env_index)
        for i, agent in enumerate(agents):
            if i == self.n_agents - 1:
                agent.set_pos(central_agent_pos, batch_index=env_index)
            else:
                agent.set_pos(central_agent_pos + torch.tensor([[0.0 if i % 2 else self.agent_spacing if i == 0 else -self.agent_spacing, 0.0 if not i % 2 else self.agent_spacing if i == 1 else -self.agent_spacing]], device=self.world.device), batch_index=env_index)
            if env_index is None:
                agent.global_shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.shaping_factor
            else:
                agent.global_shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.shaping_factor
        order = torch.randperm(len(self.world.landmarks[self.n_agents:])).tolist()
        passages = [self.world.landmarks[self.n_agents:][i] for i in order]
        for i, passage in enumerate(passages):
            if not passage.collide:
                passage.is_rendering[:] = False
            passage.set_pos(torch.tensor([-1 - self.agent_radius + self.passage_length / 2 + self.passage_length * i, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if self.shared_reward:
            if is_first:
                self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
                for a in self.world.agents:
                    dist_to_goal = torch.linalg.vector_norm(a.state.pos - a.goal.state.pos, dim=1)
                    agent_shaping = dist_to_goal * self.shaping_factor
                    self.rew += a.global_shaping - agent_shaping
                    a.global_shaping = agent_shaping
        else:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            dist_to_goal = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1)
            agent_shaping = dist_to_goal * self.shaping_factor
            self.rew += agent.global_shaping - agent_shaping
            agent.global_shaping = agent_shaping
        if agent.collide:
            for a in self.world.agents:
                if a != agent:
                    self.rew[self.world.is_overlapping(a, agent)] -= 10
            for landmark in self.world.landmarks[self.n_agents:]:
                if landmark.collide:
                    self.rew[self.world.is_overlapping(agent, landmark)] -= 10
        return self.rew

    def observation(self, agent: Agent):
        passage_obs = []
        passages = self.world.landmarks[self.n_agents:]
        for passage in passages:
            if not passage.collide:
                passage_obs.append(passage.state.pos - agent.state.pos)
        return torch.cat([agent.state.pos, agent.state.vel, agent.goal.state.pos - agent.state.pos, *passage_obs], dim=-1)

    def done(self):
        return torch.all(torch.stack([torch.linalg.vector_norm(a.state.pos - a.goal.state.pos, dim=1) <= a.shape.radius / 2 for a in self.world.agents], dim=1), dim=1)

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        for i in range(4):
            geom = Line(length=2 + self.agent_radius * 2).get_geometry()
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(0.0 if i % 2 else self.world.x_semidim + self.agent_radius if i == 0 else -self.world.x_semidim - self.agent_radius, 0.0 if not i % 2 else self.world.x_semidim + self.agent_radius if i == 1 else -self.world.x_semidim - self.agent_radius)
            xform.set_rotation(torch.pi / 2 if not i % 2 else 0.0)
            color = Color.BLACK.value
            if isinstance(color, torch.Tensor) and len(color.shape) > 1:
                color = color[env_index]
            geom.set_color(*color)
            geoms.append(geom)
        return geoms

def reset_world_at(self, env_index: int=None):
    central_agent_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), 1 - (3 * self.agent_radius + self.agent_spacing)), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), -(3 * self.agent_radius + self.agent_spacing) - self.passage_width / 2)], dim=1)
    central_goal_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1 + (3 * self.agent_radius + self.agent_spacing), 1 - (3 * self.agent_radius + self.agent_spacing)), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(3 * self.agent_radius + self.agent_spacing + self.passage_width / 2, 1 - (3 * self.agent_radius + self.agent_spacing))], dim=1)
    order = torch.randperm(self.n_agents).tolist()
    agents = [self.world.agents[i] for i in order]
    goals = [self.world.landmarks[i] for i in order]
    for i, goal in enumerate(goals):
        if i == self.n_agents - 1:
            goal.set_pos(central_goal_pos, batch_index=env_index)
        else:
            goal.set_pos(central_goal_pos + torch.tensor([[0.0 if i % 2 else self.agent_spacing if i == 0 else -self.agent_spacing, 0.0 if not i % 2 else self.agent_spacing if i == 1 else -self.agent_spacing]], device=self.world.device), batch_index=env_index)
    for i, agent in enumerate(agents):
        if i == self.n_agents - 1:
            agent.set_pos(central_agent_pos, batch_index=env_index)
        else:
            agent.set_pos(central_agent_pos + torch.tensor([[0.0 if i % 2 else self.agent_spacing if i == 0 else -self.agent_spacing, 0.0 if not i % 2 else self.agent_spacing if i == 1 else -self.agent_spacing]], device=self.world.device), batch_index=env_index)
        if env_index is None:
            agent.global_shaping = torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=1) * self.shaping_factor
        else:
            agent.global_shaping[env_index] = torch.linalg.vector_norm(agent.state.pos[env_index] - agent.goal.state.pos[env_index]) * self.shaping_factor
    order = torch.randperm(len(self.world.landmarks[self.n_agents:])).tolist()
    passages = [self.world.landmarks[self.n_agents:][i] for i in order]
    for i, passage in enumerate(passages):
        if not passage.collide:
            passage.is_rendering[:] = False
        passage.set_pos(torch.tensor([-1 - self.agent_radius + self.passage_length / 2 + self.passage_length * i, 0.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        self.share_reward = kwargs.pop('share_reward', False)
        self.penalise_by_time = kwargs.pop('penalise_by_time', False)
        self.food_radius = kwargs.pop('food_radius', 0.05)
        self.pos_range = kwargs.pop('pos_range', 1.0)
        n_food = kwargs.pop('n_food', n_agents)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device, x_semidim=self.pos_range, y_semidim=self.pos_range)
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', collide=False, shape=Sphere(radius=0.035))
            world.add_agent(agent)
        for i in range(n_food):
            food = Landmark(name=f'food_{i}', collide=False, shape=Sphere(radius=self.food_radius), color=Color.GREEN)
            world.add_landmark(food)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.set_pos(torch.zeros(self.world.dim_p, device=self.world.device, dtype=torch.float32), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.pos_range, self.pos_range), batch_index=env_index)
            if env_index is None:
                landmark.eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
                landmark.just_eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
                landmark.reset_render()
            else:
                landmark.eaten[env_index] = False
                landmark.just_eaten[env_index] = False
                landmark.is_rendering[env_index] = True

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        is_last = agent == self.world.agents[-1]
        rews = torch.zeros(self.world.batch_dim, device=self.world.device)
        for landmark in self.world.landmarks:
            if is_first:
                landmark.how_many_on_food = torch.stack([torch.linalg.vector_norm(a.state.pos - landmark.state.pos, dim=1) < a.shape.radius + landmark.shape.radius for a in self.world.agents], dim=1).sum(-1)
                landmark.anyone_on_food = landmark.how_many_on_food > 0
                landmark.just_eaten[landmark.anyone_on_food] = True
            assert (landmark.how_many_on_food <= len(self.world.agents)).all()
            if self.share_reward:
                rews[landmark.just_eaten * ~landmark.eaten] += 1
            else:
                on_food = torch.linalg.vector_norm(agent.state.pos - landmark.state.pos, dim=1) < agent.shape.radius + landmark.shape.radius
                eating_rew = landmark.how_many_on_food.reciprocal().nan_to_num(posinf=0, neginf=0)
                rews[on_food * ~landmark.eaten] += eating_rew[on_food * ~landmark.eaten]
            if is_last:
                landmark.eaten += landmark.just_eaten
                landmark.just_eaten[:] = False
                landmark.is_rendering[landmark.eaten] = False
        if self.penalise_by_time:
            rews[rews == 0] = -0.01
        return rews

    def observation(self, agent: Agent):
        obs = []
        for landmark in self.world.landmarks:
            obs.append(torch.cat([landmark.state.pos - agent.state.pos, landmark.eaten.to(torch.int).unsqueeze(-1)], dim=-1))
        return torch.cat([agent.state.pos, agent.state.vel, *obs], dim=-1)

    def done(self):
        return torch.all(torch.stack([landmark.eaten for landmark in self.world.landmarks], dim=1), dim=-1)

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.set_pos(torch.zeros(self.world.dim_p, device=self.world.device, dtype=torch.float32), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.pos_range, self.pos_range), batch_index=env_index)
        if env_index is None:
            landmark.eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
            landmark.just_eaten = torch.full((self.world.batch_dim,), False, device=self.world.device)
            landmark.reset_render()
        else:
            landmark.eaten[env_index] = False
            landmark.just_eaten[env_index] = False
            landmark.is_rendering[env_index] = True

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_agents = kwargs.pop('n_agents', 3)
        self.package_mass = kwargs.pop('package_mass', 5)
        self.random_package_pos_on_line = kwargs.pop('random_package_pos_on_line', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert self.n_agents > 1
        self.line_length = 0.8
        self.agent_radius = 0.03
        self.shaping_factor = 100
        self.fall_reward = -10
        self.visualize_semidims = False
        world = World(batch_dim, device, gravity=(0.0, -0.05), y_semidim=1)
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(self.agent_radius), u_multiplier=0.7)
            world.add_agent(agent)
        goal = Landmark(name='goal', collide=False, shape=Sphere(), color=Color.LIGHT_GREEN)
        world.add_landmark(goal)
        self.package = Landmark(name='package', collide=True, movable=True, shape=Sphere(), mass=self.package_mass, color=Color.RED)
        self.package.goal = goal
        world.add_landmark(self.package)
        self.line = Landmark(name='line', shape=Line(length=self.line_length), collide=True, movable=True, rotatable=True, mass=5, color=Color.BLACK)
        world.add_landmark(self.line)
        self.floor = Landmark(name='floor', collide=True, shape=Box(length=10, width=1), color=Color.WHITE)
        world.add_landmark(self.floor)
        self.pos_rew = torch.zeros(batch_dim, device=device, dtype=torch.float32)
        self.ground_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        goal_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(0.0, self.world.y_semidim)], dim=1)
        line_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1.0 + self.line_length / 2, 1.0 - self.line_length / 2), torch.full((1, 1) if env_index is not None else (self.world.batch_dim, 1), -self.world.y_semidim + self.agent_radius * 2, device=self.world.device, dtype=torch.float32)], dim=1)
        package_rel_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.line_length / 2 + self.package.shape.radius if self.random_package_pos_on_line else 0.0, self.line_length / 2 - self.package.shape.radius if self.random_package_pos_on_line else 0.0), torch.full((1, 1) if env_index is not None else (self.world.batch_dim, 1), self.package.shape.radius, device=self.world.device, dtype=torch.float32)], dim=1)
        for i, agent in enumerate(self.world.agents):
            agent.set_pos(line_pos + torch.tensor([-(self.line_length - agent.shape.radius) / 2 + i * (self.line_length - agent.shape.radius) / (self.n_agents - 1), -self.agent_radius * 2], device=self.world.device, dtype=torch.float32), batch_index=env_index)
        self.line.set_pos(line_pos, batch_index=env_index)
        self.package.goal.set_pos(goal_pos, batch_index=env_index)
        self.line.set_rot(torch.zeros(1, device=self.world.device, dtype=torch.float32), batch_index=env_index)
        self.package.set_pos(line_pos + package_rel_pos, batch_index=env_index)
        self.floor.set_pos(torch.tensor([0, -self.world.y_semidim - self.floor.shape.width / 2 - self.agent_radius], device=self.world.device), batch_index=env_index)
        self.compute_on_the_ground()
        if env_index is None:
            self.global_shaping = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1) * self.shaping_factor
        else:
            self.global_shaping[env_index] = torch.linalg.vector_norm(self.package.state.pos[env_index] - self.package.goal.state.pos[env_index]) * self.shaping_factor

    def compute_on_the_ground(self):
        self.on_the_ground = self.world.is_overlapping(self.line, self.floor) + self.world.is_overlapping(self.package, self.floor)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.pos_rew[:] = 0
            self.ground_rew[:] = 0
            self.compute_on_the_ground()
            self.package_dist = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1)
            self.ground_rew[self.on_the_ground] = self.fall_reward
            global_shaping = self.package_dist * self.shaping_factor
            self.pos_rew = self.global_shaping - global_shaping
            self.global_shaping = global_shaping
        return self.ground_rew + self.pos_rew

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel, agent.state.pos - self.package.state.pos, agent.state.pos - self.line.state.pos, self.package.state.pos - self.package.goal.state.pos, self.package.state.vel, self.line.state.vel, self.line.state.ang_vel, self.line.state.rot % torch.pi], dim=-1)

    def done(self):
        return self.on_the_ground + self.world.is_overlapping(self.package, self.package.goal)

    def info(self, agent: Agent):
        info = {'pos_rew': self.pos_rew, 'ground_rew': self.ground_rew}
        return info

def reset_world_at(self, env_index: int=None):
    goal_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(0.0, self.world.y_semidim)], dim=1)
    line_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1.0 + self.line_length / 2, 1.0 - self.line_length / 2), torch.full((1, 1) if env_index is not None else (self.world.batch_dim, 1), -self.world.y_semidim + self.agent_radius * 2, device=self.world.device, dtype=torch.float32)], dim=1)
    package_rel_pos = torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.line_length / 2 + self.package.shape.radius if self.random_package_pos_on_line else 0.0, self.line_length / 2 - self.package.shape.radius if self.random_package_pos_on_line else 0.0), torch.full((1, 1) if env_index is not None else (self.world.batch_dim, 1), self.package.shape.radius, device=self.world.device, dtype=torch.float32)], dim=1)
    for i, agent in enumerate(self.world.agents):
        agent.set_pos(line_pos + torch.tensor([-(self.line_length - agent.shape.radius) / 2 + i * (self.line_length - agent.shape.radius) / (self.n_agents - 1), -self.agent_radius * 2], device=self.world.device, dtype=torch.float32), batch_index=env_index)
    self.line.set_pos(line_pos, batch_index=env_index)
    self.package.goal.set_pos(goal_pos, batch_index=env_index)
    self.line.set_rot(torch.zeros(1, device=self.world.device, dtype=torch.float32), batch_index=env_index)
    self.package.set_pos(line_pos + package_rel_pos, batch_index=env_index)
    self.floor.set_pos(torch.tensor([0, -self.world.y_semidim - self.floor.shape.width / 2 - self.agent_radius], device=self.world.device), batch_index=env_index)
    self.compute_on_the_ground()
    if env_index is None:
        self.global_shaping = torch.linalg.vector_norm(self.package.state.pos - self.package.goal.state.pos, dim=1) * self.shaping_factor
    else:
        self.global_shaping[env_index] = torch.linalg.vector_norm(self.package.state.pos[env_index] - self.package.goal.state.pos[env_index]) * self.shaping_factor

class HeuristicPolicy(BaseHeuristicPolicy):

    def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
        batch_dim = observation.shape[0]
        index_package_goal_pos = 8
        dist_package_goal = observation[:, index_package_goal_pos:index_package_goal_pos + 2]
        y_distance_ge_0 = dist_package_goal[:, Y] >= 0
        if self.continuous_actions:
            action_agent = torch.clamp(torch.stack([torch.zeros(batch_dim, device=observation.device), -dist_package_goal[:, Y]], dim=1), min=-u_range, max=u_range)
            action_agent[:, Y][y_distance_ge_0] = 0
        else:
            action_agent = torch.full((batch_dim,), 4, device=observation.device)
            action_agent[y_distance_ge_0] = 0
        return action_agent

def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
    batch_dim = observation.shape[0]
    index_package_goal_pos = 8
    dist_package_goal = observation[:, index_package_goal_pos:index_package_goal_pos + 2]
    y_distance_ge_0 = dist_package_goal[:, Y] >= 0
    if self.continuous_actions:
        action_agent = torch.clamp(torch.stack([torch.zeros(batch_dim, device=observation.device), -dist_package_goal[:, Y]], dim=1), min=-u_range, max=u_range)
        action_agent[:, Y][y_distance_ge_0] = 0
    else:
        action_agent = torch.full((batch_dim,), 4, device=observation.device)
        action_agent[y_distance_ge_0] = 0
    return action_agent

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

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

def reward(self, agent: Agent):
    return torch.zeros(self.world.batch_dim, device=self.world.device)

def process_action(self, agent: Agent):
    torque = agent.action.u
    thrust = torch.full((self.world.batch_dim, 1), agent.mass * agent.dynamics.g, device=self.world.device)
    agent.action.u = torch.cat([thrust, torque], dim=-1)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.obs_noise = kwargs.pop('obs_noise', 0)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.agent_radius = 0.03
        self.line_length = 3
        world = World(batch_dim, device, drag=0.1)
        self.agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), mass=2, f_range=0.5, u_range=1, render_action=True)
        self.agent.controller = VelocityController(self.agent, world, [4, 1.25, 0.001], 'standard')
        world.add_agent(self.agent)
        self.tangent = torch.zeros((world.batch_dim, world.dim_p), device=world.device)
        self.tangent[:, Y] = 1
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.dot_product = self.pos_rew.clone()
        self.steady_rew = self.pos_rew.clone()
        return world

    def process_action(self, agent: Agent):
        self.vel_action = agent.action.u.clone()
        agent.controller.process_force()

    def reset_world_at(self, env_index: int=None):
        self.agent.controller.reset(env_index)
        self.agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, 1), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, 0)], dim=1), batch_index=env_index)

    def reward(self, agent: Agent):
        closest_point = agent.state.pos.clone()
        closest_point[:, X] = 0
        self.pos_rew = -torch.linalg.vector_norm(agent.state.pos - closest_point, dim=1) ** 0.5 * 1
        self.dot_product = torch.einsum('bs,bs->b', self.tangent, agent.state.vel) * 0.5
        normalized_vel = agent.state.vel / torch.linalg.vector_norm(agent.state.vel, dim=1).unsqueeze(-1)
        normalized_vel = torch.nan_to_num(normalized_vel)
        normalized_vel_action = self.vel_action / torch.linalg.vector_norm(self.vel_action, dim=1).unsqueeze(-1)
        normalized_vel_action = torch.nan_to_num(normalized_vel_action)
        self.steady_rew = torch.einsum('bs,bs->b', normalized_vel, normalized_vel_action) * 0.2
        return self.pos_rew + self.dot_product + self.steady_rew

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel, agent.state.pos]
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def done(self):
        return self.world.agents[0].state.pos[:, Y] > self.line_length - 1

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'dot_product': self.dot_product, 'steady_rew': self.steady_rew}

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        color = Color.BLACK.value
        line = rendering.Line((0, -1), (0, -1 + self.line_length), width=1)
        line.set_color(*color)
        geoms.append(line)
        return geoms

def reset_world_at(self, env_index: int=None):
    self.agent.controller.reset(env_index)
    self.agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, 1), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, 0)], dim=1), batch_index=env_index)

def observation(self, agent: Agent):
    observations = [agent.state.pos, agent.state.vel, agent.state.pos]
    for i, obs in enumerate(observations):
        noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
        observations[i] = obs + noise
    return torch.cat(observations, dim=-1)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_agents = kwargs.pop('n_agents', 15)
        self.n_lines = kwargs.pop('n_lines', 15)
        self.n_boxes = kwargs.pop('n_boxes', 15)
        self.lidar = kwargs.pop('lidar', False)
        self.vectorized_lidar = kwargs.pop('vectorized_lidar', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.agent_radius = 0.05
        self.line_length = 0.3
        self.box_length = 0.2
        self.box_width = 0.1
        self.world_semidim = 1
        self.min_dist_between_entities = 0.1
        world = World(batch_dim, device, dt=0.1, drag=0.25, substeps=5, collision_force=500, x_semidim=self.world_semidim, y_semidim=self.world_semidim)
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(radius=self.agent_radius), u_multiplier=0.7, rotatable=True, sensors=[Lidar(world, n_rays=16, max_range=0.5)] if self.lidar else [])
            world.add_agent(agent)
        for i in range(self.n_lines):
            landmark = Landmark(name=f'line {i}', collide=True, movable=True, rotatable=True, shape=Line(length=self.line_length), color=Color.BLACK)
            world.add_landmark(landmark)
        for i in range(self.n_boxes):
            landmark = Landmark(name=f'box {i}', collide=True, movable=True, rotatable=True, shape=Box(length=self.box_length, width=self.box_width), color=Color.RED)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents + self.world.landmarks, self.world, env_index, self.min_dist_between_entities, (-self.world_semidim, self.world_semidim), (-self.world_semidim, self.world_semidim))

    def reward(self, agent: Agent):
        return torch.zeros(self.world.batch_dim, device=self.world.device)

    def observation(self, agent: Agent):
        return torch.zeros(self.world.batch_dim, 1, device=self.world.device) if not self.lidar else agent.sensors[0].measure(vectorized=self.vectorized_lidar)

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents + self.world.landmarks, self.world, env_index, self.min_dist_between_entities, (-self.world_semidim, self.world_semidim), (-self.world_semidim, self.world_semidim))

def reward(self, agent: Agent):
    return torch.zeros(self.world.batch_dim, device=self.world.device)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.u_range = kwargs.pop('u_range', 1)
        self.a_range = kwargs.pop('a_range', 1)
        self.obs_noise = kwargs.pop('obs_noise', 0.0)
        self.dt_delay = kwargs.pop('dt_delay', 0)
        self.min_input_norm = kwargs.pop('min_input_norm', 0.08)
        self.linear_friction = kwargs.pop('linear_friction', 0.1)
        self.pos_shaping_factor = kwargs.pop('pos_shaping_factor', 1.0)
        self.time_rew_coeff = kwargs.pop('time_rew_coeff', -0.01)
        self.energy_reward_coeff = kwargs.pop('energy_rew_coeff', 0.0)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.viewer_size = (1600, 700)
        self.viewer_zoom = 2
        self.plot_grid = True
        self.agent_radius = 0.16
        self.lab_length = 6
        self.lab_width = 3
        controller_params = [2, 6, 0.002]
        self.f_range = self.a_range + self.linear_friction
        world = World(batch_dim, device, drag=0, dt=0.05, substeps=5)
        null_action = torch.zeros(world.batch_dim, world.dim_p, device=world.device)
        self.input_queue = [null_action.clone() for _ in range(self.dt_delay)]
        self.goal = Landmark('goal', collide=False, movable=False, shape=Sphere(radius=0.06))
        world.add_landmark(self.goal)
        agent = Agent(name='agent 0', collide=True, color=Color.GREEN, render_action=True, linear_friction=self.linear_friction, shape=Sphere(radius=self.agent_radius), f_range=self.f_range, u_range=self.u_range)
        agent.controller = VelocityController(agent, world, controller_params, 'standard')
        agent.goal = self.goal
        agent.energy_rew = torch.zeros(batch_dim, device=device)
        world.add_agent(agent)
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.time_rew = self.pos_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.controller.reset(env_index)
            agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_length / 2, self.lab_length / 2), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_width / 2, self.lab_width / 2)], dim=1), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_length / 2, self.lab_length / 2), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_width / 2, self.lab_width / 2)], dim=1), batch_index=env_index)
            if env_index is None:
                landmark.pos_shaping = torch.stack([torch.linalg.vector_norm(landmark.state.pos - a.state.pos, dim=1) for a in self.world.agents], dim=1).min(dim=1)[0] * self.pos_shaping_factor
            else:
                landmark.pos_shaping[env_index] = torch.stack([torch.linalg.vector_norm(landmark.state.pos[env_index] - a.state.pos[env_index]).unsqueeze(-1) for a in self.world.agents], dim=1).min(dim=1)[0] * self.pos_shaping_factor

    def process_action(self, agent: Agent):
        self.input_queue.append(agent.action.u.clone())
        agent.action.u = self.input_queue.pop(0)
        agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, self.u_range)
        action_norm = torch.linalg.vector_norm(agent.action.u, dim=1)
        agent.action.u[action_norm < self.min_input_norm] = 0
        agent.vel_action = agent.action.u.clone()
        agent.controller.process_force()

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.pos_rew[:] = 0
            self.time_rew[:] = 0
            goal_dist = torch.stack([torch.linalg.vector_norm(self.goal.state.pos - a.state.pos, dim=1) for a in self.world.agents], dim=1).min(dim=1)[0]
            self.goal_reached = goal_dist < self.goal.shape.radius
            pos_shaping = goal_dist * self.pos_shaping_factor
            self.pos_rew[~self.goal_reached] = (self.goal.pos_shaping - pos_shaping)[~self.goal_reached]
            self.goal.pos_shaping = pos_shaping
            self.time_rew[~self.goal_reached] += self.time_rew_coeff
        agent.energy_expenditure = torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * a.f_range ** 2) for a in self.world.agents], dim=1).sum(-1)
        agent.energy_rew = -agent.energy_expenditure * self.energy_reward_coeff
        return self.pos_rew + agent.energy_rew + self.time_rew

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos]
        if self.obs_noise > 0:
            for i, obs in enumerate(observations):
                noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
                observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'energy_rew': agent.energy_rew, 'time_rew': self.time_rew}

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.controller.reset(env_index)
        agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_length / 2, self.lab_length / 2), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_width / 2, self.lab_width / 2)], dim=1), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_length / 2, self.lab_length / 2), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-self.lab_width / 2, self.lab_width / 2)], dim=1), batch_index=env_index)
        if env_index is None:
            landmark.pos_shaping = torch.stack([torch.linalg.vector_norm(landmark.state.pos - a.state.pos, dim=1) for a in self.world.agents], dim=1).min(dim=1)[0] * self.pos_shaping_factor
        else:
            landmark.pos_shaping[env_index] = torch.stack([torch.linalg.vector_norm(landmark.state.pos[env_index] - a.state.pos[env_index]).unsqueeze(-1) for a in self.world.agents], dim=1).min(dim=1)[0] * self.pos_shaping_factor

def observation(self, agent: Agent):
    observations = [agent.state.pos, agent.state.vel, agent.state.pos - self.goal.state.pos]
    if self.obs_noise > 0:
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs + noise
    return torch.cat(observations, dim=-1)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.joint_length = kwargs.pop('joint_length', 0.5)
        self.random_start_angle = kwargs.pop('random_start_angle', False)
        self.observe_joint_angle = kwargs.pop('observe_joint_angle', False)
        self.joint_angle_obs_noise = kwargs.pop('joint_angle_obs_noise', 0.0)
        self.asym_package = kwargs.pop('asym_package', True)
        self.mass_ratio = kwargs.pop('mass_ratio', 5)
        self.mass_position = kwargs.pop('mass_position', 0.75)
        self.max_speed_1 = kwargs.pop('max_speed_1', None)
        self.obs_noise = kwargs.pop('obs_noise', 0.2)
        self.rot_shaping_factor = kwargs.pop('rot_shaping_factor', 1)
        self.energy_reward_coeff = kwargs.pop('energy_reward_coeff', 0.08)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device, substeps=7 if not self.asym_package else 10, joint_force=900 if self.asym_package else 400, drag=0.25 if not self.asym_package else 0.15)
        if not self.observe_joint_angle:
            assert self.joint_angle_obs_noise == 0
        self.goal_angle = torch.pi / 2
        self.n_agents = 2
        self.agent_radius = 0.03333
        self.mass_radius = self.agent_radius * (2 / 3)
        agent = Agent(name='agent 0', shape=Sphere(self.agent_radius), u_multiplier=0.8, obs_noise=self.obs_noise, render_action=True)
        world.add_agent(agent)
        agent = Agent(name='agent 1', shape=Sphere(self.agent_radius), u_multiplier=0.8, mass=1 if self.asym_package else self.mass_ratio, max_speed=self.max_speed_1, obs_noise=self.obs_noise, render_action=True)
        world.add_agent(agent)
        self.joint = Joint(world.agents[0], world.agents[1], anchor_a=(0, 0), anchor_b=(0, 0), dist=self.joint_length, rotate_a=True, rotate_b=True, collidable=False, width=0, mass=1)
        world.add_joint(self.joint)
        if self.asym_package:

            def mass_collision_filter(e):
                return not isinstance(e.shape, Sphere)
            self.mass = Landmark(name='mass', shape=Sphere(radius=self.mass_radius), collide=False, movable=True, color=Color.BLACK, mass=self.mass_ratio, collision_filter=mass_collision_filter)
            world.add_landmark(self.mass)
            joint = Joint(self.mass, self.joint.landmark, anchor_a=(0, 0), anchor_b=(self.mass_position, 0), dist=0, rotate_a=True, rotate_b=True)
            world.add_joint(joint)
        self.rot_rew = torch.zeros(batch_dim, device=device)
        self.energy_rew = self.rot_rew.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_start_angle else 0, torch.pi / 2 if self.random_start_angle else 0)
        start_delta_x = self.joint_length / 2 * torch.cos(start_angle)
        min_x_start = 0
        max_x_start = 0
        start_delta_y = self.joint_length / 2 * torch.sin(start_angle)
        min_y_start = 0
        max_y_start = 0
        joint_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
        order = torch.randperm(self.n_agents).tolist()
        agents = [self.world.agents[i] for i in order]
        for i, agent in enumerate(agents):
            if i == 0:
                agent.set_pos(joint_pos - torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
            else:
                agent.set_pos(joint_pos + torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        if self.asym_package:
            self.mass.set_pos(joint_pos + self.mass_position * torch.cat([start_delta_x, start_delta_y], dim=1) * (1 if agents[0] == self.world.agents[0] else -1), batch_index=env_index)
        if env_index is None:
            self.joint.rot_shaping_pre = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal_angle) * self.rot_shaping_factor
        else:
            self.joint.rot_shaping_pre[env_index] = get_line_angle_dist_0_180(self.joint.landmark.state.rot[env_index], self.goal_angle) * self.rot_shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rot_rew[:] = 0
            joint_dist_to_90_rot = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal_angle)
            joint_shaping = joint_dist_to_90_rot * self.rot_shaping_factor
            self.rot_rew += self.joint.rot_shaping_pre - joint_shaping
            self.joint.rot_shaping_pre = joint_shaping
            self.energy_expenditure = torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * (a.u_range * a.u_multiplier) ** 2) for a in self.world.agents], dim=1).sum(-1)
            self.energy_rew = -self.energy_expenditure * self.energy_reward_coeff
            self.rew = self.rot_rew + self.energy_rew
        return self.rew

    def observation(self, agent: Agent):
        if self.observe_joint_angle:
            joint_angle = self.joint.landmark.state.rot
            angle_noise = torch.randn(*joint_angle.shape, device=self.world.device, dtype=torch.float32) * self.joint_angle_obs_noise if self.joint_angle_obs_noise else 0.0
            joint_angle += angle_noise
        observations = [agent.state.pos, agent.state.vel] + ([angle_to_vector(joint_angle)] if self.observe_joint_angle else [])
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs.clone() + noise
        return torch.cat(observations, dim=-1)

    def done(self):
        return torch.all(get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal_angle).unsqueeze(-1) <= 0.01, dim=1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'rot_rew': self.rot_rew, 'energy_rew': self.energy_rew}

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        from vmas.simulator import rendering
        geoms = []
        color = Color.GREEN.value
        origin = rendering.make_circle(0.01)
        xform = rendering.Transform()
        origin.add_attr(xform)
        xform.set_translation(0, 0)
        origin.set_color(*color)
        geoms.append(origin)
        return geoms

def reset_world_at(self, env_index: int=None):
    start_angle = torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-torch.pi / 2 if self.random_start_angle else 0, torch.pi / 2 if self.random_start_angle else 0)
    start_delta_x = self.joint_length / 2 * torch.cos(start_angle)
    min_x_start = 0
    max_x_start = 0
    start_delta_y = self.joint_length / 2 * torch.sin(start_angle)
    min_y_start = 0
    max_y_start = 0
    joint_pos = torch.cat([(min_x_start - max_x_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_x_start, (min_y_start - max_y_start) * torch.rand((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32) + max_y_start], dim=1)
    order = torch.randperm(self.n_agents).tolist()
    agents = [self.world.agents[i] for i in order]
    for i, agent in enumerate(agents):
        if i == 0:
            agent.set_pos(joint_pos - torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
        else:
            agent.set_pos(joint_pos + torch.cat([start_delta_x, start_delta_y], dim=1), batch_index=env_index)
    if self.asym_package:
        self.mass.set_pos(joint_pos + self.mass_position * torch.cat([start_delta_x, start_delta_y], dim=1) * (1 if agents[0] == self.world.agents[0] else -1), batch_index=env_index)
    if env_index is None:
        self.joint.rot_shaping_pre = get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal_angle) * self.rot_shaping_factor
    else:
        self.joint.rot_shaping_pre[env_index] = get_line_angle_dist_0_180(self.joint.landmark.state.rot[env_index], self.goal_angle) * self.rot_shaping_factor

def observation(self, agent: Agent):
    if self.observe_joint_angle:
        joint_angle = self.joint.landmark.state.rot
        angle_noise = torch.randn(*joint_angle.shape, device=self.world.device, dtype=torch.float32) * self.joint_angle_obs_noise if self.joint_angle_obs_noise else 0.0
        joint_angle += angle_noise
    observations = [agent.state.pos, agent.state.vel] + ([angle_to_vector(joint_angle)] if self.observe_joint_angle else [])
    for i, obs in enumerate(observations):
        noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
        observations[i] = obs.clone() + noise
    return torch.cat(observations, dim=-1)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.n_agents = kwargs.pop('n_agents', 5)
        self.with_joints = kwargs.pop('joints', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.agent_dist = 0.1
        self.agent_radius = 0.04
        world = World(batch_dim, device, dt=0.1, drag=0.25, substeps=5, collision_force=500)
        for i in range(self.n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(radius=self.agent_radius), u_multiplier=0.7, rotatable=True)
            world.add_agent(agent)
        if self.with_joints:
            for i in range(self.n_agents - 1):
                joint = Joint(world.agents[i], world.agents[i + 1], anchor_a=(1, 0), anchor_b=(-1, 0), dist=self.agent_dist, rotate_a=True, rotate_b=True, collidable=True, width=0, mass=1)
                world.add_joint(joint)
            landmark = Landmark(name='joined landmark', collide=True, movable=True, rotatable=True, shape=Box(length=self.agent_radius * 2, width=0.3), color=Color.GREEN)
            world.add_landmark(landmark)
            joint = Joint(world.agents[-1], landmark, anchor_a=(1, 0), anchor_b=(-1, 0), dist=self.agent_dist, rotate_a=False, rotate_b=False, collidable=True, width=0, mass=1)
            world.add_joint(joint)
        for i in range(5):
            landmark = Landmark(name=f'landmark {i}', collide=True, movable=True, rotatable=True, shape=Box(length=0.3, width=0.1), color=Color.RED)
            world.add_landmark(landmark)
        floor = Landmark(name='floor', collide=True, movable=False, shape=Line(length=2), color=Color.BLACK)
        world.add_landmark(floor)
        return world

    def reset_world_at(self, env_index: int=None):
        for i, agent in enumerate(self.world.agents + [self.world.landmarks[self.n_agents - 1]]):
            agent.set_pos(torch.tensor([-0.2 + (self.agent_dist + 2 * self.agent_radius) * i, 1.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        for i, landmark in enumerate(self.world.landmarks[self.n_agents + 1 if self.with_joints else 0:-1]):
            landmark.set_pos(torch.tensor([0.2 if i % 2 else -0.2, 0.6 - 0.3 * i], dtype=torch.float32, device=self.world.device), batch_index=env_index)
            landmark.set_rot(torch.tensor([torch.pi / 4 if i % 2 else -torch.pi / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        floor = self.world.landmarks[-1]
        floor.set_pos(torch.tensor([0, -1], dtype=torch.float32, device=self.world.device), batch_index=env_index)

    def reward(self, agent: Agent):
        dist2 = torch.linalg.vector_norm(agent.state.pos - self.world.landmarks[-1].state.pos, dim=1)
        return -dist2

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel] + [landmark.state.pos - agent.state.pos for landmark in self.world.landmarks], dim=-1)

def reset_world_at(self, env_index: int=None):
    for i, agent in enumerate(self.world.agents + [self.world.landmarks[self.n_agents - 1]]):
        agent.set_pos(torch.tensor([-0.2 + (self.agent_dist + 2 * self.agent_radius) * i, 1.0], dtype=torch.float32, device=self.world.device), batch_index=env_index)
    for i, landmark in enumerate(self.world.landmarks[self.n_agents + 1 if self.with_joints else 0:-1]):
        landmark.set_pos(torch.tensor([0.2 if i % 2 else -0.2, 0.6 - 0.3 * i], dtype=torch.float32, device=self.world.device), batch_index=env_index)
        landmark.set_rot(torch.tensor([torch.pi / 4 if i % 2 else -torch.pi / 4], dtype=torch.float32, device=self.world.device), batch_index=env_index)
    floor = self.world.landmarks[-1]
    floor.set_pos(torch.tensor([0, -1], dtype=torch.float32, device=self.world.device), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.green_mass = kwargs.pop('green_mass', 1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.plot_grid = True
        self.agent_radius = 0.16
        controller_params = [2, 6, 0.002]
        linear_friction = 0.1
        v_range = 1
        a_range = 1
        f_range = linear_friction + a_range
        u_range = v_range
        world = World(batch_dim, device, linear_friction=linear_friction, drag=0, dt=0.05, substeps=4)
        null_action = torch.zeros(world.batch_dim, world.dim_p, device=world.device)
        self.input_queue = [null_action.clone() for _ in range(2)]
        agent = Agent(name='agent 0', collide=False, color=Color.GREEN, render_action=True, mass=self.green_mass, f_range=f_range, u_range=u_range)
        agent.controller = VelocityController(agent, world, controller_params, 'standard')
        world.add_agent(agent)
        agent = Agent(name='agent 1', collide=False, render_action=True, u_range=u_range)
        agent.controller = VelocityController(agent, world, controller_params, 'standard')
        world.add_agent(agent)
        agent = Agent(name='agent 2', collide=False, render_action=True, f_range=30, u_range=u_range)
        agent.controller = VelocityController(agent, world, controller_params, 'standard')
        world.add_agent(agent)
        self.landmark = Landmark('landmark 0', collide=False, movable=True)
        world.add_landmark(self.landmark)
        self.energy_expenditure = torch.zeros(batch_dim, device=device)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.controller.reset(env_index)
            agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, -1), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(0, 0)], dim=1), batch_index=env_index)

    def process_action(self, agent: Agent):
        agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, agent.u_range)
        action_norm = torch.linalg.vector_norm(agent.action.u, dim=1)
        agent.action.u[action_norm < 0.08] = 0
        if agent == self.world.agents[1]:
            max_a = 1
            agent.vel_goal = agent.action.u[:, X]
            requested_a = (agent.vel_goal - agent.state.vel[:, X]) / self.world.dt
            achievable_a = torch.clamp(requested_a, -max_a, max_a)
            agent.action.u[:, X] = achievable_a * self.world.dt + agent.state.vel[:, X]
        agent.controller.process_force()

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.energy_expenditure = -torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) for a in self.world.agents], dim=1).sum(-1) * 3
        return self.energy_expenditure

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel], dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'energy_expenditure': self.energy_expenditure}

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.controller.reset(env_index)
        agent.set_pos(torch.cat([torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(-1, -1), torch.zeros((1, 1) if env_index is not None else (self.world.batch_dim, 1), device=self.world.device, dtype=torch.float32).uniform_(0, 0)], dim=1), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.green_mass = kwargs.pop('green_mass', 4)
        self.blue_mass = kwargs.pop('blue_mass', 2)
        self.mass_noise = kwargs.pop('mass_noise', 1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.plot_grid = True
        world = World(batch_dim, device)
        self.green_agent = Agent(name='agent 0', collide=False, color=Color.GREEN, render_action=True, mass=self.green_mass, f_range=1)
        world.add_agent(self.green_agent)
        self.blue_agent = Agent(name='agent 1', collide=False, render_action=True, f_range=1)
        world.add_agent(self.blue_agent)
        self.max_speed = torch.zeros(batch_dim, device=device)
        self.energy_expenditure = self.max_speed.clone()
        return world

    def reset_world_at(self, env_index: int=None):
        self.blue_agent.mass = self.blue_mass + np.random.uniform(-self.mass_noise, self.mass_noise)
        self.green_agent.mass = self.green_mass + np.random.uniform(-self.mass_noise, self.mass_noise)
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1, 1), batch_index=env_index)

    def process_action(self, agent: Agent):
        agent.action.u[:, Y] = 0

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.max_speed = torch.stack([torch.linalg.vector_norm(a.state.vel, dim=1) for a in self.world.agents], dim=1).max(dim=1)[0]
            self.energy_expenditure = -torch.stack([torch.linalg.vector_norm(a.action.u, dim=-1) / math.sqrt(self.world.dim_p * a.f_range ** 2) for a in self.world.agents], dim=1).sum(-1) * 0.17
        return self.max_speed + self.energy_expenditure

    def observation(self, agent: Agent):
        return torch.cat([agent.state.pos, agent.state.vel], dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'max_speed': self.max_speed, 'energy_expenditure': self.energy_expenditure}

def reset_world_at(self, env_index: int=None):
    self.blue_agent.mass = self.blue_mass + np.random.uniform(-self.mass_noise, self.mass_noise)
    self.green_agent.mass = self.green_mass + np.random.uniform(-self.mass_noise, self.mass_noise)
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1, 1), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        """
        Kinematic bicycle model example scenario
        """
        self.n_agents = kwargs.pop('n_agents', 2)
        width = kwargs.pop('width', 0.1)
        l_f = kwargs.pop('l_f', 0.1)
        l_r = kwargs.pop('l_r', 0.1)
        max_steering_angle = kwargs.pop('max_steering_angle', torch.deg2rad(torch.tensor(30.0)))
        max_speed = kwargs.pop('max_speed', 1.0)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device, substeps=10, collision_force=500)
        for i in range(self.n_agents):
            if i == 0:
                agent = Agent(name=f'bicycle_{i}', shape=Box(length=l_f + l_r, width=width), collide=True, render_action=True, u_range=[max_speed, max_steering_angle], u_multiplier=[1, 1], max_speed=max_speed, dynamics=KinematicBicycle(world, width=width, l_f=l_f, l_r=l_r, max_steering_angle=max_steering_angle, integration='euler'))
            else:
                agent = Agent(name=f'holo_rot_{i}', shape=Box(length=l_f + l_r, width=width), collide=True, render_action=True, u_range=[1, 1, 1], u_multiplier=[1, 1, 0.001], dynamics=HolonomicWithRotation())
            world.add_agent(agent)
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

    def reward(self, agent: Agent):
        return torch.zeros(self.world.batch_dim)

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel]
        return torch.cat(observations, dim=-1)

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        geoms: List[Geom] = []
        for agent in self.world.agents:
            geoms.append(ScenarioUtils.plot_entity_rotation(agent, env_index, length=0.1))
        return geoms

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

def reward(self, agent: Agent):
    return torch.zeros(self.world.batch_dim)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        """
        Differential drive example scenario
        Run this file to try it out

        The first agent has differential drive dynamics.
        You can control its forward input with the LEFT and RIGHT arrows.
        You can control its rotation with UP and DOWN.

        The second agent has standard vmas holonomic dynamics.
        You can control it with WASD
        You can control its rotation with Q and E.

        """
        self.plot_grid = True
        self.n_agents = kwargs.pop('n_agents', 2)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device, substeps=10)
        for i in range(self.n_agents):
            if i == 0:
                agent = Agent(name=f'diff_drive_{i}', collide=True, render_action=True, u_range=[1, 1], u_multiplier=[1, 1], dynamics=DiffDrive(world, integration='rk4'))
            else:
                agent = Agent(name=f'holo_rot_{i}', collide=True, render_action=True, u_range=[1, 1, 1], u_multiplier=[1, 1, 0.001], dynamics=HolonomicWithRotation())
            world.add_agent(agent)
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

    def reward(self, agent: Agent):
        return torch.zeros(self.world.batch_dim)

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel]
        return torch.cat(observations, dim=-1)

    def extra_render(self, env_index: int=0) -> 'List[Geom]':
        geoms: List[Geom] = []
        for agent in self.world.agents:
            geoms.append(ScenarioUtils.plot_entity_rotation(agent, env_index, length=0.1))
        return geoms

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=0.1, x_bounds=(-1, 1), y_bounds=(-1, 1))

def reward(self, agent: Agent):
    return torch.zeros(self.world.batch_dim)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        self.u_range = kwargs.pop('u_range', 1)
        self.a_range = kwargs.pop('a_range', 1)
        self.obs_noise = kwargs.pop('obs_noise', 0.0)
        self.dt_delay = kwargs.pop('dt_delay', 0)
        self.min_input_norm = kwargs.pop('min_input_norm', 0.08)
        self.linear_friction = kwargs.pop('linear_friction', 0.1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.agent_radius = 0.16
        self.desired_radius = 1.5
        self.viewer_zoom = 2
        world = World(batch_dim, device, linear_friction=self.linear_friction, dt=0.05, drag=0)
        controller_params = [2, 6, 0.002]
        self.f_range = self.a_range + self.linear_friction
        null_action = torch.zeros(world.batch_dim, world.dim_p, device=world.device)
        self.input_queue = [null_action.clone() for _ in range(self.dt_delay)]
        self.agent = Agent(name='agent_0', shape=Sphere(self.agent_radius), f_range=self.f_range, u_range=self.u_range, render_action=True)
        self.agent.controller = VelocityController(self.agent, world, controller_params, 'standard')
        world.add_agent(self.agent)
        self.pos_rew = torch.zeros(batch_dim, device=device)
        self.dot_product = self.pos_rew.clone()
        return world

    def process_action(self, agent: Agent):
        self.input_queue.append(agent.action.u.clone())
        agent.action.u = self.input_queue.pop(0)
        agent.action.u = TorchUtils.clamp_with_norm(agent.action.u, self.u_range)
        action_norm = torch.linalg.vector_norm(agent.action.u, dim=1)
        agent.action.u[action_norm < self.min_input_norm] = 0
        agent.vel_action = agent.action.u.clone()
        agent.controller.process_force()

    def reset_world_at(self, env_index: int=None):
        self.agent.controller.reset(env_index)
        self.agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.desired_radius, self.desired_radius), batch_index=env_index)

    def reward(self, agent: Agent):
        closest_point = self.get_closest_point_circle(agent)
        self.pos_rew = -torch.linalg.vector_norm(agent.state.pos - closest_point, dim=1) ** 0.5 * 1
        tangent = self.get_tangent_to_circle(agent, closest_point)
        self.dot_product = torch.einsum('bs,bs->b', tangent, agent.state.vel) * 0.5
        return self.pos_rew + self.dot_product

    def get_closest_point_circle(self, agent: Agent):
        pos_norm = torch.linalg.vector_norm(agent.state.pos, dim=1)
        agent_pos_normalized = agent.state.pos / pos_norm.unsqueeze(-1)
        agent_pos_normalized *= self.desired_radius
        return torch.nan_to_num(agent_pos_normalized)

    def get_next_closest_point_circle(self, agent: Agent):
        closest_point = self.get_closest_point_circle(agent)
        angle = torch.atan2(closest_point[:, Y], closest_point[:, X])
        angle += torch.pi / 24
        new_point = torch.stack([torch.cos(angle), torch.sin(angle)], dim=1) * self.desired_radius
        return new_point

    def get_tangent_to_circle(self, agent: Agent, closest_point=None):
        if closest_point is None:
            closest_point = self.get_closest_point_circle(agent)
        distance_to_circle = agent.state.pos - closest_point
        inside_circle = (torch.linalg.vector_norm(agent.state.pos, dim=1) < self.desired_radius,)
        angle_90 = torch.tensor(torch.pi / 2, device=self.world.device).expand(self.world.batch_dim)
        rotated_vector_90 = TorchUtils.rotate_vector(distance_to_circle, angle_90)
        rotated_vector_neg_90 = TorchUtils.rotate_vector(distance_to_circle, -angle_90)
        rotated_vector = rotated_vector_90
        rotated_vector[inside_circle] = rotated_vector_neg_90[inside_circle]
        angle = rotated_vector / torch.linalg.vector_norm(rotated_vector, dim=1).unsqueeze(-1)
        angle = torch.nan_to_num(angle)
        return angle

    def observation(self, agent: Agent):
        observations = [agent.state.pos, agent.state.vel, agent.state.pos]
        for i, obs in enumerate(observations):
            noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
            observations[i] = obs + noise
        return torch.cat(observations, dim=-1)

    def info(self, agent: Agent) -> Dict[str, Tensor]:
        return {'pos_rew': self.pos_rew, 'dot_product': self.dot_product}

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        color = Color.BLACK.value
        circle = rendering.make_circle(self.desired_radius, filled=False)
        xform = rendering.Transform()
        circle.add_attr(xform)
        xform.set_translation(0, 0)
        circle.set_color(*color)
        geoms.append(circle)
        tangent = self.get_tangent_to_circle(self.agent)
        color = Color.BLACK.value
        circle = rendering.Line((0, 0), tangent[env_index], width=1)
        xform = rendering.Transform()
        circle.add_attr(xform)
        circle.set_color(*color)
        geoms.append(circle)
        return geoms

def reset_world_at(self, env_index: int=None):
    self.agent.controller.reset(env_index)
    self.agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.desired_radius, self.desired_radius), batch_index=env_index)

def get_tangent_to_circle(self, agent: Agent, closest_point=None):
    if closest_point is None:
        closest_point = self.get_closest_point_circle(agent)
    distance_to_circle = agent.state.pos - closest_point
    inside_circle = (torch.linalg.vector_norm(agent.state.pos, dim=1) < self.desired_radius,)
    angle_90 = torch.tensor(torch.pi / 2, device=self.world.device).expand(self.world.batch_dim)
    rotated_vector_90 = TorchUtils.rotate_vector(distance_to_circle, angle_90)
    rotated_vector_neg_90 = TorchUtils.rotate_vector(distance_to_circle, -angle_90)
    rotated_vector = rotated_vector_90
    rotated_vector[inside_circle] = rotated_vector_neg_90[inside_circle]
    angle = rotated_vector / torch.linalg.vector_norm(rotated_vector, dim=1).unsqueeze(-1)
    angle = torch.nan_to_num(angle)
    return angle

def observation(self, agent: Agent):
    observations = [agent.state.pos, agent.state.vel, agent.state.pos]
    for i, obs in enumerate(observations):
        noise = torch.zeros(*obs.shape, device=self.world.device).uniform_(-self.obs_noise, self.obs_noise)
        observations[i] = obs + noise
    return torch.cat(observations, dim=-1)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 3)
        n_adversaries = kwargs.pop('n_adversaries', 1)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert n_agents > n_adversaries
        world = World(batch_dim=batch_dim, device=device)
        num_adversaries = n_adversaries
        num_landmarks = n_agents - 1
        for i in range(n_agents):
            adversary = True if i < num_adversaries else False
            name = f'adversary_{i}' if adversary else f'agent_{i - num_adversaries}'
            agent = Agent(name=name, collide=False, shape=Sphere(radius=0.15), color=Color.RED if adversary else Color.BLUE, adversary=adversary)
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=False, shape=Sphere(radius=0.08), color=Color.BLACK)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        if env_index is None:
            goal = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
            goal.color = Color.GREEN
            for agent in self.world.agents:
                agent.goal = goal
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def good_agents(self):
        return [agent for agent in self.world.agents if not agent.adversary]

    def adversaries(self):
        return [agent for agent in self.world.agents if agent.adversary]

    def reward(self, agent: Agent):
        return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

    def agent_reward(self, agent: Agent):
        shaped_reward = True
        shaped_adv_reward = True
        adversary_agents = self.adversaries()
        if shaped_adv_reward:
            adv_rew = torch.sum(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) for a in adversary_agents], dim=1), dim=-1)
        else:
            adv_rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            for a in adversary_agents:
                is_too_close = torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) < 2 * a.goal.size
                adv_rew[is_too_close] -= 5
        good_agents = self.good_agents()
        if shaped_reward:
            pos_rew = -torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) for a in good_agents], dim=1), dim=-1)[0]
        else:
            pos_rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            is_close_enough = torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) for a in good_agents], dim=1), dim=-1) < 2 * agent.goal.size
            pos_rew[is_close_enough] += 5
            pos_rew -= torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) for a in good_agents], dim=1), dim=-1)
        return pos_rew + adv_rew

    def adversary_reward(self, agent: Agent):
        shaped_reward = True
        if shaped_reward:
            return -torch.sqrt(torch.sum(torch.square(agent.state.pos - agent.goal.state.pos), dim=-1))
        else:
            adv_rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            close_enough = torch.sqrt(torch.sum(torch.square(agent.state.pos - agent.goal.state.pos), dim=-1)) < 2 * agent.goal.size
            adv_rew[close_enough] += 5
            return adv_rew

    def observation(self, agent: Agent):
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        other_pos = []
        for other in self.world.agents:
            if other is agent:
                continue
            other_pos.append(other.state.pos - agent.state.pos)
        if not agent.adversary:
            return torch.cat([agent.goal.state.pos - agent.state.pos, *entity_pos, *other_pos], dim=-1)
        else:
            return torch.cat([*entity_pos, *other_pos], dim=-1)

def reset_world_at(self, env_index: int=None):
    if env_index is None:
        goal = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
        goal.color = Color.GREEN
        for agent in self.world.agents:
            agent.goal = goal
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        world = World(batch_dim=batch_dim, device=device, x_semidim=1, y_semidim=1, dim_c=4)
        num_good_agents = kwargs.pop('num_good_agents', 2)
        num_adversaries = kwargs.pop('num_adversaries', 4)
        num_landmarks = kwargs.pop('num_landmarks', 1)
        num_food = kwargs.pop('num_food', 2)
        num_forests = kwargs.pop('num_forests', 2)
        num_agents = num_good_agents + num_adversaries
        ScenarioUtils.check_kwargs_consumed(kwargs)
        for i in range(num_agents):
            adversary = True if i < num_adversaries else False
            leader = True if i == 0 else False
            name = 'lead_adversary_0' if leader else f'adversary_{i}' if adversary else f'agent_{i - num_adversaries}'
            agent = Agent(name=name, collide=True, shape=Sphere(radius=0.075 if adversary else 0.045), u_multiplier=3.0 if adversary else 4.0, max_speed=1.0 if adversary else 1.3, color=Color.RED if adversary else Color.GREEN, adversary=adversary, silent=not leader)
            agent.leader = leader
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=True, shape=Sphere(radius=0.2))
            landmark.boundary = False
            world.add_landmark(landmark)
        world.food = []
        for i in range(num_food):
            landmark = Landmark(name=f'food {i}', collide=False, shape=Sphere(radius=0.03))
            landmark.boundary = False
            world.food.append(landmark)
            world.add_landmark(landmark)
        world.forests = []
        for i in range(num_forests):
            landmark = Landmark(name=f'forest {i}', collide=False, shape=Sphere(radius=0.3))
            landmark.boundary = False
            world.forests.append(landmark)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        if env_index is None:
            for agent in self.world.agents:
                agent.color = torch.tensor([0.45, 0.95, 0.45], device=self.world.device, dtype=torch.float32) if not agent.adversary else torch.tensor([0.95, 0.45, 0.45], device=self.world.device, dtype=torch.float32)
                agent.color -= torch.tensor([0.3, 0.3, 0.3], device=self.world.device, dtype=torch.float32) if agent.leader else torch.tensor([0, 0, 0], device=self.world.device, dtype=torch.float32)
            for landmark in self.world.landmarks:
                landmark.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            for landmark in self.world.food:
                landmark.color = torch.tensor([0.15, 0.15, 0.65], device=self.world.device, dtype=torch.float32)
            for landmark in self.world.forests:
                landmark.color = torch.tensor([0.6, 0.9, 0.6], device=self.world.device, dtype=torch.float32)
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-0.9, 0.9), batch_index=env_index)

    def is_collision(self, agent1: Agent, agent2: Agent):
        delta_pos = agent1.state.pos - agent2.state.pos
        dist = torch.sqrt(torch.sum(torch.square(delta_pos), dim=-1))
        dist_min = agent1.shape.radius + agent2.shape.radius
        return dist < dist_min

    def good_agents(self):
        return [agent for agent in self.world.agents if not agent.adversary]

    def adversaries(self):
        return [agent for agent in self.world.agents if agent.adversary]

    def reward(self, agent: Agent):
        main_reward = self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)
        return main_reward

    def agent_reward(self, agent: Agent):
        rew = rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        shape = False
        adversaries = self.adversaries()
        if shape:
            for adv in adversaries:
                rew += 0.1 * torch.sqrt(torch.sum(torch.square(agent.state.pos - adv.state.pos), dim=-1))
        if agent.collide:
            for a in adversaries:
                rew[self.is_collision(a, agent)] -= 5
        for food in self.world.food:
            rew[self.is_collision(agent, food)] += 2
        rew -= 0.05 * torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(food.state.pos - agent.state.pos), dim=-1)) for food in self.world.food], dim=1), dim=-1)[0]
        return rew

    def adversary_reward(self, agent: Agent):
        rew = rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        shape = True
        agents = self.good_agents()
        adversaries = self.adversaries()
        if shape:
            rew -= 0.1 * torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.state.pos), dim=-1)) for a in agents], dim=1), dim=-1)[0]
        if agent.collide:
            for ag in agents:
                for adv in adversaries:
                    rew[self.is_collision(ag, adv)] += 5
        return rew

    def observation(self, agent: Agent):
        entity_pos = []
        for entity in self.world.landmarks:
            if not entity.boundary:
                entity_pos.append(entity.state.pos - agent.state.pos)
        in_forest = torch.full((self.world.batch_dim, len(self.world.forests)), -1, device=self.world.device)
        inf = torch.full((self.world.batch_dim, len(self.world.forests)), False, device=self.world.device)
        for i in range(len(self.world.forests)):
            index = self.is_collision(agent, self.world.forests[i])
            in_forest[index][:, i] = 1
            inf[index][:, i] = True
        food_pos = []
        for entity in self.world.food:
            if not entity.boundary:
                food_pos.append(entity.state.pos - agent.state.pos)
        other_pos = []
        other_vel = []
        for other in self.world.agents:
            if other is agent:
                continue
            oth_f = torch.stack([self.is_collision(other, self.world.forests[i]) for i in range(len(self.world.forests))], dim=1)
            for i in range(len(self.world.forests)):
                other_info = torch.zeros(self.world.batch_dim, 4, device=self.world.device, dtype=torch.float32)
                index = torch.logical_and(inf[:, i], oth_f[:, i])
                other_info[index, :2] = other.state.pos[index] - agent.state.pos[index]
                if not other.adversary:
                    other_info[index, 2:] = other.state.vel[index]
                if agent.leader:
                    other_info[~index, :2] = other.state.pos[~index] - agent.state.pos[~index]
                    if not other.adversary:
                        other_info[~index, 2:] = other.state.vel[~index]
                other_pos.append(other_info[:, :2])
                other_vel.append(other_info[:, 2:])
        prey_forest = torch.full((self.world.batch_dim, len(self.good_agents())), -1, device=self.world.device)
        ga = self.good_agents()
        for i, a in enumerate(ga):
            index = torch.any(torch.stack([self.is_collision(a, f) for f in self.world.forests], dim=1), dim=-1)
            prey_forest[index][:, i] = 1
        prey_forest = torch.full((self.world.batch_dim, len(self.world.forests)), -1, device=self.world.device)
        for i, f in enumerate(self.world.forests):
            index = torch.any(torch.stack([self.is_collision(a, f) for a in ga], dim=1), dim=-1)
            prey_forest[index, i] = 1
        comm = self.world.agents[0].state.c
        if agent.adversary and (not agent.leader):
            return torch.cat([agent.state.vel, agent.state.pos, *entity_pos, *other_pos, *other_vel, in_forest, comm], dim=-1)
        if agent.leader:
            return torch.cat([agent.state.vel, agent.state.pos, *entity_pos, *other_pos, *other_vel, in_forest, comm], dim=-1)
        else:
            return torch.cat([agent.state.vel, agent.state.pos, *entity_pos, *other_pos, *other_vel, in_forest], dim=-1)

def reset_world_at(self, env_index: int=None):
    if env_index is None:
        for agent in self.world.agents:
            agent.color = torch.tensor([0.45, 0.95, 0.45], device=self.world.device, dtype=torch.float32) if not agent.adversary else torch.tensor([0.95, 0.45, 0.45], device=self.world.device, dtype=torch.float32)
            agent.color -= torch.tensor([0.3, 0.3, 0.3], device=self.world.device, dtype=torch.float32) if agent.leader else torch.tensor([0, 0, 0], device=self.world.device, dtype=torch.float32)
        for landmark in self.world.landmarks:
            landmark.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
        for landmark in self.world.food:
            landmark.color = torch.tensor([0.15, 0.15, 0.65], device=self.world.device, dtype=torch.float32)
        for landmark in self.world.forests:
            landmark.color = torch.tensor([0.6, 0.9, 0.6], device=self.world.device, dtype=torch.float32)
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-0.9, 0.9), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim=batch_dim, device=device)
        num_agents = 2
        num_adversaries = 1
        num_landmarks = 2
        for i in range(num_agents):
            adversary = True if i < num_adversaries else False
            name = f'adversary_{i}' if adversary else f'agent_{i - num_adversaries}'
            agent = Agent(name=name, collide=True, adversary=adversary)
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=False)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        if env_index is None:
            for i, landmark in enumerate(self.world.landmarks):
                landmark.color = torch.tensor([0.1, 0.1, 0.1], device=self.world.device, dtype=torch.float32)
                landmark.color[i + 1] += 0.8
                landmark.index = i
            goal = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
            for agent in self.world.agents:
                agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
                if agent.adversary:
                    agent.color = torch.tensor([0.75, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
                else:
                    j = goal.index
                    agent.color[j + 1] += 0.5
                agent.goal = goal
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def reward(self, agent: Agent):
        return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

    def agent_reward(self, agent: Agent):
        return -torch.sqrt(torch.sum(torch.square(agent.state.pos - agent.goal.state.pos), dim=-1))

    def adversary_reward(self, agent: Agent):
        pos_rew = torch.min(torch.stack([torch.sqrt(torch.sum(torch.square(a.state.pos - a.goal.state.pos), dim=-1)) for a in self.world.agents if not a.adversary], dim=1), dim=-1)[0]
        neg_rew = -torch.sqrt(torch.sum(torch.square(agent.goal.state.pos - agent.state.pos), dim=-1))
        return pos_rew + neg_rew

    def observation(self, agent: Agent):
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        entity_color = []
        for entity in self.world.landmarks:
            entity_color.append(entity.color.repeat(self.world.batch_dim, 1))
        other_pos = []
        for other in self.world.agents:
            if other is agent:
                continue
            other_pos.append(other.state.pos - agent.state.pos)
        if not agent.adversary:
            return torch.cat([agent.state.vel, agent.goal.state.pos - agent.state.pos, agent.color.repeat(self.world.batch_dim, 1), *entity_pos, *entity_color, *other_pos], dim=-1)
        else:
            return torch.cat([agent.state.vel, *entity_pos, *other_pos], dim=-1)

def reset_world_at(self, env_index: int=None):
    if env_index is None:
        for i, landmark in enumerate(self.world.landmarks):
            landmark.color = torch.tensor([0.1, 0.1, 0.1], device=self.world.device, dtype=torch.float32)
            landmark.color[i + 1] += 0.8
            landmark.index = i
        goal = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
        for agent in self.world.agents:
            agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            if agent.adversary:
                agent.color = torch.tensor([0.75, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            else:
                j = goal.index
                agent.color[j + 1] += 0.5
            agent.goal = goal
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        num_agents = kwargs.pop('n_agents', 3)
        obs_agents = kwargs.pop('obs_agents', True)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.obs_agents = obs_agents
        world = World(batch_dim=batch_dim, device=device)
        num_landmarks = num_agents
        for i in range(num_agents):
            agent = Agent(name=f'agent_{i}', collide=True, shape=Sphere(radius=0.15), color=Color.BLUE)
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=False, color=Color.BLACK)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            for single_agent in self.world.agents:
                for landmark in self.world.landmarks:
                    closest = torch.min(torch.stack([torch.linalg.vector_norm(a.state.pos - landmark.state.pos, dim=1) for a in self.world.agents], dim=-1), dim=-1)[0]
                    self.rew -= closest
                if single_agent.collide:
                    for a in self.world.agents:
                        if a != single_agent:
                            self.rew[self.world.is_overlapping(a, single_agent)] -= 1
        return self.rew

    def observation(self, agent: Agent):
        landmark_pos = []
        for landmark in self.world.landmarks:
            landmark_pos.append(landmark.state.pos - agent.state.pos)
        other_pos = []
        for other in self.world.agents:
            if other != agent:
                other_pos.append(other.state.pos - agent.state.pos)
        return torch.cat([agent.state.pos, agent.state.vel, *landmark_pos, *(other_pos if self.obs_agents else [])], dim=-1)

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        dim_c = kwargs.pop('dim_c', 4)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        assert dim_c > 0
        world = World(batch_dim=batch_dim, device=device, dim_c=dim_c)
        num_agents = 3
        num_adversaries = 1
        for i in range(num_agents):
            adversary = True if i < num_adversaries else False
            speaker = True if i == 2 else False
            agent = Agent(name='eve_0' if adversary else 'alice_0' if speaker else 'bob_0', collide=False, movable=False, color=Color.RED if adversary else Color.GREEN if speaker else Color.BLUE, adversary=adversary, silent=False)
            agent.speaker = speaker
            world.add_agent(agent)
        return world

    def reset_world_at(self, env_index: int=None):
        key = torch.randint(0, 2, (self.world.batch_dim, self.world.dim_c), device=self.world.device)
        secret = torch.randint(0, 2, (self.world.batch_dim, self.world.dim_c), device=self.world.device)
        if env_index is None:
            for agent in self.world.agents:
                agent.key = None if not agent.speaker else key
                agent.secret = secret
                agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        else:
            for agent in self.world.agents:
                if agent.speaker:
                    agent.key[env_index] = key[env_index]
                agent.secret[env_index] = secret[env_index]

    def good_listeners(self):
        return [agent for agent in self.world.agents if not agent.adversary and (not agent.speaker)]

    def good_agents(self):
        return [agent for agent in self.world.agents if not agent.adversary]

    def adversaries(self):
        return [agent for agent in self.world.agents if agent.adversary]

    def reward(self, agent: Agent):
        return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

    def agent_reward(self, agent: Agent):
        good_listeners = self.good_listeners()
        adversaries = self.adversaries()
        good_rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        adv_rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        for a in good_listeners:
            zero_comms = torch.all(a.state.c == torch.zeros(self.world.batch_dim, self.world.dim_c, device=self.world.device, dtype=torch.float32), dim=-1)
            good_rew[~zero_comms] -= torch.sum(torch.square(a.state.c - agent.secret), dim=-1)[~zero_comms]
        for a in adversaries:
            zero_comms = torch.all(a.state.c == torch.zeros(self.world.batch_dim, self.world.dim_c, device=self.world.device, dtype=torch.float32), dim=-1)
            adv_rew[~zero_comms] += torch.sum(torch.square(a.state.c - agent.secret), dim=-1)[~zero_comms]
        return adv_rew + good_rew

    def adversary_reward(self, agent: Agent):
        rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        zero_comms = torch.all(agent.state.c == torch.zeros(self.world.batch_dim, self.world.dim_c, device=self.world.device, dtype=torch.float32), dim=-1)
        rew[~zero_comms] -= torch.sum(torch.square(agent.state.c - agent.secret), dim=-1)[~zero_comms]
        return rew

    def observation(self, agent: Agent):
        comm = []
        for other in self.world.agents:
            if other is agent or not other.speaker:
                continue
            comm.append(other.state.c)
        key = self.world.agents[2].key
        secret = self.world.agents[0].secret
        if agent.speaker:
            return torch.cat([secret, key], dim=-1).to(torch.float)
        if not agent.speaker and (not agent.adversary):
            return torch.cat([key, *comm], dim=-1).to(torch.float)
        if not agent.speaker and agent.adversary:
            return torch.cat([*comm], dim=-1).to(torch.float)

def reset_world_at(self, env_index: int=None):
    key = torch.randint(0, 2, (self.world.batch_dim, self.world.dim_c), device=self.world.device)
    secret = torch.randint(0, 2, (self.world.batch_dim, self.world.dim_c), device=self.world.device)
    if env_index is None:
        for agent in self.world.agents:
            agent.key = None if not agent.speaker else key
            agent.secret = secret
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    else:
        for agent in self.world.agents:
            if agent.speaker:
                agent.key[env_index] = key[env_index]
            agent.secret[env_index] = secret[env_index]

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        num_good_agents = kwargs.pop('num_good_agents', 1)
        num_adversaries = kwargs.pop('num_adversaries', 3)
        num_landmarks = kwargs.pop('num_landmarks', 2)
        self.shape_agent_rew = kwargs.pop('shape_agent_rew', False)
        self.shape_adversary_rew = kwargs.pop('shape_adversary_rew', False)
        self.agents_share_rew = kwargs.pop('agents_share_rew', False)
        self.adversaries_share_rew = kwargs.pop('adversaries_share_rew', True)
        self.observe_same_team = kwargs.pop('observe_same_team', True)
        self.observe_pos = kwargs.pop('observe_pos', True)
        self.observe_vel = kwargs.pop('observe_vel', True)
        self.bound = kwargs.pop('bound', 1.0)
        self.respawn_at_catch = kwargs.pop('respawn_at_catch', False)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.visualize_semidims = False
        world = World(batch_dim=batch_dim, device=device, x_semidim=self.bound, y_semidim=self.bound, substeps=10, collision_force=500)
        num_agents = num_adversaries + num_good_agents
        self.adversary_radius = 0.075
        for i in range(num_agents):
            adversary = True if i < num_adversaries else False
            name = f'adversary_{i}' if adversary else f'agent_{i - num_adversaries}'
            agent = Agent(name=name, collide=True, shape=Sphere(radius=self.adversary_radius if adversary else 0.05), u_multiplier=3.0 if adversary else 4.0, max_speed=1.0 if adversary else 1.3, color=Color.RED if adversary else Color.GREEN, adversary=adversary)
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=True, shape=Sphere(radius=0.2), color=Color.BLACK)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.bound, self.bound), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-(self.bound - 0.1), self.bound - 0.1), batch_index=env_index)

    def is_collision(self, agent1: Agent, agent2: Agent):
        delta_pos = agent1.state.pos - agent2.state.pos
        dist = torch.linalg.vector_norm(delta_pos, dim=-1)
        dist_min = agent1.shape.radius + agent2.shape.radius
        return dist < dist_min

    def good_agents(self):
        return [agent for agent in self.world.agents if not agent.adversary]

    def adversaries(self):
        return [agent for agent in self.world.agents if agent.adversary]

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            for a in self.world.agents:
                a.rew = self.adversary_reward(a) if a.adversary else self.agent_reward(a)
            self.agents_rew = torch.stack([a.rew for a in self.good_agents()], dim=-1).sum(-1)
            self.adverary_rew = torch.stack([a.rew for a in self.adversaries()], dim=-1).sum(-1)
            if self.respawn_at_catch:
                for a in self.good_agents():
                    for adv in self.adversaries():
                        coll = self.is_collision(a, adv)
                        a.state.pos[coll] = torch.zeros((self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.bound, self.bound)[coll]
                        a.state.vel[coll] = 0.0
        if agent.adversary:
            if self.adversaries_share_rew:
                return self.adverary_rew
            else:
                return agent.rew
        elif self.agents_share_rew:
            return self.agents_rew
        else:
            return agent.rew

    def agent_reward(self, agent: Agent):
        rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        adversaries = self.adversaries()
        if self.shape_agent_rew:
            for adv in adversaries:
                rew += 0.1 * torch.linalg.vector_norm(agent.state.pos - adv.state.pos, dim=-1)
        if agent.collide:
            for a in adversaries:
                rew[self.is_collision(a, agent)] -= 10
        return rew

    def adversary_reward(self, agent: Agent):
        rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        agents = self.good_agents()
        if self.shape_adversary_rew:
            rew -= 0.1 * torch.min(torch.stack([torch.linalg.vector_norm(a.state.pos - agent.state.pos, dim=-1) for a in agents], dim=-1), dim=-1)[0]
        if agent.collide:
            for ag in agents:
                rew[self.is_collision(ag, agent)] += 10
        return rew

    def observation(self, agent: Agent):
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        other_pos = []
        other_vel = []
        for other in self.world.agents:
            if other is agent:
                continue
            if agent.adversary and (not other.adversary):
                other_pos.append(other.state.pos - agent.state.pos)
                other_vel.append(other.state.vel)
            elif not agent.adversary and (not other.adversary) and self.observe_same_team:
                other_pos.append(other.state.pos - agent.state.pos)
                other_vel.append(other.state.vel)
            elif not agent.adversary and other.adversary:
                other_pos.append(other.state.pos - agent.state.pos)
            elif agent.adversary and other.adversary and self.observe_same_team:
                other_pos.append(other.state.pos - agent.state.pos)
        return torch.cat([*([agent.state.vel] if self.observe_vel else []), *([agent.state.pos] if self.observe_pos else []), *entity_pos, *other_pos, *other_vel], dim=-1)

    def extra_render(self, env_index: int=0):
        from vmas.simulator import rendering
        geoms = []
        for i in range(4):
            geom = Line(length=2 * (self.bound - self.adversary_radius + self.adversary_radius * 2)).get_geometry()
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(0.0 if i % 2 else self.bound + self.adversary_radius if i == 0 else -self.bound - self.adversary_radius, 0.0 if not i % 2 else self.bound + self.adversary_radius if i == 1 else -self.bound - self.adversary_radius)
            xform.set_rotation(torch.pi / 2 if not i % 2 else 0.0)
            color = Color.BLACK.value
            if isinstance(color, torch.Tensor) and len(color.shape) > 1:
                color = color[env_index]
            geom.set_color(*color)
            geoms.append(geom)
        return geoms

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-self.bound, self.bound), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-(self.bound - 0.1), self.bound - 0.1), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim=batch_dim, device=device, dim_c=10)
        n_agents = 2
        n_landmarks = 3
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', collide=False, silent=False)
            world.add_agent(agent)
        for i in range(n_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=False)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        if env_index is None:
            for agent in self.world.agents:
                agent.goal_a = None
                agent.goal_b = None
            self.world.agents[0].goal_a = self.world.agents[1]
            self.world.agents[0].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
            self.world.agents[1].goal_a = self.world.agents[0]
            self.world.agents[1].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
            for agent in self.world.agents:
                agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[0].color = torch.tensor([0.75, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[1].color = torch.tensor([0.25, 0.75, 0.25], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[2].color = torch.tensor([0.25, 0.25, 0.75], device=self.world.device, dtype=torch.float32)
            self.world.agents[0].goal_a.color = self.world.agents[0].goal_b.color
            self.world.agents[1].goal_a.color = self.world.agents[1].goal_b.color
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device)
            for a in self.world.agents:
                if a.goal_a is None or a.goal_b is None:
                    return torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
                self.rew += -torch.sqrt(torch.sum(torch.square(a.goal_a.state.pos - a.goal_b.state.pos), dim=-1))
        return self.rew

    def observation(self, agent: Agent):
        goal_color = agent.goal_b.color
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        comm = []
        for other in self.world.agents:
            if other is agent:
                continue
            comm.append(other.state.c)
        return torch.cat([agent.state.vel, *entity_pos, goal_color.repeat(self.world.batch_dim, 1), *comm], dim=-1)

def reset_world_at(self, env_index: int=None):
    if env_index is None:
        for agent in self.world.agents:
            agent.goal_a = None
            agent.goal_b = None
        self.world.agents[0].goal_a = self.world.agents[1]
        self.world.agents[0].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
        self.world.agents[1].goal_a = self.world.agents[0]
        self.world.agents[1].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
        for agent in self.world.agents:
            agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[0].color = torch.tensor([0.75, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[1].color = torch.tensor([0.25, 0.75, 0.25], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[2].color = torch.tensor([0.25, 0.25, 0.75], device=self.world.device, dtype=torch.float32)
        self.world.agents[0].goal_a.color = self.world.agents[0].goal_b.color
        self.world.agents[1].goal_a.color = self.world.agents[1].goal_b.color
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim=batch_dim, device=device, dim_c=3)
        num_agents = 2
        num_landmarks = 3
        for i in range(num_agents):
            speaker = True if i == 0 else False
            name = 'speaker_0' if speaker else 'listener_0'
            agent = Agent(name=name, collide=False, movable=False if speaker else True, silent=False if speaker else True, shape=Sphere(radius=0.075))
            world.add_agent(agent)
        for i in range(num_landmarks):
            landmark = Landmark(name=f'landmark {i}', collide=False, shape=Sphere(radius=0.04))
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        if env_index is None:
            for agent in self.world.agents:
                agent.goal_a = None
                agent.goal_b = None
            self.world.agents[0].goal_a = self.world.agents[1]
            self.world.agents[0].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
            for agent in self.world.agents:
                agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[0].color = torch.tensor([0.65, 0.15, 0.15], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[1].color = torch.tensor([0.15, 0.65, 0.15], device=self.world.device, dtype=torch.float32)
            self.world.landmarks[2].color = torch.tensor([0.15, 0.15, 0.65], device=self.world.device, dtype=torch.float32)
            self.world.agents[0].goal_a.color = self.world.agents[0].goal_b.color + torch.tensor([0.45, 0.45, 0.45], device=self.world.device, dtype=torch.float32)
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device)
            for _ in self.world.agents:
                a = self.world.agents[0]
                self.rew += -torch.sqrt(torch.sum(torch.square(a.goal_a.state.pos - a.goal_b.state.pos), dim=-1))
        return self.rew

    def observation(self, agent):
        goal_color = torch.zeros(3, device=self.world.device, dtype=torch.float32)
        if agent.goal_b is not None:
            goal_color = agent.goal_b.color
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        comm = []
        for other in self.world.agents:
            if other is agent or other.state.c is None:
                continue
            comm.append(other.state.c)
        if not agent.movable:
            return goal_color.repeat(self.world.batch_dim, 1)
        if agent.silent:
            return torch.cat([agent.state.vel, *entity_pos, *comm], dim=-1)

def reset_world_at(self, env_index: int=None):
    if env_index is None:
        for agent in self.world.agents:
            agent.goal_a = None
            agent.goal_b = None
        self.world.agents[0].goal_a = self.world.agents[1]
        self.world.agents[0].goal_b = self.world.landmarks[torch.randint(0, len(self.world.landmarks), (1,)).item()]
        for agent in self.world.agents:
            agent.color = torch.tensor([0.25, 0.25, 0.25], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[0].color = torch.tensor([0.65, 0.15, 0.15], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[1].color = torch.tensor([0.15, 0.65, 0.15], device=self.world.device, dtype=torch.float32)
        self.world.landmarks[2].color = torch.tensor([0.15, 0.15, 0.65], device=self.world.device, dtype=torch.float32)
        self.world.agents[0].goal_a.color = self.world.agents[0].goal_b.color + torch.tensor([0.45, 0.45, 0.45], device=self.world.device, dtype=torch.float32)
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        ScenarioUtils.check_kwargs_consumed(kwargs)
        world = World(batch_dim, device)
        for i in range(1):
            agent = Agent(name=f'agent_{i}', collide=False, color=Color.GRAY)
            world.add_agent(agent)
        for i in range(1):
            landmark = Landmark(name=f'landmark {i}', collide=False, color=Color.RED)
            world.add_landmark(landmark)
        return world

    def reset_world_at(self, env_index: int=None):
        for agent in self.world.agents:
            agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
        for landmark in self.world.landmarks:
            landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

    def reward(self, agent: Agent):
        dist2 = torch.sum(torch.square(agent.state.pos - self.world.landmarks[0].state.pos), dim=-1)
        return -dist2

    def observation(self, agent: Agent):
        entity_pos = []
        for entity in self.world.landmarks:
            entity_pos.append(entity.state.pos - agent.state.pos)
        return torch.cat([agent.state.vel, *entity_pos], dim=-1)

def reset_world_at(self, env_index: int=None):
    for agent in self.world.agents:
        agent.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)
    for landmark in self.world.landmarks:
        landmark.set_pos(torch.zeros((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device, dtype=torch.float32).uniform_(-1.0, 1.0), batch_index=env_index)

def _get_deterministic_action(agent: Agent, continuous: bool, env):
    if continuous:
        action = -agent.action.u_range_tensor.expand(env.batch_dim, agent.action_size)
    else:
        action = torch.tensor([1], device=env.device, dtype=torch.long).unsqueeze(-1).expand(env.batch_dim, 1)
    return action.clone()

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

class RandomPolicy(BaseHeuristicPolicy):

    def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
        n_envs = observation.shape[0]
        return torch.clamp(torch.randn(n_envs, 2), -u_range, u_range)

def compute_action(self, observation: torch.Tensor, u_range: float) -> torch.Tensor:
    n_envs = observation.shape[0]
    return torch.clamp(torch.randn(n_envs, 2), -u_range, u_range)

def _get_inner_point_box(outside_point, surface_point, box_pos):
    v = surface_point - outside_point
    u = box_pos - surface_point
    v_norm = torch.linalg.vector_norm(v, dim=-1).unsqueeze(-1)
    x_magnitude = (v * u).sum(-1).unsqueeze(-1) / v_norm
    x = v / v_norm * x_magnitude
    cond = v_norm == 0
    cond_exp = cond.expand(x.shape)
    x = torch.where(cond_exp, surface_point, x)
    x_magnitude = torch.where(cond, 0, x_magnitude)
    return (surface_point + x, torch.abs(x_magnitude.squeeze(-1)))

def _get_closest_box_box(box_pos, box_rot, box_width, box_length, box2_pos, box2_rot, box2_width, box2_length):
    if not isinstance(box_width, torch.Tensor):
        box_width = torch.tensor(box_width, dtype=torch.float32, device=box_pos.device).expand(box_pos.shape[0])
    if not isinstance(box_length, torch.Tensor):
        box_length = torch.tensor(box_length, dtype=torch.float32, device=box2_pos.device).expand(box_pos.shape[0])
    if not isinstance(box2_width, torch.Tensor):
        box2_width = torch.tensor(box2_width, dtype=torch.float32, device=box2_pos.device).expand(box2_pos.shape[0])
    if not isinstance(box2_length, torch.Tensor):
        box2_length = torch.tensor(box2_length, dtype=torch.float32, device=box2_pos.device).expand(box2_pos.shape[0])
    lines_pos, lines_rot, lines_length = _get_all_lines_box(torch.stack([box_pos, box2_pos], dim=0), torch.stack([box_rot, box2_rot], dim=0), torch.stack([box_width, box2_width], dim=0), torch.stack([box_length, box2_length], dim=0))
    lines_a_pos, lines_b_pos = lines_pos.unbind(1)
    lines_a_rot, lines_b_rot = lines_rot.unbind(1)
    lines_a_length, lines_b_length = lines_length.unbind(1)
    points_first, points_second = _get_closest_line_box(torch.stack([box2_pos.unsqueeze(0).expand(lines_a_pos.shape), box_pos.unsqueeze(0).expand(lines_b_pos.shape)], dim=0), torch.stack([box2_rot.unsqueeze(0).expand(lines_a_rot.shape), box_rot.unsqueeze(0).expand(lines_b_rot.shape)], dim=0), torch.stack([box2_width.unsqueeze(0).expand(lines_a_length.shape), box_width.unsqueeze(0).expand(lines_b_length.shape)], dim=0), torch.stack([box2_length.unsqueeze(0).expand(lines_a_length.shape), box_length.unsqueeze(0).expand(lines_b_length.shape)], dim=0), torch.stack([lines_a_pos, lines_b_pos], dim=0), torch.stack([lines_a_rot, lines_b_rot], dim=0), torch.stack([lines_a_length, lines_b_length], dim=0))
    points_box2_a, points_box_b = points_first.unbind(0)
    points_box_a, points_box2_b = points_second.unbind(0)
    p1s = points_box_a.unbind(0) + points_box_b.unbind(0)
    p2s = points_box2_a.unbind(0) + points_box2_b.unbind(0)
    closest_point_1 = torch.full(box_pos.shape, float('inf'), device=box_pos.device, dtype=torch.float32)
    closest_point_2 = torch.full(box_pos.shape, float('inf'), device=box_pos.device, dtype=torch.float32)
    distance = torch.full(box_pos.shape[:-1], float('inf'), device=box_pos.device, dtype=torch.float32)
    for p1, p2 in zip(p1s, p2s):
        d = torch.linalg.vector_norm(p1 - p2, dim=-1)
        is_closest = d < distance
        is_closest_exp = is_closest.unsqueeze(-1).expand(p1.shape)
        closest_point_1 = torch.where(is_closest_exp, p1, closest_point_1)
        closest_point_2 = torch.where(is_closest_exp, p2, closest_point_2)
        distance = torch.where(is_closest, d, distance)
    return (closest_point_1, closest_point_2)

def _get_closest_points_line_line(line_pos, line_rot, line_length, line2_pos, line2_rot, line2_length):
    if not isinstance(line_length, torch.Tensor):
        line_length = torch.tensor(line_length, dtype=torch.float32, device=line_pos.device).expand(line_pos.shape[0])
    if not isinstance(line2_length, torch.Tensor):
        line2_length = torch.tensor(line2_length, dtype=torch.float32, device=line_pos.device).expand(line_pos.shape[0])
    points_a, points_b = _get_line_extrema(torch.stack([line_pos, line2_pos], dim=0), torch.stack([line_rot, line2_rot], dim=0), torch.stack([line_length, line2_length], dim=0))
    point_a1, point_b1 = points_a.unbind(0)
    point_a2, point_b2 = points_b.unbind(0)
    point_i, d_i = _get_intersection_point_line_line(point_a1, point_a2, point_b1, point_b2)
    point_a1_line_b, point_a2_line_b, point_b1_line_a, point_b2_line_a = _get_closest_point_line(torch.stack([line2_pos, line2_pos, line_pos, line_pos], dim=0), torch.stack([line2_rot, line2_rot, line_rot, line_rot], dim=0), torch.stack([line2_length, line2_length, line_length, line_length], dim=0), torch.stack([point_a1, point_a2, point_b1, point_b2], dim=0)).unbind(0)
    point_pairs = ((point_a1, point_a1_line_b), (point_a2, point_a2_line_b), (point_b1_line_a, point_b1), (point_b2_line_a, point_b2))
    closest_point_1 = torch.full(line_pos.shape, float('inf'), device=line_pos.device, dtype=torch.float32)
    closest_point_2 = torch.full(line_pos.shape, float('inf'), device=line_pos.device, dtype=torch.float32)
    min_distance = torch.full(line_pos.shape[:-1], float('inf'), device=line_pos.device, dtype=torch.float32)
    for p1, p2 in point_pairs:
        d = torch.linalg.vector_norm(p1 - p2, dim=-1)
        is_closest = d < min_distance
        is_closest_exp = is_closest.unsqueeze(-1).expand(p1.shape)
        closest_point_1 = torch.where(is_closest_exp, p1, closest_point_1)
        closest_point_2 = torch.where(is_closest_exp, p2, closest_point_2)
        min_distance = torch.where(is_closest, d, min_distance)
    cond = (d_i == 0).unsqueeze(-1).expand(point_i.shape)
    closest_point_1 = torch.where(cond, point_i, closest_point_1)
    closest_point_2 = torch.where(cond, point_i, closest_point_2)
    return (closest_point_1, closest_point_2)

def _get_intersection_point_line_line(point_a1, point_a2, point_b1, point_b2):
    """
    Taken from:
    https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
    """
    r = point_a2 - point_a1
    s = point_b2 - point_b1
    p = point_a1
    q = point_b1
    cross_q_minus_p_r = TorchUtils.cross(q - p, r)
    cross_q_minus_p_s = TorchUtils.cross(q - p, s)
    cross_r_s = TorchUtils.cross(r, s)
    u = cross_q_minus_p_r / cross_r_s
    t = cross_q_minus_p_s / cross_r_s
    t_in_range = (0 <= t) * (t <= 1)
    u_in_range = (0 <= u) * (u <= 1)
    cross_r_s_is_zero = cross_r_s == 0
    distance = torch.full(point_a1.shape[:-1], float('inf'), device=point_a1.device, dtype=torch.float32)
    point = torch.full(point_a1.shape, float('inf'), device=point_a1.device, dtype=torch.float32)
    condition = ~cross_r_s_is_zero * u_in_range * t_in_range
    condition_exp = condition.expand(point.shape)
    point = torch.where(condition_exp, p + t * r, point)
    distance = torch.where(condition.squeeze(-1), 0.0, distance)
    return (point, distance)

def _get_closest_point_box(box_pos, box_rot, box_width, box_length, test_point_pos):
    if not isinstance(box_width, torch.Tensor):
        box_width = torch.tensor(box_width, dtype=torch.float32, device=box_pos.device).expand(box_pos.shape[0])
    if not isinstance(box_length, torch.Tensor):
        box_length = torch.tensor(box_length, dtype=torch.float32, device=box_pos.device).expand(box_pos.shape[0])
    closest_points = _get_all_points_box(box_pos, box_rot, box_width, box_length, test_point_pos)
    closest_point = torch.full(box_pos.shape, float('inf'), device=box_pos.device, dtype=torch.float32)
    distance = torch.full(box_pos.shape[:-1], float('inf'), device=box_pos.device, dtype=torch.float32)
    for p in closest_points:
        d = torch.linalg.vector_norm(test_point_pos - p, dim=-1)
        is_closest = d < distance
        is_closest_exp = is_closest.unsqueeze(-1).expand(p.shape)
        closest_point = torch.where(is_closest_exp, p, closest_point)
        distance = torch.where(is_closest, d, distance)
    return closest_point

def _get_all_lines_box(box_pos, box_rot, box_width, box_length):
    rotated_vector = torch.cat([box_rot.cos(), box_rot.sin()], dim=-1)
    rot_2 = box_rot + torch.pi / 2
    rotated_vector2 = torch.cat([rot_2.cos(), rot_2.sin()], dim=-1)
    expanded_half_box_length = box_length.unsqueeze(-1).expand(rotated_vector.shape) / 2
    expanded_half_box_width = box_width.unsqueeze(-1).expand(rotated_vector.shape) / 2
    p1 = box_pos + rotated_vector * expanded_half_box_length
    p2 = box_pos - rotated_vector * expanded_half_box_length
    p3 = box_pos + rotated_vector2 * expanded_half_box_width
    p4 = box_pos - rotated_vector2 * expanded_half_box_width
    ps = []
    rots = []
    lengths = []
    for i, p in enumerate([p1, p2, p3, p4]):
        ps.append(p)
        rots.append(box_rot + torch.pi / 2 if i <= 1 else box_rot)
        lengths.append(box_width if i <= 1 else box_length)
    return (torch.stack(ps, dim=0), torch.stack(rots, dim=0), torch.stack(lengths, dim=0))

def _get_closest_line_box(box_pos, box_rot, box_width, box_length, line_pos, line_rot, line_length):
    if not isinstance(box_width, torch.Tensor):
        box_width = torch.tensor(box_width, dtype=torch.float32, device=box_pos.device).expand(box_pos.shape[0])
    if not isinstance(box_length, torch.Tensor):
        box_length = torch.tensor(box_length, dtype=torch.float32, device=box_pos.device).expand(box_pos.shape[0])
    if not isinstance(line_length, torch.Tensor):
        line_length = torch.tensor(line_length, dtype=torch.float32, device=line_pos.device).expand(line_pos.shape[0])
    lines_pos, lines_rot, lines_length = _get_all_lines_box(box_pos, box_rot, box_width, box_length)
    closest_point_1 = torch.full(box_pos.shape, float('inf'), device=box_pos.device, dtype=torch.float32)
    closest_point_2 = torch.full(box_pos.shape, float('inf'), device=box_pos.device, dtype=torch.float32)
    distance = torch.full(box_pos.shape[:-1], float('inf'), device=box_pos.device, dtype=torch.float32)
    ps_box, ps_line = _get_closest_points_line_line(lines_pos, lines_rot, lines_length, line_pos.unsqueeze(0).expand(lines_pos.shape), line_rot.unsqueeze(0).expand(lines_rot.shape), line_length.unsqueeze(0).expand(lines_length.shape))
    for p_box, p_line in zip(ps_box.unbind(0), ps_line.unbind(0)):
        d = torch.linalg.vector_norm(p_box - p_line, dim=-1)
        is_closest = d < distance
        is_closest_exp = is_closest.unsqueeze(-1).expand(closest_point_1.shape)
        closest_point_1 = torch.where(is_closest_exp, p_box, closest_point_1)
        closest_point_2 = torch.where(is_closest_exp, p_line, closest_point_2)
        distance = torch.where(is_closest, d, distance)
    return (closest_point_1, closest_point_2)

def _get_all_points_box(box_pos, box_rot, box_width, box_length, test_point_pos):
    lines_pos, lines_rot, lines_length = _get_all_lines_box(box_pos, box_rot, box_width, box_length)
    closest_points = _get_closest_point_line(lines_pos, lines_rot, lines_length, test_point_pos.unsqueeze(0).expand(lines_pos.shape)).unbind(0)
    return closest_points

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
def clamp_with_norm(tensor: Tensor, max_norm: float):
    norm = torch.linalg.vector_norm(tensor, dim=-1)
    new_tensor = tensor / norm.unsqueeze(-1) * max_norm
    cond = (norm > max_norm).unsqueeze(-1).expand(tensor.shape)
    tensor = torch.where(cond, new_tensor, tensor)
    return tensor

@staticmethod
def cross(vector_a: Tensor, vector_b: Tensor):
    return (vector_a[..., X] * vector_b[..., Y] - vector_a[..., Y] * vector_b[..., X]).unsqueeze(-1)

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
def spawn_entities_randomly(entities, world, env_index: int, min_dist_between_entities: float, x_bounds: Tuple[int, int], y_bounds: Tuple[int, int], occupied_positions: Tensor=None, disable_warn: bool=False):
    batch_size = world.batch_dim if env_index is None else 1
    if occupied_positions is None:
        occupied_positions = torch.zeros((batch_size, 0, world.dim_p), device=world.device)
    for entity in entities:
        pos = ScenarioUtils.find_random_pos_for_entity(occupied_positions, env_index, world, min_dist_between_entities, x_bounds, y_bounds, disable_warn)
        occupied_positions = torch.cat([occupied_positions, pos], dim=1)
        entity.set_pos(pos.squeeze(1), batch_index=env_index)

class Transform(Attr):

    def __init__(self, translation=(0.0, 0.0), rotation=0.0, scale=(1, 1)):
        self.set_translation(*translation)
        self.set_rotation(rotation)
        self.set_scale(*scale)

    def enable(self):
        glPushMatrix()
        glTranslatef(self.translation[0], self.translation[1], 0)
        glRotatef(RAD2DEG * self.rotation, 0, 0, 1.0)
        glScalef(self.scale[0], self.scale[1], 1)

    def disable(self):
        glPopMatrix()

    def set_translation(self, newx, newy):
        self.translation = (float(newx), float(newy))

    def set_rotation(self, new):
        self.rotation = float(new)

    def set_scale(self, newx, newy):
        self.scale = (float(newx), float(newy))

def set_translation(self, newx, newy):
    self.translation = (float(newx), float(newy))

def set_rotation(self, new):
    self.rotation = float(new)

def set_scale(self, newx, newy):
    self.scale = (float(newx), float(newy))

class Joint(vmas.simulator.utils.Observer):

    def __init__(self, entity_a: vmas.simulator.core.Entity, entity_b: vmas.simulator.core.Entity, anchor_a: Tuple[float, float]=(0.0, 0.0), anchor_b: Tuple[float, float]=(0.0, 0.0), rotate_a: bool=True, rotate_b: bool=True, dist: float=0.0, collidable: bool=False, width: float=0.0, mass: float=1.0, fixed_rotation_a: Optional[float]=None, fixed_rotation_b: Optional[float]=None):
        assert entity_a != entity_b, 'Cannot join same entity'
        for anchor in (anchor_a, anchor_b):
            assert max(anchor) <= 1 and min(anchor) >= -1, f'Joint anchor points should be between -1 and 1, got {anchor}'
        assert dist >= 0, f'Joint dist must be >= 0, got {dist}'
        if dist == 0:
            assert not collidable, 'Cannot have collidable joint with dist 0'
            assert width == 0, 'Cannot have width for joint with dist 0'
            assert fixed_rotation_a == fixed_rotation_b, 'If dist is 0, fixed_rotation_a and fixed_rotation_b should be the same'
        if fixed_rotation_a is not None:
            assert not rotate_a, 'If you provide a fixed rotation for a, rotate_a should be False'
        if fixed_rotation_b is not None:
            assert not rotate_b, 'If you provide a fixed rotation for b, rotate_b should be False'
        if width > 0:
            assert collidable
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.rotate_a = rotate_a
        self.rotate_b = rotate_b
        self.fixed_rotation_a = fixed_rotation_a
        self.fixed_rotation_b = fixed_rotation_b
        self.landmark = None
        self.joint_constraints = []
        if dist == 0:
            self.joint_constraints.append(JointConstraint(entity_a, entity_b, anchor_a=anchor_a, anchor_b=anchor_b, dist=dist, rotate=rotate_a and rotate_b, fixed_rotation=fixed_rotation_a))
        else:
            entity_a.subscribe(self)
            entity_b.subscribe(self)
            self.landmark = vmas.simulator.core.Landmark(name=f'joint {entity_a.name} {entity_b.name}', collide=collidable, movable=True, rotatable=True, mass=mass, shape=vmas.simulator.core.Box(length=dist, width=width) if width != 0 else vmas.simulator.core.Line(length=dist), color=vmas.simulator.utils.Color.BLACK, is_joint=True)
            self.joint_constraints += [JointConstraint(self.landmark, entity_a, anchor_a=(-1, 0), anchor_b=anchor_a, dist=0.0, rotate=rotate_a, fixed_rotation=fixed_rotation_a), JointConstraint(self.landmark, entity_b, anchor_a=(1, 0), anchor_b=anchor_b, dist=0.0, rotate=rotate_b, fixed_rotation=fixed_rotation_b)]

    def notify(self, observable, *args, **kwargs):
        pos_a = self.joint_constraints[0].pos_point(self.entity_a)
        pos_b = self.joint_constraints[1].pos_point(self.entity_b)
        self.landmark.set_pos((pos_a + pos_b) / 2, batch_index=None)
        angle = torch.atan2(pos_b[:, vmas.simulator.utils.Y] - pos_a[:, vmas.simulator.utils.Y], pos_b[:, vmas.simulator.utils.X] - pos_a[:, vmas.simulator.utils.X]).unsqueeze(-1)
        self.landmark.set_rot(angle, batch_index=None)
        if not self.rotate_a and self.fixed_rotation_a is None:
            self.joint_constraints[0].fixed_rotation = angle - self.entity_a.state.rot
        if not self.rotate_b and self.fixed_rotation_b is None:
            self.joint_constraints[1].fixed_rotation = angle - self.entity_b.state.rot

def notify(self, observable, *args, **kwargs):
    pos_a = self.joint_constraints[0].pos_point(self.entity_a)
    pos_b = self.joint_constraints[1].pos_point(self.entity_b)
    self.landmark.set_pos((pos_a + pos_b) / 2, batch_index=None)
    angle = torch.atan2(pos_b[:, vmas.simulator.utils.Y] - pos_a[:, vmas.simulator.utils.Y], pos_b[:, vmas.simulator.utils.X] - pos_a[:, vmas.simulator.utils.X]).unsqueeze(-1)
    self.landmark.set_rot(angle, batch_index=None)
    if not self.rotate_a and self.fixed_rotation_a is None:
        self.joint_constraints[0].fixed_rotation = angle - self.entity_a.state.rot
    if not self.rotate_b and self.fixed_rotation_b is None:
        self.joint_constraints[1].fixed_rotation = angle - self.entity_b.state.rot

class JointConstraint:
    """
    This is an uncollidable constraint that bounds two entities in the specified anchor points at the specified distance
    """

    def __init__(self, entity_a: vmas.simulator.core.Entity, entity_b: vmas.simulator.core.Entity, anchor_a: Tuple[float, float]=(0.0, 0.0), anchor_b: Tuple[float, float]=(0.0, 0.0), dist: float=0.0, rotate: bool=True, fixed_rotation: Optional[float]=None):
        assert entity_a != entity_b, 'Cannot join same entity'
        for anchor in (anchor_a, anchor_b):
            assert max(anchor) <= 1 and min(anchor) >= -1, f'Joint anchor points should be between -1 and 1, got {anchor}'
        assert dist >= 0, f'Joint dist must be >= 0, got {dist}'
        if fixed_rotation is not None:
            assert not rotate, 'If fixed rotation is provided, rotate should be False'
        if rotate:
            assert fixed_rotation is None, 'If you provide a fixed rotation, rotate should be False'
            fixed_rotation = 0.0
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        self.dist = dist
        self.fixed_rotation = fixed_rotation
        self.rotate = rotate
        self._delta_anchor_tensor_map = {}

    def _delta_anchor_tensor(self, entity):
        if entity not in self._delta_anchor_tensor_map:
            if entity == self.entity_a:
                anchor = self.anchor_a
            elif entity == self.entity_b:
                anchor = self.anchor_b
            else:
                raise AssertionError()
            delta_anchor_tensor = torch.tensor(entity.shape.get_delta_from_anchor(anchor), device=entity.state.pos.device).unsqueeze(0).expand(entity.state.pos.shape)
            self._delta_anchor_tensor_map[entity] = delta_anchor_tensor
        self._delta_anchor_tensor_map[entity] = self._delta_anchor_tensor_map[entity].to(entity.state.pos.device)
        return self._delta_anchor_tensor_map[entity]

    def get_delta_anchor(self, entity: vmas.simulator.core.Entity):
        return vmas.simulator.utils.TorchUtils.rotate_vector(self._delta_anchor_tensor(entity), entity.state.rot)

    def pos_point(self, entity: vmas.simulator.core.Entity):
        return entity.state.pos + self.get_delta_anchor(entity)

    def render(self, env_index: int=0) -> List[Geom]:
        if self.dist == 0:
            return []
        from vmas.simulator import rendering
        geoms: List[rendering.Geom] = []
        joint_line = rendering.Line((-self.dist / 2, 0), (self.dist / 2, 0), width=UNCOLLIDABLE_JOINT_RENDERING_WIDTH)
        pos_point_a = self.pos_point(self.entity_a)[env_index]
        pos_point_b = self.pos_point(self.entity_b)[env_index]
        angle = torch.atan2(pos_point_b[vmas.simulator.utils.Y] - pos_point_a[vmas.simulator.utils.Y], pos_point_b[vmas.simulator.utils.X] - pos_point_a[vmas.simulator.utils.X])
        xform = rendering.Transform()
        xform.set_translation(*(pos_point_a + pos_point_b) / 2)
        xform.set_rotation(angle)
        joint_line.add_attr(xform)
        geoms.append(joint_line)
        return geoms

def _delta_anchor_tensor(self, entity):
    if entity not in self._delta_anchor_tensor_map:
        if entity == self.entity_a:
            anchor = self.anchor_a
        elif entity == self.entity_b:
            anchor = self.anchor_b
        else:
            raise AssertionError()
        delta_anchor_tensor = torch.tensor(entity.shape.get_delta_from_anchor(anchor), device=entity.state.pos.device).unsqueeze(0).expand(entity.state.pos.shape)
        self._delta_anchor_tensor_map[entity] = delta_anchor_tensor
    self._delta_anchor_tensor_map[entity] = self._delta_anchor_tensor_map[entity].to(entity.state.pos.device)
    return self._delta_anchor_tensor_map[entity]

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

def get_delta_from_anchor(self, anchor: Tuple[float, float]) -> Tuple[float, float]:
    delta = torch.tensor([anchor[X] * self.radius, anchor[Y] * self.radius]).to(torch.float32)
    delta_norm = torch.linalg.vector_norm(delta)
    if delta_norm > self.radius:
        delta /= delta_norm * self.radius
    return tuple(delta.tolist())

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

def _spawn(self, dim_c: int, dim_p: int):
    self.pos = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
    self.vel = torch.zeros(self.batch_dim, dim_p, device=self.device, dtype=torch.float32)
    self.rot = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)
    self.ang_vel = torch.zeros(self.batch_dim, 1, device=self.device, dtype=torch.float32)

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

@property
def is_rendering(self):
    if self._render is None:
        self.reset_render()
    return self._render

def reset_render(self):
    self._render = torch.full((self.batch_dim,), True, device=self.device)

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

def _action_list_to_tensor(self, list_in: List) -> List:
    assert len(list_in) == self._env.n_agents, f'Expecting actions for {self._env.n_agents} agents, got {len(list_in)} actions'
    dtype = torch.float32 if self._env.continuous_actions else torch.long
    return [torch.tensor(act, device=self._env.device, dtype=dtype).reshape(self._env.num_envs, self._env.get_agent_action_size(agent)) if not isinstance(act, torch.Tensor) else act.to(dtype=dtype, device=self._env.device).reshape(self._env.num_envs, self._env.get_agent_action_size(agent)) for agent, act in zip(self._env.agents, list_in)]

class HolonomicWithRotation(Dynamics):

    @property
    def needed_action_size(self) -> int:
        return 3

    def process_action(self):
        self.agent.state.force = self.agent.action.u[:, :2]
        self.agent.state.torque = self.agent.action.u[:, 2].unsqueeze(-1)

def process_action(self):
    self.agent.state.force = self.agent.action.u[:, :2]
    self.agent.state.torque = self.agent.action.u[:, 2].unsqueeze(-1)

class Forward(Dynamics):

    @property
    def needed_action_size(self) -> int:
        return 1

    def process_action(self):
        force = torch.zeros(self.agent.batch_dim, 2, device=self.agent.device, dtype=torch.float)
        force[:, X] = self.agent.action.u[:, 0]
        self.agent.state.force = TorchUtils.rotate_vector(force, self.agent.state.rot)

def process_action(self):
    force = torch.zeros(self.agent.batch_dim, 2, device=self.agent.device, dtype=torch.float)
    force[:, X] = self.agent.action.u[:, 0]
    self.agent.state.force = TorchUtils.rotate_vector(force, self.agent.state.rot)

class Rotation(Dynamics):

    @property
    def needed_action_size(self) -> int:
        return 1

    def process_action(self):
        self.agent.state.torque = self.agent.action.u[:, 0].unsqueeze(-1)

def process_action(self):
    self.agent.state.torque = self.agent.action.u[:, 0].unsqueeze(-1)

def set_nvec(agent, nvec):
    agent.action_size = len(nvec)
    agent.discrete_action_nvec = nvec
    agent.action.action_size = agent.action_size

