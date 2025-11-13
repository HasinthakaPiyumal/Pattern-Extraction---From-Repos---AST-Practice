# Cluster 22

def minimum_bounding_rectangle(points: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Finds the smallest bounding rectangle for a set of points in two dimensional space.
    Returns a set of points (in clockwise order) representing the corners of the bounding box.

    Algorithm high level idea:
        One edge of the minimum bounding rectangle for a set of points will be the same as one of the edges of the
        convex hull of those points.

    Algorithm:
     1. Create a convex hull (https://en.wikipedia.org/wiki/Convex_hull) of the input points.
     2. Calculate the angles that all the edges of the convex hull make with the x-axis. Assume that there are N unique
        angles calculated in this step.
     3. Create rotation matrices for all the N unique angles computed in step 2.
     4. Create N set of convex hull points by rotating the original convex hull points using all the N rotation matrices
        computed in the last step.
     5. For each of the N set of convex hull points computed in the last step, calculate the bounding rectangle by
        calculating (min_x, max_x, min_y, max_y).
     6. For the N bounding rectangles computed in the last step, find the rectangle with the minimum area. This will
        give the minimum bounding rectangle for our rotated set of convex hull points (see Step 4).
     7. Undo the rotation of the convex hull by multiplying the points with the inverse of the rotation matrix. And
        remember that the inverse of a rotation matrix is equal to the transpose of the rotation matrix. The returned
        points are in a clockwise order.

    To visualize what this function does, you can use the following snippet:

    for n in range(10):
        points = np.random.rand(8,2)
        plt.scatter(points[:,0], points[:,1])
        bbox = minimum_bounding_rectangle(points)
        plt.fill(bbox[:,0], bbox[:,1], alpha=0.2)
        plt.axis('equal')
        plt.show()

    :param points: <nbr_points, 2>. A nx2 matrix of coordinates where n >= 3.
    :return: A 4x2 matrix of coordinates of the minimum bounding rectangle (in clockwise order).
    """
    assert points.ndim == 2, 'Points ndim should be 2.'
    assert points.shape[1] == 2, 'Points shape: n x 2 where n>= 3.'
    assert points.shape[0] >= 3, 'Points shape: n x 2 where n>= 3.'
    pi2 = np.pi / 2.0
    hull_points = points[ConvexHull(points).vertices]
    edges = hull_points[1:] - hull_points[:-1]
    angles = np.arctan2(edges[:, 1], edges[:, 0])
    angles = np.abs(np.mod(angles, pi2))
    angles = np.unique(angles)
    rotations = np.vstack([np.cos(angles), np.cos(angles - pi2), np.cos(angles + pi2), np.cos(angles)]).T
    rotations = rotations.reshape((-1, 2, 2))
    rot_points = np.dot(rotations, hull_points.T)
    min_x = np.nanmin(rot_points[:, 0], axis=1)
    max_x = np.nanmax(rot_points[:, 0], axis=1)
    min_y = np.nanmin(rot_points[:, 1], axis=1)
    max_y = np.nanmax(rot_points[:, 1], axis=1)
    areas = (max_x - min_x) * (max_y - min_y)
    best_idx = np.argmin(areas)
    x1 = max_x[best_idx]
    x2 = min_x[best_idx]
    y1 = max_y[best_idx]
    y2 = min_y[best_idx]
    r = rotations[best_idx]
    pts_clockwise_order = np.zeros((4, 2))
    pts_clockwise_order[0] = np.dot([x1, y2], r)
    pts_clockwise_order[1] = np.dot([x2, y2], r)
    pts_clockwise_order[2] = np.dot([x2, y1], r)
    pts_clockwise_order[3] = np.dot([x1, y1], r)
    return pts_clockwise_order

class TestUtils(unittest.TestCase):
    """
    Tests utils library.
    """

    def setUp(self) -> None:
        """Sets sample parameters for testing."""
        np.random.seed(0)
        self.inits = np.random.rand(100)
        self.deltas = np.random.rand(100)
        self.sampling_times = np.random.randint(1000000, size=100)

    def test_forward_integrate(self) -> None:
        """
        Test forward_integrate.
        """
        for init, delta, sampling_time in zip(self.inits, self.deltas, self.sampling_times):
            result = forward_integrate(init, delta, TimePoint(sampling_time))
            expect = init + delta * sampling_time * 1e-06
            self.assertAlmostEqual(result, expect)

def setUp(self) -> None:
    """Sets sample parameters for testing."""
    np.random.seed(0)
    self.inits = np.random.rand(100)
    self.deltas = np.random.rand(100)
    self.sampling_times = np.random.randint(1000000, size=100)

class RemotePlanner(AbstractPlanner):
    """
    Remote planner delegates computation of trajectories to a docker container, with which communicates through
    grpc.
    """

    def __init__(self, submission_container_manager: Optional[SubmissionContainerManager]=None, submission_image: Optional[str]=None, container_name: Optional[str]=None, compute_trajectory_timeout: float=1) -> None:
        """
        Prepares the remote container for planning.
        :param submission_container_manager: Optional manager, if provided a container will be started by RemotePlanner
        :param submission_image: Docker image name for the submission_container_factory
        :param container_name: Name to assign to the submission container
        :param compute_trajectory_timeout: Timeout for computation of trajectory.
        """
        if submission_container_manager:
            missing_parameter_message = 'Parameters for SubmissionContainer are missing!'
            assert submission_image, missing_parameter_message
            assert container_name, missing_parameter_message
            self.port = None
        else:
            self.port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        self.submission_container_manager = submission_container_manager
        self.submission_image = submission_image
        self.container_name = container_name
        self._channel = None
        self._stub = None
        self.serialized_observation: Optional[List[bytes]] = None
        self.serialized_state: Optional[List[bytes]] = None
        self.sample_interval: Optional[float] = None
        self._compute_trajectory_timeout = compute_trajectory_timeout

    def __reduce__(self) -> Tuple[Type[RemotePlanner], Tuple[Optional[SubmissionContainerManager], Optional[str], Optional[str]]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self.submission_container_manager, self.submission_image, self.container_name))

    def name(self) -> str:
        """Inherited, see superclass."""
        return 'RemotePlanner'

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    @staticmethod
    def _planner_initializations_to_message(initialization: PlannerInitialization) -> chpb.PlannerInitializationLight:
        """
        Converts a PlannerInitialization to the message specified in the protocol files.
        :param initialization: The initialization parameters for the planner
        :return: A initialization message
        """
        try:
            mission_goal = proto_se2_from_se2(initialization.mission_goal)
        except AttributeError as e:
            logger.error('Mission goal was None!')
            raise e
        planner_initialization = chpb.PlannerInitializationLight(route_roadblock_ids=initialization.route_roadblock_ids, mission_goal=mission_goal, map_name=initialization.map_api.map_name)
        return planner_initialization

    def initialize(self, initialization: PlannerInitialization, timeout: float=5) -> None:
        """
        Creates the container manager, and runs the specified docker image. The communication port is created using
        the PID from the ray worker. Sends a request to initialize the remote planner.
        :param initialization: List of PlannerInitialization objects
        :param timeout: for planner initialization
        """
        if self.submission_container_manager:
            submission_container = try_n_times(self.submission_container_manager.get_submission_container, [self.submission_image, self.container_name, find_free_port_number()], {}, (docker.errors.APIError,), max_tries=10)
            self.port = submission_container.port
            submission_container.start()
            submission_container.wait_until_running(timeout=5)
        self._channel = grpc.insecure_channel(f'{NETWORK}:{self.port}')
        self._stub = chpb_grpc.DetectionTracksChallengeStub(self._channel)
        logger.info('Client sending planner initialization request...')
        planner_initializations_message = self._planner_initializations_to_message(initialization)
        logger.info(f'Trying to communicate on port {NETWORK}:{self.port}')
        try:
            _, _ = keep_trying(self._stub.InitializePlanner, [planner_initializations_message], {}, errors=(grpc.RpcError,), timeout=timeout)
        except Exception as e:
            submission_logger.error('Planner initialization failed!')
            submission_logger.error(e)
            raise e
        logger.info('Planner initialized!')

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory.
        :param current_input: Planner input for which trajectory should be computed
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logger.debug('Client sending planner input: %s' % current_input)
        trajectory = self._compute_trajectory(self._stub, current_input=current_input)
        return trajectory

    def _compute_trajectory(self, stub: chpb_grpc.DetectionTracksChallengeStub, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Sends a request to compute the trajectory given the PlannerInput to the remote planner.
        :param stub: Service interface
        :param current_input: Planner input for which a trajectory should be computed.
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logging.debug('Client sending observation...')
        self.serialized_state, self.serialized_observation, self.sample_interval = self._get_history_update(current_input)
        serialized_simulation_iteration = chpb.SimulationIteration(time_us=current_input.iteration.time_us, index=current_input.iteration.index)
        if self.sample_interval:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=self.sample_interval)
        else:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=None)
        tl_data = self._build_tl_message_from_planner_input(current_input)
        planner_input = chpb.PlannerInput(simulation_iteration=serialized_simulation_iteration, simulation_history_buffer=serialized_buffer, traffic_light_data=tl_data)
        try:
            trajectory_message = stub.ComputeTrajectory(planner_input, timeout=self._compute_trajectory_timeout)
        except grpc.RpcError as e:
            submission_logger.error('Trajectory computation service failed!')
            submission_logger.error(e)
            raise e
        return interp_traj_from_proto_traj(trajectory_message)

    def _get_history_update(self, planner_input: PlannerInput) -> Tuple[List[bytes], List[bytes], Optional[float]]:
        """
        Gets the new states and observations from the input. If no cache is present, the entire history is
        serialized, otherwise just the last element.
        :param planner_input: The input for planners
        :return: Tuple with new serialized state and observations.
        """
        keep_all_history = not self.serialized_state and (not self.serialized_observation)
        if keep_all_history:
            serialized_state = [pickle.dumps(state) for state in planner_input.history.ego_states]
            serialized_observation = [pickle.dumps(obs) for obs in planner_input.history.observations]
        else:
            last_ego_state, last_observations = planner_input.history.current_state
            serialized_state = [pickle.dumps(last_ego_state)]
            serialized_observation = [pickle.dumps(last_observations)]
        sample_interval = planner_input.history.sample_interval if not self.sample_interval else None
        return (serialized_state, serialized_observation, sample_interval)

    @staticmethod
    def _build_tl_message_from_planner_input(planner_input: PlannerInput) -> chpb.TrafficLightStatusData:
        tl_status_data: List[List[chpb.TrafficLightStatusData]]
        if planner_input.traffic_light_data is None:
            tl_status_data = [[]]
        else:
            tl_status_data = [proto_tl_status_data_from_tl_status_data(tl_status_data) for tl_status_data in planner_input.traffic_light_data]
        return tl_status_data

@staticmethod
def _planner_initializations_to_message(initialization: PlannerInitialization) -> chpb.PlannerInitializationLight:
    """
        Converts a PlannerInitialization to the message specified in the protocol files.
        :param initialization: The initialization parameters for the planner
        :return: A initialization message
        """
    try:
        mission_goal = proto_se2_from_se2(initialization.mission_goal)
    except AttributeError as e:
        logger.error('Mission goal was None!')
        raise e
    planner_initialization = chpb.PlannerInitializationLight(route_roadblock_ids=initialization.route_roadblock_ids, mission_goal=mission_goal, map_name=initialization.map_api.map_name)
    return planner_initialization

class SimpleAgentAugmentor(AbstractAugmentor):
    """Simple data augmentation that adds Gaussian noise to the ego current position with specified mean and std."""

    def __init__(self, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
        """
        Initialize the augmentor.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
        self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
        self._augment_prob = augment_prob

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        for batch_idx in range(len(features['agents'].ego)):
            features['agents'].ego[batch_idx][-1] += self._random_offset_generator.sample()
        return (features, targets)

    @property
    def required_features(self) -> List[str]:
        """Inherited, see superclass."""
        return ['agents']

    @property
    def required_targets(self) -> List[str]:
        """Inherited, see superclass."""
        return []

    @property
    def augmentation_probability(self) -> ParameterToScale:
        """Inherited, see superclass."""
        return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

    @property
    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """Inherited, see superclass."""
        return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def __init__(self, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
    """
        Initialize the augmentor.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
    self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
    self._augment_prob = augment_prob

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    for batch_idx in range(len(features['agents'].ego)):
        features['agents'].ego[batch_idx][-1] += self._random_offset_generator.sample()
    return (features, targets)

class KinematicHistoryGenericAgentAugmentor(AbstractAugmentor):
    """
    Data augmentation that perturbs the current ego position and generates a feasible trajectory history that
    satisfies a set of kinematic constraints.

    This involves constrained minimization of the following objective:
    * minimize dist(perturbed_trajectory, ground_truth_trajectory)


    Simple data augmentation that adds Gaussian noise to the ego current position with specified mean and std.
    """

    def __init__(self, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
        """
        Initialize the augmentor.
        :param dt: Time interval between trajectory points.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
        self._dt = dt
        self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
        self._augment_prob = augment_prob

    def safety_check(self, ego: npt.NDArray[np.float32], all_agents: List[npt.NDArray[np.float32]]) -> bool:
        """
        Check if the augmented trajectory violates any safety check (going backwards, collision with other agents).
        :param ego: Perturbed ego feature tensor to be validated.
        :param all_agents: List of agent features to validate against.
        :return: Bool reflecting feature validity.
        """
        if np.diff(ego, axis=0)[-1][0] < 0.0001:
            return False
        for agents in all_agents:
            dist_to_the_closest_agent = np.min(np.linalg.norm(np.array(agents)[:, :, :2] - ego[-1, :2], axis=1))
            if dist_to_the_closest_agent < 2.5:
                return False
        return True

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        for batch_idx in range(len(features['generic_agents'].ego)):
            trajectory_length = len(features['generic_agents'].ego[batch_idx]) - 1
            _optimizer = ConstrainedNonlinearSmoother(trajectory_length, self._dt)
            ego_trajectory: npt.NDArray[np.float32] = np.copy(features['generic_agents'].ego[batch_idx])
            ego_trajectory[-1][:3] += self._random_offset_generator.sample()
            ego_x, ego_y, ego_yaw, ego_vx, ego_vy, ego_ax, ego_ay = ego_trajectory.T
            ego_velocity = np.linalg.norm(ego_trajectory[:, 3:5], axis=1)
            x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
            ref_traj = ego_trajectory[:, :3]
            _optimizer.set_reference_trajectory(x_curr, ref_traj)
            try:
                sol = _optimizer.solve()
            except RuntimeError:
                logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
                return (features, targets)
            if not sol.stats()['success']:
                logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
                return (features, targets)
            ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(_optimizer.position_x), sol.value(_optimizer.position_y), sol.value(_optimizer.yaw), sol.value(_optimizer.speed) * np.cos(sol.value(_optimizer.yaw)), sol.value(_optimizer.speed) * np.sin(sol.value(_optimizer.yaw)), np.concatenate((sol.value(_optimizer.accel), np.zeros(1))) * np.cos(sol.value(_optimizer.yaw)), np.concatenate((sol.value(_optimizer.accel), np.zeros(1))) * np.sin(sol.value(_optimizer.yaw))])
            ego_perturb = ego_perturb.T
            agents: List[npt.NDArray[np.float32]] = [agent_features[batch_idx] for agent_features in features['generic_agents'].agents.values()]
            if self.safety_check(ego_perturb, agents):
                features['generic_agents'].ego[batch_idx] = np.float32(ego_perturb)
        return (features, targets)

    @property
    def required_features(self) -> List[str]:
        """Inherited, see superclass."""
        return ['generic_agents']

    @property
    def required_targets(self) -> List[str]:
        """Inherited, see superclass."""
        return []

    @property
    def augmentation_probability(self) -> ParameterToScale:
        """Inherited, see superclass."""
        return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

    @property
    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """Inherited, see superclass."""
        return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def __init__(self, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
    """
        Initialize the augmentor.
        :param dt: Time interval between trajectory points.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
    self._dt = dt
    self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
    self._augment_prob = augment_prob

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    for batch_idx in range(len(features['generic_agents'].ego)):
        trajectory_length = len(features['generic_agents'].ego[batch_idx]) - 1
        _optimizer = ConstrainedNonlinearSmoother(trajectory_length, self._dt)
        ego_trajectory: npt.NDArray[np.float32] = np.copy(features['generic_agents'].ego[batch_idx])
        ego_trajectory[-1][:3] += self._random_offset_generator.sample()
        ego_x, ego_y, ego_yaw, ego_vx, ego_vy, ego_ax, ego_ay = ego_trajectory.T
        ego_velocity = np.linalg.norm(ego_trajectory[:, 3:5], axis=1)
        x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
        ref_traj = ego_trajectory[:, :3]
        _optimizer.set_reference_trajectory(x_curr, ref_traj)
        try:
            sol = _optimizer.solve()
        except RuntimeError:
            logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        if not sol.stats()['success']:
            logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(_optimizer.position_x), sol.value(_optimizer.position_y), sol.value(_optimizer.yaw), sol.value(_optimizer.speed) * np.cos(sol.value(_optimizer.yaw)), sol.value(_optimizer.speed) * np.sin(sol.value(_optimizer.yaw)), np.concatenate((sol.value(_optimizer.accel), np.zeros(1))) * np.cos(sol.value(_optimizer.yaw)), np.concatenate((sol.value(_optimizer.accel), np.zeros(1))) * np.sin(sol.value(_optimizer.yaw))])
        ego_perturb = ego_perturb.T
        agents: List[npt.NDArray[np.float32]] = [agent_features[batch_idx] for agent_features in features['generic_agents'].agents.values()]
        if self.safety_check(ego_perturb, agents):
            features['generic_agents'].ego[batch_idx] = np.float32(ego_perturb)
    return (features, targets)

class GaussianSmoothAgentAugmentor(AbstractAugmentor):
    """
    Augmentor that perturbs the ego's current position and future trajectory, then applies gaussian smoothing
    to generates a smooth trajectory over the current and future trajectory.
    """

    def __init__(self, mean: List[float], std: List[float], low: List[float], high: List[float], sigma: float, augment_prob: float, use_uniform_noise: bool=False) -> None:
        """
        Initialize the augmentor class.
        :param mean: Parameter to set mean vector of the Gaussian noise on [x, y, yaw].
        :param std: Parameter to set standard deviation vector of the Gaussian noise on [x, y, yaw].
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param sigma: Parameter to control the Gaussian smooth level.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
        self._sigma = sigma
        self._augment_prob = augment_prob
        self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        ego_trajectory: npt.NDArray[np.float32] = np.concatenate([features['agents'].ego[0][-1:, :], targets['trajectory'].data])
        trajectory_length, trajectory_dim = ego_trajectory.shape
        ego_trajectory += np.array([self._random_offset_generator.sample() for _ in range(trajectory_length)]) * np.expand_dims(np.exp(-np.arange(trajectory_length)), axis=1)
        ego_x, ego_y, ego_yaw = ego_trajectory.T
        step_t = np.linspace(0, 1, len(ego_x))
        step_resample_t = np.linspace(0, 1, 100)
        ego_resample_x = np.interp(step_resample_t, step_t, ego_x)
        ego_resample_y = np.interp(step_resample_t, step_t, ego_y)
        ego_resample_yaw = np.interp(step_resample_t, step_t, ego_yaw)
        ego_perturb_x = gaussian_filter1d(ego_resample_x, self._sigma)
        ego_perturb_y = gaussian_filter1d(ego_resample_y, self._sigma)
        ego_perturb_yaw = gaussian_filter1d(ego_resample_yaw, self._sigma)
        ego_perturb_x = np.interp(step_t, step_resample_t, ego_perturb_x)
        ego_perturb_y = np.interp(step_t, step_resample_t, ego_perturb_y)
        ego_perturb_yaw = np.interp(step_t, step_resample_t, ego_perturb_yaw)
        ego_perturb: npt.NDArray[np.float32] = np.vstack((ego_perturb_x, ego_perturb_y, ego_perturb_yaw)).T
        features['agents'].ego[0][-1] = ego_perturb[0]
        targets['trajectory'].data = ego_perturb[1:]
        return (features, targets)

    @property
    def required_features(self) -> List[str]:
        """Inherited, see superclass."""
        return ['agents']

    @property
    def required_targets(self) -> List[str]:
        """Inherited, see superclass."""
        return ['trajectory']

    @property
    def augmentation_probability(self) -> ParameterToScale:
        """Inherited, see superclass."""
        return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

    @property
    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """Inherited, see superclass."""
        return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def __init__(self, mean: List[float], std: List[float], low: List[float], high: List[float], sigma: float, augment_prob: float, use_uniform_noise: bool=False) -> None:
    """
        Initialize the augmentor class.
        :param mean: Parameter to set mean vector of the Gaussian noise on [x, y, yaw].
        :param std: Parameter to set standard deviation vector of the Gaussian noise on [x, y, yaw].
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param sigma: Parameter to control the Gaussian smooth level.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
    self._sigma = sigma
    self._augment_prob = augment_prob
    self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    ego_trajectory: npt.NDArray[np.float32] = np.concatenate([features['agents'].ego[0][-1:, :], targets['trajectory'].data])
    trajectory_length, trajectory_dim = ego_trajectory.shape
    ego_trajectory += np.array([self._random_offset_generator.sample() for _ in range(trajectory_length)]) * np.expand_dims(np.exp(-np.arange(trajectory_length)), axis=1)
    ego_x, ego_y, ego_yaw = ego_trajectory.T
    step_t = np.linspace(0, 1, len(ego_x))
    step_resample_t = np.linspace(0, 1, 100)
    ego_resample_x = np.interp(step_resample_t, step_t, ego_x)
    ego_resample_y = np.interp(step_resample_t, step_t, ego_y)
    ego_resample_yaw = np.interp(step_resample_t, step_t, ego_yaw)
    ego_perturb_x = gaussian_filter1d(ego_resample_x, self._sigma)
    ego_perturb_y = gaussian_filter1d(ego_resample_y, self._sigma)
    ego_perturb_yaw = gaussian_filter1d(ego_resample_yaw, self._sigma)
    ego_perturb_x = np.interp(step_t, step_resample_t, ego_perturb_x)
    ego_perturb_y = np.interp(step_t, step_resample_t, ego_perturb_y)
    ego_perturb_yaw = np.interp(step_t, step_resample_t, ego_perturb_yaw)
    ego_perturb: npt.NDArray[np.float32] = np.vstack((ego_perturb_x, ego_perturb_y, ego_perturb_yaw)).T
    features['agents'].ego[0][-1] = ego_perturb[0]
    targets['trajectory'].data = ego_perturb[1:]
    return (features, targets)

class ConstrainedNonlinearSmoother:
    """
    Smoothing a set of xy observations with a vehicle dynamics model.
    Solved with direct multiple-shooting.

    :param trajectory_len: trajectory length
    :param dt: timestep (sec)
    """

    def __init__(self, trajectory_len: int, dt: float):
        """
        :param trajectory_len: the length of trajectory to be optimized.
        :param dt: the time interval between trajectory points.
        """
        self.dt = dt
        self.trajectory_len = trajectory_len
        self.current_index = 0
        self._dts: npt.NDArray[np.float32] = np.asarray([[dt] * trajectory_len])
        self._init_optimization()

    def _init_optimization(self) -> None:
        """
        Initialize related variables and constraints for optimization.
        """
        self.nx = 4
        self.nu = 2
        self._optimizer = Opti()
        self._create_decision_variables()
        self._create_parameters()
        self._set_dynamic_constraints()
        self._set_state_constraints()
        self._set_control_constraints()
        self._set_objective()
        self._optimizer.solver('ipopt', {'ipopt.print_level': 0, 'print_time': 0, 'ipopt.sb': 'yes'})

    def set_reference_trajectory(self, x_curr: Sequence[float], reference_trajectory: Sequence[Pose]) -> None:
        """
        Set the reference trajectory that the smoother is trying to loosely track.

        :param x_curr: current state of size nx (x, y, yaw, speed)
        :param reference_trajectory: N+1 x 3 reference, where the second dim is for (x, y, yaw)
        """
        self._check_inputs(x_curr, reference_trajectory)
        self._optimizer.set_value(self.x_curr, DM(x_curr))
        self._optimizer.set_value(self.ref_traj, DM(reference_trajectory).T)
        self._set_initial_guess(x_curr, reference_trajectory)

    def set_solver_optimizerons(self, options: Dict[str, Any]) -> None:
        """
        Control solver options including verbosity.

        :param options: Dictionary containing optimization criterias
        """
        self._optimizer.solver('ipopt', options)

    def solve(self) -> OptiSol:
        """
        Solve the optimization problem. Assumes the reference trajectory was already set.

        :return Casadi optimization class
        """
        return self._optimizer.solve()

    def _create_decision_variables(self) -> None:
        """
        Define the decision variables for the trajectory optimization.
        """
        self.state = self._optimizer.variable(self.nx, self.trajectory_len + 1)
        self.position_x = self.state[0, :]
        self.position_y = self.state[1, :]
        self.yaw = self.state[2, :]
        self.speed = self.state[3, :]
        self.control = self._optimizer.variable(self.nu, self.trajectory_len)
        self.curvature = self.control[0, :]
        self.accel = self.control[1, :]
        self.curvature_rate = diff(self.curvature) / self._dts[:, 1:]
        self.jerk = diff(self.accel) / self._dts[:, 1:]
        self.lateral_accel = self.speed[:self.trajectory_len] ** 2 * self.curvature

    def _create_parameters(self) -> None:
        """
        Define the expert trjactory and current position for the trajectory optimizaiton.
        """
        self.ref_traj = self._optimizer.parameter(3, self.trajectory_len + 1)
        self.x_curr = self._optimizer.parameter(self.nx, 1)

    def _set_dynamic_constraints(self) -> None:
        """
        Set the system dynamics constraints as following:
          dx/dt = f(x,u)
          \\dot{x} = speed * cos(yaw)
          \\dot{y} = speed * sin(yaw)
          \\dot{yaw} = speed * curvature
          \\dot{speed} = accel
        """
        state = self.state
        control = self.control
        dt = self.dt

        def process(x: Sequence[float], u: Sequence[float]) -> Any:
            """Process for state propagation."""
            return vertcat(x[3] * cos(x[2]), x[3] * sin(x[2]), x[3] * u[0], u[1])
        for k in range(self.trajectory_len):
            k1 = process(state[:, k], control[:, k])
            k2 = process(state[:, k] + dt / 2 * k1, control[:, k])
            k3 = process(state[:, k] + dt / 2 * k2, control[:, k])
            k4 = process(state[:, k] + dt * k3, control[:, k])
            next_state = state[:, k] + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            self._optimizer.subject_to(state[:, k + 1] == next_state)

    def _set_control_constraints(self) -> None:
        """Set the hard control constraints."""
        curvature_limit = 1.0 / 5.0
        self._optimizer.subject_to(self._optimizer.bounded(-curvature_limit, self.curvature, curvature_limit))
        accel_limit = 4.0
        self._optimizer.subject_to(self._optimizer.bounded(-accel_limit, self.accel, accel_limit))

    def _set_state_constraints(self) -> None:
        """Set the hard state constraints."""
        self._optimizer.subject_to(self.state[:, self.current_index] == self.x_curr)
        max_speed = 35.0
        self._optimizer.subject_to(self._optimizer.bounded(0.0, self.speed, max_speed))
        max_yaw_rate = 1.75
        self._optimizer.subject_to(self._optimizer.bounded(-max_yaw_rate, diff(self.yaw) / self._dts, max_yaw_rate))
        max_lateral_accel = 4.0
        self._optimizer.subject_to(self._optimizer.bounded(-max_lateral_accel, self.speed[:, :self.trajectory_len] ** 2 * self.curvature, max_lateral_accel))

    def _set_objective(self) -> None:
        """Set the objective function. Use care when modifying these weights."""
        alpha_xy = 1.0
        alpha_yaw = 0.1
        alpha_rate = 0.08
        alpha_abs = 0.08
        alpha_lat_accel = 0.06
        cost_stage = alpha_xy * sumsqr(self.ref_traj[:2, :] - vertcat(self.position_x, self.position_y)) + alpha_yaw * sumsqr(self.ref_traj[2, :] - self.yaw) + alpha_rate * (sumsqr(self.curvature_rate) + sumsqr(self.jerk)) + alpha_abs * (sumsqr(self.curvature) + sumsqr(self.accel)) + alpha_lat_accel * sumsqr(self.lateral_accel)
        alpha_terminal_xy = 1.0
        alpha_terminal_yaw = 40.0
        cost_terminal = alpha_terminal_xy * sumsqr(self.ref_traj[:2, -1] - vertcat(self.position_x[-1], self.position_y[-1])) + alpha_terminal_yaw * sumsqr(self.ref_traj[2, -1] - self.yaw[-1])
        self._optimizer.minimize(cost_stage + self.trajectory_len / 4.0 * cost_terminal)

    def _set_initial_guess(self, x_curr: Sequence[float], reference_trajectory: Sequence[Pose]) -> None:
        """Set a warm-start for the solver based on the reference trajectory."""
        self._check_inputs(x_curr, reference_trajectory)
        self._optimizer.set_initial(self.state[:3, :], DM(reference_trajectory).T)
        self._optimizer.set_initial(self.state[3, :], DM(x_curr[3]))

    def _check_inputs(self, x_curr: Sequence[float], reference_trajectory: Sequence[Pose]) -> None:
        """Raise ValueError if inputs are not of proper size."""
        if len(x_curr) != self.nx:
            raise ValueError(f'x_curr length {len(x_curr)} must be equal to state dim {self.nx}')
        if len(reference_trajectory) != self.trajectory_len + 1:
            raise ValueError(f'reference traj length {len(reference_trajectory)} must be equal to {self.trajectory_len + 1}')

def solve(self) -> OptiSol:
    """
        Solve the optimization problem. Assumes the reference trajectory was already set.

        :return Casadi optimization class
        """
    return self._optimizer.solve()

class KinematicHistoryAgentAugmentor(AbstractAugmentor):
    """
    Data augmentation that perturbs the current ego position and generates a feasible trajectory history that
    satisfies a set of kinematic constraints.

    This involves constrained minimization of the following objective:
    * minimize dist(perturbed_trajectory, ground_truth_trajectory)


    Simple data augmentation that adds Gaussian noise to the ego current position with specified mean and std.
    """

    def __init__(self, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
        """
        Initialize the augmentor.
        :param dt: Time interval between trajectory points.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
        self._dt = dt
        self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
        self._augment_prob = augment_prob

    def safety_check(self, ego: npt.NDArray[np.float32], agents: npt.NDArray[np.float32]) -> bool:
        """
        Check if the augmented trajectory violates any safety check (going backwards, collision with other agents).
        :param ego: Perturbed ego feature tensor to be validated.
        :param agents: List of agent features to validate against.
        :return: Bool reflecting feature validity.
        """
        if np.diff(ego, axis=0)[-1][0] < 0.0001:
            return False
        dist_to_the_closest_agent = np.min(np.linalg.norm(np.array(agents)[:, :, :2] - ego[-1, :2], axis=1))
        if dist_to_the_closest_agent < 2.5:
            return False
        return True

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        for batch_idx in range(len(features['agents'].ego)):
            trajectory_length = len(features['agents'].ego[batch_idx]) - 1
            _optimizer = ConstrainedNonlinearSmoother(trajectory_length, self._dt)
            ego_trajectory: npt.NDArray[np.float32] = np.copy(features['agents'].ego[batch_idx])
            ego_trajectory[-1] += self._random_offset_generator.sample()
            ego_x, ego_y, ego_yaw = ego_trajectory.T
            ego_velocity = np.linalg.norm(np.diff(ego_trajectory[:, :2], axis=0), axis=1)
            x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
            ref_traj = ego_trajectory
            _optimizer.set_reference_trajectory(x_curr, ref_traj)
            try:
                sol = _optimizer.solve()
            except RuntimeError:
                logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
                return (features, targets)
            if not sol.stats()['success']:
                logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
                return (features, targets)
            ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(_optimizer.position_x), sol.value(_optimizer.position_y), sol.value(_optimizer.yaw)])
            ego_perturb = ego_perturb.T
            if self.safety_check(ego_perturb, features['agents'].agents[batch_idx]):
                features['agents'].ego[batch_idx] = np.float32(ego_perturb)
        return (features, targets)

    @property
    def required_features(self) -> List[str]:
        """Inherited, see superclass."""
        return ['agents']

    @property
    def required_targets(self) -> List[str]:
        """Inherited, see superclass."""
        return []

    @property
    def augmentation_probability(self) -> ParameterToScale:
        """Inherited, see superclass."""
        return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

    @property
    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """Inherited, see superclass."""
        return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def __init__(self, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
    """
        Initialize the augmentor.
        :param dt: Time interval between trajectory points.
        :param mean: mean of 3-dimensional Gaussian noise to [x, y, yaw]
        :param std: standard deviation of 3-dimenstional Gaussian noise to [x, y, yaw]
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: probability between 0 and 1 of applying the data augmentation
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
    self._dt = dt
    self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
    self._augment_prob = augment_prob

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    for batch_idx in range(len(features['agents'].ego)):
        trajectory_length = len(features['agents'].ego[batch_idx]) - 1
        _optimizer = ConstrainedNonlinearSmoother(trajectory_length, self._dt)
        ego_trajectory: npt.NDArray[np.float32] = np.copy(features['agents'].ego[batch_idx])
        ego_trajectory[-1] += self._random_offset_generator.sample()
        ego_x, ego_y, ego_yaw = ego_trajectory.T
        ego_velocity = np.linalg.norm(np.diff(ego_trajectory[:, :2], axis=0), axis=1)
        x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
        ref_traj = ego_trajectory
        _optimizer.set_reference_trajectory(x_curr, ref_traj)
        try:
            sol = _optimizer.solve()
        except RuntimeError:
            logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        if not sol.stats()['success']:
            logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(_optimizer.position_x), sol.value(_optimizer.position_y), sol.value(_optimizer.yaw)])
        ego_perturb = ego_perturb.T
        if self.safety_check(ego_perturb, features['agents'].agents[batch_idx]):
            features['agents'].ego[batch_idx] = np.float32(ego_perturb)
    return (features, targets)

class KinematicAgentAugmentor(AbstractAugmentor):
    """
    Data augmentation that perturbs the current ego position and generates a feasible future trajectory that
    satisfies a set of kinematic constraints.

    This involves constrained minimization of the following objective:
    * minimize dist(perturbed_trajectory, ground_truth_trajectory)
    """

    def __init__(self, trajectory_length: int, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
        """
        Initialize the augmentor.
        :param trajectory_length: Length of trajectory to be augmented.
        :param dt: Time interval between trajecotry points.
        :param mean: Parameter to set mean vector of the Gaussian noise on [x, y, yaw].
        :param std: Parameter to set standard deviation vector of the Gaussian noise on [x, y, yaw].
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
        self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
        self._augment_prob = augment_prob
        self._optimizer = ConstrainedNonlinearSmoother(trajectory_length, dt)

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        features['agents'].ego[0][-1] += self._random_offset_generator.sample()
        ego_trajectory: npt.NDArray[np.float32] = np.concatenate([features['agents'].ego[0][-1:, :], targets['trajectory'].data])
        ego_x, ego_y, ego_yaw = ego_trajectory.T
        ego_velocity = np.linalg.norm(np.diff(ego_trajectory[:, :2], axis=0), axis=1)
        x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
        ref_traj = ego_trajectory
        self._optimizer.set_reference_trajectory(x_curr, ref_traj)
        try:
            sol = self._optimizer.solve()
        except RuntimeError:
            logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        if not sol.stats()['success']:
            logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
            return (features, targets)
        ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(self._optimizer.position_x), sol.value(self._optimizer.position_y), sol.value(self._optimizer.yaw)])
        ego_perturb = ego_perturb.T
        features['agents'].ego[0][-1] = np.float32(ego_perturb[0])
        targets['trajectory'].data = np.float32(ego_perturb[1:])
        return (features, targets)

    @property
    def required_features(self) -> List[str]:
        """Inherited, see superclass."""
        return ['agents']

    @property
    def required_targets(self) -> List[str]:
        """Inherited, see superclass."""
        return ['trajectory']

    @property
    def augmentation_probability(self) -> ParameterToScale:
        """Inherited, see superclass."""
        return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

    @property
    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """Inherited, see superclass."""
        return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def __init__(self, trajectory_length: int, dt: float, mean: List[float], std: List[float], low: List[float], high: List[float], augment_prob: float, use_uniform_noise: bool=False) -> None:
    """
        Initialize the augmentor.
        :param trajectory_length: Length of trajectory to be augmented.
        :param dt: Time interval between trajecotry points.
        :param mean: Parameter to set mean vector of the Gaussian noise on [x, y, yaw].
        :param std: Parameter to set standard deviation vector of the Gaussian noise on [x, y, yaw].
        :param low: Parameter to set lower bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param high: Parameter to set upper bound vector of the Uniform noise on [x, y, yaw]. Used only if use_uniform_noise == True.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param use_uniform_noise: Parameter to decide to use uniform noise instead of gaussian noise if true.
        """
    self._random_offset_generator = UniformNoise(low, high) if use_uniform_noise else GaussianNoise(mean, std)
    self._augment_prob = augment_prob
    self._optimizer = ConstrainedNonlinearSmoother(trajectory_length, dt)

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    features['agents'].ego[0][-1] += self._random_offset_generator.sample()
    ego_trajectory: npt.NDArray[np.float32] = np.concatenate([features['agents'].ego[0][-1:, :], targets['trajectory'].data])
    ego_x, ego_y, ego_yaw = ego_trajectory.T
    ego_velocity = np.linalg.norm(np.diff(ego_trajectory[:, :2], axis=0), axis=1)
    x_curr = [ego_x[0], ego_y[0], ego_yaw[0], ego_velocity[0]]
    ref_traj = ego_trajectory
    self._optimizer.set_reference_trajectory(x_curr, ref_traj)
    try:
        sol = self._optimizer.solve()
    except RuntimeError:
        logger.error('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
        return (features, targets)
    if not sol.stats()['success']:
        logger.warning('Smoothing failed with status %s! Use G.T. instead' % sol.stats()['return_status'])
        return (features, targets)
    ego_perturb: npt.NDArray[np.float32] = np.vstack([sol.value(self._optimizer.position_x), sol.value(self._optimizer.position_y), sol.value(self._optimizer.yaw)])
    ego_perturb = ego_perturb.T
    features['agents'].ego[0][-1] = np.float32(ego_perturb[0])
    targets['trajectory'].data = np.float32(ego_perturb[1:])
    return (features, targets)

class TestKinematicHistoryAgentAugmentation(unittest.TestCase):
    """
    Test agent augmentation that perturbs the current ego position and generates a feasible trajectory history that
    satisfies a set of kinematic constraints.
    """

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.radius = 50
        self.features = {}
        self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[self.radius * np.random.rand(5, 1, 8) + self.radius / 2, self.radius * np.random.rand(5, 1, 8) + self.radius / 2])
        self.aug_feature_gt = {}
        self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.0120681393, -0.00109217957, 0.00104624288], [0.0268775601, -0.00105475327, 0.00400813782], [0.0512891984, -0.000897311768, 0.00889057227], [0.0852192154, -0.000480500022, 0.0156771013]])], agents=[self.radius * np.random.rand(5, 1, 8) + self.radius / 2])
        self.targets: Dict[str, Any] = {}
        augment_prob = 1.0
        dt = 0.1
        mean = [0.3, 0.1, np.pi / 12]
        std = [0.5, 0.1, np.pi / 12]
        low = [-0.1, -0.1, -0.1]
        high = [0.1, 0.1, 0.1]
        self.gaussian_augmentor = KinematicHistoryAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
        self.uniform_augmentor = KinematicHistoryAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

    def test_gaussian_augment(self) -> None:
        """
        Test gaussian augmentation.
        """
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['agents'].ego[0] - self.aug_feature_gt['agents'].ego[0]) < 0.1).all())

    def test_uniform_augment(self) -> None:
        """
        Test uniform augmentation.
        """
        original_feature_ego = self.features['agents'].ego[1].copy()
        aug_feature, _ = self.uniform_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['agents'].ego[1] - original_feature_ego) <= 0.1).all())

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.gaussian_augmentor._augment_prob = 0.0
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] == self.features['agents'].ego[0]).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.radius = 50
    self.features = {}
    self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[self.radius * np.random.rand(5, 1, 8) + self.radius / 2, self.radius * np.random.rand(5, 1, 8) + self.radius / 2])
    self.aug_feature_gt = {}
    self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.0120681393, -0.00109217957, 0.00104624288], [0.0268775601, -0.00105475327, 0.00400813782], [0.0512891984, -0.000897311768, 0.00889057227], [0.0852192154, -0.000480500022, 0.0156771013]])], agents=[self.radius * np.random.rand(5, 1, 8) + self.radius / 2])
    self.targets: Dict[str, Any] = {}
    augment_prob = 1.0
    dt = 0.1
    mean = [0.3, 0.1, np.pi / 12]
    std = [0.5, 0.1, np.pi / 12]
    low = [-0.1, -0.1, -0.1]
    high = [0.1, 0.1, 0.1]
    self.gaussian_augmentor = KinematicHistoryAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
    self.uniform_augmentor = KinematicHistoryAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

class TestGenericAgentDropoutAugmentation(unittest.TestCase):
    """Test agent augmentation that drops out random agents from the scene."""

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.features = {}
        self.agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
        self.features['generic_agents'] = GenericAgents(ego=[np.random.randn(5, 3), np.random.randn(5, 3)], agents={feature_name: [np.random.randn(5, 20, 8), np.random.randn(5, 50, 8)] for feature_name in self.agent_features})
        self.targets: Dict[str, Any] = {}
        augment_prob = 1.0
        self.dropout_rate = 0.5
        self.augmentor = GenericAgentDropoutAugmentor(augment_prob, self.dropout_rate)

    def test_augment(self) -> None:
        """
        Test augmentation.
        """
        features = deepcopy(self.features)
        aug_features, _ = self.augmentor.augment(features, self.targets)
        for feature_name in self.agent_features:
            for agents, aug_agents in zip(self.features['generic_agents'].agents[feature_name], aug_features['generic_agents'].agents[feature_name]):
                self.assertLess(aug_agents.shape[1], agents.shape[1])

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.augmentor._augment_prob = 0.0
        aug_features, _ = self.augmentor.augment(self.features, self.targets)
        for feature_name in self.agent_features:
            self.assertTrue((aug_features['generic_agents'].agents[feature_name][0] == self.features['generic_agents'].agents[feature_name][0]).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.features = {}
    self.agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
    self.features['generic_agents'] = GenericAgents(ego=[np.random.randn(5, 3), np.random.randn(5, 3)], agents={feature_name: [np.random.randn(5, 20, 8), np.random.randn(5, 50, 8)] for feature_name in self.agent_features})
    self.targets: Dict[str, Any] = {}
    augment_prob = 1.0
    self.dropout_rate = 0.5
    self.augmentor = GenericAgentDropoutAugmentor(augment_prob, self.dropout_rate)

class TestSimpleAgentAugmentation(unittest.TestCase):
    """Test agent augmentation that simply adds noise to the current ego position."""

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.features = {}
        self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8), np.random.randn(5, 1, 8)])
        self.aug_feature_gt = {}
        self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.362865111, 0.0867895137, 0.429461646]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
        self.targets: Dict[str, Any] = {}
        augment_prob = 1.0
        mean = [0.3, 0.1, np.pi / 12]
        std = [0.5, 0.1, np.pi / 12]
        low = [-0.1, -0.1, -0.1]
        high = [0.1, 0.1, 0.1]
        self.gaussian_augmentor = SimpleAgentAugmentor(mean, std, low, high, augment_prob, use_uniform_noise=False)
        self.uniform_augmentor = SimpleAgentAugmentor(mean, std, low, high, augment_prob, use_uniform_noise=True)

    def test_gaussian_augment(self) -> None:
        """
        Test gaussian augmentation.
        """
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] - self.aug_feature_gt['agents'].ego[0] < 0.0001).all())

    def test_uniform_augment(self) -> None:
        """
        Test uniform augmentation.
        """
        original_feature_ego = self.features['agents'].ego[1].copy()
        aug_feature, _ = self.uniform_augmentor.augment(self.features, self.targets)
        print(f'{original_feature_ego}, \n {aug_feature}')
        self.assertTrue((abs(aug_feature['agents'].ego[1] - original_feature_ego) <= 0.1).all())

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.gaussian_augmentor._augment_prob = 0.0
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] == self.features['agents'].ego[0]).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.features = {}
    self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8), np.random.randn(5, 1, 8)])
    self.aug_feature_gt = {}
    self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.362865111, 0.0867895137, 0.429461646]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
    self.targets: Dict[str, Any] = {}
    augment_prob = 1.0
    mean = [0.3, 0.1, np.pi / 12]
    std = [0.5, 0.1, np.pi / 12]
    low = [-0.1, -0.1, -0.1]
    high = [0.1, 0.1, 0.1]
    self.gaussian_augmentor = SimpleAgentAugmentor(mean, std, low, high, augment_prob, use_uniform_noise=False)
    self.uniform_augmentor = SimpleAgentAugmentor(mean, std, low, high, augment_prob, use_uniform_noise=True)

class TestKinematicAgentAugmentation(unittest.TestCase):
    """Test agent augmentation with kinematic constraints."""

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.features = {}
        self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8)])
        self.targets = {}
        self.targets['trajectory'] = Trajectory(data=np.array([[-0.0012336078, 0.0002229698, -2.075062e-05], [0.0032337871, 0.00035673147, -0.00011526359], [0.025042057, 0.00046393462, -0.00045901173], [0.24698858, -0.0015322007, -0.0013717031], [0.82662332, -0.0071887751, -0.0039011773], [1.7506398, -0.017746322, -0.0072191255], [3.0178127, -0.033933811, -0.0090915877], [4.5618219, -0.053034388, -0.0048586642], [6.3618584, -0.065912366, 0.00026488048], [8.3739414, -0.069805034, 0.0040571247], [10.576758, -0.044418037, 0.0074823718], [12.969443, -0.017768066, 0.0097025689]]))
        self.aug_feature_gt = {}
        self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.36286512, 0.0867895111, 0.429461658]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
        self.gaussian_aug_targets_gt = {}
        self.gaussian_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.41521129, 0.11039978, 0.41797668], [0.5046286, 0.14907575, 0.39849171], [0.63200253, 0.2006533, 0.37100676], [0.79846221, 0.26203236, 0.33552179], [1.0052546, 0.3291364, 0.29203683], [1.2535783, 0.39687237, 0.24055186], [1.5443755, 0.45909974, 0.1810669], [1.8780817, 0.50862163, 0.11358193], [2.2541707, 0.53959757, 0.050773341], [2.6713488, 0.55327171, 0.014758691], [3.1287551, 0.55699998, 0.0015426531], [3.6260972, 0.55770481, 0.0012917991]]))
        self.uniform_aug_targets_gt = {}
        self.uniform_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.05273135, -0.04831281, -0.08689969], [0.11795828, -0.05359042, -0.07457177], [0.22317114, -0.06049316, -0.05645524], [0.3684539, -0.06721046, -0.03595094], [0.553826, -0.07214818, -0.01731013], [0.77925223, -0.0745298, -0.00381898], [1.0446922, -0.07455366, 0.00363919], [1.3501287, -0.07300503, 0.00650118], [1.6955612, -0.07065626, 0.00709759], [2.080992, -0.06789713, 0.00721934], [2.5064206, -0.06473273, 0.00765666], [2.9717717, -0.06097136, 0.00850872]]))
        N = 12
        dt = 0.1
        augment_prob = 1.0
        mean = [0.3, 0.1, np.pi / 12]
        std = [0.5, 0.1, np.pi / 12]
        low = [-0.1, -0.1, -0.1]
        high = [0.1, 0.1, 0.1]
        self.gaussian_augmentor = KinematicAgentAugmentor(N, dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
        self.uniform_augmentor = KinematicAgentAugmentor(N, dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

    def test_gaussian_augment(self) -> None:
        """
        Test gaussian augmentation.
        """
        aug_feature, aug_targets = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] - self.aug_feature_gt['agents'].ego[0] < 0.0001).all())
        self.assertTrue((aug_targets['trajectory'].data - self.gaussian_aug_targets_gt['trajectory'].data < 0.0001).all())

    def test_uniform_augment(self) -> None:
        """
        Test uniform augmentation.
        """
        features_ego = self.features['agents'].ego[0].copy()
        aug_feature, aug_targets = self.uniform_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['agents'].ego[0] - features_ego) <= 0.1).all())
        self.assertTrue((abs(aug_targets['trajectory'].data - self.uniform_aug_targets_gt['trajectory'].data) <= 0.1).all())

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.gaussian_augmentor._augment_prob = 0.0
        aug_feature, aug_targets = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] == self.features['agents'].ego[0]).all())
        self.assertTrue((aug_targets['trajectory'].data == self.targets['trajectory'].data).all())

    def test_input_validation(self) -> None:
        """
        Test the augmentor's validation check.
        """
        features = {'agents': None, 'test_feature': None}
        targets = {'trajectory': None, 'test_target': None}
        self.gaussian_augmentor.validate(features, targets)
        features = {'test_feature': None}
        targets = {'test_target': None}
        self.assertRaises(AssertionError, self.gaussian_augmentor.validate, features, targets)

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.features = {}
    self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8)])
    self.targets = {}
    self.targets['trajectory'] = Trajectory(data=np.array([[-0.0012336078, 0.0002229698, -2.075062e-05], [0.0032337871, 0.00035673147, -0.00011526359], [0.025042057, 0.00046393462, -0.00045901173], [0.24698858, -0.0015322007, -0.0013717031], [0.82662332, -0.0071887751, -0.0039011773], [1.7506398, -0.017746322, -0.0072191255], [3.0178127, -0.033933811, -0.0090915877], [4.5618219, -0.053034388, -0.0048586642], [6.3618584, -0.065912366, 0.00026488048], [8.3739414, -0.069805034, 0.0040571247], [10.576758, -0.044418037, 0.0074823718], [12.969443, -0.017768066, 0.0097025689]]))
    self.aug_feature_gt = {}
    self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.36286512, 0.0867895111, 0.429461658]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
    self.gaussian_aug_targets_gt = {}
    self.gaussian_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.41521129, 0.11039978, 0.41797668], [0.5046286, 0.14907575, 0.39849171], [0.63200253, 0.2006533, 0.37100676], [0.79846221, 0.26203236, 0.33552179], [1.0052546, 0.3291364, 0.29203683], [1.2535783, 0.39687237, 0.24055186], [1.5443755, 0.45909974, 0.1810669], [1.8780817, 0.50862163, 0.11358193], [2.2541707, 0.53959757, 0.050773341], [2.6713488, 0.55327171, 0.014758691], [3.1287551, 0.55699998, 0.0015426531], [3.6260972, 0.55770481, 0.0012917991]]))
    self.uniform_aug_targets_gt = {}
    self.uniform_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.05273135, -0.04831281, -0.08689969], [0.11795828, -0.05359042, -0.07457177], [0.22317114, -0.06049316, -0.05645524], [0.3684539, -0.06721046, -0.03595094], [0.553826, -0.07214818, -0.01731013], [0.77925223, -0.0745298, -0.00381898], [1.0446922, -0.07455366, 0.00363919], [1.3501287, -0.07300503, 0.00650118], [1.6955612, -0.07065626, 0.00709759], [2.080992, -0.06789713, 0.00721934], [2.5064206, -0.06473273, 0.00765666], [2.9717717, -0.06097136, 0.00850872]]))
    N = 12
    dt = 0.1
    augment_prob = 1.0
    mean = [0.3, 0.1, np.pi / 12]
    std = [0.5, 0.1, np.pi / 12]
    low = [-0.1, -0.1, -0.1]
    high = [0.1, 0.1, 0.1]
    self.gaussian_augmentor = KinematicAgentAugmentor(N, dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
    self.uniform_augmentor = KinematicAgentAugmentor(N, dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

class TestKinematicHistoryGenericAgentAugmentation(unittest.TestCase):
    """
    Test agent augmentation that perturbs the current ego position and generates a feasible trajectory history that
    satisfies a set of kinematic constraints.
    """

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.radius = 50
        self.features = {}
        self.agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
        self.features['generic_agents'] = GenericAgents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.004325964, -0.00069646863, -9.3163371e-06, 0.0, 0.0, 0.0, 0.0], [0.0024353617, -0.00037753209, 4.7789731e-06, 0.0, 0.0, 0.0, 0.0], [0.0011352128, -0.0001273104, 3.8040514e-05, 0.0, 0.0, 0.0, 0.0], [1.1641532e-10, 0.0, -3.0870851e-19, 0.0, 0.0, 0.0, 0.0]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.004325964, -0.00069646863, -9.3163371e-06, 0.0, 0.0, 0.0, 0.0], [0.0024353617, -0.00037753209, 4.7789731e-06, 0.0, 0.0, 0.0, 0.0], [0.0011352128, -0.0001273104, 3.8040514e-05, 0.0, 0.0, 0.0, 0.0], [1.1641532e-10, 0.0, -3.0870851e-19, 0.0, 0.0, 0.0, 0.0]])], agents={feature_name: [self.radius * np.random.rand(5, 1, 8) + self.radius / 2, self.radius * np.random.rand(5, 1, 8) + self.radius / 2] for feature_name in self.agent_features})
        for sample_idx in range(len(self.features['generic_agents'].ego)):
            self.features['generic_agents'].ego[sample_idx][:-1, 3:5] = np.diff(self.features['generic_agents'].ego[sample_idx][:, :2], axis=0)
            self.features['generic_agents'].ego[sample_idx][:-1, 5:] = np.diff(self.features['generic_agents'].ego[sample_idx][:, 3:5], axis=0)
        self.aug_feature_gt = {}
        self.aug_feature_gt['generic_agents'] = GenericAgents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.0120681393, -0.00109217957, 0.00104624288, 0.0, 0.0, 0.0, 0.0], [0.0268775601, -0.00105475327, 0.00400813782, 0.0, 0.0, 0.0, 0.0], [0.0512891984, -0.000897311768, 0.00889057227, 0.0, 0.0, 0.0, 0.0], [0.0852192154, -0.000480500022, 0.0156771013, 0.0, 0.0, 0.0, 0.0]])], agents={feature_name: [self.radius * np.random.rand(5, 1, 8) + self.radius / 2] for feature_name in self.agent_features})
        for sample_idx in range(len(self.aug_feature_gt['generic_agents'].ego)):
            self.aug_feature_gt['generic_agents'].ego[sample_idx][:-1, 3:5] = np.diff(self.aug_feature_gt['generic_agents'].ego[sample_idx][:, :2], axis=0)
            self.aug_feature_gt['generic_agents'].ego[sample_idx][:-1, 5:] = np.diff(self.aug_feature_gt['generic_agents'].ego[sample_idx][:, 3:5], axis=0)
        self.targets: Dict[str, Any] = {}
        augment_prob = 1.0
        dt = 0.1
        mean = [0.3, 0.1, np.pi / 12]
        std = [0.5, 0.1, np.pi / 12]
        low = [-0.1, -0.1, -0.1]
        high = [0.1, 0.1, 0.1]
        self.gaussian_augmentor = KinematicHistoryGenericAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
        self.uniform_augmentor = KinematicHistoryGenericAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

    def test_gaussian_augment(self) -> None:
        """
        Test gaussian augmentation.
        """
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['generic_agents'].ego[0][:, :3] - self.aug_feature_gt['generic_agents'].ego[0][:, :3]) < 0.1).all())

    def test_uniform_augment(self) -> None:
        """
        Test uniform augmentation.
        """
        original_feature_ego = self.features['generic_agents'].ego[1].copy()[:, :3]
        aug_feature, _ = self.uniform_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['generic_agents'].ego[1][:, :3] - original_feature_ego) <= 0.1).all())

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.gaussian_augmentor._augment_prob = 0.0
        aug_feature, _ = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['generic_agents'].ego[0] == self.features['generic_agents'].ego[0]).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.radius = 50
    self.features = {}
    self.agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
    self.features['generic_agents'] = GenericAgents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.004325964, -0.00069646863, -9.3163371e-06, 0.0, 0.0, 0.0, 0.0], [0.0024353617, -0.00037753209, 4.7789731e-06, 0.0, 0.0, 0.0, 0.0], [0.0011352128, -0.0001273104, 3.8040514e-05, 0.0, 0.0, 0.0, 0.0], [1.1641532e-10, 0.0, -3.0870851e-19, 0.0, 0.0, 0.0, 0.0]]), np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.004325964, -0.00069646863, -9.3163371e-06, 0.0, 0.0, 0.0, 0.0], [0.0024353617, -0.00037753209, 4.7789731e-06, 0.0, 0.0, 0.0, 0.0], [0.0011352128, -0.0001273104, 3.8040514e-05, 0.0, 0.0, 0.0, 0.0], [1.1641532e-10, 0.0, -3.0870851e-19, 0.0, 0.0, 0.0, 0.0]])], agents={feature_name: [self.radius * np.random.rand(5, 1, 8) + self.radius / 2, self.radius * np.random.rand(5, 1, 8) + self.radius / 2] for feature_name in self.agent_features})
    for sample_idx in range(len(self.features['generic_agents'].ego)):
        self.features['generic_agents'].ego[sample_idx][:-1, 3:5] = np.diff(self.features['generic_agents'].ego[sample_idx][:, :2], axis=0)
        self.features['generic_agents'].ego[sample_idx][:-1, 5:] = np.diff(self.features['generic_agents'].ego[sample_idx][:, 3:5], axis=0)
    self.aug_feature_gt = {}
    self.aug_feature_gt['generic_agents'] = GenericAgents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05, 0.0, 0.0, 0.0, 0.0], [0.0120681393, -0.00109217957, 0.00104624288, 0.0, 0.0, 0.0, 0.0], [0.0268775601, -0.00105475327, 0.00400813782, 0.0, 0.0, 0.0, 0.0], [0.0512891984, -0.000897311768, 0.00889057227, 0.0, 0.0, 0.0, 0.0], [0.0852192154, -0.000480500022, 0.0156771013, 0.0, 0.0, 0.0, 0.0]])], agents={feature_name: [self.radius * np.random.rand(5, 1, 8) + self.radius / 2] for feature_name in self.agent_features})
    for sample_idx in range(len(self.aug_feature_gt['generic_agents'].ego)):
        self.aug_feature_gt['generic_agents'].ego[sample_idx][:-1, 3:5] = np.diff(self.aug_feature_gt['generic_agents'].ego[sample_idx][:, :2], axis=0)
        self.aug_feature_gt['generic_agents'].ego[sample_idx][:-1, 5:] = np.diff(self.aug_feature_gt['generic_agents'].ego[sample_idx][:, 3:5], axis=0)
    self.targets: Dict[str, Any] = {}
    augment_prob = 1.0
    dt = 0.1
    mean = [0.3, 0.1, np.pi / 12]
    std = [0.5, 0.1, np.pi / 12]
    low = [-0.1, -0.1, -0.1]
    high = [0.1, 0.1, 0.1]
    self.gaussian_augmentor = KinematicHistoryGenericAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=False)
    self.uniform_augmentor = KinematicHistoryGenericAgentAugmentor(dt, mean, std, low, high, augment_prob, use_uniform_noise=True)

class TestAgentDropoutAugmentation(unittest.TestCase):
    """Test agent augmentation that drops out random agents from the scene."""

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.features = {}
        self.features['agents'] = Agents(ego=[np.random.randn(5, 3), np.random.randn(5, 3)], agents=[np.random.randn(5, 20, 8), np.random.randn(5, 50, 8)])
        self.targets: Dict[str, Any] = {}
        augment_prob = 1.0
        self.dropout_rate = 0.5
        self.augmentor = AgentDropoutAugmentor(augment_prob, self.dropout_rate)

    def test_augment(self) -> None:
        """
        Test augmentation.
        """
        features = deepcopy(self.features)
        aug_features, _ = self.augmentor.augment(features, self.targets)
        for agents, aug_agents in zip(self.features['agents'].agents, aug_features['agents'].agents):
            self.assertLess(aug_agents.shape[1], agents.shape[1])

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.augmentor._augment_prob = 0.0
        aug_features, _ = self.augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_features['agents'].agents[0] == self.features['agents'].agents[0]).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.features = {}
    self.features['agents'] = Agents(ego=[np.random.randn(5, 3), np.random.randn(5, 3)], agents=[np.random.randn(5, 20, 8), np.random.randn(5, 50, 8)])
    self.targets: Dict[str, Any] = {}
    augment_prob = 1.0
    self.dropout_rate = 0.5
    self.augmentor = AgentDropoutAugmentor(augment_prob, self.dropout_rate)

class TestGaussianSmoothAgentAugmentation(unittest.TestCase):
    """Test agent augmentation with gaussian smooth noise."""

    def setUp(self) -> None:
        """Set up test case."""
        np.random.seed(2022)
        self.features = {}
        self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8)])
        self.targets = {}
        self.targets['trajectory'] = Trajectory(data=np.array([[-0.0012336078, 0.0002229698, -2.075062e-05], [0.0032337871, 0.00035673147, -0.00011526359], [0.025042057, 0.00046393462, -0.00045901173], [0.24698858, -0.0015322007, -0.0013717031], [0.82662332, -0.0071887751, -0.0039011773], [1.7506398, -0.017746322, -0.0072191255], [3.0178127, -0.033933811, -0.0090915877], [4.5618219, -0.053034388, -0.0048586642], [6.3618584, -0.065912366, 0.00026488048], [8.3739414, -0.069805034, 0.0040571247], [10.576758, -0.044418037, 0.0074823718], [12.969443, -0.017768066, 0.0097025689]]))
        self.aug_feature_gt = {}
        self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.267742378, 0.0587639301, 0.305916953]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
        self.gaussian_aug_targets_gt = {}
        self.gaussian_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.179909768, 0.0346292143, 0.169823954], [0.10860577, 0.0197756017, 0.042442404], [0.0955989353, 0.00718025938, 0.0104373998], [0.32935287, -0.00092038409, 0.000919450476], [0.915527184, -0.00788396897, -0.00340438637], [1.84272996, -0.0188512783, -0.00617531861], [3.09345437, -0.0344966704, -0.0072624205], [4.62998953, -0.0514234703, -0.00448675278], [6.41906077, -0.0632653042, -1.90822629e-05], [8.4253027, -0.062546126, 0.00395074816], [10.5772538, -0.0442685352, 0.00714697555], [11.9537668, -0.0290942382, 0.00873650844]]))
        self.uniform_aug_targets_gt = {}
        self.uniform_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[-0.0123269903, 0.00395750476, -0.00366945959], [0.0052339853, 0.00876677051, 0.00482984929], [0.0811338362, 0.00287675577, -0.00247428679], [0.341575812, -0.00256694967, -0.00236505408], [0.919201714, -0.00857337111, -0.00399194094], [1.84200781, -0.0191452871, -0.00689646769], [3.09258798, -0.0346222537, -0.00760822625], [4.62963856, -0.0514547445, -0.00456260133], [6.41901491, -0.0632771927, -4.26804288e-05], [8.42531047, -0.0625500536, 0.0039344597], [10.5772518, -0.0442706406, 0.00713952217], [11.9537637, -0.0290951136, 0.00873232027]]))
        augment_prob = 1.0
        mean = [0.3, 0.1, np.pi / 12]
        std = [0.5, 0.1, np.pi / 12]
        low = [-0.1, -0.1, -0.1]
        high = [0.1, 0.1, 0.1]
        sigma = 5.0
        self.gaussian_augmentor = GaussianSmoothAgentAugmentor(mean, std, low, high, sigma, augment_prob, use_uniform_noise=False)
        self.uniform_augmentor = GaussianSmoothAgentAugmentor(mean, std, low, high, sigma, augment_prob, use_uniform_noise=True)

    def test_gaussian_augment(self) -> None:
        """
        Test gaussian augmentation.
        """
        aug_feature, aug_targets = self.gaussian_augmentor.augment(self.features, self.targets)
        print(aug_feature, aug_targets)
        self.assertTrue((aug_feature['agents'].ego[0] - self.aug_feature_gt['agents'].ego[0] < 0.0001).all())
        self.assertTrue((aug_targets['trajectory'].data - self.gaussian_aug_targets_gt['trajectory'].data < 0.0001).all())

    def test_uniform_augment(self) -> None:
        """
        Test uniform augmentation.
        """
        original_features_ego = self.features['agents'].ego[0].copy()
        aug_feature, aug_targets = self.uniform_augmentor.augment(self.features, self.targets)
        self.assertTrue((abs(aug_feature['agents'].ego[0] - original_features_ego) < 0.1).all())
        self.assertTrue((aug_targets['trajectory'].data - self.uniform_aug_targets_gt['trajectory'].data < 0.0001).all())

    def test_no_augment(self) -> None:
        """
        Test no augmentation when aug_prob is set to 0.
        """
        self.gaussian_augmentor._augment_prob = 0.0
        aug_feature, aug_targets = self.gaussian_augmentor.augment(self.features, self.targets)
        self.assertTrue((aug_feature['agents'].ego[0] == self.features['agents'].ego[0]).all())
        self.assertTrue((aug_targets['trajectory'].data == self.targets['trajectory'].data).all())

def setUp(self) -> None:
    """Set up test case."""
    np.random.seed(2022)
    self.features = {}
    self.features['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [1.1641532e-10, 0.0, -3.0870851e-19]])], agents=[np.random.randn(5, 1, 8)])
    self.targets = {}
    self.targets['trajectory'] = Trajectory(data=np.array([[-0.0012336078, 0.0002229698, -2.075062e-05], [0.0032337871, 0.00035673147, -0.00011526359], [0.025042057, 0.00046393462, -0.00045901173], [0.24698858, -0.0015322007, -0.0013717031], [0.82662332, -0.0071887751, -0.0039011773], [1.7506398, -0.017746322, -0.0072191255], [3.0178127, -0.033933811, -0.0090915877], [4.5618219, -0.053034388, -0.0048586642], [6.3618584, -0.065912366, 0.00026488048], [8.3739414, -0.069805034, 0.0040571247], [10.576758, -0.044418037, 0.0074823718], [12.969443, -0.017768066, 0.0097025689]]))
    self.aug_feature_gt = {}
    self.aug_feature_gt['agents'] = Agents(ego=[np.array([[0.0069434252, -0.001094915, 2.1299818e-05], [0.004325964, -0.00069646863, -9.3163371e-06], [0.0024353617, -0.00037753209, 4.7789731e-06], [0.0011352128, -0.0001273104, 3.8040514e-05], [0.267742378, 0.0587639301, 0.305916953]])], agents=[np.array([[[-0.000527899086, -0.274901425, -0.139285562, 1.98468616, 0.282109326, 0.760808658, 0.300981606, 0.540297269]], [[0.373497287, 0.377813394, -0.0902131926, -2.30594327, 1.14276002, -1.53565429, -0.863752018, 1.01654494]], [[1.03396388, -0.824492228, 0.0189048564, -0.383343556, -0.304185475, 0.997291506, -0.127273841, -1.4758859]], [[-1.94090633, 0.833648924, -0.567217888, 1.17448696, 0.319068832, 0.190870428, 0.369270181, -0.101147863]], [[-0.941809489, -1.40414171, 2.08064701, -0.120316234, 0.759791879, 1.82743214, -0.660727087, -0.807806261]]])])
    self.gaussian_aug_targets_gt = {}
    self.gaussian_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[0.179909768, 0.0346292143, 0.169823954], [0.10860577, 0.0197756017, 0.042442404], [0.0955989353, 0.00718025938, 0.0104373998], [0.32935287, -0.00092038409, 0.000919450476], [0.915527184, -0.00788396897, -0.00340438637], [1.84272996, -0.0188512783, -0.00617531861], [3.09345437, -0.0344966704, -0.0072624205], [4.62998953, -0.0514234703, -0.00448675278], [6.41906077, -0.0632653042, -1.90822629e-05], [8.4253027, -0.062546126, 0.00395074816], [10.5772538, -0.0442685352, 0.00714697555], [11.9537668, -0.0290942382, 0.00873650844]]))
    self.uniform_aug_targets_gt = {}
    self.uniform_aug_targets_gt['trajectory'] = Trajectory(data=np.array([[-0.0123269903, 0.00395750476, -0.00366945959], [0.0052339853, 0.00876677051, 0.00482984929], [0.0811338362, 0.00287675577, -0.00247428679], [0.341575812, -0.00256694967, -0.00236505408], [0.919201714, -0.00857337111, -0.00399194094], [1.84200781, -0.0191452871, -0.00689646769], [3.09258798, -0.0346222537, -0.00760822625], [4.62963856, -0.0514547445, -0.00456260133], [6.41901491, -0.0632771927, -4.26804288e-05], [8.42531047, -0.0625500536, 0.0039344597], [10.5772518, -0.0442706406, 0.00713952217], [11.9537637, -0.0290951136, 0.00873232027]]))
    augment_prob = 1.0
    mean = [0.3, 0.1, np.pi / 12]
    std = [0.5, 0.1, np.pi / 12]
    low = [-0.1, -0.1, -0.1]
    high = [0.1, 0.1, 0.1]
    sigma = 5.0
    self.gaussian_augmentor = GaussianSmoothAgentAugmentor(mean, std, low, high, sigma, augment_prob, use_uniform_noise=False)
    self.uniform_augmentor = GaussianSmoothAgentAugmentor(mean, std, low, high, sigma, augment_prob, use_uniform_noise=True)

@dataclass
class Agents(AbstractModelFeature):
    """
    Model input feature representing the present and past states of the ego and agents.

    The structure inludes:
        ego: List[<np.ndarray: num_frames, 3>].
            The outer list is the batch dimension.
            The num_frames includes both present and past frames.
            The last dimension is the ego pose (x, y, heading) at time t.
            Example dimensions: 8 (batch_size) x 5 (1 present + 4 past frames) x 3
        agents: List[<np.ndarray: num_frames, num_agents, 8>].
            The outer list is the batch dimension.
            The num_frames includes both present and past frames.
            The num_agents is padded to fit the largest number of agents across all frames.
            The last dimension is the agent pose (x, y, heading) velocities (vx, vy, yaw rate)
             and size (length, width) at time t.

    The present/past frames dimension is populated in increasing chronological order, i.e. (t_-N, ..., t_-1, t_0)
    where N is the number of frames in the feature

    In both cases, the outer List represent number of batches. This is a special feature where each batch entry
    can have different size. For that reason, the feature can not be placed to a single tensor,
    and we batch the feature with a custom `collate` function
    """
    ego: List[FeatureDataType]
    agents: List[FeatureDataType]

    def __post_init__(self) -> None:
        """Sanitize attributes of dataclass."""
        if len(self.ego) != len(self.agents):
            raise AssertionError(f'Not consistent length of batches! {len(self.ego)} != {len(self.agents)}')
        if len(self.ego) == 0:
            raise AssertionError('Batch size has to be > 0!')
        if self.ego[0].ndim != 2:
            raise AssertionError(f'Ego feature samples does not conform to feature dimensions! Got ndim: {self.ego[0].ndim} , expected 2 [num_frames, 3]')
        if self.agents[0].ndim != 3:
            raise AssertionError(f'Agent feature samples does not conform to feature dimensions! Got ndim: {self.agents[0].ndim} , expected 3 [num_frames, num_agents, 8]')
        for i in range(len(self.ego)):
            if int(self.ego[i].shape[0]) != self.num_frames or int(self.agents[i].shape[0]) != self.num_frames:
                raise AssertionError('Agent feature samples have different number of frames!')

    @cached_property
    def is_valid(self) -> bool:
        """Inherited, see superclass."""
        return len(self.ego) > 0 and len(self.agents) > 0 and (len(self.ego) == len(self.agents)) and (len(self.ego[0]) > 0) and (len(self.agents[0]) > 0) and (len(self.ego[0]) == len(self.agents[0]) > 0) and (self.ego[0].shape[-1] == self.ego_state_dim()) and (self.agents[0].shape[-1] == self.agents_states_dim())

    @property
    def batch_size(self) -> int:
        """
        :return: number of batches
        """
        return len(self.ego)

    @classmethod
    def collate(cls, batch: List[Agents]) -> Agents:
        """
        Implemented. See interface.
        Collates a list of features that each have batch size of 1.
        """
        return Agents(ego=[item.ego[0] for item in batch], agents=[item.agents[0] for item in batch])

    def to_feature_tensor(self) -> Agents:
        """Implemented. See interface."""
        return Agents(ego=[to_tensor(ego) for ego in self.ego], agents=[to_tensor(agents) for agents in self.agents])

    def to_device(self, device: torch.device) -> Agents:
        """Implemented. See interface."""
        return Agents(ego=[to_tensor(ego).to(device=device) for ego in self.ego], agents=[to_tensor(agents).to(device=device) for agents in self.agents])

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Agents:
        """Implemented. See interface."""
        return Agents(ego=data['ego'], agents=data['agents'])

    def unpack(self) -> List[Agents]:
        """Implemented. See interface."""
        return [Agents([ego], [agents]) for ego, agents in zip(self.ego, self.agents)]

    def num_agents_in_sample(self, sample_idx: int) -> int:
        """
        Returns the number of agents at a given batch
        :param sample_idx: the batch index of interest
        :return: number of agents in the given batch
        """
        return self.agents[sample_idx].shape[1]

    @staticmethod
    def ego_state_dim() -> int:
        """
        :return: ego state dimension
        """
        return EgoFeatureIndex.dim()

    @staticmethod
    def agents_states_dim() -> int:
        """
        :return: agent state dimension
        """
        return AgentFeatureIndex.dim()

    @property
    def num_frames(self) -> int:
        """
        :return: number of frames.
        """
        return int(self.ego[0].shape[0])

    @property
    def ego_feature_dim(self) -> int:
        """
        :return: ego feature dimension. Note, the plus one is to account for the present frame
        """
        return Agents.ego_state_dim() * self.num_frames

    @property
    def agents_features_dim(self) -> int:
        """
        :return: ego feature dimension. Note, the plus one is to account for the present frame
        """
        return Agents.agents_states_dim() * self.num_frames

    def has_agents(self, batch_idx: int) -> bool:
        """
        Check whether agents exist in the feature.
        :param batch_idx: the batch index of interest
        :return: whether agents exist in the feature
        """
        return self.num_agents_in_sample(batch_idx) > 0

    def get_flatten_agents_features_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Flatten agents' features by stacking the agents' states along the num_frame dimension
        <np.ndarray: num_frames, num_agents, 8>] -> <np.ndarray: num_agents, num_frames x 8>]

        :param sample_idx: the sample index of interest
        :return: <FeatureDataType: num_agents, num_frames x 8>] agent feature
        """
        if self.num_agents_in_sample(sample_idx) == 0:
            if isinstance(self.ego[sample_idx], torch.Tensor):
                return torch.empty((0, self.num_frames * AgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype, device=self.ego[sample_idx].device)
            else:
                return np.empty((0, self.num_frames * AgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype)
        data = self.agents[sample_idx]
        axes = (1, 0) if isinstance(data, torch.Tensor) else (1, 0, 2)
        return data.transpose(*axes).reshape(data.shape[1], -1)

    def get_present_ego_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return the present ego in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: 8>. ego at sample index
        """
        return self.ego[sample_idx][-1]

    def get_present_agents_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return the present agents in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: num_agents, 8>. all agents at sample index
        """
        return self.agents[sample_idx][-1]

    def get_ego_agents_center_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return ego center in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: 2>. (x, y) positions of the ego's center at sample index
        """
        return self.get_present_ego_in_sample(sample_idx)[:EgoFeatureIndex.y() + 1]

    def get_agents_centers_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents'centers in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: num_agents, 2>. (x, y) positions of the agents' centers at the sample index
        """
        return self.get_present_agents_in_sample(sample_idx)[:, :AgentFeatureIndex.y() + 1]

    def get_agents_length_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents' length in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: num_agents>. lengths of all the agents at the sample index
        """
        return self.get_present_agents_in_sample(sample_idx)[:, AgentFeatureIndex.length()]

    def get_agents_width_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents' width in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: num_agents>. width of all the agents at the sample index
        """
        return self.get_present_agents_in_sample(sample_idx)[:, AgentFeatureIndex.width()]

    def get_agent_corners_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents' corners in the given sample index
        :param sample_idx: the batch index of interest
        :return: <FeatureDataType: num_agents, 4, 3>. (x, y, 1) positions of all the agents' corners at the sample index
        """
        widths = self.get_agents_width_in_sample(sample_idx)
        lengths = self.get_agents_length_in_sample(sample_idx)
        half_widths = widths / 2.0
        half_lengths = lengths / 2.0
        feature_cls = np.array if isinstance(widths, np.ndarray) else torch.Tensor
        return feature_cls([[[half_length, half_width, 1.0], [-half_length, half_width, 1.0], [-half_length, -half_width, 1.0], [half_length, -half_width, 1.0]] for half_width, half_length in zip(half_widths, half_lengths)])

@classmethod
def collate(cls, batch: List[Agents]) -> Agents:
    """
        Implemented. See interface.
        Collates a list of features that each have batch size of 1.
        """
    return Agents(ego=[item.ego[0] for item in batch], agents=[item.agents[0] for item in batch])

def to_device(self, device: torch.device) -> Agents:
    """Implemented. See interface."""
    return Agents(ego=[to_tensor(ego).to(device=device) for ego in self.ego], agents=[to_tensor(agents).to(device=device) for agents in self.agents])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Agents:
    """Implemented. See interface."""
    return Agents(ego=data['ego'], agents=data['agents'])

def unpack(self) -> List[Agents]:
    """Implemented. See interface."""
    return [Agents([ego], [agents]) for ego, agents in zip(self.ego, self.agents)]

class WeightedAverageMetricAggregator(AbstractMetricAggregator):
    """Metric aggregator by implementing weighted sum."""

    def __init__(self, name: str, metric_weights: Dict[str, float], file_name: str, aggregator_save_path: Path, multiple_metrics: List[str], challenge_name: Optional[str]=None):
        """
        Initializes the WeightedAverageMetricAggregator class.
        :param name: Metric aggregator name.
        :param metric_weights: Weights for each metric. Default would be 1.0.
        :param file_name: Saved file name.
        :param aggregator_save_path: Save path for this aggregated parquet file.
        :param multiple_metrics: A list if metric names used in multiple factor when computing scenario scores.
        :param challenge_name: Optional, name of the challenge the metrics refer to, if set will be part of the
        output file name and path.
        """
        self._name = name
        self._metric_weights = metric_weights
        self._file_name = file_name
        if not self._file_name.endswith('.parquet'):
            self._file_name += '.parquet'
        self._aggregator_save_path = aggregator_save_path
        self._challenge_name = challenge_name
        if not is_s3_path(self._aggregator_save_path):
            self._aggregator_save_path.mkdir(exist_ok=True, parents=True)
        self._aggregator_type = 'weighted_average'
        self._multiple_metrics = multiple_metrics
        self._parquet_file = self._aggregator_save_path / self._file_name
        self._aggregated_metric_dataframe: Optional[pandas.DataFrame] = None

    @property
    def aggregated_metric_dataframe(self) -> Optional[pandas.DataFrame]:
        """Return the aggregated metric dataframe."""
        return self._aggregated_metric_dataframe

    @property
    def name(self) -> str:
        """
        Return the metric aggregator name.
        :return the metric aggregator name.
        """
        return self._name

    @property
    def final_metric_score(self) -> Optional[float]:
        """Return the final metric score."""
        if self._aggregated_metric_dataframe is not None:
            return self._aggregated_metric_dataframe.iloc[-1, -1]
        else:
            logger.warning('The metric not yet aggregated.')
            return None

    def _get_metric_weight(self, metric_name: str) -> float:
        """
        Get metric weights.
        :param metric_name: The metric name.
        :return Weight for the metric.
        """
        weight: Optional[float] = self._metric_weights.get(metric_name, None)
        metric_weight = self._metric_weights.get('default', 1.0) if weight is None else weight
        return metric_weight

    def _compute_scenario_score(self, scenario_metric_columns: metric_aggregator_dict_column) -> None:
        """
        Compute scenario scores.
        :param scenario_metric_columns: Scenario metric column in the format of {scenario_names: {metric_column:
        value}}.
        """
        excluded_columns = ['log_name', 'planner_name', 'aggregator_type', 'scenario_type', 'num_scenarios', 'score']
        for scenario_name, columns in scenario_metric_columns.items():
            metric_scores = 0.0
            sum_weights = 0.0
            multiple_factor = 1.0
            for column_key, column_value in columns.items():
                if column_key in excluded_columns or column_value is None:
                    continue
                if self._multiple_metrics and column_key in self._multiple_metrics:
                    multiple_factor *= column_value
                else:
                    weight = self._get_metric_weight(metric_name=column_key)
                    assert column_value is not None, f'Metric: {column_key} value should not be None!'
                    assert weight is not None, f'Metric: {column_key} weight should not be None!'
                    sum_weights += weight
                    metric_scores += weight * column_value
            weighted_average_score = metric_scores / sum_weights if sum_weights else 0.0
            final_score = multiple_factor * weighted_average_score
            scenario_metric_columns[scenario_name]['score'] = final_score

    @staticmethod
    def _group_scenario_type_metric(scenario_metric_columns: metric_aggregator_dict_column) -> metric_aggregator_dict_column:
        """
        Group scenario type metric columns in the format of {scenario_type: {metric_columns: value}}.
        :param scenario_metric_columns: Scenario metric columns in the format of {scenario_name: {metric_columns:
        value}}.
        :return Metric columns based on scenario type.
        """
        scenario_type_dicts: metric_aggregator_dict_column = defaultdict(lambda: defaultdict(list))
        total_scenarios = len(scenario_metric_columns)
        for scenario_name, columns in scenario_metric_columns.items():
            scenario_type = columns['scenario_type']
            scenario_type_dicts[scenario_type]['scenario_name'].append(scenario_name)
            for column_key, column_value in columns.items():
                scenario_type_dicts[scenario_type][column_key].append(column_value)
        common_columns = ['planner_name', 'aggregator_type', 'scenario_type']
        excluded_columns = ['scenario_name']
        scenario_type_metric_columns: metric_aggregator_dict_column = defaultdict(lambda: defaultdict())
        for scenario_type, columns in scenario_type_dicts.items():
            for key, values in columns.items():
                if key in excluded_columns:
                    continue
                elif key in common_columns:
                    scenario_type_metric_columns[scenario_type][key] = values[0]
                elif key == 'log_name':
                    scenario_type_metric_columns[scenario_type][key] = None
                elif key == 'num_scenarios':
                    scenario_type_metric_columns[scenario_type]['num_scenarios'] = len(values)
                else:
                    available_values: npt.NDArray[np.float64] = np.asarray([value for value in values if value is not None])
                    value: Optional[float] = float(np.sum(available_values)) if available_values.size > 0 else None
                    if key == 'score' and value is not None:
                        score_value: float = value / len(values) if total_scenarios else 0.0
                        scenario_type_metric_columns[scenario_type][key] = score_value
                    else:
                        scenario_type_metric_columns[scenario_type][key] = value
        return scenario_type_metric_columns

    @staticmethod
    def _group_final_score_metric(scenario_type_metric_columns: metric_aggregator_dict_column) -> metric_aggregator_dict_column:
        """
        Compute a final score based on a group of scenario types.
        :param scenario_type_metric_columns: Scenario type metric columns in the format of {scenario_type:
        {metric_column: value}}.
        :return A dictionary of final score in the format of {'final_score': {metric_column: value}}.
        """
        final_score_dicts: metric_aggregator_dict_column = defaultdict(lambda: defaultdict(list))
        for scenario_type, columns in scenario_type_metric_columns.items():
            for column_key, column_value in columns.items():
                final_score_dicts['final_score'][column_key].append(column_value)
        final_score_metric_columns: metric_aggregator_dict_column = defaultdict(lambda: defaultdict())
        total_scenarios = sum(final_score_dicts['final_score']['num_scenarios'])
        common_columns = ['planner_name', 'aggregator_type']
        for final_score_column_name, columns in final_score_dicts.items():
            for key, values in columns.items():
                if key == 'scenario_type':
                    final_score_metric_columns[final_score_column_name][key] = 'final_score'
                elif key == 'log_name':
                    final_score_metric_columns[final_score_column_name][key] = None
                elif key in common_columns:
                    final_score_metric_columns[final_score_column_name][key] = values[0]
                elif key == 'num_scenarios':
                    final_score_metric_columns[final_score_column_name][key] = total_scenarios
                else:
                    available_values: List[float] = []
                    if key == 'score':
                        for value, num_scenario in zip(values, columns['num_scenarios']):
                            if value is not None:
                                available_values.append(value * num_scenario)
                    else:
                        available_values = [value for value in values if value is not None]
                    if not available_values:
                        total_values = None
                    else:
                        available_value_array: npt.NDArray[np.float64] = np.asarray(available_values)
                        total_values = np.sum(available_value_array) / total_scenarios
                    final_score_metric_columns[final_score_column_name][key] = total_values
        return final_score_metric_columns

    def _group_scenario_metrics(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame], planner_name: str) -> metric_aggregator_dict_column:
        """
        Group scenario metrics in the format of {scenario_name: {metric_column: value}}.
        :param metric_dataframes: A dict of metric dataframes.
        :param planner_name: A planner name.
        :return Dictionary column format in metric aggregator in {scenario_name: {metric_column: value}}.
        """
        metric_names = sorted(list(metric_dataframes.keys()))
        columns = {column: None for column in ['log_name', 'planner_name', 'aggregator_type', 'scenario_type', 'num_scenarios'] + metric_names + ['score']}
        scenario_metric_columns: metric_aggregator_dict_column = {}
        for metric_name, metric_dataframe in metric_dataframes.items():
            dataframe = metric_dataframe.query_scenarios(planner_names=tuple([planner_name]))
            for _, data in dataframe.iterrows():
                scenario_name = data.get('scenario_name')
                if scenario_name not in scenario_metric_columns:
                    scenario_metric_columns[scenario_name] = deepcopy(columns)
                scenario_type = data['scenario_type']
                scenario_metric_columns[scenario_name]['log_name'] = data['log_name']
                scenario_metric_columns[scenario_name]['planner_name'] = data['planner_name']
                scenario_metric_columns[scenario_name]['scenario_type'] = scenario_type
                scenario_metric_columns[scenario_name]['aggregator_type'] = self._aggregator_type
                scenario_metric_columns[scenario_name][metric_name] = data['metric_score']
        return scenario_metric_columns

    def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
        """
        Run an aggregator to generate an aggregated parquet file.
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
        planner_names = sorted(list({planner_name for metric_statistic_dataframe in metric_dataframes.values() for planner_name in metric_statistic_dataframe.planner_names}))
        weighted_average_dataframe_columns: Dict[str, List[Any]] = dict()
        for planner_name in planner_names:
            metric_names = sorted(list(metric_dataframes.keys())) + ['score']
            dataframe_columns: Dict[str, List[Any]] = {'scenario': [], 'log_name': [], 'scenario_type': [], 'num_scenarios': [], 'planner_name': [], 'aggregator_type': []}
            metric_name_columns: Dict[str, List[float]] = {metric_name: [] for metric_name in metric_names}
            dataframe_columns.update(metric_name_columns)
            scenario_metric_columns = self._group_scenario_metrics(metric_dataframes=metric_dataframes, planner_name=planner_name)
            self._compute_scenario_score(scenario_metric_columns=scenario_metric_columns)
            scenario_type_metric_columns = self._group_scenario_type_metric(scenario_metric_columns=scenario_metric_columns)
            scenario_type_final_metric_columns = self._group_final_score_metric(scenario_type_metric_columns=scenario_type_metric_columns)
            scenario_metric_columns.update(scenario_type_metric_columns)
            scenario_metric_columns.update(scenario_type_final_metric_columns)
            for scenario_name, columns in scenario_metric_columns.items():
                dataframe_columns['scenario'].append(scenario_name)
                for key, value in columns.items():
                    dataframe_columns[key].append(value)
            if not weighted_average_dataframe_columns:
                weighted_average_dataframe_columns.update(dataframe_columns)
            else:
                for column_name, value in weighted_average_dataframe_columns.items():
                    value += dataframe_columns[column_name]
        self._aggregated_metric_dataframe = pandas.DataFrame(data=weighted_average_dataframe_columns)
        self._save_parquet(dataframe=self._aggregated_metric_dataframe, save_path=self._parquet_file)

    def read_parquet(self) -> None:
        """Read a parquet file."""
        self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

    @property
    def parquet_file(self) -> Path:
        """Inherited, see superclass"""
        return self._parquet_file

    @property
    def challenge(self) -> Optional[str]:
        """Inherited, see superclass"""
        return self._challenge_name

@property
def final_metric_score(self) -> Optional[float]:
    """Return the final metric score."""
    if self._aggregated_metric_dataframe is not None:
        return self._aggregated_metric_dataframe.iloc[-1, -1]
    else:
        logger.warning('The metric not yet aggregated.')
        return None

class MockAbstractMetricAggregator(AbstractMetricAggregator):
    """Mock Metric aggregator."""

    def __init__(self, aggregator_save_path: Path, name: str='dummy_metric_aggregator', metric_weights: Optional[Dict[str, float]]=None, file_name: str='dummy_metric_aggregator.parquet'):
        """
        Initializer for MockAbstractMetricAggregator class
        :param name: Metric aggregator name
        :param metric_weights: Weights for each metric. Default would be 1.0
        :param file_name: Saved file name
        :param aggregator_save_path: Save path for this aggregated parquet file.
        """
        self._name = name
        self._metric_weights = metric_weights or {'default': 1.0}
        self._file_name = file_name
        self._aggregator_save_path = aggregator_save_path
        if not self._aggregator_save_path.exists():
            self._aggregator_save_path.mkdir(exist_ok=True, parents=True)
        self._parquet_file = self._aggregator_save_path / self._file_name
        self._aggregated_metric_dataframe: Optional[pandas.DataFrame] = None

    @property
    def aggregated_metric_dataframe(self) -> Optional[pandas.DataFrame]:
        """Return the aggregated metric dataframe."""
        return self._aggregated_metric_dataframe

    @property
    def name(self) -> str:
        """
        Return the metric aggregator name
        :return: the metric aggregator name.
        """
        return self._name

    @property
    def final_metric_score(self) -> Optional[float]:
        """Return the final metric score."""
        if self._aggregated_metric_dataframe is not None:
            return self._aggregated_metric_dataframe.iloc[-1, -1]
        else:
            logger.warning('The metric not yet aggregated.')
            return None

    def _get_metric_weight(self, metric_name: str) -> float:
        """
        Get metric weights
        :param metric_name: The metric name
        :return: Weight for the metric.
        """
        metric_weight = self._metric_weights.get(metric_name, None)
        if not metric_weight:
            metric_weight = self._metric_weights.get('default', 1.0)
        return metric_weight

    def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
        """
        Run an aggregator to generate an aggregated parquet file
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
        dataframe_columns = {'test_column_1': [1, 2, 3], 'test_column_2': [4, 5, 6]}
        self._aggregated_metric_dataframe = pandas.DataFrame(data=dataframe_columns)
        self._save_parquet(dataframe=self._aggregated_metric_dataframe, save_path=self._parquet_file)

    def read_parquet(self) -> None:
        """Read a parquet file."""
        self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

    @property
    def parquet_file(self) -> Path:
        """Inherited, see superclass."""
        return self._parquet_file

    @property
    def challenge(self) -> Optional[str]:
        """Inherited, see superclass."""
        return None

@property
def final_metric_score(self) -> Optional[float]:
    """Return the final metric score."""
    if self._aggregated_metric_dataframe is not None:
        return self._aggregated_metric_dataframe.iloc[-1, -1]
    else:
        logger.warning('The metric not yet aggregated.')
        return None

class MetricBase(AbstractMetricBuilder):
    """Base class for evaluation of metrics."""

    def __init__(self, name: str, category: str, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializer for MetricBase
        :param name: Metric name
        :param category: Metric category.
        :param metric_score_unit: Metric final score unit.
        """
        self._name = name
        self._category = category
        self._metric_score_unit = metric_score_unit

    @property
    def name(self) -> str:
        """
        Returns the metric name
        :return the metric name.
        """
        return self._name

    @property
    def category(self) -> str:
        """
        Returns the metric category
        :return the metric category.
        """
        return self._category

    @property
    def metric_score_unit(self) -> Optional[str]:
        """
        Returns the metric final score unit.
        """
        return self._metric_score_unit

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> Optional[float]:
        """Inherited, see superclass."""
        return None

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        raise NotImplementedError

    def _compute_time_series_statistic(self, time_series: TimeSeries, statistics_type_list: Optional[List[MetricStatisticsType]]=None) -> List[Statistic]:
        """
        Compute metric statistics in time series.
        :param time_series: time series (with float values).
        :param statistics_type_list: List of available types such as [MetricStatisticsType.MAX,
        MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]. Use all if set to None.
        :return A list of metric statistics.
        """
        values = time_series.values
        assert values, 'Time series values cannot be empty!'
        unit = time_series.unit
        if statistics_type_list is None:
            statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
        statistics = []
        for statistics_type in statistics_type_list:
            if statistics_type == MetricStatisticsType.MAX:
                name = f'max_{self.name}'
                value = np.nanmax(values)
            elif statistics_type == MetricStatisticsType.MEAN:
                name = f'avg_{self.name}'
                value = np.nanmean(values)
            elif statistics_type == MetricStatisticsType.MIN:
                name = f'min_{self.name}'
                value = np.nanmin(values)
            elif statistics_type == MetricStatisticsType.P90:
                name = f'p90_{self.name}'
                value = np.nanpercentile(values, 90, method='closest_observation')
            else:
                raise TypeError('Other metric types statistics cannot be created by compute_statistics()')
            statistics.append(Statistic(name=name, unit=unit, value=value, type=statistics_type))
        return statistics

    def _construct_metric_results(self, metric_statistics: List[Statistic], scenario: AbstractScenario, metric_score_unit: Optional[str]=None, time_series: Optional[TimeSeries]=None) -> List[MetricStatistics]:
        """
        Construct metric results with statistics, scenario, and time series
        :param metric_statistics: A list of metric statistics
        :param scenario: Scenario running this metric to compute a metric score
        :param metric_score_unit: Unit for the metric final score.
        :param time_series: Time series object.
        :return: A list of metric statistics.
        """
        score = self.compute_score(scenario=scenario, metric_statistics=metric_statistics, time_series=time_series)
        result = MetricStatistics(metric_computator=self.name, name=self.name, statistics=metric_statistics, time_series=time_series, metric_category=self.category, metric_score=score, metric_score_unit=metric_score_unit)
        return [result]

    def _construct_open_loop_metric_results(self, scenario: AbstractScenario, comparison_horizon: List[int], maximum_threshold: float, metric_values: npt.NDArray[np.float64], name: str, unit: str, timestamps_sampled: List[int], metric_score_unit: str, selected_frames: List[int]) -> List[MetricStatistics]:
        """
        Construct metric results with statistics, scenario, and time series for open_loop metrics.
        :param scenario: Scenario running this metric to compute a metric score.
        :param comparison_horizon: List of horizon times in future (s) to find displacement errors.
        :param maximum_threshold: Maximum acceptable error threshold.
        :param metric_values: Time series object.
        :param name: name of timeseries.
        :param unit: metric unit.
        :param timestamps_sampled:A list of sampled timestamps.
        :param metric_score_unit: Unit for the metric final score.
        :param selected_frames: List sampled indices for nuboard Timeseries frames
        :return: A list of metric statistics.
        """
        metric_statistics: List[Statistic] = [Statistic(name=f'{name}_horizon_{horizon}', unit=unit, value=np.mean(metric_values[ind]), type=MetricStatisticsType.MEAN) for ind, horizon in enumerate(comparison_horizon)]
        metric_statistics.extend([Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=np.mean(metric_values) <= maximum_threshold, type=MetricStatisticsType.BOOLEAN), Statistic(name=f'avg_{name}_over_all_horizons', unit=unit, value=np.mean(metric_values), type=MetricStatisticsType.MEAN)])
        metric_values_over_horizons_at_each_time = np.mean(metric_values, axis=0)
        time_series = TimeSeries(unit=f'avg_{name}_over_all_horizons [{unit}]', time_stamps=timestamps_sampled, values=list(metric_values_over_horizons_at_each_time), selected_frames=selected_frames)
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, metric_score_unit=metric_score_unit, time_series=time_series)
        return results

def _compute_time_series_statistic(self, time_series: TimeSeries, statistics_type_list: Optional[List[MetricStatisticsType]]=None) -> List[Statistic]:
    """
        Compute metric statistics in time series.
        :param time_series: time series (with float values).
        :param statistics_type_list: List of available types such as [MetricStatisticsType.MAX,
        MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]. Use all if set to None.
        :return A list of metric statistics.
        """
    values = time_series.values
    assert values, 'Time series values cannot be empty!'
    unit = time_series.unit
    if statistics_type_list is None:
        statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
    statistics = []
    for statistics_type in statistics_type_list:
        if statistics_type == MetricStatisticsType.MAX:
            name = f'max_{self.name}'
            value = np.nanmax(values)
        elif statistics_type == MetricStatisticsType.MEAN:
            name = f'avg_{self.name}'
            value = np.nanmean(values)
        elif statistics_type == MetricStatisticsType.MIN:
            name = f'min_{self.name}'
            value = np.nanmin(values)
        elif statistics_type == MetricStatisticsType.P90:
            name = f'p90_{self.name}'
            value = np.nanpercentile(values, 90, method='closest_observation')
        else:
            raise TypeError('Other metric types statistics cannot be created by compute_statistics()')
        statistics.append(Statistic(name=name, unit=unit, value=value, type=statistics_type))
    return statistics

class SpeedLimitComplianceStatistics(ViolationMetricBase):
    """Statistics on speed limit compliance of ego."""

    def __init__(self, name: str, category: str, lane_change_metric: EgoLaneChangeStatistics, max_violation_threshold: int, max_overspeed_value_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializes the SpeedLimitComplianceStatistics class
        :param name: Metric name
        :param category: Metric category
        :param lane_change_metric: lane change metric
        :param max_violation_threshold: Maximum threshold for the number of violation
        :param max_overspeed_value_threshold: A threshold for overspeed value driving above which is considered more
        dangerous.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, max_violation_threshold=max_violation_threshold, metric_score_unit=metric_score_unit)
        self._max_overspeed_value_threshold = max_overspeed_value_threshold
        self._lane_change_metric = lane_change_metric

    def _compute_violation_metric_score(self, time_series: TimeSeries) -> float:
        """
        Compute a metric score based on the durtaion and magnitude of the violation compared to the scenario
        duration and a threshold for overspeed value.
        :param time_series: A time series for the overspeed
        :return: A metric score between 0 and 1.
        """
        dt_in_sec = np.mean(np.diff(time_series.time_stamps)) * 1e-06
        scenario_duration_in_sec = (time_series.time_stamps[-1] - time_series.time_stamps[0]) * 1e-06
        if scenario_duration_in_sec <= 0:
            logger.warning('Scenario duration is 0 or less!')
            return 1.0
        max_overspeed_value_threshold = max(self._max_overspeed_value_threshold, 0.001)
        violation_loss = np.sum(time_series.values) * dt_in_sec / (max_overspeed_value_threshold * scenario_duration_in_sec)
        return float(max(0.0, 1.0 - violation_loss))

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        if metric_statistics[-1].value:
            return 1.0
        return float(self._compute_violation_metric_score(time_series=time_series))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated metric.
        """
        ego_route = self._lane_change_metric.ego_driven_route
        extractor = SpeedLimitViolationExtractor(history=history, metric_name=self._name, category=self._category)
        extractor.extract_metric(ego_route=ego_route)
        time_stamps = extract_ego_time_point(history.extract_ego_state)
        time_series = TimeSeries(unit='over_speeding[meters_per_second]', time_stamps=list(time_stamps), values=extractor.violation_depths)
        violation_statistics: List[MetricStatistics] = self.aggregate_metric_violations(metric_violations=extractor.violations, scenario=scenario, time_series=time_series)
        return violation_statistics

def _compute_violation_metric_score(self, time_series: TimeSeries) -> float:
    """
        Compute a metric score based on the durtaion and magnitude of the violation compared to the scenario
        duration and a threshold for overspeed value.
        :param time_series: A time series for the overspeed
        :return: A metric score between 0 and 1.
        """
    dt_in_sec = np.mean(np.diff(time_series.time_stamps)) * 1e-06
    scenario_duration_in_sec = (time_series.time_stamps[-1] - time_series.time_stamps[0]) * 1e-06
    if scenario_duration_in_sec <= 0:
        logger.warning('Scenario duration is 0 or less!')
        return 1.0
    max_overspeed_value_threshold = max(self._max_overspeed_value_threshold, 0.001)
    violation_loss = np.sum(time_series.values) * dt_in_sec / (max_overspeed_value_threshold * scenario_duration_in_sec)
    return float(max(0.0, 1.0 - violation_loss))

def proto_ego_state_from_ego_state(ego_state: EgoState) -> chpb.EgoState:
    """
    Serializes EgoState to a EgoState message
    :param ego_state: The EgoState object
    :return: The corresponding EgoState message
    """
    return chpb.EgoState(rear_axle_pose=proto_se2_from_se2(ego_state.rear_axle), rear_axle_velocity_2d=proto_vector_2d_from_vector_2d(ego_state.dynamic_car_state.rear_axle_velocity_2d), rear_axle_acceleration_2d=proto_vector_2d_from_vector_2d(ego_state.dynamic_car_state.rear_axle_acceleration_2d), tire_steering_angle=ego_state.tire_steering_angle, time_us=ego_state.time_us, angular_vel=ego_state.dynamic_car_state.angular_velocity, angular_accel=ego_state.dynamic_car_state.angular_acceleration)

class EvalaiInterface:
    """Interface to use EvalAI APIs."""

    def __init__(self, api_server: str='https://eval.ai') -> None:
        """
        :param api_server: The URL of the api server.
        """
        self.CHALLENGE_PK = os.getenv('EVALAI_CHALLENGE_PK')
        self.EVALAI_AUTH_TOKEN = os.getenv('EVALAI_PERSONAL_AUTH_TOKEN')
        assert self.CHALLENGE_PK, 'Missing required environmental variable EVALAI_CHALLENGE_PK!'
        assert self.EVALAI_AUTH_TOKEN, 'Missing required environmental variable EVALAI_PERSONAL_AUTH_TOKEN!'
        self.EVALAI_API_SERVER = api_server

    def update_submission_data(self, data: Dict[str, str]) -> Any:
        """
        Updates the status of a submission according to the input data.
        :param data: The information to update the submission. The submission is specified in data.
        :return: Server response.
        """
        url = self._format_url('update_submission')
        response = self._request(url, 'PUT', data)
        return response

    def _request(self, url: str, method: str, data: Optional[Dict[str, str]]=None) -> str:
        """
        Creates request according to parameters.
        :param url: Target url
        :param method: Method (i.e. 'PUT')
        :param data: Optional payload
        :return: Response from server.
        :raises RequestException: If connection fails.
        """
        try:
            response = requests.request(method=method, url=url, headers=self._get_request_headers(), data=data)
            response.raise_for_status()
            logger.info(response.json())
        except requests.exceptions.RequestException as e:
            logger.error('Could not establish connection with EvalAI server at %s' % self.EVALAI_API_SERVER)
            logger.error(e)
            raise e
        return response.json()

    def _format_url(self, api: str) -> str:
        """
        Creates correct URL using api and server.
        :param api: The requested API.
        :return: The formatted URL.
        """
        assert api in URLS, f'Requested API unavailable, available ones are {URLS}'
        return f'{self.EVALAI_API_SERVER}{URLS.get(api).format(self.CHALLENGE_PK)}'

    def _get_request_headers(self) -> Dict[str, str]:
        """
        Creates correct headers for authentication in requests.
        :return: The header with the authentication token.
        """
        return {'Authorization': f'Bearer {self.EVALAI_AUTH_TOKEN}'}

def _request(self, url: str, method: str, data: Optional[Dict[str, str]]=None) -> str:
    """
        Creates request according to parameters.
        :param url: Target url
        :param method: Method (i.e. 'PUT')
        :param data: Optional payload
        :return: Response from server.
        :raises RequestException: If connection fails.
        """
    try:
        response = requests.request(method=method, url=url, headers=self._get_request_headers(), data=data)
        response.raise_for_status()
        logger.info(response.json())
    except requests.exceptions.RequestException as e:
        logger.error('Could not establish connection with EvalAI server at %s' % self.EVALAI_API_SERVER)
        logger.error(e)
        raise e
    return response.json()

class TestUtils(unittest.TestCase):
    """Tests for utils function."""

    def test_submission_logger(self) -> None:
        """Tests the two handlers of the submission logger."""
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        logfile = '/'.join([tmp_dir.name, 'bar.log'])
        logger = get_submission_logger('foo', logfile)
        logger.info('DONT MIND ME')
        logger.warning('HELLO')
        logger.error('WORLD!')
        with open(logfile, 'r') as f:
            self.assertEqual(len(f.readlines()), 2)

def test_submission_logger(self) -> None:
    """Tests the two handlers of the submission logger."""
    tmp_dir = tempfile.TemporaryDirectory()
    self.addCleanup(tmp_dir.cleanup)
    logfile = '/'.join([tmp_dir.name, 'bar.log'])
    logger = get_submission_logger('foo', logfile)
    logger.info('DONT MIND ME')
    logger.warning('HELLO')
    logger.error('WORLD!')
    with open(logfile, 'r') as f:
        self.assertEqual(len(f.readlines()), 2)

