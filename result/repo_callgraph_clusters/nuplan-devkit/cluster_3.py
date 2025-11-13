# Cluster 3

def _create_dummy_simulation_history_buffer(scenario: AbstractScenario, iteration: int=0, time_horizon: int=2, num_samples: int=2, buffer_size: int=2) -> SimulationHistoryBuffer:
    """
    Create dummy SimulationHistoryBuffer.
    :param scenario: Scenario.
    :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
    :param time_horizon: the desired horizon to the future.
    :param num_samples: number of entries in the future.
    :param buffer_size: size of buffer.
    :return: SimulationHistoryBuffer.
    """
    past_observation = list(scenario.get_past_tracked_objects(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples))
    past_ego_states = list(scenario.get_ego_past_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples))
    history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=buffer_size, ego_states=past_ego_states, observations=past_observation, sample_interval=scenario.database_interval)
    return history_buffer

def serialize_scenario(scenario: AbstractScenario, num_poses: int=12, future_time_horizon: float=6.0) -> SimulationHistory:
    """
    Serialize a scenario to a list of scene dicts.
    :param scenario: Scenario.
    :param num_poses: Number of poses in trajectory.
    :param future_time_horizon: Future time horizon in trajectory.
    :return: SimulationHistory containing all scenes.
    """
    simulation_history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
    ego_controller = PerfectTrackingController(scenario)
    simulation_time_controller = StepSimulationTimeController(scenario)
    observations = TracksObservation(scenario)
    history_buffer = _create_dummy_simulation_history_buffer(scenario=scenario)
    for _ in range(simulation_time_controller.number_of_iterations()):
        iteration = simulation_time_controller.get_iteration()
        ego_state = ego_controller.get_state()
        observation = observations.get_observation()
        traffic_light_status = list(scenario.get_traffic_light_status_at_iteration(iteration.index))
        current_state = scenario.get_ego_state_at_iteration(iteration.index)
        states = scenario.get_ego_future_trajectory(iteration.index, future_time_horizon, num_poses)
        trajectory = InterpolatedTrajectory(list(itertools.chain([current_state], states)))
        simulation_history.add_sample(SimulationHistorySample(iteration, ego_state, trajectory, observation, traffic_light_status))
        next_iteration = simulation_time_controller.next_iteration()
        if next_iteration:
            ego_controller.update_state(iteration, next_iteration, ego_state, trajectory)
            observations.update_observation(iteration, next_iteration, history_buffer)
    return simulation_history

def get_last_box_index(box_sequence: List[Box3D]) -> int:
    """
    Given a list of boxes, find the highest index such that the value of the box at that index is not None.
    :param box_sequence: Sequence of boxes, for example, representing box positions over time.
    :return: List index representing the highest index such that the value of the box at that index is not None.
    """
    for i in reversed(range(len(box_sequence))):
        if box_sequence[i] is not None:
            return i
    raise ValueError(f'All boxes in sequence are None: {box_sequence}')

class TestTrack(unittest.TestCase):
    """Test class Track"""

    def setUp(self) -> None:
        """
        Initializes a test Track
        """
        self.track = get_test_nuplan_track()

    @patch('nuplan.database.nuplan_db_orm.track.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.track._session()
        inspect.assert_called_once_with(self.track)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.track.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.track.__repr__()
        simple_repr.assert_called_once_with(self.track)
        self.assertEqual(result, simple_repr.return_value)

    def test_nbr_lidar_boxes(self) -> None:
        """
        Tests property - number of boxes along the track.
        """
        result = self.track.nbr_lidar_boxes
        self.assertGreater(result, 0)
        self.assertIsInstance(result, int)

    def test_first_last_lidar_box(self) -> None:
        """
        Tests properties - first and last lidar box along the track.
        """
        first_lidar_box = self.track.first_lidar_box
        last_lidar_box = self.track.last_lidar_box
        self.assertGreaterEqual(last_lidar_box.timestamp, first_lidar_box.timestamp)

    @patch('nuplan.database.nuplan_db_orm.track.Track.first_lidar_box', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.track.Track.last_lidar_box', autospec=True)
    def test_duration(self, mock_last_box: Mock, mock_first_box: Mock) -> None:
        """
        Tests property - duration of Track.
        """
        mock_first_box.timestamp = 1000
        mock_last_box.timestamp = 5000
        result = self.track.duration
        self.assertEqual(result, 4000)

    def test_distances_to_ego(self) -> None:
        """
        Tests property - distances of all boxes in the track from ego vehicle.
        """
        result = self.track.distances_to_ego
        self.assertEqual(len(result), self.track.nbr_lidar_boxes)

    def test_min_max_distance_to_ego(self) -> None:
        """
        Tests two properties - min and max distance to ego
        """
        min_result = self.track.min_distance_to_ego
        max_result = self.track.max_distance_to_ego
        self.assertGreaterEqual(max_result, min_result)

def test_first_last_lidar_box(self) -> None:
    """
        Tests properties - first and last lidar box along the track.
        """
    first_lidar_box = self.track.first_lidar_box
    last_lidar_box = self.track.last_lidar_box
    self.assertGreaterEqual(last_lidar_box.timestamp, first_lidar_box.timestamp)

def test_min_max_distance_to_ego(self) -> None:
    """
        Tests two properties - min and max distance to ego
        """
    min_result = self.track.min_distance_to_ego
    max_result = self.track.max_distance_to_ego
    self.assertGreaterEqual(max_result, min_result)

class TestBox3D(unittest.TestCase):
    """Test Box3D."""

    def test_points_in_box(self) -> None:
        """Test the point_in_box method."""
        vel = (np.nan, np.nan, np.nan)

        def qyaw(yaw: float) -> Quaternion:
            """
            Return a Quaternion given yaw angle.
            :param yaw: Yaw angle.
            :return: A Quaternion object.
            """
            return Quaternion(axis=(0, 0, 1), angle=yaw)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask.all(), True)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.1, 0.0, 0.0], [0.5, -1.1, 0.0]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask.all(), False)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[-1.0, -1.0, 0.0], [1.0, 1.0, 0.0]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask.all(), True)
        rot = 45
        trans = [1.0, 1.0]
        box = Box3D((0.0 + trans[0], 0.0 + trans[1], 0.0), (2.0, 2.0, 1.0), qyaw(rot / 180.0 * np.pi), 1, 2.0, vel)
        points = np.array([[0.7 + trans[0], 0.7 + trans[1], 0.0], [0.71 + 1.0, 0.71 + 1.0, 0.0]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask[0], True)
        self.assertEqual(mask[1], False)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask.all(), True)
        for wlh_factor in [0.5, 1.0, 1.5, 10.0]:
            box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
            points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0]]).transpose()
            mask = points_in_box(box, points, wlh_factor=wlh_factor)
            self.assertEqual(mask.all(), True)
        for wlh_factor in [0.1, 0.49]:
            box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
            points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0]]).transpose()
            mask = points_in_box(box, points, wlh_factor=wlh_factor)
            self.assertEqual(mask[0], True)
            self.assertEqual(mask[1], False)

    def test_points_in_box_bev(self) -> None:
        """Test the points_in_box_bev method."""
        vel = (np.nan, np.nan, np.nan)

        def qyaw(yaw: float) -> Quaternion:
            """
            Return a Quaternion given yaw angle.
            :param yaw: Yaw angle.
            :return: A Quaternion object.
            """
            return Quaternion(axis=(0, 0, 1), angle=yaw)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0]]).transpose()
        mask = points_in_box_bev(box, points)
        self.assertEqual(mask.all(), True)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.1, 0.0, 0.0], [0.5, -1.1, 0.0]]).transpose()
        mask = points_in_box_bev(box, points)
        self.assertEqual(mask.all(), False)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[-1.0, -1.0, 0.0], [1.0, 1.0, 0.0]]).transpose()
        mask = points_in_box_bev(box, points)
        self.assertEqual(mask.all(), True)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), qyaw(0.0), 1, 2.0, vel)
        points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]]).transpose()
        mask = points_in_box(box, points, wlh_factor=1.0)
        self.assertEqual(mask.all(), True)
        for center_z in [0.5, 1.0, 1.5, 10.0, 100]:
            box = Box3D((0.0, 0.0, center_z), (2.0, 2.0, 1.0), qyaw(0.0), 1, 2.0, vel)
            points = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.0]]).transpose()
            mask = points_in_box_bev(box, points)
            self.assertEqual(mask.all(), True)

    def test_rotate(self) -> None:
        """Test if rotate correctly rotates the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        theta = np.pi / 2
        box.rotate(Quaternion(axis=(0.0, 0.0, 1.0), angle=theta))
        assert_array_almost_equal(box.bottom_corners[:, 0], np.array([1.0, 1.0, -1.0]))
        assert_array_almost_equal(box.bottom_corners[:, 1], np.array([-1.0, 1.0, -1.0]))
        assert_array_almost_equal(box.bottom_corners[:, 2], np.array([-1.0, -1.0, -1.0]))
        assert_array_almost_equal(box.bottom_corners[:, 3], np.array([1.0, -1.0, -1.0]))

    def test_box_in_image(self) -> None:
        """Test Box at different location in Image."""
        box = Box3D((150.0, 150.0, 150.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        intrinsic = np.eye(3)
        imsize = (300, 300)
        box_in_img = box_in_image(box, intrinsic, imsize)
        self.assertEqual(box_in_img, True)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ALL)
        self.assertEqual(box_in_img, False)
        box = Box3D((0.0, 0.0, 0.0), (0.01, 0.01, 0.05), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ANY)
        self.assertEqual(box_in_img, False)
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.NONE)
        self.assertEqual(box_in_img, True)
        box = Box3D((-10.0, -90.0, -100.0), (2.0, 2.0, 2.0), Quaternion(axis=(10.0, 20.0, 1.4), angle=20))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.NONE)
        self.assertEqual(box_in_img, True)
        box = Box3D((0.0, 0.0, 3.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ANY)
        self.assertEqual(box_in_img, True)
        box = Box3D((-2.0, -2.0, -2.0), (1.0, 1.0, 1.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ANY)
        self.assertEqual(box_in_img, False)
        box = Box3D((10.0, 10.0, 0.51), (1.0, 1.0, 1.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ANY)
        self.assertEqual(box_in_img, True)
        box = Box3D((150.0, 150.0, 150.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0), velocity=(10.0, 20.0, 3.0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ALL, with_velocity=True)
        self.assertEqual(box_in_img, True)
        box = Box3D((150.0, 150.0, 2.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0), velocity=(2000.0, 20.0, 3.0))
        box_in_img = box_in_image(box, intrinsic, imsize, vis_level=BoxVisibility.ALL, with_velocity=True)
        self.assertEqual(box_in_img, False)

    def test_copy(self) -> None:
        """Verify that box copy works as expected."""
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        self.assertEqual(box_orig, box_copy)
        box_orig.center[0] += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.wlh[0] += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.orientation.q[0] += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.label += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.score += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.velocity[0] += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.angular_velocity += 1
        self.assertNotEqual(box_orig, box_copy)
        box_orig = Box3D.make_random()
        box_copy = box_orig.copy()
        box_orig.payload = {'abc': 'def'}
        self.assertNotEqual(box_orig, box_copy)

    def test_translate(self) -> None:
        """Tests box translation performs as expected."""
        box = Box3D((150.0, 120.0, 10.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.2, 0.4, 1.43), angle=30))
        box.translate(np.array([12.3, 0.0, 1.4], dtype=float))
        self.assertTrue(np.array_equal(box.center, [162.3, 120.0, 11.4]))
        box = Box3D((10.0, 1220.0, 1.0), (2.0, 2.0, 2.0), Quaternion(axis=(2.2, 0.24, 0), angle=20))
        box.translate(np.array([-990.0, 10.0, -0.4], dtype=float))
        self.assertTrue(np.array_equal(box.center, [-980.0, 1230.0, 0.6]))
        box = Box3D((10.0, 1220.0, 1.0), (2.0, 2.0, 2.0), Quaternion(axis=(2.2, 0.24, 0), angle=20))
        box.translate(np.array([0.0, 0.0, 0.0], dtype=float))
        self.assertTrue(np.array_equal(box.center, [10.0, 1220.0, 1.0]))

    def test_transform(self) -> None:
        """Tests the equivalence of using box.transform compared to box.translation followed by box.rotation."""
        box1 = Box3D.arbitrary_box()
        box2 = Box3D.arbitrary_box()
        self.assertEqual(box1, box2)
        r1 = Quaternion(np.random.rand(4))
        t1 = np.random.rand(3)
        r2 = Quaternion(np.random.rand(4))
        t2 = np.random.rand(3)
        tf1 = r1.transformation_matrix
        tf1[:3, 3] = t1
        tf2 = r2.transformation_matrix
        tf2[:3, 3] = t2
        tf = np.dot(tf2, tf1)
        box1.rotate(r1)
        box1.translate(t1)
        box1.rotate(r2)
        box1.translate(t2)
        box2.transform(tf)
        self.assertEqual(box1, box2)

    def test_xflip_no_flip(self) -> None:
        """Tests that there is no change."""
        for input_yaw in (np.pi / 2, -np.pi / 2):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=input_yaw))
            box.xflip()
            assert_almost_equal(quaternion_yaw(box.orientation), input_yaw)

    def test_xflip_180_flip(self) -> None:
        """Test flip from left to right and right to left."""
        input_yaw = (0, np.pi)
        output_yaw = (np.pi, 0)
        for in_yaw, out_yaw in zip(input_yaw, output_yaw):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=in_yaw))
            box.xflip()
            assert_almost_equal(quaternion_yaw(box.orientation), out_yaw)

    def test_xflip_pos_yaw(self) -> None:
        """Test flips when starting with positive yaw."""
        for yaw in np.linspace(0, np.pi, 100):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=yaw))
            box.xflip()
            assert_almost_equal(quaternion_yaw(box.orientation), np.pi - yaw)

    def test_xflip_neg_yaw(self) -> None:
        """Test flips when starting with negative yaw."""
        for yaw in np.linspace(-np.pi, -0.0001, 100):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=yaw))
            box.xflip()
            assert_almost_equal(quaternion_yaw(box.orientation), -np.pi - yaw)

    def test_yflip_no_flip(self) -> None:
        """Test that there is no change."""
        for input_yaw in (0, np.pi):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=input_yaw))
            box.yflip()
            assert_almost_equal(quaternion_yaw(box.orientation), -input_yaw)

    def test_yflip_180_flip(self) -> None:
        """Test flip from left to right and right to left."""
        input_yaw = (-np.pi / 2, np.pi / 2)
        output_yaw = (np.pi / 2, -np.pi / 2)
        for in_yaw, out_yaw in zip(input_yaw, output_yaw):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=in_yaw))
            box.yflip()
            assert_almost_equal(quaternion_yaw(box.orientation), out_yaw)

    def test_yflip_pos_yaw(self) -> None:
        """Test flips when starting with positive yaw."""
        for yaw in np.linspace(0, np.pi, 100):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=yaw))
            box.yflip()
            assert_almost_equal(quaternion_yaw(box.orientation), -yaw)

    def test_yflip_neg_yaw(self) -> None:
        """Test flips when starting with negative yaw."""
        for yaw in np.linspace(-np.pi, -0.0001, 100):
            box = Box3D((0, 0, 0), (1, 1, 1), Quaternion(axis=(0, 0, 1), angle=yaw))
            box.yflip()
            assert_almost_equal(quaternion_yaw(box.orientation), -yaw)

    def test_arbitrary_box(self) -> None:
        """Tests arbitrary_box method could initiate a box correctly."""
        box = Box3D.arbitrary_box()
        self.assertTrue(box)
        self.assertEqual(box, Box3D.deserialize(box.serialize()))

    def test_center_bottom_forward(self) -> None:
        """Tests the point of the center of the intersection of the bottom and forward faces of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        self.assertEqual(box.center_bottom_forward[0], 1)
        self.assertEqual(box.center_bottom_forward[1], 0)
        self.assertEqual(box.center_bottom_forward[2], -1)

    def test_front_center(self) -> None:
        """Tests the center of the front face of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        self.assertEqual(box.front_center[0], 1)
        self.assertEqual(box.front_center[1], 0)
        self.assertEqual(box.front_center[2], 0)

    def test_rear_center(self) -> None:
        """Tests the center of the rear face of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        self.assertEqual(box.rear_center[0], -1)
        self.assertEqual(box.rear_center[1], 0)
        self.assertEqual(box.rear_center[2], 0)

    def test_bottom_center(self) -> None:
        """Tests the bottom face center of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        self.assertEqual(box.bottom_center[0], 0)
        self.assertEqual(box.bottom_center[1], 0)
        self.assertEqual(box.bottom_center[2], -1)

    def test_velocity_endpoint(self) -> None:
        """Tests the velocity vector is correct."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0), velocity=(1.0, 1.0, 1.0))
        self.assertEqual(box.velocity_endpoint[0], 2)
        self.assertEqual(box.velocity_endpoint[1], 1)
        self.assertEqual(box.velocity_endpoint[2], 0)

    def test_corners(self) -> None:
        """Tests if corners change after translation."""
        box = Box3D.make_random()
        corners = box.corners()
        translation: npt.NDArray[np.float64] = np.array([4, 4, 4])
        box.translate(translation)
        corners_translated: npt.NDArray[np.float64] = corners + translation.reshape(-1, 1)
        self.assertTrue(np.allclose(box.corners(), corners_translated))
        box = Box3D.make_random()
        corners = box.corners()
        translation = np.array([np.random.randint(-box.center[0] - CONST_NUM, 0), np.random.randint(-box.center[1] - CONST_NUM, 0), np.random.randint(-box.center[2] - CONST_NUM, 0)])
        box.translate(translation)
        corners_translated = corners + translation.reshape(-1, 1)
        self.assertTrue(np.allclose(box.corners(), corners_translated))

    def test_front_corners(self) -> None:
        """Tests the four corners of the front face of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        assert_array_almost_equal(box.front_corners[:, 0], np.array([1, 1, 1]))
        assert_array_almost_equal(box.front_corners[:, 1], np.array([1, -1, 1]))
        assert_array_almost_equal(box.front_corners[:, 2], np.array([1, -1, -1]))
        assert_array_almost_equal(box.front_corners[:, 3], np.array([1, 1, -1]))

    def test_rear_corners(self) -> None:
        """Tests the four corners of the rear face of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        assert_array_almost_equal(box.rear_corners[:, 0], np.array([-1, 1, 1]))
        assert_array_almost_equal(box.rear_corners[:, 1], np.array([-1, -1, 1]))
        assert_array_almost_equal(box.rear_corners[:, 2], np.array([-1, -1, -1]))
        assert_array_almost_equal(box.rear_corners[:, 3], np.array([-1, 1, -1]))

    def test_bottom_corners(self) -> None:
        """Tests the four bottom corners of the box."""
        box = Box3D((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), Quaternion(axis=(0.0, 0.0, 1.0), angle=0))
        assert_array_almost_equal(box.bottom_corners[:, 0], np.array([1, -1, -1]))
        assert_array_almost_equal(box.bottom_corners[:, 1], np.array([1, 1, -1]))
        assert_array_almost_equal(box.bottom_corners[:, 2], np.array([-1, 1, -1]))
        assert_array_almost_equal(box.bottom_corners[:, 3], np.array([-1, -1, -1]))

    def test_box_only_size_error(self) -> None:
        """Tests that invalid box sizes get rejected."""
        center = (1, 1, 1)
        quaternion = Quaternion(axis=(0.0, 0.0, 1.0), angle=0)
        size = (-1, 1, 1)
        self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
        size = (1, -1, 1)
        self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
        size = (1, 1, -1)
        self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
        size = (-1, -1, -1)
        self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)

def test_box_only_size_error(self) -> None:
    """Tests that invalid box sizes get rejected."""
    center = (1, 1, 1)
    quaternion = Quaternion(axis=(0.0, 0.0, 1.0), angle=0)
    size = (-1, 1, 1)
    self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
    size = (1, -1, 1)
    self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
    size = (1, 1, -1)
    self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)
    size = (-1, -1, -1)
    self.assertRaises(AssertionError, Box3D, center=center, size=size, orientation=quaternion)

class TestImage(unittest.TestCase):
    """Test suite for the Image class using synthetic image."""

    def setUp(self) -> None:
        """Inherited, see superclass"""
        pil_img: PilImg.Image = PilImg.new('RGB', (500, 500))
        self.image = Image(pil_img)

    def _test_numpy_type(self, img: Any) -> None:
        """
        Checks if the given object is a numpy array with dtype uint8.
        :param img: The image object to test. Type hint any because the test should be valid for all objects.
        """
        self.assertEqual(np.ndarray, type(img))
        self.assertEqual(np.uint8, img.dtype)
        self.assertNotEqual(np.float64, img.dtype)

    def test_as_pil(self) -> None:
        """Test the function as_pil."""
        img = self.image.as_pil
        self.assertEqual(PilImg.Image, type(img))

    def test_as_numpy_nocache(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_numpy_nocache()
        self._test_numpy_type(img)

    def test_as_numpy(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_numpy
        self._test_numpy_type(img)

    def test_as_cv2_nocache(self) -> None:
        """Test the function as_cv2_nocache."""
        img = self.image.as_cv2_nocache()
        self._test_numpy_type(img)

    def test_as_cv2(self) -> None:
        """Test the function as_numpy_nocache."""
        img = self.image.as_cv2
        self._test_numpy_type(img)

def test_as_pil(self) -> None:
    """Test the function as_pil."""
    img = self.image.as_pil
    self.assertEqual(PilImg.Image, type(img))

class TestTryNTimes(unittest.TestCase, HelperTestingSetup):
    """Test suite for tests that lets tests run multiple times before declaring failure."""

    def setUp(self) -> None:
        """Inherited, see superclass"""
        HelperTestingSetup.__init__(self)

    def test_fails_on_invalid_number_of_tries(self) -> None:
        """Tests that we calling this method with zero tries result in failure."""
        with self.assertRaises(AssertionError):
            _ = try_n_times(self.passing_function, [], {}, self.errors, max_tries=0)

    def test_pass_on_valid_cases(self) -> None:
        """Tests that for nominal cases the output of the function is returned."""
        result = try_n_times(self.passing_function, self.args, self.kwargs, self.errors, max_tries=1)
        self.assertEqual('result', result)
        self.passing_function.assert_called_once_with(*self.args, **self.kwargs)

    @patch('time.sleep')
    def test_fail_on_invalid_case_after_n_tries(self, mock_sleep: Mock) -> None:
        """Tests that the helper throws after too many attempts."""
        with self.assertRaises(self.errors[0]):
            _ = try_n_times(self.failing_function, self.args, self.kwargs, self.errors, max_tries=2, sleep_time=4.2)
        calls = [call(*self.args, **self.kwargs)] * 2
        self.failing_function.assert_has_calls(calls)
        mock_sleep.assert_called_with(4.2)

def test_fails_on_invalid_number_of_tries(self) -> None:
    """Tests that we calling this method with zero tries result in failure."""
    with self.assertRaises(AssertionError):
        _ = try_n_times(self.passing_function, [], {}, self.errors, max_tries=0)

class TestKeepTrying(unittest.TestCase, HelperTestingSetup):
    """Test suite for tests that lets tests run until a timeout is reached before declaring failure."""

    def setUp(self) -> None:
        """Inherited, see superclass"""
        HelperTestingSetup.__init__(self)

    def test_fails_on_invalid_number_of_tries(self) -> None:
        """Tests that we calling this method with zero tries result in failure."""
        with self.assertRaises(AssertionError):
            _ = keep_trying(self.passing_function, [], {}, self.errors, timeout=0.0)

    def test_pass_on_valid_cases(self) -> None:
        """Tests that for nominal cases the output of the function is returned."""
        result, _ = keep_trying(self.passing_function, self.args, self.kwargs, self.errors, timeout=1)
        self.assertEqual('result', result)
        self.passing_function.assert_called_once_with(*self.args, **self.kwargs)

    def test_fail_on_invalid_case_after_timeout(self) -> None:
        """Tests that the helper throws after timeout."""
        with self.assertRaises(TimeoutError):
            _ = keep_trying(self.failing_function, self.args, self.kwargs, self.errors, timeout=1e-06, sleep_time=1e-05)
        self.failing_function.assert_called_with(*self.args, **self.kwargs)

def test_fails_on_invalid_number_of_tries(self) -> None:
    """Tests that we calling this method with zero tries result in failure."""
    with self.assertRaises(AssertionError):
        _ = keep_trying(self.passing_function, [], {}, self.errors, timeout=0.0)

def test_fail_on_invalid_case_after_timeout(self) -> None:
    """Tests that the helper throws after timeout."""
    with self.assertRaises(TimeoutError):
        _ = keep_trying(self.failing_function, self.args, self.kwargs, self.errors, timeout=1e-06, sleep_time=1e-05)
    self.failing_function.assert_called_with(*self.args, **self.kwargs)

def test_initialize_all_layers(map_factory: NuPlanMapFactory) -> None:
    """Tests initialize all layers function"""
    nuplan_map = map_factory.build_map_from_name('us-nv-las-vegas-strip')
    assert not nuplan_map._vector_map
    nuplan_map.initialize_all_layers()
    assert nuplan_map._vector_map

class TestTimeDuration(unittest.TestCase):
    """Tests for TimeDurationClass"""

    def test_default_initialization(self) -> None:
        """Checks raising when constructor is called directly unless flagged."""
        with self.assertRaises(RuntimeError):
            _ = TimeDuration(time_us=42)
        dt = TimeDuration(time_us=42, _direct=False)
        self.assertEqual(dt.time_us, 42)

    def test_constructors(self) -> None:
        """Checks constructors perform correct conversions"""
        dt_s = TimeDuration.from_s(42)
        dt_ms = TimeDuration.from_ms(42)
        dt_us = TimeDuration.from_us(42)
        self.assertEqual(dt_s.time_us, 42000000)
        self.assertEqual(dt_ms.time_us, 42000)
        self.assertEqual(dt_us.time_us, 42)

    def test_getters(self) -> None:
        """Checks getters work as intended"""
        dt = TimeDuration.from_s(42)
        value_s = dt.time_s
        value_ms = dt.time_ms
        value_us = dt.time_us
        self.assertEqual(value_s, 42)
        self.assertEqual(value_ms, 42000)
        self.assertEqual(value_us, 42000000)

    def test_operators(self) -> None:
        """Tests basic math operators."""
        t1 = TimeDuration.from_s(1)
        t2 = TimeDuration.from_s(2)
        self.assertTrue(t2 > t1)
        self.assertFalse(t2 < t1)
        self.assertTrue(t1 < t2)
        self.assertFalse(t1 > t2)
        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 <= t1)
        self.assertEqual((t1 + t2).time_s, 3)
        self.assertEqual((t1 - t2).time_s, -1)
        self.assertEqual((t1 * 3).time_s, 3)
        self.assertEqual((3 * t1).time_s, 3)
        self.assertEqual((t2 / 2).time_s, 1)
        self.assertEqual((t2 // 3).time_s, 0)

def test_default_initialization(self) -> None:
    """Checks raising when constructor is called directly unless flagged."""
    with self.assertRaises(RuntimeError):
        _ = TimeDuration(time_us=42)
    dt = TimeDuration(time_us=42, _direct=False)
    self.assertEqual(dt.time_us, 42)

class TestTimePoint(unittest.TestCase):
    """Tests for TimePoint class."""

    def test_initialization(self) -> None:
        """Tests initialization fails with negative values and works otherwise."""
        with self.assertRaises(AssertionError):
            _ = TimePoint(-42)
        t1 = TimePoint(123456)
        self.assertEqual(t1.time_us, 123456)

    def test_comparisons(self) -> None:
        """Test basic comparison operators."""
        t1 = TimePoint(123123)
        t2 = TimePoint(234234)
        self.assertTrue(t2 > t1)
        self.assertFalse(t2 < t1)
        self.assertTrue(t1 < t2)
        self.assertFalse(t1 > t2)
        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 <= t1)

    def test_addition(self) -> None:
        """Tests addition and subtractions."""
        t1 = TimePoint(123)
        dt = TimeDuration.from_us(100)
        self.assertEqual(t1 + dt, TimePoint(223))
        self.assertEqual(dt + t1, TimePoint(223))
        self.assertEqual(t1 - dt, TimePoint(23))

def test_initialization(self) -> None:
    """Tests initialization fails with negative values and works otherwise."""
    with self.assertRaises(AssertionError):
        _ = TimePoint(-42)
    t1 = TimePoint(123456)
    self.assertEqual(t1.time_us, 123456)

class TestAgent(unittest.TestCase):
    """Test suite for the Agent class"""

    def setUp(self) -> None:
        """Setup parameters for tests"""
        self.sample_token = 'abc123'
        self.track_token = 'abc123'
        self.timestamp = 123
        self.agent_type = TrackedObjectType.VEHICLE
        self.sample_pose = StateSE2(1.0, 2.0, np.pi / 2.0)
        self.wlh = (2.0, 4.0, 1.5)
        self.velocity = StateVector2D(1.0, 2.2)

    def test_agent_state(self) -> None:
        """Test AgentState."""
        angular_velocity = 10.0
        oriented_box = get_sample_oriented_box()
        metadata = SceneObjectMetadata(token=self.sample_token, track_token=self.track_token, timestamp_us=self.timestamp, track_id=None)
        agent_state = AgentState(TrackedObjectType.VEHICLE, oriented_box=oriented_box, velocity=self.velocity, metadata=metadata, angular_velocity=angular_velocity)
        self.assertEqual(agent_state.tracked_object_type, TrackedObjectType.VEHICLE)
        self.assertEqual(agent_state.box, oriented_box)
        self.assertEqual(agent_state.metadata, metadata)
        self.assertEqual(agent_state.velocity, self.velocity)
        self.assertEqual(agent_state.angular_velocity, angular_velocity)
        self.assertEqual(agent_state.token, metadata.token)
        self.assertEqual(agent_state.track_token, metadata.track_token)

    def test_agent_types(self) -> None:
        """Test that enum works for both existing and missing keys"""
        self.assertEqual(TrackedObjectType(0), TrackedObjectType.VEHICLE)
        self.assertEqual(TrackedObjectType.VEHICLE.fullname, 'vehicle')
        with self.assertRaises(ValueError):
            TrackedObjectType('missing_key')

    def test_construction(self) -> None:
        """Test that agents can be constructed correctly."""
        oriented_box = get_sample_oriented_box()
        agent = Agent(metadata=SceneObjectMetadata(token=self.sample_token, track_token=self.track_token, timestamp_us=self.timestamp, track_id=None), tracked_object_type=self.agent_type, oriented_box=oriented_box, velocity=self.velocity)
        self.assertTrue(agent.angular_velocity is None)

    def test_set_predictions(self) -> None:
        """Tests assignment of predictions to agents, and that this fails if the probabilities don't sum to one."""
        agent = get_sample_agent()
        waypoints = [Waypoint(TimePoint(t), get_sample_oriented_box(), StateVector2D(0.0, 0.0)) for t in range(5)]
        predictions = [PredictedTrajectory(0.3, waypoints), PredictedTrajectory(0.7, waypoints)]
        agent.predictions = predictions
        self.assertEqual(len(agent.predictions), 2)
        self.assertEqual(0.3, agent.predictions[0].probability)
        self.assertEqual(0.7, agent.predictions[1].probability)
        predictions += predictions
        with self.assertRaises(ValueError):
            agent.predictions = predictions

    def test_set_past_trajectory(self) -> None:
        """Tests assignment of past trajectory to agents."""
        agent = get_sample_agent()
        waypoints = [Waypoint(TimePoint(t), get_sample_oriented_box(), StateVector2D(0.0, 0.0)) for t in range(agent.metadata.timestamp_us + 1)]
        agent.past_trajectory = PredictedTrajectory(1, waypoints)
        self.assertEqual(len(agent.past_trajectory.waypoints), 11)
        with self.assertRaises(ValueError):
            agent.past_trajectory = PredictedTrajectory(1, [Waypoint(TimePoint(t), get_sample_oriented_box(), StateVector2D(0.0, 0.0)) for t in range(3)])

def test_agent_types(self) -> None:
    """Test that enum works for both existing and missing keys"""
    self.assertEqual(TrackedObjectType(0), TrackedObjectType.VEHICLE)
    self.assertEqual(TrackedObjectType.VEHICLE.fullname, 'vehicle')
    with self.assertRaises(ValueError):
        TrackedObjectType('missing_key')

@dataclass(frozen=True)
class SceneColor:
    """
    Represents all colors needed for a scene.
    """
    trajectory_color: Color
    prediction_bike_color: Color
    prediction_pedestrian_color: Color
    prediction_vehicle_color: Color

    def __iter__(self) -> Iterator[Color]:
        """
        Return color components.
        """
        return iter(astuple(self))

    def __mul__(self, other: float) -> SceneColor:
        """
        Return new SceneColor with all color components multiplied by other.
        :param other: Factor to multiply all colors by.
        :return: A new SceneColor, with each color being multiplied by other.
        """
        if isinstance(other, (float, int)):
            return SceneColor(*(color * other for color in self))
        else:
            raise TypeError(f"TypeError: unsupported operand type(s) for *: 'SceneColor' and '{type(other)}')")

    def __rmul__(self, other: float) -> SceneColor:
        """
        Return new SceneColor with all color components multiplied by other.
        :param other: Factor to multiply all colors by.
        :return: A new SceneColor, with each color being multiplied by other.
        """
        return self.__mul__(other)

def __mul__(self, other: float) -> SceneColor:
    """
        Return new SceneColor with all color components multiplied by other.
        :param other: Factor to multiply all colors by.
        :return: A new SceneColor, with each color being multiplied by other.
        """
    if isinstance(other, (float, int)):
        return SceneColor(*(color * other for color in self))
    else:
        raise TypeError(f"TypeError: unsupported operand type(s) for *: 'SceneColor' and '{type(other)}')")

class TestSceneColor(TestCase):
    """
    Test scene color.
    """

    def setUp(self) -> None:
        """
        Set up.
        """
        self.trajectory_color = MagicMock(name='1', spec=Color)
        self.prediction_bike_color = MagicMock(name='2', spec=Color)
        self.prediction_pedestrian_color = MagicMock(name='3', spec=Color)
        self.prediction_vehicle_color = MagicMock(name='4', spec=Color)
        self.scene_color = SceneColor(self.trajectory_color, self.prediction_bike_color, self.prediction_pedestrian_color, self.prediction_vehicle_color)

    def test_init(self) -> None:
        """
        Test initialisation.
        """
        self.assertEqual(self.scene_color.trajectory_color, self.trajectory_color)
        self.assertEqual(self.scene_color.prediction_bike_color, self.prediction_bike_color)
        self.assertEqual(self.scene_color.prediction_pedestrian_color, self.prediction_pedestrian_color)
        self.assertEqual(self.scene_color.prediction_vehicle_color, self.prediction_vehicle_color)

    def test_iter(self) -> None:
        """
        Tests iteration of colors.
        """
        result = [color for color in self.scene_color]
        self.assertEqual(result[0], self.trajectory_color)
        self.assertEqual(result[1], self.prediction_bike_color)
        self.assertEqual(result[2], self.prediction_pedestrian_color)
        self.assertEqual(result[3], self.prediction_vehicle_color)

    def test_mul(self) -> None:
        """
        Tests multiplication operation.
        """
        result = self.scene_color * 0.75
        self.assertEqual(result, SceneColor(self.trajectory_color.__mul__.return_value, self.prediction_bike_color.__mul__.return_value, self.prediction_pedestrian_color.__mul__.return_value, self.prediction_vehicle_color.__mul__.return_value))

    @patch('nuplan.planning.utils.color.SceneColor.__mul__')
    def test_rmul(self, mock_mul: Mock) -> None:
        """
        Tests reverse multiplication operation.
        """
        result = 0.75 * self.scene_color
        mock_mul.assert_called_once_with(0.75)
        self.assertEqual(result, mock_mul.return_value)

def setUp(self) -> None:
    """
        Set up.
        """
    self.trajectory_color = MagicMock(name='1', spec=Color)
    self.prediction_bike_color = MagicMock(name='2', spec=Color)
    self.prediction_pedestrian_color = MagicMock(name='3', spec=Color)
    self.prediction_vehicle_color = MagicMock(name='4', spec=Color)
    self.scene_color = SceneColor(self.trajectory_color, self.prediction_bike_color, self.prediction_pedestrian_color, self.prediction_vehicle_color)

def test_mul(self) -> None:
    """
        Tests multiplication operation.
        """
    result = self.scene_color * 0.75
    self.assertEqual(result, SceneColor(self.trajectory_color.__mul__.return_value, self.prediction_bike_color.__mul__.return_value, self.prediction_pedestrian_color.__mul__.return_value, self.prediction_vehicle_color.__mul__.return_value))

class Simulation:
    """
    This class queries data for initialization of a planner, and propagates simulation a step forward based on the
        planned trajectory of a planner.
    """

    def __init__(self, simulation_setup: SimulationSetup, callback: Optional[AbstractCallback]=None, simulation_history_buffer_duration: float=2):
        """
        Create Simulation.
        :param simulation_setup: Configuration that describes the simulation.
        :param callback: A callback to be executed for this simulation setup
        :param simulation_history_buffer_duration: [s] Duration to pre-load scenario into the buffer.
        """
        if simulation_history_buffer_duration < simulation_setup.scenario.database_interval:
            raise ValueError(f'simulation_history_buffer_duration {simulation_history_buffer_duration} has to be larger than the scenario database_interval {simulation_setup.scenario.database_interval}')
        self._setup = simulation_setup
        self._time_controller = simulation_setup.time_controller
        self._ego_controller = simulation_setup.ego_controller
        self._observations = simulation_setup.observations
        self._scenario = simulation_setup.scenario
        self._callback = MultiCallback([]) if callback is None else callback
        self._history = SimulationHistory(self._scenario.map_api, self._scenario.get_mission_goal())
        self._simulation_history_buffer_duration = simulation_history_buffer_duration + self._scenario.database_interval
        self._history_buffer_size = int(self._simulation_history_buffer_duration / self._scenario.database_interval) + 1
        self._history_buffer: Optional[SimulationHistoryBuffer] = None
        self._is_simulation_running = True

    def __reduce__(self) -> Tuple[Type[Simulation], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._setup, self._callback, self._simulation_history_buffer_duration))

    def is_simulation_running(self) -> bool:
        """
        Check whether a simulation reached the end
        :return True if simulation hasn't reached the end, otherwise false.
        """
        return not self._time_controller.reached_end() and self._is_simulation_running

    def reset(self) -> None:
        """
        Reset all internal states of simulation.
        """
        self._history.reset()
        self._setup.reset()
        self._history_buffer = None
        self._is_simulation_running = True

    def initialize(self) -> PlannerInitialization:
        """
        Initialize the simulation
         - Initialize Planner with goals and maps
        :return data needed for planner initialization.
        """
        self.reset()
        self._history_buffer = SimulationHistoryBuffer.initialize_from_scenario(self._history_buffer_size, self._scenario, self._observations.observation_type())
        self._observations.initialize()
        self._history_buffer.append(self._ego_controller.get_state(), self._observations.get_observation())
        return PlannerInitialization(route_roadblock_ids=self._scenario.get_route_roadblock_ids(), mission_goal=self._scenario.get_mission_goal(), map_api=self._scenario.map_api)

    def get_planner_input(self) -> PlannerInput:
        """
        Construct inputs to the planner for the current iteration step
        :return Inputs to the planner.
        """
        if self._history_buffer is None:
            raise RuntimeError('Simulation was not initialized!')
        if not self.is_simulation_running():
            raise RuntimeError('Simulation is not running, stepping can not be performed!')
        iteration = self._time_controller.get_iteration()
        traffic_light_data = list(self._scenario.get_traffic_light_status_at_iteration(iteration.index))
        logger.debug(f'Executing {iteration.index}!')
        return PlannerInput(iteration=iteration, history=self._history_buffer, traffic_light_data=traffic_light_data)

    def propagate(self, trajectory: AbstractTrajectory) -> None:
        """
        Propagate the simulation based on planner's trajectory and the inputs to the planner
        This function also decides whether simulation should still continue. This flag can be queried through
        reached_end() function
        :param trajectory: computed trajectory from planner.
        """
        if self._history_buffer is None:
            raise RuntimeError('Simulation was not initialized!')
        if not self.is_simulation_running():
            raise RuntimeError('Simulation is not running, simulation can not be propagated!')
        iteration = self._time_controller.get_iteration()
        ego_state, observation = self._history_buffer.current_state
        traffic_light_status = list(self._scenario.get_traffic_light_status_at_iteration(iteration.index))
        logger.debug(f'Adding to history: {iteration.index}')
        self._history.add_sample(SimulationHistorySample(iteration, ego_state, trajectory, observation, traffic_light_status))
        next_iteration = self._time_controller.next_iteration()
        if next_iteration:
            self._ego_controller.update_state(iteration, next_iteration, ego_state, trajectory)
            self._observations.update_observation(iteration, next_iteration, self._history_buffer)
        else:
            self._is_simulation_running = False
        self._history_buffer.append(self._ego_controller.get_state(), self._observations.get_observation())

    @property
    def scenario(self) -> AbstractScenario:
        """
        :return: used scenario in this simulation.
        """
        return self._scenario

    @property
    def setup(self) -> SimulationSetup:
        """
        :return: Setup for this simulation.
        """
        return self._setup

    @property
    def callback(self) -> AbstractCallback:
        """
        :return: Callback for this simulation.
        """
        return self._callback

    @property
    def history(self) -> SimulationHistory:
        """
        :return History from the simulation.
        """
        return self._history

    @property
    def history_buffer(self) -> SimulationHistoryBuffer:
        """
        :return SimulationHistoryBuffer from the simulation.
        """
        if self._history_buffer is None:
            raise RuntimeError('_history_buffer is None. Please initialize the buffer by calling Simulation.initialize()')
        return self._history_buffer

def is_simulation_running(self) -> bool:
    """
        Check whether a simulation reached the end
        :return True if simulation hasn't reached the end, otherwise false.
        """
    return not self._time_controller.reached_end() and self._is_simulation_running

def reset(self) -> None:
    """
        Reset all internal states of simulation.
        """
    self._history.reset()
    self._setup.reset()
    self._history_buffer = None
    self._is_simulation_running = True

def initialize(self) -> PlannerInitialization:
    """
        Initialize the simulation
         - Initialize Planner with goals and maps
        :return data needed for planner initialization.
        """
    self.reset()
    self._history_buffer = SimulationHistoryBuffer.initialize_from_scenario(self._history_buffer_size, self._scenario, self._observations.observation_type())
    self._observations.initialize()
    self._history_buffer.append(self._ego_controller.get_state(), self._observations.get_observation())
    return PlannerInitialization(route_roadblock_ids=self._scenario.get_route_roadblock_ids(), mission_goal=self._scenario.get_mission_goal(), map_api=self._scenario.map_api)

def get_planner_input(self) -> PlannerInput:
    """
        Construct inputs to the planner for the current iteration step
        :return Inputs to the planner.
        """
    if self._history_buffer is None:
        raise RuntimeError('Simulation was not initialized!')
    if not self.is_simulation_running():
        raise RuntimeError('Simulation is not running, stepping can not be performed!')
    iteration = self._time_controller.get_iteration()
    traffic_light_data = list(self._scenario.get_traffic_light_status_at_iteration(iteration.index))
    logger.debug(f'Executing {iteration.index}!')
    return PlannerInput(iteration=iteration, history=self._history_buffer, traffic_light_data=traffic_light_data)

def propagate(self, trajectory: AbstractTrajectory) -> None:
    """
        Propagate the simulation based on planner's trajectory and the inputs to the planner
        This function also decides whether simulation should still continue. This flag can be queried through
        reached_end() function
        :param trajectory: computed trajectory from planner.
        """
    if self._history_buffer is None:
        raise RuntimeError('Simulation was not initialized!')
    if not self.is_simulation_running():
        raise RuntimeError('Simulation is not running, simulation can not be propagated!')
    iteration = self._time_controller.get_iteration()
    ego_state, observation = self._history_buffer.current_state
    traffic_light_status = list(self._scenario.get_traffic_light_status_at_iteration(iteration.index))
    logger.debug(f'Adding to history: {iteration.index}')
    self._history.add_sample(SimulationHistorySample(iteration, ego_state, trajectory, observation, traffic_light_status))
    next_iteration = self._time_controller.next_iteration()
    if next_iteration:
        self._ego_controller.update_state(iteration, next_iteration, ego_state, trajectory)
        self._observations.update_observation(iteration, next_iteration, self._history_buffer)
    else:
        self._is_simulation_running = False
    self._history_buffer.append(self._ego_controller.get_state(), self._observations.get_observation())

@dataclass
class SimulationSetup:
    """Setup class for contructing a Simulation."""
    time_controller: AbstractSimulationTimeController
    observations: AbstractObservation
    ego_controller: AbstractEgoController
    scenario: AbstractScenario

    def __post_init__(self) -> None:
        """Post-initialization sanity checks."""
        assert isinstance(self.time_controller, AbstractSimulationTimeController), 'Error: simulation_time_controller must inherit from AbstractSimulationTimeController!'
        assert isinstance(self.observations, AbstractObservation), 'Error: observations must inherit from AbstractObservation!'
        assert isinstance(self.ego_controller, AbstractEgoController), 'Error: ego_controller must inherit from AbstractEgoController!'

    def reset(self) -> None:
        """
        Reset all simulation controllers
        """
        self.observations.reset()
        self.ego_controller.reset()
        self.time_controller.reset()

def reset(self) -> None:
    """
        Reset all simulation controllers
        """
    self.observations.reset()
    self.ego_controller.reset()
    self.time_controller.reset()

class TestAbstractPredictor(unittest.TestCase):
    """Test the AbstractPredictor interface"""

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.predictor = MockAbstractPredictor()

    def test_initialize(self) -> None:
        """Test initialization"""
        mock_initialization = get_mock_predictor_initialization()
        self.predictor.initialize(mock_initialization)
        self.assertEqual(self.predictor._map_api, mock_initialization.map_api)

    def test_name(self) -> None:
        """Test name"""
        self.assertEqual(self.predictor.name(), 'MockAbstractPredictor')

    def test_observation_type(self) -> None:
        """Test observation_type"""
        self.assertEqual(self.predictor.observation_type(), DetectionsTracks)

    def test_compute_predictions(self) -> None:
        """Test compute_predictions"""
        predictor_input = get_mock_predictor_input()
        start_time = time.perf_counter()
        detections = self.predictor.compute_predictions(predictor_input)
        compute_predictions_time = time.perf_counter() - start_time
        self.assertEqual(type(detections), DetectionsTracks)
        predictor_report = self.predictor.generate_predictor_report()
        self.assertEqual(len(predictor_report.compute_predictions_runtimes), 1)
        self.assertNotIsInstance(predictor_report, MLPredictorReport)
        self.assertAlmostEqual(predictor_report.compute_predictions_runtimes[0], compute_predictions_time, delta=0.1)

def test_initialize(self) -> None:
    """Test initialization"""
    mock_initialization = get_mock_predictor_initialization()
    self.predictor.initialize(mock_initialization)
    self.assertEqual(self.predictor._map_api, mock_initialization.map_api)

def get_mock_predictor_initialization() -> PredictorInitialization:
    """
    Returns a mock PredictorInitialization for testing.
    :return: PredictorInitialization.
    """
    return PredictorInitialization(MockAbstractMap())

class TestSimulation(unittest.TestCase):
    """
    Tests Simulation class which is updating simulation
    """

    def setUp(self) -> None:
        """Setup Mock classes."""
        self.scenario = MockAbstractScenario(number_of_past_iterations=10)
        self.sim_manager = StepSimulationTimeController(self.scenario)
        self.observation = TracksObservation(self.scenario)
        self.controller = PerfectTrackingController(self.scenario)
        self.setup = SimulationSetup(time_controller=self.sim_manager, observations=self.observation, ego_controller=self.controller, scenario=self.scenario)
        self.simulation_history_buffer_duration = 2
        self.stepper = Simulation(simulation_setup=self.setup, callback=MultiCallback([]), simulation_history_buffer_duration=self.simulation_history_buffer_duration)

    def test_stepper_initialize(self) -> None:
        """Test initialization method."""
        initialization = self.stepper.initialize()
        self.assertEqual(initialization.mission_goal, self.scenario.get_mission_goal())
        self.assertEqual(self.stepper._history_buffer.current_state[0].rear_axle, self.scenario.get_ego_state_at_iteration(0).rear_axle)

    def test_stepper_planner_input(self) -> None:
        """Test query to planner input function."""
        stepper = Simulation(simulation_setup=self.setup, callback=MultiCallback([]), simulation_history_buffer_duration=self.simulation_history_buffer_duration)
        stepper.initialize()
        planner_input = stepper.get_planner_input()
        self.assertEqual(planner_input.iteration.index, 0)

    def test_run_callbacks(self) -> None:
        """Test whether all callbacks are called"""
        callback = MagicMock()
        planner = SimplePlanner(2, 0.5, [0, 0])
        stepper = Simulation(simulation_setup=self.setup, callback=MultiCallback([callback]), simulation_history_buffer_duration=self.simulation_history_buffer_duration)
        runner = SimulationRunner(stepper, planner)
        runner.run()
        callback.on_simulation_start.assert_has_calls([call(stepper.setup)])
        callback.on_initialization_end.assert_has_calls([call(stepper.setup, planner)])
        callback.on_initialization_start.assert_has_calls([call(stepper.setup, planner)])
        callback.on_step_start.assert_has_calls([call(stepper.setup, planner)])
        callback.on_planner_start.assert_has_calls([call(stepper.setup, planner)])
        callback.on_step_end.assert_has_calls([call(stepper.setup, planner, stepper.history.last())])
        callback.on_simulation_end.assert_has_calls([call(stepper.setup, planner, stepper.history)])

    def test_buffer_simulation_duration(self) -> None:
        """Test initialization method."""
        self.stepper.initialize()
        simulation_buffer = self.stepper.history_buffer
        self.assertGreaterEqual(simulation_buffer.duration, self.simulation_history_buffer_duration)

def setUp(self) -> None:
    """Setup Mock classes."""
    self.scenario = MockAbstractScenario(number_of_past_iterations=10)
    self.sim_manager = StepSimulationTimeController(self.scenario)
    self.observation = TracksObservation(self.scenario)
    self.controller = PerfectTrackingController(self.scenario)
    self.setup = SimulationSetup(time_controller=self.sim_manager, observations=self.observation, ego_controller=self.controller, scenario=self.scenario)
    self.simulation_history_buffer_duration = 2
    self.stepper = Simulation(simulation_setup=self.setup, callback=MultiCallback([]), simulation_history_buffer_duration=self.simulation_history_buffer_duration)

def test_stepper_initialize(self) -> None:
    """Test initialization method."""
    initialization = self.stepper.initialize()
    self.assertEqual(initialization.mission_goal, self.scenario.get_mission_goal())
    self.assertEqual(self.stepper._history_buffer.current_state[0].rear_axle, self.scenario.get_ego_state_at_iteration(0).rear_axle)

def test_stepper_planner_input(self) -> None:
    """Test query to planner input function."""
    stepper = Simulation(simulation_setup=self.setup, callback=MultiCallback([]), simulation_history_buffer_duration=self.simulation_history_buffer_duration)
    stepper.initialize()
    planner_input = stepper.get_planner_input()
    self.assertEqual(planner_input.iteration.index, 0)

def test_buffer_simulation_duration(self) -> None:
    """Test initialization method."""
    self.stepper.initialize()
    simulation_buffer = self.stepper.history_buffer
    self.assertGreaterEqual(simulation_buffer.duration, self.simulation_history_buffer_duration)

class TestSimulationBufferInitialization(unittest.TestCase):
    """
    A class to test the simulation buffer initialization
    """

    def _test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
        """
        Test the simulation buffer duration is equal or greater than simulation_history_buffer_duration.
        :param time_step: [s] The time interval of the simulation buffer.
        :param simulation_history_buffer_duration: [s] The requested simulation buffer duration.
        """
        scenario = MockAbstractScenario(number_of_past_iterations=200, time_step=time_step)
        sim_manager = StepSimulationTimeController(scenario)
        observation = TracksObservation(scenario)
        controller = PerfectTrackingController(scenario)
        setup = SimulationSetup(time_controller=sim_manager, observations=observation, ego_controller=controller, scenario=scenario)
        stepper = Simulation(simulation_setup=setup, callback=MultiCallback([]), simulation_history_buffer_duration=simulation_history_buffer_duration)
        stepper.initialize()
        simulation_buffer = stepper.history_buffer
        self.assertGreaterEqual(simulation_buffer.duration, simulation_history_buffer_duration)

    @settings(deadline=1000)
    @given(time_step=st.floats(min_value=0.05, max_value=1), simulation_history_buffer_duration=st.floats(min_value=1.0, max_value=10.0))
    @example(time_step=0.5, simulation_history_buffer_duration=2.0)
    def test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
        """Test the simulation buffer initialization."""
        if simulation_history_buffer_duration % time_step > 1e-06:
            return
        if time_step > simulation_history_buffer_duration:
            with self.assertRaises(ValueError):
                self._test_simulation_buffer(time_step, simulation_history_buffer_duration)
        else:
            self._test_simulation_buffer(time_step, simulation_history_buffer_duration)

def _test_simulation_buffer(self, time_step: float, simulation_history_buffer_duration: float) -> None:
    """
        Test the simulation buffer duration is equal or greater than simulation_history_buffer_duration.
        :param time_step: [s] The time interval of the simulation buffer.
        :param simulation_history_buffer_duration: [s] The requested simulation buffer duration.
        """
    scenario = MockAbstractScenario(number_of_past_iterations=200, time_step=time_step)
    sim_manager = StepSimulationTimeController(scenario)
    observation = TracksObservation(scenario)
    controller = PerfectTrackingController(scenario)
    setup = SimulationSetup(time_controller=sim_manager, observations=observation, ego_controller=controller, scenario=scenario)
    stepper = Simulation(simulation_setup=setup, callback=MultiCallback([]), simulation_history_buffer_duration=simulation_history_buffer_duration)
    stepper.initialize()
    simulation_buffer = stepper.history_buffer
    self.assertGreaterEqual(simulation_buffer.duration, simulation_history_buffer_duration)

class LogPlaybackController(AbstractEgoController):
    """
    Replay the GT position from samples
    """

    def __init__(self, scenario: AbstractScenario):
        """
        Initialize a controller which just reads
        :param scenario: to play through
        """
        self.scenario = scenario
        self.current_iteration = 0

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_iteration = 0

    def get_state(self) -> EgoState:
        """Inherited, see superclass."""
        return self.scenario.get_ego_state_at_iteration(self.current_iteration)

    def update_state(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, ego_state: EgoState, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        self.current_iteration = next_iteration.index

def get_state(self) -> EgoState:
    """Inherited, see superclass."""
    return self.scenario.get_ego_state_at_iteration(self.current_iteration)

class TestPerfectTracking(unittest.TestCase):
    """
    Tests Tracker
    """

    def test_perfect_tracker(self) -> None:
        """
        Test the basic functionality of perfect tracker
        """
        initial_time_point = TimePoint(0)
        scenario = MockAbstractScenario(initial_time_us=initial_time_point)
        trajectory = InterpolatedTrajectory(list(scenario.get_expert_ego_trajectory()))
        tracker = PerfectTrackingController(scenario)
        desired_state = scenario.initial_ego_state
        state = scenario.initial_ego_state
        self.assertAlmostEqual(state.rear_axle.x, desired_state.rear_axle.x)
        self.assertAlmostEqual(state.rear_axle.y, desired_state.rear_axle.y)
        self.assertAlmostEqual(state.rear_axle.heading, desired_state.rear_axle.heading)
        tracker.update_state(current_iteration=SimulationIteration(time_point=initial_time_point, index=0), next_iteration=SimulationIteration(time_point=TimePoint(int(1 * 1000000.0)), index=1), ego_state=scenario.initial_ego_state, trajectory=trajectory)
        next_state = tracker.get_state()
        desired_state = scenario.get_ego_state_at_iteration(2)
        self.assertAlmostEqual(next_state.rear_axle.x, desired_state.rear_axle.x)
        self.assertAlmostEqual(next_state.rear_axle.y, desired_state.rear_axle.y)
        self.assertAlmostEqual(next_state.rear_axle.heading, desired_state.rear_axle.heading)

def test_perfect_tracker(self) -> None:
    """
        Test the basic functionality of perfect tracker
        """
    initial_time_point = TimePoint(0)
    scenario = MockAbstractScenario(initial_time_us=initial_time_point)
    trajectory = InterpolatedTrajectory(list(scenario.get_expert_ego_trajectory()))
    tracker = PerfectTrackingController(scenario)
    desired_state = scenario.initial_ego_state
    state = scenario.initial_ego_state
    self.assertAlmostEqual(state.rear_axle.x, desired_state.rear_axle.x)
    self.assertAlmostEqual(state.rear_axle.y, desired_state.rear_axle.y)
    self.assertAlmostEqual(state.rear_axle.heading, desired_state.rear_axle.heading)
    tracker.update_state(current_iteration=SimulationIteration(time_point=initial_time_point, index=0), next_iteration=SimulationIteration(time_point=TimePoint(int(1 * 1000000.0)), index=1), ego_state=scenario.initial_ego_state, trajectory=trajectory)
    next_state = tracker.get_state()
    desired_state = scenario.get_ego_state_at_iteration(2)
    self.assertAlmostEqual(next_state.rear_axle.x, desired_state.rear_axle.x)
    self.assertAlmostEqual(next_state.rear_axle.y, desired_state.rear_axle.y)
    self.assertAlmostEqual(next_state.rear_axle.heading, desired_state.rear_axle.heading)

class LogFuturePlanner(AbstractPlanner):
    """
    Planner which just looks as future GT and returns it as a desired trajectory
    the input to this planner are detections.
    """
    requires_scenario: bool = True

    def __init__(self, scenario: AbstractScenario, num_poses: int, future_time_horizon: float):
        """
        Constructor of LogFuturePlanner.
        :param scenario: The scenario the planner is running on.
        :param num_poses: The number of poses to plan for.
        :param future_time_horizon: [s] The horizon length to plan for.
        """
        self._scenario = scenario
        self._num_poses = num_poses
        self._future_time_horizon = future_time_horizon
        self._trajectory: Optional[AbstractTrajectory] = None

    def initialize(self, initialization: List[PlannerInitialization]) -> None:
        """Inherited, see superclass."""
        pass

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """Inherited, see superclass."""
        current_state = self._scenario.get_ego_state_at_iteration(current_input.iteration.index)
        try:
            states = self._scenario.get_ego_future_trajectory(current_input.iteration.index, self._future_time_horizon, self._num_poses)
            self._trajectory = InterpolatedTrajectory(list(itertools.chain([current_state], states)))
        except AssertionError:
            logger.warning('Cannot retrieve future ego trajectory. Using previous computed trajectory.')
            if self._trajectory is None:
                raise RuntimeError('Future ego trajectory cannot be retrieved from the scenario!')
        return self._trajectory

def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
    """Inherited, see superclass."""
    current_state = self._scenario.get_ego_state_at_iteration(current_input.iteration.index)
    try:
        states = self._scenario.get_ego_future_trajectory(current_input.iteration.index, self._future_time_horizon, self._num_poses)
        self._trajectory = InterpolatedTrajectory(list(itertools.chain([current_state], states)))
    except AssertionError:
        logger.warning('Cannot retrieve future ego trajectory. Using previous computed trajectory.')
        if self._trajectory is None:
            raise RuntimeError('Future ego trajectory cannot be retrieved from the scenario!')
    return self._trajectory

class IDMPlanner(AbstractIDMPlanner):
    """
    The IDM planner is composed of two parts:
        1. Path planner that constructs a route to the same road block as the goal pose.
        2. IDM policy controller to control the longitudinal movement of the ego along the planned route.
    """
    requires_scenario: bool = False

    def __init__(self, target_velocity: float, min_gap_to_lead_agent: float, headway_time: float, accel_max: float, decel_max: float, planned_trajectory_samples: int, planned_trajectory_sample_interval: float, occupancy_map_radius: float):
        """
        Constructor for IDMPlanner
        :param target_velocity: [m/s] Desired velocity in free traffic.
        :param min_gap_to_lead_agent: [m] Minimum relative distance to lead vehicle.
        :param headway_time: [s] Desired time headway. The minimum possible time to the vehicle in front.
        :param accel_max: [m/s^2] maximum acceleration.
        :param decel_max: [m/s^2] maximum deceleration (positive value).
        :param planned_trajectory_samples: number of elements to sample for the planned trajectory.
        :param planned_trajectory_sample_interval: [s] time interval of sequence to sample from.
        :param occupancy_map_radius: [m] The range around the ego to add objects to be considered.
        """
        super(IDMPlanner, self).__init__(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max, planned_trajectory_samples, planned_trajectory_sample_interval, occupancy_map_radius)
        self._initialized = False

    def initialize(self, initialization: PlannerInitialization) -> None:
        """Inherited, see superclass."""
        self._map_api = initialization.map_api
        self._initialize_route_plan(initialization.route_roadblock_ids)
        self._initialized = False

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """Inherited, see superclass."""
        ego_state, observations = current_input.history.current_state
        if not self._initialized:
            self._initialize_ego_path(ego_state)
            self._initialized = True
        occupancy_map, unique_observations = self._construct_occupancy_map(ego_state, observations)
        traffic_light_data = current_input.traffic_light_data
        self._annotate_occupancy_map(traffic_light_data, occupancy_map)
        return self._get_planned_trajectory(ego_state, occupancy_map, unique_observations)

    def _initialize_ego_path(self, ego_state: EgoState) -> None:
        """
        Initializes the ego path from the ground truth driven trajectory
        :param ego_state: The ego state at the start of the scenario.
        """
        route_plan, _ = self._breadth_first_search(ego_state)
        ego_speed = ego_state.dynamic_car_state.rear_axle_velocity_2d.magnitude()
        speed_limit = route_plan[0].speed_limit_mps or self._policy.target_velocity
        self._policy.target_velocity = speed_limit if speed_limit > ego_speed else ego_speed
        discrete_path = []
        for edge in route_plan:
            discrete_path.extend(edge.baseline_path.discrete_path)
        self._ego_path = create_path_from_se2(discrete_path)
        self._ego_path_linestring = path_to_linestring(discrete_path)

    def _get_starting_edge(self, ego_state: EgoState) -> LaneGraphEdgeMapObject:
        """
        Get the starting edge based on ego state. If a lane graph object does not contain the ego state then
        the closest one is taken instead.
        :param ego_state: Current ego state.
        :return: The starting LaneGraphEdgeMapObject.
        """
        assert self._route_roadblocks is not None, '_route_roadblocks has not yet been initialized. Please call the initialize() function first!'
        assert len(self._route_roadblocks) >= 2, '_route_roadblocks should have at least 2 elements!'
        starting_edge = None
        closest_distance = math.inf
        for edge in self._route_roadblocks[0].interior_edges + self._route_roadblocks[1].interior_edges:
            if edge.contains_point(ego_state.center):
                starting_edge = edge
                break
            distance = edge.polygon.distance(ego_state.car_footprint.geometry)
            if distance < closest_distance:
                starting_edge = edge
                closest_distance = distance
        assert starting_edge, 'Starting edge for IDM path planning could not be found!'
        return starting_edge

    def _breadth_first_search(self, ego_state: EgoState) -> Tuple[List[LaneGraphEdgeMapObject], bool]:
        """
        Performs iterative breath first search to find a route to the target roadblock.
        :param ego_state: Current ego state.
        :return:
            - A route starting from the given start edge
            - A bool indicating if the route is successfully found. Successful means that there exists a path
              from the start edge to an edge contained in the end roadblock. If unsuccessful a longest route is given.
        """
        assert self._route_roadblocks is not None, '_route_roadblocks has not yet been initialized. Please call the initialize() function first!'
        assert self._candidate_lane_edge_ids is not None, '_candidate_lane_edge_ids has not yet been initialized. Please call the initialize() function first!'
        starting_edge = self._get_starting_edge(ego_state)
        graph_search = BreadthFirstSearch(starting_edge, self._candidate_lane_edge_ids)
        offset = 1 if starting_edge.get_roadblock_id() == self._route_roadblocks[1].id else 0
        route_plan, path_found = graph_search.search(self._route_roadblocks[-1], len(self._route_roadblocks[offset:]))
        if not path_found:
            logger.warning('IDMPlanner could not find valid path to the target roadblock. Using longest route found instead')
        return (route_plan, path_found)

def initialize(self, initialization: PlannerInitialization) -> None:
    """Inherited, see superclass."""
    self._map_api = initialization.map_api
    self._initialize_route_plan(initialization.route_roadblock_ids)
    self._initialized = False

class MockIDMPlanner(AbstractIDMPlanner):
    """
    Mock IDMPlanner class for testing the AbstractIDMPlanner interface
    """
    requires_scenario: bool = False

    def __init__(self, target_velocity: float, min_gap_to_lead_agent: float, headway_time: float, accel_max: float, decel_max: float, planned_trajectory_samples: int, planned_trajectory_sample_interval: float, occupancy_map_radius: float):
        """
        Constructor for IDMPlanner
        :param target_velocity: [m/s] Desired velocity in free traffic.
        :param min_gap_to_lead_agent: [m] Minimum relative distance to lead vehicle.
        :param headway_time: [s] Desired time headway. The minimum possible time to the vehicle in front.
        :param accel_max: [m/s^2] maximum acceleration.
        :param decel_max: [m/s^2] maximum deceleration (positive value).
        :param planned_trajectory_samples: number of elements to sample for the planned trajectory.
        :param planned_trajectory_sample_interval: [s] time interval of sequence to sample from.
        :param occupancy_map_radius: [m] The range around the ego to add objects to be considered.
        """
        super(MockIDMPlanner, self).__init__(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max, planned_trajectory_samples, planned_trajectory_sample_interval, occupancy_map_radius)
        self._scenario = MockAbstractScenario()
        self._scenario_buffer = 10

    def initialize(self, initialization: List[PlannerInitialization]) -> None:
        """Inherited, see superclass."""
        self._map_api = initialization[0].map_api
        self._initialize_route_plan(initialization[0].route_roadblock_ids)
        self._ego_path: InterpolatedPath = create_path_from_ego_state(self._scenario.get_ego_future_trajectory(0, self._scenario_buffer, 10))
        self._ego_path_linestring = LineString()

    def compute_planner_trajectory(self, current_input: List[PlannerInput]) -> List[AbstractTrajectory]:
        """Inherited, see superclass."""
        return [InterpolatedTrajectory(self._ego_path.get_sampled_path())]

def initialize(self, initialization: List[PlannerInitialization]) -> None:
    """Inherited, see superclass."""
    self._map_api = initialization[0].map_api
    self._initialize_route_plan(initialization[0].route_roadblock_ids)
    self._ego_path: InterpolatedPath = create_path_from_ego_state(self._scenario.get_ego_future_trajectory(0, self._scenario_buffer, 10))
    self._ego_path_linestring = LineString()

class TestAbstractIDMPlanner(unittest.TestCase):
    """Test the AbstractIDMPlanner interface"""
    TEST_FILE_PATH = 'nuplan.planning.simulation.planner.abstract_idm_planner'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.scenario = get_test_nuplan_scenario()
        self.planned_trajectory_samples = 10
        self.planner = MockIDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

    def test_name(self) -> None:
        """Test name"""
        self.assertEqual(self.planner.name(), 'MockIDMPlanner')

    def test_observation_type(self) -> None:
        """Test observation_type"""
        self.assertEqual(self.planner.observation_type(), DetectionsTracks)

    def test__initialize_route_plan_assertion_error(self) -> None:
        """Test raise if _map_api is uninitialized"""
        with self.assertRaises(AssertionError):
            self.planner._initialize_route_plan([])

    def test__initialize_route_plan(self) -> None:
        """Test _map_api is uninitialized."""
        with patch.object(self.planner, '_map_api') as _map_api:
            _map_api.get_map_object = Mock()
            _map_api.get_map_object.side_effect = [MagicMock(), None, MagicMock()]
            mock_route_roadblock_ids = ['a']
            self.planner._initialize_route_plan(mock_route_roadblock_ids)
            _map_api.get_map_object.assert_called_with('a', SemanticMapLayer.ROADBLOCK)
            mock_route_roadblock_ids = ['b']
            self.planner._initialize_route_plan(mock_route_roadblock_ids)
            _map_api.get_map_object.assert_called_with('b', SemanticMapLayer.ROADBLOCK_CONNECTOR)

    def test__construct_occupancy_map_value_error(self) -> None:
        """Test raise if observation type is incorrect"""
        with self.assertRaises(ValueError):
            self.planner._construct_occupancy_map(Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.STRTreeOccupancyMapFactory.get_from_boxes')
    def test__construct_occupancy_map(self, mock_get_from_boxes: Mock) -> None:
        """Test raise if observation type is incorrect"""
        mock_observations = self.scenario.initial_tracked_objects
        mock_ego_state = self.scenario.initial_ego_state
        self.planner._construct_occupancy_map(mock_ego_state, mock_observations)
        mock_get_from_boxes.assert_called_once()

    def test__propagate(self) -> None:
        """Test _propagate()"""
        with patch.object(self.planner, '_policy') as _policy:
            init_progress = 1
            init_velocity = 2
            tspan = 0.5
            mock_ego_idm_state = IDMAgentState(init_progress, init_velocity)
            mock_lead_agent = Mock()
            _policy.solve_forward_euler_idm_policy = Mock(return_value=IDMAgentState(3, 4))
            self.planner._propagate(mock_ego_idm_state, mock_lead_agent, tspan)
            _policy.solve_forward_euler_idm_policy.assert_called_once_with(IDMAgentState(0, init_velocity), mock_lead_agent, tspan)
            self.assertEqual(init_progress + _policy.solve_forward_euler_idm_policy().progress, mock_ego_idm_state.progress)
            self.assertEqual(_policy.solve_forward_euler_idm_policy().velocity, mock_ego_idm_state.velocity)

    def test__get_planned_trajectory_error(self) -> None:
        """Test raise if _ego_path_linestring has not been initialized"""
        with self.assertRaises(AssertionError):
            self.planner._get_planned_trajectory(Mock(), Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.InterpolatedTrajectory')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._propagate')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._get_leading_object')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._idm_state_to_ego_state')
    def test__get_planned_trajectory(self, mock_idm_state_to_ego_state: Mock, mock_get_leading_object: Mock, mock_propagate: Mock, mock_trajectory: Mock) -> None:
        """Test _get_planned_trajectory"""
        with patch.object(self.planner, '_ego_path_linestring') as _ego_path_linestring:
            _ego_path_linestring.project = call()
            mock_idm_state_to_ego_state.return_value = Mock()
            mock_get_leading_object.return_value = Mock()
            self.planner._get_planned_trajectory(MagicMock(), MagicMock(), MagicMock())
            _ego_path_linestring.project.assert_called_once()
            mock_idm_state_to_ego_state.assert_called()
            mock_get_leading_object.assert_called()
            mock_propagate.assert_called()
            mock_trajectory.assert_called_once()

    def test__idm_state_to_ego_state_error(self) -> None:
        """Test raise if _ego_path has not been initialized"""
        with self.assertRaises(AssertionError):
            self.planner._idm_state_to_ego_state(Mock(), Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.EgoState.build_from_center')
    @patch(f'{TEST_FILE_PATH}.max')
    @patch(f'{TEST_FILE_PATH}.min')
    def test__idm_state_to_ego_state(self, mock_max: Mock, mock_min: Mock, mock_build_from_center: Mock) -> None:
        """Test _idm_state_to_ego_state"""
        with patch.object(self.planner, '_ego_path') as _ego_path:
            mock_new_center = MagicMock(autospec=True)
            mock_ego_idm_state = IDMAgentState(0, 1)
            mock_time_point = Mock()
            mock_vehicle_params = Mock()
            _ego_path.get_state_at_progress = Mock(return_value=mock_new_center)
            self.planner._idm_state_to_ego_state(mock_ego_idm_state, mock_time_point, mock_vehicle_params)
            mock_max.assert_called_once()
            mock_min.assert_called_once()
            mock_build_from_center.assert_called_with(center=StateSE2(mock_new_center.x, mock_new_center.y, mock_new_center.heading), center_velocity_2d=StateVector2D(mock_ego_idm_state.velocity, 0), center_acceleration_2d=StateVector2D(0, 0), tire_steering_angle=0.0, time_point=mock_time_point, vehicle_parameters=mock_vehicle_params)

    def test__annotate_occupancy_map_error(self) -> None:
        """Test raise if _map_api or _candidate_lane_edge_ids has not been initialized"""
        with self.assertRaises(AssertionError):
            with patch.object(self.planner, '_map_api'):
                self.planner._annotate_occupancy_map(Mock(), Mock())
        with self.assertRaises(AssertionError):
            with patch.object(self.planner, '_candidate_lane_edge_ids'):
                self.planner._annotate_occupancy_map(Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.trim_path')
    @patch(f'{TEST_FILE_PATH}.unary_union')
    @patch(f'{TEST_FILE_PATH}.path_to_linestring')
    def test__get_expanded_ego_path(self, mock_path_to_linestring: MagicMock, mock_unary_union: Mock, mock_trim_path: Mock) -> None:
        """Test _get_expanded_ego_path"""
        mock_ego_idm_state = IDMAgentState(0, 1)
        mock_ego_state = MagicMock(spec_set=EgoState)
        mock_trim_path.return_value = Mock()
        with patch.object(self.planner, '_ego_path') as _ego_path:
            _ego_path.get_start_progress = Mock(return_value=0)
            _ego_path.get_end_progress = Mock(return_value=10)
            self.planner._get_expanded_ego_path(mock_ego_state, mock_ego_idm_state)
            mock_trim_path.assert_called_once()
            mock_path_to_linestring.assert_called_once_with(mock_trim_path.return_value)
            mock_unary_union.assert_called_once()

    @patch(f'{TEST_FILE_PATH}.transform')
    @patch(f'{TEST_FILE_PATH}.principal_value')
    def test__get_leading_idm_agent(self, mock_principal_value: Mock, mock_transform: Mock) -> None:
        """Test _get_leading_idm_agent when an Agent object is passed"""
        mock_agent = MagicMock(spec_set=Agent)
        mock_transform.return_value = StateSE2(1, 0, 0)
        mock_relative_distance = 2
        result = self.planner._get_leading_idm_agent(MagicMock(spec_set=EgoState), mock_agent, mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(mock_transform.return_value.x, result.velocity)
        self.assertEqual(0.0, result.length_rear)
        mock_principal_value.assert_called_once()
        mock_transform.assert_called_once()

    def test__get_leading_idm_agent_static(self) -> None:
        """Test _get_leading_idm_agent when a Staic object is passed"""
        mock_relative_distance = 2
        result = self.planner._get_leading_idm_agent(Mock(spec_set=EgoState), Mock(), mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(0.0, result.velocity)
        self.assertEqual(0.0, result.length_rear)

    def test__get_free_road_leading_idm_state(self) -> None:
        """Test _get_free_road_leading_idm_state"""
        mock_ego_idm_state = IDMAgentState(0, 1)
        mock_ego_state = self.scenario.initial_ego_state
        with patch.object(self.planner, '_ego_path', spec_set=AbstractPath) as _ego_path:
            _ego_path.get_start_progress = Mock(return_value=0)
            _ego_path.get_end_progress = Mock(return_value=10)
            result = self.planner._get_free_road_leading_idm_state(mock_ego_state, mock_ego_idm_state)
            self.assertEqual(_ego_path.get_end_progress() - mock_ego_idm_state.progress, result.progress)
            self.assertEqual(0.0, result.velocity)
            self.assertEqual(mock_ego_state.car_footprint.length / 2, result.length_rear)

    def test__get_red_light_leading_idm_state(self) -> None:
        """Test _get_red_light_leading_idm_state"""
        mock_relative_distance = 2
        result = self.planner._get_red_light_leading_idm_state(mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(0.0, result.velocity)
        self.assertEqual(0.0, result.length_rear)

    def test__get_leading_object(self) -> None:
        """Test _get_leading_object"""
        mock_occupancy_map = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents.size = 1
        mock_intersecting_agents.get_nearest_entry_to = Mock(return_value=('red_light', Mock(), 0.0))
        mock_occupancy_map.intersects = Mock(return_value=mock_intersecting_agents)
        with patch.object(self.planner, '_get_red_light_leading_idm_state') as mock_handle_traffic_light:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, Mock())
                mock_handle_traffic_light.assert_called_once_with(0.0)
                mock_get_expanded_ego_path.assert_called_once()
        mock_intersecting_agents.get_nearest_entry_to = Mock(return_value=('', Mock(), 0.0))
        with patch.object(self.planner, '_get_leading_idm_agent') as mock_handle_tracks:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, MagicMock())
                mock_handle_tracks.assert_called_once()
                mock_get_expanded_ego_path.assert_called_once()

    def test__get_leading_object_free_road(self) -> None:
        """Test _get_leading_object in the case where there are no leading agents"""
        mock_occupancy_map = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents.size = 0
        mock_occupancy_map.intersects = Mock(return_value=mock_intersecting_agents)
        with patch.object(self.planner, '_get_free_road_leading_idm_state') as mock_handle_free_road_case:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, Mock())
                mock_handle_free_road_case.assert_called_once()
                mock_get_expanded_ego_path.assert_called_once()

def test__initialize_route_plan_assertion_error(self) -> None:
    """Test raise if _map_api is uninitialized"""
    with self.assertRaises(AssertionError):
        self.planner._initialize_route_plan([])

class TestAbstractIDMPlanner(unittest.TestCase):
    """Test the AbstractIDMPlanner interface"""
    TEST_FILE_PATH = 'nuplan.planning.simulation.planner.idm_planner'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.scenario = get_test_nuplan_scenario()
        self.planned_trajectory_samples = 10
        self.planner = IDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

    def test_name(self) -> None:
        """Test name"""
        self.assertEqual(self.planner.name(), 'IDMPlanner')

    def test_observation_type(self) -> None:
        """Test observation_type"""
        self.assertEqual(self.planner.observation_type(), DetectionsTracks)

    def test__initialize_route_plan_assertion_error(self) -> None:
        """Test raise if _map_api is uninitialized"""
        with self.assertRaises(AssertionError):
            self.planner._initialize_route_plan([])

    @patch(f'{TEST_FILE_PATH}.IDMPlanner._initialize_route_plan')
    def test_initialize(self, mock_initialize_route_plan: Mock) -> None:
        """Test initialize"""
        initialization = MagicMock()
        self.planner.initialize(initialization)
        mock_initialize_route_plan.assert_called_once_with(initialization.route_roadblock_ids)

    @patch(f'{TEST_FILE_PATH}.path_to_linestring')
    @patch(f'{TEST_FILE_PATH}.create_path_from_se2')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._breadth_first_search')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._get_starting_edge')
    def test__initialize_ego_path(self, mock_get_starting_edge: Mock, mock_breadth_first_search: Mock, mock_create_path_from_se2: Mock, mock_path_to_linestring: Mock) -> None:
        """Test _initialize_ego_path()"""
        mock_starting_edge = Mock()
        mock_lane = MagicMock()
        mock_lane.speed_limit_mps = 0
        ego_state = self.scenario.initial_ego_state
        mock_breadth_first_search.return_value = ([mock_lane], True)
        mock_get_starting_edge.return_value = mock_starting_edge
        with patch.object(self.planner, '_route_roadblocks'):
            self.planner._initialize_ego_path(ego_state)
            mock_breadth_first_search.assert_called_once_with(ego_state)
            mock_create_path_from_se2.assert_called_once_with([])
            mock_path_to_linestring.assert_called_once_with([])

    def test__get_starting_edge(self) -> None:
        """Test _get_starting_edge()"""
        mock_edge = MagicMock(spec_set=LaneGraphEdgeMapObject)
        mock_edge.contains_point.side_effect = [False, True]
        mock_edge.polygon.distance.side_effect = [0, 0]
        mock_roadblock = MagicMock(spec_set=RoadBlockGraphEdgeMapObject)
        mock_roadblock.interior_edges = [mock_edge]
        self.planner._route_roadblocks = [mock_roadblock, mock_roadblock]
        result = self.planner._get_starting_edge(Mock(spec=EgoState))
        mock_edge.contains_point.assert_called()
        mock_edge.polygon.distance.assert_called()
        self.assertEqual(result, mock_edge)

    @patch(f'{TEST_FILE_PATH}.IDMPlanner._initialize_ego_path')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._construct_occupancy_map')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._annotate_occupancy_map')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._get_planned_trajectory')
    def test_compute_trajectory(self, mock_get_planned_trajectory: Mock, mock_annotate_occupancy_map: Mock, mock_construct_occupancy_map: Mock, mock_initialize_ego_path: Mock) -> None:
        """Test compute_trajectory"""
        planner_input = MagicMock()
        mock_ego_state = Mock()
        mock_traffic_light_data = call()
        planner_input.history.current_state = (mock_ego_state, Mock())
        planner_input.traffic_light_data = mock_traffic_light_data
        mock_occupancy_map = Mock()
        mock_unique_observations = Mock()
        mock_construct_occupancy_map.return_value = (mock_occupancy_map, mock_unique_observations)
        self.planner.compute_trajectory(planner_input)
        mock_initialize_ego_path.assert_called_once_with(mock_ego_state)
        mock_construct_occupancy_map.assert_called_once_with(*planner_input.history.current_state)
        mock_annotate_occupancy_map.assert_called_once_with(mock_traffic_light_data, mock_occupancy_map)
        mock_get_planned_trajectory.assert_called_once_with(mock_ego_state, mock_occupancy_map, mock_unique_observations)

    def test_compute_trajectory_integration(self) -> None:
        """Test the IDMPlanner in full using mock data"""
        history_buffer = SimulationHistoryBuffer.initialize_from_scenario(10, self.scenario, DetectionsTracks)
        self.planner.initialize(PlannerInitialization(self.scenario.get_route_roadblock_ids(), self.scenario.get_mission_goal(), self.scenario.map_api))
        trajectories = self.planner.compute_trajectory(PlannerInput(SimulationIteration(self.scenario.get_time_point(0), 0), history_buffer, list(self.scenario.get_traffic_light_status_at_iteration(0))))
        self.assertEqual(self.planned_trajectory_samples + 1, len(trajectories.get_sampled_trajectory()))

def test__initialize_route_plan_assertion_error(self) -> None:
    """Test raise if _map_api is uninitialized"""
    with self.assertRaises(AssertionError):
        self.planner._initialize_route_plan([])

def test_compute_trajectory_integration(self) -> None:
    """Test the IDMPlanner in full using mock data"""
    history_buffer = SimulationHistoryBuffer.initialize_from_scenario(10, self.scenario, DetectionsTracks)
    self.planner.initialize(PlannerInitialization(self.scenario.get_route_roadblock_ids(), self.scenario.get_mission_goal(), self.scenario.map_api))
    trajectories = self.planner.compute_trajectory(PlannerInput(SimulationIteration(self.scenario.get_time_point(0), 0), history_buffer, list(self.scenario.get_traffic_light_status_at_iteration(0))))
    self.assertEqual(self.planned_trajectory_samples + 1, len(trajectories.get_sampled_trajectory()))

class TestLogFuturePlanner(unittest.TestCase):
    """
    Test LogFuturePlanner class
    """

    def _get_mock_planner_input(self) -> PlannerInput:
        """
        Returns a mock PlannerInput for testing.
        :return: PlannerInput.
        """
        buffer = SimulationHistoryBuffer.initialize_from_list(1, [self.scenario.initial_ego_state], [self.scenario.initial_tracked_objects])
        return PlannerInput(iteration=SimulationIteration(TimePoint(0), 0), history=buffer, traffic_light_data=None)

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.scenario = MockAbstractScenario(number_of_future_iterations=20)
        self.num_poses = 10
        self.future_time_horizon = 5
        self.planner = LogFuturePlanner(self.scenario, self.num_poses, self.future_time_horizon)

    def test_name(self) -> None:
        """Tests planner name is set correctly."""
        result = self.planner.name()
        self.assertEqual(result, 'LogFuturePlanner')

    @patch('nuplan.planning.simulation.planner.log_future_planner.DetectionsTracks')
    def test_observation_type(self, mock_detection_tracks: Mock) -> None:
        """Tests observation type is set correctly."""
        result = self.planner.observation_type()
        self.assertEqual(result, mock_detection_tracks)

    def test_compute_trajectory(self) -> None:
        """Test compute_trajectory"""
        planner_input = self._get_mock_planner_input()
        start_time = time.perf_counter()
        result = self.planner.compute_trajectory(planner_input)
        compute_trajectory_time = time.perf_counter() - start_time
        self.assertEqual(len(result.get_sampled_trajectory()), self.num_poses + 1)
        planner_report = self.planner.generate_planner_report()
        self.assertEqual(len(planner_report.compute_trajectory_runtimes), 1)
        self.assertNotIsInstance(planner_report, MLPlannerReport)
        self.assertAlmostEqual(planner_report.compute_trajectory_runtimes[0], compute_trajectory_time, delta=0.1)

    def test_compute_trajectory_fail_extraction_previous_available(self) -> None:
        """
        Test compute_trajectory when future ego extraction from scenario fails and planner should fall back on previous
        trajectory.
        """
        previous_trajectory = Mock()
        self.planner._trajectory = previous_trajectory
        planner_input = self._get_mock_planner_input()
        with patch.object(self.scenario, 'get_ego_future_trajectory', side_effect=AssertionError):
            result = self.planner.compute_trajectory(planner_input)
        self.assertEqual(result, previous_trajectory)

    def test_compute_trajectory_fail_extraction_no_previous(self) -> None:
        """
        Test compute_trajectory when future ego extraction from scenario fails and there is no prior trajectory
        to fall back on.
        """
        self.planner._trajectory = None
        planner_input = self._get_mock_planner_input()
        with patch.object(self.scenario, 'get_ego_future_trajectory', side_effect=AssertionError):
            with self.assertRaises(RuntimeError):
                _ = self.planner.compute_trajectory(planner_input)

def _get_mock_planner_input(self) -> PlannerInput:
    """
        Returns a mock PlannerInput for testing.
        :return: PlannerInput.
        """
    buffer = SimulationHistoryBuffer.initialize_from_list(1, [self.scenario.initial_ego_state], [self.scenario.initial_tracked_objects])
    return PlannerInput(iteration=SimulationIteration(TimePoint(0), 0), history=buffer, traffic_light_data=None)

class MLPlanner(AbstractPlanner):
    """
    Implements abstract planner interface.
    Used for simulating any ML planner trained through the nuPlan training framework.
    """

    def __init__(self, model: TorchModuleWrapper) -> None:
        """
        Initializes the ML planner class.
        :param model: Model to use for inference.
        """
        self._future_horizon = model.future_trajectory_sampling.time_horizon
        self._step_interval = model.future_trajectory_sampling.step_time
        self._num_output_dim = model.future_trajectory_sampling.num_poses
        self._model_loader = ModelLoader(model)
        self._initialization: Optional[PlannerInitialization] = None
        self._feature_building_runtimes: List[float] = []
        self._inference_runtimes: List[float] = []

    def _infer_model(self, features: FeaturesType) -> npt.NDArray[np.float32]:
        """
        Makes a single inference on a Pytorch/Torchscript model.

        :param features: dictionary of feature types
        :return: predicted trajectory poses as a numpy array
        """
        predictions = self._model_loader.infer(features)
        trajectory_predicted = cast(Trajectory, predictions['trajectory'])
        trajectory_tensor = trajectory_predicted.data
        trajectory = trajectory_tensor.cpu().detach().numpy()[0]
        return cast(npt.NDArray[np.float32], trajectory)

    def initialize(self, initialization: PlannerInitialization) -> None:
        """Inherited, see superclass."""
        self._model_loader.initialize()
        self._initialization = initialization

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Infer relative trajectory poses from model and convert to absolute agent states wrapped in a trajectory.
        Inherited, see superclass.
        """
        history = current_input.history
        start_time = time.perf_counter()
        features = self._model_loader.build_features(current_input, self._initialization)
        self._feature_building_runtimes.append(time.perf_counter() - start_time)
        start_time = time.perf_counter()
        predictions = self._infer_model(features)
        self._inference_runtimes.append(time.perf_counter() - start_time)
        states = transform_predictions_to_states(predictions, history.ego_states, self._future_horizon, self._step_interval)
        trajectory = InterpolatedTrajectory(states)
        return trajectory

    def generate_planner_report(self, clear_stats: bool=True) -> PlannerReport:
        """Inherited, see superclass."""
        report = MLPlannerReport(compute_trajectory_runtimes=self._compute_trajectory_runtimes, feature_building_runtimes=self._feature_building_runtimes, inference_runtimes=self._inference_runtimes)
        if clear_stats:
            self._compute_trajectory_runtimes: List[float] = []
            self._feature_building_runtimes = []
            self._inference_runtimes = []
        return report

def initialize(self, initialization: PlannerInitialization) -> None:
    """Inherited, see superclass."""
    self._model_loader.initialize()
    self._initialization = initialization

def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
    """
        Infer relative trajectory poses from model and convert to absolute agent states wrapped in a trajectory.
        Inherited, see superclass.
        """
    history = current_input.history
    start_time = time.perf_counter()
    features = self._model_loader.build_features(current_input, self._initialization)
    self._feature_building_runtimes.append(time.perf_counter() - start_time)
    start_time = time.perf_counter()
    predictions = self._infer_model(features)
    self._inference_runtimes.append(time.perf_counter() - start_time)
    states = transform_predictions_to_states(predictions, history.ego_states, self._future_horizon, self._step_interval)
    trajectory = InterpolatedTrajectory(states)
    return trajectory

class ModelLoader:
    """
    A class to load in an NNModel and prepare pytorch for inference.
    Used for simulating ML planners and smart agents throughout the nuPlan training framework.
    """

    def __init__(self, model: TorchModuleWrapper) -> None:
        """
        Initializes the ModelLoader class.
        :param model: Model to use for inference.
        """
        self.feature_builders = model.get_list_of_required_feature()
        self._model = model
        self._initialized = False

    def _initialize_torch(self) -> None:
        """
        Sets up torch/torchscript for inference.
        """
        torch.set_grad_enabled(False)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def _initialize_model(self) -> None:
        """
        Sets up the model.
        """
        self._model.eval()
        self._model = self._model.to(self.device)

    def initialize(self) -> None:
        """
        Initializes the ModelLoader
        """
        self._initialize_torch()
        self._initialize_model()
        self._initialized = True

    def build_features(self, current_input: PlannerInput, initialization: PlannerInitialization) -> FeaturesType:
        """
        Makes a single inference on a Pytorch/Torchscript model.
        :param current_input: Iteration specific inputs for building the feature.
        :param initialization: Additional data require for building the feature.
        :return: dictionary of FeaturesType types.
        """
        assert self._initialized, 'The model loader has not been initialized!'
        features = {builder.get_feature_unique_name(): builder.get_features_from_simulation(current_input, initialization) for builder in self.feature_builders}
        features = {name: feature.to_feature_tensor() for name, feature in features.items()}
        features = {name: feature.to_device(self.device) for name, feature in features.items()}
        features = {name: feature.collate([feature]) for name, feature in features.items()}
        return features

    def infer(self, features: FeaturesType) -> TargetsType:
        """
        Makes a single inference on a Pytorch/Torchscript model.

        :param features: dictionary of feature types
        :return: dictionary of target types
        """
        assert self._initialized is True, 'The model loader has not been initialized!'
        return self._model.forward(features)

def build_features(self, current_input: PlannerInput, initialization: PlannerInitialization) -> FeaturesType:
    """
        Makes a single inference on a Pytorch/Torchscript model.
        :param current_input: Iteration specific inputs for building the feature.
        :param initialization: Additional data require for building the feature.
        :return: dictionary of FeaturesType types.
        """
    assert self._initialized, 'The model loader has not been initialized!'
    features = {builder.get_feature_unique_name(): builder.get_features_from_simulation(current_input, initialization) for builder in self.feature_builders}
    features = {name: feature.to_feature_tensor() for name, feature in features.items()}
    features = {name: feature.to_device(self.device) for name, feature in features.items()}
    features = {name: feature.collate([feature]) for name, feature in features.items()}
    return features

class TestMlPlanner(unittest.TestCase):
    """
    Test MLPlanner with two models.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.scenario = get_test_nuplan_scenario()

    def test_simple_vector_net_model(self) -> None:
        """Test Model Vector Map Simple"""
        self.run_test_ml_planner(construct_simple_vector_map_ml_planner())

    def test_raster_net_model(self) -> None:
        """Test Raster Net model"""
        self.run_test_ml_planner(construct_raster_ml_planner())

    def test_urban_driver_open_loop_model(self) -> None:
        """Test UrbanDriverOpenLoop model"""
        self.run_test_ml_planner(construct_urban_driver_open_loop_ml_planner())

    def run_test_ml_planner(self, planner: MLPlanner) -> None:
        """Tests if progress is calculated correctly"""
        scenario = self.scenario
        simulation_history_buffer_duration = 2
        buffer_size = int(simulation_history_buffer_duration / self.scenario.database_interval + 1)
        history = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=buffer_size, scenario=self.scenario, observation_type=DetectionsTracks)
        initialization = PlannerInitialization(route_roadblock_ids=scenario.get_route_roadblock_ids(), mission_goal=scenario.get_mission_goal(), map_api=scenario.map_api)
        planner.initialize(initialization)
        trajectory = planner.compute_trajectory(PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=list(scenario.get_traffic_light_status_at_iteration(0))))
        self.assertNotEqual(trajectory, None)
        self.assertEqual(len(trajectory.get_sampled_trajectory()), planner._num_output_dim + 1)

def run_test_ml_planner(self, planner: MLPlanner) -> None:
    """Tests if progress is calculated correctly"""
    scenario = self.scenario
    simulation_history_buffer_duration = 2
    buffer_size = int(simulation_history_buffer_duration / self.scenario.database_interval + 1)
    history = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=buffer_size, scenario=self.scenario, observation_type=DetectionsTracks)
    initialization = PlannerInitialization(route_roadblock_ids=scenario.get_route_roadblock_ids(), mission_goal=scenario.get_mission_goal(), map_api=scenario.map_api)
    planner.initialize(initialization)
    trajectory = planner.compute_trajectory(PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=list(scenario.get_traffic_light_status_at_iteration(0))))
    self.assertNotEqual(trajectory, None)
    self.assertEqual(len(trajectory.get_sampled_trajectory()), planner._num_output_dim + 1)

class TracksObservation(AbstractObservation):
    """
    Replay detections from samples.
    """

    def __init__(self, scenario: AbstractScenario):
        """
        :param scenario: The scenario
        """
        self.scenario = scenario
        self.current_iteration = 0

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_iteration = 0

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def initialize(self) -> None:
        """Inherited, see superclass."""
        pass

    def get_observation(self) -> DetectionsTracks:
        """Inherited, see superclass."""
        return self.scenario.get_tracked_objects_at_iteration(self.current_iteration)

    def update_observation(self, iteration: SimulationIteration, next_iteration: SimulationIteration, history: SimulationHistoryBuffer) -> None:
        """Inherited, see superclass."""
        self.current_iteration = next_iteration.index

def get_observation(self) -> DetectionsTracks:
    """Inherited, see superclass."""
    return self.scenario.get_tracked_objects_at_iteration(self.current_iteration)

class AbstractMLAgents(AbstractObservation):
    """
    Simulate agents based on an ML model.
    """

    def __init__(self, model: TorchModuleWrapper, scenario: AbstractScenario) -> None:
        """
        Initializes the AbstractEgoCentricMLAgents class.
        :param model: Model to use for inference.
        :param scenario: scenario
        """
        self._model_loader = ModelLoader(model)
        self._future_horizon = model.future_trajectory_sampling.time_horizon
        self._step_interval_us = model.future_trajectory_sampling.step_time * 1000000.0
        self._num_output_dim = model.future_trajectory_sampling.num_poses
        self._scenario = scenario
        self._ego_anchor_state = scenario.initial_ego_state
        self.step_time = None
        self._agents: Optional[Dict[str, TrackedObject]] = None

    @abstractmethod
    def _infer_model(self, features: FeaturesType) -> TargetsType:
        """
        Makes a single inference on a Pytorch/Torchscript model.
        :param features: dictionary of feature types
        :return: predicted trajectory poses as a numpy array
        """
        pass

    @abstractmethod
    def _update_observation_with_predictions(self, agent_predictions: TargetsType) -> None:
        """
        Update smart agent using the predictions from the ML model
        :param agent_predictions: The prediction output from the ML_model
        """
        pass

    def _initialize_agents(self) -> None:
        """
        Initializes the agents based on the first step of the scenario
        """
        unique_agents = {tracked_object.track_token: tracked_object for tracked_object in self._scenario.initial_tracked_objects.tracked_objects if tracked_object.tracked_object_type == TrackedObjectType.VEHICLE}
        self._agents = sort_dict(unique_agents)

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def reset(self) -> None:
        """Inherited, see superclass."""
        self._initialize_agents()

    def initialize(self) -> None:
        """Inherited, see superclass."""
        self._initialize_agents()
        self._model_loader.initialize()

    def update_observation(self, iteration: SimulationIteration, next_iteration: SimulationIteration, history: SimulationHistoryBuffer) -> None:
        """Inherited, see superclass."""
        self.step_time = next_iteration.time_point - iteration.time_point
        self._ego_anchor_state, _ = history.current_state
        initialization = PlannerInitialization(mission_goal=self._scenario.get_mission_goal(), route_roadblock_ids=self._scenario.get_route_roadblock_ids(), map_api=self._scenario.map_api)
        traffic_light_data = self._scenario.get_traffic_light_status_at_iteration(next_iteration.index)
        current_input = PlannerInput(next_iteration, history, traffic_light_data)
        features = self._model_loader.build_features(current_input, initialization)
        predictions = self._infer_model(features)
        self._update_observation_with_predictions(predictions)

    def get_observation(self) -> DetectionsTracks:
        """Inherited, see superclass."""
        assert self._agents, 'ML agent observation has not been initialized!Please make sure initialize() is called before getting the observation.'
        return DetectionsTracks(TrackedObjects(list(self._agents.values())))

def reset(self) -> None:
    """Inherited, see superclass."""
    self._initialize_agents()

def initialize(self) -> None:
    """Inherited, see superclass."""
    self._initialize_agents()
    self._model_loader.initialize()

def update_observation(self, iteration: SimulationIteration, next_iteration: SimulationIteration, history: SimulationHistoryBuffer) -> None:
    """Inherited, see superclass."""
    self.step_time = next_iteration.time_point - iteration.time_point
    self._ego_anchor_state, _ = history.current_state
    initialization = PlannerInitialization(mission_goal=self._scenario.get_mission_goal(), route_roadblock_ids=self._scenario.get_route_roadblock_ids(), map_api=self._scenario.map_api)
    traffic_light_data = self._scenario.get_traffic_light_status_at_iteration(next_iteration.index)
    current_input = PlannerInput(next_iteration, history, traffic_light_data)
    features = self._model_loader.build_features(current_input, initialization)
    predictions = self._infer_model(features)
    self._update_observation_with_predictions(predictions)

class LidarPcObservation(AbstractObservation):
    """
    Replay lidar pointclouds from the scenario.
    """

    def __init__(self, scenario: AbstractScenario):
        """
        Constructor for LidarPcObservation.
        :param scenario: to get observations from.
        """
        self.scenario = scenario
        self.current_iteration = 0

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_iteration = 0

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return Sensors

    def initialize(self) -> None:
        """Inherited, see superclass."""
        pass

    def get_observation(self) -> Sensors:
        """Inherited, see superclass."""
        return self.scenario.get_sensors_at_iteration(self.current_iteration)

    def update_observation(self, iteration: SimulationIteration, next_iteration: SimulationIteration, history: SimulationHistoryBuffer) -> None:
        """Inherited, see superclass."""
        self.current_iteration = next_iteration.index

def get_observation(self) -> Sensors:
    """Inherited, see superclass."""
    return self.scenario.get_sensors_at_iteration(self.current_iteration)

class TestEgoCentricMLAgents(unittest.TestCase):
    """Test important functions of EgoCentricMLAgents class"""

    def setUp(self) -> None:
        """Initialize scenario and model for constructing AgentCentricMLAgents class."""
        self.scenario = MockAbstractScenario(number_of_detections=1)
        self.model = Mock(spec=TorchModuleWrapper)
        self.model.future_trajectory_sampling = TrajectorySampling(num_poses=1, time_horizon=1.0)
        self.pred_trajectory = AgentsTrajectories(data=[np.array([[[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]]])])

    def test_update_observation_with_predictions(self) -> None:
        """Test the _update_observation_with_predictions fucntion."""
        obs = EgoCentricMLAgents(model=self.model, scenario=self.scenario)
        obs.initialize()
        self.assertEqual(len(obs._agents), 1)
        self.assertEqual(obs._agents['0'].center.x, 1.0)
        self.assertEqual(obs._agents['0'].center.y, 2.0)
        self.assertAlmostEqual(obs._agents['0'].center.heading, np.pi / 2)
        obs.step_time = TimePoint(1000000.0)
        predictions = {'agents_trajectory': self.pred_trajectory}
        obs._update_observation_with_predictions(predictions)
        self.assertEqual(len(obs._agents), 1)
        self.assertAlmostEqual(obs._agents['0'].center.x, 1.0)
        self.assertAlmostEqual(obs._agents['0'].center.y, 1.0)
        self.assertAlmostEqual(obs._agents['0'].center.heading, 0.0)

    @patch('nuplan.planning.simulation.planner.ml_planner.model_loader.ModelLoader.infer')
    def test_infer_model(self, mock_infer: Mock) -> None:
        """Test _infer_model function."""
        predictions = {'agents_trajectory': self.pred_trajectory.to_feature_tensor()}
        mock_infer.return_value = predictions
        obs = EgoCentricMLAgents(model=self.model, scenario=self.scenario)
        obs.initialize()
        agents_raster = Mock(spec=Agents)
        features = {'agents': agents_raster}
        results = obs._infer_model(features)
        mock_infer.assert_called_with(features)
        self.assertIn(obs.prediction_type, results)
        self.assertIsInstance(results[obs.prediction_type], AgentsTrajectories)
        self.assertIsInstance(results[obs.prediction_type].data[0], np.ndarray)

def test_update_observation_with_predictions(self) -> None:
    """Test the _update_observation_with_predictions fucntion."""
    obs = EgoCentricMLAgents(model=self.model, scenario=self.scenario)
    obs.initialize()
    self.assertEqual(len(obs._agents), 1)
    self.assertEqual(obs._agents['0'].center.x, 1.0)
    self.assertEqual(obs._agents['0'].center.y, 2.0)
    self.assertAlmostEqual(obs._agents['0'].center.heading, np.pi / 2)
    obs.step_time = TimePoint(1000000.0)
    predictions = {'agents_trajectory': self.pred_trajectory}
    obs._update_observation_with_predictions(predictions)
    self.assertEqual(len(obs._agents), 1)
    self.assertAlmostEqual(obs._agents['0'].center.x, 1.0)
    self.assertAlmostEqual(obs._agents['0'].center.y, 1.0)
    self.assertAlmostEqual(obs._agents['0'].center.heading, 0.0)

class TestProfileIDM(unittest.TestCase):
    """
    Profiling test for IDM agents.
    """

    def setUp(self) -> None:
        """
        Inherited, see super class.
        """
        self.n_repeat_trials = 1
        self.display_results = True
        self.scenario = get_test_nuplan_scenario()

    def test_profile_idm_agent_observation(self) -> None:
        """Profile IDMAgents."""
        profiler = Profiler(interval=0.0001)
        profiler.start()
        for _ in range(self.n_repeat_trials):
            observation = IDMAgents(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, scenario=self.scenario, open_loop_detections_types=[])
            for step in range(self.scenario.get_number_of_iterations() - 1):
                iteration = SimulationIteration(time_point=self.scenario.get_time_point(step), index=step)
                next_iteration = SimulationIteration(time_point=self.scenario.get_time_point(step + 1), index=step + 1)
                buffer = SimulationHistoryBuffer.initialize_from_list(1, [self.scenario.get_ego_state_at_iteration(step)], [self.scenario.get_tracked_objects_at_iteration(step)], next_iteration.time_point.time_s - iteration.time_point.time_s)
                observation.update_observation(iteration, next_iteration, buffer)
        profiler.stop()
        if self.display_results:
            logger.info(profiler.output_text(unicode=True, color=True))

def test_profile_idm_agent_observation(self) -> None:
    """Profile IDMAgents."""
    profiler = Profiler(interval=0.0001)
    profiler.start()
    for _ in range(self.n_repeat_trials):
        observation = IDMAgents(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, scenario=self.scenario, open_loop_detections_types=[])
        for step in range(self.scenario.get_number_of_iterations() - 1):
            iteration = SimulationIteration(time_point=self.scenario.get_time_point(step), index=step)
            next_iteration = SimulationIteration(time_point=self.scenario.get_time_point(step + 1), index=step + 1)
            buffer = SimulationHistoryBuffer.initialize_from_list(1, [self.scenario.get_ego_state_at_iteration(step)], [self.scenario.get_tracked_objects_at_iteration(step)], next_iteration.time_point.time_s - iteration.time_point.time_s)
            observation.update_observation(iteration, next_iteration, buffer)
    profiler.stop()
    if self.display_results:
        logger.info(profiler.output_text(unicode=True, color=True))

@nuplan_test(path='json/idm_agent_observation/baseline.json')
def test_idm_observations(scene: Dict[str, Any]) -> None:
    """
    Overall integration test of IDM smart agents
    """
    simulation_step = 17
    observation = IDMAgents(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, scenario=scenario, open_loop_detections_types=[])
    agent_history: Dict[str, List[StateSE2]] = dict()
    for step in range(simulation_step):
        iteration = SimulationIteration(time_point=scenario.get_time_point(step), index=step)
        next_iteration = SimulationIteration(time_point=scenario.get_time_point(step + 1), index=step + 1)
        buffer = SimulationHistoryBuffer.initialize_from_list(1, [scenario.get_ego_state_at_iteration(step)], [scenario.get_tracked_objects_at_iteration(step)], sample_interval=next_iteration.time_point.time_s - iteration.time_point.time_s)
        observation.update_observation(iteration, next_iteration, buffer)
        for agent_id, agent in observation._idm_agent_manager.agents.items():
            if agent_id not in agent_history:
                agent_history[agent_id] = []
            agent_history[agent_id].append(agent.to_se2())

class SimulationHistoryBuffer:
    """
    This class is used to keep a rolling buffer of a given size. The buffer is a first-in first-out queue. Hence, the
    oldest samples in the buffer are continuously replaced as new samples are appended.
    """

    def __init__(self, ego_state_buffer: Deque[EgoState], observations_buffer: Deque[Observation], sample_interval: Optional[float]=None):
        """
        Constructs a SimulationHistoryBuffer
        :param ego_state_buffer: Past ego state trajectory including the state.
            at the current time step [t_-N, ..., t_-1, t_0]
        :param observations_buffer: Past observations including the observation.
            at the current time step [t_-N, ..., t_-1, t_0].
        :param sample_interval: [s] the time interval between each sample, if given
        """
        if not ego_state_buffer or not observations_buffer:
            raise ValueError('Ego and observation buffers cannot be empty!')
        if len(ego_state_buffer) != len(observations_buffer):
            raise ValueError(f'Ego and observations buffer is not the same length {len(ego_state_buffer) != len(observations_buffer)}!')
        self._ego_state_buffer = ego_state_buffer
        self._observations_buffer = observations_buffer
        self._sample_interval = sample_interval

    @property
    def ego_state_buffer(self) -> Deque[EgoState]:
        """
        :return: current ego state buffer
        """
        return self._ego_state_buffer

    @property
    def observation_buffer(self) -> Deque[Observation]:
        """
        :return: current observation buffer
        """
        return self._observations_buffer

    @property
    def size(self) -> int:
        """
        :return: Size of the buffer.
        """
        return len(self.ego_states)

    @property
    def duration(self) -> Optional[float]:
        """
        :return: [s] Duration of the buffer.
        """
        return self.sample_interval * self.size if self.sample_interval else None

    @property
    def current_state(self) -> Tuple[EgoState, Observation]:
        """
        :return: current state of AV vehicle and its observations
        """
        return (self.ego_states[-1], self.observations[-1])

    @property
    def sample_interval(self) -> Optional[float]:
        """
        :return: the sample interval
        """
        return self._sample_interval

    @sample_interval.setter
    def sample_interval(self, sample_interval: float) -> None:
        """
        Sets the sample interval of the buffer, raises if the sample interval was not None
        :param sample_interval: The sample interval of the buffer
        """
        assert self._sample_interval is None, "Can't overwrite a pre-existing sample-interval!"
        self._sample_interval = sample_interval

    @property
    def ego_states(self) -> List[EgoState]:
        """
        :return: the ego state buffer in increasing temporal order where the last sample is the more recent sample
                 [t_-N, ..., t_-1, t_0]
        """
        return list(self._ego_state_buffer)

    @property
    def observations(self) -> List[Observation]:
        """
        :return: the observation buffer in increasing temporal order where the last sample is the more recent sample
                 [t_-N, ..., t_-1, t_0]
        """
        return list(self._observations_buffer)

    def append(self, ego_state: EgoState, observation: Observation) -> None:
        """
        Adds new samples to the buffers
        :param ego_state: an ego state
        :param observation: an observation
        """
        self._ego_state_buffer.append(ego_state)
        self._observations_buffer.append(observation)

    def extend(self, ego_states: List[EgoState], observations: List[Observation]) -> None:
        """
        Adds new samples to the buffers
        :param ego_states: an ego states list
        :param observations: an observations list
        """
        if len(ego_states) != len(observations):
            raise ValueError(f'Ego and observations are not the same length {len(ego_states) != len(observations)}!')
        self._ego_state_buffer.extend(ego_states)
        self._observations_buffer.extend(observations)

    def __len__(self) -> int:
        """
        :return: the length of the buffer
        @raise AssertionError if the length of each buffers are not the same
        """
        return len(self._ego_state_buffer)

    @classmethod
    def initialize_from_list(cls, buffer_size: int, ego_states: List[EgoState], observations: List[Observation], sample_interval: Optional[float]=None) -> SimulationHistoryBuffer:
        """
        Create history buffer from lists
        :param buffer_size: size of buffer
        :param ego_states: list of ego states
        :param observations: list of observations
        :param sample_interval: [s] the time interval between each sample, if given
        :return: SimulationHistoryBuffer
        """
        ego_state_buffer: Deque[EgoState] = deque(ego_states[-buffer_size:], maxlen=buffer_size)
        observations_buffer: Deque[Observation] = deque(observations[-buffer_size:], maxlen=buffer_size)
        return cls(ego_state_buffer=ego_state_buffer, observations_buffer=observations_buffer, sample_interval=sample_interval)

    @staticmethod
    def initialize_from_scenario(buffer_size: int, scenario: AbstractScenario, observation_type: Type[Observation]) -> SimulationHistoryBuffer:
        """
        Initializes ego_state_buffer and observations_buffer from scenario
        :param buffer_size: size of the buffer
        :param scenario: Simulation scenario
        :param observation_type: Observation type used for the simulation
        """
        buffer_duration = buffer_size * scenario.database_interval
        if observation_type == DetectionsTracks:
            observation_getter = scenario.get_past_tracked_objects
        elif observation_type == Sensors:
            observation_getter = scenario.get_past_sensors
        else:
            raise ValueError(f'No matching observation type for {observation_type} for history!')
        past_observation = list(observation_getter(iteration=0, time_horizon=buffer_duration, num_samples=buffer_size))
        past_ego_states = list(scenario.get_ego_past_trajectory(iteration=0, time_horizon=buffer_duration, num_samples=buffer_size))
        return SimulationHistoryBuffer.initialize_from_list(buffer_size=buffer_size, ego_states=past_ego_states, observations=past_observation, sample_interval=scenario.database_interval)

@staticmethod
def initialize_from_scenario(buffer_size: int, scenario: AbstractScenario, observation_type: Type[Observation]) -> SimulationHistoryBuffer:
    """
        Initializes ego_state_buffer and observations_buffer from scenario
        :param buffer_size: size of the buffer
        :param scenario: Simulation scenario
        :param observation_type: Observation type used for the simulation
        """
    buffer_duration = buffer_size * scenario.database_interval
    if observation_type == DetectionsTracks:
        observation_getter = scenario.get_past_tracked_objects
    elif observation_type == Sensors:
        observation_getter = scenario.get_past_sensors
    else:
        raise ValueError(f'No matching observation type for {observation_type} for history!')
    past_observation = list(observation_getter(iteration=0, time_horizon=buffer_duration, num_samples=buffer_size))
    past_ego_states = list(scenario.get_ego_past_trajectory(iteration=0, time_horizon=buffer_duration, num_samples=buffer_size))
    return SimulationHistoryBuffer.initialize_from_list(buffer_size=buffer_size, ego_states=past_ego_states, observations=past_observation, sample_interval=scenario.database_interval)

class TestSimulationHistoryBuffer(unittest.TestCase):
    """Test suite for SimulationHistoryBuffer"""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        self.scenario = MockAbstractScenario(number_of_past_iterations=20)
        self.buffer_size = 10

    def test_initialize_with_box(self) -> None:
        """Test the initialize function"""
        tracks_observation = TracksObservation(self.scenario)
        history_buffer = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=self.buffer_size, scenario=self.scenario, observation_type=tracks_observation.observation_type())
        self.assertEqual(len(history_buffer), self.buffer_size)

    def test_initialize_with_lidar_pc(self) -> None:
        """Test the initialize function"""
        lidar_pc_observation = LidarPcObservation(self.scenario)
        history_buffer = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=self.buffer_size, scenario=self.scenario, observation_type=lidar_pc_observation.observation_type())
        self.assertEqual(len(history_buffer), self.buffer_size)

    def test_initialize_from_list(self) -> None:
        """Test the initialization from lists"""
        history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=self.buffer_size, ego_states=[self.scenario.initial_ego_state], observations=[self.scenario.initial_tracked_objects], sample_interval=0.05)
        self.assertEqual(len(history_buffer), 1)
        self.assertEqual(history_buffer.ego_states, [self.scenario.initial_ego_state])
        self.assertEqual(history_buffer.observations, [self.scenario.initial_tracked_objects])

    def test_append(self) -> None:
        """Test the append function"""
        history_buffer = SimulationHistoryBuffer(ego_state_buffer=deque([Mock()], maxlen=1), observations_buffer=deque([Mock()], maxlen=1))
        history_buffer.append(self.scenario.initial_ego_state, self.scenario.initial_tracked_objects)
        self.assertEqual(len(history_buffer), 1)
        self.assertEqual(history_buffer.ego_states, [self.scenario.initial_ego_state])
        self.assertEqual(history_buffer.observations, [self.scenario.initial_tracked_objects])

    def test_extend(self) -> None:
        """Test the extend function"""
        history_buffer = SimulationHistoryBuffer(ego_state_buffer=deque([Mock()], maxlen=2), observations_buffer=deque([Mock()], maxlen=2))
        history_buffer.extend([self.scenario.initial_ego_state] * 2, [self.scenario.initial_tracked_objects] * 2)
        self.assertEqual(len(history_buffer), 2)
        self.assertEqual(history_buffer.ego_states, [self.scenario.initial_ego_state] * 2)
        self.assertEqual(history_buffer.observations, [self.scenario.initial_tracked_objects] * 2)

def test_initialize_with_lidar_pc(self) -> None:
    """Test the initialize function"""
    lidar_pc_observation = LidarPcObservation(self.scenario)
    history_buffer = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=self.buffer_size, scenario=self.scenario, observation_type=lidar_pc_observation.observation_type())
    self.assertEqual(len(history_buffer), self.buffer_size)

def test_initialize_from_list(self) -> None:
    """Test the initialization from lists"""
    history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=self.buffer_size, ego_states=[self.scenario.initial_ego_state], observations=[self.scenario.initial_tracked_objects], sample_interval=0.05)
    self.assertEqual(len(history_buffer), 1)
    self.assertEqual(history_buffer.ego_states, [self.scenario.initial_ego_state])
    self.assertEqual(history_buffer.observations, [self.scenario.initial_tracked_objects])

class TestInterpolatedPath(unittest.TestCase):
    """Tests implementation of InterpolatedPath."""

    def setUp(self) -> None:
        """Test setup."""
        self.path = [StateSE2(0, 0, 0), StateSE2(3, 4, 1), StateSE2(7, 7, 2), StateSE2(10, 10, 3)]
        self.interpolated_path = InterpolatedPath(convert_se2_path_to_progress_path(self.path))

    def test_get_start_progress(self) -> None:
        """Check start progress"""
        self.assertEqual(self.interpolated_path.get_start_progress(), self.interpolated_path.get_sampled_path()[0].progress)

    def test_get_end_progress(self) -> None:
        """Check end progress"""
        self.assertEqual(self.interpolated_path.get_end_progress(), self.interpolated_path.get_sampled_path()[-1].progress)

    def test_get_state_at_progress(self) -> None:
        """Check if the interpolated states are calculated correctly progress"""
        state = self.interpolated_path.get_state_at_progress(5)
        self.assertEqual(5, state.progress)
        self.assertEqual(3, state.x)
        self.assertEqual(4, state.y)
        self.assertEqual(1, state.heading)

    def test_get_state_at_progresses(self) -> None:
        """Check if the interpolated states are calculated correctly given a list of progresses."""
        states = self.interpolated_path.get_state_at_progresses([0, 5])
        self.assertEqual(0, states[0].progress)
        self.assertEqual(0, states[0].x)
        self.assertEqual(0, states[0].y)
        self.assertEqual(0, states[0].heading)
        self.assertEqual(5, states[1].progress)
        self.assertEqual(3, states[1].x)
        self.assertEqual(4, states[1].y)
        self.assertEqual(1, states[1].heading)

    def test_get_state_at_progress_expect_throw(self) -> None:
        """Check if assertion is raised for invalid calls"""
        self.assertRaises(AssertionError, self.interpolated_path.get_state_at_progress, 100)
        self.assertRaises(AssertionError, self.interpolated_path.get_state_at_progress, -1)

    def test_get_sampled_path(self) -> None:
        """Test if the sampled path is the same as the one originally given"""
        sample_path = self.interpolated_path.get_sampled_path()
        self.assertEqual(self.interpolated_path._path, sample_path)

    def test_trimmed_path_up_to_progress(self) -> None:
        """Test if path is trimmed correctly"""
        sample_path = trim_path_up_to_progress(self.interpolated_path, 2)
        self.assertEqual([self.interpolated_path.get_state_at_progress(2)] + self.interpolated_path._path[1:], sample_path)
        trimmed_sample_path = trim_path_up_to_progress(self.interpolated_path, 5)
        self.assertEqual(self.interpolated_path._path[1:], trimmed_sample_path)

    def test_trim_path(self) -> None:
        """Test if path is trimmed correctly"""
        sample_path = trim_path(self.interpolated_path, 2, 10)
        self.assertEqual([self.interpolated_path.get_state_at_progress(2)] + [self.interpolated_path._path[1]] + [self.interpolated_path.get_state_at_progress(10)], sample_path)
        sample_path = trim_path(self.interpolated_path, 2, 3)
        self.assertEqual([self.interpolated_path.get_state_at_progress(2)] + [self.interpolated_path.get_state_at_progress(3)], sample_path)
        sample_path = trim_path(self.interpolated_path, 0, 0)
        self.assertEqual(self.interpolated_path._path[:2], sample_path)

def test_get_state_at_progress_expect_throw(self) -> None:
    """Check if assertion is raised for invalid calls"""
    self.assertRaises(AssertionError, self.interpolated_path.get_state_at_progress, 100)
    self.assertRaises(AssertionError, self.interpolated_path.get_state_at_progress, -1)

class SimulationRunner(AbstractRunner):
    """
    Manager which executes multiple simulations with the same planner
    """

    def __init__(self, simulation: Simulation, planner: AbstractPlanner):
        """
        Initialize the simulations manager
        :param simulation: Simulation which will be executed
        :param planner: to be used to compute the desired ego's trajectory
        """
        self._simulation = simulation
        self._planner = planner

    def _initialize(self) -> None:
        """
        Initialize the planner
        """
        self._simulation.callback.on_initialization_start(self._simulation.setup, self.planner)
        self.planner.initialize(self._simulation.initialize())
        self._simulation.callback.on_initialization_end(self._simulation.setup, self.planner)

    @property
    def planner(self) -> AbstractPlanner:
        """
        :return: Planner used by the SimulationRunner
        """
        return self._planner

    @property
    def simulation(self) -> Simulation:
        """
        :return: Simulation used by the SimulationRunner
        """
        return self._simulation

    @property
    def scenario(self) -> AbstractScenario:
        """
        :return: Get the scenario relative to the simulation.
        """
        return self.simulation.scenario

    def run(self) -> RunnerReport:
        """
        Run through all simulations. The steps of execution follow:
         - Initialize all planners
         - Step through simulations until there no running simulation
        :return: List of SimulationReports containing the results of each simulation
        """
        start_time = time.perf_counter()
        report = RunnerReport(succeeded=True, error_message=None, start_time=start_time, end_time=None, planner_report=None, scenario_name=self._simulation.scenario.scenario_name, planner_name=self.planner.name(), log_name=self._simulation.scenario.log_name)
        self.simulation.callback.on_simulation_start(self.simulation.setup)
        self._initialize()
        while self.simulation.is_simulation_running():
            self.simulation.callback.on_step_start(self.simulation.setup, self.planner)
            planner_input = self._simulation.get_planner_input()
            logger.debug('Simulation iterations: %s' % planner_input.iteration.index)
            self._simulation.callback.on_planner_start(self.simulation.setup, self.planner)
            trajectory = self.planner.compute_trajectory(planner_input)
            self._simulation.callback.on_planner_end(self.simulation.setup, self.planner, trajectory)
            self.simulation.propagate(trajectory)
            self.simulation.callback.on_step_end(self.simulation.setup, self.planner, self.simulation.history.last())
            current_time = time.perf_counter()
            if not self.simulation.is_simulation_running():
                report.end_time = current_time
        self.simulation.callback.on_simulation_end(self.simulation.setup, self.planner, self.simulation.history)
        planner_report = self.planner.generate_planner_report()
        report.planner_report = planner_report
        return report

def _initialize(self) -> None:
    """
        Initialize the planner
        """
    self._simulation.callback.on_initialization_start(self._simulation.setup, self.planner)
    self.planner.initialize(self._simulation.initialize())
    self._simulation.callback.on_initialization_end(self._simulation.setup, self.planner)

class StepSimulationTimeController(AbstractSimulationTimeController):
    """
    Class handling simulation time and completion.
    """

    def __init__(self, scenario: AbstractScenario):
        """
        Initialize simulation control.
        """
        self.current_iteration_index = 0
        self.scenario = scenario

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_iteration_index = 0

    def get_iteration(self) -> SimulationIteration:
        """Inherited, see superclass."""
        scenario_time = self.scenario.get_time_point(self.current_iteration_index)
        return SimulationIteration(time_point=scenario_time, index=self.current_iteration_index)

    def next_iteration(self) -> Optional[SimulationIteration]:
        """Inherited, see superclass."""
        self.current_iteration_index += 1
        return None if self.reached_end() else self.get_iteration()

    def reached_end(self) -> bool:
        """Inherited, see superclass."""
        return self.current_iteration_index >= self.number_of_iterations() - 1

    def number_of_iterations(self) -> int:
        """Inherited, see superclass."""
        return cast(int, self.scenario.get_number_of_iterations())

def get_iteration(self) -> SimulationIteration:
    """Inherited, see superclass."""
    scenario_time = self.scenario.get_time_point(self.current_iteration_index)
    return SimulationIteration(time_point=scenario_time, index=self.current_iteration_index)

def next_iteration(self) -> Optional[SimulationIteration]:
    """Inherited, see superclass."""
    self.current_iteration_index += 1
    return None if self.reached_end() else self.get_iteration()

def reached_end(self) -> bool:
    """Inherited, see superclass."""
    return self.current_iteration_index >= self.number_of_iterations() - 1

def number_of_iterations(self) -> int:
    """Inherited, see superclass."""
    return cast(int, self.scenario.get_number_of_iterations())

class MultiCallback(AbstractCallback):
    """
    This class simply calls many callbacks for simplified code.
    """

    def __init__(self, callbacks: List[AbstractCallback]):
        """
        Initialize with multiple callbacks.
        :param callbacks: all callbacks that will be called sequentially.
        """
        self._callbacks = callbacks

    @property
    def callbacks(self) -> List[AbstractCallback]:
        """
        Property to access callbacks.
        :return: list of callbacks this MultiCallback runs.
        """
        return self._callbacks

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_initialization_start(setup, planner)

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_initialization_end(setup, planner)

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_step_start(setup, planner)

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_step_end(setup, planner, sample)

    def on_planner_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_planner_start(setup, planner)

    def on_planner_end(self, setup: SimulationSetup, planner: AbstractPlanner, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_planner_end(setup, planner, trajectory)

    def on_simulation_start(self, setup: SimulationSetup) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_simulation_start(setup)

    def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
        """Inherited, see superclass."""
        for callback in self._callbacks:
            callback.on_simulation_end(setup, planner, history)

def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
    """Inherited, see superclass."""
    for callback in self._callbacks:
        callback.on_initialization_end(setup, planner)

class SerializationCallback(AbstractCallback):
    """Callback for serializing scenes at the end of the simulation."""

    def __init__(self, output_directory: Union[str, pathlib.Path], folder_name: Union[str, pathlib.Path], serialization_type: str, serialize_into_single_file: bool):
        """
        Construct serialization callback
        :param output_directory: where scenes should be serialized
        :param folder_name: folder where output should be serialized
        :param serialization_type: A way to serialize output, options: ["json", "pickle", "msgpack"]
        :param serialize_into_single_file: if true all data will be in single file, if false, each time step will
                be serialized into a separate file
        """
        available_formats = ['json', 'pickle', 'msgpack']
        if serialization_type not in available_formats:
            raise ValueError(f'The serialization callback will not store files anywhere!Choose at least one format from {available_formats} instead of {serialization_type}!')
        self._output_directory = pathlib.Path(output_directory) / folder_name
        self._serialization_type = serialization_type
        self._serialize_into_single_file = serialize_into_single_file

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """
        Create directory at initialization
        :param setup: simulation setup
        :param planner: planner before initialization
        """
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
        scenario_directory.mkdir(exist_ok=True, parents=True)

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """Inherited, see superclass."""
        pass

    def on_planner_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_planner_end(self, setup: SimulationSetup, planner: AbstractPlanner, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        pass

    def on_simulation_start(self, setup: SimulationSetup) -> None:
        """Inherited, see superclass."""
        pass

    def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
        """
        On reached_end validate that all steps were correctly serialized
        :param setup: simulation setup
        :param planner: planner when simulation ends
        :param history: resulting from simulation
        """
        number_of_scenes = len(history)
        if number_of_scenes == 0:
            raise RuntimeError('Number of scenes has to be greater than 0')
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
        scenario = setup.scenario
        expert_trajectory = list(scenario.get_expert_ego_trajectory())
        scenes = [convert_sample_to_scene(map_name=scenario.map_api.map_name, database_interval=scenario.database_interval, traffic_light_status=scenario.get_traffic_light_status_at_iteration(index), expert_trajectory=expert_trajectory, mission_goal=scenario.get_mission_goal(), data=sample, colors=TrajectoryColors()) for index, sample in enumerate(history.data)]
        self._serialize_scenes(scenes, scenario_directory)

    def _serialize_scenes(self, scenes: List[Dict[str, Any]], scenario_directory: pathlib.Path) -> None:
        """
        Serialize scenes based on callback setup to json/pickle or other
        :param scenes: scenes to be serialized
        :param scenario_directory: directory where they should be serialized
        """
        if not self._serialize_into_single_file:
            for scene in scenes:
                file_name = scenario_directory / str(scene['ego']['timestamp_us'])
                _dump_to_file(file_name, scene, self._serialization_type)
        else:
            file_name = scenario_directory / scenario_directory.name
            _dump_to_file(file_name, scenes, self._serialization_type)

    def _get_scenario_folder(self, planner_name: str, scenario: AbstractScenario) -> pathlib.Path:
        """
        Compute scenario folder directory where all files will be stored
        :param planner_name: planner name
        :param scenario: for which to compute directory name
        :return directory path
        """
        return self._output_directory / planner_name / scenario.scenario_type / scenario.log_name / scenario.scenario_name

def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """
        On reached_end validate that all steps were correctly serialized
        :param setup: simulation setup
        :param planner: planner when simulation ends
        :param history: resulting from simulation
        """
    number_of_scenes = len(history)
    if number_of_scenes == 0:
        raise RuntimeError('Number of scenes has to be greater than 0')
    scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
    scenario = setup.scenario
    expert_trajectory = list(scenario.get_expert_ego_trajectory())
    scenes = [convert_sample_to_scene(map_name=scenario.map_api.map_name, database_interval=scenario.database_interval, traffic_light_status=scenario.get_traffic_light_status_at_iteration(index), expert_trajectory=expert_trajectory, mission_goal=scenario.get_mission_goal(), data=sample, colors=TrajectoryColors()) for index, sample in enumerate(history.data)]
    self._serialize_scenes(scenes, scenario_directory)

class TestTimingCallback(TestCase):
    """
    Tests the simulation TimingCallback.
    """

    def setUp(self) -> None:
        """
        Setup mocks for the tests
        """
        self.writer = Mock(spec=SummaryWriter)
        self.setup = Mock(spec=SimulationSetup)
        self.planner = Mock(spec=AbstractPlanner)
        self.trajectory = Mock(spec=AbstractTrajectory)
        self.history = Mock(spec=SimulationHistory)
        self.history_sample = Mock(spec=SimulationHistorySample)
        self.setup.scenario = Mock()
        self.setup.scenario.token = TOKEN
        self.tc = TimingCallback(self.writer)
        return super().setUp()

    def test_constructor(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        self.assertEqual(self.tc._writer, self.writer)
        self.assertFalse(self.tc._scenarios_captured)
        self.assertIsNone(self.tc._step_start)
        self.assertIsNone(self.tc._simulation_start)
        self.assertIsNone(self.tc._planner_start)
        self.assertFalse(self.tc._step_duration)
        self.assertFalse(self.tc._planner_step_duration)
        self.assertEqual(self.tc._tensorboard_global_step, 0)

    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_planner_start(self, get_time: MagicMock) -> None:
        """
        Tests if the get_time method is called and the start time is set accordingly.
        """
        get_time.return_value = START_TIME
        self.tc.on_planner_start(self.setup, self.planner)
        get_time.assert_called_once()
        self.assertEqual(self.tc._planner_start, START_TIME)

    def test_on_planner_end_throws_if_no_start_time_set(self) -> None:
        """
        Tests if on_planner_end throws an exception if the planner_start time is not set.
        """
        with self.assertRaises(AssertionError):
            self.tc.on_planner_end(self.setup, self.planner, self.trajectory)

    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_planner_end(self, get_time: MagicMock) -> None:
        """
        Tests if the get_time method is called and the duration is set accordingly.
        """
        get_time.return_value = END_TIME
        self.tc._planner_start = START_TIME
        with patch.object(self.tc, '_planner_step_duration') as planner_step_duration:
            self.tc.on_planner_end(self.setup, self.planner, self.trajectory)
            planner_step_duration.append.assert_called_once_with(END_TIME - START_TIME)
            get_time.assert_called_once()

    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_simulation_start(self, get_time: MagicMock) -> None:
        """
        Tests if the captured scenarios for token passed with setup is set to None.
        Tests if the get_time method is called and the simulation_start is set accordingly.
        """
        get_time.return_value = START_TIME
        self.tc.on_simulation_start(self.setup)
        get_time.assert_called_once()
        self.assertEqual(self.tc._scenarios_captured[TOKEN], None)
        self.assertEqual(self.tc._simulation_start, START_TIME)

    def test_on_simulation_end_throws_if_no_start_time_set(self) -> None:
        """
        Tests if on_simulation_end throws an exception if the simulation_start time is not set.
        """
        with self.assertRaises(AssertionError):
            self.tc.on_simulation_end(self.setup, self.planner, self.history)

    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_simulation_end(self, get_time: MagicMock) -> None:
        """
        Tests if the get_time method is called and the elapsed time is set accordingly.
        Tests if the timings are calculated properly and writer is called with the correct values.
        Tests if the timings are stored in the scenarios_captured under the right token.
        Tests if the step_duration and planner_step_duration are cleared.
        """
        get_time.return_value = END_TIME
        self.writer.add_scalar = Mock()
        self.tc._tensorboard_global_step = GLOBAL_STEP
        self.tc._simulation_start = START_TIME
        self.tc._step_duration = [123, 444, 789]
        self.tc._planner_step_duration = [456, 555, 1011]
        self.tc.on_simulation_end(self.setup, self.planner, self.history)
        get_time.assert_called_once()
        self.writer.add_scalar.assert_has_calls([call('simulation_elapsed_time', END_TIME - START_TIME, 7), call('mean_step_time', 452, 7), call('max_step_time', 789, 7), call('max_planner_step_time', 1011, 7), call('mean_planner_step_time', 674, 7)])
        self.assertEqual(self.tc._scenarios_captured[TOKEN], {'simulation_elapsed_time': END_TIME - START_TIME, 'mean_step_time': 452, 'max_step_time': 789, 'max_planner_step_time': 1011, 'mean_planner_step_time': 674})
        self.assertEqual(self.tc._tensorboard_global_step, GLOBAL_STEP + 1)
        self.assertFalse(self.tc._step_duration)
        self.assertFalse(self.tc._planner_step_duration)

    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_step_start(self, get_time: MagicMock) -> None:
        """
        Tests if the get_time method is called and the step_start is set accordingly.
        """
        get_time.return_value = START_TIME
        self.tc.on_step_start(self.setup, self.planner)
        self.assertEqual(self.tc._step_start, START_TIME)

    def test_on_step_end_throws_if_no_start_time_set(self) -> None:
        """
        Tests if on_step_end throws an exception if the step_start time is not set.
        """
        with self.assertRaises(AssertionError):
            self.tc.on_step_end(self.setup, self.planner, self.history_sample)

    @patch.object(TimingCallback, '_step_start', create=True, new_callable=PropertyMock)
    @patch.object(TimingCallback, '_get_time', autospec=True)
    def test_on_step_end(self, get_time: MagicMock, step_start: MagicMock) -> None:
        """
        Tests if the get_time method is called and the duration since start is appended to the step_duration.
        """
        get_time.return_value = END_TIME
        step_start.return_value = START_TIME
        with patch.object(self.tc, '_step_duration') as step_duration:
            self.tc.on_step_end(self.setup, self.planner, self.history_sample)
            step_duration.append.assert_called_once_with(END_TIME - START_TIME)
            get_time.assert_called_once()

    @patch('nuplan.planning.simulation.callback.timing_callback.time.perf_counter')
    def test_get_time(self, perf_counter: MagicMock) -> None:
        """
        Tests if the perf_counter method is called and the result is returned.
        """
        perf_counter.return_value = START_TIME
        result = self.tc._get_time()
        self.assertEqual(result, START_TIME)
        perf_counter.assert_called_once()

def test_on_simulation_end_throws_if_no_start_time_set(self) -> None:
    """
        Tests if on_simulation_end throws an exception if the simulation_start time is not set.
        """
    with self.assertRaises(AssertionError):
        self.tc.on_simulation_end(self.setup, self.planner, self.history)

def move_features_type_to_device(batch: FeaturesType, device: torch.device) -> FeaturesType:
    """
    Move all features to a device
    :param batch: batch of features
    :param device: new device
    :return: batch moved to new device
    """
    output = {}
    for key, value in batch.items():
        output[key] = value.to_device(device)
    return output

class VectorMapSimpleMLP(ScriptableTorchModuleWrapper):
    """Simple vector-based model that encodes agents and map elements through an MLP."""

    def __init__(self, num_output_features: int, hidden_size: int, vector_map_feature_radius: int, past_trajectory_sampling: TrajectorySampling, future_trajectory_sampling: TrajectorySampling):
        """
        Initialize the simple vector map model.
        :param num_output_features: number of target features
        :param hidden_size: size of hidden layers of MLP
        :param vector_map_feature_radius: The query radius scope relative to the current ego-pose.
        :param past_trajectory_sampling: Sampling parameters for past trajectory
        :param future_trajectory_sampling: Sampling parameters for future trajectory
        """
        super().__init__(feature_builders=[VectorMapFeatureBuilder(radius=vector_map_feature_radius), AgentsFeatureBuilder(past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling)], future_trajectory_sampling=future_trajectory_sampling)
        self._hidden_size = hidden_size
        self.vectormap_mlp = create_mlp(input_size=2 * VectorMap.lane_coord_dim(), output_size=self._hidden_size, hidden_size=self._hidden_size)
        self.ego_mlp = create_mlp(input_size=(past_trajectory_sampling.num_poses + 1) * Agents.ego_state_dim(), output_size=self._hidden_size, hidden_size=self._hidden_size)
        self._agent_mlp_dim = (past_trajectory_sampling.num_poses + 1) * Agents.agents_states_dim()
        self.agent_mlp = create_mlp(input_size=self._agent_mlp_dim, output_size=self._hidden_size, hidden_size=self._hidden_size)
        self._mlp = create_mlp(input_size=3 * self._hidden_size, output_size=num_output_features, hidden_size=self._hidden_size)
        self._vector_map_flatten_lane_coord_dim = VectorMap.flatten_lane_coord_dim()
        self._trajectory_state_size = Trajectory.state_size()

    @torch.jit.unused
    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "vector_map": VectorMap,
                            "agents": Agents,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        vector_map_data = cast(VectorMap, features['vector_map'])
        ego_agents_feature = cast(Agents, features['agents'])
        tensor_inputs: Dict[str, torch.Tensor] = {}
        list_tensor_inputs = {'vector_map.coords': vector_map_data.coords, 'agents.ego': ego_agents_feature.ego, 'agents.agents': ego_agents_feature.agents}
        list_list_tensor_inputs: Dict[str, List[List[torch.Tensor]]] = {}
        output_tensors, output_list_tensors, output_list_list_tensors = self.scriptable_forward(tensor_inputs, list_tensor_inputs, list_list_tensor_inputs)
        return {'trajectory': Trajectory(data=output_tensors['trajectory'])}

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Implemented. See interface.
        """
        ego_past_trajectory = list_tensor_data['agents.ego']
        ego_agents_agents = list_tensor_data['agents.agents']
        vector_map_coords = list_tensor_data['vector_map.coords']
        if len(vector_map_coords) != len(ego_agents_agents) or len(vector_map_coords) != len(ego_past_trajectory):
            raise ValueError(f'Mixed batch sizes passed to scriptable_forward: vector_map.coords = {len(vector_map_coords)}, agents.agents = {len(ego_agents_agents)}, agents.ego_past_trajectory={len(ego_past_trajectory)}')
        batch_size = len(vector_map_coords)
        vector_map_feature: List[torch.Tensor] = []
        agents_feature: List[torch.Tensor] = []
        ego_feature: List[torch.Tensor] = []
        for sample_idx in range(batch_size):
            sample_ego_feature = self.ego_mlp(ego_past_trajectory[sample_idx].view(1, -1))
            ego_feature.append(torch.max(sample_ego_feature, dim=0).values)
            vectormap_coords = vector_map_coords[sample_idx].reshape(-1, self._vector_map_flatten_lane_coord_dim)
            if vectormap_coords.numel() == 0:
                vectormap_coords = torch.zeros((1, self._vector_map_flatten_lane_coord_dim), dtype=vectormap_coords.dtype, device=vectormap_coords.device)
            sample_vectormap_feature = self.vectormap_mlp(vectormap_coords)
            vector_map_feature.append(torch.max(sample_vectormap_feature, dim=0).values)
            this_agents_feature = ego_agents_agents[sample_idx]
            agents_multiplier = float(min(this_agents_feature.shape[1], 1))
            if this_agents_feature.shape[1] > 0:
                orig_shape = this_agents_feature.shape
                flattened_agents = this_agents_feature.transpose(1, 0).reshape(orig_shape[1], -1)
            else:
                flattened_agents = torch.zeros((this_agents_feature.shape[0], self._agent_mlp_dim), device=sample_vectormap_feature.device, dtype=sample_vectormap_feature.dtype, layout=sample_vectormap_feature.layout)
            sample_agent_feature = self.agent_mlp(flattened_agents)
            sample_agent_feature *= agents_multiplier
            agents_feature.append(torch.max(sample_agent_feature, dim=0).values)
        vector_map_feature = torch.cat(vector_map_feature).reshape(batch_size, -1)
        ego_feature = torch.cat(ego_feature).reshape(batch_size, -1)
        agents_feature = torch.cat(agents_feature).reshape(batch_size, -1)
        input_features = torch.cat([vector_map_feature, ego_feature, agents_feature], dim=1)
        predictions = self._mlp(input_features)
        output_tensors: Dict[str, torch.Tensor] = {'trajectory': convert_predictions_to_trajectory(predictions, self._trajectory_state_size)}
        output_list_tensors: Dict[str, List[torch.Tensor]] = {}
        output_list_list_tensors: Dict[str, List[List[torch.Tensor]]] = {}
        return (output_tensors, output_list_tensors, output_list_list_tensors)

def __init__(self, num_output_features: int, hidden_size: int, vector_map_feature_radius: int, past_trajectory_sampling: TrajectorySampling, future_trajectory_sampling: TrajectorySampling):
    """
        Initialize the simple vector map model.
        :param num_output_features: number of target features
        :param hidden_size: size of hidden layers of MLP
        :param vector_map_feature_radius: The query radius scope relative to the current ego-pose.
        :param past_trajectory_sampling: Sampling parameters for past trajectory
        :param future_trajectory_sampling: Sampling parameters for future trajectory
        """
    super().__init__(feature_builders=[VectorMapFeatureBuilder(radius=vector_map_feature_radius), AgentsFeatureBuilder(past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling)], future_trajectory_sampling=future_trajectory_sampling)
    self._hidden_size = hidden_size
    self.vectormap_mlp = create_mlp(input_size=2 * VectorMap.lane_coord_dim(), output_size=self._hidden_size, hidden_size=self._hidden_size)
    self.ego_mlp = create_mlp(input_size=(past_trajectory_sampling.num_poses + 1) * Agents.ego_state_dim(), output_size=self._hidden_size, hidden_size=self._hidden_size)
    self._agent_mlp_dim = (past_trajectory_sampling.num_poses + 1) * Agents.agents_states_dim()
    self.agent_mlp = create_mlp(input_size=self._agent_mlp_dim, output_size=self._hidden_size, hidden_size=self._hidden_size)
    self._mlp = create_mlp(input_size=3 * self._hidden_size, output_size=num_output_features, hidden_size=self._hidden_size)
    self._vector_map_flatten_lane_coord_dim = VectorMap.flatten_lane_coord_dim()
    self._trajectory_state_size = Trajectory.state_size()

class TestUrbanDriverOpenLoop(unittest.TestCase):
    """Test UrbanDriverOpenLoopModel model."""

    def setUp(self) -> None:
        """Set up the test."""
        self.model_params = UrbanDriverOpenLoopModelParams(local_embedding_size=256, global_embedding_size=256, num_subgraph_layers=3, global_head_dropout=0.0)
        self.feature_params = UrbanDriverOpenLoopModelFeatureParams(feature_types={'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}, total_max_points=20, feature_dimension=8, agent_features=['VEHICLE', 'BICYCLE', 'PEDESTRIAN'], ego_dimension=3, agent_dimension=8, max_agents=30, past_trajectory_sampling=TrajectorySampling(time_horizon=2.0, num_poses=4), map_features=['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES'], max_elements={'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}, max_points={'LANE': 20, 'LEFT_BOUNDARY': 20, 'RIGHT_BOUNDARY': 20, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 20}, vector_set_map_feature_radius=35, interpolation_method='linear', disable_map=False, disable_agents=False)
        self.target_params = UrbanDriverOpenLoopModelTargetParams(num_output_features=36, future_trajectory_sampling=TrajectorySampling(time_horizon=6.0, num_poses=12))

    def _build_model(self) -> UrbanDriverOpenLoopModel:
        """
        Creates a new instance of a UrbanDriverOpenLoop with some default parameters.
        """
        model = UrbanDriverOpenLoopModel(self.model_params, self.feature_params, self.target_params)
        return model

    def _build_input_features(self, device: torch.device, include_agents: bool) -> FeaturesType:
        """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :return: FeaturesType to be consumed by the model
        """
        num_frames = 5
        num_agents = num_frames if include_agents else 0
        coords: Dict[str, List[torch.Tensor]] = dict()
        traffic_light_data: Dict[str, List[torch.Tensor]] = dict()
        availabilities: Dict[str, List[torch.BoolTensor]] = dict()
        for feature_name in self.feature_params.map_features:
            coords[feature_name] = [torch.zeros((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name], VectorSetMap.coord_dim()), dtype=torch.float32, device=device)]
            availabilities[feature_name] = [torch.ones((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name]), dtype=torch.bool, device=device)]
        traffic_light_data['LANE'] = [torch.zeros((self.feature_params.max_elements['LANE'], self.feature_params.max_points['LANE'], VectorSetMap.traffic_light_status_dim()), dtype=torch.float32, device=device)]
        vector_set_map_feature = VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)
        ego_agents = [torch.zeros((num_frames, GenericAgents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = {feature_name: [torch.zeros((num_frames, num_agents, GenericAgents.agents_states_dim()), dtype=torch.float32, device=device)] for feature_name in self.feature_params.agent_features}
        generic_agents_feature = GenericAgents(ego=ego_agents, agents=agent_agents)
        return {'vector_set_map': vector_set_map_feature, 'generic_agents': generic_agents_feature}

    def _find_free_port(self) -> int:
        """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            address, port = s.getsockname()
            return int(port)

    def _init_distributed_process_group(self) -> None:
        """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def _assert_valid_output(self, model_output: TargetsType) -> None:
        """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
        self.assertTrue('trajectory' in model_output)
        self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
        predicted_trajectory: Trajectory = model_output['trajectory']
        self.assertIsNotNone(predicted_trajectory.data)

    def _perform_backprop_step(self, optimizer: torch.optim.Optimizer, loss_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor], predictions: TargetsType) -> None:
        """
        Performs a backpropagation step.
        :param optimizer: The optimizer to use for training.
        :param loss_function: The loss function to use.
        :param predictions: The output from the model.
        """
        loss = loss_function(predictions['trajectory'].data, torch.zeros_like(predictions['trajectory'].data))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    def test_backprop(self) -> None:
        """
        Tests that the UrbanDriverOpenLoop model can train with DDP.
        This test was developed in response to an error related to zero agent input
        """
        self._init_distributed_process_group()
        device = torch.device('cpu')
        model = self._build_model().to(device)
        ddp_model = DDP(model, device_ids=None, output_device=None)
        optimizer = torch.optim.RMSprop(ddp_model.parameters())
        loss_function = torch.nn.MSELoss()
        num_epochs = 3
        for _ in range(num_epochs):
            for include_agents in [True, False]:
                input_features = self._build_input_features(device, include_agents=include_agents)
                predictions = ddp_model.forward(input_features)
                self._assert_valid_output(predictions)
                self._perform_backprop_step(optimizer, loss_function, predictions)

def _build_input_features(self, device: torch.device, include_agents: bool) -> FeaturesType:
    """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :return: FeaturesType to be consumed by the model
        """
    num_frames = 5
    num_agents = num_frames if include_agents else 0
    coords: Dict[str, List[torch.Tensor]] = dict()
    traffic_light_data: Dict[str, List[torch.Tensor]] = dict()
    availabilities: Dict[str, List[torch.BoolTensor]] = dict()
    for feature_name in self.feature_params.map_features:
        coords[feature_name] = [torch.zeros((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name], VectorSetMap.coord_dim()), dtype=torch.float32, device=device)]
        availabilities[feature_name] = [torch.ones((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name]), dtype=torch.bool, device=device)]
    traffic_light_data['LANE'] = [torch.zeros((self.feature_params.max_elements['LANE'], self.feature_params.max_points['LANE'], VectorSetMap.traffic_light_status_dim()), dtype=torch.float32, device=device)]
    vector_set_map_feature = VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)
    ego_agents = [torch.zeros((num_frames, GenericAgents.ego_state_dim()), dtype=torch.float32, device=device)]
    agent_agents = {feature_name: [torch.zeros((num_frames, num_agents, GenericAgents.agents_states_dim()), dtype=torch.float32, device=device)] for feature_name in self.feature_params.agent_features}
    generic_agents_feature = GenericAgents(ego=ego_agents, agents=agent_agents)
    return {'vector_set_map': vector_set_map_feature, 'generic_agents': generic_agents_feature}

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

class VisualizationCallback(pl.Callback):
    """
    Callback that visualizes planner model inputs/outputs and logs them in Tensorboard.
    """

    def __init__(self, images_per_tile: int, num_train_tiles: int, num_val_tiles: int, pixel_size: float):
        """
        Initialize the class.

        :param images_per_tile: number of images per tiles to visualize
        :param num_train_tiles: number of tiles from the training set
        :param num_val_tiles: number of tiles from the validation set
        :param pixel_size: [m] size of pixel in meters
        """
        super().__init__()
        self.custom_batch_size = images_per_tile
        self.num_train_images = num_train_tiles * images_per_tile
        self.num_val_images = num_val_tiles * images_per_tile
        self.pixel_size = pixel_size
        self.train_dataloader: Optional[torch.utils.data.DataLoader] = None
        self.val_dataloader: Optional[torch.utils.data.DataLoader] = None

    def _initialize_dataloaders(self, datamodule: pl.LightningDataModule) -> None:
        """
        Initialize the dataloaders. This makes sure that the same examples are sampled
        every time for comparison during visualization.

        :param datamodule: lightning datamodule
        """
        train_set = datamodule.train_dataloader().dataset
        val_set = datamodule.val_dataloader().dataset
        self.train_dataloader = self._create_dataloader(train_set, self.num_train_images)
        self.val_dataloader = self._create_dataloader(val_set, self.num_val_images)

    def _create_dataloader(self, dataset: torch.utils.data.Dataset, num_samples: int) -> torch.utils.data.DataLoader:
        dataset_size = len(dataset)
        num_keep = min(dataset_size, num_samples)
        sampled_idxs = random.sample(range(dataset_size), num_keep)
        subset = torch.utils.data.Subset(dataset=dataset, indices=sampled_idxs)
        return torch.utils.data.DataLoader(dataset=subset, batch_size=self.custom_batch_size, collate_fn=FeatureCollate())

    def _log_from_dataloader(self, pl_module: pl.LightningModule, dataloader: torch.utils.data.DataLoader, loggers: List[Any], training_step: int, prefix: str) -> None:
        """
        Visualizes and logs all examples from the input dataloader.

        :param pl_module: lightning module used for inference
        :param dataloader: torch dataloader
        :param loggers: list of loggers from the trainer
        :param training_step: global step in training
        :param prefix: prefix to add to the log tag
        """
        for batch_idx, batch in enumerate(dataloader):
            features: FeaturesType = batch[0]
            targets: TargetsType = batch[1]
            predictions = self._infer_model(pl_module, move_features_type_to_device(features, pl_module.device))
            self._log_batch(loggers, features, targets, predictions, batch_idx, training_step, prefix)

    def _log_batch(self, loggers: List[Any], features: FeaturesType, targets: TargetsType, predictions: TargetsType, batch_idx: int, training_step: int, prefix: str) -> None:
        """
        Visualizes and logs a batch of data (features, targets, predictions) from the model.

        :param loggers: list of loggers from the trainer
        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :param batch_idx: index of total batches to visualize
        :param training_step: global training step
        :param prefix: prefix to add to the log tag
        """
        if 'trajectory' not in targets or 'trajectory' not in predictions:
            return
        if 'raster' in features:
            image_batch = self._get_images_from_raster_features(features, targets, predictions)
        elif ('vector_map' in features or 'vector_set_map' in features) and ('agents' in features or 'generic_agents' in features):
            image_batch = self._get_images_from_vector_features(features, targets, predictions)
        else:
            return
        tag = f'{prefix}_visualization_{batch_idx}'
        for logger in loggers:
            if isinstance(logger, torch.utils.tensorboard.writer.SummaryWriter):
                logger.add_images(tag=tag, img_tensor=torch.from_numpy(image_batch), global_step=training_step, dataformats='NHWC')

    def _get_images_from_raster_features(self, features: FeaturesType, targets: TargetsType, predictions: TargetsType) -> npt.NDArray[np.uint8]:
        """
        Create a list of RGB raster images from a batch of model data of raster features.

        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :return: list of raster images
        """
        images = list()
        for raster, target_trajectory, predicted_trajectory in zip(features['raster'].unpack(), targets['trajectory'].unpack(), predictions['trajectory'].unpack()):
            image = get_raster_with_trajectories_as_rgb(raster, target_trajectory, predicted_trajectory, pixel_size=self.pixel_size)
            images.append(image)
        return np.asarray(images)

    def _get_images_from_vector_features(self, features: FeaturesType, targets: TargetsType, predictions: TargetsType) -> npt.NDArray[np.uint8]:
        """
        Create a list of RGB raster images from a batch of model data of vectormap and agent features.

        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :return: list of raster images
        """
        images = list()
        vector_map_feature = 'vector_map' if 'vector_map' in features else 'vector_set_map'
        agents_feature = 'agents' if 'agents' in features else 'generic_agents'
        for vector_map, agents, target_trajectory, predicted_trajectory in zip(features[vector_map_feature].unpack(), features[agents_feature].unpack(), targets['trajectory'].unpack(), predictions['trajectory'].unpack()):
            image = get_raster_from_vector_map_with_agents(vector_map, agents, target_trajectory, predicted_trajectory, pixel_size=self.pixel_size)
            images.append(image)
        return np.asarray(images)

    def _infer_model(self, pl_module: pl.LightningModule, features: FeaturesType) -> TargetsType:
        """
        Make an inference of the input batch features given a model.

        :param pl_module: lightning model
        :param features: model inputs
        :return: model predictions
        """
        with torch.no_grad():
            pl_module.eval()
            predictions = move_features_type_to_device(pl_module(features), torch.device('cpu'))
            pl_module.train()
        return predictions

    def on_train_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional=None) -> None:
        """
        Visualizes and logs training examples at the end of the epoch.

        :param trainer: lightning trainer
        :param pl_module: lightning module
        """
        assert hasattr(trainer, 'datamodule'), 'Trainer missing datamodule attribute'
        assert hasattr(trainer, 'global_step'), 'Trainer missing global_step attribute'
        if self.train_dataloader is None:
            self._initialize_dataloaders(trainer.datamodule)
        self._log_from_dataloader(pl_module, self.train_dataloader, trainer.logger.experiment, trainer.global_step, 'train')

    def on_validation_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional=None) -> None:
        """
        Visualizes and logs validation examples at the end of the epoch.

        :param trainer: lightning trainer
        :param pl_module: lightning module
        """
        assert hasattr(trainer, 'datamodule'), 'Trainer missing datamodule attribute'
        assert hasattr(trainer, 'global_step'), 'Trainer missing global_step attribute'
        if self.val_dataloader is None:
            self._initialize_dataloaders(trainer.datamodule)
        self._log_from_dataloader(pl_module, self.val_dataloader, trainer.logger.experiment, trainer.global_step, 'val')

def _log_from_dataloader(self, pl_module: pl.LightningModule, dataloader: torch.utils.data.DataLoader, loggers: List[Any], training_step: int, prefix: str) -> None:
    """
        Visualizes and logs all examples from the input dataloader.

        :param pl_module: lightning module used for inference
        :param dataloader: torch dataloader
        :param loggers: list of loggers from the trainer
        :param training_step: global step in training
        :param prefix: prefix to add to the log tag
        """
    for batch_idx, batch in enumerate(dataloader):
        features: FeaturesType = batch[0]
        targets: TargetsType = batch[1]
        predictions = self._infer_model(pl_module, move_features_type_to_device(features, pl_module.device))
        self._log_batch(loggers, features, targets, predictions, batch_idx, training_step, prefix)

class ScenarioSceneConverter(SceneConverter):
    """
    Scene writer that converts a scenario sample to scene.
    """

    def __init__(self, ego_trajectory_horizon: float, ego_trajectory_poses: int) -> None:
        """
        Initialize scene writer.
        :param ego_trajectory_horizon: the horizon to get ego's future trajectory.
        :param ego_trajectory_poses: number of poses for ego's future trajectory.
        """
        self._ego_trajectory_horizon = ego_trajectory_horizon
        self._ego_trajectory_poses = ego_trajectory_poses

    def __call__(self, scenario: AbstractScenario, features: FeaturesType, targets: TargetsType, predictions: FeaturesType) -> List[Dict[str, Any]]:
        """Inherited, see superclass."""
        index = 0
        ego_trajectory = [scenario.get_ego_state_at_iteration(index)] + list(scenario.get_ego_future_trajectory(index, self._ego_trajectory_horizon, self._ego_trajectory_poses))
        sample = SimulationHistorySample(iteration=SimulationIteration(time_point=scenario.get_time_point(index), index=index), ego_state=scenario.get_ego_state_at_iteration(index), trajectory=InterpolatedTrajectory(ego_trajectory), observation=scenario.get_tracked_objects_at_iteration(index), traffic_light_status=scenario.get_traffic_light_status_at_iteration(index))
        scene = convert_sample_to_scene(map_name=scenario.map_api.map_name, database_interval=scenario.database_interval, traffic_light_status=scenario.get_traffic_light_status_at_iteration(index), expert_trajectory=ego_trajectory, mission_goal=scenario.get_mission_goal(), data=sample)
        return [scene]

def __call__(self, scenario: AbstractScenario, features: FeaturesType, targets: TargetsType, predictions: FeaturesType) -> List[Dict[str, Any]]:
    """Inherited, see superclass."""
    index = 0
    ego_trajectory = [scenario.get_ego_state_at_iteration(index)] + list(scenario.get_ego_future_trajectory(index, self._ego_trajectory_horizon, self._ego_trajectory_poses))
    sample = SimulationHistorySample(iteration=SimulationIteration(time_point=scenario.get_time_point(index), index=index), ego_state=scenario.get_ego_state_at_iteration(index), trajectory=InterpolatedTrajectory(ego_trajectory), observation=scenario.get_tracked_objects_at_iteration(index), traffic_light_status=scenario.get_traffic_light_status_at_iteration(index))
    scene = convert_sample_to_scene(map_name=scenario.map_api.map_name, database_interval=scenario.database_interval, traffic_light_status=scenario.get_traffic_light_status_at_iteration(index), expert_trajectory=ego_trajectory, mission_goal=scenario.get_mission_goal(), data=sample)
    return [scene]

class FeaturePreprocessor:
    """
    Compute features and targets for a scenario. This class also manages cache. If a feature/target
    is not present in a cache, it is computed, otherwise it is loaded
    """

    def __init__(self, cache_path: Optional[str], force_feature_computation: bool, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
        """
        Initialize class.
        :param cache_path: Whether to cache features.
        :param force_feature_computation: If true, even if cache exists, it will be overwritten.
        :param feature_builders: List of feature builders.
        :param target_builders: List of target builders.
        """
        self._cache_path = pathlib.Path(cache_path) if cache_path else None
        self._force_feature_computation = force_feature_computation
        self._feature_builders = feature_builders
        self._target_builders = target_builders
        self._storing_mechanism = FeatureCacheS3(cache_path) if str(cache_path).startswith('s3://') else FeatureCachePickle()
        assert len(feature_builders) != 0, 'Number of feature builders has to be grater than 0!'

    @property
    def feature_builders(self) -> List[AbstractFeatureBuilder]:
        """
        :return: all feature builders
        """
        return self._feature_builders

    @property
    def target_builders(self) -> List[AbstractTargetBuilder]:
        """
        :return: all target builders
        """
        return self._target_builders

    def get_list_of_feature_types(self) -> List[Type[AbstractModelFeature]]:
        """
        :return all features that are computed by the builders
        """
        return [builder.get_feature_type() for builder in self._feature_builders]

    def get_list_of_target_types(self) -> List[Type[AbstractModelFeature]]:
        """
        :return all targets that are computed by the builders
        """
        return [builder.get_feature_type() for builder in self._target_builders]

    def compute_features(self, scenario: AbstractScenario) -> Tuple[FeaturesType, TargetsType, List[CacheMetadataEntry]]:
        """
        Compute features for a scenario, in case cache_path is set, features will be stored in cache,
        otherwise just recomputed
        :param scenario for which features and targets should be computed
        :return: model features and targets and cache metadata
        """
        try:
            all_features: FeaturesType
            all_feature_cache_metadata: List[CacheMetadataEntry]
            all_targets: TargetsType
            all_targets_cache_metadata: List[CacheMetadataEntry]
            all_features, all_feature_cache_metadata = self._compute_all_features(scenario, self._feature_builders)
            all_targets, all_targets_cache_metadata = self._compute_all_features(scenario, self._target_builders)
            all_cache_metadata = all_feature_cache_metadata + all_targets_cache_metadata
            return (all_features, all_targets, all_cache_metadata)
        except Exception as error:
            msg = f'Failed to compute features for scenario token {scenario.token} in log {scenario.log_name}\nError: {error}'
            logger.error(msg)
            traceback.print_exc()
            raise RuntimeError(msg)

    def _compute_all_features(self, scenario: AbstractScenario, builders: List[Union[AbstractFeatureBuilder, AbstractTargetBuilder]]) -> Tuple[Union[FeaturesType, TargetsType], List[Optional[CacheMetadataEntry]]]:
        """
        Compute all features/targets from builders for scenario
        :param scenario: for which features should be computed
        :param builders: to use for feature computation
        :return: computed features/targets and the metadata entries for the computed features/targets
        """
        all_features: FeaturesType = {}
        all_features_metadata_entries: List[CacheMetadataEntry] = []
        for builder in builders:
            feature, feature_metadata_entry = compute_or_load_feature(scenario, self._cache_path, builder, self._storing_mechanism, self._force_feature_computation)
            all_features[builder.get_feature_unique_name()] = feature
            all_features_metadata_entries.append(feature_metadata_entry)
        return (all_features, all_features_metadata_entries)

def get_list_of_feature_types(self) -> List[Type[AbstractModelFeature]]:
    """
        :return all features that are computed by the builders
        """
    return [builder.get_feature_type() for builder in self._feature_builders]

def get_list_of_target_types(self) -> List[Type[AbstractModelFeature]]:
    """
        :return all targets that are computed by the builders
        """
    return [builder.get_feature_type() for builder in self._target_builders]

def extract_initial_offset(scenario: AbstractScenario) -> npt.NDArray[np.float32]:
    """
    Return offset
    :param scenario: for which offset should be computed
    :return: offset of type [x, y, heading]
    """
    initial_ego_pose = ego_pose_to_array(scenario.get_ego_state_at_iteration(0))
    initial_offset: npt.NDArray[np.float32] = np.array([initial_ego_pose[0], initial_ego_pose[1], 0.0])
    return initial_offset

def extract_ego_trajectory(scenario: AbstractScenario, shorten_end_of_scenario: int, offset_start_of_scenario: int=0, subtract_initial_pose_offset: bool=True) -> Trajectory:
    """
    Extract ego trajectory from scenario
    :param scenario: for which ego trajectory should be extracted
    :param shorten_end_of_scenario: future poses
    :param offset_start_of_scenario: future poses
    :param subtract_initial_pose_offset: subtract offset from initial ego pose
    :return: Ego Trajectory
    """
    iteration_end = scenario.get_number_of_iterations() - shorten_end_of_scenario
    iteration_start = offset_start_of_scenario
    number_of_scenes = iteration_end - iteration_start
    trajectory_poses = np.zeros((number_of_scenes, Trajectory.state_size()))
    for index, index_in_scenario in enumerate(np.arange(iteration_start, iteration_end)):
        ego_pose = scenario.get_ego_state_at_iteration(index_in_scenario)
        trajectory_poses[index] = ego_pose_to_array(ego_pose)
    if subtract_initial_pose_offset:
        initial_offset = extract_initial_offset(scenario)
        trajectory_poses = trajectory_poses - initial_offset
    return Trajectory(data=trajectory_poses.astype(np.float32))

class GenericAgentsFeatureBuilder(ScriptableFeatureBuilder):
    """Builder for constructing agent features during training and simulation."""

    def __init__(self, agent_features: List[str], trajectory_sampling: TrajectorySampling) -> None:
        """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        """
        super().__init__()
        self.agent_features = agent_features
        self.num_past_poses = trajectory_sampling.num_poses
        self.past_time_horizon = trajectory_sampling.time_horizon
        self._agents_states_dim = GenericAgents.agents_states_dim()
        if 'EGO' in self.agent_features:
            raise AssertionError('EGO not valid agents feature type!')
        for feature_name in self.agent_features:
            if feature_name not in TrackedObjectType._member_names_:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'generic_agents'

    @torch.jit.unused
    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return GenericAgents

    @torch.jit.unused
    def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        anchor_ego_state = scenario.initial_ego_state
        past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
        sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
        time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
        present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
        past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
        sampled_past_observations = past_tracked_objects + [present_tracked_objects]
        assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
        assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_scriptable_input_from_simulation(self, current_input: PlannerInput) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the simulation input
        :param current_input: planner input from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        history = current_input.history
        assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
        present_ego_state, present_observation = history.current_state
        past_observations = history.observations[:-1]
        past_ego_states = history.ego_states[:-1]
        assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
        indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
        try:
            sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
            sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
        except IndexError:
            raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
        sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
        sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
        time_stamps = [state.time_point for state in sampled_past_ego_states]
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> GenericAgents:
        """Inherited, see superclass."""
        with torch.no_grad():
            tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_scenario(scenario)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> GenericAgents:
        """Inherited, see superclass."""
        with torch.no_grad():
            tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_simulation(current_input)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, past_ego_states: List[EgoState], past_time_stamps: List[TimePoint], past_tracked_objects: List[TrackedObjects]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Packs the provided objects into tensors to be used with the scriptable core of the builder.
        :param past_ego_states: The past states of the ego vehicle.
        :param past_time_stamps: The past time stamps of the input data.
        :param past_tracked_objects: The past tracked objects.
        :return: The packed tensors.
        """
        list_tensor_data: Dict[str, List[torch.Tensor]] = {}
        past_ego_states_tensor = sampled_past_ego_states_to_tensor(past_ego_states)
        past_time_stamps_tensor = sampled_past_timestamps_to_tensor(past_time_stamps)
        for feature_name in self.agent_features:
            past_tracked_objects_tensor_list = sampled_tracked_objects_to_tensor_list(past_tracked_objects, TrackedObjectType[feature_name])
            list_tensor_data[f'past_tracked_objects.{feature_name}'] = past_tracked_objects_tensor_list
        return ({'past_ego_states': past_ego_states_tensor, 'past_time_stamps': past_time_stamps_tensor}, list_tensor_data, {})

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> GenericAgents:
        """
        Unpacks the data returned from the scriptable core into an GenericAgents feature class.
        :param tensor_data: The tensor data output from the scriptable core.
        :param list_tensor_data: The List[tensor] data output from the scriptable core.
        :param list_tensor_data: The List[List[tensor]] data output from the scriptable core.
        :return: The packed GenericAgents object.
        """
        ego_features = [list_tensor_data['generic_agents.ego'][0].detach().numpy()]
        agent_features = {}
        for key in list_tensor_data:
            if key.startswith('generic_agents.agents.'):
                feature_name = key[len('generic_agents.agents.'):]
                agent_features[feature_name] = [list_tensor_data[key][0].detach().numpy()]
        return GenericAgents(ego=ego_features, agents=agent_features)

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Inherited. See interface.
        """
        output_dict: Dict[str, torch.Tensor] = {}
        output_list_dict: Dict[str, List[torch.Tensor]] = {}
        output_list_list_dict: Dict[str, List[List[torch.Tensor]]] = {}
        ego_history: torch.Tensor = tensor_data['past_ego_states']
        time_stamps: torch.Tensor = tensor_data['past_time_stamps']
        anchor_ego_state = ego_history[-1, :].squeeze()
        ego_tensor = build_generic_ego_features_from_tensor(ego_history, reverse=True)
        output_list_dict['generic_agents.ego'] = [ego_tensor]
        for feature_name in self.agent_features:
            if f'past_tracked_objects.{feature_name}' in list_tensor_data:
                agents: List[torch.Tensor] = list_tensor_data[f'past_tracked_objects.{feature_name}']
                agent_history = filter_agents_tensor(agents, reverse=True)
                if agent_history[-1].shape[0] == 0:
                    agents_tensor: torch.Tensor = torch.zeros((len(agent_history), 0, self._agents_states_dim)).float()
                else:
                    padded_agent_states = pad_agent_states(agent_history, reverse=True)
                    local_coords_agent_states = convert_absolute_quantities_to_relative(padded_agent_states, anchor_ego_state)
                    yaw_rate_horizon = compute_yaw_rate_from_state_tensors(padded_agent_states, time_stamps)
                    agents_tensor = pack_agents_tensor(local_coords_agent_states, yaw_rate_horizon)
                output_list_dict[f'generic_agents.agents.{feature_name}'] = [agents_tensor]
        return (output_dict, output_list_dict, output_list_list_dict)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Inherited. See interface.
        """
        return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses), 'agent_features': ','.join(self.agent_features)}}

@torch.jit.unused
def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
    anchor_ego_state = scenario.initial_ego_state
    past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
    sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
    time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
    present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
    past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
    sampled_past_observations = past_tracked_objects + [present_tracked_objects]
    assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
    assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
    tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
    return (tensor, list_tensor, list_list_tensor)

@torch.jit.unused
def get_scriptable_input_from_simulation(self, current_input: PlannerInput) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        Extract the input for the scriptable forward method from the simulation input
        :param current_input: planner input from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
    history = current_input.history
    assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
    present_ego_state, present_observation = history.current_state
    past_observations = history.observations[:-1]
    past_ego_states = history.ego_states[:-1]
    assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
    indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
    try:
        sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
        sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
    except IndexError:
        raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
    sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
    sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
    time_stamps = [state.time_point for state in sampled_past_ego_states]
    tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
    return (tensor, list_tensor, list_list_tensor)

@torch.jit.unused
def get_features_from_scenario(self, scenario: AbstractScenario) -> GenericAgents:
    """Inherited, see superclass."""
    with torch.no_grad():
        tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_scenario(scenario)
        tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
        return output

@torch.jit.unused
def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> GenericAgents:
    """Inherited, see superclass."""
    with torch.no_grad():
        tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_simulation(current_input)
        tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
        return output

class VectorMapFeatureBuilder(ScriptableFeatureBuilder):
    """
    Feature builder for constructing map features in a vector-representation.
    """

    def __init__(self, radius: float, connection_scales: Optional[List[int]]=None) -> None:
        """
        Initialize vector map builder with configuration parameters.
        :param radius:  The query radius scope relative to the current ego-pose.
        :param connection_scales: Connection scales to generate. Use the 1-hop connections if it's left empty.
        :return: Vector map data including lane segment coordinates and connections within the given range.
        """
        super().__init__()
        self._radius = radius
        self._connection_scales = connection_scales

    @torch.jit.unused
    def get_feature_type(self) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return VectorMap

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'vector_map'

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorMap:
        """Inherited, see superclass."""
        with torch.no_grad():
            ego_state = scenario.initial_ego_state
            ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
            lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(scenario.map_api, ego_coords, self._radius)
            on_route_status = get_on_route_status(scenario.get_route_roadblock_ids(), lane_seg_roadblock_ids)
            traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
            traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
            tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorMap:
        """Inherited, see superclass."""
        with torch.no_grad():
            ego_state = current_input.history.ego_states[-1]
            ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
            lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(initialization.map_api, ego_coords, self._radius)
            on_route_status = get_on_route_status(initialization.route_roadblock_ids, lane_seg_roadblock_ids)
            if current_input.traffic_light_data is None:
                raise ValueError('Cannot build VectorMap feature. PlannerInput.traffic_light_data is None')
            traffic_light_data = current_input.traffic_light_data
            traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
            tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.ignore
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> VectorMap:
        """
        Unpacks the data returned from the scriptable portion of the method into a VectorMap object.
        :param tensor_data: The tensor data to unpack.
        :param list_tensor_data: The List[tensor] data to unpack.
        :param list_list_tensor_data: The List[List[tensor]] data to unpack.
        :return: The unpacked VectorMap.
        """
        multi_scale_connections: Dict[int, torch.Tensor] = {}
        for key in list_tensor_data:
            if key.startswith('vector_map.multi_scale_connections_'):
                multi_scale_connections[int(key[len('vector_map.multi_scale_connections_'):])] = list_tensor_data[key][0].detach().numpy()
        lane_groupings = [t.detach().numpy() for t in list_list_tensor_data['vector_map.lane_groupings'][0]]
        return VectorMap(coords=[list_tensor_data['vector_map.coords'][0].detach().numpy()], lane_groupings=[lane_groupings], multi_scale_connections=[multi_scale_connections], on_route_status=[list_tensor_data['vector_map.on_route_status'][0].detach().numpy()], traffic_light_data=[list_tensor_data['vector_map.traffic_light_data'][0].detach().numpy()])

    @torch.jit.ignore
    def _pack_to_feature_tensor_dict(self, lane_coords: LaneSegmentCoords, lane_conns: LaneSegmentConnections, lane_groupings: LaneSegmentGroupings, lane_on_route_status: LaneOnRouteStatusData, traffic_light_data: LaneSegmentTrafficLightData, anchor_state: StateSE2) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Transforms the provided map and actor state primitives into scriptable types.
        This is to prepare for the scriptable portion of the feature tranform.
        :param lane_coords: The LaneSegmentCoords returned from `get_neighbor_vector_map` to transform.
        :param lane_conns: The LaneSegmentConnections returned from `get_neighbor_vector_map` to transform.
        :param lane_groupings: The LaneSegmentGroupings returned from `get_neighbor_vector_map` to transform.
        :param lane_on_route_status: The LaneOnRouteStatusData returned from `get_neighbor_vector_map` to transform.
        :param traffic_light_data: The LaneSegmentTrafficLightData returned from `get_neighbor_vector_map` to transform.
        :param anchor_state: The ego state to transform to vector.
        """
        lane_segment_coords: torch.tensor = torch.tensor(lane_coords.to_vector(), dtype=torch.float64)
        lane_segment_conns: torch.tensor = torch.tensor(lane_conns.to_vector(), dtype=torch.int64)
        on_route_status: torch.tensor = torch.tensor(lane_on_route_status.to_vector(), dtype=torch.float32)
        traffic_light_array: torch.tensor = torch.tensor(traffic_light_data.to_vector(), dtype=torch.float32)
        lane_segment_groupings: List[torch.tensor] = []
        for lane_grouping in lane_groupings.to_vector():
            lane_segment_groupings.append(torch.tensor(lane_grouping, dtype=torch.int64))
        anchor_state_tensor = torch.tensor([anchor_state.x, anchor_state.y, anchor_state.heading], dtype=torch.float64)
        return ({'lane_segment_coords': lane_segment_coords, 'lane_segment_conns': lane_segment_conns, 'on_route_status': on_route_status, 'traffic_light_array': traffic_light_array, 'anchor_state': anchor_state_tensor}, {'lane_segment_groupings': lane_segment_groupings}, {})

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Implemented. See interface.
        """
        lane_segment_coords = tensor_data['lane_segment_coords']
        anchor_state = tensor_data['anchor_state']
        lane_segment_conns = tensor_data['lane_segment_conns']
        if len(lane_segment_conns.shape) == 1:
            if lane_segment_conns.shape[0] == 0:
                lane_segment_conns = torch.zeros((0, 2), device=lane_segment_coords.device, layout=lane_segment_coords.layout, dtype=torch.int64)
            else:
                raise ValueError(f'Unexpected shape for lane_segment_conns: {lane_segment_conns.shape}')
        lane_segment_coords = lane_segment_coords.reshape(-1, 2)
        lane_segment_coords = coordinates_to_local_frame(lane_segment_coords, anchor_state, precision=torch.float64)
        lane_segment_coords = lane_segment_coords.reshape(-1, 2, 2).float()
        if self._connection_scales is not None:
            multi_scale_connections = _generate_multi_scale_connections(lane_segment_conns, self._connection_scales)
        else:
            multi_scale_connections = {1: lane_segment_conns}
        list_list_tensor_output: Dict[str, List[List[torch.Tensor]]] = {'vector_map.lane_groupings': [list_tensor_data['lane_segment_groupings']]}
        list_tensor_output: Dict[str, List[torch.Tensor]] = {'vector_map.coords': [lane_segment_coords], 'vector_map.on_route_status': [tensor_data['on_route_status']], 'vector_map.traffic_light_data': [tensor_data['traffic_light_array']]}
        for key in multi_scale_connections:
            list_tensor_output[f'vector_map.multi_scale_connections_{key}'] = [multi_scale_connections[key]]
        tensor_output: Dict[str, torch.Tensor] = {}
        return (tensor_output, list_tensor_output, list_list_tensor_output)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Implemented. See Interface.
        """
        empty: Dict[str, str] = {}
        return {'neighbor_vector_map': {'radius': str(self._radius)}, 'initial_ego_state': empty}

@torch.jit.unused
def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorMap:
    """Inherited, see superclass."""
    with torch.no_grad():
        ego_state = scenario.initial_ego_state
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(scenario.map_api, ego_coords, self._radius)
        on_route_status = get_on_route_status(scenario.get_route_roadblock_ids(), lane_seg_roadblock_ids)
        traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
        traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
        tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

@torch.jit.unused
def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorMap:
    """Inherited, see superclass."""
    with torch.no_grad():
        ego_state = current_input.history.ego_states[-1]
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(initialization.map_api, ego_coords, self._radius)
        on_route_status = get_on_route_status(initialization.route_roadblock_ids, lane_seg_roadblock_ids)
        if current_input.traffic_light_data is None:
            raise ValueError('Cannot build VectorMap feature. PlannerInput.traffic_light_data is None')
        traffic_light_data = current_input.traffic_light_data
        traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
        tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

class VectorSetMapFeatureBuilder(ScriptableFeatureBuilder):
    """
    Feature builder for constructing map features in a vector set representation, similar to that of
        VectorNet ("VectorNet: Encoding HD Maps and Agent Dynamics from Vectorized Representation").
    """

    def __init__(self, map_features: List[str], max_elements: Dict[str, int], max_points: Dict[str, int], radius: float, interpolation_method: str) -> None:
        """
        Initialize vector set map builder with configuration parameters.
        :param map_features: name of map features to be extracted.
        :param max_elements: maximum number of elements to extract per feature layer.
        :param max_points: maximum number of points per feature to extract per feature layer.
        :param radius:  [m ]The query radius scope relative to the current ego-pose.
        :param interpolation_method: Interpolation method to apply when interpolating to maintain fixed size
            map elements.
        :return: Vector set map data including map element coordinates and traffic light status info.
        """
        super().__init__()
        self.map_features = map_features
        self.max_elements = max_elements
        self.max_points = max_points
        self.radius = radius
        self.interpolation_method = interpolation_method
        self._traffic_light_encoding_dim = LaneSegmentTrafficLightData.encoding_dim()
        for feature_name in self.map_features:
            try:
                VectorFeatureLayer[feature_name]
            except KeyError:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
            if feature_name not in self.max_elements:
                raise RuntimeError(f'Max elements unavailable for {feature_name} feature layer!')
            if feature_name not in self.max_points:
                raise RuntimeError(f'Max points unavailable for {feature_name} feature layer!')

    @torch.jit.unused
    def get_feature_type(self) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return VectorSetMap

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'vector_set_map'

    @torch.jit.unused
    def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        ego_state = scenario.initial_ego_state
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        route_roadblock_ids = scenario.get_route_roadblock_ids()
        traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
        coords, traffic_light_data = get_neighbor_vector_set_map(scenario.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_scriptable_input_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the simulation objects
        :param current_input: planner input from sim
        :param initialization: planner initialization from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        ego_state = current_input.history.ego_states[-1]
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        route_roadblock_ids = initialization.route_roadblock_ids
        if current_input.traffic_light_data is None:
            raise ValueError('Cannot build VectorSetMap feature. PlannerInput.traffic_light_data is None')
        traffic_light_data = current_input.traffic_light_data
        coords, traffic_light_data = get_neighbor_vector_set_map(initialization.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorSetMap:
        """Inherited, see superclass."""
        tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_scenario(scenario)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorSetMap:
        """Inherited, see superclass."""
        tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_simulation(current_input, initialization)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> VectorSetMap:
        """
        Unpacks the data returned from the scriptable portion of the method into a VectorSetMap object.
        :param tensor_data: The tensor data to unpack.
        :param list_tensor_data: The List[tensor] data to unpack.
        :param list_list_tensor_data: The List[List[tensor]] data to unpack.
        :return: The unpacked VectorSetMap.
        """
        coords: Dict[str, List[FeatureDataType]] = {}
        traffic_light_data: Dict[str, List[FeatureDataType]] = {}
        availabilities: Dict[str, List[FeatureDataType]] = {}
        for key in list_tensor_data:
            if key.startswith('vector_set_map.coords.'):
                feature_name = key[len('vector_set_map.coords.'):]
                coords[feature_name] = [list_tensor_data[key][0].detach().numpy()]
            if key.startswith('vector_set_map.traffic_light_data.'):
                feature_name = key[len('vector_set_map.traffic_light_data.'):]
                traffic_light_data[feature_name] = [list_tensor_data[key][0].detach().numpy()]
            if key.startswith('vector_set_map.availabilities.'):
                feature_name = key[len('vector_set_map.availabilities.'):]
                availabilities[feature_name] = [list_tensor_data[key][0].detach().numpy()]
        return VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, coords: Dict[str, MapObjectPolylines], traffic_light_data: Dict[str, LaneSegmentTrafficLightData], anchor_state: StateSE2) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Transforms the provided map and actor state primitives into scriptable types.
        This is to prepare for the scriptable portion of the feature transform.
        :param coords: Dictionary mapping feature name to polyline vector sets.
        :param traffic_light_data: Dictionary mapping feature name to traffic light info corresponding to map elements
            in coords.
        :param anchor_state: The ego state to transform to vector.
        :return
           tensor_data: Packed tensor data.
           list_tensor_data: Packed List[tensor] data.
           list_list_tensor_data: Packed List[List[tensor]] data.
        """
        tensor_data: Dict[str, torch.Tensor] = {}
        anchor_state_tensor = torch.tensor([anchor_state.x, anchor_state.y, anchor_state.heading], dtype=torch.float64)
        tensor_data['anchor_state'] = anchor_state_tensor
        list_tensor_data: Dict[str, List[torch.Tensor]] = {}
        for feature_name, feature_coords in coords.items():
            list_feature_coords: List[torch.Tensor] = []
            for element_coords in feature_coords.to_vector():
                list_feature_coords.append(torch.tensor(element_coords, dtype=torch.float64))
            list_tensor_data[f'coords.{feature_name}'] = list_feature_coords
            if feature_name in traffic_light_data:
                list_feature_tl_data: List[torch.Tensor] = []
                for element_tl_data in traffic_light_data[feature_name].to_vector():
                    list_feature_tl_data.append(torch.tensor(element_tl_data, dtype=torch.float32))
                list_tensor_data[f'traffic_light_data.{feature_name}'] = list_feature_tl_data
        return (tensor_data, list_tensor_data, {})

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Implemented. See interface.
        """
        tensor_output: Dict[str, torch.Tensor] = {}
        list_tensor_output: Dict[str, List[torch.Tensor]] = {}
        list_list_tensor_output: Dict[str, List[List[torch.Tensor]]] = {}
        anchor_state = tensor_data['anchor_state']
        for feature_name in self.map_features:
            if f'coords.{feature_name}' in list_tensor_data:
                feature_coords = list_tensor_data[f'coords.{feature_name}']
                feature_tl_data = [list_tensor_data[f'traffic_light_data.{feature_name}']] if f'traffic_light_data.{feature_name}' in list_tensor_data else None
                coords, tl_data, avails = convert_feature_layer_to_fixed_size(feature_coords, feature_tl_data, self.max_elements[feature_name], self.max_points[feature_name], self._traffic_light_encoding_dim, interpolation=self.interpolation_method if feature_name in [VectorFeatureLayer.LANE.name, VectorFeatureLayer.LEFT_BOUNDARY.name, VectorFeatureLayer.RIGHT_BOUNDARY.name, VectorFeatureLayer.ROUTE_LANES.name] else None)
                coords = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
                list_tensor_output[f'vector_set_map.coords.{feature_name}'] = [coords]
                list_tensor_output[f'vector_set_map.availabilities.{feature_name}'] = [avails]
                if tl_data is not None:
                    list_tensor_output[f'vector_set_map.traffic_light_data.{feature_name}'] = [tl_data[0]]
        return (tensor_output, list_tensor_output, list_list_tensor_output)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Implemented. See Interface.
        """
        empty: Dict[str, str] = {}
        max_elements: List[str] = [f'{feature_name}.{feature_max_elements}' for feature_name, feature_max_elements in self.max_elements.items()]
        max_points: List[str] = [f'{feature_name}.{feature_max_points}' for feature_name, feature_max_points in self.max_points.items()]
        return {'neighbor_vector_set_map': {'radius': str(self.radius), 'interpolation_method': self.interpolation_method, 'map_features': ','.join(self.map_features), 'max_elements': ','.join(max_elements), 'max_points': ','.join(max_points)}, 'initial_ego_state': empty}

@torch.jit.unused
def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
    ego_state = scenario.initial_ego_state
    ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
    route_roadblock_ids = scenario.get_route_roadblock_ids()
    traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
    coords, traffic_light_data = get_neighbor_vector_set_map(scenario.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
    tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
    return (tensor, list_tensor, list_list_tensor)

@torch.jit.unused
def get_scriptable_input_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
    """
        Extract the input for the scriptable forward method from the simulation objects
        :param current_input: planner input from sim
        :param initialization: planner initialization from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
    ego_state = current_input.history.ego_states[-1]
    ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
    route_roadblock_ids = initialization.route_roadblock_ids
    if current_input.traffic_light_data is None:
        raise ValueError('Cannot build VectorSetMap feature. PlannerInput.traffic_light_data is None')
    traffic_light_data = current_input.traffic_light_data
    coords, traffic_light_data = get_neighbor_vector_set_map(initialization.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
    tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
    return (tensor, list_tensor, list_list_tensor)

@torch.jit.unused
def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorSetMap:
    """Inherited, see superclass."""
    tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_scenario(scenario)
    tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
    return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

@torch.jit.unused
def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorSetMap:
    """Inherited, see superclass."""
    tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_simulation(current_input, initialization)
    tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
    return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

class AgentsFeatureBuilder(ScriptableFeatureBuilder):
    """Builder for constructing agent features during training and simulation."""

    def __init__(self, trajectory_sampling: TrajectorySampling, object_type: TrackedObjectType=TrackedObjectType.VEHICLE) -> None:
        """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        :param object_type: Type of agents (TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN) set to TrackedObjectType.VEHICLE by default
        """
        super().__init__()
        if object_type not in [TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]:
            raise ValueError(f"The model's been tested just for vehicles and pedestrians types, but the provided object_type is {object_type}.")
        self.num_past_poses = trajectory_sampling.num_poses
        self.past_time_horizon = trajectory_sampling.time_horizon
        self.object_type = object_type
        self._agents_states_dim = Agents.agents_states_dim()

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'agents'

    @torch.jit.unused
    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return Agents

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> Agents:
        """Inherited, see superclass."""
        with torch.no_grad():
            anchor_ego_state = scenario.initial_ego_state
            past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
            sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
            time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
            present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
            past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
            sampled_past_observations = past_tracked_objects + [present_tracked_objects]
            assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
            assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Agents:
        """Inherited, see superclass."""
        with torch.no_grad():
            history = current_input.history
            assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
            present_ego_state, present_observation = history.current_state
            past_observations = history.observations[:-1]
            past_ego_states = history.ego_states[:-1]
            assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
            indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
            try:
                sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
                sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
            except IndexError:
                raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
            sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
            sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
            time_stamps = [state.time_point for state in sampled_past_ego_states]
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, past_ego_states: List[EgoState], past_time_stamps: List[TimePoint], past_tracked_objects: List[TrackedObjects]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Packs the provided objects into tensors to be used with the scriptable core of the builder.
        :param past_ego_states: The past states of the ego vehicle.
        :param past_time_stamps: The past time stamps of the input data.
        :param past_tracked_objects: The past tracked objects.
        :return: The packed tensors.
        """
        past_ego_states_tensor = sampled_past_ego_states_to_tensor(past_ego_states)
        past_time_stamps_tensor = sampled_past_timestamps_to_tensor(past_time_stamps)
        past_tracked_objects_tensor_list = sampled_tracked_objects_to_tensor_list(past_tracked_objects=past_tracked_objects, object_type=self.object_type)
        return ({'past_ego_states': past_ego_states_tensor, 'past_time_stamps': past_time_stamps_tensor}, {'past_tracked_objects': past_tracked_objects_tensor_list}, {})

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Agents:
        """
        Unpacks the data returned from the scriptable core into an Agents feature class.
        :param tensor_data: The tensor data output from the scriptable core.
        :param list_tensor_data: The List[tensor] data output from the scriptable core.
        :param list_tensor_data: The List[List[tensor]] data output from the scriptable core.
        :return: The packed Agents object.
        """
        ego_features = [list_tensor_data['agents.ego'][0].detach().numpy()]
        agent_features = [list_tensor_data['agents.agents'][0].detach().numpy()]
        return Agents(ego=ego_features, agents=agent_features)

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Inherited. See interface.
        """
        ego_history: torch.Tensor = tensor_data['past_ego_states']
        time_stamps: torch.Tensor = tensor_data['past_time_stamps']
        agents: List[torch.Tensor] = list_tensor_data['past_tracked_objects']
        anchor_ego_state = ego_history[-1, :].squeeze()
        agent_history = filter_agents_tensor(agents, reverse=True)
        if agent_history[-1].shape[0] == 0:
            agents_tensor: torch.Tensor = torch.zeros((len(agent_history), 0, self._agents_states_dim)).float()
        else:
            padded_agent_states = pad_agent_states(agent_history, reverse=True)
            local_coords_agent_states = convert_absolute_quantities_to_relative(padded_agent_states, anchor_ego_state)
            yaw_rate_horizon = compute_yaw_rate_from_state_tensors(padded_agent_states, time_stamps)
            agents_tensor = pack_agents_tensor(local_coords_agent_states, yaw_rate_horizon)
        ego_tensor = build_ego_features_from_tensor(ego_history, reverse=True)
        output_dict: Dict[str, torch.Tensor] = {}
        output_list_dict: Dict[str, List[torch.Tensor]] = {'agents.ego': [ego_tensor], 'agents.agents': [agents_tensor]}
        output_list_list_dict: Dict[str, List[List[torch.Tensor]]] = {}
        return (output_dict, output_list_dict, output_list_list_dict)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Inherited. See interface.
        """
        return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses)}}

@torch.jit.unused
def get_features_from_scenario(self, scenario: AbstractScenario) -> Agents:
    """Inherited, see superclass."""
    with torch.no_grad():
        anchor_ego_state = scenario.initial_ego_state
        past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
        sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
        time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
        present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
        past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
        sampled_past_observations = past_tracked_objects + [present_tracked_objects]
        assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
        assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
        tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
        return output

@torch.jit.unused
def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Agents:
    """Inherited, see superclass."""
    with torch.no_grad():
        history = current_input.history
        assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
        present_ego_state, present_observation = history.current_state
        past_observations = history.observations[:-1]
        past_ego_states = history.ego_states[:-1]
        assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
        indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
        try:
            sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
            sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
        except IndexError:
            raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
        sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
        sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
        time_stamps = [state.time_point for state in sampled_past_ego_states]
        tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
        output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
        return output

def get_neighbor_vector_set_map(map_api: AbstractMap, map_features: List[str], point: Point2D, radius: float, route_roadblock_ids: List[str], traffic_light_statuses_over_time: List[TrafficLightStatuses]) -> Tuple[Dict[str, MapObjectPolylines], List[Dict[str, LaneSegmentTrafficLightData]]]:
    """
    Extract neighbor vector set map information around ego vehicle.
    :param map_api: map to perform extraction on.
    :param map_features: Name of map features to extract.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about vector map query range.
    :param route_roadblock_ids: List of ids of roadblocks/roadblock connectors (lane groups) within goal route.
    :param traffic_light_statuses_over_time: A list of available traffic light statuses data, indexed by time step.
    :return:
        coords: Dictionary mapping feature name to polyline vector sets.
        traffic_light_data: Dictionary mapping feature name to traffic light info corresponding to map elements
            in coords.
    :raise ValueError: if provided feature_name is not a valid VectorFeatureLayer.
    """
    coords: Dict[str, MapObjectPolylines] = {}
    feature_layers: List[VectorFeatureLayer] = []
    traffic_light_data_over_time: List[Dict[str, LaneSegmentTrafficLightData]] = []
    for feature_name in map_features:
        try:
            feature_layers.append(VectorFeatureLayer[feature_name])
        except KeyError:
            raise ValueError(f'Object representation for layer: {feature_name} is unavailable')
    if VectorFeatureLayer.LANE in feature_layers:
        lanes_mid, lanes_left, lanes_right, lane_ids = get_lane_polylines(map_api, point, radius)
        coords[VectorFeatureLayer.LANE.name] = lanes_mid
        if VectorFeatureLayer.LEFT_BOUNDARY in feature_layers:
            coords[VectorFeatureLayer.LEFT_BOUNDARY.name] = MapObjectPolylines(lanes_left.polylines)
        if VectorFeatureLayer.RIGHT_BOUNDARY in feature_layers:
            coords[VectorFeatureLayer.RIGHT_BOUNDARY.name] = MapObjectPolylines(lanes_right.polylines)
        for traffic_lights in traffic_light_statuses_over_time:
            traffic_light_data_at_t: Dict[str, LaneSegmentTrafficLightData] = {}
            traffic_light_data_at_t[VectorFeatureLayer.LANE.name] = get_traffic_light_encoding(lane_ids, traffic_lights.traffic_lights)
            traffic_light_data_over_time.append(traffic_light_data_at_t)
    if VectorFeatureLayer.ROUTE_LANES in feature_layers:
        route_polylines = get_route_lane_polylines_from_roadblock_ids(map_api, point, radius, route_roadblock_ids)
        coords[VectorFeatureLayer.ROUTE_LANES.name] = route_polylines
    for feature_layer in feature_layers:
        if feature_layer in VectorFeatureLayerMapping.available_polygon_layers():
            polygons = get_map_object_polygons(map_api, point, radius, VectorFeatureLayerMapping.semantic_map_layer(feature_layer))
            coords[feature_layer.name] = polygons
    return (coords, traffic_light_data_over_time)

class TestAgentsFeatureBuilder(unittest.TestCase):
    """Test builder that constructs agent features during training and simulation."""

    def setUp(self) -> None:
        """
        Set up test case.
        """
        self.batch_size = 1
        self.past_time_horizon = 4.0
        self.num_past_poses = 4
        self.num_total_past_poses = self.num_past_poses + 1

    @given(number_of_detections=st.sampled_from([0, 10]), feature_builder_type=st.sampled_from([TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]))
    def test_agent_feature_builder(self, number_of_detections: int, feature_builder_type: TrackedObjectType) -> None:
        """
        Test AgentFeatureBuilder with and without agents in the scene for both pedestrian and vehicles
        """
        feature_builder = AgentsFeatureBuilder(TrajectorySampling(self.num_past_poses, self.past_time_horizon), feature_builder_type)
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=number_of_detections, tracked_object_types=[TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN])
        feature = feature_builder.get_features_from_scenario(scenario)
        self.assertEqual(type(feature), Agents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), Agents.ego_state_dim())
        self.assertEqual(len(feature.agents), self.batch_size)
        self.assertEqual(len(feature.agents[0]), self.num_total_past_poses)
        self.assertEqual(feature.agents[0].shape[1], number_of_detections)
        self.assertEqual(feature.agents[0].shape[2], Agents.agents_states_dim())

    @given(feature_builder_type=st.sampled_from([TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]))
    def test_get_feature_from_simulation(self, feature_builder_type: TrackedObjectType) -> None:
        """
        Test get feature from simulation
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=10, tracked_object_types=[TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN])
        mock_meta_data = PlannerInitialization(map_api=MockAbstractMap(), route_roadblock_ids=None, mission_goal=StateSE2(0, 0, 0))
        ego_past_states = list(scenario.get_ego_past_trajectory(iteration=0, num_samples=10, time_horizon=5))
        ego_initial_state = scenario.initial_ego_state
        ego_history = ego_past_states + [ego_initial_state]
        past_observations = list(scenario.get_past_tracked_objects(iteration=0, num_samples=10, time_horizon=5))
        initial_observation = scenario.initial_tracked_objects
        observation_history = past_observations + [initial_observation]
        history = SimulationHistoryBuffer.initialize_from_list(len(ego_history), ego_history, observation_history, scenario.database_interval)
        current_input = PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=scenario.get_traffic_light_status_at_iteration(0))
        feature_builder = AgentsFeatureBuilder(TrajectorySampling(self.num_past_poses, self.past_time_horizon), feature_builder_type)
        feature = feature_builder.get_features_from_simulation(current_input=current_input, initialization=mock_meta_data)
        self.assertEqual(type(feature), Agents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), Agents.ego_state_dim())
        self.assertEqual(len(feature.agents), self.batch_size)
        self.assertEqual(len(feature.agents[0]), self.num_total_past_poses)
        self.assertEqual(feature.agents[0].shape[1], 10)
        self.assertEqual(feature.agents[0].shape[2], Agents.agents_states_dim())

    @given(feature_builder_type=st.sampled_from([TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]))
    @settings(deadline=1000)
    def test_agents_feature_builder_scripts_properly(self, feature_builder_type: TrackedObjectType) -> None:
        """
        Tests that the Agents Feature Builder scripts properly
        """
        feature_builder = AgentsFeatureBuilder(TrajectorySampling(self.num_past_poses, self.past_time_horizon), feature_builder_type)
        config = feature_builder.precomputed_feature_config()
        for expected_key in ['past_ego_states', 'past_time_stamps', 'past_tracked_objects']:
            self.assertIn(expected_key, config)
            config_dict = config[expected_key]
            self.assertEqual(len(config_dict), 3)
            self.assertEqual(0, int(config_dict['iteration']))
            self.assertEqual(self.num_past_poses, int(config_dict['num_samples']))
            self.assertEqual(self.past_time_horizon, int(float(config_dict['time_horizon'])))
        num_frames = 5
        num_agents = 3
        ego_dim = EgoInternalIndex.dim()
        agent_dim = AgentInternalIndex.dim()
        past_ego_states = torch.zeros((num_frames, ego_dim), dtype=torch.float32)
        past_timestamps = torch.tensor([i * 50 for i in range(num_frames)], dtype=torch.int64)
        past_tracked_objects = [torch.ones((num_agents, agent_dim), dtype=torch.float32) for _ in range(num_frames)]
        for i in range(num_frames):
            for j in range(num_agents):
                past_tracked_objects[i][j, :] *= j + 1
        tensor_data = {'past_ego_states': past_ego_states, 'past_time_stamps': past_timestamps}
        list_tensor_data = {'past_tracked_objects': past_tracked_objects}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_builder = torch.jit.script(feature_builder)
        scripted_tensors, scripted_list_tensors, scripted_list_list_tensors = scripted_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        py_tensors, py_list_tensors, py_list_list_tensors = feature_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        self.assertEqual(0, len(scripted_tensors))
        self.assertEqual(0, len(py_tensors))
        self.assertEqual(len(scripted_list_tensors), len(py_list_tensors))
        for key in py_list_tensors:
            scripted_list = scripted_list_tensors[key]
            py_list = py_list_tensors[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                scripted = scripted_list[i]
                py = py_list[i]
                torch.testing.assert_allclose(py, scripted, atol=0.01, rtol=0.01)
        self.assertEqual(0, len(scripted_list_list_tensors))
        self.assertEqual(0, len(py_list_list_tensors))

@given(number_of_detections=st.sampled_from([0, 10]), feature_builder_type=st.sampled_from([TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]))
def test_agent_feature_builder(self, number_of_detections: int, feature_builder_type: TrackedObjectType) -> None:
    """
        Test AgentFeatureBuilder with and without agents in the scene for both pedestrian and vehicles
        """
    feature_builder = AgentsFeatureBuilder(TrajectorySampling(self.num_past_poses, self.past_time_horizon), feature_builder_type)
    scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=number_of_detections, tracked_object_types=[TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN])
    feature = feature_builder.get_features_from_scenario(scenario)
    self.assertEqual(type(feature), Agents)
    self.assertEqual(feature.batch_size, self.batch_size)
    self.assertEqual(len(feature.ego), self.batch_size)
    self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
    self.assertEqual(len(feature.ego[0][0]), Agents.ego_state_dim())
    self.assertEqual(len(feature.agents), self.batch_size)
    self.assertEqual(len(feature.agents[0]), self.num_total_past_poses)
    self.assertEqual(feature.agents[0].shape[1], number_of_detections)
    self.assertEqual(feature.agents[0].shape[2], Agents.agents_states_dim())

@given(feature_builder_type=st.sampled_from([TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]))
def test_get_feature_from_simulation(self, feature_builder_type: TrackedObjectType) -> None:
    """
        Test get feature from simulation
        """
    scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=10, tracked_object_types=[TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN])
    mock_meta_data = PlannerInitialization(map_api=MockAbstractMap(), route_roadblock_ids=None, mission_goal=StateSE2(0, 0, 0))
    ego_past_states = list(scenario.get_ego_past_trajectory(iteration=0, num_samples=10, time_horizon=5))
    ego_initial_state = scenario.initial_ego_state
    ego_history = ego_past_states + [ego_initial_state]
    past_observations = list(scenario.get_past_tracked_objects(iteration=0, num_samples=10, time_horizon=5))
    initial_observation = scenario.initial_tracked_objects
    observation_history = past_observations + [initial_observation]
    history = SimulationHistoryBuffer.initialize_from_list(len(ego_history), ego_history, observation_history, scenario.database_interval)
    current_input = PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=scenario.get_traffic_light_status_at_iteration(0))
    feature_builder = AgentsFeatureBuilder(TrajectorySampling(self.num_past_poses, self.past_time_horizon), feature_builder_type)
    feature = feature_builder.get_features_from_simulation(current_input=current_input, initialization=mock_meta_data)
    self.assertEqual(type(feature), Agents)
    self.assertEqual(feature.batch_size, self.batch_size)
    self.assertEqual(len(feature.ego), self.batch_size)
    self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
    self.assertEqual(len(feature.ego[0][0]), Agents.ego_state_dim())
    self.assertEqual(len(feature.agents), self.batch_size)
    self.assertEqual(len(feature.agents[0]), self.num_total_past_poses)
    self.assertEqual(feature.agents[0].shape[1], 10)
    self.assertEqual(feature.agents[0].shape[2], Agents.agents_states_dim())

class MockTorchModuleWrapperTrajectoryPredictor(TorchModuleWrapper):
    """
    A simple implementation of the TorchModuleWrapper interface for use with unit tests.
    It validates the input tensor, and returns a trajectory object.
    """

    def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], raise_on_builder_access: bool=False, raise_on_forward: bool=False, expected_forward_tensor: Optional[torch.Tensor]=None, data_tensor_to_return: Optional[torch.Tensor]=None) -> None:
        """
        The init method.
        :param future_trajectory_sampling: The TrajectorySampling to use.
        :param feature_builders: The feature builders used by the model.
        :param target_builders: The target builders used by the model.
        :param raise_on_builder_access: If set, an exeption will be raised if the builders are accessed.
        :param raise_on_forward: If set, an exception will be raised if the forward function is called.
        :param expected_forward_tensor: The tensor that is expected to be provided to to the forward function.
        :param data_tensor_to_return: The tensor that expected to be returned from the forward function.
        """
        super().__init__(future_trajectory_sampling, feature_builders, target_builders)
        self.raise_on_builder_access = raise_on_builder_access
        self.raise_on_forward = raise_on_forward
        self.expected_forward_tensor = expected_forward_tensor
        self.data_tensor_to_return = data_tensor_to_return
        if not self.raise_on_builder_access:
            if self.feature_builders is None or len(self.feature_builders) == 0:
                raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length feature builders.\n                    This is likely a misconfigured unit test.\n                    '))
            if self.target_builders is None or len(self.target_builders) == 0:
                raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length target builders.\n                    This is likely a misconfigured unit test.\n                    '))
        if not self.raise_on_forward:
            if self.expected_forward_tensor is None:
                raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None expected_forward_tensor.\n                    This is likely a misconfigured unit test.\n                    '))
            if self.data_tensor_to_return is None:
                raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None data_tensor_to_return.\n                    This is likely a misconfigured unit test.\n                    '))

    def get_list_of_required_feature(self) -> List[AbstractFeatureBuilder]:
        """
        Implemented. See interface.
        """
        if self.raise_on_builder_access:
            raise ValueError('get_list_of_required_feature() called when raise_on_builder_access set.')
        result: List[AbstractFeatureBuilder] = TorchModuleWrapper.get_list_of_required_feature(self)
        return result

    def get_list_of_computed_target(self) -> List[AbstractTargetBuilder]:
        """
        Implemented. See interface.
        """
        if self.raise_on_builder_access:
            raise ValueError('get_list_of_computed_target() called when raise_on_builder_access set.')
        result: List[AbstractTargetBuilder] = TorchModuleWrapper.get_list_of_computed_target(self)
        return result

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Implemented. See interface.
        """
        if self.raise_on_forward:
            raise ValueError('forward() called when raise_on_forward set.')
        self._validate_input_feature(features)
        return {'trajectory': Trajectory(data=self.data_tensor_to_return)}

    def _validate_input_feature(self, features: FeaturesType) -> None:
        """
        Validates that the proper feature is provided.
        Raises an exception if it is not.
        :param features: The feature provided to the model.
        """
        if 'MockFeature' not in features:
            raise ValueError(f'MockFeature not in provided features. Available keys: {sorted(list(features.keys()))}')
        if len(features) != 1:
            raise ValueError(f'Expected a single feature. Instead got {len(features)}: {sorted(list(features.keys()))}')
        mock_feature = features['MockFeature']
        if not isinstance(mock_feature, MockFeature):
            raise ValueError(f'Expected feature of type MockFeature, but got {type(mock_feature)}')
        mock_feature_data = mock_feature.data
        torch.testing.assert_close(mock_feature_data, self.expected_forward_tensor)

def _validate_input_feature(self, features: FeaturesType) -> None:
    """
        Validates that the proper feature is provided.
        Raises an exception if it is not.
        :param features: The feature provided to the model.
        """
    if 'MockFeature' not in features:
        raise ValueError(f'MockFeature not in provided features. Available keys: {sorted(list(features.keys()))}')
    if len(features) != 1:
        raise ValueError(f'Expected a single feature. Instead got {len(features)}: {sorted(list(features.keys()))}')
    mock_feature = features['MockFeature']
    if not isinstance(mock_feature, MockFeature):
        raise ValueError(f'Expected feature of type MockFeature, but got {type(mock_feature)}')
    mock_feature_data = mock_feature.data
    torch.testing.assert_close(mock_feature_data, self.expected_forward_tensor)

class TestVectorUtils(unittest.TestCase):
    """Test vector building utility functions."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        scenario = MockAbstractScenario()
        ego_state = scenario.initial_ego_state
        self.ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        self.map_api = scenario.map_api
        self.route_roadblock_ids = scenario.get_route_roadblock_ids()
        self.traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
        self.radius = 35
        self.map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
        self._num_past_poses = 1
        self._past_time_horizon = 1.0
        self._num_future_poses = 5
        self._future_time_horizon = 5.0
        current_tl = [TrafficLightStatuses(list(scenario.get_traffic_light_status_at_iteration(iteration=0)))]
        past_tl = scenario.get_past_traffic_light_status_history(iteration=0, num_samples=self._num_past_poses, time_horizon=self._past_time_horizon)
        future_tl = scenario.get_future_traffic_light_status_history(iteration=0, num_samples=self._num_future_poses, time_horizon=self._future_time_horizon)
        past_tl_list = list(past_tl)
        future_tl_list = list(future_tl)
        self.traffic_light_data_over_time = past_tl_list + current_tl + future_tl_list

    def test_prune_route_by_connectivity(self) -> None:
        """
        Test pruning route roadblock ids by those within query radius (specified in roadblock_ids)
        maintaining connectivity.
        """
        route_roadblock_ids = ['-1', '0', '1', '2', '3']
        roadblock_ids = {'0', '1', '3'}
        pruned_route_roadblock_ids = prune_route_by_connectivity(route_roadblock_ids, roadblock_ids)
        self.assertEqual(pruned_route_roadblock_ids, ['0', '1'])

    def test_get_lane_polylines(self) -> None:
        """
        Test extracting lane/lane connector baseline path and boundary polylines from given map api.
        """
        lanes_mid, lanes_left, lanes_right, lane_ids = get_lane_polylines(self.map_api, self.ego_coords, self.radius)
        assert type(lanes_mid) == MapObjectPolylines
        assert type(lanes_left) == MapObjectPolylines
        assert type(lanes_right) == MapObjectPolylines
        assert type(lane_ids) == LaneSegmentLaneIDs

    def test_get_map_object_polygons(self) -> None:
        """
        Test extracting map object polygons from map.
        """
        for layer in [SemanticMapLayer.CROSSWALK, SemanticMapLayer.STOP_LINE]:
            polygons = get_map_object_polygons(self.map_api, self.ego_coords, self.radius, layer)
            assert type(polygons) == MapObjectPolylines

    def test_get_route_polygon_from_roadblock_ids(self) -> None:
        """
        Test extracting route polygon from map given list of roadblock ids.
        """
        route = get_route_polygon_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
        assert type(route) == MapObjectPolylines

    def test_get_route_lane_polylines_from_roadblock_ids(self) -> None:
        """
        Test extracting route lane polylines from map given list of roadblock ids.
        """
        route = get_route_lane_polylines_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
        assert type(route) == MapObjectPolylines

    def test_get_on_route_status(self) -> None:
        """
        Test identifying whether given roadblock lie within goal route.
        """
        route_roadblock_ids = ['0']
        roadblock_ids = LaneSegmentRoadBlockIDs(['0', '1'])
        on_route_status = get_on_route_status(route_roadblock_ids, roadblock_ids)
        assert type(on_route_status) == LaneOnRouteStatusData
        assert len(on_route_status.on_route_status) == LaneOnRouteStatusData.encoding_dim()
        assert on_route_status.on_route_status[0] == on_route_status.encode(OnRouteStatusType.ON_ROUTE)
        assert on_route_status.on_route_status[1] == on_route_status.encode(OnRouteStatusType.OFF_ROUTE)

    def test_get_neighbor_vector_map(self) -> None:
        """
        Test extracting neighbor vector map information from map api.
        """
        lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(self.map_api, self.ego_coords, self.radius)
        assert type(lane_seg_coords) == LaneSegmentCoords
        assert type(lane_seg_conns) == LaneSegmentConnections
        assert type(lane_seg_groupings) == LaneSegmentGroupings
        assert type(lane_seg_lane_ids) == LaneSegmentLaneIDs
        assert type(lane_seg_roadblock_ids) == LaneSegmentRoadBlockIDs

    def test_get_neighbor_vector_set_map(self) -> None:
        """
        Test extracting neighbor vector set map information from map api.
        """
        coords, traffic_light_data = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, [TrafficLightStatuses(self.traffic_light_data)])
        for feature_name in self.map_features:
            assert feature_name in coords
            assert type(coords[feature_name]) == MapObjectPolylines
        assert len(traffic_light_data) == 1
        assert 'LANE' in traffic_light_data[0]
        assert type(traffic_light_data[0]['LANE']) == LaneSegmentTrafficLightData

    def test_get_neighbor_vector_set_map_for_time_horizon(self) -> None:
        """
        Test extracting neighbor vector set map information from map api.
        """
        coords, traffic_light_data_list = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, self.traffic_light_data_over_time)
        for feature_name in self.map_features:
            assert feature_name in coords
            assert type(coords[feature_name]) == MapObjectPolylines
        for traffic_light_data in traffic_light_data_list:
            assert 'LANE' in traffic_light_data
            assert type(traffic_light_data['LANE']) == LaneSegmentTrafficLightData

def setUp(self) -> None:
    """
        Initializes DB
        """
    scenario = MockAbstractScenario()
    ego_state = scenario.initial_ego_state
    self.ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
    self.map_api = scenario.map_api
    self.route_roadblock_ids = scenario.get_route_roadblock_ids()
    self.traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
    self.radius = 35
    self.map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
    self._num_past_poses = 1
    self._past_time_horizon = 1.0
    self._num_future_poses = 5
    self._future_time_horizon = 5.0
    current_tl = [TrafficLightStatuses(list(scenario.get_traffic_light_status_at_iteration(iteration=0)))]
    past_tl = scenario.get_past_traffic_light_status_history(iteration=0, num_samples=self._num_past_poses, time_horizon=self._past_time_horizon)
    future_tl = scenario.get_future_traffic_light_status_history(iteration=0, num_samples=self._num_future_poses, time_horizon=self._future_time_horizon)
    past_tl_list = list(past_tl)
    future_tl_list = list(future_tl)
    self.traffic_light_data_over_time = past_tl_list + current_tl + future_tl_list

def test_get_lane_polylines(self) -> None:
    """
        Test extracting lane/lane connector baseline path and boundary polylines from given map api.
        """
    lanes_mid, lanes_left, lanes_right, lane_ids = get_lane_polylines(self.map_api, self.ego_coords, self.radius)
    assert type(lanes_mid) == MapObjectPolylines
    assert type(lanes_left) == MapObjectPolylines
    assert type(lanes_right) == MapObjectPolylines
    assert type(lane_ids) == LaneSegmentLaneIDs

def test_get_map_object_polygons(self) -> None:
    """
        Test extracting map object polygons from map.
        """
    for layer in [SemanticMapLayer.CROSSWALK, SemanticMapLayer.STOP_LINE]:
        polygons = get_map_object_polygons(self.map_api, self.ego_coords, self.radius, layer)
        assert type(polygons) == MapObjectPolylines

def test_get_route_polygon_from_roadblock_ids(self) -> None:
    """
        Test extracting route polygon from map given list of roadblock ids.
        """
    route = get_route_polygon_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
    assert type(route) == MapObjectPolylines

def test_get_route_lane_polylines_from_roadblock_ids(self) -> None:
    """
        Test extracting route lane polylines from map given list of roadblock ids.
        """
    route = get_route_lane_polylines_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
    assert type(route) == MapObjectPolylines

def test_get_neighbor_vector_map(self) -> None:
    """
        Test extracting neighbor vector map information from map api.
        """
    lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(self.map_api, self.ego_coords, self.radius)
    assert type(lane_seg_coords) == LaneSegmentCoords
    assert type(lane_seg_conns) == LaneSegmentConnections
    assert type(lane_seg_groupings) == LaneSegmentGroupings
    assert type(lane_seg_lane_ids) == LaneSegmentLaneIDs
    assert type(lane_seg_roadblock_ids) == LaneSegmentRoadBlockIDs

def test_get_neighbor_vector_set_map(self) -> None:
    """
        Test extracting neighbor vector set map information from map api.
        """
    coords, traffic_light_data = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, [TrafficLightStatuses(self.traffic_light_data)])
    for feature_name in self.map_features:
        assert feature_name in coords
        assert type(coords[feature_name]) == MapObjectPolylines
    assert len(traffic_light_data) == 1
    assert 'LANE' in traffic_light_data[0]
    assert type(traffic_light_data[0]['LANE']) == LaneSegmentTrafficLightData

def test_get_neighbor_vector_set_map_for_time_horizon(self) -> None:
    """
        Test extracting neighbor vector set map information from map api.
        """
    coords, traffic_light_data_list = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, self.traffic_light_data_over_time)
    for feature_name in self.map_features:
        assert feature_name in coords
        assert type(coords[feature_name]) == MapObjectPolylines
    for traffic_light_data in traffic_light_data_list:
        assert 'LANE' in traffic_light_data
        assert type(traffic_light_data['LANE']) == LaneSegmentTrafficLightData

class TestVectorMapFeatureBuilder(unittest.TestCase):
    """Test feature builder that constructs map features in vectorized format."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        self.scenario = get_test_nuplan_scenario()

    def test_vector_map_feature_builder(self) -> None:
        """
        Test VectorMapFeatureBuilder
        """
        feature_builder = VectorMapFeatureBuilder(radius=20, connection_scales=[2])
        self.assertEqual(feature_builder.get_feature_type(), VectorMap)
        features = feature_builder.get_features_from_scenario(self.scenario)
        self.assertEqual(type(features), VectorMap)
        ego_state = self.scenario.initial_ego_state
        detections = self.scenario.initial_tracked_objects
        meta_data = PlannerInitialization(map_api=self.scenario.map_api, mission_goal=self.scenario.get_mission_goal(), route_roadblock_ids=self.scenario.get_route_roadblock_ids())
        history = SimulationHistoryBuffer.initialize_from_list(1, [ego_state], [detections], self.scenario.database_interval)
        iteration = SimulationIteration(TimePoint(0), 0)
        tl_data = self.scenario.get_traffic_light_status_at_iteration(iteration.index)
        current_input = PlannerInput(iteration=iteration, history=history, traffic_light_data=tl_data)
        features_sim = feature_builder.get_features_from_simulation(current_input=current_input, initialization=meta_data)
        self.assertEqual(type(features_sim), VectorMap)
        self.assertTrue(np.allclose(features_sim.coords[0], features.coords[0], atol=0.0001))
        for connections, connections_simulation in zip(features_sim.multi_scale_connections[0].values(), features.multi_scale_connections[0].values()):
            self.assertTrue(np.allclose(connections, connections_simulation))
        for lane in range(len(features_sim.lane_groupings[0])):
            for lane_groupings, lane_groupings_simulation in zip(features_sim.lane_groupings[0][lane], features.lane_groupings[0][lane]):
                self.assertTrue(np.allclose(lane_groupings, lane_groupings_simulation))
        self.assertTrue(np.allclose(features_sim.on_route_status[0], features.on_route_status[0], atol=0.0001))
        self.assertTrue(np.allclose(features_sim.traffic_light_data[0], features.traffic_light_data[0]))

    def test_vector_map_feature_builder_scripts_properly(self) -> None:
        """
        Tests that the VectorMapFeatureBuilder can be scripted properly.
        """
        feature_builder = VectorMapFeatureBuilder(radius=20, connection_scales=[2])
        self.assertEqual(feature_builder.get_feature_type(), VectorMap)
        scripted_builder = torch.jit.script(feature_builder)
        self.assertIsNotNone(scripted_builder)
        config = scripted_builder.precomputed_feature_config()
        self.assertTrue('initial_ego_state' in config)
        self.assertTrue('neighbor_vector_map' in config)
        self.assertTrue('radius' in config['neighbor_vector_map'])
        self.assertEqual('20', config['neighbor_vector_map']['radius'])
        num_lane_segment = 5
        num_connections = 7
        tensor_data = {'lane_segment_coords': torch.rand((num_lane_segment, 2, 2), dtype=torch.float64), 'lane_segment_conns': torch.zeros((num_connections, 2), dtype=torch.int64), 'on_route_status': torch.zeros((num_lane_segment, 2), dtype=torch.float32), 'traffic_light_array': torch.zeros((num_lane_segment, 4), dtype=torch.float32), 'anchor_state': torch.zeros((3,), dtype=torch.float64)}
        list_tensor_data = {'lane_segment_groupings': [torch.zeros(size=(2,), dtype=torch.int64) for _ in range(num_lane_segment)]}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_tensor_output, scripted_list_output, scripted_list_list_output = scripted_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        py_tensor_output, py_list_output, py_list_list_output = feature_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        self.assertEqual(0, len(scripted_tensor_output))
        self.assertEqual(0, len(py_tensor_output))
        self.assertEqual(len(scripted_list_output), len(py_list_output))
        for key in py_list_output:
            self.assertEqual(len(py_list_output[key]), len(scripted_list_output[key]))
            for i in range(len(py_list_output[key])):
                torch.testing.assert_close(py_list_output[key][i], scripted_list_output[key][i])
        self.assertEqual(len(py_list_list_output), len(scripted_list_list_output))
        for key in py_list_list_output:
            py_list = py_list_list_output[key]
            scripted_list = scripted_list_list_output[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                py = py_list[i]
                script = scripted_list[i]
                self.assertEqual(len(py), len(script))
                for j in range(len(py)):
                    torch.testing.assert_close(py[j], script[j])

def test_vector_map_feature_builder(self) -> None:
    """
        Test VectorMapFeatureBuilder
        """
    feature_builder = VectorMapFeatureBuilder(radius=20, connection_scales=[2])
    self.assertEqual(feature_builder.get_feature_type(), VectorMap)
    features = feature_builder.get_features_from_scenario(self.scenario)
    self.assertEqual(type(features), VectorMap)
    ego_state = self.scenario.initial_ego_state
    detections = self.scenario.initial_tracked_objects
    meta_data = PlannerInitialization(map_api=self.scenario.map_api, mission_goal=self.scenario.get_mission_goal(), route_roadblock_ids=self.scenario.get_route_roadblock_ids())
    history = SimulationHistoryBuffer.initialize_from_list(1, [ego_state], [detections], self.scenario.database_interval)
    iteration = SimulationIteration(TimePoint(0), 0)
    tl_data = self.scenario.get_traffic_light_status_at_iteration(iteration.index)
    current_input = PlannerInput(iteration=iteration, history=history, traffic_light_data=tl_data)
    features_sim = feature_builder.get_features_from_simulation(current_input=current_input, initialization=meta_data)
    self.assertEqual(type(features_sim), VectorMap)
    self.assertTrue(np.allclose(features_sim.coords[0], features.coords[0], atol=0.0001))
    for connections, connections_simulation in zip(features_sim.multi_scale_connections[0].values(), features.multi_scale_connections[0].values()):
        self.assertTrue(np.allclose(connections, connections_simulation))
    for lane in range(len(features_sim.lane_groupings[0])):
        for lane_groupings, lane_groupings_simulation in zip(features_sim.lane_groupings[0][lane], features.lane_groupings[0][lane]):
            self.assertTrue(np.allclose(lane_groupings, lane_groupings_simulation))
    self.assertTrue(np.allclose(features_sim.on_route_status[0], features.on_route_status[0], atol=0.0001))
    self.assertTrue(np.allclose(features_sim.traffic_light_data[0], features.traffic_light_data[0]))

class TestVectorSetMapFeatureBuilder(unittest.TestCase):
    """Test feature builder that constructs map features in vector set format."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        self.scenario = MockAbstractScenario()
        self.batch_size = 1
        self.radius = 35
        self.interpolation_method = 'linear'
        self.map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
        self.max_elements = {'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}
        self.max_points = {'LANE': 20, 'LEFT_BOUNDARY': 20, 'RIGHT_BOUNDARY': 20, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 20}
        self.feature_builder = VectorSetMapFeatureBuilder(map_features=self.map_features, max_elements=self.max_elements, max_points=self.max_points, radius=self.radius, interpolation_method=self.interpolation_method)

    def test_vector_set_map_feature_builder(self) -> None:
        """
        Tests VectorSetMapFeatureBuilder.
        """
        self.assertEqual(self.feature_builder.get_feature_type(), VectorSetMap)
        features = self.feature_builder.get_features_from_scenario(self.scenario)
        self.assertEqual(type(features), VectorSetMap)
        self.assertEqual(features.batch_size, self.batch_size)
        for feature_name in self.map_features:
            self.assertEqual(features.coords[feature_name][0].shape, (self.max_elements[feature_name], self.max_points[feature_name], 2))
            self.assertEqual(features.availabilities[feature_name][0].shape, (self.max_elements[feature_name], self.max_points[feature_name]))
            np.testing.assert_array_equal(features.availabilities[feature_name][0], np.zeros((self.max_elements[feature_name], self.max_points[feature_name]), dtype=np.bool_))

    def test_vector_set_map_feature_builder_simulation_and_scenario_match(self) -> None:
        """
        Tests that get_features_from_scenario and get_features_from_simulation give same results.
        """
        features = self.feature_builder.get_features_from_scenario(self.scenario)
        ego_state = self.scenario.initial_ego_state
        detections = self.scenario.initial_tracked_objects
        meta_data = PlannerInitialization(map_api=self.scenario.map_api, mission_goal=self.scenario.get_mission_goal(), route_roadblock_ids=self.scenario.get_route_roadblock_ids())
        history = SimulationHistoryBuffer.initialize_from_list(1, [ego_state], [detections], self.scenario.database_interval)
        iteration = SimulationIteration(TimePoint(0), 0)
        tl_data = self.scenario.get_traffic_light_status_at_iteration(iteration.index)
        current_input = PlannerInput(iteration=iteration, history=history, traffic_light_data=tl_data)
        features_sim = self.feature_builder.get_features_from_simulation(current_input=current_input, initialization=meta_data)
        self.assertEqual(type(features_sim), VectorSetMap)
        self.assertEqual(set(features_sim.coords.keys()), set(features.coords.keys()))
        for feature_name in features_sim.coords.keys():
            np.testing.assert_allclose(features_sim.coords[feature_name][0], features.coords[feature_name][0], atol=0.0001)
        self.assertEqual(set(features_sim.traffic_light_data.keys()), set(features.traffic_light_data.keys()))
        for feature_name in features_sim.traffic_light_data.keys():
            np.testing.assert_allclose(features_sim.traffic_light_data[feature_name][0], features.traffic_light_data[feature_name][0])
        self.assertEqual(set(features_sim.availabilities.keys()), set(features.availabilities.keys()))
        for feature_name in features_sim.availabilities.keys():
            np.testing.assert_array_equal(features_sim.availabilities[feature_name][0], features.availabilities[feature_name][0])

    def test_vector_set_map_feature_builder_scripts_properly(self) -> None:
        """
        Tests that the VectorSetMapFeatureBuilder can be scripted properly.
        """
        self.assertEqual(self.feature_builder.get_feature_type(), VectorSetMap)
        scripted_builder = torch.jit.script(self.feature_builder)
        self.assertIsNotNone(scripted_builder)
        config = scripted_builder.precomputed_feature_config()
        self.assertTrue('initial_ego_state' in config)
        self.assertTrue('neighbor_vector_set_map' in config)
        self.assertTrue('radius' in config['neighbor_vector_set_map'])
        self.assertEqual(str(self.radius), config['neighbor_vector_set_map']['radius'])
        self.assertEqual(str(self.interpolation_method), config['neighbor_vector_set_map']['interpolation_method'])
        self.assertEqual(','.join(self.map_features), config['neighbor_vector_set_map']['map_features'])
        max_elements: List[str] = [f'{feature_name}.{feature_max_elements}' for feature_name, feature_max_elements in self.max_elements.items()]
        max_points: List[str] = [f'{feature_name}.{feature_max_points}' for feature_name, feature_max_points in self.max_points.items()]
        self.assertEqual(','.join(max_elements), config['neighbor_vector_set_map']['max_elements'])
        self.assertEqual(','.join(max_points), config['neighbor_vector_set_map']['max_points'])
        tensor_data = {'anchor_state': torch.zeros((3,))}
        for feature_name in self.map_features:
            feature_max_elements = self.max_elements[feature_name]
            feature_max_points = self.max_points[feature_name]
            tensor_data[f'coords.{feature_name}'] = torch.rand((feature_max_elements, feature_max_points, 2), dtype=torch.float64)
            tensor_data[f'traffic_light_data.{feature_name}'] = torch.zeros((feature_max_elements, feature_max_points, 4), dtype=torch.int64)
            tensor_data[f'availabilities.{feature_name}'] = torch.zeros((feature_max_elements, feature_max_points), dtype=torch.bool)
        list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_tensor_output, scripted_list_output, scripted_list_list_output = scripted_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        py_tensor_output, py_list_output, py_list_list_output = self.feature_builder.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        self.assertEqual(0, len(scripted_tensor_output))
        self.assertEqual(0, len(py_tensor_output))
        self.assertEqual(len(scripted_list_output), len(py_list_output))
        for key in py_list_output:
            self.assertEqual(len(py_list_output[key]), len(scripted_list_output[key]))
            for i in range(len(py_list_output[key])):
                torch.testing.assert_close(py_list_output[key][i], scripted_list_output[key][i])
        self.assertEqual(len(py_list_list_output), len(scripted_list_list_output))
        for key in py_list_list_output:
            py_list = py_list_list_output[key]
            scripted_list = scripted_list_list_output[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                py = py_list[i]
                script = scripted_list[i]
                self.assertEqual(len(py), len(script))
                for j in range(len(py)):
                    torch.testing.assert_close(py[j], script[j])

def test_vector_set_map_feature_builder(self) -> None:
    """
        Tests VectorSetMapFeatureBuilder.
        """
    self.assertEqual(self.feature_builder.get_feature_type(), VectorSetMap)
    features = self.feature_builder.get_features_from_scenario(self.scenario)
    self.assertEqual(type(features), VectorSetMap)
    self.assertEqual(features.batch_size, self.batch_size)
    for feature_name in self.map_features:
        self.assertEqual(features.coords[feature_name][0].shape, (self.max_elements[feature_name], self.max_points[feature_name], 2))
        self.assertEqual(features.availabilities[feature_name][0].shape, (self.max_elements[feature_name], self.max_points[feature_name]))
        np.testing.assert_array_equal(features.availabilities[feature_name][0], np.zeros((self.max_elements[feature_name], self.max_points[feature_name]), dtype=np.bool_))

def test_vector_set_map_feature_builder_simulation_and_scenario_match(self) -> None:
    """
        Tests that get_features_from_scenario and get_features_from_simulation give same results.
        """
    features = self.feature_builder.get_features_from_scenario(self.scenario)
    ego_state = self.scenario.initial_ego_state
    detections = self.scenario.initial_tracked_objects
    meta_data = PlannerInitialization(map_api=self.scenario.map_api, mission_goal=self.scenario.get_mission_goal(), route_roadblock_ids=self.scenario.get_route_roadblock_ids())
    history = SimulationHistoryBuffer.initialize_from_list(1, [ego_state], [detections], self.scenario.database_interval)
    iteration = SimulationIteration(TimePoint(0), 0)
    tl_data = self.scenario.get_traffic_light_status_at_iteration(iteration.index)
    current_input = PlannerInput(iteration=iteration, history=history, traffic_light_data=tl_data)
    features_sim = self.feature_builder.get_features_from_simulation(current_input=current_input, initialization=meta_data)
    self.assertEqual(type(features_sim), VectorSetMap)
    self.assertEqual(set(features_sim.coords.keys()), set(features.coords.keys()))
    for feature_name in features_sim.coords.keys():
        np.testing.assert_allclose(features_sim.coords[feature_name][0], features.coords[feature_name][0], atol=0.0001)
    self.assertEqual(set(features_sim.traffic_light_data.keys()), set(features.traffic_light_data.keys()))
    for feature_name in features_sim.traffic_light_data.keys():
        np.testing.assert_allclose(features_sim.traffic_light_data[feature_name][0], features.traffic_light_data[feature_name][0])
    self.assertEqual(set(features_sim.availabilities.keys()), set(features.availabilities.keys()))
    for feature_name in features_sim.availabilities.keys():
        np.testing.assert_array_equal(features_sim.availabilities[feature_name][0], features.availabilities[feature_name][0])

class TestGenericAgentsFeatureBuilder(unittest.TestCase):
    """Test builder that constructs agent features during training and simulation."""

    def setUp(self) -> None:
        """
        Set up test case.
        """
        self.batch_size = 1
        self.past_time_horizon = 4.0
        self.num_agents = 10
        self.num_past_poses = 4
        self.num_total_past_poses = self.num_past_poses + 1
        self.agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE', 'TRAFFIC_CONE', 'BARRIER', 'CZONE_SIGN', 'GENERIC_OBJECT']
        self.tracked_object_types: List[TrackedObjectType] = []
        for feature_name in self.agent_features:
            try:
                self.tracked_object_types.append(TrackedObjectType[feature_name])
            except KeyError:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
        self.feature_builder = GenericAgentsFeatureBuilder(self.agent_features, TrajectorySampling(num_poses=self.num_past_poses, time_horizon=self.past_time_horizon))

    def test_generic_agent_feature_builder(self) -> None:
        """
        Test GenericAgentFeatureBuilder
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
        feature = self.feature_builder.get_features_from_scenario(scenario)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
            self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

    def test_no_agents(self) -> None:
        """
        Test when there are no agents
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=0, tracked_object_types=self.tracked_object_types)
        feature = self.feature_builder.get_features_from_scenario(scenario)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), 0)
            self.assertEqual(feature.agents[feature_name][0].shape[1], 0)
            self.assertEqual(feature.agents[feature_name][0].shape[2], GenericAgents.agents_states_dim())

    def test_get_feature_from_simulation(self) -> None:
        """
        Test get feature from simulation
        """
        scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
        mock_meta_data = PlannerInitialization(map_api=MockAbstractMap(), route_roadblock_ids=None, mission_goal=StateSE2(0, 0, 0))
        ego_past_states = list(scenario.get_ego_past_trajectory(iteration=0, num_samples=10, time_horizon=5))
        ego_initial_state = scenario.initial_ego_state
        ego_history = ego_past_states + [ego_initial_state]
        past_observations = list(scenario.get_past_tracked_objects(iteration=0, num_samples=10, time_horizon=5))
        initial_observation = scenario.initial_tracked_objects
        observation_history = past_observations + [initial_observation]
        history = SimulationHistoryBuffer.initialize_from_list(len(ego_history), ego_history, observation_history, scenario.database_interval)
        current_input = PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=scenario.get_traffic_light_status_at_iteration(0))
        feature = self.feature_builder.get_features_from_simulation(current_input=current_input, initialization=mock_meta_data)
        self.assertEqual(type(feature), GenericAgents)
        self.assertEqual(feature.batch_size, self.batch_size)
        self.assertEqual(len(feature.ego), self.batch_size)
        self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
        self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
        for feature_name in self.agent_features:
            self.assertTrue(feature_name in feature.agents)
            self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
            self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
            self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
            self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

    def test_agents_feature_builder_scripts_properly(self) -> None:
        """
        Tests that the Generic Agents Feature Builder scripts properly
        """
        config = self.feature_builder.precomputed_feature_config()
        for expected_key in ['past_ego_states', 'past_time_stamps']:
            self.assertTrue(expected_key in config)
            config_dict = config[expected_key]
            self.assertTrue(len(config_dict) == 3)
            self.assertEqual(0, int(config_dict['iteration']))
            self.assertEqual(self.num_past_poses, int(config_dict['num_samples']))
            self.assertEqual(self.past_time_horizon, int(float(config_dict['time_horizon'])))
        tracked_objects_config_dict = config['past_tracked_objects']
        self.assertTrue(len(tracked_objects_config_dict) == 4)
        self.assertEqual(0, int(tracked_objects_config_dict['iteration']))
        self.assertEqual(self.num_past_poses, int(tracked_objects_config_dict['num_samples']))
        self.assertEqual(self.past_time_horizon, int(float(tracked_objects_config_dict['time_horizon'])))
        self.assertTrue('agent_features' in tracked_objects_config_dict)
        self.assertEqual(','.join(self.agent_features), tracked_objects_config_dict['agent_features'])
        num_frames = 5
        num_agents = 3
        ego_dim = EgoInternalIndex.dim()
        agent_dim = AgentInternalIndex.dim()
        past_ego_states = torch.zeros((num_frames, ego_dim), dtype=torch.float32)
        past_timestamps = torch.tensor([i * 50 for i in range(num_frames)], dtype=torch.int64)
        past_tracked_objects = [torch.ones((num_agents, agent_dim), dtype=torch.float32) for _ in range(num_frames)]
        for i in range(num_frames):
            for j in range(num_agents):
                past_tracked_objects[i][j, :] *= j + 1
        tensor_data = {'past_ego_states': past_ego_states, 'past_time_stamps': past_timestamps}
        list_tensor_data = {f'past_tracked_objects.{feature_name}': past_tracked_objects for feature_name in self.agent_features}
        list_list_tensor_data: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_builder = torch.jit.script(self.feature_builder)
        scripted_tensors, scripted_list_tensors, scripted_list_list_tensors = scripted_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        py_tensors, py_list_tensors, py_list_list_tensors = self.feature_builder.scriptable_forward(copy.deepcopy(tensor_data), copy.deepcopy(list_tensor_data), copy.deepcopy(list_list_tensor_data))
        self.assertEqual(0, len(scripted_tensors))
        self.assertEqual(0, len(py_tensors))
        self.assertEqual(len(scripted_list_tensors), len(py_list_tensors))
        for key in py_list_tensors:
            scripted_list = scripted_list_tensors[key]
            py_list = py_list_tensors[key]
            self.assertEqual(len(py_list), len(scripted_list))
            for i in range(len(py_list)):
                scripted = scripted_list[i]
                py = py_list[i]
                torch.testing.assert_allclose(py, scripted, atol=0.05, rtol=0.05)
        self.assertEqual(0, len(scripted_list_list_tensors))
        self.assertEqual(0, len(py_list_list_tensors))

def test_generic_agent_feature_builder(self) -> None:
    """
        Test GenericAgentFeatureBuilder
        """
    scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
    feature = self.feature_builder.get_features_from_scenario(scenario)
    self.assertEqual(type(feature), GenericAgents)
    self.assertEqual(feature.batch_size, self.batch_size)
    self.assertEqual(len(feature.ego), self.batch_size)
    self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
    self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
    for feature_name in self.agent_features:
        self.assertTrue(feature_name in feature.agents)
        self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
        self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
        self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
        self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

def test_no_agents(self) -> None:
    """
        Test when there are no agents
        """
    scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=0, tracked_object_types=self.tracked_object_types)
    feature = self.feature_builder.get_features_from_scenario(scenario)
    self.assertEqual(type(feature), GenericAgents)
    self.assertEqual(feature.batch_size, self.batch_size)
    self.assertEqual(len(feature.ego), self.batch_size)
    self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
    self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
    for feature_name in self.agent_features:
        self.assertTrue(feature_name in feature.agents)
        self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
        self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
        self.assertEqual(len(feature.agents[feature_name][0][0]), 0)
        self.assertEqual(feature.agents[feature_name][0].shape[1], 0)
        self.assertEqual(feature.agents[feature_name][0].shape[2], GenericAgents.agents_states_dim())

def test_get_feature_from_simulation(self) -> None:
    """
        Test get feature from simulation
        """
    scenario = MockAbstractScenario(number_of_past_iterations=10, number_of_detections=self.num_agents, tracked_object_types=self.tracked_object_types)
    mock_meta_data = PlannerInitialization(map_api=MockAbstractMap(), route_roadblock_ids=None, mission_goal=StateSE2(0, 0, 0))
    ego_past_states = list(scenario.get_ego_past_trajectory(iteration=0, num_samples=10, time_horizon=5))
    ego_initial_state = scenario.initial_ego_state
    ego_history = ego_past_states + [ego_initial_state]
    past_observations = list(scenario.get_past_tracked_objects(iteration=0, num_samples=10, time_horizon=5))
    initial_observation = scenario.initial_tracked_objects
    observation_history = past_observations + [initial_observation]
    history = SimulationHistoryBuffer.initialize_from_list(len(ego_history), ego_history, observation_history, scenario.database_interval)
    current_input = PlannerInput(iteration=SimulationIteration(index=0, time_point=scenario.start_time), history=history, traffic_light_data=scenario.get_traffic_light_status_at_iteration(0))
    feature = self.feature_builder.get_features_from_simulation(current_input=current_input, initialization=mock_meta_data)
    self.assertEqual(type(feature), GenericAgents)
    self.assertEqual(feature.batch_size, self.batch_size)
    self.assertEqual(len(feature.ego), self.batch_size)
    self.assertEqual(len(feature.ego[0]), self.num_total_past_poses)
    self.assertEqual(len(feature.ego[0][0]), GenericAgents.ego_state_dim())
    for feature_name in self.agent_features:
        self.assertTrue(feature_name in feature.agents)
        self.assertEqual(len(feature.agents[feature_name]), self.batch_size)
        self.assertEqual(len(feature.agents[feature_name][0]), self.num_total_past_poses)
        self.assertEqual(len(feature.agents[feature_name][0][0]), self.num_agents)
        self.assertEqual(len(feature.agents[feature_name][0][0][0]), GenericAgents.agents_states_dim())

@dataclass
class GenericAgents(AbstractModelFeature):
    """
    Model input feature representing the present and past states of the ego and agents.

    The structure includes:
        ego: List[<np.ndarray: num_frames, 7>].
            The outer list is the batch dimension.
            The num_frames includes both present and past frames.
            The last dimension is the ego pose (x, y, heading) velocities (vx, vy) accelerations (ax, ay) at time t.
            Example dimensions: 8 (batch_size) x 5 (1 present + 4 past frames) x 7
        agents: Dict[str, List[<np.ndarray: num_frames, num_agents, 8>]].
            Agent features indexed by agent feature type.
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
    agents: Dict[str, List[FeatureDataType]]

    def __post_init__(self) -> None:
        """Sanitize attributes of dataclass."""
        if not all([len(self.ego) == len(agent) for agent in self.agents.values()]):
            raise AssertionError('Batch size inconsistent across features!')
        if len(self.ego) == 0:
            raise AssertionError('Batch size has to be > 0!')
        if self.ego[0].ndim != 2:
            raise AssertionError(f'Ego feature samples does not conform to feature dimensions! Got ndim: {self.ego[0].ndim} , expected 2 [num_frames, 7]')
        if 'EGO' in self.agents.keys():
            raise AssertionError('EGO not a valid agents feature type!')
        for feature_name in self.agents.keys():
            if feature_name not in TrackedObjectType._member_names_:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
        for agent in self.agents.values():
            if agent[0].ndim != 3:
                raise AssertionError(f'Agent feature samples does not conform to feature dimensions! Got ndim: {agent[0].ndim} , expected 3 [num_frames, num_agents, 8]')
        for sample_idx in range(len(self.ego)):
            if int(self.ego[sample_idx].shape[0]) != self.num_frames or not all([int(agent[sample_idx].shape[0]) == self.num_frames for agent in self.agents.values()]):
                raise AssertionError('Agent feature samples have different number of frames!')

    def _validate_ego_query(self, sample_idx: int) -> None:
        """
        Validate ego sample query is valid.
        :param sample_idx: the batch index of interest.
        :raise
            ValueError if sample_idx invalid.
            RuntimeError if feature at given sample index is empty.
        """
        if self.batch_size < sample_idx:
            raise ValueError(f'Requsted sample index {sample_idx} larger than batch size {self.batch_size}!')
        if self.ego[sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')

    def _validate_agent_query(self, agent_type: str, sample_idx: int) -> None:
        """
        Validate agent type, sample query is valid.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :raise ValueError if agent_type or sample_idx invalid.
        """
        if agent_type not in TrackedObjectType._member_names_:
            raise ValueError(f'Invalid agent type: {agent_type}')
        if agent_type not in self.agents.keys():
            raise ValueError(f'Agent type: {agent_type} is unavailable!')
        if self.batch_size < sample_idx:
            raise ValueError(f'Requsted sample index {sample_idx} larger than batch size {self.batch_size}!')

    @cached_property
    def is_valid(self) -> bool:
        """Inherited, see superclass."""
        return len(self.ego) > 0 and all([len(agent) > 0 for agent in self.agents.values()]) and all([len(self.ego) == len(agent) for agent in self.agents.values()]) and (len(self.ego[0]) > 0) and all([len(agent[0]) > 0 for agent in self.agents.values()]) and all([len(self.ego[0]) == len(agent[0]) > 0 for agent in self.agents.values()]) and (self.ego[0].shape[-1] == self.ego_state_dim()) and all([agent[0].shape[-1] == self.agents_states_dim() for agent in self.agents.values()])

    @property
    def batch_size(self) -> int:
        """
        :return: number of batches.
        """
        return len(self.ego)

    @classmethod
    def collate(cls, batch: List[GenericAgents]) -> GenericAgents:
        """
        Implemented. See interface.
        Collates a list of features that each have batch size of 1.
        """
        agents: Dict[str, List[FeatureDataType]] = defaultdict(list)
        for sample in batch:
            for agent_name, agent in sample.agents.items():
                agents[agent_name] += [agent[0]]
        return GenericAgents(ego=[item.ego[0] for item in batch], agents=agents)

    def to_feature_tensor(self) -> GenericAgents:
        """Implemented. See interface."""
        return GenericAgents(ego=[to_tensor(sample) for sample in self.ego], agents={agent_name: [to_tensor(sample) for sample in agent] for agent_name, agent in self.agents.items()})

    def to_device(self, device: torch.device) -> GenericAgents:
        """Implemented. See interface."""
        return GenericAgents(ego=[to_tensor(ego).to(device=device) for ego in self.ego], agents={agent_name: [to_tensor(sample).to(device=device) for sample in agent] for agent_name, agent in self.agents.items()})

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> GenericAgents:
        """Implemented. See interface."""
        return GenericAgents(ego=data['ego'], agents=data['agents'])

    def unpack(self) -> List[GenericAgents]:
        """Implemented. See interface."""
        return [GenericAgents(ego=[self.ego[sample_idx]], agents={agent_name: [agent[sample_idx]] for agent_name, agent in self.agents.items()}) for sample_idx in range(self.batch_size)]

    def num_agents_in_sample(self, agent_type: str, sample_idx: int) -> int:
        """
        Returns the number of agents at a given batch for given agent feature type.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: number of agents in the given batch.
        """
        self._validate_agent_query(agent_type, sample_idx)
        return self.agents[agent_type][sample_idx].shape[1]

    @staticmethod
    def ego_state_dim() -> int:
        """
        :return: ego state dimension.
        """
        return GenericEgoFeatureIndex.dim()

    @staticmethod
    def agents_states_dim() -> int:
        """
        :return: agent state dimension.
        """
        return GenericAgentFeatureIndex.dim()

    @property
    def num_frames(self) -> int:
        """
        :return: number of frames.
        """
        return int(self.ego[0].shape[0])

    @property
    def ego_feature_dim(self) -> int:
        """
        :return: ego feature dimension.
        """
        return GenericAgents.ego_state_dim() * self.num_frames

    @property
    def agents_features_dim(self) -> int:
        """
        :return: ego feature dimension.
        """
        return GenericAgents.agents_states_dim() * self.num_frames

    def has_agents(self, agent_type: str, sample_idx: int) -> bool:
        """
        Check whether agents of specified type exist in the feature.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: whether agents exist in the feature.
        """
        self._validate_agent_query(agent_type, sample_idx)
        return self.num_agents_in_sample(agent_type, sample_idx) > 0

    def agent_processing_by_type(self, processing_function: Callable[[str, int], FeatureDataType], sample_idx: int) -> FeatureDataType:
        """
        Apply agent processing functions across all agent types in features for given batch sample.
        :param processing_function: function to apply across agent types
        :param sample_idx: the batch index of interest.
        :return Processed agent feature across agent types.
        """
        agents: List[FeatureDataType] = []
        for agent_type in self.agents.keys():
            if self.has_agents(agent_type, sample_idx):
                agents.append(processing_function(agent_type, sample_idx))
        if len(agents) == 0:
            if isinstance(self.ego[sample_idx], torch.Tensor):
                return torch.empty((0, len(self.agents.keys()) * self.num_frames * GenericAgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype, device=self.ego[sample_idx].device)
            else:
                return np.empty((0, len(self.agents.keys()) * self.num_frames * GenericAgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype)
        elif isinstance(agents[0], torch.Tensor):
            return torch.cat(agents, dim=0)
        else:
            return np.concatenate(agents, axis=0)

    def get_flatten_agents_features_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Flatten agents' features of specified type by stacking the agents' states along the num_frame dimension
        <np.ndarray: num_frames, num_agents, 8>] -> <np.ndarray: num_agents, num_frames x 8>].

        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents, num_frames x 8>] agent feature.
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.num_agents_in_sample(agent_type, sample_idx) == 0:
            if isinstance(self.ego[sample_idx], torch.Tensor):
                return torch.empty((0, self.num_frames * GenericAgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype, device=self.ego[sample_idx].device)
            else:
                return np.empty((0, self.num_frames * GenericAgentFeatureIndex.dim()), dtype=self.ego[sample_idx].dtype)
        data = self.agents[agent_type][sample_idx]
        axes = (1, 0) if isinstance(data, torch.Tensor) else (1, 0, 2)
        return data.transpose(*axes).reshape(data.shape[1], -1)

    def get_flatten_agents_features_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Flatten agents' features of all types by stacking the agents' states along the num_frame dimension
        <np.ndarray: num_frames, num_agents, 8>] -> <np.ndarray: num_agents, num_frames x 8>].

        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents, num_frames x 8>] agent feature.
        """
        return self.agent_processing_by_type(self.get_flatten_agents_features_by_type_in_sample, sample_idx)

    def get_present_ego_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return the present ego in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: 8>. ego at sample index.
        """
        self._validate_ego_query(sample_idx)
        return self.ego[sample_idx][-1]

    def get_present_agents_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Return the present agents of specified type in the given sample index.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents, 8>. all agents at sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.agents[agent_type][sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')
        return self.agents[agent_type][sample_idx][-1]

    def get_present_agents_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return the present agents of all types in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents, 8>. all agents at sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        return self.agent_processing_by_type(self.get_present_agents_by_type_in_sample, sample_idx)

    def get_ego_agents_center_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Return ego center in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: 2>. (x, y) positions of the ego's center at sample index.
        """
        self._validate_ego_query(sample_idx)
        return self.get_present_ego_in_sample(sample_idx)[:GenericEgoFeatureIndex.y() + 1]

    def get_agents_centers_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of specified type's centers in the given sample index.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents, 2>. (x, y) positions of the agents' centers at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.agents[agent_type][sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')
        return self.get_present_agents_by_type_in_sample(agent_type, sample_idx)[:, :GenericAgentFeatureIndex.y() + 1]

    def get_agents_centers_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of all types' centers in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents, 2>.
            (x, y) positions of the agents' centers at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        return self.agent_processing_by_type(self.get_agents_centers_by_type_in_sample, sample_idx)

    def get_agents_length_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of specified type's length at the given sample index.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents>. lengths of all the agents at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.agents[agent_type][sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')
        return self.get_present_agents_by_type_in_sample(agent_type, sample_idx)[:, GenericAgentFeatureIndex.length()]

    def get_agents_length_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of all types' length at the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents>. lengths of all the agents at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        return self.agent_processing_by_type(self.get_agents_length_by_type_in_sample, sample_idx)

    def get_agents_width_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of specified type's width in the given sample index.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents>. width of all the agents at the sample index.
        :raise RuntimeError if feature at given sample index is empty
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.agents[agent_type][sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')
        return self.get_present_agents_by_type_in_sample(agent_type, sample_idx)[:, GenericAgentFeatureIndex.width()]

    def get_agents_width_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of all types' width in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents>. width of all the agents at the sample index.
        :raise RuntimeError if feature at given sample index is empty
        """
        return self.agent_processing_by_type(self.get_agents_width_by_type_in_sample, sample_idx)

    def get_agent_corners_by_type_in_sample(self, agent_type: str, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of specified type's corners in the given sample index.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_agents, 4, 3>. (x, y, 1) positions of all the agents' corners at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        self._validate_agent_query(agent_type, sample_idx)
        if self.agents[agent_type][sample_idx].size == 0:
            raise RuntimeError('Feature is empty!')
        widths = self.get_agents_width_by_type_in_sample(agent_type, sample_idx)
        lengths = self.get_agents_length_by_type_in_sample(agent_type, sample_idx)
        half_widths = widths / 2.0
        half_lengths = lengths / 2.0
        feature_cls = np.array if isinstance(widths, np.ndarray) else torch.Tensor
        return feature_cls([[[half_length, half_width, 1.0], [-half_length, half_width, 1.0], [-half_length, -half_width, 1.0], [half_length, -half_width, 1.0]] for half_width, half_length in zip(half_widths, half_lengths)])

    def get_agent_corners_in_sample(self, sample_idx: int) -> FeatureDataType:
        """
        Returns all agents of all types' corners in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: num_types, num_agents, 4, 3>.
            (x, y, 1) positions of all the agents' corners at the sample index.
        :raise RuntimeError if feature at given sample index is empty.
        """
        return self.agent_processing_by_type(self.get_agent_corners_by_type_in_sample, sample_idx)

@cached_property
def is_valid(self) -> bool:
    """Inherited, see superclass."""
    return len(self.ego) > 0 and all([len(agent) > 0 for agent in self.agents.values()]) and all([len(self.ego) == len(agent) for agent in self.agents.values()]) and (len(self.ego[0]) > 0) and all([len(agent[0]) > 0 for agent in self.agents.values()]) and all([len(self.ego[0]) == len(agent[0]) > 0 for agent in self.agents.values()]) and (self.ego[0].shape[-1] == self.ego_state_dim()) and all([agent[0].shape[-1] == self.agents_states_dim() for agent in self.agents.values()])

@property
def ego_feature_dim(self) -> int:
    """
        :return: ego feature dimension.
        """
    return GenericAgents.ego_state_dim() * self.num_frames

@property
def agents_features_dim(self) -> int:
    """
        :return: ego feature dimension.
        """
    return GenericAgents.agents_states_dim() * self.num_frames

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

@cached_property
def is_valid(self) -> bool:
    """Inherited, see superclass."""
    return len(self.ego) > 0 and len(self.agents) > 0 and (len(self.ego) == len(self.agents)) and (len(self.ego[0]) > 0) and (len(self.agents[0]) > 0) and (len(self.ego[0]) == len(self.agents[0]) > 0) and (self.ego[0].shape[-1] == self.ego_state_dim()) and (self.agents[0].shape[-1] == self.agents_states_dim())

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

@dataclass
class Raster(AbstractModelFeature):
    """
    Dataclass that holds map/environment signals in a raster (HxWxC) or (CxHxW) to be consumed by the model.

    :param ego_layer: raster layer that represents the ego's position and extent
    :param agents_layer: raster layer that represents the position and extent of agents surrounding the ego
    :param roadmap_layer: raster layer that represents map information around the ego
    """
    data: FeatureDataType

    def __post_init__(self) -> None:
        """Sanitize attributes of dataclass."""
        self.num_map_channels = 2
        self.ego_agent_sep_channel_num = int((self.num_channels() - self.num_map_channels) // 2)
        shape = self.data.shape
        array_dims = len(shape)
        if array_dims != 3 and array_dims != 4:
            raise RuntimeError(f'Invalid raster array. Expected 3 or 4 dims, got {array_dims}.')

    @property
    def num_batches(self) -> Optional[int]:
        """Number of batches in the feature."""
        return None if len(self.data.shape) < 4 else self.data.shape[0]

    def to_feature_tensor(self) -> AbstractModelFeature:
        """Implemented. See interface."""
        to_tensor_torchvision = torchvision.transforms.ToTensor()
        return Raster(data=to_tensor_torchvision(np.asarray(self.data)))

    def to_device(self, device: torch.device) -> Raster:
        """Implemented. See interface."""
        validate_type(self.data, torch.Tensor)
        return Raster(data=self.data.to(device=device))

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Raster:
        """Implemented. See interface."""
        return Raster(data=data['data'])

    def unpack(self) -> List[Raster]:
        """Implemented. See interface."""
        return [Raster(data[None]) for data in self.data]

    @staticmethod
    def from_feature_tensor(tensor: torch.Tensor) -> Raster:
        """Implemented. See interface."""
        array = tensor.numpy()
        if len(array.shape) == 4:
            array = array.transpose(0, 2, 3, 1)
        else:
            array = array.transpose(1, 2, 0)
        return Raster(array)

    @property
    def width(self) -> int:
        """
        :return: the width of a raster
        """
        return self.data.shape[-2] if self._is_channels_last() else self.data.shape[-1]

    @property
    def height(self) -> int:
        """
        :return: the height of a raster
        """
        return self.data.shape[-3] if self._is_channels_last() else self.data.shape[-2]

    def num_channels(self) -> int:
        """
        Number of raster channels.
        """
        return self.data.shape[-1] if self._is_channels_last() else self.data.shape[-3]

    @property
    def ego_layer(self) -> FeatureDataType:
        """
        Get the 2D grid representing the ego layer
        located at channel 0.
        """
        return self._get_data_channel(range(0, self.ego_agent_sep_channel_num))

    @property
    def agents_layer(self) -> FeatureDataType:
        """
        Get the 2D grid representing the agents layer
        located at channel 1.
        """
        start_channel = self.ego_agent_sep_channel_num
        end_channel = self.num_channels() - self.num_map_channels
        return self._get_data_channel(range(start_channel, end_channel))

    @property
    def roadmap_layer(self) -> FeatureDataType:
        """
        Get the 2D grid representing the map layer
        located at channel 2.
        """
        return self._get_data_channel(-2)

    @property
    def baseline_paths_layer(self) -> FeatureDataType:
        """
        Get the 2D grid representing the baseline paths layer
        located at channel 3.
        """
        return self._get_data_channel(-1)

    def _is_channels_last(self) -> bool:
        """
        Check location of channel dimension
        :return True if position [-1] is the number of channels
        """
        if isinstance(self.data, Tensor):
            return False
        elif isinstance(self.data, ndarray):
            return True
        else:
            raise RuntimeError(f'The data needs to be either numpy array or torch Tensor, but got type(data): {type(self.data)}')

    def _get_data_channel(self, index: Union[int, range]) -> FeatureDataType:
        """
        Extract channel data
        :param index: of layer
        :return: data corresponding to layer
        """
        if self._is_channels_last():
            return self.data[..., index]
        else:
            return self.data[..., index, :, :]

def _is_channels_last(self) -> bool:
    """
        Check location of channel dimension
        :return True if position [-1] is the number of channels
        """
    if isinstance(self.data, Tensor):
        return False
    elif isinstance(self.data, ndarray):
        return True
    else:
        raise RuntimeError(f'The data needs to be either numpy array or torch Tensor, but got type(data): {type(self.data)}')

class TestVectorSetMap(unittest.TestCase):
    """Test vector set map feature representation."""

    def setUp(self) -> None:
        """Set up test case."""
        self.coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
        self.traffic_light_data: Dict[str, List[npt.NDArray[np.int64]]] = {'LANE': [np.array([[[0, 0, 0, 1], [1, 0, 0, 0]], [[0, 0, 0, 1], [1, 0, 0, 0]]])]}
        self.availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])], 'ROUTE': [np.array([[True, True, False], [True, True, False]])]}

    def test_vector_set_map_feature(self) -> None:
        """
        Test the core functionality of features.
        """
        feature = VectorSetMap(coords=self.coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(VectorSetMap.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(list(feature.coords.values())[0][0], np.ndarray)
        self.assertIsInstance(list(feature.traffic_light_data.values())[0][0], np.ndarray)
        self.assertIsInstance(list(feature.availabilities.values())[0][0], np.ndarray)
        feature = feature.to_feature_tensor()
        self.assertIsInstance(list(feature.coords.values())[0][0], torch.Tensor)
        self.assertIsInstance(list(feature.traffic_light_data.values())[0][0], torch.Tensor)
        self.assertIsInstance(list(feature.availabilities.values())[0][0], torch.Tensor)

    def test_feature_layer_mismatch(self) -> None:
        """
        Test when same feature layers not present across feature.
        """
        coords: Dict[str, List[npt.NDArray[np.float32]]] = {'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
        availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=self.coords, traffic_light_data=self.traffic_light_data, availabilities=availabilities)

    def test_dimension_mismatch(self) -> None:
        """
        Test when feature dimensions don't match within or across feature layers.
        """
        coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0, 0.0]], [[0.0, 0.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
        coords = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
        coords = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
        availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])], 'ROUTE': [np.array([[True, True, False], [True, True, False]]), np.array([[True, True, False], [True, True, False]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=availabilities)

    def test_bad_data(self) -> None:
        """
        Test data dimensions are wrong or missing.
        """
        coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0], [1.0]], [[0.0], [1.0]]])], 'ROUTE': [np.array([[[0.0], [1.0], [0.0]], [[0.0], [1.0], [0.0]]])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
        coords = {'LANE': [np.array([])], 'ROUTE': [np.array([])]}
        with self.assertRaises(RuntimeError):
            VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

def test_feature_layer_mismatch(self) -> None:
    """
        Test when same feature layers not present across feature.
        """
    coords: Dict[str, List[npt.NDArray[np.float32]]] = {'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
    availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=self.coords, traffic_light_data=self.traffic_light_data, availabilities=availabilities)

def test_dimension_mismatch(self) -> None:
    """
        Test when feature dimensions don't match within or across feature layers.
        """
    coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0, 0.0]], [[0.0, 0.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
    coords = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
    coords = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]), np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
    availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])], 'ROUTE': [np.array([[True, True, False], [True, True, False]]), np.array([[True, True, False], [True, True, False]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=availabilities)

def test_bad_data(self) -> None:
    """
        Test data dimensions are wrong or missing.
        """
    coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0], [1.0]], [[0.0], [1.0]]])], 'ROUTE': [np.array([[[0.0], [1.0], [0.0]], [[0.0], [1.0], [0.0]]])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)
    coords = {'LANE': [np.array([])], 'ROUTE': [np.array([])]}
    with self.assertRaises(RuntimeError):
        VectorSetMap(coords=coords, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

def build_simulations(cfg: DictConfig, worker: WorkerPool, callbacks: List[AbstractCallback], callbacks_worker: Optional[WorkerPool]=None, pre_built_planners: Optional[List[AbstractPlanner]]=None) -> List[SimulationRunner]:
    """
    Build simulations.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :param callbacks: Callbacks for simulation.
    :param worker: Worker for job execution.
    :param callbacks_worker: worker pool to use for callbacks from sim
    :param pre_built_planners: List of pre-built planners to run in simulation.
    :return A dict of simulation engines with challenge names.
    """
    logger.info('Building simulations...')
    simulations = list()
    logger.info('Extracting scenarios...')
    if not int(os.environ.get('NUPLAN_SIMULATION_ALLOW_ANY_BUILDER', '0')) and (not is_target_type(cfg.scenario_builder, NuPlanScenarioBuilder)):
        raise ValueError(f'Simulation framework only runs with NuPlanScenarioBuilder. Got {cfg.scenario_builder}')
    scenario_filter = DistributedScenarioFilter(cfg=cfg, worker=worker, node_rank=int(os.environ.get('NODE_RANK', 0)), num_nodes=int(os.environ.get('NUM_NODES', 1)), synchronization_path=cfg.output_dir, timeout_seconds=cfg.distributed_timeout_seconds, distributed_mode=DistributedMode[cfg.distributed_mode])
    scenarios = scenario_filter.get_scenarios()
    metric_engines_map = {}
    if cfg.run_metric:
        logger.info('Building metric engines...')
        metric_engines_map = build_metrics_engines(cfg=cfg, scenarios=scenarios)
        logger.info('Building metric engines...DONE')
    else:
        logger.info('Metric engine is disable')
    logger.info('Building simulations from %d scenarios...', len(scenarios))
    for scenario in scenarios:
        if pre_built_planners is None:
            if 'planner' not in cfg.keys():
                raise KeyError('Planner not specified in config. Please specify a planner using "planner" field.')
            planners = build_planners(cfg.planner, scenario)
        else:
            planners = pre_built_planners
        for planner in planners:
            ego_controller: AbstractEgoController = instantiate(cfg.ego_controller, scenario=scenario)
            simulation_time_controller: AbstractSimulationTimeController = instantiate(cfg.simulation_time_controller, scenario=scenario)
            observations: AbstractObservation = build_observations(cfg.observation, scenario=scenario)
            metric_engine = metric_engines_map.get(scenario.scenario_type, None)
            if metric_engine is not None:
                stateful_callbacks = [MetricCallback(metric_engine=metric_engine, worker_pool=callbacks_worker)]
            else:
                stateful_callbacks = []
            if 'simulation_log_callback' in cfg.callback:
                stateful_callbacks.append(instantiate(cfg.callback['simulation_log_callback'], worker_pool=callbacks_worker))
            simulation_setup = SimulationSetup(time_controller=simulation_time_controller, observations=observations, ego_controller=ego_controller, scenario=scenario)
            simulation = Simulation(simulation_setup=simulation_setup, callback=MultiCallback(callbacks + stateful_callbacks), simulation_history_buffer_duration=cfg.simulation_history_buffer_duration)
            simulations.append(SimulationRunner(simulation, planner))
    logger.info('Building simulations...DONE!')
    return simulations

def validate_type(instantiated_class: Any, desired_type: Type[Any]) -> None:
    """
    Validate that constructed type is indeed the desired one
    :param instantiated_class: class that was created
    :param desired_type: type that the created class should have
    """
    assert isinstance(instantiated_class, desired_type), f'Class to be of type {desired_type}, but is {type(instantiated_class)}!'

def are_the_same_type(lhs: Any, rhs: Any) -> None:
    """
    Validate that lhs and rhs are of the same type
    :param lhs: left argument
    :param rhs: right argument
    """
    lhs_type = type(lhs)
    rhs_type = type(rhs)
    assert lhs_type == rhs_type, f'Lhs and Rhs are not of the same type! {lhs_type} != {rhs_type}!'

class TestUtilsType(unittest.TestCase):
    """Test utils_type functions."""

    def test_is_TorchModuleWrapper_config(self) -> None:
        """Tests that is_TorchModuleWrapper_config works as expected."""
        mock_config = DictConfig({'model_config': 'some_value', 'checkpoint_path': 'some_value', 'some_other_key': 'some_value'})
        expect_true = is_TorchModuleWrapper_config(mock_config)
        self.assertTrue(expect_true)
        mock_config.pop('some_other_key')
        expect_true = is_TorchModuleWrapper_config(mock_config)
        self.assertTrue(expect_true)
        mock_config.pop('model_config')
        expect_false = is_TorchModuleWrapper_config(mock_config)
        self.assertFalse(expect_false)
        mock_config.pop('checkpoint_path')
        expect_false = is_TorchModuleWrapper_config(mock_config)
        self.assertFalse(expect_false)

    def test_is_target_type(self) -> None:
        """Tests that is_target_type works as expected."""
        mock_config_test_utils_mock_type = DictConfig({'_target_': f'{__name__}.TestUtilsTypeMockType'})
        mock_config_test_utils_another_mock_type = DictConfig({'_target_': f'{__name__}.TestUtilsTypeAnotherMockType'})
        expect_true = is_target_type(mock_config_test_utils_mock_type, TestUtilsTypeMockType)
        self.assertTrue(expect_true)
        expect_true = is_target_type(mock_config_test_utils_another_mock_type, TestUtilsTypeAnotherMockType)
        self.assertTrue(expect_true)
        expect_false = is_target_type(mock_config_test_utils_mock_type, TestUtilsTypeAnotherMockType)
        self.assertFalse(expect_false)
        expect_false = is_target_type(mock_config_test_utils_another_mock_type, TestUtilsTypeMockType)
        self.assertFalse(expect_false)

    def test_validate_type(self) -> None:
        """Tests that validate_type works as expected."""
        test_utils_type_mock_type = TestUtilsTypeMockType()
        validate_type(test_utils_type_mock_type, TestUtilsTypeMockType)
        with self.assertRaises(AssertionError):
            validate_type(test_utils_type_mock_type, TestUtilsTypeAnotherMockType)

    def test_are_the_same_type(self) -> None:
        """Tests that are_the_same_type works as expected."""
        test_utils_type_mock_type = TestUtilsTypeMockType()
        another_test_utils_type_mock_type = TestUtilsTypeMockType()
        test_utils_type_another_mock_type = TestUtilsTypeAnotherMockType()
        are_the_same_type(test_utils_type_mock_type, another_test_utils_type_mock_type)
        with self.assertRaises(AssertionError):
            are_the_same_type(test_utils_type_mock_type, test_utils_type_another_mock_type)

    def test_validate_dict_type(self) -> None:
        """Tests that validate_dict_type works as expected."""
        mock_config = DictConfig({'_convert_': 'all', 'correct_object': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}, 'correct_object_2': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}})
        instantiated_config = hydra.utils.instantiate(mock_config)
        validate_dict_type(instantiated_config, TestUtilsTypeMockType)
        mock_config.other_object = {'_target_': f'{__name__}.TestUtilsTypeAnotherMockType', 'c': 1}
        instantiated_config = hydra.utils.instantiate(mock_config)
        with self.assertRaises(AssertionError):
            validate_dict_type(instantiated_config, TestUtilsTypeMockType)

    def test_find_builder_in_config(self) -> None:
        """Tests that find_builder_in_config works as expected."""
        mock_config = DictConfig({'correct_object': {'_target_': f'{__name__}.TestUtilsTypeMockType', 'a': 1, 'b': 2.5}, 'other_object': {'_target_': f'{__name__}.TestUtilsTypeAnotherMockType', 'c': 1}})
        test_utils_mock_type = find_builder_in_config(mock_config, TestUtilsTypeMockType)
        self.assertTrue(is_target_type(test_utils_mock_type, TestUtilsTypeMockType))
        test_utils_another_mock_type = find_builder_in_config(mock_config, TestUtilsTypeAnotherMockType)
        self.assertTrue(is_target_type(test_utils_another_mock_type, TestUtilsTypeAnotherMockType))
        del mock_config.other_object
        with self.assertRaises(ValueError):
            find_builder_in_config(mock_config, TestUtilsTypeAnotherMockType)

def test_validate_type(self) -> None:
    """Tests that validate_type works as expected."""
    test_utils_type_mock_type = TestUtilsTypeMockType()
    validate_type(test_utils_type_mock_type, TestUtilsTypeMockType)
    with self.assertRaises(AssertionError):
        validate_type(test_utils_type_mock_type, TestUtilsTypeAnotherMockType)

def test_are_the_same_type(self) -> None:
    """Tests that are_the_same_type works as expected."""
    test_utils_type_mock_type = TestUtilsTypeMockType()
    another_test_utils_type_mock_type = TestUtilsTypeMockType()
    test_utils_type_another_mock_type = TestUtilsTypeAnotherMockType()
    are_the_same_type(test_utils_type_mock_type, another_test_utils_type_mock_type)
    with self.assertRaises(AssertionError):
        are_the_same_type(test_utils_type_mock_type, test_utils_type_another_mock_type)

class AbstractScenario(abc.ABC):
    """
    Interface for a generic scenarios from any database.
    """

    @property
    @abc.abstractmethod
    def token(self) -> str:
        """
        Unique identifier of a scenario
        :return: str representing unique token.
        """
        pass

    @property
    @abc.abstractmethod
    def log_name(self) -> str:
        """
        Log name for from which this scenario was created
        :return: str representing log name.
        """
        pass

    @property
    @abc.abstractmethod
    def scenario_name(self) -> str:
        """
        Name of this scenario, e.g. extraction_xxxx
        :return: str representing name of this scenario.
        """
        pass

    @property
    @abc.abstractmethod
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """
        Query the vehicle parameters of ego
        :return: VehicleParameters struct.
        """
        pass

    @property
    @abc.abstractmethod
    def scenario_type(self) -> str:
        """
        :return: type of scenario e.g. [lane_change, lane_follow, ...].
        """
        pass

    @property
    @abc.abstractmethod
    def map_api(self) -> AbstractMap:
        """
        Return the Map API for this scenario
        :return: AbstractMap.
        """
        pass

    @property
    @abc.abstractmethod
    def database_interval(self) -> float:
        """
        Database interval in seconds
        :return: [s] database interval.
        """
        pass

    @abc.abstractmethod
    def get_number_of_iterations(self) -> int:
        """
        Get how many frames does this scenario contain
        :return: [int] representing number of scenarios.
        """
        pass

    @abc.abstractmethod
    def get_time_point(self, iteration: int) -> TimePoint:
        """
        Get time point of the iteration
        :param iteration: iteration in scenario 0 <= iteration < number_of_iterations
        :return: global time point.
        """
        pass

    @property
    def start_time(self) -> TimePoint:
        """
        Get the start time of a scenario
        :return: starting time.
        """
        return self.get_time_point(0)

    @property
    def end_time(self) -> TimePoint:
        """
        Get end time of the scenario
        :return: end time point.
        """
        return self.get_time_point(self.get_number_of_iterations() - 1)

    @property
    def duration_s(self) -> TimeDuration:
        """
        Get the duration of the scenario in seconds
        :return: the difference in seconds between the scenario's final and first timepoints.
        """
        return TimeDuration.from_s(self.end_time.time_s - self.start_time.time_s)

    @abc.abstractmethod
    def get_lidar_to_ego_transform(self) -> Transform:
        """
        Return the transformation matrix between lidar and ego
        :return: [4x4] rotation and translation matrix.
        """
        pass

    @abc.abstractmethod
    def get_mission_goal(self) -> Optional[StateSE2]:
        """
        Goal far into future (in generally more than 100m far beyond scenario length).
        :return: StateSE2 for the final state.
        """
        pass

    @abc.abstractmethod
    def get_route_roadblock_ids(self) -> List[str]:
        """
        Get list of roadblock ids comprising goal route.
        :return: List of roadblock id strings.
        """
        pass

    @abc.abstractmethod
    def get_expert_goal_state(self) -> StateSE2:
        """
        Get the final state which the expert driver achieved at the end of the scenario
        :return: StateSE2 for the final state.
        """
        pass

    @abc.abstractmethod
    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """
        Return tracked objects from iteration
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: DetectionsTracks.
        """
        pass

    @abc.abstractmethod
    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """
        Gets all tracked objects present within a time window that stretches from past_time_horizon before the iteration to future_time_horizon afterwards.
        Also optionally filters the included results on the provided track_tokens.
        Results will be sorted by object type, then by timestamp, then by track token.
        :param iteration: The iteration of the scenario to query.
        :param past_time_horizon [s]: The amount of time to look into the past from the iteration timestamp.
        :param future_time_horizon [s]: The amount of time to look into the future from the iteration timestamp.
        :param filter_track_tokens: If provided, then the results will be filtered to only contain objects with
            track_tokens included in the provided set. If None, then all results are returned.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: The retrieved detection tracks.
        """
        pass

    @property
    def initial_tracked_objects(self) -> DetectionsTracks:
        """
        Get initial tracked objects
        :return: DetectionsTracks.
        """
        return self.get_tracked_objects_at_iteration(0)

    @abc.abstractmethod
    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """
        Return sensor from iteration
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :param channels: The sensor channels to return.
        :return: Sensors.
        """
        pass

    @property
    def initial_sensors(self) -> Sensors:
        """
        Return the initial sensors (e.g. pointcloud)
        :return: Sensors.
        """
        return self.get_sensors_at_iteration(0)

    @abc.abstractmethod
    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """
        Return ego (expert) state in a dataset
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :return: EgoState of ego.
        """
        pass

    @property
    def initial_ego_state(self) -> EgoState:
        """
        Return the initial ego state
        :return: EgoState of ego.
        """
        return self.get_ego_state_at_iteration(0)

    @abc.abstractmethod
    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """
        Get traffic light status at an iteration.
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :return traffic light status at the iteration.
        """
        pass

    @abc.abstractmethod
    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets past traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the past.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the past.
        """
        pass

    @abc.abstractmethod
    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets future traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the future.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the future.
        """
        pass

    def get_expert_ego_trajectory(self) -> Generator[EgoState, None, None]:
        """
        Return trajectory that was taken by the expert-driver
        :return: sequence of agent states taken by ego.
        """
        return (self.get_ego_state_at_iteration(index) for index in range(self.get_number_of_iterations()))

    def get_ego_trajectory_slice(self, start_idx: int, end_idx: int) -> Generator[EgoState, None, None]:
        """
        Return trajectory that was taken by the expert-driver between start_idx and end_idx
        :param start_idx: starting index for ego's trajectory
        :param end_idx: ending index for ego's trajectory
        :return: sequence of agent states taken by ego
        timestamp (best matching to the database).
        """
        return (self.get_ego_state_at_iteration(index) for index in range(start_idx, end_idx))

    @abc.abstractmethod
    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """
        Find timesteps in future
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the future timestamps with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """
        Find timesteps in past
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the past
        :param time_horizon [s]: the desired horizon to the past
        :return: the future timestamps with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """
        Find ego future trajectory
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the future ego trajectory with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """
        Find ego past trajectory
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the past ego trajectory with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """
        Find past sensors
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param time_horizon: [s] the desired horizon to the future
        :param num_samples: number of entries in the future
        :param channels: The sensor channels to return.
        :return: the past sensors with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """
        Find past detections.
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param num_samples: number of entries in the future.
        :param time_horizon [s]: the desired horizon to the future.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: the past detections.
        """
        pass

    @abc.abstractmethod
    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """
        Find future detections.
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param num_samples: number of entries in the future.
        :param time_horizon [s]: the desired horizon to the future.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: the past detections.
        """
        pass

@property
def start_time(self) -> TimePoint:
    """
        Get the start time of a scenario
        :return: starting time.
        """
    return self.get_time_point(0)

@property
def end_time(self) -> TimePoint:
    """
        Get end time of the scenario
        :return: end time point.
        """
    return self.get_time_point(self.get_number_of_iterations() - 1)

@property
def initial_tracked_objects(self) -> DetectionsTracks:
    """
        Get initial tracked objects
        :return: DetectionsTracks.
        """
    return self.get_tracked_objects_at_iteration(0)

@property
def initial_sensors(self) -> Sensors:
    """
        Return the initial sensors (e.g. pointcloud)
        :return: Sensors.
        """
    return self.get_sensors_at_iteration(0)

@property
def initial_ego_state(self) -> EgoState:
    """
        Return the initial ego state
        :return: EgoState of ego.
        """
    return self.get_ego_state_at_iteration(0)

def get_expert_ego_trajectory(self) -> Generator[EgoState, None, None]:
    """
        Return trajectory that was taken by the expert-driver
        :return: sequence of agent states taken by ego.
        """
    return (self.get_ego_state_at_iteration(index) for index in range(self.get_number_of_iterations()))

def get_ego_trajectory_slice(self, start_idx: int, end_idx: int) -> Generator[EgoState, None, None]:
    """
        Return trajectory that was taken by the expert-driver between start_idx and end_idx
        :param start_idx: starting index for ego's trajectory
        :param end_idx: ending index for ego's trajectory
        :return: sequence of agent states taken by ego
        timestamp (best matching to the database).
        """
    return (self.get_ego_state_at_iteration(index) for index in range(start_idx, end_idx))

class TestIndexTimeSampling(unittest.TestCase):
    """
    Tests the index time sampling functionality.
    """

    def test_round_time_horizon(self) -> None:
        """
        Tests the conversion of N number of samples and T time horizon (round) to sample indices.
        """
        time_interval = 0.05
        frames = np.arange(0, 20, time_interval)
        indices = sample_indices_with_time_horizon(num_samples=10, time_horizon=8.0, time_interval=time_interval)
        samples = frames[indices]
        assert np.allclose(samples, np.array([0.8, 1.6, 2.4, 3.2, 4.0, 4.8, 5.6, 6.4, 7.2, 8.0]))

    def test_non_round_time_horizon(self) -> None:
        """
        Tests the conversion of N number of samples and T time horizon (non-round) to sample indices.
        """
        time_interval = 0.05
        frames = np.arange(0, 20, time_interval)
        indices = sample_indices_with_time_horizon(num_samples=12, time_horizon=1.2, time_interval=time_interval)
        samples = frames[indices]
        assert np.allclose(samples, np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]))

    def test_raises_error(self) -> None:
        """
        Tests the edge case of receiving a smaller time horizon than time interval.
        """
        self.assertRaises(ValueError, sample_indices_with_time_horizon, num_samples=3, time_horizon=0.3, time_interval=0.5)

def test_raises_error(self) -> None:
    """
        Tests the edge case of receiving a smaller time horizon than time interval.
        """
    self.assertRaises(ValueError, sample_indices_with_time_horizon, num_samples=3, time_horizon=0.3, time_interval=0.5)

class MockMapFactory(AbstractMapFactory):
    """Mock abstract map factory class used for testing."""

    def build_map_from_name(self, map_name: str) -> AbstractMap:
        """Implemented. See interface."""
        return MockAbstractMap()

def build_map_from_name(self, map_name: str) -> AbstractMap:
    """Implemented. See interface."""
    return MockAbstractMap()

class MockAbstractScenario(AbstractScenario):
    """Mock abstract scenario class used for testing."""

    def __init__(self, initial_time_us: TimePoint=TimePoint(time_us=1621641671099), time_step: float=0.5, number_of_future_iterations: int=10, number_of_past_iterations: int=0, initial_velocity: StateVector2D=StateVector2D(x=1.0, y=0.0), fixed_acceleration: StateVector2D=StateVector2D(x=0.0, y=0.0), number_of_detections: int=10, initial_ego_state: StateSE2=StateSE2(x=0.0, y=0.0, heading=0.0), mission_goal: StateSE2=StateSE2(10, 0, 0), tracked_object_types: List[TrackedObjectType]=[TrackedObjectType.VEHICLE]):
        """
        Create mocked scenario where ego starts with an initial velocity [m/s] and has a constant acceleration
            throughout (0 m/s^2 by default). The ego does not turn.
        :param initial_time_us: initial time from start point of scenario [us]
        :param time_step: time step in [s]
        :param number_of_future_iterations: number of iterations in the future
        :param number_of_past_iterations: number of iterations in the past
        :param initial_velocity: [m/s] velocity assigned to the ego at iteration 0
        :param fixed_acceleration: [m/s^2] constant ego acceleration throughout scenario
        :param number_of_detections: number of detections in the scenario
        :param initial_ego_state: Initial state of ego
        :param mission_goal: Dummy mission goal
        :param tracked_object_types: Types of tracked objects to mock
        """
        self._initial_time_us = initial_time_us
        self._time_step = time_step
        self._number_of_past_iterations = number_of_past_iterations
        self._number_of_future_iterations = number_of_future_iterations
        self._current_iteration = number_of_past_iterations
        self._total_iterations = number_of_past_iterations + number_of_future_iterations + 1
        self._tracked_object_types = tracked_object_types
        start_time_us = max(TimePoint(int(number_of_past_iterations * time_step * 1000000.0)), initial_time_us)
        time_horizon = (number_of_past_iterations + number_of_future_iterations) * time_step
        history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=10, ego_states=[EgoState.build_from_rear_axle(StateSE2(x=initial_ego_state.x, y=initial_ego_state.y, heading=initial_ego_state.heading), time_point=start_time_us, rear_axle_velocity_2d=initial_velocity, tire_steering_angle=0.0, rear_axle_acceleration_2d=fixed_acceleration, vehicle_parameters=self.ego_vehicle_parameters)], observations=[DetectionsTracks(TrackedObjects())], sample_interval=time_step)
        planner_input = PlannerInput(iteration=SimulationIteration(start_time_us, 0), history=history_buffer)
        planner = SimplePlanner(horizon_seconds=time_horizon, sampling_time=time_step, acceleration=fixed_acceleration.array)
        self._ego_states = planner.compute_trajectory(planner_input).get_sampled_trajectory()
        self._tracked_objects = [DetectionsTracks(TrackedObjects([get_sample_agent(token=str(idx + type_idx * number_of_detections), agent_type=agent_type, num_future_states=0) for idx in range(number_of_detections) for type_idx, agent_type in enumerate(self._tracked_object_types)])) for _ in range(self._total_iterations)]
        self._sensors = [Sensors(pointcloud={LidarChannel.MERGED_PC: np.eye(3) for _ in range(number_of_detections)}, images=None) for _ in range(self._total_iterations)]
        if len(self._ego_states) != len(self._tracked_objects) or len(self._ego_states) != self._total_iterations:
            raise RuntimeError('The dimensions of detections and ego trajectory is not the same!')
        self._mission_goal = mission_goal
        self._map_api = MockAbstractMap()
        self._token_suffix = str(uuid.uuid4())

    @property
    def token(self) -> str:
        """Implemented. See interface."""
        return f'mock_token_{self._token_suffix}'

    @property
    def log_name(self) -> str:
        """Implemented. See interface."""
        return 'mock_log_name'

    @property
    def scenario_name(self) -> str:
        """Implemented. See interface."""
        return 'mock_scenario_name'

    @property
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """Inherited, see superclass."""
        return get_pacifica_parameters()

    @property
    def scenario_type(self) -> str:
        """Implemented. See interface."""
        return 'mock_scenario_type'

    @property
    def map_api(self) -> AbstractMap:
        """Implemented. See interface."""
        return self._map_api

    @property
    def database_interval(self) -> float:
        """Inherited, see superclass."""
        return self._time_step

    def get_number_of_iterations(self) -> int:
        """Implemented. See interface."""
        return self._number_of_future_iterations

    def get_time_point(self, iteration: int) -> TimePoint:
        """Implemented. See interface."""
        return self._ego_states[self._current_iteration + iteration].time_point

    def get_lidar_to_ego_transform(self) -> Transform:
        """Implemented. See interface."""
        return np.eye(4)

    def get_mission_goal(self) -> Optional[StateSE2]:
        """Implemented. See interface."""
        return self._mission_goal

    def get_route_roadblock_ids(self) -> List[str]:
        """Implemented. See interface."""
        return []

    def get_expert_goal_state(self) -> StateSE2:
        """Implemented. See interface."""
        return self._mission_goal

    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Implemented. See interface."""
        return self._tracked_objects[self._current_iteration + iteration]

    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Implemented. See interface."""
        raise NotImplementedError

    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """Implemented. See interface."""
        raise NotImplementedError

    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """Implemented. See interface."""
        return self._ego_states[self._current_iteration + iteration]

    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """Implemented. see interface."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        yield dummy_data

    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Gets past traffic light status."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        for _ in range(num_samples):
            yield TrafficLightStatuses([dummy_data])

    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """Gets future traffic light status."""
        dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        for _ in range(num_samples):
            yield TrafficLightStatuses([dummy_data])

    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Implemented. See interface."""
        ego_states = self.get_ego_future_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
        for state in ego_states:
            yield state.time_point

    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Implemented. See interface."""
        ego_states = self.get_ego_past_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
        for state in ego_states:
            yield state.time_point

    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
        for idx in indices:
            yield self._ego_states[self._current_iteration + iteration + idx]

    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._current_iteration + iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}'
        for idx in reversed(indices):
            yield self._ego_states[self._current_iteration + iteration - idx]

    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """Implemented. See interface."""
        num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        for idx in indices:
            yield self._sensors[self._current_iteration + iteration - idx - 1]

    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Implemented. See interface."""
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        if self._current_iteration + iteration < indices[-1]:
            raise ValueError(f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}')
        for idx in reversed(indices):
            yield self._tracked_objects[self._current_iteration + iteration - idx]

    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Implemented. See interface."""
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
        assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
        for idx in indices:
            yield self._tracked_objects[self._current_iteration + iteration + idx]

def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
    """Gets past traffic light status."""
    dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
    num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
    for _ in range(num_samples):
        yield TrafficLightStatuses([dummy_data])

def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
    """Gets future traffic light status."""
    dummy_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=1627066061949808)
    num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
    for _ in range(num_samples):
        yield TrafficLightStatuses([dummy_data])

def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Implemented. See interface."""
    ego_states = self.get_ego_future_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
    for state in ego_states:
        yield state.time_point

def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Implemented. See interface."""
    ego_states = self.get_ego_past_trajectory(iteration=iteration, time_horizon=time_horizon, num_samples=num_samples)
    for state in ego_states:
        yield state.time_point

def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
    """Implemented. See interface."""
    num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
    indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
    assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
    for idx in indices:
        yield self._ego_states[self._current_iteration + iteration + idx]

def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
    """Implemented. See interface."""
    num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
    indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
    assert self._current_iteration + iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}'
    for idx in reversed(indices):
        yield self._ego_states[self._current_iteration + iteration - idx]

def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
    """Implemented. See interface."""
    num_samples = get_num_samples(num_samples, time_horizon, self.database_interval)
    indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
    for idx in indices:
        yield self._sensors[self._current_iteration + iteration - idx - 1]

def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
    """Implemented. See interface."""
    indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
    if self._current_iteration + iteration < indices[-1]:
        raise ValueError(f'Requested time horizon of {time_horizon}s is too long! Scenario past has length {(self._current_iteration + iteration) * self._time_step}s from the iteration {iteration}')
    for idx in reversed(indices):
        yield self._tracked_objects[self._current_iteration + iteration - idx]

def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
    """Implemented. See interface."""
    indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._time_step)
    assert self._number_of_future_iterations - iteration >= indices[-1], f'Requested time horizon of {time_horizon}s is too long! Scenario future has length {(self._number_of_future_iterations - iteration) * self._time_step}s from the iteration {iteration}'
    for idx in indices:
        yield self._tracked_objects[self._current_iteration + iteration + idx]

class NuPlanScenario(AbstractScenario):
    """Scenario implementation for the nuPlan dataset that is used in training and simulation."""

    def __init__(self, data_root: str, log_file_load_path: str, initial_lidar_token: str, initial_lidar_timestamp: int, scenario_type: str, map_root: str, map_version: str, map_name: str, scenario_extraction_info: Optional[ScenarioExtractionInfo], ego_vehicle_parameters: VehicleParameters, sensor_root: Optional[str]=None) -> None:
        """
        Initialize the nuPlan scenario.
        :param data_root: The prefix for the log file. e.g. "/data/root/nuplan". For remote paths, this is where the file will be downloaded if necessary.
        :param log_file_load_path: Name of the log that this scenario belongs to. e.g. "/data/sets/nuplan-v1.1/splits/mini/2021.07.16.20.45.29_veh-35_01095_01486.db", "s3://path/to/db.db"
        :param initial_lidar_token: Token of the scenario's initial lidarpc.
        :param initial_lidar_timestamp: The timestamp of the initial lidarpc.
        :param scenario_type: Type of scenario (e.g. ego overtaking).
        :param map_root: The root path for the map db
        :param map_version: The version of maps to load
        :param map_name: The map name to use for the scenario
        :param scenario_extraction_info: Structure containing information used to extract the scenario.
            None means the scenario has no length and it is comprised only by the initial lidarpc.
        :param ego_vehicle_parameters: Structure containing the vehicle parameters.
        :param sensor_root: The root path for the sensor blobs.
        """
        self._local_store: Optional[LocalStore] = None
        self._remote_store: Optional[S3Store] = None
        self._data_root = data_root
        self._log_file_load_path = log_file_load_path
        self._initial_lidar_token = initial_lidar_token
        self._initial_lidar_timestamp = initial_lidar_timestamp
        self._scenario_type = scenario_type
        self._map_root = map_root
        self._map_version = map_version
        self._map_name = map_name
        self._scenario_extraction_info = scenario_extraction_info
        self._ego_vehicle_parameters = ego_vehicle_parameters
        self._sensor_root = sensor_root
        if self._scenario_extraction_info is not None:
            skip_rows = 1.0 / self._scenario_extraction_info.subsample_ratio
            if abs(int(skip_rows) - skip_rows) > 0.001:
                raise ValueError(f'Subsample ratio is not valid. Must resolve to an integer number of skipping rows, instead received {self._scenario_extraction_info.subsample_ratio}, which would skip {skip_rows} rows.')
        self._database_row_interval = 0.05
        self._log_file = download_file_if_necessary(self._data_root, self._log_file_load_path)
        self._log_name: str = absolute_path_to_log_name(self._log_file)

    def __reduce__(self) -> Tuple[Type[NuPlanScenario], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._data_root, self._log_file_load_path, self._initial_lidar_token, self._initial_lidar_timestamp, self._scenario_type, self._map_root, self._map_version, self._map_name, self._scenario_extraction_info, self._ego_vehicle_parameters, self._sensor_root))

    @property
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """Inherited, see superclass."""
        return self._ego_vehicle_parameters

    @cached_property
    def _lidarpc_tokens(self) -> List[str]:
        """
        :return: list of lidarpc tokens in the scenario
        """
        if self._scenario_extraction_info is None:
            return [self._initial_lidar_token]
        lidarpc_tokens = list(extract_sensor_tokens_as_scenario(self._log_file, get_lidarpc_sensor_data(), self._initial_lidar_timestamp, self._scenario_extraction_info))
        return cast(List[str], lidarpc_tokens)

    @cached_property
    def _route_roadblock_ids(self) -> List[str]:
        """
        return: Route roadblock ids extracted from expert trajectory.
        """
        expert_trajectory = list(self._extract_expert_trajectory())
        return get_roadblock_ids_from_trajectory(self.map_api, expert_trajectory)

    @property
    def token(self) -> str:
        """Inherited, see superclass."""
        return self._initial_lidar_token

    @property
    def log_name(self) -> str:
        """Inherited, see superclass."""
        return self._log_name

    @property
    def scenario_name(self) -> str:
        """Inherited, see superclass."""
        return self.token

    @property
    def scenario_type(self) -> str:
        """Inherited, see superclass."""
        return self._scenario_type

    @property
    def map_api(self) -> AbstractMap:
        """Inherited, see superclass."""
        return get_maps_api(self._map_root, self._map_version, self._map_name)

    @property
    def map_root(self) -> str:
        """Get the map root folder."""
        return self._map_root

    @property
    def map_version(self) -> str:
        """Get the map version."""
        return self._map_version

    @property
    def database_interval(self) -> float:
        """Inherited, see superclass."""
        if self._scenario_extraction_info is None:
            return 0.05
        return float(0.05 / self._scenario_extraction_info.subsample_ratio)

    def get_number_of_iterations(self) -> int:
        """Inherited, see superclass."""
        return len(self._lidarpc_tokens)

    def get_lidar_to_ego_transform(self) -> Transform:
        """Inherited, see superclass."""
        return get_sensor_transform_matrix_for_sensor_data_token_from_db(self._log_file, get_lidarpc_sensor_data(), self._initial_lidar_token)

    def get_mission_goal(self) -> Optional[StateSE2]:
        """Inherited, see superclass."""
        return get_mission_goal_for_sensor_data_token_from_db(self._log_file, get_lidarpc_sensor_data(), self._initial_lidar_token)

    def get_route_roadblock_ids(self) -> List[str]:
        """Inherited, see superclass."""
        roadblock_ids = get_roadblock_ids_for_lidarpc_token_from_db(self._log_file, self._initial_lidar_token)
        assert roadblock_ids is not None, 'Unable to find Roadblock ids for current scenario'
        return cast(List[str], roadblock_ids)

    def get_expert_goal_state(self) -> StateSE2:
        """Inherited, see superclass."""
        return get_statese2_for_lidarpc_token_from_db(self._log_file, self._lidarpc_tokens[-1])

    def get_time_point(self, iteration: int) -> TimePoint:
        """Inherited, see superclass."""
        return TimePoint(time_us=get_sensor_data_token_timestamp_from_db(self._log_file, get_lidarpc_sensor_data(), self._lidarpc_tokens[iteration]))

    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """Inherited, see superclass."""
        return get_ego_state_for_lidarpc_token_from_db(self._log_file, self._lidarpc_tokens[iteration])

    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Inherited, see superclass."""
        assert 0 <= iteration < self.get_number_of_iterations(), f'Iteration is out of scenario: {iteration}!'
        return DetectionsTracks(extract_tracked_objects(self._lidarpc_tokens[iteration], self._log_file, future_trajectory_sampling))

    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """Inherited, see superclass."""
        assert 0 <= iteration < self.get_number_of_iterations(), f'Iteration is out of scenario: {iteration}!'
        return DetectionsTracks(extract_tracked_objects_within_time_window(self._lidarpc_tokens[iteration], self._log_file, past_time_horizon, future_time_horizon, filter_track_tokens, future_trajectory_sampling))

    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """Inherited, see superclass."""
        channels = [LidarChannel.MERGED_PC] if channels is None else channels
        lidar_pc = next(get_sensor_data_from_sensor_data_tokens_from_db(self._log_file, get_lidarpc_sensor_data(), LidarPc, [self._lidarpc_tokens[iteration]]))
        return self._get_sensor_data_from_lidar_pc(cast(LidarPc, lidar_pc), channels)

    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Inherited, see superclass."""
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, True):
            yield TimePoint(lidar_pc.timestamp)

    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """Inherited, see superclass."""
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, False):
            yield TimePoint(lidar_pc.timestamp)

    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Inherited, see superclass."""
        num_samples = num_samples if num_samples else int(time_horizon / self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._database_row_interval)
        return cast(Generator[EgoState, None, None], get_sampled_ego_states_from_db(self._log_file, self._lidarpc_tokens[iteration], get_lidarpc_sensor_data(), indices, future=False))

    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """Inherited, see superclass."""
        num_samples = num_samples if num_samples else int(time_horizon / self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._database_row_interval)
        return cast(Generator[EgoState, None, None], get_sampled_ego_states_from_db(self._log_file, self._lidarpc_tokens[iteration], get_lidarpc_sensor_data(), indices, future=True))

    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Inherited, see superclass."""
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, False):
            yield DetectionsTracks(extract_tracked_objects(lidar_pc.token, self._log_file, future_trajectory_sampling))

    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """Inherited, see superclass."""
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, True):
            yield DetectionsTracks(extract_tracked_objects(lidar_pc.token, self._log_file, future_trajectory_sampling))

    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """Inherited, see superclass."""
        channels = [LidarChannel.MERGED_PC] if channels is None else channels
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, False):
            yield self._get_sensor_data_from_lidar_pc(lidar_pc, channels)

    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """Inherited, see superclass."""
        token = self._lidarpc_tokens[iteration]
        return cast(Generator[TrafficLightStatusData, None, None], get_traffic_light_status_for_lidarpc_token_from_db(self._log_file, token))

    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets past traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the past.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the past.
        """
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, False):
            yield TrafficLightStatuses(list(get_traffic_light_status_for_lidarpc_token_from_db(self._log_file, lidar_pc.token)))

    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets future traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the future.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the future.
        """
        for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, True):
            yield TrafficLightStatuses(list(get_traffic_light_status_for_lidarpc_token_from_db(self._log_file, lidar_pc.token)))

    def get_scenario_tokens(self) -> List[str]:
        """Return the list of lidarpc tokens from the DB that are contained in the scenario."""
        return self._lidarpc_tokens

    def _find_matching_lidar_pcs(self, iteration: int, num_samples: Optional[int], time_horizon: float, look_into_future: bool) -> Generator[LidarPc, None, None]:
        """
        Find the best matching lidar_pcs to the desired samples and time horizon
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future, if None it will be deduced from the DB
        :param time_horizon: the desired horizon to the future
        :param look_into_future: if True, we will iterate into next lidar_pc otherwise we will iterate through prev
        :return: lidar_pcs matching to database indices
        """
        num_samples = num_samples if num_samples else int(time_horizon / self.database_interval)
        indices = sample_indices_with_time_horizon(num_samples, time_horizon, self._database_row_interval)
        return cast(Generator[LidarPc, None, None], get_sampled_lidarpcs_from_db(self._log_file, self._lidarpc_tokens[iteration], get_lidarpc_sensor_data(), indices, look_into_future))

    def _extract_expert_trajectory(self, max_future_seconds: int=60) -> Generator[EgoState, None, None]:
        """
        Extract expert trajectory with specified time parameters. If initial lidar pc does not have enough history/future
            only available time will be extracted
        :param max_future_seconds: time to future which should be considered for route extraction [s]
        :return: list of expert ego states
        """
        minimal_required_future_time_available = 0.5
        end_log_time_us = get_end_sensor_time_from_db(self._log_file, get_lidarpc_sensor_data())
        max_future_time = min((end_log_time_us - self._initial_lidar_timestamp) * 1e-06, max_future_seconds)
        if max_future_time < minimal_required_future_time_available:
            return
        for traj in self.get_ego_future_trajectory(0, max_future_time):
            yield traj

    def _create_blob_store_if_needed(self) -> Tuple[LocalStore, Optional[S3Store]]:
        """
        A convenience method that creates the blob stores if it's not already created.
        :return: The created or cached LocalStore and S3Store objects.
        """
        if self._local_store is not None and self._remote_store is not None:
            return (self._local_store, self._remote_store)
        if self._sensor_root is None:
            raise ValueError('sensor_root is not set. Please set the sensor_root to access sensor data.')
        Path(self._sensor_root).mkdir(exist_ok=True)
        self._local_store = LocalStore(self._sensor_root)
        if os.getenv('NUPLAN_DATA_STORE', '') == 's3':
            s3_url = os.getenv('NUPLAN_DATA_ROOT_S3_URL', '')
            self._remote_store = S3Store(os.path.join(s3_url, 'sensor_blobs'), show_progress=True)
        return (self._local_store, self._remote_store)

    def _get_sensor_data_from_lidar_pc(self, lidar_pc: LidarPc, channels: List[SensorChannel]) -> Sensors:
        """
        Loads Sensor data given a database LidarPC object.
        :param lidar_pc: The lidar_pc for which to grab the point cloud.
        :param channels: The sensor channels to return.
        :return: The corresponding sensor data.
        """
        local_store, remote_store = self._create_blob_store_if_needed()
        retrieved_images = get_images_from_lidar_tokens(self._log_file, [lidar_pc.token], [cast(str, channel.value) for channel in channels])
        lidar_pcs = {LidarChannel.MERGED_PC: load_point_cloud(cast(LidarPc, lidar_pc), local_store, remote_store)} if LidarChannel.MERGED_PC in channels else None
        images = {CameraChannel[image.channel]: load_image(image, local_store, remote_store) for image in retrieved_images}
        return Sensors(pointcloud=lidar_pcs, images=images if images else None)

def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
    """Inherited, see superclass."""
    assert 0 <= iteration < self.get_number_of_iterations(), f'Iteration is out of scenario: {iteration}!'
    return DetectionsTracks(extract_tracked_objects_within_time_window(self._lidarpc_tokens[iteration], self._log_file, past_time_horizon, future_time_horizon, filter_track_tokens, future_trajectory_sampling))

def _filter_goals(scenarios: List[NuPlanScenario]) -> List[NuPlanScenario]:
    """
        Filter scenarios that contain invalid mission goals.
        :param scenarios: List of scenarios to filter.
        :return: List of filtered scenarios.
        """
    return [scenario for scenario in scenarios if scenario.get_mission_goal()]

def _is_non_stationary(scenario: NuPlanScenario, minimum_threshold: float) -> bool:
    """
    Determines whether the ego cumulatively moves at least minimum_threshold meters over the course of a given scenario
    :param scenario: a NuPlan expert scenario
    :param minimum_threshold: minimum distance in meters (inclusive) the ego center has to travel in the scenario
        for the ego to be determined non-stationary
    :return: True if the cumulative frame-to-frame displacement of the ego center in the scenario
        is >= the minimum threshold
    """
    trajectory = scenario.get_ego_future_trajectory(iteration=0, time_horizon=scenario.duration_s.time_s)
    trajectory_xy_matrix = np.array([[state.center.x, state.center.y] for state in trajectory])
    current_state = trajectory_xy_matrix[:-1]
    next_state = trajectory_xy_matrix[1:]
    total_ego_displacement = np.sum(np.linalg.norm(next_state - current_state, axis=1))
    return bool(total_ego_displacement >= minimum_threshold)

def _check_for_speed_edge(scenario: NuPlanScenario, speed_threshold: float, speed_noise_tolerance: float, edge_type: EdgeType) -> bool:
    """
    For a given scenario, determine whether there is a sub-scenario in which the ego's speed either
        rises above or falls below the speed_threshold.

    :param scenario: a NuPlan scenario
    :speed_threshold: what rear axle speed does the ego have to pass above (exclusive) to have "started moving?"
        likewise, what rear axle speed does the ego have to fall below (inclusive) to have "stopped moving?"
    :param speed_noise_tolerance: a value at or below which a speed change be ignored as noise.
    :param edge_type: are we filtering for speed RISING above the threshold or FALLING below the threshold?
    :return: a boolean, revealing whether a RISING/FALLING ego speed edge is present in the given scenario.
        or equal to the speed threshold and a subsequent frame in which the ego's speed is above the speed threshold.
        The second tells whether the scenario contains one frame in which the ego's speed is above the speed
        threshold and a subsequent frame in which the ego's speed is below or equal to the speed threshold.
    """
    if speed_noise_tolerance is None:
        speed_noise_tolerance = 0.1
    initial_ego_state = scenario.get_ego_state_at_iteration(0)
    current_speed, start_detector, stop_detector = (initial_ego_state.dynamic_car_state.rear_axle_velocity_2d.magnitude(),) * 3
    edge_type_presence = [False, False]
    for next_ego_state in scenario.get_ego_future_trajectory(iteration=0, time_horizon=scenario.duration_s.time_s):
        next_speed = next_ego_state.dynamic_car_state.rear_axle_velocity_2d.magnitude()
        if next_speed > start_detector:
            start_detector = next_speed
            if start_detector > speed_threshold >= stop_detector and start_detector - stop_detector > speed_noise_tolerance:
                edge_type_presence[EdgeType.RISING] = True
                stop_detector = start_detector
        if next_speed < stop_detector:
            stop_detector = next_speed
            if start_detector > speed_threshold >= stop_detector and start_detector - stop_detector > speed_noise_tolerance:
                edge_type_presence[EdgeType.FALLING] = True
                start_detector = stop_detector
    return edge_type_presence[edge_type]

def _ego_has_route(scenario: NuPlanScenario, map_radius: float) -> bool:
    """
    Determines the presence of an on-route lane segment in a VectorMap built from
    the given scenario within map_radius meters of the ego.
    :param scenario: A NuPlan scenario.
    :param map_radius: the radius of the VectorMap built around the ego's position
    to check for on-route lane segments.
    :return: True if there is at least one on-route lane segment in the VectorMap.
    """
    ego_state = scenario.initial_ego_state
    ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
    _, _, _, _, lane_seg_roadblock_ids = get_neighbor_vector_map(scenario.map_api, ego_coords, map_radius)
    map_lane_roadblock_ids = set(lane_seg_roadblock_ids.roadblock_ids)
    return len(map_lane_roadblock_ids.intersection(scenario.get_route_roadblock_ids())) > 0

class TestCachedScenario(unittest.TestCase):
    """
    Test suite for CachedScenario
    """

    def _make_cached_scenario(self) -> CachedScenario:
        return CachedScenario(log_name='log/name', token='token', scenario_type='type')

    def test_token(self) -> None:
        """
        Test the token method.
        """
        scenario = self._make_cached_scenario()
        self.assertEqual('token', scenario.token)

    def test_log_name(self) -> None:
        """
        Test the log_name method.
        """
        scenario = self._make_cached_scenario()
        self.assertEqual('log/name', scenario.log_name)

    def test_scenario_name_raises(self) -> None:
        """
        Test that the scenario_name method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.scenario_name

    def test_ego_vehicle_parameters_raises(self) -> None:
        """
        Test that the ego_vehicle_parameters method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.ego_vehicle_parameters

    def test_scenario_type(self) -> None:
        """
        Test that the scenario_type method returns scenario_type.
        """
        scenario = self._make_cached_scenario()
        self.assertEqual('type', scenario.scenario_type)

    def test_map_api_raises(self) -> None:
        """
        Test that the map_api method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.map_api

    def test_database_interval_raises(self) -> None:
        """
        Test that the database_interval method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.database_interval

    def test_get_number_of_iterations_raises(self) -> None:
        """
        Test that the get_number_of_iterations method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_number_of_iterations()

    def test_get_time_point_raises(self) -> None:
        """
        Test that the get_time_point method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_time_point()

    def test_get_lidar_to_ego_transform_raises(self) -> None:
        """
        Test that the get_lidar_to_ego_transform method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_lidar_to_ego_transform()

    def test_get_mission_goal_raises(self) -> None:
        """
        Test that the get_mission_goal method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_mission_goal()

    def test_get_route_roadblock_ids_raises(self) -> None:
        """
        Test that the get_route_roadblock_ids method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_route_roadblock_ids()

    def test_get_expert_goal_state_raises(self) -> None:
        """
        Test that the get_expert_goal_state method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_expert_goal_state()

    def test_get_tracked_objects_at_iteration_raises(self) -> None:
        """
        Test that the get_tracked_objects_at_iteration method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_tracked_objects_at_iteration(0)

    def test_get_sensors_at_iteration_raises(self) -> None:
        """
        Test that the get_sensors_at_iteration method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_sensors_at_iteration(0)

    def test_get_ego_state_at_iteration_raises(self) -> None:
        """
        Test that the get_ego_state_at_iteration method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_ego_state_at_iteration(0)

    def test_get_traffic_light_status_at_iteration_raises(self) -> None:
        """
        Test that the get_traffic_light_status_at_iteration method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_traffic_light_status_at_iteration(0)

    def test_get_future_timestamps_raises(self) -> None:
        """
        Test that the get_future_timestamps method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_future_timestamps(0, 0, 0)

    def test_get_past_timestamps_raises(self) -> None:
        """
        Test that the get_past_timestamps method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_past_timestamps(0, 0, 0)

    def test_ego_future_trajectory_raises(self) -> None:
        """
        Test that the ego_future_trajectory method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_ego_future_trajectory(0, 0, 0)

    def test_get_ego_past_trajectory_raises(self) -> None:
        """
        Test that the get_ego_past_trajectory method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_ego_past_trajectory(0, 0, 0)

    def test_get_past_sensors_raises(self) -> None:
        """
        Test that the get_past_sensors method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_past_sensors(0, 0, 0)

    def test_get_past_tracked_objects_raises(self) -> None:
        """
        Test that the get_past_tracked_objects method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_past_tracked_objects(0, 0, 0)

    def test_get_future_tracked_objects_raises(self) -> None:
        """
        Test that the get_future_tracked_objects method raises an error.
        """
        scenario = self._make_cached_scenario()
        with self.assertRaises(NotImplementedError):
            _ = scenario.get_future_tracked_objects(0, 0, 0)

def test_token(self) -> None:
    """
        Test the token method.
        """
    scenario = self._make_cached_scenario()
    self.assertEqual('token', scenario.token)

def test_log_name(self) -> None:
    """
        Test the log_name method.
        """
    scenario = self._make_cached_scenario()
    self.assertEqual('log/name', scenario.log_name)

def test_scenario_name_raises(self) -> None:
    """
        Test that the scenario_name method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.scenario_name

def test_ego_vehicle_parameters_raises(self) -> None:
    """
        Test that the ego_vehicle_parameters method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.ego_vehicle_parameters

def test_scenario_type(self) -> None:
    """
        Test that the scenario_type method returns scenario_type.
        """
    scenario = self._make_cached_scenario()
    self.assertEqual('type', scenario.scenario_type)

def test_map_api_raises(self) -> None:
    """
        Test that the map_api method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.map_api

def test_database_interval_raises(self) -> None:
    """
        Test that the database_interval method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.database_interval

def test_get_number_of_iterations_raises(self) -> None:
    """
        Test that the get_number_of_iterations method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_number_of_iterations()

def test_get_time_point_raises(self) -> None:
    """
        Test that the get_time_point method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_time_point()

def test_get_lidar_to_ego_transform_raises(self) -> None:
    """
        Test that the get_lidar_to_ego_transform method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_lidar_to_ego_transform()

def test_get_mission_goal_raises(self) -> None:
    """
        Test that the get_mission_goal method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_mission_goal()

def test_get_route_roadblock_ids_raises(self) -> None:
    """
        Test that the get_route_roadblock_ids method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_route_roadblock_ids()

def test_get_expert_goal_state_raises(self) -> None:
    """
        Test that the get_expert_goal_state method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_expert_goal_state()

def test_get_tracked_objects_at_iteration_raises(self) -> None:
    """
        Test that the get_tracked_objects_at_iteration method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_tracked_objects_at_iteration(0)

def test_get_sensors_at_iteration_raises(self) -> None:
    """
        Test that the get_sensors_at_iteration method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_sensors_at_iteration(0)

def test_get_ego_state_at_iteration_raises(self) -> None:
    """
        Test that the get_ego_state_at_iteration method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_ego_state_at_iteration(0)

def test_get_traffic_light_status_at_iteration_raises(self) -> None:
    """
        Test that the get_traffic_light_status_at_iteration method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_traffic_light_status_at_iteration(0)

def test_get_future_timestamps_raises(self) -> None:
    """
        Test that the get_future_timestamps method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_future_timestamps(0, 0, 0)

def test_get_past_timestamps_raises(self) -> None:
    """
        Test that the get_past_timestamps method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_past_timestamps(0, 0, 0)

def test_ego_future_trajectory_raises(self) -> None:
    """
        Test that the ego_future_trajectory method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_ego_future_trajectory(0, 0, 0)

def test_get_ego_past_trajectory_raises(self) -> None:
    """
        Test that the get_ego_past_trajectory method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_ego_past_trajectory(0, 0, 0)

def test_get_past_sensors_raises(self) -> None:
    """
        Test that the get_past_sensors method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_past_sensors(0, 0, 0)

def test_get_past_tracked_objects_raises(self) -> None:
    """
        Test that the get_past_tracked_objects method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_past_tracked_objects(0, 0, 0)

def test_get_future_tracked_objects_raises(self) -> None:
    """
        Test that the get_future_tracked_objects method raises an error.
        """
    scenario = self._make_cached_scenario()
    with self.assertRaises(NotImplementedError):
        _ = scenario.get_future_tracked_objects(0, 0, 0)

class SubmissionContainer:
    """Class handling a submission Docker container"""

    def __init__(self, submission_image: str, container_name: str, port: int):
        """
        :param submission_image: Name of the docker image of the submission
        :param container_name: Name for the container to be run
        :param port: Port number to be used for communication
        """
        self.submission_image = submission_image
        self.container_name = container_name
        self.port = port
        self.client: docker.client.DockerClient | None = None

    def __del__(self) -> None:
        """Stop the running container when the destructor is called."""
        self.stop()

    def start(self, cpus: str='0,1', gpus: list[str] | None=None) -> Any:
        """
        Starts the submission container given a docker client, and the submission details. It exposes the specified
        port, and volume mounts (read only) the data directory to make it available to the container.
        :param cpus: CPUs to be used by the submission container
        :param gpus: GPUs to be used by the submission container
        """
        if gpus is None:
            gpus = ['0']
        self.client = docker.from_env()
        self.stop()
        ports = {f'{str(self.port)}': self.port}
        self.client.containers.run(self.submission_image, name=self.container_name, detach=True, ports=ports, tty=True, environment={'SUBMISSION_CONTAINER_PORT': str(self.port)}, device_requests=[docker.types.DeviceRequest(device_ids=gpus, capabilities=[['gpu']])], cpuset_cpus=cpus, volumes={os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'): {'bind': '/data/sets/nuplan', 'mode': 'ro'}})
        logging.debug(f'Started submission container with image: {self.submission_image} with port: {self.port}')
        return self.client.containers.get(self.container_name)

    def stop(self) -> None:
        """Checks if the submission container is running, if it is it stops and removes it."""
        try:
            container = self.client.containers.get(self.container_name)
        except NotFound:
            pass
        else:
            logging.debug('Stopping and removing pre-existing container')
            try:
                container.kill()
            except docker.errors.APIError:
                pass
            container.remove()

    def wait_until_running(self, timeout: float=3) -> None:
        """
        Waits until a container is running until timeout.
        :param timeout: timeout in seconds
        """

        def is_running(manager: SubmissionContainer) -> bool:
            """
            Checks if the container is running
            :param manager: The container manager
            :returns: True if the container is in running state
            """
            return bool(manager.client.api.inspect_container(manager.container_name)['State']['Status'] == 'running')
        keep_trying(is_running, [self], {}, (docker.errors.NotFound,), timeout)

def wait_until_running(self, timeout: float=3) -> None:
    """
        Waits until a container is running until timeout.
        :param timeout: timeout in seconds
        """

    def is_running(manager: SubmissionContainer) -> bool:
        """
            Checks if the container is running
            :param manager: The container manager
            :returns: True if the container is in running state
            """
        return bool(manager.client.api.inspect_container(manager.container_name)['State']['Status'] == 'running')
    keep_trying(is_running, [self], {}, (docker.errors.NotFound,), timeout)

class DetectionTracksChallengeServicer(chpb_grpc.DetectionTracksChallengeServicer):
    """
    Servicer for exposing initialization and trajectory computation services to the client.
    It keeps a rolling history buffer to avoid unnecessary serialization/deserialization.
    """

    def __init__(self, planner_config: DictConfig, map_manager: MapManager):
        """
        :param planner_config: The planner configuration to instantiate the planner.
        :param map_manager: The map manager.
        """
        self.planner: Optional[AbstractPlanner] = None
        self._planner_config = planner_config
        self.map_manager = map_manager
        self.simulation_history_buffer: Optional[SimulationHistoryBuffer] = None
        self._initialized = False

    @staticmethod
    def _extract_simulation_iteration(planner_input_message: chpb.PlannerInput) -> SimulationIteration:
        return SimulationIteration(TimePoint(planner_input_message.simulation_iteration.time_us), planner_input_message.simulation_iteration.index)

    def _build_planner_input(self, planner_input_message: chpb.PlannerInput, buffer: Optional[SimulationHistoryBuffer]) -> PlannerInput:
        """
        Builds a PlannerInput from a serialized PlannerInput message and an existing data buffer
        :param planner_input_message: the serialized message
        :param buffer: The history buffer
        :return: PlannerInput object
        """
        simulation_iteration = self._extract_simulation_iteration(planner_input_message)
        new_data = planner_input_message.simulation_history_buffer
        states = []
        observations = []
        for serialized_state, serialized_observation in zip(new_data.ego_states, new_data.observations):
            states.append(pickle.loads(serialized_state))
            observations.append(pickle.loads(serialized_observation))
        if buffer is not None:
            buffer.extend(states, observations)
        else:
            buffer = SimulationHistoryBuffer.initialize_from_list(len(states), states, observations, new_data.sample_interval)
            self.simulation_history_buffer = buffer
        tl_data_messages = planner_input_message.traffic_light_data
        tl_data = [tl_status_data_from_proto_tl_status_data(tl_data_message) for tl_data_message in tl_data_messages]
        return PlannerInput(iteration=simulation_iteration, history=buffer, traffic_light_data=tl_data)

    def InitializePlanner(self, planner_initialization_message: chpb.PlannerInitializationLight, context: Any) -> chpb.Empty:
        """
        Service to initialize the planner given the initialization request.
        :param planner_initialization_message: Message containing initialization details
        :param context
        """
        planners = build_planners(self._planner_config, None)
        assert len(planners) == 1, f'Configuration should build exactly 1 planner, got {len(planners)} instead!'
        self.planner = planners[0]
        logger.info('Initialization request received..')
        route_roadblock_ids = planner_initialization_message.route_roadblock_ids
        mission_goal = se2_from_proto_se2(planner_initialization_message.mission_goal)
        map_api = self.map_manager.get_map(planner_initialization_message.map_name)
        map_api.initialize_all_layers()
        planner_initialization = PlannerInitialization(route_roadblock_ids=route_roadblock_ids, mission_goal=mission_goal, map_api=map_api)
        self.simulation_history_buffer = None
        self.planner.initialize(planner_initialization)
        logging.info('Planner initialized!')
        self._initialized = True
        return chpb.Empty()

    def ComputeTrajectory(self, planner_input_message: chpb.PlannerInput, context: Any) -> chpb.Trajectory:
        """
        Service to compute a trajectory given a planner input message
        :param planner_input_message: Message containing the input to the planner
        :param context
        :return Message containing the computed trajectories
        """
        assert self._initialized, 'Planner has not been initialized. Please call InitializePlanner'
        planner_inputs = self._build_planner_input(planner_input_message, self.simulation_history_buffer)
        if isinstance(self.planner, AbstractPlanner):
            trajectory = self.planner.compute_trajectory(planner_inputs)
            return proto_traj_from_inter_traj(trajectory)
        raise RuntimeError('The planner was not initialized correctly!')

def _build_planner_input(self, planner_input_message: chpb.PlannerInput, buffer: Optional[SimulationHistoryBuffer]) -> PlannerInput:
    """
        Builds a PlannerInput from a serialized PlannerInput message and an existing data buffer
        :param planner_input_message: the serialized message
        :param buffer: The history buffer
        :return: PlannerInput object
        """
    simulation_iteration = self._extract_simulation_iteration(planner_input_message)
    new_data = planner_input_message.simulation_history_buffer
    states = []
    observations = []
    for serialized_state, serialized_observation in zip(new_data.ego_states, new_data.observations):
        states.append(pickle.loads(serialized_state))
        observations.append(pickle.loads(serialized_observation))
    if buffer is not None:
        buffer.extend(states, observations)
    else:
        buffer = SimulationHistoryBuffer.initialize_from_list(len(states), states, observations, new_data.sample_interval)
        self.simulation_history_buffer = buffer
    tl_data_messages = planner_input_message.traffic_light_data
    tl_data = [tl_status_data_from_proto_tl_status_data(tl_data_message) for tl_data_message in tl_data_messages]
    return PlannerInput(iteration=simulation_iteration, history=buffer, traffic_light_data=tl_data)

def InitializePlanner(self, planner_initialization_message: chpb.PlannerInitializationLight, context: Any) -> chpb.Empty:
    """
        Service to initialize the planner given the initialization request.
        :param planner_initialization_message: Message containing initialization details
        :param context
        """
    planners = build_planners(self._planner_config, None)
    assert len(planners) == 1, f'Configuration should build exactly 1 planner, got {len(planners)} instead!'
    self.planner = planners[0]
    logger.info('Initialization request received..')
    route_roadblock_ids = planner_initialization_message.route_roadblock_ids
    mission_goal = se2_from_proto_se2(planner_initialization_message.mission_goal)
    map_api = self.map_manager.get_map(planner_initialization_message.map_name)
    map_api.initialize_all_layers()
    planner_initialization = PlannerInitialization(route_roadblock_ids=route_roadblock_ids, mission_goal=mission_goal, map_api=map_api)
    self.simulation_history_buffer = None
    self.planner.initialize(planner_initialization)
    logging.info('Planner initialized!')
    self._initialized = True
    return chpb.Empty()

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

def update_submission_data(self, data: Dict[str, str]) -> Any:
    """
        Updates the status of a submission according to the input data.
        :param data: The information to update the submission. The submission is specified in data.
        :return: Server response.
        """
    url = self._format_url('update_submission')
    response = self._request(url, 'PUT', data)
    return response

class TestEvalaiInterface(unittest.TestCase):
    """Tests interface class to EvalAI api."""

    @patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': '1234', 'EVALAI_PERSONAL_AUTH_TOKEN': 'authorization_token'})
    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.evalai = EvalaiInterface('bounce_server')

    def test_initialization(self) -> None:
        """Checks that initialization works and fails as expected."""
        self.assertEqual(self.evalai.EVALAI_AUTH_TOKEN, 'authorization_token')
        self.assertEqual(self.evalai.CHALLENGE_PK, '1234')
        self.assertEqual(self.evalai.EVALAI_API_SERVER, 'bounce_server')
        with patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': ''}):
            with self.assertRaises(AssertionError):
                _ = EvalaiInterface('server')
        with patch.dict(os.environ, {'EVALAI_PERSONAL_AUTH_TOKEN': ''}):
            with self.assertRaises(AssertionError):
                _ = EvalaiInterface('server')

    @patch('requests.request', side_effect=mocked_put_request)
    def test_update_submission_data(self, mock_put: Mock) -> None:
        """Tests update submission with mock server."""
        test_payload = {'test': 'payload'}
        response = self.evalai.update_submission_data(test_payload)
        self.assertEqual(response, test_payload)
        expected_call = call(method='PUT', url='bounce_server/api/jobs/challenge/1234/update_submission/', headers={'Authorization': 'Bearer authorization_token'}, data=test_payload)
        self.assertEqual(response, test_payload)
        self.assertIn(expected_call, mock_put.call_args_list)
        self.assertEqual(len(mock_put.call_args_list), 1)

    def test_fail_on_missing_api(self) -> None:
        """Test failure of url generation on missing api."""
        with self.assertRaises(AssertionError):
            _ = self.evalai._format_url('missing_api')

def test_fail_on_missing_api(self) -> None:
    """Test failure of url generation on missing api."""
    with self.assertRaises(AssertionError):
        _ = self.evalai._format_url('missing_api')

class SubmissionComputesTrajectoryValidator(BaseSubmissionValidator):
    """Checks if a submission is able to compute a trajectory"""

    def validate(self, submission: str) -> bool:
        """
        Checks if the provided submission is able to provide a trajectory given an input.
        :param submission: The submission image
        :return: Whether the submission is able to compute a trajectory
        """
        logger.info('validating trajectory computation')
        scenario = get_test_nuplan_scenario()
        step = 0
        iteration = SimulationIteration(time_point=scenario.get_time_point(0), index=0)
        history = SimulationHistoryBuffer.initialize_from_list(1, [scenario.get_ego_state_at_iteration(step)], [scenario.get_tracked_objects_at_iteration(step)], scenario.database_interval)
        planner_input = PlannerInput(iteration, history)
        container_name = container_name_from_image_name(submission)
        container_manager = SubmissionContainerManager(SubmissionContainerFactory())
        planner = RemotePlanner(container_manager, submission, container_name)
        planner_initialization = PlannerInitialization(scenario.get_mission_goal(), scenario.get_route_roadblock_ids(), scenario.map_api)
        planner.initialize([planner_initialization])
        trajectory = planner.compute_trajectory([planner_input])
        if trajectory:
            logger.debug(f'Computed trajectory {trajectory}')
            return True
        logger.error('Submission failed to compute trajectory')
        self._failing_validator = SubmissionComputesTrajectoryValidator
        return False

def validate(self, submission: str) -> bool:
    """
        Checks if the provided submission is able to provide a trajectory given an input.
        :param submission: The submission image
        :return: Whether the submission is able to compute a trajectory
        """
    logger.info('validating trajectory computation')
    scenario = get_test_nuplan_scenario()
    step = 0
    iteration = SimulationIteration(time_point=scenario.get_time_point(0), index=0)
    history = SimulationHistoryBuffer.initialize_from_list(1, [scenario.get_ego_state_at_iteration(step)], [scenario.get_tracked_objects_at_iteration(step)], scenario.database_interval)
    planner_input = PlannerInput(iteration, history)
    container_name = container_name_from_image_name(submission)
    container_manager = SubmissionContainerManager(SubmissionContainerFactory())
    planner = RemotePlanner(container_manager, submission, container_name)
    planner_initialization = PlannerInitialization(scenario.get_mission_goal(), scenario.get_route_roadblock_ids(), scenario.map_api)
    planner.initialize([planner_initialization])
    trajectory = planner.compute_trajectory([planner_input])
    if trajectory:
        logger.debug(f'Computed trajectory {trajectory}')
        return True
    logger.error('Submission failed to compute trajectory')
    self._failing_validator = SubmissionComputesTrajectoryValidator
    return False

