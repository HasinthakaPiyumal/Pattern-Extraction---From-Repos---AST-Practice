# Cluster 29

@cli.command()
def info(db_version: str=typer.Argument(NUPLAN_DB_VERSION, help='The database version.'), data_root: str=typer.Option(NUPLAN_DATA_ROOT, help='The root location of the database')) -> None:
    """
    Print out detailed information about the selected database.
    """
    db_version = _ensure_file_downloaded(data_root, db_version)
    db_description = get_db_description(db_version)
    for table_name, table_description in db_description.tables.items():
        typer.echo(f'Table {table_name}: {table_description.row_count} rows')
        for column_name, column_description in table_description.columns.items():
            typer.echo(''.join([f'\tcolumn {column_name}: {column_description.data_type} ', 'NULL ' if column_description.nullable else 'NOT NULL ', 'PRIMARY KEY ' if column_description.is_primary_key else '']))
        typer.echo()

@cli.command()
def duration(db_version: str=typer.Argument(NUPLAN_DB_VERSION, help='The database version.'), data_root: str=typer.Option(NUPLAN_DATA_ROOT, help='The root location of the database')) -> None:
    """
    Print out the duration of the selected db.
    """
    db_version = _ensure_file_downloaded(data_root, db_version)
    db_duration_us = get_db_duration_in_us(db_version)
    db_duration_s = float(db_duration_us) / 1000000.0
    db_duration_str = time.strftime('%H:%M:%S', time.gmtime(db_duration_s))
    typer.echo(f'DB duration is {db_duration_str} [HH:MM:SS]')

@cli.command()
def log_duration(db_version: str=typer.Argument(NUPLAN_DB_VERSION, help='The database version.'), data_root: str=typer.Option(NUPLAN_DATA_ROOT, help='The root location of the database')) -> None:
    """
    Print out the duration of every log in the selected db.
    """
    db_version = _ensure_file_downloaded(data_root, db_version)
    num_logs = 0
    for log_file_name, log_file_duration_us in get_db_log_duration(db_version):
        log_file_duration_s = float(log_file_duration_us) / 1000000.0
        log_file_duration_str = time.strftime('%H:%M:%S', time.gmtime(log_file_duration_s))
        typer.echo(f'The duration of log {log_file_name} is {log_file_duration_str} [HH:MM:SS]')
        num_logs += 1
    typer.echo(f'There are {num_logs} total logs.')

@cli.command()
def log_vehicle(db_version: str=typer.Argument(NUPLAN_DB_VERSION, help='The database version.'), data_root: str=typer.Option(NUPLAN_DATA_ROOT, help='The root location of the database')) -> None:
    """
    Print out vehicle information from every log in the selected database.
    """
    db_version = _ensure_file_downloaded(data_root, db_version)
    for log_file, vehicle_name in get_db_log_vehicles(db_version):
        typer.echo(f'For the log {log_file}, vehicle {vehicle_name} was used.')

@cli.command()
def scenarios(db_version: str=typer.Argument(NUPLAN_DB_VERSION, help='The database version.'), data_root: str=typer.Option(NUPLAN_DATA_ROOT, help='The root location of the database')) -> None:
    """
    Print out the available scenarios in the selected db.
    """
    db_version = _ensure_file_downloaded(data_root, db_version)
    total_count = 0
    for tag, num_scenarios in get_db_scenario_info(db_version):
        typer.echo(f'{tag}: {num_scenarios} scenarios.')
        total_count += num_scenarios
    typer.echo(f'TOTAL: {total_count} scenarios.')

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

class TestDbCliQueries(unittest.TestCase):
    """
    Test suite for the DB Cli queries.
    """

    @staticmethod
    def getDBFilePath() -> Path:
        """
        Get the location for the temporary SQLite file used for the test DB.
        :return: The filepath for the test data.
        """
        return Path('/tmp/test_db_cli_queries.sqlite3')

    @classmethod
    def setUpClass(cls) -> None:
        """
        Create the mock DB data.
        """
        db_file_path = TestDbCliQueries.getDBFilePath()
        if db_file_path.exists():
            db_file_path.unlink()
        generation_parameters = DBGenerationParameters(num_lidars=1, num_cameras=2, num_sensor_data_per_sensor=50, num_lidarpc_per_image_ratio=2, num_scenes=10, num_traffic_lights_per_lidar_pc=5, num_agents_per_lidar_pc=3, num_static_objects_per_lidar_pc=2, scene_scenario_tag_mapping={5: ['first_tag'], 6: ['first_tag', 'second_tag']}, file_path=str(db_file_path))
        generate_minimal_nuplan_db(generation_parameters)

    def setUp(self) -> None:
        """
        The method to run before each test.
        """
        self.db_file_name = str(TestDbCliQueries.getDBFilePath())

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Destroy the mock DB data.
        """
        db_file_path = TestDbCliQueries.getDBFilePath()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    def test_get_db_description(self) -> None:
        """
        Test the get_db_description queries.
        """
        db_description = get_db_description(self.db_file_name)
        expected_tables = ['category', 'ego_pose', 'lidar', 'lidar_box', 'lidar_pc', 'log', 'scenario_tag', 'scene', 'track', 'traffic_light_status', 'camera', 'image']
        self.assertEqual(len(expected_tables), len(db_description.tables))
        for expected_table in expected_tables:
            self.assertTrue(expected_table in db_description.tables)
        lidar_pc_table = db_description.tables['lidar_pc']
        self.assertEqual('lidar_pc', lidar_pc_table.name)
        self.assertEqual(50, lidar_pc_table.row_count)
        self.assertEqual(8, len(lidar_pc_table.columns))
        columns = sorted(lidar_pc_table.columns.values(), key=lambda x: x.column_id)

        def _validate_column(column: ColumnDescription, expected_id: int, expected_name: str, expected_data_type: str, expected_nullable: bool, expected_is_primary_key: bool) -> None:
            """
            A quick method to validate column info to reduce boilerplate.
            """
            self.assertEqual(expected_id, column.column_id)
            self.assertEqual(expected_name, column.name)
            self.assertEqual(expected_data_type, column.data_type)
            self.assertEqual(expected_nullable, column.nullable)
            self.assertEqual(expected_is_primary_key, column.is_primary_key)
        _validate_column(columns[0], 0, 'token', 'BLOB', False, True)
        _validate_column(columns[1], 1, 'next_token', 'BLOB', True, False)
        _validate_column(columns[2], 2, 'prev_token', 'BLOB', True, False)
        _validate_column(columns[3], 3, 'ego_pose_token', 'BLOB', False, False)
        _validate_column(columns[4], 4, 'lidar_token', 'BLOB', False, False)
        _validate_column(columns[5], 5, 'scene_token', 'BLOB', True, False)
        _validate_column(columns[6], 6, 'filename', 'VARCHAR(128)', True, False)
        _validate_column(columns[7], 7, 'timestamp', 'INTEGER', True, False)

    def test_get_db_duration_in_us(self) -> None:
        """
        Test the get_db_duration_in_us query
        """
        duration = get_db_duration_in_us(self.db_file_name)
        self.assertEqual(49 * 1000000.0, duration)

    def test_get_db_log_duration(self) -> None:
        """
        Test the get_db_log_duration query.
        """
        log_durations = list(get_db_log_duration(self.db_file_name))
        self.assertEqual(1, len(log_durations))
        self.assertEqual('logfile', log_durations[0][0])
        self.assertEqual(49 * 1000000.0, log_durations[0][1])

    def test_get_db_log_vehicles(self) -> None:
        """
        Test the get_db_log_vehicles query.
        """
        log_vehicles = list(get_db_log_vehicles(self.db_file_name))
        self.assertEqual(1, len(log_vehicles))
        self.assertEqual('logfile', log_vehicles[0][0])
        self.assertEqual('vehicle_name', log_vehicles[0][1])

    def test_get_db_scenario_info(self) -> None:
        """
        Test the get_db_scenario_info query.
        """
        scenario_info_tags = list(get_db_scenario_info(self.db_file_name))
        self.assertEqual(2, len(scenario_info_tags))
        self.assertEqual('first_tag', scenario_info_tags[0][0])
        self.assertEqual(2, scenario_info_tags[0][1])
        self.assertEqual('second_tag', scenario_info_tags[1][0])
        self.assertEqual(1, scenario_info_tags[1][1])

def test_get_db_duration_in_us(self) -> None:
    """
        Test the get_db_duration_in_us query
        """
    duration = get_db_duration_in_us(self.db_file_name)
    self.assertEqual(49 * 1000000.0, duration)

def test_get_db_log_duration(self) -> None:
    """
        Test the get_db_log_duration query.
        """
    log_durations = list(get_db_log_duration(self.db_file_name))
    self.assertEqual(1, len(log_durations))
    self.assertEqual('logfile', log_durations[0][0])
    self.assertEqual(49 * 1000000.0, log_durations[0][1])

def test_get_db_log_vehicles(self) -> None:
    """
        Test the get_db_log_vehicles query.
        """
    log_vehicles = list(get_db_log_vehicles(self.db_file_name))
    self.assertEqual(1, len(log_vehicles))
    self.assertEqual('logfile', log_vehicles[0][0])
    self.assertEqual('vehicle_name', log_vehicles[0][1])

def test_get_db_scenario_info(self) -> None:
    """
        Test the get_db_scenario_info query.
        """
    scenario_info_tags = list(get_db_scenario_info(self.db_file_name))
    self.assertEqual(2, len(scenario_info_tags))
    self.assertEqual('first_tag', scenario_info_tags[0][0])
    self.assertEqual(2, scenario_info_tags[0][1])
    self.assertEqual('second_tag', scenario_info_tags[1][0])
    self.assertEqual(1, scenario_info_tags[1][1])

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

def test_update(self) -> None:
    """
        Tests whether TrajectoryState is compatible with dict.update()
        """
    scene = {'example': 'unchanged', 'pose': 'old_pose', 'speed': 'old_speed'}
    scene.update(self.trajectory_state)
    self.assertEqual(scene, {'example': 'unchanged', 'pose': [self.pose_x, self.pose_y, self.pose_heading], 'speed': self.speed, 'velocity_2d': self.velocity_2d, 'lateral': self.lateral, 'acceleration': self.acceleration})

class TestTrajectory(unittest.TestCase):
    """
    Test scene dataclass Trajectory
    """

    def setUp(self) -> None:
        """
        Set up
        """
        self.color = Color(1, 0.5, 0, 1, ColorType.INT)
        self.states = [Mock(spec=TrajectoryState), Mock(spec=TrajectoryState)]
        self.trajectory_structure = Trajectory(color=self.color, states=self.states)

    def test_init(self) -> None:
        """
        Tests TrajectoryState initialization
        """
        self.assertEqual(self.trajectory_structure.color, self.color)
        self.assertEqual(self.trajectory_structure.states, self.states)

    @patch('nuplan.planning.utils.serialization.scene.type')
    def test_serialize(self, mock_type: Mock) -> None:
        """
        Tests whether TrajectoryState is serializable
        """
        self.states[0].__iter__ = Mock(return_value=iter([['state_0', 'value_0']]))
        self.states[1].__iter__ = Mock(return_value=iter([['state_1', 'value_1']]))
        mock_type.side_effect = lambda x: TrajectoryState if isinstance(x, TrajectoryState) else type(x)
        result = dict(self.trajectory_structure)
        self.assertEqual(result, {'color': self.color.to_list(), 'states': [{'state_0': 'value_0'}, {'state_1': 'value_1'}]})

    def test_update(self) -> None:
        """
        Tests whether Trajectory is compatible with dict.update()
        """
        scene = {'example': 'unchanged', 'color': 'old_color'}
        scene.update(self.trajectory_structure)
        self.assertEqual(scene, {'example': 'unchanged', 'color': self.color.to_list(), 'states': self.states})

def test_update(self) -> None:
    """
        Tests whether Trajectory is compatible with dict.update()
        """
    scene = {'example': 'unchanged', 'color': 'old_color'}
    scene.update(self.trajectory_structure)
    self.assertEqual(scene, {'example': 'unchanged', 'color': self.color.to_list(), 'states': self.states})

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

def submit(self, task: Task, *args: Any, **kwargs: Any) -> Future[Any]:
    """Inherited, see superclass."""
    return self._executor.submit(task.fn, *args, **kwargs)

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

def test_name(self) -> None:
    """Test name"""
    self.assertEqual(self.predictor.name(), 'MockAbstractPredictor')

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

class TestAbstractIDMPlanner(unittest.TestCase):
    """Test the AbstractIDMPlanner interface"""
    TEST_FILE_PATH = 'nuplan.planning.simulation.planner.abstract_idm_planner'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.scenario = get_test_nuplan_scenario()
        self.planned_trajectory_samples = 10
        self.planner = MockIDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

    def test_name(self) -> None:
        """Test name"""
        self.assertEqual(self.planner.name(), 'MockIDMPlanner')

    def test_observation_type(self) -> None:
        """Test observation_type"""
        self.assertEqual(self.planner.observation_type(), DetectionsTracks)

    def test__initialize_route_plan_assertion_error(self) -> None:
        """Test raise if _map_api is uninitialized"""
        with self.assertRaises(AssertionError):
            self.planner._initialize_route_plan([])

    def test__initialize_route_plan(self) -> None:
        """Test _map_api is uninitialized."""
        with patch.object(self.planner, '_map_api') as _map_api:
            _map_api.get_map_object = Mock()
            _map_api.get_map_object.side_effect = [MagicMock(), None, MagicMock()]
            mock_route_roadblock_ids = ['a']
            self.planner._initialize_route_plan(mock_route_roadblock_ids)
            _map_api.get_map_object.assert_called_with('a', SemanticMapLayer.ROADBLOCK)
            mock_route_roadblock_ids = ['b']
            self.planner._initialize_route_plan(mock_route_roadblock_ids)
            _map_api.get_map_object.assert_called_with('b', SemanticMapLayer.ROADBLOCK_CONNECTOR)

    def test__construct_occupancy_map_value_error(self) -> None:
        """Test raise if observation type is incorrect"""
        with self.assertRaises(ValueError):
            self.planner._construct_occupancy_map(Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.STRTreeOccupancyMapFactory.get_from_boxes')
    def test__construct_occupancy_map(self, mock_get_from_boxes: Mock) -> None:
        """Test raise if observation type is incorrect"""
        mock_observations = self.scenario.initial_tracked_objects
        mock_ego_state = self.scenario.initial_ego_state
        self.planner._construct_occupancy_map(mock_ego_state, mock_observations)
        mock_get_from_boxes.assert_called_once()

    def test__propagate(self) -> None:
        """Test _propagate()"""
        with patch.object(self.planner, '_policy') as _policy:
            init_progress = 1
            init_velocity = 2
            tspan = 0.5
            mock_ego_idm_state = IDMAgentState(init_progress, init_velocity)
            mock_lead_agent = Mock()
            _policy.solve_forward_euler_idm_policy = Mock(return_value=IDMAgentState(3, 4))
            self.planner._propagate(mock_ego_idm_state, mock_lead_agent, tspan)
            _policy.solve_forward_euler_idm_policy.assert_called_once_with(IDMAgentState(0, init_velocity), mock_lead_agent, tspan)
            self.assertEqual(init_progress + _policy.solve_forward_euler_idm_policy().progress, mock_ego_idm_state.progress)
            self.assertEqual(_policy.solve_forward_euler_idm_policy().velocity, mock_ego_idm_state.velocity)

    def test__get_planned_trajectory_error(self) -> None:
        """Test raise if _ego_path_linestring has not been initialized"""
        with self.assertRaises(AssertionError):
            self.planner._get_planned_trajectory(Mock(), Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.InterpolatedTrajectory')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._propagate')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._get_leading_object')
    @patch(f'{TEST_FILE_PATH}.AbstractIDMPlanner._idm_state_to_ego_state')
    def test__get_planned_trajectory(self, mock_idm_state_to_ego_state: Mock, mock_get_leading_object: Mock, mock_propagate: Mock, mock_trajectory: Mock) -> None:
        """Test _get_planned_trajectory"""
        with patch.object(self.planner, '_ego_path_linestring') as _ego_path_linestring:
            _ego_path_linestring.project = call()
            mock_idm_state_to_ego_state.return_value = Mock()
            mock_get_leading_object.return_value = Mock()
            self.planner._get_planned_trajectory(MagicMock(), MagicMock(), MagicMock())
            _ego_path_linestring.project.assert_called_once()
            mock_idm_state_to_ego_state.assert_called()
            mock_get_leading_object.assert_called()
            mock_propagate.assert_called()
            mock_trajectory.assert_called_once()

    def test__idm_state_to_ego_state_error(self) -> None:
        """Test raise if _ego_path has not been initialized"""
        with self.assertRaises(AssertionError):
            self.planner._idm_state_to_ego_state(Mock(), Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.EgoState.build_from_center')
    @patch(f'{TEST_FILE_PATH}.max')
    @patch(f'{TEST_FILE_PATH}.min')
    def test__idm_state_to_ego_state(self, mock_max: Mock, mock_min: Mock, mock_build_from_center: Mock) -> None:
        """Test _idm_state_to_ego_state"""
        with patch.object(self.planner, '_ego_path') as _ego_path:
            mock_new_center = MagicMock(autospec=True)
            mock_ego_idm_state = IDMAgentState(0, 1)
            mock_time_point = Mock()
            mock_vehicle_params = Mock()
            _ego_path.get_state_at_progress = Mock(return_value=mock_new_center)
            self.planner._idm_state_to_ego_state(mock_ego_idm_state, mock_time_point, mock_vehicle_params)
            mock_max.assert_called_once()
            mock_min.assert_called_once()
            mock_build_from_center.assert_called_with(center=StateSE2(mock_new_center.x, mock_new_center.y, mock_new_center.heading), center_velocity_2d=StateVector2D(mock_ego_idm_state.velocity, 0), center_acceleration_2d=StateVector2D(0, 0), tire_steering_angle=0.0, time_point=mock_time_point, vehicle_parameters=mock_vehicle_params)

    def test__annotate_occupancy_map_error(self) -> None:
        """Test raise if _map_api or _candidate_lane_edge_ids has not been initialized"""
        with self.assertRaises(AssertionError):
            with patch.object(self.planner, '_map_api'):
                self.planner._annotate_occupancy_map(Mock(), Mock())
        with self.assertRaises(AssertionError):
            with patch.object(self.planner, '_candidate_lane_edge_ids'):
                self.planner._annotate_occupancy_map(Mock(), Mock())

    @patch(f'{TEST_FILE_PATH}.trim_path')
    @patch(f'{TEST_FILE_PATH}.unary_union')
    @patch(f'{TEST_FILE_PATH}.path_to_linestring')
    def test__get_expanded_ego_path(self, mock_path_to_linestring: MagicMock, mock_unary_union: Mock, mock_trim_path: Mock) -> None:
        """Test _get_expanded_ego_path"""
        mock_ego_idm_state = IDMAgentState(0, 1)
        mock_ego_state = MagicMock(spec_set=EgoState)
        mock_trim_path.return_value = Mock()
        with patch.object(self.planner, '_ego_path') as _ego_path:
            _ego_path.get_start_progress = Mock(return_value=0)
            _ego_path.get_end_progress = Mock(return_value=10)
            self.planner._get_expanded_ego_path(mock_ego_state, mock_ego_idm_state)
            mock_trim_path.assert_called_once()
            mock_path_to_linestring.assert_called_once_with(mock_trim_path.return_value)
            mock_unary_union.assert_called_once()

    @patch(f'{TEST_FILE_PATH}.transform')
    @patch(f'{TEST_FILE_PATH}.principal_value')
    def test__get_leading_idm_agent(self, mock_principal_value: Mock, mock_transform: Mock) -> None:
        """Test _get_leading_idm_agent when an Agent object is passed"""
        mock_agent = MagicMock(spec_set=Agent)
        mock_transform.return_value = StateSE2(1, 0, 0)
        mock_relative_distance = 2
        result = self.planner._get_leading_idm_agent(MagicMock(spec_set=EgoState), mock_agent, mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(mock_transform.return_value.x, result.velocity)
        self.assertEqual(0.0, result.length_rear)
        mock_principal_value.assert_called_once()
        mock_transform.assert_called_once()

    def test__get_leading_idm_agent_static(self) -> None:
        """Test _get_leading_idm_agent when a Staic object is passed"""
        mock_relative_distance = 2
        result = self.planner._get_leading_idm_agent(Mock(spec_set=EgoState), Mock(), mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(0.0, result.velocity)
        self.assertEqual(0.0, result.length_rear)

    def test__get_free_road_leading_idm_state(self) -> None:
        """Test _get_free_road_leading_idm_state"""
        mock_ego_idm_state = IDMAgentState(0, 1)
        mock_ego_state = self.scenario.initial_ego_state
        with patch.object(self.planner, '_ego_path', spec_set=AbstractPath) as _ego_path:
            _ego_path.get_start_progress = Mock(return_value=0)
            _ego_path.get_end_progress = Mock(return_value=10)
            result = self.planner._get_free_road_leading_idm_state(mock_ego_state, mock_ego_idm_state)
            self.assertEqual(_ego_path.get_end_progress() - mock_ego_idm_state.progress, result.progress)
            self.assertEqual(0.0, result.velocity)
            self.assertEqual(mock_ego_state.car_footprint.length / 2, result.length_rear)

    def test__get_red_light_leading_idm_state(self) -> None:
        """Test _get_red_light_leading_idm_state"""
        mock_relative_distance = 2
        result = self.planner._get_red_light_leading_idm_state(mock_relative_distance)
        self.assertEqual(mock_relative_distance, result.progress)
        self.assertEqual(0.0, result.velocity)
        self.assertEqual(0.0, result.length_rear)

    def test__get_leading_object(self) -> None:
        """Test _get_leading_object"""
        mock_occupancy_map = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents.size = 1
        mock_intersecting_agents.get_nearest_entry_to = Mock(return_value=('red_light', Mock(), 0.0))
        mock_occupancy_map.intersects = Mock(return_value=mock_intersecting_agents)
        with patch.object(self.planner, '_get_red_light_leading_idm_state') as mock_handle_traffic_light:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, Mock())
                mock_handle_traffic_light.assert_called_once_with(0.0)
                mock_get_expanded_ego_path.assert_called_once()
        mock_intersecting_agents.get_nearest_entry_to = Mock(return_value=('', Mock(), 0.0))
        with patch.object(self.planner, '_get_leading_idm_agent') as mock_handle_tracks:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, MagicMock())
                mock_handle_tracks.assert_called_once()
                mock_get_expanded_ego_path.assert_called_once()

    def test__get_leading_object_free_road(self) -> None:
        """Test _get_leading_object in the case where there are no leading agents"""
        mock_occupancy_map = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents = MagicMock(spec_set=OccupancyMap)
        mock_intersecting_agents.size = 0
        mock_occupancy_map.intersects = Mock(return_value=mock_intersecting_agents)
        with patch.object(self.planner, '_get_free_road_leading_idm_state') as mock_handle_free_road_case:
            with patch.object(self.planner, '_get_expanded_ego_path') as mock_get_expanded_ego_path:
                self.planner._get_leading_object(Mock(), MagicMock(), mock_occupancy_map, Mock())
                mock_handle_free_road_case.assert_called_once()
                mock_get_expanded_ego_path.assert_called_once()

def test_name(self) -> None:
    """Test name"""
    self.assertEqual(self.planner.name(), 'MockIDMPlanner')

class TestAbstractIDMPlanner(unittest.TestCase):
    """Test the AbstractIDMPlanner interface"""
    TEST_FILE_PATH = 'nuplan.planning.simulation.planner.idm_planner'

    def setUp(self) -> None:
        """Inherited, see superclass"""
        self.scenario = get_test_nuplan_scenario()
        self.planned_trajectory_samples = 10
        self.planner = IDMPlanner(target_velocity=10, min_gap_to_lead_agent=0.5, headway_time=1.5, accel_max=1.0, decel_max=2.0, planned_trajectory_samples=self.planned_trajectory_samples, planned_trajectory_sample_interval=0.2, occupancy_map_radius=20)

    def test_name(self) -> None:
        """Test name"""
        self.assertEqual(self.planner.name(), 'IDMPlanner')

    def test_observation_type(self) -> None:
        """Test observation_type"""
        self.assertEqual(self.planner.observation_type(), DetectionsTracks)

    def test__initialize_route_plan_assertion_error(self) -> None:
        """Test raise if _map_api is uninitialized"""
        with self.assertRaises(AssertionError):
            self.planner._initialize_route_plan([])

    @patch(f'{TEST_FILE_PATH}.IDMPlanner._initialize_route_plan')
    def test_initialize(self, mock_initialize_route_plan: Mock) -> None:
        """Test initialize"""
        initialization = MagicMock()
        self.planner.initialize(initialization)
        mock_initialize_route_plan.assert_called_once_with(initialization.route_roadblock_ids)

    @patch(f'{TEST_FILE_PATH}.path_to_linestring')
    @patch(f'{TEST_FILE_PATH}.create_path_from_se2')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._breadth_first_search')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._get_starting_edge')
    def test__initialize_ego_path(self, mock_get_starting_edge: Mock, mock_breadth_first_search: Mock, mock_create_path_from_se2: Mock, mock_path_to_linestring: Mock) -> None:
        """Test _initialize_ego_path()"""
        mock_starting_edge = Mock()
        mock_lane = MagicMock()
        mock_lane.speed_limit_mps = 0
        ego_state = self.scenario.initial_ego_state
        mock_breadth_first_search.return_value = ([mock_lane], True)
        mock_get_starting_edge.return_value = mock_starting_edge
        with patch.object(self.planner, '_route_roadblocks'):
            self.planner._initialize_ego_path(ego_state)
            mock_breadth_first_search.assert_called_once_with(ego_state)
            mock_create_path_from_se2.assert_called_once_with([])
            mock_path_to_linestring.assert_called_once_with([])

    def test__get_starting_edge(self) -> None:
        """Test _get_starting_edge()"""
        mock_edge = MagicMock(spec_set=LaneGraphEdgeMapObject)
        mock_edge.contains_point.side_effect = [False, True]
        mock_edge.polygon.distance.side_effect = [0, 0]
        mock_roadblock = MagicMock(spec_set=RoadBlockGraphEdgeMapObject)
        mock_roadblock.interior_edges = [mock_edge]
        self.planner._route_roadblocks = [mock_roadblock, mock_roadblock]
        result = self.planner._get_starting_edge(Mock(spec=EgoState))
        mock_edge.contains_point.assert_called()
        mock_edge.polygon.distance.assert_called()
        self.assertEqual(result, mock_edge)

    @patch(f'{TEST_FILE_PATH}.IDMPlanner._initialize_ego_path')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._construct_occupancy_map')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._annotate_occupancy_map')
    @patch(f'{TEST_FILE_PATH}.IDMPlanner._get_planned_trajectory')
    def test_compute_trajectory(self, mock_get_planned_trajectory: Mock, mock_annotate_occupancy_map: Mock, mock_construct_occupancy_map: Mock, mock_initialize_ego_path: Mock) -> None:
        """Test compute_trajectory"""
        planner_input = MagicMock()
        mock_ego_state = Mock()
        mock_traffic_light_data = call()
        planner_input.history.current_state = (mock_ego_state, Mock())
        planner_input.traffic_light_data = mock_traffic_light_data
        mock_occupancy_map = Mock()
        mock_unique_observations = Mock()
        mock_construct_occupancy_map.return_value = (mock_occupancy_map, mock_unique_observations)
        self.planner.compute_trajectory(planner_input)
        mock_initialize_ego_path.assert_called_once_with(mock_ego_state)
        mock_construct_occupancy_map.assert_called_once_with(*planner_input.history.current_state)
        mock_annotate_occupancy_map.assert_called_once_with(mock_traffic_light_data, mock_occupancy_map)
        mock_get_planned_trajectory.assert_called_once_with(mock_ego_state, mock_occupancy_map, mock_unique_observations)

    def test_compute_trajectory_integration(self) -> None:
        """Test the IDMPlanner in full using mock data"""
        history_buffer = SimulationHistoryBuffer.initialize_from_scenario(10, self.scenario, DetectionsTracks)
        self.planner.initialize(PlannerInitialization(self.scenario.get_route_roadblock_ids(), self.scenario.get_mission_goal(), self.scenario.map_api))
        trajectories = self.planner.compute_trajectory(PlannerInput(SimulationIteration(self.scenario.get_time_point(0), 0), history_buffer, list(self.scenario.get_traffic_light_status_at_iteration(0))))
        self.assertEqual(self.planned_trajectory_samples + 1, len(trajectories.get_sampled_trajectory()))

def test_name(self) -> None:
    """Test name"""
    self.assertEqual(self.planner.name(), 'IDMPlanner')

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

def test_name(self) -> None:
    """Tests planner name is set correctly."""
    result = self.planner.name()
    self.assertEqual(result, 'LogFuturePlanner')

class TestRemotePlanner(TestCase):
    """Tests RemotePlanner class"""

    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
    def setUp(self, mock_factory: Mock) -> None:
        """Sets variables for testing"""
        self.planner = RemotePlanner()
        self.planner_with_container = RemotePlanner(submission_container_manager=Mock(), submission_image='foo', container_name='bar')

    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', autospec=True)
    def test_initialization(self, mock_factory: Mock) -> None:
        """Tests that the class is initialized as intended."""
        mock_planner = RemotePlanner()
        self.assertEqual(None, mock_planner.submission_container_manager)
        self.assertEqual(50051, mock_planner.port)
        mock_planner = RemotePlanner(submission_container_manager=mock_factory, submission_image='foo', container_name='bar')
        self.assertEqual(mock_factory, mock_planner.submission_container_manager)
        self.assertEqual('foo', mock_planner.submission_image)
        self.assertEqual('bar', mock_planner.container_name)
        self.assertEqual(None, mock_planner.port)
        with self.assertRaises(AssertionError):
            _ = RemotePlanner(submission_container_manager=Mock())

    def test_name(self) -> None:
        """Tests planner name is set correctly"""
        self.assertEqual('RemotePlanner', self.planner.name())

    def test_observation_type(self) -> None:
        """Tests observation type is set correctly"""
        self.assertEqual(DetectionsTracks, self.planner.observation_type())

    def test_initialization_message_creation(self) -> None:
        """Tests that the message for the initialization request is built correctly."""
        mock_state_1 = Mock(x=0, y=1, heading=0.2)
        mock_map_api = Mock(map_name='test')
        mock_initialization = Mock(mission_goal=mock_state_1, map_api=mock_map_api, route_roadblock_ids=['a', 'b', 'c'])
        with self.assertRaises(AttributeError):
            self.planner._planner_initializations_to_message(Mock(mission_goal=None, map_api=mock_map_api))
        initialization_message = self.planner._planner_initializations_to_message(mock_initialization)
        self.assertAlmostEqual(mock_state_1.x, initialization_message.mission_goal.x)
        self.assertAlmostEqual(mock_state_1.y, initialization_message.mission_goal.y)
        self.assertAlmostEqual(mock_state_1.heading, initialization_message.mission_goal.heading)
        self.assertEqual(mock_map_api.map_name, initialization_message.map_name)
        self.assertEqual(initialization_message.route_roadblock_ids, ['a', 'b', 'c'])

    @patch.object(RemotePlanner, '_planner_initializations_to_message', return_value=123, autospec=True)
    @patch('grpc.insecure_channel')
    @patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', autospec=True)
    @patch('nuplan.planning.simulation.planner.remote_planner.SubmissionContainerManager', Mock(spec_set=SubmissionContainerManager))
    @patch('nuplan.planning.simulation.planner.remote_planner.find_free_port_number')
    def test_initialize(self, mock_find_port: Mock, mock_stub_function: Mock, mock_channel: Mock, initialization_to_message: Mock) -> None:
        """Tests that the initialization request is called correctly."""
        mock_initialization = Mock()
        mock_stub = Mock()
        mock_stub_function.return_value = mock_stub
        self.planner.initialize(mock_initialization)
        mock_channel.assert_called()
        initialization_to_message.assert_called_with(mock_initialization)
        self.planner._stub.InitializePlanner.assert_called_with(123)
        self.planner_with_container.initialize(mock_initialization)
        self.planner_with_container.submission_container_manager.get_submission_container.assert_called_with(self.planner_with_container.submission_image, self.planner_with_container.container_name, mock_find_port())
        self.planner_with_container.submission_container_manager.get_submission_container().start.assert_called()

    @patch.object(RemotePlanner, '_compute_trajectory')
    @patch('grpc.insecure_channel', Mock())
    @patch('nuplan.submission.challenge_pb2_grpc.DetectionTracksChallengeStub', Mock(spec_set=DetectionTracksChallengeStub))
    def test_compute_trajectory_interface(self, mock_compute_trajectory: Mock) -> None:
        """Tests that the interface for the trajectory computation request is called correctly."""
        mock_compute_trajectory.return_value = 'trajectories'
        mock_input = [Mock()]
        trajectories = self.planner.compute_trajectory(mock_input)
        mock_compute_trajectory.assert_called_with(self.planner._stub, current_input=mock_input)
        self.assertEqual('trajectories', trajectories)

    @patch('nuplan.planning.simulation.planner.remote_planner.interp_traj_from_proto_traj', Mock)
    @patch('nuplan.planning.simulation.planner.remote_planner.proto_tl_status_data_from_tl_status_data')
    @patch('nuplan.submission.challenge_pb2.PlannerInput')
    @patch('nuplan.submission.challenge_pb2.SimulationIteration')
    @patch('nuplan.submission.challenge_pb2.SimulationHistoryBuffer')
    def test_compute_trajectory(self, history_buffer: Mock, simulation_iteration: Mock, planner_input: Mock, mock_proto_tl_status_data: Mock) -> None:
        """Tests deserialization and serialization of the input/output for the trajectory computation interface."""
        with patch.object(self.planner, '_get_history_update', MagicMock()) as get_history_update:
            get_history_update.return_value = [['states'], ['observations'], ['intervals']]
            mock_stub = MagicMock()
            mock_tl_data = Mock()
            mock_input = Mock(iteration=Mock(time_us=1, index=0), history=Mock(ego_states='fake_input'), traffic_light_data=[mock_tl_data])
            mock_input.history.ego_states = ['fake_input']
            planner_input.return_value = 'planner input'
            simulation_iteration.return_value = 'iter_1'
            history_buffer.return_value = 'hb_1'
            self.planner._compute_trajectory(mock_stub, mock_input)
            get_history_update.assert_called_once_with(mock_input)
            mock_proto_tl_status_data.assert_called_once_with(mock_tl_data)
            simulation_iteration.assert_has_calls([call(time_us=1, index=0)])
            planner_input.assert_has_calls([call(simulation_iteration='iter_1', simulation_history_buffer='hb_1', traffic_light_data=[mock_proto_tl_status_data.return_value])])
            mock_stub.ComputeTrajectory.assert_called_once_with(planner_input.return_value, timeout=1)

    @patch('pickle.dumps')
    def test_get_history_update(self, mock_dumps: Mock) -> None:
        """Tests that the history update is built correctly."""
        planner_input = Mock()
        planner_input.history.ego_states = [1, 2]
        planner_input.history.observations = [4, 5]
        planner_input.history.current_state = (6, 7)
        serialized_states, serialized_observations, sample_interval = self.planner._get_history_update(planner_input)
        calls = [call(1), call(2), call(4), call(5)]
        mock_dumps.assert_has_calls(calls)
        self.planner.serialized_state = serialized_states
        self.planner.serialized_observation = serialized_observations
        self.planner.sample_intervals = sample_interval
        _, _, _ = self.planner._get_history_update(planner_input)
        calls = calls + [call(6), call(7)]
        mock_dumps.assert_has_calls(calls)

def test_name(self) -> None:
    """Tests planner name is set correctly"""
    self.assertEqual('RemotePlanner', self.planner.name())

class TimeCallback(AbstractMainCallback):
    """
    Callback for tracking how long a simulation took to run.
    """

    def __init__(self) -> None:
        """Callback to log simulation duration at the end of process."""
        self._start_time = 0.0

    def on_run_simulation_start(self) -> None:
        """Callback after the simulation function starts."""
        self._start_time = time.perf_counter()

    def on_run_simulation_end(self) -> None:
        """Callback before end of the main function."""
        end_time = time.perf_counter()
        elapsed_time_s = end_time - self._start_time
        time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
        logger.info(f'Simulation duration: {time_str} [HH:MM:SS]')

def on_run_simulation_start(self) -> None:
    """Callback after the simulation function starts."""
    self._start_time = time.perf_counter()

def on_run_simulation_end(self) -> None:
    """Callback before end of the main function."""
    end_time = time.perf_counter()
    elapsed_time_s = end_time - self._start_time
    time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
    logger.info(f'Simulation duration: {time_str} [HH:MM:SS]')

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

class MetricAggregatorCallback(AbstractMainCallback):
    """Callback to aggregate metrics after the simulation ends."""

    def __init__(self, metric_save_path: str, metric_aggregators: List[AbstractMetricAggregator]):
        """Callback to handle metric files at the end of process."""
        self._metric_save_path = Path(metric_save_path)
        self._metric_aggregators = metric_aggregators

    def on_run_simulation_end(self) -> None:
        """Callback before end of the main function."""
        start_time = time.perf_counter()
        if not is_s3_path(self._metric_save_path) and (not self._metric_save_path.exists()):
            return
        for metric_aggregator in self._metric_aggregators:
            metric_dataframes = {}
            if is_s3_path(self._metric_save_path):
                metrics = [path for path in list_files_in_directory(self._metric_save_path) if path.suffix == '.parquet']
            else:
                metrics = list(self._metric_save_path.rglob('*.parquet'))
            if not metric_aggregator.challenge:
                challenge_metrics = list(metrics)
            else:
                challenge_metrics = [path for path in metrics if metric_aggregator.challenge in str(path)]
            for file in challenge_metrics:
                try:
                    metric_statistic_dataframe = MetricStatisticsDataFrame.load_parquet(file)
                    metric_statistic_name = metric_statistic_dataframe.metric_statistic_name
                    metric_dataframes[metric_statistic_name] = metric_statistic_dataframe
                except (FileNotFoundError, Exception) as e:
                    logger.info(f'Cannot load the file: {file}, error: {e}')
            if metric_dataframes:
                logger.info(f'Running metric aggregator: {metric_aggregator.name}')
                metric_aggregator(metric_dataframes=metric_dataframes)
            else:
                logger.warning(f'{metric_aggregator.name}: No metric files found for aggregation!')
                logger.warning("If you didn't expect this, ensure that the challenge name is part of your submitted job name.")
        end_time = time.perf_counter()
        elapsed_time_s = end_time - start_time
        time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
        logger.info(f'Metric aggregator: {time_str} [HH:MM:SS]')

def on_run_simulation_end(self) -> None:
    """Callback before end of the main function."""
    start_time = time.perf_counter()
    if not is_s3_path(self._metric_save_path) and (not self._metric_save_path.exists()):
        return
    for metric_aggregator in self._metric_aggregators:
        metric_dataframes = {}
        if is_s3_path(self._metric_save_path):
            metrics = [path for path in list_files_in_directory(self._metric_save_path) if path.suffix == '.parquet']
        else:
            metrics = list(self._metric_save_path.rglob('*.parquet'))
        if not metric_aggregator.challenge:
            challenge_metrics = list(metrics)
        else:
            challenge_metrics = [path for path in metrics if metric_aggregator.challenge in str(path)]
        for file in challenge_metrics:
            try:
                metric_statistic_dataframe = MetricStatisticsDataFrame.load_parquet(file)
                metric_statistic_name = metric_statistic_dataframe.metric_statistic_name
                metric_dataframes[metric_statistic_name] = metric_statistic_dataframe
            except (FileNotFoundError, Exception) as e:
                logger.info(f'Cannot load the file: {file}, error: {e}')
        if metric_dataframes:
            logger.info(f'Running metric aggregator: {metric_aggregator.name}')
            metric_aggregator(metric_dataframes=metric_dataframes)
        else:
            logger.warning(f'{metric_aggregator.name}: No metric files found for aggregation!')
            logger.warning("If you didn't expect this, ensure that the challenge name is part of your submitted job name.")
    end_time = time.perf_counter()
    elapsed_time_s = end_time - start_time
    time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
    logger.info(f'Metric aggregator: {time_str} [HH:MM:SS]')

def run_simulation(sim_runner: AbstractRunner, exit_on_failure: bool=False) -> RunnerReport:
    """
    Proxy for calling simulation.
    :param sim_runner: A simulation runner which will execute all batched simulations.
    :param exit_on_failure: If true, raises an exception when the simulation fails.
    :return report for the simulation.
    """
    start_time = time.perf_counter()
    try:
        return sim_runner.run()
    except Exception as e:
        error = traceback.format_exc()
        logger.warning('----------- Simulation failed: with the following trace:')
        traceback.print_exc()
        logger.warning(f'Simulation failed with error:\n {e}')
        failed_scenarios = f'[{sim_runner.scenario.log_name}, {sim_runner.scenario.scenario_name}]\n'
        logger.warning(f'\nFailed simulation [log,token]:\n {failed_scenarios}')
        logger.warning('----------- Simulation failed!')
        if exit_on_failure:
            raise RuntimeError('Simulation failed')
        end_time = time.perf_counter()
        report = RunnerReport(succeeded=False, error_message=error, start_time=start_time, end_time=end_time, planner_report=None, scenario_name=sim_runner.scenario.scenario_name, planner_name=sim_runner.planner.name(), log_name=sim_runner.scenario.log_name)
        return report

class MetricRunner(AbstractRunner):
    """Manager which executes metrics with multiple simulation logs."""

    def __init__(self, simulation_log: SimulationLog, metric_callback: MetricCallback) -> None:
        """
        Initialize the metric manager.
        :param simulation_log: A simulation log.
        :param metric_callback: A metric callback.
        """
        self._simulation_log = simulation_log
        self._metric_callback = metric_callback

    def run(self) -> RunnerReport:
        """
        Run through all metric runners with simulation logs.
        :return A list of runner reports.
        """
        start_time = time.perf_counter()
        report = RunnerReport(succeeded=True, error_message=None, start_time=start_time, end_time=None, planner_report=None, scenario_name=self._simulation_log.scenario.scenario_name, planner_name=self._simulation_log.planner.name(), log_name=self._simulation_log.scenario.log_name)
        run_metric_engine(metric_engine=self._metric_callback.metric_engine, scenario=self._simulation_log.scenario, history=self._simulation_log.simulation_history, planner_name=self._simulation_log.planner.name())
        enc_time = time.perf_counter()
        report.end_time = enc_time
        return report

    @property
    def scenario(self) -> AbstractScenario:
        """
        :return: Get the scenario.
        """
        return self._simulation_log.scenario

    @property
    def planner(self) -> AbstractPlanner:
        """
        :return: Get a planner.
        """
        return self._simulation_log.planner

def run(self) -> RunnerReport:
    """
        Run through all metric runners with simulation logs.
        :return A list of runner reports.
        """
    start_time = time.perf_counter()
    report = RunnerReport(succeeded=True, error_message=None, start_time=start_time, end_time=None, planner_report=None, scenario_name=self._simulation_log.scenario.scenario_name, planner_name=self._simulation_log.planner.name(), log_name=self._simulation_log.scenario.log_name)
    run_metric_engine(metric_engine=self._metric_callback.metric_engine, scenario=self._simulation_log.scenario, history=self._simulation_log.simulation_history, planner_name=self._simulation_log.planner.name())
    enc_time = time.perf_counter()
    report.end_time = enc_time
    return report

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

def _get_time(self) -> float:
    return time.perf_counter()

class SimulationLogCallback(AbstractCallback):
    """
    Callback for simulation logging/object serialization to disk.
    """

    def __init__(self, output_directory: Union[str, pathlib.Path], simulation_log_dir: Union[str, pathlib.Path], serialization_type: str, worker_pool: Optional[WorkerPool]=None):
        """
        Construct simulation log callback.
        :param output_directory: where scenes should be serialized.
        :param simulation_log_dir: Folder where to save simulation logs.
        :param serialization_type: A way to serialize output, options: ["json", "pickle", "msgpack"].
        """
        available_formats = ['pickle', 'msgpack']
        if serialization_type not in available_formats:
            raise ValueError(f'The simulation log callback will not store files anywhere!Choose at least one format from {available_formats} instead of {serialization_type}!')
        self._output_directory = pathlib.Path(output_directory) / simulation_log_dir
        self._serialization_type = serialization_type
        if serialization_type == 'pickle':
            file_suffix = '.pkl.xz'
        elif serialization_type == 'msgpack':
            file_suffix = '.msgpack.xz'
        else:
            raise ValueError(f'Unknown option: {serialization_type}')
        self._file_suffix = file_suffix
        self._pool = worker_pool
        self._futures: List[Future[None]] = []

    @property
    def futures(self) -> List[Future[None]]:
        """
        Returns a list of futures, eg. for the main process to block on.
        :return: any futures generated by running any part of the callback asynchronously.
        """
        return self._futures

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """
        Create directory at initialization
        :param setup: simulation setup
        :param planner: planner before initialization
        """
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
        if not is_s3_path(scenario_directory):
            scenario_directory.mkdir(exist_ok=True, parents=True)

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """Inherited, see superclass."""
        pass

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
        On reached_end validate that all steps were correctly serialized.
        :param setup: simulation setup.
        :param planner: planner when simulation ends.
        :param history: resulting from simulation.
        """
        number_of_scenes = len(history)
        if number_of_scenes == 0:
            raise RuntimeError('Number of scenes has to be greater than 0')
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
        scenario = setup.scenario
        file_name = scenario_directory / (scenario.scenario_name + self._file_suffix)
        if self._pool is not None:
            self._futures = []
            self._futures.append(self._pool.submit(Task(_save_log_to_file, num_cpus=1, num_gpus=0), file_name, scenario, planner, history))
        else:
            _save_log_to_file(file_name, scenario, planner, history)

    def _get_scenario_folder(self, planner_name: str, scenario: AbstractScenario) -> pathlib.Path:
        """
        Compute scenario folder directory where all files will be stored.
        :param planner_name: planner name.
        :param scenario: for which to compute directory name.
        :return directory path.
        """
        return self._output_directory / planner_name / scenario.scenario_type / scenario.log_name / scenario.scenario_name

def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """
        On reached_end validate that all steps were correctly serialized.
        :param setup: simulation setup.
        :param planner: planner when simulation ends.
        :param history: resulting from simulation.
        """
    number_of_scenes = len(history)
    if number_of_scenes == 0:
        raise RuntimeError('Number of scenes has to be greater than 0')
    scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
    scenario = setup.scenario
    file_name = scenario_directory / (scenario.scenario_name + self._file_suffix)
    if self._pool is not None:
        self._futures = []
        self._futures.append(self._pool.submit(Task(_save_log_to_file, num_cpus=1, num_gpus=0), file_name, scenario, planner, history))
    else:
        _save_log_to_file(file_name, scenario, planner, history)

class MetricCallback(AbstractCallback):
    """Callback for computing metrics at the end of the simulation."""

    def __init__(self, metric_engine: MetricsEngine, worker_pool: Optional[WorkerPool]=None):
        """
        Build A metric callback.
        :param metric_engine: Metric Engine.
        """
        self._metric_engine = metric_engine
        self._pool = worker_pool
        self._futures: List[Future[None]] = []

    @property
    def metric_engine(self) -> MetricsEngine:
        """
        Returns metric engine.
        :return: metric engine
        """
        return self._metric_engine

    @property
    def futures(self) -> List[Future[None]]:
        """
        Returns a list of futures, eg. for the main process to block on.
        :return: any futures generated by running any part of the callback asynchronously.
        """
        return self._futures

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_initialization_end(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """Inherited, see superclass."""
        pass

    def on_step_end(self, setup: SimulationSetup, planner: AbstractPlanner, sample: SimulationHistorySample) -> None:
        """Inherited, see superclass."""
        pass

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
        """Inherited, see superclass."""
        if self._pool is not None:
            self._futures = []
            self._futures.append(self._pool.submit(Task(run_metric_engine, num_cpus=1, num_gpus=0), metric_engine=self._metric_engine, history=history, scenario=setup.scenario, planner_name=planner.name()))
        else:
            run_metric_engine(metric_engine=self._metric_engine, history=history, scenario=setup.scenario, planner_name=planner.name())

def on_simulation_end(self, setup: SimulationSetup, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """Inherited, see superclass."""
    if self._pool is not None:
        self._futures = []
        self._futures.append(self._pool.submit(Task(run_metric_engine, num_cpus=1, num_gpus=0), metric_engine=self._metric_engine, history=history, scenario=setup.scenario, planner_name=planner.name()))
    else:
        run_metric_engine(metric_engine=self._metric_engine, history=history, scenario=setup.scenario, planner_name=planner.name())

class LightningModuleWrapper(pl.LightningModule):
    """
    Lightning module that wraps the training/validation/testing procedure and handles the objective/metric computation.
    """

    def __init__(self, model: TorchModuleWrapper, objectives: List[AbstractObjective], metrics: List[AbstractTrainingMetric], batch_size: int, optimizer: Optional[DictConfig]=None, lr_scheduler: Optional[DictConfig]=None, warm_up_lr_scheduler: Optional[DictConfig]=None, objective_aggregate_mode: str='mean') -> None:
        """
        Initializes the class.

        :param model: pytorch model
        :param objectives: list of learning objectives used for supervision at each step
        :param metrics: list of planning metrics computed at each step
        :param batch_size: batch_size taken from dataloader config
        :param optimizer: config for instantiating optimizer. Can be 'None' for older models.
        :param lr_scheduler: config for instantiating lr_scheduler. Can be 'None' for older models and when an lr_scheduler is not being used.
        :param warm_up_lr_scheduler: config for instantiating warm up lr scheduler. Can be 'None' for older models and when a warm up lr_scheduler is not being used.
        :param objective_aggregate_mode: how should different objectives be combined, can be 'sum', 'mean', and 'max'.
        """
        super().__init__()
        self.save_hyperparameters(ignore=['model'])
        self.model = model
        self.objectives = objectives
        self.metrics = metrics
        self.optimizer = optimizer
        self.lr_scheduler = lr_scheduler
        self.warm_up_lr_scheduler = warm_up_lr_scheduler
        self.objective_aggregate_mode = objective_aggregate_mode
        model_targets = {builder.get_feature_unique_name() for builder in model.get_list_of_computed_target()}
        for objective in self.objectives:
            for feature in objective.get_list_of_required_target_types():
                assert feature in model_targets, f'Objective target: "{feature}" is not in model computed targets!'
        for metric in self.metrics:
            for feature in metric.get_list_of_required_target_types():
                assert feature in model_targets, f'Metric target: "{feature}" is not in model computed targets!'

    def _step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], prefix: str) -> torch.Tensor:
        """
        Propagates the model forward and backwards and computes/logs losses and metrics.

        This is called either during training, validation or testing stage.

        :param batch: input batch consisting of features and targets
        :param prefix: prefix prepended at each artifact's name during logging
        :return: model's scalar loss
        """
        features, targets, scenarios = batch
        predictions = self.forward(features)
        objectives = self._compute_objectives(predictions, targets, scenarios)
        metrics = self._compute_metrics(predictions, targets)
        loss = aggregate_objectives(objectives, agg_mode=self.objective_aggregate_mode)
        self._log_step(loss, objectives, metrics, prefix)
        return loss

    def _compute_objectives(self, predictions: TargetsType, targets: TargetsType, scenarios: ScenarioListType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of learning objectives used for supervision given the model's predictions and targets.

        :param predictions: model's output signal
        :param targets: supervisory signal
        :return: dictionary of objective names and values
        """
        return {objective.name(): objective.compute(predictions, targets, scenarios) for objective in self.objectives}

    def _compute_metrics(self, predictions: TargetsType, targets: TargetsType) -> Dict[str, torch.Tensor]:
        """
        Computes a set of planning metrics given the model's predictions and targets.

        :param predictions: model's predictions
        :param targets: ground truth targets
        :return: dictionary of metrics names and values
        """
        return {metric.name(): metric.compute(predictions, targets) for metric in self.metrics}

    def _log_step(self, loss: torch.Tensor, objectives: Dict[str, torch.Tensor], metrics: Dict[str, torch.Tensor], prefix: str, loss_name: str='loss') -> None:
        """
        Logs the artifacts from a training/validation/test step.

        :param loss: scalar loss value
        :type objectives: [type]
        :param metrics: dictionary of metrics names and values
        :param prefix: prefix prepended at each artifact's name
        :param loss_name: name given to the loss for logging
        """
        self.log(f'loss/{prefix}_{loss_name}', loss)
        for key, value in objectives.items():
            self.log(f'objectives/{prefix}_{key}', value)
        for key, value in metrics.items():
            self.log(f'metrics/{prefix}_{key}', value)

    def training_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during training.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'train')

    def validation_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during validation.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'val')

    def test_step(self, batch: Tuple[FeaturesType, TargetsType, ScenarioListType], batch_idx: int) -> torch.Tensor:
        """
        Step called for each batch example during testing.

        :param batch: example batch
        :param batch_idx: batch's index (unused)
        :return: model's loss tensor
        """
        return self._step(batch, 'test')

    def forward(self, features: FeaturesType) -> TargetsType:
        """
        Propagates a batch of features through the model.

        :param features: features batch
        :return: model's predictions
        """
        return self.model(features)

    def configure_optimizers(self) -> Union[Optimizer, Dict[str, Union[Optimizer, _LRScheduler]]]:
        """
        Configures the optimizers and learning schedules for the training.

        :return: optimizer or dictionary of optimizers and schedules
        """
        if self.optimizer is None:
            raise RuntimeError('To train, optimizer must not be None.')
        optimizer: Optimizer = instantiate(config=self.optimizer, params=self.parameters(), lr=self.optimizer.lr)
        logger.info(f'Using optimizer: {self.optimizer._target_}')
        lr_scheduler_params: Dict[str, Union[_LRScheduler, str, int]] = build_lr_scheduler(optimizer=optimizer, lr=self.optimizer.lr, warm_up_lr_scheduler_cfg=self.warm_up_lr_scheduler, lr_scheduler_cfg=self.lr_scheduler)
        optimizer_dict: Dict[str, Any] = {}
        optimizer_dict['optimizer'] = optimizer
        if lr_scheduler_params:
            logger.info(f'Using lr_schedulers {lr_scheduler_params}')
            optimizer_dict['lr_scheduler'] = lr_scheduler_params
        return optimizer_dict if 'lr_scheduler' in optimizer_dict else optimizer_dict['optimizer']

def _compute_objectives(self, predictions: TargetsType, targets: TargetsType, scenarios: ScenarioListType) -> Dict[str, torch.Tensor]:
    """
        Computes a set of learning objectives used for supervision given the model's predictions and targets.

        :param predictions: model's output signal
        :param targets: supervisory signal
        :return: dictionary of objective names and values
        """
    return {objective.name(): objective.compute(predictions, targets, scenarios) for objective in self.objectives}

def _compute_metrics(self, predictions: TargetsType, targets: TargetsType) -> Dict[str, torch.Tensor]:
    """
        Computes a set of planning metrics given the model's predictions and targets.

        :param predictions: model's predictions
        :param targets: ground truth targets
        :return: dictionary of metrics names and values
        """
    return {metric.name(): metric.compute(predictions, targets) for metric in self.metrics}

@dataclass(frozen=True)
class S3FileContent:
    """S3 file contents."""
    filename: Optional[str] = None
    last_modified: Optional[datetime] = None
    size: Optional[int] = None

    @property
    def date_string(self) -> Optional[str]:
        """Return date string format."""
        if not self.last_modified:
            return None
        return self.last_modified.strftime('%m/%d/%Y %H:%M:%S %Z')

    @property
    def last_modified_day(self) -> Optional[str]:
        """Return last modified day."""
        if not self.last_modified:
            return None
        datetime_now = datetime.now(timezone.utc)
        difference_day = (datetime_now - self.last_modified).days
        if difference_day == 0:
            return 'Less than 24 hours'
        elif difference_day < 30:
            return f'{difference_day} days ago'
        elif 30 <= difference_day < 60:
            return 'a month ago'
        else:
            return f'{difference_day / 30} months ago'

    def kb_size(self, decimals: int=2) -> Optional[float]:
        """
        Return file size in KB.
        :param decimals: Decimal points.
        """
        if not self.size:
            return None
        return float(np.round(self.size / 1024, decimals))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the class.
        :return A dict of object variables.
        """
        return {'filename': self.filename, 'last_modified': str(self.last_modified), 'size': self.size}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> S3FileContent:
        """
        Deserialize data to s3 file content.
        :param data: A dictionary of data.
        :return S3FileContent after loaded the data.
        """
        return S3FileContent(filename=data['filename'], last_modified=datetime.fromisoformat(data['last_modified']), size=data['size'])

@property
def date_string(self) -> Optional[str]:
    """Return date string format."""
    if not self.last_modified:
        return None
    return self.last_modified.strftime('%m/%d/%Y %H:%M:%S %Z')

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

def render() -> None:
    """Wrapper for the actual render logic, for multi-threading compatibility."""
    self._render_map_polygon_layers(main_figure)
    self._render_map_line_layers(main_figure)

def render_map_dependent() -> None:
    """Wrapper for the map-dependent parts of the rendering logic."""
    self._load_map_data(main_figure=main_figure)
    main_figure.update_map_dependent_data_sources()
    self._render_map(main_figure=main_figure)

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

class CloudTab:
    """Cloud tab in nuboard."""

    def __init__(self, doc: Document, configuration_tab: ConfigurationTab, s3_bucket: Optional[str]=''):
        """
        Cloud tab for remote connection features.
        :param doc: Bokeh HTML document.
        :param configuration_tab: Configuration tab.
        :param s3_bucket: Aws s3 bucket name.
        """
        self._doc = doc
        self._configuration_tab = configuration_tab
        self._nuplan_exp_root = os.getenv('NUPLAN_EXP_ROOT', None)
        assert self._nuplan_exp_root is not None, 'Please set environment variable: NUPLAN_EXP_ROOT!'
        download_path = Path(self._nuplan_exp_root)
        download_path.mkdir(parents=True, exist_ok=True)
        self._default_datasource_dict = dict(object=['-'], last_modified=['-'], timestamp=['-'], size=['-'])
        self._s3_content_datasource = ColumnDataSource(data=self._default_datasource_dict)
        self._selected_column = TextInput()
        self._selected_row = TextInput()
        self.s3_bucket_name = Div(**S3TabBucketNameConfig.get_config())
        self.s3_bucket_name.js_on_change('text', S3TabDataTableUpdateJSCode.get_js_code())
        self.s3_error_text = Div(**S3TabErrorTextConfig.get_config())
        self.s3_download_text_input = TextInput(**S3TabDownloadTextInputConfig.get_config())
        self.s3_download_button = Button(**S3TabDownloadButtonConfig.get_config())
        self.s3_download_button.on_click(self._s3_download_button_on_click)
        self.s3_download_button.js_on_click(S3TabLoadingJSCode.get_js_code())
        self.s3_download_button.js_on_change('disabled', S3TabDownloadUpdateJSCode.get_js_code())
        self.s3_bucket_text_input = TextInput(**S3TabBucketTextInputConfig.get_config(), value=s3_bucket)
        self.s3_access_key_id_text_input = TextInput(**S3TabS3AccessKeyIDTextInputConfig.get_config())
        self.s3_secret_access_key_password_input = PasswordInput(**S3TabS3SecretAccessKeyPasswordTextInputConfig.get_config())
        self.s3_bucket_prefix_text_input = TextInput(**S3TabS3BucketPrefixTextInputConfig.get_config())
        self.s3_modal_query_btn = Button(**S3TabS3ModalQueryButtonConfig.get_config())
        self.s3_modal_query_btn.on_click(self._s3_modal_query_on_click)
        self.s3_modal_query_btn.js_on_click(S3TabLoadingJSCode.get_js_code())
        self._default_columns = [TableColumn(**S3TabObjectColumnConfig.get_config()), TableColumn(**S3TabLastModifiedColumnConfig.get_config()), TableColumn(**S3TabTimeStampColumnConfig.get_config()), TableColumn(**S3TabSizeColumnConfig.get_config())]
        self._s3_content_datasource = ColumnDataSource(data=self._default_datasource_dict)
        self._s3_content_datasource.js_on_change('data', S3TabDataTableUpdateJSCode.get_js_code())
        self._s3_content_datasource.selected.js_on_change('indices', S3TabContentDataSourceOnSelected.get_js_code(selected_column=self._selected_column, selected_row=self._selected_row))
        self._s3_content_datasource.selected.js_on_change('indices', S3TabContentDataSourceOnSelectedLoadingJSCode.get_js_code(source=self._s3_content_datasource, selected_column=self._selected_column))
        self._s3_content_datasource.selected.on_change('indices', self._s3_data_source_on_selected)
        self.data_table = DataTable(source=self._s3_content_datasource, columns=self._default_columns, **S3TabDataTableConfig.get_config())
        self._s3_client: Optional[boto3.client] = None
        if s3_bucket:
            self._update_blob_store(s3_bucket=s3_bucket, s3_prefix='')

    def _update_blob_store(self, s3_bucket: str, s3_prefix: str='') -> None:
        """
        :param s3_bucket:
        :param s3_prefix:
        """
        aws_profile_name = bytes(self.s3_access_key_id_text_input.value + self.s3_secret_access_key_password_input.value, encoding='utf-8')
        hash_md5 = hashlib.md5(aws_profile_name)
        profile = hash_md5.hexdigest()
        self._s3_client = get_s3_client(aws_access_key_id=self.s3_access_key_id_text_input.value, aws_secret_access_key=self.s3_secret_access_key_password_input.value, profile_name=profile)
        s3_path = os.path.join(s3_bucket, s3_prefix)
        s3_file_result_message = get_s3_file_contents(s3_path=s3_path, include_previous_folder=True, client=self._s3_client)
        self._load_s3_contents(s3_file_result_message=s3_file_result_message)
        self.s3_error_text.text = s3_file_result_message.s3_connection_status.return_message
        if s3_file_result_message.s3_connection_status.success:
            self.s3_bucket_name.text = s3_bucket

    def _s3_modal_query_on_click(self) -> None:
        """On click function for modal query button."""
        self._update_blob_store(s3_bucket=self.s3_bucket_text_input.value, s3_prefix=self.s3_bucket_prefix_text_input.value)

    def _s3_data_source_on_selected(self, attr: str, old: List[int], new: List[int]) -> None:
        """Helper function when select a row in data source."""
        if not new:
            return
        row_index = new[0]
        self._s3_content_datasource.selected.update(indices=[])
        column_index = int(self._selected_column.value)
        s3_prefix = self.data_table.source.data['object'][row_index]
        if column_index == 0:
            if not s3_prefix or s3_prefix == '-':
                return
            if '..' in s3_prefix:
                s3_prefix = Path(s3_prefix).parents[1].name
            self._update_blob_store(s3_bucket=self.s3_bucket_text_input.value, s3_prefix=s3_prefix)
        else:
            if '..' in s3_prefix or '-' == s3_prefix:
                return
            self.s3_download_text_input.value = s3_prefix

    def _update_data_table_source(self, data_sources: Dict[str, List[Any]]) -> None:
        """Update data table source."""
        self.data_table.source.data = data_sources

    def _load_s3_contents(self, s3_file_result_message: S3FileResultMessage) -> None:
        """
        Load s3 contents into a data table.
        :param s3_file_result_message: File content and return messages from s3 connection.
        """
        file_contents = s3_file_result_message.file_contents
        if not s3_file_result_message.s3_connection_status.success or len(s3_file_result_message.file_contents) <= 1:
            default_data_sources = self._default_datasource_dict
            self._doc.add_next_tick_callback(partial(self._update_data_table_source, data_sources=default_data_sources))
        else:
            data_sources: Dict[str, List[Any]] = {'object': [], 'last_modified': [], 'timestamp': [], 'size': []}
            for file_name, content in file_contents.items():
                data_sources['object'].append(file_name)
                data_sources['last_modified'].append(content.last_modified_day if content.last_modified is not None else '')
                data_sources['timestamp'].append(content.date_string if content.date_string is not None else '')
                data_sources['size'].append(content.kb_size() if content.kb_size() is not None else '')
            self._doc.add_next_tick_callback(partial(self._update_data_table_source, data_sources=data_sources))

    def _reset_s3_download_button(self) -> None:
        """Reset s3 download button."""
        self.s3_download_button.label = 'Download'
        self.s3_download_button.disabled = False
        self.s3_download_text_input.disabled = False

    def _update_error_text_label(self, text: str) -> None:
        """Update error text message in a sequential manner."""
        self.s3_error_text.text = text

    def _s3_download_prefixes(self) -> None:
        """Download s3 prefixes and update progress in a sequential manner."""
        try:
            start_time = time.perf_counter()
            if not self._s3_client:
                raise Boto3Error('No s3 connection!')
            selected_s3_bucket = str(self.s3_bucket_name.text).strip()
            selected_s3_prefix = str(self.s3_download_text_input.value).strip()
            selected_s3_path = os.path.join(selected_s3_bucket, selected_s3_prefix)
            s3_result_file_contents = get_s3_file_contents(s3_path=selected_s3_path, client=self._s3_client, include_previous_folder=False)
            s3_nuboard_file_result = check_s3_nuboard_files(s3_result_file_contents.file_contents, s3_client=self._s3_client, s3_path=selected_s3_path)
            if not s3_nuboard_file_result.s3_connection_status.success:
                raise Boto3Error(s3_nuboard_file_result.s3_connection_status.return_message)
            if not s3_result_file_contents.file_contents:
                raise Boto3Error(f'No objects exist in the path: {selected_s3_path}')
            self._download_s3_file_contents(s3_result_file_contents=s3_result_file_contents, selected_s3_bucket=selected_s3_bucket)
            self._update_s3_nuboard_file_main_path(s3_nuboard_file_result=s3_nuboard_file_result, selected_prefix=selected_s3_prefix)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            successful_message = f'Downloaded to {self._nuplan_exp_root} and took {elapsed_time:.4f} seconds'
            logger.info('Downloaded to {} and took {:.4f} seconds'.format(self._nuplan_exp_root, elapsed_time))
            self._doc.add_next_tick_callback(partial(self._update_error_text_label, text=successful_message))
        except Exception as e:
            logger.info(str(e))
            self.s3_error_text.text = str(e)
        self._doc.add_next_tick_callback(self._reset_s3_download_button)

    def _update_s3_nuboard_file_main_path(self, s3_nuboard_file_result: S3NuBoardFileResultMessage, selected_prefix: str) -> None:
        """
        Update nuboard file simulation and metric main path.
        :param s3_nuboard_file_result: S3 nuboard file result.
        :param selected_prefix: Selected prefix on s3.
        """
        nuboard_file = s3_nuboard_file_result.nuboard_file
        nuboard_filename = s3_nuboard_file_result.nuboard_filename
        if not nuboard_file or not nuboard_filename or (not self._nuplan_exp_root):
            return
        main_path = Path(self._nuplan_exp_root) / selected_prefix
        nuboard_file.simulation_main_path = str(main_path)
        nuboard_file.metric_main_path = str(main_path)
        metric_path = main_path / nuboard_file.metric_folder
        if not metric_path.exists():
            metric_path.mkdir(parents=True, exist_ok=True)
        simulation_path = main_path / nuboard_file.simulation_folder
        if not simulation_path.exists():
            simulation_path.mkdir(parents=True, exist_ok=True)
        aggregator_metric_path = main_path / nuboard_file.aggregator_metric_folder
        if not aggregator_metric_path.exists():
            aggregator_metric_path.mkdir(parents=True, exist_ok=True)
        save_path = main_path / nuboard_filename
        nuboard_file.save_nuboard_file(save_path)
        logger.info('Updated nubBard main path in {} to {}'.format(save_path, main_path))
        self._configuration_tab.add_nuboard_file_to_experiments(nuboard_file=s3_nuboard_file_result.nuboard_file)

    def _download_s3_file_contents(self, s3_result_file_contents: S3FileResultMessage, selected_s3_bucket: str) -> None:
        """
        Download s3 file contents.
        :param s3_result_file_contents: S3 file result contents.
        :param selected_s3_bucket: Selected s3 bucket name.
        """
        for index, (file_name, content) in enumerate(s3_result_file_contents.file_contents.items()):
            if '..' in file_name:
                continue
            s3_path = os.path.join(selected_s3_bucket, file_name)
            if not file_name.endswith('/'):
                s3_connection_message = download_s3_file(s3_path=s3_path, s3_client=self._s3_client, file_content=content, save_path=self._nuplan_exp_root)
            else:
                s3_connection_message = download_s3_path(s3_path=s3_path, s3_client=self._s3_client, save_path=self._nuplan_exp_root)
            if s3_connection_message.success:
                text_message = f'Downloaded {file_name} ({index + 1} / {len(s3_result_file_contents.file_contents)})'
                logger.info('Downloaded {} / ({}/{})'.format(file_name, index + 1, len(s3_result_file_contents.file_contents)))
                self._doc.add_next_tick_callback(partial(self._update_error_text_label, text=text_message))

    def _s3_download_button_on_click(self) -> None:
        """Function to call when the download button is click."""
        selected_s3_bucket = str(self.s3_bucket_name.text).strip()
        self.s3_download_button.label = 'Downloading...'
        self.s3_download_button.disabled = True
        self.s3_download_text_input.disabled = True
        if not selected_s3_bucket:
            self.s3_error_text.text = 'Please connect to a s3 bucket'
            self._doc.add_next_tick_callback(self._reset_s3_download_button)
            return
        selected_s3_prefix = str(self.s3_download_text_input.value).strip()
        if not selected_s3_prefix:
            self.s3_error_text.text = 'Please input a prefix'
            self._doc.add_next_tick_callback(self._reset_s3_download_button)
            return
        self._doc.add_next_tick_callback(self._s3_download_prefixes)

def _s3_modal_query_on_click(self) -> None:
    """On click function for modal query button."""
    self._update_blob_store(s3_bucket=self.s3_bucket_text_input.value, s3_prefix=self.s3_bucket_prefix_text_input.value)

def _s3_data_source_on_selected(self, attr: str, old: List[int], new: List[int]) -> None:
    """Helper function when select a row in data source."""
    if not new:
        return
    row_index = new[0]
    self._s3_content_datasource.selected.update(indices=[])
    column_index = int(self._selected_column.value)
    s3_prefix = self.data_table.source.data['object'][row_index]
    if column_index == 0:
        if not s3_prefix or s3_prefix == '-':
            return
        if '..' in s3_prefix:
            s3_prefix = Path(s3_prefix).parents[1].name
        self._update_blob_store(s3_bucket=self.s3_bucket_text_input.value, s3_prefix=s3_prefix)
    else:
        if '..' in s3_prefix or '-' == s3_prefix:
            return
        self.s3_download_text_input.value = s3_prefix

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

def _click_planner_checkbox_group(self, attr: Any) -> None:
    """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
    if not self._aggregated_data and (not self._histogram_edges):
        return
    self._histogram_figures = self._render_histograms()
    self._doc.add_next_tick_callback(self._update_histogram_layouts)

def _update_histograms(self) -> None:
    """Update histograms."""
    self._aggregated_data = self._aggregate_statistics()
    aggregated_scenario_type_score_data = self._aggregate_scenario_type_score_histogram()
    self._aggregated_data.update(aggregated_scenario_type_score_data)
    self._histogram_edges = compute_histogram_edges(aggregated_data=self._aggregated_data, bins=self._bins)
    self._histogram_figures = self._render_histograms()
    self._doc.add_next_tick_callback(self._update_histogram_layouts)

def construct_dataframe(log_name: str, scenario_name: str, scenario_type: str, planner_name: str, metric_statistics: MetricStatistics) -> Dict[str, Any]:
    """
    Construct a metric dataframe for metric results.
    :param log_name: A log name.
    :param scenario_name: Scenario name.
    :param scenario_type: Scenario type.
    :param planner_name: Planner name.
    :param metric_statistics: Metric statistics.
    :return A pandas dataframe for metric statistics.
    """
    statistic_columns = {'log_name': log_name, 'scenario_name': scenario_name, 'scenario_type': scenario_type, 'planner_name': planner_name, 'metric_computator': metric_statistics.metric_computator, 'metric_statistics_name': metric_statistics.name}
    statistic_columns.update(metric_statistics.serialize_dataframe())
    return statistic_columns

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

class AbstractMetricAggregator(metaclass=ABCMeta):
    """Interface for metric aggregator"""

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the metric aggregator name
        :return the metric aggregator name.
        """
        pass

    @property
    @abstractmethod
    def final_metric_score(self) -> Optional[float]:
        """Returns the final metric score."""
        pass

    @abstractmethod
    def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
        """
        Run an aggregator to generate an aggregated parquet file
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
        pass

    @staticmethod
    def _save_with_metadata(dataframe: pandas.DataFrame, save_path: Path, metadata: Dict[str, str]) -> None:
        """
        Save to a parquet file with additional metadata using pyarrow
        :param dataframe: Pandas dataframe
        :param save_path: Path to save the dataframe.
        """
        pyarrow_table = pyarrow.Table.from_pandas(df=dataframe)
        schema_metadata = pyarrow_table.schema.metadata
        schema_metadata.update(metadata)
        updated_schema = pyarrow_table.schema.with_metadata(schema_metadata)
        pyarrow_table = pyarrow_table.cast(updated_schema)
        pq.write_table(pyarrow_table, str(save_path))

    @staticmethod
    def _save_parquet(dataframe: pandas.DataFrame, save_path: Path) -> None:
        """
        Save dataframe to a parquet file.
        The path can be local or s3.
        :param dataframe: Pandas dataframe.
        :param save_path: Path to save the dataframe.
        """
        dataframe.to_parquet(safe_path_to_string(save_path))

    @abstractmethod
    def read_parquet(self) -> None:
        """Read a parquet file, and update the dataframe."""
        pass

    @property
    @abstractmethod
    def parquet_file(self) -> Path:
        """Getter for the path to the generated parquet file."""
        pass

    @property
    @abstractmethod
    def challenge(self) -> Optional[str]:
        """Returns the name of the challenge, if applicable."""
        pass

@staticmethod
def _save_with_metadata(dataframe: pandas.DataFrame, save_path: Path, metadata: Dict[str, str]) -> None:
    """
        Save to a parquet file with additional metadata using pyarrow
        :param dataframe: Pandas dataframe
        :param save_path: Path to save the dataframe.
        """
    pyarrow_table = pyarrow.Table.from_pandas(df=dataframe)
    schema_metadata = pyarrow_table.schema.metadata
    schema_metadata.update(metadata)
    updated_schema = pyarrow_table.schema.with_metadata(schema_metadata)
    pyarrow_table = pyarrow_table.cast(updated_schema)
    pq.write_table(pyarrow_table, str(save_path))

