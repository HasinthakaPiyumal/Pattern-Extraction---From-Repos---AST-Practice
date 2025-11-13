# Cluster 15

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

def done(self):
    return (torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) <= 0.01) + self.collided

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

def done(self):
    return (torch.linalg.vector_norm(self.ball.state.pos - self.goal.state.pos, dim=1) <= 0.01) + (-self.world.x_semidim + self.ball_radius >= self.ball.state.pos[:, X]) + (self.ball.state.pos[:, X] >= self.world.x_semidim - self.ball_radius) + (-self.world.y_semidim + self.ball_radius >= self.ball.state.pos[:, Y]) + (self.ball.state.pos[:, Y] >= self.world.y_semidim - self.ball_radius)

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

def get_closest_point_circle(self, pos: Tensor):
    pos_norm = torch.linalg.vector_norm(pos, dim=1)
    agent_pos_normalized = pos / pos_norm.unsqueeze(-1)
    agent_pos_normalized *= self.desired_radius
    return torch.nan_to_num(agent_pos_normalized)

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

def get_line_angle_dist_0_360(angle, goal):
    angle = angle_to_vector(angle)
    goal = angle_to_vector(goal)
    return -torch.einsum('bs,bs->b', angle, goal)

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

def process_action(self, agent: Agent):
    if self.use_vel_controller:
        vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
        agent.controller.reset(vel_is_zero)
        agent.controller.process_force()

def done(self):
    return torch.all((torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) <= 0.01) * (get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot).unsqueeze(-1) <= 0.01), dim=1)

def get_pos(i):
    pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2, 0.0], dtype=torch.float32, device=self.world.device).repeat(i.shape[0], 1)
    pos[:, X] += self.passage_length * i
    return pos

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

def done(self):
    return torch.stack([torch.linalg.vector_norm(agent.state.pos - agent.goal.state.pos, dim=-1) < agent.shape.radius for agent in self.world.agents], dim=-1).all(-1)

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

def done(self):
    return torch.all((torch.linalg.vector_norm(self.joint.landmark.state.pos - self.goal.state.pos, dim=1) <= 0.01) * (get_line_angle_dist_0_180(self.joint.landmark.state.rot, self.goal.state.rot).unsqueeze(-1) <= 0.01), dim=1)

def process_action(self, agent: Agent):
    if self.use_controller:
        vel_is_zero = torch.linalg.vector_norm(agent.action.u, dim=1) < 0.001
        agent.controller.reset(vel_is_zero)
        agent.controller.process_force()

def get_pos(i):
    pos = torch.tensor([-1 - self.agent_radius + self.passage_length / 2, 0.0], dtype=torch.float32, device=self.world.device).repeat(i.shape[0], 1)
    pos[:, X] += self.passage_length * i
    return pos

class Scenario(BaseScenario):

    def make_world(self, batch_dim: int, device: torch.device, **kwargs):
        n_agents = kwargs.pop('n_agents', 4)
        self.n_packages = kwargs.pop('n_packages', 1)
        self.package_width = kwargs.pop('package_width', 0.15)
        self.package_length = kwargs.pop('package_length', 0.15)
        self.package_mass = kwargs.pop('package_mass', 50)
        ScenarioUtils.check_kwargs_consumed(kwargs)
        self.shaping_factor = 100
        self.world_semidim = 1
        self.agent_radius = 0.03
        world = World(batch_dim, device, x_semidim=self.world_semidim + 2 * self.agent_radius + max(self.package_length, self.package_width), y_semidim=self.world_semidim + 2 * self.agent_radius + max(self.package_length, self.package_width))
        for i in range(n_agents):
            agent = Agent(name=f'agent_{i}', shape=Sphere(self.agent_radius), u_multiplier=0.6)
            world.add_agent(agent)
        goal = Landmark(name='goal', collide=False, shape=Sphere(radius=0.15), color=Color.LIGHT_GREEN)
        world.add_landmark(goal)
        self.packages = []
        for i in range(self.n_packages):
            package = Landmark(name=f'package {i}', collide=True, movable=True, mass=self.package_mass, shape=Box(length=self.package_length, width=self.package_width), color=Color.RED)
            package.goal = goal
            self.packages.append(package)
            world.add_landmark(package)
        return world

    def reset_world_at(self, env_index: int=None):
        ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=self.agent_radius * 2, x_bounds=(-self.world_semidim, self.world_semidim), y_bounds=(-self.world_semidim, self.world_semidim))
        agent_occupied_positions = torch.stack([agent.state.pos for agent in self.world.agents], dim=1)
        if env_index is not None:
            agent_occupied_positions = agent_occupied_positions[env_index].unsqueeze(0)
        goal = self.world.landmarks[0]
        ScenarioUtils.spawn_entities_randomly([goal] + self.packages, self.world, env_index, min_dist_between_entities=max((package.shape.circumscribed_radius() + goal.shape.radius + 0.01 for package in self.packages)), x_bounds=(-self.world_semidim, self.world_semidim), y_bounds=(-self.world_semidim, self.world_semidim), occupied_positions=agent_occupied_positions)
        for package in self.packages:
            package.on_goal = self.world.is_overlapping(package, package.goal)
            if env_index is None:
                package.global_shaping = torch.linalg.vector_norm(package.state.pos - package.goal.state.pos, dim=1) * self.shaping_factor
            else:
                package.global_shaping[env_index] = torch.linalg.vector_norm(package.state.pos[env_index] - package.goal.state.pos[env_index]) * self.shaping_factor

    def reward(self, agent: Agent):
        is_first = agent == self.world.agents[0]
        if is_first:
            self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
            for package in self.packages:
                package.dist_to_goal = torch.linalg.vector_norm(package.state.pos - package.goal.state.pos, dim=1)
                package.on_goal = self.world.is_overlapping(package, package.goal)
                package.color = torch.tensor(Color.RED.value, device=self.world.device, dtype=torch.float32).repeat(self.world.batch_dim, 1)
                package.color[package.on_goal] = torch.tensor(Color.GREEN.value, device=self.world.device, dtype=torch.float32)
                package_shaping = package.dist_to_goal * self.shaping_factor
                self.rew[~package.on_goal] += package.global_shaping[~package.on_goal] - package_shaping[~package.on_goal]
                package.global_shaping = package_shaping
        return self.rew

    def observation(self, agent: Agent):
        package_obs = []
        for package in self.packages:
            package_obs.append(package.state.pos - package.goal.state.pos)
            package_obs.append(package.state.pos - agent.state.pos)
            package_obs.append(package.state.vel)
            package_obs.append(package.on_goal.unsqueeze(-1))
        return torch.cat([agent.state.pos, agent.state.vel, *package_obs], dim=-1)

    def done(self):
        return torch.all(torch.stack([package.on_goal for package in self.packages], dim=1), dim=-1)

def reset_world_at(self, env_index: int=None):
    ScenarioUtils.spawn_entities_randomly(self.world.agents, self.world, env_index, min_dist_between_entities=self.agent_radius * 2, x_bounds=(-self.world_semidim, self.world_semidim), y_bounds=(-self.world_semidim, self.world_semidim))
    agent_occupied_positions = torch.stack([agent.state.pos for agent in self.world.agents], dim=1)
    if env_index is not None:
        agent_occupied_positions = agent_occupied_positions[env_index].unsqueeze(0)
    goal = self.world.landmarks[0]
    ScenarioUtils.spawn_entities_randomly([goal] + self.packages, self.world, env_index, min_dist_between_entities=max((package.shape.circumscribed_radius() + goal.shape.radius + 0.01 for package in self.packages)), x_bounds=(-self.world_semidim, self.world_semidim), y_bounds=(-self.world_semidim, self.world_semidim), occupied_positions=agent_occupied_positions)
    for package in self.packages:
        package.on_goal = self.world.is_overlapping(package, package.goal)
        if env_index is None:
            package.global_shaping = torch.linalg.vector_norm(package.state.pos - package.goal.state.pos, dim=1) * self.shaping_factor
        else:
            package.global_shaping[env_index] = torch.linalg.vector_norm(package.state.pos[env_index] - package.goal.state.pos[env_index]) * self.shaping_factor

def reward(self, agent: Agent):
    is_first = agent == self.world.agents[0]
    if is_first:
        self.rew = torch.zeros(self.world.batch_dim, device=self.world.device, dtype=torch.float32)
        for package in self.packages:
            package.dist_to_goal = torch.linalg.vector_norm(package.state.pos - package.goal.state.pos, dim=1)
            package.on_goal = self.world.is_overlapping(package, package.goal)
            package.color = torch.tensor(Color.RED.value, device=self.world.device, dtype=torch.float32).repeat(self.world.batch_dim, 1)
            package.color[package.on_goal] = torch.tensor(Color.GREEN.value, device=self.world.device, dtype=torch.float32)
            package_shaping = package.dist_to_goal * self.shaping_factor
            self.rew[~package.on_goal] += package.global_shaping[~package.on_goal] - package_shaping[~package.on_goal]
            package.global_shaping = package_shaping
    return self.rew

def get_line_angle_dist_0_360(angle, goal):
    angle = angle_to_vector(angle)
    goal = angle_to_vector(goal)
    return -torch.einsum('bs,bs->b', angle, goal)

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

def process_action(self, agent: Agent):
    if self.use_controller:
        agent.controller.process_force()

def info(self, agent: Agent) -> Dict[str, Tensor]:
    return {'dist_rew': self.dist_rew, 'rot_rew': self.rot_rew, 'pos_rew': self.pos_rew, 'agent_wind_rew': agent.wind_rew, 'agent_vel_rew': agent.vel_rew, 'agent_energy_rew': agent.energy_rew, 'delta_vel_to_goal': torch.linalg.vector_norm(agent.state.vel - self.desired_vel, dim=-1)}

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

def done(self):
    return torch.all(torch.stack([torch.linalg.vector_norm(a.state.pos - a.goal.state.pos, dim=1) <= a.shape.radius / 2 for a in self.world.agents], dim=1), dim=1)

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

def done(self):
    return self.on_the_ground + self.world.is_overlapping(self.package, self.package.goal)

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

def process_action(self, agent: Agent):
    self.vel_action = agent.action.u.clone()
    agent.controller.process_force()

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

def reward(self, agent: Agent):
    dist2 = torch.linalg.vector_norm(agent.state.pos - self.world.landmarks[-1].state.pos, dim=1)
    return -dist2

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

def reward(self, agent: Agent):
    return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

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

def reward(self, agent: Agent):
    main_reward = self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)
    return main_reward

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

def reward(self, agent: Agent):
    return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

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

def reward(self, agent: Agent):
    return self.adversary_reward(agent) if agent.adversary else self.agent_reward(agent)

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

def is_collision(self, agent1: Agent, agent2: Agent):
    delta_pos = agent1.state.pos - agent2.state.pos
    dist = torch.linalg.vector_norm(delta_pos, dim=-1)
    dist_min = agent1.shape.radius + agent2.shape.radius
    return dist < dist_min

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

@TorchVectorizedObject.batch_dim.setter
def batch_dim(self, batch_dim: int):
    TorchVectorizedObject.batch_dim.fset(self, batch_dim)
    self._state.batch_dim = batch_dim

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

@Entity.batch_dim.setter
def batch_dim(self, batch_dim: int):
    Entity.batch_dim.fset(self, batch_dim)
    self._action.batch_dim = batch_dim

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

