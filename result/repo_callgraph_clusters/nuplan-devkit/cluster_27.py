# Cluster 27

def setup_notebook() -> None:
    """
    Code that must be run at the start of every tutorial notebook to:
        - patch the event loop to allow nesting, eg. so we can run asyncio.run from
          within a notebook.
    """
    nest_asyncio.apply()

class NuPlanDB(DB):
    """
    Database for loading and accessing nuPlan .db files.

    It provides lookups and get methods to access the SQL database tables and metadata.
    In addition, it provides functionality for automatically downloading a database from a remote (e.g. S3)
    if not present in the local filesystem and storing it.

    A database file is in the form of "<log_date>_<vehicle_number>_<snippet_start>_<snippet_end>.db"
    for example "2021.05.24.12.28.29_veh-12_04802_04907.db" - each database represents a log snippet of
    variable duration (e.g. 60sec or 30min) that was manually driven by an expert driver.

    The nuPlan dataset comprises of thousands of .db files.
    These can be collectively loaded and accessed from the `NuPlanDBWrapper` class and be used in training/simulation.
    """

    def __init__(self, data_root: str, load_path: str, maps_db: Optional[GPKGMapsDB]=None, verbose: bool=False):
        """
        Load database and create reverse indexes and shortcuts.
        :param data_root: Local data root for loading (or storing if downloaded) the database.
        :param load_path: Local or remote (S3) filename of the database to be loaded
        :param maps_db: Map database associated with this database.
        :param verbose: Whether to print status messages during load.
        """
        self._data_root = data_root
        self._load_path = load_path
        self._maps_db = maps_db
        self._verbose = verbose
        table_names = list(nuplandb_table_templates.keys())
        nuplandb_models_dict = {}
        nuplandb_models_dict['default'] = 'models'
        nuplandb_models_dict['Camera'] = 'camera'
        nuplandb_models_dict['Category'] = 'category'
        nuplandb_models_dict['Image'] = 'image'
        nuplandb_models_dict['Lidar'] = 'lidar'
        nuplandb_models_dict['Log'] = 'log'
        nuplandb_models_dict['Track'] = 'track'
        nuplandb_models_dict['TrafficLightStatus'] = 'traffic_light_status'
        nuplandb_models_dict['LidarBox'] = 'lidar_box'
        nuplandb_models_dict['Scene'] = 'scene'
        nuplandb_models_dict['ScenarioTag'] = 'scenario_tag'
        nuplandb_models_dict['LidarPc'] = 'lidar_pc'
        nuplandb_models_dict['EgoPose'] = 'ego_pose'
        super().__init__(table_names, nuplan_db_orm, data_root, load_path, verbose, nuplandb_models_dict)

    def __reduce__(self) -> Tuple[Type[NuPlanDB], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._data_root, self._load_path, self._maps_db, self._verbose))

    @property
    def load_path(self) -> str:
        """Get the path from which the db file was loaded."""
        return self._load_path

    @property
    def maps_db(self) -> Optional[GPKGMapsDB]:
        """Get the MapsDB objectd attached to the database."""
        return self._maps_db

    @property
    def log_name(self) -> str:
        """Get the name of the log contained within the database."""
        return cast(str, self.log.logfile)

    @property
    def map_name(self) -> str:
        """Get the name of the map associated with the log of the database."""
        return cast(str, self.log.map_version)

    @property
    def category(self) -> Table[Category]:
        """
        Get Category table.
        :return: The category table.
        """
        return self.tables['category']

    @property
    def log(self) -> Log:
        """
        Get first and only entry in the log table.
        :return: The log entry in the log table.
        """
        return self.tables['log'][0]

    @property
    def camera(self) -> Table[Camera]:
        """
        Get Camera table.
        :return: The camera table.
        """
        return self.tables['camera']

    @property
    def lidar(self) -> Table[Lidar]:
        """
        Get Lidar table.
        :return: The lidar table.
        """
        return self.tables['lidar']

    @property
    def ego_pose(self) -> Table[EgoPose]:
        """
        Get Ego Pose table.
        :return: The ego pose table.
        """
        return self.tables['ego_pose']

    @property
    def image(self) -> Table[Image]:
        """
        Get Image table.
        :return: The image table.
        """
        return self.tables['image']

    @property
    def lidar_pc(self) -> Table[LidarPc]:
        """
        Get Lidar Pc table.
        :return: The lidar pc table.
        """
        return self.tables['lidar_pc']

    @property
    def lidar_box(self) -> Table[LidarBox]:
        """
        Get Lidar Box table.
        :return: The lidar box table.
        """
        return self.tables['lidar_box']

    @property
    def track(self) -> Table[Track]:
        """
        Get Track table.
        :return: The track table.
        """
        return self.tables['track']

    @property
    def scene(self) -> Table[Scene]:
        """
        Get Scene table.
        :return: The scene table.
        """
        return self.tables['scene']

    @property
    def scenario_tag(self) -> Table[ScenarioTag]:
        """
        Get Scenario Tag table.
        :return: The scenario tag table.
        """
        return self.tables['scenario_tag']

    @property
    def traffic_light_status(self) -> Table[TrafficLightStatus]:
        """
        Get Traffic Light Status table.
        :return: The traffic light status table.
        """
        return self.tables['traffic_light_status']

    @cached_property
    def cam_channels(self) -> Set[str]:
        """
        Get list of camera channels.
        :return: The list of camera channels.
        """
        return {cam.channel for cam in self.camera}

    @cached_property
    def lidar_channels(self) -> Set[str]:
        """
        Get list of lidar channels.
        :return: The list of lidar channels.
        """
        return {lidar.channel for lidar in self.lidar}

    def get_unique_scenario_tags(self) -> List[str]:
        """Retrieve all unique scenario tags in the database."""
        return sorted({tag[0] for tag in self.session.query(ScenarioTag.type).distinct().all()})

@property
def log_name(self) -> str:
    """Get the name of the log contained within the database."""
    return cast(str, self.log.logfile)

@property
def map_name(self) -> str:
    """Get the name of the map associated with the log of the database."""
    return cast(str, self.log.map_version)

def hausdorff_distance_box(obsbox: Box3D, gtbox: Box3D) -> float:
    """
    Calculate Hausdorff distance between two 2d-boxes in Box3D class.
    :param obsbox: Observation box.
    :param gtbox: Ground truth box.
    :return: Hausdorff distance.
    """

    def footprint(box: Box3D) -> Polygon:
        """
        Get footprint polygon.
        :param box: (center_x <float>, center_y <float>, width <float>, length <float>, theta <float>).
        :return: <Polygon>. A polygon representation of the 2d box.
        """
        x, y, w, l, head = (box.center[0], box.center[1], box.wlh[0], box.wlh[1], quaternion_yaw(box.orientation))
        rot = np.array([[math.cos(head), -math.sin(head)], [math.sin(head), math.cos(head)]])
        q0 = np.array([x, y])[:, None]
        q1 = np.array([-w / 2, -l / 2])[:, None]
        q2 = np.array([-w / 2, l / 2])[:, None]
        q3 = np.array([w / 2, l / 2])[:, None]
        q4 = np.array([w / 2, -l / 2])[:, None]
        q1 = np.dot(rot, q1) + q0
        q2 = np.dot(rot, q2) + q0
        q3 = np.dot(rot, q3) + q0
        q4 = np.dot(rot, q4) + q0
        return Polygon([(q1.item(0), q1.item(1)), (q2.item(0), q2.item(1)), (q3.item(0), q3.item(1)), (q4.item(0), q4.item(1))])
    obs_poly = footprint(obsbox)
    gt_poly = footprint(gtbox)
    distance = 0.0
    for p in list(gt_poly.exterior.coords):
        new_dist = float(obs_poly.distance(Point(p)))
        if new_dist > distance:
            distance = new_dist
    for p in list(obs_poly.exterior.coords):
        new_dist = float(gt_poly.distance(Point(p)))
        if new_dist > distance:
            distance = new_dist
    return distance

def hausdorff_distance(obsbox: TwoDimBox, gtbox: TwoDimBox) -> float:
    """
    Calculate Hausdorff distance between two 2d-boxes.
    :param obsbox: Observation 2d box.
    :param gtbox: Ground truth 2d box.
    :return: Hausdorff distance.
    """

    def footprint(box: TwoDimBox) -> Polygon:
        """
        Get footprint polygon.
        :param box: Input 2-d box.
        :return: A polygon representation of the 2d box.
        """
        x, y, w, l, head = box
        rot = np.array([[math.cos(head), -math.sin(head)], [math.sin(head), math.cos(head)]])
        q0 = np.array([x, y])[:, None]
        q1 = np.array([-w / 2, -l / 2])[:, None]
        q2 = np.array([-w / 2, l / 2])[:, None]
        q3 = np.array([w / 2, l / 2])[:, None]
        q4 = np.array([w / 2, -l / 2])[:, None]
        q1 = np.dot(rot, q1) + q0
        q2 = np.dot(rot, q2) + q0
        q3 = np.dot(rot, q3) + q0
        q4 = np.dot(rot, q4) + q0
        return Polygon([(q1.item(0), q1.item(1)), (q2.item(0), q2.item(1)), (q3.item(0), q3.item(1)), (q4.item(0), q4.item(1))])
    obs_poly = footprint(obsbox)
    gt_poly = footprint(gtbox)
    distance = 0.0
    for p in list(gt_poly.exterior.coords):
        new_dist = float(obs_poly.distance(Point(p)))
        if new_dist > distance:
            distance = new_dist
    for p in list(obs_poly.exterior.coords):
        new_dist = float(gt_poly.distance(Point(p)))
        if new_dist > distance:
            distance = new_dist
    return distance

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

def serialize(self) -> Dict[str, Any]:
    """
        Implemented. See interface.
        :return: Dict of field name to field values.
        """
    future_orientations_serialized = [[orientation.elements.tolist() if orientation is not None else None for orientation in future_orientations_of_mode] for future_orientations_of_mode in self.future_orientations] if self.future_orientations is not None else None
    return {'center': self.center.tolist(), 'wlh': self.wlh.tolist(), 'orientation': self.orientation.elements.tolist(), 'label': self.label, 'score': self.score, 'velocity': self.velocity.tolist(), 'angular_velocity': self.angular_velocity, 'payload': self.payload, 'token': self.token, 'track_token': self.track_token, 'future_horizon_len_s': self.future_horizon_len_s, 'future_interval_s': self.future_interval_s, 'future_centers': self.future_centers.tolist() if self.future_centers is not None else None, 'future_orientations': future_orientations_serialized, 'mode_probs': self.mode_probs.tolist() if self.mode_probs is not None else None}

def connect_blp_predecessor(blp_id: str, lane_conn_info: gpd.geodataframe, cross_blp_conns: Dict[str, List[int]], ls_conns: List[List[int]]) -> None:
    """
    Given a specific baseline path id, find its predecessor and update info in ls_connections information.
    :param blp_id: a specific baseline path id to query
    :param lane_conn_info: baseline paths information in intersections contains the from_blp/to_blp info
    :param cross_blp_conns: Dict to record the baseline path id as key(str) and [blp_start_ls_idx, blp_end_ls_idx] pair
        as value (List[int])
    :param ls_conns: lane_segment_connection to record the [from_ls_idx, to_ls_idx] connection info, updated with
        predecessors found.
    """
    blp_start, blp_end = cross_blp_conns[blp_id]
    predecessor_blp = lane_conn_info[lane_conn_info['to_blp'] == blp_id]
    predecessor_list = predecessor_blp['fid'].to_list()
    for predecessor_id in predecessor_list:
        predecessor_start, predecessor_end = cross_blp_conns[predecessor_id]
        ls_conns.append([predecessor_end, blp_start])

def connect_blp_successor(blp_id: str, lane_conn_info: gpd.geodataframe, cross_blp_conns: Dict[str, List[int]], ls_conns: List[List[int]]) -> None:
    """
    Given a specific baseline path id, find its successor and update info in ls_connections information.
    :param blp_id: a specific baseline path id to query
    :param lane_conn_info: baseline paths information in intersections contains the from_blp/to_blp info
    :param cross_blp_conns: Dict to record the baseline path id as key(str) and [blp_start_ls_idx, blp_end_ls_idx] pair
        as value (List[int])
    :param ls_conns: lane_segment_connnection to record the [from_ls_idx, to_ls_idx] connection info, updated with
        predecessors found.
    """
    blp_start, blp_end = cross_blp_conns[blp_id]
    successor_blp = lane_conn_info[lane_conn_info['from_blp'] == blp_id]
    successor_list = successor_blp['fid'].to_list()
    for successor_id in successor_list:
        successor_start, successor_end = cross_blp_conns[successor_id]
        ls_conns.append([blp_end, successor_start])

@dataclasses.dataclass
class MapVersionMeta:
    """Stores the metadata for a MapVersionMeta, a collection of MapLayerMeta objects."""

    def __init__(self, name: str) -> None:
        """
        Constructor.
        :param name: The name of a map layer.
        """
        self.name = name
        self.size = None
        self.layers: Dict[str, MapLayerMeta] = {}
        self.origin = None
        self.transform_matrix = None

    def __getitem__(self, item: str) -> MapLayerMeta:
        """
        Retrieves the MapLayer meta data for a given layer name.
        :param item: Layer name.
        :return: The metadata of a map layer.
        """
        return self.layers[item]

    def set_size(self, size: Tuple[int, int]) -> None:
        """
        Sets the size of map layer.
        :param size: The size used to set the map layer.
        """
        if self.size is None:
            self.size = size
        else:
            assert size == self.size, "Map layer size doesn't match map other layers from this map version."

    def set_map_origin(self, origin: Tuple[float, float]) -> None:
        """
        Sets the origin of the map.
        :param origin: The coordinate of the map origin.
        """
        if self.origin is None:
            self.origin = origin
        else:
            assert origin == self.origin, f'origin does not match other layers for map version {self.name}'

    def set_transform_matrix(self, transform_matrix: List[List[float]]) -> None:
        """
        Sets the transform matrix of the MapVersionMeta object.
        :param transform_matrix: The transform matrix for converting from physical coordinates to pixel coordinates.
        """
        if transform_matrix is not None:
            self.transform_matrix = np.array(transform_matrix)

    def add_layer(self, map_layer: MapLayerMeta) -> None:
        """
        Adds layer to the MapLayerMeta.
        :param map_layer: The map layer to be added.
        """
        self.layers[map_layer.name] = map_layer

    @property
    def layer_names(self) -> List[str]:
        """
        Returns a list of the layer names.
        :return: A list of the layer names.
        """
        return sorted(list(self.layers.keys()))

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the MapVersionMeta instance to a JSON-friendly dictionary representation.
        :return: Encoding of the MapVersionMeta.
        """
        return {'size': self.size, 'name': self.name, 'origin': self.origin, 'layers': [layer.serialize() for layer in self.layers.values()]}

    @classmethod
    def deserialize(cls, encoding: Dict[str, Any]) -> MapVersionMeta:
        """
        Instantiates a MapVersionMeta instance from serialized dictionary representation.
        :param encoding: Output from serialize.
        :return: Deserialized MapVersionMeta.
        """
        mv = MapVersionMeta(name=encoding['name'])
        mv.set_size(encoding['size'])
        mv.set_map_origin(encoding.get('origin'))
        mv.set_transform_matrix(encoding.get('transform_matrix'))
        for layer in encoding['layers']:
            mv.add_layer(MapLayerMeta.deserialize(layer))
        return mv

    def __hash__(self) -> int:
        """
        Returns the hash value for the MapVersionMeta object.
        :return: The hash value.
        """
        return hash((self.name, *[(key, self.layers[key].md5_hash) for key in sorted(self.layers)]))

    def __eq__(self, other: object) -> bool:
        """
        Compares two MapVersionMeta objects are the same or not by checking the hash value.
        :param other: The other MapVersionMeta objects.
        :return: True if both objects are the same, otherwise False.
        """
        if not isinstance(other, MapVersionMeta):
            return NotImplemented
        return self.__hash__() == hash(other)

def __hash__(self) -> int:
    """
        Returns the hash value for the MapVersionMeta object.
        :return: The hash value.
        """
    return hash((self.name, *[(key, self.layers[key].md5_hash) for key in sorted(self.layers)]))

def __eq__(self, other: object) -> bool:
    """
        Compares two MapVersionMeta objects are the same or not by checking the hash value.
        :param other: The other MapVersionMeta objects.
        :return: True if both objects are the same, otherwise False.
        """
    if not isinstance(other, MapVersionMeta):
        return NotImplemented
    return self.__hash__() == hash(other)

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

def load_vector_layer(self, layer_name: str) -> gpd.geodataframe:
    """
        Loads Vector Layer.
        :param layer_name: Name of Layer.
        :return: Returns vector layer as a GeoDataFrame object.
        """
    assert layer_name in self.available_vector_layers, f'{layer_name} is not a vector layer'
    return self._load_vector_map_layer(layer_name)

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

class PolygonMapObject(AbstractMapObject):
    """
    A class to represent any map object that can be represented as a polygon.
    """

    @property
    @abc.abstractmethod
    def polygon(self) -> Polygon:
        """
        Returns the surface of the map object as a Polygon.
        :return: The map object as a Polygon.
        """
        pass

    def contains_point(self, point: Point2D) -> bool:
        """
        Checks if the specified point is part of the map object polygon.
        :return: True if the point is within the polygon.
        """
        return bool(self.polygon.contains(Point(point.x, point.y)))

def contains_point(self, point: Point2D) -> bool:
    """
        Checks if the specified point is part of the map object polygon.
        :return: True if the point is within the polygon.
        """
    return bool(self.polygon.contains(Point(point.x, point.y)))

class NuPlanRoadBlock(RoadBlockGraphEdgeMapObject):
    """
    NuPlanMap implementation of Roadblock.
    """

    def __init__(self, roadblock_id: str, lanes_df: VectorLayer, lane_connectors_df: VectorLayer, baseline_paths_df: VectorLayer, boundaries_df: VectorLayer, roadblocks_df: VectorLayer, roadblock_connectors_df: VectorLayer, stop_lines_df: VectorLayer, intersections_df: VectorLayer, lane_connector_polygon_df: VectorLayer, map_data: AbstractMap):
        """
        Constructor of NuPlanRoadBlock.
        :param roadblock_id: unique identifier of the roadblock.
        :param lanes_df: the geopandas GeoDataframe that contains all lanes in the map.
        :param lane_connectors_df: the geopandas GeoDataframe that contains all lane connectors in the map.
        :param baseline_paths_df: the geopandas GeoDataframe that contains all baselines in the map.
        :param boundaries_df: the geopandas GeoDataframe that contains all boundaries in the map.
        :param roadblocks_df: the geopandas GeoDataframe that contains all roadblocks (lane groups) in the map.
        :param roadblock_connectors_df: the geopandas GeoDataframe that contains all roadblock connectors (lane group
            connectors) in the map.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        :param lane_connector_polygon_df: the geopandas GeoDataframe that contains polygons for lane connectors.
        """
        super().__init__(roadblock_id)
        self._lanes_df = lanes_df
        self._lane_connectors_df = lane_connectors_df
        self._baseline_paths_df = baseline_paths_df
        self._boundaries_df = boundaries_df
        self._roadblocks_df = roadblocks_df
        self._roadblock_connectors_df = roadblock_connectors_df
        self._stop_lines_df = stop_lines_df
        self._intersections_df = intersections_df
        self._lane_connector_polygon_df = lane_connector_polygon_df
        self._roadblock = None
        self._map_data = map_data

    @cached_property
    def incoming_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        roadblock_connectors_ids = get_all_rows_with_value(self._roadblock_connectors_df, 'to_lane_group_fid', self.id)['fid']
        return [roadblock_connector.NuPlanRoadBlockConnector(str(roadblock_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data) for roadblock_connector_id in roadblock_connectors_ids.tolist()]

    @cached_property
    def outgoing_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        roadblock_connectors_ids = get_all_rows_with_value(self._roadblock_connectors_df, 'from_lane_group_fid', self.id)['fid']
        return [roadblock_connector.NuPlanRoadBlockConnector(str(roadblock_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data) for roadblock_connector_id in roadblock_connectors_ids.to_list()]

    @cached_property
    def interior_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        lane_ids = get_all_rows_with_value(self._lanes_df, 'lane_group_fid', self.id)['fid']
        return [NuPlanLane(str(lane_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_id in lane_ids.to_list()]

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._get_roadblock().geometry

    @cached_property
    def children_stop_lines(self) -> List[StopLine]:
        """Inherited from superclass."""
        raise NotImplementedError

    @cached_property
    def parallel_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        raise NotImplementedError

    def _get_roadblock(self) -> pd.Series:
        """
        Gets the series from the roadblock dataframe containing roadblock's id.
        :return: the respective series from the roadblocks dataframe.
        """
        if self._roadblock is None:
            self._roadblock = get_row_with_value(self._roadblocks_df, 'fid', self.id)
        return self._roadblock

@cached_property
def incoming_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
    """Inherited from superclass."""
    roadblock_connectors_ids = get_all_rows_with_value(self._roadblock_connectors_df, 'to_lane_group_fid', self.id)['fid']
    return [roadblock_connector.NuPlanRoadBlockConnector(str(roadblock_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data) for roadblock_connector_id in roadblock_connectors_ids.tolist()]

@cached_property
def outgoing_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
    """Inherited from superclass."""
    roadblock_connectors_ids = get_all_rows_with_value(self._roadblock_connectors_df, 'from_lane_group_fid', self.id)['fid']
    return [roadblock_connector.NuPlanRoadBlockConnector(str(roadblock_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data) for roadblock_connector_id in roadblock_connectors_ids.to_list()]

@cached_property
def interior_edges(self) -> List[LaneGraphEdgeMapObject]:
    """Inherited from superclass."""
    lane_ids = get_all_rows_with_value(self._lanes_df, 'lane_group_fid', self.id)['fid']
    return [NuPlanLane(str(lane_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_id in lane_ids.to_list()]

class NuPlanLane(Lane):
    """
    NuPlanMap implementation of Lane.
    """

    def __init__(self, lane_id: str, lanes_df: VectorLayer, lane_connectors_df: VectorLayer, baseline_paths_df: VectorLayer, boundaries_df: VectorLayer, stop_lines_df: VectorLayer, lane_connector_polygon_df: VectorLayer, map_data: AbstractMap):
        """
        Constructor of NuPlanLane.
        :param lane_id: unique identifier of the lane.
        :param lanes_df: the geopandas GeoDataframe that contains all lanes in the map.
        :param lane_connectors_df: the geopandas GeoDataframe that contains all lane connectors in the map.
        :param baseline_paths_df: the geopandas GeoDataframe that contains all baselines in the map.
        :param boundaries_df: the geopandas GeoDataframe that contains all boundaries in the map.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        :param lane_connector_polygon_df: the geopandas GeoDataframe that contains polygons for lane connectors.
        """
        super().__init__(lane_id)
        self._lanes_df = lanes_df
        self._lane_connectors_df = lane_connectors_df
        self._baseline_paths_df = baseline_paths_df
        self._boundaries_df = boundaries_df
        self._stop_lines_df = stop_lines_df
        self._lane_connector_polygon_df = lane_connector_polygon_df
        self._lane = None
        self._map_data = map_data

    @cached_property
    def incoming_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        lane_connectors_ids = get_all_rows_with_value(self._lane_connectors_df, 'entry_lane_fid', self.id)['fid']
        return [lane_connector.NuPlanLaneConnector(lane_connector_id, self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connectors_ids.tolist()]

    @cached_property
    def outgoing_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        lane_connectors_ids = get_all_rows_with_value(self._lane_connectors_df, 'exit_lane_fid', self.id)['fid']
        return [lane_connector.NuPlanLaneConnector(lane_connector_id, self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connectors_ids.to_list()]

    @cached_property
    def parallel_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def baseline_path(self) -> PolylineMapObject:
        """Inherited from superclass."""
        return NuPlanPolylineMapObject(get_row_with_value(self._baseline_paths_df, 'lane_fid', self.id))

    @cached_property
    def left_boundary(self) -> PolylineMapObject:
        """Inherited from superclass."""
        boundary_fid = self._get_lane()['left_boundary_fid']
        return NuPlanPolylineMapObject(get_row_with_value(self._boundaries_df, 'fid', str(boundary_fid)))

    @cached_property
    def right_boundary(self) -> PolylineMapObject:
        """Inherited from superclass."""
        boundary_fid = self._get_lane()['right_boundary_fid']
        return NuPlanPolylineMapObject(get_row_with_value(self._boundaries_df, 'fid', str(boundary_fid)))

    def get_roadblock_id(self) -> str:
        """Inherited from superclass."""
        return str(self._get_lane()['lane_group_fid'])

    @cached_property
    def parent(self) -> RoadBlockGraphEdgeMapObject:
        """Inherited from superclass"""
        return self._map_data.get_map_object(self.get_roadblock_id(), SemanticMapLayer.ROADBLOCK)

    @cached_property
    def speed_limit_mps(self) -> Optional[float]:
        """Inherited from superclass."""
        speed_limit = self._get_lane()['speed_limit_mps']
        is_valid = speed_limit == speed_limit and speed_limit is not None
        return float(speed_limit) if is_valid else None

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._get_lane().geometry

    def is_left_of(self, other: Lane) -> bool:
        """Inherited from superclass."""
        assert self.is_same_roadblock(other), 'Lanes must be in the same roadblock'
        other_lane = get_row_with_value(self._lanes_df, 'fid', other.id)
        other_index = int(other_lane['lane_index'])
        self_index = int(self._get_lane()['lane_index'])
        return self_index < other_index

    def is_right_of(self, other: Lane) -> bool:
        """Inherited from superclass."""
        assert self.is_same_roadblock(other), 'Lanes must be in the same roadblock'
        other_lane = get_row_with_value(self._lanes_df, 'fid', other.id)
        other_index = int(other_lane['lane_index'])
        self_index = int(self._get_lane()['lane_index'])
        return self_index > other_index

    @cached_property
    def adjacent_edges(self) -> Tuple[Optional[LaneGraphEdgeMapObject], Optional[LaneGraphEdgeMapObject]]:
        """Inherited from superclass."""
        lane_group_fid = self._get_lane()['lane_group_fid']
        all_lanes = get_all_rows_with_value(self._lanes_df, 'lane_group_fid', lane_group_fid)
        lane_index = self._get_lane()['lane_index']
        left_lane_id = all_lanes[all_lanes['lane_index'] == int(lane_index) - 1]['fid']
        right_lane_id = all_lanes[all_lanes['lane_index'] == int(lane_index) + 1]['fid']
        left_lane = NuPlanLane(left_lane_id.item(), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) if not left_lane_id.empty else None
        right_lane = NuPlanLane(right_lane_id.item(), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) if not right_lane_id.empty else None
        return (left_lane, right_lane)

    def get_width_left_right(self, point: Point2D, include_outside: bool=False) -> Tuple[Optional[float], Optional[float]]:
        """Inherited from superclass."""
        raise NotImplementedError

    def oriented_distance(self, point: Point2D) -> float:
        """Inherited from superclass"""
        raise NotImplementedError

    def _get_lane(self) -> pd.Series:
        """
        Gets the series from the lane dataframe containing lane's id.
        :return: the respective series from the lanes dataframe.
        """
        if self._lane is None:
            self._lane = get_row_with_value(self._lanes_df, 'fid', self.id)
        return self._lane

    @cached_property
    def index(self) -> int:
        """Inherited from superclass"""
        return int(self._get_lane()['lane_index'])

@cached_property
def incoming_edges(self) -> List[LaneGraphEdgeMapObject]:
    """Inherited from superclass."""
    lane_connectors_ids = get_all_rows_with_value(self._lane_connectors_df, 'entry_lane_fid', self.id)['fid']
    return [lane_connector.NuPlanLaneConnector(lane_connector_id, self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connectors_ids.tolist()]

@cached_property
def outgoing_edges(self) -> List[LaneGraphEdgeMapObject]:
    """Inherited from superclass."""
    lane_connectors_ids = get_all_rows_with_value(self._lane_connectors_df, 'exit_lane_fid', self.id)['fid']
    return [lane_connector.NuPlanLaneConnector(lane_connector_id, self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connectors_ids.to_list()]

@cached_property
def adjacent_edges(self) -> Tuple[Optional[LaneGraphEdgeMapObject], Optional[LaneGraphEdgeMapObject]]:
    """Inherited from superclass."""
    lane_group_fid = self._get_lane()['lane_group_fid']
    all_lanes = get_all_rows_with_value(self._lanes_df, 'lane_group_fid', lane_group_fid)
    lane_index = self._get_lane()['lane_index']
    left_lane_id = all_lanes[all_lanes['lane_index'] == int(lane_index) - 1]['fid']
    right_lane_id = all_lanes[all_lanes['lane_index'] == int(lane_index) + 1]['fid']
    left_lane = NuPlanLane(left_lane_id.item(), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) if not left_lane_id.empty else None
    right_lane = NuPlanLane(right_lane_id.item(), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) if not right_lane_id.empty else None
    return (left_lane, right_lane)

def is_in_type(x: float, y: float, vector_layer: VectorLayer) -> bool:
    """
    Checks if position [x, y] is in any entry of type.
    :param x: [m] floating point x-coordinate in global frame.
    :param y: [m] floating point y-coordinate in global frame.
    :param vector_layer: vector layer to be searched through.
    :return True iff position [x, y] is in any entry of type, False if it is not.
    """
    assert vector_layer is not None, 'type can not be None!'
    in_polygon = vector_layer.contains(geom.Point(x, y))
    return any(in_polygon.values)

def get_row_with_value(elements: gpd.geodataframe.GeoDataFrame, column_label: str, desired_value: str) -> pd.Series:
    """
    Extract a matching element.
    :param elements: data frame from MapsDb.
    :param column_label: key to extract from a column.
    :param desired_value: key which is compared with the values of column_label entry.
    :return row from GeoDataFrame.
    """
    if column_label == 'fid':
        return elements.loc[desired_value]
    matching_rows = get_all_rows_with_value(elements, column_label, desired_value)
    assert len(matching_rows) > 0, f'Could not find the desired key = {desired_value}'
    assert len(matching_rows) == 1, f'{len(matching_rows)} matching keys found. Expected to only find one.Try using get_all_rows_with_value'
    return matching_rows.iloc[0]

def get_distance_between_map_object_and_point(point: Point2D, map_object: MapObject) -> float:
    """
    Get distance between point and nearest surface of specified map object.
    :param point: Point to calculate distance between.
    :param map_object: MapObject (containing underlying polygon) to check distance between.
    :return: Computed distance.
    """
    return float(geom.Point(point.x, point.y).distance(map_object.polygon))

class NuPlanMap(AbstractMap):
    """
    NuPlanMap implementation of Map API.
    """

    def __init__(self, maps_db: IMapsDB, map_name: str) -> None:
        """
        Initializes the map class.
        :param maps_db: MapsDB instance.
        :param map_name: Name of the map.
        """
        self._maps_db = maps_db
        self._vector_map: Dict[str, VectorLayer] = defaultdict(VectorLayer)
        self._raster_map: Dict[str, RasterLayer] = defaultdict(RasterLayer)
        self._map_objects: Dict[SemanticMapLayer, Dict[str, MapObject]] = defaultdict(dict)
        self._map_name = map_name
        self._map_object_getter: Dict[SemanticMapLayer, Callable[[str], MapObject]] = {SemanticMapLayer.LANE: self._get_lane, SemanticMapLayer.LANE_CONNECTOR: self._get_lane_connector, SemanticMapLayer.ROADBLOCK: self._get_roadblock, SemanticMapLayer.ROADBLOCK_CONNECTOR: self._get_roadblock_connector, SemanticMapLayer.STOP_LINE: self._get_stop_line, SemanticMapLayer.CROSSWALK: self._get_crosswalk, SemanticMapLayer.INTERSECTION: self._get_intersection, SemanticMapLayer.WALKWAYS: self._get_walkway, SemanticMapLayer.CARPARK_AREA: self._get_carpark_area}
        self._vector_layer_mapping = {SemanticMapLayer.LANE: 'lanes_polygons', SemanticMapLayer.ROADBLOCK: 'lane_groups_polygons', SemanticMapLayer.INTERSECTION: 'intersections', SemanticMapLayer.STOP_LINE: 'stop_polygons', SemanticMapLayer.CROSSWALK: 'crosswalks', SemanticMapLayer.DRIVABLE_AREA: 'drivable_area', SemanticMapLayer.LANE_CONNECTOR: 'lane_connectors', SemanticMapLayer.ROADBLOCK_CONNECTOR: 'lane_group_connectors', SemanticMapLayer.BASELINE_PATHS: 'baseline_paths', SemanticMapLayer.BOUNDARIES: 'boundaries', SemanticMapLayer.WALKWAYS: 'walkways', SemanticMapLayer.CARPARK_AREA: 'carpark_areas'}
        self._raster_layer_mapping = {SemanticMapLayer.DRIVABLE_AREA: 'drivable_area'}
        self._LANE_CONNECTOR_POLYGON_LAYER = 'gen_lane_connectors_scaled_width_polygons'

    def __reduce__(self) -> Tuple[Type['NuPlanMap'], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        This object is reconstructed by pickle to avoid serializing potentially large state/caches.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._maps_db, self._map_name))

    @property
    def map_name(self) -> str:
        """Inherited, see superclass."""
        return self._map_name

    def get_available_map_objects(self) -> List[SemanticMapLayer]:
        """Inherited, see superclass."""
        return list(self._map_object_getter.keys())

    def get_available_raster_layers(self) -> List[SemanticMapLayer]:
        """Inherited, see superclass."""
        return list(self._raster_layer_mapping.keys())

    def get_raster_map_layer(self, layer: SemanticMapLayer) -> RasterLayer:
        """Inherited, see superclass."""
        layer_id = self._semantic_raster_layer_map(layer)
        return self._load_raster_layer(layer_id)

    def get_raster_map(self, layers: List[SemanticMapLayer]) -> RasterMap:
        """Inherited, see superclass."""
        raster_map = RasterMap(layers=defaultdict(RasterLayer))
        for layer in layers:
            raster_map.layers[layer] = self.get_raster_map_layer(layer)
        return raster_map

    def is_in_layer(self, point: Point2D, layer: SemanticMapLayer) -> bool:
        """Inherited, see superclass."""
        if layer == SemanticMapLayer.TURN_STOP:
            stop_lines = self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)
            in_stop_line = stop_lines.loc[stop_lines.contains(geom.Point(point.x, point.y))]
            return any(in_stop_line.loc[in_stop_line['stop_polygon_type_fid'] == StopLineType.TURN_STOP.value].values)
        return bool(is_in_type(point.x, point.y, self._get_vector_map_layer(layer)))

    def get_all_map_objects(self, point: Point2D, layer: SemanticMapLayer) -> List[MapObject]:
        """Inherited, see superclass."""
        try:
            return self._get_all_map_objects(point, layer)
        except KeyError:
            raise ValueError(f'Object representation for layer: {layer.name} is unavailable')

    def get_one_map_object(self, point: Point2D, layer: SemanticMapLayer) -> Optional[MapObject]:
        """Inherited, see superclass."""
        map_objects = self.get_all_map_objects(point, layer)
        if len(map_objects) > 1:
            raise AssertionError(f'{len(map_objects)} map objects found. Expected only one. Try using get_all_map_objects()')
        if len(map_objects) == 0:
            return None
        return map_objects[0]

    def get_proximal_map_objects(self, point: Point2D, radius: float, layers: List[SemanticMapLayer]) -> Dict[SemanticMapLayer, List[MapObject]]:
        """Inherited, see superclass."""
        x_min, x_max = (point.x - radius, point.x + radius)
        y_min, y_max = (point.y - radius, point.y + radius)
        patch = geom.box(x_min, y_min, x_max, y_max)
        supported_layers = self.get_available_map_objects()
        unsupported_layers = [layer for layer in layers if layer not in supported_layers]
        assert len(unsupported_layers) == 0, f'Object representation for layer(s): {unsupported_layers} is unavailable'
        object_map: Dict[SemanticMapLayer, List[MapObject]] = defaultdict(list)
        for layer in layers:
            object_map[layer] = self._get_proximity_map_object(patch, layer)
        return object_map

    def get_map_object(self, object_id: str, layer: SemanticMapLayer) -> Optional[MapObject]:
        """Inherited, see superclass."""
        try:
            if object_id not in self._map_objects[layer]:
                map_object: MapObject = self._map_object_getter[layer](object_id)
                self._map_objects[layer][object_id] = map_object
            return self._map_objects[layer][object_id]
        except KeyError:
            raise ValueError(f'Object representation for layer: {layer.name} object: {object_id} is unavailable')

    def get_distance_to_nearest_map_object(self, point: Point2D, layer: SemanticMapLayer) -> Tuple[Optional[str], Optional[float]]:
        """Inherited from superclass."""
        surfaces = self._get_vector_map_layer(layer)
        if surfaces is not None:
            surfaces['distance_to_point'] = surfaces.apply(lambda row: geom.Point(point.x, point.y).distance(row.geometry), axis=1)
            surfaces = surfaces.sort_values(by='distance_to_point')
            nearest_surface = surfaces.iloc[0]
            nearest_surface_id = nearest_surface.fid
            nearest_surface_distance = nearest_surface.distance_to_point
        else:
            nearest_surface_id = None
            nearest_surface_distance = None
        return (nearest_surface_id, nearest_surface_distance)

    def get_distance_to_nearest_raster_layer(self, point: Point2D, layer: SemanticMapLayer) -> float:
        """Inherited from superclass"""
        raise NotImplementedError

    def get_distances_matrix_to_nearest_map_object(self, points: List[Point2D], layer: SemanticMapLayer) -> Optional[npt.NDArray[np.float64]]:
        """
        Returns the distance matrix (in meters) between a list of points and their nearest desired surface.
            That distance is the L1 norm from the point to the closest location on the surface.
        :param points: [m] A list of x, y coordinates in global frame.
        :param layer: A semantic layer to query.
        :return: An array of shortest distance from each point to the nearest desired surface.
        """
        surfaces = self._get_vector_map_layer(layer)
        if surfaces is not None:
            corner_points = geopandas.GeoSeries([geom.Point(point.x, point.y) for point in points])
            distances = surfaces.geometry.apply(lambda g: corner_points.distance(g))
            distances = np.asarray(distances.min())
            return cast(npt.NDArray[np.float64], distances)
        else:
            return None

    def initialize_all_layers(self) -> None:
        """
        Load all layers to vector map
        :param: None
        :return: None
        """
        for layer_name in self._vector_layer_mapping.values():
            self._load_vector_map_layer(layer_name)
        for layer_name in self._raster_layer_mapping.values():
            self._load_vector_map_layer(layer_name)
        self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER)

    def _semantic_vector_layer_map(self, layer: SemanticMapLayer) -> str:
        """
        Mapping from SemanticMapLayer int to MapsDB internal representation of vector layers.
        :param layer: The querired semantic map layer.
        :return: A internal layer name as a string.
        @raise ValueError if the requested layer does not exist for MapsDBMap
        """
        try:
            return self._vector_layer_mapping[layer]
        except KeyError:
            raise ValueError('Unknown layer: {}'.format(layer.name))

    def _semantic_raster_layer_map(self, layer: SemanticMapLayer) -> str:
        """
        Mapping from SemanticMapLayer int to MapsDB internal representation of raster layers.
        :param layer: The queried semantic map layer.
        :return: A internal layer name as a string.
        @raise ValueError if the requested layer does not exist for MapsDBMap
        """
        try:
            return self._raster_layer_mapping[layer]
        except KeyError:
            raise ValueError('Unknown layer: {}'.format(layer.name))

    def _get_vector_map_layer(self, layer: SemanticMapLayer) -> VectorLayer:
        """Inherited, see superclass."""
        layer_id = self._semantic_vector_layer_map(layer)
        return self._load_vector_map_layer(layer_id)

    def _load_raster_layer(self, layer_name: str) -> RasterLayer:
        """
        Load and cache raster layers.
        :layer_name: the name of the vector layer to be loaded.
        :return: the loaded RasterLayer.
        """
        if layer_name not in self._raster_map:
            map_layer: MapLayer = self._maps_db.load_layer(self._map_name, layer_name)
            self._raster_map[layer_name] = raster_layer_from_map_layer(map_layer)
        return self._raster_map[layer_name]

    def _load_vector_map_layer(self, layer_name: str) -> VectorLayer:
        """
        Load and cache vector layers.
        :layer_name: the name of the vector layer to be loaded.
        :return: the loaded VectorLayer.
        """
        if layer_name not in self._vector_map:
            if layer_name == 'drivable_area':
                self._initialize_drivable_area()
            else:
                self._vector_map[layer_name] = self._maps_db.load_vector_layer(self._map_name, layer_name)
        return self._vector_map[layer_name]

    def _get_all_map_objects(self, point: Point2D, layer: SemanticMapLayer) -> List[MapObject]:
        """
        Gets a list of lanes where its polygon overlaps the queried point.
        :param point: [m] x, y coordinates in global frame.
        :return: a list of lanes. An empty list if no lanes were found.
        """
        if layer == SemanticMapLayer.LANE_CONNECTOR:
            return self._get_all_lane_connectors(point)
        else:
            layer_df = self._get_vector_map_layer(layer)
            ids = layer_df.loc[layer_df.contains(geom.Point(point.x, point.y))]['fid'].tolist()
            return [self.get_map_object(map_object_id, layer) for map_object_id in ids]

    def _get_all_lane_connectors(self, point: Point2D) -> List[LaneConnector]:
        """
        Gets a list of lane connectors where its polygon overlaps the queried point.
        :param point: [m] x, y coordinates in global frame.
        :return: a list of lane connectors. An empty list if no lane connectors were found.
        """
        lane_connectors_df = self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER)
        ids = lane_connectors_df.loc[lane_connectors_df.contains(geom.Point(point.x, point.y))]['lane_connector_fid'].tolist()
        lane_connector_ids = list(map(str, ids))
        return [self._get_lane_connector(lane_connector_id) for lane_connector_id in lane_connector_ids]

    def _get_proximity_map_object(self, patch: geom.Polygon, layer: SemanticMapLayer) -> List[MapObject]:
        """
        Gets nearby lanes within the given patch.
        :param patch: The area to be checked.
        :param layer: desired layer to check.
        :return: A list of map objects.
        """
        layer_df = self._get_vector_map_layer(layer)
        map_object_ids = layer_df[layer_df['geometry'].intersects(patch)]['fid']
        return [self.get_map_object(map_object_id, layer) for map_object_id in map_object_ids]

    def _get_lane(self, lane_id: str) -> Lane:
        """
        Gets the lane with the given lane id.
        :param lane_id: Desired unique id of a lane that should be extracted.
        :return: Lane object.
        """
        return NuPlanLane(lane_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if int(lane_id) in self._get_vector_map_layer(SemanticMapLayer.LANE)['lane_fid'].tolist() else None

    def _get_lane_connector(self, lane_connector_id: str) -> LaneConnector:
        """
        Gets the lane connector with the given lane_connector_id.
        :param lane_connector_id: Desired unique id of a lane connector that should be extracted.
        :return: LaneConnector object.
        """
        return NuPlanLaneConnector(lane_connector_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if lane_connector_id in self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR)['fid'].tolist() else None

    def _get_roadblock(self, roadblock_id: str) -> RoadBlockGraphEdgeMapObject:
        """
        Gets the roadblock with the given roadblock_id.
        :param roadblock_id: Desired unique id of a roadblock that should be extracted.
        :return: RoadBlock object.
        """
        return NuPlanRoadBlock(roadblock_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._get_vector_map_layer(SemanticMapLayer.INTERSECTION), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if roadblock_id in self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK)['fid'].tolist() else None

    def _get_roadblock_connector(self, roadblock_connector_id: str) -> RoadBlockGraphEdgeMapObject:
        """
        Gets the roadblock connector with the given roadblock_connector_id.
        :param roadblock_connector_id: Desired unique id of a roadblock connector that should be extracted.
        :return: RoadBlockConnector object.
        """
        return NuPlanRoadBlockConnector(roadblock_connector_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._get_vector_map_layer(SemanticMapLayer.INTERSECTION), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if roadblock_connector_id in self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR)['fid'].tolist() else None

    def _initialize_drivable_area(self) -> None:
        """
        Drivable area is considered as the union of road_segments, intersections and generic_drivable_areas.
        Hence, the three layers has to be joined to cover all drivable areas.
        """
        road_segments = self._load_vector_map_layer('road_segments')
        intersections = self._load_vector_map_layer('intersections')
        generic_drivable_areas = self._load_vector_map_layer('generic_drivable_areas')
        car_parks = self._load_vector_map_layer('carpark_areas')
        self._vector_map['drivable_area'] = pd.concat([road_segments, intersections, generic_drivable_areas, car_parks]).dropna(axis=1, how='any')

    def _get_stop_line(self, stop_line_id: str) -> StopLine:
        """
        Gets the stop line with the given stop_line_id.
        :param stop_line_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
        return NuPlanStopLine(stop_line_id, self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)) if stop_line_id in self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)['fid'].tolist() else None

    def _get_crosswalk(self, crosswalk_id: str) -> NuPlanPolygonMapObject:
        """
        Gets the stop line with the given crosswalk_id.
        :param crosswalk_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
        return NuPlanPolygonMapObject(crosswalk_id, self._get_vector_map_layer(SemanticMapLayer.CROSSWALK)) if crosswalk_id in self._get_vector_map_layer(SemanticMapLayer.CROSSWALK)['fid'].tolist() else None

    def _get_intersection(self, intersection_id: str) -> Intersection:
        """
        Gets the stop line with the given stop_line_id.
        :param intersection_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
        return NuPlanIntersection(intersection_id, self._get_vector_map_layer(SemanticMapLayer.INTERSECTION)) if intersection_id in self._get_vector_map_layer(SemanticMapLayer.INTERSECTION)['fid'].tolist() else None

    def _get_walkway(self, walkway_id: str) -> NuPlanPolygonMapObject:
        """
        Gets the walkway with the given walkway_id.
        :param walkway_id: desired unique id of a walkway that should be extracted.
        :return: NuPlanPolygonMapObject object.
        """
        return NuPlanPolygonMapObject(walkway_id, self._get_vector_map_layer(SemanticMapLayer.WALKWAYS)) if walkway_id in self._get_vector_map_layer(SemanticMapLayer.WALKWAYS)['fid'].tolist() else None

    def _get_carpark_area(self, carpark_area_id: str) -> NuPlanPolygonMapObject:
        """
        Gets the car park area with the given car_park_area_id.
        :param carpark_area_id: desired unique id of a car park that should be extracted.
        :return: NuPlanPolygonMapObject object.
        """
        return NuPlanPolygonMapObject(carpark_area_id, self._get_vector_map_layer(SemanticMapLayer.CARPARK_AREA)) if carpark_area_id in self._get_vector_map_layer(SemanticMapLayer.CARPARK_AREA)['fid'].tolist() else None

def is_in_layer(self, point: Point2D, layer: SemanticMapLayer) -> bool:
    """Inherited, see superclass."""
    if layer == SemanticMapLayer.TURN_STOP:
        stop_lines = self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)
        in_stop_line = stop_lines.loc[stop_lines.contains(geom.Point(point.x, point.y))]
        return any(in_stop_line.loc[in_stop_line['stop_polygon_type_fid'] == StopLineType.TURN_STOP.value].values)
    return bool(is_in_type(point.x, point.y, self._get_vector_map_layer(layer)))

def get_distance_to_nearest_map_object(self, point: Point2D, layer: SemanticMapLayer) -> Tuple[Optional[str], Optional[float]]:
    """Inherited from superclass."""
    surfaces = self._get_vector_map_layer(layer)
    if surfaces is not None:
        surfaces['distance_to_point'] = surfaces.apply(lambda row: geom.Point(point.x, point.y).distance(row.geometry), axis=1)
        surfaces = surfaces.sort_values(by='distance_to_point')
        nearest_surface = surfaces.iloc[0]
        nearest_surface_id = nearest_surface.fid
        nearest_surface_distance = nearest_surface.distance_to_point
    else:
        nearest_surface_id = None
        nearest_surface_distance = None
    return (nearest_surface_id, nearest_surface_distance)

def get_distances_matrix_to_nearest_map_object(self, points: List[Point2D], layer: SemanticMapLayer) -> Optional[npt.NDArray[np.float64]]:
    """
        Returns the distance matrix (in meters) between a list of points and their nearest desired surface.
            That distance is the L1 norm from the point to the closest location on the surface.
        :param points: [m] A list of x, y coordinates in global frame.
        :param layer: A semantic layer to query.
        :return: An array of shortest distance from each point to the nearest desired surface.
        """
    surfaces = self._get_vector_map_layer(layer)
    if surfaces is not None:
        corner_points = geopandas.GeoSeries([geom.Point(point.x, point.y) for point in points])
        distances = surfaces.geometry.apply(lambda g: corner_points.distance(g))
        distances = np.asarray(distances.min())
        return cast(npt.NDArray[np.float64], distances)
    else:
        return None

def _get_vector_map_layer(self, layer: SemanticMapLayer) -> VectorLayer:
    """Inherited, see superclass."""
    layer_id = self._semantic_vector_layer_map(layer)
    return self._load_vector_map_layer(layer_id)

def _get_all_map_objects(self, point: Point2D, layer: SemanticMapLayer) -> List[MapObject]:
    """
        Gets a list of lanes where its polygon overlaps the queried point.
        :param point: [m] x, y coordinates in global frame.
        :return: a list of lanes. An empty list if no lanes were found.
        """
    if layer == SemanticMapLayer.LANE_CONNECTOR:
        return self._get_all_lane_connectors(point)
    else:
        layer_df = self._get_vector_map_layer(layer)
        ids = layer_df.loc[layer_df.contains(geom.Point(point.x, point.y))]['fid'].tolist()
        return [self.get_map_object(map_object_id, layer) for map_object_id in ids]

def _get_all_lane_connectors(self, point: Point2D) -> List[LaneConnector]:
    """
        Gets a list of lane connectors where its polygon overlaps the queried point.
        :param point: [m] x, y coordinates in global frame.
        :return: a list of lane connectors. An empty list if no lane connectors were found.
        """
    lane_connectors_df = self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER)
    ids = lane_connectors_df.loc[lane_connectors_df.contains(geom.Point(point.x, point.y))]['lane_connector_fid'].tolist()
    lane_connector_ids = list(map(str, ids))
    return [self._get_lane_connector(lane_connector_id) for lane_connector_id in lane_connector_ids]

def _get_lane(self, lane_id: str) -> Lane:
    """
        Gets the lane with the given lane id.
        :param lane_id: Desired unique id of a lane that should be extracted.
        :return: Lane object.
        """
    return NuPlanLane(lane_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if int(lane_id) in self._get_vector_map_layer(SemanticMapLayer.LANE)['lane_fid'].tolist() else None

def _get_lane_connector(self, lane_connector_id: str) -> LaneConnector:
    """
        Gets the lane connector with the given lane_connector_id.
        :param lane_connector_id: Desired unique id of a lane connector that should be extracted.
        :return: LaneConnector object.
        """
    return NuPlanLaneConnector(lane_connector_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if lane_connector_id in self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR)['fid'].tolist() else None

def _get_roadblock(self, roadblock_id: str) -> RoadBlockGraphEdgeMapObject:
    """
        Gets the roadblock with the given roadblock_id.
        :param roadblock_id: Desired unique id of a roadblock that should be extracted.
        :return: RoadBlock object.
        """
    return NuPlanRoadBlock(roadblock_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._get_vector_map_layer(SemanticMapLayer.INTERSECTION), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if roadblock_id in self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK)['fid'].tolist() else None

def _get_roadblock_connector(self, roadblock_connector_id: str) -> RoadBlockGraphEdgeMapObject:
    """
        Gets the roadblock connector with the given roadblock_connector_id.
        :param roadblock_connector_id: Desired unique id of a roadblock connector that should be extracted.
        :return: RoadBlockConnector object.
        """
    return NuPlanRoadBlockConnector(roadblock_connector_id, self._get_vector_map_layer(SemanticMapLayer.LANE), self._get_vector_map_layer(SemanticMapLayer.LANE_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.BASELINE_PATHS), self._get_vector_map_layer(SemanticMapLayer.BOUNDARIES), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK), self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR), self._get_vector_map_layer(SemanticMapLayer.STOP_LINE), self._get_vector_map_layer(SemanticMapLayer.INTERSECTION), self._load_vector_map_layer(self._LANE_CONNECTOR_POLYGON_LAYER), self) if roadblock_connector_id in self._get_vector_map_layer(SemanticMapLayer.ROADBLOCK_CONNECTOR)['fid'].tolist() else None

def _get_stop_line(self, stop_line_id: str) -> StopLine:
    """
        Gets the stop line with the given stop_line_id.
        :param stop_line_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
    return NuPlanStopLine(stop_line_id, self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)) if stop_line_id in self._get_vector_map_layer(SemanticMapLayer.STOP_LINE)['fid'].tolist() else None

def _get_crosswalk(self, crosswalk_id: str) -> NuPlanPolygonMapObject:
    """
        Gets the stop line with the given crosswalk_id.
        :param crosswalk_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
    return NuPlanPolygonMapObject(crosswalk_id, self._get_vector_map_layer(SemanticMapLayer.CROSSWALK)) if crosswalk_id in self._get_vector_map_layer(SemanticMapLayer.CROSSWALK)['fid'].tolist() else None

def _get_intersection(self, intersection_id: str) -> Intersection:
    """
        Gets the stop line with the given stop_line_id.
        :param intersection_id: desired unique id of a stop line that should be extracted.
        :return: NuPlanStopLine object.
        """
    return NuPlanIntersection(intersection_id, self._get_vector_map_layer(SemanticMapLayer.INTERSECTION)) if intersection_id in self._get_vector_map_layer(SemanticMapLayer.INTERSECTION)['fid'].tolist() else None

def _get_walkway(self, walkway_id: str) -> NuPlanPolygonMapObject:
    """
        Gets the walkway with the given walkway_id.
        :param walkway_id: desired unique id of a walkway that should be extracted.
        :return: NuPlanPolygonMapObject object.
        """
    return NuPlanPolygonMapObject(walkway_id, self._get_vector_map_layer(SemanticMapLayer.WALKWAYS)) if walkway_id in self._get_vector_map_layer(SemanticMapLayer.WALKWAYS)['fid'].tolist() else None

def _get_carpark_area(self, carpark_area_id: str) -> NuPlanPolygonMapObject:
    """
        Gets the car park area with the given car_park_area_id.
        :param carpark_area_id: desired unique id of a car park that should be extracted.
        :return: NuPlanPolygonMapObject object.
        """
    return NuPlanPolygonMapObject(carpark_area_id, self._get_vector_map_layer(SemanticMapLayer.CARPARK_AREA)) if carpark_area_id in self._get_vector_map_layer(SemanticMapLayer.CARPARK_AREA)['fid'].tolist() else None

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

@cached_property
def discrete_path(self) -> List[StateSE2]:
    """Inherited from superclass."""
    return cast(List[StateSE2], extract_discrete_polyline(self._polyline))

def get_nearest_arc_length_from_position(self, point: Point2D) -> float:
    """Inherited from superclass."""
    return self._polyline.project(Point(point.x, point.y))

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
def speed_limit_mps(self) -> Optional[float]:
    """Inherited from superclass."""
    speed_limit = self._get_lane_connector()['speed_limit_mps']
    is_valid = speed_limit == speed_limit and speed_limit is not None
    return float(speed_limit) if is_valid else None

def get_roadblock_id(self) -> str:
    """Inherited from superclass."""
    return str(self._get_lane_connector()['lane_group_connector_fid'])

def has_traffic_lights(self) -> bool:
    """Inherited from superclass."""
    return bool(self._get_lane_connector()['traffic_light_stop_line_fids'])

def distance_to_stop_line(stop_line: StopLine) -> float:
    """
            Calculates the distance between the first point of the lane connector's baseline path
            :param stop_line: The stop line to calculate the distance to.
            :return: [m] The distance between first point points of the lane connector to the stop_line polygon.
            """
    start = Point(self.baseline_path.linestring.coords[0])
    return float(start.distance(stop_line.polygon))

class NuPlanRoadBlockConnector(RoadBlockGraphEdgeMapObject):
    """
    NuPlanMap implmentation of Roadblock Connector.
    """

    def __init__(self, roadblock_connector_id: str, lanes_df: VectorLayer, lane_connectors_df: VectorLayer, baseline_paths_df: VectorLayer, boundaries_df: VectorLayer, roadblocks_df: VectorLayer, roadblock_connectors_df: VectorLayer, stop_lines_df: VectorLayer, intersections_df: VectorLayer, lane_connector_polygon_df: VectorLayer, map_data: AbstractMap):
        """
        Constructor of NuPlanLaneConnector.
        :param roadblock_connector_id: unique identifier of the roadblock connector.
        :param lanes_df: the geopandas GeoDataframe that contains all lanes in the map.
        :param lane_connectors_df: the geopandas GeoDataframe that contains all lane connectors in the map.
        :param baseline_paths_df: the geopandas GeoDataframe that contains all baselines in the map.
        :param boundaries_df: the geopandas GeoDataframe that contains all boundaries in the map.
        :param roadblocks_df: the geopandas GeoDataframe that contains all roadblocks (lane groups) in the map.
        :param roadblock_connectors_df: the geopandas GeoDataframe that contains all roadblock connectors (lane group
            connectors) in the map.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        :param lane_connector_polygon_df: the geopandas GeoDataframe that contains polygons for lane connectors.
        """
        super().__init__(roadblock_connector_id)
        self._lanes_df = lanes_df
        self._lane_connectors_df = lane_connectors_df
        self._baseline_paths_df = baseline_paths_df
        self._boundaries_df = boundaries_df
        self._roadblocks_df = roadblocks_df
        self._roadblock_connectors_df = roadblock_connectors_df
        self._stop_lines_df = stop_lines_df
        self._lane_connector_polygon_df = lane_connector_polygon_df
        self._intersections_df = intersections_df
        self._map_data = map_data

    @cached_property
    def incoming_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        incoming_roadblock_id = self._roadblock_connector['from_lane_group_fid']
        return [roadblock.NuPlanRoadBlock(str(incoming_roadblock_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data)]

    @cached_property
    def outgoing_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        outgoing_roadblock_id = self._roadblock_connector['to_lane_group_fid']
        return [roadblock.NuPlanRoadBlock(str(outgoing_roadblock_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data)]

    @cached_property
    def interior_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass."""
        lane_connector_ids = get_all_rows_with_value(self._lane_connectors_df, 'lane_group_connector_fid', self.id)['fid']
        return [NuPlanLaneConnector(str(lane_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connector_ids.to_list()]

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._roadblock_connector.geometry

    @cached_property
    def children_stop_lines(self) -> List[StopLine]:
        """Inherited from superclass."""
        raise NotImplementedError

    @cached_property
    def parallel_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """Inherited from superclass."""
        raise NotImplementedError

    @cached_property
    def _roadblock_connector(self) -> pd.Series:
        """
        Gets the series from the roadblock connector dataframe containing roadblock connector's id.
        :return: the respective series from the roadblock connectors dataframe.
        """
        return get_row_with_value(self._roadblock_connectors_df, 'fid', self.id)

    @property
    def intersection(self) -> Optional[Intersection]:
        """Inherited from superclass."""
        intersection_id = str(self._roadblock_connector['intersection_fid'])
        return intersection.NuPlanIntersection(intersection_id, self._intersections_df)

@cached_property
def interior_edges(self) -> List[LaneGraphEdgeMapObject]:
    """Inherited from superclass."""
    lane_connector_ids = get_all_rows_with_value(self._lane_connectors_df, 'lane_group_connector_fid', self.id)['fid']
    return [NuPlanLaneConnector(str(lane_connector_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._stop_lines_df, self._lane_connector_polygon_df, self._map_data) for lane_connector_id in lane_connector_ids.to_list()]

@property
def intersection(self) -> Optional[Intersection]:
    """Inherited from superclass."""
    intersection_id = str(self._roadblock_connector['intersection_fid'])
    return intersection.NuPlanIntersection(intersection_id, self._intersections_df)

def test_get_drivable_area(map_factory: NuPlanMapFactory) -> None:
    """Tests drivable area construction"""
    nuplan_map = map_factory.build_map_from_name('us-nv-las-vegas-strip')
    target_layer = 'drivable_area'
    base_layers = ['road_segments', 'intersections', 'generic_drivable_areas', 'carpark_areas']
    all_layers = base_layers + [target_layer]
    assert not any((layer in nuplan_map._vector_map.keys() for layer in all_layers))
    nuplan_map._load_vector_map_layer(target_layer)
    assert all((layer in nuplan_map._vector_map.keys() for layer in all_layers))
    drivable_fids = nuplan_map._vector_map[target_layer]['fid'].to_list()
    base_fids = [fid for layer in base_layers for fid in nuplan_map._vector_map[layer]['fid'].to_list()]
    assert sorted(drivable_fids) == sorted(base_fids)

class TimeDuration:
    """Class representing a time delta, with a microsecond resolution."""
    __slots__ = '_time_us'

    def __init__(self, *, time_us: int, _direct: bool=True) -> None:
        """Constructor, should not be called directly. Raises if the keyword parameter _direct is not set to false."""
        if _direct:
            raise RuntimeError("Don't initialize this class directly, use one of the constructors instead!")
        self._time_us = time_us

    @classmethod
    def from_us(cls, t_us: int) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in microseconds.
        :param t_us: Time in microseconds.
        :return: TimeDuration.
        """
        assert isinstance(t_us, int), 'Microseconds must be an integer!'
        return cls(time_us=t_us, _direct=False)

    @classmethod
    def from_ms(cls, t_ms: float) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in milliseconds.
        :param t_ms: Time in milliseconds.
        :return: TimeDuration.
        """
        return cls(time_us=int(t_ms * int(1000.0)), _direct=False)

    @classmethod
    def from_s(cls, t_s: float) -> TimeDuration:
        """
        Constructs a TimeDuration from a value in seconds.
        :param t_s: Time in seconds.
        :return: TimeDuration.
        """
        return cls(time_us=int(t_s * int(1000000.0)), _direct=False)

    @property
    def time_us(self) -> int:
        """
        :return: TimeDuration in microseconds.
        """
        return self._time_us

    @property
    def time_ms(self) -> float:
        """
        :return: TimeDuration in milliseconds.
        """
        return self._time_us / 1000.0

    @property
    def time_s(self) -> float:
        """
        :return: TimeDuration in seconds.
        """
        return self._time_us / 1000000.0

    def __add__(self, other: object) -> TimeDuration:
        """
        Adds a time duration to a time duration.
        :param other: time duration.
        :return: self + other if other is a TimeDuration.
        """
        if isinstance(other, TimeDuration):
            return TimeDuration.from_us(self.time_us + other.time_us)
        return NotImplemented

    def __sub__(self, other: object) -> TimeDuration:
        """
        Subtract a time duration from a time duration.
        :param other: time duration.
        :return: self - other if other is a TimeDuration.
        """
        if isinstance(other, TimeDuration):
            return TimeDuration.from_us(self.time_us - other.time_us)
        return NotImplemented

    def __mul__(self, other: object) -> TimeDuration:
        """
        Multiply a time duration by a scalar value.
        :param other: value to multiply.
        :return: self * other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s * other)
        return NotImplemented

    def __rmul__(self, other: object) -> TimeDuration:
        """
        Multiply a time duration by a scalar value.
        :param other: value to multiply.
        :return: self * other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return self * other
        return NotImplemented

    def __truediv__(self, other: object) -> TimeDuration:
        """
        Divides a time duration by a scalar value.
        :param other: value to divide for.
        :return: self / other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s / other)
        return NotImplemented

    def __floordiv__(self, other: object) -> TimeDuration:
        """
        Floor divides a time duration by a scalar value.
        :param other: value to divide for.
        :return: self // other if other is a scalar.
        """
        if isinstance(other, (int, float)):
            return TimeDuration.from_s(self.time_s // other)
        return NotImplemented

    def __gt__(self, other: TimeDuration) -> bool:
        """
        Self is greater than other.
        :param other: TimeDuration.
        :return: True if self > other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us > other.time_us
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        """
        Self is greater or equal than other.
        :param other: TimeDuration.
        :return: True if self >= other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us >= other.time_us
        return NotImplemented

    def __lt__(self, other: TimeDuration) -> bool:
        """
        Self is less than other.
        :param other: TimeDuration.
        :return: True if self < other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us < other.time_us
        return NotImplemented

    def __le__(self, other: TimeDuration) -> bool:
        """
        Self is less or equal than other.
        :param other: TimeDuration.
        :return: True if self <= other, False otherwise.
        """
        if isinstance(other, TimeDuration):
            return self.time_us <= other.time_us
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """
        Self is equal to other.
        :param other: TimeDuration.
        :return: True if self == other, False otherwise.
        """
        if not isinstance(other, TimeDuration):
            return NotImplemented
        return self.time_us == other.time_us

    def __hash__(self) -> int:
        """
        :return: hash for this object.
        """
        return hash(self.time_us)

    def __repr__(self) -> str:
        """
        :return: String representation.
        """
        return 'TimeDuration({}s)'.format(self.time_s)

def __hash__(self) -> int:
    """
        :return: hash for this object.
        """
    return hash(self.time_us)

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

def __hash__(self) -> int:
    """
        :return: hash for this object
        """
    return hash(self.time_us)

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

def __hash__(self) -> int:
    """Hash method"""
    return hash((self.x, self.y))

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

def __hash__(self) -> int:
    """
        :return: hash for this object
        """
    return hash((self.x, self.y, self.heading))

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

def __hash__(self) -> int:
    """
        :return: hash for this object
        """
    return hash((self.center, self.width, self.height, self.length))

def in_collision(box1: OrientedBox, box2: OrientedBox, radius_threshold: Optional[float]=None) -> bool:
    """
    Check for collision between two boxes. First do a quick check by approximating each box with a circle of given radius,
    if there is an overlap, check for the exact intersection using geometry Polygon
    :param box1: Oriented box (e.g., of ego)
    :param box2: Oriented box (e.g., of other tracks)
    :param radius: Radius for quick collision check
    :return True if there is a collision between the two boxes.
    """
    return bool(box1.geometry.intersects(box2.geometry)) if collision_by_radius_check(box1, box2, radius_threshold) else False

class TrackedObjectType(Enum):
    """Enum of classification types for TrackedObject."""
    VEHICLE = (0, 'vehicle')
    PEDESTRIAN = (1, 'pedestrian')
    BICYCLE = (2, 'bicycle')
    TRAFFIC_CONE = (3, 'traffic_cone')
    BARRIER = (4, 'barrier')
    CZONE_SIGN = (5, 'czone_sign')
    GENERIC_OBJECT = (6, 'generic_object')
    EGO = (7, 'ego')

    def __int__(self) -> int:
        """
        Convert an element to int
        :return: int
        """
        return self.value

    def __new__(cls, value: int, name: str) -> TrackedObjectType:
        """
        Create new element
        :param value: its value
        :param name: its name
        """
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = name
        return member

    def __eq__(self, other: object) -> bool:
        """
        Equality checking
        :return: int
        """
        try:
            return self.name == other.name and self.value == other.value
        except AttributeError:
            return NotImplemented

    def __hash__(self) -> int:
        """Hash"""
        return hash((self.name, self.value))

def __hash__(self) -> int:
    """Hash"""
    return hash((self.name, self.value))

class VehicleParameters(BoxParameters):
    """
    Class holding parameters of a vehicle
    """

    def __init__(self, width: float, front_length: float, rear_length: float, cog_position_from_rear_axle: float, wheel_base: float, vehicle_name: str, vehicle_type: str, height: Optional[float]=None):
        """
        :param width: [m] width of box around vehicle
        :param front_length: [m] distance between rear axle and front bumper
        :param rear_length: [m] distance between rear axle and rear bumper
        :param cog_position_from_rear_axle: [m] distance between rear axle and center of gravity (cog)
        :param wheel_base: [m] wheel base of the vehicle
        :param vehicle_name: name of the vehicle
        :param vehicle_type: type of the vehicle
        :param height: [m] height of box around vehicle
        """
        self.width = width
        self.front_length = front_length
        self.rear_length = rear_length
        self.wheel_base = wheel_base
        self.length = front_length + rear_length
        self.cog_position_from_rear_axle = cog_position_from_rear_axle
        self.height = height
        self.vehicle_name = vehicle_name
        self.vehicle_type = vehicle_type

    def __reduce__(self) -> Tuple[Type[VehicleParameters], Tuple[Any, ...]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self.width, self.front_length, self.rear_length, self.cog_position_from_rear_axle, self.wheel_base, self.vehicle_name, self.vehicle_type, self.height))

    @property
    def rear_axle_to_center(self) -> float:
        """
        :return: [m] distance between rear axle and center of vehicle
        """
        return self.half_length - self.rear_length

    @property
    def length_cog_to_front_axle(self) -> float:
        """
        :return: [m] distance between cog and front axle
        """
        return self.wheel_base - self.cog_position_from_rear_axle

    def __hash__(self) -> int:
        """
        :return: hash vehicle parameters
        """
        return hash((self.vehicle_name, self.vehicle_type, self.width, self.front_length, self.rear_length, self.cog_position_from_rear_axle, self.wheel_base, self.height))

    def __str__(self) -> str:
        """
        :return: string for this class
        """
        return f'VehicleParameters(vehicle_name={self.vehicle_name}, vehicle_type={self.vehicle_type}, width={self.width}, front_length={self.front_length}, rear_length={self.rear_length}, cog_position_from_rear_axle={self.cog_position_from_rear_axle}, wheel_base={self.wheel_base}, height={self.height}, width={self.width})'

def __hash__(self) -> int:
    """
        :return: hash vehicle parameters
        """
    return hash((self.vehicle_name, self.vehicle_type, self.width, self.front_length, self.rear_length, self.cog_position_from_rear_axle, self.wheel_base, self.height))

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

def test_get_subset(self) -> None:
    """Tests that the object can be created correctly."""
    tracked_objects = TrackedObjects(self.agents)
    agents = tracked_objects.get_agents()
    static_objects = tracked_objects.get_static_objects()
    self.assertEqual(3, len(agents))
    self.assertEqual(0, len(static_objects))

def interpolate_tracks(tracked_objects: Union[TrackedObjects, List[TrackedObject]], horizon_len_s: float, interval_s: float) -> List[TrackedObject]:
    """
    Interpolate agent's predictions and past trajectory, if not enough states are present, add NONE!
    :param tracked_objects: agents to be interpolated
    :param horizon_len_s: [s] horizon from initial waypoint
    :param interval_s: [s] interval between two states
    :return: interpolated agents
    """
    all_tracked_objects = tracked_objects if isinstance(tracked_objects, TrackedObjects) else TrackedObjects(tracked_objects)
    return [interpolate_agent(agent, horizon_len_s=horizon_len_s, interval_s=interval_s) for agent in all_tracked_objects.get_agents()] + cast(List[TrackedObject], all_tracked_objects.get_static_objects())

def interpolate_future_waypoints(waypoints: List[InterpolatableState], horizon_len_s: float, interval_s: float) -> List[Optional[InterpolatableState]]:
    """
    Interpolate waypoints which are in the future. If not enough waypoints are provided, we append None
    :param waypoints: list of waypoints, there needs to be at least one
    :param horizon_len_s: [s] time distance to future
    :param interval_s: [s] interval between two states
    :return: interpolated waypoints
    """
    _validate_waypoints(waypoints)
    start_timestamp = waypoints[0].time_us
    end_timestamp = int(start_timestamp + horizon_len_s * 1000000.0)
    target_timestamps, num_future_boxes = _compute_desired_time_steps(start_timestamp, end_timestamp, horizon_len_s=horizon_len_s, interval_s=interval_s)
    if len(waypoints) == 1:
        return waypoints + cast(List[Optional[InterpolatableState]], [None] * (num_future_boxes - 1))
    return _interpolate_waypoints(waypoints, target_timestamps)

def interpolate_past_waypoints(waypoints: List[InterpolatableState], horizon_len_s: float, interval_s: float) -> List[Optional[InterpolatableState]]:
    """
    Interpolate waypoints which are in the past. We assume that they are still monotonically increasing.
        If not enough waypoints are provided, we append None
    :param waypoints: list of waypoints, there needs to be at least one
    :param horizon_len_s: [s] time distance to past
    :param interval_s: [s] interval between two states
    :return: interpolated waypoints
    """
    _validate_waypoints(waypoints)
    end_timestamp = waypoints[-1].time_us
    start_timestamp = max(int(end_timestamp - horizon_len_s * 1000000.0), 0)
    target_timestamps, num_future_boxes = _compute_desired_time_steps(start_timestamp, end_timestamp, horizon_len_s=horizon_len_s, interval_s=interval_s)
    if len(waypoints) == 1:
        return cast(List[Optional[InterpolatableState]], [None] * (num_future_boxes - 1)) + waypoints
    sampled_trajectory = _interpolate_waypoints(waypoints, target_timestamps)
    if not sampled_trajectory[-1]:
        raise RuntimeError('Last state of the trajectory has to be existent!')
    return sampled_trajectory

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

def test_to_list(self) -> None:
    """
        Tests to list method.
        """
    result = self.color.to_list()
    self.assertEqual(result, [self.red, self.green, self.blue, self.alpha])

def to_scene_ego_from_ego_state(ego_pose: Union[EgoState, EgoTemporalState]) -> EgoScene:
    """
    :param ego_pose: temporal state trajectory
    :return serialized scene
    """
    ego_temporal_state = EgoTemporalState(ego_pose) if isinstance(ego_pose, EgoState) else ego_pose
    current_state = ego_temporal_state.ego_current_state
    future = [to_scene_waypoint(state, -current_state.time_point.time_s) for prediction in ego_temporal_state.predictions for state in prediction.valid_waypoints] if ego_temporal_state.predictions else []
    past = [to_scene_waypoint(state, -current_state.time_point.time_s) for state in ego_temporal_state.past_trajectory.valid_waypoints] if ego_temporal_state.past_trajectory else []
    predictions = {'color': Color(red=1, green=0, blue=0, alpha=1, serialize_to=ColorType.FLOAT).to_list(), 'states': past + future}
    rear_axle = current_state.rear_axle
    return EgoScene(acceleration=0.0, pose=rear_axle, speed=current_state.dynamic_car_state.speed, prediction=predictions)

def to_scene_ego_from_car_footprint(car_footprint: CarFootprint) -> EgoScene:
    """
    Convert car footprint to scene structure for ego.
    :param car_footprint: CarFootprint of ego.
    :return Ego in scene format.
    """
    return EgoScene(acceleration=0.0, pose=car_footprint.rear_axle, speed=0.0)

def _to_scene_agent_prediction(tracked_object: TrackedObject, color: Color) -> Dict[str, Any]:
    """
    Extract agent's predicted states from TrackedObject to scene.
    :param tracked_object: tracked_object representation.
    :param color: color [R, G, B, A].
    :return a prediction scene.
    """

    def extract_prediction_state(pose: StateSE2, time_delta: float, speed: float) -> Dict[str, Any]:
        """
        Extract the representation of prediction state for scene.
        :param pose: Track pose.
        :param time_delta: Time difference from initial timestamp.
        :param speed: Speed of track.
        :return: Scene-like dict containing prediction state.
        """
        return {'pose': [pose.x, pose.y, pose.heading], 'polygon': [[pose.x, pose.y]], 'timestamp': time_delta, 'speed': speed}
    past_states = [] if not tracked_object.past_trajectory else [extract_prediction_state(waypoint.oriented_box.center, tracked_object.metadata.timestamp_s - waypoint.time_point.time_s, waypoint.velocity.magnitude() if waypoint.velocity is not None else 0) for waypoint in tracked_object.past_trajectory.waypoints if waypoint]
    future_states = [extract_prediction_state(waypoint.oriented_box.center, waypoint.time_point.time_s - mode.waypoints[0].time_point.time_s, waypoint.velocity.magnitude() if waypoint.velocity is not None else 0) for mode in tracked_object.predictions for waypoint in mode.waypoints if waypoint]
    return {'id': tracked_object.metadata.track_id, 'color': color.to_list(), 'size': [tracked_object.box.width, tracked_object.box.length], 'states': past_states + future_states}

class GeoPandasOccupancyMap(OccupancyMap):
    """OccupancyMap supported by GeoPandas."""

    def __init__(self, dataframe: gp.GeoDataFrame):
        """
        Constructor of GeoPandasOccupancyMap.
        :param dataframe: underlying geopandas dataframe.
        """
        self._dataframe = dataframe

    def get_nearest_entry_to(self, geometry_id: str) -> Tuple[str, Geometry, float]:
        """Inherited, see superclass."""
        assert self.contains(geometry_id), 'This occupancy map does not contain given geometry id'
        polygons = self._dataframe
        polygon = self._dataframe.loc[geometry_id]['geometry']
        polygons.drop(geometry_id, axis=0, inplace=True)
        distances = polygons.distance(polygon).sort_values()
        polygon_index = distances.index[0]
        return (polygon_index, self._dataframe.loc[polygon_index]['geometry'], distances[0])

    def intersects(self, geometry: Geometry) -> OccupancyMap:
        """Inherited, see superclass."""
        candidate_df = {'geometry': [geometry]}
        return GeoPandasOccupancyMap(gp.sjoin(self._dataframe, gp.GeoDataFrame(candidate_df), how='inner', predicate='intersects'))

    def insert(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        candidate_df = {'geometry': [geometry]}
        self._dataframe = pandas.concat([self._dataframe, gp.GeoDataFrame(candidate_df, index=[geometry_id])])

    def get(self, geometry_id: str) -> Geometry:
        """Inherited, see superclass."""
        return self._dataframe.loc[geometry_id]['geometry']

    def set(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        self._dataframe.loc[geometry_id] = geometry

    def get_all_ids(self) -> List[str]:
        """Inherited, see superclass."""
        return list(self._dataframe.index)

    def get_all_geometries(self) -> List[Geometry]:
        """Inherited, see superclass."""
        return list(self._dataframe.geometry)

    @property
    def size(self) -> int:
        """Inherited, see superclass."""
        index = self._dataframe.index
        return len(index)

    def is_empty(self) -> bool:
        """Inherited, see superclass."""
        return self._dataframe.empty

    def contains(self, geometry_id: str) -> bool:
        """Inherited, see superclass."""
        return geometry_id in self._dataframe.index

    def remove(self, geometry_id: List[str]) -> None:
        """Inherited, see superclass."""
        self._dataframe.drop(geometry_id)

def get_nearest_entry_to(self, geometry_id: str) -> Tuple[str, Geometry, float]:
    """Inherited, see superclass."""
    assert self.contains(geometry_id), 'This occupancy map does not contain given geometry id'
    polygons = self._dataframe
    polygon = self._dataframe.loc[geometry_id]['geometry']
    polygons.drop(geometry_id, axis=0, inplace=True)
    distances = polygons.distance(polygon).sort_values()
    polygon_index = distances.index[0]
    return (polygon_index, self._dataframe.loc[polygon_index]['geometry'], distances[0])

def remove(self, geometry_id: List[str]) -> None:
    """Inherited, see superclass."""
    self._dataframe.drop(geometry_id)

class STRTreeOccupancyMap(OccupancyMap):
    """
    OccupancyMap using an SR-tree to support efficient get-nearest queries.
    """

    def __init__(self, geom_map: GeometryMap):
        """
        Constructor of STRTreeOccupancyMap.
        :param geom_map: underlying geometries for occupancy map.
        """
        self._geom_map: GeometryMap = geom_map

    def get_nearest_entry_to(self, geometry_id: str) -> Tuple[str, Geometry, float]:
        """Inherited, see superclass."""
        assert self.contains(geometry_id), 'This occupancy map does not contain given geometry id'
        strtree, index_by_id = self._build_strtree(geometry_id)
        nearest_index = strtree.nearest(self.get(geometry_id))
        nearest = strtree.geometries.take(nearest_index)
        p1, p2 = nearest_points(self.get(geometry_id), nearest)
        return (index_by_id[id(nearest)], nearest, p1.distance(p2))

    def intersects(self, geometry: Geometry) -> OccupancyMap:
        """Inherited, see superclass."""
        strtree, index_by_id = self._build_strtree()
        indices = strtree.query(geometry)
        return STRTreeOccupancyMap({index_by_id[id(geom)]: geom for geom in strtree.geometries.take(indices) if geom.intersects(geometry)})

    def insert(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        self._geom_map[geometry_id] = geometry

    def get(self, geometry_id: str) -> Geometry:
        """Inherited, see superclass."""
        return self._geom_map[geometry_id]

    def set(self, geometry_id: str, geometry: Geometry) -> None:
        """Inherited, see superclass."""
        self._geom_map[geometry_id] = geometry

    def get_all_ids(self) -> List[str]:
        """Inherited, see superclass."""
        return list(self._geom_map.keys())

    def get_all_geometries(self) -> List[Geometry]:
        """Inherited, see superclass."""
        return list(self._geom_map.values())

    @property
    def size(self) -> int:
        """Inherited, see superclass."""
        return len(self._geom_map)

    def is_empty(self) -> bool:
        """Inherited, see superclass."""
        return not self._geom_map

    def contains(self, geometry_id: str) -> bool:
        """Inherited, see superclass."""
        return geometry_id in self._geom_map

    def remove(self, geometry_ids: List[str]) -> None:
        """Remove geometries from the occupancy map by ids."""
        for id in geometry_ids:
            assert id in self._geom_map, 'Geometry does not exist in occupancy map'
            self._geom_map.pop(id)

    def _get_other_geometries(self, ignore_id: str) -> GeometryMap:
        """
        Returns all geometries as except for one specified by ignore_id

        :param ignore_id: the key corresponding to the geometry to be skipped
        :return: GeometryMap
        """
        return {geom_id: geom for geom_id, geom in self._geom_map.items() if geom_id not in ignore_id}

    def _build_strtree(self, ignore_id: Optional[str]=None) -> Tuple[STRtree, Dict[int, str]]:
        """
        Constructs an STRTree from the geometries stored in the geometry map. Additionally, returns a index-id
        mapping to the original keys of the geometries. Has the option to build a tree omitting on geometry
        :param ignore_id: the key corresponding to the geometry to be skipped
        :return: STRTree containing the values of _geom_map, index mapping to the original keys
        """
        if ignore_id is not None:
            temp_geom_map = self._get_other_geometries(ignore_id)
        else:
            temp_geom_map = self._geom_map
        strtree = STRtree(list(temp_geom_map.values()))
        index_by_id = {id(geom): geom_id for geom_id, geom in temp_geom_map.items()}
        return (strtree, index_by_id)

def get_nearest_entry_to(self, geometry_id: str) -> Tuple[str, Geometry, float]:
    """Inherited, see superclass."""
    assert self.contains(geometry_id), 'This occupancy map does not contain given geometry id'
    strtree, index_by_id = self._build_strtree(geometry_id)
    nearest_index = strtree.nearest(self.get(geometry_id))
    nearest = strtree.geometries.take(nearest_index)
    p1, p2 = nearest_points(self.get(geometry_id), nearest)
    return (index_by_id[id(nearest)], nearest, p1.distance(p2))

def intersects(self, geometry: Geometry) -> OccupancyMap:
    """Inherited, see superclass."""
    strtree, index_by_id = self._build_strtree()
    indices = strtree.query(geometry)
    return STRTreeOccupancyMap({index_by_id[id(geom)]: geom for geom in strtree.geometries.take(indices) if geom.intersects(geometry)})

class STRTreeOccupancyMapFactory:
    """
    Factory for STRTreeOccupancyMap.
    """

    @staticmethod
    def get_from_boxes(scene_objects: List[SceneObject]) -> OccupancyMap:
        """
        Builds an STRTreeOccupancyMap from a list of SceneObject. The underlying dictionary will have the format
          key    : value
        return {geom_id: geom for geom_id, geom in self._geom_map.items() if ge
          token1 : [Polygon, LineString]
          token2 : [Polygon, LineString]
        The polygon is derived from the corners of each SceneObject
        :param scene_objects: list of SceneObject to be converted
        :return: STRTreeOccupancyMap
        """
        return STRTreeOccupancyMap({scene_object.track_token: scene_object.box.geometry for scene_object in scene_objects if scene_object.track_token is not None})

    @staticmethod
    def get_from_geometry(geometries: List[Geometry], geometry_ids: Optional[List[str]]=None) -> OccupancyMap:
        """
        Builds an STRTreeOccupancyMap from a list of Geometry. The underlying dictionary will have the format
          key    : value
          token1 : [Polygon, LineString]
          token2 : [Polygon, LineString]]
        :param geometries: list of [Polygon, LineString]
        :param geometry_ids: list of corresponding ids
        :return: STRTreeOccupancyMap
        """
        if geometry_ids is None:
            return STRTreeOccupancyMap({str(geom_id): geom for geom_id, geom in enumerate(geometries)})
        return STRTreeOccupancyMap({str(geom_id): geom for geom_id, geom in zip(geometry_ids, geometries)})

@staticmethod
def get_from_boxes(scene_objects: List[SceneObject]) -> OccupancyMap:
    """
        Builds an STRTreeOccupancyMap from a list of SceneObject. The underlying dictionary will have the format
          key    : value
        return {geom_id: geom for geom_id, geom in self._geom_map.items() if ge
          token1 : [Polygon, LineString]
          token2 : [Polygon, LineString]
        The polygon is derived from the corners of each SceneObject
        :param scene_objects: list of SceneObject to be converted
        :return: STRTreeOccupancyMap
        """
    return STRTreeOccupancyMap({scene_object.track_token: scene_object.box.geometry for scene_object in scene_objects if scene_object.track_token is not None})

@staticmethod
def get_from_geometry(geometries: List[Geometry], geometry_ids: Optional[List[str]]=None) -> OccupancyMap:
    """
        Builds an STRTreeOccupancyMap from a list of Geometry. The underlying dictionary will have the format
          key    : value
          token1 : [Polygon, LineString]
          token2 : [Polygon, LineString]]
        :param geometries: list of [Polygon, LineString]
        :param geometry_ids: list of corresponding ids
        :return: STRTreeOccupancyMap
        """
    if geometry_ids is None:
        return STRTreeOccupancyMap({str(geom_id): geom for geom_id, geom in enumerate(geometries)})
    return STRTreeOccupancyMap({str(geom_id): geom for geom_id, geom in zip(geometry_ids, geometries)})

class LogFuturePredictor(AbstractPredictor):
    """
    Predictor that wraps grabbing future agent trajectories from scenario and returning as ground truth predicted
    trajectories. Predictions are extracted only for agents in input DetectionsTracks.
    """
    requires_scenario: bool = True

    def __init__(self, scenario: AbstractScenario, future_trajectory_sampling: TrajectorySampling):
        """
        Constructor of LogFuturePredictor.
        :param scenario: The scenario the predictor is running on.
        :param future_trajectory_sampling: Sampling parameters for future agent trajectory extraction.
        """
        self._scenario = scenario
        self._future_trajectory_sampling = future_trajectory_sampling

    def initialize(self, initialization: PredictorInitialization) -> None:
        """Inherited, see superclass."""
        pass

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def compute_predicted_trajectories(self, current_input: PredictorInput) -> DetectionsTracks:
        """Inherited, see superclass."""
        iteration = current_input.iteration
        scenario_tracked_objects = self._scenario.get_tracked_objects_at_iteration(iteration.index, self._future_trajectory_sampling)
        scenario_agent_dict: Dict[str, Agent] = {agent.metadata.token: agent for agent in scenario_tracked_objects.tracked_objects.get_agents() if agent.predictions is not None}
        _, curr_detections = current_input.history.current_state
        for agent in curr_detections.tracked_objects.get_agents():
            agent.predictions = scenario_agent_dict[agent.metadata.token].predictions if agent.metadata.token in scenario_agent_dict else None
        return curr_detections

def compute_predicted_trajectories(self, current_input: PredictorInput) -> DetectionsTracks:
    """Inherited, see superclass."""
    iteration = current_input.iteration
    scenario_tracked_objects = self._scenario.get_tracked_objects_at_iteration(iteration.index, self._future_trajectory_sampling)
    scenario_agent_dict: Dict[str, Agent] = {agent.metadata.token: agent for agent in scenario_tracked_objects.tracked_objects.get_agents() if agent.predictions is not None}
    _, curr_detections = current_input.history.current_state
    for agent in curr_detections.tracked_objects.get_agents():
        agent.predictions = scenario_agent_dict[agent.metadata.token].predictions if agent.metadata.token in scenario_agent_dict else None
    return curr_detections

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

def is_agent_ahead(ego_state: StateSE2, agent_state: StateSE2, angle_tolerance: float=30) -> bool:
    """
    Determines if an agent is ahead of the ego
    :param ego_state: ego's pose
    :param agent_state: agent's pose
    :param angle_tolerance: tolerance to consider if agent is ahead, where zero is the heading of the ego [deg]
    :return: true if agent is ahead, false otherwise.
    """
    return bool(get_agent_relative_angle(ego_state, agent_state) < np.deg2rad(angle_tolerance))

def is_agent_behind(ego_state: StateSE2, agent_state: StateSE2, angle_tolerance: float=150) -> bool:
    """
    Determines if an agent is behind of the ego
    :param ego_state: ego's pose
    :param agent_state: agent's pose
    :param angle_tolerance: tolerance to consider if agent is behind, where zero is the heading of the ego [deg]
    :return: true if agent is behind, false otherwise
    """
    return bool(get_agent_relative_angle(ego_state, agent_state) > np.deg2rad(angle_tolerance))

def get_closest_agent_in_position(ego_state: EgoState, observations: DetectionsTracks, is_in_position: Callable[[StateSE2, StateSE2], bool], collided_track_ids: Set[str]=set(), lateral_distance_threshold: float=0.5) -> Tuple[Optional[Agent], float]:
    """
    Searches for the closest agent in a specified position
    :param ego_state: ego's state
    :param observations: agents as DetectionTracks
    :param is_in_position: a function to determine the positional relationship to the ego
    :param collided_track_ids: Set of collided track tokens, default {}
    :param lateral_distance_threshold: Agents laterally further away than this threshold are not considered, default 0.5 meters
    :return: the closest agent in the position and the corresponding shortest distance.
    """
    closest_distance = np.inf
    closest_agent = None
    for agent in observations.tracked_objects.get_agents():
        if is_in_position(ego_state.rear_axle, agent.center) and agent.track_token not in collided_track_ids and (abs(signed_lateral_distance(ego_state.rear_axle, agent.box.geometry)) < lateral_distance_threshold):
            distance = abs(ego_state.car_footprint.oriented_box.geometry.distance(agent.box.geometry))
            if distance < closest_distance:
                closest_distance = distance
                closest_agent = agent
    return (closest_agent, float(closest_distance))

def rotate_vector(vector: Tuple[float, float, float], theta: float, inverse: bool=False) -> Tuple[float, float, float]:
    """
    Apply a 2D rotation around the z axis.

    :param vector: the vector to be rotated
    :param theta: the amount to rotate by
    :param inverse: direction of rotation
    :return: the transformed vector.
    """
    assert len(vector) == 3, 'vector to be transformed must have length 3'
    rotation_matrix = R.from_rotvec([0, 0, theta])
    if inverse:
        rotation_matrix = rotation_matrix.inv()
    local_vector = rotation_matrix.apply(vector)
    return cast(Tuple[float, float, float], local_vector.tolist())

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

def is_in_range(self, time_point: Union[TimePoint, int]) -> bool:
    """
        Check whether a time point is in range of trajectory.
        :return: True if it is, False otherwise.
        """
    if isinstance(time_point, int):
        time_point = TimePoint(time_point)
    return bool(self.start_time <= time_point <= self.end_time)

@dataclass
class TrajectorySampling:
    """
    Trajectory sampling config. The variables are set as optional, to make sure we can deduce last variable if only
        two are set.
    """
    num_poses: Optional[int] = None
    time_horizon: Optional[float] = None
    interval_length: Optional[float] = None

    def __post_init__(self) -> None:
        """
        Make sure all entries are correctly initialized.
        """
        if self.num_poses and (not isinstance(self.num_poses, int)):
            raise ValueError(f'num_poses was defined but it is not int. Instead {type(self.num_poses)}!')
        if self.time_horizon:
            self.time_horizon = float(self.time_horizon)
        if self.interval_length:
            self.interval_length = float(self.interval_length)
        if self.num_poses and self.time_horizon and (not self.interval_length):
            self.interval_length = self.time_horizon / self.num_poses
        elif self.num_poses and self.interval_length and (not self.time_horizon):
            self.time_horizon = self.num_poses * self.interval_length
        elif self.time_horizon and self.interval_length and (not self.num_poses):
            remainder = math.fmod(self.time_horizon, self.interval_length)
            is_close_to_zero = math.isclose(remainder, 0, abs_tol=PROXIMITY_ABS_TOL)
            is_close_to_interval_length = math.isclose(remainder, self.interval_length, abs_tol=PROXIMITY_ABS_TOL)
            if not is_close_to_zero and (not is_close_to_interval_length):
                raise ValueError(f'The time horizon must be a multiple of interval length! time_horizon = {self.time_horizon}, interval = {self.interval_length} and is {remainder}')
            self.num_poses = int(self.time_horizon / self.interval_length)
        elif self.num_poses and self.time_horizon and self.interval_length:
            if not math.isclose(self.num_poses, self.time_horizon / self.interval_length, abs_tol=PROXIMITY_ABS_TOL):
                raise ValueError(f'Not valid initialization of sampling class!time_horizon = {self.time_horizon}, interval = {self.interval_length}, num_poses = {self.num_poses}')
        else:
            raise ValueError(f'Cant initialize class! num_poses = {self.num_poses}, interval = {self.interval_length}, time_horizon = {self.time_horizon}')

    @property
    def step_time(self) -> float:
        """
        :return: [s] The time difference between two poses.
        """
        if not self.interval_length:
            raise RuntimeError('Invalid interval length!')
        return self.interval_length

    def __hash__(self) -> int:
        """
        :return: hash for the dataclass. It has to be custom because the dataclass is not frozen.
            It is not frozen because we deduce the missing parameters.
        """
        return hash((self.num_poses, self.time_horizon, self.interval_length))

    def __eq__(self, other: object) -> bool:
        """
        Compare two instances of trajectory sampling
        :param other: object, needs to be TrajectorySampling class
        :return: true, if they are equal, false otherwise
        """
        if not isinstance(other, TrajectorySampling):
            return NotImplemented
        return math.isclose(cast(float, other.time_horizon), cast(float, self.time_horizon)) and math.isclose(cast(float, other.interval_length), cast(float, self.interval_length)) and (other.num_poses == self.num_poses)

def __hash__(self) -> int:
    """
        :return: hash for the dataclass. It has to be custom because the dataclass is not frozen.
            It is not frozen because we deduce the missing parameters.
        """
    return hash((self.num_poses, self.time_horizon, self.interval_length))

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

@property
def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """Inherited, see superclass."""
    return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

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

@property
def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """Inherited, see superclass."""
    return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

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

@property
def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """Inherited, see superclass."""
    return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

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

@property
def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """Inherited, see superclass."""
    return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

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

@property
def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """Inherited, see superclass."""
    return cast(List[ParameterToScale], self._random_offset_generator.get_schedulable_attributes())

def read_cache_metadata(cache_path: Path, metadata_filenames: List[str], worker: WorkerPool) -> List[CacheMetadataEntry]:
    """
    Reads csv file path into list of CacheMetadataEntry.
    :param cache_path: Path to s3 cache.
    :param metadata_filenames: Filenames of the metadata csv files.
    :return: List of CacheMetadataEntry.
    """
    parallel_inputs = [ReadMetadataFromS3Input(cache_path=cache_path, metadata_filename=mf) for mf in metadata_filenames]
    result = worker_map(worker, _read_metadata_from_s3, parallel_inputs)
    return cast(List[CacheMetadataEntry], result)

@dataclass(frozen=True)
class TrainingEngine:
    """Lightning training engine dataclass wrapping the lightning trainer, model and datamodule."""
    trainer: pl.Trainer
    model: pl.LightningModule
    datamodule: pl.LightningDataModule

    def __repr__(self) -> str:
        """
        :return: String representation of class without expanding the fields.
        """
        return f'<{type(self).__module__}.{type(self).__qualname__} object at {hex(id(self))}>'

def __repr__(self) -> str:
    """
        :return: String representation of class without expanding the fields.
        """
    return f'<{type(self).__module__}.{type(self).__qualname__} object at {hex(id(self))}>'

class ScenarioTab(BaseTab):
    """Scenario tab in nuboard."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, vehicle_parameters: VehicleParameters, scenario_builder: AbstractScenarioBuilder, async_rendering: bool=True, frame_rate_cap_hz: int=60):
        """
        Scenario tab to render metric results about a scenario.
        :param doc: Bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        :param vehicle_parameters: Vehicle parameters.
        :param scenario_builder: nuPlan scenario builder instance.
        :param async_rendering: When true, will use threads to render SimulationTiles asynchronously.
        :param frame_rate_cap_hz: Maximum frames to render per second. Internally this value is capped at 60.
        """
        super().__init__(doc=doc, experiment_file_data=experiment_file_data)
        self._number_metrics_per_figure: int = 4
        self.planner_checkbox_group.name = 'scenario_planner_checkbox_group'
        self._scenario_builder = scenario_builder
        self._scenario_title_div = Div(**ScenarioTabTitleDivConfig.get_config())
        self._scalar_scenario_type_select = Select(name='scenario_scalar_scenario_type_select', css_classes=['scalar-scenario-type-select'])
        self._scalar_scenario_type_select.on_change('value', self._scalar_scenario_type_select_on_change)
        self._scalar_log_name_select = Select(name='scenario_scalar_log_name_select', css_classes=['scalar-log-name-select'])
        self._scalar_log_name_select.on_change('value', self._scalar_log_name_select_on_change)
        self._scalar_scenario_name_select = Select(name='scenario_scalar_name_select', css_classes=['scalar-scenario-name-select'])
        self._scalar_scenario_name_select.js_on_change('value', ScenarioTabUpdateWindowsSizeJSCode.get_js_code())
        self._scalar_scenario_name_select.on_change('value', self._scalar_scenario_name_select_on_change)
        self._scenario_token_multi_choice = MultiChoice(**ScenarioTabScenarioTokenMultiChoiceConfig.get_config())
        self._scenario_token_multi_choice.on_change('value', self._scenario_token_multi_choice_on_change)
        self._scenario_modal_query_btn = Button(**ScenarioTabModalQueryButtonConfig.get_config())
        self._scenario_modal_query_btn.js_on_click(ScenarioTabLoadingJSCode.get_js_code())
        self._scenario_modal_query_btn.on_click(self._scenario_modal_query_button_on_click)
        self.planner_checkbox_group.js_on_change('active', ScenarioTabLoadingJSCode.get_js_code())
        self._default_time_series_div = Div(text=' <p> No time series results, please add more experiments or\n                adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._time_series_layout = column(self._default_time_series_div, css_classes=['scenario-time-series-layout'], name='time_series_layout')
        self._default_ego_expert_states_div = Div(text=' <p> No expert and ego states, please add more experiments or\n                        adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._ego_expert_states_layout = column(self._default_ego_expert_states_div, css_classes=['scenario-ego-expert-states-layout'], name='ego_expert_states_layout')
        self._default_simulation_div = Div(text=' <p> No simulation data, please add more experiments or\n                adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._simulation_tile_layout = column(self._default_simulation_div, css_classes=['scenario-simulation-layout'], name='simulation_tile_layout')
        self._simulation_tile_layout.js_on_change('children', ScenarioTabLoadingEndJSCode.get_js_code())
        self.simulation_tile = SimulationTile(map_factory=self._scenario_builder.get_map_factory(), doc=self._doc, vehicle_parameters=vehicle_parameters, experiment_file_data=experiment_file_data, async_rendering=async_rendering, frame_rate_cap_hz=frame_rate_cap_hz)
        self._default_scenario_score_div = Div(text=' <p> No scenario score results, please add more experiments or\n                        adjust the search filter.</p>', css_classes=['scenario-default-div'], margin=default_div_style['margin'], width=default_div_style['width'])
        self._scenario_score_layout = column(self._default_scenario_score_div, css_classes=['scenario-score-layout'], name='scenario_score_layout')
        self._scenario_metric_score_data_figure_sizes = scenario_tab_style['scenario_metric_score_figure_sizes']
        self._scenario_metric_score_data: scenario_metric_score_dict_type = {}
        self._time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = {}
        self._simulation_figure_data: List[SimulationData] = []
        self._available_scenario_names: List[str] = []
        self._simulation_plots: Optional[column] = None
        object_types = ['Ego', 'Vehicle', 'Pedestrian', 'Bicycle', 'Generic', 'Traffic Cone', 'Barrier', 'Czone Sign']
        self._object_checkbox_group = CheckboxGroup(labels=object_types, active=list(range(len(object_types))), css_classes=['scenario-object-checkbox-group'], name='scenario_object_checkbox_group')
        self._object_checkbox_group.on_change('active', self._object_checkbox_group_active_on_change)
        trajectories = ['Expert Trajectory', 'Ego Trajectory', 'Goal', 'Traffic Light', 'RoadBlock']
        self._traj_checkbox_group = CheckboxGroup(labels=trajectories, active=list(range(len(trajectories))), css_classes=['scenario-traj-checkbox-group'], name='scenario_traj_checkbox_group')
        self._traj_checkbox_group.on_change('active', self._traj_checkbox_group_active_on_change)
        map_objects = ['Lane', 'Intersection', 'Stop Line', 'Crosswalk', 'Walkway', 'Carpark', 'Lane Connector', 'Lane Line']
        self._map_checkbox_group = CheckboxGroup(labels=map_objects, active=list(range(len(map_objects))), css_classes=['scenario-map-checkbox-group'], name='scenario_map_checkbox_group')
        self._map_checkbox_group.on_change('active', self._map_checkbox_group_active_on_change)
        self.plot_state_keys = ['x [m]', 'y [m]', 'heading [rad]', 'velocity_x [m/s]', 'velocity_y [m/s]', 'speed [m/s]', 'acceleration_x [m/s^2]', 'acceleration_y [m/s^2]', 'acceleration [m/s^2]', 'steering_angle [rad]', 'yaw_rate [rad/s]']
        self.expert_planner_key = 'Expert'
        self._init_selection()

    @property
    def scenario_title_div(self) -> Div:
        """Return scenario title div."""
        return self._scenario_title_div

    @property
    def scalar_scenario_type_select(self) -> Select:
        """Return scalar_scenario_type_select."""
        return self._scalar_scenario_type_select

    @property
    def scalar_log_name_select(self) -> Select:
        """Return scalar_log_name_select."""
        return self._scalar_log_name_select

    @property
    def scalar_scenario_name_select(self) -> Select:
        """Return scalar_scenario_name_select."""
        return self._scalar_scenario_name_select

    @property
    def scenario_token_multi_choice(self) -> MultiChoice:
        """Return scenario_token multi choice."""
        return self._scenario_token_multi_choice

    @property
    def scenario_modal_query_btn(self) -> Button:
        """Return scenario_modal_query_button."""
        return self._scenario_modal_query_btn

    @property
    def object_checkbox_group(self) -> CheckboxGroup:
        """Return object checkbox group."""
        return self._object_checkbox_group

    @property
    def traj_checkbox_group(self) -> CheckboxGroup:
        """Return traj checkbox group."""
        return self._traj_checkbox_group

    @property
    def map_checkbox_group(self) -> CheckboxGroup:
        """Return map checkbox group."""
        return self._map_checkbox_group

    @property
    def time_series_layout(self) -> column:
        """Return time_series_layout."""
        return self._time_series_layout

    @property
    def scenario_score_layout(self) -> column:
        """Return scenario_score_layout."""
        return self._scenario_score_layout

    @property
    def simulation_tile_layout(self) -> column:
        """Return simulation_tile_layout."""
        return self._simulation_tile_layout

    @property
    def ego_expert_states_layout(self) -> column:
        """Return time_series_state_layout."""
        return self._ego_expert_states_layout

    def _update_glyph_checkbox_group(self, glyph_names: List[str]) -> None:
        """
        Update visibility of glyphs according to checkbox group.
        :param glyph_names: A list of updated glyph names.
        """
        for simulation_figure in self.simulation_tile.figures:
            simulation_figure.update_glyphs_visibility(glyph_names=glyph_names)

    def _traj_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for traj checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._traj_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def _map_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for map checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._map_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def _object_checkbox_group_active_on_change(self, attr: str, old: List[int], new: List[int]) -> None:
        """
        Helper function for object checkbox group when the list of actives changes.
        :param attr: Attribute name.
        :param old: Old active index.
        :param new: New active index.
        """
        active_indices = list(set(old) - set(new)) + list(set(new) - set(old))
        active_labels = [self._object_checkbox_group.labels[index] for index in active_indices]
        self._update_glyph_checkbox_group(glyph_names=active_labels)

    def file_paths_on_change(self, experiment_file_data: ExperimentFileData, experiment_file_active_index: List[int]) -> None:
        """
        Interface to update layout when file_paths is changed.
        :param experiment_file_data: Experiment file data.
        :param experiment_file_active_index: Active indexes for experiment files.
        """
        self._experiment_file_data = experiment_file_data
        self._experiment_file_active_index = experiment_file_active_index
        self.simulation_tile.init_simulations(figure_sizes=self.simulation_figure_sizes)
        self._init_selection()
        self._scenario_metric_score_data = self._update_aggregation_metric()
        self._update_scenario_plot()

    def _click_planner_checkbox_group(self, attr: Any) -> None:
        """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
        scenario_metric_score_figure_data = self._render_scenario_metric_score()
        scenario_metric_score_layout = self._render_scenario_metric_layout(figure_data=scenario_metric_score_figure_data, default_div=self._default_scenario_score_div, plot_width=self._scenario_metric_score_data_figure_sizes[0], legend=False)
        self._scenario_score_layout.children[0] = layout(scenario_metric_score_layout)
        filtered_time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = defaultdict(list)
        for key, time_series_data in self._time_series_data.items():
            for data in time_series_data:
                if data.planner_name not in self.enable_planner_names:
                    continue
                filtered_time_series_data[key].append(data)
        time_series_figure_data = self._render_time_series(aggregated_time_series_data=filtered_time_series_data)
        time_series_figures = self._render_scenario_metric_layout(figure_data=time_series_figure_data, default_div=self._default_time_series_div, plot_width=self.plot_sizes[0], legend=True)
        self._time_series_layout.children[0] = layout(time_series_figures)
        filtered_simulation_figures = [data for data in self._simulation_figure_data if data.planner_name in self.enable_planner_names]
        if not filtered_simulation_figures:
            simulation_layouts = column(self._default_simulation_div)
            ego_expert_state_layouts = column(self._default_ego_expert_states_div)
        else:
            simulation_layouts = gridplot([simulation_figure.plot for simulation_figure in filtered_simulation_figures], ncols=self.get_plot_cols(plot_width=self.simulation_figure_sizes[0], offset_width=scenario_tab_style['col_offset_width']), toolbar_location=None)
            ego_expert_state_layouts = self._render_ego_expert_states(simulation_figure_data=filtered_simulation_figures)
        self._simulation_tile_layout.children[0] = layout(simulation_layouts)
        self._ego_expert_states_layout.children[0] = layout(ego_expert_state_layouts)

    def _update_simulation_layouts(self) -> None:
        """Update simulation layouts."""
        self._simulation_tile_layout.children[0] = layout(self._simulation_plots)

    def _update_scenario_plot(self) -> None:
        """Update scenario plots when selection is made."""
        start_time = time.perf_counter()
        self._simulation_figure_data = []
        scenario_metric_score_figure_data = self._render_scenario_metric_score()
        scenario_metric_score_layout = self._render_scenario_metric_layout(figure_data=scenario_metric_score_figure_data, default_div=self._default_scenario_score_div, plot_width=self._scenario_metric_score_data_figure_sizes[0], legend=False)
        self._scenario_score_layout.children[0] = layout(scenario_metric_score_layout)
        self._time_series_data = self._aggregate_time_series_data()
        time_series_figure_data = self._render_time_series(aggregated_time_series_data=self._time_series_data)
        time_series_figures = self._render_scenario_metric_layout(figure_data=time_series_figure_data, default_div=self._default_time_series_div, plot_width=self.plot_sizes[0], legend=True)
        self._time_series_layout.children[0] = layout(time_series_figures)
        self._simulation_plots = self._render_simulations()
        ego_expert_state_layout = self._render_ego_expert_states(simulation_figure_data=self._simulation_figure_data)
        self._ego_expert_states_layout.children[0] = layout(ego_expert_state_layout)
        self._doc.add_next_tick_callback(self._update_simulation_layouts)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        logger.info(f'Rending scenario plot takes {elapsed_time:.4f} seconds.')

    def _update_planner_names(self) -> None:
        """Update planner name options in the checkbox widget."""
        self.planner_checkbox_group.labels = []
        self.planner_checkbox_group.active = []
        selected_keys = [key for key in self.experiment_file_data.simulation_scenario_keys if key.scenario_type == self._scalar_scenario_type_select.value and key.scenario_name == self._scalar_scenario_name_select.value]
        sorted_planner_names = sorted(list({key.planner_name for key in selected_keys}))
        self.planner_checkbox_group.labels = sorted_planner_names
        self.planner_checkbox_group.active = [index for index in range(len(sorted_planner_names))]

    def _scalar_scenario_type_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar scenario type.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if new == '':
            return
        available_log_names = self.load_log_name(scenario_type=self._scalar_scenario_type_select.value)
        self._scalar_log_name_select.options = [''] + available_log_names
        self._scalar_log_name_select.value = ''
        self._scalar_scenario_name_select.options = ['']
        self._scalar_scenario_name_select.value = ''

    def _scalar_log_name_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar log name.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if new == '':
            return
        available_scenario_names = self.load_scenario_names(scenario_type=self._scalar_scenario_type_select.value, log_name=self._scalar_log_name_select.value)
        self._scalar_scenario_name_select.options = [''] + available_scenario_names
        self._scalar_scenario_name_select.value = ''

    def _scalar_scenario_name_select_on_change(self, attr: str, old: str, new: str) -> None:
        """
        Helper function to change event in scalar scenario name.
        :param attr: Attribute.
        :param old: Old value.
        :param new: New value.
        """
        if self._scalar_scenario_name_select.tags:
            self.window_width = self._scalar_scenario_name_select.tags[0]
            self.window_height = self._scalar_scenario_name_select.tags[1]

    def _scenario_token_multi_choice_on_change(self, attr: str, old: List[str], new: List[str]) -> None:
        """
        Helper function to change event in scenario token multi choice.
        :param attr: Attribute.
        :param old: List of old values.
        :param new: List of new values.
        """
        available_scenario_tokens = self._experiment_file_data.available_scenario_tokens
        if not available_scenario_tokens or not new:
            return
        scenario_token_info = available_scenario_tokens.get(new[0])
        if self._scalar_scenario_type_select.value != scenario_token_info.scenario_type:
            self._scalar_scenario_type_select.value = scenario_token_info.scenario_type
        if self._scalar_log_name_select.value != scenario_token_info.log_name:
            self._scalar_log_name_select.value = scenario_token_info.log_name
        if self._scalar_scenario_name_select.value != scenario_token_info.scenario_name:
            self.scalar_scenario_name_select.value = scenario_token_info.scenario_name

    def _scenario_modal_query_button_on_click(self) -> None:
        """Helper function when click the modal query button."""
        if self._scalar_scenario_name_select.tags:
            self.window_width = self._scalar_scenario_name_select.tags[0]
            self.window_height = self._scalar_scenario_name_select.tags[1]
        self._update_planner_names()
        self._update_scenario_plot()

    def _init_selection(self) -> None:
        """Init histogram and scalar selection options."""
        self._scalar_scenario_type_select.value = ''
        self._scalar_scenario_type_select.options = []
        self._scalar_log_name_select.value = ''
        self._scalar_log_name_select.options = []
        self._scalar_scenario_name_select.value = ''
        self._scalar_scenario_name_select.options = []
        self._available_scenario_names = []
        self._simulation_figure_data = []
        if len(self._scalar_scenario_type_select.options) == 0:
            self._scalar_scenario_type_select.options = [''] + self.experiment_file_data.available_scenario_types
        if len(self._scalar_scenario_type_select.options) > 0:
            self._scalar_scenario_type_select.value = self._scalar_scenario_type_select.options[0]
        available_scenario_tokens = list(self._experiment_file_data.available_scenario_tokens.keys())
        self._scenario_token_multi_choice.options = available_scenario_tokens
        self._update_planner_names()

    @staticmethod
    def _render_scalar_figure(title: str, y_axis_label: str, hover: HoverTool, sizes: List[int], x_axis_label: Optional[str]=None, x_range: Optional[List[str]]=None, y_range: Optional[List[str]]=None) -> Figure:
        """
        Render a scalar figure.
        :param title: Plot title.
        :param y_axis_label: Y axis label.
        :param hover: Hover tool for the plot.
        :param sizes: Width and height in pixels.
        :param x_axis_label: Label in x axis.
        :param x_range: Labels in x major axis.
        :param y_range: Labels in y major axis.
        :return A time series plot.
        """
        scenario_scalar_figure = Figure(background_fill_color=PLOT_PALETTE['background_white'], title=title, css_classes=['time-series-figure'], margin=scenario_tab_style['time_series_figure_margins'], width=sizes[0], height=sizes[1], active_scroll='wheel_zoom', output_backend='webgl', x_range=x_range, y_range=y_range)
        scenario_scalar_figure.add_tools(hover)
        scenario_scalar_figure.title.text_font_size = scenario_tab_style['time_series_figure_title_text_font_size']
        scenario_scalar_figure.xaxis.axis_label_text_font_size = scenario_tab_style['time_series_figure_xaxis_axis_label_text_font_size']
        scenario_scalar_figure.xaxis.major_label_text_font_size = scenario_tab_style['time_series_figure_xaxis_major_label_text_font_size']
        scenario_scalar_figure.yaxis.axis_label_text_font_size = scenario_tab_style['time_series_figure_yaxis_axis_label_text_font_size']
        scenario_scalar_figure.yaxis.major_label_text_font_size = scenario_tab_style['time_series_figure_yaxis_major_label_text_font_size']
        scenario_scalar_figure.toolbar.logo = None
        scenario_scalar_figure.xaxis.major_label_orientation = np.pi / 4
        scenario_scalar_figure.yaxis.axis_label = y_axis_label
        scenario_scalar_figure.xaxis.axis_label = x_axis_label
        return scenario_scalar_figure

    def _update_aggregation_metric(self) -> scenario_metric_score_dict_type:
        """
        Update metric score for each scenario.
        :return A dict of log name: {scenario names and their metric scores}.
        """
        data: scenario_metric_score_dict_type = defaultdict(lambda: defaultdict(list))
        for index, metric_aggregator_dataframes in enumerate(self.experiment_file_data.metric_aggregator_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for file_index, (metric_aggregator_filename, metric_aggregator_dataframe) in enumerate(metric_aggregator_dataframes.items()):
                columns = set(list(metric_aggregator_dataframe.columns))
                non_metric_columns = {'scenario', 'log_name', 'scenario_type', 'num_scenarios', 'planner_name', 'aggregator_type'}
                metric_columns = sorted(list(columns - non_metric_columns))
                for _, row_data in metric_aggregator_dataframe.iterrows():
                    num_scenarios = row_data['num_scenarios']
                    if not np.isnan(num_scenarios):
                        continue
                    planner_name = row_data['planner_name']
                    scenario_name = row_data['scenario']
                    log_name = row_data['log_name']
                    for metric_column in metric_columns:
                        score = row_data[metric_column]
                        if score is not None:
                            data[log_name][scenario_name].append(ScenarioMetricScoreData(experiment_index=index, metric_aggregator_file_name=metric_aggregator_filename, metric_aggregator_file_index=file_index, planner_name=planner_name, metric_statistic_name=metric_column, score=np.round(score, 4)))
        return data

    def _aggregate_time_series_data(self) -> Dict[str, List[ScenarioTimeSeriesData]]:
        """
        Aggregate time series data.
        :return A dict of metric statistic names and their data.
        """
        aggregated_time_series_data: Dict[str, List[ScenarioTimeSeriesData]] = {}
        scenario_types = tuple([self._scalar_scenario_type_select.value]) if self._scalar_scenario_type_select.value else None
        log_names = tuple([self._scalar_log_name_select.value]) if self._scalar_log_name_select.value else None
        if not len(self._scalar_scenario_name_select.value):
            return aggregated_time_series_data
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            if index not in self._experiment_file_active_index:
                continue
            for metric_statistics_dataframe in metric_statistics_dataframes:
                planner_names = metric_statistics_dataframe.planner_names
                if metric_statistics_dataframe.metric_statistic_name not in aggregated_time_series_data:
                    aggregated_time_series_data[metric_statistics_dataframe.metric_statistic_name] = []
                for planner_name in planner_names:
                    data_frame = metric_statistics_dataframe.query_scenarios(scenario_names=tuple([str(self._scalar_scenario_name_select.value)]), scenario_types=scenario_types, planner_names=tuple([planner_name]), log_names=log_names)
                    if not len(data_frame):
                        continue
                    time_series_headers = metric_statistics_dataframe.time_series_headers
                    time_series: pandas.DataFrame = data_frame[time_series_headers]
                    if time_series[time_series_headers[0]].iloc[0] is None:
                        continue
                    time_series_values: npt.NDArray[np.float64] = np.round(np.asarray(list(chain.from_iterable(time_series[metric_statistics_dataframe.time_series_values_column]))), 4)
                    time_series_timestamps = list(chain.from_iterable(time_series[metric_statistics_dataframe.time_series_timestamp_column]))
                    time_series_unit = time_series[metric_statistics_dataframe.time_series_unit_column].iloc[0]
                    time_series_selected_frames = metric_statistics_dataframe.get_time_series_selected_frames
                    scenario_time_series_data = ScenarioTimeSeriesData(experiment_index=index, planner_name=planner_name, time_series_values=time_series_values, time_series_timestamps=time_series_timestamps, time_series_unit=time_series_unit, time_series_selected_frames=time_series_selected_frames)
                    aggregated_time_series_data[metric_statistics_dataframe.metric_statistic_name].append(scenario_time_series_data)
        return aggregated_time_series_data

    def _render_time_series(self, aggregated_time_series_data: Dict[str, List[ScenarioTimeSeriesData]]) -> Dict[str, Figure]:
        """
        Render time series plots.
        :param aggregated_time_series_data: Aggregated scenario time series data.
        :return A dict of figure name and figures.
        """
        time_series_figures: Dict[str, Figure] = {}
        for metric_statistic_name, scenario_time_series_data in aggregated_time_series_data.items():
            for data in scenario_time_series_data:
                if not len(data.time_series_values):
                    continue
                if metric_statistic_name not in time_series_figures:
                    time_series_figures[metric_statistic_name] = self._render_scalar_figure(title=metric_statistic_name, y_axis_label=data.time_series_unit, x_axis_label='frame', hover=HoverTool(tooltips=[('Frame', '@x'), ('Value', '@y{0.0000}'), ('Time_us', '@time_us'), ('Planner', '$name')]), sizes=self.plot_sizes)
                planner_name = data.planner_name + f' ({self.get_file_path_last_name(data.experiment_index)})'
                color = self.experiment_file_data.file_path_colors[data.experiment_index][data.planner_name]
                time_series_figure = time_series_figures[metric_statistic_name]
                timestamp_frames = data.time_series_selected_frames if data.time_series_selected_frames is not None else list(range(len(data.time_series_timestamps)))
                data_source = ColumnDataSource(dict(x=timestamp_frames, y=data.time_series_values, time_us=data.time_series_timestamps))
                if data.time_series_selected_frames is not None:
                    time_series_figure.scatter(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source)
                else:
                    time_series_figure.line(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source)
        return time_series_figures

    def _render_scenario_metric_score_scatter(self, scatter_figure: Figure, scenario_metric_score_data: Dict[str, List[ScenarioMetricScoreData]]) -> None:
        """
        Render scatter plot with scenario metric score data.
        :param scatter_figure: A scatter figure.
        :param scenario_metric_score_data: Metric score data for a scenario.
        """
        data_sources: Dict[str, ScenarioMetricScoreDataSource] = {}
        for metric_name, metric_score_data in scenario_metric_score_data.items():
            for index, score_data in enumerate(metric_score_data):
                experiment_name = self.get_file_path_last_name(score_data.experiment_index)
                legend_label = f'{score_data.planner_name} ({experiment_name})'
                data_source_index = legend_label + f' - {score_data.metric_aggregator_file_index})'
                if data_source_index not in data_sources:
                    data_sources[data_source_index] = ScenarioMetricScoreDataSource(xs=[], ys=[], planners=[], aggregators=[], experiments=[], fill_colors=[], marker=self.get_scatter_sign(score_data.metric_aggregator_file_index), legend_label=legend_label)
                fill_color = self.experiment_file_data.file_path_colors[score_data.experiment_index][score_data.planner_name]
                data_sources[data_source_index].xs.append(score_data.metric_statistic_name)
                data_sources[data_source_index].ys.append(score_data.score)
                data_sources[data_source_index].planners.append(score_data.planner_name)
                data_sources[data_source_index].aggregators.append(score_data.metric_aggregator_file_name)
                data_sources[data_source_index].experiments.append(self.get_file_path_last_name(score_data.experiment_index))
                data_sources[data_source_index].fill_colors.append(fill_color)
        for legend_label, data_source in data_sources.items():
            sources = ColumnDataSource(dict(xs=data_source.xs, ys=data_source.ys, planners=data_source.planners, experiments=data_source.experiments, aggregators=data_source.aggregators, fill_colors=data_source.fill_colors, line_colors=data_source.fill_colors))
            glyph_renderer = self.get_scatter_render_func(scatter_sign=data_source.marker, scatter_figure=scatter_figure)
            glyph_renderer(x='xs', y='ys', size=10, fill_color='fill_colors', line_color='fill_colors', source=sources)

    def _render_scenario_metric_score(self) -> Dict[str, Figure]:
        """
        Render scenario metric score plot.
        :return A dict of figure names and figures.
        """
        if not self._scalar_log_name_select.value or not self._scalar_scenario_name_select.value or (not self._scenario_metric_score_data):
            return {}
        selected_scenario_metric_score: List[ScenarioMetricScoreData] = self._scenario_metric_score_data[self._scalar_log_name_select.value][self._scalar_scenario_name_select.value]
        data: Dict[str, List[ScenarioMetricScoreData]] = defaultdict(list)
        for scenario_metric_score_data in selected_scenario_metric_score:
            if scenario_metric_score_data.planner_name not in self.enable_planner_names:
                continue
            metric_statistic_name = scenario_metric_score_data.metric_statistic_name
            data[metric_statistic_name].append(scenario_metric_score_data)
        metric_statistic_names = sorted(list(set(data.keys())))
        if 'score' in metric_statistic_names:
            metric_statistic_names.remove('score')
            metric_statistic_names.append('score')
        hover = HoverTool(tooltips=[('Metric', '@xs'), ('Score', '@ys'), ('Planner', '@planners'), ('Experiment', '@experiments'), ('Aggregator', '@aggregators')])
        number_of_figures = ceil(len(metric_statistic_names) / self._number_metrics_per_figure)
        scenario_metric_score_figures: Dict[str, Figure] = defaultdict()
        for index in range(number_of_figures):
            starting_index = index * self._number_metrics_per_figure
            ending_index = starting_index + self._number_metrics_per_figure
            selected_metric_names = metric_statistic_names[starting_index:ending_index]
            scenario_metric_score_figure = self._render_scalar_figure(title='', y_axis_label='score', hover=hover, x_range=selected_metric_names, sizes=self._scenario_metric_score_data_figure_sizes)
            metric_score_data = {metric_name: data[metric_name] for metric_name in selected_metric_names}
            self._render_scenario_metric_score_scatter(scatter_figure=scenario_metric_score_figure, scenario_metric_score_data=metric_score_data)
            scenario_metric_score_figures[str(index)] = scenario_metric_score_figure
        return scenario_metric_score_figures

    def _render_grid_plot(self, figures: Dict[str, Figure], plot_width: int, legend: bool=True) -> LayoutDOM:
        """
        Render a grid plot.
        :param figures: A dict of figure names and figures.
        :param plot_width: Width of each plot.
        :param legend: If figures have legends.
        :return A grid plot.
        """
        figure_plot_list: List[Figure] = []
        for figure_name, figure_plot in figures.items():
            if legend:
                figure_plot.legend.label_text_font_size = scenario_tab_style['plot_legend_label_text_font_size']
                figure_plot.legend.background_fill_alpha = 0.0
                figure_plot.legend.click_policy = 'hide'
            figure_plot_list.append(figure_plot)
        grid_plot = gridplot(figure_plot_list, ncols=self.get_plot_cols(plot_width=plot_width), toolbar_location='left')
        return grid_plot

    def _render_scenario_metric_layout(self, figure_data: Dict[str, Figure], default_div: Div, plot_width: int, legend: bool=True) -> column:
        """
        Render a layout for scenario metric.
        :param figure_data: A dict of figure_data.
        :param default_div: Default message when there is no result.
        :param plot_width: Figure width.
        :param legend: If figures have legends.
        :return A bokeh column layout.
        """
        if not figure_data:
            return column(default_div)
        grid_plot = self._render_grid_plot(figures=figure_data, plot_width=plot_width, legend=legend)
        scenario_metric_layout = column(grid_plot)
        return scenario_metric_layout

    def _render_simulations(self) -> column:
        """
        Render simulation plot.
        :return: A list of Bokeh columns or rows.
        """
        selected_keys = [key for key in self.experiment_file_data.simulation_scenario_keys if key.scenario_type == self._scalar_scenario_type_select.value and key.log_name == self._scalar_log_name_select.value and (key.scenario_name == self._scalar_scenario_name_select.value) and (key.nuboard_file_index in self._experiment_file_active_index)]
        if not selected_keys:
            self._scenario_title_div.text = '-'
            simulation_layouts = column(self._default_simulation_div)
        else:
            hidden_glyph_names = [label for checkbox_group in [self._object_checkbox_group, self._traj_checkbox_group, self._map_checkbox_group] for index, label in enumerate(checkbox_group.labels) if index not in checkbox_group.active]
            self._simulation_figure_data = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=selected_keys, figure_sizes=self.simulation_figure_sizes, hidden_glyph_names=hidden_glyph_names)
            simulation_figures = [data.plot for data in self._simulation_figure_data]
            simulation_layouts = gridplot(simulation_figures, ncols=self.get_plot_cols(plot_width=self.simulation_figure_sizes[0], offset_width=scenario_tab_style['col_offset_width']), toolbar_location=None)
            self._scenario_title_div.text = f'{self._scalar_scenario_type_select.value} - {self._scalar_log_name_select.value} - {self._scalar_scenario_name_select.value}'
        return simulation_layouts

    @staticmethod
    def _get_ego_expert_states(state_key: str, ego_state: EgoState) -> float:
        """
        Get states based on the state key.
        :param state_key: Ego state key.
        :param ego_state: Ego state.
        :return ego state based on the key.
        """
        if state_key == 'x [m]':
            return cast(float, ego_state.car_footprint.center.x)
        elif state_key == 'y [m]':
            return cast(float, ego_state.car_footprint.center.y)
        elif state_key == 'velocity_x [m/s]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.x)
        elif state_key == 'velocity_y [m/s]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.y)
        elif state_key == 'speed [m/s]':
            return cast(float, ego_state.dynamic_car_state.speed)
        elif state_key == 'acceleration_x [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.x)
        elif state_key == 'acceleration_y [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.y)
        elif state_key == 'acceleration [m/s^2]':
            return cast(float, ego_state.dynamic_car_state.acceleration)
        elif state_key == 'heading [rad]':
            return cast(float, ego_state.car_footprint.center.heading)
        elif state_key == 'steering_angle [rad]':
            return cast(float, ego_state.dynamic_car_state.tire_steering_rate)
        elif state_key == 'yaw_rate [rad/s]':
            return cast(float, ego_state.dynamic_car_state.angular_velocity)
        else:
            raise ValueError(f'{state_key} not available!')

    def _render_ego_expert_state_glyph(self, ego_expert_plot_aggregated_states: scenario_ego_expert_state_figure_type, ego_expert_plot_colors: Dict[str, str]) -> column:
        """
        Render line and circle glyphs on ego_expert_state figures and get a grid plot.
        :param ego_expert_plot_aggregated_states: Aggregated ego and expert states over frames.
        :param ego_expert_plot_colors: Colors for different planners.
        :return Column layout for ego and expert states.
        """
        ego_expert_state_figures: Dict[str, Figure] = defaultdict()
        for plot_state_key in self.plot_state_keys:
            hover = HoverTool(tooltips=[('Frame', '@x'), ('Value', '@y{0.0000}'), ('Planner', '$name')])
            ego_expert_state_figure = self._render_scalar_figure(title='', y_axis_label=plot_state_key, x_axis_label='frame', hover=hover, sizes=scenario_tab_style['ego_expert_state_figure_sizes'])
            ego_expert_state_figure.yaxis.formatter = BasicTickFormatter(use_scientific=False)
            ego_expert_state_figures[plot_state_key] = ego_expert_state_figure
        for planner_name, plot_states in ego_expert_plot_aggregated_states.items():
            color = ego_expert_plot_colors.get(planner_name, None)
            if not color:
                color = None
            for plot_state_key, plot_state_values in plot_states.items():
                ego_expert_state_figure = ego_expert_state_figures[plot_state_key]
                data_source = ColumnDataSource(dict(x=list(range(len(plot_state_values))), y=np.round(plot_state_values, 2)))
                if self.expert_planner_key in planner_name:
                    ego_expert_state_figure.circle(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source, size=2)
                else:
                    ego_expert_state_figure.line(x='x', y='y', name=planner_name, color=color, legend_label=planner_name, source=data_source, line_width=1)
        ego_expert_states_layout = self._render_grid_plot(figures=ego_expert_state_figures, plot_width=scenario_tab_style['ego_expert_state_figure_sizes'][0], legend=True)
        return ego_expert_states_layout

    def _get_ego_expert_plot_color(self, planner_name: str, file_path_index: int, figure_planer_name: str) -> str:
        """
        Get color for ego expert plot states based on the planner name.
        :param planner_name: Plot planner name.
        :param file_path_index: File path index for the plot.
        :param figure_planer_name: Figure original planner name.
        """
        return cast(str, self.experiment_file_data.expert_color_palettes[file_path_index] if self.expert_planner_key in planner_name else self.experiment_file_data.file_path_colors[file_path_index][figure_planer_name])

    def _render_ego_expert_states(self, simulation_figure_data: List[SimulationData]) -> column:
        """
        Render expert and ego time series states. Make sure it is called after _render_simulation.
        :param simulation_figure_data: Simulation figure data after rendering simulation.
        :return Column layout for ego and expert states.
        """
        if not simulation_figure_data:
            return column(self._default_ego_expert_states_div)
        ego_expert_plot_aggregated_states: scenario_ego_expert_state_figure_type = defaultdict(lambda: defaultdict(list))
        ego_expert_plot_colors: Dict[str, str] = defaultdict()
        for figure_data in simulation_figure_data:
            experiment_file_index = figure_data.simulation_figure.file_path_index
            experiment_name = self.get_file_path_last_name(experiment_file_index)
            expert_planner_name = f'{self.expert_planner_key} - ({experiment_name})'
            ego_planner_name = f'{figure_data.planner_name} - ({experiment_name})'
            ego_expert_states = {expert_planner_name: figure_data.simulation_figure.scenario.get_expert_ego_trajectory(), ego_planner_name: figure_data.simulation_figure.simulation_history.extract_ego_state}
            for planner_name, planner_states in ego_expert_states.items():
                ego_expert_plot_colors[planner_name] = self._get_ego_expert_plot_color(planner_name=planner_name, figure_planer_name=figure_data.planner_name, file_path_index=figure_data.simulation_figure.file_path_index)
                if planner_name in ego_expert_plot_aggregated_states:
                    continue
                for planner_state in planner_states:
                    for plot_state_key in self.plot_state_keys:
                        state_key_value = self._get_ego_expert_states(state_key=plot_state_key, ego_state=planner_state)
                        ego_expert_plot_aggregated_states[planner_name][plot_state_key].append(state_key_value)
        ego_expert_states_layout = self._render_ego_expert_state_glyph(ego_expert_plot_aggregated_states=ego_expert_plot_aggregated_states, ego_expert_plot_colors=ego_expert_plot_colors)
        return ego_expert_states_layout

@staticmethod
def _get_ego_expert_states(state_key: str, ego_state: EgoState) -> float:
    """
        Get states based on the state key.
        :param state_key: Ego state key.
        :param ego_state: Ego state.
        :return ego state based on the key.
        """
    if state_key == 'x [m]':
        return cast(float, ego_state.car_footprint.center.x)
    elif state_key == 'y [m]':
        return cast(float, ego_state.car_footprint.center.y)
    elif state_key == 'velocity_x [m/s]':
        return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.x)
    elif state_key == 'velocity_y [m/s]':
        return cast(float, ego_state.dynamic_car_state.rear_axle_velocity_2d.y)
    elif state_key == 'speed [m/s]':
        return cast(float, ego_state.dynamic_car_state.speed)
    elif state_key == 'acceleration_x [m/s^2]':
        return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.x)
    elif state_key == 'acceleration_y [m/s^2]':
        return cast(float, ego_state.dynamic_car_state.rear_axle_acceleration_2d.y)
    elif state_key == 'acceleration [m/s^2]':
        return cast(float, ego_state.dynamic_car_state.acceleration)
    elif state_key == 'heading [rad]':
        return cast(float, ego_state.car_footprint.center.heading)
    elif state_key == 'steering_angle [rad]':
        return cast(float, ego_state.dynamic_car_state.tire_steering_rate)
    elif state_key == 'yaw_rate [rad/s]':
        return cast(float, ego_state.dynamic_car_state.angular_velocity)
    else:
        raise ValueError(f'{state_key} not available!')

def _get_ego_expert_plot_color(self, planner_name: str, file_path_index: int, figure_planer_name: str) -> str:
    """
        Get color for ego expert plot states based on the planner name.
        :param planner_name: Plot planner name.
        :param file_path_index: File path index for the plot.
        :param figure_planer_name: Figure original planner name.
        """
    return cast(str, self.experiment_file_data.expert_color_palettes[file_path_index] if self.expert_planner_key in planner_name else self.experiment_file_data.file_path_colors[file_path_index][figure_planer_name])

@dataclass
class MetricStatisticsDataFrame:
    """Metric statistics data frame class."""
    metric_statistic_name: str
    metric_statistics_dataframe: pandas.DataFrame
    time_series_unit_column: ClassVar[str] = 'time_series_unit'
    time_series_timestamp_column: ClassVar[str] = 'time_series_timestamps'
    time_series_values_column: ClassVar[str] = 'time_series_values'
    time_series_selected_frames_column: ClassVar[str] = 'time_series_selected_frames'

    def __eq__(self, other: object) -> bool:
        """Compare equality."""
        if not isinstance(other, MetricStatisticsDataFrame):
            return NotImplemented
        return self.metric_statistic_name == other.metric_statistic_name and self.metric_statistics_dataframe.equals(other.metric_statistics_dataframe)

    def __hash__(self) -> int:
        """Implement hash for caching."""
        return hash(self.metric_statistic_name) + id(self.metric_statistics_dataframe)

    @classmethod
    def load_parquet(cls, parquet_path: Path) -> MetricStatisticsDataFrame:
        """
        Load a parquet file to this class.
        The path can be local or s3.
        :param parquet_path: A path to a parquet file.
        """
        data_frame = pandas.read_parquet(path=safe_path_to_string(parquet_path))
        try:
            if not len(data_frame):
                raise IndexError
            metric_statistics_name = data_frame['metric_statistics_name'][0]
        except (IndexError, Exception):
            metric_statistics_name = parquet_path.stem
        return MetricStatisticsDataFrame(metric_statistic_name=metric_statistics_name, metric_statistics_dataframe=data_frame)

    @lru_cache
    def query_scenarios(self, scenario_names: Optional[Tuple[str]]=None, scenario_types: Optional[Tuple[str]]=None, planner_names: Optional[Tuple[str]]=None, log_names: Optional[Tuple[str]]=None) -> pandas.DataFrame:
        """
        Query scenarios with a list of scenario types and planner names.
        :param scenario_names: A tuple of scenario names.
        :param scenario_types: A tuple of scenario types.
        :param planner_names: A tuple of planner names.
        :param log_names: A tuple of log names.
        :return Pandas dataframe after filtering.
        """
        if not scenario_names and (not scenario_types) and (not planner_names):
            return self.metric_statistics_dataframe
        default_query: npt.NDArray[np.bool_] = np.asarray([True] * len(self.metric_statistics_dataframe.index))
        scenario_name_query = self.metric_statistics_dataframe['scenario_name'].isin(scenario_names) if scenario_names else default_query
        scenario_type_query = self.metric_statistics_dataframe['scenario_type'].isin(scenario_types) if scenario_types else default_query
        planner_name_query = self.metric_statistics_dataframe['planner_name'].isin(planner_names) if planner_names else default_query
        log_name_query = self.metric_statistics_dataframe['log_name'].isin(log_names) if log_names else default_query
        return self.metric_statistics_dataframe[scenario_name_query & scenario_type_query & planner_name_query & log_name_query]

    @cached_property
    def metric_statistics_names(self) -> List[str]:
        """Return metric statistic names."""
        return list(self.metric_statistics_dataframe['metric_statistics_name'].unique())

    @cached_property
    def metric_computator(self) -> str:
        """Return metric computator."""
        if len(self.metric_statistics_dataframe):
            return self.metric_statistics_dataframe['metric_computator'][0]
        else:
            raise IndexError('No available records found!')

    @cached_property
    def metric_category(self) -> str:
        """Return metric category."""
        if len(self.metric_statistics_dataframe):
            return self.metric_statistics_dataframe['metric_category'][0]
        else:
            raise IndexError('No available records found!')

    @cached_property
    def metric_score_unit(self) -> str:
        """Return metric score unit."""
        return self.metric_statistics_dataframe['metric_score_unit'][0]

    @cached_property
    def scenario_types(self) -> List[str]:
        """Return a list of scenario types."""
        return list(self.metric_statistics_dataframe['scenario_type'].unique())

    @cached_property
    def scenario_names(self) -> List[str]:
        """Return a list of scenario names."""
        return list(self.metric_statistics_dataframe['scenario_name'])

    @cached_property
    def column_names(self) -> List[str]:
        """Return a list of column names in a table."""
        return list(self.metric_statistics_dataframe.columns)

    @cached_property
    def statistic_names(self) -> List[str]:
        """Return a list of statistic names in a table."""
        return [col.split('_stat_type')[0] for col in self.column_names if '_stat_type' in col]

    @cached_property
    def time_series_headers(self) -> List[str]:
        """Return time series headers."""
        return [self.time_series_unit_column, self.time_series_timestamp_column, self.time_series_values_column]

    @cached_property
    def get_time_series_selected_frames(self) -> Optional[List[int]]:
        """Return selected frames in time series."""
        try:
            return self.metric_statistics_dataframe[self.time_series_selected_frames_column].iloc[0]
        except KeyError:
            return None

    @cached_property
    def time_series_dataframe(self) -> pandas.DataFrame:
        """Return time series dataframe."""
        return self.metric_statistics_dataframe.loc[:, self.time_series_headers]

    @lru_cache
    def statistics_dataframe(self, statistic_names: Optional[Tuple[str]]=None) -> pandas.DataFrame:
        """
        Return statistics columns
        :param statistic_names: A list of statistic names to query
        :return Pandas dataframe after querying.
        """
        if statistic_names:
            return self.metric_statistics_dataframe[statistic_names]
        statistic_headers = []
        for column_name in self.column_names:
            for statistic_name in self.statistic_names:
                if statistic_name in column_name:
                    statistic_headers.append(column_name)
                    continue
        return self.metric_statistics_dataframe[statistic_headers]

    @cached_property
    def planner_names(self) -> List[str]:
        """Return a list of planner names."""
        return list(self.metric_statistics_dataframe['planner_name'].unique())

def __hash__(self) -> int:
    """Implement hash for caching."""
    return hash(self.metric_statistic_name) + id(self.metric_statistics_dataframe)

def get_distance_of_closest_baseline_point_to_its_start(base_line: PolylineMapObject, pose: Point2D) -> float:
    """Computes distance of "closest point on the baseline to pose" to the beginning of the baseline
    :param base_line: A baseline path
    :param pose: An ego pose
    :return: distance to start.
    """
    return float(base_line.linestring.project(Point(*pose)))

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

@staticmethod
def compute_distance_to_map_objects_list(pose: Point2D, map_objects: List[GraphEdgeMapObject]) -> float:
    """
        Compute the min distance to a list of map objects.
        :param pose: pose.
        :param map_objects: list of map objects.
        :return: distance.
        """
    return float(min((obj.polygon.distance(Point(*pose)) for obj in map_objects)))

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

def _get_lr_from_optimizer(optimizer: Optimizer) -> float:
    """
    Gets learning rate from optimizer.
    :param optimizer: Optimizer object.
    :return: Learning rate.
    """
    if len(optimizer.param_groups) == 0:
        raise ValueError('Could not get learning rate.')
    group = optimizer.param_groups[0]
    key = 'initial_lr' if 'initial_lr' in group else 'lr'
    return cast(float, group[key])

def build_lightning_module(cfg: DictConfig, torch_module_wrapper: TorchModuleWrapper) -> pl.LightningModule:
    """
    Builds the lightning module from the config.
    :param cfg: omegaconf dictionary
    :param torch_module_wrapper: NN model used for training
    :return: built object.
    """
    objectives = build_objectives(cfg)
    metrics = build_training_metrics(cfg)
    model = LightningModuleWrapper(model=torch_module_wrapper, objectives=objectives, metrics=metrics, batch_size=cfg.data_loader.params.batch_size, optimizer=cfg.optimizer, lr_scheduler=cfg.lr_scheduler if 'lr_scheduler' in cfg else None, warm_up_lr_scheduler=cfg.warm_up_lr_scheduler if 'warm_up_lr_scheduler' in cfg else None, objective_aggregate_mode=cfg.objective_aggregate_mode)
    return cast(pl.LightningModule, model)

def is_target_type(cfg: DictConfig, target_type: Union[Type[Any], Callable[..., Any]]) -> bool:
    """
    Check whether the config's resolved type matches the target type or callable.
    :param cfg: config
    :param target_type: Type or callable to check against.
    :return: Whether cfg._target_ matches the target_type.
    """
    return bool(_locate(cfg._target_) == target_type)

def find_builder_in_config(cfg: DictConfig, desired_type: Type[Any]) -> DictConfig:
    """
    Find the corresponding config for the desired builder
    :param cfg: config structured as a dictionary
    :param desired_type: desired builder type
    :return: found config
    @raise ValueError if the config cannot be found for the builder
    """
    for cfg_builder in cfg.values():
        if is_target_type(cfg_builder, desired_type):
            return cast(DictConfig, cfg_builder)
    raise ValueError(f'Config does not exist for builder type: {desired_type}!')

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

@classmethod
def get_scenario_type(cls) -> Type[AbstractScenario]:
    """Inherited. See superclass."""
    return cast(Type[AbstractScenario], MockAbstractScenario)

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

@cached_property
def _lidarpc_tokens(self) -> List[str]:
    """
        :return: list of lidarpc tokens in the scenario
        """
    if self._scenario_extraction_info is None:
        return [self._initial_lidar_token]
    lidarpc_tokens = list(extract_sensor_tokens_as_scenario(self._log_file, get_lidarpc_sensor_data(), self._initial_lidar_timestamp, self._scenario_extraction_info))
    return cast(List[str], lidarpc_tokens)

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

@classmethod
def get_scenario_type(cls) -> Type[AbstractScenario]:
    """Inherited. See superclass."""
    return cast(Type[AbstractScenario], NuPlanScenario)

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

def _extract_initial_lidar_timestamp(scenario: NuPlanScenario) -> int:
    return cast(int, scenario._initial_lidar_timestamp)

def filter_invalid_goals(scenario_dict: ScenarioDict, worker: WorkerPool) -> ScenarioDict:
    """
    Filter the scenarios with invalid mission goals in a scenario dictionary.
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type.
    :param worker: Worker pool for concurrent scenario processing.
    :return: Filtered scenario dictionary.
    """

    def _filter_goals(scenarios: List[NuPlanScenario]) -> List[NuPlanScenario]:
        """
        Filter scenarios that contain invalid mission goals.
        :param scenarios: List of scenarios to filter.
        :return: List of filtered scenarios.
        """
        return [scenario for scenario in scenarios if scenario.get_mission_goal()]
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = worker_map(worker, _filter_goals, scenario_dict[scenario_type])
    return scenario_dict

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

def is_running(manager: SubmissionContainer) -> bool:
    """
            Checks if the container is running
            :param manager: The container manager
            :returns: True if the container is in running state
            """
    return bool(manager.client.api.inspect_container(manager.container_name)['State']['Status'] == 'running')

def validate_submission(image: str, validator: BaseSubmissionValidator) -> tuple[bool, Optional[Type[AbstractSubmissionValidator]]]:
    """
    Calls the chain of validators on one image.
    :param image: The query docker image
    :param validator: The chain of validators
    :return: A tuple with two possible values:
        (True, None) If the image is valid
        (False, Failing validator type) if image is deemed invalid by a validator on the chain
    """
    image_is_valid = validator.validate(image)
    return (bool(image_is_valid), validator.failing_validator)

class BaseSubmissionValidator(AbstractSubmissionValidator):
    """Base validator for submission validation."""

    def __init__(self) -> None:
        """Constructor, sets next validator and failing validator to none"""
        self._next_validator: AbstractSubmissionValidator | None = None
        self._failing_validator: type[AbstractSubmissionValidator] | None = None

    def set_next(self, validator: AbstractSubmissionValidator) -> AbstractSubmissionValidator:
        """
        Sets the next validator in the chain
        :param validator: The next validator
        :return: The set validator
        """
        self._next_validator = validator
        return validator

    def validate(self, submission: str) -> bool:
        """
        Validates the given submission.
        :param submission: Query submission
        :return: True, if no validator is present, otherwise the next validator validate method output.
        """
        if self._next_validator:
            return bool(self._next_validator.validate(submission))
        return True

    @property
    def failing_validator(self) -> type[AbstractSubmissionValidator] | None:
        """
        Getter for the failing validator
        :return: the failing validator
        """
        return self._failing_validator

def validate(self, submission: str) -> bool:
    """
        Validates the given submission.
        :param submission: Query submission
        :return: True, if no validator is present, otherwise the next validator validate method output.
        """
    if self._next_validator:
        return bool(self._next_validator.validate(submission))
    return True

