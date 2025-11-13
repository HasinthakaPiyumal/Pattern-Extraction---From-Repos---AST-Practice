# Cluster 15

def get_candidates(position: Union[Tuple[float, float], npt.NDArray[np.float64]], xrange: Union[Tuple[float, float], npt.NDArray[np.float64]], yrange: Union[Tuple[float, float], npt.NDArray[np.float64]], lane_groups_gdf: gpd.geodataframe, intersections_gdf: gpd.geodataframe) -> Tuple[gpd.geodataframe, gpd.geodataframe]:
    """
    Given a sample ego_pose position, find applicable lane_groups and intersections within its range.
    :param position: Ego pose position.
    :param xrange: only inside or intersects with xrange would lane_groups and intersections be considered.
    :param yrange: only inside or intersects with yrange would lane_groups and intersections be considered.
    :param lane_groups_gdf: dataframe of lane_groups data
    :param intersections_gdf: dataframe of intersections data
    :return: selected lane_groups dataframe and intersections dataframe within the range of sample ego-pose.
    """
    x_min, x_max = (position[0] + xrange[0], position[0] + xrange[1])
    y_min, y_max = (position[1] + yrange[0], position[1] + yrange[1])
    patch = geometry.box(x_min, y_min, x_max, y_max)
    candidate_lane_groups = lane_groups_gdf[lane_groups_gdf['geometry'].intersects(patch)]
    candidate_intersections = intersections_gdf[intersections_gdf['geometry'].intersects(patch)]
    return (candidate_lane_groups, candidate_intersections)

def _color_prep(ncolors: Optional[int]=None, alpha: int=128, colors: Optional[Union[Dict[int, Tuple[int, int, int]], Dict[int, Tuple[int, int, int, int]]]]=None) -> Dict[int, Tuple[int, int, int, int]]:
    """
    Prepares colors for image_with_boxes and draw_masks.
    :param ncolors: Total number of colors.
    :param alpha: Alpha-matting value to use for fill (0-255).
    :param colors: {id: (R, G, B) OR (R, G, B, A)}.
    :return: {id: (R, G, B, A)}.
    """
    if colors is None:
        assert ncolors is not None, 'If no colors are supplied, need to include ncolors'
        colors = [tuple(color) + (alpha,) for color in rainbow(ncolors - 1)]
    else:
        if ncolors is not None:
            assert ncolors == len(colors), 'Number of supplied colors {} disagrees with supplied ncolor: {}'.format(len(colors), ncolors)
        for _id, color in colors.items():
            if isinstance(color, list):
                color = tuple(color)
            if len(color) == 3:
                color = color + (alpha,)
            colors[_id] = color
    return colors

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

class TestRainbow(unittest.TestCase):
    """Test the rainbow."""

    def test_number_colors(self) -> None:
        """Check that correct number of colors is returned."""
        n_list = [3, 5, 7]
        for n in n_list:
            colors = rainbow(n)
            self.assertEqual(len(colors), n)

    def test_normalized(self) -> None:
        """Check that the colors are normalized."""
        n = 7
        colors = rainbow(n, normalized=True)
        for color in colors:
            for c in color:
                self.assertTrue(isinstance(c, float))
                self.assertTrue(0.0 <= c <= 1.0)

    def test_non_normalized(self) -> None:
        """Check that the colors are not normalized."""
        n = 7
        colors = rainbow(n, normalized=False)
        for color in colors:
            for c in color:
                self.assertTrue(isinstance(c, int))
                self.assertTrue(0 <= c <= 255)
        max_value = max([max(color) for color in colors])
        self.assertTrue(max_value > 1)

def test_number_colors(self) -> None:
    """Check that correct number of colors is returned."""
    n_list = [3, 5, 7]
    for n in n_list:
        colors = rainbow(n)
        self.assertEqual(len(colors), n)

def test_normalized(self) -> None:
    """Check that the colors are normalized."""
    n = 7
    colors = rainbow(n, normalized=True)
    for color in colors:
        for c in color:
            self.assertTrue(isinstance(c, float))
            self.assertTrue(0.0 <= c <= 1.0)

def test_non_normalized(self) -> None:
    """Check that the colors are not normalized."""
    n = 7
    colors = rainbow(n, normalized=False)
    for color in colors:
        for c in color:
            self.assertTrue(isinstance(c, int))
            self.assertTrue(0 <= c <= 255)
    max_value = max([max(color) for color in colors])
    self.assertTrue(max_value > 1)

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

def __eq__(self, other: object) -> bool:
    """
        Checks if two labels are equal.
        :param other: Other object.
        :return: True if both objects are the same.
        """
    if not isinstance(other, Label):
        return NotImplemented
    return self.name == other.name and self.color == other.color

def parametrize_filebased(abspath: Optional[str], filename: str, relpath: Optional[str]) -> Any:
    """
    Converts a target json file as a source of parameters for pytest.
    :param abspath: Absolute path of the json file
    :param filename: Name of the json file
    :param relpath: Relative path to the json file
    :return A pytest parameter
    """
    if filename.endswith('.json'):
        id_ = filename[:-5]
        return pytest.param(None, id=id_, marks=[pytest.mark.nuplan_test(relpath=relpath, absdirpath=abspath, params=id_)])
    else:
        return pytest.param(None, id='-', marks=[pytest.mark.nuplan_test(relpath=relpath, absdirpath=None, params=None)])

def parametrize_dir(absdirpath: Optional[str], files: List[str], relpath: Optional[str]) -> List[Any]:
    """
    Converts a target json file as a source of parameters for pytest.
    :param absdirpath: Absolute path of the directory containing the json files
    :param files: Name of the json files
    :param relpath: Relative path to the json file
    :return A list of pytest parameters
    """
    parameters = [pytest.param(None, id='<newname>', marks=[pytest.mark.nuplan_test(relpath=relpath, absdirpath=absdirpath, params=None)])]
    for file in files:
        if file.endswith('.json'):
            parameters.append(parametrize_filebased(absdirpath, file, relpath))
    return parameters

@functools.wraps(nuplan_test)
@pytest.mark.nuplan_test(type='hardcoded', params=None, absdirpath=None, relpath=None)
@pytest.mark.usefixtures('scene')
@pytest.mark.parametrize(argnames='nuplan_test', argvalues=[None], ids=['-'])
def testwrapper(*args: Any, **kwargs: Any) -> Any:
    return nuplan_test(*args, **kwargs)

class MapManager:
    """Class to store created maps using a map factory."""

    def __init__(self, map_factory: AbstractMapFactory):
        """
        Constructor of MapManager.
        :param map_factory: map factory.
        """
        self.map_factory = map_factory
        self.maps: Dict[str, AbstractMap] = {}

    def get_map(self, map_name: str) -> AbstractMap:
        """
        Returns the queried map from the map factory, creating it if it's missing.
        :param map_name: Name of the map.
        :return: The queried map.
        """
        if map_name not in self.maps:
            self.maps[map_name] = self.map_factory.build_map_from_name(map_name)
        return self.maps[map_name]

def get_map(self, map_name: str) -> AbstractMap:
    """
        Returns the queried map from the map factory, creating it if it's missing.
        :param map_name: Name of the map.
        :return: The queried map.
        """
    if map_name not in self.maps:
        self.maps[map_name] = self.map_factory.build_map_from_name(map_name)
    return self.maps[map_name]

def add_map_objects_to_scene(scene: Dict[str, Any], map_object: List[AbstractMapObject], layer: Optional[SemanticMapLayer]=None) -> None:
    """
    Serialize and append map objects to the scene.
    :param scene: scene dict.
    :param map_object: The map object to be added.
    :param layer: SemanticMapLayer type.
    """
    for obj in map_object:
        if isinstance(obj, (StopLine, PolygonMapObject, Intersection, RoadBlockGraphEdgeMapObject)):
            add_polygon_to_scene(scene, obj.polygon, obj.id, _color_to_object_mapping(layer))
        elif isinstance(obj, GraphEdgeMapObject):
            add_polyline_to_scene(scene, obj.baseline_path.discrete_path)

def compare_poses(pose1: StateSE2, pose2: StateSE2) -> None:
    """
    Compare x, y, and heading attribute of a StateSE2.
    :param pose1: first pose for comparing.
    :param pose2: second pose for comparing.
    """
    assert pose1.x == pytest.approx(pose2.x, 0.001)
    assert pose1.y == pytest.approx(pose2.y, 0.001)
    assert pose1.heading == pytest.approx(pose2.heading, 0.001)

class LaneGraphEdgeMapObject(GraphEdgeMapObject):
    """
    A class to represent a map object that can be an edge as a part of the map graph connectivity and contains a
    BaselinePath within it.
    """

    @property
    @abc.abstractmethod
    def incoming_edges(self) -> List[LaneGraphEdgeMapObject]:
        """
        Returns incoming edges connecting to this edge.
        :return: a list of LaneGraphEdgeMapObject.
        """
        pass

    @property
    @abc.abstractmethod
    def outgoing_edges(self) -> List[LaneGraphEdgeMapObject]:
        """
        Returns outgoing edges from this edge.
        :return: a list of LaneGraphEdgeMapObject.
        """
        pass

    @property
    @abc.abstractmethod
    def baseline_path(self) -> PolylineMapObject:
        """
        Getter function for obtaining the baseline path of the lane.
        :return: Baseline path of the lane.
        """
        pass

    @property
    @abc.abstractmethod
    def left_boundary(self) -> PolylineMapObject:
        """
        Getter function for obtaining the left boundary of the lane.
        :return: Left boundary of the lane.
        """
        pass

    @property
    @abc.abstractmethod
    def right_boundary(self) -> PolylineMapObject:
        """
        Getter function for obtaining the right boundary of the lane.
        :return: Right boundary of the lane.
        """
        pass

    @property
    @abc.abstractmethod
    def speed_limit_mps(self) -> Optional[float]:
        """
        Getter function for obtaining the speed limit of the lane.
        :return: [m/s] Speed limit.
        """
        pass

    @abc.abstractmethod
    def get_roadblock_id(self) -> str:
        """
        Getter function for obtaining the roadblock id containing the lane.
        :return: Roadblock ID containing the lane.
        """
        pass

    @abc.abstractmethod
    def parent(self) -> RoadBlockGraphEdgeMapObject:
        """
        Getter function for obtaining the parent RoadBlockGraphEdgeMapObject containing the LaneGraphEdgeMapObject.
        :return: RoadblockBlockGraphEdgeMapObject containing the LaneGraphEdgeMapObject.
        """
        pass

    @abc.abstractmethod
    def has_traffic_lights(self) -> bool:
        """
        Returns whether this graph edge is controlled by traffic lights.
        :return: True if the edge is controlled by traffic lights. False otherwise.
        """
        pass

    @property
    @abc.abstractmethod
    def stop_lines(self) -> List[StopLine]:
        """
        Returns a list of stop lines associated with this lane connector.
        :return: A list of stop lines associated with this lane connector.
        """
        pass

    def is_same_roadblock(self, other: Lane) -> bool:
        """
        :param other: Lane to check if it is in the same roadblock as self.
        :return: True if lanes are in the same roadblock.
        """
        return self.get_roadblock_id() == other.get_roadblock_id()

    def is_adjacent_to(self, other: Lane) -> bool:
        """
        :param other: Lane to check if it is adjacent to self.
        :return: True if self and other are in the same roadblock and adjacent.
        """
        return self.is_same_roadblock(other) and (self.right_boundary.id == other.left_boundary.id or self.left_boundary.id == other.right_boundary.id)

    @abc.abstractmethod
    def is_left_of(self, other: Lane) -> bool:
        """
        :param other: Lane to check if self is left of.
        :return: True if self and other are in the same RoadBlock and self is anywhere to the left of other.
        :raise AssertionError: if lanes are not in the same RoadBlock.
        """
        pass

    @abc.abstractmethod
    def is_right_of(self, other: Lane) -> bool:
        """
        :param other: Lane to check if self is right of.
        :return: True if self and other are in the same RoadBlock and self is anywhere to the right of other.
        :raise AssertionError: if lanes are not in the same RoadBlock.
        """
        pass

    @property
    @abc.abstractmethod
    def adjacent_edges(self) -> Tuple[Optional[LaneGraphEdgeMapObject], Optional[LaneGraphEdgeMapObject]]:
        """
        Gets adjacent LaneGraphEdgeMapObjects.
        :return: Tuple of adjacent LaneGraphEdgeMapObjects where first element is the left lane and the second element is the right lane.
        """
        pass

    @abc.abstractmethod
    def get_width_left_right(self, point: Point2D, include_outside: bool=False) -> Tuple[float, float]:
        """
        Gets distance to left and right sides of the lane from point.
        :param point: Point in global frame.
        :param include_outside: Allow point to be outside of lane.
        :return: The distance to left and right sides of the lane. If the query is invalid, inf is returned.
            If point is outside the LaneGraphEdgeMapObject and cannot be projected onto the LaneGraphEdgeMapObject and
            include_outside is True then the distance to the edge on the nearest end is returned.
        """
        pass

    @abc.abstractmethod
    def oriented_distance(self, point: Point2D) -> float:
        """
        Calculate the distance between the edge and a point with an oriented distance.
        :param point: Point global frame.
        :return: The distance between the edge and a point with an oriented distance. If the point is outside of the interval of
            the LaneGraphEdgeMapObject then the L1 distance to the nearest end is returned. The distance is positive if the
            point is on the left side of the line, while it is negative if the point is on the right side of the line.
        """
        pass

def is_same_roadblock(self, other: Lane) -> bool:
    """
        :param other: Lane to check if it is in the same roadblock as self.
        :return: True if lanes are in the same roadblock.
        """
    return self.get_roadblock_id() == other.get_roadblock_id()

class PolylineMapObject(AbstractMapObject):
    """
    A class to represent any map object that can be represented as a polyline.
    """

    def __init__(self, path_id: str):
        """
        Constructor of the PolylineMapObject type.
        :param path_id: unique identifier of the polyline.
        """
        super().__init__(path_id)

    @property
    @abc.abstractmethod
    def linestring(self) -> LineString:
        """
        Returns the polyline as a Linestring.
        :return: The polyline as a Linestring.
        """
        pass

    @property
    @abc.abstractmethod
    def length(self) -> float:
        """
        Returns the length of the polyline [m].
        :return: the length of the polyline.
        """
        pass

    @property
    @abc.abstractmethod
    def discrete_path(self) -> List[StateSE2]:
        """
        Gets a discretized representation of the polyline.
        :return: a list of StateSE2.
        """
        pass

    @abc.abstractmethod
    def get_nearest_arc_length_from_position(self, point: Point2D) -> float:
        """
        Returns the arc length along the polyline where the given point is the closest.
        :param point: [m] x, y coordinates in global frame.
        :return: [m] arc length along the polyline.
        """
        pass

    @abc.abstractmethod
    def get_nearest_pose_from_position(self, point: Point2D) -> StateSE2:
        """
        Returns the pose along the polyline where the given point is the closest.
        :param point: [m] x, y coordinates in global frame.
        :return: nearest pose along the polyline as StateSE2.
        """
        pass

    @abc.abstractmethod
    def get_curvature_at_arc_length(self, arc_length: float) -> float:
        """
        Return curvature at an arc length along the polyline.
        :param arc_length: [m] arc length along the polyline. It has to be 0<= arc_length <=length.
        :return: [1/m] curvature along a polyline.
        """
        pass

    def get_nearest_curvature_from_position(self, point: Point2D) -> float:
        """
        Returns the curvature along the polyline where the given point is the closest.
        :param point: [m] x, y coordinates in global frame.
        :return: [1/m] curvature along a polyline.
        """
        return self.get_curvature_at_arc_length(self.get_nearest_arc_length_from_position(point))

def get_nearest_curvature_from_position(self, point: Point2D) -> float:
    """
        Returns the curvature along the polyline where the given point is the closest.
        :param point: [m] x, y coordinates in global frame.
        :return: [1/m] curvature along a polyline.
        """
    return self.get_curvature_at_arc_length(self.get_nearest_arc_length_from_position(point))

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
def parent(self) -> RoadBlockGraphEdgeMapObject:
    """Inherited from superclass"""
    return self._map_data.get_map_object(self.get_roadblock_id(), SemanticMapLayer.ROADBLOCK)

def build_lane_segments_from_blps_with_trim(point: Point2D, radius: float, map_obj: MapObject, start_lane_seg_idx: int) -> Union[None, Tuple[List[List[List[float]]], List[Tuple[int, int]], List[List[int]], List[str], List[str], Tuple[int, int]]]:
    """
    Process baseline paths of associated lanes/lane connectors to series of lane-segments along with connection info.
    :param point: [m] x, y coordinates in global frame.
    :param radius [m] floating number about vector map query range.
    :param map_obj: Lane or LaneConnector for building lane segments from associated baseline path.
    :param start_lane_seg_idx: Starting index for lane segments.
    :return
        obj_coords: Data recording lane-segment coordinates in format of [N, 2, 2].
        obj_conns: Data recording lane-segment connection relations in format of [M, 2].
        obj_groupings: Data recording lane-segment indices associated with each lane in format
            [num_lanes, num_segments_in_lane].
        obj_lane_ids: Data recording map object ids of lane/lane connector containing lane-segment.
        obj_roadblock_ids: Data recording map object ids of roadblock/roadblock connector containing lane-segment.
        obj_cross_blp_conn: Data storing indices of first and last lane segments of a given map object's baseline path
            as [blp_start_lane_seg_idx, blp_end_lane_seg_idx].
    """
    map_obj_id = map_obj.id
    roadblock_id = map_obj.get_roadblock_id()
    nodes = map_obj.baseline_path.discrete_path
    nodes = trim_lane_nodes(point, radius, nodes)
    if len(nodes) <= 2:
        return None
    lane_seg_num = len(nodes) - 1
    end_lane_seg_idx = start_lane_seg_idx + lane_seg_num - 1
    obj_coords = split_blp_lane_segments(nodes, lane_seg_num)
    obj_conns = connect_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    obj_groupings = group_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    obj_lane_ids = [map_obj_id for _ in range(lane_seg_num)]
    obj_roadblock_ids = [roadblock_id for _ in range(lane_seg_num)]
    obj_cross_blp_conn = (start_lane_seg_idx, end_lane_seg_idx)
    return (obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn)

def build_lane_segments_from_blps(map_obj: MapObject, start_lane_seg_idx: int) -> Tuple[List[List[List[float]]], List[Tuple[int, int]], List[List[int]], List[str], List[str], Tuple[int, int]]:
    """
    Process baseline paths of associated lanes/lane connectors to series of lane-segments along with connection info.
    :param map_obj: Lane or LaneConnector for building lane segments from associated baseline path.
    :param start_lane_seg_idx: Starting index for lane segments.
    :return
        obj_coords: Data recording lane-segment coordinates in format of [N, 2, 2].
        obj_conns: Data recording lane-segment connection relations in format of [M, 2].
        obj_groupings: Data recording lane-segment indices associated with each lane in format
            [num_lanes, num_segments_in_lane].
        obj_lane_ids: Data recording map object ids of lane/lane connector containing lane-segment.
        obj_roadblock_ids: Data recording map object ids of roadblock/roadblock connector containing lane-segment.
        obj_cross_blp_conn: Data storing indices of first and last lane segments of a given map object's baseline path
            as [blp_start_lane_seg_idx, blp_end_lane_seg_idx].
    """
    map_obj_id = map_obj.id
    roadblock_id = map_obj.get_roadblock_id()
    nodes = map_obj.baseline_path.discrete_path
    lane_seg_num = len(nodes) - 1
    end_lane_seg_idx = start_lane_seg_idx + lane_seg_num - 1
    obj_coords = split_blp_lane_segments(nodes, lane_seg_num)
    obj_conns = connect_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    obj_groupings = group_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    obj_lane_ids = [map_obj_id for _ in range(lane_seg_num)]
    obj_roadblock_ids = [roadblock_id for _ in range(lane_seg_num)]
    obj_cross_blp_conn = (start_lane_seg_idx, end_lane_seg_idx)
    return (obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn)

def extract_polygon_from_map_object(map_object: MapObject) -> List[Point2D]:
    """
    Extract polygon from map object.
    :param map_object: input MapObject.
    :return: polygon as list of Point2D.
    """
    x_coords, y_coords = map_object.polygon.exterior.coords.xy
    return [Point2D(x, y) for x, y in zip(x_coords, y_coords)]

def extract_roadblock_objects(map_api: AbstractMap, point: Point2D) -> List[RoadBlockGraphEdgeMapObject]:
    """
    Extract roadblock or roadblock connectors from map containing point if they exist.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :return List of roadblocks/roadblock connectors containing point if they exist.
    """
    roadblock = map_api.get_one_map_object(point, SemanticMapLayer.ROADBLOCK)
    if roadblock:
        return [roadblock]
    else:
        roadblock_conns = map_api.get_all_map_objects(point, SemanticMapLayer.ROADBLOCK_CONNECTOR)
        return cast(List[RoadBlockGraphEdgeMapObject], roadblock_conns)

def get_roadblock_ids_from_trajectory(map_api: AbstractMap, ego_states: List[EgoState]) -> List[str]:
    """
    Extract ids of roadblocks and roadblock connectors containing points in specified trajectory.
    :param map_api: map to perform extraction on.
    :param ego_states: sequence of agent states representing trajectory.
    :return roadblock_ids: List of ids of roadblocks/roadblock connectors containing trajectory points.
    """
    roadblock_ids: List[str] = []
    roadblock_candidates: List[RoadBlockGraphEdgeMapObject] = []
    last_roadblock = None
    points = [ego_state.rear_axle.point for ego_state in ego_states]
    for point in points:
        if last_roadblock and last_roadblock.contains_point(point):
            continue
        if last_roadblock and (not roadblock_candidates):
            roadblock_candidates = last_roadblock.outgoing_edges
        roadblock_candidates = [roadblock for roadblock in roadblock_candidates if roadblock.contains_point(point)]
        if len(roadblock_candidates) == 1:
            last_roadblock = roadblock_candidates.pop()
            roadblock_ids.append(last_roadblock.id)
        elif not roadblock_candidates:
            roadblock_objects = extract_roadblock_objects(map_api, point)
            if len(roadblock_objects) == 1:
                last_roadblock = roadblock_objects.pop()
                roadblock_ids.append(last_roadblock.id)
            else:
                roadblock_candidates = roadblock_objects
    return roadblock_ids

def compute_curvature(point1: geom.Point, point2: geom.Point, point3: geom.Point) -> float:
    """
    Estimate signed curvature along the three points.
    :param point1: First point of a circle.
    :param point2: Second point of a circle.
    :param point3: Third point of a circle.
    :return signed curvature of the three points.
    """
    a = point1.distance(point2)
    b = point2.distance(point3)
    c = point3.distance(point1)
    surface_2 = (a + (b + c)) * (c - (a - b)) * (c + (a - b)) * (a + (b - c))
    if surface_2 < 1e-06:
        return 0.0
    assert surface_2 >= 0
    k = np.sqrt(surface_2) / 4
    den = a * b * c
    curvature = 4 * k / den if not np.isclose(den, 0.0) else 0.0
    position = np.sign((point2.x - point1.x) * (point3.y - point1.y) - (point2.y - point1.y) * (point3.x - point1.x))
    return float(position * curvature)

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
def parent(self) -> RoadBlockGraphEdgeMapObject:
    """Inherited from superclass"""
    return self._map_data.get_map_object(self.get_roadblock_id(), SemanticMapLayer.ROADBLOCK_CONNECTOR)

@nuplan_test(path='json/stop_lines/nearby.json')
def test_get_nearby_stop_lines(scene: Dict[str, Any]) -> None:
    """
    Test getting nearby stop lines.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_distance, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_distance'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        stop_line_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.STOP_LINE)
        assert stop_line_id is not None
        assert expected_distance == distance
        assert expected_id == stop_line_id
        stop_line: StopLine = nuplan_map.get_map_object(stop_line_id, SemanticMapLayer.STOP_LINE)
        add_map_objects_to_scene(scene, [stop_line])

@nuplan_test(path='json/stop_lines/on_stopline.json')
def test_get_stop_lines(scene: Dict[str, Any]) -> None:
    """
    Test getting stop lines at a point.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        stop_line: StopLine = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.STOP_LINE)
        assert stop_line is not None
        assert expected_id == stop_line.id
        assert stop_line.contains_point(Point2D(pose[0], pose[1]))
        add_map_objects_to_scene(scene, [stop_line])

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_baseline_queries_in_lane(scene: Dict[str, Any]) -> None:
    """
    Test baseline queries.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    expected_arc_length = scene['xtr']['expected_arc_length']
    expected_pose = scene['xtr']['expected_pose']
    expected_curvature = scene['xtr']['expected_curvature']
    poses = {}
    for marker, exp_arc_length, exp_pose, exp_curv in zip(scene['markers'], expected_arc_length, expected_pose.values(), expected_curvature):
        pose = marker['pose']
        point = Point2D(pose[0], pose[1])
        lane = nuplan_map.get_one_map_object(point, SemanticMapLayer.LANE)
        assert lane is not None
        assert lane.contains_point(point)
        add_map_objects_to_scene(scene, [lane])
        lane_blp = lane.baseline_path
        arc_length = lane_blp.get_nearest_arc_length_from_position(point)
        pose = lane_blp.get_nearest_pose_from_position(point)
        curv = lane_blp.get_curvature_at_arc_length(arc_length)
        poses[marker['id']] = pose
        assert arc_length == pytest.approx(exp_arc_length)
        assert pose == StateSE2(exp_pose[0], exp_pose[1], exp_pose[2])
        assert curv == pytest.approx(exp_curv)
        constructed_blp = NuPlanPolylineMapObject(get_row_with_value(lane._baseline_paths_df, 'lane_fid', lane.id))
        constructed_blp_arc_length = constructed_blp.get_nearest_arc_length_from_position(point)
        constructed_blp_pose = constructed_blp.get_nearest_pose_from_position(point)
        constructed_blp_curv = constructed_blp.get_curvature_at_arc_length(constructed_blp_arc_length)
        assert arc_length == pytest.approx(constructed_blp_arc_length)
        assert pose == constructed_blp_pose
        assert curv == pytest.approx(constructed_blp_curv)
    for pose_id, pose in poses.items():
        add_marker_to_scene(scene, str(pose_id), pose)

@nuplan_test(path='json/intersections/on_intersection.json')
def test_get_intersections(scene: Dict[str, Any]) -> None:
    """
    Test getting intersections at a point.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        intersection: Intersection = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.INTERSECTION)
        assert intersection is not None
        assert expected_id == intersection.id
        assert intersection.contains_point(Point2D(pose[0], pose[1]))
        add_map_objects_to_scene(scene, [intersection])

@nuplan_test(path='json/intersections/nearby.json')
def test_get_nearby_intersection(scene: Dict[str, Any]) -> None:
    """
    Test getting nearby crosswalks.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_distance, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_distance'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        intersection_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.INTERSECTION)
        assert intersection_id is not None
        assert expected_distance == distance
        assert expected_id == intersection_id
        intersection: Intersection = nuplan_map.get_map_object(intersection_id, SemanticMapLayer.INTERSECTION)
        add_map_objects_to_scene(scene, [intersection])

@nuplan_test(path='json/crosswalks/nearby.json')
def test_get_nearby_crosswalks(scene: Dict[str, Any]) -> None:
    """
    Test getting nearby crosswalks.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_distance, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_distance'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        crosswalk_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.CROSSWALK)
        assert crosswalk_id is not None
        assert expected_distance == distance
        assert expected_id == crosswalk_id
        crosswalk: PolygonMapObject = nuplan_map.get_map_object(crosswalk_id, SemanticMapLayer.CROSSWALK)
        add_map_objects_to_scene(scene, [crosswalk])

@nuplan_test(path='json/crosswalks/on_crosswalk.json')
def test_get_crosswalk(scene: Dict[str, Any]) -> None:
    """
    Test getting crosswalk at a point.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        crosswalk: PolygonMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.CROSSWALK)
        assert crosswalk is not None
        assert expected_id == crosswalk.id
        assert crosswalk.contains_point(Point2D(pose[0], pose[1]))
        add_map_objects_to_scene(scene, [crosswalk])

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_incoming_outgoing_lanes(scene: Dict[str, Any]) -> None:
    """
    Test getting incoming and outgoing lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        incoming_edges = lane_connectors[0].incoming_edges
        outgoing_edges = lane_connectors[0].outgoing_edges
        add_map_objects_to_scene(scene, incoming_edges)
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_lane_left_boundaries(scene: Dict[str, Any]) -> None:
    """
    Test getting left boundaries of lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        left_boundary = lane_connectors[0].left_boundary
        assert left_boundary is not None
        assert isinstance(left_boundary, PolylineMapObject)
        add_polyline_to_scene(scene, left_boundary.discrete_path)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_lane_right_boundaries(scene: Dict[str, Any]) -> None:
    """
    Test getting right boundaries of lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        right_boundary = lane_connectors[0].right_boundary
        assert right_boundary is not None
        assert isinstance(right_boundary, PolylineMapObject)
        add_polyline_to_scene(scene, right_boundary.discrete_path)

@nuplan_test(path='json/intersections/on_intersection_with_stop_lines.json')
def test_get_stop_lines(scene: Dict[str, Any]) -> None:
    """
    Test getting stop lines from lane connector.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        stop_lines = lane_connectors[0].stop_lines
        assert len(stop_lines) > 0
        add_map_objects_to_scene(scene, stop_lines)

@nuplan_test(path='json/intersections/on_intersection_with_no_stop_lines.json')
def test_get_stop_lines_empty(scene: Dict[str, Any]) -> None:
    """
    Test getting stop lines from lane connector when there are no stop lines.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        stop_lines = lane_connectors[0].stop_lines
        assert len(stop_lines) == 0
        add_map_objects_to_scene(scene, stop_lines)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_polygon(scene: Dict[str, Any]) -> None:
    """
    Test getting polygons from lane_connector.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        point = Point(pose[0], pose[1])
        lane_connectors: List[LaneConnector] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert len(lane_connectors) > 0
        polygon = lane_connectors[0].polygon
        assert polygon.contains(point)
        add_map_objects_to_scene(scene, lane_connectors)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_incoming_outgoing_roadblock_connectors(scene: Dict[str, Any]) -> None:
    """
    Test getting incoming and outgoing roadblock connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock: RoadBlockGraphEdgeMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        incoming_edges = roadblock.incoming_edges
        outgoing_edges = roadblock.outgoing_edges
        assert len(incoming_edges) > 0
        assert len(outgoing_edges) > 0
        add_map_objects_to_scene(scene, incoming_edges)
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/connections/no_end_connection.json')
def test_no_end_roadblock_connector(scene: Dict[str, Any]) -> None:
    """
    Test when there are not outgoing roadblock connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock: RoadBlockGraphEdgeMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        incoming_edges = roadblock.incoming_edges
        outgoing_edges = roadblock.outgoing_edges
        assert not outgoing_edges
        add_map_objects_to_scene(scene, incoming_edges)

@nuplan_test(path='json/connections/no_start_connection.json')
def test_no_start_roadblock_connector(scene: Dict[str, Any]) -> None:
    """
    Test when there are not incoming lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock: RoadBlockGraphEdgeMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        incoming_edges = roadblock.incoming_edges
        outgoing_edges = roadblock.outgoing_edges
        assert not incoming_edges
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_roadblock_interior_edges(scene: Dict[str, Any]) -> None:
    """
    Test getting roadblock's interior lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock: RoadBlockGraphEdgeMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        interior_edges = roadblock.interior_edges
        assert len(interior_edges) > 0
        add_map_objects_to_scene(scene, interior_edges)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_roadblock_polygon(scene: Dict[str, Any]) -> None:
    """
    Test getting roadblock's polygon.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock: RoadBlockGraphEdgeMapObject = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        polygon = roadblock.polygon
        assert polygon
        assert isinstance(polygon, Polygon)

def test_split_blp_lane_segments() -> None:
    """
    Test splitting baseline paths node list into lane segments.
    """
    nodes = [StateSE2(0.0, 0.0, 0.0), StateSE2(0.0, 0.0, 0.0), StateSE2(0.0, 0.0, 0.0)]
    lane_seg_num = 2
    obj_coords = split_blp_lane_segments(nodes, lane_seg_num)
    assert len(obj_coords) == 2
    assert len(obj_coords[0]) == 2
    assert len(obj_coords[0][0]) == 2
    assert isinstance(obj_coords, List)
    assert isinstance(obj_coords[0], List)
    assert isinstance(obj_coords[0][0], List)
    assert isinstance(obj_coords[0][0][0], float)

def test_connect_blp_lane_segments() -> None:
    """
    Test connecting lane indices.
    """
    start_lane_seg_idx = 0
    lane_seg_num = 10
    obj_conns = connect_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    assert len(obj_conns) == lane_seg_num - 1
    assert len(obj_conns[0]) == 2
    assert isinstance(obj_conns, List)
    assert isinstance(obj_conns[0], tuple)
    assert isinstance(obj_conns[0][0], int)

def test_group_blp_lane_segments() -> None:
    """
    Test grouping lane indices belonging to same lane/lane connector.
    """
    start_lane_seg_idx = 0
    lane_seg_num = 10
    obj_groupings = group_blp_lane_segments(start_lane_seg_idx, lane_seg_num)
    assert len(obj_groupings) == 1
    assert len(obj_groupings[0]) == lane_seg_num
    assert isinstance(obj_groupings, List)
    assert isinstance(obj_groupings[0], List)
    assert isinstance(obj_groupings[0][0], int)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_build_lane_segments_from_blps_with_trim(scene: Dict[str, Any]) -> None:
    """
    Test build and trim the lane segments from the baseline paths.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        radius = 20
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        start_idx = 0
        trimmed_obj_coords, trimmed_obj_conns, trimmed_obj_groupings, trimmed_obj_lane_ids, trimmed_obj_roadblock_ids, trimmed_obj_cross_blp_conn = build_lane_segments_from_blps_with_trim(Point2D(pose[0], pose[1]), radius, lane, start_idx)
        start_idx = 0
        obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn = build_lane_segments_from_blps(lane, start_idx)
        assert len(trimmed_obj_coords) > 0
        assert len(trimmed_obj_conns) > 0
        assert len(trimmed_obj_groupings) > 0
        assert len(trimmed_obj_lane_ids) > 0
        assert len(trimmed_obj_roadblock_ids) > 0
        assert len(trimmed_obj_cross_blp_conn) == 2
        assert len(trimmed_obj_coords) == len(trimmed_obj_conns) + 1
        assert len(trimmed_obj_coords) == len(trimmed_obj_groupings[0])
        assert len(trimmed_obj_coords) == len(trimmed_obj_lane_ids)
        assert len(trimmed_obj_coords) == len(trimmed_obj_roadblock_ids)
        assert len(trimmed_obj_coords) <= len(obj_coords)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_connect_trimmed_lane_conn_predecessor(scene: Dict[str, Any]) -> None:
    """
    Test connecting trimmed lane connector to incoming lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connector: LaneConnector = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)[0]
        assert lane_connector is not None
        incoming_edges = lane_connector.incoming_edges
        assert len(incoming_edges) > 0
        lane: Lane = lane_connector.incoming_edges[0]
        assert lane is not None
        start_idx = 0
        radius = 20
        trim_nodes = build_lane_segments_from_blps_with_trim(Point2D(pose[0], pose[1]), radius, lane, start_idx)
        if trim_nodes is not None:
            obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn = trim_nodes
        else:
            continue
        cross_blp_conns: Dict[str, List[int]] = {}
        cross_blp_conns[lane_connector.id] = [0, 0]
        cross_blp_conns[incoming_edges[0].id] = [0, 0]
        lane_seg_pred_conns = connect_trimmed_lane_conn_predecessor(obj_coords, lane_connector, cross_blp_conns)
        assert len(lane_seg_pred_conns) > 0
        assert isinstance(lane_seg_pred_conns, List)
        assert isinstance(lane_seg_pred_conns[0], tuple)
        assert isinstance(lane_seg_pred_conns[0][0], int)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_connect_trimmed_lane_conn_successor(scene: Dict[str, Any]) -> None:
    """
    Test connecting trimmed lane connector to outgoing lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connector: LaneConnector = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)[0]
        assert lane_connector is not None
        outgoing_edges = lane_connector.outgoing_edges
        assert len(outgoing_edges) > 0
        lane: Lane = lane_connector.outgoing_edges[0]
        assert lane is not None
        start_idx = 0
        radius = 20
        trim_nodes = build_lane_segments_from_blps_with_trim(Point2D(pose[0], pose[1]), radius, lane, start_idx)
        if trim_nodes is not None:
            obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn = trim_nodes
        else:
            continue
        cross_blp_conns: Dict[str, List[int]] = {}
        cross_blp_conns[lane_connector.id] = [0, 0]
        cross_blp_conns[outgoing_edges[0].id] = [0, 0]
        lane_seg_suc_conns = connect_trimmed_lane_conn_successor(obj_coords, lane_connector, cross_blp_conns)
        assert len(lane_seg_suc_conns) > 0
        assert isinstance(lane_seg_suc_conns, List)
        assert isinstance(lane_seg_suc_conns[0], tuple)
        assert isinstance(lane_seg_suc_conns[0][0], int)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_build_lane_segments_from_blps(scene: Dict[str, Any]) -> None:
    """
    Test building lane segments from baseline paths.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        start_idx = 0
        obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn = build_lane_segments_from_blps(lane, start_idx)
        assert len(obj_coords) > 0
        assert len(obj_conns) > 0
        assert len(obj_groupings) > 0
        assert len(obj_lane_ids) > 0
        assert len(obj_roadblock_ids) > 0
        assert len(obj_cross_blp_conn) == 2
        assert len(obj_coords) == len(obj_conns) + 1
        assert len(obj_coords) == len(obj_groupings[0])
        assert len(obj_coords) == len(obj_lane_ids)
        assert len(obj_coords) == len(obj_roadblock_ids)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_connect_lane_conn_predecessor(scene: Dict[str, Any]) -> None:
    """
    Test connecting lane connector to incoming lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connector: LaneConnector = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)[0]
        assert lane_connector is not None
        incoming_edges = lane_connector.incoming_edges
        assert len(incoming_edges) > 0
        cross_blp_conns: Dict[str, List[int]] = {}
        cross_blp_conns[lane_connector.id] = [0, 0]
        cross_blp_conns[incoming_edges[0].id] = [0, 0]
        lane_seg_pred_conns = connect_lane_conn_predecessor(lane_connector, cross_blp_conns)
        assert len(lane_seg_pred_conns) > 0
        assert isinstance(lane_seg_pred_conns, List)
        assert isinstance(lane_seg_pred_conns[0], tuple)
        assert isinstance(lane_seg_pred_conns[0][0], int)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_connect_lane_conn_successor(scene: Dict[str, Any]) -> None:
    """
    Test connecting lane connector to outgoing lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane_connector: LaneConnector = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)[0]
        assert lane_connector is not None
        outgoing_edges = lane_connector.outgoing_edges
        assert len(outgoing_edges) > 0
        cross_blp_conns: Dict[str, List[int]] = {}
        cross_blp_conns[lane_connector.id] = [0, 0]
        cross_blp_conns[outgoing_edges[0].id] = [0, 0]
        lane_seg_suc_conns = connect_lane_conn_successor(lane_connector, cross_blp_conns)
        assert len(lane_seg_suc_conns) > 0
        assert isinstance(lane_seg_suc_conns, List)
        assert isinstance(lane_seg_suc_conns[0], tuple)
        assert isinstance(lane_seg_suc_conns[0][0], int)

@nuplan_test(path='json/crosswalks/nearby.json')
def test_extract_polygon_from_map_object_crosswalk(scene: Dict[str, Any]) -> None:
    """
    Test extracting polygon from map object. Tests crosswalks.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    radius = 20
    for marker in scene['markers']:
        pose = marker['pose']
        layers = nuplan_map.get_proximal_map_objects(Point2D(pose[0], pose[1]), radius, [SemanticMapLayer.CROSSWALK])
        crosswalks = layers[SemanticMapLayer.CROSSWALK]
        assert len(crosswalks) > 0
        crosswalk_polygon = extract_polygon_from_map_object(crosswalks[0])
        assert isinstance(crosswalk_polygon, List)
        assert len(crosswalk_polygon) > 0
        assert isinstance(crosswalk_polygon[0], Point2D)

@nuplan_test(path='json/stop_lines/nearby.json')
def test_extract_polygon_from_map_object_stop_lines(scene: Dict[str, Any]) -> None:
    """
    Test extracting polygon from map object. Tests stop lines.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    radius = 20
    for marker in scene['markers']:
        pose = marker['pose']
        layers = nuplan_map.get_proximal_map_objects(Point2D(pose[0], pose[1]), radius, [SemanticMapLayer.STOP_LINE])
        stop_lines = layers[SemanticMapLayer.STOP_LINE]
        assert len(stop_lines) > 0
        stop_line_polygon = extract_polygon_from_map_object(stop_lines[0])
        assert isinstance(stop_line_polygon, List)
        assert len(stop_line_polygon) > 0
        assert isinstance(stop_line_polygon[0], Point2D)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_extract_roadblock_objects_roadblocks(scene: Dict[str, Any]) -> None:
    """
    Test extract roadblock or roadblock connectors from map containing point. Tests roadblocks.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_objects = extract_roadblock_objects(nuplan_map, Point2D(pose[0], pose[1]))
        assert isinstance(roadblock_objects, List)
        assert len(roadblock_objects) > 0
        roadblock_object = roadblock_objects[0]
        assert isinstance(roadblock_object, RoadBlockGraphEdgeMapObject)
        roadblock_polygon = extract_polygon_from_map_object(roadblock_object)
        assert isinstance(roadblock_polygon, List)
        assert len(roadblock_polygon) > 0
        assert isinstance(roadblock_polygon[0], Point2D)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_extract_roadblock_objects_roadblock_connectors(scene: Dict[str, Any]) -> None:
    """
    Test extract roadblock or roadblock connectors from map containing point. Tests roadblock connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_objects = extract_roadblock_objects(nuplan_map, Point2D(pose[0], pose[1]))
        assert isinstance(roadblock_objects, List)
        assert len(roadblock_objects) > 0
        roadblock_object = roadblock_objects[0]
        assert isinstance(roadblock_object, RoadBlockGraphEdgeMapObject)
        roadblock_polygon = extract_polygon_from_map_object(roadblock_object)
        assert isinstance(roadblock_polygon, List)
        assert len(roadblock_polygon) > 0
        assert isinstance(roadblock_polygon[0], Point2D)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_roadblock_ids_from_trajectory(scene: Dict[str, Any]) -> None:
    """
    Test extracting ids of roadblocks and roadblock connectors containing points specified in trajectory.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    trajectory: List[EgoState] = []
    for marker in scene['markers']:
        pose = marker['pose']
        ego_state = get_sample_ego_state()
        ego_state.car_footprint.rear_axle = StateSE2(pose[0], pose[1], pose[2])
        trajectory.append(ego_state)
    roadblock_ids = get_roadblock_ids_from_trajectory(nuplan_map, trajectory)
    assert isinstance(roadblock_ids, List)
    for roadblock_id in roadblock_ids:
        assert isinstance(roadblock_id, str)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_distance_between_map_object_and_point_lanes_roadblocks(scene: Dict[str, Any]) -> None:
    """
    Test get distance between point and nearest surface of specified map object.
    Tests lane/connectors and roadblock/connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    radius = 35
    pose = scene['markers'][0]['pose']
    point = Point2D(pose[0], pose[1])
    layer_names = [SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR]
    layers = nuplan_map.get_proximal_map_objects(point, radius, layer_names)
    for layer_name in layer_names:
        map_objects = layers[layer_name]
        assert len(map_objects) > 0
        dist = get_distance_between_map_object_and_point(point, map_objects[0])
        assert dist <= radius

@nuplan_test(path='json/crosswalks/nearby.json')
def test_get_distance_between_map_object_and_point_crosswalks(scene: Dict[str, Any]) -> None:
    """
    Test get distance between point and nearest surface of specified map object. Tests crosswalks.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    radius = 35
    pose = scene['markers'][0]['pose']
    point = Point2D(pose[0], pose[1])
    layers = nuplan_map.get_proximal_map_objects(point, radius, [SemanticMapLayer.CROSSWALK])
    map_objects = layers[SemanticMapLayer.CROSSWALK]
    assert len(map_objects) > 0
    dist = get_distance_between_map_object_and_point(point, map_objects[0])
    assert dist <= radius

@nuplan_test(path='json/stop_lines/nearby.json')
def test_get_distance_between_map_object_and_point_stop_lines(scene: Dict[str, Any]) -> None:
    """
    Test get distance between point and nearest surface of specified map object. Tests stop lines.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    radius = 35
    pose = scene['markers'][0]['pose']
    point = Point2D(pose[0], pose[1])
    layers = nuplan_map.get_proximal_map_objects(point, radius, [SemanticMapLayer.STOP_LINE])
    map_objects = layers[SemanticMapLayer.STOP_LINE]
    assert len(map_objects) > 0
    dist = get_distance_between_map_object_and_point(point, map_objects[0])
    assert dist <= radius

def assert_helper(first_markers: List[Dict[str, List[float]]], second_markers: List[Dict[str, List[float]]], assertion: Callable[[Lane, Lane, bool], None], map: AbstractMap, inverse: bool) -> None:
    """
    Helper function to remove redundant lane instantiation and checking
    """
    for first_marker, second_marker in zip(first_markers, second_markers):
        first_point = Point2D(*first_marker['pose'][:2])
        second_point = Point2D(*second_marker['pose'][:2])
        first_lane = map.get_one_map_object(first_point, SemanticMapLayer.LANE)
        second_lane = map.get_one_map_object(second_point, SemanticMapLayer.LANE)
        assertion(first_lane, second_lane, inverse)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_incoming_outgoing_lane_connectors(scene: Dict[str, Any]) -> None:
    """
    Test getting incoming and outgoing lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        incoming_edges = lane.incoming_edges
        outgoing_edges = lane.outgoing_edges
        assert len(incoming_edges) > 0
        assert len(outgoing_edges) > 0
        add_map_objects_to_scene(scene, incoming_edges)
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/connections/no_end_connection.json')
def test_no_end_lane_connector(scene: Dict[str, Any]) -> None:
    """
    Test when there are not outgoing lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        incoming_edges = lane.incoming_edges
        outgoing_edges = lane.outgoing_edges
        assert not outgoing_edges
        add_map_objects_to_scene(scene, incoming_edges)

@nuplan_test(path='json/connections/no_start_connection.json')
def test_no_start_lane_connector(scene: Dict[str, Any]) -> None:
    """
    Test when there are not incoming lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        incoming_edges = lane.incoming_edges
        outgoing_edges = lane.outgoing_edges
        assert not incoming_edges
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_lane_left_boundaries(scene: Dict[str, Any]) -> None:
    """
    Test getting left boundaries of lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        left_boundary = lane.left_boundary
        assert left_boundary is not None
        assert isinstance(left_boundary, PolylineMapObject)
        add_polyline_to_scene(scene, left_boundary.discrete_path)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_lane_right_boundaries(scene: Dict[str, Any]) -> None:
    """
    Test getting right boundaries of lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        right_boundary = lane.right_boundary
        assert right_boundary is not None
        assert isinstance(right_boundary, PolylineMapObject)
        add_polyline_to_scene(scene, right_boundary.discrete_path)

@nuplan_test(path='json/lanes/lanes_in_same_roadblock.json')
def test_lane_is_same_roadblock(scene: Dict[str, Any]) -> None:
    """
    Test if lanes are in the same roadblock
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])

    def is_same_roadblock(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
        if not inverse:
            assert first_lane.is_same_roadblock(second_lane)
        else:
            assert not first_lane.is_same_roadblock(second_lane)
    assert_helper(scene['markers'][:4:2], scene['markers'][1:4:2], is_same_roadblock, nuplan_map, False)
    assert_helper(scene['markers'][4::2], scene['markers'][5::2], is_same_roadblock, nuplan_map, True)

@nuplan_test(path='json/lanes/lanes_are_adjacent.json')
def test_lane_is_adjacent_to(scene: Dict[str, Any]) -> None:
    """
    Test if lanes are adjacent
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])

    def is_adjacent_to(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
        if not inverse:
            assert first_lane.is_adjacent_to(second_lane)
        else:
            assert not first_lane.is_adjacent_to(second_lane)
    assert_helper(scene['markers'][:4:2], scene['markers'][1:4:2], is_adjacent_to, nuplan_map, False)
    assert_helper(scene['markers'][4::2], scene['markers'][5::2], is_adjacent_to, nuplan_map, True)

def is_adjacent_to(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
    if not inverse:
        assert first_lane.is_adjacent_to(second_lane)
    else:
        assert not first_lane.is_adjacent_to(second_lane)

@nuplan_test(path='json/lanes/lane_is_left_of.json')
def test_lane_is_left_of(scene: Dict[str, Any]) -> None:
    """
    Test if first is left of second
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])

    def is_left_of(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
        if not inverse:
            assert first_lane.is_left_of(second_lane)
        else:
            assert not first_lane.is_left_of(second_lane)
    assert_helper(scene['markers'][:4:2], scene['markers'][1:4:2], is_left_of, nuplan_map, False)
    assert_helper(scene['markers'][4::2], scene['markers'][5::2], is_left_of, nuplan_map, True)

def is_left_of(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
    if not inverse:
        assert first_lane.is_left_of(second_lane)
    else:
        assert not first_lane.is_left_of(second_lane)

@nuplan_test(path='json/lanes/lane_is_left_of.json')
def test_lane_is_right_of(scene: Dict[str, Any]) -> None:
    """
    Test if first is right of second
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])

    def is_right_of(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
        if not inverse:
            assert first_lane.is_right_of(second_lane)
        else:
            assert not first_lane.is_right_of(second_lane)
    assert_helper(scene['markers'][1:4:2], scene['markers'][:4:2], is_right_of, nuplan_map, False)
    assert_helper(scene['markers'][5::2], scene['markers'][4::2], is_right_of, nuplan_map, True)

def is_right_of(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
    if not inverse:
        assert first_lane.is_right_of(second_lane)
    else:
        assert not first_lane.is_right_of(second_lane)

@nuplan_test(path='json/lanes/get_adjacent_lanes.json')
def test_get_lane_adjacent_lanes(scene: Dict[str, Any]) -> None:
    """
    Test if getting correct adjacent lanes
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        left_lane, right_lane = lane.adjacent_edges
        assert left_lane or right_lane
        if left_lane:
            assert left_lane.is_left_of(lane)
            assert left_lane.is_adjacent_to(lane)
        if right_lane:
            assert right_lane.is_right_of(lane)
            assert right_lane.is_adjacent_to(lane)

@nuplan_test(path='json/lanes/lane_index.json')
def test_get_lane_index(scene: Dict[str, Any]) -> None:
    """
    Test if getting correct lane index
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_index in zip(scene['markers'], scene['xtr']['expected_lane_index']):
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is not None
        assert lane.index == expected_index

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_incoming_outgoing_roadblock(scene: Dict[str, Any]) -> None:
    """
    Test getting incoming and outgoing lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_connectors: List[RoadBlockGraphEdgeMapObject] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert len(roadblock_connectors) > 0
        incoming_edges = roadblock_connectors[0].incoming_edges
        outgoing_edges = roadblock_connectors[0].outgoing_edges
        add_map_objects_to_scene(scene, incoming_edges)
        add_map_objects_to_scene(scene, outgoing_edges)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_roadblock_connector_interior_edges(scene: Dict[str, Any]) -> None:
    """
    Test getting roadblock connector's interior lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_connectors: List[RoadBlockGraphEdgeMapObject] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert len(roadblock_connectors) > 0
        interior_edges = roadblock_connectors[0].interior_edges
        assert len(interior_edges) > 0
        add_map_objects_to_scene(scene, interior_edges)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_roadblock_connector_polygon(scene: Dict[str, Any]) -> None:
    """
    Test getting roadblock connector's polygon.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_connectors: List[RoadBlockGraphEdgeMapObject] = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert len(roadblock_connectors) > 0
        polygon = roadblock_connectors[0].polygon
        assert polygon
        assert isinstance(polygon, Polygon)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_is_in_layer_lane(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test is in lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        assert nuplan_map.is_in_layer(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_is_in_layer_intersection(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test is in intersection.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        assert nuplan_map.is_in_layer(Point2D(pose[0], pose[1]), SemanticMapLayer.INTERSECTION)

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_lane(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting one lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_speed_limit in zip(scene['markers'], scene['xtr']['expected_speed_limit']):
        pose = marker['pose']
        point = Point2D(pose[0], pose[1])
        lane = nuplan_map.get_one_map_object(point, SemanticMapLayer.LANE)
        assert lane is not None
        assert lane.contains_point(point)
        assert lane.speed_limit_mps == pytest.approx(expected_speed_limit)
        add_map_objects_to_scene(scene, [lane])

@nuplan_test(path='json/baseline/no_baseline.json')
def test_no_baseline(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test when there is no baseline.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        lane: Lane = nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane is None
        lane_connector = nuplan_map.get_all_map_objects(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        assert not lane_connector

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_lane_connector(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting lane connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    idx = 0
    for marker in scene['markers']:
        pose = marker['pose']
        point = Point2D(pose[0], pose[1])
        lane_connectors = nuplan_map.get_all_map_objects(point, SemanticMapLayer.LANE_CONNECTOR)
        assert lane_connectors is not None
        add_map_objects_to_scene(scene, lane_connectors)
        for lane_connector in lane_connectors:
            assert lane_connector.contains_point(point)
            assert lane_connector.speed_limit_mps == pytest.approx(scene['xtr']['expected_speed_limit'][idx])
            idx += 1
    pose = scene['markers'][0]['pose']
    with pytest.raises(AssertionError):
        nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)

@nuplan_test(path='json/get_nearest/lane.json')
def test_get_nearest_lane(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting nearest lane.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_distance, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_distance'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        lane_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE)
        assert lane_id == expected_id
        assert distance == expected_distance
        lane = nuplan_map.get_map_object(str(lane_id), SemanticMapLayer.LANE)
        add_map_objects_to_scene(scene, [lane])

@nuplan_test(path='json/get_nearest/lane_connector.json')
def test_get_nearest_lane_connector(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting nearest lane connector.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker, expected_distance, expected_id in zip(scene['markers'], scene['xtr']['expected_nearest_distance'], scene['xtr']['expected_nearest_id']):
        pose = marker['pose']
        lane_connector_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.LANE_CONNECTOR)
        lane_connector = nuplan_map.get_map_object(str(lane_connector_id), SemanticMapLayer.LANE_CONNECTOR)
        add_map_objects_to_scene(scene, [lane_connector])

@nuplan_test(path='json/baseline/baseline_in_lane.json')
def test_get_roadblock(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting one roadblock.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        point = Point2D(pose[0], pose[1])
        roadblock = nuplan_map.get_one_map_object(point, SemanticMapLayer.ROADBLOCK)
        assert roadblock is not None
        assert roadblock.contains_point(point)
        add_map_objects_to_scene(scene, [roadblock])

@nuplan_test(path='json/baseline/baseline_in_intersection.json')
def test_get_roadblock_connector(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting roadblock connectors.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        point = Point2D(pose[0], pose[1])
        roadblock_connectors = nuplan_map.get_all_map_objects(point, SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert roadblock_connectors is not None
        add_map_objects_to_scene(scene, roadblock_connectors)
        for roadblock_connector in roadblock_connectors:
            assert roadblock_connector.contains_point(point)
    pose = scene['markers'][0]['pose']
    with pytest.raises(AssertionError):
        nuplan_map.get_one_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK_CONNECTOR)

@nuplan_test(path='json/get_nearest/lane.json')
def test_get_nearest_roadblock(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting nearest roadblock.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK)
        roadblock = nuplan_map.get_map_object(str(roadblock_id), SemanticMapLayer.ROADBLOCK)
        assert roadblock_id
        add_map_objects_to_scene(scene, [roadblock])

@nuplan_test(path='json/get_nearest/lane_connector.json')
def test_get_nearest_roadblock_connector(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test getting nearest roadblock connector.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    for marker in scene['markers']:
        pose = marker['pose']
        roadblock_connector_id, distance = nuplan_map.get_distance_to_nearest_map_object(Point2D(pose[0], pose[1]), SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert roadblock_connector_id != -1
        assert distance != np.NaN
        roadblock_connector = nuplan_map.get_map_object(str(roadblock_connector_id), SemanticMapLayer.ROADBLOCK_CONNECTOR)
        assert roadblock_connector
        add_map_objects_to_scene(scene, [roadblock_connector])

@nuplan_test(path='json/neighboring/all_map_objects.json')
def test_get_proximal_map_objects(scene: Dict[str, Any], map_factory: NuPlanMapFactory) -> None:
    """
    Test get_neighbor_lanes.
    """
    nuplan_map = map_factory.build_map_from_name(scene['map']['area'])
    marker = scene['markers'][0]
    pose = marker['pose']
    map_objects = nuplan_map.get_proximal_map_objects(Point2D(pose[0], pose[1]), 40, [SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR, SemanticMapLayer.STOP_LINE, SemanticMapLayer.CROSSWALK, SemanticMapLayer.INTERSECTION])
    assert len(map_objects[SemanticMapLayer.LANE]) == scene['xtr']['expected_num_lanes']
    assert len(map_objects[SemanticMapLayer.LANE_CONNECTOR]) == scene['xtr']['expected_num_lane_connectors']
    assert len(map_objects[SemanticMapLayer.ROADBLOCK]) == scene['xtr']['expected_num_roadblocks']
    assert len(map_objects[SemanticMapLayer.ROADBLOCK_CONNECTOR]) == scene['xtr']['expected_num_roadblock_connectors']
    assert len(map_objects[SemanticMapLayer.STOP_LINE]) == scene['xtr']['expected_num_stop_lines']
    assert len(map_objects[SemanticMapLayer.CROSSWALK]) == scene['xtr']['expected_num_cross_walks']
    assert len(map_objects[SemanticMapLayer.INTERSECTION]) == scene['xtr']['expected_num_intersections']
    for layer, map_objects in map_objects.items():
        add_map_objects_to_scene(scene, map_objects, layer)

@nuplan_test()
def test_unsupported_neighbor_map_objects(map_factory: NuPlanMapFactory) -> None:
    """
    Test throw if unsupported layer is queried.
    """
    nuplan_map = map_factory.build_map_from_name('us-nv-las-vegas-strip')
    with pytest.raises(AssertionError):
        nuplan_map.get_proximal_map_objects(Point2D(0, 0), 15, [SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR, SemanticMapLayer.STOP_LINE, SemanticMapLayer.CROSSWALK, SemanticMapLayer.INTERSECTION, SemanticMapLayer.TRAFFIC_LIGHT])

@nuplan_test()
def test_get_available_map_objects(map_factory: NuPlanMapFactory) -> None:
    """
    Test getting available map objects for all SemanticMapLayers.
    """
    nuplan_map = map_factory.build_map_from_name('us-nv-las-vegas-strip')
    assert set(nuplan_map.get_available_map_objects()) == {SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR, SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR, SemanticMapLayer.STOP_LINE, SemanticMapLayer.CROSSWALK, SemanticMapLayer.INTERSECTION, SemanticMapLayer.WALKWAYS, SemanticMapLayer.CARPARK_AREA}

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

def __eq__(self, other: object) -> bool:
    """
        Compare two instances whether they are numerically close
        :param other: object
        :return: true if the classes are almost equal
        """
    if not isinstance(other, DynamicCarState):
        return NotImplemented
    return self.rear_axle_velocity_2d == other.rear_axle_velocity_2d and self.rear_axle_acceleration_2d == other.rear_axle_acceleration_2d and math.isclose(self._angular_acceleration, other._angular_acceleration) and math.isclose(self._angular_velocity, other._angular_velocity) and math.isclose(self._rear_axle_to_center_dist, other._rear_axle_to_center_dist) and math.isclose(self._tire_steering_rate, other._tire_steering_rate)

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

def __radd__(self, other: object) -> TimePoint:
    """
        :param other: Right addition target.
        :return: Addition with other if other is a TimeDuration.
        """
    if isinstance(other, TimeDuration):
        return self.__add__(other)
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

def diff(self, time_point: TimePoint) -> TimeDuration:
    """
        Computes the TimeDuration between self and another TimePoint.
        :param time_point: The other time point.
        :return: The TimeDuration between the two TimePoints.
        """
    return TimeDuration.from_us(int(self.time_us - time_point.time_us))

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

@property
def point(self) -> Point2D:
    """
        Gets a point from the StateSE2
        :return: Point with x and y from StateSE2
        """
    return Point2D(self.x, self.y)

def __eq__(self, other: object) -> bool:
    """
        Compare two state SE2
        :param other: object
        :return: true if the objects are equal, false otherwise
        """
    if not isinstance(other, StateSE2):
        return NotImplemented
    return math.isclose(self.x, other.x, abs_tol=0.001) and math.isclose(self.y, other.y, abs_tol=0.001) and math.isclose(self.heading, other.heading, abs_tol=0.0001)

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

def __eq__(self, other: object) -> bool:
    """
        Compare two oriented boxes
        :param other: object
        :return: true if other and self is equal
        """
    if not isinstance(other, OrientedBox):
        return NotImplemented
    return math.isclose(self.width, other.width) and math.isclose(self.height, other.height) and math.isclose(self.length, other.length) and (self.center == other.center)

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

def __eq__(self, other: Any) -> bool:
    """
        Comparison between two Waypoints.
        :param other: Other object.
        :return True if both objects are same.
        """
    if not isinstance(other, Waypoint):
        return NotImplemented
    return other.oriented_box == self._oriented_box and other.time_point == self.time_point and (other.velocity == self._velocity)

class TestTimeDuration(unittest.TestCase):
    """Tests for TimeDurationClass"""

    def test_default_initialization(self) -> None:
        """Checks raising when constructor is called directly unless flagged."""
        with self.assertRaises(RuntimeError):
            _ = TimeDuration(time_us=42)
        dt = TimeDuration(time_us=42, _direct=False)
        self.assertEqual(dt.time_us, 42)

    def test_constructors(self) -> None:
        """Checks constructors perform correct conversions"""
        dt_s = TimeDuration.from_s(42)
        dt_ms = TimeDuration.from_ms(42)
        dt_us = TimeDuration.from_us(42)
        self.assertEqual(dt_s.time_us, 42000000)
        self.assertEqual(dt_ms.time_us, 42000)
        self.assertEqual(dt_us.time_us, 42)

    def test_getters(self) -> None:
        """Checks getters work as intended"""
        dt = TimeDuration.from_s(42)
        value_s = dt.time_s
        value_ms = dt.time_ms
        value_us = dt.time_us
        self.assertEqual(value_s, 42)
        self.assertEqual(value_ms, 42000)
        self.assertEqual(value_us, 42000000)

    def test_operators(self) -> None:
        """Tests basic math operators."""
        t1 = TimeDuration.from_s(1)
        t2 = TimeDuration.from_s(2)
        self.assertTrue(t2 > t1)
        self.assertFalse(t2 < t1)
        self.assertTrue(t1 < t2)
        self.assertFalse(t1 > t2)
        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 <= t1)
        self.assertEqual((t1 + t2).time_s, 3)
        self.assertEqual((t1 - t2).time_s, -1)
        self.assertEqual((t1 * 3).time_s, 3)
        self.assertEqual((3 * t1).time_s, 3)
        self.assertEqual((t2 / 2).time_s, 1)
        self.assertEqual((t2 // 3).time_s, 0)

def test_constructors(self) -> None:
    """Checks constructors perform correct conversions"""
    dt_s = TimeDuration.from_s(42)
    dt_ms = TimeDuration.from_ms(42)
    dt_us = TimeDuration.from_us(42)
    self.assertEqual(dt_s.time_us, 42000000)
    self.assertEqual(dt_ms.time_us, 42000)
    self.assertEqual(dt_us.time_us, 42)

def test_getters(self) -> None:
    """Checks getters work as intended"""
    dt = TimeDuration.from_s(42)
    value_s = dt.time_s
    value_ms = dt.time_ms
    value_us = dt.time_us
    self.assertEqual(value_s, 42)
    self.assertEqual(value_ms, 42000)
    self.assertEqual(value_us, 42000000)

class TestTimePoint(unittest.TestCase):
    """Tests for TimePoint class."""

    def test_initialization(self) -> None:
        """Tests initialization fails with negative values and works otherwise."""
        with self.assertRaises(AssertionError):
            _ = TimePoint(-42)
        t1 = TimePoint(123456)
        self.assertEqual(t1.time_us, 123456)

    def test_comparisons(self) -> None:
        """Test basic comparison operators."""
        t1 = TimePoint(123123)
        t2 = TimePoint(234234)
        self.assertTrue(t2 > t1)
        self.assertFalse(t2 < t1)
        self.assertTrue(t1 < t2)
        self.assertFalse(t1 > t2)
        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 <= t1)

    def test_addition(self) -> None:
        """Tests addition and subtractions."""
        t1 = TimePoint(123)
        dt = TimeDuration.from_us(100)
        self.assertEqual(t1 + dt, TimePoint(223))
        self.assertEqual(dt + t1, TimePoint(223))
        self.assertEqual(t1 - dt, TimePoint(23))

def test_addition(self) -> None:
    """Tests addition and subtractions."""
    t1 = TimePoint(123)
    dt = TimeDuration.from_us(100)
    self.assertEqual(t1 + dt, TimePoint(223))
    self.assertEqual(dt + t1, TimePoint(223))
    self.assertEqual(t1 - dt, TimePoint(23))

def signed_lateral_distance(ego_state: StateSE2, other: Polygon) -> float:
    """
    Computes the minimal lateral distance of ego from another polygon
    :param ego_state: the state of ego
    :param other: the query polygon
    :return: the signed lateral distance
    """
    ego_half_width = get_pacifica_parameters().half_width
    ego_left = translate_laterally(ego_state, ego_half_width)
    ego_right = translate_laterally(ego_state, -ego_half_width)
    vertices = list(zip(*other.exterior.coords.xy))
    distance_left = max(min((lateral_distance(ego_left, Point2D(*vertex)) for vertex in vertices)), 0)
    distance_right = max(min((-lateral_distance(ego_right, Point2D(*vertex)) for vertex in vertices)), 0)
    return distance_left if distance_left > distance_right else -distance_right

def signed_longitudinal_distance(ego_state: StateSE2, other: Polygon) -> float:
    """
    Computes the minimal longitudinal distance of ego from another polygon
    :param ego_state: the state of ego
    :param other: the query polygon
    :return: the signed lateral distance
    """
    ego_half_length = get_pacifica_parameters().half_length
    ego_front = translate_longitudinally(ego_state, ego_half_length)
    ego_back = translate_longitudinally(ego_state, -ego_half_length)
    vertices = list(zip(*other.exterior.coords.xy))
    distance_front = max(min((longitudinal_distance(ego_front, Point2D(*vertex)) for vertex in vertices)), 0)
    distance_back = max(min((-longitudinal_distance(ego_back, Point2D(*vertex)) for vertex in vertices)), 0)
    return distance_front if distance_front > distance_back else -distance_back

@nuplan_test(path='json/load_from_scene.json')
def test_load_from_scene(scene: Dict[str, Any]) -> None:
    """
    Tests loading tracked objects with predictions from a scene json.
    :param scene: The input scene loaded from the json file.
    """
    tracked_objects = from_scene_to_tracked_objects_with_scene_predictions(scene)
    agent = tracked_objects.tracked_objects[0]
    assert agent.track_token == '0'
    assert agent.tracked_object_type == TrackedObjectType.VEHICLE
    assert list(agent.box.center) == [1, 2, 0]
    assert len(agent.predictions) == 2
    assert agent.predictions[0].probability == 0.9
    assert agent.predictions[1].probability == 0.1
    assert agent.box.width == 2.0
    assert agent.box.length == 4.7
    for i, state in enumerate(agent.predictions[0].waypoints):
        assert list(state.center) == pytest.approx([1 + 0.01 * i, 2 + 0.01 * i, 0.01 * i])
        assert state.time_us == pytest.approx(agent.metadata.timestamp_us + int(0.5 * i * 1000000.0))

class TestWorkerPool(unittest.TestCase):
    """Unittest class for WorkerPool"""

    def setUp(self) -> None:
        """Set up basic config."""
        self.lhs_matrix: npt.NDArray[np.float32] = np.array([[1, 2, 4], [2, 3, 4]])
        self.rhs_matrix: npt.NDArray[np.float32] = np.array([[2, 3, 4], [2, 5, 4]]).T
        self.target: npt.NDArray[np.float32] = np.array([[24, 28], [29, 35]])
        self.workers = [Sequential(), RayDistributed(debug_mode=True), SingleMachineParallelExecutor(), SingleMachineParallelExecutor(use_process_pool=True)]

    def test_task(self) -> None:
        """Test Task whether a function can be called"""

        def add_inputs(input1: float, input2: float) -> float:
            """
            :return: input1 + input2 + 1
            """
            return input1 + input2 + 1
        task = Task(fn=add_inputs)
        self.assertEqual(task(10, 20), 31)

    def test_workers(self) -> None:
        """Tests the sequential worker."""
        for worker in self.workers:
            if not isinstance(worker, Sequential):
                self.check_worker_submit(worker)
            self.check_worker_map(worker)

    def check_worker_map(self, worker: WorkerPool) -> None:
        """
        Check whether worker.map passes all checks.
        :param worker: to be tested.
        """
        task = Task(fn=matrix_multiplication)
        result = worker.map(task, self.lhs_matrix, self.rhs_matrix)
        self.assertEqual(len(result), 1)
        self.validate_result(result)
        number_of_functions = 10
        result = worker.map(task, [self.lhs_matrix] * number_of_functions, self.rhs_matrix)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)
        result = worker.map(task, self.lhs_matrix, [self.rhs_matrix] * number_of_functions)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)
        result = worker.map(task, [self.lhs_matrix] * number_of_functions, [self.rhs_matrix] * number_of_functions)
        self.assertEqual(len(result), number_of_functions)
        self.validate_result(result)

    def check_worker_submit(self, worker: WorkerPool) -> None:
        """
        Check whether worker.submit passes all checks
        :param worker: to be tested
        """
        task = Task(fn=matrix_multiplication)
        result = worker.submit(task, self.lhs_matrix, self.rhs_matrix).result()
        self.assertTrue((result == self.target).all())

    def validate_result(self, results: List[npt.NDArray[np.float32]]) -> None:
        """
        Validate that result from np.dot matched expectations
        :param results: List of results from worker
        """
        for result in results:
            self.assertTrue((result == self.target).all())

    def test_splitter(self) -> None:
        """
        Test chunk splitter
        """
        num_chunks = 10
        chunks = chunk_list([1] * num_chunks, num_chunks)
        self.assertEqual(len(chunks), num_chunks)
        chunks = chunk_list([1, 2, 3, 4, 5], 2)
        self.assertEqual(len(chunks), 2)

def test_workers(self) -> None:
    """Tests the sequential worker."""
    for worker in self.workers:
        if not isinstance(worker, Sequential):
            self.check_worker_submit(worker)
        self.check_worker_map(worker)

@dataclass
class SimulationSetup:
    """Setup class for contructing a Simulation."""
    time_controller: AbstractSimulationTimeController
    observations: AbstractObservation
    ego_controller: AbstractEgoController
    scenario: AbstractScenario

    def __post_init__(self) -> None:
        """Post-initialization sanity checks."""
        assert isinstance(self.time_controller, AbstractSimulationTimeController), 'Error: simulation_time_controller must inherit from AbstractSimulationTimeController!'
        assert isinstance(self.observations, AbstractObservation), 'Error: observations must inherit from AbstractObservation!'
        assert isinstance(self.ego_controller, AbstractEgoController), 'Error: ego_controller must inherit from AbstractEgoController!'

    def reset(self) -> None:
        """
        Reset all simulation controllers
        """
        self.observations.reset()
        self.ego_controller.reset()
        self.time_controller.reset()

def __post_init__(self) -> None:
    """Post-initialization sanity checks."""
    assert isinstance(self.time_controller, AbstractSimulationTimeController), 'Error: simulation_time_controller must inherit from AbstractSimulationTimeController!'
    assert isinstance(self.observations, AbstractObservation), 'Error: observations must inherit from AbstractObservation!'
    assert isinstance(self.ego_controller, AbstractEgoController), 'Error: ego_controller must inherit from AbstractEgoController!'

class OccupancyMapTests(unittest.TestCase):
    """Tests implementation of OccupancyMap"""

    def setUp(self) -> None:
        """Test setup"""
        self.p1 = Polygon([(0, 0), (0, 2), (3, 2), (3, 0)])
        self.p2 = Polygon([(2, 0), (2, 4), (3, 4), (3, 0)])
        self.p3 = Polygon([(4, 0), (4, 2), (5, 2), (5, 0)])
        self.p4 = Polygon([(0, 4), (0, 5), (1.5, 5), (1.5, 4)])
        self.l1 = LineString([(0, 3), (4, 3), (4, 1)])

    def test_intersects_polygon(self):
        """Tests polygon-polygon intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.p2)
            assert not intersection.is_empty()
            intersection = occupancy_map.intersects(self.p3)
            assert intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring(self):
        """Tests polygon-linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1)
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1)
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_intersects_linestring_buffered(self):
        """Tests polygon-buffered linestring intersections correctness"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('4', self.p4.buffer(0.5, cap_style=2))
            intersection = occupancy_map.intersects(self.l1.buffer(0.1, cap_style=2))
            assert intersection.is_empty()
            occupancy_map.insert('2', self.p2)
            intersection = occupancy_map.intersects(self.l1.buffer(0.4, cap_style=2))
            assert not intersection.is_empty()
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_insert_get_set(self):
        """Tests the expected behavior of get and set"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p1])
        strtree_occupancy_map = STRTreeOccupancyMapFactory.get_from_geometry([self.p1])

        def test(occupancy_map: OccupancyMap) -> None:
            assert occupancy_map.size == 1
            occupancy_map.insert('2', self.p3)
            assert occupancy_map.size == 2
            assert self.p3 == occupancy_map.get('2')
            occupancy_map.set('2', self.p2)
            assert self.p2 == occupancy_map.get('2')
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_nearest_entry(self):
        """Tests expected behavior of get_nearest_entry"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            nearest_id, nearest_polygon, distance = occupancy_map.get_nearest_entry_to('0')
            self.assertEqual(nearest_id, '2')
            self.assertEqual(nearest_polygon, self.p4)
            self.assertEqual(distance, 0.5)
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

    def test_get_all(self):
        """Tests the expected behavior of get_all_ids"""
        gp_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])
        strtree_occupancy_map = GeoPandasOccupancyMapFactory.get_from_geometry([self.p2, self.p3, self.p4])

        def test(occupancy_map: OccupancyMap) -> None:
            ids = occupancy_map.get_all_ids()
            assert set(ids) == {'0', '1', '2'}
            assert set(ids) != {'0', '1', '3'}
            geoms = occupancy_map.get_all_geometries()
            for actual, expect in zip(geoms, [self.p2, self.p3, self.p4]):
                assert actual == expect
        test(gp_occupancy_map)
        test(strtree_occupancy_map)

def test(occupancy_map: OccupancyMap) -> None:
    ids = occupancy_map.get_all_ids()
    assert set(ids) == {'0', '1', '2'}
    assert set(ids) != {'0', '1', '3'}
    geoms = occupancy_map.get_all_geometries()
    for actual, expect in zip(geoms, [self.p2, self.p3, self.p4]):
        assert actual == expect

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

def create_path_from_se2(states: List[StateSE2]) -> InterpolatedPath:
    """
    Constructs an InterpolatedPath from a list of StateSE2.
    :param states: Waypoints to construct an InterpolatedPath.
    :return: InterpolatedPath.
    """
    progress_list = calculate_progress(states)
    progress_diff = np.diff(progress_list)
    repeated_states_mask = np.isclose(progress_diff, 0.0)
    progress_states = [ProgressStateSE2(progress=progress, x=point.x, y=point.y, heading=point.heading) for point, progress, is_repeated in zip(states, progress_list, repeated_states_mask) if not is_repeated]
    return InterpolatedPath(progress_states)

def get_starting_segment(agent: Agent, map_api: AbstractMap) -> Tuple[Optional[LaneGraphEdgeMapObject], Optional[float]]:
    """
    Gets the map object that the agent is on and the progress along the segment.
    :param agent: The agent of interested.
    :param map_api: An AbstractMap instance.
    :return: GraphEdgeMapObject and progress along the segment. If no map object is found then None.
    """
    if map_api.is_in_layer(agent.center, SemanticMapLayer.LANE):
        layer = SemanticMapLayer.LANE
    elif map_api.is_in_layer(agent.center, SemanticMapLayer.INTERSECTION):
        layer = SemanticMapLayer.LANE_CONNECTOR
    else:
        return (None, None)
    segments: List[LaneGraphEdgeMapObject] = map_api.get_all_map_objects(agent.center, layer)
    if not segments:
        return (None, None)
    heading_diff = [segment.baseline_path.get_nearest_pose_from_position(agent.center).heading - agent.center.heading for segment in segments]
    closest_segment = segments[np.argmin(np.abs(heading_diff))]
    progress = closest_segment.baseline_path.get_nearest_arc_length_from_position(agent.center)
    return (closest_segment, progress)

@nuplan_test(path='json/idm_manager/')
def test_idm_manager(scene: Dict[str, Any]) -> None:
    """
    Test idm agent manager behaviour when ego is in lane
    """
    simulation_step = 20
    idm_manager = build_idm_manager(scene, map_factory, policy)
    ego_agent = to_agent_state_from_scene(scene['ego'], get_pacifica_parameters(), to_cog=False)
    traffic_light_status = {TrafficLightStatusType.GREEN: cast(List[str], scene['active_lane_connectors']), TrafficLightStatusType.RED: cast(List[str], scene['inactive_lane_connectors'])}
    for step in range(simulation_step):
        idm_manager.propagate_agents(ego_state=ego_agent, tspan=0.5, iteration=0, traffic_light_status=traffic_light_status, open_loop_detections=[], radius=100)
    for geom1, geom2 in itertools.combinations(idm_manager.agent_occupancy.get_all_geometries(), 2):
        assert not geom1.intersects(geom2)

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

def __eq__(self, other: object) -> bool:
    """
        Compare two instances of trajectory sampling
        :param other: object, needs to be TrajectorySampling class
        :return: true, if they are equal, false otherwise
        """
    if not isinstance(other, TrajectorySampling):
        return NotImplemented
    return math.isclose(cast(float, other.time_horizon), cast(float, self.time_horizon)) and math.isclose(cast(float, other.interval_length), cast(float, self.interval_length)) and (other.num_poses == self.num_poses)

def convert_se2_path_to_progress_path(path: List[StateSE2]) -> List[ProgressStateSE2]:
    """
    Converts a list of StateSE2 to a list of ProgressStateSE2

    :return: a list of ProgressStateSE2
    """
    progress_list = calculate_progress(path)
    return [ProgressStateSE2(progress=progress, x=point.x, y=point.y, heading=point.heading) for point, progress in zip(path, progress_list)]

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

def test_calculate_progress(self) -> None:
    """Tests if progress is calculated correctly"""
    progress = calculate_progress(self.path)
    self.assertEqual([0.0, 5.0, 10.0, 14.242640687119284], progress)

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

def setUp(self) -> None:
    """Set up test case."""
    self.max_elements = 30
    self.max_points = 20
    self.interpolation = None
    self.traffic_light_encoding_dim = LaneSegmentTrafficLightData.encoding_dim()

def lane_segment_coords_from_lane_segment_vector(coords: List[List[List[float]]]) -> LaneSegmentCoords:
    """
    Convert lane segment coords [N, 2, 2] to nuPlan LaneSegmentCoords.
    :param coords: lane segment coordinates in vector form.
    :return: lane segment coordinates as LaneSegmentCoords.
    """
    return LaneSegmentCoords([(Point2D(*start), Point2D(*end)) for start, end in coords])

def get_lane_polylines(map_api: AbstractMap, point: Point2D, radius: float) -> Tuple[MapObjectPolylines, MapObjectPolylines, MapObjectPolylines, LaneSegmentLaneIDs]:
    """
    Extract ids, baseline path polylines, and boundary polylines of neighbor lanes and lane connectors around ego vehicle.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about extraction query range.
    :return:
        lanes_mid: extracted lane/lane connector baseline polylines.
        lanes_left: extracted lane/lane connector left boundary polylines.
        lanes_right: extracted lane/lane connector right boundary polylines.
        lane_ids: ids of lanes/lane connector associated polylines were extracted from.
    """
    lanes_mid: List[List[Point2D]] = []
    lanes_left: List[List[Point2D]] = []
    lanes_right: List[List[Point2D]] = []
    lane_ids: List[str] = []
    layer_names = [SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR]
    layers = map_api.get_proximal_map_objects(point, radius, layer_names)
    map_objects: List[MapObject] = []
    for layer_name in layer_names:
        map_objects += layers[layer_name]
    map_objects.sort(key=lambda map_obj: float(get_distance_between_map_object_and_point(point, map_obj)))
    for map_obj in map_objects:
        baseline_path_polyline = [Point2D(node.x, node.y) for node in map_obj.baseline_path.discrete_path]
        lanes_mid.append(baseline_path_polyline)
        lanes_left.append([Point2D(node.x, node.y) for node in map_obj.left_boundary.discrete_path])
        lanes_right.append([Point2D(node.x, node.y) for node in map_obj.right_boundary.discrete_path])
        lane_ids.append(map_obj.id)
    return (MapObjectPolylines(lanes_mid), MapObjectPolylines(lanes_left), MapObjectPolylines(lanes_right), LaneSegmentLaneIDs(lane_ids))

def get_map_object_polygons(map_api: AbstractMap, point: Point2D, radius: float, layer_name: SemanticMapLayer) -> MapObjectPolylines:
    """
    Extract polygons of neighbor map object around ego vehicle for specified semantic layers.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about extraction query range.
    :param layer_name: semantic layer to query.
    :return extracted map object polygons.
    """
    map_objects = map_api.get_proximal_map_objects(point, radius, [layer_name])[layer_name]
    map_objects.sort(key=lambda map_obj: get_distance_between_map_object_and_point(point, map_obj))
    polygons = [extract_polygon_from_map_object(map_obj) for map_obj in map_objects]
    return MapObjectPolylines(polygons)

def get_route_polygon_from_roadblock_ids(map_api: AbstractMap, point: Point2D, radius: float, route_roadblock_ids: List[str]) -> MapObjectPolylines:
    """
    Extract route polygon from map for route specified by list of roadblock ids. Polygon is represented as collection of
        polygons of roadblocks/roadblock connectors encompassing route.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about extraction query range.
    :param route_roadblock_ids: ids of roadblocks/roadblock connectors specifying route.
    :return: A route as sequence of roadblock/roadblock connector polygons.
    """
    route_polygons: List[List[Point2D]] = []
    layer_names = [SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR]
    layers = map_api.get_proximal_map_objects(point, radius, layer_names)
    roadblock_ids: Set[str] = set()
    for layer_name in layer_names:
        roadblock_ids = roadblock_ids.union({map_object.id for map_object in layers[layer_name]})
    route_roadblock_ids = prune_route_by_connectivity(route_roadblock_ids, roadblock_ids)
    for route_roadblock_id in route_roadblock_ids:
        roadblock_obj = map_api.get_map_object(route_roadblock_id, SemanticMapLayer.ROADBLOCK)
        if not roadblock_obj:
            roadblock_obj = map_api.get_map_object(route_roadblock_id, SemanticMapLayer.ROADBLOCK_CONNECTOR)
        if roadblock_obj:
            polygon = extract_polygon_from_map_object(roadblock_obj)
            route_polygons.append(polygon)
    return MapObjectPolylines(route_polygons)

def get_route_lane_polylines_from_roadblock_ids(map_api: AbstractMap, point: Point2D, radius: float, route_roadblock_ids: List[str]) -> MapObjectPolylines:
    """
    Extract route polylines from map for route specified by list of roadblock ids. Route is represented as collection of
        baseline polylines of all children lane/lane connectors or roadblock/roadblock connectors encompassing route.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about extraction query range.
    :param route_roadblock_ids: ids of roadblocks/roadblock connectors specifying route.
    :return: A route as sequence of lane/lane connector polylines.
    """
    route_lane_polylines: List[List[Point2D]] = []
    map_objects = []
    layer_names = [SemanticMapLayer.ROADBLOCK, SemanticMapLayer.ROADBLOCK_CONNECTOR]
    layers = map_api.get_proximal_map_objects(point, radius, layer_names)
    roadblock_ids: Set[str] = set()
    for layer_name in layer_names:
        roadblock_ids = roadblock_ids.union({map_object.id for map_object in layers[layer_name]})
    route_roadblock_ids = prune_route_by_connectivity(route_roadblock_ids, roadblock_ids)
    for route_roadblock_id in route_roadblock_ids:
        roadblock_obj = map_api.get_map_object(route_roadblock_id, SemanticMapLayer.ROADBLOCK)
        if not roadblock_obj:
            roadblock_obj = map_api.get_map_object(route_roadblock_id, SemanticMapLayer.ROADBLOCK_CONNECTOR)
        if roadblock_obj:
            map_objects += roadblock_obj.interior_edges
    map_objects.sort(key=lambda map_obj: float(get_distance_between_map_object_and_point(point, map_obj)))
    for map_obj in map_objects:
        baseline_path_polyline = [Point2D(node.x, node.y) for node in map_obj.baseline_path.discrete_path]
        route_lane_polylines.append(baseline_path_polyline)
    return MapObjectPolylines(route_lane_polylines)

def get_neighbor_vector_map(map_api: AbstractMap, point: Point2D, radius: float) -> Tuple[LaneSegmentCoords, LaneSegmentConnections, LaneSegmentGroupings, LaneSegmentLaneIDs, LaneSegmentRoadBlockIDs]:
    """
    Extract neighbor vector map information around ego vehicle.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about vector map query range.
    :return
        lane_seg_coords: lane_segment coords in shape of [num_lane_segment, 2, 2].
        lane_seg_conns: lane_segment connections [start_idx, end_idx] in shape of [num_connection, 2].
        lane_seg_groupings: collection of lane_segment indices in each lane in shape of
            [num_lane, num_lane_segment_in_lane].
        lane_seg_lane_ids: lane ids of segments at given index in coords in shape of [num_lane_segment 1].
        lane_seg_roadblock_ids: roadblock ids of segments at given index in coords in shape of [num_lane_segment 1].
    """
    lane_seg_coords: List[List[List[float]]] = []
    lane_seg_conns: List[Tuple[int, int]] = []
    lane_seg_groupings: List[List[int]] = []
    lane_seg_lane_ids: List[str] = []
    lane_seg_roadblock_ids: List[str] = []
    cross_blp_conns: Dict[str, Tuple[int, int]] = dict()
    layer_names = [SemanticMapLayer.LANE, SemanticMapLayer.LANE_CONNECTOR]
    nearest_vector_map = map_api.get_proximal_map_objects(point, radius, layer_names)
    for layer_name in layer_names:
        for map_obj in nearest_vector_map[layer_name]:
            start_lane_seg_idx = len(lane_seg_coords)
            trim_nodes = build_lane_segments_from_blps_with_trim(point, radius, map_obj, start_lane_seg_idx)
            if trim_nodes is not None:
                obj_coords, obj_conns, obj_groupings, obj_lane_ids, obj_roadblock_ids, obj_cross_blp_conn = trim_nodes
                lane_seg_coords += obj_coords
                lane_seg_conns += obj_conns
                lane_seg_groupings += obj_groupings
                lane_seg_lane_ids += obj_lane_ids
                lane_seg_roadblock_ids += obj_roadblock_ids
                cross_blp_conns[map_obj.id] = obj_cross_blp_conn
    for lane_conn in nearest_vector_map[SemanticMapLayer.LANE_CONNECTOR]:
        if lane_conn.id in cross_blp_conns:
            lane_seg_conns += connect_trimmed_lane_conn_predecessor(lane_seg_coords, lane_conn, cross_blp_conns)
            lane_seg_conns += connect_trimmed_lane_conn_successor(lane_seg_coords, lane_conn, cross_blp_conns)
    return (lane_segment_coords_from_lane_segment_vector(lane_seg_coords), LaneSegmentConnections(lane_seg_conns), LaneSegmentGroupings(lane_seg_groupings), LaneSegmentLaneIDs(lane_seg_lane_ids), LaneSegmentRoadBlockIDs(lane_seg_roadblock_ids))

class TestVectorUtils(unittest.TestCase):
    """Test vector building utility functions."""

    def setUp(self) -> None:
        """
        Initializes DB
        """
        scenario = MockAbstractScenario()
        ego_state = scenario.initial_ego_state
        self.ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        self.map_api = scenario.map_api
        self.route_roadblock_ids = scenario.get_route_roadblock_ids()
        self.traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
        self.radius = 35
        self.map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
        self._num_past_poses = 1
        self._past_time_horizon = 1.0
        self._num_future_poses = 5
        self._future_time_horizon = 5.0
        current_tl = [TrafficLightStatuses(list(scenario.get_traffic_light_status_at_iteration(iteration=0)))]
        past_tl = scenario.get_past_traffic_light_status_history(iteration=0, num_samples=self._num_past_poses, time_horizon=self._past_time_horizon)
        future_tl = scenario.get_future_traffic_light_status_history(iteration=0, num_samples=self._num_future_poses, time_horizon=self._future_time_horizon)
        past_tl_list = list(past_tl)
        future_tl_list = list(future_tl)
        self.traffic_light_data_over_time = past_tl_list + current_tl + future_tl_list

    def test_prune_route_by_connectivity(self) -> None:
        """
        Test pruning route roadblock ids by those within query radius (specified in roadblock_ids)
        maintaining connectivity.
        """
        route_roadblock_ids = ['-1', '0', '1', '2', '3']
        roadblock_ids = {'0', '1', '3'}
        pruned_route_roadblock_ids = prune_route_by_connectivity(route_roadblock_ids, roadblock_ids)
        self.assertEqual(pruned_route_roadblock_ids, ['0', '1'])

    def test_get_lane_polylines(self) -> None:
        """
        Test extracting lane/lane connector baseline path and boundary polylines from given map api.
        """
        lanes_mid, lanes_left, lanes_right, lane_ids = get_lane_polylines(self.map_api, self.ego_coords, self.radius)
        assert type(lanes_mid) == MapObjectPolylines
        assert type(lanes_left) == MapObjectPolylines
        assert type(lanes_right) == MapObjectPolylines
        assert type(lane_ids) == LaneSegmentLaneIDs

    def test_get_map_object_polygons(self) -> None:
        """
        Test extracting map object polygons from map.
        """
        for layer in [SemanticMapLayer.CROSSWALK, SemanticMapLayer.STOP_LINE]:
            polygons = get_map_object_polygons(self.map_api, self.ego_coords, self.radius, layer)
            assert type(polygons) == MapObjectPolylines

    def test_get_route_polygon_from_roadblock_ids(self) -> None:
        """
        Test extracting route polygon from map given list of roadblock ids.
        """
        route = get_route_polygon_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
        assert type(route) == MapObjectPolylines

    def test_get_route_lane_polylines_from_roadblock_ids(self) -> None:
        """
        Test extracting route lane polylines from map given list of roadblock ids.
        """
        route = get_route_lane_polylines_from_roadblock_ids(self.map_api, self.ego_coords, self.radius, self.route_roadblock_ids)
        assert type(route) == MapObjectPolylines

    def test_get_on_route_status(self) -> None:
        """
        Test identifying whether given roadblock lie within goal route.
        """
        route_roadblock_ids = ['0']
        roadblock_ids = LaneSegmentRoadBlockIDs(['0', '1'])
        on_route_status = get_on_route_status(route_roadblock_ids, roadblock_ids)
        assert type(on_route_status) == LaneOnRouteStatusData
        assert len(on_route_status.on_route_status) == LaneOnRouteStatusData.encoding_dim()
        assert on_route_status.on_route_status[0] == on_route_status.encode(OnRouteStatusType.ON_ROUTE)
        assert on_route_status.on_route_status[1] == on_route_status.encode(OnRouteStatusType.OFF_ROUTE)

    def test_get_neighbor_vector_map(self) -> None:
        """
        Test extracting neighbor vector map information from map api.
        """
        lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(self.map_api, self.ego_coords, self.radius)
        assert type(lane_seg_coords) == LaneSegmentCoords
        assert type(lane_seg_conns) == LaneSegmentConnections
        assert type(lane_seg_groupings) == LaneSegmentGroupings
        assert type(lane_seg_lane_ids) == LaneSegmentLaneIDs
        assert type(lane_seg_roadblock_ids) == LaneSegmentRoadBlockIDs

    def test_get_neighbor_vector_set_map(self) -> None:
        """
        Test extracting neighbor vector set map information from map api.
        """
        coords, traffic_light_data = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, [TrafficLightStatuses(self.traffic_light_data)])
        for feature_name in self.map_features:
            assert feature_name in coords
            assert type(coords[feature_name]) == MapObjectPolylines
        assert len(traffic_light_data) == 1
        assert 'LANE' in traffic_light_data[0]
        assert type(traffic_light_data[0]['LANE']) == LaneSegmentTrafficLightData

    def test_get_neighbor_vector_set_map_for_time_horizon(self) -> None:
        """
        Test extracting neighbor vector set map information from map api.
        """
        coords, traffic_light_data_list = get_neighbor_vector_set_map(self.map_api, self.map_features, self.ego_coords, self.radius, self.route_roadblock_ids, self.traffic_light_data_over_time)
        for feature_name in self.map_features:
            assert feature_name in coords
            assert type(coords[feature_name]) == MapObjectPolylines
        for traffic_light_data in traffic_light_data_list:
            assert 'LANE' in traffic_light_data
            assert type(traffic_light_data['LANE']) == LaneSegmentTrafficLightData

def test_prune_route_by_connectivity(self) -> None:
    """
        Test pruning route roadblock ids by those within query radius (specified in roadblock_ids)
        maintaining connectivity.
        """
    route_roadblock_ids = ['-1', '0', '1', '2', '3']
    roadblock_ids = {'0', '1', '3'}
    pruned_route_roadblock_ids = prune_route_by_connectivity(route_roadblock_ids, roadblock_ids)
    self.assertEqual(pruned_route_roadblock_ids, ['0', '1'])

def test_get_on_route_status(self) -> None:
    """
        Test identifying whether given roadblock lie within goal route.
        """
    route_roadblock_ids = ['0']
    roadblock_ids = LaneSegmentRoadBlockIDs(['0', '1'])
    on_route_status = get_on_route_status(route_roadblock_ids, roadblock_ids)
    assert type(on_route_status) == LaneOnRouteStatusData
    assert len(on_route_status.on_route_status) == LaneOnRouteStatusData.encoding_dim()
    assert on_route_status.on_route_status[0] == on_route_status.encode(OnRouteStatusType.ON_ROUTE)
    assert on_route_status.on_route_status[1] == on_route_status.encode(OnRouteStatusType.OFF_ROUTE)

def _form_lane_segment_coords_connections_from_points(points: List[Point2D], start_lane_segment_index: int) -> Tuple[LaneSegmentCoords, LaneSegmentConnections]:
    """
    Helper function to take in a set of points and convert into an example set of lane segments and lane connections.
    We assume that points i and (i+1) form lane segments l_i.
    We assume lane_segment l_i connects to segment l_{i+1}.
    :param points: The list of points to form lane segments + connections from.
    :param start_lane_segment_index: This is used to label the lane segments by setting the starting value of i above.
    :return: The lane segments coordinates (start + end point) and connectivity (lane_segment_from, lane_segment_to).
    """
    segments = [(p_prev, p_next) for p_prev, p_next in zip(points[:-1], points[1:])]
    connections = [(start_lane_segment_index + idx, start_lane_segment_index + idx + 1) for idx in range(len(segments) - 1)]
    return (LaneSegmentCoords(segments), LaneSegmentConnections(connections))

def _get_neighbor_vector_map_patch(map_api: AbstractMap, point: Point2D, radius: float) -> Tuple[LaneSegmentCoords, LaneSegmentConnections, LaneSegmentGroupings, LaneSegmentLaneIDs, LaneSegmentRoadBlockIDs]:
    """
    A patch for get_neighbor_vector_map that uses the following dummy map for testing.
    Original function docstring:
    Extract neighbor vector map information around ego vehicle.
    :param map_api: map to perform extraction on.
    :param point: [m] x, y coordinates in global frame.
    :param radius: [m] floating number about vector map query range.
    :return
        lane_seg_coords: lane_segment coords in shape of [num_lane_segment, 2, 2].
        lane_seg_conns: lane_segment connections [start_idx, end_idx] in shape of [num_connection, 2].
        lane_seg_groupings: collection of lane_segment indices in each lane in shape of
            [num_lane, num_lane_segment_in_lane].
        lane_seg_lane_ids: lane ids of segments at given index in coords in shape of [num_lane_segment 1].
        lane_seg_roadblock_ids: roadblock ids of segments at given index in coords in shape of [num_lane_segment 1].

    Dummy map setup where ls = lane_segment, lc = lane/lane connector, rb = roadblock.  Origin at the center of the map.

    ls_id    0  1  2  3  4  5
    lc_id   5000    5001   5002
            ______|_____|______

            x--x--x--x--x--x--x
    origin           O
            x--x--x--x--x--x--x
            ______|_____|______
    ls_id    6  7  8  9  10 11
    lc_id   5003    5004   5005
    rb_id   60000  70000  80000
    """
    top_line_points = [Point2D(x=x, y=1) for x in range(-3, 4)]
    top_line_segments_coords, top_line_segment_connections = _form_lane_segment_coords_connections_from_points(points=top_line_points, start_lane_segment_index=0)
    bottom_line_points = [Point2D(x=x, y=-1) for x in range(-3, 4)]
    bottom_line_segments_coords, bottom_line_segment_connections = _form_lane_segment_coords_connections_from_points(points=bottom_line_points, start_lane_segment_index=len(top_line_segments_coords.coords))
    combined_coords = LaneSegmentCoords(coords=top_line_segments_coords.coords + bottom_line_segments_coords.coords)
    combined_connections = LaneSegmentConnections(connections=top_line_segment_connections.connections + bottom_line_segment_connections.connections)
    if len(combined_coords.coords) != 12:
        raise ValueError(f'Expected 12 lane segments to match dummy map.  Got {combined_coords} instead.')
    if len(combined_connections.connections) != 10:
        raise ValueError(f'Expected 10 lane segment connections to match dummy map.  Got {combined_connections} instead.')
    combined_lane_seg_groupings = LaneSegmentGroupings([[x, x + 1] for x in range(0, 12, 2)])
    lane_id_list = [str(x) for x in range(5000, 5006)]
    combined_lane_seg_lane_ids = LaneSegmentLaneIDs([doubled_entry for doubled_entry in itertools.chain.from_iterable(((entry, entry) for entry in lane_id_list))])
    roadblock_id_list = ['60000', '70000', '80000'] * 2
    combined_lane_seg_roadblock_ids = LaneSegmentRoadBlockIDs([doubled_entry for doubled_entry in itertools.chain.from_iterable(((entry, entry) for entry in roadblock_id_list))])
    return (combined_coords, combined_connections, combined_lane_seg_groupings, combined_lane_seg_lane_ids, combined_lane_seg_roadblock_ids)

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

def _map_api(self, map_name: str) -> AbstractMap:
    """
        Get a map api.
        :param map_name: Map name.
        :return Map api.
        """
    if map_name not in self._maps:
        self._maps[map_name] = self._map_factory.build_map_from_name(map_name)
    return self._maps[map_name]

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

@dataclass
class NuBoardFile:
    """Data class to save nuBoard file info."""
    simulation_main_path: str
    metric_main_path: str
    metric_folder: str
    aggregator_metric_folder: str
    simulation_folder: Optional[str] = None
    current_path: Optional[pathlib.Path] = None

    @classmethod
    def extension(cls) -> str:
        """Return nuboard file extension."""
        return '.nuboard'

    def __eq__(self, other: object) -> bool:
        """
        Comparison between two NuBoardFile.
        :param other: Other object.
        :return True if both objects are same.
        """
        if not isinstance(other, NuBoardFile):
            return NotImplemented
        return other.simulation_main_path == self.simulation_main_path and other.simulation_folder == self.simulation_folder and (other.metric_main_path == self.metric_main_path) and (other.metric_folder == self.metric_folder) and (other.aggregator_metric_folder == self.aggregator_metric_folder) and (other.current_path == self.current_path)

    def save_nuboard_file(self, filename: pathlib.Path) -> None:
        """
        Save NuBoardFile data class to a file.
        :param filename: The saved file path.
        """
        save_object_as_pickle(filename, self.serialize())

    @classmethod
    def load_nuboard_file(cls, filename: pathlib.Path) -> NuBoardFile:
        """
        Read a NuBoard file to NuBoardFile data class.
        :file: NuBoard file path.
        """
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        return cls.deserialize(data=data)

    def serialize(self) -> Dict[str, str]:
        """
        Serialization of NuBoardFile data class to dictionary.
        :return A serialized dictionary class.
        """
        as_dict = {'simulation_main_path': self.simulation_main_path, 'metric_main_path': self.metric_main_path, 'metric_folder': self.metric_folder, 'aggregator_metric_folder': self.aggregator_metric_folder}
        if self.simulation_folder is not None:
            as_dict['simulation_folder'] = self.simulation_folder
        return as_dict

    @classmethod
    def deserialize(cls, data: Dict[str, str]) -> NuBoardFile:
        """
        Deserialization of a NuBoard file into NuBoardFile data class.
        :param data: A serialized nuboard file data.
        :return A NuBoard file data class.
        """
        simulation_main_path = data['simulation_main_path'].replace('//', '/')
        metric_main_path = data['metric_main_path'].replace('//', '/')
        return NuBoardFile(simulation_main_path=simulation_main_path, simulation_folder=data.get('simulation_folder', None), metric_main_path=metric_main_path, metric_folder=data['metric_folder'], aggregator_metric_folder=data['aggregator_metric_folder'])

def __eq__(self, other: object) -> bool:
    """
        Comparison between two NuBoardFile.
        :param other: Other object.
        :return True if both objects are same.
        """
    if not isinstance(other, NuBoardFile):
        return NotImplemented
    return other.simulation_main_path == self.simulation_main_path and other.simulation_folder == self.simulation_folder and (other.metric_main_path == self.metric_main_path) and (other.metric_folder == self.metric_folder) and (other.aggregator_metric_folder == self.aggregator_metric_folder) and (other.current_path == self.current_path)

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

def __eq__(self, other: object) -> bool:
    """Compare equality."""
    if not isinstance(other, MetricStatisticsDataFrame):
        return NotImplemented
    return self.metric_statistic_name == other.metric_statistic_name and self.metric_statistics_dataframe.equals(other.metric_statistics_dataframe)

def get_current_route_objects(map_api: AbstractMap, pose: Point2D) -> List[GraphEdgeMapObject]:
    """
    Gets the list including the lane or lane_connectors the pose corresponds to if there exists one, and empty list o.w
    :param map_api: map
    :param pose: xy coordinates
    :return the corresponding route object.
    """
    curr_lane = map_api.get_one_map_object(pose, SemanticMapLayer.LANE)
    if curr_lane is None:
        curr_lane_connectors = map_api.get_all_map_objects(pose, SemanticMapLayer.LANE_CONNECTOR)
        route_objects_with_pose = curr_lane_connectors
    else:
        route_objects_with_pose = [curr_lane]
    return route_objects_with_pose

def remove_extra_lane_connectors(route_objs: List[List[GraphEdgeMapObject]]) -> List[List[GraphEdgeMapObject]]:
    """
    # This function iterate through route object and replace field with multiple lane_connectors
    # with the one lane_connector ego ends up in.
    :param route_objs: a list of route objects.
    """
    last_to_first_route_list = route_objs[::-1]
    enum = enumerate(last_to_first_route_list)
    for ind, curr_last_obj in enum:
        if ind == 0 or len(curr_last_obj) <= 1:
            continue
        if len(curr_last_obj) > len(last_to_first_route_list[ind - 1]):
            curr_route_obj_ids = [obj.id for obj in curr_last_obj]
            if all([obj.id in curr_route_obj_ids for obj in last_to_first_route_list[ind - 1]]):
                last_to_first_route_list[ind] = last_to_first_route_list[ind - 1]
        if len(curr_last_obj) <= 1:
            continue
        if last_to_first_route_list[ind - 1] and isinstance(last_to_first_route_list[ind - 1][0], Lane):
            next_lane_incoming_edge_ids = [obj.id for obj in last_to_first_route_list[ind - 1][0].incoming_edges]
            objs_to_keep = [obj for obj in curr_last_obj if obj.id in next_lane_incoming_edge_ids]
            if objs_to_keep:
                last_to_first_route_list[ind] = objs_to_keep
    return last_to_first_route_list[::-1]

def get_route_baseline_roadblock_linkedlist(map_api: AbstractMap, expert_route: List[List[LaneGraphEdgeMapObject]]) -> RouteRoadBlockLinkedList:
    """
    This function generates a linked list of baseline & unique road-block pairs
    (RouteBaselineRoadBlockPair) from a simplified route
    :param map_api: Corresponding map
    :param expert_route: A route list
    :return A linked list of RouteBaselineRoadBlockPair.
    """
    route_baseline_roadblock_list = RouteRoadBlockLinkedList()
    prev_roadblock_id = None
    for route_object in expert_route:
        if route_object:
            roadblock_id = route_object[0].get_roadblock_id()
            if roadblock_id != prev_roadblock_id:
                prev_roadblock_id = roadblock_id
                if isinstance(route_object[0], Lane):
                    road_block = map_api.get_map_object(roadblock_id, SemanticMapLayer.ROADBLOCK)
                else:
                    road_block = map_api.get_map_object(roadblock_id, SemanticMapLayer.ROADBLOCK_CONNECTOR)
                ref_baseline_path = route_object[0].baseline_path
                if route_baseline_roadblock_list.head is None:
                    prev_route_baseline_roadblock = RouteBaselineRoadBlockPair(base_line=ref_baseline_path, road_block=road_block)
                    route_baseline_roadblock_list.head = prev_route_baseline_roadblock
                else:
                    prev_route_baseline_roadblock.next = RouteBaselineRoadBlockPair(base_line=ref_baseline_path, road_block=road_block)
                    prev_route_baseline_roadblock = prev_route_baseline_roadblock.next
    return route_baseline_roadblock_list

def get_timestamps_in_common_or_connected_route_objs(common_or_connected_route_objs: List[Optional[Set[GraphEdgeMapObject]]], ego_timestamps: npt.NDArray[np.int32]) -> List[int]:
    """
    Extract timestamps when ego's corners are in common or connected lane/lane connectors.
    :param common_or_connected_route_objs: list of common or connected lane/lane connectors of corners if exist,
    empty list if all corners are in non_drivable area and None if corners are in different lane/lane connectors
    :param ego_timestamps: Array of times in time_us
    :return List of ego_timestamps where all corners of ego are in common or connected route objects
    """
    return [timestamp for route_obj, timestamp in zip(common_or_connected_route_objs, ego_timestamps) if route_obj]

def build_mock_history_scenario_test(scene: Dict[str, Any]) -> Tuple[SimulationHistory, MockAbstractScenario]:
    """
    A common template to create a test history and scenario.
    :param scene: A json format to represent a scene.
    :return The mock history and scenario.
    """
    goal_pose = None
    if 'goal' in scene and 'pose' in scene['goal'] and scene['goal']['pose']:
        goal_pose = StateSE2(x=scene['goal']['pose'][0], y=scene['goal']['pose'][1], heading=scene['goal']['pose'][2])
    if 'ego' in scene and 'time_us' in scene['ego'] and ('ego_future_states' in scene) and scene['ego_future_states'] and ('time_us' in scene['ego_future_states'][0]):
        initial_time_us = TimePoint(time_us=scene['ego']['time_us'])
        time_step = (scene['ego_future_states'][0]['time_us'] - scene['ego']['time_us']) * 1e-06
        mock_abstract_scenario = MockAbstractScenario(initial_time_us=initial_time_us, time_step=time_step)
    else:
        mock_abstract_scenario = MockAbstractScenario()
    if goal_pose is not None:
        mock_abstract_scenario.get_mission_goal = lambda: goal_pose
    history = setup_history(scene, mock_abstract_scenario)
    return (history, mock_abstract_scenario)

def metric_statistic_test(scene: Dict[str, Any], metric: AbstractMetricBuilder, history: Optional[SimulationHistory]=None, mock_abstract_scenario: Optional[MockAbstractScenario]=None) -> MetricStatistics:
    """
    A common template to test metric statistics.
    :param scene: A json format to represent a scene.
    :param metric: An evaluation metric.
    :param history: A SimulationHistory history.
    :param mock_abstract_scenario: A scenario.
    :return Metric statistics.
    """
    if not history or not mock_abstract_scenario:
        history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    metric_results = metric.compute(history, mock_abstract_scenario)
    expected_statistics_list = scene['expected']
    if not isinstance(expected_statistics_list, list):
        expected_statistics_list = [expected_statistics_list]
    for ind, metric_result in enumerate(metric_results):
        statistics = metric_result.statistics
        expected_statistic = expected_statistics_list[ind]['statistics']
        assert len(expected_statistic) == len(statistics), f'Length of actual ({len(statistics)}) and expected ({len(expected_statistic)}) statistics must be same!'
        for expected_statistic, statistic in zip(expected_statistic, statistics):
            expected_type, expected_value = expected_statistic
            assert expected_type == str(statistic.type), f"Statistic types don't match. Actual: {statistic.type}, Expected: {expected_type}"
            assert np.isclose(expected_value, statistic.value, atol=0.01), f"Statistic values don't match. Actual: {statistic.value}, Expected: {expected_value}"
        expected_time_series = expected_statistics_list[ind].get('time_series', None)
        if expected_time_series and metric_result.time_series is not None:
            time_series = metric_result.time_series
            expected_time_series = expected_statistics_list[ind]['time_series']
            assert isinstance(time_series, TimeSeries), 'Time series type not correct.'
            assert time_series.time_stamps == expected_time_series['time_stamps'], 'Time stamps are not correct.'
            assert np.all(np.round(time_series.values, 2) == expected_time_series['values']), 'Time stamp values are not correct.'
    return metric_result

@nuplan_test(path='json/route_extractor/route_extractor.json')
def test_get_route_and_simplify(scene: Dict[str, Any]) -> None:
    """
    Test getting route from ego pose and simplifying.
    """
    map_api = map_factory.build_map_from_name(scene['map']['area'])
    poses = []
    for marker in scene['markers']:
        poses.append(Point2D(*marker['pose'][:2]))
    expert_route = get_route(map_api=map_api, poses=poses)
    assert len(expert_route) == len(poses)
    all_route_obj = [map_object for map_objects in expert_route for map_object in map_objects]
    assert len(all_route_obj) == len(poses)
    route_simplified = get_route_simplified(expert_route)
    assert len(route_simplified) == 3

@nuplan_test(path='json/route_extractor/route_extractor.json')
def test_corners_route_extraction(scene: Dict[str, Any]) -> None:
    """
    Test getting ego's corners route objects.
    """
    map_api = map_factory.build_map_from_name(scene['map']['area'])
    vehicle_parameters = get_pacifica_parameters()
    expert_footprints = []
    for marker in scene['markers']:
        expert_footprints.append(CarFootprint.build_from_center(StateSE2(*marker['pose'][:3]), vehicle_parameters))
    corners_route = extract_corners_route(map_api=map_api, ego_footprint_list=expert_footprints)
    assert len(corners_route) == len(expert_footprints)
    all_route_obj = [map_object for corners_objects in corners_route for corner in corners_objects.__dict__.values() for map_object in corner]
    unique_route_obj_ids = {obj.id for obj in all_route_obj}
    assert len(unique_route_obj_ids) == 4

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

def _get_collision_type(ego_state: EgoState, tracked_object: TrackedObject, stopped_speed_threshold: float=0.05) -> CollisionType:
    """
    Classify collision between ego and the track.
    :param ego_state: Ego's state at the current timestamp.
    :param tracked_object: Tracked object.
    :param stopped_speed_threshold: Threshold for 0 speed due to noise.
    :return Collision type.
    """
    is_ego_stopped = ego_state.dynamic_car_state.speed <= stopped_speed_threshold
    if is_ego_stopped:
        collision_type = CollisionType.STOPPED_EGO_COLLISION
    elif is_track_stopped(tracked_object):
        collision_type = CollisionType.STOPPED_TRACK_COLLISION
    elif is_agent_behind(ego_state.rear_axle, tracked_object.box.center):
        collision_type = CollisionType.ACTIVE_REAR_COLLISION
    elif LineString([ego_state.car_footprint.oriented_box.geometry.exterior.coords[0], ego_state.car_footprint.oriented_box.geometry.exterior.coords[3]]).intersects(tracked_object.box.geometry):
        collision_type = CollisionType.ACTIVE_FRONT_COLLISION
    else:
        collision_type = CollisionType.ACTIVE_LATERAL_COLLISION
    return collision_type

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
def not_in_drivable_area_with_route_object(pose: Point2D, route_object: List[GraphEdgeMapObject], map_api: AbstractMap) -> bool:
    """
        Return a boolean is_in_drivable_area.
        :param pose: pose.
        :param route_object: lane/lane connector of that pose or empty list.
        :param map_api: map.
        :return: a boolean is_in_drivable_area.
        """
    return not route_object and (not map_api.is_in_layer(pose, layer=SemanticMapLayer.DRIVABLE_AREA))

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

def extract_tracks_info_excluding_collided_tracks(ego_states: List[EgoState], ego_timestamps: npt.NDArray[np.int64], observations: List[Observation], all_collisions: List[Collisions], timestamps_in_common_or_connected_route_objs: List[int], map_api: AbstractMap) -> TRACKS_POSE_SPEED_BOX:
    """
    Extracts arrays of tracks pose, speed and oriented box for TTC: all lead and cross tracks, plus lateral tracks if ego is in
    between lanes or in nondrivable area or in intersection.

    :param ego_states: A list of ego states
    :param ego_timestamps: Array of times in time_us
    :param observations: A list of observations
    :param all_collisions: List of all collisions in the history
    :param timestamps_in_common_or_connected_route_objs: List of timestamps where ego is in same or connected
        lanes/lane connectors
    :param map_api: map api.
    :return: A tuple of lists of arrays of tracks pose, speed and represented box at each timestep.
    """
    collided_track_ids: Set[str] = set()
    history_tracks_poses: List[npt.NDArray[np.float64]] = []
    history_tracks_speed: List[npt.NDArray[np.float64]] = []
    history_tracks_boxes: List[npt.NDArray[OrientedBox]] = []
    collision_time_dict = {collision.timestamp: list(collision.collisions_id_data.keys()) for collision in all_collisions}
    for ego_state, timestamp, observation in zip(ego_states, ego_timestamps, observations):
        collided_track_ids = collided_track_ids.union(set(collision_time_dict.get(timestamp, [])))
        ego_not_in_common_or_connected_route_objs = timestamp not in timestamps_in_common_or_connected_route_objs
        tracked_objects = [tracked_object for tracked_object in observation.tracked_objects if tracked_object.track_token not in collided_track_ids and (is_agent_ahead(ego_state.rear_axle, tracked_object.center) or ((ego_not_in_common_or_connected_route_objs or map_api.is_in_layer(ego_state.rear_axle, layer=SemanticMapLayer.INTERSECTION)) and (not is_agent_behind(ego_state.rear_axle, tracked_object.center))))]
        poses: List[npt.NDArray[np.float64]] = [np.array([*tracked_object.center], dtype=np.float64) for tracked_object in tracked_objects]
        speeds: List[npt.NDArray[np.float64]] = [np.array(tracked_object.velocity.magnitude(), dtype=np.float64) if isinstance(tracked_object, Agent) else 0 for tracked_object in tracked_objects]
        boxes: List[OrientedBox] = [tracked_object.box for tracked_object in tracked_objects]
        history_tracks_poses.append(np.array(poses))
        history_tracks_speed.append(np.array(speeds))
        history_tracks_boxes.append(np.array(boxes))
    return (history_tracks_poses, history_tracks_speed, history_tracks_boxes)

@nuplan_test(path='json/ego_lon_jerk/ego_lon_jerk.json')
def test_ego_longitudinal_jerk(scene: Dict[str, Any]) -> None:
    """
    Tests ego longitudinal jerk statistics as expected.
    :param scene: the json scene
    """
    metric = EgoLonJerkStatistics('ego_lon_jerk_statistics', 'Dynamics', max_abs_lon_jerk=8.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/driving_direction_compliance/ego_does_not_drive_backward.json')
def test_ego_no_backward_driving(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress metric when there's no route.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivingDirectionComplianceStatistics('driving_direction_compliance', 'Planning', lane_change_metric, driving_direction_compliance_threshold=2, driving_direction_violation_threshold=6, time_horizon=1)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/driving_direction_compliance/ego_drives_backward.json')
def test_ego_backward_driving(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress metric when ego drives backward more than driving_direction_violation_threshold.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivingDirectionComplianceStatistics('driving_direction_compliance', 'Planning', lane_change_metric, driving_direction_compliance_threshold=2, driving_direction_violation_threshold=6, time_horizon=1)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/driving_direction_compliance/ego_slightly_drives_backward.json')
def test_ego_slightly_backward_driving(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress metric when ego drives backward more than driving_direction_compliance_threshold but less than driving_direction_violation_threshold.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivingDirectionComplianceStatistics('driving_direction_compliance', 'Planning', lane_change_metric, driving_direction_compliance_threshold=2, driving_direction_violation_threshold=15, time_horizon=1)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/drivable_area_compliance/drivable_area_violation.json')
def test_violations_detected_and_reported(scene: Dict[str, Any]) -> None:
    """
    Tests drivable area violation metric, by checking the detection and the depth of violation on a made up scenario.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivableAreaComplianceStatistics('drivable_area_compliance', 'Planning', lane_change_metric, 0.3)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/drivable_area_compliance/no_drivable_area_violation.json')
def test_works_with_no_violations(scene: Dict[str, Any]) -> None:
    """
    Tests drivable area violation metric, by checking the detection and the depth of violation on a made up scenario.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivableAreaComplianceStatistics('drivable_area_compliance', 'Planning', lane_change_metric, 0.3)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/drivable_area_compliance/small_drivable_area_violation.json')
def test_works_with_small_violations(scene: Dict[str, Any]) -> None:
    """
    Tests drivable area violation metric when ego's footprint overapproximation is slightly outside drivable area.
    :param scene: the json scene
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivableAreaComplianceStatistics('drivable_area_compliance', 'Planning', lane_change_metric, 0.3)
    metric_statistic_test(scene=scene, metric=metric)
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.1)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = DrivableAreaComplianceStatistics('drivable_area_compliance', 'Planning', lane_change_metric, 0.3)
    metric.compute(history, mock_abstract_scenario)
    assert np.isclose(metric.results[0].statistics[0].value, 0, atol=0.01)

@nuplan_test(path='json/planner_expert_average_heading_error_within_bound/low_average_heading_error.json')
def test_planner_expert_average_heading_error(scene: Dict[str, Any]) -> None:
    """
    Tests planner_expert_average_heading_error is expected value.
    :param scene: the json scene.
    """
    planner_expert_average_l2_error_within_bound_metric = PlannerExpertAverageL2ErrorStatistics('planner_expert_average_l2_error', 'Planning', comparison_horizon=[3, 5, 8], comparison_frequency=1, max_average_l2_error_threshold=8)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    planner_expert_average_l2_error_within_bound_metric.compute(history, mock_abstract_scenario)
    metric = PlannerExpertAverageHeadingErrorStatistics('planner_expert_average_heading_error_within_bound', 'Planning', planner_expert_average_l2_error_within_bound_metric, max_average_heading_error_threshold=0.8)
    metric_statistic_test(scene, metric, history, mock_abstract_scenario)

def _run_time_to_collision_test(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision
    :param scene: the json scene
    """
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    no_ego_at_fault_collisions_metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Dynamics', ego_lane_change_metric)
    no_ego_at_fault_collisions_metric.compute(history, mock_abstract_scenario)[0]
    metric = TimeToCollisionStatistics('time_to_collision_statistics', 'Planning', ego_lane_change_metric, no_ego_at_fault_collisions_metric, **scene['metric_parameters'])
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/time_to_collision_within_bound/time_to_collision_above_threshold.json')
def test_time_to_collision_above_threshold(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision when above threshold.
    :param scene: the json scene
    """
    _run_time_to_collision_test(scene)

@nuplan_test(path='json/time_to_collision_within_bound/in_collision.json')
def test_time_to_collision_in_collision(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision in case where there is a collision.
    :param scene: the json scene
    """
    _run_time_to_collision_test(scene)

@nuplan_test(path='json/time_to_collision_within_bound/ego_stopped.json')
def test_time_to_collision_ego_stopped(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision when ego is stopped.
    :param scene: the json scene
    """
    _run_time_to_collision_test(scene)

@nuplan_test(path='json/time_to_collision_within_bound/no_collisions.json')
def test_time_to_collision_no_collisions(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision when there are relevant tracks, but ego will not collide.
    :param scene: the json scene
    """
    _run_time_to_collision_test(scene)

@nuplan_test(path='json/time_to_collision_within_bound/no_relevant_tracks.json')
def test_time_to_collision_no_relevant_tracks(scene: Dict[str, Any]) -> None:
    """
    Test predicted time to collision when no relevant tracks.
    :param scene: the json scene
    """
    _run_time_to_collision_test(scene)

@nuplan_test(path='json/ego_mean_speed/ego_mean_speed.json')
def test_ego_mean_speed(scene: Dict[str, Any]) -> None:
    """
    Tests ego mean speed statistics as expected.
    :param scene: the json scene
    """
    metric = EgoMeanSpeedStatistics('ego_lon_jerk_statistics', 'Dynamics')
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_acceleration/ego_acceleration.json')
def test_ego_expected_acceleration(scene: Dict[str, Any]) -> None:
    """
    Tests ego acceleration by checking if it is the expected acceleration.
    :param scene: the json scene
    """
    metric = EgoAccelerationStatistics('ego_acceleration_statistics', 'Dynamics')
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_is_comfortable/ego_is_comfortable.json')
def test_ego_is_comfortable(scene: Dict[str, Any]) -> None:
    """
    Tests ego is comfortable by checking if it is the expected comfortable.
    :param scene: the json scene
    """
    ego_jerk_metric = EgoJerkStatistics('ego_jerk', 'Dynamics', max_abs_mag_jerk=8.37)
    ego_lat_accel_metric = EgoLatAccelerationStatistics('ego_lat_accel', 'Dynamics', max_abs_lat_accel=4.89)
    ego_lon_accel_metric = EgoLonAccelerationStatistics('ego_lon_accel', 'Dynamics', min_lon_accel=-4.05, max_lon_accel=2.4)
    ego_lon_jerk_metric = EgoLonJerkStatistics('ego_lon_jerk', 'dynamic', max_abs_lon_jerk=4.13)
    ego_yaw_accel_metric = EgoYawAccelerationStatistics('ego_yaw_accel', 'dynamic', max_abs_yaw_accel=1.93)
    ego_yaw_rate_metric = EgoYawRateStatistics('ego_yaw_rate', 'dynamic', max_abs_yaw_rate=0.95)
    metric = EgoIsComfortableStatistics(name='ego_is_comfortable_statistics', category='Dynamics', ego_jerk_metric=ego_jerk_metric, ego_lat_acceleration_metric=ego_lat_accel_metric, ego_lon_acceleration_metric=ego_lon_accel_metric, ego_lon_jerk_metric=ego_lon_jerk_metric, ego_yaw_acceleration_metric=ego_yaw_accel_metric, ego_yaw_rate_metric=ego_yaw_rate_metric)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_jerk/ego_jerk.json')
def test_ego_jerk(scene: Dict[str, Any]) -> None:
    """
    Tests ego jerk statistics as expected.
    :param scene: the json scene
    """
    metric = EgoJerkStatistics('ego_jerk_statistics', 'Dynamics', max_abs_mag_jerk=7.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/no_ego_at_fault_collision/no_collision.json')
def test_no_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is no collision as expected.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_result = metric_statistic_test(scene=scene, metric=metric)
    statistics = metric_result.statistics
    assert statistics[1].value == 0
    assert len(metric.all_collisions) == 0

@nuplan_test(path='json/no_ego_at_fault_collision/active_front_collision.json')
def test_active_front_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is one front collision in this scene.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 1
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.ACTIVE_FRONT_COLLISION

@nuplan_test(path='json/no_ego_at_fault_collision/active_lateral_collision.json')
def test_active_lateral_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is one lateral collision in this scene which is at fault.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 1
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.ACTIVE_LATERAL_COLLISION

@nuplan_test(path='json/no_ego_at_fault_collision/active_rear_collision.json')
def test_active_rear_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is one rear collision in this scene which is not at fault.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 1
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.ACTIVE_REAR_COLLISION

@nuplan_test(path='json/no_ego_at_fault_collision/stopped_track_collision.json')
def test_stopped_track_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is one collision with a stopped track in this scene which is at fault.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 1
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.STOPPED_TRACK_COLLISION

@nuplan_test(path='json/no_ego_at_fault_collision/stopped_ego_collision.json')
def test_stopped_ego_collision(scene: Dict[str, Any]) -> None:
    """
    Tests there is one collision when ego is stopped in this scene which is not at fault.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 1
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.STOPPED_EGO_COLLISION

@nuplan_test(path='json/no_ego_at_fault_collision/multiple_collisions.json')
def test_multiple_collisions(scene: Dict[str, Any]) -> None:
    """
    Tests there are 4 tracks and 3 collisions in this scene, and there are 2 at-fault-collisions for which
    we find the violation metric.
    :param scene: the json scene
    """
    ego_lane_change_metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    _ = ego_lane_change_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoAtFaultCollisionStatistics('no_ego_at_fault_collisions_statistics', 'Planning', ego_lane_change_metric)
    metric_statistic_test(scene=scene, metric=metric)
    assert np.sum([len(collision.collisions_id_data) for collision in metric.all_collisions]) == 3
    assert list(metric.all_collisions[0].collisions_id_data.values())[0].collision_type == CollisionType.ACTIVE_LATERAL_COLLISION
    assert list(metric.all_collisions[1].collisions_id_data.values())[0].collision_type == CollisionType.ACTIVE_FRONT_COLLISION
    assert list(metric.all_collisions[1].collisions_id_data.values())[1].collision_type == CollisionType.ACTIVE_FRONT_COLLISION

@nuplan_test(path='json/ego_yaw_rate/ego_yaw_rate.json')
def test_ego_yaw_rate(scene: Dict[str, Any]) -> None:
    """
    Tests ego yaw rate statistics as expected.
    :param scene: the json scene
    """
    metric = EgoYawRateStatistics('ego_yaw_rate_statistics', 'Dynamics', max_abs_yaw_rate=5.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_lon_acceleration/ego_lon_acceleration.json')
def test_ego_longitudinal_acceleration(scene: Dict[str, Any]) -> None:
    """
    Tests ego longitudinal acceleration statistics as expected
    :param scene: the json scene.
    """
    metric = EgoLonAccelerationStatistics('ego_lon_acceleration_statistics', 'Dynamics', min_lon_accel=0.0, max_lon_accel=10.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/planner_miss_rate_within_bound/high_miss_rate.json')
def test_planner_miss_rate(scene: Dict[str, Any]) -> None:
    """
    Tests planner_miss_rate is expected value.
    :param scene: the json scene.
    """
    planner_expert_average_l2_error_within_bound_metric = PlannerExpertAverageL2ErrorStatistics('planner_expert_average_l2_error_within_bound', 'Planning', comparison_horizon=[3, 5, 8], comparison_frequency=1, max_average_l2_error_threshold=8)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    planner_expert_average_l2_error_within_bound_metric.compute(history, mock_abstract_scenario)
    metric = PlannerMissRateStatistics('planner_miss_rate_within_bound_statistics', 'Planning', planner_expert_average_l2_error_within_bound_metric, max_displacement_threshold=[6, 8, 16], max_miss_rate_threshold=0.3)
    metric_statistic_test(scene, metric, history, mock_abstract_scenario)

@nuplan_test(path='json/ego_expert_l2_error_with_yaw/ego_expert_l2_error_with_yaw.json')
def test_ego_expert_l2_error_with_yaw(scene: Dict[str, Any]) -> None:
    """
    Tests ego expert l2 error with yaw is expected value.
    :param scene: the json scene
    """
    metric = EgoExpertL2ErrorWithYawStatistics('ego_expert_L2_error_with_yaw', 'Dynamics', discount_factor=1.0, heading_diff_weight=2.5)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_expert_l2_error_with_yaw/ego_expert_l2_error_with_yaw_zero.json')
def test_ego_expert_l2_error_with_yaw_zero(scene: Dict[str, Any]) -> None:
    """
    Tests ego expert l2 error with yaw is zero.
    :param scene: the json scene
    """
    metric = EgoExpertL2ErrorWithYawStatistics('ego_expert_L2_error_with_yaw', 'Dynamics', discount_factor=1.0, heading_diff_weight=2.5)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_yaw_acceleration/ego_yaw_acceleration.json')
def test_ego_yaw_acceleration(scene: Dict[str, Any]) -> None:
    """
    Tests ego yaw acceleration statistics as expected.
    :param scene: the json scene
    """
    metric = EgoYawAccelerationStatistics('ego_yaw_acceleration_statistics', 'Dynamics', max_abs_yaw_accel=3.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_lat_jerk/ego_lat_jerk.json')
def test_ego_lateral_jerk(scene: Dict[str, Any]) -> None:
    """
    Tests ego lateral jerk statistics as expected.
    :param scene: the json scene
    """
    metric = EgoLatJerkStatistics('ego_lat_jerk_statistics', 'Dynamics')
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/planner_expert_final_heading_error_within_bound/low_final_heading_error.json')
def test_planner_expert_final_heading_error(scene: Dict[str, Any]) -> None:
    """
    Tests planner_expert_final_heading_error is expected value.
    :param scene: the json scene.
    """
    planner_expert_average_l2_error_within_bound = PlannerExpertAverageL2ErrorStatistics('planner_expert_average_l2_error', 'Planning', comparison_horizon=[3, 5, 8], comparison_frequency=1, max_average_l2_error_threshold=8)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    planner_expert_average_l2_error_within_bound.compute(history, mock_abstract_scenario)
    metric = PlannerExpertFinalHeadingErrorStatistics('planner_expert_final_heading_error_within_bound', 'Planning', planner_expert_average_l2_error_within_bound, max_final_heading_error_threshold=0.8)
    metric_statistic_test(scene, metric, history, mock_abstract_scenario)

@nuplan_test(path='json/ego_expert_l2_error/ego_expert_l2_error.json')
def test_ego_expert_l2_error(scene: Dict[str, Any]) -> None:
    """
    Tests ego expert l2 error is expected value.
    :param scene: the json scene
    """
    metric = EgoExpertL2ErrorStatistics('ego_expert_L2_error', 'Dynamics', discount_factor=1.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_lane_change/ego_lane_change.json')
def test_ego_lane_change(scene: Dict[str, Any]) -> None:
    """
    Tests ego lane change statistics as expected.
    :param scene: the json scene
    """
    metric = EgoLaneChangeStatistics('ego_lane_change_statistics', 'Planning', max_fail_rate=0.3)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/planner_expert_average_l2_error_within_bound/high_average_l2_error.json')
def test_planner_miss_rate(scene: Dict[str, Any]) -> None:
    """
    Tests planner_expert_average_l2_error is expected value.
    :param scene: the json scene.
    """
    metric = PlannerExpertAverageL2ErrorStatistics('planner_expert_average_l2_error', 'Planning', comparison_horizon=[3, 5, 8], comparison_frequency=1, max_average_l2_error_threshold=8)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_lat_acceleration/ego_lat_acceleration.json')
def test_ego_lateral_acceleration(scene: Dict[str, Any]) -> None:
    """
    Tests ego lateral acceleration statistics as expected.
    :param scene: the json scene
    """
    metric = EgoLatAccelerationStatistics('ego_lat_acceleration_statistics', 'Dynamics', max_abs_lat_accel=10.0)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/speed_limit_compliance/speed_limit_violation.json')
def test_speed_limit_violation(scene: Dict[str, Any]) -> None:
    """
    Tests speed limit violation, by checking the detection and the depth of compliance on a made up scenario
    :param scene: the json scene.
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = SpeedLimitComplianceStatistics('speed_limit_compliance', '', lane_change_metric=lane_change_metric, max_violation_threshold=1, max_overspeed_value_threshold=2.23)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/speed_limit_compliance/no_speed_limit_violation.json')
def test_no_violations(scene: Dict[str, Any]) -> None:
    """
    Tests speed limit violation, by checking that the metric works without violations
    :param scene: the json scene.
    """
    lane_change_metric = EgoLaneChangeStatistics('lane_change', 'Planning', 0.3)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    lane_change_metric.compute(history, mock_abstract_scenario)
    metric = SpeedLimitComplianceStatistics('speed_limit_compliance', '', lane_change_metric=lane_change_metric, max_violation_threshold=1, max_overspeed_value_threshold=2.23)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_progress_along_expert_route/ego_progress_along_expert_route.json')
def test_ego_progress_to_goal(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress along expert route statistics as expected.
    :param scene: the json scene
    """
    metric = EgoProgressAlongExpertRouteStatistics('ego_progress_along_expert_route_statistics', 'Dynamics', score_progress_threshold=2)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_progress_along_expert_route/ego_no_progress_along_expert_route.json')
def test_ego_no_progress_to_goal(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress along expert route statistics when expert isn't assigned a route at first and ego isn't making enough progress.
    :param scene: the json scene
    """
    metric = EgoProgressAlongExpertRouteStatistics('ego_progress_along_expert_route_statistics', 'Dynamics', score_progress_threshold=2)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_progress_along_expert_route/ego_no_route.json')
def test_no_route(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress metric when there's no route.
    :param scene: the json scene
    """
    metric = EgoProgressAlongExpertRouteStatistics('ego_progress_along_expert_route_statistics', 'Dynamics', score_progress_threshold=2)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_progress_along_expert_route/ego_drives_backward.json')
def test_ego_backward_driving(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress metric when ego drives backward.
    :param scene: the json scene
    """
    metric = EgoProgressAlongExpertRouteStatistics('ego_progress_along_expert_route_statistics', 'Dynamics', score_progress_threshold=2)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/ego_is_making_progress/ego_is_making_progress.json')
def test_ego_progress_to_goal(scene: Dict[str, Any]) -> None:
    """
    Tests ego progress along expert route statistics as expected.
    :param scene: the json scene
    """
    ego_progress_along_expert_route_metric = EgoProgressAlongExpertRouteStatistics('ego_progress_along_expert_route_statistics', 'Dynamics', score_progress_threshold=0.1)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    ego_progress_along_expert_route_metric.compute(history, mock_abstract_scenario)[0]
    metric = EgoIsMakingProgressStatistics('ego_is_making_progress_statistics', 'Plannning', ego_progress_along_expert_route_metric, min_progress_threshold=0.2)
    metric_statistic_test(scene=scene, metric=metric)

@nuplan_test(path='json/planner_expert_final_l2_error_within_bound/high_final_l2_error.json')
def test_planner_expert_final_l2_error(scene: Dict[str, Any]) -> None:
    """
    Tests planner_expert_final_l2_error is expected value.
    :param scene: the json scene.
    """
    planner_expert_average_l2_error_within_bound_metric = PlannerExpertAverageL2ErrorStatistics('planner_expert_average_l2_error', 'Planning', comparison_horizon=[3, 5, 8], comparison_frequency=1, max_average_l2_error_threshold=8)
    history, mock_abstract_scenario = build_mock_history_scenario_test(scene)
    planner_expert_average_l2_error_within_bound_metric.compute(history, mock_abstract_scenario)
    metric = PlannerExpertFinalL2ErrorStatistics('planner_expert_final_l2_error_within_bound', 'Planning', planner_expert_average_l2_error_within_bound_metric, max_final_l2_error_threshold=8)
    metric_statistic_test(scene, metric, history, mock_abstract_scenario)

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

@nuplan_test(path='json/ego_stop_at_stop_line/ego_stop_at_stop_line.json')
def test_stop_polygons_in_lanes(scene: Dict[str, Any]) -> None:
    """
    Check if verification of stop polygons in lanes works as expected
    :param scene: the json scene.
    """
    mock_abstract_scenario = MockAbstractScenario()
    history = setup_history(scene, scenario=mock_abstract_scenario)
    ego_stop_at_stop_line_metric = EgoStopAtStopLineStatistics(name='ego_stop_at_stop_line', category='scenario_dependent', distance_threshold=5.0, velocity_threshold=0.1, max_violation_threshold=1)
    map_api: AbstractMap = history.map_api
    valid_stop_polygons = []
    for data in history.data:
        ego_corners = data.ego_state.car_footprint.oriented_box.geometry.exterior.coords
        ego_pose_front: LineString = LineString([ego_corners[0], ego_corners[3]])
        stop_polygon_info = ego_stop_at_stop_line_metric.get_nearest_stop_line(map_api=map_api, ego_pose_front=ego_pose_front)
        if stop_polygon_info is not None:
            valid_stop_polygons.append(stop_polygon_info)
    assert len(history.data) == 6
    assert len(valid_stop_polygons) == 6

@nuplan_test(path='json/ego_stop_at_stop_line/ego_stop_at_stop_line.json')
def test_check_leading_agent(scene: Dict[str, Any]) -> None:
    """
    Check if check_leading_agent work as expected
    :param scene: the json scene.
    """
    mock_abstract_scenario = MockAbstractScenario()
    history = setup_history(scene, scenario=mock_abstract_scenario)
    ego_stop_at_stop_line_metric = EgoStopAtStopLineStatistics(name='ego_stop_at_stop_line', category='scenario_dependent', distance_threshold=5.0, velocity_threshold=0.1, max_violation_threshold=1)
    map_api: AbstractMap = history.map_api
    remove_agents = [False, False, False, True, True, False]
    expected_results = [True, True, True, False, False, False]
    results = []
    for data, remove_agent in zip(history.data, remove_agents):
        detections = data.observation
        if remove_agent:
            detections.boxes = []
        has_leading_agent = ego_stop_at_stop_line_metric.check_for_leading_agents(detections=detections, ego_state=data.ego_state, map_api=map_api)
        results.append(has_leading_agent)
    assert expected_results == results

@nuplan_test(path='json/ego_stop_at_stop_line/ego_stop_at_stop_line.json')
def test_egos_stop_at_stop_line(scene: Dict[str, Any]) -> None:
    """
    Check if egos stop at stop line as expected
    :param scene: the json scene.
    """
    scene['world']['vehicles'] = []
    mock_abstract_scenario = MockAbstractScenario()
    history = setup_history(scene, scenario=mock_abstract_scenario)
    ego_stop_at_stop_line_metric = EgoStopAtStopLineStatistics(name='ego_stop_at_stop_line', category='scenario_dependent', distance_threshold=5.0, velocity_threshold=0.1, max_violation_threshold=1)
    results = ego_stop_at_stop_line_metric.compute(history=history, scenario=mock_abstract_scenario)
    assert len(results) == 1
    result = results[0]
    metric_statistics = result.statistics
    time_series: Optional[TimeSeries] = result.time_series
    assert metric_statistics[0].value == 1
    assert metric_statistics[1].value == 1
    assert metric_statistics[2].value == 0.06016734670118855
    assert metric_statistics[3].value == 0.05
    expected_velocity = [0.5, 0.05]
    assert time_series.values if time_series is not None else [] == expected_velocity

def build_metrics_engines(cfg: DictConfig, scenarios: List[AbstractScenario]) -> Dict[str, MetricsEngine]:
    """
    Build a metric engine for each different scenario type.
    :param cfg: Config.
    :param scenarios: list of scenarios for which metrics should be build.
    :return Dict of scenario types to metric engines.
    """
    main_save_path = pathlib.Path(cfg.output_dir) / cfg.metric_dir
    selected_metrics = cfg.selected_simulation_metrics
    if isinstance(selected_metrics, str):
        selected_metrics = [selected_metrics]
    simulation_metrics = cfg.simulation_metric
    low_level_metrics: DictConfig = simulation_metrics.get('low_level', {})
    high_level_metrics: DictConfig = simulation_metrics.get('high_level', {})
    metric_engines = {}
    for scenario in scenarios:
        if scenario.scenario_type in metric_engines:
            continue
        metric_engine = MetricsEngine(main_save_path=main_save_path)
        scenario_type = scenario.scenario_type
        scenario_metrics: DictConfig = simulation_metrics.get(scenario_type, {})
        metrics_in_scope = low_level_metrics.copy()
        metrics_in_scope.update(scenario_metrics)
        high_level_metric_in_scope = high_level_metrics.copy()
        if selected_metrics is not None:
            metrics_in_scope = {metric_name: metrics_in_scope[metric_name] for metric_name in selected_metrics if metric_name in metrics_in_scope}
            high_level_metric_in_scope = {metric_name: high_level_metrics[metric_name] for metric_name in selected_metrics if metric_name in high_level_metric_in_scope}
        base_metrics = {metric_name: instantiate(metric_config) for metric_name, metric_config in metrics_in_scope.items()}
        for metric in base_metrics.values():
            metric_engine.add_metric(metric)
        for metric_name, metric in high_level_metric_in_scope.items():
            high_level_metric = build_high_level_metric(cfg=metric, base_metrics=base_metrics)
            metric_engine.add_metric(high_level_metric)
            base_metrics[metric_name] = high_level_metric
        metric_engines[scenario_type] = metric_engine
    return metric_engines

class AbstractScenario(abc.ABC):
    """
    Interface for a generic scenarios from any database.
    """

    @property
    @abc.abstractmethod
    def token(self) -> str:
        """
        Unique identifier of a scenario
        :return: str representing unique token.
        """
        pass

    @property
    @abc.abstractmethod
    def log_name(self) -> str:
        """
        Log name for from which this scenario was created
        :return: str representing log name.
        """
        pass

    @property
    @abc.abstractmethod
    def scenario_name(self) -> str:
        """
        Name of this scenario, e.g. extraction_xxxx
        :return: str representing name of this scenario.
        """
        pass

    @property
    @abc.abstractmethod
    def ego_vehicle_parameters(self) -> VehicleParameters:
        """
        Query the vehicle parameters of ego
        :return: VehicleParameters struct.
        """
        pass

    @property
    @abc.abstractmethod
    def scenario_type(self) -> str:
        """
        :return: type of scenario e.g. [lane_change, lane_follow, ...].
        """
        pass

    @property
    @abc.abstractmethod
    def map_api(self) -> AbstractMap:
        """
        Return the Map API for this scenario
        :return: AbstractMap.
        """
        pass

    @property
    @abc.abstractmethod
    def database_interval(self) -> float:
        """
        Database interval in seconds
        :return: [s] database interval.
        """
        pass

    @abc.abstractmethod
    def get_number_of_iterations(self) -> int:
        """
        Get how many frames does this scenario contain
        :return: [int] representing number of scenarios.
        """
        pass

    @abc.abstractmethod
    def get_time_point(self, iteration: int) -> TimePoint:
        """
        Get time point of the iteration
        :param iteration: iteration in scenario 0 <= iteration < number_of_iterations
        :return: global time point.
        """
        pass

    @property
    def start_time(self) -> TimePoint:
        """
        Get the start time of a scenario
        :return: starting time.
        """
        return self.get_time_point(0)

    @property
    def end_time(self) -> TimePoint:
        """
        Get end time of the scenario
        :return: end time point.
        """
        return self.get_time_point(self.get_number_of_iterations() - 1)

    @property
    def duration_s(self) -> TimeDuration:
        """
        Get the duration of the scenario in seconds
        :return: the difference in seconds between the scenario's final and first timepoints.
        """
        return TimeDuration.from_s(self.end_time.time_s - self.start_time.time_s)

    @abc.abstractmethod
    def get_lidar_to_ego_transform(self) -> Transform:
        """
        Return the transformation matrix between lidar and ego
        :return: [4x4] rotation and translation matrix.
        """
        pass

    @abc.abstractmethod
    def get_mission_goal(self) -> Optional[StateSE2]:
        """
        Goal far into future (in generally more than 100m far beyond scenario length).
        :return: StateSE2 for the final state.
        """
        pass

    @abc.abstractmethod
    def get_route_roadblock_ids(self) -> List[str]:
        """
        Get list of roadblock ids comprising goal route.
        :return: List of roadblock id strings.
        """
        pass

    @abc.abstractmethod
    def get_expert_goal_state(self) -> StateSE2:
        """
        Get the final state which the expert driver achieved at the end of the scenario
        :return: StateSE2 for the final state.
        """
        pass

    @abc.abstractmethod
    def get_tracked_objects_at_iteration(self, iteration: int, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """
        Return tracked objects from iteration
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: DetectionsTracks.
        """
        pass

    @abc.abstractmethod
    def get_tracked_objects_within_time_window_at_iteration(self, iteration: int, past_time_horizon: float, future_time_horizon: float, filter_track_tokens: Optional[Set[str]]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> DetectionsTracks:
        """
        Gets all tracked objects present within a time window that stretches from past_time_horizon before the iteration to future_time_horizon afterwards.
        Also optionally filters the included results on the provided track_tokens.
        Results will be sorted by object type, then by timestamp, then by track token.
        :param iteration: The iteration of the scenario to query.
        :param past_time_horizon [s]: The amount of time to look into the past from the iteration timestamp.
        :param future_time_horizon [s]: The amount of time to look into the future from the iteration timestamp.
        :param filter_track_tokens: If provided, then the results will be filtered to only contain objects with
            track_tokens included in the provided set. If None, then all results are returned.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: The retrieved detection tracks.
        """
        pass

    @property
    def initial_tracked_objects(self) -> DetectionsTracks:
        """
        Get initial tracked objects
        :return: DetectionsTracks.
        """
        return self.get_tracked_objects_at_iteration(0)

    @abc.abstractmethod
    def get_sensors_at_iteration(self, iteration: int, channels: Optional[List[SensorChannel]]=None) -> Sensors:
        """
        Return sensor from iteration
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :param channels: The sensor channels to return.
        :return: Sensors.
        """
        pass

    @property
    def initial_sensors(self) -> Sensors:
        """
        Return the initial sensors (e.g. pointcloud)
        :return: Sensors.
        """
        return self.get_sensors_at_iteration(0)

    @abc.abstractmethod
    def get_ego_state_at_iteration(self, iteration: int) -> EgoState:
        """
        Return ego (expert) state in a dataset
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :return: EgoState of ego.
        """
        pass

    @property
    def initial_ego_state(self) -> EgoState:
        """
        Return the initial ego state
        :return: EgoState of ego.
        """
        return self.get_ego_state_at_iteration(0)

    @abc.abstractmethod
    def get_traffic_light_status_at_iteration(self, iteration: int) -> Generator[TrafficLightStatusData, None, None]:
        """
        Get traffic light status at an iteration.
        :param iteration: within scenario 0 <= iteration < number_of_iterations
        :return traffic light status at the iteration.
        """
        pass

    @abc.abstractmethod
    def get_past_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets past traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the past.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the past.
        """
        pass

    @abc.abstractmethod
    def get_future_traffic_light_status_history(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TrafficLightStatuses, None, None]:
        """
        Gets future traffic light status.

        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param time_horizon [s]: the desired horizon to the future.
        :param num_samples: number of entries in the future, if None it will be deduced from the DB.
        :return: Generator object for traffic light history to the future.
        """
        pass

    def get_expert_ego_trajectory(self) -> Generator[EgoState, None, None]:
        """
        Return trajectory that was taken by the expert-driver
        :return: sequence of agent states taken by ego.
        """
        return (self.get_ego_state_at_iteration(index) for index in range(self.get_number_of_iterations()))

    def get_ego_trajectory_slice(self, start_idx: int, end_idx: int) -> Generator[EgoState, None, None]:
        """
        Return trajectory that was taken by the expert-driver between start_idx and end_idx
        :param start_idx: starting index for ego's trajectory
        :param end_idx: ending index for ego's trajectory
        :return: sequence of agent states taken by ego
        timestamp (best matching to the database).
        """
        return (self.get_ego_state_at_iteration(index) for index in range(start_idx, end_idx))

    @abc.abstractmethod
    def get_future_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """
        Find timesteps in future
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the future timestamps with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_timestamps(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[TimePoint, None, None]:
        """
        Find timesteps in past
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the past
        :param time_horizon [s]: the desired horizon to the past
        :return: the future timestamps with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_ego_future_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """
        Find ego future trajectory
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the future ego trajectory with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_ego_past_trajectory(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None) -> Generator[EgoState, None, None]:
        """
        Find ego past trajectory
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param num_samples: number of entries in the future
        :param time_horizon [s]: the desired horizon to the future
        :return: the past ego trajectory with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_sensors(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, channels: Optional[List[SensorChannel]]=None) -> Generator[Sensors, None, None]:
        """
        Find past sensors
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations
        :param time_horizon: [s] the desired horizon to the future
        :param num_samples: number of entries in the future
        :param channels: The sensor channels to return.
        :return: the past sensors with the best matching entries to the desired time_horizon/num_samples
        timestamp (best matching to the database)
        """
        pass

    @abc.abstractmethod
    def get_past_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """
        Find past detections.
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param num_samples: number of entries in the future.
        :param time_horizon [s]: the desired horizon to the future.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: the past detections.
        """
        pass

    @abc.abstractmethod
    def get_future_tracked_objects(self, iteration: int, time_horizon: float, num_samples: Optional[int]=None, future_trajectory_sampling: Optional[TrajectorySampling]=None) -> Generator[DetectionsTracks, None, None]:
        """
        Find future detections.
        :param iteration: iteration within scenario 0 <= scenario_iteration < get_number_of_iterations.
        :param num_samples: number of entries in the future.
        :param time_horizon [s]: the desired horizon to the future.
        :param future_trajectory_sampling: sampling parameters of agent future ground truth predictions if desired.
        :return: the past detections.
        """
        pass

@property
def duration_s(self) -> TimeDuration:
    """
        Get the duration of the scenario in seconds
        :return: the difference in seconds between the scenario's final and first timepoints.
        """
    return TimeDuration.from_s(self.end_time.time_s - self.start_time.time_s)

@dataclass(frozen=True)
class ScenarioFilter:
    """
    Collection of filters used to construct scenarios from a database for training/simulation.
    """
    scenario_types: Optional[List[str]]
    scenario_tokens: Optional[List[Sequence[str]]]
    log_names: Optional[List[str]]
    map_names: Optional[List[str]]
    num_scenarios_per_type: Optional[int]
    limit_total_scenarios: Optional[Union[int, float]]
    timestamp_threshold_s: Optional[float]
    ego_displacement_minimum_m: Optional[float]
    expand_scenarios: bool
    remove_invalid_goals: bool
    shuffle: bool
    ego_start_speed_threshold: Optional[float] = None
    ego_stop_speed_threshold: Optional[float] = None
    speed_noise_tolerance: Optional[float] = None
    token_set_path: Optional[Path] = None
    fraction_in_token_set_threshold: Optional[float] = None
    ego_route_radius: Optional[float] = None

    def __post_init__(self) -> None:
        """Sanitize class attributes."""
        if self.num_scenarios_per_type is not None:
            assert 0 < self.num_scenarios_per_type, 'num_scenarios_per_type should be a positive integer'
        if isinstance(self.limit_total_scenarios, float):
            assert 0.0 < self.limit_total_scenarios <= 1.0, 'limit_total_scenarios should be in (0, 1] when float'
        elif isinstance(self.limit_total_scenarios, int):
            assert 0 < self.limit_total_scenarios, 'limit_total_scenarios should be positive when integer'

def __post_init__(self) -> None:
    """Sanitize class attributes."""
    if self.num_scenarios_per_type is not None:
        assert 0 < self.num_scenarios_per_type, 'num_scenarios_per_type should be a positive integer'
    if isinstance(self.limit_total_scenarios, float):
        assert 0.0 < self.limit_total_scenarios <= 1.0, 'limit_total_scenarios should be in (0, 1] when float'
    elif isinstance(self.limit_total_scenarios, int):
        assert 0 < self.limit_total_scenarios, 'limit_total_scenarios should be positive when integer'

def absolute_path_to_log_name(absolute_path: str) -> str:
    """
    Gets the log name from the absolute path to a log file.
    E.g.
        input: data/sets/nuplan/nuplan-v1.1/splits/mini/2021.10.11.02.57.41_veh-50_01522_02088.db
        output: 2021.10.11.02.57.41_veh-50_01522_02088

        input: /tmp/abcdef
        output: abcdef
    :param absolute_path: The absolute path to a log file.
    :return: The log name.
    """
    filename = os.path.basename(absolute_path)
    if filename.endswith('.db'):
        filename = os.path.splitext(filename)[0]
    return filename

def _filter_scenarios_by_timestamp(scenario_list: List[NuPlanScenario], timestamp_threshold_s: float) -> List[NuPlanScenario]:
    """
    Filters the list of scenarios by timestamp.
    :param scenario_list: List of scenarios to filtered.
    :param timestamp_threshold_s: Threshold for filtering out scenarios clustered together in time.
    :return: Filtered list of scenarios.
    """
    if len(scenario_list) == 0:
        return scenario_list

    def _extract_initial_lidar_timestamp(scenario: NuPlanScenario) -> int:
        return cast(int, scenario._initial_lidar_timestamp)
    scenario_list.sort(key=_extract_initial_lidar_timestamp)
    filtered_scenarios = []
    min_next_timestamp = scenario_list[0]._initial_lidar_timestamp * 1e-06
    for scenario in scenario_list:
        if scenario._initial_lidar_timestamp * 1e-06 >= min_next_timestamp:
            filtered_scenarios.append(scenario)
            min_next_timestamp = scenario._initial_lidar_timestamp * 1e-06 + timestamp_threshold_s
    return filtered_scenarios

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

def test_construction(self) -> None:
    """Tests that the variables are initialized correctly."""
    self.assertTrue(isinstance(self.validator, BaseSubmissionValidator))

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

def test_construction(self) -> None:
    """Tests that the variables are initialized correctly."""
    self.assertTrue(isinstance(self.validator, BaseSubmissionValidator))

