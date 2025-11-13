# Cluster 56

class TestPlannerTutorialNotebook(unittest.TestCase):
    """
    Test planner tutorial Jupyter notebook across executed commands.
    """

    def test_full_execution(self) -> None:
        """
        Sanity test for notebook calling planner simulation.
        """
        environ['NUPLAN_TUTORIAL_PATH'] = TUTORIAL_PATH_REL
        with testbook(path.join(TUTORIAL_PATH_ABS, 'nuplan_planner_tutorial.ipynb'), timeout=250) as tb:
            tb.execute_cell(range(28))

def test_full_execution(self) -> None:
    """
        Sanity test for notebook calling planner simulation.
        """
    environ['NUPLAN_TUTORIAL_PATH'] = TUTORIAL_PATH_REL
    with testbook(path.join(TUTORIAL_PATH_ABS, 'nuplan_planner_tutorial.ipynb'), timeout=250) as tb:
        tb.execute_cell(range(28))

class TestScenarioVisualizationTutorialNotebook(unittest.TestCase):
    """
    Test scenario visualization tutorial Jupyter notebook across executed commands.
    """

    def test_scenario_visualization_execution(self) -> None:
        """
        Sanity test for notebook calling scenario visualization.
        """
        with testbook(path.join(TUTORIAL_PATH_ABS, 'nuplan_scenario_visualization.ipynb'), timeout=250) as tb:
            tb.execute_cell(range(7))

def test_scenario_visualization_execution(self) -> None:
    """
        Sanity test for notebook calling scenario visualization.
        """
    with testbook(path.join(TUTORIAL_PATH_ABS, 'nuplan_scenario_visualization.ipynb'), timeout=250) as tb:
        tb.execute_cell(range(7))

class TestNuPlanCli(unittest.TestCase):
    """
    Test nuplan cli with typer engine
    """

    def _get_ensure_file_downloaded_patch(self, expected_data_root: str, expected_remote_path: str) -> Callable[[str, str], str]:
        """
        Get the patch for ensure_file_downloaded.
        """

        def fxn(actual_data_root: str, actual_remote_path: str) -> str:
            """
            The patch for ensure_file_downloaded.
            """
            self.assertEqual(expected_data_root, actual_data_root)
            self.assertEqual(expected_remote_path, actual_remote_path)
            return actual_remote_path
        return fxn

    def test_db_info_info(self) -> None:
        """
        Test nuplan_cli.py db info command.
        """

        def _patch_get_db_description(log_name: str) -> DbDescription:
            """
            A patch for the get_db_description db function.
            """
            self.assertEqual('expected_log_name', log_name)
            return DbDescription(tables={'first_table': TableDescription(name='first_table', row_count=123, columns={'first_token': ColumnDescription(column_id=0, name='first_token', data_type='blob', nullable=False, is_primary_key=True), 'first_something': ColumnDescription(column_id=1, name='first_something', data_type='varchar(64)', nullable=True, is_primary_key=False)}), 'second_table': TableDescription(name='second_table', row_count=456, columns={'second_token': ColumnDescription(column_id=0, name='token', data_type='blob', nullable=False, is_primary_key=True), 'second_something': ColumnDescription(column_id=1, name='somthing', data_type='varchar(128)', nullable=True, is_primary_key=False)})})
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_description', _patch_get_db_description), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'info', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['table first_table: 123 rows', 'table second_table: 456 rows', 'column first_token: blob not null primary key', 'column first_something: varchar(64) null', 'column second_token: blob not null primary key', 'column second_something: varchar(128) null']
            result_stdout = result.stdout.lower()
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result_stdout)

    def test_db_cli_duration(self) -> None:
        """
        Test nuplan_cli.py db duration command.
        """

        def _patch_db_duration(log_name: str) -> int:
            """
            A patch for the get_db_duration function.
            """
            self.assertEqual('expected_log_name', log_name)
            return int(125 * 1000000.0)
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_duration_in_us', _patch_db_duration), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'duration', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            self.assertTrue('00:02:05' in result.stdout)

    def test_db_cli_log_duration(self) -> None:
        """
        Test nuplan_cli.py db log-duration command.
        """

        def _patch_db_log_duration(log_name: str) -> Generator[Tuple[str, int], None, None]:
            """
            Patch for get_db_log_duration function.
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'log_file_{i}', int((i + 1) * 67 * 1000000.0))
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_log_duration', _patch_db_log_duration), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'log-duration', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['log_file_0 is 00:01:07', 'log_file_1 is 00:02:14', 'log_file_2 is 00:03:21', '3 total logs']
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result.stdout)

    def test_db_cli_log_vehicle(self) -> None:
        """
        Test nuplan_cli.py log-vehicle command.
        """

        def _patch_db_log_vehicles(log_name: str) -> Generator[Tuple[str, str], None, None]:
            """
            Patch for get_db_log_vehicles function.
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'log_file_{i}', f'vehicle_{i}')
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_log_vehicles', _patch_db_log_vehicles), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'log-vehicle', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            for i in range(0, 3, 1):
                self.assertTrue(f'log_file_{i}, vehicle vehicle_{i}' in result.stdout)

    def test_db_cli_scenarios(self) -> None:
        """
        Test db_cli scenarios command.
        """

        def _patch_db_scenario_info(log_name: str) -> Generator[Tuple[str, int], None, None]:
            """
            Patch for get_db_scenario_info
            """
            self.assertEqual('expected_log_name', log_name)
            for i in range(0, 3, 1):
                yield (f'scenario_{i}', i + 5)
        ensure_file_downloaded_patch = self._get_ensure_file_downloaded_patch('/data/sets/nuplan', 'expected_log_name')
        with mock.patch('nuplan.cli.db_cli.get_db_scenario_info', _patch_db_scenario_info), mock.patch('nuplan.cli.db_cli._ensure_file_downloaded', ensure_file_downloaded_patch):
            result = runner.invoke(cli, ['db', 'scenarios', 'expected_log_name'])
            self.assertEqual(0, result.exit_code)
            strings_of_interest = ['scenario_0: 5', 'scenario_1: 6', 'scenario_2: 7', 'TOTAL: 18']
            for string_of_interest in strings_of_interest:
                self.assertTrue(string_of_interest in result.stdout)

def _patch_db_log_vehicles(log_name: str) -> Generator[Tuple[str, str], None, None]:
    """
            Patch for get_db_log_vehicles function.
            """
    self.assertEqual('expected_log_name', log_name)
    for i in range(0, 3, 1):
        yield (f'log_file_{i}', f'vehicle_{i}')

def _patch_db_scenario_info(log_name: str) -> Generator[Tuple[str, int], None, None]:
    """
            Patch for get_db_scenario_info
            """
    self.assertEqual('expected_log_name', log_name)
    for i in range(0, 3, 1):
        yield (f'scenario_{i}', i + 5)

def _get_past_future_sweep(present_lidarpc: LidarPc, sweep_idx: int) -> LidarPc:
    """
    Find a past or future sweep given the present sweep and its index.
    :param present_lidarpc: The present sweep.
    :param sweep_idx: The sweep index.
        - Negative numbers corresponding to past sweeps.
        - 0 corresponding to the present sweep.
        - Positive numbers corresponding to future sweeps.
    :returns: The specified sweep or None if we hit the start or end of an extraction.
    """
    cur_lidarpc = present_lidarpc
    for _ in range(abs(sweep_idx)):
        if sweep_idx > 0:
            if cur_lidarpc.next is None:
                return None
            else:
                cur_lidarpc = cur_lidarpc.next
        elif sweep_idx < 0:
            if cur_lidarpc.prev is None:
                return None
            else:
                cur_lidarpc = cur_lidarpc.prev
    return cur_lidarpc

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

def test_log(self) -> None:
    """Tests the log property"""
    result = self.lidar_pc.log
    self.assertIsInstance(result, Log)

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

def test_trans_matrix_and_inv(self) -> None:
    """Tests the transformation matrix and it's inverse method"""
    trans_matrix = self.ego_pose.trans_matrix
    trans_matrix_inv = self.ego_pose.trans_matrix_inv
    result = np.matmul(trans_matrix, trans_matrix_inv)
    np.testing.assert_allclose(result, np.identity(4), atol=0.001)

def image_with_boxes(img: npt.NDArray[np.uint8], boxes: Optional[List[Tuple[float, float, float, float]]]=None, labels: Optional[List[int]]=None, ncolors: Optional[int]=None, alpha: int=128, labelset: Optional[Dict[int, str]]=None, scores: Optional[List[float]]=None, colors: Optional[Union[Dict[int, Tuple[int, int, int]], Dict[int, Tuple[int, int, int, int]]]]=None) -> Image:
    """
    Simple plotting function to view image with boxes.
    :param img: <np.uint8: nrows, ncols, 3>. Input image.
    :param boxes: [(xmin, ymin, xmax, ymax)]. Bounding boxes.
    :param labels: Box3D labels.
    :param ncolors: Total number of colors needed (ie number of foreground classes).
    :param alpha: Alpha-matting value to use for fill (0-255).
    :param labelset: {id: name}. Maps label ids to names.
    :param scores: Prediction scores.
    :param colors: {id: (R, G, B) OR (R, G, B, A)}.
    :return: Image instance with overlaid boxes.
    """
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    if not boxes or len(boxes) == 0:
        return img
    if not labels:
        labels = [1] * len(boxes)
    if not scores:
        scores = [None] * len(boxes)
    colors = _color_prep(ncolors, alpha, colors)
    draw = ImageDraw.Draw(img, 'RGBA')
    for box, label, score in zip(boxes, labels, scores):
        color = colors[label]
        bbox = [int(b) for b in box]
        draw.rectangle(bbox, outline=color[:3], fill=color)
        draw.rectangle([bbox[0] - 1, bbox[1] - 1, bbox[2] - 1, bbox[3] - 1], outline=color[:3], fill=None)
        text = labelset[label] if labelset else '{:.0f}'.format(label)
        if score:
            text += ': {:.0f}'.format(100 * score)
        draw.text((box[0], box[1]), text)
    return img

def draw_masks(img: Image, target: npt.NDArray[np.uint8], ncolors: Optional[int]=None, colors: Optional[Union[Dict[int, Tuple[int, int, int]], Dict[int, Tuple[int, int, int, int]]]]=None, alpha: int=128) -> None:
    """
    Utility function for overlaying masks on images.
    :param img: Input image.
    :param target: <np.uint8: nrows, ncols>. Same size as image. Indicates the label of each pixel.
    :param ncolors: Total number of colors needed (ie number of foreground classes).
    :param colors: {id: (R, G, B) OR (R, G, B, A)}.
    :param alpha: Alpha-matting value to use for fill (0-255).
    """
    assert isinstance(img, Image.Image), 'img should be PIL type.'
    alpha_img = img.convert('RGBA')
    colors_prep = _color_prep(ncolors, alpha, colors)
    color_mask = build_color_mask(target, colors_prep)
    color_mask_image = Image.fromarray(color_mask, mode='RGBA')
    alpha_img.alpha_composite(color_mask_image)
    img.paste(alpha_img.convert('RGB'))

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

def __getitem__(self, item: int) -> LidarBox:
    """
        Returns the LidarBox object at the given index.
        """
    box = self._begin
    for _ in range(item):
        if box:
            box = self._items_dict[box.timestamp][1]
    return box

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

class TestAngleDiffNumpy(unittest.TestCase):
    """Unittests for angle difference of numpy array."""

    def test_zero_shape(self) -> None:
        """Tests with zero input."""
        period = 2 * np.pi
        x = np.zeros((0,))
        y = np.zeros((0,))
        answer = np.zeros((0,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

    def test_angle_diff_2pi(self) -> None:
        """Tests angle diff function for 2 pi."""
        period = 2 * np.pi
        x: npt.NDArray[np.float64] = np.pi * np.ones((2,))
        y: npt.NDArray[np.float64] = np.pi * np.ones((2,))
        answer = np.zeros((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = np.pi * np.ones((2,))
        y = -np.pi * np.ones((2,))
        answer = np.zeros((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = -np.pi / 6 * np.ones((2,))
        y = np.pi / 6 * np.ones((2,))
        answer = -np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = 2 * np.pi / 3 * np.ones((2,))
        y = -2 * np.pi / 3 * np.ones((2,))
        answer = -2 * np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = 8 * np.pi / 3 * np.ones((2,))
        y = -2 * np.pi / 3 * np.ones((2,))
        answer = -2 * np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = np.zeros((2,))
        y = np.pi * np.ones((2,))
        answer = -np.pi * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

    def test_angle_diff_pi(self) -> None:
        """Tests angle diff function for pi."""
        period = math.pi
        x: npt.NDArray[np.float64] = np.pi * np.ones((2,))
        y: npt.NDArray[np.float64] = np.pi * np.ones((2,))
        answer = np.zeros((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = np.pi * np.ones((2,))
        y = -np.pi * np.ones((2,))
        answer = np.zeros((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = -np.pi / 6 * np.ones((2,))
        y = np.pi / 6 * np.ones((2,))
        answer = -np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = 2 * np.pi / 3 * np.ones((2,))
        y = -2 * np.pi / 3 * np.ones((2,))
        answer = np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = 8 * np.pi / 3 * np.ones((2,))
        y = -2 * np.pi / 3 * np.ones((2,))
        answer = np.pi / 3 * np.ones((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
        x = np.zeros((2,))
        y = np.pi * np.ones((2,))
        answer = np.zeros((2,))
        assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

def test_zero_shape(self) -> None:
    """Tests with zero input."""
    period = 2 * np.pi
    x = np.zeros((0,))
    y = np.zeros((0,))
    answer = np.zeros((0,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

def test_angle_diff_2pi(self) -> None:
    """Tests angle diff function for 2 pi."""
    period = 2 * np.pi
    x: npt.NDArray[np.float64] = np.pi * np.ones((2,))
    y: npt.NDArray[np.float64] = np.pi * np.ones((2,))
    answer = np.zeros((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = np.pi * np.ones((2,))
    y = -np.pi * np.ones((2,))
    answer = np.zeros((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = -np.pi / 6 * np.ones((2,))
    y = np.pi / 6 * np.ones((2,))
    answer = -np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = 2 * np.pi / 3 * np.ones((2,))
    y = -2 * np.pi / 3 * np.ones((2,))
    answer = -2 * np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = 8 * np.pi / 3 * np.ones((2,))
    y = -2 * np.pi / 3 * np.ones((2,))
    answer = -2 * np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = np.zeros((2,))
    y = np.pi * np.ones((2,))
    answer = -np.pi * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

def test_angle_diff_pi(self) -> None:
    """Tests angle diff function for pi."""
    period = math.pi
    x: npt.NDArray[np.float64] = np.pi * np.ones((2,))
    y: npt.NDArray[np.float64] = np.pi * np.ones((2,))
    answer = np.zeros((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = np.pi * np.ones((2,))
    y = -np.pi * np.ones((2,))
    answer = np.zeros((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = -np.pi / 6 * np.ones((2,))
    y = np.pi / 6 * np.ones((2,))
    answer = -np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = 2 * np.pi / 3 * np.ones((2,))
    y = -2 * np.pi / 3 * np.ones((2,))
    answer = np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = 8 * np.pi / 3 * np.ones((2,))
    y = -2 * np.pi / 3 * np.ones((2,))
    answer = np.pi / 3 * np.ones((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)
    x = np.zeros((2,))
    y = np.pi * np.ones((2,))
    answer = np.zeros((2,))
    assert_almost_equal(measure.angle_diff_numpy(x, y, period), answer)

class TestImageWithBoxes(unittest.TestCase):
    """Test drawing of input image with boxes and labels."""

    @mock.patch('nuplan.database.utils.plot._color_prep')
    def test_image_with_boxes(self, mock__color_prep) -> None:
        """Test function of viewing image with boxes."""
        target_image_array = np.zeros((100, 100, 3), np.uint8)
        target_image_array[10:41, 10:41] = (255, 0, 0)
        target_image_array[60:91, 60:91] = (0, 255, 0)
        target_image_array[10, 40] = (0, 0, 0)
        target_image_array[40, 10] = (0, 0, 0)
        target_image_array[60, 90] = (0, 0, 0)
        target_image_array[90, 60] = (0, 0, 0)
        target_image = Image.fromarray(target_image_array)
        draw = ImageDraw.Draw(target_image, 'RGB')
        test_image = np.zeros((100, 100, 3), np.uint8)
        labelset = {3: 'green', 2: 'red'}
        boxes = [(11.0, 11.0, 40.0, 40.0), (61.0, 61.0, 90.0, 90.0)]
        scores = [0.01, 0.01]
        labels = [2, 3]
        colors = {2: (255, 0, 0, 255), 3: (0, 255, 0, 255)}
        mock__color_prep.return_value = colors
        draw.text((boxes[0][0], boxes[0][1]), 'red: 1')
        draw.text((boxes[1][0], boxes[1][1]), 'green: 1')
        image = image_with_boxes(test_image, boxes, labels, 2, 255, labelset, scores, colors)
        image = np.array(image.convert('RGB'))
        target_image_converted = np.array(target_image.convert('RGB'))
        mock__color_prep.assert_called_with(2, 255, colors)
        self.assertIsInstance(image, np.ndarray)
        self.assertIsInstance(target_image_converted, np.ndarray)
        self.assertEqual(np.array_equal(target_image_converted, image), True)

@mock.patch('nuplan.database.utils.plot._color_prep')
def test_image_with_boxes(self, mock__color_prep) -> None:
    """Test function of viewing image with boxes."""
    target_image_array = np.zeros((100, 100, 3), np.uint8)
    target_image_array[10:41, 10:41] = (255, 0, 0)
    target_image_array[60:91, 60:91] = (0, 255, 0)
    target_image_array[10, 40] = (0, 0, 0)
    target_image_array[40, 10] = (0, 0, 0)
    target_image_array[60, 90] = (0, 0, 0)
    target_image_array[90, 60] = (0, 0, 0)
    target_image = Image.fromarray(target_image_array)
    draw = ImageDraw.Draw(target_image, 'RGB')
    test_image = np.zeros((100, 100, 3), np.uint8)
    labelset = {3: 'green', 2: 'red'}
    boxes = [(11.0, 11.0, 40.0, 40.0), (61.0, 61.0, 90.0, 90.0)]
    scores = [0.01, 0.01]
    labels = [2, 3]
    colors = {2: (255, 0, 0, 255), 3: (0, 255, 0, 255)}
    mock__color_prep.return_value = colors
    draw.text((boxes[0][0], boxes[0][1]), 'red: 1')
    draw.text((boxes[1][0], boxes[1][1]), 'green: 1')
    image = image_with_boxes(test_image, boxes, labels, 2, 255, labelset, scores, colors)
    image = np.array(image.convert('RGB'))
    target_image_converted = np.array(target_image.convert('RGB'))
    mock__color_prep.assert_called_with(2, 255, colors)
    self.assertIsInstance(image, np.ndarray)
    self.assertIsInstance(target_image_converted, np.ndarray)
    self.assertEqual(np.array_equal(target_image_converted, image), True)

class LidarPointCloud:
    """Simple data class representing a point cloud."""

    def __init__(self, points: npt.NDArray[np.float32]) -> None:
        """
        Class for manipulating and viewing point clouds.
        :param points: <np.float: f, n>. Input point cloud matrix with f features per point and n points.
        """
        if points.ndim == 1:
            points = np.atleast_2d(points).T
        self.points = points

    @staticmethod
    def load_pcd_bin(pcd_bin: Union[str, IO[Any], ByteString], pcd_bin_version: int=1) -> npt.NDArray[np.float32]:
        """
        Loads from pcd binary format:
            version 1: a numpy array with 5 cols (x, y, z, intensity, ring).
            version 2: a numpy array with 6 cols (x, y, z, intensity, ring, lidar_id).
        :param pcd_bin: File path or a file-like object or raw bytes.
        :param pcd_bin_version: 1 or 2, see above.
        :return: <np.float: 6, n>. Point cloud matrix[(x, y, z, intensity, ring, lidar_id)].
        """
        if isinstance(pcd_bin, str):
            scan = np.fromfile(pcd_bin, dtype=np.float32)
        else:
            if not isinstance(pcd_bin, bytes):
                pcd_bin = pcd_bin.read()
            scan = np.frombuffer(pcd_bin, dtype=np.float32)
            scan = np.copy(scan)
        if pcd_bin_version == 1:
            points = scan.reshape((-1, 5))
            points = np.hstack((points, -1 * np.ones((points.shape[0], 1), dtype=np.float32)))
        elif pcd_bin_version == 2:
            points = scan.reshape((-1, 6))
        else:
            pytest.fail('Unknown pcd bin file version: %d' % pcd_bin_version)
        return points.T

    @staticmethod
    def load_pcd(pcd_data: Union[IO[Any], ByteString]) -> npt.NDArray[np.float32]:
        """
        Loads a pcd file.
        :param pcd_data: File path or a file-like object or raw bytes.
        :return: <np.float: 6, n>. Point cloud matrix[(x, y, z, intensity, ring, lidar_id)].
        """
        if not isinstance(pcd_data, bytes):
            pcd_data = pcd_data.read()
        return PointCloud.parse(pcd_data).to_pcd_bin2()

    @classmethod
    def from_file(cls, file_name: str) -> LidarPointCloud:
        """
        Instantiates from a .pcl, .pcd, .npy, or .bin file.
        :param file_name: Path of the pointcloud file on disk.
        :return: A LidarPointCloud object.
        """
        if file_name.endswith('.bin'):
            points = cls.load_pcd_bin(file_name, 1)
        elif file_name.endswith('.bin2'):
            points = cls.load_pcd_bin(file_name, 2)
        elif file_name.endswith('.pcl') or file_name.endswith('.pcd'):
            points = pcd_to_numpy(file_name).T
        elif file_name.endswith('.npy'):
            points = np.load(file_name)
        else:
            raise ValueError('Unsupported filetype {}'.format(file_name))
        return cls(points)

    @classmethod
    def from_buffer(cls, pcd_data: Union[IO[Any], ByteString], content_type: str='bin') -> LidarPointCloud:
        """
        Instantiates from buffer.
        :param pcd_data: File path or a file-like object or raw bytes.
        :param content_type: Type of the point cloud content, such as 'bin', 'bin2', 'pcd'.
        :return: A LidarPointCloud object.
        """
        if content_type == 'bin':
            return cls(cls.load_pcd_bin(pcd_data, 1))
        elif content_type == 'bin2':
            return cls(cls.load_pcd_bin(pcd_data, 2))
        elif content_type == 'pcd':
            return cls(cls.load_pcd(pcd_data))
        else:
            raise NotImplementedError('Not implemented content type: %s' % content_type)

    @classmethod
    def make_random(cls) -> LidarPointCloud:
        """
        Instantiates a random point cloud.
        :return: LidarPointCloud instance.
        """
        return LidarPointCloud(points=np.random.normal(0, 100, size=(4, 100)))

    def __eq__(self, other: object) -> bool:
        """
        Checks if two LidarPointCloud are equal.
        :param other: Other object.
        :return: True if both objects are equal otherwise False.
        """
        if not isinstance(other, LidarPointCloud):
            return NotImplemented
        return np.allclose(self.points, other.points, atol=1e-06)

    def copy(self) -> LidarPointCloud:
        """
        Creates a copy of self.
        :return: LidarPointCloud instance.
        """
        return LidarPointCloud(points=self.points.copy())

    def nbr_points(self) -> int:
        """
        Returns the number of points.
        :return: Number of points.
        """
        return int(self.points.shape[1])

    def subsample(self, ratio: float) -> None:
        """
        Sub-samples the pointcloud.
        :param ratio: Fraction to keep.
        """
        assert 0 < ratio < 1
        selected_ind = np.random.choice(np.arange(0, self.nbr_points()), size=int(self.nbr_points() * ratio))
        self.points = self.points[:, selected_ind]

    def remove_close(self, min_dist: float) -> None:
        """
        Removes points too close within a certain distance from origin from bird view (so dist = sqrt(x^2+y^2)).
        :param min_dist: The distance threshold.
        """
        dist_from_orig = np.linalg.norm(self.points[:2, :], axis=0)
        self.points = self.points[:, dist_from_orig >= min_dist]

    def radius_filter(self, radius: float) -> None:
        """
        Removes points outside the given radius.
        :param radius: Radius in meters.
        """
        keep = np.sqrt(self.points[0] ** 2 + self.points[1] ** 2) <= radius
        self.points = self.points[:, keep]

    def range_filter(self, xrange: Tuple[float, float]=(-np.inf, np.inf), yrange: Tuple[float, float]=(-np.inf, np.inf), zrange: Tuple[float, float]=(-np.inf, np.inf)) -> None:
        """
        Restricts points to specified ranges.
        :param xrange: (xmin, xmax).
        :param yrange: (ymin, ymax).
        :param zrange: (zmin, zmax).
        """
        keep_x = np.logical_and(xrange[0] <= self.points[0], self.points[0] <= xrange[1])
        keep_y = np.logical_and(yrange[0] <= self.points[1], self.points[1] <= yrange[1])
        keep_z = np.logical_and(zrange[0] <= self.points[2], self.points[2] <= zrange[1])
        keep = np.logical_and(keep_x, np.logical_and(keep_y, keep_z))
        self.points = self.points[:, keep]

    def translate(self, x: npt.NDArray[np.float64]) -> None:
        """
        Applies a translation to the point cloud.
        :param x: <np.float: 3,>. Translation in x, y, z.
        """
        self.points[:3] += x.reshape((-1, 1))

    def rotate(self, quaternion: Quaternion) -> None:
        """
        Applies a rotation.
        :param quaternion: Rotation to apply.
        """
        self.points[:3] = np.dot(quaternion.rotation_matrix.astype(np.float32), self.points[:3])

    def transform(self, transf_matrix: npt.NDArray[np.float64]) -> None:
        """
        Applies a homogeneous transform.
        :param transf_matrix: <np.float: 4, 4>. Homogeneous transformation matrix.
        """
        transf_matrix = transf_matrix.astype(np.float32)
        self.points[:3, :] = transf_matrix[:3, :3] @ self.points[:3] + transf_matrix[:3, 3].reshape((-1, 1))

    def scale(self, scale: Tuple[float, float, float]) -> None:
        """
        Scales the lidar xyz coordinates.
        :param scale: The scaling parameter.
        """
        scale_arr = np.array(scale)
        scale_arr.shape = (3, 1)
        self.points[:3, :] *= np.tile(scale_arr, (1, self.nbr_points()))

    def render_image(self, canvas_size: Tuple[int, int]=(1001, 1001), view: npt.NDArray[np.float64]=np.array([[10, 0, 0, 500], [0, 10, 0, 500], [0, 0, 10, 0]]), color_dim: int=2) -> Image.Image:
        """
        Renders pointcloud to an array with 3 channels appropriate for viewing as an image. The image is color coded
        according the color_dim dimension of points (typically the height).
        :param canvas_size: (width, height). Size of the canvas on which to render the image.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param color_dim: The dimension of the points to be visualized as color. Default is 2 for height.
        :return: A Image instance.
        """
        heights = self.points[2, :]
        points = view_points(self.points[:3, :], view, normalize=False)
        points[2, :] = heights
        mask = np.ones(points.shape[1], dtype=bool)
        mask = np.logical_and(mask, points[0, :] < canvas_size[0] - 1)
        mask = np.logical_and(mask, points[0, :] > 0)
        mask = np.logical_and(mask, points[1, :] < canvas_size[1] - 1)
        mask = np.logical_and(mask, points[1, :] > 0)
        points = points[:, mask]
        color_values = points[color_dim, :]
        color_values = 255.0 * (color_values - np.amin(color_values)) / (np.amax(color_values) - np.amin(color_values))
        points = np.int16(np.round(points[:2, :]))
        color_values = np.int16(np.round(color_values))
        cmap = [cm.jet(i / 255, bytes=True)[:3] for i in range(256)]
        render = np.tile(np.expand_dims(np.zeros(canvas_size, dtype=np.uint8), axis=2), [1, 1, 3])
        color_value_array: npt.NDArray[np.float64] = -1 * np.ones(canvas_size, dtype=float)
        for (col, row), color_value in zip(points.T, color_values.T):
            if color_value > color_value_array[row, col]:
                color_value_array[row, col] = color_value
                render[row, col] = cmap[color_value]
        return Image.fromarray(render)

    def render_height(self, ax: axes.Axes, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points colored by height (z-value).
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        self._render_helper(self.points[2, :], ax, view, x_lim, y_lim, marker_size)

    def render_intensity(self, ax: axes.Axes, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points colored by intensity.
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        self._render_helper(self.points[3, :], ax, view, x_lim, y_lim, marker_size)

    def render_label(self, ax: axes.Axes, id2color: Optional[Dict[int, Tuple[float, float, float, float]]]=None, view: npt.NDArray[np.float64]=np.eye(4), x_lim: Tuple[float, float]=(-20, 20), y_lim: Tuple[float, float]=(-20, 20), marker_size: float=1.0) -> None:
        """
        Very simple method that applies a transformation and then scatter plots the points. Each points is colored based
        on labels through the label color mapping, If no mapping provided, we use the rainbow function to assign
        the colors.
        :param id2color: {label_id : (R, G, B, A)}. Id to color mapping where RGBA is within [0, 255].
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        label = self.points[-1]
        colors: Dict[int, Tuple[Any, ...]] = {}
        if id2color is None:
            unique_label = np.unique(label)
            color_rainbow = rainbow(len(unique_label), normalized=True)
            for label_id, c in zip(unique_label, color_rainbow):
                colors[label_id] = c
        else:
            for key, color in id2color.items():
                colors[key] = np.array(color) / 255.0
        color_list = list(map(lambda x: colors.get(x, np.array((1.0, 1.0, 1.0, 0.0))), label))
        self._render_helper(color_list, ax, view, x_lim, y_lim, marker_size)

    def _render_helper(self, colors: Union[npt.NDArray[np.float64], List[npt.NDArray[np.float64]]], ax: axes.Axes, view: npt.NDArray[np.float64], x_lim: Tuple[float, float], y_lim: Tuple[float, float], marker_size: float) -> None:
        """
        Helper function for rendering.
        :param colors: Array-like or list of colors or color input for scatter function.
        :param ax: Axes on which to render the points.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param x_lim: (min, max).
        :param y_lim: (min, max).
        :param marker_size: Marker size.
        """
        points = view_points(self.points[:3, :], view, normalize=False)
        ax.scatter(points[0, :], points[1, :], c=colors, s=marker_size)
        ax.set_xlim(x_lim)
        ax.set_ylim(y_lim)

def render_image(self, canvas_size: Tuple[int, int]=(1001, 1001), view: npt.NDArray[np.float64]=np.array([[10, 0, 0, 500], [0, 10, 0, 500], [0, 0, 10, 0]]), color_dim: int=2) -> Image.Image:
    """
        Renders pointcloud to an array with 3 channels appropriate for viewing as an image. The image is color coded
        according the color_dim dimension of points (typically the height).
        :param canvas_size: (width, height). Size of the canvas on which to render the image.
        :param view: <np.float: n, n>. Defines an arbitrary projection (n <= 4).
        :param color_dim: The dimension of the points to be visualized as color. Default is 2 for height.
        :return: A Image instance.
        """
    heights = self.points[2, :]
    points = view_points(self.points[:3, :], view, normalize=False)
    points[2, :] = heights
    mask = np.ones(points.shape[1], dtype=bool)
    mask = np.logical_and(mask, points[0, :] < canvas_size[0] - 1)
    mask = np.logical_and(mask, points[0, :] > 0)
    mask = np.logical_and(mask, points[1, :] < canvas_size[1] - 1)
    mask = np.logical_and(mask, points[1, :] > 0)
    points = points[:, mask]
    color_values = points[color_dim, :]
    color_values = 255.0 * (color_values - np.amin(color_values)) / (np.amax(color_values) - np.amin(color_values))
    points = np.int16(np.round(points[:2, :]))
    color_values = np.int16(np.round(color_values))
    cmap = [cm.jet(i / 255, bytes=True)[:3] for i in range(256)]
    render = np.tile(np.expand_dims(np.zeros(canvas_size, dtype=np.uint8), axis=2), [1, 1, 3])
    color_value_array: npt.NDArray[np.float64] = -1 * np.ones(canvas_size, dtype=float)
    for (col, row), color_value in zip(points.T, color_values.T):
        if color_value > color_value_array[row, col]:
            color_value_array[row, col] = color_value
            render[row, col] = cmap[color_value]
    return Image.fromarray(render)

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

def _generate_camera_data(db_generation_parameters: DBGenerationParameters, token_dicts: Dict[str, List[Dict[str, Any]]], offset_image_token: int, offset_camera_token: int, offset_ego_pose_token: int) -> None:
    """
    Generate all the mappings for the camera table based on the provided parameters.
    :param db_generation_parameters: The generation parameters to use.
    :param token_dicts: Dicts containing the FK information for each table
    :param offset_image_token: Offset to mark the range of the image tokens
    :param offset_camera_token: Offset to mark the range of the camera tokens
    :param offset_ego_pose_token: Offset to mark the range of the ego pose tokens
    """
    for sensor_idx in range(db_generation_parameters.num_cameras):
        camera_token = offset_camera_token + sensor_idx
        camera_channel_name = f'camera_{sensor_idx}'
        for sensor_data_idx in range(db_generation_parameters.num_sensor_data_per_sensor):
            if sensor_data_idx % db_generation_parameters.num_lidarpc_per_image_ratio == 0:
                ego_pose_token = sensor_data_idx + offset_ego_pose_token
                image_timestamp = sensor_data_idx * 1000000.0
                image_token = sensor_data_idx + sensor_idx * db_generation_parameters.num_sensor_data_per_sensor + offset_image_token
                image_entry = {'image_token': image_token, 'prev_image_token': None if sensor_data_idx == 0 else token_dicts['image'][-1]['image_token'], 'next_image_token': image_token + db_generation_parameters.num_lidarpc_per_image_ratio, 'ego_pose_token': ego_pose_token, 'camera_token': camera_token, 'image_timestamp': image_timestamp + 10 + sensor_idx}
                token_dicts['image'].append(image_entry)
        token_dicts['image'][-1]['next_image_token'] = None
        camera_entry = {'token': camera_token, 'channel': camera_channel_name}
        token_dicts['camera'].append(camera_entry)

class TestTorchMath(unittest.TestCase):
    """
    A class to test the functionality of the scriptable torch math library.
    """

    def test_approximate_derivatives_tensor_functionality(self) -> None:
        """
        Tests the numerical accuracy of approximate_derivatives_tensor.
        """
        input_y = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.float64)
        input_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
        window_length = 3
        poly_order = 2
        deriv_order = 1
        expected_output = torch.tensor([[1, 1, 1, 1, 1]], dtype=torch.float64)
        actual_output = approximate_derivatives_tensor(input_y, input_x, window_length, poly_order, deriv_order)
        torch.testing.assert_allclose(expected_output, actual_output)

    def test_approximate_derivatives_tensor_scripts_properly(self) -> None:
        """
        Tests that approximate_derivatives_tensor scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
                output = approximate_derivatives_tensor(y, x, window_length=3, poly_order=2, deriv_order=1)
                return output
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_y = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.float64)
        test_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
        py_result = to_script.forward(test_x, test_y)
        script_result = scripted.forward(test_x, test_y)
        torch.testing.assert_allclose(py_result, script_result)

    def test_unwrap_functionality(self) -> None:
        """
        Tests that the unwrap function behaves in the same way as np.unwrap
        """
        threshold = 1e-06
        signal = torch.tensor([-math.pi - threshold, -math.pi + threshold, -threshold, 0, threshold, math.pi - threshold, math.pi + threshold], dtype=torch.float64)
        signal_np = torch.from_numpy(np.unwrap(signal.numpy(), axis=-1))
        signal_torch = unwrap(signal, dim=-1)
        self.assertTrue(torch.allclose(signal_np, signal_torch, atol=threshold, rtol=0))

    def test_unwrap_scripts_properly(self) -> None:
        """
        Tests that unwrap scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                output = unwrap(x, dim=-1)
                return output
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
        py_result = to_script.forward(test_x)
        script_result = scripted.forward(test_x)
        torch.testing.assert_allclose(py_result, script_result)

def test_approximate_derivatives_tensor_functionality(self) -> None:
    """
        Tests the numerical accuracy of approximate_derivatives_tensor.
        """
    input_y = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.float64)
    input_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
    window_length = 3
    poly_order = 2
    deriv_order = 1
    expected_output = torch.tensor([[1, 1, 1, 1, 1]], dtype=torch.float64)
    actual_output = approximate_derivatives_tensor(input_y, input_x, window_length, poly_order, deriv_order)
    torch.testing.assert_allclose(expected_output, actual_output)

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        output = unwrap(x, dim=-1)
        return output

def forward(self, x: torch.Tensor) -> torch.Tensor:
    output = unwrap(x, dim=-1)
    return output

def test_approximate_derivatives_tensor_scripts_properly(self) -> None:
    """
        Tests that approximate_derivatives_tensor scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
            output = approximate_derivatives_tensor(y, x, window_length=3, poly_order=2, deriv_order=1)
            return output
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_y = torch.tensor([[1, 2, 3, 4, 5]], dtype=torch.float64)
    test_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
    py_result = to_script.forward(test_x, test_y)
    script_result = scripted.forward(test_x, test_y)
    torch.testing.assert_allclose(py_result, script_result)

def test_unwrap_functionality(self) -> None:
    """
        Tests that the unwrap function behaves in the same way as np.unwrap
        """
    threshold = 1e-06
    signal = torch.tensor([-math.pi - threshold, -math.pi + threshold, -threshold, 0, threshold, math.pi - threshold, math.pi + threshold], dtype=torch.float64)
    signal_np = torch.from_numpy(np.unwrap(signal.numpy(), axis=-1))
    signal_torch = unwrap(signal, dim=-1)
    self.assertTrue(torch.allclose(signal_np, signal_torch, atol=threshold, rtol=0))

def test_unwrap_scripts_properly(self) -> None:
    """
        Tests that unwrap scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            output = unwrap(x, dim=-1)
            return output
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_x = torch.tensor([1, 2, 3, 4, 5], dtype=torch.float64)
    py_result = to_script.forward(test_x)
    script_result = scripted.forward(test_x)
    torch.testing.assert_allclose(py_result, script_result)

def split_blp_lane_segments(nodes: List[StateSE2], lane_seg_num: int) -> List[List[List[float]]]:
    """
    Split baseline path points into series of lane segment coordinate vectors.
    :param nodes: Baseline path nodes to be cut to lane_segments.
    :param lane_seg_num: Number of lane segments to split from baseline path.
    :return obj_coords: Data recording lane segment coordinates in format of [N, 2, 2].
    """
    obj_coords: List[List[List[float]]] = []
    for idx in range(lane_seg_num):
        curr_pt = [nodes[idx].x, nodes[idx].y]
        next_pt = [nodes[idx + 1].x, nodes[idx + 1].y]
        obj_coords.append([curr_pt, next_pt])
    return obj_coords

def connect_blp_lane_segments(start_lane_seg_idx: int, lane_seg_num: int) -> List[Tuple[int, int]]:
    """
    Add connection info for neighboring segments in baseline path.
    :param start_lane_seg_idx: Index for first lane segment in baseline path.
    :param lane_seg_num: Number of lane segments.
    :return obj_conns: Data recording lane-segment connection relations [from_lane_seg_idx, to_lane_seg_idx].
    """
    obj_conns: List[Tuple[int, int]] = []
    for lane_seg_idx in range(start_lane_seg_idx + 1, start_lane_seg_idx + lane_seg_num):
        obj_conns.append((lane_seg_idx - 1, lane_seg_idx))
    return obj_conns

def group_blp_lane_segments(start_lane_seg_idx: int, lane_seg_num: int) -> List[List[int]]:
    """
    Collect lane segment indices across lane/lane connector baseline path.
    :param start_lane_seg_idx: Index for first lane segment in baseline path.
    :param lane_seg_num: Number of lane segments.
    :return obj_groupings: Data recording lane-segment indices associated with given lane/lane connector.
    """
    obj_grouping: List[int] = []
    for lane_seg_idx in range(start_lane_seg_idx, start_lane_seg_idx + lane_seg_num):
        obj_grouping.append(lane_seg_idx)
    return [obj_grouping]

def global_state_se2_tensor_to_local(global_states: torch.Tensor, local_state: torch.Tensor, precision: Optional[torch.dtype]=None) -> torch.Tensor:
    """
    Transforms the StateSE2 in tensor from to the frame of reference in local_frame.

    :param global_states: A tensor of Nx3, where the columns are [x, y, heading].
    :param local_state: A tensor of [x, y, h] of the frame to which to transform.
    :param precision: The precision with which to allocate the intermediate tensors. If None, then it will be inferred from the input precisions.
    :return: The transformed coordinates.
    """
    _validate_state_se2_tensor_shape(global_states, expected_first_dim=2)
    _validate_state_se2_tensor_shape(local_state, expected_first_dim=1)
    if precision is None:
        if global_states.dtype != local_state.dtype:
            raise ValueError('Mixed datatypes provided to coordinates_to_local_frame without precision specifier.')
        precision = global_states.dtype
    local_xform = state_se2_tensor_to_transform_matrix(local_state, precision=precision)
    local_xform_inv = torch.linalg.inv(local_xform)
    transforms = state_se2_tensor_to_transform_matrix_batch(global_states, precision=precision)
    transforms = torch.matmul(local_xform_inv, transforms)
    output = transform_matrix_to_state_se2_tensor_batch(transforms)
    return output

def coordinates_to_local_frame(coords: torch.Tensor, anchor_state: torch.Tensor, precision: Optional[torch.dtype]=None) -> torch.Tensor:
    """
    Transform a set of [x, y] coordinates without heading to the the given frame.
    :param coords: <torch.Tensor: num_coords, 2> Coordinates to be transformed, in the form [x, y].
    :param anchor_state: The coordinate frame to transform to, in the form [x, y, heading].
    :param precision: The precision with which to allocate the intermediate tensors. If None, then it will be inferred from the input precisions.
    :return: <torch.Tensor: num_coords, 2> Transformed coordinates.
    """
    if len(coords.shape) != 2 or coords.shape[1] != 2:
        raise ValueError(f'Unexpected coords shape: {coords.shape}')
    if precision is None:
        if coords.dtype != anchor_state.dtype:
            raise ValueError('Mixed datatypes provided to coordinates_to_local_frame without precision specifier.')
        precision = coords.dtype
    if coords.shape[0] == 0:
        return coords
    transform = state_se2_tensor_to_transform_matrix(anchor_state, precision=precision)
    transform = torch.linalg.inv(transform)
    coords = torch.nn.functional.pad(coords, (0, 1, 0, 0), 'constant', value=1.0)
    coords = torch.matmul(transform, coords.transpose(0, 1))
    result = coords.transpose(0, 1)
    result = result[:, :2]
    return result

def vector_set_coordinates_to_local_frame(coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor, output_precision: Optional[torch.dtype]=torch.float32) -> torch.Tensor:
    """
    Transform the vector set map element coordinates from global frame to ego vehicle frame, as specified by
        anchor_state.
    :param coords: Coordinates to transform. <torch.Tensor: num_elements, num_points, 2>.
    :param avails: Availabilities mask identifying real vs zero-padded data in coords.
        <torch.Tensor: num_elements, num_points>.
    :param anchor_state: The coordinate frame to transform to, in the form [x, y, heading].
    :param output_precision: The precision with which to allocate output tensors.
    :return: Transformed coordinates.
    :raise ValueError: If coordinates dimensions are not valid or don't match availabilities.
    """
    if len(coords.shape) != 3 or coords.shape[2] != 2:
        raise ValueError(f'Unexpected coords shape: {coords.shape}. Expected shape: (*, *, 2)')
    if coords.shape[:2] != avails.shape:
        raise ValueError(f'Mismatching shape between coords and availabilities: {coords.shape[:2]}, {avails.shape}')
    num_map_elements, num_points_per_element, _ = coords.size()
    coords = coords.reshape(num_map_elements * num_points_per_element, 2)
    coords = coordinates_to_local_frame(coords.double(), anchor_state.double(), precision=torch.float64)
    coords = coords.reshape(num_map_elements, num_points_per_element, 2)
    coords = coords.to(output_precision)
    coords[~avails] = 0.0
    return coords

def compute_lateral_displacements(poses: List[StateSE2]) -> List[float]:
    """
    Computes the lateral displacements (y_t - y_t-1) from a list of poses

    :param poses: list of N poses to compute displacements from
    :return: list of N-1 lateral displacements
    """
    return [poses[idx].y - poses[idx - 1].y for idx in range(1, len(poses))]

class TestTorchGeometry(unittest.TestCase):
    """
    A class for testing the functionality of the torch geometry library.
    """

    def test_transform_matrix_conversion_functionality(self) -> None:
        """
        Test the numerical accuracy of the transform matrix conversion utilities.
        """
        initial_state = torch.tensor([5, 6, math.pi / 2], dtype=torch.float32)
        expected_xform_matrix = torch.tensor([[0, -1, 5], [1, 0, 6], [0, 0, 1]], dtype=torch.float32)
        xform_matrix = state_se2_tensor_to_transform_matrix(initial_state, precision=torch.float32)
        torch.testing.assert_allclose(expected_xform_matrix, xform_matrix)
        reverted = transform_matrix_to_state_se2_tensor(xform_matrix, precision=torch.float32)
        torch.testing.assert_allclose(initial_state, reverted)

    def test_transform_matrix_scriptability(self) -> None:
        """
        Tests that the transform matrix conversion utilities script properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                xform = state_se2_tensor_to_transform_matrix(x)
                result = transform_matrix_to_state_se2_tensor(xform)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_input = torch.tensor([1, 2, 3], dtype=torch.float32)
        py_result = to_script.forward(test_input)
        script_result = scripted.forward(test_input)
        torch.testing.assert_allclose(py_result, script_result)

    def test_transform_matrix_batch_conversion_functionality(self) -> None:
        """
        Test the numerical accuracy of the transform matrix conversion utilities.
        """
        initial_state = torch.tensor([[5, 6, math.pi / 2]], dtype=torch.float32)
        expected_xform_matrix = torch.tensor([[[0, -1, 5], [1, 0, 6], [0, 0, 1]]], dtype=torch.float32)
        xform_matrix = state_se2_tensor_to_transform_matrix_batch(initial_state, precision=torch.float32)
        torch.testing.assert_allclose(expected_xform_matrix, xform_matrix)
        reverted = transform_matrix_to_state_se2_tensor_batch(xform_matrix)
        torch.testing.assert_allclose(initial_state, reverted)
        with self.assertRaises(ValueError):
            misshaped_tensor = torch.tensor([1, 2, 3], dtype=torch.float32)
            state_se2_tensor_to_transform_matrix_batch(misshaped_tensor)

    def test_transform_matrix_batch_scriptability(self) -> None:
        """
        Tests that the transform matrix conversion utilities script properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                xform = state_se2_tensor_to_transform_matrix_batch(x)
                result = transform_matrix_to_state_se2_tensor_batch(xform)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_input = torch.tensor([[1, 2, 3]], dtype=torch.float32)
        py_result = to_script.forward(test_input)
        script_result = scripted.forward(test_input)
        torch.testing.assert_allclose(py_result, script_result)

    def test_global_state_se2_tensor_to_local_functionality(self) -> None:
        """
        Tests the numerical accuracy of global_state_se2_tensor_to_local.
        """
        '\n           o = coordinates to transform, facing direction >\n           # = local reference frame\n           y_world\n            ^              x_local\n            |               ^\n            |               |\n            |   y_local <---#\n            |\n            |\n            |\n         o  |  o>\n         V  |\n            |\n            *---------------------> x_world\n               ^\n        <o     o\n\n        '
        global_states = torch.tensor([[1, 1, 0], [1, -1, math.pi / 2], [-1, -1, math.pi], [-1, 1, -math.pi / 2]], dtype=torch.float32)
        local_state = torch.tensor([5, 5, math.pi / 2], dtype=torch.float32)
        expected_transformed_states = torch.tensor([[-4, 4, -math.pi / 2], [-6, 4, 0], [-6, 6, math.pi / 2], [-4, 6, math.pi]], dtype=torch.float32)
        actual_transformed_states = global_state_se2_tensor_to_local(global_states, local_state, precision=torch.float32)
        torch.testing.assert_allclose(expected_transformed_states, actual_transformed_states)

    def test_global_state_se2_tensor_to_local_scriptability(self) -> None:
        """
        Tests that global_state_se2_tensor_to_local scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, states: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
                result = global_state_se2_tensor_to_local(states, pose)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_states = torch.tensor([[1, 2, 3], [4, 5, 6]], dtype=torch.float32)
        test_pose = torch.tensor([1, 2, 3], dtype=torch.float32)
        py_result = to_script.forward(test_states, test_pose)
        script_result = scripted.forward(test_states, test_pose)
        torch.testing.assert_allclose(py_result, script_result)

    def test_coordinates_to_local_frame_functionality(self) -> None:
        """
        Tests the numerical accuracy of coordinates_to_local_frame.
        """
        '\n           o = coordinates to transform\n           # = local reference frame\n           y_world\n            ^              x_local\n            |               ^\n            |               |\n            |   y_local <---#\n            |\n            |\n            |\n         o  |  o\n            |\n            |\n            *---------------------> x_world\n\n         o     o\n\n        '
        coordinates = torch.tensor([[1, 1], [1, -1], [-1, -1], [-1, 1]], dtype=torch.float32)
        local_state = torch.tensor([5, 5, math.pi / 2], dtype=torch.float32)
        expected_coordinates = torch.tensor([[-4, 4], [-6, 4], [-6, 6], [-4, 6]], dtype=torch.float32)
        actual_coordinates = coordinates_to_local_frame(coordinates, local_state, precision=torch.float32)
        torch.testing.assert_allclose(expected_coordinates, actual_coordinates)

    def test_coordinates_to_local_frame_scriptability(self) -> None:
        """
        Tests that the function coordinates_to_local_frame scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, states: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
                result = coordinates_to_local_frame(states, pose, precision=torch.float32)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_states = torch.tensor([[1, 2], [4, 5]], dtype=torch.float32)
        test_pose = torch.tensor([1, 2, 3], dtype=torch.float32)
        py_result = to_script.forward(test_states, test_pose)
        script_result = scripted.forward(test_states, test_pose)
        torch.testing.assert_allclose(py_result, script_result)

    def test_vector_set_coordinates_to_local_frame_functionality(self) -> None:
        """
        Test converting vector set map coordinates from global to local ego frame.
        """
        coords = torch.tensor([[[1, 1], [3, 1], [5, 1]]], dtype=torch.float64)
        avails = torch.ones(coords.shape[:2], dtype=torch.bool)
        anchor_state = torch.tensor([0, 0, 0], dtype=torch.float64)
        result_coords = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
        self.assertIsInstance(result_coords, torch.FloatTensor)
        self.assertEqual(result_coords.shape, coords.shape)
        torch.testing.assert_allclose(coords.float(), result_coords)
        with self.assertRaises(ValueError):
            vector_set_coordinates_to_local_frame(coords[0], avails[0], anchor_state)
        with self.assertRaises(ValueError):
            vector_set_coordinates_to_local_frame(coords, avails[0], anchor_state)

    def test_vector_set_coordinates_to_local_frame_scriptability(self) -> None:
        """
        Tests that the function vector_set_coordinates_to_local_frame scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor) -> torch.Tensor:
                result = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_coords = torch.tensor([[[1, 1], [3, 1], [5, 1]]], dtype=torch.float64)
        test_avails = torch.ones(test_coords.shape[:2], dtype=torch.bool)
        test_anchor_state = torch.tensor([0, 0, 0], dtype=torch.float64)
        py_result = to_script.forward(test_coords, test_avails, test_anchor_state)
        script_result = scripted.forward(test_coords, test_avails, test_anchor_state)
        torch.testing.assert_allclose(py_result, script_result)

def test_transform_matrix_conversion_functionality(self) -> None:
    """
        Test the numerical accuracy of the transform matrix conversion utilities.
        """
    initial_state = torch.tensor([5, 6, math.pi / 2], dtype=torch.float32)
    expected_xform_matrix = torch.tensor([[0, -1, 5], [1, 0, 6], [0, 0, 1]], dtype=torch.float32)
    xform_matrix = state_se2_tensor_to_transform_matrix(initial_state, precision=torch.float32)
    torch.testing.assert_allclose(expected_xform_matrix, xform_matrix)
    reverted = transform_matrix_to_state_se2_tensor(xform_matrix, precision=torch.float32)
    torch.testing.assert_allclose(initial_state, reverted)

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor) -> torch.Tensor:
        result = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
        return result

def forward(self, coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor) -> torch.Tensor:
    result = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
    return result

def test_transform_matrix_scriptability(self) -> None:
    """
        Tests that the transform matrix conversion utilities script properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            xform = state_se2_tensor_to_transform_matrix(x)
            result = transform_matrix_to_state_se2_tensor(xform)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_input = torch.tensor([1, 2, 3], dtype=torch.float32)
    py_result = to_script.forward(test_input)
    script_result = scripted.forward(test_input)
    torch.testing.assert_allclose(py_result, script_result)

def test_transform_matrix_batch_conversion_functionality(self) -> None:
    """
        Test the numerical accuracy of the transform matrix conversion utilities.
        """
    initial_state = torch.tensor([[5, 6, math.pi / 2]], dtype=torch.float32)
    expected_xform_matrix = torch.tensor([[[0, -1, 5], [1, 0, 6], [0, 0, 1]]], dtype=torch.float32)
    xform_matrix = state_se2_tensor_to_transform_matrix_batch(initial_state, precision=torch.float32)
    torch.testing.assert_allclose(expected_xform_matrix, xform_matrix)
    reverted = transform_matrix_to_state_se2_tensor_batch(xform_matrix)
    torch.testing.assert_allclose(initial_state, reverted)
    with self.assertRaises(ValueError):
        misshaped_tensor = torch.tensor([1, 2, 3], dtype=torch.float32)
        state_se2_tensor_to_transform_matrix_batch(misshaped_tensor)

def test_transform_matrix_batch_scriptability(self) -> None:
    """
        Tests that the transform matrix conversion utilities script properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            xform = state_se2_tensor_to_transform_matrix_batch(x)
            result = transform_matrix_to_state_se2_tensor_batch(xform)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_input = torch.tensor([[1, 2, 3]], dtype=torch.float32)
    py_result = to_script.forward(test_input)
    script_result = scripted.forward(test_input)
    torch.testing.assert_allclose(py_result, script_result)

def test_global_state_se2_tensor_to_local_functionality(self) -> None:
    """
        Tests the numerical accuracy of global_state_se2_tensor_to_local.
        """
    '\n           o = coordinates to transform, facing direction >\n           # = local reference frame\n           y_world\n            ^              x_local\n            |               ^\n            |               |\n            |   y_local <---#\n            |\n            |\n            |\n         o  |  o>\n         V  |\n            |\n            *---------------------> x_world\n               ^\n        <o     o\n\n        '
    global_states = torch.tensor([[1, 1, 0], [1, -1, math.pi / 2], [-1, -1, math.pi], [-1, 1, -math.pi / 2]], dtype=torch.float32)
    local_state = torch.tensor([5, 5, math.pi / 2], dtype=torch.float32)
    expected_transformed_states = torch.tensor([[-4, 4, -math.pi / 2], [-6, 4, 0], [-6, 6, math.pi / 2], [-4, 6, math.pi]], dtype=torch.float32)
    actual_transformed_states = global_state_se2_tensor_to_local(global_states, local_state, precision=torch.float32)
    torch.testing.assert_allclose(expected_transformed_states, actual_transformed_states)

def test_global_state_se2_tensor_to_local_scriptability(self) -> None:
    """
        Tests that global_state_se2_tensor_to_local scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, states: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
            result = global_state_se2_tensor_to_local(states, pose)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_states = torch.tensor([[1, 2, 3], [4, 5, 6]], dtype=torch.float32)
    test_pose = torch.tensor([1, 2, 3], dtype=torch.float32)
    py_result = to_script.forward(test_states, test_pose)
    script_result = scripted.forward(test_states, test_pose)
    torch.testing.assert_allclose(py_result, script_result)

def test_coordinates_to_local_frame_functionality(self) -> None:
    """
        Tests the numerical accuracy of coordinates_to_local_frame.
        """
    '\n           o = coordinates to transform\n           # = local reference frame\n           y_world\n            ^              x_local\n            |               ^\n            |               |\n            |   y_local <---#\n            |\n            |\n            |\n         o  |  o\n            |\n            |\n            *---------------------> x_world\n\n         o     o\n\n        '
    coordinates = torch.tensor([[1, 1], [1, -1], [-1, -1], [-1, 1]], dtype=torch.float32)
    local_state = torch.tensor([5, 5, math.pi / 2], dtype=torch.float32)
    expected_coordinates = torch.tensor([[-4, 4], [-6, 4], [-6, 6], [-4, 6]], dtype=torch.float32)
    actual_coordinates = coordinates_to_local_frame(coordinates, local_state, precision=torch.float32)
    torch.testing.assert_allclose(expected_coordinates, actual_coordinates)

def test_coordinates_to_local_frame_scriptability(self) -> None:
    """
        Tests that the function coordinates_to_local_frame scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, states: torch.Tensor, pose: torch.Tensor) -> torch.Tensor:
            result = coordinates_to_local_frame(states, pose, precision=torch.float32)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_states = torch.tensor([[1, 2], [4, 5]], dtype=torch.float32)
    test_pose = torch.tensor([1, 2, 3], dtype=torch.float32)
    py_result = to_script.forward(test_states, test_pose)
    script_result = scripted.forward(test_states, test_pose)
    torch.testing.assert_allclose(py_result, script_result)

def test_vector_set_coordinates_to_local_frame_functionality(self) -> None:
    """
        Test converting vector set map coordinates from global to local ego frame.
        """
    coords = torch.tensor([[[1, 1], [3, 1], [5, 1]]], dtype=torch.float64)
    avails = torch.ones(coords.shape[:2], dtype=torch.bool)
    anchor_state = torch.tensor([0, 0, 0], dtype=torch.float64)
    result_coords = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
    self.assertIsInstance(result_coords, torch.FloatTensor)
    self.assertEqual(result_coords.shape, coords.shape)
    torch.testing.assert_allclose(coords.float(), result_coords)
    with self.assertRaises(ValueError):
        vector_set_coordinates_to_local_frame(coords[0], avails[0], anchor_state)
    with self.assertRaises(ValueError):
        vector_set_coordinates_to_local_frame(coords, avails[0], anchor_state)

def test_vector_set_coordinates_to_local_frame_scriptability(self) -> None:
    """
        Tests that the function vector_set_coordinates_to_local_frame scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor) -> torch.Tensor:
            result = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_coords = torch.tensor([[[1, 1], [3, 1], [5, 1]]], dtype=torch.float64)
    test_avails = torch.ones(test_coords.shape[:2], dtype=torch.bool)
    test_anchor_state = torch.tensor([0, 0, 0], dtype=torch.float64)
    py_result = to_script.forward(test_coords, test_avails, test_anchor_state)
    script_result = scripted.forward(test_coords, test_avails, test_anchor_state)
    torch.testing.assert_allclose(py_result, script_result)

def to_scene_trajectory_from_list_ego_state(trajectory: List[EgoState], color: Color) -> Trajectory:
    """
    Convert list of ego states and a color into a scene structure for a trajectory.
    :param trajectory: a list of states.
    :param color: color [R, G, B, A].
    :return: Trajectory in scene format.
    """
    trajectory_states = [to_scene_trajectory_state_from_ego_state(state) for state in trajectory]
    return Trajectory(color=color, states=trajectory_states)

def to_scene_trajectory_from_list_waypoint(trajectory: List[Waypoint], color: Color) -> Trajectory:
    """
    Convert list of waypoints and a color into a scene structure for a trajectory.
    :param trajectory: a list of states.
    :param color: color [R, G, B, A].
    :return: Trajectory in scene format.
    """
    trajectory_states = [to_scene_trajectory_state_from_waypoint(state) for state in trajectory]
    return Trajectory(color=color, states=trajectory_states)

def function_to_load_model(dummy_var: Any) -> Tuple[bool, int]:
    """
    Dummy function
    return: gpu_available, num_threads avaialble for torch
    """
    model = RasterModel(feature_builders=[], target_builders=[], model_name='resnet50', pretrained=True, num_input_channels=4, num_features_per_pose=3, future_trajectory_sampling=TrajectorySampling(num_poses=10, time_horizon=5))
    gpu_available = torch.cuda.is_available()
    device = torch.device('cuda' if gpu_available else 'cpu')
    model.to(device)
    sleep(1)
    return (gpu_available, torch.get_num_threads())

class SequentialLR(_LRScheduler):
    """
    Receives the list of schedulers that is expected to be called sequentially during
    optimization process and milestone points that provides exact intervals to reflect
    which scheduler is supposed to be called at a given epoch.

    Args:
        optimizer (Optimizer): Wrapped optimizer.
        schedulers (list): List of chained schedulers.
        milestones (list): List of integers that reflects milestone points.
        last_epoch (int): The index of last epoch. Default: -1.
        verbose (bool): Does nothing.

    Example:
        >>> # Assuming optimizer uses lr = 1. for all groups
        >>> # lr = 0.1     if epoch == 0
        >>> # lr = 0.1     if epoch == 1
        >>> # lr = 0.9     if epoch == 2
        >>> # lr = 0.81    if epoch == 3
        >>> # lr = 0.729   if epoch == 4
        >>> scheduler1 = ConstantLR(self.opt, factor=0.1, total_iters=2)
        >>> scheduler2 = ExponentialLR(self.opt, gamma=0.9)
        >>> scheduler = SequentialLR(self.opt, schedulers=[scheduler1, scheduler2], milestones=[2])
        >>> for epoch in range(100):
        >>>     train(...)
        >>>     validate(...)
        >>>     scheduler.step()
    """

    def __init__(self, optimizer: Optimizer, schedulers: List[_LRScheduler], milestones: List[int], last_epoch: int=-1, verbose: bool=False) -> None:
        """
        Initialise sequential learning rate scheduler.
        """
        for scheduler_idx in range(len(schedulers)):
            if schedulers[scheduler_idx].optimizer != optimizer:
                raise ValueError(f'Sequential Schedulers expects all schedulers to belong to the same optimizer, but got schedulers at index {scheduler_idx} to be different than the optimizer passed in.')
            if schedulers[scheduler_idx].optimizer != schedulers[0].optimizer:
                raise ValueError(f'Sequential Schedulers expects all schedulers to belong to the same optimizer, but got schedulers at index {0} and {scheduler_idx} to be different.')
        if len(milestones) != len(schedulers) - 1:
            raise ValueError('Sequential Schedulers expects number of schedulers provided to be one more than the number of milestone points, but got number of schedulers {} and the number of milestones to be equal to {}'.format(len(schedulers), len(milestones)))
        self.optimizer = optimizer
        self.last_epoch = last_epoch + 1
        self._milestones = milestones + [sys.maxsize]
        self._schedulers = schedulers
        self._current_scheduler_index = 0

    def step(self) -> None:
        """
        Advance a single step in the learning rate schedule.
        """
        self.last_epoch += 1
        if self.last_epoch > self._milestones[self._current_scheduler_index]:
            self._current_scheduler_index += 1
        self._schedulers[self._current_scheduler_index].step()
        self._last_lr = self._schedulers[self._current_scheduler_index].get_last_lr()

    def state_dict(self) -> Dict[str, Any]:
        """
        Returns the state of the scheduler as a :class:`dict`.

        It contains an entry for every variable in self.__dict__ which
        is not the optimizer.
        The wrapped scheduler states will also be saved.
        :return: State dict of scheduler
        """
        state_dict = {key: value for key, value in self.__dict__.items() if key not in ('optimizer', '_schedulers')}
        state_dict['_schedulers'] = [None] * len(self._schedulers)
        for idx, s in enumerate(self._schedulers):
            state_dict['_schedulers'][idx] = s.state_dict()
        return state_dict

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """
        Loads the schedulers state.
        :param state_dict: Scheduler state. should be an object returned from a call to :meth:`state_dict`
        """
        _schedulers = state_dict.pop('_schedulers')
        self.__dict__.update(state_dict)
        state_dict['_schedulers'] = _schedulers
        for idx, s in enumerate(_schedulers):
            self._schedulers[idx].load_state_dict(s)

def step(self) -> None:
    """
        Advance a single step in the learning rate schedule.
        """
    self.last_epoch += 1
    if self.last_epoch > self._milestones[self._current_scheduler_index]:
        self._current_scheduler_index += 1
    self._schedulers[self._current_scheduler_index].step()
    self._last_lr = self._schedulers[self._current_scheduler_index].get_last_lr()

class TestSequentialLRScheduler(unittest.TestCase):
    """Test update_distributed_optimizer_config function."""
    world_size = 4

    def setUp(self) -> None:
        """Set up schedulers and optimizer"""
        self.optimizer = Adam(params=[torch.tensor([1.0])], lr=0.0001)
        self.total_steps = 300
        self.milestones = [100, 200]
        self.scheduler3 = LambdaLR(self.optimizer, lambda step: 1)
        self.scheduler2 = LambdaLR(self.optimizer, self._get_mock_linear_func())
        self.scheduler1 = LambdaLR(self.optimizer, self._get_mock_linear_func())
        self.schedulers = [self.scheduler1, self.scheduler2, self.scheduler3]
        self.expected_lrs = [1e-06, 0.0001, 0.0001, 0.0001]

    def _get_mock_linear_func(self) -> Callable[..., float]:
        """Gets mock linear function"""

        def _linear_func(step: int) -> float:
            num_steps = self.milestones[1] - self.milestones[0]
            return step / num_steps if step <= num_steps else 1.0
        return _linear_func

    def _get_lr_from_optimizer(self, optimizer: torch.optim.Optimizer) -> float:
        lr: float
        for param_group in optimizer.param_groups:
            lr = param_group['lr']
            break
        return lr

    def test_sequential_lr_with_multiple_schedulers(self) -> None:
        """Tests that SequentialLR Scheduler works with multiple schedulers."""
        sequential_lr_scheduler = SequentialLR(self.optimizer, self.schedulers, self.milestones)
        lr = []
        self.assertAlmostEqual(self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer), 0.0)
        for i in range(self.total_steps):
            sequential_lr_scheduler.step()
            print(i + 1, self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer))
            lr.append(self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer))
        self.assertAlmostEqual(lr[0], self.expected_lrs[0])
        self.assertAlmostEqual(lr[self.milestones[0] - 1], self.expected_lrs[1])
        self.assertAlmostEqual(lr[self.milestones[1] - 1], self.expected_lrs[2])
        self.assertAlmostEqual(lr[-1], self.expected_lrs[-1])

def setUp(self) -> None:
    """Set up schedulers and optimizer"""
    self.optimizer = Adam(params=[torch.tensor([1.0])], lr=0.0001)
    self.total_steps = 300
    self.milestones = [100, 200]
    self.scheduler3 = LambdaLR(self.optimizer, lambda step: 1)
    self.scheduler2 = LambdaLR(self.optimizer, self._get_mock_linear_func())
    self.scheduler1 = LambdaLR(self.optimizer, self._get_mock_linear_func())
    self.schedulers = [self.scheduler1, self.scheduler2, self.scheduler3]
    self.expected_lrs = [1e-06, 0.0001, 0.0001, 0.0001]

def test_sequential_lr_with_multiple_schedulers(self) -> None:
    """Tests that SequentialLR Scheduler works with multiple schedulers."""
    sequential_lr_scheduler = SequentialLR(self.optimizer, self.schedulers, self.milestones)
    lr = []
    self.assertAlmostEqual(self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer), 0.0)
    for i in range(self.total_steps):
        sequential_lr_scheduler.step()
        print(i + 1, self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer))
        lr.append(self._get_lr_from_optimizer(sequential_lr_scheduler.optimizer))
    self.assertAlmostEqual(lr[0], self.expected_lrs[0])
    self.assertAlmostEqual(lr[self.milestones[0] - 1], self.expected_lrs[1])
    self.assertAlmostEqual(lr[self.milestones[1] - 1], self.expected_lrs[2])
    self.assertAlmostEqual(lr[-1], self.expected_lrs[-1])

class LQRTracker(AbstractTracker):
    """
    Implements an LQR tracker for a kinematic bicycle model.

    We decouple into two subsystems, longitudinal and lateral, with small angle approximations for linearization.
    We then solve two sequential LQR subproblems to find acceleration and steering rate inputs.

    Longitudinal Subsystem:
        States: [velocity]
        Inputs: [acceleration]
        Dynamics (continuous time):
            velocity_dot = acceleration

    Lateral Subsystem (After Linearization/Small Angle Approximation):
        States: [lateral_error, heading_error, steering_angle]
        Inputs: [steering_rate]
        Parameters: [velocity, curvature]
        Dynamics (continuous time):
            lateral_error_dot  = velocity * heading_error
            heading_error_dot  = velocity * (steering_angle / wheelbase_length - curvature)
            steering_angle_dot = steering_rate

    The continuous time dynamics are discretized using Euler integration and zero-order-hold on the input.
    In case of a stopping reference, we use a simplified stopping P controller instead of LQR.

    The final control inputs passed on to the motion model are:
        - acceleration
        - steering_rate
    """

    def __init__(self, q_longitudinal: npt.NDArray[np.float64], r_longitudinal: npt.NDArray[np.float64], q_lateral: npt.NDArray[np.float64], r_lateral: npt.NDArray[np.float64], discretization_time: float, tracking_horizon: int, jerk_penalty: float, curvature_rate_penalty: float, stopping_proportional_gain: float, stopping_velocity: float, vehicle: VehicleParameters=get_pacifica_parameters()):
        """
        Constructor for LQR controller
        :param q_longitudinal: The weights for the Q matrix for the longitudinal subystem.
        :param r_longitudinal: The weights for the R matrix for the longitudinal subystem.
        :param q_lateral: The weights for the Q matrix for the lateral subystem.
        :param r_lateral: The weights for the R matrix for the lateral subystem.
        :param discretization_time: [s] The time interval used for discretizing the continuous time dynamics.
        :param tracking_horizon: How many discrete time steps ahead to consider for the LQR objective.
        :param stopping_proportional_gain: The proportional_gain term for the P controller when coming to a stop.
        :param stopping_velocity: [m/s] The velocity below which we are deemed to be stopping and we don't use LQR.
        :param vehicle: Vehicle parameters
        """
        assert len(q_longitudinal) == 1, 'q_longitudinal should have 1 element (velocity).'
        assert len(r_longitudinal) == 1, 'r_longitudinal should have 1 element (acceleration).'
        self._q_longitudinal: npt.NDArray[np.float64] = np.diag(q_longitudinal)
        self._r_longitudinal: npt.NDArray[np.float64] = np.diag(r_longitudinal)
        assert len(q_lateral) == 3, 'q_lateral should have 3 elements (lateral_error, heading_error, steering_angle).'
        assert len(r_lateral) == 1, 'r_lateral should have 1 element (steering_rate).'
        self._q_lateral: npt.NDArray[np.float64] = np.diag(q_lateral)
        self._r_lateral: npt.NDArray[np.float64] = np.diag(r_lateral)
        for attr in ['_q_lateral', '_q_longitudinal']:
            assert np.all(np.diag(getattr(self, attr)) >= 0.0), f'self.{attr} must be positive semidefinite.'
        for attr in ['_r_lateral', '_r_longitudinal']:
            assert np.all(np.diag(getattr(self, attr)) > 0.0), f'self.{attr} must be positive definite.'
        assert discretization_time > 0.0, 'The discretization_time should be positive.'
        assert tracking_horizon > 1, 'We expect the horizon to be greater than 1 - else steering_rate has no impact with Euler integration.'
        self._discretization_time = discretization_time
        self._tracking_horizon = tracking_horizon
        self._wheel_base = vehicle.wheel_base
        assert jerk_penalty > 0.0, 'The jerk penalty must be positive.'
        assert curvature_rate_penalty > 0.0, 'The curvature rate penalty must be positive.'
        self._jerk_penalty = jerk_penalty
        self._curvature_rate_penalty = curvature_rate_penalty
        assert stopping_proportional_gain > 0, 'stopping_proportional_gain has to be greater than 0.'
        assert stopping_velocity > 0, 'stopping_velocity has to be greater than 0.'
        self._stopping_proportional_gain = stopping_proportional_gain
        self._stopping_velocity = stopping_velocity

    def track_trajectory(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, initial_state: EgoState, trajectory: AbstractTrajectory) -> DynamicCarState:
        """Inherited, see superclass."""
        initial_velocity, initial_lateral_state_vector = self._compute_initial_velocity_and_lateral_state(current_iteration, initial_state, trajectory)
        reference_velocity, curvature_profile = self._compute_reference_velocity_and_curvature_profile(current_iteration, trajectory)
        should_stop = reference_velocity <= self._stopping_velocity and initial_velocity <= self._stopping_velocity
        if should_stop:
            accel_cmd, steering_rate_cmd = self._stopping_controller(initial_velocity, reference_velocity)
        else:
            accel_cmd = self._longitudinal_lqr_controller(initial_velocity, reference_velocity)
            velocity_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_velocity, derivatives=np.ones(self._tracking_horizon, dtype=np.float64) * accel_cmd, discretization_time=self._discretization_time)[:self._tracking_horizon]
            steering_rate_cmd = self._lateral_lqr_controller(initial_lateral_state_vector, velocity_profile, curvature_profile)
        return DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=initial_state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=initial_state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel_cmd, 0), tire_steering_rate=steering_rate_cmd)

    def _compute_initial_velocity_and_lateral_state(self, current_iteration: SimulationIteration, initial_state: EgoState, trajectory: AbstractTrajectory) -> Tuple[float, npt.NDArray[np.float64]]:
        """
        This method projects the initial tracking error into vehicle/Frenet frame.  It also extracts initial velocity.
        :param current_iteration: Used to get the current time.
        :param initial_state: The current state for ego.
        :param trajectory: The reference trajectory we are tracking.
        :return: Initial velocity [m/s] and initial lateral state.
        """
        initial_trajectory_state = trajectory.get_state_at_time(current_iteration.time_point)
        x_error = initial_state.rear_axle.x - initial_trajectory_state.rear_axle.x
        y_error = initial_state.rear_axle.y - initial_trajectory_state.rear_axle.y
        heading_reference = initial_trajectory_state.rear_axle.heading
        lateral_error = -x_error * np.sin(heading_reference) + y_error * np.cos(heading_reference)
        heading_error = angle_diff(initial_state.rear_axle.heading, heading_reference, 2 * np.pi)
        initial_velocity = initial_state.dynamic_car_state.rear_axle_velocity_2d.x
        initial_lateral_state_vector: npt.NDArray[np.float64] = np.array([lateral_error, heading_error, initial_state.tire_steering_angle], dtype=np.float64)
        return (initial_velocity, initial_lateral_state_vector)

    def _compute_reference_velocity_and_curvature_profile(self, current_iteration: SimulationIteration, trajectory: AbstractTrajectory) -> Tuple[float, npt.NDArray[np.float64]]:
        """
        This method computes reference velocity and curvature profile based on the reference trajectory.
        We use a lookahead time equal to self._tracking_horizon * self._discretization_time.
        :param current_iteration: Used to get the current time.
        :param trajectory: The reference trajectory we are tracking.
        :return: The reference velocity [m/s] and curvature profile [rad] to track.
        """
        times_s, poses = get_interpolated_reference_trajectory_poses(trajectory, self._discretization_time)
        velocity_profile, acceleration_profile, curvature_profile, curvature_rate_profile = get_velocity_curvature_profiles_with_derivatives_from_poses(discretization_time=self._discretization_time, poses=poses, jerk_penalty=self._jerk_penalty, curvature_rate_penalty=self._curvature_rate_penalty)
        reference_time = current_iteration.time_point.time_s + self._tracking_horizon * self._discretization_time
        reference_velocity = np.interp(reference_time, times_s[:-1], velocity_profile)
        profile_times = [current_iteration.time_point.time_s + x * self._discretization_time for x in range(self._tracking_horizon)]
        reference_curvature_profile = np.interp(profile_times, times_s[:-1], curvature_profile)
        return (float(reference_velocity), reference_curvature_profile)

    def _stopping_controller(self, initial_velocity: float, reference_velocity: float) -> Tuple[float, float]:
        """
        Apply proportional controller when at near-stop conditions.
        :param initial_velocity: [m/s] The current velocity of ego.
        :param reference_velocity: [m/s] The reference velocity to track.
        :return: Acceleration [m/s^2] and zero steering_rate [rad/s] command.
        """
        accel = -self._stopping_proportional_gain * (initial_velocity - reference_velocity)
        return (accel, 0.0)

    def _longitudinal_lqr_controller(self, initial_velocity: float, reference_velocity: float) -> float:
        """
        This longitudinal controller determines an acceleration input to minimize velocity error at a lookahead time.
        :param initial_velocity: [m/s] The current velocity of ego.
        :param reference_velocity: [m/s] The reference_velocity to track at a lookahead time.
        :return: Acceleration [m/s^2] command based on LQR.
        """
        A: npt.NDArray[np.float64] = np.array([1.0], dtype=np.float64)
        B: npt.NDArray[np.float64] = np.array([self._tracking_horizon * self._discretization_time], dtype=np.float64)
        accel_cmd = self._solve_one_step_lqr(initial_state=np.array([initial_velocity], dtype=np.float64), reference_state=np.array([reference_velocity], dtype=np.float64), Q=self._q_longitudinal, R=self._r_longitudinal, A=A, B=B, g=np.zeros(1, dtype=np.float64), angle_diff_indices=[])
        return float(accel_cmd)

    def _lateral_lqr_controller(self, initial_lateral_state_vector: npt.NDArray[np.float64], velocity_profile: npt.NDArray[np.float64], curvature_profile: npt.NDArray[np.float64]) -> float:
        """
        This lateral controller determines a steering_rate input to minimize lateral errors at a lookahead time.
        It requires a velocity sequence as a parameter to ensure linear time-varying lateral dynamics.
        :param initial_lateral_state_vector: The current lateral state of ego.
        :param velocity_profile: [m/s] The velocity over the entire self._tracking_horizon-step lookahead.
        :param curvature_profile: [rad] The curvature over the entire self._tracking_horizon-step lookahead..
        :return: Steering rate [rad/s] command based on LQR.
        """
        assert len(velocity_profile) == self._tracking_horizon, f'The linearization velocity sequence should have length {self._tracking_horizon} but is {len(velocity_profile)}.'
        assert len(curvature_profile) == self._tracking_horizon, f'The linearization curvature sequence should have length {self._tracking_horizon} but is {len(curvature_profile)}.'
        n_lateral_states = len(LateralStateIndex)
        I: npt.NDArray[np.float64] = np.eye(n_lateral_states, dtype=np.float64)
        A: npt.NDArray[np.float64] = I
        B: npt.NDArray[np.float64] = np.zeros((n_lateral_states, 1), dtype=np.float64)
        g: npt.NDArray[np.float64] = np.zeros(n_lateral_states, dtype=np.float64)
        idx_lateral_error = LateralStateIndex.LATERAL_ERROR
        idx_heading_error = LateralStateIndex.HEADING_ERROR
        idx_steering_angle = LateralStateIndex.STEERING_ANGLE
        input_matrix: npt.NDArray[np.float64] = np.zeros((n_lateral_states, 1), np.float64)
        input_matrix[idx_steering_angle] = self._discretization_time
        for index_step, (velocity, curvature) in enumerate(zip(velocity_profile, curvature_profile)):
            state_matrix_at_step: npt.NDArray[np.float64] = np.eye(n_lateral_states, dtype=np.float64)
            state_matrix_at_step[idx_lateral_error, idx_heading_error] = velocity * self._discretization_time
            state_matrix_at_step[idx_heading_error, idx_steering_angle] = velocity * self._discretization_time / self._wheel_base
            affine_term: npt.NDArray[np.float64] = np.zeros(n_lateral_states, dtype=np.float64)
            affine_term[idx_heading_error] = -velocity * curvature * self._discretization_time
            A = state_matrix_at_step @ A
            B = state_matrix_at_step @ B + input_matrix
            g = state_matrix_at_step @ g + affine_term
        steering_rate_cmd = self._solve_one_step_lqr(initial_state=initial_lateral_state_vector, reference_state=np.zeros(n_lateral_states, dtype=np.float64), Q=self._q_lateral, R=self._r_lateral, A=A, B=B, g=g, angle_diff_indices=[idx_heading_error, idx_steering_angle])
        return float(steering_rate_cmd)

    @staticmethod
    def _solve_one_step_lqr(initial_state: npt.NDArray[np.float64], reference_state: npt.NDArray[np.float64], Q: npt.NDArray[np.float64], R: npt.NDArray[np.float64], A: npt.NDArray[np.float64], B: npt.NDArray[np.float64], g: npt.NDArray[np.float64], angle_diff_indices: List[int]=[]) -> npt.NDArray[np.float64]:
        """
        This function uses LQR to find an optimal input to minimize tracking error in one step of dynamics.
        The dynamics are next_state = A @ initial_state + B @ input + g and our target is the reference_state.
        :param initial_state: The current state.
        :param reference_state: The desired state in 1 step (according to A,B,g dynamics).
        :param Q: The state tracking 2-norm cost matrix.
        :param R: The input 2-norm cost matrix.
        :param A: The state dynamics matrix.
        :param B: The input dynamics matrix.
        :param g: The offset/affine dynamics term.
        :param angle_diff_indices: The set of state indices for which we need to apply angle differences, if defined.
        :return: LQR optimal input for the 1-step problem.
        """
        state_error_zero_input = A @ initial_state + g - reference_state
        for angle_diff_index in angle_diff_indices:
            state_error_zero_input[angle_diff_index] = angle_diff(state_error_zero_input[angle_diff_index], 0.0, 2 * np.pi)
        lqr_input = -np.linalg.inv(B.T @ Q @ B + R) @ B.T @ Q @ state_error_zero_input
        return lqr_input

def track_trajectory(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, initial_state: EgoState, trajectory: AbstractTrajectory) -> DynamicCarState:
    """Inherited, see superclass."""
    initial_velocity, initial_lateral_state_vector = self._compute_initial_velocity_and_lateral_state(current_iteration, initial_state, trajectory)
    reference_velocity, curvature_profile = self._compute_reference_velocity_and_curvature_profile(current_iteration, trajectory)
    should_stop = reference_velocity <= self._stopping_velocity and initial_velocity <= self._stopping_velocity
    if should_stop:
        accel_cmd, steering_rate_cmd = self._stopping_controller(initial_velocity, reference_velocity)
    else:
        accel_cmd = self._longitudinal_lqr_controller(initial_velocity, reference_velocity)
        velocity_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_velocity, derivatives=np.ones(self._tracking_horizon, dtype=np.float64) * accel_cmd, discretization_time=self._discretization_time)[:self._tracking_horizon]
        steering_rate_cmd = self._lateral_lqr_controller(initial_lateral_state_vector, velocity_profile, curvature_profile)
    return DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=initial_state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=initial_state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel_cmd, 0), tire_steering_rate=steering_rate_cmd)

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

def infer(self, features: FeaturesType) -> TargetsType:
    """
        Makes a single inference on a Pytorch/Torchscript model.

        :param features: dictionary of feature types
        :return: dictionary of target types
        """
    assert self._initialized is True, 'The model loader has not been initialized!'
    return self._model.forward(features)

class EgoCentricMLAgents(AbstractMLAgents):
    """
    Simulate agents based on an ML model.
    """

    def __init__(self, model: TorchModuleWrapper, scenario: AbstractScenario) -> None:
        """
        Initializes the EgoCentricMLAgents class.
        :param model: Model to use for inference.
        :param scenario: scenario
        """
        super().__init__(model, scenario)
        self.prediction_type = 'agents_trajectory'

    @property
    def _ego_velocity_anchor_state(self) -> StateSE2:
        """
        Returns the ego's velocity state vector as an anchor state for transformation.
        :return: A StateSE2 representing ego's velocity state as an anchor state
        """
        ego_velocity = self._ego_anchor_state.dynamic_car_state.rear_axle_velocity_2d
        return StateSE2(ego_velocity.x, ego_velocity.y, self._ego_anchor_state.rear_axle.heading)

    def _infer_model(self, features: FeaturesType) -> TargetsType:
        """Inherited, see superclass."""
        predictions = self._model_loader.infer(features)
        if self.prediction_type not in predictions:
            raise ValueError(f"Prediction does not have the output '{self.prediction_type}'")
        agents_prediction_tensor = cast(AgentsTrajectories, predictions[self.prediction_type]).data
        agents_prediction = agents_prediction_tensor[0].cpu().detach().numpy()
        return {self.prediction_type: AgentsTrajectories([cast(npt.NDArray[np.float32], agents_prediction)]).get_agents_only_trajectories()}

    def _update_observation_with_predictions(self, predictions: TargetsType) -> None:
        """Inherited, see superclass."""
        assert self._agents, 'The agents have not been initialized. Please make sure they are initialized!'
        agent_predictions = cast(AgentsTrajectories, predictions[self.prediction_type])
        agent_predictions.reshape_to_agents()
        agent_poses = agent_predictions.poses[0]
        agent_velocities = agent_predictions.xy_velocity[0]
        for agent_token, agent, poses_horizon, xy_velocity_horizon in zip(self._agents, self._agents.values(), agent_poses, agent_velocities):
            poses = numpy_array_to_absolute_pose(self._ego_anchor_state.rear_axle, poses_horizon)
            xy_velocities = numpy_array_to_absolute_velocity(self._ego_velocity_anchor_state, xy_velocity_horizon)
            future_trajectory = _convert_prediction_to_predicted_trajectory(agent, poses, xy_velocities, self._step_interval_us)
            new_state = future_trajectory.trajectory.get_state_at_time(self.step_time)
            new_agent = Agent(tracked_object_type=agent.tracked_object_type, oriented_box=new_state.oriented_box, velocity=new_state.velocity, metadata=agent.metadata)
            new_agent.predictions = [future_trajectory]
            self._agents[agent_token] = new_agent

def _infer_model(self, features: FeaturesType) -> TargetsType:
    """Inherited, see superclass."""
    predictions = self._model_loader.infer(features)
    if self.prediction_type not in predictions:
        raise ValueError(f"Prediction does not have the output '{self.prediction_type}'")
    agents_prediction_tensor = cast(AgentsTrajectories, predictions[self.prediction_type]).data
    agents_prediction = agents_prediction_tensor[0].cpu().detach().numpy()
    return {self.prediction_type: AgentsTrajectories([cast(npt.NDArray[np.float32], agents_prediction)]).get_agents_only_trajectories()}

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

def setUp(self) -> None:
    """Initialize scenario and model for constructing AgentCentricMLAgents class."""
    self.scenario = MockAbstractScenario(number_of_detections=1)
    self.model = Mock(spec=TorchModuleWrapper)
    self.model.future_trajectory_sampling = TrajectorySampling(num_poses=1, time_horizon=1.0)
    self.pred_trajectory = AgentsTrajectories(data=[np.array([[[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]]])])

class LightningModuleWrapper(pl.LightningModule):
    """
    Lightning module that wraps the training/validation/testing procedure and handles the objective/metric computation.
    """

    def __init__(self, model: TorchModuleWrapper, objectives: List[AbstractObjective], metrics: List[AbstractTrainingMetric], batch_size: int, optimizer: Optional[DictConfig]=None, lr_scheduler: Optional[DictConfig]=None, warm_up_lr_scheduler: Optional[DictConfig]=None, objective_aggregate_mode: str='mean') -> None:
        """
        Initializes the class.

        :param model: pytorch model
        :param objectives: list of learning objectives used for supervision at each step
        :param metrics: list of planning metrics computed at each step
        :param batch_size: batch_size taken from dataloader config
        :param optimizer: config for instantiating optimizer. Can be 'None' for older models.
        :param lr_scheduler: config for instantiating lr_scheduler. Can be 'None' for older models and when an lr_scheduler is not being used.
        :param warm_up_lr_scheduler: config for instantiating warm up lr scheduler. Can be 'None' for older models and when a warm up lr_scheduler is not being used.
        :param objective_aggregate_mode: how should different objectives be combined, can be 'sum', 'mean', and 'max'.
        """
        super().__init__()
        self.save_hyperparameters(ignore=['model'])
        self.model = model
        self.objectives = objectives
        self.metrics = metrics
        self.optimizer = optimizer
        self.lr_scheduler = lr_scheduler
        self.warm_up_lr_scheduler = warm_up_lr_scheduler
        self.objective_aggregate_mode = objective_aggregate_mode
        model_targets = {builder.get_feature_unique_name() for builder in model.get_list_of_computed_target()}
        for objective in self.objectives:
            for feature in objective.get_list_of_required_target_types():
                assert feature in model_targets, f'Objective target: "{feature}" is not in model computed targets!'
        for metric in self.metrics:
            for feature in metric.get_list_of_required_target_types():
                assert feature in model_targets, f'Metric target: "{feature}" is not in model computed targets!'

    def _step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], prefix: str) -> torch.Tensor:
        """
        Propagates the model forward and backwards and computes/logs losses and metrics.

        This is called either during training, validation or testing stage.

        :param batch: input batch consisting of features and targets
        :param prefix: prefix prepended at each artifact's name during logging
        :return: model's scalar loss
        """
        features, targets, scenarios = batch
        predictions = self.forward(features)
        objectives = self._compute_objectives(predictions, targets, scenarios)
        metrics = self._compute_metrics(predictions, targets)
        loss = aggregate_objectives(objectives, agg_mode=self.objective_aggregate_mode)
        self._log_step(loss, objectives, metrics, prefix)
        return loss

    def _compute_objectives(self, predictions: TargetsType, targets: TargetsType, scenarios: ScenarioListType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of learning objectives used for supervision given the model's predictions and targets.

        :param predictions: model's output signal
        :param targets: supervisory signal
        :return: dictionary of objective names and values
        """
        return {objective.name(): objective.compute(predictions, targets, scenarios) for objective in self.objectives}

    def _compute_metrics(self, predictions: TargetsType, targets: TargetsType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of planning metrics given the model's predictions and targets.

        :param predictions: model's predictions
        :param targets: ground truth targets
        :return: dictionary of metrics names and values
        """
        return {metric.name(): metric.compute(predictions, targets) for metric in self.metrics}

    def _log_step(self, loss: torch.Tensor, objectives: Dict[str, torch.Tensor], metrics: Dict[str, torch.Tensor], prefix: str, loss_name: str='loss') -> None:
        """
        Logs the artifacts from a training/validation/test step.

        :param loss: scalar loss value
        :type objectives: [type]
        :param metrics: dictionary of metrics names and values
        :param prefix: prefix prepended at each artifact's name
        :param loss_name: name given to the loss for logging
        """
        self.log(f'loss/{prefix}_{loss_name}', loss)
        for key, value in objectives.items():
            self.log(f'objectives/{prefix}_{key}', value)
        for key, value in metrics.items():
            self.log(f'metrics/{prefix}_{key}', value)

    def training_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during training.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'train')

    def validation_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during validation.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'val')

    def test_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during testing.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'test')

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Propagates a batch of features through the model.

        :param features: features batch
        :return: model's predictions
        """
        return self.model(features)

    def configure_optimizers(self) -> Union[Optimizer, Dict[str, Union[Optimizer, _LRScheduler]]]:
        """
        Configures the optimizers and learning schedules for the training.

        :return: optimizer or dictionary of optimizers and schedules
        """
        if self.optimizer is None:
            raise RuntimeError('To train, optimizer must not be None.')
        optimizer: Optimizer = instantiate(config=self.optimizer, params=self.parameters(), lr=self.optimizer.lr)
        logger.info(f'Using optimizer: {self.optimizer._target_}')
        lr_scheduler_params: Dict[str, Union[_LRScheduler, str, int]] = build_lr_scheduler(optimizer=optimizer, lr=self.optimizer.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler, lr_scheduler_cfg=self.lr_scheduler)
        optimizer_dict: Dict[str, Any] = {}
        optimizer_dict['optimizer'] = optimizer
        if lr_scheduler_params:
            logger.info(f'Using lr_schedulers {lr_scheduler_params}')
            optimizer_dict['lr_scheduler'] = lr_scheduler_params
        return optimizer_dict if 'lr_scheduler' in optimizer_dict else optimizer_dict['optimizer']

def _step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], prefix: str) -> torch.Tensor:
    """
        Propagates the model forward and backwards and computes/logs losses and metrics.

        This is called either during training, validation or testing stage.

        :param batch: input batch consisting of features and targets
        :param prefix: prefix prepended at each artifact's name during logging
        :return: model's scalar loss
        """
    features, targets, scenarios = batch
    predictions = self.forward(features)
    objectives = self._compute_objectives(predictions, targets, scenarios)
    metrics = self._compute_metrics(predictions, targets)
    loss = aggregate_objectives(objectives, agg_mode=self.objective_aggregate_mode)
    self._log_step(loss, objectives, metrics, prefix)
    return loss

class TrajectoryWeightDecayImitationObjective(AbstractObjective):
    """
    Objective that drives the model to imitate the signals from expert behaviors/trajectories.
    When comparing model's predictions to expert's trajectory, it assigns more weight to earlier timestamps than later ones.
    Formula: mean(loss * exp(-index / poses))
    """

    def __init__(self, scenario_type_loss_weighting: Dict[str, float], weight: float=1.0):
        """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
        self._name = 'trajectory_weight_decay_imitation_objective'
        self._weight = weight
        self._decay = 1.0
        self._fn_xy = torch.nn.modules.loss.L1Loss(reduction='none')
        self._fn_heading = torch.nn.modules.loss.L1Loss(reduction='none')
        self._scenario_type_loss_weighting = scenario_type_loss_weighting

    def name(self) -> str:
        """
        Name of the objective
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['trajectory']

    def compute(self, predictions: FeaturesType, targets: TargetsType, scenarios: ScenarioListType) -> torch.Tensor:
        """
        Computes the objective's loss given the ground truth targets and the model's predictions
        and weights it based on a fixed weight factor.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: loss scalar tensor
        """
        predicted_trajectory = cast(Trajectory, predictions['trajectory'])
        targets_trajectory = cast(Trajectory, targets['trajectory'])
        loss_weights = extract_scenario_type_weight(scenarios, self._scenario_type_loss_weighting, device=predicted_trajectory.xy.device)
        planner_output_steps = predicted_trajectory.xy.shape[1]
        decay_weight = torch.ones_like(predicted_trajectory.xy)
        decay_value = torch.exp(-torch.Tensor(range(planner_output_steps)) / (planner_output_steps * self._decay))
        decay_weight[:, :] = decay_value.unsqueeze(1)
        broadcast_shape_xy = tuple([-1] + [1 for _ in range(predicted_trajectory.xy.dim() - 1)])
        broadcasted_loss_weights_xy = loss_weights.view(broadcast_shape_xy)
        broadcast_shape_heading = tuple([-1] + [1 for _ in range(predicted_trajectory.heading.dim() - 1)])
        broadcasted_loss_weights_heading = loss_weights.view(broadcast_shape_heading)
        weighted_xy_loss = self._fn_xy(predicted_trajectory.xy, targets_trajectory.xy) * broadcasted_loss_weights_xy
        weighted_heading_loss = self._fn_heading(predicted_trajectory.heading, targets_trajectory.heading) * broadcasted_loss_weights_heading
        assert weighted_xy_loss.size() == predicted_trajectory.xy.size()
        assert weighted_heading_loss.size() == predicted_trajectory.heading.size()
        return self._weight * (torch.mean(weighted_xy_loss * decay_weight) + torch.mean(weighted_heading_loss * decay_weight[:, :, 0]))

def __init__(self, scenario_type_loss_weighting: Dict[str, float], weight: float=1.0):
    """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
    self._name = 'trajectory_weight_decay_imitation_objective'
    self._weight = weight
    self._decay = 1.0
    self._fn_xy = torch.nn.modules.loss.L1Loss(reduction='none')
    self._fn_heading = torch.nn.modules.loss.L1Loss(reduction='none')
    self._scenario_type_loss_weighting = scenario_type_loss_weighting

def compute(self, predictions: FeaturesType, targets: TargetsType, scenarios: ScenarioListType) -> torch.Tensor:
    """
        Computes the objective's loss given the ground truth targets and the model's predictions
        and weights it based on a fixed weight factor.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: loss scalar tensor
        """
    predicted_trajectory = cast(Trajectory, predictions['trajectory'])
    targets_trajectory = cast(Trajectory, targets['trajectory'])
    loss_weights = extract_scenario_type_weight(scenarios, self._scenario_type_loss_weighting, device=predicted_trajectory.xy.device)
    planner_output_steps = predicted_trajectory.xy.shape[1]
    decay_weight = torch.ones_like(predicted_trajectory.xy)
    decay_value = torch.exp(-torch.Tensor(range(planner_output_steps)) / (planner_output_steps * self._decay))
    decay_weight[:, :] = decay_value.unsqueeze(1)
    broadcast_shape_xy = tuple([-1] + [1 for _ in range(predicted_trajectory.xy.dim() - 1)])
    broadcasted_loss_weights_xy = loss_weights.view(broadcast_shape_xy)
    broadcast_shape_heading = tuple([-1] + [1 for _ in range(predicted_trajectory.heading.dim() - 1)])
    broadcasted_loss_weights_heading = loss_weights.view(broadcast_shape_heading)
    weighted_xy_loss = self._fn_xy(predicted_trajectory.xy, targets_trajectory.xy) * broadcasted_loss_weights_xy
    weighted_heading_loss = self._fn_heading(predicted_trajectory.heading, targets_trajectory.heading) * broadcasted_loss_weights_heading
    assert weighted_xy_loss.size() == predicted_trajectory.xy.size()
    assert weighted_heading_loss.size() == predicted_trajectory.heading.size()
    return self._weight * (torch.mean(weighted_xy_loss * decay_weight) + torch.mean(weighted_heading_loss * decay_weight[:, :, 0]))

class ImitationObjective(AbstractObjective):
    """
    Objective that drives the model to imitate the signals from expert behaviors/trajectories.
    """

    def __init__(self, scenario_type_loss_weighting: Dict[str, float], weight: float=1.0):
        """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
        self._name = 'imitation_objective'
        self._weight = weight
        self._fn_xy = torch.nn.modules.loss.MSELoss(reduction='none')
        self._fn_heading = torch.nn.modules.loss.L1Loss(reduction='none')
        self._scenario_type_loss_weighting = scenario_type_loss_weighting

    def name(self) -> str:
        """
        Name of the objective
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['trajectory']

    def compute(self, predictions: FeaturesType, targets: TargetsType, scenarios: ScenarioListType) -> torch.Tensor:
        """
        Computes the objective's loss given the ground truth targets and the model's predictions
        and weights it based on a fixed weight factor.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: loss scalar tensor
        """
        predicted_trajectory = cast(Trajectory, predictions['trajectory'])
        targets_trajectory = cast(Trajectory, targets['trajectory'])
        loss_weights = extract_scenario_type_weight(scenarios, self._scenario_type_loss_weighting, device=predicted_trajectory.xy.device)
        broadcast_shape_xy = tuple([-1] + [1 for _ in range(predicted_trajectory.xy.dim() - 1)])
        broadcasted_loss_weights_xy = loss_weights.view(broadcast_shape_xy)
        broadcast_shape_heading = tuple([-1] + [1 for _ in range(predicted_trajectory.heading.dim() - 1)])
        broadcasted_loss_weights_heading = loss_weights.view(broadcast_shape_heading)
        weighted_xy_loss = self._fn_xy(predicted_trajectory.xy, targets_trajectory.xy) * broadcasted_loss_weights_xy
        weighted_heading_loss = self._fn_heading(predicted_trajectory.heading, targets_trajectory.heading) * broadcasted_loss_weights_heading
        assert weighted_xy_loss.size() == predicted_trajectory.xy.size()
        assert weighted_heading_loss.size() == predicted_trajectory.heading.size()
        return self._weight * (torch.mean(weighted_xy_loss) + torch.mean(weighted_heading_loss))

def __init__(self, scenario_type_loss_weighting: Dict[str, float], weight: float=1.0):
    """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
    self._name = 'imitation_objective'
    self._weight = weight
    self._fn_xy = torch.nn.modules.loss.MSELoss(reduction='none')
    self._fn_heading = torch.nn.modules.loss.L1Loss(reduction='none')
    self._scenario_type_loss_weighting = scenario_type_loss_weighting

def compute(self, predictions: FeaturesType, targets: TargetsType, scenarios: ScenarioListType) -> torch.Tensor:
    """
        Computes the objective's loss given the ground truth targets and the model's predictions
        and weights it based on a fixed weight factor.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: loss scalar tensor
        """
    predicted_trajectory = cast(Trajectory, predictions['trajectory'])
    targets_trajectory = cast(Trajectory, targets['trajectory'])
    loss_weights = extract_scenario_type_weight(scenarios, self._scenario_type_loss_weighting, device=predicted_trajectory.xy.device)
    broadcast_shape_xy = tuple([-1] + [1 for _ in range(predicted_trajectory.xy.dim() - 1)])
    broadcasted_loss_weights_xy = loss_weights.view(broadcast_shape_xy)
    broadcast_shape_heading = tuple([-1] + [1 for _ in range(predicted_trajectory.heading.dim() - 1)])
    broadcasted_loss_weights_heading = loss_weights.view(broadcast_shape_heading)
    weighted_xy_loss = self._fn_xy(predicted_trajectory.xy, targets_trajectory.xy) * broadcasted_loss_weights_xy
    weighted_heading_loss = self._fn_heading(predicted_trajectory.heading, targets_trajectory.heading) * broadcasted_loss_weights_heading
    assert weighted_xy_loss.size() == predicted_trajectory.xy.size()
    assert weighted_heading_loss.size() == predicted_trajectory.heading.size()
    return self._weight * (torch.mean(weighted_xy_loss) + torch.mean(weighted_heading_loss))

class AgentsImitationObjective(AbstractObjective):
    """
    Objective that drives the model to imitate the signals from expert behaviors/trajectories.
    """

    def __init__(self, scenario_type_loss_weighting: Dict[str, float], name: str='agent_imitation_objective', weight: float=1.0):
        """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
        self._name = name
        self._weight = weight
        self._fn = torch.nn.modules.loss.MSELoss(reduction='mean')
        self._scenario_type_loss_weighting = scenario_type_loss_weighting

    def name(self) -> str:
        """
        Name of the objective
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['agents_trajectory']

    def compute(self, predictions: FeaturesType, targets: TargetsType, scenarios: ScenarioListType) -> torch.Tensor:
        """
        Computes the objective's loss given the ground truth targets and the model's predictions
        and weights it based on a fixed weight factor.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: loss scalar tensor
        """
        predicted_trajectory = cast(AgentsTrajectories, predictions['agents_trajectory'])
        targets_trajectory = cast(AgentsTrajectories, targets['agents_trajectory'])
        batch_size = predicted_trajectory.batch_size
        loss = 0.0
        for sample_idx in range(batch_size):
            loss += self._fn(predicted_trajectory.poses[sample_idx], targets_trajectory.poses[sample_idx])
        return self._weight * loss / batch_size

def __init__(self, scenario_type_loss_weighting: Dict[str, float], name: str='agent_imitation_objective', weight: float=1.0):
    """
        Initializes the class

        :param name: name of the objective
        :param weight: weight contribution to the overall loss
        """
    self._name = name
    self._weight = weight
    self._fn = torch.nn.modules.loss.MSELoss(reduction='mean')
    self._scenario_type_loss_weighting = scenario_type_loss_weighting

class TestAgentImitationObjective(unittest.TestCase):
    """Test agent imitation objective."""

    def setUp(self) -> None:
        """Set up test case."""
        self.target_data: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])]
        self.prediction_data: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]]])]
        self.objective = AgentsImitationObjective(scenario_type_loss_weighting={})

    def test_compute_loss(self) -> None:
        """
        Test loss computation
        """
        prediction = AgentsTrajectories(data=self.prediction_data)
        target = AgentsTrajectories(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
        loss = self.objective.compute({'agents_trajectory': prediction.to_feature_tensor()}, {'agents_trajectory': target.to_feature_tensor()}, scenarios)
        self.assertEqual(loss, torch.tensor(0.5))

    def test_zero_loss(self) -> None:
        """
        Test perfect prediction. The loss should be zero
        """
        target = AgentsTrajectories(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
        loss = self.objective.compute({'agents_trajectory': target.to_feature_tensor()}, {'agents_trajectory': target.to_feature_tensor()}, scenarios)
        self.assertEqual(loss, torch.tensor(0.0))

def test_compute_loss(self) -> None:
    """
        Test loss computation
        """
    prediction = AgentsTrajectories(data=self.prediction_data)
    target = AgentsTrajectories(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
    loss = self.objective.compute({'agents_trajectory': prediction.to_feature_tensor()}, {'agents_trajectory': target.to_feature_tensor()}, scenarios)
    self.assertEqual(loss, torch.tensor(0.5))

def test_zero_loss(self) -> None:
    """
        Test perfect prediction. The loss should be zero
        """
    target = AgentsTrajectories(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
    loss = self.objective.compute({'agents_trajectory': target.to_feature_tensor()}, {'agents_trajectory': target.to_feature_tensor()}, scenarios)
    self.assertEqual(loss, torch.tensor(0.0))

class TestTrajectoryWeightDecayImitationObjective(unittest.TestCase):
    """Test weight decay imitation objective."""

    def setUp(self) -> None:
        """Set up test case."""
        self.target_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]])
        self.prediction_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]]])
        self.objective = TrajectoryWeightDecayImitationObjective(scenario_type_loss_weighting={})

    def test_compute_loss(self) -> None:
        """
        Test loss computation
        """
        prediction = Trajectory(data=self.prediction_data)
        target = Trajectory(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
        loss = self.objective.compute({'trajectory': prediction.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
        torch.testing.assert_allclose(loss, torch.tensor(0.60653, dtype=torch.float64))

    def test_zero_loss(self) -> None:
        """
        Test perfect prediction. The loss should be zero
        """
        target = Trajectory(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
        loss = self.objective.compute({'trajectory': target.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
        self.assertEqual(loss, torch.tensor(0.0))

def test_compute_loss(self) -> None:
    """
        Test loss computation
        """
    prediction = Trajectory(data=self.prediction_data)
    target = Trajectory(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
    loss = self.objective.compute({'trajectory': prediction.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
    torch.testing.assert_allclose(loss, torch.tensor(0.60653, dtype=torch.float64))

def test_zero_loss(self) -> None:
    """
        Test perfect prediction. The loss should be zero
        """
    target = Trajectory(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='lane_following_with_lead', scenario_type='') for _ in range(2)]
    loss = self.objective.compute({'trajectory': target.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
    self.assertEqual(loss, torch.tensor(0.0))

class TestImitationObjective(unittest.TestCase):
    """Test weight decay imitation objective."""

    def setUp(self) -> None:
        """Set up test case."""
        self.target_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]])
        self.prediction_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]]])
        self.objective = ImitationObjective(scenario_type_loss_weighting={'unknown': 1.0, 'lane_following_with_lead': 2.0})

    def test_compute_loss(self) -> None:
        """
        Test loss computation
        """
        prediction = Trajectory(data=self.prediction_data)
        target = Trajectory(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='', scenario_type='lane_following_with_lead'), CachedScenario(log_name='', token='', scenario_type='unknown')]
        loss = self.objective.compute({'trajectory': prediction.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
        self.assertEqual(loss, torch.tensor(1.5))

    def test_zero_loss(self) -> None:
        """
        Test perfect prediction. The loss should be zero
        """
        target = Trajectory(data=self.target_data)
        scenarios = [CachedScenario(log_name='', token='', scenario_type='lane_following_with_lead'), CachedScenario(log_name='', token='', scenario_type='unknown')]
        loss = self.objective.compute({'trajectory': target.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
        self.assertEqual(loss, torch.tensor(0.0))

def test_compute_loss(self) -> None:
    """
        Test loss computation
        """
    prediction = Trajectory(data=self.prediction_data)
    target = Trajectory(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='', scenario_type='lane_following_with_lead'), CachedScenario(log_name='', token='', scenario_type='unknown')]
    loss = self.objective.compute({'trajectory': prediction.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
    self.assertEqual(loss, torch.tensor(1.5))

def test_zero_loss(self) -> None:
    """
        Test perfect prediction. The loss should be zero
        """
    target = Trajectory(data=self.target_data)
    scenarios = [CachedScenario(log_name='', token='', scenario_type='lane_following_with_lead'), CachedScenario(log_name='', token='', scenario_type='unknown')]
    loss = self.objective.compute({'trajectory': target.to_feature_tensor()}, {'trajectory': target.to_feature_tensor()}, scenarios)
    self.assertEqual(loss, torch.tensor(0.0))

def convert_predictions_to_trajectory(predictions: torch.Tensor) -> torch.Tensor:
    """
    Convert predictions tensor to Trajectory.data shape
    :param predictions: tensor from network
    :return: data suitable for Trajectory
    """
    num_batches = predictions.shape[0]
    return predictions.view(num_batches, -1, Trajectory.state_size())

class LaneGCN(TorchModuleWrapper):
    """
    Vector-based model that uses a series of MLPs to encode ego and agent signals, a lane graph to encode vector-map
    elements and a fusion network to capture lane & agent intra/inter-interactions through attention layers.
    Dynamic map elements such as traffic light status and ego route information are also encoded in the fusion network.

    Implementation of the original LaneGCN paper ("Learning Lane Graph Representations for Motion Forecasting").
    """

    def __init__(self, map_net_scales: int, num_res_blocks: int, num_attention_layers: int, a2a_dist_threshold: float, l2a_dist_threshold: float, num_output_features: int, feature_dim: int, vector_map_feature_radius: int, vector_map_connection_scales: Optional[List[int]], past_trajectory_sampling: TrajectorySampling, future_trajectory_sampling: TrajectorySampling):
        """
        :param map_net_scales: Number of scales to extend the predecessor and successor lane nodes.
        :param num_res_blocks: Number of residual blocks for the GCN (LaneGCN uses 4).
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param a2a_dist_threshold: [m] distance threshold for aggregating actor-to-actor nodes
        :param l2a_dist_threshold: [m] distance threshold for aggregating map-to-actor nodes
        :param num_output_features: number of target features
        :param feature_dim: hidden layer dimension
        :param vector_map_feature_radius: The query radius scope relative to the current ego-pose.
        :param vector_map_connection_scales: The hops of lane neighbors to extract, default 1 hop
        :param past_trajectory_sampling: Sampling parameters for past trajectory
        :param future_trajectory_sampling: Sampling parameters for future trajectory
        """
        super().__init__(feature_builders=[VectorMapFeatureBuilder(radius=vector_map_feature_radius, connection_scales=vector_map_connection_scales), AgentsFeatureBuilder(trajectory_sampling=past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling=future_trajectory_sampling)], future_trajectory_sampling=future_trajectory_sampling)
        self.feature_dim = feature_dim
        self.connection_scales = list(range(map_net_scales)) if vector_map_connection_scales is None else vector_map_connection_scales
        self.ego_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.ego_state_dim()
        self.agent_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.agents_states_dim()
        self.lane_net = LaneNet(lane_input_len=2, lane_feature_len=self.feature_dim, num_scales=map_net_scales, num_residual_blocks=num_res_blocks, is_map_feat=False)
        self.ego_feature_extractor = torch.nn.Sequential(nn.Linear(self.ego_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(inplace=True), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
        self.agent_feature_extractor = torch.nn.Sequential(nn.Linear(self.agent_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
        self.actor2lane_attention = Actor2LaneAttention(actor_feature_len=self.feature_dim, lane_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
        self.lane2actor_attention = Lane2ActorAttention(lane_feature_len=self.feature_dim, actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
        self.actor2actor_attention = Actor2ActorAttention(actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=a2a_dist_threshold)
        self._mlp = nn.Sequential(nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, num_output_features))

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
        ego_agent_features = cast(Agents, features['agents'])
        ego_past_trajectory = ego_agent_features.ego
        batch_size = ego_agent_features.batch_size
        ego_features = []
        for sample_idx in range(batch_size):
            sample_ego_feature = self.ego_feature_extractor(ego_past_trajectory[sample_idx].reshape(1, -1))
            sample_ego_center = ego_agent_features.get_ego_agents_center_in_sample(sample_idx)
            if not vector_map_data.is_valid:
                num_coords = 1
                coords = torch.zeros((num_coords, 2, 2), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
                connections = {}
                for scale in self.connection_scales:
                    connections[scale] = torch.zeros((num_coords, 2), device=sample_ego_feature.device).long()
                lane_meta_tl = torch.zeros((num_coords, LaneSegmentTrafficLightData._encoding_dim), device=sample_ego_feature.device)
                lane_meta_route = torch.zeros((num_coords, LaneOnRouteStatusData._encoding_dim), device=sample_ego_feature.device)
                lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
            else:
                coords = vector_map_data.coords[sample_idx]
                connections = vector_map_data.multi_scale_connections[sample_idx]
                lane_meta_tl = vector_map_data.traffic_light_data[sample_idx]
                lane_meta_route = vector_map_data.on_route_status[sample_idx]
                lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
            lane_features = self.lane_net(coords, connections)
            lane_centers = coords.mean(axis=1)
            if ego_agent_features.has_agents(sample_idx):
                sample_agents_feature = self.agent_feature_extractor(ego_agent_features.get_flatten_agents_features_in_sample(sample_idx))
                sample_agents_center = ego_agent_features.get_agents_centers_in_sample(sample_idx)
            else:
                flattened_agents = torch.zeros((1, self.agent_input_dim), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
                sample_agents_feature = self.agent_feature_extractor(flattened_agents)
                sample_agents_center = torch.zeros_like(sample_ego_center).unsqueeze(dim=0)
            ego_agents_feature = torch.cat([sample_ego_feature, sample_agents_feature], dim=0)
            ego_agents_center = torch.cat([sample_ego_center.unsqueeze(dim=0), sample_agents_center], dim=0)
            lane_features = self.actor2lane_attention(ego_agents_feature, ego_agents_center, lane_features, lane_meta, lane_centers)
            ego_agents_feature = self.lane2actor_attention(lane_features, lane_centers, ego_agents_feature, ego_agents_center)
            ego_agents_feature = self.actor2actor_attention(ego_agents_feature, ego_agents_center)
            ego_features.append(ego_agents_feature[0])
        ego_features = torch.cat(ego_features).view(batch_size, -1)
        predictions = self._mlp(ego_features)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

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
    ego_agent_features = cast(Agents, features['agents'])
    ego_past_trajectory = ego_agent_features.ego
    batch_size = ego_agent_features.batch_size
    ego_features = []
    for sample_idx in range(batch_size):
        sample_ego_feature = self.ego_feature_extractor(ego_past_trajectory[sample_idx].reshape(1, -1))
        sample_ego_center = ego_agent_features.get_ego_agents_center_in_sample(sample_idx)
        if not vector_map_data.is_valid:
            num_coords = 1
            coords = torch.zeros((num_coords, 2, 2), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
            connections = {}
            for scale in self.connection_scales:
                connections[scale] = torch.zeros((num_coords, 2), device=sample_ego_feature.device).long()
            lane_meta_tl = torch.zeros((num_coords, LaneSegmentTrafficLightData._encoding_dim), device=sample_ego_feature.device)
            lane_meta_route = torch.zeros((num_coords, LaneOnRouteStatusData._encoding_dim), device=sample_ego_feature.device)
            lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
        else:
            coords = vector_map_data.coords[sample_idx]
            connections = vector_map_data.multi_scale_connections[sample_idx]
            lane_meta_tl = vector_map_data.traffic_light_data[sample_idx]
            lane_meta_route = vector_map_data.on_route_status[sample_idx]
            lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
        lane_features = self.lane_net(coords, connections)
        lane_centers = coords.mean(axis=1)
        if ego_agent_features.has_agents(sample_idx):
            sample_agents_feature = self.agent_feature_extractor(ego_agent_features.get_flatten_agents_features_in_sample(sample_idx))
            sample_agents_center = ego_agent_features.get_agents_centers_in_sample(sample_idx)
        else:
            flattened_agents = torch.zeros((1, self.agent_input_dim), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
            sample_agents_feature = self.agent_feature_extractor(flattened_agents)
            sample_agents_center = torch.zeros_like(sample_ego_center).unsqueeze(dim=0)
        ego_agents_feature = torch.cat([sample_ego_feature, sample_agents_feature], dim=0)
        ego_agents_center = torch.cat([sample_ego_center.unsqueeze(dim=0), sample_agents_center], dim=0)
        lane_features = self.actor2lane_attention(ego_agents_feature, ego_agents_center, lane_features, lane_meta, lane_centers)
        ego_agents_feature = self.lane2actor_attention(lane_features, lane_centers, ego_agents_feature, ego_agents_center)
        ego_agents_feature = self.actor2actor_attention(ego_agents_feature, ego_agents_center)
        ego_features.append(ego_agents_feature[0])
    ego_features = torch.cat(ego_features).view(batch_size, -1)
    predictions = self._mlp(ego_features)
    return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

def pad_avails(avails: torch.Tensor, pad_to: int, dim: int) -> torch.Tensor:
    """
    Copied from L5Kit's implementation `pad_avail`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/common.py.
    Changes:
        1. Change function name `pad_avail` to `pad_avails`
        2. Add dimension checking and adjust output dimension

    Pad vectors to 'pad_to' size. Dimensions are:
    N: number of elements (polylines)
    P: number of points
    :param avails: Availabilities to be padded, should be (N,P) and we're padding dim.
    :param pad_to: Number of elements or points.
    :param dim: Dimension at which to apply padding.
    :return: The padded polyline availabilities (N,P).
    """
    num_els, num_points = avails.shape
    if dim == 0 or dim == -2:
        num_els = pad_to - num_els
    elif dim == 1 or dim == -1:
        num_points = pad_to - num_points
    else:
        raise ValueError(dim)
    pad = torch.zeros(num_els, num_points, dtype=avails.dtype, device=avails.device)
    return torch.cat([avails, pad], dim=dim)

def pad_polylines(polylines: torch.Tensor, pad_to: int, dim: int) -> torch.Tensor:
    """
    Copied from L5Kit's implementation `pad_points`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/common.py.
    Changes:
        1. Change function name `pad_points` to `pad_polylines`
        2. Add dimension checking and adjust output dimension

    Pad vectors to 'pad_to' size. Dimensions are:
    N: number of elements (polylines)
    P: number of points
    F: number of features
    :param polylines: Polylines to be padded, should be (N,P,F) and we're padding dim.
    :param pad_to: Number of elements, points, or features.
    :param dim: Dimension at which to apply padding.
    :return: The padded polylines (N,P,F).
    """
    num_els, num_points, num_feats = polylines.shape
    if dim == 0 or dim == -3:
        num_els = pad_to - num_els
    elif dim == 1 or dim == -2:
        num_points = pad_to - num_points
    elif dim == 2 or dim == -1:
        num_feats = pad_to - num_feats
    else:
        raise ValueError(dim)
    pad = torch.zeros(num_els, num_points, num_feats, dtype=polylines.dtype, device=polylines.device)
    return torch.cat([polylines, pad], dim=dim)

class MultiheadAttentionGlobalHead(nn.Module):
    """
    Copied from L5Kit's implementation `MultiheadAttentionGlobalHead`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/global_graph.py.
    Changes:
        1. Add input & output description for `__init__`, `forward`
        2. Add num_mlp_layers & hidden_size_scaling to adjust MLP layers
        3. Change input variable `d_model` to `global_embedding_size`

    Global graph making use of multi-head attention.
    """

    def __init__(self, global_embedding_size: int, num_timesteps: int, num_outputs: int, nhead: int=8, dropout: float=0.1, hidden_size_scaling: int=4, num_mlp_layers: int=3):
        """
        Constructs global multi-head attention layer.
        :param global_embedding_size: Feature size.
        :param num_timesteps: Number of output timesteps.
        :param num_outputs: Number of output features per timestep.
        :param nhead: Number of attention heads. Default 8: query=ego, keys=types,ego,agents,map, values=ego,agents,map.
        :param dropout: Float in range [0,1] for level of dropout. Set to 0 to disable it. Default 0.1.
        :param hidden_size_scaling: Controls hidden layer size, scales embedding dimensionality. Default 4.
        :param num_mlp_layers: Num MLP layers. Default 3.
        """
        super().__init__()
        self.num_timesteps = num_timesteps
        self.num_outputs = num_outputs
        self.encoder = nn.MultiheadAttention(global_embedding_size, nhead, dropout=dropout)
        self.output_embed = MLP(global_embedding_size, global_embedding_size * hidden_size_scaling, num_timesteps * num_outputs, num_mlp_layers)

    def forward(self, inputs: torch.Tensor, type_embedding: torch.Tensor, mask: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward of the module.
        :param inputs: Model inputs. [1 + N + M, batch_size, feature_dim]
        :param type_embedding: Type embedding describing the different input types. [1 + N + M, batch_size, feature_dim]
        :param mask: Availability mask. [batch_size, 1 + N + M]
        :return Tuple of outputs, attention.
        """
        out, attns = self.encoder(inputs[[0]], inputs + type_embedding, inputs, mask)
        outputs = self.output_embed(out[0]).view(-1, self.num_timesteps, self.num_outputs)
        return (outputs, attns)

def forward(self, inputs: torch.Tensor, type_embedding: torch.Tensor, mask: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
    """
        Forward of the module.
        :param inputs: Model inputs. [1 + N + M, batch_size, feature_dim]
        :param type_embedding: Type embedding describing the different input types. [1 + N + M, batch_size, feature_dim]
        :param mask: Availability mask. [batch_size, 1 + N + M]
        :return Tuple of outputs, attention.
        """
    out, attns = self.encoder(inputs[[0]], inputs + type_embedding, inputs, mask)
    outputs = self.output_embed(out[0]).view(-1, self.num_timesteps, self.num_outputs)
    return (outputs, attns)

class GraphAttention(nn.Module):
    """
    Graph attention module to pool features from source nodes to destination nodes.

    Given a destination node i, we aggregate the features from nearby source nodes j whose L2
    distance from the destination node i is smaller than a threshold.

    This graph attention module follows the implementation in LaneGCN and is slightly different
    from the one in Graph Attention Networks.

    Compared to the open-sourced LaneGCN, this implementation omitted a few LayerNorm operations
    after some layers.
    """

    def __init__(self, src_feature_len: int, dst_feature_len: int, dist_threshold: float):
        """
        Initialize the model.
        :param src_feature_len: source node feature length.
        :param dst_feature_len: destination node feature length.
        :param dist_threshold: Distance threshold in meters. Only node information is aggregated if the destination
                               nodes are within this distance threshold from the source nodes.
        """
        super().__init__()
        self.dist_threshold = dist_threshold
        self.src_encoder = nn.Sequential(nn.Linear(src_feature_len, src_feature_len), nn.ReLU(inplace=True))
        self.dst_encoder = nn.Sequential(nn.Linear(dst_feature_len, dst_feature_len), nn.ReLU(inplace=True))
        edge_dist_feature_len = dst_feature_len
        self.edge_dist_encoder = nn.Sequential(nn.Linear(2, edge_dist_feature_len), nn.ReLU(inplace=True))
        edge_input_feature_len = src_feature_len + edge_dist_feature_len + dst_feature_len
        edge_output_feature_len = dst_feature_len
        self.edge_encoder = nn.Sequential(nn.Linear(edge_input_feature_len, edge_output_feature_len), nn.ReLU(inplace=True), nn.Linear(edge_output_feature_len, edge_output_feature_len))
        self.dst_feature_norm = nn.LayerNorm(dst_feature_len)
        self.output_linear = nn.Linear(dst_feature_len, dst_feature_len)

    def forward(self, src_node_features: torch.Tensor, src_node_pos: torch.Tensor, dst_node_features: torch.Tensor, dst_node_pos: torch.Tensor) -> torch.Tensor:
        """
        Graph attention module to pool features from source nodes to destination nodes.
        :param src_node_features: <torch.FloatTensor: num_src_nodes, src_node_feature_len>. Source node features.
        :param src_node_pos: <torch.FloatTensor: num_src_nodes, 2>. Source node (x, y) positions.
        :param dst_node_features: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Destination node features.
        :param dst_node_pos: <torch.FloatTensor: num_dst_nodes, 2>. Destination node (x, y) positions.
        :return: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Output destination node features.
        """
        src_dst_dist = (src_node_pos.view(-1, 1, 2) - dst_node_pos.view(1, -1, 2)).norm(dim=-1)
        src_dst_dist_mask = src_dst_dist <= self.dist_threshold
        edge_src_dist_pairs = src_dst_dist_mask.nonzero(as_tuple=False)
        edge_src_idx = edge_src_dist_pairs[:, 0]
        edge_dst_idx = edge_src_dist_pairs[:, 1]
        src_node_encoded_features = self.src_encoder(src_node_features)
        dst_node_encoded_features = self.dst_encoder(dst_node_features)
        edge_src_features = src_node_encoded_features[edge_src_idx]
        edge_dst_features = dst_node_encoded_features[edge_dst_idx]
        edge_src_pos = src_node_pos[edge_src_idx]
        edge_dst_pos = dst_node_pos[edge_dst_idx]
        edge_dist = self.edge_dist_encoder(edge_src_pos - edge_dst_pos)
        edge_input_features = torch.cat([edge_src_features, edge_dist, edge_dst_features], dim=-1)
        edge_output_features = self.edge_encoder(edge_input_features)
        dst_node_output_features = dst_node_encoded_features.clone()
        dst_node_output_features.index_add_(0, edge_dst_idx, edge_output_features)
        dst_node_output_features = self.dst_feature_norm(dst_node_output_features)
        dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
        dst_node_output_features = self.output_linear(dst_node_output_features)
        dst_node_output_features += dst_node_features
        dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
        return dst_node_output_features

def forward(self, src_node_features: torch.Tensor, src_node_pos: torch.Tensor, dst_node_features: torch.Tensor, dst_node_pos: torch.Tensor) -> torch.Tensor:
    """
        Graph attention module to pool features from source nodes to destination nodes.
        :param src_node_features: <torch.FloatTensor: num_src_nodes, src_node_feature_len>. Source node features.
        :param src_node_pos: <torch.FloatTensor: num_src_nodes, 2>. Source node (x, y) positions.
        :param dst_node_features: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Destination node features.
        :param dst_node_pos: <torch.FloatTensor: num_dst_nodes, 2>. Destination node (x, y) positions.
        :return: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Output destination node features.
        """
    src_dst_dist = (src_node_pos.view(-1, 1, 2) - dst_node_pos.view(1, -1, 2)).norm(dim=-1)
    src_dst_dist_mask = src_dst_dist <= self.dist_threshold
    edge_src_dist_pairs = src_dst_dist_mask.nonzero(as_tuple=False)
    edge_src_idx = edge_src_dist_pairs[:, 0]
    edge_dst_idx = edge_src_dist_pairs[:, 1]
    src_node_encoded_features = self.src_encoder(src_node_features)
    dst_node_encoded_features = self.dst_encoder(dst_node_features)
    edge_src_features = src_node_encoded_features[edge_src_idx]
    edge_dst_features = dst_node_encoded_features[edge_dst_idx]
    edge_src_pos = src_node_pos[edge_src_idx]
    edge_dst_pos = dst_node_pos[edge_dst_idx]
    edge_dist = self.edge_dist_encoder(edge_src_pos - edge_dst_pos)
    edge_input_features = torch.cat([edge_src_features, edge_dist, edge_dst_features], dim=-1)
    edge_output_features = self.edge_encoder(edge_input_features)
    dst_node_output_features = dst_node_encoded_features.clone()
    dst_node_output_features.index_add_(0, edge_dst_idx, edge_output_features)
    dst_node_output_features = self.dst_feature_norm(dst_node_output_features)
    dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
    dst_node_output_features = self.output_linear(dst_node_output_features)
    dst_node_output_features += dst_node_features
    dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
    return dst_node_output_features

class Actor2LaneAttention(nn.Module):
    """
    Actor-to-Lane attention module.
    """

    def __init__(self, actor_feature_len: int, lane_feature_len: int, num_attention_layers: int, dist_threshold_m: float, num_groups: int=1) -> None:
        """
        :param actor_feature_len: Actor feature length.
        :param lane_feature_len: Lane feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m: Distance threshold in meters. We only aggregate map-to-actor node information if the
                                 actor nodes are within this distance threshold from the lane nodes. The value used
                                 in the LaneGCN paper is 100 meters.
        :param num_groups: Number of groups in groupnorm layer.
        """
        super().__init__()
        extra_lane_feature_dim = 6
        self.lane_meta = LinearWithGroupNorm(lane_feature_len + extra_lane_feature_dim, lane_feature_len, num_groups=num_groups, activation=False)
        attention_layers = [GraphAttention(actor_feature_len, lane_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor, lane_features: torch.Tensor, lane_meta: torch.Tensor, lane_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Actor-to-Lane attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_meta: <torch.FloatTensor: num_lanes, meta_feature_len>. Lane meta feature (TL,
            goal)
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
        lane_features = torch.cat((lane_features, lane_meta), dim=1)
        lane_features = self.lane_meta(lane_features)
        for attention_layer in self.attention_layers:
            lane_features = attention_layer(actor_features, actor_centers, lane_features, lane_centers)
        return lane_features

def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor, lane_features: torch.Tensor, lane_meta: torch.Tensor, lane_centers: torch.Tensor) -> torch.Tensor:
    """
        Perform Actor-to-Lane attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_meta: <torch.FloatTensor: num_lanes, meta_feature_len>. Lane meta feature (TL,
            goal)
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
    lane_features = torch.cat((lane_features, lane_meta), dim=1)
    lane_features = self.lane_meta(lane_features)
    for attention_layer in self.attention_layers:
        lane_features = attention_layer(actor_features, actor_centers, lane_features, lane_centers)
    return lane_features

class Lane2ActorAttention(nn.Module):
    """
    Lane-to-Actor attention module.
    """

    def __init__(self, lane_feature_len: int, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
        """
        :param lane_feature_len: Lane feature length.
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate map-to-actor node
            information if the actor nodes are within this distance threshold from the lane nodes.
            The value used in the LaneGCN paper is 100 meters.
        """
        super().__init__()
        attention_layers = [GraphAttention(lane_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, lane_features: torch.Tensor, lane_centers: torch.Tensor, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Lane-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
        for attention_layer in self.attention_layers:
            actor_features = attention_layer(lane_features, lane_centers, actor_features, actor_centers)
        return actor_features

def forward(self, lane_features: torch.Tensor, lane_centers: torch.Tensor, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
    """
        Perform Lane-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
    for attention_layer in self.attention_layers:
        actor_features = attention_layer(lane_features, lane_centers, actor_features, actor_centers)
    return actor_features

class Actor2ActorAttention(nn.Module):
    """
    Actor-to-Actor attention module.
    """

    def __init__(self, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
        """
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate actor-to-actor node
            information if the actor nodes are within this distance threshold from the other actor nodes.
            The value used in the LaneGCN paper is 30 meters.
        """
        super().__init__()
        attention_layers = [GraphAttention(actor_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Actor-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after aggregating the lane features.
        """
        for attention_layer in self.attention_layers:
            actor_features = attention_layer(actor_features, actor_centers, actor_features, actor_centers)
        return actor_features

def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
    """
        Perform Actor-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after aggregating the lane features.
        """
    for attention_layer in self.attention_layers:
        actor_features = attention_layer(actor_features, actor_centers, actor_features, actor_centers)
    return actor_features

def convert_predictions_to_trajectory(predictions: torch.Tensor) -> torch.Tensor:
    """
    Convert predictions tensor to Trajectory.data shape
    :param predictions: tensor from network
    :return: data suitable for Trajectory
    """
    num_batches = predictions.shape[0]
    return predictions.view(num_batches, -1, Trajectory.state_size())

class RasterModel(TorchModuleWrapper):
    """
    Wrapper around raster-based CNN model that consumes ego, agent and map data in rasterized format
    and regresses ego's future trajectory.
    """

    def __init__(self, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], model_name: str, pretrained: bool, num_input_channels: int, num_features_per_pose: int, future_trajectory_sampling: TrajectorySampling):
        """
        Initialize model.
        :param feature_builders: list of builders for features
        :param target_builders: list of builders for targets
        :param model_name: name of the model (e.g. resnet_50, efficientnet_b3)
        :param pretrained: whether the model will be pretrained
        :param num_input_channels: number of input channel of the raster model.
        :param num_features_per_pose: number of features per single pose
        :param future_trajectory_sampling: parameters of predicted trajectory
        """
        super().__init__(feature_builders=feature_builders, target_builders=target_builders, future_trajectory_sampling=future_trajectory_sampling)
        num_output_features = future_trajectory_sampling.num_poses * num_features_per_pose
        self._model = timm.create_model(model_name, pretrained=pretrained, num_classes=0, in_chans=num_input_channels)
        mlp = torch.nn.Linear(in_features=self._model.num_features, out_features=num_output_features)
        if hasattr(self._model, 'classifier'):
            self._model.classifier = mlp
        elif hasattr(self._model, 'fc'):
            self._model.fc = mlp
        else:
            raise NameError('Expected output layer named "classifier" or "fc" in model')

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "raster": Raster,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        raster: Raster = features['raster']
        predictions = self._model.forward(raster.data)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

def forward(self, features: FeaturesType) -> TargetsType:
    """
        Predict
        :param features: input features containing
                        {
                            "raster": Raster,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
    raster: Raster = features['raster']
    predictions = self._model.forward(raster.data)
    return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

def convert_predictions_to_trajectory(predictions: torch.Tensor) -> torch.Tensor:
    """
    Convert predictions tensor to Trajectory.data shape
    :param predictions: tensor from network
    :return: data suitable for Trajectory
    """
    num_batches = predictions.shape[0]
    return predictions.view(num_batches, -1, Trajectory.state_size())

class UrbanDriverOpenLoopModel(TorchModuleWrapper):
    """
    Vector-based model that uses PointNet-based subgraph layers for collating loose collections of vectorized inputs
    into local feature descriptors to be used as input to a global Transformer.

    Adapted from L5Kit's implementation of "Urban Driver: Learning to Drive from Real-world Demonstrations
    Using Policy Gradients":
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/open_loop_model.py
    Only the open-loop  version of the model is here represented, with slight modifications to fit the nuPlan framework.
    Changes:
        1. Use nuPlan features from NuPlanScenario
        2. Format model for using pytorch_lightning
    """

    def __init__(self, model_params: UrbanDriverOpenLoopModelParams, feature_params: UrbanDriverOpenLoopModelFeatureParams, target_params: UrbanDriverOpenLoopModelTargetParams):
        """
        Initialize UrbanDriverOpenLoop model.
        :param model_params: internal model parameters.
        :param feature_params: agent and map feature parameters.
        :param target_params: target parameters.
        """
        super().__init__(feature_builders=[VectorSetMapFeatureBuilder(map_features=feature_params.map_features, max_elements=feature_params.max_elements, max_points=feature_params.max_points, radius=feature_params.vector_set_map_feature_radius, interpolation_method=feature_params.interpolation_method), GenericAgentsFeatureBuilder(feature_params.agent_features, feature_params.past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(target_params.future_trajectory_sampling)], future_trajectory_sampling=target_params.future_trajectory_sampling)
        self._model_params = model_params
        self._feature_params = feature_params
        self._target_params = target_params
        self.feature_embedding = nn.Linear(self._feature_params.feature_dimension, self._model_params.local_embedding_size)
        self.positional_embedding = SinusoidalPositionalEmbedding(self._model_params.local_embedding_size)
        self.type_embedding = TypeEmbedding(self._model_params.global_embedding_size, self._feature_params.feature_types)
        self.local_subgraph = LocalSubGraph(num_layers=self._model_params.num_subgraph_layers, dim_in=self._model_params.local_embedding_size)
        if self._model_params.global_embedding_size != self._model_params.local_embedding_size:
            self.global_from_local = nn.Linear(self._model_params.local_embedding_size, self._model_params.global_embedding_size)
        num_timesteps = self.future_trajectory_sampling.num_poses
        self.global_head = MultiheadAttentionGlobalHead(self._model_params.global_embedding_size, num_timesteps, self._target_params.num_output_features // num_timesteps, dropout=self._model_params.global_head_dropout)

    def extract_agent_features(self, ego_agent_features: GenericAgents, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract ego and agent features into format expected by network and build accompanying availability matrix.
        :param ego_agent_features: agent features to be extracted (ego + other agents)
        :param batch_size: number of samples in batch to extract
        :return:
            agent_features: <torch.FloatTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element, feature_dimension>. Stacked ego, agent, and map features.
            agent_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
        agent_features = []
        agent_avails = []
        for sample_idx in range(batch_size):
            sample_ego_feature = ego_agent_features.ego[sample_idx][..., :min(self._feature_params.ego_dimension, self._feature_params.feature_dimension)].unsqueeze(0)
            if min(self._feature_params.ego_dimension, GenericAgents.ego_state_dim()) < self._feature_params.feature_dimension:
                sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.feature_dimension, dim=2)
            sample_ego_avails = torch.ones(sample_ego_feature.shape[0], sample_ego_feature.shape[1], dtype=torch.bool, device=sample_ego_feature.device)
            sample_ego_feature = torch.flip(sample_ego_feature, dims=[1])
            sample_ego_feature = sample_ego_feature[:, :self._feature_params.total_max_points, ...]
            sample_ego_avails = sample_ego_avails[:, :self._feature_params.total_max_points, ...]
            if sample_ego_feature.shape[1] < self._feature_params.total_max_points:
                sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.total_max_points, dim=1)
                sample_ego_avails = pad_avails(sample_ego_avails, self._feature_params.total_max_points, dim=1)
            sample_features = [sample_ego_feature]
            sample_avails = [sample_ego_avails]
            for feature_name in self._feature_params.agent_features:
                if ego_agent_features.has_agents(feature_name, sample_idx):
                    sample_agent_features = torch.permute(ego_agent_features.agents[feature_name][sample_idx], (1, 0, 2))
                    sample_agent_features = sample_agent_features[..., :min(self._feature_params.agent_dimension, self._feature_params.feature_dimension)]
                    if min(self._feature_params.agent_dimension, GenericAgents.agents_states_dim()) < self._feature_params.feature_dimension:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.feature_dimension, dim=2)
                    sample_agent_avails = torch.ones(sample_agent_features.shape[0], sample_agent_features.shape[1], dtype=torch.bool, device=sample_agent_features.device)
                    sample_agent_features = torch.flip(sample_agent_features, dims=[1])
                    sample_agent_features = sample_agent_features[:, :self._feature_params.total_max_points, ...]
                    sample_agent_avails = sample_agent_avails[:, :self._feature_params.total_max_points, ...]
                    if sample_agent_features.shape[1] < self._feature_params.total_max_points:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.total_max_points, dim=1)
                        sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.total_max_points, dim=1)
                    sample_agent_features = sample_agent_features[:self._feature_params.max_agents, ...]
                    sample_agent_avails = sample_agent_avails[:self._feature_params.max_agents, ...]
                    if sample_agent_features.shape[0] < self._feature_params.max_agents:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.max_agents, dim=0)
                        sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.max_agents, dim=0)
                else:
                    sample_agent_features = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, self._feature_params.feature_dimension, dtype=torch.float32, device=sample_ego_feature.device)
                    sample_agent_avails = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, dtype=torch.bool, device=sample_agent_features.device)
                sample_features.append(sample_agent_features)
                sample_avails.append(sample_agent_avails)
            sample_features = torch.cat(sample_features, dim=0)
            sample_avails = torch.cat(sample_avails, dim=0)
            agent_features.append(sample_features)
            agent_avails.append(sample_avails)
        agent_features = torch.stack(agent_features)
        agent_avails = torch.stack(agent_avails)
        return (agent_features, agent_avails)

    def extract_map_features(self, vector_set_map_data: VectorSetMap, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract map features into format expected by network and build accompanying availability matrix.
        :param vector_set_map_data: VectorSetMap features to be extracted
        :param batch_size: number of samples in batch to extract
        :return:
            map_features: <torch.FloatTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element, feature_dimension>. Stacked map features.
            map_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
        map_features = []
        map_avails = []
        for sample_idx in range(batch_size):
            sample_map_features = []
            sample_map_avails = []
            for feature_name in self._feature_params.map_features:
                coords = vector_set_map_data.coords[feature_name][sample_idx]
                tl_data = vector_set_map_data.traffic_light_data[feature_name][sample_idx] if feature_name in vector_set_map_data.traffic_light_data else None
                avails = vector_set_map_data.availabilities[feature_name][sample_idx]
                if tl_data is not None:
                    coords = torch.cat((coords, tl_data), dim=2)
                coords = coords[:, :self._feature_params.total_max_points, ...]
                avails = avails[:, :self._feature_params.total_max_points]
                if coords.shape[1] < self._feature_params.total_max_points:
                    coords = pad_polylines(coords, self._feature_params.total_max_points, dim=1)
                    avails = pad_avails(avails, self._feature_params.total_max_points, dim=1)
                coords = coords[..., :self._feature_params.feature_dimension]
                if coords.shape[2] < self._feature_params.feature_dimension:
                    coords = pad_polylines(coords, self._feature_params.feature_dimension, dim=2)
                sample_map_features.append(coords)
                sample_map_avails.append(avails)
            map_features.append(torch.cat(sample_map_features))
            map_avails.append(torch.cat(sample_map_avails))
        map_features = torch.stack(map_features)
        map_avails = torch.stack(map_avails)
        return (map_features, map_avails)

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "vector_set_map": VectorSetMap,
                            "generic_agents": GenericAgents,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        vector_set_map_data = cast(VectorSetMap, features['vector_set_map'])
        ego_agent_features = cast(GenericAgents, features['generic_agents'])
        batch_size = ego_agent_features.batch_size
        agent_features, agent_avails = self.extract_agent_features(ego_agent_features, batch_size)
        map_features, map_avails = self.extract_map_features(vector_set_map_data, batch_size)
        features = torch.cat([agent_features, map_features], dim=1)
        avails = torch.cat([agent_avails, map_avails], dim=1)
        feature_embedding = self.feature_embedding(features)
        pos_embedding = self.positional_embedding(features).unsqueeze(0).transpose(1, 2)
        invalid_mask = ~avails
        invalid_polys = invalid_mask.all(-1)
        embeddings = self.local_subgraph(feature_embedding, invalid_mask, pos_embedding)
        if hasattr(self, 'global_from_local'):
            embeddings = self.global_from_local(embeddings)
        embeddings = F.normalize(embeddings, dim=-1) * self._model_params.global_embedding_size ** 0.5
        embeddings = embeddings.transpose(0, 1)
        type_embedding = self.type_embedding(batch_size, self._feature_params.max_agents, self._feature_params.agent_features, self._feature_params.map_features, self._feature_params.max_elements, device=features.device).transpose(0, 1)
        if self._feature_params.disable_agents:
            invalid_polys[:, 1:1 + self._feature_params.max_agents * len(self._feature_params.agent_features)] = 1
        if self._feature_params.disable_map:
            invalid_polys[:, 1 + self._feature_params.max_agents * len(self._feature_params.agent_features):] = 1
        invalid_polys[:, 0] = 0
        outputs, attns = self.global_head(embeddings, type_embedding, invalid_polys)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(outputs))}

def extract_agent_features(self, ego_agent_features: GenericAgents, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
    """
        Extract ego and agent features into format expected by network and build accompanying availability matrix.
        :param ego_agent_features: agent features to be extracted (ego + other agents)
        :param batch_size: number of samples in batch to extract
        :return:
            agent_features: <torch.FloatTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element, feature_dimension>. Stacked ego, agent, and map features.
            agent_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
    agent_features = []
    agent_avails = []
    for sample_idx in range(batch_size):
        sample_ego_feature = ego_agent_features.ego[sample_idx][..., :min(self._feature_params.ego_dimension, self._feature_params.feature_dimension)].unsqueeze(0)
        if min(self._feature_params.ego_dimension, GenericAgents.ego_state_dim()) < self._feature_params.feature_dimension:
            sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.feature_dimension, dim=2)
        sample_ego_avails = torch.ones(sample_ego_feature.shape[0], sample_ego_feature.shape[1], dtype=torch.bool, device=sample_ego_feature.device)
        sample_ego_feature = torch.flip(sample_ego_feature, dims=[1])
        sample_ego_feature = sample_ego_feature[:, :self._feature_params.total_max_points, ...]
        sample_ego_avails = sample_ego_avails[:, :self._feature_params.total_max_points, ...]
        if sample_ego_feature.shape[1] < self._feature_params.total_max_points:
            sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.total_max_points, dim=1)
            sample_ego_avails = pad_avails(sample_ego_avails, self._feature_params.total_max_points, dim=1)
        sample_features = [sample_ego_feature]
        sample_avails = [sample_ego_avails]
        for feature_name in self._feature_params.agent_features:
            if ego_agent_features.has_agents(feature_name, sample_idx):
                sample_agent_features = torch.permute(ego_agent_features.agents[feature_name][sample_idx], (1, 0, 2))
                sample_agent_features = sample_agent_features[..., :min(self._feature_params.agent_dimension, self._feature_params.feature_dimension)]
                if min(self._feature_params.agent_dimension, GenericAgents.agents_states_dim()) < self._feature_params.feature_dimension:
                    sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.feature_dimension, dim=2)
                sample_agent_avails = torch.ones(sample_agent_features.shape[0], sample_agent_features.shape[1], dtype=torch.bool, device=sample_agent_features.device)
                sample_agent_features = torch.flip(sample_agent_features, dims=[1])
                sample_agent_features = sample_agent_features[:, :self._feature_params.total_max_points, ...]
                sample_agent_avails = sample_agent_avails[:, :self._feature_params.total_max_points, ...]
                if sample_agent_features.shape[1] < self._feature_params.total_max_points:
                    sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.total_max_points, dim=1)
                    sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.total_max_points, dim=1)
                sample_agent_features = sample_agent_features[:self._feature_params.max_agents, ...]
                sample_agent_avails = sample_agent_avails[:self._feature_params.max_agents, ...]
                if sample_agent_features.shape[0] < self._feature_params.max_agents:
                    sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.max_agents, dim=0)
                    sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.max_agents, dim=0)
            else:
                sample_agent_features = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, self._feature_params.feature_dimension, dtype=torch.float32, device=sample_ego_feature.device)
                sample_agent_avails = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, dtype=torch.bool, device=sample_agent_features.device)
            sample_features.append(sample_agent_features)
            sample_avails.append(sample_agent_avails)
        sample_features = torch.cat(sample_features, dim=0)
        sample_avails = torch.cat(sample_avails, dim=0)
        agent_features.append(sample_features)
        agent_avails.append(sample_avails)
    agent_features = torch.stack(agent_features)
    agent_avails = torch.stack(agent_avails)
    return (agent_features, agent_avails)

def extract_map_features(self, vector_set_map_data: VectorSetMap, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
    """
        Extract map features into format expected by network and build accompanying availability matrix.
        :param vector_set_map_data: VectorSetMap features to be extracted
        :param batch_size: number of samples in batch to extract
        :return:
            map_features: <torch.FloatTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element, feature_dimension>. Stacked map features.
            map_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
    map_features = []
    map_avails = []
    for sample_idx in range(batch_size):
        sample_map_features = []
        sample_map_avails = []
        for feature_name in self._feature_params.map_features:
            coords = vector_set_map_data.coords[feature_name][sample_idx]
            tl_data = vector_set_map_data.traffic_light_data[feature_name][sample_idx] if feature_name in vector_set_map_data.traffic_light_data else None
            avails = vector_set_map_data.availabilities[feature_name][sample_idx]
            if tl_data is not None:
                coords = torch.cat((coords, tl_data), dim=2)
            coords = coords[:, :self._feature_params.total_max_points, ...]
            avails = avails[:, :self._feature_params.total_max_points]
            if coords.shape[1] < self._feature_params.total_max_points:
                coords = pad_polylines(coords, self._feature_params.total_max_points, dim=1)
                avails = pad_avails(avails, self._feature_params.total_max_points, dim=1)
            coords = coords[..., :self._feature_params.feature_dimension]
            if coords.shape[2] < self._feature_params.feature_dimension:
                coords = pad_polylines(coords, self._feature_params.feature_dimension, dim=2)
            sample_map_features.append(coords)
            sample_map_avails.append(avails)
        map_features.append(torch.cat(sample_map_features))
        map_avails.append(torch.cat(sample_map_avails))
    map_features = torch.stack(map_features)
    map_avails = torch.stack(map_avails)
    return (map_features, map_avails)

def forward(self, features: FeaturesType) -> TargetsType:
    """
        Predict
        :param features: input features containing
                        {
                            "vector_set_map": VectorSetMap,
                            "generic_agents": GenericAgents,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
    vector_set_map_data = cast(VectorSetMap, features['vector_set_map'])
    ego_agent_features = cast(GenericAgents, features['generic_agents'])
    batch_size = ego_agent_features.batch_size
    agent_features, agent_avails = self.extract_agent_features(ego_agent_features, batch_size)
    map_features, map_avails = self.extract_map_features(vector_set_map_data, batch_size)
    features = torch.cat([agent_features, map_features], dim=1)
    avails = torch.cat([agent_avails, map_avails], dim=1)
    feature_embedding = self.feature_embedding(features)
    pos_embedding = self.positional_embedding(features).unsqueeze(0).transpose(1, 2)
    invalid_mask = ~avails
    invalid_polys = invalid_mask.all(-1)
    embeddings = self.local_subgraph(feature_embedding, invalid_mask, pos_embedding)
    if hasattr(self, 'global_from_local'):
        embeddings = self.global_from_local(embeddings)
    embeddings = F.normalize(embeddings, dim=-1) * self._model_params.global_embedding_size ** 0.5
    embeddings = embeddings.transpose(0, 1)
    type_embedding = self.type_embedding(batch_size, self._feature_params.max_agents, self._feature_params.agent_features, self._feature_params.map_features, self._feature_params.max_elements, device=features.device).transpose(0, 1)
    if self._feature_params.disable_agents:
        invalid_polys[:, 1:1 + self._feature_params.max_agents * len(self._feature_params.agent_features)] = 1
    if self._feature_params.disable_map:
        invalid_polys[:, 1 + self._feature_params.max_agents * len(self._feature_params.agent_features):] = 1
    invalid_polys[:, 0] = 0
    outputs, attns = self.global_head(embeddings, type_embedding, invalid_polys)
    return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(outputs))}

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

class TestUrbanDriverOpenLoopUtils(unittest.TestCase):
    """Test UrbanDriverOpenLoop utils functions."""

    def test_pad_avails(self) -> None:
        """Test padding availability masks."""
        num_elements = 10
        num_points = 20
        input = torch.ones((num_elements, num_points), dtype=torch.bool)
        elements_padded = pad_avails(input, 20, 0)
        self.assertEqual(elements_padded.dtype, torch.bool)
        self.assertEqual(elements_padded.shape, (20, num_points))
        torch.testing.assert_allclose(elements_padded[10:, :], torch.zeros((10, num_points), dtype=torch.bool))
        points_padded = pad_avails(input, 30, 1)
        self.assertEqual(points_padded.dtype, torch.bool)
        self.assertEqual(points_padded.shape, (num_elements, 30))
        torch.testing.assert_allclose(points_padded[:, 20:], torch.zeros((num_elements, 10), dtype=torch.bool))

    def test_pad_polylines(self) -> None:
        """Test padding polyline features."""
        num_elements = 10
        num_points = 20
        num_features = 2
        input = torch.ones((num_elements, num_points, num_features), dtype=torch.float32)
        elements_padded = pad_polylines(input, 20, 0)
        self.assertEqual(elements_padded.dtype, torch.float32)
        self.assertEqual(elements_padded.shape, (20, num_points, num_features))
        torch.testing.assert_allclose(elements_padded[10:, :, :], torch.zeros((10, num_points, num_features), dtype=torch.float32))
        points_padded = pad_polylines(input, 30, 1)
        self.assertEqual(points_padded.dtype, torch.float32)
        self.assertEqual(points_padded.shape, (num_elements, 30, num_features))
        torch.testing.assert_allclose(points_padded[:, 20:, :], torch.zeros((num_elements, 10, num_features), dtype=torch.float32))
        features_padded = pad_polylines(input, 3, 2)
        self.assertEqual(features_padded.dtype, torch.float32)
        self.assertEqual(features_padded.shape, (num_elements, num_points, 3))
        torch.testing.assert_allclose(features_padded[:, :, 2:], torch.zeros((num_elements, num_points, 1), dtype=torch.float32))

def test_pad_avails(self) -> None:
    """Test padding availability masks."""
    num_elements = 10
    num_points = 20
    input = torch.ones((num_elements, num_points), dtype=torch.bool)
    elements_padded = pad_avails(input, 20, 0)
    self.assertEqual(elements_padded.dtype, torch.bool)
    self.assertEqual(elements_padded.shape, (20, num_points))
    torch.testing.assert_allclose(elements_padded[10:, :], torch.zeros((10, num_points), dtype=torch.bool))
    points_padded = pad_avails(input, 30, 1)
    self.assertEqual(points_padded.dtype, torch.bool)
    self.assertEqual(points_padded.shape, (num_elements, 30))
    torch.testing.assert_allclose(points_padded[:, 20:], torch.zeros((num_elements, 10), dtype=torch.bool))

def test_pad_polylines(self) -> None:
    """Test padding polyline features."""
    num_elements = 10
    num_points = 20
    num_features = 2
    input = torch.ones((num_elements, num_points, num_features), dtype=torch.float32)
    elements_padded = pad_polylines(input, 20, 0)
    self.assertEqual(elements_padded.dtype, torch.float32)
    self.assertEqual(elements_padded.shape, (20, num_points, num_features))
    torch.testing.assert_allclose(elements_padded[10:, :, :], torch.zeros((10, num_points, num_features), dtype=torch.float32))
    points_padded = pad_polylines(input, 30, 1)
    self.assertEqual(points_padded.dtype, torch.float32)
    self.assertEqual(points_padded.shape, (num_elements, 30, num_features))
    torch.testing.assert_allclose(points_padded[:, 20:, :], torch.zeros((num_elements, 10, num_features), dtype=torch.float32))
    features_padded = pad_polylines(input, 3, 2)
    self.assertEqual(features_padded.dtype, torch.float32)
    self.assertEqual(features_padded.shape, (num_elements, num_points, 3))
    torch.testing.assert_allclose(features_padded[:, :, 2:], torch.zeros((num_elements, num_points, 1), dtype=torch.float32))

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

def test_forward(self) -> None:
    """Test forward()."""
    num_inputs = 10
    inputs = torch.zeros((num_inputs, self.dim_in))
    output = self.model.forward(inputs)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_inputs, self.dim_in))

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

def test_forward(self) -> None:
    """Test forward()."""
    num_inputs = 10
    inputs = torch.zeros((num_inputs, self.input_dim))
    output = self.model.forward(inputs)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_inputs, self.output_dim))

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

def test_forward(self) -> None:
    """Test forward()."""
    batch_size = 2
    num_elements = 10
    num_points = 20
    inputs = torch.zeros((batch_size, num_elements, num_points, self.embedding_size))
    output = self.model.forward(inputs)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_points, 1, self.embedding_size))

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

def test_forward(self) -> None:
    """Test forward()."""
    num_elements = 10
    num_points = 20
    inputs = torch.zeros((num_elements, num_points, self.dim_in))
    invalid_mask = torch.zeros((num_elements, num_points), dtype=torch.bool)
    output = self.model.forward(inputs, invalid_mask)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_elements, num_points, self.dim_out))

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

def test_forward(self) -> None:
    """Test forward()."""
    num_actors = 3
    actor_features = torch.zeros((num_actors, self.actor_feature_len))
    actor_centers = torch.zeros((num_actors, 2))
    output = self.model.forward(actor_features, actor_centers)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_actors, self.actor_feature_len))

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

def test_forward(self) -> None:
    """Test forward()."""
    num_lanes = 4
    lane_input = torch.zeros((num_lanes, self.lane_input_len, 2))
    multi_scale_connections = {1: torch.tensor([[0, 1], [1, 2], [2, 3]]), 2: torch.tensor([[0, 2], [1, 3]])}
    vector_map = Munch(multi_scale_connections=multi_scale_connections)
    output = self.model.forward(lane_input, vector_map.multi_scale_connections)
    self.assertIsInstance(output, torch.Tensor)
    self.assertEqual(output.shape, (num_lanes, self.lane_feature_len))

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

def _create_empty_vector_map_for_test(device: torch.device) -> VectorMap:
    """
    Helper function to create a dummy empty vector map solely for testing purposes.
    :param device: The device on which to place the constructed vector map.
    :return: A VectorMap with batch size 1 but otherwise empty features.
    """
    coords = [torch.zeros(size=(0, 2, 2), dtype=torch.float32, device=device)]
    lane_groupings = [[torch.zeros(size=(0,), dtype=torch.float32, device=device)]]
    multi_scale_connections = {1: [torch.zeros(size=(0, 2), dtype=torch.float32, device=device)]}
    on_route_status = [torch.zeros(size=(0, VectorMap.on_route_status_encoding_dim()), dtype=torch.float32, device=device)]
    traffic_light_data = [torch.zeros(size=(0, 4), dtype=torch.float32, device=device)]
    return VectorMap(coords=coords, lane_groupings=lane_groupings, multi_scale_connections=multi_scale_connections, on_route_status=on_route_status, traffic_light_data=traffic_light_data)

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

class DeepDynamicalSystemLayer(nn.Module):
    """
    Class to forward simulate a dynamical systems
    for k steps, given an initial condition and
    inputs for each k step.

    By subclassing nn.Module, it can be integrated
    in a pipeline where gradient-based optimization
    is employed.

    Adapted from https://arxiv.org/abs/1908.00219 (Eq.ns 6 in
    the paper have slightly different kinematics)
    """

    def __init__(self, dynamics: DynamicsLayer) -> None:
        """
        Class constructor.
        """
        super().__init__()
        self.dynamics = dynamics

    def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, agents_pars: torch.FloatTensor) -> torch.FloatTensor:
        """
        Forward pass.
        Returns state at each time step k

        :param initial_state: torch.FloatTensor [..., dynamics.state_dim()]
        :param controls: torch.FloatTensor[..., k, dynamics.control_dim()]
        :param timestep: float
        :param agents_pars: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., k, dynamics.state_dim()]
        """
        if initial_state.shape[-1] != self.dynamics.state_dim():
            raise RuntimeError(f'State dimension must be {self.dynamics.state_dim()}, got {initial_state.shape[-1]}')
        if controls.shape[-1] != self.dynamics.input_dim():
            raise RuntimeError(f'Control dimension must be {self.dynamics.input_dim()}, got {controls.shape[-1]}')
        xout = torch.empty((*controls.shape[:-1], self.dynamics.state_dim()), dtype=initial_state.dtype, device=initial_state.device)
        for i in range(controls.shape[-2]):
            initial_state = self.dynamics.forward(initial_state, controls[..., i, :], timestep, agents_pars)
            xout[..., i, :] = initial_state
        return xout

def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, agents_pars: torch.FloatTensor) -> torch.FloatTensor:
    """
        Forward pass.
        Returns state at each time step k

        :param initial_state: torch.FloatTensor [..., dynamics.state_dim()]
        :param controls: torch.FloatTensor[..., k, dynamics.control_dim()]
        :param timestep: float
        :param agents_pars: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., k, dynamics.state_dim()]
        """
    if initial_state.shape[-1] != self.dynamics.state_dim():
        raise RuntimeError(f'State dimension must be {self.dynamics.state_dim()}, got {initial_state.shape[-1]}')
    if controls.shape[-1] != self.dynamics.input_dim():
        raise RuntimeError(f'Control dimension must be {self.dynamics.input_dim()}, got {controls.shape[-1]}')
    xout = torch.empty((*controls.shape[:-1], self.dynamics.state_dim()), dtype=initial_state.dtype, device=initial_state.device)
    for i in range(controls.shape[-2]):
        initial_state = self.dynamics.forward(initial_state, controls[..., i, :], timestep, agents_pars)
        xout[..., i, :] = initial_state
    return xout

class TestDeepKinematicBicycleLayer(unittest.TestCase):
    """
    Test Deep Kinematic Layer.
    """

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.dev = torch.device('cpu')
        self.dtype = torch.float
        self.layer = DeepDynamicalSystemLayer(dynamics=KinematicBicycleLayerRearAxle())
        self.layer.to(device=self.dev)
        self.wheelbase = torch.tensor([2.5], device=self.dev, dtype=self.dtype)
        self.timestep = 0.5
        self.x0 = torch.tensor([0.1, -0.2, 0.0, 0.7, -0.4, 0.1], device=self.dev, dtype=self.dtype)

    def assert_gradient_element_almost_equal(self, x0: torch.Tensor, control: torch.Tensor, manual_grad: torch.Tensor, el: int, control_idx: int) -> None:
        """
        Auxiliary function to ensure single element
        of the gradient is computed correctly.
        """
        ctrl = control.clone().detach().requires_grad_(True)
        xnext = self.layer.forward(x0, ctrl, self.timestep, self.wheelbase)
        xnext[0, el].backward()
        self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 0].item(), manual_grad[el, 0].item())
        self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 1].item(), manual_grad[el, 1].item())

    def test_autograd_computation_one_step(self) -> None:
        """
        Test autograd calculations for DeepKinematicLayer (one step prediction)
        """
        acceleration = 0.75
        steering_angle = 0.3
        manual_grad = kinematic_bicycle_rear_axle_manual_grad(acceleration, steering_angle, self.timestep, self.x0, self.wheelbase)
        control = torch.tensor([acceleration, steering_angle], device=self.dev, dtype=self.dtype).reshape(1, -1).requires_grad_(True)
        for i in range(self.layer.dynamics.state_dim()):
            self.assert_gradient_element_almost_equal(self.x0, control, manual_grad, i, 0)

    def test_autograd_computation_no_future_leak(self) -> None:
        """
        Check states' gradient does not depend
        on future inputs
        """
        acceleration = 0.75
        steering_angle = 0.3
        control = torch.tensor([[acceleration, steering_angle], [acceleration, -steering_angle]], device=self.dev, dtype=self.dtype).requires_grad_(True)
        for i in range(self.layer.dynamics.state_dim()):
            for k in range(control.shape[-2]):
                for j in range(k):
                    ctrl = control.clone().detach().requires_grad_(True)
                    xnext = self.layer.forward(self.x0, ctrl, self.timestep, self.wheelbase)
                    xnext[j, i].backward()
                    self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 0].item(), 0.0)
                    self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 1].item(), 0.0)

    class MockDynamics(DynamicsLayer):
        """Mock dynamics for testing forward pass"""

        def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
            """Dummy forward pass"""
            x = initial_state[..., 0] + controls[..., 0]
            y = initial_state[..., 1] * controls[..., 0]
            return torch.stack((x, y), dim=-1)

        @staticmethod
        def state_dim() -> int:
            """State dim"""
            return 2

        @staticmethod
        def input_dim() -> int:
            """Input dim"""
            return 1

    def test_forward_pass_mock_layer(self) -> None:
        """
        Check forward pass by employing
        a dummy dynamics layer
        """
        mockdynamics = self.MockDynamics()
        layer = DeepDynamicalSystemLayer(dynamics=mockdynamics)
        x0 = torch.tensor([0.0, -1.0], device=self.dev, dtype=self.dtype)
        control = torch.tensor([[2.0], [-1.0]], device=self.dev, dtype=self.dtype)
        xfinal = layer.forward(x0, control, float('nan'), torch.tensor([]))
        xexp = mockdynamics.forward(mockdynamics.forward(x0, control[0, :], float('nan'), torch.tensor([])), control[1, :], float('nan'), torch.tensor([]))
        for i in range(layer.dynamics.state_dim()):
            self.assertAlmostEqual(xfinal[-1, i].item(), xexp[i].item())

    def test_forward_pass_throws(self) -> None:
        """
        Check forward throws when using
        input with wrong size
        """
        mockdynamics = self.MockDynamics()
        layer = DeepDynamicalSystemLayer(dynamics=mockdynamics)
        x0 = torch.tensor([0.0, -1.0, 1.0], device=self.dev, dtype=self.dtype)
        control = torch.tensor([[2.0], [-1.0]], device=self.dev, dtype=self.dtype)
        with self.assertRaises(RuntimeError):
            layer.forward(x0, control, float('nan'), torch.tensor([]))
        x0 = torch.tensor([0.0, -1.0], device=self.dev, dtype=self.dtype)
        control = torch.tensor([[2.0, 1.0], [-1.0, 2.0]], device=self.dev, dtype=self.dtype)
        with self.assertRaises(RuntimeError):
            layer.forward(x0, control, float('nan'), torch.tensor([]))
        x0 = torch.tensor([0.0, -1.0, 1.0], device=self.dev, dtype=self.dtype)
        with self.assertRaises(RuntimeError):
            layer.forward(x0, control, float('nan'), torch.tensor([]))

def setUp(self) -> None:
    """Sets variables for testing"""
    self.dev = torch.device('cpu')
    self.dtype = torch.float
    self.layer = DeepDynamicalSystemLayer(dynamics=KinematicBicycleLayerRearAxle())
    self.layer.to(device=self.dev)
    self.wheelbase = torch.tensor([2.5], device=self.dev, dtype=self.dtype)
    self.timestep = 0.5
    self.x0 = torch.tensor([0.1, -0.2, 0.0, 0.7, -0.4, 0.1], device=self.dev, dtype=self.dtype)

def assert_gradient_element_almost_equal(self, x0: torch.Tensor, control: torch.Tensor, manual_grad: torch.Tensor, el: int, control_idx: int) -> None:
    """
        Auxiliary function to ensure single element
        of the gradient is computed correctly.
        """
    ctrl = control.clone().detach().requires_grad_(True)
    xnext = self.layer.forward(x0, ctrl, self.timestep, self.wheelbase)
    xnext[0, el].backward()
    self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 0].item(), manual_grad[el, 0].item())
    self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 1].item(), manual_grad[el, 1].item())

def test_autograd_computation_one_step(self) -> None:
    """
        Test autograd calculations for DeepKinematicLayer (one step prediction)
        """
    acceleration = 0.75
    steering_angle = 0.3
    manual_grad = kinematic_bicycle_rear_axle_manual_grad(acceleration, steering_angle, self.timestep, self.x0, self.wheelbase)
    control = torch.tensor([acceleration, steering_angle], device=self.dev, dtype=self.dtype).reshape(1, -1).requires_grad_(True)
    for i in range(self.layer.dynamics.state_dim()):
        self.assert_gradient_element_almost_equal(self.x0, control, manual_grad, i, 0)

def test_autograd_computation_no_future_leak(self) -> None:
    """
        Check states' gradient does not depend
        on future inputs
        """
    acceleration = 0.75
    steering_angle = 0.3
    control = torch.tensor([[acceleration, steering_angle], [acceleration, -steering_angle]], device=self.dev, dtype=self.dtype).requires_grad_(True)
    for i in range(self.layer.dynamics.state_dim()):
        for k in range(control.shape[-2]):
            for j in range(k):
                ctrl = control.clone().detach().requires_grad_(True)
                xnext = self.layer.forward(self.x0, ctrl, self.timestep, self.wheelbase)
                xnext[j, i].backward()
                self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 0].item(), 0.0)
                self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 1].item(), 0.0)

def test_forward_pass_mock_layer(self) -> None:
    """
        Check forward pass by employing
        a dummy dynamics layer
        """
    mockdynamics = self.MockDynamics()
    layer = DeepDynamicalSystemLayer(dynamics=mockdynamics)
    x0 = torch.tensor([0.0, -1.0], device=self.dev, dtype=self.dtype)
    control = torch.tensor([[2.0], [-1.0]], device=self.dev, dtype=self.dtype)
    xfinal = layer.forward(x0, control, float('nan'), torch.tensor([]))
    xexp = mockdynamics.forward(mockdynamics.forward(x0, control[0, :], float('nan'), torch.tensor([])), control[1, :], float('nan'), torch.tensor([]))
    for i in range(layer.dynamics.state_dim()):
        self.assertAlmostEqual(xfinal[-1, i].item(), xexp[i].item())

def test_forward_pass_throws(self) -> None:
    """
        Check forward throws when using
        input with wrong size
        """
    mockdynamics = self.MockDynamics()
    layer = DeepDynamicalSystemLayer(dynamics=mockdynamics)
    x0 = torch.tensor([0.0, -1.0, 1.0], device=self.dev, dtype=self.dtype)
    control = torch.tensor([[2.0], [-1.0]], device=self.dev, dtype=self.dtype)
    with self.assertRaises(RuntimeError):
        layer.forward(x0, control, float('nan'), torch.tensor([]))
    x0 = torch.tensor([0.0, -1.0], device=self.dev, dtype=self.dtype)
    control = torch.tensor([[2.0, 1.0], [-1.0, 2.0]], device=self.dev, dtype=self.dtype)
    with self.assertRaises(RuntimeError):
        layer.forward(x0, control, float('nan'), torch.tensor([]))
    x0 = torch.tensor([0.0, -1.0, 1.0], device=self.dev, dtype=self.dtype)
    with self.assertRaises(RuntimeError):
        layer.forward(x0, control, float('nan'), torch.tensor([]))

class TestDeepKinematicUnicycleLayer(unittest.TestCase):
    """
    Test Deep Kinematic Unicycle Layer.
    """

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.dev = torch.device('cpu')
        self.dtype = torch.float
        self.layer = DeepDynamicalSystemLayer(dynamics=KinematicUnicycleLayerRearAxle())
        self.layer.to(device=self.dev)
        self.timestep = 0.5
        self.x0 = torch.tensor([0.1, -0.2, 0.0, 0.7, -0.4, 0.75, 0.0], device=self.dev, dtype=self.dtype)

    def assert_gradient_element_almost_equal(self, x0: torch.Tensor, control: torch.Tensor, manual_grad: torch.Tensor, el: int, control_idx: int) -> None:
        """
        Auxiliary function to ensure single element
        of the gradient is computed correctly.
        """
        ctrl = control.clone().detach().requires_grad_(True)
        xnext = self.layer.forward(x0, ctrl, self.timestep, None)
        xnext[0, el].backward()
        self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 0].item(), manual_grad[el, 0].item())
        self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 1].item(), manual_grad[el, 1].item())

    def test_autograd_computation_one_step(self) -> None:
        """
        Test autograd calculations for DeepKinematicLayer (one step prediction)
        """
        curvature = 0.125
        jerk = 0.3
        manual_grad = kinematic_unicycle_rear_axle_manual_grad(curvature, jerk, self.timestep, self.x0)
        control = torch.tensor([curvature, jerk], device=self.dev, dtype=self.dtype).reshape(1, -1).requires_grad_(True)
        for i in range(self.layer.dynamics.state_dim()):
            self.assert_gradient_element_almost_equal(self.x0, control, manual_grad, i, 0)

    def test_autograd_computation_no_future_leak(self) -> None:
        """
        Check states' gradient does not depend
        on future inputs
        """
        curvature = 0.125
        jerk = 0.3
        control = torch.tensor([[curvature, jerk], [curvature, -jerk]], device=self.dev, dtype=self.dtype).requires_grad_(True)
        for i in range(self.layer.dynamics.state_dim()):
            for k in range(control.shape[-2]):
                for j in range(k):
                    ctrl = control.clone().detach().requires_grad_(True)
                    xnext = self.layer.forward(self.x0, ctrl, self.timestep, None)
                    xnext[j, i].backward()
                    self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 0].item(), 0.0)
                    self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 1].item(), 0.0)

def setUp(self) -> None:
    """Sets variables for testing"""
    self.dev = torch.device('cpu')
    self.dtype = torch.float
    self.layer = DeepDynamicalSystemLayer(dynamics=KinematicUnicycleLayerRearAxle())
    self.layer.to(device=self.dev)
    self.timestep = 0.5
    self.x0 = torch.tensor([0.1, -0.2, 0.0, 0.7, -0.4, 0.75, 0.0], device=self.dev, dtype=self.dtype)

def assert_gradient_element_almost_equal(self, x0: torch.Tensor, control: torch.Tensor, manual_grad: torch.Tensor, el: int, control_idx: int) -> None:
    """
        Auxiliary function to ensure single element
        of the gradient is computed correctly.
        """
    ctrl = control.clone().detach().requires_grad_(True)
    xnext = self.layer.forward(x0, ctrl, self.timestep, None)
    xnext[0, el].backward()
    self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 0].item(), manual_grad[el, 0].item())
    self.assertAlmostEqual(ctrl.grad.detach().cpu()[control_idx, 1].item(), manual_grad[el, 1].item())

def test_autograd_computation_one_step(self) -> None:
    """
        Test autograd calculations for DeepKinematicLayer (one step prediction)
        """
    curvature = 0.125
    jerk = 0.3
    manual_grad = kinematic_unicycle_rear_axle_manual_grad(curvature, jerk, self.timestep, self.x0)
    control = torch.tensor([curvature, jerk], device=self.dev, dtype=self.dtype).reshape(1, -1).requires_grad_(True)
    for i in range(self.layer.dynamics.state_dim()):
        self.assert_gradient_element_almost_equal(self.x0, control, manual_grad, i, 0)

def test_autograd_computation_no_future_leak(self) -> None:
    """
        Check states' gradient does not depend
        on future inputs
        """
    curvature = 0.125
    jerk = 0.3
    control = torch.tensor([[curvature, jerk], [curvature, -jerk]], device=self.dev, dtype=self.dtype).requires_grad_(True)
    for i in range(self.layer.dynamics.state_dim()):
        for k in range(control.shape[-2]):
            for j in range(k):
                ctrl = control.clone().detach().requires_grad_(True)
                xnext = self.layer.forward(self.x0, ctrl, self.timestep, None)
                xnext[j, i].backward()
                self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 0].item(), 0.0)
                self.assertAlmostEqual(ctrl.grad.detach().cpu()[k, 1].item(), 0.0)

class TestKinematicBicycleLayersUtils(unittest.TestCase):
    """
    Test Kinematic Bicycle Layers utils.
    """

    def setUp(self) -> None:
        """Sets variables for testing"""
        pass

    def test_enums_equal(self) -> None:
        """
        Ensure our internal indexing matches the
        one from Agents' trajectories
        """
        self.assertEqual(StateIndex.X_POS, AgentFeatureIndex.x())
        self.assertEqual(StateIndex.Y_POS, AgentFeatureIndex.y())
        self.assertEqual(StateIndex.YAW, AgentFeatureIndex.heading())
        self.assertEqual(StateIndex.X_VELOCITY, AgentFeatureIndex.vx())
        self.assertEqual(StateIndex.Y_VELOCITY, AgentFeatureIndex.vy())
        self.assertEqual(StateIndex.YAW_RATE, AgentFeatureIndex.yaw_rate())

def test_enums_equal(self) -> None:
    """
        Ensure our internal indexing matches the
        one from Agents' trajectories
        """
    self.assertEqual(StateIndex.X_POS, AgentFeatureIndex.x())
    self.assertEqual(StateIndex.Y_POS, AgentFeatureIndex.y())
    self.assertEqual(StateIndex.YAW, AgentFeatureIndex.heading())
    self.assertEqual(StateIndex.X_VELOCITY, AgentFeatureIndex.vx())
    self.assertEqual(StateIndex.Y_VELOCITY, AgentFeatureIndex.vy())
    self.assertEqual(StateIndex.YAW_RATE, AgentFeatureIndex.yaw_rate())

class TestKinematicUnicycleLayersUtils(unittest.TestCase):
    """
    Test Kinematic Unicycle Layers utils.
    """

    def setUp(self) -> None:
        """Sets variables for testing"""
        pass

    def test_enums_equal(self) -> None:
        """
        Ensure our internal indexing matches the
        one from Ego's trajectory
        """
        self.assertEqual(StateIndex.X_POS, GenericEgoFeatureIndex.x())
        self.assertEqual(StateIndex.Y_POS, GenericEgoFeatureIndex.y())
        self.assertEqual(StateIndex.YAW, GenericEgoFeatureIndex.heading())
        self.assertEqual(StateIndex.X_VELOCITY, GenericEgoFeatureIndex.vx())
        self.assertEqual(StateIndex.Y_VELOCITY, GenericEgoFeatureIndex.vy())
        self.assertEqual(StateIndex.X_ACCEL, GenericEgoFeatureIndex.ax())
        self.assertEqual(StateIndex.Y_ACCEL, GenericEgoFeatureIndex.ay())

def test_enums_equal(self) -> None:
    """
        Ensure our internal indexing matches the
        one from Ego's trajectory
        """
    self.assertEqual(StateIndex.X_POS, GenericEgoFeatureIndex.x())
    self.assertEqual(StateIndex.Y_POS, GenericEgoFeatureIndex.y())
    self.assertEqual(StateIndex.YAW, GenericEgoFeatureIndex.heading())
    self.assertEqual(StateIndex.X_VELOCITY, GenericEgoFeatureIndex.vx())
    self.assertEqual(StateIndex.Y_VELOCITY, GenericEgoFeatureIndex.vy())
    self.assertEqual(StateIndex.X_ACCEL, GenericEgoFeatureIndex.ax())
    self.assertEqual(StateIndex.Y_ACCEL, GenericEgoFeatureIndex.ay())

class DataModule(pl.LightningDataModule):
    """
    Datamodule wrapping all preparation and dataset creation functionality.
    """

    def __init__(self, feature_preprocessor: FeaturePreprocessor, splitter: AbstractSplitter, all_scenarios: List[AbstractScenario], train_fraction: float, val_fraction: float, test_fraction: float, dataloader_params: Dict[str, Any], scenario_type_sampling_weights: DictConfig, worker: WorkerPool, augmentors: Optional[List[AbstractAugmentor]]=None) -> None:
        """
        Initialize the class.
        :param feature_preprocessor: Feature preprocessor object.
        :param splitter: Splitter object used to retrieve lists of samples to construct train/val/test sets.
        :param train_fraction: Fraction of training examples to load.
        :param val_fraction: Fraction of validation examples to load.
        :param test_fraction: Fraction of test examples to load.
        :param dataloader_params: Parameter dictionary passed to the dataloaders.
        :param augmentors: Augmentor object for providing data augmentation to data samples.
        """
        super().__init__()
        assert train_fraction > 0.0, 'Train fraction has to be larger than 0!'
        assert val_fraction > 0.0, 'Validation fraction has to be larger than 0!'
        assert test_fraction >= 0.0, 'Test fraction has to be larger/equal than 0!'
        self._train_set: Optional[torch.utils.data.Dataset] = None
        self._val_set: Optional[torch.utils.data.Dataset] = None
        self._test_set: Optional[torch.utils.data.Dataset] = None
        self._feature_preprocessor = feature_preprocessor
        self._splitter = splitter
        self._train_fraction = train_fraction
        self._val_fraction = val_fraction
        self._test_fraction = test_fraction
        self._dataloader_params = dataloader_params
        self._all_samples = all_scenarios
        assert len(self._all_samples) > 0, 'No samples were passed to the datamodule'
        self._scenario_type_sampling_weights = scenario_type_sampling_weights
        self._augmentors = augmentors
        self._worker = worker

    @property
    def feature_and_targets_builder(self) -> FeaturePreprocessor:
        """Get feature and target builders."""
        return self._feature_preprocessor

    def setup(self, stage: Optional[str]=None) -> None:
        """
        Set up the dataset for each target set depending on the training stage.
        This is called by every process in distributed training.
        :param stage: Stage of training, can be "fit" or "test".
        """
        if stage is None:
            return
        if stage == 'fit':
            train_samples = self._splitter.get_train_samples(self._all_samples, self._worker)
            assert len(train_samples) > 0, 'Splitter returned no training samples'
            self._train_set = create_dataset(train_samples, self._feature_preprocessor, self._train_fraction, 'train', self._augmentors)
            val_samples = self._splitter.get_val_samples(self._all_samples, self._worker)
            assert len(val_samples) > 0, 'Splitter returned no validation samples'
            self._val_set = create_dataset(val_samples, self._feature_preprocessor, self._val_fraction, 'validation')
        elif stage == 'test':
            test_samples = self._splitter.get_test_samples(self._all_samples, self._worker)
            assert len(test_samples) > 0, 'Splitter returned no test samples'
            self._test_set = create_dataset(test_samples, self._feature_preprocessor, self._test_fraction, 'test')
        else:
            raise ValueError(f'Stage must be one of ["fit", "test"], got ${stage}.')

    def teardown(self, stage: Optional[str]=None) -> None:
        """
        Clean up after a training stage.
        This is called by every process in distributed training.
        :param stage: Stage of training, can be "fit" or "test".
        """
        pass

    def train_dataloader(self) -> torch.utils.data.DataLoader:
        """
        Create the training dataloader.
        :raises RuntimeError: If this method is called without calling "setup()" first.
        :return: The instantiated torch dataloader.
        """
        if self._train_set is None:
            raise DataModuleNotSetupError
        if self._scenario_type_sampling_weights.enable:
            weighted_sampler = distributed_weighted_sampler_init(scenario_dataset=self._train_set, scenario_sampling_weights=self._scenario_type_sampling_weights.scenario_type_weights)
        else:
            weighted_sampler = None
        return torch.utils.data.DataLoader(dataset=self._train_set, shuffle=weighted_sampler is None, collate_fn=FeatureCollate(), sampler=weighted_sampler, **self._dataloader_params)

    def val_dataloader(self) -> torch.utils.data.DataLoader:
        """
        Create the validation dataloader.
        :raises RuntimeError: if this method is called without calling "setup()" first.
        :return: The instantiated torch dataloader.
        """
        if self._val_set is None:
            raise DataModuleNotSetupError
        return torch.utils.data.DataLoader(dataset=self._val_set, **self._dataloader_params, collate_fn=FeatureCollate())

    def test_dataloader(self) -> torch.utils.data.DataLoader:
        """
        Create the test dataloader.
        :raises RuntimeError: if this method is called without calling "setup()" first.
        :return: The instantiated torch dataloader.
        """
        if self._test_set is None:
            raise DataModuleNotSetupError
        return torch.utils.data.DataLoader(dataset=self._test_set, **self._dataloader_params, collate_fn=FeatureCollate())

    def transfer_batch_to_device(self, batch: Tuple[FeaturesType, ...], device: torch.device) -> Tuple[FeaturesType, ...]:
        """
        Transfer a batch to device.
        :param batch: Batch on origin device.
        :param device: Desired device.
        :return: Batch in new device.
        """
        return tuple((move_features_type_to_device(batch[0], device), move_features_type_to_device(batch[1], device), batch[2]))

def transfer_batch_to_device(self, batch: Tuple[FeaturesType, ...], device: torch.device) -> Tuple[FeaturesType, ...]:
    """
        Transfer a batch to device.
        :param batch: Batch on origin device.
        :param device: Desired device.
        :return: Batch in new device.
        """
    return tuple((move_features_type_to_device(batch[0], device), move_features_type_to_device(batch[1], device), batch[2]))

class TestScenarioSamplingWeights(unittest.TestCase):
    """
    Tests data loading functionality in a sequential manner.
    """

    def setUp(self) -> None:
        """Set up test variables."""
        self.mock_scenario_sampling_weights = {DEFAULT_SCENARIO_NAME: 0.5}
        self.mock_scenario_types = [DEFAULT_SCENARIO_NAME, 'following_lane_with_lead']
        self.mock_scenarios = []
        for scenario_type in self.mock_scenario_types:
            self.mock_scenarios += [CachedScenario(log_name='', token='', scenario_type=scenario_type) for _ in range(3)]
        self.expected_sampler_weights = [self.mock_scenario_sampling_weights[DEFAULT_SCENARIO_NAME]] * 3 + [1.0] * 3

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

    def test_scenario_sampling_weight_initialises_correctly(self) -> None:
        """
        Test that the scenario sampling weights are correct.
        """
        self._init_distributed_process_group()
        scenarios_dataset = Mock(ScenarioDataset)
        scenarios_dataset._scenarios = self.mock_scenarios
        distributed_weight_sampler = distributed_weighted_sampler_init(scenario_dataset=scenarios_dataset, scenario_sampling_weights=self.mock_scenario_sampling_weights)
        self.assertEqual(list(distributed_weight_sampler.sampler.weights), self.expected_sampler_weights)

def setUp(self) -> None:
    """Set up test variables."""
    self.mock_scenario_sampling_weights = {DEFAULT_SCENARIO_NAME: 0.5}
    self.mock_scenario_types = [DEFAULT_SCENARIO_NAME, 'following_lane_with_lead']
    self.mock_scenarios = []
    for scenario_type in self.mock_scenario_types:
        self.mock_scenarios += [CachedScenario(log_name='', token='', scenario_type=scenario_type) for _ in range(3)]
    self.expected_sampler_weights = [self.mock_scenario_sampling_weights[DEFAULT_SCENARIO_NAME]] * 3 + [1.0] * 3

class TestDistributedSamplerWrapper(unittest.TestCase):
    """
    Skeleton with initialized dataloader used in testing.
    """

    def setUp(self) -> None:
        """
        Set up basic configs.
        """
        self.mock_sampler = self._get_sampler()
        self.num_replicas = 4
        self.expected_indices = [[i % 10 for i in range(j, j + 3)] for j in range(0, 12, 3)]

    def _get_sampler(self) -> SequentialSampler:
        mock_sampler = SequentialSampler([i for i in range(10)])
        return mock_sampler

    def test_distributed_sampler_wrapper(self) -> None:
        """
        Tests that the indices produced by the distributed sampler wrapper are as expected.
        """
        distributed_samplers = [DistributedSamplerWrapper(sampler=self.mock_sampler, num_replicas=self.num_replicas, rank=i) for i in range(self.num_replicas)]
        for i, distributed_sampler in enumerate(distributed_samplers):
            indices = list(distributed_sampler)
            self.assertEqual(self.expected_indices[i], indices)

def setUp(self) -> None:
    """
        Set up basic configs.
        """
    self.mock_sampler = self._get_sampler()
    self.num_replicas = 4
    self.expected_indices = [[i % 10 for i in range(j, j + 3)] for j in range(0, 12, 3)]

def _get_sampler(self) -> SequentialSampler:
    mock_sampler = SequentialSampler([i for i in range(10)])
    return mock_sampler

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

def _score_model(pl_module: pl.LightningModule, features: FeaturesType, targets: TargetsType) -> Tuple[float, FeaturesType]:
    """
    Make an inference of the input batch feature given a model and score them through their objective
    :param pl_module: lightning model
    :param features: model inputs
    :param targets: training targets
    :return: tuple of score and prediction
    """
    objectives = pl_module.objectives
    with torch.no_grad():
        pl_module.eval()
        predictions = pl_module(features)
        pl_module.train()
    score = 0.0
    for objective in objectives:
        score += objective.compute(predictions, targets).to('cpu')
    return (score / len(objectives), move_features_type_to_device(predictions, torch.device('cpu')))

def _eval_model_and_write_to_scene(dataloader: torch.utils.data.DataLoader, pl_module: pl.LightningModule, scene_converter: SceneConverter, num_store: int, output_dir: Path) -> None:
    """
    Evaluate prediction of the model and write scenes based on their scores
    :param dataloader: pytorch data loader
    :param pl_module: lightning module
    :param scene_converter: converts data from the scored scenario into scene dictionary
    :param num_store: n number of scenarios to be written into scenes for each best, worst and random cases
    :param output_dir: output directory of scene file
    """
    scenario_dataset = dataloader.dataset
    score_record = torch.empty(len(scenario_dataset))
    predictions: List[TargetsType] = []
    for sample_idx, sample in enumerate(dataloader):
        features = cast(FeaturesType, sample[0])
        targets = cast(TargetsType, sample[1])
        score, prediction = _score_model(pl_module, move_features_type_to_device(features, pl_module.device), move_features_type_to_device(targets, pl_module.device))
        predictions.append(prediction)
        score_record[sample_idx] = score
    best_n_idx = torch.topk(score_record, num_store, largest=False).indices.tolist()
    worst_n_idx = torch.topk(score_record, num_store).indices.tolist()
    random_n_idx = random.sample(range(len(scenario_dataset)), num_store)
    for data_idx, score_type in zip((best_n_idx, worst_n_idx, random_n_idx), ('best', 'worst', 'random')):
        for idx in data_idx:
            features, targets, _ = scenario_dataset[idx]
            scenario = scenario_dataset._scenarios[idx]
            scenes = scene_converter(scenario, features, targets, predictions[idx])
            file_dir = output_dir / score_type / scenario.token
            if not is_s3_path(file_dir):
                file_dir.mkdir(parents=True, exist_ok=True)
            _dump_scenes(scenes, file_dir)

def _create_ego_raster(vehicle_parameters: VehicleParameters, pixel_size: float, size: int, color: int=1, thickness: int=-1) -> npt.NDArray[np.uint8]:
    """
    Create ego raster layer to be visualized.

    :param vehicle_parameters: Ego vehicle parameters dataclass object.
    :param pixel_size: [m] Size of each pixel.
    :param size: [pixels] Size of grid.
    :param color: Grid color.
    :param thickness: Box line thickness (-1 means fill).
    :return: Instantiated grid.
    """
    ego_raster: npt.NDArray[np.uint8] = np.zeros((size, size), dtype=np.uint8)
    ego_width = vehicle_parameters.width
    ego_front_length = vehicle_parameters.front_length
    ego_rear_length = vehicle_parameters.rear_length
    ego_width_pixels = int(ego_width / pixel_size)
    ego_front_length_pixels = int(ego_front_length / pixel_size)
    ego_rear_length_pixels = int(ego_rear_length / pixel_size)
    map_x_center = int(ego_raster.shape[1] * 0.5)
    map_y_center = int(ego_raster.shape[0] * 0.5)
    ego_top_left = (map_x_center - ego_width_pixels // 2, map_y_center - ego_front_length_pixels)
    ego_bottom_right = (map_x_center + ego_width_pixels // 2, map_y_center + ego_rear_length_pixels)
    cv2.rectangle(ego_raster, ego_top_left, ego_bottom_right, color=color, thickness=thickness, lineType=cv2.LINE_AA)
    return ego_raster

def mock_compute_features(scenario: AbstractScenario) -> Tuple[FeaturesType, TargetsType, None]:
    """
    Mock feature computation.
    :param scenario: Input scenario to extract features from.
    :return: Extracted features and targets.
    """
    mission_goal = scenario.get_mission_goal()
    data1 = torch.tensor(mission_goal.x)
    data2 = torch.tensor(mission_goal.y)
    data3 = torch.tensor(mission_goal.heading)
    mock_feature = DummyVectorMapFeature(data1=[data1], data2=[data2], data3=[{'test': data3}])
    mock_output = {'mock_feature': mock_feature}
    mock_cache_metadata = None
    return (mock_output, mock_output, mock_cache_metadata)

class TestScenarioScoringCallback(unittest.TestCase):
    """Test scenario scoring callback"""

    def setUp(self) -> None:
        """Set up test case."""
        self.output_dir = tempfile.TemporaryDirectory()
        preprocessor = Mock()
        preprocessor.compute_features.side_effect = mock_compute_features
        self.mock_scenarios = [MockAbstractScenario(mission_goal=StateSE2(x=1.0, y=0.0, heading=0.0)), MockAbstractScenario(mission_goal=StateSE2(x=0.0, y=0.0, heading=0.0))]
        self.scenario_time_stamp = self.mock_scenarios[0]._initial_time_us
        mock_scenario_dataset = ScenarioDataset(scenarios=self.mock_scenarios, feature_preprocessor=preprocessor)
        mock_datamodule = Mock()
        mock_datamodule.val_dataloader().dataset = mock_scenario_dataset
        self.trainer = Mock()
        self.trainer.datamodule = mock_datamodule
        self.trainer.current_epoch = 1
        mock_objective = Mock()
        mock_objective.compute.side_effect = mock_compute_objective
        self.pl_module = Mock()
        self.pl_module.device = 'cpu'
        self.pl_module.side_effect = mock_predict
        self.pl_module.objectives = [mock_objective]
        scenario_converter = ScenarioSceneConverter(ego_trajectory_horizon=1, ego_trajectory_poses=2)
        self.callback = ScenarioScoringCallback(scene_converter=scenario_converter, num_store=1, frequency=1, output_dir=self.output_dir.name)
        self.callback._initialize_dataloaders(self.trainer.datamodule)

    def test_initialize_dataloaders(self) -> None:
        """
        Test callback dataloader initialization.
        """
        invalid_datamodule = Mock()
        invalid_datamodule.val_dataloader().dataset = None
        with self.assertRaises(AssertionError):
            self.callback._initialize_dataloaders(invalid_datamodule)
        self.callback._initialize_dataloaders(self.trainer.datamodule)
        self.assertIsInstance(self.callback._val_dataloader, torch.utils.data.DataLoader)

    def test_score_model(self) -> None:
        """
        Test scoring of the model with mock features.
        """
        data1 = torch.tensor(1)
        data2 = torch.tensor(2)
        data3 = torch.tensor(3)
        mock_feature = DummyVectorMapFeature(data1=[data1], data2=[data2], data3=[{'test': data3}])
        mock_input = {'mock_feature': mock_feature}
        score, prediction = _score_model(self.pl_module, mock_input, mock_input)
        self.assertEqual(score, mock_feature.data1[0])
        self.assertEqual(prediction, mock_input)

    def test_on_validation_epoch_end(self) -> None:
        """
        Test on validation callback.
        """
        BEST_INDEX = 1
        WORST_INDEX = 0
        self.callback._initialize_dataloaders(self.trainer.datamodule)
        self.callback.on_validation_epoch_end(self.trainer, self.pl_module)
        best_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/best/{self.mock_scenarios[BEST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
        self.assertTrue(best_score_path.exists())
        worst_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/worst/{self.mock_scenarios[WORST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
        self.assertTrue(worst_score_path.exists())
        random_score_dir = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}/random/')
        random_score_paths = list(random_score_dir.glob(f'*/{self.scenario_time_stamp.time_us}.json'))
        self.assertEqual(len(random_score_paths), 1)
        with open(str(best_score_path), 'r') as f:
            best_data = json.load(f)
        with open(str(worst_score_path), 'r') as f:
            worst_data = json.load(f)
        self.assertEqual(worst_data['goal']['pose'][0], self.mock_scenarios[WORST_INDEX].get_mission_goal().x)
        self.assertEqual(best_data['goal']['pose'][0], self.mock_scenarios[BEST_INDEX].get_mission_goal().x)

def test_score_model(self) -> None:
    """
        Test scoring of the model with mock features.
        """
    data1 = torch.tensor(1)
    data2 = torch.tensor(2)
    data3 = torch.tensor(3)
    mock_feature = DummyVectorMapFeature(data1=[data1], data2=[data2], data3=[{'test': data3}])
    mock_input = {'mock_feature': mock_feature}
    score, prediction = _score_model(self.pl_module, mock_input, mock_input)
    self.assertEqual(score, mock_feature.data1[0])
    self.assertEqual(prediction, mock_input)

class TestVisualizationUtils(unittest.TestCase):
    """Unit tests for visualization utlities."""

    def test_raster_visualization(self) -> None:
        """
        Test raster visualization utils.
        """
        trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
        trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
        size = 224
        raster = Raster(data=np.zeros((1, size, size, 4)))
        image = get_raster_with_trajectories_as_rgb(raster, trajectory_1, trajectory_2)
        self.assertEqual(image.shape, (size, size, 3))
        self.assertTrue(np.any(image))

    def test_vector_map_agents_visualization(self) -> None:
        """
        Test vector map and agents visualization utils.
        """
        trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
        trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
        pixel_size = 0.5
        radius = 50.0
        size = int(2 * radius / pixel_size)
        vector_map = VectorMap(coords=[np.zeros((1000, 2, 2))], lane_groupings=[[]], multi_scale_connections=[{}], on_route_status=[np.zeros((1000, 2))], traffic_light_data=[np.zeros((1000, 4))])
        agents = Agents(ego=[np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))], agents=[np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])])
        image = get_raster_from_vector_map_with_agents(vector_map, agents, trajectory_1, trajectory_2, pixel_size=pixel_size, radius=radius)
        self.assertEqual(image.shape, (size, size, 3))
        self.assertTrue(np.any(image))

    def test_vector_set_map_generic_agents_visualization(self) -> None:
        """
        Test vector set map and generic agents visualization utils.
        """
        trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
        trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
        pixel_size = 0.5
        radius = 50.0
        size = int(2 * radius / pixel_size)
        agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE']
        vector_set_map = VectorSetMap(coords={VectorFeatureLayer.LANE.name: [np.zeros((100, 100, 2))]}, traffic_light_data={}, availabilities={VectorFeatureLayer.LANE.name: [np.ones((100, 100), dtype=bool)]})
        agents = GenericAgents(ego=[np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))], agents={feature_name: [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])] for feature_name in agent_features})
        image = get_raster_from_vector_map_with_agents(vector_set_map, agents, trajectory_1, trajectory_2, pixel_size=pixel_size, radius=radius)
        self.assertEqual(image.shape, (size, size, 3))
        self.assertTrue(np.any(image))

def test_raster_visualization(self) -> None:
    """
        Test raster visualization utils.
        """
    trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
    trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
    size = 224
    raster = Raster(data=np.zeros((1, size, size, 4)))
    image = get_raster_with_trajectories_as_rgb(raster, trajectory_1, trajectory_2)
    self.assertEqual(image.shape, (size, size, 3))
    self.assertTrue(np.any(image))

def test_vector_map_agents_visualization(self) -> None:
    """
        Test vector map and agents visualization utils.
        """
    trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
    trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
    pixel_size = 0.5
    radius = 50.0
    size = int(2 * radius / pixel_size)
    vector_map = VectorMap(coords=[np.zeros((1000, 2, 2))], lane_groupings=[[]], multi_scale_connections=[{}], on_route_status=[np.zeros((1000, 2))], traffic_light_data=[np.zeros((1000, 4))])
    agents = Agents(ego=[np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))], agents=[np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])])
    image = get_raster_from_vector_map_with_agents(vector_map, agents, trajectory_1, trajectory_2, pixel_size=pixel_size, radius=radius)
    self.assertEqual(image.shape, (size, size, 3))
    self.assertTrue(np.any(image))

def test_vector_set_map_generic_agents_visualization(self) -> None:
    """
        Test vector set map and generic agents visualization utils.
        """
    trajectory_1 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]]))
    trajectory_2 = Trajectory(data=np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0], [0.0, 3.0, 0.0]]))
    pixel_size = 0.5
    radius = 50.0
    size = int(2 * radius / pixel_size)
    agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE']
    vector_set_map = VectorSetMap(coords={VectorFeatureLayer.LANE.name: [np.zeros((100, 100, 2))]}, traffic_light_data={}, availabilities={VectorFeatureLayer.LANE.name: [np.ones((100, 100), dtype=bool)]})
    agents = GenericAgents(ego=[np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))], agents={feature_name: [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])] for feature_name in agent_features})
    image = get_raster_from_vector_map_with_agents(vector_set_map, agents, trajectory_1, trajectory_2, pixel_size=pixel_size, radius=radius)
    self.assertEqual(image.shape, (size, size, 3))
    self.assertTrue(np.any(image))

def _batch_abstract_features(initial_not_batched_features: FeaturesType, to_be_batched_features: List[FeaturesType]) -> FeaturesType:
    """
    Batch abstract feature with custom collate function
    :param initial_not_batched_features: features from initial batch which are used only for keys
    :param to_be_batched_features: list of features which should be batched
    :return: batched features
    """
    output_features = {}
    for key in initial_not_batched_features.keys():
        list_features = [feature_single[key] for feature_single in to_be_batched_features]
        output_features[key] = initial_not_batched_features[key].collate(list_features)
    return output_features

def _validate_ego_feature_shape(feature: torch.Tensor) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be an EgoFeature.
    :param feature: The tensor to validate.
    """
    if len(feature.shape) == 2 and feature.shape[1] == EgoFeatureIndex.dim():
        return
    if len(feature.shape) == 1 and feature.shape[0] == EgoFeatureIndex.dim():
        return
    raise ValueError(f'Improper ego feature shape: {feature.shape}.')

def _validate_agent_feature_shape(feature: torch.Tensor) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be an AgentFeature.
    :param feature: The tensor to validate.
    """
    if len(feature.shape) != 3 or feature.shape[2] != AgentFeatureIndex.dim():
        raise ValueError(f'Improper agent feature shape: {feature.shape}.')

def _validate_generic_ego_feature_shape(feature: torch.Tensor) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be a GenericEgoFeature.
    :param feature: The tensor to validate.
    """
    if len(feature.shape) == 2 and feature.shape[1] == GenericEgoFeatureIndex.dim():
        return
    if len(feature.shape) == 1 and feature.shape[0] == GenericEgoFeatureIndex.dim():
        return
    raise ValueError(f'Improper ego feature shape: {feature.shape}.')

def _validate_generic_agent_feature_shape(feature: torch.Tensor) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be a GenericAgentFeature.
    :param feature: The tensor to validate.
    """
    if len(feature.shape) != 3 or feature.shape[2] != GenericAgentFeatureIndex.dim():
        raise ValueError(f'Improper agent feature shape: {feature.shape}.')

def _validate_ego_internal_shape(feature: torch.Tensor, expected_first_dim: Optional[int]=None) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be an EgoInternal.
    :param feature: The tensor to validate.
    :param expected_first_dim: If None, accept either [N, EgoInternalIndex.dim()] or [EgoInternalIndex.dim()]
                                If 1, only accept [EgoInternalIndex.dim()]
                                If 2, only accept [N, EgoInternalIndex.dim()]
    """
    if len(feature.shape) == 2 and feature.shape[1] == EgoInternalIndex.dim():
        if expected_first_dim is None or expected_first_dim == 2:
            return
    if len(feature.shape) == 1 and feature.shape[0] == EgoInternalIndex.dim():
        if expected_first_dim is None or expected_first_dim == 1:
            return
    raise ValueError(f'Improper ego internal shape: {feature.shape}')

def _validate_agent_internal_shape(feature: torch.Tensor) -> None:
    """
    Validates the shape of the provided tensor if it's expected to be an AgentInternal.
    :param feature: the tensor to validate.
    """
    if len(feature.shape) != 2 or feature.shape[1] != AgentInternalIndex.dim():
        raise ValueError(f'Improper agent internal shape: {feature.shape}')

def build_ego_features(ego_trajectory: List[EgoState], reverse: bool=False) -> FeatureDataType:
    """
    Build agent features from the ego and agents trajectory
    :param ego_trajectory: ego trajectory comprising of EgoState [num_frames]
    :param reverse: if True, the last element in the list will be considered as the present ego state
    :return: ego_features: <np.ndarray: num_frames, 3>
                         The num_frames includes both present and past/future frames.
                         The last dimension is the ego pose (x, y, heading) at time t.
    """
    if reverse:
        anchor_ego_state = ego_trajectory[-1]
    else:
        anchor_ego_state = ego_trajectory[0]
    ego_poses = [ego_state.rear_axle for ego_state in ego_trajectory]
    ego_relative_poses = convert_absolute_to_relative_poses(anchor_ego_state.rear_axle, ego_poses)
    return ego_relative_poses

def build_ego_center_features(ego_trajectory: List[EgoState], reverse: bool=False) -> FeatureDataType:
    """
    Build agent features from the ego and agents trajectory, using center of ego OrientedBox as reference points.
    :param ego_trajectory: ego trajectory comprising of EgoState [num_frames]
    :param reverse: if True, the last element in the list will be considered as the present ego state
    :return: ego_features
             ego_features: <np.ndarray: num_frames, 3>
                         The num_frames includes both present and past/future frames.
                         The last dimension is the ego pose (x, y, heading) at time t.
    """
    if reverse:
        anchor_ego_state = ego_trajectory[-1]
    else:
        anchor_ego_state = ego_trajectory[0]
    ego_poses = [ego_state.center for ego_state in ego_trajectory]
    ego_relative_poses = convert_absolute_to_relative_poses(anchor_ego_state.center, ego_poses)
    return ego_relative_poses

def convert_absolute_quantities_to_relative(agent_states: List[torch.Tensor], ego_state: torch.Tensor) -> List[torch.Tensor]:
    """
    Converts the agents' poses and relative velocities from absolute to ego-relative coordinates.
    :param agent_states: The agent states to convert, in the AgentInternalIndex schema.
    :param ego_state: The ego state to convert, in the EgoInternalIndex schema.
    :return: The converted states, in AgentInternalIndex schema.
    """
    _validate_ego_internal_shape(ego_state, expected_first_dim=1)
    ego_pose = torch.tensor([float(ego_state[EgoInternalIndex.x()].item()), float(ego_state[EgoInternalIndex.y()].item()), float(ego_state[EgoInternalIndex.heading()].item())], dtype=torch.float64)
    ego_velocity = torch.tensor([float(ego_state[EgoInternalIndex.vx()].item()), float(ego_state[EgoInternalIndex.vy()].item()), float(ego_state[EgoInternalIndex.heading()].item())], dtype=torch.float64)
    for agent_state in agent_states:
        _validate_agent_internal_shape(agent_state)
        agent_global_poses = agent_state[:, [AgentInternalIndex.x(), AgentInternalIndex.y(), AgentInternalIndex.heading()]].double()
        agent_global_velocities = agent_state[:, [AgentInternalIndex.vx(), AgentInternalIndex.vy(), AgentInternalIndex.heading()]].double()
        transformed_poses = global_state_se2_tensor_to_local(agent_global_poses, ego_pose, precision=torch.float64)
        transformed_velocities = global_state_se2_tensor_to_local(agent_global_velocities, ego_velocity, precision=torch.float64)
        agent_state[:, AgentInternalIndex.x()] = transformed_poses[:, 0].float()
        agent_state[:, AgentInternalIndex.y()] = transformed_poses[:, 1].float()
        agent_state[:, AgentInternalIndex.heading()] = transformed_poses[:, 2].float()
        agent_state[:, AgentInternalIndex.vx()] = transformed_velocities[:, 0].float()
        agent_state[:, AgentInternalIndex.vy()] = transformed_velocities[:, 1].float()
    return agent_states

def pad_agent_states(agent_trajectories: List[torch.Tensor], reverse: bool) -> List[torch.Tensor]:
    """
    Pads the agent states with the most recent available states. The order of the agents is also
    preserved. Note: only agents that appear in the current time step will be computed for. Agents appearing in the
    future or past will be discarded.

     t1      t2           t1      t2
    |a1,t1| |a1,t2|  pad |a1,t1| |a1,t2|
    |a2,t1| |a3,t2|  ->  |a2,t1| |a2,t1| (padded with agent 2 state at t1)
    |a3,t1| |     |      |a3,t1| |a3,t2|


    If reverse is True, the padding direction will start from the end of the trajectory towards the start

     tN-1    tN             tN-1    tN
    |a1,tN-1| |a1,tN|  pad |a1,tN-1| |a1,tN|
    |a2,tN  | |a2,tN|  <-  |a3,tN-1| |a2,tN| (padded with agent 2 state at tN)
    |a3,tN-1| |a3,tN|      |       | |a3,tN|

    :param agent_trajectories: agent trajectories [num_frames, num_agents, AgentInternalIndex.dim()], corresponding to the AgentInternalIndex schema.
    :param reverse: if True, the padding direction will start from the end of the list instead
    :return: A trajectory of extracted states
    """
    for traj in agent_trajectories:
        _validate_agent_internal_shape(traj)
    track_id_idx = AgentInternalIndex.track_token()
    if reverse:
        agent_trajectories = agent_trajectories[::-1]
    key_frame = agent_trajectories[0]
    id_row_mapping: Dict[int, int] = {}
    for idx, val in enumerate(key_frame[:, track_id_idx]):
        id_row_mapping[int(val.item())] = idx
    current_state = torch.zeros((key_frame.shape[0], key_frame.shape[1]), dtype=torch.float32)
    for idx in range(len(agent_trajectories)):
        frame = agent_trajectories[idx]
        for row_idx in range(frame.shape[0]):
            mapped_row: int = id_row_mapping[int(frame[row_idx, track_id_idx].item())]
            current_state[mapped_row, :] = frame[row_idx, :]
        agent_trajectories[idx] = torch.clone(current_state)
    if reverse:
        agent_trajectories = agent_trajectories[::-1]
    return agent_trajectories

def build_ego_features_from_tensor(ego_trajectory: torch.Tensor, reverse: bool=False) -> torch.Tensor:
    """
    Build agent features from the ego states
    :param ego_trajectory: ego states at past times. Tensors complying with the EgoInternalIndex schema.
    :param reverse: if True, the last element in the list will be considered as the present ego state
    :return: Tensor complying with the EgoFeatureIndex schema.
    """
    _validate_ego_internal_shape(ego_trajectory, expected_first_dim=2)
    if reverse:
        anchor_ego_state = ego_trajectory[ego_trajectory.shape[0] - 1, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].squeeze().double()
    else:
        anchor_ego_state = ego_trajectory[0, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].squeeze().double()
    global_ego_trajectory = ego_trajectory[:, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].double()
    local_ego_trajectory = global_state_se2_tensor_to_local(global_ego_trajectory, anchor_ego_state, precision=torch.float64)
    return local_ego_trajectory.float()

def build_generic_ego_features_from_tensor(ego_trajectory: torch.Tensor, reverse: bool=False) -> torch.Tensor:
    """
    Build generic agent features from the ego states
    :param ego_trajectory: ego states at past times. Tensors complying with the EgoInternalIndex schema.
    :param reverse: if True, the last element in the list will be considered as the present ego state
    :return: Tensor complying with the GenericEgoFeatureIndex schema.
    """
    _validate_ego_internal_shape(ego_trajectory, expected_first_dim=2)
    if reverse:
        anchor_ego_pose = ego_trajectory[ego_trajectory.shape[0] - 1, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].squeeze().double()
        anchor_ego_velocity = ego_trajectory[ego_trajectory.shape[0] - 1, [EgoInternalIndex.vx(), EgoInternalIndex.vy(), EgoInternalIndex.heading()]].squeeze().double()
        anchor_ego_acceleration = ego_trajectory[ego_trajectory.shape[0] - 1, [EgoInternalIndex.ax(), EgoInternalIndex.ay(), EgoInternalIndex.heading()]].squeeze().double()
    else:
        anchor_ego_pose = ego_trajectory[0, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].squeeze().double()
        anchor_ego_velocity = ego_trajectory[0, [EgoInternalIndex.vx(), EgoInternalIndex.vy(), EgoInternalIndex.heading()]].squeeze().double()
        anchor_ego_acceleration = ego_trajectory[0, [EgoInternalIndex.ax(), EgoInternalIndex.ay(), EgoInternalIndex.heading()]].squeeze().double()
    global_ego_poses = ego_trajectory[:, [EgoInternalIndex.x(), EgoInternalIndex.y(), EgoInternalIndex.heading()]].double()
    global_ego_velocities = ego_trajectory[:, [EgoInternalIndex.vx(), EgoInternalIndex.vy(), EgoInternalIndex.heading()]].double()
    global_ego_accelerations = ego_trajectory[:, [EgoInternalIndex.ax(), EgoInternalIndex.ay(), EgoInternalIndex.heading()]].double()
    local_ego_poses = global_state_se2_tensor_to_local(global_ego_poses, anchor_ego_pose, precision=torch.float64)
    local_ego_velocities = global_state_se2_tensor_to_local(global_ego_velocities, anchor_ego_velocity, precision=torch.float64)
    local_ego_accelerations = global_state_se2_tensor_to_local(global_ego_accelerations, anchor_ego_acceleration, precision=torch.float64)
    local_ego_trajectory: torch.Tensor = torch.empty(ego_trajectory.size(), dtype=torch.float32, device=ego_trajectory.device)
    local_ego_trajectory[:, EgoInternalIndex.x()] = local_ego_poses[:, 0].float()
    local_ego_trajectory[:, EgoInternalIndex.y()] = local_ego_poses[:, 1].float()
    local_ego_trajectory[:, EgoInternalIndex.heading()] = local_ego_poses[:, 2].float()
    local_ego_trajectory[:, EgoInternalIndex.vx()] = local_ego_velocities[:, 0].float()
    local_ego_trajectory[:, EgoInternalIndex.vy()] = local_ego_velocities[:, 1].float()
    local_ego_trajectory[:, EgoInternalIndex.ax()] = local_ego_accelerations[:, 0].float()
    local_ego_trajectory[:, EgoInternalIndex.ay()] = local_ego_accelerations[:, 1].float()
    return local_ego_trajectory

def filter_agents_tensor(agents: List[torch.Tensor], reverse: bool=False) -> List[torch.Tensor]:
    """
    Filter detections to keep only agents which appear in the first frame (or last frame if reverse=True)
    :param agents: The past agents in the scene. A list of [num_frames] tensors, each complying with the AgentInternalIndex schema
    :param reverse: if True, the last element in the list will be used as the filter
    :return: filtered agents in the same format as the input `agents` parameter
    """
    target_tensor = agents[-1] if reverse else agents[0]
    for i in range(len(agents)):
        _validate_agent_internal_shape(agents[i])
        rows: List[torch.Tensor] = []
        for j in range(agents[i].shape[0]):
            if target_tensor.shape[0] > 0:
                agent_id: float = float(agents[i][j, int(AgentInternalIndex.track_token())].item())
                is_in_target_frame: bool = bool((agent_id == target_tensor[:, AgentInternalIndex.track_token()]).max().item())
                if is_in_target_frame:
                    rows.append(agents[i][j, :].squeeze())
        if len(rows) > 0:
            agents[i] = torch.stack(rows)
        else:
            agents[i] = torch.empty((0, agents[i].shape[1]), dtype=torch.float32)
    return agents

def compute_yaw_rate_from_state_tensors(agent_states: List[torch.Tensor], time_stamps: torch.Tensor) -> torch.Tensor:
    """
    Computes the yaw rate of all agents over the trajectory from heading
    :param agent_states_horizon: Agent trajectories [num_frames, num_agent, AgentsInternalBuffer.dim()]
    :param time_stamps: The time stamps of each frame.
    :return: <torch.Tensor: num_frames, num_agents> of yaw rates
    """
    if len(time_stamps.shape) != 1:
        raise ValueError(f'Unexpected timestamps shape: {time_stamps.shape}')
    time_stamps_s = (time_stamps - int(torch.min(time_stamps).item())).double() * 1e-06
    yaws: List[torch.Tensor] = []
    for agent_state in agent_states:
        _validate_agent_internal_shape(agent_state)
        yaws.append(agent_state[:, AgentInternalIndex.heading()].squeeze().double())
    yaws_tensor = torch.vstack(yaws)
    yaws_tensor = yaws_tensor.transpose(0, 1)
    yaws_tensor = unwrap(yaws_tensor, dim=-1)
    yaw_rate_horizon = approximate_derivatives_tensor(yaws_tensor, time_stamps_s, window_length=3)
    return yaw_rate_horizon.transpose(0, 1)

def sampled_past_ego_states_to_tensor(past_ego_states: List[EgoState]) -> torch.Tensor:
    """
    Converts a list of N ego states into a N x 7 tensor. The 7 fields are as defined in `EgoInternalIndex`
    :param past_ego_states: The ego states to convert.
    :return: The converted tensor.
    """
    output = torch.zeros((len(past_ego_states), EgoInternalIndex.dim()), dtype=torch.float32)
    for i in range(0, len(past_ego_states), 1):
        output[i, EgoInternalIndex.x()] = past_ego_states[i].rear_axle.x
        output[i, EgoInternalIndex.y()] = past_ego_states[i].rear_axle.y
        output[i, EgoInternalIndex.heading()] = past_ego_states[i].rear_axle.heading
        output[i, EgoInternalIndex.vx()] = past_ego_states[i].dynamic_car_state.rear_axle_velocity_2d.x
        output[i, EgoInternalIndex.vy()] = past_ego_states[i].dynamic_car_state.rear_axle_velocity_2d.y
        output[i, EgoInternalIndex.ax()] = past_ego_states[i].dynamic_car_state.rear_axle_acceleration_2d.x
        output[i, EgoInternalIndex.ay()] = past_ego_states[i].dynamic_car_state.rear_axle_acceleration_2d.y
    return output

def sampled_past_timestamps_to_tensor(past_time_stamps: List[TimePoint]) -> torch.Tensor:
    """
    Converts a list of N past timestamps into a 1-d tensor of shape [N]. The field is the timestamp in uS.
    :param past_time_stamps: The time stamps to convert.
    :return: The converted tensor.
    """
    flat = [t.time_us for t in past_time_stamps]
    return torch.tensor(flat, dtype=torch.int64)

def _extract_agent_tensor(tracked_objects: TrackedObjects, track_token_ids: Dict[str, int], object_type: TrackedObjectType) -> Tuple[torch.Tensor, Dict[str, int]]:
    """
    Extracts the relevant data from the agents present in a past detection into a tensor.
    Only objects of specified type will be transformed. Others will be ignored.
    The output is a tensor as described in AgentInternalIndex
    :param tracked_objects: The tracked objects to turn into a tensor.
    :track_token_ids: A dictionary used to assign track tokens to integer IDs.
    :object_type: TrackedObjectType to filter agents by.
    :return: The generated tensor and the updated track_token_ids dict.
    """
    agents = tracked_objects.get_tracked_objects_of_type(object_type)
    output = torch.zeros((len(agents), AgentInternalIndex.dim()), dtype=torch.float32)
    max_agent_id = len(track_token_ids)
    for idx, agent in enumerate(agents):
        if agent.track_token not in track_token_ids:
            track_token_ids[agent.track_token] = max_agent_id
            max_agent_id += 1
        track_token_int = track_token_ids[agent.track_token]
        output[idx, AgentInternalIndex.track_token()] = float(track_token_int)
        output[idx, AgentInternalIndex.vx()] = agent.velocity.x
        output[idx, AgentInternalIndex.vy()] = agent.velocity.y
        output[idx, AgentInternalIndex.heading()] = agent.center.heading
        output[idx, AgentInternalIndex.width()] = agent.box.width
        output[idx, AgentInternalIndex.length()] = agent.box.length
        output[idx, AgentInternalIndex.x()] = agent.center.x
        output[idx, AgentInternalIndex.y()] = agent.center.y
    return (output, track_token_ids)

def pack_agents_tensor(padded_agents_tensors: List[torch.Tensor], yaw_rates: torch.Tensor) -> torch.Tensor:
    """
    Combines the local padded agents states and the computed yaw rates into the final output feature tensor.
    :param padded_agents_tensors: The padded agent states for each timestamp.
        Each tensor is of shape <num_agents, len(AgentInternalIndex)> and conforms to the AgentInternalIndex schema.
    :param yaw_rates: The computed yaw rates. The tensor is of shape <num_timestamps, agent>
    :return: The final feature, a tensor of shape [timestamp, num_agents, len(AgentsFeatureIndex)] conforming to the AgentFeatureIndex Schema
    """
    if yaw_rates.shape != (len(padded_agents_tensors), padded_agents_tensors[0].shape[0]):
        raise ValueError(f'Unexpected yaw_rates tensor shape: {yaw_rates.shape}')
    agents_tensor = torch.zeros((len(padded_agents_tensors), padded_agents_tensors[0].shape[0], AgentFeatureIndex.dim()))
    for i in range(len(padded_agents_tensors)):
        _validate_agent_internal_shape(padded_agents_tensors[i])
        agents_tensor[i, :, AgentFeatureIndex.x()] = padded_agents_tensors[i][:, AgentInternalIndex.x()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.y()] = padded_agents_tensors[i][:, AgentInternalIndex.y()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.heading()] = padded_agents_tensors[i][:, AgentInternalIndex.heading()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.vx()] = padded_agents_tensors[i][:, AgentInternalIndex.vx()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.vy()] = padded_agents_tensors[i][:, AgentInternalIndex.vy()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.yaw_rate()] = yaw_rates[i, :].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.width()] = padded_agents_tensors[i][:, AgentInternalIndex.width()].squeeze()
        agents_tensor[i, :, AgentFeatureIndex.length()] = padded_agents_tensors[i][:, AgentInternalIndex.length()].squeeze()
    return agents_tensor

def interpolate_points(coords: torch.Tensor, max_points: int, interpolation: str) -> torch.Tensor:
    """
    Interpolate points within map element to maintain fixed size.
    :param coords: Sequence of coordinate points representing map element. <torch.Tensor: num_points, 2>
    :param max_points: Desired size to interpolate to.
    :param interpolation: Torch interpolation mode. Available options: 'linear' and 'area'.
    :return: Coordinate points interpolated to max_points size.
    :raise ValueError: If coordinates dimensions are not valid.
    """
    if len(coords.shape) != 2 or coords.shape[1] != 2:
        raise ValueError(f'Unexpected coords shape: {coords.shape}. Expected shape: (*, 2)')
    x_coords = coords[:, 0].unsqueeze(0).unsqueeze(0)
    y_coords = coords[:, 1].unsqueeze(0).unsqueeze(0)
    align_corners = True if interpolation == 'linear' else None
    x_coords = torch.nn.functional.interpolate(x_coords, max_points, mode=interpolation, align_corners=align_corners)
    y_coords = torch.nn.functional.interpolate(y_coords, max_points, mode=interpolation, align_corners=align_corners)
    coords = torch.stack((x_coords, y_coords), dim=-1).squeeze()
    return coords

def convert_feature_layer_to_fixed_size(feature_coords: List[torch.Tensor], feature_tl_data_over_time: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
    """
    Converts variable sized map features to fixed size tensors. Map elements are padded/trimmed to max_elements size.
        Points per feature are interpolated to maintain max_points size.
    :param feature_coords: Vector set of coordinates for collection of elements in map layer.
        [num_elements, num_points_in_element (variable size), 2]
    :param feature_tl_data_over_time: Optional traffic light status corresponding to map elements at given index in coords.
        [num_frames, num_elements, traffic_light_encoding_dim (4)]
    :param max_elements: Number of elements to pad/trim to.
    :param max_points: Number of points to interpolate or pad/trim to.
    :param traffic_light_encoding_dim: Dimensionality of traffic light data.
    :param interpolation: Optional interpolation mode for maintaining fixed number of points per element.
        None indicates trimming and zero-padding to take place in lieu of interpolation. Interpolation options:
        'linear' and 'area'.
    :return
        coords_tensor: The converted coords tensor.
        tl_data_tensor: The converted traffic light data tensor (if available).
        avails_tensor: Availabilities tensor identifying real vs zero-padded data in coords_tensor and tl_data_tensor.
    :raise ValueError: If coordinates and traffic light data size do not match.
    """
    coords_tensor = torch.zeros((max_elements, max_points, 2), dtype=torch.float64)
    avails_tensor = torch.zeros((max_elements, max_points), dtype=torch.bool)
    tl_data_tensor = torch.zeros((len(feature_tl_data_over_time), max_elements, max_points, traffic_light_encoding_dim), dtype=torch.float32) if feature_tl_data_over_time is not None else None
    for element_idx in range(min(len(feature_coords), max_elements)):
        element_coords = feature_coords[element_idx]
        if interpolation is not None:
            num_points = max_points
            element_coords = interpolate_points(element_coords, max_points, interpolation=interpolation)
        else:
            num_points = min(len(element_coords), max_points)
            element_coords = element_coords[:num_points]
        coords_tensor[element_idx, :num_points] = element_coords
        avails_tensor[element_idx, :num_points] = True
        if feature_tl_data_over_time is not None and tl_data_tensor is not None:
            for time_ind in range(len(feature_tl_data_over_time)):
                if len(feature_coords) != len(feature_tl_data_over_time[time_ind]):
                    raise ValueError(f'num_elements between feature_coords and feature_tl_data_over_time inconsistent: {len(feature_coords)}, {len(feature_tl_data_over_time[time_ind])}')
                tl_data_tensor[time_ind, element_idx, :num_points] = feature_tl_data_over_time[time_ind][element_idx]
    return (coords_tensor, tl_data_tensor, avails_tensor)

def _create_ego_trajectory_tensor(num_frames: int) -> torch.Tensor:
    """
    Generate a dummy ego trajectory
    :param num_frames: length of the trajectory to be generate
    :return: The generated trajectory
    """
    output = torch.ones((num_frames, EgoInternalIndex.dim()))
    for i in range(num_frames):
        output[i, :] *= i
    return output

def _create_tracked_object_agent_tensor(num_agents: int) -> torch.Tensor:
    """
    Generates a dummy tracked object input tensor.
    :param num_agents: The number of agents in the tensor.
    :return: The generated tensor.
    """
    output = torch.ones((num_agents, AgentInternalIndex.dim()))
    for i in range(num_agents):
        output[i, :] *= i
    return output

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

def get_dummy_states() -> List[torch.Tensor]:
    """
            Create a series of dummy agent tensors
            """
    dummy_agent_state = _create_tracked_object_agent_tensor(7)
    dummy_states = [dummy_agent_state + i for i in range(5)]
    return dummy_states

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

class TestVectorPreprocessing(unittest.TestCase):
    """Test preprocessing utility functions to assist with builders for vectorized map features."""

    def setUp(self) -> None:
        """Set up test case."""
        self.max_elements = 30
        self.max_points = 20
        self.interpolation = None
        self.traffic_light_encoding_dim = LaneSegmentTrafficLightData.encoding_dim()

    def test_interpolate_points_functionality(self) -> None:
        """
        Test interpolating coordinate points.
        """
        coords = torch.tensor([[1, 1], [3, 1], [5, 1]], dtype=torch.float64)
        interpolated_coords = interpolate_points(coords, 5, interpolation='linear')
        self.assertEqual(interpolated_coords.shape, (5, 2))
        torch.testing.assert_allclose(coords, interpolated_coords[::2])
        torch.testing.assert_allclose(interpolated_coords[:, 1], torch.ones(5, dtype=torch.float64))
        self.assertTrue(interpolated_coords[1][0].item() > interpolated_coords[0][0].item())
        self.assertTrue(interpolated_coords[1][0].item() < interpolated_coords[2][0].item())
        self.assertTrue(interpolated_coords[3][0].item() > interpolated_coords[2][0].item())
        self.assertTrue(interpolated_coords[3][0].item() < interpolated_coords[4][0].item())
        interpolated_coords = interpolate_points(coords, 5, interpolation='area')
        self.assertEqual(interpolated_coords.shape, (5, 2))
        torch.testing.assert_allclose(coords, interpolated_coords[::2])
        torch.testing.assert_allclose(interpolated_coords[:, 1], torch.ones(5, dtype=torch.float64))
        self.assertTrue(interpolated_coords[1][0].item() > interpolated_coords[0][0].item())
        self.assertTrue(interpolated_coords[1][0].item() < interpolated_coords[2][0].item())
        self.assertTrue(interpolated_coords[3][0].item() > interpolated_coords[2][0].item())
        self.assertTrue(interpolated_coords[3][0].item() < interpolated_coords[4][0].item())

    def test_interpolate_points_scriptability(self) -> None:
        """
        Tests that the function interpolate_points scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, coords: torch.Tensor, max_points: int, interpolation: str) -> torch.Tensor:
                result = interpolate_points(coords, max_points, interpolation)
                return result
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_coords = torch.tensor([[1, 1], [3, 1], [5, 1]], dtype=torch.float64)
        py_result = to_script.forward(test_coords, 5, 'linear')
        script_result = scripted.forward(test_coords, 5, 'linear')
        torch.testing.assert_allclose(py_result, script_result)

    def test_convert_feature_layer_to_fixed_size_functionality(self) -> None:
        """
        Test converting variable size data to fixed size tensors.
        """
        coords: List[torch.Tensor] = [torch.tensor([[0.0, 0.0]])]
        traffic_light_data: List[torch.Tensor] = [[torch.tensor([LaneSegmentTrafficLightData.encode(TrafficLightStatusType.UNKNOWN)])]]
        coords_tensor, tl_data_tensor, avails_tensor = convert_feature_layer_to_fixed_size(coords, traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
        self.assertIsInstance(coords_tensor, torch.DoubleTensor)
        self.assertIsInstance(tl_data_tensor, torch.FloatTensor)
        self.assertIsInstance(avails_tensor, torch.BoolTensor)
        self.assertEqual(coords_tensor.shape, (self.max_elements, self.max_points, 2))
        self.assertEqual(tl_data_tensor[0].shape, (self.max_elements, self.max_points, LaneSegmentTrafficLightData.encoding_dim()))
        self.assertEqual(avails_tensor.shape, (self.max_elements, self.max_points))
        expected_avails = torch.zeros(avails_tensor.shape, dtype=torch.bool)
        expected_avails[0][0] = True
        torch.testing.assert_equal(expected_avails, avails_tensor)
        coords_tensor, tl_data_tensor, avails_tensor = convert_feature_layer_to_fixed_size(coords, traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, interpolation='linear')
        expected_avails = torch.zeros(avails_tensor.shape, dtype=torch.bool)
        expected_avails[0][:] = True
        torch.testing.assert_equal(expected_avails, avails_tensor)

    def test_convert_feature_layer_to_fixed_size_scriptability(self) -> None:
        """
        Tests that the function convert_feature_layer_to_fixed_size scripts properly.
        """

        class tmp_module(torch.nn.Module):

            def __init__(self) -> None:
                super().__init__()

            def forward(self, coords: List[torch.Tensor], traffic_light_data: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
                result_coords, result_tl_data, result_avails = convert_feature_layer_to_fixed_size(coords, traffic_light_data, max_elements, max_points, traffic_light_encoding_dim, interpolation)
                return (result_coords, result_tl_data, result_avails)
        to_script = tmp_module()
        scripted = torch.jit.script(to_script)
        test_coords: List[torch.Tensor] = [torch.tensor([[0.0, 0.0]])]
        test_traffic_light_data: List[torch.Tensor] = [[torch.tensor([LaneSegmentTrafficLightData.encode(TrafficLightStatusType.UNKNOWN)])]]
        py_result_coords, py_script_result_tl_data, py_script_result_avails = to_script.forward(test_coords, test_traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
        script_result_coords, script_result_tl_data, script_result_avails = scripted.forward(test_coords, test_traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
        torch.testing.assert_allclose(py_result_coords, script_result_coords)
        torch.testing.assert_allclose(py_script_result_tl_data, script_result_tl_data)
        torch.testing.assert_allclose(py_script_result_avails, script_result_avails)

def test_interpolate_points_functionality(self) -> None:
    """
        Test interpolating coordinate points.
        """
    coords = torch.tensor([[1, 1], [3, 1], [5, 1]], dtype=torch.float64)
    interpolated_coords = interpolate_points(coords, 5, interpolation='linear')
    self.assertEqual(interpolated_coords.shape, (5, 2))
    torch.testing.assert_allclose(coords, interpolated_coords[::2])
    torch.testing.assert_allclose(interpolated_coords[:, 1], torch.ones(5, dtype=torch.float64))
    self.assertTrue(interpolated_coords[1][0].item() > interpolated_coords[0][0].item())
    self.assertTrue(interpolated_coords[1][0].item() < interpolated_coords[2][0].item())
    self.assertTrue(interpolated_coords[3][0].item() > interpolated_coords[2][0].item())
    self.assertTrue(interpolated_coords[3][0].item() < interpolated_coords[4][0].item())
    interpolated_coords = interpolate_points(coords, 5, interpolation='area')
    self.assertEqual(interpolated_coords.shape, (5, 2))
    torch.testing.assert_allclose(coords, interpolated_coords[::2])
    torch.testing.assert_allclose(interpolated_coords[:, 1], torch.ones(5, dtype=torch.float64))
    self.assertTrue(interpolated_coords[1][0].item() > interpolated_coords[0][0].item())
    self.assertTrue(interpolated_coords[1][0].item() < interpolated_coords[2][0].item())
    self.assertTrue(interpolated_coords[3][0].item() > interpolated_coords[2][0].item())
    self.assertTrue(interpolated_coords[3][0].item() < interpolated_coords[4][0].item())

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, coords: List[torch.Tensor], traffic_light_data: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
        result_coords, result_tl_data, result_avails = convert_feature_layer_to_fixed_size(coords, traffic_light_data, max_elements, max_points, traffic_light_encoding_dim, interpolation)
        return (result_coords, result_tl_data, result_avails)

def forward(self, coords: List[torch.Tensor], traffic_light_data: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
    result_coords, result_tl_data, result_avails = convert_feature_layer_to_fixed_size(coords, traffic_light_data, max_elements, max_points, traffic_light_encoding_dim, interpolation)
    return (result_coords, result_tl_data, result_avails)

def test_interpolate_points_scriptability(self) -> None:
    """
        Tests that the function interpolate_points scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, coords: torch.Tensor, max_points: int, interpolation: str) -> torch.Tensor:
            result = interpolate_points(coords, max_points, interpolation)
            return result
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_coords = torch.tensor([[1, 1], [3, 1], [5, 1]], dtype=torch.float64)
    py_result = to_script.forward(test_coords, 5, 'linear')
    script_result = scripted.forward(test_coords, 5, 'linear')
    torch.testing.assert_allclose(py_result, script_result)

def test_convert_feature_layer_to_fixed_size_functionality(self) -> None:
    """
        Test converting variable size data to fixed size tensors.
        """
    coords: List[torch.Tensor] = [torch.tensor([[0.0, 0.0]])]
    traffic_light_data: List[torch.Tensor] = [[torch.tensor([LaneSegmentTrafficLightData.encode(TrafficLightStatusType.UNKNOWN)])]]
    coords_tensor, tl_data_tensor, avails_tensor = convert_feature_layer_to_fixed_size(coords, traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
    self.assertIsInstance(coords_tensor, torch.DoubleTensor)
    self.assertIsInstance(tl_data_tensor, torch.FloatTensor)
    self.assertIsInstance(avails_tensor, torch.BoolTensor)
    self.assertEqual(coords_tensor.shape, (self.max_elements, self.max_points, 2))
    self.assertEqual(tl_data_tensor[0].shape, (self.max_elements, self.max_points, LaneSegmentTrafficLightData.encoding_dim()))
    self.assertEqual(avails_tensor.shape, (self.max_elements, self.max_points))
    expected_avails = torch.zeros(avails_tensor.shape, dtype=torch.bool)
    expected_avails[0][0] = True
    torch.testing.assert_equal(expected_avails, avails_tensor)
    coords_tensor, tl_data_tensor, avails_tensor = convert_feature_layer_to_fixed_size(coords, traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, interpolation='linear')
    expected_avails = torch.zeros(avails_tensor.shape, dtype=torch.bool)
    expected_avails[0][:] = True
    torch.testing.assert_equal(expected_avails, avails_tensor)

def test_convert_feature_layer_to_fixed_size_scriptability(self) -> None:
    """
        Tests that the function convert_feature_layer_to_fixed_size scripts properly.
        """

    class tmp_module(torch.nn.Module):

        def __init__(self) -> None:
            super().__init__()

        def forward(self, coords: List[torch.Tensor], traffic_light_data: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
            result_coords, result_tl_data, result_avails = convert_feature_layer_to_fixed_size(coords, traffic_light_data, max_elements, max_points, traffic_light_encoding_dim, interpolation)
            return (result_coords, result_tl_data, result_avails)
    to_script = tmp_module()
    scripted = torch.jit.script(to_script)
    test_coords: List[torch.Tensor] = [torch.tensor([[0.0, 0.0]])]
    test_traffic_light_data: List[torch.Tensor] = [[torch.tensor([LaneSegmentTrafficLightData.encode(TrafficLightStatusType.UNKNOWN)])]]
    py_result_coords, py_script_result_tl_data, py_script_result_avails = to_script.forward(test_coords, test_traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
    script_result_coords, script_result_tl_data, script_result_avails = scripted.forward(test_coords, test_traffic_light_data, self.max_elements, self.max_points, self.traffic_light_encoding_dim, self.interpolation)
    torch.testing.assert_allclose(py_result_coords, script_result_coords)
    torch.testing.assert_allclose(py_script_result_tl_data, script_result_tl_data)
    torch.testing.assert_allclose(py_script_result_avails, script_result_avails)

class TestCollate(unittest.TestCase):
    """Test feature collation functionality."""

    def test_list_as_batch(self) -> None:
        """
        Test collating lists
        """
        single_feature1: FeaturesType = {'VectorMap': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
        single_targets1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3)))}
        singe_scenario: ScenarioListType = [CachedScenario(log_name='', token='', scenario_type='')]
        to_be_batched = [(single_feature1, single_targets1, singe_scenario), (single_feature1, single_targets1, singe_scenario)]
        collate = FeatureCollate()
        features, targets, scenarios = collate(to_be_batched)
        vector_map: DummyVectorMapFeature = features['VectorMap']
        self.assertEqual(vector_map.num_of_batches, 2)
        self.assertEqual(len(vector_map.data1), 2)
        self.assertEqual(vector_map.data1[0].shape, (13, 3))
        trajectory: Trajectory = targets['Trajectory']
        self.assertEqual(trajectory.data.shape, (2, 12, 3))
        self.assertEqual(len(scenarios), 2)

    def test_collate(self) -> None:
        """
        Test collating features
        """
        single_feature1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
        single_targets1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
        single_feature2: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
        single_targets2: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
        single_feature3: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
        single_targets3: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
        singe_scenario: ScenarioListType = [CachedScenario(log_name='', token='', scenario_type='')]
        to_be_batched = [(single_feature1, single_targets1, singe_scenario), (single_feature2, single_targets2, singe_scenario), (single_feature3, single_targets3, singe_scenario)]
        collate = FeatureCollate()
        features, targets, scenarios = collate(to_be_batched)
        self.assertEqual(features['Trajectory'].data.shape, (3, 12, 3))
        self.assertEqual(features['Raster'].data.shape, (3, 244, 244, 3))
        self.assertEqual(features['DummyVectorMapFeature'].num_of_batches, 3)
        self.assertEqual(targets['Trajectory'].data.shape, (3, 12, 3))
        self.assertEqual(len(scenarios), 3)

def test_list_as_batch(self) -> None:
    """
        Test collating lists
        """
    single_feature1: FeaturesType = {'VectorMap': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
    single_targets1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3)))}
    singe_scenario: ScenarioListType = [CachedScenario(log_name='', token='', scenario_type='')]
    to_be_batched = [(single_feature1, single_targets1, singe_scenario), (single_feature1, single_targets1, singe_scenario)]
    collate = FeatureCollate()
    features, targets, scenarios = collate(to_be_batched)
    vector_map: DummyVectorMapFeature = features['VectorMap']
    self.assertEqual(vector_map.num_of_batches, 2)
    self.assertEqual(len(vector_map.data1), 2)
    self.assertEqual(vector_map.data1[0].shape, (13, 3))
    trajectory: Trajectory = targets['Trajectory']
    self.assertEqual(trajectory.data.shape, (2, 12, 3))
    self.assertEqual(len(scenarios), 2)

def test_collate(self) -> None:
    """
        Test collating features
        """
    single_feature1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
    single_targets1: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
    single_feature2: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
    single_targets2: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
    single_feature3: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Raster': Raster(data=torch.zeros((244, 244, 3))), 'DummyVectorMapFeature': DummyVectorMapFeature(data1=[torch.zeros((13, 3))], data2=[torch.zeros((13, 3))], data3=[{'test': torch.zeros((13, 3))}])}
    single_targets3: FeaturesType = {'Trajectory': Trajectory(data=torch.zeros((12, 3))), 'Trajectory2': Trajectory(data=torch.zeros((12, 3)))}
    singe_scenario: ScenarioListType = [CachedScenario(log_name='', token='', scenario_type='')]
    to_be_batched = [(single_feature1, single_targets1, singe_scenario), (single_feature2, single_targets2, singe_scenario), (single_feature3, single_targets3, singe_scenario)]
    collate = FeatureCollate()
    features, targets, scenarios = collate(to_be_batched)
    self.assertEqual(features['Trajectory'].data.shape, (3, 12, 3))
    self.assertEqual(features['Raster'].data.shape, (3, 244, 244, 3))
    self.assertEqual(features['DummyVectorMapFeature'].num_of_batches, 3)
    self.assertEqual(targets['Trajectory'].data.shape, (3, 12, 3))
    self.assertEqual(len(scenarios), 3)

@dataclass
class DummyVectorMapFeature(AbstractModelFeature):
    """Dummy vector map feature used in testing."""
    data1: List[FeatureDataType]
    data2: List[FeatureDataType]
    data3: List[Dict[str, FeatureDataType]]

    def __post_init__(self) -> None:
        """Sanitize attributes of dataclass."""
        if len(self.data1) != len(self.data2) != len(self.data3):
            raise RuntimeError(f'Not consistent length of batches! {len(self.data1)}!= {len(self.data2)} != {len(self.data3)}')
        if self.num_of_batches == 0:
            raise ValueError('Batch size has to be larger than 0!')
        assert 'test' in self.data3[0].keys(), f'Test is not present in data: {self.data3[0].keys()}!'

    @classmethod
    def collate(cls, batch: List[DummyVectorMapFeature]) -> DummyVectorMapFeature:
        """Inherited, see superclass."""
        return DummyVectorMapFeature(data1=[data for b in batch for data in b.data1], data2=[data for b in batch for data in b.data2], data3=[data for b in batch for data in b.data3])

    @property
    def num_of_batches(self) -> int:
        """Number of batches in the feature."""
        return len(self.data1)

    def to_feature_tensor(self) -> DummyVectorMapFeature:
        """Inherited, see superclass."""
        return DummyVectorMapFeature(self.data1, self.data2, self.data3)

    def to_device(self, device: torch.device) -> DummyVectorMapFeature:
        """Implemented. See interface."""
        return DummyVectorMapFeature(data1=[data.to(device) for data in self.data1], data2=[data.to(device) for data in self.data2], data3=[{'test': data['test'].to(device) for data in self.data3}])

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> DummyVectorMapFeature:
        """Implemented. See interface."""
        return DummyVectorMapFeature(data1=data['data1'], data2=data['data2'], data3=data['data3'])

    def unpack(self) -> List[DummyVectorMapFeature]:
        """Implemented. See interface."""
        return [DummyVectorMapFeature([data1], [data2], [data3]) for data1, data2, data3 in zip(self.data1, self.data2, self.data3)]

@classmethod
def collate(cls, batch: List[DummyVectorMapFeature]) -> DummyVectorMapFeature:
    """Inherited, see superclass."""
    return DummyVectorMapFeature(data1=[data for b in batch for data in b.data1], data2=[data for b in batch for data in b.data2], data3=[data for b in batch for data in b.data3])

def to_feature_tensor(self) -> DummyVectorMapFeature:
    """Inherited, see superclass."""
    return DummyVectorMapFeature(self.data1, self.data2, self.data3)

def to_device(self, device: torch.device) -> DummyVectorMapFeature:
    """Implemented. See interface."""
    return DummyVectorMapFeature(data1=[data.to(device) for data in self.data1], data2=[data.to(device) for data in self.data2], data3=[{'test': data['test'].to(device) for data in self.data3}])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> DummyVectorMapFeature:
    """Implemented. See interface."""
    return DummyVectorMapFeature(data1=data['data1'], data2=data['data2'], data3=data['data3'])

def unpack(self) -> List[DummyVectorMapFeature]:
    """Implemented. See interface."""
    return [DummyVectorMapFeature([data1], [data2], [data3]) for data1, data2, data3 in zip(self.data1, self.data2, self.data3)]

class DummyVectorMapBuilder(AbstractFeatureBuilder):
    """Dummy vector map feature builder used in testing."""

    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'vector_map'

    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return DummyVectorMapFeature

    def get_features_from_simulation(self, history: SimulationHistoryBuffer, initialization: PlannerInitialization) -> AbstractModelFeature:
        """Inherited, see superclass."""
        return NotImplemented

    def get_features_from_scenario(self, scenario: AbstractScenario) -> AbstractModelFeature:
        """Inherited, see superclass."""
        return DummyVectorMapFeature(data1=[np.zeros((10, 10, 10))], data2=[np.zeros((10, 10, 10))], data3=[{'test': np.zeros((10, 10, 10))}])

def get_features_from_scenario(self, scenario: AbstractScenario) -> AbstractModelFeature:
    """Inherited, see superclass."""
    return DummyVectorMapFeature(data1=[np.zeros((10, 10, 10))], data2=[np.zeros((10, 10, 10))], data3=[{'test': np.zeros((10, 10, 10))}])

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

def _accumulate_connections(node_idx_to_neighbor_dict: Dict[int, Dict[str, Dict[int, int]]], scales: List[int]) -> Dict[int, torch.Tensor]:
    """
    Accumulate the connections over multiple scales
    :param node_idx_to_neighbor_dict: {node_idx: neighbor_dict} where each neighbor_dict
                                      will have format {'i_hop_neighbors': set_of_i_hop_neighbors}
    :param scales: Connections scales to generate.
    :return: Multi-scale connections as a dict of {scale: connections_of_scale}.
    """
    multi_scale_connections: Dict[int, torch.Tensor] = {}
    for scale in scales:
        scale_hop_neighbors = f'{scale}_hop_neighbors'
        scale_connections: List[List[int]] = []
        for node_idx, neighbor_dict in node_idx_to_neighbor_dict.items():
            for n_hop_neighbor in neighbor_dict[scale_hop_neighbors]:
                scale_connections.append([node_idx, n_hop_neighbor])
        if len(scale_connections) == 0:
            multi_scale_connections[scale] = torch.empty((0, 2), dtype=torch.int64)
        else:
            multi_scale_connections[scale] = torch.tensor(scale_connections, dtype=torch.int64)
    return multi_scale_connections

def _generate_multi_scale_connections(connections: torch.Tensor, scales: List[int]) -> Dict[int, torch.Tensor]:
    """
    Generate multi-scale connections by finding the neighbors up to max(scales) hops away for each node.
    :param connections: <torch.Tensor: num_connections, 2>. A 1-hop connection is represented by [start_idx, end_idx]
    :param scales: Connections scales to generate.
    :return: Multi-scale connections as a dict of {scale: connections_of_scale}.
             Each connections_of_scale is represented by an array of <np.ndarray: num_connections, 2>,
    """
    if len(connections.shape) != 2 or connections.shape[1] != 2:
        raise ValueError(f'Unexpected connections shape: {connections.shape}')
    node_idx_to_neighbor_dict: Dict[int, Dict[str, Dict[int, int]]] = {}
    dummy_value: int = 0
    for connection in connections:
        start_idx, end_idx = (connection[0].item(), connection[1].item())
        if start_idx not in node_idx_to_neighbor_dict:
            start_empty: Dict[int, int] = {}
            node_idx_to_neighbor_dict[start_idx] = {'1_hop_neighbors': start_empty}
        if end_idx not in node_idx_to_neighbor_dict:
            end_empty: Dict[int, int] = {}
            node_idx_to_neighbor_dict[end_idx] = {'1_hop_neighbors': end_empty}
        node_idx_to_neighbor_dict[start_idx]['1_hop_neighbors'][end_idx] = dummy_value
    for scale in range(2, max(scales) + 1):
        scale_hop_neighbors = f'{scale}_hop_neighbors'
        prev_scale_hop_neighbors = f'{scale - 1}_hop_neighbors'
        for neighbor_dict in node_idx_to_neighbor_dict.values():
            empty: Dict[int, int] = {}
            neighbor_dict[scale_hop_neighbors] = empty
            for n_hop_neighbor in neighbor_dict[prev_scale_hop_neighbors]:
                for n_plus_1_hop_neighbor in node_idx_to_neighbor_dict[n_hop_neighbor]['1_hop_neighbors']:
                    neighbor_dict[scale_hop_neighbors][n_plus_1_hop_neighbor] = dummy_value
    return _accumulate_connections(node_idx_to_neighbor_dict, scales)

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

def forward(self, features: FeaturesType) -> TargetsType:
    """
        Implemented. See interface.
        """
    if self.raise_on_forward:
        raise ValueError('forward() called when raise_on_forward set.')
    self._validate_input_feature(features)
    return {'trajectory': Trajectory(data=self.data_tensor_to_return)}

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

class TestVectorMapFeatureBuilderLaneMetadata(unittest.TestCase):
    """Test feature builder that constructs map features in vectorized format."""

    @patch(f'{PATCH_PREFIX}.AbstractScenario', autospec=True)
    def test_vectormap_example_metadata(self, mock_abstract_scenario: Mock) -> None:
        """
        Test VectorMapFeatureBuilder
        """
        test_radius = 50.0
        builder = VectorMapFeatureBuilder(radius=test_radius, connection_scales=None)
        initial_ego_center_pose = StateSE2(x=0.0, y=0.0, heading=0.0)
        timestamp = 1000000
        traffic_light_statuses = [TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=4000, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=5000, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.YELLOW, lane_connector_id=5002, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.RED, lane_connector_id=5003, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.RED, lane_connector_id=5005, timestamp=timestamp)]
        route_roadblock_ids = ['60000', '70000']
        _fill_in_abstract_scenario_mock_parameters(scenario_mock=mock_abstract_scenario, initial_ego_center_pose=initial_ego_center_pose, initial_timestamp=timestamp, traffic_light_statuses=traffic_light_statuses, route_roadblock_ids=route_roadblock_ids)
        with patch_with_validation('nuplan.planning.training.preprocessing.feature_builders.vector_map_feature_builder.get_neighbor_vector_map', _get_neighbor_vector_map_patch):
            vector_map_feature = builder.get_features_from_scenario(mock_abstract_scenario)
            self.assertIsInstance(vector_map_feature, VectorMap)
            self.assertEqual(vector_map_feature.num_of_batches, 1)
            self.assertTrue(vector_map_feature.is_valid)
            self.assertEqual(vector_map_feature.num_lanes_in_sample(0), 6)
            self.assertEqual(vector_map_feature.get_lane_coords(0).shape, (12, 2, 2))
            actual_traffic_light_data = vector_map_feature.traffic_light_data[0]
            expected_traffic_light_data = np.zeros_like(actual_traffic_light_data)
            tl_encoding_dict = LaneSegmentTrafficLightData._one_hot_encoding
            expected_traffic_light_data[[0, 1]] = tl_encoding_dict[TrafficLightStatusType.GREEN]
            expected_traffic_light_data[[6, 7, 10, 11]] = tl_encoding_dict[TrafficLightStatusType.RED]
            expected_traffic_light_data[[2, 3, 4, 5, 8, 9]] = tl_encoding_dict[TrafficLightStatusType.UNKNOWN]
            np_test.assert_allclose(actual_traffic_light_data, expected_traffic_light_data)
            actual_on_route_status = vector_map_feature.on_route_status[0]
            expected_on_route_status = np.zeros_like(actual_on_route_status)
            route_encoding_dict = LaneOnRouteStatusData._binary_encoding
            expected_on_route_status[[4, 5, 10, 11]] = route_encoding_dict[OnRouteStatusType.OFF_ROUTE]
            expected_on_route_status[[0, 1, 2, 3, 6, 7, 8, 9]] = route_encoding_dict[OnRouteStatusType.ON_ROUTE]
            np_test.assert_allclose(actual_on_route_status, expected_on_route_status)

@patch(f'{PATCH_PREFIX}.AbstractScenario', autospec=True)
def test_vectormap_example_metadata(self, mock_abstract_scenario: Mock) -> None:
    """
        Test VectorMapFeatureBuilder
        """
    test_radius = 50.0
    builder = VectorMapFeatureBuilder(radius=test_radius, connection_scales=None)
    initial_ego_center_pose = StateSE2(x=0.0, y=0.0, heading=0.0)
    timestamp = 1000000
    traffic_light_statuses = [TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=4000, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=5000, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.YELLOW, lane_connector_id=5002, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.RED, lane_connector_id=5003, timestamp=timestamp), TrafficLightStatusData(status=TrafficLightStatusType.RED, lane_connector_id=5005, timestamp=timestamp)]
    route_roadblock_ids = ['60000', '70000']
    _fill_in_abstract_scenario_mock_parameters(scenario_mock=mock_abstract_scenario, initial_ego_center_pose=initial_ego_center_pose, initial_timestamp=timestamp, traffic_light_statuses=traffic_light_statuses, route_roadblock_ids=route_roadblock_ids)
    with patch_with_validation('nuplan.planning.training.preprocessing.feature_builders.vector_map_feature_builder.get_neighbor_vector_map', _get_neighbor_vector_map_patch):
        vector_map_feature = builder.get_features_from_scenario(mock_abstract_scenario)
        self.assertIsInstance(vector_map_feature, VectorMap)
        self.assertEqual(vector_map_feature.num_of_batches, 1)
        self.assertTrue(vector_map_feature.is_valid)
        self.assertEqual(vector_map_feature.num_lanes_in_sample(0), 6)
        self.assertEqual(vector_map_feature.get_lane_coords(0).shape, (12, 2, 2))
        actual_traffic_light_data = vector_map_feature.traffic_light_data[0]
        expected_traffic_light_data = np.zeros_like(actual_traffic_light_data)
        tl_encoding_dict = LaneSegmentTrafficLightData._one_hot_encoding
        expected_traffic_light_data[[0, 1]] = tl_encoding_dict[TrafficLightStatusType.GREEN]
        expected_traffic_light_data[[6, 7, 10, 11]] = tl_encoding_dict[TrafficLightStatusType.RED]
        expected_traffic_light_data[[2, 3, 4, 5, 8, 9]] = tl_encoding_dict[TrafficLightStatusType.UNKNOWN]
        np_test.assert_allclose(actual_traffic_light_data, expected_traffic_light_data)
        actual_on_route_status = vector_map_feature.on_route_status[0]
        expected_on_route_status = np.zeros_like(actual_on_route_status)
        route_encoding_dict = LaneOnRouteStatusData._binary_encoding
        expected_on_route_status[[4, 5, 10, 11]] = route_encoding_dict[OnRouteStatusType.OFF_ROUTE]
        expected_on_route_status[[0, 1, 2, 3, 6, 7, 8, 9]] = route_encoding_dict[OnRouteStatusType.ON_ROUTE]
        np_test.assert_allclose(actual_on_route_status, expected_on_route_status)

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

@dataclass
class VectorMap(AbstractModelFeature):
    """
    Vector map data struture, including:
        coords: List[<np.ndarray: num_lane_segments, 2, 2>].
            The (x, y) coordinates of the start and end point of the lane segments.
        lane_groupings: List[List[<np.ndarray: num_lane_segments_in_lane>]].
            Each lane grouping or polyline is represented by an array of indices of lane segments
            in coords belonging to the given lane. Each batch contains a List of lane groupings.
        multi_scale_connections: List[Dict of {scale: connections_of_scale}].
            Each connections_of_scale is represented by an array of <np.ndarray: num_connections, 2>,
            and each column in the array is [from_lane_segment_idx, to_lane_segment_idx].
        on_route_status: List[<np.ndarray: num_lane_segments, 2>].
            Binary encoding of on route status for lane segment at given index.
            Encoding: off route [0, 1], on route [1, 0], unknown [0, 0]
        traffic_light_data: List[<np.ndarray: num_lane_segments, 4>]
            One-hot encoding of on traffic light status for lane segment at given index.
            Encoding: green [1, 0, 0, 0] yellow [0, 1, 0, 0], red [0, 0, 1, 0], unknown [0, 0, 0, 1]

    In all cases, the top level List represent number of batches. This is a special feature where
    each batch entry can have different size. Similarly, each lane grouping within a batch can have
    a variable number of elements. For that reason, the feature can not be placed to a single tensor,
    and we batch the feature with a custom `collate` function
    """
    coords: List[FeatureDataType]
    lane_groupings: List[List[FeatureDataType]]
    multi_scale_connections: List[Dict[int, FeatureDataType]]
    on_route_status: List[FeatureDataType]
    traffic_light_data: List[FeatureDataType]
    _lane_coord_dim: int = 2
    _on_route_status_encoding_dim: int = LaneOnRouteStatusData.encoding_dim()

    def __post_init__(self) -> None:
        """Sanitize attributes of the dataclass."""
        if len(self.coords) != len(self.multi_scale_connections):
            raise RuntimeError(f'Not consistent length of batches! {len(self.coords)} != {len(self.multi_scale_connections)}')
        if len(self.coords) != len(self.lane_groupings):
            raise RuntimeError(f'Not consistent length of batches! {len(self.coords)} != {len(self.lane_groupings)}')
        if len(self.coords) != len(self.on_route_status):
            raise RuntimeError(f'Not consistent length of batches! {len(self.coords)} != {len(self.on_route_status)}')
        if len(self.coords) != len(self.traffic_light_data):
            raise RuntimeError(f'Not consistent length of batches! {len(self.coords)} != {len(self.traffic_light_data)}')
        if len(self.coords) == 0:
            raise RuntimeError('Batch size has to be > 0!')
        for coords in self.coords:
            if coords.shape[1] != 2 or coords.shape[2] != 2:
                raise RuntimeError('The dimension of coords is not correct!')
        for coords, traffic_lights in zip(self.coords, self.traffic_light_data):
            if coords.shape[0] != traffic_lights.shape[0]:
                raise RuntimeError('Number of segments are inconsistent')

    @cached_property
    def is_valid(self) -> bool:
        """Inherited, see superclass."""
        return len(self.coords) > 0 and len(self.coords[0]) > 0 and (len(self.lane_groupings) > 0) and (len(self.lane_groupings[0]) > 0) and (len(self.lane_groupings[0][0]) > 0) and (len(self.on_route_status) > 0) and (len(self.on_route_status[0]) > 0) and (len(self.traffic_light_data) > 0) and (len(self.traffic_light_data[0]) > 0) and (len(self.multi_scale_connections) > 0) and (len(list(self.multi_scale_connections[0].values())[0]) > 0)

    @property
    def num_of_batches(self) -> int:
        """
        :return: number of batches
        """
        return len(self.coords)

    def num_lanes_in_sample(self, sample_idx: int) -> int:
        """
        :param sample_idx: sample index in batch
        :return: number of lanes represented by lane_groupings in sample
        """
        return len(self.lane_groupings[sample_idx])

    @classmethod
    def lane_coord_dim(cls) -> int:
        """
        :return: dimension of coords, should be 2 (x, y)
        """
        return cls._lane_coord_dim

    @classmethod
    def on_route_status_encoding_dim(cls) -> int:
        """
        :return: dimension of route following status encoding
        """
        return cls._on_route_status_encoding_dim

    @classmethod
    def flatten_lane_coord_dim(cls) -> int:
        """
        :return: dimension of flattened start and end coords, should be 4 = 2 x (x, y)
        """
        return 2 * cls._lane_coord_dim

    def get_lane_coords(self, sample_idx: int) -> FeatureDataType:
        """
        Retrieve lane coordinates at given sample index.
        :param sample_idx: the batch index of interest.
        :return: lane coordinate features.
        """
        return self.coords[sample_idx]

    @classmethod
    def collate(cls, batch: List[VectorMap]) -> VectorMap:
        """Implemented. See interface."""
        return VectorMap(coords=[data for sample in batch for data in sample.coords], lane_groupings=[data for sample in batch for data in sample.lane_groupings], multi_scale_connections=[data for sample in batch for data in sample.multi_scale_connections], on_route_status=[data for sample in batch for data in sample.on_route_status], traffic_light_data=[data for sample in batch for data in sample.traffic_light_data])

    def to_feature_tensor(self) -> VectorMap:
        """Implemented. See interface."""
        return VectorMap(coords=[to_tensor(coords).contiguous() for coords in self.coords], lane_groupings=[[to_tensor(lane_grouping).contiguous() for lane_grouping in lane_groupings] for lane_groupings in self.lane_groupings], multi_scale_connections=[{scale: to_tensor(connection).contiguous() for scale, connection in multi_scale_connections.items()} for multi_scale_connections in self.multi_scale_connections], on_route_status=[to_tensor(status).contiguous() for status in self.on_route_status], traffic_light_data=[to_tensor(data).contiguous() for data in self.traffic_light_data])

    def to_device(self, device: torch.device) -> VectorMap:
        """Implemented. See interface."""
        return VectorMap(coords=[coords.to(device=device) for coords in self.coords], lane_groupings=[[lane_grouping.to(device=device) for lane_grouping in lane_groupings] for lane_groupings in self.lane_groupings], multi_scale_connections=[{scale: connection.to(device=device) for scale, connection in multi_scale_connections.items()} for multi_scale_connections in self.multi_scale_connections], on_route_status=[status.to(device=device) for status in self.on_route_status], traffic_light_data=[data.to(device=device) for data in self.traffic_light_data])

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> VectorMap:
        """Implemented. See interface."""
        return VectorMap(coords=data['coords'], lane_groupings=data['lane_groupings'], multi_scale_connections=data['multi_scale_connections'], on_route_status=data['on_route_status'], traffic_light_data=data['traffic_light_data'])

    def unpack(self) -> List[VectorMap]:
        """Implemented. See interface."""
        return [VectorMap([coords], [lane_groupings], [multi_scale_connections], [on_route_status], [traffic_light_data]) for coords, lane_groupings, multi_scale_connections, on_route_status, traffic_light_data in zip(self.coords, self.lane_groupings, self.multi_scale_connections, self.on_route_status, self.traffic_light_data)]

    def rotate(self, quaternion: Quaternion) -> VectorMap:
        """
        Rotate the vector map.
        :param quaternion: Rotation to apply.
        """
        for coord in self.coords:
            validate_type(coord, np.ndarray)
        return VectorMap(coords=[rotate_coords(data, quaternion) for data in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

    def translate(self, translation_value: FeatureDataType) -> VectorMap:
        """
        Translate the vector map.
        :param translation_value: Translation in x, y, z.
        """
        assert translation_value.size == 3, 'Translation value must have dimension of 3 (x, y, z)'
        are_the_same_type(translation_value, self.coords[0])
        return VectorMap(coords=[translate_coords(coords, translation_value) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

    def scale(self, scale_value: FeatureDataType) -> VectorMap:
        """
        Scale the vector map.
        :param scale_value: <np.float: 3,>. Scale in x, y, z.
        """
        assert scale_value.size == 3, f'Scale value has incorrect dimension: {scale_value.size}!'
        are_the_same_type(scale_value, self.coords[0])
        return VectorMap(coords=[scale_coords(coords, scale_value) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

    def xflip(self) -> VectorMap:
        """
        Flip the vector map along the X-axis.
        """
        return VectorMap(coords=[xflip_coords(coords) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

    def yflip(self) -> VectorMap:
        """
        Flip the vector map along the Y-axis.
        """
        return VectorMap(coords=[yflip_coords(coords) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

    def extract_lane_polyline(self, sample_idx: int, lane_idx: int) -> FeatureDataType:
        """
        Extract start points (first coordinate) for segments in lane, specified by segment indices
            in lane_groupings.
        :param sample_idx: sample index in batch
        :param lane_idx: lane index in sample
        :return: lane_polyline: <np.ndarray: num_lane_segments_in_lane, 2>. Array of start points
            for each segment in lane.
        """
        lane_grouping = self.lane_groupings[sample_idx][lane_idx]
        return self.coords[sample_idx][lane_grouping, 0]

@classmethod
def collate(cls, batch: List[VectorMap]) -> VectorMap:
    """Implemented. See interface."""
    return VectorMap(coords=[data for sample in batch for data in sample.coords], lane_groupings=[data for sample in batch for data in sample.lane_groupings], multi_scale_connections=[data for sample in batch for data in sample.multi_scale_connections], on_route_status=[data for sample in batch for data in sample.on_route_status], traffic_light_data=[data for sample in batch for data in sample.traffic_light_data])

def to_device(self, device: torch.device) -> VectorMap:
    """Implemented. See interface."""
    return VectorMap(coords=[coords.to(device=device) for coords in self.coords], lane_groupings=[[lane_grouping.to(device=device) for lane_grouping in lane_groupings] for lane_groupings in self.lane_groupings], multi_scale_connections=[{scale: connection.to(device=device) for scale, connection in multi_scale_connections.items()} for multi_scale_connections in self.multi_scale_connections], on_route_status=[status.to(device=device) for status in self.on_route_status], traffic_light_data=[data.to(device=device) for data in self.traffic_light_data])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> VectorMap:
    """Implemented. See interface."""
    return VectorMap(coords=data['coords'], lane_groupings=data['lane_groupings'], multi_scale_connections=data['multi_scale_connections'], on_route_status=data['on_route_status'], traffic_light_data=data['traffic_light_data'])

def unpack(self) -> List[VectorMap]:
    """Implemented. See interface."""
    return [VectorMap([coords], [lane_groupings], [multi_scale_connections], [on_route_status], [traffic_light_data]) for coords, lane_groupings, multi_scale_connections, on_route_status, traffic_light_data in zip(self.coords, self.lane_groupings, self.multi_scale_connections, self.on_route_status, self.traffic_light_data)]

def rotate(self, quaternion: Quaternion) -> VectorMap:
    """
        Rotate the vector map.
        :param quaternion: Rotation to apply.
        """
    for coord in self.coords:
        validate_type(coord, np.ndarray)
    return VectorMap(coords=[rotate_coords(data, quaternion) for data in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

def translate(self, translation_value: FeatureDataType) -> VectorMap:
    """
        Translate the vector map.
        :param translation_value: Translation in x, y, z.
        """
    assert translation_value.size == 3, 'Translation value must have dimension of 3 (x, y, z)'
    are_the_same_type(translation_value, self.coords[0])
    return VectorMap(coords=[translate_coords(coords, translation_value) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

def scale(self, scale_value: FeatureDataType) -> VectorMap:
    """
        Scale the vector map.
        :param scale_value: <np.float: 3,>. Scale in x, y, z.
        """
    assert scale_value.size == 3, f'Scale value has incorrect dimension: {scale_value.size}!'
    are_the_same_type(scale_value, self.coords[0])
    return VectorMap(coords=[scale_coords(coords, scale_value) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

def xflip(self) -> VectorMap:
    """
        Flip the vector map along the X-axis.
        """
    return VectorMap(coords=[xflip_coords(coords) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

def yflip(self) -> VectorMap:
    """
        Flip the vector map along the Y-axis.
        """
    return VectorMap(coords=[yflip_coords(coords) for coords in self.coords], lane_groupings=self.lane_groupings, multi_scale_connections=self.multi_scale_connections, on_route_status=self.on_route_status, traffic_light_data=self.traffic_light_data)

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

def get_present_ego_in_sample(self, sample_idx: int) -> FeatureDataType:
    """
        Return the present ego in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: 8>. ego at sample index.
        """
    self._validate_ego_query(sample_idx)
    return self.ego[sample_idx][-1]

def get_ego_agents_center_in_sample(self, sample_idx: int) -> FeatureDataType:
    """
        Return ego center in the given sample index.
        :param sample_idx: the batch index of interest.
        :return: <FeatureDataType: 2>. (x, y) positions of the ego's center at sample index.
        """
    self._validate_ego_query(sample_idx)
    return self.get_present_ego_in_sample(sample_idx)[:GenericEgoFeatureIndex.y() + 1]

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

@dataclass
class Trajectories(AbstractModelFeature):
    """
    A feature that contains multiple trajectories
    """
    trajectories: List[Trajectory]

    def to_feature_tensor(self) -> Trajectories:
        """Implemented. See interface."""
        return Trajectories(trajectories=[trajectory.to_feature_tensor() for trajectory in self.trajectories])

    def to_device(self, device: torch.device) -> Trajectories:
        """Implemented. See interface."""
        return Trajectories(trajectories=[trajectory.to_device(device) for trajectory in self.trajectories])

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Trajectories:
        """Implemented. See interface."""
        return Trajectories(trajectories=[Trajectory.deserialize(trajectory) for trajectory in data['trajectories']])

    @property
    def number_of_trajectories(self) -> int:
        """
        :return: number of trajectories in this feature.
        """
        return len(self.trajectories)

    def unpack(self) -> List[Trajectories]:
        """Implemented. See interface."""
        return [Trajectories([trajectories]) for trajectories in self.trajectories]

def to_feature_tensor(self) -> Trajectories:
    """Implemented. See interface."""
    return Trajectories(trajectories=[trajectory.to_feature_tensor() for trajectory in self.trajectories])

def to_device(self, device: torch.device) -> Trajectories:
    """Implemented. See interface."""
    return Trajectories(trajectories=[trajectory.to_device(device) for trajectory in self.trajectories])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Trajectories:
    """Implemented. See interface."""
    return Trajectories(trajectories=[Trajectory.deserialize(trajectory) for trajectory in data['trajectories']])

def unpack(self) -> List[Trajectories]:
    """Implemented. See interface."""
    return [Trajectories([trajectories]) for trajectories in self.trajectories]

def get_focus_agent_raster(agent: AgentState, raster_shape: Tuple[int, int], ego_longitudinal_offset: float, target_pixel_size: float) -> npt.NDArray[np.float32]:
    """
    Construct the focus agent layer of the raster by drawing a polygon of the ego's extent in the middle of the grid.
    :param agent: Focus agent of the target raster.
    :param raster_shape: Shape of the target raster.
    :param ego_longitudinal_offset: [%] offset percentage to place the ego vehicle in the raster.
    :param target_pixel_size: [m] target pixel size in meters.
    :return: Constructed ego raster layer.
    """
    ego_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    map_x_center = int(raster_shape[1] * 0.5)
    map_y_center = int(raster_shape[0] * (0.5 + ego_longitudinal_offset))
    ego_width_pixels = int(agent.box.width / target_pixel_size)
    ego_length_pixels = int(agent.box.length / target_pixel_size)
    ego_top_left = (map_x_center - ego_width_pixels // 2, map_y_center - ego_length_pixels // 2)
    ego_bottom_right = (map_x_center + ego_width_pixels // 2, map_y_center + ego_length_pixels // 2)
    cv2.rectangle(ego_raster, ego_top_left, ego_bottom_right, 1, -1)
    return np.asarray(ego_raster)

def get_ego_raster(raster_shape: Tuple[int, int], ego_longitudinal_offset: float, ego_width_pixels: float, ego_front_length_pixels: float, ego_rear_length_pixels: float) -> npt.NDArray[np.float32]:
    """
    Construct the ego layer of the raster by drawing a polygon of the ego's extent in the middle of the grid.
    :param raster_shape: shape of the target raster.
    :param ego_longitudinal_offset: [%] offset percentage to place the ego vehicle in the raster.
    :param ego_width_pixels: width of the ego vehicle in pixels.
    :param ego_front_length_pixels: distance between the rear axle and the front bumper in pixels.
    :param ego_rear_length_pixels: distance between the rear axle and the rear bumper in pixels.
    :return: constructed ego raster layer.
    """
    ego_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    map_x_center = int(raster_shape[1] * 0.5)
    map_y_center = int(raster_shape[0] * (0.5 + ego_longitudinal_offset))
    ego_top_left = (map_x_center - ego_width_pixels // 2, map_y_center - ego_front_length_pixels)
    ego_bottom_right = (map_x_center + ego_width_pixels // 2, map_y_center + ego_rear_length_pixels)
    cv2.rectangle(ego_raster, ego_top_left, ego_bottom_right, 1, -1)
    return np.asarray(ego_raster)

def rotate_coords(coords: npt.NDArray[np.float32], quaternion: Quaternion) -> npt.NDArray[np.float32]:
    """
    Rotate all vector coordinates within input tensor using input quaternion.
    :param coords: coordinates to translate: <num_map_elements, num_points_per_element, 2>.
    :param quaternion: Rotation to apply.
    :return rotated coords.
    """
    _validate_coords_shape(coords)
    validate_type(coords, np.ndarray)
    num_map_elements, num_points_per_element, _ = coords.shape
    coords = coords.reshape(num_map_elements * num_points_per_element, 2)
    coords = np.concatenate((coords, np.zeros_like(coords[:, 0:1])), axis=-1)
    coords = np.dot(quaternion.rotation_matrix.astype(coords.dtype), coords.T)
    return coords.T[:, :2].reshape(num_map_elements, num_points_per_element, 2)

def translate_coords(coords: FeatureDataType, translation_value: FeatureDataType, avails: Optional[FeatureDataType]=None) -> FeatureDataType:
    """
    Translate all vector coordinates within input tensor along x, y dimensions of input translation tensor.
        Note: Z-dimension ignored.
    :param coords: coordinates to translate: <num_map_elements, num_points_per_element, 2>.
    :param translation_value: <np.float: 3,>. Translation in x, y, z.
    :param avails: Optional mask to specify real vs zero-padded data to ignore in coords:
        <num_map_elements, num_points_per_element>.
    :return translated coords.
    :raise ValueError: If translation_value dimensions are not valid or coords and avails have inconsistent shape.
    """
    if translation_value.shape[0] != 3:
        raise ValueError(f'Translation value has incorrect dimensions: {translation_value.shape[0]}! Expected: 3 (x, y, z)')
    _validate_coords_shape(coords)
    are_the_same_type(coords, translation_value)
    if avails is not None and coords.shape[:2] != avails.shape:
        raise ValueError(f'Mismatching shape between coords and availabilities: {coords.shape[:2]}, {avails.shape}')
    coords = coords + translation_value[:2]
    if avails is not None:
        coords[~avails] = 0.0
    return coords

def scale_coords(coords: FeatureDataType, scale_value: FeatureDataType) -> FeatureDataType:
    """
    Scale all vector coordinates within input tensor along x, y dimensions of input scaling tensor.
        Note: Z-dimension ignored.
    :param coords: coordinates to scale: <num_map_elements, num_points_per_element, 2>.
    :param scale_value: <np.float: 3,>. Scale in x, y, z.
    :return scaled coords.
    :raise ValueError: If scale_value dimensions are not valid.
    """
    if scale_value.shape[0] != 3:
        raise ValueError(f'Scale value has incorrect dimensions: {scale_value.shape[0]}! Expected: 3 (x, y, z)')
    _validate_coords_shape(coords)
    are_the_same_type(coords, scale_value)
    return coords * scale_value[:2]

def xflip_coords(coords: FeatureDataType) -> FeatureDataType:
    """
    Flip all vector coordinates within input tensor along X-axis.
    :param coords: coordinates to flip: <num_map_elements, num_points_per_element, 2>.
    :return flipped coords.
    """
    _validate_coords_shape(coords)
    coords = deepcopy(coords)
    coords[:, :, 0] *= -1
    return coords

def yflip_coords(coords: FeatureDataType) -> FeatureDataType:
    """
    Flip all vector coordinates within input tensor along Y-axis.
    :param coords: coordinates to flip: <num_map_elements, num_points_per_element, 2>.
    :return flipped coords.
    """
    _validate_coords_shape(coords)
    coords = deepcopy(coords)
    coords[:, :, 1] *= -1
    return coords

@dataclass
class AgentsTrajectories(AbstractModelFeature):
    """
    Model input feature representing the present and past states of the ego and agents.

    The structure inludes:
        agents: List[<np.ndarray: num_frames, num_agents, 6>].
            The outer list is the batch dimension.
            The num_frames includes both present and past frames.
            The num_agents is padded to fit the largest number of agents across all frames.
            The last dimension is the agent pose (x, y, heading) velocities (vx, vy, yaw rate) at time t.

    The present/future frames dimension is populated in ascending chronological order, i.e. (t_1, t_2, ..., t_n)

    The outer List represent number of batches. This is a special feature where each batch entry
    can have different size. For that reason, the feature can not be placed to a single tensor,
    and we batch the feature with a custom `collate` function
    """
    data: List[FeatureDataType]

    def __post_init__(self) -> None:
        """Sanitize attributes of the dataclass."""
        if len(self.data) == 0:
            raise AssertionError('Batch size has to be > 0!')

    @property
    def batch_size(self) -> int:
        """
        :return: batch size
        """
        return len(self.data)

    @staticmethod
    def states_dim() -> int:
        """
        :return: agent state dimension
        """
        return 6

    @property
    def num_frames(self) -> int:
        """
        :return: number of future frames. Note: this excludes the present frame
        """
        return int(self.data[0].shape[0])

    @property
    def features_dim(self) -> int:
        """
        :return: ego feature dimension
        """
        return self.num_frames * AgentsTrajectories.states_dim()

    @classmethod
    def collate(cls, batch: List[AgentsTrajectories]) -> AgentsTrajectories:
        """
        Implemented. See interface.
        Collates a list of features that each have batch size of 1.
        """
        return AgentsTrajectories(data=[item.data[0] for item in batch])

    def to_feature_tensor(self) -> AgentsTrajectories:
        """Implemented. See interface."""
        return AgentsTrajectories(data=[to_tensor(data) for data in self.data])

    def to_device(self, device: torch.device) -> AgentsTrajectories:
        """Implemented. See interface."""
        return AgentsTrajectories(data=[data.to(device=device) for data in self.data])

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> AgentsTrajectories:
        """Implemented. See interface."""
        return AgentsTrajectories(data=data['data'])

    def unpack(self) -> List[AgentsTrajectories]:
        """Implemented. See interface."""
        return [AgentsTrajectories([data]) for data in self.data]

    def num_agents_in_sample(self, sample_idx: int) -> int:
        """
        Returns the number of agents at a given batch
        :param sample_idx: the batch index of interest
        :return: number of agents in the given batch
        """
        return int(self.data[sample_idx].shape[1])

    def has_agents(self, batch_idx: int) -> bool:
        """
        Check whether agents exist in the feature.
        :param batch_idx: the batch index of interest
        :return: whether agents exist in the feature
        """
        return self.num_agents_in_sample(batch_idx) > 0

    @property
    def xy(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: num_frames, num_agents, 2>] x, y of all agent across all frames
        """
        return [sample[..., :2] for sample in self.data]

    @property
    def heading(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: num_frames, num_agents, 1>] yaw of all agent across all frames
        """
        return [sample[..., 2] for sample in self.data]

    @property
    def poses(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: num_frames, num_agents, 3>] x, y, yaw of all agents across all frames
        """
        return [sample[..., :3] for sample in self.data]

    @property
    def xy_velocity(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: num_frames, num_agents, 2>] x velocity, y velocity of all agent across all frames
        """
        return [sample[..., 3:5] for sample in self.data]

    @property
    def yaw_rate(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: num_frames, num_agents, 1>] yaw_rate of all agents across all frames
        """
        return [sample[..., 5] for sample in self.data]

    @property
    def terminal_xy(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: terminal_frame, num_agents, 2>] x, y of all agents at terminal frame
        """
        return [sample[-1, :, :2] for sample in self.data]

    @property
    def terminal_heading(self) -> FeatureDataType:
        """
        :return: List[<np.ndarray: terminal_frame, num_agents, 1>] heading of all agents at terminal frame
        """
        return [sample[-1, :, 3] for sample in self.data]

    def get_agents_only_trajectories(self) -> AgentsTrajectories:
        """
        :return: A new AgentsTrajectories isntance with only trajecotries data of agents (ignoring ego AV).
        """
        return AgentsTrajectories([sample[1:] for sample in self.data])

    def reshape_to_agents(self) -> None:
        """
        Reshapes predicted agent data by number of agents
        """
        axes = (1, 0) if isinstance(self.data[0], torch.Tensor) else (1, 0, 2)
        self.data = [sample.transpose(*axes).reshape(-1, self.num_frames, self.states_dim()) for sample in self.data]

@classmethod
def collate(cls, batch: List[AgentsTrajectories]) -> AgentsTrajectories:
    """
        Implemented. See interface.
        Collates a list of features that each have batch size of 1.
        """
    return AgentsTrajectories(data=[item.data[0] for item in batch])

def to_device(self, device: torch.device) -> AgentsTrajectories:
    """Implemented. See interface."""
    return AgentsTrajectories(data=[data.to(device=device) for data in self.data])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> AgentsTrajectories:
    """Implemented. See interface."""
    return AgentsTrajectories(data=data['data'])

def unpack(self) -> List[AgentsTrajectories]:
    """Implemented. See interface."""
    return [AgentsTrajectories([data]) for data in self.data]

def get_agents_only_trajectories(self) -> AgentsTrajectories:
    """
        :return: A new AgentsTrajectories isntance with only trajecotries data of agents (ignoring ego AV).
        """
    return AgentsTrajectories([sample[1:] for sample in self.data])

def to_tensor(data: FeatureDataType) -> torch.Tensor:
    """
    Convert data to tensor
    :param data which is either numpy or Tensor
    :return torch.Tensor
    """
    if isinstance(data, torch.Tensor):
        return data
    elif isinstance(data, np.ndarray):
        return torch.from_numpy(data)
    else:
        raise ValueError(f'Unknown type: {type(data)}')

@dataclass
class Trajectory(AbstractModelFeature):
    """
    Dataclass that holds trajectory signals produced from the model or from the dataset for supervision.

    :param data: either a [num_batches, num_states, 3] or [num_states, 3] representing the trajectory
                 where se2_state is [x, y, heading] with units [meters, meters, radians].
    """
    data: FeatureDataType

    def __post_init__(self) -> None:
        """Sanitize attributes of the dataclass."""
        array_dims = self.num_dimensions
        state_size = self.data.shape[-1]
        if array_dims != 2 and array_dims != 3:
            raise RuntimeError(f'Invalid trajectory array. Expected 2 or 3 dims, got {array_dims}.')
        if state_size != self.state_size():
            raise RuntimeError(f'Invalid trajectory array. Expected {self.state_size()} variables per state, got {state_size}.')

    @cached_property
    def is_valid(self) -> bool:
        """Inherited, see superclass."""
        return len(self.data) > 0 and self.data.shape[-2] > 0 and (self.data.shape[-1] == self.state_size())

    def to_device(self, device: torch.device) -> Trajectory:
        """Implemented. See interface."""
        validate_type(self.data, torch.Tensor)
        return Trajectory(data=self.data.to(device=device))

    def to_feature_tensor(self) -> Trajectory:
        """Inherited, see superclass."""
        return Trajectory(data=to_tensor(self.data))

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Trajectory:
        """Implemented. See interface."""
        return Trajectory(data=data['data'])

    def unpack(self) -> List[Trajectory]:
        """Implemented. See interface."""
        return [Trajectory(data[None]) for data in self.data]

    @staticmethod
    def state_size() -> int:
        """
        Size of each SE2 state of the trajectory.
        """
        return 3

    @property
    def xy(self) -> FeatureDataType:
        """
        :return: tensor of positions [..., x, y]
        """
        return self.data[..., :2]

    @property
    def terminal_position(self) -> FeatureDataType:
        """
        :return: tensor of terminal position [..., x, y]
        """
        return self.data[..., -1, :2]

    @property
    def terminal_heading(self) -> FeatureDataType:
        """
        :return: tensor of terminal position [..., heading]
        """
        return self.data[..., -1, 2]

    @property
    def position_x(self) -> FeatureDataType:
        """
        Array of x positions of trajectory.
        """
        return self.data[..., 0]

    @property
    def numpy_position_x(self) -> FeatureDataType:
        """
        Array of x positions of trajectory.
        """
        return np.asarray(self.data[..., 0])

    @property
    def position_y(self) -> FeatureDataType:
        """
        Array of y positions of trajectory.
        """
        return self.data[..., 1]

    @property
    def numpy_position_y(self) -> FeatureDataType:
        """
        Array of y positions of trajectory.
        """
        return np.asarray(self.data[..., 1])

    @property
    def heading(self) -> FeatureDataType:
        """
        Array of heading positions of trajectory.
        """
        return self.data[..., 2]

    @property
    def num_dimensions(self) -> int:
        """
        :return: dimensions of underlying data
        """
        return len(self.data.shape)

    @property
    def num_of_iterations(self) -> int:
        """
        :return: number of states in a trajectory
        """
        return int(self.data.shape[-2])

    @property
    def num_batches(self) -> Optional[int]:
        """
        :return: number of batches in the trajectory, None if trajectory does not have batch dimension
        """
        return None if self.num_dimensions <= 2 else self.data.shape[0]

    def state_at_index(self, index: int) -> FeatureDataType:
        """
        Query state at index along trajectory horizon
        :param index: along horizon
        :return: state corresponding to the index along trajectory horizon
        @raise in case index is not within valid range: 0 < index <= num_of_iterations
        """
        assert 0 <= index < self.num_of_iterations, f'Index is out of bounds! 0 <= {index} < {self.num_of_iterations}!'
        return self.data[..., index, :]

    def extract_number_of_last_states(self, number_of_states: int) -> Trajectory:
        """
        Extract last number_of_states from a trajectory
        :param number_of_states: from last point
        :return: shorter trajectory containing number_of_states from end of trajectory
        @raise in case number_of_states is not within valid range: 0 < number_of_states <= length
        """
        assert number_of_states > 0, f'number_of_states has to be > 0, {number_of_states} > 0!'
        length = self.num_of_iterations
        assert number_of_states <= length, f'number_of_states has to be smaller than length, {number_of_states} <= {length}!'
        return self.extract_trajectory_between(length - number_of_states, length)

    def extract_trajectory_between(self, start_index: int, end_index: Optional[int]) -> Trajectory:
        """
        Extract partial trajectory based on [start_index, end_index]
        :param start_index: starting index
        :param end_index: ending index
        :return: Trajectory
        @raise in case the desired ranges are not valid
        """
        if not end_index:
            end_index = self.num_of_iterations
        assert 0 <= start_index < self.num_of_iterations, f'Start index is out of bounds! 0 <= {start_index} < {self.num_of_iterations}!'
        assert 0 <= end_index <= self.num_of_iterations, f'Start index is out of bounds! 0 <= {end_index} <= {self.num_of_iterations}!'
        assert start_index < end_index, f'Start Index has to be smaller then end, {start_index} < {end_index}!'
        return Trajectory(data=self.data[..., start_index:end_index, :])

    @classmethod
    def append_to_trajectory(cls, trajectory: Trajectory, new_state: torch.Tensor) -> Trajectory:
        """
        Extend trajectory with a new state, in this case we require that both trajectory and new_state has dimension
        of 3, that means that they both have batch dimension
        :param trajectory: to be extended
        :param new_state: state with which trajectory should be extended
        :return: extended trajectory
        """
        assert trajectory.num_dimensions == 3, f'Trajectory dimension {trajectory.num_dimensions} != 3!'
        assert len(new_state.shape) == 3, f'New state dimension {new_state.shape} != 3!'
        if new_state.shape[0] != trajectory.data.shape[0]:
            raise RuntimeError(f'Not compatible shapes {new_state.shape} != {trajectory.data.shape}!')
        if new_state.shape[-1] != trajectory.data.shape[-1]:
            raise RuntimeError(f'Not compatible shapes {new_state.shape} != {trajectory.data.shape}!')
        return Trajectory(data=torch.cat((trajectory.data, new_state.clone()), dim=1))

def __post_init__(self) -> None:
    """Sanitize attributes of the dataclass."""
    array_dims = self.num_dimensions
    state_size = self.data.shape[-1]
    if array_dims != 2 and array_dims != 3:
        raise RuntimeError(f'Invalid trajectory array. Expected 2 or 3 dims, got {array_dims}.')
    if state_size != self.state_size():
        raise RuntimeError(f'Invalid trajectory array. Expected {self.state_size()} variables per state, got {state_size}.')

@cached_property
def is_valid(self) -> bool:
    """Inherited, see superclass."""
    return len(self.data) > 0 and self.data.shape[-2] > 0 and (self.data.shape[-1] == self.state_size())

def to_device(self, device: torch.device) -> Trajectory:
    """Implemented. See interface."""
    validate_type(self.data, torch.Tensor)
    return Trajectory(data=self.data.to(device=device))

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Trajectory:
    """Implemented. See interface."""
    return Trajectory(data=data['data'])

def unpack(self) -> List[Trajectory]:
    """Implemented. See interface."""
    return [Trajectory(data[None]) for data in self.data]

def extract_number_of_last_states(self, number_of_states: int) -> Trajectory:
    """
        Extract last number_of_states from a trajectory
        :param number_of_states: from last point
        :return: shorter trajectory containing number_of_states from end of trajectory
        @raise in case number_of_states is not within valid range: 0 < number_of_states <= length
        """
    assert number_of_states > 0, f'number_of_states has to be > 0, {number_of_states} > 0!'
    length = self.num_of_iterations
    assert number_of_states <= length, f'number_of_states has to be smaller than length, {number_of_states} <= {length}!'
    return self.extract_trajectory_between(length - number_of_states, length)

def extract_trajectory_between(self, start_index: int, end_index: Optional[int]) -> Trajectory:
    """
        Extract partial trajectory based on [start_index, end_index]
        :param start_index: starting index
        :param end_index: ending index
        :return: Trajectory
        @raise in case the desired ranges are not valid
        """
    if not end_index:
        end_index = self.num_of_iterations
    assert 0 <= start_index < self.num_of_iterations, f'Start index is out of bounds! 0 <= {start_index} < {self.num_of_iterations}!'
    assert 0 <= end_index <= self.num_of_iterations, f'Start index is out of bounds! 0 <= {end_index} <= {self.num_of_iterations}!'
    assert start_index < end_index, f'Start Index has to be smaller then end, {start_index} < {end_index}!'
    return Trajectory(data=self.data[..., start_index:end_index, :])

@classmethod
def append_to_trajectory(cls, trajectory: Trajectory, new_state: torch.Tensor) -> Trajectory:
    """
        Extend trajectory with a new state, in this case we require that both trajectory and new_state has dimension
        of 3, that means that they both have batch dimension
        :param trajectory: to be extended
        :param new_state: state with which trajectory should be extended
        :return: extended trajectory
        """
    assert trajectory.num_dimensions == 3, f'Trajectory dimension {trajectory.num_dimensions} != 3!'
    assert len(new_state.shape) == 3, f'New state dimension {new_state.shape} != 3!'
    if new_state.shape[0] != trajectory.data.shape[0]:
        raise RuntimeError(f'Not compatible shapes {new_state.shape} != {trajectory.data.shape}!')
    if new_state.shape[-1] != trajectory.data.shape[-1]:
        raise RuntimeError(f'Not compatible shapes {new_state.shape} != {trajectory.data.shape}!')
    return Trajectory(data=torch.cat((trajectory.data, new_state.clone()), dim=1))

@dataclass
class VectorSetMap(AbstractModelFeature):
    """
    Vector set map data structure, including:
        coords: Dict[str, List[<np.ndarray: num_elements, num_points, 2>]].
            The (x, y) coordinates of each point in a map element across map elements per sample in batch,
                indexed by map feature.
        traffic_light_data: Dict[str, List[<np.ndarray: num_elements, num_points, 4>]].
            One-hot encoding of traffic light status for each point in a map element across map elements per sample
                in batch, indexed by map feature. Same indexing as coords.
            Encoding: green [1, 0, 0, 0] yellow [0, 1, 0, 0], red [0, 0, 1, 0], unknown [0, 0, 0, 1]
        availabilities: Dict[str, List[<np.ndarray: num_elements, num_points>]].
            Boolean indicator of whether feature data (coords as well as traffic light status if it exists for feature)
                is available for point at given index or if it is zero-padded.

    Feature formulation as sets of vectors for each map element similar to that of VectorNet ("VectorNet: Encoding HD
    Maps and Agent Dynamics from Vectorized Representation"), except map elements are encoded as sets of singular x, y
    points instead of start, end point pairs.

    Coords, traffic light status, and availabilities data are each keyed by map feature name, with dimensionality
    (availabilities don't include feature dimension):
    B: number of samples per batch (variable)
    N: number of map elements (fixed for a given map feature)
    P: number of points (fixed for a given map feature)
    F: number of features (2 for coords, 4 for traffic light status)

    Data at the same index represent the same map element/point among coords, traffic_light_data, and availabilities,
    with traffic_light_data only optionally included. For each map feature, the top level List represents number of
    samples per batch. This is a special feature where each batch entry can have a different size. For that reason, the
    features can not be placed to a single tensor, and we batch the feature with a custom `collate` function.
    """
    coords: Dict[str, List[FeatureDataType]]
    traffic_light_data: Dict[str, List[FeatureDataType]]
    availabilities: Dict[str, List[FeatureDataType]]
    _polyline_coord_dim: int = 2
    _traffic_light_status_dim: int = LaneSegmentTrafficLightData.encoding_dim()

    def __post_init__(self) -> None:
        """
        Sanitize attributes of the dataclass.
        :raise RuntimeError if dimensions invalid.
        """
        if not len(self.coords) > 0:
            raise RuntimeError('Coords cannot be empty!')
        if not all([len(coords) > 0 for coords in self.coords.values()]):
            raise RuntimeError('Batch size has to be > 0!')
        self._sanitize_feature_consistency()
        self._sanitize_data_dimensionality()

    def _sanitize_feature_consistency(self) -> None:
        """
        Check data dimensionality consistent across and within map features.
        :raise RuntimeError if dimensions invalid.
        """
        if not all([len(coords) == len(list(self.coords.values())[0]) for coords in self.coords.values()]):
            raise RuntimeError('Batch size inconsistent across features!')
        for feature_name, feature_coords in self.coords.items():
            if feature_name not in self.availabilities:
                raise RuntimeError('No matching feature in coords for availabilities data!')
            feature_avails = self.availabilities[feature_name]
            if len(feature_avails) != len(feature_coords):
                raise RuntimeError(f'Batch size between coords and availabilities data inconsistent! {len(feature_coords)} != {len(feature_avails)}')
            feature_size = self.feature_size(feature_name)
            if feature_size[1] == 0:
                raise RuntimeError('Features cannot be empty!')
            for coords in feature_coords:
                if coords.shape[0:2] != feature_size:
                    raise RuntimeError(f"Coords for {feature_name} feature don't have consistent feature size! {coords.shape[0:2] != feature_size}")
            for avails in feature_avails:
                if avails.shape[0:2] != feature_size:
                    raise RuntimeError(f"Availabilities for {feature_name} feature don't have consistent feature size! {avails.shape[0:2] != feature_size}")
        for feature_name, feature_tl_data in self.traffic_light_data.items():
            if feature_name not in self.coords:
                raise RuntimeError('No matching feature in coords for traffic light data!')
            feature_coords = self.coords[feature_name]
            if len(feature_tl_data) != len(self.coords[feature_name]):
                raise RuntimeError(f'Batch size between coords and traffic light data inconsistent! {len(feature_coords)} != {len(feature_tl_data)}')
            feature_size = self.feature_size(feature_name)
            for tl_data in feature_tl_data:
                if tl_data.shape[0:2] != feature_size:
                    raise RuntimeError(f"Traffic light data for {feature_name} feature don't have consistent feature size! {tl_data.shape[0:2] != feature_size}")

    def _sanitize_data_dimensionality(self) -> None:
        """
        Check data dimensionality as expected.
        :raise RuntimeError if dimensions invalid.
        """
        for feature_coords in self.coords.values():
            for sample in feature_coords:
                if sample.shape[2] != self._polyline_coord_dim:
                    raise RuntimeError('The dimension of coords is not correct!')
        for feature_tl_data in self.traffic_light_data.values():
            for sample in feature_tl_data:
                if sample.shape[2] != self._traffic_light_status_dim:
                    raise RuntimeError('The dimension of traffic light data is not correct!')
        for feature_avails in self.availabilities.values():
            for sample in feature_avails:
                if len(sample.shape) != 2:
                    raise RuntimeError('The dimension of availabilities is not correct!')

    @cached_property
    def is_valid(self) -> bool:
        """Inherited, see superclass."""
        return all([len(feature_coords) > 0 for feature_coords in self.coords.values()]) and all([feature_coords[0].shape[0] > 0 for feature_coords in self.coords.values()]) and all([feature_coords[0].shape[1] > 0 for feature_coords in self.coords.values()]) and all([len(feature_tl_data) > 0 for feature_tl_data in self.traffic_light_data.values()]) and all([feature_tl_data[0].shape[0] > 0 for feature_tl_data in self.traffic_light_data.values()]) and all([feature_tl_data[0].shape[1] > 0 for feature_tl_data in self.traffic_light_data.values()]) and all([len(features_avails) > 0 for features_avails in self.availabilities.values()]) and all([features_avails[0].shape[0] > 0 for features_avails in self.availabilities.values()]) and all([features_avails[0].shape[1] > 0 for features_avails in self.availabilities.values()])

    @property
    def batch_size(self) -> int:
        """
        Batch size across features.
        :return: number of batches.
        """
        return len(list(self.coords.values())[0])

    def feature_size(self, feature_name: str) -> Tuple[int, int]:
        """
        Number of map elements for given feature, points per element.
        :param feature_name: name of map feature to access.
        :return: [num_elements, num_points]
        :raise: RuntimeError if empty feature.
        """
        map_feature = self.coords[feature_name][0]
        if map_feature.size == 0:
            raise RuntimeError('Feature is empty!')
        return (map_feature.shape[0], map_feature.shape[1])

    @classmethod
    def coord_dim(cls) -> int:
        """
        Coords dimensionality, should be 2 (x, y).
        :return: dimension of coords.
        """
        return cls._polyline_coord_dim

    @classmethod
    def traffic_light_status_dim(cls) -> int:
        """
        Traffic light status dimensionality, should be 4.
        :return: dimension of traffic light status.
        """
        return cls._traffic_light_status_dim

    def get_lane_coords(self, sample_idx: int) -> FeatureDataType:
        """
        Retrieve lane coordinates at given sample index.
        :param sample_idx: the batch index of interest.
        :return: lane coordinate features.
        """
        lane_coords = self.coords[VectorFeatureLayer.LANE.name][sample_idx]
        if lane_coords.size == 0:
            raise RuntimeError('Lane feature is empty!')
        return lane_coords

    @classmethod
    def collate(cls, batch: List[VectorSetMap]) -> VectorSetMap:
        """Implemented. See interface."""
        coords: Dict[str, List[FeatureDataType]] = defaultdict(list)
        traffic_light_data: Dict[str, List[FeatureDataType]] = defaultdict(list)
        availabilities: Dict[str, List[FeatureDataType]] = defaultdict(list)
        for sample in batch:
            for feature_name, feature_coords in sample.coords.items():
                coords[feature_name] += feature_coords
            for feature_name, feature_tl_data in sample.traffic_light_data.items():
                traffic_light_data[feature_name] += feature_tl_data
            for feature_name, feature_avails in sample.availabilities.items():
                availabilities[feature_name] += feature_avails
        return VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)

    def to_feature_tensor(self) -> VectorSetMap:
        """Implemented. See interface."""
        return VectorSetMap(coords={feature_name: [to_tensor(sample).contiguous() for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data={feature_name: [to_tensor(sample).contiguous() for sample in feature_tl_data] for feature_name, feature_tl_data in self.traffic_light_data.items()}, availabilities={feature_name: [to_tensor(sample).contiguous() for sample in feature_avails] for feature_name, feature_avails in self.availabilities.items()})

    def to_device(self, device: torch.device) -> VectorSetMap:
        """Implemented. See interface."""
        return VectorSetMap(coords={feature_name: [sample.to(device=device) for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data={feature_name: [sample.to(device=device) for sample in feature_tl_data] for feature_name, feature_tl_data in self.traffic_light_data.items()}, availabilities={feature_name: [sample.to(device=device) for sample in feature_avails] for feature_name, feature_avails in self.availabilities.items()})

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> VectorSetMap:
        """Implemented. See interface."""
        return VectorSetMap(coords=data['coords'], traffic_light_data=data['traffic_light_data'], availabilities=data['availabilities'])

    def unpack(self) -> List[VectorSetMap]:
        """Implemented. See interface."""
        return [VectorSetMap({feature_name: [feature_coords[sample_idx]] for feature_name, feature_coords in self.coords.items()}, {feature_name: [feature_tl_data[sample_idx]] for feature_name, feature_tl_data in self.traffic_light_data.items()}, {feature_name: [feature_avails[sample_idx]] for feature_name, feature_avails in self.availabilities.items()}) for sample_idx in range(self.batch_size)]

    def rotate(self, quaternion: Quaternion) -> VectorSetMap:
        """
        Rotate the vector set map.
        :param quaternion: Rotation to apply.
        :return rotated VectorSetMap.
        """
        for feature_coords in self.coords.values():
            for sample in feature_coords:
                validate_type(sample, np.ndarray)
        return VectorSetMap(coords={feature_name: [rotate_coords(sample, quaternion) for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

    def translate(self, translation_value: FeatureDataType) -> VectorSetMap:
        """
        Translate the vector set map.
        :param translation_value: Translation in x, y, z.
        :return translated VectorSetMap.
        :raise ValueError if translation_value dimensions invalid.
        """
        if translation_value.size != 3:
            raise ValueError(f'Translation value has incorrect dimensions: {translation_value.size}! Expected: 3 (x, y, z)')
        are_the_same_type(translation_value, list(self.coords.values())[0])
        return VectorSetMap(coords={feature_name: [translate_coords(sample_coords, translation_value, sample_avails) for sample_coords, sample_avails in zip(self.coords[feature_name], self.availabilities[feature_name])] for feature_name in self.coords}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

    def scale(self, scale_value: FeatureDataType) -> VectorSetMap:
        """
        Scale the vector set map.
        :param scale_value: <np.float: 3,>. Scale in x, y, z.
        :return scaled VectorSetMap.
        :raise ValueError if scale_value dimensions invalid.
        """
        if scale_value.size != 3:
            raise ValueError(f'Scale value has incorrect dimensions: {scale_value.size}! Expected: 3 (x, y, z)')
        are_the_same_type(scale_value, list(self.coords.values())[0])
        return VectorSetMap(coords={feature_name: [scale_coords(sample, scale_value) for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

    def xflip(self) -> VectorSetMap:
        """
        Flip the vector set map along the X-axis.
        :return flipped VectorSetMap.
        """
        return VectorSetMap(coords={feature_name: [xflip_coords(sample) for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

    def yflip(self) -> VectorSetMap:
        """
        Flip the vector set map along the Y-axis.
        :return flipped VectorSetMap.
        """
        return VectorSetMap(coords={feature_name: [yflip_coords(sample) for sample in feature_coords] for feature_name, feature_coords in self.coords.items()}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

def translate(self, translation_value: FeatureDataType) -> VectorSetMap:
    """
        Translate the vector set map.
        :param translation_value: Translation in x, y, z.
        :return translated VectorSetMap.
        :raise ValueError if translation_value dimensions invalid.
        """
    if translation_value.size != 3:
        raise ValueError(f'Translation value has incorrect dimensions: {translation_value.size}! Expected: 3 (x, y, z)')
    are_the_same_type(translation_value, list(self.coords.values())[0])
    return VectorSetMap(coords={feature_name: [translate_coords(sample_coords, translation_value, sample_avails) for sample_coords, sample_avails in zip(self.coords[feature_name], self.availabilities[feature_name])] for feature_name in self.coords}, traffic_light_data=self.traffic_light_data, availabilities=self.availabilities)

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

class TestAgents(unittest.TestCase):
    """Test agent feature representation."""

    def setUp(self) -> None:
        """Set up test case."""
        self.ego: List[npt.NDArray[np.float32]] = [np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))]
        self.ego_incorrect: List[npt.NDArray[np.float32]] = [np.array([0.0, 0.0, 0.0])]
        self.agents: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])]
        self.agents_incorrect: List[npt.NDArray[np.float32]] = [np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])]

    def test_agent_feature(self) -> None:
        """
        Test the core functionality of features
        """
        feature = Agents(ego=self.ego, agents=self.agents)
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], np.ndarray)
        self.assertIsInstance(feature.agents[0], np.ndarray)
        self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), np.ndarray)
        self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (2, feature.agents_features_dim))
        feature = feature.to_feature_tensor()
        self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), torch.Tensor)
        self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (2, feature.agents_features_dim))
        self.assertIsInstance(feature.ego[0], torch.Tensor)
        self.assertIsInstance(feature.agents[0], torch.Tensor)

    def test_no_agents(self) -> None:
        """
        Test when there are no agents
        """
        agents: List[npt.NDArray[np.float32]] = [np.empty((self.ego[0].shape[0], 0, 8), dtype=np.float32)]
        feature = Agents(ego=self.ego, agents=agents)
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], np.ndarray)
        self.assertIsInstance(feature.agents[0], np.ndarray)
        self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), np.ndarray)
        self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (0, feature.agents_features_dim))
        feature = feature.to_feature_tensor()
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], torch.Tensor)
        self.assertIsInstance(feature.agents[0], torch.Tensor)
        self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), torch.Tensor)
        self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (0, feature.agents_features_dim))

    def test_incorrect_dimension(self) -> None:
        """
        Test when inputs dimension are incorrect
        """
        with self.assertRaises(AssertionError):
            Agents(ego=self.ego, agents=self.agents_incorrect)
        with self.assertRaises(AssertionError):
            Agents(ego=self.ego_incorrect, agents=self.agents)
        agents: List[npt.NDArray[np.float32]] = [np.empty((self.ego[0].shape[0] + 1, 0, 8), dtype=np.float32)]
        with self.assertRaises(AssertionError):
            Agents(ego=self.ego, agents=agents)
        ego = copy.copy(self.ego)
        ego.append(np.zeros((self.ego[0].shape[0] + 1, self.ego[0].shape[1]), dtype=np.float32))
        with self.assertRaises(AssertionError):
            Agents(ego=ego, agents=self.agents)
        with self.assertRaises(AssertionError):
            Agents(ego=ego, agents=agents)

def test_agent_feature(self) -> None:
    """
        Test the core functionality of features
        """
    feature = Agents(ego=self.ego, agents=self.agents)
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], np.ndarray)
    self.assertIsInstance(feature.agents[0], np.ndarray)
    self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), np.ndarray)
    self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (2, feature.agents_features_dim))
    feature = feature.to_feature_tensor()
    self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), torch.Tensor)
    self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (2, feature.agents_features_dim))
    self.assertIsInstance(feature.ego[0], torch.Tensor)
    self.assertIsInstance(feature.agents[0], torch.Tensor)

def test_no_agents(self) -> None:
    """
        Test when there are no agents
        """
    agents: List[npt.NDArray[np.float32]] = [np.empty((self.ego[0].shape[0], 0, 8), dtype=np.float32)]
    feature = Agents(ego=self.ego, agents=agents)
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], np.ndarray)
    self.assertIsInstance(feature.agents[0], np.ndarray)
    self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), np.ndarray)
    self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (0, feature.agents_features_dim))
    feature = feature.to_feature_tensor()
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(Agents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], torch.Tensor)
    self.assertIsInstance(feature.agents[0], torch.Tensor)
    self.assertIsInstance(feature.get_flatten_agents_features_in_sample(0), torch.Tensor)
    self.assertEqual(feature.get_flatten_agents_features_in_sample(0).shape, (0, feature.agents_features_dim))

def test_incorrect_dimension(self) -> None:
    """
        Test when inputs dimension are incorrect
        """
    with self.assertRaises(AssertionError):
        Agents(ego=self.ego, agents=self.agents_incorrect)
    with self.assertRaises(AssertionError):
        Agents(ego=self.ego_incorrect, agents=self.agents)
    agents: List[npt.NDArray[np.float32]] = [np.empty((self.ego[0].shape[0] + 1, 0, 8), dtype=np.float32)]
    with self.assertRaises(AssertionError):
        Agents(ego=self.ego, agents=agents)
    ego = copy.copy(self.ego)
    ego.append(np.zeros((self.ego[0].shape[0] + 1, self.ego[0].shape[1]), dtype=np.float32))
    with self.assertRaises(AssertionError):
        Agents(ego=ego, agents=self.agents)
    with self.assertRaises(AssertionError):
        Agents(ego=ego, agents=agents)

class TestVectorUtils(unittest.TestCase):
    """Test vector-based feature utility functions."""

    def setUp(self) -> None:
        """Set up test case."""
        self.coords: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, 1.0], [1.0, 1.0]], [[1.0, 0.0], [-1.0, -1.0], [1.0, -1.0]]])
        self.avails: npt.NDArray[np.bool_] = np.array([[False, True, True], [True, True, True]])

    def test_rotate_coords(self) -> None:
        """
        Test vector feature coordinate rotation.
        """
        quaternion = Quaternion(axis=[1, 0, 0], angle=3.14159265)
        expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, -1.0], [1.0, -1.0]], [[1.0, 0.0], [-1.0, 1.0], [1.0, 1.0]]])
        result = rotate_coords(self.coords, quaternion)
        np.testing.assert_allclose(expected_result, result)

    def test_translate_coords(self) -> None:
        """
        Test vector feature coordinate translation.
        """
        translation_value: npt.NDArray[np.float32] = np.array([1.0, 0.0, -1.0])
        expected_result: npt.NDArray[np.float32] = np.array([[[1.0, 0.0], [0.0, 1.0], [2.0, 1.0]], [[2.0, 0.0], [0.0, -1.0], [2.0, -1.0]]])
        result = translate_coords(self.coords, translation_value)
        np.testing.assert_allclose(expected_result, result)
        result = translate_coords(self.coords, translation_value, self.avails)
        expected_result[0][0] = [0.0, 0.0]
        np.testing.assert_allclose(expected_result, result)
        result = translate_coords(torch.from_numpy(self.coords), torch.from_numpy(translation_value), torch.from_numpy(self.avails))
        torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

    def test_scale_coords(self) -> None:
        """
        Test vector feature coordinate scaling.
        """
        scale_value: npt.NDArray[np.float32] = np.array([-2.0, 0.0, -1.0])
        expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [2.0, 0.0], [-2.0, 0.0]], [[-2.0, 0.0], [2.0, 0.0], [-2.0, 0.0]]])
        result = scale_coords(self.coords, scale_value)
        np.testing.assert_allclose(expected_result, result)
        result = scale_coords(torch.from_numpy(self.coords), torch.from_numpy(scale_value))
        torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

    def test_xflip_coords(self) -> None:
        """
        Test flipping vector feature coordinates about X-axis.
        """
        expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [1.0, 1.0], [-1.0, 1.0]], [[-1.0, 0.0], [1.0, -1.0], [-1.0, -1.0]]])
        result = xflip_coords(self.coords)
        np.testing.assert_allclose(expected_result, result)
        result = xflip_coords(torch.from_numpy(self.coords))
        torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

    def test_yflip_coords(self) -> None:
        """
        Test flipping vector feature coordinates about Y-axis.
        """
        expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, -1.0], [1.0, -1.0]], [[1.0, 0.0], [-1.0, 1.0], [1.0, 1.0]]])
        result = yflip_coords(self.coords)
        np.testing.assert_allclose(expected_result, result)
        result = yflip_coords(torch.from_numpy(self.coords))
        torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

def test_rotate_coords(self) -> None:
    """
        Test vector feature coordinate rotation.
        """
    quaternion = Quaternion(axis=[1, 0, 0], angle=3.14159265)
    expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, -1.0], [1.0, -1.0]], [[1.0, 0.0], [-1.0, 1.0], [1.0, 1.0]]])
    result = rotate_coords(self.coords, quaternion)
    np.testing.assert_allclose(expected_result, result)

def test_translate_coords(self) -> None:
    """
        Test vector feature coordinate translation.
        """
    translation_value: npt.NDArray[np.float32] = np.array([1.0, 0.0, -1.0])
    expected_result: npt.NDArray[np.float32] = np.array([[[1.0, 0.0], [0.0, 1.0], [2.0, 1.0]], [[2.0, 0.0], [0.0, -1.0], [2.0, -1.0]]])
    result = translate_coords(self.coords, translation_value)
    np.testing.assert_allclose(expected_result, result)
    result = translate_coords(self.coords, translation_value, self.avails)
    expected_result[0][0] = [0.0, 0.0]
    np.testing.assert_allclose(expected_result, result)
    result = translate_coords(torch.from_numpy(self.coords), torch.from_numpy(translation_value), torch.from_numpy(self.avails))
    torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

def test_scale_coords(self) -> None:
    """
        Test vector feature coordinate scaling.
        """
    scale_value: npt.NDArray[np.float32] = np.array([-2.0, 0.0, -1.0])
    expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [2.0, 0.0], [-2.0, 0.0]], [[-2.0, 0.0], [2.0, 0.0], [-2.0, 0.0]]])
    result = scale_coords(self.coords, scale_value)
    np.testing.assert_allclose(expected_result, result)
    result = scale_coords(torch.from_numpy(self.coords), torch.from_numpy(scale_value))
    torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

def test_xflip_coords(self) -> None:
    """
        Test flipping vector feature coordinates about X-axis.
        """
    expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [1.0, 1.0], [-1.0, 1.0]], [[-1.0, 0.0], [1.0, -1.0], [-1.0, -1.0]]])
    result = xflip_coords(self.coords)
    np.testing.assert_allclose(expected_result, result)
    result = xflip_coords(torch.from_numpy(self.coords))
    torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

def test_yflip_coords(self) -> None:
    """
        Test flipping vector feature coordinates about Y-axis.
        """
    expected_result: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, -1.0], [1.0, -1.0]], [[1.0, 0.0], [-1.0, 1.0], [1.0, 1.0]]])
    result = yflip_coords(self.coords)
    np.testing.assert_allclose(expected_result, result)
    result = yflip_coords(torch.from_numpy(self.coords))
    torch.testing.assert_allclose(torch.from_numpy(expected_result), result)

class TestGenericAgents(unittest.TestCase):
    """Test agent feature representation."""

    def setUp(self) -> None:
        """Set up test case."""
        self.agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE', 'TRAFFIC_CONE', 'BARRIER', 'CZONE_SIGN', 'GENERIC_OBJECT']
        self.ego: List[npt.NDArray[np.float32]] = [np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))]
        self.ego_incorrect: List[npt.NDArray[np.float32]] = [np.array([0.0, 0.0, 0.0])]
        self.agents: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])] for feature_name in self.agent_features}
        self.agents_incorrect: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])] for feature_name in self.agent_features}

    def test_agent_feature(self) -> None:
        """
        Test the core functionality of features
        """
        feature = GenericAgents(ego=self.ego, agents=self.agents)
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], np.ndarray)
        for feature_name in self.agent_features:
            self.assertIsInstance(feature.agents[feature_name][0], np.ndarray)
            self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), np.ndarray)
            self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (2, feature.agents_features_dim))
        feature = feature.to_feature_tensor()
        self.assertIsInstance(feature.ego[0], torch.Tensor)
        for feature_name in self.agent_features:
            self.assertIsInstance(feature.agents[feature_name][0], torch.Tensor)
            self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), torch.Tensor)
            self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (2, feature.agents_features_dim))

    def test_no_agents(self) -> None:
        """
        Test when there are no agents
        """
        agents: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.empty((self.ego[0].shape[0], 0, 8), dtype=np.float32)] for feature_name in self.agent_features}
        feature = GenericAgents(ego=self.ego, agents=agents)
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], np.ndarray)
        for feature_name in self.agent_features:
            self.assertIsInstance(feature.agents[feature_name][0], np.ndarray)
            self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), np.ndarray)
            self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (0, feature.agents_features_dim))
            self.assertEqual(feature.num_agents_in_sample(feature_name, 0), 0)
        feature = feature.to_feature_tensor()
        self.assertEqual(feature.batch_size, 1)
        self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
        self.assertIsInstance(feature.ego[0], torch.Tensor)
        for feature_name in self.agent_features:
            self.assertIsInstance(feature.agents[feature_name][0], torch.Tensor)
            self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), torch.Tensor)
            self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (0, feature.agents_features_dim))
            self.assertEqual(feature.num_agents_in_sample(feature_name, 0), 0)

    def test_incorrect_dimension(self) -> None:
        """
        Test when inputs dimension are incorrect
        """
        with self.assertRaises(AssertionError):
            GenericAgents(ego=self.ego, agents=self.agents_incorrect)
        with self.assertRaises(AssertionError):
            GenericAgents(ego=self.ego_incorrect, agents=self.agents)
        agents: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.empty((self.ego[0].shape[0] + 1, 0, 8), dtype=np.float32)] for feature_name in self.agent_features}
        with self.assertRaises(AssertionError):
            GenericAgents(ego=self.ego, agents=agents)
        ego = copy.copy(self.ego)
        ego.append(np.zeros((self.ego[0].shape[0] + 1, self.ego[0].shape[1]), dtype=np.float32))
        with self.assertRaises(AssertionError):
            GenericAgents(ego=ego, agents=self.agents)
        with self.assertRaises(AssertionError):
            GenericAgents(ego=ego, agents=agents)

def test_agent_feature(self) -> None:
    """
        Test the core functionality of features
        """
    feature = GenericAgents(ego=self.ego, agents=self.agents)
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], np.ndarray)
    for feature_name in self.agent_features:
        self.assertIsInstance(feature.agents[feature_name][0], np.ndarray)
        self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), np.ndarray)
        self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (2, feature.agents_features_dim))
    feature = feature.to_feature_tensor()
    self.assertIsInstance(feature.ego[0], torch.Tensor)
    for feature_name in self.agent_features:
        self.assertIsInstance(feature.agents[feature_name][0], torch.Tensor)
        self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), torch.Tensor)
        self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (2, feature.agents_features_dim))

def test_no_agents(self) -> None:
    """
        Test when there are no agents
        """
    agents: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.empty((self.ego[0].shape[0], 0, 8), dtype=np.float32)] for feature_name in self.agent_features}
    feature = GenericAgents(ego=self.ego, agents=agents)
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], np.ndarray)
    for feature_name in self.agent_features:
        self.assertIsInstance(feature.agents[feature_name][0], np.ndarray)
        self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), np.ndarray)
        self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (0, feature.agents_features_dim))
        self.assertEqual(feature.num_agents_in_sample(feature_name, 0), 0)
    feature = feature.to_feature_tensor()
    self.assertEqual(feature.batch_size, 1)
    self.assertEqual(GenericAgents.collate([feature, feature]).batch_size, 2)
    self.assertIsInstance(feature.ego[0], torch.Tensor)
    for feature_name in self.agent_features:
        self.assertIsInstance(feature.agents[feature_name][0], torch.Tensor)
        self.assertIsInstance(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0), torch.Tensor)
        self.assertEqual(feature.get_flatten_agents_features_by_type_in_sample(feature_name, 0).shape, (0, feature.agents_features_dim))
        self.assertEqual(feature.num_agents_in_sample(feature_name, 0), 0)

class TestTrajectory(unittest.TestCase):
    """Test trajectory target representation."""

    def setUp(self) -> None:
        """Set up test case."""
        self.data = torch.Tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
        self.batched_data = default_collate([self.data, self.data])
        self.batched_trajectory = Trajectory(data=self.batched_data)

    def test_batches(self) -> None:
        """
        Test the number of batches in trajectory
        """
        self.assertEqual(self.batched_trajectory.num_batches, 2)
        self.assertEqual(Trajectory(data=self.data).num_batches, None)

    def test_extend_trajectory(self) -> None:
        """
        Test extending trajectory by a new state
        """
        feature_builder = Trajectory(data=torch.zeros((30, 10, 3)))
        new_state = torch.zeros((30, 3)).unsqueeze(1)
        new_trajectory = Trajectory.append_to_trajectory(feature_builder, new_state)
        self.assertEqual(feature_builder.num_of_iterations + 1, new_trajectory.num_of_iterations)
        self.assertEqual(feature_builder.num_batches, 30)
        self.assertEqual(new_trajectory.num_batches, 30)

    def test_extract_trajectory(self) -> None:
        """
        Test extracting part of a trajectory
        """
        extracted = self.batched_trajectory.extract_trajectory_between(0, 4)
        self.assertEqual(extracted.data.shape, (2, 4, 3))
        self.assertAlmostEqual(extracted.data[0, 0, 0].item(), 0.0)
        self.assertAlmostEqual(extracted.data[0, -1, 0].item(), 3.0)
        state_at = self.batched_trajectory.state_at_index(3)
        state_at = state_at.unsqueeze(1)
        self.assertEqual(state_at.shape, (2, 1, 3))
        self.assertAlmostEqual(state_at[0, 0, 0], 3)

def test_batches(self) -> None:
    """
        Test the number of batches in trajectory
        """
    self.assertEqual(self.batched_trajectory.num_batches, 2)
    self.assertEqual(Trajectory(data=self.data).num_batches, None)

def test_extend_trajectory(self) -> None:
    """
        Test extending trajectory by a new state
        """
    feature_builder = Trajectory(data=torch.zeros((30, 10, 3)))
    new_state = torch.zeros((30, 3)).unsqueeze(1)
    new_trajectory = Trajectory.append_to_trajectory(feature_builder, new_state)
    self.assertEqual(feature_builder.num_of_iterations + 1, new_trajectory.num_of_iterations)
    self.assertEqual(feature_builder.num_batches, 30)
    self.assertEqual(new_trajectory.num_batches, 30)

def test_extract_trajectory(self) -> None:
    """
        Test extracting part of a trajectory
        """
    extracted = self.batched_trajectory.extract_trajectory_between(0, 4)
    self.assertEqual(extracted.data.shape, (2, 4, 3))
    self.assertAlmostEqual(extracted.data[0, 0, 0].item(), 0.0)
    self.assertAlmostEqual(extracted.data[0, -1, 0].item(), 3.0)
    state_at = self.batched_trajectory.state_at_index(3)
    state_at = state_at.unsqueeze(1)
    self.assertEqual(state_at.shape, (2, 1, 3))
    self.assertAlmostEqual(state_at[0, 0, 0], 3)

class TestTrajectories(unittest.TestCase):
    """Test trajectories target representation."""

    def setUp(self) -> None:
        """Set up test case."""
        data = torch.Tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
        trajectory = Trajectory(data=data)
        self.trajectories = Trajectories(trajectories=[trajectory])

    def test_serialize_deserialize(self) -> None:
        """Test that serialization and deserialization work, and the resulting data matches."""
        serialized = self.trajectories.serialize()
        deserialized = Trajectories.deserialize(serialized)
        self.assertTrue(torch.allclose(self.trajectories.trajectories[0].data, deserialized.trajectories[0].data))

def setUp(self) -> None:
    """Set up test case."""
    data = torch.Tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
    trajectory = Trajectory(data=data)
    self.trajectories = Trajectories(trajectories=[trajectory])

class EgoTrajectoryTargetBuilder(AbstractTargetBuilder):
    """Trajectory builders constructed the desired ego's trajectory from a scenario."""

    def __init__(self, future_trajectory_sampling: TrajectorySampling) -> None:
        """
        Initializes the class.
        :param future_trajectory_sampling: parameters for sampled future trajectory
        """
        self._num_future_poses = future_trajectory_sampling.num_poses
        self._time_horizon = future_trajectory_sampling.time_horizon

    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'trajectory'

    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return Trajectory

    def get_targets(self, scenario: AbstractScenario) -> Trajectory:
        """Inherited, see superclass."""
        current_absolute_state = scenario.initial_ego_state
        trajectory_absolute_states = scenario.get_ego_future_trajectory(iteration=0, num_samples=self._num_future_poses, time_horizon=self._time_horizon)
        trajectory_relative_poses = convert_absolute_to_relative_poses(current_absolute_state.rear_axle, [state.rear_axle for state in trajectory_absolute_states])
        if len(trajectory_relative_poses) != self._num_future_poses:
            raise RuntimeError(f'Expected {self._num_future_poses} num poses but got {len(trajectory_relative_poses)}')
        return Trajectory(data=trajectory_relative_poses)

def get_targets(self, scenario: AbstractScenario) -> Trajectory:
    """Inherited, see superclass."""
    current_absolute_state = scenario.initial_ego_state
    trajectory_absolute_states = scenario.get_ego_future_trajectory(iteration=0, num_samples=self._num_future_poses, time_horizon=self._time_horizon)
    trajectory_relative_poses = convert_absolute_to_relative_poses(current_absolute_state.rear_axle, [state.rear_axle for state in trajectory_absolute_states])
    if len(trajectory_relative_poses) != self._num_future_poses:
        raise RuntimeError(f'Expected {self._num_future_poses} num poses but got {len(trajectory_relative_poses)}')
    return Trajectory(data=trajectory_relative_poses)

def compute_traj_errors(ego_traj: Union[List[Point2D], List[StateSE2]], expert_traj: Union[List[Point2D], List[StateSE2]], discount_factor: float=1.0, heading_diff_weight: float=1.0) -> npt.NDArray:
    """
    Compute the errors between the position/position_with_yaw of ego trajectory and expert trajectory
    :param ego_traj: a list of Point2D or StateSE2 that describe ego position/position with yaw
    :param expert_traj: a list of Point2D or StateSE2 that describe expert position/position with yaw
    :param discount_factor: Displacements corresponding to the k^th timestep will
    be discounted by a factor of discount_factor^k., defaults to 1.0
    :param heading_diff_weight: factor to weight heading differences if yaw errors are also
    considered, defaults to 1.0
    :return an array of displacement errors.
    """
    traj_len = len(ego_traj)
    expert_traj_len = len(expert_traj)
    assert traj_len != 0, 'ego_traj should be a nonempty list'
    assert traj_len == expert_traj_len or traj_len == expert_traj_len - 1, 'ego and expert have different trajectory lengths'
    displacements = np.zeros((traj_len, 2))
    for i in range(traj_len):
        displacements[i, :] = [ego_traj[i].x - expert_traj[i].x, ego_traj[i].y - expert_traj[i].y]
    dist_seq = np.hypot(displacements[:, 0], displacements[:, 1])
    if isinstance(ego_traj[0], StateSE2) and isinstance(expert_traj[0], StateSE2) and (heading_diff_weight != 0):
        heading_errors = compute_traj_heading_errors(ego_traj, expert_traj)
        weighted_heading_errors = heading_errors * heading_diff_weight
        dist_seq = dist_seq + weighted_heading_errors
    if discount_factor != 1:
        discount_weights = get_discount_weights(discount_factor=discount_factor, traj_len=traj_len)
        dist_seq = np.multiply(dist_seq, discount_weights)
    return dist_seq

def create_scenario_from_paths(paths: List[Path]) -> List[AbstractScenario]:
    """
    Create scenario objects from a list of cache paths in the format of ".../log_name/scenario_token".
    :param paths: List of paths to load scenarios from.
    :return: List of created scenarios.
    """
    scenarios = [CachedScenario(log_name=path.parent.parent.name, token=path.name, scenario_type=path.parent.name) for path in paths]
    return scenarios

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

def mock_expand_s3_dir(cache_path: str) -> List[str]:
    """
            Mock function for expand_s3_dir.
            :param cache_path: S3 cache path.
            :return: List of mock s3 file paths fetched directly from s3 cache path provided.
            """
    return [f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin' for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]

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

def _get_mock_scenario_dict(self) -> Dict[str, List[CachedScenario]]:
    """Gets mock scenario dict."""
    return {DEFAULT_SCENARIO_NAME: [CachedScenario(log_name='log/name', token=DEFAULT_SCENARIO_NAME, scenario_type=DEFAULT_SCENARIO_NAME) for i in range(500)], 'lane_following_with_lead': [CachedScenario(log_name='log/name', token='lane_following_with_lead', scenario_type='lane_following_with_lead') for i in range(80)], 'unprotected_left_turn': [CachedScenario(log_name='log/name', token='unprotected_left_turn', scenario_type='unprotected_left_turn') for i in range(120)]}

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

def _make_cached_scenario(self) -> CachedScenario:
    return CachedScenario(log_name='log/name', token='token', scenario_type='type')

def proto_traj_from_inter_traj(trajectory: AbstractTrajectory) -> chpb.Trajectory:
    """
    Serializes AbstractTrajectory to a Trajectory message
    :param trajectory: The AbstractTrajectory object
    :return: The corresponding Trajectory message
    """
    return chpb.Trajectory(ego_states=[proto_ego_state_from_ego_state(state) for state in trajectory.get_sampled_trajectory()])

