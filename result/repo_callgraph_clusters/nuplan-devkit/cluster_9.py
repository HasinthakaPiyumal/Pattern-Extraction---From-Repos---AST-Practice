# Cluster 9

def _ensure_file_downloaded(data_root: str, potentially_remote_path: str) -> str:
    """
    Attempts to download the DB file from a remote URL if it does not exist locally.
    If the download fails, an error will be raised.
    :param data_root: The location to download the file, if necessary.
    :param potentially_remote_path: The path to the file.
    :return: The resulting file path. Will be one of a few options:
        * If potentially_remote_path points to a local file, will return potentially_remote_path
        * If potentially_remote_file points to a remote file, it does not exist currently, and the file can be successfully downloaded, it will return the path of the downloaded file.
        * In all other cases, an error will be raised.
    """
    output_file_path: str = download_file_if_necessary(data_root, potentially_remote_path)
    if not os.path.exists(output_file_path):
        raise ValueError(f'{potentially_remote_path} could not be downloaded.')
    return output_file_path

class Track(Base):
    """
    Track from tracker output. A track represents a bunch of lidar boxes with the same instance id in a given log.
    """
    __tablename__ = 'track'
    token: str = Column(sql_types.HexLen8, primary_key=True)
    category_token: str = Column(sql_types.HexLen8, ForeignKey('category.token'), nullable=False)
    width: float = Column(Float)
    length: float = Column(Float)
    height: float = Column(Float)
    lidar_boxes: List[LidarBox] = relationship('LidarBox', foreign_keys=[LidarBox.track_token], back_populates='track')
    scenario_tags: List[ScenarioTag] = relationship('ScenarioTag', foreign_keys=[ScenarioTag.agent_track_token], back_populates='agent_track')
    category: Category = relationship('Category', foreign_keys=[category_token], back_populates='tracks')

    @property
    def _session(self) -> Any:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return inspect(self).session

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        desc: str = simple_repr(self)
        return desc

    @property
    def nbr_lidar_boxes(self) -> int:
        """
        Returns number of boxes in the Track.
        :return: Number of boxes.
        """
        nbr: int = self._session.query(LidarBox).filter(LidarBox.track_token == self.token).count()
        return nbr

    @property
    def first_lidar_box(self) -> LidarBox:
        """
        Returns first lidar box along the track.
        :return: First lidar box along the track.
        """
        box: LidarBox = self._session.query(LidarBox).filter(LidarBox.track_token == self.token).join(LidarPc).order_by(LidarPc.timestamp.asc()).first()
        return box

    @property
    def last_lidar_box(self) -> LidarBox:
        """
        Returns last lidar box along the track.
        :return: Last lidar box along the track.
        """
        box: LidarBox = self._session.query(LidarBox).filter(LidarBox.track_token == self.token).join(LidarPc).order_by(LidarPc.timestamp.desc()).first()
        return box

    @property
    def duration(self) -> int:
        """
        Returns duration of Track.
        :return: Duration of the track.
        """
        d: int = self.last_lidar_box.timestamp - self.first_lidar_box.timestamp
        return d

    @property
    def distances_to_ego(self) -> npt.NDArray[np.float64]:
        """
        Returns array containing distances of all boxes in the Track from ego vehicle.
        :return: Distances of all boxes in the track from ego vehicle.
        """
        return np.asarray([lidar_box.distance_to_ego for lidar_box in self.lidar_boxes])

    @property
    def min_distance_to_ego(self) -> float:
        """
        Returns minimum distance of Track from Ego Vehicle.
        :return: The minimum distance of the track from ego vehicle.
        """
        min_dist: float = np.amin(self.distances_to_ego)
        return min_dist

    @property
    def max_distance_to_ego(self) -> float:
        """
        Returns maximum distance of Track from Ego Vehicle.
        :return: The maximum distance of the tack from ego vehicle.
        """
        max_dist: float = np.amax(self.distances_to_ego)
        return max_dist

@property
def max_distance_to_ego(self) -> float:
    """
        Returns maximum distance of Track from Ego Vehicle.
        :return: The maximum distance of the tack from ego vehicle.
        """
    max_dist: float = np.amax(self.distances_to_ego)
    return max_dist

class TestLidarPc(unittest.TestCase):
    """Tests the LidarBox class"""

    def setUp(self) -> None:
        """Sets up for the tests cases"""
        self.lidar_pc = get_test_nuplan_lidarpc()
        self.lidar_pc_with_blob = get_test_nuplan_lidarpc_with_blob()

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the _session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.lidar_pc._session
        inspect_mock.assert_called_once_with(self.lidar_pc)
        self.assertEqual(result, session_mock)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the __repr__ method"""
        result = self.lidar_pc.__repr__()
        simple_repr_mock.assert_called_once_with(self.lidar_pc)
        self.assertEqual(result, simple_repr_mock.return_value)

    def test_log(self) -> None:
        """Tests the log property"""
        result = self.lidar_pc.log
        self.assertIsInstance(result, Log)

    def test_future_ego_pose_has_next(self) -> None:
        """Tests the future_ego_pose method when there is a future ego pose"""
        result = self.lidar_pc.future_ego_pose()
        self.assertEqual(result, self.lidar_pc.next.ego_pose)

    def test_future_ego_pose_no_next(self) -> None:
        """Tests the future_ego_pose method when there is no future ego pose"""
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.next = None
        result = lidar_pc.future_ego_pose()
        self.assertEqual(result, None)

    def test_past_ego_pose_has_prev(self) -> None:
        """Tests the past_ego_pose method when there is a past ego pose"""
        result = self.lidar_pc.past_ego_pose()
        self.assertEqual(result, self.lidar_pc.prev.ego_pose)

    def test_past_ego_pose_no_prev(self) -> None:
        """Tests the past_ego_pose method when there is no past ego pose"""
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.prev = None
        result = lidar_pc.past_ego_pose()
        self.assertEqual(result, None)

    def test_future_or_past_ego_poses_prev_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'prev')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'prev')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'prev')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_next_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'next')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'next')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'next')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_unknown_direction(self) -> None:
        """Tests the future_or_past_ego_poses when direction is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'unknown_direction')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.LidarPointCloud.from_buffer', autospec=True)
    def test_load_channel_is_merged_point_cloud(self, from_buffer_mock: Mock) -> None:
        """Tests the load method when lidar channel is MergedPointCloud"""
        db = get_test_nuplan_db()
        result = self.lidar_pc.load(db)
        self.assertEqual(result, from_buffer_mock.return_value)

    def test_load_channel_is_not_implemented(self) -> None:
        """Tests the load method when lidar channel is not implemented"""
        db = get_test_nuplan_db()
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.lidar.channel = 'UnknownPointCloud'
        with self.assertRaises(NotImplementedError):
            lidar_pc.load(db)

    def test_load_bytes(self) -> None:
        """Tests the load bytes method"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.load_bytes(db)
        self.assertIsNotNone(result)

    def test_path(self) -> None:
        """Tests the path property"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.path(db)
        self.assertIsInstance(result, str)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.get_boxes', autospec=True)
    def test_boxes(self, get_boxes_mock: Mock) -> None:
        """Tests the boxes method"""
        result = self.lidar_pc.boxes()
        self.assertEqual(result, get_boxes_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.pack_future_boxes', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.lidar_pc.get_future_box_sequence', autospec=True)
    def test_boxes_with_future_waypoints(self, get_future_box_sequence_mock: Mock, pack_future_boxes_mock: Mock) -> None:
        """Tests the boxes_with_future_waypoints method"""
        future_horizon_len_s, future_interval_s = (1.0, 1.0)
        result = self.lidar_pc.boxes_with_future_waypoints(future_horizon_len_s, future_interval_s)
        get_future_box_sequence_mock.assert_called_once()
        pack_future_boxes_mock.assert_called_once_with(get_future_box_sequence_mock.return_value, future_interval_s, future_horizon_len_s)
        self.assertEqual(result, pack_future_boxes_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.render_on_map', autospec=True)
    def test_render(self, render_on_map_mock: Mock) -> None:
        """Tests the render method"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.render(db)
        render_on_map_mock.assert_called_once()
        self.assertIsInstance(result, Axes)

    def test_past_ego_poses(self) -> None:
        """Test if past ego poses are returned correctly."""
        n_ego_poses = 4
        lidar_pc = self.lidar_pc.next.next.next
        past_ego_poses = lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
        ego_pose = lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be greater than past EgoPoses.')

    def test_future_ego_poses(self) -> None:
        """Test if future ego poses are returned correctly."""
        n_ego_poses = 4
        future_ego_poses = self.lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
        ego_pose = self.lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be less that future EgoPoses.')

def test_future_or_past_ego_poses_prev_nposes(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev, mode=n_poses"""
    number, mode, direction = (1, 'n_poses', 'prev')
    result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_prev_nseconds(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev, mode=n_seconds"""
    number, mode, direction = (1, 'n_seconds', 'prev')
    result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_prev_unknown_mode(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev and mode is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'prev')
    with self.assertRaises(ValueError):
        self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

def test_future_or_past_ego_poses_next_nposes(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next, mode=n_poses"""
    number, mode, direction = (1, 'n_poses', 'next')
    result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_next_nseconds(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next, mode=n_seconds"""
    number, mode, direction = (1, 'n_seconds', 'next')
    result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_next_unknown_mode(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next and mode is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'next')
    with self.assertRaises(ValueError):
        self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

def test_future_or_past_ego_poses_unknown_direction(self) -> None:
    """Tests the future_or_past_ego_poses when direction is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'unknown_direction')
    with self.assertRaises(ValueError):
        self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

def test_past_ego_poses(self) -> None:
    """Test if past ego poses are returned correctly."""
    n_ego_poses = 4
    lidar_pc = self.lidar_pc.next.next.next
    past_ego_poses = lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
    ego_pose = lidar_pc.ego_pose
    for i in range(n_ego_poses):
        self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be greater than past EgoPoses.')

def test_future_ego_poses(self) -> None:
    """Test if future ego poses are returned correctly."""
    n_ego_poses = 4
    future_ego_poses = self.lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
    ego_pose = self.lidar_pc.ego_pose
    for i in range(n_ego_poses):
        self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be less that future EgoPoses.')

class TestLidarBox(unittest.TestCase):
    """Tests the LidarBox class"""

    def setUp(self) -> None:
        """Sets up for the test cases"""
        self.lidar_box_vehicle = get_test_nuplan_lidar_box_vehicle()
        self.lidar_box = get_test_nuplan_lidar_box()

    @patch('nuplan.database.nuplan_db_orm.lidar_box.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the _session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.lidar_box._session()
        inspect_mock.assert_called_once_with(self.lidar_box)
        self.assertEqual(result, session_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_box.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the __repr__ method"""
        result = self.lidar_box.__repr__()
        simple_repr_mock.assert_called_once_with(self.lidar_box)
        self.assertEqual(result, simple_repr_mock.return_value)

    def test_log(self) -> None:
        """Tests the log property"""
        result = self.lidar_box.log
        self.assertIsInstance(result, Log)

    def test_category(self) -> None:
        """Tests the category property"""
        result = self.lidar_box.category
        self.assertIsInstance(result, Category)

    def test_timestamp(self) -> None:
        """Tests the timestamp property"""
        result = self.lidar_box.timestamp
        self.assertIsInstance(result, int)

    def test_distance_to_ego(self) -> None:
        """Tests the distance_to_ego property"""
        x = self.lidar_box.x
        y = self.lidar_box.y
        x_ego = self.lidar_box.lidar_pc.ego_pose.x
        y_ego = self.lidar_box.lidar_pc.ego_pose.y
        expected_result = math.sqrt((x - x_ego) * (x - x_ego) + (y - y_ego) * (y - y_ego))
        actual_result = self.lidar_box.distance_to_ego
        self.assertEqual(expected_result, actual_result)

    def test_size(self) -> None:
        """Tests the size property"""
        result = self.lidar_box.size
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], self.lidar_box.width)
        self.assertEqual(result[1], self.lidar_box.length)
        self.assertEqual(result[2], self.lidar_box.height)

    def test_translation(self) -> None:
        """Tests the translation property"""
        result = self.lidar_box.translation
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], self.lidar_box.x)
        self.assertEqual(result[1], self.lidar_box.y)
        self.assertEqual(result[2], self.lidar_box.z)

    @patch('nuplan.database.nuplan_db_orm.lidar_box.Quaternion', autospec=True)
    def test_rotation(self, quaternion_mock: Mock) -> None:
        """Tests the rotation property"""
        result = self.lidar_box.rotation
        self.assertIsInstance(result, list)
        quaternion_mock.assert_called()

    @patch('nuplan.database.nuplan_db_orm.lidar_box.Quaternion', autospec=True)
    def test_quaternion(self, quaternion_mock: Mock) -> None:
        """Tests the quaternion property"""
        result = self.lidar_box.quaternion
        self.assertEqual(result, quaternion_mock.return_value)
        quaternion_mock.assert_called()

    @patch('nuplan.database.nuplan_db_orm.lidar_box.np.array', autospec=True)
    def test_translation_np(self, np_array_mock: Mock) -> None:
        """Tests the translation_np property"""
        result = self.lidar_box.translation_np
        np_array_mock.assert_called_once_with(self.lidar_box.translation)
        self.assertEqual(result, np_array_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_box.np.array', autospec=True)
    def test_size_np(self, np_array_mock: Mock) -> None:
        """Tests the size_np property"""
        result = self.lidar_box.size_np
        np_array_mock.assert_called_once_with(self.lidar_box.size)
        self.assertEqual(result, np_array_mock.return_value)

    def test_get_box_items(self) -> None:
        """Tests the _get_box_items method"""
        result = self.lidar_box._get_box_items()
        self.assertEqual(len(result), 2)

    def test_find_box_out_of_bounds(self) -> None:
        """Tests the _find_box method index is out of bounds"""
        result = self.lidar_box._find_box(maxsize)
        self.assertEqual(result, None)

    def test_find_box_within_bounds(self) -> None:
        """Tests the _find_box method index is within bounds"""
        result = self.lidar_box._find_box(0)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'prev')
        result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'prev')
        result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'prev')
        with self.assertRaises(ValueError):
            self.lidar_box.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_next_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'next')
        result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'next')
        result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'next')
        with self.assertRaises(ValueError):
            self.lidar_box.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_unknown_direction(self) -> None:
        """Tests the future_or_past_ego_poses when direction is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'unknown_direction')
        with self.assertRaises(ValueError):
            self.lidar_box.future_or_past_ego_poses(number, mode, direction)

    def test_temporal_neighbours_prev_exists(self) -> None:
        """Tests the _temporal_neighbours method when prev exists"""
        result = self.lidar_box._temporal_neighbors()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], self.lidar_box.prev)

    def test_temporal_neighbours_prev_is_empty(self) -> None:
        """Tests the _temporal_neighbours method when prev does not exist"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.prev = None
        result = lidar_box._temporal_neighbors()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], lidar_box)

    def test_temporal_neighbours_next_exists(self) -> None:
        """Tests the _temporal_neighbours method when next exists"""
        result = self.lidar_box._temporal_neighbors()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1], self.lidar_box.next)

    def test_temporal_neighbours_next_is_empty(self) -> None:
        """Tests the _temporal_neighbours method when next does not exist"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.next = None
        result = lidar_box._temporal_neighbors()
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1], lidar_box)

    def test_velocity_no_next_and_prev(self) -> None:
        """Tests the velocity property when next and prev does not exist"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.next = None
        lidar_box.prev = None
        result = lidar_box.velocity
        self.assertTrue(np.isnan(result).any())

    def test_velocity_time_diff_exceed_limit(self) -> None:
        """Tests the velocity property when the difference between timestamps exceed limit"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.next.lidar_pc.timestamp = lidar_box.prev.lidar_pc.timestamp + 1000000000
        result = lidar_box.velocity
        self.assertTrue(np.isnan(result).any())

    def test_velocity_default(self) -> None:
        """Tests the default velocity property, should not return any NaN values"""
        result = self.lidar_box.velocity
        self.assertFalse(np.isnan(result).any())

    def test_angular_velocity_no_next_and_prev(self) -> None:
        """Tests the angular_velocity property when next and prev does not exist"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.next = None
        lidar_box.prev = None
        result = lidar_box.angular_velocity
        self.assertTrue(np.isnan(result))

    def test_angular_velocity_time_diff_exceed_limit(self) -> None:
        """Tests the angular_velocity property when the difference between timestamps exceed limit"""
        lidar_box = deepcopy(self.lidar_box)
        lidar_box.next.lidar_pc.timestamp = lidar_box.prev.lidar_pc.timestamp + 1000000000
        result = lidar_box.angular_velocity
        self.assertTrue(np.isnan(result))

    def test_angular_velocity_default(self) -> None:
        """Tests the default angular_velocity property, should not return any NaN values"""
        result = self.lidar_box.angular_velocity
        self.assertFalse(np.isnan(result))

    def test_box(self) -> None:
        """Tests the box method"""
        result = self.lidar_box.box()
        self.assertIsInstance(result, Box3D)

    @patch('nuplan.database.nuplan_db_orm.lidar_box.PredictedTrajectory', autospec=True)
    def test_tracked_object_is_agent(self, predicted_trajectory_mock: Mock) -> None:
        """Tests the tracked_object method"""
        future_waypoints = Mock()
        predicted_trajectory_mock.return_value.probability = 1.0
        result = self.lidar_box_vehicle.tracked_object(future_waypoints)
        predicted_trajectory_mock.assert_called_once_with(1.0, future_waypoints)
        self.assertIsInstance(result, Agent)

    def test_tracked_object_is_static_object(self) -> None:
        """Tests the tracked_object method"""
        future_waypoints = Mock()
        result = self.lidar_box.tracked_object(future_waypoints)
        self.assertIsInstance(result, StaticObject)

    def test_velocity(self) -> None:
        """Test if velocity is calculated correctly."""
        self.assertTrue(self.lidar_box.prev is not None)
        self.assertTrue(self.lidar_box.next is not None)
        prev_lidar_box: LidarBox = self.lidar_box.prev
        next_lidar_box: LidarBox = self.lidar_box.next
        time_diff = 1e-06 * (next_lidar_box.timestamp - prev_lidar_box.timestamp)
        pos_diff = self.lidar_box.velocity * time_diff
        pos_next = next_lidar_box.translation_np
        pos_next_pred = prev_lidar_box.translation_np + pos_diff
        np.testing.assert_array_almost_equal(pos_next[:2], pos_next_pred[:2], decimal=4)

    def test_angular_velocity(self) -> None:
        """Test if angular velocity is calculated correctly."""
        self.assertTrue(self.lidar_box.prev is not None)
        self.assertTrue(self.lidar_box.next is not None)
        prev_lidar_box: LidarBox = self.lidar_box.prev
        next_lidar_box: LidarBox = self.lidar_box.next
        time_diff = 1e-06 * (next_lidar_box.timestamp - prev_lidar_box.timestamp)
        yaw_diff = self.lidar_box.angular_velocity * time_diff
        yaw_prev = quaternion_yaw(prev_lidar_box.quaternion)
        q_yaw_prev = Quaternion(np.array([np.cos(yaw_prev / 2), 0, 0, np.sin(yaw_prev / 2)]))
        q_yaw_next_pred = Quaternion(np.array([np.cos(yaw_diff / 2), 0, 0, np.sin(yaw_diff / 2)])) * q_yaw_prev
        yaw_next_pred = quaternion_yaw(q_yaw_next_pred)
        yaw_next = quaternion_yaw(next_lidar_box.quaternion)
        self.assertAlmostEqual(yaw_next, yaw_next_pred, delta=0.0001)

    def test_next(self) -> None:
        """Test next."""
        self.assertGreater(self.lidar_box.next.timestamp, self.lidar_box.timestamp, 'Timestamp of succeeding box must be greater then current box.')

    def test_prev(self) -> None:
        """Test prev."""
        self.assertLess(self.lidar_box.prev.timestamp, self.lidar_box.timestamp, 'Timestamp of preceding box must be lower then current box.')

    def test_past_ego_poses(self) -> None:
        """Test if past ego poses are returned correctly."""
        n_ego_poses = 4
        past_ego_poses = self.lidar_box.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
        ego_pose = self.lidar_box.lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamp of current EgoPose must be greater than past EgoPoses')

    def test_future_ego_poses(self) -> None:
        """Test if future ego poses are returned correctly."""
        n_ego_poses = 4
        future_ego_poses = self.lidar_box.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
        ego_pose = self.lidar_box.lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamp of current EgoPose must be less than future EgoPoses ')

    def test_get_box_items_to_iterate(self) -> None:
        """Tests the get_box_items_to_iterate method"""
        result = self.lidar_box.get_box_items_to_iterate()
        self.assertTrue(self.lidar_box.timestamp in result)
        self.assertEqual(self.lidar_box.prev, result[self.lidar_box.timestamp][0])
        self.assertEqual(self.lidar_box.next, result[self.lidar_box.timestamp][1])

    @patch('nuplan.database.nuplan_db_orm.lidar_box.IterableLidarBox', autospec=True)
    def test_iter(self, iterable_lidar_box_mock: Mock) -> None:
        """Tests the iterator for LidarBox"""
        result = iter(self.lidar_box)
        iterable_lidar_box_mock.assert_called_once_with(self.lidar_box)
        self.assertEqual(result, iterable_lidar_box_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_box.IterableLidarBox', autospec=True)
    def test_reverse_iter(self, iterable_lidar_box_mock: Mock) -> None:
        """Tests the reverse iterator for LidarBox"""
        result = reversed(self.lidar_box)
        iterable_lidar_box_mock.assert_called_once_with(self.lidar_box, reverse=True)
        self.assertEqual(result, iterable_lidar_box_mock.return_value)

def test_find_box_out_of_bounds(self) -> None:
    """Tests the _find_box method index is out of bounds"""
    result = self.lidar_box._find_box(maxsize)
    self.assertEqual(result, None)

def test_find_box_within_bounds(self) -> None:
    """Tests the _find_box method index is within bounds"""
    result = self.lidar_box._find_box(0)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_prev_nposes(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev, mode=n_poses"""
    number, mode, direction = (1, 'n_poses', 'prev')
    result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_prev_nseconds(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev, mode=n_seconds"""
    number, mode, direction = (1, 'n_seconds', 'prev')
    result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_prev_unknown_mode(self) -> None:
    """Tests the future_or_past_ego_poses when direction=prev and mode is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'prev')
    with self.assertRaises(ValueError):
        self.lidar_box.future_or_past_ego_poses(number, mode, direction)

def test_future_or_past_ego_poses_next_nposes(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next, mode=n_poses"""
    number, mode, direction = (1, 'n_poses', 'next')
    result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_next_nseconds(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next, mode=n_seconds"""
    number, mode, direction = (1, 'n_seconds', 'next')
    result = self.lidar_box.future_or_past_ego_poses(number, mode, direction)
    self.assertIsNotNone(result)

def test_future_or_past_ego_poses_next_unknown_mode(self) -> None:
    """Tests the future_or_past_ego_poses when direction=next and mode is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'next')
    with self.assertRaises(ValueError):
        self.lidar_box.future_or_past_ego_poses(number, mode, direction)

def test_future_or_past_ego_poses_unknown_direction(self) -> None:
    """Tests the future_or_past_ego_poses when direction is unknown"""
    number, mode, direction = (1, 'unknown_mode', 'unknown_direction')
    with self.assertRaises(ValueError):
        self.lidar_box.future_or_past_ego_poses(number, mode, direction)

def test_velocity_no_next_and_prev(self) -> None:
    """Tests the velocity property when next and prev does not exist"""
    lidar_box = deepcopy(self.lidar_box)
    lidar_box.next = None
    lidar_box.prev = None
    result = lidar_box.velocity
    self.assertTrue(np.isnan(result).any())

def test_velocity_time_diff_exceed_limit(self) -> None:
    """Tests the velocity property when the difference between timestamps exceed limit"""
    lidar_box = deepcopy(self.lidar_box)
    lidar_box.next.lidar_pc.timestamp = lidar_box.prev.lidar_pc.timestamp + 1000000000
    result = lidar_box.velocity
    self.assertTrue(np.isnan(result).any())

def test_velocity_default(self) -> None:
    """Tests the default velocity property, should not return any NaN values"""
    result = self.lidar_box.velocity
    self.assertFalse(np.isnan(result).any())

def test_angular_velocity_no_next_and_prev(self) -> None:
    """Tests the angular_velocity property when next and prev does not exist"""
    lidar_box = deepcopy(self.lidar_box)
    lidar_box.next = None
    lidar_box.prev = None
    result = lidar_box.angular_velocity
    self.assertTrue(np.isnan(result))

def test_angular_velocity_time_diff_exceed_limit(self) -> None:
    """Tests the angular_velocity property when the difference between timestamps exceed limit"""
    lidar_box = deepcopy(self.lidar_box)
    lidar_box.next.lidar_pc.timestamp = lidar_box.prev.lidar_pc.timestamp + 1000000000
    result = lidar_box.angular_velocity
    self.assertTrue(np.isnan(result))

def test_angular_velocity_default(self) -> None:
    """Tests the default angular_velocity property, should not return any NaN values"""
    result = self.lidar_box.angular_velocity
    self.assertFalse(np.isnan(result))

def test_next(self) -> None:
    """Test next."""
    self.assertGreater(self.lidar_box.next.timestamp, self.lidar_box.timestamp, 'Timestamp of succeeding box must be greater then current box.')

def test_prev(self) -> None:
    """Test prev."""
    self.assertLess(self.lidar_box.prev.timestamp, self.lidar_box.timestamp, 'Timestamp of preceding box must be lower then current box.')

def test_past_ego_poses(self) -> None:
    """Test if past ego poses are returned correctly."""
    n_ego_poses = 4
    past_ego_poses = self.lidar_box.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
    ego_pose = self.lidar_box.lidar_pc.ego_pose
    for i in range(n_ego_poses):
        self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamp of current EgoPose must be greater than past EgoPoses')

def test_future_ego_poses(self) -> None:
    """Test if future ego poses are returned correctly."""
    n_ego_poses = 4
    future_ego_poses = self.lidar_box.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
    ego_pose = self.lidar_box.lidar_pc.ego_pose
    for i in range(n_ego_poses):
        self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamp of current EgoPose must be less than future EgoPoses ')

def test_get_box_items_to_iterate(self) -> None:
    """Tests the get_box_items_to_iterate method"""
    result = self.lidar_box.get_box_items_to_iterate()
    self.assertTrue(self.lidar_box.timestamp in result)
    self.assertEqual(self.lidar_box.prev, result[self.lidar_box.timestamp][0])
    self.assertEqual(self.lidar_box.next, result[self.lidar_box.timestamp][1])

class TestPointCloudPreparation(unittest.TestCase):
    """Test preparation of point cloud method (standalone method)."""

    def setUp(self) -> None:
        """Setup funciton for class."""
        self.db = get_test_nuplan_db()
        self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

    def test_prepare_pointcloud_points(self) -> None:
        """
        Tests if the lidar point clouds are properly filtered when loaded and decorations are correctly applied.
        """
        pc_none = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=False, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_intensity = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=False, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_ring = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=True, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_lidar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=False, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_all = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_single_lidar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0,), sample_apillar_lidar_rings=True)
        pc_all_0 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 1, 2, 3, 4), sample_apillar_lidar_rings=True)
        pc_all_1 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=True)
        pc_all_no_sample_apillar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
        pc_sample_apillar_0 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 3, 4), sample_apillar_lidar_rings=True)
        pc_sample_apillar_1 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 3, 4), sample_apillar_lidar_rings=False)
        pt_cloud = self.lidar_pc.load(self.db)
        self.assertEqual(pc_none.points.shape[0], 3)
        self.assertEqual(pc_intensity.points.shape[0], 4)
        self.assertEqual(pc_ring.points.shape[0], 4)
        self.assertEqual(pc_lidar.points.shape[0], 4)
        self.assertEqual(pc_all.points.shape[0], 6)
        self.assertTrue(pt_cloud.nbr_points() > pc_single_lidar.nbr_points())
        self.assertTrue((pc_all_0.points == pc_all_1.points).all())
        self.assertTrue((pc_single_lidar.points[5] == 0).all())
        self.assertTrue(np.isin(pc_all_0.points[5], [0, 1, 2, 3, 4]).all())
        self.assertTrue(np.array_equal(pc_sample_apillar_0.points, pc_sample_apillar_1.points))
        self.assertTrue(pc_all_no_sample_apillar.points[:, np.logical_or(pc_all_no_sample_apillar.points[5] == 1, pc_all_no_sample_apillar.points[5] == 2)].shape[1] > pc_all_0.points[:, np.logical_or(pc_all_0.points[5] == 1, pc_all_0.points[5] == 2)].shape[1])

def test_prepare_pointcloud_points(self) -> None:
    """
        Tests if the lidar point clouds are properly filtered when loaded and decorations are correctly applied.
        """
    pc_none = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=False, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_intensity = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=False, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_ring = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=True, use_lidar_index=False, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_lidar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=False, use_ring=False, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_all = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_single_lidar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0,), sample_apillar_lidar_rings=True)
    pc_all_0 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 1, 2, 3, 4), sample_apillar_lidar_rings=True)
    pc_all_1 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=True)
    pc_all_no_sample_apillar = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=None, sample_apillar_lidar_rings=False)
    pc_sample_apillar_0 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 3, 4), sample_apillar_lidar_rings=True)
    pc_sample_apillar_1 = prepare_pointcloud_points(self.lidar_pc.load(self.db), use_intensity=True, use_ring=True, use_lidar_index=True, lidar_indices=(0, 3, 4), sample_apillar_lidar_rings=False)
    pt_cloud = self.lidar_pc.load(self.db)
    self.assertEqual(pc_none.points.shape[0], 3)
    self.assertEqual(pc_intensity.points.shape[0], 4)
    self.assertEqual(pc_ring.points.shape[0], 4)
    self.assertEqual(pc_lidar.points.shape[0], 4)
    self.assertEqual(pc_all.points.shape[0], 6)
    self.assertTrue(pt_cloud.nbr_points() > pc_single_lidar.nbr_points())
    self.assertTrue((pc_all_0.points == pc_all_1.points).all())
    self.assertTrue((pc_single_lidar.points[5] == 0).all())
    self.assertTrue(np.isin(pc_all_0.points[5], [0, 1, 2, 3, 4]).all())
    self.assertTrue(np.array_equal(pc_sample_apillar_0.points, pc_sample_apillar_1.points))
    self.assertTrue(pc_all_no_sample_apillar.points[:, np.logical_or(pc_all_no_sample_apillar.points[5] == 1, pc_all_no_sample_apillar.points[5] == 2)].shape[1] > pc_all_0.points[:, np.logical_or(pc_all_0.points[5] == 1, pc_all_0.points[5] == 2)].shape[1])

class TestNuPlanDBLidarMethods(unittest.TestCase):
    """Tests for NuPlanDBLidarMethods (Helper methods for interacting with NuPlanDB's lidar samples)."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.db = get_test_nuplan_db()
        self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

    def test_get_past_future_sweep(self) -> None:
        """
        Go N sweeps back and N sweeps forth and see if we are back at the original.
        """
        for sweep_idx in range(-10, 10):
            sweep_lidarpc_rec = _get_past_future_sweep(self.lidar_pc, sweep_idx)
            if sweep_lidarpc_rec is None:
                continue
            return_lidarpc_rec = _get_past_future_sweep(sweep_lidarpc_rec, -sweep_idx)
            self.assertEqual(self.lidar_pc, return_lidarpc_rec)

    def test_load_pointcloud_from_pc(self) -> None:
        """
        Test loading of point cloud from LidarPc based on distance, data shape, map filtering and timestmap.
        """
        min_dist = 0.9
        max_dist = 50.0
        pc = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
        pc_intensity = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
        pc_ring = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=True, use_lidar_index=False)
        pc_lidar_index = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=True)
        pc_multiple_sweeps = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=3, max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
        pc_multiple_sweeps_new_format = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=list(range(-3 + 1, 0 + 1)), max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
        pc_map_filtered_random = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
        pc_past_future = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=[-2, 0, 1], max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
        pc_dist_from_orig = np.linalg.norm(pc.points[:2, :], axis=0)
        pc_multiple_sweeps_dist_from_orig = np.linalg.norm(pc_multiple_sweeps.points[:2, :], axis=0)
        self.assertEqual(pc.points.shape[0], 4)
        self.assertEqual(pc_map_filtered_random.points.shape[0], 4)
        self.assertEqual(pc_intensity.points.shape[0], 5)
        self.assertEqual(pc_ring.points.shape[0], 5)
        self.assertEqual(pc_lidar_index.points.shape[0], 5)
        self.assertEqual(pc_multiple_sweeps.points.shape[0], 5)
        self.assertTrue((pc_dist_from_orig >= min_dist).all() and (pc_dist_from_orig <= max_dist).all())
        self.assertTrue((pc_multiple_sweeps_dist_from_orig <= max_dist).all())
        self.assertTrue(pc_multiple_sweeps.points.shape[1] >= pc.points.shape[1])
        self.assertTrue(pc_map_filtered_random.points.shape[1] <= pc.points.shape[1])
        timestamps = np.unique(pc_past_future.points[3, :])
        past_timestamp = (self.lidar_pc.timestamp - self.lidar_pc.prev.prev.timestamp) / 1000000.0
        future_timestamp = (self.lidar_pc.timestamp - self.lidar_pc.next.timestamp) / 1000000.0
        self.assertAlmostEqual(past_timestamp, timestamps[2])
        self.assertAlmostEqual(0, timestamps[1])
        self.assertAlmostEqual(future_timestamp, timestamps[0])
        self.assertTrue(len(timestamps) == 3)
        self.assertTrue(np.all(pc_multiple_sweeps.points == pc_multiple_sweeps_new_format.points))

def test_load_pointcloud_from_pc(self) -> None:
    """
        Test loading of point cloud from LidarPc based on distance, data shape, map filtering and timestmap.
        """
    min_dist = 0.9
    max_dist = 50.0
    pc = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
    pc_intensity = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
    pc_ring = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=True, use_lidar_index=False)
    pc_lidar_index = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=True)
    pc_multiple_sweeps = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=3, max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
    pc_multiple_sweeps_new_format = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=list(range(-3 + 1, 0 + 1)), max_distance=max_dist, min_distance=min_dist, use_intensity=True, use_ring=False, use_lidar_index=False)
    pc_map_filtered_random = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=1, max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
    pc_past_future = load_pointcloud_from_pc(nuplandb=self.db, token=self.lidar_pc.token, nsweeps=[-2, 0, 1], max_distance=max_dist, min_distance=min_dist, use_intensity=False, use_ring=False, use_lidar_index=False)
    pc_dist_from_orig = np.linalg.norm(pc.points[:2, :], axis=0)
    pc_multiple_sweeps_dist_from_orig = np.linalg.norm(pc_multiple_sweeps.points[:2, :], axis=0)
    self.assertEqual(pc.points.shape[0], 4)
    self.assertEqual(pc_map_filtered_random.points.shape[0], 4)
    self.assertEqual(pc_intensity.points.shape[0], 5)
    self.assertEqual(pc_ring.points.shape[0], 5)
    self.assertEqual(pc_lidar_index.points.shape[0], 5)
    self.assertEqual(pc_multiple_sweeps.points.shape[0], 5)
    self.assertTrue((pc_dist_from_orig >= min_dist).all() and (pc_dist_from_orig <= max_dist).all())
    self.assertTrue((pc_multiple_sweeps_dist_from_orig <= max_dist).all())
    self.assertTrue(pc_multiple_sweeps.points.shape[1] >= pc.points.shape[1])
    self.assertTrue(pc_map_filtered_random.points.shape[1] <= pc.points.shape[1])
    timestamps = np.unique(pc_past_future.points[3, :])
    past_timestamp = (self.lidar_pc.timestamp - self.lidar_pc.prev.prev.timestamp) / 1000000.0
    future_timestamp = (self.lidar_pc.timestamp - self.lidar_pc.next.timestamp) / 1000000.0
    self.assertAlmostEqual(past_timestamp, timestamps[2])
    self.assertAlmostEqual(0, timestamps[1])
    self.assertAlmostEqual(future_timestamp, timestamps[0])
    self.assertTrue(len(timestamps) == 3)
    self.assertTrue(np.all(pc_multiple_sweeps.points == pc_multiple_sweeps_new_format.points))

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

def test_nbr_lidar_boxes(self) -> None:
    """
        Tests property - number of boxes along the track.
        """
    result = self.track.nbr_lidar_boxes
    self.assertGreater(result, 0)
    self.assertIsInstance(result, int)

class TestVectorMapNp(unittest.TestCase):
    """
    Tests the VectorMapNp class
    """

    def setUp(self) -> None:
        """
        Sets up for the test cases
        """
        coords: npt.NDArray[np.float64] = np.ones([1, 2, 2], dtype=np.float32)
        multi_scale_connections = Dict[int, npt.NDArray[np.float64]]
        self.vector_map_np = VectorMapNp(coords, multi_scale_connections)

    def test_translate(self) -> None:
        """
        Tests the translate method
        """
        vector_map_np = self.vector_map_np
        translate = [1.0, 1.0, 0.0]
        expected_coords = 2.0 * np.ones([1, 2, 2], dtype=np.float32)
        result = vector_map_np.translate(translate)
        self.assertTrue(np.array_equal(result.coords, expected_coords))

    @patch('nuplan.database.nuplan_db_orm.vector_map_np.np.dot', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.vector_map_np.np.concatenate', autospec=True)
    def test_rotate(self, concatenate_mock: Mock, dot_mock: Mock) -> None:
        """
        Tests the rotate method
        """
        vector_map_np = self.vector_map_np
        quarternion = Mock()
        vector_map_np.rotate(quarternion)
        dot_mock.assert_called_once()
        concatenate_mock.assert_called_once()

    def test_scale(self) -> None:
        """
        Tests the scale method
        """
        vector_map_np = self.vector_map_np
        scale = [3.0, 3.0, 3.0]
        expected_coords = 3.0 * np.ones([1, 2, 2], dtype=np.float32)
        result = vector_map_np.scale(scale)
        self.assertTrue(np.array_equal(result.coords, expected_coords))

    def test_xflip(self) -> None:
        """
        Tests the xflip method
        """
        vector_map_np = self.vector_map_np
        expected_coords: npt.NDArray[np.float64] = np.array([[[-1, 1], [-1, 1]]])
        result = vector_map_np.xflip()
        self.assertTrue(np.array_equal(result.coords, expected_coords))

    def test_yflip(self) -> None:
        """
        Tests the yflip method
        """
        vector_map_np = self.vector_map_np
        expected_coords: npt.NDArray[np.float64] = np.array([[[1, -1], [1, -1]]])
        result = vector_map_np.yflip()
        self.assertTrue(np.array_equal(result.coords, expected_coords))

def test_translate(self) -> None:
    """
        Tests the translate method
        """
    vector_map_np = self.vector_map_np
    translate = [1.0, 1.0, 0.0]
    expected_coords = 2.0 * np.ones([1, 2, 2], dtype=np.float32)
    result = vector_map_np.translate(translate)
    self.assertTrue(np.array_equal(result.coords, expected_coords))

def test_scale(self) -> None:
    """
        Tests the scale method
        """
    vector_map_np = self.vector_map_np
    scale = [3.0, 3.0, 3.0]
    expected_coords = 3.0 * np.ones([1, 2, 2], dtype=np.float32)
    result = vector_map_np.scale(scale)
    self.assertTrue(np.array_equal(result.coords, expected_coords))

def test_xflip(self) -> None:
    """
        Tests the xflip method
        """
    vector_map_np = self.vector_map_np
    expected_coords: npt.NDArray[np.float64] = np.array([[[-1, 1], [-1, 1]]])
    result = vector_map_np.xflip()
    self.assertTrue(np.array_equal(result.coords, expected_coords))

def test_yflip(self) -> None:
    """
        Tests the yflip method
        """
    vector_map_np = self.vector_map_np
    expected_coords: npt.NDArray[np.float64] = np.array([[[1, -1], [1, -1]]])
    result = vector_map_np.yflip()
    self.assertTrue(np.array_equal(result.coords, expected_coords))

class TestImage(unittest.TestCase):
    """Test class Image"""

    def setUp(self) -> None:
        """
        Initializes a test Image
        """
        self.db = get_test_nuplan_db()
        self.image = get_test_nuplan_image()

    @patch('nuplan.database.nuplan_db_orm.image.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.image._session()
        inspect.assert_called_once_with(self.image)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.image.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.image.__repr__()
        simple_repr.assert_called_once_with(self.image)
        self.assertEqual(result, simple_repr.return_value)

    def test_log(self) -> None:
        """
        Tests property log
        """
        log = self.image.log
        self.assertEqual(log, self.image.camera.log)

    @patch('nuplan.database.nuplan_db_orm.image.func')
    @patch('nuplan.database.nuplan_db_orm.image.Image._session')
    def test_lidar_pc(self, mock_session: Mock, mock_func: Mock) -> None:
        """
        Tests property lidar_pc
        """
        mock_query = mock_session.query
        mock_lidar_pc = mock_query.return_value
        mock_lidar_pc_ordered = mock_lidar_pc.order_by.return_value
        mock_first = mock_lidar_pc_ordered.first.return_value
        result = self.image.lidar_pc
        mock_query.assert_called_once_with(LidarPc)
        self.assertTrue(mock_func.abs.call_args[0][0].compare(LidarPc.timestamp - self.image.timestamp))
        mock_lidar_pc.order_by.assert_called_once_with(mock_func.abs.return_value)
        mock_lidar_pc_ordered.first.assert_called_once()
        self.assertEqual(result, mock_first)

    @patch('nuplan.database.nuplan_db_orm.image.Image.lidar_pc')
    def test_lidar_boxes(self, mock_lidar_pc: Mock) -> None:
        """
        Tests property lidar_boxes
        """
        result = self.image.lidar_boxes
        self.assertEqual(result, mock_lidar_pc.lidar_boxes)

    @patch('nuplan.database.nuplan_db_orm.image.Image.lidar_pc')
    def test_scene(self, mock_lidar_pc: Mock) -> None:
        """
        Tests property scene
        """
        result = self.image.scene
        self.assertEqual(result, mock_lidar_pc.scene)

    @patch('nuplan.database.nuplan_db_orm.image.PIL.Image.open')
    @patch('nuplan.database.nuplan_db_orm.image.Image.load_bytes_jpg')
    def test_load_as_pil(self, mock_load_bytes: Mock, mock_pil_open: Mock) -> None:
        """
        Tests load_as with PIL image type
        """
        mock_db = Mock()
        img = self.image.load_as(mock_db, 'pil')
        mock_load_bytes.assert_called_once_with(mock_db)
        mock_pil_open.assert_called_once_with(mock_load_bytes.return_value)
        self.assertEqual(img, mock_pil_open.return_value)

    @patch('nuplan.database.nuplan_db_orm.image.np.array')
    @patch('nuplan.database.nuplan_db_orm.image.PIL.Image.open')
    @patch('nuplan.database.nuplan_db_orm.image.Image.load_bytes_jpg')
    def test_load_as_np(self, mock_load_bytes: Mock, mock_pil_open: Mock, mock_np_array: Mock) -> None:
        """
        Tests load_as with numpy array image type
        """
        mock_db = Mock()
        img = self.image.load_as(mock_db, 'np')
        mock_load_bytes.assert_called_once_with(mock_db)
        mock_pil_open.assert_called_once_with(mock_load_bytes.return_value)
        mock_np_array.assert_called_once_with(mock_pil_open.return_value)
        self.assertEqual(img, mock_np_array.return_value)

    @patch('nuplan.database.nuplan_db_orm.image.cv2.COLOR_RGB2BGR')
    @patch('nuplan.database.nuplan_db_orm.image.cv2.cvtColor')
    @patch('nuplan.database.nuplan_db_orm.image.np.array')
    @patch('nuplan.database.nuplan_db_orm.image.PIL.Image.open')
    @patch('nuplan.database.nuplan_db_orm.image.Image.load_bytes_jpg')
    def test_load_as_cv2(self, mock_load_bytes: Mock, mock_pil_open: Mock, mock_np_array: Mock, mock_cvtColor: Mock, mock_rgb2bgr: Mock) -> None:
        """
        Tests load_as with cv2 image type
        """
        mock_db = Mock()
        img = self.image.load_as(mock_db, 'cv2')
        mock_load_bytes.assert_called_once_with(mock_db)
        mock_pil_open.assert_called_once_with(mock_load_bytes.return_value)
        mock_np_array.assert_called_once_with(mock_pil_open.return_value)
        mock_cvtColor.assert_called_once_with(mock_np_array.return_value, mock_rgb2bgr)
        self.assertEqual(img, mock_cvtColor.return_value)

    def test_load_as_invalid(self) -> None:
        """
        Tests load_as with invalid image type
        """
        mock_db = Mock()
        with self.assertRaises(AssertionError):
            self.image.load_as(mock_db, 'invalid')

    def test_filename(self) -> None:
        """
        Tests property filename
        """
        filename = self.image.filename
        self.assertEqual(filename, self.image.filename_jpg)

    @patch('nuplan.database.nuplan_db_orm.image.osp.join')
    @patch('nuplan.database.nuplan_db_orm.image.Image.filename')
    def test_load_bytes_jpg(self, mock_filename: Mock, mock_osp_join: Mock) -> None:
        """
        Tests method to load bytes of the jpg data db.load_blob(osp.join("sensor_blobs", self.filename))
        """
        mock_load_blob = Mock()
        mock_db = Mock(load_blob=mock_load_blob)
        result = self.image.load_bytes_jpg(mock_db)
        mock_osp_join.assert_called_once_with('sensor_blobs', mock_filename)
        mock_load_blob.assert_called_once_with(mock_osp_join.return_value)
        self.assertEqual(result, mock_load_blob.return_value)

    @patch('nuplan.database.nuplan_db_orm.image.osp.join')
    def test_path(self, mock_osp_join: Mock) -> None:
        """
        Tests image path based on DB data root
        """
        mock_db = Mock(data_root='data_root')
        path = self.image.path(mock_db)
        mock_osp_join.assert_called_once_with('data_root', self.image.filename)
        self.assertEqual(path, mock_osp_join.return_value)

    @patch('nuplan.database.nuplan_db_orm.image.get_boxes')
    @patch('nuplan.database.nuplan_db_orm.image.Image.camera')
    @patch('nuplan.database.nuplan_db_orm.image.Image.ego_pose')
    def test_boxes(self, mock_egopose: Mock, mock_camera: Mock, mock_get_boxes: Mock) -> None:
        """
        Test loading of boxes associated with this Image
        """
        boxes = self.image.boxes('Frame')
        mock_get_boxes.assert_called_once_with(self.image, 'Frame', mock_egopose.trans_matrix_inv, mock_camera.trans_matrix_inv)
        self.assertEqual(boxes, mock_get_boxes.return_value)

    def test_future_ego_poses(self) -> None:
        """
        Test method to get n future poses
        """
        n_ego_poses = 4
        future_ego_poses = self.image.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
        ego_pose = self.image.ego_pose
        for i in range(n_ego_poses):
            self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be less that future EgoPoses.')

    def test_past_ego_poses(self) -> None:
        """
        Test method to get n past poses
        """
        n_ego_poses = 4
        past_ego_poses = self.image.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
        ego_pose = self.image.ego_pose
        for i in range(n_ego_poses):
            self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be greater than past EgoPoses ')

    def test_invalid_ego_poses(self) -> None:
        """
        Test method to get poses, with invalid inputs
        """
        with self.assertRaises(ValueError):
            self.image.future_or_past_ego_poses(number=1, mode='n_poses', direction='invalid')
        with self.assertRaises(NotImplementedError):
            self.image.future_or_past_ego_poses(number=1, mode='invalid', direction='prev')

    @patch('nuplan.database.nuplan_db_orm.image.Image.boxes')
    @patch('nuplan.database.nuplan_db_orm.image.box_in_image')
    @patch('nuplan.database.nuplan_db_orm.image.Image.load_as', autospec=True)
    def test_render(self, mock_load: Mock, mock_box_in_image: Mock, mock_boxes: Mock) -> None:
        """
        Test render method
        """
        mock_ax = Mock(spec=Axes)
        mock_box = Mock(spec=Box3D, token='token')
        mock_box.render = Mock()
        mock_boxes.return_value = [mock_box]
        mock_db = MagicMock()
        mock_db.lidar_box = MagicMock()
        mock_box_in_image.return_value = True
        self.image.render(mock_db, with_3d_anns=True, box_vis_level='box_vis_level', ax=mock_ax)
        mock_boxes.assert_called_once()
        self.assertEqual(mock_box_in_image.call_args.args[0], mock_box)
        np.testing.assert_array_equal(mock_box_in_image.call_args.args[1], self.image.camera.intrinsic_np)
        np.testing.assert_array_equal(mock_box_in_image.call_args.args[2], (self.image.camera.width, self.image.camera.height))
        self.assertEqual(mock_box_in_image.call_args.kwargs, {'vis_level': 'box_vis_level'})
        mock_box.render.assert_called_once()

def test_future_ego_poses(self) -> None:
    """
        Test method to get n future poses
        """
    n_ego_poses = 4
    future_ego_poses = self.image.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
    ego_pose = self.image.ego_pose
    for i in range(n_ego_poses):
        self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be less that future EgoPoses.')

def test_past_ego_poses(self) -> None:
    """
        Test method to get n past poses
        """
    n_ego_poses = 4
    past_ego_poses = self.image.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
    ego_pose = self.image.ego_pose
    for i in range(n_ego_poses):
        self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be greater than past EgoPoses ')

def test_invalid_ego_poses(self) -> None:
    """
        Test method to get poses, with invalid inputs
        """
    with self.assertRaises(ValueError):
        self.image.future_or_past_ego_poses(number=1, mode='n_poses', direction='invalid')
    with self.assertRaises(NotImplementedError):
        self.image.future_or_past_ego_poses(number=1, mode='invalid', direction='prev')

def weighted_harmonic_mean(x: List[float], w: List[float]) -> float:
    """
    Calculate the weighted harmonic mean of x with weights given by w.
    :param x: [<float> * n]. Input data.
    :param w: [<float> * n]. Weights. Needs to be same shape.
    :return: The weighted harmonic mean.
    """
    w = list(map(float, w))
    if any([xi == 0 for xi in x]):
        return 0
    if any([wi <= 0 for wi in w]):
        raise ValueError('w must contain strictly positive entries')
    return float(np.sum(w) / np.sum([wi / xi for xi, wi in zip(x, w)]))

class IterableLidarBox:
    """Helper class to make LidarBox object iterable via for loop."""

    def __init__(self, box: LidarBox, reverse: bool=False) -> None:
        """
        Constructs the iterable object.

        :param box: LidarBox to iterate over.
        :param reverse: if true, this iterator will iterate to past
        """
        self._begin = box
        self._current = box
        self._reverse = reverse
        self._items_dict = box.get_box_items_to_iterate()

    @property
    def box(self) -> LidarBox:
        """
        :return: the current lidar box
        """
        return self._current

    @property
    def reverse(self) -> int:
        """
        :return: whether this class is iterating into past.
        """
        return self._reverse

    def __iter__(self) -> IterableLidarBox:
        """
        Returns the iterable object itself.
        """
        return self

    def __next__(self) -> LidarBox:
        """
        Returns the next LidarBox object.
        """
        box = self._current
        if box:
            index = 1 if not self._reverse else 0
            self._current = self._items_dict[box.timestamp][index]
            return box
        raise StopIteration

    def __getitem__(self, item: int) -> LidarBox:
        """
        Returns the LidarBox object at the given index.
        """
        box = self._begin
        for _ in range(item):
            if box:
                box = self._items_dict[box.timestamp][1]
        return box

def __init__(self, box: LidarBox, reverse: bool=False) -> None:
    """
        Constructs the iterable object.

        :param box: LidarBox to iterate over.
        :param reverse: if true, this iterator will iterate to past
        """
    self._begin = box
    self._current = box
    self._reverse = reverse
    self._items_dict = box.get_box_items_to_iterate()

class Box3D(BoxInterface):
    """Simple data class representing a 3d box including, label, score and velocity."""
    MAX_LABELS = 100
    _labelmap = None
    _min_size = np.finfo(np.float32).eps
    RENDER_MODE_PROB_THRESHOLD = 0.1

    def __init__(self, center: Tuple[float, float, float], size: Tuple[float, float, float], orientation: Quaternion, label: int=np.nan, score: float=np.nan, velocity: Tuple[float, float, float]=(np.nan, np.nan, np.nan), angular_velocity: float=np.nan, payload: Optional[Dict[str, Any]]=None, token: Optional[str]=None, track_token: Optional[str]=None, future_horizon_len_s: Optional[float]=None, future_interval_s: Optional[float]=None, future_centers: Optional[List[List[Tuple[float, float, float]]]]=None, future_orientations: Optional[List[List[Quaternion]]]=None, mode_probs: Optional[List[float]]=None) -> None:
        """
        The convention is that: x points forward, y to the left, z up when this box is initialized with an orientation
        of zero.
        :param center: Center of box given as x, y, z.
        :param size: Size of box in width, length, height.
        :param orientation: Box3D orientation.
        :param label: Integer label, optional.
        :param score: Classification score, optional.
        :param velocity: Box3D velocity in x, y, z direction.
        :param angular_velocity: Box3D angular velocity in yaw direction.
        :param payload: Box3D payload, optional. For example, can be used to denote category name or provide boolean
            data regarding whether the box trajectory goes off the driveable area. The format should be a dictionary
            so that different types of metadata can be stored here, e.g., payload['category_name'] and
            payload['timestamp_2_on_road_bool'].
        :param token: Unique token (optional). Usually DB annotation token. In NuPlanDB, 3D annotations are present in
            the LidarBox table, in which case the token provided corresponds to the LidarBox token.
        :param track_token: Track token in the "track" table that corresponds to a particular box.
        :param future_horizon_len_s: Timestamp horizon of the future waypoints in seconds.
        :param future_interval_s: Timestamp interval of the future waypoints in seconds.
        :param future_centers: List of future center coordinates given as (x, y, z), where the list indices increase
            with time and are spaced apart at the specified intervals. If the box is missing at a future timestamp, then
            the future center coordinates at the corresponding list index will have the format (np.nan, np.nan, np.nan)
        :param future_orientations: List of future Box3D orientations, where the list indices increase with time and
            are spaced apart at the specified intervals. If the box is missing at a future timestamp, then
            the future orientation at the corresponding list index will be represented as None.
        :param mode_probs: Mode probabilities.
        """
        assert not np.any(np.isnan(center))
        assert not np.any(np.isnan(size))
        assert len(center) == 3
        assert len(size) == 3
        assert len(velocity) == 3
        assert type(orientation) == Quaternion
        assert size[0] > self._min_size, 'Error: box Width must be larger than {} cm'.format(100 * self._min_size)
        assert size[1] > self._min_size, 'Error: box Length must be larger than {} cm'.format(100 * self._min_size)
        assert size[2] > self._min_size, 'Error: box Height must be larger than {} cm'.format(100 * self._min_size)
        assert size[0] * size[1] * size[2] > self._min_size, 'Invalid box volume'
        self.center = np.array(center, dtype=float)
        self.size = size
        self.wlh = np.array(size, dtype=float)
        self.orientation = orientation.__copy__()
        self._label = int(label) if not np.isnan(label) else label
        self._score = float(score) if not np.isnan(score) else score
        self.velocity = np.array(velocity, dtype=float)
        self.angular_velocity = float(angular_velocity) if not np.isnan(angular_velocity) else angular_velocity
        self.payload = payload if payload is not None else {}
        assert type(self.payload) == dict, 'Error: box payload is not a dict'
        self.token = token
        self._color = None
        self.track_token = track_token
        self.init_trajectory_fields(future_horizon_len_s, future_interval_s, future_centers, future_orientations, mode_probs)

    @classmethod
    def set_labelmap(cls, labelmap: Dict[int, Label]) -> None:
        """
        :param labelmap: {id: label}. Map from label id to Label.
        """
        cls._labelmap = labelmap

    @property
    def color(self) -> Color:
        """RGBA color of Box3D."""
        if self._color is None:
            self._set_color()
        return self._color

    @property
    def width(self) -> float:
        """Width of the box."""
        return float(self.wlh[0])

    @width.setter
    def width(self, width: float) -> None:
        """Implemented. See interface."""
        self.wlh[0] = width

    @property
    def length(self) -> float:
        """Length of the box."""
        return float(self.wlh[1])

    @length.setter
    def length(self, length: float) -> None:
        """Implemented. See interface."""
        self.wlh[1] = length

    @property
    def height(self) -> float:
        """Height of the box."""
        return float(self.wlh[2])

    @height.setter
    def height(self, height: float) -> None:
        """Implemented. See interface."""
        self.wlh[2] = height

    @property
    def yaw(self) -> float:
        """Yaw of the box."""
        return quaternion_yaw(self.orientation)

    @property
    def distance_plane(self) -> float:
        """
        The euclidean distance of the box center from the z-axis passing through the origin of the coordinate system
        (sensor/world). Refer to the axial/radial distance in a cylindrical coordinate system:
        https://en.wikipedia.org/wiki/Cylindrical_coordinate_system.
        """
        return float((self.center[0] ** 2 + self.center[1] ** 2) ** 0.5)

    @property
    def distance_3d(self) -> float:
        """
        The euclidean distance of the box center from the origin of the coordinate system (sensor/world). Refer to the
        radial distance in a spherical coordinate system: https://en.wikipedia.org/wiki/Spherical_coordinate_system.
        """
        return float((self.center[0] ** 2 + self.center[1] ** 2 + self.center[2] ** 2) ** 0.5)

    def init_trajectory_fields(self, future_horizon_len_s: Optional[float]=None, future_interval_s: Optional[float]=None, future_centers: Optional[List[List[Tuple[float, float, float]]]]=None, future_orientations: Optional[List[List[Quaternion]]]=None, mode_probs: Optional[List[float]]=None) -> None:
        """
        Checks that values for future horizon length, interval length, future orientations and future centers are either
        all provided or all None. Check that future centers and future orientations are the expected length, if
        applicable.
        :param future_horizon_len_s: Timestamp horizon of the future waypoints in seconds.
        :param future_interval_s: Timestamp interval of the future waypoints in seconds.
        :param future_centers: List of future center coordinates given as (x, y, z), where the list indices increase
            with time and are spaced apart at the specified intervals. If the box is missing at a future timestamp, then
            the future center coordinates at the corresponding list index will have the format (np.nan, np.nan, np.nan)
        :param future_orientations: List of future Box3D orientations, where the list indices increase with time and
            are spaced apart at the specified intervals. If the box is missing at a future timestamp, then
            the future orientation at the corresponding list index will be represented as None.
        :param mode_probs: Mode probabilities.
        """
        if future_centers is None:
            assert future_horizon_len_s is None
            assert future_interval_s is None
            assert future_orientations is None
            assert mode_probs is None
            self.future_horizon_len_s = None
            self.future_interval_s = None
            self.future_centers = None
            self.future_orientations = None
            self.mode_probs = None
            self.num_modes = None
            self.num_future_timesteps = None
            return
        assert future_horizon_len_s is not None
        assert future_interval_s is not None
        assert future_orientations is not None
        assert mode_probs is not None
        self.future_horizon_len_s = future_horizon_len_s
        self.future_interval_s = future_interval_s
        self.future_centers = np.array(future_centers, dtype=float)
        self.future_orientations = future_orientations
        self.mode_probs = np.array(mode_probs, dtype=float)
        assert self.future_centers.ndim == 3
        if not self.mode_probs.shape[0] == self.future_centers.shape[0] == len(self.future_orientations):
            raise ValueError(f'Future parameters have different number of modes:\nself.mode_probs.shape: {self.mode_probs.shape}\nself.future_centers.shape: {self.future_centers.shape}\nlen(self.future_orientations): {len(self.future_orientations)}')
        self.num_modes = self.mode_probs.shape[0]
        if self.future_centers.shape[1] != len(self.future_orientations[0]):
            raise ValueError(f'Future parameters have different number of timesteps:\nself.future_centers.shape: {self.future_centers.shape}\nlen(self.future_orientations[0]): {len(self.future_orientations[0])}')
        self.num_future_timesteps = self.future_centers.shape[1]
        if self.future_horizon_len_s != self.future_interval_s * self.num_future_timesteps:
            raise ValueError(f'Future horizon length ({self.future_horizon_len_s}) should equal to future interval ({self.future_interval_s}) times number of timesteps ({self.num_future_timesteps}).')

    def _set_color(self) -> None:
        """Sets color based on label."""
        if self._labelmap is None or self.label not in self._labelmap:
            if self.label is None or np.isnan(self.label):
                self._color = (255, 61, 99, 0)
            else:
                fixed_colors = [(255, 61, 99, 0), (255, 158, 0, 0), (0, 0, 230, 0)]
                colors = [el + (255,) for el in rainbow(self.MAX_LABELS - 3)]
                random.Random(1).shuffle(colors)
                colors = fixed_colors + colors
                self._color = colors[self.label % self.MAX_LABELS]
        else:
            self._color = self._labelmap[self.label].color

    @property
    def name(self) -> str:
        """Name of Box3D."""
        if self._labelmap is None or self.label is np.nan:
            return 'not_set'
        elif self.label not in self._labelmap:
            return 'unknown'
        else:
            return self._labelmap[self.label].name

    @property
    def label(self) -> int:
        """Implemented. See interface."""
        return self._label

    @label.setter
    def label(self, label: int) -> None:
        """Implemented. See interface."""
        self._label = label

    @property
    def score(self) -> float:
        """Implemented. See interface."""
        return self._score

    @score.setter
    def score(self, score: float) -> None:
        """Implemented. See interface."""
        self._score = score

    @property
    def has_future_waypoints(self) -> bool:
        """Whether this box has future waypoints."""
        return self.future_centers is not None

    def equate_orientations(self, other: object) -> bool:
        """
        Compare orientations of two Box3D Objects.
        :param other: The other Box3D object.
        :return: True if orientations of both objects are the same, otherwise False.
        """
        if (self.future_orientations is None) != (other.future_orientations is None):
            return False
        if self.future_orientations is not None and other.future_orientations is not None:
            for mode_idx in range(self.num_modes):
                for horizon_idx in range(self.num_future_timesteps):
                    self_future_orientation = self.future_orientations[mode_idx][horizon_idx]
                    other_future_orientation = other.future_orientations[mode_idx][horizon_idx]
                    if (self_future_orientation is None) != (other_future_orientation is None):
                        return False
                    if self_future_orientation is not None and other_future_orientation is not None:
                        if not np.allclose(self.future_orientations[mode_idx][horizon_idx].rotation_matrix, other.future_orientations[mode_idx][horizon_idx].rotation_matrix, atol=0.0001):
                            return False
        return True

    def __eq__(self, other: object) -> bool:
        """
        Compares the two Box3D object are the same.
        :param other: The other Box3D object.
        :return: True if both objects are the same, otherwise False.
        """
        if not isinstance(other, Box3D):
            return NotImplemented
        center = np.allclose(self.center, other.center, atol=0.0001)
        wlh = np.allclose(self.wlh, other.wlh, atol=0.0001)
        orientation = np.allclose(self.orientation.rotation_matrix, other.orientation.rotation_matrix, atol=0.0001)
        label = self.label == other.label or (np.isnan(self.label) and np.isnan(other.label))
        score = self.score == other.score or (np.isnan(self.score) and np.isnan(other.score))
        vel = np.allclose(self.velocity, other.velocity, atol=0.0001) or (np.all(np.isnan(self.velocity)) and np.all(np.isnan(other.velocity)))
        angular_vel = np.isclose(self.angular_velocity, other.angular_velocity, atol=0.0001) or (np.isnan(self.angular_velocity) and np.isnan(other.angular_velocity))
        payload = self.payload == other.payload
        if not (center and wlh and orientation and label and score and vel and angular_vel and payload):
            return False
        if self.future_horizon_len_s != other.future_horizon_len_s:
            return False
        if self.future_interval_s != other.future_interval_s:
            return False
        if self.num_future_timesteps != other.num_future_timesteps:
            return False
        if self.num_modes != other.num_modes:
            return False
        if (self.future_centers is None) != (other.future_centers is None):
            return False
        if self.future_centers is not None and other.future_centers is not None:
            if not np.array_equal(np.isnan(self.future_centers), np.isnan(other.future_centers)):
                return False
            if not np.allclose(self.future_centers[~np.isnan(self.future_centers)], other.future_centers[~np.isnan(other.future_centers)], atol=0.0001):
                return False
        if not self.equate_orientations(other):
            return False
        if (self.mode_probs is None) != (other.mode_probs is None):
            return False
        if self.mode_probs is not None and other.mode_probs is not None:
            if not np.allclose(self.mode_probs, other.mode_probs, atol=0.0001):
                return False
        return True

    def __repr__(self) -> str:
        """
        Represent a box using a string.
        :return: A string to represent a box.
        """
        arguments = 'center={}, size={}, orientation={}'.format(tuple(self.center), tuple(self.wlh), self.orientation.__repr__())
        if not np.isnan(self.label):
            arguments += ', label={}'.format(self.label)
        if not np.isnan(self.score):
            arguments += ', score={}'.format(self.score)
        if not all(np.isnan(self.velocity)):
            arguments += ', velocity={}'.format(tuple(self.velocity))
        if not np.isnan(self.angular_velocity):
            arguments += ', angular_velocity={}'.format(self.angular_velocity)
        if self.payload is not None:
            arguments += ", payload='{}'".format(self.payload)
        if self.token is not None:
            arguments += ", token='{}'".format(self.token)
        if self.track_token is not None:
            arguments += ", track_token='{}'".format(self.track_token)
        if self.future_horizon_len_s is not None:
            arguments += ", future_horizon_len_s='{}'".format(self.future_horizon_len_s)
        if self.future_interval_s is not None:
            arguments += ", future_interval_s='{}'".format(self.future_interval_s)
        if self.future_centers is not None:
            arguments += ", future_centers='{}'".format(self.future_centers)
        if self.future_orientations is not None:
            arguments += ", future_orientations='{}'".format(self.future_orientations)
        if self.mode_probs is not None:
            arguments += ", mode_probs='{}'".format(self.mode_probs)
        return 'Box3D({})'.format(arguments)

    def serialize(self) -> Dict[str, Any]:
        """
        Implemented. See interface.
        :return: Dict of field name to field values.
        """
        future_orientations_serialized = [[orientation.elements.tolist() if orientation is not None else None for orientation in future_orientations_of_mode] for future_orientations_of_mode in self.future_orientations] if self.future_orientations is not None else None
        return {'center': self.center.tolist(), 'wlh': self.wlh.tolist(), 'orientation': self.orientation.elements.tolist(), 'label': self.label, 'score': self.score, 'velocity': self.velocity.tolist(), 'angular_velocity': self.angular_velocity, 'payload': self.payload, 'token': self.token, 'track_token': self.track_token, 'future_horizon_len_s': self.future_horizon_len_s, 'future_interval_s': self.future_interval_s, 'future_centers': self.future_centers.tolist() if self.future_centers is not None else None, 'future_orientations': future_orientations_serialized, 'mode_probs': self.mode_probs.tolist() if self.mode_probs is not None else None}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Box3D:
        """
        Implemented. See interface.
        :param data: Output from serialize.
        :return: Deserialized Box3D.
        """
        if type(data) is dict:
            future_orientations = [[Quaternion(orientation) if orientation is not None else None for orientation in orientations_of_mode] for orientations_of_mode in data['future_orientations']] if data['future_orientations'] is not None else None
            return Box3D(data['center'], data['wlh'], Quaternion(data['orientation']), label=data['label'], score=data['score'], velocity=data['velocity'], angular_velocity=data['angular_velocity'], payload=data['payload'], token=data['token'], track_token=data['track_token'], future_horizon_len_s=data['future_horizon_len_s'], future_interval_s=data['future_interval_s'], future_centers=data['future_centers'], future_orientations=future_orientations, mode_probs=data['mode_probs'])
        else:
            raise TypeError('Type of data should be a dictionary.')

    @classmethod
    def arbitrary_box(cls) -> Box3D:
        """Instantiates an arbitrary box."""
        return Box3D(center=(1.1, 2.2, 3.3), size=(2.2, 5.5, 3.1), orientation=Quaternion(1, 2, 3, 4), label=1, score=0.5, velocity=(1.1, 2.3, 3.3), angular_velocity=0.314, payload={'def': 'hij'}, token='abc', track_token='wxy')

    @classmethod
    def make_random(cls) -> Box3D:
        """
        Instantiates a random box.
        :return: Box3D instance.
        """
        center = random.sample(range(50), 3)
        size = random.sample(range(1, 50), 3)
        quaternion = Quaternion(random.sample(range(10), 4))
        label = random.choice(range(cls.MAX_LABELS))
        score = random.uniform(0, 1)
        velocity = tuple((random.uniform(0, 10) for _ in range(3)))
        angular_velocity = np.random.uniform(-np.pi, np.pi)
        return Box3D(center=center, size=size, orientation=quaternion, label=label, score=score, velocity=velocity, angular_velocity=angular_velocity)

    def copy(self) -> Box3D:
        """
        Create a copy of self.
        :return: Box3D instance.
        """
        return Box3D(center=self.center, size=self.wlh, orientation=self.orientation, label=self.label, score=self.score, velocity=self.velocity, angular_velocity=self.angular_velocity, payload=self.payload, token=self.token, track_token=self.track_token, future_horizon_len_s=self.future_horizon_len_s, future_interval_s=self.future_interval_s, future_centers=self.future_centers, future_orientations=self.future_orientations, mode_probs=self.mode_probs)

    @property
    def rotation_matrix(self) -> npt.NDArray[np.float64]:
        """
        Returns a rotation matrix.
        :return: <np.float: (3, 3)>.
        """
        return self.orientation.rotation_matrix

    def translate(self, x: npt.NDArray[np.float64]) -> None:
        """
        Applies a translation.
        :param x: <np.float: 3>. Translation in x, y, z direction.
        """
        self.center += x
        if self.future_centers is not None:
            assert x.ndim == 1
            assert x.shape[-1] == self.future_centers.shape[-1]
            self.future_centers += x

    def rotate(self, quaternion: Quaternion) -> None:
        """
        Rotates a box.
        :param quaternion: Rotation to apply.
        """
        self.orientation = quaternion * self.orientation
        rotation_matrix = quaternion.rotation_matrix
        self.center = np.dot(rotation_matrix, self.center)
        self.velocity = np.dot(rotation_matrix, self.velocity)
        if self.future_centers is not None:
            for mode_idx in range(self.num_modes):
                for horizon_idx in range(self.num_future_timesteps):
                    self.future_centers[mode_idx][horizon_idx] = np.dot(rotation_matrix, self.future_centers[mode_idx][horizon_idx])
        if self.future_orientations is not None:
            for mode_idx in range(self.num_modes):
                for horizon_idx in range(self.num_future_timesteps):
                    if self.future_orientations[mode_idx][horizon_idx] is None:
                        continue
                    self.future_orientations[mode_idx][horizon_idx] = quaternion * self.future_orientations[mode_idx][horizon_idx]

    def transform(self, trans_matrix: npt.NDArray[np.float64]) -> None:
        """
        Applies a transformation matrix to the box
        :param trans_matrix: <np.float: 4, 4>. Homogeneous transformation matrix.
        """
        self.rotate(Quaternion(matrix=trans_matrix[:3, :3]))
        self.translate(trans_matrix[:3, 3])

    def scale(self, s: Tuple[float, float, float]) -> None:
        """
        Scales the box coordinate system.
        :param s: Scale parameter in x, y, z direction.
        """
        scale = np.asarray(s)
        assert len(scale) == 3
        self.center *= scale
        self.wlh *= scale
        self.velocity *= scale
        if self.future_centers is not None:
            assert scale.ndim == 1
            assert scale.shape[-1] == self.future_centers.shape[-1]
            self.future_centers *= scale

    def xflip(self) -> None:
        """Flip the box along the X-axis."""
        self.center[0] *= -1
        self.velocity[0] *= -1
        self.angular_velocity *= -1
        if self.future_centers is not None:
            self.future_centers[:, :, 0] *= -1
        current_yaw = quaternion_yaw(self.orientation)
        final_yaw = -current_yaw + np.pi
        self.orientation = Quaternion(axis=(0, 0, 1), angle=final_yaw)
        if self.future_orientations is not None:
            for mode_idx in range(self.num_modes):
                for horizon_idx in range(self.num_future_timesteps):
                    orientation = self.future_orientations[mode_idx][horizon_idx]
                    if orientation is None:
                        continue
                    current_yaw = quaternion_yaw(orientation)
                    final_yaw = -current_yaw + np.pi
                    self.future_orientations[mode_idx][horizon_idx] = Quaternion(axis=(0, 0, 1), angle=final_yaw)

    def yflip(self) -> None:
        """Flip the box along the Y-axis."""
        self.center[1] *= -1
        self.velocity[1] *= -1
        self.angular_velocity *= -1
        if self.future_centers is not None:
            self.future_centers[:, :, 1] *= -1
        current_yaw = quaternion_yaw(self.orientation)
        final_yaw = -current_yaw
        self.orientation = Quaternion(axis=(0, 0, 1), angle=final_yaw)
        if self.future_orientations is not None:
            for mode_idx in range(self.num_modes):
                for horizon_idx in range(self.num_future_timesteps):
                    orientation = self.future_orientations[mode_idx][horizon_idx]
                    if orientation is None:
                        continue
                    current_yaw = quaternion_yaw(orientation)
                    final_yaw = -current_yaw
                    self.future_orientations[mode_idx][horizon_idx] = Quaternion(axis=(0, 0, 1), angle=final_yaw)

    def corners(self, wlh_factor: float=1.0) -> npt.NDArray[np.float64]:
        """
        Returns the bounding box corners.
        :param wlh_factor: Multiply w, l, h by a factor to inflate or deflate the box.
        :return: <np.float: 3, 8>. First four corners are the ones facing forward.
            The last four are the ones facing backwards.
        """
        w: float = self.wlh[0] * wlh_factor
        l: float = self.wlh[1] * wlh_factor
        h: float = self.wlh[2] * wlh_factor
        center = tuple(self.center.flatten())
        rotation_matrix = tuple(self.rotation_matrix.flatten())
        return self._calc_corners(w, l, h, center, rotation_matrix)

    @property
    def front_corners(self) -> npt.NDArray[np.float64]:
        """
        Returns the four corners of the front face of the box. First two are on top face while the last two are on the
        bottom face.
        :return: <np.float: 3, 4>. Front corners.
        """
        return self.corners()[:, :4]

    @property
    def rear_corners(self) -> npt.NDArray[np.float64]:
        """
        Returns the four corners of the rear face of the box. First two are on top face while the last two are on the
        bottom face.
        :return: <np.float: 3, 4>. Rear corners.
        """
        return self.corners()[:, 4:]

    @property
    def bottom_corners(self) -> npt.NDArray[np.float64]:
        """
        Returns the four bottom corners.
        :return: <np.float: 3, 4>. Bottom corners. First two face forward, last two face backwards.
        """
        return self.corners()[:, [2, 3, 7, 6]]

    @property
    def center_bottom_forward(self) -> npt.NDArray[np.float64]:
        """
        Returns the coordinate of the following point: the center of the intersection of the bottom and forward faces
        of the box.
        :return: <np.float: 3, 1>.
        """
        return np.expand_dims(np.mean(self.corners().T[2:4], axis=0), 0).T

    @property
    def front_center(self) -> npt.NDArray[np.float64]:
        """
        Returns the coordinate of the center of the front face of the box.
        :return: <np.float: 3>.
        """
        return np.mean(self.front_corners, axis=1)

    @property
    def rear_center(self) -> npt.NDArray[np.float64]:
        """
        Returns the coordinate of the center of the rear face of the box.
        :return: <np.float: 3>.
        """
        return np.mean(self.rear_corners, axis=1)

    @property
    def bottom_center(self) -> npt.NDArray[np.float64]:
        """
        Returns the coordinate of the bottom face center.
        :return: <np.float: 3>.
        """
        return np.mean(self.bottom_corners, axis=1)

    @property
    def velocity_endpoint(self) -> npt.NDArray[np.float64]:
        """
        Extends the velocity vector from the front bottom center.
        :return: <np.float: 3, 1>.
        """
        return self.center_bottom_forward + np.expand_dims(self.velocity.T, axis=1)

    def get_future_horizon_idx(self, future_horizon_s: float) -> int:
        """
        Gets the index of a future horizon.
        :param future_horizon_s: Future horizon in seconds.
        :return: The index of the future horizon.
        """
        if self.future_horizon_len_s is None or self.future_interval_s is None:
            raise ValueError(f'Future horizon information is not available. Invalid variable values:\nfuture_horizon_len_s={self.future_horizon_len_s}\nfuture_interval_s={self.future_interval_s}.')
        if not 0.0 < future_horizon_s <= self.future_horizon_len_s:
            raise ValueError(f'Future horizon ({future_horizon_s}) should be in (0, {self.future_horizon_len_s}].')
        horizon_idx = round(future_horizon_s / self.future_interval_s - 1, 1)
        if not horizon_idx.is_integer():
            raise ValueError(f'Future horizon ({future_horizon_s}) divided by future interval ({self.future_interval_s}) is not an integer.')
        horizon_idx = int(horizon_idx)
        assert 0 <= horizon_idx < self.num_future_timesteps
        return horizon_idx

    def get_all_future_horizons_s(self) -> List[float]:
        """
        Gets the list of all future horizons.
        :return: The list of all future horizons.
        """
        return [round((horizon_idx + 1) * self.future_interval_s, 2) for horizon_idx in range(self.num_future_timesteps)]

    def get_future_center_at_horizon(self, future_horizon_s: float) -> npt.NDArray[np.float64]:
        """
        Gets future center of the highest probability trajectory at a given horizon.
        :param future_horizon_s: Future horizon in seconds.
        :return: Future center at the given horizon.
        """
        if self.future_centers is None:
            raise ValueError('Future center is not available.')
        highest_prob_mode_idx = self.get_highest_prob_mode_idx()
        horizon_idx = self.get_future_horizon_idx(future_horizon_s)
        return self.future_centers[highest_prob_mode_idx, horizon_idx]

    def get_future_centers_at_horizons(self, future_horizons_s: List[float]) -> npt.NDArray[np.float64]:
        """
        Gets future centers at the given horizons.
        :param future_horizons_s: Future horizons in seconds.
        :return: Future centers at the given horizons.
        """
        if self.future_centers is None:
            raise ValueError('Future center is not available.')
        highest_prob_mode_idx = self.get_highest_prob_mode_idx()
        horizon_indices = [self.get_future_horizon_idx(future_horizon_s) for future_horizon_s in future_horizons_s]
        return self.future_centers[highest_prob_mode_idx, horizon_indices]

    def get_future_orientation_at_horizon(self, future_horizon_s: float) -> Quaternion:
        """
        Gets future orientation of the highest probability trajectory at a given horizon.
        :param future_horizon_s: Future horizon in seconds.
        :return: Future orientation at the given horizon.
        """
        if self.future_orientations is None:
            raise ValueError('Future orientation is not available.')
        highest_prob_mode_idx = self.get_highest_prob_mode_idx()
        horizon_idx = self.get_future_horizon_idx(future_horizon_s)
        return self.future_orientations[highest_prob_mode_idx][horizon_idx]

    def get_future_orientations_at_horizons(self, future_horizons_s: List[float]) -> List[Quaternion]:
        """
        Gets future orientation of the highest probability trajectory at the given horizons.
        :param future_horizons_s: Future horizons in seconds.
        :return: Future orientations at the given horizons.
        """
        if self.future_orientations is None:
            raise ValueError('Future orientation is not available.')
        highest_prob_mode_idx = self.get_highest_prob_mode_idx()
        horizon_indices = [self.get_future_horizon_idx(future_horizon_s) for future_horizon_s in future_horizons_s]
        return [self.future_orientations[highest_prob_mode_idx][horizon_idx] for horizon_idx in horizon_indices]

    def get_topk_future_center_at_horizon(self, future_horizon_s: float, topk: int) -> npt.NDArray[np.float64]:
        """
        Gets top-k future centers at a given horizon.
        :param future_horizon_s: Future horizon in seconds.
        :param topk: The number of top-k modes.
        :return: Future center at the given horizon.
        """
        if self.future_centers is None:
            raise ValueError('Future centers are not available.')
        topk_mode_indices = self.get_topk_mode_indices(topk)
        horizon_idx = self.get_future_horizon_idx(future_horizon_s)
        return self.future_centers[topk_mode_indices, horizon_idx]

    def get_topk_future_orientation_at_horizon(self, future_horizon_s: float, topk: int) -> List[Quaternion]:
        """
        Gets top-k future orientations at a given horizon.
        :param future_horizon_s: Future horizon in seconds.
        :param topk: The number of top-k modes.
        :return: Future orientation at the given horizon.
        """
        if self.future_orientations is None:
            raise ValueError('Future orientations are not available.')
        topk_mode_indices = self.get_topk_mode_indices(topk)
        horizon_idx = self.get_future_horizon_idx(future_horizon_s)
        return [self.future_orientations[mode_idx][horizon_idx] for mode_idx in topk_mode_indices]

    def get_topk_mode_indices(self, topk: int) -> List[int]:
        """
        Gets the indices for the top-k highest probability modes.
        :param topk: Number of top-k modes.
        :return: The list of top-k highest probability mode indices.
        """
        if self.mode_probs is None:
            raise ValueError('Mode probabilities are not available.')
        return self.mode_probs.argsort()[::-1][:topk]

    def get_highest_prob_mode_idx(self) -> int:
        """
        Gets the index of the highest probability mode.
        :return: The index of the highest probability mode.
        """
        return self.get_topk_mode_indices(1)[0]

    def draw_line(self, canvas: Union[plt.Axes, npt.NDArray[np.uint8]], from_x: float, to_x: float, from_y: float, to_y: float, color: Tuple[Union[float, str], Union[float, str], Union[float, str]], linewidth: float, marker: Optional[str]=None, alpha: float=1.0) -> None:
        """
        Draws a line on a matplotlib/cv2 canvas.
        :param canvas: <matplotlib.pyplot.axis> OR <np.array: width, height, 3>.
        Axis/Image onto which the box should be drawn.
        :param from_x: The start x coordinates of vertices.
        :param to_x: The end x coordinates of vertices.
        :param from_y: The start y coordinates of vertices.
        :param to_y: The end y coordinates of vertices.
        :param color: The color used to draw line.
        :param linewidth: Width in pixel of the box sides.
        :param marker: Marker style string to draw line.
        :param alpha: The degree of transparency (or opacity) of a color.
        """
        if isinstance(canvas, np.ndarray):
            color_int = tuple((int(c * 255) for c in color))
            cv2.line(canvas, (int(from_x), int(from_y)), (int(to_x), int(to_y)), color_int[::-1], linewidth)
        else:
            canvas.plot([from_x, to_x], [from_y, to_y], color=color, linewidth=linewidth, marker=marker, alpha=alpha)

    def draw_rect(self, canvas: Union[plt.Axes, npt.NDArray[np.uint8]], selected_corners: npt.NDArray[np.float64], color: Tuple[float, float, float], linewidth: float) -> None:
        """
        Draws a rectangle on a matplotlib/cv2 canvas.
        :param canvas: <matplotlib.pyplot.axis> OR <np.array: width, height, 3>.
        Axis/Image onto which the box should be drawn.
        :param selected_corners: The selected corners for a rectangle.
        :param color: The color used to draw rectangle.
        :param linewidth: Width in pixel of the box sides.
        """
        prev = selected_corners[-1]
        for corner in selected_corners:
            self.draw_line(canvas, prev[0], corner[0], prev[1], corner[1], color=color, linewidth=linewidth)
            prev = corner

    def draw_text(self, canvas: Union[plt.Axes, npt.NDArray[np.uint8]], x: float, y: float, text: str) -> None:
        """
        Draws text on a matplotlib/cv2 canvas.
        :param canvas: <matplotlib.pyplot.axis> OR <np.array: width, height, 3>.
        Axis/Image onto which the box should be drawn.
        :param x: The x coordinates of vertices.
        :param y: The y coordinates of vertices.
        :param text: The text to draw.
        """
        if isinstance(canvas, np.ndarray):
            cv2.putText(canvas, text, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            canvas.text(x, y, text)

    def render(self, canvas: Union[plt.Axes, npt.NDArray[np.uint8]], view: npt.NDArray[np.float64]=np.eye(3), normalize: bool=False, colors: Tuple[MatplotlibColor, MatplotlibColor, MatplotlibColor]=None, linewidth: float=2, marker: str='o', with_direction: bool=True, with_velocity: bool=False, with_label: bool=False) -> None:
        """
        Renders the box. Canvas can be either a Matplotlib axis or a numpy array image (using cv2).
        :param canvas: <matplotlib.pyplot.axis> OR <np.array: width, height, 3>.
            Axis/Image onto which the box should be drawn.
        :param view: <np.array: 3, 3>. Define a projection in needed (e.g. for drawing projection in an image).
        :param normalize: Whether to normalize the remaining coordinate.
        :param colors: (<Matplotlib.colors>: 3). Valid Matplotlib colors (<str> or normalized RGB tuple) for front,
            rear/top and bottom.
        :param linewidth: Width in pixel of the box sides.
        :param marker: Marker style string to draw line.
        :param with_direction: Whether to draw a line indicating box direction.
        :param with_velocity: Whether to draw a line indicating box velocity.
        :param with_label: Whether to render the label.
        """
        corners = self.corners()
        sel = corners[2, :] < 0
        corners[2, sel] *= -1
        corners = view_points(corners, view, normalize=normalize)[:2, :]
        if colors is None:
            color = tuple((c / 255 for c in self.color[:3]))
            colors = (color, color, 'k')
        colors = tuple((matplotlib.colors.to_rgb(c) if isinstance(c, str) else c for c in colors))
        for i in [2, 3]:
            self.draw_line(canvas, corners.T[i][0], corners.T[i + 4][0], corners.T[i][1], corners.T[i + 4][1], color=colors[2], linewidth=linewidth)
        for i in [0, 1]:
            self.draw_line(canvas, corners.T[i][0], corners.T[i + 4][0], corners.T[i][1], corners.T[i + 4][1], color=colors[1], linewidth=linewidth)
        self.draw_rect(canvas, corners.T[:4], colors[0], linewidth)
        self.draw_rect(canvas, corners.T[4:], colors[1], linewidth)
        if with_direction:
            center_bottom = np.mean(corners.T[[2, 3, 7, 6]], axis=0)
            center_bottom_forward = np.mean(corners.T[2:4], axis=0)
            self.draw_line(canvas, center_bottom[0], center_bottom_forward[0], center_bottom[1], center_bottom_forward[1], color=colors[1], linewidth=linewidth)
        if with_velocity and (not any(np.isnan(self.velocity))):
            center_bottom_forward = np.mean(corners.T[2:4], axis=0)
            velocity_end = view_points(self.velocity_endpoint, view, normalize=normalize)[:2, 0]
            self.draw_line(canvas, center_bottom_forward[0], velocity_end[0], center_bottom_forward[1], velocity_end[1], color=colors[1], linewidth=linewidth * 2, marker='o')
        if with_label:
            org_center = np.expand_dims(self.center, axis=0).T
            proj_center = view_points(org_center, view, normalize=normalize)[:2, 0]
            self.draw_text(canvas, proj_center[0], proj_center[1], str(self.label))
        if self.future_centers is not None:
            for mode_idx in range(self.num_modes):
                mode_prob = self.mode_probs[mode_idx]
                if mode_prob < self.RENDER_MODE_PROB_THRESHOLD:
                    continue
                prev_x, prev_y, _ = self.center
                for horizon_idx in range(self.num_future_timesteps):
                    if self.num_future_timesteps > 1:
                        color_int = tuple((int(c * 255) for c in colors[0]))
                        color = self.fade_color(color_int, horizon_idx, self.num_future_timesteps - 1)
                        color = tuple((c / 255 for c in color))
                    else:
                        color = colors[0]
                    waypoint = self.future_centers[mode_idx, horizon_idx]
                    if waypoint is not None and (not np.isnan(waypoint).any()):
                        next_x, next_y, _ = waypoint
                        alpha = max(1.0 - horizon_idx * 0.1, 0.1) * mode_prob
                        self.draw_line(from_x=prev_x, to_x=next_x, from_y=prev_y, to_y=next_y, color=color, marker=marker, linewidth=linewidth, canvas=canvas, alpha=alpha)
                        prev_x, prev_y = (next_x, next_y)

    @staticmethod
    def fade_color(color: Tuple[int, int, int], step: int, total_number_of_steps: int) -> Tuple[int, int, int]:
        """
        Fades a color so that future observations are darker in the image.
        :param color: Tuple of ints describing an RGB color.
        :param step: The current time step.
        :param total_number_of_steps: The total number of time steps the agent has in the image.
        :return: Tuple representing faded rgb color.
        """
        LOWEST_VALUE = 0.2
        hsv_color = colorsys.rgb_to_hsv(*color)
        increment = (float(hsv_color[2]) / 255.0 - LOWEST_VALUE) / total_number_of_steps
        new_value = float(hsv_color[2]) / 255.0 - step * increment
        new_rgb = colorsys.hsv_to_rgb(float(hsv_color[0]), float(hsv_color[1]), new_value * 255.0)
        new_rgb_int = tuple((int(c) for c in new_rgb))
        return new_rgb_int

    @staticmethod
    @functools.lru_cache()
    def _calc_corners(width: float, length: float, height: float, center: Tuple[float], rotation_matrix: Tuple[float]) -> npt.NDArray[np.float64]:
        """
        Cached helper function to calculate corners from center and size.
        :param w: Width of box.
        :param l: Length of box.
        :param h: Height of box.
        :param center: Center of box.
        :param rotation_matrix: Rotation matrix of box.
        :return: Corners of box given as <np.float: 3, 8>. First four corners are the ones facing forward.
            The last four are the ones facing backwards.
        """
        corners = np.array([[1, 1, 1, 1, -1, -1, -1, -1], [1, -1, -1, 1, 1, -1, -1, 1], [1, 1, -1, -1, 1, 1, -1, -1]], dtype=float)
        corners[0] *= length / 2
        corners[1] *= width / 2
        corners[2] *= height / 2
        rot_mat = np.array(rotation_matrix).reshape(3, 3)
        corners = np.dot(rot_mat, corners)
        corners += np.array(center).reshape((-1, 1))
        return corners

def __eq__(self, other: object) -> bool:
    """
        Compares the two Box3D object are the same.
        :param other: The other Box3D object.
        :return: True if both objects are the same, otherwise False.
        """
    if not isinstance(other, Box3D):
        return NotImplemented
    center = np.allclose(self.center, other.center, atol=0.0001)
    wlh = np.allclose(self.wlh, other.wlh, atol=0.0001)
    orientation = np.allclose(self.orientation.rotation_matrix, other.orientation.rotation_matrix, atol=0.0001)
    label = self.label == other.label or (np.isnan(self.label) and np.isnan(other.label))
    score = self.score == other.score or (np.isnan(self.score) and np.isnan(other.score))
    vel = np.allclose(self.velocity, other.velocity, atol=0.0001) or (np.all(np.isnan(self.velocity)) and np.all(np.isnan(other.velocity)))
    angular_vel = np.isclose(self.angular_velocity, other.angular_velocity, atol=0.0001) or (np.isnan(self.angular_velocity) and np.isnan(other.angular_velocity))
    payload = self.payload == other.payload
    if not (center and wlh and orientation and label and score and vel and angular_vel and payload):
        return False
    if self.future_horizon_len_s != other.future_horizon_len_s:
        return False
    if self.future_interval_s != other.future_interval_s:
        return False
    if self.num_future_timesteps != other.num_future_timesteps:
        return False
    if self.num_modes != other.num_modes:
        return False
    if (self.future_centers is None) != (other.future_centers is None):
        return False
    if self.future_centers is not None and other.future_centers is not None:
        if not np.array_equal(np.isnan(self.future_centers), np.isnan(other.future_centers)):
            return False
        if not np.allclose(self.future_centers[~np.isnan(self.future_centers)], other.future_centers[~np.isnan(other.future_centers)], atol=0.0001):
            return False
    if not self.equate_orientations(other):
        return False
    if (self.mode_probs is None) != (other.mode_probs is None):
        return False
    if self.mode_probs is not None and other.mode_probs is not None:
        if not np.allclose(self.mode_probs, other.mode_probs, atol=0.0001):
            return False
    return True

class TestBox3DEncoding(unittest.TestCase):
    """Test Box3D Encoding."""

    def test_simple(self) -> None:
        """Test a Box3D object is still the same after serialize and deserialize."""
        box = Box3D((1, 2, 3), (1, 2, 3), Quaternion(0, 0, 0, 0), label=1, score=1.4)
        self.assertEqual(box, Box3D.deserialize(box.serialize()))

    def test_only_mandatory(self) -> None:
        """Test the only mandatory fields to instantiate a Box3D object."""
        box = Box3D((1, 2, 3), (1, 2, 3), Quaternion(0, 0, 0, 0))
        self.assertEqual(box, Box3D.deserialize(box.serialize()))

    def test_all(self) -> None:
        """Test all the fields to instantiate a Box3D object."""
        box = Box3D((1, 2, 3), (1, 2, 3), Quaternion(0, 0, 0, 0), label=1, score=1.2, velocity=(1, 2, 3), angular_velocity=1, payload=dict({'abc': 'def'}))
        self.assertEqual(box, Box3D.deserialize(box.serialize()))

    def test_random(self) -> None:
        """Test random box. After serialize and deserialize, the box is still the same."""
        for i in range(100):
            box = Box3D.make_random()
            self.assertEqual(box, Box3D.deserialize(box.serialize()))

def test_random(self) -> None:
    """Test random box. After serialize and deserialize, the box is still the same."""
    for i in range(100):
        box = Box3D.make_random()
        self.assertEqual(box, Box3D.deserialize(box.serialize()))

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

class TestAssign(unittest.TestCase):
    """Test hungarian algorithm in assign."""

    def test_assign_linear(self) -> None:
        """Test linear cost function."""
        gtboxes = [1, 2, 5]
        estboxes = [4]

        def distance_fcn(a: Any, b: Any) -> float:
            """
            Distance function.
            :param a: Input a.
            :param b: Input b.
            :return: distance between input.
            """
            return float(np.abs(a - b))
        pairs_index = measure.assign(gtboxes, estboxes, distance_fcn, 1.5)
        pairs = [(gtboxes[pair[0]], estboxes[pair[1]]) for pair in pairs_index]
        self.assertEqual(len(pairs), 1)
        self.assertTrue(5 in pairs[0])
        self.assertTrue(4 in pairs[0])
        pairs_index = measure.assign(gtboxes, estboxes, distance_fcn, 0.5)
        pairs = [(gtboxes[pair[0]], estboxes[pair[1]]) for pair in pairs_index]
        self.assertEqual(len(pairs), 0)

    def test_center_distance(self) -> None:
        """Test center distance cost function and new Hungarian algorithm variant."""
        distance_fcn = measure.birdview_center_distance
        gtboxes = [(0, 0), (5, 0)]
        estboxes = [(-5, 0), (0, 0.5)]
        matching = np.array(measure.assign(gtboxes, estboxes, distance_fcn, 2))
        self.assertTrue((matching == [(0, 1)]).all())

def test_assign_linear(self) -> None:
    """Test linear cost function."""
    gtboxes = [1, 2, 5]
    estboxes = [4]

    def distance_fcn(a: Any, b: Any) -> float:
        """
            Distance function.
            :param a: Input a.
            :param b: Input b.
            :return: distance between input.
            """
        return float(np.abs(a - b))
    pairs_index = measure.assign(gtboxes, estboxes, distance_fcn, 1.5)
    pairs = [(gtboxes[pair[0]], estboxes[pair[1]]) for pair in pairs_index]
    self.assertEqual(len(pairs), 1)
    self.assertTrue(5 in pairs[0])
    self.assertTrue(4 in pairs[0])
    pairs_index = measure.assign(gtboxes, estboxes, distance_fcn, 0.5)
    pairs = [(gtboxes[pair[0]], estboxes[pair[1]]) for pair in pairs_index]
    self.assertEqual(len(pairs), 0)

def test_center_distance(self) -> None:
    """Test center distance cost function and new Hungarian algorithm variant."""
    distance_fcn = measure.birdview_center_distance
    gtboxes = [(0, 0), (5, 0)]
    estboxes = [(-5, 0), (0, 0.5)]
    matching = np.array(measure.assign(gtboxes, estboxes, distance_fcn, 2))
    self.assertTrue((matching == [(0, 1)]).all())

class TestMinimumBoundingRectangle(unittest.TestCase):
    """Tests for the minimum_bounding_rectangle() methods."""

    def check_minimum_bounding_rectangle(self, rect_points: npt.NDArray[np.float64], points_to_check: List[List[int]]) -> None:
        """
        Given the points of the minimum rectangle and the points to check, this function checks whether each point
        in points_to_check lies in rect_points.
        :param rect_points: The points of the minimum rectangle.
        :param points_to_check: Points to check if they lie in the minimum rectangle.
        """
        self.assertTrue(rect_points.shape == (4, 2))
        rect_points = np.around(rect_points, decimals=3)
        for point in points_to_check:
            self.assertTrue(np.equal(rect_points, np.around(point, decimals=3)).all(1).any())

    def test_all_square_vertices(self) -> None:
        """
        Use the vertices of a square as the input points. The minimum bounding rectangle for them would be the same
        square.
        """
        points = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [1, 0], [1, 1], [0, 1]])

    def test_all_rectangle_vertices(self) -> None:
        """
        Use the vertices of a rectangle as the input points. The minimum bounding rectangle for them would be the
        complete rectangle.
        """
        points = np.array([[0, 0], [2, 1], [2, 0], [0, 1]])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [2, 0], [0, 1], [2, 1]])

    def test_three_square_vertices(self) -> None:
        """
        Use the three vertices of a square as the input points. The minimum bounding rectangle for them would be the
        complete square.
        """
        points = np.array([[0, 0], [1, 1], [0, 1]])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [1, 0], [1, 1], [0, 1]])
        points = np.array([[1, 0], [1, 1], [0, 1]])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [1, 0], [1, 1], [0, 1]])
        points = np.array([[0, 0], [1, 1], [1, 0]])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [1, 0], [1, 1], [0, 1]])

    def test_lots_of_random_points_in_a_square(self) -> None:
        """
        Use the three vertices of a square as the input points. Then concatenate a bunch of random points inside the
        square to those points. The minimum bounding rectangle for them would be the original square.
        """
        points = np.array([[0, 0], [1, 1], [0, 1]])
        pts_inside_square = np.random.rand(30, 2)
        points = np.concatenate([points, pts_inside_square])
        rect_points = minimum_bounding_rectangle(points)
        self.check_minimum_bounding_rectangle(rect_points, [[0, 0], [1, 0], [1, 1], [0, 1]])

    def test_lots_of_random_points_in_a_rotated_square(self) -> None:
        """
        Use the four vertices of a square as the input points. Then concatenate a bunch of random points inside the
        square to those points. Finally rotate all the points by a fixed angle. The minimum bounding rectangle for them
        would be the original square rotated by the same angle chosen in the last step.
        """
        points = np.array([[0, 0], [1, 1], [0, 1], [1, 0]])
        pts_inside_square = np.random.rand(30, 2)
        points = np.concatenate([points, pts_inside_square])
        rand_angle = np.random.randn()
        rot_mat = np.array([[np.cos(rand_angle), np.sin(rand_angle)], [-np.sin(rand_angle), np.cos(rand_angle)]])
        rect_points = minimum_bounding_rectangle(np.dot(rot_mat, points.T).T)
        self.check_minimum_bounding_rectangle(rect_points, np.dot(rot_mat, np.array([[0, 0], [1, 0], [1, 1], [0, 1]]).T).T)

def check_minimum_bounding_rectangle(self, rect_points: npt.NDArray[np.float64], points_to_check: List[List[int]]) -> None:
    """
        Given the points of the minimum rectangle and the points to check, this function checks whether each point
        in points_to_check lies in rect_points.
        :param rect_points: The points of the minimum rectangle.
        :param points_to_check: Points to check if they lie in the minimum rectangle.
        """
    self.assertTrue(rect_points.shape == (4, 2))
    rect_points = np.around(rect_points, decimals=3)
    for point in points_to_check:
        self.assertTrue(np.equal(rect_points, np.around(point, decimals=3)).all(1).any())

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

def _test_numpy_type(self, img: Any) -> None:
    """
        Checks if the given object is a numpy array with dtype uint8.
        :param img: The image object to test. Type hint any because the test should be valid for all objects.
        """
    self.assertEqual(np.ndarray, type(img))
    self.assertEqual(np.uint8, img.dtype)
    self.assertNotEqual(np.float64, img.dtype)

class PointCloud:
    """
    Class for raw .pcd file.
    """

    def __init__(self, header: PointCloudHeader, points: npt.NDArray[np.float64]) -> None:
        """
        PointCloud.
        :param header: Pointcloud header.
        :param points: <np.ndarray, X, N>. X columns, N points.
        """
        self._header = header
        self._points = points

    @property
    def header(self) -> PointCloudHeader:
        """
        Returns pointcloud header.
        :return: A PointCloudHeader instance.
        """
        return self._header

    @property
    def points(self) -> npt.NDArray[np.float64]:
        """
        Returns points.
        :return: <np.ndarray, X, N>. X columns, N points.
        """
        return self._points

    def save(self, file_path: str) -> None:
        """
        Saves to .pcd file.
        :param file_path: The path to the .pcd file.
        """
        with open(file_path, 'wb') as fp:
            fp.write('# .PCD v{} - Point Cloud Data file format\n'.format(self._header.version).encode('utf8'))
            for field in self._header._fields:
                value = getattr(self._header, field)
                if isinstance(value, list):
                    text = ' '.join(map(str, value))
                else:
                    text = str(value)
                fp.write('{} {}\n'.format(field.upper(), text).encode('utf8'))
            fp.write(self._points.tobytes())

    @classmethod
    def parse(cls, pcd_content: bytes) -> PointCloud:
        """
        Parses the pointcloud from byte stream.
        :param pcd_content: The byte stream that holds the pcd content.
        :return: A PointCloud object.
        """
        with BytesIO(pcd_content) as stream:
            header = cls.parse_header(stream)
            points = cls.parse_points(stream, header)
            return cls(header, points)

    @classmethod
    def parse_from_file(cls, pcd_file: str) -> PointCloud:
        """
        Parses the pointcloud from .pcd file on disk.
        :param pcd_file: The path to the .pcd file.
        :return: A PointCloud instance.
        """
        with open(pcd_file, 'rb') as stream:
            header = cls.parse_header(stream)
            points = cls.parse_points(stream, header)
            return cls(header, points)

    @staticmethod
    def parse_header(stream: IO[Any]) -> PointCloudHeader:
        """
        Parses the header of a pointcloud from byte IO stream.
        :param stream: Binary stream.
        :return: A PointCloudHeader instance.
        """
        headers_list = []
        while True:
            line = stream.readline().decode('utf8').strip()
            if line.startswith('#'):
                continue
            columns = line.split()
            key = columns[0].lower()
            val = columns[1:] if len(columns) > 2 else columns[1]
            headers_list.append((key, val))
            if key == 'data':
                break
        headers = dict(headers_list)
        headers['size'] = list(map(int, headers['size']))
        headers['count'] = list(map(int, headers['count']))
        headers['width'] = int(headers['width'])
        headers['height'] = int(headers['height'])
        headers['viewpoint'] = list(map(int, headers['viewpoint']))
        headers['points'] = int(headers['points'])
        header = PointCloudHeader(**headers)
        if any([c != 1 for c in header.count]):
            raise RuntimeError('"count" has to be 1')
        if not len(header.fields) == len(header.size) == len(header.type) == len(header.count):
            raise RuntimeError('fields/size/type/count field number are inconsistent')
        return header

    @staticmethod
    def parse_points(stream: IO[Any], header: PointCloudHeader) -> npt.NDArray[np.float64]:
        """
        Parses points from byte IO stream.
        :param stream: Byte stream that holds the points.
        :param header: <np.ndarray, X, N>. A numpy array that has X columns(features), N points.
        :return: Points of Point Cloud.
        """
        if header.data != 'binary':
            raise RuntimeError('Un-supported data foramt: {}. "binary" is expected.'.format(header.data))
        row_type = PointCloud.np_type(header)
        length = row_type.itemsize * header.points
        buff = stream.read(length)
        if len(buff) != length:
            raise RuntimeError('Incomplete pointcloud stream: {} bytes expected, {} got'.format(length, len(buff)))
        points = np.frombuffer(buff, row_type)
        return points

    @staticmethod
    def np_type(header: PointCloudHeader) -> np.dtype:
        """
        Helper function that translate column types in pointcloud to np types.
        :param header: A PointCloudHeader object.
        :return: np.dtype that holds the X features.
        """
        type_mapping = {'I': 'int', 'U': 'uint', 'F': 'float'}
        np_types = [type_mapping[t] + str(int(s) * 8) for t, s in zip(header.type, header.size)]
        return np.dtype([(f, getattr(np, nt)) for f, nt in zip(header.fields, np_types)])

    def to_pcd_bin(self) -> npt.NDArray[np.float32]:
        """
        Converts pointcloud to .pcd.bin format.
        :return: <np.float32, 5, N>, the point cloud in .pcd.bin format.
        """
        lidar_fields = ['x', 'y', 'z', 'intensity', 'ring']
        return np.array([np.array(self.points[f], dtype=np.float32) for f in lidar_fields])

    def to_pcd_bin2(self) -> npt.NDArray[np.float32]:
        """
        Converts pointcloud to .pcd.bin2 format.
        :return: <np.float32, 6, N>, the point cloud in .pcd.bin2 format.
        """
        lidar_fields = ['x', 'y', 'z', 'intensity', 'ring', 'lidar_info']
        return np.array([np.array(self.points[f], dtype=np.float32) for f in lidar_fields])

@staticmethod
def np_type(header: PointCloudHeader) -> np.dtype:
    """
        Helper function that translate column types in pointcloud to np types.
        :param header: A PointCloudHeader object.
        :return: np.dtype that holds the X features.
        """
    type_mapping = {'I': 'int', 'U': 'uint', 'F': 'float'}
    np_types = [type_mapping[t] + str(int(s) * 8) for t, s in zip(header.type, header.size)]
    return np.dtype([(f, getattr(np, nt)) for f, nt in zip(header.fields, np_types)])

class TestPointCloud(unittest.TestCase):
    """Test Class for Point Cloud."""

    def test_load_pcd_bin_v1(self) -> None:
        """Testing if points in binary format v1 can be read."""
        pcd_expected = np.array([[3.5999999, -3.0999999, 0, 1, 0.5, -1], [1.0, -3.01, 10.0, 0.4, 10, -1], [4.5999999, -2.90001, -1.0, 0.1, 1.5, -1]], dtype=np.float32)
        file_path = tempfile.NamedTemporaryFile()
        with open(file_path.name, 'w+b'):
            for point in pcd_expected:
                file_path.write(struct.pack('5f', point[0], point[1], point[2], point[3], point[4]))
            _ = file_path.seek(0)
            pcd = LidarPointCloud.load_pcd_bin(file_path.name)
            assert np.all(pcd == pcd_expected.T)

    def test_load_pcd_bin_v2(self) -> None:
        """Testing if points in binary format v2 can be read."""
        pcd_expected = np.array([[3.5999999, -3.0999999, 0, 1, 0.5, -1], [1.0, -3.01, 10.0, 0.4, 10, -1], [4.5999999, -2.90001, -1.0, 0.1, 1.5, -1]], dtype=np.float32)
        file_path = tempfile.NamedTemporaryFile()
        with open(file_path.name, 'w+b'):
            for point in pcd_expected:
                file_path.write(struct.pack('6f', point[0], point[1], point[2], point[3], point[4], point[5]))
            _ = file_path.seek(0)
            pcd = LidarPointCloud.load_pcd_bin(file_path.name, 2)
            assert np.all(pcd == pcd_expected.T)

    def test_nbr_points(self) -> None:
        """Testing if the number of points in the pointcloud is returned."""
        test_pointcloud = np.array([[35, 35, 0, 0, 0], [20.0, 30.0, 2000, 0, 0], [30.0, 20.0, 0, 0, 0], [8.0, 8.0, 0, 0, 0], [0.0, 15.0, 10, 0, 0]])
        pc = LidarPointCloud(test_pointcloud.T)
        self.assertEqual(pc.nbr_points(), 5)

    def test_subsample(self) -> None:
        """Testing if the correct number of points are sampled given the ratio."""
        test_pointcloud = np.zeros((100, 5))
        pc = LidarPointCloud(test_pointcloud.T)
        pc.subsample(ratio=0.5)
        self.assertEqual(pc.nbr_points(), 50)
        pc.subsample(ratio=0.2)
        self.assertEqual(pc.nbr_points(), 10)
        pc.subsample(ratio=0.18)
        self.assertEqual(pc.nbr_points(), 1)

    def test_1d_array_input(self) -> None:
        """Testing if can do translate/rotate function from single point input array."""
        pc = LidarPointCloud(np.array([0, 0, 0, 0, 0]))
        test_translate = np.array([0, 0, 1])
        pc.translate(test_translate)
        assert_array_equal(pc.points[:, 0], np.array([0, 0, 1, 0, 0]))
        theta = np.pi
        test_rot_matrix = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(theta), -np.sin(theta)], [0.0, np.sin(theta), np.cos(theta)]])
        pc.rotate(Quaternion(matrix=test_rot_matrix))
        self.assertAlmostEqual(pc.points[0, 0], 0)
        self.assertAlmostEqual(pc.points[1, 0], 0)
        self.assertAlmostEqual(pc.points[2, 0], -1)

    def test_remove_close(self) -> None:
        """Testing if points within a certain radius from origin (in bird view) are correctly removed."""
        test_pointcloud = np.array([[35, 35, 0, 0, 0], [20.0, 30.0, 2000, 0, 0], [30.0, 20.0, 0, 0, 0], [8.0, 8.0, 0, 0, 0], [0.0, 15.0, 10, 0, 0]])
        pc = LidarPointCloud(test_pointcloud.T)
        pc.remove_close(5)
        self.assertEqual(pc.nbr_points(), 5)
        pc.remove_close(12)
        self.assertEqual(pc.nbr_points(), 4)
        pc.remove_close(15)
        self.assertEqual(pc.nbr_points(), 4)
        pc.remove_close(36.1)
        self.assertEqual(pc.nbr_points(), 1)

    def test_radius_filter(self) -> None:
        """Testing if points within a certain radius from origin (in bird view) is correctly removed."""
        test_pointcloud = np.array([[35, 35, 0, 0, 0], [20.0, 30.0, 2000, 0, 0], [30.0, 20.0, 0, 0, 0], [8.0, 8.0, 0, 0, 0], [0.0, 15.0, 10, 0, 0]])
        pointcloud = LidarPointCloud(test_pointcloud.T)
        pc = pointcloud.copy()
        pc.radius_filter(5)
        self.assertEqual(pc.nbr_points(), 0)
        pc = pointcloud.copy()
        pc.radius_filter(12)
        self.assertEqual(pc.nbr_points(), 1)
        pc = pointcloud.copy()
        pc.radius_filter(15)
        self.assertEqual(pc.nbr_points(), 2)
        pc = pointcloud.copy()
        pc.radius_filter(36.1)
        self.assertEqual(pc.nbr_points(), 4)

    def test_scale(self) -> None:
        """Testing if the lidar xyz coordinates are scaled."""
        test_pointcloud = np.array([[35, 35, 0, 0, 0], [20.0, 30.0, 2000, 0, 0], [30.0, 20.0, 0, 0, 0], [8.0, 8.0, 0, 0, 0], [0.0, 15.0, 10, 0, 0]])
        test_pc = test_pointcloud.copy()
        pc = LidarPointCloud(test_pc.T)
        pc.scale((2, 2, 2))
        test_pc_scaled = test_pointcloud.copy()
        test_pc_scaled[:, 0:3] *= 2
        pc_scaled = LidarPointCloud(test_pc_scaled.T)
        self.assertEqual(pc, pc_scaled)

    def test_translate_simple(self) -> None:
        """Testing if points are translated correctly given a translate vector."""
        pc = LidarPointCloud(np.array([[0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 2.0, 3.0, 0.0, 0.0]]).T)
        test_translate = np.array([5.2, 10.4, 15.1])
        pc.translate(test_translate)
        assert_array_equal(pc.points[:, 0], np.array([5.2, 10.4, 15.1, 0, 0]))
        assert_array_equal(pc.points[:, 1], np.array([6.2, 12.4, 18.1, 0, 0]))

    def test_rotate_simple(self) -> None:
        """Testing if points are rotated correctly given a rotation matrix."""
        theta = np.pi / 4
        test_rot_matrix = np.array([[1.0, 0.0, 0.0], [0.0, np.cos(theta), -np.sin(theta)], [0.0, np.sin(theta), np.cos(theta)]])
        pc = LidarPointCloud(np.array([[0.0, 0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0]]).T)
        pc.rotate(Quaternion(matrix=test_rot_matrix))
        self.assertAlmostEqual(pc.points[0, 0], 0)
        self.assertAlmostEqual(pc.points[1, 0], -1 / np.sqrt(2))
        self.assertAlmostEqual(pc.points[2, 0], 1 / np.sqrt(2))

    def test_copy(self) -> None:
        """Verify that copy works as expected."""
        pc_orig = LidarPointCloud.make_random()
        pc_copy = pc_orig.copy()
        self.assertEqual(pc_orig, pc_copy)
        pc_orig.points[0, 0] += 1
        self.assertNotEqual(pc_orig, pc_copy)

    def test_read_pcd_ascii_xyz(self) -> None:
        """Test making a LidarPointCloud with x, y, and z fields from a .pcd file with ascii data."""
        pcd_contents = b'#.PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH 3\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS 3\nDATA ascii\n3.5999999 -3.0999999 0\n1.0 -3.01 10.0\n4.5999999 -2.90001 -1.0'
        temp_file = tempfile.NamedTemporaryFile(suffix='.pcd')
        temp_file.write(pcd_contents)
        _ = temp_file.seek(0)
        pcd = LidarPointCloud.from_file(temp_file.name)
        self.assertEqual(pcd.nbr_points(), 3)
        expected_points = np.array([[3.5999999, -3.0999999, 0, 0], [1.0, -3.01, 10, 0], [4.5999999, -2.90001, -1.0, 0]]).T
        self.assertEqual(np.all(np.isclose(pcd.points, expected_points)), True)

    def test_read_pcd_ascii_xyzi(self) -> None:
        """Test making a LidarPointCloud with x, y, z, and intensity fields from a .pcd file with ascii data."""
        pcd_contents = b'#.PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS x y z r intensity rcs\nSIZE 4 4 4 4 4 4\nTYPE F F F F F F\nCOUNT 1 1 1 1 1 1\nWIDTH 3\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS 3\nDATA ascii\n3.5999999 -3.0999999 0 1 0.5 7.5\n1.0 -3.01 10.0 0.4 10 2.5\n4.5999999 -2.90001 -1.0 0.1 1.5 -3.5'
        temp_file = tempfile.NamedTemporaryFile(suffix='.pcd')
        temp_file.write(pcd_contents)
        _ = temp_file.seek(0)
        pcd = LidarPointCloud.from_file(temp_file.name)
        self.assertEqual(pcd.nbr_points(), 3)
        expected_points = np.array([[3.5999999, -3.0999999, 0, 0.5], [1.0, -3.01, 10, 10], [4.5999999, -2.90001, -1.0, 1.5]]).T
        self.assertEqual(np.all(np.isclose(pcd.points, expected_points)), True)

    def test_read_pcd_ascii_xyzit(self) -> None:
        """Test making a LidarPointCloud with x, y, z, intensity, and time fields from a .pcd file with ascii data."""
        pcd_contents = f'#.PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS x y z r intensity rcs {PCD_TIMESTAMP_FIELD_NAME}\nSIZE 4 4 4 4 4 4 4\nTYPE F F F F F F F\nCOUNT 1 1 1 1 1 1 1\nWIDTH 3\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS 3\nDATA ascii\n3.5999999 -3.0999999 0 1 0.5 7.5 0\n1.0 -3.01 10.0 0.4 10 2.5 0.05\n4.5999999 -2.90001 -1.0 0.1 1.5 -3.5 0.1'.encode('utf-8')
        temp_file = tempfile.NamedTemporaryFile(suffix='.pcd')
        temp_file.write(pcd_contents)
        _ = temp_file.seek(0)
        pcd = LidarPointCloud.from_file(temp_file.name)
        self.assertEqual(pcd.nbr_points(), 3)
        expected_points = np.array([[3.5999999, -3.0999999, 0, 0.5, 0], [1.0, -3.01, 10, 10, 0.05], [4.5999999, -2.90001, -1.0, 1.5, 0.1]]).T
        self.assertEqual(np.all(np.isclose(pcd.points, expected_points)), True)

    def test_read_pcd_ascii_shuffled_field_order(self) -> None:
        """
        Test making a LidarPointCloud with x, y, z, intensity, and time fields from a .pcd file
        with ascii data where the fields are in an unusual order.
        """
        pcd_contents = f'#.PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS {PCD_TIMESTAMP_FIELD_NAME} intensity r rcs x y z\nSIZE 4 4 4 4 4 4 4\nTYPE F F F F F F F\nCOUNT 1 1 1 1 1 1 1\nWIDTH 2\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS 2\nDATA ascii\n1 2 3 4 5 6 7\n8 9 10 11 12 13 14'.encode('utf-8')
        temp_file = tempfile.NamedTemporaryFile(suffix='.pcd')
        temp_file.write(pcd_contents)
        _ = temp_file.seek(0)
        pcd = LidarPointCloud.from_file(temp_file.name)
        self.assertEqual(pcd.nbr_points(), 2)
        expected_points = np.array([[5, 6, 7, 2, 1], [12, 13, 14, 9, 8]]).T
        self.assertEqual(np.all(np.isclose(pcd.points, expected_points)), True)

    def test_range_filter(self) -> None:
        """Test if Range filter works as expected."""
        points_orig = np.array([[2.26, -0.76, 4.72, -5.46, 9.54, -8.89, 5.45, 7.05, -0.89, 8.58], [-0.88, 1.81, -9.12, 3.32, 3.13, -8.67, -5.11, 6.22, 9.39, -3.25], [4.42, -9.08, 0.12, 2.5, -4.23, 2.08, 8.12, 9.22, -8.71, 3.9], [2.25, 4.32, 4.53, 2.88, 2.84, 0.79, 7.62, 1.21, 3.3, 0.52], [9.72, 9.43, 3.67, 9.99, 5.56, 3.15, 0.02, 7.07, 8.64, 6.16]], dtype=float)
        pc = LidarPointCloud(points_orig)
        pc.range_filter(xrange=(-2, 2))
        should_match = np.array([[-0.76, 1.81, -9.08, 4.32, 9.43], [-0.89, 9.39, -8.71, 3.3, 8.64]]).T
        self.assertTrue(np.array_equal(pc.points, should_match))
        pc = LidarPointCloud(points_orig)
        pc.range_filter(xrange=(5, 10), yrange=(-5, 0), zrange=(3, 5))
        should_match = np.array([[8.58, -3.25, 3.9, 0.52, 6.16]]).T
        self.assertTrue(np.array_equal(pc.points, should_match))
        pc = LidarPointCloud(points_orig)
        pc.range_filter(xrange=(1000, 2000))
        self.assertEqual(pc.nbr_points(), 0)
        pc = LidarPointCloud(points_orig)
        pc.range_filter(xrange=(-100, 100), yrange=(-100, 100), zrange=(-100, 100))
        self.assertTrue(np.array_equal(pc.points, points_orig))

    def test_transform(self) -> None:
        """
        Test the transform function (example transformation matrices taken from
        https://www.springer.com/cda/content/document/cda_downloaddocument/9789048137756-c2.pdf?SGWID=0-0-45-1123955-p173940737
        """
        test_points = np.array([[1, 0, 1], [0, 1, 1], [0, 0, 1], [0.0, 0.0, 0.0]])
        pc = LidarPointCloud(test_points.copy())
        pc.transform(np.array([[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 0], [0.0, 0.0, 0.0, 1]]))
        shouldMatch = np.array([[2, 1, 2], [1, 2, 2], [0, 0, 1], [0.0, 0.0, 0.0]])
        self.assertTrue(np.array_equal(pc.points, shouldMatch))
        pc = LidarPointCloud(test_points.copy())
        pc.transform(np.array([[0, 0, 1, 4], [1, 0, 0, -3], [0, 1, 0, 7], [0.0, 0.0, 0.0, 1]]))
        shouldMatch = np.array([[4, 4, 5], [-2, -3, -2], [7, 8, 8], [0.0, 0.0, 0.0]])
        self.assertTrue(np.array_equal(pc.points, shouldMatch))

    def test_equality(self) -> None:
        """Test equality of two points cloud based on element-wise difference."""
        test_points = np.array([[1, 0, 1], [0, 1, 1], [0, 0, 1], [0.0, 0.0, 0.0]])
        pc = LidarPointCloud(test_points.copy())
        test_points_2 = np.asarray([[1.0000001, 1e-07, 1], [1e-07, 1.0000001, 1], [0, 0.0, 1], [0.0, 0.0, 0.0]])
        pc2 = LidarPointCloud(test_points_2.copy())
        self.assertEqual(pc, pc2)
        pc = LidarPointCloud.make_random()
        pc2 = LidarPointCloud.make_random()
        self.assertNotEqual(pc, pc2)

    def test_rotate_composite(self) -> None:
        """Testing if points are rotated correctly for a composite rotation sequence."""
        test_point = np.array([[0, 0, -1, 0, 0], [0, -1, 0, 0, 0]]).T
        alpha, beta, gamma = (np.pi, np.pi / 2, np.pi / 2)
        test_rot_matrix_alpha = np.array([[1.0, 0.0, 0.0], [0, np.cos(alpha), -np.sin(alpha)], [0, np.sin(alpha), np.cos(alpha)]])
        test_rot_matrix_beta = np.array([[np.cos(beta), 0, np.sin(beta)], [0, 1, 0], [-np.sin(beta), 0, np.cos(beta)]])
        test_rot_matrix_gamma = np.array([[np.cos(gamma), -np.sin(gamma), 0], [np.sin(gamma), np.cos(gamma), 0], [0, 0, 1]])
        rotated_test_point = np.array([[0, 1, 0, 0, 0], [-1, 0, 0, 0, 0]]).T
        pc = LidarPointCloud(test_point)
        pc.rotate(Quaternion(matrix=test_rot_matrix_alpha))
        pc.rotate(Quaternion(matrix=test_rot_matrix_beta))
        pc.rotate(Quaternion(matrix=test_rot_matrix_gamma))
        assert_array_equal(pc.points, rotated_test_point)

def test_scale(self) -> None:
    """Testing if the lidar xyz coordinates are scaled."""
    test_pointcloud = np.array([[35, 35, 0, 0, 0], [20.0, 30.0, 2000, 0, 0], [30.0, 20.0, 0, 0, 0], [8.0, 8.0, 0, 0, 0], [0.0, 15.0, 10, 0, 0]])
    test_pc = test_pointcloud.copy()
    pc = LidarPointCloud(test_pc.T)
    pc.scale((2, 2, 2))
    test_pc_scaled = test_pointcloud.copy()
    test_pc_scaled[:, 0:3] *= 2
    pc_scaled = LidarPointCloud(test_pc_scaled.T)
    self.assertEqual(pc, pc_scaled)

def test_copy(self) -> None:
    """Verify that copy works as expected."""
    pc_orig = LidarPointCloud.make_random()
    pc_copy = pc_orig.copy()
    self.assertEqual(pc_orig, pc_copy)
    pc_orig.points[0, 0] += 1
    self.assertNotEqual(pc_orig, pc_copy)

def test_equality(self) -> None:
    """Test equality of two points cloud based on element-wise difference."""
    test_points = np.array([[1, 0, 1], [0, 1, 1], [0, 0, 1], [0.0, 0.0, 0.0]])
    pc = LidarPointCloud(test_points.copy())
    test_points_2 = np.asarray([[1.0000001, 1e-07, 1], [1e-07, 1.0000001, 1], [0, 0.0, 1], [0.0, 0.0, 0.0]])
    pc2 = LidarPointCloud(test_points_2.copy())
    self.assertEqual(pc, pc2)
    pc = LidarPointCloud.make_random()
    pc2 = LidarPointCloud.make_random()
    self.assertNotEqual(pc, pc2)

class Table(Sequence[T]):
    """
    Table wrapper. Provide some convenient APIs, for example:
        table = Table(Sample, session)

        first_row = table[0]
        last_row = table[-1]
        some_random_rows = table[50:100]
        my_row = table['row_token_here']

        total_num = len(table)
    """

    def __init__(self, table: Any, db: DB) -> None:
        """
        Init table.
        :param table: Class type in models.py.
        :param db: DB instance.
        """
        self._table = table
        self._db = db
        event.listen(table, 'load', self._decorate_record)

    def _decorate_record(self, record: T, context: Any) -> None:
        """
        Sqlalchemy hook function. This will be called each time sqlalchemy loads a object from db.
        We save table reference as "_table" in the record here.
        :param record: The record loaded from database.
        :param context: Some context we don't use.
        """
        record._table = self

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        count = self.count()
        _repr = str(self._table.__name__) + '({} entries):\n{}\n'.format(count, '-' * 50)
        for ind in range(count)[:3]:
            _repr += repr(self._session.query(self._table)[ind])
        if count > 3:
            _repr += '(...) \n'
            _repr += repr(self._session.query(self._table)[count - 1])
        return _repr

    @property
    def _session(self) -> Session:
        """
        Get the underlying db session.
        :return: The underlying db session.
        """
        return self.db.session

    @property
    def db(self) -> DB:
        """
        Get the underlying db.
        :return: The underlying db.
        """
        return self._db

    def get(self, token: str) -> T:
        """
        Returns a record from table.
        :param token: Token of the record.
        :return: Record object.
        """
        return self._session.query(self._table).get(token)

    def select_one(self, **filters: Any) -> Optional[T]:
        """
        Query table using filters. There should be at most one record matching
        given filters, use select_many for searching multiple records.
            cat = nuplandb.category.select_one(name='vehicle')
        :param filters: Query using keyword expression. For example, query log by log file name:
            log = nuplandb.log.select_one(logfile='2021.07.16.20.45.29_veh-35_01095_01486')
        :return: Record object matching the given filters.
        """
        record: Optional[T] = self._session.query(self._table).filter_by(**filters).one_or_none()
        return record

    def select_many(self, **filters: Any) -> List[T]:
        """
        Query table using filters.
            boston_logs = nuplandb.log.select_many(location='boston').
        :param filters: Query using keyword expression. For example, query log by vehicle:
            logs = nuplandb.log.select_many(vehicle_name='35')
        :return: A list of records mathing the given filters.
        """
        return self._session.query(self._table).filter_by(**filters).all()

    def count(self, **kwargs: Any) -> int:
        """
        Count records for the given queries. For example:
            nuplandb.log.count(location='las_vegas').
        :param kwargs: Filters to count records.
        :return: The number of counted records.
        """
        return self._session.query(self._table).filter_by(**kwargs).count()

    def all(self) -> List[T]:
        """
        Return all the items for the given queries. For example:
            nuplandb.log.all().
        :return: List of records.
        """
        return self._session.query(self._table).all()

    def detach(self) -> None:
        """
        Performs any necessary cleanup of the table for destruction.
        This function must be called once the table is ready to be destroyed to properly free resources.
        Once this function is called, the table should no longer be queried.
        """
        event.remove(self._table, 'load', self._decorate_record)

    def __len__(self) -> int:
        """
        Return length of the records for the given queries. For example:
            nuplandb.log.__len()
        :return: Number of records.
        """
        return self._session.query(self._table.token).count()

    @overload
    def __getitem__(self, index: int) -> T:
        """Inherited, see superclass."""
        ...

    @overload
    def __getitem__(self, token: str) -> T:
        """Inherited, see superclass."""
        ...

    @overload
    def __getitem__(self, indexes: slice) -> List[T]:
        """Inherited, see superclass."""
        ...

    def __getitem__(self, key: Union[int, str, slice]) -> T:
        """Inherited, see superclass."""
        if isinstance(key, str):
            return self._session.query(self._table).get(key)
        else:
            return self._session.query(self._table)[key]

    def __iter__(self) -> Iterator[T]:
        """
        Inherited, see superclass.
        The implementation in Sequence is not good, it uses self[i] to loop over all elements
        which makes it much slower.
        Detail of yield_per can be found:
            https://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per
        """
        query = self._session.query(self._table).yield_per(2000).enable_eagerloads(False)
        for row in query:
            yield row

def detach(self) -> None:
    """
        Performs any necessary cleanup of the table for destruction.
        This function must be called once the table is ready to be destroyed to properly free resources.
        Once this function is called, the table should no longer be queried.
        """
    event.remove(self._table, 'load', self._decorate_record)

class DB:
    """
    Base class for DB loaders. Inherited classes should implement property method for each table with type
    annotation, for example:
        class NuPlanDB(DB):
            @property
            def category(self) -> Table[nuplandb_model.Category]:
                return self.tables['category']

    It is not recommended to use db.get('category', some_token), use db.category.get(some_token) or
    db.category[some_token] instead, because we can't get any type hint from the former one.
    """

    def __init__(self, table_names: List[str], models: Any, data_root: str, db_path: str, verbose: bool, model_source_dict: Dict[str, str]={}):
        """
        Initialize database by loading from filesystem or downloading from S3, load json table and build token index.
        :param table_names: List of table names.
        :param models: Auto-generated model template.
        :param data_root: Path to load the database from; if the database is downloaded from S3
                          this is the path to store the downloaded database.
        :param db_path: Local or S3 path to the database file.
        :param verbose: Whether to print status messages when loading the database.
        """
        self._table_names = list(table_names)
        self._data_root = data_root
        self._blob_store = BlobStoreCreator.create_nuplandb(data_root)
        self._tables = {}
        self._tables_detached = False
        self._refcount = 1
        self._refcount_lock = threading.Lock()
        db_path = db_path if db_path.endswith('.db') else f'{db_path}.db'
        self._db_path = Path(db_path)
        self._filename = self._db_path if self._db_path.exists() else Path(self._data_root) / self._db_path.name
        if not self._filename.exists():
            logger.debug(f'DB path not found, downloading db file to {self._filename}...')
            start_time = time.time()
            cache_store = CacheStore(self._data_root, self._blob_store)
            cache_store.save_to_disk(self._db_path.name)
            logger.debug('Downloading db file took {:.1f} seconds'.format(time.time() - start_time))
        if verbose:
            logger.debug('\nLoading tables for database {}...'.format(self.name))
            start_time = time.time()
        self._session_manager = SessionManager(self._create_db_instance)
        for table_name in self._table_names:
            model_name = ''.join([s.capitalize() for s in table_name.split('_')])
            if len(model_source_dict) != 0:
                if model_name in model_source_dict:
                    model_pcls = getattr(models, model_source_dict[model_name])
                else:
                    model_pcls = getattr(models, model_source_dict['default'])
                model_cls = getattr(model_pcls, model_name)
            else:
                model_cls = getattr(models, model_name)
            self._tables[table_name] = Table[model_cls](model_cls, self)
        if verbose:
            for table_name in self._table_names:
                logger.debug('{} {},'.format(len(self._tables[table_name]), table_name))
            logger.debug('Done loading in {:.1f} seconds.\n'.format(time.time() - start_time))

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        return "{}('{}', data_root='{}')".format(self.__class__.__name__, self.name, self.data_root)

    def __str__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        _str = '{} {} with tables:\n{}'.format(self.__class__.__name__, self.name, '=' * 30)
        for table_name in self.table_names:
            if 'log' == table_name:
                continue
            _str += '\n{:20}: {}'.format(table_name, getattr(self, table_name).count())
        return _str

    @property
    def session(self) -> Session:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return self._session_manager.session

    @property
    def name(self) -> str:
        """
        Get the db name.
        :return: The db name.
        """
        return self._db_path.stem

    @property
    def data_root(self) -> str:
        """
        Get the data root.
        :return: The data root.
        """
        return self._data_root

    @property
    def table_root(self) -> str:
        """
        Get the table root.
        :return: The table root.
        """
        return str(self._filename)

    @property
    def table_names(self) -> List[str]:
        """
        Get the list of table names.
        :return: The list of table names.
        """
        self._assert_tables_attached()
        return self._table_names

    @property
    def tables(self) -> Dict[str, Table[Any]]:
        """
        Get the list of tables.
        :return: The list of tables.
        """
        self._assert_tables_attached()
        return self._tables

    def load_blob(self, path: str) -> BinaryIO:
        """
        Loads a blob.
        :param path: Path to the blob.
        :return: A binary stream to read the blob.
        """
        return self._blob_store.get(path)

    def get(self, table: str, token: str) -> Any:
        """
        Returns a record from table.
        :param table: Table name.
        :param token: Token of the record.
        :return: The record. See "templates.py" for details.
        """
        warnings.warn('deprecated', DeprecationWarning)
        self._assert_tables_attached()
        return getattr(self, table).get(token)

    def field2token(self, table: str, field: str, query: str) -> List[str]:
        """
        Function returns a list of tokens given a table and field of that table.
        :param table: Table name.
        :param field: Field name, see "template.py" for details.
        :param query: The same type as the field.
        :return: Return a list of record tokens.
        """
        warnings.warn('deprecated', DeprecationWarning)
        self._assert_tables_attached()
        return [rec.token for rec in getattr(self, table).search(**{field: query})]

    def are_tables_detached(self) -> bool:
        """
        Returns true if the tables have been detached, false otherwise.
        :returns: True if the tables have been detached, false otherwise.
        """
        return self._tables_detached

    def detach_tables(self) -> None:
        """
        Prepares all tables for destruction.
        This must be called when DB is ready to be released to reclaim used memory.
        After calling this method, no further queries should be run from the db.

        Placing this in __del__ is not sufficient, because without detaching tables,
          SQLAlchemy will keep references to the tables alive.
          Which contain references to the DB.
          Which means that __del__ will never be called.
        """
        if not self._tables_detached:
            for table_name in self.table_names:
                self.tables[table_name].detach()
            self._tables_detached = True

    def _assert_tables_attached(self) -> None:
        """
        Checks to ensure that the tables are attached. If not, raises an error.
        """
        if self.are_tables_detached():
            raise RuntimeError('Attempting to query from detached tables.')

    def add_ref(self) -> None:
        """
        Add an external reference to this class to prevent it from being reclaimed by the GC.
        This method should be called when any non-SqlAlchemy class takes a reference to the class.

        See the comments in __init__ for explanation
        """
        with self._refcount_lock:
            if self._refcount == 0:
                raise ValueError('Attempting to revive a database that has had its tables detached. This is likely due to a reference counting error.')
            self._refcount += 1

    def remove_ref(self) -> None:
        """
        Removes an external reference to this class.
        This should be called when any non-SqlAlchemy class is finished using the database (e.g. in their __del__ method).
        If the reference count gets to zero, it will be prepared for collection by the GC.
        """
        with self._refcount_lock:
            self._refcount -= 1
            if self._refcount == 0:
                self.detach_tables()

    def _create_db_instance(self) -> sqlite3.Connection:
        """
        Internal method, return sqlite3 connection for sqlalchemy.
        :return: Sqlite3 connection.
        """
        assert Path(self.table_root).exists(), 'DB file not found: {}'.format(self.table_root)
        db = sqlite3.connect('file:{}?mode=ro'.format(self.table_root), uri=True, check_same_thread=False)
        db.execute('PRAGMA main.journal_mode = OFF;')
        db.execute('PRAGMA main.cache_size=10240;')
        db.execute('PRAGMA main.page_size = 4096;')
        db.execute('PRAGMA main.journal_mode = OFF;')
        db.execute('PRAGMA query_only = 1;')
        return db

@property
def table_names(self) -> List[str]:
    """
        Get the list of table names.
        :return: The list of table names.
        """
    self._assert_tables_attached()
    return self._table_names

@property
def tables(self) -> Dict[str, Table[Any]]:
    """
        Get the list of tables.
        :return: The list of tables.
        """
    self._assert_tables_attached()
    return self._tables

def get(self, table: str, token: str) -> Any:
    """
        Returns a record from table.
        :param table: Table name.
        :param token: Token of the record.
        :return: The record. See "templates.py" for details.
        """
    warnings.warn('deprecated', DeprecationWarning)
    self._assert_tables_attached()
    return getattr(self, table).get(token)

def field2token(self, table: str, field: str, query: str) -> List[str]:
    """
        Function returns a list of tokens given a table and field of that table.
        :param table: Table name.
        :param field: Field name, see "template.py" for details.
        :param query: The same type as the field.
        :return: Return a list of record tokens.
        """
    warnings.warn('deprecated', DeprecationWarning)
    self._assert_tables_attached()
    return [rec.token for rec in getattr(self, table).search(**{field: query})]

class MapLayer:
    """
    Wraps a map layer numpy array and provides methods for computing the distance to the foreground and
     determining if points are on the foreground.
    """

    def __init__(self, data: npt.NDArray[np.uint8], metadata: MapLayerMeta, joint_distance: Optional[npt.NDArray[np.float64]]=None, transform_matrix: Optional[npt.NDArray[np.float64]]=None) -> None:
        """
        Initiates MapLayer.
        :param data: Map layer as a binary numpy array with one channel.
        :param metadata: Map layer metadata.
        :param joint_distance:
            Same shape as `mask`.
            For every valid (row, col) in `joint_distance`, the *magnitude* of the value `joint_distance[row][col]` is
             the l2 distance on the ground plane from `mask[row][col]` to the nearest value in `mask` not equal to
              `mask[row][col]`.

            The *sign* of `joint_distance[row][col]` is positive if `mask[row][col] == 0`, and
             negative if `mask[row][col] == 1`.
        :param transform_matrix: Matrix for converting from physical coordinates to pixel coordinates.
        """
        if metadata.is_binary and np.amax(data) == 255:
            data = data.copy()
            data[data == 255] = 1
        self.data = data
        self.metadata = metadata
        self.nrows, self.ncols = data.shape[-2:]
        self.joint_distance = joint_distance
        self.foreground = 1
        self.background = 0
        if transform_matrix is None:
            transform_matrix = np.array([[1.0 / self.metadata.precision, 0, 0, 0], [0, -1.0 / self.metadata.precision, 0, self.nrows - 1], [0, 0, 1, 0], [0, 0, 0, 1]])
        self._transform_matrix = transform_matrix

    @property
    def precision(self) -> float:
        """
        Returns map resolution in meters per pixel. Typically set to 0.1, meaning that 10 pixels
            correspond to 1 meter.
        :return: Meters per pixel.
        """
        return self.metadata.precision

    def mask(self, dilation: float=0) -> npt.NDArray[np.float64]:
        """
        Returns full map layer content optionally including dilation.
        :param dilation: Max distance from the foreground. Should be not less than 0.
        :return: A full map layer content as a numpy array.
        """
        return self.crop(slice(0, self.nrows), slice(0, self.ncols), dilation)

    def crop(self, rows: slice, cols: slice, dilation: float=0) -> npt.NDArray[np.float64]:
        """
        Returns the map data in the rows and cols specified.
        :param rows: Range of rows to include in the crop.
        :param cols: Range of columns to include in the crop.
        :param dilation: If greater than 0, all pixels within dilation distance of the foreground will be made
         foreground pixels.
        :return: A full map layer content as a numpy array.
        """
        assert dilation >= 0, 'Negative dilation not supported.'
        if dilation == 0:
            return self.data[rows, cols]
        else:
            assert self.metadata.can_dilate
            return self.joint_distance[rows, cols] <= dilation

    @property
    def transform_matrix(self) -> npt.NDArray[np.float64]:
        """
        Matrix for transforming physical coordinates into pixel coordinates.
        Physical coordinates use bottom-left origin, while pixel coordinates use upper-left origin.
        :return: <np.ndarray: 4, 4>, the transform matrix.
        """
        return self._transform_matrix

    def to_pixel_coords(self, x: Any, y: Any) -> Tuple[npt.NDArray[np.int32], npt.NDArray[np.int32]]:
        """
        Gets the image coordinates given the x-y coordinates of points.
        :param x: Global x coordinates. Can be a scalar, list or a numpy array.
        :param y: Global y coordinates. Can be a scalar, list or a numpy array.
        :return: (px <np.int32: x.shape>, py <np.int32: y.shape>). Pixel coordinates in map.
        """
        x = np.atleast_1d(np.array(x))
        y = np.atleast_1d(np.array(y))
        assert x.shape == y.shape
        assert x.ndim == y.ndim == 1
        pts = np.stack([x, y, np.zeros(x.shape), np.ones(x.shape)])
        pixel_coords = np.round(np.dot(self.transform_matrix, pts)).astype(np.int32)
        return (pixel_coords[0, :], pixel_coords[1, :])

    def _is_in_bounds(self, px: npt.NDArray[np.int32], py: npt.NDArray[np.int32]) -> npt.NDArray[np.bool_]:
        """
        Determines whether points in pixel space are within the dimensions of this map.
        :param px: pixel coordinates.
        :param py: pixel coordinates.
        :return: <np.bool: px.shape> with True to indicate points in pixel space are within the dimensions of this map.
        """
        in_bounds = np.full(px.shape, True)
        in_bounds[px < 0] = False
        in_bounds[px >= self.ncols] = False
        in_bounds[py < 0] = False
        in_bounds[py >= self.nrows] = False
        return in_bounds

    def _dilated_distance(self, px: npt.NDArray[np.float64], py: npt.NDArray[np.float64], dilation: float) -> npt.NDArray[np.float64]:
        """
        Gives the distance to the dilated mask. A positive distance means outside the mask,
        a negative means inside. px and py are in pixel coordinates and should be in bound.
        :param px: pixel coordinates.
        :param py: pixel coordinates.
        :param dilation: dilation in meters.
        :return: The distance matrix to the dilated mask.
        """
        return self.joint_distance[py, px] - dilation

    def is_on_mask(self, x: Any, y: Any, dilation: float=0.0) -> npt.NDArray[np.bool_]:
        """
        Determines whether the points are on the mask (foreground of the layer).
        :param x: Global x coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Global y coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
            The drivable_area mask is dilated to include points which are within this distance from itself.
        :return: <np.bool: x.shape>, True if the points are on the mask, otherwise False.
        """
        px, py = self.to_pixel_coords(x, y)
        on_mask = np.zeros(px.size, dtype=bool)
        in_bounds = self._is_in_bounds(px, py)
        if dilation > 0:
            assert self.metadata.can_dilate
            on_mask[in_bounds] = self._dilated_distance(px[in_bounds], py[in_bounds], dilation) < 0
        else:
            on_mask[in_bounds] = self.data[py[in_bounds], px[in_bounds]] == self.foreground
        return on_mask

    def dist_to_mask(self, x: Any, y: Any, dilation: float=0.0) -> npt.NDArray[np.float32]:
        """
        Returns the physical distance of the closest 'mask boundary' to physical point (x, y).
        If (x, y) is *on* mask, returns distance to nearest point *off* mask as a *negative* value.
        If (x, y) is *off* mask, returns distance to nearest point *on* mask as a *positive* value.
        :param x: Physical x. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Physical y. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
             The drivable_area mask is dilated to include points which are within this distance from itself.
        :return: <np.float32: x.shape>, Distance to nearest mask boundary, or NAN if out of bounds in pixel space.
        """
        assert self.metadata.can_dilate
        px, py = self.to_pixel_coords(x, y)
        in_bounds = self._is_in_bounds(px, py)
        distance = np.full(px.shape, np.nan, dtype=np.float32)
        distance[in_bounds] = self._dilated_distance(px[in_bounds], py[in_bounds], dilation)
        return distance

def __init__(self, data: npt.NDArray[np.uint8], metadata: MapLayerMeta, joint_distance: Optional[npt.NDArray[np.float64]]=None, transform_matrix: Optional[npt.NDArray[np.float64]]=None) -> None:
    """
        Initiates MapLayer.
        :param data: Map layer as a binary numpy array with one channel.
        :param metadata: Map layer metadata.
        :param joint_distance:
            Same shape as `mask`.
            For every valid (row, col) in `joint_distance`, the *magnitude* of the value `joint_distance[row][col]` is
             the l2 distance on the ground plane from `mask[row][col]` to the nearest value in `mask` not equal to
              `mask[row][col]`.

            The *sign* of `joint_distance[row][col]` is positive if `mask[row][col] == 0`, and
             negative if `mask[row][col] == 1`.
        :param transform_matrix: Matrix for converting from physical coordinates to pixel coordinates.
        """
    if metadata.is_binary and np.amax(data) == 255:
        data = data.copy()
        data[data == 255] = 1
    self.data = data
    self.metadata = metadata
    self.nrows, self.ncols = data.shape[-2:]
    self.joint_distance = joint_distance
    self.foreground = 1
    self.background = 0
    if transform_matrix is None:
        transform_matrix = np.array([[1.0 / self.metadata.precision, 0, 0, 0], [0, -1.0 / self.metadata.precision, 0, self.nrows - 1], [0, 0, 1, 0], [0, 0, 0, 1]])
    self._transform_matrix = transform_matrix

def mask(self, dilation: float=0) -> npt.NDArray[np.float64]:
    """
        Returns full map layer content optionally including dilation.
        :param dilation: Max distance from the foreground. Should be not less than 0.
        :return: A full map layer content as a numpy array.
        """
    return self.crop(slice(0, self.nrows), slice(0, self.ncols), dilation)

def is_on_mask(self, x: Any, y: Any, dilation: float=0.0) -> npt.NDArray[np.bool_]:
    """
        Determines whether the points are on the mask (foreground of the layer).
        :param x: Global x coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Global y coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
            The drivable_area mask is dilated to include points which are within this distance from itself.
        :return: <np.bool: x.shape>, True if the points are on the mask, otherwise False.
        """
    px, py = self.to_pixel_coords(x, y)
    on_mask = np.zeros(px.size, dtype=bool)
    in_bounds = self._is_in_bounds(px, py)
    if dilation > 0:
        assert self.metadata.can_dilate
        on_mask[in_bounds] = self._dilated_distance(px[in_bounds], py[in_bounds], dilation) < 0
    else:
        on_mask[in_bounds] = self.data[py[in_bounds], px[in_bounds]] == self.foreground
    return on_mask

def dist_to_mask(self, x: Any, y: Any, dilation: float=0.0) -> npt.NDArray[np.float32]:
    """
        Returns the physical distance of the closest 'mask boundary' to physical point (x, y).
        If (x, y) is *on* mask, returns distance to nearest point *off* mask as a *negative* value.
        If (x, y) is *off* mask, returns distance to nearest point *on* mask as a *positive* value.
        :param x: Physical x. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Physical y. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
             The drivable_area mask is dilated to include points which are within this distance from itself.
        :return: <np.float32: x.shape>, Distance to nearest mask boundary, or NAN if out of bounds in pixel space.
        """
    assert self.metadata.can_dilate
    px, py = self.to_pixel_coords(x, y)
    in_bounds = self._is_in_bounds(px, py)
    distance = np.full(px.shape, np.nan, dtype=np.float32)
    distance[in_bounds] = self._dilated_distance(px[in_bounds], py[in_bounds], dilation)
    return distance

class NuPlanMapWrapper(NuPlanMap):
    """
    NuPlanMapWrapper database class for querying and retrieving information from the semantic maps.
    Before using this class please use the provided tutorial `maps_tutorials.ipynb`.
    """

    def __init__(self, maps_db: GPKGMapsDB, map_name: str) -> None:
        """
        Loads the layers, create reverse indices and shortcuts, initializes the explorer class.
        :param maps_db: MapsDB instance.
        :param map_name: Name of map location, e.g. "sg-one-north". See `maps_db.get_locations()`.
        """
        map_name = map_name.replace('.gpkg', '')
        super().__init__(maps_db, map_name)
        self.available_vector_layers = self._maps_db.vector_layer_names(map_name)
        self.available_raster_layers = self._maps_db.get_raster_layer_names(map_name)
        self.semantic_scale = 10.0
        self.vector_polygon_layers = ['lanes_polygons', 'intersections', 'generic_drivable_areas', 'walkways', 'carpark_areas', 'crosswalks', 'lane_group_connectors', 'lane_groups_polygons', 'road_segments', 'stop_polygons']
        self.vector_line_layers = ['lane_connectors', 'boundaries']
        self.vector_point_layers = ['traffic_lights']
        self.vector_layers = self.vector_polygon_layers + self.vector_line_layers + self.vector_point_layers

    def load_vector_layer(self, layer_name: str) -> gpd.geodataframe:
        """
        Loads Vector Layer.
        :param layer_name: Name of Layer.
        :return: Returns vector layer as a GeoDataFrame object.
        """
        assert layer_name in self.available_vector_layers, f'{layer_name} is not a vector layer'
        return self._load_vector_map_layer(layer_name)

    def load_raster_layer_as_numpy(self, layer_name: str) -> npt.NDArray[np.uint8]:
        """
        Loads raster layer as numpy.
        :param layer_name: Name of Layer.
        :return: Returns raster layer as numpy array.
        """
        raster_layer: RasterLayer = self._load_raster_layer(layer_name)
        return raster_layer.data

    def get_map_dimension(self) -> Tuple[int, int]:
        """
        Gets the dimension of the map.
        :return: The dimension of the map.
        """
        map_dims = self._maps_db._map_dimensions[self._map_name]
        return (int(map_dims[0]), int(map_dims[1]))

    def get_map_aspect_ratio(self) -> float:
        """
        Gets the aspect ratio of the map.
        :return: Aspect ratio of the map.
        """
        map_dims = self.get_map_dimension()
        map_aspect_ratio = map_dims[1] / map_dims[0]
        return map_aspect_ratio

    def get_bounds(self, layer_name: str, tokens: Optional[List[str]]=None) -> Tuple[float, float, float, float]:
        """
        Gets the bounds of the layer that corresponding to the given tokens. If no tokens are provided the bounds of
        the whole layer are returned.
        :param layer_name: Name of the layer that we are interested in.
        :param tokens: List of Tokens for layer.
        :return: min_x, min_y, max_x, max_y of the representation.
        """
        if layer_name in self.vector_layers:
            records = self.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        xmin, ymin = (float('inf'), float('inf'))
        xmax, ymax = (float('-inf'), float('-inf'))
        for i in range(len(records)):
            fid = records['fid'][i]
            if tokens is not None:
                if fid not in tokens:
                    continue
            polygons = records['geometry'][i]
            bounds = polygons.bounds
            xmin = min(xmin, bounds[0])
            ymin = min(ymin, bounds[1])
            xmax = max(xmax, bounds[2])
            ymax = max(ymax, bounds[3])
        return (xmin, ymin, xmax, ymax)

    @staticmethod
    def _is_line_record_in_patch(line_coords: LineString, box_coords: List[float], mode: str='within') -> bool:
        """
        Query whether a particular polygon record is in a rectangular patch.
        :param line_coords: Line Coordinates.
        :param box_coords: The rectangular patch coordinates (x_min, y_min, x_max, y_max).
        :param mode: "intersect" means it will return True if the line object intersects the patch and False
        otherwise, "within" will return True if the line object is within the patch and False otherwise.
        :return: Boolean value on whether a particular polygon record intersects or is within a particular patch.
        """
        line_coords = np.asarray(line_coords.coords)
        if len(line_coords) == 0:
            return False
        x_min, y_min, x_max, y_max = box_coords
        cond_x = np.logical_and(line_coords[:, 0] < x_max, line_coords[:, 0] > x_min)
        cond_y = np.logical_and(line_coords[:, 1] < y_max, line_coords[:, 1] > y_min)
        cond = np.logical_and(cond_x, cond_y)
        if mode == 'intersect':
            return np.any(cond)
        elif mode == 'within':
            return np.all(cond)
        else:
            raise ValueError("Only 'intersect' and 'within' are supported.")

    @staticmethod
    def _is_polygon_record_in_patch(polygon_coords: Polygon, box_coords: List[float], mode: str='within') -> bool:
        """
        Query whether a particular polygon record is in a rectangular patch.
        :param polygon_coords: Polygon Coordinates.
        :param box_coords: The rectangular patch coordinates (x_min, y_min, x_max, y_max).
        :param mode: "intersect" means it will return True if the polygon object intersects the patch and False
        otherwise, "within" will return True if the polygon object is within the patch and False otherwise.
        :return: Boolean value on whether a particular polygon record intersects or is within a particular patch.
        """
        x_min, y_min, x_max, y_max = box_coords
        rectangular_patch = box(x_min, y_min, x_max, y_max)
        if mode == 'intersect':
            return polygon_coords.intersects(rectangular_patch)
        elif mode == 'within':
            return polygon_coords.within(rectangular_patch)
        else:
            raise ValueError("Only 'intersect' and 'within' are supported.")

    @staticmethod
    def get_patch_coord(patch_box: Tuple[float, float, float, float], patch_angle: float=0.0) -> Polygon:
        """
        Converts patch_box to shapely Polygon coordinates.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
        :return: Box Polygon for patch_box.
        """
        patch_x, patch_y, patch_h, patch_w = patch_box
        x_min = patch_x - patch_w / 2.0
        y_min = patch_y - patch_h / 2.0
        x_max = patch_x + patch_w / 2.0
        y_max = patch_y + patch_h / 2.0
        patch = box(x_min, y_min, x_max, y_max)
        patch = affinity.rotate(patch, patch_angle, origin=(patch_x, patch_y), use_radians=False)
        return patch

    def layers_on_point(self, x: float, y: float, layer_names: Optional[List[str]]=None) -> Dict[str, List[str]]:
        """
        Returns all the polygonal layers that a particular point is on.
        :param x: x coordinate of the point of interest.
        :param y: y coordinate of the point of interest.
        :param layer_names: The names of the layers to search for.
        :return: All the polygonal layers that a particular point is on.
        """
        if layer_names is None:
            layer_names = self.vector_polygon_layers
        layer_points = dict()
        for layer_name in layer_names:
            layer_points.update({layer_name: self.records_on_point(x, y, layer_name)})
        return layer_points

    def records_on_point(self, x: float, y: float, layer_name: str) -> List[str]:
        """
        Query what record of a layer a particular point is on.
        :param x: x coordinate of the point of interest.
        :param y: y coordinate of the point of interest.
        :param layer_name: The polygonal layer name that we are interested in.
        :return: The tokens of a layer at particular point.
        """
        if layer_name not in self.vector_polygon_layers:
            raise ValueError('{} is not a polygon layer'.format(layer_name))
        point = Point(x, y)
        if layer_name in self.vector_layers:
            records = self.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        fids = []
        for i in range(len(records)):
            polygon = records['geometry'][i]
            if point.within(polygon):
                fids.append(records['fid'][i])
            else:
                pass
        return fids

    def get_records_in_patch(self, box_coords: List[float], layer_names: Optional[List[str]]=None, mode: str='intersect') -> Dict[str, List[str]]:
        """
        Gets all the record token that intersects or within a particular rectangular patch.
        :param box_coords: The rectangular patch coordinates (x_min, y_min, x_max, y_max).
        :param layer_names: Names of the layers that we want to retrieve in a particular patch.
        :param mode: "intersect" will return all records that intersects the patch,
            "within" will return all records that are within the patch.
        :return: Dictionary of layer_name - tokens pairs.
        """
        if mode not in ['intersect', 'within']:
            raise ValueError("Mode {} is not valid, choice=('intersect', 'within')".format(mode))
        if layer_names is None:
            layer_names = self.vector_layers
        records_in_patch = dict()
        for layer_name in layer_names:
            layer_records = []
            if layer_name in self.vector_layers:
                records = self.load_vector_layer(layer_name)
            else:
                raise ValueError('{} is not a valid layer'.format(layer_name))
            for i in range(len(records)):
                ann_points = records['geometry'][i]
                token = records['fid'][i]
                if layer_name in self.vector_polygon_layers:
                    if self._is_polygon_record_in_patch(ann_points, box_coords, mode):
                        layer_records.append(token)
                elif layer_name in self.vector_line_layers:
                    if self._is_line_record_in_patch(ann_points, box_coords, mode):
                        layer_records.append(token)
            records_in_patch.update({layer_name: layer_records})
        return records_in_patch

    def get_layer_polygon(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_name: str) -> List[Polygon]:
        """
        Retrieves the polygons of a particular layer within the specified patch.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
        :param layer_name: name of map layer to be extracted.
        :return: List of Polygon in a patch box.
        """
        patch_x = patch_box[0]
        patch_y = patch_box[1]
        patch = self.get_patch_coord(patch_box, patch_angle)
        polygon_list = []
        if layer_name in self.vector_layers:
            records = self.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        for i in range(len(records)):
            polygons = records['geometry'][i]
            new_polygon = polygons.intersection(patch)
            if not new_polygon.is_empty:
                new_polygon = affinity.rotate(new_polygon, -patch_angle, origin=(patch_x, patch_y), use_radians=False)
                new_polygon = affinity.affine_transform(new_polygon, [1.0, 0.0, 0.0, 1.0, -patch_x, -patch_y])
                if new_polygon.geom_type == 'Polygon':
                    new_polygon = MultiPolygon([new_polygon])
                polygon_list.append(new_polygon)
        return polygon_list

    def get_layer_line(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_name: str) -> Optional[List[LineString]]:
        """
        Retrieve the lines of a particular layer within the specified patch.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
        :param layer_name: Name of map layer to be converted to binary map mask patch.
        :return: List of LineString in a patch box.
        """
        patch_x = patch_box[0]
        patch_y = patch_box[1]
        patch = self.get_patch_coord(patch_box, patch_angle)
        line_list = []
        if layer_name in self.vector_layers:
            records = self.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        for i in range(len(records)):
            line = records['geometry'][i]
            if line.is_empty:
                continue
            new_line = line.intersection(patch)
            if not new_line.is_empty:
                new_line = affinity.rotate(new_line, -patch_angle, origin=(patch_x, patch_y), use_radians=False)
                new_line = affinity.affine_transform(new_line, [1.0, 0.0, 0.0, 1.0, -patch_x, -patch_y])
                line_list.append(new_line)
        return line_list

def get_map_aspect_ratio(self) -> float:
    """
        Gets the aspect ratio of the map.
        :return: Aspect ratio of the map.
        """
    map_dims = self.get_map_dimension()
    map_aspect_ratio = map_dims[1] / map_dims[0]
    return map_aspect_ratio

def get_records_in_patch(self, box_coords: List[float], layer_names: Optional[List[str]]=None, mode: str='intersect') -> Dict[str, List[str]]:
    """
        Gets all the record token that intersects or within a particular rectangular patch.
        :param box_coords: The rectangular patch coordinates (x_min, y_min, x_max, y_max).
        :param layer_names: Names of the layers that we want to retrieve in a particular patch.
        :param mode: "intersect" will return all records that intersects the patch,
            "within" will return all records that are within the patch.
        :return: Dictionary of layer_name - tokens pairs.
        """
    if mode not in ['intersect', 'within']:
        raise ValueError("Mode {} is not valid, choice=('intersect', 'within')".format(mode))
    if layer_names is None:
        layer_names = self.vector_layers
    records_in_patch = dict()
    for layer_name in layer_names:
        layer_records = []
        if layer_name in self.vector_layers:
            records = self.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        for i in range(len(records)):
            ann_points = records['geometry'][i]
            token = records['fid'][i]
            if layer_name in self.vector_polygon_layers:
                if self._is_polygon_record_in_patch(ann_points, box_coords, mode):
                    layer_records.append(token)
            elif layer_name in self.vector_line_layers:
                if self._is_line_record_in_patch(ann_points, box_coords, mode):
                    layer_records.append(token)
        records_in_patch.update({layer_name: layer_records})
    return records_in_patch

class NuPlanMapExplorer:
    """Helper class to explore the nuPlan map data."""

    def __init__(self, map_api: NuPlanMapWrapper, color_map: Optional[Dict[str, str]]=None) -> None:
        """
        Constructor.
        :param map_api: A NuPlanMapWrapper instance.
        :param color_map: Color Map for each segment.
        """
        self.map_api = map_api
        if color_map is None:
            self.color_map = dict(generic_drivable_areas='#a6cee3', road_segments='#1f78b4', lanes_polygons='#b2df8a', ped_crossings='#fb9a99', walkways='#e31a1c', carpark_areas='#ff7f00', traffic_lights='#7e772e', intersections='#703642', lane_group_connectors='#cab2d6', stop_polygons='#800080', speed_bumps='#DC7633', lane_connectors='#6a3d9a', lane_groups_polygons='#85929E', boundaries='#839192', crosswalks='#F6DDCC')
        else:
            self.color_map = color_map

    def render_map_mask(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_names: List[str], output_size: Tuple[int, int], figsize: Tuple[int, int], n_row: int=2) -> Tuple[Figure, List[Axes]]:
        """
        Render map mask of the patch specified by patch_box and patch_angle.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
        :param layer_names: A list of layer names to be rendered.
        :param output_size: Size of the output mask (h, w).
        :param figsize: Size of the figure.
        :param n_row: Number of rows with plots.
        :return: The matplotlib figure and a list of axes of the rendered layers.
        """
        map_dims = self.map_api.get_map_dimension()
        if output_size is None:
            output_size = (int(map_dims[1]), int(map_dims[0]))
        map_mask = self.get_map_mask(patch_box, patch_angle, layer_names, output_size)
        fig = plt.figure(figsize=figsize)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, output_size[1])
        ax.set_ylim(0, output_size[0])
        n_col = map_mask.shape[0]
        gs = gridspec.GridSpec(n_row, n_col)
        gs.update(wspace=0.025, hspace=0.05)
        for i in range(len(map_mask)):
            r = i // n_col
            c = i - r * n_col
            subax = plt.subplot(gs[r, c])
            subax.imshow(map_mask[i], origin='lower')
            subax.text(output_size[0] * 0.5, output_size[1] * 1.1, layer_names[i])
            subax.grid(False)
        return (fig, fig.axes)

    def render_layers(self, layer_names: List[str], alpha: float, tokens: Optional[Dict[str, List[str]]]=None) -> Tuple[Figure, Axes]:
        """
        Render a list of layers.
        :param layer_names: A list of layer names.
        :param alpha: The opacity of each layer.
        :param tokens: Dict of tokens for each layer in layer_name.
        :return: The matplotlib figure and axes of the rendered layers.
        """
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1 / self.map_api.get_map_aspect_ratio()])
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            xmin, ymin = (float('inf'), float('inf'))
            xmax, ymax = (float('-inf'), float('-inf'))
            for layer_name in layer_names:
                if tokens is None:
                    bounds = self.map_api.get_bounds(layer_name)
                else:
                    bounds = self.map_api.get_bounds(layer_name, tokens[layer_name])
                xmin = min(xmin, bounds[0])
                ymin = min(ymin, bounds[1])
                xmax = max(xmax, bounds[2])
                ymax = max(ymax, bounds[3])
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            layer_names = list(set(layer_names))
            for layer_name in layer_names:
                if tokens is None:
                    self._render_layer(ax, layer_name, alpha)
                else:
                    self._render_layer(ax, layer_name, alpha, tokens[layer_name])
            ax.legend()
            return (fig, ax)

    def _render_layer(self, ax: Axes, layer_name: str, alpha: float, tokens: Optional[List[str]]=None) -> None:
        """
        Wrapper method that renders individual layers on an axis.
        :param ax: The matplotlib axes where the layer will get rendered.
        :param layer_name: Name of the layer that we are interested in.
        :param alpha: The opacity of the layer to be rendered.
        :param tokens: The list of tokens of layer to render.
        """
        if layer_name in self.map_api.vector_polygon_layers:
            self._render_polygon_layer(ax, layer_name, alpha, tokens)
        elif layer_name in self.map_api.vector_line_layers or layer_name in self.map_api.vector_point_layers:
            self._render_line_layer(ax, layer_name, alpha, tokens)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))

    def _render_polygon_layer(self, ax: Axes, layer_name: str, alpha: float, tokens: Optional[List[str]]=None) -> None:
        """
        Renders an individual polygon layer on an axis.
        :param ax: The matplotlib axes where the layer will get rendered.
        :param layer_name: Name of the layer that we are interested in.
        :param alpha: The opacity of the layer to be rendered.
        :param tokens: The list of tokens of layer to render.
        """
        if layer_name in self.map_api.vector_layers:
            records = self.map_api.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        for i in range(len(records)):
            polygons = records['geometry'][i]
            if tokens is not None:
                fid = records['fid'][i]
                if fid not in tokens:
                    continue
            xs, ys = polygons.exterior.xy
            ax.fill(xs, ys, alpha=alpha, fc=self.color_map[layer_name], ec='none')

    def _render_line_layer(self, ax: Axes, layer_name: str, alpha: float, tokens: Optional[List[str]]=None) -> None:
        """
        Renders an individual line layer on an axis.
        :param ax: The matplotlib axes where the layer will get rendered.
        :param layer_name: Name of the layer that we are interested in.
        :param alpha: The opacity of the layer to be rendered.
        :param tokens: List of tokens of layer to render.
        """
        if layer_name in self.map_api.vector_layers:
            records = self.map_api.load_vector_layer(layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))
        first_time = True
        for i in range(len(records)):
            line = records['geometry'][i]
            if tokens is not None:
                fid = records['fid'][i]
                if fid not in tokens:
                    continue
            if first_time:
                label = layer_name
                first_time = False
            else:
                label = None
            if line.is_empty:
                continue
            xs, ys = line.xy
            if layer_name in self.map_api.vector_point_layers:
                ax.add_patch(Circle((xs[0], ys[0]), color=self.color_map[layer_name], label=label))
            else:
                ax.plot(xs, ys, color=self.color_map[layer_name], alpha=alpha, label=label)

    def map_geom_to_mask(self, map_geom: List[Tuple[str, List[Geometry]]], local_box: Tuple[float, float, float, float], output_size: Tuple[int, int]) -> npt.NDArray[np.uint8]:
        """
        Return list of map mask layers of the specified patch.
        :param map_geom: List of layer names and their corresponding geometries.
        :param local_box: The local patch box defined as (x_center, y_center, height, width), where typically
            x_center = y_center = 0.
        :param output_size: Size of the output mask (h, w).
        :return: Stacked numpy array of size [c x h x w] with c channels and the same height/width as the canvas.
        """
        map_mask = []
        for layer_name, layer_geom in map_geom:
            layer_mask = self._layer_geom_to_mask(layer_name, layer_geom, local_box, output_size)
            if layer_mask is not None:
                map_mask.append(layer_mask)
        return np.array(map_mask)

    def get_map_mask(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_names: List[str], output_size: Tuple[int, int]) -> npt.NDArray[np.uint8]:
        """
        Returns list of map mask layers of the specified patch.
        :param patch_box: Patch box defined as [x_center, y_center, height, width]. If None, returns the entire map.
        :param patch_angle: Patch orientation in degrees. North-facing corresponds to 0.
        :param layer_names: A list of layer names to be extracted.
        :param output_size: Size of the output mask (h, w).
        :return: Stacked numpy array of size [c x h x w] with c channels and the same width/height as the canvas.
        """
        map_geom = self.get_map_geom(patch_box, patch_angle, layer_names)
        local_box = (0.0, 0.0, patch_box[2], patch_box[3])
        map_mask = self.map_geom_to_mask(map_geom, local_box, output_size)
        assert np.all(map_mask.shape[1:] == output_size)
        return map_mask

    def get_map_geom(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_names: List[str]) -> List[Tuple[str, List[Geometry]]]:
        """
        Returns a list of geometries in the specified patch_box.
        These are unscaled, but aligned with the patch angle.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
                            North-facing corresponds to 0.
        :param layer_names: A list of layer names to be extracted.
        :return: List of layer names and their corresponding geometries.
        """
        map_geom = []
        for layer_name in layer_names:
            layer_geom = self._get_layer_geom(patch_box, patch_angle, layer_name)
            if layer_geom is None:
                continue
            map_geom.append((layer_name, layer_geom))
        return map_geom

    def _layer_geom_to_mask(self, layer_name: str, layer_geom: List[Geometry], local_box: Tuple[float, float, float, float], output_size: Tuple[int, int]) -> npt.NDArray[np.uint8]:
        """
        Wrapper method that gets the mask for each layer's geometries.
        :param layer_name: The name of the layer for which we get the masks.
        :param layer_geom: List of the geometries of the layer specified in layer_name.
        :param local_box: The local patch box defined as (x_center, y_center, height, width), where typically
            x_center = y_center = 0.
        :param output_size: Size of the output mask (h, w).
        :return: Binary map mask patch in a canvas size.
        """
        if layer_name in self.map_api.vector_polygon_layers:
            return self._polygon_geom_to_mask(layer_geom, local_box, output_size)
        elif layer_name in self.map_api.vector_line_layers:
            return self._line_geom_to_mask(layer_geom, local_box, layer_name, output_size)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))

    def _polygon_geom_to_mask(self, layer_geom: List[LineString], local_box: Tuple[float, float, float, float], output_size: Tuple[int, int]) -> npt.NDArray[np.uint8]:
        """
        Convert polygon inside patch to binary mask and return the map patch.
        :param layer_geom: list of polygons for each map layer.
        :param local_box: The local patch box defined as (x_center, y_center, height, width), where typically
            x_center = y_center = 0.
        :param output_size: Size of the output mask (h, w).
        :return: Binary map mask patch with the size canvas_size.
        """
        patch_x, patch_y, patch_h, patch_w = local_box
        patch = self.map_api.get_patch_coord(local_box)
        output_h = output_size[0]
        output_w = output_size[1]
        scale_height = output_h / patch_h
        scale_width = output_w / patch_w
        trans_x = -patch_x + patch_w / 2.0
        trans_y = -patch_y + patch_h / 2.0
        map_mask = np.zeros(output_size, np.uint8)
        for polygon in layer_geom:
            new_polygon = polygon.intersection(patch)
            if not new_polygon.is_empty:
                new_polygon = affinity.affine_transform(new_polygon, [1.0, 0.0, 0.0, 1.0, trans_x, trans_y])
                new_polygon = affinity.scale(new_polygon, xfact=scale_width, yfact=scale_height, origin=(0, 0))
                if new_polygon.geom_type == 'Polygon':
                    new_polygon = MultiPolygon([new_polygon])
                map_mask = self.mask_for_polygons(new_polygon, map_mask)
        return map_mask

    def _line_geom_to_mask(self, layer_geom: List[LineString], local_box: Tuple[float, float, float, float], layer_name: str, output_size: Tuple[int, int]) -> Optional[npt.NDArray[np.uint8]]:
        """
        Convert line inside patch to binary mask and return the map patch.
        :param layer_geom: list of LineStrings for each map layer.
        :param local_box: The local patch box defined as (x_center, y_center, height, width), where typically
            x_center = y_center = 0.
        :param layer_name: name of map layer to be converted to binary map mask patch.
        :param output_size: Size of the output mask (h, w).
        :return: Binary map mask patch in a canvas size.
        """
        patch_x, patch_y, patch_h, patch_w = local_box
        patch = self.map_api.get_patch_coord(local_box)
        output_h = output_size[0]
        output_w = output_size[1]
        scale_height = output_h / patch_h
        scale_width = output_w / patch_w
        trans_x = -patch_x + patch_w / 2.0
        trans_y = -patch_y + patch_h / 2.0
        map_mask = np.zeros(output_size, np.uint8)
        if layer_name == 'traffic_light':
            return None
        for line in layer_geom:
            new_line = line.intersection(patch)
            if not new_line.is_empty:
                new_line = affinity.affine_transform(new_line, [1.0, 0.0, 0.0, 1.0, trans_x, trans_y])
                new_line = affinity.scale(new_line, xfact=scale_width, yfact=scale_height, origin=(0, 0))
                map_mask = self.mask_for_lines(new_line, map_mask)
        return map_mask

    def _get_layer_geom(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_name: str) -> List[Geometry]:
        """
        Wrapper method that gets the geometries for each layer.
        :param patch_box: Patch box defined as [x_center, y_center, height, width].
        :param patch_angle: Patch orientation in degrees.
        :param layer_name: Name of map layer to be converted to binary map mask patch.
        :return: List of geometries for the given layer.
        """
        if layer_name in self.map_api.vector_polygon_layers:
            return self.map_api.get_layer_polygon(patch_box, patch_angle, layer_name)
        elif layer_name in self.map_api.vector_line_layers:
            return self.map_api.get_layer_line(patch_box, patch_angle, layer_name)
        else:
            raise ValueError('{} is not a valid layer'.format(layer_name))

    def get_nearby_roads(self, x: float, y: float) -> Dict[str, List[str]]:
        """
        Gets the possible next roads from a point of interest.
        Returns road_segment, road_block and lane.
        :param x: x coordinate of the point of interest.
        :param y: y coordinate of the point of interest.
        :return: Dictionary of layer_name - tokens pairs.
        """
        road_layers = ['lanes_polygons', 'road_segments']
        layers_tokens = self.map_api.layers_on_point(x, y, road_layers)
        assert layers_tokens is not None, 'Error: No suitable layer in the specified point location!'
        xmin, ymin = (float('inf'), float('inf'))
        xmax, ymax = (float('-inf'), float('-inf'))
        for road_layer in road_layers:
            bounds = self.map_api.get_bounds(road_layer, layers_tokens[road_layer])
            xmin = min(xmin, bounds[0])
            ymin = min(ymin, bounds[1])
            xmax = max(xmax, bounds[2])
            ymax = max(ymax, bounds[3])
        box_coords = [xmin, ymin, xmax, ymax]
        intersect = self.map_api.get_records_in_patch(box_coords, road_layers, mode='intersect')
        return intersect

    def render_nearby_roads(self, x: float, y: float, alpha: float=0.5) -> Tuple[Figure, Axes]:
        """
        Renders the possible next roads from a point of interest.
        :param x: x coordinate of the point of interest.
        :param y: y coordinate of the point of interest.
        :param alpha: The opacity of each layer that gets rendered.
        """
        nearby_roads = self.get_nearby_roads(x, y)
        layer_names = []
        for layer_name, layer_tokens in nearby_roads.items():
            if len(layer_tokens) > 0:
                layer_names.append(layer_name)
        fig, ax = self.render_layers(layer_names, alpha, tokens=nearby_roads)
        ax.plot(x, y, 'x', markersize=12, color='red')
        return (fig, ax)

    @staticmethod
    def mask_for_lines(lines: LineString, mask: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """
        Convert a Shapely LineString back to an image mask ndarray.
        :param lines: List of shapely LineStrings to be converted to a numpy array.
        :param mask: Canvas where mask will be generated.
        :return: Numpy ndarray line mask.
        """
        if lines.geom_type == 'MultiLineString':
            for line in lines:
                coords = np.array(line.coords, np.int32)
                coords = coords.reshape((-1, 2))
                cv2.polylines(mask, [coords], False, 1, 2)
        else:
            coords = np.array(lines.coords, np.int32)
            coords = coords.reshape((-1, 2))
            cv2.polylines(mask, [coords], False, 1, 2)
        return mask

    @staticmethod
    def mask_for_polygons(polygons: MultiPolygon, mask: npt.NDArray[np.uint8]) -> npt.NDArray[np.uint8]:
        """
        Convert a polygon or multipolygon list to an image mask ndarray.
        :param polygons: List of Shapely polygons to be converted to numpy array.
        :param mask: Canvas where mask will be generated.
        :return: Numpy ndarray polygon mask.
        """
        if not polygons:
            return mask

        def int_coords(x: Any) -> npt.NDArray[np.int32]:
            """
            Function to round and convert to int.
            :param x: Input data, in any form that can be converted to an array.
            :return: The converted array-like int.
            """
            return np.array(x).round().astype(np.int32)
        exteriors = [int_coords(poly.exterior.coords) for poly in polygons.geoms]
        interiors = [int_coords(pi.coords) for poly in polygons.geoms for pi in poly.interiors]
        cv2.fillPoly(mask, exteriors, 1)
        cv2.fillPoly(mask, interiors, 0)
        return mask

def get_map_mask(self, patch_box: Tuple[float, float, float, float], patch_angle: float, layer_names: List[str], output_size: Tuple[int, int]) -> npt.NDArray[np.uint8]:
    """
        Returns list of map mask layers of the specified patch.
        :param patch_box: Patch box defined as [x_center, y_center, height, width]. If None, returns the entire map.
        :param patch_angle: Patch orientation in degrees. North-facing corresponds to 0.
        :param layer_names: A list of layer names to be extracted.
        :param output_size: Size of the output mask (h, w).
        :return: Stacked numpy array of size [c x h x w] with c channels and the same width/height as the canvas.
        """
    map_geom = self.get_map_geom(patch_box, patch_angle, layer_names)
    local_box = (0.0, 0.0, patch_box[2], patch_box[3])
    map_mask = self.map_geom_to_mask(map_geom, local_box, output_size)
    assert np.all(map_mask.shape[1:] == output_size)
    return map_mask

def get_nearby_roads(self, x: float, y: float) -> Dict[str, List[str]]:
    """
        Gets the possible next roads from a point of interest.
        Returns road_segment, road_block and lane.
        :param x: x coordinate of the point of interest.
        :param y: y coordinate of the point of interest.
        :return: Dictionary of layer_name - tokens pairs.
        """
    road_layers = ['lanes_polygons', 'road_segments']
    layers_tokens = self.map_api.layers_on_point(x, y, road_layers)
    assert layers_tokens is not None, 'Error: No suitable layer in the specified point location!'
    xmin, ymin = (float('inf'), float('inf'))
    xmax, ymax = (float('-inf'), float('-inf'))
    for road_layer in road_layers:
        bounds = self.map_api.get_bounds(road_layer, layers_tokens[road_layer])
        xmin = min(xmin, bounds[0])
        ymin = min(ymin, bounds[1])
        xmax = max(xmax, bounds[2])
        ymax = max(ymax, bounds[3])
    box_coords = [xmin, ymin, xmax, ymax]
    intersect = self.map_api.get_records_in_patch(box_coords, road_layers, mode='intersect')
    return intersect

class TestMapApi(unittest.TestCase):
    """Test NuPlanMapWrapper class."""

    def setUp(self) -> None:
        """
        Initialize the map for each location.
        """
        self.maps_db = get_test_maps_db()
        self.locations = ['sg-one-north', 'us-ma-boston', 'us-nv-las-vegas-strip', 'us-pa-pittsburgh-hazelwood']
        self.available_locations = self.maps_db.get_locations()
        self.nuplan_maps = dict()
        for location in self.available_locations:
            self.nuplan_maps[location] = NuPlanMapWrapper(maps_db=self.maps_db, map_name=location)

    def test_version_names(self) -> None:
        """Tests the locations map version are correct."""
        assert len(self.maps_db.version_names) == len(self.available_locations), 'Incorrect number of version names'

    def test_locations(self) -> None:
        """
        Checks if maps for all locations are available.
        """
        assert len(self.locations) == len(self.available_locations), 'Incorrect number of locations'
        assert sorted(self.locations) == sorted(self.available_locations), 'Missing Locations'

    def test_patch_coord(self) -> None:
        """
        Checks the function to get patch coordinates without rotation.
        """
        path_center = [0, 0]
        path_dimension = [10, 10]
        polygon_coords = self.nuplan_maps[self.locations[0]].get_patch_coord((path_center[0], path_center[1], path_dimension[0], path_dimension[1]), 0.0)
        expected_polygon_coords = Polygon([[5, -5], [5, 5], [-5, 5], [-5, -5], [5, -5]])
        self.assertEqual(polygon_coords, expected_polygon_coords)

    def test_patch_coord_rotated(self) -> None:
        """
        Checks the function to get patch coordinates with rotation.
        """
        path_center = [0, 0]
        path_dimension = [10, 20]
        polygon_coords = self.nuplan_maps[self.locations[0]].get_patch_coord((path_center[0], path_center[1], path_dimension[0], path_dimension[1]), 90.0)
        expected_polygon_coords = Polygon([[5, 10], [-5, 10], [-5, -10], [5, -10], [5, 10]])
        self.assertEqual(polygon_coords, expected_polygon_coords)

    def test_vector_dimensions(self) -> None:
        """
        Checks dimensions of vector layer. It must be less than or equal to size of map.
        """
        for location in self.locations:
            vector_layer_bounds = self.nuplan_maps[location].get_bounds('lanes_polygons')
            map_shape = self.nuplan_maps[location].get_map_dimension()
            self.assertLess(vector_layer_bounds[0], vector_layer_bounds[2])
            self.assertLess(vector_layer_bounds[1], vector_layer_bounds[3])
            self.assertLess(vector_layer_bounds[2] - vector_layer_bounds[0], map_shape[0])
            self.assertLess(vector_layer_bounds[3] - vector_layer_bounds[1], map_shape[1])

    def test_line_in_patch(self) -> None:
        """
        Checks if the line inside patch.
        """
        line_coords = LineString([(1.0, 1.0), (10.0, 10.0)])
        box_coords = [0.0, 0.0, 11.0, 11.0]
        self.assertTrue(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords))
        box_coords = [0.0, 0.0, 8.0, 8.0]
        self.assertFalse(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords))

    def test_line_intersects_patch(self) -> None:
        """
        Checks if line intersects the patch.
        """
        line_coords = LineString([(0.0, 0.0), (10.0, 10.0)])
        box_coords = [0.0, 0.0, 11.0, 11.0]
        self.assertTrue(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords, 'intersect'))
        box_coords = [11.0, 11.0, 16.0, 16.0]
        self.assertFalse(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords, 'intersect'))

    def test_polygon_in_patch(self) -> None:
        """
        Checks if polygon is inside patch.
        """
        polygon_coords = Polygon([(1.0, 1.0), (1.0, 10.0), (10.0, 10.0), (1.0, 1.0)])
        box_coords = [0.0, 0.0, 11.0, 11.0]
        self.assertTrue(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords))
        box_coords = [0.0, 0.0, 8.0, 8.0]
        self.assertFalse(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords))

    def test_polygon_intersects_patch(self) -> None:
        """
        Check if polygon intersects patch.
        """
        polygon_coords = Polygon([(1.0, 1.0), (1.0, 10.0), (10.0, 10.0), (1.0, 1.0)])
        box_coords = [1.0, 1.0, 11.0, 11.0]
        self.assertTrue(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords, 'intersect'))
        box_coords = [12.0, 14.0, 15.0, 15.0]
        self.assertFalse(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords, 'intersect'))

    def test_mask_for_polygons(self) -> None:
        """
        Checks the mask generated using polygons.
        """
        polygon_coords = MultiPolygon([Polygon([(0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0)])])
        mask = np.zeros((10, 10))
        map_explorer = NuPlanMapExplorer(self.nuplan_maps[self.locations[0]])
        predicted_mask = map_explorer.mask_for_polygons(polygon_coords, mask)
        expected_mask = np.zeros((10, 10))
        expected_mask[0:3, 0:3] = 1
        np.testing.assert_array_equal(predicted_mask, expected_mask)

    def test_mask_for_lines(self) -> None:
        """Checks the mask generated using lines."""
        line_coords = LineString([(0, 0), (0, 5), (5, 5), (5, 0), (0, 0)])
        mask = np.zeros((10, 10))
        map_explorer = NuPlanMapExplorer(self.nuplan_maps[self.locations[0]])
        predicted_mask = map_explorer.mask_for_lines(line_coords, mask)
        expected_mask = np.zeros((10, 10))
        expected_mask[0:7, 0:7] = 1
        expected_mask[2:4, 2:4] = 0
        expected_mask[6, 6] = 0
        np.testing.assert_array_equal(predicted_mask, expected_mask)

    def test_layers_on_points(self) -> None:
        """
        Checks if returns correct layers given a point.
        """
        with self.assertRaises(Exception):
            self.nuplan_maps[self.locations[3]].layers_on_point(0, 0, ['lane_connectors'])
        self.assertFalse(self.nuplan_maps[self.locations[3]].layers_on_point(0, 0, []))
        layer = self.nuplan_maps[self.locations[2]].layers_on_point(664777.776, 3999698.364, ['lanes_polygons'])
        self.assertEqual(layer['lanes_polygons'], ['63085'])
        layer = self.nuplan_maps[self.locations[3]].layers_on_point(87488.0, 43600.0, ['lanes_polygons'])
        self.assertFalse(layer['lanes_polygons'])

    def test_get_records_in_patch(self) -> None:
        """
        Checks the function of getting all the record token that intersects or within a particular rectangular patch.
        """
        with self.assertRaises(Exception):
            self.nuplan_maps[self.locations[3]].get_records_in_patch([0, 0, 0, 0], ['drivable_area'])
        tokens = self.nuplan_maps[self.locations[3]].get_records_in_patch([0, 0, 0, 0], ['lanes_polygons'])
        self.assertFalse(tokens['lanes_polygons'])
        xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[3]].get_bounds('lanes_polygons')
        tokens = self.nuplan_maps[self.locations[3]].get_records_in_patch([xmin, ymin, xmax, ymax], ['lanes_polygons'])
        self.assertTrue(tokens['lanes_polygons'])

    def test_get_layer_polygon(self) -> None:
        """Checks the function of retrieving the polygons of a particular layer within the specified patch."""
        with self.assertRaises(Exception):
            self.nuplan_maps[self.locations[3]].get_layer_polygon((0, 0, 0, 0), 0.0, 'drivable_area')
        self.assertFalse(self.nuplan_maps[self.locations[3]].get_layer_polygon((0, 0, 0, 0), 0.0, 'lanes_polygons'))
        xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[0]].get_bounds('lanes_polygons')
        width = xmax - xmin
        height = ymax - ymin
        patch_box = (xmin + width / 2, ymin + height / 2, height, width)
        patch_angle = 0.0
        self.assertTrue(self.nuplan_maps[self.locations[0]].get_layer_polygon(patch_box, patch_angle, 'lanes_polygons'))

    def test_get_layer_line(self) -> None:
        """Checks the function of retrieving the lines of a particular layer within the specified patch."""
        with self.assertRaises(Exception):
            self.nuplan_maps[self.locations[3]].get_layer_line((0, 0, 0, 0), 0.0, 'drivable_area')
        self.assertFalse(self.nuplan_maps[self.locations[3]].get_layer_line((0, 0, 0, 0), 0.0, 'lanes_polygons'))
        xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[0]].get_bounds('lanes_polygons')
        width = xmax - xmin
        height = ymax - ymin
        patch_box = (xmin + width / 2, ymin + height / 2, height, width)
        patch_angle = 0.0
        self.assertTrue(self.nuplan_maps[self.locations[0]].get_layer_line(patch_box, patch_angle, 'lanes_polygons'))

def test_patch_coord(self) -> None:
    """
        Checks the function to get patch coordinates without rotation.
        """
    path_center = [0, 0]
    path_dimension = [10, 10]
    polygon_coords = self.nuplan_maps[self.locations[0]].get_patch_coord((path_center[0], path_center[1], path_dimension[0], path_dimension[1]), 0.0)
    expected_polygon_coords = Polygon([[5, -5], [5, 5], [-5, 5], [-5, -5], [5, -5]])
    self.assertEqual(polygon_coords, expected_polygon_coords)

def test_vector_dimensions(self) -> None:
    """
        Checks dimensions of vector layer. It must be less than or equal to size of map.
        """
    for location in self.locations:
        vector_layer_bounds = self.nuplan_maps[location].get_bounds('lanes_polygons')
        map_shape = self.nuplan_maps[location].get_map_dimension()
        self.assertLess(vector_layer_bounds[0], vector_layer_bounds[2])
        self.assertLess(vector_layer_bounds[1], vector_layer_bounds[3])
        self.assertLess(vector_layer_bounds[2] - vector_layer_bounds[0], map_shape[0])
        self.assertLess(vector_layer_bounds[3] - vector_layer_bounds[1], map_shape[1])

def test_line_in_patch(self) -> None:
    """
        Checks if the line inside patch.
        """
    line_coords = LineString([(1.0, 1.0), (10.0, 10.0)])
    box_coords = [0.0, 0.0, 11.0, 11.0]
    self.assertTrue(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords))
    box_coords = [0.0, 0.0, 8.0, 8.0]
    self.assertFalse(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords))

def test_line_intersects_patch(self) -> None:
    """
        Checks if line intersects the patch.
        """
    line_coords = LineString([(0.0, 0.0), (10.0, 10.0)])
    box_coords = [0.0, 0.0, 11.0, 11.0]
    self.assertTrue(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords, 'intersect'))
    box_coords = [11.0, 11.0, 16.0, 16.0]
    self.assertFalse(self.nuplan_maps[self.locations[0]]._is_line_record_in_patch(line_coords, box_coords, 'intersect'))

def test_polygon_in_patch(self) -> None:
    """
        Checks if polygon is inside patch.
        """
    polygon_coords = Polygon([(1.0, 1.0), (1.0, 10.0), (10.0, 10.0), (1.0, 1.0)])
    box_coords = [0.0, 0.0, 11.0, 11.0]
    self.assertTrue(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords))
    box_coords = [0.0, 0.0, 8.0, 8.0]
    self.assertFalse(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords))

def test_polygon_intersects_patch(self) -> None:
    """
        Check if polygon intersects patch.
        """
    polygon_coords = Polygon([(1.0, 1.0), (1.0, 10.0), (10.0, 10.0), (1.0, 1.0)])
    box_coords = [1.0, 1.0, 11.0, 11.0]
    self.assertTrue(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords, 'intersect'))
    box_coords = [12.0, 14.0, 15.0, 15.0]
    self.assertFalse(self.nuplan_maps[self.locations[0]]._is_polygon_record_in_patch(polygon_coords, box_coords, 'intersect'))

def test_layers_on_points(self) -> None:
    """
        Checks if returns correct layers given a point.
        """
    with self.assertRaises(Exception):
        self.nuplan_maps[self.locations[3]].layers_on_point(0, 0, ['lane_connectors'])
    self.assertFalse(self.nuplan_maps[self.locations[3]].layers_on_point(0, 0, []))
    layer = self.nuplan_maps[self.locations[2]].layers_on_point(664777.776, 3999698.364, ['lanes_polygons'])
    self.assertEqual(layer['lanes_polygons'], ['63085'])
    layer = self.nuplan_maps[self.locations[3]].layers_on_point(87488.0, 43600.0, ['lanes_polygons'])
    self.assertFalse(layer['lanes_polygons'])

def test_get_records_in_patch(self) -> None:
    """
        Checks the function of getting all the record token that intersects or within a particular rectangular patch.
        """
    with self.assertRaises(Exception):
        self.nuplan_maps[self.locations[3]].get_records_in_patch([0, 0, 0, 0], ['drivable_area'])
    tokens = self.nuplan_maps[self.locations[3]].get_records_in_patch([0, 0, 0, 0], ['lanes_polygons'])
    self.assertFalse(tokens['lanes_polygons'])
    xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[3]].get_bounds('lanes_polygons')
    tokens = self.nuplan_maps[self.locations[3]].get_records_in_patch([xmin, ymin, xmax, ymax], ['lanes_polygons'])
    self.assertTrue(tokens['lanes_polygons'])

def test_get_layer_polygon(self) -> None:
    """Checks the function of retrieving the polygons of a particular layer within the specified patch."""
    with self.assertRaises(Exception):
        self.nuplan_maps[self.locations[3]].get_layer_polygon((0, 0, 0, 0), 0.0, 'drivable_area')
    self.assertFalse(self.nuplan_maps[self.locations[3]].get_layer_polygon((0, 0, 0, 0), 0.0, 'lanes_polygons'))
    xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[0]].get_bounds('lanes_polygons')
    width = xmax - xmin
    height = ymax - ymin
    patch_box = (xmin + width / 2, ymin + height / 2, height, width)
    patch_angle = 0.0
    self.assertTrue(self.nuplan_maps[self.locations[0]].get_layer_polygon(patch_box, patch_angle, 'lanes_polygons'))

def test_get_layer_line(self) -> None:
    """Checks the function of retrieving the lines of a particular layer within the specified patch."""
    with self.assertRaises(Exception):
        self.nuplan_maps[self.locations[3]].get_layer_line((0, 0, 0, 0), 0.0, 'drivable_area')
    self.assertFalse(self.nuplan_maps[self.locations[3]].get_layer_line((0, 0, 0, 0), 0.0, 'lanes_polygons'))
    xmin, ymin, xmax, ymax = self.nuplan_maps[self.locations[0]].get_bounds('lanes_polygons')
    width = xmax - xmin
    height = ymax - ymin
    patch_box = (xmin + width / 2, ymin + height / 2, height, width)
    patch_angle = 0.0
    self.assertTrue(self.nuplan_maps[self.locations[0]].get_layer_line(patch_box, patch_angle, 'lanes_polygons'))

def make_dilatable_map_layer(mask: npt.NDArray[np.uint8], precision: float) -> MapLayer:
    """
    Convenience method for constructing a dilatable map with the appropriate pre-computed distances.
    :param mask: Pixel values.
    :param precision: Meters per pixel.
    :return: A MapLayer Object.
    """
    joint_distance = compute_joint_distance_matrix(mask, precision)
    layer = MapLayer(mask, make_meta(True, precision), joint_distance=joint_distance)
    return layer

class TestMask(unittest.TestCase):
    """Test Mask."""
    data = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])

    def test_negative_dilation(self) -> None:
        """Checks if it raises with negative dilation values."""
        layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
        for negative_number in [-0.01, -1, -200]:
            with self.subTest(negative_number=negative_number):
                self.assertRaises(AssertionError, layer.mask, dilation=negative_number)

    def test_dilate_undilatable_layer(self) -> None:
        """Checks if it raises with dilating on unlidatable layer."""
        meta = make_meta(can_dilate=False, precision=ONE_PIXEL_PER_METER)
        layer = MapLayer(TestMask.data, meta)
        self.assertRaises(AssertionError, layer.mask, dilation=1)

    def test_no_dilation(self) -> None:
        """Tests layer with no dilation."""
        layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
        self.assertTrue(np.array_equal(layer.mask(dilation=0), TestMask.data))

    def test_dilation(self) -> None:
        """Tests dilation with different dilation values."""
        layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
        test_cases = [(0.1, np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])), (0.5, np.array([[1, 1, 1], [1, 1, 0], [1, 0, 0]])), (1, np.array([[1, 1, 1], [1, 1, 1], [1, 1, 0]])), (2, np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]))]
        for dilation, expected_mask in test_cases:
            with self.subTest(dilation=dilation, expected_mask=expected_mask):
                self.assertTrue(np.array_equal(layer.mask(dilation=dilation), expected_mask))

def test_negative_dilation(self) -> None:
    """Checks if it raises with negative dilation values."""
    layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
    for negative_number in [-0.01, -1, -200]:
        with self.subTest(negative_number=negative_number):
            self.assertRaises(AssertionError, layer.mask, dilation=negative_number)

def test_dilate_undilatable_layer(self) -> None:
    """Checks if it raises with dilating on unlidatable layer."""
    meta = make_meta(can_dilate=False, precision=ONE_PIXEL_PER_METER)
    layer = MapLayer(TestMask.data, meta)
    self.assertRaises(AssertionError, layer.mask, dilation=1)

def test_no_dilation(self) -> None:
    """Tests layer with no dilation."""
    layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
    self.assertTrue(np.array_equal(layer.mask(dilation=0), TestMask.data))

def test_dilation(self) -> None:
    """Tests dilation with different dilation values."""
    layer = make_dilatable_map_layer(TestMask.data, ONE_PIXEL_PER_METER)
    test_cases = [(0.1, np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])), (0.5, np.array([[1, 1, 1], [1, 1, 0], [1, 0, 0]])), (1, np.array([[1, 1, 1], [1, 1, 1], [1, 1, 0]])), (2, np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]]))]
    for dilation, expected_mask in test_cases:
        with self.subTest(dilation=dilation, expected_mask=expected_mask):
            self.assertTrue(np.array_equal(layer.mask(dilation=dilation), expected_mask))

class TestCrop(unittest.TestCase):
    """Test class for Cropping layer."""
    data = np.array([[1, 1, 0], [1, 0, 0], [0, 0, 0]])

    def test_empty_slice(self) -> None:
        """Checks empty slice, and size of layer after cropping should be zero."""
        layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
        crop = layer.crop(slice(0), slice(0))
        self.assertEqual(crop.shape, (0, 0))

    def test_full_slices(self) -> None:
        """Tests with full slice and various out-of-bounds slices."""
        layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
        test_cases = [(slice(0, 3), slice(0, 3)), (slice(0, 3), slice(0, 5)), (slice(0, 5), slice(0, 3)), (slice(0, 5), slice(0, 5))]
        for row_slice, col_slice in test_cases:
            with self.subTest(row_slice=row_slice, col_slice=col_slice):
                crop = layer.crop(row_slice, col_slice)
                self.assertTrue(np.array_equal(crop, TestCrop.data))

    def test_negative_dilation(self) -> None:
        """Tests to dilate with negative dilation value."""
        layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
        for negative_number in [-0.01, -1, -200]:
            with self.subTest(negative_number=negative_number):
                self.assertRaises(AssertionError, layer.crop, rows=slice(0, 2), cols=slice(0, 2), dilation=negative_number)

    def test_dilate_undilatable_layer(self) -> None:
        """Tests to dilate an undilatable layer in crop function."""
        meta = make_meta(can_dilate=False, precision=ONE_PIXEL_PER_METER)
        layer = MapLayer(TestCrop.data, meta)
        self.assertRaises(AssertionError, layer.crop, rows=slice(0, 2), cols=slice(0, 2), dilation=1)

    def test_no_dilation(self) -> None:
        """Test no dilation with crop function."""
        layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
        upper_left_crop = layer.crop(rows=slice(0, 2), cols=slice(0, 2), dilation=0)
        self.assertTrue(np.array_equal(upper_left_crop, np.array([[1, 1], [1, 0]])))
        lower_right_crop = layer.crop(rows=slice(1, 3), cols=slice(1, 3), dilation=0)
        self.assertTrue(np.array_equal(lower_right_crop, np.array([[0, 0], [0, 0]])))

    def test_dilation(self) -> None:
        """Tests dilation in crop function."""
        layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
        test_cases = [(0.1, np.array([[1, 0, 0], [0, 0, 0]])), (0.5, np.array([[1, 1, 0], [1, 0, 0]])), (1, np.array([[1, 1, 1], [1, 1, 0]])), (2, np.array([[1, 1, 1], [1, 1, 1]]))]
        for dilation, expected_lower_crop in test_cases:
            with self.subTest(dilation=dilation, expected_lower_crop=expected_lower_crop):
                crop = layer.crop(rows=slice(1, 3), cols=slice(0, 3), dilation=dilation)
                self.assertTrue(np.array_equal(crop, expected_lower_crop))

def test_empty_slice(self) -> None:
    """Checks empty slice, and size of layer after cropping should be zero."""
    layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
    crop = layer.crop(slice(0), slice(0))
    self.assertEqual(crop.shape, (0, 0))

def test_full_slices(self) -> None:
    """Tests with full slice and various out-of-bounds slices."""
    layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
    test_cases = [(slice(0, 3), slice(0, 3)), (slice(0, 3), slice(0, 5)), (slice(0, 5), slice(0, 3)), (slice(0, 5), slice(0, 5))]
    for row_slice, col_slice in test_cases:
        with self.subTest(row_slice=row_slice, col_slice=col_slice):
            crop = layer.crop(row_slice, col_slice)
            self.assertTrue(np.array_equal(crop, TestCrop.data))

def test_negative_dilation(self) -> None:
    """Tests to dilate with negative dilation value."""
    layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
    for negative_number in [-0.01, -1, -200]:
        with self.subTest(negative_number=negative_number):
            self.assertRaises(AssertionError, layer.crop, rows=slice(0, 2), cols=slice(0, 2), dilation=negative_number)

def test_dilate_undilatable_layer(self) -> None:
    """Tests to dilate an undilatable layer in crop function."""
    meta = make_meta(can_dilate=False, precision=ONE_PIXEL_PER_METER)
    layer = MapLayer(TestCrop.data, meta)
    self.assertRaises(AssertionError, layer.crop, rows=slice(0, 2), cols=slice(0, 2), dilation=1)

def test_no_dilation(self) -> None:
    """Test no dilation with crop function."""
    layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
    upper_left_crop = layer.crop(rows=slice(0, 2), cols=slice(0, 2), dilation=0)
    self.assertTrue(np.array_equal(upper_left_crop, np.array([[1, 1], [1, 0]])))
    lower_right_crop = layer.crop(rows=slice(1, 3), cols=slice(1, 3), dilation=0)
    self.assertTrue(np.array_equal(lower_right_crop, np.array([[0, 0], [0, 0]])))

def test_dilation(self) -> None:
    """Tests dilation in crop function."""
    layer = make_dilatable_map_layer(TestCrop.data, ONE_PIXEL_PER_METER)
    test_cases = [(0.1, np.array([[1, 0, 0], [0, 0, 0]])), (0.5, np.array([[1, 1, 0], [1, 0, 0]])), (1, np.array([[1, 1, 1], [1, 1, 0]])), (2, np.array([[1, 1, 1], [1, 1, 1]]))]
    for dilation, expected_lower_crop in test_cases:
        with self.subTest(dilation=dilation, expected_lower_crop=expected_lower_crop):
            crop = layer.crop(rows=slice(1, 3), cols=slice(0, 3), dilation=dilation)
            self.assertTrue(np.array_equal(crop, expected_lower_crop))

class TestTransformMatrix(unittest.TestCase):
    """Test Class for Transform matrix."""

    def test_transform_matrix(self) -> None:
        """Tests transform matrix for MapLayers with different precisions and different size."""
        test_cases = [(101, 101, 1, np.array([[1, 0, 0, 0], [0, -1, 0, 100], [0, 0, 1, 0], [0, 0, 0, 1]])), (101, 101, 0.1, np.array([[10, 0, 0, 0], [0, -10, 0, 100], [0, 0, 1, 0], [0, 0, 0, 1]])), (51, 51, 1, np.array([[1, 0, 0, 0], [0, -1, 0, 50], [0, 0, 1, 0], [0, 0, 0, 1]])), (51, 51, 10, np.array([[0.1, 0, 0, 0], [0, -0.1, 0, 50], [0, 0, 1, 0], [0, 0, 0, 1]]))]
        for nrows, ncols, precision, expected_matrix in test_cases:
            with self.subTest(nrows=nrows, ncols=ncols, precision=precision, expected_matrix=expected_matrix):
                layer = MapLayer(np.ones((nrows, ncols)), make_meta(False, precision))
                self.assertTrue(np.array_equal(layer.transform_matrix, expected_matrix))

def test_transform_matrix(self) -> None:
    """Tests transform matrix for MapLayers with different precisions and different size."""
    test_cases = [(101, 101, 1, np.array([[1, 0, 0, 0], [0, -1, 0, 100], [0, 0, 1, 0], [0, 0, 0, 1]])), (101, 101, 0.1, np.array([[10, 0, 0, 0], [0, -10, 0, 100], [0, 0, 1, 0], [0, 0, 0, 1]])), (51, 51, 1, np.array([[1, 0, 0, 0], [0, -1, 0, 50], [0, 0, 1, 0], [0, 0, 0, 1]])), (51, 51, 10, np.array([[0.1, 0, 0, 0], [0, -0.1, 0, 50], [0, 0, 1, 0], [0, 0, 0, 1]]))]
    for nrows, ncols, precision, expected_matrix in test_cases:
        with self.subTest(nrows=nrows, ncols=ncols, precision=precision, expected_matrix=expected_matrix):
            layer = MapLayer(np.ones((nrows, ncols)), make_meta(False, precision))
            self.assertTrue(np.array_equal(layer.transform_matrix, expected_matrix))

class TestToPixelCoords(unittest.TestCase):
    """Test Class of converting to pixel coordinates."""

    def test_without_precision_scale(self) -> None:
        """Tests to_pixel_coords function on a map layer of 1 pixel per meter."""
        layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, ONE_PIXEL_PER_METER))
        test_cases = [[(0, 0), (0, 100)], [(0, 100), (0, 0)], [(100, 0), (100, 100)], [(100, 100), (100, 0)], [(0, 40), (0, 60)], [(40, 0), (40, 100)], [(40, 100), (40, 0)], [(100, 40), (100, 60)], [(50, 50), (50, 50)], [(36, 42), (36, 58)], [(99, 37), (99, 63)], [(7, 99), (7, 1)]]
        for input_point, expected_output in test_cases:
            with self.subTest(input_point=input_point, expected_output=expected_output):
                self.assertEqual(layer.to_pixel_coords(*input_point), expected_output)

    def test_with_precision_scale(self) -> None:
        """Test to_pixel_coords function on a map layer of 0.1 precision."""
        layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, TEN_PIXELS_PER_METER))
        test_cases = [[(0, 0), (0, 100)], [(0, 10), (0, 0)], [(10, 0), (100, 100)], [(10, 10), (100, 0)], [(0, 4), (0, 60)], [(4, 0), (40, 100)], [(4, 10), (40, 0)], [(10, 4), (100, 60)], [(5, 5), (50, 50)], [(3.6, 4.2), (36, 58)], [(9.9, 3.7), (99, 63)], [(0.7, 9.9), (7, 1)]]
        for input_point, expected_output in test_cases:
            with self.subTest(input_point=input_point, expected_output=expected_output):
                self.assertEqual(layer.to_pixel_coords(*input_point), expected_output)

    def test_multiple_inputs(self) -> None:
        """Test with multiple inputs."""
        layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, ONE_PIXEL_PER_METER))
        input_x = np.array([5, 60])
        input_y = np.array([20, 77])
        expected_x = np.array([5, 60])
        expected_y = np.array([80, 23])
        output_x, output_y = layer.to_pixel_coords(input_x, input_y)
        self.assertTrue(np.array_equal(output_x, expected_x))
        self.assertTrue(np.array_equal(output_y, expected_y))

def test_without_precision_scale(self) -> None:
    """Tests to_pixel_coords function on a map layer of 1 pixel per meter."""
    layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, ONE_PIXEL_PER_METER))
    test_cases = [[(0, 0), (0, 100)], [(0, 100), (0, 0)], [(100, 0), (100, 100)], [(100, 100), (100, 0)], [(0, 40), (0, 60)], [(40, 0), (40, 100)], [(40, 100), (40, 0)], [(100, 40), (100, 60)], [(50, 50), (50, 50)], [(36, 42), (36, 58)], [(99, 37), (99, 63)], [(7, 99), (7, 1)]]
    for input_point, expected_output in test_cases:
        with self.subTest(input_point=input_point, expected_output=expected_output):
            self.assertEqual(layer.to_pixel_coords(*input_point), expected_output)

def test_with_precision_scale(self) -> None:
    """Test to_pixel_coords function on a map layer of 0.1 precision."""
    layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, TEN_PIXELS_PER_METER))
    test_cases = [[(0, 0), (0, 100)], [(0, 10), (0, 0)], [(10, 0), (100, 100)], [(10, 10), (100, 0)], [(0, 4), (0, 60)], [(4, 0), (40, 100)], [(4, 10), (40, 0)], [(10, 4), (100, 60)], [(5, 5), (50, 50)], [(3.6, 4.2), (36, 58)], [(9.9, 3.7), (99, 63)], [(0.7, 9.9), (7, 1)]]
    for input_point, expected_output in test_cases:
        with self.subTest(input_point=input_point, expected_output=expected_output):
            self.assertEqual(layer.to_pixel_coords(*input_point), expected_output)

def test_multiple_inputs(self) -> None:
    """Test with multiple inputs."""
    layer = MapLayer(DUMMY_DATA_101_BY_101, make_meta(False, ONE_PIXEL_PER_METER))
    input_x = np.array([5, 60])
    input_y = np.array([20, 77])
    expected_x = np.array([5, 60])
    expected_y = np.array([80, 23])
    output_x, output_y = layer.to_pixel_coords(input_x, input_y)
    self.assertTrue(np.array_equal(output_x, expected_x))
    self.assertTrue(np.array_equal(output_y, expected_y))

class TestIsOnMask(unittest.TestCase):
    """Test Class of is_on_mask function."""
    small_number = 1e-05
    half_gt = TEN_PIXELS_PER_METER / 2 + small_number
    half_lt = TEN_PIXELS_PER_METER / 2 - small_number

    def test_out_of_bounds_without_dilation(self) -> None:
        """This checks the boundary conditions for is_on_mask."""
        mask = np.ones((10, 10))
        layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
        x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertTrue(np.all(layer.is_on_mask(x, y)))
        x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertFalse(np.any(layer.is_on_mask(x, y)))

    def test_out_of_bounds_with_dilation(self) -> None:
        """This checks the boundary conditions for is_on_mask."""
        mask = np.ones((10, 10))
        layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertTrue(np.all(layer.is_on_mask(x, y, dilation=0.3)))
        x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertFalse(np.any(layer.is_on_mask(x, y, dilation=0.3)))

    def test_native_resolution(self) -> None:
        """Test map resolution."""
        mask = np.zeros((51, 40))
        mask[30, 20] = 1
        layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
        self.assertTrue(layer.is_on_mask(2, 2))
        on_mask = [(2 + self.half_lt, 2), (2 - self.half_lt, 2), (2, 2 + self.half_lt), (2, 2 - self.half_lt)]
        off_mask = [(2 + self.half_gt, 2), (2 - self.half_gt, 2), (2, 2 + self.half_gt), (2, 2 - self.half_gt)]
        for point in on_mask:
            with self.subTest(point=point):
                self.assertTrue(layer.is_on_mask(*point)[0])
        for point in off_mask:
            with self.subTest(point=point):
                self.assertFalse(layer.is_on_mask(*point)[0])

    def test_edges(self) -> None:
        """Test map edges."""
        mask = np.ones((51, 40))
        layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
        self.assertTrue(layer.is_on_mask(0, 0.1))
        self.assertTrue(layer.is_on_mask(0, 5))
        self.assertTrue(layer.is_on_mask(3.9, 0.1))
        self.assertTrue(layer.is_on_mask(3.9, 5))
        self.assertFalse(layer.is_on_mask(3.9 + self.half_gt, 0.1))
        self.assertFalse(layer.is_on_mask(3.9 + self.half_gt, 5))
        self.assertFalse(layer.is_on_mask(0 - self.half_gt, 0.1))
        self.assertFalse(layer.is_on_mask(0 - self.half_gt, 5))

def test_out_of_bounds_without_dilation(self) -> None:
    """This checks the boundary conditions for is_on_mask."""
    mask = np.ones((10, 10))
    layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
    x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertTrue(np.all(layer.is_on_mask(x, y)))
    x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertFalse(np.any(layer.is_on_mask(x, y)))

def test_out_of_bounds_with_dilation(self) -> None:
    """This checks the boundary conditions for is_on_mask."""
    mask = np.ones((10, 10))
    layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertTrue(np.all(layer.is_on_mask(x, y, dilation=0.3)))
    x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertFalse(np.any(layer.is_on_mask(x, y, dilation=0.3)))

def test_native_resolution(self) -> None:
    """Test map resolution."""
    mask = np.zeros((51, 40))
    mask[30, 20] = 1
    layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
    self.assertTrue(layer.is_on_mask(2, 2))
    on_mask = [(2 + self.half_lt, 2), (2 - self.half_lt, 2), (2, 2 + self.half_lt), (2, 2 - self.half_lt)]
    off_mask = [(2 + self.half_gt, 2), (2 - self.half_gt, 2), (2, 2 + self.half_gt), (2, 2 - self.half_gt)]
    for point in on_mask:
        with self.subTest(point=point):
            self.assertTrue(layer.is_on_mask(*point)[0])
    for point in off_mask:
        with self.subTest(point=point):
            self.assertFalse(layer.is_on_mask(*point)[0])

def test_edges(self) -> None:
    """Test map edges."""
    mask = np.ones((51, 40))
    layer = MapLayer(mask, make_meta(False, TEN_PIXELS_PER_METER))
    self.assertTrue(layer.is_on_mask(0, 0.1))
    self.assertTrue(layer.is_on_mask(0, 5))
    self.assertTrue(layer.is_on_mask(3.9, 0.1))
    self.assertTrue(layer.is_on_mask(3.9, 5))
    self.assertFalse(layer.is_on_mask(3.9 + self.half_gt, 0.1))
    self.assertFalse(layer.is_on_mask(3.9 + self.half_gt, 5))
    self.assertFalse(layer.is_on_mask(0 - self.half_gt, 0.1))
    self.assertFalse(layer.is_on_mask(0 - self.half_gt, 5))

class TestDistToMask(unittest.TestCase):
    """This Class to test dist_to_mask function."""

    def test_out_of_bounds(self) -> None:
        """This checks the boundary conditions for dist_to_mask."""
        mask = np.ones((10, 10))
        layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertFalse(np.any(np.isnan(layer.dist_to_mask(x, y))))
        x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
        self.assertTrue(np.all(np.isnan(layer.dist_to_mask(x, y))))

    def test_linear_edge_low_precision(self) -> None:
        """Tests linear edges with low precision of 1."""
        mask = np.array([[0, 0, 1, 1]])
        layer = make_dilatable_map_layer(mask, ONE_PIXEL_PER_METER)
        test_cases = [(0, np.array([[1.5, 0.5, -0.5, -1.5]])), (1, np.array([[0.5, -0.5, -1.5, -2.5]])), (2, np.array([[-0.5, -1.5, -2.5, -3.5]]))]
        for dilation, expected_dist_to_mask in test_cases:
            for x in range(0, 4):
                with self.subTest(dilation=dilation, expected_dist_to_mask=expected_dist_to_mask, x=x):
                    actual = layer.dist_to_mask(x, 0, dilation)
                    expected = expected_dist_to_mask[0, x]
                    self.assertTrue(abs(actual - expected) < 0.001)

    def test_linear_edge_high_precision(self) -> None:
        """Test linear edge with high precision of 0.1."""
        mask = np.array([[0, 0, 1, 1]])
        layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        test_cases = [(0, np.array([[0.15, 0.05, -0.05, -0.15]])), (0.1, np.array([[0.05, -0.05, -0.15, -0.25]])), (0.2, np.array([[-0.05, -0.15, -0.25, -0.35]]))]
        x_in_meters = np.array([0, 0.1, 0.2, 0.3])
        y_in_meters = np.array([0, 0, 0, 0])
        for dilation, expected_dist_to_mask in test_cases:
            actual = layer.dist_to_mask(x_in_meters, y_in_meters, dilation)
            with self.subTest(dilation=dilation, expected_dist_to_mask=expected_dist_to_mask, actual=actual):
                self.assertTrue(np.allclose(actual, expected_dist_to_mask))

    def _test_non_linear_edge_helper(self, mask: npt.NDArray[np.uint8], expected_matrix: npt.NDArray[np.float64], test_name: str) -> None:
        """
        Helper function to test nonlinear edge cases.
        :param mask: Pixel values.
        :param expected_matrix: The expected distance matrix of points on mask.
        :param test_name: A string of test name.
        """
        layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        for dilation in [0, 0.1, 0.2, 0.3]:
            for x_in_pixels in range(0, 5):
                for y_in_pixels in range(0, 5):
                    x_in_meters = x_in_pixels * 0.1
                    y_in_meters = y_in_pixels * 0.1
                    matrix_row = mask.shape[1] - 1 - y_in_pixels
                    matrix_col = x_in_pixels
                    actual = layer.dist_to_mask(x_in_meters, y_in_meters, dilation=dilation)
                    expected = expected_matrix[matrix_row, matrix_col] - dilation
                    with self.subTest(x_in_meters=x_in_meters, y_in_meters=y_in_meters, actual=actual, expected=expected, test_name=test_name):
                        self.assertTrue(abs(actual - expected) < 0.005)

    def test_round_edge(self) -> None:
        """Test case of round edge."""
        mask = np.array([[0, 0, 0, 0, 1], [0, 0, 0, 0, 1], [0, 0, 0, 1, 1], [0, 1, 1, 1, 1], [1, 1, 1, 1, 1]])
        expected_matrix = np.array([[0.266, 0.23, 0.15, 0.05, -0.05], [0.174, 0.15, 0.09, 0.05, -0.05], [0.09, 0.05, 0.05, -0.05, -0.09], [0.05, -0.05, -0.05, -0.09, -0.174], [-0.05, -0.09, -0.15, -0.174, -0.23]])
        self._test_non_linear_edge_helper(mask, expected_matrix, 'test_round_edge')

    def test_hole(self) -> None:
        """Test case of a hole mask."""
        mask = np.array([[1, 1, 1, 1, 1], [1, 0, 0, 0, 1], [1, 0, 0, 0, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 1]])
        expected_matrix = np.array([[-0.09, -0.05, -0.05, -0.05, -0.09], [-0.05, 0.05, 0.05, 0.05, -0.05], [-0.05, 0.05, 0.15, 0.09, 0.05], [-0.05, 0.05, 0.05, 0.05, -0.05], [-0.09, -0.05, -0.05, -0.05, -0.09]])
        self._test_non_linear_edge_helper(mask, expected_matrix, 'test_hole')

def test_out_of_bounds(self) -> None:
    """This checks the boundary conditions for dist_to_mask."""
    mask = np.ones((10, 10))
    layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    x, y = OutOfBoundsData.in_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertFalse(np.any(np.isnan(layer.dist_to_mask(x, y))))
    x, y = OutOfBoundsData.out_of_bounds_for_10_by_10_layer_with_10px_per_m
    self.assertTrue(np.all(np.isnan(layer.dist_to_mask(x, y))))

def test_linear_edge_low_precision(self) -> None:
    """Tests linear edges with low precision of 1."""
    mask = np.array([[0, 0, 1, 1]])
    layer = make_dilatable_map_layer(mask, ONE_PIXEL_PER_METER)
    test_cases = [(0, np.array([[1.5, 0.5, -0.5, -1.5]])), (1, np.array([[0.5, -0.5, -1.5, -2.5]])), (2, np.array([[-0.5, -1.5, -2.5, -3.5]]))]
    for dilation, expected_dist_to_mask in test_cases:
        for x in range(0, 4):
            with self.subTest(dilation=dilation, expected_dist_to_mask=expected_dist_to_mask, x=x):
                actual = layer.dist_to_mask(x, 0, dilation)
                expected = expected_dist_to_mask[0, x]
                self.assertTrue(abs(actual - expected) < 0.001)

def test_linear_edge_high_precision(self) -> None:
    """Test linear edge with high precision of 0.1."""
    mask = np.array([[0, 0, 1, 1]])
    layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    test_cases = [(0, np.array([[0.15, 0.05, -0.05, -0.15]])), (0.1, np.array([[0.05, -0.05, -0.15, -0.25]])), (0.2, np.array([[-0.05, -0.15, -0.25, -0.35]]))]
    x_in_meters = np.array([0, 0.1, 0.2, 0.3])
    y_in_meters = np.array([0, 0, 0, 0])
    for dilation, expected_dist_to_mask in test_cases:
        actual = layer.dist_to_mask(x_in_meters, y_in_meters, dilation)
        with self.subTest(dilation=dilation, expected_dist_to_mask=expected_dist_to_mask, actual=actual):
            self.assertTrue(np.allclose(actual, expected_dist_to_mask))

def _test_non_linear_edge_helper(self, mask: npt.NDArray[np.uint8], expected_matrix: npt.NDArray[np.float64], test_name: str) -> None:
    """
        Helper function to test nonlinear edge cases.
        :param mask: Pixel values.
        :param expected_matrix: The expected distance matrix of points on mask.
        :param test_name: A string of test name.
        """
    layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    for dilation in [0, 0.1, 0.2, 0.3]:
        for x_in_pixels in range(0, 5):
            for y_in_pixels in range(0, 5):
                x_in_meters = x_in_pixels * 0.1
                y_in_meters = y_in_pixels * 0.1
                matrix_row = mask.shape[1] - 1 - y_in_pixels
                matrix_col = x_in_pixels
                actual = layer.dist_to_mask(x_in_meters, y_in_meters, dilation=dilation)
                expected = expected_matrix[matrix_row, matrix_col] - dilation
                with self.subTest(x_in_meters=x_in_meters, y_in_meters=y_in_meters, actual=actual, expected=expected, test_name=test_name):
                    self.assertTrue(abs(actual - expected) < 0.005)

class TestConsistentIsOnMaskDistToMask(unittest.TestCase):
    """This Class to test the consistency of is_on_mask and dist_to_mask function."""

    def assert_on_mask_equals(self, layer: MapLayer, x: Any, y: Any, dilation: float, expected: bool) -> None:
        """
        Asserts when point is on mask, return True, otherwise False, and
        dist_to_mask gives a negative value, otherwise positive.
        :param layer: A MapLayer Object.
        :param x: Global x coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Global y coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
        The drivable_area mask is dilated to include points which are within this distance from itself.
        :param expected: The expected boolean value.
        """
        on_mask_result = layer.is_on_mask(x, y, dilation=dilation)
        self.assertEqual(on_mask_result, expected, f'expected is_on_mask({x}, {y}, {dilation}) to be {expected}, got {on_mask_result}')
        dist_to_mask_result = layer.dist_to_mask(x, y, dilation=dilation)
        self.assertEqual(dist_to_mask_result <= 0, expected, f'expected dist_to_mask({x}, {y}, {dilation}), to be {('<= 0' if expected else '> 0')}, got {dist_to_mask_result}')

    def test_dilation_with_foreground_point(self) -> None:
        """Test dilation with foreground point."""
        mask = np.zeros((51, 40))
        mask[30, 20] = 1
        layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        self.assertTrue(layer.is_on_mask(2, 2))
        self.assertFalse(layer.is_on_mask(2, 3))
        self.assert_on_mask_equals(layer, 2, 3, dilation=1, expected=True)
        self.assert_on_mask_equals(layer, 3, 2, dilation=1, expected=True)
        self.assert_on_mask_equals(layer, 2 + np.sqrt(1 / 2), 2 + np.sqrt(1 / 2), dilation=1, expected=True)
        self.assert_on_mask_equals(layer, 2, 3, dilation=0.9, expected=False)

    def test_dilation_with_curved_line(self) -> None:
        """Test Dilation over Curved Line."""
        mask = np.array([[0, 0, 0, 0, 1], [0, 0, 0, 0, 1], [0, 0, 0, 1, 1], [0, 1, 1, 1, 1], [1, 1, 1, 1, 1]])
        layer = make_dilatable_map_layer(mask, ONE_PIXEL_PER_METER)
        off_mask_points_in_physical_space = [(0, 4), (1, 4)]
        for x in range(0, 5):
            for y in range(0, 5):
                with self.subTest(x=x, y=y):
                    expected_on_mask = (x, y) not in off_mask_points_in_physical_space
                    self.assert_on_mask_equals(layer, x, y, dilation=2, expected=expected_on_mask)

    def test_coarse_resolution(self) -> None:
        """Tests with normal and low resolution."""
        mask = np.zeros((51, 40))
        mask[30, 20] = 1
        mask[31, 20] = 1
        mask[30, 21] = 1
        mask[31, 21] = 1
        normal_res_layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
        low_res_layer = make_dilatable_map_layer(mask, FIVE_PIXELS_PER_METER)
        self.assert_on_mask_equals(normal_res_layer, 2, 2, dilation=0, expected=True)
        self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=0, expected=False)
        self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=2.0, expected=True)
        self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=1.9001, expected=True)
        self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=1.8, expected=False)

def assert_on_mask_equals(self, layer: MapLayer, x: Any, y: Any, dilation: float, expected: bool) -> None:
    """
        Asserts when point is on mask, return True, otherwise False, and
        dist_to_mask gives a negative value, otherwise positive.
        :param layer: A MapLayer Object.
        :param x: Global x coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param y: Global y coordinates. Can be a scalar, list or a numpy array of x coordinates.
        :param dilation: Specifies the threshold on the distance from the drivable_area mask.
        The drivable_area mask is dilated to include points which are within this distance from itself.
        :param expected: The expected boolean value.
        """
    on_mask_result = layer.is_on_mask(x, y, dilation=dilation)
    self.assertEqual(on_mask_result, expected, f'expected is_on_mask({x}, {y}, {dilation}) to be {expected}, got {on_mask_result}')
    dist_to_mask_result = layer.dist_to_mask(x, y, dilation=dilation)
    self.assertEqual(dist_to_mask_result <= 0, expected, f'expected dist_to_mask({x}, {y}, {dilation}), to be {('<= 0' if expected else '> 0')}, got {dist_to_mask_result}')

def test_dilation_with_foreground_point(self) -> None:
    """Test dilation with foreground point."""
    mask = np.zeros((51, 40))
    mask[30, 20] = 1
    layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    self.assertTrue(layer.is_on_mask(2, 2))
    self.assertFalse(layer.is_on_mask(2, 3))
    self.assert_on_mask_equals(layer, 2, 3, dilation=1, expected=True)
    self.assert_on_mask_equals(layer, 3, 2, dilation=1, expected=True)
    self.assert_on_mask_equals(layer, 2 + np.sqrt(1 / 2), 2 + np.sqrt(1 / 2), dilation=1, expected=True)
    self.assert_on_mask_equals(layer, 2, 3, dilation=0.9, expected=False)

def test_dilation_with_curved_line(self) -> None:
    """Test Dilation over Curved Line."""
    mask = np.array([[0, 0, 0, 0, 1], [0, 0, 0, 0, 1], [0, 0, 0, 1, 1], [0, 1, 1, 1, 1], [1, 1, 1, 1, 1]])
    layer = make_dilatable_map_layer(mask, ONE_PIXEL_PER_METER)
    off_mask_points_in_physical_space = [(0, 4), (1, 4)]
    for x in range(0, 5):
        for y in range(0, 5):
            with self.subTest(x=x, y=y):
                expected_on_mask = (x, y) not in off_mask_points_in_physical_space
                self.assert_on_mask_equals(layer, x, y, dilation=2, expected=expected_on_mask)

def test_coarse_resolution(self) -> None:
    """Tests with normal and low resolution."""
    mask = np.zeros((51, 40))
    mask[30, 20] = 1
    mask[31, 20] = 1
    mask[30, 21] = 1
    mask[31, 21] = 1
    normal_res_layer = make_dilatable_map_layer(mask, TEN_PIXELS_PER_METER)
    low_res_layer = make_dilatable_map_layer(mask, FIVE_PIXELS_PER_METER)
    self.assert_on_mask_equals(normal_res_layer, 2, 2, dilation=0, expected=True)
    self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=0, expected=False)
    self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=2.0, expected=True)
    self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=1.9001, expected=True)
    self.assert_on_mask_equals(low_res_layer, 2, 4, dilation=1.8, expected=False)

class TestMapExplorer(unittest.TestCase):
    """Test NuPlanMapExplorer class."""

    def setUp(self) -> None:
        """
        Initialize the map.
        """
        self.maps_db = get_test_maps_db()
        self.location = 'us-nv-las-vegas-strip'
        self.nuplan_map = NuPlanMapWrapper(maps_db=self.maps_db, map_name=self.location)
        self.nuplan_explore = NuPlanMapExplorer(self.nuplan_map)

    def test_render_layers(self) -> None:
        """
        Checks the function to render layers.
        """
        try:
            self.nuplan_explore.render_layers(self.nuplan_map.vector_layers, alpha=0.5)
        except RuntimeError:
            self.fail('render_layers() raised RuntimeError unexpectedly!')

    def test_render_map_mask(self) -> None:
        """
        Checks the function to render map mask.
        """
        xmin, ymin, xmax, ymax = self.nuplan_map.get_bounds('lanes_polygons')
        width = xmax - xmin
        height = ymax - ymin
        try:
            self.nuplan_explore.render_map_mask((xmin + width / 2, ymin + height / 2, height, width), 0.0, ['lanes_polygons', 'intersections'], (500, 500), (50, 50), 2)
        except RuntimeError:
            self.fail('render_map_mask() raised RuntimeError unexpectedly!')

    def test_render_nearby_roads(self) -> None:
        """
        Checks the function to render nearby roads.
        """
        xmin, ymin, xmax, ymax = self.nuplan_map.get_bounds('lanes_polygons')
        width = xmax - xmin
        height = ymax - ymin
        x = xmin + width / 2 - 921
        y = ymin + height / 2 + 1540
        try:
            self.nuplan_explore.render_nearby_roads(x, y)
        except RuntimeError:
            self.fail('render_nearby_roads() raised RuntimeError unexpectedly!')

def test_render_map_mask(self) -> None:
    """
        Checks the function to render map mask.
        """
    xmin, ymin, xmax, ymax = self.nuplan_map.get_bounds('lanes_polygons')
    width = xmax - xmin
    height = ymax - ymin
    try:
        self.nuplan_explore.render_map_mask((xmin + width / 2, ymin + height / 2, height, width), 0.0, ['lanes_polygons', 'intersections'], (500, 500), (50, 50), 2)
    except RuntimeError:
        self.fail('render_map_mask() raised RuntimeError unexpectedly!')

def test_render_nearby_roads(self) -> None:
    """
        Checks the function to render nearby roads.
        """
    xmin, ymin, xmax, ymax = self.nuplan_map.get_bounds('lanes_polygons')
    width = xmax - xmin
    height = ymax - ymin
    x = xmin + width / 2 - 921
    y = ymin + height / 2 + 1540
    try:
        self.nuplan_explore.render_nearby_roads(x, y)
    except RuntimeError:
        self.fail('render_nearby_roads() raised RuntimeError unexpectedly!')

def unwrap(angles: torch.Tensor, dim: int=-1) -> torch.Tensor:
    """
    This unwraps a signal p by changing elements which have an absolute difference from their
    predecessor of more than Pi to their period-complementary values.
    It is meant to mimic numpy.unwrap (https://numpy.org/doc/stable/reference/generated/numpy.unwrap.html)
    :param angles: The tensor to unwrap.
    :param dim: Axis where the unwrap operation is performed.
    :return: Unwrapped tensor.
    """
    pi = torch.tensor(math.pi, dtype=torch.float64)
    angle_diff = torch.diff(angles, dim=dim)
    nn_functional_pad_args = [(0, 0) for _ in range(len(angles.shape))]
    nn_functional_pad_args[dim] = (1, 0)
    pad_arg: List[int] = []
    for value in nn_functional_pad_args[::-1]:
        pad_arg.append(value[0])
        pad_arg.append(value[1])
    dphi = torch.nn.functional.pad(angle_diff, pad_arg)
    dphi_m = (dphi + pi) % (2.0 * pi) - pi
    dphi_m[(dphi_m == -pi) & (dphi > 0)] = pi
    phi_adj = dphi_m - dphi
    phi_adj[dphi.abs() < pi] = 0
    return angles + phi_adj.cumsum(dim)

class TestFileBackedBarrier(unittest.TestCase):
    """
    A class to test that the file backed barrier works properly.
    """

    def test_file_backed_barrier_functions_normal_case_local(self) -> None:
        """
        Tests that the file backed barrier functions properly locally.
        """
        sleep_interval_sec = 10
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                if current_time == sleep_interval_sec + 30:
                    current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                    self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
                else:
                    current_time += sleep_interval_sec
                    self.assertEqual(sleep_interval_sec, sleep_time)
                if current_time == 40:
                    FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
                if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                    FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
                return current_time
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
                barrier = FileBackedBarrier(tmp_dir)
                barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

    def test_file_backed_barrier_functions_normal_case_s3(self) -> None:
        """
        Tests that the file backed barrier functions properly in s3.
        """
        sleep_interval_sec = 10
        sample_s3_path = 's3://ml-caches/mitchell.spryn/barrier'
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                if current_time == sleep_interval_sec + 30:
                    current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                    self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
                else:
                    current_time += sleep_interval_sec
                    self.assertEqual(sleep_interval_sec, sleep_time)
                if current_time == 40:
                    FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
                if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                    FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
                return current_time

            def patch_get_s3_client() -> unittest.mock.Mock:
                """
                Mocks the get_s3_client method.
                """

                def patch_s3_client_put_object(Body: bytes, Bucket: str, Key: str) -> None:
                    """
                    A patch for the s3 client put object method.
                    :param body: The body passed to the method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                    self.assertTrue(len(Body) > 0)
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/1', Key)
                    check_file = tmp_dir / '1'
                    self.assertFalse(check_file.exists())
                    with open(check_file, 'w') as f:
                        f.write('x')

                def patch_s3_client_delete_object(Bucket: str, Key: str) -> None:
                    """
                    A patch for the s3 client put object method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/1', Key)
                    check_file = tmp_dir / '1'
                    self.assertTrue(check_file.exists())
                    check_file.unlink()

                def patch_s3_client_list_objects_v2(Bucket: str, Prefix: str) -> Dict[str, List[Dict[str, str]]]:
                    """
                    A patch for the s3 client list objects v2 method.
                    :param Bucket: The bucket passed.
                    :param Prefix: The prefix passed.
                    """
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/', Prefix)
                    return {'Contents': [{'Key': f's3://ml-caches/mitchell.spryn/barrier/{p.stem}'} for p in tmp_dir.glob('**/*') if p.is_file()]}
                mock_client = unittest.mock.Mock()
                mock_client.put_object = patch_s3_client_put_object
                mock_client.list_objects_v2 = patch_s3_client_list_objects_v2
                mock_client.delete_object = patch_s3_client_delete_object
                return mock_client
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.get_s3_client', patch_get_s3_client):
                barrier = FileBackedBarrier(Path(sample_s3_path))
                barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

    def test_file_backed_barrier_timeout(self) -> None:
        """
        Tests that the timeout feature works properly.
        """
        sleep_interval_sec = 10
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                self.assertEqual(sleep_interval_sec, sleep_time)
                current_time += sleep_interval_sec

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                return current_time
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
                barrier = FileBackedBarrier(tmp_dir)
                with self.assertRaises(TimeoutError):
                    barrier.wait_barrier('1', {'1', '2'}, timeout_s=40, poll_interval_s=sleep_interval_sec)

def patch_time_time() -> float:
    """
                A patch for the time.time method.
                :return: The current time.
                """
    nonlocal current_time
    return current_time

class TestS3Utils(unittest.TestCase):
    """
    A class to test that the S3 utilities function properly.
    """

    def test_is_s3_path(self) -> None:
        """
        Tests that the is_s3_path method works properly.
        """
        self.assertTrue(is_s3_path(Path('s3://foo/bar/baz.txt')))
        self.assertFalse(is_s3_path(Path('/foo/bar/baz')))
        self.assertFalse(is_s3_path(Path('foo/bar/baz')))
        self.assertTrue(is_s3_path('s3://foo/bar/baz.txt'))
        self.assertFalse(is_s3_path('/foo/bar/baz'))
        self.assertFalse(is_s3_path('foo/bar/baz'))

    def test_split_s3_path(self) -> None:
        """
        Tests that the split_s3_path method works properly.
        """
        sample_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
        expected_bucket = 'test-bucket'
        expected_path = Path('foo/bar/baz.txt')
        actual_bucket, actual_path = split_s3_path(sample_s3_path)
        self.assertEqual(expected_bucket, actual_bucket)
        self.assertEqual(expected_path, actual_path)

    @mock_async_s3()
    def test_get_async_s3_session(self) -> None:
        """
        Tests that getting a session works correctly.
        """
        sess_1 = get_async_s3_session()
        sess_2 = get_async_s3_session()
        self.assertEqual(sess_1, sess_2)
        sess_3 = get_async_s3_session(force_new=True)
        sess_4 = get_async_s3_session()
        self.assertNotEqual(sess_2, sess_3)
        self.assertEqual(sess_3, sess_4)

    @mock_async_s3()
    def test_download_directory_from_s3(self) -> None:
        """
        Tests that the download_directory_from_s3 method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_upload_directory = Path('test_download_directory_from_s3')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_upload_directory, test_bucket_name))
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_directory_path_and_contents = {os.path.join(temp_dir, path): contents for path, contents in expected_relative_path_and_contents.items()}
            download_directory_from_s3(temp_dir, test_upload_directory, test_bucket_name)
            all_files = glob.glob(f'{temp_dir}/**/*.txt', recursive=True)
            self.assertEqual(len(all_files), len(expected_directory_path_and_contents))
            for key in expected_directory_path_and_contents:
                self.assertTrue(os.path.exists(key))
                with open(key, 'r') as f:
                    actual_text = f.read().strip()
                self.assertEqual(expected_directory_path_and_contents[key], actual_text)

    @mock_async_s3()
    def test_list_files_in_s3_directory(self) -> None:
        """
        Tests that the list_files_in_s3_directory method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_files_directory = Path('test_list_files_in_s3_directory')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        expected_files = {test_files_directory / path for path in expected_relative_path_and_contents}
        actual_files = list_files_in_s3_directory(test_files_directory, test_bucket_name)
        self.assertEqual(len(expected_files), len(actual_files))
        for file_path in actual_files:
            self.assertTrue(file_path in expected_files)

    @mock_async_s3()
    def test_check_s3_exist_ops(self) -> None:
        """
        Tests that the check_s3_object_exists and check_s3_path_exists methods functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """

        def to_s3_path(key: Path, bucket: str) -> str:
            """
            Returns s3 path string from split path.
            :param key: s3 key.
            :param bucket: s3 bucket.
            :return: Unsplit s3 path.
            """
            return f's3://{bucket}/{key}'
        test_files_directory = Path('test_check_s3_object_exists')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'existing.txt': 'this exists.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        existing_key = test_files_directory / 'existing.txt'
        non_existing_key = test_files_directory / 'does_not_exist.txt'
        self.assertTrue(check_s3_object_exists(existing_key, test_bucket_name))
        self.assertTrue(check_s3_path_exists(to_s3_path(existing_key, test_bucket_name)))
        self.assertFalse(check_s3_object_exists(non_existing_key, test_bucket_name))
        self.assertFalse(check_s3_path_exists(to_s3_path(non_existing_key, test_bucket_name)))
        self.assertFalse(check_s3_object_exists(test_files_directory, test_bucket_name))
        self.assertTrue(check_s3_path_exists(to_s3_path(test_files_directory, test_bucket_name)))

    @mock_async_s3()
    def test_get_cache_metadata_paths(self) -> None:
        """
        Tests that the get_cache_metadata_paths method functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_files_directory = Path('test_get_cache_metadata_paths')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.csv': 'this is file1.', 'metadata/file2.csv': 'this is file2.', 'metadata/file3.csv': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        expected_metadata_files = [test_files_directory / 'metadata/file2.csv', test_files_directory / 'metadata/file3.csv']
        actual_metadata_files = get_cache_metadata_paths(test_files_directory, test_bucket_name)
        self.assertEqual(len(expected_metadata_files), len(actual_metadata_files))
        for s3_path in actual_metadata_files:
            bucket, file_path = split_s3_path(s3_path)
            self.assertTrue(file_path in expected_metadata_files)
        non_existing_files = get_cache_metadata_paths(test_files_directory, test_bucket_name, metadata_folder='non_existing')
        self.assertEqual(len(non_existing_files), 0)

    @mock_async_s3()
    def test_s3_single_file_ops(self) -> None:
        """
        Tests that the following methods work properly while mocking AWS:
        * Upload file to S3
        * Download file from S3
        * Read file from S3
        * Delete file from S3
        """
        upload_bucket_name = 'test-bucket'
        asyncio.run(create_mock_bucket(upload_bucket_name))
        test_id = str(uuid.uuid4())
        upload_bucket_folder = Path('test_upload_file_to_s3')
        upload_bucket_path = upload_bucket_folder / f'{test_id}.txt'
        expected_file_contents = f'A random identifier: {test_id}.'
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_file_path = Path(os.path.join(temp_dir, 'upload.txt'))
            with open(upload_file_path, 'w') as f:
                f.write(expected_file_contents)
            upload_file_to_s3(upload_file_path, upload_bucket_path, upload_bucket_name)
            self.assertEqual(1, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))
            read_file_contents = read_text_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(expected_file_contents, read_file_contents)
            read_binary_contents = read_binary_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(expected_file_contents, read_binary_contents.decode('utf-8'))
            download_file_path = Path(os.path.join(temp_dir, 'download.txt'))
            download_file_from_s3(download_file_path, upload_bucket_path, upload_bucket_name)
            self.assertTrue(os.path.exists(download_file_path))
            with open(download_file_path, 'r') as f:
                downloaded_text = f.read()
            self.assertEqual(expected_file_contents, downloaded_text)
            delete_file_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(0, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))

def test_is_s3_path(self) -> None:
    """
        Tests that the is_s3_path method works properly.
        """
    self.assertTrue(is_s3_path(Path('s3://foo/bar/baz.txt')))
    self.assertFalse(is_s3_path(Path('/foo/bar/baz')))
    self.assertFalse(is_s3_path(Path('foo/bar/baz')))
    self.assertTrue(is_s3_path('s3://foo/bar/baz.txt'))
    self.assertFalse(is_s3_path('/foo/bar/baz'))
    self.assertFalse(is_s3_path('foo/bar/baz'))

def _get_method_from_import(import_str: str) -> Callable[..., Any]:
    """
    Gets the method referenced by an import in the form that `unittest.mock.patch` expects.
    That is, given the string "foo.bar.baz.qux", imports "qux" from "foo.bar.baz"
    This is not a general purpose utility, so other import mechanisms (e.g. "from x import y")
      will not work.
    :param import_str: The import str.
    :return: The method.
    """
    import_path, method_name = import_str.rsplit('.', 1)
    module = importlib.import_module(import_path)
    method = cast(Callable[..., Any], getattr(module, method_name))
    return method

class StateVector2D:
    """Representation of vector in 2d."""
    __slots__ = ('_x', '_y', '_array')

    def __init__(self, x: float, y: float):
        """
        Create StateVector2D object
        :param x: float direction
        :param y: float direction
        """
        self._x = x
        self._y = y
        self._array: npt.NDArray[np.float64] = np.array([self.x, self.y], dtype=np.float64)

    def __repr__(self) -> str:
        """
        :return: string containing representation of this class
        """
        return f'x: {self.x}, y: {self.y}'

    def __eq__(self, other: object) -> bool:
        """
        Compare other object with this class
        :param other: object
        :return: true if other state vector is the same as self
        """
        if not isinstance(other, StateVector2D):
            return NotImplemented
        return bool(np.array_equal(self.array, other.array))

    @property
    def array(self) -> npt.NDArray[np.float64]:
        """
        Convert vector to array
        :return: array containing [x, y]
        """
        return self._array

    @array.setter
    def array(self, other: npt.NDArray[np.float64]) -> None:
        """Custom setter so that the object is not corrupted."""
        self._array = other
        self._x = other[0]
        self._y = other[1]

    @property
    def x(self) -> float:
        """
        :return: x float state
        """
        return self._x

    @x.setter
    def x(self, x: float) -> None:
        """Custom setter so that the object is not corrupted."""
        self._x = x
        self._array[0] = x

    @property
    def y(self) -> float:
        """
        :return: y float state
        """
        return self._y

    @y.setter
    def y(self, y: float) -> None:
        """Custom setter so that the object is not corrupted."""
        self._y = y
        self._array[1] = y

    def magnitude(self) -> float:
        """
        :return: magnitude of vector
        """
        return float(np.hypot(self.x, self.y))

def __eq__(self, other: object) -> bool:
    """
        Compare other object with this class
        :param other: object
        :return: true if other state vector is the same as self
        """
    if not isinstance(other, StateVector2D):
        return NotImplemented
    return bool(np.array_equal(self.array, other.array))

class AgentTemporalState:
    """
    Actor with current, multimodal future as well as past trajectory.
        The future trajectory probabilities have to sum up to 1.0.
        The past trajectory is only single modal with mode probability 1.0.
        The last waypoint in past trajectory has to be the same as current position (we check only timestamp).
    """

    def __init__(self, initial_time_stamp: TimePoint, predictions: Optional[List[PredictedTrajectory]]=None, past_trajectory: Optional[PredictedTrajectory]=None):
        """
        Initialize actor temporal state which has past as well as future trajectory
        :param initial_time_stamp: time stamp the current detections
        :param predictions: future multimodal trajectory
        :param past_trajectory: past trajectory transversed
        """
        self._initial_time_stamp = initial_time_stamp
        self.predictions: List[PredictedTrajectory] = predictions if predictions is not None else []
        self.past_trajectory = past_trajectory

    @property
    def previous_state(self) -> Optional[Waypoint]:
        """
        :return: None if agent's previous state does not exists, otherwise return previous state
        """
        if not self.past_trajectory or len(self.past_trajectory.valid_waypoints) < 2:
            return None
        return self.past_trajectory.waypoints[-2]

    @property
    def predictions(self) -> List[PredictedTrajectory]:
        """
        Getter for agents predicted trajectories
        :return: Trajectories
        """
        return self._predictions

    @predictions.setter
    def predictions(self, predicted_trajectories: List[PredictedTrajectory]) -> None:
        """
        Setter for predicted trajectories, checks if the listed probabilities sum to one.
        :param predicted_trajectories: List of Predicted trajectories
        """
        if not predicted_trajectories:
            self._predictions = predicted_trajectories
            return
        probability_sum = sum((prediction.probability for prediction in predicted_trajectories))
        if not abs(probability_sum - 1) < 1e-06 and predicted_trajectories:
            raise ValueError(f'The provided trajectory probabilities did not sum to one, but to {probability_sum:.2f}!')
        self._predictions = predicted_trajectories

    @property
    def past_trajectory(self) -> Optional[PredictedTrajectory]:
        """
        Getter for agents predicted trajectories
        :return: Trajectories
        """
        return self._past_trajectory

    @past_trajectory.setter
    def past_trajectory(self, past_trajectory: Optional[PredictedTrajectory]) -> None:
        """
        Setter for predicted trajectories, checks if the listed probabilities sum to one.
        :param past_trajectory: Driven Trajectory
        """
        if not past_trajectory:
            self._past_trajectory = past_trajectory
            return
        last_waypoint = past_trajectory.waypoints[-1]
        if not last_waypoint:
            raise RuntimeError("Last waypoint represents current agent's state, this should not be None!")
        if last_waypoint.time_point != self._initial_time_stamp:
            raise ValueError(f'The provided trajectory does not end at current agent state! {last_waypoint.time_us} != {self._initial_time_stamp}')
        self._past_trajectory = past_trajectory

@predictions.setter
def predictions(self, predicted_trajectories: List[PredictedTrajectory]) -> None:
    """
        Setter for predicted trajectories, checks if the listed probabilities sum to one.
        :param predicted_trajectories: List of Predicted trajectories
        """
    if not predicted_trajectories:
        self._predictions = predicted_trajectories
        return
    probability_sum = sum((prediction.probability for prediction in predicted_trajectories))
    if not abs(probability_sum - 1) < 1e-06 and predicted_trajectories:
        raise ValueError(f'The provided trajectory probabilities did not sum to one, but to {probability_sum:.2f}!')
    self._predictions = predicted_trajectories

class TestOrientedBox(unittest.TestCase):
    """Tests OrientedBox class"""

    def setUp(self) -> None:
        """Creates sample parameters for testing"""
        self.center = StateSE2(1, 2, m.pi / 8)
        self.length = 4.0
        self.width = 2.0
        self.height = 1.5
        self.expected_vertices = [(2.47, 3.69), (-1.23, 2.16), (-0.47, 0.31), (3.23, 1.84)]

    def test_construction(self) -> None:
        """Tests that the object is created correctly, including the polygon representing its geometry."""
        test_box = OrientedBox(self.center, self.length, self.width, self.height)
        self.assertTrue(self.center == test_box.center)
        self.assertEqual(self.length, test_box.length)
        self.assertEqual(self.width, test_box.width)
        self.assertEqual(self.height, test_box.height)
        self.assertFalse('geometry' in test_box.__dict__)
        for vertex, expected_vertex in zip(test_box.geometry.exterior.coords, self.expected_vertices):
            self.assertAlmostEqual(vertex[0], expected_vertex[0], 2)
            self.assertAlmostEqual(vertex[1], expected_vertex[1], 2)
        self.assertTrue('geometry' in test_box.__dict__)

def test_construction(self) -> None:
    """Tests that the object is created correctly, including the polygon representing its geometry."""
    test_box = OrientedBox(self.center, self.length, self.width, self.height)
    self.assertTrue(self.center == test_box.center)
    self.assertEqual(self.length, test_box.length)
    self.assertEqual(self.width, test_box.width)
    self.assertEqual(self.height, test_box.height)
    self.assertFalse('geometry' in test_box.__dict__)
    for vertex, expected_vertex in zip(test_box.geometry.exterior.coords, self.expected_vertices):
        self.assertAlmostEqual(vertex[0], expected_vertex[0], 2)
        self.assertAlmostEqual(vertex[1], expected_vertex[1], 2)
    self.assertTrue('geometry' in test_box.__dict__)

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

def principal_value(angle: Union[float, int, npt.NDArray[np.float64]], min_: float=-np.pi) -> Union[float, npt.NDArray[np.float64]]:
    """
    Wrap heading angle in to specified domain (multiples of 2 pi alias),
    ensuring that the angle is between min_ and min_ + 2 pi. This function raises an error if the angle is infinite
    :param angle: rad
    :param min_: minimum domain for angle (rad)
    :return angle wrapped to [min_, min_ + 2 pi).
    """
    assert np.all(np.isfinite(angle)), 'angle is not finite'
    lhs = (angle - min_) % (2 * np.pi) + min_
    return lhs

def _validate_waypoints(waypoints: List[InterpolatableState]) -> None:
    """
    Make sure that waypoints are valid for interpolation
        raise in case they are empty or they are not monotonically increasing
    :param waypoints: list of waypoints to be interpolated
    """
    if not waypoints:
        raise RuntimeError('There are no waypoints!')
    if not np.all(np.diff([w.time_us for w in waypoints]) > 0):
        raise ValueError(f'The waypoints are not monotonically increasing: {[w.time_us for w in waypoints]}!')

@dataclass(frozen=True)
class Color:
    """
    Represents a color.
    """
    red: float
    green: float
    blue: float
    alpha: float
    serialize_to: ColorType = ColorType.FLOAT

    def __post_init__(self) -> None:
        """
        Checks that the component values are floats in range 0-1.
        """
        for dim in fields(self)[:4]:
            component = getattr(self, dim.name)
            if not isinstance(component, (float, int, integer)):
                raise TypeError(f'TypeError: Invalid type {type(component)} for color field {dim.name}. Expected type float.')
            if component < 0.0 or component > 1.0:
                raise ValueError(f'ValueError: Invalid value {component} for color field {dim.name}. Expected value in range 0.0-1.0.')

    def _serialize(self, value: float) -> float:
        """
        Converts the components into correct value before serializing
        """
        if self.serialize_to == ColorType.INT:
            return int(value * 255)
        else:
            return value

    def __iter__(self) -> Iterator[float]:
        """
        Return RGBA components in order red, green, blue, alpha
        """
        return iter((self._serialize(x) for x in astuple(self)[:4]))

    def __mul__(self, other: float) -> Color:
        """
        Return a new color with RGBA components multiplied by other. The resulting values are clipped between 0 and 1.
        :param other: Factor to multiply color by.
        :return: A new Color instance with values multiplied by other, clipped between 0 and 1.
        """
        if isinstance(other, (float, int)):
            return Color(*[clip(component * other, 0, 1) for component in astuple(self)[:4]] + [self.serialize_to])
        else:
            raise TypeError(f"TypeError: unsupported operand type(s) for *: 'Color' and '{type(other)}')")

    def __rmul__(self, other: float) -> Color:
        """
        Return a new color with RGBA components multiplied by other. The resulting values are clipped between 0 and 1.
        :param other: Factor to multiply color by.
        :return: A new Color instance with values multiplied by other, clipped between 0 and 1.
        """
        return self.__mul__(other)

    def to_list(self) -> List[float]:
        """
        Return RGBA components as a list of ints/floats depending on the value of serialize_to.
        :return: list of floats representing red, green, blue and alpha values.
        """
        return [component for component in self]

def __post_init__(self) -> None:
    """
        Checks that the component values are floats in range 0-1.
        """
    for dim in fields(self)[:4]:
        component = getattr(self, dim.name)
        if not isinstance(component, (float, int, integer)):
            raise TypeError(f'TypeError: Invalid type {type(component)} for color field {dim.name}. Expected type float.')
        if component < 0.0 or component > 1.0:
            raise ValueError(f'ValueError: Invalid value {component} for color field {dim.name}. Expected value in range 0.0-1.0.')

class SceneStructure:
    """
    Base class for scene data.
    """

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """
        Iterates through attributes. Used to convert class into dict for serialization.
        Similar to dataclasses.asdict, except it skips some attributes and can convert some of its attributes to dicts too.
        """
        for dim in fields(self):
            value = getattr(self, dim.name)
            if value is None:
                continue
            elif issubclass(type(value), SceneStructure):
                yield (dim.name, dict(value))
            elif isinstance(value, dict):
                yield (dim.name, {x: dict(value[x]) if issubclass(type(value[x]), SceneStructure) else value[x] for x in value})
            elif isinstance(value, Iterable):
                yield (dim.name, [dict(v) if issubclass(type(v), SceneStructure) else v for v in value])
            else:
                yield (dim.name, value)

def __iter__(self) -> Iterator[Tuple[str, Any]]:
    """
        Iterates through attributes. Used to convert class into dict for serialization.
        Similar to dataclasses.asdict, except it skips some attributes and can convert some of its attributes to dicts too.
        """
    for dim in fields(self):
        value = getattr(self, dim.name)
        if value is None:
            continue
        elif issubclass(type(value), SceneStructure):
            yield (dim.name, dict(value))
        elif isinstance(value, dict):
            yield (dim.name, {x: dict(value[x]) if issubclass(type(value[x]), SceneStructure) else value[x] for x in value})
        elif isinstance(value, Iterable):
            yield (dim.name, [dict(v) if issubclass(type(v), SceneStructure) else v for v in value])
        else:
            yield (dim.name, value)

def worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
    """
    Map a list of objects through a worker.
    :param worker: Worker pool to use for parallelization.
    :param fn: Function to use when mapping.
    :param input_objects: List of objects to map.
    :return: List of mapped objects.
    """
    if worker.number_of_threads == 0:
        return fn(input_objects)
    object_chunks = chunk_list(input_objects, worker.number_of_threads)
    scattered_objects = worker.map(Task(fn=fn), object_chunks)
    output_objects = [result for results in scattered_objects for result in results]
    return output_objects

class TestWorkerSquareNumbersTask(unittest.TestCase):
    """Class to run all workers on a simple worker task, squaring a list of numbers."""

    def setUp(self) -> None:
        """
        Instantiate all workers we want to check, not just numerically but for correct bazel BUILD file setup.
        """
        self.worker_arg_tuples: List[Tuple[WorkerPool, Dict[str, Any]]] = [(SingleMachineParallelExecutor, {}), (SingleMachineParallelExecutor, {'use_process_pool': True}), (RayDistributed, {'threads_per_node': 2}), (Sequential, {})]
        self.number_of_tasks = 10

    def test_square_numbers_task(self) -> None:
        """Make sure all workers can correctly execute map to square a list of numbers."""
        task_list = [x for x in range(self.number_of_tasks)]
        expected_result = [x ** 2 for x in task_list]
        for worker_arg_tuple in self.worker_arg_tuples:
            worker = worker_arg_tuple[0](**worker_arg_tuple[1])
            worker_result = worker.map(Task(fn=square_fn), task_list)
            self.assertEqual(worker_result, expected_result)
            if isinstance(worker, RayDistributed):
                worker.shutdown()

def test_square_numbers_task(self) -> None:
    """Make sure all workers can correctly execute map to square a list of numbers."""
    task_list = [x for x in range(self.number_of_tasks)]
    expected_result = [x ** 2 for x in task_list]
    for worker_arg_tuple in self.worker_arg_tuples:
        worker = worker_arg_tuple[0](**worker_arg_tuple[1])
        worker_result = worker.map(Task(fn=square_fn), task_list)
        self.assertEqual(worker_result, expected_result)
        if isinstance(worker, RayDistributed):
            worker.shutdown()

class TestWorkerPool(unittest.TestCase):
    """Unittest class for WorkerPool"""

    def setUp(self) -> None:
        """
        Setup worker
        """
        self.worker = RayDistributed(debug_mode=True)

    def test_ray(self) -> None:
        """
        Test ray GPU allocation
        """
        num_calls = 3
        num_gpus = 1
        output = self.worker.map(Task(fn=function_to_load_model, num_gpus=num_gpus), num_calls * [1])
        for gpu_available, num_threads in output:
            self.assertTrue(gpu_available)
            self.assertGreater(num_threads, 0)

def test_ray(self) -> None:
    """
        Test ray GPU allocation
        """
    num_calls = 3
    num_gpus = 1
    output = self.worker.map(Task(fn=function_to_load_model, num_gpus=num_gpus), num_calls * [1])
    for gpu_available, num_threads in output:
        self.assertTrue(gpu_available)
        self.assertGreater(num_threads, 0)

class TestChunkSplitter(unittest.TestCase):
    """Unittest class for splitters to chunks"""

    def validate_chunks(self, chunks: List[List[Any]]) -> None:
        """Validate splitter chunks."""
        self.assertTrue(all([len(chunk) > 0 for chunk in chunks]))

    def test_chunk_splitter_more_data_than_number_of_chunks(self) -> None:
        """Test Chunk splitter where"""
        num_variables = 108
        num_chunks = 32
        data = list(range(1, num_variables + 1))
        chunks = chunk_list(data, num_chunks)
        self.validate_chunks(chunks)
        self.assertEqual(len(chunks), num_chunks)
        self.assertLessEqual(max(np.abs(np.diff([len(chunk) for chunk in chunks]))), 1)

    def test_chunk_splitter(self) -> None:
        """Test Chunk splitter where data size is smaller than number of chunks"""
        num_variables = 20
        num_chunks = 32
        data = list(range(1, num_variables + 1))
        chunks = chunk_list(data, num_chunks)
        self.validate_chunks(chunks)
        self.assertLessEqual(max(np.abs(np.diff([len(chunk) for chunk in chunks]))), 1)

    def test_chunk_splitter_same_size(self) -> None:
        """Test Chunk splitter where data and number chunks is the same"""
        num_chunks = 32
        num_variables = num_chunks
        data = list(range(1, num_variables + 1))
        chunks = chunk_list(data, num_chunks)
        self.validate_chunks(chunks)
        self.assertTrue(all([len(chunk) == 1 for chunk in chunks]))

def validate_chunks(self, chunks: List[List[Any]]) -> None:
    """Validate splitter chunks."""
    self.assertTrue(all([len(chunk) > 0 for chunk in chunks]))

def test_chunk_splitter_more_data_than_number_of_chunks(self) -> None:
    """Test Chunk splitter where"""
    num_variables = 108
    num_chunks = 32
    data = list(range(1, num_variables + 1))
    chunks = chunk_list(data, num_chunks)
    self.validate_chunks(chunks)
    self.assertEqual(len(chunks), num_chunks)
    self.assertLessEqual(max(np.abs(np.diff([len(chunk) for chunk in chunks]))), 1)

def test_chunk_splitter(self) -> None:
    """Test Chunk splitter where data size is smaller than number of chunks"""
    num_variables = 20
    num_chunks = 32
    data = list(range(1, num_variables + 1))
    chunks = chunk_list(data, num_chunks)
    self.validate_chunks(chunks)
    self.assertLessEqual(max(np.abs(np.diff([len(chunk) for chunk in chunks]))), 1)

def test_chunk_splitter_same_size(self) -> None:
    """Test Chunk splitter where data and number chunks is the same"""
    num_chunks = 32
    num_variables = num_chunks
    data = list(range(1, num_variables + 1))
    chunks = chunk_list(data, num_chunks)
    self.validate_chunks(chunks)
    self.assertTrue(all([len(chunk) == 1 for chunk in chunks]))

class TestWorkerPool(unittest.TestCase):
    """Unittest class for WorkerPool"""

    def setUp(self) -> None:
        """Set up basic config."""
        self.lhs_matrix: npt.NDArray[np.float32] = np.array([[1, 2, 4], [2, 3, 4]])
        self.rhs_matrix: npt.NDArray[np.float32] = np.array([[2, 3, 4], [2, 5, 4]]).T
        self.target: npt.NDArray[np.float32] = np.array([[24, 28], [29, 35]])
        self.workers = [Sequential(), RayDistributed(debug_mode=True), SingleMachineParallelExecutor(), SingleMachineParallelExecutor(use_process_pool=True)]

    def test_task(self) -> None:
        """Test Task whether a function can be called"""

        def add_inputs(input1: float, input2: float) -> float:
            """
            :return: input1 + input2 + 1
            """
            return input1 + input2 + 1
        task = Task(fn=add_inputs)
        self.assertEqual(task(10, 20), 31)

    def test_workers(self) -> None:
        """Tests the sequential worker."""
        for worker in self.workers:
            if not isinstance(worker, Sequential):
                self.check_worker_submit(worker)
            self.check_worker_map(worker)

    def check_worker_map(self, worker: WorkerPool) -> None:
        """
        Check whether worker.map passes all checks.
        :param worker: to be tested.
        """
        task = Task(fn=matrix_multiplication)
        result = worker.map(task, self.lhs_matrix, self.rhs_matrix)
        self.assertEqual(len(result), 1)
        self.validate_result(result)
        number_of_functions = 10
        result = worker.map(task, [self.lhs_matrix] * number_of_functions, self.rhs_matrix)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)
        result = worker.map(task, self.lhs_matrix, [self.rhs_matrix] * number_of_functions)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)
        result = worker.map(task, [self.lhs_matrix] * number_of_functions, [self.rhs_matrix] * number_of_functions)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)

    def check_worker_submit(self, worker: WorkerPool) -> None:
        """
        Check whether worker.submit passes all checks
        :param worker: to be tested
        """
        task = Task(fn=matrix_multiplication)
        result = worker.submit(task, self.lhs_matrix, self.rhs_matrix).result()
        self.assertTrue((result == self.target).all())

    def validate_result(self, results: List[npt.NDArray[np.float32]]) -> None:
        """
        Validate that result from np.dot matched expectations
        :param results: List of results from worker
        """
        for result in results:
            self.assertTrue((result == self.target).all())

    def test_splitter(self) -> None:
        """
        Test chunk splitter
        """
        num_chunks = 10
        chunks = chunk_list([1] * num_chunks, num_chunks)
        self.assertEqual(len(chunks), num_chunks)
        chunks = chunk_list([1, 2, 3, 4, 5], 2)
        self.assertEqual(len(chunks), 2)

def test_task(self) -> None:
    """Test Task whether a function can be called"""

    def add_inputs(input1: float, input2: float) -> float:
        """
            :return: input1 + input2 + 1
            """
        return input1 + input2 + 1
    task = Task(fn=add_inputs)
    self.assertEqual(task(10, 20), 31)

def check_worker_map(self, worker: WorkerPool) -> None:
    """
        Check whether worker.map passes all checks.
        :param worker: to be tested.
        """
    task = Task(fn=matrix_multiplication)
    result = worker.map(task, self.lhs_matrix, self.rhs_matrix)
    self.assertEqual(len(result), 1)
    self.validate_result(result)
    number_of_functions = 10
    result = worker.map(task, [self.lhs_matrix] * number_of_functions, self.rhs_matrix)
    self.assertEqual(len(result), number_of_functions)
    self.validate_result(result)
    result = worker.map(task, self.lhs_matrix, [self.rhs_matrix] * number_of_functions)
    self.assertEqual(len(result), number_of_functions)
    self.validate_result(result)
    result = worker.map(task, [self.lhs_matrix] * number_of_functions, [self.rhs_matrix] * number_of_functions)
    self.assertEqual(len(result), number_of_functions)
    self.validate_result(result)

def check_worker_submit(self, worker: WorkerPool) -> None:
    """
        Check whether worker.submit passes all checks
        :param worker: to be tested
        """
    task = Task(fn=matrix_multiplication)
    result = worker.submit(task, self.lhs_matrix, self.rhs_matrix).result()
    self.assertTrue((result == self.target).all())

def validate_result(self, results: List[npt.NDArray[np.float32]]) -> None:
    """
        Validate that result from np.dot matched expectations
        :param results: List of results from worker
        """
    for result in results:
        self.assertTrue((result == self.target).all())

def test_splitter(self) -> None:
    """
        Test chunk splitter
        """
    num_chunks = 10
    chunks = chunk_list([1] * num_chunks, num_chunks)
    self.assertEqual(len(chunks), num_chunks)
    chunks = chunk_list([1, 2, 3, 4, 5], 2)
    self.assertEqual(len(chunks), 2)

class OccupancyMapTests(unittest.TestCase):
    """Tests implementation of OccupancyMap"""

    def setUp(self) -> None:
        """Test setup"""
        self.p1 = Polygon([(0, 0), (0, 2), (3, 2), (3, 0)])
        self.p2 = Polygon([(2, 0), (2, 4), (3, 4), (3, 0)])
        self.p3 = Polygon([(4, 0), (4, 2), (5, 2), (5, 0)])
        self.p4 = Polygon([(0, 4), (0, 5), (1.5, 5), (1.5, 4)])
        self.l1 = LineString([(0, 3), (4, 3), (4, 1)])

    def test_intersects_polygon(self):
        """Tests polygon-polygon intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.p2)
            assert not intersection.is_empty()
            intersection = occupancy_map.intersects(self.p3)
            assert intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring(self):
        """Tests polygon-linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1)
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1)
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring_buffered(self):
        """Tests polygon-buffered linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('4', self.p4.buffer(0.5, cap_style=2))
            intersection = occupancy_map.intersects(self.l1.buffer(0.1, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_insert_get_set(self):
        """Tests the expected behavior of get and set"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            assert occupancy_map.size == 1
            occupancy_map.insert('2', self.p3)
            assert occupancy_map.size == 2
            assert self.p3 == occupancy_map.get('2')
            occupancy_map.set('2', self.p2)
            assert self.p2 == occupancy_map.get('2')
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_nearest_entry(self):
        """Tests expected behavior of get_nearest_entry"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            nearest_id, nearest_polygon, distance = occupancy_map.get_nearest_entry_to('0')
            self.assertEqual(nearest_id, '2')
            self.assertEqual(nearest_polygon, self.p4)
            self.assertEqual(distance, 0.5)
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_all(self):
        """Tests the expected behavior of get_all_ids"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            ids = occupancy_map.get_all_ids()
            assert set(ids) == {'0', '1', '2'}
            assert set(ids) != {'0', '1', '3'}
            geoms = occupancy_map.get_all_geometries()
            for actual, expect in zip(geoms, [self.p2, self.p3, self.p4]):
                assert actual == expect
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

def setUp(self) -> None:
    """Test setup"""
    self.p1 = Polygon([(0, 0), (0, 2), (3, 2), (3, 0)])
    self.p2 = Polygon([(2, 0), (2, 4), (3, 4), (3, 0)])
    self.p3 = Polygon([(4, 0), (4, 2), (5, 2), (5, 0)])
    self.p4 = Polygon([(0, 4), (0, 5), (1.5, 5), (1.5, 4)])
    self.l1 = LineString([(0, 3), (4, 3), (4, 1)])

def _convert_curvature_profile_to_steering_profile(curvature_profile: DoubleMatrix, discretization_time: float, wheel_base: float) -> Tuple[DoubleMatrix, DoubleMatrix]:
    """
    Converts from a curvature profile to the corresponding steering profile.
    We assume a kinematic bicycle model where curvature = tan(steering_angle) / wheel_base.
    For simplicity, we just use finite differences to determine steering rate.
    :param curvature_profile: [rad] Curvature trajectory to convert.
    :param discretization_time: [s] Time discretization used for integration.
    :param wheel_base: [m] The vehicle wheelbase parameter required for conversion.
    :return: The [rad] steering angle and [rad/s] steering rate (derivative) profiles.
    """
    assert discretization_time > 0.0, 'Discretization time must be positive.'
    assert wheel_base > 0.0, "The vehicle's wheelbase length must be positive."
    steering_angle_profile = np.arctan(wheel_base * curvature_profile)
    steering_rate_profile = np.diff(steering_angle_profile) / discretization_time
    return (steering_angle_profile, steering_rate_profile)

class TestTrackerUtils(unittest.TestCase):
    """
    Tests tracker utils, including least squares fit of kinematic states given poses.
    Throughout, we assume a kinematic bicycle model as the base dynamics model.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.test_discretization_time = 0.2
        self.least_squares_penalty = 1e-10
        self.proximity_rtol = 1e-06
        self.proximity_atol = 1e-08
        self.moving_velocity_threshold = 0.1
        self.assert_allclose = partial(np_test.assert_allclose, rtol=self.proximity_rtol, atol=self.proximity_atol)
        self.test_wheel_base = 3.0
        self.initial_pose: DoubleMatrix = np.array([5.0, 1.0, 0.1], dtype=np.float64)
        self.initial_velocity = 3.0
        self.initial_curvature = 0.0
        max_acceleration = 3.0
        max_curvature_rate = 0.05
        input_length = 10
        self.input_profiles = {}
        acceleration_profile_dict = _make_input_profiles(key_prefix='accel', magnitude=max_acceleration, length=input_length)
        curvature_rate_profile_dict = _make_input_profiles(key_prefix='curv_rate', magnitude=max_curvature_rate, length=input_length)
        for acceleration_profile_name, acceleration_profile in acceleration_profile_dict.items():
            for curvature_rate_profile_name, curvature_rate_profile in curvature_rate_profile_dict.items():
                poses, velocities, curvatures = _integrate_acceleration_and_curvature_profile(initial_pose=self.initial_pose, initial_velocity=self.initial_velocity, initial_curvature=self.initial_curvature, acceleration_profile=acceleration_profile, curvature_rate_profile=curvature_rate_profile, discretization_time=self.test_discretization_time)
                self.input_profiles[f'{acceleration_profile_name}_{curvature_rate_profile_name}'] = {'acceleration': acceleration_profile, 'curvature_rate': curvature_rate_profile, 'poses': poses, 'velocity': velocities, 'curvature': curvatures}

    def test__generate_profile_from_initial_condition_and_derivatives(self) -> None:
        """
        Check that we can correctly integrate derivative profiles.
        We use a loop here to compare against the vectorized implementation.
        """
        for input_profile in self.input_profiles.values():
            velocity_profile = [self.initial_velocity]
            for acceleration in input_profile['acceleration']:
                velocity_profile.append(velocity_profile[-1] + acceleration * self.test_discretization_time)
            self.assert_allclose(velocity_profile, input_profile['velocity'])
            curvature_profile = [self.initial_curvature]
            for curvature_rate in input_profile['curvature_rate']:
                curvature_profile.append(curvature_profile[-1] + curvature_rate * self.test_discretization_time)
            self.assert_allclose(curvature_profile, input_profile['curvature'])

    def test__get_xy_heading_displacements_from_poses(self) -> None:
        """Get displacements and check consistency with original pose trajectory."""
        for input_profile in self.input_profiles.values():
            poses = input_profile['poses']
            xy_displacements, heading_displacements = _get_xy_heading_displacements_from_poses(poses)
            self.assertEqual(len(xy_displacements), len(poses) - 1)
            self.assertEqual(len(heading_displacements), len(poses) - 1)
            x_integrated = _generate_profile_from_initial_condition_and_derivatives(initial_condition=self.initial_pose[0], derivatives=xy_displacements[:, 0], discretization_time=1.0)
            y_integrated = _generate_profile_from_initial_condition_and_derivatives(initial_condition=self.initial_pose[1], derivatives=xy_displacements[:, 1], discretization_time=1.0)
            heading_integrated = _generate_profile_from_initial_condition_and_derivatives(initial_condition=self.initial_pose[2], derivatives=heading_displacements, discretization_time=1.0)
            heading_integrated = principal_value(heading_integrated)
            self.assert_allclose(np.column_stack((x_integrated, y_integrated, heading_integrated)), poses)

    def test__make_banded_difference_matrix(self) -> None:
        """Test that the banded difference matrix has expected structure for different sizes."""
        for test_number_rows in [1, 5, 10]:
            banded_difference_matrix = _make_banded_difference_matrix(test_number_rows)
            self.assertEqual(banded_difference_matrix.shape, (test_number_rows, test_number_rows + 1))
            self.assert_allclose(np.diag(banded_difference_matrix, k=0), -1.0)
            self.assert_allclose(np.diag(banded_difference_matrix, k=1), 1.0)
            removal_mask = np.ones_like(banded_difference_matrix)
            for idx in range(len(removal_mask)):
                removal_mask[idx, idx:idx + 2] = 0.0
            banded_difference_matrix_masked = np.multiply(banded_difference_matrix, removal_mask)
            self.assert_allclose(banded_difference_matrix_masked, 0.0)

    def test__convert_curvature_profile_to_steering_profile(self) -> None:
        """Check consistency of converted steering angle/rate with curvature and pose information."""
        for input_profile in self.input_profiles.values():
            curvature_profile = input_profile['curvature']
            velocity_profile = input_profile['velocity']
            heading_profile = input_profile['poses'][:, 2]
            steering_angle_profile, steering_rate_profile = _convert_curvature_profile_to_steering_profile(curvature_profile=curvature_profile, discretization_time=self.test_discretization_time, wheel_base=self.test_wheel_base)
            self.assertEqual(len(steering_angle_profile), len(curvature_profile))
            self.assertEqual(len(steering_rate_profile), len(curvature_profile) - 1)
            steering_angle_integrated = _generate_profile_from_initial_condition_and_derivatives(initial_condition=steering_angle_profile[0], derivatives=steering_rate_profile, discretization_time=self.test_discretization_time)
            self.assert_allclose(steering_angle_integrated, steering_angle_profile)
            yawrate_profile = velocity_profile * np.tan(steering_angle_profile) / self.test_wheel_base
            heading_integrated = _generate_profile_from_initial_condition_and_derivatives(initial_condition=self.initial_pose[2], derivatives=yawrate_profile, discretization_time=self.test_discretization_time)
            heading_integrated = principal_value(heading_integrated)
            self.assert_allclose(heading_integrated, heading_profile)

    def test__fit_initial_velocity_and_acceleration_profile(self) -> None:
        """
        Test given noiseless data and a small jerk penalty, the least squares speed/acceleration match expected values.
        """
        for input_profile in self.input_profiles.values():
            poses = input_profile['poses']
            xy_displacements, _ = _get_xy_heading_displacements_from_poses(poses)
            heading_profile = poses[:-1, 2]
            initial_velocity, acceleration_profile = _fit_initial_velocity_and_acceleration_profile(xy_displacements=xy_displacements, heading_profile=heading_profile, discretization_time=self.test_discretization_time, jerk_penalty=self.least_squares_penalty)
            velocity_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_velocity, derivatives=acceleration_profile, discretization_time=self.test_discretization_time)
            self.assert_allclose(velocity_profile, input_profile['velocity'])
            self.assert_allclose(acceleration_profile, input_profile['acceleration'])

    def test__fit_initial_curvature_and_curvature_rate_profile(self) -> None:
        """
        Test given noiseless data and a small curvature_rate penalty, the least squares curvature/curvature rate match
        expected values.  A caveat is we exclude cases where ego is stopped and thus curvature estimation is unreliable.
        """
        for input_profile in self.input_profiles.values():
            poses = input_profile['poses']
            velocity_profile = input_profile['velocity']
            _, heading_displacements = _get_xy_heading_displacements_from_poses(poses)
            initial_curvature, curvature_rate_profile = _fit_initial_curvature_and_curvature_rate_profile(heading_displacements=heading_displacements, velocity_profile=velocity_profile, discretization_time=self.test_discretization_time, curvature_rate_penalty=self.least_squares_penalty)
            curvature_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_curvature, derivatives=curvature_rate_profile, discretization_time=self.test_discretization_time)
            moving_mask = (np.abs(velocity_profile) > self.moving_velocity_threshold).astype(np.float64)
            self.assert_allclose(moving_mask * curvature_profile, moving_mask * input_profile['curvature'])
            if np.all(moving_mask > 0.0):
                self.assert_allclose(curvature_rate_profile, input_profile['curvature_rate'])

    def test_compute_steering_angle_feedback(self) -> None:
        """Check that sign of the steering angle feedback makes sense for various initial tracking errors."""
        pose_reference: DoubleMatrix = self.initial_pose
        heading_reference = pose_reference[2]
        lookahead_distance = 10.0
        k_lateral_error = 0.1
        steering_angle_zero_lateral_error = compute_steering_angle_feedback(pose_reference=pose_reference, pose_current=pose_reference, lookahead_distance=lookahead_distance, k_lateral_error=k_lateral_error)
        self.assertEqual(steering_angle_zero_lateral_error, 0.0)
        for lateral_error in [-1.0, 1.0]:
            pose_lateral_error: DoubleMatrix = pose_reference + lateral_error * np.array([-np.sin(heading_reference), np.cos(heading_reference), 0.0])
            steering_angle_lateral_error = compute_steering_angle_feedback(pose_reference=pose_reference, pose_current=pose_lateral_error, lookahead_distance=lookahead_distance, k_lateral_error=k_lateral_error)
            self.assertEqual(-np.sign(lateral_error), np.sign(steering_angle_lateral_error))
        for heading_error in [-0.05, 0.05]:
            steering_angle_heading_error = compute_steering_angle_feedback(pose_reference=pose_reference, pose_current=pose_reference + [0.0, 0.0, heading_error], lookahead_distance=lookahead_distance, k_lateral_error=k_lateral_error)
            self.assertEqual(-np.sign(heading_error), np.sign(steering_angle_heading_error))

    def test_get_velocity_curvature_profiles_with_derivatives_from_poses(self) -> None:
        """
        Test the joint estimation of velocity and curvature, along with their derivatives.
        Since there is overlap with complete_kinematic_state_and_inputs_from_poses,
        we just test for one given input profile and leave the extensive testing for that function.
        """
        test_input_profile = self.input_profiles['accel_cosine_curv_rate_cosine']
        velocity_profile, acceleration_profile, curvature_profile, curvature_rate_profile = get_velocity_curvature_profiles_with_derivatives_from_poses(discretization_time=self.test_discretization_time, poses=test_input_profile['poses'], jerk_penalty=self.least_squares_penalty, curvature_rate_penalty=self.least_squares_penalty)
        self.assert_allclose(velocity_profile, test_input_profile['velocity'])
        self.assert_allclose(acceleration_profile, test_input_profile['acceleration'])
        self.assert_allclose(curvature_profile, test_input_profile['curvature'])
        self.assert_allclose(curvature_rate_profile, test_input_profile['curvature_rate'])
        self.assert_allclose(np.diff(velocity_profile) / self.test_discretization_time, acceleration_profile)
        self.assert_allclose(np.diff(curvature_profile) / self.test_discretization_time, curvature_rate_profile)

    def test_complete_kinematic_state_and_inputs_from_poses(self) -> None:
        """
        Test that the joint estimation of kinematic states and inputs are consistent with expectations.
        Since there is extrapolation involved, we only compare the non-extrapolated values.
        """
        for input_profile in self.input_profiles.values():
            poses = input_profile['poses']
            velocity_profile = input_profile['velocity']
            acceleration_profile = input_profile['acceleration']
            curvature_profile = input_profile['curvature']
            kinematic_states, kinematic_inputs = complete_kinematic_state_and_inputs_from_poses(discretization_time=self.test_discretization_time, wheel_base=self.test_wheel_base, poses=poses, jerk_penalty=self.least_squares_penalty, curvature_rate_penalty=self.least_squares_penalty)
            velocity_fit = kinematic_states[:-1, 3]
            self.assert_allclose(velocity_fit, velocity_profile)
            acceleration_fit = kinematic_inputs[:-1, 0]
            self.assert_allclose(acceleration_fit, acceleration_profile)
            steering_angle_expected, steering_rate_expected = _convert_curvature_profile_to_steering_profile(curvature_profile=curvature_profile, discretization_time=self.test_discretization_time, wheel_base=self.test_wheel_base)
            moving_mask = (np.abs(velocity_profile) > self.moving_velocity_threshold).astype(np.float64)
            steering_angle_fit = kinematic_states[:-1, 4]
            self.assert_allclose(moving_mask * steering_angle_fit, moving_mask * steering_angle_expected)
            if np.all(moving_mask > 0.0):
                steering_rate_fit = kinematic_inputs[:-1, 1]
                self.assert_allclose(steering_rate_fit, steering_rate_expected)

    def test_get_interpolated_reference_trajectory_poses(self) -> None:
        """
        Test that we can interpolate a trajectory with constant discretization time and extract poses.
        """
        scenario = MockAbstractScenario()
        trajectory = InterpolatedTrajectory(list(scenario.get_expert_ego_trajectory()))
        expected_num_steps = 1 + int((trajectory.end_time.time_s - trajectory.start_time.time_s) / self.test_discretization_time)
        times_s, poses = get_interpolated_reference_trajectory_poses(trajectory, self.test_discretization_time)
        self.assertEqual(times_s.shape, (expected_num_steps,))
        self.assertEqual(poses.shape, (expected_num_steps, 3))
        self.assertTrue(np.all(times_s >= trajectory.start_time.time_s))
        self.assertTrue(np.all(times_s <= trajectory.end_time.time_s))
        self.assert_allclose(np.diff(times_s), self.test_discretization_time)

def test_complete_kinematic_state_and_inputs_from_poses(self) -> None:
    """
        Test that the joint estimation of kinematic states and inputs are consistent with expectations.
        Since there is extrapolation involved, we only compare the non-extrapolated values.
        """
    for input_profile in self.input_profiles.values():
        poses = input_profile['poses']
        velocity_profile = input_profile['velocity']
        acceleration_profile = input_profile['acceleration']
        curvature_profile = input_profile['curvature']
        kinematic_states, kinematic_inputs = complete_kinematic_state_and_inputs_from_poses(discretization_time=self.test_discretization_time, wheel_base=self.test_wheel_base, poses=poses, jerk_penalty=self.least_squares_penalty, curvature_rate_penalty=self.least_squares_penalty)
        velocity_fit = kinematic_states[:-1, 3]
        self.assert_allclose(velocity_fit, velocity_profile)
        acceleration_fit = kinematic_inputs[:-1, 0]
        self.assert_allclose(acceleration_fit, acceleration_profile)
        steering_angle_expected, steering_rate_expected = _convert_curvature_profile_to_steering_profile(curvature_profile=curvature_profile, discretization_time=self.test_discretization_time, wheel_base=self.test_wheel_base)
        moving_mask = (np.abs(velocity_profile) > self.moving_velocity_threshold).astype(np.float64)
        steering_angle_fit = kinematic_states[:-1, 4]
        self.assert_allclose(moving_mask * steering_angle_fit, moving_mask * steering_angle_expected)
        if np.all(moving_mask > 0.0):
            steering_rate_fit = kinematic_inputs[:-1, 1]
            self.assert_allclose(steering_rate_fit, steering_rate_expected)

def test_get_interpolated_reference_trajectory_poses(self) -> None:
    """
        Test that we can interpolate a trajectory with constant discretization time and extract poses.
        """
    scenario = MockAbstractScenario()
    trajectory = InterpolatedTrajectory(list(scenario.get_expert_ego_trajectory()))
    expected_num_steps = 1 + int((trajectory.end_time.time_s - trajectory.start_time.time_s) / self.test_discretization_time)
    times_s, poses = get_interpolated_reference_trajectory_poses(trajectory, self.test_discretization_time)
    self.assertEqual(times_s.shape, (expected_num_steps,))
    self.assertEqual(poses.shape, (expected_num_steps, 3))
    self.assertTrue(np.all(times_s >= trajectory.start_time.time_s))
    self.assertTrue(np.all(times_s <= trajectory.end_time.time_s))
    self.assert_allclose(np.diff(times_s), self.test_discretization_time)

class TestLQRTracker(unittest.TestCase):
    """
    Tests LQR Tracker.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.initial_time_point = TimePoint(0)
        self.scenario = MockAbstractScenario(initial_time_us=self.initial_time_point)
        self.trajectory = InterpolatedTrajectory(list(self.scenario.get_expert_ego_trajectory()))
        self.sampling_time = 0.5
        self.tracker = LQRTracker(q_longitudinal=[10.0], r_longitudinal=[1.0], q_lateral=[1.0, 10.0, 0.0], r_lateral=[1.0], discretization_time=0.1, tracking_horizon=10, jerk_penalty=0.0001, curvature_rate_penalty=0.01, stopping_proportional_gain=0.5, stopping_velocity=0.2)

    def test_track_trajectory(self) -> None:
        """Ensure we are able to run track trajectory using LQR."""
        dynamic_state = self.tracker.track_trajectory(current_iteration=SimulationIteration(self.initial_time_point, 0), next_iteration=SimulationIteration(TimePoint(int(self.sampling_time * 1000000.0)), 1), initial_state=self.scenario.initial_ego_state, trajectory=self.trajectory)
        self.assertIsInstance(dynamic_state._rear_axle_to_center_dist, (int, float))
        self.assertIsInstance(dynamic_state.rear_axle_velocity_2d.x, (int, float))
        self.assertIsInstance(dynamic_state.rear_axle_velocity_2d.y, (int, float))
        self.assertIsInstance(dynamic_state.rear_axle_acceleration_2d.x, (int, float))
        self.assertIsInstance(dynamic_state.rear_axle_acceleration_2d.y, (int, float))
        self.assertIsInstance(dynamic_state.tire_steering_rate, (int, float))
        self.assertGreater(dynamic_state._rear_axle_to_center_dist, 0.0)
        self.assertEqual(dynamic_state.rear_axle_acceleration_2d.y, 0.0)

    def test__compute_initial_velocity_and_lateral_state(self) -> None:
        """
        This essentially checks that our projection to vehicle/Frenet frame works by reconstructing specified errors.
        """
        current_iteration = SimulationIteration(self.initial_time_point, 0)
        base_initial_state = self.trajectory.get_state_at_time(self.initial_time_point)
        base_pose_rear_axle = base_initial_state.car_footprint.rear_axle
        test_lateral_errors = [-3.0, 3.0]
        test_heading_errors = [-0.1, 0.1]
        test_longitudinal_errors = [-3.0, 3.0]
        error_product = itertools.product(test_lateral_errors, test_heading_errors, test_longitudinal_errors)
        for lateral_error, heading_error, longitudinal_error in error_product:
            theta = base_pose_rear_axle.heading
            delta_x = longitudinal_error * np.cos(theta) - lateral_error * np.sin(theta)
            delta_y = longitudinal_error * np.sin(theta) + lateral_error * np.cos(theta)
            perturbed_pose_rear_axle = StateSE2(x=base_pose_rear_axle.x + delta_x, y=base_pose_rear_axle.y + delta_y, heading=theta + heading_error)
            perturbed_car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=perturbed_pose_rear_axle, vehicle_parameters=base_initial_state.car_footprint.vehicle_parameters)
            perturbed_initial_state = EgoState(car_footprint=perturbed_car_footprint, dynamic_car_state=base_initial_state.dynamic_car_state, tire_steering_angle=base_initial_state.tire_steering_angle, is_in_auto_mode=base_initial_state.is_in_auto_mode, time_point=base_initial_state.time_point)
            initial_velocity, initial_lateral_state_vector = self.tracker._compute_initial_velocity_and_lateral_state(current_iteration=current_iteration, initial_state=perturbed_initial_state, trajectory=self.trajectory)
            self.assertEqual(initial_velocity, base_initial_state.dynamic_car_state.rear_axle_velocity_2d.x)
            np_test.assert_allclose(initial_lateral_state_vector, [lateral_error, heading_error, base_initial_state.tire_steering_angle])

    def test__compute_reference_velocity_and_curvature_profile(self) -> None:
        """
        This test just checks functionality of computing a reference velocity / curvature profile.
        Detailed evaluation of the result is handled in test_tracker_utils and omitted here.
        """
        current_iteration = SimulationIteration(self.initial_time_point, 0)
        reference_velocity, curvature_profile = self.tracker._compute_reference_velocity_and_curvature_profile(current_iteration=current_iteration, trajectory=self.trajectory)
        tracking_horizon = self.tracker._tracking_horizon
        discretization_time = self.tracker._discretization_time
        lookahead_time_point = TimePoint(current_iteration.time_point.time_us + int(1000000.0 * tracking_horizon * discretization_time))
        expected_lookahead_ego_state = self.trajectory.get_state_at_time(lookahead_time_point)
        np_test.assert_allclose(np.sign(reference_velocity), np.sign(expected_lookahead_ego_state.dynamic_car_state.rear_axle_velocity_2d.x))
        self.assertEqual(curvature_profile.shape, (tracking_horizon,))

    def test__stopping_controller(self) -> None:
        """Test P controller for when we are coming to a stop."""
        initial_velocity = 5.0
        accel, steering_rate_cmd = self.tracker._stopping_controller(initial_velocity=initial_velocity, reference_velocity=0.5 * initial_velocity)
        self.assertLess(accel, 0.0)
        self.assertEqual(steering_rate_cmd, 0.0)
        accel, steering_rate_cmd = self.tracker._stopping_controller(initial_velocity=-initial_velocity, reference_velocity=0.0)
        self.assertGreater(accel, 0.0)
        self.assertEqual(steering_rate_cmd, 0.0)

    def test__longitudinal_lqr_controller(self) -> None:
        """Test longitudinal control for simple cases of speed above or below the reference velocity."""
        test_initial_velocities = [2.0, 6.0]
        reference_velocity = float(np.mean(test_initial_velocities))
        for initial_velocity in test_initial_velocities:
            accel_cmd = self.tracker._longitudinal_lqr_controller(initial_velocity=initial_velocity, reference_velocity=reference_velocity)
            np_test.assert_allclose(np.sign(accel_cmd), -np.sign(initial_velocity - reference_velocity))

    def test__lateral_lqr_controller_straight_road(self) -> None:
        """Test how the controller handles non-zero initial tracking error on a straight road."""
        test_velocity_profile = 5.0 * np.ones(self.tracker._tracking_horizon, dtype=np.float64)
        test_curvature_profile = 0.0 * np.ones(self.tracker._tracking_horizon, dtype=np.float64)
        test_lateral_errors = [-3.0, 3.0]
        for lateral_error in test_lateral_errors:
            initial_lateral_state_vector_lateral_only: npt.NDArray[np.float64] = np.array([lateral_error, 0.0, 0.0], dtype=np.float64)
            steering_rate_cmd = self.tracker._lateral_lqr_controller(initial_lateral_state_vector=initial_lateral_state_vector_lateral_only, velocity_profile=test_velocity_profile, curvature_profile=test_curvature_profile)
            np_test.assert_allclose(np.sign(steering_rate_cmd), -np.sign(lateral_error))
        test_heading_errors = [-0.1, 0.1]
        for heading_error in test_heading_errors:
            initial_lateral_state_vector_heading_only: npt.NDArray[np.float64] = np.array([0.0, heading_error, 0.0], dtype=np.float64)
            steering_rate_cmd = self.tracker._lateral_lqr_controller(initial_lateral_state_vector=initial_lateral_state_vector_heading_only, velocity_profile=test_velocity_profile, curvature_profile=test_curvature_profile)
            np_test.assert_allclose(np.sign(steering_rate_cmd), -np.sign(heading_error))

    def test__lateral_lqr_controller_curved_road(self) -> None:
        """Test how the controller handles a curved road with zero initial tracking error and zero steering angle."""
        test_velocity_profile = 5.0 * np.ones(self.tracker._tracking_horizon, dtype=np.float64)
        test_curvature_profile = 0.1 * np.ones(self.tracker._tracking_horizon, dtype=np.float64)
        test_initial_lateral_state_vector: npt.NDArray[np.float64] = np.zeros(3, dtype=np.float64)
        steering_rate_cmd = self.tracker._lateral_lqr_controller(initial_lateral_state_vector=test_initial_lateral_state_vector, velocity_profile=test_velocity_profile, curvature_profile=test_curvature_profile)
        np_test.assert_allclose(np.sign(steering_rate_cmd), np.sign(test_curvature_profile[0]))

    def test__solve_one_step_lqr(self) -> None:
        """Test LQR on a simple linear system."""
        A: npt.NDArray[np.float64] = np.eye(2, dtype=np.float64)
        B: npt.NDArray[np.float64] = np.eye(2, dtype=np.float64)
        g: npt.NDArray[np.float64] = np.zeros(A.shape[0], dtype=np.float64)
        Q: npt.NDArray[np.float64] = np.eye(2, dtype=np.float64)
        R: npt.NDArray[np.float64] = np.eye(2, dtype=np.float64)
        for component_1, component_2 in itertools.product([-5.0, 5.0], [-10.0, 10.0]):
            initial_state: npt.NDArray[np.float64] = np.array([component_1, component_2], dtype=np.float64)
            solution = self.tracker._solve_one_step_lqr(initial_state=initial_state, reference_state=np.zeros_like(initial_state), Q=Q, R=R, A=A, B=B, g=g, angle_diff_indices=[])
            np_test.assert_allclose(np.sign(solution), -np.sign(initial_state))

def test__stopping_controller(self) -> None:
    """Test P controller for when we are coming to a stop."""
    initial_velocity = 5.0
    accel, steering_rate_cmd = self.tracker._stopping_controller(initial_velocity=initial_velocity, reference_velocity=0.5 * initial_velocity)
    self.assertLess(accel, 0.0)
    self.assertEqual(steering_rate_cmd, 0.0)
    accel, steering_rate_cmd = self.tracker._stopping_controller(initial_velocity=-initial_velocity, reference_velocity=0.0)
    self.assertGreater(accel, 0.0)
    self.assertEqual(steering_rate_cmd, 0.0)

@dataclass(frozen=True)
class ILQRSolverParameters:
    """Parameters related to the solver implementation."""
    discretization_time: float
    state_cost_diagonal_entries: List[float]
    input_cost_diagonal_entries: List[float]
    state_trust_region_entries: List[float]
    input_trust_region_entries: List[float]
    max_ilqr_iterations: int
    convergence_threshold: float
    max_solve_time: Optional[float]
    max_acceleration: float
    max_steering_angle: float
    max_steering_angle_rate: float
    min_velocity_linearization: float
    wheelbase: float = get_pacifica_parameters().wheel_base

    def __post_init__(self) -> None:
        """Ensure entries lie in expected bounds and initialize wheelbase."""
        for entry in ['discretization_time', 'max_ilqr_iterations', 'convergence_threshold', 'max_acceleration', 'max_steering_angle', 'max_steering_angle_rate', 'min_velocity_linearization', 'wheelbase']:
            assert getattr(self, entry) > 0.0, f'Field {entry} should be positive.'
        assert self.max_steering_angle < np.pi / 2.0, 'Max steering angle should be less than 90 degrees.'
        if isinstance(self.max_solve_time, float):
            assert self.max_solve_time > 0.0, 'The specified max solve time should be positive.'
        assert np.all([x >= 0 for x in self.state_cost_diagonal_entries]), 'Q matrix must be positive semidefinite.'
        assert np.all([x > 0 for x in self.input_cost_diagonal_entries]), 'R matrix must be positive definite.'
        assert np.all([x > 0 for x in self.state_trust_region_entries]), 'State trust region cost matrix must be positive definite.'
        assert np.all([x > 0 for x in self.input_trust_region_entries]), 'Input trust region cost matrix must be positive definite.'

def __post_init__(self) -> None:
    """Ensure entries lie in expected bounds and initialize wheelbase."""
    for entry in ['discretization_time', 'max_ilqr_iterations', 'convergence_threshold', 'max_acceleration', 'max_steering_angle', 'max_steering_angle_rate', 'min_velocity_linearization', 'wheelbase']:
        assert getattr(self, entry) > 0.0, f'Field {entry} should be positive.'
    assert self.max_steering_angle < np.pi / 2.0, 'Max steering angle should be less than 90 degrees.'
    if isinstance(self.max_solve_time, float):
        assert self.max_solve_time > 0.0, 'The specified max solve time should be positive.'
    assert np.all([x >= 0 for x in self.state_cost_diagonal_entries]), 'Q matrix must be positive semidefinite.'
    assert np.all([x > 0 for x in self.input_cost_diagonal_entries]), 'R matrix must be positive definite.'
    assert np.all([x > 0 for x in self.state_trust_region_entries]), 'State trust region cost matrix must be positive definite.'
    assert np.all([x > 0 for x in self.input_trust_region_entries]), 'Input trust region cost matrix must be positive definite.'

@dataclass(frozen=True)
class ILQRWarmStartParameters:
    """Parameters related to generating a warm start trajectory for iLQR."""
    k_velocity_error_feedback: float
    k_steering_angle_error_feedback: float
    lookahead_distance_lateral_error: float
    k_lateral_error: float
    jerk_penalty_warm_start_fit: float
    curvature_rate_penalty_warm_start_fit: float

    def __post_init__(self) -> None:
        """Ensure entries lie in expected bounds."""
        for entry in ['k_velocity_error_feedback', 'k_steering_angle_error_feedback', 'lookahead_distance_lateral_error', 'k_lateral_error', 'jerk_penalty_warm_start_fit', 'curvature_rate_penalty_warm_start_fit']:
            assert getattr(self, entry) > 0.0, f'Field {entry} should be positive.'

def __post_init__(self) -> None:
    """Ensure entries lie in expected bounds."""
    for entry in ['k_velocity_error_feedback', 'k_steering_angle_error_feedback', 'lookahead_distance_lateral_error', 'k_lateral_error', 'jerk_penalty_warm_start_fit', 'curvature_rate_penalty_warm_start_fit']:
        assert getattr(self, entry) > 0.0, f'Field {entry} should be positive.'

@dataclass(frozen=True)
class ILQRIterate:
    """Contains state, input, and associated Jacobian trajectories needed to perform an update step of iLQR."""
    state_trajectory: DoubleMatrix
    input_trajectory: DoubleMatrix
    state_jacobian_trajectory: DoubleMatrix
    input_jacobian_trajectory: DoubleMatrix

    def __post_init__(self) -> None:
        """Check consistency of dimension across trajectory elements."""
        assert len(self.state_trajectory.shape) == 2, 'Expect state trajectory to be a 2D matrix.'
        state_trajectory_length, state_dim = self.state_trajectory.shape
        assert len(self.input_trajectory.shape) == 2, 'Expect input trajectory to be a 2D matrix.'
        input_trajectory_length, input_dim = self.input_trajectory.shape
        assert input_trajectory_length == state_trajectory_length - 1, 'State trajectory should be 1 longer than the input trajectory.'
        assert self.state_jacobian_trajectory.shape == (input_trajectory_length, state_dim, state_dim)
        assert self.input_jacobian_trajectory.shape == (input_trajectory_length, state_dim, input_dim)
        for field in fields(self):
            assert ~np.any(np.isnan(getattr(self, field.name))), f'{field.name} has unexpected nan values.'

def __post_init__(self) -> None:
    """Check consistency of dimension across trajectory elements."""
    assert len(self.state_trajectory.shape) == 2, 'Expect state trajectory to be a 2D matrix.'
    state_trajectory_length, state_dim = self.state_trajectory.shape
    assert len(self.input_trajectory.shape) == 2, 'Expect input trajectory to be a 2D matrix.'
    input_trajectory_length, input_dim = self.input_trajectory.shape
    assert input_trajectory_length == state_trajectory_length - 1, 'State trajectory should be 1 longer than the input trajectory.'
    assert self.state_jacobian_trajectory.shape == (input_trajectory_length, state_dim, state_dim)
    assert self.input_jacobian_trajectory.shape == (input_trajectory_length, state_dim, input_dim)
    for field in fields(self):
        assert ~np.any(np.isnan(getattr(self, field.name))), f'{field.name} has unexpected nan values.'

@dataclass(frozen=True)
class ILQRInputPolicy:
    """Contains parameters for the perturbation input policy computed after performing LQR."""
    state_feedback_matrices: DoubleMatrix
    feedforward_inputs: DoubleMatrix

    def __post__init__(self) -> None:
        """Check shape of policy parameters."""
        assert len(self.state_feedback_matrices.shape) == 3, 'Expected state_feedback_matrices to have shape (n_horizon, n_inputs, n_states)'
        assert len(self.feedforward_inputs.shape) == 2, 'Expected feedforward inputs to have shape (n_horizon, n_inputs).'
        assert self.feedforward_inputs.shape == self.state_feedback_matrices.shape[:2], 'Inconsistent horizon or input dimension between feedforward inputs and state feedback matrices.'
        for field in fields(self):
            assert ~np.any(np.isnan(getattr(self, field.name))), f'{field.name} has unexpected nan values.'

def __post__init__(self) -> None:
    """Check shape of policy parameters."""
    assert len(self.state_feedback_matrices.shape) == 3, 'Expected state_feedback_matrices to have shape (n_horizon, n_inputs, n_states)'
    assert len(self.feedforward_inputs.shape) == 2, 'Expected feedforward inputs to have shape (n_horizon, n_inputs).'
    assert self.feedforward_inputs.shape == self.state_feedback_matrices.shape[:2], 'Inconsistent horizon or input dimension between feedforward inputs and state feedback matrices.'
    for field in fields(self):
        assert ~np.any(np.isnan(getattr(self, field.name))), f'{field.name} has unexpected nan values.'

class ILQRSolver:
    """iLQR solver implementation, see module docstring for details."""

    def __init__(self, solver_params: ILQRSolverParameters, warm_start_params: ILQRWarmStartParameters) -> None:
        """
        Initialize solver parameters.
        :param solver_params: Contains solver parameters for iLQR.
        :param warm_start_params: Contains warm start parameters for iLQR.
        """
        self._solver_params = solver_params
        self._warm_start_params = warm_start_params
        self._n_states = 5
        self._n_inputs = 2
        state_cost_diagonal_entries = self._solver_params.state_cost_diagonal_entries
        assert len(state_cost_diagonal_entries) == self._n_states, f'State cost matrix should have diagonal length {self._n_states}.'
        self._state_cost_matrix: DoubleMatrix = np.diag(state_cost_diagonal_entries)
        input_cost_diagonal_entries = self._solver_params.input_cost_diagonal_entries
        assert len(input_cost_diagonal_entries) == self._n_inputs, f'Input cost matrix should have diagonal length {self._n_inputs}.'
        self._input_cost_matrix: DoubleMatrix = np.diag(input_cost_diagonal_entries)
        state_trust_region_entries = self._solver_params.state_trust_region_entries
        assert len(state_trust_region_entries) == self._n_states, f'State trust region cost matrix should have diagonal length {self._n_states}.'
        self._state_trust_region_cost_matrix: DoubleMatrix = np.diag(state_trust_region_entries)
        input_trust_region_entries = self._solver_params.input_trust_region_entries
        assert len(input_trust_region_entries) == self._n_inputs, f'Input trust region cost matrix should have diagonal length {self._n_inputs}.'
        self._input_trust_region_cost_matrix: DoubleMatrix = np.diag(input_trust_region_entries)
        max_acceleration = self._solver_params.max_acceleration
        max_steering_angle_rate = self._solver_params.max_steering_angle_rate
        self._input_clip_min = (-max_acceleration, -max_steering_angle_rate)
        self._input_clip_max = (max_acceleration, max_steering_angle_rate)

    def solve(self, current_state: DoubleMatrix, reference_trajectory: DoubleMatrix) -> List[ILQRSolution]:
        """
        Run the main iLQR loop used to try to find (locally) optimal inputs to track the reference trajectory.
        :param current_state: The initial state from which we apply inputs, z_0.
        :param reference_trajectory: The state reference we'd like to track, inclusive of the initial timestep,
                                     z_{r,k} for k in {0, ..., N}.
        :return: A list of solution iterates after running the iLQR algorithm where the index is the iteration number.
        """
        assert current_state.shape == (self._n_states,), 'Incorrect state shape.'
        assert len(reference_trajectory.shape) == 2, 'Reference trajectory should be a 2D matrix.'
        reference_trajectory_length, reference_trajectory_state_dimension = reference_trajectory.shape
        assert reference_trajectory_length > 1, 'The reference trajectory should be at least two timesteps long.'
        assert reference_trajectory_state_dimension == self._n_states, 'The reference trajectory should have a matching state dimension.'
        solution_list: List[ILQRSolution] = []
        current_iterate = self._input_warm_start(current_state, reference_trajectory)
        solve_start_time = time.perf_counter()
        for _ in range(self._solver_params.max_ilqr_iterations):
            tracking_cost = self._compute_tracking_cost(iterate=current_iterate, reference_trajectory=reference_trajectory)
            solution_list.append(ILQRSolution(input_trajectory=current_iterate.input_trajectory, state_trajectory=current_iterate.state_trajectory, tracking_cost=tracking_cost))
            lqr_input_policy = self._run_lqr_backward_recursion(current_iterate=current_iterate, reference_trajectory=reference_trajectory)
            input_trajectory_next = self._update_inputs_with_policy(current_iterate=current_iterate, lqr_input_policy=lqr_input_policy)
            input_trajectory_norm_difference = np.linalg.norm(input_trajectory_next - current_iterate.input_trajectory)
            current_iterate = self._run_forward_dynamics(current_state, input_trajectory_next)
            if input_trajectory_norm_difference < self._solver_params.convergence_threshold:
                break
            elapsed_time = time.perf_counter() - solve_start_time
            if isinstance(self._solver_params.max_solve_time, float) and elapsed_time >= self._solver_params.max_solve_time:
                break
        tracking_cost = self._compute_tracking_cost(iterate=current_iterate, reference_trajectory=reference_trajectory)
        solution_list.append(ILQRSolution(input_trajectory=current_iterate.input_trajectory, state_trajectory=current_iterate.state_trajectory, tracking_cost=tracking_cost))
        return solution_list

    def _compute_tracking_cost(self, iterate: ILQRIterate, reference_trajectory: DoubleMatrix) -> float:
        """
        Compute the trajectory tracking cost given a candidate solution.
        :param iterate: Contains the candidate state and input trajectory to evaluate.
        :param reference_trajectory: The desired state reference trajectory with same length as state_trajectory.
        :return: The tracking cost of the candidate state/input trajectory.
        """
        input_trajectory = iterate.input_trajectory
        state_trajectory = iterate.state_trajectory
        assert len(state_trajectory) == len(reference_trajectory), 'The state and reference trajectory should have the same length.'
        error_state_trajectory = state_trajectory - reference_trajectory
        error_state_trajectory[:, 2] = principal_value(error_state_trajectory[:, 2])
        cost = np.sum([u.T @ self._input_cost_matrix @ u for u in input_trajectory]) + np.sum([e.T @ self._state_cost_matrix @ e for e in error_state_trajectory])
        return float(cost)

    def _clip_inputs(self, inputs: DoubleMatrix) -> DoubleMatrix:
        """
        Used to clip control inputs within constraints.
        :param: inputs: The control inputs with shape (self._n_inputs,) to clip.
        :return: Clipped version of the control inputs, unmodified if already within constraints.
        """
        assert inputs.shape == (self._n_inputs,), f'The inputs should be a 1D vector with {self._n_inputs} elements.'
        return np.clip(inputs, self._input_clip_min, self._input_clip_max)

    def _clip_steering_angle(self, steering_angle: float) -> float:
        """
        Used to clip the steering angle state within bounds.
        :param steering_angle: [rad] A steering angle (scalar) to clip.
        :return: [rad] The clipped steering angle.
        """
        steering_angle_sign = 1.0 if steering_angle >= 0 else -1.0
        steering_angle = steering_angle_sign * min(abs(steering_angle), self._solver_params.max_steering_angle)
        return steering_angle

    def _input_warm_start(self, current_state: DoubleMatrix, reference_trajectory: DoubleMatrix) -> ILQRIterate:
        """
        Given a reference trajectory, we generate the warm start (initial guess) by inferring the inputs applied based
        on poses in the reference trajectory.
        :param current_state: The initial state from which we apply inputs.
        :param reference_trajectory: The reference trajectory we are trying to follow.
        :return: The warm start iterate from which to start iLQR.
        """
        reference_states_completed, reference_inputs_completed = complete_kinematic_state_and_inputs_from_poses(discretization_time=self._solver_params.discretization_time, wheel_base=self._solver_params.wheelbase, poses=reference_trajectory[:, :3], jerk_penalty=self._warm_start_params.jerk_penalty_warm_start_fit, curvature_rate_penalty=self._warm_start_params.curvature_rate_penalty_warm_start_fit)
        _, _, _, velocity_current, steering_angle_current = current_state
        _, _, _, velocity_reference, steering_angle_reference = reference_states_completed[0, :]
        acceleration_feedback = -self._warm_start_params.k_velocity_error_feedback * (velocity_current - velocity_reference)
        steering_angle_feedback = compute_steering_angle_feedback(pose_reference=current_state[:3], pose_current=reference_states_completed[0, :3], lookahead_distance=self._warm_start_params.lookahead_distance_lateral_error, k_lateral_error=self._warm_start_params.k_lateral_error)
        steering_angle_desired = steering_angle_feedback + steering_angle_reference
        steering_rate_feedback = -self._warm_start_params.k_steering_angle_error_feedback * (steering_angle_current - steering_angle_desired)
        reference_inputs_completed[0, 0] += acceleration_feedback
        reference_inputs_completed[0, 1] += steering_rate_feedback
        return self._run_forward_dynamics(current_state, reference_inputs_completed)

    def _run_forward_dynamics(self, current_state: DoubleMatrix, input_trajectory: DoubleMatrix) -> ILQRIterate:
        """
        Compute states and corresponding state/input Jacobian matrices using forward dynamics.
        We additionally return the input since the dynamics may modify the input to ensure constraint satisfaction.
        :param current_state: The initial state from which we apply inputs.  Must be feasible given constraints.
        :param input_trajectory: The input trajectory applied to the model.  May be modified to ensure feasibility.
        :return: A feasible iterate after applying dynamics with state/input trajectories and Jacobian matrices.
        """
        N = len(input_trajectory)
        state_trajectory = np.nan * np.ones((N + 1, self._n_states), dtype=np.float64)
        final_input_trajectory = np.nan * np.ones_like(input_trajectory, dtype=np.float64)
        state_jacobian_trajectory = np.nan * np.ones((N, self._n_states, self._n_states), dtype=np.float64)
        final_input_jacobian_trajectory = np.nan * np.ones((N, self._n_states, self._n_inputs), dtype=np.float64)
        state_trajectory[0] = current_state
        for idx_u, u in enumerate(input_trajectory):
            state_next, final_input, state_jacobian, final_input_jacobian = self._dynamics_and_jacobian(state_trajectory[idx_u], u)
            state_trajectory[idx_u + 1] = state_next
            final_input_trajectory[idx_u] = final_input
            state_jacobian_trajectory[idx_u] = state_jacobian
            final_input_jacobian_trajectory[idx_u] = final_input_jacobian
        iterate = ILQRIterate(state_trajectory=state_trajectory, input_trajectory=final_input_trajectory, state_jacobian_trajectory=state_jacobian_trajectory, input_jacobian_trajectory=final_input_jacobian_trajectory)
        return iterate

    def _dynamics_and_jacobian(self, current_state: DoubleMatrix, current_input: DoubleMatrix) -> Tuple[DoubleMatrix, DoubleMatrix, DoubleMatrix, DoubleMatrix]:
        """
        Propagates the state forward by one step and computes the corresponding state and input Jacobian matrices.
        We also impose all constraints here to ensure the current input and next state are always feasible.
        :param current_state: The current state z_k.
        :param current_input: The applied input u_k.
        :return: The next state z_{k+1}, (possibly modified) input u_k, and state (df/dz) and input (df/du) Jacobians.
        """
        x, y, heading, velocity, steering_angle = current_state
        assert np.abs(steering_angle) < np.pi / 2.0, f'The steering angle {steering_angle} is outside expected limits.  There is a singularity at delta = np.pi/2.'
        current_input = self._clip_inputs(current_input)
        acceleration, steering_rate = current_input
        discretization_time = self._solver_params.discretization_time
        wheelbase = self._solver_params.wheelbase
        next_state: DoubleMatrix = np.copy(current_state)
        next_state[0] += velocity * np.cos(heading) * discretization_time
        next_state[1] += velocity * np.sin(heading) * discretization_time
        next_state[2] += velocity * np.tan(steering_angle) / wheelbase * discretization_time
        next_state[3] += acceleration * discretization_time
        next_state[4] += steering_rate * discretization_time
        next_state[2] = principal_value(next_state[2])
        next_steering_angle = self._clip_steering_angle(next_state[4])
        applied_steering_rate = (next_steering_angle - steering_angle) / discretization_time
        next_state[4] = next_steering_angle
        current_input[1] = applied_steering_rate
        state_jacobian: DoubleMatrix = np.eye(self._n_states, dtype=np.float64)
        input_jacobian: DoubleMatrix = np.zeros((self._n_states, self._n_inputs), dtype=np.float64)
        min_velocity_linearization = self._solver_params.min_velocity_linearization
        if -min_velocity_linearization <= velocity and velocity <= min_velocity_linearization:
            sign_velocity = 1.0 if velocity >= 0.0 else -1.0
            velocity = sign_velocity * min_velocity_linearization
        state_jacobian[0, 2] = -velocity * np.sin(heading) * discretization_time
        state_jacobian[0, 3] = np.cos(heading) * discretization_time
        state_jacobian[1, 2] = velocity * np.cos(heading) * discretization_time
        state_jacobian[1, 3] = np.sin(heading) * discretization_time
        state_jacobian[2, 3] = np.tan(steering_angle) / wheelbase * discretization_time
        state_jacobian[2, 4] = velocity * discretization_time / (wheelbase * np.cos(steering_angle) ** 2)
        input_jacobian[3, 0] = discretization_time
        input_jacobian[4, 1] = discretization_time
        return (next_state, current_input, state_jacobian, input_jacobian)

    def _run_lqr_backward_recursion(self, current_iterate: ILQRIterate, reference_trajectory: DoubleMatrix) -> ILQRInputPolicy:
        """
        Computes the locally optimal affine state feedback policy by applying dynamic programming to linear perturbation
        dynamics about a specified linearization trajectory.  We include a trust region penalty as part of the cost.
        :param current_iterate: Contains all relevant linearization information needed to compute LQR policy.
        :param reference_trajectory: The desired state trajectory we are tracking.
        :return: An affine state feedback policy - state feedback matrices and feedforward inputs found using LQR.
        """
        state_trajectory = current_iterate.state_trajectory
        input_trajectory = current_iterate.input_trajectory
        state_jacobian_trajectory = current_iterate.state_jacobian_trajectory
        input_jacobian_trajectory = current_iterate.input_jacobian_trajectory
        assert reference_trajectory.shape == state_trajectory.shape, 'The reference trajectory has incorrect shape.'
        error_state_trajectory = state_trajectory - reference_trajectory
        error_state_trajectory[:, 2] = principal_value(error_state_trajectory[:, 2])
        p_current = self._state_cost_matrix + self._state_trust_region_cost_matrix
        rho_current = self._state_cost_matrix @ error_state_trajectory[-1]
        N = len(input_trajectory)
        state_feedback_matrices = np.nan * np.ones((N, self._n_inputs, self._n_states), dtype=np.float64)
        feedforward_inputs = np.nan * np.ones((N, self._n_inputs), dtype=np.float64)
        for i in reversed(range(N)):
            A = state_jacobian_trajectory[i]
            B = input_jacobian_trajectory[i]
            u = input_trajectory[i]
            error = error_state_trajectory[i]
            inverse_matrix_term = np.linalg.inv(self._input_cost_matrix + self._input_trust_region_cost_matrix + B.T @ p_current @ B)
            state_feedback_matrix = -inverse_matrix_term @ B.T @ p_current @ A
            feedforward_input = -inverse_matrix_term @ (self._input_cost_matrix @ u + B.T @ rho_current)
            a_closed_loop = A + B @ state_feedback_matrix
            p_prior = self._state_cost_matrix + self._state_trust_region_cost_matrix + state_feedback_matrix.T @ self._input_cost_matrix @ state_feedback_matrix + state_feedback_matrix.T @ self._input_trust_region_cost_matrix @ state_feedback_matrix + a_closed_loop.T @ p_current @ a_closed_loop
            rho_prior = self._state_cost_matrix @ error + state_feedback_matrix.T @ self._input_cost_matrix @ (feedforward_input + u) + state_feedback_matrix.T @ self._input_trust_region_cost_matrix @ feedforward_input + a_closed_loop.T @ p_current @ B @ feedforward_input + a_closed_loop.T @ rho_current
            p_current = p_prior
            rho_current = rho_prior
            state_feedback_matrices[i] = state_feedback_matrix
            feedforward_inputs[i] = feedforward_input
        lqr_input_policy = ILQRInputPolicy(state_feedback_matrices=state_feedback_matrices, feedforward_inputs=feedforward_inputs)
        return lqr_input_policy

    def _update_inputs_with_policy(self, current_iterate: ILQRIterate, lqr_input_policy: ILQRInputPolicy) -> DoubleMatrix:
        """
        Used to update an iterate of iLQR by applying a perturbation input policy for local cost improvement.
        :param current_iterate: Contains the state and input trajectory about which we linearized.
        :param lqr_input_policy: Contains the LQR policy to apply.
        :return: The next input trajectory found by applying the LQR policy.
        """
        state_trajectory = current_iterate.state_trajectory
        input_trajectory = current_iterate.input_trajectory
        delta_state_trajectory = np.nan * np.ones((len(input_trajectory) + 1, self._n_states), dtype=np.float64)
        delta_state_trajectory[0] = [0.0] * self._n_states
        input_next_trajectory = np.nan * np.ones_like(input_trajectory, dtype=np.float64)
        zip_object = zip(input_trajectory, state_trajectory[:-1], state_trajectory[1:], lqr_input_policy.state_feedback_matrices, lqr_input_policy.feedforward_inputs)
        for input_idx, (input_lin, state_lin, state_lin_next, state_feedback_matrix, feedforward_input) in enumerate(zip_object):
            delta_state = delta_state_trajectory[input_idx]
            delta_input = state_feedback_matrix @ delta_state + feedforward_input
            input_perturbed = input_lin + delta_input
            state_perturbed = state_lin + delta_state
            state_perturbed[2] = principal_value(state_perturbed[2])
            state_perturbed_next, input_perturbed, _, _ = self._dynamics_and_jacobian(state_perturbed, input_perturbed)
            delta_state_next = state_perturbed_next - state_lin_next
            delta_state_next[2] = principal_value(delta_state_next[2])
            delta_state_trajectory[input_idx + 1] = delta_state_next
            input_next_trajectory[input_idx] = input_perturbed
        assert ~np.any(np.isnan(input_next_trajectory)), 'All next inputs should be valid float values.'
        return input_next_trajectory

def solve(self, current_state: DoubleMatrix, reference_trajectory: DoubleMatrix) -> List[ILQRSolution]:
    """
        Run the main iLQR loop used to try to find (locally) optimal inputs to track the reference trajectory.
        :param current_state: The initial state from which we apply inputs, z_0.
        :param reference_trajectory: The state reference we'd like to track, inclusive of the initial timestep,
                                     z_{r,k} for k in {0, ..., N}.
        :return: A list of solution iterates after running the iLQR algorithm where the index is the iteration number.
        """
    assert current_state.shape == (self._n_states,), 'Incorrect state shape.'
    assert len(reference_trajectory.shape) == 2, 'Reference trajectory should be a 2D matrix.'
    reference_trajectory_length, reference_trajectory_state_dimension = reference_trajectory.shape
    assert reference_trajectory_length > 1, 'The reference trajectory should be at least two timesteps long.'
    assert reference_trajectory_state_dimension == self._n_states, 'The reference trajectory should have a matching state dimension.'
    solution_list: List[ILQRSolution] = []
    current_iterate = self._input_warm_start(current_state, reference_trajectory)
    solve_start_time = time.perf_counter()
    for _ in range(self._solver_params.max_ilqr_iterations):
        tracking_cost = self._compute_tracking_cost(iterate=current_iterate, reference_trajectory=reference_trajectory)
        solution_list.append(ILQRSolution(input_trajectory=current_iterate.input_trajectory, state_trajectory=current_iterate.state_trajectory, tracking_cost=tracking_cost))
        lqr_input_policy = self._run_lqr_backward_recursion(current_iterate=current_iterate, reference_trajectory=reference_trajectory)
        input_trajectory_next = self._update_inputs_with_policy(current_iterate=current_iterate, lqr_input_policy=lqr_input_policy)
        input_trajectory_norm_difference = np.linalg.norm(input_trajectory_next - current_iterate.input_trajectory)
        current_iterate = self._run_forward_dynamics(current_state, input_trajectory_next)
        if input_trajectory_norm_difference < self._solver_params.convergence_threshold:
            break
        elapsed_time = time.perf_counter() - solve_start_time
        if isinstance(self._solver_params.max_solve_time, float) and elapsed_time >= self._solver_params.max_solve_time:
            break
    tracking_cost = self._compute_tracking_cost(iterate=current_iterate, reference_trajectory=reference_trajectory)
    solution_list.append(ILQRSolution(input_trajectory=current_iterate.input_trajectory, state_trajectory=current_iterate.state_trajectory, tracking_cost=tracking_cost))
    return solution_list

def _input_warm_start(self, current_state: DoubleMatrix, reference_trajectory: DoubleMatrix) -> ILQRIterate:
    """
        Given a reference trajectory, we generate the warm start (initial guess) by inferring the inputs applied based
        on poses in the reference trajectory.
        :param current_state: The initial state from which we apply inputs.
        :param reference_trajectory: The reference trajectory we are trying to follow.
        :return: The warm start iterate from which to start iLQR.
        """
    reference_states_completed, reference_inputs_completed = complete_kinematic_state_and_inputs_from_poses(discretization_time=self._solver_params.discretization_time, wheel_base=self._solver_params.wheelbase, poses=reference_trajectory[:, :3], jerk_penalty=self._warm_start_params.jerk_penalty_warm_start_fit, curvature_rate_penalty=self._warm_start_params.curvature_rate_penalty_warm_start_fit)
    _, _, _, velocity_current, steering_angle_current = current_state
    _, _, _, velocity_reference, steering_angle_reference = reference_states_completed[0, :]
    acceleration_feedback = -self._warm_start_params.k_velocity_error_feedback * (velocity_current - velocity_reference)
    steering_angle_feedback = compute_steering_angle_feedback(pose_reference=current_state[:3], pose_current=reference_states_completed[0, :3], lookahead_distance=self._warm_start_params.lookahead_distance_lateral_error, k_lateral_error=self._warm_start_params.k_lateral_error)
    steering_angle_desired = steering_angle_feedback + steering_angle_reference
    steering_rate_feedback = -self._warm_start_params.k_steering_angle_error_feedback * (steering_angle_current - steering_angle_desired)
    reference_inputs_completed[0, 0] += acceleration_feedback
    reference_inputs_completed[0, 1] += steering_rate_feedback
    return self._run_forward_dynamics(current_state, reference_inputs_completed)

def _run_forward_dynamics(self, current_state: DoubleMatrix, input_trajectory: DoubleMatrix) -> ILQRIterate:
    """
        Compute states and corresponding state/input Jacobian matrices using forward dynamics.
        We additionally return the input since the dynamics may modify the input to ensure constraint satisfaction.
        :param current_state: The initial state from which we apply inputs.  Must be feasible given constraints.
        :param input_trajectory: The input trajectory applied to the model.  May be modified to ensure feasibility.
        :return: A feasible iterate after applying dynamics with state/input trajectories and Jacobian matrices.
        """
    N = len(input_trajectory)
    state_trajectory = np.nan * np.ones((N + 1, self._n_states), dtype=np.float64)
    final_input_trajectory = np.nan * np.ones_like(input_trajectory, dtype=np.float64)
    state_jacobian_trajectory = np.nan * np.ones((N, self._n_states, self._n_states), dtype=np.float64)
    final_input_jacobian_trajectory = np.nan * np.ones((N, self._n_states, self._n_inputs), dtype=np.float64)
    state_trajectory[0] = current_state
    for idx_u, u in enumerate(input_trajectory):
        state_next, final_input, state_jacobian, final_input_jacobian = self._dynamics_and_jacobian(state_trajectory[idx_u], u)
        state_trajectory[idx_u + 1] = state_next
        final_input_trajectory[idx_u] = final_input
        state_jacobian_trajectory[idx_u] = state_jacobian
        final_input_jacobian_trajectory[idx_u] = final_input_jacobian
    iterate = ILQRIterate(state_trajectory=state_trajectory, input_trajectory=final_input_trajectory, state_jacobian_trajectory=state_jacobian_trajectory, input_jacobian_trajectory=final_input_jacobian_trajectory)
    return iterate

def _update_inputs_with_policy(self, current_iterate: ILQRIterate, lqr_input_policy: ILQRInputPolicy) -> DoubleMatrix:
    """
        Used to update an iterate of iLQR by applying a perturbation input policy for local cost improvement.
        :param current_iterate: Contains the state and input trajectory about which we linearized.
        :param lqr_input_policy: Contains the LQR policy to apply.
        :return: The next input trajectory found by applying the LQR policy.
        """
    state_trajectory = current_iterate.state_trajectory
    input_trajectory = current_iterate.input_trajectory
    delta_state_trajectory = np.nan * np.ones((len(input_trajectory) + 1, self._n_states), dtype=np.float64)
    delta_state_trajectory[0] = [0.0] * self._n_states
    input_next_trajectory = np.nan * np.ones_like(input_trajectory, dtype=np.float64)
    zip_object = zip(input_trajectory, state_trajectory[:-1], state_trajectory[1:], lqr_input_policy.state_feedback_matrices, lqr_input_policy.feedforward_inputs)
    for input_idx, (input_lin, state_lin, state_lin_next, state_feedback_matrix, feedforward_input) in enumerate(zip_object):
        delta_state = delta_state_trajectory[input_idx]
        delta_input = state_feedback_matrix @ delta_state + feedforward_input
        input_perturbed = input_lin + delta_input
        state_perturbed = state_lin + delta_state
        state_perturbed[2] = principal_value(state_perturbed[2])
        state_perturbed_next, input_perturbed, _, _ = self._dynamics_and_jacobian(state_perturbed, input_perturbed)
        delta_state_next = state_perturbed_next - state_lin_next
        delta_state_next[2] = principal_value(delta_state_next[2])
        delta_state_trajectory[input_idx + 1] = delta_state_next
        input_next_trajectory[input_idx] = input_perturbed
    assert ~np.any(np.isnan(input_next_trajectory)), 'All next inputs should be valid float values.'
    return input_next_trajectory

class TestILQRSolver(unittest.TestCase):
    """
    Tests for ILQRSolver class.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        solver_params = ILQRSolverParameters(discretization_time=0.2, state_cost_diagonal_entries=[1.0, 1.0, 10.0, 0.0, 0.0], input_cost_diagonal_entries=[1.0, 10.0], state_trust_region_entries=[1.0] * 5, input_trust_region_entries=[1.0] * 2, max_ilqr_iterations=100, convergence_threshold=1e-06, max_solve_time=0.05, max_acceleration=3.0, max_steering_angle=np.pi / 3.0, max_steering_angle_rate=0.5, min_velocity_linearization=0.01)
        warm_start_params = ILQRWarmStartParameters(k_velocity_error_feedback=0.5, k_steering_angle_error_feedback=0.05, lookahead_distance_lateral_error=15.0, k_lateral_error=0.1, jerk_penalty_warm_start_fit=0.0001, curvature_rate_penalty_warm_start_fit=0.01)
        self.solver = ILQRSolver(solver_params=solver_params, warm_start_params=warm_start_params)
        self.discretization_time = self.solver._solver_params.discretization_time
        self.n_states = self.solver._n_states
        self.n_inputs = self.solver._n_inputs
        self.n_horizon = 40
        self.min_velocity_linearization = self.solver._solver_params.min_velocity_linearization
        self.max_acceleration = self.solver._solver_params.max_acceleration
        self.max_steering_angle = self.solver._solver_params.max_steering_angle
        self.max_steering_angle_rate = self.solver._solver_params.max_steering_angle_rate
        self.rtol = 1e-08
        self.atol = 1e-10
        self.check_if_allclose = partial(np.allclose, rtol=self.rtol, atol=self.atol)
        self.assert_allclose = partial(np_test.assert_allclose, rtol=self.rtol, atol=self.atol)
        constant_speed = 1.0
        self.reference_trajectory: DoubleMatrix = np.zeros((self.n_horizon + 1, self.n_states), dtype=np.float64)
        self.reference_trajectory[:, 0] = constant_speed * np.arange(self.n_horizon + 1) * self.discretization_time
        self.reference_trajectory[:, 3] = constant_speed
        reference_acceleration = np.diff(self.reference_trajectory[:, 3]) / self.discretization_time
        reference_steering_rate = np.diff(self.reference_trajectory[:, 4]) / self.discretization_time
        self.reference_inputs: DoubleMatrix = np.column_stack((reference_acceleration, reference_steering_rate))

    def test_solve(self) -> None:
        """
        Check that, for reasonable tuning parameters and small initial error, the tracking cost is non-increasing.
        """
        perturbed_current_state: DoubleMatrix = np.array([1.0, -1.0, 0.01, 1.0, -0.1], dtype=np.float64)
        current_state = self.reference_trajectory[0, :] + perturbed_current_state
        start_time = time.perf_counter()
        ilqr_solutions = self.solver.solve(current_state, self.reference_trajectory)
        end_time = time.perf_counter()
        print(f'Solve took {end_time - start_time} seconds for {len(ilqr_solutions)} iterations.')
        tracking_cost_history = [isol.tracking_cost for isol in ilqr_solutions]
        self.assertTrue(np.all(np.diff(tracking_cost_history) <= 0.0))

    def test__compute_tracking_cost(self) -> None:
        """Check tracking cost computation."""
        zero_input_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_inputs), dtype=np.float64)
        zero_state_jacobian_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_states, self.n_states), dtype=np.float64)
        zero_input_jacobian_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_states, self.n_inputs), dtype=np.float64)
        test_iterate = ILQRIterate(input_trajectory=np.zeros((self.n_horizon, self.n_inputs), dtype=np.float64), state_trajectory=self.reference_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
        cost_zero_error_zero_inputs = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
        self.assert_allclose(0.0, cost_zero_error_zero_inputs)
        for input_sign in [-1.0, 1.0]:
            costs = []
            for input_magnitude in [1.0, 5.0, 10.0, 100.0]:
                test_input_trajectory = input_sign * input_magnitude * np.ones((self.n_horizon, self.n_inputs), dtype=np.float64)
                test_iterate = ILQRIterate(input_trajectory=test_input_trajectory, state_trajectory=self.reference_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
                cost = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
                costs.append(cost)
            self.assertTrue(np.all(np.diff(costs) > 0.0))
        for error_sign in [-1.0, 1.0]:
            costs = []
            for error_magnitude in [1.0, 5.0, 10.0, 100.0]:
                test_state_trajectory = self.reference_trajectory + error_sign * error_magnitude * np.ones_like(self.reference_trajectory)
                test_iterate = ILQRIterate(input_trajectory=zero_input_trajectory, state_trajectory=test_state_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
                cost = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
                costs.append(cost)
            self.assertTrue(np.all(np.diff(costs) > 0.0))

    def test__clip_inputs(self) -> None:
        """Check that input clipping works."""
        zero_inputs: DoubleMatrix = np.zeros(self.n_inputs, dtype=np.float64)
        inputs_at_bounds: DoubleMatrix = np.array([self.max_acceleration, self.max_steering_angle_rate], dtype=np.float64)
        inputs_within_bounds = 0.5 * inputs_at_bounds
        inputs_outside_bounds = 2.0 * inputs_at_bounds
        for test_inputs, expect_same in zip([zero_inputs, inputs_within_bounds, inputs_at_bounds, inputs_outside_bounds], [True, True, True, False]):
            for input_sign in [-1.0, 1.0]:
                signed_test_inputs = input_sign * test_inputs
                clipped_inputs = self.solver._clip_inputs(signed_test_inputs)
                are_same = self.check_if_allclose(signed_test_inputs, clipped_inputs)
                self.assertEqual(are_same, expect_same)
                self.assertTrue(np.all(np.sign(signed_test_inputs) == np.sign(clipped_inputs)))

    def test__clip_steering_angle(self) -> None:
        """Check that steering angle clipping works."""
        zero_steering_angle = 0.0
        steering_angle_at_bounds = self.max_steering_angle
        steering_angle_within_bounds = 0.5 * steering_angle_at_bounds
        steering_angle_outside_bounds = 2.0 * steering_angle_at_bounds
        for test_steering_angle, expect_same in zip([zero_steering_angle, steering_angle_within_bounds, steering_angle_at_bounds, steering_angle_outside_bounds], [True, True, True, False]):
            for sign in [-1.0, 1.0]:
                signed_steering_angle = sign * test_steering_angle
                clipped_steering_angle = self.solver._clip_steering_angle(signed_steering_angle)
                are_same = self.check_if_allclose(signed_steering_angle, clipped_steering_angle)
                self.assertEqual(are_same, expect_same)
                self.assertTrue(np.all(np.sign(signed_steering_angle) == np.sign(clipped_steering_angle)))

    def test__input_warm_start(self) -> None:
        """Check first warm start generation under zero and nonzero initial tracking error."""
        test_current_state = self.reference_trajectory[0, :]
        warm_start_iterate = self.solver._input_warm_start(test_current_state, self.reference_trajectory)
        self.assert_allclose(warm_start_iterate.input_trajectory, self.reference_inputs)
        perturbed_current_state = self.reference_trajectory[0, :] + np.array([1.0, -1.0, 0.01, 1.0, -0.1], dtype=np.float64)
        perturbed_warm_start_iterate = self.solver._input_warm_start(perturbed_current_state, self.reference_trajectory)
        first_input_close = self.check_if_allclose(perturbed_warm_start_iterate.input_trajectory[0], self.reference_inputs[0])
        self.assertFalse(first_input_close)
        self.assert_allclose(perturbed_warm_start_iterate.input_trajectory[1, :], self.reference_inputs[1, :])

    def test__run_forward_dynamics_no_saturation(self) -> None:
        """Check generation of a state trajectory from current state and inputs without steering angle saturation."""
        test_current_state = self.reference_trajectory[0, :]
        current_steering_angle = test_current_state[4]
        time_to_saturation_s = (self.max_steering_angle - abs(current_steering_angle)) / self.max_steering_angle_rate
        timesteps_to_saturation = np.ceil(time_to_saturation_s / self.discretization_time).astype(int)
        assert timesteps_to_saturation >= 2, "We'd like at least two timesteps_to_saturation for the subsequent test."
        steering_rate_input = self.max_steering_angle_rate
        acceleration_input = self.max_acceleration
        test_input_trajectory: DoubleMatrix = np.ones((timesteps_to_saturation - 1, 2), dtype=np.float64)
        test_input_trajectory[:, 0] = acceleration_input
        test_input_trajectory[:, 1] = steering_rate_input
        ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
        self.assertLess(np.amax(np.abs(ilqr_iterate.state_trajectory[:, 4])), self.max_steering_angle)
        steering_rate_unmodified = self.check_if_allclose(ilqr_iterate.input_trajectory[:, 1], test_input_trajectory[:, 1])
        self.assertTrue(steering_rate_unmodified)
        acceleration_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 3]) / self.discretization_time
        self.assert_allclose(acceleration_finite_differences, ilqr_iterate.input_trajectory[:, 0])
        steering_rate_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 4]) / self.discretization_time
        self.assert_allclose(steering_rate_finite_differences, ilqr_iterate.input_trajectory[:, 1])

    def test__run_forward_dynamics_saturation(self) -> None:
        """Check generation of a state trajectory from current state and inputs with steering angle saturation."""
        test_current_state = self.reference_trajectory[0, :]
        current_steering_angle = test_current_state[4]
        time_to_saturation_s = (self.max_steering_angle - abs(current_steering_angle)) / self.max_steering_angle_rate
        timesteps_to_saturation = np.ceil(time_to_saturation_s / self.discretization_time).astype(int)
        assert timesteps_to_saturation >= 2, "We'd like at least two timesteps_to_saturation for the subsequent test."
        if np.abs(current_steering_angle) > 0.0:
            steering_rate_input = self.max_steering_angle_rate * np.sign(current_steering_angle)
        else:
            steering_rate_input = self.max_steering_angle_rate
        acceleration_input = self.max_acceleration
        test_input_trajectory: DoubleMatrix = np.ones((timesteps_to_saturation + 1, 2), dtype=np.float64)
        test_input_trajectory[:, 0] = acceleration_input
        test_input_trajectory[:, 1] = steering_rate_input
        ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
        self.assertEqual(np.abs(ilqr_iterate.state_trajectory[-2, 4]), self.max_steering_angle)
        self.assertEqual(np.amax(np.abs(ilqr_iterate.state_trajectory[:, 4])), self.max_steering_angle)
        steering_rate_unmodified = self.check_if_allclose(ilqr_iterate.input_trajectory[:, 1], test_input_trajectory[:, 1])
        self.assertFalse(steering_rate_unmodified)
        acceleration_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 3]) / self.discretization_time
        steering_rate_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 4]) / self.discretization_time
        self.assert_allclose(acceleration_finite_differences, ilqr_iterate.input_trajectory[:, 0])
        self.assert_allclose(steering_rate_finite_differences, ilqr_iterate.input_trajectory[:, 1])

    def test_dynamics_and_jacobian_constraints(self) -> None:
        """Check application of constraints in dynamics."""
        test_state_in_bounds: DoubleMatrix = np.array([0.0, 0.0, 0.1, 1.0, -0.01], dtype=np.float64)
        test_state_at_bounds: DoubleMatrix = np.copy(test_state_in_bounds)
        test_state_at_bounds[4] = self.max_steering_angle
        input_at_bounds: DoubleMatrix = np.array([self.max_acceleration, self.max_steering_angle_rate], dtype=np.float64)
        test_input_in_bounds = 0.5 * input_at_bounds
        test_input_outside_bounds = 2.0 * input_at_bounds
        test_cases_dict = {}
        test_cases_dict['state_in_bounds_input_in_bounds'] = {'state': test_state_in_bounds, 'input': test_input_in_bounds, 'expect_acceleration_modified': False, 'expect_steering_rate_modified': False}
        test_cases_dict['state_at_bounds_input_in_bounds'] = {'state': test_state_at_bounds, 'input': test_input_in_bounds, 'expect_acceleration_modified': False, 'expect_steering_rate_modified': True}
        test_cases_dict['state_in_bounds_input_outside_bounds'] = {'state': test_state_in_bounds, 'input': test_input_outside_bounds, 'expect_acceleration_modified': True, 'expect_steering_rate_modified': True}
        test_cases_dict['state_at_bounds_input_outside_bounds'] = {'state': test_state_at_bounds, 'input': test_input_outside_bounds, 'expect_acceleration_modified': True, 'expect_steering_rate_modified': True}
        for test_name, test_config in test_cases_dict.items():
            next_state, applied_input, _, _ = self.solver._dynamics_and_jacobian(test_config['state'], test_config['input'])
            self.assertEqual(test_config['expect_acceleration_modified'], not self.check_if_allclose(applied_input[0], test_config['input'][0]))
            self.assertEqual(test_config['expect_steering_rate_modified'], not self.check_if_allclose(applied_input[1], test_config['input'][1]))
            self.assertLessEqual(np.abs(next_state[4]), self.max_steering_angle)

    def test_dynamics_and_jacobian_linearization(self) -> None:
        """
        Check that Jacobian computation makes sense by comparison to finite difference estimate.
        Also check that the minimum velocity linearization is triggered for the Jacobian computation.
        """
        test_state: DoubleMatrix = np.array([0.0, 0.0, 0.1, 1.0, -0.01], dtype=np.float64)
        test_input: DoubleMatrix = np.array([1.0, 0.01], dtype=np.float64)
        epsilon = 1e-06
        _, applied_input, state_jacobian, input_jacobian = self.solver._dynamics_and_jacobian(test_state, test_input)
        self.assert_allclose(test_input, applied_input)
        state_jacobian_finite_differencing = np.zeros_like(state_jacobian)
        for state_idx in range(self.n_states):
            epsilon_array = epsilon * np.array([x == state_idx for x in range(self.n_states)], dtype=np.float64)
            next_state_plus, _, _, _ = self.solver._dynamics_and_jacobian(test_state + epsilon_array, test_input)
            next_state_minus, _, _, _ = self.solver._dynamics_and_jacobian(test_state - epsilon_array, test_input)
            state_jacobian_finite_differencing[:, state_idx] = (next_state_plus - next_state_minus) / (2.0 * epsilon)
        self.assert_allclose(state_jacobian, state_jacobian_finite_differencing)
        input_jacobian_finite_differencing = np.zeros_like(input_jacobian)
        for input_idx in range(self.n_inputs):
            epsilon_array = epsilon * np.array([x == input_idx for x in range(self.n_inputs)], dtype=np.float64)
            next_state_plus, _, _, _ = self.solver._dynamics_and_jacobian(test_state, test_input + epsilon_array)
            next_state_minus, _, _, _ = self.solver._dynamics_and_jacobian(test_state, test_input - epsilon_array)
            input_jacobian_finite_differencing[:, input_idx] = (next_state_plus - next_state_minus) / (2.0 * epsilon)
        self.assert_allclose(input_jacobian, input_jacobian_finite_differencing)
        test_state_stopped: DoubleMatrix = np.copy(test_state)
        test_state_stopped[3] = 0.0
        _, _, state_jacobian_stopped, _ = self.solver._dynamics_and_jacobian(test_state_stopped, test_input)
        velocity_inferred_stopped = np.hypot(state_jacobian_stopped[0, 2], state_jacobian_stopped[1, 2]) / self.discretization_time
        with np_test.assert_raises(AssertionError):
            self.assert_allclose(velocity_inferred_stopped, test_state_stopped[3])
        self.assert_allclose(velocity_inferred_stopped, self.min_velocity_linearization)

    def test__run_lqr_backward_recursion(self) -> None:
        """Check some properties of the LQR input policy."""
        test_current_state = self.reference_trajectory[0]
        test_input_trajectory = self.reference_inputs
        input_perturbation: DoubleMatrix = np.array([-0.1 * self.max_acceleration, 0.1 * self.max_steering_angle], dtype=np.float64)
        test_input_trajectory[0] += input_perturbation
        ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
        ilqr_input_policy = self.solver._run_lqr_backward_recursion(current_iterate=ilqr_iterate, reference_trajectory=self.reference_trajectory)
        state_feedback_matrices = ilqr_input_policy.state_feedback_matrices
        feedforward_inputs = ilqr_input_policy.feedforward_inputs
        self.assertTrue(np.all(np.sign(feedforward_inputs[0]) == -np.sign(input_perturbation)))
        self.assertEqual(state_feedback_matrices.shape, (self.n_horizon, self.n_inputs, self.n_states))

    def test__update_inputs_with_policy(self) -> None:
        """Check how application of a specified input policy affects the next input trajectory."""
        ilqr_iterate = self.solver._run_forward_dynamics(self.reference_trajectory[0], self.reference_inputs)
        input_trajectory = ilqr_iterate.input_trajectory
        state_trajectory = ilqr_iterate.state_trajectory
        angle_distance_to_saturation = self.max_steering_angle - np.amax(np.abs(state_trajectory[:, 4]))
        test_feedforward_steering_rate = min(0.5 * angle_distance_to_saturation / (self.n_horizon * self.discretization_time), self.max_steering_angle_rate)
        feedforward_inputs = np.ones_like(input_trajectory)
        feedforward_inputs[:, 0] = self.max_acceleration
        feedforward_inputs[:, 1] = test_feedforward_steering_rate
        feedforward_inputs[1::2] *= -1.0
        state_feedback_matrices = np.zeros((len(feedforward_inputs), self.n_inputs, self.n_states))
        lqr_input_policy = ILQRInputPolicy(state_feedback_matrices=state_feedback_matrices, feedforward_inputs=feedforward_inputs)
        input_next_trajectory = self.solver._update_inputs_with_policy(current_iterate=ilqr_iterate, lqr_input_policy=lqr_input_policy)
        self.assert_allclose(feedforward_inputs, input_next_trajectory)
        test_input_perturbation = [self.max_acceleration, test_feedforward_steering_rate]
        feedforward_inputs = np.zeros_like(input_trajectory)
        feedforward_inputs[0, :] = test_input_perturbation
        state_feedback_matrices = np.zeros((len(feedforward_inputs), self.n_inputs, self.n_states))
        state_feedback_matrices[:, 0, 3] = -1.0
        state_feedback_matrices[:, 1, 4] = -1.0
        lqr_input_policy = ILQRInputPolicy(state_feedback_matrices=state_feedback_matrices, feedforward_inputs=feedforward_inputs)
        input_next_trajectory = self.solver._update_inputs_with_policy(current_iterate=ilqr_iterate, lqr_input_policy=lqr_input_policy)
        first_delta_input = input_next_trajectory[0, :] - input_trajectory[0, :]
        second_delta_input = input_next_trajectory[1, :] - input_trajectory[1, :]
        self.assertTrue(np.all(np.sign(first_delta_input) == -np.sign(second_delta_input)))

def test_solve(self) -> None:
    """
        Check that, for reasonable tuning parameters and small initial error, the tracking cost is non-increasing.
        """
    perturbed_current_state: DoubleMatrix = np.array([1.0, -1.0, 0.01, 1.0, -0.1], dtype=np.float64)
    current_state = self.reference_trajectory[0, :] + perturbed_current_state
    start_time = time.perf_counter()
    ilqr_solutions = self.solver.solve(current_state, self.reference_trajectory)
    end_time = time.perf_counter()
    print(f'Solve took {end_time - start_time} seconds for {len(ilqr_solutions)} iterations.')
    tracking_cost_history = [isol.tracking_cost for isol in ilqr_solutions]
    self.assertTrue(np.all(np.diff(tracking_cost_history) <= 0.0))

def test__compute_tracking_cost(self) -> None:
    """Check tracking cost computation."""
    zero_input_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_inputs), dtype=np.float64)
    zero_state_jacobian_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_states, self.n_states), dtype=np.float64)
    zero_input_jacobian_trajectory: DoubleMatrix = np.zeros((self.n_horizon, self.n_states, self.n_inputs), dtype=np.float64)
    test_iterate = ILQRIterate(input_trajectory=np.zeros((self.n_horizon, self.n_inputs), dtype=np.float64), state_trajectory=self.reference_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
    cost_zero_error_zero_inputs = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
    self.assert_allclose(0.0, cost_zero_error_zero_inputs)
    for input_sign in [-1.0, 1.0]:
        costs = []
        for input_magnitude in [1.0, 5.0, 10.0, 100.0]:
            test_input_trajectory = input_sign * input_magnitude * np.ones((self.n_horizon, self.n_inputs), dtype=np.float64)
            test_iterate = ILQRIterate(input_trajectory=test_input_trajectory, state_trajectory=self.reference_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
            cost = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
            costs.append(cost)
        self.assertTrue(np.all(np.diff(costs) > 0.0))
    for error_sign in [-1.0, 1.0]:
        costs = []
        for error_magnitude in [1.0, 5.0, 10.0, 100.0]:
            test_state_trajectory = self.reference_trajectory + error_sign * error_magnitude * np.ones_like(self.reference_trajectory)
            test_iterate = ILQRIterate(input_trajectory=zero_input_trajectory, state_trajectory=test_state_trajectory, state_jacobian_trajectory=zero_state_jacobian_trajectory, input_jacobian_trajectory=zero_input_jacobian_trajectory)
            cost = self.solver._compute_tracking_cost(iterate=test_iterate, reference_trajectory=self.reference_trajectory)
            costs.append(cost)
        self.assertTrue(np.all(np.diff(costs) > 0.0))

def test__clip_inputs(self) -> None:
    """Check that input clipping works."""
    zero_inputs: DoubleMatrix = np.zeros(self.n_inputs, dtype=np.float64)
    inputs_at_bounds: DoubleMatrix = np.array([self.max_acceleration, self.max_steering_angle_rate], dtype=np.float64)
    inputs_within_bounds = 0.5 * inputs_at_bounds
    inputs_outside_bounds = 2.0 * inputs_at_bounds
    for test_inputs, expect_same in zip([zero_inputs, inputs_within_bounds, inputs_at_bounds, inputs_outside_bounds], [True, True, True, False]):
        for input_sign in [-1.0, 1.0]:
            signed_test_inputs = input_sign * test_inputs
            clipped_inputs = self.solver._clip_inputs(signed_test_inputs)
            are_same = self.check_if_allclose(signed_test_inputs, clipped_inputs)
            self.assertEqual(are_same, expect_same)
            self.assertTrue(np.all(np.sign(signed_test_inputs) == np.sign(clipped_inputs)))

def test__clip_steering_angle(self) -> None:
    """Check that steering angle clipping works."""
    zero_steering_angle = 0.0
    steering_angle_at_bounds = self.max_steering_angle
    steering_angle_within_bounds = 0.5 * steering_angle_at_bounds
    steering_angle_outside_bounds = 2.0 * steering_angle_at_bounds
    for test_steering_angle, expect_same in zip([zero_steering_angle, steering_angle_within_bounds, steering_angle_at_bounds, steering_angle_outside_bounds], [True, True, True, False]):
        for sign in [-1.0, 1.0]:
            signed_steering_angle = sign * test_steering_angle
            clipped_steering_angle = self.solver._clip_steering_angle(signed_steering_angle)
            are_same = self.check_if_allclose(signed_steering_angle, clipped_steering_angle)
            self.assertEqual(are_same, expect_same)
            self.assertTrue(np.all(np.sign(signed_steering_angle) == np.sign(clipped_steering_angle)))

def test__input_warm_start(self) -> None:
    """Check first warm start generation under zero and nonzero initial tracking error."""
    test_current_state = self.reference_trajectory[0, :]
    warm_start_iterate = self.solver._input_warm_start(test_current_state, self.reference_trajectory)
    self.assert_allclose(warm_start_iterate.input_trajectory, self.reference_inputs)
    perturbed_current_state = self.reference_trajectory[0, :] + np.array([1.0, -1.0, 0.01, 1.0, -0.1], dtype=np.float64)
    perturbed_warm_start_iterate = self.solver._input_warm_start(perturbed_current_state, self.reference_trajectory)
    first_input_close = self.check_if_allclose(perturbed_warm_start_iterate.input_trajectory[0], self.reference_inputs[0])
    self.assertFalse(first_input_close)
    self.assert_allclose(perturbed_warm_start_iterate.input_trajectory[1, :], self.reference_inputs[1, :])

def test__run_forward_dynamics_no_saturation(self) -> None:
    """Check generation of a state trajectory from current state and inputs without steering angle saturation."""
    test_current_state = self.reference_trajectory[0, :]
    current_steering_angle = test_current_state[4]
    time_to_saturation_s = (self.max_steering_angle - abs(current_steering_angle)) / self.max_steering_angle_rate
    timesteps_to_saturation = np.ceil(time_to_saturation_s / self.discretization_time).astype(int)
    assert timesteps_to_saturation >= 2, "We'd like at least two timesteps_to_saturation for the subsequent test."
    steering_rate_input = self.max_steering_angle_rate
    acceleration_input = self.max_acceleration
    test_input_trajectory: DoubleMatrix = np.ones((timesteps_to_saturation - 1, 2), dtype=np.float64)
    test_input_trajectory[:, 0] = acceleration_input
    test_input_trajectory[:, 1] = steering_rate_input
    ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
    self.assertLess(np.amax(np.abs(ilqr_iterate.state_trajectory[:, 4])), self.max_steering_angle)
    steering_rate_unmodified = self.check_if_allclose(ilqr_iterate.input_trajectory[:, 1], test_input_trajectory[:, 1])
    self.assertTrue(steering_rate_unmodified)
    acceleration_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 3]) / self.discretization_time
    self.assert_allclose(acceleration_finite_differences, ilqr_iterate.input_trajectory[:, 0])
    steering_rate_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 4]) / self.discretization_time
    self.assert_allclose(steering_rate_finite_differences, ilqr_iterate.input_trajectory[:, 1])

def test__run_forward_dynamics_saturation(self) -> None:
    """Check generation of a state trajectory from current state and inputs with steering angle saturation."""
    test_current_state = self.reference_trajectory[0, :]
    current_steering_angle = test_current_state[4]
    time_to_saturation_s = (self.max_steering_angle - abs(current_steering_angle)) / self.max_steering_angle_rate
    timesteps_to_saturation = np.ceil(time_to_saturation_s / self.discretization_time).astype(int)
    assert timesteps_to_saturation >= 2, "We'd like at least two timesteps_to_saturation for the subsequent test."
    if np.abs(current_steering_angle) > 0.0:
        steering_rate_input = self.max_steering_angle_rate * np.sign(current_steering_angle)
    else:
        steering_rate_input = self.max_steering_angle_rate
    acceleration_input = self.max_acceleration
    test_input_trajectory: DoubleMatrix = np.ones((timesteps_to_saturation + 1, 2), dtype=np.float64)
    test_input_trajectory[:, 0] = acceleration_input
    test_input_trajectory[:, 1] = steering_rate_input
    ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
    self.assertEqual(np.abs(ilqr_iterate.state_trajectory[-2, 4]), self.max_steering_angle)
    self.assertEqual(np.amax(np.abs(ilqr_iterate.state_trajectory[:, 4])), self.max_steering_angle)
    steering_rate_unmodified = self.check_if_allclose(ilqr_iterate.input_trajectory[:, 1], test_input_trajectory[:, 1])
    self.assertFalse(steering_rate_unmodified)
    acceleration_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 3]) / self.discretization_time
    steering_rate_finite_differences = np.diff(ilqr_iterate.state_trajectory[:, 4]) / self.discretization_time
    self.assert_allclose(acceleration_finite_differences, ilqr_iterate.input_trajectory[:, 0])
    self.assert_allclose(steering_rate_finite_differences, ilqr_iterate.input_trajectory[:, 1])

def test_dynamics_and_jacobian_constraints(self) -> None:
    """Check application of constraints in dynamics."""
    test_state_in_bounds: DoubleMatrix = np.array([0.0, 0.0, 0.1, 1.0, -0.01], dtype=np.float64)
    test_state_at_bounds: DoubleMatrix = np.copy(test_state_in_bounds)
    test_state_at_bounds[4] = self.max_steering_angle
    input_at_bounds: DoubleMatrix = np.array([self.max_acceleration, self.max_steering_angle_rate], dtype=np.float64)
    test_input_in_bounds = 0.5 * input_at_bounds
    test_input_outside_bounds = 2.0 * input_at_bounds
    test_cases_dict = {}
    test_cases_dict['state_in_bounds_input_in_bounds'] = {'state': test_state_in_bounds, 'input': test_input_in_bounds, 'expect_acceleration_modified': False, 'expect_steering_rate_modified': False}
    test_cases_dict['state_at_bounds_input_in_bounds'] = {'state': test_state_at_bounds, 'input': test_input_in_bounds, 'expect_acceleration_modified': False, 'expect_steering_rate_modified': True}
    test_cases_dict['state_in_bounds_input_outside_bounds'] = {'state': test_state_in_bounds, 'input': test_input_outside_bounds, 'expect_acceleration_modified': True, 'expect_steering_rate_modified': True}
    test_cases_dict['state_at_bounds_input_outside_bounds'] = {'state': test_state_at_bounds, 'input': test_input_outside_bounds, 'expect_acceleration_modified': True, 'expect_steering_rate_modified': True}
    for test_name, test_config in test_cases_dict.items():
        next_state, applied_input, _, _ = self.solver._dynamics_and_jacobian(test_config['state'], test_config['input'])
        self.assertEqual(test_config['expect_acceleration_modified'], not self.check_if_allclose(applied_input[0], test_config['input'][0]))
        self.assertEqual(test_config['expect_steering_rate_modified'], not self.check_if_allclose(applied_input[1], test_config['input'][1]))
        self.assertLessEqual(np.abs(next_state[4]), self.max_steering_angle)

def test__run_lqr_backward_recursion(self) -> None:
    """Check some properties of the LQR input policy."""
    test_current_state = self.reference_trajectory[0]
    test_input_trajectory = self.reference_inputs
    input_perturbation: DoubleMatrix = np.array([-0.1 * self.max_acceleration, 0.1 * self.max_steering_angle], dtype=np.float64)
    test_input_trajectory[0] += input_perturbation
    ilqr_iterate = self.solver._run_forward_dynamics(test_current_state, test_input_trajectory)
    ilqr_input_policy = self.solver._run_lqr_backward_recursion(current_iterate=ilqr_iterate, reference_trajectory=self.reference_trajectory)
    state_feedback_matrices = ilqr_input_policy.state_feedback_matrices
    feedforward_inputs = ilqr_input_policy.feedforward_inputs
    self.assertTrue(np.all(np.sign(feedforward_inputs[0]) == -np.sign(input_perturbation)))
    self.assertEqual(state_feedback_matrices.shape, (self.n_horizon, self.n_inputs, self.n_states))

def test__update_inputs_with_policy(self) -> None:
    """Check how application of a specified input policy affects the next input trajectory."""
    ilqr_iterate = self.solver._run_forward_dynamics(self.reference_trajectory[0], self.reference_inputs)
    input_trajectory = ilqr_iterate.input_trajectory
    state_trajectory = ilqr_iterate.state_trajectory
    angle_distance_to_saturation = self.max_steering_angle - np.amax(np.abs(state_trajectory[:, 4]))
    test_feedforward_steering_rate = min(0.5 * angle_distance_to_saturation / (self.n_horizon * self.discretization_time), self.max_steering_angle_rate)
    feedforward_inputs = np.ones_like(input_trajectory)
    feedforward_inputs[:, 0] = self.max_acceleration
    feedforward_inputs[:, 1] = test_feedforward_steering_rate
    feedforward_inputs[1::2] *= -1.0
    state_feedback_matrices = np.zeros((len(feedforward_inputs), self.n_inputs, self.n_states))
    lqr_input_policy = ILQRInputPolicy(state_feedback_matrices=state_feedback_matrices, feedforward_inputs=feedforward_inputs)
    input_next_trajectory = self.solver._update_inputs_with_policy(current_iterate=ilqr_iterate, lqr_input_policy=lqr_input_policy)
    self.assert_allclose(feedforward_inputs, input_next_trajectory)
    test_input_perturbation = [self.max_acceleration, test_feedforward_steering_rate]
    feedforward_inputs = np.zeros_like(input_trajectory)
    feedforward_inputs[0, :] = test_input_perturbation
    state_feedback_matrices = np.zeros((len(feedforward_inputs), self.n_inputs, self.n_states))
    state_feedback_matrices[:, 0, 3] = -1.0
    state_feedback_matrices[:, 1, 4] = -1.0
    lqr_input_policy = ILQRInputPolicy(state_feedback_matrices=state_feedback_matrices, feedforward_inputs=feedforward_inputs)
    input_next_trajectory = self.solver._update_inputs_with_policy(current_iterate=ilqr_iterate, lqr_input_policy=lqr_input_policy)
    first_delta_input = input_next_trajectory[0, :] - input_trajectory[0, :]
    second_delta_input = input_next_trajectory[1, :] - input_trajectory[1, :]
    self.assertTrue(np.all(np.sign(first_delta_input) == -np.sign(second_delta_input)))

class BreadthFirstSearch:
    """
    A class that performs iterative breadth first search. The class operates on lane level graph search.
    The goal condition is specified to be if the lane can be found at the target roadblock or roadblock connector.
    """

    def __init__(self, start_edge: LaneGraphEdgeMapObject, candidate_lane_edge_ids: List[str]):
        """
        Constructor for the BreadthFirstSearch class.
        :param start_edge: The starting edge for the search
        :param candidate_lane_edge_ids: The candidates lane ids that can be included in the search.
        """
        self._queue = deque([start_edge, None])
        self._parent: Dict[str, Optional[LaneGraphEdgeMapObject]] = dict()
        self._candidate_lane_edge_ids = candidate_lane_edge_ids

    def search(self, target_roadblock: RoadBlockGraphEdgeMapObject, target_depth: int) -> Tuple[List[LaneGraphEdgeMapObject], bool]:
        """
        Performs iterative breadth first search to find a route to the target roadblock.
        :param target_roadblock: The target roadblock the path should end at.
        :param target_depth: The target depth the roadblock should be at.
        :return:
            - A route starting from the given start edge
            - A bool indicating if the route is successfully found. Successful means that there exists a path
              from the start edge to an edge contained in the end roadblock. If unsuccessful a longest route is given.
        """
        start_edge = self._queue[0]
        path_found: bool = False
        end_edge: LaneGraphEdgeMapObject = start_edge
        end_depth: int = 1
        depth: int = 1
        self._parent[start_edge.id + f'_{depth}'] = None
        while self._queue:
            current_edge = self._queue.popleft()
            if self._check_end_condition(depth, target_depth):
                break
            if current_edge is None:
                depth += 1
                self._queue.append(None)
                if self._queue[0] is None:
                    break
                continue
            if self._check_goal_condition(current_edge, target_roadblock, depth, target_depth):
                end_edge = current_edge
                end_depth = depth
                path_found = True
                break
            for next_edge in current_edge.outgoing_edges:
                if next_edge.id in self._candidate_lane_edge_ids:
                    self._queue.append(next_edge)
                    self._parent[next_edge.id + f'_{depth + 1}'] = current_edge
                    end_edge = next_edge
                    end_depth = depth + 1
        return (self._construct_path(end_edge, end_depth), path_found)

    @staticmethod
    def _check_end_condition(depth: int, target_depth: int) -> bool:
        """
        Check if the search should end regardless if the goal condition is met.
        :param depth: The current depth to check.
        :param target_depth: The target depth to check against.
        :return: True if:
            - The current depth exceeds the target depth.
        """
        return depth > target_depth

    @staticmethod
    def _check_goal_condition(current_edge: LaneGraphEdgeMapObject, target_roadblock: RoadBlockGraphEdgeMapObject, depth: int, target_depth: int) -> bool:
        """
        Check if the current edge is at the target roadblock at the given depth.
        :param current_edge: The edge to check.
        :param target_roadblock: The target roadblock the edge should be contained in.
        :param depth: The current depth to check.
        :param target_depth: The target depth the edge should be at.
        :return: True if the lane edge is contain the in the target roadblock at the target depth. False, otherwise.
        """
        return current_edge.get_roadblock_id() == target_roadblock.id and depth == target_depth

    def _construct_path(self, end_edge: LaneGraphEdgeMapObject, depth: int) -> List[LaneGraphEdgeMapObject]:
        """
        :param end_edge: The end edge to start back propagating back to the start edge.
        :param depth: The depth of the target edge.
        :return: The constructed path as a list of LaneGraphEdgeMapObject
        """
        path = [end_edge]
        while self._parent[end_edge.id + f'_{depth}'] is not None:
            path.append(self._parent[end_edge.id + f'_{depth}'])
            end_edge = self._parent[end_edge.id + f'_{depth}']
            depth -= 1
        path.reverse()
        return path

def search(self, target_roadblock: RoadBlockGraphEdgeMapObject, target_depth: int) -> Tuple[List[LaneGraphEdgeMapObject], bool]:
    """
        Performs iterative breadth first search to find a route to the target roadblock.
        :param target_roadblock: The target roadblock the path should end at.
        :param target_depth: The target depth the roadblock should be at.
        :return:
            - A route starting from the given start edge
            - A bool indicating if the route is successfully found. Successful means that there exists a path
              from the start edge to an edge contained in the end roadblock. If unsuccessful a longest route is given.
        """
    start_edge = self._queue[0]
    path_found: bool = False
    end_edge: LaneGraphEdgeMapObject = start_edge
    end_depth: int = 1
    depth: int = 1
    self._parent[start_edge.id + f'_{depth}'] = None
    while self._queue:
        current_edge = self._queue.popleft()
        if self._check_end_condition(depth, target_depth):
            break
        if current_edge is None:
            depth += 1
            self._queue.append(None)
            if self._queue[0] is None:
                break
            continue
        if self._check_goal_condition(current_edge, target_roadblock, depth, target_depth):
            end_edge = current_edge
            end_depth = depth
            path_found = True
            break
        for next_edge in current_edge.outgoing_edges:
            if next_edge.id in self._candidate_lane_edge_ids:
                self._queue.append(next_edge)
                self._parent[next_edge.id + f'_{depth + 1}'] = current_edge
                end_edge = next_edge
                end_depth = depth + 1
    return (self._construct_path(end_edge, end_depth), path_found)

class TestBreadthFirstSearch(unittest.TestCase):
    """Test class for BreadthFirstSearch"""
    TEST_FILE_PATH = 'nuplan.planning.simulation.planner.utils.breadth_first_search'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self._mock_edge = MagicMock(spec=LaneGraphEdgeMapObject)
        self._graph_search = BreadthFirstSearch(self._mock_edge, ['a'])
        self._mock_edge.id = 'a'
        self._mock_edge.get_roadblock_id.side_effect = ['1', '2', '3']
        self._mock_edge.outgoing_edges = [self._mock_edge]

    @patch(f'{TEST_FILE_PATH}.BreadthFirstSearch._check_end_condition')
    @patch(f'{TEST_FILE_PATH}.BreadthFirstSearch._check_goal_condition')
    @patch(f'{TEST_FILE_PATH}.BreadthFirstSearch._construct_path')
    def test__breadth_first_search(self, mock_construct_path: Mock, mock_check_goal_condition: Mock, mock_check_end_condition: Mock) -> None:
        """Test search()"""
        mock_check_goal_condition.side_effect = [False, False, True]
        mock_check_end_condition.side_effect = [False, False, False, False, False]
        _, path_found = self._graph_search.search(Mock(), 3)
        self.assertTrue(path_found)
        mock_check_goal_condition.assert_called()
        mock_check_end_condition.assert_called()
        mock_construct_path.assert_called_once()

    def test__construct_path(self) -> None:
        """Test _construct_path()"""
        mock_edge_1 = MagicMock(spec=LaneGraphEdgeMapObject)
        mock_edge_1.id = 'a'
        mock_edge_2 = MagicMock(spec=LaneGraphEdgeMapObject)
        mock_edge_2.id = 'b'
        self._graph_search._parent = {'a_2': mock_edge_2, 'b_1': None}
        path = self._graph_search._construct_path(mock_edge_1, 2)
        self.assertEqual(path, [mock_edge_2, mock_edge_1])

    def test__check_end_condition(self) -> None:
        """Test _check_end_condition()"""
        self.assertTrue(self._graph_search._check_end_condition(1, 0))
        self.assertFalse(self._graph_search._check_end_condition(1, 1))

    def test__check_goal_condition(self) -> None:
        """Test _check_goal_condition()"""
        mock_edge = MagicMock(spec=LaneGraphEdgeMapObject)
        mock_edge.get_roadblock_id.side_effect = ['1', '2', '3', '3']
        mock_target_block = MagicMock(spec=LaneGraphEdgeMapObject)
        mock_target_block.id = '3'
        self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 0, 3))
        self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 3, 3))
        self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 0, 3))
        self.assertTrue(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 3, 3))

def test__check_end_condition(self) -> None:
    """Test _check_end_condition()"""
    self.assertTrue(self._graph_search._check_end_condition(1, 0))
    self.assertFalse(self._graph_search._check_end_condition(1, 1))

def test__check_goal_condition(self) -> None:
    """Test _check_goal_condition()"""
    mock_edge = MagicMock(spec=LaneGraphEdgeMapObject)
    mock_edge.get_roadblock_id.side_effect = ['1', '2', '3', '3']
    mock_target_block = MagicMock(spec=LaneGraphEdgeMapObject)
    mock_target_block.id = '3'
    self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 0, 3))
    self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 3, 3))
    self.assertFalse(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 0, 3))
    self.assertTrue(self._graph_search._check_goal_condition(mock_edge, mock_target_block, 3, 3))

class TestValidationCallback(unittest.TestCase):
    """Tests for the ValidationCallback class"""

    def test_initialization(self) -> None:
        """Tests that the object is constructed correctly"""
        callback = ValidationCallback(output_dir='out', validation_dir_name='validation')
        self.assertEqual(str(callback.output_dir), 'out')
        self.assertEqual(callback._validation_dir_name, 'validation')

    def test_on_run_simulation_end(self) -> None:
        """Tests that the correct files are created in the callback."""
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        callback = ValidationCallback(output_dir=tmp_dir.name, validation_dir_name='validation')
        with patch(f'{TEST_FILE}._validation_succeeded', Mock(return_value=False)):
            callback.on_run_simulation_end()
            self.assertTrue(os.path.exists('/'.join([tmp_dir.name, 'validation', 'failed.txt'])))
        with patch(f'{TEST_FILE}._validation_succeeded', Mock(return_value=True)):
            callback.on_run_simulation_end()
            self.assertTrue(os.path.exists('/'.join([tmp_dir.name, 'validation', 'passed.txt'])))

    def test__validation_succeeded(self) -> None:
        """Tests that helper function reads the runners_report file correctly."""
        with patch(f'{TEST_FILE}.pd.read_parquet', Mock(side_effect=FileNotFoundError)):
            result = _validation_succeeded(Mock())
            self.assertFalse(result)
        failed_df = pd.DataFrame({'succeeded': [True, False]})
        with patch(f'{TEST_FILE}.pd.read_parquet', Mock(return_value=failed_df)):
            result = _validation_succeeded(Mock())
            self.assertFalse(result)
        passed_df = pd.DataFrame({'succeeded': [True, True]})
        with patch(f'{TEST_FILE}.pd.read_parquet', Mock(return_value=passed_df)):
            result = _validation_succeeded(Mock())
            self.assertTrue(result)

def test__validation_succeeded(self) -> None:
    """Tests that helper function reads the runners_report file correctly."""
    with patch(f'{TEST_FILE}.pd.read_parquet', Mock(side_effect=FileNotFoundError)):
        result = _validation_succeeded(Mock())
        self.assertFalse(result)
    failed_df = pd.DataFrame({'succeeded': [True, False]})
    with patch(f'{TEST_FILE}.pd.read_parquet', Mock(return_value=failed_df)):
        result = _validation_succeeded(Mock())
        self.assertFalse(result)
    passed_df = pd.DataFrame({'succeeded': [True, True]})
    with patch(f'{TEST_FILE}.pd.read_parquet', Mock(return_value=passed_df)):
        result = _validation_succeeded(Mock())
        self.assertTrue(result)

def path_to_linestring(path: List[StateSE2]) -> LineString:
    """
    Converts a List of StateSE2 into a LineString
    :param path: path to be converted
    :return: LineString.
    """
    return LineString([(point.x, point.y) for point in path])

def calculate_progress(path: List[StateSE2]) -> List[float]:
    """
    Calculate the cumulative progress of a given path

    :param path: a path consisting of StateSE2 as waypoints
    :return: a cumulative list of progress
    """
    x_position = [point.x for point in path]
    y_position = [point.y for point in path]
    x_diff = np.diff(x_position)
    y_diff = np.diff(y_position)
    points_diff: npt.NDArray[np.float_] = np.concatenate(([x_diff], [y_diff]), axis=0)
    progress_diff = np.append(0, np.linalg.norm(points_diff, axis=0))
    return np.cumsum(progress_diff).tolist()

class TestLocalMLP(unittest.TestCase):
    """Test LocalMLP layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.dim_in = 256
        self.model = LocalMLP(self.dim_in)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_inputs = 10
        inputs = torch.zeros((num_inputs, self.dim_in))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_inputs, self.dim_in))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestMLP(unittest.TestCase):
    """Test MLP layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.input_dim = 256
        self.hidden_dim = 256 * 4
        self.output_dim = 12 * 3
        self.num_layers = 3
        self.model = MLP(self.input_dim, self.hidden_dim, self.output_dim, self.num_layers)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_inputs = 10
        inputs = torch.zeros((num_inputs, self.input_dim))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_inputs, self.output_dim))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestSinusoidalPositionalEmbedding(unittest.TestCase):
    """Test SinusoidalPositionalEmbedding layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.embedding_size = 256
        self.model = SinusoidalPositionalEmbedding(self.embedding_size)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((batch_size, num_elements, num_points, self.embedding_size))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_points, 1, self.embedding_size))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestTypeEmbedding(unittest.TestCase):
    """Test TypeEmbedding layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.embedding_dim = 256
        self.feature_types = {'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}
        self.model = TypeEmbedding(self.embedding_dim, self.feature_types)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        device = torch.device('cpu')
        batch_size = 2
        max_agents = 30
        agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
        map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
        max_elements = {'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}
        num_elements = 1 + max_agents * len(agent_features) + sum(max_elements.values())
        output = self.model.forward(batch_size, max_agents, agent_features, map_features, max_elements, device)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, num_elements, self.embedding_dim))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestLocalSubGraphLayer(unittest.TestCase):
    """Test LocalSubGraphLayer layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.dim_in = 256
        self.dim_out = 256
        self.model = LocalSubGraphLayer(self.dim_in, self.dim_out)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((num_elements, num_points, self.dim_in))
        invalid_mask = torch.zeros((num_elements, num_points), dtype=torch.bool)
        output = self.model.forward(inputs, invalid_mask)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_elements, num_points, self.dim_out))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestLocalSubGraph(unittest.TestCase):
    """Test LocalSubGraph layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.num_layers = 3
        self.dim_in = 256
        self.model = LocalSubGraph(self.num_layers, self.dim_in)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((batch_size, num_elements, num_points, self.dim_in), dtype=torch.float32)
        invalid_mask = torch.zeros((batch_size, num_elements, num_points), dtype=torch.bool)
        pos_enc = torch.zeros((1, 1, num_points, self.dim_in), dtype=torch.float32)
        output = self.model.forward(inputs, invalid_mask, pos_enc)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, num_elements, self.dim_in))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestMultiheadAttentionGlobalHead(unittest.TestCase):
    """Test MultiheadAttentionGlobalHead layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.global_embedding_size = 256
        self.num_timesteps = 12
        self.num_outputs = 3
        self.model = MultiheadAttentionGlobalHead(self.global_embedding_size, self.num_timesteps, self.num_outputs)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        inputs = torch.zeros((num_elements, batch_size, self.global_embedding_size), dtype=torch.float32)
        type_embedding = torch.ones((num_elements, batch_size, self.global_embedding_size), dtype=torch.long)
        invalid_mask = torch.zeros((batch_size, num_elements), dtype=torch.bool)
        output, attns = self.model.forward(inputs, type_embedding, invalid_mask)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, self.num_timesteps, self.num_outputs))
        self.assertIsInstance(attns, torch.Tensor)
        assert attns is not None
        self.assertEqual(attns.shape, (batch_size, 1, num_elements))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

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

def _assert_valid_output(self, model_output: TargetsType) -> None:
    """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
    self.assertTrue('trajectory' in model_output)
    self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
    predicted_trajectory: Trajectory = model_output['trajectory']
    self.assertIsNotNone(predicted_trajectory.data)

class TestGraphAttention(unittest.TestCase):
    """Test graph attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.src_feature_len = 4
        self.dst_feature_len = 4
        self.dist_threshold = 6.0
        self.model = GraphAttention(self.src_feature_len, self.dst_feature_len, self.dist_threshold)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_src_nodes = 2
        num_dst_nodes = 3
        src_node_features = torch.zeros((num_src_nodes, self.src_feature_len))
        src_node_pos = torch.zeros((num_src_nodes, 2))
        dst_node_features = torch.zeros((num_dst_nodes, self.dst_feature_len))
        dst_node_pos = torch.zeros((num_dst_nodes, 2))
        output = self.model.forward(src_node_features, src_node_pos, dst_node_features, dst_node_pos)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_dst_nodes, self.dst_feature_len))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works
        """
    self.assertNotEqual(self.model, None)

class TestActor2ActorAttention(unittest.TestCase):
    """Test actor-to-actor attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Actor2ActorAttention(self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_actors = 3
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(actor_features, actor_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_actors, self.actor_feature_len))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works.
        """
    self.assertNotEqual(self.model, None)

class TestLane2ActorAttention(unittest.TestCase):
    """Test lane-to-actor attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.lane_feature_len = 4
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Lane2ActorAttention(self.lane_feature_len, self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 2
        num_actors = 3
        lane_features = torch.zeros((num_lanes, self.lane_feature_len))
        lane_centers = torch.zeros((num_lanes, 2))
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(lane_features, lane_centers, actor_features, actor_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_actors, self.actor_feature_len))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works
        """
    self.assertNotEqual(self.model, None)

class TestActor2LaneAttention(unittest.TestCase):
    """Test actor-to-lane attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.lane_feature_len = 4
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Actor2LaneAttention(self.actor_feature_len, self.lane_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 2
        num_actors = 3
        meta_info_len = 6
        lane_features = torch.zeros((num_lanes, self.lane_feature_len))
        lane_meta = torch.zeros((num_lanes, meta_info_len))
        lane_centers = torch.zeros((num_lanes, 2))
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(actor_features, actor_centers, lane_features, lane_meta, lane_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_lanes, self.actor_feature_len))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works
        """
    self.assertNotEqual(self.model, None)

class TestLaneNet(unittest.TestCase):
    """Test lane net layer."""

    def setUp(self) -> None:
        """Set up the test."""
        self.lane_input_len = 2
        self.lane_feature_len = 4
        self.num_scales = 2
        self.num_res_blocks = 3
        self.model = LaneNet(lane_input_len=self.lane_input_len, lane_feature_len=self.lane_feature_len, num_scales=self.num_scales, num_residual_blocks=self.num_res_blocks, is_map_feat=False)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 4
        lane_input = torch.zeros((num_lanes, self.lane_input_len, 2))
        multi_scale_connections = {1: torch.tensor([[0, 1], [1, 2], [2, 3]]), 2: torch.tensor([[0, 2], [1, 3]])}
        vector_map = Munch(multi_scale_connections=multi_scale_connections)
        output = self.model.forward(lane_input, vector_map.multi_scale_connections)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_lanes, self.lane_feature_len))

def test_instantiate(self) -> None:
    """
        Dummy test to check that instantiation works
        """
    self.assertNotEqual(self.model, None)

class TestLaneGCN(unittest.TestCase):
    """Test LaneGCN model."""

    def _build_model(self) -> LaneGCN:
        """
        Creates a new instance of a LaneGCN with some default parameters.
        """
        model = LaneGCN(map_net_scales=4, num_res_blocks=4, num_attention_layers=5, a2a_dist_threshold=20, l2a_dist_threshold=20, num_output_features=12, feature_dim=32, vector_map_feature_radius=30, vector_map_connection_scales=[1, 2, 3, 4], past_trajectory_sampling=TrajectorySampling(num_poses=4, time_horizon=1.5), future_trajectory_sampling=TrajectorySampling(num_poses=12, time_horizon=6))
        return model

    def _build_input_features(self, device: torch.device, include_agents: bool, include_lanes: bool) -> FeaturesType:
        """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :param include_lanes: If true, the generated input features will have lanes.
            If not, then there will be no lanes in the vectormap feature.
        :return: FeaturesType to be consumed by the model
        """
        num_frames = 5
        num_coords = 1000
        num_groupings = 100
        num_multi_scale_connections = 800
        num_lanes = num_coords if include_lanes else 0
        num_connections = num_multi_scale_connections if include_lanes else 0
        num_agents = num_frames if include_agents else 0
        vector_map_coords = [torch.zeros((num_lanes, VectorMap.lane_coord_dim(), VectorMap.lane_coord_dim()), dtype=torch.float32, device=device)]
        vector_map_lane_groupings = [[torch.zeros(num_groupings, device=device)]]
        multi_scale_connections = [{1: torch.zeros((num_connections, 2), device=device).long(), 2: torch.zeros((num_connections, 2), device=device).long(), 3: torch.zeros((num_connections, 2), device=device).long(), 4: torch.zeros((num_connections, 2), device=device).long()}]
        on_route_status = [torch.zeros((num_lanes, VectorMap.on_route_status_encoding_dim()), device=device)]
        traffic_light_data = [torch.zeros((num_lanes, 4), device=device)]
        vector_map_feature = VectorMap(coords=vector_map_coords, lane_groupings=vector_map_lane_groupings, multi_scale_connections=multi_scale_connections, on_route_status=on_route_status, traffic_light_data=traffic_light_data)
        ego_agents = [torch.zeros((num_frames, Agents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = [torch.zeros((num_frames, num_agents, Agents.agents_states_dim()), dtype=torch.float32, device=device)]
        agents_feature = Agents(ego=ego_agents, agents=agent_agents)
        return {'vector_map': vector_map_feature, 'agents': agents_feature}

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
        Tests that the LaneGCN model can train with DDP.
        This test was developed in response to an error related to zero agent input.
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
                for include_lanes in [True, False]:
                    input_features = self._build_input_features(device, include_agents=include_agents, include_lanes=include_lanes)
                    predictions = ddp_model.forward(input_features)
                    self._assert_valid_output(predictions)
                    self._perform_backprop_step(optimizer, loss_function, predictions)

def _assert_valid_output(self, model_output: TargetsType) -> None:
    """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
    self.assertTrue('trajectory' in model_output)
    self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
    predicted_trajectory: Trajectory = model_output['trajectory']
    self.assertIsNotNone(predicted_trajectory.data)

class TestVectorMapSimpleMLP(unittest.TestCase):
    """Test graph attention layer."""

    def _build_model(self) -> VectorMapSimpleMLP:
        """
        Creates a new instance of a VectorMapSimpleMLP with some default parameters.
        """
        num_output_features = 36
        hidden_size = 128
        vector_map_feature_radius = 20
        past_trajectory_sampling = TrajectorySampling(num_poses=4, time_horizon=1.5)
        future_trajectory_sampling = TrajectorySampling(num_poses=12, time_horizon=6)
        model = VectorMapSimpleMLP(num_output_features=num_output_features, hidden_size=hidden_size, vector_map_feature_radius=vector_map_feature_radius, past_trajectory_sampling=past_trajectory_sampling, future_trajectory_sampling=future_trajectory_sampling)
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
        num_coords = 1000
        num_groupings = 100
        num_multi_scale_connections = 800
        num_agents = num_frames if include_agents else 0
        vector_map_coords = [torch.zeros((num_coords, VectorMap.lane_coord_dim(), VectorMap.lane_coord_dim()), dtype=torch.float32, device=device)]
        vector_map_lane_groupings = [[torch.zeros(num_groupings, device=device)]]
        multi_scale_connections = {1: [torch.zeros((num_multi_scale_connections, 2), device=device)]}
        on_route_status = [torch.zeros((num_coords, VectorMap.on_route_status_encoding_dim()), device=device)]
        traffic_light_data = [torch.zeros((num_coords, 4), device=device)]
        vector_map_feature = VectorMap(coords=vector_map_coords, lane_groupings=vector_map_lane_groupings, multi_scale_connections=multi_scale_connections, on_route_status=on_route_status, traffic_light_data=traffic_light_data)
        ego_agents = [torch.zeros((num_frames, Agents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = [torch.zeros((num_frames, num_agents, Agents.agents_states_dim()), dtype=torch.float32, device=device)]
        agents_feature = Agents(ego=ego_agents, agents=agent_agents)
        return {'vector_map': vector_map_feature, 'agents': agents_feature}

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
        :param port: The starting to use for the gloo server. If taken, it will increment by 1 until a free port is found.
        :param max_port: The maximum port number to try.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def _assert_valid_gradients_for_model(self, model: torch.nn.Module) -> None:
        """
        Validates that trainable parameters in a model have gradients after a backprop operation.
        :param model: The model with parameters to update following a forward/backward pass.
        """
        all_gradients_computed = all((param.grad is not None for param in model.parameters() if param.requires_grad))
        self.assertTrue(all_gradients_computed)

    def test_can_train_distributed(self) -> None:
        """
        Tests that the model can train with DDP.
        This test was developed in response to an error like this one:
        https://discuss.pytorch.org/t/need-help-runtimeerror-expected-to-have-finished-reduction-in-the-prior-iteration-before-starting-a-new-one/119247
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
                self._assert_valid_gradients_for_model(ddp_model)

    def test_scripts_properly(self) -> None:
        """
        Test that the VectorMapSimpleMLP model scripts properly.
        """
        model = self._build_model()
        device = torch.device('cpu')
        input_features = self._build_input_features(device, include_agents=True)
        dummy_tensor_input: Dict[str, torch.Tensor] = {}
        dummy_list_tensor_input = {'vector_map.coords': input_features['vector_map'].coords, 'agents.ego': input_features['agents'].ego, 'agents.agents': input_features['agents'].agents}
        dummy_list_list_tensor_input: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_module = torch.jit.script(model)
        scripted_tensors, scripted_list_tensors, scripted_list_list_tensors = scripted_module.scriptable_forward(dummy_tensor_input, dummy_list_tensor_input, dummy_list_list_tensor_input)
        py_tensors, py_list_tensors, py_list_list_tensors = model.scriptable_forward(dummy_tensor_input, dummy_list_tensor_input, dummy_list_list_tensor_input)
        self.assertEqual(1, len(scripted_tensors))
        self.assertEqual(0, len(scripted_list_tensors))
        self.assertEqual(0, len(scripted_list_list_tensors))
        self.assertEqual(1, len(py_tensors))
        self.assertEqual(0, len(py_list_tensors))
        self.assertEqual(0, len(py_list_list_tensors))
        torch.testing.assert_allclose(py_tensors['trajectory'], scripted_tensors['trajectory'])

    def test_can_train_with_empty_vector_map(self) -> None:
        """In case of zero length vector map features, model training should not crash."""
        device = torch.device('cpu')
        test_features = self._build_input_features(device=device, include_agents=True)
        test_features['vector_map'] = _create_empty_vector_map_for_test(device=device)
        self.assertFalse(test_features['vector_map'].is_valid)
        model = self._build_model().to(device)
        optimizer = torch.optim.RMSprop(model.parameters())
        loss_function = torch.nn.MSELoss()
        predictions = model.forward(test_features)
        self._assert_valid_output(predictions)
        self._perform_backprop_step(optimizer, loss_function, predictions)
        self._assert_valid_gradients_for_model(model)

def _assert_valid_output(self, model_output: TargetsType) -> None:
    """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
    self.assertTrue('trajectory' in model_output)
    self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
    predicted_trajectory: Trajectory = model_output['trajectory']
    self.assertIsNotNone(predicted_trajectory.data)

def _assert_valid_gradients_for_model(self, model: torch.nn.Module) -> None:
    """
        Validates that trainable parameters in a model have gradients after a backprop operation.
        :param model: The model with parameters to update following a forward/backward pass.
        """
    all_gradients_computed = all((param.grad is not None for param in model.parameters() if param.requires_grad))
    self.assertTrue(all_gradients_computed)

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

def extract_field_from_cache_metadata_entries(cache_metadata_entries: List[CacheMetadataEntry], desired_attribute: str) -> List[Any]:
    """
    Extracts specified field from cache metadata entries.
    :param cache_metadata_entries: List of CacheMetadataEntry
    :return: List of desired attributes in each CacheMetadataEntry
    """
    metadata = [getattr(entry, desired_attribute) for entry in cache_metadata_entries]
    return metadata

def _batch_scenarios(to_be_batched_scenarios: List[ScenarioListType]) -> ScenarioListType:
    return sum(to_be_batched_scenarios, [])

class TestAgentsFeatureBuilder(unittest.TestCase):
    """Test feature builder that constructs features with vectorized agent information."""

    def setUp(self) -> None:
        """Set up test case."""
        self.num_frames = 8
        self.num_agents = 10
        self.num_missing_agents = 2
        self.agent_trajectories = [*_create_tracked_objects(5, self.num_agents), *_create_tracked_objects(3, self.num_agents - self.num_missing_agents)]
        self.time_stamps = [TimePoint(step) for step in range(self.num_frames)]

    def test_build_ego_features(self) -> None:
        """
        Test the ego feature building
        """
        num_frames = 5
        ego_trajectory = _create_ego_trajectory(num_frames)
        ego_features = build_ego_features(ego_trajectory)
        self.assertEqual((num_frames, EgoFeatureIndex.dim()), ego_features.shape)
        self.assertTrue(np.allclose(ego_features[0], np.array([0, 0, 0])))
        ego_features_reversed = build_ego_features(ego_trajectory, reverse=True)
        self.assertEqual((num_frames, EgoFeatureIndex.dim()), ego_features_reversed.shape)
        self.assertTrue(np.allclose(ego_features_reversed[-1], np.array([0, 0, 0])))

    def test_extract_and_pad_agent_poses(self) -> None:
        """
        Test when there is agent pose trajectory is incomplete
        """
        padded_poses, availability = extract_and_pad_agent_poses(self.agent_trajectories)
        availability = np.asarray(availability)
        stacked_poses = np.stack([[agent.serialize() for agent in frame] for frame in padded_poses])
        self.assertEqual(stacked_poses.shape[0], self.num_frames)
        self.assertEqual(stacked_poses.shape[1], self.num_agents)
        self.assertEqual(stacked_poses.shape[2], 3)
        self.assertEqual(len(availability.shape), 2)
        self.assertEqual(availability.shape[0], self.num_frames)
        self.assertEqual(availability.shape[1], self.num_agents)
        self.assertTrue(availability[:5, :].all())
        self.assertTrue(availability[:, :self.num_agents - self.num_missing_agents].all())
        self.assertTrue((~availability[5:, -self.num_missing_agents:]).all())
        padded_poses_reversed, availability_reversed = extract_and_pad_agent_poses(self.agent_trajectories[::-1], reverse=True)
        availability_reversed = np.asarray(availability_reversed)
        stacked_poses = np.stack([[agent.serialize() for agent in frame] for frame in padded_poses_reversed])
        self.assertEqual(stacked_poses.shape[0], self.num_frames)
        self.assertEqual(stacked_poses.shape[1], self.num_agents)
        self.assertEqual(stacked_poses.shape[2], 3)
        self.assertEqual(len(availability_reversed.shape), 2)
        self.assertEqual(availability_reversed.shape[0], self.num_frames)
        self.assertEqual(availability_reversed.shape[1], self.num_agents)
        self.assertTrue(availability_reversed[-5:, :].all())
        self.assertTrue(availability_reversed[:, :self.num_agents - self.num_missing_agents].all())
        self.assertTrue((~availability_reversed[:3, -self.num_missing_agents:]).all())

    def test_extract_and_pad_agent_sizes(self) -> None:
        """
        Test when there is agent size trajectory is incomplete
        """
        padded_sizes, _ = extract_and_pad_agent_sizes(self.agent_trajectories)
        stacked_sizes = np.stack(padded_sizes)
        self.assertEqual(stacked_sizes.shape[0], self.num_frames)
        self.assertEqual(stacked_sizes.shape[1], self.num_agents)
        self.assertEqual(stacked_sizes.shape[2], 2)
        padded_sizes_reversed, _ = extract_and_pad_agent_sizes(self.agent_trajectories[::-1], reverse=True)
        stacked_sizes = np.stack(padded_sizes_reversed)
        self.assertEqual(stacked_sizes.shape[0], self.num_frames)
        self.assertEqual(stacked_sizes.shape[1], self.num_agents)
        self.assertEqual(stacked_sizes.shape[2], 2)

    def test_extract_and_pad_agent_velocities(self) -> None:
        """
        Test when there is agent velocity trajectory is incomplete
        """
        padded_velocities, _ = extract_and_pad_agent_velocities(self.agent_trajectories)
        stacked_velocities = np.stack([[agent.serialize() for agent in frame] for frame in padded_velocities])
        self.assertEqual(stacked_velocities.shape[0], self.num_frames)
        self.assertEqual(stacked_velocities.shape[1], self.num_agents)
        self.assertEqual(stacked_velocities.shape[2], 3)
        padded_velocities_reversed, _ = extract_and_pad_agent_velocities(self.agent_trajectories[::-1], reverse=True)
        stacked_velocities = np.stack([[agent.serialize() for agent in frame] for frame in padded_velocities_reversed])
        self.assertEqual(stacked_velocities.shape[0], self.num_frames)
        self.assertEqual(stacked_velocities.shape[1], self.num_agents)
        self.assertEqual(stacked_velocities.shape[2], 3)

    def test_compute_yaw_rate_from_states(self) -> None:
        """
        Test computing yaw from the agent pose trajectory
        """
        padded_poses, _ = extract_and_pad_agent_poses(self.agent_trajectories)
        yaw_rates = compute_yaw_rate_from_states(padded_poses, self.time_stamps)
        self.assertEqual(yaw_rates.transpose().shape[0], self.num_frames)
        self.assertEqual(yaw_rates.transpose().shape[1], self.num_agents)

    def test_filter_agents(self) -> None:
        """
        Test agent filtering
        """
        num_frames = 8
        num_agents = 5
        missing_agents = 2
        tracked_objects_history = [*_create_tracked_objects(num_frames=5, num_agents=num_agents, object_type=TrackedObjectType.VEHICLE), *_create_tracked_objects(num_frames=2, num_agents=num_agents - missing_agents, object_type=TrackedObjectType.BICYCLE), *_create_tracked_objects(num_frames=1, num_agents=num_agents - missing_agents, object_type=TrackedObjectType.VEHICLE)]
        filtered_agents = filter_agents(tracked_objects_history)
        self.assertEqual(len(filtered_agents), num_frames)
        self.assertEqual(len(filtered_agents[0].tracked_objects), len(tracked_objects_history[0].tracked_objects))
        self.assertEqual(len(filtered_agents[5].tracked_objects), 0)
        self.assertEqual(len(filtered_agents[7].tracked_objects), num_agents - missing_agents)
        filtered_agents = filter_agents(tracked_objects_history, reverse=True)
        self.assertEqual(len(filtered_agents), num_frames)
        self.assertEqual(len(filtered_agents[0].tracked_objects), len(tracked_objects_history[-1].tracked_objects))
        self.assertEqual(len(filtered_agents[5].tracked_objects), 0)
        self.assertEqual(len(filtered_agents[7].tracked_objects), num_agents - missing_agents)
        tracked_objects_history = [*_create_tracked_objects(num_frames=5, num_agents=num_agents, object_type=TrackedObjectType.BICYCLE), *_create_tracked_objects(num_frames=2, num_agents=num_agents - missing_agents, object_type=TrackedObjectType.VEHICLE), *_create_tracked_objects(num_frames=1, num_agents=num_agents - missing_agents, object_type=TrackedObjectType.BICYCLE)]
        filtered_agents = filter_agents(tracked_objects_history, allowable_types=[TrackedObjectType.BICYCLE])
        self.assertEqual(len(filtered_agents), num_frames)
        self.assertEqual(len(filtered_agents[0].tracked_objects), len(tracked_objects_history[0].tracked_objects))
        self.assertEqual(len(filtered_agents[5].tracked_objects), 0)
        self.assertEqual(len(filtered_agents[7].tracked_objects), num_agents - missing_agents)

    def test_build_ego_features_from_tensor(self) -> None:
        """
        Test the ego feature building
        """
        num_frames = 5
        zeros = torch.tensor([0, 0, 0], dtype=torch.float32)
        ego_trajectory = _create_ego_trajectory_tensor(num_frames)
        ego_features = build_ego_features_from_tensor(ego_trajectory)
        self.assertEqual((num_frames, EgoFeatureIndex.dim()), ego_features.shape)
        self.assertTrue(torch.allclose(ego_features[0], zeros, atol=1e-07))
        ego_features_reversed = build_ego_features_from_tensor(ego_trajectory, reverse=True)
        self.assertEqual((num_frames, EgoFeatureIndex.dim()), ego_features_reversed.shape)
        self.assertTrue(torch.allclose(ego_features_reversed[-1], zeros, atol=1e-07))

    def test_build_generic_ego_features_from_tensor(self) -> None:
        """
        Test the ego feature building
        """
        num_frames = 5
        zeros = torch.tensor([0, 0, 0, 0, 0, 0, 0], dtype=torch.float32)
        ego_trajectory = _create_ego_trajectory_tensor(num_frames)
        ego_features = build_generic_ego_features_from_tensor(ego_trajectory)
        self.assertEqual((num_frames, GenericEgoFeatureIndex.dim()), ego_features.shape)
        self.assertTrue(torch.allclose(ego_features[0], zeros, atol=1e-07))
        ego_features_reversed = build_generic_ego_features_from_tensor(ego_trajectory, reverse=True)
        self.assertEqual((num_frames, GenericEgoFeatureIndex.dim()), ego_features_reversed.shape)
        self.assertTrue(torch.allclose(ego_features_reversed[-1], zeros, atol=1e-07))

    def test_convert_absolute_quantities_to_relative(self) -> None:
        """
        Test the conversion routine between absolute and relative quantities
        """

        def get_dummy_states() -> List[torch.Tensor]:
            """
            Create a series of dummy agent tensors
            """
            dummy_agent_state = _create_tracked_object_agent_tensor(7)
            dummy_states = [dummy_agent_state + i for i in range(5)]
            return dummy_states
        zeros = torch.tensor([0, 0, 0], dtype=torch.float32)
        dummy_states = get_dummy_states()
        ego_pose = torch.tensor([4, 4, 4, 2, 2, 2, 2], dtype=torch.float32)
        transformed = convert_absolute_quantities_to_relative(dummy_states, ego_pose)
        for i in range(0, len(transformed), 1):
            should_be_zero_row = 4 - i
            check_tensor = torch.tensor([transformed[i][should_be_zero_row, AgentInternalIndex.x()].item(), transformed[i][should_be_zero_row, AgentInternalIndex.y()].item(), transformed[i][should_be_zero_row, AgentInternalIndex.heading()].item()], dtype=torch.float32)
            self.assertTrue(torch.allclose(check_tensor, zeros, atol=1e-07))
        dummy_states = get_dummy_states()
        ego_pose = torch.tensor([2, 2, 4, 4, 4, 4, 4], dtype=torch.float32)
        transformed = convert_absolute_quantities_to_relative(dummy_states, ego_pose)
        for i in range(0, len(transformed), 1):
            should_be_zero_row = 4 - i
            check_tensor = torch.tensor([transformed[i][should_be_zero_row, AgentInternalIndex.vx()].item(), transformed[i][should_be_zero_row, AgentInternalIndex.vy()].item(), transformed[i][should_be_zero_row, AgentInternalIndex.heading()].item()], dtype=torch.float32)
            self.assertTrue(torch.allclose(check_tensor, zeros, atol=1e-07))

    def test_pad_agent_states(self) -> None:
        """
        Test the pad agent states functionality
        """
        forward_dummy_states = [_create_tracked_object_agent_tensor(7), _create_tracked_object_agent_tensor(5), _create_tracked_object_agent_tensor(6)]
        padded = pad_agent_states(forward_dummy_states, reverse=False)
        self.assertTrue(len(padded) == 3)
        self.assertEqual((7, AgentInternalIndex.dim()), padded[0].shape)
        for i in range(1, len(padded)):
            self.assertTrue(torch.allclose(padded[0], padded[i]))
        backward_dummy_states = [_create_tracked_object_agent_tensor(6), _create_tracked_object_agent_tensor(5), _create_tracked_object_agent_tensor(7)]
        padded_reverse = pad_agent_states(backward_dummy_states, reverse=True)
        self.assertTrue(len(padded_reverse) == 3)
        self.assertEqual((7, AgentInternalIndex.dim()), padded_reverse[2].shape)
        for i in range(0, len(padded_reverse) - 1):
            self.assertTrue(torch.allclose(padded_reverse[2], padded_reverse[i]))

    def test_compute_yaw_rate_from_state_tensors(self) -> None:
        """
        Test compute yaw rate functionality
        """
        num_frames = 6
        num_agents = 5
        agent_states = [_create_tracked_object_agent_tensor(num_agents) + i for i in range(num_frames)]
        time_stamps = torch.tensor([int(i * 1000000.0) for i in range(num_frames)], dtype=torch.int64)
        yaw_rate = compute_yaw_rate_from_state_tensors(agent_states, time_stamps)
        self.assertEqual((num_frames, num_agents), yaw_rate.shape)
        self.assertTrue(torch.allclose(torch.ones((num_frames, num_agents), dtype=torch.float64), yaw_rate))

    def test_filter_agents_tensor(self) -> None:
        """
        Test filter agents
        """
        dummy_states = [_create_tracked_object_agent_tensor(7), _create_tracked_object_agent_tensor(8), _create_tracked_object_agent_tensor(6)]
        filtered = filter_agents_tensor(dummy_states, reverse=False)
        self.assertEqual((7, AgentInternalIndex.dim()), filtered[0].shape)
        self.assertEqual((7, AgentInternalIndex.dim()), filtered[1].shape)
        self.assertEqual((6, AgentInternalIndex.dim()), filtered[2].shape)
        dummy_states = [_create_tracked_object_agent_tensor(6), _create_tracked_object_agent_tensor(8), _create_tracked_object_agent_tensor(7)]
        filtered_reverse = filter_agents_tensor(dummy_states, reverse=True)
        self.assertEqual((6, AgentInternalIndex.dim()), filtered_reverse[0].shape)
        self.assertEqual((7, AgentInternalIndex.dim()), filtered_reverse[1].shape)
        self.assertEqual((7, AgentInternalIndex.dim()), filtered_reverse[2].shape)

    def test_sampled_past_ego_states_to_tensor(self) -> None:
        """
        Test the conversion routine to convert ego states to tensors.
        """
        num_egos = 6
        test_egos = []
        for i in range(num_egos):
            footprint = CarFootprint(center=StateSE2(x=i, y=i, heading=i), vehicle_parameters=VehicleParameters(vehicle_name='vehicle_name', vehicle_type='vehicle_type', width=i, front_length=i, rear_length=i, cog_position_from_rear_axle=i, wheel_base=i, height=i))
            dynamic_car_state = DynamicCarState(rear_axle_to_center_dist=i, rear_axle_velocity_2d=StateVector2D(x=i + 5, y=i + 5), rear_axle_acceleration_2d=StateVector2D(x=i, y=i), angular_velocity=i, angular_acceleration=i, tire_steering_rate=i)
            test_ego = EgoState(car_footprint=footprint, dynamic_car_state=dynamic_car_state, tire_steering_angle=i, is_in_auto_mode=i, time_point=TimePoint(time_us=i))
            test_egos.append(test_ego)
        tensor = sampled_past_ego_states_to_tensor(test_egos)
        self.assertEqual((6, EgoInternalIndex.dim()), tensor.shape)
        for i in range(0, tensor.shape[0], 1):
            ego = test_egos[i]
            self.assertEqual(ego.rear_axle.x, tensor[i, EgoInternalIndex.x()].item())
            self.assertEqual(ego.rear_axle.y, tensor[i, EgoInternalIndex.y()].item())
            self.assertEqual(ego.rear_axle.heading, tensor[i, EgoInternalIndex.heading()].item())
            self.assertEqual(ego.dynamic_car_state.rear_axle_velocity_2d.x, tensor[i, EgoInternalIndex.vx()].item())
            self.assertEqual(ego.dynamic_car_state.rear_axle_velocity_2d.y, tensor[i, EgoInternalIndex.vy()].item())
            self.assertEqual(ego.dynamic_car_state.rear_axle_acceleration_2d.x, tensor[i, EgoInternalIndex.ax()].item())
            self.assertEqual(ego.dynamic_car_state.rear_axle_acceleration_2d.y, tensor[i, EgoInternalIndex.ay()].item())

    def test_sampled_past_timestamps_to_tensor(self) -> None:
        """
        Test the conversion routine to convert timestamps to tensors.
        """
        points = [TimePoint(time_us=i) for i in range(10)]
        tensor = sampled_past_timestamps_to_tensor(points)
        self.assertEqual((10,), tensor.shape)
        for i in range(tensor.shape[0]):
            self.assertEqual(i, int(tensor[i].item()))

    def test_tracked_objects_to_tensor_list(self) -> None:
        """
        Test the conversion routine to convert tracked objects to tensors.
        """
        num_frames = 5
        test_tracked_objects = _create_dummy_tracked_objects_tensor(num_frames)
        tensors = sampled_tracked_objects_to_tensor_list(test_tracked_objects)
        self.assertEqual(num_frames, len(tensors))
        for idx, generated_tensor in enumerate(tensors):
            expected_num_agents = idx + 1
            self.assertEqual((expected_num_agents, AgentInternalIndex.dim()), generated_tensor.shape)
            for row in range(generated_tensor.shape[0]):
                for col in range(generated_tensor.shape[1]):
                    self.assertEqual(row + col, int(generated_tensor[row, col].item()))
        tensors = sampled_tracked_objects_to_tensor_list(test_tracked_objects, object_type=TrackedObjectType.BICYCLE)
        self.assertEqual(num_frames, len(tensors))
        for idx, generated_tensor in enumerate(tensors):
            expected_num_agents = idx + 1
            self.assertEqual((expected_num_agents, AgentInternalIndex.dim()), generated_tensor.shape)
            for row in range(generated_tensor.shape[0]):
                for col in range(generated_tensor.shape[1]):
                    self.assertEqual(row + col, int(generated_tensor[row, col].item()))
        tensors = sampled_tracked_objects_to_tensor_list(test_tracked_objects, object_type=TrackedObjectType.PEDESTRIAN)
        self.assertEqual(num_frames, len(tensors))
        for idx, generated_tensor in enumerate(tensors):
            expected_num_agents = idx + 1
            self.assertEqual((expected_num_agents, AgentInternalIndex.dim()), generated_tensor.shape)
            for row in range(generated_tensor.shape[0]):
                for col in range(generated_tensor.shape[1]):
                    self.assertEqual(row + col, int(generated_tensor[row, col].item()))

    def test_pack_agents_tensor(self) -> None:
        """
        Test the routine used to convert local buffers into the final feature.
        """
        num_agents = 4
        num_timestamps = 3
        agents_tensors = [_create_tracked_object_agent_tensor(num_agents) for _ in range(num_timestamps)]
        yaw_rates = torch.ones((num_timestamps, num_agents)) * 100
        packed = pack_agents_tensor(agents_tensors, yaw_rates)
        self.assertEqual((num_timestamps, num_agents, AgentFeatureIndex.dim()), packed.shape)
        for ts in range(num_timestamps):
            for agent in range(num_agents):
                for col in range(AgentFeatureIndex.dim()):
                    if col == AgentFeatureIndex.yaw_rate():
                        self.assertEqual(100, packed[ts, agent, col])
                    else:
                        self.assertEqual(agent, packed[ts, agent, col])

def test_extract_and_pad_agent_poses(self) -> None:
    """
        Test when there is agent pose trajectory is incomplete
        """
    padded_poses, availability = extract_and_pad_agent_poses(self.agent_trajectories)
    availability = np.asarray(availability)
    stacked_poses = np.stack([[agent.serialize() for agent in frame] for frame in padded_poses])
    self.assertEqual(stacked_poses.shape[0], self.num_frames)
    self.assertEqual(stacked_poses.shape[1], self.num_agents)
    self.assertEqual(stacked_poses.shape[2], 3)
    self.assertEqual(len(availability.shape), 2)
    self.assertEqual(availability.shape[0], self.num_frames)
    self.assertEqual(availability.shape[1], self.num_agents)
    self.assertTrue(availability[:5, :].all())
    self.assertTrue(availability[:, :self.num_agents - self.num_missing_agents].all())
    self.assertTrue((~availability[5:, -self.num_missing_agents:]).all())
    padded_poses_reversed, availability_reversed = extract_and_pad_agent_poses(self.agent_trajectories[::-1], reverse=True)
    availability_reversed = np.asarray(availability_reversed)
    stacked_poses = np.stack([[agent.serialize() for agent in frame] for frame in padded_poses_reversed])
    self.assertEqual(stacked_poses.shape[0], self.num_frames)
    self.assertEqual(stacked_poses.shape[1], self.num_agents)
    self.assertEqual(stacked_poses.shape[2], 3)
    self.assertEqual(len(availability_reversed.shape), 2)
    self.assertEqual(availability_reversed.shape[0], self.num_frames)
    self.assertEqual(availability_reversed.shape[1], self.num_agents)
    self.assertTrue(availability_reversed[-5:, :].all())
    self.assertTrue(availability_reversed[:, :self.num_agents - self.num_missing_agents].all())
    self.assertTrue((~availability_reversed[:3, -self.num_missing_agents:]).all())

@dataclass
class SimulationFigure:
    """Simulation figure data."""
    planner_name: str
    scenario: AbstractScenario
    simulation_history: SimulationHistory
    vehicle_parameters: VehicleParameters
    figure: Figure
    file_path_index: int
    slider: Slider
    video_button: Button
    first_button: Button
    prev_button: Button
    play_button: Button
    next_button: Button
    last_button: Button
    figure_title_name: str
    x_y_coordinate_title: Title
    time_us: Optional[List[int]] = None
    mission_goal_plot: Optional[GlyphRenderer] = None
    expert_trajectory_plot: Optional[GlyphRenderer] = None
    legend_state: bool = False
    map_polygon_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    map_line_plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    traffic_light_plot: Optional[TrafficLightPlot] = None
    ego_state_plot: Optional[EgoStatePlot] = None
    ego_state_trajectory_plot: Optional[EgoStateTrajectoryPlot] = None
    agent_state_plot: Optional[AgentStatePlot] = None
    agent_state_heading_plot: Optional[AgentStateHeadingPlot] = None
    lane_connectors: Optional[Dict[str, LaneConnector]] = None
    glyph_names_from_checkbox_group: Optional[Dict[str, str]] = None

    def __post_init__(self) -> None:
        """Initialize all plots and data sources."""
        if self.lane_connectors is None:
            self.lane_connectors = {}
        if self.time_us is None:
            self.time_us = []
        if self.traffic_light_plot is None:
            self.traffic_light_plot = TrafficLightPlot()
        if self.ego_state_plot is None:
            self.ego_state_plot = EgoStatePlot(vehicle_parameters=self.vehicle_parameters)
        if self.ego_state_trajectory_plot is None:
            self.ego_state_trajectory_plot = EgoStateTrajectoryPlot()
        if self.agent_state_plot is None:
            self.agent_state_plot = AgentStatePlot()
        if self.agent_state_heading_plot is None:
            self.agent_state_heading_plot = AgentStateHeadingPlot()

    def is_rendering(self) -> bool:
        """:return: true if at least one plot is currently rendering a frame request."""
        plots = [self.traffic_light_plot, self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]
        return any((plot.render_event.is_set() if plot.render_event else False for plot in plots if plot))

    def figure_title_name_with_timestamp(self, frame_index: int) -> str:
        """
        Return figure title with a timestamp.
        :param frame_index: Frame index.
        """
        if self.time_us:
            return f'{self.figure_title_name} (Frame: {frame_index}, Time_us: {self.time_us[frame_index]})'
        else:
            return self.figure_title_name

    def copy_datasources(self, other: SimulationFigure) -> None:
        """
        Copy data sources from another simulation figure.
        :param other: Another SimulationFigure object.
        """
        self.time_us = other.time_us
        self.scenario = other.scenario
        self.simulation_history = other.simulation_history
        self.lane_connectors = other.lane_connectors
        self.traffic_light_plot.data_sources = other.traffic_light_plot.data_sources
        self.ego_state_plot.data_sources = other.ego_state_plot.data_sources
        self.ego_state_trajectory_plot.data_sources = other.ego_state_trajectory_plot.data_sources
        self.agent_state_plot.data_sources = other.agent_state_plot.data_sources
        self.agent_state_heading_plot.data_sources = other.agent_state_heading_plot.data_sources

    def update_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        self.slider.end = len(self.simulation_history.data) - 1
        self.time_us = [sample.ego_state.time_us for sample in self.simulation_history.data]
        for plot in [self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]:
            if plot:
                t = threading.Thread(target=plot.update_data_sources, args=(self.simulation_history,), daemon=True)
                t.start()

    def update_map_dependent_data_sources(self) -> None:
        """
        Update data sources in a multi-threading manner to speed up loading and initialization in
        scenario rendering.
        """
        if len(self.simulation_history.data) == 0:
            raise ValueError('SimulationHistory cannot be empty!')
        if self.lane_connectors is not None and len(self.lane_connectors):
            if not self.traffic_light_plot:
                return
            thread = threading.Thread(target=self.traffic_light_plot.update_data_sources, args=(self.scenario, self.simulation_history, self.lane_connectors), daemon=True)
            thread.start()

    def render_mission_goal(self, mission_goal_state: StateSE2) -> None:
        """
        Render the mission goal.
        :param mission_goal_state: Mission goal state.
        """
        source = ColumnDataSource(dict(xs=[mission_goal_state.x], ys=[mission_goal_state.y], heading=[mission_goal_state.heading]))
        self.mission_goal_plot = self.figure.rect(x='xs', y='ys', height=self.vehicle_parameters.height, width=self.vehicle_parameters.length, angle='heading', fill_alpha=simulation_tile_style['mission_goal_alpha'], color=simulation_tile_style['mission_goal_color'], line_width=simulation_tile_style['mission_goal_line_width'], source=source)

    def render_expert_trajectory(self, expert_ego_trajectory_state: ColumnDataSource) -> None:
        """
        Render expert trajectory.
        :param expert_ego_trajectory_state: A list of trajectory states.
        """
        self.expert_trajectory_plot = self.figure.line(x='xs', y='ys', line_color=simulation_tile_trajectory_style['expert_ego']['line_color'], line_alpha=simulation_tile_trajectory_style['expert_ego']['line_alpha'], line_width=simulation_tile_trajectory_style['expert_ego']['line_width'], source=expert_ego_trajectory_state)

    @staticmethod
    def _update_glyph_visibility(glyphs: List[Optional[GlyphRenderer]]) -> None:
        """
        Update visibility in a list of glyphs.
        :param glyphs: A list of glyphs.
        """
        for glyph in glyphs:
            if glyph is not None:
                glyph.visible = not glyph.visible

    def get_glyph_name_from_checkbox_group(self, glyph_checkbox_group_name: str) -> str:
        """
        Get the correct glyph name of each glyph type based on the name from checkbox group.
        :param glyph_checkbox_group_name: glyph name from a checkbox group.
        :return Correct glyph name based on the glyph name from checkbox groups.
        """
        if not self.glyph_names_from_checkbox_group:
            self.glyph_names_from_checkbox_group = {'Vehicle': 'vehicles', 'Pedestrian': 'pedestrians', 'Bicycle': 'bicycles', 'Generic': 'genericobjects', 'Traffic Cone': 'traffic_cone', 'Barrier': 'barrier', 'Czone Sign': 'czone_sign', 'Lane': SemanticMapLayer.LANE.name, 'Intersection': SemanticMapLayer.INTERSECTION.name, 'Stop Line': SemanticMapLayer.STOP_LINE.name, 'Crosswalk': SemanticMapLayer.CROSSWALK.name, 'Walkway': SemanticMapLayer.WALKWAYS.name, 'Carpark': SemanticMapLayer.CARPARK_AREA.name, 'RoadBlock': SemanticMapLayer.ROADBLOCK.name, 'Lane Connector': SemanticMapLayer.LANE_CONNECTOR.name, 'Lane Line': SemanticMapLayer.LANE.name}
        name = self.glyph_names_from_checkbox_group.get(glyph_checkbox_group_name, None)
        if not name:
            raise ValueError(f'{glyph_checkbox_group_name} is not a valid glyph name!')
        return name

    def _get_trajectory_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Get a trajectory glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        if glyph_name == 'Expert Trajectory':
            return [self.expert_trajectory_plot if self.expert_trajectory_plot is not None else None]
        elif glyph_name == 'Ego Trajectory':
            return [self.ego_state_trajectory_plot.plot if self.ego_state_trajectory_plot is not None else None]
        elif glyph_name == 'Goal':
            return [self.mission_goal_plot]
        elif glyph_name == 'Traffic Light':
            return [self.traffic_light_plot.plot if self.traffic_light_plot is not None else None]
        else:
            raise ValueError(f'{glyph_name} is not a valid trajectory name.')

    def _get_agent_glyph_to_update(self, glyph_name: str) -> List[Optional[GlyphRenderer]]:
        """
        Update an agent glyph to update its visibility.
        :param glyph_name: Glyph name.
        :return A list of glyphs to be updated.
        """
        object_type_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
        return [self.agent_state_plot.plots.get(object_type_name, None) if self.agent_state_plot is not None else None, self.agent_state_heading_plot.plots.get(object_type_name, None) if self.agent_state_heading_plot is not None else None]

    def update_glyphs_visibility(self, glyph_names: Optional[List[str]]=None) -> None:
        """
        Update glyphs' visibility based on a list of glyph names.
        :param glyph_names: List of glyph names to update their visibility.
        """
        if not glyph_names:
            return
        glyphs = []
        for glyph_name in glyph_names:
            if glyph_name == 'Ego':
                glyphs += [self.ego_state_plot.plot if self.ego_state_plot is not None else None]
            elif glyph_name in ['Expert Trajectory', 'Ego Trajectory', 'Goal', 'Traffic Light']:
                glyphs += self._get_trajectory_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Vehicle', 'Pedestrian', 'Bicycle', 'Generic', 'Traffic Cone', 'Barrier', 'Czone Sign']:
                glyphs += self._get_agent_glyph_to_update(glyph_name=glyph_name)
            elif glyph_name in ['Lane', 'Intersection', 'Stop Line', 'Crosswalk', 'Walkway', 'Carpark', 'RoadBlock']:
                map_polygon_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_polygon_plots.get(map_polygon_name, None)]
            elif glyph_name in ['Lane Connector', 'Lane Line']:
                map_line_name = self.get_glyph_name_from_checkbox_group(glyph_checkbox_group_name=glyph_name)
                glyphs += [self.map_line_plots.get(map_line_name, None)]
        self._update_glyph_visibility(glyphs=glyphs)

    def update_legend(self) -> None:
        """Update legend."""
        if self.legend_state:
            return
        if not self.agent_state_heading_plot or not self.agent_state_plot:
            return
        agent_legends = [(category.capitalize(), [plot, self.agent_state_heading_plot.plots[category]]) for category, plot in self.agent_state_plot.plots.items()]
        selected_map_polygon_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.INTERSECTION.name, SemanticMapLayer.STOP_LINE.name, SemanticMapLayer.CROSSWALK.name, SemanticMapLayer.WALKWAYS.name, SemanticMapLayer.CARPARK_AREA.name]
        map_polygon_legend_items = []
        for map_polygon_layer in selected_map_polygon_layers:
            map_polygon_legend_items.append((map_polygon_layer.capitalize(), [self.map_polygon_plots[map_polygon_layer]]))
        selected_map_line_layers = [SemanticMapLayer.LANE.name, SemanticMapLayer.LANE_CONNECTOR.name]
        map_line_legend_items = []
        for map_line_layer in selected_map_line_layers:
            map_line_legend_items.append((map_line_layer.capitalize(), [self.map_line_plots[map_line_layer]]))
        if not self.ego_state_plot or not self.ego_state_trajectory_plot:
            return
        legend_items = [('Ego', [self.ego_state_plot.plot]), ('Ego traj', [self.ego_state_trajectory_plot.plot])]
        if self.mission_goal_plot is not None:
            legend_items.append(('Goal', [self.mission_goal_plot]))
        if self.expert_trajectory_plot is not None:
            legend_items.append(('Expert traj', [self.expert_trajectory_plot]))
        legend_items += agent_legends
        legend_items += map_polygon_legend_items
        legend_items += map_line_legend_items
        if self.traffic_light_plot and self.traffic_light_plot.plot is not None:
            legend_items.append(('Traffic light', [self.traffic_light_plot.plot]))
        legend = Legend(items=legend_items)
        legend.click_policy = 'hide'
        self.figure.add_layout(legend)
        self.legend_state = True
        self.figure.legend.label_text_font_size = '0.8em'

def is_rendering(self) -> bool:
    """:return: true if at least one plot is currently rendering a frame request."""
    plots = [self.traffic_light_plot, self.ego_state_plot, self.ego_state_trajectory_plot, self.agent_state_plot, self.agent_state_heading_plot]
    return any((plot.render_event.is_set() if plot.render_event else False for plot in plots if plot))

class TestSimulationTile(unittest.TestCase):
    """Test simulation_tile functionality."""

    def set_up_simulation_log(self, output_path: Path) -> None:
        """
        Create a simulation log and save it to disk.
        :param output path: to write the simulation log to.
        """
        simulation_log = create_sample_simulation_log(output_path)
        simulation_log.save_to_file()

    def setUp(self) -> None:
        """Set up simulation tile with nuboard file."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vehicle_parameters = get_pacifica_parameters()
        simulation_log_path = Path(self.tmp_dir.name) / 'test_simulation_tile_simulation_log.msgpack.xz'
        self.set_up_simulation_log(simulation_log_path)
        nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulation', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        self.scenario_keys = [SimulationScenarioKey(nuboard_file_index=0, log_name='dummy_log', planner_name='SimplePlanner', scenario_type='common', scenario_name='test', files=[simulation_log_path])]
        self.doc = Document()
        self.map_factory = MockMapFactory()
        self.experiment_file_data = ExperimentFileData(file_paths=[nuboard_file])
        self.simulation_tile = SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)

    @given(frame_rate_cap=st.integers(min_value=1, max_value=60))
    def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests valid frame rate cap range."""
        SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    @given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
    def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests invalid frame rate cap range."""
        with self.assertRaises(ValueError):
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    def test_simulation_tile_layout(self) -> None:
        """Test layout design."""
        layout = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        self.assertEqual(len(layout), 1)

    def test_periodic_callback(self) -> None:
        """Tests that _periodic_callback is registered correctly to the bokeh Document."""
        with patch.object(SimulationTile, '_periodic_callback', autospec=True) as mock_periodic_callback:
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)
            for cb in self.doc.callbacks.session_callbacks:
                cb.callback()
            self.assertEqual(mock_periodic_callback.call_count, 1)

    def _trigger_button_click_event(self, figure_index: int, button_name: str) -> None:
        """
        Trigger a bokeh.model.Button click event.
        :param figure_index: The index of the SimulationTile figure.
        :param button_name: The name of SimulationTile button.
        """
        button = getattr(self.simulation_tile.figures[figure_index], button_name)
        button._trigger_event(ButtonClick(button))

    def _test_frame_index_request_button(self, button_name: str, frame_index_request: FrameIndexRequest) -> None:
        """
        Helper function to test that frame index request buttons (first, prev, next, last) work correctly.
        :param click_callback_name: Button click callback function name in SimulationTile that's registered to bokeh.
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_index_request: FrameIndexRequest object representing the frame index requested.
        """
        with patch.object(self.simulation_tile, '_render_plots'):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            if frame_index_request == FrameIndexRequest.FIRST or frame_index_request == FrameIndexRequest.LAST:
                self._trigger_button_click_event(figure_index, button_name)
                frame_index = len(figure.simulation_history) - 1 if frame_index_request == FrameIndexRequest.LAST else 0
                self.assertEqual(figure.slider.value, frame_index)
            elif frame_index_request == FrameIndexRequest.NEXT:
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index + 1)
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)
            elif frame_index_request == FrameIndexRequest.PREV:
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index - 1)
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)

    def test_first_frame_button(self) -> None:
        """Tests that go to first frame button works correctly."""
        self._test_frame_index_request_button(button_name='first_button', frame_index_request=FrameIndexRequest.FIRST)

    def test_last_frame_button(self) -> None:
        """Tests that go to last frame button works correctly."""
        self._test_frame_index_request_button(button_name='last_button', frame_index_request=FrameIndexRequest.LAST)

    def _test_symbolic_frame_request_callback_called(self, button_name: str, frame_request_callback_name: str) -> None:
        """
        Helper function to test that the provided symbolic frame request (previous, next, play/stop) callback is called when a button is clicked
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_request_callback_name: Frame request callback function name in SimulationTile that's supposed to be called.
        """
        with patch.object(self.simulation_tile, frame_request_callback_name, autospec=True) as mock_request_frame:
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            button = getattr(self.simulation_tile.figures[figure_index], button_name)
            button._trigger_event(ButtonClick(button))
            mock_request_frame.assert_called_once_with(self.simulation_tile.figures[figure_index])

    def test_prev_button(self) -> None:
        """Tests that show prev frame button works correctly."""
        self._test_frame_index_request_button(button_name='prev_button', frame_index_request=FrameIndexRequest.PREV)

    def test_next_button(self) -> None:
        """Tests that show next frame button works correctly."""
        self._test_frame_index_request_button(button_name='next_button', frame_index_request=FrameIndexRequest.NEXT)

    def test_play_button(self) -> None:
        """Tests that the play button works correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        button_name = 'play_button'
        self.assertFalse(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertTrue(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_playback_callback(self) -> None:
        """Tests that the playback callback is registered correctly to the bokeh Document & behaves correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        figure = self.simulation_tile.figures[figure_index]
        button_name = 'play_button'
        previous_request_index = figure.slider.value
        self._trigger_button_click_event(figure_index, button_name)
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertTrue(self.simulation_tile.is_in_playback)
        self.assertTrue(figure.slider.value, previous_request_index + 1)
        self.simulation_tile._current_frame_index = len(figure.simulation_history) - 1
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_deferred_plot_rendering(self) -> None:
        """Tests that plot rendering request will be deferred if successive requests are triggered faster than the frame rate cap configured."""
        self.assertIsNone(self.simulation_tile._plot_render_queue)
        with patch.object(self.simulation_tile, '_last_frame_time', new=time.time()):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            trigger_count = 2
            for _ in range(trigger_count):
                figure.slider.trigger(attr='value', old=0, new=1)
            self.assertIsNotNone(self.simulation_tile._plot_render_queue)

    def tearDown(self) -> None:
        """Clean up temporary folder and files."""
        self.tmp_dir.cleanup()

def test_simulation_tile_layout(self) -> None:
    """Test layout design."""
    layout = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
    self.assertEqual(len(layout), 1)

def _trigger_button_click_event(self, figure_index: int, button_name: str) -> None:
    """
        Trigger a bokeh.model.Button click event.
        :param figure_index: The index of the SimulationTile figure.
        :param button_name: The name of SimulationTile button.
        """
    button = getattr(self.simulation_tile.figures[figure_index], button_name)
    button._trigger_event(ButtonClick(button))

def _test_frame_index_request_button(self, button_name: str, frame_index_request: FrameIndexRequest) -> None:
    """
        Helper function to test that frame index request buttons (first, prev, next, last) work correctly.
        :param click_callback_name: Button click callback function name in SimulationTile that's registered to bokeh.
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_index_request: FrameIndexRequest object representing the frame index requested.
        """
    with patch.object(self.simulation_tile, '_render_plots'):
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        figure = self.simulation_tile.figures[figure_index]
        if frame_index_request == FrameIndexRequest.FIRST or frame_index_request == FrameIndexRequest.LAST:
            self._trigger_button_click_event(figure_index, button_name)
            frame_index = len(figure.simulation_history) - 1 if frame_index_request == FrameIndexRequest.LAST else 0
            self.assertEqual(figure.slider.value, frame_index)
        elif frame_index_request == FrameIndexRequest.NEXT:
            self.simulation_tile._current_frame_index = 0
            self._trigger_button_click_event(figure_index, button_name)
            self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index + 1)
            self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
            self._trigger_button_click_event(figure_index, button_name)
            self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)
        elif frame_index_request == FrameIndexRequest.PREV:
            self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
            self._trigger_button_click_event(figure_index, button_name)
            self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index - 1)
            self.simulation_tile._current_frame_index = 0
            self._trigger_button_click_event(figure_index, button_name)
            self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)

def _test_symbolic_frame_request_callback_called(self, button_name: str, frame_request_callback_name: str) -> None:
    """
        Helper function to test that the provided symbolic frame request (previous, next, play/stop) callback is called when a button is clicked
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_request_callback_name: Frame request callback function name in SimulationTile that's supposed to be called.
        """
    with patch.object(self.simulation_tile, frame_request_callback_name, autospec=True) as mock_request_frame:
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        button = getattr(self.simulation_tile.figures[figure_index], button_name)
        button._trigger_event(ButtonClick(button))
        mock_request_frame.assert_called_once_with(self.simulation_tile.figures[figure_index])

def test_play_button(self) -> None:
    """Tests that the play button works correctly."""
    self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
    figure_index = 0
    button_name = 'play_button'
    self.assertFalse(self.simulation_tile.is_in_playback)
    self._trigger_button_click_event(figure_index, button_name)
    self.assertTrue(self.simulation_tile.is_in_playback)
    self._trigger_button_click_event(figure_index, button_name)
    self.assertFalse(self.simulation_tile.is_in_playback)

def test_playback_callback(self) -> None:
    """Tests that the playback callback is registered correctly to the bokeh Document & behaves correctly."""
    self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
    figure_index = 0
    figure = self.simulation_tile.figures[figure_index]
    button_name = 'play_button'
    previous_request_index = figure.slider.value
    self._trigger_button_click_event(figure_index, button_name)
    for cb in self.doc.callbacks.session_callbacks:
        cb.callback()
    self.assertTrue(self.simulation_tile.is_in_playback)
    self.assertTrue(figure.slider.value, previous_request_index + 1)
    self.simulation_tile._current_frame_index = len(figure.simulation_history) - 1
    for cb in self.doc.callbacks.session_callbacks:
        cb.callback()
    self.assertFalse(self.simulation_tile.is_in_playback)

class TestS3Tab(unittest.TestCase):
    """Test nuboard s3 tab functionality."""

    def setUp(self) -> None:
        """Set up a configuration tab."""
        self.doc = Document()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        metric_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        simulation_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
        self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)
        self.configuration_tab = ConfigurationTab(experiment_file_data=self.experiment_file_data, doc=self.doc, tabs=[self.histogram_tab])
        if not os.getenv('NUPLAN_EXP_ROOT', None):
            os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
        self.s3_tab = CloudTab(doc=self.doc, configuration_tab=self.configuration_tab)
        self.dummy_file_result_message = S3FileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Connect successfully'), file_contents={'dummy_a': S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)), 'dummy_b': S3FileContent(filename='dummy_b', size=10, last_modified=datetime(day=3, month=8, year=1992, tzinfo=timezone.utc))})

    def test_modal_query_btn(self) -> None:
        """Test if modal query btn works."""
        self.s3_tab._s3_modal_query_on_click()
        self.assertNotEqual(self.s3_tab._s3_client, None)

    def test_load_s3_contents_with_file_contents(self) -> None:
        """Test _load_s3_contents works if there are file contents."""
        self.s3_tab._load_s3_contents(s3_file_result_message=self.dummy_file_result_message)
        self.s3_tab.s3_error_text.text = self.dummy_file_result_message.s3_connection_status.return_message
        self.assertEqual(self.s3_tab.s3_error_text.text, self.dummy_file_result_message.s3_connection_status.return_message)

    def test_s3_data_source_on_selected(self) -> None:
        """Test _s3_data_source_on_selected work."""
        data_sources: Dict[str, List[Any]] = {'object': [], 'last_modified': [], 'timestamp': [], 'size': []}
        for file_name, content in self.dummy_file_result_message.file_contents.items():
            data_sources['object'].append(file_name)
            data_sources['last_modified'].append(content.last_modified_day if content.last_modified is not None else '')
            data_sources['timestamp'].append(content.date_string if content.date_string is not None else '')
            data_sources['size'].append(content.kb_size() if content.kb_size() is not None else '')
        self.s3_tab.data_table.source.data = data_sources
        self.s3_tab._selected_column.value = str(1)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[0], old=[])
        self.assertEqual(self.s3_tab.s3_download_text_input.value, 'dummy_a')
        self.s3_tab._selected_column.value = str(2)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[1], old=[])
        self.assertEqual(self.s3_tab.s3_download_text_input.value, 'dummy_b')
        self.s3_tab._selected_column.value = str(0)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[0], old=[])
        self.assertNotEqual(self.s3_tab._s3_client, None)

    def test_s3_download_button_on_click(self) -> None:
        """Test if s3 download button on_click function works."""
        self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
        self.s3_tab.s3_download_text_input.value = 'test-prefix'
        self.s3_tab._s3_download_button_on_click()
        self.assertEqual(self.s3_tab.s3_download_button.label, 'Downloading...')
        self.assertTrue(self.s3_tab.s3_download_button.disabled)

    def test_s3_download_prefixes_fail_without_s3_client(self) -> None:
        """Test s3 tab download_prefixes function fails when there is no s3 client."""
        self.s3_tab._s3_download_prefixes()
        self.assertEqual(self.s3_tab.s3_error_text.text, 'No s3 connection!')

    def test_s3_download_prefixes_fail_without_nuboard_files(self) -> None:
        """Test s3 tab download_prefixes function fails when there is no nuboard files."""
        self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
        self.s3_tab.s3_download_text_input.value = 'test-prefix'
        s3_client = boto3.Session().client('s3')
        self.s3_tab._s3_client = s3_client
        stubber = Stubber(s3_client)
        expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
        expected_params = {'Bucket': 'test-bucket', 'Prefix': 'test-prefix/', 'Delimiter': '/'}
        stubber.add_response('list_objects_v2', expected_response, expected_params)
        with stubber:
            self.s3_tab._s3_download_prefixes()
            self.assertEqual(self.s3_tab.s3_error_text.text, 'No available nuboard files in the prefix')

    def test_s3_update_nuboard_file_main_path(self) -> None:
        """Test s3 tab _update_s3_nuboard_file_main_path function updates main path based on the selected prefix."""
        s3_nuboard_file_result_message = S3NuBoardFileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Get s3 nuboasrd file'), nuboard_file=self.nuboard_file, nuboard_filename=self.nuboard_file_name.name)
        prefix = self.tmp_dir.name
        self.s3_tab._update_s3_nuboard_file_main_path(s3_nuboard_file_result=s3_nuboard_file_result_message, selected_prefix=prefix)
        nuboard_file = s3_nuboard_file_result_message.nuboard_file
        self.assertEqual(nuboard_file.simulation_main_path, self.tmp_dir.name)
        self.assertEqual(nuboard_file.metric_main_path, self.tmp_dir.name)

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

def test_modal_query_btn(self) -> None:
    """Test if modal query btn works."""
    self.s3_tab._s3_modal_query_on_click()
    self.assertNotEqual(self.s3_tab._s3_client, None)

def test_s3_download_button_on_click(self) -> None:
    """Test if s3 download button on_click function works."""
    self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
    self.s3_tab.s3_download_text_input.value = 'test-prefix'
    self.s3_tab._s3_download_button_on_click()
    self.assertEqual(self.s3_tab.s3_download_button.label, 'Downloading...')
    self.assertTrue(self.s3_tab.s3_download_button.disabled)

def extract_common_or_connecting_route_objs(corners_route_obj: CornersGraphEdgeMapObject) -> Optional[Set[GraphEdgeMapObject]]:
    """
    Extracts common or connecting (outgoing or incoming) lane/lane connectors of corners
    :param corners_route_obj: Class containing list of lane/lane connectors of each corner
    :return common or connecting lane/lane connectors of corners if exists, else None.
    If all corners are in nondrivable area, returns an empty set.
    """
    corners_route_obj_list = [*corners_route_obj.__iter__()]
    not_in_lane_or_laneconn = [True if len(corner_route_obj) == 0 else False for corner_route_obj in corners_route_obj_list]
    if np.all(not_in_lane_or_laneconn):
        return set()
    if np.any(not_in_lane_or_laneconn):
        return None
    obj_id_dict = {obj.id: obj for corner_route_obj in corners_route_obj_list for obj in corner_route_obj}
    corners_route_obj_ids = [{obj.id for obj in corner_route_obj} for corner_route_obj in corners_route_obj_list]
    all_corners_common_obj = get_common_route_object(corners_route_obj_ids, obj_id_dict)
    if len(all_corners_common_obj) > 0:
        return all_corners_common_obj
    all_corners_connecting_obj = get_connecting_route_object(corners_route_obj_list, corners_route_obj_ids, obj_id_dict)
    if len(all_corners_connecting_obj) > 0:
        return all_corners_connecting_obj
    return None

def get_rectangle_corners(center: StateSE2, half_width: float, half_length: float) -> Polygon:
    """
    Get all four corners of actor's footprint
    :param center: StateSE2 object for the center of the actor
    :param half_width: rectangle width divided by 2
    :param half_length: rectangle length divided by 2.
    """
    corners = Polygon([get_front_left_corner(center, half_length, half_width), get_rear_left_corner(center, half_length, half_width), get_rear_right_corner(center, half_length, half_width), get_front_right_corner(center, half_length, half_width)])
    return corners

def approximate_derivatives(y: npt.NDArray[np.float32], x: npt.NDArray[np.float32], window_length: int=5, poly_order: int=2, deriv_order: int=1, axis: int=-1) -> npt.NDArray[np.float32]:
    """
    Given two equal-length sequences y and x, compute an approximation to the n-th
    derivative of some function interpolating the (x, y) data points, and return its
    values at the x's.  We assume the x's are increasing and equally-spaced.
    :param y: The dependent variable (say of length n)
    :param x: The independent variable (must have the same length n).  Must be strictly
        increasing and equally-spaced.
    :param window_length: The order (default 5) of the Savitsky-Golay filter used.
        (Ignored if the x's are not equally-spaced.)  Must be odd and at least 3
    :param poly_order: The degree (default 2) of the filter polynomial used.  Must
        be less than the window_length
    :param deriv_order: The order of derivative to compute (default 1)
    :param axis: The axis of the array x along which the filter is to be applied. Default is -1.
    :return Derivatives.
    """
    window_length = min(window_length, len(x))
    if not poly_order < window_length:
        raise ValueError(f'{poly_order} < {window_length} does not hold!')
    dx = np.diff(x)
    if not (dx > 0).all():
        raise RuntimeError('dx is not monotonically increasing!')
    dx = dx.mean()
    derivative: npt.NDArray[np.float32] = savgol_filter(y, polyorder=poly_order, window_length=window_length, deriv=deriv_order, delta=dx, axis=axis)
    return derivative

def phase_unwrap(headings: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """
    Returns an array of heading angles equal mod 2 pi to the input heading angles,
    and such that the difference between successive output angles is less than or
    equal to pi radians in absolute value
    :param headings: An array of headings (radians)
    :return The phase-unwrapped equivalent headings.
    """
    two_pi = 2.0 * np.pi
    adjustments = np.zeros_like(headings)
    adjustments[1:] = np.cumsum(np.round(np.diff(headings) / two_pi))
    unwrapped = headings - two_pi * adjustments
    return unwrapped

class TestWithinBoundMetricBase(TestCase):
    """
    Test WithinBoundMetricBase
    """

    def setUp(self) -> None:
        """
        Set up the test
        """
        values: npt.NDArray[np.float32] = np.array(np.random.normal(size=(10,)))
        self.max_val = np.max(values) + 0.0001
        self.min_val = np.min(values) - 0.0001
        self.time_series = MagicMock()
        self.time_series.values = values.tolist()
        self.metrics = WithinBoundMetricBase(name='test', category='test')

    def test_compute_within_bound(self) -> None:
        """
        Test within bound metric
        """
        self.assertTrue(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val, max_within_bound_threshold=self.max_val))
        self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val + 0.1, max_within_bound_threshold=self.max_val))
        self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val, max_within_bound_threshold=self.max_val - 0.1))
        self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val + 0.1, max_within_bound_threshold=self.max_val - 0.1))

def test_compute_within_bound(self) -> None:
    """
        Test within bound metric
        """
    self.assertTrue(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val, max_within_bound_threshold=self.max_val))
    self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val + 0.1, max_within_bound_threshold=self.max_val))
    self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val, max_within_bound_threshold=self.max_val - 0.1))
    self.assertFalse(self.metrics._compute_within_bound(self.time_series, min_within_bound_threshold=self.min_val + 0.1, max_within_bound_threshold=self.max_val - 0.1))

class EgoLatAccelerationStatistics(WithinBoundMetricBase):
    """Ego lateral acceleration metric."""

    def __init__(self, name: str, category: str, max_abs_lat_accel: float) -> None:
        """
        Initializes the EgoLatAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lat_accel: Maximum threshold to define if absolute lateral acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_lat_accel = max_abs_lat_accel

    @staticmethod
    def compute_comfortability(history: SimulationHistory, max_abs_lat_accel: float) -> bool:
        """
        Compute comfortability based on max_abs_lat_accel
        :param history: History from a simulation engine
        :param max_abs_lat_accel: Threshold for the absolute lat jerk
        :return True if within the threshold otherwise false.
        """
        ego_pose_states = history.extract_ego_state
        ego_pose_lat_accels = extract_ego_acceleration(ego_pose_states, acceleration_coordinate='y')
        lat_accels_within_bounds = np.abs(ego_pose_lat_accels) < max_abs_lat_accel
        return bool(np.all(lat_accels_within_bounds))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lateral acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'y'}, min_within_bound_threshold=-self._max_abs_lat_accel, max_within_bound_threshold=self._max_abs_lat_accel)
        return metric_statistics

@staticmethod
def compute_comfortability(history: SimulationHistory, max_abs_lat_accel: float) -> bool:
    """
        Compute comfortability based on max_abs_lat_accel
        :param history: History from a simulation engine
        :param max_abs_lat_accel: Threshold for the absolute lat jerk
        :return True if within the threshold otherwise false.
        """
    ego_pose_states = history.extract_ego_state
    ego_pose_lat_accels = extract_ego_acceleration(ego_pose_states, acceleration_coordinate='y')
    lat_accels_within_bounds = np.abs(ego_pose_lat_accels) < max_abs_lat_accel
    return bool(np.all(lat_accels_within_bounds))

def get_local_scenario_cache(cache_path: str, feature_names: Set[str]) -> List[Path]:
    """
    Get a list of cached scenario paths from a local cache.
    :param cache_path: Root path of the local cache dir.
    :param feature_names: Set of required feature names to check when loading scenario paths from the cache.
    :return: List of discovered cached scenario paths.
    """
    cache_dir = Path(cache_path)
    assert cache_dir.exists(), f'Local cache {cache_dir} does not exist!'
    assert any(cache_dir.iterdir()), f'No files found in the local cache {cache_dir}!'
    candidate_scenario_dirs = {x.parent for x in cache_dir.rglob('*.gz')}
    scenario_cache_paths = [path for path in candidate_scenario_dirs if not feature_names - {feature_name.stem for feature_name in path.iterdir()}]
    return scenario_cache_paths

def validate_scenario_type_in_cache_path(paths: List[Path]) -> None:
    """
    Checks if scenario_type is in cache path.
    :param path: Scenario cache path
    :return: Whether scenario type is in cache path
    """
    sample_cache_path = paths[0]
    assert all((not char.isdigit() for char in sample_cache_path.parent.name)), 'Unable to filter cache by scenario types as it was generated without scenario type information. Please regenerate a new cache if scenario type filtering is required.'

class TestUtilsConfig(unittest.TestCase):
    """Tests for the non-distributed training functions in utils_config.py."""
    specific_world_size = 4

    @staticmethod
    def _generate_mock_training_config() -> DictConfig:
        """
        Returns a mock training configuration with sensible default values.
        :return: DictConfig representing the training configuration.
        """
        return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'cache': {'cleanup_cache': False, 'cache_path': None}, 'data_loader': {'params': {'num_workers': None}}, 'lightning': {'trainer': {'params': {'gpus': None, 'accelerator': None, 'precision': None}, 'overfitting': {'enable': False}}}, 'gpu': False})

    @staticmethod
    def _generate_mock_simulation_config() -> DictConfig:
        """
        Returns a mock simulation configuration with sensible default values.
        :return: DictConfig representing the simulation configuration.
        """
        return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}, 'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})

    @staticmethod
    def _patch_return_false() -> bool:
        """A patch function that will always return False."""
        return False

    @staticmethod
    def _patch_return_true() -> bool:
        """A patch function that will always return True."""
        return True

    @given(cache_path=st.one_of(st.none(), st.just('s3://bucket/key')))
    @settings(deadline=None)
    def test_update_config_for_training_cache_path_none_or_s3(self, cache_path: Optional[str]) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path is either
        None or an S3 path.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.cache.cache_path = cache_path
        with TemporaryDirectory() as tmp_dir:
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertTrue(Path(tmp_dir).exists())

    def test_update_config_for_training_cache_path_local_non_existing(self) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path doesn't exist yet.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        with TemporaryDirectory() as tmp_dir:
            mock_config.cache.cache_path = tmp_dir
            rmtree(tmp_dir)
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertTrue(Path(tmp_dir).exists())

    def test_update_config_for_training_cache_path_local_cleanup(self) -> None:
        """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path exists and
        cleanup_cache is requested.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        with TemporaryDirectory() as tmp_dir:
            _, tmp_file = mkstemp(dir=tmp_dir)
            mock_config.cache.cache_path = tmp_dir
            mock_config.cache.cleanup_cache = True
            self.assertTrue(Path(tmp_file).exists())
            with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
                update_config_for_training(mock_config)
            self.assertFalse(Path(tmp_file).exists())
            self.assertTrue(Path(tmp_dir).exists())
        self.assertFalse(Path(tmp_dir).exists())

    def test_update_config_for_training_overfitting(self) -> None:
        """
        Tests the behavior of update_config_for_training in regard to overfitting configurations.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        num_workers = 32
        mock_config.data_loader.params.num_workers = num_workers
        mock_config.lightning.trainer.overfitting.enable = False
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertEqual(num_workers, mock_config.data_loader.params.num_workers)
        mock_config.lightning.trainer.overfitting.enable = True
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertEqual(0, mock_config.data_loader.params.num_workers)

    @given(is_gpu_enabled=st.booleans(), is_cuda_available=st.booleans())
    @settings(deadline=None)
    def test_update_config_for_training_gpu(self, is_gpu_enabled: bool, is_cuda_available: bool) -> None:
        """
        Tests the behavior of update_config_for_training in regard to gpu configurations.
        """
        invalid_value = -99
        cuda_patch = TestUtilsConfig._patch_return_true if is_cuda_available else TestUtilsConfig._patch_return_false

        def get_expected_gpu_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return -1 if gpu_enabled and cuda_available else None

        def get_expected_accelerator_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return invalid_value if gpu_enabled and cuda_available else None

        def get_expected_precision_config(gpu_enabled: bool, cuda_available: bool) -> Optional[int]:
            return invalid_value if gpu_enabled and cuda_available else 32
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.gpu = is_gpu_enabled
        mock_config.lightning.trainer.params.gpus = invalid_value
        mock_config.lightning.trainer.params.accelerator = invalid_value
        mock_config.lightning.trainer.params.precision = invalid_value
        with patch_with_validation('torch.cuda.is_available', cuda_patch):
            update_config_for_training(mock_config)
        self.assertEqual(get_expected_gpu_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.gpus)
        self.assertEqual(get_expected_accelerator_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.accelerator)
        self.assertEqual(get_expected_precision_config(is_gpu_enabled, is_cuda_available), mock_config.lightning.trainer.params.precision)

    @given(max_number_of_workers=st.one_of(st.none(), st.just(0)))
    @settings(deadline=None)
    def test_update_config_for_simulation_falsy_max_number_of_workers(self, max_number_of_workers: int) -> None:
        """
        Tests that update_config_for_simulation works as expected.
        When max number of workers is falsy, timing_callback won't be removed
        """
        mock_config = TestUtilsConfig._generate_mock_simulation_config()
        mock_config.max_number_of_workers = max_number_of_workers
        update_config_for_simulation(mock_config)
        self.assertEqual(3, len(mock_config.callback))

    @given(max_number_of_workers=st.integers(min_value=1))
    @settings(deadline=None)
    def test_update_config_for_simulation_truthy_max_number_of_workers(self, max_number_of_workers: int) -> None:
        """
        Tests that update_config_for_simulation works as expected. When max number of workers is truthy, a new
        `callbacks` entry will be added. The values are taken from `callback` with timing_callback target removed.
        """
        mock_config = TestUtilsConfig._generate_mock_simulation_config()
        mock_config.max_number_of_workers = max_number_of_workers
        update_config_for_simulation(mock_config)
        self.assertEqual(3, len(mock_config.callback))
        self.assertEqual(2, len(mock_config.callbacks))
        callbacks_targets = [callback['_target_'] for callback in mock_config.callbacks]
        self.assertNotIn('nuplan.planning.simulation.callback.timing_callback.TimingCallback', callbacks_targets)

    def test_update_config_for_nuboard(self) -> None:
        """Tests that update_config_for_nuboard works as expected."""
        mock_config = DictConfig({'log_config': True})
        mock_config.simulation_path = None
        update_config_for_nuboard(mock_config)
        self.assertIsNotNone(mock_config.simulation_path)
        self.assertEqual(0, len(mock_config.simulation_path))
        simulation_path_list = ['/mock/path', '/to/somewhere']
        mock_config.simulation_path = simulation_path_list
        update_config_for_nuboard(mock_config)
        self.assertEqual(simulation_path_list, mock_config.simulation_path)
        simulation_path_list_config = ListConfig(element_type=str, content=['/mock/path', '/to/somewhere'])
        mock_config.simulation_path = simulation_path_list_config
        update_config_for_nuboard(mock_config)
        self.assertEqual(simulation_path_list_config, mock_config.simulation_path)
        simulation_path = '/mock/path'
        mock_config.simulation_path = simulation_path
        update_config_for_nuboard(mock_config)
        expected_simulation_path_list = [simulation_path]
        self.assertEqual(expected_simulation_path_list, mock_config.simulation_path)

    @patch.dict(os.environ, {'WORLD_SIZE': str(specific_world_size)}, clear=True)
    def test_get_num_gpus_used_from_world_size(self) -> None:
        """
        Tests that that get_num_gpus_used works as expected. When WORLD_SIZE is set to a specific value, the function
        will simply return that value.
        """
        mock_config = DictConfig({})
        num_gpus = get_num_gpus_used(mock_config)
        self.assertEqual(self.specific_world_size, num_gpus)

    @given(num_gpus_config=st.integers(min_value=-1), cuda_device_count=st.integers(min_value=0), num_nodes=st.integers(min_value=1))
    @example(num_gpus_config=-1, cuda_device_count=2, num_nodes=2)
    @settings(deadline=None)
    def test_get_num_gpus_used_from_config(self, num_gpus_config: int, cuda_device_count: int, num_nodes: int) -> None:
        """
        Tests that that get_num_gpus_used works as expected when WORLD_SIZE environment variable is not set.
        """

        def patch_get_cuda_device_count() -> int:
            return cuda_device_count
        with patch.dict(os.environ, {'NUM_NODES': str(num_nodes)}, clear=True), patch_with_validation('torch.cuda.device_count', patch_get_cuda_device_count):
            mock_config = TestUtilsConfig._generate_mock_training_config()
            mock_config.lightning.trainer.params.gpus = num_gpus_config
            num_gpus = get_num_gpus_used(mock_config)
            expected_num_gpus = num_gpus_config if num_gpus_config != -1 else cuda_device_count * num_nodes
            self.assertEqual(expected_num_gpus, num_gpus)

    def test_get_num_gpus_used_invalid_config(self) -> None:
        """
        Tests that that get_num_gpus_used raises a RuntimeError when WORLD_SIZE environment variable is not set and
        a string is passed as the value of mock_config.lightning.trainer.params.gpus.
        """
        mock_config = TestUtilsConfig._generate_mock_training_config()
        mock_config.lightning.trainer.params.gpus = '1'
        with self.assertRaises(RuntimeError):
            get_num_gpus_used(mock_config)

@staticmethod
def _generate_mock_training_config() -> DictConfig:
    """
        Returns a mock training configuration with sensible default values.
        :return: DictConfig representing the training configuration.
        """
    return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'cache': {'cleanup_cache': False, 'cache_path': None}, 'data_loader': {'params': {'num_workers': None}}, 'lightning': {'trainer': {'params': {'gpus': None, 'accelerator': None, 'precision': None}, 'overfitting': {'enable': False}}}, 'gpu': False})

@staticmethod
def _generate_mock_simulation_config() -> DictConfig:
    """
        Returns a mock simulation configuration with sensible default values.
        :return: DictConfig representing the simulation configuration.
        """
    return DictConfig({'log_config': True, 'experiment': 'mock_experiment_name', 'group': 'mock_group_name', 'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}, 'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})

def test_update_config_for_training_cache_path_local_cleanup(self) -> None:
    """
        Tests the behavior of update_config_for_training when the supplied cfg.cache.cache_path exists and
        cleanup_cache is requested.
        """
    mock_config = TestUtilsConfig._generate_mock_training_config()
    with TemporaryDirectory() as tmp_dir:
        _, tmp_file = mkstemp(dir=tmp_dir)
        mock_config.cache.cache_path = tmp_dir
        mock_config.cache.cleanup_cache = True
        self.assertTrue(Path(tmp_file).exists())
        with patch_with_validation('torch.cuda.is_available', TestUtilsConfig._patch_return_false):
            update_config_for_training(mock_config)
        self.assertFalse(Path(tmp_file).exists())
        self.assertTrue(Path(tmp_dir).exists())
    self.assertFalse(Path(tmp_dir).exists())

def test_update_config_for_nuboard(self) -> None:
    """Tests that update_config_for_nuboard works as expected."""
    mock_config = DictConfig({'log_config': True})
    mock_config.simulation_path = None
    update_config_for_nuboard(mock_config)
    self.assertIsNotNone(mock_config.simulation_path)
    self.assertEqual(0, len(mock_config.simulation_path))
    simulation_path_list = ['/mock/path', '/to/somewhere']
    mock_config.simulation_path = simulation_path_list
    update_config_for_nuboard(mock_config)
    self.assertEqual(simulation_path_list, mock_config.simulation_path)
    simulation_path_list_config = ListConfig(element_type=str, content=['/mock/path', '/to/somewhere'])
    mock_config.simulation_path = simulation_path_list_config
    update_config_for_nuboard(mock_config)
    self.assertEqual(simulation_path_list_config, mock_config.simulation_path)
    simulation_path = '/mock/path'
    mock_config.simulation_path = simulation_path
    update_config_for_nuboard(mock_config)
    expected_simulation_path_list = [simulation_path]
    self.assertEqual(expected_simulation_path_list, mock_config.simulation_path)

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

class TestUpdateDistributedTrainingCfg(unittest.TestCase):
    """Test update_distributed_optimizer_config function."""
    world_size = 4

    def setUp(self) -> None:
        """Setup test attributes."""
        self.lr = 1e-05
        self.num_train_batches = 12
        self.batch_size = 2
        self.div_factor = 2
        self.max_lr = 0.01
        self.betas = [0.9, 0.999]
        self.max_epochs = 2
        self.exponential_lr_scheduler_cfg = {'_target_': 'torch.optim.lr_scheduler.ExponentialLR', 'gamma': 0.9, 'steps_per_epoch': None}
        self.one_cycle_lr_scheduler_cfg = {'_target_': 'torch.optim.lr_scheduler.OneCycleLR', 'max_lr': self.max_lr, 'steps_per_epoch': None, 'div_factor': self.div_factor}
        self.cfg_mock = DictConfig({'optimizer': {'_target_': 'torch.optim.Adam', 'lr': self.lr, 'betas': self.betas.copy()}, 'lightning': {'trainer': {'overfitting': {'enable': False, 'params': {'overfit_batches': 1}}, 'params': {'max_epochs': self.max_epochs}}, 'distributed_training': {'equal_variance_scaling_strategy': False}}, 'dataloader': {'params': {'batch_size': self.batch_size}}, 'warm_up_scheduler': {'lr_lambda': {'warm_up_steps': 0.0}}})

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_optimizer_config_equal_variance(self) -> None:
        """Test default setting where the lr is scaled to maintain equal variance."""
        cfg_mock = self.cfg_mock.copy()
        cfg_mock.lightning.distributed_training.equal_variance_scaling_strategy = True
        cfg_mock = update_distributed_optimizer_config(cfg_mock)
        msg = f'Expected {self.world_size ** 0.5 * self.lr} but got {cfg_mock.optimizer.lr}'
        msg_beta_1 = f'Expected {self.betas[0]}, {self.world_size ** 0.5}, {self.betas[0] ** self.world_size ** 0.5} but got {cfg_mock.optimizer.betas[0]}'
        msg_beta_2 = f'Expected {self.betas[1] ** self.world_size ** 0.5} but got {cfg_mock.optimizer.betas[1]}'
        self.assertAlmostEqual(float(cfg_mock.optimizer.lr), self.world_size ** 0.5 * self.lr, msg=msg)
        self.assertAlmostEqual(float(cfg_mock.optimizer.betas[0]), self.betas[0] ** self.world_size ** 0.5, msg=msg_beta_1)
        self.assertAlmostEqual(float(cfg_mock.optimizer.betas[1]), self.betas[1] ** self.world_size ** 0.5, msg=msg_beta_2)

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_optimizer_config_linearly(self) -> None:
        """Test default setting where the lr is scaled linearly."""
        cfg_mock = self.cfg_mock.copy()
        cfg_mock = update_distributed_optimizer_config(cfg_mock)
        msg = f'Expected {self.world_size * self.lr} but got {cfg_mock.optimizer.lr}'
        msg_beta_1 = f'Expected {self.betas[0] ** self.world_size} but got {cfg_mock.optimizer.betas[0]}'
        msg_beta_2 = f'Expected {self.betas[1] ** self.world_size} but got {cfg_mock.optimizer.betas[1]}'
        self.assertAlmostEqual(float(cfg_mock.optimizer.lr), self.world_size * self.lr, msg=msg)
        self.assertAlmostEqual(float(cfg_mock.optimizer.betas[0]), self.betas[0] ** self.world_size, msg=msg_beta_1)
        self.assertAlmostEqual(float(cfg_mock.optimizer.betas[1]), self.betas[1] ** self.world_size, msg=msg_beta_2)

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_lr_scheduler_config_not_one_cycle_lr(self) -> None:
        """
        Test default setting where the lr_scheduler is not supported.
        Currently, anything other than OneCycleLR is not supported.
        """
        cfg_mock = self.cfg_mock.copy()
        cfg_mock.lr_scheduler = self.exponential_lr_scheduler_cfg.copy()
        cfg_mock.lightning.trainer.overfitting.enable = True
        cfg_mock.lightning.trainer.overfitting.params.overfit_batches = 1
        cfg_mock = update_distributed_lr_scheduler_config(cfg_mock, num_train_batches=self.num_train_batches)
        msg_steps_per_epoch = f'Expected Mock to not be edited, but steps_per_epoch was edited: steps_per_epoch is {cfg_mock.lr_scheduler.steps_per_epoch}'
        self.assertIsNone(cfg_mock.lr_scheduler.steps_per_epoch, msg=msg_steps_per_epoch)

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_lr_scheduler_config_oclr_overfit_zero_batches(self) -> None:
        """Test default setting where the overfit_batches parameter is set to 0."""
        cfg_mock = self.cfg_mock.copy()
        cfg_mock.lr_scheduler = self.one_cycle_lr_scheduler_cfg.copy()
        cfg_mock.lightning.trainer.overfitting.enable = True
        cfg_mock.lightning.trainer.overfitting.params.overfit_batches = 0
        cfg_mock = update_distributed_lr_scheduler_config(cfg_mock, num_train_batches=self.num_train_batches)
        expected_steps_per_epoch = math.ceil(math.ceil(self.num_train_batches / self.world_size) / self.max_epochs)
        msg_steps_per_epoch = f'Expected steps per epoch to be {expected_steps_per_epoch} but got {cfg_mock.lr_scheduler.steps_per_epoch}'
        self.assertEqual(cfg_mock.lr_scheduler.steps_per_epoch, expected_steps_per_epoch, msg=msg_steps_per_epoch)

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_lr_scheduler_config_overfit_one_batches(self) -> None:
        """Test default setting where the overfit_batches parameter is set to 1."""
        cfg_mock = self.cfg_mock.copy()
        cfg_mock.lr_scheduler = self.one_cycle_lr_scheduler_cfg.copy()
        cfg_mock.lightning.trainer.overfitting.enable = True
        cfg_mock.lightning.trainer.overfitting.params.overfit_batches = 1
        cfg_mock = update_distributed_lr_scheduler_config(cfg_mock, num_train_batches=self.num_train_batches)
        expected_steps_per_epoch = math.ceil(cfg_mock.lightning.trainer.overfitting.params.overfit_batches / self.world_size / self.max_epochs)
        msg_steps_per_epoch = f'Expected steps per epoch to be {expected_steps_per_epoch} but got {cfg_mock.lr_scheduler.steps_per_epoch}'
        self.assertEqual(cfg_mock.lr_scheduler.steps_per_epoch, expected_steps_per_epoch, msg=msg_steps_per_epoch)

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=True)
    def test_update_distributed_lr_scheduler_config_overfit_batches_fractional(self) -> None:
        """Test default setting where the overfit_batches parameter is set to 1."""
        cfg_mock = self.cfg_mock.copy()
        cfg_mock.lr_scheduler = self.one_cycle_lr_scheduler_cfg.copy()
        cfg_mock.lightning.trainer.overfitting.enable = True
        cfg_mock.lightning.trainer.overfitting.params.overfit_batches = 0.5
        cfg_mock = update_distributed_lr_scheduler_config(cfg_mock, num_train_batches=self.num_train_batches)
        batches_to_overfit = math.ceil(self.num_train_batches * cfg_mock.lightning.trainer.overfitting.params.overfit_batches)
        expected_steps_per_epoch = math.ceil(math.ceil(batches_to_overfit / self.world_size) / self.max_epochs)
        msg_steps_per_epoch = f'Expected steps per epoch to be {expected_steps_per_epoch} but got {cfg_mock.lr_scheduler.steps_per_epoch}'
        self.assertEqual(cfg_mock.lr_scheduler.steps_per_epoch, expected_steps_per_epoch, msg=msg_steps_per_epoch)

def setUp(self) -> None:
    """Setup test attributes."""
    self.lr = 1e-05
    self.num_train_batches = 12
    self.batch_size = 2
    self.div_factor = 2
    self.max_lr = 0.01
    self.betas = [0.9, 0.999]
    self.max_epochs = 2
    self.exponential_lr_scheduler_cfg = {'_target_': 'torch.optim.lr_scheduler.ExponentialLR', 'gamma': 0.9, 'steps_per_epoch': None}
    self.one_cycle_lr_scheduler_cfg = {'_target_': 'torch.optim.lr_scheduler.OneCycleLR', 'max_lr': self.max_lr, 'steps_per_epoch': None, 'div_factor': self.div_factor}
    self.cfg_mock = DictConfig({'optimizer': {'_target_': 'torch.optim.Adam', 'lr': self.lr, 'betas': self.betas.copy()}, 'lightning': {'trainer': {'overfitting': {'enable': False, 'params': {'overfit_batches': 1}}, 'params': {'max_epochs': self.max_epochs}}, 'distributed_training': {'equal_variance_scaling_strategy': False}}, 'dataloader': {'params': {'batch_size': self.batch_size}}, 'warm_up_scheduler': {'lr_lambda': {'warm_up_steps': 0.0}}})

class TestSimulationCallbackBuilder(unittest.TestCase):
    """Unit tests for functions in simulation_callback_builder.py."""
    mock_cpu_node_count = 4

    @staticmethod
    def _generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation: int=1, max_callback_workers: int=1, disable_callback_parallelization: bool=False) -> DictConfig:
        """
        Utility function to generate a mocked callback worker configuration with Sequential worker type. Parameters are
        used directly as the config values.
        """
        return DictConfig({'worker': {'_target_': 'nuplan.planning.utils.multithreading.worker_sequential.Sequential'}, 'number_of_cpus_allocated_per_simulation': number_of_cpus_allocated_per_simulation, 'max_callback_workers': max_callback_workers, 'disable_callback_parallelization': disable_callback_parallelization})

    @staticmethod
    def _calculate_expected_number_of_threads(max_callback_workers: int) -> int:
        """
        Utility function to calculate the expected number of threads available to the workers. The calculation is based on
        the current build_callbacks_worker implementation.
        :param max_callback_workers: Config value passed from Sequential worker config.
        """
        return min(TestSimulationCallbackBuilder.mock_cpu_node_count - 1, max_callback_workers)

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_nominal(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests the nominal case of build_callbacks_worker."""
        with mock.patch('nuplan.planning.utils.multithreading.worker_pool.WorkerResources.current_node_cpu_count', return_value=self.mock_cpu_node_count):
            mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers)
            worker_pool = build_callbacks_worker(mock_config)
            expected_number_of_threads = TestSimulationCallbackBuilder._calculate_expected_number_of_threads(max_callback_workers)
            self.assertEqual(worker_pool.number_of_threads, expected_number_of_threads)
            self.assertTrue(isinstance(worker_pool, SingleMachineParallelExecutor))

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.integers(max_value=0), st.integers(min_value=2)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_edge_case_invalid_cpus_allocated(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests an edge case of build_callbacks_worker, where an invalid cpu allocation setting is passed."""
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
        with self.assertRaises(ValueError):
            build_callbacks_worker(mock_config)

    @given(number_of_cpus_allocated_per_simulation=st.one_of(st.none(), st.just(1)), max_callback_workers=st.integers(min_value=1))
    def test_build_callbacks_worker_edge_cases(self, number_of_cpus_allocated_per_simulation: int, max_callback_workers: int) -> None:
        """Tests other edge cases of build_callbacks_worker."""
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=False)
        mock_config.worker._target_ = 'nuplan.planning.utils.multithreading.worker_parallel.SingleMachineParallelExecutor'
        worker_pool = build_callbacks_worker(mock_config)
        self.assertIsNone(worker_pool)
        mock_config = TestSimulationCallbackBuilder._generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation=number_of_cpus_allocated_per_simulation, max_callback_workers=max_callback_workers, disable_callback_parallelization=True)
        worker_pool = build_callbacks_worker(mock_config)
        self.assertIsNone(worker_pool)

    def test_build_simulation_callbacks_serialization_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed SerializationCallback config.
        """
        mock_config = DictConfig({'callback': {'serialization_callback': {'_target_': 'nuplan.planning.simulation.callback.serialization_callback.SerializationCallback', 'folder_name': 'mock_folder', 'serialization_type': 'pickle', 'serialize_into_single_file': False}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_serialization_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_serialization_callback, SerializationCallback))

    def test_build_simulation_callbacks_timing_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed TimingCallback config.
        """
        mock_config = DictConfig({'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_timing_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_timing_callback, TimingCallback))

    def test_build_simulation_callbacks_simulation_log_metric_callbacks(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed SimulationLogCallback
        & MetricCallback configurations.
        """
        mock_config = DictConfig({'callback': {'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        self.assertEqual(0, len(callbacks))

    def test_build_simulation_callbacks_multi_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
        mock_config = DictConfig({'callback': {'multi_callback': {'_target_': 'nuplan.planning.simulation.callback.multi_callback.MultiCallback', 'callbacks': []}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_multi_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_multi_callback, MultiCallback))

    def test_build_simulation_callbacks_visualization_callback(self) -> None:
        """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
        mock_config = DictConfig({'callback': {'visualization_callback': {'_target_': 'nuplan.planning.simulation.callback.visualization_callback.VisualizationCallback', 'renderer': {}}}})
        callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
        expected_visualization_callback, *_ = callbacks
        self.assertEqual(1, len(callbacks))
        self.assertTrue(isinstance(expected_visualization_callback, VisualizationCallback))

@staticmethod
def _generate_mock_build_callbacks_worker_config(number_of_cpus_allocated_per_simulation: int=1, max_callback_workers: int=1, disable_callback_parallelization: bool=False) -> DictConfig:
    """
        Utility function to generate a mocked callback worker configuration with Sequential worker type. Parameters are
        used directly as the config values.
        """
    return DictConfig({'worker': {'_target_': 'nuplan.planning.utils.multithreading.worker_sequential.Sequential'}, 'number_of_cpus_allocated_per_simulation': number_of_cpus_allocated_per_simulation, 'max_callback_workers': max_callback_workers, 'disable_callback_parallelization': disable_callback_parallelization})

def test_build_simulation_callbacks_serialization_callback(self) -> None:
    """
        Tests that build_simulation_callbacks returns the expected result when passed SerializationCallback config.
        """
    mock_config = DictConfig({'callback': {'serialization_callback': {'_target_': 'nuplan.planning.simulation.callback.serialization_callback.SerializationCallback', 'folder_name': 'mock_folder', 'serialization_type': 'pickle', 'serialize_into_single_file': False}}})
    callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
    expected_serialization_callback, *_ = callbacks
    self.assertEqual(1, len(callbacks))
    self.assertTrue(isinstance(expected_serialization_callback, SerializationCallback))

def test_build_simulation_callbacks_timing_callback(self) -> None:
    """
        Tests that build_simulation_callbacks returns the expected result when passed TimingCallback config.
        """
    mock_config = DictConfig({'callback': {'timing_callback': {'_target_': 'nuplan.planning.simulation.callback.timing_callback.TimingCallback'}}})
    callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
    expected_timing_callback, *_ = callbacks
    self.assertEqual(1, len(callbacks))
    self.assertTrue(isinstance(expected_timing_callback, TimingCallback))

def test_build_simulation_callbacks_simulation_log_metric_callbacks(self) -> None:
    """
        Tests that build_simulation_callbacks returns the expected result when passed SimulationLogCallback
        & MetricCallback configurations.
        """
    mock_config = DictConfig({'callback': {'simulation_log_callback': {'_target_': 'nuplan.planning.simulation.callback.simulation_log_callback.SimulationLogCallback'}, 'metric_callback': {'_target_': 'nuplan.planning.simulation.callback.metric_callback.MetricCallback'}}})
    callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
    self.assertEqual(0, len(callbacks))

def test_build_simulation_callbacks_multi_callback(self) -> None:
    """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
    mock_config = DictConfig({'callback': {'multi_callback': {'_target_': 'nuplan.planning.simulation.callback.multi_callback.MultiCallback', 'callbacks': []}}})
    callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
    expected_multi_callback, *_ = callbacks
    self.assertEqual(1, len(callbacks))
    self.assertTrue(isinstance(expected_multi_callback, MultiCallback))

def test_build_simulation_callbacks_visualization_callback(self) -> None:
    """
        Tests that build_simulation_callbacks returns the expected result when passed MultiCallback config.
        """
    mock_config = DictConfig({'callback': {'visualization_callback': {'_target_': 'nuplan.planning.simulation.callback.visualization_callback.VisualizationCallback', 'renderer': {}}}})
    callbacks = build_simulation_callbacks(mock_config, Path('/tmp/mock_dir'))
    expected_visualization_callback, *_ = callbacks
    self.assertEqual(1, len(callbacks))
    self.assertTrue(isinstance(expected_visualization_callback, VisualizationCallback))

class TestScenarioBuilder(unittest.TestCase):
    """Test update_distributed_optimizer_config function."""

    def setUp(self) -> None:
        """Setup test attributes."""
        self.num_scenarios = 5
        self.specified_feature_names = ['agents', 'trajectory', 'vector_map']
        self.mock_cache_path = 's3://mock_path'
        self.expected_s3_paths = sorted((Path(f'mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}') for i in range(5)))

    def _get_mock_get_s3_scenario_cache_with_scenario_type_patch(self) -> Callable[..., List[Any]]:
        """
        Gets mock get_s3_scenario_cache_patch function with scenario types.
        """

        def mock_get_s3_scenario_cache_with_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool, load_from_metadata: bool=True) -> List[Path]:
            """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
            return [Path('s3://mock_vehicle_log_123/mock_scenario_type_A/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_scenario_type_B/mock_token') for _ in range(5)]
        return mock_get_s3_scenario_cache_with_scenario_type

    def _get_mock_get_s3_scenario_cache_without_scenario_type_patch(self) -> Callable[..., List[Any]]:
        """
        Gets mock get_s3_scenario_cache_patch function without scenario types.
        """

        def mock_get_s3_scenario_cache_without_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool) -> List[Path]:
            """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
            return [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)]
        return mock_get_s3_scenario_cache_without_scenario_type

    def _get_mock_check_s3_path_exists_patch(self) -> Callable[[str], bool]:
        """
        Gets mock get_s3_scenario_cache_patch function without scenario types.
        """

        def mock_check_s3_path_exists(cache_path: str) -> bool:
            """
            Mock function for check_s3_path_exists
            :param cache_path: Parent of cache path
            :return: True
            """
            return True
        return mock_check_s3_path_exists

    def _get_mock_expand_s3_dir(self) -> Callable[[str], List[str]]:
        """
        Gets mock expand_s3_dir function.
        """

        def mock_expand_s3_dir(cache_path: str) -> List[str]:
            """
            Mock function for expand_s3_dir.
            :param cache_path: S3 cache path.
            :return: List of mock s3 file paths fetched directly from s3 cache path provided.
            """
            return [f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin' for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]
        return mock_expand_s3_dir

    def _get_mock_fail_to_get_cache_metadata_paths(self) -> Callable[[Path, str], List[str]]:
        """
        Gets mock get_cache_metadata_paths function.
        """

        def mock_fail_to_get_cache_metadata_paths(s3_key: Path, s3_bucket: str) -> List[str]:
            """
            Mock function for get_cache_metadata_paths.
            :param s3_key: S3 cache key.
            :param s3_bucket: S3 cache bucket.
            :return: List of mock s3 metadata file paths fetched from s3 cache path provided.
            """
            return []
        return mock_fail_to_get_cache_metadata_paths

    def _get_mock_worker_map(self) -> Callable[..., List[Any]]:
        """
        Gets mock worker_map function.
        """

        def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
            """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
            return fn(input_objects)
        return mock_worker_map

    def _get_mock_read_cache_metadata(self) -> Callable[..., List[CacheMetadataEntry]]:
        """
        Gets mock read_cache_metadata function.
        """

        def mock_read_cache_metadata(cache_path: Path, metadata_filenames: List[str], worker: WorkerPool) -> List[CacheMetadataEntry]:
            """
            Mock function for read_cache_metadata
            :param cache_path: Path to s3 cache.
            :param metadata_filenames: Filenames of the metadata csv files.
            :return: List of CacheMetadataEntry
            """
            return [CacheMetadataEntry(f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin') for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]
        return mock_read_cache_metadata

    def test_is_valid_token(self) -> None:
        """
        Test that scenario token validation works.
        """
        self.assertFalse(is_valid_token('a'))
        self.assertFalse(is_valid_token(3))
        self.assertTrue(is_valid_token('48681125850853e4'))

    def test_extract_and_filter_scenarios_from_cache(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['mock_scenario_type_A']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_with_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            scenarios = extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)
            msg = f'Expected number of scenarios to be {self.num_scenarios} but got {len(scenarios)}'
            self.assertEqual(len(scenarios), self.num_scenarios, msg=msg)

    def test_extract_and_filter_scenarios_from_cache_when_cache_path_has_no_scenario_type(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type when it doesn't exist in the cache path.
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['mock_scenario_type_A']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_without_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            with self.assertRaises(AssertionError):
                extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)

    def test_extract_and_filter_scenarios_from_cache_when_specified_scenario_type_does_not_exist(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type when specified scenario type does not exist.
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['nonexistent_scenario_type']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_with_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            with self.assertRaises(AssertionError):
                extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)

    def test_get_s3_scenario_cache(self) -> None:
        """
        Test get_s3_scenario_cache and ensure that it returns the correct format of cache paths.
        """
        mock_cache_path = self.mock_cache_path
        mock_feature_names = set(self.specified_feature_names)
        mock_worker = Mock(WorkerPool)
        mock_expand_s3_dir = self._get_mock_expand_s3_dir()
        mock_check_s3_path_exists = self._get_mock_check_s3_path_exists_patch()
        mock_read_cache_metadata = self._get_mock_read_cache_metadata()
        mock_fail_to_get_cache_metadata_paths = self._get_mock_fail_to_get_cache_metadata_paths()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.expand_s3_dir', mock_expand_s3_dir), mock.patch('nuplan.planning.script.builders.scenario_builder.check_s3_path_exists', mock_check_s3_path_exists), mock.patch('nuplan.planning.script.builders.scenario_builder.read_cache_metadata', mock_read_cache_metadata), mock.patch('nuplan.planning.script.builders.scenario_builder.get_cache_metadata_paths', mock_fail_to_get_cache_metadata_paths):
            scenario_cache_paths = get_s3_scenario_cache(mock_cache_path, mock_feature_names, mock_worker)
            msg = f'Expected S3 cache paths to be {self.expected_s3_paths} but got {scenario_cache_paths}'
            self.assertEqual(scenario_cache_paths, self.expected_s3_paths, msg=msg)

def test_is_valid_token(self) -> None:
    """
        Test that scenario token validation works.
        """
    self.assertFalse(is_valid_token('a'))
    self.assertFalse(is_valid_token(3))
    self.assertTrue(is_valid_token('48681125850853e4'))

class TestLRSchedulerBuilder(unittest.TestCase):
    """Test update_distributed_optimizer_config function."""
    world_size = 4

    def setUp(self) -> None:
        """Setup test attributes."""
        self.lr = 5e-05
        self.weight_decay = 0.0005
        self.betas = [0.9, 0.999]
        self.mock_params = [torch.rand(1)]
        self.warm_up_lr_scheduler_cfg = DictConfig({'_target_': 'torch.optim.lr_scheduler.LambdaLR', '_convert_': 'all', 'optimizer': '', 'lr_lambda': {'_target_': 'nuplan.planning.script.builders.lr_scheduler_builder.get_warm_up_lr_scheduler_func', 'warm_up_steps': 100, 'warm_up_strategy': 'linear'}})
        self.lr_scheduler_cfg = DictConfig({'_target_': 'torch.optim.lr_scheduler.OneCycleLR', '_convert_': 'all', 'optimizer': '', 'max_lr': 5e-05, 'epochs': 1, 'steps_per_epoch': 100, 'pct_start': 0.25, 'anneal_strategy': 'cos', 'cycle_momentum': True, 'base_momentum': 0.85, 'max_momentum': 0.95, 'div_factor': 10, 'final_div_factor': 10, 'last_epoch': -1})
        self.initial_lr = self.lr / self.lr_scheduler_cfg.div_factor

    def _get_lr_from_optimizer(self, optimizer: torch.optim.Optimizer) -> float:
        lr: float
        for param_group in optimizer.param_groups:
            lr = param_group['lr']
            break
        return lr

    def test_build_lr_scheduler_with_warm_up_scheduler_and_one_cycle_lr_scheduler(self) -> None:
        """Test that lr_scheduler with warm up scheduler works as expected"""
        optimizer = torch.optim.AdamW(lr=self.lr, weight_decay=self.weight_decay, betas=self.betas, params=self.mock_params)
        sequential_scheduler = build_lr_scheduler(optimizer=optimizer, lr=self.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler_cfg, lr_scheduler_cfg=self.lr_scheduler_cfg)['scheduler']
        self.assertAlmostEqual(self._get_lr_from_optimizer(sequential_scheduler.optimizer), 0.0)
        total_steps = self.lr_scheduler_cfg.steps_per_epoch * self.lr_scheduler_cfg.epochs + self.warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps
        lrs = []
        for _ in range(total_steps):
            sequential_scheduler.step()
            lrs.append(self._get_lr_from_optimizer(sequential_scheduler.optimizer))
        lr_at_end_of_warm_up = lrs[self.warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps - 1]
        lr_at_end_of_training = lrs[-1]
        max_lr = max(lrs)
        self.assertAlmostEqual(max_lr, self.lr)
        self.assertAlmostEqual(lr_at_end_of_warm_up, self.initial_lr)
        self.assertAlmostEqual(lr_at_end_of_training, self.initial_lr / self.lr_scheduler_cfg.final_div_factor)

    def test_build_lr_scheduler_with_warm_up_scheduler_and_no_main_scheduler(self) -> None:
        """Test that lr_scheduler with warm up scheduler works as expected"""
        optimizer = torch.optim.AdamW(lr=self.lr, weight_decay=self.weight_decay, betas=self.betas, params=self.mock_params)
        sequential_scheduler = build_lr_scheduler(optimizer=optimizer, lr=self.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler_cfg, lr_scheduler_cfg=None)['scheduler']
        self.assertAlmostEqual(self._get_lr_from_optimizer(sequential_scheduler.optimizer), 0.0)
        total_steps = self.lr_scheduler_cfg.steps_per_epoch * self.lr_scheduler_cfg.epochs + self.warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps
        lrs = []
        for _ in range(total_steps):
            sequential_scheduler.step()
            lrs.append(self._get_lr_from_optimizer(sequential_scheduler.optimizer))
        lr_at_end_of_warm_up = lrs[self.warm_up_lr_scheduler_cfg.lr_lambda.warm_up_steps - 1]
        lr_at_end_of_training = lrs[-1]
        self.assertAlmostEqual(lr_at_end_of_warm_up, self.lr)
        self.assertAlmostEqual(lr_at_end_of_training, self.lr)

def setUp(self) -> None:
    """Setup test attributes."""
    self.lr = 5e-05
    self.weight_decay = 0.0005
    self.betas = [0.9, 0.999]
    self.mock_params = [torch.rand(1)]
    self.warm_up_lr_scheduler_cfg = DictConfig({'_target_': 'torch.optim.lr_scheduler.LambdaLR', '_convert_': 'all', 'optimizer': '', 'lr_lambda': {'_target_': 'nuplan.planning.script.builders.lr_scheduler_builder.get_warm_up_lr_scheduler_func', 'warm_up_steps': 100, 'warm_up_strategy': 'linear'}})
    self.lr_scheduler_cfg = DictConfig({'_target_': 'torch.optim.lr_scheduler.OneCycleLR', '_convert_': 'all', 'optimizer': '', 'max_lr': 5e-05, 'epochs': 1, 'steps_per_epoch': 100, 'pct_start': 0.25, 'anneal_strategy': 'cos', 'cycle_momentum': True, 'base_momentum': 0.85, 'max_momentum': 0.95, 'div_factor': 10, 'final_div_factor': 10, 'last_epoch': -1})
    self.initial_lr = self.lr / self.lr_scheduler_cfg.div_factor

class TestRunResultProcessor(unittest.TestCase):
    """Test ResultProcessor script."""

    def test_is_submission_successful(self) -> None:
        """Tests that is_submission_successful utility function is working as expected."""
        challenge_names = ['challenge_1', 'challenge_2']
        temp_dirs = []
        temp_files = []
        with TemporaryDirectory() as tmpdir:
            for _ in challenge_names:
                temp_files.append(NamedTemporaryFile(dir=tmpdir))
                sub_tmpdir = TemporaryDirectory(dir=tmpdir)
                temp_dirs.append(sub_tmpdir)
                for instance in range(NUM_INSTANCES_PER_CHALLENGE):
                    temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
                    temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed_not.txt'))
            self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
            extra_completed_at_root = NamedTemporaryFile(dir=tmpdir, suffix='_completed.txt')
            self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
            extra_completed_at_root.close()
            extra_completed_at_challenge_dirs = []
            for sub_tmpdir in temp_dirs:
                extra_completed_at_challenge_dirs.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
            self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
            for item in extra_completed_at_challenge_dirs:
                item.close()
            self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
            for item in temp_files:
                item.close()

    def test_list_subdirs_filtered(self) -> None:
        """Tests listing of filtered files in subdirectories."""
        expected_found = []
        temporary_files = []
        with TemporaryDirectory() as tmpdir:
            with TemporaryDirectory(dir=tmpdir) as sub_tmpdir:
                file1 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.yes')
                file2 = NamedTemporaryFile(dir=tmpdir, suffix='.yes')
                rubbish1 = NamedTemporaryFile(dir=tmpdir, suffix='.no')
                rubbish2 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.no')
                temporary_files.extend([file1, file2, rubbish1, rubbish2])
                expected_found.extend([file1.name, file2.name])
                paths = list_subdirs_filtered(Path(tmpdir), regex_pattern=re.compile('\\.yes'))
                self.assertEqual(set(expected_found), set(paths))
                for temp_file in temporary_files:
                    temp_file.close()

def test_is_submission_successful(self) -> None:
    """Tests that is_submission_successful utility function is working as expected."""
    challenge_names = ['challenge_1', 'challenge_2']
    temp_dirs = []
    temp_files = []
    with TemporaryDirectory() as tmpdir:
        for _ in challenge_names:
            temp_files.append(NamedTemporaryFile(dir=tmpdir))
            sub_tmpdir = TemporaryDirectory(dir=tmpdir)
            temp_dirs.append(sub_tmpdir)
            for instance in range(NUM_INSTANCES_PER_CHALLENGE):
                temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
                temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed_not.txt'))
        self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
        extra_completed_at_root = NamedTemporaryFile(dir=tmpdir, suffix='_completed.txt')
        self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
        extra_completed_at_root.close()
        extra_completed_at_challenge_dirs = []
        for sub_tmpdir in temp_dirs:
            extra_completed_at_challenge_dirs.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
        self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
        for item in extra_completed_at_challenge_dirs:
            item.close()
        self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
        for item in temp_files:
            item.close()

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

class TestNuPlanScenarioUtilsIntegration(unittest.TestCase):
    """Test cases for nuplan_scenario_utils.py"""

    def setUp(self) -> None:
        """Will be run before every test."""
        self.data_root = Path('/data/sets/nuplan/nuplan-v1.1/splits/mini/')
        self.local_path = self.data_root / '2021.09.16.15.12.03_veh-42_01037_01434.db'

    def test_download_file_if_necessary_local_path(self) -> None:
        """
        Test that download_file_if_necessary works as expected with local path input.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
        self.assertFalse(os.path.exists(self.local_path))
        download_file_if_necessary(str(self.data_root), str(self.local_path))
        self.assertTrue(os.path.exists(self.local_path))

    def test_download_file_if_necessary_remote_path(self) -> None:
        """
        Test that download_file_if_necessary works as expected.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
        self.assertFalse(os.path.exists(self.local_path))
        remote_path = 's3://nuplan-production/nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        download_file_if_necessary(str(self.data_root), remote_path)
        self.assertTrue(os.path.exists(self.local_path))

def test_download_file_if_necessary_local_path(self) -> None:
    """
        Test that download_file_if_necessary works as expected with local path input.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
    if os.path.exists(self.local_path):
        os.remove(self.local_path)
    self.assertFalse(os.path.exists(self.local_path))
    download_file_if_necessary(str(self.data_root), str(self.local_path))
    self.assertTrue(os.path.exists(self.local_path))

def test_download_file_if_necessary_remote_path(self) -> None:
    """
        Test that download_file_if_necessary works as expected.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
    if os.path.exists(self.local_path):
        os.remove(self.local_path)
    self.assertFalse(os.path.exists(self.local_path))
    remote_path = 's3://nuplan-production/nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    download_file_if_necessary(str(self.data_root), remote_path)
    self.assertTrue(os.path.exists(self.local_path))

class TestNuPlanScenarioBuilder(unittest.TestCase):
    """
    Tests scenario filtering and construction functionality.
    """

    def test_nuplan_scenario_builder_implements_abstract_scenario_builder(self) -> None:
        """
        Tests that the NuPlanScenarioBuilder implements the AbstractScenarioBuilder interface.
        """
        assert_class_properly_implements_interface(AbstractScenarioBuilder, NuPlanScenarioBuilder)

    def test_get_scenarios_no_filters(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With no additional filters applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method that validates the input args.
            """
            self.assertIsNone(params.filter_tokens)
            self.assertIsNone(params.filter_types)
            self.assertIsNone(params.filter_map_names)
            self.assertFalse(params.include_cameras)
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method.
            """
            return ['filename']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=None, scenario_tokens=None, log_names=None, map_names=None, num_scenarios_per_type=None, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(3, len(result))
            result.sort(key=lambda s: s.token)
            self.assertEqual('a', result[0].token)
            self.assertEqual('b', result[1].token)
            self.assertEqual('c', result[2].token)

    def test_get_scenarios_db_filters(self) -> None:
        """
        Tests that the get_scenarios() method functions properly with db filters applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method.
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertTrue(params.include_cameras)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method.
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=True)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=None, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(6, len(result))
            result.sort(key=lambda s: s.token)
            self.assertEqual('a', result[0].token)
            self.assertEqual('a', result[1].token)
            self.assertEqual('b', result[2].token)
            self.assertEqual('b', result[3].token)
            self.assertEqual('c', result[4].token)
            self.assertEqual('c', result[5].token)

    def test_get_scenarios_num_scenarios_per_type_filter(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With a num_scenarios_per_type filter applied.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertEqual(params.include_cameras, False)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=2, limit_total_scenarios=None, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(4, len(result))
            self.assertEqual(2, sum((1 if s.scenario_type == 'type1' else 0 for s in result)))
            self.assertEqual(2, sum((1 if s.scenario_type == 'type2' else 0 for s in result)))

    def test_get_scenarios_total_num_scenarios_filter(self) -> None:
        """
        Tests that the get_scenarios() method functions properly
        With a total_num_scenarios filter.
        """

        def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
            """
            A patch for the get_scenarios_from_db_file method
            """
            self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
            self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
            self.assertEqual(params.filter_map_names, ['map1', 'map2'])
            self.assertFalse(params.include_cameras)
            self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
            m1 = MockNuPlanScenario(token='a', scenario_type='type1')
            m2 = MockNuPlanScenario(token='b', scenario_type='type1')
            m3 = MockNuPlanScenario(token='c', scenario_type='type2')
            return {'type1': [m1, m2], 'type2': [m3]}

        def discover_log_dbs_patch(load_path: Union[List[str], str]) -> List[str]:
            """
            A patch for the discover_log_dbs method
            """
            return ['filename1', 'filename2', 'filename3']
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_scenarios_from_db_file', db_file_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_builder.discover_log_dbs', discover_log_dbs_patch):
            scenario_builder = NuPlanScenarioBuilder(data_root='foo', map_root='bar', sensor_root='qux', db_files=None, map_version='baz', max_workers=None, verbose=False, scenario_mapping=None, vehicle_parameters=None, include_cameras=False)
            scenario_filter = ScenarioFilter(scenario_types=['type1', 'type2', 'type3'], scenario_tokens=['a', 'b', 'c', 'd', 'e', 'f'], log_names=['filename1', 'filename2'], map_names=['map1', 'map2'], num_scenarios_per_type=None, limit_total_scenarios=5, expand_scenarios=False, remove_invalid_goals=False, shuffle=False, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
            result = scenario_builder.get_scenarios(scenario_filter, Sequential())
            self.assertEqual(5, len(result))

def db_file_patch(params: GetScenariosFromDbFileParams) -> ScenarioDict:
    """
            A patch for the get_scenarios_from_db_file method
            """
    self.assertEqual(params.filter_tokens, ['a', 'b', 'c', 'd', 'e', 'f'])
    self.assertEqual(params.filter_types, ['type1', 'type2', 'type3'])
    self.assertEqual(params.filter_map_names, ['map1', 'map2'])
    self.assertFalse(params.include_cameras)
    self.assertTrue(params.log_file_absolute_path in ['filename1', 'filename2'])
    m1 = MockNuPlanScenario(token='a', scenario_type='type1')
    m2 = MockNuPlanScenario(token='b', scenario_type='type1')
    m3 = MockNuPlanScenario(token='c', scenario_type='type2')
    return {'type1': [m1, m2], 'type2': [m3]}

class TestNuPlanScenarioFilterUtils(unittest.TestCase):
    """
    Tests scenario filter utils for NuPlan
    """

    def _get_mock_scenario_dict(self) -> Dict[str, List[CachedScenario]]:
        """Gets mock scenario dict."""
        return {DEFAULT_SCENARIO_NAME: [CachedScenario(log_name='log/name', token=DEFAULT_SCENARIO_NAME, scenario_type=DEFAULT_SCENARIO_NAME) for i in range(500)], 'lane_following_with_lead': [CachedScenario(log_name='log/name', token='lane_following_with_lead', scenario_type='lane_following_with_lead') for i in range(80)], 'unprotected_left_turn': [CachedScenario(log_name='log/name', token='unprotected_left_turn', scenario_type='unprotected_left_turn') for i in range(120)]}

    def _get_mock_nuplan_scenario_dict_for_timestamp_filtering(self) -> Dict[str, List[CachedScenario]]:
        """Gets mock scenario dict."""
        mock_scenario_dict = {DEFAULT_SCENARIO_NAME: [Mock(NuPlanScenario) for _ in range(0, 100, 3)], 'lane_following_with_lead': [Mock(NuPlanScenario) for _ in range(0, 100, 6)], 'lane_following_without_lead': [Mock(NuPlanScenario) for _ in range(3)]}
        for i in range(0, len(mock_scenario_dict[DEFAULT_SCENARIO_NAME]) * int(1000000.0), int(1000000.0)):
            mock_scenario_dict[DEFAULT_SCENARIO_NAME][int(i / 1000000.0)]._initial_lidar_timestamp = i * 3
        for i in range(0, len(mock_scenario_dict['lane_following_with_lead']) * int(1000000.0), int(1000000.0)):
            mock_scenario_dict['lane_following_with_lead'][int(i / 1000000.0)]._initial_lidar_timestamp = i * 6
        mock_scenario_dict['lane_following_without_lead'][0]._initial_lidar_timestamp = 5.0 * int(1000000.0)
        mock_scenario_dict['lane_following_without_lead'][1]._initial_lidar_timestamp = 100.0 * int(1000000.0)
        mock_scenario_dict['lane_following_without_lead'][2]._initial_lidar_timestamp = 6.0 * int(1000000.0)
        return mock_scenario_dict

    def _get_mock_worker_map(self) -> Callable[..., List[Any]]:
        """
        Gets mock worker_map function.
        """

        def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
            """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
            return fn(input_objects)
        return mock_worker_map

    def test_filter_total_num_scenarios_int_max_scenarios_requires_removing_known_scenario_types(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 100
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
        self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_total_num_scenarios_int_max_scenarios_less_than_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 300
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
        self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
        self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_total_num_scenarios_int_max_scenarios_more_than_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 800
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertDictEqual(final_scenario_dict, mock_scenario_dict)

    def test_filter_total_num_scenarios_float_requires_removing_known_scenario_types(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.2
        randomize = True
        final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
        self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

    def test_filter_total_num_scenarios_float_removes_only_default_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.5
        randomize = True
        final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
        self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
        self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

    def test_remove_all_scenarios_int_limit_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0
        randomize = True
        with self.assertRaises(AssertionError):
            filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

    def test_remove_all_scenarios_float_limit_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.0
        randomize = True
        with self.assertRaises(AssertionError):
            filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

    def test_remove_exactly_all_default_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to number of known scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 200
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertEqual(len(final_scenario_dict['lane_following_with_lead']), len(mock_scenario_dict['lane_following_with_lead']))
        self.assertEqual(len(final_scenario_dict['unprotected_left_turn']), len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_scenarios_by_timestamp(self) -> None:
        """
        Tests filter_scenarios_by_timestamp with default threshold
        """
        mock_worker_map = self._get_mock_worker_map()
        mock_nuplan_scenario_dict = self._get_mock_nuplan_scenario_dict_for_timestamp_filtering()
        with patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.worker_map', mock_worker_map):
            final_scenario_dict = filter_scenarios_by_timestamp(mock_nuplan_scenario_dict.copy())
            self.assertEqual(len(final_scenario_dict['lane_following_with_lead']), len(mock_nuplan_scenario_dict['lane_following_with_lead']))
            self.assertEqual(len(final_scenario_dict[DEFAULT_SCENARIO_NAME]), len(mock_nuplan_scenario_dict[DEFAULT_SCENARIO_NAME]) * 0.5)
            self.assertEqual(len(final_scenario_dict['lane_following_without_lead']), len(mock_nuplan_scenario_dict['lane_following_without_lead']) - 1)

    def test_filter_fraction_lidarpc_tokens_in_set(self) -> None:
        """
        Test filter_fraction_lidarpc_tokens_in_set with fractional thresholds {0, 0.5, 1}.
        """
        alphabet = ['a', 'b', 'c', 'd', 'e', 'f']
        mock_nuplan_scenarios = []
        for start_letter in range(4):
            mock_nuplan_scenario = Mock(NuPlanScenario)
            mock_nuplan_scenario.get_scenario_tokens.return_value = set(alphabet[start_letter:start_letter + 3])
            mock_nuplan_scenarios.append(mock_nuplan_scenario)
        full_intersection_scenario, two_intersection_scenario, one_intersection_scenario, no_intersection_scenario = mock_nuplan_scenarios
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_json_path = Path(tmp_dir) / 'tmp_token_set.json'
            json.dump(['a', 'b', 'c'], open(tmp_json_path, 'w'))
            scenario_dict = {'on_pickup_dropoff': [no_intersection_scenario, one_intersection_scenario]}
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 0), {'on_pickup_dropoff': [one_intersection_scenario]})
            scenario_dict['on_pickup_dropoff'] = [one_intersection_scenario, two_intersection_scenario]
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 0.5), {'on_pickup_dropoff': [two_intersection_scenario]})
            scenario_dict['on_pickup_dropoff'] = [two_intersection_scenario, full_intersection_scenario]
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 1), {'on_pickup_dropoff': [full_intersection_scenario]})

    def test_filter_non_stationary_ego(self) -> None:
        """Test filter_non_stationary_ego with 0.5m displacement threshold"""
        stationary_ego_pudo_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.01, y=0.0))
        mobile_ego_pudo_scenario = MockAbstractScenario()
        scenario_dict = {'on_pickup_dropoff': [stationary_ego_pudo_scenario, mobile_ego_pudo_scenario]}
        filtered_scenario_dict = filter_non_stationary_ego(scenario_dict, minimum_threshold=0.5)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [mobile_ego_pudo_scenario])

    def test_filter_ego_starts(self) -> None:
        """Test filter_ego_starts with 0.1 m/s speed threshold"""
        slow_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=0.01, y=0.0), time_step=1)
        fast_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=1, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [slow_acceleration_scenario, fast_acceleration_scenario]}
        filtered_scenario_dict = filter_ego_starts(scenario_dict, speed_threshold=0.1, speed_noise_tolerance=0.1)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [fast_acceleration_scenario])

    def test_filter_ego_stops(self) -> None:
        """Test filter_ego_stops with 0.1 m/s speed threshold"""
        slow_deceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=1.0, y=0.0), fixed_acceleration=StateVector2D(x=-0.01, y=0.0), time_step=1)
        fast_deceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=1.0, y=0.0), fixed_acceleration=StateVector2D(x=-1 / 9, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [slow_deceleration_scenario, fast_deceleration_scenario]}
        filtered_scenario_dict = filter_ego_stops(scenario_dict, speed_threshold=0.1, speed_noise_tolerance=0.1)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [fast_deceleration_scenario])

    def test_ego_startstop_noise_tolerance(self) -> None:
        """Test filter_ego_starts with ego barely crossing speed threshold and noise tolerance higher than threshold"""
        fast_enough_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=0.11, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [fast_enough_acceleration_scenario]}
        filtered_scenario_dict = filter_ego_starts(scenario_dict, speed_threshold=1, speed_noise_tolerance=2)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [])

    def test_filter_ego_has_route(self) -> None:
        """
        Test filter_ego_has_route with one route roadblock in the VectorMap (True case),
        and with no route-intersecting roadblocks (False case).
        """
        map_radius = 35
        scenario = MockAbstractScenario()
        scenario_dict = {'on_pickup_dropoff': [scenario]}
        with patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_neighbor_vector_map') as get_neighbor_vector_map:
            get_neighbor_vector_map.return_value = (None, None, None, None, LaneSegmentRoadBlockIDs(['a', 'b', 'c']))
            with patch.object(scenario, 'get_route_roadblock_ids') as get_route_roadblock_ids:
                get_route_roadblock_ids.return_value = ['d', 'e', 'a']
                self.assertEqual(filter_ego_has_route(scenario_dict, map_radius)['on_pickup_dropoff'], [scenario])
                get_route_roadblock_ids.return_value = ['d', 'e', 'f']
                self.assertEqual(filter_ego_has_route(scenario_dict, map_radius)['on_pickup_dropoff'], [])

def test_filter_total_num_scenarios_int_max_scenarios_requires_removing_known_scenario_types(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 100
    randomize = True
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
    self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
    self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
    self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

def test_filter_total_num_scenarios_int_max_scenarios_less_than_total_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 300
    randomize = True
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
    self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
    self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
    self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

def test_filter_total_num_scenarios_int_max_scenarios_more_than_total_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 800
    randomize = True
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertDictEqual(final_scenario_dict, mock_scenario_dict)

def test_filter_total_num_scenarios_float_requires_removing_known_scenario_types(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 0.2
    randomize = True
    final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
    self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
    self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
    self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

def test_filter_total_num_scenarios_float_removes_only_default_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 0.5
    randomize = True
    final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
    self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
    self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
    self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

def test_remove_all_scenarios_int_limit_total_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 0
    randomize = True
    with self.assertRaises(AssertionError):
        filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

def test_remove_all_scenarios_float_limit_total_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 0.0
    randomize = True
    with self.assertRaises(AssertionError):
        filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

def test_remove_exactly_all_default_scenarios(self) -> None:
    """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to number of known scenarios.
        """
    mock_scenario_dict = self._get_mock_scenario_dict()
    limit_total_scenarios = 200
    randomize = True
    final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
    self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
    self.assertEqual(len(final_scenario_dict['lane_following_with_lead']), len(mock_scenario_dict['lane_following_with_lead']))
    self.assertEqual(len(final_scenario_dict['unprotected_left_turn']), len(mock_scenario_dict['unprotected_left_turn']))
    self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

def filter_paths(paths: List[str], filters: Optional[List[str]]) -> List[str]:
    """Filters a list of paths according to a list of filters.
    :param paths: The input paths.
    :param filters: The filters of the elements to keep.
    :return: The subset of paths that contain at least one of the keywords defined in filters.
    """
    return [path for path in paths if not filters or any((_filter in path for _filter in filters))]

