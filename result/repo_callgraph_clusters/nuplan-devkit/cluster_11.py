# Cluster 11

def visualize_scenarios(simulation_scenario_keys: List[SimulationScenarioKey], map_factory: NuPlanMapFactory, save_path: Path, bokeh_port: int=8899) -> None:
    """
    Visualize scenarios in Bokeh.
    :param simulation_scenario_keys: A list of simulation scenario keys.
    :param map_factory: Map factory object to use for rendering.
    :param save_path: Path where to save the scene dict.
    :param bokeh_port: Port that the server bokeh starts to render the generate the visualization will run on.
    """

    def complete_message() -> None:
        """Logging to print once the visualization is ready."""
        logger.info('Done rendering!')

    def notebook_url_callback(server_port: Optional[int]) -> str:
        """
        Callback that configures the bokeh server started by bokeh.io.show to accept requests
        from any origin. Without this, running a notebook on a port other than 8888 results in
        scenario visualizations not being rendered. For reference, see:
            - show() docs: https://docs.bokeh.org/en/latest/docs/reference/io.html#bokeh.io.show
            - downstream usage: https://github.com/bokeh/bokeh/blob/aae3034/src/bokeh/io/notebook.py#L545
        :param server_port: Passed by bokeh to indicate what port it started a server on (random by default).
        :return: Origin string and server url used by bokeh.
        """
        if server_port is None:
            return '*'
        return f'http://localhost:{server_port}'

    def bokeh_app(doc: Document) -> None:
        """
        Run bokeh app in jupyter notebook.
        :param doc: Bokeh document to render.
        """
        nuboard_file = NuBoardFile(simulation_main_path=save_path.name, simulation_folder='', metric_main_path='', metric_folder='', aggregator_metric_folder='')
        experiment_file_data = ExperimentFileData(file_paths=[nuboard_file])
        simulation_tile = SimulationTile(doc=doc, map_factory=map_factory, experiment_file_data=experiment_file_data, vehicle_parameters=get_pacifica_parameters())
        simulation_scenario_data = simulation_tile.render_simulation_tiles(simulation_scenario_keys)
        simulation_figures = [data.plot for data in simulation_scenario_data]
        simulation_layouts = column(simulation_figures)
        doc.add_root(simulation_layouts)
        doc.add_next_tick_callback(complete_message)
    for server_uuid, server in curstate().uuid_to_server.items():
        if server.port == bokeh_port:
            server.unlisten()
            logging.debug('Shut down bokeh server %s running on port %d', server_uuid, bokeh_port)
    start_event_loop_if_needed()
    show(bokeh_app, notebook_url=notebook_url_callback, port=bokeh_port)

def start_event_loop_if_needed() -> None:
    """
    Starts event loop, if there isn't already one running.
    Should be called before funcitons that require the event loop to be running (or able
    to be auto-started) to work (eg. bokeh.show).
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

class TestTutorialUtils(unittest.TestCase):
    """Unit tests for tutorial_utils.py."""

    def test_scenario_visualization_utils(self) -> None:
        """Test if scenario visualization utils work as expected."""
        visualize_nuplan_scenarios(data_root=NUPLAN_DATA_ROOT, db_files=NUPLAN_DB_FILES, map_root=NUPLAN_MAPS_ROOT, map_version=NUPLAN_MAP_VERSION)

    def test_scenario_rendering(self) -> None:
        """Test if scenario rendering works."""
        bokeh_port = 8999
        output_notebook()
        scenario_type_token_map = get_scenario_type_token_map(NUPLAN_DB_FILES)
        available_keys = list(scenario_type_token_map.keys())
        log_db, token = scenario_type_token_map[available_keys[0]][0]
        scenario = get_default_scenario_from_token(NUPLAN_DATA_ROOT, log_db, token, NUPLAN_MAPS_ROOT, NUPLAN_MAP_VERSION)
        for _ in range(2):
            visualize_scenario(scenario, bokeh_port=bokeh_port)
        for server in curstate().uuid_to_server.values():
            self.assertEqual(bokeh_port, server.port)

    def test_start_event_loop_if_needed(self) -> None:
        """Tests if start_event_loop_if_needed works."""

        async def test_fn() -> int:
            """Minimal async function"""
            return 1
        start_event_loop_if_needed()
        _ = asyncio.get_event_loop()
        start_event_loop_if_needed()
        _ = asyncio.get_event_loop()
        asyncio.run(test_fn())
        with self.assertRaises(RuntimeError):
            _ = asyncio.get_event_loop()
        start_event_loop_if_needed()
        _ = asyncio.get_event_loop()

def test_start_event_loop_if_needed(self) -> None:
    """Tests if start_event_loop_if_needed works."""

    async def test_fn() -> int:
        """Minimal async function"""
        return 1
    start_event_loop_if_needed()
    _ = asyncio.get_event_loop()
    start_event_loop_if_needed()
    _ = asyncio.get_event_loop()
    asyncio.run(test_fn())
    with self.assertRaises(RuntimeError):
        _ = asyncio.get_event_loop()
    start_event_loop_if_needed()
    _ = asyncio.get_event_loop()

def download_directory_from_s3(local_dir: Path, s3_key: Path, s3_bucket: str) -> None:
    """
    Downloads a directory to the local machine.
    :param local_dir: The directory to which to download.
    :param s3_key: The directory in S3 to download, without the bucket.
    :param s3_bucket: The bucket name to use.
    """
    asyncio.run(download_directory_from_s3_async(local_dir, s3_key, s3_bucket))

def download_file_from_s3(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
    """
    Downloads a file to local disk from S3.
    :param local_path: The path to which to download.
    :param s3_key: The S3 path from which to download, without the bucket.
    :param s3_bucket: The bucket name to use.
    """
    asyncio.run(download_file_from_s3_async(local_path, s3_key, s3_bucket))

@retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
def upload_file_to_s3(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
    """
    Uploads a file from the local disk to S3.
    :param local_path: The local path to the file.
    :param s3_key: The S3 path for the file, without the bucket.
    :param s3_bucket: The name of the bucket to write to.
    """
    asyncio.run(upload_file_to_s3_async(local_path, s3_key, s3_bucket))

@retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
def delete_file_from_s3(s3_key: Path, s3_bucket: str) -> None:
    """
    Deletes a single file from S3.
    :param s3_key: The path pointing to the file, without the bucket.
    :param s3_bucket: The name of the bucket.
    """
    asyncio.run(delete_file_from_s3_async(s3_key, s3_bucket))

def read_text_file_contents_from_s3(s3_key: Path, s3_bucket: str) -> str:
    """
    Reads the entire contents of a text file from S3.
    :param s3_key: The path pointing to the file, without the bucket.
    :param s3_bucket: The name of the bucket.
    :return: The contents of the file, decoded as a UTF-8 string.
    """
    result: str = asyncio.run(read_text_file_contents_from_s3_async(s3_key, s3_bucket))
    return result

def read_binary_file_contents_from_s3(s3_key: Path, s3_bucket: str) -> bytes:
    """
    Reads the entire contents of a file from S3.
    :param s3_key: The path pointing to the file, without the bucket.
    :param s3_bucket: The name of the bucket.
    :return: The contents of the file.
    """
    result: bytes = asyncio.run(read_binary_file_contents_from_s3_async(s3_key, s3_bucket))
    return result

@retry(RETRYABLE_EXCEPTIONS, backoff=2, tries=7, delay=0.5, jitter=(0.5, 3))
def check_s3_path_exists(s3_path: Optional[str]) -> bool:
    """
    Check whether the S3 path exists.
    If "None" is passed, then the return will be false, because a "None" path will never exist.
    :param s3_path: S3 path to check.
    :return: Whether the path exists or not.
    """
    if s3_path is None:
        return False
    result: bool = asyncio.run(check_s3_path_exists_async(s3_path))
    return result

def check_s3_object_exists(s3_key: Path, s3_bucket: str) -> bool:
    """
    Checks if an object in S3 exists.
    Returns False if the path is to a directory.
    :param s3_key: The path to list, without the bucket.
    :param s3_bucket: The bucket to list.
    :return: True if the object exists, false otherwise.
    """
    result: bool = asyncio.run(check_s3_object_exists_async(s3_key, s3_bucket))
    return result

def list_files_in_s3_directory(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
    """
    Lists the files available in a particular S3 directory.
    :param s3_key: The path to list, without the bucket.
    :param s3_bucket: The bucket to list.
    :param filter_suffix: Optional suffix to filter S3 filenames with.
    :return: The s3 keys of files in the folder.
    """
    result: List[Path] = asyncio.run(list_files_in_s3_directory_async(s3_key, s3_bucket, filter_suffix))
    return result

def get_cache_metadata_paths(s3_key: Path, s3_bucket: str, metadata_folder: str='metadata', filter_suffix: str='csv') -> List[str]:
    """
    Find metadata file paths in S3 cache path provided.
    :param s3_key: The path of cache outputs.
    :param s3_bucket: The bucket of cache outputs.
    :param metadata_folder: Metadata folder name.
    :param filter_suffix: Optional suffix to filter S3 filenames with.
    :return: List of S3 filenames discovered.
    """
    result: List[str] = asyncio.run(get_cache_metadata_paths_async(s3_key, s3_bucket, metadata_folder, filter_suffix))
    return result

def save_buffer(output_path: Path, buf: bytes) -> None:
    """
    Saves a buffer to file synchronously.
    The path can either be local or S3.
    :param output_path: The output path to which to save.
    :param buf: The byte buffer to save.
    """
    asyncio.run(_save_buffer_async(output_path, buf))

def save_object_as_pickle(output_path: Path, obj: Any) -> None:
    """
    Pickles the output object and saves it to the provided path.
    The path can be a local path or an S3 path.
    :param output_path: The output path to which to save.
    :param obj: The object to save. Must be picklable.
    """
    asyncio.run(save_object_as_pickle_async(output_path, obj))

def save_text(output_path: Path, text: str) -> None:
    """
    Saves the provided text string to the given output path.
    The path can be a local path or an S3 path.
    :param output_path: The output path to which to save.
    :param obj: The text to save.
    """
    asyncio.run(save_text_async(output_path, text))

def read_text(path: Path) -> str:
    """
    Reads a text file from the provided path.
    The path can be a local path or an S3 path.
    :param path: The path to read.
    :return: The text of the file.
    """
    result: str = asyncio.run(read_binary_async(path)).decode('utf-8')
    return result

def read_pickle(path: Path) -> Any:
    """
    Reads an object as a pickle file from the provided path.
    The path can be a local path or an S3 path.
    :param path: The path to read.
    :return: The depickled object.
    """
    return asyncio.run(read_pickle_async(path))

def read_binary(path: Path) -> bytes:
    """
    Reads binary data from the provided path into memory.
    The path can be a local path or an S3 path.
    :param path: The path to read.
    :return: The contents of the file, in binary format.
    """
    result: bytes = asyncio.run(read_binary_async(path))
    return result

def path_exists(path: Path, include_directories: bool=True) -> bool:
    """
    Checks to see if a path exists.
    The path can be a local path or an S3 path.
    This method does not examine the file contents.
        That is, a file that exists and empty will return True.
    :param path: The path to check for existance.
    :param include_directories: Whether or not directories count as paths.
    :return: True if the path exists, False otherwise.
    """
    result: bool = asyncio.run(path_exists_async(path, include_directories=include_directories))
    return result

def list_files_in_directory(path: Path) -> List[Path]:
    """
    Returns a list of the string file paths in a directory.
    The path can be a local path or an S3 path.
    :param path: The path to list.
    :return: List of file paths in the folder.
    """
    result: List[Path] = asyncio.run(list_files_in_directory_async(path))
    return result

def delete_file(path: Path) -> None:
    """
    Deletes a single file.
    The path can be a local path or an S3 path.
    :param path: Path of file to delete.
    """
    asyncio.run(delete_file_async(path))

class TestMetricRunner(unittest.TestCase):
    """Tests MetricRunner class which is computing metric."""

    def setUp(self) -> None:
        """Setup Mock classes."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.scenario = MockAbstractScenario(number_of_past_iterations=10)
        self.history = SimulationHistory(self.scenario.map_api, self.scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=self.scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
        self.history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=self.scenario.get_traffic_light_status_at_iteration(0)))
        save_path = Path(self.tmp_dir.name)
        planner = SimplePlanner(2, 0.5, [0, 0])
        self.simulation_log = SimulationLog(file_path=save_path / 'simulation_logs', simulation_history=self.history, scenario=self.scenario, planner=planner)
        self.metric_engine = MetricsEngine(metrics=[], main_save_path=save_path / 'metrics')
        self.metric_callback = MetricCallback(metric_engine=self.metric_engine)
        self.metric_runner = MetricRunner(simulation_log=self.simulation_log, metric_callback=self.metric_callback)

    def tearDown(self) -> None:
        """Clean up folders."""
        self.tmp_dir.cleanup()

    def test_run_metric_runner(self) -> None:
        """Test to run metric_runner."""
        self.metric_runner.run()

def test_run_metric_runner(self) -> None:
    """Test to run metric_runner."""
    self.metric_runner.run()

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Execute all available challenges simultaneously on the same scenario.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    """
    nuboard = initialize_nuboard(cfg)
    nuboard.run()

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

def get_scenarios(self, scenario_filter: ScenarioFilter, worker: WorkerPool) -> List[AbstractScenario]:
    """Implemented. See interface."""
    scenario_dict = self._create_scenarios(scenario_filter, worker)
    filter_wrappers = self._create_filter_wrappers(scenario_filter, worker)
    for filter_wrapper in filter_wrappers:
        scenario_dict = filter_wrapper.run(scenario_dict)
    return scenario_dict_to_list(scenario_dict, shuffle=scenario_filter.shuffle)

def _filter_scenarios(scenario_dict: ScenarioDict, total_num_scenarios: int, required_num_scenarios: int, randomize: bool) -> ScenarioDict:
    """
    Filters scenarios until we reach the user specified number of scenarios. Scenarios with scenario_type DEFAULT_SCENARIO_NAME are removed first either randomly or with equisampling, and subsequently
    the other scenarios are sampled randomly or with equisampling if necessary.
    :param scenario_dict: Dictionary containining a mapping of scenario_type to a list of the AbstractScenario objects.
    :param total_num_scenarios: Total number of scenarios in the scenario dictionary.
    :param required_num_scenarios: Number of scenarios desired.
    :param randomize: boolean to decide whether to randomize the sampling of scenarios.
    :return: Scenario dictionary with the required number of scenarios.
    """

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
    if total_num_scenarios == 0 or required_num_scenarios == 0 or len(scenario_dict) == 0:
        return {}
    if DEFAULT_SCENARIO_NAME in scenario_dict:
        num_default_scenarios = len(scenario_dict[DEFAULT_SCENARIO_NAME])
        if total_num_scenarios - required_num_scenarios < num_default_scenarios:
            num_default_scenarios_to_keep = num_default_scenarios - (total_num_scenarios - required_num_scenarios)
            scenario_dict[DEFAULT_SCENARIO_NAME] = _filter_scenarios_from_scenario_list(scenario_dict[DEFAULT_SCENARIO_NAME], num_default_scenarios_to_keep, randomize)
            return scenario_dict
        else:
            scenario_dict.pop(DEFAULT_SCENARIO_NAME)
    scenario_list = scenario_dict_to_list(scenario_dict)
    scenario_list = _filter_scenarios_from_scenario_list(scenario_list, required_num_scenarios, randomize)
    scenario_dict = scenario_list_to_dict(scenario_list)
    return scenario_dict

