# Cluster 16

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

def get_unique_scenario_tags(self) -> List[str]:
    """Retrieve all unique scenario tags in the database."""
    return sorted({tag[0] for tag in self.session.query(ScenarioTag.type).distinct().all()})

def unique_scenario_tags(db: NuPlanDB) -> List[str]:
    """
    Get list of all the unique ScenarioTag types in the DB.
    :param db: Database to use for printing metadata.
    :return: The list of all the unique scenario tag types.
    """
    return [tag[0] for tag in db.session.query(ScenarioTag.type).distinct().all()]

def lidar_pc_closest_image(lidar_pc: LidarPc, camera_channels: Optional[List[str]]=None) -> List[Image]:
    """
    Find the closest images to LidarPc.
    :param camera_channels: List of image channels to find closest image of.
    :return: List of Images from the provided channels closest to LidarPc.
    """
    if camera_channels is None:
        camera_channels = ['CAM_F0', 'CAM_B0', 'CAM_L0', 'CAM_L1', 'CAM_R0', 'CAM_R1']
    imgs = []
    for channel in camera_channels:
        img = lidar_pc._session.query(Image).join(Camera).filter(Image.camera_token == Camera.token).filter(Camera.channel == channel).filter(Camera.log_token == lidar_pc.lidar.log_token).order_by(func.abs(Image.timestamp - lidar_pc.timestamp)).first()
        imgs.append(img)
    return imgs

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

@property
def lidar_pc(self) -> LidarPc:
    """
        Get the closest LidarPc by timestamp
        :return: LidarPc closest to the Image by time
        """
    lidar_pc = self._session.query(LidarPc).order_by(func.abs(LidarPc.timestamp - self.timestamp)).first()
    return lidar_pc

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

def __repr__(self) -> str:
    """
        Get the string representation.
        :return: The string representation.
        """
    return "{}(NuPlanDB('{}'))".format(self.__class__.__name__, self._db.name)

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

def test_maps_db(self) -> None:
    """Test that maps DB has been loaded."""
    self.db_wrapper.maps_db.load_vector_layer('us-nv-las-vegas-strip', 'lane_connectors')

def union(a: Rectangle, b: Rectangle) -> float:
    """
    Union of two rectangles.
    :param a: Rectangle 1.
    :param b: Rectangle 2.
    :return: Area of union between a and b.
    """
    return (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection(a, b)

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

class TestIOU(unittest.TestCase):
    """Test IOU related functions."""

    def test_intersection(self) -> None:
        """Test intersection of boxes."""
        a = (0.0, 0.0, 100.0, 100.0)
        b = (0.0, 0.0, 100.0, 100.0)
        self.assertEqual(measure.intersection(a, b), 10000.0)
        b = (100.0, 100.0, 100.0, 100.0)
        self.assertEqual(measure.intersection(a, b), 0.0)
        b = (100.0, 100.0, 200.0, 200.0)
        self.assertEqual(measure.intersection(a, b), 0.0)
        b = (50.0, 50.0, 150.0, 150.0)
        self.assertEqual(measure.intersection(a, b), 2500.0)

    def test_union(self) -> None:
        """Test union of boxes."""
        a = (0.0, 0.0, 100.0, 100.0)
        b = (0.0, 0.0, 100.0, 100.0)
        self.assertEqual(measure.union(a, b), 10000.0)
        b = (100.0, 100.0, 100.0, 100.0)
        self.assertEqual(measure.union(a, b), 10000.0)
        b = (100.0, 100.0, 200.0, 200.0)
        self.assertEqual(measure.union(a, b), 20000.0)
        b = (50.0, 50.0, 150.0, 150.0)
        self.assertEqual(measure.union(a, b), 17500.0)

def test_intersection(self) -> None:
    """Test intersection of boxes."""
    a = (0.0, 0.0, 100.0, 100.0)
    b = (0.0, 0.0, 100.0, 100.0)
    self.assertEqual(measure.intersection(a, b), 10000.0)
    b = (100.0, 100.0, 100.0, 100.0)
    self.assertEqual(measure.intersection(a, b), 0.0)
    b = (100.0, 100.0, 200.0, 200.0)
    self.assertEqual(measure.intersection(a, b), 0.0)
    b = (50.0, 50.0, 150.0, 150.0)
    self.assertEqual(measure.intersection(a, b), 2500.0)

class Label:
    """A label with the name and color."""

    def __init__(self, name: str, color: Color) -> None:
        """
        :param name: The name of the color.
        :param color: An R, G, B, alpha tuple which defines the color.
        """
        self.name = name
        self.color = color
        for c in self.color:
            assert 0 <= c <= 255

    def __repr__(self) -> str:
        """
        Represents a label using a string.
        :return: A string to represent a label.
        """
        return "Label(name='{}', color={})".format(self.name, self.color)

    def __eq__(self, other: object) -> bool:
        """
        Checks if two labels are equal.
        :param other: Other object.
        :return: True if both objects are the same.
        """
        if not isinstance(other, Label):
            return NotImplemented
        return self.name == other.name and self.color == other.color

    @property
    def normalized_color(self) -> Tuple[float, ...]:
        """
        Normalized color used for pyplot.
        :return: Normalized color.
        """
        return tuple((c / 255.0 for c in self.color))

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the label instance to a JSON-friendly dictionary representation.
        :return: Encoding of the label.
        """
        return {'name': self.name, 'color': self.color}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Label:
        """
        Instantiates a Label instance from serialized dictionary representation.
        :param data: Output from serialize.
        :return: Deserialized label.
        """
        return Label(name=data['name'], color=tuple((int(channel) for channel in data['color'])))

def __repr__(self) -> str:
    """
        Represents a label using a string.
        :return: A string to represent a label.
        """
    return "Label(name='{}', color={})".format(self.name, self.color)

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

class DBSplitterInterface(abc.ABC):
    """
    Interface for DB splitters. A DB splitter is responsible for splitting a DB into machine learning
    splits. Splits names are not fixed by this interface and can vary between implementations, but the splits
    themselves are assumed to be defined as a list of DB tokens.
    """

    def __str__(self) -> str:
        """
        Get the string representation.
        :return: The string representation.
        """
        out = 'Splits:\n{}\n'.format('-' * 28)
        for split_name in self.list():
            out += '{:20s}: {:>6d}\n'.format(split_name, len(self.split(split_name)))
        return out

    @abc.abstractmethod
    def list(self) -> List[str]:
        """
        Return the list of all split names.
        :return: The list of all split names.
        """
        pass

    @abc.abstractmethod
    def split(self, split_name: str) -> List[str]:
        """
        Return record tokens in the split given by split_name.
        :return: The list of record tokens in the given split.
        """
        pass

    @abc.abstractmethod
    def logs(self, split_name: str) -> List[str]:
        """
        Return the list of log names present in split split_name.
        :return: The list of log names in the given split.
        """
        pass

def __str__(self) -> str:
    """
        Get the string representation.
        :return: The string representation.
        """
    out = 'Splits:\n{}\n'.format('-' * 28)
    for split_name in self.list():
        out += '{:20s}: {:>6d}\n'.format(split_name, len(self.split(split_name)))
    return out

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

def __len__(self) -> int:
    """
        Return length of the records for the given queries. For example:
            nuplandb.log.__len()
        :return: Number of records.
        """
    return self._session.query(self._table.token).count()

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

def jsontabledump(f: TextIO, c: Tuple[str, Dict[str, Tuple[str, str]]], name: str) -> None:
    """
    Dump table schema to the given file.
    :param f: File object to dump the table to.
    :param c: Table schema.
    :param name: Table name.
    """
    f.write('{}\n---------\n'.format(name))
    f.write('\n' + c[0] + '\n')
    f.write('```\n')
    f.write('{}{}\n'.format(name, '{'))
    for key in c[1].keys():
        f.write('   {:27}{} -- {}\n'.format('"' + key + '":', c[1][key][0], c[1][key][1]))
    f.write('{}\n```\n'.format('}'))

def get_transform_matrix(layer_dataset) -> npt.NDArray[np.float64]:
    """
    Converts 2D affine.Affine objects to 3D numpy arrays.
    :param layer_dataset: A *context manager* for the layer dataset.
    :return: The transform matrix.
    """
    pixel_to_spatial = layer_dataset.transform
    if pixel_to_spatial[1] != 0 or pixel_to_spatial[3] != 0:
        raise ValueError(f'Rasterio dataset {layer_dataset.name} uses shear or rotation transform. This is supposed to be impossible as GPKG standard only supports north-up. Pixel to spatial transform was {pixel_to_spatial}')
    spatial_to_pixel = ~pixel_to_spatial
    return np.array([[spatial_to_pixel[0], 0, 0, spatial_to_pixel[2]], [0, spatial_to_pixel[4], 0, spatial_to_pixel[5]], [0, 0, 1, 0], [0, 0, 0, 1]])

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

class GPKGMapsDB(IMapsDB):
    """GPKG MapsDB implementation."""

    def __init__(self, map_version: str, map_root: str) -> None:
        """
        Constructor.
        :param map_version: Version of map.
        :param map_root: Root folder of the maps.
        """
        self._map_version = map_version
        self._map_root = map_root
        self._blob_store = BlobStoreCreator.create_mapsdb(map_root=self._map_root)
        version_file = self._blob_store.get(f'{self._map_version}.json')
        self._metadata = json.load(version_file)
        self._map_dimensions = MAP_DIMENSIONS
        self._max_attempts = MAX_ATTEMPTS
        self._seconds_between_attempts = SECONDS_BETWEEN_ATTEMPTS
        self._map_lock_dir = os.path.join(self._map_root, '.maplocks')
        os.makedirs(self._map_lock_dir, exist_ok=True)
        self._load_map_data()

    def __reduce__(self) -> Tuple[Type['GPKGMapsDB'], Tuple[Any, ...]]:
        """
        Hints on how to reconstruct the object when pickling.
        This object is reconstructed by pickle to avoid serializing potentially large state/caches.
        :return: Object type and constructor arguments to be used.
        """
        return (self.__class__, (self._map_version, self._map_root))

    def _load_map_data(self) -> None:
        """Load all available maps once to trigger automatic downloading if the maps are loaded for the first time."""
        for location in MAP_LOCATIONS:
            self.load_vector_layer(location, DUMMY_LOAD_LAYER)

    @property
    def version_names(self) -> List[str]:
        """
        Lists the map version names for all valid map locations, e.g.
        ['9.17.1964', '9.12.1817', '9.15.1915', '9.17.1937']
        """
        return [self._metadata[location]['version'] for location in self.get_locations()]

    def get_map_version(self) -> str:
        """Inherited, see superclass."""
        return self._map_version

    def get_version(self, location: str) -> str:
        """Inherited, see superclass."""
        return str(self._metadata[location]['version'])

    def _get_shape(self, location: str, layer_name: str) -> List[int]:
        """
        Gets the shape of a layer given the map location and layer name.
        :param location: Name of map location, e.g. "sg-one-north". See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
        if layer_name == 'intensity':
            return self._metadata[location]['layers']['Intensity']['shape']
        else:
            return list(self._map_dimensions[location])

    def _get_transform_matrix(self, location: str, layer_name: str) -> npt.NDArray[np.float64]:
        """
        Get transformation matrix of a layer given location and layer name.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
        return np.array(self._metadata[location]['layers'][layer_name]['transform_matrix'])

    @staticmethod
    def is_binary(layer_name: str) -> bool:
        """
        Checks if the layer is binary.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
        return layer_name in ['drivable_area', 'intersection', 'pedestrian_crossing', 'walkway', 'walk_way']

    @staticmethod
    def _can_dilate(layer_name: str) -> bool:
        """
        If the layer can be dilated.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
        return layer_name in ['drivable_area']

    def get_locations(self) -> Sequence[str]:
        """
        Gets the list of available location in this GPKGMapsDB version.
        """
        return self._metadata.keys()

    def layer_names(self, location: str) -> Sequence[str]:
        """Inherited, see superclass."""
        gpkg_layers = self._metadata[location]['layers'].keys()
        return list(filter(lambda x: '_distance_px' not in x, gpkg_layers))

    def load_layer(self, location: str, layer_name: str) -> MapLayer:
        """Inherited, see superclass."""
        if layer_name == 'intensity':
            layer_name = 'Intensity'
        is_bin = self.is_binary(layer_name)
        can_dilate = self._can_dilate(layer_name)
        layer_data = self._get_layer_matrix(location, layer_name)
        transform_matrix = self._get_transform_matrix(location, layer_name)
        precision = 1 / transform_matrix[0, 0]
        layer_meta = MapLayerMeta(name=layer_name, md5_hash='not_used_for_gpkg_mapsdb', can_dilate=can_dilate, is_binary=is_bin, precision=precision)
        distance_matrix = None
        return MapLayer(data=layer_data, metadata=layer_meta, joint_distance=distance_matrix, transform_matrix=transform_matrix)

    def _wait_for_expected_filesize(self, path_on_disk: str, location: str) -> None:
        """
        Waits until the file at `path_on_disk` is exactly `expected_size` bytes.
        :param path_on_disk: Path of the file being downloaded.
        :param location: Location to which the file belongs.
        """
        if isinstance(self._blob_store, LocalStore):
            return
        s3_bucket = self._blob_store._remote._bucket
        s3_key = os.path.join(self._blob_store._remote._prefix, self._get_gpkg_file_path(location))
        client = get_s3_client()
        map_file_size = client.head_object(Bucket=s3_bucket, Key=s3_key).get('ContentLength', 0)
        for _ in range(self._max_attempts):
            if os.path.getsize(path_on_disk) == map_file_size:
                break
            time.sleep(self._seconds_between_attempts)
        if os.path.getsize(path_on_disk) != map_file_size:
            raise GPKGMapsDBException(f'Waited {self._max_attempts * self._seconds_between_attempts} seconds for file {path_on_disk} to reach {map_file_size}, but size is now {os.path.getsize(path_on_disk)}')

    def _safe_save_layer(self, layer_lock_file: str, file_path: str) -> None:
        """
        Safely download the file.
        :param layer_lock_file: Path to lock file.
        :param file_path: Path of the file being downloaded.
        """
        fd = open(layer_lock_file, 'w')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            _ = self._blob_store.save_to_disk(file_path, check_for_compressed=True)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()

    @lru_cache(maxsize=16)
    def load_vector_layer(self, location: str, layer_name: str) -> gpd.geodataframe:
        """Inherited, see superclass."""
        location = location.replace('.gpkg', '')
        rel_path = self._get_gpkg_file_path(location)
        path_on_disk = os.path.join(self._map_root, rel_path)
        if not os.path.exists(path_on_disk):
            layer_lock_file = f'{self._map_lock_dir}/{location}_{layer_name}.lock'
            self._safe_save_layer(layer_lock_file, rel_path)
        self._wait_for_expected_filesize(path_on_disk, location)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            map_meta = gpd.read_file(path_on_disk, layer='meta', engine='pyogrio')
            projection_system = map_meta[map_meta['key'] == 'projectedCoordSystem']['value'].iloc[0]
            gdf_in_pixel_coords = pyogrio.read_dataframe(path_on_disk, layer=layer_name, fid_as_index=True)
            gdf_in_utm_coords = gdf_in_pixel_coords.to_crs(projection_system)
            gdf_in_utm_coords.index = gdf_in_utm_coords.index.map(str)
            gdf_in_utm_coords['fid'] = gdf_in_utm_coords.index
        return gdf_in_utm_coords

    def vector_layer_names(self, location: str) -> Sequence[str]:
        """Inherited, see superclass."""
        location = location.replace('.gpkg', '')
        rel_path = self._get_gpkg_file_path(location)
        path_on_disk = os.path.join(self._map_root, rel_path)
        self._blob_store.save_to_disk(rel_path)
        return pyogrio.list_layers(path_on_disk)

    def purge_cache(self) -> None:
        """Inherited, see superclass."""
        logger.debug('Purging cache...')
        for f in glob.glob(os.path.join(self._map_root, 'gpkg', '*')):
            os.remove(f)
        logger.debug('Done purging cache.')

    def _get_map_dataset(self, location: str) -> rasterio.DatasetReader:
        """
        Returns a *context manager* for the map dataset (includes all the layers).
        Extract the result in a "with ... as ...:" line.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :return: A *context manager* for the map dataset (includes all the layers).
        """
        rel_path = self._get_gpkg_file_path(location)
        path_on_disk = os.path.join(self._map_root, rel_path)
        self._blob_store.save_to_disk(rel_path)
        return rasterio.open(path_on_disk)

    def get_layer_dataset(self, location: str, layer_name: str) -> rasterio.DatasetReader:
        """
        Returns a *context manager* for the layer dataset.
        Extract the result in a "with ... as ...:" line.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        :return: A *context manager* for the layer dataset.
        """
        with self._get_map_dataset(location) as map_dataset:
            layer_dataset_path = next((path for path in map_dataset.subdatasets if path.endswith(':' + layer_name)), None)
            if layer_dataset_path is None:
                raise ValueError(f"Layer '{layer_name}' not found in map '{location}', version '{self.get_version(location)}'")
            return rasterio.open(layer_dataset_path)

    def get_raster_layer_names(self, location: str) -> Sequence[str]:
        """
        Gets the list of available layers for a given map location.
        :param location: The layers name for this map location will be returned.
        :return: List of available raster layers.
        """
        all_layers_dataset = self._get_map_dataset(location)
        fully_qualified_layer_names = all_layers_dataset.subdatasets
        return [name.split(':')[-1] for name in fully_qualified_layer_names]

    def get_gpkg_path_and_store_on_disk(self, location: str) -> str:
        """
        Saves a gpkg map from a location to disk.
        :param location: The layers name for this map location will be returned.
        :return: Path on disk to save a gpkg file.
        """
        rel_path = self._get_gpkg_file_path(location)
        path_on_disk = os.path.join(self._map_root, rel_path)
        self._blob_store.save_to_disk(rel_path)
        return path_on_disk

    def get_metadata_json_path_and_store_on_disk(self, location: str) -> str:
        """
        Saves a metadata.json for a location to disk.
        :param location: The layers name for this map location will be returned.
        :return: Path on disk to save metadata.json.
        """
        rel_path = self._get_metadata_json_path(location)
        path_on_disk = os.path.join(self._map_root, rel_path)
        self._blob_store.save_to_disk(rel_path)
        return path_on_disk

    def _get_gpkg_file_path(self, location: str) -> str:
        """
        Gets path to the gpkg map file.
        :param location: Location for which gpkg needs to be loaded.
        :return: Path to the gpkg file.
        """
        version = self.get_version(location)
        return f'{location}/{version}/map.gpkg'

    def _get_metadata_json_path(self, location: str) -> str:
        """
        Gets path to the metadata json file.
        :param location: Location for which json needs to be loaded.
        :return: Path to the meta json file.
        """
        version = self.get_version(location)
        return f'{location}/{version}/metadata.json'

    def _get_layer_matrix_npy_path(self, location: str, layer_name: str) -> str:
        """
        Gets path to the numpy file for the layer.
        :param location: Location for which layer needs to be loaded.
        :param layer_name: Which layer to load.
        :return: Path to the numpy file.
        """
        version = self.get_version(location)
        return f'{location}/{version}/{layer_name}.npy.npz'

    @staticmethod
    def _get_np_array(path_on_disk: str) -> np.ndarray:
        """
        Gets numpy array from file.
        :param path_on_disk: Path to numpy file.
        :return: Numpy array containing the layer.
        """
        np_data = np.load(path_on_disk)
        return np_data['data']

    def _get_expected_file_size(self, path: str, shape: List[int]) -> int:
        """
        Gets the expected file size.
        :param path: Path to the file.
        :param shape: The shape of the map file.
        :return: The expected file size.
        """
        if path.endswith('_dist.npy'):
            return shape[0] * shape[1] * 4
        return shape[0] * shape[1]

    def _get_layer_matrix(self, location: str, layer_name: str) -> npt.NDArray[np.uint8]:
        """
        Returns the map layer for `location` and `layer_name` as a numpy array.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        :return: Numpy representation of layer.
        """
        rel_path = self._get_layer_matrix_npy_path(location, layer_name)
        path_on_disk = os.path.join(self._map_root, rel_path)
        if not os.path.exists(path_on_disk):
            self._save_layer_matrix(location=location, layer_name=layer_name)
        return self._get_np_array(path_on_disk)

    def _save_layer_matrix(self, location: str, layer_name: str) -> None:
        """
        Extracts the data for `layer_name` from the GPKG file for `location`,
        and saves it on disk so it can be retrieved with `_get_layer_matrix`.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
        is_bin = self.is_binary(layer_name)
        with self.get_layer_dataset(location, layer_name) as layer_dataset:
            layer_data = layer_dataset_ops.load_layer_as_numpy(layer_dataset, is_bin)
        if '_distance_px' in layer_name:
            transform_matrix = self._get_transform_matrix(location, layer_name)
            precision = 1 / transform_matrix[0, 0]
            layer_data = np.negative(layer_data / precision).astype('float32')
        npy_file_path = os.path.join(self._map_root, f'{location}/{self.get_version(location)}/{layer_name}.npy')
        np.savez_compressed(npy_file_path, data=layer_data)

    def _save_all_layers(self, location: str) -> None:
        """
        Saves data on disk for all layers in the GPKG file for `location`.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        """
        rasterio_layers = self.get_raster_layer_names(location)
        for layer_name in rasterio_layers:
            logger.debug('Working on layer: ', layer_name)
            self._save_layer_matrix(location, layer_name)

def _load_map_data(self) -> None:
    """Load all available maps once to trigger automatic downloading if the maps are loaded for the first time."""
    for location in MAP_LOCATIONS:
        self.load_vector_layer(location, DUMMY_LOAD_LAYER)

@property
def version_names(self) -> List[str]:
    """
        Lists the map version names for all valid map locations, e.g.
        ['9.17.1964', '9.12.1817', '9.15.1915', '9.17.1937']
        """
    return [self._metadata[location]['version'] for location in self.get_locations()]

def layer_names(self, location: str) -> Sequence[str]:
    """Inherited, see superclass."""
    gpkg_layers = self._metadata[location]['layers'].keys()
    return list(filter(lambda x: '_distance_px' not in x, gpkg_layers))

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

def test_patch_coord_rotated(self) -> None:
    """
        Checks the function to get patch coordinates with rotation.
        """
    path_center = [0, 0]
    path_dimension = [10, 20]
    polygon_coords = self.nuplan_maps[self.locations[0]].get_patch_coord((path_center[0], path_center[1], path_dimension[0], path_dimension[1]), 90.0)
    expected_polygon_coords = Polygon([[5, 10], [-5, 10], [-5, -10], [5, -10], [5, 10]])
    self.assertEqual(polygon_coords, expected_polygon_coords)

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

def setUp(self) -> None:
    """
        Initialize the map.
        """
    self.maps_db = get_test_maps_db()
    self.location = 'us-nv-las-vegas-strip'
    self.nuplan_map = NuPlanMapWrapper(maps_db=self.maps_db, map_name=self.location)
    self.nuplan_explore = NuPlanMapExplorer(self.nuplan_map)

@dataclass(frozen=True)
class SensorDataSource:
    """
    Class holding parameters for querying db files to extract sensor data.

    For example, for querying lidar data the attributes would be:
    table: lidar_pc
    sensor_table: lidar
    sensor_token_column: lidar_token (this is how the column holding the sensor token is stored in the `table`
    channel: MergedPointCloud
    """
    table: str
    sensor_table: str
    sensor_token_column: str
    channel: str

    def __post_init__(self) -> None:
        """Checks that the tables provided are compatible"""
        if self.table == 'lidar_pc':
            assert self.sensor_table == 'lidar', f'Incompatible sensor_table: {self.sensor_table} for table {self.table}'
        elif self.table == 'image':
            assert self.sensor_table == 'camera', f'Incompatible sensor_table: {self.sensor_table} for table {self.table}'
        else:
            raise ValueError(f'Unknown requested sensor table: {self.table}!')
        assert self.sensor_token_column == f'{self.sensor_table}_token', f'Incompatible sensor_token_column: {self.sensor_token_column} for sensor_table {self.sensor_table}'

def __post_init__(self) -> None:
    """Checks that the tables provided are compatible"""
    if self.table == 'lidar_pc':
        assert self.sensor_table == 'lidar', f'Incompatible sensor_table: {self.sensor_table} for table {self.table}'
    elif self.table == 'image':
        assert self.sensor_table == 'camera', f'Incompatible sensor_table: {self.sensor_table} for table {self.table}'
    else:
        raise ValueError(f'Unknown requested sensor table: {self.table}!')
    assert self.sensor_token_column == f'{self.sensor_table}_token', f'Incompatible sensor_token_column: {self.sensor_token_column} for sensor_table {self.sensor_table}'

@dataclass(frozen=True)
class DBGenerationParameters:
    """
    Encapsulates the parameters used to generate a synthetic NuPlan DB.
    """
    num_lidars: int
    num_cameras: int
    num_sensor_data_per_sensor: int
    num_lidarpc_per_image_ratio: int
    num_scenes: int
    num_traffic_lights_per_lidar_pc: int
    num_agents_per_lidar_pc: int
    num_static_objects_per_lidar_pc: int
    scene_scenario_tag_mapping: Dict[int, List[str]]
    file_path: str

    def __post_init__(self) -> None:
        """
        Sanity checks to ensure that the class contains a valid configuration.
        """
        if self.num_scenes > self.num_sensor_data_per_sensor or self.num_sensor_data_per_sensor % self.num_scenes != 0:
            raise ValueError('Number of scenes must be less than number of point clouds, and must be an equal divisor.')

    def total_object_count(self) -> int:
        """
        Gets the total number of objects per lidar_pc in the configuration.
        :return: The number of objects per lidar_pc in the configuration.
        """
        return self.num_agents_per_lidar_pc + self.num_static_objects_per_lidar_pc

def __post_init__(self) -> None:
    """
        Sanity checks to ensure that the class contains a valid configuration.
        """
    if self.num_scenes > self.num_sensor_data_per_sensor or self.num_sensor_data_per_sensor % self.num_scenes != 0:
        raise ValueError('Number of scenes must be less than number of point clouds, and must be an equal divisor.')

def int_to_str_token(val: Optional[int]) -> Optional[str]:
    """
    Convert an int to a string token used for DB access functions.
    :param val: The val to convert.
    :return: None if the input is None. Else, a string version of the input value to be used with db functions as a token.
    """
    return None if val is None else '{:08d}'.format(val)

def get_test_nuplan_db_nocache() -> NuPlanDB:
    """
    Get a nuPlan DB object with default settings to be used in testing.
    Forces the data to be read from disk.
    """
    load_path = get_test_nuplan_db_path()
    maps_db = get_test_maps_db()
    return NuPlanDB(data_root=NUPLAN_DATA_ROOT, load_path=load_path, maps_db=maps_db)

def _validate_approximate_derivatives_shapes(y: torch.Tensor, x: torch.Tensor) -> None:
    """
    Validates that the shapes for approximate_derivatives_tensor are correct.
    :param y: The Y input.
    :param x: The X input.
    """
    if len(y.shape) == 2 and len(x.shape) == 1 and (y.shape[1] == x.shape[0]):
        return
    raise ValueError(f'Unexpected tensor shapes in approximate_derivatives_tensor: y.shape = {y.shape}, x.shape = {x.shape}')

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

def get_all_map_objects(self, point: Point2D, layer: SemanticMapLayer) -> List[MapObject]:
    """Inherited, see superclass."""
    try:
        return self._get_all_map_objects(point, layer)
    except KeyError:
        raise ValueError(f'Object representation for layer: {layer.name} is unavailable')

def get_map_object(self, object_id: str, layer: SemanticMapLayer) -> Optional[MapObject]:
    """Inherited, see superclass."""
    try:
        if object_id not in self._map_objects[layer]:
            map_object: MapObject = self._map_object_getter[layer](object_id)
            self._map_objects[layer][object_id] = map_object
        return self._map_objects[layer][object_id]
    except KeyError:
        raise ValueError(f'Object representation for layer: {layer.name} object: {object_id} is unavailable')

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

def __repr__(self) -> str:
    """
        :return: String representation.
        """
    return 'TimeDuration({}s)'.format(self.time_s)

def _validate_state_se2_tensor_shape(tensor: torch.Tensor, expected_first_dim: Optional[int]=None) -> None:
    """
    Validates that a tensor is of the proper shape for a tensorized StateSE2.
    :param tensor: The tensor to validate.
    :param expected_first_dim: The expected first dimension. Can be one of three values:
        * 1: Tensor is expected to be of shape (3,)
        * 2: Tensor is expected to be of shape (N, 3)
        * None: Either shape is acceptable
    """
    expected_feature_dim = 3
    if len(tensor.shape) == 2 and tensor.shape[1] == expected_feature_dim:
        if expected_first_dim is None or expected_first_dim == 2:
            return
    if len(tensor.shape) == 1 and tensor.shape[0] == expected_feature_dim:
        if expected_first_dim is None or expected_first_dim == 1:
            return
    raise ValueError(f'Improper se2 tensor shape: {tensor.shape}')

def _validate_state_se2_tensor_batch_shape(tensor: torch.Tensor) -> None:
    """
    Validates that a tensor is of the proper shape for a batch of tensorized StateSE2.
    :param tensor: The tensor to validate.
    """
    expected_feature_dim = 3
    if len(tensor.shape) == 2 and tensor.shape[1] == expected_feature_dim:
        return
    raise ValueError(f'Improper se2 tensor batch shape: {tensor.shape}')

def _validate_transform_matrix_shape(tensor: torch.Tensor) -> None:
    """
    Validates that a tensor has the proper shape for a 3x3 transform matrix.
    :param tensor: the tensor to validate.
    """
    if len(tensor.shape) == 2 and tensor.shape[0] == 3 and (tensor.shape[1] == 3):
        return
    raise ValueError(f'Improper transform matrix shape: {tensor.shape}')

def _validate_transform_matrix_batch_shape(tensor: torch.Tensor) -> None:
    """
    Validates that a tensor has the proper shape for a 3x3 transform matrix.
    :param tensor: the tensor to validate.
    """
    if len(tensor.shape) == 3 and tensor.shape[1] == 3 and (tensor.shape[2] == 3):
        return
    raise ValueError(f'Improper transform matrix shape: {tensor.shape}')

def to_scene_agent_type(agent_type: TrackedObjectType) -> str:
    """
    Convert TrackedObjectType to string.
    :param agent_type: TrackedObjectType.
    :return string representing an agent type.
    """
    if agent_type == TrackedObjectType.VEHICLE:
        return 'Vehicle'
    elif agent_type == TrackedObjectType.PEDESTRIAN:
        return 'Pedestrian'
    elif agent_type == TrackedObjectType.BICYCLE:
        return 'Bicycle'
    elif agent_type == TrackedObjectType.GENERIC_OBJECT:
        return 'Generic_object'
    raise ValueError('Unknown input type: {}'.format(str(agent_type)))

def from_scene_to_tracked_objects(scene: Dict[str, Any]) -> TrackedObjects:
    """
    Convert scene["world"] into boxes
    :param scene: scene["world"] coming from json
    :return List of boxes representing all agents
    """
    if 'world' in scene.keys():
        raise ValueError("You need to pass only the 'world' field of scene, not the whole dict!")
    tracked_objects: List[TrackedObject] = []
    scene_labels_map = {'vehicles': TrackedObjectType.VEHICLE, 'bicycles': TrackedObjectType.BICYCLE, 'pedestrians': TrackedObjectType.PEDESTRIAN}
    for label, object_type in scene_labels_map.items():
        if label in scene:
            tracked_objects.extend([from_scene_tracked_object(scene_object, object_type) for scene_object in scene[label]])
    return TrackedObjects(tracked_objects)

def _validate_an_unite_predictions(current_state: Dict[str, Any], future_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Checks that the states are in a temporally consistent order, then builds the prediction with current_state
    and the rest of the future states.
    :param current_state: The current state of the tracked object.
    :param future_states: Future states of prediction.
    :return: Prediction containing the current state as first element.
    """
    if current_state['timestamp'] >= future_states[0]['timestamp']:
        raise ValueError("Timestamp of first state of future states must be larger than the track's timestamp.")
    for prev_state, state in zip(future_states, future_states[1:]):
        if prev_state['timestamp'] >= state['timestamp']:
            raise ValueError('The predictions states must be in strictly increasing temporal order!')
    return [current_state] + future_states

def wrapped_fn(*args: Any, **kwargs: Any) -> Any:
    if log_dir is None:
        return fn(*args, **kwargs)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f'{uuid1().hex}__{fn.__name__}.log'
    logging.basicConfig()
    logger = logging.getLogger()
    fh = logging.FileHandler(log_path, delay=True)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    result = fn(*args, **kwargs)
    fh.flush()
    fh.close()
    logger.removeHandler(fh)
    return result

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

@dataclass
class SimulationLog:
    """Simulation log."""
    file_path: Path
    scenario: AbstractScenario
    planner: AbstractPlanner
    simulation_history: SimulationHistory

    def _dump_to_pickle(self) -> None:
        """
        Dump file into compressed pickle.
        """
        pickle_object = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        save_buffer(self.file_path, lzma.compress(pickle_object, preset=0))

    def _dump_to_msgpack(self) -> None:
        """
        Dump file into compressed msgpack.
        """
        pickle_object = pickle.dumps(self, protocol=pickle.HIGHEST_PROTOCOL)
        msg_packed_bytes = msgpack.packb(pickle_object)
        save_buffer(self.file_path, lzma.compress(msg_packed_bytes, preset=0))

    def save_to_file(self) -> None:
        """
        Dump simulation log into file.
        """
        serialization_type = self.simulation_log_type(self.file_path)
        if serialization_type == 'pickle':
            self._dump_to_pickle()
        elif serialization_type == 'msgpack':
            self._dump_to_msgpack()
        else:
            raise ValueError(f'Unknown option: {serialization_type}')

    @staticmethod
    def simulation_log_type(file_path: Path) -> str:
        """
        Deduce the simulation log type based on the last two portions of the suffix.
        The last suffix must be .xz, since we always dump/load to/from an xz container.
        If the second to last suffix is ".msgpack", assumes the log is of type "msgpack".
        If the second to last suffix is ".pkl", assumes the log is of type "pickle."
        If it's neither, raises a ValueError.
        Examples:
        - "/foo/bar/baz.1.2.pkl.xz" -> "pickle"
        - "/foo/bar/baz/1.2.msgpack.xz" -> "msgpack"
        - "/foo/bar/baz/1.2.msgpack.pkl.xz" -> "pickle"
        - "/foo/bar/baz/1.2.msgpack" -> Error
        :param file_path: File path.
        :return: one from ["msgpack", "pickle"].
        """
        if len(file_path.suffixes) < 2:
            raise ValueError(f'Inconclusive file type: {file_path}')
        last_suffix = file_path.suffixes[-1]
        if last_suffix != '.xz':
            raise ValueError(f'Inconclusive file type: {file_path}')
        second_to_last_suffix = file_path.suffixes[-2]
        log_type_mapping = {'.msgpack': 'msgpack', '.pkl': 'pickle'}
        if second_to_last_suffix not in log_type_mapping:
            raise ValueError(f'Inconclusive file type: {file_path}')
        return log_type_mapping[second_to_last_suffix]

    @classmethod
    def load_data(cls, file_path: Path) -> Any:
        """Load simulation log."""
        simulation_log_type = SimulationLog.simulation_log_type(file_path=file_path)
        if simulation_log_type == 'msgpack':
            with lzma.open(str(file_path), 'rb') as f:
                data = msgpack.unpackb(f.read())
                data = pickle.loads(data)
        elif simulation_log_type == 'pickle':
            with lzma.open(str(file_path), 'rb') as f:
                data = pickle.load(f)
        else:
            raise ValueError(f'Unknown serialization type: {simulation_log_type}!')
        return data

def save_to_file(self) -> None:
    """
        Dump simulation log into file.
        """
    serialization_type = self.simulation_log_type(self.file_path)
    if serialization_type == 'pickle':
        self._dump_to_pickle()
    elif serialization_type == 'msgpack':
        self._dump_to_msgpack()
    else:
        raise ValueError(f'Unknown option: {serialization_type}')

@staticmethod
def simulation_log_type(file_path: Path) -> str:
    """
        Deduce the simulation log type based on the last two portions of the suffix.
        The last suffix must be .xz, since we always dump/load to/from an xz container.
        If the second to last suffix is ".msgpack", assumes the log is of type "msgpack".
        If the second to last suffix is ".pkl", assumes the log is of type "pickle."
        If it's neither, raises a ValueError.
        Examples:
        - "/foo/bar/baz.1.2.pkl.xz" -> "pickle"
        - "/foo/bar/baz/1.2.msgpack.xz" -> "msgpack"
        - "/foo/bar/baz/1.2.msgpack.pkl.xz" -> "pickle"
        - "/foo/bar/baz/1.2.msgpack" -> Error
        :param file_path: File path.
        :return: one from ["msgpack", "pickle"].
        """
    if len(file_path.suffixes) < 2:
        raise ValueError(f'Inconclusive file type: {file_path}')
    last_suffix = file_path.suffixes[-1]
    if last_suffix != '.xz':
        raise ValueError(f'Inconclusive file type: {file_path}')
    second_to_last_suffix = file_path.suffixes[-2]
    log_type_mapping = {'.msgpack': 'msgpack', '.pkl': 'pickle'}
    if second_to_last_suffix not in log_type_mapping:
        raise ValueError(f'Inconclusive file type: {file_path}')
    return log_type_mapping[second_to_last_suffix]

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

def _dump_to_file(file: pathlib.Path, scene_to_save: Any, serialization_type: str) -> None:
    """
    Dump scene into file
    :param serialization_type: type of serialization ["json", "pickle", "msgpack"]
    :param file: file name
    :param scene_to_save: what to store
    """
    if serialization_type == 'json':
        _dump_to_json(file, scene_to_save)
    elif serialization_type == 'pickle':
        _dump_to_pickle(file, scene_to_save)
    elif serialization_type == 'msgpack':
        _dump_to_msgpack(file, scene_to_save)
    else:
        raise ValueError(f'Unknown option: {serialization_type}')

def callable_name_matches(a: Callable[..., Any], b: Callable[..., Any]) -> bool:
    """
    Checks that callable names match.
    :param a: first callable to compare.
    :param b: second callable to compare.
    :return: true if the names match, otherwise false.
    """
    if hasattr(a, '__name__'):
        if a.__name__ != b.__name__:
            return False
    elif 'object at' in (a_repr := repr(a)):
        address_ind = a_repr.index('object at')
        a_name = a_repr[1:address_ind - 1]
        b_name = repr(b)[1:address_ind - 1]
        if a_name != b_name:
            return False
    else:
        raise NotImplementedError
    return True

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

def _check_inputs(self, x_curr: Sequence[float], reference_trajectory: Sequence[Pose]) -> None:
    """Raise ValueError if inputs are not of proper size."""
    if len(x_curr) != self.nx:
        raise ValueError(f'x_curr length {len(x_curr)} must be equal to state dim {self.nx}')
    if len(reference_trajectory) != self.trajectory_len + 1:
        raise ValueError(f'reference traj length {len(reference_trajectory)} must be equal to {self.trajectory_len + 1}')

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

class EgoInternalIndex:
    """
    A convenience class for assigning semantic meaning to the tensor indexes
      in the Ego Trajectory Tensors.

    It is intended to be used like an IntEnum, but supported by TorchScript
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the ego x position.
        :return: index
        """
        return 0

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the ego y position.
        :return: index
        """
        return 1

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the ego heading.
        :return: index
        """
        return 2

    @staticmethod
    def vx() -> int:
        """
        The dimension corresponding to the ego x velocity.
        :return: index
        """
        return 3

    @staticmethod
    def vy() -> int:
        """
        The dimension corresponding to the ego y velocity.
        :return: index
        """
        return 4

    @staticmethod
    def ax() -> int:
        """
        The dimension corresponding to the ego x acceleration.
        :return: index
        """
        return 5

    @staticmethod
    def ay() -> int:
        """
        The dimension corresponding to the ego y acceleration.
        :return: index
        """
        return 6

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the EgoInternal buffer.
        :return: number of features.
        """
        return 7

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

class AgentInternalIndex:
    """
    A convenience class for assigning semantic meaning to the tensor indexes
      in the tensors used to compute the final Agent Feature.


    It is intended to be used like an IntEnum, but supported by TorchScript
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def track_token() -> int:
        """
        The dimension corresponding to the track_token for the agent.
        :return: index
        """
        return 0

    @staticmethod
    def vx() -> int:
        """
        The dimension corresponding to the x velocity of the agent.
        :return: index
        """
        return 1

    @staticmethod
    def vy() -> int:
        """
        The dimension corresponding to the y velocity of the agent.
        :return: index
        """
        return 2

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the heading of the agent.
        :return: index
        """
        return 3

    @staticmethod
    def width() -> int:
        """
        The dimension corresponding to the width of the agent.
        :return: index
        """
        return 4

    @staticmethod
    def length() -> int:
        """
        The dimension corresponding to the length of the agent.
        :return: index
        """
        return 5

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the x position of the agent.
        :return: index
        """
        return 6

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the y position of the agent.
        :return: index
        """
        return 7

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the AgentsInternal buffer.
        :return: number of features.
        """
        return 8

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

def _get_traffic_light_status_at_iteration_patch(iteration: int) -> Generator[TrafficLightStatusData, None, None]:
    """A patch to populate traffic light states for the 0th iteration only."""
    if iteration != 0:
        raise ValueError('We expect the vector map builder to only use the 0th iteration TL states.')
    yield from traffic_light_statuses

class GenericEgoFeatureIndex:
    """
    A convenience class for assigning semantic meaning to the tensor index
        in the final output ego feature.

    It is intended to be used like an IntEnum, but supported by TorchScript.
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the x coordinate of the ego.
        :return: index
        """
        return 0

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the y coordinate of the ego.
        :return: index
        """
        return 1

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the heading of the ego.
        :return: index
        """
        return 2

    @staticmethod
    def vx() -> int:
        """
        The dimension corresponding to the x velocity of the ego.
        :return: index
        """
        return 3

    @staticmethod
    def vy() -> int:
        """
        The dimension corresponding to the y velocity of the ego.
        :return: index
        """
        return 4

    @staticmethod
    def ax() -> int:
        """
        The dimension corresponding to the x acceleration of the ego.
        :return: index
        """
        return 5

    @staticmethod
    def ay() -> int:
        """
        The dimension corresponding to the y acceleration of the ego.
        :return: index
        """
        return 6

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the EgoFeature.
        :return: number of features.
        """
        return 7

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

class GenericAgentFeatureIndex:
    """
    A convenience class for assigning semantic meaning to the tensor indexes
        in the final output agents feature.

    It is intended to be used like an IntEnum, but supported by TorchScript.
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the x coordinate of the agent.
        :return: index
        """
        return 0

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the y coordinate of the agent.
        :return: index
        """
        return 1

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the heading of the agent.
        :return: index
        """
        return 2

    @staticmethod
    def vx() -> int:
        """
        The dimension corresponding to the x velocity of the agent.
        :return: index
        """
        return 3

    @staticmethod
    def vy() -> int:
        """
        The dimension corresponding to the y velocity of the agent.
        :return: index
        """
        return 4

    @staticmethod
    def yaw_rate() -> int:
        """
        The dimension corresponding to the yaw rate of the agent.
        :return: index
        """
        return 5

    @staticmethod
    def length() -> int:
        """
        The dimension corresponding to the length of the agent.
        :return: index
        """
        return 6

    @staticmethod
    def width() -> int:
        """
        The dimension corresponding to the width of the agent.
        :return: index
        """
        return 7

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the AgentsFeature.
        :return: number of features.
        """
        return 8

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

class EgoFeatureIndex:
    """
    A convenience class for assigning semantic meaning to the tensor index
        in the final output ego feature.

    It is intended to be used like an IntEnum, but supported by TorchScript.
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the x coordinate of the ego.
        :return: index
        """
        return 0

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the y coordinate of the ego.
        :return: index
        """
        return 1

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the heading of the ego.
        :return: index
        """
        return 2

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the EgoFeature.
        :return: number of features.
        """
        return 3

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

class AgentFeatureIndex:
    """
    A convenience class for assigning semantic meaning to the tensor indexes
        in the final output agents feature.

    It is intended to be used like an IntEnum, but supported by TorchScript
    """

    def __init__(self) -> None:
        """
        Init method.
        """
        raise ValueError('This class is not to be instantiated.')

    @staticmethod
    def x() -> int:
        """
        The dimension corresponding to the x coordinate of the agent.
        :return: index
        """
        return 0

    @staticmethod
    def y() -> int:
        """
        The dimension corresponding to the y coordinate of the agent.
        :return: index
        """
        return 1

    @staticmethod
    def heading() -> int:
        """
        The dimension corresponding to the heading of the agent.
        :return: index
        """
        return 2

    @staticmethod
    def vx() -> int:
        """
        The dimension corresponding to the x velocity of the agent.
        :return: index
        """
        return 3

    @staticmethod
    def vy() -> int:
        """
        The dimension corresponding to the y velocity of the agent.
        :return: index
        """
        return 4

    @staticmethod
    def yaw_rate() -> int:
        """
        The dimension corresponding to the yaw rate of the agent.
        :return: index
        """
        return 5

    @staticmethod
    def length() -> int:
        """
        The dimension corresponding to the length of the agent.
        :return: index
        """
        return 6

    @staticmethod
    def width() -> int:
        """
        The dimension corresponding to the width of the agent.
        :return: index
        """
        return 7

    @staticmethod
    def dim() -> int:
        """
        The number of features present in the AgentsFeature.
        :return: number of features.
        """
        return 8

def __init__(self) -> None:
    """
        Init method.
        """
    raise ValueError('This class is not to be instantiated.')

def _validate_coords_shape(coords: FeatureDataType) -> None:
    """
    Validate coordinates have proper shape: <num_map_elements, num_points_per_element, 2>.
    :param coords: Coordinates to validate.
    :raise ValueError: If coordinates dimensions are not valid.
    """
    if len(coords.shape) != 3 or coords.shape[2] != 2:
        raise ValueError(f'Unexpected coords shape: {coords.shape}. Expected shape: (*, *, 2)')

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

class MetricStatisticsType(Enum):
    """Enum of different types for statistics."""
    MAX = 'MAX'
    MIN = 'MIN'
    P90 = 'P90'
    MEAN = 'MEAN'
    VALUE = 'VALUE'
    VELOCITY = 'VELOCITY'
    BOOLEAN = 'BOOLEAN'
    RATIO = 'RATIO'
    COUNT = 'COUNT'

    def __str__(self) -> str:
        """Metric type string representation."""
        return str(self.value)

    def __repr__(self) -> str:
        """Metric type string representation."""
        return str(self.value)

    @property
    def unit(self) -> str:
        """Get a default unit with a type."""
        if self.value == 'BOOLEAN':
            return 'boolean'
        elif self.value == 'RATIO':
            return 'ratio'
        elif self.value == 'COUNT':
            return 'count'
        else:
            raise ValueError(f"{self.value} don't have a default unit!")

    def serialize(self) -> str:
        """Serialize the type when saving."""
        return self.value

    @classmethod
    def deserialize(cls, key: str) -> MetricStatisticsType:
        """Deserialize the type when loading from a string."""
        return MetricStatisticsType.__members__[key]

@property
def unit(self) -> str:
    """Get a default unit with a type."""
    if self.value == 'BOOLEAN':
        return 'boolean'
    elif self.value == 'RATIO':
        return 'ratio'
    elif self.value == 'COUNT':
        return 'count'
    else:
        raise ValueError(f"{self.value} don't have a default unit!")

def get_route_obj_with_candidates(pose: Point2D, candidate_route_objs: List[GraphEdgeMapObject]) -> List[GraphEdgeMapObject]:
    """
    This function uses a candidate set of lane/lane-connectors and return the lane/lane-connector that correponds to the pose
    by checking if pose belongs to one of the route objs in candidate_route_objs or their outgoing_edges
    :param pose: ego_pose
    :param candidate_route_objs: a list of route objects
    :return: a list of route objects corresponding to the pose
    """
    if not len(candidate_route_objs):
        raise ValueError('candidate_route_objs list is empty, no candidates to start with')
    route_objects_with_pose = [one_route_obj for one_route_obj in candidate_route_objs if one_route_obj.contains_point(pose)]
    if not route_objects_with_pose and len(candidate_route_objs) == 1:
        route_objects_with_pose = [next_route_obj for next_route_obj in candidate_route_objs[0].outgoing_edges if next_route_obj.contains_point(pose)]
    return route_objects_with_pose

def get_common_route_object(corners_route_obj_ids: List[Set[str]], obj_id_dict: dict[str, GraphEdgeMapObject]) -> Set[GraphEdgeMapObject]:
    """
    Extracts common lane/lane connectors of corners
    :param corners_route_obj_ids: List of ids of route objects of corners of ego
    :param obj_id_dict: dictionary of ids and corresponding route objects
    :return set of common route objects, returns an empty set of no common object is found.
    """
    return {obj_id_dict[id] for id in set.intersection(*corners_route_obj_ids)}

class PerFrameProgressAlongRouteComputer:
    """Class that computes progress per frame along a route."""

    def __init__(self, route_roadblocks: RouteRoadBlockLinkedList):
        """Class initializer
        :param route_roadblocks: A route roadblock linked list.
        """
        self.curr_roadblock_pair = route_roadblocks.head
        self.progress = [float(0)]
        self.prev_distance_to_start = float(0)
        self.next_roadblock_pair: Optional[RouteBaselineRoadBlockPair] = None
        self.skipped_roadblock_pair: Optional[RouteBaselineRoadBlockPair] = None

    @staticmethod
    def get_some_baseline_point(baseline: PolylineMapObject, ind: str) -> Optional[Point2D]:
        """Gets the first or last point on a given baselinePath
        :param baseline: A baseline path
        :param ind: Either 'last' or 'first' strings to show which point function should return
        :return: A point.
        """
        if ind == 'last':
            return Point2D(baseline.linestring.xy[0][-1], baseline.linestring.xy[1][-1])
        elif ind == 'first':
            return Point2D(baseline.linestring.xy[0][0], baseline.linestring.xy[1][0])
        else:
            raise ValueError('invalid position argument')

    def compute_progress_for_skipped_road_block(self) -> float:
        """Computes progress for skipped road_blocks (when ego pose exits one road block in a route and it does not
        enter the next one)
        :return: progress_for_skipped_roadblock
        """
        assert self.next_roadblock_pair is not None
        if self.skipped_roadblock_pair:
            prev_roadblock_last_point = self.get_some_baseline_point(self.skipped_roadblock_pair.base_line, 'last')
        else:
            prev_roadblock_last_point = self.get_some_baseline_point(self.curr_roadblock_pair.base_line, 'last')
        self.skipped_roadblock_pair = self.next_roadblock_pair
        skipped_distance_to_start = get_distance_of_closest_baseline_point_to_its_start(self.skipped_roadblock_pair.base_line, prev_roadblock_last_point)
        self.next_roadblock_pair = self.next_roadblock_pair.next
        next_roadblock_first_point = self.get_some_baseline_point(self.next_roadblock_pair.base_line, 'first')
        next_baseline_start_dist_to_skipped = get_distance_of_closest_baseline_point_to_its_start(self.skipped_roadblock_pair.base_line, next_roadblock_first_point)
        progress_for_skipped_roadblock: float = next_baseline_start_dist_to_skipped - skipped_distance_to_start
        return progress_for_skipped_roadblock

    def get_progress_including_skipped_roadblocks(self, ego_pose: Point2D, progress_for_skipped_roadblock: float) -> float:
        """Computes ego's progress when it first enters a new road-block in the route by considering possible progress
        for roadblocks it has skipped as multi_block_progress = (progress along the baseline of prev ego roadblock)
        + (progress along the baseline of the roadblock ego is in now) + (progress along skipped roadblocks if any).
        :param ego_pose: ego pose
        :param progress_for_skipped_roadblock: Prgoress for skipped road_blocks (zero if no roadblocks is skipped)
        :return: multi_block_progress
        """
        assert self.next_roadblock_pair is not None
        progress_in_prev_roadblock = self.curr_roadblock_pair.base_line.linestring.length - self.prev_distance_to_start
        prev_roadblock_last_point = self.get_some_baseline_point(self.curr_roadblock_pair.base_line, 'last')
        self.curr_roadblock_pair = self.next_roadblock_pair
        distance_to_start = get_distance_of_closest_baseline_point_to_its_start(self.curr_roadblock_pair.base_line, ego_pose)
        last_baseline_point_dist_to_start = get_distance_of_closest_baseline_point_to_its_start(self.curr_roadblock_pair.base_line, prev_roadblock_last_point)
        progress_in_new_roadblock = distance_to_start - last_baseline_point_dist_to_start
        multi_block_progress = progress_in_prev_roadblock + progress_in_new_roadblock + progress_for_skipped_roadblock
        self.prev_distance_to_start = distance_to_start
        return float(multi_block_progress)

    def get_multi_block_progress(self, ego_pose: Point2D) -> float:
        """When ego pose exits previous roadblock this function takes next road blocks in the expert route one by one
        until it finds one (if any) that pose belongs to. Once found, ego progress for multiple roadblocks including
        possible skipped roadblocks is computed and returned
        :param ego_pose: ego pose
        :return: multi block progress
        """
        multi_block_progress = float(0)
        progress_for_skipped_roadblocks = float(0)
        self.next_roadblock_pair = self.curr_roadblock_pair.next
        self.skipped_roadblock_pair = None
        while self.next_roadblock_pair is not None:
            if self.next_roadblock_pair.road_block.contains_point(ego_pose):
                multi_block_progress = self.get_progress_including_skipped_roadblocks(ego_pose, progress_for_skipped_roadblocks)
                break
            elif not self.next_roadblock_pair.next:
                break
            else:
                progress_for_skipped_roadblocks += self.compute_progress_for_skipped_road_block()
        return multi_block_progress

    def __call__(self, ego_poses: List[Point2D]) -> List[float]:
        """
        Computes per frame progress along the route baselines for ego poses
        :param ego_poses: ego poses
        :return: progress along the route.
        """
        self.prev_distance_to_start = get_distance_of_closest_baseline_point_to_its_start(self.curr_roadblock_pair.base_line, ego_poses[0])
        for ego_pose in ego_poses[1:]:
            if self.curr_roadblock_pair.road_block.contains_point(ego_pose):
                distance_to_start = get_distance_of_closest_baseline_point_to_its_start(self.curr_roadblock_pair.base_line, ego_pose)
                self.progress.append(distance_to_start - self.prev_distance_to_start)
                self.prev_distance_to_start = distance_to_start
            else:
                multi_block_progress = self.get_multi_block_progress(ego_pose)
                self.progress.append(multi_block_progress)
        return self.progress

@staticmethod
def get_some_baseline_point(baseline: PolylineMapObject, ind: str) -> Optional[Point2D]:
    """Gets the first or last point on a given baselinePath
        :param baseline: A baseline path
        :param ind: Either 'last' or 'first' strings to show which point function should return
        :return: A point.
        """
    if ind == 'last':
        return Point2D(baseline.linestring.xy[0][-1], baseline.linestring.xy[1][-1])
    elif ind == 'first':
        return Point2D(baseline.linestring.xy[0][0], baseline.linestring.xy[1][0])
    else:
        raise ValueError('invalid position argument')

class TqdmLoggingHandler(logging.Handler):
    """
    Log consistently when using the tqdm progress bar.
    From https://stackoverflow.com/questions/38543506/
    change-logging-print-function-to-tqdm-write-so-logging-doesnt-interfere-wit
    """

    def __init__(self, level: int=logging.NOTSET) -> None:
        """
        Constructor.
        :param level: A log level.
        """
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Consistently emit the specified logging record.
        :param record: Logging.LogRecord, the record to emit.
        """
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

def emit(self, record: logging.LogRecord) -> None:
    """
        Consistently emit the specified logging record.
        :param record: Logging.LogRecord, the record to emit.
        """
    try:
        msg = self.format(record)
        tqdm.tqdm.write(msg)
        self.flush()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        self.handleError(record)

def configure_logger(handler_configs: List[LogHandlerConfig], format_str: str='%(asctime)s %(levelname)-2s {%(pathname)s:%(lineno)d}  %(message)s') -> logging.Logger:
    """
    Configures the python default logger.
    :param handler_configs: List of LogHandlerConfig objects specifying the logger handlers.
    :param format_str: Formats the log events.
    :return: A logger.
    """
    logger = logging.getLogger()
    for old_handler in logger.handlers:
        logger.removeHandler(old_handler)
    for config in handler_configs:
        if not config.path:
            handler = TqdmLoggingHandler()
        else:
            handler = logging.FileHandler(config.path)
        handler.setLevel(LOGGING_LEVEL_MAP[config.level])
        handler.setFormatter(logging.Formatter(format_str))
        handler.addFilter(PathKeywordMatch(config.filter_regexp))
        logger.addHandler(handler)
    return logger

def build_logger(cfg: DictConfig) -> logging.Logger:
    """
    Setup the standard logger, always log to sys.stdout and optionally log to disk.
    :param cfg: Input dict config.
    :return: Logger with associated handlers.
    """
    handler_configs = [LogHandlerConfig(level=cfg.logger_level)]
    if cfg.output_dir is not None:
        path = str(Path(cfg.output_dir) / 'log.txt')
        handler_configs.append(LogHandlerConfig(level=cfg.logger_level, path=path))
    format_string = '%(asctime)s %(levelname)-2s {%(pathname)s:%(lineno)d}  %(message)s' if not cfg.logger_format_string else cfg.logger_format_string
    logger = configure_logger(handler_configs, format_str=format_string)
    if cfg.gpu:
        logger.disabled = int(os.environ.get('LOCAL_RANK', 0)) != 0
    logger.setLevel(level=LOGGING_LEVEL_MAP[cfg.logger_level])
    return logger

class TestPathKeywordMatch(unittest.TestCase):
    """Test PathKeywordMatch class."""
    log_record = logging.LogRecord('', logging.NOTSET, '/my/filtered/path', 0, msg='', args=None, exc_info=None)

    def test_default_filter(self) -> None:
        """Test filtering by default pattern, which means no filter."""
        pkm = PathKeywordMatch()
        self.assertTrue(pkm.filter(self.log_record))

    def test_filter(self) -> None:
        """Test filtering by a custom pattern."""
        pkm = PathKeywordMatch(regexp='filtered')
        self.assertFalse(pkm.filter(self.log_record))

def test_default_filter(self) -> None:
    """Test filtering by default pattern, which means no filter."""
    pkm = PathKeywordMatch()
    self.assertTrue(pkm.filter(self.log_record))

def test_filter(self) -> None:
    """Test filtering by a custom pattern."""
    pkm = PathKeywordMatch(regexp='filtered')
    self.assertFalse(pkm.filter(self.log_record))

def _are_lidarpc_tokens_in_set(scenario: NuPlanScenario, token_set: Set[str], fraction_threshold: float) -> bool:
    """
        For a single scenario, report whether (True/False) the fraction of the scenario's lidarpc tokens
            in token_set is greater than fraction_threshold (greater than or equal to for fraction_threshold=1).
        :param scenario: a valid NuplanScenario instance.
        :param token_set: a Pyton Set of lidarpc tokens from a Nuplan DB.
        :param fraction_threshold: a Python float in [0, 1].
        :return: True if strictly more than fraction_threshold fraction of the lidarpc tokens in scenario belong to
            token_set (strictly equal if fraction_threshold is 1)
        """
    scenario_tokens = set(scenario.get_scenario_tokens())
    if fraction_threshold == 1:
        return scenario_tokens == token_set
    return len(scenario_tokens.intersection(token_set)) / len(scenario_tokens) > fraction_threshold

def filter_non_stationary_ego(scenario_dict: ScenarioDict, minimum_threshold: float) -> ScenarioDict:
    """
    Filters a ScenarioDict, leaving only scenarios (of any type) in which the ego center travels at least
        minimum_threshold meters cumulatively. These are "non-stationary ego scenarios"
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type. Modified by function
    :param minimum_threshold: minimum distance in meters (inclusive, cumulative) the ego center has to travel in a given
        scenario for the scenario to be called a non-stationary ego scenario
    :return: Filtered scenario dictionary where the cumulative frame-to-frame displacement of the ego center in the
        scenario is >= the minimum threshold
    """
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = list(filter(lambda scenario: _is_non_stationary(scenario, minimum_threshold), scenario_dict[scenario_type]))
    return scenario_dict

def filter_ego_starts(scenario_dict: ScenarioDict, speed_threshold: float, speed_noise_tolerance: float) -> ScenarioDict:
    """
    Filters a ScenarioDict, leaving only scenarios where the ego has started from a static position at some point

    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type. Modified by function
    :param speed_threshold: exclusive minimum velocity in meters per second that the ego rear axle must reach to be
        considered started
    :return: Filtered scenario dictionary where the ego reaches a speed greater than speed_threshold m/s from below
        at some point in all scenarios
    """
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = list(filter(lambda scenario: _check_for_speed_edge(scenario, speed_threshold, speed_noise_tolerance, EdgeType.RISING), scenario_dict[scenario_type]))
    return scenario_dict

def filter_ego_stops(scenario_dict: ScenarioDict, speed_threshold: float, speed_noise_tolerance: float) -> ScenarioDict:
    """
    Filters a ScenarioDict, leaving only scenarios where the ego has stopped from a moving position at some point

    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type. Modified by function
    :param speed_threshold: inclusive maximum velocity in meters per second that the ego rear axle must reach to be
        considered stopped
    :return: Filtered scenario dictionary where the ego reaches a speed less than or equal to speed_threshold m/s
        from above at some point in all scenarios
    """
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = list(filter(lambda scenario: _check_for_speed_edge(scenario, speed_threshold, speed_noise_tolerance, EdgeType.FALLING), scenario_dict[scenario_type]))
    return scenario_dict

def filter_ego_has_route(scenario_dict: ScenarioDict, map_radius: float) -> ScenarioDict:
    """
    Rid a scenario dictionary of the scenarios that don't have an on-route lane segment within map_radius meters of the ego.
    Uses a VectorMap to gather lane segments.
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type.
    :param map_radius: How far out from ego to check for on-route lane segments.
    :return: Filtered scenario dictionary.
    """
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = list(filter(lambda scenario: _ego_has_route(scenario, map_radius), scenario_dict[scenario_type]))
    return scenario_dict

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

def _format_url(self, api: str) -> str:
    """
        Creates correct URL using api and server.
        :param api: The requested API.
        :return: The formatted URL.
        """
    assert api in URLS, f'Requested API unavailable, available ones are {URLS}'
    return f'{self.EVALAI_API_SERVER}{URLS.get(api).format(self.CHALLENGE_PK)}'

def get_submission_logger(logger_name: str, logfile: str='/tmp/submission.log') -> logging.Logger:
    """
    Returns a logger with level WARNING that logs to the given file.
    :param logger_name: Name for the logger.
    :param logfile: Output file for the logger.
    :return: The logger.
    """
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s')
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

