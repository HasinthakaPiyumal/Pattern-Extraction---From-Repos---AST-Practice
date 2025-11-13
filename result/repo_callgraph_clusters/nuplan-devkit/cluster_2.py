# Cluster 2

class VectorMapNp(NamedTuple):
    """
    Vector map data structure, including:
        coords: <np.float: num_lane_segments, 2, 2>
            The (x, y) coordinates of the start and end point of the lane segments.
        multi_scale_connections: Dict of {scale: connections_of_scale}.
            Each connections_of_scale is represented by an array of <np.float: num_connections, 2>,
            and each column in the array is [from_lane_segment_idx, to_lane_segment_idx].
    """
    coords: npt.NDArray[np.float64]
    multi_scale_connections: Dict[int, npt.NDArray[np.float64]]

    def translate(self, translate: npt.NDArray[np.float64]) -> VectorMapNp:
        """
        Translate the vector map.

        :param translate: <np.float: 3,>. Translation in x, y, z.
        :return: Translated vector map.
        """
        coords = self.coords
        coords += translate[:2]
        return self._replace(coords=coords)

    def rotate(self, quaternion: Quaternion) -> VectorMapNp:
        """
        Rotate the vector map.

        :param quaternion: Rotation to apply.
        :return: Rotated vector map.
        """
        coords = self.coords
        num_lane_segments, _, _ = coords.shape
        coords = coords.reshape(num_lane_segments * 2, 2)
        coords = np.concatenate((coords, np.zeros_like(coords[:, 0:1])), axis=-1)
        coords = np.dot(quaternion.rotation_matrix.astype(coords.dtype), coords)
        coords = coords[:, :2].reshape(num_lane_segments, 2, 2)
        return self._replace(coords=coords)

    def scale(self, scale: npt.NDArray[np.float64]) -> VectorMapNp:
        """
        Scale the vector map.

        :param scale: <np.float: 3,>. Scale in x, y, z.
        :return: Scaled vector map.
        """
        coords = self.coords
        coords *= scale[:2]
        return self._replace(coords=coords)

    def xflip(self) -> VectorMapNp:
        """
        Flip the vector map along the X-axis.
        :return: Flipped vector map.
        """
        coords = self.coords
        coords[:, :, 0] *= -1
        return self._replace(coords=coords)

    def yflip(self) -> VectorMapNp:
        """
        Flip the vector map along the Y-axis.
        :return: Flipped vector map.
        """
        coords = self.coords
        coords[:, :, 1] *= -1
        return self._replace(coords=coords)

def translate(self, translate: npt.NDArray[np.float64]) -> VectorMapNp:
    """
        Translate the vector map.

        :param translate: <np.float: 3,>. Translation in x, y, z.
        :return: Translated vector map.
        """
    coords = self.coords
    coords += translate[:2]
    return self._replace(coords=coords)

def rotate(self, quaternion: Quaternion) -> VectorMapNp:
    """
        Rotate the vector map.

        :param quaternion: Rotation to apply.
        :return: Rotated vector map.
        """
    coords = self.coords
    num_lane_segments, _, _ = coords.shape
    coords = coords.reshape(num_lane_segments * 2, 2)
    coords = np.concatenate((coords, np.zeros_like(coords[:, 0:1])), axis=-1)
    coords = np.dot(quaternion.rotation_matrix.astype(coords.dtype), coords)
    coords = coords[:, :2].reshape(num_lane_segments, 2, 2)
    return self._replace(coords=coords)

def scale(self, scale: npt.NDArray[np.float64]) -> VectorMapNp:
    """
        Scale the vector map.

        :param scale: <np.float: 3,>. Scale in x, y, z.
        :return: Scaled vector map.
        """
    coords = self.coords
    coords *= scale[:2]
    return self._replace(coords=coords)

def xflip(self) -> VectorMapNp:
    """
        Flip the vector map along the X-axis.
        :return: Flipped vector map.
        """
    coords = self.coords
    coords[:, :, 0] *= -1
    return self._replace(coords=coords)

def yflip(self) -> VectorMapNp:
    """
        Flip the vector map along the Y-axis.
        :return: Flipped vector map.
        """
    coords = self.coords
    coords[:, :, 1] *= -1
    return self._replace(coords=coords)

def transform_ego_traj(ego_poses: npt.NDArray[np.float64], transform_matrix: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    """
    Transform the ego trajectory to the first ego pose.
    :param ego_poses: Ego trajectory to transform.
    :param transform_matrix: Transformation to apply.
    :return The transformed ego poses.
    """
    ego_poses_new = transform_matrix[:3, :3] @ ego_poses[:, 0:3].T + transform_matrix[:3, 3].reshape((-1, 1))
    ego_poses[:, 0:3] = ego_poses_new.T
    return ego_poses

def get_future_ego_trajectory(lidarpc_rec: LidarPc, future_ego_poses: List[EgoPose], transformmatrix: npt.NDArray[np.float64], future_horizon_len_s: float, future_interval_s: float=0.5, extrapolation_threshold_ms: float=100000.0) -> npt.NDArray[np.float64]:
    """
    Extract ego trajectory data starting from current sample timestamp for a duration of
        future horizon length in seconds.
    :param lidarpc_rec: Lidar point cloud record.
    :param future_ego_poses: future ego poses for a duration of horizon length.
    :param transformmatrix: Transformation matrix to transform the boxes from the global frame to the map_crop frame.
    :param future_horizon_len_s: Timestamp horizon of the future waypoints in seconds.
    :param future_interval_s: Timestamp interval of the future waypoints in seconds.
    :param extrapolation_threshold_ms: If the ego interpolation timestamp extends beyond the timestamp of the
        last recorded pose for the ego, then the values for the box position at the target timestamp will only
        be extrapolated if the target timestamp is within the specified number of microseconds of the last recorded
        pose. Otherwise the pose at the target timestamp will be set to None.
    :return: 2d numpy array of extracted trajectory data. Columns are
        (x_map, y_map, z_map, timestamp)
    """
    num_future_poses = int(future_horizon_len_s / future_interval_s)
    num_target_timestamps = num_future_poses + 1
    start_timestamp = lidarpc_rec.ego_pose.timestamp
    ego_traj: List[Tuple[float, ...]] = [(lidarpc_rec.ego_pose.x, lidarpc_rec.ego_pose.y, lidarpc_rec.ego_pose.z)]
    timestamps = [start_timestamp]
    ego_traj.extend([(pose.x, pose.y, pose.z) for pose in future_ego_poses])
    timestamps.extend([pose.timestamp for pose in future_ego_poses])
    target_timestamps: Union[npt.NDArray[np.float64], List[float]] = np.linspace(start=start_timestamp, stop=start_timestamp + future_horizon_len_s * 1000000.0, num=num_target_timestamps)
    last_ego_timestamp = timestamps[-1]
    target_timestamps = [t for t in target_timestamps if t <= last_ego_timestamp + extrapolation_threshold_ms]
    interpolated_ego_traj = interpolate_coordinates(target_timestamps=target_timestamps, box_timestamps=np.array([float(ts) for ts in timestamps]), box_coordinates=ego_traj)
    ego_traj_np = np.zeros((len(interpolated_ego_traj), 4))
    for i, wp in enumerate(interpolated_ego_traj):
        ego_traj_np[i, :] = [wp[0], wp[1], wp[2], target_timestamps[i]]
    num_waypoint = ego_traj_np.shape[0]
    if num_waypoint < num_target_timestamps:
        num_missing_rows = num_target_timestamps - num_waypoint
        padded_row = np.array([np.nan, np.nan, np.nan, np.nan])
        padding = np.tile(padded_row, (num_missing_rows, 1))
        ego_traj_np = np.concatenate((ego_traj_np, padding), axis=0)
    ego_poses = transform_ego_traj(ego_traj_np, lidarpc_rec.ego_pose.trans_matrix_inv)
    transf_matrix = transformmatrix.astype(np.float32)
    ego_poses = transformmatrix[:3, :3] @ ego_traj_np[:, 0:3].T + transf_matrix[:3, 3].reshape((-1, 1))
    ego_traj_np[:, 0:3] = ego_poses.T
    return ego_traj_np

def scale(inp: npt.NDArray[np.float64], scale: Tuple[float, float, float]) -> npt.NDArray[np.float64]:
    """
    Scale a vector.
    :param inp: Vector to scale.
    :param scale: Scale factors.
    :return: Scaled vector.
    """
    scale_np = np.asarray(scale)
    assert len(scale_np) == 3
    return inp * scale_np

def prepare_pointcloud_points(pc: LidarPointCloud, use_intensity: bool=True, use_ring: bool=False, use_lidar_index: bool=False, lidar_indices: Optional[Tuple[int, ...]]=None, sample_apillar_lidar_rings: bool=False) -> LidarPointCloud:
    """
    Prepare the lidar points.
    There are two independent steps:
        - filter points to only use a subset of the lidars
        - change the decorations (intensity and ring)
    :param pc: Pointcloud input.
    :param use_intensity: Whether to use intensity or not.
    :param use_ring: Whether to use ring index or not.
    :param use_lidar_index: Whether to use lidar index as a decoration.
    :param lidar_indices: Which lidars to keep.
        MergedPointCloud has following options:
            0: top lidar
            1: right A pillar lidar
            2: left A pillar lidar
            3: back lidar
            4: front lidar
            None: Use all lidars
    :param sample_apillar_lidar_rings: Whether you want to sample rings for the A-pillar lidars.
    :return: Modified pointcloud.
    """
    a_pillar_lidar_indices = (1, 2)
    ring_indices_to_keep = [0, 1, 2, 3, 4, 5, 6, 8, 11, 17, 23, 29, 35, 38, 39]
    if lidar_indices is None:
        if sample_apillar_lidar_rings:
            keep = np.zeros(pc.points.shape[1])
            keep = np.logical_or(keep, (pc.points[5] != a_pillar_lidar_indices[0]) & (pc.points[5] != a_pillar_lidar_indices[1]))
            for index in a_pillar_lidar_indices:
                keep = np.logical_or(keep, (pc.points[5] == index) & np.isin(pc.points[4], ring_indices_to_keep))
            pc.points = pc.points[:, keep]
    else:
        keep = np.zeros(pc.points.shape[1])
        for index in lidar_indices:
            if sample_apillar_lidar_rings and index in a_pillar_lidar_indices:
                current_keep = (pc.points[5] == index) & np.isin(pc.points[4], ring_indices_to_keep)
            else:
                current_keep = pc.points[5] == index
            keep = np.logical_or(keep, current_keep)
        pc.points = pc.points[:, keep]
    decoration_index = [0, 1, 2]
    if use_intensity:
        decoration_index += [3]
    if use_ring:
        decoration_index += [4]
    if use_lidar_index:
        decoration_index += [5]
    pc.points = pc.points[np.array(decoration_index)]
    return pc

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
def distances_to_ego(self) -> npt.NDArray[np.float64]:
    """
        Returns array containing distances of all boxes in the Track from ego vehicle.
        :return: Distances of all boxes in the track from ego vehicle.
        """
    return np.asarray([lidar_box.distance_to_ego for lidar_box in self.lidar_boxes])

class TestGenerateMultiScaleConnections(unittest.TestCase):
    """
    Test generation of multi-scale connections
    """

    def test_generate_multi_scale_connections(self) -> None:
        """Test generate_multi_scale_connections()"""
        connections = np.array([[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [0, 3], [2, 4]], dtype=np.float64)
        scales = [1, 2, 4]
        expected_multi_scale_connections = {1: connections, 2: np.array([[0, 2], [1, 3], [2, 4], [3, 5], [0, 4], [1, 4], [2, 5]]), 4: np.array([[0, 4], [0, 5], [1, 5]])}
        multi_scale_connections = generate_multi_scale_connections(connections, scales)

        def _convert_to_connection_set(connection_array: npt.NDArray[np.float64]) -> Set[Tuple[float, float]]:
            """
            Convert connections from array to set.

            :param connection_array: <np.float: N, 2>. Connection in array format.
            :return: Connection in set format.
            """
            return {(connection[0], connection[1]) for connection in connection_array}
        self.assertEqual(multi_scale_connections.keys(), expected_multi_scale_connections.keys())
        for key in multi_scale_connections:
            connection_set = _convert_to_connection_set(multi_scale_connections[key])
            expected_connection_set = _convert_to_connection_set(expected_multi_scale_connections[key])
            self.assertEqual(connection_set, expected_connection_set)

def test_generate_multi_scale_connections(self) -> None:
    """Test generate_multi_scale_connections()"""
    connections = np.array([[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [0, 3], [2, 4]], dtype=np.float64)
    scales = [1, 2, 4]
    expected_multi_scale_connections = {1: connections, 2: np.array([[0, 2], [1, 3], [2, 4], [3, 5], [0, 4], [1, 4], [2, 5]]), 4: np.array([[0, 4], [0, 5], [1, 5]])}
    multi_scale_connections = generate_multi_scale_connections(connections, scales)

    def _convert_to_connection_set(connection_array: npt.NDArray[np.float64]) -> Set[Tuple[float, float]]:
        """
            Convert connections from array to set.

            :param connection_array: <np.float: N, 2>. Connection in array format.
            :return: Connection in set format.
            """
        return {(connection[0], connection[1]) for connection in connection_array}
    self.assertEqual(multi_scale_connections.keys(), expected_multi_scale_connections.keys())
    for key in multi_scale_connections:
        connection_set = _convert_to_connection_set(multi_scale_connections[key])
        expected_connection_set = _convert_to_connection_set(expected_multi_scale_connections[key])
        self.assertEqual(connection_set, expected_connection_set)

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

def test_rotate_2d_points2d_to_ego_vehicle_frame(self) -> None:
    """Tests the rotate_2d_points2d_to_ego_vehicle_frame method"""
    points2d: npt.NDArray[np.float32] = np.ones([1, 2], dtype=np.float32)
    result = self.ego_pose.rotate_2d_points2d_to_ego_vehicle_frame(points2d)
    self.assertEqual(result.ndim, 2)

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

def setUp(self) -> None:
    """
        Sets up for the test cases
        """
    coords: npt.NDArray[np.float64] = np.ones([1, 2, 2], dtype=np.float32)
    multi_scale_connections = Dict[int, npt.NDArray[np.float64]]
    self.vector_map_np = VectorMapNp(coords, multi_scale_connections)

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

@property
def velocity_endpoint(self) -> npt.NDArray[np.float64]:
    """
        Extends the velocity vector from the front bottom center.
        :return: <np.float: 3, 1>.
        """
    return self.center_bottom_forward + np.expand_dims(self.velocity.T, axis=1)

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

@classmethod
def make_random(cls) -> LidarPointCloud:
    """
        Instantiates a random point cloud.
        :return: LidarPointCloud instance.
        """
    return LidarPointCloud(points=np.random.normal(0, 100, size=(4, 100)))

def translate(self, x: npt.NDArray[np.float64]) -> None:
    """
        Applies a translation to the point cloud.
        :param x: <np.float: 3,>. Translation in x, y, z.
        """
    self.points[:3] += x.reshape((-1, 1))

def transform(self, transf_matrix: npt.NDArray[np.float64]) -> None:
    """
        Applies a homogeneous transform.
        :param transf_matrix: <np.float: 4, 4>. Homogeneous transformation matrix.
        """
    transf_matrix = transf_matrix.astype(np.float32)
    self.points[:3, :] = transf_matrix[:3, :3] @ self.points[:3] + transf_matrix[:3, 3].reshape((-1, 1))

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

def _assert_tables_attached(self) -> None:
    """
        Checks to ensure that the tables are attached. If not, raises an error.
        """
    if self.are_tables_detached():
        raise RuntimeError('Attempting to query from detached tables.')

def compute_joint_distance_matrix(array: npt.NDArray[np.uint8], precision: float) -> npt.NDArray[np.float64]:
    """
    For each pixel in `array`, computes the physical distance to the nearest
    mask boundary. Distances from a 0 to the boundary are returned as positive
    values, and distances from a 1 to the boundary are returned as negative
    values.
    :param array: Binary array of pixel values.
    :param precision: Meters per pixel.
    :return: The physical distance to the nearest mask boundary.
    """
    distances_0_to_boundary = cv2.distanceTransform((1.0 - array).astype(np.uint8), cv2.DIST_L2, 5)
    distances_0_to_boundary[distances_0_to_boundary > 0] -= 0.5
    distances_0_to_boundary = (distances_0_to_boundary * precision).astype(np.float32)
    distances_1_to_boundary = cv2.distanceTransform(array.astype(np.uint8), cv2.DIST_L2, 5)
    distances_1_to_boundary[distances_1_to_boundary > 0] -= 0.5
    distances_1_to_boundary = (distances_1_to_boundary * precision).astype(np.float32)
    return distances_0_to_boundary - distances_1_to_boundary

@dataclasses.dataclass
class MapLayerMeta:
    """Stores the metadata for a map layer (layer name and md5 hash)."""

    def __init__(self, name: str, md5_hash: str, can_dilate: bool, is_binary: bool, precision: float):
        """
        Initializes MapLayerMeta.
        :param name: Map layer name, e.g. 'drivable_area'
        :param md5_hash: Hash calculated from the mask itself.
        :param can_dilate: Whether we support dilation for this layer.
        :param is_binary: Whether the layer is binary. Most layers, e.g. `drivable_area` are. But some,
            like `intensity` are not.
        :param precision: Identified map resolution in meters per pixel. Typically set to 0.1, meaning that 10 pixels
            correspond to 1 meter.
        """
        self.name = name
        self.md5_hash = md5_hash
        self.can_dilate = can_dilate
        self.is_binary = is_binary
        self.precision = precision

    @property
    def binary_mask_name(self) -> str:
        """
        Returns the binary mask file name.
        :return: The binary mask file name.
        """
        return self.md5_hash + '.bin'

    @property
    def binary_joint_dist_name(self) -> str:
        """
        Returns the binary joint distance file name.
        :return: The binary joint distance file name.
        """
        return self.md5_hash + '.joint_dist.bin'

    @property
    def png_mask_name(self) -> str:
        """
        Returns the PNG mask file name.
        :return: The PNG mask file name.
        """
        return self.md5_hash + '.png'

    def serialize(self) -> Dict[str, Any]:
        """
        Serializes the meta data of a map layer to a JSON-friendly dictionary representation.
        :return: A dict of meta data of map layer.
        """
        return {'name': self.name, 'md5_hash': self.md5_hash, 'can_dilate': self.can_dilate, 'is_binary': self.is_binary, 'precision': self.precision}

    @classmethod
    def deserialize(cls, encoding: Dict[str, Any]) -> MapLayerMeta:
        """
        Instantiates a MapLayerMeta instance from serialized dictionary representation.
        :param encoding: Output from serialize.
        :return: Deserialized meta data.
        """
        return MapLayerMeta(name=encoding['name'], md5_hash=encoding['md5_hash'], can_dilate=encoding['can_dilate'], is_binary=encoding['is_binary'], precision=encoding['precision'])

@classmethod
def deserialize(cls, encoding: Dict[str, Any]) -> MapLayerMeta:
    """
        Instantiates a MapLayerMeta instance from serialized dictionary representation.
        :param encoding: Output from serialize.
        :return: Deserialized meta data.
        """
    return MapLayerMeta(name=encoding['name'], md5_hash=encoding['md5_hash'], can_dilate=encoding['can_dilate'], is_binary=encoding['is_binary'], precision=encoding['precision'])

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

def make_meta(can_dilate: bool, precision: float, is_binary: bool=True) -> MapLayerMeta:
    """
    Helper method to initialize a MapLayerMeta instance.
    :param can_dilate: whether to can dilate or not.
    :param precision: Meters per pixel.
    :param is_binary: Flag to indicate if is binary.
    :return: A MapLayerMeta object.
    """
    return MapLayerMeta(name='test_fixture', md5_hash='not used here', can_dilate=can_dilate, is_binary=is_binary, precision=precision)

def base_method(x: int) -> int:
    """
    A base method that should be patched.
    :param x: The input.
    :return: The output.
    """
    raise RuntimeError('Should be patched.')

def swappable_with_base_method(x: int) -> int:
    """
    A function that is swappable with base_method.
    This exists primarily to test the dynamic import capabilities of `patch_with_validation`.
    :param x: The input.
    :return: The output.
    """
    raise RuntimeError('Should not be actually run.')

class Registry:
    """Registry containing all the nuplan tests."""

    def __init__(self) -> None:
        """Initializes an empty registry"""
        self.registry: Dict[str, TestInfo] = {}

    def add(self, id_: str, params: Optional[str], absdirpath: Optional[str], relpath: Optional[str]) -> None:
        """Adds a test to the registry, fails if the same test is added twice.
        :param id_: The id of the test
        :param params: Parameters of the test
        :param absdirpath: Absolute path of the test json
        :param relpath: Relative path of the test json
        """
        if id_ not in self.registry:
            self.registry[id_] = TestInfo(params, absdirpath, relpath)
        else:
            raise RuntimeError('Tried to add the same node ID twice!')

    def get_type(self, id_: str) -> str:
        """
        Gets the configuration type of the queried test
        :param id_: Id of the test
        :return: String containing the type of test configuration
        """
        if self.registry[id_].is_invalid():
            return 'invalid'
        if self.registry[id_].is_file_based():
            return 'filebased'
        if self.registry[id_].is_hardcoded():
            return 'hardcoded'
        if self.registry[id_].is_newable():
            return 'newable'
        raise RuntimeError('Unknown test id: ' + id_)

    def get_data(self, id_: str) -> Any:
        """
        Loads the information of the queried test from the registry from a json file
        :param id_: ID of the test
        :return: The test dict
        """
        if id_ in self.registry:
            test_info = self.registry[id_]
            if test_info.is_file_based():
                file_path = os.path.join(test_info.absdirpath, test_info.params) + '.json'
                with open(file_path) as f:
                    return json.load(f)
        return {}

def add(self, id_: str, params: Optional[str], absdirpath: Optional[str], relpath: Optional[str]) -> None:
    """Adds a test to the registry, fails if the same test is added twice.
        :param id_: The id of the test
        :param params: Parameters of the test
        :param absdirpath: Absolute path of the test json
        :param relpath: Relative path of the test json
        """
    if id_ not in self.registry:
        self.registry[id_] = TestInfo(params, absdirpath, relpath)
    else:
        raise RuntimeError('Tried to add the same node ID twice!')

def get_type(self, id_: str) -> str:
    """
        Gets the configuration type of the queried test
        :param id_: Id of the test
        :return: String containing the type of test configuration
        """
    if self.registry[id_].is_invalid():
        return 'invalid'
    if self.registry[id_].is_file_based():
        return 'filebased'
    if self.registry[id_].is_hardcoded():
        return 'hardcoded'
    if self.registry[id_].is_newable():
        return 'newable'
    raise RuntimeError('Unknown test id: ' + id_)

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

def __init__(self, *, time_us: int, _direct: bool=True) -> None:
    """Constructor, should not be called directly. Raises if the keyword parameter _direct is not set to false."""
    if _direct:
        raise RuntimeError("Don't initialize this class directly, use one of the constructors instead!")
    self._time_us = time_us

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
def deserialize(vector: List[float]) -> StateSE2:
    """
        Deserialize vector into state SE2
        :param vector: serialized list of floats
        :return: StateSE2
        """
    if len(vector) != 3:
        raise RuntimeError(f'Expected a vector of size 3, got {len(vector)}')
    return StateSE2(x=vector[0], y=vector[1], heading=vector[2])

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

def transform_matrix_to_state_se2_tensor_batch(input_data: torch.Tensor) -> torch.Tensor:
    """
    Converts a Nx3x3 batch transformation matrix into a Nx3 tensor of [x, y, heading] rows.
    :param input_data: The 3x3 transformation matrix.
    :return: The converted tensor.
    """
    _validate_transform_matrix_batch_shape(input_data)
    first_columns = input_data[:, :, 0].reshape(-1, 3)
    angles = torch.atan2(first_columns[:, 1], first_columns[:, 0])
    result = input_data[:, :, 2]
    result[:, 2] = angles
    return result

class WorkerPool(abc.ABC):
    """
    This class executed function on list of arguments. This can either be distributed/parallel or sequential worker.
    """

    def __init__(self, config: WorkerResources):
        """
        Initialize worker with resource description.
        :param config: setup of this worker.
        """
        self.config = config
        if self.config.number_of_threads < 1:
            raise RuntimeError(f'Number of threads can not be 0, and it is {self.config.number_of_threads}!')
        logger.info(f'Worker: {self.__class__.__name__}')
        logger.info(f'{self}')

    def map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """
        Run function with arguments from item_lists, this function will make sure all arguments have the same
        number of elements.
        :param task: function to be run.
        :param item_lists: arguments to the function.
        :param verbose: Whether to increase logger verbosity.
        :return: type from the fn.
        """
        max_size, aligned_item_lists = align_size_of_arguments(*item_lists)
        if verbose:
            logger.info(f'Submitting {max_size} tasks!')
        return self._map(task, *aligned_item_lists, verbose=verbose)

    @abc.abstractmethod
    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """
        Run function with arguments from item_lists. This function can assume that all the args in item_lists have
        the same number of elements.
        :param fn: function to be run.
        :param item_lists: arguments to the function.
        :param number_of_elements: number of calls to the function.
        :return: type from the fn.
        """

    @abc.abstractmethod
    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """
        Submit a task to the worker.
        :param task: to be submitted.
        :param args: arguments for the task.
        :param kwargs: keyword arguments for the task.
        :return: future.
        """
        pass

    @property
    def number_of_threads(self) -> int:
        """
        :return: the number of available threads across all nodes.
        """
        return self.config.number_of_threads

    def __str__(self) -> str:
        """
        :return: string with information about this worker.
        """
        return f'Number of nodes: {self.config.number_of_nodes}\nNumber of CPUs per node: {self.config.number_of_cpus_per_node}\nNumber of GPUs per node: {self.config.number_of_gpus_per_node}\nNumber of threads across all nodes: {self.config.number_of_threads}'

def __init__(self, config: WorkerResources):
    """
        Initialize worker with resource description.
        :param config: setup of this worker.
        """
    self.config = config
    if self.config.number_of_threads < 1:
        raise RuntimeError(f'Number of threads can not be 0, and it is {self.config.number_of_threads}!')
    logger.info(f'Worker: {self.__class__.__name__}')
    logger.info(f'{self}')

def ray_map(task: Task, *item_lists: Iterable[List[Any]], log_dir: Optional[Path]=None) -> List[Any]:
    """
    Initialize ray, align item lists and map each item of a list of arguments to a callable and executes in parallel.
    :param task: callable to be run
    :param item_lists: items to be parallelized
    :param log_dir: directory to store worker logs
    :return: list of outputs
    """
    try:
        results = _ray_map_items(task, *item_lists, log_dir=log_dir)
        return results
    except (RayTaskError, Exception) as exc:
        ray.shutdown()
        traceback.print_exc()
        raise RuntimeError(exc)

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

@property
def history_buffer(self) -> SimulationHistoryBuffer:
    """
        :return SimulationHistoryBuffer from the simulation.
        """
    if self._history_buffer is None:
        raise RuntimeError('_history_buffer is None. Please initialize the buffer by calling Simulation.initialize()')
    return self._history_buffer

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

def _clip_inputs(self, inputs: DoubleMatrix) -> DoubleMatrix:
    """
        Used to clip control inputs within constraints.
        :param: inputs: The control inputs with shape (self._n_inputs,) to clip.
        :return: Clipped version of the control inputs, unmodified if already within constraints.
        """
    assert inputs.shape == (self._n_inputs,), f'The inputs should be a 1D vector with {self._n_inputs} elements.'
    return np.clip(inputs, self._input_clip_min, self._input_clip_max)

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

@property
def step_time(self) -> float:
    """
        :return: [s] The time difference between two poses.
        """
    if not self.interval_length:
        raise RuntimeError('Invalid interval length!')
    return self.interval_length

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

def last(self) -> SimulationHistorySample:
    """
        :return: last sample from history, or raise if empty
        """
    if not self.data:
        raise RuntimeError('Data is empty!')
    return self.data[-1]

def convert_predictions_to_trajectory(predictions: torch.Tensor, trajectory_state_size: int) -> torch.Tensor:
    """
    Convert predictions tensor to Trajectory.data shape
    :param predictions: tensor from network
    :param trajectory_state_size: trajectory state size
    :return: data suitable for Trajectory
    """
    num_batches = predictions.shape[0]
    return predictions.reshape(num_batches, -1, trajectory_state_size)

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

def sample(self) -> npt.NDArray[np.float32]:
    """
        Generate random Gaussian noise vector
        :return: random multi-variant Gaussian vector sample
        """
    return self.rng.normal(self.mean, self.std).astype(np.float32)

def _create_map_raster(vector_map: Union[VectorMap, VectorSetMap], radius: float, size: int, bit_shift: int, pixel_size: float, color: int=1, thickness: int=2) -> npt.NDArray[np.uint8]:
    """
    Create vector map raster layer to be visualized.

    :param vector_map: Vector map feature object.
    :param radius: [m] Radius of grid.
    :param bit_shift: Bit shift when drawing or filling precise polylines/rectangles.
    :param pixel_size: [m] Size of each pixel.
    :param size: [pixels] Size of grid.
    :param color: Grid color.
    :param thickness: Map lane/baseline thickness.
    :return: Instantiated grid.
    """
    vector_coords = vector_map.get_lane_coords(0)
    num_elements, num_points, _ = vector_coords.shape
    map_ortho_align = Rotation.from_euler('z', 90, degrees=True).as_matrix().astype(np.float32)
    coords = vector_coords.reshape(num_elements * num_points, 2)
    coords = np.concatenate((coords, np.zeros_like(coords[:, 0:1])), axis=-1)
    coords = (map_ortho_align @ coords.T).T
    coords = coords[:, :2].reshape(num_elements, num_points, 2)
    coords[..., 0] = np.clip(coords[..., 0], -radius, radius)
    coords[..., 1] = np.clip(coords[..., 1], -radius, radius)
    map_raster: npt.NDArray[np.uint8] = np.zeros((size, size), dtype=np.uint8)
    index_coords = (radius + coords) / pixel_size
    shifted_index_coords = (index_coords * 2 ** bit_shift).astype(np.int64)
    cv2.polylines(map_raster, shifted_index_coords, isClosed=False, color=color, thickness=thickness, shift=bit_shift, lineType=cv2.LINE_AA)
    map_raster = np.flipud(map_raster)
    return map_raster

def _create_agents_raster(agents: Union[Agents, GenericAgents], radius: float, size: int, bit_shift: int, pixel_size: float, color: int=1) -> npt.NDArray[np.uint8]:
    """
    Create agents raster layer to be visualized.

    :param agents: agents feature object (either Agents or GenericAgents).
    :param radius: [m] Radius of grid.
    :param bit_shift: Bit shift when drawing or filling precise polylines/rectangles.
    :param pixel_size: [m] Size of each pixel.
    :param size: [pixels] Size of grid.
    :param color: Grid color.
    :return: Instantiated grid.
    """
    agents_raster: npt.NDArray[np.uint8] = np.zeros((size, size), dtype=np.uint8)
    agents_array: npt.NDArray[np.float32] = np.asarray(agents.get_present_agents_in_sample(0))
    agents_corners: npt.NDArray[np.float32] = np.asarray(agents.get_agent_corners_in_sample(0))
    if len(agents_array) == 0:
        return agents_raster
    map_ortho_align = Rotation.from_euler('z', 90, degrees=True).as_matrix().astype(np.float32)
    transform = Rotation.from_euler('z', agents_array[:, 2], degrees=False).as_matrix().astype(np.float32)
    transform[:, :2, 2] = agents_array[:, :2]
    points = (map_ortho_align @ transform @ agents_corners.transpose([0, 2, 1])).transpose([0, 2, 1])[..., :2]
    points[..., 0] = np.clip(points[..., 0], -radius, radius)
    points[..., 1] = np.clip(points[..., 1], -radius, radius)
    index_points = (radius + points) / pixel_size
    shifted_index_points = (index_points * 2 ** bit_shift).astype(np.int64)
    for box in shifted_index_points:
        cv2.fillPoly(agents_raster, box[None], color=color, shift=bit_shift, lineType=cv2.LINE_AA)
    agents_raster = np.flipud(agents_raster)
    return agents_raster

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

def __post_init__(self) -> None:
    """Sanitize attributes of dataclass."""
    if len(self.data1) != len(self.data2) != len(self.data3):
        raise RuntimeError(f'Not consistent length of batches! {len(self.data1)}!= {len(self.data2)} != {len(self.data3)}')
    if self.num_of_batches == 0:
        raise ValueError('Batch size has to be larger than 0!')
    assert 'test' in self.data3[0].keys(), f'Test is not present in data: {self.data3[0].keys()}!'

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

def _compute_feature(self, ego_state: EgoState, detections: DetectionsTracks, map_api: AbstractMap) -> Raster:
    roadmap_raster = get_roadmap_raster(ego_state.agent, map_api, self.map_features, self.x_range, self.y_range, self.raster_shape, self.target_pixel_size)
    agents_raster = get_agents_raster(ego_state, detections, self.x_range, self.y_range, self.raster_shape)
    ego_raster = get_ego_raster(self.raster_shape, self.ego_longitudinal_offset, self.ego_width_pixels, self.ego_front_length_pixels, self.ego_rear_length_pixels)
    baseline_paths_raster = get_baseline_paths_raster(ego_state.agent, map_api, self.x_range, self.y_range, self.raster_shape, self.target_pixel_size, self.baseline_path_thickness)
    collated_layers: npt.NDArray[np.float32] = np.dstack([ego_raster, agents_raster, roadmap_raster, baseline_paths_raster]).astype(np.float32)
    if collated_layers.shape[-1] != self.num_input_channels:
        raise RuntimeError(f'Invalid raster numpy array. Expected {self.num_input_channels} channels, got {collated_layers.shape[-1]} Shape is {collated_layers.shape}')
    return Raster(data=collated_layers)

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

def num_agents_in_sample(self, agent_type: str, sample_idx: int) -> int:
    """
        Returns the number of agents at a given batch for given agent feature type.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: number of agents in the given batch.
        """
    self._validate_agent_query(agent_type, sample_idx)
    return self.agents[agent_type][sample_idx].shape[1]

def has_agents(self, agent_type: str, sample_idx: int) -> bool:
    """
        Check whether agents of specified type exist in the feature.
        :param agent_type: agent feature type.
        :param sample_idx: the batch index of interest.
        :return: whether agents exist in the feature.
        """
    self._validate_agent_query(agent_type, sample_idx)
    return self.num_agents_in_sample(agent_type, sample_idx) > 0

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

def _convert_absolute_to_relative_states(origin_absolute_state: StateSE2, absolute_states: List[StateSE2]) -> List[StateSE2]:
    """
    Computes the relative states from a list of absolute states using an origin (anchor) state.

    :param origin_absolute_state: absolute state to be used as origin.
    :param absolute_states: list of absolute poses.
    :return: list of relative states.
    """
    origin_absolute_transform = origin_absolute_state.as_matrix()
    origin_transform = np.linalg.inv(origin_absolute_transform)
    absolute_transforms: npt.NDArray[np.float32] = np.array([state.as_matrix() for state in absolute_states])
    relative_transforms = origin_transform @ absolute_transforms.reshape(-1, 3, 3)
    relative_states = [StateSE2.from_matrix(transform) for transform in relative_transforms]
    return relative_states

def _convert_relative_to_absolute_states(origin_absolute_state: StateSE2, relative_states: List[StateSE2]) -> List[StateSE2]:
    """
    Computes the absolute states from a list of relative states using an origin (anchor) state.

    :param origin_absolute_state: absolute state to be used as origin.
    :param relative_states: list of relative poses.
    :return: list of absolute states.
    """
    origin_transform = origin_absolute_state.as_matrix()
    relative_transforms: npt.NDArray[np.float32] = np.array([state.as_matrix() for state in relative_states])
    absolute_transforms = origin_transform @ relative_transforms.reshape(-1, 3, 3)
    absolute_states = [StateSE2.from_matrix(transform) for transform in absolute_transforms]
    return absolute_states

def convert_absolute_to_relative_poses(origin_absolute_state: StateSE2, absolute_states: List[StateSE2]) -> npt.NDArray[np.float32]:
    """
    Computes the relative poses from a list of absolute states using an origin (anchor) state.

    :param origin_absolute_state: absolute state to be used as origin.
    :param absolute_states: list of absolute poses.
    :return: list of relative poses as numpy array.
    """
    relative_states = _convert_absolute_to_relative_states(origin_absolute_state, absolute_states)
    relative_poses: npt.NDArray[np.float32] = np.asarray([state.serialize() for state in relative_states]).astype(np.float32)
    return relative_poses

def convert_relative_to_absolute_poses(origin_absolute_state: StateSE2, relative_states: List[StateSE2]) -> npt.NDArray[np.float64]:
    """
    Computes the absolute poses from a list of relative states using an origin (anchor) state.

    :param origin_absolute_state: absolute state to be used as origin.
    :param relative_states: list of absolute poses.
    :return: list of relative poses as numpy array.
    """
    absolute_states = _convert_relative_to_absolute_states(origin_absolute_state, relative_states)
    absolute_poses: npt.NDArray[np.float64] = np.asarray([state.serialize() for state in absolute_states]).astype(np.float64)
    return absolute_poses

def convert_absolute_to_relative_velocities(origin_absolute_velocity: StateSE2, absolute_velocities: List[StateSE2]) -> npt.NDArray[np.float32]:
    """
    Computes the relative velocities from a list of absolute velocities using an origin (anchor) velocity.

    :param origin_absolute_velocity: absolute velocities to be used as origin.
    :param absolute_velocities: list of absolute velocities.
    :return: list of relative velocities as numpy array.
    """
    relative_states = _convert_absolute_to_relative_states(origin_absolute_velocity, absolute_velocities)
    relative_velocities: npt.NDArray[np.float32] = np.asarray([[state.x, state.y] for state in relative_states]).astype(np.float32)
    return relative_velocities

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

def __post_init__(self) -> None:
    """Sanitize attributes of dataclass."""
    self.num_map_channels = 2
    self.ego_agent_sep_channel_num = int((self.num_channels() - self.num_map_channels) // 2)
    shape = self.data.shape
    array_dims = len(shape)
    if array_dims != 3 and array_dims != 4:
        raise RuntimeError(f'Invalid raster array. Expected 3 or 4 dims, got {array_dims}.')

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

def _get_layer_coords(agent: AgentState, map_api: AbstractMap, map_layer_name: SemanticMapLayer, map_layer_geometry: str, radius: float) -> Tuple[List[npt.NDArray[np.float64]], List[str]]:
    """
    Construct the map layer of the raster by converting vector map to raster map, based on the focus agent.
    :param agent: the focus agent used for raster generating.
    :param map_api: map api
    :param map_layer_name: name of the vector map layer to create a raster from.
    :param map_layer_geometry: geometric primitive of the vector map layer. i.e. either polygon or linestring.
    :param radius: [m] the radius of the square raster map.
    :return
        object_coords: the list of 2d coordinates which represent the shape of the map.
        lane_ids: the list of ids for the map objects.
    """
    ego_position = Point2D(agent.center.x, agent.center.y)
    nearest_vector_map = map_api.get_proximal_map_objects(layers=[map_layer_name], point=ego_position, radius=radius)
    geometry = nearest_vector_map[map_layer_name]
    if len(geometry):
        global_transform = np.linalg.inv(agent.center.as_matrix())
        map_align_transform = R.from_euler('z', 90, degrees=True).as_matrix().astype(np.float32)
        transform = map_align_transform @ global_transform
        if map_layer_geometry == 'polygon':
            _object_coords = _polygon_to_coords(geometry)
        elif map_layer_geometry == 'linestring':
            _object_coords = _linestring_to_coords(geometry)
        else:
            raise RuntimeError(f'Layer geometry {map_layer_geometry} type not supported')
        object_coords: List[npt.NDArray[np.float64]] = [np.vstack(coords).T for coords in _object_coords]
        object_coords = [(transform @ _cartesian_to_projective_coords(coords).T).T[:, :2] for coords in object_coords]
        lane_ids = [lane.id for lane in geometry]
    else:
        object_coords = []
        lane_ids = []
    return (object_coords, lane_ids)

def _draw_polygon_image(image: npt.NDArray[np.float32], object_coords: List[npt.NDArray[np.float64]], radius: float, resolution: float, color: float, bit_shift: int=12) -> npt.NDArray[np.float32]:
    """
    Draw a map feature consisting of polygons using a list of its coordinates.
    :param image: the raster map on which the map feature will be drawn
    :param object_coords: the coordinates that represents the shape of the map feature.
    :param radius: the radius of the square raster map.
    :param resolution: [m] pixel size in meters.
    :param color: color of the map feature.
    :param bit_shift: bit shift of the polygon used in opencv.
    :return: the resulting raster map with the map feature.
    """
    if len(object_coords):
        for coords in object_coords:
            index_coords = (radius + coords) / resolution
            shifted_index_coords = (index_coords * 2 ** bit_shift).astype(np.int64)
            cv2.fillPoly(image, shifted_index_coords[None], color=color, shift=bit_shift, lineType=cv2.LINE_AA)
    return image

def _draw_linestring_image(image: npt.NDArray[np.float32], object_coords: List[npt.NDArray[np.float64]], radius: float, resolution: float, baseline_path_thickness: int, lane_colors: npt.NDArray[np.uint8], bit_shift: int=13) -> npt.NDArray[np.float32]:
    """
    Draw a map feature consisting of linestring using a list of its coordinates.
    :param image: the raster map on which the map feature will be drawn
    :param object_coords: the coordinates that represents the shape of the map feature.
    :param radius: the radius of the square raster map.
    :param resolution: [m] pixel size in meters.
    :param baseline_path_thickness: [pixel] the thickness of polylines used in opencv.
    :param lane_colors: an array indicate colors for each element of object_coords.
    :param bit_shift: bit shift of the polylines used in opencv.
    :return: the resulting raster map with the map feature.
    """
    if len(object_coords):
        assert len(object_coords) == len(lane_colors)
        for coords, lane_color in zip(object_coords, lane_colors):
            index_coords = (radius + coords) / resolution
            shifted_index_coords = (index_coords * 2 ** bit_shift).astype(np.int64)
            lane_color = int(lane_color) if np.isscalar(lane_color) else [int(item) for item in lane_color]
            cv2.polylines(image, [shifted_index_coords], isClosed=False, color=lane_color, thickness=baseline_path_thickness, shift=bit_shift, lineType=cv2.LINE_AA)
    return image

def get_roadmap_raster(focus_agent: AgentState, map_api: AbstractMap, map_features: Dict[str, int], x_range: Tuple[float, float], y_range: Tuple[float, float], raster_shape: Tuple[int, int], resolution: float) -> npt.NDArray[np.float32]:
    """
    Construct the map layer of the raster by converting vector map to raster map.
    :param focus_agent: agent state representing ego.
    :param map_api: map api.
    :param map_features: name of map features to be drawn and its color for encoding.
    :param x_range: [m] min and max range from the edges of the grid in x direction.
    :param y_range: [m] min and max range from the edges of the grid in y direction.
    :param raster_shape: shape of the target raster.
    :param resolution: [m] pixel size in meters.
    :return roadmap_raster: the constructed map raster layer.
    """
    assert x_range[1] - x_range[0] == y_range[1] - y_range[0], f'Raster shape is assumed to be square but got width:             {y_range[1] - y_range[0]} and height: {x_range[1] - x_range[0]}'
    radius = (x_range[1] - x_range[0]) / 2
    roadmap_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    for feature_name, feature_color in map_features.items():
        coords, _ = _get_layer_coords(focus_agent, map_api, SemanticMapLayer[feature_name], 'polygon', radius)
        roadmap_raster = _draw_polygon_image(roadmap_raster, coords, radius, resolution, feature_color)
    roadmap_raster = np.flip(roadmap_raster, axis=0)
    roadmap_raster = np.ascontiguousarray(roadmap_raster, dtype=np.float32)
    return roadmap_raster

def get_agents_raster(ego_state: EgoState, detections: DetectionsTracks, x_range: Tuple[float, float], y_range: Tuple[float, float], raster_shape: Tuple[int, int], polygon_bit_shift: int=9) -> npt.NDArray[np.float32]:
    """
    Construct the agents layer of the raster by transforming all detected boxes around the agent
    and creating polygons of them in a raster grid.
    :param ego_state: SE2 state of ego.
    :param detections: list of 3D bounding box of detected agents.
    :param x_range: [m] min and max range from the edges of the grid in x direction.
    :param y_range: [m] min and max range from the edges of the grid in y direction.
    :param raster_shape: shape of the target raster.
    :param polygon_bit_shift: bit shift of the polygon used in opencv.
    :return: constructed agents raster layer.
    """
    xmin, xmax = x_range
    ymin, ymax = y_range
    width, height = raster_shape
    agents_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    ego_to_global = ego_state.rear_axle.as_matrix()
    global_to_ego = np.linalg.inv(ego_to_global)
    north_aligned_transform = StateSE2(0, 0, np.pi / 2).as_matrix()
    tracked_objects = [deepcopy(tracked_object) for tracked_object in detections.tracked_objects]
    for tracked_object in tracked_objects:
        raster_object_matrix = north_aligned_transform @ global_to_ego @ tracked_object.center.as_matrix()
        raster_object_pose = StateSE2.from_matrix(raster_object_matrix)
        valid_x = x_range[0] < raster_object_pose.x < x_range[1]
        valid_y = y_range[0] < raster_object_pose.y < y_range[1]
        if not (valid_x and valid_y):
            continue
        raster_oriented_box = OrientedBox(raster_object_pose, tracked_object.box.length, tracked_object.box.width, tracked_object.box.height)
        box_bottom_corners = raster_oriented_box.all_corners()
        x_corners = np.asarray([corner.x for corner in box_bottom_corners])
        y_corners = np.asarray([corner.y for corner in box_bottom_corners])
        y_corners = (y_corners - ymin) / (ymax - ymin) * height
        x_corners = (x_corners - xmin) / (xmax - xmin) * width
        box_2d_coords = np.stack([x_corners, y_corners], axis=1)
        box_2d_coords = np.expand_dims(box_2d_coords, axis=0)
        box_2d_coords = (box_2d_coords * 2 ** polygon_bit_shift).astype(np.int32)
        cv2.fillPoly(agents_raster, box_2d_coords, color=1.0, shift=polygon_bit_shift, lineType=cv2.LINE_AA)
    agents_raster = np.asarray(agents_raster)
    agents_raster = np.flip(agents_raster, axis=0)
    agents_raster = np.ascontiguousarray(agents_raster, dtype=np.float32)
    return agents_raster

def get_non_focus_agents_raster(focus_agent: AgentState, other_agents: List[Agent], x_range: Tuple[float, float], y_range: Tuple[float, float], raster_shape: Tuple[int, int], polygon_bit_shift: int=9) -> npt.NDArray[np.float32]:
    """
    Construct the agents layer of the raster by transforming all other agents around the focus agent
    and creating polygons of them in a raster grid.
    :param focus_agent: focus agent used for rasterization.
    :param other agents: list of agents including the ego AV but excluding the focus agent.
    :param x_range: [m] min and max range from the edges of the grid in x direction.
    :param y_range: [m] min and max range from the edges of the grid in y direction.
    :param raster_shape: shape of the target raster.
    :param polygon_bit_shift: bit shift of the polygon used in opencv.
    :return: constructed agents raster layer.
    """
    xmin, xmax = x_range
    ymin, ymax = y_range
    width, height = raster_shape
    agents_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    ego_to_global = focus_agent.center.as_matrix()
    global_to_ego = np.linalg.inv(ego_to_global)
    north_aligned_transform = StateSE2(0, 0, np.pi / 2).as_matrix()
    for tracked_object in other_agents:
        raster_object_matrix = north_aligned_transform @ global_to_ego @ tracked_object.center.as_matrix()
        raster_object_pose = StateSE2.from_matrix(raster_object_matrix)
        valid_x = x_range[0] < raster_object_pose.x < x_range[1]
        valid_y = y_range[0] < raster_object_pose.y < y_range[1]
        if not (valid_x and valid_y):
            continue
        raster_oriented_box = OrientedBox(raster_object_pose, tracked_object.box.length, tracked_object.box.width, tracked_object.box.height)
        box_bottom_corners = raster_oriented_box.all_corners()
        x_corners = np.asarray([corner.x for corner in box_bottom_corners])
        y_corners = np.asarray([corner.y for corner in box_bottom_corners])
        y_corners = (y_corners - ymin) / (ymax - ymin) * height
        x_corners = (x_corners - xmin) / (xmax - xmin) * width
        box_2d_coords = np.stack([x_corners, y_corners], axis=1)
        box_2d_coords = np.expand_dims(box_2d_coords, axis=0)
        box_2d_coords = (box_2d_coords * 2 ** polygon_bit_shift).astype(np.int32)
        cv2.fillPoly(agents_raster, box_2d_coords, color=1.0, shift=polygon_bit_shift, lineType=cv2.LINE_AA)
    agents_raster = np.asarray(agents_raster)
    agents_raster = np.flip(agents_raster, axis=0)
    agents_raster = np.ascontiguousarray(agents_raster, dtype=np.float32)
    return agents_raster

def get_baseline_paths_raster(focus_agent: AgentState, map_api: AbstractMap, x_range: Tuple[float, float], y_range: Tuple[float, float], raster_shape: Tuple[int, int], resolution: float, baseline_path_thickness: int=1) -> npt.NDArray[np.float32]:
    """
    Construct the baseline paths layer by converting vector map to raster map.
    This funciton is for ego raster model, the baselin path only has one channel.
    :param ego_state: SE2 state of ego.
    :param map_api: map api
    :param x_range: [m] min and max range from the edges of the grid in x direction.
    :param y_range: [m] min and max range from the edges of the grid in y direction.
    :param raster_shape: shape of the target raster.
    :param resolution: [m] pixel size in meters.
    :param baseline_path_thickness: [pixel] the thickness of polylines used in opencv.
    :return baseline_paths_raster: the constructed baseline paths layer.
    """
    if x_range[1] - x_range[0] != y_range[1] - y_range[0]:
        raise ValueError(f'Raster shape is assumed to be square but got width:             {y_range[1] - y_range[0]} and height: {x_range[1] - x_range[0]}')
    radius = (x_range[1] - x_range[0]) / 2
    baseline_paths_raster: npt.NDArray[np.float32] = np.zeros(raster_shape, dtype=np.float32)
    for map_features in ['LANE', 'LANE_CONNECTOR']:
        baseline_paths_coords, lane_ids = _get_layer_coords(agent=focus_agent, map_api=map_api, map_layer_name=SemanticMapLayer[map_features], map_layer_geometry='linestring', radius=radius)
        lane_colors: npt.NDArray[np.uint8] = np.ones(len(lane_ids)).astype(np.uint8)
        baseline_paths_raster = _draw_linestring_image(image=baseline_paths_raster, object_coords=baseline_paths_coords, radius=radius, resolution=resolution, baseline_path_thickness=baseline_path_thickness, lane_colors=lane_colors)
    baseline_paths_raster = np.flip(baseline_paths_raster, axis=0)
    baseline_paths_raster = np.ascontiguousarray(baseline_paths_raster, dtype=np.float32)
    return baseline_paths_raster

def get_baseline_paths_agents_raster(focus_agent: AgentState, map_api: AbstractMap, x_range: Tuple[float, float], y_range: Tuple[float, float], raster_shape: Tuple[int, int], resolution: float, traffic_light_connectors: Dict[TrafficLightStatusType, List[str]], baseline_path_thickness: int=1) -> npt.NDArray[np.float32]:
    """
    Construct the baseline paths layer by converting vector map to raster map.
    This function is for agents raster model, it has 3 channels for baseline path.
    :param focus_agent: agent state representing ego.
    :param map_api: map api
    :param x_range: [m] min and max range from the edges of the grid in x direction.
    :param y_range: [m] min and max range from the edges of the grid in y direction.
    :param raster_shape: shape of the target raster.
    :param resolution: [m] pixel size in meters.
    :param traffic_light_connectors: a dict mapping tl status type to a list of lane ids in this status.
    :param baseline_path_thickness: [pixel] the thickness of polylines used in opencv.
    :return baseline_paths_raster: the constructed baseline paths layer.
    """
    if x_range[1] - x_range[0] != y_range[1] - y_range[0]:
        raise ValueError(f'Raster shape is assumed to be square but got width:             {y_range[1] - y_range[0]} and height: {x_range[1] - x_range[0]}')
    radius = (x_range[1] - x_range[0]) / 2
    baseline_paths_raster: npt.NDArray[np.float32] = np.zeros((*raster_shape, 3), dtype=np.float32)
    for map_features in ['LANE', 'LANE_CONNECTOR']:
        baseline_paths_coords, lane_ids = _get_layer_coords(agent=focus_agent, map_api=map_api, map_layer_name=SemanticMapLayer[map_features], map_layer_geometry='linestring', radius=radius)
        lane_ids = np.asarray(lane_ids)
        lane_colors: npt.NDArray[np.uint8] = np.full((len(lane_ids), 3), BASELINE_TL_COLOR[TrafficLightStatusType.UNKNOWN], dtype=np.uint8)
        if len(traffic_light_connectors) > 0:
            for tl_status in TrafficLightStatusType:
                if tl_status != TrafficLightStatusType.UNKNOWN and len(traffic_light_connectors[tl_status]) > 0:
                    lanes_in_tl_status = np.isin(lane_ids, traffic_light_connectors[tl_status])
                    lane_colors[lanes_in_tl_status] = BASELINE_TL_COLOR[tl_status]
        baseline_paths_raster = _draw_linestring_image(image=baseline_paths_raster, object_coords=baseline_paths_coords, radius=radius, resolution=resolution, baseline_path_thickness=baseline_path_thickness, lane_colors=lane_colors)
    baseline_paths_raster = np.flip(baseline_paths_raster, axis=0)
    baseline_paths_raster = np.ascontiguousarray(baseline_paths_raster, dtype=np.float32)
    return baseline_paths_raster

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

def has_agents(self, batch_idx: int) -> bool:
    """
        Check whether agents exist in the feature.
        :param batch_idx: the batch index of interest
        :return: whether agents exist in the feature
        """
    return self.num_agents_in_sample(batch_idx) > 0

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
def numpy_position_x(self) -> FeatureDataType:
    """
        Array of x positions of trajectory.
        """
    return np.asarray(self.data[..., 0])

@property
def numpy_position_y(self) -> FeatureDataType:
    """
        Array of y positions of trajectory.
        """
    return np.asarray(self.data[..., 1])

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

class TestRasterUtils(unittest.TestCase):
    """Test raster building utility functions."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        scenario = get_test_nuplan_scenario()
        self.x_range = [-56.0, 56.0]
        self.y_range = [-56.0, 56.0]
        self.raster_shape = (224, 224)
        self.resolution = 0.5
        self.thickness = 2
        self.ego_state = scenario.initial_ego_state
        self.map_api = scenario.map_api
        self.tracked_objects = scenario.initial_tracked_objects
        self.map_features = {'LANE': 255, 'INTERSECTION': 255, 'STOP_LINE': 128, 'CROSSWALK': 128}
        ego_width = 2.297
        ego_front_length = 4.049
        ego_rear_length = 1.127
        self.ego_longitudinal_offset = 0.0
        self.ego_width_pixels = int(ego_width / self.resolution)
        self.ego_front_length_pixels = int(ego_front_length / self.resolution)
        self.ego_rear_length_pixels = int(ego_rear_length / self.resolution)

    def test_get_roadmap_raster(self) -> None:
        """
        Test get_roadmap_raster / get_agents_raster / get_baseline_paths_raster
        """
        self.assertGreater(len(self.tracked_objects.tracked_objects), 0)
        roadmap_raster = get_roadmap_raster(self.ego_state, self.map_api, self.map_features, self.x_range, self.y_range, self.raster_shape, self.resolution)
        agents_raster = get_agents_raster(self.ego_state, self.tracked_objects, self.x_range, self.y_range, self.raster_shape)
        ego_raster = get_ego_raster(self.raster_shape, self.ego_longitudinal_offset, self.ego_width_pixels, self.ego_front_length_pixels, self.ego_rear_length_pixels)
        baseline_paths_raster = get_baseline_paths_raster(self.ego_state, self.map_api, self.x_range, self.y_range, self.raster_shape, self.resolution, self.thickness)
        self.assertEqual(roadmap_raster.shape, self.raster_shape)
        self.assertEqual(agents_raster.shape, self.raster_shape)
        self.assertEqual(ego_raster.shape, self.raster_shape)
        self.assertEqual(baseline_paths_raster.shape, self.raster_shape)
        self.assertTrue(np.any(roadmap_raster))
        self.assertTrue(np.any(agents_raster))
        self.assertTrue(np.any(ego_raster))
        self.assertTrue(np.any(baseline_paths_raster))

def test_get_roadmap_raster(self) -> None:
    """
        Test get_roadmap_raster / get_agents_raster / get_baseline_paths_raster
        """
    self.assertGreater(len(self.tracked_objects.tracked_objects), 0)
    roadmap_raster = get_roadmap_raster(self.ego_state, self.map_api, self.map_features, self.x_range, self.y_range, self.raster_shape, self.resolution)
    agents_raster = get_agents_raster(self.ego_state, self.tracked_objects, self.x_range, self.y_range, self.raster_shape)
    ego_raster = get_ego_raster(self.raster_shape, self.ego_longitudinal_offset, self.ego_width_pixels, self.ego_front_length_pixels, self.ego_rear_length_pixels)
    baseline_paths_raster = get_baseline_paths_raster(self.ego_state, self.map_api, self.x_range, self.y_range, self.raster_shape, self.resolution, self.thickness)
    self.assertEqual(roadmap_raster.shape, self.raster_shape)
    self.assertEqual(agents_raster.shape, self.raster_shape)
    self.assertEqual(ego_raster.shape, self.raster_shape)
    self.assertEqual(baseline_paths_raster.shape, self.raster_shape)
    self.assertTrue(np.any(roadmap_raster))
    self.assertTrue(np.any(agents_raster))
    self.assertTrue(np.any(ego_raster))
    self.assertTrue(np.any(baseline_paths_raster))

def _extract_serialization_type(first_file: pathlib.Path) -> str:
    """
    Deduce the serialization type
    :param first_file: serialized file
    :return: one from ["msgpack", "pickle", "json"].
    """
    msg_pack = first_file.suffixes == ['.msgpack', '.xz']
    msg_pickle = first_file.suffixes == ['.pkl', '.xz']
    msg_json = first_file.suffix == '.json'
    number_of_available_types = int(msg_pack) + int(msg_json) + int(msg_pickle)
    if number_of_available_types != 1:
        raise RuntimeError(f'Inconclusive file type: {first_file}!')
    if msg_pickle:
        return 'pickle'
    elif msg_json:
        return 'json'
    elif msg_pack:
        return 'msgpack'
    else:
        raise RuntimeError('Unknown condition!')

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

class WeightedAverageMetricAggregator(AbstractMetricAggregator):
    """Metric aggregator by implementing weighted sum."""

    def __init__(self, name: str, metric_weights: Dict[str, float], file_name: str, aggregator_save_path: Path, multiple_metrics: List[str], challenge_name: Optional[str]=None):
        """
        Initializes the WeightedAverageMetricAggregator class.
        :param name: Metric aggregator name.
        :param metric_weights: Weights for each metric. Default would be 1.0.
        :param file_name: Saved file name.
        :param aggregator_save_path: Save path for this aggregated parquet file.
        :param multiple_metrics: A list if metric names used in multiple factor when computing scenario scores.
        :param challenge_name: Optional, name of the challenge the metrics refer to, if set will be part of the
        output file name and path.
        """
        self._name = name
        self._metric_weights = metric_weights
        self._file_name = file_name
        if not self._file_name.endswith('.parquet'):
            self._file_name += '.parquet'
        self._aggregator_save_path = aggregator_save_path
        self._challenge_name = challenge_name
        if not is_s3_path(self._aggregator_save_path):
            self._aggregator_save_path.mkdir(exist_ok=True, parents=True)
        self._aggregator_type = 'weighted_average'
        self._multiple_metrics = multiple_metrics
        self._parquet_file = self._aggregator_save_path / self._file_name
        self._aggregated_metric_dataframe: Optional[pandas.DataFrame] = None

    @property
    def aggregated_metric_dataframe(self) -> Optional[pandas.DataFrame]:
        """Return the aggregated metric dataframe."""
        return self._aggregated_metric_dataframe

    @property
    def name(self) -> str:
        """
        Return the metric aggregator name.
        :return the metric aggregator name.
        """
        return self._name

    @property
    def final_metric_score(self) -> Optional[float]:
        """Return the final metric score."""
        if self._aggregated_metric_dataframe is not None:
            return self._aggregated_metric_dataframe.iloc[-1, -1]
        else:
            logger.warning('The metric not yet aggregated.')
            return None

    def _get_metric_weight(self, metric_name: str) -> float:
        """
        Get metric weights.
        :param metric_name: The metric name.
        :return Weight for the metric.
        """
        weight: Optional[float] = self._metric_weights.get(metric_name, None)
        metric_weight = self._metric_weights.get('default', 1.0) if weight is None else weight
        return metric_weight

    def _compute_scenario_score(self, scenario_metric_columns: metric_aggregator_dict_column) -> None:
        """
        Compute scenario scores.
        :param scenario_metric_columns: Scenario metric column in the format of {scenario_names: {metric_column:
        value}}.
        """
        excluded_columns = ['log_name', 'planner_name', 'aggregator_type', 'scenario_type', 'num_scenarios', 'score']
        for scenario_name, columns in scenario_metric_columns.items():
            metric_scores = 0.0
            sum_weights = 0.0
            multiple_factor = 1.0
            for column_key, column_value in columns.items():
                if column_key in excluded_columns or column_value is None:
                    continue
                if self._multiple_metrics and column_key in self._multiple_metrics:
                    multiple_factor *= column_value
                else:
                    weight = self._get_metric_weight(metric_name=column_key)
                    assert column_value is not None, f'Metric: {column_key} value should not be None!'
                    assert weight is not None, f'Metric: {column_key} weight should not be None!'
                    sum_weights += weight
                    metric_scores += weight * column_value
            weighted_average_score = metric_scores / sum_weights if sum_weights else 0.0
            final_score = multiple_factor * weighted_average_score
            scenario_metric_columns[scenario_name]['score'] = final_score

    @staticmethod
    def _group_scenario_type_metric(scenario_metric_columns: metric_aggregator_dict_column) -> metric_aggregator_dict_column:
        """
        Group scenario type metric columns in the format of {scenario_type: {metric_columns: value}}.
        :param scenario_metric_columns: Scenario metric columns in the format of {scenario_name: {metric_columns:
        value}}.
        :return Metric columns based on scenario type.
        """
        scenario_type_dicts: metric_aggregator_dict_column = defaultdict(lambda: defaultdict(list))
        total_scenarios = len(scenario_metric_columns)
        for scenario_name, columns in scenario_metric_columns.items():
            scenario_type = columns['scenario_type']
            scenario_type_dicts[scenario_type]['scenario_name'].append(scenario_name)
            for column_key, column_value in columns.items():
                scenario_type_dicts[scenario_type][column_key].append(column_value)
        common_columns = ['planner_name', 'aggregator_type', 'scenario_type']
        excluded_columns = ['scenario_name']
        scenario_type_metric_columns: metric_aggregator_dict_column = defaultdict(lambda: defaultdict())
        for scenario_type, columns in scenario_type_dicts.items():
            for key, values in columns.items():
                if key in excluded_columns:
                    continue
                elif key in common_columns:
                    scenario_type_metric_columns[scenario_type][key] = values[0]
                elif key == 'log_name':
                    scenario_type_metric_columns[scenario_type][key] = None
                elif key == 'num_scenarios':
                    scenario_type_metric_columns[scenario_type]['num_scenarios'] = len(values)
                else:
                    available_values: npt.NDArray[np.float64] = np.asarray([value for value in values if value is not None])
                    value: Optional[float] = float(np.sum(available_values)) if available_values.size > 0 else None
                    if key == 'score' and value is not None:
                        score_value: float = value / len(values) if total_scenarios else 0.0
                        scenario_type_metric_columns[scenario_type][key] = score_value
                    else:
                        scenario_type_metric_columns[scenario_type][key] = value
        return scenario_type_metric_columns

    @staticmethod
    def _group_final_score_metric(scenario_type_metric_columns: metric_aggregator_dict_column) -> metric_aggregator_dict_column:
        """
        Compute a final score based on a group of scenario types.
        :param scenario_type_metric_columns: Scenario type metric columns in the format of {scenario_type:
        {metric_column: value}}.
        :return A dictionary of final score in the format of {'final_score': {metric_column: value}}.
        """
        final_score_dicts: metric_aggregator_dict_column = defaultdict(lambda: defaultdict(list))
        for scenario_type, columns in scenario_type_metric_columns.items():
            for column_key, column_value in columns.items():
                final_score_dicts['final_score'][column_key].append(column_value)
        final_score_metric_columns: metric_aggregator_dict_column = defaultdict(lambda: defaultdict())
        total_scenarios = sum(final_score_dicts['final_score']['num_scenarios'])
        common_columns = ['planner_name', 'aggregator_type']
        for final_score_column_name, columns in final_score_dicts.items():
            for key, values in columns.items():
                if key == 'scenario_type':
                    final_score_metric_columns[final_score_column_name][key] = 'final_score'
                elif key == 'log_name':
                    final_score_metric_columns[final_score_column_name][key] = None
                elif key in common_columns:
                    final_score_metric_columns[final_score_column_name][key] = values[0]
                elif key == 'num_scenarios':
                    final_score_metric_columns[final_score_column_name][key] = total_scenarios
                else:
                    available_values: List[float] = []
                    if key == 'score':
                        for value, num_scenario in zip(values, columns['num_scenarios']):
                            if value is not None:
                                available_values.append(value * num_scenario)
                    else:
                        available_values = [value for value in values if value is not None]
                    if not available_values:
                        total_values = None
                    else:
                        available_value_array: npt.NDArray[np.float64] = np.asarray(available_values)
                        total_values = np.sum(available_value_array) / total_scenarios
                    final_score_metric_columns[final_score_column_name][key] = total_values
        return final_score_metric_columns

    def _group_scenario_metrics(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame], planner_name: str) -> metric_aggregator_dict_column:
        """
        Group scenario metrics in the format of {scenario_name: {metric_column: value}}.
        :param metric_dataframes: A dict of metric dataframes.
        :param planner_name: A planner name.
        :return Dictionary column format in metric aggregator in {scenario_name: {metric_column: value}}.
        """
        metric_names = sorted(list(metric_dataframes.keys()))
        columns = {column: None for column in ['log_name', 'planner_name', 'aggregator_type', 'scenario_type', 'num_scenarios'] + metric_names + ['score']}
        scenario_metric_columns: metric_aggregator_dict_column = {}
        for metric_name, metric_dataframe in metric_dataframes.items():
            dataframe = metric_dataframe.query_scenarios(planner_names=tuple([planner_name]))
            for _, data in dataframe.iterrows():
                scenario_name = data.get('scenario_name')
                if scenario_name not in scenario_metric_columns:
                    scenario_metric_columns[scenario_name] = deepcopy(columns)
                scenario_type = data['scenario_type']
                scenario_metric_columns[scenario_name]['log_name'] = data['log_name']
                scenario_metric_columns[scenario_name]['planner_name'] = data['planner_name']
                scenario_metric_columns[scenario_name]['scenario_type'] = scenario_type
                scenario_metric_columns[scenario_name]['aggregator_type'] = self._aggregator_type
                scenario_metric_columns[scenario_name][metric_name] = data['metric_score']
        return scenario_metric_columns

    def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
        """
        Run an aggregator to generate an aggregated parquet file.
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
        planner_names = sorted(list({planner_name for metric_statistic_dataframe in metric_dataframes.values() for planner_name in metric_statistic_dataframe.planner_names}))
        weighted_average_dataframe_columns: Dict[str, List[Any]] = dict()
        for planner_name in planner_names:
            metric_names = sorted(list(metric_dataframes.keys())) + ['score']
            dataframe_columns: Dict[str, List[Any]] = {'scenario': [], 'log_name': [], 'scenario_type': [], 'num_scenarios': [], 'planner_name': [], 'aggregator_type': []}
            metric_name_columns: Dict[str, List[float]] = {metric_name: [] for metric_name in metric_names}
            dataframe_columns.update(metric_name_columns)
            scenario_metric_columns = self._group_scenario_metrics(metric_dataframes=metric_dataframes, planner_name=planner_name)
            self._compute_scenario_score(scenario_metric_columns=scenario_metric_columns)
            scenario_type_metric_columns = self._group_scenario_type_metric(scenario_metric_columns=scenario_metric_columns)
            scenario_type_final_metric_columns = self._group_final_score_metric(scenario_type_metric_columns=scenario_type_metric_columns)
            scenario_metric_columns.update(scenario_type_metric_columns)
            scenario_metric_columns.update(scenario_type_final_metric_columns)
            for scenario_name, columns in scenario_metric_columns.items():
                dataframe_columns['scenario'].append(scenario_name)
                for key, value in columns.items():
                    dataframe_columns[key].append(value)
            if not weighted_average_dataframe_columns:
                weighted_average_dataframe_columns.update(dataframe_columns)
            else:
                for column_name, value in weighted_average_dataframe_columns.items():
                    value += dataframe_columns[column_name]
        self._aggregated_metric_dataframe = pandas.DataFrame(data=weighted_average_dataframe_columns)
        self._save_parquet(dataframe=self._aggregated_metric_dataframe, save_path=self._parquet_file)

    def read_parquet(self) -> None:
        """Read a parquet file."""
        self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

    @property
    def parquet_file(self) -> Path:
        """Inherited, see superclass"""
        return self._parquet_file

    @property
    def challenge(self) -> Optional[str]:
        """Inherited, see superclass"""
        return self._challenge_name

@staticmethod
def _group_final_score_metric(scenario_type_metric_columns: metric_aggregator_dict_column) -> metric_aggregator_dict_column:
    """
        Compute a final score based on a group of scenario types.
        :param scenario_type_metric_columns: Scenario type metric columns in the format of {scenario_type:
        {metric_column: value}}.
        :return A dictionary of final score in the format of {'final_score': {metric_column: value}}.
        """
    final_score_dicts: metric_aggregator_dict_column = defaultdict(lambda: defaultdict(list))
    for scenario_type, columns in scenario_type_metric_columns.items():
        for column_key, column_value in columns.items():
            final_score_dicts['final_score'][column_key].append(column_value)
    final_score_metric_columns: metric_aggregator_dict_column = defaultdict(lambda: defaultdict())
    total_scenarios = sum(final_score_dicts['final_score']['num_scenarios'])
    common_columns = ['planner_name', 'aggregator_type']
    for final_score_column_name, columns in final_score_dicts.items():
        for key, values in columns.items():
            if key == 'scenario_type':
                final_score_metric_columns[final_score_column_name][key] = 'final_score'
            elif key == 'log_name':
                final_score_metric_columns[final_score_column_name][key] = None
            elif key in common_columns:
                final_score_metric_columns[final_score_column_name][key] = values[0]
            elif key == 'num_scenarios':
                final_score_metric_columns[final_score_column_name][key] = total_scenarios
            else:
                available_values: List[float] = []
                if key == 'score':
                    for value, num_scenario in zip(values, columns['num_scenarios']):
                        if value is not None:
                            available_values.append(value * num_scenario)
                else:
                    available_values = [value for value in values if value is not None]
                if not available_values:
                    total_values = None
                else:
                    available_value_array: npt.NDArray[np.float64] = np.asarray(available_values)
                    total_values = np.sum(available_value_array) / total_scenarios
                final_score_metric_columns[final_score_column_name][key] = total_values
    return final_score_metric_columns

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

