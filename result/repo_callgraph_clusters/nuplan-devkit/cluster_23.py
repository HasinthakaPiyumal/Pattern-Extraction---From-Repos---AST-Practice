# Cluster 23

def list_categories(db: NuPlanDB) -> None:
    """
    Print categories, counts and stats.
    :param db: Database to use for printing metadata.
    """
    logger.info('\nCompiling category summary ... ')
    length_name = db.session.query(LidarBox.length, Category.name).join(Track, LidarBox.track_token == Track.token).join(Category, Track.category_token == Category.token)
    width_name = db.session.query(LidarBox.width, Category.name).join(Track, LidarBox.track_token == Track.token).join(Category, Track.category_token == Category.token)
    height_name = db.session.query(LidarBox.height, Category.name).join(Track, LidarBox.track_token == Track.token).join(Category, Track.category_token == Category.token)
    length_categories = defaultdict(list)
    for size, name in length_name:
        length_categories[name].append(size)
    width_categories = defaultdict(list)
    for size, name in width_name:
        width_categories[name].append(size)
    height_categories = defaultdict(list)
    for size, name in height_name:
        height_categories[name].append(size)
    logger.info(f'{'name':>50} {'count':>10} {'width':>10} {'len':>10} {'height':>10} \n {'-' * 101:>10}')
    for name, stats in sorted(length_categories.items()):
        length_stats: npt.NDArray[np.float32] = np.array(stats)
        width_stats: npt.NDArray[np.float32] = np.array(width_categories[name])
        height_stats: npt.NDArray[np.float32] = np.array(height_categories[name])
        logger.info(f'{name[:50]:>50} {length_stats.shape[0]:>10.2f} {np.mean(length_stats):>5.2f} {np.std(length_stats):>5.2f} {np.mean(width_stats):>5.2f} {np.std(width_stats):>5.2f} {np.mean(height_stats):>5.2f} {np.std(height_stats):>5.2f}')

class Log(Base):
    """
    Information about the log from which the data was extracted.
    """
    __tablename__ = 'log'
    token = Column(sql_types.HexLen8, primary_key=True)
    vehicle_name = Column(String(64))
    date = Column(String(64))
    timestamp = Column(Integer)
    logfile = Column(String(64))
    location = Column(String(64))
    map_version = Column(String(64))
    cameras = relationship('Camera', foreign_keys='Camera.log_token', back_populates='log')
    ego_poses = relationship('EgoPose', foreign_keys='EgoPose.log_token', back_populates='log')
    lidars = relationship('Lidar', foreign_keys='Lidar.log_token', back_populates='log')
    scenes = relationship('Scene', foreign_keys='Scene.log_token', back_populates='log')

    @property
    def _session(self) -> Any:
        """
        Get the underlying session.
        :return: The underlying session.
        """
        return inspect(self).session

    @property
    def images(self) -> List[Image]:
        """
        Returns list of Images contained in the Log.
        :return: The list of Images contained in the log.
        """
        log_images = []
        for camera in self.cameras:
            log_images.extend(camera.images)
        return log_images

    @property
    def lidar_pcs(self) -> List[LidarPc]:
        """
        Returns list of Lidar PCs in the Log.
        :return: The list of Lidar PCs in the log.
        """
        log_lidar_pcs = []
        for lidar in self.lidars:
            log_lidar_pcs.extend(lidar.lidar_pcs)
        return log_lidar_pcs

    @property
    def lidar_boxes(self) -> List[LidarBox]:
        """
        Returns list of Lidar Boxes in the Log.
        :return: The list of Lidar Boxes in the log.
        """
        log_lidar_boxes = []
        for lidar_pc in self.lidar_pcs:
            log_lidar_boxes.extend(lidar_pc.lidar_boxes)
        return log_lidar_boxes

    def __repr__(self) -> str:
        """
        Return the string representation.
        :return: The string representation.
        """
        desc: str = simple_repr(self)
        return desc

@property
def images(self) -> List[Image]:
    """
        Returns list of Images contained in the Log.
        :return: The list of Images contained in the log.
        """
    log_images = []
    for camera in self.cameras:
        log_images.extend(camera.images)
    return log_images

@property
def lidar_pcs(self) -> List[LidarPc]:
    """
        Returns list of Lidar PCs in the Log.
        :return: The list of Lidar PCs in the log.
        """
    log_lidar_pcs = []
    for lidar in self.lidars:
        log_lidar_pcs.extend(lidar.lidar_pcs)
    return log_lidar_pcs

@property
def lidar_boxes(self) -> List[LidarBox]:
    """
        Returns list of Lidar Boxes in the Log.
        :return: The list of Lidar Boxes in the log.
        """
    log_lidar_boxes = []
    for lidar_pc in self.lidar_pcs:
        log_lidar_boxes.extend(lidar_pc.lidar_boxes)
    return log_lidar_boxes

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

def pil_grid(images: List[Image.Image], max_horiz: int) -> Image.Image:
    """
    Automatically creates a mosaic from a list of PIL images.
    :param images: List of images in PIL form.
    :param max_horiz: Maximum number of images in the column.
    :return: Mosaic-like image.
    """
    n_images = len(images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = ([0] * n_horiz, [0] * (n_images // n_horiz))
    for i, im in enumerate(images):
        h, v = (i % n_horiz, i // n_horiz)
        h_sizes[h] = max(h_sizes[h], im.size[0])
        v_sizes[v] = max(v_sizes[v], im.size[1])
    h_sizes, v_sizes = (np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes))
    im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im in enumerate(images):
        im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    return im_grid

def intersection(a: Rectangle, b: Rectangle) -> float:
    """
    Intersection between rectangles.
    :param a: Rectangle 1.
    :param b: Rectangle 2.
    :return: Area of intersection between a and b.
    """
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    if dx >= 0 and dy >= 0:
        return dx * dy
    else:
        return 0

def birdview_corner_angle_mean_distance(a: TwoDimBox, b: TwoDimBox, period: float) -> float:
    """
    Calculates ad-hoc birdsview distance of two 2-d boxes.
    :param a: 2-d box1.
    :param b: 2-d box2.
    :param period: Periodicity for assessing angle difference.
    :return: Birdview distance.
    """
    box_error: npt.NDArray[np.float64] = np.array(a[:4]) - np.array(b[:4])
    yaw_error = angle_diff(a[4], b[4], period)
    avg_abs_error = float(np.mean(np.abs(np.concatenate((box_error, np.array([yaw_error]))))))
    return avg_abs_error

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

def remove_close(self, min_dist: float) -> None:
    """
        Removes points too close within a certain distance from origin from bird view (so dist = sqrt(x^2+y^2)).
        :param min_dist: The distance threshold.
        """
    dist_from_orig = np.linalg.norm(self.points[:2, :], axis=0)
    self.points = self.points[:, dist_from_orig >= min_dist]

def approximate_derivatives_tensor(y: torch.Tensor, x: torch.Tensor, window_length: int=5, poly_order: int=2, deriv_order: int=1) -> torch.Tensor:
    """
    Given a time series [y], and [x], approximate [dy/dx].
    :param y: Input tensor to filter.
    :param x: Time dimension for tensor to filter.
    :param window_length: The size of the window to use.
    :param poly_order: The order of polymonial to use when filtering.
    :deriv_order: The order of derivitave to use when filtering.
    :return: The differentiated tensor.
    """
    _validate_approximate_derivatives_shapes(y, x)
    window_length = min(window_length, x.shape[0])
    if not poly_order < window_length:
        raise ValueError(f'{poly_order} < {window_length} does not hold!')
    dx = torch.diff(x)
    min_increase = float(torch.min(dx).item())
    if min_increase <= 0:
        raise RuntimeError('dx is not monotonically increasing!')
    dx = dx.mean()
    derivative: torch.Tensor = _torch_savgol_filter(y, poly_order=poly_order, window_length=window_length, deriv_order=deriv_order, delta=dx)
    return derivative

def add_polyline_to_scene(scene: Dict[str, Any], polyline: List[StateSE2]) -> None:
    """
    Serialize and append a polyline to the scene.
    :param scene: scene dict.
    :param polyline: The polyline to be added.
    """
    if 'path_info' not in scene.keys():
        scene['path_info'] = []
    scene['path_info'].extend([[pose.x, pose.y, pose.heading] for pose in polyline])

def connect_trimmed_lane_conn_predecessor(lane_coords: Tuple[List[List[List[float]]]], lane_conn: LaneConnector, cross_blp_conns: Dict[str, Tuple[int, int]], distance_threshold: float=0.3) -> List[Tuple[int, int]]:
    """
    Given a specific lane connector, find its predecessor lane and return new connection info. To
                       handle the case where the end points of lane connector or/and the predecissor
                       lane being trimmed, a distance check is performed to make sure the end points
                       of the predecissor lane is close enough to be connected.
    :param: lane_coords: the lane segment cooridnates
    :param lane_conn: a specific lane connector.
    :param cross_blp_conns: Dict recording the map object id as key(str) and corresponding [first segment index,
        last segment index] pair as value (Tuple[int, int]).
    :param distance_threshold: the distance to determine if the end points are close enough to be
        connected in the lane graph.
    :return lane_seg_pred_conns: container recording the connection [from_lane_seg_idx, to_lane_seg_idx] between
        last predecessor segment and first segment of given lane connector.
    """
    lane_seg_pred_conns: List[Tuple[int, int]] = []
    lane_conn_start_seg_idx, lane_conn_end_seg_idx = cross_blp_conns[lane_conn.id]
    incoming_lanes = [incoming_edge for incoming_edge in lane_conn.incoming_edges if isinstance(incoming_edge, Lane)]
    for incoming_lane in incoming_lanes:
        lane_id = incoming_lane.id
        if lane_id in cross_blp_conns.keys():
            predecessor_start_idx, predecessor_end_idx = cross_blp_conns[lane_id]
            if np.linalg.norm(np.array(lane_coords[predecessor_end_idx][1]) - np.array(lane_coords[lane_conn_start_seg_idx][0])) < distance_threshold:
                lane_seg_pred_conns.append((predecessor_end_idx, lane_conn_start_seg_idx))
    return lane_seg_pred_conns

def connect_trimmed_lane_conn_successor(lane_coords: Tuple[List[List[List[float]]]], lane_conn: LaneConnector, cross_blp_conns: Dict[str, Tuple[int, int]], distance_threshold: float=0.3) -> List[Tuple[int, int]]:
    """
    Given a specific lane connector, find its successor lane and return new connection info. To
                       handle the case where the end points of lane connector or/and the predecissor
                       lane being trimmed, a distance check is performed to make sure the end points
                       of the predecissor lane is close enough to be connected.
    :param: lane_coords: the lane segment cooridnates
    :param lane_conn: a specific lane connector.
    :param cross_blp_conns: Dict recording the map object id as key(str) and corresponding [first segment index,
        last segment index] pair as value (Tuple[int, int]).
    :param distance_threshold: the distance to determine if the end points are close enough to be
        connected in the lane graph.
    :return lane_seg_suc_conns: container recording the connection [from_lane_seg_idx, to_lane_seg_idx] between
        last segment of given lane connector and first successor lane segment.
    """
    lane_seg_suc_conns: List[Tuple[int, int]] = []
    lane_conn_start_seg_idx, lane_conn_end_seg_idx = cross_blp_conns[lane_conn.id]
    outgoing_lanes = [outgoing_edge for outgoing_edge in lane_conn.outgoing_edges if isinstance(outgoing_edge, Lane)]
    for outgoing_lane in outgoing_lanes:
        lane_id = outgoing_lane.id
        if lane_id in cross_blp_conns.keys():
            successor_start_idx, successor_end_seg_idx = cross_blp_conns[lane_id]
            if np.linalg.norm(np.array(lane_coords[lane_conn_end_seg_idx][1]) - np.array(lane_coords[successor_start_idx][0])) < distance_threshold:
                lane_seg_suc_conns.append((lane_conn_end_seg_idx, successor_start_idx))
    return lane_seg_suc_conns

def estimate_curvature_along_path(path: geom.LineString, arc_length: float, distance_for_curvature_estimation: float) -> float:
    """
    Estimate curvature along a path at arc_length from origin.
    :param path: LineString creating a continuous path.
    :param arc_length: [m] distance from origin of the path.
    :param distance_for_curvature_estimation: [m] the distance used to construct 3 points.
    :return estimated curvature at point arc_length.
    """
    assert 0 <= arc_length <= path.length
    if path.length < 2.0 * distance_for_curvature_estimation:
        first_arch_length = 0.0
        second_arc_length = path.length / 2.0
        third_arc_length = path.length
    elif arc_length - distance_for_curvature_estimation < 0.0:
        first_arch_length = 0.0
        second_arc_length = distance_for_curvature_estimation
        third_arc_length = 2.0 * distance_for_curvature_estimation
    elif arc_length + distance_for_curvature_estimation > path.length:
        first_arch_length = path.length - 2.0 * distance_for_curvature_estimation
        second_arc_length = path.length - distance_for_curvature_estimation
        third_arc_length = path.length
    else:
        first_arch_length = arc_length - distance_for_curvature_estimation
        second_arc_length = arc_length
        third_arc_length = arc_length + distance_for_curvature_estimation
    first_arch_position = path.interpolate(first_arch_length)
    second_arch_position = path.interpolate(second_arc_length)
    third_arch_position = path.interpolate(third_arc_length)
    return compute_curvature(first_arch_position, second_arch_position, third_arch_position)

class NuPlanPolylineMapObject(PolylineMapObject):
    """
    NuPlanMap implementation of Polyline Map Object.
    """

    def __init__(self, polyline: Series, distance_for_curvature_estimation: float=2.0, distance_for_heading_estimation: float=0.5):
        """
        Constructor of polyline map layer.
        :param polyline: a pandas series representing the polyline.
        :param distance_for_curvature_estimation: [m] distance of the split between 3-points curvature estimation.
        :param distance_for_heading_estimation: [m] distance between two points on the polyline to calculate
                                                    the relative heading.
        """
        super().__init__(polyline['fid'])
        self._polyline: LineString = polyline.geometry
        assert self._polyline.length > 0.0, 'The length of the polyline has to be greater than 0!'
        self._distance_for_curvature_estimation = distance_for_curvature_estimation
        self._distance_for_heading_estimation = distance_for_heading_estimation

    @property
    def linestring(self) -> LineString:
        """Inherited from superclass."""
        return self._polyline

    @property
    def length(self) -> float:
        """Inherited from superclass."""
        return float(self._polyline.length)

    @cached_property
    def discrete_path(self) -> List[StateSE2]:
        """Inherited from superclass."""
        return cast(List[StateSE2], extract_discrete_polyline(self._polyline))

    def get_nearest_arc_length_from_position(self, point: Point2D) -> float:
        """Inherited from superclass."""
        return self._polyline.project(Point(point.x, point.y))

    def get_nearest_pose_from_position(self, point: Point2D) -> StateSE2:
        """Inherited from superclass."""
        arc_length = self.get_nearest_arc_length_from_position(point)
        state1 = self._polyline.interpolate(arc_length)
        state2 = self._polyline.interpolate(arc_length + self._distance_for_heading_estimation)
        if state1 == state2:
            state2 = self._polyline.interpolate(arc_length - self._distance_for_heading_estimation)
            heading = _get_heading(state2, state1)
        else:
            heading = _get_heading(state1, state2)
        return StateSE2(state1.x, state1.y, heading)

    def get_curvature_at_arc_length(self, arc_length: float) -> float:
        """Inherited from superclass."""
        curvature = estimate_curvature_along_path(self._polyline, arc_length, self._distance_for_curvature_estimation)
        return float(curvature)

def get_nearest_pose_from_position(self, point: Point2D) -> StateSE2:
    """Inherited from superclass."""
    arc_length = self.get_nearest_arc_length_from_position(point)
    state1 = self._polyline.interpolate(arc_length)
    state2 = self._polyline.interpolate(arc_length + self._distance_for_heading_estimation)
    if state1 == state2:
        state2 = self._polyline.interpolate(arc_length - self._distance_for_heading_estimation)
        heading = _get_heading(state2, state1)
    else:
        heading = _get_heading(state1, state2)
    return StateSE2(state1.x, state1.y, heading)

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

def to_split_state(self) -> SplitState:
    """Inherited, see superclass."""
    linear_states = [self.time_us, self.rear_axle.x, self.rear_axle.y, self.dynamic_car_state.rear_axle_velocity_2d.x, self.dynamic_car_state.rear_axle_velocity_2d.y, self.dynamic_car_state.rear_axle_acceleration_2d.x, self.dynamic_car_state.rear_axle_acceleration_2d.y, self.tire_steering_angle]
    angular_states = [self.rear_axle.heading]
    fixed_state = [self.car_footprint.vehicle_parameters]
    return SplitState(linear_states, angular_states, fixed_state)

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

def to_split_state(self) -> SplitState:
    """Inherited, see superclass."""
    linear_states = [self.time_point.time_us, self._oriented_box.center.x, self._oriented_box.center.y, self._velocity.x if self._velocity is not None else None, self._velocity.y if self._velocity is not None else None]
    angular_states = [self._oriented_box.center.heading]
    fixed_state = [self._oriented_box.width, self._oriented_box.length, self._oriented_box.height]
    return SplitState(linear_states, angular_states, fixed_state)

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

def test_interpolate_real_value(self) -> None:
    """Interpolates multiple state"""
    states: npt.NDArray[np.float64] = np.array([1, 3])
    angular_states = [[3.0, -2.0], [-3.0, 2.0]]
    interpolator = AngularInterpolator(states, angular_states)
    np.testing.assert_allclose(np.array([-np.pi, -np.pi]), interpolator.interpolate(2))

def get_max_size_of_arguments(*item_lists: Iterable[List[Any]]) -> int:
    """
    Find the argument with most elements.
        e.g. [db, [arg1, arg2] -> 2.
    :param item_lists: arguments where some of the arguments is a list.
    :return: size of largest list.
    """
    lengths = [len(items) for items in item_lists if isinstance(items, list)]
    if len(list(set(lengths))) > 1:
        raise RuntimeError(f'There exists lists with different element size = {lengths}!')
    return max(lengths) if len(lengths) != 0 else 1

@dataclass(frozen=True)
class PredictorReport:
    """
    Information about predictor runtimes, etc. to store to disk.
    """
    compute_predictions_runtimes: List[float]

    def compute_summary_statistics(self) -> Dict[str, float]:
        """
        Compute summary statistics over report fields.
        :return: dictionary containing summary statistics of each field.
        """
        summary = {}
        for field in fields(self):
            attr_value = getattr(self, field.name)
            summary[f'{field.name}_mean'] = np.mean(attr_value)
            summary[f'{field.name}_median'] = np.median(attr_value)
            summary[f'{field.name}_95_percentile'] = np.percentile(attr_value, 95)
            summary[f'{field.name}_std'] = np.std(attr_value)
        return summary

def compute_summary_statistics(self) -> Dict[str, float]:
    """
        Compute summary statistics over report fields.
        :return: dictionary containing summary statistics of each field.
        """
    summary = {}
    for field in fields(self):
        attr_value = getattr(self, field.name)
        summary[f'{field.name}_mean'] = np.mean(attr_value)
        summary[f'{field.name}_median'] = np.median(attr_value)
        summary[f'{field.name}_95_percentile'] = np.percentile(attr_value, 95)
        summary[f'{field.name}_std'] = np.std(attr_value)
    return summary

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

def _clip_steering_angle(self, steering_angle: float) -> float:
    """
        Used to clip the steering angle state within bounds.
        :param steering_angle: [rad] A steering angle (scalar) to clip.
        :return: [rad] The clipped steering angle.
        """
    steering_angle_sign = 1.0 if steering_angle >= 0 else -1.0
    steering_angle = steering_angle_sign * min(abs(steering_angle), self._solver_params.max_steering_angle)
    return steering_angle

@dataclass(frozen=True)
class PlannerReport:
    """
    Information about planner runtimes, etc. to store to disk.
    """
    compute_trajectory_runtimes: List[float]

    def compute_summary_statistics(self) -> Dict[str, float]:
        """
        Compute summary statistics over report fields.
        :return: dictionary containing summary statistics of each field.
        """
        summary = {}
        for field in fields(self):
            attr_value = getattr(self, field.name)
            summary[f'{field.name}_mean'] = np.mean(attr_value)
            summary[f'{field.name}_median'] = np.median(attr_value)
            summary[f'{field.name}_std'] = np.std(attr_value)
        return summary

def compute_summary_statistics(self) -> Dict[str, float]:
    """
        Compute summary statistics over report fields.
        :return: dictionary containing summary statistics of each field.
        """
    summary = {}
    for field in fields(self):
        attr_value = getattr(self, field.name)
        summary[f'{field.name}_mean'] = np.mean(attr_value)
        summary[f'{field.name}_median'] = np.median(attr_value)
        summary[f'{field.name}_std'] = np.std(attr_value)
    return summary

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

def test_metric_callback_init(self) -> None:
    """
        Tests if all the properties are set to the expected values in constructor.
        """
    metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
    self.assertEqual(metric_file_callback._metric_file_output_path, self.path)
    self.assertEqual(metric_file_callback._scenario_metric_paths, [self.path])

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

class IDMPolicy:
    """
    An agent policy that describes the agent's behaviour w.r.t to a lead agent. The policy only controls the
    longitudinal states (progress, velocity) of the agent. This longitudinal states are used to propagate the agent
    along a given path.
    """

    def __init__(self, target_velocity: float, min_gap_to_lead_agent: float, headway_time: float, accel_max: float, decel_max: float):
        """
        Constructor for IDMPolicy

        :param target_velocity: Desired velocity in free traffic [m/s]
        :param min_gap_to_lead_agent: Minimum relative distance to lead vehicle [m]
        :param headway_time: Desired time headway. The minimum possible time to the vehicle in front [s]
        :param accel_max: maximum acceleration [m/s^2]
        :param decel_max: maximum deceleration (positive value) [m/s^2]
        """
        self._target_velocity = target_velocity
        self._min_gap_to_lead_agent = min_gap_to_lead_agent
        self._headway_time = headway_time
        self._accel_max = accel_max
        self._decel_max = decel_max

    @property
    def idm_params(self) -> List[float]:
        """Returns the policy parameters as a list"""
        return [self._target_velocity, self._min_gap_to_lead_agent, self._headway_time, self._accel_max, self._decel_max]

    @property
    def target_velocity(self) -> float:
        """
        The policy's desired velocity in free traffic [m/s]
        :return: target velocity
        """
        return self._target_velocity

    @target_velocity.setter
    def target_velocity(self, target_velocity: float) -> None:
        """
        Sets the policy's desired velocity in free traffic [m/s]
        """
        self._target_velocity = target_velocity
        assert target_velocity > 0, f'The target velocity must be greater than 0! {target_velocity} > 0'

    @property
    def headway_time(self) -> float:
        """
        The policy's minimum possible time to the vehicle in front [s]
        :return: Desired time headway
        """
        return self._headway_time

    @property
    def decel_max(self) -> float:
        """
        The policy's maximum deceleration (positive value) [m/s^2]
        :return: Maximum deceleration
        """
        return self._decel_max

    @staticmethod
    def idm_model(time_points: List[float], state_variables: List[float], lead_agent: List[float], params: List[float]) -> List[Any]:
        """
        Defines the differential equations for IDM.

        :param state_variables: vector of the state variables:
                  state_variables = [x_agent: progress,
                                     v_agent: velocity]
        :param time_points: time A sequence of time points for which to solve for the state variables
        :param lead_agent: vector of the state variables for the lead vehicle:
                  lead_agent = [x_lead: progress,
                                v_lead: velocity,
                                l_r_lead: half length of the leading vehicle]
        :param params:vector of the parameters:
                  params = [target_velocity: desired velocity in free traffic,
                            min_gap_to_lead_agent: minimum relative distance to lead vehicle,
                            headway_time: desired time headway. The minimum possible time to the vehicle in front,
                            accel_max: maximum acceleration,
                            decel_max: maximum deceleration (positive value)]

        :return: system of differential equations
        """
        x_agent, v_agent = state_variables
        x_lead, v_lead, l_r_lead = lead_agent
        target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max = params
        acceleration_exponent = 4
        s_star = min_gap_to_lead_agent + v_agent * headway_time + v_agent * (v_agent - v_lead) / (2 * sqrt(accel_max * decel_max))
        s_alpha = max(x_lead - x_agent - l_r_lead, min_gap_to_lead_agent)
        x_dot = v_agent
        v_agent_dot = accel_max * (1 - (v_agent / target_velocity) ** acceleration_exponent - (s_star / s_alpha) ** 2)
        return [x_dot, v_agent_dot]

    def solve_forward_euler_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float) -> IDMAgentState:
        """
        Solves Solves an initial value problem for a system of ODEs using forward euler.
        This has the benefit of being differentiable

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :return: solution to the differential equations
        """
        params = self.idm_params
        x_dot, v_agent_dot = self.idm_model([], agent.to_array(), lead_agent.to_array(), params)
        return IDMAgentState(agent.progress + sampling_time * x_dot, agent.velocity + sampling_time * min(max(-self._decel_max, v_agent_dot), self._accel_max))

    def solve_odeint_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float, solve_points: int=10) -> IDMAgentState:
        """
        Solves an initial value problem for a system of ODEs using scipy odeint

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :param solve_points: number of points for temporal resolution
        :return: solution to the differential equations
        """
        t = np.linspace(0, sampling_time, solve_points)
        solution = odeint(self.idm_model, agent.to_array(), t, args=(lead_agent.to_array(), self.idm_params), tfirst=True)
        return IDMAgentState(solution[-1][0], solution[-1][1])

    def solve_ivp_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float) -> IDMAgentState:
        """
        Solves an initial value problem for a system of ODEs using scipy RK45

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :return: solution to the differential equations
        """
        t = (0, sampling_time)
        solution = solve_ivp(self.idm_model, t, agent.to_array(), args=(lead_agent.to_array(), self.idm_params), method='RK45')
        return IDMAgentState(solution.y[0][-1], solution.y[1][-1])

@staticmethod
def idm_model(time_points: List[float], state_variables: List[float], lead_agent: List[float], params: List[float]) -> List[Any]:
    """
        Defines the differential equations for IDM.

        :param state_variables: vector of the state variables:
                  state_variables = [x_agent: progress,
                                     v_agent: velocity]
        :param time_points: time A sequence of time points for which to solve for the state variables
        :param lead_agent: vector of the state variables for the lead vehicle:
                  lead_agent = [x_lead: progress,
                                v_lead: velocity,
                                l_r_lead: half length of the leading vehicle]
        :param params:vector of the parameters:
                  params = [target_velocity: desired velocity in free traffic,
                            min_gap_to_lead_agent: minimum relative distance to lead vehicle,
                            headway_time: desired time headway. The minimum possible time to the vehicle in front,
                            accel_max: maximum acceleration,
                            decel_max: maximum deceleration (positive value)]

        :return: system of differential equations
        """
    x_agent, v_agent = state_variables
    x_lead, v_lead, l_r_lead = lead_agent
    target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max = params
    acceleration_exponent = 4
    s_star = min_gap_to_lead_agent + v_agent * headway_time + v_agent * (v_agent - v_lead) / (2 * sqrt(accel_max * decel_max))
    s_alpha = max(x_lead - x_agent - l_r_lead, min_gap_to_lead_agent)
    x_dot = v_agent
    v_agent_dot = accel_max * (1 - (v_agent / target_velocity) ** acceleration_exponent - (s_star / s_alpha) ** 2)
    return [x_dot, v_agent_dot]

def solve_forward_euler_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float) -> IDMAgentState:
    """
        Solves Solves an initial value problem for a system of ODEs using forward euler.
        This has the benefit of being differentiable

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :return: solution to the differential equations
        """
    params = self.idm_params
    x_dot, v_agent_dot = self.idm_model([], agent.to_array(), lead_agent.to_array(), params)
    return IDMAgentState(agent.progress + sampling_time * x_dot, agent.velocity + sampling_time * min(max(-self._decel_max, v_agent_dot), self._accel_max))

def solve_odeint_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float, solve_points: int=10) -> IDMAgentState:
    """
        Solves an initial value problem for a system of ODEs using scipy odeint

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :param solve_points: number of points for temporal resolution
        :return: solution to the differential equations
        """
    t = np.linspace(0, sampling_time, solve_points)
    solution = odeint(self.idm_model, agent.to_array(), t, args=(lead_agent.to_array(), self.idm_params), tfirst=True)
    return IDMAgentState(solution[-1][0], solution[-1][1])

def solve_ivp_idm_policy(self, agent: IDMAgentState, lead_agent: IDMLeadAgentState, sampling_time: float) -> IDMAgentState:
    """
        Solves an initial value problem for a system of ODEs using scipy RK45

        :param agent: the agent of interest
        :param lead_agent: the lead vehicle
        :param sampling_time: interval of integration
        :return: solution to the differential equations
        """
    t = (0, sampling_time)
    solution = solve_ivp(self.idm_model, t, agent.to_array(), args=(lead_agent.to_array(), self.idm_params), method='RK45')
    return IDMAgentState(solution.y[0][-1], solution.y[1][-1])

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

def test_idm_model(self):
    """Tests the model correctness"""
    model = self.idm.idm_model([], self.agent.to_array(), self.lead_agent.to_array(), self.idm.idm_params)
    self.assertEqual(3, model[0])
    self.assertAlmostEqual(-1.073366, model[1])

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

class InterpolatedPath(AbstractPath):
    """A path that is interpolated from a list of points."""

    def __init__(self, path: List[ProgressStateSE2]):
        """
        Constructor of InterpolatedPath.

        :param path: List of states creating a path.
            The path has to have at least 2 elements, otherwise it is considered invalid and the class will raise.
        """
        assert len(path) > 1, 'Path has to has more than 1 element!'
        self._path = path
        progress = [point.progress for point in self._path]
        linear_states = []
        angular_states = []
        for point in path:
            linear_states.append([point.progress, point.x, point.y])
            angular_states.append([point.heading])
        linear_states = np.array(linear_states, dtype='float64')
        angular_states = np.array(angular_states, dtype='float64')
        self._function_interp_linear = sp_interp.interp1d(progress, linear_states, axis=0)
        self._angular_interpolator = AngularInterpolator(progress, angular_states)

    def get_start_progress(self) -> float:
        """Inherited, see superclass."""
        return self._path[0].progress

    def get_end_progress(self) -> float:
        """Inherited, see superclass."""
        return self._path[-1].progress

    def get_state_at_progress(self, progress: float) -> ProgressStateSE2:
        """Inherited, see superclass."""
        self._assert_progress(progress)
        linear_states = list(self._function_interp_linear(progress))
        angular_states = list(self._angular_interpolator.interpolate(progress))
        return ProgressStateSE2.deserialize(linear_states + angular_states)

    def get_state_at_progresses(self, progresses: List[float]) -> List[ProgressStateSE2]:
        """Inherited, see superclass."""
        self._assert_progress(min(progresses))
        self._assert_progress(max(progresses))
        linear_states_batch = self._function_interp_linear(progresses)
        angular_states_batch = self._angular_interpolator.interpolate(progresses)
        return [ProgressStateSE2.deserialize(list(linear_states) + list(angular_states)) for linear_states, angular_states in zip(linear_states_batch, angular_states_batch)]

    def get_sampled_path(self) -> List[ProgressStateSE2]:
        """Inherited, see superclass."""
        return self._path

    def _assert_progress(self, progress: float) -> None:
        """Check if queried progress is within bounds"""
        start_progress = self.get_start_progress()
        end_progress = self.get_end_progress()
        assert start_progress <= progress <= end_progress, f'Progress exceeds path! {start_progress} <= {progress} <= {end_progress}'

def get_state_at_progress(self, progress: float) -> ProgressStateSE2:
    """Inherited, see superclass."""
    self._assert_progress(progress)
    linear_states = list(self._function_interp_linear(progress))
    angular_states = list(self._angular_interpolator.interpolate(progress))
    return ProgressStateSE2.deserialize(linear_states + angular_states)

def get_state_at_progresses(self, progresses: List[float]) -> List[ProgressStateSE2]:
    """Inherited, see superclass."""
    self._assert_progress(min(progresses))
    self._assert_progress(max(progresses))
    linear_states_batch = self._function_interp_linear(progresses)
    angular_states_batch = self._angular_interpolator.interpolate(progresses)
    return [ProgressStateSE2.deserialize(list(linear_states) + list(angular_states)) for linear_states, angular_states in zip(linear_states_batch, angular_states_batch)]

class TimingCallback(AbstractCallback):
    """Callback to log timing information to Tensorboard as the simulation runs."""

    def __init__(self, writer: SummaryWriter):
        """
        Constructor for TimingCallback.
        :param writer: handler for writing to tensorboard.
        """
        self._writer = writer
        self._scenarios_captured: Dict[str, Any] = defaultdict(None)
        self._step_start: Optional[float] = None
        self._simulation_start: Optional[float] = None
        self._planner_start: Optional[float] = None
        self._step_duration: List[float] = []
        self._planner_step_duration: List[float] = []
        self._tensorboard_global_step = 0

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_planner_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        self._planner_start = self._get_time()

    def on_planner_end(self, setup: SimulationSetup, planner: AbstractPlanner, trajectory: AbstractTrajectory) -> None:
        """Inherited, see superclass."""
        assert self._planner_start, 'Start time has to be set: on_planner_end!'
        self._planner_step_duration.append(self._get_time() - self._planner_start)

    def on_simulation_start(self, setup: SimulationSetup) -> None:
        """Inherited, see superclass."""
        self._scenarios_captured[setup.scenario.token] = None
        self._simulation_start = self._get_time()

    def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
        """Inherited, see superclass."""
        assert self._simulation_start, 'Start time has to be set: on_simulation_end!'
        elapsed_time = self._get_time() - self._simulation_start
        timings = {'simulation_elapsed_time': elapsed_time, 'mean_step_time': np.mean(self._step_duration), 'max_step_time': np.max(self._step_duration), 'max_planner_step_time': np.max(self._planner_step_duration), 'mean_planner_step_time': np.mean(self._planner_step_duration)}
        step = self._tensorboard_global_step
        self._writer.add_scalar('simulation_elapsed_time', timings['simulation_elapsed_time'], step)
        self._writer.add_scalar('mean_step_time', timings['mean_step_time'], step)
        self._writer.add_scalar('max_step_time', timings['max_step_time'], step)
        self._writer.add_scalar('max_planner_step_time', timings['max_planner_step_time'], step)
        self._writer.add_scalar('mean_planner_step_time', timings['mean_planner_step_time'], step)
        self._tensorboard_global_step += 1
        self._scenarios_captured[setup.scenario.token] = timings
        self._step_duration = []
        self._planner_step_duration = []

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        self._step_start = self._get_time()

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """Inherited, see superclass."""
        assert self._step_start, 'Start time has to be set: on_step_end!'
        elapsed_time = self._get_time() - self._step_start
        self._step_duration.append(elapsed_time)

    def _get_time(self) -> float:
        return time.perf_counter()

def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """Inherited, see superclass."""
    assert self._simulation_start, 'Start time has to be set: on_simulation_end!'
    elapsed_time = self._get_time() - self._simulation_start
    timings = {'simulation_elapsed_time': elapsed_time, 'mean_step_time': np.mean(self._step_duration), 'max_step_time': np.max(self._step_duration), 'max_planner_step_time': np.max(self._planner_step_duration), 'mean_planner_step_time': np.mean(self._planner_step_duration)}
    step = self._tensorboard_global_step
    self._writer.add_scalar('simulation_elapsed_time', timings['simulation_elapsed_time'], step)
    self._writer.add_scalar('mean_step_time', timings['mean_step_time'], step)
    self._writer.add_scalar('max_step_time', timings['max_step_time'], step)
    self._writer.add_scalar('max_planner_step_time', timings['max_planner_step_time'], step)
    self._writer.add_scalar('mean_planner_step_time', timings['mean_planner_step_time'], step)
    self._tensorboard_global_step += 1
    self._scenarios_captured[setup.scenario.token] = timings
    self._step_duration = []
    self._planner_step_duration = []

class AgentsAverageDisplacementError(AbstractTrainingMetric):
    """
    Metric representing the displacement L2 error averaged from all poses of all agents' trajectory.
    """

    def __init__(self, name: str='agents_avg_displacement_error') -> None:
        """
        Initializes the class.

        :param name: the name of the metric (used in logger)
        """
        self._name = name

    def name(self) -> str:
        """
        Name of the metric
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['agents_trajectory']

    def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
        """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
        predicted_agents: AgentsTrajectories = predictions['agents_trajectory']
        target_agents: AgentsTrajectories = targets['agents_trajectory']
        batch_size = predicted_agents.batch_size
        error = torch.mean(torch.tensor([torch.norm(predicted_agents.xy[sample_idx] - target_agents.xy[sample_idx], dim=-1).mean() for sample_idx in range(batch_size)]))
        return error

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_agents: AgentsTrajectories = predictions['agents_trajectory']
    target_agents: AgentsTrajectories = targets['agents_trajectory']
    batch_size = predicted_agents.batch_size
    error = torch.mean(torch.tensor([torch.norm(predicted_agents.xy[sample_idx] - target_agents.xy[sample_idx], dim=-1).mean() for sample_idx in range(batch_size)]))
    return error

class AgentsFinalDisplacementError(AbstractTrainingMetric):
    """
    Metric representing the displacement L2 error from the final pose of all agents trajectory.
    """

    def __init__(self, name: str='agents_final_displacement_error') -> None:
        """
        Initializes the class.

        :param name: the name of the metric (used in logger)
        """
        self._name = name

    def name(self) -> str:
        """
        Name of the metric
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['agents_trajectory']

    def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
        """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
        predicted_agents: AgentsTrajectories = predictions['agents_trajectory']
        target_agents: AgentsTrajectories = targets['agents_trajectory']
        batch_size = predicted_agents.batch_size
        error = torch.mean(torch.tensor([torch.norm(predicted_agents.terminal_xy[sample_idx] - target_agents.terminal_xy[sample_idx], dim=-1).mean() for sample_idx in range(batch_size)]))
        return error

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_agents: AgentsTrajectories = predictions['agents_trajectory']
    target_agents: AgentsTrajectories = targets['agents_trajectory']
    batch_size = predicted_agents.batch_size
    error = torch.mean(torch.tensor([torch.norm(predicted_agents.terminal_xy[sample_idx] - target_agents.terminal_xy[sample_idx], dim=-1).mean() for sample_idx in range(batch_size)]))
    return error

class AverageDisplacementError(AbstractTrainingMetric):
    """
    Metric representing the displacement L2 error averaged from all poses of a trajectory.
    """

    def __init__(self, name: str='avg_displacement_error') -> None:
        """
        Initializes the class.

        :param name: the name of the metric (used in logger)
        """
        self._name = name

    def name(self) -> str:
        """
        Name of the metric
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['trajectory']

    def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
        """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
        predicted_trajectory: Trajectory = predictions['trajectory']
        targets_trajectory: Trajectory = targets['trajectory']
        return torch.norm(predicted_trajectory.xy - targets_trajectory.xy, dim=-1).mean()

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_trajectory: Trajectory = predictions['trajectory']
    targets_trajectory: Trajectory = targets['trajectory']
    return torch.norm(predicted_trajectory.xy - targets_trajectory.xy, dim=-1).mean()

class FinalDisplacementError(AbstractTrainingMetric):
    """
    Metric representing the displacement L2 error from the final pose of a trajectory.
    """

    def __init__(self, name: str='final_displacement_error') -> None:
        """
        Initializes the class.

        :param name: the name of the metric (used in logger)
        """
        self._name = name

    def name(self) -> str:
        """
        Name of the metric
        """
        return self._name

    def get_list_of_required_target_types(self) -> List[str]:
        """Implemented. See interface."""
        return ['trajectory']

    def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
        """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
        predicted_trajectory: Trajectory = predictions['trajectory']
        targets_trajectory: Trajectory = targets['trajectory']
        return torch.norm(predicted_trajectory.terminal_position - targets_trajectory.terminal_position, dim=-1).mean()

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_trajectory: Trajectory = predictions['trajectory']
    targets_trajectory: Trajectory = targets['trajectory']
    return torch.norm(predicted_trajectory.terminal_position - targets_trajectory.terminal_position, dim=-1).mean()

def aggregate_objectives(objectives: Dict[str, torch.Tensor], agg_mode: str) -> torch.Tensor:
    """
    Aggregates all computed objectives in a single scalar loss tensor used for backpropagation.

    :param objectives: dictionary of objective names and values
    :param agg_mode: how to aggregate multiple objectives. [mean, sum, max]
    :return: scalar loss tensor
    """
    if agg_mode == 'mean':
        return torch.stack(list(objectives.values())).mean()
    elif agg_mode == 'sum':
        return torch.stack(list(objectives.values())).sum()
    elif agg_mode == 'max':
        return torch.stack(list(objectives.values())).max()
    else:
        raise ValueError("agg_mode should be one of 'mean', 'sum', and 'max'.")

class LocalMLP(nn.Module):
    """
    A Local 1-layer MLP.
    Copied from L5Kit's implementation `LocalMLP`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/local_graph.py.
    Changes:
        1. Change input & output description
    """

    def __init__(self, dim_in: int, use_norm: bool=True):
        """
        Constructs LocalMLP.
        :param dim_in: Input feature size.
        :param use_norm: Whether to apply layer norm, defaults to True.
        """
        super().__init__()
        self.linear = nn.Linear(dim_in, dim_in, bias=not use_norm)
        self.use_norm = use_norm
        if use_norm:
            self.norm = nn.LayerNorm(dim_in)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        :param x: Input tensor (..., dim_in).
        :return: Output tensor (..., dim_in).
        """
        x = self.linear(x)
        if hasattr(self, 'norm'):
            x = self.norm(x)
        x = F.relu(x, inplace=True)
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    """
        Forward of the module.
        :param x: Input tensor (..., dim_in).
        :return: Output tensor (..., dim_in).
        """
    x = self.linear(x)
    if hasattr(self, 'norm'):
        x = self.norm(x)
    x = F.relu(x, inplace=True)
    return x

class MLP(nn.Module):
    """
    Copied from L5Kit's implementation `MLP`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/global_graph.py.
    Changes:
        1. Add input & output description for `__init__`, `reset_parameters`, `forward`
        2. Change variable name `h` to `hidden_dims` in `__init__`
        3. Change variable name `i` to `layer_idx` in `forward`

    Very simple multi-layer perceptron (also called FFN)
    """

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, num_layers: int):
        """
        Constructs MLP.
        :param input_dim: Input feature size.
        :param hidden_dim: Hidden layer size.
        :paran output_dim: Output feature size.
        :param num_layers: Number of model layers.
        """
        super().__init__()
        self.num_layers = num_layers
        hidden_dims = [hidden_dim] * (num_layers - 1)
        self.layers = nn.ModuleList((nn.Linear(n_in, n_out) for n_in, n_out in zip([input_dim] + hidden_dims, hidden_dims + [output_dim])))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        """
        Re-initialize layer parameters.
        """
        for layer in self.layers.children():
            nn.init.zeros_(layer.bias)
            nn.init.kaiming_normal_(layer.weight, nonlinearity='relu')

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        :param x: Input tensor.
        :return: Output tensor.
        """
        for layer_idx, layer in enumerate(self.layers):
            x = F.relu(layer(x)) if layer_idx < self.num_layers - 1 else layer(x)
        return x

def forward(self, x: torch.Tensor) -> torch.Tensor:
    """
        Forward of the module.
        :param x: Input tensor.
        :return: Output tensor.
        """
    for layer_idx, layer in enumerate(self.layers):
        x = F.relu(layer(x)) if layer_idx < self.num_layers - 1 else layer(x)
    return x

class LocalSubGraphLayer(nn.Module):
    """
    Copied from L5Kit's implementation `LocalSubGraphLayer`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/local_graph.py.
    Changes:
        1. Change input & output description
    """

    def __init__(self, dim_in: int, dim_out: int) -> None:
        """
        Constructs local subgraph layer.
        :param dim_in: Input feat size.
        :param dim_out: Output feat size.
        """
        super(LocalSubGraphLayer, self).__init__()
        self.mlp = LocalMLP(dim_in)
        self.linear_remap = nn.Linear(dim_in * 2, dim_out)

    def forward(self, x: torch.Tensor, invalid_mask: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        :param x: Input tensor [num_elements, num_points, dim_in].
        :param invalid_mask: Invalid mask for x [batch_size, num_elements, num_points].
        :return: Output tensor [num_elements, num_points, dim_out].
        """
        _, num_points, _ = x.shape
        x = self.mlp(x)
        masked_x = x.masked_fill(invalid_mask[..., None] > 0, float('-inf'))
        x_agg = masked_x.max(dim=1, keepdim=True).values
        x_agg = x_agg.repeat(1, num_points, 1)
        x = torch.cat([x, x_agg], dim=-1)
        x = self.linear_remap(x)
        return x

def forward(self, x: torch.Tensor, invalid_mask: torch.Tensor) -> torch.Tensor:
    """
        Forward of the module.
        :param x: Input tensor [num_elements, num_points, dim_in].
        :param invalid_mask: Invalid mask for x [batch_size, num_elements, num_points].
        :return: Output tensor [num_elements, num_points, dim_out].
        """
    _, num_points, _ = x.shape
    x = self.mlp(x)
    masked_x = x.masked_fill(invalid_mask[..., None] > 0, float('-inf'))
    x_agg = masked_x.max(dim=1, keepdim=True).values
    x_agg = x_agg.repeat(1, num_points, 1)
    x = torch.cat([x, x_agg], dim=-1)
    x = self.linear_remap(x)
    return x

class LocalSubGraph(nn.Module):
    """
    Copied from L5Kit's implementation `LocalSubGraph`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/local_graph.py.
    Changes:
        1. Change input & output description

    PointNet-like local subgraph - implemented as a collection of local graph layers.
    """

    def __init__(self, num_layers: int, dim_in: int) -> None:
        """
        :param num_layers: Number of LocalSubGraphLayers.
        :param dim_in: Input, hidden, output dim for features.
        """
        super(LocalSubGraph, self).__init__()
        assert num_layers > 0
        self.layers = nn.ModuleList()
        self.dim_in = dim_in
        for _ in range(num_layers):
            self.layers.append(LocalSubGraphLayer(dim_in, dim_in))

    def forward(self, x: torch.Tensor, invalid_mask: torch.Tensor, pos_enc: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        - Add positional encoding
        - Forward to layers
        - Aggregates using max
        (calculates a feature descriptor per element - reduces over points)
        :param x: Input tensor [batch_size, num_elements, num_points, dim_in].
        :param invalid_mask: Invalid mask for x [batch_size, num_elements, num_points].
        :param pos_enc: Positional_encoding for x.
        :return: Output tensor [batch_size, num_elements, num_points, dim_in].
        """
        batch_size, num_elements, num_points, dim_in = x.shape
        x += pos_enc
        x_flat = x.view(-1, num_points, dim_in)
        invalid_mask_flat = invalid_mask.view(-1, num_points)
        valid_polys = ~invalid_mask.all(-1).flatten()
        x_to_process = x_flat[valid_polys]
        mask_to_process = invalid_mask_flat[valid_polys]
        for layer in self.layers:
            x_to_process = layer(x_to_process, mask_to_process)
        x_to_process = x_to_process.masked_fill(mask_to_process[..., None] > 0, float('-inf'))
        x_to_process = torch.max(x_to_process, dim=1).values
        x = torch.zeros_like(x_flat[:, 0])
        x[valid_polys] = x_to_process
        x = x.view(batch_size, num_elements, self.dim_in)
        return x

def forward(self, x: torch.Tensor, invalid_mask: torch.Tensor, pos_enc: torch.Tensor) -> torch.Tensor:
    """
        Forward of the module.
        - Add positional encoding
        - Forward to layers
        - Aggregates using max
        (calculates a feature descriptor per element - reduces over points)
        :param x: Input tensor [batch_size, num_elements, num_points, dim_in].
        :param invalid_mask: Invalid mask for x [batch_size, num_elements, num_points].
        :param pos_enc: Positional_encoding for x.
        :return: Output tensor [batch_size, num_elements, num_points, dim_in].
        """
    batch_size, num_elements, num_points, dim_in = x.shape
    x += pos_enc
    x_flat = x.view(-1, num_points, dim_in)
    invalid_mask_flat = invalid_mask.view(-1, num_points)
    valid_polys = ~invalid_mask.all(-1).flatten()
    x_to_process = x_flat[valid_polys]
    mask_to_process = invalid_mask_flat[valid_polys]
    for layer in self.layers:
        x_to_process = layer(x_to_process, mask_to_process)
    x_to_process = x_to_process.masked_fill(mask_to_process[..., None] > 0, float('-inf'))
    x_to_process = torch.max(x_to_process, dim=1).values
    x = torch.zeros_like(x_flat[:, 0])
    x[valid_polys] = x_to_process
    x = x.view(batch_size, num_elements, self.dim_in)
    return x

class LaneNet(nn.Module):
    """
    Lane feature extractor with either lane graph convolution
    Based on the dilated LaneConv, LaneNet builds a multi-scale LaneConv operator to extract
    lane information. It is composed of LaneConv residual blocks, which are the stack of a LaneConv
    and a linear layer, as well as a shortcut. Layer normalization and ReLU are used after each
    LaneConv and linear layer.
    """

    def __init__(self, lane_input_len: int, lane_feature_len: int, num_scales: int, num_residual_blocks: int, is_map_feat: bool, num_groups: int=1) -> None:
        """
        Constructs LaneGraphCNN layer for LaneGCN. It consists of several modules that performs
        multi-scale graph convolution based on lane connections. Essentially allow lane feature to
        capture the long range lane topology and information.
        :param lane_input_len: Raw feature size of lane vector representation (e.g. 2 if using
            average of x,y coordinates of lane end points)
        :param lane_feature_len: Feature size of lane nodes.
        :param num_scales: Number of scales to extend the predecessor and successor lane nodes.
        :param num_residual_blocks: Number of residual blocks for the GCN (LaneGCN uses 4).
        :param is_map_feat: if set to True, output max pooling over the lane features so it can
            be used as a map feature, otherwise output lane features as is.
        :param num_groups: Number of groups in groupnorm layer.
        """
        super().__init__()
        self.is_map_feat = is_map_feat
        self.num_scales = num_scales
        self.num_residual_blocks = num_residual_blocks
        self.input = nn.Sequential(nn.Linear(lane_input_len, lane_feature_len), nn.ReLU(inplace=True), LinearWithGroupNorm(lane_feature_len, lane_feature_len, num_groups=num_groups, activation=False))
        self._seg = nn.Sequential(nn.Linear(lane_input_len, lane_feature_len), nn.ReLU(inplace=True), LinearWithGroupNorm(lane_feature_len, lane_feature_len, num_groups=num_groups, activation=False))
        self._relu = nn.ReLU(inplace=True)
        fusion_components = ['center', 'group_norm', 'linear_w_group_norm']
        for scale in range(1, num_scales + 1):
            fusion_components.append(f'pre{scale}')
            fusion_components.append(f'suc{scale}')
        fusion_net: Dict[str, List[nn.module]] = dict()
        for key in fusion_components:
            fusion_net[key] = []
        for _ in range(num_residual_blocks):
            for key in fusion_net:
                if key in ['group_norm']:
                    fusion_net[key].append(nn.GroupNorm(gcd(num_groups, lane_feature_len), lane_feature_len))
                elif key in ['linear_w_group_norm']:
                    fusion_net[key].append(LinearWithGroupNorm(lane_feature_len, lane_feature_len, num_groups=num_groups, activation=False))
                else:
                    fusion_net[key].append(nn.Linear(lane_feature_len, lane_feature_len, bias=False))
        for key in fusion_net:
            fusion_net[key] = nn.ModuleList(fusion_net[key])
        self.fusion_net = nn.ModuleDict(fusion_net)

    def forward(self, coords: torch.Tensor, conns: torch.Tensor) -> torch.FloatTensor:
        """
        :param coords:<torch.FloatTensor: num_lanes, 2, 2>. Coordindates of the start and
                    end point of each lane segment.
        :param conns:<torch.LongTensor: num_scale, num_connections, 2>. Indices of the predecessor
                    and successor segment pair with different scale/hop.
        :return:
            lane_features: <torch.FloatTensor: num lane segments across all batches,
               map feature size>. Features corresponding to lane nodes, updated with
               information from adjacent lane nodes.
        """
        lane_centers = coords.mean(axis=1)
        lane_diff = coords[:, 1] - coords[:, 0]
        lane_features = self.input(lane_centers)
        lane_features += self._seg(lane_diff)
        lane_features = self._relu(lane_features)
        residual = lane_features
        for idx in range(self.num_residual_blocks):
            temp_features = self.fusion_net['center'][idx](lane_features)
            for key in self.fusion_net:
                if key.startswith('pre'):
                    scale = int(key[3:])
                    connections = conns[scale]
                    src_node_idx = connections[:, 1]
                    dst_node_idx = connections[:, 0]
                    temp_features.index_add_(0, dst_node_idx, self.fusion_net[key][idx](lane_features[src_node_idx]))
                if key.startswith('suc'):
                    scale = int(key[3:])
                    connections = conns[scale]
                    src_node_idx = connections[:, 0]
                    dst_node_idx = connections[:, 1]
                    temp_features.index_add_(0, dst_node_idx, self.fusion_net[key][idx](lane_features[src_node_idx]))
            lane_features = self.fusion_net['group_norm'][idx](temp_features)
            lane_features = self._relu(lane_features)
            lane_features = self.fusion_net['linear_w_group_norm'][idx](lane_features)
            lane_features += residual
            lane_features = self._relu(lane_features)
            residual = lane_features
        if self.is_map_feat:
            return torch.max(lane_features, 0, keepdim=True)[0]
        else:
            return lane_features

def forward(self, coords: torch.Tensor, conns: torch.Tensor) -> torch.FloatTensor:
    """
        :param coords:<torch.FloatTensor: num_lanes, 2, 2>. Coordindates of the start and
                    end point of each lane segment.
        :param conns:<torch.LongTensor: num_scale, num_connections, 2>. Indices of the predecessor
                    and successor segment pair with different scale/hop.
        :return:
            lane_features: <torch.FloatTensor: num lane segments across all batches,
               map feature size>. Features corresponding to lane nodes, updated with
               information from adjacent lane nodes.
        """
    lane_centers = coords.mean(axis=1)
    lane_diff = coords[:, 1] - coords[:, 0]
    lane_features = self.input(lane_centers)
    lane_features += self._seg(lane_diff)
    lane_features = self._relu(lane_features)
    residual = lane_features
    for idx in range(self.num_residual_blocks):
        temp_features = self.fusion_net['center'][idx](lane_features)
        for key in self.fusion_net:
            if key.startswith('pre'):
                scale = int(key[3:])
                connections = conns[scale]
                src_node_idx = connections[:, 1]
                dst_node_idx = connections[:, 0]
                temp_features.index_add_(0, dst_node_idx, self.fusion_net[key][idx](lane_features[src_node_idx]))
            if key.startswith('suc'):
                scale = int(key[3:])
                connections = conns[scale]
                src_node_idx = connections[:, 0]
                dst_node_idx = connections[:, 1]
                temp_features.index_add_(0, dst_node_idx, self.fusion_net[key][idx](lane_features[src_node_idx]))
        lane_features = self.fusion_net['group_norm'][idx](temp_features)
        lane_features = self._relu(lane_features)
        lane_features = self.fusion_net['linear_w_group_norm'][idx](lane_features)
        lane_features += residual
        lane_features = self._relu(lane_features)
        residual = lane_features
    if self.is_map_feat:
        return torch.max(lane_features, 0, keepdim=True)[0]
    else:
        return lane_features

class Lane2Lane(nn.Module):
    """The lane to lane block propagates information over lane graphs and updates the lane feature."""

    def __init__(self, lane_feature_len: int, num_scales: int, num_res_blocks: int, num_groups: int=1) -> None:
        """
        Constructs Fusion Net among lane nodes.
        :param lane_feature_len: Feature size of lane nodes.
        :param num_scales: Number of scales to extend the predecessor and successor lane nodes.
        :param num_res_blocks: Number of residual blocks for the GCN (LaneGCN uses 4).
        :param num_groups: Number of groups in groupnorm layer.
        """
        super().__init__()
        fusion_components = ['center', 'normalize', 'center2']
        for scale in range(num_scales):
            fusion_components.append(f'pre{scale}')
            fusion_components.append(f'suc{scale}')
        fusion_net: Dict[str, nn.ModuleList] = dict()
        for key in fusion_components:
            fusion_net[key] = []
        for _ in range(num_res_blocks):
            for key in fusion_net:
                if key in ['normalize']:
                    fusion_net[key].append(nn.GroupNorm(gcd(num_groups, lane_feature_len), lane_feature_len))
                elif key in ['center2']:
                    fusion_net[key].append(LinearWithGroupNorm(lane_feature_len, lane_feature_len, num_groups=num_groups, activation=False))
                else:
                    fusion_net[key].append(nn.Linear(lane_feature_len, lane_feature_len, bias=False))
        for key in fusion_net:
            fusion_net[key] = nn.ModuleList(fusion_net[key])
        self.fusion_net = nn.ModuleDict(fusion_net)
        self._relu = nn.ReLU(inplace=True)

    def forward(self, lane_features: torch.FloatTensor, lane_graph: Dict[str, Dict[str, torch.Tensor]]) -> torch.FloatTensor:
        """
        Propagate the model.
        :param lane_features: <torch.FloatTensor: num lane nodes across all batches,
            lane node feature size>. Features corresponding to lane nodes.
        :param lane_graph: <Dict[str, List[torch.Tensor]]: Extracted lane graph from MapNet()>
            n_hop_pre: List of n_hop pre neighbor node index, torch.Tensor: num of lane nodes
            suc: List of cooresponding successor nodes, torch.Tensor: num of lane nodes
            n_hop_suc: List of n_hop suc neighbor node index, torch.Tensor: num of lane nodes
            pre: List of cooresponding precessor nodes, torch.Tensor: num of lane nodes
        :return: lane_features: <torch.FloatTensor: num lane segments across all batches,
                                map feature size>.
            Features corresponding to lane nodes, updated with information from adjacent
                lane nodes.
        """
        res = lane_features
        for idx in range(len(self.fusion_net['center'])):
            temp = self.fusion_net['center'][idx](lane_features)
            for key in self.fusion_net:
                if key.startswith('pre'):
                    k2 = int(key[3:])
                    temp.index_add_(0, lane_graph['suc'][str(k2)], self.fusion_net[key][idx](lane_features[lane_graph['n_hop_pre'][str(k2)]]))
                if key.startswith('suc'):
                    k2 = int(key[3:])
                    temp.index_add_(0, lane_graph['pre'][str(k2)], self.fusion_net[key][idx](lane_features[lane_graph['n_hop_suc'][str(k2)]]))
            lane_features = self.fusion_net['normalize'][idx](temp)
            lane_features = self._relu(lane_features)
            lane_features = self.fusion_net['center2'][idx](lane_features)
            lane_features += res
            lane_features = self._relu(lane_features)
            res = lane_features
        return lane_features

def forward(self, lane_features: torch.FloatTensor, lane_graph: Dict[str, Dict[str, torch.Tensor]]) -> torch.FloatTensor:
    """
        Propagate the model.
        :param lane_features: <torch.FloatTensor: num lane nodes across all batches,
            lane node feature size>. Features corresponding to lane nodes.
        :param lane_graph: <Dict[str, List[torch.Tensor]]: Extracted lane graph from MapNet()>
            n_hop_pre: List of n_hop pre neighbor node index, torch.Tensor: num of lane nodes
            suc: List of cooresponding successor nodes, torch.Tensor: num of lane nodes
            n_hop_suc: List of n_hop suc neighbor node index, torch.Tensor: num of lane nodes
            pre: List of cooresponding precessor nodes, torch.Tensor: num of lane nodes
        :return: lane_features: <torch.FloatTensor: num lane segments across all batches,
                                map feature size>.
            Features corresponding to lane nodes, updated with information from adjacent
                lane nodes.
        """
    res = lane_features
    for idx in range(len(self.fusion_net['center'])):
        temp = self.fusion_net['center'][idx](lane_features)
        for key in self.fusion_net:
            if key.startswith('pre'):
                k2 = int(key[3:])
                temp.index_add_(0, lane_graph['suc'][str(k2)], self.fusion_net[key][idx](lane_features[lane_graph['n_hop_pre'][str(k2)]]))
            if key.startswith('suc'):
                k2 = int(key[3:])
                temp.index_add_(0, lane_graph['pre'][str(k2)], self.fusion_net[key][idx](lane_features[lane_graph['n_hop_suc'][str(k2)]]))
        lane_features = self.fusion_net['normalize'][idx](temp)
        lane_features = self._relu(lane_features)
        lane_features = self.fusion_net['center2'][idx](lane_features)
        lane_features += res
        lane_features = self._relu(lane_features)
        res = lane_features
    return lane_features

class LinearWithGroupNorm(nn.Module):
    """Linear layer with group normalization activation used in LaneGCN."""

    def __init__(self, n_in: int, n_out: int, num_groups: int=32, activation: bool=True) -> None:
        """
        Initialize layer.
        :param n_in: Number of input channels.
        :param n_out: Number of output channels.
        :param num_groups: Number of groups for GroupNorm.
        :param activation: Boolean indicating whether to apply ReLU activation.
        """
        super().__init__()
        self.linear = nn.Linear(n_in, n_out, bias=False)
        self.norm = nn.GroupNorm(gcd(num_groups, n_out), n_out)
        self.relu = nn.ReLU(inplace=True)
        self.activation = activation

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply linear layer to input tensor.
        :param x: Input tensor.
        :return: Output of linear layer.
        """
        out = self.linear(x)
        out = self.norm(out)
        if self.activation:
            out = self.relu(out)
        return out

def forward(self, x: torch.Tensor) -> torch.Tensor:
    """
        Apply linear layer to input tensor.
        :param x: Input tensor.
        :return: Output of linear layer.
        """
    out = self.linear(x)
    out = self.norm(out)
    if self.activation:
        out = self.relu(out)
    return out

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

def cache_scenarios(args: List[Dict[str, Union[List[str], DictConfig]]]) -> List[CacheResult]:
    """
    Performs the caching of scenario DB files in parallel.
    :param args: A list of dicts containing the following items:
        "scenario": the scenario as built by scenario_builder
        "cfg": the DictConfig to use to process the file.
    :return: A dict with the statistics of the job. Contains the following keys:
        "successes": The number of successfully processed scenarios.
        "failures": The number of scenarios that couldn't be processed.
    """

    def cache_scenarios_internal(args: List[Dict[str, Union[List[AbstractScenario], DictConfig]]]) -> List[CacheResult]:
        node_id = int(os.environ.get('NODE_RANK', 0))
        thread_id = str(uuid.uuid4())
        scenarios: List[AbstractScenario] = [a['scenario'] for a in args]
        cfg: DictConfig = args[0]['cfg']
        model = build_torch_module_wrapper(cfg.model)
        feature_builders = model.get_list_of_required_feature()
        target_builders = model.get_list_of_computed_target()
        del model
        assert cfg.cache.cache_path is not None, f'Cache path cannot be None when caching, got {cfg.cache.cache_path}'
        preprocessor = FeaturePreprocessor(cache_path=cfg.cache.cache_path, force_feature_computation=cfg.cache.force_feature_computation, feature_builders=feature_builders, target_builders=target_builders)
        logger.info('Extracted %s scenarios for thread_id=%s, node_id=%s.', str(len(scenarios)), thread_id, node_id)
        num_failures = 0
        num_successes = 0
        all_file_cache_metadata: List[Optional[CacheMetadataEntry]] = []
        for idx, scenario in enumerate(scenarios):
            logger.info('Processing scenario %s / %s in thread_id=%s, node_id=%s', idx + 1, len(scenarios), thread_id, node_id)
            features, targets, file_cache_metadata = preprocessor.compute_features(scenario)
            scenario_num_failures = sum((0 if feature.is_valid else 1 for feature in itertools.chain(features.values(), targets.values())))
            scenario_num_successes = len(features.values()) + len(targets.values()) - scenario_num_failures
            num_failures += scenario_num_failures
            num_successes += scenario_num_successes
            all_file_cache_metadata += file_cache_metadata
        logger.info('Finished processing scenarios for thread_id=%s, node_id=%s', thread_id, node_id)
        return [CacheResult(failures=num_failures, successes=num_successes, cache_metadata=all_file_cache_metadata)]
    result = cache_scenarios_internal(args)
    gc.collect()
    return result

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

@staticmethod
def _render_expert_trajectory(main_figure: SimulationFigure) -> None:
    """
        Render expert trajectory.
        :param main_figure: Main simulation figure.
        """
    expert_ego_trajectory = main_figure.scenario.get_expert_ego_trajectory()
    source = extract_source_from_states(expert_ego_trajectory)
    main_figure.render_expert_trajectory(expert_ego_trajectory_state=source)

class TestBaseTab(unittest.TestCase):
    """Test base_tab functionality."""

    def set_up_dummy_simulation(self, simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
        save_path.mkdir(parents=True, exist_ok=True)
        simulation_data = create_sample_simulation_log(save_path / 'test_base_tab_simulation_log.msgpack.xz')
        simulation_data.save_to_file()

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
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """Set up a nuboard base tab."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        doc = Document()
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
        color_palettes = Category20[20] + Set3[12] + Bokeh[8]
        experiment_file_data = ExperimentFileData(file_paths=[], color_palettes=color_palettes)
        self.base_tab = BaseTab(doc=doc, experiment_file_data=experiment_file_data)

    def test_update_experiment_file_data(self) -> None:
        """Test update experiment file data."""
        self.base_tab.experiment_file_data.update_data(file_paths=[self.nuboard_file])
        self.assertEqual(len(self.base_tab.experiment_file_data.available_metric_statistics_names), 1)
        self.assertEqual(len(self.base_tab.experiment_file_data.simulation_scenario_keys), 1)

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change feature."""
        self.base_tab.experiment_file_data.update_data(file_paths=[self.nuboard_file])
        self.assertRaises(NotImplementedError, self.base_tab.file_paths_on_change, self.base_tab.experiment_file_data, [0])

    def tearDown(self) -> None:
        """Remove all temporary folders and files."""
        self.tmp_dir.cleanup()

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
    metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
    metric_file_callback.on_run_simulation_end()

class HistogramTab(BaseTab):
    """Histogram tab in nuBoard."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, bins: int=HistogramTabBinSpinnerConfig.default_bins, max_scenario_names: int=20):
        """
        Histogram for metric results about simulation.
        :param doc: Bokeh html document.
        :param experiment_file_data: Experiment file data.
        :param bins: Default number of bins in histograms.
        :param max_scenario_names: Show the maximum list of scenario names in each bin, 0 or None to disable
        """
        super().__init__(doc=doc, experiment_file_data=experiment_file_data)
        self._bins = bins
        self._max_scenario_names = max_scenario_names
        self.planner_checkbox_group.name = HistogramConstantConfig.PLANNER_CHECKBOX_GROUP_NAME
        self.planner_checkbox_group.js_on_change('active', HistogramTabLoadingJSCode.get_js_code())
        self._scenario_type_multi_choice = MultiChoice(**HistogramTabScenarioTypeMultiChoiceConfig.get_config())
        self._scenario_type_multi_choice.on_change('value', self._scenario_type_multi_choice_on_change)
        self._scenario_type_multi_choice.js_on_change('value', HistogramTabUpdateWindowsSizeJSCode.get_js_code())
        self._metric_name_multi_choice = MultiChoice(**HistogramTabMetricNameMultiChoiceConfig.get_config())
        self._metric_name_multi_choice.on_change('value', self._metric_name_multi_choice_on_change)
        self._metric_name_multi_choice.js_on_change('value', HistogramTabUpdateWindowsSizeJSCode.get_js_code())
        self._bin_spinner = Spinner(**HistogramTabBinSpinnerConfig.get_config())
        self._histogram_modal_query_btn = Button(**HistogramTabModalQueryButtonConfig.get_config())
        self._histogram_modal_query_btn.js_on_click(HistogramTabLoadingJSCode.get_js_code())
        self._histogram_modal_query_btn.on_click(self._setting_modal_query_button_on_click)
        self._default_div = Div(**HistogramTabDefaultDivConfig.get_config())
        self._histogram_plots = column(self._default_div, **HistogramTabPlotConfig.get_config())
        self._histogram_plots.js_on_change('children', HistogramTabLoadingEndJSCode.get_js_code())
        self._histogram_figures: Optional[column] = None
        self._aggregated_data: Optional[HistogramConstantConfig.HistogramDataType] = None
        self._histogram_edges: Optional[HistogramConstantConfig.HistogramEdgesDataType] = None
        self._plot_data: Dict[str, List[glyph]] = defaultdict(list)
        self._init_selection()

    @property
    def bin_spinner(self) -> Spinner:
        """Return a bin spinner."""
        return self._bin_spinner

    @property
    def scenario_type_multi_choice(self) -> MultiChoice:
        """Return scenario_type_multi_choice."""
        return self._scenario_type_multi_choice

    @property
    def metric_name_multi_choice(self) -> MultiChoice:
        """Return metric_name_multi_choice."""
        return self._metric_name_multi_choice

    @property
    def histogram_plots(self) -> column:
        """Return histogram_plots."""
        return self._histogram_plots

    @property
    def histogram_modal_query_btn(self) -> Button:
        """Return histogram modal query button."""
        return self._histogram_modal_query_btn

    def _click_planner_checkbox_group(self, attr: Any) -> None:
        """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
        if not self._aggregated_data and (not self._histogram_edges):
            return
        self._histogram_figures = self._render_histograms()
        self._doc.add_next_tick_callback(self._update_histogram_layouts)

    def file_paths_on_change(self, experiment_file_data: ExperimentFileData, experiment_file_active_index: List[int]) -> None:
        """
        Interface to update layout when file_paths is changed.
        :param experiment_file_data: Experiment file data.
        :param experiment_file_active_index: Active indexes for experiment files.
        """
        self._experiment_file_data = experiment_file_data
        self._experiment_file_active_index = experiment_file_active_index
        self._init_selection()
        self._update_histograms()

    def _update_histogram_layouts(self) -> None:
        """Update histogram layouts."""
        self._histogram_plots.children[0] = layout(self._histogram_figures)

    def _update_histograms(self) -> None:
        """Update histograms."""
        self._aggregated_data = self._aggregate_statistics()
        aggregated_scenario_type_score_data = self._aggregate_scenario_type_score_histogram()
        self._aggregated_data.update(aggregated_scenario_type_score_data)
        self._histogram_edges = compute_histogram_edges(aggregated_data=self._aggregated_data, bins=self._bins)
        self._histogram_figures = self._render_histograms()
        self._doc.add_next_tick_callback(self._update_histogram_layouts)

    def _setting_modal_query_button_on_click(self) -> None:
        """Setting modal query button on click helper function."""
        if self._metric_name_multi_choice.tags:
            self.window_width = self._metric_name_multi_choice.tags[0]
            self.window_height = self._metric_name_multi_choice.tags[1]
        if self._bin_spinner.value:
            self._bins = self._bin_spinner.value
        self._update_histograms()

    def _metric_name_multi_choice_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in histogram metric name.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if self._metric_name_multi_choice.tags:
            self.window_width = self._metric_name_multi_choice.tags[0]
            self.window_height = self._metric_name_multi_choice.tags[1]

    def _scenario_type_multi_choice_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in histogram scenario type.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if self._scenario_type_multi_choice.tags:
            self.window_width = self._scenario_type_multi_choice.tags[0]
            self.window_height = self.scenario_type_multi_choice.tags[1]

    def _adjust_plot_width_size(self, n_bins: int) -> int:
        """
        Adjust plot width size based on number of bins.
        :param n_bins: Number of bins.
        :return Width size of a histogram plot.
        """
        base_plot_width: int = self.plot_sizes[0]
        if n_bins < 20:
            return base_plot_width
        width_multiplier_factor: int = n_bins // 20 * 100
        width_size: int = min(base_plot_width + width_multiplier_factor, HistogramTabFigureStyleConfig.maximum_plot_width)
        return width_size

    def _init_selection(self) -> None:
        """Init histogram and scalar selection options."""
        planner_name_list: List[str] = []
        self.planner_checkbox_group.labels = []
        self.planner_checkbox_group.active = []
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for metric_statistics_dataframe in metric_statistics_dataframes:
                planner_names = metric_statistics_dataframe.planner_names
                planner_name_list += planner_names
        sorted_planner_name_list = sorted(list(set(planner_name_list)))
        self.planner_checkbox_group.labels = sorted_planner_name_list
        self.planner_checkbox_group.active = [index for index in range(len(sorted_planner_name_list))]
        self._init_multi_search_criteria_selection(scenario_type_multi_choice=self._scenario_type_multi_choice, metric_name_multi_choice=self._metric_name_multi_choice)

    def plot_vbar(self, histogram_figure_data: HistogramFigureData, counts: npt.NDArray[np.int64], category: List[str], planner_name: str, legend_label: str, color: str, scenario_names: List[str], x_values: List[str], width: float=0.4, histogram_file_name: Optional[str]=None) -> None:
        """
        Plot a vertical bar plot.
        :param histogram_figure_data: Figure class.
        :param counts: An array of counts for each category.
        :param category: A list of category (x-axis label).
        :param planner_name: Planner name.
        :param legend_label: Legend label.
        :param color: Legend color.
        :param scenario_names: A list of scenario names.
        :param x_values: X-axis values.
        :param width: Bar width.
        :param histogram_file_name: Histogram file name for the histogram data.
        """
        y_values = deepcopy(counts)
        bottom: npt.NDArray[np.int64] = np.zeros_like(counts) if histogram_figure_data.frequency_array is None else histogram_figure_data.frequency_array
        count_position = counts > 0
        bottom_arrays: npt.NDArray[np.int64] = bottom * count_position
        top = counts + bottom_arrays
        histogram_file_names = [histogram_file_name] * len(top)
        data_source = ColumnDataSource(dict(x=category, top=top, bottom=bottom_arrays, y_values=y_values, x_values=x_values, scenario_names=scenario_names, histogram_file_name=histogram_file_names))
        figure_plot = histogram_figure_data.figure_plot
        vbar = figure_plot.vbar(x='x', top='top', bottom='bottom', fill_color=color, legend_label=legend_label, width=width, source=data_source, **HistogramTabHistogramBarStyleConfig.get_config())
        self._plot_data[planner_name].append(vbar)
        HistogramTabHistogramBarStyleConfig.update_histogram_bar_figure_style(histogram_figure=figure_plot)

    def plot_histogram(self, histogram_figure_data: HistogramFigureData, hist: npt.NDArray[np.float64], edges: npt.NDArray[np.float64], planner_name: str, legend_label: str, color: str, scenario_names: List[str], x_values: List[str], histogram_file_name: Optional[str]=None) -> None:
        """
        Plot a histogram.
        Reference from https://docs.bokeh.org/en/latest/docs/gallery/histogram.html.
        :param histogram_figure_data: Histogram figure data.
        :param hist: Histogram data.
        :param edges: Histogram bin data.
        :param planner_name: Planner name.
        :param legend_label: Legend label.
        :param color: Legend color.
        :param scenario_names: A list of scenario names.
        :param x_values: A list of x value names.
        :param histogram_file_name: Histogram file name for the histogram data.
        """
        bottom: npt.NDArray[np.int64] = np.zeros_like(hist) if histogram_figure_data.frequency_array is None else histogram_figure_data.frequency_array
        hist_position = hist > 0
        bottom_arrays: npt.NDArray[np.int64] = bottom * hist_position
        top = hist + bottom_arrays
        histogram_file_names = [histogram_file_name] * len(top)
        data_source = ColumnDataSource(dict(top=top, bottom=bottom_arrays, left=edges[:-1], right=edges[1:], y_values=hist, x_values=x_values, scenario_names=scenario_names, histogram_file_name=histogram_file_names))
        figure_plot = histogram_figure_data.figure_plot
        quad = figure_plot.quad(top='top', bottom='bottom', left='left', right='right', fill_color=color, legend_label=legend_label, **HistogramTabHistogramBarStyleConfig.get_config(), source=data_source)
        self._plot_data[planner_name].append(quad)
        HistogramTabHistogramBarStyleConfig.update_histogram_bar_figure_style(histogram_figure=figure_plot)

    def _render_histogram_plot(self, title: str, x_axis_label: str, x_range: Optional[Union[List[str], FactorRange]]=None, histogram_file_name: Optional[str]=None) -> HistogramFigureData:
        """
        Render a histogram plot.
        :param title: Title.
        :param x_axis_label: x-axis label.
        :param x_range: A list of category data if specified.
        :param histogram_file_name: Histogram file name for the histogram plot.
        :return a figure.
        """
        if x_range is None:
            len_plot_width = 1
        elif isinstance(x_range, list):
            len_plot_width = len(x_range)
        else:
            len_plot_width = len(x_range.factors)
        plot_width = self._adjust_plot_width_size(n_bins=len_plot_width)
        tooltips = [('Frequency', '@y_values'), ('Values', '@x_values{safe}'), ('Scenarios', '@scenario_names{safe}')]
        if histogram_file_name:
            tooltips.append(('File', '@histogram_file_name'))
        hover_tool = HoverTool(tooltips=tooltips, point_policy='follow_mouse')
        statistic_figure = figure(**HistogramTabFigureStyleConfig.get_config(title=title, x_axis_label=x_axis_label, width=plot_width, height=self.plot_sizes[1], x_range=x_range), tools=['pan', 'wheel_zoom', 'save', 'reset', hover_tool])
        HistogramTabFigureStyleConfig.update_histogram_figure_style(histogram_figure=statistic_figure)
        return HistogramFigureData(figure_plot=statistic_figure)

    def _render_histogram_layout(self, histograms: HistogramConstantConfig.HistogramFigureDataType) -> List[column]:
        """
        Render histogram layout.
        :param histograms: A dictionary of histogram names and their histograms.
        :return: A list of lists of figures (a list per row).
        """
        layouts = []
        ncols = self.get_plot_cols(plot_width=self.plot_sizes[0], default_ncols=HistogramConstantConfig.HISTOGRAM_TAB_DEFAULT_NUMBER_COLS)
        for metric_statistics_name, statistics_data in histograms.items():
            title_div = Div(**HistogramTabFigureTitleDivStyleConfig.get_config(title=metric_statistics_name))
            figures = [histogram_figure.figure_plot for statistic_name, histogram_figure in statistics_data.items()]
            grid_plot = gridplot(figures, **HistogramTabFigureGridPlotStyleConfig.get_config(ncols=ncols, height=self.plot_sizes[1]))
            grid_layout = column(title_div, grid_plot)
            layouts.append(grid_layout)
        return layouts

    def _aggregate_scenario_type_score_histogram(self) -> HistogramConstantConfig.HistogramDataType:
        """
        Aggregate metric aggregator data.
        :return: A dictionary of metric aggregator names and their metric scores.
        """
        data: HistogramConstantConfig.HistogramDataType = defaultdict(list)
        selected_scenario_types = self._scenario_type_multi_choice.value
        for index, metric_aggregator_dataframes in enumerate(self.experiment_file_data.metric_aggregator_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for metric_aggregator_filename, metric_aggregator_dataframe in metric_aggregator_dataframes.items():
                histogram_data_list = aggregate_metric_aggregator_dataframe_histogram_data(metric_aggregator_dataframe_index=index, metric_aggregator_dataframe=metric_aggregator_dataframe, scenario_types=selected_scenario_types, dataframe_file_name=metric_aggregator_filename)
                if histogram_data_list:
                    data[HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME] += histogram_data_list
        return data

    def _aggregate_statistics(self) -> HistogramConstantConfig.HistogramDataType:
        """
        Aggregate statistics data.
        :return A dictionary of metric names and their aggregated data.
        """
        data: HistogramConstantConfig.HistogramDataType = defaultdict(list)
        scenario_types = self._scenario_type_multi_choice.value
        metric_choices = self._metric_name_multi_choice.value
        if not len(scenario_types) and (not len(metric_choices)):
            return data
        if 'all' in scenario_types:
            scenario_types = None
        else:
            scenario_types = tuple(scenario_types)
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for metric_statistics_dataframe in metric_statistics_dataframes:
                histogram_data_list = aggregate_metric_statistics_dataframe_histogram_data(metric_statistics_dataframe=metric_statistics_dataframe, metric_statistics_dataframe_index=index, scenario_types=scenario_types, metric_choices=metric_choices)
                if histogram_data_list:
                    data[metric_statistics_dataframe.metric_statistic_name] += histogram_data_list
        return data

    def _plot_bool_histogram(self, histogram_figure_data: HistogramFigureData, values: npt.NDArray[np.float64], scenarios: List[str], planner_name: str, legend_name: str, color: str, histogram_file_name: Optional[str]=None) -> None:
        """
        Plot boolean type of histograms.
        :param histogram_figure_data: Histogram figure data.
        :param values: An array of values.
        :param scenarios: A list of scenario names.
        :param planner_name: Planner name.
        :param legend_name: Legend name.
        :param color: Plot color.
        :param histogram_file_name: Histogram file name for the histogram data.
        """
        num_true = np.nansum(values)
        num_false = len(values[values == 0])
        scenario_names: List[List[str]] = [[] for _ in range(2)]
        for index, scenario in enumerate(scenarios):
            scenario_name_index = 1 if values[index] else 0
            if not self._max_scenario_names or len(scenario_names[scenario_name_index]) < self._max_scenario_names:
                scenario_names[scenario_name_index].append(scenario)
        scenario_names_flatten = ['<br>'.join(names) if names else '' for names in scenario_names]
        counts: npt.NDArray[np.int64] = np.asarray([num_false, num_true])
        x_range = ['False', 'True']
        x_values = ['False', 'True']
        self.plot_vbar(histogram_figure_data=histogram_figure_data, category=x_range, counts=counts, planner_name=planner_name, legend_label=legend_name, color=color, scenario_names=scenario_names_flatten, x_values=x_values, histogram_file_name=histogram_file_name)
        counts = np.asarray(counts)
        if histogram_figure_data.frequency_array is None:
            histogram_figure_data.frequency_array = deepcopy(counts)
        else:
            histogram_figure_data.frequency_array += counts

    def _plot_count_histogram(self, histogram_figure_data: HistogramFigureData, values: npt.NDArray[np.float64], scenarios: List[str], planner_name: str, legend_name: str, color: str, edges: npt.NDArray[np.float64], histogram_file_name: Optional[str]=None) -> None:
        """
        Plot count type of histograms.
        :param histogram_figure_data: Histogram figure data.
        :param values: An array of values.
        :param scenarios: A list of scenario names.
        :param planner_name: Planner name.
        :param legend_name: Legend name.
        :param color: Plot color.
        :param edges: Count edges.
        :param histogram_file_name: Histogram file name for the histogram data.
        """
        uniques: Any = np.unique(values, return_inverse=True)
        unique_values: npt.NDArray[np.float64] = uniques[0]
        unique_index: npt.NDArray[np.int64] = uniques[1]
        counts = {value: 0 for value in edges}
        bin_count = np.bincount(unique_index)
        for index, count_value in enumerate(bin_count):
            counts[unique_values[index]] = count_value
        scenario_names: List[List[str]] = [[] for _ in range(len(counts))]
        for index, bin_index in enumerate(unique_index):
            if not self._max_scenario_names or len(scenario_names[bin_index]) < self._max_scenario_names:
                scenario_names[bin_index].append(scenarios[index])
        scenario_names_flatten = ['<br>'.join(names) if names else '' for names in scenario_names]
        category = [str(key) for key in counts.keys()]
        count_values: npt.NDArray[np.int64] = np.asarray(list(counts.values()))
        self.plot_vbar(histogram_figure_data=histogram_figure_data, category=category, counts=count_values, planner_name=planner_name, legend_label=legend_name, color=color, scenario_names=scenario_names_flatten, width=0.1, x_values=category, histogram_file_name=histogram_file_name)
        if histogram_figure_data.frequency_array is None:
            histogram_figure_data.frequency_array = deepcopy(count_values)
        else:
            histogram_figure_data.frequency_array += count_values

    def _plot_bin_histogram(self, histogram_figure_data: HistogramFigureData, values: npt.NDArray[np.float64], scenarios: List[str], planner_name: str, legend_name: str, color: str, edges: npt.NDArray[np.float64], histogram_file_name: Optional[str]=None) -> None:
        """
        Plot bin type of histograms.
        :param histogram_figure_data: Histogram figure data.
        :param values: An array of values.
        :param scenarios: A list of scenario names.
        :param planner_name: Planner name.
        :param legend_name: Legend name.
        :param color: Plot color.
        :param edges: Histogram bin edges.
        :param histogram_file_name: Histogram file name for the histogram data.
        """
        hist, bins = np.histogram(values, bins=edges)
        value_bin_index: npt.NDArray[np.int64] = np.asarray(np.digitize(values, bins=bins[:-1]))
        scenario_names: List[List[str]] = [[] for _ in range(len(hist))]
        for index, bin_index in enumerate(value_bin_index):
            if not self._max_scenario_names or len(scenario_names[bin_index - 1]) < self._max_scenario_names:
                scenario_names[bin_index - 1].append(scenarios[index])
        scenario_names_flatten = ['<br>'.join(names) if names else '' for names in scenario_names]
        bins = np.round(bins, HistogramTabFigureStyleConfig.decimal_places)
        x_values = [str(value) + ' - ' + str(bins[index + 1]) for index, value in enumerate(bins[:-1])]
        self.plot_histogram(histogram_figure_data=histogram_figure_data, planner_name=planner_name, legend_label=legend_name, hist=hist, edges=edges, color=color, scenario_names=scenario_names_flatten, x_values=x_values, histogram_file_name=histogram_file_name)
        if histogram_figure_data.frequency_array is None:
            histogram_figure_data.frequency_array = deepcopy(hist)
        else:
            histogram_figure_data.frequency_array += hist

    def _draw_histogram_data(self) -> HistogramConstantConfig.HistogramFigureDataType:
        """
        Draw histogram data based on aggregated data.
        :return A dictionary of metric names and theirs histograms.
        """
        histograms: HistogramConstantConfig.HistogramFigureDataType = defaultdict()
        if self._aggregated_data is None or self._histogram_edges is None:
            return histograms
        for metric_statistics_name, aggregated_histogram_data in self._aggregated_data.items():
            if metric_statistics_name not in histograms:
                histograms[metric_statistics_name] = {}
            for histogram_data in aggregated_histogram_data:
                legend_name = histogram_data.planner_name + f' ({self.get_file_path_last_name(histogram_data.experiment_index)})'
                if histogram_data.planner_name not in self.enable_planner_names:
                    continue
                color = self.experiment_file_data.file_path_colors[histogram_data.experiment_index][histogram_data.planner_name]
                for statistic_name, statistic in histogram_data.statistics.items():
                    unit = statistic.unit
                    data: npt.NDArray[np.float64] = np.unique(self._histogram_edges[metric_statistics_name].get(statistic_name, None))
                    assert data is not None, f'Count edge data for {statistic_name} cannot be None!'
                    if statistic_name not in histograms[metric_statistics_name]:
                        x_range = get_histogram_plot_x_range(unit=unit, data=data)
                        histograms[metric_statistics_name][statistic_name] = self._render_histogram_plot(title=statistic_name, x_axis_label=unit, x_range=x_range, histogram_file_name=histogram_data.histogram_file_name)
                    histogram_figure_data = histograms[metric_statistics_name][statistic_name]
                    values = statistic.values
                    if unit in ['bool', 'boolean']:
                        self._plot_bool_histogram(histogram_figure_data=histogram_figure_data, values=values, scenarios=statistic.scenarios, planner_name=histogram_data.planner_name, legend_name=legend_name, color=color, histogram_file_name=histogram_data.histogram_file_name)
                    else:
                        edges = self._histogram_edges[metric_statistics_name][statistic_name]
                        if edges is None:
                            continue
                        if unit in ['count']:
                            self._plot_count_histogram(histogram_figure_data=histogram_figure_data, values=values, scenarios=statistic.scenarios, planner_name=histogram_data.planner_name, legend_name=legend_name, color=color, edges=edges, histogram_file_name=histogram_data.histogram_file_name)
                        else:
                            self._plot_bin_histogram(histogram_figure_data=histogram_figure_data, values=values, scenarios=statistic.scenarios, planner_name=histogram_data.planner_name, legend_name=legend_name, color=color, edges=edges, histogram_file_name=histogram_data.histogram_file_name)
        sorted_histograms = {}
        if HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME in histograms:
            sorted_histograms[HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME] = histograms[HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME]
        sorted_histogram_keys = sorted((key for key in histograms.keys() if key != HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME), reverse=False)
        sorted_histograms.update({key: histograms[key] for key in sorted_histogram_keys})
        return sorted_histograms

    def _render_histograms(self) -> List[column]:
        """
        Render histograms across all scenarios based on a scenario type.
        :return: A list of lists of figures (a list per row).
        """
        histograms = self._draw_histogram_data()
        layouts = self._render_histogram_layout(histograms)
        if not layouts:
            layouts = [column(self._default_div, width=HistogramTabPlotConfig.default_width, **HistogramTabPlotConfig.get_config())]
        return layouts

def _adjust_plot_width_size(self, n_bins: int) -> int:
    """
        Adjust plot width size based on number of bins.
        :param n_bins: Number of bins.
        :return Width size of a histogram plot.
        """
    base_plot_width: int = self.plot_sizes[0]
    if n_bins < 20:
        return base_plot_width
    width_multiplier_factor: int = n_bins // 20 * 100
    width_size: int = min(base_plot_width + width_multiplier_factor, HistogramTabFigureStyleConfig.maximum_plot_width)
    return width_size

class SkeletonTestTab(unittest.TestCase):
    """Base class for nuBoard tab unit tests."""

    @staticmethod
    def set_up_dummy_simulation(simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
        save_path.mkdir(parents=True, exist_ok=True)
        simulation_data = create_sample_simulation_log(save_path / f'{uuid4()}.msgpack.xz')
        simulation_data.save_to_file()

    @staticmethod
    def set_up_dummy_metric(metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90), Statistic(name='ego_count_acceleration', unit=MetricStatisticsType.COUNT.unit, value=2, type=MetricStatisticsType.COUNT), Statistic(name='ego_boolean_acceleration', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
        time_stamps = [0, 1, 2]
        accel = [0.0, 1.0, 2.0]
        time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
        result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1.0)
        key = MetricFileKey(metric_name='ego_acceleration', log_name=log_name, scenario_name=scenario_name, scenario_type=scenario_type, planner_name=planner_name)
        metric_engine = MetricsEngine(main_save_path=metric_path)
        metric_files = {scenario_name: [MetricFile(key=key, metric_statistics=[result])]}
        metric_engine.write_to_files(metric_files=metric_files)
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """
        Set up common data for nuboard unit tests.
        """
        self.doc = Document()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

@staticmethod
def set_up_dummy_metric(metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
    """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
    statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90), Statistic(name='ego_count_acceleration', unit=MetricStatisticsType.COUNT.unit, value=2, type=MetricStatisticsType.COUNT), Statistic(name='ego_boolean_acceleration', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
    time_stamps = [0, 1, 2]
    accel = [0.0, 1.0, 2.0]
    time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
    result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1.0)
    key = MetricFileKey(metric_name='ego_acceleration', log_name=log_name, scenario_name=scenario_name, scenario_type=scenario_type, planner_name=planner_name)
    metric_engine = MetricsEngine(main_save_path=metric_path)
    metric_files = {scenario_name: [MetricFile(key=key, metric_statistics=[result])]}
    metric_engine.write_to_files(metric_files=metric_files)
    metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
    metric_file_callback.on_run_simulation_end()

class MetricsEngine:
    """The metrics engine aggregates and manages the instantiated metrics for a scenario."""

    def __init__(self, main_save_path: Path, metrics: Optional[List[AbstractMetricBuilder]]=None) -> None:
        """
        Initializer for MetricsEngine class
        :param metrics: Metric objects.
        """
        self._main_save_path = main_save_path
        if not is_s3_path(self._main_save_path):
            self._main_save_path.mkdir(parents=True, exist_ok=True)
        if metrics is None:
            self._metrics: List[AbstractMetricBuilder] = []
        else:
            self._metrics = metrics

    @property
    def metrics(self) -> List[AbstractMetricBuilder]:
        """Retrieve a list of metric results."""
        return self._metrics

    def add_metric(self, metric_builder: AbstractMetricBuilder) -> None:
        """TODO: Create the list of types needed from the history"""
        self._metrics.append(metric_builder)

    def write_to_files(self, metric_files: Dict[str, List[MetricFile]]) -> None:
        """
        Write to a file by constructing a dataframe
        :param metric_files: A dictionary of scenario names and a list of their metric files.
        """
        for scenario_name, metric_files in metric_files.items():
            file_name = scenario_name + JSON_FILE_EXTENSION
            save_path = self._main_save_path / file_name
            dataframes = []
            for metric_file in metric_files:
                metric_file_key = metric_file.key
                for metric_statistic in metric_file.metric_statistics:
                    dataframe = construct_dataframe(log_name=metric_file_key.log_name, scenario_name=metric_file_key.scenario_name, scenario_type=metric_file_key.scenario_type, planner_name=metric_file_key.planner_name, metric_statistics=metric_statistic)
                    dataframes.append(dataframe)
            if len(dataframes):
                save_object_as_pickle(save_path, dataframes)

    def compute_metric_results(self, history: SimulationHistory, scenario: AbstractScenario) -> Dict[str, List[MetricStatistics]]:
        """
        Compute metrics in the engine
        :param history: History from simulation
        :param scenario: Scenario running this metric engine
        :return A list of metric statistics.
        """
        metric_results = {}
        for metric in self._metrics:
            try:
                start_time = time.perf_counter()
                metric_results[metric.name] = metric.compute(history, scenario=scenario)
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                logger.debug(f'Metric: {metric.name} running time: {elapsed_time:.2f} seconds.')
            except (NotImplementedError, Exception) as e:
                logger.error(f'Running {metric.name} with error: {e}')
                raise RuntimeError(f'Metric Engine failed with: {e}')
        return metric_results

    def compute(self, history: SimulationHistory, scenario: AbstractScenario, planner_name: str) -> Dict[str, List[MetricFile]]:
        """
        Compute metrics and return in a format of MetricStorageResult for each metric computation
        :param history: History from simulation
        :param scenario: Scenario running this metric engine
        :param planner_name: name of the planner
        :return A dictionary of scenario name and list of MetricStorageResult.
        """
        all_metrics_results = self.compute_metric_results(history=history, scenario=scenario)
        metric_files = defaultdict(list)
        for metric_name, metric_statistics_results in all_metrics_results.items():
            metric_file_key = MetricFileKey(metric_name=metric_name, log_name=scenario.log_name, scenario_name=scenario.scenario_name, scenario_type=scenario.scenario_type, planner_name=planner_name)
            metric_file = MetricFile(key=metric_file_key, metric_statistics=metric_statistics_results)
            metric_file_name = scenario.scenario_type + '_' + scenario.scenario_name + '_' + planner_name
            metric_files[metric_file_name].append(metric_file)
        return metric_files

def compute(self, history: SimulationHistory, scenario: AbstractScenario, planner_name: str) -> Dict[str, List[MetricFile]]:
    """
        Compute metrics and return in a format of MetricStorageResult for each metric computation
        :param history: History from simulation
        :param scenario: Scenario running this metric engine
        :param planner_name: name of the planner
        :return A dictionary of scenario name and list of MetricStorageResult.
        """
    all_metrics_results = self.compute_metric_results(history=history, scenario=scenario)
    metric_files = defaultdict(list)
    for metric_name, metric_statistics_results in all_metrics_results.items():
        metric_file_key = MetricFileKey(metric_name=metric_name, log_name=scenario.log_name, scenario_name=scenario.scenario_name, scenario_type=scenario.scenario_type, planner_name=planner_name)
        metric_file = MetricFile(key=metric_file_key, metric_statistics=metric_statistics_results)
        metric_file_name = scenario.scenario_type + '_' + scenario.scenario_name + '_' + planner_name
        metric_files[metric_file_name].append(metric_file)
    return metric_files

@dataclass
class MetricFileKey:
    """Class to retain metric name, scenario name and type and planner corresponding to metrics results."""
    metric_name: str
    log_name: str
    scenario_name: str
    scenario_type: str
    planner_name: str

    def serialize(self) -> Dict[str, str]:
        """Serialization of metric result key."""
        return {'metric_name': self.metric_name, 'log_name': self.log_name, 'scenario_name': self.scenario_name, 'scenario_type': self.scenario_type, 'planner_name': self.planner_name}

    @classmethod
    def deserialize(cls, data: Dict[str, str]) -> MetricFileKey:
        """
        Deserialization of metric result key
        :param data: A dictionary of data
        :return A Statistic data class.
        """
        return MetricFileKey(metric_name=data['metric_name'], log_name=data['log_name'], scenario_name=data['scenario_name'], scenario_type=data['scenario_type'], planner_name=data['planner_name'])

@classmethod
def deserialize(cls, data: Dict[str, str]) -> MetricFileKey:
    """
        Deserialization of metric result key
        :param data: A dictionary of data
        :return A Statistic data class.
        """
    return MetricFileKey(metric_name=data['metric_name'], log_name=data['log_name'], scenario_name=data['scenario_name'], scenario_type=data['scenario_type'], planner_name=data['planner_name'])

@dataclass
class TimeSeries:
    """
    Class to report time series data of metrics.
    """
    unit: str
    time_stamps: List[int]
    values: List[float]
    selected_frames: Optional[List[int]] = None

    def __post_init__(self) -> None:
        """Post initialization of TimeSeries."""
        assert len(self.time_stamps) == len(self.values)

    def serialize(self) -> Dict[str, Any]:
        """Serialization of TimeSeries."""
        return {'unit': self.unit, 'time_stamps': self.time_stamps, 'values': self.values, 'selected_frames': self.selected_frames}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Optional[TimeSeries]:
        """
        Deserialization of TimeSeries
        :param data: A dictionary of data
        :return A TimeSeries dataclass.
        """
        return TimeSeries(unit=data['unit'], time_stamps=data['time_stamps'], values=data['values'], selected_frames=data['selected_frames']) if data is not None else None

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Optional[TimeSeries]:
    """
        Deserialization of TimeSeries
        :param data: A dictionary of data
        :return A TimeSeries dataclass.
        """
    return TimeSeries(unit=data['unit'], time_stamps=data['time_stamps'], values=data['values'], selected_frames=data['selected_frames']) if data is not None else None

@dataclass
class MetricViolation(MetricResult):
    """Class to report results of violation-based metrics."""
    unit: str
    start_timestamp: int
    duration: int
    extremum: float
    mean: float

    def serialize(self) -> Dict[str, Any]:
        """Serialize the metric result."""
        return {'metric_computator': self.metric_computator, 'name': self.name, 'unit': self.unit, 'start_timestamp': self.start_timestamp, 'duration': self.duration, 'extremum': self.extremum, 'metric_category': self.metric_category}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> MetricViolation:
        """
        Deserialize the metric result when loading from a file
        :param data; A dictionary of data in loading.
        """
        return MetricViolation(metric_computator=data['metric_computator'], name=data['name'], start_timestamp=data['start_timestamp'], duration=data['duration'], extremum=data['extremum'], unit=data['unit'], metric_category=data['metric_category'], mean=data['mean'])

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> MetricViolation:
    """
        Deserialize the metric result when loading from a file
        :param data; A dictionary of data in loading.
        """
    return MetricViolation(metric_computator=data['metric_computator'], name=data['name'], start_timestamp=data['start_timestamp'], duration=data['duration'], extremum=data['extremum'], unit=data['unit'], metric_category=data['metric_category'], mean=data['mean'])

def calculate_relative_progress_to_goal(ego_states: List[EgoState], expert_states: List[EgoState], goal: StateSE2, tolerance: float=0.1) -> float:
    """
    Ratio of ego's to the expert's progress towards goal rounded up
    :param ego_states: A list of ego states
    :param expert_states: A list of expert states
    :param goal: goal
    :param tolerance: tolerance used for round up
    :return Ratio of progress towards goal.
    """
    ego_progress_value = calculate_ego_progress_to_goal(ego_states, goal)
    expert_progress_value = calculate_ego_progress_to_goal(expert_states, goal)
    relative_progress: float = max(tolerance, ego_progress_value) / max(tolerance, expert_progress_value)
    return relative_progress

def get_fault_type_statistics(all_at_fault_collisions: Dict[TrackedObjectType, List[float]]) -> List[Statistic]:
    """
    :param all_at_fault_collisions: Dict of at_fault collisions.
    :return: List of Statistics for all collision track types.
    """
    statistics = []
    track_types_collisions_energy_dict: Dict[str, List[float]] = {}
    for collision_track_type, collision_name in zip([VRU_types, [TrackedObjectType.VEHICLE], object_types], ['VRUs', 'vehicles', 'objects']):
        track_types_collisions_energy_dict[collision_name] = [colision_energy for track_type in collision_track_type for colision_energy in all_at_fault_collisions[track_type]]
        statistics.extend([Statistic(name=f'number_of_at_fault_collisions_with_{collision_name}', unit=MetricStatisticsType.COUNT.unit, value=len(track_types_collisions_energy_dict[collision_name]), type=MetricStatisticsType.COUNT)])
    for collision_name, track_types_collisions_energy in track_types_collisions_energy_dict.items():
        if len(track_types_collisions_energy) > 0:
            statistics.extend([Statistic(name=f'max_collision_energy_with_{collision_name}', unit='meters_per_second', value=max(track_types_collisions_energy), type=MetricStatisticsType.MAX), Statistic(name=f'min_collision_energy_with_{collision_name}', unit='meters_per_second', value=min(track_types_collisions_energy), type=MetricStatisticsType.MIN), Statistic(name=f'mean_collision_energy_with_{collision_name}', unit='meters_per_second', value=np.mean(track_types_collisions_energy), type=MetricStatisticsType.MEAN)])
    return statistics

def extract_ego_jerk(ego_states: List[EgoState], acceleration_coordinate: str, decimals: int=8, deriv_order: int=1, poly_order: int=2, window_length: int=15) -> npt.NDArray[np.float32]:
    """
    Extract jerk of ego pose in simulation history
    :param ego_states: A list of ego states
    :param acceleration_coordinate: x, y or 'magnitude' in acceleration
    :param decimals: Decimal precision
    :return An array of valid ego pose jerk and timestamps.
    """
    time_points = extract_ego_time_point(ego_states)
    ego_acceleration = extract_ego_acceleration(ego_states=ego_states, acceleration_coordinate=acceleration_coordinate)
    jerk = approximate_derivatives(ego_acceleration, time_points / 1000000.0, deriv_order=deriv_order, poly_order=poly_order, window_length=min(window_length, len(ego_acceleration)))
    jerk = np.round(jerk, decimals=decimals)
    return jerk

class ViolationMetricBase(MetricBase):
    """Base class for evaluation of violation metrics."""

    def __init__(self, name: str, category: str, max_violation_threshold: int=0, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializes the ViolationMetricBase class
        :param name: Metric name
        :param category: Metric category
        :param max_violation_threshold: Maximum threshold for the violation when computing the score.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._max_violation_threshold = max_violation_threshold
        self.number_of_violations = 0

    def aggregate_metric_violations(self, metric_violations: List[MetricViolation], scenario: AbstractScenario, time_series: Optional[TimeSeries]=None) -> List[MetricStatistics]:
        """
        Aggregates (possibly) multiple MetricViolations to a MetricStatistics.
        All the violations must be of the same metric.
        :param metric_violations: The list of violations for a single metric name.
        :param scenario: Scenario running this metric.
        :param time_series: Time series metrics.
        :return Statistics about the violations.
        """
        if not metric_violations:
            statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
        else:
            sample_violation = metric_violations[0]
            name = sample_violation.name
            unit = sample_violation.unit
            extrema = []
            mean_values = []
            durations = []
            for violation in metric_violations:
                assert name == violation.name
                extrema.append(violation.extremum)
                mean_values.append(violation.mean)
                durations.append(violation.duration)
            max_val = max(extrema)
            min_val = min(extrema)
            mean_val = np.sum([mean_value * duration for mean_value, duration in zip(mean_values, durations)]) / sum(durations)
            statistics = [Statistic(name=f'number_of_violations_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=len(metric_violations), type=MetricStatisticsType.COUNT), Statistic(name=f'max_violation_of_{self.name}', unit=unit, value=max_val, type=MetricStatisticsType.MAX), Statistic(name=f'min_violation_of_{self.name}', unit=unit, value=min_val, type=MetricStatisticsType.MIN), Statistic(name=f'mean_violation_of_{self.name}', unit=unit, value=mean_val, type=MetricStatisticsType.MEAN), Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=False, type=MetricStatisticsType.BOOLEAN)]
        self.number_of_violations = len(metric_violations)
        results: list[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
        return results

    def _compute_violation_metric_score(self, number_of_violations: int) -> float:
        """
        Compute a metric score based on a violation threshold. It is 1 - (x / (max_violation_threshold + 1))
        The score will be 0 if the number of violations exceeds this value
        :param number_of_violations: Total number of violations
        :return A metric score between 0 and 1.
        """
        return max(0.0, 1.0 - number_of_violations / (self._max_violation_threshold + 1))

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return self._compute_violation_metric_score(number_of_violations=self.number_of_violations)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        raise NotImplementedError

def aggregate_metric_violations(self, metric_violations: List[MetricViolation], scenario: AbstractScenario, time_series: Optional[TimeSeries]=None) -> List[MetricStatistics]:
    """
        Aggregates (possibly) multiple MetricViolations to a MetricStatistics.
        All the violations must be of the same metric.
        :param metric_violations: The list of violations for a single metric name.
        :param scenario: Scenario running this metric.
        :param time_series: Time series metrics.
        :return Statistics about the violations.
        """
    if not metric_violations:
        statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
    else:
        sample_violation = metric_violations[0]
        name = sample_violation.name
        unit = sample_violation.unit
        extrema = []
        mean_values = []
        durations = []
        for violation in metric_violations:
            assert name == violation.name
            extrema.append(violation.extremum)
            mean_values.append(violation.mean)
            durations.append(violation.duration)
        max_val = max(extrema)
        min_val = min(extrema)
        mean_val = np.sum([mean_value * duration for mean_value, duration in zip(mean_values, durations)]) / sum(durations)
        statistics = [Statistic(name=f'number_of_violations_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=len(metric_violations), type=MetricStatisticsType.COUNT), Statistic(name=f'max_violation_of_{self.name}', unit=unit, value=max_val, type=MetricStatisticsType.MAX), Statistic(name=f'min_violation_of_{self.name}', unit=unit, value=min_val, type=MetricStatisticsType.MIN), Statistic(name=f'mean_violation_of_{self.name}', unit=unit, value=mean_val, type=MetricStatisticsType.MEAN), Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=False, type=MetricStatisticsType.BOOLEAN)]
    self.number_of_violations = len(metric_violations)
    results: list[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
    return results

def _compute_violation_metric_score(self, number_of_violations: int) -> float:
    """
        Compute a metric score based on a violation threshold. It is 1 - (x / (max_violation_threshold + 1))
        The score will be 0 if the number of violations exceeds this value
        :param number_of_violations: Total number of violations
        :return A metric score between 0 and 1.
        """
    return max(0.0, 1.0 - number_of_violations / (self._max_violation_threshold + 1))

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

class WithinBoundMetricBase(MetricBase):
    """Base class for evaluation of within_bound metrics."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the WithinBoundMetricBase class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)
        self.within_bound_status: Optional[bool] = False

    @staticmethod
    def _compute_within_bound_metric_score(within_bound_status: bool) -> float:
        """
        Compute a metric score based on within bound condition
        :param within_bound_status: True if the value is within the bound, otherwise false
        :return 1.0 if within_bound_status is true otherwise 0.
        """
        return 1.0 if within_bound_status else 0.0

    def compute_score(self, scenario: AbstractScenario, metric_statistics: Dict[str, Statistic], time_series: Optional[TimeSeries]=None) -> Optional[float]:
        """Inherited, see superclass."""
        return None

    @staticmethod
    def _compute_within_bound(time_series: TimeSeries, min_within_bound_threshold: Optional[float]=None, max_within_bound_threshold: Optional[float]=None) -> Optional[bool]:
        """
        Compute if value is within bound based on the thresholds
        :param time_series: Time series object
        :param min_within_bound_threshold: Minimum threshold to check if value is within bound
        :param max_within_bound_threshold: Maximum threshold to check if value is within bound.
        """
        ego_pose_values: npt.NDArray[np.float32] = np.array(time_series.values)
        if not min_within_bound_threshold and (not max_within_bound_threshold):
            return None
        if min_within_bound_threshold is None:
            min_within_bound_threshold = float(-np.inf)
        if max_within_bound_threshold is None:
            max_within_bound_threshold = float(np.inf)
        ego_pose_value_within_bound = (ego_pose_values > min_within_bound_threshold) & (ego_pose_values < max_within_bound_threshold)
        return bool(np.all(ego_pose_value_within_bound))

    def _compute_statistics(self, history: SimulationHistory, scenario: AbstractScenario, statistic_unit_name: str, extract_function: Any, extract_function_params: Dict[str, Any], min_within_bound_threshold: Optional[float]=None, max_within_bound_threshold: Optional[float]=None) -> List[MetricStatistics]:
        """
        Compute metrics following the same structure
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :param statistic_unit_name: Statistic unit name
        :param extract_function: Function used to extract certain values
        :param extract_function_params: Params used in extract_function
        :param min_within_bound_threshold: Minimum threshold to check if value is within bound
        :param max_within_bound_threshold: Maximum threshold to check if value is within bound.
        """
        ego_pose_states = history.extract_ego_state
        ego_pose_values = extract_function(ego_pose_states, **extract_function_params)
        ego_pose_timestamps = extract_ego_time_point(ego_pose_states)
        time_series = TimeSeries(unit=statistic_unit_name, time_stamps=list(ego_pose_timestamps), values=list(ego_pose_values))
        statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
        metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
        self.within_bound_status = self._compute_within_bound(time_series=time_series, min_within_bound_threshold=min_within_bound_threshold, max_within_bound_threshold=max_within_bound_threshold)
        if self.within_bound_status is not None:
            metric_statistics.append(Statistic(name=f'abs_{self.name}_within_bounds', unit=MetricStatisticsType.BOOLEAN.unit, value=self.within_bound_status, type=MetricStatisticsType.BOOLEAN))
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, time_series=time_series, scenario=scenario)
        return results

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated metric.
        """
        raise NotImplementedError

def _compute_statistics(self, history: SimulationHistory, scenario: AbstractScenario, statistic_unit_name: str, extract_function: Any, extract_function_params: Dict[str, Any], min_within_bound_threshold: Optional[float]=None, max_within_bound_threshold: Optional[float]=None) -> List[MetricStatistics]:
    """
        Compute metrics following the same structure
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :param statistic_unit_name: Statistic unit name
        :param extract_function: Function used to extract certain values
        :param extract_function_params: Params used in extract_function
        :param min_within_bound_threshold: Minimum threshold to check if value is within bound
        :param max_within_bound_threshold: Maximum threshold to check if value is within bound.
        """
    ego_pose_states = history.extract_ego_state
    ego_pose_values = extract_function(ego_pose_states, **extract_function_params)
    ego_pose_timestamps = extract_ego_time_point(ego_pose_states)
    time_series = TimeSeries(unit=statistic_unit_name, time_stamps=list(ego_pose_timestamps), values=list(ego_pose_values))
    statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MIN, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
    metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
    self.within_bound_status = self._compute_within_bound(time_series=time_series, min_within_bound_threshold=min_within_bound_threshold, max_within_bound_threshold=max_within_bound_threshold)
    if self.within_bound_status is not None:
        metric_statistics.append(Statistic(name=f'abs_{self.name}_within_bounds', unit=MetricStatisticsType.BOOLEAN.unit, value=self.within_bound_status, type=MetricStatisticsType.BOOLEAN))
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, time_series=time_series, scenario=scenario)
    return results

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

def _create_mock_violation(self, metric_name: str, duration: int, extremum: float, mean: float) -> MetricViolation:
    """Creates a simple violation
        :param metric_name: name of the metric
        :param duration: duration of the violation
        :param extremum: maximally violating value
        :param mean: mean value of violation depth
        :return: a MetricViolation with the given parameters.
        """
    return MetricViolation(metric_computator=self.violation_metric_base.name, name=metric_name, metric_category=self.violation_metric_base.category, unit='unit', start_timestamp=0, duration=duration, extremum=extremum, mean=mean)

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

class EgoProgressAlongExpertRouteStatistics(MetricBase):
    """Ego progress along the expert route metric."""

    def __init__(self, name: str, category: str, score_progress_threshold: float=2, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializes the EgoProgressAlongExpertRouteStatistics class
        :param name: Metric name
        :param category: Metric category
        :param score_progress_threshold: Progress distance threshold for the score.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._score_progress_threshold = score_progress_threshold
        self.results: List[MetricStatistics] = []

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[-1].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the ego progress along the expert route metric
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric
        :return: Ego progress along expert route statistics.
        """
        ego_states = history.extract_ego_state
        ego_poses = extract_ego_center(ego_states)
        expert_states = scenario.get_expert_ego_trajectory()
        expert_poses = extract_ego_center(expert_states)
        expert_route = get_route(map_api=history.map_api, poses=expert_poses)
        expert_route_simplified = get_route_simplified(expert_route)
        if not expert_route_simplified:
            statistics = [Statistic(name='expert_total_progress_along_route', unit='meters', value=0.0, type=MetricStatisticsType.VALUE), Statistic(name='ego_expert_progress_along_route_ratio', unit=MetricStatisticsType.RATIO.unit, value=1.0, type=MetricStatisticsType.RATIO)]
            self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario)
        else:
            route_baseline_roadblock_pairs = get_route_baseline_roadblock_linkedlist(history.map_api, expert_route_simplified)
            ego_progress_computer = PerFrameProgressAlongRouteComputer(route_roadblocks=route_baseline_roadblock_pairs)
            ego_progress = ego_progress_computer(ego_poses=ego_poses)
            overall_ego_progress = np.sum(ego_progress)
            expert_progress_computer = PerFrameProgressAlongRouteComputer(route_roadblocks=route_baseline_roadblock_pairs)
            expert_progress = expert_progress_computer(ego_poses=expert_poses)
            overall_expert_progress = np.sum(expert_progress)
            if overall_ego_progress < -self._score_progress_threshold:
                ego_expert_progress_along_route_ratio = 0
            else:
                ego_expert_progress_along_route_ratio = min(1.0, max(overall_ego_progress, self._score_progress_threshold) / max(overall_expert_progress, self._score_progress_threshold))
            ego_timestamps = extract_ego_time_point(ego_states)
            time_series = TimeSeries(unit='meters', time_stamps=list(ego_timestamps), values=list(ego_progress))
            statistics = [Statistic(name='expert_total_progress_along_route', unit='meters', value=float(overall_expert_progress), type=MetricStatisticsType.VALUE), Statistic(name='ego_total_progress_along_route', unit='meters', value=float(overall_ego_progress), type=MetricStatisticsType.VALUE), Statistic(name='ego_expert_progress_along_route_ratio', unit=MetricStatisticsType.RATIO.unit, value=ego_expert_progress_along_route_ratio, type=MetricStatisticsType.RATIO)]
            self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
        return self.results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the ego progress along the expert route metric
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric
        :return: Ego progress along expert route statistics.
        """
    ego_states = history.extract_ego_state
    ego_poses = extract_ego_center(ego_states)
    expert_states = scenario.get_expert_ego_trajectory()
    expert_poses = extract_ego_center(expert_states)
    expert_route = get_route(map_api=history.map_api, poses=expert_poses)
    expert_route_simplified = get_route_simplified(expert_route)
    if not expert_route_simplified:
        statistics = [Statistic(name='expert_total_progress_along_route', unit='meters', value=0.0, type=MetricStatisticsType.VALUE), Statistic(name='ego_expert_progress_along_route_ratio', unit=MetricStatisticsType.RATIO.unit, value=1.0, type=MetricStatisticsType.RATIO)]
        self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario)
    else:
        route_baseline_roadblock_pairs = get_route_baseline_roadblock_linkedlist(history.map_api, expert_route_simplified)
        ego_progress_computer = PerFrameProgressAlongRouteComputer(route_roadblocks=route_baseline_roadblock_pairs)
        ego_progress = ego_progress_computer(ego_poses=ego_poses)
        overall_ego_progress = np.sum(ego_progress)
        expert_progress_computer = PerFrameProgressAlongRouteComputer(route_roadblocks=route_baseline_roadblock_pairs)
        expert_progress = expert_progress_computer(ego_poses=expert_poses)
        overall_expert_progress = np.sum(expert_progress)
        if overall_ego_progress < -self._score_progress_threshold:
            ego_expert_progress_along_route_ratio = 0
        else:
            ego_expert_progress_along_route_ratio = min(1.0, max(overall_ego_progress, self._score_progress_threshold) / max(overall_expert_progress, self._score_progress_threshold))
        ego_timestamps = extract_ego_time_point(ego_states)
        time_series = TimeSeries(unit='meters', time_stamps=list(ego_timestamps), values=list(ego_progress))
        statistics = [Statistic(name='expert_total_progress_along_route', unit='meters', value=float(overall_expert_progress), type=MetricStatisticsType.VALUE), Statistic(name='ego_total_progress_along_route', unit='meters', value=float(overall_ego_progress), type=MetricStatisticsType.VALUE), Statistic(name='ego_expert_progress_along_route_ratio', unit=MetricStatisticsType.RATIO.unit, value=ego_expert_progress_along_route_ratio, type=MetricStatisticsType.RATIO)]
        self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
    return self.results

class PlannerExpertAverageHeadingErrorStatistics(MetricBase):
    """
    Average of absolute difference between planned ego heading and expert heading given a comparison time horizon.
    """

    def __init__(self, name: str, category: str, planner_expert_average_l2_error_within_bound_metric: PlannerExpertAverageL2ErrorStatistics, max_average_heading_error_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the PlannerExpertAverageHeadingErrorStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param planner_expert_average_l2_error_within_bound_metric: planner_expert_average_l2_error_within_bound metric.
        :param max_average_heading_error_threshold: Maximum acceptable heading error threshold
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._max_average_heading_error_threshold = max_average_heading_error_threshold
        self._planner_expert_average_l2_error_within_bound_metric = planner_expert_average_l2_error_within_bound_metric

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(max(0, 1 - metric_statistics[-1].value / self._max_average_heading_error_threshold))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
        average_heading_errors = self._planner_expert_average_l2_error_within_bound_metric.average_heading_errors
        ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
        selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
        comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
        results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_average_heading_error_threshold, metric_values=average_heading_errors, name='planner_expert_AHE', unit='radian', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
        return results

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(max(0, 1 - metric_statistics[-1].value / self._max_average_heading_error_threshold))

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
    average_heading_errors = self._planner_expert_average_l2_error_within_bound_metric.average_heading_errors
    ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
    selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
    comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
    results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_average_heading_error_threshold, metric_values=average_heading_errors, name='planner_expert_AHE', unit='radian', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
    return results

class PlannerExpertFinalHeadingErrorStatistics(MetricBase):
    """
    Absolute difference between planned ego heading and expert heading at the final pose given a comparison time horizon.
    """

    def __init__(self, name: str, category: str, planner_expert_average_l2_error_within_bound_metric: PlannerExpertAverageL2ErrorStatistics, max_final_heading_error_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the PlannerExpertFinalHeadingErrorStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param planner_expert_average_l2_error_within_bound_metric: planner_expert_average_l2_error_within_bound metric.
        :param max_final_heading_error_threshold: Maximum acceptable error threshold.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._planner_expert_average_l2_error_within_bound_metric = planner_expert_average_l2_error_within_bound_metric
        self._max_final_heading_error_threshold = max_final_heading_error_threshold

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(max(0, 1 - metric_statistics[-1].value / self._max_final_heading_error_threshold))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
        final_heading_errors = self._planner_expert_average_l2_error_within_bound_metric.final_heading_errors
        ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
        selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
        comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
        results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_final_heading_error_threshold, metric_values=final_heading_errors, name='planner_expert_FHE', unit='radian', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
        return results

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(max(0, 1 - metric_statistics[-1].value / self._max_final_heading_error_threshold))

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
    final_heading_errors = self._planner_expert_average_l2_error_within_bound_metric.final_heading_errors
    ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
    selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
    comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
    results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_final_heading_error_threshold, metric_values=final_heading_errors, name='planner_expert_FHE', unit='radian', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
    return results

class EgoIsComfortableStatistics(MetricBase):
    """
    Check if ego trajectory is comfortable based on min_ego_lon_acceleration, max_ego_lon_acceleration,
    max_ego_abs_lat_acceleration, max_ego_abs_yaw_rate, max_ego_abs_yaw_acceleration, max_ego_abs_jerk_lon,
    max_ego_abs_jerk.
    """

    def __init__(self, name: str, category: str, ego_jerk_metric: EgoJerkStatistics, ego_lat_acceleration_metric: EgoLatAccelerationStatistics, ego_lon_acceleration_metric: EgoLonAccelerationStatistics, ego_lon_jerk_metric: EgoLonJerkStatistics, ego_yaw_acceleration_metric: EgoYawAccelerationStatistics, ego_yaw_rate_metric: EgoYawRateStatistics, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializes the EgoIsComfortableStatistics class
        :param name: Metric name
        :param category: Metric category
        :param ego_jerk_metric: Ego jerk metric
        :param ego_lat_acceleration_metric: Ego lat acceleration metric
        :param ego_lon_acceleration_metric: Ego lon acceleration metric
        :param ego_lon_jerk_metric: Ego lon jerk metric
        :param ego_yaw_acceleration_metric: Ego yaw acceleration metric
        :param ego_yaw_rate_metric: Ego yaw rate metric.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._comfortability_metrics = [ego_jerk_metric, ego_lat_acceleration_metric, ego_lon_acceleration_metric, ego_lon_jerk_metric, ego_yaw_acceleration_metric, ego_yaw_rate_metric]

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[0].value)

    def check_ego_is_comfortable(self, history: SimulationHistory, scenario: AbstractScenario) -> bool:
        """
        Check if ego trajectory is comfortable
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return Ego comfortable status.
        """
        metrics_results = [metric.within_bound_status for metric in self._comfortability_metrics]
        ego_is_comfortable = bool(np.all(metrics_results))
        return ego_is_comfortable

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        ego_is_comfortable = self.check_ego_is_comfortable(history=history, scenario=scenario)
        statistics = [Statistic(name='ego_is_comfortable', unit=MetricStatisticsType.BOOLEAN.unit, value=ego_is_comfortable, type=MetricStatisticsType.BOOLEAN)]
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
    ego_is_comfortable = self.check_ego_is_comfortable(history=history, scenario=scenario)
    statistics = [Statistic(name='ego_is_comfortable', unit=MetricStatisticsType.BOOLEAN.unit, value=ego_is_comfortable, type=MetricStatisticsType.BOOLEAN)]
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
    return results

class PlannerExpertAverageL2ErrorStatistics(MetricBase):
    """Average displacement error metric between the planned ego pose and expert."""

    def __init__(self, name: str, category: str, comparison_horizon: List[int], comparison_frequency: int, max_average_l2_error_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the PlannerExpertL2ErrorStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param comparison_horizon: List of horizon times in future (s) to find displacement errors.
        :param comparison_frequency: Frequency to sample expert and planner trajectory.
        :param max_average_l2_error_threshold: Maximum acceptable error threshold.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self.comparison_horizon = comparison_horizon
        self._comparison_frequency = comparison_frequency
        self._max_average_l2_error_threshold = max_average_l2_error_threshold
        self.maximum_displacement_errors: npt.NDArray[np.float64] = np.array([0])
        self.final_displacement_errors: npt.NDArray[np.float64] = np.array([0])
        self.expert_timestamps_sampled: List[int] = []
        self.average_heading_errors: npt.NDArray[np.float64] = np.array([0])
        self.final_heading_errors: npt.NDArray[np.float64] = np.array([0])
        self.selected_frames: List[int] = [0]

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(max(0, 1 - metric_statistics[-1].value / self._max_average_l2_error_threshold))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
        expert_frequency = 1 / scenario.database_interval
        step_size = int(expert_frequency / self._comparison_frequency)
        sampled_indices = list(range(0, len(history.data), step_size))
        expert_states = list(itertools.chain(list(scenario.get_expert_ego_trajectory())[0::step_size], scenario.get_ego_future_trajectory(sampled_indices[-1], max(self.comparison_horizon), max(self.comparison_horizon) // self._comparison_frequency)))
        expert_traj_poses = extract_ego_center_with_heading(expert_states)
        expert_timestamps_sampled = extract_ego_time_point(expert_states)
        planned_trajectories = list((history.data[index].trajectory for index in sampled_indices))
        average_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
        maximum_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
        final_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
        average_heading_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
        final_heading_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
        for curr_frame, curr_ego_planned_traj in enumerate(planned_trajectories):
            future_horizon_frame = int(curr_frame + max(self.comparison_horizon))
            planner_interpolated_traj = list((curr_ego_planned_traj.get_state_at_time(TimePoint(int(timestamp))) for timestamp in expert_timestamps_sampled[curr_frame:future_horizon_frame + 1] if timestamp <= curr_ego_planned_traj.end_time.time_us))
            if len(planner_interpolated_traj) < max(self.comparison_horizon) + 1:
                planner_interpolated_traj = list(itertools.chain(planner_interpolated_traj, [curr_ego_planned_traj.get_sampled_trajectory()[-1]]))
                expert_traj = expert_traj_poses[curr_frame + 1:future_horizon_frame] + [InterpolatedTrajectory(expert_states).get_state_at_time(curr_ego_planned_traj.end_time).center]
            else:
                expert_traj = expert_traj_poses[curr_frame + 1:future_horizon_frame + 1]
            planner_interpolated_traj_poses = extract_ego_center_with_heading(planner_interpolated_traj)
            displacement_errors = compute_traj_errors(planner_interpolated_traj_poses[1:], expert_traj, heading_diff_weight=0)
            heading_errors = compute_traj_heading_errors(planner_interpolated_traj_poses[1:], expert_traj)
            for ind, horizon in enumerate(self.comparison_horizon):
                horizon_index = horizon // self._comparison_frequency
                average_displacement_errors[ind, curr_frame] = np.mean(displacement_errors[:horizon_index])
                maximum_displacement_errors[ind, curr_frame] = np.max(displacement_errors[:horizon_index])
                final_displacement_errors[ind, curr_frame] = displacement_errors[horizon_index - 1]
                average_heading_errors[ind, curr_frame] = np.mean(heading_errors[:horizon_index])
                final_heading_errors[ind, curr_frame] = heading_errors[horizon_index - 1]
        self.ego_timestamps_sampled = expert_timestamps_sampled[:len(sampled_indices)]
        self.selected_frames = sampled_indices
        results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, self.comparison_horizon, self._max_average_l2_error_threshold, metric_values=average_displacement_errors, name='planner_expert_ADE', unit='meter', timestamps_sampled=self.ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=sampled_indices)
        self.maximum_displacement_errors = maximum_displacement_errors
        self.final_displacement_errors = final_displacement_errors
        self.average_heading_errors = average_heading_errors
        self.final_heading_errors = final_heading_errors
        return results

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(max(0, 1 - metric_statistics[-1].value / self._max_average_l2_error_threshold))

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
    expert_frequency = 1 / scenario.database_interval
    step_size = int(expert_frequency / self._comparison_frequency)
    sampled_indices = list(range(0, len(history.data), step_size))
    expert_states = list(itertools.chain(list(scenario.get_expert_ego_trajectory())[0::step_size], scenario.get_ego_future_trajectory(sampled_indices[-1], max(self.comparison_horizon), max(self.comparison_horizon) // self._comparison_frequency)))
    expert_traj_poses = extract_ego_center_with_heading(expert_states)
    expert_timestamps_sampled = extract_ego_time_point(expert_states)
    planned_trajectories = list((history.data[index].trajectory for index in sampled_indices))
    average_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
    maximum_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
    final_displacement_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
    average_heading_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
    final_heading_errors = np.zeros((len(self.comparison_horizon), len(sampled_indices)))
    for curr_frame, curr_ego_planned_traj in enumerate(planned_trajectories):
        future_horizon_frame = int(curr_frame + max(self.comparison_horizon))
        planner_interpolated_traj = list((curr_ego_planned_traj.get_state_at_time(TimePoint(int(timestamp))) for timestamp in expert_timestamps_sampled[curr_frame:future_horizon_frame + 1] if timestamp <= curr_ego_planned_traj.end_time.time_us))
        if len(planner_interpolated_traj) < max(self.comparison_horizon) + 1:
            planner_interpolated_traj = list(itertools.chain(planner_interpolated_traj, [curr_ego_planned_traj.get_sampled_trajectory()[-1]]))
            expert_traj = expert_traj_poses[curr_frame + 1:future_horizon_frame] + [InterpolatedTrajectory(expert_states).get_state_at_time(curr_ego_planned_traj.end_time).center]
        else:
            expert_traj = expert_traj_poses[curr_frame + 1:future_horizon_frame + 1]
        planner_interpolated_traj_poses = extract_ego_center_with_heading(planner_interpolated_traj)
        displacement_errors = compute_traj_errors(planner_interpolated_traj_poses[1:], expert_traj, heading_diff_weight=0)
        heading_errors = compute_traj_heading_errors(planner_interpolated_traj_poses[1:], expert_traj)
        for ind, horizon in enumerate(self.comparison_horizon):
            horizon_index = horizon // self._comparison_frequency
            average_displacement_errors[ind, curr_frame] = np.mean(displacement_errors[:horizon_index])
            maximum_displacement_errors[ind, curr_frame] = np.max(displacement_errors[:horizon_index])
            final_displacement_errors[ind, curr_frame] = displacement_errors[horizon_index - 1]
            average_heading_errors[ind, curr_frame] = np.mean(heading_errors[:horizon_index])
            final_heading_errors[ind, curr_frame] = heading_errors[horizon_index - 1]
    self.ego_timestamps_sampled = expert_timestamps_sampled[:len(sampled_indices)]
    self.selected_frames = sampled_indices
    results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, self.comparison_horizon, self._max_average_l2_error_threshold, metric_values=average_displacement_errors, name='planner_expert_ADE', unit='meter', timestamps_sampled=self.ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=sampled_indices)
    self.maximum_displacement_errors = maximum_displacement_errors
    self.final_displacement_errors = final_displacement_errors
    self.average_heading_errors = average_heading_errors
    self.final_heading_errors = final_heading_errors
    return results

class EgoAtFaultCollisionStatistics(MetricBase):
    """
    Statistics on number and energy of collisions of ego.
    A collision is defined as the event of ego intersecting another bounding box. If the same collision lasts for
    multiple frames, it still counts as a single one.
    """

    def __init__(self, name: str, category: str, ego_lane_change_metric: EgoLaneChangeStatistics, max_violation_threshold_vru: int=0, max_violation_threshold_vehicle: int=0, max_violation_threshold_object: int=1, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the EgoAtFaultCollisionStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param ego_lane_change_metric: Lane change metric computed prior to calling the current metric.
        :param max_violation_threshold_vru: Maximum threshold for the collision with VRUs.
        :param max_violation_threshold_vehicle: Maximum threshold for the collision with vehicles.
        :param max_violation_threshold_object: Maximum threshold for the collision with objects.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._max_violation_threshold_vru = max_violation_threshold_vru
        self._max_violation_threshold_vehicle = max_violation_threshold_vehicle
        self._max_violation_threshold_object = max_violation_threshold_object
        self.results: List[MetricStatistics] = []
        self.all_collisions: List[Collisions] = []
        self.all_at_fault_collisions: Dict[TrackedObjectType, List[float]] = defaultdict(list)
        self.timestamps_at_fault_collisions: List[int] = []
        self._ego_lane_change_metric = ego_lane_change_metric

    def _compute_collision_score(self, number_of_collisions: int, max_violation_threshold: int) -> float:
        """
        Compute a score based on a maximum violation threshold. The score is max( 0, 1 - (x / (max_violation_threshold + 1)))
        The score will be 0 if the number of collisions exceeds this value.
        :param max_violation_threshold: Total number of allowed collisions.
        :return A metric score between 0 and 1.
        """
        return max(0.0, 1.0 - number_of_collisions / (max_violation_threshold + 1))

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> Optional[float]:
        """Inherited, see superclass.
        The total score for this metric is defined as the product of the scores for VRUs, vehicles and object track types. If no at fault collision exist, the score is 1.
        """
        return 1 if metric_statistics[0].value else self._compute_collision_score(metric_statistics[2].value, self._max_violation_threshold_vru) * self._compute_collision_score(metric_statistics[3].value, self._max_violation_threshold_vehicle) * self._compute_collision_score(metric_statistics[4].value, self._max_violation_threshold_object)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the collision metric.
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated collision energy and counts.
        """
        assert self._ego_lane_change_metric.results, 'ego_lane_change_metric must be run prior to calling {}'.format(self.name)
        timestamps_in_common_or_connected_route_objs: List[int] = self._ego_lane_change_metric.timestamps_in_common_or_connected_route_objs
        all_collisions: List[Collisions] = []
        collided_track_ids: Set[str] = set()
        for sample in history.data:
            ego_state = sample.ego_state
            observation = sample.observation
            timestamp = ego_state.time_point.time_us
            collided_track_ids, collisions_id_data = find_new_collisions(ego_state, observation, collided_track_ids)
            if len(collisions_id_data):
                all_collisions.append(Collisions(timestamp, collisions_id_data))
        self.timestamps_at_fault_collisions, self.all_at_fault_collisions = classify_at_fault_collisions(all_collisions, timestamps_in_common_or_connected_route_objs)
        number_of_at_fault_collisions = sum((len(track_collisions) for track_collisions in self.all_at_fault_collisions.values()))
        statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=number_of_at_fault_collisions == 0, type=MetricStatisticsType.BOOLEAN), Statistic(name='number_of_all_at_fault_collisions', unit=MetricStatisticsType.COUNT.unit, value=number_of_at_fault_collisions, type=MetricStatisticsType.COUNT)]
        statistics.extend(get_fault_type_statistics(self.all_at_fault_collisions))
        self.results = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
        self.all_collisions = all_collisions
        return self.results

def _compute_collision_score(self, number_of_collisions: int, max_violation_threshold: int) -> float:
    """
        Compute a score based on a maximum violation threshold. The score is max( 0, 1 - (x / (max_violation_threshold + 1)))
        The score will be 0 if the number of collisions exceeds this value.
        :param max_violation_threshold: Total number of allowed collisions.
        :return A metric score between 0 and 1.
        """
    return max(0.0, 1.0 - number_of_collisions / (max_violation_threshold + 1))

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the collision metric.
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated collision energy and counts.
        """
    assert self._ego_lane_change_metric.results, 'ego_lane_change_metric must be run prior to calling {}'.format(self.name)
    timestamps_in_common_or_connected_route_objs: List[int] = self._ego_lane_change_metric.timestamps_in_common_or_connected_route_objs
    all_collisions: List[Collisions] = []
    collided_track_ids: Set[str] = set()
    for sample in history.data:
        ego_state = sample.ego_state
        observation = sample.observation
        timestamp = ego_state.time_point.time_us
        collided_track_ids, collisions_id_data = find_new_collisions(ego_state, observation, collided_track_ids)
        if len(collisions_id_data):
            all_collisions.append(Collisions(timestamp, collisions_id_data))
    self.timestamps_at_fault_collisions, self.all_at_fault_collisions = classify_at_fault_collisions(all_collisions, timestamps_in_common_or_connected_route_objs)
    number_of_at_fault_collisions = sum((len(track_collisions) for track_collisions in self.all_at_fault_collisions.values()))
    statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=number_of_at_fault_collisions == 0, type=MetricStatisticsType.BOOLEAN), Statistic(name='number_of_all_at_fault_collisions', unit=MetricStatisticsType.COUNT.unit, value=number_of_at_fault_collisions, type=MetricStatisticsType.COUNT)]
    statistics.extend(get_fault_type_statistics(self.all_at_fault_collisions))
    self.results = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
    self.all_collisions = all_collisions
    return self.results

class SpeedLimitViolationExtractor:
    """Class to extract speed limit violations."""

    def __init__(self, history: SimulationHistory, metric_name: str, category: str) -> None:
        """
        Initializes the SpeedLimitViolationExtractor class
        :param history: History from a simulation engine
        :param metric_name: Metric name
        :param category: Metric category.
        """
        self.history = history
        self.open_violation: Optional[GenericViolation] = None
        self.violations: List[MetricViolation] = []
        self.violation_depths: List[float] = []
        self.metric_name = metric_name
        self.category = category

    def extract_metric(self, ego_route: List[List[GraphEdgeMapObject]]) -> None:
        """Extracts the drivable area violations from the history of Ego poses."""
        timestamp = None
        for sample, curr_ego_route in zip(self.history.data, ego_route):
            ego_state = sample.ego_state
            timestamp = ego_state.time_point.time_us
            if not curr_ego_route:
                violation = None
            else:
                violation = self._get_speed_limit_violation(ego_state, timestamp, curr_ego_route)
            if violation:
                if not self.open_violation:
                    self.start_violation(violation)
                else:
                    self.update_violation(violation)
                self.violation_depths.append(violation.violation_depths[0])
            else:
                self.violation_depths.append(0)
                if self.open_violation:
                    self.end_violation(timestamp, higher_is_worse=True)
        if timestamp and self.open_violation:
            self.end_violation(timestamp)

    def start_violation(self, violation: GenericViolation) -> None:
        """
        Opens the violation window of the given IDs, as they now starting to violate the metric
        :param violation: The current violation.
        """
        self.open_violation = violation

    def update_violation(self, violation: GenericViolation) -> None:
        """
        Updates the violation if the maximum depth of violation is greater than the current maximum
        :param violation: The current violation.
        """
        assert isinstance(self.open_violation, GenericViolation), 'There is no open violation, cannot update it!'
        self.open_violation.violation_depths.extend(violation.violation_depths)

    def end_violation(self, timestamp: int, higher_is_worse: bool=True) -> None:
        """
        Closes the violation window, as Ego re-enters the non-violating regime
        :param timestamp: The current timestamp
        :param higher_is_worse: True if the violation gravity is monotonic increasing with violation depth.
        """
        assert isinstance(self.open_violation, GenericViolation), 'There is no open violation, cannot end it!'
        maximal_violation = max(self.open_violation.violation_depths) if higher_is_worse else min(self.open_violation.violation_depths)
        self.violations.append(MetricViolation(name='speed_limit_violation', metric_computator=self.metric_name, metric_category=self.category, unit='meters_per_second', start_timestamp=self.open_violation.timestamp, duration=timestamp - self.open_violation.timestamp, extremum=maximal_violation, mean=statistics.mean(self.open_violation.violation_depths)))
        self.open_violation = None

    @staticmethod
    def _get_speed_limit_violation(ego_state: EgoState, timestamp: int, ego_lane_or_laneconnector: List[GraphEdgeMapObject]) -> Optional[GenericViolation]:
        """
        Computes by how much ego is exceeding the speed limit
        :param ego_state: The current state of Ego
        :param timestamp: The current timestamp
        :return: By how much ego is exceeding the speed limit, none if not violation is present or unable to find
        the speed limit.
        """
        if isinstance(ego_lane_or_laneconnector[0], Lane):
            assert len(ego_lane_or_laneconnector) == 1, 'Ego should can assigned to one lane only'
            speed_limits = [ego_lane_or_laneconnector[0].speed_limit_mps]
        else:
            speed_limits = []
            for map_obj in ego_lane_or_laneconnector:
                edges = map_obj.outgoing_edges + map_obj.incoming_edges
                speed_limits.extend([lane.speed_limit_mps for lane in edges])
        if all(speed_limits):
            max_speed_limit = max(speed_limits)
            exceeding_speed = ego_state.dynamic_car_state.speed - max_speed_limit
            return GenericViolation(timestamp, violation_depths=[exceeding_speed]) if exceeding_speed > 0 else None
        return None

def update_violation(self, violation: GenericViolation) -> None:
    """
        Updates the violation if the maximum depth of violation is greater than the current maximum
        :param violation: The current violation.
        """
    assert isinstance(self.open_violation, GenericViolation), 'There is no open violation, cannot update it!'
    self.open_violation.violation_depths.extend(violation.violation_depths)

def end_violation(self, timestamp: int, higher_is_worse: bool=True) -> None:
    """
        Closes the violation window, as Ego re-enters the non-violating regime
        :param timestamp: The current timestamp
        :param higher_is_worse: True if the violation gravity is monotonic increasing with violation depth.
        """
    assert isinstance(self.open_violation, GenericViolation), 'There is no open violation, cannot end it!'
    maximal_violation = max(self.open_violation.violation_depths) if higher_is_worse else min(self.open_violation.violation_depths)
    self.violations.append(MetricViolation(name='speed_limit_violation', metric_computator=self.metric_name, metric_category=self.category, unit='meters_per_second', start_timestamp=self.open_violation.timestamp, duration=timestamp - self.open_violation.timestamp, extremum=maximal_violation, mean=statistics.mean(self.open_violation.violation_depths)))
    self.open_violation = None

@staticmethod
def _get_speed_limit_violation(ego_state: EgoState, timestamp: int, ego_lane_or_laneconnector: List[GraphEdgeMapObject]) -> Optional[GenericViolation]:
    """
        Computes by how much ego is exceeding the speed limit
        :param ego_state: The current state of Ego
        :param timestamp: The current timestamp
        :return: By how much ego is exceeding the speed limit, none if not violation is present or unable to find
        the speed limit.
        """
    if isinstance(ego_lane_or_laneconnector[0], Lane):
        assert len(ego_lane_or_laneconnector) == 1, 'Ego should can assigned to one lane only'
        speed_limits = [ego_lane_or_laneconnector[0].speed_limit_mps]
    else:
        speed_limits = []
        for map_obj in ego_lane_or_laneconnector:
            edges = map_obj.outgoing_edges + map_obj.incoming_edges
            speed_limits.extend([lane.speed_limit_mps for lane in edges])
    if all(speed_limits):
        max_speed_limit = max(speed_limits)
        exceeding_speed = ego_state.dynamic_car_state.speed - max_speed_limit
        return GenericViolation(timestamp, violation_depths=[exceeding_speed]) if exceeding_speed > 0 else None
    return None

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

class DrivableAreaComplianceStatistics(MetricBase):
    """Statistics on drivable area compliance of ego."""

    def __init__(self, name: str, category: str, lane_change_metric: EgoLaneChangeStatistics, max_violation_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the DrivableAreaComplianceStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param lane_change_metric: lane change metric.
        :param max_violation_threshold: [m] tolerance threshold.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self.results: List[MetricStatistics] = []
        self._lane_change_metric = lane_change_metric
        self._max_violation_threshold = max_violation_threshold

    @staticmethod
    def not_in_drivable_area_with_route_object(pose: Point2D, route_object: List[GraphEdgeMapObject], map_api: AbstractMap) -> bool:
        """
        Return a boolean is_in_drivable_area.
        :param pose: pose.
        :param route_object: lane/lane connector of that pose or empty list.
        :param map_api: map.
        :return: a boolean is_in_drivable_area.
        """
        return not route_object and (not map_api.is_in_layer(pose, layer=SemanticMapLayer.DRIVABLE_AREA))

    @staticmethod
    def compute_distance_to_map_objects_list(pose: Point2D, map_objects: List[GraphEdgeMapObject]) -> float:
        """
        Compute the min distance to a list of map objects.
        :param pose: pose.
        :param map_objects: list of map objects.
        :return: distance.
        """
        return float(min((obj.polygon.distance(Point(*pose)) for obj in map_objects)))

    def is_corner_far_from_drivable_area(self, map_api: AbstractMap, center_lane_lane_connector: List[GraphEdgeMapObject], ego_corner: Point2D) -> bool:
        """
        Return a boolean that shows if ego_corner is far from drivable area according to the threshold.
        :param map_api: map api.
        :param center_lane_lane_connector: ego's center route obj in iteration.
        :param ego_corner: one of ego's corners.
        :return: boolean is_corner_far_from_drivable_area.
        """
        if center_lane_lane_connector:
            distance = self.compute_distance_to_map_objects_list(ego_corner, center_lane_lane_connector)
            if distance < self._max_violation_threshold:
                return False
        id_distance_tuple = map_api.get_distance_to_nearest_map_object(ego_corner, layer=SemanticMapLayer.DRIVABLE_AREA)
        return id_distance_tuple[1] is None or id_distance_tuple[1] >= self._max_violation_threshold

    def compute_violation_for_iteration(self, map_api: AbstractMap, ego_corners: List[Point2D], corners_lane_lane_connector: CornersGraphEdgeMapObject, center_lane_lane_connector: List[GraphEdgeMapObject], far_from_drivable_area: bool) -> Tuple[bool, bool]:
        """
        Compute violation of drivable area for an iteration.
        :param map_api: map api.
        :param ego_corners: 4 corners of ego (FL, RL, RR, FR) in iteration.
        :param corners_lane_lane_connector: object holding corners route objects.
        :param center_lane_lane_connector: ego's center route obj in iteration.
        :param far_from_drivable_area: boolean showing if ego got far from drivable_area in a previous iteration.
        :return: booleans not_in_drivable_area, far_from_drivable_area.
        """
        outside_drivable_area_objs = [ind for ind, obj in enumerate(corners_lane_lane_connector) if self.not_in_drivable_area_with_route_object(ego_corners[ind], obj, map_api)]
        not_in_drivable_area = len(outside_drivable_area_objs) > 0
        far_from_drivable_area = far_from_drivable_area or any((self.is_corner_far_from_drivable_area(map_api, center_lane_lane_connector, ego_corners[ind]) for ind in outside_drivable_area_objs))
        return (not_in_drivable_area, far_from_drivable_area)

    def extract_metric(self, history: SimulationHistory) -> Tuple[List[float], bool]:
        """
        Extract the drivable area violations from the history of Ego poses to evaluate drivable area compliance.
        :param history: SimulationHistory.
        :param corners_lane_lane_connector_list: List of corners lane and lane connectors.
        :return: list of float that shows if corners are in drivable area.
        """
        ego_states = history.extract_ego_state
        map_api = history.map_api
        all_ego_corners = extract_ego_corners(ego_states)
        corners_lane_lane_connector_list = self._lane_change_metric.corners_route
        center_route = self._lane_change_metric.ego_driven_route
        corners_in_drivable_area = []
        far_from_drivable_area = False
        for ego_corners, corners_lane_lane_connector, center_lane_lane_connector in zip(all_ego_corners, corners_lane_lane_connector_list, center_route):
            not_in_drivable_area, far_from_drivable_area = self.compute_violation_for_iteration(map_api, ego_corners, corners_lane_lane_connector, center_lane_lane_connector, far_from_drivable_area)
            corners_in_drivable_area.append(float(not not_in_drivable_area))
        return (corners_in_drivable_area, far_from_drivable_area)

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[0].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return: the estimated metric.
        """
        corners_in_drivable_area, far_from_drivable_area = self.extract_metric(history=history)
        statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=float(not far_from_drivable_area), type=MetricStatisticsType.BOOLEAN)]
        self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, metric_score_unit=self._metric_score_unit)
        time_stamps = extract_ego_time_point(history.extract_ego_state)
        time_series = TimeSeries(unit='boolean', time_stamps=list(time_stamps), values=corners_in_drivable_area)
        corners_statistics = [Statistic(name='corners_in_drivable_area', unit=MetricStatisticsType.BOOLEAN.unit, value=float(np.all(corners_in_drivable_area)), type=MetricStatisticsType.BOOLEAN)]
        corners_statistics_result = MetricStatistics(metric_computator=self.name, name='corners_in_drivable_area', statistics=corners_statistics, time_series=time_series, metric_category=self.category)
        self.results.append(corners_statistics_result)
        return self.results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return: the estimated metric.
        """
    corners_in_drivable_area, far_from_drivable_area = self.extract_metric(history=history)
    statistics = [Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=float(not far_from_drivable_area), type=MetricStatisticsType.BOOLEAN)]
    self.results = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, metric_score_unit=self._metric_score_unit)
    time_stamps = extract_ego_time_point(history.extract_ego_state)
    time_series = TimeSeries(unit='boolean', time_stamps=list(time_stamps), values=corners_in_drivable_area)
    corners_statistics = [Statistic(name='corners_in_drivable_area', unit=MetricStatisticsType.BOOLEAN.unit, value=float(np.all(corners_in_drivable_area)), type=MetricStatisticsType.BOOLEAN)]
    corners_statistics_result = MetricStatistics(metric_computator=self.name, name='corners_in_drivable_area', statistics=corners_statistics, time_series=time_series, metric_category=self.category)
    self.results.append(corners_statistics_result)
    return self.results

class EgoExpertL2ErrorStatistics(MetricBase):
    """Ego pose L2 error metric w.r.t expert."""

    def __init__(self, name: str, category: str, discount_factor: float) -> None:
        """
        Initializes the EgoExpertL2ErrorStatistics class
        :param name: Metric name
        :param category: Metric category
        :param discount_factor: Displacement at step i is discounted by discount_factor^i.
        """
        super().__init__(name=name, category=category)
        self._discount_factor = discount_factor

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        ego_states = history.extract_ego_state
        expert_states = scenario.get_expert_ego_trajectory()
        ego_traj = extract_ego_center(ego_states)
        expert_traj = extract_ego_center(expert_states)
        error = compute_traj_errors(ego_traj=ego_traj, expert_traj=expert_traj, discount_factor=self._discount_factor)
        ego_timestamps = extract_ego_time_point(ego_states)
        statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
        time_series = TimeSeries(unit='meters', time_stamps=list(ego_timestamps), values=list(error))
        metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, time_series=time_series)
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
    ego_states = history.extract_ego_state
    expert_states = scenario.get_expert_ego_trajectory()
    ego_traj = extract_ego_center(ego_states)
    expert_traj = extract_ego_center(expert_states)
    error = compute_traj_errors(ego_traj=ego_traj, expert_traj=expert_traj, discount_factor=self._discount_factor)
    ego_timestamps = extract_ego_time_point(ego_states)
    statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
    time_series = TimeSeries(unit='meters', time_stamps=list(ego_timestamps), values=list(error))
    metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, time_series=time_series)
    return results

class PlannerMissRateStatistics(MetricBase):
    """Miss rate defined based on the maximum L2 error of planned ego pose w.r.t expert."""

    def __init__(self, name: str, category: str, planner_expert_average_l2_error_within_bound_metric: PlannerExpertAverageL2ErrorStatistics, max_displacement_threshold: List[float], max_miss_rate_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the PlannerMissRateStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param planner_expert_average_l2_error_within_bound_metric: planner_expert_average_l2_error_within_bound metric for each horizon.
        :param max_displacement_threshold: A List of thresholds at different horizons
        :param max_miss_rate_threshold: maximum acceptable miss rate threshold.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._max_displacement_threshold = max_displacement_threshold
        self._max_miss_rate_threshold = max_miss_rate_threshold
        self._planner_expert_average_l2_error_within_bound_metric = planner_expert_average_l2_error_within_bound_metric

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[-1].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
        maximum_displacement_errors = self._planner_expert_average_l2_error_within_bound_metric.maximum_displacement_errors
        comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
        miss_rates: npt.NDArray[np.float64] = np.array([np.mean(maximum_displacement_errors[i] > self._max_displacement_threshold[i]) for i in range(len(comparison_horizon))])
        metric_statistics = [Statistic(name=f'planner_miss_rate_horizon_{comparison_horizon[ind]}', unit=MetricStatisticsType.RATIO.unit, value=miss_rate, type=MetricStatisticsType.RATIO) for ind, miss_rate in enumerate(miss_rates)]
        metric_statistics.append(Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=float(np.all(miss_rates <= self._max_miss_rate_threshold)), type=MetricStatisticsType.BOOLEAN))
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, metric_score_unit=self.metric_score_unit)
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
    maximum_displacement_errors = self._planner_expert_average_l2_error_within_bound_metric.maximum_displacement_errors
    comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
    miss_rates: npt.NDArray[np.float64] = np.array([np.mean(maximum_displacement_errors[i] > self._max_displacement_threshold[i]) for i in range(len(comparison_horizon))])
    metric_statistics = [Statistic(name=f'planner_miss_rate_horizon_{comparison_horizon[ind]}', unit=MetricStatisticsType.RATIO.unit, value=miss_rate, type=MetricStatisticsType.RATIO) for ind, miss_rate in enumerate(miss_rates)]
    metric_statistics.append(Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=float(np.all(miss_rates <= self._max_miss_rate_threshold)), type=MetricStatisticsType.BOOLEAN))
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, metric_score_unit=self.metric_score_unit)
    return results

class EgoExpertL2ErrorWithYawStatistics(MetricBase):
    """Ego pose and heading L2 error metric w.r.t expert."""

    def __init__(self, name: str, category: str, discount_factor: float, heading_diff_weight: float=2.5) -> None:
        """
        Initializes the EgoExpertL2ErrorWithYawStatistics class
        :param name: Metric name
        :param category: Metric category
        :param discount_factor: Displacement at step i is dicounted by discount_factor^i
        :heading_diff_weight: The weight of heading differences.
        """
        super().__init__(name=name, category=category)
        self._discount_factor = discount_factor
        self._heading_diff_weight = heading_diff_weight

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        ego_states = history.extract_ego_state
        expert_states = scenario.get_expert_ego_trajectory()
        ego_traj = extract_ego_center_with_heading(ego_states)
        expert_traj = extract_ego_center_with_heading(expert_states)
        error = compute_traj_errors(ego_traj=ego_traj, expert_traj=expert_traj, discount_factor=self._discount_factor, heading_diff_weight=self._heading_diff_weight)
        ego_timestamps = extract_ego_time_point(ego_states)
        statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
        time_series = TimeSeries(unit='None', time_stamps=list(ego_timestamps), values=list(error))
        metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, time_series=time_series)
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
    ego_states = history.extract_ego_state
    expert_states = scenario.get_expert_ego_trajectory()
    ego_traj = extract_ego_center_with_heading(ego_states)
    expert_traj = extract_ego_center_with_heading(expert_states)
    error = compute_traj_errors(ego_traj=ego_traj, expert_traj=expert_traj, discount_factor=self._discount_factor, heading_diff_weight=self._heading_diff_weight)
    ego_timestamps = extract_ego_time_point(ego_states)
    statistics_type_list = [MetricStatisticsType.MAX, MetricStatisticsType.MEAN, MetricStatisticsType.P90]
    time_series = TimeSeries(unit='None', time_stamps=list(ego_timestamps), values=list(error))
    metric_statistics = self._compute_time_series_statistic(time_series=time_series, statistics_type_list=statistics_type_list)
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, scenario=scenario, time_series=time_series)
    return results

class TimeToCollisionStatistics(MetricBase):
    """
    Ego time to collision metric, reports the minimal time for a projected collision if agents proceed with
    zero acceleration.
    """

    def __init__(self, name: str, category: str, ego_lane_change_metric: EgoLaneChangeStatistics, no_ego_at_fault_collisions_metric: EgoAtFaultCollisionStatistics, time_step_size: float, time_horizon: float, least_min_ttc: float, metric_score_unit: Optional[str]=None):
        """
        Initializes the TimeToCollisionStatistics class
        :param name: Metric name
        :param category: Metric category
        :param ego_lane_change_metric: Lane chang metric computed prior to calling the current metric
        :param no_ego_at_fault_collisions_metric: Ego at fault collisions computed prior to the current metric
        :param time_step_size: [s] Step size for the propagation of collision agents
        :param time_horizon: [s] Time horizon for collision checking
        :param least_min_ttc: minimum desired TTC.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._time_step_size = time_step_size
        self._time_horizon = time_horizon
        self._least_min_ttc = least_min_ttc
        self._ego_lane_change_metric = ego_lane_change_metric
        self._no_ego_at_fault_collisions_metric = no_ego_at_fault_collisions_metric
        self.results: List[MetricStatistics] = []

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[-1].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the time to collision statistics
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the time to collision metric
        """
        timestamps_in_common_or_connected_route_objs: List[int] = self._ego_lane_change_metric.timestamps_in_common_or_connected_route_objs
        assert self._no_ego_at_fault_collisions_metric.results, 'no_ego_at_fault_collisions metric must be run prior to calling {}'.format(self.name)
        all_collisions = self._no_ego_at_fault_collisions_metric.all_collisions
        timestamps_at_fault_collisions = self._no_ego_at_fault_collisions_metric.timestamps_at_fault_collisions
        ego_states = history.extract_ego_state
        ego_timestamps = extract_ego_time_point(ego_states)
        observations = [sample.observation for sample in history.data]
        time_to_collision = compute_time_to_collision(ego_states, ego_timestamps, observations, timestamps_in_common_or_connected_route_objs, all_collisions, timestamps_at_fault_collisions, history.map_api, self._time_step_size, self._time_horizon)
        time_to_collision_within_bounds = self._least_min_ttc < np.array(time_to_collision, dtype=np.float64)
        time_series = TimeSeries(unit='time_to_collision_under_' + f'{self._time_horizon}' + '_seconds [s]', time_stamps=list(ego_timestamps), values=list(time_to_collision))
        metric_statistics = [Statistic(name='min_time_to_collision', unit='seconds', value=np.min(time_to_collision), type=MetricStatisticsType.MIN), Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=bool(np.all(time_to_collision_within_bounds)), type=MetricStatisticsType.BOOLEAN)]
        self.results = self._construct_metric_results(metric_statistics=metric_statistics, time_series=time_series, scenario=scenario, metric_score_unit=self.metric_score_unit)
        return self.results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the time to collision statistics
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the time to collision metric
        """
    timestamps_in_common_or_connected_route_objs: List[int] = self._ego_lane_change_metric.timestamps_in_common_or_connected_route_objs
    assert self._no_ego_at_fault_collisions_metric.results, 'no_ego_at_fault_collisions metric must be run prior to calling {}'.format(self.name)
    all_collisions = self._no_ego_at_fault_collisions_metric.all_collisions
    timestamps_at_fault_collisions = self._no_ego_at_fault_collisions_metric.timestamps_at_fault_collisions
    ego_states = history.extract_ego_state
    ego_timestamps = extract_ego_time_point(ego_states)
    observations = [sample.observation for sample in history.data]
    time_to_collision = compute_time_to_collision(ego_states, ego_timestamps, observations, timestamps_in_common_or_connected_route_objs, all_collisions, timestamps_at_fault_collisions, history.map_api, self._time_step_size, self._time_horizon)
    time_to_collision_within_bounds = self._least_min_ttc < np.array(time_to_collision, dtype=np.float64)
    time_series = TimeSeries(unit='time_to_collision_under_' + f'{self._time_horizon}' + '_seconds [s]', time_stamps=list(ego_timestamps), values=list(time_to_collision))
    metric_statistics = [Statistic(name='min_time_to_collision', unit='seconds', value=np.min(time_to_collision), type=MetricStatisticsType.MIN), Statistic(name=f'{self.name}', unit=MetricStatisticsType.BOOLEAN.unit, value=bool(np.all(time_to_collision_within_bounds)), type=MetricStatisticsType.BOOLEAN)]
    self.results = self._construct_metric_results(metric_statistics=metric_statistics, time_series=time_series, scenario=scenario, metric_score_unit=self.metric_score_unit)
    return self.results

class EgoMeanSpeedStatistics(MetricBase):
    """Ego mean speed metric."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the EgoMeanSpeedStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)

    @staticmethod
    def ego_avg_speed(history: SimulationHistory) -> Any:
        """
        Compute mean of ego speed over the scenario duration
        :param history: History from a simulation engine
        :return mean of ego speed (m/s).
        """
        ego_states = history.extract_ego_state
        ego_velocities = extract_ego_velocity(ego_states)
        mean_speed = np.mean(ego_velocities)
        return mean_speed

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the mean of ego speed over the scenario duration
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the mean of ego speed.
        """
        mean_speed = self.ego_avg_speed(history=history)
        statistics = [Statistic(name='ego_mean_speed_value', unit='meters_per_second', value=mean_speed, type=MetricStatisticsType.VALUE)]
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario)
        return results

@staticmethod
def ego_avg_speed(history: SimulationHistory) -> Any:
    """
        Compute mean of ego speed over the scenario duration
        :param history: History from a simulation engine
        :return mean of ego speed (m/s).
        """
    ego_states = history.extract_ego_state
    ego_velocities = extract_ego_velocity(ego_states)
    mean_speed = np.mean(ego_velocities)
    return mean_speed

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the mean of ego speed over the scenario duration
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the mean of ego speed.
        """
    mean_speed = self.ego_avg_speed(history=history)
    statistics = [Statistic(name='ego_mean_speed_value', unit='meters_per_second', value=mean_speed, type=MetricStatisticsType.VALUE)]
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario)
    return results

class EgoLaneChangeStatistics(MetricBase):
    """Statistics on lane change."""

    def __init__(self, name: str, category: str, max_fail_rate: float) -> None:
        """
        Initializes the EgoLaneChangeStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_fail_rate: maximum acceptable ratio of failed to total number of lane changes.
        """
        super().__init__(name=name, category=category)
        self._max_fail_rate = max_fail_rate
        self.ego_driven_route: List[List[Optional[GraphEdgeMapObject]]] = []
        self.corners_route: List[CornersGraphEdgeMapObject] = [CornersGraphEdgeMapObject([], [], [], [])]
        self.timestamps_in_common_or_connected_route_objs: List[int] = []
        self.results: List[MetricStatistics] = []

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lane chane metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lane change duration in micro seconds and status.
        """
        ego_states = history.extract_ego_state
        ego_poses = extract_ego_center(ego_states)
        self.ego_driven_route = get_route(history.map_api, ego_poses)
        ego_timestamps = extract_ego_time_point(ego_states)
        ego_footprint_list = [ego_state.car_footprint for ego_state in ego_states]
        corners_route = extract_corners_route(history.map_api, ego_footprint_list)
        self.corners_route = corners_route
        common_or_connected_route_objs = get_common_or_connected_route_objs_of_corners(corners_route)
        timestamps_in_common_or_connected_route_objs = get_timestamps_in_common_or_connected_route_objs(common_or_connected_route_objs, ego_timestamps)
        self.timestamps_in_common_or_connected_route_objs = timestamps_in_common_or_connected_route_objs
        lane_changes = find_lane_changes(ego_timestamps, common_or_connected_route_objs)
        if len(lane_changes) == 0:
            metric_statistics = [Statistic(name=f'number_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=0, type=MetricStatisticsType.COUNT), Statistic(name=f'{self.name}_fail_rate_below_threshold', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
        else:
            lane_change_durations = [lane_change.duration_us * 1e-06 for lane_change in lane_changes]
            failed_lane_changes = [lane_change for lane_change in lane_changes if not lane_change.success]
            failed_ratio = len(failed_lane_changes) / len(lane_changes)
            fail_rate_below_threshold = 1 if self._max_fail_rate >= failed_ratio else 0
            metric_statistics = [Statistic(name=f'number_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=len(lane_changes), type=MetricStatisticsType.COUNT), Statistic(name=f'max_{self.name}_duration', unit='seconds', value=np.max(lane_change_durations), type=MetricStatisticsType.MAX), Statistic(name=f'avg_{self.name}_duration', unit='seconds', value=float(np.mean(lane_change_durations)), type=MetricStatisticsType.MEAN), Statistic(name=f'ratio_of_failed_{self.name}', unit=MetricStatisticsType.RATIO.unit, value=failed_ratio, type=MetricStatisticsType.RATIO), Statistic(name=f'{self.name}_fail_rate_below_threshold', unit=MetricStatisticsType.BOOLEAN.unit, value=bool(fail_rate_below_threshold), type=MetricStatisticsType.BOOLEAN)]
        results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, time_series=None, scenario=scenario)
        self.results = results
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the lane chane metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lane change duration in micro seconds and status.
        """
    ego_states = history.extract_ego_state
    ego_poses = extract_ego_center(ego_states)
    self.ego_driven_route = get_route(history.map_api, ego_poses)
    ego_timestamps = extract_ego_time_point(ego_states)
    ego_footprint_list = [ego_state.car_footprint for ego_state in ego_states]
    corners_route = extract_corners_route(history.map_api, ego_footprint_list)
    self.corners_route = corners_route
    common_or_connected_route_objs = get_common_or_connected_route_objs_of_corners(corners_route)
    timestamps_in_common_or_connected_route_objs = get_timestamps_in_common_or_connected_route_objs(common_or_connected_route_objs, ego_timestamps)
    self.timestamps_in_common_or_connected_route_objs = timestamps_in_common_or_connected_route_objs
    lane_changes = find_lane_changes(ego_timestamps, common_or_connected_route_objs)
    if len(lane_changes) == 0:
        metric_statistics = [Statistic(name=f'number_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=0, type=MetricStatisticsType.COUNT), Statistic(name=f'{self.name}_fail_rate_below_threshold', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
    else:
        lane_change_durations = [lane_change.duration_us * 1e-06 for lane_change in lane_changes]
        failed_lane_changes = [lane_change for lane_change in lane_changes if not lane_change.success]
        failed_ratio = len(failed_lane_changes) / len(lane_changes)
        fail_rate_below_threshold = 1 if self._max_fail_rate >= failed_ratio else 0
        metric_statistics = [Statistic(name=f'number_of_{self.name}', unit=MetricStatisticsType.COUNT.unit, value=len(lane_changes), type=MetricStatisticsType.COUNT), Statistic(name=f'max_{self.name}_duration', unit='seconds', value=np.max(lane_change_durations), type=MetricStatisticsType.MAX), Statistic(name=f'avg_{self.name}_duration', unit='seconds', value=float(np.mean(lane_change_durations)), type=MetricStatisticsType.MEAN), Statistic(name=f'ratio_of_failed_{self.name}', unit=MetricStatisticsType.RATIO.unit, value=failed_ratio, type=MetricStatisticsType.RATIO), Statistic(name=f'{self.name}_fail_rate_below_threshold', unit=MetricStatisticsType.BOOLEAN.unit, value=bool(fail_rate_below_threshold), type=MetricStatisticsType.BOOLEAN)]
    results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=metric_statistics, time_series=None, scenario=scenario)
    self.results = results
    return results

class EgoIsMakingProgressStatistics(MetricBase):
    """
    Check if ego trajectory is making progress along expert route more than a minimum required progress.
    """

    def __init__(self, name: str, category: str, ego_progress_along_expert_route_metric: EgoProgressAlongExpertRouteStatistics, min_progress_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initializes the EgoIsMakingProgressStatistics class
        :param name: Metric name
        :param category: Metric category
        :param ego_progress_along_expert_route_metric: Ego progress along expert route metric
        :param min_progress_threshold: minimimum required progress threshold
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._min_progress_threshold = min_progress_threshold
        self._ego_progress_along_expert_route_metric = ego_progress_along_expert_route_metric

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[0].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the ego_is_making_progress metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated metric.
        """
        ego_is_making_progress = self._ego_progress_along_expert_route_metric.results[0].statistics[-1].value >= self._min_progress_threshold
        statistics = [Statistic(name='ego_is_making_progress', unit='boolean', value=ego_is_making_progress, type=MetricStatisticsType.BOOLEAN)]
        results = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
        return results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Returns the ego_is_making_progress metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return: the estimated metric.
        """
    ego_is_making_progress = self._ego_progress_along_expert_route_metric.results[0].statistics[-1].value >= self._min_progress_threshold
    statistics = [Statistic(name='ego_is_making_progress', unit='boolean', value=ego_is_making_progress, type=MetricStatisticsType.BOOLEAN)]
    results = self._construct_metric_results(metric_statistics=statistics, time_series=None, scenario=scenario, metric_score_unit=self.metric_score_unit)
    return results

class DrivingDirectionComplianceStatistics(MetricBase):
    """Driving direction compliance metric.
    This metric traces if ego has been driving against the traffic flow more than some threshold during some time interval of ineterst.
    """

    def __init__(self, name: str, category: str, lane_change_metric: EgoLaneChangeStatistics, driving_direction_compliance_threshold: float=2, driving_direction_violation_threshold: float=6, time_horizon: float=1, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the DrivingDirectionComplianceStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param lane_change_metric: Lane change metric.
        :param driving_direction_compliance_threshold: Driving in opposite direction up to this threshold isn't considered violation
        :param driving_direction_violation_threshold: Driving in opposite direction above this threshold isn't tolerated
        :param time_horizon: Movement of the vehicle along baseline direction during a horizon time_horizon is
        considered for evaluation.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._lane_change_metric = lane_change_metric
        self._driving_direction_compliance_threshold = driving_direction_compliance_threshold
        self._driving_direction_violation_threshold = driving_direction_violation_threshold
        self._time_horizon = time_horizon

    @staticmethod
    def _extract_metric(ego_poses: List[Point2D], ego_driven_route: List[List[GraphEdgeMapObject]], n_horizon: int) -> List[float]:
        """Compute the movement of ego during the past n_horizon samples along the direction of baselines.
        :param ego_poses: List of  ego poses.
        :param ego_driven_route: List of lanes/lane_connectors ego belongs to.
        :param n_horizon: Number of samples to sum the movement over.
        :return: A list of floats including ego's overall movements in the past n_horizon samples.
        """
        progress_along_baseline = []
        distance_to_start = None
        prev_distance_to_start = None
        prev_route_obj_id = None
        if ego_driven_route[0]:
            prev_route_obj_id = ego_driven_route[0][0].id
        for ego_pose, ego_route_object in zip(ego_poses, ego_driven_route):
            if not ego_route_object:
                progress_along_baseline.append(0.0)
                continue
            if prev_route_obj_id and ego_route_object[0].id == prev_route_obj_id:
                distance_to_start = get_distance_of_closest_baseline_point_to_its_start(ego_route_object[0].baseline_path, ego_pose)
                progress_made = distance_to_start - prev_distance_to_start if prev_distance_to_start is not None and distance_to_start else 0.0
                progress_along_baseline.append(progress_made)
                prev_distance_to_start = distance_to_start
            else:
                distance_to_start = None
                prev_distance_to_start = None
                progress_along_baseline.append(0.0)
                prev_route_obj_id = ego_route_object[0].id
        progress_over_n_horizon = [sum(progress_along_baseline[max(0, ind - n_horizon):ind + 1]) for ind, _ in enumerate(progress_along_baseline)]
        return progress_over_n_horizon

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(metric_statistics[0].value)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the driving direction compliance metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return: driving direction compliance statistics.
        """
        ego_states = history.extract_ego_state
        ego_poses = extract_ego_center(ego_states)
        ego_driven_route = self._lane_change_metric.ego_driven_route
        ego_timestamps = extract_ego_time_point(ego_states)
        n_horizon = int(self._time_horizon * 1000000.0 / np.mean(np.diff(ego_timestamps)))
        progress_over_interval = self._extract_metric(ego_poses, ego_driven_route, n_horizon)
        max_negative_progress_over_interval = abs(min(progress_over_interval))
        if max_negative_progress_over_interval < self._driving_direction_compliance_threshold:
            driving_direction_score = 1.0
        elif max_negative_progress_over_interval < self._driving_direction_violation_threshold:
            driving_direction_score = 0.5
        else:
            driving_direction_score = 0.0
        time_series = TimeSeries(unit='progress_along_driving_direction_in_last_' + f'{self._time_horizon}' + '_seconds_[m]', time_stamps=list(ego_timestamps), values=list(progress_over_interval))
        statistics = [Statistic(name=f'{self.name}' + '_score', unit='value', value=float(driving_direction_score), type=MetricStatisticsType.VALUE), Statistic(name='min_progress_along_driving_direction_in_' + f'{self._time_horizon}' + '_second_interval', unit='meters', value=float(-max_negative_progress_over_interval), type=MetricStatisticsType.MIN)]
        self.results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
        return self.results

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the driving direction compliance metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return: driving direction compliance statistics.
        """
    ego_states = history.extract_ego_state
    ego_poses = extract_ego_center(ego_states)
    ego_driven_route = self._lane_change_metric.ego_driven_route
    ego_timestamps = extract_ego_time_point(ego_states)
    n_horizon = int(self._time_horizon * 1000000.0 / np.mean(np.diff(ego_timestamps)))
    progress_over_interval = self._extract_metric(ego_poses, ego_driven_route, n_horizon)
    max_negative_progress_over_interval = abs(min(progress_over_interval))
    if max_negative_progress_over_interval < self._driving_direction_compliance_threshold:
        driving_direction_score = 1.0
    elif max_negative_progress_over_interval < self._driving_direction_violation_threshold:
        driving_direction_score = 0.5
    else:
        driving_direction_score = 0.0
    time_series = TimeSeries(unit='progress_along_driving_direction_in_last_' + f'{self._time_horizon}' + '_seconds_[m]', time_stamps=list(ego_timestamps), values=list(progress_over_interval))
    statistics = [Statistic(name=f'{self.name}' + '_score', unit='value', value=float(driving_direction_score), type=MetricStatisticsType.VALUE), Statistic(name='min_progress_along_driving_direction_in_' + f'{self._time_horizon}' + '_second_interval', unit='meters', value=float(-max_negative_progress_over_interval), type=MetricStatisticsType.MIN)]
    self.results: List[MetricStatistics] = self._construct_metric_results(metric_statistics=statistics, scenario=scenario, time_series=time_series, metric_score_unit=self.metric_score_unit)
    return self.results

class PlannerExpertFinalL2ErrorStatistics(MetricBase):
    """
    L2 error of planned ego pose w.r.t expert at the final pose given a comparison time horizon.
    """

    def __init__(self, name: str, category: str, planner_expert_average_l2_error_within_bound_metric: PlannerExpertAverageL2ErrorStatistics, max_final_l2_error_threshold: float, metric_score_unit: Optional[str]=None) -> None:
        """
        Initialize the PlannerExpertFinalL2ErrorStatistics class.
        :param name: Metric name.
        :param category: Metric category.
        :param planner_expert_average_l2_error_within_bound_metric: planner_expert_average_l2_error_within_bound metric.
        :param max_final_l2_error_threshold: Maximum acceptable error threshold.
        :param metric_score_unit: Metric final score unit.
        """
        super().__init__(name=name, category=category, metric_score_unit=metric_score_unit)
        self._planner_expert_average_l2_error_within_bound_metric = planner_expert_average_l2_error_within_bound_metric
        self._max_final_l2_error_threshold = max_final_l2_error_threshold

    def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
        """Inherited, see superclass."""
        return float(max(0, 1 - metric_statistics[-1].value / self._max_final_l2_error_threshold))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
        final_displacement_errors = self._planner_expert_average_l2_error_within_bound_metric.final_displacement_errors
        ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
        selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
        comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
        results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_final_l2_error_threshold, metric_values=final_displacement_errors, name='planner_expert_FDE', unit='meter', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
        return results

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(max(0, 1 - metric_statistics[-1].value / self._max_final_l2_error_threshold))

def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
    """
        Return the estimated metric.
        :param history: History from a simulation engine.
        :param scenario: Scenario running this metric.
        :return the estimated metric.
        """
    final_displacement_errors = self._planner_expert_average_l2_error_within_bound_metric.final_displacement_errors
    ego_timestamps_sampled = self._planner_expert_average_l2_error_within_bound_metric.ego_timestamps_sampled
    selected_frames = self._planner_expert_average_l2_error_within_bound_metric.selected_frames
    comparison_horizon = self._planner_expert_average_l2_error_within_bound_metric.comparison_horizon
    results: List[MetricStatistics] = self._construct_open_loop_metric_results(scenario, comparison_horizon, self._max_final_l2_error_threshold, metric_values=final_displacement_errors, name='planner_expert_FDE', unit='meter', timestamps_sampled=ego_timestamps_sampled, metric_score_unit=self.metric_score_unit, selected_frames=selected_frames)
    return results

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
def _calculate_expected_number_of_threads(max_callback_workers: int) -> int:
    """
        Utility function to calculate the expected number of threads available to the workers. The calculation is based on
        the current build_callbacks_worker implementation.
        :param max_callback_workers: Config value passed from Sequential worker config.
        """
    return min(TestSimulationCallbackBuilder.mock_cpu_node_count - 1, max_callback_workers)

def filter_num_scenarios_per_type(scenario_dict: ScenarioDict, num_scenarios_per_type: int, randomize: bool) -> ScenarioDict:
    """
    Filter the number of scenarios in a scenario dictionary per scenario type.
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type.
    :param num_scenarios_per_type: Number of scenarios per type to keep.
    :param randomize: Whether to randomly sample the scenarios.
    :return: Filtered scenario dictionary.
    """
    for scenario_type in scenario_dict:
        if randomize and num_scenarios_per_type < len(scenario_dict[scenario_type]):
            scenario_dict[scenario_type] = random.sample(scenario_dict[scenario_type], num_scenarios_per_type)
        else:
            step = max(len(scenario_dict[scenario_type]) // num_scenarios_per_type, 1)
            scenario_dict[scenario_type] = scenario_dict[scenario_type][::step]
            scenario_dict[scenario_type] = scenario_dict[scenario_type][:num_scenarios_per_type]
    return scenario_dict

def _filter_scenarios_from_scenario_list(scenario_list: List[NuPlanScenario], num_scenarios_to_keep: int, randomize: bool) -> List[NuPlanScenario]:
    """
        Removes scenarios randomly or does equisampling of the scenarios.
        :param scenario_list: List of scenarios.
        :param num_scenarios_to_keep: Number of scenarios that should be in the final list.
        :param randomize: Boolean for whether to randomly sample from scenario_list or carry out equisampling of scenarios.
        """
    total_num_scenarios = len(scenario_list)
    step = max(total_num_scenarios // num_scenarios_to_keep, 1)
    scenario_list = random.sample(scenario_list, num_scenarios_to_keep) if randomize else scenario_list[::step]
    scenario_list = scenario_list[:num_scenarios_to_keep]
    return scenario_list

def read_metrics_from_results(results: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    """
    Transforms a pandas dataframe containing metric results to a string understandable by EvalAI leaderboard.
    :param results: The dataframes of metric results.
    :return: Dict holding the metric names and values.
    """
    ch1_df = results['open_loop_boxes']
    ch2_df = results['closed_loop_nonreactive_agents']
    ch3_df = results['closed_loop_reactive_agents']
    ch1, ch2, ch3 = [df.loc[df['scenario'] == 'final_score'] for df in [ch1_df, ch2_df, ch3_df]]
    metrics = {'ch1_overall_score': ch1['score'].values[0], 'ch1_avg_displacement_error_within_bound': ch1['planner_expert_average_l2_error_within_bound'].values[0], 'ch1_final_displacement_error_within_bound': ch1['planner_expert_final_l2_error_within_bound'].values[0], 'ch1_miss_rate_within_bound': ch1['planner_miss_rate_within_bound'].values[0], 'ch1_avg_heading_error_within_bound': ch1['planner_expert_average_heading_error_within_bound'].values[0], 'ch1_final_heading_error_within_bound': ch1['planner_expert_final_heading_error_within_bound'].values[0], 'ch2_overall_score': ch2['score'].values[0], 'ch2_ego_is_making_progress': ch2['ego_is_making_progress'].values[0], 'ch2_no_ego_at_fault_collisions': ch2['no_ego_at_fault_collisions'].values[0], 'ch2_drivable_area_compliance': ch2['drivable_area_compliance'].values[0], 'ch2_driving_direction_compliance': ch2['driving_direction_compliance'].values[0], 'ch2_ego_is_comfortable': ch2['ego_is_comfortable'].values[0], 'ch2_ego_progress_along_expert_route': ch2['ego_progress_along_expert_route'].values[0], 'ch2_time_to_collision_within_bound': ch2['time_to_collision_within_bound'].values[0], 'ch2_speed_limit_compliance': ch2['speed_limit_compliance'].values[0], 'ch3_overall_score': ch3['score'].values[0], 'ch3_ego_is_making_progress': ch3['ego_is_making_progress'].values[0], 'ch3_no_ego_at_fault_collisions': ch3['no_ego_at_fault_collisions'].values[0], 'ch3_drivable_area_compliance': ch3['drivable_area_compliance'].values[0], 'ch3_driving_direction_compliance': ch3['driving_direction_compliance'].values[0], 'ch3_ego_is_comfortable': ch3['ego_is_comfortable'].values[0], 'ch3_ego_progress_along_expert_route': ch3['ego_progress_along_expert_route'].values[0], 'ch3_time_to_collision_within_bound': ch3['time_to_collision_within_bound'].values[0], 'ch3_speed_limit_compliance': ch3['speed_limit_compliance'].values[0], 'combined_overall_score': np.mean([ch1['score'].values[0], ch2['score'].values[0], ch3['score'].values[0]])}
    return metrics

