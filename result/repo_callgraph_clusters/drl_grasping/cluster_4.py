# Cluster 4

class OctreeCreator:

    def __init__(self, node: Node, tf2_listener: Tf2Listener, reference_frame_id: str, min_bound: Tuple[float, float, float]=(-1.0, -1.0, -1.0), max_bound: Tuple[float, float, float]=(1.0, 1.0, 1.0), include_color: bool=False, include_intensity: bool=False, depth: int=4, full_depth: int=2, adaptive: bool=False, adp_depth: int=4, normals_radius: float=0.05, normals_max_nn: int=10, node_dis: bool=True, node_feature: bool=False, split_label: bool=False, th_normal: float=0.1, th_distance: float=2.0, extrapolate: bool=False, save_pts: bool=False, key2xyz: bool=False, debug_draw: bool=False, debug_write_octree: bool=False):
        self._node = node
        self.__tf2_listener = tf2_listener
        self._reference_frame_id = reference_frame_id
        self._min_bound = min_bound
        self._max_bound = max_bound
        self._include_color = include_color
        self._include_intensity = include_intensity
        self._normals_radius = normals_radius
        self._normals_max_nn = normals_max_nn
        self._debug_draw = debug_draw
        self._debug_write_octree = debug_write_octree
        self._points_to_octree = ocnn.Points2Octree(depth=depth, full_depth=full_depth, node_dis=node_dis, node_feature=node_feature, split_label=split_label, adaptive=adaptive, adp_depth=adp_depth, th_normal=th_normal, th_distance=th_distance, extrapolate=extrapolate, save_pts=save_pts, key2xyz=key2xyz, bb_min=min_bound, bb_max=max_bound)

    def __call__(self, ros_point_cloud2: PointCloud2) -> torch.Tensor:
        open3d_point_cloud = conversions.pointcloud2_to_open3d(ros_point_cloud2=ros_point_cloud2, include_color=self._include_color, include_intensity=self._include_intensity)
        open3d_point_cloud = self.preprocess_point_cloud(open3d_point_cloud=open3d_point_cloud, camera_frame_id=ros_point_cloud2.header.frame_id, reference_frame_id=self._reference_frame_id, min_bound=self._min_bound, max_bound=self._max_bound, normals_radius=self._normals_radius, normals_max_nn=self._normals_max_nn)
        if self._debug_draw:
            open3d.visualization.draw_geometries([open3d_point_cloud, open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.2, origin=[0.0, 0.0, 0.0])], point_show_normal=True)
        octree = self.construct_octree(open3d_point_cloud, include_color=self._include_color, include_intensity=self._include_intensity)
        if self._debug_write_octree:
            ocnn.write_octree(octree, 'octree.octree')
        return octree

    def preprocess_point_cloud(self, open3d_point_cloud: open3d.geometry.PointCloud, camera_frame_id: str, reference_frame_id: str, min_bound: List[float], max_bound: List[float], normals_radius: float, normals_max_nn: int) -> open3d.geometry.PointCloud:
        if not open3d_point_cloud.has_points():
            self._node.get_logger().warn('Point cloud has no points. Pre-processing skipped.')
            return open3d_point_cloud
        if camera_frame_id != reference_frame_id:
            transform = self.__tf2_listener.lookup_transform_sync(target_frame=reference_frame_id, source_frame=camera_frame_id)
            transform_mat = conversions.transform_to_matrix(transform=transform)
            open3d_point_cloud = open3d_point_cloud.transform(transform_mat)
        open3d_point_cloud = open3d_point_cloud.crop(bounding_box=open3d.geometry.AxisAlignedBoundingBox(min_bound=min_bound, max_bound=max_bound))
        if not open3d_point_cloud.has_points():
            self._node.get_logger().warn('Point cloud has no points after cropping it to the workspace volume.')
            return open3d_point_cloud
        open3d_point_cloud.estimate_normals(search_param=open3d.geometry.KDTreeSearchParamHybrid(radius=normals_radius, max_nn=normals_max_nn), fast_normal_computation=True)
        open3d_point_cloud.orient_normals_towards_camera_location(camera_location=transform_mat[0:3, 3])
        return open3d_point_cloud

    def construct_octree(self, open3d_point_cloud: open3d.geometry.PointCloud, include_color: bool, include_intensity: bool) -> torch.Tensor:
        if not open3d_point_cloud.has_points():
            open3d_point_cloud.points.append(((self._min_bound[0] + self._max_bound[0]) / 2, (self._min_bound[1] + self._max_bound[1]) / 2, (self._min_bound[2] + self._max_bound[2]) / 2))
            open3d_point_cloud.normals.append((0.0, 0.0, 0.0))
            if include_color or include_intensity:
                open3d_point_cloud.colors.append((0.0, 0.0, 0.0))
        octree_points = conversions.open3d_point_cloud_to_octree_points(open3d_point_cloud=open3d_point_cloud, include_color=include_color, include_intensity=include_intensity)
        octree_points_ndarray = np.frombuffer(np.copy(octree_points.buffer()), np.uint8)
        octree_points_tensor = torch.from_numpy(octree_points_ndarray)
        return self._points_to_octree(octree_points_tensor)

def __init__(self, node: Node, tf2_listener: Tf2Listener, reference_frame_id: str, min_bound: Tuple[float, float, float]=(-1.0, -1.0, -1.0), max_bound: Tuple[float, float, float]=(1.0, 1.0, 1.0), include_color: bool=False, include_intensity: bool=False, depth: int=4, full_depth: int=2, adaptive: bool=False, adp_depth: int=4, normals_radius: float=0.05, normals_max_nn: int=10, node_dis: bool=True, node_feature: bool=False, split_label: bool=False, th_normal: float=0.1, th_distance: float=2.0, extrapolate: bool=False, save_pts: bool=False, key2xyz: bool=False, debug_draw: bool=False, debug_write_octree: bool=False):
    self._node = node
    self.__tf2_listener = tf2_listener
    self._reference_frame_id = reference_frame_id
    self._min_bound = min_bound
    self._max_bound = max_bound
    self._include_color = include_color
    self._include_intensity = include_intensity
    self._normals_radius = normals_radius
    self._normals_max_nn = normals_max_nn
    self._debug_draw = debug_draw
    self._debug_write_octree = debug_write_octree
    self._points_to_octree = ocnn.Points2Octree(depth=depth, full_depth=full_depth, node_dis=node_dis, node_feature=node_feature, split_label=split_label, adaptive=adaptive, adp_depth=adp_depth, th_normal=th_normal, th_distance=th_distance, extrapolate=extrapolate, save_pts=save_pts, key2xyz=key2xyz, bb_min=min_bound, bb_max=max_bound)

