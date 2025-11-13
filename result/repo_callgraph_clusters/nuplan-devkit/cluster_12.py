# Cluster 12

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
def distance_to_ego(self) -> float:
    """
        Returns the distance of detection from Ego Vehicle.
        :return: The distance to ego vehicle.
        """
    return float(np.sqrt((self.x - self.lidar_pc.ego_pose.x) ** 2 + (self.y - self.lidar_pc.ego_pose.y) ** 2))

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

def box(self) -> Box3D:
    """
        Get the Box3D representation of the box.
        :return: The box3d representation of the box.
        """
    label_local = raw_mapping['global2local'][self.category.name]
    label_int = raw_mapping['local2id'][label_local]
    return Box3D(center=self.translation, size=self.size, orientation=self.quaternion, token=self.token, label=label_int, track_token=self.track_token)

class Camera(Base):
    """
    Defines a calibrated camera used to record a particular log.
    """
    __tablename__ = 'camera'
    token = Column(sql_types.HexLen8, primary_key=True)
    log_token = Column(sql_types.HexLen8, ForeignKey('log.token'), nullable=False)
    channel = Column(String(64))
    model = Column(String(64))
    translation = Column(sql_types.SqlTranslation)
    rotation = Column(sql_types.SqlRotation)
    intrinsic = Column(sql_types.SqlCameraIntrinsic)
    distortion = Column(PickleType)
    width = Column(Integer)
    height = Column(Integer)

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
        :return : The string representation.
        """
        desc: str = simple_repr(self)
        return desc

    @property
    def intrinsic_np(self) -> npt.NDArray[np.float64]:
        """
        Get the intrinsic in numpy format.
        :return: <np.float: 3, 3> Camera intrinsic.
        """
        return np.array(self.intrinsic)

    @property
    def distortion_np(self) -> npt.NDArray[np.float64]:
        """
        Get the distortion in numpy format.
        :return: <np.float: N> Camera distrotion.
        """
        return np.array(self.distortion)

    @property
    def translation_np(self) -> npt.NDArray[np.float64]:
        """
        Get the translation in numpy format.
        :return: <np.float: 3> Translation.
        """
        return np.array(self.translation)

    @property
    def quaternion(self) -> Quaternion:
        """
        Get the rotation in quaternion.
        :return: Rotation in quaternion.
        """
        return Quaternion(self.rotation)

    @property
    def trans_matrix(self) -> npt.NDArray[np.float64]:
        """
        Get the transformation matrix.
        :return: <np.float: 4, 4>. Transformation matrix.
        """
        tm: npt.NDArray[np.float64] = self.quaternion.transformation_matrix
        tm[:3, 3] = self.translation_np
        return tm

    @property
    def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
        """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
        tm: npt.NDArray[np.float64] = np.eye(4)
        rot_inv = self.quaternion.rotation_matrix.T
        tm[:3, :3] = rot_inv
        tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
        return tm

@property
def intrinsic_np(self) -> npt.NDArray[np.float64]:
    """
        Get the intrinsic in numpy format.
        :return: <np.float: 3, 3> Camera intrinsic.
        """
    return np.array(self.intrinsic)

@property
def distortion_np(self) -> npt.NDArray[np.float64]:
    """
        Get the distortion in numpy format.
        :return: <np.float: N> Camera distrotion.
        """
    return np.array(self.distortion)

@property
def translation_np(self) -> npt.NDArray[np.float64]:
    """
        Get the translation in numpy format.
        :return: <np.float: 3> Translation.
        """
    return np.array(self.translation)

@property
def quaternion(self) -> Quaternion:
    """
        Get the rotation in quaternion.
        :return: Rotation in quaternion.
        """
    return Quaternion(self.rotation)

@property
def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
    """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
    tm: npt.NDArray[np.float64] = np.eye(4)
    rot_inv = self.quaternion.rotation_matrix.T
    tm[:3, :3] = rot_inv
    tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
    return tm

def rotate(inp: npt.NDArray[np.float64], quaternion: Quaternion) -> npt.NDArray[np.float64]:
    """
    Rotate a vector.
    :param inp: Vector to rotate.
    :param quaternion: Rotation.
    :return: Rotated vector.
    """
    rotation_matrix: npt.NDArray[np.float64] = quaternion.rotation_matrix
    return np.dot(rotation_matrix, inp)

def transform(inp: npt.NDArray[np.float64], trans_matrix: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Transform a vector.
    :param inp: Vector to transform.
    :param trans_matrix: Transformation matrix.
    :return: Transformed vector.
    """
    inp = rotate(inp, Quaternion(matrix=trans_matrix[:3, :3]))
    inp = translate(inp, trans_matrix[:3, 3])
    return inp

def get_colors_marker(labelmap: Optional[Dict[int, Label]], box: Box3D) -> Tuple[Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float], str]], Optional[str]]:
    """
    Get the color and marker to use.
    :param labelmap: The labelmap is used to color the boxes. If not provided, default colors from box.render() will be
        used.
    :param box: The box for which color and marker are to be returned.
    :return: The color and marker to be used.
    """
    if labelmap is not None:
        c = np.array(labelmap[box.label].color)[:-1] / 255.0
        colors = (c, c, 'k')
    else:
        colors = None
    if box.label == 2:
        marker = None
    else:
        marker = 'o'
    return (colors, marker)

class Category(Base):
    """
    A category within our taxonomy. Includes both things (e.g. cars) or stuff (e.g. lanes, sidewalks).
    Subcategories are delineated by a period.
    """
    __tablename__ = 'category'
    token = Column(sql_types.HexLen8, primary_key=True)
    name = Column(String(64))
    description = Column(Text)

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
    def color(self) -> Tuple[int, int, int]:
        """
        Get category color.
        :return: The category color tuple.
        """
        c: Tuple[int, int, int] = default_color(self.name)
        return c

    @property
    def color_np(self) -> npt.NDArray[np.float64]:
        """
        Get category color in numpy.
        :return: The category color in numpy.
        """
        c: npt.NDArray[np.float64] = default_color_np(self.name)
        return c

@property
def color(self) -> Tuple[int, int, int]:
    """
        Get category color.
        :return: The category color tuple.
        """
    c: Tuple[int, int, int] = default_color(self.name)
    return c

class EgoPose(Base):
    """
    Ego vehicle pose at a particular timestamp. Given with respect to global coordinate system.
    """
    __tablename__ = 'ego_pose'
    token = Column(sql_types.HexLen8, primary_key=True)
    timestamp = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    qw: float = Column(Float)
    qx: float = Column(Float)
    qy: float = Column(Float)
    qz: float = Column(Float)
    vx = Column(Float)
    vy = Column(Float)
    vz = Column(Float)
    acceleration_x = Column(Float)
    acceleration_y = Column(Float)
    acceleration_z = Column(Float)
    angular_rate_x = Column(Float)
    angular_rate_y = Column(Float)
    angular_rate_z = Column(Float)
    epsg = Column(Integer)
    log_token = Column(sql_types.HexLen8, ForeignKey('log.token'), nullable=False)

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
    def quaternion(self) -> Quaternion:
        """
        Get the orientation of ego vehicle as quaternion respect to global coordinate system.
        :return: The orientation in quaternion.
        """
        return Quaternion(self.qw, self.qx, self.qy, self.qz)

    @property
    def translation_np(self) -> npt.NDArray[np.float64]:
        """
        Position of ego vehicle respect to global coordinate system.
        :return: <np.float: 3> Translation.
        """
        return np.array([self.x, self.y, self.z])

    @property
    def trans_matrix(self) -> npt.NDArray[np.float64]:
        """
        Get the transformation matrix.
        :return: <np.float: 4, 4>. Transformation matrix.
        """
        tm: npt.NDArray[np.float64] = self.quaternion.transformation_matrix
        tm[:3, 3] = self.translation_np
        return tm

    @property
    def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
        """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
        tm: npt.NDArray[np.float64] = np.eye(4)
        rot_inv = self.quaternion.rotation_matrix.T
        tm[:3, :3] = rot_inv
        tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
        return tm

    def rotate_2d_points2d_to_ego_vehicle_frame(self, points2d: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """
        Rotate 2D points from global frame to ego-vehicle frame.
        :param points2d: <np.float: num_points, 2>. 2D points in global frame.
        :return: <np.float: num_points, 2>. 2D points rotated to ego-vehicle frame.
        """
        points3d: npt.NDArray[np.float32] = np.concatenate((points2d, np.zeros_like(points2d[:, 0:1])), axis=-1)
        rotation = R.from_matrix(self.quaternion.rotation_matrix.T)
        ego_rotation_angle = rotation.as_euler('zxy', degrees=True)[0]
        xy_rotation = R.from_euler('z', ego_rotation_angle, degrees=True)
        rotated_points3d = xy_rotation.apply(points3d)
        rotated_points2d: npt.NDArray[np.float64] = rotated_points3d[:, :2]
        return rotated_points2d

    def get_map_crop(self, maps_db: Optional[GPKGMapsDB], xrange: Tuple[float, float], yrange: Tuple[float, float], map_layer_name: str, rotate_face_up: bool, target_imsize_xy: Optional[Tuple[float, float]]=None) -> Tuple[Optional[npt.NDArray[np.float64]], npt.NDArray[np.float64], Tuple[float, ...]]:
        """
        This function returns the crop of the map centered at the current ego-pose with the given xrange and yrange.
        :param maps_db: Map database associated with this database.
        :param xrange: The range in x direction in meters relative to the current ego-pose. Eg: (-60, 60]).
        :param yrange: The range in y direction in meters relative to the current ego-pose Eg: (-60, 60).
        :param map_layer_name: A relevant map layer. Eg: 'drivable_area' or 'intensity'.
        :param rotate_face_up: Boolean indicating whether to rotate the image face up with respect to ego-pose.
        :param target_imsize_xy: The target grid xy dimensions for the output array. The xy resolution in meters / grid
            may be scaled by zooming to the desired dimensions.
        :return: (map_crop, map_translation, map_scale). Where:
            map_crop: The desired crop of the map.
            map_translation: The translation in map coordinates from the origin to the ego-pose.
            map_scale: Map scale (inverse of the map precision). This will be a tuple specifying the zoom in both the x
                and y direction if the target_imsize_xy parameter was set, which causes the resolution to change.

            map_scale and map_translation are useful for transforming objects like pointcloud/boxes to the map_crop.
            Refer to render_on_map().
        """
        if maps_db is None:
            precision: float = 1

            def to_pixel_coords(x: float, y: float) -> Tuple[float, float]:
                """
                Get the image coordinates given the x-y coordinates of point. This implementation simply returns the
                same coordinates.
                :param x: Global x coordinate.
                :param y: Global y coordinate.
                :return: Pixel coordinates in map.
                """
                return (x, y)
        else:
            map_layer = maps_db.load_layer(self.log.map_version, map_layer_name)
            precision = map_layer.precision
            to_pixel_coords = map_layer.to_pixel_coords
        map_scale: Tuple[float, ...] = (1.0 / precision, 1.0 / precision, 1.0)
        ego_translation = self.translation_np
        center_x, center_y = to_pixel_coords(ego_translation[0], ego_translation[1])
        center_x, center_y = (int(center_x), int(center_y))
        top_left = (int(xrange[0] * map_scale[0]), int(yrange[0] * map_scale[1]))
        bottom_right = (int(xrange[1] * map_scale[0]), int(yrange[1] * map_scale[1]))
        rotation = R.from_matrix(self.quaternion.rotation_matrix.T)
        ego_rotation_angle = rotation.as_euler('zxy', degrees=True)[0]
        xy_rotation = R.from_euler('z', ego_rotation_angle, degrees=True)
        map_rotate = 0
        rotated = xy_rotation.apply([[top_left[0], top_left[1], 0], [top_left[0], bottom_right[1], 0], [bottom_right[0], top_left[1], 0], [bottom_right[0], bottom_right[1], 0]])[:, :2]
        rect = cv2.minAreaRect(np.hstack([rotated[:, :1] + center_x, rotated[:, 1:] + center_y]).astype(int))
        rect_angle = rect[2]
        cropped_dimensions: npt.NDArray[np.float32] = np.array([map_scale[0] * (xrange[1] - xrange[0]), map_scale[1] * (yrange[1] - yrange[0])])
        rect = (rect[0], cropped_dimensions, rect_angle)
        rect_angle = rect[2]
        cropped_dimensions = np.array([map_scale[0] * (xrange[1] - xrange[0]), map_scale[1] * (yrange[1] - yrange[0])])
        if rect_angle >= 0:
            rect = (rect[0], cropped_dimensions, rect_angle - 90)
        else:
            rect = (rect[0], cropped_dimensions, rect_angle)
        if ego_rotation_angle < -90:
            map_rotate = -90
        if -90 < ego_rotation_angle < 0:
            map_rotate = 0
        if 0 < ego_rotation_angle < 90:
            map_rotate = 90
        if 90 < ego_rotation_angle < 180:
            map_rotate = 180
        if map_layer is None:
            map_crop = None
        else:
            map_crop = crop_rect(map_layer.data, rect)
            map_crop = ndimage.rotate(map_crop, map_rotate, reshape=False)
            if rotate_face_up:
                map_crop = np.rot90(map_crop)
        if map_layer is None:
            map_upper_left_offset_from_global_coordinate_origin = np.zeros((2,))
        else:
            map_upper_left_offset_from_global_coordinate_origin = np.array([-map_layer.transform_matrix[0, -1], map_layer.transform_matrix[1, -1]])
        ego_offset_from_map_upper_left: npt.NDArray[np.float32] = np.array([center_x, -center_y])
        crop_upper_left_offset_from_ego: npt.NDArray[np.float32] = np.array([xrange[0] * map_scale[0], yrange[0] * map_scale[1]])
        map_translation: npt.NDArray[np.float64] = -map_upper_left_offset_from_global_coordinate_origin - ego_offset_from_map_upper_left - crop_upper_left_offset_from_ego
        map_translation_with_z: npt.NDArray[np.float64] = np.array([map_translation[0], map_translation[1], 0])
        if target_imsize_xy is not None:
            zoom_size_x = target_imsize_xy[0] / cropped_dimensions[0]
            zoom_size_y = target_imsize_xy[1] / cropped_dimensions[1]
            map_crop = ndimage.zoom(map_crop, [zoom_size_x, zoom_size_y])
            map_scale = (zoom_size_x, zoom_size_y)
        return (map_crop, map_translation_with_z, map_scale)

    def get_vector_map(self, maps_db: Optional[GPKGMapsDB], xrange: Tuple[float, float], yrange: Tuple[float, float], connection_scales: Optional[List[int]]=None) -> VectorMapNp:
        """
        This function returns the crop of baseline paths (blps) map centered at the current ego-pose with
        the given xrange and yrange.
        :param maps_db: Map database associated with this database.
        :param xrange: The range in x direction in meters relative to the current ego-pose. Eg: [-60, 60].
        :param yrange: The range in y direction in meters relative to the current ego-pose Eg: [-60, 60].
        :param connection_scales: Connection scales to generate. Use the 1-hop connections if it's left empty.
        :return: Vector map data including lane segment coordinates and connections within the given range.
        """
        map_version = self.lidar_pc.log.map_version.replace('.gpkg', '')
        blps_gdf = maps_db.load_vector_layer(map_version, 'baseline_paths')
        lane_poly_gdf = maps_db.load_vector_layer(map_version, 'lanes_polygons')
        intersections_gdf = maps_db.load_vector_layer(map_version, 'intersections')
        lane_connectors_gdf = maps_db.load_vector_layer(map_version, 'lane_connectors')
        lane_groups_gdf = maps_db.load_vector_layer(map_version, 'lane_groups_polygons')
        if blps_gdf is None or lane_poly_gdf is None or intersections_gdf is None or (lane_connectors_gdf is None) or (lane_groups_gdf is None):
            coords: npt.NDArray[np.float32] = np.empty([0, 2, 2], dtype=np.float32)
            if not connection_scales:
                connection_scales = [1]
            multi_scale_connections: Dict[int, Any] = {scale: np.empty([0, 2], dtype=np.int64) for scale in connection_scales}
            return VectorMapNp(coords=coords, multi_scale_connections=multi_scale_connections)
        blps_in_lanes = blps_gdf[blps_gdf['lane_fid'].notna()]
        blps_in_intersections = blps_gdf[blps_gdf['lane_connector_fid'].notna()]
        lane_group_info = lane_poly_gdf[['lane_fid', 'lane_group_fid']]
        blps_in_lanes = blps_in_lanes.merge(lane_group_info, on='lane_fid', how='outer')
        lane_connectors_gdf['lane_connector_fid'] = lane_connectors_gdf['fid']
        lane_conns_info = lane_connectors_gdf[['lane_connector_fid', 'intersection_fid', 'exit_lane_fid', 'entry_lane_fid']]
        lane_conns_info = lane_conns_info.astype({'lane_connector_fid': int})
        blps_in_intersections = blps_in_intersections.astype({'lane_connector_fid': int})
        blps_in_intersections = blps_in_intersections.merge(lane_conns_info, on='lane_connector_fid', how='outer')
        lane_blps_info = blps_in_lanes[['fid', 'lane_fid']]
        from_blps_info = lane_blps_info.rename(columns={'fid': 'from_blp', 'lane_fid': 'exit_lane_fid'})
        to_blps_info = lane_blps_info.rename(columns={'fid': 'to_blp', 'lane_fid': 'entry_lane_fid'})
        blps_in_intersections = blps_in_intersections.merge(from_blps_info, on='exit_lane_fid', how='inner')
        blps_in_intersections = blps_in_intersections.merge(to_blps_info, on='entry_lane_fid', how='inner')
        candidate_lane_groups, candidate_intersections = get_candidates(self.translation_np, xrange, yrange, lane_groups_gdf, intersections_gdf)
        candidate_blps_in_lanes = blps_in_lanes[blps_in_lanes['lane_group_fid'].isin(candidate_lane_groups['fid'].astype(int))]
        candidate_blps_in_intersections = blps_in_intersections[blps_in_intersections['intersection_fid'].isin(candidate_intersections['fid'].astype(int))]
        ls_coordinates_list: List[List[List[float]]] = []
        ls_connections_list: List[List[int]] = []
        ls_groupings_list: List[List[int]] = []
        cross_blp_connection: Dict[str, List[int]] = dict()
        build_lane_segments_from_blps(candidate_blps_in_lanes, ls_coordinates_list, ls_connections_list, ls_groupings_list, cross_blp_connection)
        build_lane_segments_from_blps(candidate_blps_in_intersections, ls_coordinates_list, ls_connections_list, ls_groupings_list, cross_blp_connection)
        for blp_id, blp_info in cross_blp_connection.items():
            connect_blp_predecessor(blp_id, candidate_blps_in_intersections, cross_blp_connection, ls_connections_list)
            connect_blp_successor(blp_id, candidate_blps_in_intersections, cross_blp_connection, ls_connections_list)
        ls_coordinates: npt.NDArray[np.float64] = np.asarray(ls_coordinates_list, self.translation_np.dtype)
        ls_connections: npt.NDArray[np.int64] = np.asarray(ls_connections_list, np.int64)
        ls_coordinates = ls_coordinates.reshape(-1, 2)
        ls_coordinates = ls_coordinates - self.translation_np[:2]
        ls_coordinates = self.rotate_2d_points2d_to_ego_vehicle_frame(ls_coordinates)
        ls_coordinates = ls_coordinates.reshape(-1, 2, 2).astype(np.float32)
        if connection_scales:
            multi_scale_connections = generate_multi_scale_connections(ls_connections, connection_scales)
        else:
            multi_scale_connections = {1: ls_connections}
        return VectorMapNp(coords=ls_coordinates, multi_scale_connections=multi_scale_connections)

@property
def quaternion(self) -> Quaternion:
    """
        Get the orientation of ego vehicle as quaternion respect to global coordinate system.
        :return: The orientation in quaternion.
        """
    return Quaternion(self.qw, self.qx, self.qy, self.qz)

@property
def translation_np(self) -> npt.NDArray[np.float64]:
    """
        Position of ego vehicle respect to global coordinate system.
        :return: <np.float: 3> Translation.
        """
    return np.array([self.x, self.y, self.z])

@property
def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
    """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
    tm: npt.NDArray[np.float64] = np.eye(4)
    rot_inv = self.quaternion.rotation_matrix.T
    tm[:3, :3] = rot_inv
    tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
    return tm

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

class Lidar(Base):
    """
    Defines a calibrated lidar used to record a particular log.
    """
    __tablename__ = 'lidar'
    token = Column(sql_types.HexLen8, primary_key=True)
    log_token = Column(sql_types.HexLen8, ForeignKey('log.token'), nullable=False)
    channel = Column(String(64))
    model = Column(String(64))
    translation = Column(sql_types.SqlTranslation)
    rotation = Column(sql_types.SqlRotation)
    lidar_pcs = relationship('LidarPc', foreign_keys='LidarPc.lidar_token', back_populates='lidar')

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
    def translation_np(self) -> npt.NDArray[np.float64]:
        """
        Get the translation in numpy format.
        :return: <np.float: 3> Translation.
        """
        return np.array(self.translation)

    @property
    def quaternion(self) -> Quaternion:
        """
        Get the rotation in quaternion.
        :return: The rotation in quaternion.
        """
        return Quaternion(self.rotation)

    @property
    def trans_matrix(self) -> npt.NDArray[np.float64]:
        """
        Get the transformation matrix.
        :return: <np.float: 4, 4>. Transformation matrix.
        """
        tm: npt.NDArray[np.float64] = self.quaternion.transformation_matrix
        tm[:3, 3] = self.translation_np
        return tm

    @property
    def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
        """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
        tm: npt.NDArray[np.float64] = np.eye(4)
        rot_inv = self.quaternion.rotation_matrix.T
        tm[:3, :3] = rot_inv
        tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
        return tm

@property
def translation_np(self) -> npt.NDArray[np.float64]:
    """
        Get the translation in numpy format.
        :return: <np.float: 3> Translation.
        """
    return np.array(self.translation)

@property
def quaternion(self) -> Quaternion:
    """
        Get the rotation in quaternion.
        :return: The rotation in quaternion.
        """
    return Quaternion(self.rotation)

@property
def trans_matrix_inv(self) -> npt.NDArray[np.float64]:
    """
        Get the inverse transformation matrix.
        :return: <np.float: 4, 4>. Inverse transformation matrix.
        """
    tm: npt.NDArray[np.float64] = np.eye(4)
    rot_inv = self.quaternion.rotation_matrix.T
    tm[:3, :3] = rot_inv
    tm[:3, 3] = rot_inv.dot(np.transpose(-self.translation_np))
    return tm

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

def test_distance_to_ego(self) -> None:
    """Tests the distance_to_ego property"""
    x = self.lidar_box.x
    y = self.lidar_box.y
    x_ego = self.lidar_box.lidar_pc.ego_pose.x
    y_ego = self.lidar_box.lidar_pc.ego_pose.y
    expected_result = math.sqrt((x - x_ego) * (x - x_ego) + (y - y_ego) * (y - y_ego))
    actual_result = self.lidar_box.distance_to_ego
    self.assertEqual(expected_result, actual_result)

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

class TestLoadPointcloudFromSampledataUsingMocks(unittest.TestCase):
    """Test Loading PointCloud."""

    @unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
    def test_distance_filtering(self, prepare_pointcloud_points_mock: Mock) -> None:
        """
        Make sure close and far points are filtered properly.
        """
        prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
        mock_lidarpc_rec = Mock()
        mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[0.1, -0.1, 10, -10, 1000, 1000], [0.2, -0.2, 20, 20, 2000, -2000]]))
        nuplandb = MagicMock()
        nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
        loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=1, max_distance=1000, min_distance=1)
        expected_points = np.array([[10, -10], [20, 20], [0, 0]], dtype=np.float32)
        self.assertTrue(np.allclose(loaded_pc.points, expected_points))

    @unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
    def test_3_sweeps(self, prepare_pointcloud_points_mock: Mock) -> None:
        """
        Make sure points and timestamps accumulate properly with multiple sweeps.
        """
        prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
        mock_lidarpc_rec = Mock()
        mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100, -100], [200, 200], [300, 300]]))
        mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=np.array([[10, -10], [20, 20], [30, 30]]))
        mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1, -1], [2, 2], [3, 3]]))
        mock_lidarpc_rec.timestamp = 507
        mock_lidarpc_rec.prev.timestamp = 504
        mock_lidarpc_rec.prev.prev.timestamp = 500
        mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
        mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.prev.ego_pose.trans_matrix = np.eye(4)
        mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.eye(4)
        nuplandb = MagicMock()
        nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
        loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=3, max_distance=1000, min_distance=0)
        expected_points = np.array([[1, -1, 10, -10, 100, -100], [2, 2, 20, 20, 200, 200], [3, 3, 30, 30, 300, 300], [7e-06, 7e-06, 3e-06, 3e-06, 0, 0]], dtype=np.float32)
        self.assertTrue(np.allclose(loaded_pc.points, expected_points))

    @unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
    def test_3_sweeps_past_future(self, prepare_pointcloud_points_mock: Mock) -> None:
        """
        Make sure points and timestamps accumulate properly with multiple sweeps, using past and future data.
        """
        prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
        mock_lidarpc_rec = Mock()
        mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100, -100], [200, 200], [300, 300]]))
        mock_lidarpc_rec.next.next.load.return_value = LidarPointCloud(points=np.array([[10, -10], [20, 20], [30, 30]]))
        mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1, -1], [2, 2], [3, 3]]))
        mock_lidarpc_rec.prev.prev.timestamp = 500
        mock_lidarpc_rec.timestamp = 504
        mock_lidarpc_rec.next.next.timestamp = 507
        mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
        mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.eye(4)
        mock_lidarpc_rec.next.next.ego_pose.trans_matrix = np.eye(4)
        nuplandb = MagicMock()
        nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
        loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=[-2, 0, 2], max_distance=1000, min_distance=0)
        expected_points = np.array([[1, -1, 100, -100, 10, -10], [2, 2, 200, 200, 20, 20], [3, 3, 300, 300, 30, 30], [4e-06, 4e-06, 0, 0, -3e-06, -3e-06]], dtype=np.float32)
        self.assertTrue(np.allclose(loaded_pc.points, expected_points))

    @unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
    def test_5_sweeps_moving_vehicle(self, prepare_pointcloud_points_mock: Mock) -> None:
        """Test accumulating sweeps with moving vehicle."""
        prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
        point_111 = np.ones((3, 1), dtype=np.float32)
        mock_lidarpc_rec = Mock()
        mock_lidarpc_rec.load.return_value = LidarPointCloud(points=point_111)
        mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=point_111)
        mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=point_111)
        mock_lidarpc_rec.prev.prev.prev.load.return_value = LidarPointCloud(points=point_111)
        mock_lidarpc_rec.prev.prev.prev.prev.load.return_value = LidarPointCloud(points=point_111)
        mock_lidarpc_rec.timestamp = 504
        mock_lidarpc_rec.prev.timestamp = 503
        mock_lidarpc_rec.prev.prev.timestamp = 502
        mock_lidarpc_rec.prev.prev.prev.timestamp = 501
        mock_lidarpc_rec.prev.prev.prev.prev.timestamp = 500
        mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
        mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)

        def addition_transform(x: float, y: float, z: float) -> npt.NDArray[np.float64]:
            """
            Create a 4 by 4 transformation matrix given translation.
            :return: <np.float: 4, 4>. The transformation matrix.
            """
            return np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]], dtype=np.float32)
        mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.prev.ego_pose.trans_matrix = addition_transform(1, 2, 3)
        mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = addition_transform(2, 3, 4)
        mock_lidarpc_rec.prev.prev.prev.ego_pose.trans_matrix = addition_transform(3, 4, 5)
        mock_lidarpc_rec.prev.prev.prev.prev.ego_pose.trans_matrix = addition_transform(4, 5, 6)
        nuplandb = MagicMock()
        nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
        loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=5, max_distance=1000, min_distance=0)
        expected_points = np.array([[5, 4, 3, 2, 1], [6, 5, 4, 3, 1], [7, 6, 5, 4, 1], [4e-06, 3e-06, 2e-06, 1e-06, 0]], dtype=np.float32)
        self.assertTrue(np.allclose(loaded_pc.points, expected_points))

    @unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
    def test_coordinate_transforms(self, prepare_pointcloud_points_mock: Mock) -> None:
        """
        Make sure points and timestamps accumulate properly with multiple sweeps.
        """
        prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
        mock_lidarpc_rec = Mock()
        mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100], [200], [300]], dtype=np.float32))
        mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=np.array([[10], [20], [30]], dtype=np.float32))
        mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1], [2], [3]], dtype=np.float32))
        mock_lidarpc_rec.timestamp = 507
        mock_lidarpc_rec.prev.timestamp = 504
        mock_lidarpc_rec.prev.prev.timestamp = 500
        mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
        mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
        mock_lidarpc_rec.prev.ego_pose.trans_matrix = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
        mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
        nuplandb = MagicMock()
        nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
        loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=3, max_distance=1000, min_distance=0, sweep_map='sweep_idx')
        expected_points = np.array([[2, -20, 100], [-1, 10, 200], [3, 30, 300], [1, 2, 3]], dtype=np.float32)
        self.assertTrue(np.allclose(loaded_pc.points, expected_points))

@unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
def test_distance_filtering(self, prepare_pointcloud_points_mock: Mock) -> None:
    """
        Make sure close and far points are filtered properly.
        """
    prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
    mock_lidarpc_rec = Mock()
    mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[0.1, -0.1, 10, -10, 1000, 1000], [0.2, -0.2, 20, 20, 2000, -2000]]))
    nuplandb = MagicMock()
    nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
    loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=1, max_distance=1000, min_distance=1)
    expected_points = np.array([[10, -10], [20, 20], [0, 0]], dtype=np.float32)
    self.assertTrue(np.allclose(loaded_pc.points, expected_points))

@unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
def test_3_sweeps(self, prepare_pointcloud_points_mock: Mock) -> None:
    """
        Make sure points and timestamps accumulate properly with multiple sweeps.
        """
    prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
    mock_lidarpc_rec = Mock()
    mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100, -100], [200, 200], [300, 300]]))
    mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=np.array([[10, -10], [20, 20], [30, 30]]))
    mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1, -1], [2, 2], [3, 3]]))
    mock_lidarpc_rec.timestamp = 507
    mock_lidarpc_rec.prev.timestamp = 504
    mock_lidarpc_rec.prev.prev.timestamp = 500
    mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
    mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.prev.ego_pose.trans_matrix = np.eye(4)
    mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.eye(4)
    nuplandb = MagicMock()
    nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
    loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=3, max_distance=1000, min_distance=0)
    expected_points = np.array([[1, -1, 10, -10, 100, -100], [2, 2, 20, 20, 200, 200], [3, 3, 30, 30, 300, 300], [7e-06, 7e-06, 3e-06, 3e-06, 0, 0]], dtype=np.float32)
    self.assertTrue(np.allclose(loaded_pc.points, expected_points))

@unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
def test_3_sweeps_past_future(self, prepare_pointcloud_points_mock: Mock) -> None:
    """
        Make sure points and timestamps accumulate properly with multiple sweeps, using past and future data.
        """
    prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
    mock_lidarpc_rec = Mock()
    mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100, -100], [200, 200], [300, 300]]))
    mock_lidarpc_rec.next.next.load.return_value = LidarPointCloud(points=np.array([[10, -10], [20, 20], [30, 30]]))
    mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1, -1], [2, 2], [3, 3]]))
    mock_lidarpc_rec.prev.prev.timestamp = 500
    mock_lidarpc_rec.timestamp = 504
    mock_lidarpc_rec.next.next.timestamp = 507
    mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
    mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.eye(4)
    mock_lidarpc_rec.next.next.ego_pose.trans_matrix = np.eye(4)
    nuplandb = MagicMock()
    nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
    loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=[-2, 0, 2], max_distance=1000, min_distance=0)
    expected_points = np.array([[1, -1, 100, -100, 10, -10], [2, 2, 200, 200, 20, 20], [3, 3, 300, 300, 30, 30], [4e-06, 4e-06, 0, 0, -3e-06, -3e-06]], dtype=np.float32)
    self.assertTrue(np.allclose(loaded_pc.points, expected_points))

@unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
def test_5_sweeps_moving_vehicle(self, prepare_pointcloud_points_mock: Mock) -> None:
    """Test accumulating sweeps with moving vehicle."""
    prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
    point_111 = np.ones((3, 1), dtype=np.float32)
    mock_lidarpc_rec = Mock()
    mock_lidarpc_rec.load.return_value = LidarPointCloud(points=point_111)
    mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=point_111)
    mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=point_111)
    mock_lidarpc_rec.prev.prev.prev.load.return_value = LidarPointCloud(points=point_111)
    mock_lidarpc_rec.prev.prev.prev.prev.load.return_value = LidarPointCloud(points=point_111)
    mock_lidarpc_rec.timestamp = 504
    mock_lidarpc_rec.prev.timestamp = 503
    mock_lidarpc_rec.prev.prev.timestamp = 502
    mock_lidarpc_rec.prev.prev.prev.timestamp = 501
    mock_lidarpc_rec.prev.prev.prev.prev.timestamp = 500
    mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
    mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)

    def addition_transform(x: float, y: float, z: float) -> npt.NDArray[np.float64]:
        """
            Create a 4 by 4 transformation matrix given translation.
            :return: <np.float: 4, 4>. The transformation matrix.
            """
        return np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]], dtype=np.float32)
    mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.prev.ego_pose.trans_matrix = addition_transform(1, 2, 3)
    mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = addition_transform(2, 3, 4)
    mock_lidarpc_rec.prev.prev.prev.ego_pose.trans_matrix = addition_transform(3, 4, 5)
    mock_lidarpc_rec.prev.prev.prev.prev.ego_pose.trans_matrix = addition_transform(4, 5, 6)
    nuplandb = MagicMock()
    nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
    loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=5, max_distance=1000, min_distance=0)
    expected_points = np.array([[5, 4, 3, 2, 1], [6, 5, 4, 3, 1], [7, 6, 5, 4, 1], [4e-06, 3e-06, 2e-06, 1e-06, 0]], dtype=np.float32)
    self.assertTrue(np.allclose(loaded_pc.points, expected_points))

def addition_transform(x: float, y: float, z: float) -> npt.NDArray[np.float64]:
    """
            Create a 4 by 4 transformation matrix given translation.
            :return: <np.float: 4, 4>. The transformation matrix.
            """
    return np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]], dtype=np.float32)

@unittest.mock.patch('nuplan.database.nuplan_db_orm.utils.prepare_pointcloud_points')
def test_coordinate_transforms(self, prepare_pointcloud_points_mock: Mock) -> None:
    """
        Make sure points and timestamps accumulate properly with multiple sweeps.
        """
    prepare_pointcloud_points_mock.side_effect = mock_prepare_pointcloud_points
    mock_lidarpc_rec = Mock()
    mock_lidarpc_rec.load.return_value = LidarPointCloud(points=np.array([[100], [200], [300]], dtype=np.float32))
    mock_lidarpc_rec.prev.load.return_value = LidarPointCloud(points=np.array([[10], [20], [30]], dtype=np.float32))
    mock_lidarpc_rec.prev.prev.load.return_value = LidarPointCloud(points=np.array([[1], [2], [3]], dtype=np.float32))
    mock_lidarpc_rec.timestamp = 507
    mock_lidarpc_rec.prev.timestamp = 504
    mock_lidarpc_rec.prev.prev.timestamp = 500
    mock_lidarpc_rec.lidar.trans_matrix = np.eye(4)
    mock_lidarpc_rec.lidar.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.ego_pose.trans_matrix_inv = np.eye(4)
    mock_lidarpc_rec.prev.ego_pose.trans_matrix = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    mock_lidarpc_rec.prev.prev.ego_pose.trans_matrix = np.array([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    nuplandb = MagicMock()
    nuplandb.lidar_pc.__getitem__.return_value = mock_lidarpc_rec
    loaded_pc = load_pointcloud_from_pc(nuplandb, token='abc', nsweeps=3, max_distance=1000, min_distance=0, sweep_map='sweep_idx')
    expected_points = np.array([[2, -20, 100], [-1, 10, 200], [3, 30, 300], [1, 2, 3]], dtype=np.float32)
    self.assertTrue(np.allclose(loaded_pc.points, expected_points))

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

def quaternion_yaw(q: Quaternion) -> float:
    """
    Calculates the yaw angle from a quaternion.
    Follow convention: R = Rz(yaw)Ry(pitch)Px(roll)
    Source: https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    :param q: Quaternion of interest.
    :return: Yaw angle in radians.
    """
    a = 2.0 * (q[0] * q[3] + q[1] * q[2])
    b = 1.0 - 2.0 * (q[2] ** 2 + q[3] ** 2)
    return math.atan2(a, b)

def yaw_to_quaternion(yaw: float) -> Quaternion:
    """
    Calculate the quaternion from a yaw angle.
    :param yaw: yaw angle
    :return: Quaternion
    """
    return Quaternion(axis=(0, 0, 1), radians=yaw)

def transform_matrix(translation: npt.NDArray[np.float64]=np.array([0, 0, 0]), rotation: Quaternion=Quaternion([1, 0, 0, 0]), inverse: bool=False) -> npt.NDArray[np.float64]:
    """
    Converts pose to transform matrix.
    :param translation: <np.float32: 3>. Translation in x, y, z.
    :param rotation: Rotation in quaternions (w, ri, rj, rk).
    :param inverse: Whether to compute inverse transform matrix.
    :return: <np.float32: 4, 4>. Transformation matrix.
    """
    tm = np.eye(4)
    if inverse:
        rot_inv = rotation.rotation_matrix.T
        trans = np.transpose(-np.array(translation))
        tm[:3, :3] = rot_inv
        tm[:3, 3] = rot_inv.dot(trans)
    else:
        tm[:3, :3] = rotation.rotation_matrix
        tm[:3, 3] = np.transpose(np.array(translation))
    return tm

def view_points(points: npt.NDArray[np.float64], view: npt.NDArray[np.float64], normalize: bool) -> npt.NDArray[np.float64]:
    """
    This is a helper class that maps 3d points to a 2d plane. It can be used to implement both perspective and
    orthographic projections. It first applies the dot product between the points and the view. By convention,
    the view should be such that the data is projected onto the first 2 axis. It then optionally applies a
    normalization along the third dimension.

    For a perspective projection the view should be a 3x3 camera matrix, and normalize=True
    For an orthographic projection with translation the view is a 3x4 matrix and normalize=False
    For an orthographic projection without translation the view is a 3x3 matrix (optionally 3x4 with last columns
     all zeros) and normalize=False

    :param points: <np.float32: 3, n> Matrix of points, where each point (x, y, z) is along each column.
    :param view: <np.float32: n, n>. Defines an arbitrary projection (n <= 4).
        The projection should be such that the corners are projected onto the first 2 axis.
    :param normalize: Whether to normalize the remaining coordinate (along the third axis).
    :return: <np.float32: 3, n>. Mapped point. If normalize=False, the third coordinate is the height.
    """
    assert view.shape[0] <= 4
    assert view.shape[1] <= 4
    assert points.shape[0] == 3
    viewpad = np.eye(4)
    viewpad[:view.shape[0], :view.shape[1]] = view
    nbr_points = points.shape[1]
    points = np.concatenate((points, np.ones((1, nbr_points))))
    points = np.dot(viewpad, points)
    points = points[:3, :]
    if normalize:
        points = points / points[2:3, :].repeat(3, 0).reshape(3, nbr_points)
    return points

def birdview_corner_angle_mean_distance_box(a: Box3D, b: Box3D, period: float) -> float:
    """
    Calculates ad-hoc birdview distance of two Box3D instances.
    :param a: Box3D 1.
    :param b: Box3D 2.
    :param period: Periodicity for assessing angle difference.
    :return: Birdview distance.
    """
    error = 0.0
    error += abs(a.center[0] - b.center[0])
    error += abs(a.center[1] - b.center[1])
    error += abs(a.wlh[0] - b.wlh[0])
    error += abs(a.wlh[1] - b.wlh[1])
    a_yaw = quaternion_yaw(a.orientation)
    b_yaw = quaternion_yaw(b.orientation)
    error += abs(angle_diff(a_yaw, b_yaw, period))
    return error / 5

def birdview_pseudo_iou_box(a: Box3D, b: Box3D, period: float) -> float:
    """
    Calculates ad-hoc birdview IoU of two Box3D instances.
    :param a: Box3D 1.
    :param b: Box3D 2.
    :param period: Periodicity for assessing angle difference.
    :return: Birdview IoU.
    """
    return 1 / (1 + birdview_corner_angle_mean_distance_box(a, b, period))

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

def birdview_center_distance_box(a: Box3D, b: Box3D) -> float:
    """
    Calculates the l2 distance between birdsview bounding box centers in Box3D class format.
    :param a: Box3D class.
    :param b: Box3D class.
    :return: Center distance.
    """
    return float(np.sqrt((a.center[0] - b.center[0]) ** 2 + (a.center[1] - b.center[1]) ** 2))

def birdview_center_distance(a: Union[Tuple[float, float], TwoDimBox], b: Union[Tuple[float, float], TwoDimBox]) -> float:
    """
    Calculates the l2 distance between birdsview bounding box centers.
    :param a: (xcenter, ycenter). Also accepts longer representation including width, height, yaw.
    :param b: (xcenter, ycenter). Also accepts longer representation including width, height, yaw.
    :return: Center distance.
    """
    return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

def long_lat_dist_decomposition(gt_vector: npt.NDArray[np.float64], est_vector: npt.NDArray[np.float64]) -> Tuple[float, float]:
    """
    Longitudinal and lateral decomposition of est_vector - gt_vector.
    We define longitudinal direction as the direction of gt_vector. Lateral direction is defined as direction of
    cross product between longitudinal vector and vertical vector (longitudinal x vertical).
    :param gt_vector: <np.float: 2>. 2-dimensional ground truth vector.
    :param est_vector: <np.float: 2>. 2-dimensional ground estimated vector.
    :return: Longitudinal distance and lateral distance.
    """
    assert gt_vector.size == est_vector.size == 2, 'Input vector should be 2-dimensional'
    if np.all(gt_vector == 0):
        return (np.linalg.norm(est_vector), 0)
    unit_long_vector = gt_vector / np.linalg.norm(gt_vector)
    dist_vector: npt.NDArray[np.float64] = est_vector - gt_vector
    long_dist = float(np.dot(unit_long_vector, dist_vector))
    lat_dist = np.linalg.norm(dist_vector - long_dist * unit_long_vector)
    return (long_dist, lat_dist)

def get_euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Gets the straight line distance between two points (generally used for finding the distance between two UTM
    coordinates).
    :param x1: The x-coordinate of the first point.
    :param y1: The y-coordinate of the first point.
    :param x2: The x-coordinate of the second point.
    :param y2: The y-coordinate of the second point.
    :return: The straight line distance between (x1, y1) and (x2, y2).
    """
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx * dx + dy * dy)

class Image:
    """
    A class to represent an image. This class is an analogue to LidarPointCloud. It is a class for manipulating and
    transforming an image. Any transformation functions (flip, scale, translate) should be added to this class in the
    future.
    """

    def __init__(self, image: PilImage.Image) -> None:
        """
        Constructor for the Image class.
        :param image: An image of type PIL.Image.Image.
        """
        self._image = image

    @property
    def as_pil(self) -> PilImage.Image:
        """
        Returns the image of type PIL.Image.Image in uint8, RGB format.
        :return: An image of type PIL.Image.Image.
        """
        return self._image

    @cached_property
    def as_numpy(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a numpy array in uint8, RGB format.
        :return: An image as a numpy array.
        """
        return self.as_numpy_nocache()

    def as_numpy_nocache(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a numpy array in uint8, RGB format. A non caching variation to save on memory if needed.
        :return: An image as a numpy array.
        """
        return np.array(self._image, dtype=np.uint8)

    @cached_property
    def as_cv2(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood.
        This function is a convenience for to be used with cv2.imshow().
        :return: An image as a CV2 image.
        """
        return self.as_cv2_nocache()

    def as_cv2_nocache(self) -> npt.NDArray[np.uint8]:
        """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood. This function
        is a convenience for to be used with cv2.imshow(). A non caching variation to save on memory if needed.
        :return: An image as a CV2 image.
        """
        return cast(npt.NDArray[np.uint8], cv2.cvtColor(np.array(self._image, dtype=np.uint8), cv2.COLOR_RGB2BGR))

    @classmethod
    def from_buffer(cls, blob: BinaryIO) -> Image:
        """
        Instantiates Image from buffer.
        :param blob: Data to load.
        :return: An Image object.
        """
        return cls(PilImage.open(blob))

def as_numpy_nocache(self) -> npt.NDArray[np.uint8]:
    """
        Returns the image as a numpy array in uint8, RGB format. A non caching variation to save on memory if needed.
        :return: An image as a numpy array.
        """
    return np.array(self._image, dtype=np.uint8)

def as_cv2_nocache(self) -> npt.NDArray[np.uint8]:
    """
        Returns the image as a CV2 image in uint8, BGR format. It is a numpy array under the hood. This function
        is a convenience for to be used with cv2.imshow(). A non caching variation to save on memory if needed.
        :return: An image as a CV2 image.
        """
    return cast(npt.NDArray[np.uint8], cv2.cvtColor(np.array(self._image, dtype=np.uint8), cv2.COLOR_RGB2BGR))

def points_in_box_bev(box: Box3D, points: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Checks whether points are inside the box in birds eyed view.
    :param box: Box3D instance.
    :param points: Trajectory given as <np.float: 3, n_way_points)
    :return: A boolean mask whether points are in the box in BEV world.
    """
    box = box.copy()
    points = points.copy()
    points[2, :] = box.center[2]
    return points_in_box(box, points)

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

@width.setter
def width(self, width: float) -> None:
    """Implemented. See interface."""
    self.wlh[0] = width

@length.setter
def length(self, length: float) -> None:
    """Implemented. See interface."""
    self.wlh[1] = length

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

def qyaw(yaw: float) -> Quaternion:
    """
            Return a Quaternion given yaw angle.
            :param yaw: Yaw angle.
            :return: A Quaternion object.
            """
    return Quaternion(axis=(0, 0, 1), angle=yaw)

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

class TestAngleDiff(unittest.TestCase):
    """Unittests for angle difference."""

    def test_angle_diff_2pi(self) -> None:
        """Tests angle diff function for 2 pi."""
        period = 2 * math.pi
        x, y = (math.pi, math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
        x, y = (math.pi, -math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
        x, y = (-math.pi / 6, math.pi / 6)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi / 3)
        x, y = (2 * math.pi / 3, -2 * math.pi / 3)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), -2 * math.pi / 3)
        x, y = (8 * math.pi / 3, -2 * math.pi / 3)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), -2 * math.pi / 3)
        x, y = (0, math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi)

    def test_angle_diff_pi(self) -> None:
        """Tests angle diff function for pi."""
        period = math.pi
        x, y = (math.pi, math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
        x, y = (math.pi, -math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
        x, y = (-math.pi / 6, math.pi / 6)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi / 3)
        x, y = (2 * math.pi / 3, -2 * math.pi / 3)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), math.pi / 3)
        x, y = (8 * math.pi / 3, -2 * math.pi / 3)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), math.pi / 3)
        x, y = (0, math.pi)
        self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)

    def test_quaternion(self) -> None:
        """Tests the angle difference between two yaw angles from two quaternions."""
        x = quaternion_yaw(Quaternion(axis=(0, 0, 1), angle=1.1 * np.pi))
        y = quaternion_yaw(Quaternion(axis=(0, 0, 1), angle=0.9 * np.pi))
        diff = measure.angle_diff(x, y, period=2 * np.pi)
        self.assertAlmostEqual(diff, 0.2 * np.pi)

def test_angle_diff_2pi(self) -> None:
    """Tests angle diff function for 2 pi."""
    period = 2 * math.pi
    x, y = (math.pi, math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
    x, y = (math.pi, -math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
    x, y = (-math.pi / 6, math.pi / 6)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi / 3)
    x, y = (2 * math.pi / 3, -2 * math.pi / 3)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), -2 * math.pi / 3)
    x, y = (8 * math.pi / 3, -2 * math.pi / 3)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), -2 * math.pi / 3)
    x, y = (0, math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi)

def test_angle_diff_pi(self) -> None:
    """Tests angle diff function for pi."""
    period = math.pi
    x, y = (math.pi, math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
    x, y = (math.pi, -math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)
    x, y = (-math.pi / 6, math.pi / 6)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), -math.pi / 3)
    x, y = (2 * math.pi / 3, -2 * math.pi / 3)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), math.pi / 3)
    x, y = (8 * math.pi / 3, -2 * math.pi / 3)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), math.pi / 3)
    x, y = (0, math.pi)
    self.assertAlmostEqual(measure.angle_diff(x, y, period), 0)

def test_quaternion(self) -> None:
    """Tests the angle difference between two yaw angles from two quaternions."""
    x = quaternion_yaw(Quaternion(axis=(0, 0, 1), angle=1.1 * np.pi))
    y = quaternion_yaw(Quaternion(axis=(0, 0, 1), angle=0.9 * np.pi))
    diff = measure.angle_diff(x, y, period=2 * np.pi)
    self.assertAlmostEqual(diff, 0.2 * np.pi)

class TestBirdviewCenterDistanceBox(unittest.TestCase):
    """Unit test for birdview center distance."""

    def test_birdview_center_distance(self) -> None:
        """Test the l2 distance between birdview bounding box centers."""
        dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (0.0, 0.0, 1.0, 1.0, 0.0))
        self.assertEqual(dist, 0)
        dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 0.0, 1.0, 1.0, 0.0))
        self.assertEqual(dist, 1)
        dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 1.0, 0.0))
        self.assertAlmostEqual(dist, 1.4142135623730951)

    def test_birdview_center_distance_box(self) -> None:
        """Test the l2 distance between birdview bounding box centers in Box3D class format."""
        dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
        self.assertEqual(dist, 0)
        dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
        self.assertEqual(dist, 1)
        dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 1, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
        self.assertAlmostEqual(dist, 1.4142135623730951)
        dist1 = measure.birdview_center_distance_box(Box3D((4, 5, 0), (2, 2, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 4, 0), (2, 4, 1), Quaternion(axis=(0, 0, 1), angle=np.pi / 3)))
        dist2 = measure.birdview_center_distance((4.0, 5.0, 2.0, 2.0, 0.0), (1.0, 4.0, 2.0, 4.0, np.pi / 3.0))
        self.assertEqual(dist1, dist2)

def test_birdview_center_distance(self) -> None:
    """Test the l2 distance between birdview bounding box centers."""
    dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (0.0, 0.0, 1.0, 1.0, 0.0))
    self.assertEqual(dist, 0)
    dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 0.0, 1.0, 1.0, 0.0))
    self.assertEqual(dist, 1)
    dist = measure.birdview_center_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 1.0, 0.0))
    self.assertAlmostEqual(dist, 1.4142135623730951)

def test_birdview_center_distance_box(self) -> None:
    """Test the l2 distance between birdview bounding box centers in Box3D class format."""
    dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
    self.assertEqual(dist, 0)
    dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
    self.assertEqual(dist, 1)
    dist = measure.birdview_center_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 1, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
    self.assertAlmostEqual(dist, 1.4142135623730951)
    dist1 = measure.birdview_center_distance_box(Box3D((4, 5, 0), (2, 2, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 4, 0), (2, 4, 1), Quaternion(axis=(0, 0, 1), angle=np.pi / 3)))
    dist2 = measure.birdview_center_distance((4.0, 5.0, 2.0, 2.0, 0.0), (1.0, 4.0, 2.0, 4.0, np.pi / 3.0))
    self.assertEqual(dist1, dist2)

class TestHausdorffDistance(unittest.TestCase):
    """Unit test for hausdorff_distance"""

    def test_hausdorff_distance(self) -> None:
        """Test Hausdorff distance between two 2d-boxes"""
        dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (0.0, 0.0, 1.0, 1.0, 0.0))
        self.assertEqual(dist, 0)
        dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 0.0, 1.0, 1.0, 0.0))
        self.assertEqual(dist, 1.0)
        dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 1.0, 0.0))
        self.assertAlmostEqual(dist, 1.4142135623730951)
        dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 1.0, 1.0, 2.0, np.pi / 2.0))
        self.assertAlmostEqual(dist, 0.5)
        dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 1.5, 1.0, 2.0, 0.0))
        self.assertAlmostEqual(dist, 0.5)
        dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 2.0, 2.0, 4.0, 0.0))
        self.assertAlmostEqual(dist, np.sqrt(0.5 ** 2 + 2 ** 2))
        dist = measure.hausdorff_distance((0.0, 0.0, 2.0 / np.sqrt(2.0), 2.0 / np.sqrt(2.0), 0.0), (0.0, 1.0 / np.sqrt(2.0), 1.0, 1.0, np.pi / 4.0))
        self.assertAlmostEqual(dist, 1)

    def test_hausdorff_distance_box(self) -> None:
        """Test Hausdorff distance between two 2d-boxes in Box3D class."""
        dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((0, 0, 0), (1, 1, 10), Quaternion(0, 0, 0, 0)))
        self.assertEqual(dist, 0)
        dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
        self.assertEqual(dist, 1.0)
        dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 1, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
        self.assertAlmostEqual(dist, 1.4142135623730951)
        dist1 = measure.hausdorff_distance_box(Box3D((4, 5, 0), (2, 2, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 4, 0), (2, 4, 1), Quaternion(axis=(0, 0, 1), angle=np.pi / 3)))
        dist2 = measure.hausdorff_distance((4.0, 5.0, 2.0, 2.0, 0.0), (1.0, 4.0, 2.0, 4.0, np.pi / 3.0))
        self.assertEqual(dist1, dist2)

def test_hausdorff_distance(self) -> None:
    """Test Hausdorff distance between two 2d-boxes"""
    dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (0.0, 0.0, 1.0, 1.0, 0.0))
    self.assertEqual(dist, 0)
    dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 0.0, 1.0, 1.0, 0.0))
    self.assertEqual(dist, 1.0)
    dist = measure.hausdorff_distance((0.0, 0.0, 1.0, 1.0, 0.0), (1.0, 1.0, 1.0, 1.0, 0.0))
    self.assertAlmostEqual(dist, 1.4142135623730951)
    dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 1.0, 1.0, 2.0, np.pi / 2.0))
    self.assertAlmostEqual(dist, 0.5)
    dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 1.5, 1.0, 2.0, 0.0))
    self.assertAlmostEqual(dist, 0.5)
    dist = measure.hausdorff_distance((1.0, 1.0, 1.0, 2.0, 0.0), (1.0, 2.0, 2.0, 4.0, 0.0))
    self.assertAlmostEqual(dist, np.sqrt(0.5 ** 2 + 2 ** 2))
    dist = measure.hausdorff_distance((0.0, 0.0, 2.0 / np.sqrt(2.0), 2.0 / np.sqrt(2.0), 0.0), (0.0, 1.0 / np.sqrt(2.0), 1.0, 1.0, np.pi / 4.0))
    self.assertAlmostEqual(dist, 1)

def test_hausdorff_distance_box(self) -> None:
    """Test Hausdorff distance between two 2d-boxes in Box3D class."""
    dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((0, 0, 0), (1, 1, 10), Quaternion(0, 0, 0, 0)))
    self.assertEqual(dist, 0)
    dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
    self.assertEqual(dist, 1.0)
    dist = measure.hausdorff_distance_box(Box3D((0, 0, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 1, 0), (1, 1, 1), Quaternion(0, 0, 0, 0)))
    self.assertAlmostEqual(dist, 1.4142135623730951)
    dist1 = measure.hausdorff_distance_box(Box3D((4, 5, 0), (2, 2, 1), Quaternion(0, 0, 0, 0)), Box3D((1, 4, 0), (2, 4, 1), Quaternion(axis=(0, 0, 1), angle=np.pi / 3)))
    dist2 = measure.hausdorff_distance((4.0, 5.0, 2.0, 2.0, 0.0), (1.0, 4.0, 2.0, 4.0, np.pi / 3.0))
    self.assertEqual(dist1, dist2)

class TestPseudoIOU(unittest.TestCase):
    """Test the birdview_pseudo_iou metric."""

    def test_pseudo_distance_2pi(self) -> None:
        """Test ad-hoc birdview distance of two 2-d boxes with period of 2 pi."""
        period = 2 * np.pi
        a = (0.0, 0.0, 1.0, 2.0, 0.0)
        b = (0.0, 0.0, 1.0, 2.0, 0.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
        a = (0.0, 0.0, 1.0, 2.0, 0.0)
        b = (0.0, 0.0, 1.0, 2.0, 2.0 * math.pi)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
        a = (-10.0, 10.0, 0.1, 20.0, 0.0)
        b = (-10.0, 10.0, 0.1, 20.0, math.pi / 2.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 2 / 5)
        a = (-10, 10, 0.1, 20, 0)
        b = (-10, 10, 0.1, 20, math.pi)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 5)
        a = (-100.0, -100.0, 100.0, 100.0, 0.0)
        b = (0.0, 0.0, 1.0, 1.0, 0.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 398 / 5)
        a = (-100.0, -100.0, 100.0, 100.0, 0.0)
        b = (0.0, 0.0, 1.0, 1.0, math.pi / 2.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), (398 + math.pi / 2) / 5)

    def test_pseudo_distance_pi(self) -> None:
        """Test ad-hoc birdview distance of two 2-d boxes with period of pi."""
        period = np.pi
        a = (0.0, 0.0, 1.0, 2.0, 0.0)
        b = (0.0, 0.0, 1.0, 2.0, 0.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
        a = (0.0, 0.0, 1.0, 2.0, 0.0)
        b = (0.0, 0.0, 1.0, 2.0, 2.0 * math.pi)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
        a = (-10.0, 10.0, 0.1, 20.0, 0.0)
        b = (-10.0, 10.0, 0.1, 20.0, math.pi / 2.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 2 / 5)
        a = (-10.0, 10.0, 0.1, 20.0, 0.0)
        b = (-10.0, 10.0, 0.1, 20.0, math.pi)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
        a = (-100.0, -100.0, 100.0, 100.0, 0.0)
        b = (0.0, 0.0, 1.0, 1.0, 0.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 398 / 5)
        a = (-100.0, -100.0, 100.0, 100.0, 0.0)
        b = (0.0, 0.0, 1.0, 1.0, math.pi / 2.0)
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), (398 + math.pi / 2) / 5)

    def test_pseudo_distance_box_pi(self) -> None:
        """Unit test for calculating ad-hoc birdview distance of two Box3D instances with period of pi."""
        period = np.pi
        a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
        a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=2 * math.pi))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
        a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 2 / 5)
        a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
        a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 398 / 5)
        a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), (398 + math.pi / 2) / 5)

    def test_pseudo_distance_box_2pi(self) -> None:
        """Unit test for calculating ad-hoc birdview distance of two Box3D instances with period of 2 * pi."""
        period = 2 * np.pi
        a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
        a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=2 * math.pi))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
        a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 2 / 5)
        a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 5)
        a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 398 / 5)
        a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
        b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
        self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), (398 + math.pi / 2) / 5)

def test_pseudo_distance_2pi(self) -> None:
    """Test ad-hoc birdview distance of two 2-d boxes with period of 2 pi."""
    period = 2 * np.pi
    a = (0.0, 0.0, 1.0, 2.0, 0.0)
    b = (0.0, 0.0, 1.0, 2.0, 0.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
    a = (0.0, 0.0, 1.0, 2.0, 0.0)
    b = (0.0, 0.0, 1.0, 2.0, 2.0 * math.pi)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
    a = (-10.0, 10.0, 0.1, 20.0, 0.0)
    b = (-10.0, 10.0, 0.1, 20.0, math.pi / 2.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 2 / 5)
    a = (-10, 10, 0.1, 20, 0)
    b = (-10, 10, 0.1, 20, math.pi)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 5)
    a = (-100.0, -100.0, 100.0, 100.0, 0.0)
    b = (0.0, 0.0, 1.0, 1.0, 0.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 398 / 5)
    a = (-100.0, -100.0, 100.0, 100.0, 0.0)
    b = (0.0, 0.0, 1.0, 1.0, math.pi / 2.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), (398 + math.pi / 2) / 5)

def test_pseudo_distance_pi(self) -> None:
    """Test ad-hoc birdview distance of two 2-d boxes with period of pi."""
    period = np.pi
    a = (0.0, 0.0, 1.0, 2.0, 0.0)
    b = (0.0, 0.0, 1.0, 2.0, 0.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
    a = (0.0, 0.0, 1.0, 2.0, 0.0)
    b = (0.0, 0.0, 1.0, 2.0, 2.0 * math.pi)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
    a = (-10.0, 10.0, 0.1, 20.0, 0.0)
    b = (-10.0, 10.0, 0.1, 20.0, math.pi / 2.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), math.pi / 2 / 5)
    a = (-10.0, 10.0, 0.1, 20.0, 0.0)
    b = (-10.0, 10.0, 0.1, 20.0, math.pi)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 0)
    a = (-100.0, -100.0, 100.0, 100.0, 0.0)
    b = (0.0, 0.0, 1.0, 1.0, 0.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), 398 / 5)
    a = (-100.0, -100.0, 100.0, 100.0, 0.0)
    b = (0.0, 0.0, 1.0, 1.0, math.pi / 2.0)
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance(a, b, period=period), (398 + math.pi / 2) / 5)

def test_pseudo_distance_box_pi(self) -> None:
    """Unit test for calculating ad-hoc birdview distance of two Box3D instances with period of pi."""
    period = np.pi
    a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
    a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=2 * math.pi))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
    a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 2 / 5)
    a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
    a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 398 / 5)
    a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), (398 + math.pi / 2) / 5)

def test_pseudo_distance_box_2pi(self) -> None:
    """Unit test for calculating ad-hoc birdview distance of two Box3D instances with period of 2 * pi."""
    period = 2 * np.pi
    a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
    a = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 2, 1), orientation=Quaternion(axis=[0, 0, 1], angle=2 * math.pi))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 0)
    a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 2 / 5)
    a = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(-10, 10, 0), size=(0.1, 20, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), math.pi / 5)
    a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), 398 / 5)
    a = Box3D(center=(-100, -100, 0), size=(100, 100, 1), orientation=Quaternion(axis=[0, 0, 1], angle=0))
    b = Box3D(center=(0, 0, 0), size=(1, 1, 1), orientation=Quaternion(axis=[0, 0, 1], angle=math.pi / 2))
    self.assertAlmostEqual(measure.birdview_corner_angle_mean_distance_box(a, b, period=period), (398 + math.pi / 2) / 5)

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

def distance_fcn(a: Any, b: Any) -> float:
    """
            Distance function.
            :param a: Input a.
            :param b: Input b.
            :return: distance between input.
            """
    return float(np.abs(a - b))

class TestLongLatDecomp(unittest.TestCase):
    """Test long_lat_dist_decomposition."""

    def test_euclidean(self) -> None:
        """
        Test if distance between gt and est is correctly decomposed as longitudinal and lateral components.
        This tests only checks the magnitude of both components.
        """
        for _ in range(5):
            gt: npt.NDArray[np.float64] = np.random.rand(2) * np.random.randint(10)
            est: npt.NDArray[np.float64] = np.random.rand(2) * np.random.randint(10)
            long, lat = measure.long_lat_dist_decomposition(gt, est)
            dist1 = np.linalg.norm([long, lat])
            dist2 = np.linalg.norm(gt - est)
            self.assertTrue(np.allclose(dist1, dist2))

    def test_trivial(self) -> None:
        """Test for two identical vectors."""
        gt = np.array([1, 1])
        est = np.array([1, 1])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (0, 0)))

    def test_zero(self) -> None:
        """Test for two zero vectors."""
        gt = np.array([0, 0])
        est = np.array([0, 0])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (0, 0)))

    def test_gt_x_axis(self) -> None:
        """Test for simple cases where gt_vector is on x axis."""
        gt = np.array([1, 0])
        est = np.array([0, 1])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (-1, 1)))
        gt = np.array([1, 0])
        est = np.array([1, 1])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (0, 1)))
        gt = np.array([1, 0])
        est = np.array([3, 4])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (2, 4)))

    def test_negative(self) -> None:
        """Test when both gt and est are in negative directions."""
        gt = np.array([-1, -1])
        est = np.array([-2, -2])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (np.sqrt(2), 0)))
        gt = np.array([-1, -1])
        est = np.array([-1, 0])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(long_lat, (1 / np.sqrt(2), 1 / np.sqrt(2)))

    def test_edge_case(self) -> None:
        """Test some edge cases."""
        gt = np.array([1, 1])
        est = np.array([2, 2])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (np.sqrt(2), 0)))
        gt = np.array([-1, -1])
        est = np.array([1, 1])
        long_lat = measure.long_lat_dist_decomposition(gt, est)
        self.assertTrue(np.allclose(long_lat, (-np.sqrt(8), 0)))

def test_euclidean(self) -> None:
    """
        Test if distance between gt and est is correctly decomposed as longitudinal and lateral components.
        This tests only checks the magnitude of both components.
        """
    for _ in range(5):
        gt: npt.NDArray[np.float64] = np.random.rand(2) * np.random.randint(10)
        est: npt.NDArray[np.float64] = np.random.rand(2) * np.random.randint(10)
        long, lat = measure.long_lat_dist_decomposition(gt, est)
        dist1 = np.linalg.norm([long, lat])
        dist2 = np.linalg.norm(gt - est)
        self.assertTrue(np.allclose(dist1, dist2))

def test_trivial(self) -> None:
    """Test for two identical vectors."""
    gt = np.array([1, 1])
    est = np.array([1, 1])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (0, 0)))

def test_zero(self) -> None:
    """Test for two zero vectors."""
    gt = np.array([0, 0])
    est = np.array([0, 0])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (0, 0)))

def test_gt_x_axis(self) -> None:
    """Test for simple cases where gt_vector is on x axis."""
    gt = np.array([1, 0])
    est = np.array([0, 1])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (-1, 1)))
    gt = np.array([1, 0])
    est = np.array([1, 1])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (0, 1)))
    gt = np.array([1, 0])
    est = np.array([3, 4])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (2, 4)))

def test_negative(self) -> None:
    """Test when both gt and est are in negative directions."""
    gt = np.array([-1, -1])
    est = np.array([-2, -2])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (np.sqrt(2), 0)))
    gt = np.array([-1, -1])
    est = np.array([-1, 0])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(long_lat, (1 / np.sqrt(2), 1 / np.sqrt(2)))

def test_edge_case(self) -> None:
    """Test some edge cases."""
    gt = np.array([1, 1])
    est = np.array([2, 2])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (np.sqrt(2), 0)))
    gt = np.array([-1, -1])
    est = np.array([1, 1])
    long_lat = measure.long_lat_dist_decomposition(gt, est)
    self.assertTrue(np.allclose(long_lat, (-np.sqrt(8), 0)))

class TestBuildColorMask(unittest.TestCase):
    """Test build color mask function."""

    def test_build_color_mask(self) -> None:
        """Check if correct color mask is built."""
        colors = {0: (0, 0, 0, 0), 1: (128, 20, 20, 10), 2: (255, 100, 100, 255)}
        test_array = np.array([[0, 1], [2, 2]])
        target_mask = np.array([[[0, 0, 0, 0], [128, 20, 20, 10]], [[255, 100, 100, 255], [255, 100, 100, 255]]])
        color_mask = build_color_mask(test_array, colors)
        self.assertEqual(np.array_equal(color_mask, target_mask), True)

    def test_build_color_mask_invalid_key(self) -> None:
        """Check if build_color_mask throws a KeyError exception for invalid keys."""
        colors = {100: (0, 0, 0, 0), 1: (128, 20, 20, 10), 2: (255, 100, 100, 255)}
        test_array = np.array([[0, 1], [2, 2]])
        with self.assertRaises(KeyError):
            build_color_mask(test_array, colors)

def test_build_color_mask(self) -> None:
    """Check if correct color mask is built."""
    colors = {0: (0, 0, 0, 0), 1: (128, 20, 20, 10), 2: (255, 100, 100, 255)}
    test_array = np.array([[0, 1], [2, 2]])
    target_mask = np.array([[[0, 0, 0, 0], [128, 20, 20, 10]], [[255, 100, 100, 255], [255, 100, 100, 255]]])
    color_mask = build_color_mask(test_array, colors)
    self.assertEqual(np.array_equal(color_mask, target_mask), True)

def test_build_color_mask_invalid_key(self) -> None:
    """Check if build_color_mask throws a KeyError exception for invalid keys."""
    colors = {100: (0, 0, 0, 0), 1: (128, 20, 20, 10), 2: (255, 100, 100, 255)}
    test_array = np.array([[0, 1], [2, 2]])
    with self.assertRaises(KeyError):
        build_color_mask(test_array, colors)

class TestTransformMatrix(unittest.TestCase):
    """Test TransformMatrix."""

    def test_transform_matrix(self) -> None:
        """Test transform matrix using translation and rotation."""
        zero_rotation = Quaternion(axis=(0.0, 0.0, 1.0), angle=0.0)
        for _ in range(100):
            x_trans = random.uniform(-100.0, 100.0)
            y_trans = random.uniform(-100.0, 100.0)
            z_trans = random.uniform(-100.0, 100.0)
            translation = np.array([x_trans, y_trans, z_trans])
            tm = transform_matrix(translation, zero_rotation, False)
            tm_test = np.eye(4)
            tm_test[0:3, 3] = translation
            assert_array_almost_equal(tm, tm_test)
        zero_translation = np.array([0.0, 0.0, 0.0])
        x_axis = (1.0, 0.0, 0.0)
        y_axis = (0.0, 1.0, 0.0)
        z_axis = (0.0, 0.0, 1.0)
        for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
            for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
                rotation = Quaternion(axis=axis, angle=theta)
                tm = transform_matrix(zero_translation, rotation, False)
                tm_test = np.eye(4)
                tm_test[(axis_idx + 1) % 3, (axis_idx + 1) % 3] = np.cos(theta)
                tm_test[(axis_idx + 1) % 3, (axis_idx + 2) % 3] = -np.sin(theta)
                tm_test[(axis_idx + 2) % 3, (axis_idx + 1) % 3] = np.sin(theta)
                tm_test[(axis_idx + 2) % 3, (axis_idx + 2) % 3] = np.cos(theta)
                assert_array_almost_equal(tm, tm_test)
        x_axis = (1.0, 0.0, 0.0)
        y_axis = (0.0, 1.0, 0.0)
        z_axis = (0.0, 0.0, 1.0)
        for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
            for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
                x_trans = random.uniform(-100.0, 100.0)
                y_trans = random.uniform(-100.0, 100.0)
                z_trans = random.uniform(-100.0, 100.0)
                translation = np.array([x_trans, y_trans, z_trans])
                rotation = Quaternion(axis=axis, angle=theta)
                tm = transform_matrix(translation, rotation, False)
                tm_test = np.eye(4)
                tm_test[(axis_idx + 1) % 3, (axis_idx + 1) % 3] = np.cos(theta)
                tm_test[(axis_idx + 1) % 3, (axis_idx + 2) % 3] = -np.sin(theta)
                tm_test[(axis_idx + 2) % 3, (axis_idx + 1) % 3] = np.sin(theta)
                tm_test[(axis_idx + 2) % 3, (axis_idx + 2) % 3] = np.cos(theta)
                tm_test[0:3, 3] = translation
                assert_array_almost_equal(tm, tm_test)
        x_axis = (1.0, 0.0, 0.0)
        y_axis = (0.0, 1.0, 0.0)
        z_axis = (0.0, 0.0, 1.0)
        for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
            for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
                x_trans = random.uniform(-100.0, 100.0)
                y_trans = random.uniform(-100.0, 100.0)
                z_trans = random.uniform(-100.0, 100.0)
                translation = np.array([x_trans, y_trans, z_trans])
                rotation = Quaternion(axis=axis, angle=theta)
                tm = transform_matrix(translation, rotation, False)
                inverse_tm = transform_matrix(translation, rotation, True)
                assert_array_almost_equal(inverse_tm, np.linalg.inv(tm))
        zero_rotation = Quaternion(axis=(0.0, 0.0, 1.0), angle=0.0)
        for _ in range(100):
            x_trans1 = random.uniform(-100.0, 100.0)
            y_trans1 = random.uniform(-100.0, 100.0)
            z_trans1 = random.uniform(-100.0, 100.0)
            translation1 = np.array([x_trans1, y_trans1, z_trans1])
            tm1 = transform_matrix(translation1, zero_rotation, False)
            x_trans2 = random.uniform(-100.0, 100.0)
            y_trans2 = random.uniform(-100.0, 100.0)
            z_trans2 = random.uniform(-100.0, 100.0)
            translation2 = np.array([x_trans2, y_trans2, z_trans2])
            tm2 = transform_matrix(translation2, zero_rotation, False)
            assert_array_almost_equal(tm1 * tm2, tm2 * tm1)
        zero_translation = np.array([0.0, 0.0, 0.0])
        x_axis = (1.0, 0.0, 0.0)
        y_axis = (0.0, 1.0, 0.0)
        z_axis = (0.0, 0.0, 1.0)
        for _ in range(100):
            axis1 = random.choice([x_axis, y_axis, z_axis])
            theta1 = random.uniform(-4.0 * np.pi, 4.0 * np.pi)
            rotation1 = Quaternion(axis=axis1, angle=theta1)
            tm1 = transform_matrix(zero_translation, rotation1, False)
            axis2 = random.choice([x_axis, y_axis, z_axis])
            theta2 = random.uniform(-4.0 * np.pi, 4.0 * np.pi)
            rotation2 = Quaternion(axis=axis2, angle=theta2)
            tm2 = transform_matrix(zero_translation, rotation2, False)
            assert_array_almost_equal(tm1 * tm2, tm2 * tm1)

def test_transform_matrix(self) -> None:
    """Test transform matrix using translation and rotation."""
    zero_rotation = Quaternion(axis=(0.0, 0.0, 1.0), angle=0.0)
    for _ in range(100):
        x_trans = random.uniform(-100.0, 100.0)
        y_trans = random.uniform(-100.0, 100.0)
        z_trans = random.uniform(-100.0, 100.0)
        translation = np.array([x_trans, y_trans, z_trans])
        tm = transform_matrix(translation, zero_rotation, False)
        tm_test = np.eye(4)
        tm_test[0:3, 3] = translation
        assert_array_almost_equal(tm, tm_test)
    zero_translation = np.array([0.0, 0.0, 0.0])
    x_axis = (1.0, 0.0, 0.0)
    y_axis = (0.0, 1.0, 0.0)
    z_axis = (0.0, 0.0, 1.0)
    for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
        for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
            rotation = Quaternion(axis=axis, angle=theta)
            tm = transform_matrix(zero_translation, rotation, False)
            tm_test = np.eye(4)
            tm_test[(axis_idx + 1) % 3, (axis_idx + 1) % 3] = np.cos(theta)
            tm_test[(axis_idx + 1) % 3, (axis_idx + 2) % 3] = -np.sin(theta)
            tm_test[(axis_idx + 2) % 3, (axis_idx + 1) % 3] = np.sin(theta)
            tm_test[(axis_idx + 2) % 3, (axis_idx + 2) % 3] = np.cos(theta)
            assert_array_almost_equal(tm, tm_test)
    x_axis = (1.0, 0.0, 0.0)
    y_axis = (0.0, 1.0, 0.0)
    z_axis = (0.0, 0.0, 1.0)
    for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
        for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
            x_trans = random.uniform(-100.0, 100.0)
            y_trans = random.uniform(-100.0, 100.0)
            z_trans = random.uniform(-100.0, 100.0)
            translation = np.array([x_trans, y_trans, z_trans])
            rotation = Quaternion(axis=axis, angle=theta)
            tm = transform_matrix(translation, rotation, False)
            tm_test = np.eye(4)
            tm_test[(axis_idx + 1) % 3, (axis_idx + 1) % 3] = np.cos(theta)
            tm_test[(axis_idx + 1) % 3, (axis_idx + 2) % 3] = -np.sin(theta)
            tm_test[(axis_idx + 2) % 3, (axis_idx + 1) % 3] = np.sin(theta)
            tm_test[(axis_idx + 2) % 3, (axis_idx + 2) % 3] = np.cos(theta)
            tm_test[0:3, 3] = translation
            assert_array_almost_equal(tm, tm_test)
    x_axis = (1.0, 0.0, 0.0)
    y_axis = (0.0, 1.0, 0.0)
    z_axis = (0.0, 0.0, 1.0)
    for axis_idx, axis in enumerate([x_axis, y_axis, z_axis]):
        for theta in np.linspace(-4.0 * np.pi, 4.0 * np.pi, 100):
            x_trans = random.uniform(-100.0, 100.0)
            y_trans = random.uniform(-100.0, 100.0)
            z_trans = random.uniform(-100.0, 100.0)
            translation = np.array([x_trans, y_trans, z_trans])
            rotation = Quaternion(axis=axis, angle=theta)
            tm = transform_matrix(translation, rotation, False)
            inverse_tm = transform_matrix(translation, rotation, True)
            assert_array_almost_equal(inverse_tm, np.linalg.inv(tm))
    zero_rotation = Quaternion(axis=(0.0, 0.0, 1.0), angle=0.0)
    for _ in range(100):
        x_trans1 = random.uniform(-100.0, 100.0)
        y_trans1 = random.uniform(-100.0, 100.0)
        z_trans1 = random.uniform(-100.0, 100.0)
        translation1 = np.array([x_trans1, y_trans1, z_trans1])
        tm1 = transform_matrix(translation1, zero_rotation, False)
        x_trans2 = random.uniform(-100.0, 100.0)
        y_trans2 = random.uniform(-100.0, 100.0)
        z_trans2 = random.uniform(-100.0, 100.0)
        translation2 = np.array([x_trans2, y_trans2, z_trans2])
        tm2 = transform_matrix(translation2, zero_rotation, False)
        assert_array_almost_equal(tm1 * tm2, tm2 * tm1)
    zero_translation = np.array([0.0, 0.0, 0.0])
    x_axis = (1.0, 0.0, 0.0)
    y_axis = (0.0, 1.0, 0.0)
    z_axis = (0.0, 0.0, 1.0)
    for _ in range(100):
        axis1 = random.choice([x_axis, y_axis, z_axis])
        theta1 = random.uniform(-4.0 * np.pi, 4.0 * np.pi)
        rotation1 = Quaternion(axis=axis1, angle=theta1)
        tm1 = transform_matrix(zero_translation, rotation1, False)
        axis2 = random.choice([x_axis, y_axis, z_axis])
        theta2 = random.uniform(-4.0 * np.pi, 4.0 * np.pi)
        rotation2 = Quaternion(axis=axis2, angle=theta2)
        tm2 = transform_matrix(zero_translation, rotation2, False)
        assert_array_almost_equal(tm1 * tm2, tm2 * tm1)

class TestViewPoints(unittest.TestCase):
    """Test ViewPoints."""

    def test_view_points(self) -> None:
        """Test expected value of view_points()."""
        for _ in range(100):
            intrinsic = np.eye(3)
            focal = random.uniform(0.0, 10.0)
            intrinsic[0, 0] = focal
            intrinsic[1, 1] = focal
            pc1 = np.random.uniform(-100.0, 100.0, (3, 100))
            pc2: npt.NDArray[np.float64] = np.random.uniform(-100.0, 100.0) * pc1
            pc1_in_img = view_points(pc1, intrinsic, True)
            pc2_in_img = view_points(pc2, intrinsic, True)
            assert_array_almost_equal(pc1_in_img, pc2_in_img)
        for _ in range(100):
            intrinsic = np.eye(3)
            focal = random.uniform(0.0, 10.0)
            intrinsic[0, 0] = focal
            intrinsic[1, 1] = focal
            x_trans = random.uniform(-100.0, 100.0)
            y_trans = random.uniform(-100.0, 100.0)
            intrinsic[0, 2] = x_trans
            intrinsic[1, 2] = y_trans
            pc3 = np.random.uniform(-100.0, 100.0, (3, 100))
            pc4: npt.NDArray[np.float64] = np.random.uniform(-100.0, 100.0) * pc3
            pc3_in_img = view_points(pc3, intrinsic, True)
            pc4_in_img = view_points(pc4, intrinsic, True)
            assert_array_almost_equal(pc3_in_img, pc4_in_img)

def test_view_points(self) -> None:
    """Test expected value of view_points()."""
    for _ in range(100):
        intrinsic = np.eye(3)
        focal = random.uniform(0.0, 10.0)
        intrinsic[0, 0] = focal
        intrinsic[1, 1] = focal
        pc1 = np.random.uniform(-100.0, 100.0, (3, 100))
        pc2: npt.NDArray[np.float64] = np.random.uniform(-100.0, 100.0) * pc1
        pc1_in_img = view_points(pc1, intrinsic, True)
        pc2_in_img = view_points(pc2, intrinsic, True)
        assert_array_almost_equal(pc1_in_img, pc2_in_img)
    for _ in range(100):
        intrinsic = np.eye(3)
        focal = random.uniform(0.0, 10.0)
        intrinsic[0, 0] = focal
        intrinsic[1, 1] = focal
        x_trans = random.uniform(-100.0, 100.0)
        y_trans = random.uniform(-100.0, 100.0)
        intrinsic[0, 2] = x_trans
        intrinsic[1, 2] = y_trans
        pc3 = np.random.uniform(-100.0, 100.0, (3, 100))
        pc4: npt.NDArray[np.float64] = np.random.uniform(-100.0, 100.0) * pc3
        pc3_in_img = view_points(pc3, intrinsic, True)
        pc4_in_img = view_points(pc4, intrinsic, True)
        assert_array_almost_equal(pc3_in_img, pc4_in_img)

class TestQuaternionYaw(unittest.TestCase):
    """Test QuaternionYaw."""

    def test_quaternion_yaw(self) -> None:
        """Test valid and invalid inputs for quaternion_yaw()."""
        for yaw_in in np.linspace(-10, 10, 100):
            q = Quaternion(axis=(0, 0, 1), angle=yaw_in)
            yaw_true = yaw_in % (2 * np.pi)
            if yaw_true > np.pi:
                yaw_true -= 2 * np.pi
            yaw_test = quaternion_yaw(q)
            self.assertAlmostEqual(yaw_true, yaw_test)
        yaw_in = np.pi / 4
        q = Quaternion(axis=(0, 0, 0.5), angle=yaw_in)
        yaw_test = quaternion_yaw(q)
        self.assertAlmostEqual(yaw_in, yaw_test)
        yaw_in = np.pi / 4
        q = Quaternion(axis=(0, 0, -1), angle=yaw_in)
        yaw_test = -quaternion_yaw(q)
        self.assertAlmostEqual(yaw_in, yaw_test)
        yaw_in = np.pi / 4
        q = Quaternion(axis=(0, 1, 0), angle=yaw_in)
        yaw_test = quaternion_yaw(q)
        self.assertAlmostEqual(0, yaw_test)
        yaw_in = np.pi / 2
        q = Quaternion(axis=(0, 1, 1), angle=yaw_in)
        yaw_test = quaternion_yaw(q)
        self.assertAlmostEqual(yaw_in, yaw_test)
        yaw_in = np.pi / 2
        q = Quaternion(axis=(0, 0, 1), angle=yaw_in) * Quaternion(axis=(0, 1, 0), angle=0.5821)
        yaw_test = quaternion_yaw(q)
        self.assertAlmostEqual(yaw_in, yaw_test)

def test_quaternion_yaw(self) -> None:
    """Test valid and invalid inputs for quaternion_yaw()."""
    for yaw_in in np.linspace(-10, 10, 100):
        q = Quaternion(axis=(0, 0, 1), angle=yaw_in)
        yaw_true = yaw_in % (2 * np.pi)
        if yaw_true > np.pi:
            yaw_true -= 2 * np.pi
        yaw_test = quaternion_yaw(q)
        self.assertAlmostEqual(yaw_true, yaw_test)
    yaw_in = np.pi / 4
    q = Quaternion(axis=(0, 0, 0.5), angle=yaw_in)
    yaw_test = quaternion_yaw(q)
    self.assertAlmostEqual(yaw_in, yaw_test)
    yaw_in = np.pi / 4
    q = Quaternion(axis=(0, 0, -1), angle=yaw_in)
    yaw_test = -quaternion_yaw(q)
    self.assertAlmostEqual(yaw_in, yaw_test)
    yaw_in = np.pi / 4
    q = Quaternion(axis=(0, 1, 0), angle=yaw_in)
    yaw_test = quaternion_yaw(q)
    self.assertAlmostEqual(0, yaw_test)
    yaw_in = np.pi / 2
    q = Quaternion(axis=(0, 1, 1), angle=yaw_in)
    yaw_test = quaternion_yaw(q)
    self.assertAlmostEqual(yaw_in, yaw_test)
    yaw_in = np.pi / 2
    q = Quaternion(axis=(0, 0, 1), angle=yaw_in) * Quaternion(axis=(0, 1, 0), angle=0.5821)
    yaw_test = quaternion_yaw(q)
    self.assertAlmostEqual(yaw_in, yaw_test)

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

def subsample(self, ratio: float) -> None:
    """
        Sub-samples the pointcloud.
        :param ratio: Fraction to keep.
        """
    assert 0 < ratio < 1
    selected_ind = np.random.choice(np.arange(0, self.nbr_points()), size=int(self.nbr_points() * ratio))
    self.points = self.points[:, selected_ind]

def radius_filter(self, radius: float) -> None:
    """
        Removes points outside the given radius.
        :param radius: Radius in meters.
        """
    keep = np.sqrt(self.points[0] ** 2 + self.points[1] ** 2) <= radius
    self.points = self.points[:, keep]

def rotate(self, quaternion: Quaternion) -> None:
    """
        Applies a rotation.
        :param quaternion: Rotation to apply.
        """
    self.points[:3] = np.dot(quaternion.rotation_matrix.astype(np.float32), self.points[:3])

def scale(self, scale: Tuple[float, float, float]) -> None:
    """
        Scales the lidar xyz coordinates.
        :param scale: The scaling parameter.
        """
    scale_arr = np.array(scale)
    scale_arr.shape = (3, 1)
    self.points[:3, :] *= np.tile(scale_arr, (1, self.nbr_points()))

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

def default_color_np(category_name: str) -> npt.NDArray[np.float64]:
    """
    Get the default color for a category in numpy.

    :param category_name: Category name.
    :return: <np.float: 3> RGB color.
    """
    return np.array(default_color(category_name)) / 255.0

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

def set_transform_matrix(self, transform_matrix: List[List[float]]) -> None:
    """
        Sets the transform matrix of the MapVersionMeta object.
        :param transform_matrix: The transform matrix for converting from physical coordinates to pixel coordinates.
        """
    if transform_matrix is not None:
        self.transform_matrix = np.array(transform_matrix)

def serialize(self) -> Dict[str, Any]:
    """
        Serializes the MapVersionMeta instance to a JSON-friendly dictionary representation.
        :return: Encoding of the MapVersionMeta.
        """
    return {'size': self.size, 'name': self.name, 'origin': self.origin, 'layers': [layer.serialize() for layer in self.layers.values()]}

@dataclasses.dataclass
class MapMetaData:
    """Stores the map metadata for all the MapVersions."""

    def __init__(self) -> None:
        """Init function for class."""
        self.versions: Dict[str, MapVersionMeta] = {}

    def __getitem__(self, item: str) -> MapVersionMeta:
        """
        Retrieves the MapVersionMeta for a given map version name.
        :param item: Map version name.
        :return: A MapVersionMeta object.
        """
        return self.versions[item]

    def add_version(self, map_version: MapVersionMeta) -> None:
        """
        Adds a MapVersionMeta to the versions.
        :param map_version: A map version to be added.
        """
        self.versions[map_version.name] = map_version

    @property
    def hash_sizes(self) -> Set[Tuple[str, Tuple[int, int]]]:
        """Returns the hash size of each layer in each map version."""
        hash_sizes_: Set[Tuple[str, Tuple[int, int]]] = set()
        for version in self.versions.values():
            for layer in version.layers.values():
                hash_sizes_.add((layer.md5_hash, tuple(version.size)))
        return hash_sizes_

    @property
    def version_names(self) -> List[str]:
        """
        Returns a list of version names.
        :return: A list of version names.
        """
        return sorted(list(self.versions.keys()))

    def serialize(self) -> List[Dict[str, Any]]:
        """
        Serializes the MapMetaData instance to a JSON-friendly list representation.
        :return: Encoding of the MapMetaData.
        """
        return [map_version.serialize() for map_version in self.versions.values()]

    @classmethod
    def deserialize(cls, encoding: List[Dict[str, Any]]) -> MapMetaData:
        """
        Instantiates a MapMetaData instance from serialized list representation.
        :param encoding: Output from serialize.
        :return: Deserialized MapMetaData.
        """
        mmd = MapMetaData()
        for map_version_encoding in encoding:
            mmd.add_version(MapVersionMeta.deserialize(map_version_encoding))
        return mmd

def serialize(self) -> List[Dict[str, Any]]:
    """
        Serializes the MapMetaData instance to a JSON-friendly list representation.
        :return: Encoding of the MapMetaData.
        """
    return [map_version.serialize() for map_version in self.versions.values()]

@classmethod
def deserialize(cls, encoding: List[Dict[str, Any]]) -> MapMetaData:
    """
        Instantiates a MapMetaData instance from serialized list representation.
        :param encoding: Output from serialize.
        :return: Deserialized MapMetaData.
        """
    mmd = MapMetaData()
    for map_version_encoding in encoding:
        mmd.add_version(MapVersionMeta.deserialize(map_version_encoding))
    return mmd

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

def _get_transform_matrix(self, location: str, layer_name: str) -> npt.NDArray[np.float64]:
    """
        Get transformation matrix of a layer given location and layer name.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        :param layer_name: Name of layer, e.g. `drivable_area`. Use self.layer_names(location) for complete list.
        """
    return np.array(self._metadata[location]['layers'][layer_name]['transform_matrix'])

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

def _torch_savgol_filter(y: torch.Tensor, window_length: int, poly_order: int, deriv_order: int, delta: float) -> torch.Tensor:
    """
    Perform Savinsky Golay filtering on the given tensor.
    This is adapted from the scipy method `scipy.signal.savgol_filter`
        However, it currently only works with window_length of 3.
    :param y: The tensor to filter. Should be of dimension 2.
    :param window_length: The window length to use.
        Currently provided as a parameter, but for now must be 3.
    :param poly_order: The polynomial order to use.
    :param deriv_order: The order of derivitave to use.
    :coefficients: The Savinsky Golay coefficients to use.
    :return: The filtered tensor.
    """
    if window_length != 3:
        raise ValueError('This method has unexpected edge behavior for window_length != 3.')
    if len(y.shape) != 2:
        raise ValueError(f'Unexpected input tensor shape to _torch_savgol_filter(): {y.shape}')
    halflen, rem = divmod(window_length, 2)
    if rem == 0:
        pos = halflen - 0.5
    else:
        pos = float(halflen)
    x = torch.arange(-pos, window_length - pos, dtype=torch.float64)
    order = torch.arange(poly_order + 1).reshape(-1, 1)
    yy = torch.zeros(poly_order + 1, dtype=torch.float64)
    A = x ** order
    yy[deriv_order] = math.factorial(deriv_order) / delta ** deriv_order
    coeffs, _, _, _ = torch.linalg.lstsq(A, yy)
    y_in = y.unsqueeze(1)
    coeffs_in = coeffs.reshape(1, 1, -1)
    result = torch.nn.functional.conv1d(y_in, coeffs_in, padding='same').reshape(y.shape)
    n = result.shape[1]
    result[:, 0] = y[:, 1] - y[:, 0]
    result[:, n - 1] = y[:, n - 1] - y[:, n - 2]
    return result

class CorrectConcrete(ValidationInterface):
    """
    A class that correctly implements the interface.
    """

    def implement_me(self, y: int) -> float:
        """
        Implemented. See interface.
        """
        return float(y + 1.0)

    def some_other_public_method(self, z: int) -> int:
        """
        An additional public method.
        :param z: The input.
        :return: The output.
        """
        return z + 1

    def _some_private_method(self, b: str) -> str:
        """
        A private method.
        :param b: The input.
        :return: The output
        """
        return b + '_foo'

def implement_me(self, y: int) -> float:
    """
        Implemented. See interface.
        """
    return float(y + 1.0)

class CorrectConcreteMulti(ValidationInterface, SecondValidationInterface):
    """
    A class that implements both interfaces.
    """

    def implement_me(self, y: int) -> float:
        """
        Implemented. See interface.
        """
        return float(y) + 5.0

    def implement_me_2(self, q: float) -> str:
        """
        Implemented. See interface.
        """
        return str(q)

def implement_me(self, y: int) -> float:
    """
        Implemented. See interface.
        """
    return float(y) + 5.0

@dataclass
class TrafficLightStatusData:
    """Traffic light status."""
    status: TrafficLightStatusType
    lane_connector_id: int
    timestamp: int

    def serialize(self) -> Dict[str, Any]:
        """Serialize traffic light status."""
        return {'status': self.status.serialize(), 'lane_connector_id': self.lane_connector_id, 'timestamp': self.timestamp}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> TrafficLightStatusData:
        """Deserialize a dict of data to this class."""
        return TrafficLightStatusData(status=TrafficLightStatusType.deserialize(data['status']), lane_connector_id=data['lane_connector_id'], timestamp=data['timestamp'])

def serialize(self) -> Dict[str, Any]:
    """Serialize traffic light status."""
    return {'status': self.status.serialize(), 'lane_connector_id': self.lane_connector_id, 'timestamp': self.timestamp}

def add_marker_to_scene(scene: Dict[str, Any], marker_id: str, pose: StateSE2) -> None:
    """
    Serialize and append a marker to the scene.
    :param scene: scene dict.
    :param marker_id: A unique id of the marker.
    :param pose: The pose of the marker.
    """
    if 'markers' not in scene.keys():
        scene['markers'] = []
    scene['markers'].append({'id': int(marker_id), 'name': marker_id, 'pose': pose.serialize(), 'shape': 'arrow'})

def _get_heading(pt1: Point, pt2: Point) -> float:
    """
    Computes the angle two points makes to the x-axis.
    :param pt1: origin point.
    :param pt2: end point.
    :return: [rad] resulting angle.
    """
    x_diff = pt2.x - pt1.x
    y_diff = pt2.y - pt1.y
    return math.atan2(y_diff, x_diff)

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

@property
def length(self) -> float:
    """Inherited from superclass."""
    return float(self._polyline.length)

def get_curvature_at_arc_length(self, arc_length: float) -> float:
    """Inherited from superclass."""
    curvature = estimate_curvature_along_path(self._polyline, arc_length, self._distance_for_curvature_estimation)
    return float(curvature)

def _get_beta(steering_angle: float, wheel_base: float) -> float:
    """
    Computes beta, the angle from rear axle to COG at instantaneous center of rotation
    :param [rad] steering_angle: steering angle of the car
    :param [m] wheel_base: distance between the axles
    :return: [rad] Value of beta
    """
    beta = math.atan2(math.tan(steering_angle), wheel_base)
    return beta

def _projected_velocities_from_cog(beta: float, cog_speed: float) -> Tuple[float, float]:
    """
    Computes the projected velocities at the rear axle using the Bicycle kinematic model using COG data
    :param beta: [rad] the angle from rear axle to COG at instantaneous center of rotation
    :param cog_speed: [m/s] Magnitude of velocity vector at COG
    :return: Tuple with longitudinal and lateral velocities [m/s] at the rear axle
    """
    rear_axle_forward_velocity = math.cos(beta) * cog_speed
    rear_axle_lateral_velocity = 0
    return (rear_axle_forward_velocity, rear_axle_lateral_velocity)

def _angular_velocity_from_cog(cog_speed: float, length_rear_axle_to_cog: float, beta: float, steering_angle: float) -> float:
    """
    Computes the angular velocity using the Bicycle kinematic model using COG data.
    :param cog_speed: [m/s] Magnitude of velocity vector at COG
    :param length_rear_axle_to_cog: [m] Distance from rear axle to COG
    :param beta: [rad] angle from rear axle to COG at instantaneous center of rotation
    :param steering_angle: [rad] of the car
    """
    return cog_speed / length_rear_axle_to_cog * math.cos(beta) * math.tan(steering_angle)

def _project_accelerations_from_cog(rear_axle_longitudinal_velocity: float, angular_velocity: float, cog_acceleration: float, beta: float) -> Tuple[float, float]:
    """
    Computes the projected accelerations at the rear axle using the Bicycle kinematic model using COG data
    :param rear_axle_longitudinal_velocity: [m/s] Longitudinal component of velocity vector at COG
    :param angular_velocity: [rad/s] Angular velocity at COG
    :param cog_acceleration: [m/s^2] Magnitude of acceleration vector at COG
    :param beta: [rad] ]the angle from rear axle to COG at instantaneous center of rotation
    :return: Tuple with longitudinal and lateral velocities [m/s] at the rear axle
    """
    rear_axle_longitudinal_acceleration = math.cos(beta) * cog_acceleration
    rear_axle_lateral_acceleration = rear_axle_longitudinal_velocity * angular_velocity
    return (rear_axle_longitudinal_acceleration, rear_axle_lateral_acceleration)

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

@property
def array(self) -> npt.NDArray[np.float64]:
    """
        Convert vector to array
        :return: array containing [x, y]
        """
    return np.array([self.x, self.y], dtype=np.float64)

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

def __init__(self, x: float, y: float):
    """
        Create StateVector2D object
        :param x: float direction
        :param y: float direction
        """
    self._x = x
    self._y = y
    self._array: npt.NDArray[np.float64] = np.array([self.x, self.y], dtype=np.float64)

def magnitude(self) -> float:
    """
        :return: magnitude of vector
        """
    return float(np.hypot(self.x, self.y))

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

@property
def rear_axle_to_center_dist(self) -> float:
    """
        Getter for the distance from the rear axle to the center of mass of Ego.
        :return: Distance from rear axle to COG
        """
    return float(self._vehicle_parameters.rear_axle_to_center)

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

@property
def time_seconds(self) -> float:
    """
        Time in seconds
        :return: [s]
        """
    return float(self.time_us * 1e-06)

def get_pacifica_parameters() -> VehicleParameters:
    """
    :return VehicleParameters containing parameters of Pacifica Vehicle.
    """
    return VehicleParameters(vehicle_name='pacifica', vehicle_type='gen1', width=1.1485 * 2.0, front_length=4.049, rear_length=1.127, wheel_base=3.089, cog_position_from_rear_axle=1.67, height=1.777)

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

def test_serialize(self) -> None:
    """Tests that the serialization works as expected."""
    serialized_waypoint = self.waypoint.serialize()
    serialized_expected = [0, 'center_x', 'center_y', 'center_heading', 'length', 'width', 'height', 'velocity_x', 'velocity_y']
    self.assertEqual(serialized_expected, serialized_waypoint)
    serialized_waypoint_no_vel = self.waypoint_no_vel.serialize()
    serialized_no_vel_expected = [0, 'center_x', 'center_y', 'center_heading', 'length', 'width', 'height', None, None]
    self.assertEqual(serialized_no_vel_expected, serialized_waypoint_no_vel)

class TestStateRepresentation(unittest.TestCase):
    """Test StateSE2 and Point2D"""

    def test_point2d(self) -> None:
        """Test Point2D"""
        x = 1.2222
        y = 3.553435
        point = Point2D(x=x, y=y)
        self.assertAlmostEqual(point.x, x)
        self.assertAlmostEqual(point.y, y)

    def test_state_se2(self) -> None:
        """Test StateSE2"""
        x = 1.2222
        y = 3.553435
        heading = 1.32498
        state = StateSE2(x, y, heading)
        self.assertAlmostEqual(state.x, x)
        self.assertAlmostEqual(state.y, y)
        self.assertAlmostEqual(state.heading, heading)

def test_point2d(self) -> None:
    """Test Point2D"""
    x = 1.2222
    y = 3.553435
    point = Point2D(x=x, y=y)
    self.assertAlmostEqual(point.x, x)
    self.assertAlmostEqual(point.y, y)

def test_state_se2(self) -> None:
    """Test StateSE2"""
    x = 1.2222
    y = 3.553435
    heading = 1.32498
    state = StateSE2(x, y, heading)
    self.assertAlmostEqual(state.x, x)
    self.assertAlmostEqual(state.y, y)
    self.assertAlmostEqual(state.heading, heading)

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

def test_properties(self) -> None:
    """Checks that the properties return the expected variables."""
    self.assertTrue(self.dynamic_car_state.rear_axle_velocity_2d is self.dynamic_car_state._rear_axle_velocity_2d)
    self.assertTrue(self.dynamic_car_state.rear_axle_acceleration_2d is self.dynamic_car_state._rear_axle_acceleration_2d)
    self.assertTrue(self.dynamic_car_state.tire_steering_rate is self.dynamic_car_state._tire_steering_rate)
    self.assertTrue(self.dynamic_car_state.tire_steering_rate is self.dynamic_car_state._tire_steering_rate)
    self.assertAlmostEqual(4.104875150354758, self.dynamic_car_state.speed)
    self.assertEqual(0.22360679774997896, self.dynamic_car_state.acceleration)

def matrix_from_pose(pose: StateSE2) -> npt.NDArray[np.float64]:
    """
    Converts a 2D pose to a 3x3 transformation matrix

    :param pose: 2D pose (x, y, yaw)
    :return: 3x3 transformation matrix
    """
    return np.array([[np.cos(pose.heading), -np.sin(pose.heading), pose.x], [np.sin(pose.heading), np.cos(pose.heading), pose.y], [0, 0, 1]])

def absolute_to_relative_poses(absolute_poses: List[StateSE2]) -> List[StateSE2]:
    """
    Converts a list of SE2 poses from absolute to relative coordinates with the first pose being the origin
    :param absolute_poses: list of absolute poses to convert
    :return: list of converted relative poses
    """
    absolute_transforms: npt.NDArray[np.float64] = np.array([matrix_from_pose(pose) for pose in absolute_poses])
    origin_transform = np.linalg.inv(absolute_transforms[0])
    relative_transforms = origin_transform @ absolute_transforms
    relative_poses = [pose_from_matrix(transform_matrix) for transform_matrix in relative_transforms]
    return relative_poses

def relative_to_absolute_poses(origin_pose: StateSE2, relative_poses: List[StateSE2]) -> List[StateSE2]:
    """
    Converts a list of SE2 poses from relative to absolute coordinates using an origin pose.
    :param origin_pose: Reference origin pose
    :param relative_poses: list of relative poses to convert
    :return: list of converted absolute poses
    """
    relative_transforms: npt.NDArray[np.float64] = np.array([matrix_from_pose(pose) for pose in relative_poses])
    origin_transform = matrix_from_pose(origin_pose)
    absolute_transforms: npt.NDArray[np.float32] = origin_transform @ relative_transforms
    absolute_poses = [pose_from_matrix(transform_matrix) for transform_matrix in absolute_transforms]
    return absolute_poses

def numpy_array_to_absolute_velocity(origin_absolute_state: StateSE2, velocities: npt.NDArray[np.float32]) -> List[StateVector2D]:
    """
    Converts an array of relative numpy velocities to a list of absolute StateVector2D objects.
    :param velocities: list of velocities to convert
    :param origin_absolute_state: Reference origin pose
    :return: list of StateVector2D
    """
    assert velocities.shape[1] == 2, f'Expected poses shape of (*, 2), got {velocities.shape}'
    velocities = np.pad(velocities.astype(np.float64), ((0, 0), (0, 1)), 'constant', constant_values=0.0)
    relative_states = [StateSE2.deserialize(pose) for pose in velocities]
    return [StateVector2D(state.x, state.y) for state in relative_to_absolute_poses(origin_absolute_state, relative_states)]

def numpy_array_to_absolute_pose(origin_absolute_state: StateSE2, poses: npt.NDArray[np.float32]) -> List[StateSE2]:
    """
    Converts an array of relative numpy poses to a list of absolute StateSE2 objects.
    :param poses: list of poses to convert
    :param origin_absolute_state: Reference origin pose
    :return: list of StateSE2
    """
    assert poses.shape[1] == 3, f'Expected poses shape of (*, 3), got {poses.shape}'
    relative_states = [StateSE2.deserialize(pose) for pose in poses]
    return relative_to_absolute_poses(origin_absolute_state, relative_states)

def vector_2d_from_magnitude_angle(magnitude: float, angle: float) -> StateVector2D:
    """
    Projects magnitude and angle into a vector of x-y components.
    :param magnitude: The magnitude of the vector.
    :param angle: The angle of the vector.
    :return: A state vector.
    """
    return StateVector2D(np.cos(angle) * magnitude, np.sin(angle) * magnitude)

def state_se2_tensor_to_transform_matrix(input_data: torch.Tensor, precision: Optional[torch.dtype]=None) -> torch.Tensor:
    """
    Transforms a state of the form [x, y, heading] into a 3x3 transform matrix.
    :param input_data: the input data as a 3-d tensor.
    :return: The output 3x3 transformation matrix.
    """
    _validate_state_se2_tensor_shape(input_data, expected_first_dim=1)
    if precision is None:
        precision = input_data.dtype
    x: float = float(input_data[0].item())
    y: float = float(input_data[1].item())
    h: float = float(input_data[2].item())
    cosine: float = math.cos(h)
    sine: float = math.sin(h)
    return torch.tensor([[cosine, -sine, x], [sine, cosine, y], [0.0, 0.0, 1.0]], dtype=precision, device=input_data.device)

def state_se2_tensor_to_transform_matrix_batch(input_data: torch.Tensor, precision: Optional[torch.dtype]=None) -> torch.Tensor:
    """
    Transforms a tensor of states of the form Nx3 (x, y, heading) into a Nx3x3 transform tensor.
    :param input_data: the input data as a Nx3 tensor.
    :param precision: The precision with which to create the output tensor. If None, then it will be inferred from the input tensor.
    :return: The output Nx3x3 batch transformation tensor.
    """
    _validate_state_se2_tensor_batch_shape(input_data)
    if precision is None:
        precision = input_data.dtype
    processed_input = torch.column_stack((input_data[:, 0], input_data[:, 1], torch.cos(input_data[:, 2]), torch.sin(input_data[:, 2]), torch.ones_like(input_data[:, 0], dtype=precision)))
    reshaping_tensor = torch.tensor([[0, 0, 1, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0], [1, 0, 0, 0, 1, 0, 0, 0, 0], [0, -1, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 1]], dtype=precision, device=input_data.device)
    return (processed_input @ reshaping_tensor).reshape(-1, 3, 3)

def transform_matrix_to_state_se2_tensor(input_data: torch.Tensor, precision: Optional[torch.dtype]=None) -> torch.Tensor:
    """
    Converts a Nx3x3 transformation tensor into a Nx3 tensor of [x, y, heading] rows.
    :param input_data: The Nx3x3 transformation matrix.
    :param precision: The precision with which to create the output tensor. If None, then it will be inferred from the input tensor.
    :return: The converted tensor.
    """
    _validate_transform_matrix_shape(input_data)
    if precision is None:
        precision = input_data.dtype
    return torch.tensor([float(input_data[0, 2].item()), float(input_data[1, 2].item()), float(math.atan2(float(input_data[1, 0].item()), float(input_data[0, 0].item())))], dtype=precision)

def rotate_2d(point: Point2D, rotation_matrix: npt.NDArray[np.float64]) -> Point2D:
    """
    Rotate 2D point with a 2d rotation matrix
    :param point: to be rotated
    :param rotation_matrix: [[R11, R12], [R21, R22]]
    :return: rotated point
    """
    assert rotation_matrix.shape == (2, 2)
    rotated_point = np.array([point.x, point.y]) @ rotation_matrix
    return Point2D(rotated_point[0], rotated_point[1])

def rotate_angle(pose: StateSE2, theta: float) -> StateSE2:
    """
    Rotates the scene object by the given angle.
    :param pose: The input pose
    :param theta: The rotation angle.
    """
    cos_theta, sin_theta = (np.cos(theta), np.sin(theta))
    rotation_matrix: npt.NDArray[np.float64] = np.array([[cos_theta, -sin_theta], [sin_theta, cos_theta]])
    return rotate(pose, rotation_matrix)

def transform(pose: StateSE2, transform_matrix: npt.NDArray[np.float64]) -> StateSE2:
    """
    Applies an SE2 transform
    :param pose: The input pose
    :param transform_matrix: The transform matrix, can be 2D (3x3) or 3D (4x4)
    """
    rotated_pose = rotate(pose, transform_matrix[:2, :2])
    return translate(rotated_pose, transform_matrix[:2, 2])

def translate_longitudinally(pose: StateSE2, distance: float) -> StateSE2:
    """
    Translate an SE2 pose longitudinally (along heading direction)
    :param pose: SE2 pose to be translated
    :param distance: [m] distance by which point (x, y, heading) should be translated longitudinally
    :return translated se2
    """
    translation: npt.NDArray[np.float64] = np.array([distance * np.cos(pose.heading), distance * np.sin(pose.heading)])
    return translate(pose, translation)

def translate_laterally(pose: StateSE2, distance: float) -> StateSE2:
    """
    Translate an SE2 pose laterally
    :param pose: SE2 pose to be translated
    :param distance: [m] distance by which point (x, y, heading) should be translated longitudinally
    :return translated se2
    """
    half_pi = np.pi / 2.0
    translation: npt.NDArray[np.float64] = np.array([distance * np.cos(pose.heading + half_pi), distance * np.sin(pose.heading + half_pi)])
    return translate(pose, translation)

def translate_longitudinally_and_laterally(pose: StateSE2, lon: float, lat: float) -> StateSE2:
    """
    Translate the position component of an SE2 pose longitudinally and laterally
    :param pose: SE2 pose to be translated
    :param lon: [m] distance by which a point should be translated in longitudinal direction
    :param lat: [m] distance by which a point should be translated in lateral direction
    :return Point2D translated position
    """
    half_pi = np.pi / 2.0
    translation: npt.NDArray[np.float64] = np.array([lat * np.cos(pose.heading + half_pi) + lon * np.cos(pose.heading), lat * np.sin(pose.heading + half_pi) + lon * np.sin(pose.heading)])
    return translate(pose, translation)

def lateral_distance(reference: StateSE2, other: Point2D) -> float:
    """
    Lateral distance from a point to a reference pose
    :param reference: the reference pose
    :param other: the query point
    :return: the lateral distance
    """
    return float(-np.sin(reference.heading) * (other.x - reference.x) + np.cos(reference.heading) * (other.y - reference.y))

def longitudinal_distance(reference: StateSE2, other: Point2D) -> float:
    """
    Longitudinal distance from a point to a reference pose
    :param reference: the reference pose
    :param other: the query point
    :return: the longitudinal distance
    """
    return float(np.cos(reference.heading) * (other.x - reference.x) + np.sin(reference.heading) * (other.y - reference.y))

def compute_distance(lhs: StateSE2, rhs: StateSE2) -> float:
    """
    Compute the euclidean distance between two points
    :param lhs: first point
    :param rhs: second point
    :return distance between two points
    """
    return float(np.hypot(lhs.x - rhs.x, lhs.y - rhs.y))

class AngularInterpolator:
    """Creates an angular linear interpolator."""

    def __init__(self, states: npt.NDArray[np.float64], angular_states: npt.NDArray[np.float64]):
        """
        :param states: x values for interpolation
        :param angular_states: y values for interpolation
        """
        _angular_states = np.unwrap(angular_states, axis=0)
        self.interpolator = interp1d(states, _angular_states, axis=0)

    def interpolate(self, sampled_state: Union[float, List[float]]) -> npt.NDArray[np.float64]:
        """
        Interpolates a single state
        :param sampled_state: The state at which to perform interpolation
        :return: The value of the state interpolating linearly at the given state
        """
        return principal_value(self.interpolator(sampled_state))

def __init__(self, states: npt.NDArray[np.float64], angular_states: npt.NDArray[np.float64]):
    """
        :param states: x values for interpolation
        :param angular_states: y values for interpolation
        """
    _angular_states = np.unwrap(angular_states, axis=0)
    self.interpolator = interp1d(states, _angular_states, axis=0)

def interpolate(self, sampled_state: Union[float, List[float]]) -> npt.NDArray[np.float64]:
    """
        Interpolates a single state
        :param sampled_state: The state at which to perform interpolation
        :return: The value of the state interpolating linearly at the given state
        """
    return principal_value(self.interpolator(sampled_state))

def _compute_desired_time_steps(start_timestamp: int, end_timestamp: int, horizon_len_s: float, interval_s: float) -> Tuple[npt.NDArray[np.float64], int]:
    """
    Compute the desired sampling
    :param start_timestamp: [us] starting time stamp
    :param end_timestamp: [us] ending time stamp
    :param horizon_len_s: [s] length of horizon
    :param interval_s: [s] interval between states
    :return: array of time stamps, and the desired length
    """
    num_future_boxes = int(horizon_len_s / interval_s)
    num_target_timestamps = num_future_boxes + 1
    return (np.linspace(start=start_timestamp, stop=end_timestamp, num=num_target_timestamps), num_target_timestamps)

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

def test_rotate_2d(self) -> None:
    """Tests rotation of 2D point"""
    point = Point2D(1, 0)
    rotation_matrix: npt.NDArray[np.float32] = np.array([[0, 1], [-1, 0]], dtype=np.float32)
    result = rotate_2d(point, rotation_matrix)
    self.assertEqual(result, Point2D(0, 1))

def test_rotate(self) -> None:
    """Tests rotation of SE2 pose by rotation matrix"""
    pose = StateSE2(1, 2, np.pi / 4)
    rotation_matrix: npt.NDArray[np.float32] = np.array([[0, 1], [-1, 0]], dtype=np.float32)
    result = rotate(pose, rotation_matrix)
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

def test_principal_value(self) -> None:
    """Tests principal angle calculation"""
    values: npt.NDArray[np.float64] = np.array([0, np.pi, 2 * np.pi, 3 * np.pi, -4 * np.pi, -3 * np.pi])
    expected_wrapped_0_to_pi: npt.NDArray[np.float64] = np.array([0, np.pi, 0, np.pi, 0, np.pi])
    expected_wrapped_neg_pi_to_pi: npt.NDArray[np.float64] = np.array([0, -np.pi, 0, -np.pi, 0, -np.pi])
    actual_wrapped_0_to_pi = principal_value(values, min_=0)
    actual_wrapped_neg_pi_to_pi = principal_value(values)
    np.testing.assert_allclose(expected_wrapped_0_to_pi, actual_wrapped_0_to_pi)
    np.testing.assert_allclose(expected_wrapped_neg_pi_to_pi, actual_wrapped_neg_pi_to_pi)

def to_scene_box(tracked_object: TrackedObject, track_id: str) -> Dict[str, Any]:
    """
    Convert tracked_object into json representation.
    :param tracked_object: tracked_object representation.
    :param track_id: unique id of a track.
    :return json representation of an agent.
    """
    center_x = tracked_object.center.x
    center_y = tracked_object.center.y
    center_heading = tracked_object.center.heading
    if tracked_object.tracked_object_type in AGENT_TYPES:
        speed = np.hypot(tracked_object.velocity.x, tracked_object.velocity.y)
    else:
        speed = 0
    if track_id is None:
        track_id = 'null'
    scene = {'active': True, 'real': True, 'speed': speed if not np.isnan(speed) else 0.0, 'box': {'pose': [center_x, center_y, center_heading], 'size': [tracked_object.box.width, tracked_object.box.length]}, 'id': track_id, 'type': tracked_object.tracked_object_type.fullname, 'tooltip': f'avtest_track_id: {track_id}\ntrack_token: {tracked_object.metadata.track_token}\ntoken: {tracked_object.metadata.token}\ncategory_name: {tracked_object.metadata.category_name}\ntrack_id: {tracked_object.metadata.track_id}\ntype: {tracked_object.tracked_object_type.fullname}\nvelocity: {tracked_object.velocity}'}
    if tracked_object.tracked_object_type == TrackedObjectType.PEDESTRIAN:
        scene['box']['radius'] = 0.5
    return scene

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

def forward_integrate(init: float, delta: float, sampling_time: TimePoint) -> float:
    """
    Performs a simple euler integration.
    :param init: Initial state
    :param delta: The rate of chance of the state.
    :param sampling_time: The time duration to propagate for.
    :return: The result of integration
    """
    return float(init + delta * sampling_time.time_s)

def _get_xy_heading_displacements_from_poses(poses: DoubleMatrix) -> Tuple[DoubleMatrix, DoubleMatrix]:
    """
    Returns position and heading displacements given a pose trajectory.
    :param poses: <np.ndarray: num_poses, 3> A trajectory of poses (x, y, heading).
    :return: Tuple of xy displacements with shape (num_poses-1, 2) and heading displacements with shape (num_poses-1,).
    """
    assert len(poses.shape) == 2, 'Expect a 2D matrix representing a trajectory of poses.'
    assert poses.shape[0] > 1, 'Cannot get displacements given an empty or single element pose trajectory.'
    assert poses.shape[1] == 3, 'Expect pose to have three elements (x, y, heading).'
    pose_differences = np.diff(poses, axis=0)
    xy_displacements = pose_differences[:, :2]
    heading_displacements = principal_value(pose_differences[:, 2])
    return (xy_displacements, heading_displacements)

def _make_banded_difference_matrix(number_rows: int) -> DoubleMatrix:
    """
    Returns a banded difference matrix with specified number_rows.
    When applied to a vector [x_1, ..., x_N], it returns [x_2 - x_1, ..., x_N - x_{N-1}].
    :param number_rows: The row dimension of the banded difference matrix (e.g. N-1 in the example above).
    :return: A banded difference matrix with shape (number_rows, number_rows+1).
    """
    banded_matrix: DoubleMatrix = -1.0 * np.eye(number_rows + 1, dtype=np.float64)[:-1, :]
    for ind in range(len(banded_matrix)):
        banded_matrix[ind, ind + 1] = 1.0
    return banded_matrix

def _fit_initial_velocity_and_acceleration_profile(xy_displacements: DoubleMatrix, heading_profile: DoubleMatrix, discretization_time: float, jerk_penalty: float) -> Tuple[float, DoubleMatrix]:
    """
    Estimates initial velocity (v_0) and acceleration ({a_0, ...}) using least squares with jerk penalty regularization.
    :param xy_displacements: [m] Deviations in x and y occurring between M+1 poses, a M by 2 matrix.
    :param heading_profile: [rad] Headings associated to the starting timestamp for xy_displacements, a M-length vector.
    :param discretization_time: [s] Time discretization used for integration.
    :param jerk_penalty: A regularization parameter used to penalize acceleration differences.  Should be positive.
    :return: Least squares solution for initial velocity (v_0) and acceleration profile ({a_0, ..., a_M-1})
             for M displacement values.
    """
    assert discretization_time > 0.0, 'Discretization time must be positive.'
    assert jerk_penalty > 0, 'Should have a positive jerk_penalty.'
    assert len(xy_displacements.shape) == 2, 'Expect xy_displacements to be a matrix.'
    assert xy_displacements.shape[1] == 2, 'Expect xy_displacements to have 2 columns.'
    num_displacements = len(xy_displacements)
    assert heading_profile.shape == (num_displacements,), 'Expect the length of heading_profile to match that of xy_displacements.'
    y = xy_displacements.flatten()
    A: DoubleMatrix = np.zeros((2 * num_displacements, num_displacements), dtype=np.float64)
    for idx_timestep, heading in enumerate(heading_profile):
        start_row = 2 * idx_timestep
        A[start_row:start_row + 2, 0] = np.array([np.cos(heading) * discretization_time, np.sin(heading) * discretization_time], dtype=np.float64)
        if idx_timestep > 0:
            A[start_row:start_row + 2, 1:1 + idx_timestep] = np.array([[np.cos(heading) * discretization_time ** 2], [np.sin(heading) * discretization_time ** 2]], dtype=np.float64)
    banded_matrix = _make_banded_difference_matrix(num_displacements - 2)
    R: DoubleMatrix = np.block([np.zeros((len(banded_matrix), 1)), banded_matrix])
    x = np.linalg.pinv(A.T @ A + jerk_penalty * R.T @ R) @ A.T @ y
    initial_velocity = x[0]
    acceleration_profile = x[1:]
    return (initial_velocity, acceleration_profile)

def compute_steering_angle_feedback(pose_reference: DoubleMatrix, pose_current: DoubleMatrix, lookahead_distance: float, k_lateral_error: float) -> float:
    """
    Given pose information, determines the steering angle feedback value to address initial tracking error.
    This is based on the feedback controller developed in Section 2.2 of the following paper:
    https://ddl.stanford.edu/publications/design-feedback-feedforward-steering-controller-accurate-path-tracking-and-stability
    :param pose_reference: <np.ndarray: 3,> Contains the reference pose at the current timestep.
    :param pose_current: <np.ndarray: 3,> Contains the actual pose at the current timestep.
    :param lookahead_distance: [m] Distance ahead for which we should estimate lateral error based on a linear fit.
    :param k_lateral_error: Feedback gain for lateral error used to determine steering angle feedback.
    :return: [rad] The steering angle feedback to apply.
    """
    assert pose_reference.shape == (3,), 'We expect a single reference pose.'
    assert pose_current.shape == (3,), 'We expect a single current pose.'
    assert lookahead_distance > 0.0, 'Lookahead distance should be positive.'
    assert k_lateral_error > 0.0, 'Feedback gain for lateral error should be positive.'
    x_reference, y_reference, heading_reference = pose_reference
    x_current, y_current, heading_current = pose_current
    x_error = x_current - x_reference
    y_error = y_current - y_reference
    heading_error = principal_value(heading_current - heading_reference)
    lateral_error = -x_error * np.sin(heading_reference) + y_error * np.cos(heading_reference)
    return float(-k_lateral_error * (lateral_error + lookahead_distance * heading_error))

def get_velocity_curvature_profiles_with_derivatives_from_poses(discretization_time: float, poses: DoubleMatrix, jerk_penalty: float, curvature_rate_penalty: float) -> Tuple[DoubleMatrix, DoubleMatrix, DoubleMatrix, DoubleMatrix]:
    """
    Main function for joint estimation of velocity, acceleration, curvature, and curvature rate given N poses
    sampled at discretization_time.  This is done by solving two least squares problems with the given penalty weights.
    :param discretization_time: [s] Time discretization used for integration.
    :param poses: <np.ndarray: num_poses, 3> A trajectory of N poses (x, y, heading).
    :param jerk_penalty: A regularization parameter used to penalize acceleration differences.  Should be positive.
    :param curvature_rate_penalty: A regularization parameter used to penalize curvature_rate.  Should be positive.
    :return: Profiles for velocity (N-1), acceleration (N-2), curvature (N-1), and curvature rate (N-2).
    """
    xy_displacements, heading_displacements = _get_xy_heading_displacements_from_poses(poses)
    initial_velocity, acceleration_profile = _fit_initial_velocity_and_acceleration_profile(xy_displacements=xy_displacements, heading_profile=poses[:-1, 2], discretization_time=discretization_time, jerk_penalty=jerk_penalty)
    velocity_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_velocity, derivatives=acceleration_profile, discretization_time=discretization_time)
    initial_curvature, curvature_rate_profile = _fit_initial_curvature_and_curvature_rate_profile(heading_displacements=heading_displacements, velocity_profile=velocity_profile, discretization_time=discretization_time, curvature_rate_penalty=curvature_rate_penalty)
    curvature_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_curvature, derivatives=curvature_rate_profile, discretization_time=discretization_time)
    return (velocity_profile, acceleration_profile, curvature_profile, curvature_rate_profile)

def complete_kinematic_state_and_inputs_from_poses(discretization_time: float, wheel_base: float, poses: DoubleMatrix, jerk_penalty: float, curvature_rate_penalty: float) -> Tuple[DoubleMatrix, DoubleMatrix]:
    """
    Main function for joint estimation of velocity, acceleration, steering angle, and steering rate given poses
    sampled at discretization_time and the vehicle wheelbase parameter for curvature -> steering angle conversion.
    One caveat is that we can only determine the first N-1 kinematic states and N-2 kinematic inputs given
    N-1 displacement/difference values, so we need to extrapolate to match the length of poses provided.
    This is handled by repeating the last input and extrapolating the motion model for the last state.
    :param discretization_time: [s] Time discretization used for integration.
    :param wheel_base: [m] The wheelbase length for the kinematic bicycle model being used.
    :param poses: <np.ndarray: num_poses, 3> A trajectory of poses (x, y, heading).
    :param jerk_penalty: A regularization parameter used to penalize acceleration differences.  Should be positive.
    :param curvature_rate_penalty: A regularization parameter used to penalize curvature_rate.  Should be positive.
    :return: kinematic_states (x, y, heading, velocity, steering_angle) and corresponding
            kinematic_inputs (acceleration, steering_rate).
    """
    velocity_profile, acceleration_profile, curvature_profile, curvature_rate_profile = get_velocity_curvature_profiles_with_derivatives_from_poses(discretization_time=discretization_time, poses=poses, jerk_penalty=jerk_penalty, curvature_rate_penalty=curvature_rate_penalty)
    steering_angle_profile, steering_rate_profile = _convert_curvature_profile_to_steering_profile(curvature_profile=curvature_profile, discretization_time=discretization_time, wheel_base=wheel_base)
    acceleration_profile = np.append(acceleration_profile, acceleration_profile[-1])
    steering_rate_profile = np.append(steering_rate_profile, steering_rate_profile[-1])
    velocity_profile = np.append(velocity_profile, velocity_profile[-1] + acceleration_profile[-1] * discretization_time)
    steering_angle_profile = np.append(steering_angle_profile, steering_angle_profile[-1] + steering_rate_profile[-1] * discretization_time)
    kinematic_states: DoubleMatrix = np.column_stack((poses, velocity_profile, steering_angle_profile))
    kinematic_inputs: DoubleMatrix = np.column_stack((acceleration_profile, steering_rate_profile))
    return (kinematic_states, kinematic_inputs)

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

def _make_input_profiles(key_prefix: str, magnitude: float, length: int) -> Dict[str, DoubleMatrix]:
    """
    This test helper function adds input profiles to a dictionary to enable parametrized testing of the tracker utils.
    :param key_prefix: A prefix for keys in the dictionary, e.g. "curv_rate" or "acceleration".
    :param magnitude: A maximum absolute value bound for the input profile.
    :param length: How many elements (timesteps) we should have within the input profile.
    :return: A dictionary containing multiple input profiles we can apply.
    """
    acceleration_dict: Dict[str, DoubleMatrix] = {}
    acceleration_dict[f'{key_prefix}_positive'] = magnitude * np.ones(length, dtype=np.float64)
    acceleration_dict[f'{key_prefix}_zero'] = np.zeros(length, dtype=np.float64)
    acceleration_dict[f'{key_prefix}_negative'] = -magnitude * np.ones(length, dtype=np.float64)
    acceleration_dict[f'{key_prefix}_cosine'] = magnitude * np.cos(np.arange(length, dtype=np.float64))
    return acceleration_dict

def _integrate_acceleration_and_curvature_profile(initial_pose: DoubleMatrix, initial_velocity: DoubleMatrix, initial_curvature: DoubleMatrix, acceleration_profile: DoubleMatrix, curvature_rate_profile: DoubleMatrix, discretization_time: float) -> Tuple[DoubleMatrix, DoubleMatrix, DoubleMatrix]:
    """
    This test helper function takes in an initial state and input profile to generate the associated state trajectory.
    We use curvature for simplicity (the relationship with steering angle is 1-1 for the achievable range).
    :param initial_pose: Initial (x, y, heading) pose state.
    :param initial_velocity: [m/s] The initial velocity state.
    :param initial_curvature: [rad] The initial curvature state.
    :param acceleration_profile: [m/s^2] The acceleration input sequence to apply.
    :param curvature_rate_profile: [rad/s] The curvature rate input to apply.
    :param discretization_time: [s] Time discretization used for integration.
    :return Pose, velocity, and curvature state trajectories after integration.
    """
    velocity_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_velocity, derivatives=acceleration_profile, discretization_time=discretization_time)
    curvature_profile = _generate_profile_from_initial_condition_and_derivatives(initial_condition=initial_curvature, derivatives=curvature_rate_profile, discretization_time=discretization_time)
    pose_trajectory = [initial_pose]
    for velocity, curvature in zip(velocity_profile, curvature_profile):
        x, y, heading = pose_trajectory[-1]
        next_pose = [x + velocity * np.cos(heading) * discretization_time, y + velocity * np.sin(heading) * discretization_time, principal_value(heading + velocity * curvature * discretization_time)]
        pose_trajectory.append(next_pose)
    return (np.array(pose_trajectory), velocity_profile, curvature_profile)

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

def get_state_dot(self, state: EgoState) -> EgoStateDot:
    """Inherited, see super class."""
    longitudinal_speed = state.dynamic_car_state.rear_axle_velocity_2d.x
    x_dot = longitudinal_speed * np.cos(state.rear_axle.heading)
    y_dot = longitudinal_speed * np.sin(state.rear_axle.heading)
    yaw_dot = longitudinal_speed * np.tan(state.tire_steering_angle) / self._vehicle.wheel_base
    return EgoStateDot.build_from_rear_axle(rear_axle_pose=StateSE2(x=x_dot, y=y_dot, heading=yaw_dot), rear_axle_velocity_2d=state.dynamic_car_state.rear_axle_acceleration_2d, rear_axle_acceleration_2d=StateVector2D(0.0, 0.0), tire_steering_angle=state.dynamic_car_state.tire_steering_rate, time_point=state.time_point, is_in_auto_mode=True, vehicle_parameters=self._vehicle)

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

def _get_fixed_timesteps(state: EgoState, future_horizon: float, step_interval: float) -> List[float]:
    """
    Get a fixed array of timesteps starting from a state's time.

    :param state: input state
    :param future_horizon: [s] future time horizon
    :param step_interval: [s] interval between steps in the array
    :return: constructed timestep list
    """
    timesteps = np.arange(0.0, future_horizon, step_interval) + step_interval
    timesteps += state.time_point.time_s
    return list(timesteps.tolist())

def _project_from_global_to_ego_centric_ds(ego_poses: npt.NDArray[np.float32], values: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """
    Project value from the global xy frame to the ego centric ds frame.

    :param ego_poses: [x, y, heading] with size [planned steps, 3].
    :param values: values in global frame with size [planned steps, 2]
    :return: values projected onto the new frame with size [planned steps, 2]
    """
    headings = ego_poses[:, -1:]
    values_lon = values[:, :1] * np.cos(headings) + values[:, 1:2] * np.sin(headings)
    values_lat = values[:, :1] * np.sin(headings) - values[:, 1:2] * np.cos(headings)
    values = np.concatenate((values_lon, values_lat), axis=1)
    return values

def _get_velocity_and_acceleration(ego_poses: List[StateSE2], ego_history: Deque[EgoState], timesteps: List[float]) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """
    Given the past, current and planned ego poses, estimate the velocity and acceleration by taking the derivatives.

    :param ego_poses: a list of the planned ego poses
    :param ego_history: the ego history that includes the current
    :param timesteps: [s] timesteps of the planned ego poses
    :return: the approximated velocity and acceleration in ego centric frame
    """
    ego_history_len = len(ego_history)
    current_ego_state = ego_history[-1]
    timesteps_past_current = [state.time_point.time_s for state in ego_history]
    ego_poses_past_current: npt.NDArray[np.float32] = np.stack([np.array(state.rear_axle.serialize()) for state in ego_history])
    dt = current_ego_state.time_point.time_s - ego_history[-2].time_point.time_s
    timesteps_current_planned: npt.NDArray[np.float32] = np.array([current_ego_state.time_point.time_s] + timesteps)
    ego_poses_current_planned: npt.NDArray[np.float32] = np.stack([current_ego_state.rear_axle.serialize()] + [pose.serialize() for pose in ego_poses])
    ego_poses_interpolate = interp1d(timesteps_current_planned, ego_poses_current_planned, axis=0, fill_value='extrapolate')
    timesteps_current_planned_interp = np.arange(start=current_ego_state.time_point.time_s, stop=timesteps[-1] + 1e-06, step=dt)
    ego_poses_current_planned_interp = ego_poses_interpolate(timesteps_current_planned_interp)
    timesteps_past_current_planned = [*timesteps_past_current, *timesteps_current_planned_interp[1:]]
    ego_poses_past_current_planned: npt.NDArray[np.float32] = np.concatenate([ego_poses_past_current, ego_poses_current_planned_interp[1:]], axis=0)
    ego_velocity_past_current_planned = approximate_derivatives(ego_poses_past_current_planned[:, :2], timesteps_past_current_planned, axis=0)
    ego_acceleration_past_current_planned = approximate_derivatives(ego_poses_past_current_planned[:, :2], timesteps_past_current_planned, axis=0, deriv_order=2)
    ego_velocity_planned_xy = ego_velocity_past_current_planned[ego_history_len:]
    ego_acceleration_planned_xy = ego_acceleration_past_current_planned[ego_history_len:]
    ego_velocity_planned_ds = _project_from_global_to_ego_centric_ds(ego_poses_current_planned_interp[1:], ego_velocity_planned_xy)
    ego_acceleration_planned_ds = _project_from_global_to_ego_centric_ds(ego_poses_current_planned_interp[1:], ego_acceleration_planned_xy)
    ego_velocity_interp_back = interp1d(timesteps_past_current_planned[ego_history_len:], ego_velocity_planned_ds, axis=0, fill_value='extrapolate')
    ego_acceleration_interp_back = interp1d(timesteps_past_current_planned[ego_history_len:], ego_acceleration_planned_ds, axis=0, fill_value='extrapolate')
    ego_velocity_planned_ds = ego_velocity_interp_back(timesteps)
    ego_acceleration_planned_ds = ego_acceleration_interp_back(timesteps)
    return (ego_velocity_planned_ds, ego_acceleration_planned_ds)

def _get_absolute_agent_states_from_numpy_poses(poses: npt.NDArray[np.float32], ego_history: Deque[EgoState], timesteps: List[float]) -> List[EgoState]:
    """
    Converts an array of relative numpy poses to a list of absolute EgoState objects.

    :param poses: input relative poses
    :param ego_history: the history of the ego state, including the current
    :param timesteps: timestamps corresponding to each state
    :return: list of agent states
    """
    ego_state = ego_history[-1]
    relative_states = [StateSE2.deserialize(pose) for pose in poses]
    absolute_states = relative_to_absolute_poses(ego_state.rear_axle, relative_states)
    velocities, accelerations = _get_velocity_and_acceleration(absolute_states, ego_history, timesteps)
    agent_states = [_se2_vel_acc_to_ego_state(state, velocity, acceleration, timestep, ego_state.car_footprint.vehicle_parameters) for state, velocity, acceleration, timestep in zip(absolute_states, velocities, accelerations, timesteps)]
    return agent_states

class TestTransformUtils(unittest.TestCase):
    """
    Unit tests for transform_utils.py
    """

    def test_transform_predictions_to_states(self) -> None:
        """
        Test transform predictions to states
        """
        predicted_poses: npt.NDArray[np.float32] = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
        ego_history: List[MagicMock] = []
        for i in range(5):
            s = MagicMock()
            s.time_point.time_s = i * 0.1
            s.car_footprint.vehicle_parameters = VehicleParameters(width=2, front_length=4, rear_length=1, cog_position_from_rear_axle=2, height=2, wheel_base=3, vehicle_name='mock', vehicle_type='mock')
            s.rear_axle = StateSE2.deserialize([i * 0.1, i * 0.1, np.pi / 4])
            ego_history.append(s)
        future_horizon = 3
        time_interval = 1
        states = transform_predictions_to_states(predicted_poses, ego_history, future_horizon, time_interval)
        np.testing.assert_allclose(ego_history[-1].rear_axle.serialize(), states[0].rear_axle.serialize())
        gt_poses = [[0.4 + i * np.cos(np.pi / 4), 0.4 + i * np.sin(np.pi / 4), np.pi / 4] for i in range(1, 4)]
        np.testing.assert_allclose(gt_poses, [s.rear_axle.serialize() for s in states[1:]])
        np.testing.assert_allclose([0.4, 1.4, 2.4, 3.4], [s.time_point.time_s for s in states])
        np.testing.assert_allclose([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], [s.dynamic_car_state.center_velocity_2d.array for s in states[1:]], rtol=1e-06, atol=1e-06)
        np.testing.assert_allclose([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], [s.dynamic_car_state.center_acceleration_2d.array for s in states[1:]], rtol=1e-06, atol=1e-06)

def test_transform_predictions_to_states(self) -> None:
    """
        Test transform predictions to states
        """
    predicted_poses: npt.NDArray[np.float32] = np.array([[1, 0, 0], [2, 0, 0], [3, 0, 0]])
    ego_history: List[MagicMock] = []
    for i in range(5):
        s = MagicMock()
        s.time_point.time_s = i * 0.1
        s.car_footprint.vehicle_parameters = VehicleParameters(width=2, front_length=4, rear_length=1, cog_position_from_rear_axle=2, height=2, wheel_base=3, vehicle_name='mock', vehicle_type='mock')
        s.rear_axle = StateSE2.deserialize([i * 0.1, i * 0.1, np.pi / 4])
        ego_history.append(s)
    future_horizon = 3
    time_interval = 1
    states = transform_predictions_to_states(predicted_poses, ego_history, future_horizon, time_interval)
    np.testing.assert_allclose(ego_history[-1].rear_axle.serialize(), states[0].rear_axle.serialize())
    gt_poses = [[0.4 + i * np.cos(np.pi / 4), 0.4 + i * np.sin(np.pi / 4), np.pi / 4] for i in range(1, 4)]
    np.testing.assert_allclose(gt_poses, [s.rear_axle.serialize() for s in states[1:]])
    np.testing.assert_allclose([0.4, 1.4, 2.4, 3.4], [s.time_point.time_s for s in states])
    np.testing.assert_allclose([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], [s.dynamic_car_state.center_velocity_2d.array for s in states[1:]], rtol=1e-06, atol=1e-06)
    np.testing.assert_allclose([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], [s.dynamic_car_state.center_acceleration_2d.array for s in states[1:]], rtol=1e-06, atol=1e-06)

@lru_cache(maxsize=256)
def get_agent_relative_angle(ego_state: StateSE2, agent_state: StateSE2) -> float:
    """
    Get the the relative angle of an agent position to the ego
    :param ego_state: pose of ego
    :param agent_state: pose of an agent
    :return: relative angle in radians.
    """
    agent_vector: npt.NDArray[np.float32] = np.array([agent_state.x - ego_state.x, agent_state.y - ego_state.y])
    ego_vector: npt.NDArray[np.float32] = np.array([np.cos(ego_state.heading), np.sin(ego_state.heading)])
    dot_product = np.dot(ego_vector, agent_vector / np.linalg.norm(agent_vector))
    return float(np.arccos(dot_product))

def is_track_stopped(tracked_object: TrackedObject, stopped_speed_threshhold: float=0.05) -> bool:
    """
    Evaluates if a tracked object is stopped
    :param tracked_object: tracked_object representation
    :param stopped_speed_threshhold: Threshhold for 0 speed due to noise
    :return: True if track is stopped else False.
    """
    return True if not isinstance(tracked_object, Agent) else bool(tracked_object.velocity.magnitude() <= stopped_speed_threshhold)

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
def width(self) -> float:
    """:return: [m] agent's width"""
    return float(self._initial_state.box.width)

@property
def length(self) -> float:
    """:return: [m] agent's length"""
    return float(self._initial_state.box.length)

def _velocity_to_global_frame(self, heading: float) -> StateVector2D:
    """
        Transform agent's velocity along the path to global frame
        :param heading: [rad] The heading defining the transform to global frame.
        :return: The velocity vector in global frame.
        """
    return StateVector2D(self.velocity * np.cos(heading), self.velocity * np.sin(heading))

def marker_to_scene(scene: Dict[str, Any], marker_id: str, pose: StateSE2) -> None:
    """
    Renders a pose as an arrow marker
    :param scene: scene dictionary
    :param marker_id: marker id as a string
    :param pose: the pose that defines the markers location
    """
    if 'markers' not in scene.keys():
        scene['markers'] = []
    scene['markers'].append({'id': 0, 'name': marker_id, 'pose': pose.serialize(), 'shape': 'arrow'})

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

class IDMPolicyTests(unittest.TestCase):
    """
    Tests IDM utils.
    """

    def setUp(self) -> None:
        """Test setup."""
        self.test_vector = [1, 0, 0]

    def test_convert_global_to_local_frame(self):
        """
        Tests transform_vector_global_to_local_frame.
        """
        result = transform_vector_global_to_local_frame(self.test_vector, np.pi / 2)
        expect: npt.NDArray[np.int_] = np.array([0, 1, 0])
        actual: npt.NDArray[np.float_] = np.array(result)
        self.assertTrue(np.allclose(expect, actual))
        result = transform_vector_global_to_local_frame(self.test_vector, -np.pi / 2)
        expect = np.array([0, -1, 0])
        actual = np.array(result)
        self.assertTrue(np.allclose(expect, actual))

    def test_convert_local_to_global_frame(self):
        """
        Tests transform_vector_local_to_global_frame.
        """
        result = transform_vector_local_to_global_frame(self.test_vector, np.pi / 2)
        expect: npt.NDArray[np.int_] = np.array([0, -1, 0])
        actual: npt.NDArray[np.float_] = np.array(result)
        self.assertTrue(np.allclose(expect, actual))
        result = transform_vector_local_to_global_frame(self.test_vector, -np.pi / 2)
        expect = np.array([0, 1, 0])
        actual = np.array(result)
        self.assertTrue(np.allclose(expect, actual))
    if __name__ == '__main__':
        unittest.main()

def test_convert_global_to_local_frame(self):
    """
        Tests transform_vector_global_to_local_frame.
        """
    result = transform_vector_global_to_local_frame(self.test_vector, np.pi / 2)
    expect: npt.NDArray[np.int_] = np.array([0, 1, 0])
    actual: npt.NDArray[np.float_] = np.array(result)
    self.assertTrue(np.allclose(expect, actual))
    result = transform_vector_global_to_local_frame(self.test_vector, -np.pi / 2)
    expect = np.array([0, -1, 0])
    actual = np.array(result)
    self.assertTrue(np.allclose(expect, actual))

def test_convert_local_to_global_frame(self):
    """
        Tests transform_vector_local_to_global_frame.
        """
    result = transform_vector_local_to_global_frame(self.test_vector, np.pi / 2)
    expect: npt.NDArray[np.int_] = np.array([0, -1, 0])
    actual: npt.NDArray[np.float_] = np.array(result)
    self.assertTrue(np.allclose(expect, actual))
    result = transform_vector_local_to_global_frame(self.test_vector, -np.pi / 2)
    expect = np.array([0, 1, 0])
    actual = np.array(result)
    self.assertTrue(np.allclose(expect, actual))

class SimulationHistory:
    """
    Simulation history including a sequence of simulation states.
    """

    def __init__(self, map_api: AbstractMap, mission_goal: StateSE2, data: Optional[List[SimulationHistorySample]]=None) -> None:
        """
        Construct the history
        :param map_api: abstract map api for accessing the maps
        :param mission_goal: mission goal for which this history was recorded for
        :param data: A list of simulation data.
        """
        self.map_api: AbstractMap = map_api
        self.mission_goal = mission_goal
        self.data: List[SimulationHistorySample] = data if data is not None else list()

    def add_sample(self, sample: SimulationHistorySample) -> None:
        """
        Add a sample to history
        :param sample: one snapshot of a simulation
        """
        self.data.append(sample)

    def last(self) -> SimulationHistorySample:
        """
        :return: last sample from history, or raise if empty
        """
        if not self.data:
            raise RuntimeError('Data is empty!')
        return self.data[-1]

    def reset(self) -> None:
        """
        Clear the stored data
        """
        self.data.clear()

    def __len__(self) -> int:
        """
        Return the number of history samples as len().
        """
        return len(self.data)

    @property
    def extract_ego_state(self) -> List[EgoState]:
        """
        Extract ego states in simulation history.
        :return An List of ego_states.
        """
        return [sample.ego_state for sample in self.data]

    @property
    def interval_seconds(self) -> float:
        """
        Return the interval between SimulationHistorySamples.
        :return The interval in seconds.
        """
        if not self.data or len(self.data) < 1:
            raise ValueError('Data is empty!')
        elif len(self.data) < 2:
            raise ValueError("Can't calculate the interval of a single-iteration simulation.")
        return float(self.data[1].iteration.time_s - self.data[0].iteration.time_s)

@property
def interval_seconds(self) -> float:
    """
        Return the interval between SimulationHistorySamples.
        :return The interval in seconds.
        """
    if not self.data or len(self.data) < 1:
        raise ValueError('Data is empty!')
    elif len(self.data) < 2:
        raise ValueError("Can't calculate the interval of a single-iteration simulation.")
    return float(self.data[1].iteration.time_s - self.data[0].iteration.time_s)

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
def time_s(self) -> float:
    """
        :return: Time in seconds.
        """
    return float(self.time_point.time_s)

class AgentsAverageHeadingError(AbstractTrainingMetric):
    """
    Metric representing the heading L2 error averaged from all poses of all agents trajectory.
    """

    def __init__(self, name: str='agents_avg_heading_error') -> None:
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
        errors = []
        for sample_idx in range(batch_size):
            error = torch.abs(predicted_agents.heading[sample_idx] - target_agents.heading[sample_idx])
            error_wrapped = torch.atan2(torch.sin(error), torch.cos(error)).mean()
            errors.append(error_wrapped)
        return torch.mean(torch.tensor(errors))

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
    errors = []
    for sample_idx in range(batch_size):
        error = torch.abs(predicted_agents.heading[sample_idx] - target_agents.heading[sample_idx])
        error_wrapped = torch.atan2(torch.sin(error), torch.cos(error)).mean()
        errors.append(error_wrapped)
    return torch.mean(torch.tensor(errors))

class AgentsFinalHeadingError(AbstractTrainingMetric):
    """
    Metric representing the heading L2 error from the final pose of all agents agents.
    """

    def __init__(self, name: str='agents_final_heading_error') -> None:
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
        errors = []
        for sample_idx in range(batch_size):
            error = torch.abs(predicted_agents.terminal_heading[sample_idx] - target_agents.terminal_heading[sample_idx])
            error_wrapped = torch.atan2(torch.sin(error), torch.cos(error)).mean()
            errors.append(error_wrapped)
        return torch.mean(torch.tensor(errors))

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
    errors = []
    for sample_idx in range(batch_size):
        error = torch.abs(predicted_agents.terminal_heading[sample_idx] - target_agents.terminal_heading[sample_idx])
        error_wrapped = torch.atan2(torch.sin(error), torch.cos(error)).mean()
        errors.append(error_wrapped)
    return torch.mean(torch.tensor(errors))

class AverageHeadingError(AbstractTrainingMetric):
    """
    Metric representing the heading L2 error averaged from all poses of a trajectory.
    """

    def __init__(self, name: str='avg_heading_error') -> None:
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
        errors = torch.abs(predicted_trajectory.heading - targets_trajectory.heading)
        return torch.atan2(torch.sin(errors), torch.cos(errors)).mean()

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_trajectory: Trajectory = predictions['trajectory']
    targets_trajectory: Trajectory = targets['trajectory']
    errors = torch.abs(predicted_trajectory.heading - targets_trajectory.heading)
    return torch.atan2(torch.sin(errors), torch.cos(errors)).mean()

class FinalHeadingError(AbstractTrainingMetric):
    """
    Metric representing the heading L2 error from the final pose of a trajectory.
    """

    def __init__(self, name: str='final_heading_error') -> None:
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
        errors = torch.abs(predicted_trajectory.terminal_heading - targets_trajectory.terminal_heading)
        return torch.atan2(torch.sin(errors), torch.cos(errors)).mean()

def compute(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
    """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
    predicted_trajectory: Trajectory = predictions['trajectory']
    targets_trajectory: Trajectory = targets['trajectory']
    errors = torch.abs(predicted_trajectory.terminal_heading - targets_trajectory.terminal_heading)
    return torch.atan2(torch.sin(errors), torch.cos(errors)).mean()

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

def setUp(self) -> None:
    """Set up test case."""
    self.target_data: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])]
    self.prediction_data: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]]])]
    self.objective = AgentsImitationObjective(scenario_type_loss_weighting={})

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

def setUp(self) -> None:
    """Set up test case."""
    self.target_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]])
    self.prediction_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]]])
    self.objective = TrajectoryWeightDecayImitationObjective(scenario_type_loss_weighting={})

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

def setUp(self) -> None:
    """Set up test case."""
    self.target_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]])
    self.prediction_data: npt.NDArray[np.float32] = np.array([[[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]], [[0.0, 0.0, 0.0], [2.0, 2.0, 2.0]]])
    self.objective = ImitationObjective(scenario_type_loss_weighting={'unknown': 1.0, 'lane_following_with_lead': 2.0})

class SinusoidalPositionalEmbedding(nn.Module):
    """
    Copied from L5Kit's implementation `SinusoidalPositionalEmbedding`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/local_graph.py.
    Changes:
        1. Change input variable name `d_model` to `embedding_size`
        2. Change variable name `pe` to `pos_encoding`
        3. Change variable name `t` to `seq_idx`

    A positional embedding module.
    Useful to inject the position of sequence elements in local graphs.
    """

    def __init__(self, embedding_size: int, max_len: int=5000):
        """
        Constructs positional embedding module.
        :param embedding_size: Feature size.
        :param max_len: Max length of the sequences, defaults to 5000.
        """
        super().__init__()
        pos_encoding = torch.zeros(max_len, embedding_size)
        seq_idx = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        log_value = torch.log(torch.tensor([10000.0])).item()
        omega = torch.exp(-log_value / embedding_size * torch.arange(0, embedding_size, 2).float())
        pos_encoding[:, 0::2] = torch.sin(seq_idx * omega)
        pos_encoding[:, 1::2] = torch.cos(seq_idx * omega)
        self.register_buffer('static_embedding', pos_encoding.unsqueeze(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward of the module.
        :param x: Input tensor of shape batch_size x num_agents x sequence_length x d_model.
        :return: Output tensor.
        """
        return self.static_embedding[:x.shape[2], :]

def __init__(self, embedding_size: int, max_len: int=5000):
    """
        Constructs positional embedding module.
        :param embedding_size: Feature size.
        :param max_len: Max length of the sequences, defaults to 5000.
        """
    super().__init__()
    pos_encoding = torch.zeros(max_len, embedding_size)
    seq_idx = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
    log_value = torch.log(torch.tensor([10000.0])).item()
    omega = torch.exp(-log_value / embedding_size * torch.arange(0, embedding_size, 2).float())
    pos_encoding[:, 0::2] = torch.sin(seq_idx * omega)
    pos_encoding[:, 1::2] = torch.cos(seq_idx * omega)
    self.register_buffer('static_embedding', pos_encoding.unsqueeze(1))

class KinematicUnicycleLayerRearAxle(DynamicsLayer):
    """
    Class to forward simulate a dynamical system
    for 1 step, given an initial condition and
    an input.

    The model is a Kinematic unicycle model
    based on first order Euler discretization.
    Reference point is rear axle of vehicle.
    State is (x, y, yaw, vel_x, vel_y, accel_x, accel_y).
    Input is (curvature, jerk).

    Note: Forward Euler means that the inputs
    at time 0 will affect vel_x, vel_y at time 2 and x, y at time 3.

    By subclassing nn.Module, it can be integrated
    in a pipeline where gradient-based optimization
    is employed.

    Adapted from unicycle model in https://arxiv.org/pdf/2109.13602.pdf,
    itself an adaption of the deep kinematic model of https://arxiv.org/abs/1908.00219.
    """

    def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor=None) -> torch.FloatTensor:
        """
        Apply (curvature, jerk) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicUnicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicUnicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicUnicycleLayer.state_dim()]
        """
        x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
        y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
        vel_init = torch.sqrt(torch.square(initial_state[..., StateIndex.X_VELOCITY]) + torch.square(initial_state[..., StateIndex.Y_VELOCITY]))
        yaw = initial_state[..., StateIndex.YAW] + controls[..., InputIndex.CURVATURE] * vel_init * timestep
        vel_x = initial_state[..., StateIndex.X_VELOCITY] + initial_state[..., StateIndex.X_ACCEL] * timestep
        vel_y = initial_state[..., StateIndex.Y_VELOCITY] + initial_state[..., StateIndex.Y_ACCEL] * timestep
        accel_init = torch.sqrt(torch.square(initial_state[..., StateIndex.X_ACCEL]) + torch.square(initial_state[..., StateIndex.Y_ACCEL]))
        accel = accel_init + controls[..., InputIndex.JERK] * timestep
        accel_x = accel * torch.cos(initial_state[..., StateIndex.YAW])
        accel_y = accel * torch.sin(initial_state[..., StateIndex.YAW])
        return torch.stack((x, y, yaw, vel_x, vel_y, accel_x, accel_y), dim=-1)

    @staticmethod
    def state_dim() -> int:
        """
        Utility function returning state dimension.
        States are (x, y, yaw, vel_x, vel_y, accel_x, accel_y)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_unicycle_layers_utils.StateIndex)
        """
        return 7

    @staticmethod
    def input_dim() -> int:
        """
        Utility function returning control dimension.
        Controls are (curvature, jerk)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_unicycle_layers_utils.InputIndex)
        """
        return 2

def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor=None) -> torch.FloatTensor:
    """
        Apply (curvature, jerk) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicUnicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicUnicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicUnicycleLayer.state_dim()]
        """
    x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
    y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
    vel_init = torch.sqrt(torch.square(initial_state[..., StateIndex.X_VELOCITY]) + torch.square(initial_state[..., StateIndex.Y_VELOCITY]))
    yaw = initial_state[..., StateIndex.YAW] + controls[..., InputIndex.CURVATURE] * vel_init * timestep
    vel_x = initial_state[..., StateIndex.X_VELOCITY] + initial_state[..., StateIndex.X_ACCEL] * timestep
    vel_y = initial_state[..., StateIndex.Y_VELOCITY] + initial_state[..., StateIndex.Y_ACCEL] * timestep
    accel_init = torch.sqrt(torch.square(initial_state[..., StateIndex.X_ACCEL]) + torch.square(initial_state[..., StateIndex.Y_ACCEL]))
    accel = accel_init + controls[..., InputIndex.JERK] * timestep
    accel_x = accel * torch.cos(initial_state[..., StateIndex.YAW])
    accel_y = accel * torch.sin(initial_state[..., StateIndex.YAW])
    return torch.stack((x, y, yaw, vel_x, vel_y, accel_x, accel_y), dim=-1)

class KinematicBicycleLayerRearAxle(DynamicsLayer):
    """
    Class to forward simulate a dynamical system
    for 1 step, given an initial condition and
    an input.

    The model is a Kinematic bicycle model
    based on first order Euler discretization.
    Reference point is rear axle of vehicle.
    State is (x, y, yaw, vel_x, vel_y, yaw_rate).
    Input is (acceleration, steering_angle).

    Note: Forward Euler means that the inputs
    at time 0 will affect x,y,yaw at time 2.

    By subclassing nn.Module, it can be integrated
    in a pipeline where gradient-based optimization
    is employed.

    Adapted from https://arxiv.org/abs/1908.00219 (Eq.ns 6 in
    the paper have slightly different kinematics)
    """

    def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
        """
        Apply (acceleration, steering_angle) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicBicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        """
        wheelbase = vehicle_parameters[..., 0]
        vel_init = torch.sqrt(initial_state[..., StateIndex.X_VELOCITY] ** 2 + initial_state[..., StateIndex.Y_VELOCITY] ** 2)
        vel = vel_init + controls[..., InputIndex.ACCEL] * timestep
        yaw_rate = vel_init * torch.tan(controls[..., InputIndex.STEERING_ANGLE]) / wheelbase
        yaw = initial_state[..., StateIndex.YAW] + initial_state[..., StateIndex.YAW_RATE] * timestep
        vel_x = vel * torch.cos(initial_state[..., StateIndex.YAW])
        vel_y = vel * torch.sin(initial_state[..., StateIndex.YAW])
        x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
        y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
        return torch.stack((x, y, yaw, vel_x, vel_y, yaw_rate), dim=-1)

    @staticmethod
    def state_dim() -> int:
        """
        Utility function returning state dimension.
        States are (x, y, yaw, vel_x, vel_y, yaw_rate)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_bicycle_layers_utils.StateIndex)
        """
        return 6

    @staticmethod
    def input_dim() -> int:
        """
        Utility function returning control dimension.
        Controls are (acceleration, steering_angle)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_bicycle_layers_utils.InputIndex)
        """
        return 2

def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
    """
        Apply (acceleration, steering_angle) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicBicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        """
    wheelbase = vehicle_parameters[..., 0]
    vel_init = torch.sqrt(initial_state[..., StateIndex.X_VELOCITY] ** 2 + initial_state[..., StateIndex.Y_VELOCITY] ** 2)
    vel = vel_init + controls[..., InputIndex.ACCEL] * timestep
    yaw_rate = vel_init * torch.tan(controls[..., InputIndex.STEERING_ANGLE]) / wheelbase
    yaw = initial_state[..., StateIndex.YAW] + initial_state[..., StateIndex.YAW_RATE] * timestep
    vel_x = vel * torch.cos(initial_state[..., StateIndex.YAW])
    vel_y = vel * torch.sin(initial_state[..., StateIndex.YAW])
    x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
    y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
    return torch.stack((x, y, yaw, vel_x, vel_y, yaw_rate), dim=-1)

class KinematicBicycleLayerGeometricCenter(DynamicsLayer):
    """
    Class to forward simulate a dynamical systems
    for 1 step, given an initial condition and
    an input.

    The model is a Kinematic bicycle model
    (Eq.ns 1 in https://ieeexplore.ieee.org/document/7225830)
    based on first order Euler discretization.
    Reference point is geometric center of vehicle.
    State is (x, y, yaw, vel_x, vel_y, yaw_rate).
    Input is (acceleration, steering_angle).

    Note: Forward Euler means that the inputs
    at time 0 will affect x,y,yaw at time 2.

    By subclassing nn.Module, it can be integrated
    in a pipeline where gradient-based optimization
    is employed.

    Adapted from https://arxiv.org/abs/1908.00219 (Eq.ns 6 in
    the paper have slightly different kinematics)
    """

    def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
        """
        Apply (acceleration, steering_angle) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicBicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        """
        half_wheelbase = vehicle_parameters[..., 0] * 0.5
        beta = torch.atan(torch.tensor(0.5, dtype=controls.dtype, device=controls.device) * torch.tan(controls[..., InputIndex.STEERING_ANGLE]))
        vel_init = torch.sqrt(initial_state[..., StateIndex.X_VELOCITY] ** 2 + initial_state[..., StateIndex.Y_VELOCITY] ** 2)
        vel = vel_init + controls[..., InputIndex.ACCEL] * timestep
        yaw_rate = vel_init * torch.sin(beta) / half_wheelbase
        yaw = initial_state[..., StateIndex.YAW] + initial_state[..., StateIndex.YAW_RATE] * timestep
        vel_x = vel * torch.cos(initial_state[..., StateIndex.YAW] + beta)
        vel_y = vel * torch.sin(initial_state[..., StateIndex.YAW] + beta)
        x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
        y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
        return torch.stack((x, y, yaw, vel_x, vel_y, yaw_rate), dim=-1)

    @staticmethod
    def state_dim() -> int:
        """
        Utility function returning state dimension.
        States are (x, y, yaw, vel_x, vel_y, yaw_rate)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_bicycle_layers_utils.StateIndex)
        """
        return 6

    @staticmethod
    def input_dim() -> int:
        """
        Utility function returning control dimension.
        Controls are (acceleration, steering_angle)
        (same as nuplan.training.modeling.models.dynamics_layers.kinematic_bicycle_layers_utils.InputIndex)
        """
        return 2

def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
    """
        Apply (acceleration, steering_angle) to agent to obtain next sampled state.

        Note: when using the sampled state (e.g., with an imitation loss),
        pay particular care to yaw and 0 <-> 2pi transitions.

        Tensors below have ellipses, since they can be, e.g. (for initial_state),:
        - torch.FloatTensor[state_dim()] for a single batch, single vehicle
        - torch.FloatTensor[num_vehicles, state_dim()] for a single batch, num_vehicles vehicles
        - torch.FloatTensor[num_batches, num_vehicles, state_dim()] for num_batches batches, num_vehicles vehicles
        - torch.FloatTensor[num_vehicles, num_batches, state_dim()] for num_batches batches, num_vehicles vehicles

        :param initial_state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        :param controls: torch.FloatTensor[..., KinematicBicycleLayer.control_dim()]
        :param timestep: float
        :param vehicle_parameters: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., KinematicBicycleLayer.state_dim()]
        """
    half_wheelbase = vehicle_parameters[..., 0] * 0.5
    beta = torch.atan(torch.tensor(0.5, dtype=controls.dtype, device=controls.device) * torch.tan(controls[..., InputIndex.STEERING_ANGLE]))
    vel_init = torch.sqrt(initial_state[..., StateIndex.X_VELOCITY] ** 2 + initial_state[..., StateIndex.Y_VELOCITY] ** 2)
    vel = vel_init + controls[..., InputIndex.ACCEL] * timestep
    yaw_rate = vel_init * torch.sin(beta) / half_wheelbase
    yaw = initial_state[..., StateIndex.YAW] + initial_state[..., StateIndex.YAW_RATE] * timestep
    vel_x = vel * torch.cos(initial_state[..., StateIndex.YAW] + beta)
    vel_y = vel * torch.sin(initial_state[..., StateIndex.YAW] + beta)
    x = initial_state[..., StateIndex.X_POS] + initial_state[..., StateIndex.X_VELOCITY] * timestep
    y = initial_state[..., StateIndex.Y_POS] + initial_state[..., StateIndex.Y_VELOCITY] * timestep
    return torch.stack((x, y, yaw, vel_x, vel_y, yaw_rate), dim=-1)

def kinematic_bicycle_rear_axle_manual_grad(acceleration: float, steering_angle: float, t: float, x0: torch.Tensor, wheelbase: torch.Tensor) -> torch.Tensor:
    """
    Helper function to manually compute gradient.
    """
    man_grad = torch.zeros(6, 2)
    v0 = torch.sqrt(x0[3] ** 2 + x0[4] ** 2)
    man_grad[3, 0] = t * torch.cos(x0[2])
    man_grad[4, 0] = t * torch.sin(x0[2])
    man_grad[5, 1] = v0 / torch.cos(torch.as_tensor(steering_angle)) ** 2 / wheelbase
    return man_grad

def kinematic_unicycle_rear_axle_manual_grad(curvature: float, jerk: float, t: float, x0: torch.Tensor) -> torch.Tensor:
    """
    Helper function to manually compute gradient.
    """
    man_grad = torch.zeros(7, 2)
    v0 = torch.sqrt(x0[3] ** 2 + x0[4] ** 2)
    man_grad[2, 0] = t * v0
    man_grad[5, 1] = t * torch.cos(x0[2])
    man_grad[6, 1] = t * torch.sin(x0[2])
    return man_grad

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

def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, vehicle_parameters: torch.FloatTensor) -> torch.FloatTensor:
    """Dummy forward pass"""
    x = initial_state[..., 0] + controls[..., 0]
    y = initial_state[..., 1] * controls[..., 0]
    return torch.stack((x, y), dim=-1)

class AgentDropoutAugmentor(AbstractAugmentor):
    """Data augmentation that randomly drops out a part of agents in the scene."""

    def __init__(self, augment_prob: float, dropout_rate: float) -> None:
        """
        Initialize the augmentor.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param dropout_rate: Rate of agents in the scenes to drop out - 0 means no dropout.
        """
        self._augment_prob = augment_prob
        self._dropout_rate = dropout_rate

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        for batch_idx in range(len(features['agents'].agents)):
            num_agents = features['agents'].agents[batch_idx].shape[1]
            keep_mask = np.random.choice([True, False], num_agents, p=[1.0 - self._dropout_rate, self._dropout_rate])
            agent_indices = np.arange(num_agents)[keep_mask]
            features['agents'].agents[batch_idx] = features['agents'].agents[batch_idx].take(agent_indices, axis=1)
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

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    for batch_idx in range(len(features['agents'].agents)):
        num_agents = features['agents'].agents[batch_idx].shape[1]
        keep_mask = np.random.choice([True, False], num_agents, p=[1.0 - self._dropout_rate, self._dropout_rate])
        agent_indices = np.arange(num_agents)[keep_mask]
        features['agents'].agents[batch_idx] = features['agents'].agents[batch_idx].take(agent_indices, axis=1)
    return (features, targets)

class GenericAgentDropoutAugmentor(AbstractAugmentor):
    """Data augmentation that randomly drops out a part of agents in the scene."""

    def __init__(self, augment_prob: float, dropout_rate: float) -> None:
        """
        Initialize the augmentor.
        :param augment_prob: Probability between 0 and 1 of applying the data augmentation.
        :param dropout_rate: Rate of agents in the scenes to drop out - 0 means no dropout.
        """
        self._augment_prob = augment_prob
        self._dropout_rate = dropout_rate

    def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
        """Inherited, see superclass."""
        if np.random.rand() >= self._augment_prob:
            return (features, targets)
        for feature_name in features['generic_agents'].agents.keys():
            for batch_idx in range(len(features['generic_agents'].agents[feature_name])):
                num_agents = features['generic_agents'].agents[feature_name][batch_idx].shape[1]
                keep_mask = np.random.choice([True, False], num_agents, p=[1.0 - self._dropout_rate, self._dropout_rate])
                agent_indices = np.arange(num_agents)[keep_mask]
                features['generic_agents'].agents[feature_name][batch_idx] = features['generic_agents'].agents[feature_name][batch_idx].take(agent_indices, axis=1)
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

def augment(self, features: FeaturesType, targets: TargetsType, scenario: Optional[AbstractScenario]=None) -> Tuple[FeaturesType, TargetsType]:
    """Inherited, see superclass."""
    if np.random.rand() >= self._augment_prob:
        return (features, targets)
    for feature_name in features['generic_agents'].agents.keys():
        for batch_idx in range(len(features['generic_agents'].agents[feature_name])):
            num_agents = features['generic_agents'].agents[feature_name][batch_idx].shape[1]
            keep_mask = np.random.choice([True, False], num_agents, p=[1.0 - self._dropout_rate, self._dropout_rate])
            agent_indices = np.arange(num_agents)[keep_mask]
            features['generic_agents'].agents[feature_name][batch_idx] = features['generic_agents'].agents[feature_name][batch_idx].take(agent_indices, axis=1)
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

def process(x: Sequence[float], u: Sequence[float]) -> Any:
    """Process for state propagation."""
    return vertcat(x[3] * cos(x[2]), x[3] * sin(x[2]), x[3] * u[0], u[1])

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

class GaussianNoise:
    """
    GaussianNoise draws samples from a normal distribution with specified mean and standard deviation.
    """

    def __init__(self, mean: List[float], std: List[float], random_seed: Optional[int]=0):
        """
        :param mean: mean vector for the Gaussian random variables
        :param std: standard deviation for the Gaussian random variables
        :param random_seed: random seed for the random number generation
        """
        self.mean: npt.NDArray[np.float32] = np.array(mean, np.float32)
        self.std: npt.NDArray[np.float32] = np.array(std, np.float32)
        self.rng = np.random.default_rng(random_seed)

    def sample(self) -> npt.NDArray[np.float32]:
        """
        Generate random Gaussian noise vector
        :return: random multi-variant Gaussian vector sample
        """
        return self.rng.normal(self.mean, self.std).astype(np.float32)

    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """
        Gets name of the attributes to be modified by augmentation scheduler callback.
        :return: Names of attributes to be modified by augmentation scheduler callback.
        """
        return [ParameterToScale(self.mean, param_name=f'self.mean={self.mean!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX), ParameterToScale(self.std, param_name=f'self.std={self.std!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)]

def __init__(self, mean: List[float], std: List[float], random_seed: Optional[int]=0):
    """
        :param mean: mean vector for the Gaussian random variables
        :param std: standard deviation for the Gaussian random variables
        :param random_seed: random seed for the random number generation
        """
    self.mean: npt.NDArray[np.float32] = np.array(mean, np.float32)
    self.std: npt.NDArray[np.float32] = np.array(std, np.float32)
    self.rng = np.random.default_rng(random_seed)

class UniformNoise:
    """
    UniformNoise draws samples from a uniform distribution with specified internal.
    """

    def __init__(self, low: List[float], high: List[float], random_seed: Optional[int]=0):
        """
        :param low: vector for lower bound of Uniform random variables
        :param high: vector for lower bound of Uniform random variables
        :param random_seed: random seed for the random number generation
        """
        self.low: npt.NDArray[np.float32] = np.array(low, np.float32)
        self.high: npt.NDArray[np.float32] = np.array(high, np.float32)
        self.rng = np.random.default_rng(random_seed)

    def sample(self) -> npt.NDArray[np.float32]:
        """
        Generate random Gaussian noise vector
        :return: random multi-variant Gaussian vector sample
        """
        return self.rng.uniform(self.low, self.high).astype(np.float32)

    def get_schedulable_attributes(self) -> List[ParameterToScale]:
        """
        Gets attributes to be modified by augmentation scheduler callback.
        :return: Attributes to be modified by augmentation scheduler callback.
        """
        return [ParameterToScale(param=self.low, param_name=f'self.low={self.low!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX), ParameterToScale(param=self.high, param_name=f'self.high={self.high!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)]

def __init__(self, low: List[float], high: List[float], random_seed: Optional[int]=0):
    """
        :param low: vector for lower bound of Uniform random variables
        :param high: vector for lower bound of Uniform random variables
        :param random_seed: random seed for the random number generation
        """
    self.low: npt.NDArray[np.float32] = np.array(low, np.float32)
    self.high: npt.NDArray[np.float32] = np.array(high, np.float32)
    self.rng = np.random.default_rng(random_seed)

def sample(self) -> npt.NDArray[np.float32]:
    """
        Generate random Gaussian noise vector
        :return: random multi-variant Gaussian vector sample
        """
    return self.rng.uniform(self.low, self.high).astype(np.float32)

def compute_yaw_rate_from_states(agent_states_horizon: List[List[StateSE2]], time_stamps: List[TimePoint]) -> npt.NDArray[np.float32]:
    """
    Computes the yaw rate of all agents over the trajectory from heading
    :param agent_states_horizon: agent trajectories [num_frames, num_agents, 1]
           where each state is represented by StateSE2
    :param time_stamps: the time stamps of each frame
    :return: <np.ndarray: num_frames, num_agents, 1> where last dimension is the yaw rate
    """
    yaw: npt.NDArray[np.float32] = np.array([[agent.heading for agent in frame] for frame in agent_states_horizon], dtype=np.float32)
    yaw_rate_horizon = approximate_derivatives(yaw.transpose(), np.array([stamp.time_s for stamp in time_stamps]), window_length=3)
    return cast(npt.NDArray[np.float32], yaw_rate_horizon)

def ego_pose_to_array(ego_pose: EgoState) -> npt.NDArray[np.float32]:
    """
    Convert EgoState to array
    :param ego_pose: agent state
    :return: [x, y, heading]
    """
    return np.array([ego_pose.rear_axle.x, ego_pose.rear_axle.y, ego_pose.rear_axle.heading])

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

def _cartesian_to_projective_coords(coords: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Convert from cartesian coordinates to projective coordinates.
    :param coords: the 2d coordinates of shape (N, 2) where N is the number of points.
    :return: the resulting projective coordinates of shape (N, 3).
    """
    return np.pad(coords, ((0, 0), (0, 1)), 'constant', constant_values=1.0)

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
def features_dim(self) -> int:
    """
        :return: ego feature dimension
        """
    return self.num_frames * AgentsTrajectories.states_dim()

def reshape_to_agents(self) -> None:
    """
        Reshapes predicted agent data by number of agents
        """
    axes = (1, 0) if isinstance(self.data[0], torch.Tensor) else (1, 0, 2)
    self.data = [sample.transpose(*axes).reshape(-1, self.num_frames, self.states_dim()) for sample in self.data]

class AbstractModelFeature(ABC):
    """
    Abstract dataclass that holds the model's input features.

    One can reconstruct this class from a cache e.g.:
        module = importlib.import_module(feature.class_module())
        metric_class_callable = getattr(module, feature.class_name())
        metric_class: AbstractModelFeature = metric_class_callable.from_numpy(np.zeros((10, 10, 10, 8)))

    The inherited dataclass can contain elements which will be available during training
    """

    @classmethod
    def collate(cls, batch: List[AbstractModelFeature]) -> AbstractModelFeature:
        """
        Batch features together with a default_collate function
        :param batch: features to be batched
        :return: batched features together
        """
        serialized = [sample.serialize() for sample in batch]
        return cls.deserialize(default_collate(serialized))

    @abstractmethod
    def to_feature_tensor(self) -> AbstractModelFeature:
        """
        :return object which will be collated into a batch
        """
        pass

    @abstractmethod
    def to_device(self, device: torch.device) -> AbstractModelFeature:
        """
        :param device: desired device to move feature to
        :return feature type that was moved to a device
        """
        pass

    def serialize(self) -> Dict[str, Any]:
        """
        :return: Return dictionary of data that can be serialized
        """
        return dataclasses.asdict(self)

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> AbstractModelFeature:
        """
        :return: Return dictionary of data that can be serialized
        """
        pass

    @abstractmethod
    def unpack(self) -> List[AbstractModelFeature]:
        """
        :return: Unpack a batched feature to a list of features.
        """
        pass

    @property
    def is_valid(self) -> bool:
        """
        :return: Whether the feature is valid (e.g. non empty). By default all features are valid unless overridden.
        """
        return True

@classmethod
def collate(cls, batch: List[AbstractModelFeature]) -> AbstractModelFeature:
    """
        Batch features together with a default_collate function
        :param batch: features to be batched
        :return: batched features together
        """
    serialized = [sample.serialize() for sample in batch]
    return cls.deserialize(default_collate(serialized))

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

def setUp(self) -> None:
    """Set up test case."""
    self.coords: Dict[str, List[npt.NDArray[np.float32]]] = {'LANE': [np.array([[[0.0, 0.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]]])], 'ROUTE': [np.array([[[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0], [0.0, 0.0]]])]}
    self.traffic_light_data: Dict[str, List[npt.NDArray[np.int64]]] = {'LANE': [np.array([[[0, 0, 0, 1], [1, 0, 0, 0]], [[0, 0, 0, 1], [1, 0, 0, 0]]])]}
    self.availabilities: Dict[str, List[npt.NDArray[np.bool_]]] = {'LANE': [np.array([[True, True], [True, True]])], 'ROUTE': [np.array([[True, True, False], [True, True, False]])]}

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

def setUp(self) -> None:
    """Set up test case."""
    self.ego: List[npt.NDArray[np.float32]] = [np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))]
    self.ego_incorrect: List[npt.NDArray[np.float32]] = [np.array([0.0, 0.0, 0.0])]
    self.agents: List[npt.NDArray[np.float32]] = [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])]
    self.agents_incorrect: List[npt.NDArray[np.float32]] = [np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])]

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

def setUp(self) -> None:
    """Set up test case."""
    self.coords: npt.NDArray[np.float32] = np.array([[[0.0, 0.0], [-1.0, 1.0], [1.0, 1.0]], [[1.0, 0.0], [-1.0, -1.0], [1.0, -1.0]]])
    self.avails: npt.NDArray[np.bool_] = np.array([[False, True, True], [True, True, True]])

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

def setUp(self) -> None:
    """Set up test case."""
    self.agent_features = ['VEHICLE', 'PEDESTRIAN', 'BICYCLE', 'TRAFFIC_CONE', 'BARRIER', 'CZONE_SIGN', 'GENERIC_OBJECT']
    self.ego: List[npt.NDArray[np.float32]] = [np.array(([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]))]
    self.ego_incorrect: List[npt.NDArray[np.float32]] = [np.array([0.0, 0.0, 0.0])]
    self.agents: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.array([[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]]])] for feature_name in self.agent_features}
    self.agents_incorrect: Dict[str, List[npt.NDArray[np.float32]]] = {feature_name: [np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])] for feature_name in self.agent_features}

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

def setUp(self) -> None:
    """Set up test case."""
    self.data = torch.Tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [4.0, 0.0, 0.0], [5.0, 0.0, 0.0]])
    self.batched_data = default_collate([self.data, self.data])
    self.batched_trajectory = Trajectory(data=self.batched_data)

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

def test_serialize_deserialize(self) -> None:
    """Test that serialization and deserialization work, and the resulting data matches."""
    serialized = self.trajectories.serialize()
    deserialized = Trajectories.deserialize(serialized)
    self.assertTrue(torch.allclose(self.trajectories.trajectories[0].data, deserialized.trajectories[0].data))

@dataclass
class MetricFile:
    """Metric storage result."""
    key: MetricFileKey
    metric_statistics: List[MetricStatistics] = field(default_factory=list)

    def serialize(self) -> Dict[str, Any]:
        """Serialization of metric result key."""
        return {'key': self.key.serialize(), 'metric_statistics': [metric_statistic.serialize() for metric_statistic in self.metric_statistics]}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> MetricFile:
        """
        Deserialization of metric storage result
        :param data: A dictionary of data
        :return A Statistic data class.
        """
        metric_file_key = MetricFileKey.deserialize(data['key'])
        return MetricFile(key=metric_file_key, metric_statistics=data['metric_statistics'])

def serialize(self) -> Dict[str, Any]:
    """Serialization of metric result key."""
    return {'key': self.key.serialize(), 'metric_statistics': [metric_statistic.serialize() for metric_statistic in self.metric_statistics]}

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> MetricFile:
    """
        Deserialization of metric storage result
        :param data: A dictionary of data
        :return A Statistic data class.
        """
    metric_file_key = MetricFileKey.deserialize(data['key'])
    return MetricFile(key=metric_file_key, metric_statistics=data['metric_statistics'])

@dataclass
class Statistic:
    """
    Class to report statsitcs of metrics.
    """
    name: str
    unit: str
    type: MetricStatisticsType
    value: Union[float, bool]

    def serialize(self) -> Dict[str, Any]:
        """Serialization of TimeSeries."""
        return {'name': self.name, 'unit': self.unit, 'value': self.value, 'type': self.type.serialize()}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Statistic:
        """
        Deserialization of TimeSeries
        :param data: A dictionary of data
        :return A Statistic data class.
        """
        return Statistic(name=data['name'], unit=data['unit'], value=data['value'], type=MetricStatisticsType.deserialize(data['type']))

def serialize(self) -> Dict[str, Any]:
    """Serialization of TimeSeries."""
    return {'name': self.name, 'unit': self.unit, 'value': self.value, 'type': self.type.serialize()}

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Statistic:
    """
        Deserialization of TimeSeries
        :param data: A dictionary of data
        :return A Statistic data class.
        """
    return Statistic(name=data['name'], unit=data['unit'], value=data['value'], type=MetricStatisticsType.deserialize(data['type']))

@dataclass
class MetricStatistics(MetricResult):
    """Class to report results of metric statistics."""
    statistics: List[Statistic]
    time_series: Optional[TimeSeries] = None
    metric_score: Optional[float] = None
    metric_score_unit: Optional[str] = None

    def serialize(self) -> Dict[str, Any]:
        """Serialize the metric result."""
        return {'metric_computator': self.metric_computator, 'name': self.name, 'statistics': [statistic.serialize() for statistic in self.statistics], 'time_series': self.time_series.serialize() if self.time_series is not None else None, 'metric_category': self.metric_category, 'metric_score': self.metric_score, 'metric_score_unit': self.metric_score_unit}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> MetricStatistics:
        """
        Deserialize the metric result when loading from a file.
        :param data; A dictionary of data in loading.
        """
        return MetricStatistics(metric_computator=data['metric_computator'], name=data['name'], statistics=[Statistic.deserialize(statistic) for statistic in data['statistics']], time_series=TimeSeries.deserialize(data['time_series']), metric_category=data['metric_category'], metric_score=data['metric_score'], metric_score_unit=data['metric_score_unit'])

    def serialize_dataframe(self) -> Dict[str, Any]:
        """
        Serialize a dictionary for dataframe
        :return a dictionary
        """
        columns: Dict[str, Any] = {'metric_score': self.metric_score, 'metric_score_unit': self.metric_score_unit, 'metric_category': self.metric_category}
        for statistic in self.statistics:
            statistic_columns = {f'{statistic.name}_stat_type': statistic.type.serialize(), f'{statistic.name}_stat_unit': [statistic.unit], f'{statistic.name}_stat_value': [statistic.value]}
            columns.update(statistic_columns)
        time_series_columns: Dict[str, List[Any]] = {}
        if self.time_series is None:
            time_series_columns.update({MetricStatisticsDataFrame.time_series_unit_column: [None], MetricStatisticsDataFrame.time_series_timestamp_column: [None], MetricStatisticsDataFrame.time_series_values_column: [None], MetricStatisticsDataFrame.time_series_selected_frames_column: [None]})
        else:
            time_series_columns.update({MetricStatisticsDataFrame.time_series_unit_column: [self.time_series.unit], MetricStatisticsDataFrame.time_series_timestamp_column: [[int(timestamp) for timestamp in self.time_series.time_stamps]], MetricStatisticsDataFrame.time_series_values_column: [self.time_series.values], MetricStatisticsDataFrame.time_series_selected_frames_column: [self.time_series.selected_frames]})
        columns.update(time_series_columns)
        return columns

def serialize(self) -> Dict[str, Any]:
    """Serialize the metric result."""
    return {'metric_computator': self.metric_computator, 'name': self.name, 'statistics': [statistic.serialize() for statistic in self.statistics], 'time_series': self.time_series.serialize() if self.time_series is not None else None, 'metric_category': self.metric_category, 'metric_score': self.metric_score, 'metric_score_unit': self.metric_score_unit}

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> MetricStatistics:
    """
        Deserialize the metric result when loading from a file.
        :param data; A dictionary of data in loading.
        """
    return MetricStatistics(metric_computator=data['metric_computator'], name=data['name'], statistics=[Statistic.deserialize(statistic) for statistic in data['statistics']], time_series=TimeSeries.deserialize(data['time_series']), metric_category=data['metric_category'], metric_score=data['metric_score'], metric_score_unit=data['metric_score_unit'])

def compute_traj_heading_errors(ego_traj: List[StateSE2], expert_traj: List[StateSE2]) -> npt.NDArray:
    """
    Compute the heading (yaw) errors between the ego trajectory and expert trajectory
    :param ego_traj: a list of StateSE2 that describe ego position with yaw
    :param expert_traj: a list of StateSE2 that describe expert position with yaw
    :return An array of yaw errors.
    """
    yaw_displacements: npt.NDArray[np.float32] = np.array([ego_traj[i].heading - expert_traj[i].heading for i in range(len(ego_traj))])
    heading_errors = np.abs(principal_value(yaw_displacements))
    return heading_errors

def get_discount_weights(discount_factor: float, traj_len: int, num_trajs: int=1) -> Optional[npt.NDArray[np.float32]]:
    """
    Return the trajectory discount weight array if applicable
    :param discount_factor: the discount factor by which the displacements corresponding to the k^th timestep will
    be discounted
    :param traj_len: len of traj
    :param optional num_trajs: num of ego trajs, default is set to 1, but it's generalized in case we need to
    compare multiple ego trajs with expert
    :return array of discount_weights.
    """
    discount_weights = None
    if discount_factor != 1.0:
        pow_arr = np.tile(np.arange(traj_len), (num_trajs, 1))
        discount_weights = np.power(discount_factor, pow_arr)
    return discount_weights

def ego_delta_v_collision(ego_state: EgoState, scene_object: SceneObject, ego_mass: float=2000, agent_mass: float=2000) -> float:
    """
    Compute the ego delta V (loss of velocity during the collision). Delta V represents the intensity of the collision
    of the ego with other agents.
    :param ego_state: The state of ego.
    :param scene_object: The scene_object ego is colliding with.
    :param ego_mass: mass of ego.
    :param agent_mass: mass of the agent.
    :return The delta V measure for ego.
    """
    ego_mass_ratio = agent_mass / (agent_mass + ego_mass)
    scene_object_speed = scene_object.velocity.magnitude() if isinstance(scene_object, Agent) else 0
    sum_speed_squared = ego_state.dynamic_car_state.speed ** 2 + scene_object_speed ** 2
    cos_rule_term = 2 * ego_state.dynamic_car_state.speed * scene_object_speed * np.cos(ego_state.rear_axle.heading - scene_object.center.heading)
    velocity_component = float(np.sqrt(sum_speed_squared - cos_rule_term))
    return ego_mass_ratio * velocity_component

def extract_ego_time_point(ego_states: List[EgoState]) -> npt.NDArray[np.int32]:
    """
    Extract time point in simulation history
    :param ego_states: A list of ego stets
    :return An array of time in micro seconds.
    """
    time_point: npt.NDArray[np.int32] = np.array([ego_state.time_point.time_us for ego_state in ego_states])
    return time_point

def extract_ego_x_position(history: SimulationHistory) -> npt.NDArray[np.float32]:
    """
    Extract x position of ego pose in simulation history
    :param history: Simulation history
    :return An array of ego pose in x-axis.
    """
    x: npt.NDArray[np.float32] = np.array([sample.ego_state.rear_axle.x for sample in history.data])
    return x

def extract_ego_y_position(history: SimulationHistory) -> npt.NDArray[np.float32]:
    """
    Extract y position of ego pose in simulation history
    :param history: Simulation history
    :return An array of ego pose in y-axis.
    """
    y: npt.NDArray[np.float32] = np.array([sample.ego_state.rear_axle.y for sample in history.data])
    return y

def extract_ego_heading(ego_states: List[EgoState]) -> npt.NDArray[np.float32]:
    """
    Extract yaw headings of ego pose in simulation history
    :param ego_states: A list of ego states
    :return An array of ego pose yaw heading.
    """
    heading: npt.NDArray[np.float32] = np.array([ego_state.rear_axle.heading for ego_state in ego_states])
    return heading

def extract_ego_velocity(ego_states: List[EgoState]) -> npt.NDArray[np.float32]:
    """
    Extract velocity of ego pose from list of ego states
    :param ego_states: A list of ego states
    :return An array of ego pose velocity.
    """
    velocity: npt.NDArray[np.float32] = np.array([ego_state.dynamic_car_state.speed for ego_state in ego_states])
    return velocity

def extract_ego_tire_steering_angle(history: SimulationHistory) -> npt.NDArray[np.float32]:
    """
    Extract ego steering angle
    :param history: Simulation history
    :return An array of ego yaw steering angle.
    """
    tire_steering_angle: npt.NDArray[np.float32] = np.array([sample.ego_state.tire_steering_angle for sample in history.data])
    return tire_steering_angle

def longitudinal_projection(state_vectors: npt.NDArray[np.float32], headings: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """
    Returns the signed projection of the input vectors onto the directions defined
    by the input heading angles
    :param state_vectors: An array of input vectors
    :param headings: Corresponding heading angles defining
        the longitudinal direction (radians).  Need not be principal values
    :return The signed magnitudes of the projections of the
        given input vectors onto the directions given by the headings.
    """
    projection: npt.NDArray[np.float32] = np.cos(headings) * state_vectors[:, 0] + np.sin(headings) * state_vectors[:, 1]
    return projection

def lateral_projection(state_vectors: npt.NDArray[np.float32], headings: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """
    Returns the signed projection of the input vectors onto the directions defined by the input heading angles plus pi/2, i.e. directions normal to the headings
    :param state_vectors: An array of input vectors
    :param headings: Corresponding heading angles defining the longitudinal direction (radians). Need not be principal values
    :return The signed magnitudes of the projections of the given input vectors onto the directions normal to the headings.
    """
    projection: npt.NDArray[np.float32] = -np.sin(headings) * state_vectors[:, 0] + np.cos(headings) * state_vectors[:, 1]
    return projection

def ego_delta_v_collision(ego_state: EgoState, scene_object: SceneObject, ego_mass: float=2000, agent_mass: float=2000) -> float:
    """
    Computes the ego delta V (loss of velocity during the collision). Delta V represents the intensity of the collision
    of the ego with other agents.
    :param ego_state: The state of ego
    :param scene_object: The scene_object ego is colliding with
    :param ego_mass: mass of ego
    :param agent_mass: mass of the agent
    :return The delta V measure for ego
    """
    ego_mass_ratio = agent_mass / (agent_mass + ego_mass)
    scene_object_speed = scene_object.velocity.magnitude() if isinstance(scene_object, Agent) else 0
    sum_speed_squared = ego_state.dynamic_car_state.speed ** 2 + scene_object_speed ** 2
    cos_rule_term = 2 * ego_state.dynamic_car_state.speed * scene_object_speed * np.cos(ego_state.rear_axle.heading - scene_object.center.heading)
    velocity_component = float(np.sqrt(sum_speed_squared - cos_rule_term))
    return ego_mass_ratio * velocity_component

def extract_tracks_speed(history: SimulationHistory) -> List[npt.NDArray[np.float32]]:
    """
    Extracts the speed of detected tracks to a list of N_i x 1 arrays, where N_i is the number of detections at frame i
    :param history: History from a simulation engine
    :return List of arrays containing speed at each timestep.
    """
    tracks_speed: List[npt.NDArray[np.float32]] = []
    for sample in history.data:
        speeds = [np.array(tracked_object.velocity.magnitude()) if isinstance(tracked_object, Agent) else 0 for tracked_object in sample.observation.tracked_objects]
        tracks_speed.append(np.array(speeds))
    return tracks_speed

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return self._compute_violation_metric_score(number_of_violations=self.number_of_violations)

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

def __init__(self, route_roadblocks: RouteRoadBlockLinkedList):
    """Class initializer
        :param route_roadblocks: A route roadblock linked list.
        """
    self.curr_roadblock_pair = route_roadblocks.head
    self.progress = [float(0)]
    self.prev_distance_to_start = float(0)
    self.next_roadblock_pair: Optional[RouteBaselineRoadBlockPair] = None
    self.skipped_roadblock_pair: Optional[RouteBaselineRoadBlockPair] = None

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[-1].value)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[0].value)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    if metric_statistics[-1].value:
        return 1.0
    return float(self._compute_violation_metric_score(time_series=time_series))

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[0].value)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[-1].value)

def _get_elongated_box_length(length: float, dx: float, dy: float, time_step_size: float, time_horizon: float) -> float:
    """
    Helper to find the length of an elongated box projected up to a given time horizon.
    :param length: The length of the OrientedBox.
    :param dx: Movement in x axis in global frame at each time_step_size.
    :param dy: Movement in y axis in global frame at each time_step_size.
    :param time_step_size: [s] Step size for the propagation of collision agents.
    :param time_horizon: [s] Time horizon for collision checking.
    :return: Length of elonated box up to time horizon.
    """
    return float(length + np.hypot(dx * time_horizon / time_step_size, dy * time_horizon / time_step_size))

def _get_ego_tracks_displacement_info(ego_state: EgoState, ego_speed: npt.NDArray[np.float64], tracks_poses: npt.NDArray[np.float64], tracks_speed: npt.NDArray[np.float64], time_step_size: float) -> EgoTracksDisplacementInfo:
    """
    Helper function for compute_time_to_collision. Gets relevent pose, displacement values for TTC calculations.
    :param ego_state: Ego state.
    :param ego_speed: Ego speed.
    :param tracks_poses: Array of tracks poses.
    :param tracks_speed: Array of tracks speeds.
    :param time_step_size: [s] Step size for the propagation of collision agents.
    :return: Relevent pose, displacement information for ego and tracks supporting time to collision calculations.
    """
    ego_pose: npt.NDArray[np.float64] = np.array([*ego_state.center], dtype=np.float64)
    ego_box = ego_state.car_footprint.oriented_box
    ego_dx = np.cos(ego_pose[2]) * ego_speed * time_step_size
    ego_dy = np.sin(ego_pose[2]) * ego_speed * time_step_size
    tracks_dxy: npt.NDArray[np.float64] = np.array([np.cos(tracks_poses[:, 2]) * tracks_speed * time_step_size, np.sin(tracks_poses[:, 2]) * tracks_speed * time_step_size], dtype=np.float64).T
    return EgoTracksDisplacementInfo(ego_pose, ego_box, ego_dx, ego_dy, tracks_dxy)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[-1].value)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[0].value)

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

def compute_score(self, scenario: AbstractScenario, metric_statistics: List[Statistic], time_series: Optional[TimeSeries]=None) -> float:
    """Inherited, see superclass."""
    return float(metric_statistics[0].value)

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

def get_lidar_to_ego_transform(self) -> Transform:
    """Implemented. See interface."""
    return np.eye(4)

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
def database_interval(self) -> float:
    """Inherited, see superclass."""
    if self._scenario_extraction_info is None:
        return 0.05
    return float(0.05 / self._scenario_extraction_info.subsample_ratio)

def tl_status_type_from_proto_tl_status_type(tl_status_type: chpb.TrafficLightStatusType) -> TrafficLightStatusType:
    """
    Deserializes TrafficLightStatusType message to a TrafficLightStatusType object
    :param tl_status_type: The proto TrafficLightStatusType message
    :return: The corresponding TrafficLightStatusType object
    """
    return TrafficLightStatusType.deserialize(tl_status_type.status_name)

