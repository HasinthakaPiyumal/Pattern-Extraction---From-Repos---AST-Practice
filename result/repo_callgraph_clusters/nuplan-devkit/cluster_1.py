# Cluster 1

def _create_dummy_simple_planner(acceleration: List[float], horizon_seconds: float=10.0, sampling_time: float=20.0) -> SimplePlanner:
    """
    Create a dummy simple planner.
    :param acceleration: [m/s^2] constant ego acceleration, till limited by max_velocity.
    :param horizon_seconds: [s] time horizon being run.
    :param sampling_time: [s] sampling timestep.
    :return: dummy simple planner.
    """
    acceleration_np: npt.NDArray[np.float32] = np.asarray(acceleration)
    return SimplePlanner(horizon_seconds=horizon_seconds, sampling_time=sampling_time, acceleration=acceleration_np)

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

def _patch_db_duration(log_name: str) -> int:
    """
            A patch for the get_db_duration function.
            """
    self.assertEqual('expected_log_name', log_name)
    return int(125 * 1000000.0)

def _patch_db_log_duration(log_name: str) -> Generator[Tuple[str, int], None, None]:
    """
            Patch for get_db_log_duration function.
            """
    self.assertEqual('expected_log_name', log_name)
    for i in range(0, 3, 1):
        yield (f'log_file_{i}', int((i + 1) * 67 * 1000000.0))

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

@property
def timestamp(self) -> int:
    """
        Returns the timestamp of the LidarBox.
        :return: The timestamp of the lidar box.
        """
    return int(self.lidar_pc.timestamp)

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

def _waypoint_from_lidar_box(lidar_box: LidarBox) -> Waypoint:
    """
    Creates a Waypoint from a LidarBox
    :param lidar_box: the input LidarBox
    :return: the corresponding Waypoint
    """
    pose = StateSE2(lidar_box.translation[0], lidar_box.translation[1], lidar_box.yaw)
    oriented_box = OrientedBox(pose, width=lidar_box.size[0], length=lidar_box.size[1], height=lidar_box.size[2])
    velocity = StateVector2D(lidar_box.vx, lidar_box.vy)
    waypoint = Waypoint(TimePoint(lidar_box.timestamp), oriented_box, velocity)
    return waypoint

def interpolate_waypoints(waypoints: List[Waypoint], trajectory_sampling: TrajectorySampling) -> List[Waypoint]:
    """
    Interpolates a list of waypoints given sampling time and horizon, starting at the first waypoint timestamp.
    :param waypoints: The sample waypoints
    :param trajectory_sampling: The sampling parameters
    :return: A list of interpolated waypoints
    """
    waypoint_trajectory = InterpolatedTrajectory(waypoints)
    start_time_us = waypoints[0].time_us
    end_time_us = waypoints[-1].time_us
    time_horizon_us = int(trajectory_sampling.time_horizon * 1000000.0)
    step_time_us = int(trajectory_sampling.step_time * 1000000.0)
    max_horizon_time = min(end_time_us, start_time_us + time_horizon_us + step_time_us)
    interpolation_times = np.arange(start_time_us, max_horizon_time, step_time_us)
    interpolated_waypoints = [waypoint_trajectory.get_state_at_time(TimePoint(int(interpolation_time))) for interpolation_time in interpolation_times]
    return interpolated_waypoints

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

def nbr_points(self) -> int:
    """
        Returns the number of points.
        :return: Number of points.
        """
    return int(self.points.shape[1])

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

def get_map_dimension(self) -> Tuple[int, int]:
    """
        Gets the dimension of the map.
        :return: The dimension of the map.
        """
    map_dims = self._maps_db._map_dimensions[self._map_name]
    return (int(map_dims[0]), int(map_dims[1]))

def _parse_tracked_object_row(row: sqlite3.Row) -> TrackedObject:
    """
    A convenience method to parse a TrackedObject from a sqlite3 row.
    :param row: The row from the DB query.
    :return: The parsed TrackedObject.
    """
    category_name = row['category_name']
    pose = StateSE2(row['x'], row['y'], row['yaw'])
    oriented_box = OrientedBox(pose, width=row['width'], length=row['length'], height=row['height'])
    label_local = raw_mapping['global2local'][category_name]
    tracked_object_type = TrackedObjectType[local2agent_type[label_local]]
    if tracked_object_type in AGENT_TYPES:
        return Agent(tracked_object_type=tracked_object_type, oriented_box=oriented_box, velocity=StateVector2D(row['vx'], row['vy']), predictions=[], angular_velocity=np.nan, metadata=SceneObjectMetadata(token=row['token'].hex(), track_token=row['track_token'].hex(), track_id=get_unique_incremental_track_id(str(row['track_token'].hex())), timestamp_us=row['timestamp'], category_name=category_name))
    else:
        return StaticObject(tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=SceneObjectMetadata(token=row['token'].hex(), track_token=row['track_token'].hex(), track_id=get_unique_incremental_track_id(str(row['track_token'].hex())), timestamp_us=row['timestamp'], category_name=category_name))

def str_token_to_int(val: Optional[str]) -> Optional[int]:
    """
    Convert a string token previously genreated with int_to_str_token() back to an int.
    :param val: The token to convert.
    :return: None if the input is None. Else, the int version of the string.
        The output is undefined if the token was not generated with int_to_str_token().
    """
    return None if val is None else int(val)

def _generate_mapping_keys(db_generation_parameters: DBGenerationParameters) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate all the FK mappings between the generated tables based on the provided parameters.
    :param db_generation_parameters: The generation parameters to use.
    :return: Dicts containing the FK information for each table.
    """
    token_dicts: Dict[str, List[Dict[str, Any]]] = {'lidar_pc': [], 'lidar': [], 'image': [], 'camera': [], 'ego_pose': [], 'track': [], 'lidar_box': [], 'scene': [], 'traffic_light_status': [], 'category': [], 'scenario_tag': []}
    num_pc_tokens_per_scene = int(db_generation_parameters.num_sensor_data_per_sensor / db_generation_parameters.num_scenes)
    base_token_multiplier = 100000
    offset_scene_token = 1 * base_token_multiplier
    offset_ego_pose_token = 3 * base_token_multiplier
    offset_traffic_light_status_token = 4 * base_token_multiplier
    offset_lidar_box_token = 5 * base_token_multiplier
    offset_track_token_token = 6 * base_token_multiplier
    offset_lidar_token = 7 * base_token_multiplier
    offset_scenario_tag_token = 8 * base_token_multiplier
    offset_agents_token = 9 * base_token_multiplier
    offset_static_objects_token = 9 * base_token_multiplier + 5
    offset_camera_token = 10 * base_token_multiplier
    offset_image_token = 11 * base_token_multiplier
    step_traffic_light_status_pc = 10000
    step_lidar_box_pc = 10000
    _generate_camera_data(db_generation_parameters, token_dicts, offset_image_token, offset_camera_token, offset_ego_pose_token)
    for sensor_idx in range(db_generation_parameters.num_lidars):
        lidar_token = offset_lidar_token + sensor_idx
        lidar_channel_name = 'channel' if sensor_idx < 1 else f'channel_{sensor_idx}'
        for sensor_data_idx in range(db_generation_parameters.num_sensor_data_per_sensor):
            lidar_pc_token = sensor_data_idx + sensor_idx * db_generation_parameters.num_sensor_data_per_sensor
            scene_token = int(sensor_data_idx / num_pc_tokens_per_scene) + offset_scene_token
            ego_pose_token = sensor_data_idx + offset_ego_pose_token
            timestamp_ego_pose = sensor_data_idx * 1000000.0
            timestamp_lidar_pc = timestamp_ego_pose + sensor_idx
            next_lidar_pc = {'lidar_pc_token': lidar_pc_token, 'prev_lidar_pc_token': None if sensor_data_idx == 0 else sensor_data_idx - 1, 'next_lidar_pc_token': None if sensor_data_idx == db_generation_parameters.num_sensor_data_per_sensor - 1 else sensor_data_idx + 1, 'scene_token': scene_token, 'ego_pose_token': ego_pose_token, 'lidar_token': lidar_token, 'lidar_pc_timestamp': timestamp_lidar_pc}
            token_dicts['lidar_pc'].append(next_lidar_pc)
            ego_pose_entry = {'token': ego_pose_token, 'timestamp': timestamp_ego_pose + 333}
            if ego_pose_entry not in token_dicts['ego_pose']:
                token_dicts['ego_pose'].append(ego_pose_entry)
            lidar_token_entry = {'token': lidar_token, 'channel': lidar_channel_name}
            if lidar_token_entry not in token_dicts['lidar']:
                token_dicts['lidar'].append(lidar_token_entry)
            for traffic_light_idx in range(db_generation_parameters.num_traffic_lights_per_lidar_pc):
                statuses = ['green', 'red', 'yellow', 'unknown']
                traffic_light_status_entry = {'token': offset_traffic_light_status_token + sensor_data_idx * step_traffic_light_status_pc + traffic_light_idx, 'lidar_pc_token': sensor_data_idx, 'lane_connector_id': traffic_light_idx, 'status': statuses[(offset_traffic_light_status_token + traffic_light_idx) % len(statuses)]}
                if traffic_light_status_entry not in token_dicts['traffic_light_status']:
                    token_dicts['traffic_light_status'].append(traffic_light_status_entry)
            for object_idx in range(db_generation_parameters.total_object_count()):
                lidar_box_entry = {'token': offset_lidar_box_token + sensor_data_idx * step_lidar_box_pc + object_idx, 'lidar_pc_token': sensor_data_idx, 'track_token': offset_track_token_token + object_idx, 'prev_token': None if sensor_data_idx == 0 else offset_lidar_box_token + (sensor_data_idx - 1) * step_lidar_box_pc + object_idx, 'next_token': None if sensor_data_idx == db_generation_parameters.num_sensor_data_per_sensor - 1 else offset_lidar_box_token + (sensor_data_idx + 1) * step_lidar_box_pc + object_idx}
                if lidar_box_entry not in token_dicts['lidar_box']:
                    token_dicts['lidar_box'].append(lidar_box_entry)
            if sensor_data_idx % num_pc_tokens_per_scene == 0:
                scene_token_entry = {'token': scene_token, 'ego_pose_token': ego_pose_token + num_pc_tokens_per_scene - 1, 'name': 'scene-{:03d}'.format(int(sensor_data_idx / num_pc_tokens_per_scene))}
                if scene_token_entry not in token_dicts['scene']:
                    token_dicts['scene'].append(scene_token_entry)
                scene_idx = sensor_data_idx // num_pc_tokens_per_scene
                if scene_idx in db_generation_parameters.scene_scenario_tag_mapping and lidar_channel_name == 'channel':
                    tags = db_generation_parameters.scene_scenario_tag_mapping[scene_idx]
                    for tag in tags:
                        row = {'token': offset_scenario_tag_token + len(token_dicts['scenario_tag']), 'lidar_pc_token': lidar_pc_token, 'type': tag}
                        token_dicts['scenario_tag'].append(row)
    for lidar_pc_idx in range(db_generation_parameters.total_object_count()):
        token_dicts['track'].append({'token': offset_track_token_token + lidar_pc_idx, 'category_token': offset_agents_token if lidar_pc_idx < db_generation_parameters.num_agents_per_lidar_pc else offset_static_objects_token})
    return token_dicts

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

def test_get_sampled_sensor_tokens_in_time_window_from_db(self) -> None:
    """
        Test the get_sampled_lidarpc_tokens_in_time_window_from_db query.
        """
    expected_tokens = [10, 13, 16, 19]
    actual_tokens = list((str_token_to_int(v) for v in get_sampled_sensor_tokens_in_time_window_from_db(log_file=self.db_file_name, sensor_source=self.sensor_source, start_timestamp=int(10 * 1000000.0), end_timestamp=int(20 * 1000000.0), subsample_interval=3)))
    self.assertEqual(expected_tokens, actual_tokens)

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

class InterpolatableState(ABC):
    """
    Interface for producing interpolatable arrays from objects. Objects must have two methods implemented,
    to_split_state which splits the object state in a list of variables and in a list of constants; and from_split_state
    which constructs a new object using the same set of parameters, a list of variables and a list of constants.
    This is to interpolate states which contain fixed parts.
    """

    @property
    @abstractmethod
    def time_point(self) -> TimePoint:
        """
        Interpolation time
        :return: The time corresponding to the time_point
        """
        pass

    @property
    def time_us(self) -> int:
        """
        Interpolation time
        :return: The time corresponding to the state time point
        """
        return int(self.time_point.time_us)

    @abstractmethod
    def to_split_state(self) -> SplitState:
        """
        Serializes the object in three lists, one containing variable (interpolatable) states, the other
        containing states which are not meant to be interpolated, but are required to de-serialize the object
        after interpolation.
        :return: A tuple with list of variable and a list of fixed states
        """
        pass

    @staticmethod
    @abstractmethod
    def from_split_state(split_state: SplitState) -> InterpolatableState:
        """
        De-serializes an object by its variable and fixed states, for example after interpolation.
        :param split_state: The split state representation
        :return: The deserialized Object
        """
        pass

@property
def time_us(self) -> int:
    """
        Interpolation time
        :return: The time corresponding to the state time point
        """
    return int(self.time_point.time_us)

class TestPatch(unittest.TestCase):
    """
    A class to test the patch utils.
    """

    def test_patch_with_validation_correct_patch(self) -> None:
        """
        Tests that the patch works with a correct patch.
        """

        def correct_patch(x: int) -> int:
            """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
            return x + 1
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch):
            result = complex_method(x=1, y=2)
            self.assertEqual(4, result)

    def test_patch_with_validation_correct_patch_direct(self) -> None:
        """
        Tests that the patch works with a correct patch that is directly provided.
        """

        def correct_patch(x: int) -> int:
            """
            A correct patch for the base_method.
            :param x: The input.
            :return: The output.
            """
            return x + 1
        with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', correct_patch, override_function=swappable_with_base_method):
            result = complex_method(x=1, y=2)
            self.assertEqual(4, result)

    def test_patch_raises_with_incorrect_patch(self) -> None:
        """
        Tests that an incorrect patch causes an error to be rasied.
        """

        def incorrect_patch(x: float) -> int:
            """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
            return int(x) + 1
        with self.assertRaises(TypeError):
            with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch):
                _ = complex_method(x=1, y=2)

    def test_patch_raises_with_incorrect_patch_direct(self) -> None:
        """
        Tests that an incorrect patch causes an error to be rasied.
        """

        def incorrect_patch(x: float) -> int:
            """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
            return int(x) + 1
        with self.assertRaises(TypeError):
            with patch_with_validation('nuplan.common.utils.test.patch_test_methods.base_method', incorrect_patch, override_function=swappable_with_base_method):
                _ = complex_method(x=1, y=2)

def incorrect_patch(x: float) -> int:
    """
            An incorrect patch for the _base_method.
            :param x: The input.
            :return: The output.
            """
    return int(x) + 1

class IncorrectConcrete(ValidationInterface):
    """
    A class that incorrectly implements the interface.
    """

    def implement_me(self, y: int) -> int:
        """
        Implemented incorrectly with wrong return type. See interface.
        """
        return int(y + 1.0)

def implement_me(self, y: int) -> int:
    """
        Implemented incorrectly with wrong return type. See interface.
        """
    return int(y + 1.0)

class TestGetUniqueJobId(unittest.TestCase):
    """Test suite for the generation of unique job IDs"""

    def test_unique_job_id_no_job_id(self) -> None:
        """
        Tests that if NUPLAN_JOB_ID is not set, the same job ID is returned.
        """
        if os.environ.get('NUPLAN_JOB_ID') is not None:
            del os.environ['NUPLAN_JOB_ID']
        get_unique_job_id.cache_clear()
        job_id_1 = get_unique_job_id()
        job_id_2 = get_unique_job_id()
        self.assertEqual(job_id_1, job_id_2)

    def test_unique_job_id_with_job_id(self) -> None:
        """
        Tests that if NUPLAN_JOB_ID is not set, the same job ID is returned.
        """
        os.environ['NUPLAN_JOB_ID'] = '12345'
        get_unique_job_id.cache_clear()
        job_id_1 = get_unique_job_id()
        job_id_2 = get_unique_job_id()
        self.assertEqual(job_id_1, job_id_2)
        del os.environ['NUPLAN_JOB_ID']

    def test_uniqueness_job_id(self) -> None:
        """
        Tests that the returned job ids are unique if they are not cached.
        """
        if os.environ.get('NUPLAN_JOB_ID') is not None:
            del os.environ['NUPLAN_JOB_ID']
        job_id_1 = get_unique_job_id()
        get_unique_job_id.cache_clear()
        job_id_2 = get_unique_job_id()
        self.assertNotEqual(job_id_1, job_id_2)

    def test_get_unique_incremental_track_id(self) -> None:
        """Tests creation of unique track ids."""
        track_token_and_expected_id_0 = ('track_0', 0)
        track_token_and_expected_id_1 = ('track_1', 1)
        self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_0[0]), track_token_and_expected_id_0[1])
        self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_1[0]), track_token_and_expected_id_1[1])
        self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_0[0]), track_token_and_expected_id_0[1])

def test_get_unique_incremental_track_id(self) -> None:
    """Tests creation of unique track ids."""
    track_token_and_expected_id_0 = ('track_0', 0)
    track_token_and_expected_id_1 = ('track_1', 1)
    self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_0[0]), track_token_and_expected_id_0[1])
    self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_1[0]), track_token_and_expected_id_1[1])
    self.assertEqual(get_unique_incremental_track_id(track_token_and_expected_id_0[0]), track_token_and_expected_id_0[1])

def get_all_rows_with_value(elements: gpd.geodataframe.GeoDataFrame, column_label: str, desired_value: str) -> gpd.geodataframe.GeoDataFrame:
    """
    Extract all matching elements. Note, if no matching desired_key is found and empty list is returned.
    :param elements: data frame from MapsDb.
    :param column_label: key to extract from a column.
    :param desired_value: key which is compared with the values of column_label entry.
    :return: a subset of the original GeoDataFrame containing the matching key.
    """
    return elements.iloc[np.where(elements[column_label].to_numpy().astype(int) == int(desired_value))]

def compute_linestring_heading(linestring: geom.linestring.LineString) -> List[float]:
    """
    Compute the heading of each coordinate to its successor coordinate. The last coordinate will have the same heading
        as the second last coordinate.
    :param linestring: linestring as a shapely LineString.
    :return: a list of headings associated to each starting coordinate.
    """
    coords: npt.NDArray[np.float64] = np.asarray(linestring.coords)
    vectors = np.diff(coords, axis=0)
    angles = np.arctan2(vectors.T[1], vectors.T[0])
    angles = np.append(angles, angles[-1])
    assert len(angles) == len(coords), 'Calculated heading must have the same length as input coordinates'
    return list(angles)

def extract_discrete_polyline(polyline: geom.LineString) -> List[StateSE2]:
    """
    Returns a discretized polyline composed of StateSE2 as nodes.
    :param polyline: the polyline of interest.
    :returns: linestring as a list of waypoints represented by StateSE2.
    """
    assert polyline.length > 0.0, 'The length of the polyline has to be greater than 0!'
    headings = compute_linestring_heading(polyline)
    x_coords, y_coords = polyline.coords.xy
    return [StateSE2(x, y, heading) for x, y, heading in zip(x_coords, y_coords, headings)]

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

@classmethod
def from_oriented_boxes(cls, boxes: List[OrientedBox]) -> TrackedObjects:
    """When iterating return the tracked objects."""
    scene_objects = [SceneObject(TrackedObjectType.GENERIC_OBJECT, box, SceneObjectMetadata(timestamp_us=i, token=str(i), track_token=None, track_id=None)) for i, box in enumerate(boxes)]
    return TrackedObjects(scene_objects)

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

def get_velocity_shifted(displacement: StateVector2D, ref_velocity: StateVector2D, ref_angular_vel: float) -> StateVector2D:
    """
    Computes the velocity at a query point on the same planar rigid body as a reference point.
    :param displacement: [m] The displacement vector from the reference to the query point
    :param ref_velocity: [m/s] The velocity vector at the reference point
    :param ref_angular_vel: [rad/s] The angular velocity of the body around the vertical axis
    :return: [m/s] The velocity vector at the given displacement.
    """
    velocity_shift_term: npt.NDArray[np.float64] = np.array([-displacement.y * ref_angular_vel, displacement.x * ref_angular_vel])
    return StateVector2D(*ref_velocity.array + velocity_shift_term)

def get_acceleration_shifted(displacement: StateVector2D, ref_accel: StateVector2D, ref_angular_vel: float, ref_angular_accel: float) -> StateVector2D:
    """
    Computes the acceleration at a query point on the same planar rigid body as a reference point.
    :param displacement: [m] The displacement vector from the reference to the query point
    :param ref_accel: [m/s^2] The acceleration vector at the reference point
    :param ref_angular_vel: [rad/s] The angular velocity of the body around the vertical axis
    :param ref_angular_accel: [rad/s^2] The angular acceleration of the body around the vertical axis
    :return: [m/s^2] The acceleration vector at the given displacement.
    """
    centripetal_acceleration_term = displacement.array * ref_angular_vel ** 2
    angular_acceleration_term = displacement.array * ref_angular_accel
    return StateVector2D(*ref_accel.array + centripetal_acceleration_term + angular_acceleration_term)

class DynamicCarState:
    """Contains the various dynamic attributes of ego."""

    def __init__(self, rear_axle_to_center_dist: float, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, angular_velocity: float=0.0, angular_acceleration: float=0.0, tire_steering_rate: float=0.0):
        """
        :param rear_axle_to_center_dist:[m]  Distance (positive) from rear axle to the geometrical center of ego
        :param rear_axle_velocity_2d: [m/s]Velocity vector at the rear axle
        :param rear_axle_acceleration_2d: [m/s^2] Acceleration vector at the rear axle
        :param angular_velocity: [rad/s] Angular velocity of ego
        :param angular_acceleration: [rad/s^2] Angular acceleration of ego
        :param tire_steering_rate: [rad/s] Tire steering rate of ego
        """
        self._rear_axle_to_center_dist = rear_axle_to_center_dist
        self._angular_velocity = angular_velocity
        self._angular_acceleration = angular_acceleration
        self._rear_axle_velocity_2d = rear_axle_velocity_2d
        self._rear_axle_acceleration_2d = rear_axle_acceleration_2d
        self._tire_steering_rate = tire_steering_rate

    @property
    def rear_axle_velocity_2d(self) -> StateVector2D:
        """
        Returns the vectorial velocity at the middle of the rear axle.
        :return: StateVector2D Containing the velocity at the rear axle
        """
        return self._rear_axle_velocity_2d

    @property
    def rear_axle_acceleration_2d(self) -> StateVector2D:
        """
        Returns the vectorial acceleration at the middle of the rear axle.
        :return: StateVector2D Containing the acceleration at the rear axle
        """
        return self._rear_axle_acceleration_2d

    @cached_property
    def center_velocity_2d(self) -> StateVector2D:
        """
        Returns the vectorial velocity at the geometrical center of Ego.
        :return: StateVector2D Containing the velocity at the geometrical center of Ego
        """
        displacement = StateVector2D(self._rear_axle_to_center_dist, 0.0)
        return get_velocity_shifted(displacement, self.rear_axle_velocity_2d, self.angular_velocity)

    @cached_property
    def center_acceleration_2d(self) -> StateVector2D:
        """
        Returns the vectorial acceleration at the geometrical center of Ego.
        :return: StateVector2D Containing the acceleration at the geometrical center of Ego
        """
        displacement = StateVector2D(self._rear_axle_to_center_dist, 0.0)
        return get_acceleration_shifted(displacement, self.rear_axle_acceleration_2d, self.angular_velocity, self.angular_acceleration)

    @property
    def angular_velocity(self) -> float:
        """
        Getter for the angular velocity of ego.
        :return: [rad/s] Angular velocity
        """
        return self._angular_velocity

    @property
    def angular_acceleration(self) -> float:
        """
        Getter for the angular acceleration of ego.
        :return: [rad/s^2] Angular acceleration
        """
        return self._angular_acceleration

    @property
    def tire_steering_rate(self) -> float:
        """
        Getter for the tire steering rate of ego.
        :return: [rad/s] Tire steering rate
        """
        return self._tire_steering_rate

    @cached_property
    def speed(self) -> float:
        """
        Magnitude of the speed of the center of ego.
        :return: [m/s] 1D speed
        """
        return float(self._rear_axle_velocity_2d.magnitude())

    @cached_property
    def acceleration(self) -> float:
        """
        Magnitude of the acceleration of the center of ego.
        :return: [m/s^2] 1D acceleration
        """
        return float(self._rear_axle_acceleration_2d.magnitude())

    def __eq__(self, other: object) -> bool:
        """
        Compare two instances whether they are numerically close
        :param other: object
        :return: true if the classes are almost equal
        """
        if not isinstance(other, DynamicCarState):
            return NotImplemented
        return self.rear_axle_velocity_2d == other.rear_axle_velocity_2d and self.rear_axle_acceleration_2d == other.rear_axle_acceleration_2d and math.isclose(self._angular_acceleration, other._angular_acceleration) and math.isclose(self._angular_velocity, other._angular_velocity) and math.isclose(self._rear_axle_to_center_dist, other._rear_axle_to_center_dist) and math.isclose(self._tire_steering_rate, other._tire_steering_rate)

    def __repr__(self) -> str:
        """Repr magic method"""
        return f'Rear Axle| velocity: {self.rear_axle_velocity_2d}, acceleration: {self.rear_axle_acceleration_2d}\nCenter   | velocity: {self.center_velocity_2d}, acceleration: {self.center_acceleration_2d}\nangular velocity: {self.angular_velocity}, angular acceleration: {self._angular_acceleration}\nrear_axle_to_center_dist: {self._rear_axle_to_center_dist} \n_tire_steering_rate: {self._tire_steering_rate} \n'

    @staticmethod
    def build_from_rear_axle(rear_axle_to_center_dist: float, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, angular_velocity: float=0.0, angular_acceleration: float=0.0, tire_steering_rate: float=0.0) -> DynamicCarState:
        """
        Construct ego state from rear axle parameters
        :param rear_axle_to_center_dist: [m] distance between center and rear axle
        :param rear_axle_velocity_2d: [m/s] velocity at rear axle
        :param rear_axle_acceleration_2d: [m/s^2] acceleration at rear axle
        :param angular_velocity: [rad/s] angular velocity
        :param angular_acceleration: [rad/s^2] angular acceleration
        :param tire_steering_rate: [rad/s] tire steering_rate
        :return: constructed DynamicCarState of ego.
        """
        return DynamicCarState(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_velocity, angular_acceleration=angular_acceleration, tire_steering_rate=tire_steering_rate)

    @staticmethod
    def build_from_cog(wheel_base: float, rear_axle_to_center_dist: float, cog_speed: float, cog_acceleration: float, steering_angle: float, angular_acceleration: float=0.0, tire_steering_rate: float=0.0) -> DynamicCarState:
        """
        Construct ego state from rear axle parameters
        :param wheel_base: distance between axles [m]
        :param rear_axle_to_center_dist: distance between center and rear axle [m]
        :param cog_speed: magnitude of speed COG [m/s]
        :param cog_acceleration: magnitude of acceleration at COG [m/s^s]
        :param steering_angle: steering angle at tire [rad]
        :param angular_acceleration: angular acceleration
        :param tire_steering_rate: tire steering rate
        :return: constructed DynamicCarState of ego.
        """
        beta = _get_beta(steering_angle, wheel_base)
        rear_axle_longitudinal_velocity, rear_axle_lateral_velocity = _projected_velocities_from_cog(beta, cog_speed)
        angular_velocity = _angular_velocity_from_cog(cog_speed, wheel_base, beta, steering_angle)
        longitudinal_acceleration, lateral_acceleration = _project_accelerations_from_cog(rear_axle_longitudinal_velocity, angular_velocity, cog_acceleration, beta)
        return DynamicCarState(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=StateVector2D(rear_axle_longitudinal_velocity, rear_axle_lateral_velocity), rear_axle_acceleration_2d=StateVector2D(longitudinal_acceleration, lateral_acceleration), angular_velocity=angular_velocity, angular_acceleration=angular_acceleration, tire_steering_rate=tire_steering_rate)

@cached_property
def center_velocity_2d(self) -> StateVector2D:
    """
        Returns the vectorial velocity at the geometrical center of Ego.
        :return: StateVector2D Containing the velocity at the geometrical center of Ego
        """
    displacement = StateVector2D(self._rear_axle_to_center_dist, 0.0)
    return get_velocity_shifted(displacement, self.rear_axle_velocity_2d, self.angular_velocity)

@cached_property
def center_acceleration_2d(self) -> StateVector2D:
    """
        Returns the vectorial acceleration at the geometrical center of Ego.
        :return: StateVector2D Containing the acceleration at the geometrical center of Ego
        """
    displacement = StateVector2D(self._rear_axle_to_center_dist, 0.0)
    return get_acceleration_shifted(displacement, self.rear_axle_acceleration_2d, self.angular_velocity, self.angular_acceleration)

@staticmethod
def build_from_rear_axle(rear_axle_to_center_dist: float, rear_axle_velocity_2d: StateVector2D, rear_axle_acceleration_2d: StateVector2D, angular_velocity: float=0.0, angular_acceleration: float=0.0, tire_steering_rate: float=0.0) -> DynamicCarState:
    """
        Construct ego state from rear axle parameters
        :param rear_axle_to_center_dist: [m] distance between center and rear axle
        :param rear_axle_velocity_2d: [m/s] velocity at rear axle
        :param rear_axle_acceleration_2d: [m/s^2] acceleration at rear axle
        :param angular_velocity: [rad/s] angular velocity
        :param angular_acceleration: [rad/s^2] angular acceleration
        :param tire_steering_rate: [rad/s] tire steering_rate
        :return: constructed DynamicCarState of ego.
        """
    return DynamicCarState(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=rear_axle_velocity_2d, rear_axle_acceleration_2d=rear_axle_acceleration_2d, angular_velocity=angular_velocity, angular_acceleration=angular_acceleration, tire_steering_rate=tire_steering_rate)

@staticmethod
def build_from_cog(wheel_base: float, rear_axle_to_center_dist: float, cog_speed: float, cog_acceleration: float, steering_angle: float, angular_acceleration: float=0.0, tire_steering_rate: float=0.0) -> DynamicCarState:
    """
        Construct ego state from rear axle parameters
        :param wheel_base: distance between axles [m]
        :param rear_axle_to_center_dist: distance between center and rear axle [m]
        :param cog_speed: magnitude of speed COG [m/s]
        :param cog_acceleration: magnitude of acceleration at COG [m/s^s]
        :param steering_angle: steering angle at tire [rad]
        :param angular_acceleration: angular acceleration
        :param tire_steering_rate: tire steering rate
        :return: constructed DynamicCarState of ego.
        """
    beta = _get_beta(steering_angle, wheel_base)
    rear_axle_longitudinal_velocity, rear_axle_lateral_velocity = _projected_velocities_from_cog(beta, cog_speed)
    angular_velocity = _angular_velocity_from_cog(cog_speed, wheel_base, beta, steering_angle)
    longitudinal_acceleration, lateral_acceleration = _project_accelerations_from_cog(rear_axle_longitudinal_velocity, angular_velocity, cog_acceleration, beta)
    return DynamicCarState(rear_axle_to_center_dist=rear_axle_to_center_dist, rear_axle_velocity_2d=StateVector2D(rear_axle_longitudinal_velocity, rear_axle_lateral_velocity), rear_axle_acceleration_2d=StateVector2D(longitudinal_acceleration, lateral_acceleration), angular_velocity=angular_velocity, angular_acceleration=angular_acceleration, tire_steering_rate=tire_steering_rate)

class AgentState(SceneObject):
    """
    Class describing Agent State (including dynamics) in the scene, representing Vehicles, Bicycles and Pedestrians.
    """

    def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, velocity: StateVector2D, metadata: SceneObjectMetadata, angular_velocity: Optional[float]=None):
        """
        Representation of an Agent in the scene (Vehicles, Pedestrians, Bicyclists and GenericObjects).
        :param tracked_object_type: Type of the current agent.
        :param oriented_box: Geometrical representation of the Agent.
        :param velocity: Velocity (vectorial) of Agent.
        :param metadata: Agent's metadata.
        :param angular_velocity: The scalar angular velocity of the agent, if available.
        """
        super().__init__(tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=metadata)
        self._velocity = velocity
        self._angular_velocity = angular_velocity

    @property
    def velocity(self) -> StateVector2D:
        """
        Getter for velocity.
        :return: The agent vectorial velocity.
        """
        return self._velocity

    @property
    def angular_velocity(self) -> Optional[float]:
        """
        Getter for angular.
        :return: The agent angular velocity.
        """
        return self._angular_velocity

    @classmethod
    def from_new_pose(cls, agent: AgentState, pose: StateSE2) -> AgentState:
        """
        Initializer that create the same agent in a different pose.
        :param agent: A sample agent.
        :param pose: The new pose.
        :return: A new agent.
        """
        return AgentState(tracked_object_type=agent.tracked_object_type, oriented_box=OrientedBox.from_new_pose(agent.box, pose), velocity=agent.velocity, angular_velocity=agent.angular_velocity, metadata=copy.deepcopy(agent.metadata))

@classmethod
def from_new_pose(cls, agent: AgentState, pose: StateSE2) -> AgentState:
    """
        Initializer that create the same agent in a different pose.
        :param agent: A sample agent.
        :param pose: The new pose.
        :return: A new agent.
        """
    return AgentState(tracked_object_type=agent.tracked_object_type, oriented_box=OrientedBox.from_new_pose(agent.box, pose), velocity=agent.velocity, angular_velocity=agent.angular_velocity, metadata=copy.deepcopy(agent.metadata))

@dataclass
class TimePoint:
    """
    Time instance in a time series.
    """
    time_us: int
    __slots__ = 'time_us'

    def __post_init__(self) -> None:
        """
        Validate class after creation.
        """
        assert self.time_us >= 0, 'Time point has to be positive!'

    @property
    def time_s(self) -> float:
        """
        :return [s] time in seconds.
        """
        return self.time_us * 1e-06

    def __add__(self, other: object) -> TimePoint:
        """
        Adds a TimeDuration to generate a new TimePoint.
        :param other: time point.
        :return: self + other.
        """
        if isinstance(other, (TimeDuration, TimePoint)):
            return TimePoint(self.time_us + other.time_us)
        return NotImplemented

    def __radd__(self, other: object) -> TimePoint:
        """
        :param other: Right addition target.
        :return: Addition with other if other is a TimeDuration.
        """
        if isinstance(other, TimeDuration):
            return self.__add__(other)
        return NotImplemented

    def __sub__(self, other: object) -> TimePoint:
        """
        Subtract a time duration from a time point.
        :param other: time duration.
        :return: self - other if other is a TimeDuration.
        """
        if isinstance(other, (TimeDuration, TimePoint)):
            return TimePoint(self.time_us - other.time_us)
        return NotImplemented

    def __gt__(self, other: TimePoint) -> bool:
        """
        Self is greater than other.
        :param other: time point.
        :return: True if self > other, False otherwise.
        """
        if isinstance(other, TimePoint):
            return self.time_us > other.time_us
        return NotImplemented

    def __ge__(self, other: TimePoint) -> bool:
        """
        Self is greater or equal than other.
        :param other: time point.
        :return: True if self >= other, False otherwise.
        """
        if isinstance(other, TimePoint):
            return self.time_us >= other.time_us
        return NotImplemented

    def __lt__(self, other: TimePoint) -> bool:
        """
        Self is less than other.
        :param other: time point.
        :return: True if self < other, False otherwise.
        """
        if isinstance(other, TimePoint):
            return self.time_us < other.time_us
        return NotImplemented

    def __le__(self, other: TimePoint) -> bool:
        """
        Self is less or equal than other.
        :param other: time point.
        :return: True if self <= other, False otherwise.
        """
        if isinstance(other, TimePoint):
            return self.time_us <= other.time_us
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """
        Self is equal to other
        :param other: time point
        :return: True if self == other, False otherwise
        """
        if not isinstance(other, TimePoint):
            return NotImplemented
        return self.time_us == other.time_us

    def __hash__(self) -> int:
        """
        :return: hash for this object
        """
        return hash(self.time_us)

    def diff(self, time_point: TimePoint) -> TimeDuration:
        """
        Computes the TimeDuration between self and another TimePoint.
        :param time_point: The other time point.
        :return: The TimeDuration between the two TimePoints.
        """
        return TimeDuration.from_us(int(self.time_us - time_point.time_us))

def __add__(self, other: object) -> TimePoint:
    """
        Adds a TimeDuration to generate a new TimePoint.
        :param other: time point.
        :return: self + other.
        """
    if isinstance(other, (TimeDuration, TimePoint)):
        return TimePoint(self.time_us + other.time_us)
    return NotImplemented

def __sub__(self, other: object) -> TimePoint:
    """
        Subtract a time duration from a time point.
        :param other: time duration.
        :return: self - other if other is a TimeDuration.
        """
    if isinstance(other, (TimeDuration, TimePoint)):
        return TimePoint(self.time_us - other.time_us)
    return NotImplemented

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

@staticmethod
def from_matrix(matrix: npt.NDArray[np.float32]) -> StateSE2:
    """
        :param matrix: 3x3 2D transformation matrix
        :return: StateSE2 object
        """
    assert matrix.shape == (3, 3), f'Expected 3x3 transformation matrix, but input matrix has shape {matrix.shape}'
    vector = [matrix[0, 2], matrix[1, 2], np.arctan2(matrix[1, 0], matrix[0, 0])]
    return StateSE2.deserialize(vector)

class CarFootprint(OrientedBox):
    """Class that represent the car semantically, with geometry and relevant point of interest."""

    def __init__(self, center: StateSE2, vehicle_parameters: VehicleParameters):
        """
        :param center: The pose of ego in the specified frame
        :param vehicle_parameters: The parameters of ego
        """
        super().__init__(center=center, width=vehicle_parameters.width, length=vehicle_parameters.length, height=vehicle_parameters.height)
        self._vehicle_parameters = vehicle_parameters

    @property
    def vehicle_parameters(self) -> VehicleParameters:
        """
        :return: vehicle parameters corresponding to the footprint
        """
        return self._vehicle_parameters

    def get_point_of_interest(self, point_of_interest: OrientedBoxPointType) -> Point2D:
        """
        Getter for the point of interest of ego.
        :param point_of_interest: The query point of the car
        :return: The position of the query point.
        """
        return self.corner(point_of_interest)

    @property
    def oriented_box(self) -> OrientedBox:
        """
        Getter for Ego's OrientedBox
        :return: OrientedBox of Ego
        """
        return self

    @property
    def rear_axle_to_center_dist(self) -> float:
        """
        Getter for the distance from the rear axle to the center of mass of Ego.
        :return: Distance from rear axle to COG
        """
        return float(self._vehicle_parameters.rear_axle_to_center)

    @cached_property
    def rear_axle(self) -> StateSE2:
        """
        Getter for the pose at the middle of the rear axle
        :return: SE2 Pose of the rear axle.
        """
        return translate_longitudinally(self.oriented_box.center, -self.rear_axle_to_center_dist)

    @classmethod
    def build_from_rear_axle(cls, rear_axle_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from rear axle position
        :param rear_axle_pose: SE2 position of rear axle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        center = translate_longitudinally(rear_axle_pose, vehicle_parameters.rear_axle_to_center)
        return cls(center=center, vehicle_parameters=vehicle_parameters)

    @classmethod
    def build_from_cog(cls, cog_pose: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from COG position
        :param cog_pose: SE2 position of COG
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        cog_to_center = vehicle_parameters.rear_axle_to_center - vehicle_parameters.cog_position_from_rear_axle
        center = translate_longitudinally(cog_pose, cog_to_center)
        return cls(center=center, vehicle_parameters=vehicle_parameters)

    @classmethod
    def build_from_center(cls, center: StateSE2, vehicle_parameters: VehicleParameters) -> CarFootprint:
        """
        Construct Car Footprint from geometric center of vehicle
        :param center: SE2 position of geometric center of vehicle
        :param vehicle_parameters: parameters of vehicle
        :return: CarFootprint
        """
        return cls(center=center, vehicle_parameters=vehicle_parameters)

def get_point_of_interest(self, point_of_interest: OrientedBoxPointType) -> Point2D:
    """
        Getter for the point of interest of ego.
        :param point_of_interest: The query point of the car
        :return: The position of the query point.
        """
    return self.corner(point_of_interest)

class EgoTemporalState(AgentTemporalState):
    """
    Temporal ego state, with future and past trajectory
    """

    def __init__(self, current_state: EgoState, past_trajectory: Optional[PredictedTrajectory]=None, predictions: Optional[List[PredictedTrajectory]]=None):
        """
        Initialize temporal state
        :param current_state: current state of ego
        :param past_trajectory: past trajectory, where last waypoint represents the same position as current state
        :param predictions: multimodal predictions, or future trajectory
        """
        super().__init__(initial_time_stamp=current_state.time_point, predictions=predictions, past_trajectory=past_trajectory)
        self._ego_current_state = current_state

    @property
    def ego_current_state(self) -> EgoState:
        """
        :return: the current ego state
        """
        return self._ego_current_state

    @property
    def ego_previous_state(self) -> Optional[EgoState]:
        """
        :return: the previous ego state if exists. This is just a proxy to make sure the return type is correct.
        """
        return self.previous_state

    @cached_property
    def agent(self) -> Agent:
        """
        Casts the EgoTemporalState to an Agent object.
        :return: An Agent object with the parameters of EgoState
        """
        return Agent(metadata=self.ego_current_state.scene_object_metadata, tracked_object_type=TrackedObjectType.EGO, oriented_box=self.ego_current_state.car_footprint.oriented_box, velocity=self.ego_current_state.dynamic_car_state.center_velocity_2d, past_trajectory=self.past_trajectory, predictions=self.predictions)

@cached_property
def agent(self) -> Agent:
    """
        Casts the EgoTemporalState to an Agent object.
        :return: An Agent object with the parameters of EgoState
        """
    return Agent(metadata=self.ego_current_state.scene_object_metadata, tracked_object_type=TrackedObjectType.EGO, oriented_box=self.ego_current_state.car_footprint.oriented_box, velocity=self.ego_current_state.dynamic_car_state.center_velocity_2d, past_trajectory=self.past_trajectory, predictions=self.predictions)

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

@property
def dimensions(self) -> Dimension:
    """
        :return: Dimensions of this oriented box in meters
        """
    return Dimension(length=self.length, width=self.width, height=self.height)

def all_corners(self) -> List[Point2D]:
    """
        Return 4 corners of oriented box (FL, RL, RR, FR)
        :return: all corners of a oriented box in a list
        """
    return [self.corner(OrientedBoxPointType.FRONT_LEFT), self.corner(OrientedBoxPointType.REAR_LEFT), self.corner(OrientedBoxPointType.REAR_RIGHT), self.corner(OrientedBoxPointType.FRONT_RIGHT)]

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

@staticmethod
def from_split_state(split_state: SplitState) -> EgoState:
    """Inherited, see superclass."""
    if len(split_state) != 10:
        raise RuntimeError(f'Expected a variable state vector of size 10, got {len(split_state)}')
    return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(split_state.linear_states[1], split_state.linear_states[2], split_state.angular_states[0]), rear_axle_velocity_2d=StateVector2D(split_state.linear_states[3], split_state.linear_states[4]), rear_axle_acceleration_2d=StateVector2D(split_state.linear_states[5], split_state.linear_states[6]), tire_steering_angle=split_state.linear_states[7], time_point=TimePoint(int(split_state.linear_states[0])), vehicle_parameters=split_state.fixed_states[0])

@property
def time_us(self) -> int:
    """
        Time in micro seconds
        :return: [us].
        """
    return int(self.time_point.time_us)

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

class Agent(AgentTemporalState, AgentState):
    """
    AgentState with future and past trajectory.
    """

    def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, velocity: StateVector2D, metadata: SceneObjectMetadata, angular_velocity: Optional[float]=None, predictions: Optional[List[PredictedTrajectory]]=None, past_trajectory: Optional[PredictedTrajectory]=None):
        """
        Representation of an Agent in the scene (Vehicles, Pedestrians, Bicyclists and GenericObjects).
        :param tracked_object_type: Type of the current agent.
        :param oriented_box: Geometrical representation of the Agent.
        :param velocity: Velocity (vectorial) of Agent.
        :param metadata: Agent's metadata.
        :param angular_velocity: The scalar angular velocity of the agent, if available.
        :param predictions: Optional list of (possibly multiple) predicted trajectories.
        :param past_trajectory: Optional past trajectory of this agent.
        """
        AgentTemporalState.__init__(self, initial_time_stamp=TimePoint(metadata.timestamp_us), predictions=predictions, past_trajectory=past_trajectory)
        AgentState.__init__(self, tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=metadata, velocity=velocity, angular_velocity=angular_velocity)

    @classmethod
    def from_agent_state(cls, agent: AgentState) -> Agent:
        """
        Create Agent from AgentState.
        :param agent: input single agent state.
        :return: Agent with None for future and past trajectory.
        """
        return cls(tracked_object_type=agent.tracked_object_type, oriented_box=agent.box, velocity=agent.velocity, metadata=agent.metadata, angular_velocity=agent.angular_velocity, predictions=None, past_trajectory=None)

def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, velocity: StateVector2D, metadata: SceneObjectMetadata, angular_velocity: Optional[float]=None, predictions: Optional[List[PredictedTrajectory]]=None, past_trajectory: Optional[PredictedTrajectory]=None):
    """
        Representation of an Agent in the scene (Vehicles, Pedestrians, Bicyclists and GenericObjects).
        :param tracked_object_type: Type of the current agent.
        :param oriented_box: Geometrical representation of the Agent.
        :param velocity: Velocity (vectorial) of Agent.
        :param metadata: Agent's metadata.
        :param angular_velocity: The scalar angular velocity of the agent, if available.
        :param predictions: Optional list of (possibly multiple) predicted trajectories.
        :param past_trajectory: Optional past trajectory of this agent.
        """
    AgentTemporalState.__init__(self, initial_time_stamp=TimePoint(metadata.timestamp_us), predictions=predictions, past_trajectory=past_trajectory)
    AgentState.__init__(self, tracked_object_type=tracked_object_type, oriented_box=oriented_box, metadata=metadata, velocity=velocity, angular_velocity=angular_velocity)

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

@staticmethod
def deserialize(vector: List[Union[int, float]]) -> Waypoint:
    """
        Deserializes the object.
        :param vector: a list of data to initialize a waypoint
        :return: Waypoint
        """
    assert len(vector) == 9, f'Expected a vector of size 9, got {len(vector)}'
    return Waypoint(time_point=TimePoint(int(vector[0])), oriented_box=OrientedBox(StateSE2(vector[1], vector[2], vector[3]), vector[4], vector[5], vector[6]), velocity=StateVector2D(vector[7], vector[8]) if vector[7] is not None and vector[8] is not None else None)

@staticmethod
def from_split_state(split_state: SplitState) -> Waypoint:
    """Inherited, see superclass."""
    total_state_length = len(split_state)
    assert total_state_length == 9, f'Expected a vector of size 9, got {total_state_length}'
    return Waypoint(time_point=TimePoint(int(split_state.linear_states[0])), oriented_box=OrientedBox(StateSE2(split_state.linear_states[1], split_state.linear_states[2], split_state.angular_states[0]), length=split_state.fixed_states[1], width=split_state.fixed_states[0], height=split_state.fixed_states[2]), velocity=StateVector2D(split_state.linear_states[3], split_state.linear_states[4]) if split_state.linear_states[3] is not None and split_state.linear_states[4] is not None else None)

class SceneObject:
    """Class describing SceneObjects, i.e. objects present in a planning scene"""

    def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, metadata: SceneObjectMetadata):
        """
        Representation of an Agent in the scene.
        :param tracked_object_type: Type of the current static object
        :param oriented_box: Geometrical representation of the static object
        :param metadata: High-level information about the object
        """
        self._metadata = metadata
        self.instance_token = None
        self._tracked_object_type = tracked_object_type
        self._box: OrientedBox = oriented_box

    @property
    def metadata(self) -> SceneObjectMetadata:
        """
        Getter for object metadata
        :return: Object's metadata
        """
        return self._metadata

    @property
    def token(self) -> str:
        """
        Getter for object unique token, different for same object in different samples
        :return: The unique token
        """
        return self._metadata.token

    @property
    def track_token(self) -> Optional[str]:
        """
        Getter for object unique token tracked across samples, same for same objects in different samples
        :return: The unique track token
        """
        return self._metadata.track_token

    @property
    def tracked_object_type(self) -> TrackedObjectType:
        """
        Getter for object classification type
        :return: The object classification type
        """
        return self._tracked_object_type

    @property
    def box(self) -> OrientedBox:
        """
        Getter for object OrientedBox
        :return: The object oriented box
        """
        return self._box

    @property
    def center(self) -> StateSE2:
        """
        Getter for object center pose
        :return: The center pose
        """
        return self.box.center

    @classmethod
    def make_random(cls, token: str, object_type: TrackedObjectType) -> SceneObject:
        """
        Instantiates a random SceneObject.
        :param token: Unique token
        :param object_type: Classification type
        :return: SceneObject instance.
        """
        center = random.sample(range(50), 2)
        heading = np.random.uniform(-np.pi, np.pi)
        size = random.sample(range(1, 50), 3)
        track_id = random.sample(range(1, 10), 1)[0]
        timestamp_us = random.sample(range(1, 10), 1)[0]
        return SceneObject(metadata=SceneObjectMetadata(token=token, track_id=track_id, track_token=token, timestamp_us=timestamp_us), tracked_object_type=object_type, oriented_box=OrientedBox(StateSE2(*center, heading), size[0], size[1], size[2]))

    @classmethod
    def from_raw_params(cls, token: str, track_token: str, timestamp_us: int, track_id: int, center: StateSE2, size: Tuple[float, float, float]) -> SceneObject:
        """
        Instantiates a generic SceneObject.
        :param token: The token of the object.
        :param track_token: The track token of the object.
        :param timestamp_us: [us] timestamp for the object.
        :param track_id: Human readable track id.
        :param center: Center pose.
        :param size: Size of the geometrical box (width, length, height).
        :return: SceneObject instance.
        """
        box = OrientedBox(center, width=size[0], length=size[1], height=size[2])
        return SceneObject(metadata=SceneObjectMetadata(token=token, track_token=track_token, timestamp_us=timestamp_us, track_id=track_id), tracked_object_type=TrackedObjectType.GENERIC_OBJECT, oriented_box=box)

@classmethod
def make_random(cls, token: str, object_type: TrackedObjectType) -> SceneObject:
    """
        Instantiates a random SceneObject.
        :param token: Unique token
        :param object_type: Classification type
        :return: SceneObject instance.
        """
    center = random.sample(range(50), 2)
    heading = np.random.uniform(-np.pi, np.pi)
    size = random.sample(range(1, 50), 3)
    track_id = random.sample(range(1, 10), 1)[0]
    timestamp_us = random.sample(range(1, 10), 1)[0]
    return SceneObject(metadata=SceneObjectMetadata(token=token, track_id=track_id, track_token=token, timestamp_us=timestamp_us), tracked_object_type=object_type, oriented_box=OrientedBox(StateSE2(*center, heading), size[0], size[1], size[2]))

@classmethod
def from_raw_params(cls, token: str, track_token: str, timestamp_us: int, track_id: int, center: StateSE2, size: Tuple[float, float, float]) -> SceneObject:
    """
        Instantiates a generic SceneObject.
        :param token: The token of the object.
        :param track_token: The track token of the object.
        :param timestamp_us: [us] timestamp for the object.
        :param track_id: Human readable track id.
        :param center: Center pose.
        :param size: Size of the geometrical box (width, length, height).
        :return: SceneObject instance.
        """
    box = OrientedBox(center, width=size[0], length=size[1], height=size[2])
    return SceneObject(metadata=SceneObjectMetadata(token=token, track_token=track_token, timestamp_us=timestamp_us, track_id=track_id), tracked_object_type=TrackedObjectType.GENERIC_OBJECT, oriented_box=box)

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

def setUp(self) -> None:
    """Sets sample parameters for testing"""
    mock_time_point = Mock(time_us=0)
    mock_box = Mock(center=Mock(x='center_x', y='center_y', heading='center_heading'), length='length', width='width', height='height')
    mock_velocity = Mock(x='velocity_x', y='velocity_y')
    self.waypoint = Waypoint(mock_time_point, mock_box, mock_velocity)
    self.waypoint_no_vel = Waypoint(mock_time_point, mock_box)

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

def setUp(self) -> None:
    """Creates sample parameters for testing"""
    self.center = StateSE2(1, 2, m.pi / 8)
    self.length = 4.0
    self.width = 2.0
    self.height = 1.5
    self.expected_vertices = [(2.47, 3.69), (-1.23, 2.16), (-0.47, 0.31), (3.23, 1.84)]

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

class TestTrackedObjects(unittest.TestCase):
    """Tests TrackedObjects class"""

    def setUp(self) -> None:
        """Creates sample agents for testing"""
        self.agents = [get_sample_agent('foo', TrackedObjectType.PEDESTRIAN), get_sample_agent('bar', TrackedObjectType.VEHICLE), get_sample_agent('bar_out_the_car', TrackedObjectType.PEDESTRIAN)]

    def test_construction(self) -> None:
        """Tests that the object can be created correctly."""
        tracked_objects = TrackedObjects(self.agents)
        expected_type_and_set_of_tokens: Dict[TrackedObjectType, Any] = {object_type: set() for object_type in TrackedObjectType}
        expected_type_and_set_of_tokens[TrackedObjectType.PEDESTRIAN].update({'foo', 'bar_out_the_car'})
        expected_type_and_set_of_tokens[TrackedObjectType.VEHICLE].update({'bar'})
        for tracked_object_type in TrackedObjectType:
            if tracked_object_type not in expected_type_and_set_of_tokens:
                continue
            self.assertEqual(expected_type_and_set_of_tokens[tracked_object_type], {tracked_object.token for tracked_object in tracked_objects.get_tracked_objects_of_type(tracked_object_type)})

    def test_get_subset(self) -> None:
        """Tests that the object can be created correctly."""
        tracked_objects = TrackedObjects(self.agents)
        agents = tracked_objects.get_agents()
        static_objects = tracked_objects.get_static_objects()
        self.assertEqual(3, len(agents))
        self.assertEqual(0, len(static_objects))

    def test_get_tracked_objects_of_types(self) -> None:
        """Test get_tracked_objects_of_types()"""
        tracked_objects = TrackedObjects(self.agents)
        track_types = [TrackedObjectType.PEDESTRIAN, TrackedObjectType.VEHICLE]
        tracks = tracked_objects.get_tracked_objects_of_types(track_types)
        self.assertEqual(3, len(tracks))

def setUp(self) -> None:
    """Creates sample agents for testing"""
    self.agents = [get_sample_agent('foo', TrackedObjectType.PEDESTRIAN), get_sample_agent('bar', TrackedObjectType.VEHICLE), get_sample_agent('bar_out_the_car', TrackedObjectType.PEDESTRIAN)]

def test_construction(self) -> None:
    """Tests that the object can be created correctly."""
    tracked_objects = TrackedObjects(self.agents)
    expected_type_and_set_of_tokens: Dict[TrackedObjectType, Any] = {object_type: set() for object_type in TrackedObjectType}
    expected_type_and_set_of_tokens[TrackedObjectType.PEDESTRIAN].update({'foo', 'bar_out_the_car'})
    expected_type_and_set_of_tokens[TrackedObjectType.VEHICLE].update({'bar'})
    for tracked_object_type in TrackedObjectType:
        if tracked_object_type not in expected_type_and_set_of_tokens:
            continue
        self.assertEqual(expected_type_and_set_of_tokens[tracked_object_type], {tracked_object.token for tracked_object in tracked_objects.get_tracked_objects_of_type(tracked_object_type)})

def test_get_tracked_objects_of_types(self) -> None:
    """Test get_tracked_objects_of_types()"""
    tracked_objects = TrackedObjects(self.agents)
    track_types = [TrackedObjectType.PEDESTRIAN, TrackedObjectType.VEHICLE]
    tracks = tracked_objects.get_tracked_objects_of_types(track_types)
    self.assertEqual(3, len(tracks))

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

def get_sample_pose() -> StateSE2:
    """
    Creates a sample SE2 Pose.
    :return: A sample SE2 Pose with arbitrary parameters
    """
    return StateSE2(1.0, 2.0, math.pi / 2.0)

def get_sample_oriented_box() -> OrientedBox:
    """
    Creates a sample OrientedBox.
    :return: A sample OrientedBox with arbitrary parameters
    """
    return OrientedBox(get_sample_pose(), 4.0, 2.0, 1.5)

def get_sample_car_footprint(center: Optional[StateSE2]=None) -> CarFootprint:
    """
    Creates a sample CarFootprint.
    :param center: Vehicle's position. If none it uses the same position returned by get_sample_pose()
    :return: A sample CarFootprint with arbitrary parameters
    """
    if center:
        return CarFootprint.build_from_center(center=center, vehicle_parameters=get_pacifica_parameters())
    else:
        return CarFootprint.build_from_center(center=get_sample_oriented_box().center, vehicle_parameters=get_pacifica_parameters())

def get_sample_dynamic_car_state(rear_axle_to_center_dist: float=1.44) -> DynamicCarState:
    """
    Creates a sample DynamicCarState.
    :param rear_axle_to_center_dist: distance between rear axle and center [m]
    :return: A sample DynamicCarState with arbitrary parameters
    """
    return DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist, StateVector2D(1.0, 2.0), StateVector2D(0.1, 0.2))

def get_sample_ego_state(center: Optional[StateSE2]=None, time_us: Optional[int]=0) -> EgoState:
    """
    Creates a sample EgoState.
    :param center: Vehicle's position. If none it uses the same position returned by get_sample_pose()
    :param time_us: Time in microseconds
    :return: A sample EgoState with arbitrary parameters
    """
    return EgoState(car_footprint=get_sample_car_footprint(center), dynamic_car_state=get_sample_dynamic_car_state(), tire_steering_angle=0.2, time_point=TimePoint(time_us), is_in_auto_mode=False)

def get_sample_agent(token: str='test', agent_type: TrackedObjectType=TrackedObjectType.VEHICLE, num_past_states: Optional[int]=1, num_future_states: Optional[int]=1) -> Agent:
    """
    Creates a sample Agent, the token and agent type can be specified for various testing purposes.
    :param token: The unique token to assign to the agent.
    :param agent_type: Classification of the agent.
    :param num_past_states: How many states to generate in the past trajectory. With None, that will be assigned to
    the past_trajectory otherwise the current state + num_past_states will be added.
    :param num_future_states: How many states to generate in the future trajectory. If `None` is passed, `None` will
    be assigned to the predictions; otherwise the current state + num_future_states will be added.
    :return: A sample Agent.
    """
    initial_timestamp = 10
    sample_oriented_box = get_sample_oriented_box()
    return Agent(agent_type, sample_oriented_box, metadata=SceneObjectMetadata(timestamp_us=initial_timestamp, track_token=token, track_id=None, token=token), velocity=StateVector2D(0.0, 0.0), predictions=[PredictedTrajectory(1.0, [Waypoint(time_point=TimePoint(initial_timestamp + i * 5), oriented_box=sample_oriented_box) for i in range(num_future_states + 1)])] if num_future_states is not None else None, past_trajectory=PredictedTrajectory(1.0, [Waypoint(time_point=TimePoint(initial_timestamp - i * 5), oriented_box=sample_oriented_box) for i in reversed(range(num_past_states + 1))]) if num_past_states is not None else None)

class TestActorTemporalState(unittest.TestCase):
    """Test suite for the AgentTemporalState class"""

    def setUp(self) -> None:
        """Setup initial waypoints."""
        self.current_time_us = int(10 * 1000000.0)
        mock_oriented_box = Mock()
        self.future_waypoints: List[Optional[Waypoint]] = [Waypoint(time_point=TimePoint(self.current_time_us), oriented_box=mock_oriented_box), Waypoint(time_point=TimePoint(self.current_time_us + int(1000000.0)), oriented_box=mock_oriented_box)]
        self.past_waypoints: List[Optional[Waypoint]] = [Waypoint(time_point=TimePoint(self.current_time_us - int(1000000.0)), oriented_box=mock_oriented_box), Waypoint(time_point=TimePoint(self.current_time_us), oriented_box=mock_oriented_box)]

    def test_past_setting_successful(self) -> None:
        """Test that we can set past trajectory."""
        past_waypoints = [None] + self.past_waypoints
        actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), past_trajectory=PredictedTrajectory(waypoints=past_waypoints, probability=1.0))
        self.assertEqual(actor.past_trajectory.probability, 1.0)
        self.assertEqual(len(actor.past_trajectory.valid_waypoints), 2)
        self.assertEqual(len(actor.past_trajectory), 3)
        self.assertEqual(actor.previous_state, self.past_waypoints[0])

    def test_past_setting_fail(self) -> None:
        """Test that we can raise if past trajectory does not start at current state."""
        past_waypoints = list(reversed(self.past_waypoints))
        with self.assertRaises(ValueError):
            AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), past_trajectory=PredictedTrajectory(waypoints=past_waypoints, probability=1.0))

    def test_future_trajectory_successful(self) -> None:
        """Test that we can set future predictions."""
        future_waypoints = self.future_waypoints
        actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=[PredictedTrajectory(waypoints=future_waypoints, probability=1.0)])
        self.assertEqual(len(actor.predictions), 1)
        self.assertEqual(actor.predictions[0].probability, 1.0)

    def test_trajectory_successful_none(self) -> None:
        """Test that we can set future predictions with None."""
        actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=None, past_trajectory=None)
        self.assertEqual(len(actor.predictions), 0)
        self.assertEqual(actor.past_trajectory, None)

    def test_future_trajectory_fail(self) -> None:
        """Test that we can set future predictions, but it will fail if all conditions are not met."""
        future_waypoints = self.future_waypoints
        with self.assertRaises(ValueError):
            AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=[PredictedTrajectory(waypoints=future_waypoints, probability=0.4)])

def setUp(self) -> None:
    """Setup initial waypoints."""
    self.current_time_us = int(10 * 1000000.0)
    mock_oriented_box = Mock()
    self.future_waypoints: List[Optional[Waypoint]] = [Waypoint(time_point=TimePoint(self.current_time_us), oriented_box=mock_oriented_box), Waypoint(time_point=TimePoint(self.current_time_us + int(1000000.0)), oriented_box=mock_oriented_box)]
    self.past_waypoints: List[Optional[Waypoint]] = [Waypoint(time_point=TimePoint(self.current_time_us - int(1000000.0)), oriented_box=mock_oriented_box), Waypoint(time_point=TimePoint(self.current_time_us), oriented_box=mock_oriented_box)]

def test_past_setting_successful(self) -> None:
    """Test that we can set past trajectory."""
    past_waypoints = [None] + self.past_waypoints
    actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), past_trajectory=PredictedTrajectory(waypoints=past_waypoints, probability=1.0))
    self.assertEqual(actor.past_trajectory.probability, 1.0)
    self.assertEqual(len(actor.past_trajectory.valid_waypoints), 2)
    self.assertEqual(len(actor.past_trajectory), 3)
    self.assertEqual(actor.previous_state, self.past_waypoints[0])

def test_past_setting_fail(self) -> None:
    """Test that we can raise if past trajectory does not start at current state."""
    past_waypoints = list(reversed(self.past_waypoints))
    with self.assertRaises(ValueError):
        AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), past_trajectory=PredictedTrajectory(waypoints=past_waypoints, probability=1.0))

def test_future_trajectory_successful(self) -> None:
    """Test that we can set future predictions."""
    future_waypoints = self.future_waypoints
    actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=[PredictedTrajectory(waypoints=future_waypoints, probability=1.0)])
    self.assertEqual(len(actor.predictions), 1)
    self.assertEqual(actor.predictions[0].probability, 1.0)

def test_trajectory_successful_none(self) -> None:
    """Test that we can set future predictions with None."""
    actor = AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=None, past_trajectory=None)
    self.assertEqual(len(actor.predictions), 0)
    self.assertEqual(actor.past_trajectory, None)

def test_future_trajectory_fail(self) -> None:
    """Test that we can set future predictions, but it will fail if all conditions are not met."""
    future_waypoints = self.future_waypoints
    with self.assertRaises(ValueError):
        AgentTemporalState(initial_time_stamp=TimePoint(self.current_time_us), predictions=[PredictedTrajectory(waypoints=future_waypoints, probability=0.4)])

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

class TestCarFootprint(unittest.TestCase):
    """Tests CarFoorprint class"""

    def setUp(self) -> None:
        """Sets sample parameters for testing"""
        self.center_position_from_rear_axle = get_pacifica_parameters().rear_axle_to_center

    def test_car_footprint_creation(self) -> None:
        """Checks that the car footprint is created correctly, in particular the point of interest."""
        car_footprint = CarFootprint.build_from_rear_axle(get_sample_pose(), get_pacifica_parameters())
        self.assertAlmostEqual(car_footprint.rear_axle_to_center_dist, self.center_position_from_rear_axle)
        expected_values = {OrientedBoxPointType.FRONT_BUMPER: (1.0, 6.049), OrientedBoxPointType.REAR_BUMPER: (1.0, 0.873), OrientedBoxPointType.FRONT_LEFT: (-0.1485, 6.049), OrientedBoxPointType.REAR_LEFT: (-0.1485, 0.873), OrientedBoxPointType.REAR_RIGHT: (2.1485, 0.873), OrientedBoxPointType.FRONT_RIGHT: (2.1485, 6.049), OrientedBoxPointType.CENTER: (1.0, 3.461)}
        for point, position in expected_values.items():
            np.testing.assert_array_almost_equal(position, tuple(car_footprint.corner(point)))
        np.testing.assert_array_almost_equal(expected_values[OrientedBoxPointType.FRONT_LEFT], tuple(car_footprint.get_point_of_interest(OrientedBoxPointType.FRONT_LEFT)), 6)

def setUp(self) -> None:
    """Sets sample parameters for testing"""
    self.center_position_from_rear_axle = get_pacifica_parameters().rear_axle_to_center

def test_car_footprint_creation(self) -> None:
    """Checks that the car footprint is created correctly, in particular the point of interest."""
    car_footprint = CarFootprint.build_from_rear_axle(get_sample_pose(), get_pacifica_parameters())
    self.assertAlmostEqual(car_footprint.rear_axle_to_center_dist, self.center_position_from_rear_axle)
    expected_values = {OrientedBoxPointType.FRONT_BUMPER: (1.0, 6.049), OrientedBoxPointType.REAR_BUMPER: (1.0, 0.873), OrientedBoxPointType.FRONT_LEFT: (-0.1485, 6.049), OrientedBoxPointType.REAR_LEFT: (-0.1485, 0.873), OrientedBoxPointType.REAR_RIGHT: (2.1485, 0.873), OrientedBoxPointType.FRONT_RIGHT: (2.1485, 6.049), OrientedBoxPointType.CENTER: (1.0, 3.461)}
    for point, position in expected_values.items():
        np.testing.assert_array_almost_equal(position, tuple(car_footprint.corner(point)))
    np.testing.assert_array_almost_equal(expected_values[OrientedBoxPointType.FRONT_LEFT], tuple(car_footprint.get_point_of_interest(OrientedBoxPointType.FRONT_LEFT)), 6)

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

@patch('nuplan.common.actor_state.tracked_objects_types.TrackedObjectType')
@patch('nuplan.common.actor_state.oriented_box.OrientedBox')
def test_initialization(self, mock_box: Mock, mock_tracked_object_type: Mock) -> None:
    """Tests that agents can be initialized correctly"""
    scene_object = SceneObject(mock_tracked_object_type, mock_box, SceneObjectMetadata(1, '123', 1, '456'))
    self.assertEqual('123', scene_object.token)
    self.assertEqual('456', scene_object.track_token)
    self.assertEqual(mock_box, scene_object.box)
    self.assertEqual(mock_tracked_object_type, scene_object.tracked_object_type)

def pose_from_matrix(transform_matrix: npt.NDArray[np.float32]) -> StateSE2:
    """
    Converts a 3x3 transformation matrix to a 2D pose
    :param transform_matrix: 3x3 transformation matrix
    :return: 2D pose (x, y, yaw)
    """
    if transform_matrix.shape != (3, 3):
        raise RuntimeError(f'Expected a 3x3 transformation matrix, got {transform_matrix.shape}')
    heading = np.arctan2(transform_matrix[1, 0], transform_matrix[0, 0])
    return StateSE2(transform_matrix[0, 2], transform_matrix[1, 2], heading)

def translate(pose: StateSE2, translation: npt.NDArray[np.float64]) -> StateSE2:
    """ "
    Applies a 2D translation
    :param pose: The pose to be transformed
    :param translation: The translation to be applied
    :return: The translated pose
    """
    assert translation.shape == (2,) or translation.shape == (2, 1)
    return StateSE2(pose.x + translation[0], pose.y + translation[1], pose.heading)

def rotate(pose: StateSE2, rotation_matrix: npt.NDArray[np.float64]) -> StateSE2:
    """
    Applies a 2D rotation to an SE2 Pose
    :param pose: The pose to be transformed
    :param rotation_matrix: The 2x2 rotation matrix representing the rotation
    :return: The rotated pose
    """
    assert rotation_matrix.shape == (2, 2)
    rotated_point = np.array([pose.x, pose.y]) @ rotation_matrix
    rotation_angle = np.arctan2(rotation_matrix[1, 0], rotation_matrix[1, 1])
    return StateSE2(rotated_point[0], rotated_point[1], pose.heading + rotation_angle)

def se2_box_distances(query: StateSE2, targets: list[StateSE2], box_size: Dimension, consider_flipped: bool=True) -> List[float]:
    """
    Computes the minimal distance [m] from a query to a list of targets. The distance is computed using the norm of the
    euclidean distances between the corners of a box spawned using the pose as center and given dimensions.
    The query box is also rotated by 180deg and the minimum of the two distances is used.
    :param query: The query pose.
    :param targets: The targets to compute the distance.
    :param box_size: The size of the box to be constructed.
    :param consider_flipped: Whether to also check for the same query pose, but rotated by 180 degrees.
    :return: A list of distances [m] from query to targets
    """
    query_box = OrientedBox(query, box_size.length, box_size.width, box_size.height)
    backwards_query_box = OrientedBox.from_new_pose(query_box, StateSE2(query.x, query.y, query.heading + np.pi))
    target_boxes = [OrientedBox(target, box_size.length, box_size.width, box_size.height) for target in targets]
    if consider_flipped:
        return [min(l2_euclidean_corners_distance(query_box, target_box), l2_euclidean_corners_distance(backwards_query_box, target_box)) for target_box in target_boxes]
    else:
        return [l2_euclidean_corners_distance(query_box, target_box) for target_box in target_boxes]

def _interpolate_waypoints(waypoints: List[InterpolatableState], target_timestamps: npt.NDArray[np.float64], pad_with_none: bool=True) -> List[Optional[InterpolatableState]]:
    """
    Interpolate waypoints when required from target_timestamps
    :param waypoints: to be interpolated
    :param target_timestamps: desired sampling
    :param pad_with_none: if True, the output will have None for states that can not be interpolated
    :return: list of existent interpolations, if an interpolation is not possible, it will be replaced with None
    """
    trajectory = InterpolatedTrajectory(waypoints)
    if pad_with_none:
        return [trajectory.get_state_at_time(TimePoint(t)) if trajectory.is_in_range(TimePoint(t)) else None for t in target_timestamps]
    return [trajectory.get_state_at_time(TimePoint(t)) for t in target_timestamps if trajectory.is_in_range(TimePoint(t))]

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

def test_input_numpy_array_to_absolute_velocity(self) -> None:
    """Tests input validation of numpy_array_to_absolute_velocity"""
    np_velocities = np.random.random(size=(10, 3))
    with self.assertRaises(AssertionError):
        numpy_array_to_absolute_velocity(StateSE2(0, 0, 0), np_velocities)

def test_input_numpy_array_to_absolute_pose_input(self) -> None:
    """Tests input validation of numpy_array_to_absolute_pose_input"""
    np_poses = np.random.random((10, 2))
    with self.assertRaises(AssertionError):
        numpy_array_to_absolute_pose(StateSE2(0, 0, 0), np_poses)

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

def test_translate(self) -> None:
    """Tests translate"""
    pose = StateSE2(3, 5, np.pi / 4)
    translation: npt.NDArray[np.float32] = np.array([1, 2], dtype=np.float32)
    result = translate(pose, translation)
    self.assertEqual(result, StateSE2(4, 7, np.pi / 4))

def test_rotate_angle(self) -> None:
    """Tests rotation of SE2 pose by angle (in radian)"""
    pose = StateSE2(1, 2, np.pi / 4)
    angle = -np.pi / 2
    result = rotate_angle(pose, angle)
    self.assertAlmostEqual(result.x, -2)
    self.assertAlmostEqual(result.y, 1)
    self.assertAlmostEqual(result.heading, -np.pi / 4)

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

def _serialize(self, value: float) -> float:
    """
        Converts the components into correct value before serializing
        """
    if self.serialize_to == ColorType.INT:
        return int(value * 255)
    else:
        return value

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

def test_iter_255(self) -> None:
    """
        Tests iteration of RGBA components, with color type specified as int.
        """
    result = [color for color in self.color_255]
    self.assertEqual(result[0], int(self.red * 255))
    self.assertEqual(result[1], int(self.green * 255))
    self.assertEqual(result[2], int(self.blue * 255))
    self.assertEqual(result[3], int(self.alpha * 255))

def to_scene_trajectory_state_from_ego_state(ego_state: EgoState) -> TrajectoryState:
    """
    Convert ego state into scene structure for states in a trajectory.
    :param ego_state: ego state.
    :return: state in scene format.
    """
    return TrajectoryState(pose=ego_state.rear_axle, speed=ego_state.dynamic_car_state.speed, velocity_2d=[ego_state.dynamic_car_state.rear_axle_velocity_2d.x, ego_state.dynamic_car_state.rear_axle_velocity_2d.y], lateral=[0.0, 0.0], acceleration=[ego_state.dynamic_car_state.rear_axle_acceleration_2d.x, ego_state.dynamic_car_state.rear_axle_acceleration_2d.y], tire_steering_angle=ego_state.tire_steering_angle)

def to_scene_trajectory_state_from_waypoint(waypoint: Waypoint) -> TrajectoryState:
    """
    Convert ego state into scene structure for states in a trajectory.
    :param waypoint: waypoint in a trajectory.
    :return: state in scene format.
    """
    return TrajectoryState(pose=waypoint.center, speed=waypoint.velocity.magnitude(), velocity_2d=[waypoint.velocity.x, waypoint.velocity.y] if waypoint.velocity else [0, 0], lateral=[0.0, 0.0])

def to_scene_from_ego_and_boxes(ego_pose: StateSE2, tracked_objects: TrackedObjects, map_name: str, set_camera: bool=False) -> Dict[str, Any]:
    """
    Extract scene from ego_pose and boxes.
    :param ego_pose: Ego Position.
    :param tracked_objects: list of actors in global coordinate frame.
    :param map_name: map name.
    :param set_camera: True if we wish to also set camera view.
    :return scene.
    """
    world = to_scene_boxes(tracked_objects)
    map_name_without_suffix = str(pathlib.Path(map_name).stem)
    scene: Dict[str, Any] = {'map': {'area': map_name_without_suffix}, 'world': world, 'ego': dict(to_scene_ego_from_car_footprint(CarFootprint.build_from_center(ego_pose, get_pacifica_parameters())))}
    if set_camera:
        ego_pose = scene['ego']['pose']
        ego_x = ego_pose[0]
        ego_y = ego_pose[1]
        ego_heading = ego_pose[2]
        bearing_rad = np.fmod(ego_heading, np.pi * 2)
        if bearing_rad < 0:
            bearing_rad += np.pi * 2
        bearing_rad = 1.75 - bearing_rad / (np.pi * 2)
        if bearing_rad >= 1:
            bearing_rad -= 1.0
        scene['camera'] = {'pitch': 50, 'scale': 2500000, 'bearing': bearing_rad, 'lookat': [ego_x, ego_y, 0.0]}
    return scene

class SceneSimpleTrajectory(AbstractTrajectory):
    """
    Simple trajectory that is used to represent scene's predictions.
    """

    def __init__(self, prediction_states: List[Dict[str, Any]], width: float, length: float, height: float):
        """
        Constructor.

        :param prediction_states: Dictionary of states.
        :param width: [m] Width of the agent.
        :param length: [m] Length of the agent.
        :param height: [m] Height of the agent.
        """
        self._states: List[Waypoint] = []
        self._state_at_time: Dict[TimePoint, Waypoint] = {}
        for state in prediction_states:
            time = TimePoint(int(state['timestamp'] * 1000000.0))
            coordinates: List[float] = state['pose']
            center = StateSE2(x=coordinates[0], y=coordinates[1], heading=coordinates[2])
            self._states.append(Waypoint(time_point=time, oriented_box=OrientedBox(center=center, width=width, length=length, height=height)))
            self._state_at_time[time] = self._states[-1]
        self._start_time = prediction_states[0]['timestamp']
        self._end_time = prediction_states[-1]['timestamp']

    @property
    def start_time(self) -> TimePoint:
        """
        Get the trajectory start time.
        :return: Start time.
        """
        return self._start_time

    @property
    def end_time(self) -> TimePoint:
        """
        Get the trajectory end time.
        :return: End time.
        """
        return self._end_time

    def get_state_at_time(self, time_point: TimePoint) -> Any:
        """
        Get the state of the actor at the specified time point.
        :param time_point: Time for which are want to query a state.
        :return: State at the specified time.

        :raises Exception: Throws an exception in case a time_point is beyond range of a trajectory.
        """
        return self._state_at_time[time_point]

    def get_state_at_times(self, time_points: List[TimePoint]) -> List[Any]:
        """Inherited, see superclass."""
        raise NotImplementedError

    def get_sampled_trajectory(self) -> List[Any]:
        """
        Get the sampled states along the trajectory.
        :return: Discrete trajectory consisting of states.
        """
        return self._states

def __init__(self, prediction_states: List[Dict[str, Any]], width: float, length: float, height: float):
    """
        Constructor.

        :param prediction_states: Dictionary of states.
        :param width: [m] Width of the agent.
        :param length: [m] Length of the agent.
        :param height: [m] Height of the agent.
        """
    self._states: List[Waypoint] = []
    self._state_at_time: Dict[TimePoint, Waypoint] = {}
    for state in prediction_states:
        time = TimePoint(int(state['timestamp'] * 1000000.0))
        coordinates: List[float] = state['pose']
        center = StateSE2(x=coordinates[0], y=coordinates[1], heading=coordinates[2])
        self._states.append(Waypoint(time_point=time, oriented_box=OrientedBox(center=center, width=width, length=length, height=height)))
        self._state_at_time[time] = self._states[-1]
    self._start_time = prediction_states[0]['timestamp']
    self._end_time = prediction_states[-1]['timestamp']

def to_state_from_scene(scene: Dict[str, Any]) -> StateSE2:
    """
    Extract state se2 from pose.
    :param scene: position from scene.
    :return StateSE2.
    """
    return StateSE2(x=scene['pose'][0], y=scene['pose'][1], heading=scene['pose'][2])

def to_agent_state_from_scene(scene: Dict[str, Any], vehicle: VehicleParameters, time_us: int=10, to_cog: bool=True) -> EgoState:
    """
    Extract agent state from scene.
    :param scene: from json.
    :param vehicle: parameters.
    :param time_us: [us] initial time.
    :param to_cog: If true, xy will be translated to the COG of the car. Otherwise xy is assumed to be at rear axle.
    :return EgoState.
    """
    if to_cog:
        ego_state2d = to_ego_center_from_scene(scene, vehicle)
    else:
        ego_pose = scene['pose']
        ego_state2d = StateSE2(ego_pose[0], ego_pose[1], ego_pose[2])
    if 'velocity_x' not in scene or 'velocity_y' not in scene:
        velocity_x = scene['speed']
        velocity_y = 0.0
    else:
        velocity_x = scene['velocity_x']
        velocity_y = scene['velocity_y']
    if 'acceleration_x' not in scene or 'acceleration_y' not in scene:
        acceleration_x = scene['acceleration']
        acceleration_y = 0.0
    else:
        acceleration_x = scene['acceleration_x']
        acceleration_y = scene['acceleration_y']
    return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(x=ego_state2d.x, y=ego_state2d.y, heading=ego_state2d.heading), time_point=TimePoint(time_us), rear_axle_velocity_2d=StateVector2D(x=velocity_x, y=velocity_y), rear_axle_acceleration_2d=StateVector2D(x=acceleration_x, y=acceleration_y), tire_steering_angle=0, vehicle_parameters=get_pacifica_parameters())

def from_scene_tracked_object(scene: Dict[str, Any], object_type: TrackedObjectType) -> TrackedObject:
    """
    Convert scene to a TrackedObject.
    :param scene: scene of an agent.
    :param object_type: type of the resulting object.
    :return Agent extracted from a scene.
    """
    token = scene['id']
    box = scene['box']
    pose = box['pose']
    size = box['size'] if 'size' in box.keys() else [0.5, 0.5]
    default_height = 1.5
    box = OrientedBox(StateSE2(*pose), width=size[0], length=size[1], height=default_height)
    if object_type in AGENT_TYPES:
        return Agent(metadata=SceneObjectMetadata(token=str(token), track_token=str(token), track_id=token, timestamp_us=0), tracked_object_type=object_type, oriented_box=box, velocity=StateVector2D(scene['speed'], 0))
    else:
        return StaticObject(metadata=SceneObjectMetadata(token=str(token), track_token=str(token), track_id=token, timestamp_us=0), tracked_object_type=object_type, oriented_box=box)

def from_scene_to_tracked_objects_with_scene_predictions(scene: Dict[str, Any]) -> TrackedObjects:
    """
    Creates tracked objects, loading the predictions directly from the scene json.
    :param scene: The input scene loaded from the json file.
    :return: Tracked objects from the scene, with predictions loaded from the scene json.
    """
    tracked_objects = from_scene_to_tracked_objects(scene['world'])
    tracked_objects_map: Dict[str, TrackedObject] = {track.token: track for track in tracked_objects}
    for prediction in scene['prediction']:
        prediction_id = str(prediction['id'])
        if prediction_id not in tracked_objects_map:
            logger.warning('Json scene file contains prediction not assigned to any track: %s.', prediction_id)
            continue
        box = tracked_objects_map[prediction_id].box
        current_state = {'timestamp': tracked_objects_map[prediction_id].metadata.timestamp_s, 'pose': list(tracked_objects_map[prediction_id].center)}
        tracked_objects_map[prediction_id].predictions = [PredictedTrajectory(probability=mode['probability'], waypoints=SceneSimpleTrajectory(_validate_an_unite_predictions(current_state, mode['states']), width=box.width, length=box.length, height=box.height).get_sampled_trajectory()) for mode in prediction['modes']]
    return tracked_objects

def from_scene_to_tracked_objects_with_predictions(scene: Dict[str, Any], predictions: List[Dict[str, Any]]) -> TrackedObjects:
    """
    Creates tracked objects, adding prediction from the given parameter.
    :param scene: The input scene loaded from the json file.
    :param predictions: Predictions for the tracked objects in the scene.
    :return: Tracked objects from the scene, with predictions loaded from the input.
    """
    tracked_objects = from_scene_to_tracked_objects(scene)
    for tracked_object in tracked_objects:
        for prediction in predictions:
            if str(prediction['id']) == str(tracked_object.token):
                box = tracked_object.box
                tracked_object.predictions = [PredictedTrajectory(probability=1.0, waypoints=SceneSimpleTrajectory(prediction['states'], width=box.width, length=box.length, height=box.height).get_sampled_trajectory())]
                del prediction
                break
    return tracked_objects

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

class TestLogFuturePredictor(unittest.TestCase):
    """
    Test LogFuturePredictor class.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.scenario = MockAbstractScenario()
        self.future_trajectory_sampling = TrajectorySampling(num_poses=1, time_horizon=1.0)
        self.predictor = LogFuturePredictor(self.scenario, self.future_trajectory_sampling)

    def test_compute_predicted_trajectories(self) -> None:
        """Test compute_predicted_trajectories."""
        predictor_input = get_mock_predictor_input()
        start_time = time.perf_counter()
        detections = self.predictor.compute_predictions(predictor_input)
        compute_predictions_time = time.perf_counter() - start_time
        _, input_detections = predictor_input.history.current_state
        self.assertEqual(len(detections.tracked_objects), len(input_detections.tracked_objects))
        for agent in detections.tracked_objects.get_agents():
            self.assertTrue(agent.predictions is not None)
            for prediction in agent.predictions:
                self.assertEqual(len(prediction.valid_waypoints), self.future_trajectory_sampling.num_poses)
        predictor_report = self.predictor.generate_predictor_report()
        self.assertEqual(len(predictor_report.compute_predictions_runtimes), 1)
        self.assertNotIsInstance(predictor_report, MLPredictorReport)
        self.assertAlmostEqual(predictor_report.compute_predictions_runtimes[0], compute_predictions_time, delta=0.1)

def setUp(self) -> None:
    """Inherited, see superclass."""
    self.scenario = MockAbstractScenario()
    self.future_trajectory_sampling = TrajectorySampling(num_poses=1, time_horizon=1.0)
    self.predictor = LogFuturePredictor(self.scenario, self.future_trajectory_sampling)

def get_mock_predictor_input(buffer_size: int=1) -> PredictorInput:
    """
    Returns a mock PredictorInput for testing.
    :return: PredictorInput.
    """
    scenario = MockAbstractScenario()
    history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size, [scenario.initial_ego_state for _ in range(buffer_size)], [scenario.initial_tracked_objects for _ in range(buffer_size)], 0.5)
    return PredictorInput(iteration=SimulationIteration(TimePoint(0), 0), history=history_buffer, traffic_light_data=None)

class TwoStageController(AbstractEgoController):
    """
    Implements a two stage tracking controller. The two stages comprises of:
        1. an AbstractTracker - This is to simulate a low level controller layer that is present in real AVs.
        2. an AbstractMotionModel - Describes how the AV evolves according to a physical model.
    """

    def __init__(self, scenario: AbstractScenario, tracker: AbstractTracker, motion_model: AbstractMotionModel):
        """
        Constructor for TwoStageController
        :param scenario: Scenario
        :param tracker: The tracker used to compute control actions
        :param motion_model: The motion model to propagate the control actions
        """
        self._scenario = scenario
        self._tracker = tracker
        self._motion_model = motion_model
        self._current_state: Optional[EgoState] = None

    def reset(self) -> None:
        """Inherited, see superclass."""
        self._current_state = None

    def get_state(self) -> EgoState:
        """Inherited, see superclass."""
        if self._current_state is None:
            self._current_state = self._scenario.initial_ego_state
        return self._current_state

    def update_state(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, ego_state: EgoState, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        sampling_time = next_iteration.time_point - current_iteration.time_point
        dynamic_state = self._tracker.track_trajectory(current_iteration, next_iteration, ego_state, trajectory)
        self._current_state = self._motion_model.propagate_state(state=ego_state, ideal_dynamic_state=dynamic_state, sampling_time=sampling_time)

def update_state(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, ego_state: EgoState, trajectory: AbstractTrajectory) -> None:
    """Inherited, see superclass."""
    sampling_time = next_iteration.time_point - current_iteration.time_point
    dynamic_state = self._tracker.track_trajectory(current_iteration, next_iteration, ego_state, trajectory)
    self._current_state = self._motion_model.propagate_state(state=ego_state, ideal_dynamic_state=dynamic_state, sampling_time=sampling_time)

class PerfectTrackingController(AbstractEgoController):
    """
    Assume tracking controller is absolutely perfect, and just follow a trajectory.
    """

    def __init__(self, scenario: AbstractScenario):
        """
        Constructor of PerfectTrackingController.
        :param scenario: scenario to run through.
        """
        self.scenario = scenario
        self.current_state = None

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_state = None

    def get_state(self) -> EgoState:
        """Inherited, see superclass."""
        if self.current_state is None:
            self.current_state = self.scenario.initial_ego_state
        return self.current_state

    def update_state(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, ego_state: EgoState, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        self.current_state = trajectory.get_state_at_time(next_iteration.time_point)
        assert self.current_state is not None, 'Current state of controller cannot be None'
        very_large_velocity_threshold = 50
        if self.current_state.dynamic_car_state.speed >= very_large_velocity_threshold:
            raise RuntimeError(f'Velocity is too high: {self.current_state.dynamic_car_state.speed}!')

def update_state(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, ego_state: EgoState, trajectory: AbstractTrajectory) -> None:
    """Inherited, see superclass."""
    self.current_state = trajectory.get_state_at_time(next_iteration.time_point)
    assert self.current_state is not None, 'Current state of controller cannot be None'
    very_large_velocity_threshold = 50
    if self.current_state.dynamic_car_state.speed >= very_large_velocity_threshold:
        raise RuntimeError(f'Velocity is too high: {self.current_state.dynamic_car_state.speed}!')

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

def test_forward_integrate(self) -> None:
    """
        Test forward_integrate.
        """
    for init, delta, sampling_time in zip(self.inits, self.deltas, self.sampling_times):
        result = forward_integrate(init, delta, TimePoint(sampling_time))
        expect = init + delta * sampling_time * 1e-06
        self.assertAlmostEqual(result, expect)

def get_interpolated_reference_trajectory_poses(trajectory: AbstractTrajectory, discretization_time: float) -> Tuple[DoubleMatrix, DoubleMatrix]:
    """
    Resamples the reference trajectory at discretization_time resolution.
    It will return N times and poses, where N is a function of the trajectory duration and the discretization time.
    :param trajectory: The full trajectory from which we perform pose interpolation.
    :param discretization_time: [s] The discretization time for resampling the trajectory.
    :return An array of times in seconds (N) and an array of associated poses (N,3), sampled at the discretization time.
    """
    start_time_point = trajectory.start_time
    end_time_point = trajectory.end_time
    delta_time_point = TimePoint(int(discretization_time * 1000000.0))
    interpolation_times_us = np.arange(start_time_point.time_us, end_time_point.time_us, delta_time_point.time_us)
    if interpolation_times_us[-1] + delta_time_point.time_us <= end_time_point.time_us:
        interpolation_times_us = np.append(interpolation_times_us, interpolation_times_us[-1] + delta_time_point.time_us)
    interpolation_time_points = [TimePoint(t_us) for t_us in interpolation_times_us]
    states = trajectory.get_state_at_times(interpolation_time_points)
    poses_interp = [[*state.rear_axle] for state in states]
    return (interpolation_times_us / 1000000.0, np.array(poses_interp))

class ILQRTracker(AbstractTracker):
    """
    Tracker using an iLQR solver with a kinematic bicycle model.
    """

    def __init__(self, n_horizon: int, ilqr_solver: ILQRSolver) -> None:
        """
        Initialize tracker parameters, primarily the iLQR solver.
        :param n_horizon: Maximum time horizon (number of discrete time steps) that we should plan ahead.
                          Please note the associated discretization_time is specified in the ilqr_solver.
        :param ilqr_solver: Solver used to compute inputs to apply.
        """
        assert n_horizon > 0, 'The time horizon length should be positive.'
        self._n_horizon = n_horizon
        self._ilqr_solver = ilqr_solver

    def track_trajectory(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, initial_state: EgoState, trajectory: AbstractTrajectory) -> DynamicCarState:
        """Inherited, see superclass."""
        current_state: DoubleMatrix = np.array([initial_state.rear_axle.x, initial_state.rear_axle.y, initial_state.rear_axle.heading, initial_state.dynamic_car_state.rear_axle_velocity_2d.x, initial_state.tire_steering_angle])
        reference_trajectory = self._get_reference_trajectory(current_iteration, trajectory)
        solutions = self._ilqr_solver.solve(current_state, reference_trajectory)
        optimal_inputs = solutions[-1].input_trajectory
        accel_cmd = optimal_inputs[0, 0]
        steering_rate_cmd = optimal_inputs[0, 1]
        return DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=initial_state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=initial_state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel_cmd, 0), tire_steering_rate=steering_rate_cmd)

    def _get_reference_trajectory(self, current_iteration: SimulationIteration, trajectory: AbstractTrajectory) -> DoubleMatrix:
        """
        Determines reference trajectory, (z_{ref,k})_k=0^self._n_horizon.
        In case the query timestep exceeds the trajectory length, we return a smaller trajectory (z_{ref,k})_k=0^M,
        where M < self._n_horizon.  The shorter reference will then be handled downstream by the solver appropriately.
        :param current_iteration: Provides the current time from which we interpolate.
        :param trajectory: The full planned trajectory from which we perform state interpolation.
        :return a (M+1 or self._n_horizon+1) by self._n_states array.
        """
        assert trajectory.start_time.time_s <= current_iteration.time_s, 'Current time is before trajectory start.'
        assert current_iteration.time_s <= trajectory.end_time.time_s, 'Current time is after trajectory end'
        discretization_time = self._ilqr_solver._solver_params.discretization_time
        time_deltas_s: DoubleMatrix = np.array([x * discretization_time for x in range(0, self._n_horizon + 1)], dtype=np.float64)
        states_interp = []
        for tm_delta_s in time_deltas_s:
            timepoint = TimePoint(int(tm_delta_s * 1000000.0)) + current_iteration.time_point
            if timepoint > trajectory.end_time:
                break
            state = trajectory.get_state_at_time(timepoint)
            states_interp.append([state.rear_axle.x, state.rear_axle.y, state.rear_axle.heading, state.dynamic_car_state.rear_axle_velocity_2d.x, state.tire_steering_angle])
        return np.array(states_interp)

def track_trajectory(self, current_iteration: SimulationIteration, next_iteration: SimulationIteration, initial_state: EgoState, trajectory: AbstractTrajectory) -> DynamicCarState:
    """Inherited, see superclass."""
    current_state: DoubleMatrix = np.array([initial_state.rear_axle.x, initial_state.rear_axle.y, initial_state.rear_axle.heading, initial_state.dynamic_car_state.rear_axle_velocity_2d.x, initial_state.tire_steering_angle])
    reference_trajectory = self._get_reference_trajectory(current_iteration, trajectory)
    solutions = self._ilqr_solver.solve(current_state, reference_trajectory)
    optimal_inputs = solutions[-1].input_trajectory
    accel_cmd = optimal_inputs[0, 0]
    steering_rate_cmd = optimal_inputs[0, 1]
    return DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=initial_state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=initial_state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel_cmd, 0), tire_steering_rate=steering_rate_cmd)

def _get_reference_trajectory(self, current_iteration: SimulationIteration, trajectory: AbstractTrajectory) -> DoubleMatrix:
    """
        Determines reference trajectory, (z_{ref,k})_k=0^self._n_horizon.
        In case the query timestep exceeds the trajectory length, we return a smaller trajectory (z_{ref,k})_k=0^M,
        where M < self._n_horizon.  The shorter reference will then be handled downstream by the solver appropriately.
        :param current_iteration: Provides the current time from which we interpolate.
        :param trajectory: The full planned trajectory from which we perform state interpolation.
        :return a (M+1 or self._n_horizon+1) by self._n_states array.
        """
    assert trajectory.start_time.time_s <= current_iteration.time_s, 'Current time is before trajectory start.'
    assert current_iteration.time_s <= trajectory.end_time.time_s, 'Current time is after trajectory end'
    discretization_time = self._ilqr_solver._solver_params.discretization_time
    time_deltas_s: DoubleMatrix = np.array([x * discretization_time for x in range(0, self._n_horizon + 1)], dtype=np.float64)
    states_interp = []
    for tm_delta_s in time_deltas_s:
        timepoint = TimePoint(int(tm_delta_s * 1000000.0)) + current_iteration.time_point
        if timepoint > trajectory.end_time:
            break
        state = trajectory.get_state_at_time(timepoint)
        states_interp.append([state.rear_axle.x, state.rear_axle.y, state.rear_axle.heading, state.dynamic_car_state.rear_axle_velocity_2d.x, state.tire_steering_angle])
    return np.array(states_interp)

class TestILQRTracker(unittest.TestCase):
    """
    Tests the functionality of the ILQRTracker class.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.initial_time_point = TimePoint(1000000)
        self.scenario = MockAbstractScenario(initial_time_us=self.initial_time_point)
        self.trajectory = InterpolatedTrajectory(list(self.scenario.get_expert_ego_trajectory()))
        solver_params = ILQRSolverParameters(discretization_time=0.2, state_cost_diagonal_entries=[1.0, 1.0, 10.0, 0.0, 0.0], input_cost_diagonal_entries=[1.0, 10.0], state_trust_region_entries=[1.0] * 5, input_trust_region_entries=[1.0] * 2, max_ilqr_iterations=100, convergence_threshold=1e-06, max_solve_time=0.05, max_acceleration=3.0, max_steering_angle=np.pi / 3.0, max_steering_angle_rate=0.5, min_velocity_linearization=0.01)
        warm_start_params = ILQRWarmStartParameters(k_velocity_error_feedback=0.5, k_steering_angle_error_feedback=0.05, lookahead_distance_lateral_error=15.0, k_lateral_error=0.1, jerk_penalty_warm_start_fit=0.0001, curvature_rate_penalty_warm_start_fit=0.01)
        self.tracker = ILQRTracker(n_horizon=40, ilqr_solver=ILQRSolver(solver_params=solver_params, warm_start_params=warm_start_params))
        self.discretization_time_us = int(1000000.0 * self.tracker._ilqr_solver._solver_params.discretization_time)

    def test_track_trajectory(self) -> None:
        """Ensure that we can run a single solver call to track a trajectory."""
        current_iteration = SimulationIteration(time_point=self.initial_time_point, index=0)
        time_point_delta = TimePoint(self.discretization_time_us)
        next_iteration = SimulationIteration(time_point=self.initial_time_point + time_point_delta, index=1)
        self.tracker.track_trajectory(current_iteration=current_iteration, next_iteration=next_iteration, initial_state=self.scenario.initial_ego_state, trajectory=self.trajectory)

    def test__get_reference_trajectory(self) -> None:
        """Test reference trajectory extraction for the solver."""
        current_iteration_before_trajectory_start = SimulationIteration(time_point=self.trajectory.start_time - TimePoint(1), index=0)
        with self.assertRaises(AssertionError):
            self.tracker._get_reference_trajectory(current_iteration_before_trajectory_start, self.trajectory)
        current_iteration_after_trajectory_end = SimulationIteration(time_point=self.trajectory.end_time + TimePoint(1), index=0)
        with self.assertRaises(AssertionError):
            self.tracker._get_reference_trajectory(current_iteration_after_trajectory_end, self.trajectory)
        start_time_us = self.trajectory.start_time.time_us
        end_time_us = self.trajectory.end_time.time_us
        mid_time_us = int((start_time_us + end_time_us) / 2)
        for test_time_us in [start_time_us, mid_time_us, end_time_us]:
            expected_trajectory_length = min((end_time_us - test_time_us) // self.discretization_time_us + 1, self.tracker._n_horizon + 1)
            current_iteration = SimulationIteration(time_point=TimePoint(test_time_us), index=0)
            reference_trajectory = self.tracker._get_reference_trajectory(current_iteration, self.trajectory)
            self.assertEqual(len(reference_trajectory), expected_trajectory_length)
            first_state_reference_trajectory = reference_trajectory[0]
            first_ego_state_expected = self.trajectory.get_state_at_time(current_iteration.time_point)
            np_test.assert_allclose(first_state_reference_trajectory[0], first_ego_state_expected.rear_axle.x)
            np_test.assert_allclose(first_state_reference_trajectory[1], first_ego_state_expected.rear_axle.y)
            np_test.assert_allclose(first_state_reference_trajectory[2], first_ego_state_expected.rear_axle.heading)
            np_test.assert_allclose(first_state_reference_trajectory[3], first_ego_state_expected.dynamic_car_state.rear_axle_velocity_2d.x)
            np_test.assert_allclose(first_state_reference_trajectory[4], first_ego_state_expected.tire_steering_angle)

def setUp(self) -> None:
    """Inherited, see superclass."""
    self.initial_time_point = TimePoint(1000000)
    self.scenario = MockAbstractScenario(initial_time_us=self.initial_time_point)
    self.trajectory = InterpolatedTrajectory(list(self.scenario.get_expert_ego_trajectory()))
    solver_params = ILQRSolverParameters(discretization_time=0.2, state_cost_diagonal_entries=[1.0, 1.0, 10.0, 0.0, 0.0], input_cost_diagonal_entries=[1.0, 10.0], state_trust_region_entries=[1.0] * 5, input_trust_region_entries=[1.0] * 2, max_ilqr_iterations=100, convergence_threshold=1e-06, max_solve_time=0.05, max_acceleration=3.0, max_steering_angle=np.pi / 3.0, max_steering_angle_rate=0.5, min_velocity_linearization=0.01)
    warm_start_params = ILQRWarmStartParameters(k_velocity_error_feedback=0.5, k_steering_angle_error_feedback=0.05, lookahead_distance_lateral_error=15.0, k_lateral_error=0.1, jerk_penalty_warm_start_fit=0.0001, curvature_rate_penalty_warm_start_fit=0.01)
    self.tracker = ILQRTracker(n_horizon=40, ilqr_solver=ILQRSolver(solver_params=solver_params, warm_start_params=warm_start_params))
    self.discretization_time_us = int(1000000.0 * self.tracker._ilqr_solver._solver_params.discretization_time)

def test_track_trajectory(self) -> None:
    """Ensure that we can run a single solver call to track a trajectory."""
    current_iteration = SimulationIteration(time_point=self.initial_time_point, index=0)
    time_point_delta = TimePoint(self.discretization_time_us)
    next_iteration = SimulationIteration(time_point=self.initial_time_point + time_point_delta, index=1)
    self.tracker.track_trajectory(current_iteration=current_iteration, next_iteration=next_iteration, initial_state=self.scenario.initial_ego_state, trajectory=self.trajectory)

def test__get_reference_trajectory(self) -> None:
    """Test reference trajectory extraction for the solver."""
    current_iteration_before_trajectory_start = SimulationIteration(time_point=self.trajectory.start_time - TimePoint(1), index=0)
    with self.assertRaises(AssertionError):
        self.tracker._get_reference_trajectory(current_iteration_before_trajectory_start, self.trajectory)
    current_iteration_after_trajectory_end = SimulationIteration(time_point=self.trajectory.end_time + TimePoint(1), index=0)
    with self.assertRaises(AssertionError):
        self.tracker._get_reference_trajectory(current_iteration_after_trajectory_end, self.trajectory)
    start_time_us = self.trajectory.start_time.time_us
    end_time_us = self.trajectory.end_time.time_us
    mid_time_us = int((start_time_us + end_time_us) / 2)
    for test_time_us in [start_time_us, mid_time_us, end_time_us]:
        expected_trajectory_length = min((end_time_us - test_time_us) // self.discretization_time_us + 1, self.tracker._n_horizon + 1)
        current_iteration = SimulationIteration(time_point=TimePoint(test_time_us), index=0)
        reference_trajectory = self.tracker._get_reference_trajectory(current_iteration, self.trajectory)
        self.assertEqual(len(reference_trajectory), expected_trajectory_length)
        first_state_reference_trajectory = reference_trajectory[0]
        first_ego_state_expected = self.trajectory.get_state_at_time(current_iteration.time_point)
        np_test.assert_allclose(first_state_reference_trajectory[0], first_ego_state_expected.rear_axle.x)
        np_test.assert_allclose(first_state_reference_trajectory[1], first_ego_state_expected.rear_axle.y)
        np_test.assert_allclose(first_state_reference_trajectory[2], first_ego_state_expected.rear_axle.heading)
        np_test.assert_allclose(first_state_reference_trajectory[3], first_ego_state_expected.dynamic_car_state.rear_axle_velocity_2d.x)
        np_test.assert_allclose(first_state_reference_trajectory[4], first_ego_state_expected.tire_steering_angle)

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

class KinematicBicycleModel(AbstractMotionModel):
    """
    A class describing the kinematic motion model where the rear axle is the point of reference.
    """

    def __init__(self, vehicle: VehicleParameters, max_steering_angle: float=np.pi / 3, accel_time_constant: float=0.2, steering_angle_time_constant: float=0.05):
        """
        Construct KinematicBicycleModel.

        :param vehicle: Vehicle parameters.
        :param max_steering_angle: [rad] Maximum absolute value steering angle allowed by model.
        :param accel_time_constant: low pass filter time constant for acceleration in s
        :param steering_angle_time_constant: low pass filter time constant for steering angle in s
        """
        self._vehicle = vehicle
        self._max_steering_angle = max_steering_angle
        self._accel_time_constant = accel_time_constant
        self._steering_angle_time_constant = steering_angle_time_constant

    def get_state_dot(self, state: EgoState) -> EgoStateDot:
        """Inherited, see super class."""
        longitudinal_speed = state.dynamic_car_state.rear_axle_velocity_2d.x
        x_dot = longitudinal_speed * np.cos(state.rear_axle.heading)
        y_dot = longitudinal_speed * np.sin(state.rear_axle.heading)
        yaw_dot = longitudinal_speed * np.tan(state.tire_steering_angle) / self._vehicle.wheel_base
        return EgoStateDot.build_from_rear_axle(rear_axle_pose=StateSE2(x=x_dot, y=y_dot, heading=yaw_dot), rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_acceleration_2d, rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_angle=state.dynamic_car_state.tire_steering_rate, time_point=state.time_point, is_in_auto_mode=True, vehicle_parameters=self._vehicle)

    def _update_commands(self, state: EgoState, ideal_dynamic_state: DynamicCarState, sampling_time: TimePoint) -> EgoState:
        """
        This function applies some first order control delay/a low pass filter to acceleration/steering.

        :param state: Ego state
        :param ideal_dynamic_state: The desired dynamic state for propagation
        :param sampling_time: The time duration to propagate for
        :return: propagating_state including updated dynamic_state
        """
        dt_control = sampling_time.time_s
        accel = state.dynamic_car_state.rear_axle_acceleration_2d.x
        steering_angle = state.tire_steering_angle
        ideal_accel_x = ideal_dynamic_state.rear_axle_acceleration_2d.x
        ideal_steering_angle = dt_control * ideal_dynamic_state.tire_steering_rate + steering_angle
        updated_accel_x = dt_control / (dt_control + self._accel_time_constant) * (ideal_accel_x - accel) + accel
        updated_steering_angle = dt_control / (dt_control + self._steering_angle_time_constant) * (ideal_steering_angle - steering_angle) + steering_angle
        updated_steering_rate = (updated_steering_angle - steering_angle) / dt_control
        dynamic_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(updated_accel_x, 0), tire_steering_rate=updated_steering_rate)
        propagating_state = EgoState(car_footprint=state.car_footprint, dynamic_car_state=dynamic_state, tire_steering_angle=state.tire_steering_angle, is_in_auto_mode=True, time_point=state.time_point)
        return propagating_state

    def propagate_state(self, state: EgoState, ideal_dynamic_state: DynamicCarState, sampling_time: TimePoint) -> EgoState:
        """Inherited, see super class."""
        propagating_state = self._update_commands(state, ideal_dynamic_state, sampling_time)
        state_dot = self.get_state_dot(propagating_state)
        next_x = forward_integrate(propagating_state.rear_axle.x, state_dot.rear_axle.x, sampling_time)
        next_y = forward_integrate(propagating_state.rear_axle.y, state_dot.rear_axle.y, sampling_time)
        next_heading = forward_integrate(propagating_state.rear_axle.heading, state_dot.rear_axle.heading, sampling_time)
        next_heading = principal_value(next_heading)
        next_point_velocity_x = forward_integrate(propagating_state.dynamic_car_state.rear_axle_velocity_2d.x, state_dot.dynamic_car_state.rear_axle_velocity_2d.x, sampling_time)
        next_point_velocity_y = 0.0
        next_point_tire_steering_angle = np.clip(forward_integrate(propagating_state.tire_steering_angle, state_dot.tire_steering_angle, sampling_time), -self._max_steering_angle, self._max_steering_angle)
        next_point_angular_velocity = next_point_velocity_x * np.tan(next_point_tire_steering_angle) / self._vehicle.wheel_base
        rear_axle_accel = [state_dot.dynamic_car_state.rear_axle_velocity_2d.x, state_dot.dynamic_car_state.rear_axle_velocity_2d.y]
        angular_accel = (next_point_angular_velocity - state.dynamic_car_state.angular_velocity) / sampling_time.time_s
        return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(next_x, next_y, next_heading), rear_axle_velocity_2d=StateVector2D(next_point_velocity_x, next_point_velocity_y), rear_axle_acceleration_2d=StateVector2D(rear_axle_accel[0], rear_axle_accel[1]), tire_steering_angle=float(next_point_tire_steering_angle), time_point=propagating_state.time_point + sampling_time, vehicle_parameters=self._vehicle, is_in_auto_mode=True, angular_vel=next_point_angular_velocity, angular_accel=angular_accel, tire_steering_rate=state_dot.tire_steering_angle)

def _update_commands(self, state: EgoState, ideal_dynamic_state: DynamicCarState, sampling_time: TimePoint) -> EgoState:
    """
        This function applies some first order control delay/a low pass filter to acceleration/steering.

        :param state: Ego state
        :param ideal_dynamic_state: The desired dynamic state for propagation
        :param sampling_time: The time duration to propagate for
        :return: propagating_state including updated dynamic_state
        """
    dt_control = sampling_time.time_s
    accel = state.dynamic_car_state.rear_axle_acceleration_2d.x
    steering_angle = state.tire_steering_angle
    ideal_accel_x = ideal_dynamic_state.rear_axle_acceleration_2d.x
    ideal_steering_angle = dt_control * ideal_dynamic_state.tire_steering_rate + steering_angle
    updated_accel_x = dt_control / (dt_control + self._accel_time_constant) * (ideal_accel_x - accel) + accel
    updated_steering_angle = dt_control / (dt_control + self._steering_angle_time_constant) * (ideal_steering_angle - steering_angle) + steering_angle
    updated_steering_rate = (updated_steering_angle - steering_angle) / dt_control
    dynamic_state = DynamicCarState.build_from_rear_axle(rear_axle_to_center_dist=state.car_footprint.rear_axle_to_center_dist, rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(updated_accel_x, 0), tire_steering_rate=updated_steering_rate)
    propagating_state = EgoState(car_footprint=state.car_footprint, dynamic_car_state=dynamic_state, tire_steering_angle=state.tire_steering_angle, is_in_auto_mode=True, time_point=state.time_point)
    return propagating_state

def propagate_state(self, state: EgoState, ideal_dynamic_state: DynamicCarState, sampling_time: TimePoint) -> EgoState:
    """Inherited, see super class."""
    propagating_state = self._update_commands(state, ideal_dynamic_state, sampling_time)
    state_dot = self.get_state_dot(propagating_state)
    next_x = forward_integrate(propagating_state.rear_axle.x, state_dot.rear_axle.x, sampling_time)
    next_y = forward_integrate(propagating_state.rear_axle.y, state_dot.rear_axle.y, sampling_time)
    next_heading = forward_integrate(propagating_state.rear_axle.heading, state_dot.rear_axle.heading, sampling_time)
    next_heading = principal_value(next_heading)
    next_point_velocity_x = forward_integrate(propagating_state.dynamic_car_state.rear_axle_velocity_2d.x, state_dot.dynamic_car_state.rear_axle_velocity_2d.x, sampling_time)
    next_point_velocity_y = 0.0
    next_point_tire_steering_angle = np.clip(forward_integrate(propagating_state.tire_steering_angle, state_dot.tire_steering_angle, sampling_time), -self._max_steering_angle, self._max_steering_angle)
    next_point_angular_velocity = next_point_velocity_x * np.tan(next_point_tire_steering_angle) / self._vehicle.wheel_base
    rear_axle_accel = [state_dot.dynamic_car_state.rear_axle_velocity_2d.x, state_dot.dynamic_car_state.rear_axle_velocity_2d.y]
    angular_accel = (next_point_angular_velocity - state.dynamic_car_state.angular_velocity) / sampling_time.time_s
    return EgoState.build_from_rear_axle(rear_axle_pose=StateSE2(next_x, next_y, next_heading), rear_axle_velocity_2d=StateVector2D(next_point_velocity_x, next_point_velocity_y), rear_axle_acceleration_2d=StateVector2D(rear_axle_accel[0], rear_axle_accel[1]), tire_steering_angle=float(next_point_tire_steering_angle), time_point=propagating_state.time_point + sampling_time, vehicle_parameters=self._vehicle, is_in_auto_mode=True, angular_vel=next_point_angular_velocity, angular_accel=angular_accel, tire_steering_rate=state_dot.tire_steering_angle)

class TestKinematicMotionModel(unittest.TestCase):
    """
    Run tests for Kinematic Bicycle Model.
    """

    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.vehicle = get_pacifica_parameters()
        self.ego_state = get_sample_ego_state()
        self.sampling_time = TimePoint(1000000)
        self.motion_model = KinematicBicycleModel(self.vehicle)
        wheel_base = self.vehicle.wheel_base
        self.longitudinal_speed = self.ego_state.dynamic_car_state.rear_axle_velocity_2d.x
        self.x_dot = self.longitudinal_speed * np.cos(self.ego_state.rear_axle.heading)
        self.y_dot = self.longitudinal_speed * np.sin(self.ego_state.rear_axle.heading)
        self.yaw_dot = self.longitudinal_speed * np.tan(self.ego_state.tire_steering_angle) / wheel_base

    def test_get_state_dot(self) -> None:
        """
        Test get_state_dot for expected results
        """
        state_dot = self.motion_model.get_state_dot(self.ego_state)
        self.assertEqual(state_dot.rear_axle, StateSE2(self.x_dot, self.y_dot, self.yaw_dot))
        self.assertEqual(state_dot.dynamic_car_state.rear_axle_velocity_2d, self.ego_state.dynamic_car_state.rear_axle_acceleration_2d)
        self.assertEqual(state_dot.dynamic_car_state.rear_axle_acceleration_2d, StateVector2D(0, 0))
        self.assertEqual(state_dot.tire_steering_angle, self.ego_state.dynamic_car_state.tire_steering_rate)

    def test_propagate_state(self) -> None:
        """
        Test propagate_state
        """
        state = self.motion_model.propagate_state(self.ego_state, self.ego_state.dynamic_car_state, self.sampling_time)
        self.assertEqual(state.rear_axle, StateSE2(forward_integrate(self.ego_state.rear_axle.x, self.x_dot, self.sampling_time), forward_integrate(self.ego_state.rear_axle.y, self.y_dot, self.sampling_time), forward_integrate(self.ego_state.rear_axle.heading, self.yaw_dot, self.sampling_time)))
        self.assertEqual(state.dynamic_car_state.rear_axle_velocity_2d, StateVector2D(forward_integrate(self.ego_state.dynamic_car_state.rear_axle_velocity_2d.x, self.ego_state.dynamic_car_state.rear_axle_acceleration_2d.x, self.sampling_time), 0.0))
        self.assertEqual(state.dynamic_car_state.rear_axle_acceleration_2d, StateVector2D(0.1, 0.0))
        self.assertEqual(state.tire_steering_angle, forward_integrate(self.ego_state.tire_steering_angle, self.ego_state.dynamic_car_state.tire_steering_rate, self.sampling_time))
        self.assertEqual(state.dynamic_car_state.angular_velocity, state.dynamic_car_state.rear_axle_velocity_2d.x * np.tan(state.tire_steering_angle) / self.vehicle.wheel_base)

    def test_limit_steering_angle(self) -> None:
        """
        Test whether the KinematicBicycleModel correct enforces steering angle
        limits.
        """
        dynamic_car_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_rate=10.0)
        car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=StateSE2(x=0.0, y=0.0, heading=0.0), vehicle_parameters=self.vehicle)
        ego_state = EgoState(car_footprint, dynamic_car_state, tire_steering_angle=self.motion_model._max_steering_angle - 0.0001, is_in_auto_mode=True, time_point=TimePoint(0))
        propagated_state = self.motion_model.propagate_state(ego_state, dynamic_car_state, self.sampling_time)
        self.assertEqual(propagated_state.tire_steering_angle, self.motion_model._max_steering_angle)

    def test_update_command(self) -> None:
        """
        Test whether the update_command function performs as expected:
        1) returns same commands if time constants are set to zero (no delay)
        2) returns an smaller command (in the absolute sense) when filter is applied
        """
        dynamic_car_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_rate=0.0)
        car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=StateSE2(x=0.0, y=0.0, heading=0.0), vehicle_parameters=self.vehicle)
        state = EgoState(car_footprint, dynamic_car_state, tire_steering_angle=self.motion_model._max_steering_angle - 0.0001, is_in_auto_mode=True, time_point=TimePoint(0))
        ideal_dynamic_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(1.0, 0.0), tire_steering_rate=0.5)
        no_delay_motion_model = KinematicBicycleModel(self.vehicle, accel_time_constant=0, steering_angle_time_constant=0)
        no_delay_propagating_state = no_delay_motion_model._update_commands(state, ideal_dynamic_state, self.sampling_time)
        self.assertEqual(round(no_delay_propagating_state.dynamic_car_state.rear_axle_acceleration_2d.x, 10), ideal_dynamic_state.rear_axle_acceleration_2d.x)
        self.assertEqual(round(no_delay_propagating_state.dynamic_car_state.tire_steering_rate, 10), ideal_dynamic_state.tire_steering_rate)
        propagating_state = self.motion_model._update_commands(state, ideal_dynamic_state, self.sampling_time)
        self.assertTrue(propagating_state.dynamic_car_state.rear_axle_acceleration_2d.x < ideal_dynamic_state.rear_axle_acceleration_2d.x)
        self.assertLess(propagating_state.dynamic_car_state.tire_steering_rate, ideal_dynamic_state.tire_steering_rate)

def test_get_state_dot(self) -> None:
    """
        Test get_state_dot for expected results
        """
    state_dot = self.motion_model.get_state_dot(self.ego_state)
    self.assertEqual(state_dot.rear_axle, StateSE2(self.x_dot, self.y_dot, self.yaw_dot))
    self.assertEqual(state_dot.dynamic_car_state.rear_axle_velocity_2d, self.ego_state.dynamic_car_state.rear_axle_acceleration_2d)
    self.assertEqual(state_dot.dynamic_car_state.rear_axle_acceleration_2d, StateVector2D(0, 0))
    self.assertEqual(state_dot.tire_steering_angle, self.ego_state.dynamic_car_state.tire_steering_rate)

def test_propagate_state(self) -> None:
    """
        Test propagate_state
        """
    state = self.motion_model.propagate_state(self.ego_state, self.ego_state.dynamic_car_state, self.sampling_time)
    self.assertEqual(state.rear_axle, StateSE2(forward_integrate(self.ego_state.rear_axle.x, self.x_dot, self.sampling_time), forward_integrate(self.ego_state.rear_axle.y, self.y_dot, self.sampling_time), forward_integrate(self.ego_state.rear_axle.heading, self.yaw_dot, self.sampling_time)))
    self.assertEqual(state.dynamic_car_state.rear_axle_velocity_2d, StateVector2D(forward_integrate(self.ego_state.dynamic_car_state.rear_axle_velocity_2d.x, self.ego_state.dynamic_car_state.rear_axle_acceleration_2d.x, self.sampling_time), 0.0))
    self.assertEqual(state.dynamic_car_state.rear_axle_acceleration_2d, StateVector2D(0.1, 0.0))
    self.assertEqual(state.tire_steering_angle, forward_integrate(self.ego_state.tire_steering_angle, self.ego_state.dynamic_car_state.tire_steering_rate, self.sampling_time))
    self.assertEqual(state.dynamic_car_state.angular_velocity, state.dynamic_car_state.rear_axle_velocity_2d.x * np.tan(state.tire_steering_angle) / self.vehicle.wheel_base)

def test_limit_steering_angle(self) -> None:
    """
        Test whether the KinematicBicycleModel correct enforces steering angle
        limits.
        """
    dynamic_car_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_rate=10.0)
    car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=StateSE2(x=0.0, y=0.0, heading=0.0), vehicle_parameters=self.vehicle)
    ego_state = EgoState(car_footprint, dynamic_car_state, tire_steering_angle=self.motion_model._max_steering_angle - 0.0001, is_in_auto_mode=True, time_point=TimePoint(0))
    propagated_state = self.motion_model.propagate_state(ego_state, dynamic_car_state, self.sampling_time)
    self.assertEqual(propagated_state.tire_steering_angle, self.motion_model._max_steering_angle)

def test_update_command(self) -> None:
    """
        Test whether the update_command function performs as expected:
        1) returns same commands if time constants are set to zero (no delay)
        2) returns an smaller command (in the absolute sense) when filter is applied
        """
    dynamic_car_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_rate=0.0)
    car_footprint = CarFootprint.build_from_rear_axle(rear_axle_pose=StateSE2(x=0.0, y=0.0, heading=0.0), vehicle_parameters=self.vehicle)
    state = EgoState(car_footprint, dynamic_car_state, tire_steering_angle=self.motion_model._max_steering_angle - 0.0001, is_in_auto_mode=True, time_point=TimePoint(0))
    ideal_dynamic_state = DynamicCarState.build_from_rear_axle(self.vehicle.rear_axle_to_center, rear_axle_velocity_2d=StateVector2D(0.0, 0.0), rear_axle_acceleration_2d=StateVector2D(1.0, 0.0), tire_steering_rate=0.5)
    no_delay_motion_model = KinematicBicycleModel(self.vehicle, accel_time_constant=0, steering_angle_time_constant=0)
    no_delay_propagating_state = no_delay_motion_model._update_commands(state, ideal_dynamic_state, self.sampling_time)
    self.assertEqual(round(no_delay_propagating_state.dynamic_car_state.rear_axle_acceleration_2d.x, 10), ideal_dynamic_state.rear_axle_acceleration_2d.x)
    self.assertEqual(round(no_delay_propagating_state.dynamic_car_state.tire_steering_rate, 10), ideal_dynamic_state.tire_steering_rate)
    propagating_state = self.motion_model._update_commands(state, ideal_dynamic_state, self.sampling_time)
    self.assertTrue(propagating_state.dynamic_car_state.rear_axle_acceleration_2d.x < ideal_dynamic_state.rear_axle_acceleration_2d.x)
    self.assertLess(propagating_state.dynamic_car_state.tire_steering_rate, ideal_dynamic_state.tire_steering_rate)

class SimplePlanner(AbstractPlanner):
    """
    Planner going straight.
    """

    def __init__(self, horizon_seconds: float, sampling_time: float, acceleration: npt.NDArray[np.float32], max_velocity: float=5.0, steering_angle: float=0.0):
        """
        Constructor for SimplePlanner.
        :param horizon_seconds: [s] time horizon being run.
        :param sampling_time: [s] sampling timestep.
        :param acceleration: [m/s^2] constant ego acceleration, till limited by max_velocity.
        :param max_velocity: [m/s] ego max velocity.
        :param steering_angle: [rad] ego steering angle.
        """
        self.horizon_seconds = TimePoint(int(horizon_seconds * 1000000.0))
        self.sampling_time = TimePoint(int(sampling_time * 1000000.0))
        self.acceleration = StateVector2D(acceleration[0], acceleration[1])
        self.max_velocity = max_velocity
        self.steering_angle = steering_angle
        self.vehicle = get_pacifica_parameters()
        self.motion_model = KinematicBicycleModel(self.vehicle)

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
        """
        Implement a trajectory that goes straight.
        Inherited, see superclass.
        """
        history = current_input.history
        ego_state, _ = history.current_state
        state = EgoState(car_footprint=ego_state.car_footprint, dynamic_car_state=DynamicCarState.build_from_rear_axle(ego_state.car_footprint.rear_axle_to_center_dist, ego_state.dynamic_car_state.rear_axle_velocity_2d, self.acceleration), tire_steering_angle=self.steering_angle, is_in_auto_mode=True, time_point=ego_state.time_point)
        trajectory: List[EgoState] = [state]
        for _ in range(int(self.horizon_seconds.time_us / self.sampling_time.time_us)):
            if state.dynamic_car_state.speed > self.max_velocity:
                accel = self.max_velocity - state.dynamic_car_state.speed
                state = EgoState.build_from_rear_axle(rear_axle_pose=state.rear_axle, rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel, 0), tire_steering_angle=state.tire_steering_angle, time_point=state.time_point, vehicle_parameters=state.car_footprint.vehicle_parameters, is_in_auto_mode=True, angular_vel=state.dynamic_car_state.angular_velocity, angular_accel=state.dynamic_car_state.angular_acceleration)
            state = self.motion_model.propagate_state(state, state.dynamic_car_state, self.sampling_time)
            trajectory.append(state)
        return InterpolatedTrajectory(trajectory)

def __init__(self, horizon_seconds: float, sampling_time: float, acceleration: npt.NDArray[np.float32], max_velocity: float=5.0, steering_angle: float=0.0):
    """
        Constructor for SimplePlanner.
        :param horizon_seconds: [s] time horizon being run.
        :param sampling_time: [s] sampling timestep.
        :param acceleration: [m/s^2] constant ego acceleration, till limited by max_velocity.
        :param max_velocity: [m/s] ego max velocity.
        :param steering_angle: [rad] ego steering angle.
        """
    self.horizon_seconds = TimePoint(int(horizon_seconds * 1000000.0))
    self.sampling_time = TimePoint(int(sampling_time * 1000000.0))
    self.acceleration = StateVector2D(acceleration[0], acceleration[1])
    self.max_velocity = max_velocity
    self.steering_angle = steering_angle
    self.vehicle = get_pacifica_parameters()
    self.motion_model = KinematicBicycleModel(self.vehicle)

def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
    """
        Implement a trajectory that goes straight.
        Inherited, see superclass.
        """
    history = current_input.history
    ego_state, _ = history.current_state
    state = EgoState(car_footprint=ego_state.car_footprint, dynamic_car_state=DynamicCarState.build_from_rear_axle(ego_state.car_footprint.rear_axle_to_center_dist, ego_state.dynamic_car_state.rear_axle_velocity_2d, self.acceleration), tire_steering_angle=self.steering_angle, is_in_auto_mode=True, time_point=ego_state.time_point)
    trajectory: List[EgoState] = [state]
    for _ in range(int(self.horizon_seconds.time_us / self.sampling_time.time_us)):
        if state.dynamic_car_state.speed > self.max_velocity:
            accel = self.max_velocity - state.dynamic_car_state.speed
            state = EgoState.build_from_rear_axle(rear_axle_pose=state.rear_axle, rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_velocity_2d, rear_axle_acceleration_2d=StateVector2D(accel, 0), tire_steering_angle=state.tire_steering_angle, time_point=state.time_point, vehicle_parameters=state.car_footprint.vehicle_parameters, is_in_auto_mode=True, angular_vel=state.dynamic_car_state.angular_velocity, angular_accel=state.dynamic_car_state.angular_acceleration)
        state = self.motion_model.propagate_state(state, state.dynamic_car_state, self.sampling_time)
        trajectory.append(state)
    return InterpolatedTrajectory(trajectory)

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

def setUp(self) -> None:
    """Inherited, see superclass."""
    self.scenario = MockAbstractScenario(number_of_future_iterations=20)
    self.num_poses = 10
    self.future_time_horizon = 5
    self.planner = LogFuturePlanner(self.scenario, self.num_poses, self.future_time_horizon)

def _se2_vel_acc_to_ego_state(state: StateSE2, velocity: npt.NDArray[np.float32], acceleration: npt.NDArray[np.float32], timestamp: float, vehicle: VehicleParameters) -> EgoState:
    """
    Convert StateSE2, velocity and acceleration to EgoState given a timestamp.

    :param state: input SE2 state
    :param velocity: [m/s] longitudinal velocity, lateral velocity
    :param acceleration: [m/s^2] longitudinal acceleration, lateral acceleration
    :param timestamp: [s] timestamp of state
    :return: output agent state
    """
    return EgoState.build_from_rear_axle(rear_axle_pose=state, rear_axle_velocity_2d=StateVector2D(*velocity), rear_axle_acceleration_2d=StateVector2D(*acceleration), tire_steering_angle=0.0, time_point=TimePoint(int(timestamp * 1000000.0)), vehicle_parameters=vehicle, is_in_auto_mode=True)

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

def get_observation(self) -> DetectionsTracks:
    """Inherited, see superclass."""
    assert self._agents, 'ML agent observation has not been initialized!Please make sure initialize() is called before getting the observation.'
    return DetectionsTracks(TrackedObjects(list(self._agents.values())))

class IDMAgents(AbstractObservation):
    """
    Simulate agents based on IDM policy.
    """

    def __init__(self, target_velocity: float, min_gap_to_lead_agent: float, headway_time: float, accel_max: float, decel_max: float, open_loop_detections_types: List[str], scenario: AbstractScenario, minimum_path_length: float=20, planned_trajectory_samples: Optional[int]=None, planned_trajectory_sample_interval: Optional[float]=None, radius: float=100):
        """
        Constructor for IDMAgents

        :param target_velocity: [m/s] Desired velocity in free traffic
        :param min_gap_to_lead_agent: [m] Minimum relative distance to lead vehicle
        :param headway_time: [s] Desired time headway. The minimum possible time to the vehicle in front
        :param accel_max: [m/s^2] maximum acceleration
        :param decel_max: [m/s^2] maximum deceleration (positive value)
        :param scenario: scenario
        :param open_loop_detections_types: The open-loop detection types to include.
        :param minimum_path_length: [m] The minimum path length to maintain.
        :param planned_trajectory_samples: number of elements to sample for the planned trajectory.
        :param planned_trajectory_sample_interval: [s] time interval of sequence to sample from.
        :param radius: [m] Only agents within this radius around the ego will be simulated.
        """
        self.current_iteration = 0
        self._target_velocity = target_velocity
        self._min_gap_to_lead_agent = min_gap_to_lead_agent
        self._headway_time = headway_time
        self._accel_max = accel_max
        self._decel_max = decel_max
        self._scenario = scenario
        self._open_loop_detections_types: List[TrackedObjectType] = []
        self._minimum_path_length = minimum_path_length
        self._planned_trajectory_samples = planned_trajectory_samples
        self._planned_trajectory_sample_interval = planned_trajectory_sample_interval
        self._radius = radius
        self._idm_agent_manager: Optional[IDMAgentManager] = None
        self._initialize_open_loop_detection_types(open_loop_detections_types)

    def reset(self) -> None:
        """Inherited, see superclass."""
        self.current_iteration = 0
        self._idm_agent_manager = None

    def _initialize_open_loop_detection_types(self, open_loop_detections: List[str]) -> None:
        """
        Initializes open-loop detections with the enum types from TrackedObjectType
        :param open_loop_detections: A list of open-loop detections types as strings
        :return: A list of open-loop detections types as strings as the corresponding TrackedObjectType
        """
        for _type in open_loop_detections:
            try:
                self._open_loop_detections_types.append(TrackedObjectType[_type])
            except KeyError:
                raise ValueError(f'The given detection type {_type} does not exist or is not supported!')

    def _get_idm_agent_manager(self) -> IDMAgentManager:
        """
        Create idm agent manager in case it does not already exists
        :return: IDMAgentManager
        """
        if not self._idm_agent_manager:
            agents, agent_occupancy = build_idm_agents_on_map_rails(self._target_velocity, self._min_gap_to_lead_agent, self._headway_time, self._accel_max, self._decel_max, self._minimum_path_length, self._scenario, self._open_loop_detections_types)
            self._idm_agent_manager = IDMAgentManager(agents, agent_occupancy, self._scenario.map_api)
        return self._idm_agent_manager

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def initialize(self) -> None:
        """Inherited, see superclass."""
        pass

    def get_observation(self) -> DetectionsTracks:
        """Inherited, see superclass."""
        detections = self._get_idm_agent_manager().get_active_agents(self.current_iteration, self._planned_trajectory_samples, self._planned_trajectory_sample_interval)
        if self._open_loop_detections_types:
            open_loop_detections = self._get_open_loop_track_objects(self.current_iteration)
            detections.tracked_objects.tracked_objects.extend(open_loop_detections)
        return detections

    def update_observation(self, iteration: SimulationIteration, next_iteration: SimulationIteration, history: SimulationHistoryBuffer) -> None:
        """Inherited, see superclass."""
        self.current_iteration = next_iteration.index
        tspan = next_iteration.time_s - iteration.time_s
        traffic_light_data = self._scenario.get_traffic_light_status_at_iteration(self.current_iteration)
        traffic_light_status: Dict[TrafficLightStatusType, List[str]] = defaultdict(list)
        for data in traffic_light_data:
            traffic_light_status[data.status].append(str(data.lane_connector_id))
        ego_state, _ = history.current_state
        self._get_idm_agent_manager().propagate_agents(ego_state, tspan, self.current_iteration, traffic_light_status, self._get_open_loop_track_objects(self.current_iteration), self._radius)

    def _get_open_loop_track_objects(self, iteration: int) -> List[TrackedObject]:
        """
        Get open-loop tracked objects from scenario.
        :param iteration: The simulation iteration.
        :return: A list of TrackedObjects.
        """
        detections = self._scenario.get_tracked_objects_at_iteration(iteration)
        return detections.tracked_objects.get_tracked_objects_of_types(self._open_loop_detections_types)

def _get_idm_agent_manager(self) -> IDMAgentManager:
    """
        Create idm agent manager in case it does not already exists
        :return: IDMAgentManager
        """
    if not self._idm_agent_manager:
        agents, agent_occupancy = build_idm_agents_on_map_rails(self._target_velocity, self._min_gap_to_lead_agent, self._headway_time, self._accel_max, self._decel_max, self._minimum_path_length, self._scenario, self._open_loop_detections_types)
        self._idm_agent_manager = IDMAgentManager(agents, agent_occupancy, self._scenario.map_api)
    return self._idm_agent_manager

def _get_open_loop_track_objects(self, iteration: int) -> List[TrackedObject]:
    """
        Get open-loop tracked objects from scenario.
        :param iteration: The simulation iteration.
        :return: A list of TrackedObjects.
        """
    detections = self._scenario.get_tracked_objects_at_iteration(iteration)
    return detections.tracked_objects.get_tracked_objects_of_types(self._open_loop_detections_types)

def _convert_prediction_to_predicted_trajectory(agent: TrackedObject, poses: List[StateSE2], xy_velocities: List[StateVector2D], step_interval_us: float) -> PredictedTrajectory:
    """
    Convert each agent predictions into a PredictedTrajectory.
    :param agent: The agent the predictions are for.
    :param poses: A list of poses that makes up the predictions
    :param xy_velocities: A list of velocities in world frame corresponding to each pose.
    :return: The predictions parsed into PredictedTrajectory.
    """
    waypoints = [Waypoint(TimePoint(0), agent.box, agent.velocity)]
    waypoints += [Waypoint(TimePoint(int((step + 1) * step_interval_us)), OrientedBox.from_new_pose(agent.box, pose), velocity) for step, (pose, velocity) in enumerate(zip(poses, xy_velocities))]
    return PredictedTrajectory(1.0, waypoints)

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

@property
def _ego_velocity_anchor_state(self) -> StateSE2:
    """
        Returns the ego's velocity state vector as an anchor state for transformation.
        :return: A StateSE2 representing ego's velocity state as an anchor state
        """
    ego_velocity = self._ego_anchor_state.dynamic_car_state.rear_axle_velocity_2d
    return StateSE2(ego_velocity.x, ego_velocity.y, self._ego_anchor_state.rear_axle.heading)

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

def create_path_from_ego_state(states: List[EgoState]) -> InterpolatedPath:
    """
    Constructs an InterpolatedPath from a list of EgoState.
    :param states: waypoints to construct an InterpolatedPath.
    :return InterpolatedPath.
    """
    return create_path_from_se2(ego_path_to_se2(states))

def ego_path_to_linestring(path: List[EgoState]) -> LineString:
    """
    Converts a List of EgoState into a LineString
    :param path: path to be converted
    :return: LineString.
    """
    return path_to_linestring(ego_path_to_se2(path))

class IDMAgentManager:
    """IDM smart-agents manager."""

    def __init__(self, agents: UniqueIDMAgents, agent_occupancy: OccupancyMap, map_api: AbstractMap):
        """
        Constructor for IDMAgentManager.
        :param agents: A dictionary pairing the agent's token to it's IDM representation.
        :param agent_occupancy: An occupancy map describing the spatial relationship between agents.
        :param map_api: AbstractMap API
        """
        self.agents: UniqueIDMAgents = agents
        self.agent_occupancy = agent_occupancy
        self._map_api = map_api

    def propagate_agents(self, ego_state: EgoState, tspan: float, iteration: int, traffic_light_status: Dict[TrafficLightStatusType, List[str]], open_loop_detections: List[TrackedObject], radius: float) -> None:
        """
        Propagate each active agent forward in time.

        :param ego_state: the ego's current state in the simulation.
        :param tspan: the interval of time to simulate.
        :param iteration: the simulation iteration.
        :param traffic_light_status: {traffic_light_status: lane_connector_ids} A dictionary containing traffic light information.
        :param open_loop_detections: A list of open loop detections the IDM agents should be responsive to.
        :param radius: [m] The radius around the ego state
        """
        self.agent_occupancy.set('ego', ego_state.car_footprint.geometry)
        track_ids = []
        for track in open_loop_detections:
            track_ids.append(track.track_token)
            self.agent_occupancy.insert(track.track_token, track.box.geometry)
        self._filter_agents_out_of_range(ego_state, radius)
        for agent_token, agent in self.agents.items():
            if agent.is_active(iteration) and agent.has_valid_path():
                agent.plan_route(traffic_light_status)
                stop_lines = self._get_relevant_stop_lines(agent, traffic_light_status)
                inactive_stop_line_tokens = self._insert_stop_lines_into_occupancy_map(stop_lines)
                agent_path = path_to_linestring(agent.get_path_to_go())
                intersecting_agents = self.agent_occupancy.intersects(agent_path.buffer(agent.width / 2, cap_style=CAP_STYLE.flat))
                assert intersecting_agents.contains(agent_token), "Agent's baseline does not intersect the agent itself"
                if intersecting_agents.size > 1:
                    nearest_id, nearest_agent_polygon, relative_distance = intersecting_agents.get_nearest_entry_to(agent_token)
                    agent_heading = agent.to_se2().heading
                    if 'ego' in nearest_id:
                        ego_velocity = ego_state.dynamic_car_state.rear_axle_velocity_2d
                        longitudinal_velocity = np.hypot(ego_velocity.x, ego_velocity.y)
                        relative_heading = ego_state.rear_axle.heading - agent_heading
                    elif 'stop_line' in nearest_id:
                        longitudinal_velocity = 0.0
                        relative_heading = 0.0
                    elif nearest_id in self.agents:
                        nearest_agent = self.agents[nearest_id]
                        longitudinal_velocity = nearest_agent.velocity
                        relative_heading = nearest_agent.to_se2().heading - agent_heading
                    else:
                        longitudinal_velocity = 0.0
                        relative_heading = 0.0
                    relative_heading = principal_value(relative_heading)
                    projected_velocity = rotate_angle(StateSE2(longitudinal_velocity, 0, 0), relative_heading).x
                    length_rear = 0
                else:
                    projected_velocity = 0.0
                    relative_distance = agent.get_progress_to_go()
                    length_rear = agent.length / 2
                agent.propagate(IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=length_rear), tspan)
                self.agent_occupancy.set(agent_token, agent.projected_footprint)
                self.agent_occupancy.remove(inactive_stop_line_tokens)
        self.agent_occupancy.remove(track_ids)

    def get_active_agents(self, iteration: int, num_samples: int, sampling_time: float) -> DetectionsTracks:
        """
        Returns all agents as DetectionsTracks.
        :param iteration: the current simulation iteration.
        :param num_samples: number of elements to sample.
        :param sampling_time: [s] time interval of sequence to sample from.
        :return: agents as DetectionsTracks.
        """
        return DetectionsTracks(TrackedObjects([agent.get_agent_with_planned_trajectory(num_samples, sampling_time) for agent in self.agents.values() if agent.is_active(iteration)]))

    def _filter_agents_out_of_range(self, ego_state: EgoState, radius: float=100) -> None:
        """
        Filter out agents that are out of range.
        :param ego_state: The ego state used as the center of the given radius
        :param radius: [m] The radius around the ego state
        """
        if len(self.agents) == 0:
            return
        agents: npt.NDArray[np.int32] = np.array([agent.to_se2().point.array for agent in self.agents.values()])
        distances = cdist(np.expand_dims(ego_state.center.point.array, axis=0), agents)
        remove_indices = np.argwhere(distances.flatten() > radius)
        remove_tokens = np.array(list(self.agents.keys()))[remove_indices.flatten()]
        self.agent_occupancy.remove(remove_tokens)
        for token in remove_tokens:
            self.agents.pop(token)

    def _get_relevant_stop_lines(self, agent: IDMAgent, traffic_light_status: Dict[TrafficLightStatusType, List[str]]) -> List[StopLine]:
        """
        Retrieve the stop lines that are affecting the given agent.
        :param agent: The IDM agent of interest.
        :param traffic_light_status: {traffic_light_status: lane_connector_ids} A dictionary containing traffic light information.
        :return: A list of stop lines associated with the given traffic light status.
        """
        relevant_lane_connectors = list({segment.id for segment in agent.get_route()} & set(traffic_light_status[TrafficLightStatusType.RED]))
        lane_connectors = [self._map_api.get_map_object(lc_id, SemanticMapLayer.LANE_CONNECTOR) for lc_id in relevant_lane_connectors]
        return [stop_line for lc in lane_connectors if lc for stop_line in lc.stop_lines]

    def _insert_stop_lines_into_occupancy_map(self, stop_lines: List[StopLine]) -> List[str]:
        """
        Insert stop lines into the occupancy map.
        :param stop_lines: A list of stop lines to be inserted.
        :return: A list of token corresponding to the inserted stop lines.
        """
        stop_line_tokens: List[str] = []
        for stop_line in stop_lines:
            stop_line_token = f'stop_line_{stop_line.id}'
            if not self.agent_occupancy.contains(stop_line_token):
                self.agent_occupancy.set(stop_line_token, stop_line.polygon)
                stop_line_tokens.append(stop_line_token)
        return stop_line_tokens

def propagate_agents(self, ego_state: EgoState, tspan: float, iteration: int, traffic_light_status: Dict[TrafficLightStatusType, List[str]], open_loop_detections: List[TrackedObject], radius: float) -> None:
    """
        Propagate each active agent forward in time.

        :param ego_state: the ego's current state in the simulation.
        :param tspan: the interval of time to simulate.
        :param iteration: the simulation iteration.
        :param traffic_light_status: {traffic_light_status: lane_connector_ids} A dictionary containing traffic light information.
        :param open_loop_detections: A list of open loop detections the IDM agents should be responsive to.
        :param radius: [m] The radius around the ego state
        """
    self.agent_occupancy.set('ego', ego_state.car_footprint.geometry)
    track_ids = []
    for track in open_loop_detections:
        track_ids.append(track.track_token)
        self.agent_occupancy.insert(track.track_token, track.box.geometry)
    self._filter_agents_out_of_range(ego_state, radius)
    for agent_token, agent in self.agents.items():
        if agent.is_active(iteration) and agent.has_valid_path():
            agent.plan_route(traffic_light_status)
            stop_lines = self._get_relevant_stop_lines(agent, traffic_light_status)
            inactive_stop_line_tokens = self._insert_stop_lines_into_occupancy_map(stop_lines)
            agent_path = path_to_linestring(agent.get_path_to_go())
            intersecting_agents = self.agent_occupancy.intersects(agent_path.buffer(agent.width / 2, cap_style=CAP_STYLE.flat))
            assert intersecting_agents.contains(agent_token), "Agent's baseline does not intersect the agent itself"
            if intersecting_agents.size > 1:
                nearest_id, nearest_agent_polygon, relative_distance = intersecting_agents.get_nearest_entry_to(agent_token)
                agent_heading = agent.to_se2().heading
                if 'ego' in nearest_id:
                    ego_velocity = ego_state.dynamic_car_state.rear_axle_velocity_2d
                    longitudinal_velocity = np.hypot(ego_velocity.x, ego_velocity.y)
                    relative_heading = ego_state.rear_axle.heading - agent_heading
                elif 'stop_line' in nearest_id:
                    longitudinal_velocity = 0.0
                    relative_heading = 0.0
                elif nearest_id in self.agents:
                    nearest_agent = self.agents[nearest_id]
                    longitudinal_velocity = nearest_agent.velocity
                    relative_heading = nearest_agent.to_se2().heading - agent_heading
                else:
                    longitudinal_velocity = 0.0
                    relative_heading = 0.0
                relative_heading = principal_value(relative_heading)
                projected_velocity = rotate_angle(StateSE2(longitudinal_velocity, 0, 0), relative_heading).x
                length_rear = 0
            else:
                projected_velocity = 0.0
                relative_distance = agent.get_progress_to_go()
                length_rear = agent.length / 2
            agent.propagate(IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=length_rear), tspan)
            self.agent_occupancy.set(agent_token, agent.projected_footprint)
            self.agent_occupancy.remove(inactive_stop_line_tokens)
    self.agent_occupancy.remove(track_ids)

def get_active_agents(self, iteration: int, num_samples: int, sampling_time: float) -> DetectionsTracks:
    """
        Returns all agents as DetectionsTracks.
        :param iteration: the current simulation iteration.
        :param num_samples: number of elements to sample.
        :param sampling_time: [s] time interval of sequence to sample from.
        :return: agents as DetectionsTracks.
        """
    return DetectionsTracks(TrackedObjects([agent.get_agent_with_planned_trajectory(num_samples, sampling_time) for agent in self.agents.values() if agent.is_active(iteration)]))

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

@property
def agent(self) -> Agent:
    """:return: the agent as a Agent object"""
    return self._get_agent_at_progress(self._get_bounded_progress())

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

def to_se2(self) -> StateSE2:
    """
        :return: the agent as a StateSE2 object
        """
    return self._get_agent_at_progress(self._get_bounded_progress()).box.center

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

def _convert_route_to_path(self) -> InterpolatedPath:
    """
        Converts the route into an InterpolatedPath
        :return: InterpolatedPath from the agent's route
        """
    blp: List[StateSE2] = []
    for segment in self._route:
        blp.extend(segment.baseline_path.discrete_path)
    return create_path_from_se2(blp)

def build_idm_agents_on_map_rails(target_velocity: float, min_gap_to_lead_agent: float, headway_time: float, accel_max: float, decel_max: float, minimum_path_length: float, scenario: AbstractScenario, open_loop_detections_types: List[TrackedObjectType]) -> Tuple[UniqueIDMAgents, OccupancyMap]:
    """
    Build unique agents from a scenario. InterpolatedPaths are created for each agent according to their driven path

    :param target_velocity: Desired velocity in free traffic [m/s]
    :param min_gap_to_lead_agent: Minimum relative distance to lead vehicle [m]
    :param headway_time: Desired time headway. The minimum possible time to the vehicle in front [s]
    :param accel_max: maximum acceleration [m/s^2]
    :param decel_max: maximum deceleration (positive value) [m/s^2]
    :param minimum_path_length: [m] The minimum path length
    :param scenario: scenario
    :param open_loop_detections_types: The open-loop detection types to include.
    :return: a dictionary of IDM agent uniquely identified by a track_token
    """
    unique_agents: UniqueIDMAgents = {}
    detections = scenario.initial_tracked_objects
    map_api = scenario.map_api
    ego_agent = scenario.get_ego_state_at_iteration(0).agent
    open_loop_detections = detections.tracked_objects.get_tracked_objects_of_types(open_loop_detections_types)
    init_agent_occupancy = STRTreeOccupancyMapFactory.get_from_boxes(open_loop_detections)
    init_agent_occupancy.insert(ego_agent.token, ego_agent.box.geometry)
    occupancy_map = STRTreeOccupancyMap({})
    desc = 'Converting detections to smart agents'
    agent: Agent
    for agent in tqdm(detections.tracked_objects.get_tracked_objects_of_type(TrackedObjectType.VEHICLE), desc=desc, leave=False):
        if agent.track_token not in unique_agents:
            route, progress = get_starting_segment(agent, map_api)
            if route is None:
                continue
            state_on_path = route.baseline_path.get_nearest_pose_from_position(agent.center.point)
            box_on_baseline = OrientedBox.from_new_pose(agent.box, StateSE2(state_on_path.x, state_on_path.y, state_on_path.heading))
            if not init_agent_occupancy.intersects(box_on_baseline.geometry).is_empty():
                continue
            init_agent_occupancy.insert(agent.track_token, box_on_baseline.geometry)
            occupancy_map.insert(agent.track_token, box_on_baseline.geometry)
            if np.isnan(agent.velocity.array).any():
                ego_state = scenario.get_ego_state_at_iteration(0)
                logger.debug(f"Agents has nan velocity. Setting velocity to ego's velocity of {ego_state.dynamic_car_state.speed}")
                velocity = StateVector2D(ego_state.dynamic_car_state.speed, 0.0)
            else:
                velocity = StateVector2D(np.hypot(agent.velocity.x, agent.velocity.y), 0)
            initial_state = IDMInitialState(metadata=agent.metadata, tracked_object_type=agent.tracked_object_type, box=box_on_baseline, velocity=velocity, path_progress=progress, predictions=agent.predictions)
            target_velocity = route.speed_limit_mps or target_velocity
            unique_agents[agent.track_token] = IDMAgent(start_iteration=0, initial_state=initial_state, route=[route], policy=IDMPolicy(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max), minimum_path_length=minimum_path_length)
    return (unique_agents, occupancy_map)

def agent_baselines_to_scene(scene: Dict[str, Any], agents: UniqueIDMAgents) -> None:
    """
    Renders all agents' reference baseline paths as series of poses
    :param scene: scene dictionary
    :param agents: all agents for which the baseline path should be rendered for
    """
    for agent in agents.values():
        baseline_path_to_scene(scene, agent.get_path_to_go())

def agents_pose_to_scene(scene: Dict[str, Any], agents: UniqueIDMAgents) -> None:
    """
    Renders all agents' pose as markers
    :param scene: scene dictionary
    :param agents: all agents for which the pose should be rendered for
    """
    for agent_id, agent in agents.items():
        marker_to_scene(scene, agent_id, agent.to_se2())

def agents_box_to_scene(scene: Dict[str, Any], agents: UniqueIDMAgents) -> None:
    """
    Renders all agents' box in scene
    :param scene: scene dictionary
    :param agents: all agents to be rendered
    """
    for vehicle in scene['world']['vehicles']:
        agent_id = str(vehicle['id'])
        if agent_id in agents:
            vehicle['box']['pose'] = agents[agent_id].to_se2().serialize()
            vehicle['speed'] = agents[agent_id].velocity

def _build_idm_agents(agents: List[Agent], map_api: AbstractMap, policy: IDMPolicy) -> UniqueIDMAgents:
    """
    Builds idm agents.
    :param agents: list of agents represented by Agent
    :param map_api: AbstractMap
    :param policy: IDM policy
    :return: A dictionary of unique agents
    """
    unique_agents: UniqueIDMAgents = {}
    for agent in agents:
        route, progress = get_starting_segment(agent, map_api)
        initial_state = IDMInitialState(metadata=agent.metadata, tracked_object_type=agent.tracked_object_type, box=agent.box, velocity=agent.velocity, path_progress=progress, predictions=None)
        unique_agents[str(agent.token)] = IDMAgent(start_iteration=0, initial_state=initial_state, route=[route], policy=policy, minimum_path_length=10)
    return unique_agents

def build_idm_manager(scene: Dict[str, Any], map_factory: AbstractMapFactory, policy: IDMPolicy) -> IDMAgentManager:
    """
    Builds IDMAgentManager from scene
    :param scene: scene dictionary
    :param map_factory: AbstractMapFactory
    :param policy: IDM policy
    :return: IDMAgentManager object
    """
    map_name = scene['map']['area']
    map_maps_db = map_factory.build_map_from_name(map_name)
    agents = from_scene_to_tracked_objects(scene['world']).get_tracked_objects_of_type(TrackedObjectType.VEHICLE)
    unique_agents = _build_idm_agents(agents, map_maps_db, policy)
    occupancy_map = STRTreeOccupancyMapFactory().get_from_boxes(agents)
    idm_manager = IDMAgentManager(unique_agents, occupancy_map, map_maps_db)
    return idm_manager

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

def setUp(self):
    """Test setup"""
    self.idm = IDMPolicy(target_velocity=30, min_gap_to_lead_agent=2, headway_time=1.5, accel_max=0.73, decel_max=1.67)
    self.sampling_time = 0.5
    self.agent = IDMAgentState(5, 3)
    self.lead_agent = IDMLeadAgentState(15, 2, 5)

class AbstractTrajectory(metaclass=ABCMeta):
    """
    Generic agent or ego trajectory interface.
    """

    @property
    @abstractmethod
    def start_time(self) -> TimePoint:
        """
        Get the trajectory start time.
        :return: Start time.
        """
        pass

    @property
    @abstractmethod
    def end_time(self) -> TimePoint:
        """
        Get the trajectory end time.
        :return: End time.
        """
        pass

    @property
    def duration(self) -> float:
        """
        :return: the time duration of the trajectory
        """
        return self.end_time.time_s - self.start_time.time_s

    @property
    def duration_us(self) -> int:
        """
        :return: the time duration of the trajectory in micro seconds
        """
        return int(self.end_time.time_us - self.start_time.time_us)

    @abstractmethod
    def get_state_at_time(self, time_point: TimePoint) -> Any:
        """
        Get the state of the actor at the specified time point.
        :param time_point: Time for which are want to query a state.
        :return: State at the specified time.

        :raises AssertionError: Throws an exception in case a time_point is beyond range of a trajectory.
        """
        pass

    @abstractmethod
    def get_state_at_times(self, time_points: List[TimePoint]) -> List[Any]:
        """
        Get the state of the actor at the specified time points.
        :param time_points: List of time points for which are want to query a state.
        :return: States at the specified time.

        :raises AssertionError: Throws an exception in case a time_point is beyond range of a trajectory.
        """
        pass

    @abstractmethod
    def get_sampled_trajectory(self) -> List[Any]:
        """
        Get the sampled states along the trajectory.
        :return: Discrete trajectory consisting of states.
        """
        pass

    def is_in_range(self, time_point: Union[TimePoint, int]) -> bool:
        """
        Check whether a time point is in range of trajectory.
        :return: True if it is, False otherwise.
        """
        if isinstance(time_point, int):
            time_point = TimePoint(time_point)
        return bool(self.start_time <= time_point <= self.end_time)

@property
def duration_us(self) -> int:
    """
        :return: the time duration of the trajectory in micro seconds
        """
    return int(self.end_time.time_us - self.start_time.time_us)

@dataclass
class PredictedTrajectory:
    """Stores a predicted trajectory, along with its probability."""
    probability: float
    waypoints: List[Optional[WaypointTypes]]

    @property
    def valid_waypoints(self) -> List[WaypointTypes]:
        """
        Interface to get only valid waypoints
        :return: waypoints which are not None
        """
        return [w for w in self.waypoints if w]

    @cached_property
    def trajectory(self) -> AbstractTrajectory:
        """
        Interface to compute trajectory from waypoints
        :return: trajectory from waypoints
        """
        return InterpolatedTrajectory(self.valid_waypoints)

    def __len__(self) -> int:
        """
        :return: number of waypoints in trajectory
        """
        return len(self.waypoints)

@cached_property
def trajectory(self) -> AbstractTrajectory:
    """
        Interface to compute trajectory from waypoints
        :return: trajectory from waypoints
        """
    return InterpolatedTrajectory(self.valid_waypoints)

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

def setUp(self) -> None:
    """
        Setup mocks for the tests
        """
    self.map = MagicMock(spec=AbstractMap)
    self.se2 = MagicMock(spec=StateSE2)
    self.sample = MagicMock(spec=SimulationHistorySample)
    self.sh = SimulationHistory(self.map, self.se2)

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

def setUp(self) -> None:
    """
        Initializes DB
        """
    self.scenario = MockAbstractScenario(number_of_past_iterations=20)
    self.buffer_size = 10

class TestPathUtils(unittest.TestCase):
    """Tests path util functions."""

    def setUp(self) -> None:
        """Test setup."""
        self.path = [StateSE2(0, 0, 0), StateSE2(3, 4, 1), StateSE2(7, 7, 2), StateSE2(10, 10, 3)]

    def test_calculate_progress(self) -> None:
        """Tests if progress is calculated correctly"""
        progress = calculate_progress(self.path)
        self.assertEqual([0.0, 5.0, 10.0, 14.242640687119284], progress)

    def test_convert_se2_path_to_progress_path(self) -> None:
        """Tests if conversion to List[ProgressStateSE2] is calculated correctly"""
        progress_path = convert_se2_path_to_progress_path(self.path)
        self.assertEqual([0.0, 5.0, 10.0, 14.242640687119284], [point.progress for point in progress_path])
        self.assertEqual(self.path, [StateSE2(x=point.x, y=point.y, heading=point.heading) for point in progress_path])

def setUp(self) -> None:
    """Test setup."""
    self.path = [StateSE2(0, 0, 0), StateSE2(3, 4, 1), StateSE2(7, 7, 2), StateSE2(10, 10, 3)]

def test_convert_se2_path_to_progress_path(self) -> None:
    """Tests if conversion to List[ProgressStateSE2] is calculated correctly"""
    progress_path = convert_se2_path_to_progress_path(self.path)
    self.assertEqual([0.0, 5.0, 10.0, 14.242640687119284], [point.progress for point in progress_path])
    self.assertEqual(self.path, [StateSE2(x=point.x, y=point.y, heading=point.heading) for point in progress_path])

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

def setUp(self) -> None:
    """Test setup."""
    self.path = [StateSE2(0, 0, 0), StateSE2(3, 4, 1), StateSE2(7, 7, 2), StateSE2(10, 10, 3)]
    self.interpolated_path = InterpolatedPath(convert_se2_path_to_progress_path(self.path))

def test_get_state_at_progress(self) -> None:
    """Check if the interpolated states are calculated correctly progress"""
    state = self.interpolated_path.get_state_at_progress(5)
    self.assertEqual(5, state.progress)
    self.assertEqual(3, state.x)
    self.assertEqual(4, state.y)
    self.assertEqual(1, state.heading)

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

class TestMetricRunner(unittest.TestCase):
    """Tests MetricRunner class which is computing metric."""

    def setUp(self) -> None:
        """Setup Mock classes."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.scenario = MockAbstractScenario(number_of_past_iterations=10)
        self.history = SimulationHistory(self.scenario.map_api, self.scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
        self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
        save_path = Path(self.tmp_dir.name)
        planner = SimplePlanner(2, 0.5, [0, 0])
        self.simulation_log = SimulationLog(file_path=save_path / 'simulation_logs', simulation_history=self.history, scenario=self.scenario, planner=planner)
        self.metric_engine = MetricsEngine(metrics=[], main_save_path=save_path / 'metrics')
        self.metric_callback = MetricCallback(metric_engine=self.metric_engine)
        self.metric_runner = MetricRunner(simulation_log=self.simulation_log, metric_callback=self.metric_callback)

    def tearDown(self) -> None:
        """Clean up folders."""
        self.tmp_dir.cleanup()

    def test_run_metric_runner(self) -> None:
        """Test to run metric_runner."""
        self.metric_runner.run()

def setUp(self) -> None:
    """Setup Mock classes."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.scenario = MockAbstractScenario(number_of_past_iterations=10)
    self.history = SimulationHistory(self.scenario.map_api, self.scenario.get_mission_goal())
    state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
    state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
    self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
    self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
    save_path = Path(self.tmp_dir.name)
    planner = SimplePlanner(2, 0.5, [0, 0])
    self.simulation_log = SimulationLog(file_path=save_path / 'simulation_logs', simulation_history=self.history, scenario=self.scenario, planner=planner)
    self.metric_engine = MetricsEngine(metrics=[], main_save_path=save_path / 'metrics')
    self.metric_callback = MetricCallback(metric_engine=self.metric_engine)
    self.metric_runner = MetricRunner(simulation_log=self.simulation_log, metric_callback=self.metric_callback)

@dataclass
class SimulationIteration:
    """
    Simulation step time and index.
    """
    time_point: TimePoint
    index: int

    def __post_init__(self) -> None:
        """Post-init index sanity check."""
        assert self.index >= 0, f'Iteration must be >= 0, but it is {self.index}!'

    @property
    def time_us(self) -> int:
        """
        :return: time in micro seconds.
        """
        return int(self.time_point.time_us)

    @property
    def time_s(self) -> float:
        """
        :return: Time in seconds.
        """
        return float(self.time_point.time_s)

@property
def time_us(self) -> int:
    """
        :return: time in micro seconds.
        """
    return int(self.time_point.time_us)

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

def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
    """Inherited, see superclass."""
    for callback in self._callbacks:
        callback.on_initialization_start(setup, planner)

def convert_sample_to_scene(map_name: str, database_interval: float, traffic_light_status: Generator[TrafficLightStatusData, None, None], mission_goal: Optional[StateSE2], expert_trajectory: List[EgoState], data: SimulationHistorySample, colors: TrajectoryColors=TrajectoryColors()) -> Dict[str, Any]:
    """
    Serialize history and scenario.
    :param map_name: name of the map used for this scenario.
    :param database_interval: Database interval (fps).
    :param traffic_light_status: Traffic light status.
    :param mission_goal: if mission goal is present, this is goal of this mission.
    :param expert_trajectory: trajectory of an expert driver.
    :param data: single sample from history.
    :param colors: colors for trajectories.
    :return: serialized dictionary.
    """
    scene: Dict[str, Any] = {'timestamp_us': data.ego_state.time_us}
    trajectories: Dict[str, Dict[str, Any]] = {}
    if mission_goal is not None:
        scene['goal'] = dict(to_scene_goal_from_state(mission_goal))
    else:
        scene['goal'] = None
    scene['ego'] = dict(to_scene_ego_from_car_footprint(CarFootprint.build_from_center(data.ego_state.center, get_pacifica_parameters())))
    scene['ego']['timestamp_us'] = data.ego_state.time_us
    map_name_without_suffix = str(pathlib.Path(map_name).with_suffix(''))
    scene['map'] = {'area': map_name_without_suffix}
    scene['map_name'] = map_name
    if isinstance(data.observation, DetectionsTracks):
        scene['world'] = to_scene_boxes(data.observation.tracked_objects)
        scene['prediction'] = to_scene_agent_prediction_from_boxes(data.observation.tracked_objects, colors.agents_predicted_trajectory)
    trajectories['ego_predicted_trajectory'] = dict(to_scene_trajectory_from_list_ego_state(data.trajectory.get_sampled_trajectory(), colors.ego_predicted_trajectory))
    trajectories['ego_expert_trajectory'] = dict(to_scene_trajectory_from_list_ego_state(expert_trajectory, colors.ego_expert_trajectory))
    scene['trajectories'] = trajectories
    scene['traffic_light_status'] = [traffic_light.serialize() for traffic_light in traffic_light_status]
    scene['database_interval'] = database_interval
    return scene

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

def test_metric_callback_init(self) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    mc = MetricCallback(self.mock_metric_engine)
    self.assertEqual(mc._metric_engine, self.mock_metric_engine)

class TestSimulationLogCallback(unittest.TestCase):
    """Tests simulation_log_callback."""

    def setUp(self) -> None:
        """Setup Mocked classes."""
        self.output_folder = tempfile.TemporaryDirectory()
        self.callback = SimulationLogCallback(output_directory=self.output_folder.name, simulation_log_dir='simulation_log', serialization_type='msgpack')
        self.sim_manager = Mock(spec=AbstractSimulationTimeController)
        self.observation = Mock(spec=AbstractObservation)
        self.controller = Mock(spec=AbstractEgoController)

    def tearDown(self) -> None:
        """Clean up folder."""
        self.output_folder.cleanup()

    def test_callback(self) -> None:
        """
        Tests whether a scene can be dumped into a simulation log, checks that the keys are correct,
        and checks that the log contains the expected data after being re-loaded from disk.
        """
        scenario = MockAbstractScenario()
        self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
        planner = SimplePlanner(2, 0.5, [0, 0])
        directory = self.callback._get_scenario_folder(planner.name(), scenario)
        self.assertEqual(str(directory), self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
        self.callback.on_initialization_start(self.setup, planner)
        history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
        for data in history.data:
            self.callback.on_step_end(self.setup, planner, data)
        self.callback.on_simulation_end(self.setup, planner, history)
        path = pathlib.Path(self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name/mock_scenario_name.msgpack.xz')
        self.assertTrue(path.exists())
        simulation_log = SimulationLog.load_data(file_path=path)
        self.assertEqual(simulation_log.file_path, path)
        self.assertTrue(objects_are_equal(simulation_log.simulation_history, history))

def test_callback(self) -> None:
    """
        Tests whether a scene can be dumped into a simulation log, checks that the keys are correct,
        and checks that the log contains the expected data after being re-loaded from disk.
        """
    scenario = MockAbstractScenario()
    self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
    planner = SimplePlanner(2, 0.5, [0, 0])
    directory = self.callback._get_scenario_folder(planner.name(), scenario)
    self.assertEqual(str(directory), self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
    self.callback.on_initialization_start(self.setup, planner)
    history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
    state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
    state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
    for data in history.data:
        self.callback.on_step_end(self.setup, planner, data)
    self.callback.on_simulation_end(self.setup, planner, history)
    path = pathlib.Path(self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name/mock_scenario_name.msgpack.xz')
    self.assertTrue(path.exists())
    simulation_log = SimulationLog.load_data(file_path=path)
    self.assertEqual(simulation_log.file_path, path)
    self.assertTrue(objects_are_equal(simulation_log.simulation_history, history))

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

def _find_free_port(self) -> int:
    """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        address, port = s.getsockname()
        return int(port)

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

def _find_free_port(self) -> int:
    """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        address, port = s.getsockname()
        return int(port)

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

def _find_free_port(self) -> int:
    """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        address, port = s.getsockname()
        return int(port)

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

def _find_free_port(self) -> int:
    """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        address, port = s.getsockname()
        return int(port)

def extract_and_pad_agent_poses(agent_trajectories: List[TrackedObjects], reverse: bool=False) -> Tuple[List[List[StateSE2]], List[List[bool]]]:
    """
    Extract and pad agent poses along the given trajectory. For details see extract_and_pad_agent_states.
    :param agent_trajectories: agent trajectories [num_frames, num_agents]
    :param reverse: if True, the padding direction will start from the end of the list instead
    :return: A trajectory of StateSE2 for all agents, and an availability array indicate whether a agent's
    future state is available at each frame.
    """
    return extract_and_pad_agent_states(agent_trajectories, lambda scene_object: StateSE2(scene_object.center.x, scene_object.center.y, scene_object.center.heading), reverse)

def extract_and_pad_agent_sizes(agent_trajectories: List[TrackedObjects], reverse: bool=False) -> Tuple[List[List[npt.NDArray[np.float32]]], List[List[bool]]]:
    """
    Extract and pad agent sizes along the given trajectory. For details see extract_and_pad_agent_states.
    :param agent_trajectories: agent trajectories [num_frames, num_agents]
    :param reverse: if True, the padding direction will start from the end of the list instead
    :return: A trajectory of sizes for all agents, and an availability array indicate whether a agent's
    future state is available at each frame.
    """
    return extract_and_pad_agent_states(agent_trajectories, lambda agent: np.array([agent.box.width, agent.box.length], np.float32), reverse)

def extract_and_pad_agent_velocities(agent_trajectories: List[TrackedObjects], reverse: bool=False) -> Tuple[List[List[StateSE2]], List[List[bool]]]:
    """
    Extract and pad agent sizes along the given trajectory. For details see extract_and_pad_agent_states.
    :param agent_trajectories: agent trajectories [num_frames, num_agents]
    :param reverse: if True, the padding direction will start from the end of the list instead
    :return: A trajectory of velocities for all agents, and an availability array indicate whether a agent's
    future state is available at each frame.
    """
    return extract_and_pad_agent_states(agent_trajectories, lambda box: StateSE2(0, 0, 0) if np.isnan(box.velocity.array).any() else StateSE2(box.velocity.x, box.velocity.y, box.center.heading), reverse)

def filter_agents(tracked_objects_history: List[TrackedObjects], reverse: bool=False, allowable_types: Optional[Set[TrackedObjectType]]=None) -> List[TrackedObjects]:
    """
    Filter detections to keep only agents of specified types which appear in the first frame (or last frame if reverse=True)
    :param tracked_objects_history: agent trajectories [num_frames, num_agents]
    :param reverse: if True, the last element in the list will be used as the filter
    :param allowable_types: TrackedObjectTypes to filter for (optional: defaults to VEHICLE)
    :return: filtered agents in the same format [num_frames, num_agents]
    """
    if allowable_types is None:
        allowable_types = {TrackedObjectType.VEHICLE}
    if reverse:
        agent_tokens = [box.track_token for object_type in allowable_types for box in tracked_objects_history[-1].get_tracked_objects_of_type(object_type)]
    else:
        agent_tokens = [box.track_token for object_type in allowable_types for box in tracked_objects_history[0].get_tracked_objects_of_type(object_type)]
    filtered_agents = [TrackedObjects([agent for object_type in allowable_types for agent in tracked_objects.get_tracked_objects_of_type(object_type) if agent.track_token in agent_tokens]) for tracked_objects in tracked_objects_history]
    return filtered_agents

def _create_ego_trajectory(num_frames: int) -> List[EgoState]:
    """
    Generate a dummy ego trajectory
    :param num_frames: length of the trajectory to be generate
    """
    return [EgoState.build_from_rear_axle(StateSE2(step, step, step), rear_axle_velocity_2d=StateVector2D(step, step), rear_axle_acceleration_2d=StateVector2D(step, step), tire_steering_angle=step, time_point=TimePoint(step), vehicle_parameters=get_pacifica_parameters()) for step in range(num_frames)]

def _create_scene_object(token: str, object_type: TrackedObjectType) -> Agent:
    """
    :param token: a unique instance token
    :param object_type: agent type.
    :return: a random Agent
    """
    scene = SceneObject.make_random(token, object_type)
    return Agent(tracked_object_type=object_type, oriented_box=scene.box, velocity=StateVector2D(0, 0), metadata=SceneObjectMetadata(token=token, track_token=token, track_id=None, timestamp_us=0))

def _create_dummy_tracked_objects_tensor(num_frames: int) -> List[TrackedObjects]:
    """
    Generates some dummy tracked objects for use with testing the tensorization functions.
    :param num_frames: The number of frames for which to generate the objects.
    :return: The generated dummy objects.
    """
    test_tracked_objects = []
    for i in range(num_frames):
        num_agents_in_frame = i + 1
        num_non_agents_in_frame = num_frames + 1 - num_agents_in_frame
        objects_in_frame: List[TrackedObject] = []
        for j in range(num_agents_in_frame):
            objects_in_frame.append(Agent(tracked_object_type=TrackedObjectType.VEHICLE, oriented_box=OrientedBox(center=StateSE2(x=j + 6, y=j + 7, heading=j + 3), length=j + 5, width=j + 4, height=-1), velocity=StateVector2D(x=j + 1, y=j + 2), metadata=SceneObjectMetadata(timestamp_us=1, token=f'agent_{j}', track_id=f'agent_{j}', track_token=f'agent_{j}'), angular_velocity=-1, predictions=None, past_trajectory=None))
            objects_in_frame.append(Agent(tracked_object_type=TrackedObjectType.BICYCLE, oriented_box=OrientedBox(center=StateSE2(x=j + 6, y=j + 7, heading=j + 3), length=j + 5, width=j + 4, height=-1), velocity=StateVector2D(x=j + 1, y=j + 2), metadata=SceneObjectMetadata(timestamp_us=1, token=f'agent_{j}', track_id=f'agent_{j}', track_token=f'agent_{j}'), angular_velocity=-1, predictions=None, past_trajectory=None))
            objects_in_frame.append(Agent(tracked_object_type=TrackedObjectType.PEDESTRIAN, oriented_box=OrientedBox(center=StateSE2(x=j + 6, y=j + 7, heading=j + 3), length=j + 5, width=j + 4, height=-1), velocity=StateVector2D(x=j + 1, y=j + 2), metadata=SceneObjectMetadata(timestamp_us=1, token=f'agent_{j}', track_id=f'agent_{j}', track_token=f'agent_{j}'), angular_velocity=-1, predictions=None, past_trajectory=None))
        for j in range(num_non_agents_in_frame):
            jj = j + 100
            objects_in_frame.append(StaticObject(tracked_object_type=TrackedObjectType.GENERIC_OBJECT, oriented_box=OrientedBox(center=StateSE2(x=jj, y=jj, heading=jj), length=jj, width=jj, height=jj), metadata=SceneObjectMetadata(timestamp_us=jj, token=f'static_{jj}', track_id=f'static_{jj}', track_token=f'static_{jj}')))
        test_tracked_objects.append(TrackedObjects(objects_in_frame))
    return test_tracked_objects

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

def setUp(self) -> None:
    """Set up test case."""
    self.num_frames = 8
    self.num_agents = 10
    self.num_missing_agents = 2
    self.agent_trajectories = [*_create_tracked_objects(5, self.num_agents), *_create_tracked_objects(3, self.num_agents - self.num_missing_agents)]
    self.time_stamps = [TimePoint(step) for step in range(self.num_frames)]

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

class RasterFeatureBuilder(AbstractFeatureBuilder):
    """
    Raster builder responsible for constructing model input features.
    """

    def __init__(self, map_features: Dict[str, int], num_input_channels: int, target_width: int, target_height: int, target_pixel_size: float, ego_width: float, ego_front_length: float, ego_rear_length: float, ego_longitudinal_offset: float, baseline_path_thickness: int) -> None:
        """
        Initializes the builder.
        :param map_features: name of map features to be drawn and their color for encoding.
        :param num_input_channels: number of input channel of the raster model.
        :param target_width: [pixels] target width of the raster
        :param target_height: [pixels] target height of the raster
        :param target_pixel_size: [m] target pixel size in meters
        :param ego_width: [m] width of the ego vehicle
        :param ego_front_length: [m] distance between the rear axle and the front bumper
        :param ego_rear_length: [m] distance between the rear axle and the rear bumper
        :param ego_longitudinal_offset: [%] offset percentage to place the ego vehicle in the raster.
                                        0.0 means place the ego at 1/2 from the bottom of the raster image.
                                        0.25 means place the ego at 1/4 from the bottom of the raster image.
        :param baseline_path_thickness: [pixels] the thickness of baseline paths in the baseline_paths_raster.
        """
        self.map_features = map_features
        self.num_input_channels = num_input_channels
        self.target_width = target_width
        self.target_height = target_height
        self.target_pixel_size = target_pixel_size
        self.ego_longitudinal_offset = ego_longitudinal_offset
        self.baseline_path_thickness = baseline_path_thickness
        self.raster_shape = (self.target_width, self.target_height)
        x_size = self.target_width * self.target_pixel_size / 2.0
        y_size = self.target_height * self.target_pixel_size / 2.0
        x_offset = 2.0 * self.ego_longitudinal_offset * x_size
        self.x_range = (-x_size + x_offset, x_size + x_offset)
        self.y_range = (-y_size, y_size)
        self.ego_width_pixels = int(ego_width / self.target_pixel_size)
        self.ego_front_length_pixels = int(ego_front_length / self.target_pixel_size)
        self.ego_rear_length_pixels = int(ego_rear_length / self.target_pixel_size)

    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'raster'

    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return Raster

    def get_features_from_scenario(self, scenario: AbstractScenario) -> Raster:
        """Inherited, see superclass."""
        ego_state = scenario.initial_ego_state
        detections = scenario.initial_tracked_objects
        map_api = scenario.map_api
        return self._compute_feature(ego_state, detections, map_api)

    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Raster:
        """Inherited, see superclass."""
        history = current_input.history
        ego_state = history.ego_states[-1]
        observation = history.observations[-1]
        if isinstance(observation, DetectionsTracks):
            return self._compute_feature(ego_state, observation, initialization.map_api)
        else:
            raise TypeError(f'Observation was type {observation.detection_type()}. Expected DetectionsTracks')

    def _compute_feature(self, ego_state: EgoState, detections: DetectionsTracks, map_api: AbstractMap) -> Raster:
        roadmap_raster = get_roadmap_raster(ego_state.agent, map_api, self.map_features, self.x_range, self.y_range, self.raster_shape, self.target_pixel_size)
        agents_raster = get_agents_raster(ego_state, detections, self.x_range, self.y_range, self.raster_shape)
        ego_raster = get_ego_raster(self.raster_shape, self.ego_longitudinal_offset, self.ego_width_pixels, self.ego_front_length_pixels, self.ego_rear_length_pixels)
        baseline_paths_raster = get_baseline_paths_raster(ego_state.agent, map_api, self.x_range, self.y_range, self.raster_shape, self.target_pixel_size, self.baseline_path_thickness)
        collated_layers: npt.NDArray[np.float32] = np.dstack([ego_raster, agents_raster, roadmap_raster, baseline_paths_raster]).astype(np.float32)
        if collated_layers.shape[-1] != self.num_input_channels:
            raise RuntimeError(f'Invalid raster numpy array. Expected {self.num_input_channels} channels, got {collated_layers.shape[-1]} Shape is {collated_layers.shape}')
        return Raster(data=collated_layers)

def __init__(self, map_features: Dict[str, int], num_input_channels: int, target_width: int, target_height: int, target_pixel_size: float, ego_width: float, ego_front_length: float, ego_rear_length: float, ego_longitudinal_offset: float, baseline_path_thickness: int) -> None:
    """
        Initializes the builder.
        :param map_features: name of map features to be drawn and their color for encoding.
        :param num_input_channels: number of input channel of the raster model.
        :param target_width: [pixels] target width of the raster
        :param target_height: [pixels] target height of the raster
        :param target_pixel_size: [m] target pixel size in meters
        :param ego_width: [m] width of the ego vehicle
        :param ego_front_length: [m] distance between the rear axle and the front bumper
        :param ego_rear_length: [m] distance between the rear axle and the rear bumper
        :param ego_longitudinal_offset: [%] offset percentage to place the ego vehicle in the raster.
                                        0.0 means place the ego at 1/2 from the bottom of the raster image.
                                        0.25 means place the ego at 1/4 from the bottom of the raster image.
        :param baseline_path_thickness: [pixels] the thickness of baseline paths in the baseline_paths_raster.
        """
    self.map_features = map_features
    self.num_input_channels = num_input_channels
    self.target_width = target_width
    self.target_height = target_height
    self.target_pixel_size = target_pixel_size
    self.ego_longitudinal_offset = ego_longitudinal_offset
    self.baseline_path_thickness = baseline_path_thickness
    self.raster_shape = (self.target_width, self.target_height)
    x_size = self.target_width * self.target_pixel_size / 2.0
    y_size = self.target_height * self.target_pixel_size / 2.0
    x_offset = 2.0 * self.ego_longitudinal_offset * x_size
    self.x_range = (-x_size + x_offset, x_size + x_offset)
    self.y_range = (-y_size, y_size)
    self.ego_width_pixels = int(ego_width / self.target_pixel_size)
    self.ego_front_length_pixels = int(ego_front_length / self.target_pixel_size)
    self.ego_rear_length_pixels = int(ego_rear_length / self.target_pixel_size)

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

@property
def num_frames(self) -> int:
    """
        :return: number of frames.
        """
    return int(self.ego[0].shape[0])

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

@property
def num_frames(self) -> int:
    """
        :return: number of frames.
        """
    return int(self.ego[0].shape[0])

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

@property
def num_frames(self) -> int:
    """
        :return: number of future frames. Note: this excludes the present frame
        """
    return int(self.data[0].shape[0])

def num_agents_in_sample(self, sample_idx: int) -> int:
    """
        Returns the number of agents at a given batch
        :param sample_idx: the batch index of interest
        :return: number of agents in the given batch
        """
    return int(self.data[sample_idx].shape[1])

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

@property
def num_of_iterations(self) -> int:
    """
        :return: number of states in a trajectory
        """
    return int(self.data.shape[-2])

def create_sample_simulation_log(output_path: Path) -> SimulationLog:
    """
    Generates a sample simulation log for use in tests.
    :param output_path: to write to.
    """
    scenario = MockAbstractScenario()
    planner = SimplePlanner(horizon_seconds=2, sampling_time=0.5, acceleration=np.array([0.0, 0.0]))
    history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
    state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
    state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
    history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
    return SimulationLog(file_path=Path(output_path), scenario=scenario, planner=planner, simulation_history=history)

@dataclass
class EgoStateTrajectoryPlot(BaseScenarioPlot):
    """A dataclass for ego state trajectory plot."""
    data_sources: Dict[int, ColumnDataSource] = field(default_factory=dict)
    plot: Optional[GlyphRenderer] = None

    def update_plot(self, main_figure: Figure, frame_index: int, doc: Document) -> None:
        """
        Update the plot.
        :param main_figure: The plotting figure.
        :param frame_index: Frame index.
        :param doc: Bokeh document that the plot lives in.
        """
        if not self.data_source_condition:
            return
        self.render_event.set()
        with self.data_source_condition:
            while self.data_sources.get(frame_index, None) is None:
                self.data_source_condition.wait()
            data_sources = dict(self.data_sources[frame_index].data)

            def update_main_figure() -> None:
                """Wrapper for the main_figure update logic to support multi-threading."""
                if self.plot is None:
                    self.plot = main_figure.line(x='xs', y='ys', line_color=simulation_tile_trajectory_style['ego']['line_color'], line_width=simulation_tile_trajectory_style['ego']['line_width'], line_alpha=simulation_tile_trajectory_style['ego']['line_alpha'], source=data_sources)
                else:
                    self.plot.data_source.data = data_sources
                self.render_event.clear()
            doc.add_next_tick_callback(lambda: update_main_figure())

    def update_data_sources(self, history: SimulationHistory) -> None:
        """
        Update ego_pose trajectory data sources.
        :param history: SimulationHistory time-series data.
        """
        if not self.data_source_condition:
            return
        with self.data_source_condition:
            for frame_index, sample in enumerate(history.data):
                trajectory = sample.trajectory.get_sampled_trajectory()
                x_coords = []
                y_coords = []
                for state in trajectory:
                    x_coords.append(state.center.x)
                    y_coords.append(state.center.y)
                source = ColumnDataSource(dict(xs=x_coords, ys=y_coords))
                self.data_sources[frame_index] = source
                self.data_source_condition.notify()

def update_data_sources(self, history: SimulationHistory) -> None:
    """
        Update ego_pose trajectory data sources.
        :param history: SimulationHistory time-series data.
        """
    if not self.data_source_condition:
        return
    with self.data_source_condition:
        for frame_index, sample in enumerate(history.data):
            trajectory = sample.trajectory.get_sampled_trajectory()
            x_coords = []
            y_coords = []
            for state in trajectory:
                x_coords.append(state.center.x)
                y_coords.append(state.center.y)
            source = ColumnDataSource(dict(xs=x_coords, ys=y_coords))
            self.data_sources[frame_index] = source
            self.data_source_condition.notify()

def setup_history(scene: Dict[str, Any], scenario: MockAbstractScenario) -> SimulationHistory:
    """
    Mock the history with a mock scenario. The scenario contains the map api, and markers present in the scene are
    used to build a list of ego poses.
    :param scene: The json scene.
    :param scenario: Scenario object.
    :return The mock history.
    """
    if 'expert_ego_states' in scene:
        expert_ego_states = scene['expert_ego_states']
        expert_egos = []
        for expert_ego_state in expert_ego_states:
            ego_state = EgoState.build_from_rear_axle(time_point=TimePoint(expert_ego_state['time_us']), rear_axle_pose=StateSE2(x=expert_ego_state['pose'][0], y=expert_ego_state['pose'][1], heading=expert_ego_state['pose'][2]), rear_axle_velocity_2d=StateVector2D(x=expert_ego_state['velocity'][0], y=expert_ego_state['velocity'][1]), rear_axle_acceleration_2d=StateVector2D(x=expert_ego_state['acceleration'][0], y=expert_ego_state['acceleration'][1]), tire_steering_angle=0, vehicle_parameters=scenario.ego_vehicle_parameters)
            expert_egos.append(ego_state)
        if len(expert_egos):
            scenario.get_expert_ego_trajectory = lambda: expert_egos
            scenario.get_ego_future_trajectory = lambda iteration, time_horizon, num_samples: expert_egos[iteration:iteration + time_horizon + 1:time_horizon // num_samples][1:num_samples + 1]
    map_name = scene['map']['area']
    map_api = get_maps_api(NUPLAN_MAPS_ROOT, NUPLAN_MAP_VERSION, map_name)
    tracked_objects = from_scene_to_tracked_objects(scene['world'])
    for tracked_object in tracked_objects:
        tracked_object._track_token = tracked_object.token
    ego_pose = scene['ego']['pose']
    ego_x = ego_pose[0]
    ego_y = ego_pose[1]
    ego_heading = ego_pose[2]
    ego_states = []
    observations = []
    ego_state = EgoState.build_from_rear_axle(time_point=TimePoint(scene['ego']['time_us']), rear_axle_pose=StateSE2(x=ego_x, y=ego_y, heading=ego_heading), rear_axle_velocity_2d=StateVector2D(x=scene['ego']['velocity'][0], y=scene['ego']['velocity'][1]), rear_axle_acceleration_2d=StateVector2D(x=scene['ego']['acceleration'][0], y=scene['ego']['acceleration'][1]), tire_steering_angle=0, vehicle_parameters=scenario.ego_vehicle_parameters)
    ego_states.append(ego_state)
    observations.append(DetectionsTracks(tracked_objects))
    ego_future_states: List[Dict[str, Any]] = scene['ego_future_states'] if 'ego_future_states' in scene else []
    world_future_states: List[Dict[str, Any]] = scene['world_future_states'] if 'world_future_states' in scene else []
    assert len(ego_future_states) == len(world_future_states), f'Length of world world_future_states: {len(world_future_states)} and length of ego_future_states: {len(ego_future_states)} not same'
    for index, (ego_future_state, future_world_state) in enumerate(zip(ego_future_states, world_future_states)):
        pose = ego_future_state['pose']
        time_us = ego_future_state['time_us']
        ego_state = EgoState.build_from_rear_axle(time_point=TimePoint(time_us), rear_axle_pose=StateSE2(x=pose[0], y=pose[1], heading=pose[2]), rear_axle_velocity_2d=StateVector2D(x=ego_future_state['velocity'][0], y=ego_future_state['velocity'][1]), rear_axle_acceleration_2d=StateVector2D(x=ego_future_state['acceleration'][0], y=ego_future_state['acceleration'][1]), vehicle_parameters=scenario.ego_vehicle_parameters, tire_steering_angle=0)
        future_tracked_objects = from_scene_to_tracked_objects(future_world_state)
        for future_tracked_object in future_tracked_objects:
            future_tracked_object._track_token = future_tracked_object.token
        ego_states.append(ego_state)
        observations.append(DetectionsTracks(future_tracked_objects))
    if ego_states:
        scenario.get_number_of_iterations = lambda: len(ego_states)
    simulation_iterations = []
    trajectories = []
    for index, ego_state in enumerate(ego_states):
        simulation_iterations.append(SimulationIteration(ego_state.time_point, index))
        history_buffer = SimulationHistoryBuffer.initialize_from_list(buffer_size=10, ego_states=[ego_states[index]], observations=[observations[index]], sample_interval=1)
        planner_input = PlannerInput(iteration=SimulationIteration(ego_states[index].time_point, 0), history=history_buffer)
        planner = SimplePlanner(horizon_seconds=10.0, sampling_time=1, acceleration=[0.0, 0.0])
        trajectories.append(planner.compute_planner_trajectory(planner_input))
    history = SimulationHistory(map_api, scenario.get_mission_goal())
    for ego_state, simulation_iteration, trajectory, observation in zip(ego_states, simulation_iterations, trajectories, observations):
        history.add_sample(SimulationHistorySample(iteration=simulation_iteration, ego_state=ego_state, trajectory=trajectory, observation=observation, traffic_light_status=scenario.get_traffic_light_status_at_iteration(simulation_iteration.index)))
    return history

class TestMetricEngine(unittest.TestCase):
    """Run metric_engine unit tests."""

    def setUp(self) -> None:
        """Set up a metric engine."""
        goal = StateSE2(x=664430.1930625531, y=3997650.6249544094, heading=0)
        self.scenario = MockAbstractScenario(mission_goal=goal)
        self.metric_names = ['ego_acceleration', 'ego_jerk']
        ego_acceleration_metric = EgoAccelerationStatistics(name=self.metric_names[0], category='Dynamics')
        ego_jerk = EgoJerkStatistics(name=self.metric_names[1], category='Dynamics', max_abs_mag_jerk=10.0)
        self.planner_name = 'planner'
        self.metric_engine = MetricsEngine(metrics=[ego_acceleration_metric], main_save_path=Path(''))
        self.metric_engine.add_metric(ego_jerk)
        self.history = self.setup_history()

    def setup_history(self) -> SimulationHistory:
        """Set up a history."""
        history = SimulationHistory(self.scenario.map_api, self.scenario.get_mission_goal())
        scene_objects = [SceneObject.from_raw_params('1', '1', 1, 1, center=StateSE2(664436.5810496865, 3997678.37696938, -1.50403628994573), size=(1.8634377032974847, 4.555735325993202, 1.5))]
        vehicle_parameters = get_pacifica_parameters()
        ego_states = [EgoState.build_from_rear_axle(StateSE2(664430.3396621217, 3997673.373507501, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(1000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664431.1930625531, 3997675.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=1.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.5, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(2000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664432.1930625531, 3997678.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(3000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664432.1930625531, 3997678.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(4000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664434.1930625531, 3997679.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=1.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(5000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664434.1930625531, 3997679.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=2.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(6000000), vehicle_parameters=vehicle_parameters)]
        simulation_iterations = [SimulationIteration(TimePoint(1000000), 0), SimulationIteration(TimePoint(2000000), 1), SimulationIteration(TimePoint(3000000), 2), SimulationIteration(TimePoint(4000000), 3), SimulationIteration(TimePoint(5000000), 4)]
        trajectories = [InterpolatedTrajectory([ego_states[0], ego_states[1]]), InterpolatedTrajectory([ego_states[1], ego_states[2]]), InterpolatedTrajectory([ego_states[2], ego_states[3]]), InterpolatedTrajectory([ego_states[3], ego_states[4]]), InterpolatedTrajectory([ego_states[4], ego_states[5]])]
        for ego_state, simulation_iteration, trajectory in zip(ego_states, simulation_iterations, trajectories):
            history.add_sample(SimulationHistorySample(iteration=simulation_iteration, ego_state=ego_state, trajectory=trajectory, observation=DetectionsTracks(TrackedObjects(scene_objects)), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(simulation_iteration.index)))
        return history

    def test_compute(self) -> None:
        """Test compute() in MetricEngine."""
        expected_values = [[0.81, 0.04, 0.3, 0.81], [0.58, -0.28, 0.15, 0.58]]
        expected_time_stamps = [1000000, 2000000, 3000000, 4000000, 5000000]
        expected_time_series_values = [[0.21, 0.04, 0.09, 0.34, 0.81], [-0.28, -0.06, 0.15, 0.36, 0.58]]
        metric_dict = self.metric_engine.compute(history=self.history, planner_name=self.planner_name, scenario=self.scenario)
        metric_files = metric_dict['mock_scenario_type_mock_scenario_name_planner']
        self.assertEqual(len(metric_files), 2)
        for index, metric_file in enumerate(metric_files):
            key = metric_file.key
            self.assertEqual(key.metric_name, self.metric_names[index])
            self.assertEqual(key.scenario_type, self.scenario.scenario_type)
            self.assertEqual(key.scenario_name, self.scenario.scenario_name)
            self.assertEqual(key.planner_name, self.planner_name)
            metric_statistics = metric_file.metric_statistics
            for statistic_result in metric_statistics:
                statistics = statistic_result.statistics
                self.assertEqual(np.round(statistics[0].value, 2), expected_values[index][0])
                self.assertEqual(np.round(statistics[1].value, 2), expected_values[index][1])
                self.assertEqual(np.round(statistics[2].value, 2), expected_values[index][2])
                self.assertEqual(np.round(statistics[3].value, 2), expected_values[index][3])
                time_series = statistic_result.time_series
                assert isinstance(time_series, TimeSeries)
                self.assertEqual(time_series.time_stamps, expected_time_stamps)
                self.assertEqual(np.round(time_series.values, 2).tolist(), expected_time_series_values[index])

def setup_history(self) -> SimulationHistory:
    """Set up a history."""
    history = SimulationHistory(self.scenario.map_api, self.scenario.get_mission_goal())
    scene_objects = [SceneObject.from_raw_params('1', '1', 1, 1, center=StateSE2(664436.5810496865, 3997678.37696938, -1.50403628994573), size=(1.8634377032974847, 4.555735325993202, 1.5))]
    vehicle_parameters = get_pacifica_parameters()
    ego_states = [EgoState.build_from_rear_axle(StateSE2(664430.3396621217, 3997673.373507501, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(1000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664431.1930625531, 3997675.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=1.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.5, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(2000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664432.1930625531, 3997678.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(3000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664432.1930625531, 3997678.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=0.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(4000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664434.1930625531, 3997679.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.5, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=1.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(5000000), vehicle_parameters=vehicle_parameters), EgoState.build_from_rear_axle(StateSE2(664434.1930625531, 3997679.3735075, -1.534863576938717), rear_axle_velocity_2d=StateVector2D(x=0.0, y=0.0), rear_axle_acceleration_2d=StateVector2D(x=2.0, y=0.0), tire_steering_angle=0.0, time_point=TimePoint(6000000), vehicle_parameters=vehicle_parameters)]
    simulation_iterations = [SimulationIteration(TimePoint(1000000), 0), SimulationIteration(TimePoint(2000000), 1), SimulationIteration(TimePoint(3000000), 2), SimulationIteration(TimePoint(4000000), 3), SimulationIteration(TimePoint(5000000), 4)]
    trajectories = [InterpolatedTrajectory([ego_states[0], ego_states[1]]), InterpolatedTrajectory([ego_states[1], ego_states[2]]), InterpolatedTrajectory([ego_states[2], ego_states[3]]), InterpolatedTrajectory([ego_states[3], ego_states[4]]), InterpolatedTrajectory([ego_states[4], ego_states[5]])]
    for ego_state, simulation_iteration, trajectory in zip(ego_states, simulation_iterations, trajectories):
        history.add_sample(SimulationHistorySample(iteration=simulation_iteration, ego_state=ego_state, trajectory=trajectory, observation=DetectionsTracks(TrackedObjects(scene_objects)), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(simulation_iteration.index)))
    return history

class TestViolationMetricBase(unittest.TestCase):
    """Creates mock violations for testing."""

    def setUp(self) -> None:
        """Set up mock violations."""
        self.violation_metric_base = ViolationMetricBase(name='metric_1', category='Dynamics', max_violation_threshold=1)
        self.mock_abstract_scenario = MockAbstractScenario()
        self.violation_metric_1 = [self._create_mock_violation('metric_1', duration=3, extremum=12.23, mean=8.9), self._create_mock_violation('metric_1', duration=1, extremum=123.23, mean=111.1), self._create_mock_violation('metric_1', duration=10, extremum=12.23, mean=4.92)]
        self.violation_metric_2 = [self._create_mock_violation('metric_2', duration=13, extremum=1.2, mean=0.0)]

    def _create_mock_violation(self, metric_name: str, duration: int, extremum: float, mean: float) -> MetricViolation:
        """Creates a simple violation
        :param metric_name: name of the metric
        :param duration: duration of the violation
        :param extremum: maximally violating value
        :param mean: mean value of violation depth
        :return: a MetricViolation with the given parameters.
        """
        return MetricViolation(metric_computator=self.violation_metric_base.name, name=metric_name, metric_category=self.violation_metric_base.category, unit='unit', start_timestamp=0, duration=duration, extremum=extremum, mean=mean)

    def test_successful_aggregation(self) -> None:
        """Checks that the aggregation of MetricViolations works as intended."""
        aggregated_metrics = self.violation_metric_base.aggregate_metric_violations(metric_violations=self.violation_metric_1, scenario=self.mock_abstract_scenario)[0]
        self.assertEqual(aggregated_metrics.metric_computator, self.violation_metric_base.name)
        self.assertEqual(aggregated_metrics.metric_category, self.violation_metric_base.category)
        statistics = aggregated_metrics.statistics
        self.assertEqual(len(self.violation_metric_1), statistics[0].value)
        self.assertAlmostEqual(statistics[1].value, 123.23, 2)
        self.assertAlmostEqual(statistics[2].value, 12.23, 3)
        self.assertAlmostEqual(statistics[3].value, 13.357, 3)

    def test_failure_on_mixed_metrics(self) -> None:
        """Checks that the aggregation fails when called on MetricViolations from different metrics."""
        with self.assertRaises(AssertionError):
            self.violation_metric_base.aggregate_metric_violations(self.violation_metric_1 + self.violation_metric_2, scenario=self.mock_abstract_scenario)

    def test_empty_statistics_on_empty_violations(self) -> None:
        """Checks that for an empty list of MetricViolations we get a MetricStatistics with zero violations."""
        empty_statistics = self.violation_metric_base.aggregate_metric_violations([], self.mock_abstract_scenario)[0]
        self.assertTrue(empty_statistics.statistics[0].value)

def setUp(self) -> None:
    """Set up mock violations."""
    self.violation_metric_base = ViolationMetricBase(name='metric_1', category='Dynamics', max_violation_threshold=1)
    self.mock_abstract_scenario = MockAbstractScenario()
    self.violation_metric_1 = [self._create_mock_violation('metric_1', duration=3, extremum=12.23, mean=8.9), self._create_mock_violation('metric_1', duration=1, extremum=123.23, mean=111.1), self._create_mock_violation('metric_1', duration=10, extremum=12.23, mean=4.92)]
    self.violation_metric_2 = [self._create_mock_violation('metric_2', duration=13, extremum=1.2, mean=0.0)]

def find_new_collisions(ego_state: EgoState, observation: DetectionsTracks, collided_track_ids: Set[str]) -> Tuple[Set[str], Dict[str, CollisionData]]:
    """
    Identify and classify new collisions in a given timestamp. We assume that ego can only collide with an agent
    once in the scenario. Collided tracks will be removed from metrics evaluation at future timestamps.
    :param ego_state: Ego's state at the current timestamp.
    :param observation: DetectionsTracks at the current timestamp.
    :param collided_track_ids: Set of all collisions happend before the current timestamp.
    :return Updated set of collided track ids and a dict of new collided tracks and their CollisionData.
    """
    collisions_id_data: Dict[str, CollisionData] = {}
    for tracked_object in observation.tracked_objects:
        if tracked_object.track_token not in collided_track_ids and in_collision(ego_state.car_footprint.oriented_box, tracked_object.box):
            collided_track_ids.add(tracked_object.track_token)
            collision_delta_v = ego_delta_v_collision(ego_state, tracked_object)
            collision_type = _get_collision_type(ego_state, tracked_object)
            collisions_id_data[tracked_object.track_token] = CollisionData(collision_delta_v, collision_type, tracked_object.tracked_object_type)
    return (collided_track_ids, collisions_id_data)

def _get_relevant_tracks(ego_pose: npt.NDArray[np.float64], ego_box: OrientedBox, ego_dx: float, ego_dy: float, tracks_poses: npt.NDArray[np.float64], tracks_boxes: List[OrientedBox], tracks_dxy: npt.NDArray[np.float64], time_step_size: float, time_horizon: float) -> npt.NDArray[np.int64]:
    """
    Find relevant tracks affecting time to collision, determined by overlapping boxes elongated according to current
      movement.
    :param ego_pose: Ego pose.
    :param ego_box: Oriented box of ego.
    :param ego_dx: Movement in x axis in global frame at each time_step_size.
    :param ego_dy: Movement in y axis in global frame at each time_step_size.
    :param tracks_poses: Pose for each track.
    :param tracks_boxes: Oriented box for each track.
    :param tracks_dxy: Tracks' movements in the global frame
    :param time_step_size: [s] Step size for the propagation of collision agents.
    :param time_horizon: [s] Time horizon for collision checking.
    :return: Indices for tracks revlevant to time to collision calculations.
    """
    ego_elongated_box_center_pose: npt.NDArray[np.float64] = np.array([time_horizon / time_step_size / 2 * ego_dx + ego_pose[0], time_horizon / time_step_size / 2 * ego_dy + ego_pose[1], ego_pose[2]], dtype=np.float64)
    ego_elongated_box = OrientedBox(StateSE2(*ego_elongated_box_center_pose), _get_elongated_box_length(ego_box.length, ego_dx, ego_dy, time_step_size, time_horizon), ego_box.width, ego_box.height)
    tracks_elongated_box_center_poses: npt.NDArray[np.float64] = np.concatenate((time_horizon / time_step_size / 2 * tracks_dxy + tracks_poses[:, :2], tracks_poses[:, 2].reshape(-1, 1)), axis=1)
    tracks_elongated_boxes = [OrientedBox(StateSE2(*track_elongated_box_center_pose), _get_elongated_box_length(track_box.length, track_dxy[0], track_dxy[1], time_step_size, time_horizon), track_box.width, track_box.height) for track_box, track_dxy, track_elongated_box_center_pose in zip(tracks_boxes, tracks_dxy, tracks_elongated_box_center_poses)]
    relevant_tracks_mask = np.where([in_collision(ego_elongated_box, track_elongated_box) for track_elongated_box in tracks_elongated_boxes])[0]
    return relevant_tracks_mask

def _compute_time_to_collision_at_timestamp(timestamp: int, ego_state: EgoState, ego_speed: npt.NDArray[np.float64], tracks_poses: npt.NDArray[np.float64], tracks_speed: npt.NDArray[np.float64], tracks_boxes: List[OrientedBox], timestamps_at_fault_collisions: List[int], time_step_size: float, time_horizon: float, stopped_speed_threshold: float) -> Optional[float]:
    """
    Helper function for compute_time_to_collision. Computes time to collision value at given timestamp.
    :param timestamp: Time in time_us.
    :param ego_state: Ego state.
    :param ego_speed: Ego speed.
    :param tracks_poses: Pose for each track.
    :param tracks_speed: Array of tracks speeds.
    :param tracks_boxes: Oriented box for each track.
    :param timestamps_at_fault_collisions: List of timestamps corresponding to at-fault-collisions in the history.
    :param time_step_size: [s] Step size for the propagation of collision agents.
    :param time_horizon: [s] Time horizon for collision checking.
    :param stopped_speed_threshold: Threshold for 0 speed due to noise.
    :return: Computed time to collision if available, otherwise None.
    """
    ego_in_at_fault_collision = timestamp in timestamps_at_fault_collisions
    if ego_in_at_fault_collision:
        return 0.0
    if len(tracks_poses) == 0 or ego_speed <= stopped_speed_threshold:
        return None
    displacement_info = _get_ego_tracks_displacement_info(ego_state, ego_speed, tracks_poses, tracks_speed, time_step_size)
    relevant_tracks_mask = _get_relevant_tracks(displacement_info.ego_pose, displacement_info.ego_box, displacement_info.ego_dx, displacement_info.ego_dy, tracks_poses, tracks_boxes, displacement_info.tracks_dxy, time_step_size, time_horizon)
    if not len(relevant_tracks_mask):
        return None
    for time_to_collision in np.arange(time_step_size, time_horizon, time_step_size):
        displacement_info.ego_pose[:2] += (displacement_info.ego_dx, displacement_info.ego_dy)
        projected_ego_box = OrientedBox.from_new_pose(displacement_info.ego_box, StateSE2(*displacement_info.ego_pose))
        tracks_poses[:, :2] += displacement_info.tracks_dxy
        for track_box, track_pose in zip(tracks_boxes[relevant_tracks_mask], tracks_poses[relevant_tracks_mask]):
            projected_track_box = OrientedBox.from_new_pose(track_box, StateSE2(*track_pose))
            if in_collision(projected_ego_box, projected_track_box):
                return float(time_to_collision)
    return None

@dataclass
class VelocityData:
    """
    Class to track VelocityRecord over the simulation history.
    """
    data: List[VelocityRecord]

    def add_data(self, velocity: float, timestamp: int, distance_to_stop_line: float) -> None:
        """
        Add new data to the list
        :param velocity: [m/s^2], Velocity at the current timestamp
        :param timestamp: Timestamp
        :param distance_to_stop_line: [m], Distance to the stop line.
        """
        if self.data is None:
            self.data = []
        self.data.append(VelocityRecord(velocity=velocity, timestamp=timestamp, distance_to_stop_line=distance_to_stop_line))

    @property
    def velocity_np(self) -> npt.NDArray[np.float32]:
        """
        Velocity in numpy representation.
        """
        return np.asarray([data.velocity for data in self.data])

    @property
    def timestamp_np(self) -> npt.NDArray[np.int32]:
        """
        Timestamp in numpy representation.
        """
        return np.asarray([data.timestamp for data in self.data])

    @property
    def distance_to_stop_line_np(self) -> npt.NDArray[np.float32]:
        """
        Distance to stop line in numpy representation.
        """
        return np.asarray([data.distance_to_stop_line for data in self.data])

    @property
    def min_distance_stop_line_record(self) -> VelocityRecord:
        """
        Return velocity record of minimum distance stop line
        :return A velocity record.
        """
        distance_to_stop_line = self.distance_to_stop_line_np
        index = np.argmin(distance_to_stop_line)
        return self.data[int(index)]

    @property
    def min_velocity_record(self) -> VelocityRecord:
        """
        Return minimum velocity record
        :return A velocity record.
        """
        index = np.argmin(self.velocity_np)
        return self.data[int(index)]

@property
def min_distance_stop_line_record(self) -> VelocityRecord:
    """
        Return velocity record of minimum distance stop line
        :return A velocity record.
        """
    distance_to_stop_line = self.distance_to_stop_line_np
    index = np.argmin(distance_to_stop_line)
    return self.data[int(index)]

@property
def min_velocity_record(self) -> VelocityRecord:
    """
        Return minimum velocity record
        :return A velocity record.
        """
    index = np.argmin(self.velocity_np)
    return self.data[int(index)]

class EgoStopAtStopLineStatistics(ViolationMetricBase):
    """
    Ego stopped at stop line metric.
    """

    def __init__(self, name: str, category: str, max_violation_threshold: int, distance_threshold: float, velocity_threshold: float) -> None:
        """
        Initializes the EgoProgressAlongExpertRouteStatistics class
        Rule formulation: 1. Get the nearest stop polygon (less than the distance threshold).
                          2. Check if the stop polygon is in any lanes.
                          3. Check if front corners of ego cross the stop polygon.
                          4. Check if no any leading agents.
                          5. Get min_velocity(distance_stop_line) until the ego leaves the stop polygon.
        :param name: Metric name
        :param category: Metric category
        :param max_violation_threshold: Maximum threshold for the violation when computing the score
        :param distance_threshold: Distances between ego front side and stop line lower than this threshold
        assumed to be the first vehicle before the stop line
        :param velocity_threshold: Velocity threshold to consider an ego stopped.
        """
        super().__init__(name=name, category=category, max_violation_threshold=max_violation_threshold)
        self._distance_threshold = distance_threshold
        self._velocity_threshold = velocity_threshold
        self._stopping_velocity_data: List[VelocityData] = []
        self._previous_stop_polygon_fid: Optional[str] = None

    @staticmethod
    def get_nearest_stop_line(map_api: AbstractMap, ego_pose_front: LineString) -> Optional[Tuple[str, Polygon]]:
        """
        Retrieve the nearest stop polygon
        :param map_api: AbstractMap map api
        :param ego_pose_front: Ego pose front corner line
        :return Nearest stop polygon fid if distance is less than the threshold.
        """
        center_x, center_y = ego_pose_front.centroid.xy
        center = Point2D(center_x[0], center_y[0])
        if not map_api.is_in_layer(center, layer=SemanticMapLayer.LANE):
            return None
        stop_line_fid, distance = map_api.get_distance_to_nearest_map_object(center, SemanticMapLayer.STOP_LINE)
        if stop_line_fid is None:
            return None
        stop_line: StopLine = map_api.get_map_object(stop_line_fid, SemanticMapLayer.STOP_LINE)
        lane: Optional[Lane] = map_api.get_one_map_object(center, SemanticMapLayer.LANE)
        if lane is not None:
            return (stop_line_fid, stop_line.polygon if stop_line.polygon.intersects(lane.polygon) else None)
        return None

    @staticmethod
    def check_for_leading_agents(detections: Observation, ego_state: EgoState, map_api: AbstractMap) -> bool:
        """
        Get the nearest leading agent
        :param detections: Detection class
        :param ego_state: Ego in oriented box representation
        :param map_api: AbstractMap api
        :return True if there is a leading agent, False otherwise
        """
        if isinstance(detections, DetectionsTracks):
            if len(detections.tracked_objects.tracked_objects) == 0:
                return False
            ego_agent = ego_state.agent
            for index, box in enumerate(detections.tracked_objects):
                if box.token is None:
                    box.token = str(index + 1)
            scene_objects: List[SceneObject] = [ego_agent]
            scene_objects.extend([scene_object for scene_object in detections.tracked_objects])
            occupancy_map = STRTreeOccupancyMapFactory.get_from_boxes(scene_objects)
            agent_states = {scene_object.token: StateSE2(x=scene_object.center.x, y=scene_object.center.y, heading=scene_object.center.heading) for scene_object in scene_objects}
            ego_pose: StateSE2 = agent_states['ego']
            lane = map_api.get_one_map_object(ego_pose, SemanticMapLayer.LANE)
            ego_baseline = lane.baseline_path
            ego_progress = ego_baseline.get_nearest_arc_length_from_position(ego_pose)
            progress_path = create_path_from_se2(ego_baseline.discrete_path)
            ego_path_to_go = trim_path_up_to_progress(progress_path, ego_progress)
            ego_path_to_go = path_to_linestring(ego_path_to_go)
            intersecting_agents = occupancy_map.intersects(ego_path_to_go.buffer(scene_objects[0].box.width / 2, cap_style=CAP_STYLE.flat))
            if intersecting_agents.size > 1:
                return True
        return False

    def _compute_velocity_statistics(self, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Compute statistics in each stop line
        :param scenario: Scenario running this metric
        :return A list of metric statistics.
        """
        if not self._stopping_velocity_data:
            return []
        mean_ego_min_distance_to_stop_line = []
        mean_ego_min_velocity_before_stop_line = []
        aggregated_timestamp_velocity = []
        aggregated_timestamps = []
        ego_stop_status = []
        for velocity_data in self._stopping_velocity_data:
            min_distance_velocity_record = velocity_data.min_distance_stop_line_record
            mean_ego_min_distance_to_stop_line.append(min_distance_velocity_record.distance_to_stop_line)
            mean_ego_min_velocity_before_stop_line.append(min_distance_velocity_record.velocity)
            if min_distance_velocity_record.distance_to_stop_line < self._distance_threshold and min_distance_velocity_record.velocity < self._velocity_threshold:
                stop_status = True
            else:
                stop_status = False
            ego_stop_status.append(stop_status)
            aggregated_timestamp_velocity.append(velocity_data.velocity_np)
            aggregated_timestamps.append(velocity_data.timestamp_np)
        statistics = [Statistic(name='number_of_ego_stop_before_stop_line', unit=MetricStatisticsType.COUNT.unit, value=sum(ego_stop_status), type=MetricStatisticsType.COUNT), Statistic(name='number_of_ego_before_stop_line', unit=MetricStatisticsType.COUNT.unit, value=len(ego_stop_status), type=MetricStatisticsType.COUNT), Statistic(name='mean_ego_min_distance_to_stop_line', unit='meters', value=float(np.mean(mean_ego_min_distance_to_stop_line)), type=MetricStatisticsType.VALUE), Statistic(name='mean_ego_min_velocity_before_stop_line', unit='meters_per_second_squared', value=float(np.mean(mean_ego_min_velocity_before_stop_line)), type=MetricStatisticsType.VALUE)]
        aggregated_timestamp_velocity = np.hstack(aggregated_timestamp_velocity)
        aggregated_timestamps = np.hstack(aggregated_timestamps)
        velocity_time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(aggregated_timestamps), values=list(aggregated_timestamp_velocity))
        results = self._construct_metric_results(metric_statistics=statistics, time_series=velocity_time_series, scenario=scenario)
        return results

    def _save_stopping_velocity(self, current_stop_polygon_fid: str, history_data: SimulationHistorySample, stop_polygon_in_lane: Polygon, ego_pose_front: LineString) -> None:
        """
        Save velocity, timestamp and distance to a stop line if the ego is stopping
        :param current_stop_polygon_fid: Current stop polygon fid
        :param history_data: History sample data at current timestamp
        :param stop_polygon_in_lane: The stop polygon where the ego is in
        :param ego_pose_front: Front line string (front right corner and left corner) of the ego.
        """
        stop_line: LineString = LineString(stop_polygon_in_lane.exterior.coords[:2])
        distance_ego_front_stop_line = stop_line.distance(ego_pose_front)
        current_velocity = history_data.ego_state.dynamic_car_state.speed
        current_timestamp = history_data.ego_state.time_point.time_us
        if current_stop_polygon_fid == self._previous_stop_polygon_fid:
            self._stopping_velocity_data[-1].add_data(velocity=current_velocity, timestamp=current_timestamp, distance_to_stop_line=distance_ego_front_stop_line)
        else:
            self._previous_stop_polygon_fid = current_stop_polygon_fid
            velocity_data = VelocityData([])
            velocity_data.add_data(velocity=current_velocity, timestamp=current_timestamp, distance_to_stop_line=distance_ego_front_stop_line)
            self._stopping_velocity_data.append(velocity_data)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the ego stopped at stop line metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated ego stopped at stop line metric.
        """
        ego_states: List[EgoState] = history.extract_ego_state
        ego_pose_fronts: List[LineString] = [LineString([state.car_footprint.oriented_box.geometry.exterior.coords[0], state.car_footprint.oriented_box.geometry.exterior.coords[3]]) for state in ego_states]
        scenario_map: AbstractMap = history.map_api
        for ego_pose_front, ego_state, history_data in zip(ego_pose_fronts, ego_states, history.data):
            stop_polygon_info: Optional[Tuple[str, Polygon]] = self.get_nearest_stop_line(map_api=scenario_map, ego_pose_front=ego_pose_front)
            if stop_polygon_info is None:
                continue
            fid, stop_polygon_in_lane = stop_polygon_info
            ego_pose_front_stop_polygon_distance: float = ego_pose_front.distance(stop_polygon_in_lane)
            if ego_pose_front_stop_polygon_distance != 0:
                continue
            detections: Observation = history_data.observation
            has_leading_agent = self.check_for_leading_agents(detections=detections, ego_state=ego_state, map_api=scenario_map)
            if has_leading_agent:
                continue
            self._save_stopping_velocity(current_stop_polygon_fid=fid, history_data=history_data, stop_polygon_in_lane=stop_polygon_in_lane, ego_pose_front=ego_pose_front)
        results = self._compute_velocity_statistics(scenario=scenario)
        return results

@staticmethod
def check_for_leading_agents(detections: Observation, ego_state: EgoState, map_api: AbstractMap) -> bool:
    """
        Get the nearest leading agent
        :param detections: Detection class
        :param ego_state: Ego in oriented box representation
        :param map_api: AbstractMap api
        :return True if there is a leading agent, False otherwise
        """
    if isinstance(detections, DetectionsTracks):
        if len(detections.tracked_objects.tracked_objects) == 0:
            return False
        ego_agent = ego_state.agent
        for index, box in enumerate(detections.tracked_objects):
            if box.token is None:
                box.token = str(index + 1)
        scene_objects: List[SceneObject] = [ego_agent]
        scene_objects.extend([scene_object for scene_object in detections.tracked_objects])
        occupancy_map = STRTreeOccupancyMapFactory.get_from_boxes(scene_objects)
        agent_states = {scene_object.token: StateSE2(x=scene_object.center.x, y=scene_object.center.y, heading=scene_object.center.heading) for scene_object in scene_objects}
        ego_pose: StateSE2 = agent_states['ego']
        lane = map_api.get_one_map_object(ego_pose, SemanticMapLayer.LANE)
        ego_baseline = lane.baseline_path
        ego_progress = ego_baseline.get_nearest_arc_length_from_position(ego_pose)
        progress_path = create_path_from_se2(ego_baseline.discrete_path)
        ego_path_to_go = trim_path_up_to_progress(progress_path, ego_progress)
        ego_path_to_go = path_to_linestring(ego_path_to_go)
        intersecting_agents = occupancy_map.intersects(ego_path_to_go.buffer(scene_objects[0].box.width / 2, cap_style=CAP_STYLE.flat))
        if intersecting_agents.size > 1:
            return True
    return False

def build_metric_runners(cfg: DictConfig, simulation_logs: List[SimulationLog]) -> List[MetricRunner]:
    """
    Build metric runners.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :param simulation_logs: A list of simulation logs.
    :return A list of metric runners.
    """
    logger.info('Building metric runners...')
    metric_runners = list()
    logger.info('Extracting scenarios...')
    scenarios = [simulation_log.scenario for simulation_log in simulation_logs]
    logger.info('Extracting scenarios...DONE!')
    logger.info('Building metric engines...')
    metric_engines_map = build_metrics_engines(cfg=cfg, scenarios=scenarios)
    logger.info('Building metric engines...DONE')
    logger.info(f'Building metric_runner from {len(scenarios)} scenarios...')
    for simulation_log in simulation_logs:
        scenario = simulation_log.scenario
        metric_engine = metric_engines_map.get(scenario.scenario_type, None)
        if not metric_engine:
            raise ValueError(f'{scenario.scenario_type} not found in a metric engine.')
        if not simulation_log:
            raise ValueError(f'{scenario.scenario_name} not found in simulation logs.')
        metric_callback = MetricCallback(metric_engine=metric_engine)
        metric_runner = MetricRunner(simulation_log=simulation_log, metric_callback=metric_callback)
        metric_runners.append(metric_runner)
    logger.info('Building metric runners...DONE!')
    return metric_runners

def sample_indices_with_time_horizon(num_samples: int, time_horizon: float, time_interval: float) -> List[int]:
    """
    Samples the indices that can access N number of samples in a T time horizon from a sequence
    of temporal elemements with DT time interval.
    :param num_samples: number of elements to sample.
    :param time_horizon: [s] time horizon of sampled elements.
    :param time_interval: [s] time interval of sequence to sample from.
    :return: sampled indices that access the temporal sequence.
    """
    if time_horizon <= 0.0 or time_interval <= 0.0 or time_horizon < time_interval:
        raise ValueError(f'Time horizon {time_horizon} must be greater or equal than target time interval {time_interval} and both must be positive.')
    num_intervals = int(time_horizon / time_interval) + 1
    step_size = num_intervals // num_samples
    assert step_size > 0, f'Cannot get {num_samples} samples in a {time_horizon}s horizon at {time_interval}s intervals'
    indices = list(range(step_size, num_intervals + 1, step_size))
    indices = indices[:num_samples]
    assert len(indices) == num_samples, f'Expected {num_samples} samples but only {len(indices)} were sampled'
    return indices

class MockAbstractScenarioBuilder(AbstractScenarioBuilder):
    """Mock abstract scenario builder class used for testing."""

    def __init__(self, num_scenarios: int=0):
        """
        The init method
        :param num_scenarios: The number of scenarios to return from get_scenarios()
        """
        self.num_scenarios = num_scenarios

    @classmethod
    def get_scenario_type(cls) -> Type[AbstractScenario]:
        """Inherited. See superclass."""
        return cast(Type[AbstractScenario], MockAbstractScenario)

    def get_scenarios(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> List[AbstractScenario]:
        """Implemented. See interface."""
        return [MockAbstractScenario() for _ in range(self.num_scenarios)]

    def get_map_factory(self) -> AbstractMapFactory:
        """Implemented. See interface."""
        return MockMapFactory()

    @property
    def repartition_strategy(self) -> RepartitionStrategy:
        """Implemented. See interface."""
        return RepartitionStrategy.INLINE

def get_scenarios(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> List[AbstractScenario]:
    """Implemented. See interface."""
    return [MockAbstractScenario() for _ in range(self.num_scenarios)]

def get_num_samples(num_samples: Optional[int], time_horizon: float, database_interval: float) -> int:
    """
    Set num samples based on the time_horizon and database interval if num_samples is not set
    :param num_samples: if None, it will be computed based on  math.floor(time_horizon / database_interval)
    :param time_horizon: [s] horizon in which we want to look into
    :param database_interval: interval of the database
    :return: number of samples to iterate over
    """
    return num_samples if num_samples else int(time_horizon / database_interval)

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
def ego_vehicle_parameters(self) -> VehicleParameters:
    """Inherited, see superclass."""
    return get_pacifica_parameters()

def extract_tracked_objects_within_time_window(token: str, log_file: str, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> TrackedObjects:
    """
    Extracts the tracked objects in a time window centered on a token.
    :param token: The token on which to center the time window.
    :param past_time_horizon: The time in the past for which to search.
    :param future_time_horizon: The time in the future for which to search.
    :param filter_track_tokens: If provided, objects with track_tokens missing from the set will be excluded.
    :param future_trajectory_sampling: If provided, the future trajectory sampling to use for future waypoints.
    :return: The retrieved TrackedObjects.
    """
    tracked_objects: List[TrackedObject] = []
    agent_indexes: Dict[int, Dict[str, int]] = {}
    token_timestamp = get_sensor_data_token_timestamp_from_db(log_file, get_lidarpc_sensor_data(), token)
    start_time = int(token_timestamp - 1000000.0 * past_time_horizon)
    end_time = int(token_timestamp + 1000000.0 * future_time_horizon)
    for idx, tracked_object in enumerate(get_tracked_objects_within_time_interval_from_db(log_file, start_time, end_time, filter_track_tokens)):
        if future_trajectory_sampling and isinstance(tracked_object, Agent):
            if tracked_object.metadata.timestamp_us not in agent_indexes:
                agent_indexes[tracked_object.metadata.timestamp_us] = {}
            agent_indexes[tracked_object.metadata.timestamp_us][tracked_object.metadata.track_token] = idx
        tracked_objects.append(tracked_object)
    if future_trajectory_sampling:
        _process_future_trajectories_for_windowed_agents(log_file, tracked_objects, agent_indexes, future_trajectory_sampling)
    return TrackedObjects(tracked_objects=tracked_objects)

def extract_sensor_tokens_as_scenario(log_file: str, sensor_data_source: SensorDataSource, anchor_timestamp: float, scenario_extraction_info: ScenarioExtractionInfo) -> Generator[str, None, None]:
    """
    Extract a list of sensor tokens that form a scenario around an anchor timestamp.
    :param log_file: The log file to access
    :param sensor_data_source: Parameters for querying the correct table.
    :param anchor_timestamp: Timestamp of Sensor representing the start of the scenario.
    :param scenario_extraction_info: Structure containing information used to extract the scenario.
    :return: List of extracted sensor tokens representing the scenario.
    """
    start_timestamp = int(anchor_timestamp + scenario_extraction_info.extraction_offset * 1000000.0)
    end_timestamp = int(start_timestamp + scenario_extraction_info.scenario_duration * 1000000.0)
    subsample_step = int(1.0 / scenario_extraction_info.subsample_ratio)
    return cast(Generator[str, None, None], get_sampled_sensor_tokens_in_time_window_from_db(log_file, sensor_data_source, start_timestamp, end_timestamp, subsample_step))

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

@property
def map_api(self) -> AbstractMap:
    """Inherited, see superclass."""
    return get_maps_api(self._map_root, self._map_version, self._map_name)

def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
    """Inherited, see superclass."""
    assert 0 <= iteration < self.get_number_of_iterations(), f'Iteration is out of scenario: {iteration}!'
    return DetectionsTracks(extract_tracked_objects(self._lidarpc_tokens[iteration], self._log_file, future_trajectory_sampling))

def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Inherited, see superclass."""
    for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, True):
        yield TimePoint(lidar_pc.timestamp)

def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
    """Inherited, see superclass."""
    for lidar_pc in self._find_matching_lidar_pcs(iteration, num_samples, time_horizon, False):
        yield TimePoint(lidar_pc.timestamp)

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

@staticmethod
def _extract_simulation_iteration(planner_input_message: chpb.PlannerInput) -> SimulationIteration:
    return SimulationIteration(TimePoint(planner_input_message.simulation_iteration.time_us), planner_input_message.simulation_iteration.index)

def proto_vector_2d_from_vector_2d(vector: StateVector2D) -> chpb.StateVector2D:
    """
    Serializes StateVector2D to a StateVector2D message
    :param vector: The StateVector2D object
    :return: The corresponding StateVector2D message
    """
    return chpb.StateVector2D(x=vector.x, y=vector.y)

def vector_2d_from_proto_vector_2d(vector: chpb.StateVector2D) -> StateVector2D:
    """
    Deserializes StateVector2D message to a StateVector2D object
    :param vector: The proto StateVector2D message
    :return: The corresponding StateVector2D object
    """
    return StateVector2D(x=vector.x, y=vector.y)

def proto_se2_from_se2(se2: StateSE2) -> chpb.StateSE2:
    """
    Serializes StateSE2 to a StateSE2 message
    :param se2: The StateSE2 object
    :return: The corresponding StateSE2 message
    """
    return chpb.StateSE2(x=se2.x, y=se2.y, heading=se2.heading)

def se2_from_proto_se2(se2: chpb.StateSE2) -> StateSE2:
    """
    Deserializes StateSE2 message to a StateSE2 object
    :param se2: The proto StateSE2 message
    :return: The corresponding StateSE2 object
    """
    return StateSE2(x=se2.x, y=se2.y, heading=se2.heading)

def ego_state_from_proto_ego_state(ego_state: chpb.EgoState) -> EgoState:
    """
    Deserializes EgoState message to a EgoState object
    :param ego_state: The proto EgoState message
    :return: The corresponding EgoState object
    """
    vehicle_parameters = get_pacifica_parameters()
    return EgoState.build_from_rear_axle(rear_axle_pose=se2_from_proto_se2(ego_state.rear_axle_pose), rear_axle_velocity_2d=vector_2d_from_proto_vector_2d(ego_state.rear_axle_velocity_2d), rear_axle_acceleration_2d=vector_2d_from_proto_vector_2d(ego_state.rear_axle_acceleration_2d), tire_steering_angle=ego_state.tire_steering_angle, time_point=TimePoint(ego_state.time_us), angular_vel=ego_state.angular_vel, angular_accel=ego_state.angular_accel, vehicle_parameters=vehicle_parameters)

def interp_traj_from_proto_traj(trajectory: chpb.Trajectory) -> InterpolatedTrajectory:
    """
    Deserializes Trajectory message to a InterpolatedTrajectory object
    :param trajectory: The proto Trajectory message
    :return: The corresponding InterpolatedTrajectory object
    """
    return InterpolatedTrajectory([ego_state_from_proto_ego_state(state) for state in trajectory.ego_states])

def find_free_port_number() -> int:
    """
    Finds a free port number
    :return: the port number of a free port
    """
    skt = socket.socket()
    skt.bind(('', 0))
    port = skt.getsockname()[1]
    skt.close()
    return int(port)

class TestProtoConverters(unittest.TestCase):
    """Tests proto converters by checking if composition is idempotent."""

    def test_trajectory_conversions(self) -> None:
        """Tests conversions between trajectory object and messages."""
        trajectory = InterpolatedTrajectory([get_sample_ego_state(StateSE2(0, 1, 2)), get_sample_ego_state(StateSE2(1, 2, 3), time_us=1)])
        result = interp_traj_from_proto_traj(proto_traj_from_inter_traj(trajectory))
        for result_state, trajectory_state in zip(result.get_sampled_trajectory(), trajectory.get_sampled_trajectory()):
            np.allclose(result_state.to_split_state().linear_states, trajectory_state.to_split_state().linear_states)
            np.allclose(result_state.to_split_state().angular_states, trajectory_state.to_split_state().angular_states)

    def test_tl_status_type_conversions(self) -> None:
        """Tests conversions between TL status data and messages."""
        tl_status_type = TrafficLightStatusType.RED
        result = tl_status_type_from_proto_tl_status_type(proto_tl_status_type_from_tl_status_type(tl_status_type))
        self.assertEqual(tl_status_type, result)

    def test_tl_status_data_conversions(self) -> None:
        """Tests conversions between TL status type and messages."""
        tl_status = TrafficLightStatusData(TrafficLightStatusType.RED, 123, 456)
        result = tl_status_data_from_proto_tl_status_data(proto_tl_status_data_from_tl_status_data(tl_status))
        self.assertEqual(tl_status, result)

def test_trajectory_conversions(self) -> None:
    """Tests conversions between trajectory object and messages."""
    trajectory = InterpolatedTrajectory([get_sample_ego_state(StateSE2(0, 1, 2)), get_sample_ego_state(StateSE2(1, 2, 3), time_us=1)])
    result = interp_traj_from_proto_traj(proto_traj_from_inter_traj(trajectory))
    for result_state, trajectory_state in zip(result.get_sampled_trajectory(), trajectory.get_sampled_trajectory()):
        np.allclose(result_state.to_split_state().linear_states, trajectory_state.to_split_state().linear_states)
        np.allclose(result_state.to_split_state().angular_states, trajectory_state.to_split_state().angular_states)

