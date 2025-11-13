# Cluster 7

def visualize_scenario(scenario: NuPlanScenario, save_dir: str='/tmp/scenario_visualization/', bokeh_port: int=8899) -> None:
    """
    Visualize a scenario in Bokeh.
    :param scenario: Scenario object to be visualized.
    :param save_dir: Dir to save serialization and visualization artifacts.
    :param bokeh_port: Port that the server bokeh starts to render the generate the visualization will run on.
    """
    map_factory = NuPlanMapFactory(get_maps_db(map_root=scenario.map_root, map_version=scenario.map_version))
    simulation_history = serialize_scenario(scenario)
    simulation_scenario_key = save_scenes_to_dir(scenario=scenario, save_dir=save_dir, simulation_history=simulation_history)
    visualize_scenarios([simulation_scenario_key], map_factory, Path(save_dir), bokeh_port=bokeh_port)

class BaseNuPlanDBSplitter(DBSplitterInterface):
    """Base class for all NuPlanDB splitters."""

    def __init__(self, db: NuPlanDB):
        """
        :param db: NuPlanDB instance.
        """
        self._db = db
        self._db.add_ref()

    def __del__(self) -> None:
        """
        Called when the splitter is being destroyed.
        """
        self._db.remove_ref()

    def __repr__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        return "{}(NuPlanDB('{}'))".format(self.__class__.__name__, self._db.name)

    def list(self) -> List[str]:
        """
        Get the list of the splits.
        :return: The list of splits.
        """
        return list(self._splits.keys())

    def split(self, split_name: str) -> List[str]:
        """
        Get list of tokens for the split.
        :return: The list of tokens for the split.
        """
        return sorted(self._splits[split_name])

    def logs(self, split_name: str) -> List[str]:
        """
        Get list of logs for the split.
        :return: The list of logs for the split.
        """
        sample_tokens = self.split(split_name)
        return list({self._db.sample[token].extraction.log.logfile for token in sample_tokens})

    @property
    @abc.abstractmethod
    def _splits(self) -> DefaultDict[str, List[str]]:
        """
        Returns a dictionary that maps from split name to list of NuPlanDB tokens.
        :return: A dictionary that maps from split name to list of NuPlanDB tokens.
        """
        pass

def __init__(self, db: NuPlanDB):
    """
        :param db: NuPlanDB instance.
        """
    self._db = db
    self._db.add_ref()

def __del__(self) -> None:
    """
        Called when the splitter is being destroyed.
        """
    self._db.remove_ref()

class NuPlanDBWrapper:
    """Wrapper for NuPlanDB that allows loading and accessing mutliple log database."""

    def __init__(self, data_root: str, map_root: str, db_files: Optional[Union[List[str], str]], map_version: str, max_workers: Optional[int]=None, verbose: bool=True):
        """
        Initialize the database wrapper.
        :param data_root: Local data root for loading (or storing downloaded) the log databases.
                        If `db_files` is not None, all downloaded databases will be stored to this data root.
        :param map_root: Local map root for loading (or storing downloaded) the map database.
        :param db_files: Path to load the log databases from, which can be:
                         * filename path to single database:
                            - locally - e.g. /data/sets/nuplan/v1.0/log_1.db
                            - remotely (S3) - e.g. s3://bucket/nuplan/v1.0/log_1.db
                         * directory path of databases to load:
                            - locally - e.g. /data/sets/nuplan/v1.0/
                            - remotely (S3) - e.g. s3://bucket/nuplan/v1.0/
                         * list of database filenames:
                            - locally - e.g. [/data/sets/nuplan/v1.0/log_1.db, /data/sets/nuplan/v1.0/log_2.db]
                            - remotely (S3) - e.g. [s3://bucket/nuplan/v1.0/log_1.db, s3://bucket/nuplan/v1.0/log_2.db]
                         * list of database directories:
                            - locally - e.g. [/data/sets/nuplan/v1.0_split_1/, /data/sets/nuplan/v1.0_split_2/]
                            - remotely (S3) - e.g. [s3://bucket/nuplan/v1.0_split_1/, s3://bucket/nuplan/v1.0_split_2/]
                         Note: Regex expansion is not yet supported.
                         Note: If None, all database filenames found under `data_root` will be used.
        :param map_version: Version of map database to load. The map database is passed to each loaded log database.
        :param max_workers: Maximum number of workers to use when loading the databases concurrently.
                            Only used when the number of databases to load is larger than this parameter.
        :param verbose: Whether to print progress and details during the database loading process.
        """
        self._data_root = data_root
        self._map_root = map_root
        self._db_files = db_files
        self._map_version = map_version
        self._max_workers = max_workers
        self._verbose = verbose
        assert not self._data_root.startswith('s3://'), f'Data root cannot be an S3 path, got {self._data_root}'
        assert not self._map_root.startswith('s3://'), f'Map root cannot be an S3 path, got {self._map_root}'
        self._data_root = self._data_root.replace('//', '/')
        self._map_root = self._map_root.replace('//', '/')
        self._maps_db = GPKGMapsDB(map_root=self._map_root, map_version=self._map_version)
        logger.info('Loaded maps DB')
        self._log_db_mapping = load_log_db_mapping(data_root=self._data_root, db_files=self._db_files, maps_db=self._maps_db, max_workers=self._max_workers, verbose=self._verbose)
        logger.info(f'Loaded {len(self.log_dbs)} log DBs')

    def __reduce__(self) -> Tuple[Type[NuPlanDBWrapper], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._data_root, self._map_root, self._db_files, self._map_version, self._max_workers, self._verbose))

    def __del__(self) -> None:
        """
        Called when the object is being garbage collected.
        """
        for log_name in self.log_names:
            self._log_db_mapping[log_name].remove_ref()

    @property
    def data_root(self) -> str:
        """Get the data root."""
        return self._data_root

    @property
    def map_root(self) -> str:
        """Get the map root."""
        return self._map_root

    @property
    def map_version(self) -> str:
        """Get the map version."""
        return self._map_version

    @property
    def maps_db(self) -> GPKGMapsDB:
        """Get the map database object."""
        return self._maps_db

    @property
    def log_db_mapping(self) -> Dict[str, NuPlanDB]:
        """Get the dictionary that maps log names to log database objects."""
        return self._log_db_mapping

    @property
    def log_names(self) -> List[str]:
        """Get the list of log names of all loaded log databases."""
        return list(self._log_db_mapping.keys())

    @property
    def log_dbs(self) -> List[NuPlanDB]:
        """Get the list of all loaded log databases."""
        return list(self._log_db_mapping.values())

    def get_log_db(self, log_name: str) -> NuPlanDB:
        """
        Retrieve a log database by log name.
        :param log_name: Log name to access the database hash table.
        :return: Retrieve database object.
        """
        return self._log_db_mapping[log_name]

    def get_all_scenes(self) -> Iterable[Scene]:
        """
        Retrieve and yield all scenes across all loaded log databases.
        :yield: Next scene from all scenes in the loaded databases.
        """
        for db in self._log_db_mapping.values():
            for scene in db.scene:
                yield scene

    def get_all_scenario_types(self) -> List[str]:
        """Retrieve all unique scenario tags in the collection of databases."""
        return sorted({tag for log_db in self.log_dbs for tag in log_db.get_unique_scenario_tags()})

def __init__(self, data_root: str, map_root: str, db_files: Optional[Union[List[str], str]], map_version: str, max_workers: Optional[int]=None, verbose: bool=True):
    """
        Initialize the database wrapper.
        :param data_root: Local data root for loading (or storing downloaded) the log databases.
                        If `db_files` is not None, all downloaded databases will be stored to this data root.
        :param map_root: Local map root for loading (or storing downloaded) the map database.
        :param db_files: Path to load the log databases from, which can be:
                         * filename path to single database:
                            - locally - e.g. /data/sets/nuplan/v1.0/log_1.db
                            - remotely (S3) - e.g. s3://bucket/nuplan/v1.0/log_1.db
                         * directory path of databases to load:
                            - locally - e.g. /data/sets/nuplan/v1.0/
                            - remotely (S3) - e.g. s3://bucket/nuplan/v1.0/
                         * list of database filenames:
                            - locally - e.g. [/data/sets/nuplan/v1.0/log_1.db, /data/sets/nuplan/v1.0/log_2.db]
                            - remotely (S3) - e.g. [s3://bucket/nuplan/v1.0/log_1.db, s3://bucket/nuplan/v1.0/log_2.db]
                         * list of database directories:
                            - locally - e.g. [/data/sets/nuplan/v1.0_split_1/, /data/sets/nuplan/v1.0_split_2/]
                            - remotely (S3) - e.g. [s3://bucket/nuplan/v1.0_split_1/, s3://bucket/nuplan/v1.0_split_2/]
                         Note: Regex expansion is not yet supported.
                         Note: If None, all database filenames found under `data_root` will be used.
        :param map_version: Version of map database to load. The map database is passed to each loaded log database.
        :param max_workers: Maximum number of workers to use when loading the databases concurrently.
                            Only used when the number of databases to load is larger than this parameter.
        :param verbose: Whether to print progress and details during the database loading process.
        """
    self._data_root = data_root
    self._map_root = map_root
    self._db_files = db_files
    self._map_version = map_version
    self._max_workers = max_workers
    self._verbose = verbose
    assert not self._data_root.startswith('s3://'), f'Data root cannot be an S3 path, got {self._data_root}'
    assert not self._map_root.startswith('s3://'), f'Map root cannot be an S3 path, got {self._map_root}'
    self._data_root = self._data_root.replace('//', '/')
    self._map_root = self._map_root.replace('//', '/')
    self._maps_db = GPKGMapsDB(map_root=self._map_root, map_version=self._map_version)
    logger.info('Loaded maps DB')
    self._log_db_mapping = load_log_db_mapping(data_root=self._data_root, db_files=self._db_files, maps_db=self._maps_db, max_workers=self._max_workers, verbose=self._verbose)
    logger.info(f'Loaded {len(self.log_dbs)} log DBs')

def __del__(self) -> None:
    """
        Called when the object is being garbage collected.
        """
    for log_name in self.log_names:
        self._log_db_mapping[log_name].remove_ref()

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

def setUp(self) -> None:
    """Sets up for the tests cases"""
    self.lidar_pc = get_test_nuplan_lidarpc()
    self.lidar_pc_with_blob = get_test_nuplan_lidarpc_with_blob()

def test_path(self) -> None:
    """Tests the path property"""
    db = get_test_nuplan_db()
    result = self.lidar_pc_with_blob.path(db)
    self.assertIsInstance(result, str)

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

def setUp(self) -> None:
    """Sets up for the test cases"""
    self.lidar_box_vehicle = get_test_nuplan_lidar_box_vehicle()
    self.lidar_box = get_test_nuplan_lidar_box()

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

def setUp(self) -> None:
    """Setup funciton for class."""
    self.db = get_test_nuplan_db()
    self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

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

def setUp(self) -> None:
    """Set up the test case."""
    self.db = get_test_nuplan_db()
    self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

class TestLoadBoxes(unittest.TestCase):
    """Tests for get_boxes() and get_future_box_sequence()"""

    def setUp(self) -> None:
        """Set up the test case."""
        self.db = get_test_nuplan_db()
        self.lidar_pc = get_test_nuplan_lidarpc()
        self.future_horizon_len_s = 1
        self.future_interval_s = 0.05

    def test_can_run_get_future_box_sequence(self) -> None:
        """Test get future box sequence."""
        get_future_box_sequence(lidar_pcs=[self.lidar_pc, self.lidar_pc.next], frame=Frame.VEHICLE, future_horizon_len_s=self.future_horizon_len_s, trans_matrix_ego=self.lidar_pc.ego_pose.trans_matrix_inv, future_interval_s=self.future_interval_s)

    def test_pack_future_boxes(self) -> None:
        """Test pack future boxes."""
        track_token_2_box_sequence = get_future_box_sequence(lidar_pcs=[self.lidar_pc, self.lidar_pc.next], frame=Frame.VEHICLE, future_horizon_len_s=self.future_horizon_len_s, trans_matrix_ego=self.lidar_pc.ego_pose.trans_matrix_inv, future_interval_s=self.future_interval_s)
        boxes_with_futures = pack_future_boxes(track_token_2_box_sequence=track_token_2_box_sequence, future_horizon_len_s=self.future_horizon_len_s, future_interval_s=self.future_interval_s)
        for box in boxes_with_futures:
            for horizon_idx, horizon_s in enumerate(box.get_all_future_horizons_s()):
                future_center = box.get_future_center_at_horizon(horizon_s)
                future_orientation = box.get_future_orientation_at_horizon(horizon_s)
                self.assertTrue(box.track_token is not None)
                expected_future_box = track_token_2_box_sequence[box.track_token][horizon_idx + 1]
                if expected_future_box is None:
                    np.testing.assert_array_equal(future_center, [np.nan, np.nan, np.nan])
                    self.assertEqual(future_orientation, None)
                else:
                    np.testing.assert_array_equal(expected_future_box.center, future_center)
                    self.assertEqual(expected_future_box.orientation, future_orientation)

    def test_load_boxes_from_lidarpc(self) -> None:
        """Test load all boxes from a lidar pc."""
        boxes = load_boxes_from_lidarpc(self.db, self.lidar_pc, ['pedestrian', 'vehicle'], False, 80.04, self.future_horizon_len_s, self.future_interval_s, {'pedestrian': 0, 'vehicle': 1})
        self.assertSetEqual({'pedestrian', 'vehicle'}, set(boxes.keys()))
        self.assertEqual(len(boxes['pedestrian']), 70)
        self.assertEqual(len(boxes['vehicle']), 29)

def setUp(self) -> None:
    """Set up the test case."""
    self.db = get_test_nuplan_db()
    self.lidar_pc = get_test_nuplan_lidarpc()
    self.future_horizon_len_s = 1
    self.future_interval_s = 0.05

class TestGetFutureEgoTrajectory(unittest.TestCase):
    """Test getting future ego trajectory."""

    def setUp(self) -> None:
        """Set up test case."""
        self.lidar_pc = get_test_nuplan_lidarpc()
        self.future_lidarpc_recs: List[LidarPc] = [self.lidar_pc]
        while len(self.future_lidarpc_recs) < 200:
            self.future_lidarpc_recs.append(self.future_lidarpc_recs[-1].next)
        self.future_ego_poses = [rec.ego_pose for rec in self.future_lidarpc_recs]

    def test_get_future_ego_trajectory(self) -> None:
        """Test getting future ego trajectory."""
        future_ego_traj = get_future_ego_trajectory(self.lidar_pc, self.future_ego_poses, np.eye(4), 5.0, 0.5)
        self.assertEqual(future_ego_traj[0, 3], self.lidar_pc.ego_pose.timestamp)
        self.assertEqual(len(future_ego_traj), 11)
        self.assertLessEqual(abs((future_ego_traj[-1, 3] - future_ego_traj[0, 3]) / 1000000.0 - 5.0), 0.5)

    def test_get_future_ego_trajectory_not_enough(self) -> None:
        """Test getting future ego trajectory when there are not enough ego poses."""
        future_ego_traj = get_future_ego_trajectory(self.lidar_pc, self.future_ego_poses[:50], np.eye(4), 5.0, 0.5)
        self.assertEqual(future_ego_traj[0, 3], self.lidar_pc.ego_pose.timestamp)
        self.assertEqual(len(future_ego_traj), 11)
        np.testing.assert_equal(future_ego_traj[-1, :], [np.nan, np.nan, np.nan, np.nan])

def setUp(self) -> None:
    """Set up test case."""
    self.lidar_pc = get_test_nuplan_lidarpc()
    self.future_lidarpc_recs: List[LidarPc] = [self.lidar_pc]
    while len(self.future_lidarpc_recs) < 200:
        self.future_lidarpc_recs.append(self.future_lidarpc_recs[-1].next)
    self.future_ego_poses = [rec.ego_pose for rec in self.future_lidarpc_recs]

class TestRenderOnMap(unittest.TestCase):
    """Test rendering on map."""

    def setUp(self) -> None:
        """Set up test case."""
        self.db = get_test_nuplan_db()
        self.lidar_pc = get_test_nuplan_lidarpc_with_blob()
        self.future_lidarpc_recs: List[LidarPc] = [self.lidar_pc]
        while len(self.future_lidarpc_recs) < 200:
            self.future_lidarpc_recs.append(self.future_lidarpc_recs[-1].next)
        self.future_ego_poses = [rec.ego_pose for rec in self.future_lidarpc_recs]

    def test_render_on_map(self) -> None:
        """Test render on map."""
        render_on_map(self.lidar_pc, self.db, self.lidar_pc.boxes(), self.future_ego_poses, render_boxes_with_velocity=True, render_map_raster=False, render_vector_map=True, with_random_color=True, render_future_ego_poses=True)

def setUp(self) -> None:
    """Set up test case."""
    self.db = get_test_nuplan_db()
    self.lidar_pc = get_test_nuplan_lidarpc_with_blob()
    self.future_lidarpc_recs: List[LidarPc] = [self.lidar_pc]
    while len(self.future_lidarpc_recs) < 200:
        self.future_lidarpc_recs.append(self.future_lidarpc_recs[-1].next)
    self.future_ego_poses = [rec.ego_pose for rec in self.future_lidarpc_recs]

class TestNuPlanDBWrapper(unittest.TestCase):
    """Test NuPlanDB wrapper which supports loading/accessing multiple log databases."""

    def setUp(self) -> None:
        """Set up test case."""
        self.db_wrapper = get_test_nuplan_db_wrapper_nocache()

    def test_serialization(self) -> None:
        """Test whether the wrapper object can be serialized/deserialized correctly."""
        serialized_binary = pickle.dumps(self.db_wrapper)
        re_db_wrapper: NuPlanDBWrapper = pickle.loads(serialized_binary)
        self.assertEqual(self.db_wrapper.data_root, re_db_wrapper.data_root)

    def test_maps_db(self) -> None:
        """Test that maps DB has been loaded."""
        self.db_wrapper.maps_db.load_vector_layer('us-nv-las-vegas-strip', 'lane_connectors')

    def test_nuplandb_wrapper_memory_usage(self) -> None:
        """
        Test that repeatedly creating and destroying nuplan DB wrapper objects does not cause memory leaks.
        """

        def spin_up_db_wrapper() -> None:
            db_wrapper = get_test_nuplan_db_wrapper_nocache()
            del db_wrapper
        starting_usage = 0
        ending_usage = 0
        num_iterations = 5
        hpy = guppy.hpy()
        hpy.setrelheap()
        for i in range(0, num_iterations, 1):
            spin_up_db_wrapper()
            gc.collect()
            heap = hpy.heap()
            _ = heap.size
            if i == num_iterations - 2:
                starting_usage = heap.size
            if i == num_iterations - 1:
                ending_usage = heap.size
        memory_difference_in_mb = (ending_usage - starting_usage) / (1024 * 1024)
        max_allowable_growth_mb = max(0.1, 0.1 * starting_usage / (1024 * 1024))
        self.assertGreater(max_allowable_growth_mb, memory_difference_in_mb)

def setUp(self) -> None:
    """Set up test case."""
    self.db_wrapper = get_test_nuplan_db_wrapper_nocache()

def spin_up_db_wrapper() -> None:
    db_wrapper = get_test_nuplan_db_wrapper_nocache()
    del db_wrapper

class TestEgoPose(unittest.TestCase):
    """Tests the EgoPose class"""

    def setUp(self) -> None:
        """Sets up for the test cases"""
        self.ego_pose = get_test_nuplan_egopose()

    @patch('nuplan.database.nuplan_db_orm.ego_pose.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the _session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.ego_pose._session
        inspect_mock.assert_called_once_with(self.ego_pose)
        self.assertEqual(result, session_mock)

    @patch('nuplan.database.nuplan_db_orm.ego_pose.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the __repr__ method"""
        result = self.ego_pose.__repr__()
        simple_repr_mock.assert_called_once_with(self.ego_pose)
        self.assertEqual(result, simple_repr_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.ego_pose.Quaternion', autospec=True)
    def test_quaternion(self, quaternion_mock: Mock) -> None:
        """Tests the quaternion method"""
        result = self.ego_pose.quaternion
        quaternion_mock.assert_called_once_with(self.ego_pose.qw, self.ego_pose.qx, self.ego_pose.qy, self.ego_pose.qz)
        self.assertEqual(result, quaternion_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.ego_pose.np.array', autospec=True)
    def test_translation_np(self, np_array_mock: Mock) -> None:
        """Tests the translation_np method"""
        result = self.ego_pose.translation_np
        np_array_mock.assert_called_with([self.ego_pose.x, self.ego_pose.y, self.ego_pose.z])
        self.assertEqual(result, np_array_mock.return_value)

    def test_trans_matrix_and_inv(self) -> None:
        """Tests the transformation matrix and it's inverse method"""
        trans_matrix = self.ego_pose.trans_matrix
        trans_matrix_inv = self.ego_pose.trans_matrix_inv
        result = np.matmul(trans_matrix, trans_matrix_inv)
        np.testing.assert_allclose(result, np.identity(4), atol=0.001)

    def test_rotate_2d_points2d_to_ego_vehicle_frame(self) -> None:
        """Tests the rotate_2d_points2d_to_ego_vehicle_frame method"""
        points2d: npt.NDArray[np.float32] = np.ones([1, 2], dtype=np.float32)
        result = self.ego_pose.rotate_2d_points2d_to_ego_vehicle_frame(points2d)
        self.assertEqual(result.ndim, 2)

    def test_get_map_crop_dimensions(self) -> None:
        """
        Test that map crop method produces map of the correct dimensions.
        Test time: 10.569s
        """
        xrange = (-60, 60)
        yrange = (-60, 60)
        rotate_face_up = False
        map_layer_description = 'intensity'
        map_layer_precision = 0.1
        map_scale = 1 / map_layer_precision
        num_samples = 10
        db = get_test_nuplan_db()
        selected_indices = random.sample(list(range(len(db.ego_pose))), num_samples)
        expected_dimensions = ((xrange[1] - xrange[0]) * map_scale, (yrange[1] - yrange[0]) * map_scale)
        ego_pose_list = db.ego_pose
        for i in selected_indices:
            current_ego_pose = ego_pose_list[i]
            if current_ego_pose.lidar_pc is None:
                continue
            map_crop = current_ego_pose.get_map_crop(maps_db=db.maps_db, xrange=xrange, yrange=yrange, map_layer_name=map_layer_description, rotate_face_up=rotate_face_up)
            self.assertTrue(map_crop[0] is not None)
            self.assertEqual(expected_dimensions, map_crop[0].shape, f'Dimensions failed at ego pose index {i}')

    def test_get_vector_map(self) -> None:
        """Tests the get vector map method"""
        xrange = (-60, 60)
        yrange = (-60, 60)
        db = get_test_nuplan_db()
        num_samples = 10
        selected_indices = random.sample(list(range(len(db.ego_pose))), num_samples)
        ego_pose_list = db.ego_pose
        for i in selected_indices:
            current_ego_pose = ego_pose_list[i]
            if current_ego_pose.lidar_pc is None:
                continue
            result = current_ego_pose.get_vector_map(db.maps_db, xrange, yrange)
            self.assertIsNotNone(result)

def test_get_map_crop_dimensions(self) -> None:
    """
        Test that map crop method produces map of the correct dimensions.
        Test time: 10.569s
        """
    xrange = (-60, 60)
    yrange = (-60, 60)
    rotate_face_up = False
    map_layer_description = 'intensity'
    map_layer_precision = 0.1
    map_scale = 1 / map_layer_precision
    num_samples = 10
    db = get_test_nuplan_db()
    selected_indices = random.sample(list(range(len(db.ego_pose))), num_samples)
    expected_dimensions = ((xrange[1] - xrange[0]) * map_scale, (yrange[1] - yrange[0]) * map_scale)
    ego_pose_list = db.ego_pose
    for i in selected_indices:
        current_ego_pose = ego_pose_list[i]
        if current_ego_pose.lidar_pc is None:
            continue
        map_crop = current_ego_pose.get_map_crop(maps_db=db.maps_db, xrange=xrange, yrange=yrange, map_layer_name=map_layer_description, rotate_face_up=rotate_face_up)
        self.assertTrue(map_crop[0] is not None)
        self.assertEqual(expected_dimensions, map_crop[0].shape, f'Dimensions failed at ego pose index {i}')

def test_get_vector_map(self) -> None:
    """Tests the get vector map method"""
    xrange = (-60, 60)
    yrange = (-60, 60)
    db = get_test_nuplan_db()
    num_samples = 10
    selected_indices = random.sample(list(range(len(db.ego_pose))), num_samples)
    ego_pose_list = db.ego_pose
    for i in selected_indices:
        current_ego_pose = ego_pose_list[i]
        if current_ego_pose.lidar_pc is None:
            continue
        result = current_ego_pose.get_vector_map(db.maps_db, xrange, yrange)
        self.assertIsNotNone(result)

class TestNuPlanDB(unittest.TestCase):
    """Test main nuPlan database class."""

    def setUp(self) -> None:
        """Set up test case."""
        self.db = get_test_nuplan_db()
        self.db.add_ref()

    def test_pickle(self) -> None:
        """Test dumping and loading the object through pickle."""
        db_binary = pickle.dumps(self.db)
        re_db: NuPlanDB = pickle.loads(db_binary)
        self.assertEqual(self.db.data_root, re_db.data_root)
        self.assertEqual(self.db.name, re_db.name)
        self.assertEqual(self.db._verbose, re_db._verbose)

    def test_table_getters(self) -> None:
        """Test the table getters."""
        self.assertTrue(isinstance(self.db.category, Table))
        self.assertTrue(isinstance(self.db.camera, Table))
        self.assertTrue(isinstance(self.db.lidar, Table))
        self.assertTrue(isinstance(self.db.image, Table))
        self.assertTrue(isinstance(self.db.lidar_pc, Table))
        self.assertTrue(isinstance(self.db.lidar_box, Table))
        self.assertTrue(isinstance(self.db.track, Table))
        self.assertTrue(isinstance(self.db.scene, Table))
        self.assertTrue(isinstance(self.db.scenario_tag, Table))
        self.assertTrue(isinstance(self.db.traffic_light_status, Table))
        self.assertSetEqual(self.db.cam_channels, {'CAM_R2', 'CAM_R1', 'CAM_R0', 'CAM_F0', 'CAM_L2', 'CAM_L1', 'CAM_B0', 'CAM_L0'})
        self.assertSetEqual(self.db.lidar_channels, {'MergedPointCloud'})

    def test_nuplan_memory_usage(self) -> None:
        """
        Test that repeatedly creating and destroying nuplan DB objects does not cause memory leaks.
        """

        def spin_up_db() -> None:
            db = get_test_nuplan_db_nocache()
            db.remove_ref()
        starting_usage = 0
        ending_usage = 0
        num_iterations = 5
        hpy = guppy.hpy()
        hpy.setrelheap()
        for i in range(0, num_iterations, 1):
            spin_up_db()
            gc.collect()
            heap = hpy.heap()
            _ = heap.size
            if i == num_iterations - 2:
                starting_usage = heap.size
            if i == num_iterations - 1:
                ending_usage = heap.size
        memory_difference_in_mb = (ending_usage - starting_usage) / (1024 * 1024)
        max_allowable_growth_mb = max(0.1, 0.1 * starting_usage / (1024 * 1024))
        self.assertGreater(max_allowable_growth_mb, memory_difference_in_mb)

def setUp(self) -> None:
    """Set up test case."""
    self.db = get_test_nuplan_db()
    self.db.add_ref()

def spin_up_db() -> None:
    db = get_test_nuplan_db_nocache()
    db.remove_ref()

class TestRendering(unittest.TestCase):
    """Some of these tests don't assert anything, but they will fail if the rendering code throws an exception."""

    def setUp(self) -> None:
        """Set up"""
        self.db = get_test_nuplan_db()
        self.lidar_box = get_test_nuplan_lidar_box()
        self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

    def test_closest_image(self) -> None:
        """Tests the closest_image method"""
        result = lidar_pc_closest_image(self.lidar_pc)
        self.assertNotEqual(len(result), 0)

    def test_lidar_pc_render(self) -> None:
        """Test Lidar PC render."""
        self.lidar_pc.render(self.db)

    @patch('nuplan.database.nuplan_db_orm.rendering_utils.Axes.imshow', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.image.Image.load_as', autospec=True)
    def test_lidar_box_render_img_found(self, loadas_mock: Mock, axes_mock: Mock) -> None:
        """Test Lidar Box render when the image is found"""
        render_lidar_box(self.lidar_box, self.db)
        loadas_mock.assert_called_once()
        axes_mock.assert_called_once()

    @patch('nuplan.database.nuplan_db_orm.rendering_utils.box_in_image', autospec=True)
    def test_lidar_box_render_img_not_found(self, box_in_image_mock: Mock) -> None:
        """Test Lidar Box render in the event that the image is not found"""
        box_in_image_mock.return_value = False
        with self.assertRaises(AssertionError):
            render_lidar_box(self.lidar_box, self.db)

def setUp(self) -> None:
    """Set up"""
    self.db = get_test_nuplan_db()
    self.lidar_box = get_test_nuplan_lidar_box()
    self.lidar_pc = get_test_nuplan_lidarpc_with_blob()

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

def setUp(self) -> None:
    """
        Initializes a test Image
        """
    self.db = get_test_nuplan_db()
    self.image = get_test_nuplan_image()

class TestNuplan(unittest.TestCase):
    """Test Nuplan DB."""

    def test_nuplan(self) -> None:
        """
        Check whether the nuPlan DB can be loaded without errors.
        """
        db = get_test_nuplan_db()
        self.assertIsNotNone(db)

def test_nuplan(self) -> None:
    """
        Check whether the nuPlan DB can be loaded without errors.
        """
    db = get_test_nuplan_db()
    self.assertIsNotNone(db)

@lru_cache(maxsize=1)
def get_test_nuplan_db_wrapper() -> NuPlanDBWrapper:
    """Get a nuPlan DB wrapper object with default settings to be used in testing."""
    return get_test_nuplan_db_wrapper_nocache()

@lru_cache(maxsize=1)
def get_test_nuplan_db() -> NuPlanDB:
    """Get a nuPlan DB object with default settings to be used in testing."""
    return get_test_nuplan_db_nocache()

@lru_cache(maxsize=1)
def get_test_nuplan_camera() -> Camera:
    """Get a nuPlan camera object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.camera[DEFAULT_TEST_CAMERA_INDEX]

@lru_cache(maxsize=1)
def get_test_nuplan_egopose() -> EgoPose:
    """Get a nuPlan egopose object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.ego_pose[DEFAULT_TEST_EGO_POSE_INDEX]

@lru_cache(maxsize=1)
def get_test_nuplan_lidarpc(index: Union[int, str]=DEFAULT_TEST_LIDAR_PC_INDEX) -> LidarPc:
    """Get a nuPlan lidarpc object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.lidar_pc[index]

@lru_cache(maxsize=1)
def get_test_nuplan_lidarpc_with_blob() -> LidarPc:
    """Get a nuPlan lidarpc object with blob with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.lidar_pc[DEFAULT_TEST_LIDAR_PC_WITH_BLOB_TOKEN]

@lru_cache(maxsize=1)
def get_test_nuplan_image() -> Image:
    """Get a nuPlan image object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.image[DEFAULT_TEST_IMAGE_WITH_BLOB_TOKEN]

@lru_cache(maxsize=1)
def get_test_nuplan_lidar() -> Lidar:
    """Get a nuPlan lidar object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.lidar[DEFAULT_TEST_LIDAR_INDEX]

@lru_cache(maxsize=1)
def get_test_nuplan_lidar_box() -> LidarBox:
    """Get a nuPlan lidar box object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.lidar_box[DEFAULT_TEST_LIDAR_BOX_INDEX]

@lru_cache(maxsize=1)
def get_test_nuplan_lidar_box_vehicle() -> LidarBox:
    """Get a nuPlan lidar box object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.lidar_box[DEFAULT_TEST_LIDAR_BOX_INDEX_VEHICLE]

@lru_cache(maxsize=1)
def get_test_nuplan_track() -> Track:
    """Get a nuPlan track object with default settings to be used in testing."""
    db = get_test_nuplan_db()
    return db.track[DEFAULT_TEST_TRACK_INDEX]

@lru_cache(maxsize=1)
def get_test_maps_db() -> IMapsDB:
    """Get a nuPlan maps DB object with default settings to be used in testing."""
    return GPKGMapsDB(map_version=NUPLAN_MAP_VERSION, map_root=NUPLAN_MAPS_ROOT)

@functools.lru_cache(maxsize=None)
@static_vars(id=-1)
def get_unique_incremental_track_id(_: str) -> int:
    """
    Generate a unique ID (increasing number)
    :return int Unique ID
    """
    get_unique_incremental_track_id.id += 1
    return get_unique_incremental_track_id.id

class TestFunctionValidation(unittest.TestCase):
    """
    A class to test that the function validation method works properly.
    """

    def test_assert_functions_swappable(self) -> None:
        """
        Tests that the assert_functions_swappable method functions properly.
        """
        test_methods: List[MethodSpecification] = [MethodSpecification(name='_none_none', input_args={}, kw_only_args=None, return_type='None'), MethodSpecification(name='_int_none', input_args={'x': 'int'}, kw_only_args=None, return_type='None'), MethodSpecification(name='_intd1_none', input_args={'x': 'int = 1'}, kw_only_args=None, return_type='None'), MethodSpecification(name='_intk1_none', input_args={}, kw_only_args={'x': 'int = 1'}, return_type='None'), MethodSpecification(name='_int_int', input_args={'x': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_intd1_int', input_args={'x': 'int = 1'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_intd2_int', input_args={'x': 'int = 2'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_float', input_args={'x': 'int'}, kw_only_args=None, return_type='float'), MethodSpecification(name='_float_int', input_args={'x': 'float'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_list_int_int', input_args={'x': 'List[int]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_list_float_int', input_args={'x': 'List[float]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_int_int', input_args={'x': 'int', 'y': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_intk1_int', input_args={'x': 'int'}, kw_only_args={'y': 'int = 1'}, return_type='int'), MethodSpecification(name='_int_intk2_int', input_args={'x': 'int'}, kw_only_args={'y': 'int = 2'}, return_type='int'), MethodSpecification(name='_float_int_int', input_args={'x': 'float', 'y': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_ndarray_float32_int', input_args={'x': 'npt.NDArray[np.float32]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_ndarray_float64_int', input_args={'x': 'npt.NDArray[np.float64]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_duplicate_of_int_int', input_args={'x': 'int'}, kw_only_args=None, return_type='int')]
        for spec in test_methods:
            method_text = _get_method_text(spec)
            exec(method_text)
        for first_func_definition in test_methods:
            for second_func_definition in test_methods:
                first_func_name = first_func_definition.name
                second_func_name = second_func_definition.name
                first_func = locals()[first_func_name]
                second_func = locals()[second_func_name]
                if first_func_name.replace('_duplicate_of', '') != second_func_name.replace('_duplicate_of', ''):
                    with self.assertRaises(TypeError):
                        assert_functions_swappable(first_func, second_func)
                else:
                    assert_functions_swappable(first_func, second_func)

def test_assert_functions_swappable(self) -> None:
    """
        Tests that the assert_functions_swappable method functions properly.
        """
    test_methods: List[MethodSpecification] = [MethodSpecification(name='_none_none', input_args={}, kw_only_args=None, return_type='None'), MethodSpecification(name='_int_none', input_args={'x': 'int'}, kw_only_args=None, return_type='None'), MethodSpecification(name='_intd1_none', input_args={'x': 'int = 1'}, kw_only_args=None, return_type='None'), MethodSpecification(name='_intk1_none', input_args={}, kw_only_args={'x': 'int = 1'}, return_type='None'), MethodSpecification(name='_int_int', input_args={'x': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_intd1_int', input_args={'x': 'int = 1'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_intd2_int', input_args={'x': 'int = 2'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_float', input_args={'x': 'int'}, kw_only_args=None, return_type='float'), MethodSpecification(name='_float_int', input_args={'x': 'float'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_list_int_int', input_args={'x': 'List[int]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_list_float_int', input_args={'x': 'List[float]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_int_int', input_args={'x': 'int', 'y': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_int_intk1_int', input_args={'x': 'int'}, kw_only_args={'y': 'int = 1'}, return_type='int'), MethodSpecification(name='_int_intk2_int', input_args={'x': 'int'}, kw_only_args={'y': 'int = 2'}, return_type='int'), MethodSpecification(name='_float_int_int', input_args={'x': 'float', 'y': 'int'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_ndarray_float32_int', input_args={'x': 'npt.NDArray[np.float32]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_ndarray_float64_int', input_args={'x': 'npt.NDArray[np.float64]'}, kw_only_args=None, return_type='int'), MethodSpecification(name='_duplicate_of_int_int', input_args={'x': 'int'}, kw_only_args=None, return_type='int')]
    for spec in test_methods:
        method_text = _get_method_text(spec)
        exec(method_text)
    for first_func_definition in test_methods:
        for second_func_definition in test_methods:
            first_func_name = first_func_definition.name
            second_func_name = second_func_definition.name
            first_func = locals()[first_func_name]
            second_func = locals()[second_func_name]
            if first_func_name.replace('_duplicate_of', '') != second_func_name.replace('_duplicate_of', ''):
                with self.assertRaises(TypeError):
                    assert_functions_swappable(first_func, second_func)
            else:
                assert_functions_swappable(first_func, second_func)

def assert_class_properly_implements_interface(interface_class_type: Type[Any], derived_class_type: Type[Any]) -> None:
    """
    Asserts that a particular class implements a specified interface.
    This is done with the following checks:
        * Makes sure that derived_class is a subclass of interface_class.
        * Checks that all abstract public methods in interface are in derived.
        * Checks that the function signatures in derived class are swappable with abstract methods in interface.
    If the checks fail, a TypeError is raised.
    :param interface_class_type: The type of the interface class.
    :param derived_class_type: The type of the derived class.
    """
    _assert_derived_is_child_of_base(interface_class_type, derived_class_type)
    interface_abstract_methods = _get_public_methods(interface_class_type, only_abstract=True)
    derived_public_methods = _get_public_methods(derived_class_type, only_abstract=False)
    _assert_abstract_methods_present(interface_class_type, derived_class_type, {k for k in interface_abstract_methods.keys()}, {k for k in derived_public_methods.keys()})
    for key in interface_abstract_methods:
        interface_method = interface_abstract_methods[key]
        derived_method = derived_public_methods[key]
        assert_functions_swappable(interface_method, derived_method)

@contextlib.contextmanager
def patch_with_validation(method_to_patch: str, patch_function: Callable[..., Any], override_function: Optional[Callable[..., Any]]=None, **kwargs: Any) -> Generator[Callable[..., Any], None, None]:
    """
    Wraps unittest.mock.patch, injecting the function signature validation.
    :param method_to_patch: The dot-string method to patch (e.g. "my.python.file.mymethod")
    :param patch_function: The function to use for the patch.
    :param override_function: The function to use for validation. If not provided, `method_to_patch` will be imported and used.
      The intent is to provide an escape hatch in the instance automatic lookup via dot-string for method_to_patch does not work.
    :param kwargs: The additional keyword arguments passed to unittest.mock.patch.
    """
    if override_function is None:
        override_function = _get_method_from_import(method_to_patch)
    assert_functions_swappable(override_function, patch_function)
    with unittest.mock.patch(method_to_patch, patch_function, **kwargs) as mock_obj:
        yield mock_obj

@pytest.fixture()
def scene(nuplan_test: Any, request: pytest.FixtureRequest) -> Generator[Any, Any, Any]:
    """Depending on the test type, skips, fails or yields the data for the test."""
    test_type = instances.REGISTRY.get_type(request.node.nodeid)
    if test_type == 'invalid':
        pytest.fail('Invalid Test')
    elif test_type in ('hardcoded', 'filebased'):
        yield instances.REGISTRY.get_data(request.node.nodeid)
    elif test_type == 'newable':
        pytest.skip()

class NuPlanMapFactory(AbstractMapFactory):
    """
    Factory creating maps from an IMapsDB interface.
    """

    def __init__(self, maps_db: IMapsDB):
        """
        :param maps_db: An IMapsDB instance e.g. GPKGMapsDB.
        """
        self._maps_db = maps_db

    def __reduce__(self) -> Tuple[Type[NuPlanMapFactory], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._maps_db,))

    def build_map_from_name(self, map_name: str) -> NuPlanMap:
        """
        Builds a map interface given a map name.
        Examples of names: 'sg-one-north', 'us-ma-boston', 'us-nv-las-vegas-strip', 'us-pa-pittsburgh-hazelwood'
        :param map_name: Name of the map.
        :return: The constructed map interface.
        """
        return NuPlanMap(self._maps_db, map_name.replace('.gpkg', ''))

def build_map_from_name(self, map_name: str) -> NuPlanMap:
    """
        Builds a map interface given a map name.
        Examples of names: 'sg-one-north', 'us-ma-boston', 'us-nv-las-vegas-strip', 'us-pa-pittsburgh-hazelwood'
        :param map_name: Name of the map.
        :return: The constructed map interface.
        """
    return NuPlanMap(self._maps_db, map_name.replace('.gpkg', ''))

@lru_cache(maxsize=2)
def get_maps_db(map_root: str, map_version: str) -> GPKGMapsDB:
    """
    Get a maps_db from disk.
    :param map_root: The root folder for the map data.
    :param map_version: The version of the map to load.
    :return; The loaded MapsDB object.
    """
    return GPKGMapsDB(map_root=map_root, map_version=map_version)

@lru_cache(maxsize=32)
def get_maps_api(map_root: str, map_version: str, map_name: str) -> NuPlanMap:
    """
    Get a NuPlanMap object corresponding to a particular set of parameters.
    :param map_root: The root folder for the map data.
    :param map_version: The map version to load.
    :param map_name: The map name to load.
    :return: The loaded NuPlanMap object.
    """
    maps_db = get_maps_db(map_root, map_version)
    return NuPlanMap(maps_db, map_name.replace('.gpkg', ''))

class NuPlanLaneConnector(LaneConnector):
    """
    NuPlanMap implementation of LaneConnector.
    """

    def __init__(self, lane_connector_id: str, lanes_df: VectorLayer, lane_connectors_df: VectorLayer, baseline_paths_df: VectorLayer, boundaries_df: VectorLayer, stop_lines_df: VectorLayer, lane_connector_polygon_df: VectorLayer, map_data: AbstractMap):
        """
        Constructor of NuPlanLaneConnector.
        :param lane_connector_id: unique identifier of the lane connector.
        :param lanes_df: the geopandas GeoDataframe that contains all lanes in the map.
        :param lane_connectors_df: the geopandas GeoDataframe that contains all lane connectors in the map.
        :param baseline_paths_df: the geopandas GeoDataframe that contains all baselines in the map.
        :param boundaries_df: the geopandas GeoDataframe that contains all boundaries in the map.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        :param lane_connector_polygon_df: the geopandas GeoDataframe that contains polygons for lane connectors.
        """
        super().__init__(lane_connector_id)
        self._lanes_df = lanes_df
        self._lane_connectors_df = lane_connectors_df
        self._baseline_paths_df = baseline_paths_df
        self._boundaries_df = boundaries_df
        self._stop_lines_df = stop_lines_df
        self._lane_connector_polygon_df = lane_connector_polygon_df
        self._lane_connector = None
        self._map_data = map_data

    @cached_property
    def incoming_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        incoming_lane_id = self._get_lane_connector()['exit_lane_fid']
        return [lane.NuPlanLane(str(incoming_lane_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data)]

    @cached_property
    def outgoing_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        outgoing_lane_id = self._get_lane_connector()['entry_lane_fid']
        return [lane.NuPlanLane(str(outgoing_lane_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data)]

    @cached_property
    def parallel_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def baseline_path(self) -> PolylineMapObject:
        """Inherited from superclass."""
        return NuPlanPolylineMapObject(get_row_with_value(self._baseline_paths_df, 'lane_connector_fid', self.id))

    @cached_property
    def left_boundary(self) -> PolylineMapObject:
        """Inherited from superclass."""
        boundary_fid = get_row_with_value(self._lane_connector_polygon_df, 'lane_connector_fid', self.id)['left_boundary_fid']
        return NuPlanPolylineMapObject(get_row_with_value(self._boundaries_df, 'fid', str(boundary_fid)))

    @cached_property
    def right_boundary(self) -> PolylineMapObject:
        """Inherited from superclass."""
        boundary_fid = get_row_with_value(self._lane_connector_polygon_df, 'lane_connector_fid', self.id)['right_boundary_fid']
        return NuPlanPolylineMapObject(get_row_with_value(self._boundaries_df, 'fid', str(boundary_fid)))

    @cached_property
    def speed_limit_mps(self) -> Optional[float]:
        """Inherited from superclass."""
        speed_limit = self._get_lane_connector()['speed_limit_mps']
        is_valid = speed_limit == speed_limit and speed_limit is not None
        return float(speed_limit) if is_valid else None

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass. Note, the polygon is inferred from the baseline."""
        lane_connector_polygon_row = get_row_with_value(self._lane_connector_polygon_df, 'lane_connector_fid', self.id)
        return lane_connector_polygon_row.geometry

    def is_left_of(self, other: LaneConnector) -> bool:
        """Inherited from superclass."""
        return False

    def is_right_of(self, other: LaneConnector) -> bool:
        """Inherited from superclass."""
        return False

    def get_roadblock_id(self) -> str:
        """Inherited from superclass."""
        return str(self._get_lane_connector()['lane_group_connector_fid'])

    @cached_property
    def parent(self) -> RoadBlockGraphEdgeMapObject:
        """Inherited from superclass"""
        return self._map_data.get_map_object(self.get_roadblock_id(), SemanticMapLayer.ROADBLOCK_CONNECTOR)

    def has_traffic_lights(self) -> bool:
        """Inherited from superclass."""
        return bool(self._get_lane_connector()['traffic_light_stop_line_fids'])

    @cached_property
    def stop_lines(self) -> List[StopLine]:
        """Inherited from superclass."""
        stop_line_ids = self._get_lane_connector()['traffic_light_stop_line_fids']
        stop_line_ids = cast(List[str], stop_line_ids.replace(' ', '').split(','))
        candidate_stop_lines = [NuPlanStopLine(id_, self._stop_lines_df) for id_ in stop_line_ids if id_]
        if not candidate_stop_lines:
            return []
        stop_lines = [stop_line for stop_line in candidate_stop_lines if stop_line.polygon.intersects(self.baseline_path.linestring)]
        if stop_lines:
            return stop_lines

        def distance_to_stop_line(stop_line: StopLine) -> float:
            """
            Calculates the distance between the first point of the lane connector's baseline path
            :param stop_line: The stop line to calculate the distance to.
            :return: [m] The distance between first point points of the lane connector to the stop_line polygon.
            """
            start = Point(self.baseline_path.linestring.coords[0])
            return float(start.distance(stop_line.polygon))
        distances = [distance_to_stop_line(stop_line) for stop_line in candidate_stop_lines]
        return [candidate_stop_lines[np.argmin(distances)]]

    def turn_type(self) -> LaneConnectorType:
        """Inherited from superclass"""
        raise NotImplementedError

    def get_width_left_right(self, point: Point2D, include_outside: bool=False) -> Tuple[Optional[float], Optional[float]]:
        """Inherited from superclass."""
        raise NotImplementedError

    def oriented_distance(self, point: Point2D) -> float:
        """Inherited from superclass"""
        raise NotImplementedError

    def _get_lane_connector(self) -> pd.Series:
        """
        Gets the series from the lane dataframe containing lane's id.
        :return: the respective series from the lanes dataframe.
        """
        if self._lane_connector is None:
            self._lane_connector = get_row_with_value(self._lane_connectors_df, 'fid', self.id)
        return self._lane_connector

@cached_property
def stop_lines(self) -> List[StopLine]:
    """Inherited from superclass."""
    stop_line_ids = self._get_lane_connector()['traffic_light_stop_line_fids']
    stop_line_ids = cast(List[str], stop_line_ids.replace(' ', '').split(','))
    candidate_stop_lines = [NuPlanStopLine(id_, self._stop_lines_df) for id_ in stop_line_ids if id_]
    if not candidate_stop_lines:
        return []
    stop_lines = [stop_line for stop_line in candidate_stop_lines if stop_line.polygon.intersects(self.baseline_path.linestring)]
    if stop_lines:
        return stop_lines

    def distance_to_stop_line(stop_line: StopLine) -> float:
        """
            Calculates the distance between the first point of the lane connector's baseline path
            :param stop_line: The stop line to calculate the distance to.
            :return: [m] The distance between first point points of the lane connector to the stop_line polygon.
            """
        start = Point(self.baseline_path.linestring.coords[0])
        return float(start.distance(stop_line.polygon))
    distances = [distance_to_stop_line(stop_line) for stop_line in candidate_stop_lines]
    return [candidate_stop_lines[np.argmin(distances)]]

@pytest.fixture()
def map_factory() -> NuPlanMapFactory:
    """Fixture loading ta returning a map factory"""
    maps_db = get_test_maps_db()
    return NuPlanMapFactory(maps_db)

class OrientedBox:
    """Represents the physical space occupied by agents on the plane."""

    def __init__(self, center: StateSE2, length: float, width: float, height: float):
        """
        :param center: The pose of the geometrical center of the box
        :param length: The length of the OrientedBox
        :param width: The width of the OrientedBox
        :param height: The height of the OrientedBox
        """
        self._center = center
        self._length = length
        self._width = width
        self._height = height

    @property
    def dimensions(self) -> Dimension:
        """
        :return: Dimensions of this oriented box in meters
        """
        return Dimension(length=self.length, width=self.width, height=self.height)

    @lru_cache()
    def corner(self, point: OrientedBoxPointType) -> Point2D:
        """
        Extract a point of oriented box
        :param point: which point you want to query
        :return: Coordinates of a point on oriented box.
        """
        if point == OrientedBoxPointType.FRONT_LEFT:
            return translate_longitudinally_and_laterally(self.center, self.half_length, self.half_width).point
        elif point == OrientedBoxPointType.FRONT_RIGHT:
            return translate_longitudinally_and_laterally(self.center, self.half_length, -self.half_width).point
        elif point == OrientedBoxPointType.REAR_LEFT:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, self.half_width).point
        elif point == OrientedBoxPointType.REAR_RIGHT:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, -self.half_width).point
        elif point == OrientedBoxPointType.CENTER:
            return self._center.point
        elif point == OrientedBoxPointType.FRONT_BUMPER:
            return translate_longitudinally_and_laterally(self.center, self.half_length, 0.0).point
        elif point == OrientedBoxPointType.REAR_BUMPER:
            return translate_longitudinally_and_laterally(self.center, -self.half_length, 0.0).point
        elif point == OrientedBoxPointType.LEFT:
            return translate_longitudinally_and_laterally(self.center, 0, self.half_width).point
        elif point == OrientedBoxPointType.RIGHT:
            return translate_longitudinally_and_laterally(self.center, 0, -self.half_width).point
        else:
            raise RuntimeError(f'Unknown point: {point}!')

    def all_corners(self) -> List[Point2D]:
        """
        Return 4 corners of oriented box (FL, RL, RR, FR)
        :return: all corners of a oriented box in a list
        """
        return [self.corner(OrientedBoxPointType.FRONT_LEFT), self.corner(OrientedBoxPointType.REAR_LEFT), self.corner(OrientedBoxPointType.REAR_RIGHT), self.corner(OrientedBoxPointType.FRONT_RIGHT)]

    @property
    def width(self) -> float:
        """
        Returns the width of the OrientedBox
        :return: The width of the OrientedBox
        """
        return self._width

    @property
    def half_width(self) -> float:
        """
        Returns the half width of the OrientedBox
        :return: The half width of the OrientedBox
        """
        return self._width / 2.0

    @property
    def length(self) -> float:
        """
        Returns the length of the OrientedBox
        :return: The length of the OrientedBox
        """
        return self._length

    @property
    def half_length(self) -> float:
        """
        Returns the half length of the OrientedBox
        :return: The half length of the OrientedBox
        """
        return self._length / 2.0

    @property
    def height(self) -> float:
        """
        Returns the height of the OrientedBox
        :return: The height of the OrientedBox
        """
        return self._height

    @property
    def half_height(self) -> float:
        """
        Returns the half height of the OrientedBox
        :return: The half height of the OrientedBox
        """
        return self._height / 2.0

    @property
    def center(self) -> StateSE2:
        """
        Returns the pose of the center of the OrientedBox
        :return: The pose of the center
        """
        return self._center

    @cached_property
    def geometry(self) -> Polygon:
        """
        Returns the Polygon describing the OrientedBox, if not done yet it will build it lazily.
        :return: The Polygon of the OrientedBox
        """
        corners = [tuple(corner) for corner in self.all_corners()]
        return Polygon(corners)

    def __hash__(self) -> int:
        """
        :return: hash for this object
        """
        return hash((self.center, self.width, self.height, self.length))

    def __eq__(self, other: object) -> bool:
        """
        Compare two oriented boxes
        :param other: object
        :return: true if other and self is equal
        """
        if not isinstance(other, OrientedBox):
            return NotImplemented
        return math.isclose(self.width, other.width) and math.isclose(self.height, other.height) and math.isclose(self.length, other.length) and (self.center == other.center)

    @classmethod
    def from_new_pose(cls, box: OrientedBox, pose: StateSE2) -> OrientedBox:
        """
        Initializer that create the same oriented box in a different pose.
        :param box: A sample box
        :param pose: The new pose
        :return: A new OrientedBox
        """
        return cls(pose, box.length, box.width, box.height)

@lru_cache()
def corner(self, point: OrientedBoxPointType) -> Point2D:
    """
        Extract a point of oriented box
        :param point: which point you want to query
        :return: Coordinates of a point on oriented box.
        """
    if point == OrientedBoxPointType.FRONT_LEFT:
        return translate_longitudinally_and_laterally(self.center, self.half_length, self.half_width).point
    elif point == OrientedBoxPointType.FRONT_RIGHT:
        return translate_longitudinally_and_laterally(self.center, self.half_length, -self.half_width).point
    elif point == OrientedBoxPointType.REAR_LEFT:
        return translate_longitudinally_and_laterally(self.center, -self.half_length, self.half_width).point
    elif point == OrientedBoxPointType.REAR_RIGHT:
        return translate_longitudinally_and_laterally(self.center, -self.half_length, -self.half_width).point
    elif point == OrientedBoxPointType.CENTER:
        return self._center.point
    elif point == OrientedBoxPointType.FRONT_BUMPER:
        return translate_longitudinally_and_laterally(self.center, self.half_length, 0.0).point
    elif point == OrientedBoxPointType.REAR_BUMPER:
        return translate_longitudinally_and_laterally(self.center, -self.half_length, 0.0).point
    elif point == OrientedBoxPointType.LEFT:
        return translate_longitudinally_and_laterally(self.center, 0, self.half_width).point
    elif point == OrientedBoxPointType.RIGHT:
        return translate_longitudinally_and_laterally(self.center, 0, -self.half_width).point
    else:
        raise RuntimeError(f'Unknown point: {point}!')

def get_front_left_corner(center_pose: StateSE2, half_length: float, half_width: float) -> Point2D:
    """
    Compute the position of the front left corner given a center pose and dimensions
    :param center_pose: SE2 pose of the vehicle center to be translated a vehicle corner
    :param half_length: [m] half length of a vehicle's footprint
    :param half_width: [m] half width of a vehicle's footprint
    :return Point2D translated coordinates
    """
    return translate_longitudinally_and_laterally(center_pose, half_length, half_width).point

def get_front_right_corner(center_pose: StateSE2, half_length: float, half_width: float) -> Point2D:
    """
    Compute the position of the front right corner given a center pose and dimensions
    :param center_pose: SE2 pose of the vehicle center to be translated a vehicle corner
    :param half_length: [m] half length of a vehicle's footprint
    :param half_width: [m] half width of a vehicle's footprint
    :return Point2D translated coordinates
    """
    return translate_longitudinally_and_laterally(center_pose, half_length, -half_width).point

def get_rear_left_corner(center_pose: StateSE2, half_length: float, half_width: float) -> Point2D:
    """
    Compute the position of the rear left corner given a center pose and dimensions
    :param center_pose: SE2 pose of the vehicle center to be translated a vehicle corner
    :param half_length: [m] half length of a vehicle's footprint
    :param half_width: [m] half width of a vehicle's footprint
    :return Point2D translated coordinates
    """
    return translate_longitudinally_and_laterally(center_pose, -half_length, half_width).point

def get_rear_right_corner(center_pose: StateSE2, half_length: float, half_width: float) -> Point2D:
    """
    Compute the position of the rear right corner given a center pose and dimensions
    :param center_pose: SE2 pose of the vehicle center to be translated a vehicle corner
    :param half_length: [m] half length of a vehicle's footprint
    :param half_width: [m] half width of a vehicle's footprint
    :return Point2D translated coordinates
    """
    return translate_longitudinally_and_laterally(center_pose, -half_length, -half_width).point

class MockPoint(InterpolatableState, ABC):
    """Mock point for trajectory tests."""

    @staticmethod
    @static_vars(calls=[])
    def from_split_state(split_state: Mock) -> str:
        """Mock from_split_state."""
        MockPoint.from_split_state.calls.append(split_state)
        return 'foo'

    @staticmethod
    def reset_calls() -> None:
        """Resets spy."""
        MockPoint.from_split_state.calls = []

@staticmethod
@static_vars(calls=[])
def from_split_state(split_state: Mock) -> str:
    """Mock from_split_state."""
    MockPoint.from_split_state.calls.append(split_state)
    return 'foo'

def _fill_in_abstract_scenario_mock_parameters(scenario_mock: Mock, initial_ego_center_pose: StateSE2, initial_timestamp: int, traffic_light_statuses: List[TrafficLightStatusData], route_roadblock_ids: List[str]) -> None:
    """
    Helper function to configure a scenario mock with required parameters for VectorMapFeatureBuilder.
    :param scenario_mock: The AbstractScenario mock that we should update.
    :param initial_ego_center_pose: Ego vehicle center pose used to construct the scenario initial_ego_state.
    :param initial_timestamp: Initial timestamp corresponding to initial_ego_state for the test scenario.
    :param traffic_light_statuses: A list of TL statuses used to determine the traffic light scene at the 0th iteration.
    :param route_roadblock_ids: The route roadblock ids for the scenario.
    """
    scenario_mock.initial_ego_state = get_sample_ego_state(center=initial_ego_center_pose, time_us=initial_timestamp)
    scenario_mock.get_route_roadblock_ids.return_value = route_roadblock_ids

    def _get_traffic_light_status_at_iteration_patch(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """A patch to populate traffic light states for the 0th iteration only."""
        if iteration != 0:
            raise ValueError('We expect the vector map builder to only use the 0th iteration TL states.')
        yield from traffic_light_statuses
    assert_functions_swappable(AbstractScenario.get_traffic_light_status_at_iteration, _get_traffic_light_status_at_iteration_patch)
    scenario_mock.get_traffic_light_status_at_iteration.side_effect = _get_traffic_light_status_at_iteration_patch

class SimulationTile:
    """Scenario simulation tile for visualization."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, vehicle_parameters: VehicleParameters, map_factory: AbstractMapFactory, period_milliseconds: int=5000, radius: float=300.0, async_rendering: bool=True, frame_rate_cap_hz: int=60):
        """
        Scenario simulation tile.
        :param doc: Bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        :param vehicle_parameters: Ego pose parameters.
        :param map_factory: Map factory for building maps.
        :param period_milliseconds: Milliseconds to update the tile.
        :param radius: Map radius.
        :param async_rendering: When true, will use threads to render asynchronously.
        :param frame_rate_cap_hz: Maximum frames to render per second. Internally this value is capped at 60.
        """
        self._doc = doc
        self._vehicle_parameters = vehicle_parameters
        self._map_factory = map_factory
        self._experiment_file_data = experiment_file_data
        self._period_milliseconds = period_milliseconds
        self._radius = radius
        self._selected_scenario_keys: List[SimulationScenarioKey] = []
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._maps: Dict[str, AbstractMap] = {}
        self._figures: List[SimulationFigure] = []
        self._nearest_vector_map: Dict[SemanticMapLayer, List[MapObject]] = {}
        self._async_rendering = async_rendering
        self._plot_render_queue: Optional[Tuple[SimulationFigure, int]] = None
        self._doc.add_periodic_callback(self._periodic_callback, period_milliseconds=1000)
        self._last_frame_time = time.time()
        self._current_frame_index = 0
        self._last_frame_index = 0
        self._playback_callback_handle: Optional[PeriodicCallback] = None
        if frame_rate_cap_hz < 1 or frame_rate_cap_hz > 60:
            raise ValueError('frame_rate_cap_hz should be between 1 and 60')
        self._minimum_frame_time_seconds = 1.0 / float(frame_rate_cap_hz)
        logger.info('Minimum frame time=%4.3f s', self._minimum_frame_time_seconds)

    @property
    def get_figure_data(self) -> List[SimulationFigure]:
        """Return figure data."""
        return self._figures

    @property
    def is_in_playback(self) -> bool:
        """Returns True if we're currently rendering a playback of a figure."""
        return self._playback_callback_handle is not None

    def _on_mouse_move(self, event: PointEvent, figure_index: int) -> None:
        """
        Event when mouse moving in a figure.
        :param event: Point event.
        :param figure_index: Figure index where the mouse is moving.
        """
        main_figure = self._figures[figure_index]
        main_figure.x_y_coordinate_title.text = f'x [m]: {np.round(event.x, simulation_tile_style['decimal_points'])}, y [m]: {np.round(event.y, simulation_tile_style['decimal_points'])}'

    def _create_frame_control_button(self, button_config: ScenarioTabFrameButtonConfig, click_callback: EventCallback, figure_index: int) -> Button:
        """
        Helper function to create a frame control button (prev, play, etc.) based on the provided config.
        :param button_config: Configuration object for the frame control button.
        :param click_callback: Button click event callback that will be registered to the created button.
        :param figure_index: The figure index to be passed to the button's click event callback.
        :return: The created Bokeh Button instance.
        """
        button_instance = Button(label=button_config.label, margin=button_config.margin, css_classes=button_config.css_classes, width=button_config.width)
        button_instance.on_click(partial(click_callback, figure_index=figure_index))
        return button_instance

    def _create_initial_figure(self, figure_index: int, figure_sizes: List[int], backend: Optional[str]='webgl') -> SimulationFigure:
        """
        Create an initial Bokeh figure.
        :param figure_index: Figure index.
        :param figure_sizes: width and height in pixels.
        :param backend: Bokeh figure backend.
        :return: A Bokeh figure.
        """
        selected_scenario_key = self._selected_scenario_keys[figure_index]
        experiment_path = Path(self._experiment_file_data.file_paths[selected_scenario_key.nuboard_file_index].metric_main_path)
        planner_name = selected_scenario_key.planner_name
        presented_planner_name = planner_name + f' ({experiment_path.stem})'
        simulation_figure = Figure(x_range=(-self._radius, self._radius), y_range=(-self._radius, self._radius), width=figure_sizes[0], height=figure_sizes[1], title=f'{presented_planner_name}', tools=['pan', 'wheel_zoom', 'save', 'reset'], match_aspect=True, active_scroll='wheel_zoom', margin=simulation_tile_style['figure_margins'], background_fill_color=simulation_tile_style['background_color'], output_backend=backend)
        simulation_figure.on_event('mousemove', partial(self._on_mouse_move, figure_index=figure_index))
        simulation_figure.axis.visible = False
        simulation_figure.xgrid.visible = False
        simulation_figure.ygrid.visible = False
        simulation_figure.title.text_font_size = simulation_tile_style['figure_title_text_font_size']
        x_y_coordinate_title = Title(text='x [m]: , y [m]: ')
        simulation_figure.add_layout(x_y_coordinate_title, 'below')
        slider = Slider(start=0, end=1, value=0, step=1, title='Frame', margin=simulation_tile_style['slider_margins'], css_classes=['scenario-frame-slider'])
        slider.on_change('value', partial(self._slider_on_change, figure_index=figure_index))
        video_button = Button(label='Render video', margin=simulation_tile_style['video_button_margins'], css_classes=['scenario-video-button'])
        video_button.on_click(partial(self._video_button_on_click, figure_index=figure_index))
        first_button = self._create_frame_control_button(first_button_config, self._first_button_on_click, figure_index)
        prev_button = self._create_frame_control_button(prev_button_config, self._prev_button_on_click, figure_index)
        play_button = self._create_frame_control_button(play_button_config, self._play_button_on_click, figure_index)
        next_button = self._create_frame_control_button(next_button_config, self._next_button_on_click, figure_index)
        last_button = self._create_frame_control_button(last_button_config, self._last_button_on_click, figure_index)
        assert len(selected_scenario_key.files) == 1, 'Expected one file containing the serialized SimulationLog.'
        simulation_file = next(iter(selected_scenario_key.files))
        simulation_log = SimulationLog.load_data(simulation_file)
        simulation_figure_data = SimulationFigure(figure=simulation_figure, file_path_index=selected_scenario_key.nuboard_file_index, figure_title_name=presented_planner_name, slider=slider, video_button=video_button, first_button=first_button, prev_button=prev_button, play_button=play_button, next_button=next_button, last_button=last_button, vehicle_parameters=self._vehicle_parameters, planner_name=planner_name, scenario=simulation_log.scenario, simulation_history=simulation_log.simulation_history, x_y_coordinate_title=x_y_coordinate_title)
        return simulation_figure_data

    def _map_api(self, map_name: str) -> AbstractMap:
        """
        Get a map api.
        :param map_name: Map name.
        :return Map api.
        """
        if map_name not in self._maps:
            self._maps[map_name] = self._map_factory.build_map_from_name(map_name)
        return self._maps[map_name]

    def init_simulations(self, figure_sizes: List[int]) -> None:
        """
        Initialization of the visualization of simulation panel.
        :param figure_sizes: Width and height in pixels.
        """
        self._figures = []
        for figure_index in range(len(self._selected_scenario_keys)):
            simulation_figure = self._create_initial_figure(figure_index=figure_index, figure_sizes=figure_sizes)
            self._figures.append(simulation_figure)

    @property
    def figures(self) -> List[SimulationFigure]:
        """
        Access bokeh figures.
        :return A list of bokeh figures.
        """
        return self._figures

    def _render_simulation_layouts(self) -> List[SimulationData]:
        """
        Render simulation layouts.
        :return: A list of columns or rows.
        """
        grid_layouts: List[SimulationData] = []
        for simulation_figure in self.figures:
            grid_layouts.append(SimulationData(planner_name=simulation_figure.planner_name, simulation_figure=simulation_figure, plot=gridplot([[simulation_figure.slider], [row([simulation_figure.first_button, simulation_figure.prev_button, simulation_figure.play_button, simulation_figure.next_button, simulation_figure.last_button])], [simulation_figure.figure], [simulation_figure.video_button]], toolbar_location='left')))
        return grid_layouts

    def render_simulation_tiles(self, selected_scenario_keys: List[SimulationScenarioKey], figure_sizes: List[int]=simulation_tile_style['figure_sizes'], hidden_glyph_names: Optional[List[str]]=None) -> List[SimulationData]:
        """
        Render simulation tiles.
        :param selected_scenario_keys: A list of selected scenario keys.
        :param figure_sizes: Width and height in pixels.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        :return A list of bokeh layouts.
        """
        self._selected_scenario_keys = selected_scenario_keys
        self.init_simulations(figure_sizes=figure_sizes)
        for main_figure in tqdm(self._figures, desc='Rendering a scenario'):
            self._render_scenario(main_figure, hidden_glyph_names=hidden_glyph_names)
        layouts = self._render_simulation_layouts()
        return layouts

    @gen.coroutine
    @without_document_lock
    def _video_button_on_click(self, figure_index: int) -> None:
        """
        Callback to video button click event.
        Note that this callback in run on a background thread.
        :param figure_index: Figure index.
        """
        self._figures[figure_index].video_button.disabled = True
        self._figures[figure_index].video_button.label = 'Rendering video now...'
        self._executor.submit(self._video_button_next_tick, figure_index)

    def _reset_video_button(self, figure_index: int) -> None:
        """
        Reset a video button after exporting is done.
        :param figure_index: Figure index.
        """
        self.figures[figure_index].video_button.label = 'Render video'
        self.figures[figure_index].video_button.disabled = False

    def _update_video_button_label(self, figure_index: int, label: str) -> None:
        """
        Update a video button label to show progress when rendering a video.
        :param figure_index: Figure index.
        :param label: New video button text.
        """
        self.figures[figure_index].video_button.label = label

    def _video_button_next_tick(self, figure_index: int) -> None:
        """
        Synchronous callback to the video button on click event.
        :param figure_index: Figure index.
        """
        if not len(self._figures):
            return
        images = []
        scenario_key = self._selected_scenario_keys[figure_index]
        scenario_name = scenario_key.scenario_name
        scenario_type = scenario_key.scenario_type
        planner_name = scenario_key.planner_name
        video_name = scenario_type + '_' + planner_name + '_' + scenario_name + '.avi'
        nuboard_file_index = scenario_key.nuboard_file_index
        video_path = Path(self._experiment_file_data.file_paths[nuboard_file_index].simulation_main_path) / 'video_screenshot'
        if not video_path.exists():
            video_path.mkdir(parents=True, exist_ok=True)
        video_save_path = video_path / video_name
        scenario = self.figures[figure_index].scenario
        database_interval = scenario.database_interval
        selected_simulation_figure = self._figures[figure_index]
        try:
            if len(selected_simulation_figure.ego_state_plot.data_sources):
                chrome_options = webdriver.ChromeOptions()
                chrome_options.headless = True
                driver = webdriver.Chrome(chrome_options=chrome_options)
                driver.set_window_size(1920, 1080)
                shape = None
                simulation_figure = self._create_initial_figure(figure_index=figure_index, backend='canvas', figure_sizes=simulation_tile_style['render_figure_sizes'])
                simulation_figure.copy_datasources(selected_simulation_figure)
                self._render_scenario(main_figure=simulation_figure)
                length = len(selected_simulation_figure.ego_state_plot.data_sources)
                for frame_index in tqdm(range(length), desc='Rendering video'):
                    self._render_plots(main_figure=simulation_figure, frame_index=frame_index)
                    image = get_screenshot_as_png(column(simulation_figure.figure), driver=driver)
                    shape = image.size
                    images.append(image)
                    label = f'Rendering video now... ({frame_index}/{length})'
                    self._doc.add_next_tick_callback(partial(self._update_video_button_label, figure_index=figure_index, label=label))
                fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                if database_interval:
                    fps = 1 / database_interval
                else:
                    fps = 20
                video_obj = cv2.VideoWriter(filename=str(video_save_path), fourcc=fourcc, fps=fps, frameSize=shape)
                for index, image in enumerate(images):
                    cv2_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    video_obj.write(cv2_image)
                video_obj.release()
                logger.info('Video saved to %s' % str(video_save_path))
        except (RuntimeError, Exception) as e:
            logger.warning('%s' % e)
        self._doc.add_next_tick_callback(partial(self._reset_video_button, figure_index=figure_index))

    def _first_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the first button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_specific_frame(figure=figure, frame_index=0)

    def _prev_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the prev button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_previous_frame(figure)

    def _play_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the play button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._process_play_request(figure)

    def _next_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the next button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_next_frame(figure)

    def _last_button_on_click(self, figure_index: int) -> None:
        """
        Will be called when the last button is clicked.
        :param figure_index: The SimulationFigure index to render.
        """
        figure = self._figures[figure_index]
        self._request_specific_frame(figure=figure, frame_index=len(figure.simulation_history.data) - 1)

    def _slider_on_change(self, attr: str, old: int, frame_index: int, figure_index: int) -> None:
        """
        The function that's called every time the slider's value has changed.
        All frame requests are routed through slider's event handling since currently there's no way to manually
        set the slider's value programatically (to sync the slider value) without triggering this event.
        :param attr: Attribute name.
        :param old: Old value.
        :param frame_index: The new value of the slider, which is the requested frame index.
        :param figure_index: Figure index.
        """
        del attr, old
        selected_figure = self._figures[figure_index]
        self._request_plot_rendering(figure=selected_figure, frame_index=frame_index)

    def _request_specific_frame(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Requests to render the previous frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        :param frame_index: The frame index to render
        """
        figure.slider.value = frame_index

    def _request_previous_frame(self, figure: SimulationFigure) -> None:
        """
        Requests to render the previous frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        """
        if self._current_frame_index > 0:
            figure.slider.value = self._current_frame_index - 1

    def _request_next_frame(self, figure: SimulationFigure) -> bool:
        """
        Requests to render next frame of the specified SimulationFigure.
        :param figure: The SimulationFigure render.
        :return True if the request is valid, False otherwise.
        """
        result = False
        if self._current_frame_index < len(figure.simulation_history.data) - 1:
            figure.slider.value = self._current_frame_index + 1
            result = True
        return result

    def _request_plot_rendering(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Request the SimulationTile to render a frame of the plot. The requested frame will be enqueued if frame rate cap
        is reached or the figure is currently rendering a frame.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
        current_time = time.time()
        if current_time - self._last_frame_time < self._minimum_frame_time_seconds or figure.is_rendering():
            logger.info('Frame deferred: %d', frame_index)
            self._plot_render_queue = (figure, frame_index)
        else:
            self._process_plot_render_request(figure=figure, frame_index=frame_index)
            self._last_frame_time = time.time()

    def _stop_playback(self, figure: SimulationFigure) -> None:
        """
        Stops the playback for the given figure.
        :param figure: SimulationFigure to stop rendering.
        """
        if self._playback_callback_handle:
            self._doc.remove_periodic_callback(self._playback_callback_handle)
            self._playback_callback_handle = None
            figure.play_button.label = 'play'

    def _start_playback(self, figure: SimulationFigure) -> None:
        """
        Starts the playback for the given figure.
        :param figure: SimulationFigure to stop rendering.
        """
        callback_period_seconds = figure.simulation_history.interval_seconds
        callback_period_seconds = max(self._minimum_frame_time_seconds, callback_period_seconds)
        callback_period_ms = 1000.0 * callback_period_seconds
        self._playback_callback_handle = self._doc.add_periodic_callback(partial(self._playback_callback, figure), callback_period_ms)
        figure.play_button.label = 'stop'

    def _playback_callback(self, figure: SimulationFigure) -> None:
        """The callback that will advance the simulation frame. Will automatically stop the playback once we reach the final frame."""
        if not self._request_next_frame(figure):
            self._stop_playback(figure)

    def _process_play_request(self, figure: SimulationFigure) -> None:
        """
        Processes play request. When play mode is activated, the frame auto-advances, at the rate of the currently set frame rate cap.
        :param figure: The SimulationFigure to render.
        """
        if self._playback_callback_handle:
            self._stop_playback(figure)
        else:
            self._start_playback(figure)

    def _process_plot_render_request(self, figure: SimulationFigure, frame_index: int) -> None:
        """
        Process plot render requests, coming either from the slider or the render queue.
        :param figure: The SimulationFigure to render.
        :param frame_index: The requested frame index to render.
        """
        if frame_index != len(figure.simulation_history.data):
            if self._async_rendering:
                thread = threading.Thread(target=self._render_plots, kwargs={'main_figure': figure, 'frame_index': frame_index}, daemon=True)
                thread.start()
            else:
                self._render_plots(main_figure=figure, frame_index=frame_index)

    def _render_scenario(self, main_figure: SimulationFigure, hidden_glyph_names: Optional[List[str]]=None) -> None:
        """
        Render scenario.
        :param main_figure: Simulation figure object.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        """
        if self._async_rendering:

            def render() -> None:
                """Wrapper for the non-map-dependent parts of the rendering logic."""
                main_figure.update_data_sources()
                self._render_expert_trajectory(main_figure=main_figure)
                mission_goal = main_figure.scenario.get_mission_goal()
                if mission_goal is not None:
                    main_figure.render_mission_goal(mission_goal_state=mission_goal)
                self._render_plots(main_figure=main_figure, frame_index=0, hidden_glyph_names=hidden_glyph_names)

            def render_map_dependent() -> None:
                """Wrapper for the map-dependent parts of the rendering logic."""
                self._load_map_data(main_figure=main_figure)
                main_figure.update_map_dependent_data_sources()
                self._render_map(main_figure=main_figure)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            executor.submit(render)
            executor.submit(render_map_dependent)
            executor.shutdown(wait=False)
        else:
            main_figure.update_data_sources()
            self._load_map_data(main_figure=main_figure)
            main_figure.update_map_dependent_data_sources()
            self._render_map(main_figure=main_figure)
            self._render_expert_trajectory(main_figure=main_figure)
            mission_goal = main_figure.scenario.get_mission_goal()
            if mission_goal is not None:
                main_figure.render_mission_goal(mission_goal_state=mission_goal)
            self._render_plots(main_figure=main_figure, frame_index=0, hidden_glyph_names=hidden_glyph_names)

    def _load_map_data(self, main_figure: SimulationFigure) -> None:
        """
        Load the map data of the simulation tile.
        :param main_figure: Simulation figure.
        """
        map_name = main_figure.scenario.map_api.map_name
        map_api = self._map_api(map_name)
        layer_names = [SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.LANE, SemanticMapLayer.CROSSWALK, SemanticMapLayer.INTERSECTION, SemanticMapLayer.STOP_LINE, SemanticMapLayer.WALKWAYS, SemanticMapLayer.CARPARK_AREA]
        assert main_figure.simulation_history.data, 'No simulation history samples, unable to render the map.'
        ego_pose = main_figure.simulation_history.data[0].ego_state.center
        center = Point2D(ego_pose.x, ego_pose.y)
        self._nearest_vector_map = map_api.get_proximal_map_objects(center, self._radius, layer_names)
        if SemanticMapLayer.STOP_LINE in self._nearest_vector_map:
            stop_polygons = self._nearest_vector_map[SemanticMapLayer.STOP_LINE]
            self._nearest_vector_map[SemanticMapLayer.STOP_LINE] = [stop_polygon for stop_polygon in stop_polygons if stop_polygon.stop_line_type != StopLineType.TURN_STOP]
        main_figure.lane_connectors = {lane_connector.id: lane_connector for lane_connector in self._nearest_vector_map[SemanticMapLayer.LANE_CONNECTOR]}

    def _render_map_polygon_layers(self, main_figure: SimulationFigure) -> None:
        """Renders the polygon layers of the map."""
        polygon_layer_names = [(SemanticMapLayer.LANE, simulation_map_layer_color[SemanticMapLayer.LANE]), (SemanticMapLayer.INTERSECTION, simulation_map_layer_color[SemanticMapLayer.INTERSECTION]), (SemanticMapLayer.STOP_LINE, simulation_map_layer_color[SemanticMapLayer.STOP_LINE]), (SemanticMapLayer.CROSSWALK, simulation_map_layer_color[SemanticMapLayer.CROSSWALK]), (SemanticMapLayer.WALKWAYS, simulation_map_layer_color[SemanticMapLayer.WALKWAYS]), (SemanticMapLayer.CARPARK_AREA, simulation_map_layer_color[SemanticMapLayer.CARPARK_AREA])]
        roadblock_ids = main_figure.scenario.get_route_roadblock_ids()
        if roadblock_ids:
            polygon_layer_names.append((SemanticMapLayer.ROADBLOCK, simulation_map_layer_color[SemanticMapLayer.ROADBLOCK]))
        for layer_name, color in polygon_layer_names:
            map_polygon = MapPoint(point_2d=[])
            if layer_name == SemanticMapLayer.ROADBLOCK:
                layer = self._nearest_vector_map[SemanticMapLayer.LANE] + self._nearest_vector_map[SemanticMapLayer.LANE_CONNECTOR]
                for map_obj in layer:
                    roadblock_id = map_obj.get_roadblock_id()
                    if roadblock_id in roadblock_ids:
                        coords = map_obj.polygon.exterior.coords
                        points = [Point2D(x=x, y=y) for x, y in coords]
                        map_polygon.point_2d.append(points)
            else:
                layer = self._nearest_vector_map[layer_name]
                for map_obj in layer:
                    coords = map_obj.polygon.exterior.coords
                    points = [Point2D(x=x, y=y) for x, y in coords]
                    map_polygon.point_2d.append(points)
            polygon_source = ColumnDataSource(dict(xs=map_polygon.polygon_xs, ys=map_polygon.polygon_ys))
            layer_map_polygon_plot = main_figure.figure.multi_polygons(xs='xs', ys='ys', fill_color=color['fill_color'], fill_alpha=color['fill_color_alpha'], line_color=color['line_color'], source=polygon_source)
            layer_map_polygon_plot.level = 'underlay'
            main_figure.map_polygon_plots[layer_name.name] = layer_map_polygon_plot

    def _render_map_line_layers(self, main_figure: SimulationFigure) -> None:
        """Renders the line layers of the map."""
        line_layer_names = [(SemanticMapLayer.LANE, simulation_map_layer_color[SemanticMapLayer.BASELINE_PATHS]), (SemanticMapLayer.LANE_CONNECTOR, simulation_map_layer_color[SemanticMapLayer.LANE_CONNECTOR])]
        for layer_name, color in line_layer_names:
            layer = self._nearest_vector_map[layer_name]
            map_line = MapPoint(point_2d=[])
            for map_obj in layer:
                path = map_obj.baseline_path.discrete_path
                points = [Point2D(x=pose.x, y=pose.y) for pose in path]
                map_line.point_2d.append(points)
            line_source = ColumnDataSource(dict(xs=map_line.line_xs, ys=map_line.line_ys))
            layer_map_line_plot = main_figure.figure.multi_line(xs='xs', ys='ys', line_color=color['line_color'], line_alpha=color['line_color_alpha'], line_width=0.5, line_dash='dashed', source=line_source)
            layer_map_line_plot.level = 'underlay'
            main_figure.map_line_plots[layer_name.name] = layer_map_line_plot

    def _render_map(self, main_figure: SimulationFigure) -> None:
        """
        Render a map.
        :param main_figure: Simulation figure.
        """

        def render() -> None:
            """Wrapper for the actual render logic, for multi-threading compatibility."""
            self._render_map_polygon_layers(main_figure)
            self._render_map_line_layers(main_figure)
        self._doc.add_next_tick_callback(lambda: render())

    @staticmethod
    def _render_expert_trajectory(main_figure: SimulationFigure) -> None:
        """
        Render expert trajectory.
        :param main_figure: Main simulation figure.
        """
        expert_ego_trajectory = main_figure.scenario.get_expert_ego_trajectory()
        source = extract_source_from_states(expert_ego_trajectory)
        main_figure.render_expert_trajectory(expert_ego_trajectory_state=source)

    def _render_plots(self, main_figure: SimulationFigure, frame_index: int, hidden_glyph_names: Optional[List[str]]=None) -> None:
        """
        Render plot with a frame index.
        :param main_figure: Main figure to render.
        :param frame_index: A frame index.
        :param hidden_glyph_names: A list of glyph names to be hidden.
        """
        if main_figure.lane_connectors is not None and len(main_figure.lane_connectors):
            main_figure.traffic_light_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.ego_state_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, radius=self._radius, doc=self._doc)
        main_figure.ego_state_trajectory_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.agent_state_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)
        main_figure.agent_state_heading_plot.update_plot(main_figure=main_figure.figure, frame_index=frame_index, doc=self._doc)

        def update_decorations() -> None:
            main_figure.figure.title.text = main_figure.figure_title_name_with_timestamp(frame_index=frame_index)
            main_figure.update_glyphs_visibility(glyph_names=hidden_glyph_names)
        self._doc.add_next_tick_callback(lambda: update_decorations())
        self._last_frame_index = self._current_frame_index
        self._current_frame_index = frame_index

    def _periodic_callback(self) -> None:
        """Periodic callback registered to the bokeh.Document."""
        if self._plot_render_queue:
            figure, frame_index = self._plot_render_queue
            last_frame_direction = math.copysign(1, self._current_frame_index - self._last_frame_index)
            request_frame_direction = math.copysign(1, frame_index - self._current_frame_index)
            if request_frame_direction != last_frame_direction:
                logger.info('Frame dropped %d', frame_index)
                self._plot_render_queue = None
            elif not figure.is_rendering():
                logger.info('Processing render queue for frame %d', frame_index)
                self._plot_render_queue = None
                self._process_plot_render_request(figure=figure, frame_index=frame_index)

def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, vehicle_parameters: VehicleParameters, map_factory: AbstractMapFactory, period_milliseconds: int=5000, radius: float=300.0, async_rendering: bool=True, frame_rate_cap_hz: int=60):
    """
        Scenario simulation tile.
        :param doc: Bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        :param vehicle_parameters: Ego pose parameters.
        :param map_factory: Map factory for building maps.
        :param period_milliseconds: Milliseconds to update the tile.
        :param radius: Map radius.
        :param async_rendering: When true, will use threads to render asynchronously.
        :param frame_rate_cap_hz: Maximum frames to render per second. Internally this value is capped at 60.
        """
    self._doc = doc
    self._vehicle_parameters = vehicle_parameters
    self._map_factory = map_factory
    self._experiment_file_data = experiment_file_data
    self._period_milliseconds = period_milliseconds
    self._radius = radius
    self._selected_scenario_keys: List[SimulationScenarioKey] = []
    self._executor = ThreadPoolExecutor(max_workers=4)
    self._maps: Dict[str, AbstractMap] = {}
    self._figures: List[SimulationFigure] = []
    self._nearest_vector_map: Dict[SemanticMapLayer, List[MapObject]] = {}
    self._async_rendering = async_rendering
    self._plot_render_queue: Optional[Tuple[SimulationFigure, int]] = None
    self._doc.add_periodic_callback(self._periodic_callback, period_milliseconds=1000)
    self._last_frame_time = time.time()
    self._current_frame_index = 0
    self._last_frame_index = 0
    self._playback_callback_handle: Optional[PeriodicCallback] = None
    if frame_rate_cap_hz < 1 or frame_rate_cap_hz > 60:
        raise ValueError('frame_rate_cap_hz should be between 1 and 60')
    self._minimum_frame_time_seconds = 1.0 / float(frame_rate_cap_hz)
    logger.info('Minimum frame time=%4.3f s', self._minimum_frame_time_seconds)

def _start_playback(self, figure: SimulationFigure) -> None:
    """
        Starts the playback for the given figure.
        :param figure: SimulationFigure to stop rendering.
        """
    callback_period_seconds = figure.simulation_history.interval_seconds
    callback_period_seconds = max(self._minimum_frame_time_seconds, callback_period_seconds)
    callback_period_ms = 1000.0 * callback_period_seconds
    self._playback_callback_handle = self._doc.add_periodic_callback(partial(self._playback_callback, figure), callback_period_ms)
    figure.play_button.label = 'stop'

@dataclass
class NuBoardFile:
    """Data class to save nuBoard file info."""
    simulation_main_path: str
    metric_main_path: str
    metric_folder: str
    aggregator_metric_folder: str
    simulation_folder: Optional[str] = None
    current_path: Optional[pathlib.Path] = None

    @classmethod
    def extension(cls) -> str:
        """Return nuboard file extension."""
        return '.nuboard'

    def __eq__(self, other: object) -> bool:
        """
        Comparison between two NuBoardFile.
        :param other: Other object.
        :return True if both objects are same.
        """
        if not isinstance(other, NuBoardFile):
            return NotImplemented
        return other.simulation_main_path == self.simulation_main_path and other.simulation_folder == self.simulation_folder and (other.metric_main_path == self.metric_main_path) and (other.metric_folder == self.metric_folder) and (other.aggregator_metric_folder == self.aggregator_metric_folder) and (other.current_path == self.current_path)

    def save_nuboard_file(self, filename: pathlib.Path) -> None:
        """
        Save NuBoardFile data class to a file.
        :param filename: The saved file path.
        """
        save_object_as_pickle(filename, self.serialize())

    @classmethod
    def load_nuboard_file(cls, filename: pathlib.Path) -> NuBoardFile:
        """
        Read a NuBoard file to NuBoardFile data class.
        :file: NuBoard file path.
        """
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        return cls.deserialize(data=data)

    def serialize(self) -> Dict[str, str]:
        """
        Serialization of NuBoardFile data class to dictionary.
        :return A serialized dictionary class.
        """
        as_dict = {'simulation_main_path': self.simulation_main_path, 'metric_main_path': self.metric_main_path, 'metric_folder': self.metric_folder, 'aggregator_metric_folder': self.aggregator_metric_folder}
        if self.simulation_folder is not None:
            as_dict['simulation_folder'] = self.simulation_folder
        return as_dict

    @classmethod
    def deserialize(cls, data: Dict[str, str]) -> NuBoardFile:
        """
        Deserialization of a NuBoard file into NuBoardFile data class.
        :param data: A serialized nuboard file data.
        :return A NuBoard file data class.
        """
        simulation_main_path = data['simulation_main_path'].replace('//', '/')
        metric_main_path = data['metric_main_path'].replace('//', '/')
        return NuBoardFile(simulation_main_path=simulation_main_path, simulation_folder=data.get('simulation_folder', None), metric_main_path=metric_main_path, metric_folder=data['metric_folder'], aggregator_metric_folder=data['aggregator_metric_folder'])

@classmethod
def deserialize(cls, data: Dict[str, str]) -> NuBoardFile:
    """
        Deserialization of a NuBoard file into NuBoardFile data class.
        :param data: A serialized nuboard file data.
        :return A NuBoard file data class.
        """
    simulation_main_path = data['simulation_main_path'].replace('//', '/')
    metric_main_path = data['metric_main_path'].replace('//', '/')
    return NuBoardFile(simulation_main_path=simulation_main_path, simulation_folder=data.get('simulation_folder', None), metric_main_path=metric_main_path, metric_folder=data['metric_folder'], aggregator_metric_folder=data['aggregator_metric_folder'])

class NuPlanScenarioBuilder(AbstractScenarioBuilder):
    """Builder class for constructing nuPlan scenarios for training and simulation."""

    def __init__(self, data_root: str, map_root: str, sensor_root: str, db_files: Optional[Union[List[str], str]], map_version: str, include_cameras: bool=False, max_workers: Optional[int]=None, verbose: bool=True, scenario_mapping: Optional[ScenarioMapping]=None, vehicle_parameters: Optional[VehicleParameters]=None):
        """
        Initialize scenario builder that filters and retrieves scenarios from the nuPlan dataset.
        :param data_root: Local data root for loading (or storing downloaded) the log databases.
                          If `db_files` is not None, all downloaded databases will be stored to this data root.
                          E.g.: /data/sets/nuplan
        :param map_root: Local map root for loading (or storing downloaded) the map database.
        :param sensor_root: Local map root for loading (or storing downloaded) the sensor blobs.
        :param db_files: Path to load the log database(s) from.
                         It can be a local/remote path to a single database, list of databases or dir of databases.
                         If None, all database filenames found under `data_root` will be used.
                         E.g.: /data/sets/nuplan/nuplan-v1.1/splits/mini/2021.10.11.08.31.07_veh-50_01750_01948.db
        :param map_version: Version of map database to load. The map database is passed to each loaded log database.
        :param include_cameras: If true, make camera data available in scenarios.
        :param max_workers: Maximum number of workers to use when loading the databases concurrently.
                            Only used when the number of databases to load is larger than this parameter.
        :param verbose: Whether to print progress and details during the database loading and scenario building.
        :param scenario_mapping: Mapping of scenario types to extraction information.
        :param vehicle_parameters: Vehicle parameters for this db.
        """
        self._data_root = data_root
        self._map_root = map_root
        self._sensor_root = sensor_root
        self._db_files = discover_log_dbs(data_root if db_files is None else db_files)
        self._map_version = map_version
        self._include_cameras = include_cameras
        self._max_workers = max_workers
        self._verbose = verbose
        self._scenario_mapping = scenario_mapping if scenario_mapping is not None else ScenarioMapping({}, None)
        self._vehicle_parameters = vehicle_parameters if vehicle_parameters is not None else get_pacifica_parameters()

    def __reduce__(self) -> Tuple[Type[NuPlanScenarioBuilder], Tuple[Any, ...]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self._data_root, self._map_root, self._sensor_root, self._db_files, self._map_version, self._include_cameras, self._max_workers, self._verbose, self._scenario_mapping, self._vehicle_parameters))

    @classmethod
    def get_scenario_type(cls) -> Type[AbstractScenario]:
        """Inherited. See superclass."""
        return cast(Type[AbstractScenario], NuPlanScenario)

    def get_map_factory(self) -> AbstractMapFactory:
        """Inherited. See superclass."""
        return NuPlanMapFactory(get_maps_db(self._map_root, self._map_version))

    def _aggregate_dicts(self, dicts: List[ScenarioDict]) -> ScenarioDict:
        """
        Combines multiple scenario dicts into a single dictionary by concatenating lists of matching scenario names.
        Sample input:
            [{"a": [1, 2, 3], "b": [2, 3, 4]}, {"b": [3, 4, 5], "c": [4, 5]}]
        Sample output:
            {"a": [1, 2, 3], "b": [2, 3, 4, 3, 4, 5], "c": [4, 5]}
        :param dicts: The list of dictionaries to concatenate.
        :return: The concatenated dictionaries.
        """
        output_dict = dicts[0]
        for merge_dict in dicts[1:]:
            for key in merge_dict:
                if key not in output_dict:
                    output_dict[key] = merge_dict[key]
                else:
                    output_dict[key] += merge_dict[key]
        return output_dict

    def _create_scenarios(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> ScenarioDict:
        """
        Creates a scenario dictionary with scenario type as key and list of scenarios for each type.
        :param scenario_filter: Structure that contains scenario filtering instructions.
        :param worker: Worker pool for concurrent scenario processing.
        :return: Constructed scenario dictionary.
        """
        allowable_log_names = set(scenario_filter.log_names) if scenario_filter.log_names is not None else None
        map_parameters = [GetScenariosFromDbFileParams(data_root=self._data_root, log_file_absolute_path=log_file, expand_scenarios=scenario_filter.expand_scenarios, map_root=self._map_root, map_version=self._map_version, scenario_mapping=self._scenario_mapping, vehicle_parameters=self._vehicle_parameters, filter_tokens=scenario_filter.scenario_tokens, filter_types=scenario_filter.scenario_types, filter_map_names=scenario_filter.map_names, remove_invalid_goals=scenario_filter.remove_invalid_goals, sensor_root=self._sensor_root, include_cameras=self._include_cameras, verbose=self._verbose) for log_file in self._db_files if allowable_log_names is None or absolute_path_to_log_name(log_file) in allowable_log_names]
        if len(map_parameters) == 0:
            logger.warning('No log files found! This may mean that you need to set your environment, or that all of your log files got filtered out on this worker.')
            return {}
        dicts = worker_map(worker, get_scenarios_from_log_file, map_parameters)
        return self._aggregate_dicts(dicts)

    def _create_filter_wrappers(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> List[FilterWrapper]:
        """
        Creates a series of filter wrappers that will be applied sequentially to construct the list of scenarios.
        :param scenario_filter: Structure that contains scenario filtering instructions.
        :param worker: Worker pool for concurrent scenario processing.
        :return: Series of filter wrappers.
        """
        filters = [FilterWrapper(fn=partial(filter_num_scenarios_per_type, num_scenarios_per_type=scenario_filter.num_scenarios_per_type, randomize=scenario_filter.shuffle), enable=scenario_filter.num_scenarios_per_type is not None, name='num_scenarios_per_type'), FilterWrapper(fn=partial(filter_total_num_scenarios, limit_total_scenarios=scenario_filter.limit_total_scenarios, randomize=scenario_filter.shuffle), enable=scenario_filter.limit_total_scenarios is not None, name='limit_total_scenarios'), FilterWrapper(fn=partial(filter_scenarios_by_timestamp, timestamp_threshold_s=scenario_filter.timestamp_threshold_s), enable=scenario_filter.timestamp_threshold_s is not None, name='filter_scenarios_by_timestamp'), FilterWrapper(fn=partial(filter_non_stationary_ego, minimum_threshold=scenario_filter.ego_displacement_minimum_m), enable=scenario_filter.ego_displacement_minimum_m is not None, name='filter_non_stationary_ego'), FilterWrapper(fn=partial(filter_ego_starts, speed_threshold=scenario_filter.ego_start_speed_threshold, speed_noise_tolerance=scenario_filter.speed_noise_tolerance), enable=scenario_filter.ego_start_speed_threshold is not None, name='filter_ego_starts'), FilterWrapper(fn=partial(filter_ego_stops, speed_threshold=scenario_filter.ego_stop_speed_threshold, speed_noise_tolerance=scenario_filter.speed_noise_tolerance), enable=scenario_filter.ego_stop_speed_threshold is not None, name='filter_ego_stops'), FilterWrapper(fn=partial(filter_fraction_lidarpc_tokens_in_set, token_set_path=scenario_filter.token_set_path, fraction_threshold=scenario_filter.fraction_in_token_set_threshold), enable=scenario_filter.token_set_path is not None and scenario_filter.fraction_in_token_set_threshold is not None, name='filter_fraction_lidarpc_tokens_in_set'), FilterWrapper(fn=partial(filter_ego_has_route, map_radius=scenario_filter.ego_route_radius), enable=scenario_filter.ego_route_radius is not None, name='filter_ego_has_route')]
        return filters

    def get_scenarios(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> List[AbstractScenario]:
        """Implemented. See interface."""
        scenario_dict = self._create_scenarios(scenario_filter, worker)
        filter_wrappers = self._create_filter_wrappers(scenario_filter, worker)
        for filter_wrapper in filter_wrappers:
            scenario_dict = filter_wrapper.run(scenario_dict)
        return scenario_dict_to_list(scenario_dict, shuffle=scenario_filter.shuffle)

    @property
    def repartition_strategy(self) -> RepartitionStrategy:
        """Implemented. See interface."""
        return RepartitionStrategy.REPARTITION_FILE_DISK

def get_map_factory(self) -> AbstractMapFactory:
    """Inherited. See superclass."""
    return NuPlanMapFactory(get_maps_db(self._map_root, self._map_version))

@lru_cache(maxsize=1)
def get_test_nuplan_scenario_builder() -> NuPlanScenarioBuilder:
    """Get a nuPlan scenario builder object with default settings to be used in testing."""
    return NuPlanScenarioBuilder(data_root=NUPLAN_DATA_ROOT, map_root=NUPLAN_MAPS_ROOT, sensor_root=NUPLAN_SENSOR_ROOT, db_files=NUPLAN_DB_FILES, map_version=NUPLAN_MAP_VERSION)

class SubmissionPlanner:
    """
    Class holding a planner and exposing functionalities as a server. The services are planner initialization and
    trajectory computation.
    """

    def __init__(self, planner_config: DictConfig):
        """
        Prepares the planner and the server. The communication port is read from an environmental variable.
        :param planner_config: The planner configuration to instantiate the planner
        """
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        map_version = os.getenv('NUPLAN_MAP_VERSION', 'nuplan-maps-v1.0')
        map_factory = NuPlanMapFactory(GPKGMapsDB(map_version=map_version, map_root=os.path.join(os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'), 'maps')))
        map_manager = MapManager(map_factory)
        chpb_grpc.add_DetectionTracksChallengeServicer_to_server(DetectionTracksChallengeServicer(planner_config, map_manager), self.server)
        port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        logger.info(f'Submission container starting with port {port}')
        if not port:
            raise RuntimeError("Environment variable not specified: 'SUBMISSION_CONTAINER_PORT'")
        self.server.add_insecure_port(f'[::]:{port}')

    def serve(self) -> None:
        """Starts the server."""
        logger.info('Server starting...')
        self.server.start()
        logger.info('Server started!')
        self.server.wait_for_termination()
        logger.info('Server terminated!')

def __init__(self, planner_config: DictConfig):
    """
        Prepares the planner and the server. The communication port is read from an environmental variable.
        :param planner_config: The planner configuration to instantiate the planner
        """
    self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    map_version = os.getenv('NUPLAN_MAP_VERSION', 'nuplan-maps-v1.0')
    map_factory = NuPlanMapFactory(GPKGMapsDB(map_version=map_version, map_root=os.path.join(os.getenv('NUPLAN_DATA_ROOT', '~/nuplan/dataset'), 'maps')))
    map_manager = MapManager(map_factory)
    chpb_grpc.add_DetectionTracksChallengeServicer_to_server(DetectionTracksChallengeServicer(planner_config, map_manager), self.server)
    port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
    logger.info(f'Submission container starting with port {port}')
    if not port:
        raise RuntimeError("Environment variable not specified: 'SUBMISSION_CONTAINER_PORT'")
    self.server.add_insecure_port(f'[::]:{port}')

