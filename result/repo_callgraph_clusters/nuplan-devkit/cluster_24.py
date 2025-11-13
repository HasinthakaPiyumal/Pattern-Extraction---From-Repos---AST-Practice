# Cluster 24

def render_pc(sample_data: LidarPc, with_anns: bool=True, view_3d: npt.NDArray[np.float64]=np.eye(4), axes_limit: float=40, ax: Optional[Axes]=None, title: Optional[str]=None) -> None:
    """
    This is a naive rendering of the Lidar pointclouds with appropriate boxes. This is naive in the sense that it
    only renders the points but not the velocity associated with those points.
    :param sample_data: The Lidar pointcloud.
        Note: Having the type Union[LidarPc] for this throws error for TRT with Python 3.5.
    :param with_anns: Whether you want to render the annotations?
    :param view_3d: <np.float: 4, 4>. Define a projection needed (e.g. for drawing projection in an image).
    :param axes_limit: The range of that will be rendered will be between (-axes_limit, axes_limit).
    :param ax: Axes object or array of Axes objects.
    :param title: Title of the plot you want to render.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(9, 9))
    points = view_points(sample_data.load().points[:3, :], view_3d, normalize=False)
    ax.scatter(points[0, :], points[1, :], c=points[2, :], s=2)
    if with_anns:
        for box in sample_data.boxes(Frame.SENSOR):
            ann_record = sample_data.lidar_box[box.payload]
            if not ann_record.track:
                logger.error('Wrong 3d instance mapping', ann_record)
                c: npt.NDArray[np.float64] = np.array([128, 0, 128]) / 255.0
            else:
                c = ann_record.track.category.color_np
            color = (c, c, np.array([0, 0, 0]))
            box.render(ax, view=view_3d, colors=color)
    ax.set_xlim(-axes_limit, axes_limit)
    ax.set_ylim(-axes_limit, axes_limit)
    ax.set_title('{}'.format(title))

def draw_future_ego_poses(ego_box: Box3D, ego_poses_np: npt.NDArray, color: Tuple[float, float, float], ax: Union[npt.NDArray[np.float64], Axes]) -> None:
    """
    Draw Future Ego Poses
    :param ego_box: Ego Vehicle Box.
    :param ego_poses_np: Numpy array containing future Ego Poses.
    :param color: Color to use.
    :param ax: Canvas to draw.
    """
    prev_x, prev_y = (ego_box.center[0], ego_box.center[1])
    for idx in range(1, ego_poses_np.shape[0]):
        next_x, next_y = (ego_poses_np[idx, 0], ego_poses_np[idx, 1])
        alpha = max(1.0 - idx * 0.1, 0.1)
        draw_line(from_x=prev_x, to_x=next_x, from_y=prev_y, to_y=next_y, color=color, marker='o', linewidth=1.0, canvas=ax, alpha=alpha)
        prev_x, prev_y = (next_x, next_y)

def render_on_map(lidarpc_rec: LidarPc, db: NuPlanDB, boxes_lidar: List[Box3D], ego_poses: List[EgoPose], points_to_render: Optional[npt.NDArray[np.float64]]=None, radius: float=80.0, ax: Axes=None, labelmap: Optional[Dict[int, Label]]=None, render_boxes_with_velocity: bool=False, render_map_raster: bool=False, render_vector_map: bool=False, track_token: Optional[str]=None, with_random_color: bool=False, render_future_ego_poses: bool=False) -> plt.axes:
    """
    This function is used to render a LidarPC and boxes (in the lidar frame) on the map.
    :param lidarpc_rec: LidarPc record from NuPlanDB.
    :param db: Log database.
    :param boxes_lidar: List of boxes in the lidar frame.
    :param ego_poses: Ego poses to render.
    :param points_to_render: <np.float: nbr_indices, nbr_points>. If the user wants to visualize only a specific set
        of points (example points from selective rings/drivable area filtered/...) and not the entire pointcloud, they
        can pass those points along. Note that nbr_indices >=2 i.e. the user should at least pass (x, y).
    :param radius: The radius (centered on the Lidar) outside which we won't keep any points or boxes.
    :param ax: Axis on which to render.
    :param labelmap: The labelmap is used to color the boxes. If not provided, default colors from box.render() will be
        used.
    :param render_boxes_with_velocity: Whether you want to show the velocity arrow when you render the box?
    :param render_map_raster: Boolean indicating whether to include visualization of map layers from rasterized map.
    :param render_vector_map: Boolean indicating whether to include visualization of baseline paths from vector map.
    :param track_token: Which track to render, if it's None, render all the tracks.
    :param with_random_color: Whether to render the instances with different random color.
    :param render_future_ego_poses: Whether to render future EgoPoses.
    :return: plt.axes corresponding to BEV image with specified visualizations.
    """
    xrange = (-radius, radius)
    yrange = (-radius, radius)
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(9, 9))
    intensity_map_crop, intensity_map_translation, intensity_map_scale = lidarpc_rec.ego_pose.get_map_crop(db.maps_db, xrange, yrange, 'intensity', rotate_face_up=True)
    map_translation = intensity_map_translation
    map_scale = intensity_map_scale
    lidar_to_ego = lidarpc_rec.lidar.trans_matrix
    ego_to_global = lidarpc_rec.ego_pose.trans_matrix
    map_align_rot = R.from_matrix(lidarpc_rec.ego_pose.quaternion.rotation_matrix.T)
    map_align_rot_angle = map_align_rot.as_euler('zxy')[0] + math.pi / 2
    map_align_transform = Quaternion(axis=[0, 0, 1], angle=map_align_rot_angle).transformation_matrix
    if render_map_raster:
        map_raster, map_translation, map_scale = lidarpc_rec.ego_pose.get_map_crop(maps_db=db.maps_db, xrange=xrange, yrange=yrange, map_layer_name='drivable_area', rotate_face_up=True)
        ax.imshow(map_raster[::-1, :], cmap='gray')
    elif intensity_map_crop is not None:
        ax.imshow(intensity_map_crop[::-1, :], cmap='gray')
    if intensity_map_crop is not None:
        ax.set_ylim(ax.get_ylim()[::-1])
    pointcloud = lidarpc_rec.load(db)
    if points_to_render is not None:
        pointcloud.points = points_to_render
    keep = np.sqrt(pointcloud.points[0] ** 2 + pointcloud.points[1] ** 2) < radius
    pointcloud.points = pointcloud.points[:, keep]
    global_to_crop = np.array([[map_scale[0], 0, 0, map_translation[0]], [0, map_scale[1], 0, map_translation[1]], [0, 0, map_scale[2], 0], [0, 0, 0, 1]])
    lidar_to_crop = reduce(np.dot, [global_to_crop, ego_to_global, lidar_to_ego, map_align_transform])
    front_length = 4.049
    rear_length = 1.127
    ego_car_length = front_length + rear_length
    ego_car_width = 1.1485 * 2.0
    ego_pose_np = np.array([ego_poses[0].x, ego_poses[0].y, ego_poses[0].z, 1])
    ego_box = Box3D(center=(ego_pose_np[0], ego_pose_np[1], ego_pose_np[2]), size=(ego_car_width, ego_car_length, 1.78), orientation=ego_poses[0].quaternion)
    ego_box.transform(ego_poses[0].trans_matrix_inv)
    ego_box.transform(map_align_transform)
    ego_box.transform(lidar_to_ego)
    ego_box.transform(ego_to_global)
    ego_box.scale(map_scale)
    ego_box.translate(map_translation)
    color = (1.0, 0.0, 0.0)
    colors: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float], str]] = (color, color, 'k')
    ego_box.render(ax, colors=colors)
    if render_future_ego_poses:
        ego_poses_np = get_future_ego_trajectory(lidarpc_rec=lidarpc_rec, future_ego_poses=ego_poses, transformmatrix=lidar_to_crop, future_horizon_len_s=6.0, future_interval_s=0.5)
        draw_future_ego_poses(ego_box, ego_poses_np, color, ax)
    if render_vector_map:
        vector_map = lidarpc_rec.ego_pose.get_vector_map(maps_db=db.maps_db, xrange=xrange, yrange=yrange)
        lane_coords = vector_map.coords
        for coords in lane_coords:
            start = np.array([coords[0][0], coords[0][1], 0.0])
            end = np.array([coords[1][0], coords[1][1], 0.0])
            start = transform(start, map_align_transform)
            end = transform(end, map_align_transform)
            start = transform(start, lidar_to_ego)
            end = transform(end, lidar_to_ego)
            start = transform(start, ego_to_global)
            end = transform(end, ego_to_global)
            start = scale(start, map_scale)
            end = scale(end, map_scale)
            start = translate(start, map_translation)
            end = translate(end, map_translation)
            line = geometry.LineString([start[:-1], end[:-1]])
            xx, yy = line.coords.xy
            ax.plot(xx, yy, color='y', alpha=0.3)
    pointcloud.transform(lidar_to_crop)
    ax.scatter(pointcloud.points[0, :], pointcloud.points[1, :], c='g', s=1, alpha=0.2)
    if track_token is None and with_random_color:
        cmap = plt.cm.get_cmap('Dark2', len(boxes_lidar))
    for idx, box in enumerate(boxes_lidar):
        box_copy = box.copy()
        if track_token is not None:
            if box_copy.track_token != track_token:
                continue
        if np.abs(box_copy.center[0]) <= radius and np.abs(box_copy.center[1]) <= radius:
            colors, marker = get_colors_marker(labelmap, box_copy)
            if track_token is None and with_random_color:
                c = np.array(cmap(idx)[:3])
                colors = (c, c, 'k')
            box_copy.transform(map_align_transform)
            box_copy.transform(lidar_to_ego)
            box_copy.transform(ego_to_global)
            box_copy.scale(map_scale)
            box_copy.translate(map_translation)
            box_copy.render(ax, colors=colors, marker=marker, with_velocity=render_boxes_with_velocity)
    ax.axis('off')
    ax.set_aspect('equal')
    plt.tight_layout()
    return ax

def boxes_lidar_to_img(lidar_record: LidarPc, img_record: Image, boxes_lidar: List[Box3D]) -> List[Box3D]:
    """
    This function transforms the boxes in the Lidar frame to the image frame.
    :param lidar_record: The SampleData record for the point cloud.
    :param img_record: The SampleData record for the image.
    :param boxes_lidar: List of boxes in the Lidar frame (given by lidar_record).
    :return: List of boxes in the image frame (given by img_record).
    """
    cam_intrinsic = img_record.camera.intrinsic_np
    imsize = (img_record.camera.width, img_record.camera.height)
    ego_from_lidar = lidar_record.lidar.trans_matrix
    global_from_ego = lidar_record.ego_pose.trans_matrix
    ego_from_global = img_record.ego_pose.trans_matrix_inv
    img_from_ego = img_record.camera.trans_matrix_inv
    trans_matrix = reduce(np.dot, [img_from_ego, ego_from_global, global_from_ego, ego_from_lidar])
    boxes_img = []
    for box in boxes_lidar:
        box = box.copy()
        box.transform(trans_matrix)
        if box_in_image(box, cam_intrinsic, imsize):
            boxes_img.append(box)
    return boxes_img

def load_pointcloud_from_pc(nuplandb: NuPlanDB, token: str, nsweeps: Union[int, List[int]], max_distance: float, min_distance: float, drivable_area: bool=False, map_dilation: float=0.0, use_intensity: bool=True, use_ring: bool=False, use_lidar_index: bool=False, lidar_indices: Optional[Tuple[int, ...]]=None, sample_apillar_lidar_rings: bool=False, sweep_map: str='time_lag') -> LidarPointCloud:
    """
    Loads one or more sweeps of a LIDAR pointcloud from the database using a SampleData record of NuPlanDB.
    :param nuplandb: The multimodal database used in this dataset.
    :param token: Token for the Lidar pointcloud.
    :param nsweeps: The number of past LIDAR sweeps used in the model.
        Alternatively, it is possible to provide a list of relative sweep indices, with:
        - Negative numbers corresponding to past sweeps.
        - 0 corresponding to the present sweep.
        - Positive numbers corresponding to future sweeps.
    :param max_distance: Radius outside which the points will be removed. Helps speed up caching and building the
        GT database.
    :param min_distance: Radius below which near points will be removed. This is usually recommended by the lidar
        manufacturer.
    :param drivable_area: Whether the pointcloud should be filtered based on drivable_area mask.
    :param map_dilation: Map dilation factor in meters.
    :param use_intensity: See prepare_pointcloud_points documentation for details.
    :param use_ring: See prepare_pointcloud_points documentation for details.
    :param use_lidar_index: Whether to use lidar index as a decoration.
    :param lidar_indices: See prepare_pointcloud_points documentation for details.
    :param sample_apillar_lidar_rings: Whether you want to sample rings for the A-pillar lidars.
    :param sweep_map: What to append to the lidar points to give information about what sweep it belongs to.
        Options: 'time_lag' and 'sweep_idx'.
    :return: The pointcloud.
    """
    assert sweep_map in ['time_lag', 'sweep_idx']
    if isinstance(nsweeps, int):
        nsweeps = list(range(-nsweeps + 1, 0 + 1))
    elif isinstance(nsweeps, list):
        assert 0 in nsweeps, f'Error: Present sweep (0) must be included! nsweeps is: {nsweeps}'
    else:
        raise TypeError('Invalid nsweeps type: {}'.format(type(nsweeps)))
    assert sorted(nsweeps) == nsweeps, 'Error: nsweeps must be sorted in ascending order!'
    lidarpc_rec = nuplandb.lidar_pc[token]
    time_current = lidarpc_rec.timestamp
    if len(nsweeps) > 1:
        car_from_lidar = lidarpc_rec.lidar.trans_matrix
        car_from_global = lidarpc_rec.ego_pose.trans_matrix_inv
        lidar_from_car = lidarpc_rec.lidar.trans_matrix_inv
    init = False
    for rel_sweep_idx, sweep_idx in enumerate(nsweeps):
        sweep_lidarpc_rec = _get_past_future_sweep(lidarpc_rec, sweep_idx)
        if sweep_lidarpc_rec is None:
            continue
        sweep_pc = sweep_lidarpc_rec.load(nuplandb)
        sweep_pc = prepare_pointcloud_points(sweep_pc, use_intensity=use_intensity, use_ring=use_ring, use_lidar_index=use_lidar_index, lidar_indices=lidar_indices, sample_apillar_lidar_rings=sample_apillar_lidar_rings)
        sweep_pc.remove_close(min_distance)
        if sweep_idx != 0:
            sweep_pose_rec = sweep_lidarpc_rec.ego_pose
            global_from_car = sweep_pose_rec.trans_matrix
            trans_matrix = reduce(np.dot, [lidar_from_car, car_from_global, global_from_car, car_from_lidar])
            sweep_pc.transform(trans_matrix)
        sweep_pc.radius_filter(max_distance)
        if sweep_map == 'sweep_idx':
            rel_sweep_idx_pixor = np.array(rel_sweep_idx, dtype=np.float32) + 1
            assert rel_sweep_idx_pixor > 0
            sweep_vector = rel_sweep_idx_pixor * np.ones((1, sweep_pc.nbr_points()), dtype=np.float32)
        elif sweep_map == 'time_lag':
            time_lag = time_current - sweep_lidarpc_rec.timestamp if sweep_idx != 0 else 0
            sweep_vector = 1e-06 * time_lag * np.ones((1, sweep_pc.nbr_points()), dtype=np.float32)
        else:
            raise ValueError('Cannot recognize sweep_map type: {}'.format(sweep_map))
        sweep_pc.points = np.concatenate((sweep_pc.points, sweep_vector), axis=0)
        if not init:
            pc: LidarPointCloud = sweep_pc
            init = True
        else:
            pc.points = np.hstack((pc.points, sweep_pc.points))
    return pc

def load_boxes_from_lidarpc(nuplandb: NuPlanDB, lidarpc_rec: LidarPc, target_category_names: List[str], filter_boxes: bool, max_distance: float, future_horizon_len_s: float=0.0, future_interval_s: float=0.5, category2id: Optional[Dict[str, int]]=None, map_dilation: float=0.0) -> Dict[str, List[Box3D]]:
    """
    Load all the boxes for a LidarPc.
    :param nuplandb: The multimodal database used in this dataset.
    :param lidarpc_rec: Lidar sample record.
    :param target_category_names: Global names corresponding to the boxes we are interested in obtaining.
    :param filter_boxes: Whether to filter the boxes to be on the drivable area + dilation factor.
    :param max_distance: Radius outside which the boxes will be removed. Helps speed up caching and building the
        GT database.
    :param future_horizon_len_s: Num seconds in the future where we want a future box.
        If a value is provided, the center coordinates and orientation for each box will be provided at 0.5 sec
        intervals. If the value is 0 (default), the function will not provide future center coordinates or orientation.
    :param future_interval_s: Time interval between future waypoints in seconds.
    :param category2id: Mapping from category name to id. This parameter is optional and if provided, it is used to
        populate the box.label property when applicable.
    :param map_dilation: Map dilation factor in meters.
    :return: Dictionary mapping global names of desired categories to list of corresponding boxes.
    """
    if future_horizon_len_s:
        assert 0 < future_interval_s <= future_horizon_len_s
        all_boxes = lidarpc_rec.boxes_with_future_waypoints(future_horizon_len_s=future_horizon_len_s, future_interval_s=future_interval_s)
    else:
        all_boxes = lidarpc_rec.boxes()
    global2boxes: Dict[str, List[Box3D]] = {global_name: [] for global_name in target_category_names}
    for box in all_boxes:
        current_global_name = nuplandb.lidar_box[box.token].category.name
        if current_global_name in target_category_names:
            if category2id and current_global_name in list(category2id.keys()):
                box.label = category2id[current_global_name]
            global2boxes[current_global_name].append(box)
    for global_name, boxes in global2boxes.items():
        car_from_global = lidarpc_rec.ego_pose.trans_matrix_inv
        lidar_from_car = lidarpc_rec.lidar.trans_matrix_inv
        trans_matrix = reduce(np.dot, [lidar_from_car, car_from_global])
        transformed_boxes = [_box_transform(box, trans_matrix) for box in boxes]
        filtered_boxes = [box for box in transformed_boxes if box.distance_plane < max_distance]
        global2boxes[global_name] = filtered_boxes
    return global2boxes

def _box_transform(box: Box3D, trans_matrix: npt.NDArray[np.float64]) -> Box3D:
    """
    Helper method so box transform can be done in a list comprehension.
    :param box: Box to transform.
    :param trans_matrix: <np.float: 4, 4> Transformation matrix.
    :return: Transformed box.
    """
    box.transform(trans_matrix)
    return box

def project_lidarpcs_to_camera(pc: LidarPointCloud, transform: npt.NDArray[np.float64], camera_intrinsic: npt.NDArray[np.float64], width: int, height: int) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.bool8]]:
    """
    Project lidar pcs to a camera and return pcs with coordinate in a camera view.
    :param pc: Lidar point clouds.
    :param transform: <4, 4>. Matrix to transform point clouds to a camera view.
    :param camera_intrinsic: <3, 3>. Intrinsic matrix of a camera.
    :param width: Image width.
    :param height: Image height.
    :return points: <np.float: 3, number of points>. Point cloud with their coordinates in a camera.
            masks: <np.bool: number of points>. A 1d-array of boolean to indicate which points are available in
            the camera.
    """
    pc.transform(transform)
    depths = pc.points[2, :]
    points = view_points(pc.points[:3, :], camera_intrinsic, normalize=True)
    mask = np.ones(pc.points.shape[1], dtype=bool)
    mask = np.logical_and(mask, depths > 0.0)
    mask = np.logical_and(mask, points[0, :] > 0)
    mask = np.logical_and(mask, points[0, :] < width - 1)
    mask = np.logical_and(mask, points[1, :] > 0)
    mask = np.logical_and(mask, points[1, :] < height - 1)
    points = points[:, mask]
    points[2, :] = depths[mask]
    return (points, mask)

def render_pointcloud_in_image(db: NuPlanDB, lidar_pc: LidarPc, dot_size: int=5, color_channel: int=2, max_radius: float=np.inf, image_channel: str='CAM_F0') -> None:
    """
    Scatter-plots pointcloud on top of image.
    :param db: Log Database.
    :param sample: LidarPc Sample.
    :param dot_size: Scatter plot dot size.
    :param color_channel: Set to 2 for coloring dots by height, 3 for intensity.
    :param max_radius: Max xy radius of lidar points to include in visualization.
        Set to np.inf to include all points.
    :param image_channel: Which image to render.
    """
    image = lidar_pc_closest_image(lidar_pc, [image_channel])[0]
    points, coloring, im = map_pointcloud_to_image(db, lidar_pc, image, color_channel=color_channel, max_radius=max_radius)
    plt.figure(figsize=(9, 16))
    plt.imshow(im)
    plt.scatter(points[0, :], points[1, :], c=coloring, s=dot_size)
    plt.axis('off')

def map_pointcloud_to_image(db: NuPlanDB, lidar_pc: LidarPc, img: Image, color_channel: int=2, max_radius: float=np.inf) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], PIL.Image.Image]:
    """
    Given a lidar and camera sample_data, load point-cloud and map it to the image plane.
    :param db: Log Database.
    :param lidar_pc: Lidar sample_data record.
    :param img: Camera sample_data record.
    :param color_channel: Set to 2 for coloring dots by depth, 3 for intensity.
    :param max_radius: Max xy radius of lidar points to include in visualization.
        Set to np.inf to include all points.
    :return (pointcloud <np.float: 2, n)>, coloring <np.float: n>, image <Image>).
    """
    assert isinstance(lidar_pc, LidarPc), 'first input must be a lidar_pc modality'
    assert isinstance(img, Image), 'second input must be a camera modality'
    pc = lidar_pc.load()
    im = img.load_as(db, img_type='pil')
    radius = np.sqrt(pc.points[0] ** 2 + pc.points[1] ** 2)
    keep = radius <= max_radius
    pc.points = pc.points[:, keep]
    transform = reduce(np.dot, [img.camera.trans_matrix_inv, img.ego_pose.trans_matrix_inv, lidar_pc.ego_pose.trans_matrix, lidar_pc.lidar.trans_matrix])
    pc.transform(transform)
    coloring = pc.points[color_channel, :]
    depths = pc.points[2, :]
    points = view_points(pc.points[:3, :], img.camera.intrinsic_np, normalize=True)
    mask: npt.NDArray[np.bool8] = np.ones(depths.shape[0], dtype=bool)
    mask = np.logical_and(mask, depths > 0)
    mask = np.logical_and(mask, points[0, :] > 1)
    mask = np.logical_and(mask, points[0, :] < im.size[0] - 1)
    mask = np.logical_and(mask, points[1, :] > 1)
    mask = np.logical_and(mask, points[1, :] < im.size[1] - 1)
    points = points[:, mask]
    coloring = coloring[mask]
    return (points, coloring, im)

def render_lidar_box(lidar_box: LidarBox, db: NuPlanDB, ax: Optional[List[Axes]]=None) -> None:
    """
    Render LidarBox on an image and a lidar.
    :param lidar_box: A LidarBox object
    :param db: Log Database.
    :param ax: Array of Axes objects.
    """
    if ax is None:
        fig, ax = plt.subplots(1, 2, figsize=(18, 9))
    pc = lidar_box.lidar_pc
    imgs = lidar_pc_closest_image(lidar_box.lidar_pc)
    found = False
    for img in imgs:
        cam = img.camera
        box = lidar_box.box()
        box.transform(img.ego_pose.trans_matrix_inv)
        box.transform(cam.trans_matrix_inv)
        if box_in_image(box, cam.intrinsic_np, (cam.width, cam.height), vis_level=BoxVisibility.ANY):
            found = True
            break
    assert found, 'Could not find image where annotation is visible'
    if not lidar_box.category:
        logger.error('Wrong 3d instance mapping', lidar_box)
        c: npt.NDArray[np.float64] = np.array([128, 0, 128]) / 255.0
    else:
        c = lidar_box.category.color_np
    color = (c, c, np.array([0, 0, 0]))
    ax[0].imshow(img.load_as(db, img_type='pil'))
    box.render(ax[0], view=img.camera.intrinsic_np, normalize=True, colors=color)
    ax[0].set_title(img.camera.channel)
    ax[0].axis('off')
    ax[0].set_aspect('equal')
    box = lidar_box.box()
    box.transform(pc.ego_pose.trans_matrix_inv)
    box.transform(pc.lidar.trans_matrix_inv)
    view = np.eye(4)
    pc.load(db).render_height(ax[1], view=view)
    box.render(ax[1], view=view, colors=color)
    corners = view_points(box.corners(), view, False)[:2, :]
    ax[1].set_xlim([np.amin(corners[0, :]) - 10, np.amax(corners[0, :]) + 10])
    ax[1].set_ylim([np.amin(corners[1, :]) - 10, np.amax(corners[1, :]) + 10])
    ax[1].axis('off')
    ax[1].set_aspect('equal')

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
def min_distance_to_ego(self) -> float:
    """
        Returns minimum distance of Track from Ego Vehicle.
        :return: The minimum distance of the track from ego vehicle.
        """
    min_dist: float = np.amin(self.distances_to_ego)
    return min_dist

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

def test_render_on_map(self) -> None:
    """Test render on map."""
    render_on_map(self.lidar_pc, self.db, self.lidar_pc.boxes(), self.future_ego_poses, render_boxes_with_velocity=True, render_map_raster=False, render_vector_map=True, with_random_color=True, render_future_ego_poses=True)

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

def test_closest_image(self) -> None:
    """Tests the closest_image method"""
    result = lidar_pc_closest_image(self.lidar_pc)
    self.assertNotEqual(len(result), 0)

def test_lidar_pc_render(self) -> None:
    """Test Lidar PC render."""
    self.lidar_pc.render(self.db)

def points_in_box(box: Box3D, points: npt.NDArray[np.float64], wlh_factor: float=1.0) -> npt.NDArray[np.float64]:
    """
    Checks whether points are inside the box.

    Picks one corner as reference (p1) and computes the vector to a target point (v).
    Then for each of the 3 axes, project v onto the axis and compare the length.
    Inspired by: https://math.stackexchange.com/a/1552579.

    :param box: A Box3D instance.
    :param points: Points given as <np.float: 3, n_way_points)
    :param wlh_factor: Inflates or deflates the box.
    :return: <np.bool: n, >. Mask for points in box or not.
    """
    assert points.shape[0] == 3, 'Expect 3D pts'
    assert points.ndim == 2, 'Expect 2D inputs'
    r = ((box.wlh / 2) ** 2).sum() ** 0.5
    w, l, h = box.wlh
    w, l, h, r = (w * wlh_factor, l * wlh_factor, h * wlh_factor, r * wlh_factor)
    cx, cy, cz = box.center
    x, y, z = points
    pts_mask = functools.reduce(np.logical_and, [x >= cx - r, x <= cx + r, y >= cy - r, y <= cy + r, z >= cz - r, z <= cz + r])
    pts = points[:, pts_mask]
    rot = box.orientation.inverse.rotation_matrix.astype(np.float32)
    x, y, z = rot @ pts + (rot @ -box.center.astype(np.float32)).reshape(-1, 1)
    mask = functools.reduce(np.logical_and, [np.logical_and(x >= -l / 2, x <= l / 2), np.logical_and(y >= -w / 2, y <= w / 2), np.logical_and(z >= -h / 2, z <= h / 2)])
    pts_index = np.nonzero(pts_mask)
    pts_mask[pts_index] = mask
    return pts_mask

def box_in_image(box: Box3D, intrinsic: npt.NDArray[np.float64], imsize: Tuple[float, float], vis_level: int=BoxVisibility.ANY, front: int=2, min_front_th: float=0.1, with_velocity: bool=False) -> bool:
    """
    Check if a box is visible inside an image without accounting for occlusions.
    :param box: Box3D instance.
    :param intrinsic: <float: 3, 3>. Intrinsic camera matrix.
    :param imsize: Image (width, height).
    :param vis_level: One of the enumerations of <BoxVisibility>.
    :param front: Which axis represents depth. Default is z-axis (2) but can be set to y-axis (1) or x-axis (0).
    :param min_front_th: Corners' depth must be greater than this threshold for a box to be in the image.
        Note that 0.1 is a number that we found to produce reasonable plots.
    :param with_velocity: If True, include the velocity endpoint as one of the corners.
    :return True if visibility condition is satisfied.
    """
    corners_3d = box.corners()
    if with_velocity and (not np.isnan(box.velocity_endpoint).any()):
        corners_3d = np.concatenate((corners_3d, box.velocity_endpoint), axis=1)
    corners_img = view_points(corners_3d, intrinsic, normalize=True)[:2, :]
    in_front = corners_3d[front, :] > min_front_th
    corners_img = corners_img[:, in_front]
    visible = np.logical_and(corners_img[0, :] > 0, corners_img[0, :] < imsize[0])
    visible = np.logical_and(visible, corners_img[1, :] < imsize[1])
    visible = np.logical_and(visible, corners_img[1, :] > 0)
    if vis_level == BoxVisibility.ALL:
        return all(visible) and all(in_front)
    elif vis_level == BoxVisibility.ANY:
        return any(visible)
    elif vis_level == BoxVisibility.NONE:
        return True
    else:
        raise ValueError('vis_level: {} not valid'.format(vis_level))

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

def test_transform(self) -> None:
    """Tests transformation of SE2 pose"""
    pose = StateSE2(1, 2, 0)
    transform_matrix: npt.NDArray[np.float32] = np.array([[-3, -2, 5], [0, -1, 4], [0, 0, 1]], dtype=np.float32)
    result = transform(pose, transform_matrix)
    self.assertAlmostEqual(result.x, 2)
    self.assertAlmostEqual(result.y, 0)
    self.assertAlmostEqual(result.heading, np.pi, places=4)

class MetricSummaryCallback(AbstractMainCallback):
    """Callback to render histograms for metrics and metric aggregator."""

    def __init__(self, metric_save_path: str, metric_aggregator_save_path: str, summary_output_path: str, pdf_file_name: str, num_bins: int=20):
        """Callback to handle metric files at the end of process."""
        self._metric_save_path = Path(metric_save_path)
        self._metric_aggregator_save_path = Path(metric_aggregator_save_path)
        self._summary_output_path = Path(summary_output_path)
        if not is_s3_path(self._summary_output_path):
            self._summary_output_path.mkdir(parents=True, exist_ok=True)
        self._pdf_file_name = pdf_file_name
        self._num_bins = num_bins
        self._color_index = 0
        color_palette = cmap.get_cmap('Set1').colors + cmap.get_cmap('Set2').colors + cmap.get_cmap('Set3').colors
        self._color_choices = [mcolors.rgb2hex(color) for color in color_palette]
        self._metric_aggregator_dataframes: Dict[str, pd.DataFrame] = {}
        self._metric_statistics_dataframes: Dict[str, MetricStatisticsDataFrame] = {}

    @staticmethod
    def _read_metric_parquet_files(metric_save_path: Path, metric_reader: Callable[[Path], Any]) -> METRIC_DATAFRAME_TYPE:
        """
        Read metric parquet files with different readers.
        :param metric_save_path: Metric save path.
        :param metric_reader: Metric reader to read metric parquet files.
        :return A dictionary of {file_index: {file_name: MetricStatisticsDataFrame or pandas dataframe}}.
        """
        metric_dataframes: Dict[str, Union[MetricStatisticsDataFrame, pd.DataFrame]] = defaultdict()
        metric_file = metric_save_path.rglob('*.parquet')
        for file_index, file in enumerate(metric_file):
            try:
                if file.is_dir():
                    continue
                data_frame = metric_reader(file)
                metric_dataframes[file.stem] = data_frame
            except (FileNotFoundError, Exception):
                pass
        return metric_dataframes

    def _aggregate_metric_statistic_histogram_data(self) -> HistogramConstantConfig.HistogramDataType:
        """
        Aggregate metric statistic histogram data.
        :return A dictionary of metric names and their aggregated data.
        """
        data: HistogramConstantConfig.HistogramDataType = defaultdict(list)
        for dataframe_filename, dataframe in self._metric_statistics_dataframes.items():
            histogram_data_list = aggregate_metric_statistics_dataframe_histogram_data(metric_statistics_dataframe=dataframe, metric_statistics_dataframe_index=0, metric_choices=[], scenario_types=None)
            if histogram_data_list:
                data[dataframe.metric_statistic_name] += histogram_data_list
        return data

    def _aggregate_scenario_type_score_histogram_data(self) -> HistogramConstantConfig.HistogramDataType:
        """
        Aggregate scenario type score histogram data.
        :return A dictionary of scenario type metric name and their scenario type scores.
        """
        data: HistogramConstantConfig.HistogramDataType = defaultdict(list)
        for index, (dataframe_filename, dataframe) in enumerate(self._metric_aggregator_dataframes.items()):
            histogram_data_list = aggregate_metric_aggregator_dataframe_histogram_data(metric_aggregator_dataframe=dataframe, metric_aggregator_dataframe_index=index, scenario_types=['all'], dataframe_file_name=dataframe_filename)
            if histogram_data_list:
                data[f'{HistogramConstantConfig.SCENARIO_TYPE_SCORE_HISTOGRAM_NAME}_{dataframe_filename}'] += histogram_data_list
        return data

    def _assign_planner_colors(self) -> Dict[str, Any]:
        """
        Assign colors to planners.
        :return A dictionary of planner and colors.
        """
        planner_color_maps = {}
        for dataframe_filename, dataframe in self._metric_statistics_dataframes.items():
            planner_names = dataframe.planner_names
            for planner_name in planner_names:
                if planner_name not in planner_color_maps:
                    planner_color_maps[planner_name] = self._color_choices[self._color_index % len(self._color_choices)]
                    self._color_index += 1
        return planner_color_maps

    def _save_to_pdf(self, matplotlib_plots: List[Any]) -> None:
        """
        Save a list of matplotlib plots to a pdf file.
        :param matplotlib_plots: A list of matplotlib plots.
        """
        file_name = safe_path_to_string(self._summary_output_path / self._pdf_file_name)
        pp = PdfPages(file_name)
        for fig in matplotlib_plots[::-1]:
            fig.savefig(pp, format='pdf')
        pp.close()
        plt.close()

    @staticmethod
    def _render_ax_hist(ax: Any, x_values: npt.NDArray[np.float64], x_axis_label: str, y_axis_label: str, bins: npt.NDArray[np.float64], label: str, color: str, ax_title: str) -> None:
        """
        Render axis with histogram bins.
        :param ax: Matplotlib axis.
        :param x_values: An array of histogram x-axis values.
        :param x_axis_label: Label in the x-axis.
        :param y_axis_label: Label in the y-axis.
        :param bins: An array of histogram bins.
        :param label: Legend name for the bins.
        :param color: Color for the bins.
        :param ax_title: Axis title.
        """
        ax.hist(x=x_values, bins=bins, label=label, color=color, weights=np.ones(len(x_values)) / len(x_values))
        ax.set_xlabel(x_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.x_axis_label_size)
        ax.set_ylabel(y_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.y_axis_label_size)
        ax.set_title(ax_title, fontsize=HistogramTabMatPlotLibPlotStyleConfig.axis_title_size)
        ax.set_ylim(ymin=0)
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.tick_params(axis='both', which='major', labelsize=HistogramTabMatPlotLibPlotStyleConfig.axis_ticker_size)
        ax.legend(fontsize=HistogramTabMatPlotLibPlotStyleConfig.legend_font_size)

    @staticmethod
    def _render_ax_bar_hist(ax: Any, x_values: Union[npt.NDArray[np.float64], List[str]], x_axis_label: str, y_axis_label: str, x_range: List[str], label: str, color: str, ax_title: str) -> None:
        """
        Render axis with bar histogram.
        :param ax: Matplotlib axis.
        :param x_values: An array of histogram x-axis values.
        :param x_axis_label: Label in the x-axis.
        :param y_axis_label: Label in the y-axis.
        :param x_range: A list of histogram category names.
        :param label: Legend name for the bins.
        :param color: Color for the bins.
        :param ax_title: Axis title.
        """
        value_categories = {key: 0.0 for key in x_range}
        for value in x_values:
            value_categories[str(value)] += 1.0
        category_names = list(value_categories.keys())
        category_values: List[float] = list(value_categories.values())
        num_scenarios = sum(category_values)
        if num_scenarios != 0:
            category_values = [value / num_scenarios * 100 for value in category_values]
            category_values = np.round(category_values, decimals=HistogramTabFigureStyleConfig.decimal_places)
        ax.bar(category_names, category_values, label=label, color=color)
        ax.set_xlabel(x_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.x_axis_label_size)
        ax.set_ylabel(y_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.y_axis_label_size)
        ax.set_title(ax_title, fontsize=HistogramTabMatPlotLibPlotStyleConfig.axis_title_size)
        ax.set_ylim(ymin=0)
        ax.tick_params(axis='both', which='major', labelsize=HistogramTabMatPlotLibPlotStyleConfig.axis_ticker_size)
        ax.legend(fontsize=HistogramTabMatPlotLibPlotStyleConfig.legend_font_size)

    def _draw_histogram_plots(self, planner_color_maps: Dict[str, Any], histogram_data_dict: HistogramConstantConfig.HistogramDataType, histogram_edges: HistogramConstantConfig.HistogramEdgesDataType, n_cols: int=2) -> None:
        """
        :param planner_color_maps: Color maps from planner names.
        :param histogram_data_dict: A dictionary of histogram data.
        :param histogram_edges: A dictionary of histogram edges (bins) data.
        :param n_cols: Number of columns in subplot.
        """
        matplotlib_plots = []
        for histogram_title, histogram_data_list in tqdm(histogram_data_dict.items(), desc='Rendering histograms'):
            for histogram_data in histogram_data_list:
                color = planner_color_maps.get(histogram_data.planner_name, None)
                if not color:
                    planner_color_maps[histogram_data.planner_name] = self._color_choices[self._color_index % len(self._color_choices)]
                    color = planner_color_maps.get(histogram_data.planner_name)
                    self._color_index += 1
                n_rows = math.ceil(len(histogram_data.statistics) / n_cols)
                fig_size = min(max(6, len(histogram_data.statistics) // 5 * 5), 24)
                fig, axs = plt.subplots(n_rows, n_cols, figsize=(fig_size, fig_size))
                flatten_axs = axs.flatten()
                fig.suptitle(histogram_title, fontsize=HistogramTabMatPlotLibPlotStyleConfig.main_title_size)
                for index, (statistic_name, statistic) in enumerate(histogram_data.statistics.items()):
                    unit = statistic.unit
                    bins: npt.NDArray[np.float64] = np.unique(histogram_edges[histogram_title].get(statistic_name, None))
                    assert bins is not None, f'Count edge data for {statistic_name} cannot be None!'
                    x_range = get_histogram_plot_x_range(unit=unit, data=bins)
                    values = np.round(statistic.values, HistogramTabFigureStyleConfig.decimal_places)
                    if unit in ['count']:
                        self._render_ax_bar_hist(ax=flatten_axs[index], x_values=values, x_range=x_range, x_axis_label=unit, y_axis_label='Frequency (%)', label=histogram_data.planner_name, color=color, ax_title=statistic_name)
                    elif unit in ['bool', 'boolean']:
                        values = ['True' if value else 'False' for value in values]
                        self._render_ax_bar_hist(ax=flatten_axs[index], x_values=values, x_range=x_range, x_axis_label=unit, y_axis_label='Frequency (%)', label=histogram_data.planner_name, color=color, ax_title=statistic_name)
                    else:
                        self._render_ax_hist(ax=flatten_axs[index], x_values=values, bins=bins, x_axis_label=unit, y_axis_label='Frequency (%)', label=histogram_data.planner_name, color=color, ax_title=statistic_name)
                if n_rows * n_cols != len(histogram_data.statistics.values()):
                    flatten_axs[-1].set_axis_off()
                plt.tight_layout()
                matplotlib_plots.append(fig)
        self._save_to_pdf(matplotlib_plots=matplotlib_plots)

    def on_run_simulation_end(self) -> None:
        """Callback before end of the main function."""
        start_time = time.perf_counter()
        if not self._metric_save_path.exists() and (not self._metric_aggregator_save_path.exists()):
            return
        self._metric_aggregator_dataframes = self._read_metric_parquet_files(metric_save_path=self._metric_aggregator_save_path, metric_reader=metric_aggregator_reader)
        self._metric_statistics_dataframes = self._read_metric_parquet_files(metric_save_path=self._metric_save_path, metric_reader=metric_statistics_reader)
        planner_color_maps = self._assign_planner_colors()
        histogram_data_dict = self._aggregate_metric_statistic_histogram_data()
        scenario_type_histogram_data_dict = self._aggregate_scenario_type_score_histogram_data()
        histogram_data_dict.update(scenario_type_histogram_data_dict)
        histogram_edge_data = compute_histogram_edges(bins=self._num_bins, aggregated_data=histogram_data_dict)
        self._draw_histogram_plots(planner_color_maps=planner_color_maps, histogram_data_dict=histogram_data_dict, histogram_edges=histogram_edge_data)
        end_time = time.perf_counter()
        elapsed_time_s = end_time - start_time
        time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
        logger.info('Metric summary: {} [HH:MM:SS]'.format(time_str))

@staticmethod
def _render_ax_hist(ax: Any, x_values: npt.NDArray[np.float64], x_axis_label: str, y_axis_label: str, bins: npt.NDArray[np.float64], label: str, color: str, ax_title: str) -> None:
    """
        Render axis with histogram bins.
        :param ax: Matplotlib axis.
        :param x_values: An array of histogram x-axis values.
        :param x_axis_label: Label in the x-axis.
        :param y_axis_label: Label in the y-axis.
        :param bins: An array of histogram bins.
        :param label: Legend name for the bins.
        :param color: Color for the bins.
        :param ax_title: Axis title.
        """
    ax.hist(x=x_values, bins=bins, label=label, color=color, weights=np.ones(len(x_values)) / len(x_values))
    ax.set_xlabel(x_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.x_axis_label_size)
    ax.set_ylabel(y_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.y_axis_label_size)
    ax.set_title(ax_title, fontsize=HistogramTabMatPlotLibPlotStyleConfig.axis_title_size)
    ax.set_ylim(ymin=0)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.tick_params(axis='both', which='major', labelsize=HistogramTabMatPlotLibPlotStyleConfig.axis_ticker_size)
    ax.legend(fontsize=HistogramTabMatPlotLibPlotStyleConfig.legend_font_size)

@staticmethod
def _render_ax_bar_hist(ax: Any, x_values: Union[npt.NDArray[np.float64], List[str]], x_axis_label: str, y_axis_label: str, x_range: List[str], label: str, color: str, ax_title: str) -> None:
    """
        Render axis with bar histogram.
        :param ax: Matplotlib axis.
        :param x_values: An array of histogram x-axis values.
        :param x_axis_label: Label in the x-axis.
        :param y_axis_label: Label in the y-axis.
        :param x_range: A list of histogram category names.
        :param label: Legend name for the bins.
        :param color: Color for the bins.
        :param ax_title: Axis title.
        """
    value_categories = {key: 0.0 for key in x_range}
    for value in x_values:
        value_categories[str(value)] += 1.0
    category_names = list(value_categories.keys())
    category_values: List[float] = list(value_categories.values())
    num_scenarios = sum(category_values)
    if num_scenarios != 0:
        category_values = [value / num_scenarios * 100 for value in category_values]
        category_values = np.round(category_values, decimals=HistogramTabFigureStyleConfig.decimal_places)
    ax.bar(category_names, category_values, label=label, color=color)
    ax.set_xlabel(x_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.x_axis_label_size)
    ax.set_ylabel(y_axis_label, fontsize=HistogramTabMatPlotLibPlotStyleConfig.y_axis_label_size)
    ax.set_title(ax_title, fontsize=HistogramTabMatPlotLibPlotStyleConfig.axis_title_size)
    ax.set_ylim(ymin=0)
    ax.tick_params(axis='both', which='major', labelsize=HistogramTabMatPlotLibPlotStyleConfig.axis_ticker_size)
    ax.legend(fontsize=HistogramTabMatPlotLibPlotStyleConfig.legend_font_size)

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

def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
    """
        Render sample after a step
        """
    self._visualization.render_ego_state(sample.ego_state)
    self._visualization.render_observations(sample.observation)
    self._visualization.render_trajectory(sample.trajectory.get_sampled_trajectory())
    self._visualization.render(sample.iteration)

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

