# Cluster 18

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

def get_outside_pos(self, env_index):
    return torch.empty((1, self.world.dim_p) if env_index is not None else (self.world.batch_dim, self.world.dim_p), device=self.world.device).uniform_(-1000 * self.world.x_semidim, -10 * self.world.x_semidim)

def interX(L1, L2, is_return_points=False):
    """Calculate the intersections of batches of curves.
        Adapted from https://www.mathworks.com/matlabcentral/fileexchange/22441-curve-intersections
    Args:
        L1: [batch_size, num_points, 2]
        L2: [batch_size, num_points, 2]
        is_return_points: bool. Whether to return the intersecting points.
    """
    batch_dim = L1.shape[0]
    collision_index = torch.zeros(batch_dim, dtype=torch.bool)
    if L1.numel() == 0 or L2.numel() == 0:
        return torch.empty((0, 2), device=L1.device) if is_return_points else False
    x1, y1 = (L1[..., 0], L1[..., 1])
    x2, y2 = (L2[..., 0], L2[..., 1])
    dx1, dy1 = (torch.diff(x1, dim=1), torch.diff(y1, dim=1))
    dx2, dy2 = (torch.diff(x2, dim=1), torch.diff(y2, dim=1))
    S1 = dx1 * y1[..., :-1] - dy1 * x1[..., :-1]
    S2 = dx2 * y2[..., :-1] - dy2 * x2[..., :-1]

    def D(x, y):
        return (x[..., :-1] - y) * (x[..., 1:] - y)
    C1 = D(dx1.unsqueeze(2) * y2.unsqueeze(1) - dy1.unsqueeze(2) * x2.unsqueeze(1), S1.unsqueeze(2)) < 0
    C2 = (D((y1.unsqueeze(2) * dx2.unsqueeze(1) - x1.unsqueeze(2) * dy2.unsqueeze(1)).transpose(1, 2), S2.unsqueeze(2)) < 0).transpose(1, 2)
    batch_indices, i, j = torch.where(C1 & C2)
    batch_indices_pruned = torch.sort(torch.unique(batch_indices))[0]
    collision_index[batch_indices_pruned] = True
    if is_return_points:
        if batch_indices.numel() == 0:
            return torch.empty((0, 2), device=L1.device)
        else:
            intersections = []
            for b in batch_indices.unique():
                L = dy2[b, j] * dx1[b, i] - dy1[b, i] * dx2[b, j]
                nonzero = L != 0
                i_nz, j_nz, L_nz = (i[nonzero], j[nonzero], L[nonzero])
                P = torch.stack(((dx2[b, j_nz] * S1[b, i_nz] - dx1[b, i_nz] * S2[b, j_nz]) / L_nz, (dy2[b, j_nz] * S1[b, i_nz] - dy1[b, i_nz] * S2[b, j_nz]) / L_nz), dim=-1)
                intersections.append(P)
            return torch.cat(intersections, dim=0)
    else:
        return collision_index

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

