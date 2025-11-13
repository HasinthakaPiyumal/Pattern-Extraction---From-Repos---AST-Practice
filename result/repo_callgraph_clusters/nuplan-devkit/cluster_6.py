# Cluster 6

def get_default_scenario_extraction(scenario_duration: float=15.0, extraction_offset: float=-2.0, subsample_ratio: float=0.5) -> ScenarioExtractionInfo:
    """
    Get default scenario extraction instructions used in visualization.
    :param scenario_duration: [s] Duration of scenario.
    :param extraction_offset: [s] Offset of scenario (e.g. -2 means start scenario 2s before it starts).
    :param subsample_ratio: Scenario resolution.
    :return: Scenario extraction info object.
    """
    return ScenarioExtractionInfo(DEFAULT_SCENARIO_NAME, scenario_duration, extraction_offset, subsample_ratio)

def get_default_scenario_from_token(data_root: str, log_file_full_path: str, token: str, map_root: str, map_version: str) -> NuPlanScenario:
    """
    Build a scenario with default parameters for visualization.
    :param data_root: The root directory to use for looking for db files.
    :param log_file_full_path: The full path to the log db file to use.
    :param token: Lidar pc token to be used as anchor for the scenario.
    :param map_root: The root directory to use for looking for maps.
    :param map_version: The map version to use.
    :return: Instantiated scenario object.
    """
    timestamp = get_sensor_data_token_timestamp_from_db(log_file_full_path, get_lidarpc_sensor_data(), token)
    map_name = get_sensor_token_map_name_from_db(log_file_full_path, get_lidarpc_sensor_data(), token)
    return NuPlanScenario(data_root=data_root, log_file_load_path=log_file_full_path, initial_lidar_token=token, initial_lidar_timestamp=timestamp, scenario_type=DEFAULT_SCENARIO_NAME, map_root=map_root, map_version=map_version, map_name=map_name, scenario_extraction_info=get_default_scenario_extraction(), ego_vehicle_parameters=get_pacifica_parameters())

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

def fxn(actual_data_root: str, actual_remote_path: str) -> str:
    """
            The patch for ensure_file_downloaded.
            """
    self.assertEqual(expected_data_root, actual_data_root)
    self.assertEqual(expected_remote_path, actual_remote_path)
    return actual_remote_path

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

class LidarBox(Base):
    """
    Lidar box from tracker.
    """
    __tablename__ = 'lidar_box'
    token: str = Column(sql_types.HexLen8, primary_key=True)
    lidar_pc_token: str = Column(sql_types.HexLen8, ForeignKey('lidar_pc.token'), nullable=False)
    track_token: str = Column(sql_types.HexLen8, ForeignKey('track.token'))
    next_token = Column(sql_types.HexLen8, ForeignKey('lidar_box.token'), nullable=True)
    prev_token = Column(sql_types.HexLen8, ForeignKey('lidar_box.token'), nullable=True)
    x: float = Column(Float)
    y: float = Column(Float)
    z: float = Column(Float)
    width: float = Column(Float)
    length: float = Column(Float)
    height: float = Column(Float)
    vx: float = Column(Float)
    vy: float = Column(Float)
    vz: float = Column(Float)
    yaw: float = Column(Float)
    confidence: float = Column(Float)
    next = relationship('LidarBox', foreign_keys=[next_token], remote_side=[token])
    prev = relationship('LidarBox', foreign_keys=[prev_token], remote_side=[token])

    @property
    def _session(self) -> Any:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return inspect(self).session

    def __iter__(self) -> IterableLidarBox:
        """
        Returns a iterator object for LidarBox.
        :return: The iterator object.
        """
        return IterableLidarBox(self)

    def __reversed__(self) -> IterableLidarBox:
        """
        Returns a iterator object for LidarBox that traverses in reverse.
        :return: The iterator object.
        """
        return IterableLidarBox(self, reverse=True)

    def __repr__(self) -> str:
        """
        Return the string representation.
        :return: The string representation.
        """
        desc: str = simple_repr(self)
        return desc

    @property
    def log(self) -> Log:
        """
        Returns the Log containing the LidarBox.
        :return: The log containing the lidar box.
        """
        return self.lidar_pc.log

    @property
    def category(self) -> Category:
        """
        Returns the Category of the LidarBox.
        :return: The category of the lidar box.
        """
        return self.track.category

    @property
    def timestamp(self) -> int:
        """
        Returns the timestamp of the LidarBox.
        :return: The timestamp of the lidar box.
        """
        return int(self.lidar_pc.timestamp)

    @property
    def distance_to_ego(self) -> float:
        """
        Returns the distance of detection from Ego Vehicle.
        :return: The distance to ego vehicle.
        """
        return float(np.sqrt((self.x - self.lidar_pc.ego_pose.x) ** 2 + (self.y - self.lidar_pc.ego_pose.y) ** 2))

    @property
    def size(self) -> List[float]:
        """
        Get the box size.
        :return: The box size.
        """
        return [self.width, self.length, self.height]

    @property
    def translation(self) -> List[float]:
        """
        Get the box location.
        :return: The box location.
        """
        return [self.x, self.y, self.z]

    @property
    def rotation(self) -> List[float]:
        """
        Get the box rotation in euler angles.
        :return: The box rotation in euler angles.
        """
        qx = Quaternion(axis=(1, 0, 0), radians=0.0)
        qy = Quaternion(axis=(0, 1, 0), radians=0.0)
        qz = Quaternion(axis=(0, 0, 1), radians=self.yaw)
        return list(qx * qy * qz)

    @property
    def quaternion(self) -> Quaternion:
        """
        Get the box rotation in quaternion.
        :return: The box rotation in quaternion.
        """
        return Quaternion(self.rotation)

    @property
    def translation_np(self) -> npt.NDArray[np.float64]:
        """
        Get the box translation in numpy.
        :return: <np.float: 3> Translation.
        """
        return np.array(self.translation)

    @property
    def size_np(self) -> npt.NDArray[np.float64]:
        """
        Get the box size in numpy.
        :return: <np.float, 3> Width, length and height.
        """
        return np.array(self.size)

    @cached(cache=LRUCache(maxsize=LIDAR_BOX_LRU_CACHE_SIZE), key=lambda self: hashkey(self.track_token))
    def _get_box_items(self) -> Tuple[List[Integer], List[LidarBox]]:
        """
        Get all boxes along the track.
        :return: The list of timestamps and boxes along the track.
        """
        box_list: List[LidarBox] = self._session.query(LidarBox).filter(LidarBox.track_token == self.track_token).all()
        sorted_box_list = sorted(box_list, key=lambda x: x.timestamp)
        return ([b.timestamp for b in sorted_box_list], sorted_box_list)

    @cached(cache=LRUCache(maxsize=LIDAR_BOX_LRU_CACHE_SIZE), key=lambda self: hashkey(self.track_token))
    def get_box_items_to_iterate(self) -> Dict[int, Tuple[Optional[LidarBox], Optional[LidarBox]]]:
        """
        Get all boxes along the track.
        :return: Dict. Key is timestamp of box, value is Tuple of (prev,next) LidarBox.
        """
        box_list = self._session.query(LidarBox).filter(LidarBox.track_token == self.track_token).all()
        sorted_box_list = sorted(box_list, key=lambda x: x.timestamp)
        return {box.timestamp: (prev, next) for box, prev, next in zip(sorted_box_list, [None] + sorted_box_list[:-1], sorted_box_list[1:] + [None])}

    def _find_box(self, step: int=0) -> Optional[LidarBox]:
        """
        Find the next box along the track with the given step.
        :param: step: The number of steps to look ahead, defaults to zero.
        :return: The found box if any.
        """
        timestamp_list, sorted_box_list = self._get_box_items()
        i = bisect.bisect_left(timestamp_list, self.timestamp)
        j = i + step
        if j < 0 or j >= len(sorted_box_list):
            return None
        return sorted_box_list[j]

    def future_or_past_ego_poses(self, number: int, mode: str, direction: str) -> List[EgoPose]:
        """
        Get n future or past vehicle poses. Note here the frequency of pose differs from frequency of LidarBox.
        :param number: Number of poses to fetch or number of seconds of ego poses to fetch.
        :param mode: Either n_poses or n_seconds.
        :param direction: Future or past ego poses to fetch, could be 'prev' or 'next'.
        :return: List of up to n or n seconds future or past ego poses.
        """
        if direction == 'prev':
            if mode == 'n_poses':
                return self._session.query(EgoPose).filter(EgoPose.timestamp < self.lidar_pc.ego_pose.timestamp, self.lidar_pc.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).limit(number).all()
            elif mode == 'n_seconds':
                return self._session.query(EgoPose).filter(EgoPose.timestamp - self.lidar_pc.ego_pose.timestamp < 0, EgoPose.timestamp - self.lidar_pc.ego_pose.timestamp >= -number * 1000000.0, self.lidar_pc.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).all()
            else:
                raise ValueError(f'Unknown mode: {mode}.')
        elif direction == 'next':
            if mode == 'n_poses':
                return self._session.query(EgoPose).filter(EgoPose.timestamp > self.lidar_pc.ego_pose.timestamp, self.lidar_pc.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).limit(number).all()
            elif mode == 'n_seconds':
                return self._session.query(EgoPose).filter(EgoPose.timestamp - self.lidar_pc.ego_pose.timestamp > 0, EgoPose.timestamp - self.lidar_pc.ego_pose.timestamp <= number * 1000000.0, self.lidar_pc.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).all()
            else:
                raise ValueError(f'Unknown mode: {mode}.')
        else:
            raise ValueError(f'Unknown direction: {direction}.')

    def _temporal_neighbors(self) -> Tuple[LidarBox, LidarBox, bool, bool]:
        """
        Find temporal neighbors to calculate velocity and angular velocity.
        :return: The previous box, next box and their existences. If the previous or next box do not exist, they will
            be set to the current box itself.
        """
        has_prev = self.prev is not None
        has_next = self.next is not None
        if has_prev:
            prev_lidar_box = self.prev
        else:
            prev_lidar_box = self
        if has_next:
            next_lidar_box = self.next
        else:
            next_lidar_box = self
        return (prev_lidar_box, next_lidar_box, has_prev, has_next)

    @property
    def velocity(self) -> npt.NDArray[np.float64]:
        """
        Estimate box velocity for a box.
        :return: The estimated box velocity of the box.
        """
        max_time_diff = 1.5
        prev_lidar_box, next_lidar_box, has_prev, has_next = self._temporal_neighbors()
        if not has_prev and (not has_next):
            return np.array([np.nan, np.nan, np.nan])
        pos_next: npt.NDArray[np.float64] = np.array(next_lidar_box.translation)
        pos_prev: npt.NDArray[np.float64] = np.array(prev_lidar_box.translation)
        pos_diff: npt.NDArray[np.float64] = pos_next - pos_prev
        pos_diff[2] = 0
        time_next = 1e-06 * next_lidar_box.timestamp
        time_prev = 1e-06 * prev_lidar_box.timestamp
        time_diff = time_next - time_prev
        if has_next and has_prev:
            max_time_diff *= 2
        if time_diff > max_time_diff:
            return np.array([np.nan, np.nan, np.nan])
        else:
            return pos_diff / time_diff

    @property
    def angular_velocity(self) -> float:
        """
        Estimate box angular velocity for a box.
        :return: The estimated box angular velocity of the box.
        """
        max_time_diff = 1.5
        prev_lidar_box, next_lidar_box, has_prev, has_next = self._temporal_neighbors()
        if not has_prev and (not has_next):
            return np.nan
        time_next = 1e-06 * next_lidar_box.timestamp
        time_prev = 1e-06 * prev_lidar_box.timestamp
        time_diff = time_next - time_prev
        if has_next and has_prev:
            max_time_diff *= 2
        if time_diff > max_time_diff:
            return np.nan
        else:
            yaw_diff = next_lidar_box.yaw - prev_lidar_box.yaw
            if yaw_diff > np.pi:
                yaw_diff -= 2 * np.pi
            elif yaw_diff < -np.pi:
                yaw_diff += 2 * np.pi
            return float(yaw_diff / time_diff)

    def box(self) -> Box3D:
        """
        Get the Box3D representation of the box.
        :return: The box3d representation of the box.
        """
        label_local = raw_mapping['global2local'][self.category.name]
        label_int = raw_mapping['local2id'][label_local]
        return Box3D(center=self.translation, size=self.size, orientation=self.quaternion, token=self.token, label=label_int, track_token=self.track_token)

    def tracked_object(self, future_waypoints: Optional[List[Waypoint]]) -> TrackedObject:
        """
        Creates an Agent object
        :param future_waypoints: Optional future poses, which will be used as predicted trajectory
        """
        pose = StateSE2(self.translation[0], self.translation[1], self.yaw)
        oriented_box = OrientedBox(pose, width=self.size[0], length=self.size[1], height=self.size[2])
        label_local = raw_mapping['global2local'][self.category.name]
        tracked_object_type = TrackedObjectType[local2agent_type[label_local]]
        if tracked_object_type in AGENT_TYPES:
            return Agent(tracked_object_type=tracked_object_type, oriented_box=oriented_box, velocity=StateVector2D(self.vx, self.vy), predictions=[PredictedTrajectory(1.0, future_waypoints)] if future_waypoints else [], angular_velocity=np.nan, metadata=SceneObjectMetadata(token=self.token, track_token=self.track_token, track_id=None, timestamp_us=self.timestamp, category_name=self.category.name))
        else:
            return StaticObject(tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=SceneObjectMetadata(token=self.token, track_token=self.track_token, track_id=None, timestamp_us=self.timestamp, category_name=self.category.name))

def __iter__(self) -> IterableLidarBox:
    """
        Returns a iterator object for LidarBox.
        :return: The iterator object.
        """
    return IterableLidarBox(self)

def __reversed__(self) -> IterableLidarBox:
    """
        Returns a iterator object for LidarBox that traverses in reverse.
        :return: The iterator object.
        """
    return IterableLidarBox(self, reverse=True)

def get_interpolated_waypoints(lidar_pc: LidarPc, future_trajectory_sampling: TrajectorySampling) -> Dict[str, List[Waypoint]]:
    """
    Gets the interpolated future waypoints for the agents detected in the given LidarPC. The sampling is determined
    by the horizon length and the sampling time.
    :param lidar_pc: The starting lidar pc
    :param future_trajectory_sampling: Sampling parameters for future predictions
    :return: A dict containing interpolated waypoints for each agent track_token, empty if no waypoint available
    """
    horizon_end = lidar_pc.timestamp + int(future_trajectory_sampling.time_horizon * 1000000.0)
    future_waypoints = {box.track_token: get_waypoints_for_agent(box, horizon_end) for box in lidar_pc.lidar_boxes}
    agents_interpolated_waypoints = {}
    for track_token, waypoints in future_waypoints.items():
        if len(waypoints) >= 2:
            interpolated = interpolate_waypoints(waypoints, future_trajectory_sampling)
            agents_interpolated_waypoints[track_token] = interpolated if len(interpolated) > 1 else []
        else:
            agents_interpolated_waypoints[track_token] = []
    return agents_interpolated_waypoints

class Image(Base):
    """
    An image.
    """
    __tablename__ = 'image'
    token = Column(sql_types.HexLen8, primary_key=True)
    next_token = Column(sql_types.HexLen8, ForeignKey('image.token'), nullable=True)
    prev_token = Column(sql_types.HexLen8, ForeignKey('image.token'), nullable=True)
    ego_pose_token = Column(sql_types.HexLen8, ForeignKey('ego_pose.token'), nullable=False)
    camera_token = Column(sql_types.HexLen8, ForeignKey('camera.token'), nullable=False)
    filename_jpg = Column(String(128))
    timestamp = Column(Integer)
    next = relationship('Image', foreign_keys=[next_token], remote_side=[token])
    prev = relationship('Image', foreign_keys=[prev_token], remote_side=[token])
    camera = relationship('Camera', foreign_keys=[camera_token], back_populates='images')
    ego_pose = relationship('EgoPose', foreign_keys=[ego_pose_token], back_populates='image')

    @property
    def _session(self) -> Any:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return inspect(self).session

    def __repr__(self) -> str:
        """
        Return the string representation.
        :return: The string representation.
        """
        desc: str = simple_repr(self)
        return desc

    @property
    def log(self) -> Log:
        """
        Returns the Log containing the image.
        :return: The log containing this image.
        """
        return self.camera.log

    @property
    def lidar_pc(self) -> LidarPc:
        """
        Get the closest LidarPc by timestamp
        :return: LidarPc closest to the Image by time
        """
        lidar_pc = self._session.query(LidarPc).order_by(func.abs(LidarPc.timestamp - self.timestamp)).first()
        return lidar_pc

    @property
    def scene(self) -> Scene:
        """
        Get the corresponding scene by finding the closest LidarPc by timestamp.
        :return: Scene corresponding to the Image.
        """
        return self.lidar_pc.scene

    @property
    def lidar_boxes(self) -> LidarBox:
        """
        Get the list of boxes associated with this Image, based on closest LidarPc
        :return: List of boxes associated with this Image
        """
        return self.lidar_pc.lidar_boxes

    def load_as(self, db: NuPlanDB, img_type: str) -> Any:
        """
        Loads the image as a desired type.
        :param db: Log Database.
        :param img_type: Can be either 'pil' or 'np' or 'cv2'. If the img_type is cv2, the image is returned in BGR
            format, otherwise it is returned in RGB format.
        :return: The image.
        """
        assert img_type in ['pil', 'cv2', 'np'], f'Expected img_type to be pil, cv2 or np. Received {img_type}'
        pil_img = PIL.Image.open(self.load_bytes_jpg(db))
        if img_type == 'pil':
            return pil_img
        elif img_type == 'np':
            return np.array(pil_img)
        else:
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    @property
    def filename(self) -> str:
        """
        Get the file name.
        :return: The file name.
        """
        return self.filename_jpg

    def load_bytes_jpg(self, db: NuPlanDB) -> BinaryIO:
        """
        Returns the bytes of the jpg data for this image.
        :param db: Log Database.
        :return: The image bytes.
        """
        blob: BinaryIO = db.load_blob(osp.join('sensor_blobs', self.filename))
        return blob

    def path(self, db: NuPlanDB) -> str:
        """
        Get the path to image file.
        :param db: Log Database.
        :return: The image file path.
        """
        return osp.join(db.data_root, self.filename)

    def boxes(self, frame: Frame=Frame.GLOBAL) -> List[Box3D]:
        """
        Loads all boxes associated with this Image record. Boxes are returned in the global frame by default.
        :param frame: Specify the frame in which the boxes will be returned.
        :return: List of boxes.
        """
        boxes: List[Box3D] = get_boxes(self, frame, self.ego_pose.trans_matrix_inv, self.camera.trans_matrix_inv)
        return boxes

    def future_or_past_ego_poses(self, number: int, mode: str, direction: str) -> List[EgoPose]:
        """
        Get n future or past vehicle poses. Note here the frequency of pose differs from frequency of Image.
        :param number: Number of poses to fetch or number of seconds of ego poses to fetch.
        :param mode: Either n_poses or n_seconds.
        :param direction: Future or past ego poses to fetch, could be 'prev' or 'next'.
        :return: List of up to n or n seconds future or past ego poses.
        """
        ego_poses: List[EgoPose]
        if direction == 'prev':
            if mode == 'n_poses':
                ego_poses = self._session.query(EgoPose).filter(EgoPose.timestamp < self.ego_pose.timestamp, self.camera.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).limit(number).all()
                return ego_poses
            elif mode == 'n_seconds':
                ego_poses = self._session.query(EgoPose).filter(EgoPose.timestamp - self.ego_pose.timestamp < 0, EgoPose.timestamp - self.ego_pose.timestamp >= -number * 1000000.0, self.camera.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).all()
                return ego_poses
            else:
                raise NotImplementedError('Only n_poses and n_seconds two modes are supported for now!')
        elif direction == 'next':
            if mode == 'n_poses':
                ego_poses = self._session.query(EgoPose).filter(EgoPose.timestamp > self.ego_pose.timestamp, self.camera.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).limit(number).all()
                return ego_poses
            elif mode == 'n_seconds':
                ego_poses = self._session.query(EgoPose).filter(EgoPose.timestamp - self.ego_pose.timestamp > 0, EgoPose.timestamp - self.ego_pose.timestamp <= number * 1000000.0, self.camera.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).all()
                return ego_poses
            else:
                raise NotImplementedError('Only n_poses and n_seconds two modes are supported!')
        else:
            raise ValueError('Only prev and next two directions are supported!')

    def render(self, db: NuPlanDB, with_3d_anns: bool=True, box_vis_level: BoxVisibility=BoxVisibility.ANY, ax: Optional[Axes]=None) -> None:
        """
        Render the image with all 3d and 2d annotations.
        :param db: Log Database.
        :param with_3d_anns: Whether you want to render 3D boxes?
        :param box_vis_level: One of the enumerations of <BoxVisibility>.
        :param ax: Axes object or array of Axes objects.
        """
        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(9, 16))
        ax.imshow(self.load_as(db, img_type='pil'))
        if with_3d_anns:
            for box in self.boxes(Frame.SENSOR):
                ann_record = db.lidar_box[box.token]
                c = ann_record.category.color_np
                color = (c, c, np.array([0, 0, 0]))
                if box_in_image(box, self.camera.intrinsic_np, (self.camera.width, self.camera.height), vis_level=box_vis_level):
                    box.render(ax, view=self.camera.intrinsic_np, normalize=True, colors=color)
        ax.set_xlim(0, self.camera.width)
        ax.set_ylim(self.camera.height, 0)
        ax.set_title(self.camera.channel)

def boxes(self, frame: Frame=Frame.GLOBAL) -> List[Box3D]:
    """
        Loads all boxes associated with this Image record. Boxes are returned in the global frame by default.
        :param frame: Specify the frame in which the boxes will be returned.
        :return: List of boxes.
        """
    boxes: List[Box3D] = get_boxes(self, frame, self.ego_pose.trans_matrix_inv, self.camera.trans_matrix_inv)
    return boxes

class LidarPc(Base):
    """
    A lidar point cloud.
    """
    __tablename__ = 'lidar_pc'
    token = Column(sql_types.HexLen8, primary_key=True)
    next_token = Column(sql_types.HexLen8, ForeignKey('lidar_pc.token'), nullable=True)
    prev_token = Column(sql_types.HexLen8, ForeignKey('lidar_pc.token'), nullable=True)
    ego_pose_token = Column(sql_types.HexLen8, ForeignKey('ego_pose.token'), nullable=False)
    lidar_token = Column(sql_types.HexLen8, ForeignKey('lidar.token'), nullable=False)
    scene_token = Column(sql_types.HexLen8, ForeignKey('scene.token'), nullable=False)
    filename = Column(String(128))
    timestamp = Column(Integer)
    next = relationship('LidarPc', foreign_keys=[next_token], remote_side=[token])
    prev = relationship('LidarPc', foreign_keys=[prev_token], remote_side=[token])
    ego_pose = relationship('EgoPose', foreign_keys=[ego_pose_token], back_populates='lidar_pc')
    scene = relationship('Scene', foreign_keys=[scene_token], back_populates='lidar_pcs')
    lidar_boxes = relationship('LidarBox', foreign_keys='LidarBox.lidar_pc_token', back_populates='lidar_pc')

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
    def log(self) -> Log:
        """
        Returns the Log containing the LidarPC.
        :return: The log containing the LidarPC.
        """
        return self.lidar.log

    def future_ego_pose(self) -> Optional[EgoPose]:
        """
        Get future ego poses.
        :return: Ego pose at next pointcloud if any.
        """
        if self.next is not None:
            return self.next.ego_pose
        return None

    def past_ego_pose(self) -> Optional[EgoPose]:
        """
        Get past ego poses.
        :return: Ego pose at previous pointcloud if any.
        """
        if self.prev is not None:
            return self.prev.ego_pose
        return None

    def future_or_past_ego_poses(self, number: int, mode: str, direction: str) -> List[EgoPose]:
        """
        Get n future or past vehicle poses. Note here the frequency of pose differs from frequency of LidarPc.
        :param number: Number of poses to fetch or number of seconds of ego poses to fetch.
        :param mode: Either n_poses or n_seconds.
        :param direction: Future or past ego poses to fetch, could be 'prev' or 'next'.
        :return: List of up to n or n seconds future or past ego poses.
        """
        if direction == 'prev':
            if mode == 'n_poses':
                return self._session.query(EgoPose).filter(EgoPose.timestamp < self.ego_pose.timestamp, self.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).limit(number).all()
            elif mode == 'n_seconds':
                return self._session.query(EgoPose).filter(EgoPose.timestamp - self.ego_pose.timestamp < 0, EgoPose.timestamp - self.ego_pose.timestamp >= -number * 1000000.0, self.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.desc()).all()
            else:
                raise ValueError(f'Unknown mode: {mode}.')
        elif direction == 'next':
            if mode == 'n_poses':
                return self._session.query(EgoPose).filter(EgoPose.timestamp > self.ego_pose.timestamp, self.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).limit(number).all()
            elif mode == 'n_seconds':
                return self._session.query(EgoPose).filter(EgoPose.timestamp - self.ego_pose.timestamp > 0, EgoPose.timestamp - self.ego_pose.timestamp <= number * 1000000.0, self.lidar.log_token == EgoPose.log_token).order_by(EgoPose.timestamp.asc()).all()
            else:
                raise ValueError(f'Unknown mode: {mode}.')
        else:
            raise ValueError(f'Unknown direction: {direction}.')

    def load(self, db: NuPlanDB, remove_close: bool=True) -> LidarPointCloud:
        """
        Load a point cloud.
        :param db: Log Database.
        :param remove_close: If true, remove nearby points, defaults to True.
        :return: Loaded point cloud.
        """
        if self.lidar.channel == 'MergedPointCloud':
            if self.filename.endswith('bin2'):
                return LidarPointCloud.from_buffer(self.load_bytes(db), 'bin2')
            else:
                assert self.filename.endswith('pcd'), f'.pcd file is expected but get {self.filename}'
                return LidarPointCloud.from_buffer(self.load_bytes(db), 'pcd')
        else:
            raise NotImplementedError

    def load_bytes(self, db: NuPlanDB) -> BinaryIO:
        """
        Load the point cloud in binary.
        :param db: Log Database.
        :return: Point cloud bytes.
        """
        blob: BinaryIO = db.load_blob(os.path.join('sensor_blobs', self.filename))
        return blob

    def path(self, db: NuPlanDB) -> str:
        """
        Get the path to the point cloud file.
        :param db: Log Database.
        :return: Point cloud file path.
        """
        self.load_bytes(db)
        return osp.join(db.data_root, self.filename)

    def boxes(self, frame: Frame=Frame.GLOBAL) -> List[Box3D]:
        """
        Loads all boxes associated with this LidarPc record. Boxes are returned in the global frame by default.
        :param frame: Specify the frame in which the boxes will be returned.
        :return: The list of boxes.
        """
        boxes: List[Box3D] = get_boxes(self, frame, self.ego_pose.trans_matrix_inv, self.lidar.trans_matrix_inv)
        return boxes

    def boxes_with_future_waypoints(self, future_horizon_len_s: float, future_interval_s: float, frame: Frame=Frame.GLOBAL) -> List[Box3D]:
        """
        Loads all boxes and future boxes associated with this LidarPc record. Boxes are returned in the global frame by
            default and annotations are sampled at a frequency of ~0.5 seconds.
        :param future_horizon_len_s: Timestep horizon of the future waypoints in seconds.
        :param future_interval_s: Timestep interval of the future waypoints in seconds.
        :param frame: Specify the frame in which the boxes will be returned.
        :return: List of boxes in sample data that includes box centers and orientations at future timesteps.
        """
        TIMESTAMP_MARGIN_MS = 1000000.0
        future_horizon_len_ms = future_horizon_len_s * 1000000.0
        query = self._session.query(LidarPc).filter(LidarPc.timestamp - self.timestamp >= 0, LidarPc.timestamp - self.timestamp <= future_horizon_len_ms + TIMESTAMP_MARGIN_MS).order_by(LidarPc.timestamp.asc()).all()
        lidar_pcs = [lidar_pc for lidar_pc in list(query)]
        track_token_2_box_sequence = get_future_box_sequence(lidar_pcs=lidar_pcs, frame=frame, future_horizon_len_s=future_horizon_len_s, future_interval_s=future_interval_s, trans_matrix_ego=self.ego_pose.trans_matrix_inv, trans_matrix_sensor=self.lidar.trans_matrix_inv)
        boxes_with_future_waypoints: List[Box3D] = pack_future_boxes(track_token_2_box_sequence=track_token_2_box_sequence, future_interval_s=future_interval_s, future_horizon_len_s=future_horizon_len_s)
        return boxes_with_future_waypoints

    def render(self, db: NuPlanDB, render_future_waypoints: bool=False, render_map_raster: bool=False, render_vector_map: bool=False, render_track_color: bool=False, render_future_ego_poses: bool=False, track_token: Optional[str]=None, with_anns: bool=True, axes_limit: float=80.0, ax: Axes=None) -> plt.axes:
        """
        Render the Lidar pointcloud with appropriate boxes and (optionally) the map raster.
        :param db: Log database.
        :param render_future_waypoints: Whether to render future waypoints.
        :param render_map_raster: Whether to render the map raster.
        :param render_vector_map: Whether to render the vector map.
        :param render_track_color: Whether to render the tracks with different random color.
        :param render_future_ego_poses: Whether to render future ego poses.
        :param track_token: Which instance to render, if it's None, render all the instances.
        :param with_anns: Whether you want to render the annotations?
        :param axes_limit: The range of Lidar pointcloud that will be rendered will be between
            (-axes_limit, axes_limit).
        :param ax: Axes object.
        :return: Axes object.
        """
        if ax is None:
            _, ax = plt.subplots(1, 1, figsize=(25, 25))
        if with_anns:
            if render_future_waypoints:
                DEFAULT_FUTURE_HORIZON_LEN_S = 6.0
                DEFAULT_FUTURE_INTERVAL_S = 0.5
                boxes = self.boxes_with_future_waypoints(DEFAULT_FUTURE_HORIZON_LEN_S, DEFAULT_FUTURE_INTERVAL_S, Frame.SENSOR)
            else:
                boxes = self.boxes(Frame.SENSOR)
        else:
            boxes = []
        if render_future_ego_poses:
            DEFAULT_FUTURE_HORIZON_LEN_S = 6
            TIMESTAMP_MARGIN_S = 1
            ego_poses = self.future_or_past_ego_poses(DEFAULT_FUTURE_HORIZON_LEN_S + TIMESTAMP_MARGIN_S, 'n_seconds', 'next')
        else:
            ego_poses = [self.ego_pose]
        labelmap = {lid: Label(raw_mapping['id2local'][lid], raw_mapping['id2color'][lid]) for lid in raw_mapping['id2local'].keys()}
        render_on_map(lidarpc_rec=self, db=db, boxes_lidar=boxes, ego_poses=ego_poses, radius=axes_limit, ax=ax, labelmap=labelmap, render_map_raster=render_map_raster, render_vector_map=render_vector_map, track_token=track_token, with_random_color=render_track_color, render_future_ego_poses=render_future_ego_poses)
        plt.axis('equal')
        ax.set_title('PC {} from {} in {}'.format(self.token, self.lidar.channel, self.log.location))
        return ax

def boxes(self, frame: Frame=Frame.GLOBAL) -> List[Box3D]:
    """
        Loads all boxes associated with this LidarPc record. Boxes are returned in the global frame by default.
        :param frame: Specify the frame in which the boxes will be returned.
        :return: The list of boxes.
        """
    boxes: List[Box3D] = get_boxes(self, frame, self.ego_pose.trans_matrix_inv, self.lidar.trans_matrix_inv)
    return boxes

class TestPredictionConstruction(unittest.TestCase):
    """Tests free function for prediction construction given future ground truth"""

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.StateSE2', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.OrientedBox', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.StateVector2D', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.TimePoint', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.Waypoint', autospec=True)
    def test__waypoint_from_lidar_box(self, waypoint: Mock, time_point: Mock, state_vector: Mock, oriented_box: Mock, state_se2: Mock, lidar_box: Mock) -> None:
        """Tests Waypoint creation from LidarBox"""
        lidar_box.translation = ['x', 'y']
        lidar_box.yaw = 'yaw'
        lidar_box.size = ['w', 'l', 'h']
        lidar_box.vx = 'vx'
        lidar_box.vy = 'vy'
        lidar_box.timestamp = 'timestamp'
        result = _waypoint_from_lidar_box(lidar_box)
        state_se2.assert_called_once_with('x', 'y', 'yaw')
        oriented_box.assert_called_once_with(state_se2.return_value, width='w', length='l', height='h')
        state_vector.assert_called_once_with('vx', 'vy')
        time_point.assert_called_once_with('timestamp')
        waypoint.assert_called_once_with(time_point.return_value, oriented_box.return_value, state_vector.return_value)
        self.assertEqual(waypoint.return_value, result)

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction._waypoint_from_lidar_box', autospec=True)
    def test_get_waypoints_for_agent(self, waypoint_from_lidar_box: Mock, lidar_box: Mock) -> None:
        """Tests extraction of future waypoints for a single agent"""
        end_timestamp = 5
        lidar_box.timestamp = 0

        def increase_timestamp() -> Any:
            """Increases the lidar_box timestamp"""
            lidar_box.timestamp += 1
            return DEFAULT
        type(lidar_box).next = PropertyMock(return_value=lidar_box, side_effect=increase_timestamp)
        result = get_waypoints_for_agent(lidar_box, end_timestamp)
        calls = [call(lidar_box)] * 5
        waypoint_from_lidar_box.assert_has_calls(calls)
        self.assertTrue(5, len(result))

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
    def test_get_waypoints_for_agent_empty_on_invalid_time(self, lidar_box: Mock) -> None:
        """Tests extraction of future waypoints for a single agent"""
        end_timestamp = 1
        lidar_box.timestamp = 2
        result = get_waypoints_for_agent(lidar_box, end_timestamp)
        self.assertEqual([], result)

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.InterpolatedTrajectory', autospec=True)
    @patch('numpy.arange')
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.TimePoint', autospec=True)
    def test_interpolate_waypoints(self, time_point: Mock, arange: Mock, interpolated_trajectory: Mock) -> None:
        """Tests interpolation of waypoints for a single agent"""
        waypoints = [Mock(time_us=0, spec_set=Waypoint)]
        arange.return_value = [1.12, 2.23]
        time_point.side_effect = ['tp1', 'tp2']
        trajectory_sampling = Mock(time_horizon=5, step_time=1, spec=TrajectorySampling)
        result = interpolate_waypoints(waypoints, trajectory_sampling)
        arange.assert_called_once_with(0, 5 * 1000000.0, 1 * 1000000.0)
        time_point_calls = [call(1), call(2)]
        time_point.assert_has_calls(time_point_calls)
        calls = [call('tp1'), call('tp2')]
        interpolated_trajectory.return_value.get_state_at_time.assert_has_calls(calls)
        self.assertEqual(result, [interpolated_trajectory.return_value.get_state_at_time.return_value] * 2)

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.get_waypoints_for_agent', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.interpolate_waypoints', autospec=True)
    def test_get_interpolated_waypoints(self, mock_interpolate_waypoints: Mock, mock_get_waypoints_for_agent: Mock) -> None:
        """Tests extraction and interpolation of waypoints for a list of agents"""
        box_1 = Mock(track_token='1')
        box_2 = Mock(track_token='2')
        mock_lidar_pc = Mock(timestamp=0, lidar_boxes=[box_1, box_2])
        future_trajectory_sampling = Mock(time_horizon=5)
        mock_get_waypoints_for_agent.side_effect = ['waypoints_1', 'waypoints_2']
        result = get_interpolated_waypoints(mock_lidar_pc, future_trajectory_sampling)
        get_waypoints_calls = [call(box_1, 5 * 1000000.0), call(box_2, 5 * 1000000.0)]
        mock_get_waypoints_for_agent.assert_has_calls(get_waypoints_calls)
        interpolate_waypoints_calls = [call('waypoints_1', future_trajectory_sampling), call('waypoints_2', future_trajectory_sampling)]
        mock_interpolate_waypoints.assert_has_calls(interpolate_waypoints_calls)
        self.assertEqual(result, {'1': mock_interpolate_waypoints.return_value, '2': mock_interpolate_waypoints.return_value})

    @patch('nuplan.database.nuplan_db_orm.prediction_construction.get_waypoints_for_agent', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.prediction_construction.interpolate_waypoints', autospec=True)
    def test_get_interpolated_waypoints_no_waypoitns(self, mock_interpolate_waypoints: Mock, mock_get_waypoints_for_agent: Mock) -> None:
        """Tests extraction and interpolation of waypoints for a list of agents"""
        box_1 = Mock(track_token='1')
        box_2 = Mock(track_token='2')
        mock_lidar_pc = Mock(timestamp=0, lidar_boxes=[box_1, box_2])
        future_trajectory_sampling = Mock(time_horizon=5)
        mock_get_waypoints_for_agent.side_effect = [[], ['waypoint']]
        result = get_interpolated_waypoints(mock_lidar_pc, future_trajectory_sampling)
        get_waypoints_calls = [call(box_1, 5 * 1000000.0), call(box_2, 5 * 1000000.0)]
        mock_get_waypoints_for_agent.assert_has_calls(get_waypoints_calls)
        mock_interpolate_waypoints.assert_not_called()
        self.assertEqual(result, {'1': [], '2': []})

@patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.StateSE2', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.OrientedBox', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.StateVector2D', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.TimePoint', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.Waypoint', autospec=True)
def test__waypoint_from_lidar_box(self, waypoint: Mock, time_point: Mock, state_vector: Mock, oriented_box: Mock, state_se2: Mock, lidar_box: Mock) -> None:
    """Tests Waypoint creation from LidarBox"""
    lidar_box.translation = ['x', 'y']
    lidar_box.yaw = 'yaw'
    lidar_box.size = ['w', 'l', 'h']
    lidar_box.vx = 'vx'
    lidar_box.vy = 'vy'
    lidar_box.timestamp = 'timestamp'
    result = _waypoint_from_lidar_box(lidar_box)
    state_se2.assert_called_once_with('x', 'y', 'yaw')
    oriented_box.assert_called_once_with(state_se2.return_value, width='w', length='l', height='h')
    state_vector.assert_called_once_with('vx', 'vy')
    time_point.assert_called_once_with('timestamp')
    waypoint.assert_called_once_with(time_point.return_value, oriented_box.return_value, state_vector.return_value)
    self.assertEqual(waypoint.return_value, result)

@patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction._waypoint_from_lidar_box', autospec=True)
def test_get_waypoints_for_agent(self, waypoint_from_lidar_box: Mock, lidar_box: Mock) -> None:
    """Tests extraction of future waypoints for a single agent"""
    end_timestamp = 5
    lidar_box.timestamp = 0

    def increase_timestamp() -> Any:
        """Increases the lidar_box timestamp"""
        lidar_box.timestamp += 1
        return DEFAULT
    type(lidar_box).next = PropertyMock(return_value=lidar_box, side_effect=increase_timestamp)
    result = get_waypoints_for_agent(lidar_box, end_timestamp)
    calls = [call(lidar_box)] * 5
    waypoint_from_lidar_box.assert_has_calls(calls)
    self.assertTrue(5, len(result))

@patch('nuplan.database.nuplan_db_orm.prediction_construction.LidarBox', autospec=True)
def test_get_waypoints_for_agent_empty_on_invalid_time(self, lidar_box: Mock) -> None:
    """Tests extraction of future waypoints for a single agent"""
    end_timestamp = 1
    lidar_box.timestamp = 2
    result = get_waypoints_for_agent(lidar_box, end_timestamp)
    self.assertEqual([], result)

@patch('nuplan.database.nuplan_db_orm.prediction_construction.InterpolatedTrajectory', autospec=True)
@patch('numpy.arange')
@patch('nuplan.database.nuplan_db_orm.prediction_construction.TimePoint', autospec=True)
def test_interpolate_waypoints(self, time_point: Mock, arange: Mock, interpolated_trajectory: Mock) -> None:
    """Tests interpolation of waypoints for a single agent"""
    waypoints = [Mock(time_us=0, spec_set=Waypoint)]
    arange.return_value = [1.12, 2.23]
    time_point.side_effect = ['tp1', 'tp2']
    trajectory_sampling = Mock(time_horizon=5, step_time=1, spec=TrajectorySampling)
    result = interpolate_waypoints(waypoints, trajectory_sampling)
    arange.assert_called_once_with(0, 5 * 1000000.0, 1 * 1000000.0)
    time_point_calls = [call(1), call(2)]
    time_point.assert_has_calls(time_point_calls)
    calls = [call('tp1'), call('tp2')]
    interpolated_trajectory.return_value.get_state_at_time.assert_has_calls(calls)
    self.assertEqual(result, [interpolated_trajectory.return_value.get_state_at_time.return_value] * 2)

@patch('nuplan.database.nuplan_db_orm.prediction_construction.get_waypoints_for_agent', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.interpolate_waypoints', autospec=True)
def test_get_interpolated_waypoints(self, mock_interpolate_waypoints: Mock, mock_get_waypoints_for_agent: Mock) -> None:
    """Tests extraction and interpolation of waypoints for a list of agents"""
    box_1 = Mock(track_token='1')
    box_2 = Mock(track_token='2')
    mock_lidar_pc = Mock(timestamp=0, lidar_boxes=[box_1, box_2])
    future_trajectory_sampling = Mock(time_horizon=5)
    mock_get_waypoints_for_agent.side_effect = ['waypoints_1', 'waypoints_2']
    result = get_interpolated_waypoints(mock_lidar_pc, future_trajectory_sampling)
    get_waypoints_calls = [call(box_1, 5 * 1000000.0), call(box_2, 5 * 1000000.0)]
    mock_get_waypoints_for_agent.assert_has_calls(get_waypoints_calls)
    interpolate_waypoints_calls = [call('waypoints_1', future_trajectory_sampling), call('waypoints_2', future_trajectory_sampling)]
    mock_interpolate_waypoints.assert_has_calls(interpolate_waypoints_calls)
    self.assertEqual(result, {'1': mock_interpolate_waypoints.return_value, '2': mock_interpolate_waypoints.return_value})

@patch('nuplan.database.nuplan_db_orm.prediction_construction.get_waypoints_for_agent', autospec=True)
@patch('nuplan.database.nuplan_db_orm.prediction_construction.interpolate_waypoints', autospec=True)
def test_get_interpolated_waypoints_no_waypoitns(self, mock_interpolate_waypoints: Mock, mock_get_waypoints_for_agent: Mock) -> None:
    """Tests extraction and interpolation of waypoints for a list of agents"""
    box_1 = Mock(track_token='1')
    box_2 = Mock(track_token='2')
    mock_lidar_pc = Mock(timestamp=0, lidar_boxes=[box_1, box_2])
    future_trajectory_sampling = Mock(time_horizon=5)
    mock_get_waypoints_for_agent.side_effect = [[], ['waypoint']]
    result = get_interpolated_waypoints(mock_lidar_pc, future_trajectory_sampling)
    get_waypoints_calls = [call(box_1, 5 * 1000000.0), call(box_2, 5 * 1000000.0)]
    mock_get_waypoints_for_agent.assert_has_calls(get_waypoints_calls)
    mock_interpolate_waypoints.assert_not_called()
    self.assertEqual(result, {'1': [], '2': []})

class TestTrafficLightStatus(unittest.TestCase):
    """Tests the TrafficLightStatus class"""

    def setUp(self) -> None:
        """Sets up for the test cases"""
        self.traffic_light_status = TrafficLightStatus()

    @patch('nuplan.database.nuplan_db_orm.traffic_light_status.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the repr method"""
        result = self.traffic_light_status.__repr__()
        simple_repr_mock.assert_called_once_with(self.traffic_light_status)
        self.assertEqual(result, simple_repr_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.traffic_light_status.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.traffic_light_status._session()
        inspect_mock.assert_called_once_with(self.traffic_light_status)
        self.assertEqual(result, session_mock.return_value)

@patch('nuplan.database.nuplan_db_orm.traffic_light_status.simple_repr', autospec=True)
def test_repr(self, simple_repr_mock: Mock) -> None:
    """Tests the repr method"""
    result = self.traffic_light_status.__repr__()
    simple_repr_mock.assert_called_once_with(self.traffic_light_status)
    self.assertEqual(result, simple_repr_mock.return_value)

@patch('nuplan.database.nuplan_db_orm.traffic_light_status.inspect', autospec=True)
def test_session(self, inspect_mock: Mock) -> None:
    """Tests the session property"""
    session_mock = PropertyMock()
    inspect_mock.return_value = Mock()
    inspect_mock.return_value.session = session_mock
    result = self.traffic_light_status._session()
    inspect_mock.assert_called_once_with(self.traffic_light_status)
    self.assertEqual(result, session_mock.return_value)

class TestCamera(unittest.TestCase):
    """Test class Camera"""

    def setUp(self) -> None:
        """
        Initializes a test Camera
        """
        self.camera = get_test_nuplan_camera()

    @patch('nuplan.database.nuplan_db_orm.camera.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.camera._session()
        inspect.assert_called_once_with(self.camera)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.camera.__repr__()
        simple_repr.assert_called_once_with(self.camera)
        self.assertEqual(result, simple_repr.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_intrinsic_np(self, np_array: Mock) -> None:
        """
        Test property - camera intrinsic.
        """
        result = self.camera.intrinsic_np
        np_array.assert_called_once_with(self.camera.intrinsic)
        self.assertEqual(result, np_array.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_distortion_np(self, np_array: Mock) -> None:
        """
        Test property - camera distrotion.
        """
        result = self.camera.distortion_np
        np_array.assert_called_once_with(self.camera.distortion)
        self.assertEqual(result, np_array.return_value)

    @patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
    def test_translation_np(self, np_array: Mock) -> None:
        """
        Test property - translation.
        """
        result = self.camera.translation_np
        np_array.assert_called_once_with(self.camera.translation)
        self.assertEqual(result, np_array.return_value)

    def test_quaternion(self) -> None:
        """
        Test property - rotation in quaternion.
        """
        result = self.camera.quaternion
        np.testing.assert_array_equal(self.camera.rotation, result.elements)

    def test_trans_matrix_and_inv(self) -> None:
        """
        Test two properties - transformation matrix and its inverse.
        """
        trans_mat = self.camera.trans_matrix
        inv_trans_mat = self.camera.trans_matrix_inv
        np.testing.assert_allclose(trans_mat @ inv_trans_mat, np.eye(4), atol=0.001)

@patch('nuplan.database.nuplan_db_orm.camera.inspect', autospec=True)
def test_session(self, inspect: Mock) -> None:
    """
        Tests _session method
        """
    mock_session = PropertyMock()
    inspect.return_value = Mock()
    inspect.return_value.session = mock_session
    result = self.camera._session()
    inspect.assert_called_once_with(self.camera)
    mock_session.assert_called_once()
    self.assertEqual(result, mock_session.return_value)

@patch('nuplan.database.nuplan_db_orm.camera.simple_repr', autospec=True)
def test_repr(self, simple_repr: Mock) -> None:
    """
        Tests string representation
        """
    result = self.camera.__repr__()
    simple_repr.assert_called_once_with(self.camera)
    self.assertEqual(result, simple_repr.return_value)

@patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
def test_intrinsic_np(self, np_array: Mock) -> None:
    """
        Test property - camera intrinsic.
        """
    result = self.camera.intrinsic_np
    np_array.assert_called_once_with(self.camera.intrinsic)
    self.assertEqual(result, np_array.return_value)

@patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
def test_distortion_np(self, np_array: Mock) -> None:
    """
        Test property - camera distrotion.
        """
    result = self.camera.distortion_np
    np_array.assert_called_once_with(self.camera.distortion)
    self.assertEqual(result, np_array.return_value)

@patch('nuplan.database.nuplan_db_orm.camera.np.array', autospec=True)
def test_translation_np(self, np_array: Mock) -> None:
    """
        Test property - translation.
        """
    result = self.camera.translation_np
    np_array.assert_called_once_with(self.camera.translation)
    self.assertEqual(result, np_array.return_value)

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

@patch('nuplan.database.nuplan_db_orm.lidar_pc.LidarPointCloud.from_buffer', autospec=True)
def test_load_channel_is_merged_point_cloud(self, from_buffer_mock: Mock) -> None:
    """Tests the load method when lidar channel is MergedPointCloud"""
    db = get_test_nuplan_db()
    result = self.lidar_pc.load(db)
    self.assertEqual(result, from_buffer_mock.return_value)

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

class TestScenarioTag(unittest.TestCase):
    """Tests class ScenarioTag"""

    def setUp(self) -> None:
        """Sets up for the test cases"""
        self.scenario_tag = ScenarioTag()

    @patch('nuplan.database.nuplan_db_orm.scenario_tag.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.scenario_tag._session
        inspect_mock.assert_called_once_with(self.scenario_tag)
        self.assertEqual(result, session_mock)

    @patch('nuplan.database.nuplan_db_orm.scenario_tag.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the __repr__ method"""
        result = self.scenario_tag.__repr__()
        self.assertEqual(result, simple_repr_mock.return_value)

@patch('nuplan.database.nuplan_db_orm.scenario_tag.inspect', autospec=True)
def test_session(self, inspect_mock: Mock) -> None:
    """Tests the session property"""
    session_mock = PropertyMock()
    inspect_mock.return_value = Mock()
    inspect_mock.return_value.session = session_mock
    result = self.scenario_tag._session
    inspect_mock.assert_called_once_with(self.scenario_tag)
    self.assertEqual(result, session_mock)

@patch('nuplan.database.nuplan_db_orm.scenario_tag.simple_repr', autospec=True)
def test_repr(self, simple_repr_mock: Mock) -> None:
    """Tests the __repr__ method"""
    result = self.scenario_tag.__repr__()
    self.assertEqual(result, simple_repr_mock.return_value)

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

class TestGetBoxes(unittest.TestCase):
    """Test get box."""

    def _box_A(self) -> Box3D:
        """
        Helper method to get one box.
        :return: One box.
        """
        return Box3D(center=(0.0, 0.0, 0.0), size=(1.0, 1.0, 1.0), orientation=Quaternion(axis=[1, 0, 0], angle=0), velocity=(0.0, 0.0, 0.0), angular_velocity=0.0)

    def _box_B(self) -> Box3D:
        """
        Helper method to get one box.
        :return: One box.
        """
        return Box3D(center=(1.0, 2.0, 3.0), size=(1.0, 1.0, 1.0), orientation=Quaternion(axis=[1, 0, 0], angle=2), velocity=(5.0, 6.0, 7.0), angular_velocity=8.0)

    def _box_quarterway_between_A_and_B(self) -> Box3D:
        """
        Helper method to get one box.
        :return: One box.
        """
        return Box3D(center=(0.25, 0.5, 0.75), size=(1.0, 1.0, 1.0), orientation=Quaternion(axis=[1, 0, 0], angle=0.5), velocity=(1.25, 1.5, 1.75), angular_velocity=2.0)

    def _box_halfway_between_A_and_B(self) -> Box3D:
        """
        Helper method to get one box.
        :return: One box.
        """
        return Box3D(center=(0.5, 1.0, 1.5), size=(1.0, 1.0, 1.0), orientation=Quaternion(axis=[1, 0, 0], angle=1), velocity=(2.5, 3, 3.5), angular_velocity=4.0)

    def _annotation_A(self, track_token: str) -> Mock:
        """
        Helper method to get one annotation.
        :param track_token: Track token to use.
        :return: Mocked annotation.
        """
        ann = Mock()
        ann.x = 0.0
        ann.y = 0.0
        ann.z = 0.0
        ann.translation_np = np.array([ann.x, ann.y, ann.z])
        ann.width = 1.0
        ann.length = 1.0
        ann.height = 1.0
        ann.size = (ann.width, ann.length, ann.height)
        ann.roll = 0.0
        ann.pitch = 0.0
        ann.yaw = 0.0
        ann.quaternion = Quaternion(axis=[1, 0, 0], angle=0)
        ann.vx = 0.0
        ann.vy = 0.0
        ann.vz = 0.0
        ann.velocity = np.array([ann.vx, ann.vy, ann.vz])
        ann.angular_velocity = 0.0
        ann.box.return_value = self._box_A()
        ann.track_token = track_token
        return ann

    def _annotation_B(self, track_token: str) -> Mock:
        """
        Helper method to get one annotation.
        :param track_token: Track token to use.
        :return: Mocked annotation.
        """
        ann = Mock()
        ann.x = 1.0
        ann.y = 2.0
        ann.z = 3.0
        ann.translation_np = np.array([ann.x, ann.y, ann.z])
        ann.width = 1.0
        ann.length = 1.0
        ann.height = 1.0
        ann.size = (ann.width, ann.length, ann.height)
        ann.roll = 0.0
        ann.pitch = 0.0
        ann.yaw = 0.0
        ann.quaternion = Quaternion(axis=[1, 0, 0], angle=2)
        ann.vx = 5.0
        ann.vy = 6.0
        ann.vz = 7.0
        ann.velocity = np.array([ann.vx, ann.vy, ann.vz])
        ann.angular_velocity = 8.0
        ann.box.return_value = self._box_B()
        ann.track_token = track_token
        return ann

    def _trans_matrix_ego(self) -> npt.NDArray[np.float64]:
        """
        Helper method to get a transformation.
        :return: <np.float: 4, 4> Transformation matrix.
        """
        return np.array([[0, 1, 0, 1], [-1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]])

    def _trans_matrix_sensor(self) -> npt.NDArray[np.float64]:
        """
        Helper method to get a transformation.
        :return: <np.float: 4, 4> Transformation matrix.
        """
        return np.array([[0, 0, 1, 4], [0, -1, 0, 5], [1, 0, 0, 6], [0, 0, 0, 1]])

    def test_frame_vehicle(self) -> None:
        """
        Test putting resulting boxes in vehicle coordinates.
        """
        lidarpc = Mock()
        lidarpc.lidar_boxes = [self._annotation_B(track_token='456')]
        lidarpc.prev = object()
        box_b_vehicle_frame = self._box_B()
        box_b_vehicle_frame.transform(self._trans_matrix_ego())
        self.assertEqual(get_boxes(lidarpc, frame=Frame.VEHICLE, trans_matrix_ego=self._trans_matrix_ego()), [box_b_vehicle_frame])

    def test_frame_sensor(self) -> None:
        """
        Test putting resulting boxes in sensor coordinates.
        """
        lidarpc = Mock()
        lidarpc.lidar_boxes = [self._annotation_B(track_token='456')]
        lidarpc.prev = object()
        box_b_sensor_frame = self._box_B()
        box_b_sensor_frame.transform(self._trans_matrix_ego())
        box_b_sensor_frame.transform(self._trans_matrix_sensor())
        self.assertEqual(get_boxes(lidarpc, frame=Frame.SENSOR, trans_matrix_ego=self._trans_matrix_ego(), trans_matrix_sensor=self._trans_matrix_sensor()), [box_b_sensor_frame])

def _annotation_B(self, track_token: str) -> Mock:
    """
        Helper method to get one annotation.
        :param track_token: Track token to use.
        :return: Mocked annotation.
        """
    ann = Mock()
    ann.x = 1.0
    ann.y = 2.0
    ann.z = 3.0
    ann.translation_np = np.array([ann.x, ann.y, ann.z])
    ann.width = 1.0
    ann.length = 1.0
    ann.height = 1.0
    ann.size = (ann.width, ann.length, ann.height)
    ann.roll = 0.0
    ann.pitch = 0.0
    ann.yaw = 0.0
    ann.quaternion = Quaternion(axis=[1, 0, 0], angle=2)
    ann.vx = 5.0
    ann.vy = 6.0
    ann.vz = 7.0
    ann.velocity = np.array([ann.vx, ann.vy, ann.vz])
    ann.angular_velocity = 8.0
    ann.box.return_value = self._box_B()
    ann.track_token = track_token
    return ann

def test_frame_vehicle(self) -> None:
    """
        Test putting resulting boxes in vehicle coordinates.
        """
    lidarpc = Mock()
    lidarpc.lidar_boxes = [self._annotation_B(track_token='456')]
    lidarpc.prev = object()
    box_b_vehicle_frame = self._box_B()
    box_b_vehicle_frame.transform(self._trans_matrix_ego())
    self.assertEqual(get_boxes(lidarpc, frame=Frame.VEHICLE, trans_matrix_ego=self._trans_matrix_ego()), [box_b_vehicle_frame])

def test_frame_sensor(self) -> None:
    """
        Test putting resulting boxes in sensor coordinates.
        """
    lidarpc = Mock()
    lidarpc.lidar_boxes = [self._annotation_B(track_token='456')]
    lidarpc.prev = object()
    box_b_sensor_frame = self._box_B()
    box_b_sensor_frame.transform(self._trans_matrix_ego())
    box_b_sensor_frame.transform(self._trans_matrix_sensor())
    self.assertEqual(get_boxes(lidarpc, frame=Frame.SENSOR, trans_matrix_ego=self._trans_matrix_ego(), trans_matrix_sensor=self._trans_matrix_sensor()), [box_b_sensor_frame])

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

def test_load_boxes_from_lidarpc(self) -> None:
    """Test load all boxes from a lidar pc."""
    boxes = load_boxes_from_lidarpc(self.db, self.lidar_pc, ['pedestrian', 'vehicle'], False, 80.04, self.future_horizon_len_s, self.future_interval_s, {'pedestrian': 0, 'vehicle': 1})
    self.assertSetEqual({'pedestrian', 'vehicle'}, set(boxes.keys()))
    self.assertEqual(len(boxes['pedestrian']), 70)
    self.assertEqual(len(boxes['vehicle']), 29)

class TestLog(unittest.TestCase):
    """Test class Log"""

    def setUp(self) -> None:
        """
        Initializes a test Log
        """
        self.log = Log()

    @patch('nuplan.database.nuplan_db_orm.log.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.log._session()
        inspect.assert_called_once_with(self.log)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    def test_images(self) -> None:
        """
        Tests images property
        """
        mock_image_1 = Mock()
        mock_image_2 = Mock()
        mock_camera_1 = MagicMock()
        mock_camera_1.images = Mock()
        mock_camera_1.images.__iter__ = Mock(return_value=iter([mock_image_1, mock_image_2]))
        mock_camera_2 = MagicMock()
        mock_camera_2.images = Mock()
        mock_camera_2.images.__iter__ = Mock(return_value=iter([mock_image_2, mock_image_1]))
        self.log.cameras = [mock_camera_1, mock_camera_2]
        result = self.log.images
        self.assertEqual(result, [mock_image_1, mock_image_2, mock_image_2, mock_image_1])

    def test_lidar_pcs(self) -> None:
        """
        Test lidar_pcs property
        """
        mock_lidar_pc_1 = Mock()
        mock_lidar_pc_2 = Mock()
        mock_lidar_1 = MagicMock()
        mock_lidar_1.lidar_pcs = Mock()
        mock_lidar_1.lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pc_1, mock_lidar_pc_2]))
        mock_lidar_2 = MagicMock()
        mock_lidar_2.lidar_pcs = Mock()
        mock_lidar_2.lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pc_2, mock_lidar_pc_1]))
        self.log.lidars = [mock_lidar_1, mock_lidar_2]
        result = self.log.lidar_pcs
        self.assertEqual(result, [mock_lidar_pc_1, mock_lidar_pc_2, mock_lidar_pc_2, mock_lidar_pc_1])

    @patch('nuplan.database.nuplan_db_orm.log.Log.lidar_pcs', autospec=True)
    def test_lidar_boxes(self, mock_lidar_pcs: Mock) -> None:
        """
        Test lidar_boxes method
        """
        mock_lidar_box_1 = Mock()
        mock_lidar_box_2 = Mock()
        mock_lidar_pcs_1 = Mock()
        mock_lidar_pcs_1.lidar_boxes = Mock()
        mock_lidar_pcs_1.lidar_boxes.__iter__ = Mock(return_value=iter([mock_lidar_box_1, mock_lidar_box_2]))
        mock_lidar_pcs_2 = Mock()
        mock_lidar_pcs_2.lidar_boxes = Mock()
        mock_lidar_pcs_2.lidar_boxes.__iter__ = Mock(return_value=iter([mock_lidar_box_2, mock_lidar_box_1]))
        mock_lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pcs_1, mock_lidar_pcs_2]))
        result = self.log.lidar_boxes
        mock_lidar_pcs.__iter__.assert_called()
        self.assertEqual(result, [mock_lidar_box_1, mock_lidar_box_2, mock_lidar_box_2, mock_lidar_box_1])

    @patch('nuplan.database.nuplan_db_orm.log.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.log.__repr__()
        simple_repr.assert_called_once()
        self.assertEqual(result, simple_repr.return_value)

@patch('nuplan.database.nuplan_db_orm.log.inspect', autospec=True)
def test_session(self, inspect: Mock) -> None:
    """
        Tests _session method
        """
    mock_session = PropertyMock()
    inspect.return_value = Mock()
    inspect.return_value.session = mock_session
    result = self.log._session()
    inspect.assert_called_once_with(self.log)
    mock_session.assert_called_once()
    self.assertEqual(result, mock_session.return_value)

def test_images(self) -> None:
    """
        Tests images property
        """
    mock_image_1 = Mock()
    mock_image_2 = Mock()
    mock_camera_1 = MagicMock()
    mock_camera_1.images = Mock()
    mock_camera_1.images.__iter__ = Mock(return_value=iter([mock_image_1, mock_image_2]))
    mock_camera_2 = MagicMock()
    mock_camera_2.images = Mock()
    mock_camera_2.images.__iter__ = Mock(return_value=iter([mock_image_2, mock_image_1]))
    self.log.cameras = [mock_camera_1, mock_camera_2]
    result = self.log.images
    self.assertEqual(result, [mock_image_1, mock_image_2, mock_image_2, mock_image_1])

def test_lidar_pcs(self) -> None:
    """
        Test lidar_pcs property
        """
    mock_lidar_pc_1 = Mock()
    mock_lidar_pc_2 = Mock()
    mock_lidar_1 = MagicMock()
    mock_lidar_1.lidar_pcs = Mock()
    mock_lidar_1.lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pc_1, mock_lidar_pc_2]))
    mock_lidar_2 = MagicMock()
    mock_lidar_2.lidar_pcs = Mock()
    mock_lidar_2.lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pc_2, mock_lidar_pc_1]))
    self.log.lidars = [mock_lidar_1, mock_lidar_2]
    result = self.log.lidar_pcs
    self.assertEqual(result, [mock_lidar_pc_1, mock_lidar_pc_2, mock_lidar_pc_2, mock_lidar_pc_1])

@patch('nuplan.database.nuplan_db_orm.log.Log.lidar_pcs', autospec=True)
def test_lidar_boxes(self, mock_lidar_pcs: Mock) -> None:
    """
        Test lidar_boxes method
        """
    mock_lidar_box_1 = Mock()
    mock_lidar_box_2 = Mock()
    mock_lidar_pcs_1 = Mock()
    mock_lidar_pcs_1.lidar_boxes = Mock()
    mock_lidar_pcs_1.lidar_boxes.__iter__ = Mock(return_value=iter([mock_lidar_box_1, mock_lidar_box_2]))
    mock_lidar_pcs_2 = Mock()
    mock_lidar_pcs_2.lidar_boxes = Mock()
    mock_lidar_pcs_2.lidar_boxes.__iter__ = Mock(return_value=iter([mock_lidar_box_2, mock_lidar_box_1]))
    mock_lidar_pcs.__iter__ = Mock(return_value=iter([mock_lidar_pcs_1, mock_lidar_pcs_2]))
    result = self.log.lidar_boxes
    mock_lidar_pcs.__iter__.assert_called()
    self.assertEqual(result, [mock_lidar_box_1, mock_lidar_box_2, mock_lidar_box_2, mock_lidar_box_1])

@patch('nuplan.database.nuplan_db_orm.log.simple_repr', autospec=True)
def test_repr(self, simple_repr: Mock) -> None:
    """
        Tests string representation
        """
    result = self.log.__repr__()
    simple_repr.assert_called_once()
    self.assertEqual(result, simple_repr.return_value)

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

class TestCategory(unittest.TestCase):
    """Test class Category"""

    def setUp(self) -> None:
        """
        Initializes a test Category
        """
        self.category = Category()

    @patch('nuplan.database.nuplan_db_orm.category.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session methodtable property
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.category._session()
        inspect.assert_called_once_with(self.category)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.category.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.category.__repr__()
        simple_repr.assert_called_once_with(self.category)
        self.assertEqual(result, simple_repr.return_value)

    @patch('nuplan.database.nuplan_db_orm.category.default_color', autospec=True)
    def test_color(self, default_color: Mock) -> None:
        """
        Tests color property
        """
        result = self.category.color
        default_color.assert_called_once_with(self.category.name)
        self.assertEqual(result, default_color.return_value)

    @patch('nuplan.database.nuplan_db_orm.category.default_color_np', autospec=True)
    def test_color_np(self, default_color_np: Mock) -> None:
        """
        Tests color_np property
        """
        result = self.category.color_np
        default_color_np.assert_called_once_with(self.category.name)
        self.assertEqual(result, default_color_np.return_value)

@patch('nuplan.database.nuplan_db_orm.category.inspect', autospec=True)
def test_session(self, inspect: Mock) -> None:
    """
        Tests _session methodtable property
        """
    mock_session = PropertyMock()
    inspect.return_value = Mock()
    inspect.return_value.session = mock_session
    result = self.category._session()
    inspect.assert_called_once_with(self.category)
    mock_session.assert_called_once()
    self.assertEqual(result, mock_session.return_value)

@patch('nuplan.database.nuplan_db_orm.category.simple_repr', autospec=True)
def test_repr(self, simple_repr: Mock) -> None:
    """
        Tests string representation
        """
    result = self.category.__repr__()
    simple_repr.assert_called_once_with(self.category)
    self.assertEqual(result, simple_repr.return_value)

@patch('nuplan.database.nuplan_db_orm.category.default_color', autospec=True)
def test_color(self, default_color: Mock) -> None:
    """
        Tests color property
        """
    result = self.category.color
    default_color.assert_called_once_with(self.category.name)
    self.assertEqual(result, default_color.return_value)

@patch('nuplan.database.nuplan_db_orm.category.default_color_np', autospec=True)
def test_color_np(self, default_color_np: Mock) -> None:
    """
        Tests color_np property
        """
    result = self.category.color_np
    default_color_np.assert_called_once_with(self.category.name)
    self.assertEqual(result, default_color_np.return_value)

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

class TestLidar(unittest.TestCase):
    """Test class Lidar"""

    def setUp(self) -> None:
        """
        Initializes a test Lidar
        """
        self.lidar = get_test_nuplan_lidar()

    @patch('nuplan.database.nuplan_db_orm.lidar.inspect', autospec=True)
    def test_session(self, inspect: Mock) -> None:
        """
        Tests _session method
        """
        mock_session = PropertyMock()
        inspect.return_value = Mock()
        inspect.return_value.session = mock_session
        result = self.lidar._session()
        inspect.assert_called_once_with(self.lidar)
        mock_session.assert_called_once()
        self.assertEqual(result, mock_session.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar.simple_repr', autospec=True)
    def test_repr(self, simple_repr: Mock) -> None:
        """
        Tests string representation
        """
        result = self.lidar.__repr__()
        simple_repr.assert_called_once_with(self.lidar)
        self.assertEqual(result, simple_repr.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar.np.array', autospec=True)
    def test_translation_np(self, np_array: Mock) -> None:
        """
        Test property - translation.
        """
        result = self.lidar.translation_np
        np_array.assert_called_once_with(self.lidar.translation)
        self.assertEqual(result, np_array.return_value)

    def test_quaternion(self) -> None:
        """
        Test property - rotation in quaternion.
        """
        result = self.lidar.quaternion
        np.testing.assert_array_equal(self.lidar.rotation, result.elements)

    def test_trans_matrix_and_inv(self) -> None:
        """
        Test two properties - transformation matrix and its inverse.
        """
        trans_mat = self.lidar.trans_matrix
        inv_trans_mat = self.lidar.trans_matrix_inv
        np.testing.assert_allclose(trans_mat @ inv_trans_mat, np.eye(4), atol=0.001)

@patch('nuplan.database.nuplan_db_orm.lidar.inspect', autospec=True)
def test_session(self, inspect: Mock) -> None:
    """
        Tests _session method
        """
    mock_session = PropertyMock()
    inspect.return_value = Mock()
    inspect.return_value.session = mock_session
    result = self.lidar._session()
    inspect.assert_called_once_with(self.lidar)
    mock_session.assert_called_once()
    self.assertEqual(result, mock_session.return_value)

@patch('nuplan.database.nuplan_db_orm.lidar.simple_repr', autospec=True)
def test_repr(self, simple_repr: Mock) -> None:
    """
        Tests string representation
        """
    result = self.lidar.__repr__()
    simple_repr.assert_called_once_with(self.lidar)
    self.assertEqual(result, simple_repr.return_value)

@patch('nuplan.database.nuplan_db_orm.lidar.np.array', autospec=True)
def test_translation_np(self, np_array: Mock) -> None:
    """
        Test property - translation.
        """
    result = self.lidar.translation_np
    np_array.assert_called_once_with(self.lidar.translation)
    self.assertEqual(result, np_array.return_value)

class TestScene(unittest.TestCase):
    """Test class Scene"""

    def setUp(self) -> None:
        """Sets up for the test cases"""
        self.scene = Scene()

    @patch('nuplan.database.nuplan_db_orm.scene.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the repr method"""
        result = self.scene.__repr__()
        simple_repr_mock.assert_called_once_with(self.scene)
        self.assertEqual(result, simple_repr_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.scene.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.scene._session()
        inspect_mock.assert_called_once_with(self.scene)
        self.assertEqual(result, session_mock.return_value)

@patch('nuplan.database.nuplan_db_orm.scene.simple_repr', autospec=True)
def test_repr(self, simple_repr_mock: Mock) -> None:
    """Tests the repr method"""
    result = self.scene.__repr__()
    simple_repr_mock.assert_called_once_with(self.scene)
    self.assertEqual(result, simple_repr_mock.return_value)

@patch('nuplan.database.nuplan_db_orm.scene.inspect', autospec=True)
def test_session(self, inspect_mock: Mock) -> None:
    """Tests the session property"""
    session_mock = PropertyMock()
    inspect_mock.return_value = Mock()
    inspect_mock.return_value.session = session_mock
    result = self.scene._session()
    inspect_mock.assert_called_once_with(self.scene)
    self.assertEqual(result, session_mock.return_value)

class TestHarmonicMean(unittest.TestCase):
    """Test weighted_harmonic_mean calculation."""

    def test_simple(self) -> None:
        """Test agreement between x, differing weights have no effect."""
        x = [1.0, 1.0]
        for i in range(1, 20):
            w = [i, 1.0]
            hm = measure.weighted_harmonic_mean(x, w)
            self.assertEqual(hm, 1.0)

    def test_different_x(self) -> None:
        """Test different x's, now weights are important."""
        x = [2.0, 1.0]
        w = [2.0, 1.0]
        hm1 = measure.weighted_harmonic_mean(x, w)
        w = [1.0, 2.0]
        hm2 = measure.weighted_harmonic_mean(x, w)
        self.assertEqual(hm1 > hm2, True)

    def test_math(self) -> None:
        """Test the math calculation."""
        x = [1.5, 1.25]
        w = [2.0, 1.0]
        hm = measure.weighted_harmonic_mean(x, w)
        self.assertEqual(hm, 1.40625)

    def test_cornercases(self) -> None:
        """Test corner case of zeros."""
        x = [0.0, 0.0]
        w = [2.0, 1.0]
        hm = measure.weighted_harmonic_mean(x, w)
        self.assertEqual(hm, 0)

def test_simple(self) -> None:
    """Test agreement between x, differing weights have no effect."""
    x = [1.0, 1.0]
    for i in range(1, 20):
        w = [i, 1.0]
        hm = measure.weighted_harmonic_mean(x, w)
        self.assertEqual(hm, 1.0)

def test_different_x(self) -> None:
    """Test different x's, now weights are important."""
    x = [2.0, 1.0]
    w = [2.0, 1.0]
    hm1 = measure.weighted_harmonic_mean(x, w)
    w = [1.0, 2.0]
    hm2 = measure.weighted_harmonic_mean(x, w)
    self.assertEqual(hm1 > hm2, True)

def test_math(self) -> None:
    """Test the math calculation."""
    x = [1.5, 1.25]
    w = [2.0, 1.0]
    hm = measure.weighted_harmonic_mean(x, w)
    self.assertEqual(hm, 1.40625)

def test_cornercases(self) -> None:
    """Test corner case of zeros."""
    x = [0.0, 0.0]
    w = [2.0, 1.0]
    hm = measure.weighted_harmonic_mean(x, w)
    self.assertEqual(hm, 0)

class TestDrawMasks(unittest.TestCase):
    """Test draw_masks function."""

    @mock.patch('nuplan.database.utils.plot._color_prep')
    def test_draw_masks(self, mock__color_prep) -> None:
        """Test Drawing Masks on Image."""
        test_image = np.zeros((100, 100, 3), np.uint8)
        test_image[0:50, 0:50, :] = (255, 0, 0)
        test_image[0:50, 50:100, :] = (0, 255, 0)
        test_image[50:100, 0:50, :] = (0, 0, 255)
        test_image[50:, 50:, :] = (255, 255, 255)
        test_target = np.zeros((100, 100))
        test_target[:50, :50] = 1
        test_target[:50, 50:] = 2
        test_target[50:, :50] = 3
        test_target[50:, 50:] = 4
        colors = {1: (255, 0, 0, 255), 2: (0, 255, 0, 255), 3: (0, 0, 255, 255), 4: (255, 255, 255, 255)}
        mock__color_prep.return_value = colors
        input_image = Image.fromarray(np.zeros((100, 100, 3), np.uint8))
        draw_masks(input_image, test_target, ncolors=4, colors=colors, alpha=255)
        mock__color_prep.assert_called_with(4, 255, colors)
        input_image = np.array(input_image)
        self.assertEqual(np.array_equal(input_image, test_image), True)

@mock.patch('nuplan.database.utils.plot._color_prep')
def test_draw_masks(self, mock__color_prep) -> None:
    """Test Drawing Masks on Image."""
    test_image = np.zeros((100, 100, 3), np.uint8)
    test_image[0:50, 0:50, :] = (255, 0, 0)
    test_image[0:50, 50:100, :] = (0, 255, 0)
    test_image[50:100, 0:50, :] = (0, 0, 255)
    test_image[50:, 50:, :] = (255, 255, 255)
    test_target = np.zeros((100, 100))
    test_target[:50, :50] = 1
    test_target[:50, 50:] = 2
    test_target[50:, :50] = 3
    test_target[50:, 50:] = 4
    colors = {1: (255, 0, 0, 255), 2: (0, 255, 0, 255), 3: (0, 0, 255, 255), 4: (255, 255, 255, 255)}
    mock__color_prep.return_value = colors
    input_image = Image.fromarray(np.zeros((100, 100, 3), np.uint8))
    draw_masks(input_image, test_target, ncolors=4, colors=colors, alpha=255)
    mock__color_prep.assert_called_with(4, 255, colors)
    input_image = np.array(input_image)
    self.assertEqual(np.array_equal(input_image, test_image), True)

class TestIterableLidarBox(unittest.TestCase):
    """Tests the IterableLidarBox class and it's methods"""

    def test_IterableLidarBox_init(self) -> None:
        """Checks the correctness of the `IterableLidarBox` class' constructor."""
        box = Mock()
        iterable = IterableLidarBox(box)
        box.get_box_items_to_iterate.assert_called_once()
        self.assertEqual(iterable._begin, box)
        self.assertEqual(iterable.box, box)
        self.assertEqual(iterable._current, box)
        self.assertEqual(iterable._reverse, False)
        self.assertEqual(iterable._items_dict, box.get_box_items_to_iterate.return_value)

    def test_IterableLidarBox_iter(self) -> None:
        """Checks the correctness of the `IterableLidarBox` class' `__iter__` method."""
        box = Mock()
        iterable = IterableLidarBox(box)
        iter_val = iter(iterable)
        self.assertEqual(iterable, iter_val)

    def test_IterableLidarBox_next_not_end(self) -> None:
        """
        Checks the correctness of the `IterableLidarBox` class' `__next__` method.
         When the current box is not the end box, the current box should be returned
         and the `.next` box should become the current one.
        """
        box = Mock()
        box.timestamp = 1
        box.get_box_items_to_iterate.return_value = {1: (Mock(), Mock())}
        iterable = IterableLidarBox(box)
        result = next(iterable)
        self.assertEqual(result, box)
        self.assertEqual(iterable._current, box.get_box_items_to_iterate.return_value[1][1])

    def test_IterableLidarBox_getitem(self) -> None:
        """
        Checks the correctness of the `IterableLidarBox` class' `__getitem__` method.
        Should return the box at the given index.
        """
        box = Mock()
        box.timestamp = 1
        box.get_box_items_to_iterate.return_value = {1: (Mock(), Mock())}
        iterable = IterableLidarBox(box)
        box_0 = iterable[0]
        self.assertEqual(box_0, box)

def test_IterableLidarBox_init(self) -> None:
    """Checks the correctness of the `IterableLidarBox` class' constructor."""
    box = Mock()
    iterable = IterableLidarBox(box)
    box.get_box_items_to_iterate.assert_called_once()
    self.assertEqual(iterable._begin, box)
    self.assertEqual(iterable.box, box)
    self.assertEqual(iterable._current, box)
    self.assertEqual(iterable._reverse, False)
    self.assertEqual(iterable._items_dict, box.get_box_items_to_iterate.return_value)

def test_IterableLidarBox_iter(self) -> None:
    """Checks the correctness of the `IterableLidarBox` class' `__iter__` method."""
    box = Mock()
    iterable = IterableLidarBox(box)
    iter_val = iter(iterable)
    self.assertEqual(iterable, iter_val)

def test_IterableLidarBox_next_not_end(self) -> None:
    """
        Checks the correctness of the `IterableLidarBox` class' `__next__` method.
         When the current box is not the end box, the current box should be returned
         and the `.next` box should become the current one.
        """
    box = Mock()
    box.timestamp = 1
    box.get_box_items_to_iterate.return_value = {1: (Mock(), Mock())}
    iterable = IterableLidarBox(box)
    result = next(iterable)
    self.assertEqual(result, box)
    self.assertEqual(iterable._current, box.get_box_items_to_iterate.return_value[1][1])

def test_IterableLidarBox_getitem(self) -> None:
    """
        Checks the correctness of the `IterableLidarBox` class' `__getitem__` method.
        Should return the box at the given index.
        """
    box = Mock()
    box.timestamp = 1
    box.get_box_items_to_iterate.return_value = {1: (Mock(), Mock())}
    iterable = IterableLidarBox(box)
    box_0 = iterable[0]
    self.assertEqual(box_0, box)

class TestImageMock(unittest.TestCase):
    """Test suite for the Image class using mocks."""
    TEST_PATH = 'nuplan.database.utils.image'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.mock_pil_img = MagicMock(PilImg.Image)
        self.image = Image(self.mock_pil_img)

    def test_as_pil(self) -> None:
        """Test the function as_pil."""
        img = self.image.as_pil
        self.assertEqual(self.mock_pil_img, img)

    @patch(f'{TEST_PATH}.np.array', autospec=True)
    def test_as_numpy_nocache(self, mock_array: Mock) -> None:
        """Test the function as_numpy_nocache."""
        _ = self.image.as_numpy_nocache()
        mock_array.assert_called_with(self.mock_pil_img, dtype=np.uint8)

    @patch(f'{TEST_PATH}.Image.as_numpy_nocache', autospec=True)
    def test_as_numpy(self, mock_as_numpy_nocache: Mock) -> None:
        """Test the function as_numpy_nocache."""
        _ = self.image.as_numpy
        mock_as_numpy_nocache.assert_called_once()

    @patch(f'{TEST_PATH}.cv2.cvtColor', autospec=True)
    @patch(f'{TEST_PATH}.np.array', autospec=True)
    def test_as_cv2_nocache(self, mock_array: Mock, mock_cvtcolor: Mock) -> None:
        """Test the function as_cv2_nocache."""
        _ = self.image.as_cv2_nocache()
        mock_cvtcolor.assert_called_with(mock_array(self.mock_pil_img, np.uint8), cv2.COLOR_RGB2BGR)

    @patch(f'{TEST_PATH}.Image.as_cv2_nocache', autospec=True)
    def test_as_cv2(self, mock_as_cv2_nocache: Mock) -> None:
        """Test the function as_numpy_nocache."""
        _ = self.image.as_cv2
        mock_as_cv2_nocache.assert_called_once()

def setUp(self) -> None:
    """Inherited, see superclass"""
    self.mock_pil_img = MagicMock(PilImg.Image)
    self.image = Image(self.mock_pil_img)

def test_as_pil(self) -> None:
    """Test the function as_pil."""
    img = self.image.as_pil
    self.assertEqual(self.mock_pil_img, img)

@patch(f'{TEST_PATH}.np.array', autospec=True)
def test_as_numpy_nocache(self, mock_array: Mock) -> None:
    """Test the function as_numpy_nocache."""
    _ = self.image.as_numpy_nocache()
    mock_array.assert_called_with(self.mock_pil_img, dtype=np.uint8)

@patch(f'{TEST_PATH}.Image.as_numpy_nocache', autospec=True)
def test_as_numpy(self, mock_as_numpy_nocache: Mock) -> None:
    """Test the function as_numpy_nocache."""
    _ = self.image.as_numpy
    mock_as_numpy_nocache.assert_called_once()

@patch(f'{TEST_PATH}.cv2.cvtColor', autospec=True)
@patch(f'{TEST_PATH}.np.array', autospec=True)
def test_as_cv2_nocache(self, mock_array: Mock, mock_cvtcolor: Mock) -> None:
    """Test the function as_cv2_nocache."""
    _ = self.image.as_cv2_nocache()
    mock_cvtcolor.assert_called_with(mock_array(self.mock_pil_img, np.uint8), cv2.COLOR_RGB2BGR)

@patch(f'{TEST_PATH}.Image.as_cv2_nocache', autospec=True)
def test_as_cv2(self, mock_as_cv2_nocache: Mock) -> None:
    """Test the function as_numpy_nocache."""
    _ = self.image.as_cv2
    mock_as_cv2_nocache.assert_called_once()

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

def setUp(self) -> None:
    """Inherited, see superclass"""
    pil_img: PilImg.Image = PilImg.new('RGB', (500, 500))
    self.image = Image(pil_img)

def get_lidarpc_sensor_data() -> SensorDataSource:
    """
    Builds the SensorDataSource for a lidar_pc.
    :return: The query parameters for lidar_pc.
    """
    return SensorDataSource('lidar_pc', 'lidar', 'lidar_token', 'MergedPointCloud')

def get_camera_channel_sensor_data(channel: str) -> SensorDataSource:
    """
    Builds the SensorDataSource for image from a specified channel.
    :param channel: The channel to select.
    :return: The query parameters for image.
    """
    return SensorDataSource('image', 'camera', 'camera_token', channel)

class TestDbCliQueries(unittest.TestCase):
    """
    Test suite for the DB Cli queries.
    """

    @staticmethod
    def getDBFilePath() -> Path:
        """
        Get the location for the temporary SQLite file used for the test DB.
        :return: The filepath for the test data.
        """
        return Path('/tmp/test_db_cli_queries.sqlite3')

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create the mock DB data.
        """
        db_file_path = TestDbCliQueries.getDBFilePath()
        if db_file_path.exists():
            db_file_path.unlink()
        generation_parameters = DBGenerationParameters(num_lidars=1, num_cameras=2, num_sensor_data_per_sensor=50, num_lidarpc_per_image_ratio=2, num_scenes=10, num_traffic_lights_per_lidar_pc=5, num_agents_per_lidar_pc=3, num_static_objects_per_lidar_pc=2, scene_scenario_tag_mapping={5: ['first_tag'], 6: ['first_tag', 'second_tag']}, file_path=str(db_file_path))
        generate_minimal_nuplan_db(generation_parameters)

    def setUp(self) -> None:
        """
        The method to run before each test.
        """
        self.db_file_name = str(TestDbCliQueries.getDBFilePath())

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Destroy the mock DB data.
        """
        db_file_path = TestDbCliQueries.getDBFilePath()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    def test_get_db_description(self) -> None:
        """
        Test the get_db_description queries.
        """
        db_description = get_db_description(self.db_file_name)
        expected_tables = ['category', 'ego_pose', 'lidar', 'lidar_box', 'lidar_pc', 'log', 'scenario_tag', 'scene', 'track', 'traffic_light_status', 'camera', 'image']
        self.assertEqual(len(expected_tables), len(db_description.tables))
        for expected_table in expected_tables:
            self.assertTrue(expected_table in db_description.tables)
        lidar_pc_table = db_description.tables['lidar_pc']
        self.assertEqual('lidar_pc', lidar_pc_table.name)
        self.assertEqual(50, lidar_pc_table.row_count)
        self.assertEqual(8, len(lidar_pc_table.columns))
        columns = sorted(lidar_pc_table.columns.values(), key=lambda x: x.column_id)

        def _validate_column(column: ColumnDescription, expected_id: int, expected_name: str, expected_data_type: str, expected_nullable: bool, expected_is_primary_key: bool) -> None:
            """
            A quick method to validate column info to reduce boilerplate.
            """
            self.assertEqual(expected_id, column.column_id)
            self.assertEqual(expected_name, column.name)
            self.assertEqual(expected_data_type, column.data_type)
            self.assertEqual(expected_nullable, column.nullable)
            self.assertEqual(expected_is_primary_key, column.is_primary_key)
        _validate_column(columns[0], 0, 'token', 'BLOB', False, True)
        _validate_column(columns[1], 1, 'next_token', 'BLOB', True, False)
        _validate_column(columns[2], 2, 'prev_token', 'BLOB', True, False)
        _validate_column(columns[3], 3, 'ego_pose_token', 'BLOB', False, False)
        _validate_column(columns[4], 4, 'lidar_token', 'BLOB', False, False)
        _validate_column(columns[5], 5, 'scene_token', 'BLOB', True, False)
        _validate_column(columns[6], 6, 'filename', 'VARCHAR(128)', True, False)
        _validate_column(columns[7], 7, 'timestamp', 'INTEGER', True, False)

    def test_get_db_duration_in_us(self) -> None:
        """
        Test the get_db_duration_in_us query
        """
        duration = get_db_duration_in_us(self.db_file_name)
        self.assertEqual(49 * 1000000.0, duration)

    def test_get_db_log_duration(self) -> None:
        """
        Test the get_db_log_duration query.
        """
        log_durations = list(get_db_log_duration(self.db_file_name))
        self.assertEqual(1, len(log_durations))
        self.assertEqual('logfile', log_durations[0][0])
        self.assertEqual(49 * 1000000.0, log_durations[0][1])

    def test_get_db_log_vehicles(self) -> None:
        """
        Test the get_db_log_vehicles query.
        """
        log_vehicles = list(get_db_log_vehicles(self.db_file_name))
        self.assertEqual(1, len(log_vehicles))
        self.assertEqual('logfile', log_vehicles[0][0])
        self.assertEqual('vehicle_name', log_vehicles[0][1])

    def test_get_db_scenario_info(self) -> None:
        """
        Test the get_db_scenario_info query.
        """
        scenario_info_tags = list(get_db_scenario_info(self.db_file_name))
        self.assertEqual(2, len(scenario_info_tags))
        self.assertEqual('first_tag', scenario_info_tags[0][0])
        self.assertEqual(2, scenario_info_tags[0][1])
        self.assertEqual('second_tag', scenario_info_tags[1][0])
        self.assertEqual(1, scenario_info_tags[1][1])

def _validate_column(column: ColumnDescription, expected_id: int, expected_name: str, expected_data_type: str, expected_nullable: bool, expected_is_primary_key: bool) -> None:
    """
            A quick method to validate column info to reduce boilerplate.
            """
    self.assertEqual(expected_id, column.column_id)
    self.assertEqual(expected_name, column.name)
    self.assertEqual(expected_data_type, column.data_type)
    self.assertEqual(expected_nullable, column.nullable)
    self.assertEqual(expected_is_primary_key, column.is_primary_key)

class TestSensorDataSource(unittest.TestCase):
    """Tests for the SensorDataSource class."""

    def test_initialization(self) -> None:
        """Tests correct initialization and raising of invalid configuration."""
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: camera for table lidar_pc'):
            SensorDataSource('lidar_pc', 'camera', 'camera_token', '')
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_table: lidar for table image'):
            SensorDataSource('image', 'lidar', 'lidar_token', '')
        with self.assertRaisesRegex(ValueError, 'Unknown requested sensor table: unknown'):
            SensorDataSource('unknown', '', '', '')
        with self.assertRaisesRegex(AssertionError, 'Incompatible sensor_token_column: lidar_token for sensor_table camera'):
            SensorDataSource('image', 'camera', 'lidar_token', '')
        _ = SensorDataSource('lidar_pc', 'lidar', 'lidar_token', '')
        valid_sensor_data_source = SensorDataSource('image', 'camera', 'camera_token', 'channel')
        self.assertEqual(valid_sensor_data_source.table, 'image')
        self.assertEqual(valid_sensor_data_source.sensor_table, 'camera')
        self.assertEqual(valid_sensor_data_source.sensor_token_column, 'camera_token')
        self.assertEqual(valid_sensor_data_source.channel, 'channel')

    def test_get_lidarpc_sensor_data(self) -> None:
        """Tests that utility function builds the correct object."""
        sensor_data = get_lidarpc_sensor_data()
        self.assertEqual(sensor_data.table, 'lidar_pc')
        self.assertEqual(sensor_data.sensor_table, 'lidar')
        self.assertEqual(sensor_data.sensor_token_column, 'lidar_token')
        self.assertEqual(sensor_data.channel, 'MergedPointCloud')

    def test_get_camera_channel_sensor_data(self) -> None:
        """Tests that utility function builds the correct object."""
        sensor_data = get_camera_channel_sensor_data('channel')
        self.assertEqual(sensor_data.table, 'image')
        self.assertEqual(sensor_data.sensor_table, 'camera')
        self.assertEqual(sensor_data.sensor_token_column, 'camera_token')
        self.assertEqual(sensor_data.channel, 'channel')

def test_get_lidarpc_sensor_data(self) -> None:
    """Tests that utility function builds the correct object."""
    sensor_data = get_lidarpc_sensor_data()
    self.assertEqual(sensor_data.table, 'lidar_pc')
    self.assertEqual(sensor_data.sensor_table, 'lidar')
    self.assertEqual(sensor_data.sensor_token_column, 'lidar_token')
    self.assertEqual(sensor_data.channel, 'MergedPointCloud')

def test_get_camera_channel_sensor_data(self) -> None:
    """Tests that utility function builds the correct object."""
    sensor_data = get_camera_channel_sensor_data('channel')
    self.assertEqual(sensor_data.table, 'image')
    self.assertEqual(sensor_data.sensor_table, 'camera')
    self.assertEqual(sensor_data.sensor_token_column, 'camera_token')
    self.assertEqual(sensor_data.channel, 'channel')

class TestNuPlanScenarioQueries(unittest.TestCase):
    """
    Test suite for the NuPlan scenario queries.
    """
    generation_parameters: DBGenerationParameters

    @staticmethod
    def getDBFilePath() -> Path:
        """
        Get the location for the temporary SQLite file used for the test DB.
        :return: The filepath for the test data.
        """
        return Path('/tmp/test_nuplan_scenario_queries.sqlite3')

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create the mock DB data.
        """
        db_file_path = TestNuPlanScenarioQueries.getDBFilePath()
        if db_file_path.exists():
            db_file_path.unlink()
        cls.generation_parameters = DBGenerationParameters(num_lidars=1, num_cameras=2, num_sensor_data_per_sensor=50, num_lidarpc_per_image_ratio=2, num_scenes=10, num_traffic_lights_per_lidar_pc=5, num_agents_per_lidar_pc=3, num_static_objects_per_lidar_pc=2, scene_scenario_tag_mapping={5: ['first_tag'], 6: ['first_tag', 'second_tag'], 7: ['second_tag']}, file_path=str(db_file_path))
        generate_minimal_nuplan_db(cls.generation_parameters)

    def setUp(self) -> None:
        """
        The method to run before each test.
        """
        self.db_file_name = str(TestNuPlanScenarioQueries.getDBFilePath())
        self.sensor_source = SensorDataSource('lidar_pc', 'lidar', 'lidar_token', 'channel')

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Destroy the mock DB data.
        """
        db_file_path = TestNuPlanScenarioQueries.getDBFilePath()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    def test_get_sensor_token_from_index(self) -> None:
        """
        Test the get_sensor_token_from_index query.
        """
        for sample_index in [0, 12, 24]:
            retrieved_token = get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, sample_index)
            self.assertEqual(sample_index / self.generation_parameters.num_lidars, str_token_to_int(retrieved_token))
        self.assertIsNone(get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, 100000))
        with self.assertRaises(ValueError):
            get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, -2)

    def test_get_end_sensor_time_from_db(self) -> None:
        """
        Test the get_end_sensor_time_from_db query.
        """
        log_end_time = get_end_sensor_time_from_db(self.db_file_name, sensor_source=self.sensor_source)
        self.assertEqual(49 * 1000000.0, log_end_time)

    def test_get_sensor_token_timestamp_from_db(self) -> None:
        """
        Test the get_sensor_data_token_timestamp_from_db query.
        """
        for token in [0, 3, 7]:
            expected_timestamp = token * 1000000.0
            actual_timestamp = get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
            self.assertEqual(expected_timestamp, actual_timestamp)
        self.assertIsNone(get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

    def test_get_sensor_token_map_name_from_db(self) -> None:
        """
        Test the get_sensor_token_map_name_from_db query.
        """
        for token in [0, 2, 6]:
            expected_map_name = 'map_version'
            actual_map_name = get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
            self.assertEqual(expected_map_name, actual_map_name)
        self.assertIsNone(get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

    def test_get_sampled_sensor_tokens_in_time_window_from_db(self) -> None:
        """
        Test the get_sampled_lidarpc_tokens_in_time_window_from_db query.
        """
        expected_tokens = [10, 13, 16, 19]
        actual_tokens = list((str_token_to_int(v) for v in get_sampled_sensor_tokens_in_time_window_from_db(log_file=self.db_file_name, sensor_source=self.sensor_source, start_timestamp=int(10 * 1000000.0), end_timestamp=int(20 * 1000000.0), subsample_interval=3)))
        self.assertEqual(expected_tokens, actual_tokens)

    def test_get_sensor_data_from_sensor_data_tokens_from_db(self) -> None:
        """
        Test the get_sensor_data_from_sensor_data_tokens_from_db query.
        """
        lidar_pc_tokens = [int_to_str_token(v) for v in [10, 13, 21]]
        image_tokens = [int_to_str_token(v) for v in [1100000]]
        lidar_pcs = [cast(LidarPc, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, self.sensor_source, LidarPc, lidar_pc_tokens)]
        images = [cast(Image, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, SensorDataSource('image', 'camera', 'camera_token', 'camera_0'), Image, image_tokens)]
        self.assertEqual(len(lidar_pc_tokens), len(lidar_pcs))
        self.assertEqual(len(image_tokens), len(images))
        lidar_pcs.sort(key=lambda x: int(x.timestamp))
        self.assertEqual(10, str_token_to_int(lidar_pcs[0].token))
        self.assertEqual(13, str_token_to_int(lidar_pcs[1].token))
        self.assertEqual(21, str_token_to_int(lidar_pcs[2].token))
        self.assertEqual(1100000, str_token_to_int(images[0].token))

    def test_get_lidar_transform_matrix_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_sensor_transform_matrix_for_sensor_data_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            xform_mat = get_sensor_transform_matrix_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, int_to_str_token(sample_token))
            self.assertIsNotNone(xform_mat)
            self.assertEqual(xform_mat[0, 3], 0)

    def test_get_mission_goal_for_sensor_data_token_from_db(self) -> None:
        """
        Test the get_mission_goal_for_sensor_data_token_from_db query.
        """
        query_lidarpc_token = int_to_str_token(12)
        expected_ego_pose_x = 14
        expected_ego_pose_y = 15
        result = get_mission_goal_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, query_lidarpc_token)
        self.assertIsNotNone(result)
        self.assertEqual(expected_ego_pose_x, result.x)
        self.assertEqual(expected_ego_pose_y, result.y)

    def test_get_roadblock_ids_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_roadblock_ids_for_lidarpc_token_from_db query.
        """
        result = get_roadblock_ids_for_lidarpc_token_from_db(self.db_file_name, int_to_str_token(0))
        self.assertEqual(result, ['0', '1', '2'])

    def test_get_statese2_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_statese2_for_lidarpc_token_from_db query.
        """
        query_lidarpc_token = int_to_str_token(13)
        expected_ego_pose_x = 13
        expected_ego_pose_y = 14
        result = get_statese2_for_lidarpc_token_from_db(self.db_file_name, query_lidarpc_token)
        self.assertIsNotNone(result)
        self.assertEqual(expected_ego_pose_x, result.x)
        self.assertEqual(expected_ego_pose_y, result.y)

    def test_get_sampled_lidarpcs_from_db(self) -> None:
        """
        Test the get_sampled_lidarpcs_from_db query.
        """
        test_cases = [{'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': True, 'expected_return_tokens': [5, 6, 7]}, {'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': False, 'expected_return_tokens': [3, 4, 5]}, {'initial_token': 7, 'sample_indexes': [0, 3, 12], 'future': False, 'expected_return_tokens': [4, 7]}, {'initial_token': 0, 'sample_indexes': [1000], 'future': True, 'expected_return_tokens': []}]
        for test_case in test_cases:
            initial_token = int_to_str_token(test_case['initial_token'])
            expected_return_tokens = [int_to_str_token(v) for v in test_case['expected_return_tokens']]
            actual_returned_lidarpcs = list(get_sampled_lidarpcs_from_db(self.db_file_name, initial_token, self.sensor_source, test_case['sample_indexes'], test_case['future']))
            self.assertEqual(len(expected_return_tokens), len(actual_returned_lidarpcs))
            for i in range(len(expected_return_tokens)):
                self.assertEqual(expected_return_tokens[i], actual_returned_lidarpcs[i].token)

    def test_get_sampled_ego_states_from_db(self) -> None:
        """
        Test the get_sampled_ego_states_from_db query.
        """
        test_cases = [{'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': True, 'expected_row_indexes': [5, 6, 7]}, {'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': False, 'expected_row_indexes': [3, 4, 5]}, {'initial_token': 7, 'sample_indexes': [0, 3, 12], 'future': False, 'expected_row_indexes': [4, 7]}, {'initial_token': 0, 'sample_indexes': [1000], 'future': True, 'expected_row_indexes': []}]
        for test_case in test_cases:
            initial_token = int_to_str_token(test_case['initial_token'])
            expected_row_indexes = test_case['expected_row_indexes']
            actual_returned_ego_states = list(get_sampled_ego_states_from_db(self.db_file_name, initial_token, self.sensor_source, test_case['sample_indexes'], test_case['future']))
            self.assertEqual(len(expected_row_indexes), len(actual_returned_ego_states))
            for i in range(len(expected_row_indexes)):
                self.assertEqual(expected_row_indexes[i] * 1000000.0, actual_returned_ego_states[i].time_point.time_us)

    def test_get_ego_state_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_ego_state_for_lidarpc_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            returned_pose = get_ego_state_for_lidarpc_token_from_db(self.db_file_name, query_token)
            self.assertEqual(sample_token * 1000000.0, returned_pose.time_point.time_us)

    def test_get_traffic_light_status_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_traffic_light_status_for_lidarpc_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            traffic_light_statuses = list(get_traffic_light_status_for_lidarpc_token_from_db(self.db_file_name, query_token))
            self.assertEqual(5, len(traffic_light_statuses))
            for tl_status in traffic_light_statuses:
                self.assertEqual(sample_token * 1000000.0, tl_status.timestamp)

    def test_get_tracked_objects_for_lidarpc_token_from_db(self) -> None:
        """
        Test the get_tracked_objects_for_token_from_db query.
        """
        for sample_token in [0, 30, 49]:
            query_token = int_to_str_token(sample_token)
            tracked_objects = list(get_tracked_objects_for_lidarpc_token_from_db(self.db_file_name, query_token))
            self.assertEqual(5, len(tracked_objects))
            agent_count = 0
            static_object_count = 0
            track_token_base_id = 600000
            token_base_id = 500000
            token_sample_step = 10000
            for idx, tracked_object in enumerate(tracked_objects):
                expected_track_token = track_token_base_id + idx
                expected_token = token_base_id + token_sample_step * sample_token + idx
                self.assertEqual(int_to_str_token(expected_track_token), tracked_object.track_token)
                self.assertEqual(int_to_str_token(expected_token), tracked_object.token)
                if isinstance(tracked_object, Agent):
                    agent_count += 1
                    self.assertEqual(TrackedObjectType.VEHICLE, tracked_object.tracked_object_type)
                    self.assertEqual(0, len(tracked_object.predictions))
                elif isinstance(tracked_object, StaticObject):
                    static_object_count += 1
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, tracked_object.tracked_object_type)
                else:
                    raise ValueError(f'Unexpected type: {type(tracked_object)}')
            self.assertEqual(3, agent_count)
            self.assertEqual(2, static_object_count)

    def test_get_tracked_objects_within_time_interval_from_db(self) -> None:
        """
        Test the get_tracked_objects_within_time_interval_from_db query.
        """
        expected_num_windows = {0: 3, 30: 5, 48: 4}
        expected_backward_offset = {0: 0, 30: -2, 48: -2}
        for sample_token in expected_num_windows.keys():
            start_timestamp = int(1000000.0 * (sample_token - 2))
            end_timestamp = int(1000000.0 * (sample_token + 2))
            tracked_objects = list(get_tracked_objects_within_time_interval_from_db(self.db_file_name, start_timestamp, end_timestamp, filter_track_tokens=None))
            expected_num_tokens = expected_num_windows[sample_token] * 5
            self.assertEqual(expected_num_tokens, len(tracked_objects))
            agent_count = 0
            static_object_count = 0
            track_token_base_id = 600000
            token_base_id = 500000
            token_sample_step = 10000
            for idx, tracked_object in enumerate(tracked_objects):
                expected_track_token = track_token_base_id + idx % 5
                expected_token = token_base_id + token_sample_step * (sample_token + expected_backward_offset[sample_token] + math.floor(idx / 5)) + idx % 5
                self.assertEqual(int_to_str_token(expected_track_token), tracked_object.track_token)
                self.assertEqual(int_to_str_token(expected_token), tracked_object.token)
                if isinstance(tracked_object, Agent):
                    agent_count += 1
                    self.assertEqual(TrackedObjectType.VEHICLE, tracked_object.tracked_object_type)
                    self.assertEqual(0, len(tracked_object.predictions))
                elif isinstance(tracked_object, StaticObject):
                    static_object_count += 1
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, tracked_object.tracked_object_type)
                else:
                    raise ValueError(f'Unexpected type: {type(tracked_object)}')
            self.assertEqual(3 * expected_num_windows[sample_token], agent_count)
            self.assertEqual(2 * expected_num_windows[sample_token], static_object_count)

    def test_get_future_waypoints_for_agents_from_db(self) -> None:
        """
        Test the get_future_waypoints_for_agents_from_db query.
        """
        track_tokens = [600000, 600001, 600002]
        start_timestamp = 0
        end_timestamp = int(20 * 1000000.0 - 1)
        query_output: Dict[str, List[Waypoint]] = {}
        for token, waypoint in get_future_waypoints_for_agents_from_db(self.db_file_name, (int_to_str_token(t) for t in track_tokens), start_timestamp, end_timestamp):
            if token not in query_output:
                query_output[token] = []
            query_output[token].append(waypoint)
        expected_keys = ['{:08d}'.format(t) for t in track_tokens]
        self.assertEqual(len(expected_keys), len(query_output))
        for expected_key in expected_keys:
            self.assertTrue(expected_key in query_output)
            collected_waypoints = query_output[expected_key]
            self.assertEqual(20, len(collected_waypoints))
            for i in range(0, len(collected_waypoints), 1):
                self.assertEqual(i * 1000000.0, collected_waypoints[i].time_point.time_us)

    def test_get_scenarios_from_db(self) -> None:
        """
        Test the get_scenarios_from_db_query.
        """
        no_filter_output: List[int] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            no_filter_output.append(str_token_to_int(row['token'].hex()))
        self.assertEqual(list(range(10, 40, 1)), no_filter_output)
        filter_tokens = [int_to_str_token(v) for v in [15, 30]]
        tokens_filter_output: List[int] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=filter_tokens, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            tokens_filter_output.append(row['token'].hex())
        self.assertEqual(filter_tokens, tokens_filter_output)
        filter_scenarios = ['first_tag']
        extracted_rows: List[Tuple[int, str]] = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
        self.assertEqual(2, len(extracted_rows))
        self.assertEqual(25, extracted_rows[0][0])
        self.assertEqual('first_tag', extracted_rows[0][1])
        self.assertEqual(30, extracted_rows[1][0])
        self.assertEqual('first_tag', extracted_rows[1][1])
        filter_scenarios = ['second_tag']
        extracted_rows = []
        for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
            extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
        self.assertEqual(2, len(extracted_rows))
        self.assertEqual(30, extracted_rows[0][0])
        self.assertEqual('second_tag', extracted_rows[0][1])
        self.assertEqual(35, extracted_rows[1][0])
        self.assertEqual('second_tag', extracted_rows[1][1])
        filter_maps = ['map_version']
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
        self.assertLess(0, row_cnt)
        filter_maps = ['map_that_does_not_exist']
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
        self.assertEqual(0, row_cnt)
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=True)))
        self.assertEqual(15, row_cnt)
        row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=[int_to_str_token(25)], filter_types=['first_tag'], filter_map_names=['map_version'], include_invalid_mission_goals=False, include_cameras=False)))
        self.assertEqual(1, row_cnt)

    def test_get_lidarpc_tokens_with_scenario_tag_from_db(self) -> None:
        """
        Test the get_lidarpc_tokens_with_scenario_tag_from_db query.
        """
        tuples = list(get_lidarpc_tokens_with_scenario_tag_from_db(self.db_file_name))
        self.assertEqual(4, len(tuples))
        expected_tuples = [('first_tag', int_to_str_token(25)), ('first_tag', int_to_str_token(30)), ('second_tag', int_to_str_token(30)), ('second_tag', int_to_str_token(35))]
        for tup in tuples:
            self.assertTrue(tup in expected_tuples)

    def test_get_sensor_token(self) -> None:
        """Test the get_lidarpc_token_from_index query."""
        retrieved_token = get_sensor_token(self.db_file_name, 'lidar', 'channel')
        self.assertEqual(700000, str_token_to_int(retrieved_token))
        with self.assertRaisesRegex(RuntimeError, 'Channel missing_channel not found in table lidar!'):
            self.assertIsNone(get_sensor_token(self.db_file_name, 'lidar', 'missing_channel'))

    def test_get_images_from_lidar_tokens(self) -> None:
        """Test the get_images_from_lidar_tokens query."""
        token = int_to_str_token(20)
        retrieved_images = list(get_images_from_lidar_tokens(self.db_file_name, [token], ['camera_0', 'camera_1'], 50000, 50000))
        self.assertEqual(2, len(retrieved_images))
        self.assertEqual(1100020, str_token_to_int(retrieved_images[0].token))
        self.assertEqual(1100070, str_token_to_int(retrieved_images[1].token))
        self.assertEqual('camera_0', retrieved_images[0].channel)
        self.assertEqual('camera_1', retrieved_images[1].channel)

    def test_get_cameras(self) -> None:
        """Test the get_cameras query."""
        retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_0', 'camera_1']))
        self.assertEqual(2, len(retrieved_cameras))
        self.assertEqual(1000000, str_token_to_int(retrieved_cameras[0].token))
        self.assertEqual(1000001, str_token_to_int(retrieved_cameras[1].token))
        self.assertEqual('camera_0', retrieved_cameras[0].channel)
        self.assertEqual('camera_1', retrieved_cameras[1].channel)
        retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_1']))
        self.assertEqual(1, len(retrieved_cameras))
        self.assertEqual(1000001, str_token_to_int(retrieved_cameras[0].token))
        self.assertEqual('camera_1', retrieved_cameras[0].channel)

def test_get_sensor_token_from_index(self) -> None:
    """
        Test the get_sensor_token_from_index query.
        """
    for sample_index in [0, 12, 24]:
        retrieved_token = get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, sample_index)
        self.assertEqual(sample_index / self.generation_parameters.num_lidars, str_token_to_int(retrieved_token))
    self.assertIsNone(get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, 100000))
    with self.assertRaises(ValueError):
        get_sensor_token_by_index_from_db(self.db_file_name, self.sensor_source, -2)

def test_get_end_sensor_time_from_db(self) -> None:
    """
        Test the get_end_sensor_time_from_db query.
        """
    log_end_time = get_end_sensor_time_from_db(self.db_file_name, sensor_source=self.sensor_source)
    self.assertEqual(49 * 1000000.0, log_end_time)

def test_get_sensor_token_timestamp_from_db(self) -> None:
    """
        Test the get_sensor_data_token_timestamp_from_db query.
        """
    for token in [0, 3, 7]:
        expected_timestamp = token * 1000000.0
        actual_timestamp = get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
        self.assertEqual(expected_timestamp, actual_timestamp)
    self.assertIsNone(get_sensor_data_token_timestamp_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

def test_get_sensor_token_map_name_from_db(self) -> None:
    """
        Test the get_sensor_token_map_name_from_db query.
        """
    for token in [0, 2, 6]:
        expected_map_name = 'map_version'
        actual_map_name = get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(token))
        self.assertEqual(expected_map_name, actual_map_name)
    self.assertIsNone(get_sensor_token_map_name_from_db(self.db_file_name, self.sensor_source, int_to_str_token(1000)))

def test_get_sensor_data_from_sensor_data_tokens_from_db(self) -> None:
    """
        Test the get_sensor_data_from_sensor_data_tokens_from_db query.
        """
    lidar_pc_tokens = [int_to_str_token(v) for v in [10, 13, 21]]
    image_tokens = [int_to_str_token(v) for v in [1100000]]
    lidar_pcs = [cast(LidarPc, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, self.sensor_source, LidarPc, lidar_pc_tokens)]
    images = [cast(Image, sensor_data) for sensor_data in get_sensor_data_from_sensor_data_tokens_from_db(self.db_file_name, SensorDataSource('image', 'camera', 'camera_token', 'camera_0'), Image, image_tokens)]
    self.assertEqual(len(lidar_pc_tokens), len(lidar_pcs))
    self.assertEqual(len(image_tokens), len(images))
    lidar_pcs.sort(key=lambda x: int(x.timestamp))
    self.assertEqual(10, str_token_to_int(lidar_pcs[0].token))
    self.assertEqual(13, str_token_to_int(lidar_pcs[1].token))
    self.assertEqual(21, str_token_to_int(lidar_pcs[2].token))
    self.assertEqual(1100000, str_token_to_int(images[0].token))

def test_get_lidar_transform_matrix_for_lidarpc_token_from_db(self) -> None:
    """
        Test the get_sensor_transform_matrix_for_sensor_data_token_from_db query.
        """
    for sample_token in [0, 30, 49]:
        xform_mat = get_sensor_transform_matrix_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, int_to_str_token(sample_token))
        self.assertIsNotNone(xform_mat)
        self.assertEqual(xform_mat[0, 3], 0)

def test_get_mission_goal_for_sensor_data_token_from_db(self) -> None:
    """
        Test the get_mission_goal_for_sensor_data_token_from_db query.
        """
    query_lidarpc_token = int_to_str_token(12)
    expected_ego_pose_x = 14
    expected_ego_pose_y = 15
    result = get_mission_goal_for_sensor_data_token_from_db(self.db_file_name, self.sensor_source, query_lidarpc_token)
    self.assertIsNotNone(result)
    self.assertEqual(expected_ego_pose_x, result.x)
    self.assertEqual(expected_ego_pose_y, result.y)

def test_get_roadblock_ids_for_lidarpc_token_from_db(self) -> None:
    """
        Test the get_roadblock_ids_for_lidarpc_token_from_db query.
        """
    result = get_roadblock_ids_for_lidarpc_token_from_db(self.db_file_name, int_to_str_token(0))
    self.assertEqual(result, ['0', '1', '2'])

def test_get_statese2_for_lidarpc_token_from_db(self) -> None:
    """
        Test the get_statese2_for_lidarpc_token_from_db query.
        """
    query_lidarpc_token = int_to_str_token(13)
    expected_ego_pose_x = 13
    expected_ego_pose_y = 14
    result = get_statese2_for_lidarpc_token_from_db(self.db_file_name, query_lidarpc_token)
    self.assertIsNotNone(result)
    self.assertEqual(expected_ego_pose_x, result.x)
    self.assertEqual(expected_ego_pose_y, result.y)

def test_get_sampled_lidarpcs_from_db(self) -> None:
    """
        Test the get_sampled_lidarpcs_from_db query.
        """
    test_cases = [{'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': True, 'expected_return_tokens': [5, 6, 7]}, {'initial_token': 5, 'sample_indexes': [0, 1, 2], 'future': False, 'expected_return_tokens': [3, 4, 5]}, {'initial_token': 7, 'sample_indexes': [0, 3, 12], 'future': False, 'expected_return_tokens': [4, 7]}, {'initial_token': 0, 'sample_indexes': [1000], 'future': True, 'expected_return_tokens': []}]
    for test_case in test_cases:
        initial_token = int_to_str_token(test_case['initial_token'])
        expected_return_tokens = [int_to_str_token(v) for v in test_case['expected_return_tokens']]
        actual_returned_lidarpcs = list(get_sampled_lidarpcs_from_db(self.db_file_name, initial_token, self.sensor_source, test_case['sample_indexes'], test_case['future']))
        self.assertEqual(len(expected_return_tokens), len(actual_returned_lidarpcs))
        for i in range(len(expected_return_tokens)):
            self.assertEqual(expected_return_tokens[i], actual_returned_lidarpcs[i].token)

def test_get_ego_state_for_lidarpc_token_from_db(self) -> None:
    """
        Test the get_ego_state_for_lidarpc_token_from_db query.
        """
    for sample_token in [0, 30, 49]:
        query_token = int_to_str_token(sample_token)
        returned_pose = get_ego_state_for_lidarpc_token_from_db(self.db_file_name, query_token)
        self.assertEqual(sample_token * 1000000.0, returned_pose.time_point.time_us)

def test_get_scenarios_from_db(self) -> None:
    """
        Test the get_scenarios_from_db_query.
        """
    no_filter_output: List[int] = []
    for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
        no_filter_output.append(str_token_to_int(row['token'].hex()))
    self.assertEqual(list(range(10, 40, 1)), no_filter_output)
    filter_tokens = [int_to_str_token(v) for v in [15, 30]]
    tokens_filter_output: List[int] = []
    for row in get_scenarios_from_db(self.db_file_name, filter_tokens=filter_tokens, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
        tokens_filter_output.append(row['token'].hex())
    self.assertEqual(filter_tokens, tokens_filter_output)
    filter_scenarios = ['first_tag']
    extracted_rows: List[Tuple[int, str]] = []
    for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
        extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
    self.assertEqual(2, len(extracted_rows))
    self.assertEqual(25, extracted_rows[0][0])
    self.assertEqual('first_tag', extracted_rows[0][1])
    self.assertEqual(30, extracted_rows[1][0])
    self.assertEqual('first_tag', extracted_rows[1][1])
    filter_scenarios = ['second_tag']
    extracted_rows = []
    for row in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=filter_scenarios, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=False):
        extracted_rows.append((str_token_to_int(row['token'].hex()), row['scenario_type']))
    self.assertEqual(2, len(extracted_rows))
    self.assertEqual(30, extracted_rows[0][0])
    self.assertEqual('second_tag', extracted_rows[0][1])
    self.assertEqual(35, extracted_rows[1][0])
    self.assertEqual('second_tag', extracted_rows[1][1])
    filter_maps = ['map_version']
    row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
    self.assertLess(0, row_cnt)
    filter_maps = ['map_that_does_not_exist']
    row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=filter_maps, include_invalid_mission_goals=False, include_cameras=False)))
    self.assertEqual(0, row_cnt)
    row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=None, filter_types=None, filter_map_names=None, include_invalid_mission_goals=False, include_cameras=True)))
    self.assertEqual(15, row_cnt)
    row_cnt = sum((1 for _ in get_scenarios_from_db(self.db_file_name, filter_tokens=[int_to_str_token(25)], filter_types=['first_tag'], filter_map_names=['map_version'], include_invalid_mission_goals=False, include_cameras=False)))
    self.assertEqual(1, row_cnt)

def test_get_images_from_lidar_tokens(self) -> None:
    """Test the get_images_from_lidar_tokens query."""
    token = int_to_str_token(20)
    retrieved_images = list(get_images_from_lidar_tokens(self.db_file_name, [token], ['camera_0', 'camera_1'], 50000, 50000))
    self.assertEqual(2, len(retrieved_images))
    self.assertEqual(1100020, str_token_to_int(retrieved_images[0].token))
    self.assertEqual(1100070, str_token_to_int(retrieved_images[1].token))
    self.assertEqual('camera_0', retrieved_images[0].channel)
    self.assertEqual('camera_1', retrieved_images[1].channel)

def test_get_cameras(self) -> None:
    """Test the get_cameras query."""
    retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_0', 'camera_1']))
    self.assertEqual(2, len(retrieved_cameras))
    self.assertEqual(1000000, str_token_to_int(retrieved_cameras[0].token))
    self.assertEqual(1000001, str_token_to_int(retrieved_cameras[1].token))
    self.assertEqual('camera_0', retrieved_cameras[0].channel)
    self.assertEqual('camera_1', retrieved_cameras[1].channel)
    retrieved_cameras = list(get_cameras(self.db_file_name, ['camera_1']))
    self.assertEqual(1, len(retrieved_cameras))
    self.assertEqual(1000001, str_token_to_int(retrieved_cameras[0].token))
    self.assertEqual('camera_1', retrieved_cameras[0].channel)

class DistributedScenarioFilter:
    """
    Class to distribute the work to build / filter scenarios across workers, and to break up those scenarios in chunks to be
    handled on individual machines
    """

    def __init__(self, cfg: DictConfig, worker: WorkerPool, node_rank: int, num_nodes: int, synchronization_path: str, timeout_seconds: int=7200, distributed_mode: DistributedMode=DistributedMode.SCENARIO_BASED):
        """
        :param cfg: top level config for the job (used to build scenario builder / scenario_filter)
        :param worker: worker to use in each node to parallelize the work
        :param node_rank: number from (0, num_nodes -1) denoting "which" node we are on
        :param num_nodes: total number of nodes the job is running on
        :param synchronization_path: path that can be in s3 or on a shared file system that will be used to synchronize
                                     across workers
        :param timeout_seconds: how long to wait during sync operations
        :param distributed_mode: what distributed mode to use to distribute computation
        """
        self._cfg = cfg
        self._worker = worker
        self._node_rank = node_rank
        self._num_nodes = num_nodes
        self.synchronization_path = synchronization_path
        self._timeout_seconds = timeout_seconds
        self._distributed_mode = distributed_mode

    def get_scenarios(self) -> List[AbstractScenario]:
        """
        Get all the scenarios that the current node should process
        :returns: list of scenarios for the current node
        """
        if self._num_nodes == 1 or self._distributed_mode == DistributedMode.SINGLE_NODE:
            logger.info('Building Scenarios in mode %s', DistributedMode.SINGLE_NODE)
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        elif self._distributed_mode in (DistributedMode.LOG_FILE_BASED, DistributedMode.SCENARIO_BASED):
            logger.info('Getting Log Chunks')
            current_chunk = self._get_log_db_files_for_single_node()
            logger.info('Getting Scenarios From Log Chunk of size %d', len(current_chunk))
            scenarios = self._get_scenarios_from_list_of_log_files(current_chunk)
            if self._distributed_mode == DistributedMode.LOG_FILE_BASED:
                logger.info('Distributed mode is %s, so we are just returning the scenariosfound from log files on the current worker.  There are %d scenarios to processon node %d/%d', DistributedMode.LOG_FILE_BASED, len(scenarios), self._node_rank, self._num_nodes)
                return scenarios
            logger.info('Distributed mode is %s, so we are going to repartition the scenarios we got from the log files to better distribute the work', DistributedMode.SCENARIO_BASED)
            logger.info('Getting repartitioned scenario tokens')
            tokens, log_db_files = self._get_repartition_tokens(scenarios)
            OmegaConf.set_struct(self._cfg, False)
            self._cfg.scenario_filter.scenario_tokens = tokens
            self._cfg.scenario_builder.db_files = log_db_files
            OmegaConf.set_struct(self._cfg, True)
            logger.info('Building repartitioned scenarios')
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        else:
            raise ValueError(f'Distributed mode must be one of {[x.name for x in fields(DistributedMode)]}, got {self._distributed_mode} instead!')
        scenarios = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_repartition_tokens(self, scenarios: List[AbstractScenario]) -> Tuple[List[str], List[str]]:
        """
        Submit list of scenarios found by the current node, sync up with other nodes to get the full list of tokens,
        and calculate the current node's set of tokens to process
        :param scenarios: Scenarios found by the current node
        :returns: (list of tokens, list of db files)
        """
        unique_job_id = get_unique_job_id()
        token_distribution_file_dir = Path(self.synchronization_path) / Path('tokens') / Path(unique_job_id)
        token_distribution_barrier_dir = Path(self.synchronization_path) / Path('barrier') / Path(unique_job_id)
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_dir = safe_path_to_string(token_distribution_file_dir)
            token_distribution_barrier_dir = safe_path_to_string(token_distribution_barrier_dir)
        self._write_token_csv_file(scenarios, token_distribution_file_dir)
        distributed_sync(token_distribution_barrier_dir, timeout_seconds=self._timeout_seconds)
        token_distribution = self._get_all_generated_csv(token_distribution_file_dir)
        db_files_path = Path(self._cfg.scenario_builder.db_files[0]).parent if isinstance(self._cfg.scenario_builder.db_files, (list, ListConfig)) else Path(self._cfg.scenario_builder.db_files)
        return self._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)

    def _get_all_generated_csv(self, token_distribution_file_dir: Union[Path, str]) -> List[Tuple[str, str]]:
        """
        Read the csv files that every machine in the cluster generated and get the full list of (token, db_file) pairs
        :param token_distribution_file_dir: path where to the csv files are stored
        :returns: full list of (token, db_file) pairs
        """
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_list = [el for el in expand_s3_dir(token_distribution_file_dir) if el.endswith('.csv')]
            token_distribution_list = []
            bucket, file_path = split_s3_path(Path(token_distribution_file_list[0]))
            s3_store = S3Store(s3_prefix=os.path.join('s3://', bucket))
            for token_distribution_file in token_distribution_file_list:
                with s3_store.get(token_distribution_file) as f:
                    try:
                        token_distribution_list.append(pd.read_csv(f, delimiter=','))
                    except EmptyDataError:
                        logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', token_distribution_file)
        else:
            token_distribution_list = []
            for file_name in os.listdir(token_distribution_file_dir):
                try:
                    token_distribution_list.append(pd.read_csv(os.path.join(token_distribution_file_dir, str(file_name))))
                except EmptyDataError:
                    logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', file_name)
        if not token_distribution_list:
            raise AssertionError('No scenarios found to simulate!')
        token_distribution_df = pd.concat(token_distribution_list, ignore_index=True)
        token_distribution = token_distribution_df.values.tolist()
        return cast(List[Tuple[str, str]], token_distribution)

    def _get_token_and_log_chunk_on_single_node(self, token_distribution: List[Tuple[str, str]], db_files_path: Path) -> Tuple[List[str], List[str]]:
        """
        Get the list of tokens and the list of logs those tokens are found in restricted to the current node
        :param token_distribution: Full list of all (token, log_file) pairs to be divided among the nodes
        :param db_files_path: Path to the actual db files
        """
        db_files_path_sanitized = safe_path_to_string(db_files_path)
        if not check_s3_path_exists(db_files_path_sanitized):
            raise AssertionError(f'Multinode caching only works in S3, but db_files path given was {db_files_path_sanitized}')
        token_distribution_chunk = chunk_list(token_distribution, self._num_nodes)
        current_chunk = token_distribution_chunk[self._node_rank]
        current_logs_chunk = list({os.path.join(db_files_path_sanitized, f'{pair[1]}.db') for pair in current_chunk})
        current_token_chunk = [pair[0] for pair in current_chunk]
        return (current_token_chunk, current_logs_chunk)

    def _write_token_csv_file(self, scenarios: List[AbstractScenario], token_distribution_file_dir: Union[str, Path]) -> None:
        """
        Writes a csv file of format token,log_name that stores the tokens associated with the given scenarios
        :param scenarios: Scenarios to take token/log pairs from
        :param token_distribution_file_dir: directory to write our csv file to
        """
        token_distribution_file = os.path.join(token_distribution_file_dir, f'{self._node_rank}.csv')
        token_log_pairs = [(scenario.token, scenario.log_name) for scenario in scenarios]
        os.makedirs(token_distribution_file_dir, exist_ok=True)
        token_log_pairs_df = pd.DataFrame(token_log_pairs)
        token_log_pairs_df.to_csv(token_distribution_file, index=False)

    def _get_scenarios_from_list_of_log_files(self, log_db_files: List[str]) -> List[AbstractScenario]:
        """
        Gets the scenarios based on self._cfg, restricted to a list of log files
        :param log_db_files: list of log db files to restrict our search to
        :returns: list of scenarios
        """
        OmegaConf.set_struct(self._cfg, False)
        self._cfg.scenario_builder.db_files = log_db_files
        OmegaConf.set_struct(self._cfg, True)
        scenario_builder = build_scenario_builder(self._cfg)
        scenario_filter = build_scenario_filter(self._cfg.scenario_filter)
        scenarios: List[AbstractScenario] = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_log_db_files_for_single_node(self) -> List[str]:
        """
        Get the list of log db files to be run on the current node
        :returns: list of log db files
        """
        if self._num_nodes == 1:
            return cast(List[str], self._cfg.scenario_builder.db_files)
        if not check_s3_path_exists(self._cfg.scenario_builder.db_files):
            raise AssertionError(f'DistributedScenarioFilter with multiple nodes only works in S3, but db_files path given was {self._cfg.scenario_builder.db_files}')
        all_files = get_db_filenames_from_load_path(self._cfg.scenario_builder.db_files)
        file_chunks = chunk_list(all_files, self._num_nodes)
        current_chunk = file_chunks[self._node_rank]
        return cast(List[str], current_chunk)

def _get_repartition_tokens(self, scenarios: List[AbstractScenario]) -> Tuple[List[str], List[str]]:
    """
        Submit list of scenarios found by the current node, sync up with other nodes to get the full list of tokens,
        and calculate the current node's set of tokens to process
        :param scenarios: Scenarios found by the current node
        :returns: (list of tokens, list of db files)
        """
    unique_job_id = get_unique_job_id()
    token_distribution_file_dir = Path(self.synchronization_path) / Path('tokens') / Path(unique_job_id)
    token_distribution_barrier_dir = Path(self.synchronization_path) / Path('barrier') / Path(unique_job_id)
    if self.synchronization_path.startswith('s3'):
        token_distribution_file_dir = safe_path_to_string(token_distribution_file_dir)
        token_distribution_barrier_dir = safe_path_to_string(token_distribution_barrier_dir)
    self._write_token_csv_file(scenarios, token_distribution_file_dir)
    distributed_sync(token_distribution_barrier_dir, timeout_seconds=self._timeout_seconds)
    token_distribution = self._get_all_generated_csv(token_distribution_file_dir)
    db_files_path = Path(self._cfg.scenario_builder.db_files[0]).parent if isinstance(self._cfg.scenario_builder.db_files, (list, ListConfig)) else Path(self._cfg.scenario_builder.db_files)
    return self._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)

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

class TestDistributedSyncWrapper(unittest.TestCase):
    """
    Test the function distributed_sync that wraps the FileBackendBarrier for easier use
    """

    def test_call_with_single_node(self) -> None:
        """
        Test that we don't call wait if we are on one node
        """
        with unittest.mock.patch.object(nuplan.common.utils.file_backed_barrier.FileBackedBarrier, 'wait_barrier', MagicMock()) as mock_wait, unittest.mock.patch.dict(os.environ, {'NUM_NODES': '1'}):
            distributed_sync('')
            mock_wait.assert_not_called()

    def test_call_with_multiple_nodes(self) -> None:
        """
        Test that we call wait with the correct params if we are on multiple nodes
        """
        with unittest.mock.patch.object(nuplan.common.utils.file_backed_barrier.FileBackedBarrier, 'wait_barrier', MagicMock()) as mock_wait, unittest.mock.patch.dict(os.environ, {'NUM_NODES': '2', 'NODE_RANK': '1'}):
            distributed_sync('')
            mock_wait.assert_called_with(activity_id='barrier_token_1', expected_activity_ids={'barrier_token_1', 'barrier_token_0'}, timeout_s=7200, poll_interval_s=0.5)

def test_call_with_single_node(self) -> None:
    """
        Test that we don't call wait if we are on one node
        """
    with unittest.mock.patch.object(nuplan.common.utils.file_backed_barrier.FileBackedBarrier, 'wait_barrier', MagicMock()) as mock_wait, unittest.mock.patch.dict(os.environ, {'NUM_NODES': '1'}):
        distributed_sync('')
        mock_wait.assert_not_called()

def test_call_with_multiple_nodes(self) -> None:
    """
        Test that we call wait with the correct params if we are on multiple nodes
        """
    with unittest.mock.patch.object(nuplan.common.utils.file_backed_barrier.FileBackedBarrier, 'wait_barrier', MagicMock()) as mock_wait, unittest.mock.patch.dict(os.environ, {'NUM_NODES': '2', 'NODE_RANK': '1'}):
        distributed_sync('')
        mock_wait.assert_called_with(activity_id='barrier_token_1', expected_activity_ids={'barrier_token_1', 'barrier_token_0'}, timeout_s=7200, poll_interval_s=0.5)

class TestDistributedScenarioFilter(unittest.TestCase):
    """
    Test the distributed scenario filter that is intended to be used to split work across multiple nodes
    """

    def setUp(self) -> None:
        """
        Build some useful mocks to use in a variety of functions
        """
        self.scenario_builder_mock = MagicMock(AbstractScenarioBuilder)
        self.mock_scenarios = [MagicMock(AbstractScenario), MagicMock(AbstractScenario)]
        self.scenario_builder_mock.get_scenarios = MagicMock()
        self.scenario_builder_mock.get_scenarios.return_value = self.mock_scenarios
        self.build_scenario_builder_mock = MagicMock()
        self.build_scenario_builder_mock.return_value = self.scenario_builder_mock
        self.scenario_filter_mock = MagicMock(ScenarioFilter)
        self.build_scenario_filter_mock = MagicMock()
        self.build_scenario_filter_mock.return_value = self.scenario_filter_mock
        self.mock_dbs = ['file_1', 'file_2']
        self.cfg_mock = MagicMock()
        self.cfg_mock.scenario_builder = MagicMock()
        self.cfg_mock.scenario_builder.db_files = self.mock_dbs
        self.cfg_mock.scenario_filter = MagicMock()
        self.mock_scenarios[0].token = 'a'
        self.mock_scenarios[0].log_name = '1.log'
        self.mock_scenarios[1].token = 'b'
        self.mock_scenarios[1].log_name = '2.log'
        self.worker_mock = MagicMock(WorkerPool)
        self.dist_filter_get_scenarios = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, 'path')
        self.dist_filter_get_scenarios._get_log_db_files_for_single_node = MagicMock()
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files = MagicMock()
        self.dist_filter_get_scenarios._get_repartition_tokens = MagicMock()
        self.dist_filter_get_scenarios._get_repartition_tokens.return_value = (['a'], ['1.log'])

    def test_get_scenarios_scenario_based(self) -> None:
        """
        Test that get_scenarios does full repartitioning in this case
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.OmegaConf.set_struct'):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SCENARIO_BASED
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(self.mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_called()
            self.assertListEqual(self.cfg_mock.scenario_filter.scenario_tokens, ['a'])
            self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['1.log'])
            self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
            self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

    def test_get_scenarios_multiple_nodes_log_file_mode(self) -> None:
        """
        Test that get_scenarios we only call the methods that get a chunk of log files + gets the scenarios from that chunk
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.LOG_FILE_BASED
            mock_scenarios = [MagicMock()]
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.return_value = mock_scenarios
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
            self.build_scenario_builder_mock.assert_not_called()
            self.build_scenario_filter_mock.assert_not_called()

    def test_get_scenarios_single_node(self) -> None:
        """
        Test that get_scenarios just returns the scenarios built by the scenario builder in this case.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SINGLE_NODE
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(self.mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_not_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_not_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
            self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
            self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

    def test_get_repartition_tokens(self) -> None:
        """
        Test that we make all of the expected calls, in the expected order, to repartition the tokens.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_unique_job_id') as id, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.distributed_sync') as dist:
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 'path', timeout_seconds=5)
            dist_filter._write_token_csv_file = MagicMock()
            dist_filter._get_all_generated_csv = MagicMock()
            dist_filter._get_token_and_log_chunk_on_single_node = MagicMock()
            id.return_value = '1'
            dist_filter._get_all_generated_csv.return_value = [('a', '1'), ('b', '2')]
            dist_filter._get_token_and_log_chunk_on_single_node.return_value = (['a', 'b'], ['path/1.db', 'path/2.db'])
            manager = Mock()
            manager.attach_mock(dist_filter._write_token_csv_file, 'write_csv')
            manager.attach_mock(dist, 'sync')
            manager.attach_mock(dist_filter._get_all_generated_csv, 'get_csvs')
            manager.attach_mock(dist_filter._get_token_and_log_chunk_on_single_node, 'chunk')
            output = dist_filter._get_repartition_tokens(scenarios=self.mock_scenarios)
            self.assertEqual(output, (['a', 'b'], ['path/1.db', 'path/2.db']))
            expected_calls = [call.write_csv(self.mock_scenarios, Path('path/tokens/1')), call.sync(Path('path/barrier/1'), timeout_seconds=5), call.get_csvs(Path('path/tokens/1')), call.chunk([('a', '1'), ('b', '2')], Path('.'))]
            self.assertListEqual(manager.mock_calls, expected_calls)

    def test_get_all_generated_csv_s3(self) -> None:
        """
        Test that we get all of the tokens from the csv files we have created when running in mocked s3.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.expand_s3_dir') as expand, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.split_s3_path') as split, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.S3Store') as store:
            with tempfile.TemporaryDirectory() as tmp_dir_str:
                dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 's3://dummy/path')
                dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
                split.return_value = ('bucket', 'file')
                expand.return_value = [os.path.join(tmp_dir_str, '0.csv')]

                def mock_get(path: str) -> IO[str]:
                    """
                    Mock get for the s3 store we mock, just opens the file as a local file.
                    """
                    return open(path)
                store.return_value = MagicMock()
                store.return_value.get = mock_get
                filter_output = dist_filter._get_all_generated_csv('s3://dummy/path')
                self.assertEqual(filter_output, [['a', '1.log'], ['b', '2.log']])

    def test_get_all_generated_csv_local(self) -> None:
        """
        Test that we get all of the tokens from the csv files we have created when running locally.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, tmp_dir_str)
            dist_filter_2 = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 1, 2, tmp_dir_str)
            dist_filter._write_token_csv_file(self.mock_scenarios[:1], tmp_dir_str)
            dist_filter_2._write_token_csv_file(self.mock_scenarios[1:], tmp_dir_str)
            filter_1_output = dist_filter._get_all_generated_csv(tmp_dir_str)
            filter_2_output = dist_filter_2._get_all_generated_csv(tmp_dir_str)
            self.assertListEqual(filter_1_output, filter_2_output)
            expected_token_set = {('a', '1.log'), ('b', '2.log')}
            self.assertEqual(len(filter_1_output), len(expected_token_set))
            self.assertSetEqual({tuple(i) for i in filter_1_output}, expected_token_set)

    def test_get_token_and_log_chunk_on_single_node(self) -> None:
        """
        Test that we correctly chunk the tokens and associated log names on each node.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists'):
            db_files_path = Path('s3://dummy/path')
            token_distribution = [('a', '1'), ('b', '1'), ('c', '2'), ('d', '2')]
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
            tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
            self.assertSetEqual(set(tokens), {'a', 'b', 'c', 'd'})
            self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db', 's3://dummy/path/2.db'})
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
            tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
            self.assertSetEqual(set(tokens), {'a', 'b'})
            self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db'})

    def test_write_token_csv_file(self) -> None:
        """
        Test that we correctly write out a csv file for the current node for the list of scenarios provided
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
            expected_path = os.path.join(tmp_dir_str, '0.csv')
            self.assertTrue(os.path.exists(expected_path))
            csv_out = pd.read_csv(expected_path).to_dict()
            self.assertEqual(csv_out, {'0': {0: 'a', 1: 'b'}, '1': {0: '1.log', 1: '2.log'}})

    def test_get_scenarios_from_list_of_log_files(self) -> None:
        """
        Test that we build a scenario builder with the proper db files updated, and successfully get scenarios from it
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            scenarios = dist_filter._get_scenarios_from_list_of_log_files(['file_3'])
            self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['file_3'])
            self.build_scenario_filter_mock.assert_called_with(self.cfg_mock.scenario_filter)
            self.build_scenario_builder_mock.assert_called_with(self.cfg_mock)
            self.scenario_builder_mock.get_scenarios.assert_called_with(self.scenario_filter_mock, self.worker_mock)
            self.assertEqual(scenarios, self.mock_scenarios)

    def test_get_log_db_files_for_single_node_non_distributed(self) -> None:
        """
        Test that in a non-distributed context we simply return all the db files in the config
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        logs = dist_filter._get_log_db_files_for_single_node()
        self.assertListEqual(logs, self.mock_dbs)

    def test_get_log_db_files_for_single_node_distributed(self) -> None:
        """
        Test that in a distributed context we call the proper functions and chunk the data as expected
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_db_filenames_from_load_path') as get, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists') as check:
            get.side_effect = lambda x: x
            check.return_value = True
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
            logs = dist_filter._get_log_db_files_for_single_node()
            self.assertListEqual(logs, self.mock_dbs[:1])

def setUp(self) -> None:
    """
        Build some useful mocks to use in a variety of functions
        """
    self.scenario_builder_mock = MagicMock(AbstractScenarioBuilder)
    self.mock_scenarios = [MagicMock(AbstractScenario), MagicMock(AbstractScenario)]
    self.scenario_builder_mock.get_scenarios = MagicMock()
    self.scenario_builder_mock.get_scenarios.return_value = self.mock_scenarios
    self.build_scenario_builder_mock = MagicMock()
    self.build_scenario_builder_mock.return_value = self.scenario_builder_mock
    self.scenario_filter_mock = MagicMock(ScenarioFilter)
    self.build_scenario_filter_mock = MagicMock()
    self.build_scenario_filter_mock.return_value = self.scenario_filter_mock
    self.mock_dbs = ['file_1', 'file_2']
    self.cfg_mock = MagicMock()
    self.cfg_mock.scenario_builder = MagicMock()
    self.cfg_mock.scenario_builder.db_files = self.mock_dbs
    self.cfg_mock.scenario_filter = MagicMock()
    self.mock_scenarios[0].token = 'a'
    self.mock_scenarios[0].log_name = '1.log'
    self.mock_scenarios[1].token = 'b'
    self.mock_scenarios[1].log_name = '2.log'
    self.worker_mock = MagicMock(WorkerPool)
    self.dist_filter_get_scenarios = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, 'path')
    self.dist_filter_get_scenarios._get_log_db_files_for_single_node = MagicMock()
    self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files = MagicMock()
    self.dist_filter_get_scenarios._get_repartition_tokens = MagicMock()
    self.dist_filter_get_scenarios._get_repartition_tokens.return_value = (['a'], ['1.log'])

def test_get_scenarios_scenario_based(self) -> None:
    """
        Test that get_scenarios does full repartitioning in this case
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.OmegaConf.set_struct'):
        self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SCENARIO_BASED
        scenarios = self.dist_filter_get_scenarios.get_scenarios()
        self.assertEqual(self.mock_scenarios, scenarios)
        self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
        self.dist_filter_get_scenarios._get_repartition_tokens.assert_called()
        self.assertListEqual(self.cfg_mock.scenario_filter.scenario_tokens, ['a'])
        self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['1.log'])
        self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
        self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

def test_get_scenarios_multiple_nodes_log_file_mode(self) -> None:
    """
        Test that get_scenarios we only call the methods that get a chunk of log files + gets the scenarios from that chunk
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
        self.dist_filter_get_scenarios._distributed_mode = DistributedMode.LOG_FILE_BASED
        mock_scenarios = [MagicMock()]
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.return_value = mock_scenarios
        scenarios = self.dist_filter_get_scenarios.get_scenarios()
        self.assertEqual(mock_scenarios, scenarios)
        self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
        self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
        self.build_scenario_builder_mock.assert_not_called()
        self.build_scenario_filter_mock.assert_not_called()

def test_get_scenarios_single_node(self) -> None:
    """
        Test that get_scenarios just returns the scenarios built by the scenario builder in this case.
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
        self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SINGLE_NODE
        scenarios = self.dist_filter_get_scenarios.get_scenarios()
        self.assertEqual(self.mock_scenarios, scenarios)
        self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_not_called()
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_not_called()
        self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
        self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
        self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

def test_get_repartition_tokens(self) -> None:
    """
        Test that we make all of the expected calls, in the expected order, to repartition the tokens.
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_unique_job_id') as id, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.distributed_sync') as dist:
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 'path', timeout_seconds=5)
        dist_filter._write_token_csv_file = MagicMock()
        dist_filter._get_all_generated_csv = MagicMock()
        dist_filter._get_token_and_log_chunk_on_single_node = MagicMock()
        id.return_value = '1'
        dist_filter._get_all_generated_csv.return_value = [('a', '1'), ('b', '2')]
        dist_filter._get_token_and_log_chunk_on_single_node.return_value = (['a', 'b'], ['path/1.db', 'path/2.db'])
        manager = Mock()
        manager.attach_mock(dist_filter._write_token_csv_file, 'write_csv')
        manager.attach_mock(dist, 'sync')
        manager.attach_mock(dist_filter._get_all_generated_csv, 'get_csvs')
        manager.attach_mock(dist_filter._get_token_and_log_chunk_on_single_node, 'chunk')
        output = dist_filter._get_repartition_tokens(scenarios=self.mock_scenarios)
        self.assertEqual(output, (['a', 'b'], ['path/1.db', 'path/2.db']))
        expected_calls = [call.write_csv(self.mock_scenarios, Path('path/tokens/1')), call.sync(Path('path/barrier/1'), timeout_seconds=5), call.get_csvs(Path('path/tokens/1')), call.chunk([('a', '1'), ('b', '2')], Path('.'))]
        self.assertListEqual(manager.mock_calls, expected_calls)

def test_get_all_generated_csv_s3(self) -> None:
    """
        Test that we get all of the tokens from the csv files we have created when running in mocked s3.
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.expand_s3_dir') as expand, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.split_s3_path') as split, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.S3Store') as store:
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 's3://dummy/path')
            dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
            split.return_value = ('bucket', 'file')
            expand.return_value = [os.path.join(tmp_dir_str, '0.csv')]

            def mock_get(path: str) -> IO[str]:
                """
                    Mock get for the s3 store we mock, just opens the file as a local file.
                    """
                return open(path)
            store.return_value = MagicMock()
            store.return_value.get = mock_get
            filter_output = dist_filter._get_all_generated_csv('s3://dummy/path')
            self.assertEqual(filter_output, [['a', '1.log'], ['b', '2.log']])

def test_get_all_generated_csv_local(self) -> None:
    """
        Test that we get all of the tokens from the csv files we have created when running locally.
        """
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, tmp_dir_str)
        dist_filter_2 = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 1, 2, tmp_dir_str)
        dist_filter._write_token_csv_file(self.mock_scenarios[:1], tmp_dir_str)
        dist_filter_2._write_token_csv_file(self.mock_scenarios[1:], tmp_dir_str)
        filter_1_output = dist_filter._get_all_generated_csv(tmp_dir_str)
        filter_2_output = dist_filter_2._get_all_generated_csv(tmp_dir_str)
        self.assertListEqual(filter_1_output, filter_2_output)
        expected_token_set = {('a', '1.log'), ('b', '2.log')}
        self.assertEqual(len(filter_1_output), len(expected_token_set))
        self.assertSetEqual({tuple(i) for i in filter_1_output}, expected_token_set)

def test_get_token_and_log_chunk_on_single_node(self) -> None:
    """
        Test that we correctly chunk the tokens and associated log names on each node.
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists'):
        db_files_path = Path('s3://dummy/path')
        token_distribution = [('a', '1'), ('b', '1'), ('c', '2'), ('d', '2')]
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
        self.assertSetEqual(set(tokens), {'a', 'b', 'c', 'd'})
        self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db', 's3://dummy/path/2.db'})
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
        tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
        self.assertSetEqual(set(tokens), {'a', 'b'})
        self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db'})

def test_get_scenarios_from_list_of_log_files(self) -> None:
    """
        Test that we build a scenario builder with the proper db files updated, and successfully get scenarios from it
        """
    dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
        scenarios = dist_filter._get_scenarios_from_list_of_log_files(['file_3'])
        self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['file_3'])
        self.build_scenario_filter_mock.assert_called_with(self.cfg_mock.scenario_filter)
        self.build_scenario_builder_mock.assert_called_with(self.cfg_mock)
        self.scenario_builder_mock.get_scenarios.assert_called_with(self.scenario_filter_mock, self.worker_mock)
        self.assertEqual(scenarios, self.mock_scenarios)

def test_get_log_db_files_for_single_node_non_distributed(self) -> None:
    """
        Test that in a non-distributed context we simply return all the db files in the config
        """
    dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
    logs = dist_filter._get_log_db_files_for_single_node()
    self.assertListEqual(logs, self.mock_dbs)

def test_get_log_db_files_for_single_node_distributed(self) -> None:
    """
        Test that in a distributed context we call the proper functions and chunk the data as expected
        """
    with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_db_filenames_from_load_path') as get, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists') as check:
        get.side_effect = lambda x: x
        check.return_value = True
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
        logs = dist_filter._get_log_db_files_for_single_node()
        self.assertListEqual(logs, self.mock_dbs[:1])

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

def test_pass_on_valid_cases(self) -> None:
    """Tests that for nominal cases the output of the function is returned."""
    result, _ = keep_trying(self.passing_function, self.args, self.kwargs, self.errors, timeout=1)
    self.assertEqual('result', result)
    self.passing_function.assert_called_once_with(*self.args, **self.kwargs)

class MockHttpClientResponse(ClientResponse):
    """
    Mock Http Client response to make aioboto work with moto.
    """

    def __init__(self, response: AWSResponse):
        """
        Wraps moto's mocked client response for use with aioboto.
        :param response: Mocked AWS response.
        """
        read_index = 0

        async def read(n: int=-1) -> bytes:
            """
            Read handler for response contents.
            :param n: Number of bytes to read.
            :return: Bytes read from response content.
            """
            nonlocal read_index
            nonlocal response
            read_response: bytes = response.content[read_index:read_index + n]
            read_index += n
            return read_response
        self.content = MagicMock(aiohttp.StreamReader)
        self.content.read = read
        self.response = response

    @property
    def raw_headers(self) -> RawHeaders:
        """
        Return the headers encoded the way that aioboto expects them.
        :return: Raw response headers.
        """
        return {k.encode('utf-8'): str(v).encode('utf-8') for k, v in self.response.headers.items()}.items()

def __init__(self, response: AWSResponse):
    """
        Wraps moto's mocked client response for use with aioboto.
        :param response: Mocked AWS response.
        """
    read_index = 0

    async def read(n: int=-1) -> bytes:
        """
            Read handler for response contents.
            :param n: Number of bytes to read.
            :return: Bytes read from response content.
            """
        nonlocal read_index
        nonlocal response
        read_response: bytes = response.content[read_index:read_index + n]
        read_index += n
        return read_response
    self.content = MagicMock(aiohttp.StreamReader)
    self.content.read = read
    self.response = response

class TestMapManager(unittest.TestCase):
    """
    MapManager test suite.
    """

    @patch('nuplan.common.maps.map_manager.AbstractMapFactory')
    def setUp(self, mock_map_factory: Mock) -> None:
        """
        Initializes the map manager.
        """
        self.map_manager = MapManager(mock_map_factory)

    @patch('nuplan.common.maps.map_manager.AbstractMapFactory')
    def test_initialization(self, mock_map_factory: Mock) -> None:
        """Tests that objects are initialized correctly."""
        map_manager = MapManager(mock_map_factory)
        self.assertEqual(mock_map_factory, map_manager.map_factory)
        self.assertEqual({}, map_manager.maps)

    def test_get_map(self) -> None:
        """Tests that maps are retrieved from cache, if not present created and added to it."""
        map_name = 'map_name'
        self.map_manager.map_factory.build_map_from_name.return_value = 'built_map'
        _map = self.map_manager.get_map(map_name)
        self.map_manager.map_factory.build_map_from_name.assert_called_once_with(map_name)
        self.assertTrue(map_name in self.map_manager.maps)
        self.assertEqual('built_map', _map)
        _ = self.map_manager.get_map(map_name)
        self.map_manager.map_factory.build_map_from_name.assert_called_once_with(map_name)

@patch('nuplan.common.maps.map_manager.AbstractMapFactory')
def setUp(self, mock_map_factory: Mock) -> None:
    """
        Initializes the map manager.
        """
    self.map_manager = MapManager(mock_map_factory)

@patch('nuplan.common.maps.map_manager.AbstractMapFactory')
def test_initialization(self, mock_map_factory: Mock) -> None:
    """Tests that objects are initialized correctly."""
    map_manager = MapManager(mock_map_factory)
    self.assertEqual(mock_map_factory, map_manager.map_factory)
    self.assertEqual({}, map_manager.maps)

def test_get_map(self) -> None:
    """Tests that maps are retrieved from cache, if not present created and added to it."""
    map_name = 'map_name'
    self.map_manager.map_factory.build_map_from_name.return_value = 'built_map'
    _map = self.map_manager.get_map(map_name)
    self.map_manager.map_factory.build_map_from_name.assert_called_once_with(map_name)
    self.assertTrue(map_name in self.map_manager.maps)
    self.assertEqual('built_map', _map)
    _ = self.map_manager.get_map(map_name)
    self.map_manager.map_factory.build_map_from_name.assert_called_once_with(map_name)

class TrackedObjects:
    """Class representing tracked objects, a collection of SceneObjects"""

    def __init__(self, tracked_objects: Optional[List[TrackedObject]]=None):
        """
        :param tracked_objects: List of tracked objects
        """
        tracked_objects = tracked_objects if tracked_objects is not None else []
        self.tracked_objects = sorted(tracked_objects, key=lambda agent: agent.tracked_object_type.value)

    def __iter__(self) -> Iterable[TrackedObject]:
        """When iterating return the tracked objects."""
        return iter(self.tracked_objects)

    @classmethod
    def from_oriented_boxes(cls, boxes: List[OrientedBox]) -> TrackedObjects:
        """When iterating return the tracked objects."""
        scene_objects = [SceneObject(TrackedObjectType.GENERIC_OBJECT, box, SceneObjectMetadata(timestamp_us=i, token=str(i), track_token=None, track_id=None)) for i, box in enumerate(boxes)]
        return TrackedObjects(scene_objects)

    @cached_property
    def _ranges_per_type(self) -> Dict[TrackedObjectType, Tuple[int, int]]:
        """
        Returns the start and end index of the range of agents for each agent type
        in the list of agents (sorted by agent type). The ranges are cached for subsequent calls.
        """
        ranges_per_type: Dict[TrackedObjectType, Tuple[int, int]] = {}
        if self.tracked_objects:
            last_agent_type = self.tracked_objects[0].tracked_object_type
            start_range = 0
            end_range = len(self.tracked_objects)
            for idx, agent in enumerate(self.tracked_objects):
                if agent.tracked_object_type is not last_agent_type:
                    ranges_per_type[last_agent_type] = (start_range, idx)
                    start_range = idx
                    last_agent_type = agent.tracked_object_type
            ranges_per_type[last_agent_type] = (start_range, end_range)
            ranges_per_type.update({agent_type: (end_range, end_range) for agent_type in TrackedObjectType if agent_type not in ranges_per_type})
        return ranges_per_type

    def get_tracked_objects_of_type(self, tracked_object_type: TrackedObjectType) -> List[TrackedObject]:
        """
        Gets the sublist of agents of a particular TrackedObjectType
        :param tracked_object_type: The query TrackedObjectType
        :return: List of the present agents of the query type. Throws an error if the key is invalid.
        """
        if tracked_object_type in self._ranges_per_type:
            start_idx, end_idx = self._ranges_per_type[tracked_object_type]
            return self.tracked_objects[start_idx:end_idx]
        else:
            return []

    def get_agents(self) -> List[Agent]:
        """
        Getter for the tracked objects which are Agents
        :return: list of Agents
        """
        agents = []
        for agent_type in AGENT_TYPES:
            agents.extend(self.get_tracked_objects_of_type(agent_type))
        return agents

    def get_static_objects(self) -> List[StaticObject]:
        """
        Getter for the tracked objects which are StaticObjects
        :return: list of StaticObjects
        """
        static_objects = []
        for static_object_type in STATIC_OBJECT_TYPES:
            static_objects.extend(self.get_tracked_objects_of_type(static_object_type))
        return static_objects

    def __len__(self) -> int:
        """
        :return: The number of tracked objects in the class
        """
        return len(self.tracked_objects)

    def get_tracked_objects_of_types(self, tracked_object_types: List[TrackedObjectType]) -> List[TrackedObject]:
        """
        Gets the sublist of agents of particular TrackedObjectTypes
        :param tracked_object_types: The query TrackedObjectTypes
        :return: List of the present agents of the query types. Throws an error if the key is invalid.
        """
        open_loop_tracked_objects = []
        for _type in tracked_object_types:
            open_loop_tracked_objects.extend(self.get_tracked_objects_of_type(_type))
        return open_loop_tracked_objects

def __iter__(self) -> Iterable[TrackedObject]:
    """When iterating return the tracked objects."""
    return iter(self.tracked_objects)

@dataclass
class Point2D:
    """Class to represents 2D points."""
    x: float
    y: float
    __slots__ = ('x', 'y')

    def __iter__(self) -> Iterable[float]:
        """
        :return: iterator of tuples (x, y)
        """
        return iter((self.x, self.y))

    @property
    def array(self) -> npt.NDArray[np.float64]:
        """
        Convert vector to array
        :return: array containing [x, y]
        """
        return np.array([self.x, self.y], dtype=np.float64)

    def __hash__(self) -> int:
        """Hash method"""
        return hash((self.x, self.y))

def __iter__(self) -> Iterable[float]:
    """
        :return: iterator of tuples (x, y)
        """
    return iter((self.x, self.y))

@dataclass
class StateSE2(Point2D):
    """
    SE2 state - representing [x, y, heading]
    """
    heading: float
    __slots__ = 'heading'

    @property
    def point(self) -> Point2D:
        """
        Gets a point from the StateSE2
        :return: Point with x and y from StateSE2
        """
        return Point2D(self.x, self.y)

    def as_matrix(self) -> npt.NDArray[np.float32]:
        """
        :return: 3x3 2D transformation matrix representing the SE2 state.
        """
        return np.array([[np.cos(self.heading), -np.sin(self.heading), self.x], [np.sin(self.heading), np.cos(self.heading), self.y], [0.0, 0.0, 1.0]])

    def as_matrix_3d(self) -> npt.NDArray[np.float32]:
        """
        :return: 4x4 3D transformation matrix representing the SE2 state projected to SE3.
        """
        return np.array([[np.cos(self.heading), -np.sin(self.heading), 0.0, self.x], [np.sin(self.heading), np.cos(self.heading), 0.0, self.y], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]])

    def distance_to(self, state: StateSE2) -> float:
        """
        Compute the euclidean distance between two points
        :param state: state to compute distance to
        :return distance between two points
        """
        return float(np.hypot(self.x - state.x, self.y - state.y))

    @staticmethod
    def from_matrix(matrix: npt.NDArray[np.float32]) -> StateSE2:
        """
        :param matrix: 3x3 2D transformation matrix
        :return: StateSE2 object
        """
        assert matrix.shape == (3, 3), f'Expected 3x3 transformation matrix, but input matrix has shape {matrix.shape}'
        vector = [matrix[0, 2], matrix[1, 2], np.arctan2(matrix[1, 0], matrix[0, 0])]
        return StateSE2.deserialize(vector)

    @staticmethod
    def deserialize(vector: List[float]) -> StateSE2:
        """
        Deserialize vector into state SE2
        :param vector: serialized list of floats
        :return: StateSE2
        """
        if len(vector) != 3:
            raise RuntimeError(f'Expected a vector of size 3, got {len(vector)}')
        return StateSE2(x=vector[0], y=vector[1], heading=vector[2])

    def serialize(self) -> List[float]:
        """
        :return: list of serialized variables [X, Y, Heading]
        """
        return [self.x, self.y, self.heading]

    def __eq__(self, other: object) -> bool:
        """
        Compare two state SE2
        :param other: object
        :return: true if the objects are equal, false otherwise
        """
        if not isinstance(other, StateSE2):
            return NotImplemented
        return math.isclose(self.x, other.x, abs_tol=0.001) and math.isclose(self.y, other.y, abs_tol=0.001) and math.isclose(self.heading, other.heading, abs_tol=0.0001)

    def __iter__(self) -> Iterable[float]:
        """
        :return: iterator of tuples (x, y, heading)
        """
        return iter((self.x, self.y, self.heading))

    def __hash__(self) -> int:
        """
        :return: hash for this object
        """
        return hash((self.x, self.y, self.heading))

def __iter__(self) -> Iterable[float]:
    """
        :return: iterator of tuples (x, y, heading)
        """
    return iter((self.x, self.y, self.heading))

@dataclass
class ProgressStateSE2(StateSE2):
    """
    StateSE2 parameterized by progress
    """
    progress: float
    __slots__ = 'progress'

    @staticmethod
    def deserialize(vector: List[float]) -> ProgressStateSE2:
        """
        Deserialize vector into this class
        :param vector: containing raw float numbers containing [progress, x, ,y, heading]
        :return: ProgressStateSE2 class
        """
        if len(vector) != 4:
            raise RuntimeError(f'Expected a vector of size 4, got {len(vector)}')
        return ProgressStateSE2(progress=vector[0], x=vector[1], y=vector[2], heading=vector[3])

    def __iter__(self) -> Iterable[Union[float]]:
        """
        :return: an iterator over the tuble of (progress, x, y, heading) states
        """
        return iter((self.progress, self.x, self.y, self.heading))

def __iter__(self) -> Iterable[Union[float]]:
    """
        :return: an iterator over the tuble of (progress, x, y, heading) states
        """
    return iter((self.progress, self.x, self.y, self.heading))

class EgoState(InterpolatableState):
    """Represent the current state of ego, along with its dynamic attributes."""

    def __init__(self, car_footprint: CarFootprint, dynamic_car_state: DynamicCarState, tire_steering_angle: float, is_in_auto_mode: bool, time_point: TimePoint):
        """
        :param car_footprint: The CarFootprint of Ego
        :param dynamic_car_state: The current dynamical state of ego
        :param tire_steering_angle: The current steering angle of the tires
        :param is_in_auto_mode: If the state refers to car in autonomous mode
        :param time_point: Time stamp of the state
        """
        self._car_footprint = car_footprint
        self._tire_steering_angle = tire_steering_angle
        self._is_in_auto_mode = is_in_auto_mode
        self._time_point = time_point
        self._dynamic_car_state = dynamic_car_state

    @cached_property
    def waypoint(self) -> Waypoint:
        """
        :return: waypoint corresponding to this ego state
        """
        return Waypoint(time_point=self.time_point, oriented_box=self.car_footprint, velocity=self.dynamic_car_state.rear_axle_velocity_2d)

    @staticmethod
    def deserialize(vector: List[Union[int, float]], vehicle: VehicleParameters) -> EgoState:
        """
        Deserialize object, ordering kept for backward compatibility
        :param vector: List of variables for deserialization
        :param vehicle: Vehicle parameters
        """
        if len(vector) != 9:
            raise RuntimeError(f'Expected a vector of size 9, got {len(vector)}')
        return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(vector[1], vector[2], vector[3]), rear_axle_velocity_2d=StateVector2D(vector[4], vector[5]), rear_axle_acceleration_2d=StateVector2D(vector[6], vector[7]), tire_steering_angle=vector[8], time_point=TimePoint(int(vector[0])), vehicle_parameters=vehicle)

    def __iter__(self) -> Iterable[Union[int, float]]:
        """Iterable over ego parameters"""
        return iter((self.time_us, self.rear_axle.x, self.rear_axle.y, self.rear_axle.heading, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle))

    def to_split_state(self) -> SplitState:
        """Inherited, see superclass."""
        linear_states = [self.time_us, self.rear_axle.x, self.rear_axle.y, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle]
        angular_states = [self.rear_axle.heading]
        fixed_state = [self.car_footprint.vehicle_parameters]
        return SplitState(linear_states, angular_states, fixed_state)

    @staticmethod
    def from_split_state(split_state: SplitState) -> EgoState:
        """Inherited, see superclass."""
        if len(split_state) != 10:
            raise RuntimeError(f'Expected a variable state vector of size 10, got {len(split_state)}')
        return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(split_state.linear_states[1], split_state.linear_states[2], split_state.angular_states[0]), rear_axle_velocity_2d=StateVector2D(split_state.linear_states[3], split_state.linear_states[4]), rear_axle_acceleration_2d=StateVector2D(split_state.linear_states[5], split_state.linear_states[6]), tire_steering_angle=split_state.linear_states[7], time_point=TimePoint(int(split_state.linear_states[0])), vehicle_parameters=split_state.fixed_states[0])

    @property
    def is_in_auto_mode(self) -> bool:
        """
        :return: True if ego is in auto mode, False otherwise.
        """
        return self._is_in_auto_mode

    @property
    def car_footprint(self) -> CarFootprint:
        """
        Getter for Ego's Car footprint
        :return: Ego's car footprint
        """
        return self._car_footprint

    @property
    def tire_steering_angle(self) -> float:
        """
        Getter for Ego's tire steering angle
        :return: Ego's tire steering angle
        """
        return self._tire_steering_angle

    @property
    def center(self) -> StateSE2:
        """
        Getter for Ego's center pose (center of mass)
        :return: Ego's center pose
        """
        return self._car_footprint.oriented_box.center

    @property
    def rear_axle(self) -> StateSE2:
        """
        Getter for Ego's rear axle pose (middle of the rear axle)
        :return: Ego's rear axle pose
        """
        return self.car_footprint.rear_axle

    @property
    def time_point(self) -> TimePoint:
        """
        Time stamp of the EgoState
        :return: EgoState time stamp
        """
        return self._time_point

    @property
    def time_us(self) -> int:
        """
        Time in micro seconds
        :return: [us].
        """
        return int(self.time_point.time_us)

    @property
    def time_seconds(self) -> float:
        """
        Time in seconds
        :return: [s]
        """
        return float(self.time_us * 1e-06)

    @property
    def dynamic_car_state(self) -> DynamicCarState:
        """
        Getter for the dynamic car state of Ego.
        :return: The dynamic car state
        """
        return self._dynamic_car_state

    @property
    def scene_object_metadata(self) -> SceneObjectMetadata:
        """
        :return: create scene object metadata
        """
        return SceneObjectMetadata(token='ego', track_token='ego', track_id=-1, timestamp_us=self.time_us)

    @cached_property
    def agent(self) -> AgentState:
        """
        Casts the EgoState to an Agent object.
        :return: An Agent object with the parameters of EgoState
        """
        return AgentState(metadata=self.scene_object_metadata, tracked_object_type=TrackedObjectType.EGO, oriented_box=self.car_footprint.oriented_box, velocity=self.dynamic_car_state.center_velocity_2d)

    @classmethod
    def build_from_rear_axle(cls, rear_axle_pose: StateSE2, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, tire_steering_angle: float, time_point: TimePoint, vehicle_parameters: VehicleParameters, is_in_auto_mode: bool=True, angular_vel: float=0.0, angular_accel: float=0.0, tire_steering_rate: float=0.0) -> EgoState:
        """
        Initializer using raw parameters, assumes that the reference frame is CAR_POINT.REAR_AXLE
        :param rear_axle_pose: Pose of ego's rear axle
        :param rear_axle_velocity_2d: Vectorial velocity of Ego's rear axle
        :param rear_axle_acceleration_2d: Vectorial acceleration of Ego's rear axle
        :param angular_vel: Angular velocity of Ego
        :param angular_accel: Angular acceleration of Ego,
        :param tire_steering_angle: Angle of the tires
        :param is_in_auto_mode: True if ego is in auto mode, false otherwise
        :param time_point: Timestamp of the ego state
        :param vehicle_parameters: Vehicle parameters
        :param tire_steering_rate: Steering rate of tires [rad/s]
        :return: The initialized EgoState
        """
        car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=rear_axle_pose, vehicle_parameters=vehicle_parameters)
        dynamic_ego_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_vel, angular_acceleration=angular_accel, tire_steering_rate=tire_steering_rate)
        return cls(car_footprint=car_footprint, dynamic_car_state=dynamic_ego_state, tire_steering_angle=tire_steering_angle, time_point=time_point, is_in_auto_mode=is_in_auto_mode)

    @classmethod
    def build_from_center(cls, center: StateSE2, center_velocity_2d: StateVector2D, center_acceleration_2d: StateVector2D, tire_steering_angle: float, time_point: TimePoint, vehicle_parameters: VehicleParameters, is_in_auto_mode: bool=True, angular_vel: float=0.0, angular_accel: float=0.0) -> EgoState:
        """
        Initializer using raw parameters, assumes that the reference frame is center frame
        :param center: Pose of ego center
        :param center_velocity_2d: Vectorial velocity of Ego's center
        :param center_acceleration_2d: Vectorial acceleration of Ego's center
        :param tire_steering_angle: Angle of the tires
        :param time_point: Timestamp of the ego state
        :param vehicle_parameters: Vehicle parameters
        :param is_in_auto_mode: True if ego is in auto mode, false otherwise, defaults to True
        :param angular_vel: Angular velocity of Ego, defaults to 0.0
        :param angular_accel: Angular acceleration of Ego, defaults to 0.0
        :return: The initialized EgoState
        """
        car_footprint = CarFootprint.build_from_center(center, vehicle_parameters)
        rear_axle_to_center_dist = car_footprint.rear_axle_to_center_dist
        displacement = StateVector2D(-rear_axle_to_center_dist, 0.0)
        rear_axle_velocity_2d = get_velocity_shifted(displacement, center_velocity_2d, angular_vel)
        rear_axle_acceleration_2d = get_acceleration_shifted(displacement, center_acceleration_2d, angular_vel, angular_accel)
        dynamic_ego_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_vel, angular_acceleration=angular_accel)
        return cls(car_footprint=car_footprint, dynamic_car_state=dynamic_ego_state, tire_steering_angle=tire_steering_angle, time_point=time_point, is_in_auto_mode=is_in_auto_mode)

def __iter__(self) -> Iterable[Union[int, float]]:
    """Iterable over ego parameters"""
    return iter((self.time_us, self.rear_axle.x, self.rear_axle.y, self.rear_axle.heading, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle))

class Waypoint(InterpolatableState):
    """Represents a waypoint which is part of a trajectory. Optionals to allow for geometric trajectory"""

    def __init__(self, time_point: TimePoint, oriented_box: OrientedBox, velocity: Optional[StateVector2D]=None):
        """
        :param time_point: TimePoint corresponding to the Waypoint
        :param oriented_box: Position of the oriented box at the Waypoint
        :param velocity: Optional velocity information
        """
        self._time_point = time_point
        self._oriented_box = oriented_box
        self._velocity = velocity

    def __iter__(self) -> Iterable[Union[int, float]]:
        """
        Iterator for waypoint variables.
        :return: An iterator to the variables of the Waypoint.
        """
        return iter((self.time_us, self._oriented_box.center.x, self._oriented_box.center.y, self._oriented_box.center.heading, self._velocity.x if self._velocity is not None else None, self._velocity.y if self._velocity is not None else None))

    def __eq__(self, other: Any) -> bool:
        """
        Comparison between two Waypoints.
        :param other: Other object.
        :return True if both objects are same.
        """
        if not isinstance(other, Waypoint):
            return NotImplemented
        return other.oriented_box == self._oriented_box and other.time_point == self.time_point and (other.velocity == self._velocity)

    def __repr__(self) -> str:
        """
        :return: A string describing the object.
        """
        return self.__class__.__qualname__ + '(' + ', '.join([f'{f}={v}' for f, v in self.__dict__.items()]) + ')'

    @property
    def center(self) -> StateSE2:
        """
        Getter for center position of the waypoint
        :return: StateSE2 referring to position of the waypoint
        """
        return self._oriented_box.center

    @property
    def time_point(self) -> TimePoint:
        """
        Getter for time point corresponding to the waypoint
        :return: The time point
        """
        return self._time_point

    @property
    def oriented_box(self) -> OrientedBox:
        """
        Getter for the oriented box corresponding to the waypoint
        :return: The oriented box
        """
        return self._oriented_box

    @property
    def x(self) -> float:
        """
        Getter for the x position of the waypoint
        :return: The x position
        """
        return self._oriented_box.center.x

    @property
    def y(self) -> float:
        """
        Getter for the y position of the waypoint
        :return: The y position
        """
        return self._oriented_box.center.y

    @property
    def heading(self) -> float:
        """
        Getter for the heading of the waypoint
        :return: The heading
        """
        return self._oriented_box.center.heading

    @property
    def velocity(self) -> Optional[StateVector2D]:
        """
        Getter for the velocity corresponding to the waypoint
        :return: The velocity, None if not available
        """
        return self._velocity

    def serialize(self) -> List[Union[int, float]]:
        """
        Serializes the object as a list
        :return: Serialized object as a list
        """
        return [self.time_point.time_us, self._oriented_box.center.x, self._oriented_box.center.y, self._oriented_box.center.heading, self._oriented_box.length, self._oriented_box.width, self._oriented_box.height, self._velocity.x if self._velocity is not None else None, self._velocity.y if self._velocity is not None else None]

    @staticmethod
    def deserialize(vector: List[Union[int, float]]) -> Waypoint:
        """
        Deserializes the object.
        :param vector: a list of data to initialize a waypoint
        :return: Waypoint
        """
        assert len(vector) == 9, f'Expected a vector of size 9, got {len(vector)}'
        return Waypoint(time_point=TimePoint(int(vector[0])), oriented_box=OrientedBox(StateSE2(vector[1], vector[2], vector[3]), vector[4], vector[5], vector[6]), velocity=StateVector2D(vector[7], vector[8]) if vector[7] is not None and vector[8] is not None else None)

    def to_split_state(self) -> SplitState:
        """Inherited, see superclass."""
        linear_states = [self.time_point.time_us, self._oriented_box.center.x, self._oriented_box.center.y, self._velocity.x if self._velocity is not None else None, self._velocity.y if self._velocity is not None else None]
        angular_states = [self._oriented_box.center.heading]
        fixed_state = [self._oriented_box.width, self._oriented_box.length, self._oriented_box.height]
        return SplitState(linear_states, angular_states, fixed_state)

    @staticmethod
    def from_split_state(split_state: SplitState) -> Waypoint:
        """Inherited, see superclass."""
        total_state_length = len(split_state)
        assert total_state_length == 9, f'Expected a vector of size 9, got {total_state_length}'
        return Waypoint(time_point=TimePoint(int(split_state.linear_states[0])), oriented_box=OrientedBox(StateSE2(split_state.linear_states[1], split_state.linear_states[2], split_state.angular_states[0]), length=split_state.fixed_states[1], width=split_state.fixed_states[0], height=split_state.fixed_states[2]), velocity=StateVector2D(split_state.linear_states[3], split_state.linear_states[4]) if split_state.linear_states[3] is not None and split_state.linear_states[4] is not None else None)

def __iter__(self) -> Iterable[Union[int, float]]:
    """
        Iterator for waypoint variables.
        :return: An iterator to the variables of the Waypoint.
        """
    return iter((self.time_us, self._oriented_box.center.x, self._oriented_box.center.y, self._oriented_box.center.heading, self._velocity.x if self._velocity is not None else None, self._velocity.y if self._velocity is not None else None))

class TestWaypoint(unittest.TestCase):
    """Tests Waypoint class"""

    def setUp(self) -> None:
        """Sets sample parameters for testing"""
        mock_time_point = Mock(time_us=0)
        mock_box = Mock(center=Mock(x='center_x', y='center_y', heading='center_heading'), length='length', width='width', height='height')
        mock_velocity = Mock(x='velocity_x', y='velocity_y')
        self.waypoint = Waypoint(mock_time_point, mock_box, mock_velocity)
        self.waypoint_no_vel = Waypoint(mock_time_point, mock_box)

    def test_iterable(self) -> None:
        """Test that the iterable gets built correctly."""
        iterable_waypoint = iter(self.waypoint)
        iterable_expected = [0, 'center_x', 'center_y', 'center_heading', 'velocity_x', 'velocity_y']
        for expected, actual in zip(iterable_expected, iterable_waypoint):
            self.assertEqual(expected, actual)
        iterable_waypoint_no_vel = iter(self.waypoint_no_vel)
        iterable_expected = [0, 'center_x', 'center_y', 'center_heading', None, None]
        for expected, actual in zip(iterable_expected, iterable_waypoint_no_vel):
            self.assertEqual(expected, actual)

    def test_serialize(self) -> None:
        """Tests that the serialization works as expected."""
        serialized_waypoint = self.waypoint.serialize()
        serialized_expected = [0, 'center_x', 'center_y', 'center_heading', 'length', 'width', 'height', 'velocity_x', 'velocity_y']
        self.assertEqual(serialized_expected, serialized_waypoint)
        serialized_waypoint_no_vel = self.waypoint_no_vel.serialize()
        serialized_no_vel_expected = [0, 'center_x', 'center_y', 'center_heading', 'length', 'width', 'height', None, None]
        self.assertEqual(serialized_no_vel_expected, serialized_waypoint_no_vel)

    @patch('nuplan.common.actor_state.waypoint.StateVector2D')
    @patch('nuplan.common.actor_state.waypoint.OrientedBox')
    @patch('nuplan.common.actor_state.waypoint.TimePoint')
    @patch('nuplan.common.actor_state.waypoint.StateSE2')
    @patch('nuplan.common.actor_state.waypoint.Waypoint')
    def test_deserialize(self, mock_waypoint: Mock, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_velocity: Mock) -> None:
        """Tests that the object is deserialized correctly."""
        mock_se2.return_value = 'se2'
        mock_time_point.return_value = 'time_point'
        mock_box.return_value = 'mock_box'
        mock_velocity.return_value = 'velocity'
        waypoint = self.waypoint.deserialize([0, 1, 2, 3, 4, 5, 6, 7, 8])
        mock_time_point.assert_called_once_with(0)
        mock_se2.assert_called_once_with(1, 2, 3)
        mock_box.assert_called_once_with(mock_se2.return_value, 4, 5, 6)
        mock_velocity.assert_called_once_with(7, 8)
        mock_waypoint.assert_called_with(time_point=mock_time_point.return_value, oriented_box=mock_box.return_value, velocity=mock_velocity.return_value)
        self.assertEqual(mock_waypoint.return_value, waypoint)

    @patch('nuplan.common.actor_state.waypoint.StateVector2D')
    @patch('nuplan.common.actor_state.waypoint.OrientedBox')
    @patch('nuplan.common.actor_state.waypoint.TimePoint')
    @patch('nuplan.common.actor_state.waypoint.StateSE2')
    @patch('nuplan.common.actor_state.waypoint.Waypoint')
    def test_deserialize_no_velocity(self, mock_waypoint: Mock, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_velocity: Mock) -> None:
        """Tests that the object is deserialized correctly when no velocity is provided."""
        mock_se2.return_value = 'se2'
        mock_time_point.return_value = 'time_point'
        mock_box.return_value = 'mock_box'
        mock_velocity.return_value = 'velocity'
        waypoint = self.waypoint.deserialize([0, 1, 2, 3, 4, 5, 6, None, None])
        mock_time_point.assert_called_once_with(0)
        mock_se2.assert_called_once_with(1, 2, 3)
        mock_box.assert_called_once_with(mock_se2.return_value, 4, 5, 6)
        mock_velocity.assert_not_called()
        mock_waypoint.assert_called_with(time_point=mock_time_point.return_value, oriented_box=mock_box.return_value, velocity=None)
        self.assertEqual(mock_waypoint.return_value, waypoint)

    @patch('nuplan.common.actor_state.waypoint.SplitState', autospec=True)
    def test_to_split_state(self, mock_split_state: Mock) -> None:
        """Tests that the object is split correctly"""
        result = self.waypoint.to_split_state()
        expected_linear_states = [0, 'center_x', 'center_y', 'velocity_x', 'velocity_y']
        expected_angular_states = ['center_heading']
        expected_fixed_states = ['width', 'length', 'height']
        mock_split_state.assert_called_once_with(expected_linear_states, expected_angular_states, expected_fixed_states)
        self.assertEqual(result, mock_split_state.return_value)

    @patch('nuplan.common.actor_state.waypoint.StateVector2D', autospec=True)
    @patch('nuplan.common.actor_state.waypoint.OrientedBox', autospec=True)
    @patch('nuplan.common.actor_state.waypoint.TimePoint', autospec=True)
    @patch('nuplan.common.actor_state.waypoint.StateSE2', autospec=True)
    def test_from_split_state(self, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_vector: Mock) -> None:
        """Tests that the object is recreated correctly from a split state"""
        split_state = self.waypoint.to_split_state()
        result = self.waypoint.from_split_state(split_state)
        mock_time_point.assert_called_once_with(0)
        mock_se2.assert_called_once_with('center_x', 'center_y', 'center_heading')
        mock_vector.assert_called_once_with('velocity_x', 'velocity_y')
        mock_box.assert_called_once_with(mock_se2.return_value, length='length', width='width', height='height')
        self.assertEqual(result.time_point, mock_time_point.return_value)
        self.assertEqual(result.oriented_box, mock_box.return_value)
        self.assertEqual(result.velocity, mock_vector.return_value)

def test_iterable(self) -> None:
    """Test that the iterable gets built correctly."""
    iterable_waypoint = iter(self.waypoint)
    iterable_expected = [0, 'center_x', 'center_y', 'center_heading', 'velocity_x', 'velocity_y']
    for expected, actual in zip(iterable_expected, iterable_waypoint):
        self.assertEqual(expected, actual)
    iterable_waypoint_no_vel = iter(self.waypoint_no_vel)
    iterable_expected = [0, 'center_x', 'center_y', 'center_heading', None, None]
    for expected, actual in zip(iterable_expected, iterable_waypoint_no_vel):
        self.assertEqual(expected, actual)

@patch('nuplan.common.actor_state.waypoint.StateVector2D')
@patch('nuplan.common.actor_state.waypoint.OrientedBox')
@patch('nuplan.common.actor_state.waypoint.TimePoint')
@patch('nuplan.common.actor_state.waypoint.StateSE2')
@patch('nuplan.common.actor_state.waypoint.Waypoint')
def test_deserialize(self, mock_waypoint: Mock, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_velocity: Mock) -> None:
    """Tests that the object is deserialized correctly."""
    mock_se2.return_value = 'se2'
    mock_time_point.return_value = 'time_point'
    mock_box.return_value = 'mock_box'
    mock_velocity.return_value = 'velocity'
    waypoint = self.waypoint.deserialize([0, 1, 2, 3, 4, 5, 6, 7, 8])
    mock_time_point.assert_called_once_with(0)
    mock_se2.assert_called_once_with(1, 2, 3)
    mock_box.assert_called_once_with(mock_se2.return_value, 4, 5, 6)
    mock_velocity.assert_called_once_with(7, 8)
    mock_waypoint.assert_called_with(time_point=mock_time_point.return_value, oriented_box=mock_box.return_value, velocity=mock_velocity.return_value)
    self.assertEqual(mock_waypoint.return_value, waypoint)

@patch('nuplan.common.actor_state.waypoint.StateVector2D')
@patch('nuplan.common.actor_state.waypoint.OrientedBox')
@patch('nuplan.common.actor_state.waypoint.TimePoint')
@patch('nuplan.common.actor_state.waypoint.StateSE2')
@patch('nuplan.common.actor_state.waypoint.Waypoint')
def test_deserialize_no_velocity(self, mock_waypoint: Mock, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_velocity: Mock) -> None:
    """Tests that the object is deserialized correctly when no velocity is provided."""
    mock_se2.return_value = 'se2'
    mock_time_point.return_value = 'time_point'
    mock_box.return_value = 'mock_box'
    mock_velocity.return_value = 'velocity'
    waypoint = self.waypoint.deserialize([0, 1, 2, 3, 4, 5, 6, None, None])
    mock_time_point.assert_called_once_with(0)
    mock_se2.assert_called_once_with(1, 2, 3)
    mock_box.assert_called_once_with(mock_se2.return_value, 4, 5, 6)
    mock_velocity.assert_not_called()
    mock_waypoint.assert_called_with(time_point=mock_time_point.return_value, oriented_box=mock_box.return_value, velocity=None)
    self.assertEqual(mock_waypoint.return_value, waypoint)

@patch('nuplan.common.actor_state.waypoint.SplitState', autospec=True)
def test_to_split_state(self, mock_split_state: Mock) -> None:
    """Tests that the object is split correctly"""
    result = self.waypoint.to_split_state()
    expected_linear_states = [0, 'center_x', 'center_y', 'velocity_x', 'velocity_y']
    expected_angular_states = ['center_heading']
    expected_fixed_states = ['width', 'length', 'height']
    mock_split_state.assert_called_once_with(expected_linear_states, expected_angular_states, expected_fixed_states)
    self.assertEqual(result, mock_split_state.return_value)

@patch('nuplan.common.actor_state.waypoint.StateVector2D', autospec=True)
@patch('nuplan.common.actor_state.waypoint.OrientedBox', autospec=True)
@patch('nuplan.common.actor_state.waypoint.TimePoint', autospec=True)
@patch('nuplan.common.actor_state.waypoint.StateSE2', autospec=True)
def test_from_split_state(self, mock_se2: Mock, mock_time_point: Mock, mock_box: Mock, mock_vector: Mock) -> None:
    """Tests that the object is recreated correctly from a split state"""
    split_state = self.waypoint.to_split_state()
    result = self.waypoint.from_split_state(split_state)
    mock_time_point.assert_called_once_with(0)
    mock_se2.assert_called_once_with('center_x', 'center_y', 'center_heading')
    mock_vector.assert_called_once_with('velocity_x', 'velocity_y')
    mock_box.assert_called_once_with(mock_se2.return_value, length='length', width='width', height='height')
    self.assertEqual(result.time_point, mock_time_point.return_value)
    self.assertEqual(result.oriented_box, mock_box.return_value)
    self.assertEqual(result.velocity, mock_vector.return_value)

class TestEgoState(unittest.TestCase):
    """Tests EgoState class"""

    def setUp(self) -> None:
        """Creates sample parameters for testing"""
        self.ego_state = get_sample_ego_state()
        self.vehicle = get_pacifica_parameters()
        self.dynamic_car_state = get_sample_dynamic_car_state(self.vehicle.rear_axle_to_center)

    def test_ego_state_extended_construction(self) -> None:
        """Tests that the ego state extended can be constructed from a pre-existing ego state."""
        ego_state_ext = EgoState.build_from_rear_axle(rear_axle_pose=self.ego_state.rear_axle, rear_axle_velocity_2d=self.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=self.dynamic_car_state.rear_axle_acceleration_2d, tire_steering_angle=self.ego_state.tire_steering_angle, time_point=self.ego_state.time_point, angular_vel=self.dynamic_car_state.angular_velocity, angular_accel=self.dynamic_car_state.angular_acceleration, is_in_auto_mode=True, vehicle_parameters=self.vehicle)
        self.assertTrue(ego_state_ext.dynamic_car_state == self.dynamic_car_state)
        self.assertTrue(ego_state_ext.center == self.ego_state.center)
        wp = ego_state_ext.waypoint
        self.assertEqual(wp.time_point, ego_state_ext.time_point)
        self.assertEqual(wp.oriented_box, ego_state_ext.car_footprint)
        self.assertEqual(wp.velocity, ego_state_ext.dynamic_car_state.rear_axle_velocity_2d)

    def test_to_split_state(self) -> None:
        """Tests that the state gets split as expected"""
        split_state = self.ego_state.to_split_state()
        self.assertEqual(len(split_state.linear_states), 8)
        self.assertEqual(split_state.fixed_states, [self.ego_state.car_footprint.vehicle_parameters])
        self.assertEqual(split_state.angular_states, [self.ego_state.rear_axle.heading])

    def test_from_split_state(self) -> None:
        """Tests that the object gets created as expected from the split state"""
        split_state = SplitState([0, 1, 2, 3, 4, 5, 6, 7], [8], [self.ego_state.car_footprint.vehicle_parameters])
        ego_from_split = EgoState.from_split_state(split_state)
        self.assertEqual(self.ego_state.car_footprint.vehicle_parameters, ego_from_split.car_footprint.vehicle_parameters)
        self.assertAlmostEqual(ego_from_split.time_us, 0)
        self.assertAlmostEqual(ego_from_split.rear_axle.x, 1)
        self.assertAlmostEqual(ego_from_split.rear_axle.y, 2)
        self.assertAlmostEqual(ego_from_split.rear_axle.heading, 8)
        self.assertAlmostEqual(ego_from_split.dynamic_car_state.rear_axle_velocity_2d.x, 3)
        self.assertAlmostEqual(ego_from_split.dynamic_car_state.rear_axle_velocity_2d.y, 4)
        self.assertAlmostEqual(ego_from_split.dynamic_car_state.rear_axle_acceleration_2d.x, 5)
        self.assertAlmostEqual(ego_from_split.dynamic_car_state.rear_axle_acceleration_2d.y, 6)
        self.assertAlmostEqual(ego_from_split.tire_steering_angle, 7)

def test_to_split_state(self) -> None:
    """Tests that the state gets split as expected"""
    split_state = self.ego_state.to_split_state()
    self.assertEqual(len(split_state.linear_states), 8)
    self.assertEqual(split_state.fixed_states, [self.ego_state.car_footprint.vehicle_parameters])
    self.assertEqual(split_state.angular_states, [self.ego_state.rear_axle.heading])

class TestDynamicCarState(unittest.TestCase):
    """Tests DynamicCarState class and helper functions"""

    def setUp(self) -> None:
        """Sets sample variables for testing"""
        self.displacement = StateVector2D(2.0, 2.0)
        self.reference_vector = StateVector2D(2.3, 3.4)
        self.angular_velocity = 0.2
        self.dynamic_car_state = DynamicCarState(rear_axle_to_center_dist=1, rear_axle_velocity_2d=self.reference_vector, rear_axle_acceleration_2d=StateVector2D(0.1, 0.2), angular_velocity=2, angular_acceleration=2.5, tire_steering_rate=0.5)

    def test_velocity_transfer(self) -> None:
        """Tests behavior of velocity transfer formula for planar rigid bodies."""
        actual_velocity = get_velocity_shifted(self.displacement, self.reference_vector, self.angular_velocity)
        expected_velocity_p2 = StateVector2D(1.9, 3.8)
        np.testing.assert_array_almost_equal(expected_velocity_p2.array, actual_velocity.array, 6)
        actual_velocity = get_velocity_shifted(StateVector2D(0.0, 0.0), self.reference_vector, self.angular_velocity)
        np.testing.assert_array_almost_equal(self.reference_vector.array, actual_velocity.array, 6)
        actual_velocity = get_velocity_shifted(self.displacement, self.reference_vector, 0)
        np.testing.assert_array_almost_equal(self.reference_vector.array, actual_velocity.array, 6)

    def test_acceleration_transfer(self) -> None:
        """Tests behavior of acceleration transfer formula for planar rigid bodies."""
        angular_acceleration = 0.234
        actual_acceleration = get_acceleration_shifted(self.displacement, self.reference_vector, self.angular_velocity, angular_acceleration)
        np.testing.assert_array_almost_equal(StateVector2D(2.848, 3.948).array, actual_acceleration.array, 6)
        actual_acceleration = get_acceleration_shifted(StateVector2D(0.0, 0.0), self.reference_vector, self.angular_velocity, angular_acceleration)
        np.testing.assert_array_almost_equal(self.reference_vector.array, actual_acceleration.array, 6)
        actual_acceleration = get_acceleration_shifted(self.displacement, self.reference_vector, 0, 0)
        np.testing.assert_array_almost_equal(self.reference_vector.array, actual_acceleration.array, 6)

    def test_initialization(self) -> None:
        """Tests that object initialization works as intended"""
        self.assertEqual(1, self.dynamic_car_state._rear_axle_to_center_dist)
        self.assertEqual(self.reference_vector, self.dynamic_car_state._rear_axle_velocity_2d)
        self.assertEqual(StateVector2D(0.1, 0.2), self.dynamic_car_state._rear_axle_acceleration_2d)
        self.assertEqual(2, self.dynamic_car_state._angular_velocity)
        self.assertEqual(2.5, self.dynamic_car_state._angular_acceleration)
        self.assertEqual(0.5, self.dynamic_car_state._tire_steering_rate)

    def test_properties(self) -> None:
        """Checks that the properties return the expected variables."""
        self.assertTrue(self.dynamic_car_state.rear_axle_velocity_2d is self.dynamic_car_state._rear_axle_velocity_2d)
        self.assertTrue(self.dynamic_car_state.rear_axle_acceleration_2d is self.dynamic_car_state._rear_axle_acceleration_2d)
        self.assertTrue(self.dynamic_car_state.tire_steering_rate is self.dynamic_car_state._tire_steering_rate)
        self.assertTrue(self.dynamic_car_state.tire_steering_rate is self.dynamic_car_state._tire_steering_rate)
        self.assertAlmostEqual(4.104875150354758, self.dynamic_car_state.speed)
        self.assertEqual(0.22360679774997896, self.dynamic_car_state.acceleration)

    @patch('nuplan.common.actor_state.dynamic_car_state.StateVector2D', Mock())
    @patch('nuplan.common.actor_state.dynamic_car_state.DynamicCarState', autospec=DynamicCarState)
    def test_build_from_rear_axle(self, mock_dynamic_car_state: Mock) -> None:
        """Tests that constructor from rear axle behaves as intended."""
        mock_velocity = Mock()
        mock_acceleration = Mock()
        self.dynamic_car_state.build_from_rear_axle(1, mock_velocity, mock_acceleration, 4, 5, 6)
        mock_dynamic_car_state.assert_called_with(rear_axle_to_center_dist=1, rear_axle_velocity_2d=mock_velocity, rear_axle_acceleration_2d=mock_acceleration, angular_velocity=4, angular_acceleration=5, tire_steering_rate=6)

    @patch('nuplan.common.actor_state.dynamic_car_state.StateVector2D')
    @patch('nuplan.common.actor_state.dynamic_car_state.math', Mock())
    @patch('nuplan.common.actor_state.dynamic_car_state._angular_velocity_from_cog')
    @patch('nuplan.common.actor_state.dynamic_car_state._projected_velocities_from_cog')
    @patch('nuplan.common.actor_state.dynamic_car_state._project_accelerations_from_cog')
    @patch('nuplan.common.actor_state.dynamic_car_state._get_beta')
    @patch('nuplan.common.actor_state.dynamic_car_state.DynamicCarState', autospec=DynamicCarState)
    def test_build_from_cog(self, mock_dynamic_car_state: Mock, mock_beta: Mock, mock_accelerations: Mock, mock_velocities: Mock, mock_angular_velocity: Mock, mock_vector: Mock) -> None:
        """Checks that constructor from COG computes the correct projections."""
        wheel_base = MagicMock(return_value='wheel_base')
        rear_axle_to_center = MagicMock(return_value='rear_axle_to_center')
        cog_speed = MagicMock(return_value='cog_speed')
        cog_acceleration = MagicMock(return_value='cog_acceleration')
        steering_angle = MagicMock(return_value='steering_angle')
        angular_accel = MagicMock(return_value='angular_accel')
        tire_steering_rate = MagicMock(return_value='tire_steering_rate')
        mock_velocities.return_value = ('x_vel', 'y_vel')
        mock_accelerations.return_value = ('x_acc', 'y_acc')
        self.dynamic_car_state.build_from_cog(wheel_base, rear_axle_to_center, cog_speed, cog_acceleration, steering_angle, angular_accel, tire_steering_rate)
        mock_beta.assert_called_once_with(steering_angle, wheel_base)
        mock_velocities.assert_called_once_with(mock_beta.return_value, cog_speed)
        mock_angular_velocity.assert_called_once_with(cog_speed, wheel_base, mock_beta.return_value, steering_angle)
        mock_accelerations.assert_called_once_with('x_vel', mock_angular_velocity.return_value, cog_acceleration, mock_beta.return_value)
        mock_dynamic_car_state.assert_called_with(rear_axle_to_center_dist=rear_axle_to_center, rear_axle_velocity_2d=mock_vector(mock_velocities.return_value), rear_axle_acceleration_2d=mock_vector(mock_accelerations.return_value), angular_velocity=mock_angular_velocity.return_value, angular_acceleration=angular_accel, tire_steering_rate=tire_steering_rate)

@patch('nuplan.common.actor_state.dynamic_car_state.StateVector2D', Mock())
@patch('nuplan.common.actor_state.dynamic_car_state.DynamicCarState', autospec=DynamicCarState)
def test_build_from_rear_axle(self, mock_dynamic_car_state: Mock) -> None:
    """Tests that constructor from rear axle behaves as intended."""
    mock_velocity = Mock()
    mock_acceleration = Mock()
    self.dynamic_car_state.build_from_rear_axle(1, mock_velocity, mock_acceleration, 4, 5, 6)
    mock_dynamic_car_state.assert_called_with(rear_axle_to_center_dist=1, rear_axle_velocity_2d=mock_velocity, rear_axle_acceleration_2d=mock_acceleration, angular_velocity=4, angular_acceleration=5, tire_steering_rate=6)

@patch('nuplan.common.actor_state.dynamic_car_state.StateVector2D')
@patch('nuplan.common.actor_state.dynamic_car_state.math', Mock())
@patch('nuplan.common.actor_state.dynamic_car_state._angular_velocity_from_cog')
@patch('nuplan.common.actor_state.dynamic_car_state._projected_velocities_from_cog')
@patch('nuplan.common.actor_state.dynamic_car_state._project_accelerations_from_cog')
@patch('nuplan.common.actor_state.dynamic_car_state._get_beta')
@patch('nuplan.common.actor_state.dynamic_car_state.DynamicCarState', autospec=DynamicCarState)
def test_build_from_cog(self, mock_dynamic_car_state: Mock, mock_beta: Mock, mock_accelerations: Mock, mock_velocities: Mock, mock_angular_velocity: Mock, mock_vector: Mock) -> None:
    """Checks that constructor from COG computes the correct projections."""
    wheel_base = MagicMock(return_value='wheel_base')
    rear_axle_to_center = MagicMock(return_value='rear_axle_to_center')
    cog_speed = MagicMock(return_value='cog_speed')
    cog_acceleration = MagicMock(return_value='cog_acceleration')
    steering_angle = MagicMock(return_value='steering_angle')
    angular_accel = MagicMock(return_value='angular_accel')
    tire_steering_rate = MagicMock(return_value='tire_steering_rate')
    mock_velocities.return_value = ('x_vel', 'y_vel')
    mock_accelerations.return_value = ('x_acc', 'y_acc')
    self.dynamic_car_state.build_from_cog(wheel_base, rear_axle_to_center, cog_speed, cog_acceleration, steering_angle, angular_accel, tire_steering_rate)
    mock_beta.assert_called_once_with(steering_angle, wheel_base)
    mock_velocities.assert_called_once_with(mock_beta.return_value, cog_speed)
    mock_angular_velocity.assert_called_once_with(cog_speed, wheel_base, mock_beta.return_value, steering_angle)
    mock_accelerations.assert_called_once_with('x_vel', mock_angular_velocity.return_value, cog_acceleration, mock_beta.return_value)
    mock_dynamic_car_state.assert_called_with(rear_axle_to_center_dist=rear_axle_to_center, rear_axle_velocity_2d=mock_vector(mock_velocities.return_value), rear_axle_acceleration_2d=mock_vector(mock_accelerations.return_value), angular_velocity=mock_angular_velocity.return_value, angular_acceleration=angular_accel, tire_steering_rate=tire_steering_rate)

class TestSceneObject(unittest.TestCase):
    """Tests SceneObject class"""

    @patch('nuplan.common.actor_state.tracked_objects_types.TrackedObjectType')
    @patch('nuplan.common.actor_state.oriented_box.OrientedBox')
    def test_initialization(self, mock_box: Mock, mock_tracked_object_type: Mock) -> None:
        """Tests that agents can be initialized correctly"""
        scene_object = SceneObject(mock_tracked_object_type, mock_box, SceneObjectMetadata(1, '123', 1, '456'))
        self.assertEqual('123', scene_object.token)
        self.assertEqual('456', scene_object.track_token)
        self.assertEqual(mock_box, scene_object.box)
        self.assertEqual(mock_tracked_object_type, scene_object.tracked_object_type)

    @patch('nuplan.common.actor_state.scene_object.StateSE2')
    @patch('nuplan.common.actor_state.scene_object.OrientedBox')
    @patch('nuplan.common.actor_state.scene_object.TrackedObjectType')
    @patch('nuplan.common.actor_state.scene_object.SceneObject.__init__')
    def test_construction(self, mock_init: Mock, mock_type: Mock, mock_box_object: Mock, mock_state: Mock) -> None:
        """Test that agents can be constructed correctly."""
        mock_init.return_value = None
        mock_box = Mock()
        mock_box_object.return_value = mock_box
        _ = SceneObject.from_raw_params('123', '123', 1, 1, mock_state, size=(3, 2, 1))
        mock_box_object.assert_called_with(mock_state, width=3, length=2, height=1)
        mock_init.assert_called_with(metadata=SceneObjectMetadata(token='123', track_token='123', timestamp_us=1, track_id=1), tracked_object_type=mock_type.GENERIC_OBJECT, oriented_box=mock_box)

@patch('nuplan.common.actor_state.scene_object.StateSE2')
@patch('nuplan.common.actor_state.scene_object.OrientedBox')
@patch('nuplan.common.actor_state.scene_object.TrackedObjectType')
@patch('nuplan.common.actor_state.scene_object.SceneObject.__init__')
def test_construction(self, mock_init: Mock, mock_type: Mock, mock_box_object: Mock, mock_state: Mock) -> None:
    """Test that agents can be constructed correctly."""
    mock_init.return_value = None
    mock_box = Mock()
    mock_box_object.return_value = mock_box
    _ = SceneObject.from_raw_params('123', '123', 1, 1, mock_state, size=(3, 2, 1))
    mock_box_object.assert_called_with(mock_state, width=3, length=2, height=1)
    mock_init.assert_called_with(metadata=SceneObjectMetadata(token='123', track_token='123', timestamp_us=1, track_id=1), tracked_object_type=mock_type.GENERIC_OBJECT, oriented_box=mock_box)

class TestConvert(unittest.TestCase):
    """Tests for convert functions"""

    def test_pose_from_matrix(self) -> None:
        """Tests conversion from 3x3 transformation matrix to a 2D pose"""
        transform_matrix: npt.NDArray[np.float32] = np.array([[np.sqrt(3) / 2, -0.5, 2], [0.5, np.sqrt(3) / 2, 2], [0, 0, 1]], dtype=np.float32)
        expected_pose = StateSE2(2, 2, np.pi / 6)
        result = pose_from_matrix(transform_matrix=transform_matrix)
        self.assertAlmostEqual(result.x, expected_pose.x)
        self.assertAlmostEqual(result.y, expected_pose.y)
        self.assertAlmostEqual(result.heading, expected_pose.heading)
        with self.assertRaises(RuntimeError):
            bad_matrix: npt.NDArray[np.float32] = np.array([[np.sqrt(3) / 2, -0.5, 2], [0.5, np.sqrt(3) / 2, 2]], dtype=np.float32)
            _ = pose_from_matrix(transform_matrix=bad_matrix)

    def test_matrix_from_pose(self) -> None:
        """Tests conversion from 2D pose to a 3x3 transformation matrix"""
        pose = StateSE2(2, 2, np.pi / 6)
        expected_transform_matrix: npt.NDArray[np.float32] = np.array([[np.sqrt(3) / 2, -0.5, 2], [0.5, np.sqrt(3) / 2, 2], [0, 0, 1]], dtype=np.float32)
        result = matrix_from_pose(pose=pose)
        np.testing.assert_array_almost_equal(result, expected_transform_matrix)

    def test_absolute_to_relative_poses(self) -> None:
        """Tests conversion of a list of SE2 poses from absolute to relative coordinates"""
        inv_sqrt_2 = 1 / np.sqrt(2)
        origin = StateSE2(1, 1, np.pi / 4)
        poses = [origin, StateSE2(1, 1, np.pi / 2), StateSE2(1, 1, np.pi / 4), StateSE2(2, 3, 0), StateSE2(3, 2, 0)]
        expected_poses = [StateSE2(0, 0, 0), StateSE2(0, 0, np.pi / 4), StateSE2(0, 0, 0), StateSE2(3 * inv_sqrt_2, inv_sqrt_2, -np.pi / 4), StateSE2(3 * inv_sqrt_2, -inv_sqrt_2, -np.pi / 4)]
        result = absolute_to_relative_poses(poses)
        for i in range(len(result)):
            self.assertAlmostEqual(result[i].x, expected_poses[i].x)
            self.assertAlmostEqual(result[i].y, expected_poses[i].y)
            self.assertAlmostEqual(result[i].heading, expected_poses[i].heading)

    def test_relative_to_absolute_poses(self) -> None:
        """Tests conversion of a list of SE2 poses from relative to absolute coordinates"""
        inv_sqrt_2 = 1 / np.sqrt(2)
        origin = StateSE2(1, 1, np.pi / 4)
        poses = [StateSE2(0, 0, np.pi / 4), StateSE2(0, 0, 0), StateSE2(3 * inv_sqrt_2, inv_sqrt_2, -np.pi / 4), StateSE2(3 * inv_sqrt_2, -inv_sqrt_2, -np.pi / 4)]
        expected_poses = [StateSE2(1, 1, np.pi / 2), StateSE2(1, 1, np.pi / 4), StateSE2(2, 3, 0), StateSE2(3, 2, 0)]
        result = relative_to_absolute_poses(origin, poses)
        for i in range(len(result)):
            self.assertAlmostEqual(result[i].x, expected_poses[i].x)
            self.assertAlmostEqual(result[i].y, expected_poses[i].y)
            self.assertAlmostEqual(result[i].heading, expected_poses[i].heading)

    def test_input_numpy_array_to_absolute_velocity(self) -> None:
        """Tests input validation of numpy_array_to_absolute_velocity"""
        np_velocities = np.random.random(size=(10, 3))
        with self.assertRaises(AssertionError):
            numpy_array_to_absolute_velocity(StateSE2(0, 0, 0), np_velocities)

    @patch('nuplan.common.geometry.convert.relative_to_absolute_poses')
    def test_numpy_array_to_absolute_velocity(self, mock_relative_to_absolute_poses: Mock) -> None:
        """Tests conversion from relative numpy velocities to list of absolute velocities"""
        np_velocities: npt.NDArray[np.float32] = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
        num_velocities = len(np_velocities)
        mock_relative_to_absolute_poses.side_effect = lambda _, r_s: r_s
        result = numpy_array_to_absolute_velocity('origin', np_velocities)
        mock_relative_to_absolute_poses.assert_called_once()
        self.assertEqual(num_velocities, len(result))
        for i in range(num_velocities):
            self.assertEqual(result[i].x, np_velocities[i][0])
            self.assertEqual(result[i].y, np_velocities[i][1])

    def test_input_numpy_array_to_absolute_pose_input(self) -> None:
        """Tests input validation of numpy_array_to_absolute_pose_input"""
        np_poses = np.random.random((10, 2))
        with self.assertRaises(AssertionError):
            numpy_array_to_absolute_pose(StateSE2(0, 0, 0), np_poses)

    @patch('nuplan.common.geometry.convert.relative_to_absolute_poses')
    def test_numpy_array_to_absolute_pose(self, mock_relative_to_absolute_poses: Mock) -> None:
        """Tests conversion from relative numpy poses to list of absolute StateSE2 objects."""
        np_poses = np.random.random((10, 3))
        mock_relative_to_absolute_poses.side_effect = lambda _, r_s: r_s
        result = numpy_array_to_absolute_pose('origin', np_poses)
        mock_relative_to_absolute_poses.assert_called_once()
        for np_p, se2_p in zip(np_poses, result):
            self.assertEqual(np_p[0], se2_p.x)
            self.assertEqual(np_p[1], se2_p.y)
            self.assertEqual(np_p[2], se2_p.heading)

    @patch('nuplan.common.geometry.convert.np')
    @patch('nuplan.common.geometry.convert.StateVector2D')
    def test_vector_2d_from_magnitude_angle(self, vector: Mock, mock_np: Mock) -> None:
        """Tests that projection to vector works as expected."""
        magnitude = Mock()
        angle = Mock()
        result = vector_2d_from_magnitude_angle(magnitude, angle)
        self.assertEqual(result, vector.return_value)
        vector.assert_called_once_with(mock_np.cos() * magnitude, mock_np.sin() * angle)

@patch('nuplan.common.geometry.convert.relative_to_absolute_poses')
def test_numpy_array_to_absolute_velocity(self, mock_relative_to_absolute_poses: Mock) -> None:
    """Tests conversion from relative numpy velocities to list of absolute velocities"""
    np_velocities: npt.NDArray[np.float32] = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
    num_velocities = len(np_velocities)
    mock_relative_to_absolute_poses.side_effect = lambda _, r_s: r_s
    result = numpy_array_to_absolute_velocity('origin', np_velocities)
    mock_relative_to_absolute_poses.assert_called_once()
    self.assertEqual(num_velocities, len(result))
    for i in range(num_velocities):
        self.assertEqual(result[i].x, np_velocities[i][0])
        self.assertEqual(result[i].y, np_velocities[i][1])

@patch('nuplan.common.geometry.convert.relative_to_absolute_poses')
def test_numpy_array_to_absolute_pose(self, mock_relative_to_absolute_poses: Mock) -> None:
    """Tests conversion from relative numpy poses to list of absolute StateSE2 objects."""
    np_poses = np.random.random((10, 3))
    mock_relative_to_absolute_poses.side_effect = lambda _, r_s: r_s
    result = numpy_array_to_absolute_pose('origin', np_poses)
    mock_relative_to_absolute_poses.assert_called_once()
    for np_p, se2_p in zip(np_poses, result):
        self.assertEqual(np_p[0], se2_p.x)
        self.assertEqual(np_p[1], se2_p.y)
        self.assertEqual(np_p[2], se2_p.heading)

@patch('nuplan.common.geometry.convert.np')
@patch('nuplan.common.geometry.convert.StateVector2D')
def test_vector_2d_from_magnitude_angle(self, vector: Mock, mock_np: Mock) -> None:
    """Tests that projection to vector works as expected."""
    magnitude = Mock()
    angle = Mock()
    result = vector_2d_from_magnitude_angle(magnitude, angle)
    self.assertEqual(result, vector.return_value)
    vector.assert_called_once_with(mock_np.cos() * magnitude, mock_np.sin() * angle)

class TestTransform(unittest.TestCase):
    """Tests for transform functions"""

    def test_rotate_2d(self) -> None:
        """Tests rotation of 2D point"""
        point = Point2D(1, 0)
        rotation_matrix: npt.NDArray[np.float32] = np.array([[0, 1], [-1, 0]], dtype=np.float32)
        result = rotate_2d(point, rotation_matrix)
        self.assertEqual(result, Point2D(0, 1))

    def test_translate(self) -> None:
        """Tests translate"""
        pose = StateSE2(3, 5, np.pi / 4)
        translation: npt.NDArray[np.float32] = np.array([1, 2], dtype=np.float32)
        result = translate(pose, translation)
        self.assertEqual(result, StateSE2(4, 7, np.pi / 4))

    def test_rotate(self) -> None:
        """Tests rotation of SE2 pose by rotation matrix"""
        pose = StateSE2(1, 2, np.pi / 4)
        rotation_matrix: npt.NDArray[np.float32] = np.array([[0, 1], [-1, 0]], dtype=np.float32)
        result = rotate(pose, rotation_matrix)
        self.assertAlmostEqual(result.x, -2)
        self.assertAlmostEqual(result.y, 1)
        self.assertAlmostEqual(result.heading, -np.pi / 4)

    def test_rotate_angle(self) -> None:
        """Tests rotation of SE2 pose by angle (in radian)"""
        pose = StateSE2(1, 2, np.pi / 4)
        angle = -np.pi / 2
        result = rotate_angle(pose, angle)
        self.assertAlmostEqual(result.x, -2)
        self.assertAlmostEqual(result.y, 1)
        self.assertAlmostEqual(result.heading, -np.pi / 4)

    def test_transform(self) -> None:
        """Tests transformation of SE2 pose"""
        pose = StateSE2(1, 2, 0)
        transform_matrix: npt.NDArray[np.float32] = np.array([[-3, -2, 5], [0, -1, 4], [0, 0, 1]], dtype=np.float32)
        result = transform(pose, transform_matrix)
        self.assertAlmostEqual(result.x, 2)
        self.assertAlmostEqual(result.y, 0)
        self.assertAlmostEqual(result.heading, np.pi, places=4)

    @patch('nuplan.common.geometry.transform.translate')
    def test_translate_longitudinally(self, mock_translate: Mock) -> None:
        """Tests longitudinal translation"""
        pose = StateSE2(1, 2, np.arctan(1 / 3))
        result = translate_longitudinally(pose, np.sqrt(10))
        np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([3, 1]))
        self.assertEqual(result, mock_translate.return_value)

    @patch('nuplan.common.geometry.transform.translate')
    def test_translate_laterally(self, mock_translate: Mock) -> None:
        """Tests lateral translation"""
        pose = StateSE2(1, 2, np.arctan(1 / 3))
        result = translate_laterally(pose, np.sqrt(10))
        np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([-1, 3]))
        self.assertEqual(result, mock_translate.return_value)

    @patch('nuplan.common.geometry.transform.translate')
    def test_translate_longitudinally_and_laterally(self, mock_translate: Mock) -> None:
        """Tests longitudinal and lateral translation"""
        pose = StateSE2(1, 2, np.arctan(1 / 3))
        result = translate_longitudinally_and_laterally(pose, np.sqrt(10), np.sqrt(10))
        np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([2, 4]))
        self.assertEqual(result, mock_translate.return_value)

@patch('nuplan.common.geometry.transform.translate')
def test_translate_longitudinally(self, mock_translate: Mock) -> None:
    """Tests longitudinal translation"""
    pose = StateSE2(1, 2, np.arctan(1 / 3))
    result = translate_longitudinally(pose, np.sqrt(10))
    np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([3, 1]))
    self.assertEqual(result, mock_translate.return_value)

@patch('nuplan.common.geometry.transform.translate')
def test_translate_laterally(self, mock_translate: Mock) -> None:
    """Tests lateral translation"""
    pose = StateSE2(1, 2, np.arctan(1 / 3))
    result = translate_laterally(pose, np.sqrt(10))
    np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([-1, 3]))
    self.assertEqual(result, mock_translate.return_value)

@patch('nuplan.common.geometry.transform.translate')
def test_translate_longitudinally_and_laterally(self, mock_translate: Mock) -> None:
    """Tests longitudinal and lateral translation"""
    pose = StateSE2(1, 2, np.arctan(1 / 3))
    result = translate_longitudinally_and_laterally(pose, np.sqrt(10), np.sqrt(10))
    np.testing.assert_array_almost_equal(mock_translate.call_args.args[1], np.array([2, 4]))
    self.assertEqual(result, mock_translate.return_value)

class TestCompute(unittest.TestCase):
    """Tests for compute functions"""

    @patch('nuplan.common.geometry.compute.get_pacifica_parameters', autospec=True)
    def test_signed_lateral_distance(self, mock_pacifica: Mock) -> None:
        """Tests signed lateral distance of ego to polygon"""
        mock_pacifica.return_value = Mock(half_width=1)
        result_0 = signed_lateral_distance(StateSE2(1, 1, -np.pi / 2), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
        result_1 = signed_lateral_distance(StateSE2(1, 1, np.pi / 2), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
        self.assertAlmostEqual(result_0, 1)
        self.assertAlmostEqual(result_1, -1)

    @patch('nuplan.common.geometry.compute.get_pacifica_parameters', autospec=True)
    def test_signed_longitudinal_distance(self, mock_pacifica: Mock) -> None:
        """Tests signed longitudinal distance of ego to polygon"""
        mock_pacifica.return_value = Mock(half_length=1)
        result_0 = signed_longitudinal_distance(StateSE2(1, 1, 0), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
        result_1 = signed_longitudinal_distance(StateSE2(1, 1, np.pi), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
        self.assertAlmostEqual(result_0, 1)
        self.assertAlmostEqual(result_1, -1)

    def test_compute_distance(self) -> None:
        """Tests distance between two points"""
        point_0 = StateSE2(8, 8, np.pi)
        point_1 = StateSE2(4, 5, 0)
        result_0 = compute_distance(point_0, point_1)
        result_1 = compute_distance(point_1, point_0)
        self.assertEqual(result_0, 5)
        self.assertEqual(result_1, 5)

    def test_compute_lateral_displacements(self) -> None:
        """Tests lateral distance between a list of points"""
        state_0 = StateSE2(0, 0, 0)
        state_1 = StateSE2(0, 1, 0)
        state_2 = StateSE2(0, 2, 0)
        state_3 = StateSE2(0, 3, 0)
        result = compute_lateral_displacements([state_0, state_1, state_2, state_3])
        for i in range(3):
            self.assertEqual(result[i], 1)

    def test_principal_value(self) -> None:
        """Tests principal angle calculation"""
        values: npt.NDArray[np.float64] = np.array([0, np.pi, 2 * np.pi, 3 * np.pi, -4 * np.pi, -3 * np.pi])
        expected_wrapped_0_to_pi: npt.NDArray[np.float64] = np.array([0, np.pi, 0, np.pi, 0, np.pi])
        expected_wrapped_neg_pi_to_pi: npt.NDArray[np.float64] = np.array([0, -np.pi, 0, -np.pi, 0, -np.pi])
        actual_wrapped_0_to_pi = principal_value(values, min_=0)
        actual_wrapped_neg_pi_to_pi = principal_value(values)
        np.testing.assert_allclose(expected_wrapped_0_to_pi, actual_wrapped_0_to_pi)
        np.testing.assert_allclose(expected_wrapped_neg_pi_to_pi, actual_wrapped_neg_pi_to_pi)

    def test_l2_euclidean_corners_distance(self) -> None:
        """Tests computation of distances between"""
        box_dimension = Dimension(4, 3, 1)
        box1 = OrientedBox(StateSE2(0, 0, 0), box_dimension.length, box_dimension.width, box_dimension.height)
        box2 = OrientedBox(StateSE2(2, 0, 0), box_dimension.length, box_dimension.width, box_dimension.height)
        box3 = OrientedBox(StateSE2(0, 2, 0), box_dimension.length, box_dimension.width, box_dimension.height)
        box4 = OrientedBox(StateSE2(3, 4, 0), box_dimension.length, box_dimension.width, box_dimension.height)
        box1_rot = OrientedBox(StateSE2(0, 0, np.pi), box_dimension.length, box_dimension.width, box_dimension.height)
        box5 = OrientedBox(StateSE2(1, 2, 3), box_dimension.length, box_dimension.width, box_dimension.height)
        self.assertEqual(0, l2_euclidean_corners_distance(box1, box1))
        self.assertEqual(4.0, l2_euclidean_corners_distance(box1, box2))
        self.assertEqual(l2_euclidean_corners_distance(box1, box2), l2_euclidean_corners_distance(box1, box3))
        self.assertEqual(10.0, l2_euclidean_corners_distance(box1, box4))
        self.assertEqual(10.0, l2_euclidean_corners_distance(box1, box1_rot))
        self.assertTrue(math.isclose(10.931588394648887, l2_euclidean_corners_distance(box1, box5)))

    def test_se2_box_distances(self) -> None:
        """Tests computation of distances between SE2 poses using OrientedBox"""
        box_dimension = Dimension(4, 3, 1)
        query = StateSE2(0, 0, 0)
        targets = [StateSE2(0, 0, 0), StateSE2(0, 0, np.pi), StateSE2(2, 0, 0)]
        self.assertEqual([0, 0, 4.0], se2_box_distances(query, targets, box_dimension))
        self.assertEqual([0, 10.0, 4.0], se2_box_distances(query, targets, box_dimension, consider_flipped=False))

@patch('nuplan.common.geometry.compute.get_pacifica_parameters', autospec=True)
def test_signed_lateral_distance(self, mock_pacifica: Mock) -> None:
    """Tests signed lateral distance of ego to polygon"""
    mock_pacifica.return_value = Mock(half_width=1)
    result_0 = signed_lateral_distance(StateSE2(1, 1, -np.pi / 2), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
    result_1 = signed_lateral_distance(StateSE2(1, 1, np.pi / 2), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
    self.assertAlmostEqual(result_0, 1)
    self.assertAlmostEqual(result_1, -1)

@patch('nuplan.common.geometry.compute.get_pacifica_parameters', autospec=True)
def test_signed_longitudinal_distance(self, mock_pacifica: Mock) -> None:
    """Tests signed longitudinal distance of ego to polygon"""
    mock_pacifica.return_value = Mock(half_length=1)
    result_0 = signed_longitudinal_distance(StateSE2(1, 1, 0), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
    result_1 = signed_longitudinal_distance(StateSE2(1, 1, np.pi), Polygon(((3, 2), (4, 3), (6, 1), (5, 0))))
    self.assertAlmostEqual(result_0, 1)
    self.assertAlmostEqual(result_1, -1)

class TestAngularInterpolator(unittest.TestCase):
    """Tests AngularInterpolator class"""

    @patch('nuplan.common.geometry.compute.interp1d', autospec=True)
    def setUp(self, mock_interp: Mock) -> None:
        """Sets up variables for testing"""
        interpolator = Mock(return_value='interpolated')
        mock_interp.return_value = interpolator
        self.states: npt.NDArray[np.float64] = np.array([1, 2, 3, 4, 5])
        self.angular_states = [[11], [22], [33], [44]]
        self.interpolator = AngularInterpolator(self.states, self.angular_states)

    @patch('nuplan.common.geometry.compute.np.unwrap', autospec=True)
    @patch('nuplan.common.geometry.compute.interp1d', autospec=True)
    def test_initialization(self, mock_interp: Mock, unwrap: Mock) -> None:
        """Tests interpolation for angular states."""
        interpolator = AngularInterpolator(self.states, self.angular_states)
        unwrap.assert_called_with(self.angular_states, axis=0)
        self.assertEqual(mock_interp.return_value, interpolator.interpolator)

    @patch('nuplan.common.geometry.compute.principal_value')
    def test_interpolate(self, principal_value: Mock) -> None:
        """Interpolates single state"""
        state = 1.5
        principal_value.return_value = 1.23
        result = self.interpolator.interpolate(state)
        self.interpolator.interpolator.assert_called_once_with(state)
        principal_value.assert_called_once_with('interpolated')
        self.assertEqual(1.23, result)

    def test_interpolate_real_value(self) -> None:
        """Interpolates multiple state"""
        states: npt.NDArray[np.float64] = np.array([1, 3])
        angular_states = [[3.0, -2.0], [-3.0, 2.0]]
        interpolator = AngularInterpolator(states, angular_states)
        np.testing.assert_allclose(np.array([-np.pi, -np.pi]), interpolator.interpolate(2))

@patch('nuplan.common.geometry.compute.interp1d', autospec=True)
def setUp(self, mock_interp: Mock) -> None:
    """Sets up variables for testing"""
    interpolator = Mock(return_value='interpolated')
    mock_interp.return_value = interpolator
    self.states: npt.NDArray[np.float64] = np.array([1, 2, 3, 4, 5])
    self.angular_states = [[11], [22], [33], [44]]
    self.interpolator = AngularInterpolator(self.states, self.angular_states)

@patch('nuplan.common.geometry.compute.np.unwrap', autospec=True)
@patch('nuplan.common.geometry.compute.interp1d', autospec=True)
def test_initialization(self, mock_interp: Mock, unwrap: Mock) -> None:
    """Tests interpolation for angular states."""
    interpolator = AngularInterpolator(self.states, self.angular_states)
    unwrap.assert_called_with(self.angular_states, axis=0)
    self.assertEqual(mock_interp.return_value, interpolator.interpolator)

@patch('nuplan.common.geometry.compute.principal_value')
def test_interpolate(self, principal_value: Mock) -> None:
    """Interpolates single state"""
    state = 1.5
    principal_value.return_value = 1.23
    result = self.interpolator.interpolate(state)
    self.interpolator.interpolator.assert_called_once_with(state)
    principal_value.assert_called_once_with('interpolated')
    self.assertEqual(1.23, result)

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

def __iter__(self) -> Iterator[Color]:
    """
        Return color components.
        """
    return iter(astuple(self))

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

@patch('nuplan.planning.utils.color.SceneColor.__mul__')
def test_rmul(self, mock_mul: Mock) -> None:
    """
        Tests reverse multiplication operation.
        """
    result = 0.75 * self.scene_color
    mock_mul.assert_called_once_with(0.75)
    self.assertEqual(result, mock_mul.return_value)

class TestColor(TestCase):
    """
    Test color.
    """

    def setUp(self) -> None:
        """
        Set up.
        """
        self.red = 0.1
        self.green = 0.2
        self.blue = 0.3
        self.alpha = 0.5
        self.color = Color(self.red, self.green, self.blue, self.alpha, ColorType.FLOAT)
        self.color_255 = Color(self.red, self.green, self.blue, self.alpha, ColorType.INT)

    def test_init(self) -> None:
        """
        Test initialisation.
        """
        self.assertEqual(self.color.red, self.red)
        self.assertEqual(self.color.green, self.green)
        self.assertEqual(self.color.blue, self.blue)
        self.assertEqual(self.color.alpha, self.alpha)
        self.assertEqual(self.color.serialize_to, ColorType.FLOAT)
        self.assertEqual(self.color_255.serialize_to, ColorType.INT)

    def test_post_init_invalid_type(self) -> None:
        """
        Tests that post init raises TypeError when passing any non-float types.
        """
        with self.assertRaises(TypeError):
            Color(1.0, 0.5, 0.0, '1')

    def test_post_init_invalid_range(self) -> None:
        """
        Tests that post init raises ValueError when passing values outside of range 0-255.
        """
        with self.assertRaises(ValueError):
            Color(1.0, 0.5, 0.0, 100.0)
        with self.assertRaises(ValueError):
            Color(1.0, 0.5, 0.0, -1.0)

    def test_iter(self) -> None:
        """
        Tests iteration of RGBA components.
        """
        result = [color for color in self.color]
        self.assertEqual(result[0], self.red)
        self.assertEqual(result[1], self.green)
        self.assertEqual(result[2], self.blue)
        self.assertEqual(result[3], self.alpha)

    def test_iter_255(self) -> None:
        """
        Tests iteration of RGBA components, with color type specified as int.
        """
        result = [color for color in self.color_255]
        self.assertEqual(result[0], int(self.red * 255))
        self.assertEqual(result[1], int(self.green * 255))
        self.assertEqual(result[2], int(self.blue * 255))
        self.assertEqual(result[3], int(self.alpha * 255))

    def test_to_list(self) -> None:
        """
        Tests to list method.
        """
        result = self.color.to_list()
        self.assertEqual(result, [self.red, self.green, self.blue, self.alpha])

    def test_mul(self) -> None:
        """
        Tests multiplication operation without clamping ie. results already in range (0-255).
        """
        result = self.color * 2
        self.assertEqual(result, Color(self.red * 2, self.green * 2, self.blue * 2, self.alpha * 2))

    def test_mul_clamp(self) -> None:
        """
        Tests clamping of values to range (0-255) after multiplication.
        """
        red = 0.5
        green = 0.7
        blue = 0.0
        alpha = 1.0
        color = Color(red, green, blue, alpha) * 2
        self.assertEqual(color.red, 1.0)
        self.assertEqual(color.green, 1.0)
        self.assertEqual(color.blue, 0.0)
        self.assertEqual(color.alpha, 1.0)

    def test_mul_255(self) -> None:
        """
        Tests multiplication operation with a color of integer color type preserves color type
        """
        result = self.color_255 * 2
        self.assertEqual(result, Color(self.red * 2, self.green * 2, self.blue * 2, self.alpha * 2, ColorType.INT))

    @patch('nuplan.planning.utils.color.Color.__mul__')
    def test_rmul(self, mock_mul: Mock) -> None:
        """
        Tests reverse multiplication operation.
        """
        result = 2 * self.color
        mock_mul.assert_called_once_with(2)
        self.assertEqual(result, mock_mul.return_value)

def setUp(self) -> None:
    """
        Set up.
        """
    self.red = 0.1
    self.green = 0.2
    self.blue = 0.3
    self.alpha = 0.5
    self.color = Color(self.red, self.green, self.blue, self.alpha, ColorType.FLOAT)
    self.color_255 = Color(self.red, self.green, self.blue, self.alpha, ColorType.INT)

def test_init(self) -> None:
    """
        Test initialisation.
        """
    self.assertEqual(self.color.red, self.red)
    self.assertEqual(self.color.green, self.green)
    self.assertEqual(self.color.blue, self.blue)
    self.assertEqual(self.color.alpha, self.alpha)
    self.assertEqual(self.color.serialize_to, ColorType.FLOAT)
    self.assertEqual(self.color_255.serialize_to, ColorType.INT)

def test_post_init_invalid_type(self) -> None:
    """
        Tests that post init raises TypeError when passing any non-float types.
        """
    with self.assertRaises(TypeError):
        Color(1.0, 0.5, 0.0, '1')

def test_post_init_invalid_range(self) -> None:
    """
        Tests that post init raises ValueError when passing values outside of range 0-255.
        """
    with self.assertRaises(ValueError):
        Color(1.0, 0.5, 0.0, 100.0)
    with self.assertRaises(ValueError):
        Color(1.0, 0.5, 0.0, -1.0)

def test_iter(self) -> None:
    """
        Tests iteration of RGBA components.
        """
    result = [color for color in self.color]
    self.assertEqual(result[0], self.red)
    self.assertEqual(result[1], self.green)
    self.assertEqual(result[2], self.blue)
    self.assertEqual(result[3], self.alpha)

def test_mul(self) -> None:
    """
        Tests multiplication operation without clamping ie. results already in range (0-255).
        """
    result = self.color * 2
    self.assertEqual(result, Color(self.red * 2, self.green * 2, self.blue * 2, self.alpha * 2))

def test_mul_clamp(self) -> None:
    """
        Tests clamping of values to range (0-255) after multiplication.
        """
    red = 0.5
    green = 0.7
    blue = 0.0
    alpha = 1.0
    color = Color(red, green, blue, alpha) * 2
    self.assertEqual(color.red, 1.0)
    self.assertEqual(color.green, 1.0)
    self.assertEqual(color.blue, 0.0)
    self.assertEqual(color.alpha, 1.0)

def test_mul_255(self) -> None:
    """
        Tests multiplication operation with a color of integer color type preserves color type
        """
    result = self.color_255 * 2
    self.assertEqual(result, Color(self.red * 2, self.green * 2, self.blue * 2, self.alpha * 2, ColorType.INT))

@patch('nuplan.planning.utils.color.Color.__mul__')
def test_rmul(self, mock_mul: Mock) -> None:
    """
        Tests reverse multiplication operation.
        """
    result = 2 * self.color
    mock_mul.assert_called_once_with(2)
    self.assertEqual(result, mock_mul.return_value)

class TestTrajectoryState(unittest.TestCase):
    """
    Test scene dataclass TrajectoryState
    """

    def setUp(self) -> None:
        """
        Set up
        """
        self.pose_x = 1.12
        self.pose_y = 2.11
        self.pose_heading = 0.29
        self.pose = StateSE2(self.pose_x, self.pose_y, self.pose_heading)
        self.speed = 1.23
        self.velocity_2d = [0.12, 0.54]
        self.lateral = [0.0, 0.0]
        self.acceleration = [0.32, 0.43]
        self.trajectory_state = TrajectoryState(pose=self.pose, speed=self.speed, velocity_2d=self.velocity_2d, lateral=self.lateral, acceleration=self.acceleration)

    def test_init(self) -> None:
        """
        Tests TrajectoryState initialization
        """
        self.assertEqual(self.trajectory_state.pose, self.pose)
        self.assertEqual(self.trajectory_state.speed, self.speed)
        self.assertEqual(self.trajectory_state.velocity_2d, self.velocity_2d)
        self.assertEqual(self.trajectory_state.lateral, self.lateral)
        self.assertEqual(self.trajectory_state.acceleration, self.acceleration)
        self.assertIsNone(self.trajectory_state.tire_steering_angle)

    def test_serialize(self) -> None:
        """
        Tests whether TrajectoryState is serializable
        """
        result = dict(self.trajectory_state)
        self.assertEqual(result, {'pose': [self.pose_x, self.pose_y, self.pose_heading], 'speed': self.speed, 'velocity_2d': self.velocity_2d, 'lateral': self.lateral, 'acceleration': self.acceleration})
        self.assertFalse('tire_steering_angle' in result.keys())

    def test_update(self) -> None:
        """
        Tests whether TrajectoryState is compatible with dict.update()
        """
        scene = {'example': 'unchanged', 'pose': 'old_pose', 'speed': 'old_speed'}
        scene.update(self.trajectory_state)
        self.assertEqual(scene, {'example': 'unchanged', 'pose': [self.pose_x, self.pose_y, self.pose_heading], 'speed': self.speed, 'velocity_2d': self.velocity_2d, 'lateral': self.lateral, 'acceleration': self.acceleration})

def test_init(self) -> None:
    """
        Tests TrajectoryState initialization
        """
    self.assertEqual(self.trajectory_state.pose, self.pose)
    self.assertEqual(self.trajectory_state.speed, self.speed)
    self.assertEqual(self.trajectory_state.velocity_2d, self.velocity_2d)
    self.assertEqual(self.trajectory_state.lateral, self.lateral)
    self.assertEqual(self.trajectory_state.acceleration, self.acceleration)
    self.assertIsNone(self.trajectory_state.tire_steering_angle)

class TestToScene(unittest.TestCase):
    """
    Test scene conversions in to_scene.py
    """

    def test_to_scene_trajectory_state_from_ego_state(self) -> None:
        """
        Tests conversion from ego state to trajectory state (scene class)
        """
        ego_state = Mock(spec=EgoState)
        ego_state.rear_axle = [1.12, 2.11, 0.29]
        ego_state.dynamic_car_state.speed = 1.23
        ego_state.dynamic_car_state.rear_axle_velocity_2d.x = 0.12
        ego_state.dynamic_car_state.rear_axle_velocity_2d.y = 0.54
        ego_state.dynamic_car_state.rear_axle_acceleration_2d.x = 0.32
        ego_state.dynamic_car_state.rear_axle_acceleration_2d.y = 0.43
        ego_state.tire_steering_angle = 0.21
        result = to_scene_trajectory_state_from_ego_state(ego_state)
        self.assertEqual(result.pose, [1.12, 2.11, 0.29])
        self.assertEqual(result.speed, 1.23)
        self.assertEqual(result.velocity_2d, [0.12, 0.54])
        self.assertEqual(result.lateral, [0.0, 0.0])
        self.assertEqual(result.acceleration, [0.32, 0.43])
        self.assertEqual(result.tire_steering_angle, 0.21)

    @patch('nuplan.planning.utils.serialization.to_scene.to_scene_trajectory_state_from_ego_state')
    def test_to_scene_trajectory_from_list_ego_state(self, mock_to_trajectory_state: Mock) -> None:
        """
        Tests conversion of list of ego states to trajectory structure (scene class)
        """
        mock_to_trajectory_state.side_effect = lambda state: 't_' + state
        ego_states = ['s1', 's2']
        color = Color(0.5, 0.2, 0.5, 1)
        result = to_scene_trajectory_from_list_ego_state(ego_states, color)
        self.assertEqual(result.color.to_list(), [0.5, 0.2, 0.5, 1])
        self.assertEqual(result.states, ['t_s1', 't_s2'])

    def test_to_scene_trajectory_state_from_waypoint(self) -> None:
        """
        Tests conversion from waypoint to trajectory state (scene class)
        """
        waypoint = Mock(spec=Waypoint)
        waypoint.center = [1.12, 2.11, 0.29]
        waypoint.velocity.magnitude.return_value = 1.23
        waypoint.velocity.x = 0.12
        waypoint.velocity.y = 0.54
        result = to_scene_trajectory_state_from_waypoint(waypoint)
        self.assertEqual(result.pose, [1.12, 2.11, 0.29])
        self.assertEqual(result.speed, 1.23)
        self.assertEqual(result.velocity_2d, [0.12, 0.54])
        self.assertEqual(result.lateral, [0.0, 0.0])
        self.assertEqual(result.acceleration, None)
        self.assertEqual(result.tire_steering_angle, None)

    @patch('nuplan.planning.utils.serialization.to_scene.to_scene_trajectory_state_from_waypoint')
    def test_to_scene_trajectory_from_list_waypoint(self, mock_to_trajectory_state: Mock) -> None:
        """
        Tests conversion of list of waypoints to trajectory structure (scene class)
        """
        mock_to_trajectory_state.side_effect = lambda state: 'w_' + state
        waypoints = ['s1', 's2']
        color = Color(0.5, 0.2, 0.5, 1)
        result = to_scene_trajectory_from_list_waypoint(waypoints, color)
        self.assertEqual(result.color.to_list(), [0.5, 0.2, 0.5, 1])
        self.assertEqual(result.states, ['w_s1', 'w_s2'])

def test_to_scene_trajectory_state_from_ego_state(self) -> None:
    """
        Tests conversion from ego state to trajectory state (scene class)
        """
    ego_state = Mock(spec=EgoState)
    ego_state.rear_axle = [1.12, 2.11, 0.29]
    ego_state.dynamic_car_state.speed = 1.23
    ego_state.dynamic_car_state.rear_axle_velocity_2d.x = 0.12
    ego_state.dynamic_car_state.rear_axle_velocity_2d.y = 0.54
    ego_state.dynamic_car_state.rear_axle_acceleration_2d.x = 0.32
    ego_state.dynamic_car_state.rear_axle_acceleration_2d.y = 0.43
    ego_state.tire_steering_angle = 0.21
    result = to_scene_trajectory_state_from_ego_state(ego_state)
    self.assertEqual(result.pose, [1.12, 2.11, 0.29])
    self.assertEqual(result.speed, 1.23)
    self.assertEqual(result.velocity_2d, [0.12, 0.54])
    self.assertEqual(result.lateral, [0.0, 0.0])
    self.assertEqual(result.acceleration, [0.32, 0.43])
    self.assertEqual(result.tire_steering_angle, 0.21)

@patch('nuplan.planning.utils.serialization.to_scene.to_scene_trajectory_state_from_ego_state')
def test_to_scene_trajectory_from_list_ego_state(self, mock_to_trajectory_state: Mock) -> None:
    """
        Tests conversion of list of ego states to trajectory structure (scene class)
        """
    mock_to_trajectory_state.side_effect = lambda state: 't_' + state
    ego_states = ['s1', 's2']
    color = Color(0.5, 0.2, 0.5, 1)
    result = to_scene_trajectory_from_list_ego_state(ego_states, color)
    self.assertEqual(result.color.to_list(), [0.5, 0.2, 0.5, 1])
    self.assertEqual(result.states, ['t_s1', 't_s2'])

def test_to_scene_trajectory_state_from_waypoint(self) -> None:
    """
        Tests conversion from waypoint to trajectory state (scene class)
        """
    waypoint = Mock(spec=Waypoint)
    waypoint.center = [1.12, 2.11, 0.29]
    waypoint.velocity.magnitude.return_value = 1.23
    waypoint.velocity.x = 0.12
    waypoint.velocity.y = 0.54
    result = to_scene_trajectory_state_from_waypoint(waypoint)
    self.assertEqual(result.pose, [1.12, 2.11, 0.29])
    self.assertEqual(result.speed, 1.23)
    self.assertEqual(result.velocity_2d, [0.12, 0.54])
    self.assertEqual(result.lateral, [0.0, 0.0])
    self.assertEqual(result.acceleration, None)
    self.assertEqual(result.tire_steering_angle, None)

@patch('nuplan.planning.utils.serialization.to_scene.to_scene_trajectory_state_from_waypoint')
def test_to_scene_trajectory_from_list_waypoint(self, mock_to_trajectory_state: Mock) -> None:
    """
        Tests conversion of list of waypoints to trajectory structure (scene class)
        """
    mock_to_trajectory_state.side_effect = lambda state: 'w_' + state
    waypoints = ['s1', 's2']
    color = Color(0.5, 0.2, 0.5, 1)
    result = to_scene_trajectory_from_list_waypoint(waypoints, color)
    self.assertEqual(result.color.to_list(), [0.5, 0.2, 0.5, 1])
    self.assertEqual(result.states, ['w_s1', 'w_s2'])

class TestTrajectory(unittest.TestCase):
    """
    Test scene dataclass Trajectory
    """

    def setUp(self) -> None:
        """
        Set up
        """
        self.color = Color(1, 0.5, 0, 1, ColorType.INT)
        self.states = [Mock(spec=TrajectoryState), Mock(spec=TrajectoryState)]
        self.trajectory_structure = Trajectory(color=self.color, states=self.states)

    def test_init(self) -> None:
        """
        Tests TrajectoryState initialization
        """
        self.assertEqual(self.trajectory_structure.color, self.color)
        self.assertEqual(self.trajectory_structure.states, self.states)

    @patch('nuplan.planning.utils.serialization.scene.type')
    def test_serialize(self, mock_type: Mock) -> None:
        """
        Tests whether TrajectoryState is serializable
        """
        self.states[0].__iter__ = Mock(return_value=iter([['state_0', 'value_0']]))
        self.states[1].__iter__ = Mock(return_value=iter([['state_1', 'value_1']]))
        mock_type.side_effect = lambda x: TrajectoryState if isinstance(x, TrajectoryState) else type(x)
        result = dict(self.trajectory_structure)
        self.assertEqual(result, {'color': self.color.to_list(), 'states': [{'state_0': 'value_0'}, {'state_1': 'value_1'}]})

    def test_update(self) -> None:
        """
        Tests whether Trajectory is compatible with dict.update()
        """
        scene = {'example': 'unchanged', 'color': 'old_color'}
        scene.update(self.trajectory_structure)
        self.assertEqual(scene, {'example': 'unchanged', 'color': self.color.to_list(), 'states': self.states})

def setUp(self) -> None:
    """
        Set up
        """
    self.color = Color(1, 0.5, 0, 1, ColorType.INT)
    self.states = [Mock(spec=TrajectoryState), Mock(spec=TrajectoryState)]
    self.trajectory_structure = Trajectory(color=self.color, states=self.states)

def test_init(self) -> None:
    """
        Tests TrajectoryState initialization
        """
    self.assertEqual(self.trajectory_structure.color, self.color)
    self.assertEqual(self.trajectory_structure.states, self.states)

@patch('nuplan.planning.utils.serialization.scene.type')
def test_serialize(self, mock_type: Mock) -> None:
    """
        Tests whether TrajectoryState is serializable
        """
    self.states[0].__iter__ = Mock(return_value=iter([['state_0', 'value_0']]))
    self.states[1].__iter__ = Mock(return_value=iter([['state_1', 'value_1']]))
    mock_type.side_effect = lambda x: TrajectoryState if isinstance(x, TrajectoryState) else type(x)
    result = dict(self.trajectory_structure)
    self.assertEqual(result, {'color': self.color.to_list(), 'states': [{'state_0': 'value_0'}, {'state_1': 'value_1'}]})

class TestSceneSimpleTrajectory(unittest.TestCase):
    """
    Tests the class SceneSimpleTrajectory
    """

    def setUp(self) -> None:
        """
        Sets up for the test cases
        """
        state1: Dict[str, Any] = {'timestamp': 1, 'pose': [1, 2, 3]}
        state2: Dict[str, Any] = {'timestamp': 2, 'pose': [3, 4, 5]}
        prediction_states: List[Dict[str, Any]] = [state1, state2]
        self.width = 3
        self.length = 6
        self.height = 2
        self.scene_simple_trajectory = SceneSimpleTrajectory(prediction_states, width=self.width, length=self.length, height=self.height)

    def test_init(self) -> None:
        """
        Tests the init of SceneSiimpleTrajectory
        """
        state1: Dict[str, Any] = {'timestamp': 1, 'pose': [1, 2, 3]}
        state2: Dict[str, Any] = {'timestamp': 2, 'pose': [3, 4, 5]}
        prediction_states: List[Dict[str, Any]] = [state1, state2]
        result = SceneSimpleTrajectory(prediction_states, width=self.width, length=self.length, height=self.height)
        self.assertEqual(result._start_time, 1)
        self.assertEqual(result._end_time, 2)

    def test_start_time(self) -> None:
        """
        Tests the start time property
        """
        scene_simple_trajectory = self.scene_simple_trajectory
        result = scene_simple_trajectory.start_time
        self.assertEqual(result, 1)

    def test_end_time(self) -> None:
        """
        Tests the start time property
        """
        scene_simple_trajectory = self.scene_simple_trajectory
        result = scene_simple_trajectory.end_time
        self.assertEqual(result, 2)

    def test_get_state_at_time(self) -> None:
        """
        Tests the get state at time method
        """
        scene_simple_trajectory = self.scene_simple_trajectory
        result = scene_simple_trajectory.get_state_at_time(TimePoint(int(1000000.0)))
        self.assertEqual(result.x, 1)
        self.assertEqual(result.y, 2)

    def test_get_sampled_trajectory(self) -> None:
        """
        Tests the get sampled method
        """
        scene_simple_trajectory = self.scene_simple_trajectory
        result = scene_simple_trajectory.get_sampled_trajectory()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].x, 1)
        self.assertEqual(result[1].x, 3)

def test_start_time(self) -> None:
    """
        Tests the start time property
        """
    scene_simple_trajectory = self.scene_simple_trajectory
    result = scene_simple_trajectory.start_time
    self.assertEqual(result, 1)

def test_end_time(self) -> None:
    """
        Tests the start time property
        """
    scene_simple_trajectory = self.scene_simple_trajectory
    result = scene_simple_trajectory.end_time
    self.assertEqual(result, 2)

def validate_planner_setup(setup: SimulationSetup, planner: AbstractPlanner) -> None:
    """
    Validate planner and simulation setup
    :param setup: Simulation setup
    :param planner: Planner to be used
    @raise ValueError in case simulation setup and planner are not a valid combination
    """
    type_observation_planner = planner.observation_type()
    type_observation = setup.observations.observation_type()
    if type_observation_planner != type_observation:
        raise ValueError(f'Error: The planner did not receive the right observations:{type_observation} != {type_observation_planner} planner.Planner {type(planner)}, Observation:{type(setup.observations)}')

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

def test_observation_type(self) -> None:
    """Test observation_type"""
    self.assertEqual(self.predictor.observation_type(), DetectionsTracks)

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

class TestLogPlaybackController(TestCase):
    """Tests implementation of LogPlaybackController"""

    def setUp(self) -> None:
        """
        Setup mocks for the tests
        """
        self.scenario = MagicMock(spec=AbstractScenario)
        self.iteration = Mock(spec=SimulationIteration)
        self.next_iteration = Mock(spec=SimulationIteration)
        self.ego_state = Mock(spec=EgoState)
        self.trajectory = Mock(spec=AbstractTrajectory)
        self.scenario.get_ego_state_at_iteration.return_value = SCENARIO_EGO_STATE
        self.next_iteration_idx = PropertyMock(return_value=NEXT_ITERATION_IDX)
        type(self.next_iteration).index = self.next_iteration_idx
        self.lpc = LogPlaybackController(self.scenario)

    @patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock)
    @patch.object(LogPlaybackController, 'scenario', create=True, new_callable=PropertyMock)
    def test_constructor(self, scenario: MagicMock, current_iteration: MagicMock) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        LogPlaybackController(self.scenario)
        scenario.assert_called_once_with(self.scenario)
        current_iteration.assert_called_once_with(0)

    def test_get_state(self) -> None:
        """
        Tests if the scenario.get_ego_state_at_iteration is called with the current_iteration.
        """
        with patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock) as current_iteration:
            current_iteration.return_value = CURRENT_ITERATION
            result = self.lpc.get_state()
            self.assertEqual(result, SCENARIO_EGO_STATE)
            current_iteration.assert_called_once()
            self.scenario.get_ego_state_at_iteration.assert_called_once_with(CURRENT_ITERATION)

    def test_update_state(self) -> None:
        """
        Tests if the current_iteration is set to the next iteration.index value.
        """
        with patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock) as current_iteration:
            self.lpc.update_state(self.iteration, self.next_iteration, self.ego_state, self.trajectory)
            current_iteration.assert_called_once_with(NEXT_ITERATION_IDX)
            self.next_iteration_idx.assert_called_once()

def setUp(self) -> None:
    """
        Setup mocks for the tests
        """
    self.scenario = MagicMock(spec=AbstractScenario)
    self.iteration = Mock(spec=SimulationIteration)
    self.next_iteration = Mock(spec=SimulationIteration)
    self.ego_state = Mock(spec=EgoState)
    self.trajectory = Mock(spec=AbstractTrajectory)
    self.scenario.get_ego_state_at_iteration.return_value = SCENARIO_EGO_STATE
    self.next_iteration_idx = PropertyMock(return_value=NEXT_ITERATION_IDX)
    type(self.next_iteration).index = self.next_iteration_idx
    self.lpc = LogPlaybackController(self.scenario)

@patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock)
@patch.object(LogPlaybackController, 'scenario', create=True, new_callable=PropertyMock)
def test_constructor(self, scenario: MagicMock, current_iteration: MagicMock) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    LogPlaybackController(self.scenario)
    scenario.assert_called_once_with(self.scenario)
    current_iteration.assert_called_once_with(0)

def test_get_state(self) -> None:
    """
        Tests if the scenario.get_ego_state_at_iteration is called with the current_iteration.
        """
    with patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock) as current_iteration:
        current_iteration.return_value = CURRENT_ITERATION
        result = self.lpc.get_state()
        self.assertEqual(result, SCENARIO_EGO_STATE)
        current_iteration.assert_called_once()
        self.scenario.get_ego_state_at_iteration.assert_called_once_with(CURRENT_ITERATION)

def test_update_state(self) -> None:
    """
        Tests if the current_iteration is set to the next iteration.index value.
        """
    with patch.object(LogPlaybackController, 'current_iteration', create=True, new_callable=PropertyMock) as current_iteration:
        self.lpc.update_state(self.iteration, self.next_iteration, self.ego_state, self.trajectory)
        current_iteration.assert_called_once_with(NEXT_ITERATION_IDX)
        self.next_iteration_idx.assert_called_once()

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

class AbstractIDMPlanner(AbstractPlanner, ABC):
    """
    An interface for IDM based planners. Inherit from this class to use IDM policy to control the longitudinal
    behaviour of the ego.
    """

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
        self._policy = IDMPolicy(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max)
        self._planned_trajectory_samples = planned_trajectory_samples
        self._planned_trajectory_sample_interval = planned_trajectory_sample_interval
        self._planned_horizon = planned_trajectory_samples * planned_trajectory_sample_interval
        self._occupancy_map_radius = occupancy_map_radius
        self._max_path_length = self._policy.target_velocity * self._planned_horizon
        self._ego_token = 'ego_token'
        self._red_light_token = 'red_light'
        self._route_roadblocks: List[RoadBlockGraphEdgeMapObject] = []
        self._candidate_lane_edge_ids: Optional[List[str]] = None
        self._map_api: Optional[AbstractMap] = None
        self._ego_path: Optional[AbstractPath] = None
        self._ego_path_linestring: Optional[LineString] = None

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def _initialize_route_plan(self, route_roadblock_ids: List[str]) -> None:
        """
        Initializes the route plan with roadblocks.
        :param route_roadblock_ids: A list of roadblock ids that make up the ego's route
        """
        assert self._map_api, '_map_api has not yet been initialized. Please call the initialize() function first!'
        self._route_roadblocks = []
        for id_ in route_roadblock_ids:
            block = self._map_api.get_map_object(id_, SemanticMapLayer.ROADBLOCK)
            block = block or self._map_api.get_map_object(id_, SemanticMapLayer.ROADBLOCK_CONNECTOR)
            self._route_roadblocks.append(block)
        self._candidate_lane_edge_ids = [edge.id for block in self._route_roadblocks if block for edge in block.interior_edges]
        assert self._route_roadblocks, 'Cannot create route plan. No roadblocks were extracted from the given route_roadblock_ids!'

    def _get_expanded_ego_path(self, ego_state: EgoState, ego_idm_state: IDMAgentState) -> Polygon:
        """
        Returns the ego's expanded path as a Polygon.
        :return: A polygon representing the ego's path.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        ego_footprint = ego_state.car_footprint
        path_to_go = trim_path(self._ego_path, max(self._ego_path.get_start_progress(), min(ego_idm_state.progress, self._ego_path.get_end_progress())), max(self._ego_path.get_start_progress(), min(ego_idm_state.progress + abs(self._policy.target_velocity) * self._planned_horizon, self._ego_path.get_end_progress())))
        expanded_path = path_to_linestring(path_to_go).buffer(ego_footprint.width / 2, cap_style=CAP_STYLE.square)
        return unary_union([expanded_path, ego_state.car_footprint.geometry])

    @staticmethod
    def _get_leading_idm_agent(ego_state: EgoState, agent: SceneObject, relative_distance: float) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state that represents another static and dynamic agent.
        :param agent: A scene object.
        :param relative_distance: [m] The relative distance from the scene object to the ego.
        :return: A IDM lead agents state
        """
        if isinstance(agent, Agent):
            longitudinal_velocity = agent.velocity.magnitude()
            relative_heading = principal_value(agent.center.heading - ego_state.center.heading)
            projected_velocity = transform(StateSE2(longitudinal_velocity, 0, 0), StateSE2(0, 0, relative_heading).as_matrix()).x
        else:
            projected_velocity = 0.0
        return IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=0.0)

    def _get_free_road_leading_idm_state(self, ego_state: EgoState, ego_idm_state: IDMAgentState) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state when there is no leading agent.
        :return: A IDM lead agents state.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        projected_velocity = 0.0
        relative_distance = self._ego_path.get_end_progress() - ego_idm_state.progress
        length_rear = ego_state.car_footprint.length / 2
        return IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=length_rear)

    @staticmethod
    def _get_red_light_leading_idm_state(relative_distance: float) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state that represents a red light intersection.
        :param relative_distance: [m] The relative distance from the intersection to the ego.
        :return: A IDM lead agents state.
        """
        return IDMLeadAgentState(progress=relative_distance, velocity=0, length_rear=0)

    def _get_leading_object(self, ego_idm_state: IDMAgentState, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> IDMLeadAgentState:
        """
        Get the most suitable leading object based on the occupancy map.
        :param ego_idm_state: The ego's IDM state at current iteration.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        """
        intersecting_agents = occupancy_map.intersects(self._get_expanded_ego_path(ego_state, ego_idm_state))
        if intersecting_agents.size > 0:
            intersecting_agents.insert(self._ego_token, ego_state.car_footprint.geometry)
            nearest_id, nearest_agent_polygon, relative_distance = intersecting_agents.get_nearest_entry_to(self._ego_token)
            if self._red_light_token in nearest_id:
                return self._get_red_light_leading_idm_state(relative_distance)
            return self._get_leading_idm_agent(ego_state, unique_observations[nearest_id], relative_distance)
        else:
            return self._get_free_road_leading_idm_state(ego_state, ego_idm_state)

    def _construct_occupancy_map(self, ego_state: EgoState, observation: Observation) -> Tuple[OccupancyMap, UniqueObjects]:
        """
        Constructs an OccupancyMap from Observations.
        :param ego_state: Current EgoState
        :param observation: Observations of other agents and static objects in the scene.
        :return:
            - OccupancyMap.
            - A mapping between the object token and the object itself.
        """
        if isinstance(observation, DetectionsTracks):
            unique_observations = {detection.track_token: detection for detection in observation.tracked_objects.tracked_objects if np.linalg.norm(ego_state.center.array - detection.center.array) < self._occupancy_map_radius}
            return (STRTreeOccupancyMapFactory.get_from_boxes(list(unique_observations.values())), unique_observations)
        else:
            raise ValueError(f'IDM planner only supports DetectionsTracks. Got {observation.detection_type()}')

    def _propagate(self, ego: IDMAgentState, lead_agent: IDMLeadAgentState, tspan: float) -> None:
        """
        Propagate agent forward according to the IDM policy.
        :param ego: The ego's IDM state.
        :param lead_agent: The agent leading this agent.
        :param tspan: [s] The interval of time to propagate for.
        """
        solution = self._policy.solve_forward_euler_idm_policy(IDMAgentState(0, ego.velocity), lead_agent, tspan)
        ego.progress += solution.progress
        ego.velocity = max(solution.velocity, 0)

    def _get_planned_trajectory(self, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> InterpolatedTrajectory:
        """
        Plan a trajectory w.r.t. the occupancy map.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        :return: A trajectory representing the predicted ego's position in future.
        """
        assert self._ego_path_linestring, '_ego_path_linestring has not yet been initialized. Please call the initialize() function first!'
        ego_progress = self._ego_path_linestring.project(Point(*ego_state.center.point.array))
        ego_idm_state = IDMAgentState(progress=ego_progress, velocity=ego_state.dynamic_car_state.center_velocity_2d.x)
        vehicle_parameters = ego_state.car_footprint.vehicle_parameters
        current_time_point = ego_state.time_point
        projected_ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
        planned_trajectory: List[EgoState] = [projected_ego_state]
        for _ in range(self._planned_trajectory_samples):
            leading_agent = self._get_leading_object(ego_idm_state, ego_state, occupancy_map, unique_observations)
            self._propagate(ego_idm_state, leading_agent, self._planned_trajectory_sample_interval)
            current_time_point += TimePoint(int(self._planned_trajectory_sample_interval * 1000000.0))
            ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
            planned_trajectory.append(ego_state)
        return InterpolatedTrajectory(planned_trajectory)

    def _idm_state_to_ego_state(self, idm_state: IDMAgentState, time_point: TimePoint, vehicle_parameters: VehicleParameters) -> EgoState:
        """
        Convert IDMAgentState to EgoState
        :param idm_state: The IDMAgentState to be converted.
        :param time_point: The TimePoint corresponding to the state.
        :param vehicle_parameters: VehicleParameters of the ego.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        new_ego_center = self._ego_path.get_state_at_progress(max(self._ego_path.get_start_progress(), min(idm_state.progress, self._ego_path.get_end_progress())))
        return EgoState.build_from_center(center=StateSE2(new_ego_center.x, new_ego_center.y, new_ego_center.heading), center_velocity_2d=StateVector2D(idm_state.velocity, 0), center_acceleration_2d=StateVector2D(0, 0), tire_steering_angle=0.0, time_point=time_point, vehicle_parameters=vehicle_parameters)

    def _annotate_occupancy_map(self, traffic_light_data: List[TrafficLightStatusData], occupancy_map: OccupancyMap) -> None:
        """
        Add red light lane connectors on the route plan to the occupancy map. Note: the function works inline, hence,
        the occupancy map will be modified in this function.
        :param traffic_light_data: A list of all available traffic status data.
        :param occupancy_map: The occupancy map to be annotated.
        """
        assert self._map_api, '_map_api has not yet been initialized. Please call the initialize() function first!'
        assert self._candidate_lane_edge_ids is not None, '_candidate_lane_edge_ids has not yet been initialized. Please call the initialize() function first!'
        for data in traffic_light_data:
            if data.status == TrafficLightStatusType.RED and str(data.lane_connector_id) in self._candidate_lane_edge_ids:
                id_ = str(data.lane_connector_id)
                lane_conn = self._map_api.get_map_object(id_, SemanticMapLayer.LANE_CONNECTOR)
                occupancy_map.insert(f'{self._red_light_token}_{id_}', lane_conn.polygon)

def _get_leading_object(self, ego_idm_state: IDMAgentState, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> IDMLeadAgentState:
    """
        Get the most suitable leading object based on the occupancy map.
        :param ego_idm_state: The ego's IDM state at current iteration.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        """
    intersecting_agents = occupancy_map.intersects(self._get_expanded_ego_path(ego_state, ego_idm_state))
    if intersecting_agents.size > 0:
        intersecting_agents.insert(self._ego_token, ego_state.car_footprint.geometry)
        nearest_id, nearest_agent_polygon, relative_distance = intersecting_agents.get_nearest_entry_to(self._ego_token)
        if self._red_light_token in nearest_id:
            return self._get_red_light_leading_idm_state(relative_distance)
        return self._get_leading_idm_agent(ego_state, unique_observations[nearest_id], relative_distance)
    else:
        return self._get_free_road_leading_idm_state(ego_state, ego_idm_state)

def _propagate(self, ego: IDMAgentState, lead_agent: IDMLeadAgentState, tspan: float) -> None:
    """
        Propagate agent forward according to the IDM policy.
        :param ego: The ego's IDM state.
        :param lead_agent: The agent leading this agent.
        :param tspan: [s] The interval of time to propagate for.
        """
    solution = self._policy.solve_forward_euler_idm_policy(IDMAgentState(0, ego.velocity), lead_agent, tspan)
    ego.progress += solution.progress
    ego.velocity = max(solution.velocity, 0)

def _get_planned_trajectory(self, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> InterpolatedTrajectory:
    """
        Plan a trajectory w.r.t. the occupancy map.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        :return: A trajectory representing the predicted ego's position in future.
        """
    assert self._ego_path_linestring, '_ego_path_linestring has not yet been initialized. Please call the initialize() function first!'
    ego_progress = self._ego_path_linestring.project(Point(*ego_state.center.point.array))
    ego_idm_state = IDMAgentState(progress=ego_progress, velocity=ego_state.dynamic_car_state.center_velocity_2d.x)
    vehicle_parameters = ego_state.car_footprint.vehicle_parameters
    current_time_point = ego_state.time_point
    projected_ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
    planned_trajectory: List[EgoState] = [projected_ego_state]
    for _ in range(self._planned_trajectory_samples):
        leading_agent = self._get_leading_object(ego_idm_state, ego_state, occupancy_map, unique_observations)
        self._propagate(ego_idm_state, leading_agent, self._planned_trajectory_sample_interval)
        current_time_point += TimePoint(int(self._planned_trajectory_sample_interval * 1000000.0))
        ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
        planned_trajectory.append(ego_state)
    return InterpolatedTrajectory(planned_trajectory)

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

def __init__(self, start_edge: LaneGraphEdgeMapObject, candidate_lane_edge_ids: List[str]):
    """
        Constructor for the BreadthFirstSearch class.
        :param start_edge: The starting edge for the search
        :param candidate_lane_edge_ids: The candidates lane ids that can be included in the search.
        """
    self._queue = deque([start_edge, None])
    self._parent: Dict[str, Optional[LaneGraphEdgeMapObject]] = dict()
    self._candidate_lane_edge_ids = candidate_lane_edge_ids

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

def test_observation_type(self) -> None:
    """Test observation_type"""
    self.assertEqual(self.planner.observation_type(), DetectionsTracks)

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

def test_observation_type(self) -> None:
    """Test observation_type"""
    self.assertEqual(self.planner.observation_type(), DetectionsTracks)

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

class TestRemotePlanner(TestCase):
    """Tests RemotePlanner class"""

    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
    def setUp(self, mock_factory: Mock) -> None:
        """Sets variables for testing"""
        self.planner = RemotePlanner()
        self.planner_with_container = RemotePlanner(submission_container_manager=Mock(), submission_image='foo', container_name='bar')

    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
    def test_initialization(self, mock_factory: Mock) -> None:
        """Tests that the class is initialized as intended."""
        mock_planner = RemotePlanner()
        self.assertEqual(None, mock_planner.submission_container_manager)
        self.assertEqual(50051, mock_planner.port)
        mock_planner = RemotePlanner(submission_container_manager=mock_factory, submission_image='foo', container_name='bar')
        self.assertEqual(mock_factory, mock_planner.submission_container_manager)
        self.assertEqual('foo', mock_planner.submission_image)
        self.assertEqual('bar', mock_planner.container_name)
        self.assertEqual(None, mock_planner.port)
        with self.assertRaises(AssertionError):
            _ = RemotePlanner(submission_container_manager=Mock())

    def test_name(self) -> None:
        """Tests planner name is set correctly"""
        self.assertEqual('RemotePlanner', self.planner.name())

    def test_observation_type(self) -> None:
        """Tests observation type is set correctly"""
        self.assertEqual(DetectionsTracks, self.planner.observation_type())

    def test_initialization_message_creation(self) -> None:
        """Tests that the message for the initialization request is built correctly."""
        mock_state_1 = Mock(x=0, y=1, heading=0.2)
        mock_map_api = Mock(map_name='test')
        mock_initialization = Mock(mission_goal=mock_state_1, map_api=mock_map_api, route_roadblock_ids=['a', 'b', 'c'])
        with self.assertRaises(AttributeError):
            self.planner._planner_initializations_to_message(Mock(mission_goal=None, map_api=mock_map_api))
        initialization_message = self.planner._planner_initializations_to_message(mock_initialization)
        self.assertAlmostEqual(mock_state_1.x, initialization_message.mission_goal.x)
        self.assertAlmostEqual(mock_state_1.y, initialization_message.mission_goal.y)
        self.assertAlmostEqual(mock_state_1.heading, initialization_message.mission_goal.heading)
        self.assertEqual(mock_map_api.map_name, initialization_message.map_name)
        self.assertEqual(initialization_message.route_roadblock_ids, ['a', 'b', 'c'])

    @patch.object(RemotePlanner, '_planner_initializations_to_message', return_value=123, autospec=True)
    @patch('grpc.insecure_channel')
    @patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', autospec=True)
    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', Mock(spec_set=SubmissionContainerManager))
    @patch('nuplan.planning.simulation.planner.remote_planner.find_free_port_number')
    def test_initialize(self, mock_find_port: Mock, mock_stub_function: Mock, mock_channel: Mock, initialization_to_message: Mock) -> None:
        """Tests that the initialization request is called correctly."""
        mock_initialization = Mock()
        mock_stub = Mock()
        mock_stub_function.return_value = mock_stub
        self.planner.initialize(mock_initialization)
        mock_channel.assert_called()
        initialization_to_message.assert_called_with(mock_initialization)
        self.planner._stub.InitializePlanner.assert_called_with(123)
        self.planner_with_container.initialize(mock_initialization)
        self.planner_with_container.submission_container_manager.get_submission_container.assert_called_with(self.planner_with_container.submission_image, self.planner_with_container.container_name, mock_find_port())
        self.planner_with_container.submission_container_manager.get_submission_container().start.assert_called()

    @patch.object(RemotePlanner, '_compute_trajectory')
    @patch('grpc.insecure_channel', Mock())
    @patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', Mock(spec_set=DetectionTracksChallengeStub))
    def test_compute_trajectory_interface(self, mock_compute_trajectory: Mock) -> None:
        """Tests that the interface for the trajectory computation request is called correctly."""
        mock_compute_trajectory.return_value = 'trajectories'
        mock_input = [Mock()]
        trajectories = self.planner.compute_trajectory(mock_input)
        mock_compute_trajectory.assert_called_with(self.planner._stub, current_input=mock_input)
        self.assertEqual('trajectories', trajectories)

    @patch('nuplan.planning.simulation.planner.remote_planner.interp_traj_from_proto_traj', Mock)
    @patch('nuplan.planning.simulation.planner.remote_planner.proto_tl_status_data_from_tl_status_data')
    @patch('nuplan.submission.challenge_pb2.PlannerInput')
    @patch('nuplan.submission.challenge_pb2.SimulationIteration')
    @patch('nuplan.submission.challenge_pb2.SimulationHistoryBuffer')
    def test_compute_trajectory(self, history_buffer: Mock, simulation_iteration: Mock, planner_input: Mock, mock_proto_tl_status_data: Mock) -> None:
        """Tests deserialization and serialization of the input/output for the trajectory computation interface."""
        with patch.object(self.planner, '_get_history_update', MagicMock()) as get_history_update:
            get_history_update.return_value = [['states'], ['observations'], ['intervals']]
            mock_stub = MagicMock()
            mock_tl_data = Mock()
            mock_input = Mock(iteration=Mock(time_us=1, index=0), history=Mock(ego_states='fake_input'), traffic_light_data=[mock_tl_data])
            mock_input.history.ego_states = ['fake_input']
            planner_input.return_value = 'planner input'
            simulation_iteration.return_value = 'iter_1'
            history_buffer.return_value = 'hb_1'
            self.planner._compute_trajectory(mock_stub, mock_input)
            get_history_update.assert_called_once_with(mock_input)
            mock_proto_tl_status_data.assert_called_once_with(mock_tl_data)
            simulation_iteration.assert_has_calls([call(time_us=1, index=0)])
            planner_input.assert_has_calls([call(simulation_iteration='iter_1', simulation_history_buffer='hb_1', traffic_light_data=[mock_proto_tl_status_data.return_value])])
            mock_stub.ComputeTrajectory.assert_called_once_with(planner_input.return_value, timeout=1)

    @patch('pickle.dumps')
    def test_get_history_update(self, mock_dumps: Mock) -> None:
        """Tests that the history update is built correctly."""
        planner_input = Mock()
        planner_input.history.ego_states = [1, 2]
        planner_input.history.observations = [4, 5]
        planner_input.history.current_state = (6, 7)
        serialized_states, serialized_observations, sample_interval = self.planner._get_history_update(planner_input)
        calls = [call(1), call(2), call(4), call(5)]
        mock_dumps.assert_has_calls(calls)
        self.planner.serialized_state = serialized_states
        self.planner.serialized_observation = serialized_observations
        self.planner.sample_intervals = sample_interval
        _, _, _ = self.planner._get_history_update(planner_input)
        calls = calls + [call(6), call(7)]
        mock_dumps.assert_has_calls(calls)

@patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
def setUp(self, mock_factory: Mock) -> None:
    """Sets variables for testing"""
    self.planner = RemotePlanner()
    self.planner_with_container = RemotePlanner(submission_container_manager=Mock(), submission_image='foo', container_name='bar')

@patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
def test_initialization(self, mock_factory: Mock) -> None:
    """Tests that the class is initialized as intended."""
    mock_planner = RemotePlanner()
    self.assertEqual(None, mock_planner.submission_container_manager)
    self.assertEqual(50051, mock_planner.port)
    mock_planner = RemotePlanner(submission_container_manager=mock_factory, submission_image='foo', container_name='bar')
    self.assertEqual(mock_factory, mock_planner.submission_container_manager)
    self.assertEqual('foo', mock_planner.submission_image)
    self.assertEqual('bar', mock_planner.container_name)
    self.assertEqual(None, mock_planner.port)
    with self.assertRaises(AssertionError):
        _ = RemotePlanner(submission_container_manager=Mock())

def test_observation_type(self) -> None:
    """Tests observation type is set correctly"""
    self.assertEqual(DetectionsTracks, self.planner.observation_type())

def test_initialization_message_creation(self) -> None:
    """Tests that the message for the initialization request is built correctly."""
    mock_state_1 = Mock(x=0, y=1, heading=0.2)
    mock_map_api = Mock(map_name='test')
    mock_initialization = Mock(mission_goal=mock_state_1, map_api=mock_map_api, route_roadblock_ids=['a', 'b', 'c'])
    with self.assertRaises(AttributeError):
        self.planner._planner_initializations_to_message(Mock(mission_goal=None, map_api=mock_map_api))
    initialization_message = self.planner._planner_initializations_to_message(mock_initialization)
    self.assertAlmostEqual(mock_state_1.x, initialization_message.mission_goal.x)
    self.assertAlmostEqual(mock_state_1.y, initialization_message.mission_goal.y)
    self.assertAlmostEqual(mock_state_1.heading, initialization_message.mission_goal.heading)
    self.assertEqual(mock_map_api.map_name, initialization_message.map_name)
    self.assertEqual(initialization_message.route_roadblock_ids, ['a', 'b', 'c'])

@patch.object(RemotePlanner, '_planner_initializations_to_message', return_value=123, autospec=True)
@patch('grpc.insecure_channel')
@patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', autospec=True)
@patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', Mock(spec_set=SubmissionContainerManager))
@patch('nuplan.planning.simulation.planner.remote_planner.find_free_port_number')
def test_initialize(self, mock_find_port: Mock, mock_stub_function: Mock, mock_channel: Mock, initialization_to_message: Mock) -> None:
    """Tests that the initialization request is called correctly."""
    mock_initialization = Mock()
    mock_stub = Mock()
    mock_stub_function.return_value = mock_stub
    self.planner.initialize(mock_initialization)
    mock_channel.assert_called()
    initialization_to_message.assert_called_with(mock_initialization)
    self.planner._stub.InitializePlanner.assert_called_with(123)
    self.planner_with_container.initialize(mock_initialization)
    self.planner_with_container.submission_container_manager.get_submission_container.assert_called_with(self.planner_with_container.submission_image, self.planner_with_container.container_name, mock_find_port())
    self.planner_with_container.submission_container_manager.get_submission_container().start.assert_called()

@patch.object(RemotePlanner, '_compute_trajectory')
@patch('grpc.insecure_channel', Mock())
@patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', Mock(spec_set=DetectionTracksChallengeStub))
def test_compute_trajectory_interface(self, mock_compute_trajectory: Mock) -> None:
    """Tests that the interface for the trajectory computation request is called correctly."""
    mock_compute_trajectory.return_value = 'trajectories'
    mock_input = [Mock()]
    trajectories = self.planner.compute_trajectory(mock_input)
    mock_compute_trajectory.assert_called_with(self.planner._stub, current_input=mock_input)
    self.assertEqual('trajectories', trajectories)

@patch('nuplan.planning.simulation.planner.remote_planner.interp_traj_from_proto_traj', Mock)
@patch('nuplan.planning.simulation.planner.remote_planner.proto_tl_status_data_from_tl_status_data')
@patch('nuplan.submission.challenge_pb2.PlannerInput')
@patch('nuplan.submission.challenge_pb2.SimulationIteration')
@patch('nuplan.submission.challenge_pb2.SimulationHistoryBuffer')
def test_compute_trajectory(self, history_buffer: Mock, simulation_iteration: Mock, planner_input: Mock, mock_proto_tl_status_data: Mock) -> None:
    """Tests deserialization and serialization of the input/output for the trajectory computation interface."""
    with patch.object(self.planner, '_get_history_update', MagicMock()) as get_history_update:
        get_history_update.return_value = [['states'], ['observations'], ['intervals']]
        mock_stub = MagicMock()
        mock_tl_data = Mock()
        mock_input = Mock(iteration=Mock(time_us=1, index=0), history=Mock(ego_states='fake_input'), traffic_light_data=[mock_tl_data])
        mock_input.history.ego_states = ['fake_input']
        planner_input.return_value = 'planner input'
        simulation_iteration.return_value = 'iter_1'
        history_buffer.return_value = 'hb_1'
        self.planner._compute_trajectory(mock_stub, mock_input)
        get_history_update.assert_called_once_with(mock_input)
        mock_proto_tl_status_data.assert_called_once_with(mock_tl_data)
        simulation_iteration.assert_has_calls([call(time_us=1, index=0)])
        planner_input.assert_has_calls([call(simulation_iteration='iter_1', simulation_history_buffer='hb_1', traffic_light_data=[mock_proto_tl_status_data.return_value])])
        mock_stub.ComputeTrajectory.assert_called_once_with(planner_input.return_value, timeout=1)

@patch('pickle.dumps')
def test_get_history_update(self, mock_dumps: Mock) -> None:
    """Tests that the history update is built correctly."""
    planner_input = Mock()
    planner_input.history.ego_states = [1, 2]
    planner_input.history.observations = [4, 5]
    planner_input.history.current_state = (6, 7)
    serialized_states, serialized_observations, sample_interval = self.planner._get_history_update(planner_input)
    calls = [call(1), call(2), call(4), call(5)]
    mock_dumps.assert_has_calls(calls)
    self.planner.serialized_state = serialized_states
    self.planner.serialized_observation = serialized_observations
    self.planner.sample_intervals = sample_interval
    _, _, _ = self.planner._get_history_update(planner_input)
    calls = calls + [call(6), call(7)]
    mock_dumps.assert_has_calls(calls)

class MultiMainCallback(AbstractMainCallback):
    """
    Combines a set of of AbstractMainCallbacks.
    """

    def __init__(self, main_callbacks: List[AbstractMainCallback]):
        """
        Callback to handle a list of main callbacks.
        :param main_callbacks: A list of main callbacks.
        """
        self._main_callbacks = main_callbacks

    def __len__(self) -> int:
        """Support len() as counting the number of callbacks."""
        return len(self._main_callbacks)

    def on_run_simulation_start(self) -> None:
        """Callback after the simulation function starts."""
        for main_callback in self._main_callbacks:
            main_callback.on_run_simulation_start()

    def on_run_simulation_end(self) -> None:
        """Callback before the simulation function ends."""
        for main_callback in self._main_callbacks:
            main_callback.on_run_simulation_end()

def on_run_simulation_end(self) -> None:
    """Callback before the simulation function ends."""
    for main_callback in self._main_callbacks:
        main_callback.on_run_simulation_end()

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

class TestMetricFileCallback(TestCase):
    """Tests metrics files generation at the end fo the simulation."""

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        self.mock_metric_file_callback = Mock(spec=MetricFileCallback)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp_dir.name)
        self.path.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up tmp dir."""
        self.tmp_dir.cleanup()

    def test_metric_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
        self.assertEqual(metric_file_callback._metric_file_output_path, self.path)
        self.assertEqual(metric_file_callback._scenario_metric_paths, [self.path])

    @patch('nuplan.planning.simulation.main_callback.metric_file_callback.logger')
    def test_on_run_simulation_end(self, logger: MagicMock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
        metric_file_callback.on_run_simulation_end()
        logger.info.assert_has_calls([call('Metric files integration: 00:00:00 [HH:MM:SS]')])

@patch('nuplan.planning.simulation.main_callback.metric_file_callback.logger')
def test_on_run_simulation_end(self, logger: MagicMock) -> None:
    """
        Tests if the callback is called with the correct parameters.
        """
    metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
    metric_file_callback.on_run_simulation_end()
    logger.info.assert_has_calls([call('Metric files integration: 00:00:00 [HH:MM:SS]')])

class TestPublisherCallback(TestCase):
    """
    Tests PublisherCallback.
    """

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        fake_targets = {'metrics': {'upload': True, 'save_path': 'some/path/to/save', 'remote_path': 'path/save'}, 'pictures': {'upload': True, 'save_path': 'some/path/to/pictures', 'remote_path': 'path/pictures'}}
        self.fake_uploads = [UploadConfig('metrics', pathlib.Path('some/path/to/save'), pathlib.Path('user/image/path/save')), UploadConfig('pictures', pathlib.Path('some/path/to/pictures'), pathlib.Path('user/image/path/pictures'))]
        self.mock_client = Mock()
        self.publisher_callback = PublisherCallback(fake_targets, self.mock_client, 'bucket', ['user', 'image'])

    def test_publisher_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        self.assertEqual(self.fake_uploads, self.publisher_callback._upload_targets)

    @patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib')
    @patch('nuplan.planning.simulation.main_callback.publisher_callback.list_files')
    def test_on_run_simulation_end_push_to_s3(self, mock_files: Mock, mock_pathlib: Mock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        fake_path = Mock()
        fake_path.iterdir.return_value = [True]
        fake_path.__truediv__ = lambda name, x: f'bucket/{x}'
        mock_pathlib.Path.return_value = fake_path
        mock_files.return_value = ['a', 'b']
        self.publisher_callback.on_run_simulation_end()
        expected_calls = [call('some/path/to/save/a', 'bucket', 'user/image/path/save/a'), call('some/path/to/save/b', 'bucket', 'user/image/path/save/b'), call('some/path/to/pictures/a', 'bucket', 'user/image/path/pictures/a'), call('some/path/to/pictures/b', 'bucket', 'user/image/path/pictures/b')]
        self.mock_client.upload_file.assert_has_calls(expected_calls)

    @patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib', MagicMock())
    @patch('nuplan.planning.simulation.main_callback.publisher_callback.boto3')
    def test_no_push_without_results(self, mock_boto3: Mock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        empty_publisher_callback = PublisherCallback({}, self.mock_client, 'bucket', ['user', 'image'])
        empty_publisher_callback.on_run_simulation_end()
        mock_boto3.client.return_value.assert_not_called()

def test_publisher_callback_init(self) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    self.assertEqual(self.fake_uploads, self.publisher_callback._upload_targets)

@patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib')
@patch('nuplan.planning.simulation.main_callback.publisher_callback.list_files')
def test_on_run_simulation_end_push_to_s3(self, mock_files: Mock, mock_pathlib: Mock) -> None:
    """
        Tests if the callback is called with the correct parameters.
        """
    fake_path = Mock()
    fake_path.iterdir.return_value = [True]
    fake_path.__truediv__ = lambda name, x: f'bucket/{x}'
    mock_pathlib.Path.return_value = fake_path
    mock_files.return_value = ['a', 'b']
    self.publisher_callback.on_run_simulation_end()
    expected_calls = [call('some/path/to/save/a', 'bucket', 'user/image/path/save/a'), call('some/path/to/save/b', 'bucket', 'user/image/path/save/b'), call('some/path/to/pictures/a', 'bucket', 'user/image/path/pictures/a'), call('some/path/to/pictures/b', 'bucket', 'user/image/path/pictures/b')]
    self.mock_client.upload_file.assert_has_calls(expected_calls)

@patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib', MagicMock())
@patch('nuplan.planning.simulation.main_callback.publisher_callback.boto3')
def test_no_push_without_results(self, mock_boto3: Mock) -> None:
    """
        Tests if the callback is called with the correct parameters.
        """
    empty_publisher_callback = PublisherCallback({}, self.mock_client, 'bucket', ['user', 'image'])
    empty_publisher_callback.on_run_simulation_end()
    mock_boto3.client.return_value.assert_not_called()

class TestMetricSummaryCallback(unittest.TestCase):
    """Test metric_summary callback functionality."""

    def set_up_dummy_metric(self, metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90)]
        time_stamps = [0, 1, 2]
        accel = [0.0, 1.0, 2.0]
        time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
        result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1)
        key = MetricFileKey(metric_name='ego_acceleration', scenario_name=scenario_name, log_name=log_name, scenario_type=scenario_type, planner_name=planner_name)
        metric_engine = MetricsEngine(main_save_path=metric_path)
        metric_files = {'ego_acceleration': [MetricFile(key=key, metric_statistics=[result])]}
        metric_engine.write_to_files(metric_files=metric_files)
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)], delete_scenario_metric_files=True)
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """Set up a nuboard base tab."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.tmp_dir.name) / 'metrics'
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        self.aggregator_save_path = Path(self.tmp_dir.name) / 'aggregator_metric'
        self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=self.aggregator_save_path, multiple_metrics=[])
        self.metric_statistics_dataframes = {}
        for metric_parquet_file in metric_path.iterdir():
            print(metric_parquet_file)
            data_frame = MetricStatisticsDataFrame.load_parquet(metric_parquet_file)
            self.metric_statistics_dataframes[data_frame.metric_statistic_name] = data_frame
        self.metric_summary_output_path = Path(self.tmp_dir.name) / 'summary'
        self.metric_summary_callback = MetricSummaryCallback(metric_save_path=str(metric_path), metric_aggregator_save_path=str(self.aggregator_save_path), summary_output_path=str(self.metric_summary_output_path), pdf_file_name='summary.pdf')

    def test_metric_summary_callback_on_simulation_end(self) -> None:
        """Test on_simulation_end in metric summary callback."""
        self.weighted_average_metric_aggregator(metric_dataframes=self.metric_statistics_dataframes)
        self.metric_summary_callback.on_run_simulation_end()
        pdf_files = self.metric_summary_output_path.rglob('*.pdf')
        self.assertEqual(len(list(pdf_files)), 1)

    def tearDown(self) -> None:
        """Remove all temporary folders and files."""
        self.tmp_dir.cleanup()

def test_metric_summary_callback_on_simulation_end(self) -> None:
    """Test on_simulation_end in metric summary callback."""
    self.weighted_average_metric_aggregator(metric_dataframes=self.metric_statistics_dataframes)
    self.metric_summary_callback.on_run_simulation_end()
    pdf_files = self.metric_summary_output_path.rglob('*.pdf')
    self.assertEqual(len(list(pdf_files)), 1)

class TestMetricAggregatorCallback(TestCase):
    """Test MetricAggregatorCallback."""

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        self.mock_metric_aggregator_callback = Mock(spec=MetricAggregatorCallback)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp_dir.name)
        self.path.mkdir(parents=True, exist_ok=True)
        self.metric_aggregators = [MockAbstractMetricAggregator(self.path)]

    def tearDown(self) -> None:
        """Clean up tmp dir."""
        self.tmp_dir.cleanup()

    def test_metric_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        metric_aggregator_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
        self.assertEqual(metric_aggregator_callback._metric_save_path, self.path)
        self.assertEqual(metric_aggregator_callback._metric_aggregators, self.metric_aggregators)

    @patch('nuplan.planning.simulation.main_callback.metric_aggregator_callback.logger')
    def test_on_run_simulation_end(self, logger: MagicMock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        metric_file_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
        metric_file_callback.on_run_simulation_end()
        logger.warning.assert_has_calls([call('dummy_metric_aggregator: No metric files found for aggregation!')])
        logger.info.assert_has_calls([call('Metric aggregator: 00:00:00 [HH:MM:SS]')])

def test_metric_callback_init(self) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    metric_aggregator_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
    self.assertEqual(metric_aggregator_callback._metric_save_path, self.path)
    self.assertEqual(metric_aggregator_callback._metric_aggregators, self.metric_aggregators)

@patch('nuplan.planning.simulation.main_callback.metric_aggregator_callback.logger')
def test_on_run_simulation_end(self, logger: MagicMock) -> None:
    """
        Tests if the callback is called with the correct parameters.
        """
    metric_file_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
    metric_file_callback.on_run_simulation_end()
    logger.warning.assert_has_calls([call('dummy_metric_aggregator: No metric files found for aggregation!')])
    logger.info.assert_has_calls([call('Metric aggregator: 00:00:00 [HH:MM:SS]')])

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

class IDMAgent:
    """IDM smart-agent."""

    def __init__(self, start_iteration: int, initial_state: IDMInitialState, route: List[LaneGraphEdgeMapObject], policy: IDMPolicy, minimum_path_length: float, max_route_len: int=5):
        """
        Constructor for IDMAgent.
        :param start_iteration: scenario iteration where agent first appeared
        :param initial_state: agent initial state
        :param route: agent initial route plan
        :param policy: policy controlling the agent behavior
        :param minimum_path_length: [m] The minimum path length
        :param max_route_len: The max number of route elements to store
        """
        self._start_iteration = start_iteration
        self._initial_state = initial_state
        self._state = IDMAgentState(initial_state.path_progress, initial_state.velocity.x)
        self._route: Deque[LaneGraphEdgeMapObject] = deque(route, maxlen=max_route_len)
        self._path = self._convert_route_to_path()
        self._policy = policy
        self._minimum_path_length = minimum_path_length
        self._size = (initial_state.box.width, initial_state.box.length, initial_state.box.height)
        self._requires_state_update: bool = True
        self._full_agent_state: Optional[Agent] = None

    def propagate(self, lead_agent: IDMLeadAgentState, tspan: float) -> None:
        """
        Propagate agent forward according to the IDM policy.

        :param lead_agent: the agent leading this agent
        :param tspan: the interval of time to propagate for
        """
        speed_limit = self.end_segment.speed_limit_mps
        if speed_limit is not None and speed_limit > 0.0:
            self._policy.target_velocity = speed_limit
        solution = self._policy.solve_forward_euler_idm_policy(IDMAgentState(0, self._state.velocity), lead_agent, tspan)
        self._state.progress += solution.progress
        self._state.velocity = max(solution.velocity, 0)
        self._requires_state_update = True

    @property
    def agent(self) -> Agent:
        """:return: the agent as a Agent object"""
        return self._get_agent_at_progress(self._get_bounded_progress())

    @property
    def polygon(self) -> Polygon:
        """:return: the agent as a Agent object"""
        return self.agent.box.geometry

    def get_route(self) -> List[LaneGraphEdgeMapObject]:
        """:return: The route the IDM agent is following."""
        return list(self._route)

    @property
    def projected_footprint(self) -> Polygon:
        """
        Returns the agent's projected footprint along it's planned path. The extended length is proportional
        to it's current velocity
        :return: The agent's projected footprint as a Polygon.
        """
        start_progress = self._clamp_progress(self.progress - self.length / 2)
        end_progress = self._clamp_progress(self.progress + self.length / 2 + self.velocity * self._policy.headway_time)
        projected_path = path_to_linestring(trim_path(self._path, start_progress, end_progress))
        return unary_union([projected_path.buffer(self.width / 2, cap_style=CAP_STYLE.flat), self.polygon])

    @property
    def width(self) -> float:
        """:return: [m] agent's width"""
        return float(self._initial_state.box.width)

    @property
    def length(self) -> float:
        """:return: [m] agent's length"""
        return float(self._initial_state.box.length)

    @property
    def progress(self) -> float:
        """:return: [m] agent's progress"""
        return self._state.progress

    @property
    def velocity(self) -> float:
        """:return: [m/s] agent's velocity along the path"""
        return self._state.velocity

    @property
    def end_segment(self) -> LaneGraphEdgeMapObject:
        """
        Returns the last segment in the agent's route
        :return: End segment as a LaneGraphEdgeMapObject
        """
        return self._route[-1]

    def to_se2(self) -> StateSE2:
        """
        :return: the agent as a StateSE2 object
        """
        return self._get_agent_at_progress(self._get_bounded_progress()).box.center

    def is_active(self, iteration: int) -> bool:
        """
        Return if the agent should be active at a simulation iteration

        :param iteration: the current simulation iteration
        :return: true if active, false otherwise
        """
        return self._start_iteration <= iteration

    def has_valid_path(self) -> bool:
        """
        :return: true if agent has a valid path, false otherwise
        """
        return self._path is not None

    def _get_bounded_progress(self) -> float:
        """
        :return: [m] The agent's progress. The progress is clamped between the start and end progress of it's path
        """
        return self._clamp_progress(self._state.progress)

    def get_path_to_go(self) -> List[ProgressStateSE2]:
        """
        :return: The agent's path trimmed to start at the agent's current progress
        """
        return trim_path_up_to_progress(self._path, self._get_bounded_progress())

    def get_progress_to_go(self) -> float:
        """
        return: [m] the progress left until the end of the path
        """
        return self._path.get_end_progress() - self.progress

    def get_agent_with_planned_trajectory(self, num_samples: int, sampling_time: float) -> Agent:
        """
        Samples the the agent's trajectory. The velocity is assumed to be constant over the sampled trajectory
        :param num_samples: number of elements to sample.
        :param sampling_time: [s] time interval of sequence to sample from.
        :return: the agent's trajectory as a list of Agent
        """
        return self._get_agent_at_progress(self._get_bounded_progress(), num_samples, sampling_time)

    def plan_route(self, traffic_light_status: Dict[TrafficLightStatusType, List[str]]) -> None:
        """
        The planning logic for the agent.
            - Prefers going straight. Selects edge with the lowest curvature.
            - Looks to add a segment to the route if:
                - the progress to go is less than the agent's desired velocity multiplied by the desired headway time
                  plus the minimum path length
                - the outgoing segment is active

        :param traffic_light_status: {traffic_light_status: lane_connector_ids} A dictionary containing traffic light information
        """
        while self.get_progress_to_go() < self._minimum_path_length + self._policy.target_velocity * self._policy.headway_time:
            outgoing_edges = self.end_segment.outgoing_edges
            selected_outgoing_edges = []
            for edge in outgoing_edges:
                if edge.has_traffic_lights():
                    if edge.id in traffic_light_status[TrafficLightStatusType.GREEN]:
                        selected_outgoing_edges.append(edge)
                elif edge.id not in traffic_light_status[TrafficLightStatusType.RED]:
                    selected_outgoing_edges.append(edge)
            if not selected_outgoing_edges:
                break
            curvatures = [abs(edge.baseline_path.get_curvature_at_arc_length(0.0)) for edge in selected_outgoing_edges]
            idx = np.argmin(curvatures)
            new_segment = selected_outgoing_edges[idx]
            self._route.append(new_segment)
            self._path = create_path_from_se2(self.get_path_to_go() + new_segment.baseline_path.discrete_path)
            self._state.progress = 0

    def _get_agent_at_progress(self, progress: float, num_samples: Optional[int]=None, sampling_time: Optional[float]=None) -> Agent:
        """
        Returns the agent as a box at a given progress
        :param progress: the arc length along the agent's path
        :return: the agent as a Agent object at the given progress
        """
        if not self._requires_state_update:
            return self._full_agent_state
        if self._path is not None:
            init_pose = self._path.get_state_at_progress(progress)
            box = OrientedBox.from_new_pose(self._initial_state.box, StateSE2(init_pose.x, init_pose.y, init_pose.heading))
            future_trajectory = None
            if num_samples and sampling_time:
                progress_samples = [self._clamp_progress(progress + self.velocity * sampling_time * (step + 1)) for step in range(num_samples)]
                future_poses = self._path.get_state_at_progresses(progress_samples)
                time_stamps = [TimePoint(int(1000000.0 * sampling_time * (step + 1))) for step in range(num_samples)]
                init_way_point = [Waypoint(TimePoint(0), box, self._velocity_to_global_frame(init_pose.heading))]
                waypoints = [Waypoint(time, OrientedBox.from_new_pose(self._initial_state.box, pose), self._velocity_to_global_frame(pose.heading)) for time, pose in zip(time_stamps, future_poses)]
                future_trajectory = PredictedTrajectory(1.0, init_way_point + waypoints)
            self._full_agent_state = Agent(metadata=self._initial_state.metadata, oriented_box=box, velocity=self._velocity_to_global_frame(init_pose.heading), tracked_object_type=self._initial_state.tracked_object_type, predictions=[future_trajectory] if future_trajectory is not None else [])
        else:
            self._full_agent_state = Agent(metadata=self._initial_state.metadata, oriented_box=self._initial_state.box, velocity=self._initial_state.velocity, tracked_object_type=self._initial_state.tracked_object_type, predictions=self._initial_state.predictions)
        self._requires_state_update = False
        return self._full_agent_state

    def _clamp_progress(self, progress: float) -> float:
        """
        Clamp the progress to be between the agent's path bounds
        :param progress: [m] the progress along the agent's path
        :return: [m] the progress clamped between the start and end progress of the agent's path
        """
        return max(self._path.get_start_progress(), min(progress, self._path.get_end_progress()))

    def _convert_route_to_path(self) -> InterpolatedPath:
        """
        Converts the route into an InterpolatedPath
        :return: InterpolatedPath from the agent's route
        """
        blp: List[StateSE2] = []
        for segment in self._route:
            blp.extend(segment.baseline_path.discrete_path)
        return create_path_from_se2(blp)

    def _velocity_to_global_frame(self, heading: float) -> StateVector2D:
        """
        Transform agent's velocity along the path to global frame
        :param heading: [rad] The heading defining the transform to global frame.
        :return: The velocity vector in global frame.
        """
        return StateVector2D(self.velocity * np.cos(heading), self.velocity * np.sin(heading))

def __init__(self, start_iteration: int, initial_state: IDMInitialState, route: List[LaneGraphEdgeMapObject], policy: IDMPolicy, minimum_path_length: float, max_route_len: int=5):
    """
        Constructor for IDMAgent.
        :param start_iteration: scenario iteration where agent first appeared
        :param initial_state: agent initial state
        :param route: agent initial route plan
        :param policy: policy controlling the agent behavior
        :param minimum_path_length: [m] The minimum path length
        :param max_route_len: The max number of route elements to store
        """
    self._start_iteration = start_iteration
    self._initial_state = initial_state
    self._state = IDMAgentState(initial_state.path_progress, initial_state.velocity.x)
    self._route: Deque[LaneGraphEdgeMapObject] = deque(route, maxlen=max_route_len)
    self._path = self._convert_route_to_path()
    self._policy = policy
    self._minimum_path_length = minimum_path_length
    self._size = (initial_state.box.width, initial_state.box.length, initial_state.box.height)
    self._requires_state_update: bool = True
    self._full_agent_state: Optional[Agent] = None

def propagate(self, lead_agent: IDMLeadAgentState, tspan: float) -> None:
    """
        Propagate agent forward according to the IDM policy.

        :param lead_agent: the agent leading this agent
        :param tspan: the interval of time to propagate for
        """
    speed_limit = self.end_segment.speed_limit_mps
    if speed_limit is not None and speed_limit > 0.0:
        self._policy.target_velocity = speed_limit
    solution = self._policy.solve_forward_euler_idm_policy(IDMAgentState(0, self._state.velocity), lead_agent, tspan)
    self._state.progress += solution.progress
    self._state.velocity = max(solution.velocity, 0)
    self._requires_state_update = True

class IDMPolicyTests(unittest.TestCase):
    """Tests implementation of IDMPolicy"""

    def setUp(self):
        """Test setup"""
        self.idm = IDMPolicy(target_velocity=30, min_gap_to_lead_agent=2, headway_time=1.5, accel_max=0.73, decel_max=1.67)
        self.sampling_time = 0.5
        self.agent = IDMAgentState(5, 3)
        self.lead_agent = IDMLeadAgentState(15, 2, 5)

    def test_idm_model(self):
        """Tests the model correctness"""
        model = self.idm.idm_model([], self.agent.to_array(), self.lead_agent.to_array(), self.idm.idm_params)
        self.assertEqual(3, model[0])
        self.assertAlmostEqual(-1.073366, model[1])

    def test_solve_forward_euler_idm_policy(self):
        """Tests expected behaviour of forward euler method"""
        solution = self.idm.solve_forward_euler_idm_policy(self.agent, self.lead_agent, self.sampling_time)
        self.assertEqual(6.5, solution.progress)
        self.assertAlmostEqual(2.46331699693, solution.velocity)

    def test_non_differential_idm_policy(self):
        """Tests expected behaviour of odeint integrator"""
        solution = self.idm.solve_odeint_idm_policy(self.agent, self.lead_agent, self.sampling_time, 2)
        self.assertAlmostEqual(6.3558523392415, solution.progress)
        self.assertAlmostEqual(2.4058965769308, solution.velocity)

    def test_solve_ivp_idm_policy(self):
        """Tests expected behaviour of inital value problem integrator"""
        solution = self.idm.solve_ivp_idm_policy(self.agent, self.lead_agent, self.sampling_time)
        self.assertAlmostEqual(6.355856711603, solution.progress)
        self.assertAlmostEqual(2.40590847399835, solution.velocity)

def test_solve_forward_euler_idm_policy(self):
    """Tests expected behaviour of forward euler method"""
    solution = self.idm.solve_forward_euler_idm_policy(self.agent, self.lead_agent, self.sampling_time)
    self.assertEqual(6.5, solution.progress)
    self.assertAlmostEqual(2.46331699693, solution.velocity)

class InterpolatedTrajectory(AbstractTrajectory):
    """Class representing a trajectory that can be interpolated from a list of points."""

    def __init__(self, trajectory: List[InterpolatableState]):
        """
        :param trajectory: List of states creating a trajectory.
            The trajectory has to have at least 2 elements, otherwise it is considered invalid and the class will raise.
        """
        assert trajectory, "Trajectory can't be empty!"
        assert isinstance(trajectory[0], InterpolatableState)
        self._trajectory_class = trajectory[0].__class__
        assert all((isinstance(point, self._trajectory_class) for point in trajectory))
        if len(trajectory) <= 1:
            raise ValueError(f'There is not enough states in trajectory: {len(trajectory)}!')
        self._trajectory = trajectory
        time_series = [point.time_us for point in trajectory]
        linear_states = []
        angular_states = []
        for point in trajectory:
            split_state = point.to_split_state()
            linear_states.append(split_state.linear_states)
            angular_states.append(split_state.angular_states)
        self._fixed_state = trajectory[0].to_split_state().fixed_states
        linear_states = np.array(linear_states, dtype='float64')
        angular_states = np.array(angular_states, dtype='float64')
        self._function_interp_linear = sp_interp.interp1d(time_series, linear_states, axis=0)
        self._angular_interpolator = AngularInterpolator(time_series, angular_states)

    def __reduce__(self) -> Tuple[Type[InterpolatedTrajectory], Tuple[Any, ...]]:
        """
        Helper for pickling.
        """
        return (self.__class__, (self._trajectory,))

    @property
    def start_time(self) -> TimePoint:
        """Inherited, see superclass."""
        return self._trajectory[0].time_point

    @property
    def end_time(self) -> TimePoint:
        """Inherited, see superclass."""
        return self._trajectory[-1].time_point

    def get_state_at_time(self, time_point: TimePoint) -> InterpolatableState:
        """Inherited, see superclass."""
        start_time = self.start_time
        end_time = self.end_time
        assert start_time <= time_point <= end_time, f'Interpolation time time_point={time_point!r} not in trajectory time window! \nstart_time.time_us={start_time.time_us!r} <= time_point.time_us={time_point.time_us!r} <= end_time.time_us={end_time.time_us!r}'
        linear_states = list(self._function_interp_linear(time_point.time_us))
        angular_states = list(self._angular_interpolator.interpolate(time_point.time_us))
        return self._trajectory_class.from_split_state(SplitState(linear_states, angular_states, self._fixed_state))

    def get_state_at_times(self, time_points: List[TimePoint]) -> List[InterpolatableState]:
        """Inherited, see superclass."""
        start_time = self.start_time
        end_time = self.end_time
        assert start_time <= min(time_points), f'Interpolation time not in trajectory time window! The following is not satisfied:Trajectory start time: ({start_time.time_s}) <= Earliest interpolation time ({min(time_points).time_s}) {max(time_points).time_s} <= {end_time.time_s} '
        assert max(time_points) <= end_time, f'Interpolation time not in trajectory time window! The following is not satisfied:Trajectory end time: ({end_time.time_s}) >= Latest interpolation time ({max(time_points).time_s}) '
        interpolation_times = [t.time_us for t in time_points]
        linear_states = list(self._function_interp_linear(interpolation_times))
        angular_states = list(self._angular_interpolator.interpolate(interpolation_times))
        return [self._trajectory_class.from_split_state(SplitState(lin_state, ang_state, self._fixed_state)) for lin_state, ang_state in zip(linear_states, angular_states)]

    def get_sampled_trajectory(self) -> List[InterpolatableState]:
        """Inherited, see superclass."""
        return self._trajectory

def __init__(self, trajectory: List[InterpolatableState]):
    """
        :param trajectory: List of states creating a trajectory.
            The trajectory has to have at least 2 elements, otherwise it is considered invalid and the class will raise.
        """
    assert trajectory, "Trajectory can't be empty!"
    assert isinstance(trajectory[0], InterpolatableState)
    self._trajectory_class = trajectory[0].__class__
    assert all((isinstance(point, self._trajectory_class) for point in trajectory))
    if len(trajectory) <= 1:
        raise ValueError(f'There is not enough states in trajectory: {len(trajectory)}!')
    self._trajectory = trajectory
    time_series = [point.time_us for point in trajectory]
    linear_states = []
    angular_states = []
    for point in trajectory:
        split_state = point.to_split_state()
        linear_states.append(split_state.linear_states)
        angular_states.append(split_state.angular_states)
    self._fixed_state = trajectory[0].to_split_state().fixed_states
    linear_states = np.array(linear_states, dtype='float64')
    angular_states = np.array(angular_states, dtype='float64')
    self._function_interp_linear = sp_interp.interp1d(time_series, linear_states, axis=0)
    self._angular_interpolator = AngularInterpolator(time_series, angular_states)

class TestInterpolatedTrajectory(unittest.TestCase):
    """Tests implementation of InterpolatedTrajectory."""

    def setUp(self) -> None:
        """Test setup."""
        self.split_state_1 = Mock(linear_states=[123], angular_states=[2.13], fixed_states=['fix'], autspec=SplitState)
        self.split_state_2 = Mock(linear_states=[456], angular_states=[3.13], fixed_states=['fix'], autspec=SplitState)
        self.start_time_point = TimePoint(0)
        self.end_time_point = TimePoint(int(1000000.0))
        self.points = [MagicMock(time_point=self.start_time_point, time_us=self.start_time_point.time_us, to_split_state=lambda: self.split_state_1, spec=MockPoint), MagicMock(time_point=self.end_time_point, time_us=self.end_time_point.time_us, to_split_state=lambda: self.split_state_2, spec=MockPoint)]
        self.trajectory = InterpolatedTrajectory(self.points)

    def tearDown(self) -> None:
        """Resets mock objects."""
        MockPoint.reset_calls()

    @patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.sp_interp')
    @patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.np')
    @patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.AngularInterpolator', autospec=True)
    def test_initialization(self, mock_interp_angular: Mock, mock_np: Mock, mock_sp_interp: Mock) -> None:
        """Tests that initialization works as intended."""
        mock_sp_interp.interp1d.return_value = 'interp_function'
        mock_np.array.return_value = 'array'
        trajectory = InterpolatedTrajectory(self.points)
        self.assertEqual(trajectory._trajectory_class, MockPoint)
        self.assertEqual(trajectory._fixed_state, ['fix'])
        mock_sp_interp.interp1d.assert_called_with([0, 1000000], mock_np.array.return_value, axis=0)
        self.assertEqual(trajectory._function_interp_linear, mock_sp_interp.interp1d.return_value)
        mock_interp_angular.assert_called_with([0, 1000000], 'array')
        self.assertEqual(trajectory._angular_interpolator, mock_interp_angular.return_value)
        with self.assertRaises(AssertionError):
            InterpolatedTrajectory([MagicMock()])

    def test_start_end_time(self) -> None:
        """Tests that properties return correct members."""
        self.assertEqual(self.start_time_point, self.trajectory.start_time)
        self.assertEqual(self.end_time_point, self.trajectory.end_time)

    def test_get_state_at_time(self) -> None:
        """Tests interpolation method."""
        time_point = TimePoint(int(0.5 * 1000000.0))
        state = self.trajectory.get_state_at_time(time_point)
        self.assertEqual('foo', state)
        interpolated_state = SplitState(linear_states=[289.5], angular_states=[2.63], fixed_states=['fix'])
        self.assertEqual(MockPoint.from_split_state.calls, [interpolated_state])
        time_point_outside_interval = TimePoint(int(5 * 1000000.0))
        with self.assertRaises(AssertionError):
            self.trajectory.get_state_at_time(time_point_outside_interval)

    def test_get_state_at_times(self) -> None:
        """Tests batch interpolation method."""
        time_points = [TimePoint(0), TimePoint(int(0.5 * 1000000.0))]
        states = self.trajectory.get_state_at_times(time_points)
        self.assertEqual(['foo', 'foo'], states)
        initial_state = SplitState(linear_states=[123], angular_states=[2.13], fixed_states=['fix'])
        interpolated_state = SplitState(linear_states=[289.5], angular_states=[2.63], fixed_states=['fix'])
        self.assertEqual(MockPoint.from_split_state.calls, [initial_state, interpolated_state])
        time_point_outside_interval = TimePoint(int(5 * 1000000.0))
        with self.assertRaises(AssertionError):
            self.trajectory.get_state_at_times([time_point_outside_interval])

    def test_get_sampled_trajectory(self) -> None:
        """Tests getter for entire trajectory."""
        self.assertEqual(self.points, self.trajectory.get_sampled_trajectory())

def setUp(self) -> None:
    """Test setup."""
    self.split_state_1 = Mock(linear_states=[123], angular_states=[2.13], fixed_states=['fix'], autspec=SplitState)
    self.split_state_2 = Mock(linear_states=[456], angular_states=[3.13], fixed_states=['fix'], autspec=SplitState)
    self.start_time_point = TimePoint(0)
    self.end_time_point = TimePoint(int(1000000.0))
    self.points = [MagicMock(time_point=self.start_time_point, time_us=self.start_time_point.time_us, to_split_state=lambda: self.split_state_1, spec=MockPoint), MagicMock(time_point=self.end_time_point, time_us=self.end_time_point.time_us, to_split_state=lambda: self.split_state_2, spec=MockPoint)]
    self.trajectory = InterpolatedTrajectory(self.points)

@patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.sp_interp')
@patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.np')
@patch('nuplan.planning.simulation.trajectory.interpolated_trajectory.AngularInterpolator', autospec=True)
def test_initialization(self, mock_interp_angular: Mock, mock_np: Mock, mock_sp_interp: Mock) -> None:
    """Tests that initialization works as intended."""
    mock_sp_interp.interp1d.return_value = 'interp_function'
    mock_np.array.return_value = 'array'
    trajectory = InterpolatedTrajectory(self.points)
    self.assertEqual(trajectory._trajectory_class, MockPoint)
    self.assertEqual(trajectory._fixed_state, ['fix'])
    mock_sp_interp.interp1d.assert_called_with([0, 1000000], mock_np.array.return_value, axis=0)
    self.assertEqual(trajectory._function_interp_linear, mock_sp_interp.interp1d.return_value)
    mock_interp_angular.assert_called_with([0, 1000000], 'array')
    self.assertEqual(trajectory._angular_interpolator, mock_interp_angular.return_value)
    with self.assertRaises(AssertionError):
        InterpolatedTrajectory([MagicMock()])

def test_start_end_time(self) -> None:
    """Tests that properties return correct members."""
    self.assertEqual(self.start_time_point, self.trajectory.start_time)
    self.assertEqual(self.end_time_point, self.trajectory.end_time)

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

class TestSimulationHistory(TestCase):
    """Tests for SimulationHistory buffer."""

    def setUp(self) -> None:
        """
        Setup mocks for the tests
        """
        self.map = MagicMock(spec=AbstractMap)
        self.se2 = MagicMock(spec=StateSE2)
        self.sample = MagicMock(spec=SimulationHistorySample)
        self.sh = SimulationHistory(self.map, self.se2)

    def test_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        self.assertEqual(self.sh.map_api, self.map)
        self.assertEqual(self.sh.mission_goal, self.se2)
        self.assertEqual(self.sh.data, [])

    def test_add_sample(self) -> None:
        """
        Test if the add_sample method adds the passed sample to the data list.
        """
        with patch.object(self.sh, 'data', append=MagicMock()) as data:
            self.sh.add_sample(self.sample)
            data.append.assert_called_once_with(self.sample)

    def test_last(self) -> None:
        """Test if the last method works as expected."""
        self.sh.data = None
        with self.assertRaises(RuntimeError):
            self.sh.last()
        self.sh.data = [self.sample, self.sample]
        self.assertEqual(self.sh.last(), self.sample)

    def test_extract_ego_state(self) -> None:
        """Test if the extract_ego_state property works as expected."""
        with patch('nuplan.planning.simulation.history.simulation_history.SimulationHistorySample', autospec=True):
            mock_data = [SimulationHistorySample(iteration=MagicMock(), ego_state=MagicMock(side_effect=lambda: i), trajectory=MagicMock(), observation=MagicMock(), traffic_light_status=MagicMock()) for i in range(DATA_LEN)]
            self.sh.data = mock_data
            ego_states = self.sh.extract_ego_state
            self.assertTrue([ego_states[i]() == i for i in range(len(ego_states))])

    def test_clear(self) -> None:
        """
        Tests if the clear method clears the data list.
        """
        with patch.object(self.sh, 'data', clear=MagicMock()) as data:
            self.sh.reset()
            data.clear.assert_called_once()

    @patch('nuplan.planning.simulation.history.simulation_history.len', return_value=DATA_LEN)
    def test_len(self, len_mock: MagicMock) -> None:
        """
        Tests if the len method returns the length of the data list.
        """
        result = len(self.sh)
        self.assertEqual(result, DATA_LEN)
        len_mock.assert_called_once_with(self.sh.data)

    def test_interval_seconds(self) -> None:
        """Tests for the correct behavior of the interval_seconds property."""
        self.sh.data = None
        with self.assertRaises(ValueError):
            self.sh.interval_seconds
        self.sh.data = []
        with self.assertRaises(ValueError):
            self.sh.interval_seconds
        with patch('nuplan.planning.simulation.history.simulation_history.SimulationHistorySample', autospec=True):
            self.sh.data = [self.sample]
            with self.assertRaises(ValueError):
                self.sh.interval_seconds
            mock_data = [SimulationHistorySample(iteration=SimulationIteration(index=0, time_point=TimePoint(i * 1000.0)), ego_state=MagicMock(), trajectory=MagicMock(), observation=MagicMock(), traffic_light_status=MagicMock()) for i in range(DATA_LEN)]
            self.sh.data = mock_data
            expected_interval_seconds = mock_data[1].iteration.time_s - mock_data[0].iteration.time_s
            self.assertEqual(expected_interval_seconds, self.sh.interval_seconds)

def test_init(self) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    self.assertEqual(self.sh.map_api, self.map)
    self.assertEqual(self.sh.mission_goal, self.se2)
    self.assertEqual(self.sh.data, [])

def test_add_sample(self) -> None:
    """
        Test if the add_sample method adds the passed sample to the data list.
        """
    with patch.object(self.sh, 'data', append=MagicMock()) as data:
        self.sh.add_sample(self.sample)
        data.append.assert_called_once_with(self.sample)

def test_last(self) -> None:
    """Test if the last method works as expected."""
    self.sh.data = None
    with self.assertRaises(RuntimeError):
        self.sh.last()
    self.sh.data = [self.sample, self.sample]
    self.assertEqual(self.sh.last(), self.sample)

def test_extract_ego_state(self) -> None:
    """Test if the extract_ego_state property works as expected."""
    with patch('nuplan.planning.simulation.history.simulation_history.SimulationHistorySample', autospec=True):
        mock_data = [SimulationHistorySample(iteration=MagicMock(), ego_state=MagicMock(side_effect=lambda: i), trajectory=MagicMock(), observation=MagicMock(), traffic_light_status=MagicMock()) for i in range(DATA_LEN)]
        self.sh.data = mock_data
        ego_states = self.sh.extract_ego_state
        self.assertTrue([ego_states[i]() == i for i in range(len(ego_states))])

def test_clear(self) -> None:
    """
        Tests if the clear method clears the data list.
        """
    with patch.object(self.sh, 'data', clear=MagicMock()) as data:
        self.sh.reset()
        data.clear.assert_called_once()

@patch('nuplan.planning.simulation.history.simulation_history.len', return_value=DATA_LEN)
def test_len(self, len_mock: MagicMock) -> None:
    """
        Tests if the len method returns the length of the data list.
        """
    result = len(self.sh)
    self.assertEqual(result, DATA_LEN)
    len_mock.assert_called_once_with(self.sh.data)

def test_interval_seconds(self) -> None:
    """Tests for the correct behavior of the interval_seconds property."""
    self.sh.data = None
    with self.assertRaises(ValueError):
        self.sh.interval_seconds
    self.sh.data = []
    with self.assertRaises(ValueError):
        self.sh.interval_seconds
    with patch('nuplan.planning.simulation.history.simulation_history.SimulationHistorySample', autospec=True):
        self.sh.data = [self.sample]
        with self.assertRaises(ValueError):
            self.sh.interval_seconds
        mock_data = [SimulationHistorySample(iteration=SimulationIteration(index=0, time_point=TimePoint(i * 1000.0)), ego_state=MagicMock(), trajectory=MagicMock(), observation=MagicMock(), traffic_light_status=MagicMock()) for i in range(DATA_LEN)]
        self.sh.data = mock_data
        expected_interval_seconds = mock_data[1].iteration.time_s - mock_data[0].iteration.time_s
        self.assertEqual(expected_interval_seconds, self.sh.interval_seconds)

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

def test_initialize_with_box(self) -> None:
    """Test the initialize function"""
    tracks_observation = TracksObservation(self.scenario)
    history_buffer = SimulationHistoryBuffer.initialize_from_scenario(buffer_size=self.buffer_size, scenario=self.scenario, observation_type=tracks_observation.observation_type())
    self.assertEqual(len(history_buffer), self.buffer_size)

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

class VisualizationCallback(AbstractCallback):
    """Callback to render simulation data as the simulation runs."""

    def __init__(self, renderer: AbstractVisualization):
        """
        Constructor for VisualizationCallback.
        :param renderer: handler to create visualization.
        """
        self._visualization = renderer

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """
        In initialization start just render scenario
        """
        self._visualization.render_scenario(setup.scenario, True)

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """
        Render sample after a step
        """
        self._visualization.render_ego_state(sample.ego_state)
        self._visualization.render_observations(sample.observation)
        self._visualization.render_trajectory(sample.trajectory.get_sampled_trajectory())
        self._visualization.render(sample.iteration)

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
        On reached_end just call step_end
        """
        self.on_step_end(setup, planner, history.data[-1])

def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """
        On reached_end just call step_end
        """
    self.on_step_end(setup, planner, history.data[-1])

class TestVisualizationCallback(TestCase):
    """Tests VisualizationCallback."""

    def setUp(self) -> None:
        """
        Setup mocks for the tests
        """
        self.visualization = Mock(spec=AbstractVisualization)
        self.setup = Mock(spec=SimulationSetup)
        self.planner = Mock(spec=AbstractPlanner)
        self.history = Mock(spec=SimulationHistory, data=[7, 23, 42])
        self.history_sample = Mock(spec=SimulationHistorySample)
        self.setup.scenario = 'test_scenario'
        self.history_sample.ego_state = 'test_ego_state'
        self.history_sample.observation = 'test_observation'
        self.history_sample.iteration = 'test_iteration'
        self.history_sample.trajectory = Mock()
        self.history_sample.trajectory.get_sampled_trajectory = Mock(return_value=TRAJECTORY)
        self.vc = VisualizationCallback(self.visualization)
        return super().setUp()

    @patch.object(VisualizationCallback, '_visualization', create=True, new_callable=PropertyMock)
    def test_constructor(self, visualization: MagicMock) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        VisualizationCallback(self.visualization)
        visualization.assert_called_once_with(self.visualization)

    def test_on_initialization_start(self) -> None:
        """
        Tests if the visualization.render_scenario is called when the initialization starts.
        """
        with patch.object(self.vc, '_visualization', create=True, render_scenario=Mock()) as visualization:
            self.vc.on_initialization_start(self.setup, self.planner)
            visualization.render_scenario.assert_called_once_with(self.setup.scenario, True)

    def test_on_step_end(self) -> None:
        """
        Tests if render_ego_state, render_observations, render_trajectory ,render
        are called with correct parameters in the on_step_end
        """
        with patch.object(self.vc, '_visualization', create=True) as visualization:
            visualization.render_ego_state = Mock()
            visualization.render_observations = Mock()
            visualization.render_trajectory = Mock()
            visualization.render = Mock()
            self.vc.on_step_end(self.setup, self.planner, self.history_sample)
            visualization.render_ego_state.assert_called_once_with(self.history_sample.ego_state)
            visualization.render_observations.assert_called_once_with(self.history_sample.observation)
            visualization.render_trajectory.assert_called_once_with(TRAJECTORY)
            visualization.render.assert_called_once_with(self.history_sample.iteration)
            self.history_sample.trajectory.get_sampled_trajectory.assert_called_once()

    @patch.object(VisualizationCallback, 'on_step_end')
    def test_on_simulation_end(self, on_step_end: MagicMock) -> None:
        """
        Tests if on_step_end is called with correct parameters in the on_simulation_end
        """
        self.vc.on_simulation_end(self.setup, self.planner, self.history)
        on_step_end.assert_called_once_with(self.setup, self.planner, self.history.data[-1])

@patch.object(VisualizationCallback, '_visualization', create=True, new_callable=PropertyMock)
def test_constructor(self, visualization: MagicMock) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    VisualizationCallback(self.visualization)
    visualization.assert_called_once_with(self.visualization)

def test_on_initialization_start(self) -> None:
    """
        Tests if the visualization.render_scenario is called when the initialization starts.
        """
    with patch.object(self.vc, '_visualization', create=True, render_scenario=Mock()) as visualization:
        self.vc.on_initialization_start(self.setup, self.planner)
        visualization.render_scenario.assert_called_once_with(self.setup.scenario, True)

def test_on_step_end(self) -> None:
    """
        Tests if render_ego_state, render_observations, render_trajectory ,render
        are called with correct parameters in the on_step_end
        """
    with patch.object(self.vc, '_visualization', create=True) as visualization:
        visualization.render_ego_state = Mock()
        visualization.render_observations = Mock()
        visualization.render_trajectory = Mock()
        visualization.render = Mock()
        self.vc.on_step_end(self.setup, self.planner, self.history_sample)
        visualization.render_ego_state.assert_called_once_with(self.history_sample.ego_state)
        visualization.render_observations.assert_called_once_with(self.history_sample.observation)
        visualization.render_trajectory.assert_called_once_with(TRAJECTORY)
        visualization.render.assert_called_once_with(self.history_sample.iteration)
        self.history_sample.trajectory.get_sampled_trajectory.assert_called_once()

@patch.object(VisualizationCallback, 'on_step_end')
def test_on_simulation_end(self, on_step_end: MagicMock) -> None:
    """
        Tests if on_step_end is called with correct parameters in the on_simulation_end
        """
    self.vc.on_simulation_end(self.setup, self.planner, self.history)
    on_step_end.assert_called_once_with(self.setup, self.planner, self.history.data[-1])

class SkeletonTestSerializationCallback(unittest.TestCase):
    """Base class for TestsSerializationCallback* classes."""

    def _setUp(self) -> None:
        """Setup mocks for our tests."""
        self._serialization_type_to_extension_map = {'json': '.json', 'pickle': '.pkl.xz', 'msgpack': '.msgpack.xz'}
        self._serialization_type = getattr(self, '_serialization_type', '')
        self.assertIn(self._serialization_type, self._serialization_type_to_extension_map)
        self.output_folder = tempfile.TemporaryDirectory()
        self.callback = SerializationCallback(output_directory=self.output_folder.name, folder_name='sim', serialization_type=self._serialization_type, serialize_into_single_file=True)
        self.sim_manager = Mock(spec=AbstractSimulationTimeController)
        self.observation = Mock(spec=AbstractObservation)
        self.controller = Mock(spec=AbstractEgoController)
        super().setUp()

    @settings(deadline=None)
    @given(mock_timestamp=st.one_of(st.just(0), st.integers(min_value=1627066061949808, max_value=18446744073709551615)))
    def _dump_test_scenario(self, mock_timestamp: int) -> None:
        """
        Tests whether a scene can be dumped into a file and check that the keys are in the dumped scene.
        :param mock_timestamp: Mocked timestamp to pass to mock_get_traffic_light_status_at_iteration.
        """

        def mock_get_traffic_light_status_at_iteration(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
            """Mocks MockAbstractScenario.get_traffic_light_status_at_iteration to return large numbers."""
            dummy_tl_data = TrafficLightStatusData(status=TrafficLightStatusType.GREEN, lane_connector_id=1, timestamp=mock_timestamp)
            yield dummy_tl_data
        scenario = MockAbstractScenario()
        scenario.get_traffic_light_status_at_iteration = Mock(spec=scenario.get_traffic_light_status_at_iteration)
        scenario.get_traffic_light_status_at_iteration.side_effect = mock_get_traffic_light_status_at_iteration
        self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
        planner = Mock()
        planner.name = Mock(return_value='DummyPlanner')
        directory = self.callback._get_scenario_folder(planner.name(), scenario)
        self.assertEqual(str(directory), self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
        self.callback.on_initialization_start(self.setup, planner)
        history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=scenario.get_traffic_light_status_at_iteration(0)))
        for data in history.data:
            self.callback.on_step_end(self.setup, planner, data)
        self.callback.on_simulation_end(self.setup, planner, history)
        filename = 'mock_scenario_name' + self._serialization_type_to_extension_map[self._serialization_type]
        path = pathlib.Path(self.output_folder.name + '/sim/DummyPlanner/mock_scenario_type/mock_log_name/mock_scenario_name/' + filename)
        self.assertTrue(path.exists())
        if self._serialization_type == 'json':
            with open(path.absolute()) as f:
                data = json.load(f)
        elif self._serialization_type == 'msgpack':
            with lzma.open(str(path), 'rb') as f:
                data = msgpack.unpackb(f.read())
        elif self._serialization_type == 'pickle':
            with lzma.open(str(path), 'rb') as f:
                data = pickle.load(f)
        self.assertTrue(len(data) > 0)
        data = data[0]
        self.assertTrue('world' in data.keys())
        self.assertTrue('ego' in data.keys())
        self.assertTrue('trajectories' in data.keys())
        self.assertTrue('map' in data.keys())
        expected_traffic_light_data = next(scenario.get_traffic_light_status_at_iteration(0))
        actual_traffic_light_data_dict = data['traffic_light_status'][0]
        self.assertEqual(actual_traffic_light_data_dict['timestamp'], expected_traffic_light_data.timestamp)

def _setUp(self) -> None:
    """Setup mocks for our tests."""
    self._serialization_type_to_extension_map = {'json': '.json', 'pickle': '.pkl.xz', 'msgpack': '.msgpack.xz'}
    self._serialization_type = getattr(self, '_serialization_type', '')
    self.assertIn(self._serialization_type, self._serialization_type_to_extension_map)
    self.output_folder = tempfile.TemporaryDirectory()
    self.callback = SerializationCallback(output_directory=self.output_folder.name, folder_name='sim', serialization_type=self._serialization_type, serialize_into_single_file=True)
    self.sim_manager = Mock(spec=AbstractSimulationTimeController)
    self.observation = Mock(spec=AbstractObservation)
    self.controller = Mock(spec=AbstractEgoController)
    super().setUp()

class TestMetricCallback(TestCase):
    """Tests metrics callback."""

    def setUp(self) -> None:
        """
        Setup mocks for the tests
        """
        self.mock_metric_engine = Mock(spec=MetricsEngine)
        self.mock_metric_engine.compute = Mock(return_value=METRICS_LIST)
        self.mock_setup = Mock()
        self.mock_planner = Mock(spec=AbstractPlanner)
        self.mock_planner.name = Mock(return_value=PLANNER_NAME)
        self.mock_history = Mock()
        return super().setUp()

    def test_metric_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        mc = MetricCallback(self.mock_metric_engine)
        self.assertEqual(mc._metric_engine, self.mock_metric_engine)

    @patch('nuplan.planning.simulation.callback.metric_callback.logger')
    def test_on_simulation_end(self, logger: MagicMock) -> None:
        """
        Tests if the metric engine compute is called with the correct parameters.
        Tests if the metric engine save_metric_files is called with compute's result.
        Tests if the logger is called with the correct parameters.
        """
        mc = MetricCallback(self.mock_metric_engine)
        mc.on_simulation_end(self.mock_setup, self.mock_planner, self.mock_history)
        logger.debug.assert_has_calls([call('Starting metrics computation...'), call('Finished metrics computation!'), call('Saving metric statistics!'), call('Saved metrics!')])
        self.mock_planner.name.assert_called_once()
        self.mock_metric_engine.compute.assert_called_once_with(self.mock_history, scenario=self.mock_setup.scenario, planner_name=PLANNER_NAME)
        self.mock_metric_engine.write_to_files.assert_called_once_with(METRICS_LIST)

@patch('nuplan.planning.simulation.callback.metric_callback.logger')
def test_on_simulation_end(self, logger: MagicMock) -> None:
    """
        Tests if the metric engine compute is called with the correct parameters.
        Tests if the metric engine save_metric_files is called with compute's result.
        Tests if the logger is called with the correct parameters.
        """
    mc = MetricCallback(self.mock_metric_engine)
    mc.on_simulation_end(self.mock_setup, self.mock_planner, self.mock_history)
    logger.debug.assert_has_calls([call('Starting metrics computation...'), call('Finished metrics computation!'), call('Saving metric statistics!'), call('Saved metrics!')])
    self.mock_planner.name.assert_called_once()
    self.mock_metric_engine.compute.assert_called_once_with(self.mock_history, scenario=self.mock_setup.scenario, planner_name=PLANNER_NAME)
    self.mock_metric_engine.write_to_files.assert_called_once_with(METRICS_LIST)

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

def test_scenario_sampling_weight_initialises_correctly(self) -> None:
    """
        Test that the scenario sampling weights are correct.
        """
    self._init_distributed_process_group()
    scenarios_dataset = Mock(ScenarioDataset)
    scenarios_dataset._scenarios = self.mock_scenarios
    distributed_weight_sampler = distributed_weighted_sampler_init(scenario_dataset=scenarios_dataset, scenario_sampling_weights=self.mock_scenario_sampling_weights)
    self.assertEqual(list(distributed_weight_sampler.sampler.weights), self.expected_sampler_weights)

class SkeletonTestDataloader(unittest.TestCase):
    """
    Skeleton with initialized dataloader used in testing.
    """

    def setUp(self) -> None:
        """
        Set up basic configs.
        """
        pl.seed_everything(2022, workers=True)
        self.splitter = LogSplitter(log_splits={'train': ['2021.07.16.20.45.29_veh-35_01095_01486'], 'val': ['2021.06.07.18.53.26_veh-26_00005_00427'], 'test': ['2021.10.06.07.26.10_veh-52_00006_00398']})
        feature_builders = [DummyVectorMapBuilder(), VectorMapFeatureBuilder(radius=20), AgentsFeatureBuilder(TrajectorySampling(num_poses=4, time_horizon=1.5)), RasterFeatureBuilder(map_features={'LANE': 1, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1)]
        target_builders = [EgoTrajectoryTargetBuilder(TrajectorySampling(num_poses=10, time_horizon=5.0))]
        self.feature_preprocessor = FeaturePreprocessor(cache_path=None, force_feature_computation=True, feature_builders=feature_builders, target_builders=target_builders)
        self.scenario_filter = ScenarioFilter(scenario_types=None, scenario_tokens=None, log_names=None, map_names=None, num_scenarios_per_type=None, limit_total_scenarios=150, expand_scenarios=True, remove_invalid_goals=False, shuffle=True, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
        self.augmentors = [KinematicAgentAugmentor(trajectory_length=10, dt=0.1, mean=[0.3, 0.1, np.pi / 12], std=[0.5, 0.1, np.pi / 12], low=[-0.2, 0.0, 0.0], high=[0.8, 0.2, np.pi / 6], augment_prob=0.5)]
        self.scenario_builder = get_test_nuplan_scenario_builder()

    def _test_dataloader(self, worker: WorkerPool) -> None:
        """
        Tests that the training dataloader can be iterated without errors
        """
        scenarios = self.scenario_builder.get_scenarios(self.scenario_filter, worker)
        self.assertGreater(len(scenarios), 0)
        batch_size = 4
        num_workers = 4
        scenario_type_sampling_weights = DictConfig({'enable': False, 'scenario_type_weights': {'unknown': 1.0}})
        datamodule = DataModule(feature_preprocessor=self.feature_preprocessor, splitter=self.splitter, train_fraction=1.0, val_fraction=0.1, test_fraction=0.1, all_scenarios=scenarios, augmentors=self.augmentors, worker=worker, scenario_type_sampling_weights=scenario_type_sampling_weights, dataloader_params={'batch_size': batch_size, 'num_workers': num_workers, 'drop_last': True})
        datamodule.setup('fit')
        self.assertGreater(len(datamodule.train_dataloader()), 0)
        for features, targets, scenarios in datamodule.train_dataloader():
            self.assertTrue('raster' in features.keys())
            self.assertTrue('vector_map' in features.keys())
            self.assertTrue('trajectory' in targets.keys())
            scenario_features: Raster = features['raster']
            trajectory_target: Trajectory = targets['trajectory']
            self.assertEqual(scenario_features.num_batches, trajectory_target.num_batches)
            self.assertIsInstance(scenario_features, Raster)
            self.assertIsInstance(trajectory_target, Trajectory)
            self.assertEqual(scenario_features.num_batches, batch_size)

    def tearDown(self) -> None:
        """
        Clean up.
        """
        if ray.is_initialized():
            ray.shutdown()

def _test_dataloader(self, worker: WorkerPool) -> None:
    """
        Tests that the training dataloader can be iterated without errors
        """
    scenarios = self.scenario_builder.get_scenarios(self.scenario_filter, worker)
    self.assertGreater(len(scenarios), 0)
    batch_size = 4
    num_workers = 4
    scenario_type_sampling_weights = DictConfig({'enable': False, 'scenario_type_weights': {'unknown': 1.0}})
    datamodule = DataModule(feature_preprocessor=self.feature_preprocessor, splitter=self.splitter, train_fraction=1.0, val_fraction=0.1, test_fraction=0.1, all_scenarios=scenarios, augmentors=self.augmentors, worker=worker, scenario_type_sampling_weights=scenario_type_sampling_weights, dataloader_params={'batch_size': batch_size, 'num_workers': num_workers, 'drop_last': True})
    datamodule.setup('fit')
    self.assertGreater(len(datamodule.train_dataloader()), 0)
    for features, targets, scenarios in datamodule.train_dataloader():
        self.assertTrue('raster' in features.keys())
        self.assertTrue('vector_map' in features.keys())
        self.assertTrue('trajectory' in targets.keys())
        scenario_features: Raster = features['raster']
        trajectory_target: Trajectory = targets['trajectory']
        self.assertEqual(scenario_features.num_batches, trajectory_target.num_batches)
        self.assertIsInstance(scenario_features, Raster)
        self.assertIsInstance(trajectory_target, Trajectory)
        self.assertEqual(scenario_features.num_batches, batch_size)

class TestStepwiseAugmentationSheduler(unittest.TestCase):
    """Test scenario scoring callback"""

    def setUp(self) -> None:
        """Set up test case."""
        super().setUp()
        self.max_augment_prob = 0.8
        self.pct_time_increasing = 0.5
        self.max_aug_attribute_pct_increase = 0.2
        self.initial_augment_prob = 0.5
        self.milestones = [0.25, 0.5, 0.75, 1.0]
        self.cur_step = 1
        self.total_steps = 2
        self.mock_trajectory_length = 12
        self.mock_dt = 0.5
        self.mock_mean = [1.0, 0.0, 0.0]
        self.mock_std = [1.0, 1.0, 0.5]
        self.mock_low = [0.0, -1.0, -0.5]
        self.mock_high = [1.0, 1.0, 0.5]
        self.mock_augmentation_probability = 0.5
        self.mock_use_uniform_noise = False

    def test_scale_augmentor(self) -> None:
        """
        Test scale_augmentor function.
        """
        augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'linear', self.milestones)
        augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'linear', self.milestones)
        mock_augmentor = Mock(AbstractAugmentor)
        mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
        mock_augmentor._augment_prob = self.mock_augmentation_probability
        mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
        mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
        mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
        augmentation_attribute_scheduler._scale_augmentor(mock_augmentor, self.cur_step, self.total_steps)
        augmentation_probability_scheduler._scale_augmentor(mock_augmentor, self.cur_step, self.total_steps)
        expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
        expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
        expected_augmentation_probability = self.max_augment_prob
        self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

    def test_handle_scheduling(self) -> None:
        """
        Test _handle_scheduling function to ensure scaling doesn't happen on non milestone steps.
        """
        augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'milestones', self.milestones)
        augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'milestones', self.milestones)
        mock_augmentor = Mock(AbstractAugmentor)
        mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
        mock_augmentor._augment_prob = self.mock_augmentation_probability
        mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
        mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
        mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
        mock_trainer = Mock(pl.Trainer)
        mock_trainer.datamodule = Mock()
        mock_trainer.datamodule._train_set._augmentors = [mock_augmentor]
        non_milestone_cur_step = 0.1
        pct_progress = round(non_milestone_cur_step / (self.total_steps * self.pct_time_increasing), 2)
        augmentation_attribute_scheduler._handle_scheduling(mock_trainer, non_milestone_cur_step, self.total_steps, pct_progress)
        augmentation_probability_scheduler._handle_scheduling(mock_trainer, non_milestone_cur_step, self.total_steps, pct_progress)
        self.assertEqual(mock_augmentor._augment_prob, self.initial_augment_prob)
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, self.mock_mean))
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, self.mock_std))
        pct_progress = round(self.cur_step / (self.total_steps * self.pct_time_increasing), 2)
        augmentation_attribute_scheduler._handle_scheduling(mock_trainer, self.cur_step, self.total_steps, pct_progress)
        augmentation_probability_scheduler._handle_scheduling(mock_trainer, self.cur_step, self.total_steps, pct_progress)
        expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
        expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
        expected_augmentation_probability = self.max_augment_prob
        self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

    def test_on_batch_end_milestones(self) -> None:
        """
        Test on_batch_end function to ensure scaling doesn't happen after scheduling is completed using milestones strategy.
        """
        augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'milestones', self.milestones)
        augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'milestones', self.milestones)
        mock_augmentor = Mock(AbstractAugmentor)
        mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
        mock_augmentor._augment_prob = self.mock_augmentation_probability
        mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
        mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
        mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
        mock_trainer = Mock(pl.Trainer)
        mock_trainer.max_epochs = 2
        mock_trainer.num_training_batches = 1
        mock_trainer.datamodule = Mock()
        mock_trainer.datamodule._train_set._augmentors = [mock_augmentor]
        mock_module = Mock(pl.LightningModule)
        mock_trainer.global_step = 0
        augmentation_attribute_scheduler.on_batch_end(mock_trainer, mock_module)
        augmentation_probability_scheduler.on_batch_end(mock_trainer, mock_module)
        expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
        expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
        expected_augmentation_probability = self.max_augment_prob
        self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))
        mock_trainer.global_step = 1
        augmentation_attribute_scheduler.on_batch_end(mock_trainer, mock_module)
        augmentation_probability_scheduler.on_batch_end(mock_trainer, mock_module)
        self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
        self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

def test_scale_augmentor(self) -> None:
    """
        Test scale_augmentor function.
        """
    augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'linear', self.milestones)
    augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'linear', self.milestones)
    mock_augmentor = Mock(AbstractAugmentor)
    mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
    mock_augmentor._augment_prob = self.mock_augmentation_probability
    mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
    mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
    mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
    augmentation_attribute_scheduler._scale_augmentor(mock_augmentor, self.cur_step, self.total_steps)
    augmentation_probability_scheduler._scale_augmentor(mock_augmentor, self.cur_step, self.total_steps)
    expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
    expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
    expected_augmentation_probability = self.max_augment_prob
    self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

def test_handle_scheduling(self) -> None:
    """
        Test _handle_scheduling function to ensure scaling doesn't happen on non milestone steps.
        """
    augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'milestones', self.milestones)
    augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'milestones', self.milestones)
    mock_augmentor = Mock(AbstractAugmentor)
    mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
    mock_augmentor._augment_prob = self.mock_augmentation_probability
    mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
    mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
    mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
    mock_trainer = Mock(pl.Trainer)
    mock_trainer.datamodule = Mock()
    mock_trainer.datamodule._train_set._augmentors = [mock_augmentor]
    non_milestone_cur_step = 0.1
    pct_progress = round(non_milestone_cur_step / (self.total_steps * self.pct_time_increasing), 2)
    augmentation_attribute_scheduler._handle_scheduling(mock_trainer, non_milestone_cur_step, self.total_steps, pct_progress)
    augmentation_probability_scheduler._handle_scheduling(mock_trainer, non_milestone_cur_step, self.total_steps, pct_progress)
    self.assertEqual(mock_augmentor._augment_prob, self.initial_augment_prob)
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, self.mock_mean))
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, self.mock_std))
    pct_progress = round(self.cur_step / (self.total_steps * self.pct_time_increasing), 2)
    augmentation_attribute_scheduler._handle_scheduling(mock_trainer, self.cur_step, self.total_steps, pct_progress)
    augmentation_probability_scheduler._handle_scheduling(mock_trainer, self.cur_step, self.total_steps, pct_progress)
    expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
    expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
    expected_augmentation_probability = self.max_augment_prob
    self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

def test_on_batch_end_milestones(self) -> None:
    """
        Test on_batch_end function to ensure scaling doesn't happen after scheduling is completed using milestones strategy.
        """
    augmentation_attribute_scheduler = StepwiseAugmentationAttributeScheduler(self.max_aug_attribute_pct_increase, self.pct_time_increasing, 'milestones', self.milestones)
    augmentation_probability_scheduler = StepwiseAugmentationProbabilityScheduler(self.max_augment_prob, self.pct_time_increasing, 'milestones', self.milestones)
    mock_augmentor = Mock(AbstractAugmentor)
    mock_augmentor._random_offset_generator = GaussianNoise(self.mock_mean, self.mock_std)
    mock_augmentor._augment_prob = self.mock_augmentation_probability
    mock_augmentor.__name__ = Mock(return_value='mock_augmentor')
    mock_augmentor.augmentation_probability = ParameterToScale(param=self.mock_augmentation_probability, param_name='_augment_prob', scaling_direction=ScalingDirection.MAX)
    mock_augmentor.get_schedulable_attributes = mock_augmentor._random_offset_generator.get_schedulable_attributes()
    mock_trainer = Mock(pl.Trainer)
    mock_trainer.max_epochs = 2
    mock_trainer.num_training_batches = 1
    mock_trainer.datamodule = Mock()
    mock_trainer.datamodule._train_set._augmentors = [mock_augmentor]
    mock_module = Mock(pl.LightningModule)
    mock_trainer.global_step = 0
    augmentation_attribute_scheduler.on_batch_end(mock_trainer, mock_module)
    augmentation_probability_scheduler.on_batch_end(mock_trainer, mock_module)
    expected_mean = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_mean)
    expected_std = (1 + self.max_aug_attribute_pct_increase) * np.asarray(self.mock_std)
    expected_augmentation_probability = self.max_augment_prob
    self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))
    mock_trainer.global_step = 1
    augmentation_attribute_scheduler.on_batch_end(mock_trainer, mock_module)
    augmentation_probability_scheduler.on_batch_end(mock_trainer, mock_module)
    self.assertEqual(mock_augmentor._augment_prob, expected_augmentation_probability)
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.mean, expected_mean))
    self.assertTrue(np.allclose(mock_augmentor._random_offset_generator.std, expected_std))

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

def test_periodic_callback(self) -> None:
    """Tests that _periodic_callback is registered correctly to the bokeh Document."""
    with patch.object(SimulationTile, '_periodic_callback', autospec=True) as mock_periodic_callback:
        SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertEqual(mock_periodic_callback.call_count, 1)

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

class TestScenarioTab(SkeletonTestTab):
    """Test nuboard scenario tab functionality."""

    def setUp(self) -> None:
        """Set up a scenario tab."""
        super().setUp()
        vehicle_parameters = get_pacifica_parameters()
        scenario_builder = MockAbstractScenarioBuilder()
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
        self.scenario_tab = ScenarioTab(experiment_file_data=self.experiment_file_data, scenario_builder=scenario_builder, vehicle_parameters=vehicle_parameters, doc=self.doc)

    def test_update_scenario(self) -> None:
        """Test functions corresponding to selection changes work as expected."""
        self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change function."""
        new_experiment_file_data = ExperimentFileData(file_paths=[])
        self.scenario_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])
        self.assertEqual(self.scenario_tab._scalar_scenario_type_select.value, '')
        self.assertEqual(self.scenario_tab._scalar_scenario_type_select.options, [''])
        self.assertEqual(self.scenario_tab._scalar_scenario_name_select.value, '')
        self.assertEqual(self.scenario_tab._scalar_scenario_name_select.options, [])

    def test_update_scenario_legend(self) -> None:
        """Test functions corresponding to legend selection changes work as expected."""
        self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._traj_checkbox_group.active = [0]
        self.scenario_tab._map_checkbox_group.active = [0, 1, 2]
        self.scenario_tab._object_checkbox_group.active = [3, 4]

    def test_modal_button_on_click(self) -> None:
        """Test modal button on click function."""
        self.scenario_tab._experiment_file_active_index = [0]
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._scenario_modal_query_button_on_click()
        self.assertEqual(self.scenario_tab.planner_checkbox_group.labels, ['SimplePlanner'])
        self.assertIn('ego_acceleration_statistics', self.scenario_tab._time_series_data)

    def test_planner_button_on_click(self) -> None:
        """Test checkbox button in planner."""
        self.scenario_tab._experiment_file_active_index = [0]
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._scenario_modal_query_button_on_click()
        self.scenario_tab.planner_checkbox_group.active = []
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
        self.scenario_tab.planner_checkbox_group.active = [0]
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
        with self.assertRaises(IndexError):
            self.scenario_tab.planner_checkbox_group.active = [1]

def test_modal_button_on_click(self) -> None:
    """Test modal button on click function."""
    self.scenario_tab._experiment_file_active_index = [0]
    self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
    self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
    self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
    self.scenario_tab._scenario_modal_query_button_on_click()
    self.assertEqual(self.scenario_tab.planner_checkbox_group.labels, ['SimplePlanner'])
    self.assertIn('ego_acceleration_statistics', self.scenario_tab._time_series_data)

def test_planner_button_on_click(self) -> None:
    """Test checkbox button in planner."""
    self.scenario_tab._experiment_file_active_index = [0]
    self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
    self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
    self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
    self.scenario_tab._scenario_modal_query_button_on_click()
    self.scenario_tab.planner_checkbox_group.active = []
    self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
    self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
    self.scenario_tab.planner_checkbox_group.active = [0]
    self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
    self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
    with self.assertRaises(IndexError):
        self.scenario_tab.planner_checkbox_group.active = [1]

class TestHistogramTab(SkeletonTestTab):
    """Test nuboard histogram tab functionality."""

    def setUp(self) -> None:
        """Set up a histogram tab."""
        super().setUp()
        self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)

    def test_update_histograms(self) -> None:
        """Test update_histograms works as expected when we update choices."""
        self.histogram_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
        self.histogram_tab._scenario_type_multi_choice.value = ['Test']
        self.histogram_tab._metric_name_multi_choice.value = ['ego_acceleration_statistics']
        self.histogram_tab._setting_modal_query_button_on_click()
        self.assertIn('ego_acceleration_statistics', self.histogram_tab._aggregated_data)
        self.assertEqual(len(self.histogram_tab.histogram_plots.children), 1)

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change function."""
        new_experiment_file_data = ExperimentFileData(file_paths=[])
        self.histogram_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])
        self.assertEqual(self.histogram_tab._scenario_type_multi_choice.value, [])
        self.assertEqual(self.histogram_tab._scenario_type_multi_choice.options, ['all'])
        self.assertEqual(self.histogram_tab._metric_name_multi_choice.value, [])
        self.assertEqual(self.histogram_tab._metric_name_multi_choice.options, [])

def test_update_histograms(self) -> None:
    """Test update_histograms works as expected when we update choices."""
    self.histogram_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
    self.histogram_tab._scenario_type_multi_choice.value = ['Test']
    self.histogram_tab._metric_name_multi_choice.value = ['ego_acceleration_statistics']
    self.histogram_tab._setting_modal_query_button_on_click()
    self.assertIn('ego_acceleration_statistics', self.histogram_tab._aggregated_data)
    self.assertEqual(len(self.histogram_tab.histogram_plots.children), 1)

@dataclass
class CornersGraphEdgeMapObject:
    """class containing list of lane/lane connectors of each corner of ego's orientedbox."""
    front_left_map_objs: List[GraphEdgeMapObject]
    rear_left_map_objs: List[GraphEdgeMapObject]
    rear_right_map_objs: List[GraphEdgeMapObject]
    front_right_map_objs: List[GraphEdgeMapObject]

    def __iter__(self) -> Iterable[List[GraphEdgeMapObject]]:
        """Returns an iterable tuple of the class attributes
        :return: iterator of class attribute tuples
        """
        return iter((self.front_left_map_objs, self.rear_left_map_objs, self.rear_right_map_objs, self.front_right_map_objs))

def __iter__(self) -> Iterable[List[GraphEdgeMapObject]]:
    """Returns an iterable tuple of the class attributes
        :return: iterator of class attribute tuples
        """
    return iter((self.front_left_map_objs, self.rear_left_map_objs, self.rear_right_map_objs, self.front_right_map_objs))

class TestWeightedAverageMetricAggregator(unittest.TestCase):
    """Run weighted average metric aggregator unit tests."""

    def setUp(self) -> None:
        """Set up dummy data and folders."""
        self.metric_scores = [[1, 0.5, 0.8], [0.1, 0.2]]
        dummy_dataframes = [pandas.DataFrame({'scenario_name': ['test_1', 'test_2', 'test_3'], 'log_name': ['dummy', 'dummy', 'dummy_2'], 'scenario_type': ['unknown', 'ego_stop_at_stop_line', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner', 'dummy_planner'], 'metric_score': self.metric_scores[0], 'metric_score_unit': 'float'}), pandas.DataFrame({'scenario_name': ['test_1', 'test_3'], 'log_name': ['dummy', 'dummy_3'], 'scenario_type': ['unknown', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner'], 'metric_score': self.metric_scores[1], 'metric_score_unit': 'float'})]
        metric_statistic_names = ['dummy_metric', 'second_dummy_metric']
        self.metric_statistic_dataframes = []
        for dummy_dataframe, metric_statistic_name in zip(dummy_dataframes, metric_statistic_names):
            self.metric_statistic_dataframes.append(MetricStatisticsDataFrame(metric_statistic_name=metric_statistic_name, metric_statistics_dataframe=dummy_dataframe))
        self.tmpdir = tempfile.TemporaryDirectory()
        self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=Path(self.tmpdir.name), multiple_metrics=[])

    def tearDown(self) -> None:
        """Clean up when unittests end."""
        self.tmpdir.cleanup()

    def test_name(self) -> None:
        """Test if name is expected."""
        self.assertEqual('weighted_average_metric_aggregator', self.weighted_average_metric_aggregator.name)

    def test_final_metric_score(self) -> None:
        """Test if final metric score is expected."""
        self.assertEqual(None, self.weighted_average_metric_aggregator.final_metric_score)

    def test_aggregated_metric_dataframe(self) -> None:
        """Test if aggregated metric dataframe is expected."""
        self.assertEqual(None, self.weighted_average_metric_aggregator.aggregated_metric_dataframe)

    def test_aggregation(self) -> None:
        """Test running the aggregation."""
        metric_dataframes = {metric_statistic_dataframe.metric_statistic_name: metric_statistic_dataframe for metric_statistic_dataframe in self.metric_statistic_dataframes}
        self.weighted_average_metric_aggregator(metric_dataframes=metric_dataframes)
        parquet_file = Path(self.tmpdir.name) / 'test_weighted_average_metric_aggregator.parquet'
        self.assertTrue(parquet_file.exists())
        self.weighted_average_metric_aggregator.read_parquet()
        aggregated_metric_dataframe = self.weighted_average_metric_aggregator.aggregated_metric_dataframe
        self.assertIsNot(aggregated_metric_dataframe, None)
        self.assertTrue(len(aggregated_metric_dataframe))
        self.assertTrue(np.isnan(aggregated_metric_dataframe['second_dummy_metric'][0]))
        expected_planners = ['dummy_planner', 'simple_planner']
        self.assertEqual(expected_planners, sorted(aggregated_metric_dataframe['planner_name'].unique(), reverse=False))
        self.assertEqual(['weighted_average'], list(aggregated_metric_dataframe['aggregator_type'].unique()))
        expected_values = {'dummy_planner': {'dummy_metric': [0.5, 0.8, 0.5, 0.8, 0.65], 'second_dummy_metric': [-1.0, 0.2, -1.0, 0.2, 0.1], 'score': [0.5, 0.4, 0.5, 0.4, 0.45]}, 'simple_planner': {'dummy_metric': [1.0, 1.0, 1.0], 'second_dummy_metric': [0.1, 0.1, 0.1], 'score': [0.4, 0.4, 0.4]}}
        for planner in expected_planners:
            planner_metric = aggregated_metric_dataframe[aggregated_metric_dataframe['planner_name'].isin([planner])]
            for name, expected_value in expected_values[planner].items():
                planner_values = np.round(planner_metric[name].fillna(-1.0).to_numpy(), 2).tolist()
                self.assertEqual(expected_value, planner_values)

    def test_parquet(self) -> None:
        """Test property."""
        self.assertEqual(self.weighted_average_metric_aggregator.parquet_file, self.weighted_average_metric_aggregator._parquet_file)

def test_name(self) -> None:
    """Test if name is expected."""
    self.assertEqual('weighted_average_metric_aggregator', self.weighted_average_metric_aggregator.name)

def test_final_metric_score(self) -> None:
    """Test if final metric score is expected."""
    self.assertEqual(None, self.weighted_average_metric_aggregator.final_metric_score)

def test_aggregated_metric_dataframe(self) -> None:
    """Test if aggregated metric dataframe is expected."""
    self.assertEqual(None, self.weighted_average_metric_aggregator.aggregated_metric_dataframe)

def test_parquet(self) -> None:
    """Test property."""
    self.assertEqual(self.weighted_average_metric_aggregator.parquet_file, self.weighted_average_metric_aggregator._parquet_file)

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Execute submission planner which will listen to the simulation and compute trajectory at request
    :param cfg: Configuration that is used to run the experiment.
    """
    pl.seed_everything(cfg.seed, workers=True)
    submission_planner = SubmissionPlanner(planner_config=cfg.planner)
    submission_planner.serve()

def list_subdirs_filtered(root_dir: Path, regex_pattern: re.Pattern[str]) -> List[str]:
    """
    Lists the path of files present in a directory. Results are filtered by ending pattern.
    :param root_dir: The path to start the search.
    :param regex_pattern: Regex based Pattern for which paths to keep.
    :return: List of paths under root_dir which wnd with path_end_filter.
    """
    paths = [str(path) for path in root_dir.rglob('**/*') if regex_pattern.search(str(path))]
    return paths

class TestUtilsCheckpoint(unittest.TestCase):
    """Test checkpoint utils methods."""

    def setUp(self) -> None:
        """Setup test attributes."""
        self.group = Path('exp')
        self.experiment_uid = Path('2023.01.01.00.00.00')
        self.experiment = Path('experiment_name/job_name') / self.experiment_uid

    @patch.object(Path, 'exists', autospec=True, return_value=False)
    def test_find_last_checkpoint_in_dir_dir_unavailable(self, path_exists_mock: Mock) -> None:
        """Test 'find_last_checkpoint_in_dir' method when directory does not exist."""
        group_dir = self.group / self.experiment.parent
        result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
        self.assertIsNone(result)

    @patch.object(Path, 'exists', autospec=True, return_value=True)
    @patch.object(Path, 'iterdir', autospec=True, return_value=[Path('epoch=0.ckpt'), Path('epoch=1.ckpt')])
    def test_find_last_checkpoint_in_dir(self, path_iterdir_mock: Mock, path_exists_mock: Mock) -> None:
        """Test 'find_last_checkpoint_in_dir' method under typical use case."""
        group_dir = self.group / self.experiment.parent
        result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
        expected = Path('exp/experiment_name/job_name/2023.01.01.00.00.00/checkpoints/epoch=1.ckpt')
        self.assertEqual(result, expected)

    @patch.object(Path, 'iterdir', autospec=True, return_value=[Path('2023.01.01.00.00.00'), Path('2023.01.01.00.00.01'), Path('2023.01.01.00.00.02')])
    @patch(f'{PATCH_PREFIX}.find_last_checkpoint_in_dir', autospec=True)
    def test_extract_last_checkpoint_from_experiment(self, find_last_checkpoint_in_dir_mock: Mock, path_iterdir_mock: Mock) -> None:
        """Test extract_last_checkpoint_from_experiment method."""
        output_dir = self.group / self.experiment
        date_format = '%Y.%m.%d.%H.%M.%S'
        _ = extract_last_checkpoint_from_experiment(output_dir, date_format)
        calls = [call(Path('exp/experiment_name/job_name'), Path('2023.01.01.00.00.02'))]
        find_last_checkpoint_in_dir_mock.assert_has_calls(calls)

@patch.object(Path, 'exists', autospec=True, return_value=False)
def test_find_last_checkpoint_in_dir_dir_unavailable(self, path_exists_mock: Mock) -> None:
    """Test 'find_last_checkpoint_in_dir' method when directory does not exist."""
    group_dir = self.group / self.experiment.parent
    result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
    self.assertIsNone(result)

@patch.object(Path, 'exists', autospec=True, return_value=True)
@patch.object(Path, 'iterdir', autospec=True, return_value=[Path('epoch=0.ckpt'), Path('epoch=1.ckpt')])
def test_find_last_checkpoint_in_dir(self, path_iterdir_mock: Mock, path_exists_mock: Mock) -> None:
    """Test 'find_last_checkpoint_in_dir' method under typical use case."""
    group_dir = self.group / self.experiment.parent
    result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
    expected = Path('exp/experiment_name/job_name/2023.01.01.00.00.00/checkpoints/epoch=1.ckpt')
    self.assertEqual(result, expected)

@patch.object(Path, 'iterdir', autospec=True, return_value=[Path('2023.01.01.00.00.00'), Path('2023.01.01.00.00.01'), Path('2023.01.01.00.00.02')])
@patch(f'{PATCH_PREFIX}.find_last_checkpoint_in_dir', autospec=True)
def test_extract_last_checkpoint_from_experiment(self, find_last_checkpoint_in_dir_mock: Mock, path_iterdir_mock: Mock) -> None:
    """Test extract_last_checkpoint_from_experiment method."""
    output_dir = self.group / self.experiment
    date_format = '%Y.%m.%d.%H.%M.%S'
    _ = extract_last_checkpoint_from_experiment(output_dir, date_format)
    calls = [call(Path('exp/experiment_name/job_name'), Path('2023.01.01.00.00.02'))]
    find_last_checkpoint_in_dir_mock.assert_has_calls(calls)

class TestTqdmLoggingHandler(unittest.TestCase):
    """Test TqdmLoggingHandler class."""

    def test_emit_normal(self) -> None:
        """Test emit function when no errors."""
        tlh = TqdmLoggingHandler()
        log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'A normal logging message.', args=None, exc_info=None)
        self.assertIsNone(tlh.emit(log_record))

    def test_emit_keyboard_interrupt(self) -> None:
        """Test emit when KeyboardInterrupt exception is raised."""
        tlh = TqdmLoggingHandler()
        log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'An interrupted logging message.', args=None, exc_info=None)
        tlh.flush = Mock()
        tlh.flush.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            tlh.emit(log_record)

    def test_emit_other_exception(self) -> None:
        """Test emit when an unexpected error is raised."""
        tlh = TqdmLoggingHandler()
        log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'An error-handled logging message.', args=None, exc_info=None)
        tlh.flush = Mock()
        tlh.flush.side_effect = MemoryError
        tlh.handleError = Mock()
        tlh.emit(log_record)
        tlh.handleError.assert_called_once_with(log_record)

def test_emit_normal(self) -> None:
    """Test emit function when no errors."""
    tlh = TqdmLoggingHandler()
    log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'A normal logging message.', args=None, exc_info=None)
    self.assertIsNone(tlh.emit(log_record))

def test_emit_keyboard_interrupt(self) -> None:
    """Test emit when KeyboardInterrupt exception is raised."""
    tlh = TqdmLoggingHandler()
    log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'An interrupted logging message.', args=None, exc_info=None)
    tlh.flush = Mock()
    tlh.flush.side_effect = KeyboardInterrupt
    with self.assertRaises(KeyboardInterrupt):
        tlh.emit(log_record)

def test_emit_other_exception(self) -> None:
    """Test emit when an unexpected error is raised."""
    tlh = TqdmLoggingHandler()
    log_record = logging.LogRecord('', logging.NOTSET, '', 0, 'An error-handled logging message.', args=None, exc_info=None)
    tlh.flush = Mock()
    tlh.flush.side_effect = MemoryError
    tlh.handleError = Mock()
    tlh.emit(log_record)
    tlh.handleError.assert_called_once_with(log_record)

class TestLogHandlerConfig(unittest.TestCase):
    """Test LogHandlerConfig class."""

    @patch('os.makedirs')
    def test_init(self, mock_makedirs) -> None:
        """Test class initialization."""
        unique_path = str(uuid4())
        unique_dir = os.path.join(unique_path, '')
        handler = LogHandlerConfig('LEVEL', unique_dir, 'REGEX')
        self.assertEqual(handler.level, 'LEVEL')
        self.assertEqual(handler.path, unique_dir)
        self.assertEqual(handler.filter_regexp, 'REGEX')
        mock_makedirs.assert_called_once_with(unique_path)

@patch('os.makedirs')
def test_init(self, mock_makedirs) -> None:
    """Test class initialization."""
    unique_path = str(uuid4())
    unique_dir = os.path.join(unique_path, '')
    handler = LogHandlerConfig('LEVEL', unique_dir, 'REGEX')
    self.assertEqual(handler.level, 'LEVEL')
    self.assertEqual(handler.path, unique_dir)
    self.assertEqual(handler.filter_regexp, 'REGEX')
    mock_makedirs.assert_called_once_with(unique_path)

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

class ScenarioMapping:
    """
    Structure that maps each scenario type to instructions used in extracting it.
    """

    def __init__(self, scenario_map: Dict[str, Union[Tuple[float, float, float], Tuple[float, float]]], subsample_ratio_override: Optional[float]) -> None:
        """
        Initializes the scenario mapping class.
        :param scenario_map: Dictionary with scenario name/type as keys and
                             tuples of (scenario duration, extraction offset, subsample ratio) as values.
        :subsample_ratio_override: The override for the subsample ratio if not provided.
        """
        self.mapping: Dict[str, ScenarioExtractionInfo] = {}
        self.subsample_ratio_override = subsample_ratio_override if subsample_ratio_override is not None else DEFAULT_SUBSAMPLE_RATIO
        for name in scenario_map:
            this_ratio: float = scenario_map[name][2] if len(scenario_map[name]) == 3 else self.subsample_ratio_override
            self.mapping[name] = ScenarioExtractionInfo(scenario_name=name, scenario_duration=scenario_map[name][0], extraction_offset=scenario_map[name][1], subsample_ratio=this_ratio)

    def get_extraction_info(self, scenario_type: str) -> Optional[ScenarioExtractionInfo]:
        """
        Accesses the scenario mapping using a query scenario type.
        If the scenario type is not found, a default extraction info object is returned.
        :param scenario_type: Scenario type to query for.
        :return: Scenario extraction information for the queried scenario type.
        """
        return self.mapping[scenario_type] if scenario_type in self.mapping else ScenarioExtractionInfo(subsample_ratio=self.subsample_ratio_override)

def __init__(self, scenario_map: Dict[str, Union[Tuple[float, float, float], Tuple[float, float]]], subsample_ratio_override: Optional[float]) -> None:
    """
        Initializes the scenario mapping class.
        :param scenario_map: Dictionary with scenario name/type as keys and
                             tuples of (scenario duration, extraction offset, subsample ratio) as values.
        :subsample_ratio_override: The override for the subsample ratio if not provided.
        """
    self.mapping: Dict[str, ScenarioExtractionInfo] = {}
    self.subsample_ratio_override = subsample_ratio_override if subsample_ratio_override is not None else DEFAULT_SUBSAMPLE_RATIO
    for name in scenario_map:
        this_ratio: float = scenario_map[name][2] if len(scenario_map[name]) == 3 else self.subsample_ratio_override
        self.mapping[name] = ScenarioExtractionInfo(scenario_name=name, scenario_duration=scenario_map[name][0], extraction_offset=scenario_map[name][1], subsample_ratio=this_ratio)

def get_extraction_info(self, scenario_type: str) -> Optional[ScenarioExtractionInfo]:
    """
        Accesses the scenario mapping using a query scenario type.
        If the scenario type is not found, a default extraction info object is returned.
        :param scenario_type: Scenario type to query for.
        :return: Scenario extraction information for the queried scenario type.
        """
    return self.mapping[scenario_type] if scenario_type in self.mapping else ScenarioExtractionInfo(subsample_ratio=self.subsample_ratio_override)

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

def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
    """Inherited, see superclass."""
    channels = [LidarChannel.MERGED_PC] if channels is None else channels
    lidar_pc = next(get_sensor_data_from_sensor_data_tokens_from_db(self._log_file, get_lidarpc_sensor_data(), LidarPc, [self._lidarpc_tokens[iteration]]))
    return self._get_sensor_data_from_lidar_pc(cast(LidarPc, lidar_pc), channels)

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

def get_scenarios_from_db_file(params: GetScenariosFromDbFileParams) -> ScenarioDict:
    """
    Gets all of the scenarios present in a single sqlite db file that match the provided filter parameters.
    :param params: The filter parameters to use.
    :return: A ScenarioDict containing the relevant scenarios.
    """
    local_log_file_absolute_path = download_file_if_necessary(params.data_root, params.log_file_absolute_path, params.verbose)
    scenario_dict: ScenarioDict = {}
    for row in get_scenarios_from_db(local_log_file_absolute_path, params.filter_tokens, params.filter_types, params.filter_map_names, not params.remove_invalid_goals, params.include_cameras):
        scenario_type = row['scenario_type']
        if scenario_type is None:
            scenario_type = DEFAULT_SCENARIO_NAME
        if scenario_type not in scenario_dict:
            scenario_dict[scenario_type] = []
        extraction_info = None if params.expand_scenarios else params.scenario_mapping.get_extraction_info(scenario_type)
        scenario_dict[scenario_type].append(NuPlanScenario(data_root=params.data_root, log_file_load_path=params.log_file_absolute_path, initial_lidar_token=row['token'].hex(), initial_lidar_timestamp=row['timestamp'], scenario_type=scenario_type, map_root=params.map_root, map_version=params.map_version, map_name=row['map_name'], scenario_extraction_info=extraction_info, ego_vehicle_parameters=params.vehicle_parameters, sensor_root=params.sensor_root))
    return scenario_dict

@lru_cache(maxsize=1)
def get_test_nuplan_scenario(use_multi_sample: bool=False, lidar_pc_index: Optional[int]=None, sensor_root: Optional[str]=None) -> NuPlanScenario:
    """
    Retrieve a sample scenario from the db.
    :param use_multi_sample: Whether to extract multiple temporal samples in the scenario.
    :param lidar_pc_index: The initial lidarpc_token for the sceanrio. If None, then a default example (corresponding to DEFAULT_LIDARPC_INDEX) will be used.
    :param sensor_root: The directory for which the sensor data should be saved to.
    :return: A sample db scenario.
    """
    load_path = NUPLAN_DB_FILES[4]
    lidar_pc_index = DEFAULT_LIDARPC_INDEX if lidar_pc_index is None else lidar_pc_index
    token = get_sensor_token_by_index_from_db(load_path, get_lidarpc_sensor_data(), lidar_pc_index)
    timestamp = get_sensor_data_token_timestamp_from_db(load_path, get_lidarpc_sensor_data(), token)
    map_name = get_sensor_token_map_name_from_db(load_path, get_lidarpc_sensor_data(), token)
    if timestamp is None or map_name is None:
        raise ValueError(f'Token {token} not found in log.')
    scenario = NuPlanScenario(data_root=NUPLAN_DATA_ROOT, log_file_load_path=load_path, initial_lidar_token=token, initial_lidar_timestamp=timestamp, scenario_type=DEFAULT_SCENARIO_NAME, map_root=NUPLAN_MAPS_ROOT, map_version=NUPLAN_MAP_VERSION, map_name=map_name, scenario_extraction_info=ScenarioExtractionInfo() if use_multi_sample else None, ego_vehicle_parameters=get_pacifica_parameters(), sensor_root=NUPLAN_SENSOR_ROOT if sensor_root is None else sensor_root)
    return scenario

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

class TestNuPlanScenario(unittest.TestCase):
    """
    Tests scenario for NuPlan
    """

    def _make_test_scenario(self) -> NuPlanScenario:
        """
        Creates a sample scenario to use for testing.
        """
        return NuPlanScenario(data_root='data_root/', log_file_load_path='data_root/log_name.db', initial_lidar_token=int_to_str_token(1234), initial_lidar_timestamp=2345, scenario_type='scenario_type', map_root='map_root', map_version='map_version', map_name='map_name', scenario_extraction_info=ScenarioExtractionInfo(scenario_name='scenario_name', scenario_duration=20, extraction_offset=1, subsample_ratio=0.5), ego_vehicle_parameters=get_pacifica_parameters(), sensor_root='sensor_root')

    def _get_sampled_sensor_tokens_in_time_window_patch(self, expected_log_file: str, expected_sensor_data_source: SensorDataSource, expected_start_timestamp: int, expected_end_timestamp: int, expected_subsample_step: int) -> Callable[[str, SensorDataSource, int, int, int], Generator[str, None, None]]:
        """
        Creates a patch for the get_sampled_lidarpc_tokens_in_time_window function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_start_timestamp: The expected start timestamp with which the function is expected to be called.
        :param expected_end_timestamp: The expected end timestamp with which the function is expected to be called.
        :param expected_subsample_step: The expected subsample step with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_sensor_data_source: SensorDataSource, actual_start_timestamp: int, actual_end_timestamp: int, actual_subsample_step: int) -> Generator[str, None, None]:
            """
            The patch function for get_sampled_lidarpc_tokens_in_time_window.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_start_timestamp, actual_start_timestamp)
            self.assertEqual(expected_end_timestamp, actual_end_timestamp)
            self.assertEqual(expected_subsample_step, actual_subsample_step)
            num_tokens = int((expected_end_timestamp - expected_start_timestamp) / (expected_subsample_step * 1000000.0))
            for token in range(num_tokens):
                yield int_to_str_token(token)
        return fxn

    def _get_download_file_if_necessary_patch(self, expected_data_root: str, expected_log_file_load_path: str) -> Callable[[str, str], str]:
        """
        Creates a patch for the download_file_if_necessary function that validates the arguments.
        :param expected_data_root: The data_root with which the function is expected to be called.
        :param expected_log_file_load_path: The log_file_load_path with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_data_root: str, actual_log_file_load_path: str) -> str:
            """
            The generated patch function.
            """
            self.assertEqual(expected_data_root, actual_data_root)
            self.assertEqual(expected_log_file_load_path, actual_log_file_load_path)
            return actual_log_file_load_path
        return fxn

    def _get_sensor_data_from_sensor_data_tokens_from_db_patch(self, expected_log_file: str, expected_sensor_data_source: SensorDataSource, expected_sensor_class: Type[SensorDataTableRow], expected_tokens: List[str]) -> Callable[[str, SensorDataSource, Type[SensorDataTableRow], List[str]], Generator[SensorDataTableRow, None, None]]:
        """
        Creates a patch for the get_images_from_lidar_tokens_patch function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_sensor_data_source: The sensor source with which the function is expected to be called.
        :param expected_sensor_class: The sensor class with which the function is expected to be called.
        :param expected_tokens: The tokens with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_sensor_data_source: SensorDataSource, actual_sensor_class: Type[SensorDataTableRow], actual_tokens: List[str]) -> Generator[SensorDataTableRow, None, None]:
            """
            The patch function for get_sensor_data_from_sensor_data_tokens_from_db.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_sensor_class, actual_sensor_class)
            self.assertEqual(expected_tokens, actual_tokens)
            lidar_token = actual_tokens[0]
            if expected_sensor_class == LidarPc:
                yield LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token))
            elif expected_sensor_class == ImageDBRow.Image:
                camera_token = str_token_to_int(lidar_token) + CAMERA_OFFSET
                yield ImageDBRow.Image(token=int_to_str_token(camera_token), next_token=int_to_str_token(camera_token), prev_token=int_to_str_token(camera_token), ego_pose_token=int_to_str_token(camera_token), camera_token=int_to_str_token(camera_token), filename_jpg=f'image_{camera_token}', timestamp=camera_token, channel=CameraChannel.CAM_R0.value)
            else:
                self.fail(f'Unexpected type: {expected_sensor_class}.')
        return fxn

    def _load_point_cloud_patch(self, expected_lidar_pc: LidarPc, expected_local_store: LocalStore, expected_s3_store: S3Store) -> Callable[[LidarPc, LocalStore, S3Store], LidarPointCloud]:
        """
        Creates a patch for the _load_point_cloud function that validates the arguments.
        :param expected_lidar_pc: The lidar pc with which the function is expected to be called.
        :param expected_local_store: The LocalStore with which the function is expected to be called.
        :param expected_s3_store: The S3Store with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_lidar_pc: LidarPc, actual_local_store: LocalStore, actual_s3_store: S3Store) -> LidarPointCloud:
            """
            The patch function for load_point_cloud.
            """
            self.assertEqual(expected_lidar_pc, actual_lidar_pc)
            self.assertEqual(expected_local_store, actual_local_store)
            self.assertEqual(expected_s3_store, actual_s3_store)
            return LidarPointCloud(np.eye(3))
        return fxn

    def _load_image_patch(self, expected_local_store: LocalStore, expected_s3_store: S3Store) -> Callable[[ImageDBRow.Image, LocalStore, S3Store], Image]:
        """
        Creates a patch for the _load_image_patch function and validates that argument is an Image object.
        :param expected_local_store: The LocalStore with which the function is expected to be called.
        :param expected_s3_store: The S3Store with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_image: ImageDBRow.Image, actual_local_store: LocalStore, actual_s3_store: S3Store) -> Image:
            """
            The patch function for load_image.
            """
            self.assertEqual(expected_local_store, actual_local_store)
            self.assertEqual(expected_s3_store, actual_s3_store)
            self.assertTrue(isinstance(actual_image, ImageDBRow.Image))
            return Image(PilImg.new('RGB', (500, 500)))
        return fxn

    def _get_images_from_lidar_tokens_patch(self, expected_log_file: str, expected_tokens: List[str], expected_channels: List[str], expected_lookahead_window_us: int, expected_lookback_window_us: int) -> Callable[[str, List[str], List[str], int, int], Generator[ImageDBRow.Image, None, None]]:
        """
        Creates a patch for the get_images_from_lidar_tokens_patch function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_tokens: The expected tokens with which the function is expected to be called.
        :param expected_channels: The expected channels with which the function is expected to be called.
        :param expected_lookahead_window_us: The expected lookahead window with which the function is expected to be called.
        :param expected_lookahead_window_us: The expected lookback window with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_tokens: List[str], actual_channels: List[str], actual_lookahead_window_us: int=50000, actual_lookback_window_us: int=50000) -> Generator[ImageDBRow.Image, None, None]:
            """
            The patch function for get_images_from_lidar_tokens.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_tokens, actual_tokens)
            self.assertEqual(expected_channels, actual_channels)
            self.assertEqual(expected_lookahead_window_us, actual_lookahead_window_us)
            self.assertEqual(expected_lookback_window_us, actual_lookback_window_us)
            for camera_token, channel in enumerate(actual_channels):
                if channel != LidarChannel.MERGED_PC.value:
                    yield ImageDBRow.Image(token=int_to_str_token(camera_token), next_token=int_to_str_token(camera_token), prev_token=int_to_str_token(camera_token), ego_pose_token=int_to_str_token(camera_token), camera_token=int_to_str_token(camera_token), filename_jpg=f'image_{camera_token}', timestamp=camera_token, channel=channel)
        return fxn

    def _get_sampled_lidarpcs_from_db_patch(self, expected_log_file: str, expected_initial_token: str, expected_sensor_data_source: SensorDataSource, expected_sample_indexes: Union[Generator[int, None, None], List[int]], expected_future: bool) -> Callable[[str, str, SensorDataSource, Union[Generator[int, None, None], List[int]], bool], Generator[LidarPc, None, None]]:
        """
        Creates a patch for the get_sampled_lidarpcs_from_db function that validates the arguments.
        :param expected_log_file: The log file name with which the function is expected to be called.
        :param expected_initial_token: The initial token name with which the function is expected to be called.
        :param expected_sensor_data_source: The sensor source with which the function is expected to be called.
        :param expected_sample_indexes: The sample indexes with which the function is expected to be called.
        :param expected_future: The future with which the function is expected to be called.
        :return: The patch function.
        """

        def fxn(actual_log_file: str, actual_initial_token: str, actual_sensor_data_source: SensorDataSource, actual_sample_indexes: Union[Generator[int, None, None], List[int]], actual_future: bool) -> Generator[LidarPc, None, None]:
            """
            The patch function for get_images_from_lidar_tokens.
            """
            self.assertEqual(expected_log_file, actual_log_file)
            self.assertEqual(expected_initial_token, actual_initial_token)
            self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
            self.assertEqual(expected_sample_indexes, actual_sample_indexes)
            self.assertEqual(expected_future, actual_future)
            for idx in actual_sample_indexes:
                lidar_token = int_to_str_token(idx)
                yield LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token))
        return fxn

    def test_implements_abstract_scenario_interface(self) -> None:
        """
        Tests that NuPlanScenario properly implements AbstractScenario interface.
        """
        assert_class_properly_implements_interface(AbstractScenario, NuPlanScenario)

    def test_token(self) -> None:
        """
        Tests that the token method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(int_to_str_token(1234), scenario.token)

    def test_log_name(self) -> None:
        """
        Tests that the log_name method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual('log_name', scenario.log_name)

    def test_scenario_name(self) -> None:
        """
        Tests that the scenario_name method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(int_to_str_token(1234), scenario.scenario_name)

    def test_ego_vehicle_parameters(self) -> None:
        """
        Tests that the ego_vehicle_parameters method works properly.
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(get_pacifica_parameters(), scenario.ego_vehicle_parameters)

    def test_scenario_type(self) -> None:
        """
        Tests that the scenario_type method works properly
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual('scenario_type', scenario.scenario_type)

    def test_database_interval(self) -> None:
        """
        Tests that the database_interval method works properly
        """
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(0.1, scenario.database_interval)

    def test_get_number_of_iterations(self) -> None:
        """
        Tests that the get_number_of_iterations method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn):
                scenario = self._make_test_scenario()
                self.assertEqual(10, scenario.get_number_of_iterations())

    def test_get_time_point(self) -> None:
        """
        Tests that the get_time_point method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        for iter_val in [0, 3, 5]:

            def token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch method for get_lidarpc_token_timstamp_from_db that validates the arguments.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(str_token_to_int(iter_val) + 5)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.get_sensor_data_token_timestamp_from_db', token_timestamp_patch):
                scenario = self._make_test_scenario()
                self.assertEqual(iter_val + 5, scenario.get_time_point(iter_val).time_us)

    def test_get_tracked_objects_at_iteration(self) -> None:
        """
        Tests that the get_tracked_objects_at_iteration method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
        for iter_val in [0, 2, 3]:

            def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(iter_val * 1000000.0)

            def tracked_objects_for_token_patch(log_file: str, token: str) -> Generator[TrackedObject, None, None]:
                """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(int_to_str_token(iter_val), token)
                for idx in range(0, 4, 1):
                    box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                    metadata = SceneObjectMetadata(token=int_to_str_token(idx + str_token_to_int(token)), track_token=int_to_str_token(idx + str_token_to_int(token) + 100), track_id=None, timestamp_us=0, category_name='foo')
                    if idx < 2:
                        yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                    else:
                        yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

            def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
                """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
                self.assertEqual(4, len(waypoints))
                self.assertEqual(0.5, interval_s)
                self.assertEqual(5, time_horizon)
                return waypoints

            def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
                """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(iter_val * 1000000.0, start_time)
                self.assertEqual((iter_val + 5.5) * 1000000.0, end_time)
                self.assertEqual(2, len(agents_tokens))
                check_tokens = [str_token_to_int(t) for t in agents_tokens]
                check_tokens.sort()
                self.assertEqual(iter_val + 100, check_tokens[0])
                self.assertEqual(iter_val + 100 + 1, check_tokens[1])
                for i in range(8):
                    waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                    token = check_tokens[0] if i < 4 else check_tokens[1]
                    yield (int_to_str_token(token), waypoint)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_for_lidarpc_token_from_db', tracked_objects_for_token_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
                scenario = self._make_test_scenario()
                agents = scenario.get_tracked_objects_at_iteration(iter_val, ground_truth_predictions)
                objects = agents.tracked_objects.tracked_objects
                self.assertEqual(4, len(objects))
                objects.sort(key=lambda x: str_token_to_int(x.metadata.token))
                for i in range(0, 2, 1):
                    test_obj = objects[i]
                    self.assertTrue(isinstance(test_obj, Agent))
                    self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                    self.assertIsNotNone(test_obj.predictions)
                    object_waypoints = test_obj.predictions[0].waypoints
                    self.assertEqual(4, len(object_waypoints))
                    for j in range(len(object_waypoints)):
                        self.assertEqual(j + i * len(object_waypoints), object_waypoints[j].x)
                for i in range(2, 4, 1):
                    test_obj = objects[i]
                    self.assertTrue(isinstance(test_obj, StaticObject))
                    self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

    def test_get_tracked_objects_within_time_window_at_iteration(self) -> None:
        """
        Tests that the get_tracked_objects_within_time_window_at_iteration method works properly
        """
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
        for iter_val in [3, 4]:

            def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
                """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
                self.assertEqual(int_to_str_token(iter_val), token)
                return int(iter_val * 1000000.0)

            def tracked_objects_within_time_interval_patch(log_file: str, start_timestamp: int, end_timestamp: int, filter_tokens: Optional[Set[str]]) -> Generator[TrackedObject, None, None]:
                """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual((iter_val - 2) * 1000000.0, start_timestamp)
                self.assertEqual((iter_val + 2) * 1000000.0, end_timestamp)
                self.assertIsNone(filter_tokens)
                for time_idx in range(-2, 3, 1):
                    for idx in range(0, 4, 1):
                        box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                        metadata = SceneObjectMetadata(token=int_to_str_token(idx + iter_val), track_token=int_to_str_token(idx + iter_val + 100), track_id=None, timestamp_us=(iter_val + time_idx) * 1000000.0, category_name='foo')
                        if idx < 2:
                            yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                        else:
                            yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

            def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
                """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
                self.assertEqual(4, len(waypoints))
                self.assertEqual(0.5, interval_s)
                self.assertEqual(5, time_horizon)
                return waypoints

            def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
                """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
                self.assertEqual('data_root/log_name.db', log_file)
                self.assertEqual(end_time - start_time, 5.5 * 1000000.0)
                self.assertEqual(2, len(agents_tokens))
                check_tokens = [str_token_to_int(t) for t in agents_tokens]
                check_tokens.sort()
                self.assertEqual(iter_val + 100, check_tokens[0])
                self.assertEqual(iter_val + 100 + 1, check_tokens[1])
                for i in range(8):
                    waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                    token = check_tokens[0] if i < 4 else check_tokens[1]
                    yield (int_to_str_token(token), waypoint)
            with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_within_time_interval_from_db', tracked_objects_within_time_interval_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
                scenario = self._make_test_scenario()
                agents = scenario.get_tracked_objects_within_time_window_at_iteration(iter_val, 2, 2, future_trajectory_sampling=ground_truth_predictions)
                objects = agents.tracked_objects.tracked_objects
                self.assertEqual(20, len(objects))
                num_objects = 2
                for window in range(0, 5, 1):
                    for object_num in range(0, 2, 1):
                        start_agent_idx = window * 2
                        test_obj = objects[start_agent_idx + object_num]
                        self.assertTrue(isinstance(test_obj, Agent))
                        self.assertEqual(iter_val + object_num, str_token_to_int(test_obj.metadata.token))
                        self.assertEqual(iter_val + object_num + 100, str_token_to_int(test_obj.metadata.track_token))
                        self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                        self.assertIsNotNone(test_obj.predictions)
                        object_waypoints = test_obj.predictions[0].waypoints
                        self.assertEqual(4, len(object_waypoints))
                        for j in range(len(object_waypoints)):
                            self.assertEqual(j + object_num * len(object_waypoints), object_waypoints[j].x)
                        start_obj_idx = 10 + window * 2
                        test_obj = objects[start_obj_idx + object_num]
                        self.assertTrue(isinstance(test_obj, StaticObject))
                        self.assertEqual(iter_val + object_num + num_objects, str_token_to_int(test_obj.metadata.token))
                        self.assertEqual(iter_val + object_num + num_objects + 100, str_token_to_int(test_obj.metadata.track_token))
                        self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

    def test_nuplan_scenario_memory_usage(self) -> None:
        """
        Test that repeatedly creating and destroying nuplan scenario does not cause memory leaks.
        """
        starting_usage = 0
        ending_usage = 0
        num_iterations = 5
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
            hpy = guppy.hpy()
            hpy.setrelheap()
            for i in range(0, num_iterations, 1):
                scenario = self._make_test_scenario()
                _ = scenario.token
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

    @patch(f'{TEST_PATH}.LocalStore', autospec=True)
    @patch(f'{TEST_PATH}.S3Store', autospec=True)
    @patch(f'{TEST_PATH}.os.getenv')
    def test_get_sensors_at_iteration(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
        """Test get_sensors_at_iteration."""
        mock_url = 'url'
        mock_get_env.side_effect = ['s3', mock_url]
        mock_s3_store.return_value = Mock(spec_set=S3Store)
        mock_local_store.return_value = Mock(spec_set=LocalStore)
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0) + 2345, expected_end_timestamp=int(21 * 1000000.0) + 2345, expected_subsample_step=2)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn):
            scenario = self._make_test_scenario()
        for iter_val in [0, 3, 5]:
            lidar_token = int_to_str_token(iter_val)
            get_sensor_data_from_sensor_data_tokens_from_db_fxn = self._get_sensor_data_from_sensor_data_tokens_from_db_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sensor_class=LidarPc, expected_tokens=[lidar_token])
            get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
            load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
            load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
            with mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db', get_sensor_data_from_sensor_data_tokens_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
                sensors = scenario.get_sensors_at_iteration(iter_val, [CameraChannel.CAM_R0, LidarChannel.MERGED_PC])
                self.assertEqual(LidarChannel.MERGED_PC, list(sensors.pointcloud.keys())[0])
                self.assertEqual(CameraChannel.CAM_R0, list(sensors.images.keys())[0])
                mock_local_store.assert_called_with('sensor_root')
                mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

    @patch(f'{TEST_PATH}.LocalStore', autospec=True)
    @patch(f'{TEST_PATH}.S3Store', autospec=True)
    @patch(f'{TEST_PATH}.os.getenv')
    def test_get_past_sensors(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
        """Test get_past_sensors."""
        mock_url = 'url'
        mock_get_env.side_effect = ['s3', mock_url]
        mock_s3_store.return_value = Mock(spec_set=S3Store)
        mock_local_store.return_value = Mock(spec_set=LocalStore)
        lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
        lidar_token = int_to_str_token(9)
        get_sampled_lidarpcs_from_db_fxn = self._get_sampled_lidarpcs_from_db_patch(expected_log_file='data_root/log_name.db', expected_initial_token=int_to_str_token(0), expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sample_indexes=[9], expected_future=False)
        get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
        download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
        load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
        load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
        with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn), mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sampled_lidarpcs_from_db', get_sampled_lidarpcs_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
            scenario = self._make_test_scenario()
            past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=[CameraChannel.CAM_R0, LidarChannel.MERGED_PC]))
            self.assertEqual(1, len(past_sensors))
            self.assertEqual(LidarChannel.MERGED_PC, list(past_sensors[0].pointcloud.keys())[0])
            self.assertEqual(CameraChannel.CAM_R0, list(past_sensors[0].images.keys())[0])
            mock_local_store.assert_called_with('sensor_root')
            mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

    @patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
    @patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
    @patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
    @patch(f'{TEST_PATH}.NuPlanScenario._find_matching_lidar_pcs')
    @patch(f'{TEST_PATH}.load_point_cloud')
    @patch(f'{TEST_PATH}.load_image')
    def test_get_past_sensors_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock__find_matching_lidar_pcs: Mock) -> None:
        """Test get_past_sensors when no channels are passed."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.token = 'token'
        mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
        mock__find_matching_lidar_pcs.return_value = iter([mock_lidar_pc])
        scenario = self._make_test_scenario()
        past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=None))
        mock__find_matching_lidar_pcs.assert_called_once()
        mock_load_point_cloud.assert_called_once()
        mock_load_image.assert_not_called()
        self.assertIsNone(past_sensors[0].images)
        self.assertIsNotNone(past_sensors[0].pointcloud)

    @patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
    @patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
    @patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
    @patch(f'{TEST_PATH}.extract_sensor_tokens_as_scenario', Mock(return_value=[None]))
    @patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db')
    @patch(f'{TEST_PATH}.load_point_cloud')
    @patch(f'{TEST_PATH}.load_image')
    def test_get_sensors_at_iteration_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock_get_sensor_data_from_sensor_data_tokens_from_db: Mock) -> None:
        """Test get_past_sensors when no channels are passed."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.token = 'token'
        mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
        mock_get_sensor_data_from_sensor_data_tokens_from_db.return_value = iter([mock_lidar_pc])
        scenario = self._make_test_scenario()
        sensors = scenario.get_sensors_at_iteration(iteration=0, channels=None)
        mock_get_sensor_data_from_sensor_data_tokens_from_db.assert_called_once()
        mock_load_point_cloud.assert_called_once()
        mock_load_image.assert_not_called()
        self.assertIsNone(sensors.images)
        self.assertIsNotNone(sensors.pointcloud)

def _make_test_scenario(self) -> NuPlanScenario:
    """
        Creates a sample scenario to use for testing.
        """
    return NuPlanScenario(data_root='data_root/', log_file_load_path='data_root/log_name.db', initial_lidar_token=int_to_str_token(1234), initial_lidar_timestamp=2345, scenario_type='scenario_type', map_root='map_root', map_version='map_version', map_name='map_name', scenario_extraction_info=ScenarioExtractionInfo(scenario_name='scenario_name', scenario_duration=20, extraction_offset=1, subsample_ratio=0.5), ego_vehicle_parameters=get_pacifica_parameters(), sensor_root='sensor_root')

def fxn(actual_log_file: str, actual_initial_token: str, actual_sensor_data_source: SensorDataSource, actual_sample_indexes: Union[Generator[int, None, None], List[int]], actual_future: bool) -> Generator[LidarPc, None, None]:
    """
            The patch function for get_images_from_lidar_tokens.
            """
    self.assertEqual(expected_log_file, actual_log_file)
    self.assertEqual(expected_initial_token, actual_initial_token)
    self.assertEqual(expected_sensor_data_source, actual_sensor_data_source)
    self.assertEqual(expected_sample_indexes, actual_sample_indexes)
    self.assertEqual(expected_future, actual_future)
    for idx in actual_sample_indexes:
        lidar_token = int_to_str_token(idx)
        yield LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token))

def test_token(self) -> None:
    """
        Tests that the token method works properly.
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual(int_to_str_token(1234), scenario.token)

def test_log_name(self) -> None:
    """
        Tests that the log_name method works properly.
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual('log_name', scenario.log_name)

def test_scenario_name(self) -> None:
    """
        Tests that the scenario_name method works properly.
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual(int_to_str_token(1234), scenario.scenario_name)

def test_ego_vehicle_parameters(self) -> None:
    """
        Tests that the ego_vehicle_parameters method works properly.
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual(get_pacifica_parameters(), scenario.ego_vehicle_parameters)

def test_scenario_type(self) -> None:
    """
        Tests that the scenario_type method works properly
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual('scenario_type', scenario.scenario_type)

def test_database_interval(self) -> None:
    """
        Tests that the database_interval method works properly
        """
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
        self.assertEqual(0.1, scenario.database_interval)

def test_get_number_of_iterations(self) -> None:
    """
        Tests that the get_number_of_iterations method works properly
        """
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn):
            scenario = self._make_test_scenario()
            self.assertEqual(10, scenario.get_number_of_iterations())

def test_get_time_point(self) -> None:
    """
        Tests that the get_time_point method works properly
        """
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    for iter_val in [0, 3, 5]:

        def token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
            """
                The patch method for get_lidarpc_token_timstamp_from_db that validates the arguments.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
            self.assertEqual(int_to_str_token(iter_val), token)
            return int(str_token_to_int(iter_val) + 5)
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.get_sensor_data_token_timestamp_from_db', token_timestamp_patch):
            scenario = self._make_test_scenario()
            self.assertEqual(iter_val + 5, scenario.get_time_point(iter_val).time_us)

def token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
    """
                The patch method for get_lidarpc_token_timstamp_from_db that validates the arguments.
                """
    self.assertEqual('data_root/log_name.db', log_file)
    self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
    self.assertEqual(int_to_str_token(iter_val), token)
    return int(str_token_to_int(iter_val) + 5)

def test_get_tracked_objects_at_iteration(self) -> None:
    """
        Tests that the get_tracked_objects_at_iteration method works properly
        """
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
    for iter_val in [0, 2, 3]:

        def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
            """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
            self.assertEqual(int_to_str_token(iter_val), token)
            return int(iter_val * 1000000.0)

        def tracked_objects_for_token_patch(log_file: str, token: str) -> Generator[TrackedObject, None, None]:
            """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(int_to_str_token(iter_val), token)
            for idx in range(0, 4, 1):
                box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                metadata = SceneObjectMetadata(token=int_to_str_token(idx + str_token_to_int(token)), track_token=int_to_str_token(idx + str_token_to_int(token) + 100), track_id=None, timestamp_us=0, category_name='foo')
                if idx < 2:
                    yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                else:
                    yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

        def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
            """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
            self.assertEqual(4, len(waypoints))
            self.assertEqual(0.5, interval_s)
            self.assertEqual(5, time_horizon)
            return waypoints

        def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
            """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(iter_val * 1000000.0, start_time)
            self.assertEqual((iter_val + 5.5) * 1000000.0, end_time)
            self.assertEqual(2, len(agents_tokens))
            check_tokens = [str_token_to_int(t) for t in agents_tokens]
            check_tokens.sort()
            self.assertEqual(iter_val + 100, check_tokens[0])
            self.assertEqual(iter_val + 100 + 1, check_tokens[1])
            for i in range(8):
                waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                token = check_tokens[0] if i < 4 else check_tokens[1]
                yield (int_to_str_token(token), waypoint)
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_for_lidarpc_token_from_db', tracked_objects_for_token_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
            scenario = self._make_test_scenario()
            agents = scenario.get_tracked_objects_at_iteration(iter_val, ground_truth_predictions)
            objects = agents.tracked_objects.tracked_objects
            self.assertEqual(4, len(objects))
            objects.sort(key=lambda x: str_token_to_int(x.metadata.token))
            for i in range(0, 2, 1):
                test_obj = objects[i]
                self.assertTrue(isinstance(test_obj, Agent))
                self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                self.assertIsNotNone(test_obj.predictions)
                object_waypoints = test_obj.predictions[0].waypoints
                self.assertEqual(4, len(object_waypoints))
                for j in range(len(object_waypoints)):
                    self.assertEqual(j + i * len(object_waypoints), object_waypoints[j].x)
            for i in range(2, 4, 1):
                test_obj = objects[i]
                self.assertTrue(isinstance(test_obj, StaticObject))
                self.assertEqual(iter_val + i, str_token_to_int(test_obj.metadata.token))
                self.assertEqual(iter_val + i + 100, str_token_to_int(test_obj.metadata.track_token))
                self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
    """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
    self.assertEqual('data_root/log_name.db', log_file)
    self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
    self.assertEqual(int_to_str_token(iter_val), token)
    return int(iter_val * 1000000.0)

def tracked_objects_for_token_patch(log_file: str, token: str) -> Generator[TrackedObject, None, None]:
    """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
    self.assertEqual('data_root/log_name.db', log_file)
    self.assertEqual(int_to_str_token(iter_val), token)
    for idx in range(0, 4, 1):
        box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
        metadata = SceneObjectMetadata(token=int_to_str_token(idx + str_token_to_int(token)), track_token=int_to_str_token(idx + str_token_to_int(token) + 100), track_id=None, timestamp_us=0, category_name='foo')
        if idx < 2:
            yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
        else:
            yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
    """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
    self.assertEqual('data_root/log_name.db', log_file)
    self.assertEqual(end_time - start_time, 5.5 * 1000000.0)
    self.assertEqual(2, len(agents_tokens))
    check_tokens = [str_token_to_int(t) for t in agents_tokens]
    check_tokens.sort()
    self.assertEqual(iter_val + 100, check_tokens[0])
    self.assertEqual(iter_val + 100 + 1, check_tokens[1])
    for i in range(8):
        waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
        token = check_tokens[0] if i < 4 else check_tokens[1]
        yield (int_to_str_token(token), waypoint)

def test_get_tracked_objects_within_time_window_at_iteration(self) -> None:
    """
        Tests that the get_tracked_objects_within_time_window_at_iteration method works properly
        """
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    ground_truth_predictions = TrajectorySampling(num_poses=10, time_horizon=5, interval_length=None)
    for iter_val in [3, 4]:

        def get_token_timestamp_patch(log_file: str, sensor_source: SensorDataSource, token: str) -> int:
            """
                The patch for get_sensor_data_token_timestamp_from_db that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(SensorDataSource(table='lidar_pc', sensor_table='lidar', sensor_token_column='lidar_token', channel='MergedPointCloud'), sensor_source)
            self.assertEqual(int_to_str_token(iter_val), token)
            return int(iter_val * 1000000.0)

        def tracked_objects_within_time_interval_patch(log_file: str, start_timestamp: int, end_timestamp: int, filter_tokens: Optional[Set[str]]) -> Generator[TrackedObject, None, None]:
            """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual((iter_val - 2) * 1000000.0, start_timestamp)
            self.assertEqual((iter_val + 2) * 1000000.0, end_timestamp)
            self.assertIsNone(filter_tokens)
            for time_idx in range(-2, 3, 1):
                for idx in range(0, 4, 1):
                    box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
                    metadata = SceneObjectMetadata(token=int_to_str_token(idx + iter_val), track_token=int_to_str_token(idx + iter_val + 100), track_id=None, timestamp_us=(iter_val + time_idx) * 1000000.0, category_name='foo')
                    if idx < 2:
                        yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
                    else:
                        yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

        def interpolate_future_waypoints_patch(waypoints: List[InterpolatableState], time_horizon: float, interval_s: float) -> List[Optional[InterpolatableState]]:
            """
                The patch for interpolate_future_waypoints that validates the arguments and generates fake data.
                """
            self.assertEqual(4, len(waypoints))
            self.assertEqual(0.5, interval_s)
            self.assertEqual(5, time_horizon)
            return waypoints

        def future_waypoints_for_agents_patch(log_file: str, agents_tokens: List[str], start_time: int, end_time: int) -> Generator[Tuple[str, Waypoint], None, None]:
            """
                The patch for get_future_waypoints_for_agents_from_db that validates the arguments and generates fake data.
                """
            self.assertEqual('data_root/log_name.db', log_file)
            self.assertEqual(end_time - start_time, 5.5 * 1000000.0)
            self.assertEqual(2, len(agents_tokens))
            check_tokens = [str_token_to_int(t) for t in agents_tokens]
            check_tokens.sort()
            self.assertEqual(iter_val + 100, check_tokens[0])
            self.assertEqual(iter_val + 100 + 1, check_tokens[1])
            for i in range(8):
                waypoint = Waypoint(time_point=TimePoint(time_us=i), oriented_box=OrientedBox(center=StateSE2(x=i, y=i, heading=i), length=i, width=i, height=i), velocity=None)
                token = check_tokens[0] if i < 4 else check_tokens[1]
                yield (int_to_str_token(token), waypoint)
        with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_tracked_objects_within_time_interval_from_db', tracked_objects_within_time_interval_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_future_waypoints_for_agents_from_db', future_waypoints_for_agents_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.get_sensor_data_token_timestamp_from_db', get_token_timestamp_patch), mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_utils.interpolate_future_waypoints', interpolate_future_waypoints_patch):
            scenario = self._make_test_scenario()
            agents = scenario.get_tracked_objects_within_time_window_at_iteration(iter_val, 2, 2, future_trajectory_sampling=ground_truth_predictions)
            objects = agents.tracked_objects.tracked_objects
            self.assertEqual(20, len(objects))
            num_objects = 2
            for window in range(0, 5, 1):
                for object_num in range(0, 2, 1):
                    start_agent_idx = window * 2
                    test_obj = objects[start_agent_idx + object_num]
                    self.assertTrue(isinstance(test_obj, Agent))
                    self.assertEqual(iter_val + object_num, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + object_num + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.VEHICLE, test_obj.tracked_object_type)
                    self.assertIsNotNone(test_obj.predictions)
                    object_waypoints = test_obj.predictions[0].waypoints
                    self.assertEqual(4, len(object_waypoints))
                    for j in range(len(object_waypoints)):
                        self.assertEqual(j + object_num * len(object_waypoints), object_waypoints[j].x)
                    start_obj_idx = 10 + window * 2
                    test_obj = objects[start_obj_idx + object_num]
                    self.assertTrue(isinstance(test_obj, StaticObject))
                    self.assertEqual(iter_val + object_num + num_objects, str_token_to_int(test_obj.metadata.token))
                    self.assertEqual(iter_val + object_num + num_objects + 100, str_token_to_int(test_obj.metadata.track_token))
                    self.assertEqual(TrackedObjectType.CZONE_SIGN, test_obj.tracked_object_type)

def tracked_objects_within_time_interval_patch(log_file: str, start_timestamp: int, end_timestamp: int, filter_tokens: Optional[Set[str]]) -> Generator[TrackedObject, None, None]:
    """
                The patch for get_tracked_objects_for_lidarpc_token that validates the arguments and generates fake data.
                """
    self.assertEqual('data_root/log_name.db', log_file)
    self.assertEqual((iter_val - 2) * 1000000.0, start_timestamp)
    self.assertEqual((iter_val + 2) * 1000000.0, end_timestamp)
    self.assertIsNone(filter_tokens)
    for time_idx in range(-2, 3, 1):
        for idx in range(0, 4, 1):
            box = OrientedBox(center=StateSE2(x=10, y=10, heading=10), length=10, width=10, height=10)
            metadata = SceneObjectMetadata(token=int_to_str_token(idx + iter_val), track_token=int_to_str_token(idx + iter_val + 100), track_id=None, timestamp_us=(iter_val + time_idx) * 1000000.0, category_name='foo')
            if idx < 2:
                yield Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=box, velocity=StateVector2D(x=10, y=10), metadata=metadata)
            else:
                yield StaticObject(tracked_object_type=TrackedObjectType.CZONE_SIGN, oriented_box=box, metadata=metadata)

def test_nuplan_scenario_memory_usage(self) -> None:
    """
        Test that repeatedly creating and destroying nuplan scenario does not cause memory leaks.
        """
    starting_usage = 0
    ending_usage = 0
    num_iterations = 5
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario.download_file_if_necessary', download_file_patch_fxn):
        hpy = guppy.hpy()
        hpy.setrelheap()
        for i in range(0, num_iterations, 1):
            scenario = self._make_test_scenario()
            _ = scenario.token
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

@patch(f'{TEST_PATH}.LocalStore', autospec=True)
@patch(f'{TEST_PATH}.S3Store', autospec=True)
@patch(f'{TEST_PATH}.os.getenv')
def test_get_sensors_at_iteration(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
    """Test get_sensors_at_iteration."""
    mock_url = 'url'
    mock_get_env.side_effect = ['s3', mock_url]
    mock_s3_store.return_value = Mock(spec_set=S3Store)
    mock_local_store.return_value = Mock(spec_set=LocalStore)
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0) + 2345, expected_end_timestamp=int(21 * 1000000.0) + 2345, expected_subsample_step=2)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn):
        scenario = self._make_test_scenario()
    for iter_val in [0, 3, 5]:
        lidar_token = int_to_str_token(iter_val)
        get_sensor_data_from_sensor_data_tokens_from_db_fxn = self._get_sensor_data_from_sensor_data_tokens_from_db_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sensor_class=LidarPc, expected_tokens=[lidar_token])
        get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
        load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
        load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
        with mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db', get_sensor_data_from_sensor_data_tokens_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
            sensors = scenario.get_sensors_at_iteration(iter_val, [CameraChannel.CAM_R0, LidarChannel.MERGED_PC])
            self.assertEqual(LidarChannel.MERGED_PC, list(sensors.pointcloud.keys())[0])
            self.assertEqual(CameraChannel.CAM_R0, list(sensors.images.keys())[0])
            mock_local_store.assert_called_with('sensor_root')
            mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

@patch(f'{TEST_PATH}.LocalStore', autospec=True)
@patch(f'{TEST_PATH}.S3Store', autospec=True)
@patch(f'{TEST_PATH}.os.getenv')
def test_get_past_sensors(self, mock_get_env: Mock, mock_s3_store: Mock, mock_local_store: Mock) -> None:
    """Test get_past_sensors."""
    mock_url = 'url'
    mock_get_env.side_effect = ['s3', mock_url]
    mock_s3_store.return_value = Mock(spec_set=S3Store)
    mock_local_store.return_value = Mock(spec_set=LocalStore)
    lidarpc_tokens_patch_fxn = self._get_sampled_sensor_tokens_in_time_window_patch(expected_log_file='data_root/log_name.db', expected_sensor_data_source=get_lidarpc_sensor_data(), expected_start_timestamp=int(1 * 1000000.0 + 2345), expected_end_timestamp=int(21 * 1000000.0 + 2345), expected_subsample_step=2)
    lidar_token = int_to_str_token(9)
    get_sampled_lidarpcs_from_db_fxn = self._get_sampled_lidarpcs_from_db_patch(expected_log_file='data_root/log_name.db', expected_initial_token=int_to_str_token(0), expected_sensor_data_source=get_lidarpc_sensor_data(), expected_sample_indexes=[9], expected_future=False)
    get_images_from_lidar_tokens_fxn = self._get_images_from_lidar_tokens_patch(expected_log_file='data_root/log_name.db', expected_tokens=[lidar_token], expected_channels=[CameraChannel.CAM_R0.value, LidarChannel.MERGED_PC.value], expected_lookahead_window_us=50000, expected_lookback_window_us=50000)
    download_file_patch_fxn = self._get_download_file_if_necessary_patch(expected_data_root='data_root/', expected_log_file_load_path='data_root/log_name.db')
    load_lidar_fxn = self._load_point_cloud_patch(LidarPc(token=lidar_token, next_token=lidar_token, prev_token=lidar_token, ego_pose_token=lidar_token, lidar_token=lidar_token, scene_token=lidar_token, filename=f'lidar_{lidar_token}', timestamp=str_token_to_int(lidar_token)), mock_local_store.return_value, mock_s3_store.return_value)
    load_image_fxn = self._load_image_patch(mock_local_store.return_value, mock_s3_store.return_value)
    with mock.patch(f'{TEST_PATH}.download_file_if_necessary', download_file_patch_fxn), mock.patch(f'{TEST_PATH_UTILS}.get_sampled_sensor_tokens_in_time_window_from_db', lidarpc_tokens_patch_fxn), mock.patch(f'{TEST_PATH}.get_sampled_lidarpcs_from_db', get_sampled_lidarpcs_from_db_fxn), mock.patch(f'{TEST_PATH}.get_images_from_lidar_tokens', get_images_from_lidar_tokens_fxn), mock.patch(f'{TEST_PATH}.load_point_cloud', load_lidar_fxn), mock.patch(f'{TEST_PATH}.load_image', load_image_fxn):
        scenario = self._make_test_scenario()
        past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=[CameraChannel.CAM_R0, LidarChannel.MERGED_PC]))
        self.assertEqual(1, len(past_sensors))
        self.assertEqual(LidarChannel.MERGED_PC, list(past_sensors[0].pointcloud.keys())[0])
        self.assertEqual(CameraChannel.CAM_R0, list(past_sensors[0].images.keys())[0])
        mock_local_store.assert_called_with('sensor_root')
        mock_s3_store.assert_called_with(f'{mock_url}/sensor_blobs', show_progress=True)

@patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
@patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
@patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
@patch(f'{TEST_PATH}.NuPlanScenario._find_matching_lidar_pcs')
@patch(f'{TEST_PATH}.load_point_cloud')
@patch(f'{TEST_PATH}.load_image')
def test_get_past_sensors_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock__find_matching_lidar_pcs: Mock) -> None:
    """Test get_past_sensors when no channels are passed."""
    mock_lidar_pc = Mock(spec=LidarPc)
    mock_lidar_pc.token = 'token'
    mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
    mock__find_matching_lidar_pcs.return_value = iter([mock_lidar_pc])
    scenario = self._make_test_scenario()
    past_sensors = list(scenario.get_past_sensors(iteration=0, time_horizon=0.4, num_samples=1, channels=None))
    mock__find_matching_lidar_pcs.assert_called_once()
    mock_load_point_cloud.assert_called_once()
    mock_load_image.assert_not_called()
    self.assertIsNone(past_sensors[0].images)
    self.assertIsNotNone(past_sensors[0].pointcloud)

@patch(f'{TEST_PATH}.download_file_if_necessary', Mock())
@patch(f'{TEST_PATH}.absolute_path_to_log_name', Mock())
@patch(f'{TEST_PATH}.get_images_from_lidar_tokens', Mock(return_value=[]))
@patch(f'{TEST_PATH}.extract_sensor_tokens_as_scenario', Mock(return_value=[None]))
@patch(f'{TEST_PATH}.get_sensor_data_from_sensor_data_tokens_from_db')
@patch(f'{TEST_PATH}.load_point_cloud')
@patch(f'{TEST_PATH}.load_image')
def test_get_sensors_at_iteration_no_channels(self, mock_load_image: Mock, mock_load_point_cloud: Mock, mock_get_sensor_data_from_sensor_data_tokens_from_db: Mock) -> None:
    """Test get_past_sensors when no channels are passed."""
    mock_lidar_pc = Mock(spec=LidarPc)
    mock_lidar_pc.token = 'token'
    mock_load_point_cloud.return_value = Mock(spec_set=LidarPointCloud)
    mock_get_sensor_data_from_sensor_data_tokens_from_db.return_value = iter([mock_lidar_pc])
    scenario = self._make_test_scenario()
    sensors = scenario.get_sensors_at_iteration(iteration=0, channels=None)
    mock_get_sensor_data_from_sensor_data_tokens_from_db.assert_called_once()
    mock_load_point_cloud.assert_called_once()
    mock_load_image.assert_not_called()
    self.assertIsNone(sensors.images)
    self.assertIsNotNone(sensors.pointcloud)

class TestNuPlanScenarioUtils(unittest.TestCase):
    """Test cases for nuplan_scenario_utils.py"""

    def test_convert_legacy_nuplan_path_to_latest(self) -> None:
        """Test that convert_legacy_nuplan_path_to_latest works as expected."""
        legacy_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        legacy_path_str = str(legacy_path)
        expected_latest_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        expected_latest_path_str = str(expected_latest_path)
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str)
        self.assertEqual(expected_latest_path_str, actual_latest_path)
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, NUPLAN_DATA_ROOT)
        self.assertEqual(expected_latest_path_str, actual_latest_path)
        data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, data_root_without_slash)
        self.assertEqual(expected_latest_path_str, actual_latest_path)

    def test_convert_legacy_nuplan_path_to_latest_invalid_path(self) -> None:
        """Test that convert_legacy_nuplan_path_to_latest will throw if path does not contain version info."""
        invalid_legacy_path = Path(NUPLAN_DATA_ROOT) / 'mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        invalid_legacy_path_str = str(invalid_legacy_path)
        with self.assertRaises(ValueError):
            _ = convert_legacy_nuplan_path_to_latest(invalid_legacy_path_str)

    def test_infer_remote_key_from_local_path(self) -> None:
        """Test that infer_remote_key_from_local_path works as expected."""
        local_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        local_path_str = str(local_path)
        expected_remote_key = 'splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        actual_remote_key = infer_remote_key_from_local_path(local_path_str)
        self.assertEqual(expected_remote_key, actual_remote_key)
        actual_remote_key = infer_remote_key_from_local_path(local_path_str, NUPLAN_DATA_ROOT)
        self.assertEqual(expected_remote_key, actual_remote_key)
        data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
        actual_remote_key = infer_remote_key_from_local_path(local_path_str, data_root_without_slash)
        self.assertEqual(expected_remote_key, actual_remote_key)

    @patch(f'{TEST_PATH}.LidarPointCloud.from_buffer')
    @patch(f'{TEST_PATH}.download_and_cache')
    def test_load_point_cloud(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
        """Test load_point_cloud."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.filename = 'pcd'
        mock_local_store = Mock(spec=LocalStore)
        mock_remote_store = Mock(spec=S3Store)
        mock_load_sensor.return_value = Mock()
        load_point_cloud(mock_lidar_pc, mock_local_store, mock_remote_store)
        mock_load_sensor.assert_called_with(mock_lidar_pc.filename, mock_local_store, mock_remote_store)
        mock_from_buffer.assert_called_with(mock_load_sensor.return_value, mock_lidar_pc.filename)

    @patch(f'{TEST_PATH}.Image.from_buffer')
    @patch(f'{TEST_PATH}.download_and_cache')
    def test_load_image(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
        """Test load_point_cloud."""
        mock_image = Mock(spec=Image)
        mock_image.filename_jpg = 'image'
        mock_local_store = Mock(spec=LocalStore)
        mock_remote_store = Mock(spec=S3Store)
        mock_load_sensor.return_value = Mock()
        load_image(mock_image, mock_local_store, mock_remote_store)
        mock_load_sensor.assert_called_with(mock_image.filename_jpg, mock_local_store, mock_remote_store)
        mock_from_buffer.assert_called_with(mock_load_sensor.return_value)

    def test_download_and_cache(self) -> None:
        """Test download_and_cache."""
        mock_key = 'key'
        mock_image = Mock(spec=Image)
        mock_image.filename_jpg = 'image'
        mock_local_store = Mock(spec=LocalStore)
        mock_local_store.exists.side_effect = [True, False, False]
        mock_local_store.get.return_value = Mock(spec=BinaryIO)
        mock_local_store.put = Mock()
        mock_remote_store = Mock(spec=S3Store)
        mock_remote_store.get = Mock(return_value=Mock(spec=BinaryIO))
        blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
        self.assertEqual(mock_local_store.get.return_value, blob)
        self.assertTrue(isinstance(blob, BinaryIO))
        with self.assertRaises(RuntimeError):
            download_and_cache(mock_key, mock_local_store, None)
        blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
        mock_remote_store.get.assert_called_with(mock_key)
        mock_local_store.put.assert_called_with(mock_key, mock_remote_store.get.return_value)
        self.assertTrue(isinstance(blob, BinaryIO))

@patch(f'{TEST_PATH}.LidarPointCloud.from_buffer')
@patch(f'{TEST_PATH}.download_and_cache')
def test_load_point_cloud(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
    """Test load_point_cloud."""
    mock_lidar_pc = Mock(spec=LidarPc)
    mock_lidar_pc.filename = 'pcd'
    mock_local_store = Mock(spec=LocalStore)
    mock_remote_store = Mock(spec=S3Store)
    mock_load_sensor.return_value = Mock()
    load_point_cloud(mock_lidar_pc, mock_local_store, mock_remote_store)
    mock_load_sensor.assert_called_with(mock_lidar_pc.filename, mock_local_store, mock_remote_store)
    mock_from_buffer.assert_called_with(mock_load_sensor.return_value, mock_lidar_pc.filename)

@patch(f'{TEST_PATH}.Image.from_buffer')
@patch(f'{TEST_PATH}.download_and_cache')
def test_load_image(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
    """Test load_point_cloud."""
    mock_image = Mock(spec=Image)
    mock_image.filename_jpg = 'image'
    mock_local_store = Mock(spec=LocalStore)
    mock_remote_store = Mock(spec=S3Store)
    mock_load_sensor.return_value = Mock()
    load_image(mock_image, mock_local_store, mock_remote_store)
    mock_load_sensor.assert_called_with(mock_image.filename_jpg, mock_local_store, mock_remote_store)
    mock_from_buffer.assert_called_with(mock_load_sensor.return_value)

def test_download_and_cache(self) -> None:
    """Test download_and_cache."""
    mock_key = 'key'
    mock_image = Mock(spec=Image)
    mock_image.filename_jpg = 'image'
    mock_local_store = Mock(spec=LocalStore)
    mock_local_store.exists.side_effect = [True, False, False]
    mock_local_store.get.return_value = Mock(spec=BinaryIO)
    mock_local_store.put = Mock()
    mock_remote_store = Mock(spec=S3Store)
    mock_remote_store.get = Mock(return_value=Mock(spec=BinaryIO))
    blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
    self.assertEqual(mock_local_store.get.return_value, blob)
    self.assertTrue(isinstance(blob, BinaryIO))
    with self.assertRaises(RuntimeError):
        download_and_cache(mock_key, mock_local_store, None)
    blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
    mock_remote_store.get.assert_called_with(mock_key)
    mock_local_store.put.assert_called_with(mock_key, mock_remote_store.get.return_value)
    self.assertTrue(isinstance(blob, BinaryIO))

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

class SubmissionContainerManager:
    """Class to store created submission containers using a factory."""

    def __init__(self, submission_container_factory: SubmissionContainerFactory):
        """
        :param submission_container_factory: The factory class for the manager
        """
        self.submission_container_factory = submission_container_factory
        self.submission_containers: Dict[str, SubmissionContainer] = {}

    def get_submission_container(self, image: str, container_name: str, port: int) -> SubmissionContainer:
        """
        Returns the queried submission container from the factory, creating it if it's missing
        :param image: Image name
        :param container_name: Container name
        :param port: Port number to open
        :return: The queried submission container
        """
        if container_name not in self.submission_containers:
            self.submission_containers[container_name] = self.submission_container_factory.build_submission_container(image, container_name, port)
        return self.submission_containers[container_name]

def get_submission_container(self, image: str, container_name: str, port: int) -> SubmissionContainer:
    """
        Returns the queried submission container from the factory, creating it if it's missing
        :param image: Image name
        :param container_name: Container name
        :param port: Port number to open
        :return: The queried submission container
        """
    if container_name not in self.submission_containers:
        self.submission_containers[container_name] = self.submission_container_factory.build_submission_container(image, container_name, port)
    return self.submission_containers[container_name]

class SubmissionContainerFactory:
    """Factory for SubmissionContainer"""

    @staticmethod
    def build_submission_container(submission_image: str, container_name: str, port: int) -> SubmissionContainer:
        """
        Builds a SubmissionContainer given submission image, container name and port
        :param submission_image: Name of the Docker image
        :param container_name: Name for the Docker container
        :param port: Port number
        :return: The constructed SubmissionContainer
        """
        return SubmissionContainer(submission_image, container_name, port)

@staticmethod
def build_submission_container(submission_image: str, container_name: str, port: int) -> SubmissionContainer:
    """
        Builds a SubmissionContainer given submission image, container name and port
        :param submission_image: Name of the Docker image
        :param container_name: Name for the Docker container
        :param port: Port number
        :return: The constructed SubmissionContainer
        """
    return SubmissionContainer(submission_image, container_name, port)

class LeaderBoardWriter:
    """Class to write to EvalAI leaderboard."""

    def __init__(self, cfg: DictConfig, submission_path: str) -> None:
        """
        :param cfg: Hydra configuration
        :param submission_path: Path to the directory where the submission files are stored.
        """
        self.contestant_id = cfg.contestant_id
        self.submission_id = cfg.submission_id
        self.output_dir = cfg.output_dir
        self.aggregator_save_path = cfg.aggregator_save_path
        self.challenges = cfg.challenges
        with open(f'{submission_path}/submission_metadata.json', 'r') as file:
            self.submission_metadata = json.load(file)
        try:
            with open(f'{submission_path}/stout.log', 'r') as stdout:
                self.stdout = stdout.read()
        except FileNotFoundError:
            logger.info('No STDOUT log file found')
            self.stdout = ''
        try:
            with open(f'{submission_path}/stderr.log', 'r') as stderr:
                self.stderr = stderr.read()
        except FileNotFoundError:
            logger.info('No STDERR log file found')
            self.stderr = ''
        self.interface = EvalaiInterface()

    def write_to_leaderboard(self, simulation_successful: bool) -> None:
        """
        Writes to the leaderboard
        :param simulation_successful: Whether the simulation was successful or not.
        """
        if simulation_successful:
            logger.info('Writing to leaderboard SUCCESSFUL simulation...')
            data = self._on_successful_submission()
        else:
            logger.info('Writing to leaderboard FAILED simulation...')
            data = self._on_failed_submission()
        self.interface.update_submission_data(data)

    def _on_failed_submission(self) -> Dict[str, str]:
        """
        Builds leaderboard message for failed simulations.
        :return: Message to mark submission as failed
        """
        submission_data = {'challenge_phase': self.submission_metadata.get('challenge_phase'), 'submission': self.submission_metadata.get('submission_id'), 'stdout': self.stdout, 'stderr': self.stderr, 'submission_status': 'FAILED', 'metadata': ''}
        return submission_data

    def _on_successful_submission(self) -> Dict[str, str]:
        """
        Builds leaderboard message for successful simulations.
        :return: Message to mark submission as successful, and to add metric values to leaderboard.
        """
        results: Dict[str, pd.DataFrame] = {}
        for challenge in self.challenges:
            challenge_result_files = Path(self.aggregator_save_path).glob('*.parquet')
            challenge_parquets = [pd.read_parquet(file) for file in challenge_result_files if challenge in str(file)]
            results[challenge] = challenge_parquets[0] if challenge_parquets else []
        result = json.dumps([{'split': 'data_split', 'show_to_participant': True, 'accuracies': read_metrics_from_results(results)}])
        submission_data = {'challenge_phase': self.submission_metadata.get('challenge_phase'), 'submission': self.submission_metadata.get('submission_id'), 'stdout': self.stdout, 'stderr': self.stderr, 'result': result, 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
        return submission_data

def write_to_leaderboard(self, simulation_successful: bool) -> None:
    """
        Writes to the leaderboard
        :param simulation_successful: Whether the simulation was successful or not.
        """
    if simulation_successful:
        logger.info('Writing to leaderboard SUCCESSFUL simulation...')
        data = self._on_successful_submission()
    else:
        logger.info('Writing to leaderboard FAILED simulation...')
        data = self._on_failed_submission()
    self.interface.update_submission_data(data)

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

class TestLeaderboardWriter(unittest.TestCase):
    """Tests for the LeaderboardWriter class."""

    @patch(f'{TEST_FILE}.EvalaiInterface')
    def setUp(self, mock_interface: Mock) -> None:
        """Sets up variables for testing."""
        self.mock_interface = mock_interface
        main_path = os.path.dirname(os.path.realpath(__file__))
        common_dir = 'file://' + os.path.join(main_path, '../../../planning/script/config/common')
        self.search_path = f'hydra.searchpath=[{common_dir}]'
        with initialize_config_dir(config_dir=CONFIG_PATH):
            cfg = compose(config_name=CONFIG_NAME, overrides=[self.search_path, 'contestant_id=contestant', 'submission_id=submission'])
            self.tmpdir = tempfile.TemporaryDirectory()
            self.addCleanup(self.tmpdir.cleanup)
            metadata = {'challenge_phase': 'phase', 'submission_id': 'my_sub'}
            with open(f'{self.tmpdir.name}/submission_metadata.json', 'w') as fp:
                json.dump(metadata, fp)
            self.leaderboard_writer = LeaderBoardWriter(cfg, self.tmpdir.name)

    def test_write_to_leaderboard(self) -> None:
        """Tests that writing to leaderboard calls the correct callbacks an api."""
        with patch.object(self.leaderboard_writer, '_on_successful_submission'):
            self.leaderboard_writer.write_to_leaderboard(simulation_successful=True)
            self.leaderboard_writer._on_successful_submission.assert_called_once()
            self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_successful_submission.return_value)
        self.mock_interface.reset_mock()
        with patch.object(self.leaderboard_writer, '_on_failed_submission'):
            self.leaderboard_writer.write_to_leaderboard(simulation_successful=False)
            self.leaderboard_writer._on_failed_submission.assert_called_once()
            self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_failed_submission.return_value)

    def test__on_failed_submission(self) -> None:
        """Tests message creation on failes submission callback."""
        expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'submission_status': 'FAILED', 'metadata': ''}
        data = self.leaderboard_writer._on_failed_submission()
        self.assertEqual(expected_data, data)

    def test__on_successful_submission(self) -> None:
        """Tests message creation on successful submission callback."""
        expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'result': '[{"split": "data_split", "show_to_participant": true, "accuracies": "results"}]', 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
        with patch(f'{TEST_FILE}.read_metrics_from_results') as reader:
            reader.return_value = 'results'
            data = self.leaderboard_writer._on_successful_submission()
            self.assertEqual(expected_data, data)

    def test_read_metrics_from_results(self) -> None:
        """Tests parsing of dataframes."""
        dataframes = {'open_loop_boxes': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [0], 'planner_expert_average_l2_error_within_bound': [1], 'planner_expert_final_l2_error_within_bound': [2], 'planner_miss_rate_within_bound': [3], 'planner_expert_average_heading_error_within_bound': [4], 'planner_expert_final_heading_error_within_bound': [5]}), 'closed_loop_nonreactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [10], 'ego_is_making_progress': [11], 'no_ego_at_fault_collisions': [12], 'drivable_area_compliance': [13], 'driving_direction_compliance': [14], 'ego_is_comfortable': [15], 'ego_progress_along_expert_route': [16], 'time_to_collision_within_bound': [17], 'speed_limit_compliance': [18]}), 'closed_loop_reactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [110], 'ego_is_making_progress': [111], 'no_ego_at_fault_collisions': [112], 'drivable_area_compliance': [113], 'driving_direction_compliance': [114], 'ego_is_comfortable': [115], 'ego_progress_along_expert_route': [116], 'time_to_collision_within_bound': [117], 'speed_limit_compliance': [118]})}
        metrics = read_metrics_from_results(dataframes)
        expected_metrics = {'ch1_overall_score': 0, 'ch1_avg_displacement_error_within_bound': 1, 'ch1_final_displacement_error_within_bound': 2, 'ch1_miss_rate_within_bound': 3, 'ch1_avg_heading_error_within_bound': 4, 'ch1_final_heading_error_within_bound': 5, 'ch2_overall_score': 10, 'ch2_ego_is_making_progress': 11, 'ch2_no_ego_at_fault_collisions': 12, 'ch2_drivable_area_compliance': 13, 'ch2_driving_direction_compliance': 14, 'ch2_ego_is_comfortable': 15, 'ch2_ego_progress_along_expert_route': 16, 'ch2_time_to_collision_within_bound': 17, 'ch2_speed_limit_compliance': 18, 'ch3_overall_score': 110, 'ch3_ego_is_making_progress': 111, 'ch3_no_ego_at_fault_collisions': 112, 'ch3_drivable_area_compliance': 113, 'ch3_driving_direction_compliance': 114, 'ch3_ego_is_comfortable': 115, 'ch3_ego_progress_along_expert_route': 116, 'ch3_time_to_collision_within_bound': 117, 'ch3_speed_limit_compliance': 118, 'combined_overall_score': 40.0}
        self.assertEqual(metrics, expected_metrics)

def test_write_to_leaderboard(self) -> None:
    """Tests that writing to leaderboard calls the correct callbacks an api."""
    with patch.object(self.leaderboard_writer, '_on_successful_submission'):
        self.leaderboard_writer.write_to_leaderboard(simulation_successful=True)
        self.leaderboard_writer._on_successful_submission.assert_called_once()
        self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_successful_submission.return_value)
    self.mock_interface.reset_mock()
    with patch.object(self.leaderboard_writer, '_on_failed_submission'):
        self.leaderboard_writer.write_to_leaderboard(simulation_successful=False)
        self.leaderboard_writer._on_failed_submission.assert_called_once()
        self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_failed_submission.return_value)

def test__on_failed_submission(self) -> None:
    """Tests message creation on failes submission callback."""
    expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'submission_status': 'FAILED', 'metadata': ''}
    data = self.leaderboard_writer._on_failed_submission()
    self.assertEqual(expected_data, data)

def test__on_successful_submission(self) -> None:
    """Tests message creation on successful submission callback."""
    expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'result': '[{"split": "data_split", "show_to_participant": true, "accuracies": "results"}]', 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
    with patch(f'{TEST_FILE}.read_metrics_from_results') as reader:
        reader.return_value = 'results'
        data = self.leaderboard_writer._on_successful_submission()
        self.assertEqual(expected_data, data)

class TestImageIsRunnableValidator(unittest.TestCase):
    """Tests for the ImageIsRunnableValidator class"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.validator = ImageIsRunnableValidator()

    def test_construction(self) -> None:
        """Tests that the variables are initialized correctly."""
        self.assertTrue(isinstance(self.validator, BaseSubmissionValidator))

    @patch('nuplan.submission.validators.image_is_runnable_validator.SubmissionContainer')
    def test_validate_runnable(self, mock_submission_container: Mock) -> None:
        """Tests that validator calls the next validator when the image is runnable."""
        submission = 'foo'
        with patch.object(BaseSubmissionValidator, 'validate') as mock_validate:
            self.validator.validate(submission)
            mock_submission_container.return_value.start.assert_called_once()
            mock_validate.assert_called_with(submission)

    @patch('nuplan.submission.validators.image_is_runnable_validator.SubmissionContainer')
    def test_validate_not_runnable(self, mock_submission_container: Mock) -> None:
        """Tests that validator returns False when image is not runnable."""
        mock_submission_container.return_value.wait_until_running.side_effect = TimeoutError
        result = self.validator.validate('foo')
        self.assertFalse(result)

@patch('nuplan.submission.validators.image_is_runnable_validator.SubmissionContainer')
def test_validate_runnable(self, mock_submission_container: Mock) -> None:
    """Tests that validator calls the next validator when the image is runnable."""
    submission = 'foo'
    with patch.object(BaseSubmissionValidator, 'validate') as mock_validate:
        self.validator.validate(submission)
        mock_submission_container.return_value.start.assert_called_once()
        mock_validate.assert_called_with(submission)

@patch('nuplan.submission.validators.image_is_runnable_validator.SubmissionContainer')
def test_validate_not_runnable(self, mock_submission_container: Mock) -> None:
    """Tests that validator returns False when image is not runnable."""
    mock_submission_container.return_value.wait_until_running.side_effect = TimeoutError
    result = self.validator.validate('foo')
    self.assertFalse(result)

class TestSubmissionValidator(unittest.TestCase):
    """Tests for the BaseSubmissionValidator class"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.validator = BaseSubmissionValidator()

    def test_construction(self) -> None:
        """Tests that the variables are initialized correctly."""
        self.assertEqual(None, self.validator._next_validator)
        self.assertEqual(None, self.validator.failing_validator)

    def test_set_next(self) -> None:
        """Tests that assigning the next validator works."""
        next_validator = Mock()
        self.validator.set_next(next_validator)
        self.assertEqual(next_validator, self.validator._next_validator)

    def test_validate(self) -> None:
        """Tests that base validator works, and that validators are called in chain."""
        self.assertTrue(self.validator.validate(Mock()))
        validate = Mock(return_value=False)
        next_validator = Mock(validate=validate)
        self.validator._next_validator = next_validator
        result = self.validator.validate(Mock())
        validate.assert_called_once()
        self.assertEqual(validate.return_value, result)

def test_construction(self) -> None:
    """Tests that the variables are initialized correctly."""
    self.assertEqual(None, self.validator._next_validator)
    self.assertEqual(None, self.validator.failing_validator)

def test_set_next(self) -> None:
    """Tests that assigning the next validator works."""
    next_validator = Mock()
    self.validator.set_next(next_validator)
    self.assertEqual(next_validator, self.validator._next_validator)

def test_validate(self) -> None:
    """Tests that base validator works, and that validators are called in chain."""
    self.assertTrue(self.validator.validate(Mock()))
    validate = Mock(return_value=False)
    next_validator = Mock(validate=validate)
    self.validator._next_validator = next_validator
    result = self.validator.validate(Mock())
    validate.assert_called_once()
    self.assertEqual(validate.return_value, result)

class TestImageExistsValidator(unittest.TestCase):
    """Tests for the ImageExistsValidator"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.validator = ImageExistsValidator()

    def test_construction(self) -> None:
        """Tests that the variables are initialized correctly."""
        self.assertTrue(isinstance(self.validator, BaseSubmissionValidator))

    @patch('docker.from_env')
    def test_validate(self, mock_env: Mock) -> None:
        """Tests that the validator behaves as intended"""
        missing_submission = 'foo'
        present_submission = 'bar'
        mock_env.return_value.images.list.return_value = ['bar', 'b']
        self.assertEqual(False, self.validator.validate(missing_submission))
        with patch.object(BaseSubmissionValidator, 'validate') as mock_validate:
            self.validator.validate(present_submission)
            mock_validate.assert_called_with(present_submission)

@patch('docker.from_env')
def test_validate(self, mock_env: Mock) -> None:
    """Tests that the validator behaves as intended"""
    missing_submission = 'foo'
    present_submission = 'bar'
    mock_env.return_value.images.list.return_value = ['bar', 'b']
    self.assertEqual(False, self.validator.validate(missing_submission))
    with patch.object(BaseSubmissionValidator, 'validate') as mock_validate:
        self.validator.validate(present_submission)
        mock_validate.assert_called_with(present_submission)

class TestSubmissionComputesTrajectoryValidator(unittest.TestCase):
    """Tests for SubmissionComputesTrajectoryValidator class"""

    def setUp(self) -> None:
        """Sets variables for testing"""
        self.submission_computes_trajectory_validator = SubmissionComputesTrajectoryValidator()

    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.get_test_nuplan_scenario', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationIteration', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationHistoryBuffer', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.PlannerInput', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SubmissionContainerFactory', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.RemotePlanner')
    def test_report_invalid_case(self, mock_remote_planner: Mock) -> None:
        """Tests that if a planner can't provide a trajectory, the validator fails"""
        submission = 'foo'
        mock_remote_planner().compute_trajectory.return_value = []
        valid = self.submission_computes_trajectory_validator.validate(submission)
        mock_remote_planner().compute_trajectory.assert_called()
        self.assertFalse(valid)
        self.assertEqual(self.submission_computes_trajectory_validator.failing_validator, SubmissionComputesTrajectoryValidator)

    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.get_test_nuplan_scenario', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationIteration', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationHistoryBuffer', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.PlannerInput', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.SubmissionContainerFactory', Mock())
    @patch('nuplan.submission.validators.submission_computes_trajectory_validator.RemotePlanner')
    def test_report_valid_case(self, mock_remote_planner: Mock) -> None:
        """Checks that the validator succeeds when the planner computes a trajectory"""
        submission = 'foo'
        mock_remote_planner().compute_trajectory.return_value = ['my', 'wonderful', 'trajectory']
        valid = self.submission_computes_trajectory_validator.validate(submission)
        mock_remote_planner().compute_trajectory.assert_called()
        self.assertTrue(valid)
        self.assertEqual(self.submission_computes_trajectory_validator.failing_validator, None)

@patch('nuplan.submission.validators.submission_computes_trajectory_validator.get_test_nuplan_scenario', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationIteration', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationHistoryBuffer', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.PlannerInput', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SubmissionContainerFactory', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.RemotePlanner')
def test_report_invalid_case(self, mock_remote_planner: Mock) -> None:
    """Tests that if a planner can't provide a trajectory, the validator fails"""
    submission = 'foo'
    mock_remote_planner().compute_trajectory.return_value = []
    valid = self.submission_computes_trajectory_validator.validate(submission)
    mock_remote_planner().compute_trajectory.assert_called()
    self.assertFalse(valid)
    self.assertEqual(self.submission_computes_trajectory_validator.failing_validator, SubmissionComputesTrajectoryValidator)

@patch('nuplan.submission.validators.submission_computes_trajectory_validator.get_test_nuplan_scenario', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationIteration', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SimulationHistoryBuffer', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.PlannerInput', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.SubmissionContainerFactory', Mock())
@patch('nuplan.submission.validators.submission_computes_trajectory_validator.RemotePlanner')
def test_report_valid_case(self, mock_remote_planner: Mock) -> None:
    """Checks that the validator succeeds when the planner computes a trajectory"""
    submission = 'foo'
    mock_remote_planner().compute_trajectory.return_value = ['my', 'wonderful', 'trajectory']
    valid = self.submission_computes_trajectory_validator.validate(submission)
    mock_remote_planner().compute_trajectory.assert_called()
    self.assertTrue(valid)
    self.assertEqual(self.submission_computes_trajectory_validator.failing_validator, None)

def s3_download_dir(bucket: str, client: boto3.client, prefix: str, local_path_name: str, filters: Optional[List[str]]=None) -> None:
    """
    Downloads targets matching a prefix from s3
    :param bucket: The s3 bucket
    :param client: The s3 client
    :param prefix: Prefix used to filer targets to download
    :param local_path_name: the base path
    :param filters: Keywords to filter paths, if empty no filtering is performed.
    """
    directories, keys = list_objects(bucket, client, prefix)
    _create_directories(local_path_name, directories)
    _download_files(bucket, client, local_path_name, keys, filters)

class TestAWSUtils(unittest.TestCase):
    """Tests for AWS utils."""

    def test__create_directories(self) -> None:
        """Checks the right number of directories is created."""
        local_path_name = 'base_path'
        directories = ['foo', 'bar']
        with patch(f'{TEST_FILE_PATH}.pathlib.Path.mkdir') as mock_mkdir:
            _create_directories(local_path_name, directories)
            self.assertEqual(2, mock_mkdir.call_count)

    @patch(f'{TEST_FILE_PATH}.pathlib.Path.mkdir', Mock)
    def test__download_files(self) -> None:
        """Checks the S3 client is used correctly."""
        mock_client = Mock()
        files = ['file1', 'file2']
        expected_calls = (call('bucket', 'file1', 'dest/file1'), call('bucket', 'file2', 'dest/file2'))
        _download_files('bucket', mock_client, 'dest', files)
        mock_client.download_file.assert_has_calls(expected_calls)

    @patch(f'{TEST_FILE_PATH}._create_directories')
    @patch(f'{TEST_FILE_PATH}._download_files', Mock)
    def test_s3_download_dir_empty(self, mock_dir_create: Mock) -> None:
        """Tests S3 download dir downloads correct targets."""
        mock_client = StubS3Client(empty=True)
        bucket = 'bucket'
        prefix = 'prefix'
        local_path_name = '/my/path'
        s3_download_dir(bucket, mock_client, prefix, local_path_name)
        mock_dir_create.assert_called_once_with(local_path_name, [])

    @patch(f'{TEST_FILE_PATH}._create_directories')
    @patch(f'{TEST_FILE_PATH}._download_files')
    def test_s3_download_dir(self, mock_download: Mock, mock_dir_create: Mock) -> None:
        """Tests S3 download dir downloads correct targets."""
        mock_client = StubS3Client(empty=False)
        bucket = 'bucket'
        prefix = 'prefix'
        local_path_name = '/my/path'
        s3_download_dir(bucket, mock_client, prefix, local_path_name)
        mock_dir_create.assert_called_once_with(local_path_name, ['prefix/'])
        mock_download.assert_called_once_with('bucket', mock_client, local_path_name, ['prefix/file'], None)

    @patch(f'{TEST_FILE_PATH}.boto3.client')
    @patch(f'{TEST_FILE_PATH}.s3_download_dir')
    @patch.dict(os.environ, {'NUPLAN_SERVER_AWS_ACCESS_KEY_ID': 'key', 'NUPLAN_SERVER_AWS_SECRET_ACCESS_KEY': 'secret', 'NUPLAN_SERVER_S3_ROOT_URL': 'bucket'}, clear=True)
    def test_s3_download(self, mock_download_dir: Mock, mock_client: Mock) -> None:
        """Tests S3 download calls the correct api."""
        s3_download('prefix', 'path')
        mock_client.assert_called_once_with('s3', aws_access_key_id='key', aws_secret_access_key='secret', region_name='us-east-1')
        mock_download_dir.assert_called_once_with('bucket', mock_client.return_value, 'prefix', 'path', None)

def test__create_directories(self) -> None:
    """Checks the right number of directories is created."""
    local_path_name = 'base_path'
    directories = ['foo', 'bar']
    with patch(f'{TEST_FILE_PATH}.pathlib.Path.mkdir') as mock_mkdir:
        _create_directories(local_path_name, directories)
        self.assertEqual(2, mock_mkdir.call_count)

@patch(f'{TEST_FILE_PATH}.pathlib.Path.mkdir', Mock)
def test__download_files(self) -> None:
    """Checks the S3 client is used correctly."""
    mock_client = Mock()
    files = ['file1', 'file2']
    expected_calls = (call('bucket', 'file1', 'dest/file1'), call('bucket', 'file2', 'dest/file2'))
    _download_files('bucket', mock_client, 'dest', files)
    mock_client.download_file.assert_has_calls(expected_calls)

@patch(f'{TEST_FILE_PATH}._create_directories')
@patch(f'{TEST_FILE_PATH}._download_files', Mock)
def test_s3_download_dir_empty(self, mock_dir_create: Mock) -> None:
    """Tests S3 download dir downloads correct targets."""
    mock_client = StubS3Client(empty=True)
    bucket = 'bucket'
    prefix = 'prefix'
    local_path_name = '/my/path'
    s3_download_dir(bucket, mock_client, prefix, local_path_name)
    mock_dir_create.assert_called_once_with(local_path_name, [])

@patch(f'{TEST_FILE_PATH}._create_directories')
@patch(f'{TEST_FILE_PATH}._download_files')
def test_s3_download_dir(self, mock_download: Mock, mock_dir_create: Mock) -> None:
    """Tests S3 download dir downloads correct targets."""
    mock_client = StubS3Client(empty=False)
    bucket = 'bucket'
    prefix = 'prefix'
    local_path_name = '/my/path'
    s3_download_dir(bucket, mock_client, prefix, local_path_name)
    mock_dir_create.assert_called_once_with(local_path_name, ['prefix/'])
    mock_download.assert_called_once_with('bucket', mock_client, local_path_name, ['prefix/file'], None)

@patch(f'{TEST_FILE_PATH}.boto3.client')
@patch(f'{TEST_FILE_PATH}.s3_download_dir')
@patch.dict(os.environ, {'NUPLAN_SERVER_AWS_ACCESS_KEY_ID': 'key', 'NUPLAN_SERVER_AWS_SECRET_ACCESS_KEY': 'secret', 'NUPLAN_SERVER_S3_ROOT_URL': 'bucket'}, clear=True)
def test_s3_download(self, mock_download_dir: Mock, mock_client: Mock) -> None:
    """Tests S3 download calls the correct api."""
    s3_download('prefix', 'path')
    mock_client.assert_called_once_with('s3', aws_access_key_id='key', aws_secret_access_key='secret', region_name='us-east-1')
    mock_download_dir.assert_called_once_with('bucket', mock_client.return_value, 'prefix', 'path', None)

class TestDetectionTracksChallengeServicer(TestCase):
    """Tests the DetectionTracksChallengeServicer class"""

    @patch('nuplan.submission.challenge_servicers.MapManager', return_value='map')
    def setUp(self, mock_map_manager: Mock) -> None:
        """Sets variables for testing"""
        mock_planner_cfg = {'planner1': Mock()}
        self.servicer = DetectionTracksChallengeServicer(mock_planner_cfg, mock_map_manager)

    @patch('nuplan.submission.challenge_servicers.MapManager', return_value='map')
    def test_initialization(self, mock_map_manager: Mock) -> None:
        """Tests that the class is initialized as intended."""
        mock_planner_cfg = Mock()
        mock_servicer = DetectionTracksChallengeServicer(mock_planner_cfg, mock_map_manager)
        self.assertEqual(mock_servicer.planner, None)
        self.assertEqual(mock_servicer._planner_config, mock_planner_cfg)
        self.assertEqual(mock_servicer.map_manager, mock_map_manager)

    @patch('nuplan.submission.challenge_servicers.MapManager')
    @patch('nuplan.submission.challenge_servicers.PlannerInitialization', autospec=True)
    @patch('nuplan.submission.challenge_servicers.se2_from_proto_se2')
    @patch('nuplan.submission.challenge_servicers.build_planners')
    def test_InitializePlanner(self, builder: Mock, mock_s2_conversion: Mock, mock_planner_initialization: Mock, mock_map_manager: Mock) -> None:
        """Tests the client call to InitializePlanner."""
        mock_input = Mock()
        mock_context = Mock()
        mock_map_api = Mock()
        mock_planner_initialization.return_value = 'planner_initialization'
        mock_map_manager.return_value = mock_map_api
        builder.return_value = [Mock()]
        self.servicer.InitializePlanner(mock_input, mock_context)
        calls = [call(mock_input.mission_goal)]
        mock_s2_conversion.assert_has_calls(calls)
        map_calls = [call(mock_input.map_name), call().initialize_all_layers()]
        self.servicer.map_manager.get_map.assert_has_calls(map_calls)
        self.servicer.planner.initialize.assert_called_once_with('planner_initialization')

    def test_ComputeTrajectory_uninitialized(self) -> None:
        """Tests the client call to ComputeTrajectory fails if the planner wasn't initialized."""
        with self.assertRaises(AssertionError, msg='Planner has not been initialized. Please call InitializePlanner'):
            self.servicer.simulation_history_buffers = []
            self.servicer.ComputeTrajectory(Mock(), Mock())

    @patch('nuplan.submission.challenge_servicers.proto_traj_from_inter_traj')
    def test_ComputeTrajectory(self, proto_traj_from_inter_traj: Mock) -> None:
        """Tests the client call to ComputeTrajectory."""
        mock_context = Mock()
        self.servicer.planner = Mock(spec=AbstractPlanner)
        self.servicer.planner.compute_trajectory.return_value = 'trajectory'
        self.servicer.simulation_history_buffer = 'buffer_1'
        self.servicer._initialized = True
        history_buffer = MagicMock(ego_states=['ego_state_1'], observations=['observation_1'])
        simulation_iteration = MagicMock(time_us=123, index=234)
        mock_serialized_input = MagicMock(simulation_history_buffer=history_buffer, simulation_iteration=simulation_iteration)
        with patch.object(self.servicer, '_build_planner_input', autospec=True) as build_planner_input:
            result = self.servicer.ComputeTrajectory(mock_serialized_input, mock_context)
            build_planner_input.assert_called_with(mock_serialized_input, 'buffer_1')
            self.servicer.planner.compute_trajectory.assert_called_with(build_planner_input.return_value)
            proto_traj_from_inter_traj.assert_called_with(self.servicer.planner.compute_trajectory.return_value)
            self.assertEqual(proto_traj_from_inter_traj.return_value, result)

    @patch('nuplan.submission.challenge_servicers.SimulationIteration', autospec=True)
    @patch('nuplan.submission.challenge_servicers.TimePoint', autospec=True)
    def test__extract_simulation_iteration(self, time_point: Mock, simulation_iteration: Mock) -> None:
        """Tests extraction of simulation iteration data from serialized message"""
        mock_iteration = Mock(time_us=123, index=456, spec_set=SerializedSimulationIteration)
        mock_message = Mock(simulation_iteration=mock_iteration, spec_set=SerializedPlannerInput)
        result = self.servicer._extract_simulation_iteration(mock_message)
        time_point.assert_called_once_with(123)
        simulation_iteration.assert_called_once_with(time_point.return_value, 456)
        self.assertEqual(simulation_iteration.return_value, result)

    @patch('pickle.loads')
    @patch('nuplan.submission.challenge_servicers.PlannerInput', autospec=True)
    @patch('nuplan.submission.challenge_servicers.SimulationHistoryBuffer', autospec=True)
    def test__build_planner_input(self, buffer: MagicMock, planner_input: Mock, loads: Mock) -> None:
        """Tests that planner input is correctly deserialized"""
        mock_serialized_buffer = Mock(ego_states=['ego_state'], observations=['observations'], sample_interval=['sample_interval'], spec_set=SerializedHistoryBuffer)
        mock_message = MagicMock(simulation_history_buffer=mock_serialized_buffer, spec_set=SerializedPlannerInput)
        loads.side_effect = ['deserialized_ego_state', 'deserialized_observations']
        with patch.object(self.servicer, '_extract_simulation_iteration', autospec=True) as extract_iteration:
            result = self.servicer._build_planner_input(mock_message, buffer)
            extract_iteration.assert_called_with(mock_message)
            loads.assert_has_calls([call('ego_state'), call('observations')])
            buffer.extend.assert_called_once_with(['deserialized_ego_state'], ['deserialized_observations'])
            self.assertEqual(planner_input.return_value, result)

    @patch('pickle.loads')
    @patch('nuplan.submission.challenge_servicers.PlannerInput', autospec=True)
    @patch('nuplan.submission.challenge_servicers.SimulationHistoryBuffer', autospec=True)
    def test__build_planner_input_no_buffer(self, buffer: MagicMock, planner_input: Mock, loads: Mock) -> None:
        """Tests that planner input is correctly deserialized"""
        mock_serialized_buffer = Mock(ego_states=['ego_state'], observations=['observations'], sample_interval=['sample_interval'], spec_set=SerializedHistoryBuffer)
        mock_message = MagicMock(simulation_history_buffer=mock_serialized_buffer, spec_set=SerializedPlannerInput)
        loads.side_effect = ['deserialized_ego_state', 'deserialized_observations']
        with patch.object(self.servicer, '_extract_simulation_iteration', autospec=True):
            self.servicer.simulation_history_buffers = [mock_serialized_buffer]
            result = self.servicer._build_planner_input(mock_message, None)
            buffer.initialize_from_list.assert_called_once_with(1, ['deserialized_ego_state'], ['deserialized_observations'], ['sample_interval'])
            self.assertEqual(planner_input.return_value, result)

@patch('nuplan.submission.challenge_servicers.MapManager', return_value='map')
def setUp(self, mock_map_manager: Mock) -> None:
    """Sets variables for testing"""
    mock_planner_cfg = {'planner1': Mock()}
    self.servicer = DetectionTracksChallengeServicer(mock_planner_cfg, mock_map_manager)

@patch('nuplan.submission.challenge_servicers.MapManager', return_value='map')
def test_initialization(self, mock_map_manager: Mock) -> None:
    """Tests that the class is initialized as intended."""
    mock_planner_cfg = Mock()
    mock_servicer = DetectionTracksChallengeServicer(mock_planner_cfg, mock_map_manager)
    self.assertEqual(mock_servicer.planner, None)
    self.assertEqual(mock_servicer._planner_config, mock_planner_cfg)
    self.assertEqual(mock_servicer.map_manager, mock_map_manager)

@patch('nuplan.submission.challenge_servicers.MapManager')
@patch('nuplan.submission.challenge_servicers.PlannerInitialization', autospec=True)
@patch('nuplan.submission.challenge_servicers.se2_from_proto_se2')
@patch('nuplan.submission.challenge_servicers.build_planners')
def test_InitializePlanner(self, builder: Mock, mock_s2_conversion: Mock, mock_planner_initialization: Mock, mock_map_manager: Mock) -> None:
    """Tests the client call to InitializePlanner."""
    mock_input = Mock()
    mock_context = Mock()
    mock_map_api = Mock()
    mock_planner_initialization.return_value = 'planner_initialization'
    mock_map_manager.return_value = mock_map_api
    builder.return_value = [Mock()]
    self.servicer.InitializePlanner(mock_input, mock_context)
    calls = [call(mock_input.mission_goal)]
    mock_s2_conversion.assert_has_calls(calls)
    map_calls = [call(mock_input.map_name), call().initialize_all_layers()]
    self.servicer.map_manager.get_map.assert_has_calls(map_calls)
    self.servicer.planner.initialize.assert_called_once_with('planner_initialization')

def test_ComputeTrajectory_uninitialized(self) -> None:
    """Tests the client call to ComputeTrajectory fails if the planner wasn't initialized."""
    with self.assertRaises(AssertionError, msg='Planner has not been initialized. Please call InitializePlanner'):
        self.servicer.simulation_history_buffers = []
        self.servicer.ComputeTrajectory(Mock(), Mock())

@patch('nuplan.submission.challenge_servicers.proto_traj_from_inter_traj')
def test_ComputeTrajectory(self, proto_traj_from_inter_traj: Mock) -> None:
    """Tests the client call to ComputeTrajectory."""
    mock_context = Mock()
    self.servicer.planner = Mock(spec=AbstractPlanner)
    self.servicer.planner.compute_trajectory.return_value = 'trajectory'
    self.servicer.simulation_history_buffer = 'buffer_1'
    self.servicer._initialized = True
    history_buffer = MagicMock(ego_states=['ego_state_1'], observations=['observation_1'])
    simulation_iteration = MagicMock(time_us=123, index=234)
    mock_serialized_input = MagicMock(simulation_history_buffer=history_buffer, simulation_iteration=simulation_iteration)
    with patch.object(self.servicer, '_build_planner_input', autospec=True) as build_planner_input:
        result = self.servicer.ComputeTrajectory(mock_serialized_input, mock_context)
        build_planner_input.assert_called_with(mock_serialized_input, 'buffer_1')
        self.servicer.planner.compute_trajectory.assert_called_with(build_planner_input.return_value)
        proto_traj_from_inter_traj.assert_called_with(self.servicer.planner.compute_trajectory.return_value)
        self.assertEqual(proto_traj_from_inter_traj.return_value, result)

@patch('nuplan.submission.challenge_servicers.SimulationIteration', autospec=True)
@patch('nuplan.submission.challenge_servicers.TimePoint', autospec=True)
def test__extract_simulation_iteration(self, time_point: Mock, simulation_iteration: Mock) -> None:
    """Tests extraction of simulation iteration data from serialized message"""
    mock_iteration = Mock(time_us=123, index=456, spec_set=SerializedSimulationIteration)
    mock_message = Mock(simulation_iteration=mock_iteration, spec_set=SerializedPlannerInput)
    result = self.servicer._extract_simulation_iteration(mock_message)
    time_point.assert_called_once_with(123)
    simulation_iteration.assert_called_once_with(time_point.return_value, 456)
    self.assertEqual(simulation_iteration.return_value, result)

@patch('pickle.loads')
@patch('nuplan.submission.challenge_servicers.PlannerInput', autospec=True)
@patch('nuplan.submission.challenge_servicers.SimulationHistoryBuffer', autospec=True)
def test__build_planner_input(self, buffer: MagicMock, planner_input: Mock, loads: Mock) -> None:
    """Tests that planner input is correctly deserialized"""
    mock_serialized_buffer = Mock(ego_states=['ego_state'], observations=['observations'], sample_interval=['sample_interval'], spec_set=SerializedHistoryBuffer)
    mock_message = MagicMock(simulation_history_buffer=mock_serialized_buffer, spec_set=SerializedPlannerInput)
    loads.side_effect = ['deserialized_ego_state', 'deserialized_observations']
    with patch.object(self.servicer, '_extract_simulation_iteration', autospec=True) as extract_iteration:
        result = self.servicer._build_planner_input(mock_message, buffer)
        extract_iteration.assert_called_with(mock_message)
        loads.assert_has_calls([call('ego_state'), call('observations')])
        buffer.extend.assert_called_once_with(['deserialized_ego_state'], ['deserialized_observations'])
        self.assertEqual(planner_input.return_value, result)

@patch('pickle.loads')
@patch('nuplan.submission.challenge_servicers.PlannerInput', autospec=True)
@patch('nuplan.submission.challenge_servicers.SimulationHistoryBuffer', autospec=True)
def test__build_planner_input_no_buffer(self, buffer: MagicMock, planner_input: Mock, loads: Mock) -> None:
    """Tests that planner input is correctly deserialized"""
    mock_serialized_buffer = Mock(ego_states=['ego_state'], observations=['observations'], sample_interval=['sample_interval'], spec_set=SerializedHistoryBuffer)
    mock_message = MagicMock(simulation_history_buffer=mock_serialized_buffer, spec_set=SerializedPlannerInput)
    loads.side_effect = ['deserialized_ego_state', 'deserialized_observations']
    with patch.object(self.servicer, '_extract_simulation_iteration', autospec=True):
        self.servicer.simulation_history_buffers = [mock_serialized_buffer]
        result = self.servicer._build_planner_input(mock_message, None)
        buffer.initialize_from_list.assert_called_once_with(1, ['deserialized_ego_state'], ['deserialized_observations'], ['sample_interval'])
        self.assertEqual(planner_input.return_value, result)

class TestSubmissionPlanner(TestCase):
    """Tests for SubmissionPlanner class"""

    @patch('os.getenv', MagicMock())
    @patch('grpc.server', Mock())
    @patch('nuplan.submission.submission_planner.chpb_grpc', Mock())
    @patch('nuplan.submission.submission_planner.MapManager', Mock())
    @patch('nuplan.submission.submission_planner.NuPlanMapFactory', Mock())
    @patch('nuplan.submission.submission_planner.GPKGMapsDB', Mock())
    @patch('nuplan.submission.challenge_servicers.DetectionTracksChallengeServicer', Mock())
    def setUp(self) -> None:
        """Sets variables for testing"""
        mock_planner = Mock()
        self.submission_planner = SubmissionPlanner(mock_planner)

    @patch('os.getenv')
    @patch('grpc.server')
    @patch('nuplan.submission.submission_planner.chpb_grpc')
    @patch('nuplan.submission.submission_planner.MapManager', Mock())
    @patch('nuplan.submission.submission_planner.NuPlanMapFactory', Mock())
    @patch('nuplan.submission.submission_planner.GPKGMapsDB', Mock())
    @patch('nuplan.submission.submission_planner.DetectionTracksChallengeServicer')
    def test_initialization(self, mock_servicer: Mock, mock_grpc: Mock, mock_server: Mock, mock_getenv: Mock) -> None:
        """Tests that the class is initialized as intended."""
        mock_getenv.return_value = '1234'
        mock_submission_planner = SubmissionPlanner(Mock())
        args = (mock_servicer(), mock_server())
        mock_grpc.add_DetectionTracksChallengeServicer_to_server.assert_called_with(*args)
        mock_submission_planner.server.add_insecure_port.assert_called_with('[::]:1234')
        mock_getenv.return_value = ''
        with self.assertRaises(RuntimeError):
            _ = SubmissionPlanner(Mock())

    def test_serve(self) -> None:
        """Tests that the submission planner correctly starts the server."""
        self.submission_planner.serve()
        self.submission_planner.server.start.assert_called_once()
        self.submission_planner.server.wait_for_termination.assert_called_once()

@patch('os.getenv', MagicMock())
@patch('grpc.server', Mock())
@patch('nuplan.submission.submission_planner.chpb_grpc', Mock())
@patch('nuplan.submission.submission_planner.MapManager', Mock())
@patch('nuplan.submission.submission_planner.NuPlanMapFactory', Mock())
@patch('nuplan.submission.submission_planner.GPKGMapsDB', Mock())
@patch('nuplan.submission.challenge_servicers.DetectionTracksChallengeServicer', Mock())
def setUp(self) -> None:
    """Sets variables for testing"""
    mock_planner = Mock()
    self.submission_planner = SubmissionPlanner(mock_planner)

@patch('os.getenv')
@patch('grpc.server')
@patch('nuplan.submission.submission_planner.chpb_grpc')
@patch('nuplan.submission.submission_planner.MapManager', Mock())
@patch('nuplan.submission.submission_planner.NuPlanMapFactory', Mock())
@patch('nuplan.submission.submission_planner.GPKGMapsDB', Mock())
@patch('nuplan.submission.submission_planner.DetectionTracksChallengeServicer')
def test_initialization(self, mock_servicer: Mock, mock_grpc: Mock, mock_server: Mock, mock_getenv: Mock) -> None:
    """Tests that the class is initialized as intended."""
    mock_getenv.return_value = '1234'
    mock_submission_planner = SubmissionPlanner(Mock())
    args = (mock_servicer(), mock_server())
    mock_grpc.add_DetectionTracksChallengeServicer_to_server.assert_called_with(*args)
    mock_submission_planner.server.add_insecure_port.assert_called_with('[::]:1234')
    mock_getenv.return_value = ''
    with self.assertRaises(RuntimeError):
        _ = SubmissionPlanner(Mock())

def test_serve(self) -> None:
    """Tests that the submission planner correctly starts the server."""
    self.submission_planner.serve()
    self.submission_planner.server.start.assert_called_once()
    self.submission_planner.server.wait_for_termination.assert_called_once()

class TestSubmissionContainerFactory(unittest.TestCase):
    """Tests for SubmissionContainerFactory class"""

    @patch('nuplan.submission.submission_container_factory.SubmissionContainer')
    def test_build_submission_container(self, mock_submission_container: Mock) -> None:
        """Tests that the submission container factory correctly calls the builder."""
        submission_image = 'foo'
        container_name = 'bar'
        port = 1234
        _ = SubmissionContainerFactory.build_submission_container(submission_image, container_name, port)
        mock_submission_container.assert_called_with(submission_image, container_name, port)

@patch('nuplan.submission.submission_container_factory.SubmissionContainer')
def test_build_submission_container(self, mock_submission_container: Mock) -> None:
    """Tests that the submission container factory correctly calls the builder."""
    submission_image = 'foo'
    container_name = 'bar'
    port = 1234
    _ = SubmissionContainerFactory.build_submission_container(submission_image, container_name, port)
    mock_submission_container.assert_called_with(submission_image, container_name, port)

class TestSubmissionContainerManager(unittest.TestCase):
    """Tests for SubmissionContainerManager class"""

    @patch('nuplan.submission.submission_container_manager.SubmissionContainerFactory')
    def setUp(self, mock_container_factory: Mock) -> None:
        """Sets variables for testing"""
        self.container_manager = SubmissionContainerManager(mock_container_factory)

    @patch('nuplan.submission.submission_container_manager.SubmissionContainerFactory')
    def test_initialization(self, mock_container_factory: Mock) -> None:
        """Tests that objects are initialized correctly."""
        submission_container_manager = SubmissionContainerManager(mock_container_factory)
        self.assertEqual(mock_container_factory, submission_container_manager.submission_container_factory)
        self.assertEqual({}, submission_container_manager.submission_containers)

    def test_get_submission_container(self) -> None:
        """Tests that maps are retrieved from cache, if not present created and added to it."""
        image_name = 'image_name'
        container_name = 'container_name'
        port = 123
        self.container_manager.submission_container_factory.build_submission_container.return_value = 'container'
        _container = self.container_manager.get_submission_container(image_name, container_name, port)
        self.container_manager.submission_container_factory.build_submission_container.assert_called_once_with(image_name, container_name, port)
        self.assertTrue(container_name in self.container_manager.submission_containers)
        self.assertEqual('container', _container)
        _ = self.container_manager.get_submission_container(image_name, container_name, port)
        self.container_manager.submission_container_factory.build_submission_container.assert_called_once_with(image_name, container_name, port)

@patch('nuplan.submission.submission_container_manager.SubmissionContainerFactory')
def setUp(self, mock_container_factory: Mock) -> None:
    """Sets variables for testing"""
    self.container_manager = SubmissionContainerManager(mock_container_factory)

@patch('nuplan.submission.submission_container_manager.SubmissionContainerFactory')
def test_initialization(self, mock_container_factory: Mock) -> None:
    """Tests that objects are initialized correctly."""
    submission_container_manager = SubmissionContainerManager(mock_container_factory)
    self.assertEqual(mock_container_factory, submission_container_manager.submission_container_factory)
    self.assertEqual({}, submission_container_manager.submission_containers)

def test_get_submission_container(self) -> None:
    """Tests that maps are retrieved from cache, if not present created and added to it."""
    image_name = 'image_name'
    container_name = 'container_name'
    port = 123
    self.container_manager.submission_container_factory.build_submission_container.return_value = 'container'
    _container = self.container_manager.get_submission_container(image_name, container_name, port)
    self.container_manager.submission_container_factory.build_submission_container.assert_called_once_with(image_name, container_name, port)
    self.assertTrue(container_name in self.container_manager.submission_containers)
    self.assertEqual('container', _container)
    _ = self.container_manager.get_submission_container(image_name, container_name, port)
    self.container_manager.submission_container_factory.build_submission_container.assert_called_once_with(image_name, container_name, port)

class TestUtils(unittest.TestCase):
    """Tests for util functions"""

    @patch('socket.socket')
    def test_find_port(self, mock_socket: Mock) -> None:
        """Test that method uses socket to find a free port, and returns it."""
        mock_socket().getsockname.return_value = [0, '1234']
        port = find_free_port_number()
        mock_socket().bind.assert_called_once_with(('', 0))
        mock_socket().close.assert_called_once()
        self.assertEqual(1234, port)

@patch('socket.socket')
def test_find_port(self, mock_socket: Mock) -> None:
    """Test that method uses socket to find a free port, and returns it."""
    mock_socket().getsockname.return_value = [0, '1234']
    port = find_free_port_number()
    mock_socket().bind.assert_called_once_with(('', 0))
    mock_socket().close.assert_called_once()
    self.assertEqual(1234, port)

class TestSubmissionContainer(TestCase):
    """Tests for SubmissionContainer class"""

    @patch('docker.from_env')
    def setUp(self, mock_from_env: Mock) -> None:
        """Sets variables for testing"""
        self.manager = SubmissionContainer(submission_image='foo/bar', container_name='foo_bar', port=314)

    @patch('docker.from_env', Mock())
    def test_initialization(self) -> None:
        """Tests that the container manager gets initialized correctly."""
        mock_manager = SubmissionContainer(submission_image='foo/bar', container_name='foo_bar', port=314)
        self.assertEqual('foo/bar', mock_manager.submission_image)
        self.assertEqual('foo_bar', mock_manager.container_name)
        self.assertEqual(314, mock_manager.port)

    @patch('docker.from_env')
    @patch.object(SubmissionContainer, 'stop')
    def test_start_submission_container(self, mock_stop_submission_container: Mock, mock_from_env: Mock) -> None:
        """Tests that the container is run with the correct arguments."""
        mock_env = Mock()
        mock_from_env.return_value = mock_env
        mock_env.containers.get.return_value = 'test_container'
        test_container = self.manager.start()
        mock_stop_submission_container.assert_called_once()
        self.manager.client.containers.run.assert_called_with('foo/bar', name='foo_bar', detach=True, ports={'314': 314}, tty=True, environment={'SUBMISSION_CONTAINER_PORT': '314'}, device_requests=[{'Driver': '', 'Count': 0, 'DeviceIDs': ['0'], 'Capabilities': [['gpu']], 'Options': {}}], cpuset_cpus='0,1', volumes={'/data/sets/nuplan': {'bind': '/data/sets/nuplan', 'mode': 'ro'}})
        self.assertEqual('test_container', test_container)

    def test_stop_missing_container(self) -> None:
        """Checks that trying to remove a missing container does not fail (is intended behavior)"""
        mock_container = Mock()
        self.manager.client = Mock()
        self.manager.client.containers.get.side_effect = ContainerNotFound('Container not found')
        self.manager.client.containers.get.return_value = mock_container
        self.manager.stop()
        self.manager.client.containers.get.assert_called_once()
        mock_container.stop.assert_not_called()
        mock_container.remove.assert_not_called()

    def test_stop_existing_container(self) -> None:
        """Checks that if a running container is found, it is stopped and removed."""
        mock_container = Mock()
        self.manager.client = Mock()
        self.manager.client.containers.get.return_value = mock_container
        self.manager.stop()
        self.manager.client.containers.get.assert_called_once()
        mock_container.kill.assert_called_once()
        mock_container.remove.assert_called_once()

@patch('docker.from_env')
def setUp(self, mock_from_env: Mock) -> None:
    """Sets variables for testing"""
    self.manager = SubmissionContainer(submission_image='foo/bar', container_name='foo_bar', port=314)

@patch('docker.from_env', Mock())
def test_initialization(self) -> None:
    """Tests that the container manager gets initialized correctly."""
    mock_manager = SubmissionContainer(submission_image='foo/bar', container_name='foo_bar', port=314)
    self.assertEqual('foo/bar', mock_manager.submission_image)
    self.assertEqual('foo_bar', mock_manager.container_name)
    self.assertEqual(314, mock_manager.port)

@patch('docker.from_env')
@patch.object(SubmissionContainer, 'stop')
def test_start_submission_container(self, mock_stop_submission_container: Mock, mock_from_env: Mock) -> None:
    """Tests that the container is run with the correct arguments."""
    mock_env = Mock()
    mock_from_env.return_value = mock_env
    mock_env.containers.get.return_value = 'test_container'
    test_container = self.manager.start()
    mock_stop_submission_container.assert_called_once()
    self.manager.client.containers.run.assert_called_with('foo/bar', name='foo_bar', detach=True, ports={'314': 314}, tty=True, environment={'SUBMISSION_CONTAINER_PORT': '314'}, device_requests=[{'Driver': '', 'Count': 0, 'DeviceIDs': ['0'], 'Capabilities': [['gpu']], 'Options': {}}], cpuset_cpus='0,1', volumes={'/data/sets/nuplan': {'bind': '/data/sets/nuplan', 'mode': 'ro'}})
    self.assertEqual('test_container', test_container)

def test_stop_missing_container(self) -> None:
    """Checks that trying to remove a missing container does not fail (is intended behavior)"""
    mock_container = Mock()
    self.manager.client = Mock()
    self.manager.client.containers.get.side_effect = ContainerNotFound('Container not found')
    self.manager.client.containers.get.return_value = mock_container
    self.manager.stop()
    self.manager.client.containers.get.assert_called_once()
    mock_container.stop.assert_not_called()
    mock_container.remove.assert_not_called()

def test_stop_existing_container(self) -> None:
    """Checks that if a running container is found, it is stopped and removed."""
    mock_container = Mock()
    self.manager.client = Mock()
    self.manager.client.containers.get.return_value = mock_container
    self.manager.stop()
    self.manager.client.containers.get.assert_called_once()
    mock_container.kill.assert_called_once()
    mock_container.remove.assert_called_once()

