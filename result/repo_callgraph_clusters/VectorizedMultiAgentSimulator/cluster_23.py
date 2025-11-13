# Cluster 23

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

