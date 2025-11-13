# Cluster 26

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

class BlobStoreKeyNotFound(ValueError):
    """Error raised when blob store key is not found."""

    def __init__(self, *args: Any) -> None:
        """
        :param args: Arguments.
        """
        super().__init__(*args)

def __init__(self, *args: Any) -> None:
    """
        :param args: Arguments.
        """
    super().__init__(*args)

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

class GPKGMapsDBException(Exception):
    """GPKGMapsDB Exception Class."""

    def __init__(self, message: str) -> None:
        """
        Constructor.
        :param message: Exception message.
        """
        super().__init__(message)

def __init__(self, message: str) -> None:
    """
        Constructor.
        :param message: Exception message.
        """
    super().__init__(message)

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        output = unwrap(x, dim=-1)
        return output

def __init__(self) -> None:
    super().__init__()

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

def setUp(self) -> None:
    """Inherited, see superclass"""
    HelperTestingSetup.__init__(self)

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

def setUp(self) -> None:
    """Inherited, see superclass"""
    HelperTestingSetup.__init__(self)

class mock_async_s3(ContextDecorator):
    """
    Class for mocking S3 that can be used as both a context manager, and function decorator.
    Only works in/on a synchronous function.
    """

    def __init__(self) -> None:
        """
        Context manager setup.
        """
        super().__init__()
        self.patch_special_case_error = patch('aiobotocore.handlers._looks_like_special_case_error', _looks_like_special_case_error_patch)
        self.patch_convert_to_response = patch('aiobotocore.endpoint.convert_to_response_dict', convert_to_response_dict_patch)
        self.s3_mocker = mock_s3()

    def __enter__(self) -> Type['mock_async_s3']:
        """
        Context manager enter.
        """
        self.patch_special_case_error.start()
        self.patch_convert_to_response.start()
        self.s3_mocker.start()
        return cast(Type['mock_async_s3'], self)

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_value: Optional[BaseException], exc_traceback: Optional[TracebackType]) -> None:
        """
        Context manager exit.
        Note that we don't have to handle the incoming exception, by returning None, it will be re-raised.
        :param exc_type: Type of any exception that occured.
        :param exc_value: Exception that occured, or None.
        :param traceback: Traceback if an exception occured.
        :return: Always None, so exceptions are never swallowed.
        """
        self.patch_special_case_error.stop()
        self.patch_convert_to_response.stop()
        self.s3_mocker.stop()
        return None

def __init__(self) -> None:
    """
        Context manager setup.
        """
    super().__init__()
    self.patch_special_case_error = patch('aiobotocore.handlers._looks_like_special_case_error', _looks_like_special_case_error_patch)
    self.patch_convert_to_response = patch('aiobotocore.endpoint.convert_to_response_dict', convert_to_response_dict_patch)
    self.s3_mocker = mock_s3()

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

def is_adjacent_to(self, other: Lane) -> bool:
    """
        :param other: Lane to check if it is adjacent to self.
        :return: True if self and other are in the same roadblock and adjacent.
        """
    return self.is_same_roadblock(other) and (self.right_boundary.id == other.left_boundary.id or self.left_boundary.id == other.right_boundary.id)

class Lane(LaneGraphEdgeMapObject):
    """
    Class representing lanes.
    """

    def __init__(self, lane_id: str):
        """
        Constructor of the base lane type.
        :param lane_id: unique identifier of the lane.
        """
        super().__init__(lane_id)

    def has_traffic_lights(self) -> bool:
        """Inherited from superclass."""
        return False

    @property
    def stop_lines(self) -> List[StopLine]:
        """Inherited from superclass."""
        return []

    @abc.abstractmethod
    def index(self) -> int:
        """
        Gets the 1-index position of the lane within the parent roadblock.
        :return: The index of lane.
        """
        pass

def __init__(self, lane_id: str):
    """
        Constructor of the base lane type.
        :param lane_id: unique identifier of the lane.
        """
    super().__init__(lane_id)

class LaneConnector(LaneGraphEdgeMapObject):
    """
    Class representing lane connectors.
    """

    def __init__(self, lane_connector_id: str):
        """
        Constructor of the base lane connector type.
        :param lane_connector_id: unique identifier of the lane.
        """
        super().__init__(lane_connector_id)

    @property
    def adjacent_edges(self) -> Tuple[Optional[LaneGraphEdgeMapObject], Optional[LaneGraphEdgeMapObject]]:
        """Inherited from superclass."""
        return (None, None)

    @property
    @abc.abstractmethod
    def turn_type(self) -> LaneConnectorType:
        """
        Gets the turn type of the lane connector
        :return: LaneConnectorType of lane connector if lane connector has a type else None
        """
        pass

def __init__(self, lane_connector_id: str):
    """
        Constructor of the base lane connector type.
        :param lane_connector_id: unique identifier of the lane.
        """
    super().__init__(lane_connector_id)

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

def __init__(self, path_id: str):
    """
        Constructor of the PolylineMapObject type.
        :param path_id: unique identifier of the polyline.
        """
    super().__init__(path_id)

class StopLine(PolygonMapObject):
    """
    Class representing stop lines.
    """

    def __init__(self, stop_line_id: str, stop_line_type: StopLineType) -> None:
        """
        Constructor of the base stop line type.
        :param stop_line_id: unique identifier of the stop line.
        :param stop_line_type: stop line sub type. E.g. PED_CROSSING, STOP_SIGN, TRAFFIC_LIGHT, TURN_STOP.
        """
        super().__init__(stop_line_id)
        self.stop_line_type = stop_line_type

    @property
    @abc.abstractmethod
    def intersection_from(self) -> Intersection:
        """
        Gets the related intersection.
        :return: Intersection related to StopLine.
        """
        pass

    @property
    @abc.abstractmethod
    def layer_type(self) -> StopLineType:
        """
        Gets StopLineType for Stopline subtype.
        :return: StopLineType subtype.
        """
        pass

    @property
    @abc.abstractmethod
    def parent(self) -> RoadBlockGraphEdgeMapObject:
        """
        Getter function for obtaining the parent RoadBlockGraphEdgeMapObject containing the StopLine.
        :return: RoadblockBlockGraphEdgeMapObject containing the StopLine.
        """
        pass

def __init__(self, stop_line_id: str, stop_line_type: StopLineType) -> None:
    """
        Constructor of the base stop line type.
        :param stop_line_id: unique identifier of the stop line.
        :param stop_line_type: stop line sub type. E.g. PED_CROSSING, STOP_SIGN, TRAFFIC_LIGHT, TURN_STOP.
        """
    super().__init__(stop_line_id)
    self.stop_line_type = stop_line_type

class Intersection(PolygonMapObject):
    """
    Class representing intersections.
    """

    def __init__(self, intersection_id: str, intersection_type: IntersectionType) -> None:
        """
        Constructor of the base intersection type.
        :param intersection_id: unique identifier of the intersection.
        :param intersection_type: stop line sub type. E.g. DEFAULT, TRAFFIC_LIGHT, STOP_SIGN.
        """
        super().__init__(intersection_id)
        self.intersection_type = intersection_type

    @property
    @abc.abstractmethod
    def interior_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
        """
        Returns RoadBlockGraphEdgeMapObjects contained within the intersection.
        :return: a list of RoadBlockGraphEdgeMapObject.
        """
        pass

    @property
    @abc.abstractmethod
    def incoming_edges(self) -> List[Lane]:
        """
        Returns incoming Lanes connecting to this intersection.
        :return: a list of Lane.
        """
        pass

    @property
    @abc.abstractmethod
    def is_signaled(self) -> bool:
        """
        Returns if intersection is signaled.
        :return: True if intersection is a traffic light or one of the interior edges has a traffic light is signaled else False.
        """
        pass

def __init__(self, intersection_id: str, intersection_type: IntersectionType) -> None:
    """
        Constructor of the base intersection type.
        :param intersection_id: unique identifier of the intersection.
        :param intersection_type: stop line sub type. E.g. DEFAULT, TRAFFIC_LIGHT, STOP_SIGN.
        """
    super().__init__(intersection_id)
    self.intersection_type = intersection_type

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

def _get_roadblock(self) -> pd.Series:
    """
        Gets the series from the roadblock dataframe containing roadblock's id.
        :return: the respective series from the roadblocks dataframe.
        """
    if self._roadblock is None:
        self._roadblock = get_row_with_value(self._roadblocks_df, 'fid', self.id)
    return self._roadblock

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

class NuPlanIntersection(Intersection):
    """
    NuPlanMap implementation of Intersection.
    """

    def __init__(self, intersection_id: str, intersections_df: VectorLayer) -> None:
        """
        Constructor of NuPlanIntersection.
        :param intersection_id: unique identifier of the intersection.
        :param intersections_df: the geopandas GeoDataframe that contains all intersections in the map.
        """
        self._intersections_df = intersections_df
        self._intersection = get_row_with_value(self._intersections_df, 'fid', intersection_id)
        super().__init__(intersection_id, IntersectionType.DEFAULT)

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._intersection.geometry

    @cached_property
    def interior_edges(self) -> List[LaneGraphEdgeMapObject]:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def incoming_edges(self) -> List[Lane]:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def center(self) -> Tuple[float, float]:
        """
        Returns center of intersection
        :return: Center of intersection
        """
        raise NotImplementedError

    @cached_property
    def is_signaled(self) -> bool:
        """
        Returns if intersection is signaled
        :return: True if intersection is signaled else False
        """
        raise NotImplementedError

def __init__(self, intersection_id: str, intersections_df: VectorLayer) -> None:
    """
        Constructor of NuPlanIntersection.
        :param intersection_id: unique identifier of the intersection.
        :param intersections_df: the geopandas GeoDataframe that contains all intersections in the map.
        """
    self._intersections_df = intersections_df
    self._intersection = get_row_with_value(self._intersections_df, 'fid', intersection_id)
    super().__init__(intersection_id, IntersectionType.DEFAULT)

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

class NuPlanPolygonMapObject(PolygonMapObject):
    """
    NuPlanMap implementation of Polygon Map Object.
    """

    def __init__(self, generic_polygon_area_id: str, generic_polygon_area: VectorLayer):
        """
        Constructor of generic polygon map layer.
        This includes:
            - CROSSWALK
            - WALKWAYS
            - CARPARK_AREA
            - PUDO
        :param generic_polygon_area_id: Generic polygon area id.
        :param generic_polygon_area: Generic polygon area.
        """
        super().__init__(generic_polygon_area_id)
        self._generic_polygon_area = generic_polygon_area
        self._area = None

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._get_area().geometry

    def _get_area(self) -> pd.Series:
        """
        Gets the series from the polygon dataframe containing polygon's id.
        :return: The respective series from the polygon dataframe.
        """
        if self._area is None:
            self._area = get_row_with_value(self._generic_polygon_area, 'fid', self.id)
        return self._area

def __init__(self, generic_polygon_area_id: str, generic_polygon_area: VectorLayer):
    """
        Constructor of generic polygon map layer.
        This includes:
            - CROSSWALK
            - WALKWAYS
            - CARPARK_AREA
            - PUDO
        :param generic_polygon_area_id: Generic polygon area id.
        :param generic_polygon_area: Generic polygon area.
        """
    super().__init__(generic_polygon_area_id)
    self._generic_polygon_area = generic_polygon_area
    self._area = None

def _get_area(self) -> pd.Series:
    """
        Gets the series from the polygon dataframe containing polygon's id.
        :return: The respective series from the polygon dataframe.
        """
    if self._area is None:
        self._area = get_row_with_value(self._generic_polygon_area, 'fid', self.id)
    return self._area

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
def polygon(self) -> Polygon:
    """Inherited from superclass. Note, the polygon is inferred from the baseline."""
    lane_connector_polygon_row = get_row_with_value(self._lane_connector_polygon_df, 'lane_connector_fid', self.id)
    return lane_connector_polygon_row.geometry

def _get_lane_connector(self) -> pd.Series:
    """
        Gets the series from the lane dataframe containing lane's id.
        :return: the respective series from the lanes dataframe.
        """
    if self._lane_connector is None:
        self._lane_connector = get_row_with_value(self._lane_connectors_df, 'fid', self.id)
    return self._lane_connector

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
def _roadblock_connector(self) -> pd.Series:
    """
        Gets the series from the roadblock connector dataframe containing roadblock connector's id.
        :return: the respective series from the roadblock connectors dataframe.
        """
    return get_row_with_value(self._roadblock_connectors_df, 'fid', self.id)

class NuPlanStopLine(StopLine):
    """
    NuPlanMap implementation of StopLine.
    """

    def __init__(self, stop_line_id: str, stop_lines_df: VectorLayer) -> None:
        """
        Constructor of NuPlanStopLine.
        :param stop_line_id: unique identifier of the stop line.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        """
        self._stop_lines_df = stop_lines_df
        self._stop_line = get_row_with_value(self._stop_lines_df, 'fid', stop_line_id)
        super().__init__(stop_line_id, self._stop_line['stop_polygon_type_fid'])

    @cached_property
    def polygon(self) -> Polygon:
        """Inherited from superclass."""
        return self._stop_line.geometry

    @cached_property
    def intersection_from(self) -> Intersection:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def layer_type(self) -> StopLineType:
        """Inherited from superclass"""
        raise NotImplementedError

    @cached_property
    def parent(self) -> RoadBlockGraphEdgeMapObject:
        """Inherited from superclass"""
        raise NotImplementedError

def __init__(self, stop_line_id: str, stop_lines_df: VectorLayer) -> None:
    """
        Constructor of NuPlanStopLine.
        :param stop_line_id: unique identifier of the stop line.
        :param stop_lines_df: the geopandas GeoDataframe that contains all stop lines in the map.
        """
    self._stop_lines_df = stop_lines_df
    self._stop_line = get_row_with_value(self._stop_lines_df, 'fid', stop_line_id)
    super().__init__(stop_line_id, self._stop_line['stop_polygon_type_fid'])

def is_same_roadblock(first_lane: Lane, second_lane: Lane, inverse: bool) -> None:
    if not inverse:
        assert first_lane.is_same_roadblock(second_lane)
    else:
        assert not first_lane.is_same_roadblock(second_lane)

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

def __init__(self, center: StateSE2, vehicle_parameters: VehicleParameters):
    """
        :param center: The pose of ego in the specified frame
        :param vehicle_parameters: The parameters of ego
        """
    super().__init__(center=center, width=vehicle_parameters.width, length=vehicle_parameters.length, height=vehicle_parameters.height)
    self._vehicle_parameters = vehicle_parameters

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

def __init__(self, current_state: EgoState, past_trajectory: Optional[PredictedTrajectory]=None, predictions: Optional[List[PredictedTrajectory]]=None):
    """
        Initialize temporal state
        :param current_state: current state of ego
        :param past_trajectory: past trajectory, where last waypoint represents the same position as current state
        :param predictions: multimodal predictions, or future trajectory
        """
    super().__init__(initial_time_stamp=current_state.time_point, predictions=predictions, past_trajectory=past_trajectory)
    self._ego_current_state = current_state

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

class StaticObject(SceneObject):
    """Represents static objects in the scene."""

    def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, metadata: SceneObjectMetadata):
        """
        :param tracked_object_type: Classification type of the object.
        :param oriented_box: OrientedBox representing the StaticObject geometrically.
        :param metadata: Metadata of a static object.
        """
        super().__init__(tracked_object_type, oriented_box, metadata)
        self.predictions = None
        self.past_trajectory = None
        self.velocity = StateVector2D(0.0, 0.0)

def __init__(self, tracked_object_type: TrackedObjectType, oriented_box: OrientedBox, metadata: SceneObjectMetadata):
    """
        :param tracked_object_type: Classification type of the object.
        :param oriented_box: OrientedBox representing the StaticObject geometrically.
        :param metadata: Metadata of a static object.
        """
    super().__init__(tracked_object_type, oriented_box, metadata)
    self.predictions = None
    self.past_trajectory = None
    self.velocity = StateVector2D(0.0, 0.0)

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, coords: torch.Tensor, avails: torch.Tensor, anchor_state: torch.Tensor) -> torch.Tensor:
        result = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
        return result

def __init__(self) -> None:
    super().__init__()

class SingleMachineParallelExecutor(WorkerPool):
    """
    This worker distributes all tasks across multiple threads on this machine.
    """

    def __init__(self, use_process_pool: bool=False, max_workers: Optional[int]=None):
        """
        Create worker with limited threads.
        :param use_process_pool: if true, ProcessPoolExecutor will be used as executor, otherwise ThreadPoolExecutor.
        :param max_workers: if available, use this number as used number of threads.
        """
        number_of_cpus_per_node = max_workers if max_workers else WorkerResources.current_node_cpu_count()
        super().__init__(WorkerResources(number_of_nodes=1, number_of_cpus_per_node=number_of_cpus_per_node, number_of_gpus_per_node=0))
        self._executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) if use_process_pool else concurrent.futures.ThreadPoolExecutor(max_workers=number_of_cpus_per_node)

    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """Inherited, see superclass."""
        return list(tqdm(self._executor.map(task.fn, *item_lists), leave=False, total=get_max_size_of_arguments(*item_lists), desc='SingleMachineParallelExecutor', disable=not verbose))

    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """Inherited, see superclass."""
        return self._executor.submit(task.fn, *args, **kwargs)

def __init__(self, use_process_pool: bool=False, max_workers: Optional[int]=None):
    """
        Create worker with limited threads.
        :param use_process_pool: if true, ProcessPoolExecutor will be used as executor, otherwise ThreadPoolExecutor.
        :param max_workers: if available, use this number as used number of threads.
        """
    number_of_cpus_per_node = max_workers if max_workers else WorkerResources.current_node_cpu_count()
    super().__init__(WorkerResources(number_of_nodes=1, number_of_cpus_per_node=number_of_cpus_per_node, number_of_gpus_per_node=0))
    self._executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) if use_process_pool else concurrent.futures.ThreadPoolExecutor(max_workers=number_of_cpus_per_node)

class RayDistributed(WorkerPool):
    """
    This worker uses ray to distribute work across all available threads.
    """

    def __init__(self, master_node_ip: Optional[str]=None, threads_per_node: Optional[int]=None, debug_mode: bool=False, log_to_driver: bool=True, output_dir: Optional[Union[str, Path]]=None, logs_subdir: Optional[str]='logs', use_distributed: bool=False):
        """
        Initialize ray worker.
        :param master_node_ip: if available, ray will connect to remote cluster.
        :param threads_per_node: Number of threads to use per node.
        :param debug_mode: If true, the code will be executed serially. This
            is useful for debugging.
        :param log_to_driver: If true, the output from all of the worker
                processes on all nodes will be directed to the driver.
        :param output_dir: Experiment output directory.
        :param logs_subdir: Subdirectory inside experiment dir to store worker logs.
        :param use_distributed: Boolean flag to explicitly enable/disable distributed computation
        """
        self._master_node_ip = master_node_ip
        self._threads_per_node = threads_per_node
        self._local_mode = debug_mode
        self._log_to_driver = log_to_driver
        self._log_dir: Optional[Path] = Path(output_dir) / (logs_subdir or '') if output_dir is not None else None
        self._use_distributed = use_distributed
        super().__init__(self.initialize())

    def initialize(self) -> WorkerResources:
        """
        Initialize ray.
        :return: created WorkerResources.
        """
        if ray.is_initialized():
            logger.warning('Ray is running, we will shut it down before starting again!')
            ray.shutdown()
        return initialize_ray(master_node_ip=self._master_node_ip, threads_per_node=self._threads_per_node, local_mode=self._local_mode, log_to_driver=self._log_to_driver, use_distributed=self._use_distributed)

    def shutdown(self) -> None:
        """
        Shutdown the worker and clear memory.
        """
        ray.shutdown()

    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """Inherited, see superclass."""
        del verbose
        return ray_map(task, *item_lists, log_dir=self._log_dir)

    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """Inherited, see superclass."""
        remote_fn = ray.remote(task.fn).options(num_gpus=task.num_gpus, num_cpus=task.num_cpus)
        object_ids: ray._raylet.ObjectRef = remote_fn.remote(*args, **kwargs)
        return object_ids.future()

def __init__(self, master_node_ip: Optional[str]=None, threads_per_node: Optional[int]=None, debug_mode: bool=False, log_to_driver: bool=True, output_dir: Optional[Union[str, Path]]=None, logs_subdir: Optional[str]='logs', use_distributed: bool=False):
    """
        Initialize ray worker.
        :param master_node_ip: if available, ray will connect to remote cluster.
        :param threads_per_node: Number of threads to use per node.
        :param debug_mode: If true, the code will be executed serially. This
            is useful for debugging.
        :param log_to_driver: If true, the output from all of the worker
                processes on all nodes will be directed to the driver.
        :param output_dir: Experiment output directory.
        :param logs_subdir: Subdirectory inside experiment dir to store worker logs.
        :param use_distributed: Boolean flag to explicitly enable/disable distributed computation
        """
    self._master_node_ip = master_node_ip
    self._threads_per_node = threads_per_node
    self._local_mode = debug_mode
    self._log_to_driver = log_to_driver
    self._log_dir: Optional[Path] = Path(output_dir) / (logs_subdir or '') if output_dir is not None else None
    self._use_distributed = use_distributed
    super().__init__(self.initialize())

class Sequential(WorkerPool):
    """
    This function does execute all functions sequentially.
    """

    def __init__(self) -> None:
        """
        Initialize simple sequential worker.
        """
        super().__init__(WorkerResources(number_of_nodes=1, number_of_cpus_per_node=1, number_of_gpus_per_node=0))

    def _map(self, task: Task, *item_lists: Iterable[List[Any]], verbose: bool=False) -> List[Any]:
        """Inherited, see superclass."""
        if task.num_cpus not in [None, 1]:
            raise ValueError(f'Expected num_cpus to be 1 or unset for Sequential worker, got {task.num_cpus}')
        output = [task.fn(*args) for args in tqdm(zip(*item_lists), leave=False, total=get_max_size_of_arguments(*item_lists), desc='Sequential', disable=not verbose)]
        return output

    def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
        """Inherited, see superclass."""
        raise NotImplementedError

def __init__(self) -> None:
    """
        Initialize simple sequential worker.
        """
    super().__init__(WorkerResources(number_of_nodes=1, number_of_cpus_per_node=1, number_of_gpus_per_node=0))

class TestWorkerPool(unittest.TestCase):
    """Unittest class for WorkerPool"""

    def setUp(self) -> None:
        """
        Setup worker
        """
        self.worker = RayDistributed(debug_mode=True)

    def test_ray(self) -> None:
        """
        Test ray GPU allocation
        """
        num_calls = 3
        num_gpus = 1
        output = self.worker.map(Task(fn=function_to_load_model, num_gpus=num_gpus), num_calls * [1])
        for gpu_available, num_threads in output:
            self.assertTrue(gpu_available)
            self.assertGreater(num_threads, 0)

def setUp(self) -> None:
    """
        Setup worker
        """
    self.worker = RayDistributed(debug_mode=True)

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

def setUp(self) -> None:
    """Set up basic config."""
    self.lhs_matrix: npt.NDArray[np.float32] = np.array([[1, 2, 4], [2, 3, 4]])
    self.rhs_matrix: npt.NDArray[np.float32] = np.array([[2, 3, 4], [2, 5, 4]]).T
    self.target: npt.NDArray[np.float32] = np.array([[24, 28], [29, 35]])
    self.workers = [Sequential(), RayDistributed(debug_mode=True), SingleMachineParallelExecutor(), SingleMachineParallelExecutor(use_process_pool=True)]

class AbstractPredictor(abc.ABC):
    """
    Interface for a generic agent predictor.
    """
    requires_scenario: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> AbstractPredictor:
        """
        Define attributes needed by all predictors, take care when overriding.
        :param cls: class being constructed.
        :param args: arguments to constructor.
        :param kwargs: keyword arguments to constructor.
        """
        instance: AbstractPredictor = super().__new__(cls)
        instance._compute_predictions_runtimes = []
        return instance

    @abstractmethod
    def name(self) -> str:
        """
        :return string describing name of the predictor.
        """
        pass

    @abc.abstractmethod
    def initialize(self, initialization: PredictorInitialization) -> None:
        """
        Initialize predictor.
        :param initialization: Necessary data to initialize predictor.
        """
        pass

    @abc.abstractmethod
    def observation_type(self) -> Type[Observation]:
        """
        :return Type of observation that is expected in compute_predictions.
        """
        pass

    @abc.abstractmethod
    def compute_predicted_trajectories(self, current_input: PredictorInput) -> DetectionsTracks:
        """
        Computes the agent predictions.
        :param current_input: input to the predictor.
        :return: Detections updated with agents' predicted future trajectories.
        """
        pass

    def compute_predictions(self, current_input: PredictorInput) -> DetectionsTracks:
        """
        Computes the predicted trajectories for input agents and populates updated detections with predictions.
        :param current_input: Predictor input data. Includes observations (tracked objects) for which future
            trajectories will be predicted.
        :return: Detections updated with agents' predicted future trajectories.
        """
        start_time = time.perf_counter()
        try:
            return self.compute_predicted_trajectories(current_input)
        finally:
            self._compute_predictions_runtimes.append(time.perf_counter() - start_time)

    def generate_predictor_report(self, clear_stats: bool=True) -> PredictorReport:
        """
        Generate a report containing runtime stats from the predictor.
        By default, returns a report containing the time-series of compute_predictions runtimes.
        :param clear_stats: whether to clear stored stats after creating report.
        :return: report containing predictor runtime stats.
        """
        report = PredictorReport(compute_predictions_runtimes=self._compute_predictions_runtimes)
        if clear_stats:
            self._compute_predictions_runtimes: List[float] = []
        return report

def __new__(cls, *args: Any, **kwargs: Any) -> AbstractPredictor:
    """
        Define attributes needed by all predictors, take care when overriding.
        :param cls: class being constructed.
        :param args: arguments to constructor.
        :param kwargs: keyword arguments to constructor.
        """
    instance: AbstractPredictor = super().__new__(cls)
    instance._compute_predictions_runtimes = []
    return instance

class AbstractPlanner(abc.ABC):
    """
    Interface for a generic ego vehicle planner.
    """
    requires_scenario: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> AbstractPlanner:
        """
        Define attributes needed by all planners, take care when overriding.
        :param cls: class being constructed.
        :param args: arguments to constructor.
        :param kwargs: keyword arguments to constructor.
        """
        instance: AbstractPlanner = super().__new__(cls)
        instance._compute_trajectory_runtimes = []
        return instance

    @abstractmethod
    def name(self) -> str:
        """
        :return string describing name of this planner.
        """
        pass

    @abc.abstractmethod
    def initialize(self, initialization: PlannerInitialization) -> None:
        """
        Initialize planner
        :param initialization: Initialization class.
        """
        pass

    @abc.abstractmethod
    def observation_type(self) -> Type[Observation]:
        """
        :return Type of observation that is expected in compute_trajectory.
        """
        pass

    @abc.abstractmethod
    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory.
        :param current_input: List of planner inputs for which trajectory needs to be computed.
        :return: Trajectories representing the predicted ego's position in future
        """
        pass

    def compute_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory, where we check that if planner can not consume batched inputs,
            we require that the input list has exactly one element
        :param current_input: List of planner inputs for where for each of them trajectory should be computed
            In this case the list represents batched simulations. In case consume_batched_inputs is False
            the list has only single element
        :return: Trajectories representing the predicted ego's position in future for every input iteration
            In case consume_batched_inputs is False, return only a single trajectory in a list.
        """
        start_time = time.perf_counter()
        try:
            trajectory = self.compute_planner_trajectory(current_input)
        except Exception as e:
            self._compute_trajectory_runtimes.append(time.perf_counter() - start_time)
            raise e
        self._compute_trajectory_runtimes.append(time.perf_counter() - start_time)
        return trajectory

    def generate_planner_report(self, clear_stats: bool=True) -> PlannerReport:
        """
        Generate a report containing runtime stats from the planner.
        By default, returns a report containing the time-series of compute_trajectory runtimes.
        :param clear_stats: whether or not to clear stored stats after creating report.
        :return: report containing planner runtime stats.
        """
        report = PlannerReport(compute_trajectory_runtimes=self._compute_trajectory_runtimes)
        if clear_stats:
            self._compute_trajectory_runtimes: List[float] = []
        return report

def __new__(cls, *args: Any, **kwargs: Any) -> AbstractPlanner:
    """
        Define attributes needed by all planners, take care when overriding.
        :param cls: class being constructed.
        :param args: arguments to constructor.
        :param kwargs: keyword arguments to constructor.
        """
    instance: AbstractPlanner = super().__new__(cls)
    instance._compute_trajectory_runtimes = []
    return instance

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

class MockIDMPlanner(AbstractIDMPlanner):
    """
    Mock IDMPlanner class for testing the AbstractIDMPlanner interface
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
        super(MockIDMPlanner, self).__init__(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max, planned_trajectory_samples, planned_trajectory_sample_interval, occupancy_map_radius)
        self._scenario = MockAbstractScenario()
        self._scenario_buffer = 10

    def initialize(self, initialization: List[PlannerInitialization]) -> None:
        """Inherited, see superclass."""
        self._map_api = initialization[0].map_api
        self._initialize_route_plan(initialization[0].route_roadblock_ids)
        self._ego_path: InterpolatedPath = create_path_from_ego_state(self._scenario.get_ego_future_trajectory(0, self._scenario_buffer, 10))
        self._ego_path_linestring = LineString()

    def compute_planner_trajectory(self, current_input: List[PlannerInput]) -> List[AbstractTrajectory]:
        """Inherited, see superclass."""
        return [InterpolatedTrajectory(self._ego_path.get_sampled_path())]

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
    super(MockIDMPlanner, self).__init__(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max, planned_trajectory_samples, planned_trajectory_sample_interval, occupancy_map_radius)
    self._scenario = MockAbstractScenario()
    self._scenario_buffer = 10

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

def __init__(self, model: TorchModuleWrapper, scenario: AbstractScenario) -> None:
    """
        Initializes the EgoCentricMLAgents class.
        :param model: Model to use for inference.
        :param scenario: scenario
        """
    super().__init__(model, scenario)
    self.prediction_type = 'agents_trajectory'

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

class ScriptableTorchModuleWrapper(TorchModuleWrapper):
    """
    An interface representing a model that can be exported with TorchScript
    """

    def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
        """
        Construct a scriptable model with feature and target builders.
        :param future_trajectory_sampling: Parameters for a predicted trajectory.
        :param feature_builders: The list of builders which will compute features for this model.
        :param target_builders: The list of builders which will compute targets for this model.
        """
        super().__init__(future_trajectory_sampling=future_trajectory_sampling, feature_builders=feature_builders, target_builders=target_builders)

    @abstractmethod
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        This method contains the logic that will be exported when scripted.
        It is expected that the input dictionaries contain the data as created by the supplied feature builders.
        :param tensor_data: The input tensor data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_tensor_data: The input List[tensor] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :param list_list_tensor_data: The input List[List[tensor]] data to the function.
            This will come from the `scriptable_forward` methods in the provided feature builders.
        :return: The output from the function.
        """
        raise NotImplementedError()

def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
    """
        Construct a scriptable model with feature and target builders.
        :param future_trajectory_sampling: Parameters for a predicted trajectory.
        :param feature_builders: The list of builders which will compute features for this model.
        :param target_builders: The list of builders which will compute targets for this model.
        """
    super().__init__(future_trajectory_sampling=future_trajectory_sampling, feature_builders=feature_builders, target_builders=target_builders)

class TorchModuleWrapper(torch.nn.Module):
    """Torch module wrapper that encapsulates builders for constructing model features and targets."""

    def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
        """
        Construct a model with feature and target builders.
        :param future_trajectory_sampling: Parameters for a predicted trajectory.
        :param feature_builders: The list of builders which will compute features for this model.
        :param target_builders: The list of builders which will compute targets for this model.
        """
        super().__init__()
        self.future_trajectory_sampling = future_trajectory_sampling
        self.feature_builders = feature_builders
        self.target_builders = target_builders

    def get_list_of_required_feature(self) -> List[AbstractFeatureBuilder]:
        """Get list of required input features to the model."""
        return self.feature_builders

    def get_list_of_computed_target(self) -> List[AbstractTargetBuilder]:
        """Get list of features that the model computes."""
        return self.target_builders

    @abc.abstractmethod
    def forward(self, features: FeaturesType) -> TargetsType:
        """
        The main inference call for the model.
        :param features: A dictionary of the required features.
        :return: The results of the inference as a TargetsType.
        """
        pass

def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder]):
    """
        Construct a model with feature and target builders.
        :param future_trajectory_sampling: Parameters for a predicted trajectory.
        :param feature_builders: The list of builders which will compute features for this model.
        :param target_builders: The list of builders which will compute targets for this model.
        """
    super().__init__()
    self.future_trajectory_sampling = future_trajectory_sampling
    self.feature_builders = feature_builders
    self.target_builders = target_builders

class LaneGCN(TorchModuleWrapper):
    """
    Vector-based model that uses a series of MLPs to encode ego and agent signals, a lane graph to encode vector-map
    elements and a fusion network to capture lane & agent intra/inter-interactions through attention layers.
    Dynamic map elements such as traffic light status and ego route information are also encoded in the fusion network.

    Implementation of the original LaneGCN paper ("Learning Lane Graph Representations for Motion Forecasting").
    """

    def __init__(self, map_net_scales: int, num_res_blocks: int, num_attention_layers: int, a2a_dist_threshold: float, l2a_dist_threshold: float, num_output_features: int, feature_dim: int, vector_map_feature_radius: int, vector_map_connection_scales: Optional[List[int]], past_trajectory_sampling: TrajectorySampling, future_trajectory_sampling: TrajectorySampling):
        """
        :param map_net_scales: Number of scales to extend the predecessor and successor lane nodes.
        :param num_res_blocks: Number of residual blocks for the GCN (LaneGCN uses 4).
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param a2a_dist_threshold: [m] distance threshold for aggregating actor-to-actor nodes
        :param l2a_dist_threshold: [m] distance threshold for aggregating map-to-actor nodes
        :param num_output_features: number of target features
        :param feature_dim: hidden layer dimension
        :param vector_map_feature_radius: The query radius scope relative to the current ego-pose.
        :param vector_map_connection_scales: The hops of lane neighbors to extract, default 1 hop
        :param past_trajectory_sampling: Sampling parameters for past trajectory
        :param future_trajectory_sampling: Sampling parameters for future trajectory
        """
        super().__init__(feature_builders=[VectorMapFeatureBuilder(radius=vector_map_feature_radius, connection_scales=vector_map_connection_scales), AgentsFeatureBuilder(trajectory_sampling=past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling=future_trajectory_sampling)], future_trajectory_sampling=future_trajectory_sampling)
        self.feature_dim = feature_dim
        self.connection_scales = list(range(map_net_scales)) if vector_map_connection_scales is None else vector_map_connection_scales
        self.ego_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.ego_state_dim()
        self.agent_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.agents_states_dim()
        self.lane_net = LaneNet(lane_input_len=2, lane_feature_len=self.feature_dim, num_scales=map_net_scales, num_residual_blocks=num_res_blocks, is_map_feat=False)
        self.ego_feature_extractor = torch.nn.Sequential(nn.Linear(self.ego_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(inplace=True), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
        self.agent_feature_extractor = torch.nn.Sequential(nn.Linear(self.agent_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
        self.actor2lane_attention = Actor2LaneAttention(actor_feature_len=self.feature_dim, lane_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
        self.lane2actor_attention = Lane2ActorAttention(lane_feature_len=self.feature_dim, actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
        self.actor2actor_attention = Actor2ActorAttention(actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=a2a_dist_threshold)
        self._mlp = nn.Sequential(nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, num_output_features))

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "vector_map": VectorMap,
                            "agents": Agents,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        vector_map_data = cast(VectorMap, features['vector_map'])
        ego_agent_features = cast(Agents, features['agents'])
        ego_past_trajectory = ego_agent_features.ego
        batch_size = ego_agent_features.batch_size
        ego_features = []
        for sample_idx in range(batch_size):
            sample_ego_feature = self.ego_feature_extractor(ego_past_trajectory[sample_idx].reshape(1, -1))
            sample_ego_center = ego_agent_features.get_ego_agents_center_in_sample(sample_idx)
            if not vector_map_data.is_valid:
                num_coords = 1
                coords = torch.zeros((num_coords, 2, 2), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
                connections = {}
                for scale in self.connection_scales:
                    connections[scale] = torch.zeros((num_coords, 2), device=sample_ego_feature.device).long()
                lane_meta_tl = torch.zeros((num_coords, LaneSegmentTrafficLightData._encoding_dim), device=sample_ego_feature.device)
                lane_meta_route = torch.zeros((num_coords, LaneOnRouteStatusData._encoding_dim), device=sample_ego_feature.device)
                lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
            else:
                coords = vector_map_data.coords[sample_idx]
                connections = vector_map_data.multi_scale_connections[sample_idx]
                lane_meta_tl = vector_map_data.traffic_light_data[sample_idx]
                lane_meta_route = vector_map_data.on_route_status[sample_idx]
                lane_meta = torch.cat((lane_meta_tl, lane_meta_route), dim=1)
            lane_features = self.lane_net(coords, connections)
            lane_centers = coords.mean(axis=1)
            if ego_agent_features.has_agents(sample_idx):
                sample_agents_feature = self.agent_feature_extractor(ego_agent_features.get_flatten_agents_features_in_sample(sample_idx))
                sample_agents_center = ego_agent_features.get_agents_centers_in_sample(sample_idx)
            else:
                flattened_agents = torch.zeros((1, self.agent_input_dim), device=sample_ego_feature.device, dtype=sample_ego_feature.dtype, layout=sample_ego_feature.layout)
                sample_agents_feature = self.agent_feature_extractor(flattened_agents)
                sample_agents_center = torch.zeros_like(sample_ego_center).unsqueeze(dim=0)
            ego_agents_feature = torch.cat([sample_ego_feature, sample_agents_feature], dim=0)
            ego_agents_center = torch.cat([sample_ego_center.unsqueeze(dim=0), sample_agents_center], dim=0)
            lane_features = self.actor2lane_attention(ego_agents_feature, ego_agents_center, lane_features, lane_meta, lane_centers)
            ego_agents_feature = self.lane2actor_attention(lane_features, lane_centers, ego_agents_feature, ego_agents_center)
            ego_agents_feature = self.actor2actor_attention(ego_agents_feature, ego_agents_center)
            ego_features.append(ego_agents_feature[0])
        ego_features = torch.cat(ego_features).view(batch_size, -1)
        predictions = self._mlp(ego_features)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

def __init__(self, map_net_scales: int, num_res_blocks: int, num_attention_layers: int, a2a_dist_threshold: float, l2a_dist_threshold: float, num_output_features: int, feature_dim: int, vector_map_feature_radius: int, vector_map_connection_scales: Optional[List[int]], past_trajectory_sampling: TrajectorySampling, future_trajectory_sampling: TrajectorySampling):
    """
        :param map_net_scales: Number of scales to extend the predecessor and successor lane nodes.
        :param num_res_blocks: Number of residual blocks for the GCN (LaneGCN uses 4).
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param a2a_dist_threshold: [m] distance threshold for aggregating actor-to-actor nodes
        :param l2a_dist_threshold: [m] distance threshold for aggregating map-to-actor nodes
        :param num_output_features: number of target features
        :param feature_dim: hidden layer dimension
        :param vector_map_feature_radius: The query radius scope relative to the current ego-pose.
        :param vector_map_connection_scales: The hops of lane neighbors to extract, default 1 hop
        :param past_trajectory_sampling: Sampling parameters for past trajectory
        :param future_trajectory_sampling: Sampling parameters for future trajectory
        """
    super().__init__(feature_builders=[VectorMapFeatureBuilder(radius=vector_map_feature_radius, connection_scales=vector_map_connection_scales), AgentsFeatureBuilder(trajectory_sampling=past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(future_trajectory_sampling=future_trajectory_sampling)], future_trajectory_sampling=future_trajectory_sampling)
    self.feature_dim = feature_dim
    self.connection_scales = list(range(map_net_scales)) if vector_map_connection_scales is None else vector_map_connection_scales
    self.ego_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.ego_state_dim()
    self.agent_input_dim = (past_trajectory_sampling.num_poses + 1) * Agents.agents_states_dim()
    self.lane_net = LaneNet(lane_input_len=2, lane_feature_len=self.feature_dim, num_scales=map_net_scales, num_residual_blocks=num_res_blocks, is_map_feat=False)
    self.ego_feature_extractor = torch.nn.Sequential(nn.Linear(self.ego_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(inplace=True), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
    self.agent_feature_extractor = torch.nn.Sequential(nn.Linear(self.agent_input_dim, self.feature_dim), nn.ReLU(inplace=True), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), LinearWithGroupNorm(self.feature_dim, self.feature_dim, num_groups=1, activation=False))
    self.actor2lane_attention = Actor2LaneAttention(actor_feature_len=self.feature_dim, lane_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
    self.lane2actor_attention = Lane2ActorAttention(lane_feature_len=self.feature_dim, actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=l2a_dist_threshold)
    self.actor2actor_attention = Actor2ActorAttention(actor_feature_len=self.feature_dim, num_attention_layers=num_attention_layers, dist_threshold_m=a2a_dist_threshold)
    self._mlp = nn.Sequential(nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, self.feature_dim), nn.ReLU(), nn.Linear(self.feature_dim, num_output_features))

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

class TypeEmbedding(nn.Module):
    """
    Adapted from L5Kit's implementation `VectorizedEmbedding`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/global_graph.py.
    Changes:
        1. Change input variable name `d_model` to `embedding_size`
        2. Change variable name `pe` to `pos_encoding`
        3. Change variable name `t` to `seq_idx`
        4. Change `forward` with own feature types

    A module which associates learnable embeddings to types.
    """

    def __init__(self, embedding_dim: int, feature_types: Dict[str, int]):
        """
        Constructs TypeEmbedding.
        :param embedding_dim: Feature embedding dimensionality.
        :param feature_types: Dict representing feature types keyed by name (Torchscript not supportive of enums).
        """
        super(TypeEmbedding, self).__init__()
        self._feature_types = feature_types
        self.embedding = nn.Embedding(len(self._feature_types), embedding_dim)

    def forward(self, batch_size: int, agents_len: int, agent_features: List[str], map_features: List[str], map_features_len: Dict[str, int], device: torch.device) -> torch.Tensor:
        """
        Forward of the module: embed the given elements based on their type.
        Assumptions:
        - agent of interest is the first one in the batch
        - other agents follow
        - then we have map features (polylines)
        :param batch_size: number of samples in batch.
        :param agents_len: number of agents.
        :param agent_features: list of agent feature types.
        :param map_features: list of map feature types.
        :param map_features_len: number of map features per type.
        :param device: desired device of tensors to supply to torch.
        :return Output tensor.
        """
        with torch.no_grad():
            total_agents_len = agents_len * len(agent_features)
            total_len = 1 + total_agents_len + sum(map_features_len.values())
            agents_start_idx = 1
            map_start_idx = agents_start_idx + total_agents_len
            indices = torch.full((batch_size, total_len), fill_value=self._feature_types['NONE'], dtype=torch.long, device=device)
            indices[:, 0].fill_(self._feature_types['EGO'])
            for feature_name in agent_features:
                indices[:, agents_start_idx:agents_start_idx + agents_len].fill_(self._feature_types[feature_name])
                agents_start_idx += agents_len
            for feature_name in map_features:
                feature_len = map_features_len[feature_name]
                indices[:, map_start_idx:map_start_idx + feature_len].fill_(self._feature_types[feature_name])
                map_start_idx += feature_len
        return self.embedding.forward(indices)

def __init__(self, embedding_dim: int, feature_types: Dict[str, int]):
    """
        Constructs TypeEmbedding.
        :param embedding_dim: Feature embedding dimensionality.
        :param feature_types: Dict representing feature types keyed by name (Torchscript not supportive of enums).
        """
    super(TypeEmbedding, self).__init__()
    self._feature_types = feature_types
    self.embedding = nn.Embedding(len(self._feature_types), embedding_dim)

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

def __init__(self, dim_in: int, dim_out: int) -> None:
    """
        Constructs local subgraph layer.
        :param dim_in: Input feat size.
        :param dim_out: Output feat size.
        """
    super(LocalSubGraphLayer, self).__init__()
    self.mlp = LocalMLP(dim_in)
    self.linear_remap = nn.Linear(dim_in * 2, dim_out)

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

class MultiheadAttentionGlobalHead(nn.Module):
    """
    Copied from L5Kit's implementation `MultiheadAttentionGlobalHead`:
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/global_graph.py.
    Changes:
        1. Add input & output description for `__init__`, `forward`
        2. Add num_mlp_layers & hidden_size_scaling to adjust MLP layers
        3. Change input variable `d_model` to `global_embedding_size`

    Global graph making use of multi-head attention.
    """

    def __init__(self, global_embedding_size: int, num_timesteps: int, num_outputs: int, nhead: int=8, dropout: float=0.1, hidden_size_scaling: int=4, num_mlp_layers: int=3):
        """
        Constructs global multi-head attention layer.
        :param global_embedding_size: Feature size.
        :param num_timesteps: Number of output timesteps.
        :param num_outputs: Number of output features per timestep.
        :param nhead: Number of attention heads. Default 8: query=ego, keys=types,ego,agents,map, values=ego,agents,map.
        :param dropout: Float in range [0,1] for level of dropout. Set to 0 to disable it. Default 0.1.
        :param hidden_size_scaling: Controls hidden layer size, scales embedding dimensionality. Default 4.
        :param num_mlp_layers: Num MLP layers. Default 3.
        """
        super().__init__()
        self.num_timesteps = num_timesteps
        self.num_outputs = num_outputs
        self.encoder = nn.MultiheadAttention(global_embedding_size, nhead, dropout=dropout)
        self.output_embed = MLP(global_embedding_size, global_embedding_size * hidden_size_scaling, num_timesteps * num_outputs, num_mlp_layers)

    def forward(self, inputs: torch.Tensor, type_embedding: torch.Tensor, mask: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward of the module.
        :param inputs: Model inputs. [1 + N + M, batch_size, feature_dim]
        :param type_embedding: Type embedding describing the different input types. [1 + N + M, batch_size, feature_dim]
        :param mask: Availability mask. [batch_size, 1 + N + M]
        :return Tuple of outputs, attention.
        """
        out, attns = self.encoder(inputs[[0]], inputs + type_embedding, inputs, mask)
        outputs = self.output_embed(out[0]).view(-1, self.num_timesteps, self.num_outputs)
        return (outputs, attns)

def __init__(self, global_embedding_size: int, num_timesteps: int, num_outputs: int, nhead: int=8, dropout: float=0.1, hidden_size_scaling: int=4, num_mlp_layers: int=3):
    """
        Constructs global multi-head attention layer.
        :param global_embedding_size: Feature size.
        :param num_timesteps: Number of output timesteps.
        :param num_outputs: Number of output features per timestep.
        :param nhead: Number of attention heads. Default 8: query=ego, keys=types,ego,agents,map, values=ego,agents,map.
        :param dropout: Float in range [0,1] for level of dropout. Set to 0 to disable it. Default 0.1.
        :param hidden_size_scaling: Controls hidden layer size, scales embedding dimensionality. Default 4.
        :param num_mlp_layers: Num MLP layers. Default 3.
        """
    super().__init__()
    self.num_timesteps = num_timesteps
    self.num_outputs = num_outputs
    self.encoder = nn.MultiheadAttention(global_embedding_size, nhead, dropout=dropout)
    self.output_embed = MLP(global_embedding_size, global_embedding_size * hidden_size_scaling, num_timesteps * num_outputs, num_mlp_layers)

class GraphAttention(nn.Module):
    """
    Graph attention module to pool features from source nodes to destination nodes.

    Given a destination node i, we aggregate the features from nearby source nodes j whose L2
    distance from the destination node i is smaller than a threshold.

    This graph attention module follows the implementation in LaneGCN and is slightly different
    from the one in Graph Attention Networks.

    Compared to the open-sourced LaneGCN, this implementation omitted a few LayerNorm operations
    after some layers.
    """

    def __init__(self, src_feature_len: int, dst_feature_len: int, dist_threshold: float):
        """
        Initialize the model.
        :param src_feature_len: source node feature length.
        :param dst_feature_len: destination node feature length.
        :param dist_threshold: Distance threshold in meters. Only node information is aggregated if the destination
                               nodes are within this distance threshold from the source nodes.
        """
        super().__init__()
        self.dist_threshold = dist_threshold
        self.src_encoder = nn.Sequential(nn.Linear(src_feature_len, src_feature_len), nn.ReLU(inplace=True))
        self.dst_encoder = nn.Sequential(nn.Linear(dst_feature_len, dst_feature_len), nn.ReLU(inplace=True))
        edge_dist_feature_len = dst_feature_len
        self.edge_dist_encoder = nn.Sequential(nn.Linear(2, edge_dist_feature_len), nn.ReLU(inplace=True))
        edge_input_feature_len = src_feature_len + edge_dist_feature_len + dst_feature_len
        edge_output_feature_len = dst_feature_len
        self.edge_encoder = nn.Sequential(nn.Linear(edge_input_feature_len, edge_output_feature_len), nn.ReLU(inplace=True), nn.Linear(edge_output_feature_len, edge_output_feature_len))
        self.dst_feature_norm = nn.LayerNorm(dst_feature_len)
        self.output_linear = nn.Linear(dst_feature_len, dst_feature_len)

    def forward(self, src_node_features: torch.Tensor, src_node_pos: torch.Tensor, dst_node_features: torch.Tensor, dst_node_pos: torch.Tensor) -> torch.Tensor:
        """
        Graph attention module to pool features from source nodes to destination nodes.
        :param src_node_features: <torch.FloatTensor: num_src_nodes, src_node_feature_len>. Source node features.
        :param src_node_pos: <torch.FloatTensor: num_src_nodes, 2>. Source node (x, y) positions.
        :param dst_node_features: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Destination node features.
        :param dst_node_pos: <torch.FloatTensor: num_dst_nodes, 2>. Destination node (x, y) positions.
        :return: <torch.FloatTensor: num_dst_nodes, dst_node_feature_len>. Output destination node features.
        """
        src_dst_dist = (src_node_pos.view(-1, 1, 2) - dst_node_pos.view(1, -1, 2)).norm(dim=-1)
        src_dst_dist_mask = src_dst_dist <= self.dist_threshold
        edge_src_dist_pairs = src_dst_dist_mask.nonzero(as_tuple=False)
        edge_src_idx = edge_src_dist_pairs[:, 0]
        edge_dst_idx = edge_src_dist_pairs[:, 1]
        src_node_encoded_features = self.src_encoder(src_node_features)
        dst_node_encoded_features = self.dst_encoder(dst_node_features)
        edge_src_features = src_node_encoded_features[edge_src_idx]
        edge_dst_features = dst_node_encoded_features[edge_dst_idx]
        edge_src_pos = src_node_pos[edge_src_idx]
        edge_dst_pos = dst_node_pos[edge_dst_idx]
        edge_dist = self.edge_dist_encoder(edge_src_pos - edge_dst_pos)
        edge_input_features = torch.cat([edge_src_features, edge_dist, edge_dst_features], dim=-1)
        edge_output_features = self.edge_encoder(edge_input_features)
        dst_node_output_features = dst_node_encoded_features.clone()
        dst_node_output_features.index_add_(0, edge_dst_idx, edge_output_features)
        dst_node_output_features = self.dst_feature_norm(dst_node_output_features)
        dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
        dst_node_output_features = self.output_linear(dst_node_output_features)
        dst_node_output_features += dst_node_features
        dst_node_output_features = F.relu(dst_node_output_features, inplace=True)
        return dst_node_output_features

def __init__(self, src_feature_len: int, dst_feature_len: int, dist_threshold: float):
    """
        Initialize the model.
        :param src_feature_len: source node feature length.
        :param dst_feature_len: destination node feature length.
        :param dist_threshold: Distance threshold in meters. Only node information is aggregated if the destination
                               nodes are within this distance threshold from the source nodes.
        """
    super().__init__()
    self.dist_threshold = dist_threshold
    self.src_encoder = nn.Sequential(nn.Linear(src_feature_len, src_feature_len), nn.ReLU(inplace=True))
    self.dst_encoder = nn.Sequential(nn.Linear(dst_feature_len, dst_feature_len), nn.ReLU(inplace=True))
    edge_dist_feature_len = dst_feature_len
    self.edge_dist_encoder = nn.Sequential(nn.Linear(2, edge_dist_feature_len), nn.ReLU(inplace=True))
    edge_input_feature_len = src_feature_len + edge_dist_feature_len + dst_feature_len
    edge_output_feature_len = dst_feature_len
    self.edge_encoder = nn.Sequential(nn.Linear(edge_input_feature_len, edge_output_feature_len), nn.ReLU(inplace=True), nn.Linear(edge_output_feature_len, edge_output_feature_len))
    self.dst_feature_norm = nn.LayerNorm(dst_feature_len)
    self.output_linear = nn.Linear(dst_feature_len, dst_feature_len)

class Actor2LaneAttention(nn.Module):
    """
    Actor-to-Lane attention module.
    """

    def __init__(self, actor_feature_len: int, lane_feature_len: int, num_attention_layers: int, dist_threshold_m: float, num_groups: int=1) -> None:
        """
        :param actor_feature_len: Actor feature length.
        :param lane_feature_len: Lane feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m: Distance threshold in meters. We only aggregate map-to-actor node information if the
                                 actor nodes are within this distance threshold from the lane nodes. The value used
                                 in the LaneGCN paper is 100 meters.
        :param num_groups: Number of groups in groupnorm layer.
        """
        super().__init__()
        extra_lane_feature_dim = 6
        self.lane_meta = LinearWithGroupNorm(lane_feature_len + extra_lane_feature_dim, lane_feature_len, num_groups=num_groups, activation=False)
        attention_layers = [GraphAttention(actor_feature_len, lane_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor, lane_features: torch.Tensor, lane_meta: torch.Tensor, lane_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Actor-to-Lane attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_meta: <torch.FloatTensor: num_lanes, meta_feature_len>. Lane meta feature (TL,
            goal)
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
        lane_features = torch.cat((lane_features, lane_meta), dim=1)
        lane_features = self.lane_meta(lane_features)
        for attention_layer in self.attention_layers:
            lane_features = attention_layer(actor_features, actor_centers, lane_features, lane_centers)
        return lane_features

def __init__(self, actor_feature_len: int, lane_feature_len: int, num_attention_layers: int, dist_threshold_m: float, num_groups: int=1) -> None:
    """
        :param actor_feature_len: Actor feature length.
        :param lane_feature_len: Lane feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m: Distance threshold in meters. We only aggregate map-to-actor node information if the
                                 actor nodes are within this distance threshold from the lane nodes. The value used
                                 in the LaneGCN paper is 100 meters.
        :param num_groups: Number of groups in groupnorm layer.
        """
    super().__init__()
    extra_lane_feature_dim = 6
    self.lane_meta = LinearWithGroupNorm(lane_feature_len + extra_lane_feature_dim, lane_feature_len, num_groups=num_groups, activation=False)
    attention_layers = [GraphAttention(actor_feature_len, lane_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
    self.attention_layers = nn.ModuleList(attention_layers)

class Lane2ActorAttention(nn.Module):
    """
    Lane-to-Actor attention module.
    """

    def __init__(self, lane_feature_len: int, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
        """
        :param lane_feature_len: Lane feature length.
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate map-to-actor node
            information if the actor nodes are within this distance threshold from the lane nodes.
            The value used in the LaneGCN paper is 100 meters.
        """
        super().__init__()
        attention_layers = [GraphAttention(lane_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, lane_features: torch.Tensor, lane_centers: torch.Tensor, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Lane-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :param lane_features: <torch.FloatTensor: num_lanes, lane_feature_len>. Lane features.
            Features corresponding to map nodes.
        :param lane_centers: <torch.FloatTensor: num_lanes, 2>. (x, y) positions of the lanes.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after
            aggregating the lane features.
        """
        for attention_layer in self.attention_layers:
            actor_features = attention_layer(lane_features, lane_centers, actor_features, actor_centers)
        return actor_features

def __init__(self, lane_feature_len: int, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
    """
        :param lane_feature_len: Lane feature length.
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate map-to-actor node
            information if the actor nodes are within this distance threshold from the lane nodes.
            The value used in the LaneGCN paper is 100 meters.
        """
    super().__init__()
    attention_layers = [GraphAttention(lane_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
    self.attention_layers = nn.ModuleList(attention_layers)

class Actor2ActorAttention(nn.Module):
    """
    Actor-to-Actor attention module.
    """

    def __init__(self, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
        """
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate actor-to-actor node
            information if the actor nodes are within this distance threshold from the other actor nodes.
            The value used in the LaneGCN paper is 30 meters.
        """
        super().__init__()
        attention_layers = [GraphAttention(actor_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
        self.attention_layers = nn.ModuleList(attention_layers)

    def forward(self, actor_features: torch.Tensor, actor_centers: torch.Tensor) -> torch.Tensor:
        """
        Perform Actor-to-Actor attention.

        :param actor_features: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features.
        :param actor_centers: <torch.FloatTensor: num_actors, 2>. (x, y) positions of the actors.
        :return: <torch.FloatTensor: num_actors, actor_feature_len>. Actor features after aggregating the lane features.
        """
        for attention_layer in self.attention_layers:
            actor_features = attention_layer(actor_features, actor_centers, actor_features, actor_centers)
        return actor_features

def __init__(self, actor_feature_len: int, num_attention_layers: int, dist_threshold_m: float) -> None:
    """
        :param actor_feature_len: Actor feature length.
        :param num_attention_layers: Number of times to repeatedly apply the attention layer.
        :param dist_threshold_m:
            Distance threshold in meters.
            We only aggregate actor-to-actor node
            information if the actor nodes are within this distance threshold from the other actor nodes.
            The value used in the LaneGCN paper is 30 meters.
        """
    super().__init__()
    attention_layers = [GraphAttention(actor_feature_len, actor_feature_len, dist_threshold_m) for _ in range(num_attention_layers)]
    self.attention_layers = nn.ModuleList(attention_layers)

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

class RasterModel(TorchModuleWrapper):
    """
    Wrapper around raster-based CNN model that consumes ego, agent and map data in rasterized format
    and regresses ego's future trajectory.
    """

    def __init__(self, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], model_name: str, pretrained: bool, num_input_channels: int, num_features_per_pose: int, future_trajectory_sampling: TrajectorySampling):
        """
        Initialize model.
        :param feature_builders: list of builders for features
        :param target_builders: list of builders for targets
        :param model_name: name of the model (e.g. resnet_50, efficientnet_b3)
        :param pretrained: whether the model will be pretrained
        :param num_input_channels: number of input channel of the raster model.
        :param num_features_per_pose: number of features per single pose
        :param future_trajectory_sampling: parameters of predicted trajectory
        """
        super().__init__(feature_builders=feature_builders, target_builders=target_builders, future_trajectory_sampling=future_trajectory_sampling)
        num_output_features = future_trajectory_sampling.num_poses * num_features_per_pose
        self._model = timm.create_model(model_name, pretrained=pretrained, num_classes=0, in_chans=num_input_channels)
        mlp = torch.nn.Linear(in_features=self._model.num_features, out_features=num_output_features)
        if hasattr(self._model, 'classifier'):
            self._model.classifier = mlp
        elif hasattr(self._model, 'fc'):
            self._model.fc = mlp
        else:
            raise NameError('Expected output layer named "classifier" or "fc" in model')

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "raster": Raster,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        raster: Raster = features['raster']
        predictions = self._model.forward(raster.data)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(predictions))}

def __init__(self, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], model_name: str, pretrained: bool, num_input_channels: int, num_features_per_pose: int, future_trajectory_sampling: TrajectorySampling):
    """
        Initialize model.
        :param feature_builders: list of builders for features
        :param target_builders: list of builders for targets
        :param model_name: name of the model (e.g. resnet_50, efficientnet_b3)
        :param pretrained: whether the model will be pretrained
        :param num_input_channels: number of input channel of the raster model.
        :param num_features_per_pose: number of features per single pose
        :param future_trajectory_sampling: parameters of predicted trajectory
        """
    super().__init__(feature_builders=feature_builders, target_builders=target_builders, future_trajectory_sampling=future_trajectory_sampling)
    num_output_features = future_trajectory_sampling.num_poses * num_features_per_pose
    self._model = timm.create_model(model_name, pretrained=pretrained, num_classes=0, in_chans=num_input_channels)
    mlp = torch.nn.Linear(in_features=self._model.num_features, out_features=num_output_features)
    if hasattr(self._model, 'classifier'):
        self._model.classifier = mlp
    elif hasattr(self._model, 'fc'):
        self._model.fc = mlp
    else:
        raise NameError('Expected output layer named "classifier" or "fc" in model')

class UrbanDriverOpenLoopModel(TorchModuleWrapper):
    """
    Vector-based model that uses PointNet-based subgraph layers for collating loose collections of vectorized inputs
    into local feature descriptors to be used as input to a global Transformer.

    Adapted from L5Kit's implementation of "Urban Driver: Learning to Drive from Real-world Demonstrations
    Using Policy Gradients":
    https://github.com/woven-planet/l5kit/blob/master/l5kit/l5kit/planning/vectorized/open_loop_model.py
    Only the open-loop  version of the model is here represented, with slight modifications to fit the nuPlan framework.
    Changes:
        1. Use nuPlan features from NuPlanScenario
        2. Format model for using pytorch_lightning
    """

    def __init__(self, model_params: UrbanDriverOpenLoopModelParams, feature_params: UrbanDriverOpenLoopModelFeatureParams, target_params: UrbanDriverOpenLoopModelTargetParams):
        """
        Initialize UrbanDriverOpenLoop model.
        :param model_params: internal model parameters.
        :param feature_params: agent and map feature parameters.
        :param target_params: target parameters.
        """
        super().__init__(feature_builders=[VectorSetMapFeatureBuilder(map_features=feature_params.map_features, max_elements=feature_params.max_elements, max_points=feature_params.max_points, radius=feature_params.vector_set_map_feature_radius, interpolation_method=feature_params.interpolation_method), GenericAgentsFeatureBuilder(feature_params.agent_features, feature_params.past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(target_params.future_trajectory_sampling)], future_trajectory_sampling=target_params.future_trajectory_sampling)
        self._model_params = model_params
        self._feature_params = feature_params
        self._target_params = target_params
        self.feature_embedding = nn.Linear(self._feature_params.feature_dimension, self._model_params.local_embedding_size)
        self.positional_embedding = SinusoidalPositionalEmbedding(self._model_params.local_embedding_size)
        self.type_embedding = TypeEmbedding(self._model_params.global_embedding_size, self._feature_params.feature_types)
        self.local_subgraph = LocalSubGraph(num_layers=self._model_params.num_subgraph_layers, dim_in=self._model_params.local_embedding_size)
        if self._model_params.global_embedding_size != self._model_params.local_embedding_size:
            self.global_from_local = nn.Linear(self._model_params.local_embedding_size, self._model_params.global_embedding_size)
        num_timesteps = self.future_trajectory_sampling.num_poses
        self.global_head = MultiheadAttentionGlobalHead(self._model_params.global_embedding_size, num_timesteps, self._target_params.num_output_features // num_timesteps, dropout=self._model_params.global_head_dropout)

    def extract_agent_features(self, ego_agent_features: GenericAgents, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract ego and agent features into format expected by network and build accompanying availability matrix.
        :param ego_agent_features: agent features to be extracted (ego + other agents)
        :param batch_size: number of samples in batch to extract
        :return:
            agent_features: <torch.FloatTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element, feature_dimension>. Stacked ego, agent, and map features.
            agent_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (1+max_agents*num_agent_types),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
        agent_features = []
        agent_avails = []
        for sample_idx in range(batch_size):
            sample_ego_feature = ego_agent_features.ego[sample_idx][..., :min(self._feature_params.ego_dimension, self._feature_params.feature_dimension)].unsqueeze(0)
            if min(self._feature_params.ego_dimension, GenericAgents.ego_state_dim()) < self._feature_params.feature_dimension:
                sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.feature_dimension, dim=2)
            sample_ego_avails = torch.ones(sample_ego_feature.shape[0], sample_ego_feature.shape[1], dtype=torch.bool, device=sample_ego_feature.device)
            sample_ego_feature = torch.flip(sample_ego_feature, dims=[1])
            sample_ego_feature = sample_ego_feature[:, :self._feature_params.total_max_points, ...]
            sample_ego_avails = sample_ego_avails[:, :self._feature_params.total_max_points, ...]
            if sample_ego_feature.shape[1] < self._feature_params.total_max_points:
                sample_ego_feature = pad_polylines(sample_ego_feature, self._feature_params.total_max_points, dim=1)
                sample_ego_avails = pad_avails(sample_ego_avails, self._feature_params.total_max_points, dim=1)
            sample_features = [sample_ego_feature]
            sample_avails = [sample_ego_avails]
            for feature_name in self._feature_params.agent_features:
                if ego_agent_features.has_agents(feature_name, sample_idx):
                    sample_agent_features = torch.permute(ego_agent_features.agents[feature_name][sample_idx], (1, 0, 2))
                    sample_agent_features = sample_agent_features[..., :min(self._feature_params.agent_dimension, self._feature_params.feature_dimension)]
                    if min(self._feature_params.agent_dimension, GenericAgents.agents_states_dim()) < self._feature_params.feature_dimension:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.feature_dimension, dim=2)
                    sample_agent_avails = torch.ones(sample_agent_features.shape[0], sample_agent_features.shape[1], dtype=torch.bool, device=sample_agent_features.device)
                    sample_agent_features = torch.flip(sample_agent_features, dims=[1])
                    sample_agent_features = sample_agent_features[:, :self._feature_params.total_max_points, ...]
                    sample_agent_avails = sample_agent_avails[:, :self._feature_params.total_max_points, ...]
                    if sample_agent_features.shape[1] < self._feature_params.total_max_points:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.total_max_points, dim=1)
                        sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.total_max_points, dim=1)
                    sample_agent_features = sample_agent_features[:self._feature_params.max_agents, ...]
                    sample_agent_avails = sample_agent_avails[:self._feature_params.max_agents, ...]
                    if sample_agent_features.shape[0] < self._feature_params.max_agents:
                        sample_agent_features = pad_polylines(sample_agent_features, self._feature_params.max_agents, dim=0)
                        sample_agent_avails = pad_avails(sample_agent_avails, self._feature_params.max_agents, dim=0)
                else:
                    sample_agent_features = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, self._feature_params.feature_dimension, dtype=torch.float32, device=sample_ego_feature.device)
                    sample_agent_avails = torch.zeros(self._feature_params.max_agents, self._feature_params.total_max_points, dtype=torch.bool, device=sample_agent_features.device)
                sample_features.append(sample_agent_features)
                sample_avails.append(sample_agent_avails)
            sample_features = torch.cat(sample_features, dim=0)
            sample_avails = torch.cat(sample_avails, dim=0)
            agent_features.append(sample_features)
            agent_avails.append(sample_avails)
        agent_features = torch.stack(agent_features)
        agent_avails = torch.stack(agent_avails)
        return (agent_features, agent_avails)

    def extract_map_features(self, vector_set_map_data: VectorSetMap, batch_size: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract map features into format expected by network and build accompanying availability matrix.
        :param vector_set_map_data: VectorSetMap features to be extracted
        :param batch_size: number of samples in batch to extract
        :return:
            map_features: <torch.FloatTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element, feature_dimension>. Stacked map features.
            map_avails: <torch.BoolTensor: batch_size, num_elements (polylines) (max_lanes),
                num_points_per_element>. Bool specifying whether feature is available or zero padded.
        """
        map_features = []
        map_avails = []
        for sample_idx in range(batch_size):
            sample_map_features = []
            sample_map_avails = []
            for feature_name in self._feature_params.map_features:
                coords = vector_set_map_data.coords[feature_name][sample_idx]
                tl_data = vector_set_map_data.traffic_light_data[feature_name][sample_idx] if feature_name in vector_set_map_data.traffic_light_data else None
                avails = vector_set_map_data.availabilities[feature_name][sample_idx]
                if tl_data is not None:
                    coords = torch.cat((coords, tl_data), dim=2)
                coords = coords[:, :self._feature_params.total_max_points, ...]
                avails = avails[:, :self._feature_params.total_max_points]
                if coords.shape[1] < self._feature_params.total_max_points:
                    coords = pad_polylines(coords, self._feature_params.total_max_points, dim=1)
                    avails = pad_avails(avails, self._feature_params.total_max_points, dim=1)
                coords = coords[..., :self._feature_params.feature_dimension]
                if coords.shape[2] < self._feature_params.feature_dimension:
                    coords = pad_polylines(coords, self._feature_params.feature_dimension, dim=2)
                sample_map_features.append(coords)
                sample_map_avails.append(avails)
            map_features.append(torch.cat(sample_map_features))
            map_avails.append(torch.cat(sample_map_avails))
        map_features = torch.stack(map_features)
        map_avails = torch.stack(map_avails)
        return (map_features, map_avails)

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Predict
        :param features: input features containing
                        {
                            "vector_set_map": VectorSetMap,
                            "generic_agents": GenericAgents,
                        }
        :return: targets: predictions from network
                        {
                            "trajectory": Trajectory,
                        }
        """
        vector_set_map_data = cast(VectorSetMap, features['vector_set_map'])
        ego_agent_features = cast(GenericAgents, features['generic_agents'])
        batch_size = ego_agent_features.batch_size
        agent_features, agent_avails = self.extract_agent_features(ego_agent_features, batch_size)
        map_features, map_avails = self.extract_map_features(vector_set_map_data, batch_size)
        features = torch.cat([agent_features, map_features], dim=1)
        avails = torch.cat([agent_avails, map_avails], dim=1)
        feature_embedding = self.feature_embedding(features)
        pos_embedding = self.positional_embedding(features).unsqueeze(0).transpose(1, 2)
        invalid_mask = ~avails
        invalid_polys = invalid_mask.all(-1)
        embeddings = self.local_subgraph(feature_embedding, invalid_mask, pos_embedding)
        if hasattr(self, 'global_from_local'):
            embeddings = self.global_from_local(embeddings)
        embeddings = F.normalize(embeddings, dim=-1) * self._model_params.global_embedding_size ** 0.5
        embeddings = embeddings.transpose(0, 1)
        type_embedding = self.type_embedding(batch_size, self._feature_params.max_agents, self._feature_params.agent_features, self._feature_params.map_features, self._feature_params.max_elements, device=features.device).transpose(0, 1)
        if self._feature_params.disable_agents:
            invalid_polys[:, 1:1 + self._feature_params.max_agents * len(self._feature_params.agent_features)] = 1
        if self._feature_params.disable_map:
            invalid_polys[:, 1 + self._feature_params.max_agents * len(self._feature_params.agent_features):] = 1
        invalid_polys[:, 0] = 0
        outputs, attns = self.global_head(embeddings, type_embedding, invalid_polys)
        return {'trajectory': Trajectory(data=convert_predictions_to_trajectory(outputs))}

def __init__(self, model_params: UrbanDriverOpenLoopModelParams, feature_params: UrbanDriverOpenLoopModelFeatureParams, target_params: UrbanDriverOpenLoopModelTargetParams):
    """
        Initialize UrbanDriverOpenLoop model.
        :param model_params: internal model parameters.
        :param feature_params: agent and map feature parameters.
        :param target_params: target parameters.
        """
    super().__init__(feature_builders=[VectorSetMapFeatureBuilder(map_features=feature_params.map_features, max_elements=feature_params.max_elements, max_points=feature_params.max_points, radius=feature_params.vector_set_map_feature_radius, interpolation_method=feature_params.interpolation_method), GenericAgentsFeatureBuilder(feature_params.agent_features, feature_params.past_trajectory_sampling)], target_builders=[EgoTrajectoryTargetBuilder(target_params.future_trajectory_sampling)], future_trajectory_sampling=target_params.future_trajectory_sampling)
    self._model_params = model_params
    self._feature_params = feature_params
    self._target_params = target_params
    self.feature_embedding = nn.Linear(self._feature_params.feature_dimension, self._model_params.local_embedding_size)
    self.positional_embedding = SinusoidalPositionalEmbedding(self._model_params.local_embedding_size)
    self.type_embedding = TypeEmbedding(self._model_params.global_embedding_size, self._feature_params.feature_types)
    self.local_subgraph = LocalSubGraph(num_layers=self._model_params.num_subgraph_layers, dim_in=self._model_params.local_embedding_size)
    if self._model_params.global_embedding_size != self._model_params.local_embedding_size:
        self.global_from_local = nn.Linear(self._model_params.local_embedding_size, self._model_params.global_embedding_size)
    num_timesteps = self.future_trajectory_sampling.num_poses
    self.global_head = MultiheadAttentionGlobalHead(self._model_params.global_embedding_size, num_timesteps, self._target_params.num_output_features // num_timesteps, dropout=self._model_params.global_head_dropout)

def create_mlp(input_size: int, output_size: int, hidden_size: int=128) -> torch.nn.Module:
    """
    Create MLP
    :param input_size: input feature size
    :param output_size: output feature size
    :param hidden_size: hidden layer
    :return: sequential network
    """
    return nn.Sequential(nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Linear(hidden_size, output_size))

class TestLocalMLP(unittest.TestCase):
    """Test LocalMLP layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.dim_in = 256
        self.model = LocalMLP(self.dim_in)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_inputs = 10
        inputs = torch.zeros((num_inputs, self.dim_in))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_inputs, self.dim_in))

def setUp(self) -> None:
    """Set up test case."""
    self.dim_in = 256
    self.model = LocalMLP(self.dim_in)

class TestMLP(unittest.TestCase):
    """Test MLP layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.input_dim = 256
        self.hidden_dim = 256 * 4
        self.output_dim = 12 * 3
        self.num_layers = 3
        self.model = MLP(self.input_dim, self.hidden_dim, self.output_dim, self.num_layers)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_inputs = 10
        inputs = torch.zeros((num_inputs, self.input_dim))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_inputs, self.output_dim))

def setUp(self) -> None:
    """Set up test case."""
    self.input_dim = 256
    self.hidden_dim = 256 * 4
    self.output_dim = 12 * 3
    self.num_layers = 3
    self.model = MLP(self.input_dim, self.hidden_dim, self.output_dim, self.num_layers)

class TestSinusoidalPositionalEmbedding(unittest.TestCase):
    """Test SinusoidalPositionalEmbedding layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.embedding_size = 256
        self.model = SinusoidalPositionalEmbedding(self.embedding_size)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((batch_size, num_elements, num_points, self.embedding_size))
        output = self.model.forward(inputs)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_points, 1, self.embedding_size))

def setUp(self) -> None:
    """Set up test case."""
    self.embedding_size = 256
    self.model = SinusoidalPositionalEmbedding(self.embedding_size)

class TestTypeEmbedding(unittest.TestCase):
    """Test TypeEmbedding layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.embedding_dim = 256
        self.feature_types = {'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}
        self.model = TypeEmbedding(self.embedding_dim, self.feature_types)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        device = torch.device('cpu')
        batch_size = 2
        max_agents = 30
        agent_features = ['VEHICLE', 'BICYCLE', 'PEDESTRIAN']
        map_features = ['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES']
        max_elements = {'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}
        num_elements = 1 + max_agents * len(agent_features) + sum(max_elements.values())
        output = self.model.forward(batch_size, max_agents, agent_features, map_features, max_elements, device)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, num_elements, self.embedding_dim))

def setUp(self) -> None:
    """Set up test case."""
    self.embedding_dim = 256
    self.feature_types = {'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}
    self.model = TypeEmbedding(self.embedding_dim, self.feature_types)

class TestLocalSubGraphLayer(unittest.TestCase):
    """Test LocalSubGraphLayer layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.dim_in = 256
        self.dim_out = 256
        self.model = LocalSubGraphLayer(self.dim_in, self.dim_out)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((num_elements, num_points, self.dim_in))
        invalid_mask = torch.zeros((num_elements, num_points), dtype=torch.bool)
        output = self.model.forward(inputs, invalid_mask)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_elements, num_points, self.dim_out))

def setUp(self) -> None:
    """Set up test case."""
    self.dim_in = 256
    self.dim_out = 256
    self.model = LocalSubGraphLayer(self.dim_in, self.dim_out)

class TestLocalSubGraph(unittest.TestCase):
    """Test LocalSubGraph layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.num_layers = 3
        self.dim_in = 256
        self.model = LocalSubGraph(self.num_layers, self.dim_in)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        num_points = 20
        inputs = torch.zeros((batch_size, num_elements, num_points, self.dim_in), dtype=torch.float32)
        invalid_mask = torch.zeros((batch_size, num_elements, num_points), dtype=torch.bool)
        pos_enc = torch.zeros((1, 1, num_points, self.dim_in), dtype=torch.float32)
        output = self.model.forward(inputs, invalid_mask, pos_enc)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, num_elements, self.dim_in))

def setUp(self) -> None:
    """Set up test case."""
    self.num_layers = 3
    self.dim_in = 256
    self.model = LocalSubGraph(self.num_layers, self.dim_in)

class TestMultiheadAttentionGlobalHead(unittest.TestCase):
    """Test MultiheadAttentionGlobalHead layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.global_embedding_size = 256
        self.num_timesteps = 12
        self.num_outputs = 3
        self.model = MultiheadAttentionGlobalHead(self.global_embedding_size, self.num_timesteps, self.num_outputs)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        batch_size = 2
        num_elements = 10
        inputs = torch.zeros((num_elements, batch_size, self.global_embedding_size), dtype=torch.float32)
        type_embedding = torch.ones((num_elements, batch_size, self.global_embedding_size), dtype=torch.long)
        invalid_mask = torch.zeros((batch_size, num_elements), dtype=torch.bool)
        output, attns = self.model.forward(inputs, type_embedding, invalid_mask)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (batch_size, self.num_timesteps, self.num_outputs))
        self.assertIsInstance(attns, torch.Tensor)
        assert attns is not None
        self.assertEqual(attns.shape, (batch_size, 1, num_elements))

def setUp(self) -> None:
    """Set up test case."""
    self.global_embedding_size = 256
    self.num_timesteps = 12
    self.num_outputs = 3
    self.model = MultiheadAttentionGlobalHead(self.global_embedding_size, self.num_timesteps, self.num_outputs)

class TestGraphAttention(unittest.TestCase):
    """Test graph attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.src_feature_len = 4
        self.dst_feature_len = 4
        self.dist_threshold = 6.0
        self.model = GraphAttention(self.src_feature_len, self.dst_feature_len, self.dist_threshold)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_src_nodes = 2
        num_dst_nodes = 3
        src_node_features = torch.zeros((num_src_nodes, self.src_feature_len))
        src_node_pos = torch.zeros((num_src_nodes, 2))
        dst_node_features = torch.zeros((num_dst_nodes, self.dst_feature_len))
        dst_node_pos = torch.zeros((num_dst_nodes, 2))
        output = self.model.forward(src_node_features, src_node_pos, dst_node_features, dst_node_pos)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_dst_nodes, self.dst_feature_len))

def setUp(self) -> None:
    """Set up test case."""
    self.src_feature_len = 4
    self.dst_feature_len = 4
    self.dist_threshold = 6.0
    self.model = GraphAttention(self.src_feature_len, self.dst_feature_len, self.dist_threshold)

class TestActor2ActorAttention(unittest.TestCase):
    """Test actor-to-actor attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Actor2ActorAttention(self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works.
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_actors = 3
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(actor_features, actor_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_actors, self.actor_feature_len))

def setUp(self) -> None:
    """Set up test case."""
    self.actor_feature_len = 4
    self.num_attention_layers = 2
    self.dist_threshold_m = 6.0
    self.model = Actor2ActorAttention(self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

class TestLane2ActorAttention(unittest.TestCase):
    """Test lane-to-actor attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.lane_feature_len = 4
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Lane2ActorAttention(self.lane_feature_len, self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 2
        num_actors = 3
        lane_features = torch.zeros((num_lanes, self.lane_feature_len))
        lane_centers = torch.zeros((num_lanes, 2))
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(lane_features, lane_centers, actor_features, actor_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_actors, self.actor_feature_len))

def setUp(self) -> None:
    """Set up test case."""
    self.lane_feature_len = 4
    self.actor_feature_len = 4
    self.num_attention_layers = 2
    self.dist_threshold_m = 6.0
    self.model = Lane2ActorAttention(self.lane_feature_len, self.actor_feature_len, self.num_attention_layers, self.dist_threshold_m)

class TestActor2LaneAttention(unittest.TestCase):
    """Test actor-to-lane attention layer."""

    def setUp(self) -> None:
        """Set up test case."""
        self.lane_feature_len = 4
        self.actor_feature_len = 4
        self.num_attention_layers = 2
        self.dist_threshold_m = 6.0
        self.model = Actor2LaneAttention(self.actor_feature_len, self.lane_feature_len, self.num_attention_layers, self.dist_threshold_m)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 2
        num_actors = 3
        meta_info_len = 6
        lane_features = torch.zeros((num_lanes, self.lane_feature_len))
        lane_meta = torch.zeros((num_lanes, meta_info_len))
        lane_centers = torch.zeros((num_lanes, 2))
        actor_features = torch.zeros((num_actors, self.actor_feature_len))
        actor_centers = torch.zeros((num_actors, 2))
        output = self.model.forward(actor_features, actor_centers, lane_features, lane_meta, lane_centers)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_lanes, self.actor_feature_len))

def setUp(self) -> None:
    """Set up test case."""
    self.lane_feature_len = 4
    self.actor_feature_len = 4
    self.num_attention_layers = 2
    self.dist_threshold_m = 6.0
    self.model = Actor2LaneAttention(self.actor_feature_len, self.lane_feature_len, self.num_attention_layers, self.dist_threshold_m)

class TestLaneNet(unittest.TestCase):
    """Test lane net layer."""

    def setUp(self) -> None:
        """Set up the test."""
        self.lane_input_len = 2
        self.lane_feature_len = 4
        self.num_scales = 2
        self.num_res_blocks = 3
        self.model = LaneNet(lane_input_len=self.lane_input_len, lane_feature_len=self.lane_feature_len, num_scales=self.num_scales, num_residual_blocks=self.num_res_blocks, is_map_feat=False)

    def test_instantiate(self) -> None:
        """
        Dummy test to check that instantiation works
        """
        self.assertNotEqual(self.model, None)

    def test_forward(self) -> None:
        """Test forward()."""
        num_lanes = 4
        lane_input = torch.zeros((num_lanes, self.lane_input_len, 2))
        multi_scale_connections = {1: torch.tensor([[0, 1], [1, 2], [2, 3]]), 2: torch.tensor([[0, 2], [1, 3]])}
        vector_map = Munch(multi_scale_connections=multi_scale_connections)
        output = self.model.forward(lane_input, vector_map.multi_scale_connections)
        self.assertIsInstance(output, torch.Tensor)
        self.assertEqual(output.shape, (num_lanes, self.lane_feature_len))

def setUp(self) -> None:
    """Set up the test."""
    self.lane_input_len = 2
    self.lane_feature_len = 4
    self.num_scales = 2
    self.num_res_blocks = 3
    self.model = LaneNet(lane_input_len=self.lane_input_len, lane_feature_len=self.lane_feature_len, num_scales=self.num_scales, num_residual_blocks=self.num_res_blocks, is_map_feat=False)

class DeepDynamicalSystemLayer(nn.Module):
    """
    Class to forward simulate a dynamical systems
    for k steps, given an initial condition and
    inputs for each k step.

    By subclassing nn.Module, it can be integrated
    in a pipeline where gradient-based optimization
    is employed.

    Adapted from https://arxiv.org/abs/1908.00219 (Eq.ns 6 in
    the paper have slightly different kinematics)
    """

    def __init__(self, dynamics: DynamicsLayer) -> None:
        """
        Class constructor.
        """
        super().__init__()
        self.dynamics = dynamics

    def forward(self, initial_state: torch.FloatTensor, controls: torch.FloatTensor, timestep: float, agents_pars: torch.FloatTensor) -> torch.FloatTensor:
        """
        Forward pass.
        Returns state at each time step k

        :param initial_state: torch.FloatTensor [..., dynamics.state_dim()]
        :param controls: torch.FloatTensor[..., k, dynamics.control_dim()]
        :param timestep: float
        :param agents_pars: torch.FloatTensor[..., 1/2]   (length, width (optional) )

        :return: state: torch.FloatTensor[..., k, dynamics.state_dim()]
        """
        if initial_state.shape[-1] != self.dynamics.state_dim():
            raise RuntimeError(f'State dimension must be {self.dynamics.state_dim()}, got {initial_state.shape[-1]}')
        if controls.shape[-1] != self.dynamics.input_dim():
            raise RuntimeError(f'Control dimension must be {self.dynamics.input_dim()}, got {controls.shape[-1]}')
        xout = torch.empty((*controls.shape[:-1], self.dynamics.state_dim()), dtype=initial_state.dtype, device=initial_state.device)
        for i in range(controls.shape[-2]):
            initial_state = self.dynamics.forward(initial_state, controls[..., i, :], timestep, agents_pars)
            xout[..., i, :] = initial_state
        return xout

def __init__(self, dynamics: DynamicsLayer) -> None:
    """
        Class constructor.
        """
    super().__init__()
    self.dynamics = dynamics

class ScenarioDataset(torch.utils.data.Dataset):
    """
    Dataset responsible for consuming scenarios and producing pairs of model inputs/outputs.
    """

    def __init__(self, scenarios: List[AbstractScenario], feature_preprocessor: FeaturePreprocessor, augmentors: Optional[List[AbstractAugmentor]]=None) -> None:
        """
        Initializes the scenario dataset.
        :param scenarios: List of scenarios to use as dataset examples.
        :param feature_preprocessor: Feature and targets builder that converts samples to model features.
        :param augmentors: Augmentor object for providing data augmentation to data samples.
        """
        super().__init__()
        if len(scenarios) == 0:
            logger.warning('The dataset has no samples')
        self._scenarios = scenarios
        self._feature_preprocessor = feature_preprocessor
        self._augmentors = augmentors

    def __getitem__(self, idx: int) -> Tuple[FeaturesType, TargetsType, ScenarioListType]:
        """
        Retrieves the dataset examples corresponding to the input index
        :param idx: input index
        :return: model features and targets
        """
        scenario = self._scenarios[idx]
        features, targets, _ = self._feature_preprocessor.compute_features(scenario)
        if self._augmentors is not None:
            for augmentor in self._augmentors:
                augmentor.validate(features, targets)
                features, targets = augmentor.augment(features, targets, scenario)
        features = {key: value.to_feature_tensor() for key, value in features.items()}
        targets = {key: value.to_feature_tensor() for key, value in targets.items()}
        scenarios = [scenario]
        return (features, targets, scenarios)

    def __len__(self) -> int:
        """
        Returns the size of the dataset (number of samples)

        :return: size of dataset
        """
        return len(self._scenarios)

def __init__(self, scenarios: List[AbstractScenario], feature_preprocessor: FeaturePreprocessor, augmentors: Optional[List[AbstractAugmentor]]=None) -> None:
    """
        Initializes the scenario dataset.
        :param scenarios: List of scenarios to use as dataset examples.
        :param feature_preprocessor: Feature and targets builder that converts samples to model features.
        :param augmentors: Augmentor object for providing data augmentation to data samples.
        """
    super().__init__()
    if len(scenarios) == 0:
        logger.warning('The dataset has no samples')
    self._scenarios = scenarios
    self._feature_preprocessor = feature_preprocessor
    self._augmentors = augmentors

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

class DistributedSamplerWrapper(DistributedSampler):
    """Sampler that restricts data loading to a subset of input sampler indices."""

    def __init__(self, sampler: Sampler, num_replicas: Optional[int]=None, rank: Optional[int]=None) -> None:
        """
        :param sampler: Sampler object.
        :param num_replicas: Number of processes participating in distributed training.
            By default, :attr:`num_replicas` is retrieved from the current distributed group.
        :param rank: Rank of the current process within :attr:`num_replicas`.
            By default, :attr:`rank` is retrieved from the current distributed group.
        """
        super(DistributedSamplerWrapper, self).__init__(sampler, num_replicas=num_replicas, rank=rank, shuffle=False)
        self.sampler = sampler

    def __iter__(self) -> Iterator[int]:
        """Iterate through indices to be sampled from dataset"""
        torch.manual_seed(self.epoch)
        indices = list(self.sampler)
        indices += indices[:self.total_size - len(indices)]
        assert len(indices) == self.total_size, f'Length of indices sampled {len(indices)} should be same as the total number of samples {self.total_size}'
        per_replica_size = self.total_size // self.num_replicas
        replica_start = per_replica_size * self.rank
        replica_end = replica_start + per_replica_size
        epoch_indices_per_replica = indices[replica_start:replica_end]
        assert len(epoch_indices_per_replica) == self.num_samples, f'Length of indices sampled {len(epoch_indices_per_replica)} should be {self.num_samples}'
        return iter(epoch_indices_per_replica)

def __init__(self, sampler: Sampler, num_replicas: Optional[int]=None, rank: Optional[int]=None) -> None:
    """
        :param sampler: Sampler object.
        :param num_replicas: Number of processes participating in distributed training.
            By default, :attr:`num_replicas` is retrieved from the current distributed group.
        :param rank: Rank of the current process within :attr:`num_replicas`.
            By default, :attr:`rank` is retrieved from the current distributed group.
        """
    super(DistributedSamplerWrapper, self).__init__(sampler, num_replicas=num_replicas, rank=rank, shuffle=False)
    self.sampler = sampler

class TestDataloaderSequential(SkeletonTestDataloader):
    """
    Tests data loading functionality in a sequential manner.
    """

    def test_dataloader_nuplan_sequential(self) -> None:
        """
        Test dataloader using nuPlan DB using a sequential worker.
        """
        self._test_dataloader(Sequential())

def test_dataloader_nuplan_sequential(self) -> None:
    """
        Test dataloader using nuPlan DB using a sequential worker.
        """
    self._test_dataloader(Sequential())

class TestDataloaderRay(SkeletonTestDataloader):
    """
    Tests data loading functionality in ray.
    """

    def test_dataloader_nuplan_ray(self) -> None:
        """
        Test dataloader using nuPlan DB.
        """
        self._test_dataloader(RayDistributed())

def test_dataloader_nuplan_ray(self) -> None:
    """
        Test dataloader using nuPlan DB.
        """
    self._test_dataloader(RayDistributed())

class VisualizationCallback(pl.Callback):
    """
    Callback that visualizes planner model inputs/outputs and logs them in Tensorboard.
    """

    def __init__(self, images_per_tile: int, num_train_tiles: int, num_val_tiles: int, pixel_size: float):
        """
        Initialize the class.

        :param images_per_tile: number of images per tiles to visualize
        :param num_train_tiles: number of tiles from the training set
        :param num_val_tiles: number of tiles from the validation set
        :param pixel_size: [m] size of pixel in meters
        """
        super().__init__()
        self.custom_batch_size = images_per_tile
        self.num_train_images = num_train_tiles * images_per_tile
        self.num_val_images = num_val_tiles * images_per_tile
        self.pixel_size = pixel_size
        self.train_dataloader: Optional[torch.utils.data.DataLoader] = None
        self.val_dataloader: Optional[torch.utils.data.DataLoader] = None

    def _initialize_dataloaders(self, datamodule: pl.LightningDataModule) -> None:
        """
        Initialize the dataloaders. This makes sure that the same examples are sampled
        every time for comparison during visualization.

        :param datamodule: lightning datamodule
        """
        train_set = datamodule.train_dataloader().dataset
        val_set = datamodule.val_dataloader().dataset
        self.train_dataloader = self._create_dataloader(train_set, self.num_train_images)
        self.val_dataloader = self._create_dataloader(val_set, self.num_val_images)

    def _create_dataloader(self, dataset: torch.utils.data.Dataset, num_samples: int) -> torch.utils.data.DataLoader:
        dataset_size = len(dataset)
        num_keep = min(dataset_size, num_samples)
        sampled_idxs = random.sample(range(dataset_size), num_keep)
        subset = torch.utils.data.Subset(dataset=dataset, indices=sampled_idxs)
        return torch.utils.data.DataLoader(dataset=subset, batch_size=self.custom_batch_size, collate_fn=FeatureCollate())

    def _log_from_dataloader(self, pl_module: pl.LightningModule, dataloader: torch.utils.data.DataLoader, loggers: List[Any], training_step: int, prefix: str) -> None:
        """
        Visualizes and logs all examples from the input dataloader.

        :param pl_module: lightning module used for inference
        :param dataloader: torch dataloader
        :param loggers: list of loggers from the trainer
        :param training_step: global step in training
        :param prefix: prefix to add to the log tag
        """
        for batch_idx, batch in enumerate(dataloader):
            features: FeaturesType = batch[0]
            targets: TargetsType = batch[1]
            predictions = self._infer_model(pl_module, move_features_type_to_device(features, pl_module.device))
            self._log_batch(loggers, features, targets, predictions, batch_idx, training_step, prefix)

    def _log_batch(self, loggers: List[Any], features: FeaturesType, targets: TargetsType, predictions: TargetsType, batch_idx: int, training_step: int, prefix: str) -> None:
        """
        Visualizes and logs a batch of data (features, targets, predictions) from the model.

        :param loggers: list of loggers from the trainer
        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :param batch_idx: index of total batches to visualize
        :param training_step: global training step
        :param prefix: prefix to add to the log tag
        """
        if 'trajectory' not in targets or 'trajectory' not in predictions:
            return
        if 'raster' in features:
            image_batch = self._get_images_from_raster_features(features, targets, predictions)
        elif ('vector_map' in features or 'vector_set_map' in features) and ('agents' in features or 'generic_agents' in features):
            image_batch = self._get_images_from_vector_features(features, targets, predictions)
        else:
            return
        tag = f'{prefix}_visualization_{batch_idx}'
        for logger in loggers:
            if isinstance(logger, torch.utils.tensorboard.writer.SummaryWriter):
                logger.add_images(tag=tag, img_tensor=torch.from_numpy(image_batch), global_step=training_step, dataformats='NHWC')

    def _get_images_from_raster_features(self, features: FeaturesType, targets: TargetsType, predictions: TargetsType) -> npt.NDArray[np.uint8]:
        """
        Create a list of RGB raster images from a batch of model data of raster features.

        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :return: list of raster images
        """
        images = list()
        for raster, target_trajectory, predicted_trajectory in zip(features['raster'].unpack(), targets['trajectory'].unpack(), predictions['trajectory'].unpack()):
            image = get_raster_with_trajectories_as_rgb(raster, target_trajectory, predicted_trajectory, pixel_size=self.pixel_size)
            images.append(image)
        return np.asarray(images)

    def _get_images_from_vector_features(self, features: FeaturesType, targets: TargetsType, predictions: TargetsType) -> npt.NDArray[np.uint8]:
        """
        Create a list of RGB raster images from a batch of model data of vectormap and agent features.

        :param features: tensor of model features
        :param targets: tensor of model targets
        :param predictions: tensor of model predictions
        :return: list of raster images
        """
        images = list()
        vector_map_feature = 'vector_map' if 'vector_map' in features else 'vector_set_map'
        agents_feature = 'agents' if 'agents' in features else 'generic_agents'
        for vector_map, agents, target_trajectory, predicted_trajectory in zip(features[vector_map_feature].unpack(), features[agents_feature].unpack(), targets['trajectory'].unpack(), predictions['trajectory'].unpack()):
            image = get_raster_from_vector_map_with_agents(vector_map, agents, target_trajectory, predicted_trajectory, pixel_size=self.pixel_size)
            images.append(image)
        return np.asarray(images)

    def _infer_model(self, pl_module: pl.LightningModule, features: FeaturesType) -> TargetsType:
        """
        Make an inference of the input batch features given a model.

        :param pl_module: lightning model
        :param features: model inputs
        :return: model predictions
        """
        with torch.no_grad():
            pl_module.eval()
            predictions = move_features_type_to_device(pl_module(features), torch.device('cpu'))
            pl_module.train()
        return predictions

    def on_train_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional=None) -> None:
        """
        Visualizes and logs training examples at the end of the epoch.

        :param trainer: lightning trainer
        :param pl_module: lightning module
        """
        assert hasattr(trainer, 'datamodule'), 'Trainer missing datamodule attribute'
        assert hasattr(trainer, 'global_step'), 'Trainer missing global_step attribute'
        if self.train_dataloader is None:
            self._initialize_dataloaders(trainer.datamodule)
        self._log_from_dataloader(pl_module, self.train_dataloader, trainer.logger.experiment, trainer.global_step, 'train')

    def on_validation_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional=None) -> None:
        """
        Visualizes and logs validation examples at the end of the epoch.

        :param trainer: lightning trainer
        :param pl_module: lightning module
        """
        assert hasattr(trainer, 'datamodule'), 'Trainer missing datamodule attribute'
        assert hasattr(trainer, 'global_step'), 'Trainer missing global_step attribute'
        if self.val_dataloader is None:
            self._initialize_dataloaders(trainer.datamodule)
        self._log_from_dataloader(pl_module, self.val_dataloader, trainer.logger.experiment, trainer.global_step, 'val')

def __init__(self, images_per_tile: int, num_train_tiles: int, num_val_tiles: int, pixel_size: float):
    """
        Initialize the class.

        :param images_per_tile: number of images per tiles to visualize
        :param num_train_tiles: number of tiles from the training set
        :param num_val_tiles: number of tiles from the validation set
        :param pixel_size: [m] size of pixel in meters
        """
    super().__init__()
    self.custom_batch_size = images_per_tile
    self.num_train_images = num_train_tiles * images_per_tile
    self.num_val_images = num_val_tiles * images_per_tile
    self.pixel_size = pixel_size
    self.train_dataloader: Optional[torch.utils.data.DataLoader] = None
    self.val_dataloader: Optional[torch.utils.data.DataLoader] = None

class ModelCheckpointAtEpochEnd(pl.callbacks.ModelCheckpoint):
    """Customized callback for saving Lightning checkpoint for every epoch."""

    def __init__(self, save_top_k: int=-1, save_last: bool=False, dirpath: Optional[str]=None, monitor: Optional[str]=None, mode: str='max'):
        """
        Initialize the callback
        :param save_top_k: Choose how many best checkpoints we want to save:
            save_top_k == 0 means no models are saved.
            save_top_k == -1 means all models are saved.
        :param save_last: Whether to save the last model as last.ckpt.
        :param dirpath: Directory where the checkpoints are saved.
        :param monitor: The metrics to monitor for saving best checkpoints.
        :param mode: How we want to choose the best model: min, max or auto for the metrics we choose.
        """
        super().__init__(save_last=save_last, save_top_k=save_top_k, dirpath=dirpath, monitor=monitor, mode=mode)

    def on_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Customized callback function to save checkpoint every epoch.
        :param trainer: Pytorch lightning trainer instance.
        :param pl_module: LightningModule.
        """
        checkpoint_dir = Path(trainer.checkpoint_callback.dirpath).parent / 'checkpoints'
        checkpoint_name = f'epoch={trainer.current_epoch}.ckpt'
        checkpoint_path = checkpoint_dir / checkpoint_name
        trainer.save_checkpoint(str(checkpoint_path))

def __init__(self, save_top_k: int=-1, save_last: bool=False, dirpath: Optional[str]=None, monitor: Optional[str]=None, mode: str='max'):
    """
        Initialize the callback
        :param save_top_k: Choose how many best checkpoints we want to save:
            save_top_k == 0 means no models are saved.
            save_top_k == -1 means all models are saved.
        :param save_last: Whether to save the last model as last.ckpt.
        :param dirpath: Directory where the checkpoints are saved.
        :param monitor: The metrics to monitor for saving best checkpoints.
        :param mode: How we want to choose the best model: min, max or auto for the metrics we choose.
        """
    super().__init__(save_last=save_last, save_top_k=save_top_k, dirpath=dirpath, monitor=monitor, mode=mode)

class StepwiseAugmentationProbabilityScheduler(AbstractAugmentationScheduler):
    """Callback class that scales Augmentors."""

    def __init__(self, max_augment_prob: float, pct_time_increasing: float, scheduling_strategy: str, milestones: Optional[List[float]]=None):
        """
        Initializes Augmentation Scheduler Callback properties.
        :param max_augment_prob: Maximum probability of augmentation.
        :param pct_time_increasing: Percentage of the time spent increasing.
        :param scheduling strategy: Strategy for scheduling the scaling of augmentor properties during training.
        :param milestones: List of milestones for scheduling augmentation. Eg, given [0.25, 0.5, 0.75, 1.0], we will increase the augmentation when 25%, 50%, 75% of the training has completed.
        """
        super().__init__(pct_time_increasing, scheduling_strategy, milestones)
        self.max_augment_prob = max_augment_prob
        assert 0.0 <= self.max_augment_prob <= 1.0, 'Error max augmentation probability must be between 0 and 1'

    def _scale_augmentor(self, augmentor: AbstractAugmentor, cur_step: int, total_steps: int) -> None:
        """
        Scales augmentor properties.
        :param augmentor: Abstract augmentor.
        :param cur_step: Current training step.
        :param total_steps: Total number of training steps.
        """
        augmentor_name = type(augmentor).__name__
        if augmentor_name not in self._initial_augmentor_attributes:
            aug_prob = augmentor.augmentation_probability
            self._initial_augmentor_attributes[augmentor_name][aug_prob.param_name] = aug_prob
        for param_name, param_to_sale_obj in self._initial_augmentor_attributes[augmentor_name].items():
            pct_increase = self.max_augment_prob / self._initial_augmentor_attributes[augmentor_name][param_name].param - 1
            scaled_augment_prob = self._scale_augmentor_property(initial_attr=param_to_sale_obj, pct_increase=pct_increase, cur_step=cur_step, total_steps=total_steps)
            setattr(augmentor, param_name, scaled_augment_prob)

def __init__(self, max_augment_prob: float, pct_time_increasing: float, scheduling_strategy: str, milestones: Optional[List[float]]=None):
    """
        Initializes Augmentation Scheduler Callback properties.
        :param max_augment_prob: Maximum probability of augmentation.
        :param pct_time_increasing: Percentage of the time spent increasing.
        :param scheduling strategy: Strategy for scheduling the scaling of augmentor properties during training.
        :param milestones: List of milestones for scheduling augmentation. Eg, given [0.25, 0.5, 0.75, 1.0], we will increase the augmentation when 25%, 50%, 75% of the training has completed.
        """
    super().__init__(pct_time_increasing, scheduling_strategy, milestones)
    self.max_augment_prob = max_augment_prob
    assert 0.0 <= self.max_augment_prob <= 1.0, 'Error max augmentation probability must be between 0 and 1'

class StepwiseAugmentationAttributeScheduler(AbstractAugmentationScheduler):
    """Callback class that scales Noise parameters."""

    def __init__(self, max_aug_attribute_pct_increase: float, pct_time_increasing: float, scheduling_strategy: str, milestones: Optional[List[float]]=None):
        """
        Initializes Augmentation Scheduler Callback properties.
        :param max_aug_attribute_pct_increase: Percentage increase in augmentor attributes to be reached at end of training.
        :param pct_time_increasing: Percentage of the time spent increasing.
        :param scheduling strategy: Strategy for scheduling the scaling of augmentor attributes during training.
        :param milestones: List of milestones for scheduling augmentation. Eg, given [0.25, 0.5, 0.75, 1.0], we will increase the augmentation when 25%, 50%, 75% of the training has completed.
        """
        super().__init__(pct_time_increasing, scheduling_strategy, milestones)
        self.max_aug_attribute_pct_increase = max_aug_attribute_pct_increase

    def _scale_augmentor(self, augmentor: AbstractAugmentor, cur_step: int, total_steps: int) -> None:
        """
        Scales augmentor attributes.
        :param augmentor: Abstract augmentor.
        :param cur_step: Current training step.
        :param total_steps: Total number of training steps.
        """
        augmentor_name = type(augmentor).__name__
        if augmentor_name not in self._initial_augmentor_attributes:
            for param_to_scale in augmentor.get_schedulable_attributes:
                self._initial_augmentor_attributes[augmentor_name][param_to_scale.param_name] = param_to_scale
        for param_name, param_to_sale_obj in self._initial_augmentor_attributes[augmentor_name].items():
            scaled_attr = self._scale_augmentor_property(initial_attr=param_to_sale_obj, pct_increase=self.max_aug_attribute_pct_increase, cur_step=cur_step, total_steps=total_steps)
            setattr(augmentor._random_offset_generator, param_name, scaled_attr)

def __init__(self, max_aug_attribute_pct_increase: float, pct_time_increasing: float, scheduling_strategy: str, milestones: Optional[List[float]]=None):
    """
        Initializes Augmentation Scheduler Callback properties.
        :param max_aug_attribute_pct_increase: Percentage increase in augmentor attributes to be reached at end of training.
        :param pct_time_increasing: Percentage of the time spent increasing.
        :param scheduling strategy: Strategy for scheduling the scaling of augmentor attributes during training.
        :param milestones: List of milestones for scheduling augmentation. Eg, given [0.25, 0.5, 0.75, 1.0], we will increase the augmentation when 25%, 50%, 75% of the training has completed.
        """
    super().__init__(pct_time_increasing, scheduling_strategy, milestones)
    self.max_aug_attribute_pct_increase = max_aug_attribute_pct_increase

class ScenarioScoringCallback(pl.Callback):
    """
    Callback that performs an evaluation to score the model on each validation data.
    The n-best, n-worst and n-random data is written into a scene.

    The directory structure for the output of the scenes is:
        <output_dir>
            └── scenes
                ├── best
                │     ├── scenario_token_01
                │     │         ├── timestamp_01.json
                │     │         └── timestamp_02.json
                │     :                    :
                │     └── scenario_token_n
                ├── worst
                └── random
    """

    def __init__(self, scene_converter: SceneConverter, num_store: int, frequency: int, output_dir: Union[str, Path]):
        """
        Initialize the callback.
        :param scene_converter: Converts data from the scored scenario into scene dictionary.
        :param num_store: N number of scenarios to be written into scenes for each best, worst and random cases.
        :param frequency: Interval between epochs at which to perform the evaluation. Set 0 to skip the callback.
        :param output_dir: Output directory of scene file.
        """
        super().__init__()
        self._num_store = num_store
        self._frequency = frequency
        self._scene_converter = scene_converter
        self._output_dir = Path(output_dir) / 'scenes'
        self._val_dataloader: Optional[torch.utils.data.DataLoader] = None

    def _initialize_dataloaders(self, datamodule: pl.LightningDataModule) -> None:
        """
        Initialize the dataloaders. This makes sure that the same examples are sampled every time.
        :param datamodule: Lightning datamodule.
        """
        val_set = datamodule.val_dataloader().dataset
        assert isinstance(val_set, ScenarioDataset), 'invalid dataset type, dataset must be a scenario dataset'
        self._val_dataloader = torch.utils.data.DataLoader(dataset=val_set, batch_size=1, shuffle=False, collate_fn=FeatureCollate())

    def on_validation_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the end of each epoch validation.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        if self._frequency == 0:
            return
        assert hasattr(trainer, 'datamodule'), 'Trainer missing datamodule attribute'
        assert hasattr(trainer, 'current_epoch'), 'Trainer missing current_epoch attribute'
        epoch = trainer.current_epoch
        if epoch % self._frequency == 0:
            if self._val_dataloader is None:
                self._initialize_dataloaders(trainer.datamodule)
            output_dir = self._output_dir / f'epoch={epoch}'
            _eval_model_and_write_to_scene(self._val_dataloader, pl_module, self._scene_converter, self._num_store, output_dir)

def __init__(self, scene_converter: SceneConverter, num_store: int, frequency: int, output_dir: Union[str, Path]):
    """
        Initialize the callback.
        :param scene_converter: Converts data from the scored scenario into scene dictionary.
        :param num_store: N number of scenarios to be written into scenes for each best, worst and random cases.
        :param frequency: Interval between epochs at which to perform the evaluation. Set 0 to skip the callback.
        :param output_dir: Output directory of scene file.
        """
    super().__init__()
    self._num_store = num_store
    self._frequency = frequency
    self._scene_converter = scene_converter
    self._output_dir = Path(output_dir) / 'scenes'
    self._val_dataloader: Optional[torch.utils.data.DataLoader] = None

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

class tmp_module(torch.nn.Module):

    def __init__(self) -> None:
        super().__init__()

    def forward(self, coords: List[torch.Tensor], traffic_light_data: Optional[List[List[torch.Tensor]]], max_elements: int, max_points: int, traffic_light_encoding_dim: int, interpolation: Optional[str]) -> Tuple[torch.Tensor, Optional[torch.Tensor], torch.Tensor]:
        result_coords, result_tl_data, result_avails = convert_feature_layer_to_fixed_size(coords, traffic_light_data, max_elements, max_points, traffic_light_encoding_dim, interpolation)
        return (result_coords, result_tl_data, result_avails)

def __init__(self) -> None:
    super().__init__()

class GenericAgentsFeatureBuilder(ScriptableFeatureBuilder):
    """Builder for constructing agent features during training and simulation."""

    def __init__(self, agent_features: List[str], trajectory_sampling: TrajectorySampling) -> None:
        """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        """
        super().__init__()
        self.agent_features = agent_features
        self.num_past_poses = trajectory_sampling.num_poses
        self.past_time_horizon = trajectory_sampling.time_horizon
        self._agents_states_dim = GenericAgents.agents_states_dim()
        if 'EGO' in self.agent_features:
            raise AssertionError('EGO not valid agents feature type!')
        for feature_name in self.agent_features:
            if feature_name not in TrackedObjectType._member_names_:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'generic_agents'

    @torch.jit.unused
    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return GenericAgents

    @torch.jit.unused
    def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        anchor_ego_state = scenario.initial_ego_state
        past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
        sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
        time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
        present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
        past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
        sampled_past_observations = past_tracked_objects + [present_tracked_objects]
        assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
        assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_scriptable_input_from_simulation(self, current_input: PlannerInput) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the simulation input
        :param current_input: planner input from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        history = current_input.history
        assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
        present_ego_state, present_observation = history.current_state
        past_observations = history.observations[:-1]
        past_ego_states = history.ego_states[:-1]
        assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
        indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
        try:
            sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
            sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
        except IndexError:
            raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
        sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
        sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
        time_stamps = [state.time_point for state in sampled_past_ego_states]
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> GenericAgents:
        """Inherited, see superclass."""
        with torch.no_grad():
            tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_scenario(scenario)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> GenericAgents:
        """Inherited, see superclass."""
        with torch.no_grad():
            tensors, list_tensors, list_list_tensors = self.get_scriptable_input_from_simulation(current_input)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: GenericAgents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, past_ego_states: List[EgoState], past_time_stamps: List[TimePoint], past_tracked_objects: List[TrackedObjects]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Packs the provided objects into tensors to be used with the scriptable core of the builder.
        :param past_ego_states: The past states of the ego vehicle.
        :param past_time_stamps: The past time stamps of the input data.
        :param past_tracked_objects: The past tracked objects.
        :return: The packed tensors.
        """
        list_tensor_data: Dict[str, List[torch.Tensor]] = {}
        past_ego_states_tensor = sampled_past_ego_states_to_tensor(past_ego_states)
        past_time_stamps_tensor = sampled_past_timestamps_to_tensor(past_time_stamps)
        for feature_name in self.agent_features:
            past_tracked_objects_tensor_list = sampled_tracked_objects_to_tensor_list(past_tracked_objects, TrackedObjectType[feature_name])
            list_tensor_data[f'past_tracked_objects.{feature_name}'] = past_tracked_objects_tensor_list
        return ({'past_ego_states': past_ego_states_tensor, 'past_time_stamps': past_time_stamps_tensor}, list_tensor_data, {})

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> GenericAgents:
        """
        Unpacks the data returned from the scriptable core into an GenericAgents feature class.
        :param tensor_data: The tensor data output from the scriptable core.
        :param list_tensor_data: The List[tensor] data output from the scriptable core.
        :param list_tensor_data: The List[List[tensor]] data output from the scriptable core.
        :return: The packed GenericAgents object.
        """
        ego_features = [list_tensor_data['generic_agents.ego'][0].detach().numpy()]
        agent_features = {}
        for key in list_tensor_data:
            if key.startswith('generic_agents.agents.'):
                feature_name = key[len('generic_agents.agents.'):]
                agent_features[feature_name] = [list_tensor_data[key][0].detach().numpy()]
        return GenericAgents(ego=ego_features, agents=agent_features)

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Inherited. See interface.
        """
        output_dict: Dict[str, torch.Tensor] = {}
        output_list_dict: Dict[str, List[torch.Tensor]] = {}
        output_list_list_dict: Dict[str, List[List[torch.Tensor]]] = {}
        ego_history: torch.Tensor = tensor_data['past_ego_states']
        time_stamps: torch.Tensor = tensor_data['past_time_stamps']
        anchor_ego_state = ego_history[-1, :].squeeze()
        ego_tensor = build_generic_ego_features_from_tensor(ego_history, reverse=True)
        output_list_dict['generic_agents.ego'] = [ego_tensor]
        for feature_name in self.agent_features:
            if f'past_tracked_objects.{feature_name}' in list_tensor_data:
                agents: List[torch.Tensor] = list_tensor_data[f'past_tracked_objects.{feature_name}']
                agent_history = filter_agents_tensor(agents, reverse=True)
                if agent_history[-1].shape[0] == 0:
                    agents_tensor: torch.Tensor = torch.zeros((len(agent_history), 0, self._agents_states_dim)).float()
                else:
                    padded_agent_states = pad_agent_states(agent_history, reverse=True)
                    local_coords_agent_states = convert_absolute_quantities_to_relative(padded_agent_states, anchor_ego_state)
                    yaw_rate_horizon = compute_yaw_rate_from_state_tensors(padded_agent_states, time_stamps)
                    agents_tensor = pack_agents_tensor(local_coords_agent_states, yaw_rate_horizon)
                output_list_dict[f'generic_agents.agents.{feature_name}'] = [agents_tensor]
        return (output_dict, output_list_dict, output_list_list_dict)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Inherited. See interface.
        """
        return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses), 'agent_features': ','.join(self.agent_features)}}

def __init__(self, agent_features: List[str], trajectory_sampling: TrajectorySampling) -> None:
    """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        """
    super().__init__()
    self.agent_features = agent_features
    self.num_past_poses = trajectory_sampling.num_poses
    self.past_time_horizon = trajectory_sampling.time_horizon
    self._agents_states_dim = GenericAgents.agents_states_dim()
    if 'EGO' in self.agent_features:
        raise AssertionError('EGO not valid agents feature type!')
    for feature_name in self.agent_features:
        if feature_name not in TrackedObjectType._member_names_:
            raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')

class VectorMapFeatureBuilder(ScriptableFeatureBuilder):
    """
    Feature builder for constructing map features in a vector-representation.
    """

    def __init__(self, radius: float, connection_scales: Optional[List[int]]=None) -> None:
        """
        Initialize vector map builder with configuration parameters.
        :param radius:  The query radius scope relative to the current ego-pose.
        :param connection_scales: Connection scales to generate. Use the 1-hop connections if it's left empty.
        :return: Vector map data including lane segment coordinates and connections within the given range.
        """
        super().__init__()
        self._radius = radius
        self._connection_scales = connection_scales

    @torch.jit.unused
    def get_feature_type(self) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return VectorMap

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'vector_map'

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorMap:
        """Inherited, see superclass."""
        with torch.no_grad():
            ego_state = scenario.initial_ego_state
            ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
            lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(scenario.map_api, ego_coords, self._radius)
            on_route_status = get_on_route_status(scenario.get_route_roadblock_ids(), lane_seg_roadblock_ids)
            traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
            traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
            tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorMap:
        """Inherited, see superclass."""
        with torch.no_grad():
            ego_state = current_input.history.ego_states[-1]
            ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
            lane_seg_coords, lane_seg_conns, lane_seg_groupings, lane_seg_lane_ids, lane_seg_roadblock_ids = get_neighbor_vector_map(initialization.map_api, ego_coords, self._radius)
            on_route_status = get_on_route_status(initialization.route_roadblock_ids, lane_seg_roadblock_ids)
            if current_input.traffic_light_data is None:
                raise ValueError('Cannot build VectorMap feature. PlannerInput.traffic_light_data is None')
            traffic_light_data = current_input.traffic_light_data
            traffic_light_data = get_traffic_light_encoding(lane_seg_lane_ids, traffic_light_data)
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(lane_seg_coords, lane_seg_conns, lane_seg_groupings, on_route_status, traffic_light_data, ego_state.rear_axle)
            tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.ignore
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> VectorMap:
        """
        Unpacks the data returned from the scriptable portion of the method into a VectorMap object.
        :param tensor_data: The tensor data to unpack.
        :param list_tensor_data: The List[tensor] data to unpack.
        :param list_list_tensor_data: The List[List[tensor]] data to unpack.
        :return: The unpacked VectorMap.
        """
        multi_scale_connections: Dict[int, torch.Tensor] = {}
        for key in list_tensor_data:
            if key.startswith('vector_map.multi_scale_connections_'):
                multi_scale_connections[int(key[len('vector_map.multi_scale_connections_'):])] = list_tensor_data[key][0].detach().numpy()
        lane_groupings = [t.detach().numpy() for t in list_list_tensor_data['vector_map.lane_groupings'][0]]
        return VectorMap(coords=[list_tensor_data['vector_map.coords'][0].detach().numpy()], lane_groupings=[lane_groupings], multi_scale_connections=[multi_scale_connections], on_route_status=[list_tensor_data['vector_map.on_route_status'][0].detach().numpy()], traffic_light_data=[list_tensor_data['vector_map.traffic_light_data'][0].detach().numpy()])

    @torch.jit.ignore
    def _pack_to_feature_tensor_dict(self, lane_coords: LaneSegmentCoords, lane_conns: LaneSegmentConnections, lane_groupings: LaneSegmentGroupings, lane_on_route_status: LaneOnRouteStatusData, traffic_light_data: LaneSegmentTrafficLightData, anchor_state: StateSE2) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Transforms the provided map and actor state primitives into scriptable types.
        This is to prepare for the scriptable portion of the feature tranform.
        :param lane_coords: The LaneSegmentCoords returned from `get_neighbor_vector_map` to transform.
        :param lane_conns: The LaneSegmentConnections returned from `get_neighbor_vector_map` to transform.
        :param lane_groupings: The LaneSegmentGroupings returned from `get_neighbor_vector_map` to transform.
        :param lane_on_route_status: The LaneOnRouteStatusData returned from `get_neighbor_vector_map` to transform.
        :param traffic_light_data: The LaneSegmentTrafficLightData returned from `get_neighbor_vector_map` to transform.
        :param anchor_state: The ego state to transform to vector.
        """
        lane_segment_coords: torch.tensor = torch.tensor(lane_coords.to_vector(), dtype=torch.float64)
        lane_segment_conns: torch.tensor = torch.tensor(lane_conns.to_vector(), dtype=torch.int64)
        on_route_status: torch.tensor = torch.tensor(lane_on_route_status.to_vector(), dtype=torch.float32)
        traffic_light_array: torch.tensor = torch.tensor(traffic_light_data.to_vector(), dtype=torch.float32)
        lane_segment_groupings: List[torch.tensor] = []
        for lane_grouping in lane_groupings.to_vector():
            lane_segment_groupings.append(torch.tensor(lane_grouping, dtype=torch.int64))
        anchor_state_tensor = torch.tensor([anchor_state.x, anchor_state.y, anchor_state.heading], dtype=torch.float64)
        return ({'lane_segment_coords': lane_segment_coords, 'lane_segment_conns': lane_segment_conns, 'on_route_status': on_route_status, 'traffic_light_array': traffic_light_array, 'anchor_state': anchor_state_tensor}, {'lane_segment_groupings': lane_segment_groupings}, {})

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Implemented. See interface.
        """
        lane_segment_coords = tensor_data['lane_segment_coords']
        anchor_state = tensor_data['anchor_state']
        lane_segment_conns = tensor_data['lane_segment_conns']
        if len(lane_segment_conns.shape) == 1:
            if lane_segment_conns.shape[0] == 0:
                lane_segment_conns = torch.zeros((0, 2), device=lane_segment_coords.device, layout=lane_segment_coords.layout, dtype=torch.int64)
            else:
                raise ValueError(f'Unexpected shape for lane_segment_conns: {lane_segment_conns.shape}')
        lane_segment_coords = lane_segment_coords.reshape(-1, 2)
        lane_segment_coords = coordinates_to_local_frame(lane_segment_coords, anchor_state, precision=torch.float64)
        lane_segment_coords = lane_segment_coords.reshape(-1, 2, 2).float()
        if self._connection_scales is not None:
            multi_scale_connections = _generate_multi_scale_connections(lane_segment_conns, self._connection_scales)
        else:
            multi_scale_connections = {1: lane_segment_conns}
        list_list_tensor_output: Dict[str, List[List[torch.Tensor]]] = {'vector_map.lane_groupings': [list_tensor_data['lane_segment_groupings']]}
        list_tensor_output: Dict[str, List[torch.Tensor]] = {'vector_map.coords': [lane_segment_coords], 'vector_map.on_route_status': [tensor_data['on_route_status']], 'vector_map.traffic_light_data': [tensor_data['traffic_light_array']]}
        for key in multi_scale_connections:
            list_tensor_output[f'vector_map.multi_scale_connections_{key}'] = [multi_scale_connections[key]]
        tensor_output: Dict[str, torch.Tensor] = {}
        return (tensor_output, list_tensor_output, list_list_tensor_output)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Implemented. See Interface.
        """
        empty: Dict[str, str] = {}
        return {'neighbor_vector_map': {'radius': str(self._radius)}, 'initial_ego_state': empty}

def __init__(self, radius: float, connection_scales: Optional[List[int]]=None) -> None:
    """
        Initialize vector map builder with configuration parameters.
        :param radius:  The query radius scope relative to the current ego-pose.
        :param connection_scales: Connection scales to generate. Use the 1-hop connections if it's left empty.
        :return: Vector map data including lane segment coordinates and connections within the given range.
        """
    super().__init__()
    self._radius = radius
    self._connection_scales = connection_scales

class VectorSetMapFeatureBuilder(ScriptableFeatureBuilder):
    """
    Feature builder for constructing map features in a vector set representation, similar to that of
        VectorNet ("VectorNet: Encoding HD Maps and Agent Dynamics from Vectorized Representation").
    """

    def __init__(self, map_features: List[str], max_elements: Dict[str, int], max_points: Dict[str, int], radius: float, interpolation_method: str) -> None:
        """
        Initialize vector set map builder with configuration parameters.
        :param map_features: name of map features to be extracted.
        :param max_elements: maximum number of elements to extract per feature layer.
        :param max_points: maximum number of points per feature to extract per feature layer.
        :param radius:  [m ]The query radius scope relative to the current ego-pose.
        :param interpolation_method: Interpolation method to apply when interpolating to maintain fixed size
            map elements.
        :return: Vector set map data including map element coordinates and traffic light status info.
        """
        super().__init__()
        self.map_features = map_features
        self.max_elements = max_elements
        self.max_points = max_points
        self.radius = radius
        self.interpolation_method = interpolation_method
        self._traffic_light_encoding_dim = LaneSegmentTrafficLightData.encoding_dim()
        for feature_name in self.map_features:
            try:
                VectorFeatureLayer[feature_name]
            except KeyError:
                raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
            if feature_name not in self.max_elements:
                raise RuntimeError(f'Max elements unavailable for {feature_name} feature layer!')
            if feature_name not in self.max_points:
                raise RuntimeError(f'Max points unavailable for {feature_name} feature layer!')

    @torch.jit.unused
    def get_feature_type(self) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return VectorSetMap

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'vector_set_map'

    @torch.jit.unused
    def get_scriptable_input_from_scenario(self, scenario: AbstractScenario) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the scenario object
        :param scenario: planner input from training
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        ego_state = scenario.initial_ego_state
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        route_roadblock_ids = scenario.get_route_roadblock_ids()
        traffic_light_data = list(scenario.get_traffic_light_status_at_iteration(0))
        coords, traffic_light_data = get_neighbor_vector_set_map(scenario.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_scriptable_input_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Extract the input for the scriptable forward method from the simulation objects
        :param current_input: planner input from sim
        :param initialization: planner initialization from sim
        :returns: Tensor data + tensor list data to be used in scriptable forward
        """
        ego_state = current_input.history.ego_states[-1]
        ego_coords = Point2D(ego_state.rear_axle.x, ego_state.rear_axle.y)
        route_roadblock_ids = initialization.route_roadblock_ids
        if current_input.traffic_light_data is None:
            raise ValueError('Cannot build VectorSetMap feature. PlannerInput.traffic_light_data is None')
        traffic_light_data = current_input.traffic_light_data
        coords, traffic_light_data = get_neighbor_vector_set_map(initialization.map_api, self.map_features, ego_coords, self.radius, route_roadblock_ids, [TrafficLightStatuses(traffic_light_data)])
        tensor, list_tensor, list_list_tensor = self._pack_to_feature_tensor_dict(coords, traffic_light_data[0], ego_state.rear_axle)
        return (tensor, list_tensor, list_list_tensor)

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> VectorSetMap:
        """Inherited, see superclass."""
        tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_scenario(scenario)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> VectorSetMap:
        """Inherited, see superclass."""
        tensor_data, list_tensor_data, list_list_tensor_data = self.get_scriptable_input_from_simulation(current_input, initialization)
        tensor_data, list_tensor_data, list_list_tensor_data = self.scriptable_forward(tensor_data, list_tensor_data, list_list_tensor_data)
        return self._unpack_feature_from_tensor_dict(tensor_data, list_tensor_data, list_list_tensor_data)

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> VectorSetMap:
        """
        Unpacks the data returned from the scriptable portion of the method into a VectorSetMap object.
        :param tensor_data: The tensor data to unpack.
        :param list_tensor_data: The List[tensor] data to unpack.
        :param list_list_tensor_data: The List[List[tensor]] data to unpack.
        :return: The unpacked VectorSetMap.
        """
        coords: Dict[str, List[FeatureDataType]] = {}
        traffic_light_data: Dict[str, List[FeatureDataType]] = {}
        availabilities: Dict[str, List[FeatureDataType]] = {}
        for key in list_tensor_data:
            if key.startswith('vector_set_map.coords.'):
                feature_name = key[len('vector_set_map.coords.'):]
                coords[feature_name] = [list_tensor_data[key][0].detach().numpy()]
            if key.startswith('vector_set_map.traffic_light_data.'):
                feature_name = key[len('vector_set_map.traffic_light_data.'):]
                traffic_light_data[feature_name] = [list_tensor_data[key][0].detach().numpy()]
            if key.startswith('vector_set_map.availabilities.'):
                feature_name = key[len('vector_set_map.availabilities.'):]
                availabilities[feature_name] = [list_tensor_data[key][0].detach().numpy()]
        return VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, coords: Dict[str, MapObjectPolylines], traffic_light_data: Dict[str, LaneSegmentTrafficLightData], anchor_state: StateSE2) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Transforms the provided map and actor state primitives into scriptable types.
        This is to prepare for the scriptable portion of the feature transform.
        :param coords: Dictionary mapping feature name to polyline vector sets.
        :param traffic_light_data: Dictionary mapping feature name to traffic light info corresponding to map elements
            in coords.
        :param anchor_state: The ego state to transform to vector.
        :return
           tensor_data: Packed tensor data.
           list_tensor_data: Packed List[tensor] data.
           list_list_tensor_data: Packed List[List[tensor]] data.
        """
        tensor_data: Dict[str, torch.Tensor] = {}
        anchor_state_tensor = torch.tensor([anchor_state.x, anchor_state.y, anchor_state.heading], dtype=torch.float64)
        tensor_data['anchor_state'] = anchor_state_tensor
        list_tensor_data: Dict[str, List[torch.Tensor]] = {}
        for feature_name, feature_coords in coords.items():
            list_feature_coords: List[torch.Tensor] = []
            for element_coords in feature_coords.to_vector():
                list_feature_coords.append(torch.tensor(element_coords, dtype=torch.float64))
            list_tensor_data[f'coords.{feature_name}'] = list_feature_coords
            if feature_name in traffic_light_data:
                list_feature_tl_data: List[torch.Tensor] = []
                for element_tl_data in traffic_light_data[feature_name].to_vector():
                    list_feature_tl_data.append(torch.tensor(element_tl_data, dtype=torch.float32))
                list_tensor_data[f'traffic_light_data.{feature_name}'] = list_feature_tl_data
        return (tensor_data, list_tensor_data, {})

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Implemented. See interface.
        """
        tensor_output: Dict[str, torch.Tensor] = {}
        list_tensor_output: Dict[str, List[torch.Tensor]] = {}
        list_list_tensor_output: Dict[str, List[List[torch.Tensor]]] = {}
        anchor_state = tensor_data['anchor_state']
        for feature_name in self.map_features:
            if f'coords.{feature_name}' in list_tensor_data:
                feature_coords = list_tensor_data[f'coords.{feature_name}']
                feature_tl_data = [list_tensor_data[f'traffic_light_data.{feature_name}']] if f'traffic_light_data.{feature_name}' in list_tensor_data else None
                coords, tl_data, avails = convert_feature_layer_to_fixed_size(feature_coords, feature_tl_data, self.max_elements[feature_name], self.max_points[feature_name], self._traffic_light_encoding_dim, interpolation=self.interpolation_method if feature_name in [VectorFeatureLayer.LANE.name, VectorFeatureLayer.LEFT_BOUNDARY.name, VectorFeatureLayer.RIGHT_BOUNDARY.name, VectorFeatureLayer.ROUTE_LANES.name] else None)
                coords = vector_set_coordinates_to_local_frame(coords, avails, anchor_state)
                list_tensor_output[f'vector_set_map.coords.{feature_name}'] = [coords]
                list_tensor_output[f'vector_set_map.availabilities.{feature_name}'] = [avails]
                if tl_data is not None:
                    list_tensor_output[f'vector_set_map.traffic_light_data.{feature_name}'] = [tl_data[0]]
        return (tensor_output, list_tensor_output, list_list_tensor_output)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Implemented. See Interface.
        """
        empty: Dict[str, str] = {}
        max_elements: List[str] = [f'{feature_name}.{feature_max_elements}' for feature_name, feature_max_elements in self.max_elements.items()]
        max_points: List[str] = [f'{feature_name}.{feature_max_points}' for feature_name, feature_max_points in self.max_points.items()]
        return {'neighbor_vector_set_map': {'radius': str(self.radius), 'interpolation_method': self.interpolation_method, 'map_features': ','.join(self.map_features), 'max_elements': ','.join(max_elements), 'max_points': ','.join(max_points)}, 'initial_ego_state': empty}

def __init__(self, map_features: List[str], max_elements: Dict[str, int], max_points: Dict[str, int], radius: float, interpolation_method: str) -> None:
    """
        Initialize vector set map builder with configuration parameters.
        :param map_features: name of map features to be extracted.
        :param max_elements: maximum number of elements to extract per feature layer.
        :param max_points: maximum number of points per feature to extract per feature layer.
        :param radius:  [m ]The query radius scope relative to the current ego-pose.
        :param interpolation_method: Interpolation method to apply when interpolating to maintain fixed size
            map elements.
        :return: Vector set map data including map element coordinates and traffic light status info.
        """
    super().__init__()
    self.map_features = map_features
    self.max_elements = max_elements
    self.max_points = max_points
    self.radius = radius
    self.interpolation_method = interpolation_method
    self._traffic_light_encoding_dim = LaneSegmentTrafficLightData.encoding_dim()
    for feature_name in self.map_features:
        try:
            VectorFeatureLayer[feature_name]
        except KeyError:
            raise ValueError(f'Object representation for layer: {feature_name} is unavailable!')
        if feature_name not in self.max_elements:
            raise RuntimeError(f'Max elements unavailable for {feature_name} feature layer!')
        if feature_name not in self.max_points:
            raise RuntimeError(f'Max points unavailable for {feature_name} feature layer!')

class AgentsFeatureBuilder(ScriptableFeatureBuilder):
    """Builder for constructing agent features during training and simulation."""

    def __init__(self, trajectory_sampling: TrajectorySampling, object_type: TrackedObjectType=TrackedObjectType.VEHICLE) -> None:
        """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        :param object_type: Type of agents (TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN) set to TrackedObjectType.VEHICLE by default
        """
        super().__init__()
        if object_type not in [TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]:
            raise ValueError(f"The model's been tested just for vehicles and pedestrians types, but the provided object_type is {object_type}.")
        self.num_past_poses = trajectory_sampling.num_poses
        self.past_time_horizon = trajectory_sampling.time_horizon
        self.object_type = object_type
        self._agents_states_dim = Agents.agents_states_dim()

    @torch.jit.unused
    @classmethod
    def get_feature_unique_name(cls) -> str:
        """Inherited, see superclass."""
        return 'agents'

    @torch.jit.unused
    @classmethod
    def get_feature_type(cls) -> Type[AbstractModelFeature]:
        """Inherited, see superclass."""
        return Agents

    @torch.jit.unused
    def get_features_from_scenario(self, scenario: AbstractScenario) -> Agents:
        """Inherited, see superclass."""
        with torch.no_grad():
            anchor_ego_state = scenario.initial_ego_state
            past_ego_states = scenario.get_ego_past_trajectory(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)
            sampled_past_ego_states = list(past_ego_states) + [anchor_ego_state]
            time_stamps = list(scenario.get_past_timestamps(iteration=0, num_samples=self.num_past_poses, time_horizon=self.past_time_horizon)) + [scenario.start_time]
            present_tracked_objects = scenario.initial_tracked_objects.tracked_objects
            past_tracked_objects = [tracked_objects.tracked_objects for tracked_objects in scenario.get_past_tracked_objects(iteration=0, time_horizon=self.past_time_horizon, num_samples=self.num_past_poses)]
            sampled_past_observations = past_tracked_objects + [present_tracked_objects]
            assert len(sampled_past_ego_states) == len(sampled_past_observations), f'Expected the trajectory length of ego and agent to be equal. Got ego: {len(sampled_past_ego_states)} and agent: {len(sampled_past_observations)}'
            assert len(sampled_past_observations) > 2, f'Trajectory of length of {len(sampled_past_observations)} needs to be at least 3'
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def get_features_from_simulation(self, current_input: PlannerInput, initialization: PlannerInitialization) -> Agents:
        """Inherited, see superclass."""
        with torch.no_grad():
            history = current_input.history
            assert isinstance(history.observations[0], DetectionsTracks), f'Expected observation of type DetectionTracks, got {type(history.observations[0])}'
            present_ego_state, present_observation = history.current_state
            past_observations = history.observations[:-1]
            past_ego_states = history.ego_states[:-1]
            assert history.sample_interval, 'SimulationHistoryBuffer sample interval is None'
            indices = sample_indices_with_time_horizon(self.num_past_poses, self.past_time_horizon, history.sample_interval)
            try:
                sampled_past_observations = [cast(DetectionsTracks, past_observations[-idx]).tracked_objects for idx in reversed(indices)]
                sampled_past_ego_states = [past_ego_states[-idx] for idx in reversed(indices)]
            except IndexError:
                raise RuntimeError(f'SimulationHistoryBuffer duration: {history.duration} is too short for requested past_time_horizon: {self.past_time_horizon}. Please increase the simulation_buffer_duration in default_simulation.yaml')
            sampled_past_observations = sampled_past_observations + [cast(DetectionsTracks, present_observation).tracked_objects]
            sampled_past_ego_states = sampled_past_ego_states + [present_ego_state]
            time_stamps = [state.time_point for state in sampled_past_ego_states]
            tensors, list_tensors, list_list_tensors = self._pack_to_feature_tensor_dict(sampled_past_ego_states, time_stamps, sampled_past_observations)
            tensors, list_tensors, list_list_tensors = self.scriptable_forward(tensors, list_tensors, list_list_tensors)
            output: Agents = self._unpack_feature_from_tensor_dict(tensors, list_tensors, list_list_tensors)
            return output

    @torch.jit.unused
    def _pack_to_feature_tensor_dict(self, past_ego_states: List[EgoState], past_time_stamps: List[TimePoint], past_tracked_objects: List[TrackedObjects]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Packs the provided objects into tensors to be used with the scriptable core of the builder.
        :param past_ego_states: The past states of the ego vehicle.
        :param past_time_stamps: The past time stamps of the input data.
        :param past_tracked_objects: The past tracked objects.
        :return: The packed tensors.
        """
        past_ego_states_tensor = sampled_past_ego_states_to_tensor(past_ego_states)
        past_time_stamps_tensor = sampled_past_timestamps_to_tensor(past_time_stamps)
        past_tracked_objects_tensor_list = sampled_tracked_objects_to_tensor_list(past_tracked_objects=past_tracked_objects, object_type=self.object_type)
        return ({'past_ego_states': past_ego_states_tensor, 'past_time_stamps': past_time_stamps_tensor}, {'past_tracked_objects': past_tracked_objects_tensor_list}, {})

    @torch.jit.unused
    def _unpack_feature_from_tensor_dict(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Agents:
        """
        Unpacks the data returned from the scriptable core into an Agents feature class.
        :param tensor_data: The tensor data output from the scriptable core.
        :param list_tensor_data: The List[tensor] data output from the scriptable core.
        :param list_tensor_data: The List[List[tensor]] data output from the scriptable core.
        :return: The packed Agents object.
        """
        ego_features = [list_tensor_data['agents.ego'][0].detach().numpy()]
        agent_features = [list_tensor_data['agents.agents'][0].detach().numpy()]
        return Agents(ego=ego_features, agents=agent_features)

    @torch.jit.export
    def scriptable_forward(self, tensor_data: Dict[str, torch.Tensor], list_tensor_data: Dict[str, List[torch.Tensor]], list_list_tensor_data: Dict[str, List[List[torch.Tensor]]]) -> Tuple[Dict[str, torch.Tensor], Dict[str, List[torch.Tensor]], Dict[str, List[List[torch.Tensor]]]]:
        """
        Inherited. See interface.
        """
        ego_history: torch.Tensor = tensor_data['past_ego_states']
        time_stamps: torch.Tensor = tensor_data['past_time_stamps']
        agents: List[torch.Tensor] = list_tensor_data['past_tracked_objects']
        anchor_ego_state = ego_history[-1, :].squeeze()
        agent_history = filter_agents_tensor(agents, reverse=True)
        if agent_history[-1].shape[0] == 0:
            agents_tensor: torch.Tensor = torch.zeros((len(agent_history), 0, self._agents_states_dim)).float()
        else:
            padded_agent_states = pad_agent_states(agent_history, reverse=True)
            local_coords_agent_states = convert_absolute_quantities_to_relative(padded_agent_states, anchor_ego_state)
            yaw_rate_horizon = compute_yaw_rate_from_state_tensors(padded_agent_states, time_stamps)
            agents_tensor = pack_agents_tensor(local_coords_agent_states, yaw_rate_horizon)
        ego_tensor = build_ego_features_from_tensor(ego_history, reverse=True)
        output_dict: Dict[str, torch.Tensor] = {}
        output_list_dict: Dict[str, List[torch.Tensor]] = {'agents.ego': [ego_tensor], 'agents.agents': [agents_tensor]}
        output_list_list_dict: Dict[str, List[List[torch.Tensor]]] = {}
        return (output_dict, output_list_dict, output_list_list_dict)

    @torch.jit.export
    def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
        """
        Inherited. See interface.
        """
        return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses)}}

def __init__(self, trajectory_sampling: TrajectorySampling, object_type: TrackedObjectType=TrackedObjectType.VEHICLE) -> None:
    """
        Initializes AgentsFeatureBuilder.
        :param trajectory_sampling: Parameters of the sampled trajectory of every agent
        :param object_type: Type of agents (TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN) set to TrackedObjectType.VEHICLE by default
        """
    super().__init__()
    if object_type not in [TrackedObjectType.VEHICLE, TrackedObjectType.PEDESTRIAN]:
        raise ValueError(f"The model's been tested just for vehicles and pedestrians types, but the provided object_type is {object_type}.")
    self.num_past_poses = trajectory_sampling.num_poses
    self.past_time_horizon = trajectory_sampling.time_horizon
    self.object_type = object_type
    self._agents_states_dim = Agents.agents_states_dim()

class MockTorchModuleWrapperTrajectoryPredictor(TorchModuleWrapper):
    """
    A simple implementation of the TorchModuleWrapper interface for use with unit tests.
    It validates the input tensor, and returns a trajectory object.
    """

    def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], raise_on_builder_access: bool=False, raise_on_forward: bool=False, expected_forward_tensor: Optional[torch.Tensor]=None, data_tensor_to_return: Optional[torch.Tensor]=None) -> None:
        """
        The init method.
        :param future_trajectory_sampling: The TrajectorySampling to use.
        :param feature_builders: The feature builders used by the model.
        :param target_builders: The target builders used by the model.
        :param raise_on_builder_access: If set, an exeption will be raised if the builders are accessed.
        :param raise_on_forward: If set, an exception will be raised if the forward function is called.
        :param expected_forward_tensor: The tensor that is expected to be provided to to the forward function.
        :param data_tensor_to_return: The tensor that expected to be returned from the forward function.
        """
        super().__init__(future_trajectory_sampling, feature_builders, target_builders)
        self.raise_on_builder_access = raise_on_builder_access
        self.raise_on_forward = raise_on_forward
        self.expected_forward_tensor = expected_forward_tensor
        self.data_tensor_to_return = data_tensor_to_return
        if not self.raise_on_builder_access:
            if self.feature_builders is None or len(self.feature_builders) == 0:
                raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length feature builders.\n                    This is likely a misconfigured unit test.\n                    '))
            if self.target_builders is None or len(self.target_builders) == 0:
                raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length target builders.\n                    This is likely a misconfigured unit test.\n                    '))
        if not self.raise_on_forward:
            if self.expected_forward_tensor is None:
                raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None expected_forward_tensor.\n                    This is likely a misconfigured unit test.\n                    '))
            if self.data_tensor_to_return is None:
                raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None data_tensor_to_return.\n                    This is likely a misconfigured unit test.\n                    '))

    def get_list_of_required_feature(self) -> List[AbstractFeatureBuilder]:
        """
        Implemented. See interface.
        """
        if self.raise_on_builder_access:
            raise ValueError('get_list_of_required_feature() called when raise_on_builder_access set.')
        result: List[AbstractFeatureBuilder] = TorchModuleWrapper.get_list_of_required_feature(self)
        return result

    def get_list_of_computed_target(self) -> List[AbstractTargetBuilder]:
        """
        Implemented. See interface.
        """
        if self.raise_on_builder_access:
            raise ValueError('get_list_of_computed_target() called when raise_on_builder_access set.')
        result: List[AbstractTargetBuilder] = TorchModuleWrapper.get_list_of_computed_target(self)
        return result

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Implemented. See interface.
        """
        if self.raise_on_forward:
            raise ValueError('forward() called when raise_on_forward set.')
        self._validate_input_feature(features)
        return {'trajectory': Trajectory(data=self.data_tensor_to_return)}

    def _validate_input_feature(self, features: FeaturesType) -> None:
        """
        Validates that the proper feature is provided.
        Raises an exception if it is not.
        :param features: The feature provided to the model.
        """
        if 'MockFeature' not in features:
            raise ValueError(f'MockFeature not in provided features. Available keys: {sorted(list(features.keys()))}')
        if len(features) != 1:
            raise ValueError(f'Expected a single feature. Instead got {len(features)}: {sorted(list(features.keys()))}')
        mock_feature = features['MockFeature']
        if not isinstance(mock_feature, MockFeature):
            raise ValueError(f'Expected feature of type MockFeature, but got {type(mock_feature)}')
        mock_feature_data = mock_feature.data
        torch.testing.assert_close(mock_feature_data, self.expected_forward_tensor)

def __init__(self, future_trajectory_sampling: TrajectorySampling, feature_builders: List[AbstractFeatureBuilder], target_builders: List[AbstractTargetBuilder], raise_on_builder_access: bool=False, raise_on_forward: bool=False, expected_forward_tensor: Optional[torch.Tensor]=None, data_tensor_to_return: Optional[torch.Tensor]=None) -> None:
    """
        The init method.
        :param future_trajectory_sampling: The TrajectorySampling to use.
        :param feature_builders: The feature builders used by the model.
        :param target_builders: The target builders used by the model.
        :param raise_on_builder_access: If set, an exeption will be raised if the builders are accessed.
        :param raise_on_forward: If set, an exception will be raised if the forward function is called.
        :param expected_forward_tensor: The tensor that is expected to be provided to to the forward function.
        :param data_tensor_to_return: The tensor that expected to be returned from the forward function.
        """
    super().__init__(future_trajectory_sampling, feature_builders, target_builders)
    self.raise_on_builder_access = raise_on_builder_access
    self.raise_on_forward = raise_on_forward
    self.expected_forward_tensor = expected_forward_tensor
    self.data_tensor_to_return = data_tensor_to_return
    if not self.raise_on_builder_access:
        if self.feature_builders is None or len(self.feature_builders) == 0:
            raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length feature builders.\n                    This is likely a misconfigured unit test.\n                    '))
        if self.target_builders is None or len(self.target_builders) == 0:
            raise ValueError(textwrap.dedent('\n                    raise_on_builder_access set to False with None or 0-length target builders.\n                    This is likely a misconfigured unit test.\n                    '))
    if not self.raise_on_forward:
        if self.expected_forward_tensor is None:
            raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None expected_forward_tensor.\n                    This is likely a misconfigured unit test.\n                    '))
        if self.data_tensor_to_return is None:
            raise ValueError(textwrap.dedent('\n                    raise_on_forward set to false with None data_tensor_to_return.\n                    This is likely a misconfigured unit test.\n                    '))

@dataclass
class AgentStatePlot(BaseScenarioPlot):
    """A dataclass for agent state plot."""
    data_sources: Dict[int, Dict[str, ColumnDataSource]] = field(default_factory=dict)
    plots: Dict[str, GlyphRenderer] = field(default_factory=dict)
    track_id_history: Optional[Dict[str, int]] = None

    def __post_init__(self) -> None:
        """Initialize track id history."""
        super().__post_init__()
        if not self.track_id_history:
            self.track_id_history = {}

    def _get_track_id(self, track_id: str) -> Union[int, float]:
        """
        Get a number representation for track ids.
        :param track_id: Agent track id.
        :return A number representation for a track id.
        """
        if track_id == 'null' or not self.track_id_history:
            return np.nan
        number_track_id = self.track_id_history.get(track_id, None)
        if not number_track_id:
            self.track_id_history[track_id] = len(self.track_id_history)
            number_track_id = len(self.track_id_history)
        return number_track_id

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

            def update_main_figure() -> None:
                """Wrapper for the main_figure update logic to support multi-threading."""
                data_sources = self.data_sources.get(frame_index, None)
                if not data_sources:
                    return
                for category, data_source in data_sources.items():
                    plot = self.plots.get(category, None)
                    data = dict(data_source.data)
                    if plot is None:
                        agent_color = simulation_tile_agent_style.get(category)
                        self.plots[category] = main_figure.multi_polygons(xs='xs', ys='ys', fill_color=agent_color['fill_color'], fill_alpha=agent_color['fill_alpha'], line_color=agent_color['line_color'], line_width=agent_color['line_width'], source=data)
                        agent_hover = HoverTool(renderers=[self.plots[category]], tooltips=[('center_x [m]', '@center_xs{0.2f}'), ('center_y [m]', '@center_ys{0.2f}'), ('velocity_x [m/s]', '@velocity_xs{0.2f}'), ('velocity_y [m/s]', '@velocity_ys{0.2f}'), ('speed [m/s]', '@speeds{0.2f}'), ('heading [rad]', '@headings{0.2f}'), ('type', '@agent_type'), ('track token', '@track_token')])
                        main_figure.add_tools(agent_hover)
                    else:
                        self.plots[category].data_source.data = data
                self.render_event.clear()
            doc.add_next_tick_callback(lambda: update_main_figure())

    def update_data_sources(self, history: SimulationHistory) -> None:
        """
        Update agents data sources.
        :param history: SimulationHistory time-series data.
        """
        if not self.data_source_condition:
            return
        with self.data_source_condition:
            for frame_index, sample in enumerate(history.data):
                if not isinstance(sample.observation, DetectionsTracks):
                    continue
                tracked_objects = sample.observation.tracked_objects
                frame_dict = {}
                for tracked_object_type_name, tracked_object_type in tracked_object_types.items():
                    corner_xs = []
                    corner_ys = []
                    track_ids = []
                    track_tokens = []
                    agent_types = []
                    center_xs = []
                    center_ys = []
                    velocity_xs = []
                    velocity_ys = []
                    speeds = []
                    headings = []
                    for tracked_object in tracked_objects.get_tracked_objects_of_type(tracked_object_type):
                        agent_corners = tracked_object.box.all_corners()
                        corners_x = [corner.x for corner in agent_corners]
                        corners_y = [corner.y for corner in agent_corners]
                        corners_x.append(corners_x[0])
                        corners_y.append(corners_y[0])
                        corner_xs.append([[corners_x]])
                        corner_ys.append([[corners_y]])
                        center_xs.append(tracked_object.center.x)
                        center_ys.append(tracked_object.center.y)
                        velocity_xs.append(tracked_object.velocity.x)
                        velocity_ys.append(tracked_object.velocity.y)
                        speeds.append(tracked_object.velocity.magnitude())
                        headings.append(tracked_object.center.heading)
                        agent_types.append(tracked_object_type.fullname)
                        track_ids.append(self._get_track_id(tracked_object.track_token))
                        track_tokens.append(tracked_object.track_token)
                    agent_states = BokehAgentStates(xs=corner_xs, ys=corner_ys, track_id=track_ids, track_token=track_tokens, agent_type=agent_types, center_xs=center_xs, center_ys=center_ys, velocity_xs=velocity_xs, velocity_ys=velocity_ys, speeds=speeds, headings=headings)
                    frame_dict[tracked_object_type_name] = ColumnDataSource(agent_states._asdict())
                self.data_sources[frame_index] = frame_dict
                self.data_source_condition.notify()

def __post_init__(self) -> None:
    """Initialize track id history."""
    super().__post_init__()
    if not self.track_id_history:
        self.track_id_history = {}

class TestOverviewTab(SkeletonTestTab):
    """Test nuboard overview tab functionality."""

    def setUp(self) -> None:
        """Set up an overview tab."""
        super().setUp()
        self.overview_tab = OverviewTab(experiment_file_data=self.experiment_file_data, doc=self.doc)

    def test_update_table(self) -> None:
        """Test update table function."""
        self.overview_tab._overview_on_change()

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change function."""
        new_experiment_file_data = ExperimentFileData(file_paths=[])
        self.overview_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])

def setUp(self) -> None:
    """Set up an overview tab."""
    super().setUp()
    self.overview_tab = OverviewTab(experiment_file_data=self.experiment_file_data, doc=self.doc)

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

def setUp(self) -> None:
    """Set up a histogram tab."""
    super().setUp()
    self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)

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

def __init__(self, name: str, category: str) -> None:
    """
        Initializes the WithinBoundMetricBase class
        :param name: Metric name
        :param category: Metric category.
        """
    super().__init__(name=name, category=category)
    self.within_bound_status: Optional[bool] = False

class EgoLatJerkStatistics(WithinBoundMetricBase):
    """Ego lateral jerk metric."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the EgoLatJerkStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lateral jerk  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'y'})
        return metric_statistics

def __init__(self, name: str, category: str) -> None:
    """
        Initializes the EgoLatJerkStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
    super().__init__(name=name, category=category)

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

class EgoAccelerationStatistics(WithinBoundMetricBase):
    """Ego acceleration metric."""

    def __init__(self, name: str, category: str) -> None:
        """
        Initializes the EgoAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
        super().__init__(name=name, category=category)

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the estimated metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'magnitude'})
        return metric_statistics

def __init__(self, name: str, category: str) -> None:
    """
        Initializes the EgoAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
    super().__init__(name=name, category=category)

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

class EgoJerkStatistics(WithinBoundMetricBase):
    """Ego jerk metric."""

    def __init__(self, name: str, category: str, max_abs_mag_jerk: float) -> None:
        """
        Initializes the EgoProgressAlongExpertRouteStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_mag_jerk: Maximum threshold to define if absolute jerk is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_mag_jerk = max_abs_mag_jerk

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'magnitude'}, min_within_bound_threshold=-self._max_abs_mag_jerk, max_within_bound_threshold=self._max_abs_mag_jerk)
        return metric_statistics

def __init__(self, name: str, category: str, max_abs_mag_jerk: float) -> None:
    """
        Initializes the EgoProgressAlongExpertRouteStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_mag_jerk: Maximum threshold to define if absolute jerk is within bound.
        """
    super().__init__(name=name, category=category)
    self._max_abs_mag_jerk = max_abs_mag_jerk

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

class EgoLatAccelerationStatistics(WithinBoundMetricBase):
    """Ego lateral acceleration metric."""

    def __init__(self, name: str, category: str, max_abs_lat_accel: float) -> None:
        """
        Initializes the EgoLatAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lat_accel: Maximum threshold to define if absolute lateral acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_lat_accel = max_abs_lat_accel

    @staticmethod
    def compute_comfortability(history: SimulationHistory, max_abs_lat_accel: float) -> bool:
        """
        Compute comfortability based on max_abs_lat_accel
        :param history: History from a simulation engine
        :param max_abs_lat_accel: Threshold for the absolute lat jerk
        :return True if within the threshold otherwise false.
        """
        ego_pose_states = history.extract_ego_state
        ego_pose_lat_accels = extract_ego_acceleration(ego_pose_states, acceleration_coordinate='y')
        lat_accels_within_bounds = np.abs(ego_pose_lat_accels) < max_abs_lat_accel
        return bool(np.all(lat_accels_within_bounds))

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the lateral acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated lateral acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'y'}, min_within_bound_threshold=-self._max_abs_lat_accel, max_within_bound_threshold=self._max_abs_lat_accel)
        return metric_statistics

def __init__(self, name: str, category: str, max_abs_lat_accel: float) -> None:
    """
        Initializes the EgoLatAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lat_accel: Maximum threshold to define if absolute lateral acceleration is within bound.
        """
    super().__init__(name=name, category=category)
    self._max_abs_lat_accel = max_abs_lat_accel

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

class EgoLonAccelerationStatistics(WithinBoundMetricBase):
    """Ego longitudinal acceleration metric."""

    def __init__(self, name: str, category: str, min_lon_accel: float, max_lon_accel: float) -> None:
        """
        Initializes the EgoLonAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param min_lon_accel: Threshold to define if the lon acceleration is within bound
        :param max_lon_accel: Threshold to define if the lat acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._min_lon_accel = min_lon_accel
        self._max_lon_accel = max_lon_accel

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the longitudinal acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_squared', extract_function=extract_ego_acceleration, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=self._min_lon_accel, max_within_bound_threshold=self._max_lon_accel)
        return metric_statistics

def __init__(self, name: str, category: str, min_lon_accel: float, max_lon_accel: float) -> None:
    """
        Initializes the EgoLonAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param min_lon_accel: Threshold to define if the lon acceleration is within bound
        :param max_lon_accel: Threshold to define if the lat acceleration is within bound.
        """
    super().__init__(name=name, category=category)
    self._min_lon_accel = min_lon_accel
    self._max_lon_accel = max_lon_accel

class EgoYawAccelerationStatistics(WithinBoundMetricBase):
    """Ego yaw acceleration metric."""

    def __init__(self, name: str, category: str, max_abs_yaw_accel: float) -> None:
        """
        Initializes the EgoYawAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_accel: Maximum threshold to define if absolute yaw acceleration is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_yaw_accel = max_abs_yaw_accel

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the yaw acceleration metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw acceleration metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second_squared', extract_function=extract_ego_yaw_rate, extract_function_params={'deriv_order': 2, 'poly_order': 3}, min_within_bound_threshold=-self._max_abs_yaw_accel, max_within_bound_threshold=self._max_abs_yaw_accel)
        return metric_statistics

def __init__(self, name: str, category: str, max_abs_yaw_accel: float) -> None:
    """
        Initializes the EgoYawAccelerationStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_accel: Maximum threshold to define if absolute yaw acceleration is within bound.
        """
    super().__init__(name=name, category=category)
    self._max_abs_yaw_accel = max_abs_yaw_accel

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

def __init__(self, name: str, category: str, discount_factor: float) -> None:
    """
        Initializes the EgoExpertL2ErrorStatistics class
        :param name: Metric name
        :param category: Metric category
        :param discount_factor: Displacement at step i is discounted by discount_factor^i.
        """
    super().__init__(name=name, category=category)
    self._discount_factor = discount_factor

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

def __init__(self, name: str, category: str) -> None:
    """
        Initializes the EgoMeanSpeedStatistics class
        :param name: Metric name
        :param category: Metric category.
        """
    super().__init__(name=name, category=category)

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

class EgoYawRateStatistics(WithinBoundMetricBase):
    """Ego yaw rate metric."""

    def __init__(self, name: str, category: str, max_abs_yaw_rate: float) -> None:
        """
        Initializes the EgoYawRateStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_rate: Maximum threshold to define if absolute yaw rate is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_yaw_rate = max_abs_yaw_rate

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the yaw rate  metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated yaw rate metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='radians_per_second', extract_function=extract_ego_yaw_rate, extract_function_params={}, min_within_bound_threshold=-self._max_abs_yaw_rate, max_within_bound_threshold=self._max_abs_yaw_rate)
        return metric_statistics

def __init__(self, name: str, category: str, max_abs_yaw_rate: float) -> None:
    """
        Initializes the EgoYawRateStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_yaw_rate: Maximum threshold to define if absolute yaw rate is within bound.
        """
    super().__init__(name=name, category=category)
    self._max_abs_yaw_rate = max_abs_yaw_rate

class EgoLonJerkStatistics(WithinBoundMetricBase):
    """Ego longitudinal jerk metric."""

    def __init__(self, name: str, category: str, max_abs_lon_jerk: float) -> None:
        """
        Initializes the EgoLonJerkStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lon_jerk: Maximum threshold to define if lon jerk is within bound.
        """
        super().__init__(name=name, category=category)
        self._max_abs_lon_jerk = max_abs_lon_jerk

    def compute(self, history: SimulationHistory, scenario: AbstractScenario) -> List[MetricStatistics]:
        """
        Returns the longitudinal jerk metric
        :param history: History from a simulation engine
        :param scenario: Scenario running this metric
        :return the estimated longitudinal jerk metric.
        """
        metric_statistics: List[MetricStatistics] = self._compute_statistics(history=history, scenario=scenario, statistic_unit_name='meters_per_second_cubed', extract_function=extract_ego_jerk, extract_function_params={'acceleration_coordinate': 'x'}, min_within_bound_threshold=-self._max_abs_lon_jerk, max_within_bound_threshold=self._max_abs_lon_jerk)
        return metric_statistics

def __init__(self, name: str, category: str, max_abs_lon_jerk: float) -> None:
    """
        Initializes the EgoLonJerkStatistics class
        :param name: Metric name
        :param category: Metric category
        :param max_abs_lon_jerk: Maximum threshold to define if lon jerk is within bound.
        """
    super().__init__(name=name, category=category)
    self._max_abs_lon_jerk = max_abs_lon_jerk

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

def build_callbacks_worker(cfg: DictConfig) -> Optional[WorkerPool]:
    """
    Builds workerpool for callbacks.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: Workerpool, or None if we'll run without one.
    """
    if not is_target_type(cfg.worker, Sequential) or cfg.disable_callback_parallelization:
        return None
    if cfg.number_of_cpus_allocated_per_simulation not in [None, 1]:
        raise ValueError('Expected `number_of_cpus_allocated_per_simulation` to be set to 1 with Sequential worker.')
    max_workers = min(WorkerResources.current_node_cpu_count() - (cfg.number_of_cpus_allocated_per_simulation or 1), cfg.max_callback_workers)
    callbacks_worker_pool = SingleMachineParallelExecutor(use_process_pool=True, max_workers=max_workers)
    return callbacks_worker_pool

class PathKeywordMatch(logging.Filter):
    """
    This implements simple logging.Filter, by running a regexp match on the path of the log record path name.
    """

    def __init__(self, regexp: str=''):
        """
        :param regexp: Regexp used for filtering.
        """
        self.regexp = regexp
        super().__init__()

    def filter(self, log_record: logging.LogRecord) -> bool:
        """
        Determine if the specified record is to be logged.
        :param log_record: Logging.LogRecord, the record to emit.
        :return: Is the specified record to be logged? False for no, True for yes.
        """
        return re.match(self.regexp, log_record.pathname) is not None

def __init__(self, regexp: str=''):
    """
        :param regexp: Regexp used for filtering.
        """
    self.regexp = regexp
    super().__init__()

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

def __init__(self, level: int=logging.NOTSET) -> None:
    """
        Constructor.
        :param level: A log level.
        """
    super().__init__(level)

class TestCache(SkeletonTestTrain):
    """
    Test main training entry point using combinations of models, datasets, filters etc.
    """

    def setUp(self) -> None:
        """
        Set up test attributes.
        """
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.cache_path = f'{self.tmp_dir.name}/cache'
        self.test_args = ['+training=training_raster_model', 'scenario_builder=mock_abstract_scenario_builder', f'group={self.tmp_dir.name}', f'cache.cache_path={self.cache_path}']

    def tearDown(self) -> None:
        """
        Cleanup after each test.
        """
        self.tmp_dir.cleanup()

    @patch('nuplan.planning.training.modeling.models.raster_model.RasterModel.get_list_of_required_feature')
    @patch('nuplan.planning.training.modeling.models.raster_model.RasterModel.get_list_of_computed_target')
    def test_cache_dataset(self, feature_builders_fn: Mock, target_builders_fn: Mock) -> None:
        """
        Tests dataset caching.
        """
        feature_builders_fn.return_value = [MockFeatureBuilder(torch.Tensor([0.0]))]
        target_builders_fn.return_value = [MockFeatureBuilder(torch.Tensor([0.0]))]
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=cache'])
            main(cfg)
        all_feature_builders = feature_builders_fn.return_value + target_builders_fn.return_value
        all_feature_names = {builder.get_feature_unique_name() for builder in all_feature_builders}
        scenario_cache_paths = get_local_scenario_cache(self.cache_path, all_feature_names)
        self.assertTrue(len(scenario_cache_paths) == cfg.scenario_builder.num_scenarios)

def setUp(self) -> None:
    """
        Set up test attributes.
        """
    super().setUp()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.cache_path = f'{self.tmp_dir.name}/cache'
    self.test_args = ['+training=training_raster_model', 'scenario_builder=mock_abstract_scenario_builder', f'group={self.tmp_dir.name}', f'cache.cache_path={self.cache_path}']

class SkeletonTestSimulation(unittest.TestCase):
    """
    Test main simulation entry point using the same config.
    """

    def __init__(self, *args: Any, main_path: Optional[Path]=None, **kwargs: Any):
        """
        Constructor for the class SkeletonTestSimulation.
        :param args: Arguments.
        :param main_path: The main path to search hydra config paths from.
        :param kwargs: Keyword arguments.
        """
        super(SkeletonTestSimulation, self).__init__(*args, **kwargs)
        self._main_path = main_path

    def setUp(self) -> None:
        """Set up basic configs."""
        self._main_path = self._main_path if self._main_path else Path(os.path.realpath(__file__)).parent
        self.config_path = str(self._main_path.parent / 'config/simulation/')
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.default_overrides = ['log_config=false', 'scenario_builder=nuplan_mini', 'planner=simple_planner', 'scenario_filter=one_of_each_scenario_type', 'scenario_filter.limit_total_scenarios=2', 'worker=sequential', 'exit_on_failure=true', f'group={self.tmp_dir.name}', 'job_name=test_simulation', 'output_dir=${group}/${experiment}']

    def tearDown(self) -> None:
        """Clean up."""
        if Path(self.tmp_dir.name).exists():
            self.tmp_dir.cleanup()
        if ray.is_initialized():
            ray.shutdown()

def __init__(self, *args: Any, main_path: Optional[Path]=None, **kwargs: Any):
    """
        Constructor for the class SkeletonTestSimulation.
        :param args: Arguments.
        :param main_path: The main path to search hydra config paths from.
        :param kwargs: Keyword arguments.
        """
    super(SkeletonTestSimulation, self).__init__(*args, **kwargs)
    self._main_path = main_path

class TestCache(SkeletonTestTrain):
    """
    Test main training entry point using combinations of models, datasets, filters etc.
    """

    def setUp(self) -> None:
        """
        Set up test attributes.
        """
        super().setUp()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.local_cache_path = f'{self.tmp_dir.name}/cache'
        self.s3_cache_path = 's3://test-bucket/nuplan_tests/test_cache_nuplandb'
        self.test_args = ['+training=training_raster_model', 'scenario_builder=nuplan_mini', 'splitter=nuplan', f'group={self.tmp_dir.name}']

    def tearDown(self) -> None:
        """
        Cleanup after each test.
        """
        self.tmp_dir.cleanup()

    @unittest.skip('Skip in CI until issue is resolved')
    def test_cache_dataset_s3(self) -> None:
        """
        Tests dataset caching with mocked S3.
        """
        s3_bucket, s3_key = split_s3_path(self.s3_cache_path)
        set_mock_object_from_aws(Path('nuplan-v1.1/maps/us-pa-pittsburgh-hazelwood/9.17.1937/map.gpkg'), 'nuplan-production')
        with mock_async_s3():
            asyncio.run(create_mock_bucket(s3_bucket))
            with initialize_config_dir(config_dir=self.config_path):
                cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'scenario_filter.limit_total_scenarios=10', 'py_func=cache', f'cache.cache_path={self.s3_cache_path}', 'cache.force_feature_computation=True'])
                main(cfg)
            self.assertTrue(len(list_files_in_s3_directory(s3_key, s3_bucket)) > 0)
            with initialize_config_dir(config_dir=self.config_path):
                cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=train', 'scenario_filter.limit_total_scenarios=10', 'cache.cleanup_cache=false', 'cache.use_cache_without_dataset=true', f'cache.cache_path={self.s3_cache_path}'])
                main(cfg)
            with initialize_config_dir(config_dir=self.config_path):
                cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=train', 'scenario_filter.limit_total_scenarios=10', 'cache.cleanup_cache=false', 'cache.use_cache_without_dataset=false', f'cache.cache_path={self.s3_cache_path}'])
                main(cfg)

    def test_cache_dataset_local(self) -> None:
        """
        Tests local dataset caching.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=cache', f'cache.cache_path={self.local_cache_path}'])
            main(cfg)
        self.assertTrue(any(Path(self.local_cache_path).iterdir()))
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=train', 'cache.cleanup_cache=false', 'cache.use_cache_without_dataset=true', f'cache.cache_path={self.local_cache_path}'])
            main(cfg)
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=train', 'cache.cleanup_cache=false', 'cache.use_cache_without_dataset=false', f'cache.cache_path={self.local_cache_path}'])
            main(cfg)

    def test_profiling(self) -> None:
        """Test that profiling gets generated."""
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, *self.test_args, 'py_func=cache', 'enable_profiling=True', f'cache.cache_path={self.local_cache_path}'])
            main(cfg)
        self.assertTrue(Path(self.local_cache_path).rglob('caching.html'))

def setUp(self) -> None:
    """
        Set up test attributes.
        """
    super().setUp()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.local_cache_path = f'{self.tmp_dir.name}/cache'
    self.s3_cache_path = 's3://test-bucket/nuplan_tests/test_cache_nuplandb'
    self.test_args = ['+training=training_raster_model', 'scenario_builder=nuplan_mini', 'splitter=nuplan', f'group={self.tmp_dir.name}']

class TestTrainOptimizerOCLRScheduler(SkeletonTestTrain):
    """
    Test Optimizer and LR Scheduler instantiation.
    """
    world_size = 4

    def setUp(self) -> None:
        """Setup test attributes."""
        super().setUp()
        self.optimizer_initial_lr = 0.01
        self.div_factor = 20
        self.max_lr = 2
        self.steps_per_epoch = 20

    @patch.dict(os.environ, {'WORLD_SIZE': str(world_size)}, clear=False)
    def test_optimizer_oclr_scheduler_instantiation(self) -> None:
        """
        Tests that optimizer and lr_scheduler were instantiated correctly.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_simple_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=30', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1', 'gpu=false', 'optimizer=adamw', f'optimizer.lr={str(self.optimizer_initial_lr)}', 'lr_scheduler=one_cycle_lr', f'lr_scheduler.div_factor={str(self.div_factor)}', f'lr_scheduler.max_lr={str(self.max_lr)}', f'lr_scheduler.steps_per_epoch={str(self.steps_per_epoch)}'])
            engine = main(cfg)
            self.assertTrue(isinstance(engine.model.optimizers(), torch.optim.AdamW), msg=f'Expected optimizer {torch.optim.AdamW} but got {engine.model.optimizers()}')
            self.assertTrue(isinstance(engine.model.lr_schedulers(), torch.optim.lr_scheduler.OneCycleLR), msg=f'Expected lr_scheduler {torch.optim.lr_scheduler.OneCycleLR} but got {engine.model.lr_schedulers()}')
            expected_base_lr = self.optimizer_initial_lr / self.div_factor
            result_base_lr = engine.model.lr_schedulers().state_dict()['base_lrs'][0]
            self.assertEqual(result_base_lr, expected_base_lr, msg=f'Expected base lr to be {expected_base_lr} but got {result_base_lr}')
            self.tearDown()

def setUp(self) -> None:
    """Setup test attributes."""
    super().setUp()
    self.optimizer_initial_lr = 0.01
    self.div_factor = 20
    self.max_lr = 2
    self.steps_per_epoch = 20

class SkeletonTestTrain(unittest.TestCase):
    """
    Test main training entry point using combinations of models, datasets, filters etc.
    """

    def __init__(self, *args: Any, main_path: Optional[str]=None, **kwargs: Any):
        """
        Constructor for the class SkeletonTestTrain
        :param args: Arguments.
        :param additional_paths: Any additional paths needed for hydra
        :param kwargs: Keyword arguments.
        """
        super(SkeletonTestTrain, self).__init__(*args, **kwargs)
        self._main_path = main_path

    def setUp(self) -> None:
        """Set up basic config."""
        if not self._main_path:
            self._main_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(self._main_path, '../config/training/')
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.default_overrides = ['log_config=false', 'worker=sequential', 'scenario_filter.limit_total_scenarios=30', 'lightning.trainer.params.max_epochs=1', 'lightning.trainer.params.check_val_every_n_epoch=1', 'lightning.trainer.params.limit_train_batches=1', 'lightning.trainer.params.limit_val_batches=1', 'lightning.trainer.params.limit_test_batches=1', 'data_loader.params.batch_size=2', 'data_loader.params.num_workers=2', 'data_loader.params.pin_memory=false', f'group={self.tmp_dir.name}', f'cache.cache_path={self.tmp_dir.name}/cache', 'cache.cleanup_cache=True', 'output_dir=${group}/${experiment}']

    def tearDown(self) -> None:
        """Clean up."""
        if Path(self.tmp_dir.name).exists():
            self.tmp_dir.cleanup()
        if ray.is_initialized():
            ray.shutdown()

def __init__(self, *args: Any, main_path: Optional[str]=None, **kwargs: Any):
    """
        Constructor for the class SkeletonTestTrain
        :param args: Arguments.
        :param additional_paths: Any additional paths needed for hydra
        :param kwargs: Keyword arguments.
        """
    super(SkeletonTestTrain, self).__init__(*args, **kwargs)
    self._main_path = main_path

