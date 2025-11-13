# Cluster 33

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

