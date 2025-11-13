# Cluster 0

def construct_nuboard_hydra_paths(base_config_path: str) -> HydraConfigPaths:
    """
    Specifies relative paths to nuBoard configs to pass to hydra to declutter tutorial.
    :param base_config_path: Base config path.
    :return: Hydra config path.
    """
    common_dir = 'file://' + join(base_config_path, 'config', 'common')
    config_name = 'default_nuboard'
    config_path = join(base_config_path, 'config/nuboard')
    experiment_dir = 'file://' + join(base_config_path, 'experiments')
    return HydraConfigPaths(common_dir, config_name, config_path, experiment_dir)

def construct_simulation_hydra_paths(base_config_path: str) -> HydraConfigPaths:
    """
    Specifies relative paths to simulation configs to pass to hydra to declutter tutorial.
    :param base_config_path: Base config path.
    :return: Hydra config path.
    """
    common_dir = 'file://' + join(base_config_path, 'config', 'common')
    config_name = 'default_simulation'
    config_path = join(base_config_path, 'config', 'simulation')
    experiment_dir = 'file://' + join(base_config_path, 'experiments')
    return HydraConfigPaths(common_dir, config_name, config_path, experiment_dir)

def save_scenes_to_dir(scenario: AbstractScenario, save_dir: str, simulation_history: SimulationHistory) -> SimulationScenarioKey:
    """
    Save scenes to a directory.
    :param scenario: Scenario.
    :param save_dir: Save path.
    :param simulation_history: Simulation history.
    :return: Scenario key of simulation.
    """
    planner_name = 'tutorial_planner'
    scenario_type = scenario.scenario_type
    scenario_name = scenario.scenario_name
    log_name = scenario.log_name
    save_path = Path(save_dir)
    file = save_path / planner_name / scenario_type / log_name / scenario_name / (scenario_name + '.msgpack.xz')
    file.parent.mkdir(exist_ok=True, parents=True)
    dummy_planner = _create_dummy_simple_planner(acceleration=[5.0, 5.0])
    simulation_log = SimulationLog(planner=dummy_planner, scenario=scenario, simulation_history=simulation_history, file_path=file)
    simulation_log.save_to_file()
    return SimulationScenarioKey(planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type, nuboard_file_index=0, log_name=log_name, files=[file])

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

class TestPlannerTutorialHydra(unittest.TestCase):
    """
    Test planner tutorial Jupyter notebook hydra configuration.
    """

    def setUp(self) -> None:
        """Setup."""
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        """Clean up."""
        if Path(self.tmp_dir.name).exists():
            self.tmp_dir.cleanup()
        if ray.is_initialized():
            ray.shutdown()

    def test_hydra_paths_utils(self) -> None:
        """
        Test HydraConfigPaths utility functions for storing config paths for simulation and visualization.
        """
        simulation_hydra_paths = construct_simulation_hydra_paths(BASE_CONFIG_PATH)
        with hydra.initialize_config_dir(config_dir=simulation_hydra_paths.config_path):
            cfg = hydra.compose(config_name=simulation_hydra_paths.config_name, overrides=[f'hydra.searchpath=[{simulation_hydra_paths.common_dir}, {simulation_hydra_paths.experiment_dir}]', '+simulation=open_loop_boxes', 'log_config=false', 'scenario_builder=nuplan_mini', 'planner=simple_planner', 'scenario_filter=one_of_each_scenario_type', 'scenario_filter.limit_total_scenarios=2', 'exit_on_failure=true', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", f'group={self.tmp_dir.name}', 'experiment_name=hydra_paths_utils_test', 'output_dir=${group}/${experiment}'])
            main_simulation(cfg)
        results_dir = Path(cfg.output_dir)
        simulation_file = [str(file) for file in results_dir.iterdir() if file.is_file() and file.suffix == '.nuboard'][0]
        nuboard_hydra_paths = construct_nuboard_hydra_paths(BASE_CONFIG_PATH)
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(TEST_TIMEOUT)
        try:
            with hydra.initialize_config_dir(config_dir=nuboard_hydra_paths.config_path):
                cfg = hydra.compose(config_name=nuboard_hydra_paths.config_name, overrides=['scenario_builder=nuplan_mini', f'simulation_path={simulation_file}', f'hydra.searchpath=[{nuboard_hydra_paths.common_dir}, {nuboard_hydra_paths.experiment_dir}]', 'port_number=4555'])
                main_nuboard(cfg)
        except Exception as exc:
            signal.alarm(0)
            self.assertTrue(isinstance(exc, TimeoutError))

def setUp(self) -> None:
    """Setup."""
    self.tmp_dir = tempfile.TemporaryDirectory()

def tearDown(self) -> None:
    """Clean up."""
    if Path(self.tmp_dir.name).exists():
        self.tmp_dir.cleanup()
    if ray.is_initialized():
        ray.shutdown()

def test_hydra_paths_utils(self) -> None:
    """
        Test HydraConfigPaths utility functions for storing config paths for simulation and visualization.
        """
    simulation_hydra_paths = construct_simulation_hydra_paths(BASE_CONFIG_PATH)
    with hydra.initialize_config_dir(config_dir=simulation_hydra_paths.config_path):
        cfg = hydra.compose(config_name=simulation_hydra_paths.config_name, overrides=[f'hydra.searchpath=[{simulation_hydra_paths.common_dir}, {simulation_hydra_paths.experiment_dir}]', '+simulation=open_loop_boxes', 'log_config=false', 'scenario_builder=nuplan_mini', 'planner=simple_planner', 'scenario_filter=one_of_each_scenario_type', 'scenario_filter.limit_total_scenarios=2', 'exit_on_failure=true', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", f'group={self.tmp_dir.name}', 'experiment_name=hydra_paths_utils_test', 'output_dir=${group}/${experiment}'])
        main_simulation(cfg)
    results_dir = Path(cfg.output_dir)
    simulation_file = [str(file) for file in results_dir.iterdir() if file.is_file() and file.suffix == '.nuboard'][0]
    nuboard_hydra_paths = construct_nuboard_hydra_paths(BASE_CONFIG_PATH)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TEST_TIMEOUT)
    try:
        with hydra.initialize_config_dir(config_dir=nuboard_hydra_paths.config_path):
            cfg = hydra.compose(config_name=nuboard_hydra_paths.config_name, overrides=['scenario_builder=nuplan_mini', f'simulation_path={simulation_file}', f'hydra.searchpath=[{nuboard_hydra_paths.common_dir}, {nuboard_hydra_paths.experiment_dir}]', 'port_number=4555'])
            main_nuboard(cfg)
    except Exception as exc:
        signal.alarm(0)
        self.assertTrue(isinstance(exc, TimeoutError))

def make(version: str) -> None:
    """
    Generate README.md.
    :param version: Database version.
    """
    with open('README.md', 'w') as f:
        f.write('nuPlan DB schema. Version {} \n========== \n'.format(version))
        f.write('`This file is automatically generated so do not edit this file. Stay DRY.`\n\n')
        for table in tables:
            jsontabledump(f, tables[table], table)

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

def logs(self, split_name: str) -> List[str]:
    """
        Get list of logs for the split.
        :return: The list of logs for the split.
        """
    sample_tokens = self.split(split_name)
    return list({self._db.sample[token].extraction.log.logfile for token in sample_tokens})

def get_db_filenames_from_load_path(load_path: str) -> List[str]:
    """
    Retrieve all log database filenames from a load path.
    The path can be either local or remote (S3).
    The path can represent either a single database filename (.db file) or a directory containing files.
    :param load_path: Load path, it can be a filename or list of filenames.
    :return: A list of all discovered log database filenames.
    """
    if load_path.endswith('.db'):
        if load_path.startswith('s3://'):
            assert check_s3_path_exists(load_path), f'S3 db path does not exist: {load_path}'
            os.environ['NUPLAN_DATA_ROOT_S3_URL'] = load_path.rstrip(Path(load_path).name)
        else:
            assert Path(load_path).is_file(), f'Local db path does not exist: {load_path}'
        db_filenames = [load_path]
    elif load_path.startswith('s3://'):
        db_filenames = expand_s3_dir(load_path, filter_suffix='.db')
        assert len(db_filenames) > 0, f'S3 dir does not contain any dbs: {load_path}'
        os.environ['NUPLAN_DATA_ROOT_S3_URL'] = load_path
    elif Path(load_path).expanduser().is_dir():
        db_filenames = [str(path) for path in sorted(Path(load_path).expanduser().iterdir()) if path.suffix == '.db']
    else:
        raise ValueError(f'Expected db load path to be file, dir or list of files/dirs, but got {load_path}')
    return db_filenames

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

class TestLidarPc(unittest.TestCase):
    """Tests the LidarBox class"""

    def setUp(self) -> None:
        """Sets up for the tests cases"""
        self.lidar_pc = get_test_nuplan_lidarpc()
        self.lidar_pc_with_blob = get_test_nuplan_lidarpc_with_blob()

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.inspect', autospec=True)
    def test_session(self, inspect_mock: Mock) -> None:
        """Tests the _session property"""
        session_mock = PropertyMock()
        inspect_mock.return_value = Mock()
        inspect_mock.return_value.session = session_mock
        result = self.lidar_pc._session
        inspect_mock.assert_called_once_with(self.lidar_pc)
        self.assertEqual(result, session_mock)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.simple_repr', autospec=True)
    def test_repr(self, simple_repr_mock: Mock) -> None:
        """Tests the __repr__ method"""
        result = self.lidar_pc.__repr__()
        simple_repr_mock.assert_called_once_with(self.lidar_pc)
        self.assertEqual(result, simple_repr_mock.return_value)

    def test_log(self) -> None:
        """Tests the log property"""
        result = self.lidar_pc.log
        self.assertIsInstance(result, Log)

    def test_future_ego_pose_has_next(self) -> None:
        """Tests the future_ego_pose method when there is a future ego pose"""
        result = self.lidar_pc.future_ego_pose()
        self.assertEqual(result, self.lidar_pc.next.ego_pose)

    def test_future_ego_pose_no_next(self) -> None:
        """Tests the future_ego_pose method when there is no future ego pose"""
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.next = None
        result = lidar_pc.future_ego_pose()
        self.assertEqual(result, None)

    def test_past_ego_pose_has_prev(self) -> None:
        """Tests the past_ego_pose method when there is a past ego pose"""
        result = self.lidar_pc.past_ego_pose()
        self.assertEqual(result, self.lidar_pc.prev.ego_pose)

    def test_past_ego_pose_no_prev(self) -> None:
        """Tests the past_ego_pose method when there is no past ego pose"""
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.prev = None
        result = lidar_pc.past_ego_pose()
        self.assertEqual(result, None)

    def test_future_or_past_ego_poses_prev_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'prev')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'prev')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_prev_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=prev and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'prev')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_next_nposes(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_poses"""
        number, mode, direction = (1, 'n_poses', 'next')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_nseconds(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next, mode=n_seconds"""
        number, mode, direction = (1, 'n_seconds', 'next')
        result = self.lidar_pc.future_or_past_ego_poses(number, mode, direction)
        self.assertIsNotNone(result)

    def test_future_or_past_ego_poses_next_unknown_mode(self) -> None:
        """Tests the future_or_past_ego_poses when direction=next and mode is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'next')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    def test_future_or_past_ego_poses_unknown_direction(self) -> None:
        """Tests the future_or_past_ego_poses when direction is unknown"""
        number, mode, direction = (1, 'unknown_mode', 'unknown_direction')
        with self.assertRaises(ValueError):
            self.lidar_pc.future_or_past_ego_poses(number, mode, direction)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.LidarPointCloud.from_buffer', autospec=True)
    def test_load_channel_is_merged_point_cloud(self, from_buffer_mock: Mock) -> None:
        """Tests the load method when lidar channel is MergedPointCloud"""
        db = get_test_nuplan_db()
        result = self.lidar_pc.load(db)
        self.assertEqual(result, from_buffer_mock.return_value)

    def test_load_channel_is_not_implemented(self) -> None:
        """Tests the load method when lidar channel is not implemented"""
        db = get_test_nuplan_db()
        lidar_pc = deepcopy(self.lidar_pc)
        lidar_pc.lidar.channel = 'UnknownPointCloud'
        with self.assertRaises(NotImplementedError):
            lidar_pc.load(db)

    def test_load_bytes(self) -> None:
        """Tests the load bytes method"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.load_bytes(db)
        self.assertIsNotNone(result)

    def test_path(self) -> None:
        """Tests the path property"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.path(db)
        self.assertIsInstance(result, str)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.get_boxes', autospec=True)
    def test_boxes(self, get_boxes_mock: Mock) -> None:
        """Tests the boxes method"""
        result = self.lidar_pc.boxes()
        self.assertEqual(result, get_boxes_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.pack_future_boxes', autospec=True)
    @patch('nuplan.database.nuplan_db_orm.lidar_pc.get_future_box_sequence', autospec=True)
    def test_boxes_with_future_waypoints(self, get_future_box_sequence_mock: Mock, pack_future_boxes_mock: Mock) -> None:
        """Tests the boxes_with_future_waypoints method"""
        future_horizon_len_s, future_interval_s = (1.0, 1.0)
        result = self.lidar_pc.boxes_with_future_waypoints(future_horizon_len_s, future_interval_s)
        get_future_box_sequence_mock.assert_called_once()
        pack_future_boxes_mock.assert_called_once_with(get_future_box_sequence_mock.return_value, future_interval_s, future_horizon_len_s)
        self.assertEqual(result, pack_future_boxes_mock.return_value)

    @patch('nuplan.database.nuplan_db_orm.lidar_pc.render_on_map', autospec=True)
    def test_render(self, render_on_map_mock: Mock) -> None:
        """Tests the render method"""
        db = get_test_nuplan_db()
        result = self.lidar_pc_with_blob.render(db)
        render_on_map_mock.assert_called_once()
        self.assertIsInstance(result, Axes)

    def test_past_ego_poses(self) -> None:
        """Test if past ego poses are returned correctly."""
        n_ego_poses = 4
        lidar_pc = self.lidar_pc.next.next.next
        past_ego_poses = lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='prev')
        ego_pose = lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertGreater(ego_pose.timestamp, past_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be greater than past EgoPoses.')

    def test_future_ego_poses(self) -> None:
        """Test if future ego poses are returned correctly."""
        n_ego_poses = 4
        future_ego_poses = self.lidar_pc.future_or_past_ego_poses(number=n_ego_poses, mode='n_poses', direction='next')
        ego_pose = self.lidar_pc.ego_pose
        for i in range(n_ego_poses):
            self.assertLess(ego_pose.timestamp, future_ego_poses[i].timestamp, 'Timestamps of current EgoPose must be less that future EgoPoses.')

def test_load_channel_is_not_implemented(self) -> None:
    """Tests the load method when lidar channel is not implemented"""
    db = get_test_nuplan_db()
    lidar_pc = deepcopy(self.lidar_pc)
    lidar_pc.lidar.channel = 'UnknownPointCloud'
    with self.assertRaises(NotImplementedError):
        lidar_pc.load(db)

def test_load_bytes(self) -> None:
    """Tests the load bytes method"""
    db = get_test_nuplan_db()
    result = self.lidar_pc_with_blob.load_bytes(db)
    self.assertIsNotNone(result)

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

def test_serialization(self) -> None:
    """Test whether the wrapper object can be serialized/deserialized correctly."""
    serialized_binary = pickle.dumps(self.db_wrapper)
    re_db_wrapper: NuPlanDBWrapper = pickle.loads(serialized_binary)
    self.assertEqual(self.db_wrapper.data_root, re_db_wrapper.data_root)

class TestNuPlanDB(unittest.TestCase):
    """Test main nuPlan database class."""

    def setUp(self) -> None:
        """Set up test case."""
        self.db = get_test_nuplan_db()
        self.db.add_ref()

    def test_pickle(self) -> None:
        """Test dumping and loading the object through pickle."""
        db_binary = pickle.dumps(self.db)
        re_db: NuPlanDB = pickle.loads(db_binary)
        self.assertEqual(self.db.data_root, re_db.data_root)
        self.assertEqual(self.db.name, re_db.name)
        self.assertEqual(self.db._verbose, re_db._verbose)

    def test_table_getters(self) -> None:
        """Test the table getters."""
        self.assertTrue(isinstance(self.db.category, Table))
        self.assertTrue(isinstance(self.db.camera, Table))
        self.assertTrue(isinstance(self.db.lidar, Table))
        self.assertTrue(isinstance(self.db.image, Table))
        self.assertTrue(isinstance(self.db.lidar_pc, Table))
        self.assertTrue(isinstance(self.db.lidar_box, Table))
        self.assertTrue(isinstance(self.db.track, Table))
        self.assertTrue(isinstance(self.db.scene, Table))
        self.assertTrue(isinstance(self.db.scenario_tag, Table))
        self.assertTrue(isinstance(self.db.traffic_light_status, Table))
        self.assertSetEqual(self.db.cam_channels, {'CAM_R2', 'CAM_R1', 'CAM_R0', 'CAM_F0', 'CAM_L2', 'CAM_L1', 'CAM_B0', 'CAM_L0'})
        self.assertSetEqual(self.db.lidar_channels, {'MergedPointCloud'})

    def test_nuplan_memory_usage(self) -> None:
        """
        Test that repeatedly creating and destroying nuplan DB objects does not cause memory leaks.
        """

        def spin_up_db() -> None:
            db = get_test_nuplan_db_nocache()
            db.remove_ref()
        starting_usage = 0
        ending_usage = 0
        num_iterations = 5
        hpy = guppy.hpy()
        hpy.setrelheap()
        for i in range(0, num_iterations, 1):
            spin_up_db()
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

def test_pickle(self) -> None:
    """Test dumping and loading the object through pickle."""
    db_binary = pickle.dumps(self.db)
    re_db: NuPlanDB = pickle.loads(db_binary)
    self.assertEqual(self.db.data_root, re_db.data_root)
    self.assertEqual(self.db.name, re_db.name)
    self.assertEqual(self.db._verbose, re_db._verbose)

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

@classmethod
def deserialize(cls, data: Dict[str, Any]) -> Label:
    """
        Instantiates a Label instance from serialized dictionary representation.
        :param data: Output from serialize.
        :return: Deserialized label.
        """
    return Label(name=data['name'], color=tuple((int(channel) for channel in data['color'])))

class TestLabel(unittest.TestCase):
    """Test Label Serialization."""

    def test_serialize(self) -> None:
        """Tests a serialized label are still the same after serializing."""
        label = Label('my_name', (1, 3, 4, 1))
        self.assertEqual(label, Label.deserialize(json.loads(json.dumps(label.serialize()))))

def test_serialize(self) -> None:
    """Tests a serialized label are still the same after serializing."""
    label = Label('my_name', (1, 3, 4, 1))
    self.assertEqual(label, Label.deserialize(json.loads(json.dumps(label.serialize()))))

class TestParseLabelmap(unittest.TestCase):
    """Test Parsing LabMap."""

    def setUp(self) -> None:
        """Setup function."""
        self.label1 = Label('label1', (1, 1, 1, 1))
        self.label2 = Label('label2', (2, 2, 2, 2))

    def test_empty(self) -> None:
        """Tests empty label map case."""
        id2name, id2color = parse_labelmap_dataclass({})
        self.assertIsInstance(id2name, OrderedDict)
        self.assertIsInstance(id2color, OrderedDict)
        self.assertEqual(len(id2name), 0)
        self.assertEqual(len(id2color), 0)

    def test_one(self) -> None:
        """Tests one label case."""
        num = 1
        mapping = {num: self.label1}
        id2name, id2color = parse_labelmap_dataclass(mapping)
        self.assertEqual(len(id2name), len(mapping))
        self.assertEqual(id2name[num], self.label1.name)
        self.assertEqual(len(id2color), len(mapping))
        self.assertEqual(id2color[num], self.label1.color)

    def test_multiple(self) -> None:
        """Tests multiple labels case."""
        num1, num2 = (1, 2)
        mapping = {num1: self.label1, num2: self.label2}
        id2name, id2color = parse_labelmap_dataclass(mapping)
        self.assertEqual(len(id2name), len(mapping))
        self.assertEqual(len(id2color), len(mapping))
        self.assertEqual(id2name[num1], self.label1.name)
        self.assertEqual(id2name[num2], self.label2.name)
        self.assertEqual(id2color[num1], self.label1.color)
        self.assertEqual(id2color[num2], self.label2.color)
        self.assertEqual(list(id2name.keys())[0], min(num1, num2))
        self.assertEqual(list(id2name.keys())[1], max(num1, num2))
        self.assertEqual(list(id2color.keys())[0], min(num1, num2))
        self.assertEqual(list(id2color.keys())[1], max(num1, num2))

def setUp(self) -> None:
    """Setup function."""
    self.label1 = Label('label1', (1, 1, 1, 1))
    self.label2 = Label('label2', (2, 2, 2, 2))

def pcd_to_numpy(pcd_file: str) -> npt.NDArray[np.float32]:
    """
    This function converts the pointcloud *.pcl or *.pcd files to numpy (x, y, z, i) format,
    or (x, y, z, i, t) format if a time field is present.
    :param pcd_file: Name of the point cloud file (*.pcl or *.pcd)
    :return: A numpy array of shape (n, 4) or (n, 5), dtype = np.float32
    """
    with open(pcd_file) as ifile:
        data = [line.strip() for line in ifile]
    meta = data[:10]
    assert meta[0].startswith('#'), 'First line must be comment'
    assert meta[1].startswith('VERSION'), 'Second line must be VERSION'
    fields = meta[2].split(' ')[1:]
    assert all((f in fields for f in ['x', 'y', 'z'])), 'x, y, and z fields are required'
    assert data[10] == 'DATA ascii'
    data = data[11:]
    data = [d.split(' ') for d in data]
    all_columns = np.array(data, dtype=np.float32)
    num_points = all_columns.shape[0]
    has_delta_time = PCD_TIMESTAMP_FIELD_NAME in fields
    result_shape = (num_points, 5) if has_delta_time else (num_points, 4)
    result = np.zeros(result_shape, dtype=np.float32)
    result[:, 0] = all_columns[:, fields.index('x')]
    result[:, 1] = all_columns[:, fields.index('y')]
    result[:, 2] = all_columns[:, fields.index('z')]
    if 'intensity' in fields:
        result[:, 3] = all_columns[:, fields.index('intensity')]
    if has_delta_time:
        result[:, 4] = all_columns[:, fields.index(PCD_TIMESTAMP_FIELD_NAME)]
    return result

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
def load_pcd(pcd_data: Union[IO[Any], ByteString]) -> npt.NDArray[np.float32]:
    """
        Loads a pcd file.
        :param pcd_data: File path or a file-like object or raw bytes.
        :return: <np.float: 6, n>. Point cloud matrix[(x, y, z, intensity, ring, lidar_id)].
        """
    if not isinstance(pcd_data, bytes):
        pcd_data = pcd_data.read()
    return PointCloud.parse(pcd_data).to_pcd_bin2()

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

class SimplePickleType(TypeDecorator):
    """
    Use pickle for dict/list type of objects.
    """
    impl = BLOB
    class_type: Any = None

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[bytes]:
        """Inherited, see superclass."""
        if not value:
            return None
        return pickle.dumps(value)

    def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Any:
        """Inherited, see superclass."""
        if not value:
            return None
        assert self.class_type is not None
        ret = pickle.loads(value)
        return self.class_type(ret)

def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[bytes]:
    """Inherited, see superclass."""
    if not value:
        return None
    return pickle.dumps(value)

def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Any:
    """Inherited, see superclass."""
    if not value:
        return None
    assert self.class_type is not None
    ret = pickle.loads(value)
    return self.class_type(ret)

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

@property
def table_root(self) -> str:
    """
        Get the table root.
        :return: The table root.
        """
    return str(self._filename)

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

class LocalStore(BlobStore):
    """
    Local blob store. Load blobs from local file system.
    """

    def __init__(self, root_dir: str) -> None:
        """
        Initialize LocalStore.
        :param root_dir: Root directory containing the data.
        """
        self._root_dir = root_dir
        assert os.path.isdir(self._root_dir), '%s does not exist!' % self._root_dir
        assert os.access(self._root_dir, os.R_OK | os.X_OK), 'can not read from %s' % self._root_dir

    def __reduce__(self) -> Tuple[Type[LocalStore], Tuple[str]]:
        """
        :return: Tuple of class and its constructor parameters, this is used to pickle the class.
        """
        return (self.__class__, (self._root_dir,))

    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get blob content.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :raises: BlobStoreKeyNotFound is `key` is not present in backing store.
        :return: A file-like object, use read() to get raw bytes.
        """
        path = os.path.join(self._root_dir, key)
        try:
            with open(path, 'rb') as fp:
                return io.BytesIO(fp.read())
        except FileNotFoundError as e:
            raise BlobStoreKeyNotFound(e)

    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """
        Save content to disk.
        :param key:. Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        """
        pass

    async def get_async(self, key: str) -> BinaryIO:
        """Inherited, see superclass."""
        raise NotImplementedError('Not today.')

    def exists(self, key: str) -> bool:
        """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        path = os.path.join(self._root_dir, key)
        return os.path.isfile(path)

    def put(self, key: str, value: BinaryIO) -> None:
        """
        Writes content.
        :param key: Blob path or token.
        :param value: Data to save.
        """
        if not os.access(self._root_dir, os.W_OK):
            raise RuntimeError(f'No write access to {self._root_dir}')
        path = Path(self._root_dir) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(value.read())

def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
    """
        Get blob content.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :raises: BlobStoreKeyNotFound is `key` is not present in backing store.
        :return: A file-like object, use read() to get raw bytes.
        """
    path = os.path.join(self._root_dir, key)
    try:
        with open(path, 'rb') as fp:
            return io.BytesIO(fp.read())
    except FileNotFoundError as e:
        raise BlobStoreKeyNotFound(e)

def exists(self, key: str) -> bool:
    """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
    path = os.path.join(self._root_dir, key)
    return os.path.isfile(path)

def put(self, key: str, value: BinaryIO) -> None:
    """
        Writes content.
        :param key: Blob path or token.
        :param value: Data to save.
        """
    if not os.access(self._root_dir, os.W_OK):
        raise RuntimeError(f'No write access to {self._root_dir}')
    path = Path(self._root_dir) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(value.read())

class HttpStore(BlobStore):
    """
    Http blob store. Load blobs from http file server.
    """

    def __init__(self, root_url: str) -> None:
        """
        Initialize HttpStore.
        :param root_url: Root URL containing data.
        """
        assert root_url.startswith('http://') or root_url.startswith('https://'), 'invalid url %s' % root_url
        self._root_url = root_url
        if not self._root_url.endswith('/'):
            self._root_url += '/'
        self._session = requests.Session()

    def _get(self, url: str) -> BinaryIO:
        """
        Get content from URL.
        :param url: URL containing the data.
        :return: Blob binary stream.
        """
        t0 = time.time()
        response = self._session.get(url)
        logger.debug('Done fetching {} in {} seconds.'.format(url, time.time() - t0))
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            logger.error('Can not load file from URL: {}'.format(url))
            raise RuntimeError('Can not load the file: %s from server, error: %d, msg: %s.' % (url, response.status_code, response.text))

    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get content from URL.
        :param key: File name.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: Blob binary stream.
        """
        gzip_path = self._root_url + key + '.gzip'
        if check_for_compressed and self.exists(gzip_path):
            gzip_stream = self._get(gzip_path)
            content: BinaryIO = self._extract_gzip_content(gzip_stream)
        else:
            content = self._get(key)
        return content

    async def get_async(self, key: str) -> BinaryIO:
        """Inherited, see superclass."""
        raise NotImplementedError('Not today.')

    def exists(self, key: str) -> bool:
        """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        url = self._root_url + key
        response = self._session.head(url)
        return response.status_code == 200

    def put(self, key: str, value: BinaryIO) -> None:
        """Inherited, see superclass."""
        raise NotImplementedError("'Put' operation not supported for legacy HttpStore class")

    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """Inherited, see superclass."""
        super().save_to_disk(key, check_for_compressed=check_for_compressed)

def __init__(self, root_url: str) -> None:
    """
        Initialize HttpStore.
        :param root_url: Root URL containing data.
        """
    assert root_url.startswith('http://') or root_url.startswith('https://'), 'invalid url %s' % root_url
    self._root_url = root_url
    if not self._root_url.endswith('/'):
        self._root_url += '/'
    self._session = requests.Session()

def _get(self, url: str) -> BinaryIO:
    """
        Get content from URL.
        :param url: URL containing the data.
        :return: Blob binary stream.
        """
    t0 = time.time()
    response = self._session.get(url)
    logger.debug('Done fetching {} in {} seconds.'.format(url, time.time() - t0))
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        logger.error('Can not load file from URL: {}'.format(url))
        raise RuntimeError('Can not load the file: %s from server, error: %d, msg: %s.' % (url, response.status_code, response.text))

def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
    """
        Get content from URL.
        :param key: File name.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: Blob binary stream.
        """
    gzip_path = self._root_url + key + '.gzip'
    if check_for_compressed and self.exists(gzip_path):
        gzip_stream = self._get(gzip_path)
        content: BinaryIO = self._extract_gzip_content(gzip_stream)
    else:
        content = self._get(key)
    return content

def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
    """Inherited, see superclass."""
    super().save_to_disk(key, check_for_compressed=check_for_compressed)

class S3Store(BlobStore):
    """
    S3 blob store. Load blobs from AWS S3.
    """

    def __init__(self, s3_prefix: str, profile_name: Optional[str]=None, show_progress: bool=True) -> None:
        """
        Initialize S3Store.
        :param s3_prefix: S3 path
        :param profile_name: Profile name.
        :param show_progress: Whether to show download progress.
        """
        assert s3_prefix.startswith('s3://')
        self._s3_prefix = s3_prefix
        if not self._s3_prefix.endswith('/'):
            self._s3_prefix += '/'
        self._profile_name = profile_name
        url = parse.urlparse(self._s3_prefix)
        self._bucket = url.netloc
        self._prefix = url.path.lstrip('/')
        self._client = get_s3_client(self._profile_name)
        self._show_progress = show_progress

    def __reduce__(self) -> Tuple[Type[S3Store], Tuple[Any, ...]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class.
        """
        return (self.__class__, (self._s3_prefix, self._profile_name))

    def _get_s3_location(self, key: str) -> Tuple[str, str, str]:
        """
        Get s3 location information.
        :param key: Full S3 path or bucket key of blob.
        :return: Full S3 path, bucket and key.
        """
        s3_path = key if key.startswith('s3://') else f's3://{self._bucket}/{self._prefix}{key}'
        url = parse.urlparse(s3_path)
        bucket = url.netloc
        parsed_key = url.path.lstrip('/')
        return (s3_path, bucket, parsed_key)

    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get blob content.
        :param key: Full S3 path or bucket key of blob.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: A file-like object, use read() to get raw bytes.
        """
        path, _, _ = self._get_s3_location(key)
        gzip_path = path + '.gzip'
        if check_for_compressed and self.exists(gzip_path):
            gzip_stream = self._get(key=gzip_path)
            content: BinaryIO = self._extract_gzip_content(gzip_stream)
        else:
            content = self._get(key=key)
        return content

    def _get(self, key: str, num_tries: int=7) -> BinaryIO:
        """
        Get blob content from path/key.

        Note: Occasionally S3 give a ConnectionResetError or http.client.IncompleteRead
              exception. urllib3 wraps both of these in a ProtocolError. Sometimes S3 also
              gives an "ssl.SSLError: [SSL: WRONG_VERSION_NUMBER]" error. Unfortunately the
              boto3 retrying ("max_attempts") gives up when it sees any of these exceptions,
              and we have to handle retrying them ourselves. Starting with version 1.26.0,
              urllib3 wraps the ssl.SSLError into a urllib3.exceptions.SSLError.

        Note: Pytorch uses an ExceptionWrapper class that tries to "reconstruct" its wrapped
              exception, but if a new exception gets thrown *while calling the constructor* of
              the wrapped exception's type, then that new exception is raised instead of an
              instance of the wrapped exception's type. Long story short, this means some
              retryable AWS exceptions get turned into KeyErrors, so we have to catch KeyError too.

        :param key: Full S3 path or bucket key of blob.
        :param num_tries: Number of download tries.
        :return: Blob binary stream.
        """
        s3_path, bucket, key = self._get_s3_location(key)
        disable_progress = not self._show_progress
        for try_number in range(0, num_tries):
            try:
                total_length = int(self._client.head_object(Bucket=bucket, Key=key).get('ContentLength', 0))
                bar_format = '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
                with tqdm(total=total_length, desc=f'Downloading {s3_path}...', bar_format=bar_format, unit='B', unit_scale=True, unit_divisor=1024, disable=disable_progress) as pbar:
                    stream: BinaryIO = io.BytesIO()
                    self._client.download_fileobj(bucket, key, stream, Callback=pbar.update)
                    stream.seek(0)
                break
            except (urllib3.exceptions.ProtocolError, ssl.SSLError, urllib3.exceptions.SSLError, KeyError, BotoCoreError, NoCredentialsError) as e:
                if isinstance(e, KeyError):
                    logger.warning(f'Caught KeyError: {e}. Retrying S3 read.')
                was_last_try = try_number == num_tries - 1
                if was_last_try:
                    raise e
                else:
                    logger.debug(f'Retrying S3 fetch due to exception {e}')
                    time.sleep(2 ** try_number)
            except botocore.exceptions.ClientError as error:
                if error.response['Error']['Code'] == 'NoSuchKey':
                    message = f'{str(error)}\nS3 path not found: {s3_path}'
                    raise BlobStoreKeyNotFound(message)
                else:
                    raise RuntimeError(f'{error} Key: {s3_path}')
        return stream

    async def get_async(self, key: str) -> BinaryIO:
        """Inherited, see superclass."""
        raise NotImplementedError('Not today.')

    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """Inherited, see superclass."""
        super().save_to_disk(key, check_for_compressed=check_for_compressed)

    def exists(self, key: str) -> bool:
        """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        _, bucket, key = self._get_s3_location(key)
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:
                return False
            raise
        except BotoCoreError as e:
            logger.debug(e)
            return False

    def put(self, key: str, value: BinaryIO, ignore_if_client_error: bool=False) -> bool:
        """
        Writes content to the blobstore.
        :param key: Blob path or token.
        :param value: Data to save.
        :param ignore_if_client_error: Set to true if we want to ignore botocore client error
        """
        _, bucket, key = self._get_s3_location(key)
        successfully_stored_object = False
        try:
            response = self._client.put_object(Body=value, Bucket=bucket, Key=key)
            successfully_stored_object = response is not None
            if not successfully_stored_object:
                raise RuntimeError(f'Failed to store object to blobstore. Key : {key}')
        except botocore.exceptions.ClientError as error:
            logger.info(f'{error}')
            if not ignore_if_client_error:
                raise RuntimeError(f'{error} Key: {key}')
        return successfully_stored_object

def __init__(self, s3_prefix: str, profile_name: Optional[str]=None, show_progress: bool=True) -> None:
    """
        Initialize S3Store.
        :param s3_prefix: S3 path
        :param profile_name: Profile name.
        :param show_progress: Whether to show download progress.
        """
    assert s3_prefix.startswith('s3://')
    self._s3_prefix = s3_prefix
    if not self._s3_prefix.endswith('/'):
        self._s3_prefix += '/'
    self._profile_name = profile_name
    url = parse.urlparse(self._s3_prefix)
    self._bucket = url.netloc
    self._prefix = url.path.lstrip('/')
    self._client = get_s3_client(self._profile_name)
    self._show_progress = show_progress

def _get_s3_location(self, key: str) -> Tuple[str, str, str]:
    """
        Get s3 location information.
        :param key: Full S3 path or bucket key of blob.
        :return: Full S3 path, bucket and key.
        """
    s3_path = key if key.startswith('s3://') else f's3://{self._bucket}/{self._prefix}{key}'
    url = parse.urlparse(s3_path)
    bucket = url.netloc
    parsed_key = url.path.lstrip('/')
    return (s3_path, bucket, parsed_key)

def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
    """
        Get blob content.
        :param key: Full S3 path or bucket key of blob.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: A file-like object, use read() to get raw bytes.
        """
    path, _, _ = self._get_s3_location(key)
    gzip_path = path + '.gzip'
    if check_for_compressed and self.exists(gzip_path):
        gzip_stream = self._get(key=gzip_path)
        content: BinaryIO = self._extract_gzip_content(gzip_stream)
    else:
        content = self._get(key=key)
    return content

def _get(self, key: str, num_tries: int=7) -> BinaryIO:
    """
        Get blob content from path/key.

        Note: Occasionally S3 give a ConnectionResetError or http.client.IncompleteRead
              exception. urllib3 wraps both of these in a ProtocolError. Sometimes S3 also
              gives an "ssl.SSLError: [SSL: WRONG_VERSION_NUMBER]" error. Unfortunately the
              boto3 retrying ("max_attempts") gives up when it sees any of these exceptions,
              and we have to handle retrying them ourselves. Starting with version 1.26.0,
              urllib3 wraps the ssl.SSLError into a urllib3.exceptions.SSLError.

        Note: Pytorch uses an ExceptionWrapper class that tries to "reconstruct" its wrapped
              exception, but if a new exception gets thrown *while calling the constructor* of
              the wrapped exception's type, then that new exception is raised instead of an
              instance of the wrapped exception's type. Long story short, this means some
              retryable AWS exceptions get turned into KeyErrors, so we have to catch KeyError too.

        :param key: Full S3 path or bucket key of blob.
        :param num_tries: Number of download tries.
        :return: Blob binary stream.
        """
    s3_path, bucket, key = self._get_s3_location(key)
    disable_progress = not self._show_progress
    for try_number in range(0, num_tries):
        try:
            total_length = int(self._client.head_object(Bucket=bucket, Key=key).get('ContentLength', 0))
            bar_format = '{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            with tqdm(total=total_length, desc=f'Downloading {s3_path}...', bar_format=bar_format, unit='B', unit_scale=True, unit_divisor=1024, disable=disable_progress) as pbar:
                stream: BinaryIO = io.BytesIO()
                self._client.download_fileobj(bucket, key, stream, Callback=pbar.update)
                stream.seek(0)
            break
        except (urllib3.exceptions.ProtocolError, ssl.SSLError, urllib3.exceptions.SSLError, KeyError, BotoCoreError, NoCredentialsError) as e:
            if isinstance(e, KeyError):
                logger.warning(f'Caught KeyError: {e}. Retrying S3 read.')
            was_last_try = try_number == num_tries - 1
            if was_last_try:
                raise e
            else:
                logger.debug(f'Retrying S3 fetch due to exception {e}')
                time.sleep(2 ** try_number)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchKey':
                message = f'{str(error)}\nS3 path not found: {s3_path}'
                raise BlobStoreKeyNotFound(message)
            else:
                raise RuntimeError(f'{error} Key: {s3_path}')
    return stream

def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
    """Inherited, see superclass."""
    super().save_to_disk(key, check_for_compressed=check_for_compressed)

def exists(self, key: str) -> bool:
    """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
    _, bucket, key = self._get_s3_location(key)
    try:
        self._client.head_object(Bucket=bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:
            return False
        raise
    except BotoCoreError as e:
        logger.debug(e)
        return False

def put(self, key: str, value: BinaryIO, ignore_if_client_error: bool=False) -> bool:
    """
        Writes content to the blobstore.
        :param key: Blob path or token.
        :param value: Data to save.
        :param ignore_if_client_error: Set to true if we want to ignore botocore client error
        """
    _, bucket, key = self._get_s3_location(key)
    successfully_stored_object = False
    try:
        response = self._client.put_object(Body=value, Bucket=bucket, Key=key)
        successfully_stored_object = response is not None
        if not successfully_stored_object:
            raise RuntimeError(f'Failed to store object to blobstore. Key : {key}')
    except botocore.exceptions.ClientError as error:
        logger.info(f'{error}')
        if not ignore_if_client_error:
            raise RuntimeError(f'{error} Key: {key}')
    return successfully_stored_object

class BlobStoreCreator:
    """BlobStoreCreator Class."""

    @classmethod
    def create_nuplandb(cls, data_root: str, verbose: bool=False) -> BlobStore:
        """
        Create nuPlan DB blob storage.

        :param data_root: nuPlan database root.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
        conf = RemoteConfig(http_root_url=os.getenv('NUPLAN_DATA_ROOT_HTTP_URL', ''), s3_root_url=os.getenv('NUPLAN_DATA_ROOT_S3_URL', ''))
        return cls.create(data_root, conf, verbose)

    @classmethod
    def create_mapsdb(cls, map_root: str, verbose: bool=False) -> BlobStore:
        """
        Create Maps DB blob storage.

        :param map_root: Maps database root.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
        conf = RemoteConfig(http_root_url=os.getenv('NUPLAN_MAPS_ROOT_HTTP_URL', ''), s3_root_url=os.getenv('NUPLAN_MAPS_ROOT_S3_URL', ''))
        return cls.create(map_root, conf, verbose)

    @classmethod
    def create(cls, data_root: str, conf: RemoteConfig, verbose: bool=False) -> BlobStore:
        """
        Create blob storage.

        :param data_root: Data root.
        :param conf: Configuration to use.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
        if NUPLAN_DATA_STORE == 'http':
            if not conf.http_root_url:
                raise ValueError('HTTP root url to be specified if using http storage.')
            requests.get(conf.http_root_url, timeout=2.0)
            logger.debug(f'Using HTTP blob store {conf.http_root_url} WITH local disk cache at {data_root}')
            return CacheStore(data_root, HttpStore(conf.http_root_url))
        elif NUPLAN_DATA_STORE == 'local':
            logger.debug(f'Using local disk store at {data_root} with no remote store')
            return LocalStore(data_root)
        elif NUPLAN_DATA_STORE == 's3':
            if not conf.s3_root_url:
                raise ValueError(f'S3 root url to be specified if using s3 storage. s3_root_url: {conf.s3_root_url}')
            store = S3Store(conf.s3_root_url, show_progress=verbose)
            if NUPLAN_CACHE_FROM_S3:
                logger.debug(f'Using s3 blob store for {conf.s3_root_url} WITH local disk cache at {data_root}')
                return CacheStore(data_root, store)
            else:
                logger.debug(f'Using s3 blob store for {conf.s3_root_url} WITHOUT local disk cache')
                return store
        else:
            raise ValueError(f"Environment variable NUPLAN_DATA_STORE was set to '{NUPLAN_DATA_STORE}'. Valid values are 'http', 'local', 's3'.")

@classmethod
def create_nuplandb(cls, data_root: str, verbose: bool=False) -> BlobStore:
    """
        Create nuPlan DB blob storage.

        :param data_root: nuPlan database root.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
    conf = RemoteConfig(http_root_url=os.getenv('NUPLAN_DATA_ROOT_HTTP_URL', ''), s3_root_url=os.getenv('NUPLAN_DATA_ROOT_S3_URL', ''))
    return cls.create(data_root, conf, verbose)

@classmethod
def create_mapsdb(cls, map_root: str, verbose: bool=False) -> BlobStore:
    """
        Create Maps DB blob storage.

        :param map_root: Maps database root.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
    conf = RemoteConfig(http_root_url=os.getenv('NUPLAN_MAPS_ROOT_HTTP_URL', ''), s3_root_url=os.getenv('NUPLAN_MAPS_ROOT_S3_URL', ''))
    return cls.create(map_root, conf, verbose)

@classmethod
def create(cls, data_root: str, conf: RemoteConfig, verbose: bool=False) -> BlobStore:
    """
        Create blob storage.

        :param data_root: Data root.
        :param conf: Configuration to use.
        :param verbose: Verbose setting, defaults to False.
        :return: Blob storage created.
        """
    if NUPLAN_DATA_STORE == 'http':
        if not conf.http_root_url:
            raise ValueError('HTTP root url to be specified if using http storage.')
        requests.get(conf.http_root_url, timeout=2.0)
        logger.debug(f'Using HTTP blob store {conf.http_root_url} WITH local disk cache at {data_root}')
        return CacheStore(data_root, HttpStore(conf.http_root_url))
    elif NUPLAN_DATA_STORE == 'local':
        logger.debug(f'Using local disk store at {data_root} with no remote store')
        return LocalStore(data_root)
    elif NUPLAN_DATA_STORE == 's3':
        if not conf.s3_root_url:
            raise ValueError(f'S3 root url to be specified if using s3 storage. s3_root_url: {conf.s3_root_url}')
        store = S3Store(conf.s3_root_url, show_progress=verbose)
        if NUPLAN_CACHE_FROM_S3:
            logger.debug(f'Using s3 blob store for {conf.s3_root_url} WITH local disk cache at {data_root}')
            return CacheStore(data_root, store)
        else:
            logger.debug(f'Using s3 blob store for {conf.s3_root_url} WITHOUT local disk cache')
            return store
    else:
        raise ValueError(f"Environment variable NUPLAN_DATA_STORE was set to '{NUPLAN_DATA_STORE}'. Valid values are 'http', 'local', 's3'.")

class CacheStore(BlobStore):
    """
    Cache store, it combines a remote blob store and local store. The idea is to load blob
    from a remote store and cache it in local store so the next time we can load it from
    local.
    """

    def __init__(self, cache_dir: str, remote: BlobStore) -> None:
        """
        Initialize CacheStore.
        :param cache_dir: Path where to cache.
        :param remote: BlobStore instance.
        """
        os.makedirs(cache_dir, exist_ok=True)
        self._local = LocalStore(cache_dir)
        self._cache_dir = cache_dir
        self._remote = remote
        self._on_disk: Set[str] = set()

    def __reduce__(self) -> Tuple[Type[CacheStore], Tuple[str, BlobStore]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class.
        """
        return (self.__class__, (self._cache_dir, self._remote))

    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get blob content if its present. Else download and then return.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :return: A file-like object, use read() to get raw bytes.
        """
        if self.exists(key):
            content: BinaryIO = self._local.get(key)
        else:
            content = self._remote.get(key, check_for_compressed)
            key_split = key.split('/')
            self.save(key_split[-1], content)
            content.seek(0)
        return content

    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """
        Save content to disk.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        """
        if not self.exists(key):
            content = self._remote.get(key, check_for_compressed)
            self.save(key, content)

    async def get_async(self, key: str) -> BinaryIO:
        """Inherited, see superclass."""
        raise NotImplementedError('Not today.')

    def exists(self, key: str) -> bool:
        """
        Check if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        if key in self._on_disk:
            return True
        if self._local.exists(key):
            self._on_disk.add(key)
            return True
        return False

    def put(self, key: str, value: BinaryIO) -> None:
        """
        Write content.
        :param key: Blob path or token.
        :param value: Data to save.
        """
        self._remote.put(key, value)
        value.seek(0)
        self._local.put(key, value)
        self._on_disk.add(key)

    def save(self, key: str, content: BinaryIO) -> None:
        """
        Save to disk.
        :param key: Blob path or token.
        :param content: Data to save.
        """
        assert os.access(self._cache_dir, os.W_OK), 'Can not write to %s' % self._cache_dir
        path = os.path.join(self._cache_dir, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fp:
            fp.write(content.read())

def __init__(self, cache_dir: str, remote: BlobStore) -> None:
    """
        Initialize CacheStore.
        :param cache_dir: Path where to cache.
        :param remote: BlobStore instance.
        """
    os.makedirs(cache_dir, exist_ok=True)
    self._local = LocalStore(cache_dir)
    self._cache_dir = cache_dir
    self._remote = remote
    self._on_disk: Set[str] = set()

def put(self, key: str, value: BinaryIO) -> None:
    """
        Write content.
        :param key: Blob path or token.
        :param value: Data to save.
        """
    self._remote.put(key, value)
    value.seek(0)
    self._local.put(key, value)
    self._on_disk.add(key)

def save(self, key: str, content: BinaryIO) -> None:
    """
        Save to disk.
        :param key: Blob path or token.
        :param content: Data to save.
        """
    assert os.access(self._cache_dir, os.W_OK), 'Can not write to %s' % self._cache_dir
    path = os.path.join(self._cache_dir, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fp:
        fp.write(content.read())

class BlobStore(abc.ABC):
    """
    BlobStore interface, the idea is to abstract the way we load blob content.
    """

    @abc.abstractmethod
    def get(self, key: str, check_for_compressed: bool=False) -> BinaryIO:
        """
        Get blob content.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        :raises: BlobStoreKeyNotFound is `key` is not present in backing store.
        :return: A file-like object, use read() to get raw bytes.
        """
        pass

    @abc.abstractmethod
    def exists(self, key: str) -> bool:
        """
        Tell if the blob exists.
        :param key: blob path or token.
        :return: True if the blob exists else False.
        """
        pass

    @abc.abstractmethod
    def put(self, key: str, value: BinaryIO) -> None:
        """
        Writes content to the blobstore.
        :param key: Blob path or token.
        :param value: Data to save.
        """
        pass

    @abc.abstractmethod
    def save_to_disk(self, key: str, check_for_compressed: bool=False) -> None:
        """
        Save the data to disk.
        :param key: Blob path or token.
        :param check_for_compressed: Flag that check for a "<key>+.gzip" file and extracts the <key> file.
        """
        pass

    def _extract_gzip_content(self, gzip_stream: BinaryIO) -> BinaryIO:
        """
        Decompress data.
        :param gzip_stream: Data to decompress.
        :return: Extracted binary data.
        """
        decompressed = gzip.decompress(gzip_stream.read())
        return io.BytesIO(decompressed)

def _extract_gzip_content(self, gzip_stream: BinaryIO) -> BinaryIO:
    """
        Decompress data.
        :param gzip_stream: Data to decompress.
        :return: Extracted binary data.
        """
    decompressed = gzip.decompress(gzip_stream.read())
    return io.BytesIO(decompressed)

def load_mmap(path: str, size: Tuple[int, int], dtype: str) -> npt.NDArray[Union[np.uint8, np.float32]]:
    """
    Loads a binary file at path to a memory map and coverts to a numpy array.
    :param path: The path to load the binary file.
    :param size: The size of the numpy array.
    :param dtype: A string either 'int' or 'float'.
    :return: A mmap object.
    """
    assert dtype in {'int', 'float'}, f'Param dtype must be either int or float. Received {dtype}.'
    if dtype == 'int':
        dtype = np.uint8
    elif dtype == 'float':
        dtype = np.float32
    with open(path, 'rb') as fp:
        memory_map = mmap(fp.fileno(), 0, prot=PROT_READ)
    return np.ndarray(shape=size, dtype=dtype, buffer=memory_map)

def has_binary_masks(map_layer: MapLayerMeta, cache_dir: str) -> bool:
    """
    Checks if all binary masks are created.
    :param map_layer: A MapLayerMeta object.
    :param cache_dir: The directory to cache the binary mask.
    :return: True if binary masks are created, otherwise False.
    """
    binary_paths = [os.path.join(cache_dir, map_layer.binary_mask_name)]
    if map_layer.can_dilate:
        binary_paths.append(os.path.join(cache_dir, map_layer.binary_joint_dist_name))
    for binary_path in binary_paths:
        if not os.path.exists(binary_path) or os.path.getsize(binary_path) == 0:
            return False
    return True

def create_binary_masks(array: npt.NDArray[np.uint8], map_layer: MapLayerMeta, layer_dir: str) -> None:
    """
    Creates the binary mask for a given map layer in a given map version and
    stores it in the cache.
    :param array: Map array to write to binary.
    :param map_layer: Map layer to create the masks for.
    :param layer_dir: Directory where binary masks will be stored.
    """
    if len(array.shape) == 3:
        array = array[:, :, 0]
    if map_layer.is_binary:
        array[array < 255] = 0
        array[array == 255] = 1
    destination = os.path.join(layer_dir, '{}')
    logger.debug('Writing binary mask to {}...'.format(destination.format(map_layer.binary_mask_name)))
    with open(destination.format(map_layer.binary_mask_name), 'wb') as f:
        f.write(array.tobytes())
    logger.debug('Writing binary mask to {} done.'.format(destination.format(map_layer.binary_mask_name)))
    if map_layer.can_dilate:
        logger.debug('Writing joint distance mask to {}...'.format(destination.format(map_layer.binary_joint_dist_name)))
        joint_distances = compute_joint_distance_matrix(array, map_layer.precision)
        with open(destination.format(map_layer.binary_joint_dist_name), 'wb') as f:
            f.write(joint_distances.tobytes())
        del joint_distances
        del array
        logger.debug('Writing joint distance mask to {} done.'.format(destination.format(map_layer.binary_joint_dist_name)))

def load_layer_as_numpy(layer_dataset, is_binary: bool) -> npt.NDArray[np.uint8]:
    """
    Loads map layer data as a numpy array.
    :param layer_dataset: A *context manager* for the layer dataset.
    :param is_binary: Whether the layer is binary or not.
    :return: The layer data as numpy array.
    """
    if is_binary:
        raw_layer = layer_dataset.read(out_dtype=np.uint8)
        layer_data = raw_layer[0, :, :]
        layer_data[layer_data > 0] = 1
    else:
        raw_layer = layer_dataset.read()
        layer_data = raw_layer[0, :, :]
    return np.array(layer_data)

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

def get_version(self, location: str) -> str:
    """Inherited, see superclass."""
    return str(self._metadata[location]['version'])

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

def _save_all_layers(self, location: str) -> None:
    """
        Saves data on disk for all layers in the GPKG file for `location`.
        :param location: Name of map location, e.g. "sg-one-north`. See `self.get_locations()`.
        """
    rasterio_layers = self.get_raster_layer_names(location)
    for layer_name in rasterio_layers:
        logger.debug('Working on layer: ', layer_name)
        self._save_layer_matrix(location, layer_name)

def execute_many(query_text: str, query_parameters: Any, db_file: str) -> Generator[sqlite3.Row, None, None]:
    """
    Runs a query with the provided arguments on a specified Sqlite DB file.
    This query can return any number of rows.
    :param query_text: The query to run.
    :param query_parameters: The parameters to provide to the query.
    :param db_file: The DB file on which to run the query.
    :return: A generator of rows emitted from the query.
    """
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    try:
        cursor.execute(query_text, query_parameters)
        for row in cursor:
            yield row
    finally:
        cursor.close()
        connection.close()

def execute_one(query_text: str, query_parameters: Any, db_file: str) -> Optional[sqlite3.Row]:
    """
    Runs a query with the provided arguments on a specified Sqlite DB file.
    Validates that the query returns at most one row.
    :param query_text: The query to run.
    :param query_parameters: The parameters to provide to the query.
    :param db_file: The DB file on which to run the query.
    :return: The returned row, if it exists. None otherwise.
    """
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    try:
        cursor.execute(query_text, query_parameters)
        result: Optional[sqlite3.Row] = cursor.fetchone()
        if result is not None and cursor.fetchone() is not None:
            raise RuntimeError('execute_one query returned multiple rows.')
        return result
    finally:
        cursor.close()
        connection.close()

def get_sensor_transform_matrix_for_sensor_data_token_from_db(log_file: str, sensor_source: SensorDataSource, sensor_data_token: str) -> Optional[Transform]:
    """
    Get the associated lidar transform matrix from the DB for the given lidarpc_token.
    :param log_file: The log file to query.
    :param sensor_source: Parameters for querying the correct table.
    :param sensor_data_token: The sensor data token to query.
    :return: The transform matrix. Reuturns None if the matrix does not exist in the DB (e.g. for a token that does not exist).
    """
    query = f'\n        SELECT  sensor.translation,\n                sensor.rotation\n        FROM {sensor_source.sensor_table} AS sensor\n        INNER JOIN {sensor_source.table} AS sensor_data\n            ON sensor_data.{sensor_source.sensor_token_column} = sensor.token\n        WHERE sensor_data.token = ?;\n    '
    row = execute_one(query, (bytearray.fromhex(sensor_data_token),), log_file)
    if row is None:
        return None
    translation = pickle.loads(row['translation'])
    rotation = pickle.loads(row['rotation'])
    output = Quaternion(rotation).transformation_matrix
    output[:3, 3] = np.array(translation)
    return output

def _execute_non_query(query_text: str, file_path: str) -> None:
    """
    Connect to a SQLite DB and runs a query that returns no results.
    E.g. a CREATE TABLE statement.
    :param query_text: The query text to run.
    :param file_path: The file on which to run the query.
    """
    connection = sqlite3.connect(file_path)
    cursor = connection.cursor()
    try:
        cursor.execute(query_text)
    finally:
        cursor.close()
        connection.close()

def _execute_bulk_insert(query_text: str, values: List[Any], file_path: str) -> None:
    """
    Connect to a SQLite DB and runs a query that inserts many rows into the DB.
    This function will commit the changes after a successful execution.
    :param query_text: The query text to run.
    :param values: The values to insert.
    :param file_path: The file on which to run the query.
    """
    connection = sqlite3.connect(file_path)
    cursor = connection.cursor()
    try:
        cursor.executemany(query_text, values)
        cursor.execute('commit;')
    finally:
        cursor.close()
        connection.close()

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

def _get_session_internal(profile_name: Optional[str], aws_access_key_id: Optional[str], aws_secret_access_key: Optional[str], create_session_func: Callable[..., Union[boto3.Session, aioboto3.Session]], set_session_func: Callable[[Union[boto3.Session, aioboto3.Session]], None]) -> Union[boto3.Session, aioboto3.Session]:
    """
    Get synchronous boto3 session.
    :param profile_name: Optional profile name to authenticate with.
    :param aws_access_key_id: Optional access key to authenticate with.
    :param aws_secret_access_key: Optional secret access key to authenticate with.
    :param create_session_func: Session creation function.
    :param set_session_func: Session caching function.
    :return: Session object.
    """
    args: Dict[str, Any] = {}
    if os.getenv('AWS_WEB_IDENTITY_TOKEN_FILE') is not None:
        logger.debug('Using AWS_WEB_IDENTITY_TOKEN_FILE for credentials.')
    elif profile_name is None and aws_access_key_id is None and (aws_secret_access_key is None):
        logger.debug('Using default credentials for AWS session.')
    else:
        logger.debug('Attempting to use credentialed authentication for S3 client...')
        args = {'profile_name': os.getenv('NUPLAN_S3_PROFILE', '') if profile_name is None else profile_name}
        if aws_access_key_id and aws_secret_access_key:
            args['aws_access_key_id'] = aws_access_key_id
            args['aws_secret_access_key'] = aws_secret_access_key
    try:
        session = create_session_func(**args)
        set_session_func(session)
    except BotoCoreError as e:
        if 'profile_name' in args:
            logger.info(f'Trying default AWS credential chain, since we got this exception while trying to use AWS profile [{args['profile_name']}]: {e}')
        session = create_session_func()
        set_session_func(session)
    return session

def _create_session_func(**kwargs: Any) -> aioboto3.Session:
    return boto3.Session(**kwargs)

def get_s3_client(profile_name: Optional[str]=None, max_attempts: int=10, aws_access_key_id: Optional[str]=None, aws_secret_access_key: Optional[str]=None) -> boto3.client:
    """
    Start a Boto3 session and retrieve the client.
    :param profile_name: S3 profile name to use when creating the session.
    :param aws_access_key_id: Aws access key id.
    :param aws_secret_access_key: Aws secret access key.
    :param max_attempts: Maximum number of attempts in loading the client.
    :return: The instantiated client object.
    """
    session = _get_sync_session(profile_name, aws_access_key_id, aws_secret_access_key)
    config = Config(retries={'max_attempts': max_attempts})
    client = session.client('s3', config=config)
    return client

def _trim_leading_slash_if_exists(path: Union[str, Path]) -> Path:
    """
    Trims the leading slash in a path if it exists.
    :param path: The path to trim.
    :return: The trimmed path.
    """
    path_str = str(path)
    if path_str == '/':
        raise ValueError("Path is the root path '/'. This should never happen.")
    path_str = path_str[1:] if path_str.startswith('/') else path_str
    return Path(path_str)

def is_s3_path(candidate: Union[Path, str]) -> bool:
    """
    Returns true if the path points to a location in S3, false otherwise.
    :param candidate: The candidate path.
    :return: True if the path points to a location in S3, false otherwise.
    """
    candidate_str = str(candidate)
    return candidate_str.startswith('s3:/')

def split_s3_path(s3_path: Path) -> Tuple[str, Path]:
    """
    Splits a S3 path into a (bucket, path) set of identifiers.
    :param s3_path: The full S3 path.
    :return: A tuple of (bucket, path).
    """
    if not is_s3_path(s3_path):
        raise ValueError(f'{str(s3_path)} is not an s3 path.')
    chunks = [v.strip() for v in str(s3_path).split('/') if len(v.strip()) > 0]
    bucket = chunks[1]
    path = Path('/'.join(chunks[2:]))
    return (bucket, path)

@retry(RETRYABLE_EXCEPTIONS, backoff=2, tries=7, delay=0.5, jitter=(0.5, 3))
def expand_s3_dir(s3_path: str, client: Optional[boto3.client]=None, filter_suffix: str='') -> List[str]:
    """
    Expand S3 path dir to a list of S3 path files.
    :param s3_path: S3 path dir to expand.
    :param client: Boto3 client to use, if None create a new one.
    :param filter_suffix: Optional suffix to filter S3 filenames with.
    :return: List of S3 filenames discovered.
    """
    logger.warning('Function expand_s3_dir will soon be removed in favor of list_files_in_s3_directory')
    client = get_s3_client() if client is None else client
    url = parse.urlparse(s3_path)
    paginator = client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=url.netloc, Prefix=url.path.lstrip('/'))
    filenames = [str(content['Key']) for page in page_iterator for content in page['Contents']]
    filenames = [f's3://{url.netloc}/{path}' for path in filenames if path.endswith(filter_suffix)]
    return filenames

class FileBackedBarrier:
    """
    A file-based synchronization barrier.
    This class can be used to synchronize activies across multiple machines.
    """

    def __init__(self, barrier_directory: Path) -> None:
        """
        Initializes a FileBackedBarrier.
        :param barrier_directory: The path that the barrier files will use for synchronization.
          This can be a local or S3 path.
        """
        self._barrier_directory = barrier_directory
        self._is_s3 = str(barrier_directory).startswith('s3:')
        self._activity_file_content = 'x'

    def wait_barrier(self, activity_id: str, expected_activity_ids: Set[str], timeout_s: Optional[float]=None, poll_interval_s: float=1) -> None:
        """
        Registers that `activity_id` has completed.
        Waits until all activities in `expected_activity_ids` have completed.
        If timeout_s has been provided, the operation will raise a TimeoutError after
          the supplied number of seconds has passed.

        :param activity_id: The activity ID that will be registered as completed.
        :param expected_activity_ids: The list of activity IDs that are expected to be completed.
          The function will block until these are done.
        :param timeout_s: If provided, the timeout for the wait operation.
          If the operation does not complete within this amount of time, then a TimeoutError will be raised.
        :param poll_interval_s: The elapsed time before polling for new files.
        """
        logger.info('Writing completion of activity id %s to directory %s...', activity_id, self._barrier_directory)
        self._register_activity_id_complete(activity_id)
        logger.info('Waiting for all processes to finish processing')
        self._wait(expected_activity_ids, timeout_s, poll_interval_s)
        logger.info(f'Sleeping for {poll_interval_s * SLEEP_MULTIPLIER_BEFORE_CLEANUP} seconds so that the other processes catch up before moving on')
        time.sleep(poll_interval_s * SLEEP_MULTIPLIER_BEFORE_CLEANUP)
        logger.info('All Processes Synced, clearing activity file')
        self._remove_activity_after_processing(activity_id)
        logger.info('Waiting for all processes to clean up barrier files')
        self._wait(set(), timeout_s, poll_interval_s)

    def _wait(self, expected_activity_ids: Set[str], timeout_s: Optional[float]=None, poll_interval_s: float=1) -> None:
        start_wait_time = time.time()
        logger.info('Beginning barrier wait at time %f', start_wait_time)
        while True:
            next_wait_time = time.time() + poll_interval_s
            logger.debug('The next wait time is %f. Getting completed activity ids...', next_wait_time)
            completed_activity_ids = self._get_completed_activity_ids()
            logger.debug('There are %d completed activities.', len(completed_activity_ids))
            if expected_activity_ids == completed_activity_ids:
                logger.debug('All activities completed! Ending wait.')
                return
            total_wait_time = time.time() - start_wait_time
            logger.debug('All tasks not finished. Total elapsed wait time is %f.', total_wait_time)
            if timeout_s is not None and total_wait_time > timeout_s:
                raise TimeoutError(f'Waited {total_wait_time} sec for barrier {self._barrier_directory}, which is longer than configured timeout of {timeout_s}.')
            sleep_time = max(0.0, next_wait_time - time.time())
            logger.debug('Sleeping for %f seconds.', sleep_time)
            time.sleep(sleep_time)

    def _register_activity_id_complete(self, activity_id: str) -> None:
        """
        Registers an activity_id as completed by creating a file in the configured directory.
        :param activity_id: The activity ID to register as completed.
        """
        activity_id_file_path = self._barrier_directory / activity_id
        if self._is_s3:
            s3_bucket, s3_key = self._split_s3_path(activity_id_file_path)
            self._create_activity_file_in_s3(s3_key, s3_bucket)
        else:
            activity_id_file_path.parent.mkdir(exist_ok=True, parents=True)
            with open(activity_id_file_path, 'w') as f:
                f.write(self._activity_file_content)

    def _get_completed_activity_ids(self) -> Set[str]:
        """
        Gets the activity IDs from the filesystem that have been marked as completed.
        :return: The completed file system activity ids.
        """
        if self._is_s3:
            s3_bucket, s3_key = self._split_s3_path(self._barrier_directory)
            files = [Path(p) for p in self._list_files_in_s3_directory(s3_key, s3_bucket)]
        else:
            files = [x for x in self._barrier_directory.iterdir() if x.is_file()]
        unique_activity_ids = {f.stem for f in files}
        return unique_activity_ids

    def _remove_activity_after_processing(self, activity_id: str) -> None:
        """
        Removes the activity file so that we can reuse the same directory in future calls to sync
        """
        activity_id_file_path = self._barrier_directory / activity_id
        if self._is_s3:
            s3_bucket, s3_key = self._split_s3_path(activity_id_file_path)
            self._remove_activity_file_from_s3(s3_key, s3_bucket)
        else:
            activity_id_file_path.unlink()

    @retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
    def _create_activity_file_in_s3(self, s3_key: Path, s3_bucket: str) -> None:
        """
        Creates an activity file in S3
        :param s3_key: The S3 path for the file, without the bucket.
        :param s3_bucket: The name of the bucket to write to.
        """
        with closing(get_s3_client()) as s3_client:
            logger.info(f'Creating activity file at {s3_key} in bucket {s3_bucket}...')
            s3_client.put_object(Body=self._activity_file_content.encode('utf-8'), Bucket=s3_bucket, Key=str(s3_key))

    @retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
    def _remove_activity_file_from_s3(self, s3_key: Path, s3_bucket: str) -> None:
        """
        Creates an activity file in S3
        :param s3_key: The S3 path for the file, without the bucket.
        :param s3_bucket: The name of the bucket to write to.
        """
        with closing(get_s3_client()) as s3_client:
            logger.info(f'Removing activity file at {s3_key} in bucket {s3_bucket}...')
            s3_client.delete_object(Bucket=s3_bucket, Key=str(s3_key))

    @retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
    def _list_files_in_s3_directory(self, s3_key: Path, s3_bucket: str) -> List[Path]:
        """
        Lists the files available in a particular S3 directory.
        :param s3_key: The path to list, without the bucket.
        :param s3_bucket: The bucket to list.
        :return: The files in the folder.
        """
        with closing(get_s3_client()) as s3_client:
            key = str(s3_key)
            if not key.endswith('/'):
                key += '/'
            objects = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=key)
            if 'Contents' in objects:
                return [Path(k['Key']) for k in objects['Contents']]
            return []

    def _split_s3_path(self, s3_path: Path) -> Tuple[str, Path]:
        """
        Splits a S3 path into a (bucket, path) set of identifiers.
        :param s3_path: The full S3 path.
        :return: A tuple of (bucket, path).
        """
        chunks = [v.strip() for v in str(s3_path).split('/') if len(v.strip()) > 0]
        bucket = chunks[1]
        path = Path('/'.join(chunks[2:]))
        return (bucket, path)

def __init__(self, barrier_directory: Path) -> None:
    """
        Initializes a FileBackedBarrier.
        :param barrier_directory: The path that the barrier files will use for synchronization.
          This can be a local or S3 path.
        """
    self._barrier_directory = barrier_directory
    self._is_s3 = str(barrier_directory).startswith('s3:')
    self._activity_file_content = 'x'

def wait_barrier(self, activity_id: str, expected_activity_ids: Set[str], timeout_s: Optional[float]=None, poll_interval_s: float=1) -> None:
    """
        Registers that `activity_id` has completed.
        Waits until all activities in `expected_activity_ids` have completed.
        If timeout_s has been provided, the operation will raise a TimeoutError after
          the supplied number of seconds has passed.

        :param activity_id: The activity ID that will be registered as completed.
        :param expected_activity_ids: The list of activity IDs that are expected to be completed.
          The function will block until these are done.
        :param timeout_s: If provided, the timeout for the wait operation.
          If the operation does not complete within this amount of time, then a TimeoutError will be raised.
        :param poll_interval_s: The elapsed time before polling for new files.
        """
    logger.info('Writing completion of activity id %s to directory %s...', activity_id, self._barrier_directory)
    self._register_activity_id_complete(activity_id)
    logger.info('Waiting for all processes to finish processing')
    self._wait(expected_activity_ids, timeout_s, poll_interval_s)
    logger.info(f'Sleeping for {poll_interval_s * SLEEP_MULTIPLIER_BEFORE_CLEANUP} seconds so that the other processes catch up before moving on')
    time.sleep(poll_interval_s * SLEEP_MULTIPLIER_BEFORE_CLEANUP)
    logger.info('All Processes Synced, clearing activity file')
    self._remove_activity_after_processing(activity_id)
    logger.info('Waiting for all processes to clean up barrier files')
    self._wait(set(), timeout_s, poll_interval_s)

def _wait(self, expected_activity_ids: Set[str], timeout_s: Optional[float]=None, poll_interval_s: float=1) -> None:
    start_wait_time = time.time()
    logger.info('Beginning barrier wait at time %f', start_wait_time)
    while True:
        next_wait_time = time.time() + poll_interval_s
        logger.debug('The next wait time is %f. Getting completed activity ids...', next_wait_time)
        completed_activity_ids = self._get_completed_activity_ids()
        logger.debug('There are %d completed activities.', len(completed_activity_ids))
        if expected_activity_ids == completed_activity_ids:
            logger.debug('All activities completed! Ending wait.')
            return
        total_wait_time = time.time() - start_wait_time
        logger.debug('All tasks not finished. Total elapsed wait time is %f.', total_wait_time)
        if timeout_s is not None and total_wait_time > timeout_s:
            raise TimeoutError(f'Waited {total_wait_time} sec for barrier {self._barrier_directory}, which is longer than configured timeout of {timeout_s}.')
        sleep_time = max(0.0, next_wait_time - time.time())
        logger.debug('Sleeping for %f seconds.', sleep_time)
        time.sleep(sleep_time)

def _register_activity_id_complete(self, activity_id: str) -> None:
    """
        Registers an activity_id as completed by creating a file in the configured directory.
        :param activity_id: The activity ID to register as completed.
        """
    activity_id_file_path = self._barrier_directory / activity_id
    if self._is_s3:
        s3_bucket, s3_key = self._split_s3_path(activity_id_file_path)
        self._create_activity_file_in_s3(s3_key, s3_bucket)
    else:
        activity_id_file_path.parent.mkdir(exist_ok=True, parents=True)
        with open(activity_id_file_path, 'w') as f:
            f.write(self._activity_file_content)

def _get_completed_activity_ids(self) -> Set[str]:
    """
        Gets the activity IDs from the filesystem that have been marked as completed.
        :return: The completed file system activity ids.
        """
    if self._is_s3:
        s3_bucket, s3_key = self._split_s3_path(self._barrier_directory)
        files = [Path(p) for p in self._list_files_in_s3_directory(s3_key, s3_bucket)]
    else:
        files = [x for x in self._barrier_directory.iterdir() if x.is_file()]
    unique_activity_ids = {f.stem for f in files}
    return unique_activity_ids

def _remove_activity_after_processing(self, activity_id: str) -> None:
    """
        Removes the activity file so that we can reuse the same directory in future calls to sync
        """
    activity_id_file_path = self._barrier_directory / activity_id
    if self._is_s3:
        s3_bucket, s3_key = self._split_s3_path(activity_id_file_path)
        self._remove_activity_file_from_s3(s3_key, s3_bucket)
    else:
        activity_id_file_path.unlink()

@retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
def _create_activity_file_in_s3(self, s3_key: Path, s3_bucket: str) -> None:
    """
        Creates an activity file in S3
        :param s3_key: The S3 path for the file, without the bucket.
        :param s3_bucket: The name of the bucket to write to.
        """
    with closing(get_s3_client()) as s3_client:
        logger.info(f'Creating activity file at {s3_key} in bucket {s3_bucket}...')
        s3_client.put_object(Body=self._activity_file_content.encode('utf-8'), Bucket=s3_bucket, Key=str(s3_key))

@retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
def _remove_activity_file_from_s3(self, s3_key: Path, s3_bucket: str) -> None:
    """
        Creates an activity file in S3
        :param s3_key: The S3 path for the file, without the bucket.
        :param s3_bucket: The name of the bucket to write to.
        """
    with closing(get_s3_client()) as s3_client:
        logger.info(f'Removing activity file at {s3_key} in bucket {s3_bucket}...')
        s3_client.delete_object(Bucket=s3_bucket, Key=str(s3_key))

@retry(RETRYABLE_EXCEPTIONS, backoff=1, tries=3, delay=0.5)
def _list_files_in_s3_directory(self, s3_key: Path, s3_bucket: str) -> List[Path]:
    """
        Lists the files available in a particular S3 directory.
        :param s3_key: The path to list, without the bucket.
        :param s3_bucket: The bucket to list.
        :return: The files in the folder.
        """
    with closing(get_s3_client()) as s3_client:
        key = str(s3_key)
        if not key.endswith('/'):
            key += '/'
        objects = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=key)
        if 'Contents' in objects:
            return [Path(k['Key']) for k in objects['Contents']]
        return []

def _split_s3_path(self, s3_path: Path) -> Tuple[str, Path]:
    """
        Splits a S3 path into a (bucket, path) set of identifiers.
        :param s3_path: The full S3 path.
        :return: A tuple of (bucket, path).
        """
    chunks = [v.strip() for v in str(s3_path).split('/') if len(v.strip()) > 0]
    bucket = chunks[1]
    path = Path('/'.join(chunks[2:]))
    return (bucket, path)

def distributed_sync(path: Union[Path, str], timeout_seconds: int=7200, poll_interval: float=0.5) -> None:
    """
    Use a FileBackendBarrier at "path" to sync across multiple workers
    (Note that it deletes the path after the sync is done to allow the same path to be reused)
    :param path: path to use for distributed sync (must be shared across workers)
    :param timeout_seconds: how long to wait for nodes to sync
    :param poll_interval: how long to sleep between poll times
    """
    if int(os.environ.get('NUM_NODES', 1)) > 1:
        barrier = FileBackedBarrier(Path(path))
        barrier.wait_barrier(activity_id='barrier_token_' + str(os.environ.get('NODE_RANK', 0)), expected_activity_ids={'barrier_token_' + str(el) for el in range(0, int(os.environ.get('NUM_NODES', 1)))}, timeout_s=timeout_seconds, poll_interval_s=poll_interval)

def try_n_times(fn: Callable[..., Any], args: List[Any], kwargs: Dict[Any, Any], errors: Tuple[Any], max_tries: int, sleep_time: float=0) -> Any:
    """
    Keeps calling a function with given parameters until maximum number of tries, catching a set of given errors.
    :param fn: The function to call
    :param args: Argument list
    :param kwargs" Keyword arguments
    :param errors: Expected errors to be ignored
    :param max_tries: Maximal number of tries before raising error
    :param sleep_time: Time waited between subsequent tried to the function call.
    :return: The return value of the given function
    """
    assert max_tries > 0, 'Number of tries must be a positive integer'
    attempts = 0
    error = None
    while attempts < max_tries:
        try:
            return fn(*args, **kwargs)
        except errors as e:
            error = e
            attempts += 1
            logging.warning(f'Tried to call {fn} raised {e}, trying {max_tries - attempts} more times.')
            time.sleep(sleep_time)
            pass
    if error:
        raise error

def keep_trying(fn: Callable[..., Any], args: List[Any], kwargs: Dict[Any, Any], errors: Tuple[Any], timeout: float, sleep_time: float=0.1) -> Any:
    """
    Keeps calling a function with given parameters until timeout (at least once), catching a set of given errors.
    :param fn: The function to call
    :param args: Argument list
    :param kwargs" Keyword arguments
    :param errors: Expected errors to be ignored
    :param timeout: Maximal time before timeout (seconds)
    :param sleep_time: Time waited between subsequent tried to the function call.
    :return: The return value of the given function
    """
    assert timeout > 0, 'Timeout must be a positive real number'
    start_time = time.time()
    max_time = start_time + timeout
    first_run = True
    while time.time() < max_time or first_run:
        try:
            return (fn(*args, **kwargs), time.time() - start_time)
        except errors:
            first_run = False
            time.sleep(sleep_time)
    raise TimeoutError(f'Timeout on function call {fn}({args}{kwargs}) catching {errors}')

@functools.cache
def get_unique_job_id() -> str:
    """
    In the cluster, it generates a hash from the unique job ID called NUPLAN_JOB_ID.
    Locally, it generates a hash from a UUID.

    Note that the returned value is cached as soon as the function is called the first time.
    After that, it is going to return always the same value.
    If a new value is needed, use get_unique_job_id.cache_clear() first.
    """
    global_job_id_str = os.environ.get('NUPLAN_JOB_ID', str(uuid.uuid4())).encode('utf-8')
    return hashlib.sha256(global_job_id_str).hexdigest()

class NuPath(type(Path())):
    """
    Version of pathlib.Path which handles safe conversions of s3 paths to strings.
    The builtin pathlib.Path converts s3 paths as follows:
        str(Path("s3://a/b/c")) -> "s3:/a/b/c"
    omitting a '/' in the s3 prefix. This can generate errors in downstream functions,
    for example when passing a Path to a pandas io function. This class handles the
    conversion back to string transparently.

    Needs to inherit from type(Path()) because the concrete implementation populates
    a hidden instance variable depending on the platform. For more info, see
    https://stackoverflow.com/a/34116756
    """

    def __str__(self) -> str:
        """
        Override to handle converting s3 paths to strings safely.
        """
        return safe_path_to_string(super().__str__())

def __str__(self) -> str:
    """
        Override to handle converting s3 paths to strings safely.
        """
    return safe_path_to_string(super().__str__())

def safe_path_to_string(path: Union[Path, str]) -> str:
    """
    Converts local/s3 paths from Path objects to string.
    It's not always safe to pass the path object to certain io functions.
    For example,
        pd.read_csv(Path("s3://foo/bar"))
    gets interpreted like
        pd.read_csv("s3:/foo/bar")  -- should be s3://, not s3:/
    which is not recognized as an s3 path and raises and error. This function takes a path
    and returns a string that can be passed to any of these functions.
    :param s3_path: Path object of path
    :return: path with the correct format as a string.
    """
    if is_s3_path(path):
        return f's3://{str(path).lstrip('s3:/')}'
    return str(path)

class DistributedScenarioFilter:
    """
    Class to distribute the work to build / filter scenarios across workers, and to break up those scenarios in chunks to be
    handled on individual machines
    """

    def __init__(self, cfg: DictConfig, worker: WorkerPool, node_rank: int, num_nodes: int, synchronization_path: str, timeout_seconds: int=7200, distributed_mode: DistributedMode=DistributedMode.SCENARIO_BASED):
        """
        :param cfg: top level config for the job (used to build scenario builder / scenario_filter)
        :param worker: worker to use in each node to parallelize the work
        :param node_rank: number from (0, num_nodes -1) denoting "which" node we are on
        :param num_nodes: total number of nodes the job is running on
        :param synchronization_path: path that can be in s3 or on a shared file system that will be used to synchronize
                                     across workers
        :param timeout_seconds: how long to wait during sync operations
        :param distributed_mode: what distributed mode to use to distribute computation
        """
        self._cfg = cfg
        self._worker = worker
        self._node_rank = node_rank
        self._num_nodes = num_nodes
        self.synchronization_path = synchronization_path
        self._timeout_seconds = timeout_seconds
        self._distributed_mode = distributed_mode

    def get_scenarios(self) -> List[AbstractScenario]:
        """
        Get all the scenarios that the current node should process
        :returns: list of scenarios for the current node
        """
        if self._num_nodes == 1 or self._distributed_mode == DistributedMode.SINGLE_NODE:
            logger.info('Building Scenarios in mode %s', DistributedMode.SINGLE_NODE)
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        elif self._distributed_mode in (DistributedMode.LOG_FILE_BASED, DistributedMode.SCENARIO_BASED):
            logger.info('Getting Log Chunks')
            current_chunk = self._get_log_db_files_for_single_node()
            logger.info('Getting Scenarios From Log Chunk of size %d', len(current_chunk))
            scenarios = self._get_scenarios_from_list_of_log_files(current_chunk)
            if self._distributed_mode == DistributedMode.LOG_FILE_BASED:
                logger.info('Distributed mode is %s, so we are just returning the scenariosfound from log files on the current worker.  There are %d scenarios to processon node %d/%d', DistributedMode.LOG_FILE_BASED, len(scenarios), self._node_rank, self._num_nodes)
                return scenarios
            logger.info('Distributed mode is %s, so we are going to repartition the scenarios we got from the log files to better distribute the work', DistributedMode.SCENARIO_BASED)
            logger.info('Getting repartitioned scenario tokens')
            tokens, log_db_files = self._get_repartition_tokens(scenarios)
            OmegaConf.set_struct(self._cfg, False)
            self._cfg.scenario_filter.scenario_tokens = tokens
            self._cfg.scenario_builder.db_files = log_db_files
            OmegaConf.set_struct(self._cfg, True)
            logger.info('Building repartitioned scenarios')
            scenario_builder = build_scenario_builder(cfg=self._cfg)
            scenario_filter = build_scenario_filter(cfg=self._cfg.scenario_filter)
        else:
            raise ValueError(f'Distributed mode must be one of {[x.name for x in fields(DistributedMode)]}, got {self._distributed_mode} instead!')
        scenarios = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_repartition_tokens(self, scenarios: List[AbstractScenario]) -> Tuple[List[str], List[str]]:
        """
        Submit list of scenarios found by the current node, sync up with other nodes to get the full list of tokens,
        and calculate the current node's set of tokens to process
        :param scenarios: Scenarios found by the current node
        :returns: (list of tokens, list of db files)
        """
        unique_job_id = get_unique_job_id()
        token_distribution_file_dir = Path(self.synchronization_path) / Path('tokens') / Path(unique_job_id)
        token_distribution_barrier_dir = Path(self.synchronization_path) / Path('barrier') / Path(unique_job_id)
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_dir = safe_path_to_string(token_distribution_file_dir)
            token_distribution_barrier_dir = safe_path_to_string(token_distribution_barrier_dir)
        self._write_token_csv_file(scenarios, token_distribution_file_dir)
        distributed_sync(token_distribution_barrier_dir, timeout_seconds=self._timeout_seconds)
        token_distribution = self._get_all_generated_csv(token_distribution_file_dir)
        db_files_path = Path(self._cfg.scenario_builder.db_files[0]).parent if isinstance(self._cfg.scenario_builder.db_files, (list, ListConfig)) else Path(self._cfg.scenario_builder.db_files)
        return self._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)

    def _get_all_generated_csv(self, token_distribution_file_dir: Union[Path, str]) -> List[Tuple[str, str]]:
        """
        Read the csv files that every machine in the cluster generated and get the full list of (token, db_file) pairs
        :param token_distribution_file_dir: path where to the csv files are stored
        :returns: full list of (token, db_file) pairs
        """
        if self.synchronization_path.startswith('s3'):
            token_distribution_file_list = [el for el in expand_s3_dir(token_distribution_file_dir) if el.endswith('.csv')]
            token_distribution_list = []
            bucket, file_path = split_s3_path(Path(token_distribution_file_list[0]))
            s3_store = S3Store(s3_prefix=os.path.join('s3://', bucket))
            for token_distribution_file in token_distribution_file_list:
                with s3_store.get(token_distribution_file) as f:
                    try:
                        token_distribution_list.append(pd.read_csv(f, delimiter=','))
                    except EmptyDataError:
                        logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', token_distribution_file)
        else:
            token_distribution_list = []
            for file_name in os.listdir(token_distribution_file_dir):
                try:
                    token_distribution_list.append(pd.read_csv(os.path.join(token_distribution_file_dir, str(file_name))))
                except EmptyDataError:
                    logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', file_name)
        if not token_distribution_list:
            raise AssertionError('No scenarios found to simulate!')
        token_distribution_df = pd.concat(token_distribution_list, ignore_index=True)
        token_distribution = token_distribution_df.values.tolist()
        return cast(List[Tuple[str, str]], token_distribution)

    def _get_token_and_log_chunk_on_single_node(self, token_distribution: List[Tuple[str, str]], db_files_path: Path) -> Tuple[List[str], List[str]]:
        """
        Get the list of tokens and the list of logs those tokens are found in restricted to the current node
        :param token_distribution: Full list of all (token, log_file) pairs to be divided among the nodes
        :param db_files_path: Path to the actual db files
        """
        db_files_path_sanitized = safe_path_to_string(db_files_path)
        if not check_s3_path_exists(db_files_path_sanitized):
            raise AssertionError(f'Multinode caching only works in S3, but db_files path given was {db_files_path_sanitized}')
        token_distribution_chunk = chunk_list(token_distribution, self._num_nodes)
        current_chunk = token_distribution_chunk[self._node_rank]
        current_logs_chunk = list({os.path.join(db_files_path_sanitized, f'{pair[1]}.db') for pair in current_chunk})
        current_token_chunk = [pair[0] for pair in current_chunk]
        return (current_token_chunk, current_logs_chunk)

    def _write_token_csv_file(self, scenarios: List[AbstractScenario], token_distribution_file_dir: Union[str, Path]) -> None:
        """
        Writes a csv file of format token,log_name that stores the tokens associated with the given scenarios
        :param scenarios: Scenarios to take token/log pairs from
        :param token_distribution_file_dir: directory to write our csv file to
        """
        token_distribution_file = os.path.join(token_distribution_file_dir, f'{self._node_rank}.csv')
        token_log_pairs = [(scenario.token, scenario.log_name) for scenario in scenarios]
        os.makedirs(token_distribution_file_dir, exist_ok=True)
        token_log_pairs_df = pd.DataFrame(token_log_pairs)
        token_log_pairs_df.to_csv(token_distribution_file, index=False)

    def _get_scenarios_from_list_of_log_files(self, log_db_files: List[str]) -> List[AbstractScenario]:
        """
        Gets the scenarios based on self._cfg, restricted to a list of log files
        :param log_db_files: list of log db files to restrict our search to
        :returns: list of scenarios
        """
        OmegaConf.set_struct(self._cfg, False)
        self._cfg.scenario_builder.db_files = log_db_files
        OmegaConf.set_struct(self._cfg, True)
        scenario_builder = build_scenario_builder(self._cfg)
        scenario_filter = build_scenario_filter(self._cfg.scenario_filter)
        scenarios: List[AbstractScenario] = scenario_builder.get_scenarios(scenario_filter, self._worker)
        return scenarios

    def _get_log_db_files_for_single_node(self) -> List[str]:
        """
        Get the list of log db files to be run on the current node
        :returns: list of log db files
        """
        if self._num_nodes == 1:
            return cast(List[str], self._cfg.scenario_builder.db_files)
        if not check_s3_path_exists(self._cfg.scenario_builder.db_files):
            raise AssertionError(f'DistributedScenarioFilter with multiple nodes only works in S3, but db_files path given was {self._cfg.scenario_builder.db_files}')
        all_files = get_db_filenames_from_load_path(self._cfg.scenario_builder.db_files)
        file_chunks = chunk_list(all_files, self._num_nodes)
        current_chunk = file_chunks[self._node_rank]
        return cast(List[str], current_chunk)

def _get_all_generated_csv(self, token_distribution_file_dir: Union[Path, str]) -> List[Tuple[str, str]]:
    """
        Read the csv files that every machine in the cluster generated and get the full list of (token, db_file) pairs
        :param token_distribution_file_dir: path where to the csv files are stored
        :returns: full list of (token, db_file) pairs
        """
    if self.synchronization_path.startswith('s3'):
        token_distribution_file_list = [el for el in expand_s3_dir(token_distribution_file_dir) if el.endswith('.csv')]
        token_distribution_list = []
        bucket, file_path = split_s3_path(Path(token_distribution_file_list[0]))
        s3_store = S3Store(s3_prefix=os.path.join('s3://', bucket))
        for token_distribution_file in token_distribution_file_list:
            with s3_store.get(token_distribution_file) as f:
                try:
                    token_distribution_list.append(pd.read_csv(f, delimiter=','))
                except EmptyDataError:
                    logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', token_distribution_file)
    else:
        token_distribution_list = []
        for file_name in os.listdir(token_distribution_file_dir):
            try:
                token_distribution_list.append(pd.read_csv(os.path.join(token_distribution_file_dir, str(file_name))))
            except EmptyDataError:
                logger.warning('Token file for worker %s was empty, this may mean that something is wrong with yourconfiguration, or just that all of the data on that worker got filtered out.', file_name)
    if not token_distribution_list:
        raise AssertionError('No scenarios found to simulate!')
    token_distribution_df = pd.concat(token_distribution_list, ignore_index=True)
    token_distribution = token_distribution_df.values.tolist()
    return cast(List[Tuple[str, str]], token_distribution)

def _get_token_and_log_chunk_on_single_node(self, token_distribution: List[Tuple[str, str]], db_files_path: Path) -> Tuple[List[str], List[str]]:
    """
        Get the list of tokens and the list of logs those tokens are found in restricted to the current node
        :param token_distribution: Full list of all (token, log_file) pairs to be divided among the nodes
        :param db_files_path: Path to the actual db files
        """
    db_files_path_sanitized = safe_path_to_string(db_files_path)
    if not check_s3_path_exists(db_files_path_sanitized):
        raise AssertionError(f'Multinode caching only works in S3, but db_files path given was {db_files_path_sanitized}')
    token_distribution_chunk = chunk_list(token_distribution, self._num_nodes)
    current_chunk = token_distribution_chunk[self._node_rank]
    current_logs_chunk = list({os.path.join(db_files_path_sanitized, f'{pair[1]}.db') for pair in current_chunk})
    current_token_chunk = [pair[0] for pair in current_chunk]
    return (current_token_chunk, current_logs_chunk)

def _write_token_csv_file(self, scenarios: List[AbstractScenario], token_distribution_file_dir: Union[str, Path]) -> None:
    """
        Writes a csv file of format token,log_name that stores the tokens associated with the given scenarios
        :param scenarios: Scenarios to take token/log pairs from
        :param token_distribution_file_dir: directory to write our csv file to
        """
    token_distribution_file = os.path.join(token_distribution_file_dir, f'{self._node_rank}.csv')
    token_log_pairs = [(scenario.token, scenario.log_name) for scenario in scenarios]
    os.makedirs(token_distribution_file_dir, exist_ok=True)
    token_log_pairs_df = pd.DataFrame(token_log_pairs)
    token_log_pairs_df.to_csv(token_distribution_file, index=False)

class TestIoUtils(unittest.TestCase):
    """
    A class to test that the I/O utilities in nuplan_devkit function properly.
    """

    def test_nupath(self) -> None:
        """
        Tests that converting NuPath to strings works properly.
        """
        example_s3_path = NuPath('s3://test-bucket/foo/bar/baz.txt')
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = str(example_s3_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_path = NuPath('/foo/bar/baz')
        expected_local_str = '/foo/bar/baz'
        actual_local_str = str(example_local_path)
        self.assertEqual(expected_local_str, actual_local_str)

    def test_safe_path_to_string(self) -> None:
        """
        Tests that converting paths to strings safely works properly.
        """
        example_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = safe_path_to_string(example_s3_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_path = Path('/foo/bar/baz')
        expected_local_str = '/foo/bar/baz'
        actual_local_str = safe_path_to_string(example_local_path)
        self.assertEqual(expected_local_str, actual_local_str)
        example_s3_str_path = 's3://test-bucket/foo/bar/baz.txt'
        expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
        actual_s3_str = safe_path_to_string(example_s3_str_path)
        self.assertEqual(expected_s3_str, actual_s3_str)
        example_local_str_path = '/foo/bar/baz'
        expected_local_str = '/foo/bar/baz'
        actual_local_str = safe_path_to_string(example_local_str_path)
        self.assertEqual(expected_local_str, actual_local_str)

    def test_save_buffer_locally(self) -> None:
        """
        Tests that saving a buffer locally works properly.
        """
        expected_buffer = b'test'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local_buffer.bin'
            save_buffer(output_file, expected_buffer)
            with open(output_file, 'rb') as f:
                reconstructed_buffer = f.read()
            self.assertEqual(expected_buffer, reconstructed_buffer)

    def test_save_buffer_s3(self) -> None:
        """
        Tests that saving a buffer to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.bin')
        uploaded_file_contents: Optional[bytes] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'rb') as f:
                uploaded_file_contents = f.read()
        expected_buffer = b'test'
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_buffer(output_file, expected_buffer)
            self.assertIsNotNone(uploaded_file_contents)
            assert uploaded_file_contents is not None
            self.assertEqual(expected_buffer, uploaded_file_contents)

    def test_save_object_as_pickle_locally(self) -> None:
        """
        Tests that saving a pickled object locally works properly.
        """
        expected_object = {'a': 1, 'b': 2}
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local.pkl'
            save_object_as_pickle(output_file, expected_object)
            with open(output_file, 'rb') as f:
                reconstructed_object = pickle.load(f)
            self.assertEqual(expected_object, reconstructed_object)

    def test_save_object_as_pickle_s3(self) -> None:
        """
        Tests that saving a pickled object to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.pkl')
        uploaded_file_contents: Optional[bytes] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'rb') as f:
                uploaded_file_contents = f.read()
        expected_object = {'a': 1, 'b': 2}
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_object_as_pickle(output_file, expected_object)
            self.assertIsNotNone(uploaded_file_contents)
            assert uploaded_file_contents is not None
            reconstructed_object: Dict[str, int] = pickle.loads(uploaded_file_contents)
            self.assertEqual(expected_object, reconstructed_object)

    def test_save_text_locally(self) -> None:
        """
        Tests that saving a text file locally works properly.
        """
        expected_text = 'test_save_text_locally.'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'local.txt'
            save_text(output_file, expected_text)
            with open(output_file, 'r') as f:
                reconstructed_text = f.read()
            self.assertEqual(expected_text, reconstructed_text)

    def test_save_text_s3(self) -> None:
        """
        Tests that saving a text file to s3 works properly.
        """
        upload_bucket_name = 'ml-caches'
        upload_path = Path('foo/bar/baz.pkl')
        uploaded_file_contents: Optional[str] = None

        async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
            """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
            nonlocal uploaded_file_contents
            self.assertEqual(upload_bucket_name, s3_bucket)
            self.assertEqual(upload_path, s3_key)
            with open(local_path, 'r') as f:
                uploaded_file_contents = f.read()
        expected_text = 'test_save_text_s3.'
        with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
            output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
            save_text(output_file, expected_text)
            self.assertIsNotNone(uploaded_file_contents)
            self.assertEqual(expected_text, uploaded_file_contents)

    def test_read_text_locally(self) -> None:
        """
        Tests that reading a text file locally works properly.
        """
        expected_text = 'some expected text.'
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'w') as f:
                f.write(expected_text)
            reconstructed_text = read_text(output_file)
            self.assertEqual(expected_text, reconstructed_text)

    def test_read_text_from_s3(self) -> None:
        """
        Tests that reading a text file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.txt'
        expected_text = 'some expected text.'
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return expected_text.encode('utf-8')
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_text = read_text(full_filepath)
            self.assertEqual(expected_text, reconstructed_text)

    def test_read_pickle_locally(self) -> None:
        """
        Tests that reading a pickle file locally works properly.
        """
        expected_obj = {'foo': 'bar'}
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'wb') as f:
                f.write(pickle.dumps(expected_obj))
            reconstructed_obj = read_pickle(output_file)
            self.assertEqual(expected_obj, reconstructed_obj)

    def test_read_pickle_from_s3(self) -> None:
        """
        Tests that reading a pickle file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.txt'
        expected_obj = {'foo': 'bar'}
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return pickle.dumps(expected_obj)
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_obj = read_pickle(full_filepath)
            self.assertEqual(expected_obj, reconstructed_obj)

    def test_read_binary_locally(self) -> None:
        """
        Tests that reading a binary file locally works properly.
        """
        expected_data = bytes([1, 2, 3, 4, 5])
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'read_text_locally.txt'
            with open(output_file, 'wb') as f:
                f.write(expected_data)
            reconstructed_data = read_binary(output_file)
            self.assertEqual(expected_data, reconstructed_data)

    def test_read_binary_from_s3(self) -> None:
        """
        Tests that reading a binary file from S3 works properly.
        """
        download_bucket = 'ml-caches'
        download_key = 'my/file/path.data'
        expected_data = bytes([1, 2, 3, 4, 5])
        full_filepath = Path(f's3://{download_bucket}') / download_key

        async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
            """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
            self.assertEqual(Path(download_key), s3_key)
            self.assertEqual(download_bucket, s3_bucket)
            return expected_data
        with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
            reconstructed_data = read_binary(full_filepath)
            self.assertEqual(expected_data, reconstructed_data)

    def test_path_exists_locally(self) -> None:
        """
        Tests that path_exists works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            file_to_create = tmp_dir_path / 'existing.txt'
            file_to_not_create = tmp_dir_path / 'not_existing.txt'
            with open(file_to_create, 'w') as f:
                f.write('some irrelevant text.')
            self.assertTrue(path_exists(file_to_create))
            self.assertFalse(path_exists(file_to_not_create))
            self.assertTrue(path_exists(tmp_dir_path, include_directories=True))
            self.assertFalse(path_exists(tmp_dir_path, include_directories=False))

    def test_path_exists_s3(self) -> None:
        """
        Tests that path_exists works for s3 files.
        """
        test_bucket = 'ml-caches'
        test_parent_dir = 'my/file/that'
        test_existing_file = f'{test_parent_dir}/exists.txt'
        test_non_existing_file = f'{test_parent_dir}/does_not_exist.txt'
        test_dir_path = Path(f's3://{test_bucket}') / test_parent_dir
        test_existing_path = Path(f's3://{test_bucket}') / test_existing_file
        test_non_existing_path = Path(f's3://{test_bucket}') / test_non_existing_file

        async def patch_check_s3_object_exists_async(s3_key: Path, s3_bucket: str) -> bool:
            """
            Patches the check_s3_object_exists_async method.
            :param key: The s3 key to check.
            :param bucket: The s3 bucket to check.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            if str(s3_key) == test_existing_file:
                return True
            elif str(s3_key) in [test_non_existing_file, test_parent_dir]:
                return False
            self.fail(f'Unexpected path passed to check_s3_object_exists patch: {s3_key}')

        async def patch_check_s3_path_exists_async(s3_path: str) -> bool:
            """
            Patches the check_s3_object_exists_async method.
            :param s3_path: The s3 path to check.
            :return: The mocked return value.
            """
            if s3_path in [safe_path_to_string(test_existing_path), safe_path_to_string(test_dir_path)]:
                return True
            elif s3_path == safe_path_to_string(test_non_existing_path):
                return False
            self.fail(f'Unexpected path passed to check_s3_path_exists patch: {s3_path}')
        with patch_with_validation('nuplan.common.utils.io_utils.check_s3_object_exists_async', patch_check_s3_object_exists_async), patch_with_validation('nuplan.common.utils.io_utils.check_s3_path_exists_async', patch_check_s3_path_exists_async):
            self.assertTrue(path_exists(test_existing_path))
            self.assertFalse(path_exists(test_non_existing_path))
            self.assertTrue(path_exists(test_dir_path, include_directories=True))
            self.assertFalse(path_exists(test_dir_path, include_directories=False))

    def test_list_files_in_directory_locally(self) -> None:
        """
        Tests that list_files_in_directory works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            self.assertEqual(list_files_in_directory(tmp_dir_path), [])
            test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
            for filename, contents in test_file_contents.items():
                with open(tmp_dir_path / filename, 'w') as f:
                    f.write(contents)
            output_files_in_directory = list_files_in_directory(tmp_dir_path)
            self.assertEqual(len(output_files_in_directory), len(test_file_contents))
            for output_filepath in output_files_in_directory:
                self.assertIn(output_filepath.name, test_file_contents)

    def test_list_files_in_directory_s3(self) -> None:
        """
        Tests that list_files_in_directory works for s3.
        """
        test_bucket = 'ml-caches'
        test_directory_key = Path('test_dir')
        test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
        test_files_in_s3 = ['a.txt', 'b.txt']
        expected_files = [Path(f'{test_directory_key}/{filename}') for filename in test_files_in_s3]
        expected_s3_paths = [Path(f's3://{test_bucket}') / filename for filename in expected_files]

        async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
            """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key)
            return expected_files
        with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async):
            output_filepaths = list_files_in_directory(test_directory_s3_path)
            self.assertEqual(output_filepaths, expected_s3_paths)

    def test_delete_file_locally(self) -> None:
        """
        Tests that delete_file works for local files.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
            test_file_paths = [tmp_dir_path / filename for filename in test_file_contents]
            for filename, contents in test_file_contents.items():
                with open(tmp_dir_path / filename, 'w') as f:
                    f.write(contents)
            self.assertEqual(set(tmp_dir_path.iterdir()), set(test_file_paths))
            for filename in test_file_contents:
                filepath = tmp_dir_path / filename
                delete_file(filepath)
                self.assertNotIn(filepath, tmp_dir_path.iterdir())
            self.assertEqual(len(list(tmp_dir_path.iterdir())), 0)
            with self.assertRaises(ValueError):
                delete_file(tmp_dir_path)

    def test_delete_file_s3(self) -> None:
        """
        Tests that delete_file works for s3.
        """
        test_bucket = 'ml-caches'
        test_directory_key = Path('test_dir')
        test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
        test_files_in_s3 = {'a.txt', 'b.txt'}

        def get_s3_key(filename: str) -> Path:
            """
            Turns a filename into an s3 key.
            """
            return Path(f'{test_directory_key}/{filename}')

        def list_s3_keys() -> List[Path]:
            """
            Lists the keys in s3.
            :return: S3 keys in the mocked test directory.
            """
            return [get_s3_key(filename) for filename in test_files_in_s3]

        async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
            """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key)
            return list_s3_keys()

        async def patch_delete_file_from_s3_async(s3_key: Path, s3_bucket: str) -> None:
            """
            Patches the delete_file_from_s3_async method.
            :param s3_key: The s3 key to delete.
            :param s3_bucket: The s3 bucket.
            """
            nonlocal test_files_in_s3
            self.assertEqual(test_bucket, s3_bucket)
            self.assertEqual(test_directory_key, s3_key.parent)
            self.assertIn(s3_key.name, test_files_in_s3)
            test_files_in_s3.remove(s3_key.name)
        with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async), patch_with_validation('nuplan.common.utils.io_utils.delete_file_from_s3_async', patch_delete_file_from_s3_async):
            initial_s3_keys = list_s3_keys()
            for filename in test_files_in_s3:
                self.assertIn(get_s3_key(filename), initial_s3_keys)
            for filename in set(test_files_in_s3):
                s3_path = test_directory_s3_path / filename
                delete_file(s3_path)
                self.assertNotIn(get_s3_key(filename), list_s3_keys())

def test_nupath(self) -> None:
    """
        Tests that converting NuPath to strings works properly.
        """
    example_s3_path = NuPath('s3://test-bucket/foo/bar/baz.txt')
    expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
    actual_s3_str = str(example_s3_path)
    self.assertEqual(expected_s3_str, actual_s3_str)
    example_local_path = NuPath('/foo/bar/baz')
    expected_local_str = '/foo/bar/baz'
    actual_local_str = str(example_local_path)
    self.assertEqual(expected_local_str, actual_local_str)

def test_safe_path_to_string(self) -> None:
    """
        Tests that converting paths to strings safely works properly.
        """
    example_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
    expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
    actual_s3_str = safe_path_to_string(example_s3_path)
    self.assertEqual(expected_s3_str, actual_s3_str)
    example_local_path = Path('/foo/bar/baz')
    expected_local_str = '/foo/bar/baz'
    actual_local_str = safe_path_to_string(example_local_path)
    self.assertEqual(expected_local_str, actual_local_str)
    example_s3_str_path = 's3://test-bucket/foo/bar/baz.txt'
    expected_s3_str = 's3://test-bucket/foo/bar/baz.txt'
    actual_s3_str = safe_path_to_string(example_s3_str_path)
    self.assertEqual(expected_s3_str, actual_s3_str)
    example_local_str_path = '/foo/bar/baz'
    expected_local_str = '/foo/bar/baz'
    actual_local_str = safe_path_to_string(example_local_str_path)
    self.assertEqual(expected_local_str, actual_local_str)

def test_save_buffer_locally(self) -> None:
    """
        Tests that saving a buffer locally works properly.
        """
    expected_buffer = b'test'
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'local_buffer.bin'
        save_buffer(output_file, expected_buffer)
        with open(output_file, 'rb') as f:
            reconstructed_buffer = f.read()
        self.assertEqual(expected_buffer, reconstructed_buffer)

def test_save_buffer_s3(self) -> None:
    """
        Tests that saving a buffer to s3 works properly.
        """
    upload_bucket_name = 'ml-caches'
    upload_path = Path('foo/bar/baz.bin')
    uploaded_file_contents: Optional[bytes] = None

    async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
        """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
        nonlocal uploaded_file_contents
        self.assertEqual(upload_bucket_name, s3_bucket)
        self.assertEqual(upload_path, s3_key)
        with open(local_path, 'rb') as f:
            uploaded_file_contents = f.read()
    expected_buffer = b'test'
    with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
        output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
        save_buffer(output_file, expected_buffer)
        self.assertIsNotNone(uploaded_file_contents)
        assert uploaded_file_contents is not None
        self.assertEqual(expected_buffer, uploaded_file_contents)

def test_save_object_as_pickle_locally(self) -> None:
    """
        Tests that saving a pickled object locally works properly.
        """
    expected_object = {'a': 1, 'b': 2}
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'local.pkl'
        save_object_as_pickle(output_file, expected_object)
        with open(output_file, 'rb') as f:
            reconstructed_object = pickle.load(f)
        self.assertEqual(expected_object, reconstructed_object)

def test_save_object_as_pickle_s3(self) -> None:
    """
        Tests that saving a pickled object to s3 works properly.
        """
    upload_bucket_name = 'ml-caches'
    upload_path = Path('foo/bar/baz.pkl')
    uploaded_file_contents: Optional[bytes] = None

    async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
        """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
        nonlocal uploaded_file_contents
        self.assertEqual(upload_bucket_name, s3_bucket)
        self.assertEqual(upload_path, s3_key)
        with open(local_path, 'rb') as f:
            uploaded_file_contents = f.read()
    expected_object = {'a': 1, 'b': 2}
    with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
        output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
        save_object_as_pickle(output_file, expected_object)
        self.assertIsNotNone(uploaded_file_contents)
        assert uploaded_file_contents is not None
        reconstructed_object: Dict[str, int] = pickle.loads(uploaded_file_contents)
        self.assertEqual(expected_object, reconstructed_object)

def test_save_text_locally(self) -> None:
    """
        Tests that saving a text file locally works properly.
        """
    expected_text = 'test_save_text_locally.'
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'local.txt'
        save_text(output_file, expected_text)
        with open(output_file, 'r') as f:
            reconstructed_text = f.read()
        self.assertEqual(expected_text, reconstructed_text)

def test_save_text_s3(self) -> None:
    """
        Tests that saving a text file to s3 works properly.
        """
    upload_bucket_name = 'ml-caches'
    upload_path = Path('foo/bar/baz.pkl')
    uploaded_file_contents: Optional[str] = None

    async def patch_upload_file_to_s3_async(local_path: Path, s3_key: Path, s3_bucket: str) -> None:
        """
            Patch for upload_file_to_s3_async method.
            :param local_path: The passed local_path.
            :param s3_key: The passed s3_key.
            :param s3_bucket: The passed s3_bucket.
            """
        nonlocal uploaded_file_contents
        self.assertEqual(upload_bucket_name, s3_bucket)
        self.assertEqual(upload_path, s3_key)
        with open(local_path, 'r') as f:
            uploaded_file_contents = f.read()
    expected_text = 'test_save_text_s3.'
    with patch_with_validation('nuplan.common.utils.io_utils.upload_file_to_s3_async', patch_upload_file_to_s3_async):
        output_file = Path(f's3://{upload_bucket_name}') / f'{upload_path}'
        save_text(output_file, expected_text)
        self.assertIsNotNone(uploaded_file_contents)
        self.assertEqual(expected_text, uploaded_file_contents)

def test_read_text_locally(self) -> None:
    """
        Tests that reading a text file locally works properly.
        """
    expected_text = 'some expected text.'
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'read_text_locally.txt'
        with open(output_file, 'w') as f:
            f.write(expected_text)
        reconstructed_text = read_text(output_file)
        self.assertEqual(expected_text, reconstructed_text)

def test_read_text_from_s3(self) -> None:
    """
        Tests that reading a text file from S3 works properly.
        """
    download_bucket = 'ml-caches'
    download_key = 'my/file/path.txt'
    expected_text = 'some expected text.'
    full_filepath = Path(f's3://{download_bucket}') / download_key

    async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
        """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
        self.assertEqual(Path(download_key), s3_key)
        self.assertEqual(download_bucket, s3_bucket)
        return expected_text.encode('utf-8')
    with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
        reconstructed_text = read_text(full_filepath)
        self.assertEqual(expected_text, reconstructed_text)

def test_read_pickle_locally(self) -> None:
    """
        Tests that reading a pickle file locally works properly.
        """
    expected_obj = {'foo': 'bar'}
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'read_text_locally.txt'
        with open(output_file, 'wb') as f:
            f.write(pickle.dumps(expected_obj))
        reconstructed_obj = read_pickle(output_file)
        self.assertEqual(expected_obj, reconstructed_obj)

def test_read_pickle_from_s3(self) -> None:
    """
        Tests that reading a pickle file from S3 works properly.
        """
    download_bucket = 'ml-caches'
    download_key = 'my/file/path.txt'
    expected_obj = {'foo': 'bar'}
    full_filepath = Path(f's3://{download_bucket}') / download_key

    async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
        """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
        self.assertEqual(Path(download_key), s3_key)
        self.assertEqual(download_bucket, s3_bucket)
        return pickle.dumps(expected_obj)
    with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
        reconstructed_obj = read_pickle(full_filepath)
        self.assertEqual(expected_obj, reconstructed_obj)

def test_read_binary_locally(self) -> None:
    """
        Tests that reading a binary file locally works properly.
        """
    expected_data = bytes([1, 2, 3, 4, 5])
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / 'read_text_locally.txt'
        with open(output_file, 'wb') as f:
            f.write(expected_data)
        reconstructed_data = read_binary(output_file)
        self.assertEqual(expected_data, reconstructed_data)

def test_read_binary_from_s3(self) -> None:
    """
        Tests that reading a binary file from S3 works properly.
        """
    download_bucket = 'ml-caches'
    download_key = 'my/file/path.data'
    expected_data = bytes([1, 2, 3, 4, 5])
    full_filepath = Path(f's3://{download_bucket}') / download_key

    async def patch_read_binary_file_contents_from_s3_async(s3_key: Path, s3_bucket: str) -> bytes:
        """
            A patch for the read_binary_file_contents_from_s3_async method.
            :param s3_key: The passed key
            :param s3_bucket: The passed bucket.
            """
        self.assertEqual(Path(download_key), s3_key)
        self.assertEqual(download_bucket, s3_bucket)
        return expected_data
    with patch_with_validation('nuplan.common.utils.io_utils.read_binary_file_contents_from_s3_async', patch_read_binary_file_contents_from_s3_async):
        reconstructed_data = read_binary(full_filepath)
        self.assertEqual(expected_data, reconstructed_data)

def test_path_exists_locally(self) -> None:
    """
        Tests that path_exists works for local files.
        """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        file_to_create = tmp_dir_path / 'existing.txt'
        file_to_not_create = tmp_dir_path / 'not_existing.txt'
        with open(file_to_create, 'w') as f:
            f.write('some irrelevant text.')
        self.assertTrue(path_exists(file_to_create))
        self.assertFalse(path_exists(file_to_not_create))
        self.assertTrue(path_exists(tmp_dir_path, include_directories=True))
        self.assertFalse(path_exists(tmp_dir_path, include_directories=False))

def test_path_exists_s3(self) -> None:
    """
        Tests that path_exists works for s3 files.
        """
    test_bucket = 'ml-caches'
    test_parent_dir = 'my/file/that'
    test_existing_file = f'{test_parent_dir}/exists.txt'
    test_non_existing_file = f'{test_parent_dir}/does_not_exist.txt'
    test_dir_path = Path(f's3://{test_bucket}') / test_parent_dir
    test_existing_path = Path(f's3://{test_bucket}') / test_existing_file
    test_non_existing_path = Path(f's3://{test_bucket}') / test_non_existing_file

    async def patch_check_s3_object_exists_async(s3_key: Path, s3_bucket: str) -> bool:
        """
            Patches the check_s3_object_exists_async method.
            :param key: The s3 key to check.
            :param bucket: The s3 bucket to check.
            :return: The mocked return value.
            """
        self.assertEqual(test_bucket, s3_bucket)
        if str(s3_key) == test_existing_file:
            return True
        elif str(s3_key) in [test_non_existing_file, test_parent_dir]:
            return False
        self.fail(f'Unexpected path passed to check_s3_object_exists patch: {s3_key}')

    async def patch_check_s3_path_exists_async(s3_path: str) -> bool:
        """
            Patches the check_s3_object_exists_async method.
            :param s3_path: The s3 path to check.
            :return: The mocked return value.
            """
        if s3_path in [safe_path_to_string(test_existing_path), safe_path_to_string(test_dir_path)]:
            return True
        elif s3_path == safe_path_to_string(test_non_existing_path):
            return False
        self.fail(f'Unexpected path passed to check_s3_path_exists patch: {s3_path}')
    with patch_with_validation('nuplan.common.utils.io_utils.check_s3_object_exists_async', patch_check_s3_object_exists_async), patch_with_validation('nuplan.common.utils.io_utils.check_s3_path_exists_async', patch_check_s3_path_exists_async):
        self.assertTrue(path_exists(test_existing_path))
        self.assertFalse(path_exists(test_non_existing_path))
        self.assertTrue(path_exists(test_dir_path, include_directories=True))
        self.assertFalse(path_exists(test_dir_path, include_directories=False))

def test_list_files_in_directory_locally(self) -> None:
    """
        Tests that list_files_in_directory works for local files.
        """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        self.assertEqual(list_files_in_directory(tmp_dir_path), [])
        test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
        for filename, contents in test_file_contents.items():
            with open(tmp_dir_path / filename, 'w') as f:
                f.write(contents)
        output_files_in_directory = list_files_in_directory(tmp_dir_path)
        self.assertEqual(len(output_files_in_directory), len(test_file_contents))
        for output_filepath in output_files_in_directory:
            self.assertIn(output_filepath.name, test_file_contents)

def test_list_files_in_directory_s3(self) -> None:
    """
        Tests that list_files_in_directory works for s3.
        """
    test_bucket = 'ml-caches'
    test_directory_key = Path('test_dir')
    test_directory_s3_path = Path(f's3://{test_bucket}/{test_directory_key}')
    test_files_in_s3 = ['a.txt', 'b.txt']
    expected_files = [Path(f'{test_directory_key}/{filename}') for filename in test_files_in_s3]
    expected_s3_paths = [Path(f's3://{test_bucket}') / filename for filename in expected_files]

    async def patch_list_files_in_s3_directory_async(s3_key: Path, s3_bucket: str, filter_suffix: str='') -> List[Path]:
        """
            Patches the list_files_in_s3_directory_async method.
            :param key: The s3 key of the directory.
            :param bucket: The s3 bucket of the directory.
            :param filter_suffix: Unused.
            :return: The mocked return value.
            """
        self.assertEqual(test_bucket, s3_bucket)
        self.assertEqual(test_directory_key, s3_key)
        return expected_files
    with patch_with_validation('nuplan.common.utils.io_utils.list_files_in_s3_directory_async', patch_list_files_in_s3_directory_async):
        output_filepaths = list_files_in_directory(test_directory_s3_path)
        self.assertEqual(output_filepaths, expected_s3_paths)

def test_delete_file_locally(self) -> None:
    """
        Tests that delete_file works for local files.
        """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        test_file_contents = {'a.txt': 'test file a.', 'b.txt': 'test file b.'}
        test_file_paths = [tmp_dir_path / filename for filename in test_file_contents]
        for filename, contents in test_file_contents.items():
            with open(tmp_dir_path / filename, 'w') as f:
                f.write(contents)
        self.assertEqual(set(tmp_dir_path.iterdir()), set(test_file_paths))
        for filename in test_file_contents:
            filepath = tmp_dir_path / filename
            delete_file(filepath)
            self.assertNotIn(filepath, tmp_dir_path.iterdir())
        self.assertEqual(len(list(tmp_dir_path.iterdir())), 0)
        with self.assertRaises(ValueError):
            delete_file(tmp_dir_path)

def get_s3_key(filename: str) -> Path:
    """
            Turns a filename into an s3 key.
            """
    return Path(f'{test_directory_key}/{filename}')

class TestFileBackedBarrier(unittest.TestCase):
    """
    A class to test that the file backed barrier works properly.
    """

    def test_file_backed_barrier_functions_normal_case_local(self) -> None:
        """
        Tests that the file backed barrier functions properly locally.
        """
        sleep_interval_sec = 10
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                if current_time == sleep_interval_sec + 30:
                    current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                    self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
                else:
                    current_time += sleep_interval_sec
                    self.assertEqual(sleep_interval_sec, sleep_time)
                if current_time == 40:
                    FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
                if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                    FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
                return current_time
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
                barrier = FileBackedBarrier(tmp_dir)
                barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

    def test_file_backed_barrier_functions_normal_case_s3(self) -> None:
        """
        Tests that the file backed barrier functions properly in s3.
        """
        sleep_interval_sec = 10
        sample_s3_path = 's3://ml-caches/mitchell.spryn/barrier'
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                if current_time == sleep_interval_sec + 30:
                    current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                    self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
                else:
                    current_time += sleep_interval_sec
                    self.assertEqual(sleep_interval_sec, sleep_time)
                if current_time == 40:
                    FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
                if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                    FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
                return current_time

            def patch_get_s3_client() -> unittest.mock.Mock:
                """
                Mocks the get_s3_client method.
                """

                def patch_s3_client_put_object(Body: bytes, Bucket: str, Key: str) -> None:
                    """
                    A patch for the s3 client put object method.
                    :param body: The body passed to the method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                    self.assertTrue(len(Body) > 0)
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/1', Key)
                    check_file = tmp_dir / '1'
                    self.assertFalse(check_file.exists())
                    with open(check_file, 'w') as f:
                        f.write('x')

                def patch_s3_client_delete_object(Bucket: str, Key: str) -> None:
                    """
                    A patch for the s3 client put object method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/1', Key)
                    check_file = tmp_dir / '1'
                    self.assertTrue(check_file.exists())
                    check_file.unlink()

                def patch_s3_client_list_objects_v2(Bucket: str, Prefix: str) -> Dict[str, List[Dict[str, str]]]:
                    """
                    A patch for the s3 client list objects v2 method.
                    :param Bucket: The bucket passed.
                    :param Prefix: The prefix passed.
                    """
                    self.assertEqual('ml-caches', Bucket)
                    self.assertEqual('mitchell.spryn/barrier/', Prefix)
                    return {'Contents': [{'Key': f's3://ml-caches/mitchell.spryn/barrier/{p.stem}'} for p in tmp_dir.glob('**/*') if p.is_file()]}
                mock_client = unittest.mock.Mock()
                mock_client.put_object = patch_s3_client_put_object
                mock_client.list_objects_v2 = patch_s3_client_list_objects_v2
                mock_client.delete_object = patch_s3_client_delete_object
                return mock_client
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.get_s3_client', patch_get_s3_client):
                barrier = FileBackedBarrier(Path(sample_s3_path))
                barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

    def test_file_backed_barrier_timeout(self) -> None:
        """
        Tests that the timeout feature works properly.
        """
        sleep_interval_sec = 10
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            tmp_dir = Path(tmp_dir_str)
            current_time = 0.0

            def patch_time_sleep(sleep_time: float) -> None:
                """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
                nonlocal current_time
                self.assertEqual(sleep_interval_sec, sleep_time)
                current_time += sleep_interval_sec

            def patch_time_time() -> float:
                """
                A patch for the time.time method.
                :return: The current time.
                """
                nonlocal current_time
                return current_time
            with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
                barrier = FileBackedBarrier(tmp_dir)
                with self.assertRaises(TimeoutError):
                    barrier.wait_barrier('1', {'1', '2'}, timeout_s=40, poll_interval_s=sleep_interval_sec)

def test_file_backed_barrier_functions_normal_case_local(self) -> None:
    """
        Tests that the file backed barrier functions properly locally.
        """
    sleep_interval_sec = 10
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        current_time = 0.0

        def patch_time_sleep(sleep_time: float) -> None:
            """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
            nonlocal current_time
            if current_time == sleep_interval_sec + 30:
                current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
            else:
                current_time += sleep_interval_sec
                self.assertEqual(sleep_interval_sec, sleep_time)
            if current_time == 40:
                FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
            if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

        def patch_time_time() -> float:
            """
                A patch for the time.time method.
                :return: The current time.
                """
            nonlocal current_time
            self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
            return current_time
        with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
            barrier = FileBackedBarrier(tmp_dir)
            barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

def patch_time_sleep(sleep_time: float) -> None:
    """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
    nonlocal current_time
    self.assertEqual(sleep_interval_sec, sleep_time)
    current_time += sleep_interval_sec

def test_file_backed_barrier_functions_normal_case_s3(self) -> None:
    """
        Tests that the file backed barrier functions properly in s3.
        """
    sleep_interval_sec = 10
    sample_s3_path = 's3://ml-caches/mitchell.spryn/barrier'
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        current_time = 0.0

        def patch_time_sleep(sleep_time: float) -> None:
            """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
            nonlocal current_time
            if current_time == sleep_interval_sec + 30:
                current_time += SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec
                self.assertEqual(sleep_interval_sec * SLEEP_MULTIPLIER_BEFORE_CLEANUP, sleep_time)
            else:
                current_time += sleep_interval_sec
                self.assertEqual(sleep_interval_sec, sleep_time)
            if current_time == 40:
                FileBackedBarrier(tmp_dir)._register_activity_id_complete('2')
            if current_time == 70 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec:
                FileBackedBarrier(tmp_dir)._remove_activity_after_processing('2')

        def patch_time_time() -> float:
            """
                A patch for the time.time method.
                :return: The current time.
                """
            nonlocal current_time
            self.assertLess(current_time, 80 + SLEEP_MULTIPLIER_BEFORE_CLEANUP * sleep_interval_sec)
            return current_time

        def patch_get_s3_client() -> unittest.mock.Mock:
            """
                Mocks the get_s3_client method.
                """

            def patch_s3_client_put_object(Body: bytes, Bucket: str, Key: str) -> None:
                """
                    A patch for the s3 client put object method.
                    :param body: The body passed to the method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                self.assertTrue(len(Body) > 0)
                self.assertEqual('ml-caches', Bucket)
                self.assertEqual('mitchell.spryn/barrier/1', Key)
                check_file = tmp_dir / '1'
                self.assertFalse(check_file.exists())
                with open(check_file, 'w') as f:
                    f.write('x')

            def patch_s3_client_delete_object(Bucket: str, Key: str) -> None:
                """
                    A patch for the s3 client put object method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
                self.assertEqual('ml-caches', Bucket)
                self.assertEqual('mitchell.spryn/barrier/1', Key)
                check_file = tmp_dir / '1'
                self.assertTrue(check_file.exists())
                check_file.unlink()

            def patch_s3_client_list_objects_v2(Bucket: str, Prefix: str) -> Dict[str, List[Dict[str, str]]]:
                """
                    A patch for the s3 client list objects v2 method.
                    :param Bucket: The bucket passed.
                    :param Prefix: The prefix passed.
                    """
                self.assertEqual('ml-caches', Bucket)
                self.assertEqual('mitchell.spryn/barrier/', Prefix)
                return {'Contents': [{'Key': f's3://ml-caches/mitchell.spryn/barrier/{p.stem}'} for p in tmp_dir.glob('**/*') if p.is_file()]}
            mock_client = unittest.mock.Mock()
            mock_client.put_object = patch_s3_client_put_object
            mock_client.list_objects_v2 = patch_s3_client_list_objects_v2
            mock_client.delete_object = patch_s3_client_delete_object
            return mock_client
        with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.get_s3_client', patch_get_s3_client):
            barrier = FileBackedBarrier(Path(sample_s3_path))
            barrier.wait_barrier('1', {'1', '2'}, timeout_s=None, poll_interval_s=sleep_interval_sec)

def patch_s3_client_put_object(Body: bytes, Bucket: str, Key: str) -> None:
    """
                    A patch for the s3 client put object method.
                    :param body: The body passed to the method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
    self.assertTrue(len(Body) > 0)
    self.assertEqual('ml-caches', Bucket)
    self.assertEqual('mitchell.spryn/barrier/1', Key)
    check_file = tmp_dir / '1'
    self.assertFalse(check_file.exists())
    with open(check_file, 'w') as f:
        f.write('x')

def patch_s3_client_delete_object(Bucket: str, Key: str) -> None:
    """
                    A patch for the s3 client put object method.
                    :param bucket: The bucket passed to the method.
                    :param key: The key passed to the method.
                    """
    self.assertEqual('ml-caches', Bucket)
    self.assertEqual('mitchell.spryn/barrier/1', Key)
    check_file = tmp_dir / '1'
    self.assertTrue(check_file.exists())
    check_file.unlink()

def patch_s3_client_list_objects_v2(Bucket: str, Prefix: str) -> Dict[str, List[Dict[str, str]]]:
    """
                    A patch for the s3 client list objects v2 method.
                    :param Bucket: The bucket passed.
                    :param Prefix: The prefix passed.
                    """
    self.assertEqual('ml-caches', Bucket)
    self.assertEqual('mitchell.spryn/barrier/', Prefix)
    return {'Contents': [{'Key': f's3://ml-caches/mitchell.spryn/barrier/{p.stem}'} for p in tmp_dir.glob('**/*') if p.is_file()]}

def test_file_backed_barrier_timeout(self) -> None:
    """
        Tests that the timeout feature works properly.
        """
    sleep_interval_sec = 10
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        current_time = 0.0

        def patch_time_sleep(sleep_time: float) -> None:
            """
                A patch for the time.sleep method.
                :param sleep_time: The time to sleep.
                """
            nonlocal current_time
            self.assertEqual(sleep_interval_sec, sleep_time)
            current_time += sleep_interval_sec

        def patch_time_time() -> float:
            """
                A patch for the time.time method.
                :return: The current time.
                """
            nonlocal current_time
            return current_time
        with unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.sleep', patch_time_sleep), unittest.mock.patch('nuplan.common.utils.file_backed_barrier.time.time', patch_time_time):
            barrier = FileBackedBarrier(tmp_dir)
            with self.assertRaises(TimeoutError):
                barrier.wait_barrier('1', {'1', '2'}, timeout_s=40, poll_interval_s=sleep_interval_sec)

class TestDistributedScenarioFilter(unittest.TestCase):
    """
    Test the distributed scenario filter that is intended to be used to split work across multiple nodes
    """

    def setUp(self) -> None:
        """
        Build some useful mocks to use in a variety of functions
        """
        self.scenario_builder_mock = MagicMock(AbstractScenarioBuilder)
        self.mock_scenarios = [MagicMock(AbstractScenario), MagicMock(AbstractScenario)]
        self.scenario_builder_mock.get_scenarios = MagicMock()
        self.scenario_builder_mock.get_scenarios.return_value = self.mock_scenarios
        self.build_scenario_builder_mock = MagicMock()
        self.build_scenario_builder_mock.return_value = self.scenario_builder_mock
        self.scenario_filter_mock = MagicMock(ScenarioFilter)
        self.build_scenario_filter_mock = MagicMock()
        self.build_scenario_filter_mock.return_value = self.scenario_filter_mock
        self.mock_dbs = ['file_1', 'file_2']
        self.cfg_mock = MagicMock()
        self.cfg_mock.scenario_builder = MagicMock()
        self.cfg_mock.scenario_builder.db_files = self.mock_dbs
        self.cfg_mock.scenario_filter = MagicMock()
        self.mock_scenarios[0].token = 'a'
        self.mock_scenarios[0].log_name = '1.log'
        self.mock_scenarios[1].token = 'b'
        self.mock_scenarios[1].log_name = '2.log'
        self.worker_mock = MagicMock(WorkerPool)
        self.dist_filter_get_scenarios = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, 'path')
        self.dist_filter_get_scenarios._get_log_db_files_for_single_node = MagicMock()
        self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files = MagicMock()
        self.dist_filter_get_scenarios._get_repartition_tokens = MagicMock()
        self.dist_filter_get_scenarios._get_repartition_tokens.return_value = (['a'], ['1.log'])

    def test_get_scenarios_scenario_based(self) -> None:
        """
        Test that get_scenarios does full repartitioning in this case
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.OmegaConf.set_struct'):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SCENARIO_BASED
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(self.mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_called()
            self.assertListEqual(self.cfg_mock.scenario_filter.scenario_tokens, ['a'])
            self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['1.log'])
            self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
            self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

    def test_get_scenarios_multiple_nodes_log_file_mode(self) -> None:
        """
        Test that get_scenarios we only call the methods that get a chunk of log files + gets the scenarios from that chunk
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.LOG_FILE_BASED
            mock_scenarios = [MagicMock()]
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.return_value = mock_scenarios
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
            self.build_scenario_builder_mock.assert_not_called()
            self.build_scenario_filter_mock.assert_not_called()

    def test_get_scenarios_single_node(self) -> None:
        """
        Test that get_scenarios just returns the scenarios built by the scenario builder in this case.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            self.dist_filter_get_scenarios._distributed_mode = DistributedMode.SINGLE_NODE
            scenarios = self.dist_filter_get_scenarios.get_scenarios()
            self.assertEqual(self.mock_scenarios, scenarios)
            self.dist_filter_get_scenarios._get_log_db_files_for_single_node.assert_not_called()
            self.dist_filter_get_scenarios._get_scenarios_from_list_of_log_files.assert_not_called()
            self.dist_filter_get_scenarios._get_repartition_tokens.assert_not_called()
            self.build_scenario_builder_mock.assert_called_with(cfg=self.cfg_mock)
            self.build_scenario_filter_mock.assert_called_with(cfg=self.cfg_mock.scenario_filter)

    def test_get_repartition_tokens(self) -> None:
        """
        Test that we make all of the expected calls, in the expected order, to repartition the tokens.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_unique_job_id') as id, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.distributed_sync') as dist:
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 'path', timeout_seconds=5)
            dist_filter._write_token_csv_file = MagicMock()
            dist_filter._get_all_generated_csv = MagicMock()
            dist_filter._get_token_and_log_chunk_on_single_node = MagicMock()
            id.return_value = '1'
            dist_filter._get_all_generated_csv.return_value = [('a', '1'), ('b', '2')]
            dist_filter._get_token_and_log_chunk_on_single_node.return_value = (['a', 'b'], ['path/1.db', 'path/2.db'])
            manager = Mock()
            manager.attach_mock(dist_filter._write_token_csv_file, 'write_csv')
            manager.attach_mock(dist, 'sync')
            manager.attach_mock(dist_filter._get_all_generated_csv, 'get_csvs')
            manager.attach_mock(dist_filter._get_token_and_log_chunk_on_single_node, 'chunk')
            output = dist_filter._get_repartition_tokens(scenarios=self.mock_scenarios)
            self.assertEqual(output, (['a', 'b'], ['path/1.db', 'path/2.db']))
            expected_calls = [call.write_csv(self.mock_scenarios, Path('path/tokens/1')), call.sync(Path('path/barrier/1'), timeout_seconds=5), call.get_csvs(Path('path/tokens/1')), call.chunk([('a', '1'), ('b', '2')], Path('.'))]
            self.assertListEqual(manager.mock_calls, expected_calls)

    def test_get_all_generated_csv_s3(self) -> None:
        """
        Test that we get all of the tokens from the csv files we have created when running in mocked s3.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.expand_s3_dir') as expand, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.split_s3_path') as split, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.S3Store') as store:
            with tempfile.TemporaryDirectory() as tmp_dir_str:
                dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, 's3://dummy/path')
                dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
                split.return_value = ('bucket', 'file')
                expand.return_value = [os.path.join(tmp_dir_str, '0.csv')]

                def mock_get(path: str) -> IO[str]:
                    """
                    Mock get for the s3 store we mock, just opens the file as a local file.
                    """
                    return open(path)
                store.return_value = MagicMock()
                store.return_value.get = mock_get
                filter_output = dist_filter._get_all_generated_csv('s3://dummy/path')
                self.assertEqual(filter_output, [['a', '1.log'], ['b', '2.log']])

    def test_get_all_generated_csv_local(self) -> None:
        """
        Test that we get all of the tokens from the csv files we have created when running locally.
        """
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, tmp_dir_str)
            dist_filter_2 = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 1, 2, tmp_dir_str)
            dist_filter._write_token_csv_file(self.mock_scenarios[:1], tmp_dir_str)
            dist_filter_2._write_token_csv_file(self.mock_scenarios[1:], tmp_dir_str)
            filter_1_output = dist_filter._get_all_generated_csv(tmp_dir_str)
            filter_2_output = dist_filter_2._get_all_generated_csv(tmp_dir_str)
            self.assertListEqual(filter_1_output, filter_2_output)
            expected_token_set = {('a', '1.log'), ('b', '2.log')}
            self.assertEqual(len(filter_1_output), len(expected_token_set))
            self.assertSetEqual({tuple(i) for i in filter_1_output}, expected_token_set)

    def test_get_token_and_log_chunk_on_single_node(self) -> None:
        """
        Test that we correctly chunk the tokens and associated log names on each node.
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists'):
            db_files_path = Path('s3://dummy/path')
            token_distribution = [('a', '1'), ('b', '1'), ('c', '2'), ('d', '2')]
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
            tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
            self.assertSetEqual(set(tokens), {'a', 'b', 'c', 'd'})
            self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db', 's3://dummy/path/2.db'})
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
            tokens, log_files = dist_filter._get_token_and_log_chunk_on_single_node(token_distribution, db_files_path)
            self.assertSetEqual(set(tokens), {'a', 'b'})
            self.assertSetEqual(set(log_files), {'s3://dummy/path/1.db'})

    def test_write_token_csv_file(self) -> None:
        """
        Test that we correctly write out a csv file for the current node for the list of scenarios provided
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        with tempfile.TemporaryDirectory() as tmp_dir_str:
            dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
            expected_path = os.path.join(tmp_dir_str, '0.csv')
            self.assertTrue(os.path.exists(expected_path))
            csv_out = pd.read_csv(expected_path).to_dict()
            self.assertEqual(csv_out, {'0': {0: 'a', 1: 'b'}, '1': {0: '1.log', 1: '2.log'}})

    def test_get_scenarios_from_list_of_log_files(self) -> None:
        """
        Test that we build a scenario builder with the proper db files updated, and successfully get scenarios from it
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_builder', self.build_scenario_builder_mock), unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.build_scenario_filter', self.build_scenario_filter_mock):
            scenarios = dist_filter._get_scenarios_from_list_of_log_files(['file_3'])
            self.assertListEqual(self.cfg_mock.scenario_builder.db_files, ['file_3'])
            self.build_scenario_filter_mock.assert_called_with(self.cfg_mock.scenario_filter)
            self.build_scenario_builder_mock.assert_called_with(self.cfg_mock)
            self.scenario_builder_mock.get_scenarios.assert_called_with(self.scenario_filter_mock, self.worker_mock)
            self.assertEqual(scenarios, self.mock_scenarios)

    def test_get_log_db_files_for_single_node_non_distributed(self) -> None:
        """
        Test that in a non-distributed context we simply return all the db files in the config
        """
        dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
        logs = dist_filter._get_log_db_files_for_single_node()
        self.assertListEqual(logs, self.mock_dbs)

    def test_get_log_db_files_for_single_node_distributed(self) -> None:
        """
        Test that in a distributed context we call the proper functions and chunk the data as expected
        """
        with unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.get_db_filenames_from_load_path') as get, unittest.mock.patch('nuplan.common.utils.distributed_scenario_filter.check_s3_path_exists') as check:
            get.side_effect = lambda x: x
            check.return_value = True
            dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 2, '')
            logs = dist_filter._get_log_db_files_for_single_node()
            self.assertListEqual(logs, self.mock_dbs[:1])

def mock_get(path: str) -> IO[str]:
    """
                    Mock get for the s3 store we mock, just opens the file as a local file.
                    """
    return open(path)

def test_write_token_csv_file(self) -> None:
    """
        Test that we correctly write out a csv file for the current node for the list of scenarios provided
        """
    dist_filter = DistributedScenarioFilter(self.cfg_mock, self.worker_mock, 0, 1, '')
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        dist_filter._write_token_csv_file(self.mock_scenarios, tmp_dir_str)
        expected_path = os.path.join(tmp_dir_str, '0.csv')
        self.assertTrue(os.path.exists(expected_path))
        csv_out = pd.read_csv(expected_path).to_dict()
        self.assertEqual(csv_out, {'0': {0: 'a', 1: 'b'}, '1': {0: '1.log', 1: '2.log'}})

def _get_method_text(spec: MethodSpecification) -> str:
    """
    Gets the text of a method to use for unit testing.
    This method does nothing and raises a `NotImplementedError()` if it is called.
    :param spec: The method specification.
    """
    input_signature_items = [f'{kvp[0]}: {kvp[1]}' for kvp in spec.input_args.items()]
    if spec.kw_only_args is not None:
        input_signature_items.append('*')
        input_signature_items += [f'{kvp[0]}: {kvp[1]}' for kvp in spec.kw_only_args.items()]
    input_signature = ', '.join(input_signature_items)
    method_text = textwrap.dedent(f'\n        def {spec.name}({input_signature}) -> {spec.return_type}:\n            raise NotImplementedError()\n        ')
    return method_text

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

def implement_me_2(self, q: float) -> str:
    """
        Implemented. See interface.
        """
    return str(q)

class TestS3Utils(unittest.TestCase):
    """
    A class to test that the S3 utilities function properly.
    """

    def test_is_s3_path(self) -> None:
        """
        Tests that the is_s3_path method works properly.
        """
        self.assertTrue(is_s3_path(Path('s3://foo/bar/baz.txt')))
        self.assertFalse(is_s3_path(Path('/foo/bar/baz')))
        self.assertFalse(is_s3_path(Path('foo/bar/baz')))
        self.assertTrue(is_s3_path('s3://foo/bar/baz.txt'))
        self.assertFalse(is_s3_path('/foo/bar/baz'))
        self.assertFalse(is_s3_path('foo/bar/baz'))

    def test_split_s3_path(self) -> None:
        """
        Tests that the split_s3_path method works properly.
        """
        sample_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
        expected_bucket = 'test-bucket'
        expected_path = Path('foo/bar/baz.txt')
        actual_bucket, actual_path = split_s3_path(sample_s3_path)
        self.assertEqual(expected_bucket, actual_bucket)
        self.assertEqual(expected_path, actual_path)

    @mock_async_s3()
    def test_get_async_s3_session(self) -> None:
        """
        Tests that getting a session works correctly.
        """
        sess_1 = get_async_s3_session()
        sess_2 = get_async_s3_session()
        self.assertEqual(sess_1, sess_2)
        sess_3 = get_async_s3_session(force_new=True)
        sess_4 = get_async_s3_session()
        self.assertNotEqual(sess_2, sess_3)
        self.assertEqual(sess_3, sess_4)

    @mock_async_s3()
    def test_download_directory_from_s3(self) -> None:
        """
        Tests that the download_directory_from_s3 method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_upload_directory = Path('test_download_directory_from_s3')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_upload_directory, test_bucket_name))
        with tempfile.TemporaryDirectory() as temp_dir:
            expected_directory_path_and_contents = {os.path.join(temp_dir, path): contents for path, contents in expected_relative_path_and_contents.items()}
            download_directory_from_s3(temp_dir, test_upload_directory, test_bucket_name)
            all_files = glob.glob(f'{temp_dir}/**/*.txt', recursive=True)
            self.assertEqual(len(all_files), len(expected_directory_path_and_contents))
            for key in expected_directory_path_and_contents:
                self.assertTrue(os.path.exists(key))
                with open(key, 'r') as f:
                    actual_text = f.read().strip()
                self.assertEqual(expected_directory_path_and_contents[key], actual_text)

    @mock_async_s3()
    def test_list_files_in_s3_directory(self) -> None:
        """
        Tests that the list_files_in_s3_directory method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_files_directory = Path('test_list_files_in_s3_directory')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        expected_files = {test_files_directory / path for path in expected_relative_path_and_contents}
        actual_files = list_files_in_s3_directory(test_files_directory, test_bucket_name)
        self.assertEqual(len(expected_files), len(actual_files))
        for file_path in actual_files:
            self.assertTrue(file_path in expected_files)

    @mock_async_s3()
    def test_check_s3_exist_ops(self) -> None:
        """
        Tests that the check_s3_object_exists and check_s3_path_exists methods functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """

        def to_s3_path(key: Path, bucket: str) -> str:
            """
            Returns s3 path string from split path.
            :param key: s3 key.
            :param bucket: s3 bucket.
            :return: Unsplit s3 path.
            """
            return f's3://{bucket}/{key}'
        test_files_directory = Path('test_check_s3_object_exists')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'existing.txt': 'this exists.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        existing_key = test_files_directory / 'existing.txt'
        non_existing_key = test_files_directory / 'does_not_exist.txt'
        self.assertTrue(check_s3_object_exists(existing_key, test_bucket_name))
        self.assertTrue(check_s3_path_exists(to_s3_path(existing_key, test_bucket_name)))
        self.assertFalse(check_s3_object_exists(non_existing_key, test_bucket_name))
        self.assertFalse(check_s3_path_exists(to_s3_path(non_existing_key, test_bucket_name)))
        self.assertFalse(check_s3_object_exists(test_files_directory, test_bucket_name))
        self.assertTrue(check_s3_path_exists(to_s3_path(test_files_directory, test_bucket_name)))

    @mock_async_s3()
    def test_get_cache_metadata_paths(self) -> None:
        """
        Tests that the get_cache_metadata_paths method functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
        test_files_directory = Path('test_get_cache_metadata_paths')
        test_bucket_name = 'test-bucket'
        expected_relative_path_and_contents = {'file1.csv': 'this is file1.', 'metadata/file2.csv': 'this is file2.', 'metadata/file3.csv': 'this is file3.'}
        asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
        expected_metadata_files = [test_files_directory / 'metadata/file2.csv', test_files_directory / 'metadata/file3.csv']
        actual_metadata_files = get_cache_metadata_paths(test_files_directory, test_bucket_name)
        self.assertEqual(len(expected_metadata_files), len(actual_metadata_files))
        for s3_path in actual_metadata_files:
            bucket, file_path = split_s3_path(s3_path)
            self.assertTrue(file_path in expected_metadata_files)
        non_existing_files = get_cache_metadata_paths(test_files_directory, test_bucket_name, metadata_folder='non_existing')
        self.assertEqual(len(non_existing_files), 0)

    @mock_async_s3()
    def test_s3_single_file_ops(self) -> None:
        """
        Tests that the following methods work properly while mocking AWS:
        * Upload file to S3
        * Download file from S3
        * Read file from S3
        * Delete file from S3
        """
        upload_bucket_name = 'test-bucket'
        asyncio.run(create_mock_bucket(upload_bucket_name))
        test_id = str(uuid.uuid4())
        upload_bucket_folder = Path('test_upload_file_to_s3')
        upload_bucket_path = upload_bucket_folder / f'{test_id}.txt'
        expected_file_contents = f'A random identifier: {test_id}.'
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_file_path = Path(os.path.join(temp_dir, 'upload.txt'))
            with open(upload_file_path, 'w') as f:
                f.write(expected_file_contents)
            upload_file_to_s3(upload_file_path, upload_bucket_path, upload_bucket_name)
            self.assertEqual(1, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))
            read_file_contents = read_text_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(expected_file_contents, read_file_contents)
            read_binary_contents = read_binary_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(expected_file_contents, read_binary_contents.decode('utf-8'))
            download_file_path = Path(os.path.join(temp_dir, 'download.txt'))
            download_file_from_s3(download_file_path, upload_bucket_path, upload_bucket_name)
            self.assertTrue(os.path.exists(download_file_path))
            with open(download_file_path, 'r') as f:
                downloaded_text = f.read()
            self.assertEqual(expected_file_contents, downloaded_text)
            delete_file_from_s3(upload_bucket_path, upload_bucket_name)
            self.assertEqual(0, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))

def test_split_s3_path(self) -> None:
    """
        Tests that the split_s3_path method works properly.
        """
    sample_s3_path = Path('s3://test-bucket/foo/bar/baz.txt')
    expected_bucket = 'test-bucket'
    expected_path = Path('foo/bar/baz.txt')
    actual_bucket, actual_path = split_s3_path(sample_s3_path)
    self.assertEqual(expected_bucket, actual_bucket)
    self.assertEqual(expected_path, actual_path)

@mock_async_s3()
def test_get_async_s3_session(self) -> None:
    """
        Tests that getting a session works correctly.
        """
    sess_1 = get_async_s3_session()
    sess_2 = get_async_s3_session()
    self.assertEqual(sess_1, sess_2)
    sess_3 = get_async_s3_session(force_new=True)
    sess_4 = get_async_s3_session()
    self.assertNotEqual(sess_2, sess_3)
    self.assertEqual(sess_3, sess_4)

@mock_async_s3()
def test_download_directory_from_s3(self) -> None:
    """
        Tests that the download_directory_from_s3 method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
    test_upload_directory = Path('test_download_directory_from_s3')
    test_bucket_name = 'test-bucket'
    expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
    asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_upload_directory, test_bucket_name))
    with tempfile.TemporaryDirectory() as temp_dir:
        expected_directory_path_and_contents = {os.path.join(temp_dir, path): contents for path, contents in expected_relative_path_and_contents.items()}
        download_directory_from_s3(temp_dir, test_upload_directory, test_bucket_name)
        all_files = glob.glob(f'{temp_dir}/**/*.txt', recursive=True)
        self.assertEqual(len(all_files), len(expected_directory_path_and_contents))
        for key in expected_directory_path_and_contents:
            self.assertTrue(os.path.exists(key))
            with open(key, 'r') as f:
                actual_text = f.read().strip()
            self.assertEqual(expected_directory_path_and_contents[key], actual_text)

@mock_async_s3()
def test_list_files_in_s3_directory(self) -> None:
    """
        Tests that the list_files_in_s3_directory method works properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
    test_files_directory = Path('test_list_files_in_s3_directory')
    test_bucket_name = 'test-bucket'
    expected_relative_path_and_contents = {'file1.txt': 'this is file1.', 'dir1/file2.txt': 'this is file2.', 'dir1/file3.txt': 'this is file3.'}
    asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
    expected_files = {test_files_directory / path for path in expected_relative_path_and_contents}
    actual_files = list_files_in_s3_directory(test_files_directory, test_bucket_name)
    self.assertEqual(len(expected_files), len(actual_files))
    for file_path in actual_files:
        self.assertTrue(file_path in expected_files)

@mock_async_s3()
def test_check_s3_exist_ops(self) -> None:
    """
        Tests that the check_s3_object_exists and check_s3_path_exists methods functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """

    def to_s3_path(key: Path, bucket: str) -> str:
        """
            Returns s3 path string from split path.
            :param key: s3 key.
            :param bucket: s3 bucket.
            :return: Unsplit s3 path.
            """
        return f's3://{bucket}/{key}'
    test_files_directory = Path('test_check_s3_object_exists')
    test_bucket_name = 'test-bucket'
    expected_relative_path_and_contents = {'existing.txt': 'this exists.'}
    asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
    existing_key = test_files_directory / 'existing.txt'
    non_existing_key = test_files_directory / 'does_not_exist.txt'
    self.assertTrue(check_s3_object_exists(existing_key, test_bucket_name))
    self.assertTrue(check_s3_path_exists(to_s3_path(existing_key, test_bucket_name)))
    self.assertFalse(check_s3_object_exists(non_existing_key, test_bucket_name))
    self.assertFalse(check_s3_path_exists(to_s3_path(non_existing_key, test_bucket_name)))
    self.assertFalse(check_s3_object_exists(test_files_directory, test_bucket_name))
    self.assertTrue(check_s3_path_exists(to_s3_path(test_files_directory, test_bucket_name)))

@mock_async_s3()
def test_get_cache_metadata_paths(self) -> None:
    """
        Tests that the get_cache_metadata_paths method functions properly while mocking AWS.
        Assumes that upload_file_to_s3_async works (used to setup test directory in mock bucket).
        """
    test_files_directory = Path('test_get_cache_metadata_paths')
    test_bucket_name = 'test-bucket'
    expected_relative_path_and_contents = {'file1.csv': 'this is file1.', 'metadata/file2.csv': 'this is file2.', 'metadata/file3.csv': 'this is file3.'}
    asyncio.run(setup_mock_s3_directory(expected_relative_path_and_contents, test_files_directory, test_bucket_name))
    expected_metadata_files = [test_files_directory / 'metadata/file2.csv', test_files_directory / 'metadata/file3.csv']
    actual_metadata_files = get_cache_metadata_paths(test_files_directory, test_bucket_name)
    self.assertEqual(len(expected_metadata_files), len(actual_metadata_files))
    for s3_path in actual_metadata_files:
        bucket, file_path = split_s3_path(s3_path)
        self.assertTrue(file_path in expected_metadata_files)
    non_existing_files = get_cache_metadata_paths(test_files_directory, test_bucket_name, metadata_folder='non_existing')
    self.assertEqual(len(non_existing_files), 0)

@mock_async_s3()
def test_s3_single_file_ops(self) -> None:
    """
        Tests that the following methods work properly while mocking AWS:
        * Upload file to S3
        * Download file from S3
        * Read file from S3
        * Delete file from S3
        """
    upload_bucket_name = 'test-bucket'
    asyncio.run(create_mock_bucket(upload_bucket_name))
    test_id = str(uuid.uuid4())
    upload_bucket_folder = Path('test_upload_file_to_s3')
    upload_bucket_path = upload_bucket_folder / f'{test_id}.txt'
    expected_file_contents = f'A random identifier: {test_id}.'
    with tempfile.TemporaryDirectory() as temp_dir:
        upload_file_path = Path(os.path.join(temp_dir, 'upload.txt'))
        with open(upload_file_path, 'w') as f:
            f.write(expected_file_contents)
        upload_file_to_s3(upload_file_path, upload_bucket_path, upload_bucket_name)
        self.assertEqual(1, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))
        read_file_contents = read_text_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
        self.assertEqual(expected_file_contents, read_file_contents)
        read_binary_contents = read_binary_file_contents_from_s3(upload_bucket_path, upload_bucket_name)
        self.assertEqual(expected_file_contents, read_binary_contents.decode('utf-8'))
        download_file_path = Path(os.path.join(temp_dir, 'download.txt'))
        download_file_from_s3(download_file_path, upload_bucket_path, upload_bucket_name)
        self.assertTrue(os.path.exists(download_file_path))
        with open(download_file_path, 'r') as f:
            downloaded_text = f.read()
        self.assertEqual(expected_file_contents, downloaded_text)
        delete_file_from_s3(upload_bucket_path, upload_bucket_name)
        self.assertEqual(0, len(list_files_in_s3_directory(upload_bucket_path, upload_bucket_name)))

def _assert_derived_is_child_of_base(interface_class_type: Type[Any], derived_class_type: Type[Any]) -> None:
    """
    Checks that derived is an instance of base.
    Throws a TypeError if it is not.
    :param interface_class: The interface class.
    :param derived_class: The derived class.
    """
    if not issubclass(derived_class_type, interface_class_type):
        raise TypeError(textwrap.dedent(f'\n            {derived_class_type} is not a subclass of {interface_class_type}.\n            '))

def _assert_abstract_methods_present(interface_class_type: Type[Any], derived_class_type: Type[Any], interface_abstract_method_names: Set[str], derived_public_method_names: Set[str]) -> None:
    """
    Asserts that all public methods in interface are in derived.
    :param interface_class_type: The class type of interface.
    :param derived_class_type: The class type of derived.
    :param interface_abstract_method_names: The interface abstract method names.
    :param derived_public_method_names: The derived public method names.
    """
    missing_methods = [im for im in interface_abstract_method_names if im not in derived_public_method_names]
    if len(missing_methods) > 0:
        missing_method_names = ', '.join(missing_methods)
        raise TypeError(textwrap.dedent(f'\n            The following methods are missing in {derived_class_type}, which are abstract in {interface_class_type}: {missing_method_names}\n            '))

def _assert_function_signature_types_match(first_func: Callable[..., Any], second_func: Callable[..., Any]) -> None:
    """
    Checks that the types in two method's function signatures match.
    If a difference is found, a TypeError is raised.
    :param first_func: The first function that is being seconded.
    :param second_func: The second that is being used.
    """
    first_annotations = first_func.__annotations__
    second_annotations = second_func.__annotations__
    if first_annotations != second_annotations:
        first_annotations_values = list(first_annotations.items()) if first_annotations is not None else []
        second_annotations_values = list(second_annotations.items()) if second_annotations is not None else []
        first_annotations_str = ', '.join([f'{kvp[0]}: {kvp[1]}' for kvp in first_annotations_values])
        second_annotations_str = ', '.join([f'{kvp[0]}: {kvp[1]}' for kvp in second_annotations_values])
        raise TypeError(textwrap.dedent(f'\n                Types in function signature for {first_func} do not match.\n                First func: {first_annotations_str}\n                Second func: {second_annotations_str}\n            '))

def _assert_function_defaults_match(first_func: Callable[..., Any], second_func: Callable[..., Any]) -> None:
    """
    Checks that the defaults set for the functions match.
    If a difference is found, a TypeError is raised.
    :param first_func: The first function that is being seconded.
    :param second_func: The second that is being used.
    """
    first_defaults = first_func.__defaults__
    second_defaults = second_func.__defaults__
    if first_defaults != second_defaults:
        raise TypeError(textwrap.dedent(f'\n                Default values for function {first_func} do not match.\n                First func: {first_defaults}\n                Second func: {second_defaults}\n            '))

def _assert_function_kwdefaults_match(first_func: Callable[..., Any], second_func: Callable[..., Any]) -> None:
    """
    Checks that the kwdefaults set for the functions match.
    If a difference is found, a TypeError is raised.
    :param first_func: The first function that is being seconded.
    :param second_func: The second that is being used.
    """
    first_kwdefaults = first_func.__kwdefaults__
    second_kwdefaults = second_func.__kwdefaults__
    if first_kwdefaults != second_kwdefaults:
        first_kwdefault_values = list(first_kwdefaults.items()) if first_kwdefaults is not None else []
        second_kwdefault_values = list(second_kwdefaults.items()) if second_kwdefaults is not None else []
        first_kwdefault_str = ', '.join([f'{kvp[0]}: {kvp[1]}' for kvp in first_kwdefault_values])
        second_kwdefault_str = ', '.join([f'{kvp[0]}: {kvp[1]}' for kvp in second_kwdefault_values])
        raise TypeError(textwrap.dedent(f'\n                Kwdefaults values in function signature for {first_func} do not match.\n                First func: {first_kwdefault_str}\n                Second func: {second_kwdefault_str}\n            '))

class MockHttpClientResponse(ClientResponse):
    """
    Mock Http Client response to make aioboto work with moto.
    """

    def __init__(self, response: AWSResponse):
        """
        Wraps moto's mocked client response for use with aioboto.
        :param response: Mocked AWS response.
        """
        read_index = 0

        async def read(n: int=-1) -> bytes:
            """
            Read handler for response contents.
            :param n: Number of bytes to read.
            :return: Bytes read from response content.
            """
            nonlocal read_index
            nonlocal response
            read_response: bytes = response.content[read_index:read_index + n]
            read_index += n
            return read_response
        self.content = MagicMock(aiohttp.StreamReader)
        self.content.read = read
        self.response = response

    @property
    def raw_headers(self) -> RawHeaders:
        """
        Return the headers encoded the way that aioboto expects them.
        :return: Raw response headers.
        """
        return {k.encode('utf-8'): str(v).encode('utf-8') for k, v in self.response.headers.items()}.items()

@property
def raw_headers(self) -> RawHeaders:
    """
        Return the headers encoded the way that aioboto expects them.
        :return: Raw response headers.
        """
    return {k.encode('utf-8'): str(v).encode('utf-8') for k, v in self.response.headers.items()}.items()

def set_mock_object_from_aws(s3_key: Path, s3_bucket: str) -> None:
    """
    Retrieve an object from real S3 and upload it to mock S3.
    :param s3_key: The S3 key to retrieve and store.
    :param s3_bucket: The S3 bucket to retrieve from and store to. Created if it doesn't exist.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        dump_file = Path(tmp_dir) / f'{str(uuid.uuid4())}.dat'
        download_file_from_s3(dump_file, s3_key, s3_bucket)
        with mock_async_s3():
            _ = get_async_s3_session(force_new=True)
            asyncio.run(create_mock_bucket(s3_bucket))
            upload_file_to_s3(dump_file, s3_key, s3_bucket)

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

class AbstractMapObject(abc.ABC):
    """
    Base interface representation of all map objects.
    """

    def __init__(self, object_id: str):
        """
        Constructor of the base lane type.
        :param object_id: unique identifier of the map object.
        """
        self.id = str(object_id)

def __init__(self, object_id: str):
    """
        Constructor of the base lane type.
        :param object_id: unique identifier of the map object.
        """
    self.id = str(object_id)

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
def incoming_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
    """Inherited from superclass."""
    incoming_roadblock_id = self._roadblock_connector['from_lane_group_fid']
    return [roadblock.NuPlanRoadBlock(str(incoming_roadblock_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data)]

@cached_property
def outgoing_edges(self) -> List[RoadBlockGraphEdgeMapObject]:
    """Inherited from superclass."""
    outgoing_roadblock_id = self._roadblock_connector['to_lane_group_fid']
    return [roadblock.NuPlanRoadBlock(str(outgoing_roadblock_id), self._lanes_df, self._lane_connectors_df, self._baseline_paths_df, self._boundaries_df, self._roadblocks_df, self._roadblock_connectors_df, self._stop_lines_df, self._intersections_df, self._lane_connector_polygon_df, self._map_data)]

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

def __repr__(self) -> str:
    """
        :return: A string describing the object.
        """
    return self.__class__.__qualname__ + '(' + ', '.join([f'{f}={v}' for f, v in self.__dict__.items()]) + ')'

@dataclass(frozen=True)
class Task:
    """This class represents a task that can be submitted to a worker with specific resource requirements."""
    fn: Callable[..., Any]
    num_cpus: Optional[int] = None
    num_gpus: Optional[Union[int, float]] = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Call function with args.
        :return: output from fn.
        """
        return self.fn(*args, **kwargs)

def __call__(self, *args: Any, **kwargs: Any) -> Any:
    """
        Call function with args.
        :return: output from fn.
        """
    return self.fn(*args, **kwargs)

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

def intersects(self, geometry: Geometry) -> OccupancyMap:
    """Inherited, see superclass."""
    candidate_df = {'geometry': [geometry]}
    return GeoPandasOccupancyMap(gp.sjoin(self._dataframe, gp.GeoDataFrame(candidate_df), how='inner', predicate='intersects'))

def insert(self, geometry_id: str, geometry: Geometry) -> None:
    """Inherited, see superclass."""
    candidate_df = {'geometry': [geometry]}
    self._dataframe = pandas.concat([self._dataframe, gp.GeoDataFrame(candidate_df, index=[geometry_id])])

class GeoPandasOccupancyMapFactory:
    """Factory for constructing GeoPandasOccupancyMaps."""

    @staticmethod
    def get_from_geometry(geometries: List[Union[Polygon, LineString]], geometry_ids: Optional[List[str]]=None) -> OccupancyMap:
        """
        Converts a list of shapely.geometry.Polygon to a GeopandaDataFrame. The data frame will have the format
           index           geometry
        0  token1          [Polygon, LineString]
        1  token2          [Polygon, LineString]
        :param geometries: list of [Polygon, LineString]
        :param geometry_ids: list of corresponding ids
        :return: gp.GeoDataFrame
        """
        if geometry_ids is None:
            geometry_ids = [str(idx) for idx in range(len(geometries))]
        return GeoPandasOccupancyMap(gp.GeoDataFrame([[poly] for poly in geometries], columns=['geometry'], geometry='geometry', index=geometry_ids))

@staticmethod
def get_from_geometry(geometries: List[Union[Polygon, LineString]], geometry_ids: Optional[List[str]]=None) -> OccupancyMap:
    """
        Converts a list of shapely.geometry.Polygon to a GeopandaDataFrame. The data frame will have the format
           index           geometry
        0  token1          [Polygon, LineString]
        1  token2          [Polygon, LineString]
        :param geometries: list of [Polygon, LineString]
        :param geometry_ids: list of corresponding ids
        :return: gp.GeoDataFrame
        """
    if geometry_ids is None:
        geometry_ids = [str(idx) for idx in range(len(geometries))]
    return GeoPandasOccupancyMap(gp.GeoDataFrame([[poly] for poly in geometries], columns=['geometry'], geometry='geometry', index=geometry_ids))

def _generate_profile_from_initial_condition_and_derivatives(initial_condition: float, derivatives: DoubleMatrix, discretization_time: float) -> DoubleMatrix:
    """
    Returns the corresponding profile (i.e. trajectory) given an initial condition and derivatives at
    multiple timesteps by integration.
    :param initial_condition: The value of the variable at the initial timestep.
    :param derivatives: The trajectory of time derivatives of the variable at timesteps 0,..., N-1.
    :param discretization_time: [s] Time discretization used for integration.
    :return: The trajectory of the variable at timesteps 0,..., N.
    """
    assert discretization_time > 0.0, 'Discretization time must be positive.'
    profile = initial_condition + np.insert(np.cumsum(derivatives * discretization_time), 0, 0.0)
    return profile

class RemotePlanner(AbstractPlanner):
    """
    Remote planner delegates computation of trajectories to a docker container, with which communicates through
    grpc.
    """

    def __init__(self, submission_container_manager: Optional[SubmissionContainerManager]=None, submission_image: Optional[str]=None, container_name: Optional[str]=None, compute_trajectory_timeout: float=1) -> None:
        """
        Prepares the remote container for planning.
        :param submission_container_manager: Optional manager, if provided a container will be started by RemotePlanner
        :param submission_image: Docker image name for the submission_container_factory
        :param container_name: Name to assign to the submission container
        :param compute_trajectory_timeout: Timeout for computation of trajectory.
        """
        if submission_container_manager:
            missing_parameter_message = 'Parameters for SubmissionContainer are missing!'
            assert submission_image, missing_parameter_message
            assert container_name, missing_parameter_message
            self.port = None
        else:
            self.port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
        self.submission_container_manager = submission_container_manager
        self.submission_image = submission_image
        self.container_name = container_name
        self._channel = None
        self._stub = None
        self.serialized_observation: Optional[List[bytes]] = None
        self.serialized_state: Optional[List[bytes]] = None
        self.sample_interval: Optional[float] = None
        self._compute_trajectory_timeout = compute_trajectory_timeout

    def __reduce__(self) -> Tuple[Type[RemotePlanner], Tuple[Optional[SubmissionContainerManager], Optional[str], Optional[str]]]:
        """
        :return: tuple of class and its constructor parameters, this is used to pickle the class
        """
        return (self.__class__, (self.submission_container_manager, self.submission_image, self.container_name))

    def name(self) -> str:
        """Inherited, see superclass."""
        return 'RemotePlanner'

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    @staticmethod
    def _planner_initializations_to_message(initialization: PlannerInitialization) -> chpb.PlannerInitializationLight:
        """
        Converts a PlannerInitialization to the message specified in the protocol files.
        :param initialization: The initialization parameters for the planner
        :return: A initialization message
        """
        try:
            mission_goal = proto_se2_from_se2(initialization.mission_goal)
        except AttributeError as e:
            logger.error('Mission goal was None!')
            raise e
        planner_initialization = chpb.PlannerInitializationLight(route_roadblock_ids=initialization.route_roadblock_ids, mission_goal=mission_goal, map_name=initialization.map_api.map_name)
        return planner_initialization

    def initialize(self, initialization: PlannerInitialization, timeout: float=5) -> None:
        """
        Creates the container manager, and runs the specified docker image. The communication port is created using
        the PID from the ray worker. Sends a request to initialize the remote planner.
        :param initialization: List of PlannerInitialization objects
        :param timeout: for planner initialization
        """
        if self.submission_container_manager:
            submission_container = try_n_times(self.submission_container_manager.get_submission_container, [self.submission_image, self.container_name, find_free_port_number()], {}, (docker.errors.APIError,), max_tries=10)
            self.port = submission_container.port
            submission_container.start()
            submission_container.wait_until_running(timeout=5)
        self._channel = grpc.insecure_channel(f'{NETWORK}:{self.port}')
        self._stub = chpb_grpc.DetectionTracksChallengeStub(self._channel)
        logger.info('Client sending planner initialization request...')
        planner_initializations_message = self._planner_initializations_to_message(initialization)
        logger.info(f'Trying to communicate on port {NETWORK}:{self.port}')
        try:
            _, _ = keep_trying(self._stub.InitializePlanner, [planner_initializations_message], {}, errors=(grpc.RpcError,), timeout=timeout)
        except Exception as e:
            submission_logger.error('Planner initialization failed!')
            submission_logger.error(e)
            raise e
        logger.info('Planner initialized!')

    def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Computes the ego vehicle trajectory.
        :param current_input: Planner input for which trajectory should be computed
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logger.debug('Client sending planner input: %s' % current_input)
        trajectory = self._compute_trajectory(self._stub, current_input=current_input)
        return trajectory

    def _compute_trajectory(self, stub: chpb_grpc.DetectionTracksChallengeStub, current_input: PlannerInput) -> AbstractTrajectory:
        """
        Sends a request to compute the trajectory given the PlannerInput to the remote planner.
        :param stub: Service interface
        :param current_input: Planner input for which a trajectory should be computed.
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
        logging.debug('Client sending observation...')
        self.serialized_state, self.serialized_observation, self.sample_interval = self._get_history_update(current_input)
        serialized_simulation_iteration = chpb.SimulationIteration(time_us=current_input.iteration.time_us, index=current_input.iteration.index)
        if self.sample_interval:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=self.sample_interval)
        else:
            serialized_buffer = chpb.SimulationHistoryBuffer(ego_states=self.serialized_state, observations=self.serialized_observation, sample_interval=None)
        tl_data = self._build_tl_message_from_planner_input(current_input)
        planner_input = chpb.PlannerInput(simulation_iteration=serialized_simulation_iteration, simulation_history_buffer=serialized_buffer, traffic_light_data=tl_data)
        try:
            trajectory_message = stub.ComputeTrajectory(planner_input, timeout=self._compute_trajectory_timeout)
        except grpc.RpcError as e:
            submission_logger.error('Trajectory computation service failed!')
            submission_logger.error(e)
            raise e
        return interp_traj_from_proto_traj(trajectory_message)

    def _get_history_update(self, planner_input: PlannerInput) -> Tuple[List[bytes], List[bytes], Optional[float]]:
        """
        Gets the new states and observations from the input. If no cache is present, the entire history is
        serialized, otherwise just the last element.
        :param planner_input: The input for planners
        :return: Tuple with new serialized state and observations.
        """
        keep_all_history = not self.serialized_state and (not self.serialized_observation)
        if keep_all_history:
            serialized_state = [pickle.dumps(state) for state in planner_input.history.ego_states]
            serialized_observation = [pickle.dumps(obs) for obs in planner_input.history.observations]
        else:
            last_ego_state, last_observations = planner_input.history.current_state
            serialized_state = [pickle.dumps(last_ego_state)]
            serialized_observation = [pickle.dumps(last_observations)]
        sample_interval = planner_input.history.sample_interval if not self.sample_interval else None
        return (serialized_state, serialized_observation, sample_interval)

    @staticmethod
    def _build_tl_message_from_planner_input(planner_input: PlannerInput) -> chpb.TrafficLightStatusData:
        tl_status_data: List[List[chpb.TrafficLightStatusData]]
        if planner_input.traffic_light_data is None:
            tl_status_data = [[]]
        else:
            tl_status_data = [proto_tl_status_data_from_tl_status_data(tl_status_data) for tl_status_data in planner_input.traffic_light_data]
        return tl_status_data

def __init__(self, submission_container_manager: Optional[SubmissionContainerManager]=None, submission_image: Optional[str]=None, container_name: Optional[str]=None, compute_trajectory_timeout: float=1) -> None:
    """
        Prepares the remote container for planning.
        :param submission_container_manager: Optional manager, if provided a container will be started by RemotePlanner
        :param submission_image: Docker image name for the submission_container_factory
        :param container_name: Name to assign to the submission container
        :param compute_trajectory_timeout: Timeout for computation of trajectory.
        """
    if submission_container_manager:
        missing_parameter_message = 'Parameters for SubmissionContainer are missing!'
        assert submission_image, missing_parameter_message
        assert container_name, missing_parameter_message
        self.port = None
    else:
        self.port = os.getenv('SUBMISSION_CONTAINER_PORT', 50051)
    self.submission_container_manager = submission_container_manager
    self.submission_image = submission_image
    self.container_name = container_name
    self._channel = None
    self._stub = None
    self.serialized_observation: Optional[List[bytes]] = None
    self.serialized_state: Optional[List[bytes]] = None
    self.sample_interval: Optional[float] = None
    self._compute_trajectory_timeout = compute_trajectory_timeout

def compute_planner_trajectory(self, current_input: PlannerInput) -> AbstractTrajectory:
    """
        Computes the ego vehicle trajectory.
        :param current_input: Planner input for which trajectory should be computed
        :return: Trajectory representing the predicted ego's position in future for every input iteration
        """
    logger.debug('Client sending planner input: %s' % current_input)
    trajectory = self._compute_trajectory(self._stub, current_input=current_input)
    return trajectory

def _get_history_update(self, planner_input: PlannerInput) -> Tuple[List[bytes], List[bytes], Optional[float]]:
    """
        Gets the new states and observations from the input. If no cache is present, the entire history is
        serialized, otherwise just the last element.
        :param planner_input: The input for planners
        :return: Tuple with new serialized state and observations.
        """
    keep_all_history = not self.serialized_state and (not self.serialized_observation)
    if keep_all_history:
        serialized_state = [pickle.dumps(state) for state in planner_input.history.ego_states]
        serialized_observation = [pickle.dumps(obs) for obs in planner_input.history.observations]
    else:
        last_ego_state, last_observations = planner_input.history.current_state
        serialized_state = [pickle.dumps(last_ego_state)]
        serialized_observation = [pickle.dumps(last_observations)]
    sample_interval = planner_input.history.sample_interval if not self.sample_interval else None
    return (serialized_state, serialized_observation, sample_interval)

class AbstractIDMPlanner(AbstractPlanner, ABC):
    """
    An interface for IDM based planners. Inherit from this class to use IDM policy to control the longitudinal
    behaviour of the ego.
    """

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
        self._policy = IDMPolicy(target_velocity, min_gap_to_lead_agent, headway_time, accel_max, decel_max)
        self._planned_trajectory_samples = planned_trajectory_samples
        self._planned_trajectory_sample_interval = planned_trajectory_sample_interval
        self._planned_horizon = planned_trajectory_samples * planned_trajectory_sample_interval
        self._occupancy_map_radius = occupancy_map_radius
        self._max_path_length = self._policy.target_velocity * self._planned_horizon
        self._ego_token = 'ego_token'
        self._red_light_token = 'red_light'
        self._route_roadblocks: List[RoadBlockGraphEdgeMapObject] = []
        self._candidate_lane_edge_ids: Optional[List[str]] = None
        self._map_api: Optional[AbstractMap] = None
        self._ego_path: Optional[AbstractPath] = None
        self._ego_path_linestring: Optional[LineString] = None

    def name(self) -> str:
        """Inherited, see superclass."""
        return self.__class__.__name__

    def observation_type(self) -> Type[Observation]:
        """Inherited, see superclass."""
        return DetectionsTracks

    def _initialize_route_plan(self, route_roadblock_ids: List[str]) -> None:
        """
        Initializes the route plan with roadblocks.
        :param route_roadblock_ids: A list of roadblock ids that make up the ego's route
        """
        assert self._map_api, '_map_api has not yet been initialized. Please call the initialize() function first!'
        self._route_roadblocks = []
        for id_ in route_roadblock_ids:
            block = self._map_api.get_map_object(id_, SemanticMapLayer.ROADBLOCK)
            block = block or self._map_api.get_map_object(id_, SemanticMapLayer.ROADBLOCK_CONNECTOR)
            self._route_roadblocks.append(block)
        self._candidate_lane_edge_ids = [edge.id for block in self._route_roadblocks if block for edge in block.interior_edges]
        assert self._route_roadblocks, 'Cannot create route plan. No roadblocks were extracted from the given route_roadblock_ids!'

    def _get_expanded_ego_path(self, ego_state: EgoState, ego_idm_state: IDMAgentState) -> Polygon:
        """
        Returns the ego's expanded path as a Polygon.
        :return: A polygon representing the ego's path.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        ego_footprint = ego_state.car_footprint
        path_to_go = trim_path(self._ego_path, max(self._ego_path.get_start_progress(), min(ego_idm_state.progress, self._ego_path.get_end_progress())), max(self._ego_path.get_start_progress(), min(ego_idm_state.progress + abs(self._policy.target_velocity) * self._planned_horizon, self._ego_path.get_end_progress())))
        expanded_path = path_to_linestring(path_to_go).buffer(ego_footprint.width / 2, cap_style=CAP_STYLE.square)
        return unary_union([expanded_path, ego_state.car_footprint.geometry])

    @staticmethod
    def _get_leading_idm_agent(ego_state: EgoState, agent: SceneObject, relative_distance: float) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state that represents another static and dynamic agent.
        :param agent: A scene object.
        :param relative_distance: [m] The relative distance from the scene object to the ego.
        :return: A IDM lead agents state
        """
        if isinstance(agent, Agent):
            longitudinal_velocity = agent.velocity.magnitude()
            relative_heading = principal_value(agent.center.heading - ego_state.center.heading)
            projected_velocity = transform(StateSE2(longitudinal_velocity, 0, 0), StateSE2(0, 0, relative_heading).as_matrix()).x
        else:
            projected_velocity = 0.0
        return IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=0.0)

    def _get_free_road_leading_idm_state(self, ego_state: EgoState, ego_idm_state: IDMAgentState) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state when there is no leading agent.
        :return: A IDM lead agents state.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        projected_velocity = 0.0
        relative_distance = self._ego_path.get_end_progress() - ego_idm_state.progress
        length_rear = ego_state.car_footprint.length / 2
        return IDMLeadAgentState(progress=relative_distance, velocity=projected_velocity, length_rear=length_rear)

    @staticmethod
    def _get_red_light_leading_idm_state(relative_distance: float) -> IDMLeadAgentState:
        """
        Returns a lead IDM agent state that represents a red light intersection.
        :param relative_distance: [m] The relative distance from the intersection to the ego.
        :return: A IDM lead agents state.
        """
        return IDMLeadAgentState(progress=relative_distance, velocity=0, length_rear=0)

    def _get_leading_object(self, ego_idm_state: IDMAgentState, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> IDMLeadAgentState:
        """
        Get the most suitable leading object based on the occupancy map.
        :param ego_idm_state: The ego's IDM state at current iteration.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        """
        intersecting_agents = occupancy_map.intersects(self._get_expanded_ego_path(ego_state, ego_idm_state))
        if intersecting_agents.size > 0:
            intersecting_agents.insert(self._ego_token, ego_state.car_footprint.geometry)
            nearest_id, nearest_agent_polygon, relative_distance = intersecting_agents.get_nearest_entry_to(self._ego_token)
            if self._red_light_token in nearest_id:
                return self._get_red_light_leading_idm_state(relative_distance)
            return self._get_leading_idm_agent(ego_state, unique_observations[nearest_id], relative_distance)
        else:
            return self._get_free_road_leading_idm_state(ego_state, ego_idm_state)

    def _construct_occupancy_map(self, ego_state: EgoState, observation: Observation) -> Tuple[OccupancyMap, UniqueObjects]:
        """
        Constructs an OccupancyMap from Observations.
        :param ego_state: Current EgoState
        :param observation: Observations of other agents and static objects in the scene.
        :return:
            - OccupancyMap.
            - A mapping between the object token and the object itself.
        """
        if isinstance(observation, DetectionsTracks):
            unique_observations = {detection.track_token: detection for detection in observation.tracked_objects.tracked_objects if np.linalg.norm(ego_state.center.array - detection.center.array) < self._occupancy_map_radius}
            return (STRTreeOccupancyMapFactory.get_from_boxes(list(unique_observations.values())), unique_observations)
        else:
            raise ValueError(f'IDM planner only supports DetectionsTracks. Got {observation.detection_type()}')

    def _propagate(self, ego: IDMAgentState, lead_agent: IDMLeadAgentState, tspan: float) -> None:
        """
        Propagate agent forward according to the IDM policy.
        :param ego: The ego's IDM state.
        :param lead_agent: The agent leading this agent.
        :param tspan: [s] The interval of time to propagate for.
        """
        solution = self._policy.solve_forward_euler_idm_policy(IDMAgentState(0, ego.velocity), lead_agent, tspan)
        ego.progress += solution.progress
        ego.velocity = max(solution.velocity, 0)

    def _get_planned_trajectory(self, ego_state: EgoState, occupancy_map: OccupancyMap, unique_observations: UniqueObjects) -> InterpolatedTrajectory:
        """
        Plan a trajectory w.r.t. the occupancy map.
        :param ego_state: EgoState at current iteration.
        :param occupancy_map: OccupancyMap containing all objects in the scene.
        :param unique_observations: A mapping between the object token and the object itself.
        :return: A trajectory representing the predicted ego's position in future.
        """
        assert self._ego_path_linestring, '_ego_path_linestring has not yet been initialized. Please call the initialize() function first!'
        ego_progress = self._ego_path_linestring.project(Point(*ego_state.center.point.array))
        ego_idm_state = IDMAgentState(progress=ego_progress, velocity=ego_state.dynamic_car_state.center_velocity_2d.x)
        vehicle_parameters = ego_state.car_footprint.vehicle_parameters
        current_time_point = ego_state.time_point
        projected_ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
        planned_trajectory: List[EgoState] = [projected_ego_state]
        for _ in range(self._planned_trajectory_samples):
            leading_agent = self._get_leading_object(ego_idm_state, ego_state, occupancy_map, unique_observations)
            self._propagate(ego_idm_state, leading_agent, self._planned_trajectory_sample_interval)
            current_time_point += TimePoint(int(self._planned_trajectory_sample_interval * 1000000.0))
            ego_state = self._idm_state_to_ego_state(ego_idm_state, current_time_point, vehicle_parameters)
            planned_trajectory.append(ego_state)
        return InterpolatedTrajectory(planned_trajectory)

    def _idm_state_to_ego_state(self, idm_state: IDMAgentState, time_point: TimePoint, vehicle_parameters: VehicleParameters) -> EgoState:
        """
        Convert IDMAgentState to EgoState
        :param idm_state: The IDMAgentState to be converted.
        :param time_point: The TimePoint corresponding to the state.
        :param vehicle_parameters: VehicleParameters of the ego.
        """
        assert self._ego_path, '_ego_path has not yet been initialized. Please call the initialize() function first!'
        new_ego_center = self._ego_path.get_state_at_progress(max(self._ego_path.get_start_progress(), min(idm_state.progress, self._ego_path.get_end_progress())))
        return EgoState.build_from_center(center=StateSE2(new_ego_center.x, new_ego_center.y, new_ego_center.heading), center_velocity_2d=StateVector2D(idm_state.velocity, 0), center_acceleration_2d=StateVector2D(0, 0), tire_steering_angle=0.0, time_point=time_point, vehicle_parameters=vehicle_parameters)

    def _annotate_occupancy_map(self, traffic_light_data: List[TrafficLightStatusData], occupancy_map: OccupancyMap) -> None:
        """
        Add red light lane connectors on the route plan to the occupancy map. Note: the function works inline, hence,
        the occupancy map will be modified in this function.
        :param traffic_light_data: A list of all available traffic status data.
        :param occupancy_map: The occupancy map to be annotated.
        """
        assert self._map_api, '_map_api has not yet been initialized. Please call the initialize() function first!'
        assert self._candidate_lane_edge_ids is not None, '_candidate_lane_edge_ids has not yet been initialized. Please call the initialize() function first!'
        for data in traffic_light_data:
            if data.status == TrafficLightStatusType.RED and str(data.lane_connector_id) in self._candidate_lane_edge_ids:
                id_ = str(data.lane_connector_id)
                lane_conn = self._map_api.get_map_object(id_, SemanticMapLayer.LANE_CONNECTOR)
                occupancy_map.insert(f'{self._red_light_token}_{id_}', lane_conn.polygon)

def _annotate_occupancy_map(self, traffic_light_data: List[TrafficLightStatusData], occupancy_map: OccupancyMap) -> None:
    """
        Add red light lane connectors on the route plan to the occupancy map. Note: the function works inline, hence,
        the occupancy map will be modified in this function.
        :param traffic_light_data: A list of all available traffic status data.
        :param occupancy_map: The occupancy map to be annotated.
        """
    assert self._map_api, '_map_api has not yet been initialized. Please call the initialize() function first!'
    assert self._candidate_lane_edge_ids is not None, '_candidate_lane_edge_ids has not yet been initialized. Please call the initialize() function first!'
    for data in traffic_light_data:
        if data.status == TrafficLightStatusType.RED and str(data.lane_connector_id) in self._candidate_lane_edge_ids:
            id_ = str(data.lane_connector_id)
            lane_conn = self._map_api.get_map_object(id_, SemanticMapLayer.LANE_CONNECTOR)
            occupancy_map.insert(f'{self._red_light_token}_{id_}', lane_conn.polygon)

def transform_predictions_to_states(predicted_poses: npt.NDArray[np.float32], ego_history: Deque[EgoState], future_horizon: float, step_interval: float, include_ego_state: bool=True) -> List[EgoState]:
    """
    Transform an array of pose predictions to a list of EgoState.

    :param predicted_poses: input relative poses
    :param ego_history: the history of the ego state, including the current
    :param future_horizon: [s] future time horizon
    :param step_interval: [s] interval between steps in the array
    :param include_ego_state: whether to include the current ego state as the initial state
    :return: transformed absolute states
    """
    ego_state = ego_history[-1]
    timesteps = _get_fixed_timesteps(ego_state, future_horizon, step_interval)
    states = _get_absolute_agent_states_from_numpy_poses(predicted_poses, ego_history, timesteps)
    if include_ego_state:
        states.insert(0, ego_state)
    return states

class CompletionCallback(AbstractMainCallback):
    """Callback that creates a token file to mark that the simulation instance finished the job."""

    def __init__(self, output_dir: str, challenge_name: str):
        """
        :param output_dir: Root dir used to find the report file and as path to save results.
        :param challenge_name: Name of the challenge being run.
        """
        self._bucket = os.getenv('NUPLAN_SERVER_S3_ROOT_URL')
        assert self._bucket, 'Target bucket must be specified!'
        instance_id = os.getenv('SCENARIO_FILTER_ID', '0')
        task_id = '_'.join([challenge_name, instance_id])
        self._completion_dir = Path(output_dir, 'simulation-results', task_id)

    def on_run_simulation_end(self) -> None:
        """
        On reached_end mark the task as completed by creating the relative file.
        """
        self._write_empty_file(self._completion_dir, 'completed.txt')

    @staticmethod
    def _write_empty_file(path: Path, filename: str) -> None:
        """
        Creates an empty file with the specified name at the given location.
        :param path: The location where to create the file.
        :param filename: The name of the file to be created.
        """
        if not is_s3_path(path):
            path.mkdir(parents=True, exist_ok=True)
        logger.info(f'Writing file {path / filename}')
        with (path / filename).open('w'):
            pass

def __init__(self, output_dir: str, challenge_name: str):
    """
        :param output_dir: Root dir used to find the report file and as path to save results.
        :param challenge_name: Name of the challenge being run.
        """
    self._bucket = os.getenv('NUPLAN_SERVER_S3_ROOT_URL')
    assert self._bucket, 'Target bucket must be specified!'
    instance_id = os.getenv('SCENARIO_FILTER_ID', '0')
    task_id = '_'.join([challenge_name, instance_id])
    self._completion_dir = Path(output_dir, 'simulation-results', task_id)

@staticmethod
def _write_empty_file(path: Path, filename: str) -> None:
    """
        Creates an empty file with the specified name at the given location.
        :param path: The location where to create the file.
        :param filename: The name of the file to be created.
        """
    if not is_s3_path(path):
        path.mkdir(parents=True, exist_ok=True)
    logger.info(f'Writing file {path / filename}')
    with (path / filename).open('w'):
        pass

class MetricFileCallback(AbstractMainCallback):
    """Callback to handle metric files at the end of process."""

    def __init__(self, metric_file_output_path: str, scenario_metric_paths: List[str], delete_scenario_metric_files: bool=False):
        """
        Constructor of MetricFileCallback.
        Output path can be local or s3.
        :param metric_file_output_path: Path to save integrated metric files.
        :param scenario_metric_paths: A list of paths with scenario metric files.
        :param delete_scenario_metric_files: Set True to delete scenario metric files.
        """
        self._metric_file_output_path = pathlib.Path(metric_file_output_path)
        if not is_s3_path(self._metric_file_output_path):
            self._metric_file_output_path.mkdir(exist_ok=True, parents=True)
        self._scenario_metric_paths = [pathlib.Path(scenario_metric_path) for scenario_metric_path in scenario_metric_paths]
        self._delete_scenario_metric_files = delete_scenario_metric_files

    def on_run_simulation_end(self) -> None:
        """Callback before end of the main function."""
        start_time = time.perf_counter()
        metrics = defaultdict(list)
        for scenario_metric_path in self._scenario_metric_paths:
            if not is_s3_path(scenario_metric_path) and (not path_exists(scenario_metric_path)):
                continue
            for scenario_metric_file in list_files_in_directory(scenario_metric_path):
                if not scenario_metric_file.name.endswith(JSON_FILE_EXTENSION):
                    continue
                json_dataframe = read_pickle(scenario_metric_file)
                for dataframe in json_dataframe:
                    pandas_dataframe = pandas.DataFrame(dataframe)
                    metrics[dataframe['metric_statistics_name']].append(pandas_dataframe)
                if self._delete_scenario_metric_files:
                    delete_file(scenario_metric_file)
        for metric_statistics_name, dataframe in metrics.items():
            save_path = self._metric_file_output_path / (metric_statistics_name + '.parquet')
            concat_pandas = pandas.concat([*dataframe], ignore_index=True)
            concat_pandas.to_parquet(safe_path_to_string(save_path))
        end_time = time.perf_counter()
        elapsed_time_s = end_time - start_time
        time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
        logger.info(f'Metric files integration: {time_str} [HH:MM:SS]')

def __init__(self, metric_file_output_path: str, scenario_metric_paths: List[str], delete_scenario_metric_files: bool=False):
    """
        Constructor of MetricFileCallback.
        Output path can be local or s3.
        :param metric_file_output_path: Path to save integrated metric files.
        :param scenario_metric_paths: A list of paths with scenario metric files.
        :param delete_scenario_metric_files: Set True to delete scenario metric files.
        """
    self._metric_file_output_path = pathlib.Path(metric_file_output_path)
    if not is_s3_path(self._metric_file_output_path):
        self._metric_file_output_path.mkdir(exist_ok=True, parents=True)
    self._scenario_metric_paths = [pathlib.Path(scenario_metric_path) for scenario_metric_path in scenario_metric_paths]
    self._delete_scenario_metric_files = delete_scenario_metric_files

def on_run_simulation_end(self) -> None:
    """Callback before end of the main function."""
    start_time = time.perf_counter()
    metrics = defaultdict(list)
    for scenario_metric_path in self._scenario_metric_paths:
        if not is_s3_path(scenario_metric_path) and (not path_exists(scenario_metric_path)):
            continue
        for scenario_metric_file in list_files_in_directory(scenario_metric_path):
            if not scenario_metric_file.name.endswith(JSON_FILE_EXTENSION):
                continue
            json_dataframe = read_pickle(scenario_metric_file)
            for dataframe in json_dataframe:
                pandas_dataframe = pandas.DataFrame(dataframe)
                metrics[dataframe['metric_statistics_name']].append(pandas_dataframe)
            if self._delete_scenario_metric_files:
                delete_file(scenario_metric_file)
    for metric_statistics_name, dataframe in metrics.items():
        save_path = self._metric_file_output_path / (metric_statistics_name + '.parquet')
        concat_pandas = pandas.concat([*dataframe], ignore_index=True)
        concat_pandas.to_parquet(safe_path_to_string(save_path))
    end_time = time.perf_counter()
    elapsed_time_s = end_time - start_time
    time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time_s))
    logger.info(f'Metric files integration: {time_str} [HH:MM:SS]')

def list_files(source_folder_path: pathlib.Path) -> List[str]:
    """
    List the files present in a directory, including subdirectories
    :param source_folder_path:  Root folder for resources you want to list.
    :return: A string containing relative names of the files.
    """
    paths = []
    if source_folder_path.is_file():
        logger.info('Provided path was a file, returning filename only.')
        return [source_folder_path.parts[-1]]
    for file_path in source_folder_path.rglob('*'):
        if file_path.is_dir():
            continue
        str_file_path = str(file_path)
        str_file_path = str_file_path.replace(f'{str(source_folder_path)}/', '')
        paths.append(str_file_path)
    return paths

class PublisherCallback(AbstractMainCallback):
    """Callback publishing data to S3"""

    def __init__(self, uploads: Dict[str, Any], s3_client: Optional[boto3.client], s3_bucket: str, remote_prefix: Optional[List[str]]):
        """
        Construct publisher callback, responsible to publish results of simulation, image validation and result aggregation
        :param uploads: dict containing information on which directories to publish
        """
        self._s3_client = s3_client
        if self._s3_client is None:
            self._s3_client = get_s3_client()
        self._s3_bucket = s3_bucket.strip('s3://') if s3_bucket.startswith('s3://') else s3_bucket
        self._remote_prefix: List[str] = remote_prefix or ['/']
        self._upload_targets: List[UploadConfig] = []
        for name, upload_data in uploads.items():
            if upload_data['upload']:
                save_path = pathlib.Path(upload_data['save_path'])
                remote_path = pathlib.Path(upload_data.get('remote_path') or '')
                self._upload_targets.append(UploadConfig(name=name, local_path=save_path, remote_path=pathlib.Path(*self._remote_prefix) / remote_path))

    def on_run_simulation_end(self) -> None:
        """
        On reached_end push results to S3 bucket.
        """
        logger.info('Publishing results on S3...')
        for upload_target in self._upload_targets:
            paths = list_files(upload_target.local_path)
            for path in paths:
                key = str(upload_target.remote_path / path)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'Pushing to S3 bucket: {self._s3_bucket}\n\t file: {str(upload_target.local_path.joinpath(path))}\n\t on destination: {key}')
                local_target = upload_target.local_path
                if not local_target.is_file():
                    local_target = local_target.joinpath(path)
                self._s3_client.upload_file(str(local_target), self._s3_bucket, key)
        logger.info('Publishing results on S3... DONE')

def __init__(self, uploads: Dict[str, Any], s3_client: Optional[boto3.client], s3_bucket: str, remote_prefix: Optional[List[str]]):
    """
        Construct publisher callback, responsible to publish results of simulation, image validation and result aggregation
        :param uploads: dict containing information on which directories to publish
        """
    self._s3_client = s3_client
    if self._s3_client is None:
        self._s3_client = get_s3_client()
    self._s3_bucket = s3_bucket.strip('s3://') if s3_bucket.startswith('s3://') else s3_bucket
    self._remote_prefix: List[str] = remote_prefix or ['/']
    self._upload_targets: List[UploadConfig] = []
    for name, upload_data in uploads.items():
        if upload_data['upload']:
            save_path = pathlib.Path(upload_data['save_path'])
            remote_path = pathlib.Path(upload_data.get('remote_path') or '')
            self._upload_targets.append(UploadConfig(name=name, local_path=save_path, remote_path=pathlib.Path(*self._remote_prefix) / remote_path))

def on_run_simulation_end(self) -> None:
    """
        On reached_end push results to S3 bucket.
        """
    logger.info('Publishing results on S3...')
    for upload_target in self._upload_targets:
        paths = list_files(upload_target.local_path)
        for path in paths:
            key = str(upload_target.remote_path / path)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'Pushing to S3 bucket: {self._s3_bucket}\n\t file: {str(upload_target.local_path.joinpath(path))}\n\t on destination: {key}')
            local_target = upload_target.local_path
            if not local_target.is_file():
                local_target = local_target.joinpath(path)
            self._s3_client.upload_file(str(local_target), self._s3_bucket, key)
    logger.info('Publishing results on S3... DONE')

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

def _validation_succeeded(source_folder_path: Path) -> bool:
    """
    Reads runners report and checks if the simulation was successful or not.
    :param source_folder_path:  Root folder to where runners report is stored.
    :return: True, if the simulation was successful, false otherwise.
    """
    try:
        df = pd.read_parquet(f'{source_folder_path}/runner_report.parquet')
    except FileNotFoundError:
        logger.warning('No runners report file found in %s!' % source_folder_path)
        return False
    return bool(np.all(df['succeeded'].values))

class ValidationCallback(AbstractMainCallback):
    """Callback checking if a validation simulation was successful or not."""

    def __init__(self, output_dir: str, validation_dir_name: str):
        """
        :param output_dir: Root dir used to find the report file and as path to save results.
        :param validation_dir_name: Name of the directory where the validation file should be stored.
        """
        self.output_dir = Path(output_dir)
        self._validation_dir_name = validation_dir_name

    def on_run_simulation_end(self) -> None:
        """
        On reached_end push results to S3 bucket.
        """
        if _validation_succeeded(self.output_dir):
            filename = 'passed.txt'
        else:
            filename = 'failed.txt'
        logger.info('Validation filename: %s' % filename)
        validation_dir = self.output_dir / self._validation_dir_name
        if not is_s3_path(validation_dir):
            validation_dir.mkdir(parents=True, exist_ok=True)
        with (validation_dir / filename).open('w'):
            pass

def __init__(self, output_dir: str, validation_dir_name: str):
    """
        :param output_dir: Root dir used to find the report file and as path to save results.
        :param validation_dir_name: Name of the directory where the validation file should be stored.
        """
    self.output_dir = Path(output_dir)
    self._validation_dir_name = validation_dir_name

def on_run_simulation_end(self) -> None:
    """
        On reached_end push results to S3 bucket.
        """
    if _validation_succeeded(self.output_dir):
        filename = 'passed.txt'
    else:
        filename = 'failed.txt'
    logger.info('Validation filename: %s' % filename)
    validation_dir = self.output_dir / self._validation_dir_name
    if not is_s3_path(validation_dir):
        validation_dir.mkdir(parents=True, exist_ok=True)
    with (validation_dir / filename).open('w'):
        pass

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

def __init__(self, metric_save_path: str, metric_aggregators: List[AbstractMetricAggregator]):
    """Callback to handle metric files at the end of process."""
    self._metric_save_path = Path(metric_save_path)
    self._metric_aggregators = metric_aggregators

class TestValidationCallback(unittest.TestCase):
    """Tests for the ValidationCallback class"""

    @patch.dict(os.environ, {'NUPLAN_SERVER_S3_ROOT_URL': 'my-bucket'})
    @patch.dict(os.environ, {'SCENARIO_FILTER_ID': '1'})
    def setUp(self) -> None:
        """Sets up callback for testing."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.callback = CompletionCallback(output_dir=self.tmp_dir.name, challenge_name='challenge')

    def test_initialization(self) -> None:
        """Tests initialization of callback."""
        self.assertEqual(str(self.callback._bucket), 'my-bucket')
        self.assertEqual(str(self.callback._completion_dir), '/'.join([self.tmp_dir.name, 'simulation-results/challenge_1']))

    @patch.dict(os.environ, {'NUPLAN_SERVER_S3_ROOT_URL': ''})
    def test_fail_on_missing_bucket(self) -> None:
        """Tests that initialization raises when missing the target bucket."""
        with self.assertRaises(AssertionError):
            _ = CompletionCallback(output_dir='out', challenge_name='challenge')

    def test_on_simulation_end_secondary_instance(self) -> None:
        """Tests that the correct files are created in the callback."""
        self.callback.on_run_simulation_end()
        self.assertTrue(os.path.exists(self.callback._completion_dir / 'completed.txt'))

def test_initialization(self) -> None:
    """Tests initialization of callback."""
    self.assertEqual(str(self.callback._bucket), 'my-bucket')
    self.assertEqual(str(self.callback._completion_dir), '/'.join([self.tmp_dir.name, 'simulation-results/challenge_1']))

def test_on_simulation_end_secondary_instance(self) -> None:
    """Tests that the correct files are created in the callback."""
    self.callback.on_run_simulation_end()
    self.assertTrue(os.path.exists(self.callback._completion_dir / 'completed.txt'))

class TestMetricFileCallback(TestCase):
    """Tests metrics files generation at the end fo the simulation."""

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        self.mock_metric_file_callback = Mock(spec=MetricFileCallback)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp_dir.name)
        self.path.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        """Clean up tmp dir."""
        self.tmp_dir.cleanup()

    def test_metric_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
        self.assertEqual(metric_file_callback._metric_file_output_path, self.path)
        self.assertEqual(metric_file_callback._scenario_metric_paths, [self.path])

    @patch('nuplan.planning.simulation.main_callback.metric_file_callback.logger')
    def test_on_run_simulation_end(self, logger: MagicMock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        metric_file_callback = MetricFileCallback(metric_file_output_path=self.tmp_dir.name, scenario_metric_paths=[self.tmp_dir.name])
        metric_file_callback.on_run_simulation_end()
        logger.info.assert_has_calls([call('Metric files integration: 00:00:00 [HH:MM:SS]')])

def setUp(self) -> None:
    """Setup mocks for the tests"""
    self.mock_metric_file_callback = Mock(spec=MetricFileCallback)
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.path = pathlib.Path(self.tmp_dir.name)
    self.path.mkdir(parents=True, exist_ok=True)

def tearDown(self) -> None:
    """Clean up tmp dir."""
    self.tmp_dir.cleanup()

class TestPublisherCallback(TestCase):
    """
    Tests PublisherCallback.
    """

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        fake_targets = {'metrics': {'upload': True, 'save_path': 'some/path/to/save', 'remote_path': 'path/save'}, 'pictures': {'upload': True, 'save_path': 'some/path/to/pictures', 'remote_path': 'path/pictures'}}
        self.fake_uploads = [UploadConfig('metrics', pathlib.Path('some/path/to/save'), pathlib.Path('user/image/path/save')), UploadConfig('pictures', pathlib.Path('some/path/to/pictures'), pathlib.Path('user/image/path/pictures'))]
        self.mock_client = Mock()
        self.publisher_callback = PublisherCallback(fake_targets, self.mock_client, 'bucket', ['user', 'image'])

    def test_publisher_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        self.assertEqual(self.fake_uploads, self.publisher_callback._upload_targets)

    @patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib')
    @patch('nuplan.planning.simulation.main_callback.publisher_callback.list_files')
    def test_on_run_simulation_end_push_to_s3(self, mock_files: Mock, mock_pathlib: Mock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        fake_path = Mock()
        fake_path.iterdir.return_value = [True]
        fake_path.__truediv__ = lambda name, x: f'bucket/{x}'
        mock_pathlib.Path.return_value = fake_path
        mock_files.return_value = ['a', 'b']
        self.publisher_callback.on_run_simulation_end()
        expected_calls = [call('some/path/to/save/a', 'bucket', 'user/image/path/save/a'), call('some/path/to/save/b', 'bucket', 'user/image/path/save/b'), call('some/path/to/pictures/a', 'bucket', 'user/image/path/pictures/a'), call('some/path/to/pictures/b', 'bucket', 'user/image/path/pictures/b')]
        self.mock_client.upload_file.assert_has_calls(expected_calls)

    @patch('nuplan.planning.simulation.main_callback.publisher_callback.pathlib', MagicMock())
    @patch('nuplan.planning.simulation.main_callback.publisher_callback.boto3')
    def test_no_push_without_results(self, mock_boto3: Mock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        empty_publisher_callback = PublisherCallback({}, self.mock_client, 'bucket', ['user', 'image'])
        empty_publisher_callback.on_run_simulation_end()
        mock_boto3.client.return_value.assert_not_called()

def setUp(self) -> None:
    """Setup mocks for the tests"""
    fake_targets = {'metrics': {'upload': True, 'save_path': 'some/path/to/save', 'remote_path': 'path/save'}, 'pictures': {'upload': True, 'save_path': 'some/path/to/pictures', 'remote_path': 'path/pictures'}}
    self.fake_uploads = [UploadConfig('metrics', pathlib.Path('some/path/to/save'), pathlib.Path('user/image/path/save')), UploadConfig('pictures', pathlib.Path('some/path/to/pictures'), pathlib.Path('user/image/path/pictures'))]
    self.mock_client = Mock()
    self.publisher_callback = PublisherCallback(fake_targets, self.mock_client, 'bucket', ['user', 'image'])

class TestMetricSummaryCallback(unittest.TestCase):
    """Test metric_summary callback functionality."""

    def set_up_dummy_metric(self, metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90)]
        time_stamps = [0, 1, 2]
        accel = [0.0, 1.0, 2.0]
        time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
        result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1)
        key = MetricFileKey(metric_name='ego_acceleration', scenario_name=scenario_name, log_name=log_name, scenario_type=scenario_type, planner_name=planner_name)
        metric_engine = MetricsEngine(main_save_path=metric_path)
        metric_files = {'ego_acceleration': [MetricFile(key=key, metric_statistics=[result])]}
        metric_engine.write_to_files(metric_files=metric_files)
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)], delete_scenario_metric_files=True)
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """Set up a nuboard base tab."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.tmp_dir.name) / 'metrics'
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        self.aggregator_save_path = Path(self.tmp_dir.name) / 'aggregator_metric'
        self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=self.aggregator_save_path, multiple_metrics=[])
        self.metric_statistics_dataframes = {}
        for metric_parquet_file in metric_path.iterdir():
            print(metric_parquet_file)
            data_frame = MetricStatisticsDataFrame.load_parquet(metric_parquet_file)
            self.metric_statistics_dataframes[data_frame.metric_statistic_name] = data_frame
        self.metric_summary_output_path = Path(self.tmp_dir.name) / 'summary'
        self.metric_summary_callback = MetricSummaryCallback(metric_save_path=str(metric_path), metric_aggregator_save_path=str(self.aggregator_save_path), summary_output_path=str(self.metric_summary_output_path), pdf_file_name='summary.pdf')

    def test_metric_summary_callback_on_simulation_end(self) -> None:
        """Test on_simulation_end in metric summary callback."""
        self.weighted_average_metric_aggregator(metric_dataframes=self.metric_statistics_dataframes)
        self.metric_summary_callback.on_run_simulation_end()
        pdf_files = self.metric_summary_output_path.rglob('*.pdf')
        self.assertEqual(len(list(pdf_files)), 1)

    def tearDown(self) -> None:
        """Remove all temporary folders and files."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a nuboard base tab."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    log_name = 'dummy_log'
    planner_name = 'SimplePlanner'
    scenario_type = 'Test'
    scenario_name = 'Dummy_scene'
    metric_path = Path(self.tmp_dir.name) / 'metrics'
    metric_path.mkdir(exist_ok=True, parents=True)
    self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
    self.aggregator_save_path = Path(self.tmp_dir.name) / 'aggregator_metric'
    self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=self.aggregator_save_path, multiple_metrics=[])
    self.metric_statistics_dataframes = {}
    for metric_parquet_file in metric_path.iterdir():
        print(metric_parquet_file)
        data_frame = MetricStatisticsDataFrame.load_parquet(metric_parquet_file)
        self.metric_statistics_dataframes[data_frame.metric_statistic_name] = data_frame
    self.metric_summary_output_path = Path(self.tmp_dir.name) / 'summary'
    self.metric_summary_callback = MetricSummaryCallback(metric_save_path=str(metric_path), metric_aggregator_save_path=str(self.aggregator_save_path), summary_output_path=str(self.metric_summary_output_path), pdf_file_name='summary.pdf')

def tearDown(self) -> None:
    """Remove all temporary folders and files."""
    self.tmp_dir.cleanup()

class TestMetricAggregatorCallback(TestCase):
    """Test MetricAggregatorCallback."""

    def setUp(self) -> None:
        """Setup mocks for the tests"""
        self.mock_metric_aggregator_callback = Mock(spec=MetricAggregatorCallback)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp_dir.name)
        self.path.mkdir(parents=True, exist_ok=True)
        self.metric_aggregators = [MockAbstractMetricAggregator(self.path)]

    def tearDown(self) -> None:
        """Clean up tmp dir."""
        self.tmp_dir.cleanup()

    def test_metric_callback_init(self) -> None:
        """
        Tests if all the properties are set to the expected values in constructor.
        """
        metric_aggregator_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
        self.assertEqual(metric_aggregator_callback._metric_save_path, self.path)
        self.assertEqual(metric_aggregator_callback._metric_aggregators, self.metric_aggregators)

    @patch('nuplan.planning.simulation.main_callback.metric_aggregator_callback.logger')
    def test_on_run_simulation_end(self, logger: MagicMock) -> None:
        """
        Tests if the callback is called with the correct parameters.
        """
        metric_file_callback = MetricAggregatorCallback(str(self.path), self.metric_aggregators)
        metric_file_callback.on_run_simulation_end()
        logger.warning.assert_has_calls([call('dummy_metric_aggregator: No metric files found for aggregation!')])
        logger.info.assert_has_calls([call('Metric aggregator: 00:00:00 [HH:MM:SS]')])

def setUp(self) -> None:
    """Setup mocks for the tests"""
    self.mock_metric_aggregator_callback = Mock(spec=MetricAggregatorCallback)
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.path = pathlib.Path(self.tmp_dir.name)
    self.path.mkdir(parents=True, exist_ok=True)
    self.metric_aggregators = [MockAbstractMetricAggregator(self.path)]

def tearDown(self) -> None:
    """Clean up tmp dir."""
    self.tmp_dir.cleanup()

def for_each(fn: Callable[[Any], Any], items: List[Any]) -> None:
    """
    Call function on every item in items
    :param fn: function to be called fn(item)
    :param items: list of items
    """
    for item in items:
        fn(item)

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

def tearDown(self) -> None:
    """Clean up folders."""
    self.tmp_dir.cleanup()

def _save_log_to_file(file_name: pathlib.Path, scenario: AbstractScenario, planner: AbstractPlanner, history: SimulationHistory) -> None:
    """
    Create SimulationLog and save it to disk.
    :param file_name: to write to.
    :param scenario: to store in the log.
    :param planner: to store in the log.
    :param history: to store in the log.
    """
    simulation_log = SimulationLog(file_path=file_name, scenario=scenario, planner=planner, simulation_history=history)
    simulation_log.save_to_file()

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

def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
    """
        Create directory at initialization
        :param setup: simulation setup
        :param planner: planner before initialization
        """
    scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
    if not is_s3_path(scenario_directory):
        scenario_directory.mkdir(exist_ok=True, parents=True)

def _dump_to_json(file: pathlib.Path, scene_to_save: Any) -> None:
    """Dump file into json"""
    scene_json = json.dumps(scene_to_save)
    save_text(file.with_suffix('.json'), scene_json)

def _dump_to_pickle(file: pathlib.Path, scene_to_save: Any) -> None:
    """Dump file into compressed pickle"""
    pickle_object = pickle.dumps(scene_to_save, protocol=pickle.HIGHEST_PROTOCOL)
    save_buffer(file.with_suffix('.pkl.xz'), lzma.compress(pickle_object, preset=0))

def _dump_to_msgpack(file: pathlib.Path, scene_to_save: Any) -> None:
    """Dump file into compressed msgpack"""
    msg_packed_bytes = msgpack.packb(scene_to_save)
    save_buffer(file.with_suffix('.msgpack.xz'), lzma.compress(msg_packed_bytes, preset=0))

class SerializationCallback(AbstractCallback):
    """Callback for serializing scenes at the end of the simulation."""

    def __init__(self, output_directory: Union[str, pathlib.Path], folder_name: Union[str, pathlib.Path], serialization_type: str, serialize_into_single_file: bool):
        """
        Construct serialization callback
        :param output_directory: where scenes should be serialized
        :param folder_name: folder where output should be serialized
        :param serialization_type: A way to serialize output, options: ["json", "pickle", "msgpack"]
        :param serialize_into_single_file: if true all data will be in single file, if false, each time step will
                be serialized into a separate file
        """
        available_formats = ['json', 'pickle', 'msgpack']
        if serialization_type not in available_formats:
            raise ValueError(f'The serialization callback will not store files anywhere!Choose at least one format from {available_formats} instead of {serialization_type}!')
        self._output_directory = pathlib.Path(output_directory) / folder_name
        self._serialization_type = serialization_type
        self._serialize_into_single_file = serialize_into_single_file

    def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
        """
        Create directory at initialization
        :param setup: simulation setup
        :param planner: planner before initialization
        """
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
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
        On reached_end validate that all steps were correctly serialized
        :param setup: simulation setup
        :param planner: planner when simulation ends
        :param history: resulting from simulation
        """
        number_of_scenes = len(history)
        if number_of_scenes == 0:
            raise RuntimeError('Number of scenes has to be greater than 0')
        scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
        scenario = setup.scenario
        expert_trajectory = list(scenario.get_expert_ego_trajectory())
        scenes = [convert_sample_to_scene(map_name=scenario.map_api.map_name, database_interval=scenario.database_interval, traffic_light_status=scenario.get_traffic_light_status_at_iteration(index), expert_trajectory=expert_trajectory, mission_goal=scenario.get_mission_goal(), data=sample, colors=TrajectoryColors()) for index, sample in enumerate(history.data)]
        self._serialize_scenes(scenes, scenario_directory)

    def _serialize_scenes(self, scenes: List[Dict[str, Any]], scenario_directory: pathlib.Path) -> None:
        """
        Serialize scenes based on callback setup to json/pickle or other
        :param scenes: scenes to be serialized
        :param scenario_directory: directory where they should be serialized
        """
        if not self._serialize_into_single_file:
            for scene in scenes:
                file_name = scenario_directory / str(scene['ego']['timestamp_us'])
                _dump_to_file(file_name, scene, self._serialization_type)
        else:
            file_name = scenario_directory / scenario_directory.name
            _dump_to_file(file_name, scenes, self._serialization_type)

    def _get_scenario_folder(self, planner_name: str, scenario: AbstractScenario) -> pathlib.Path:
        """
        Compute scenario folder directory where all files will be stored
        :param planner_name: planner name
        :param scenario: for which to compute directory name
        :return directory path
        """
        return self._output_directory / planner_name / scenario.scenario_type / scenario.log_name / scenario.scenario_name

def __init__(self, output_directory: Union[str, pathlib.Path], folder_name: Union[str, pathlib.Path], serialization_type: str, serialize_into_single_file: bool):
    """
        Construct serialization callback
        :param output_directory: where scenes should be serialized
        :param folder_name: folder where output should be serialized
        :param serialization_type: A way to serialize output, options: ["json", "pickle", "msgpack"]
        :param serialize_into_single_file: if true all data will be in single file, if false, each time step will
                be serialized into a separate file
        """
    available_formats = ['json', 'pickle', 'msgpack']
    if serialization_type not in available_formats:
        raise ValueError(f'The serialization callback will not store files anywhere!Choose at least one format from {available_formats} instead of {serialization_type}!')
    self._output_directory = pathlib.Path(output_directory) / folder_name
    self._serialization_type = serialization_type
    self._serialize_into_single_file = serialize_into_single_file

def on_initialization_start(self, setup: SimulationSetup, planner: AbstractPlanner) -> None:
    """
        Create directory at initialization
        :param setup: simulation setup
        :param planner: planner before initialization
        """
    scenario_directory = self._get_scenario_folder(planner.name(), setup.scenario)
    scenario_directory.mkdir(exist_ok=True, parents=True)

def _serialize_scenes(self, scenes: List[Dict[str, Any]], scenario_directory: pathlib.Path) -> None:
    """
        Serialize scenes based on callback setup to json/pickle or other
        :param scenes: scenes to be serialized
        :param scenario_directory: directory where they should be serialized
        """
    if not self._serialize_into_single_file:
        for scene in scenes:
            file_name = scenario_directory / str(scene['ego']['timestamp_us'])
            _dump_to_file(file_name, scene, self._serialization_type)
    else:
        file_name = scenario_directory / scenario_directory.name
        _dump_to_file(file_name, scenes, self._serialization_type)

def run_metric_engine(metric_engine: MetricsEngine, scenario: AbstractScenario, planner_name: str, history: SimulationHistory) -> None:
    """
    Run the metric engine.
    """
    logger.debug('Starting metrics computation...')
    metric_files = metric_engine.compute(history, scenario=scenario, planner_name=planner_name)
    logger.debug('Finished metrics computation!')
    logger.debug('Saving metric statistics!')
    metric_engine.write_to_files(metric_files)
    logger.debug('Saved metrics!')

class TestSimulationLog(unittest.TestCase):
    """Tests metrics callback."""

    def test_simulation_log_type(self) -> None:
        """Checks for the expected behavior of the simulation_log_type function."""
        for path in (Path('/foo.msgpack.xz'), Path('/foo/bar/baz/1.2.msgpack.xz'), Path('/foo/bar/baz.1.2.pickle.msgpack.xz'), Path('/data/exp/username/mmdbqsb_test/simulation_simple_experiment/open_loop_boxes/2022.12.14.13.48.22/simulation_log/SimplePlanner/unknown/2021.09.01.07.19.19_g1p-veh-2051/2021.09.01.07.19.19_g1p-veh-2051_0000074/2021.09.01.07.19.msgpack.xz')):
            self.assertEqual(SimulationLog.simulation_log_type(path), 'msgpack')
        for path in (Path('/foo.pkl.xz'), Path('/foo/bar/baz.1.2.pkl.xz'), Path('/foo/bar/baz.1.2.msgpack.pkl.xz'), Path('/data/exp/username/mmdbqsb_test/simulation_simple_experiment/open_loop_boxes/2022.12.14.13.48.22/simulation_log/SimplePlanner/unknown/2021.09.01.07.19.19_g1p-veh-2051/2021.09.01.07.19.19_g1p-veh-2051_0000074/2021.09.01.07.19.pkl.xz')):
            self.assertEqual(SimulationLog.simulation_log_type(path), 'pickle')
        for path in (Path('/foo'), Path('/foo.pkl'), Path('/foo.msgpack'), Path('/foo/bar/baz.1.2.pkl'), Path('/foo/bar/baz.1.2.msgpack'), Path('/foo/bar/baz.1.2.pkl.msgpack'), Path('/foo/bar/baz.1.2.xz'), Path('/foo/bar/baz.1.2.json.xz')):
            with self.assertRaises(ValueError):
                SimulationLog.simulation_log_type(path)

def test_simulation_log_type(self) -> None:
    """Checks for the expected behavior of the simulation_log_type function."""
    for path in (Path('/foo.msgpack.xz'), Path('/foo/bar/baz/1.2.msgpack.xz'), Path('/foo/bar/baz.1.2.pickle.msgpack.xz'), Path('/data/exp/username/mmdbqsb_test/simulation_simple_experiment/open_loop_boxes/2022.12.14.13.48.22/simulation_log/SimplePlanner/unknown/2021.09.01.07.19.19_g1p-veh-2051/2021.09.01.07.19.19_g1p-veh-2051_0000074/2021.09.01.07.19.msgpack.xz')):
        self.assertEqual(SimulationLog.simulation_log_type(path), 'msgpack')
    for path in (Path('/foo.pkl.xz'), Path('/foo/bar/baz.1.2.pkl.xz'), Path('/foo/bar/baz.1.2.msgpack.pkl.xz'), Path('/data/exp/username/mmdbqsb_test/simulation_simple_experiment/open_loop_boxes/2022.12.14.13.48.22/simulation_log/SimplePlanner/unknown/2021.09.01.07.19.19_g1p-veh-2051/2021.09.01.07.19.19_g1p-veh-2051_0000074/2021.09.01.07.19.pkl.xz')):
        self.assertEqual(SimulationLog.simulation_log_type(path), 'pickle')
    for path in (Path('/foo'), Path('/foo.pkl'), Path('/foo.msgpack'), Path('/foo/bar/baz.1.2.pkl'), Path('/foo/bar/baz.1.2.msgpack'), Path('/foo/bar/baz.1.2.pkl.msgpack'), Path('/foo/bar/baz.1.2.xz'), Path('/foo/bar/baz.1.2.json.xz')):
        with self.assertRaises(ValueError):
            SimulationLog.simulation_log_type(path)

class TestSimulationLogCallback(unittest.TestCase):
    """Tests simulation_log_callback."""

    def setUp(self) -> None:
        """Setup Mocked classes."""
        self.output_folder = tempfile.TemporaryDirectory()
        self.callback = SimulationLogCallback(output_directory=self.output_folder.name, simulation_log_dir='simulation_log', serialization_type='msgpack')
        self.sim_manager = Mock(spec=AbstractSimulationTimeController)
        self.observation = Mock(spec=AbstractObservation)
        self.controller = Mock(spec=AbstractEgoController)

    def tearDown(self) -> None:
        """Clean up folder."""
        self.output_folder.cleanup()

    def test_callback(self) -> None:
        """
        Tests whether a scene can be dumped into a simulation log, checks that the keys are correct,
        and checks that the log contains the expected data after being re-loaded from disk.
        """
        scenario = MockAbstractScenario()
        self.setup = SimulationSetup(observations=self.observation, scenario=scenario, time_controller=self.sim_manager, ego_controller=self.controller)
        planner = SimplePlanner(2, 0.5, [0, 0])
        directory = self.callback._get_scenario_folder(planner.name(), scenario)
        self.assertEqual(str(directory), self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name')
        self.callback.on_initialization_start(self.setup, planner)
        history = SimulationHistory(scenario.map_api, scenario.get_mission_goal())
        state_0 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(0))
        state_1 = EgoState.build_from_rear_axle(StateSE2(0, 0, 0), vehicle_parameters=scenario.ego_vehicle_parameters, rear_axle_velocity_2d=StateVector2D(x=0, y=0), rear_axle_acceleration_2d=StateVector2D(x=0, y=0), tire_steering_angle=0, time_point=TimePoint(1000))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_0, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
        history.add_sample(SimulationHistorySample(iteration=SimulationIteration(time_point=TimePoint(0), index=0), ego_state=state_1, trajectory=InterpolatedTrajectory(trajectory=[state_0, state_1]), observation=DetectionsTracks(TrackedObjects()), traffic_light_status=list(scenario.get_traffic_light_status_at_iteration(0))))
        for data in history.data:
            self.callback.on_step_end(self.setup, planner, data)
        self.callback.on_simulation_end(self.setup, planner, history)
        path = pathlib.Path(self.output_folder.name + '/simulation_log/SimplePlanner/mock_scenario_type/mock_log_name/mock_scenario_name/mock_scenario_name.msgpack.xz')
        self.assertTrue(path.exists())
        simulation_log = SimulationLog.load_data(file_path=path)
        self.assertEqual(simulation_log.file_path, path)
        self.assertTrue(objects_are_equal(simulation_log.simulation_history, history))

def setUp(self) -> None:
    """Setup Mocked classes."""
    self.output_folder = tempfile.TemporaryDirectory()
    self.callback = SimulationLogCallback(output_directory=self.output_folder.name, simulation_log_dir='simulation_log', serialization_type='msgpack')
    self.sim_manager = Mock(spec=AbstractSimulationTimeController)
    self.observation = Mock(spec=AbstractObservation)
    self.controller = Mock(spec=AbstractEgoController)

def tearDown(self) -> None:
    """Clean up folder."""
    self.output_folder.cleanup()

class TestUrbanDriverOpenLoop(unittest.TestCase):
    """Test UrbanDriverOpenLoopModel model."""

    def setUp(self) -> None:
        """Set up the test."""
        self.model_params = UrbanDriverOpenLoopModelParams(local_embedding_size=256, global_embedding_size=256, num_subgraph_layers=3, global_head_dropout=0.0)
        self.feature_params = UrbanDriverOpenLoopModelFeatureParams(feature_types={'NONE': -1, 'EGO': 0, 'VEHICLE': 1, 'BICYCLE': 2, 'PEDESTRIAN': 3, 'LANE': 4, 'STOP_LINE': 5, 'CROSSWALK': 6, 'LEFT_BOUNDARY': 7, 'RIGHT_BOUNDARY': 8, 'ROUTE_LANES': 9}, total_max_points=20, feature_dimension=8, agent_features=['VEHICLE', 'BICYCLE', 'PEDESTRIAN'], ego_dimension=3, agent_dimension=8, max_agents=30, past_trajectory_sampling=TrajectorySampling(time_horizon=2.0, num_poses=4), map_features=['LANE', 'LEFT_BOUNDARY', 'RIGHT_BOUNDARY', 'STOP_LINE', 'CROSSWALK', 'ROUTE_LANES'], max_elements={'LANE': 30, 'LEFT_BOUNDARY': 30, 'RIGHT_BOUNDARY': 30, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 30}, max_points={'LANE': 20, 'LEFT_BOUNDARY': 20, 'RIGHT_BOUNDARY': 20, 'STOP_LINE': 20, 'CROSSWALK': 20, 'ROUTE_LANES': 20}, vector_set_map_feature_radius=35, interpolation_method='linear', disable_map=False, disable_agents=False)
        self.target_params = UrbanDriverOpenLoopModelTargetParams(num_output_features=36, future_trajectory_sampling=TrajectorySampling(time_horizon=6.0, num_poses=12))

    def _build_model(self) -> UrbanDriverOpenLoopModel:
        """
        Creates a new instance of a UrbanDriverOpenLoop with some default parameters.
        """
        model = UrbanDriverOpenLoopModel(self.model_params, self.feature_params, self.target_params)
        return model

    def _build_input_features(self, device: torch.device, include_agents: bool) -> FeaturesType:
        """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :return: FeaturesType to be consumed by the model
        """
        num_frames = 5
        num_agents = num_frames if include_agents else 0
        coords: Dict[str, List[torch.Tensor]] = dict()
        traffic_light_data: Dict[str, List[torch.Tensor]] = dict()
        availabilities: Dict[str, List[torch.BoolTensor]] = dict()
        for feature_name in self.feature_params.map_features:
            coords[feature_name] = [torch.zeros((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name], VectorSetMap.coord_dim()), dtype=torch.float32, device=device)]
            availabilities[feature_name] = [torch.ones((self.feature_params.max_elements[feature_name], self.feature_params.max_points[feature_name]), dtype=torch.bool, device=device)]
        traffic_light_data['LANE'] = [torch.zeros((self.feature_params.max_elements['LANE'], self.feature_params.max_points['LANE'], VectorSetMap.traffic_light_status_dim()), dtype=torch.float32, device=device)]
        vector_set_map_feature = VectorSetMap(coords=coords, traffic_light_data=traffic_light_data, availabilities=availabilities)
        ego_agents = [torch.zeros((num_frames, GenericAgents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = {feature_name: [torch.zeros((num_frames, num_agents, GenericAgents.agents_states_dim()), dtype=torch.float32, device=device)] for feature_name in self.feature_params.agent_features}
        generic_agents_feature = GenericAgents(ego=ego_agents, agents=agent_agents)
        return {'vector_set_map': vector_set_map_feature, 'generic_agents': generic_agents_feature}

    def _find_free_port(self) -> int:
        """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            address, port = s.getsockname()
            return int(port)

    def _init_distributed_process_group(self) -> None:
        """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def _assert_valid_output(self, model_output: TargetsType) -> None:
        """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
        self.assertTrue('trajectory' in model_output)
        self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
        predicted_trajectory: Trajectory = model_output['trajectory']
        self.assertIsNotNone(predicted_trajectory.data)

    def _perform_backprop_step(self, optimizer: torch.optim.Optimizer, loss_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor], predictions: TargetsType) -> None:
        """
        Performs a backpropagation step.
        :param optimizer: The optimizer to use for training.
        :param loss_function: The loss function to use.
        :param predictions: The output from the model.
        """
        loss = loss_function(predictions['trajectory'].data, torch.zeros_like(predictions['trajectory'].data))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    def test_backprop(self) -> None:
        """
        Tests that the UrbanDriverOpenLoop model can train with DDP.
        This test was developed in response to an error related to zero agent input
        """
        self._init_distributed_process_group()
        device = torch.device('cpu')
        model = self._build_model().to(device)
        ddp_model = DDP(model, device_ids=None, output_device=None)
        optimizer = torch.optim.RMSprop(ddp_model.parameters())
        loss_function = torch.nn.MSELoss()
        num_epochs = 3
        for _ in range(num_epochs):
            for include_agents in [True, False]:
                input_features = self._build_input_features(device, include_agents=include_agents)
                predictions = ddp_model.forward(input_features)
                self._assert_valid_output(predictions)
                self._perform_backprop_step(optimizer, loss_function, predictions)

def _init_distributed_process_group(self) -> None:
    """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = str(self._find_free_port())
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    torch.distributed.init_process_group(backend='gloo')

class TestLaneGCN(unittest.TestCase):
    """Test LaneGCN model."""

    def _build_model(self) -> LaneGCN:
        """
        Creates a new instance of a LaneGCN with some default parameters.
        """
        model = LaneGCN(map_net_scales=4, num_res_blocks=4, num_attention_layers=5, a2a_dist_threshold=20, l2a_dist_threshold=20, num_output_features=12, feature_dim=32, vector_map_feature_radius=30, vector_map_connection_scales=[1, 2, 3, 4], past_trajectory_sampling=TrajectorySampling(num_poses=4, time_horizon=1.5), future_trajectory_sampling=TrajectorySampling(num_poses=12, time_horizon=6))
        return model

    def _build_input_features(self, device: torch.device, include_agents: bool, include_lanes: bool) -> FeaturesType:
        """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :param include_lanes: If true, the generated input features will have lanes.
            If not, then there will be no lanes in the vectormap feature.
        :return: FeaturesType to be consumed by the model
        """
        num_frames = 5
        num_coords = 1000
        num_groupings = 100
        num_multi_scale_connections = 800
        num_lanes = num_coords if include_lanes else 0
        num_connections = num_multi_scale_connections if include_lanes else 0
        num_agents = num_frames if include_agents else 0
        vector_map_coords = [torch.zeros((num_lanes, VectorMap.lane_coord_dim(), VectorMap.lane_coord_dim()), dtype=torch.float32, device=device)]
        vector_map_lane_groupings = [[torch.zeros(num_groupings, device=device)]]
        multi_scale_connections = [{1: torch.zeros((num_connections, 2), device=device).long(), 2: torch.zeros((num_connections, 2), device=device).long(), 3: torch.zeros((num_connections, 2), device=device).long(), 4: torch.zeros((num_connections, 2), device=device).long()}]
        on_route_status = [torch.zeros((num_lanes, VectorMap.on_route_status_encoding_dim()), device=device)]
        traffic_light_data = [torch.zeros((num_lanes, 4), device=device)]
        vector_map_feature = VectorMap(coords=vector_map_coords, lane_groupings=vector_map_lane_groupings, multi_scale_connections=multi_scale_connections, on_route_status=on_route_status, traffic_light_data=traffic_light_data)
        ego_agents = [torch.zeros((num_frames, Agents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = [torch.zeros((num_frames, num_agents, Agents.agents_states_dim()), dtype=torch.float32, device=device)]
        agents_feature = Agents(ego=ego_agents, agents=agent_agents)
        return {'vector_map': vector_map_feature, 'agents': agents_feature}

    def _find_free_port(self) -> int:
        """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            address, port = s.getsockname()
            return int(port)

    def _init_distributed_process_group(self) -> None:
        """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def _assert_valid_output(self, model_output: TargetsType) -> None:
        """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
        self.assertTrue('trajectory' in model_output)
        self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
        predicted_trajectory: Trajectory = model_output['trajectory']
        self.assertIsNotNone(predicted_trajectory.data)

    def _perform_backprop_step(self, optimizer: torch.optim.Optimizer, loss_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor], predictions: TargetsType) -> None:
        """
        Performs a backpropagation step.
        :param optimizer: The optimizer to use for training.
        :param loss_function: The loss function to use.
        :param predictions: The output from the model.
        """
        loss = loss_function(predictions['trajectory'].data, torch.zeros_like(predictions['trajectory'].data))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    def test_backprop(self) -> None:
        """
        Tests that the LaneGCN model can train with DDP.
        This test was developed in response to an error related to zero agent input.
        """
        self._init_distributed_process_group()
        device = torch.device('cpu')
        model = self._build_model().to(device)
        ddp_model = DDP(model, device_ids=None, output_device=None)
        optimizer = torch.optim.RMSprop(ddp_model.parameters())
        loss_function = torch.nn.MSELoss()
        num_epochs = 3
        for _ in range(num_epochs):
            for include_agents in [True, False]:
                for include_lanes in [True, False]:
                    input_features = self._build_input_features(device, include_agents=include_agents, include_lanes=include_lanes)
                    predictions = ddp_model.forward(input_features)
                    self._assert_valid_output(predictions)
                    self._perform_backprop_step(optimizer, loss_function, predictions)

def _init_distributed_process_group(self) -> None:
    """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = str(self._find_free_port())
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    torch.distributed.init_process_group(backend='gloo')

class TestVectorMapSimpleMLP(unittest.TestCase):
    """Test graph attention layer."""

    def _build_model(self) -> VectorMapSimpleMLP:
        """
        Creates a new instance of a VectorMapSimpleMLP with some default parameters.
        """
        num_output_features = 36
        hidden_size = 128
        vector_map_feature_radius = 20
        past_trajectory_sampling = TrajectorySampling(num_poses=4, time_horizon=1.5)
        future_trajectory_sampling = TrajectorySampling(num_poses=12, time_horizon=6)
        model = VectorMapSimpleMLP(num_output_features=num_output_features, hidden_size=hidden_size, vector_map_feature_radius=vector_map_feature_radius, past_trajectory_sampling=past_trajectory_sampling, future_trajectory_sampling=future_trajectory_sampling)
        return model

    def _build_input_features(self, device: torch.device, include_agents: bool) -> FeaturesType:
        """
        Creates a set of input features for use with unit testing.
        :param device: The device on which to create the tensors.
        :param include_agents: If true, the generated input features will have agents.
            If not, then there will be no agents in the agents feature.
        :return: FeaturesType to be consumed by the model
        """
        num_frames = 5
        num_coords = 1000
        num_groupings = 100
        num_multi_scale_connections = 800
        num_agents = num_frames if include_agents else 0
        vector_map_coords = [torch.zeros((num_coords, VectorMap.lane_coord_dim(), VectorMap.lane_coord_dim()), dtype=torch.float32, device=device)]
        vector_map_lane_groupings = [[torch.zeros(num_groupings, device=device)]]
        multi_scale_connections = {1: [torch.zeros((num_multi_scale_connections, 2), device=device)]}
        on_route_status = [torch.zeros((num_coords, VectorMap.on_route_status_encoding_dim()), device=device)]
        traffic_light_data = [torch.zeros((num_coords, 4), device=device)]
        vector_map_feature = VectorMap(coords=vector_map_coords, lane_groupings=vector_map_lane_groupings, multi_scale_connections=multi_scale_connections, on_route_status=on_route_status, traffic_light_data=traffic_light_data)
        ego_agents = [torch.zeros((num_frames, Agents.ego_state_dim()), dtype=torch.float32, device=device)]
        agent_agents = [torch.zeros((num_frames, num_agents, Agents.agents_states_dim()), dtype=torch.float32, device=device)]
        agents_feature = Agents(ego=ego_agents, agents=agent_agents)
        return {'vector_map': vector_map_feature, 'agents': agents_feature}

    def _assert_valid_output(self, model_output: TargetsType) -> None:
        """
        Validates that the output from the model has the correct keys and that the tensor is of the correct type.
        :param model_output: The output from the model.
        """
        self.assertTrue('trajectory' in model_output)
        self.assertTrue(isinstance(model_output['trajectory'], Trajectory))
        predicted_trajectory: Trajectory = model_output['trajectory']
        self.assertIsNotNone(predicted_trajectory.data)

    def _perform_backprop_step(self, optimizer: torch.optim.Optimizer, loss_function: Callable[[torch.Tensor, torch.Tensor], torch.Tensor], predictions: TargetsType) -> None:
        """
        Performs a backpropagation step.
        :param optimizer: The optimizer to use for training.
        :param loss_function: The loss function to use.
        :param predictions: The output from the model.
        """
        loss = loss_function(predictions['trajectory'].data, torch.zeros_like(predictions['trajectory'].data))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    def _find_free_port(self) -> int:
        """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            address, port = s.getsockname()
            return int(port)

    def _init_distributed_process_group(self) -> None:
        """
        Sets up the torch distributed processing server.
        :param port: The starting to use for the gloo server. If taken, it will increment by 1 until a free port is found.
        :param max_port: The maximum port number to try.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def _assert_valid_gradients_for_model(self, model: torch.nn.Module) -> None:
        """
        Validates that trainable parameters in a model have gradients after a backprop operation.
        :param model: The model with parameters to update following a forward/backward pass.
        """
        all_gradients_computed = all((param.grad is not None for param in model.parameters() if param.requires_grad))
        self.assertTrue(all_gradients_computed)

    def test_can_train_distributed(self) -> None:
        """
        Tests that the model can train with DDP.
        This test was developed in response to an error like this one:
        https://discuss.pytorch.org/t/need-help-runtimeerror-expected-to-have-finished-reduction-in-the-prior-iteration-before-starting-a-new-one/119247
        """
        self._init_distributed_process_group()
        device = torch.device('cpu')
        model = self._build_model().to(device)
        ddp_model = DDP(model, device_ids=None, output_device=None)
        optimizer = torch.optim.RMSprop(ddp_model.parameters())
        loss_function = torch.nn.MSELoss()
        num_epochs = 3
        for _ in range(num_epochs):
            for include_agents in [True, False]:
                input_features = self._build_input_features(device, include_agents=include_agents)
                predictions = ddp_model.forward(input_features)
                self._assert_valid_output(predictions)
                self._perform_backprop_step(optimizer, loss_function, predictions)
                self._assert_valid_gradients_for_model(ddp_model)

    def test_scripts_properly(self) -> None:
        """
        Test that the VectorMapSimpleMLP model scripts properly.
        """
        model = self._build_model()
        device = torch.device('cpu')
        input_features = self._build_input_features(device, include_agents=True)
        dummy_tensor_input: Dict[str, torch.Tensor] = {}
        dummy_list_tensor_input = {'vector_map.coords': input_features['vector_map'].coords, 'agents.ego': input_features['agents'].ego, 'agents.agents': input_features['agents'].agents}
        dummy_list_list_tensor_input: Dict[str, List[List[torch.Tensor]]] = {}
        scripted_module = torch.jit.script(model)
        scripted_tensors, scripted_list_tensors, scripted_list_list_tensors = scripted_module.scriptable_forward(dummy_tensor_input, dummy_list_tensor_input, dummy_list_list_tensor_input)
        py_tensors, py_list_tensors, py_list_list_tensors = model.scriptable_forward(dummy_tensor_input, dummy_list_tensor_input, dummy_list_list_tensor_input)
        self.assertEqual(1, len(scripted_tensors))
        self.assertEqual(0, len(scripted_list_tensors))
        self.assertEqual(0, len(scripted_list_list_tensors))
        self.assertEqual(1, len(py_tensors))
        self.assertEqual(0, len(py_list_tensors))
        self.assertEqual(0, len(py_list_list_tensors))
        torch.testing.assert_allclose(py_tensors['trajectory'], scripted_tensors['trajectory'])

    def test_can_train_with_empty_vector_map(self) -> None:
        """In case of zero length vector map features, model training should not crash."""
        device = torch.device('cpu')
        test_features = self._build_input_features(device=device, include_agents=True)
        test_features['vector_map'] = _create_empty_vector_map_for_test(device=device)
        self.assertFalse(test_features['vector_map'].is_valid)
        model = self._build_model().to(device)
        optimizer = torch.optim.RMSprop(model.parameters())
        loss_function = torch.nn.MSELoss()
        predictions = model.forward(test_features)
        self._assert_valid_output(predictions)
        self._perform_backprop_step(optimizer, loss_function, predictions)
        self._assert_valid_gradients_for_model(model)

def _init_distributed_process_group(self) -> None:
    """
        Sets up the torch distributed processing server.
        :param port: The starting to use for the gloo server. If taken, it will increment by 1 until a free port is found.
        :param max_port: The maximum port number to try.
        """
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = str(self._find_free_port())
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    torch.distributed.init_process_group(backend='gloo')

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
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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

@property
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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

@property
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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

def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """
        Gets name of the attributes to be modified by augmentation scheduler callback.
        :return: Names of attributes to be modified by augmentation scheduler callback.
        """
    return [ParameterToScale(self.mean, param_name=f'self.mean={self.mean!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX), ParameterToScale(self.std, param_name=f'self.std={self.std!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)]

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

def get_schedulable_attributes(self) -> List[ParameterToScale]:
    """
        Gets attributes to be modified by augmentation scheduler callback.
        :return: Attributes to be modified by augmentation scheduler callback.
        """
    return [ParameterToScale(param=self.low, param_name=f'self.low={self.low!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX), ParameterToScale(param=self.high, param_name=f'self.high={self.high!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)]

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
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

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
def augmentation_probability(self) -> ParameterToScale:
    """Inherited, see superclass."""
    return ParameterToScale(param=self._augment_prob, param_name=f'self._augment_prob={self._augment_prob!r}'.partition('=')[0].split('.')[1], scaling_direction=ScalingDirection.MAX)

def save_cache_metadata(cache_metadata_entries: List[CacheMetadataEntry], cache_path: Path, node_id: int) -> None:
    """
    Saves list of CacheMetadataEntry to output csv file path.
    :param cache_metadata_entries: List of metadata objects for cached features.
    :param cache_path: Path to s3 cache.
    :param node_id: Node ID of a node used for differentiating between nodes in multi-node caching.
    """
    cache_metadata_entries_dicts = [asdict(entry) for entry in cache_metadata_entries]
    cache_name = cache_path.name
    using_s3_cache_path = str(cache_path).startswith('s3:/')
    sanitized_cache_path = safe_path_to_string(cache_path)
    cache_metadata_storage_path = os.path.join(sanitized_cache_path, 'metadata', f'{cache_name}_metadata_node_{node_id}.csv')
    if not using_s3_cache_path:
        Path(cache_metadata_storage_path).parent.mkdir(parents=True, exist_ok=True)
    logger.info(f'Using cache_metadata_storage_path: {cache_metadata_storage_path}')
    pd.DataFrame(cache_metadata_entries_dicts).to_csv(cache_metadata_storage_path, index=False)

def _read_metadata_from_s3(inputs: List[ReadMetadataFromS3Input]) -> List[CacheMetadataEntry]:
    """
    Reads metadata csv from s3.
    :param inputs: The inputs to use for the function.
    :returns: The read metadata.
    """
    outputs: List[CacheMetadataEntry] = []
    if len(inputs) == 0:
        return outputs
    sanitized_cache_path = safe_path_to_string(inputs[0].cache_path)
    s3_store = S3Store(sanitized_cache_path)
    for input_value in inputs:
        df = pd.read_csv(s3_store.get(input_value.metadata_filename))
        metadata_dict_list = df.to_dict('records')
        for metadata_dict in metadata_dict_list:
            outputs.append(CacheMetadataEntry(**metadata_dict))
    return outputs

class TestScenarioSamplingWeights(unittest.TestCase):
    """
    Tests data loading functionality in a sequential manner.
    """

    def setUp(self) -> None:
        """Set up test variables."""
        self.mock_scenario_sampling_weights = {DEFAULT_SCENARIO_NAME: 0.5}
        self.mock_scenario_types = [DEFAULT_SCENARIO_NAME, 'following_lane_with_lead']
        self.mock_scenarios = []
        for scenario_type in self.mock_scenario_types:
            self.mock_scenarios += [CachedScenario(log_name='', token='', scenario_type=scenario_type) for _ in range(3)]
        self.expected_sampler_weights = [self.mock_scenario_sampling_weights[DEFAULT_SCENARIO_NAME]] * 3 + [1.0] * 3

    def _find_free_port(self) -> int:
        """
        Finds a free port to use for gloo server.
        :return: A port not in use.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            address, port = s.getsockname()
            return int(port)

    def _init_distributed_process_group(self) -> None:
        """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
        os.environ['MASTER_ADDR'] = 'localhost'
        os.environ['MASTER_PORT'] = str(self._find_free_port())
        os.environ['RANK'] = '0'
        os.environ['WORLD_SIZE'] = '1'
        torch.distributed.init_process_group(backend='gloo')

    def test_scenario_sampling_weight_initialises_correctly(self) -> None:
        """
        Test that the scenario sampling weights are correct.
        """
        self._init_distributed_process_group()
        scenarios_dataset = Mock(ScenarioDataset)
        scenarios_dataset._scenarios = self.mock_scenarios
        distributed_weight_sampler = distributed_weighted_sampler_init(scenario_dataset=scenarios_dataset, scenario_sampling_weights=self.mock_scenario_sampling_weights)
        self.assertEqual(list(distributed_weight_sampler.sampler.weights), self.expected_sampler_weights)

def _init_distributed_process_group(self) -> None:
    """
        Sets up the torch distributed processing server.
        :param port: The port to use for the gloo server.
        """
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = str(self._find_free_port())
    os.environ['RANK'] = '0'
    os.environ['WORLD_SIZE'] = '1'
    torch.distributed.init_process_group(backend='gloo')

class SkeletonTestDataloader(unittest.TestCase):
    """
    Skeleton with initialized dataloader used in testing.
    """

    def setUp(self) -> None:
        """
        Set up basic configs.
        """
        pl.seed_everything(2022, workers=True)
        self.splitter = LogSplitter(log_splits={'train': ['2021.07.16.20.45.29_veh-35_01095_01486'], 'val': ['2021.06.07.18.53.26_veh-26_00005_00427'], 'test': ['2021.10.06.07.26.10_veh-52_00006_00398']})
        feature_builders = [DummyVectorMapBuilder(), VectorMapFeatureBuilder(radius=20), AgentsFeatureBuilder(TrajectorySampling(num_poses=4, time_horizon=1.5)), RasterFeatureBuilder(map_features={'LANE': 1, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1)]
        target_builders = [EgoTrajectoryTargetBuilder(TrajectorySampling(num_poses=10, time_horizon=5.0))]
        self.feature_preprocessor = FeaturePreprocessor(cache_path=None, force_feature_computation=True, feature_builders=feature_builders, target_builders=target_builders)
        self.scenario_filter = ScenarioFilter(scenario_types=None, scenario_tokens=None, log_names=None, map_names=None, num_scenarios_per_type=None, limit_total_scenarios=150, expand_scenarios=True, remove_invalid_goals=False, shuffle=True, timestamp_threshold_s=None, ego_displacement_minimum_m=None, ego_start_speed_threshold=None, ego_stop_speed_threshold=None, speed_noise_tolerance=None, token_set_path=None, fraction_in_token_set_threshold=None)
        self.augmentors = [KinematicAgentAugmentor(trajectory_length=10, dt=0.1, mean=[0.3, 0.1, np.pi / 12], std=[0.5, 0.1, np.pi / 12], low=[-0.2, 0.0, 0.0], high=[0.8, 0.2, np.pi / 6], augment_prob=0.5)]
        self.scenario_builder = get_test_nuplan_scenario_builder()

    def _test_dataloader(self, worker: WorkerPool) -> None:
        """
        Tests that the training dataloader can be iterated without errors
        """
        scenarios = self.scenario_builder.get_scenarios(self.scenario_filter, worker)
        self.assertGreater(len(scenarios), 0)
        batch_size = 4
        num_workers = 4
        scenario_type_sampling_weights = DictConfig({'enable': False, 'scenario_type_weights': {'unknown': 1.0}})
        datamodule = DataModule(feature_preprocessor=self.feature_preprocessor, splitter=self.splitter, train_fraction=1.0, val_fraction=0.1, test_fraction=0.1, all_scenarios=scenarios, augmentors=self.augmentors, worker=worker, scenario_type_sampling_weights=scenario_type_sampling_weights, dataloader_params={'batch_size': batch_size, 'num_workers': num_workers, 'drop_last': True})
        datamodule.setup('fit')
        self.assertGreater(len(datamodule.train_dataloader()), 0)
        for features, targets, scenarios in datamodule.train_dataloader():
            self.assertTrue('raster' in features.keys())
            self.assertTrue('vector_map' in features.keys())
            self.assertTrue('trajectory' in targets.keys())
            scenario_features: Raster = features['raster']
            trajectory_target: Trajectory = targets['trajectory']
            self.assertEqual(scenario_features.num_batches, trajectory_target.num_batches)
            self.assertIsInstance(scenario_features, Raster)
            self.assertIsInstance(trajectory_target, Trajectory)
            self.assertEqual(scenario_features.num_batches, batch_size)

    def tearDown(self) -> None:
        """
        Clean up.
        """
        if ray.is_initialized():
            ray.shutdown()

def tearDown(self) -> None:
    """
        Clean up.
        """
    if ray.is_initialized():
        ray.shutdown()

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

def _dump_scenes(scenes: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Dump a single scene file
    :param scenes: list of scenes to be written
    :param output_dir: final output directory
    """
    for scene in scenes:
        file_name = output_dir / str(scene['ego']['timestamp_us'])
        with open(str(file_name.with_suffix('.json')), 'w') as outfile:
            json.dump(scene, outfile, indent=4)

class ProfileCallback(pl.Callback):
    """Profiling callback that produces an html report."""

    def __init__(self, output_dir: pathlib.Path, interval: float=0.01):
        """
        Initialize callback.
        :param output_dir: directory where output should be stored. Note, "profiling" sub-dir will be added
        :param interval: of the profiler
        """
        self._output_dir = output_dir / 'profiling'
        if not is_s3_path(self._output_dir):
            self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Profiler will report into folder: {str(self._output_dir)}')
        self._profiler = Profiler(interval=interval)
        self._profiler_running = False

    def on_init_start(self, trainer: pl.Trainer) -> None:
        """
        Called during training initialization.
        :param trainer: Lightning trainer.
        """
        self.start_profiler('on_init_start')

    def on_init_end(self, trainer: pl.Trainer) -> None:
        """
        Called at the end of the training.
        :param trainer: Lightning trainer.
        """
        self.save_profiler('on_init_end')

    def on_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at each epoch start.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        self.start_profiler('on_epoch_start')

    def on_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at each epoch end.
        :param trainer: Lightning trainer.
        :param pl_module: lightning model.
        """
        self.save_profiler('epoch_' + str(trainer.current_epoch) + '-on_epoch_end')

    def start_profiler(self, when: str) -> None:
        """
        Start the profiler.
        Raise: in case profiler is already running.
        :param when: Message to log when starting the profiler.
        """
        assert not self._profiler_running, 'Profiler can not be started twice!'
        logger.info(f'STARTING profiler: {when}')
        self._profiler_running = True
        self._profiler.start()

    def stop_profiler(self) -> None:
        """
        Start profiler
        Raise: in case profiler is not running
        """
        assert self._profiler_running, 'Profiler has to be running!!'
        self._profiler.stop()
        self._profiler_running = False

    def save_profiler(self, file_name: str) -> None:
        """
        Save profiling output to a html report
        :param file_name: File name to save report to.
        """
        self.stop_profiler()
        profiler_out_html = self._profiler.output_html()
        html_save_path = self._output_dir / file_name
        path = str(html_save_path.with_suffix('.html'))
        logger.info(f'Saving profiler output to: {path}')
        fp = open(path, 'w+')
        fp.write(profiler_out_html)
        fp.close()

def __init__(self, output_dir: pathlib.Path, interval: float=0.01):
    """
        Initialize callback.
        :param output_dir: directory where output should be stored. Note, "profiling" sub-dir will be added
        :param interval: of the profiler
        """
    self._output_dir = output_dir / 'profiling'
    if not is_s3_path(self._output_dir):
        self._output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'Profiler will report into folder: {str(self._output_dir)}')
    self._profiler = Profiler(interval=interval)
    self._profiler_running = False

def save_profiler(self, file_name: str) -> None:
    """
        Save profiling output to a html report
        :param file_name: File name to save report to.
        """
    self.stop_profiler()
    profiler_out_html = self._profiler.output_html()
    html_save_path = self._output_dir / file_name
    path = str(html_save_path.with_suffix('.html'))
    logger.info(f'Saving profiler output to: {path}')
    fp = open(path, 'w+')
    fp.write(profiler_out_html)
    fp.close()

class TimeLoggingCallback(pl.Callback):
    """Log training & validation epoch time."""

    def __init__(self) -> None:
        """
        Setup start timestamp.
        """
        self.train_start = 0.0
        self.valid_start = 0.0
        self.test_start = 0.0

    def on_validation_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the start of each validation epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
        self.valid_start = time.time()

    def on_validation_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the end of each validation epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
        pl_module.log_dict({'time_eval': time.time() - self.valid_start, 'step': pl_module.current_epoch})

    def on_test_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the start of each test epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
        self.test_start = time.time()

    def on_test_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the end of each test epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
        pl_module.log_dict({'time_test': time.time() - self.test_start, 'step': pl_module.current_epoch})

    def on_train_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
        """
        Called at the start of each train epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
        self.train_start = time.time()

    def on_train_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional[Any]=None) -> None:
        """
        Called at the end of each train epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        :param outputs: Not required for time logging.
        """
        pl_module.log_dict({'time_epoch': time.time() - self.train_start, 'step': pl_module.current_epoch})

def on_validation_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at the start of each validation epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
    self.valid_start = time.time()

def on_validation_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at the end of each validation epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
    pl_module.log_dict({'time_eval': time.time() - self.valid_start, 'step': pl_module.current_epoch})

def on_test_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at the start of each test epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
    self.test_start = time.time()

def on_test_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at the end of each test epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
    pl_module.log_dict({'time_test': time.time() - self.test_start, 'step': pl_module.current_epoch})

def on_train_epoch_start(self, trainer: pl.Trainer, pl_module: pl.LightningModule) -> None:
    """
        Called at the start of each train epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        """
    self.train_start = time.time()

def on_train_epoch_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule, unused: Optional[Any]=None) -> None:
    """
        Called at the end of each train epoch.
        :param trainer: Trainer instance.
        :param pl_module: LightningModule instance.
        :param outputs: Not required for time logging.
        """
    pl_module.log_dict({'time_epoch': time.time() - self.train_start, 'step': pl_module.current_epoch})

class TestScenarioScoringCallback(unittest.TestCase):
    """Test scenario scoring callback"""

    def setUp(self) -> None:
        """Set up test case."""
        self.output_dir = tempfile.TemporaryDirectory()
        preprocessor = Mock()
        preprocessor.compute_features.side_effect = mock_compute_features
        self.mock_scenarios = [MockAbstractScenario(mission_goal=StateSE2(x=1.0, y=0.0, heading=0.0)), MockAbstractScenario(mission_goal=StateSE2(x=0.0, y=0.0, heading=0.0))]
        self.scenario_time_stamp = self.mock_scenarios[0]._initial_time_us
        mock_scenario_dataset = ScenarioDataset(scenarios=self.mock_scenarios, feature_preprocessor=preprocessor)
        mock_datamodule = Mock()
        mock_datamodule.val_dataloader().dataset = mock_scenario_dataset
        self.trainer = Mock()
        self.trainer.datamodule = mock_datamodule
        self.trainer.current_epoch = 1
        mock_objective = Mock()
        mock_objective.compute.side_effect = mock_compute_objective
        self.pl_module = Mock()
        self.pl_module.device = 'cpu'
        self.pl_module.side_effect = mock_predict
        self.pl_module.objectives = [mock_objective]
        scenario_converter = ScenarioSceneConverter(ego_trajectory_horizon=1, ego_trajectory_poses=2)
        self.callback = ScenarioScoringCallback(scene_converter=scenario_converter, num_store=1, frequency=1, output_dir=self.output_dir.name)
        self.callback._initialize_dataloaders(self.trainer.datamodule)

    def test_initialize_dataloaders(self) -> None:
        """
        Test callback dataloader initialization.
        """
        invalid_datamodule = Mock()
        invalid_datamodule.val_dataloader().dataset = None
        with self.assertRaises(AssertionError):
            self.callback._initialize_dataloaders(invalid_datamodule)
        self.callback._initialize_dataloaders(self.trainer.datamodule)
        self.assertIsInstance(self.callback._val_dataloader, torch.utils.data.DataLoader)

    def test_score_model(self) -> None:
        """
        Test scoring of the model with mock features.
        """
        data1 = torch.tensor(1)
        data2 = torch.tensor(2)
        data3 = torch.tensor(3)
        mock_feature = DummyVectorMapFeature(data1=[data1], data2=[data2], data3=[{'test': data3}])
        mock_input = {'mock_feature': mock_feature}
        score, prediction = _score_model(self.pl_module, mock_input, mock_input)
        self.assertEqual(score, mock_feature.data1[0])
        self.assertEqual(prediction, mock_input)

    def test_on_validation_epoch_end(self) -> None:
        """
        Test on validation callback.
        """
        BEST_INDEX = 1
        WORST_INDEX = 0
        self.callback._initialize_dataloaders(self.trainer.datamodule)
        self.callback.on_validation_epoch_end(self.trainer, self.pl_module)
        best_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/best/{self.mock_scenarios[BEST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
        self.assertTrue(best_score_path.exists())
        worst_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/worst/{self.mock_scenarios[WORST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
        self.assertTrue(worst_score_path.exists())
        random_score_dir = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}/random/')
        random_score_paths = list(random_score_dir.glob(f'*/{self.scenario_time_stamp.time_us}.json'))
        self.assertEqual(len(random_score_paths), 1)
        with open(str(best_score_path), 'r') as f:
            best_data = json.load(f)
        with open(str(worst_score_path), 'r') as f:
            worst_data = json.load(f)
        self.assertEqual(worst_data['goal']['pose'][0], self.mock_scenarios[WORST_INDEX].get_mission_goal().x)
        self.assertEqual(best_data['goal']['pose'][0], self.mock_scenarios[BEST_INDEX].get_mission_goal().x)

def test_on_validation_epoch_end(self) -> None:
    """
        Test on validation callback.
        """
    BEST_INDEX = 1
    WORST_INDEX = 0
    self.callback._initialize_dataloaders(self.trainer.datamodule)
    self.callback.on_validation_epoch_end(self.trainer, self.pl_module)
    best_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/best/{self.mock_scenarios[BEST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
    self.assertTrue(best_score_path.exists())
    worst_score_path = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}' + f'/worst/{self.mock_scenarios[WORST_INDEX].token}/{self.scenario_time_stamp.time_us}.json')
    self.assertTrue(worst_score_path.exists())
    random_score_dir = pathlib.Path(self.output_dir.name + f'/scenes/epoch={self.trainer.current_epoch}/random/')
    random_score_paths = list(random_score_dir.glob(f'*/{self.scenario_time_stamp.time_us}.json'))
    self.assertEqual(len(random_score_paths), 1)
    with open(str(best_score_path), 'r') as f:
        best_data = json.load(f)
    with open(str(worst_score_path), 'r') as f:
        worst_data = json.load(f)
    self.assertEqual(worst_data['goal']['pose'][0], self.mock_scenarios[WORST_INDEX].get_mission_goal().x)
    self.assertEqual(best_data['goal']['pose'][0], self.mock_scenarios[BEST_INDEX].get_mission_goal().x)

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

def compute_or_load_feature(scenario: AbstractScenario, cache_path: Optional[pathlib.Path], builder: Union[AbstractFeatureBuilder, AbstractTargetBuilder], storing_mechanism: FeatureCache, force_feature_computation: bool) -> Tuple[AbstractModelFeature, Optional[CacheMetadataEntry]]:
    """
    Compute features if non existent in cache, otherwise load them from cache
    :param scenario: for which features should be computed
    :param cache_path: location of cached features
    :param builder: which builder should compute the features
    :param storing_mechanism: a way to store features
    :param force_feature_computation: if true, even if cache exists, it will be overwritten
    :return features computed with builder and the metadata entry for the computed feature if feature is valid.
    """
    cache_path_available = cache_path is not None
    file_name = cache_path / scenario.log_name / scenario.scenario_type / scenario.token / builder.get_feature_unique_name() if cache_path_available else None
    need_to_compute_feature = force_feature_computation or not cache_path_available or (not storing_mechanism.exists_feature_cache(file_name))
    feature_stored_sucessfully = False
    if need_to_compute_feature:
        logger.debug('Computing feature...')
        if isinstance(scenario, CachedScenario):
            raise ValueError(textwrap.dedent(f'\n                Attempting to recompute scenario with CachedScenario.\n                This should typically never happen, and usually means that the scenario is missing from the cache.\n                Check the cache to ensure that the scenario is present.\n\n                If it was intended to re-compute the feature on the fly, re-run with `cache.use_cache_without_dataset=False`.\n\n                Debug information:\n                Scenario type: {scenario.scenario_type}. Scenario log name: {scenario.log_name}. Scenario token: {scenario.token}.\n                '))
        if isinstance(builder, AbstractFeatureBuilder):
            feature = builder.get_features_from_scenario(scenario)
        elif isinstance(builder, AbstractTargetBuilder):
            feature = builder.get_targets(scenario)
        else:
            raise ValueError(f'Unknown builder type: {type(builder)}')
        if feature.is_valid and cache_path_available:
            logger.debug(f'Saving feature: {file_name} to a file...')
            file_name.parent.mkdir(parents=True, exist_ok=True)
            feature_stored_sucessfully = storing_mechanism.store_computed_feature_to_folder(file_name, feature)
    else:
        logger.debug(f'Loading feature: {file_name} from a file...')
        feature = storing_mechanism.load_computed_feature_from_folder(file_name, builder.get_feature_type())
        assert feature.is_valid, 'Invalid feature loaded from cache!'
    return (feature, CacheMetadataEntry(file_name=file_name) if need_to_compute_feature and feature_stored_sucessfully else None)

class FeatureCachePickle(FeatureCache):
    """
    Store features with pickle
    """

    def exists_feature_cache(self, feature_file: pathlib.Path) -> bool:
        """Inherited, see superclass."""
        return pathlib.Path(self.with_extension(feature_file)).exists()

    def with_extension(self, feature_file: pathlib.Path) -> str:
        """Inherited, see superclass."""
        return str(feature_file.with_suffix('.gz'))

    def store_computed_feature_to_folder(self, feature_file: pathlib.Path, feature: AbstractModelFeature) -> bool:
        """Inherited, see superclass."""
        serializable_dict = feature.serialize()
        with gzip.open(self.with_extension(feature_file), 'wb', compresslevel=1) as f:
            pickle.dump(serializable_dict, f)
        return True

    def load_computed_feature_from_folder(self, feature_file: pathlib.Path, feature_type: Type[AbstractModelFeature]) -> AbstractModelFeature:
        """Inherited, see superclass."""
        with gzip.open(self.with_extension(feature_file), 'rb') as f:
            data = pickle.load(f)
        return feature_type.deserialize(data)

def exists_feature_cache(self, feature_file: pathlib.Path) -> bool:
    """Inherited, see superclass."""
    return pathlib.Path(self.with_extension(feature_file)).exists()

def with_extension(self, feature_file: pathlib.Path) -> str:
    """Inherited, see superclass."""
    return str(feature_file.with_suffix('.gz'))

def store_computed_feature_to_folder(self, feature_file: pathlib.Path, feature: AbstractModelFeature) -> bool:
    """Inherited, see superclass."""
    serializable_dict = feature.serialize()
    with gzip.open(self.with_extension(feature_file), 'wb', compresslevel=1) as f:
        pickle.dump(serializable_dict, f)
    return True

def load_computed_feature_from_folder(self, feature_file: pathlib.Path, feature_type: Type[AbstractModelFeature]) -> AbstractModelFeature:
    """Inherited, see superclass."""
    with gzip.open(self.with_extension(feature_file), 'rb') as f:
        data = pickle.load(f)
    return feature_type.deserialize(data)

class FeatureCacheS3(FeatureCache):
    """
    Store features remotely in S3
    """

    def __init__(self, s3_path: str) -> None:
        """
        Initialize the S3 remote feature cache.
        :param s3_path: Path to S3 directory where features will be stored to or loaded from.
        """
        self._store = S3Store(s3_path, show_progress=False)

    def exists_feature_cache(self, feature_file: pathlib.Path) -> bool:
        """Inherited, see superclass."""
        return cast(bool, check_s3_path_exists(self.with_extension(feature_file)))

    def with_extension(self, feature_file: pathlib.Path) -> str:
        """Inherited, see superclass."""
        fixed_s3_filename = f's3://{str(feature_file).lstrip('s3:/')}'
        return f'{fixed_s3_filename}.bin'

    def store_computed_feature_to_folder(self, feature_file: pathlib.Path, feature: AbstractModelFeature) -> bool:
        """Inherited, see superclass."""
        serialized_feature = BytesIO()
        joblib.dump(feature, serialized_feature)
        serialized_feature.seek(os.SEEK_SET)
        storage_key = self.with_extension(feature_file)
        successfully_stored_feature = self._store.put(storage_key, serialized_feature, ignore_if_client_error=True)
        return cast(bool, successfully_stored_feature)

    def load_computed_feature_from_folder(self, feature_file: pathlib.Path, feature_type: Type[AbstractModelFeature]) -> AbstractModelFeature:
        """Inherited, see superclass."""
        storage_key = self.with_extension(feature_file)
        serialized_feature = self._store.get(storage_key)
        feature = joblib.load(serialized_feature)
        return feature

def __init__(self, s3_path: str) -> None:
    """
        Initialize the S3 remote feature cache.
        :param s3_path: Path to S3 directory where features will be stored to or loaded from.
        """
    self._store = S3Store(s3_path, show_progress=False)

def exists_feature_cache(self, feature_file: pathlib.Path) -> bool:
    """Inherited, see superclass."""
    return cast(bool, check_s3_path_exists(self.with_extension(feature_file)))

def with_extension(self, feature_file: pathlib.Path) -> str:
    """Inherited, see superclass."""
    fixed_s3_filename = f's3://{str(feature_file).lstrip('s3:/')}'
    return f'{fixed_s3_filename}.bin'

def store_computed_feature_to_folder(self, feature_file: pathlib.Path, feature: AbstractModelFeature) -> bool:
    """Inherited, see superclass."""
    serialized_feature = BytesIO()
    joblib.dump(feature, serialized_feature)
    serialized_feature.seek(os.SEEK_SET)
    storage_key = self.with_extension(feature_file)
    successfully_stored_feature = self._store.put(storage_key, serialized_feature, ignore_if_client_error=True)
    return cast(bool, successfully_stored_feature)

def load_computed_feature_from_folder(self, feature_file: pathlib.Path, feature_type: Type[AbstractModelFeature]) -> AbstractModelFeature:
    """Inherited, see superclass."""
    storage_key = self.with_extension(feature_file)
    serialized_feature = self._store.get(storage_key)
    feature = joblib.load(serialized_feature)
    return feature

def _create_tracked_objects(num_frames: int, num_agents: int, object_type: TrackedObjectType=TrackedObjectType.VEHICLE) -> List[TrackedObjects]:
    """
    Generate dummy agent trajectories
    :param num_frames: length of the trajectory to be generate
    :param num_agents: number of agents to generate
    :param object_type: agent type.
    :return: agent trajectories [num_frames, num_agents, 1]
    """
    return [TrackedObjects([_create_scene_object(str(num), object_type) for num in range(num_agents)]) for _ in range(num_frames)]

class TestFeaturePreprocessor(unittest.TestCase):
    """Tests preprocessing and caching functionality during training."""

    def setUp(self) -> None:
        """
        Set up test case.
        """
        self.cache_path = pathlib.Path('/tmp/test')

    def test_sample(self) -> None:
        """
        Test computation of a features for sample
        """
        raster_feature_builder = RasterFeatureBuilder(map_features={'LANE': 1.0, 'INTERSECTION': 1.0, 'STOP_LINE': 0.5, 'CROSSWALK': 0.5}, num_input_channels=4, target_width=224, target_height=224, target_pixel_size=0.5, ego_width=2.297, ego_front_length=4.049, ego_rear_length=1.127, ego_longitudinal_offset=0.0, baseline_path_thickness=1)
        vectormap_builder = VectorMapFeatureBuilder(radius=20)
        ego_trajectory_target_builder = EgoTrajectoryTargetBuilder(TrajectorySampling(num_poses=10, time_horizon=5.0))
        logging.basicConfig(level=logging.INFO)
        feature_preprocessor = FeaturePreprocessor(cache_path=str(self.cache_path), feature_builders=[raster_feature_builder, vectormap_builder], target_builders=[ego_trajectory_target_builder], force_feature_computation=False)
        scenario = get_test_nuplan_scenario()
        self._compute_features_and_check_builders(scenario, feature_preprocessor, 2, 1)

    def _compute_features_and_check_builders(self, sample: Any, feature_preprocessor: FeaturePreprocessor, number_of_features: int, number_of_targets: int) -> None:
        """
        :param sample: Input data sample to compute features/targets from.
        :param feature_preprocessor: Preprocessor object with caching mechanism.
        :param number_of_features: Number of expected features.
        :param number_of_targets: Number of expected targets.
        """
        features, targets, _ = feature_preprocessor.compute_features(sample)
        self.assertEqual(len(targets), number_of_targets)
        self.assertEqual(len(features), number_of_features)
        for builder in feature_preprocessor.feature_builders:
            self.assertTrue(builder.get_feature_unique_name() in features.keys())
            feature = features[builder.get_feature_unique_name()]
            self.assertIsInstance(feature, builder.get_feature_type())
            self.assertTrue(feature.is_valid)
        for builder in feature_preprocessor.target_builders:
            self.assertTrue(builder.get_feature_unique_name() in targets.keys())
            target = targets[builder.get_feature_unique_name()]
            self.assertIsInstance(target, builder.get_feature_type())
            self.assertTrue(target.is_valid)

def setUp(self) -> None:
    """
        Set up test case.
        """
    self.cache_path = pathlib.Path('/tmp/test')

class TestUtilsCache(unittest.TestCase):
    """Test caching utilities."""

    def setUp(self) -> None:
        """Set up test case."""
        local_cache_path = '/tmp/cache'
        s3_cache_path = 's3://tmp/cache'
        self.cache_paths = [local_cache_path, s3_cache_path]
        local_store = FeatureCachePickle()
        s3_store = FeatureCacheS3(s3_cache_path)
        s3_store._store = MockS3Store()
        self.cache_engines = [local_store, s3_store]

    def test_storing_to_cache_vector_map(self) -> None:
        """
        Test storing feature to cache
        """
        dim = 50
        feature = VectorMap(coords=[np.zeros((dim, 2, 2)).astype(np.float32)], lane_groupings=[[np.zeros(dim).astype(np.float32)]], multi_scale_connections=[{1: np.zeros((dim, 2)).astype(np.float32)}], on_route_status=[np.zeros((dim, 2)).astype(np.float32)], traffic_light_data=[np.zeros((dim, 4)).astype(np.float32)])
        for cache_path, cache in zip(self.cache_paths, self.cache_engines):
            folder = pathlib.Path(cache_path) / 'tmp_log_name' / 'tmp_scenario_token' / 'vector_map'
            if not str(folder).startswith('s3:/'):
                folder.parent.mkdir(parents=True, exist_ok=True)
            time_now = time.time()
            loaded_feature: VectorMap = self.store_and_load(cache, folder, feature)
            time_later = time.time()
            logger.debug(f'Cache: {type(cache)} = {time_later - time_now}')
            self.assertEqual(feature.num_of_batches, loaded_feature.num_of_batches)
            self.assertEqual(1, loaded_feature.num_of_batches)
            self.assertEqual(feature.coords[0].shape, loaded_feature.coords[0].shape)
            self.assertEqual(feature.lane_groupings[0][0].shape, loaded_feature.lane_groupings[0][0].shape)
            self.assertEqual(feature.multi_scale_connections[0][1].shape, loaded_feature.multi_scale_connections[0][1].shape)

    def test_storing_to_cache_raster(self) -> None:
        """
        Test storing feature to cache
        """
        feature = Raster(data=np.zeros((244, 244, 3)))
        for cache_path, cache in zip(self.cache_paths, self.cache_engines):
            folder = pathlib.Path(cache_path) / 'tmp_log_name' / 'tmp_scenario_token' / 'raster'
            if not str(folder).startswith('s3:/'):
                folder.parent.mkdir(parents=True, exist_ok=True)
            loaded_feature = self.store_and_load(cache, folder, feature)
            self.assertEqual(feature.data.shape, loaded_feature.data.shape)

    def store_and_load(self, cache: FeatureCache, folder: pathlib.Path, feature: AbstractModelFeature) -> AbstractModelFeature:
        """
        Store feature and load it back.
        :param cache: Caching mechanism to use.
        :param folder: Folder to store feature.
        :param feature: Feature to store.
        :return: Loaded feature.
        """
        time_now = time.time()
        cache.store_computed_feature_to_folder(folder, feature)
        logger.debug(f'store_computed_feature_to_folder: {type(cache)} = {time.time() - time_now}')
        time_now = time.time()
        out = cache.load_computed_feature_from_folder(folder, feature)
        logger.debug(f'load_computed_feature_from_folder: {type(cache)} = {time.time() - time_now}')
        self.assertIsInstance(out, type(feature))
        return out

def setUp(self) -> None:
    """Set up test case."""
    local_cache_path = '/tmp/cache'
    s3_cache_path = 's3://tmp/cache'
    self.cache_paths = [local_cache_path, s3_cache_path]
    local_store = FeatureCachePickle()
    s3_store = FeatureCacheS3(s3_cache_path)
    s3_store._store = MockS3Store()
    self.cache_engines = [local_store, s3_store]

def test_storing_to_cache_vector_map(self) -> None:
    """
        Test storing feature to cache
        """
    dim = 50
    feature = VectorMap(coords=[np.zeros((dim, 2, 2)).astype(np.float32)], lane_groupings=[[np.zeros(dim).astype(np.float32)]], multi_scale_connections=[{1: np.zeros((dim, 2)).astype(np.float32)}], on_route_status=[np.zeros((dim, 2)).astype(np.float32)], traffic_light_data=[np.zeros((dim, 4)).astype(np.float32)])
    for cache_path, cache in zip(self.cache_paths, self.cache_engines):
        folder = pathlib.Path(cache_path) / 'tmp_log_name' / 'tmp_scenario_token' / 'vector_map'
        if not str(folder).startswith('s3:/'):
            folder.parent.mkdir(parents=True, exist_ok=True)
        time_now = time.time()
        loaded_feature: VectorMap = self.store_and_load(cache, folder, feature)
        time_later = time.time()
        logger.debug(f'Cache: {type(cache)} = {time_later - time_now}')
        self.assertEqual(feature.num_of_batches, loaded_feature.num_of_batches)
        self.assertEqual(1, loaded_feature.num_of_batches)
        self.assertEqual(feature.coords[0].shape, loaded_feature.coords[0].shape)
        self.assertEqual(feature.lane_groupings[0][0].shape, loaded_feature.lane_groupings[0][0].shape)
        self.assertEqual(feature.multi_scale_connections[0][1].shape, loaded_feature.multi_scale_connections[0][1].shape)

def test_storing_to_cache_raster(self) -> None:
    """
        Test storing feature to cache
        """
    feature = Raster(data=np.zeros((244, 244, 3)))
    for cache_path, cache in zip(self.cache_paths, self.cache_engines):
        folder = pathlib.Path(cache_path) / 'tmp_log_name' / 'tmp_scenario_token' / 'raster'
        if not str(folder).startswith('s3:/'):
            folder.parent.mkdir(parents=True, exist_ok=True)
        loaded_feature = self.store_and_load(cache, folder, feature)
        self.assertEqual(feature.data.shape, loaded_feature.data.shape)

def store_and_load(self, cache: FeatureCache, folder: pathlib.Path, feature: AbstractModelFeature) -> AbstractModelFeature:
    """
        Store feature and load it back.
        :param cache: Caching mechanism to use.
        :param folder: Folder to store feature.
        :param feature: Feature to store.
        :return: Loaded feature.
        """
    time_now = time.time()
    cache.store_computed_feature_to_folder(folder, feature)
    logger.debug(f'store_computed_feature_to_folder: {type(cache)} = {time.time() - time_now}')
    time_now = time.time()
    out = cache.load_computed_feature_from_folder(folder, feature)
    logger.debug(f'load_computed_feature_from_folder: {type(cache)} = {time.time() - time_now}')
    self.assertIsInstance(out, type(feature))
    return out

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

@torch.jit.export
def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
    """
        Inherited. See interface.
        """
    return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses), 'agent_features': ','.join(self.agent_features)}}

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

@torch.jit.export
def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
    """
        Implemented. See Interface.
        """
    empty: Dict[str, str] = {}
    return {'neighbor_vector_map': {'radius': str(self._radius)}, 'initial_ego_state': empty}

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

@torch.jit.export
def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
    """
        Implemented. See Interface.
        """
    empty: Dict[str, str] = {}
    max_elements: List[str] = [f'{feature_name}.{feature_max_elements}' for feature_name, feature_max_elements in self.max_elements.items()]
    max_points: List[str] = [f'{feature_name}.{feature_max_points}' for feature_name, feature_max_points in self.max_points.items()]
    return {'neighbor_vector_set_map': {'radius': str(self.radius), 'interpolation_method': self.interpolation_method, 'map_features': ','.join(self.map_features), 'max_elements': ','.join(max_elements), 'max_points': ','.join(max_points)}, 'initial_ego_state': empty}

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

@torch.jit.export
def precomputed_feature_config(self) -> Dict[str, Dict[str, str]]:
    """
        Inherited. See interface.
        """
    return {'past_ego_states': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_time_stamps': {'iteration': '0', 'num_samples': str(self.num_past_poses), 'time_horizon': str(self.past_time_horizon)}, 'past_tracked_objects': {'iteration': '0', 'time_horizon': str(self.past_time_horizon), 'num_samples': str(self.num_past_poses)}}

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

def serialize(self) -> Dict[str, Any]:
    """
        :return: Return dictionary of data that can be serialized
        """
    return dataclasses.asdict(self)

class NuBoard:
    """NuBoard application class."""

    def __init__(self, nuboard_paths: List[str], scenario_builder: AbstractScenarioBuilder, vehicle_parameters: VehicleParameters, port_number: int=5006, profiler_path: Optional[Path]=None, resource_prefix: Optional[str]=None, async_scenario_rendering: bool=True, scenario_rendering_frame_rate_cap_hz: int=60):
        """
        Nuboard main class.
        :param nuboard_paths: A list of paths to nuboard files.
        :param scenario_builder: Scenario builder instance.
        :param vehicle_parameters: vehicle parameters.
        :param port_number: Bokeh port number.
        :param profiler_path: Path to save the profiler.
        :param resource_prefix: Prefix to the resource path in HTML.
        :param async_scenario_rendering: Whether to use asynchronous scenario rendering in the scenario tab.
        :param scenario_rendering_frame_rate_cap_hz: Maximum frames to render in the scenario tab per second.
            Use lower values when running nuBoard in the cloud to prevent frame queues due to latency. The rule of thumb
            is to match the frame rate with the expected latency, e.g 5Hz for 200ms round-trip latency.
            Internally this value is capped at 60.
        """
        self._profiler_path = profiler_path
        self._nuboard_paths = check_nuboard_file_paths(nuboard_paths)
        self._scenario_builder = scenario_builder
        self._port_number = port_number
        self._vehicle_parameters = vehicle_parameters
        self._doc: Optional[Document] = None
        self._resource_prefix = resource_prefix if resource_prefix else ''
        self._resource_path = Path(__file__).parents[0] / 'resource'
        self._profiler_file_name = 'nuboard'
        self._profiler: Optional[ProfileCallback] = None
        self._async_scenario_rendering = async_scenario_rendering
        if scenario_rendering_frame_rate_cap_hz < 1 or scenario_rendering_frame_rate_cap_hz > 60:
            raise ValueError('scenario_rendering_frame_rate_cap_hz should be between 1 and 60')
        self._scenario_rendering_frame_rate_cap_hz = scenario_rendering_frame_rate_cap_hz

    def stop_handler(self, sig: Any, frame: Any) -> None:
        """Helper to handle stop signals."""
        logger.info('Stopping the Bokeh application.')
        if self._profiler:
            self._profiler.save_profiler(self._profiler_file_name)
        IOLoop.current().stop()

    def run(self) -> None:
        """Run nuBoard WebApp."""
        logger.info(f'Opening Bokeh application on http://localhost:{self._port_number}/')
        logger.info(f'Async rendering is set to: {self._async_scenario_rendering}')
        io_loop = IOLoop.current()
        if self._profiler_path is not None:
            signal.signal(signal.SIGTERM, self.stop_handler)
            signal.signal(signal.SIGINT, self.stop_handler)
            self._profiler = ProfileCallback(output_dir=self._profiler_path)
            self._profiler.start_profiler(self._profiler_file_name)
        bokeh_app = Application(FunctionHandler(self.main_page))
        server = Server({'/': bokeh_app}, io_loop=io_loop, port=self._port_number, allow_websocket_origin=['*'], extra_patterns=[('/resource/(.*)', StaticFileHandler, {'path': str(self._resource_path)})])
        server.start()
        io_loop.add_callback(server.show, '/')
        try:
            io_loop.start()
        except RuntimeError as e:
            logger.warning(f'{e}')

    def main_page(self, doc: Document) -> None:
        """
        Main nuBoard page.
        :param doc: HTML document.
        """
        self._doc = doc
        template_path = Path(os.path.dirname(os.path.realpath(__file__))) / 'templates'
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
        self._doc.template = env.get_template('index.html')
        self._doc.title = 'nuBoard'
        nuboard_files = read_nuboard_file_paths(file_paths=self._nuboard_paths)
        experiment_file_data = ExperimentFileData(file_paths=nuboard_files)
        overview_tab = OverviewTab(doc=self._doc, experiment_file_data=experiment_file_data)
        histogram_tab = HistogramTab(doc=self._doc, experiment_file_data=experiment_file_data)
        scenario_tab = ScenarioTab(experiment_file_data=experiment_file_data, scenario_builder=self._scenario_builder, doc=self._doc, vehicle_parameters=self._vehicle_parameters, async_rendering=self._async_scenario_rendering, frame_rate_cap_hz=self._scenario_rendering_frame_rate_cap_hz)
        configuration_tab = ConfigurationTab(experiment_file_data=experiment_file_data, doc=self._doc, tabs=[overview_tab, histogram_tab, scenario_tab])
        s3_tab = CloudTab(doc=self._doc, configuration_tab=configuration_tab)
        self._doc.add_root(configuration_tab.file_path_input)
        self._doc.add_root(configuration_tab.experiment_file_path_checkbox_group)
        self._doc.add_root(s3_tab.s3_bucket_name)
        self._doc.add_root(s3_tab.s3_bucket_text_input)
        self._doc.add_root(s3_tab.s3_error_text)
        self._doc.add_root(s3_tab.s3_access_key_id_text_input)
        self._doc.add_root(s3_tab.s3_secret_access_key_password_input)
        self._doc.add_root(s3_tab.s3_bucket_prefix_text_input)
        self._doc.add_root(s3_tab.s3_modal_query_btn)
        self._doc.add_root(s3_tab.s3_download_text_input)
        self._doc.add_root(s3_tab.s3_download_button)
        self._doc.add_root(s3_tab.data_table)
        self._doc.add_root(overview_tab.table)
        self._doc.add_root(overview_tab.planner_checkbox_group)
        self._doc.add_root(histogram_tab.scenario_type_multi_choice)
        self._doc.add_root(histogram_tab.metric_name_multi_choice)
        self._doc.add_root(histogram_tab.planner_checkbox_group)
        self._doc.add_root(histogram_tab.histogram_plots)
        self._doc.add_root(histogram_tab.bin_spinner)
        self._doc.add_root(histogram_tab.histogram_modal_query_btn)
        self._doc.add_root(scenario_tab.planner_checkbox_group)
        self._doc.add_root(scenario_tab.scenario_title_div)
        self._doc.add_root(scenario_tab.object_checkbox_group)
        self._doc.add_root(scenario_tab.traj_checkbox_group)
        self._doc.add_root(scenario_tab.map_checkbox_group)
        self._doc.add_root(scenario_tab.scalar_scenario_type_select)
        self._doc.add_root(scenario_tab.scalar_log_name_select)
        self._doc.add_root(scenario_tab.scalar_scenario_name_select)
        self._doc.add_root(scenario_tab.scenario_token_multi_choice)
        self._doc.add_root(scenario_tab.scenario_modal_query_btn)
        self._doc.add_root(scenario_tab.time_series_layout)
        self._doc.add_root(scenario_tab.ego_expert_states_layout)
        self._doc.add_root(scenario_tab.scenario_score_layout)
        self._doc.add_root(scenario_tab.simulation_tile_layout)

def __init__(self, nuboard_paths: List[str], scenario_builder: AbstractScenarioBuilder, vehicle_parameters: VehicleParameters, port_number: int=5006, profiler_path: Optional[Path]=None, resource_prefix: Optional[str]=None, async_scenario_rendering: bool=True, scenario_rendering_frame_rate_cap_hz: int=60):
    """
        Nuboard main class.
        :param nuboard_paths: A list of paths to nuboard files.
        :param scenario_builder: Scenario builder instance.
        :param vehicle_parameters: vehicle parameters.
        :param port_number: Bokeh port number.
        :param profiler_path: Path to save the profiler.
        :param resource_prefix: Prefix to the resource path in HTML.
        :param async_scenario_rendering: Whether to use asynchronous scenario rendering in the scenario tab.
        :param scenario_rendering_frame_rate_cap_hz: Maximum frames to render in the scenario tab per second.
            Use lower values when running nuBoard in the cloud to prevent frame queues due to latency. The rule of thumb
            is to match the frame rate with the expected latency, e.g 5Hz for 200ms round-trip latency.
            Internally this value is capped at 60.
        """
    self._profiler_path = profiler_path
    self._nuboard_paths = check_nuboard_file_paths(nuboard_paths)
    self._scenario_builder = scenario_builder
    self._port_number = port_number
    self._vehicle_parameters = vehicle_parameters
    self._doc: Optional[Document] = None
    self._resource_prefix = resource_prefix if resource_prefix else ''
    self._resource_path = Path(__file__).parents[0] / 'resource'
    self._profiler_file_name = 'nuboard'
    self._profiler: Optional[ProfileCallback] = None
    self._async_scenario_rendering = async_scenario_rendering
    if scenario_rendering_frame_rate_cap_hz < 1 or scenario_rendering_frame_rate_cap_hz > 60:
        raise ValueError('scenario_rendering_frame_rate_cap_hz should be between 1 and 60')
    self._scenario_rendering_frame_rate_cap_hz = scenario_rendering_frame_rate_cap_hz

def main_page(self, doc: Document) -> None:
    """
        Main nuBoard page.
        :param doc: HTML document.
        """
    self._doc = doc
    template_path = Path(os.path.dirname(os.path.realpath(__file__))) / 'templates'
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_path))
    self._doc.template = env.get_template('index.html')
    self._doc.title = 'nuBoard'
    nuboard_files = read_nuboard_file_paths(file_paths=self._nuboard_paths)
    experiment_file_data = ExperimentFileData(file_paths=nuboard_files)
    overview_tab = OverviewTab(doc=self._doc, experiment_file_data=experiment_file_data)
    histogram_tab = HistogramTab(doc=self._doc, experiment_file_data=experiment_file_data)
    scenario_tab = ScenarioTab(experiment_file_data=experiment_file_data, scenario_builder=self._scenario_builder, doc=self._doc, vehicle_parameters=self._vehicle_parameters, async_rendering=self._async_scenario_rendering, frame_rate_cap_hz=self._scenario_rendering_frame_rate_cap_hz)
    configuration_tab = ConfigurationTab(experiment_file_data=experiment_file_data, doc=self._doc, tabs=[overview_tab, histogram_tab, scenario_tab])
    s3_tab = CloudTab(doc=self._doc, configuration_tab=configuration_tab)
    self._doc.add_root(configuration_tab.file_path_input)
    self._doc.add_root(configuration_tab.experiment_file_path_checkbox_group)
    self._doc.add_root(s3_tab.s3_bucket_name)
    self._doc.add_root(s3_tab.s3_bucket_text_input)
    self._doc.add_root(s3_tab.s3_error_text)
    self._doc.add_root(s3_tab.s3_access_key_id_text_input)
    self._doc.add_root(s3_tab.s3_secret_access_key_password_input)
    self._doc.add_root(s3_tab.s3_bucket_prefix_text_input)
    self._doc.add_root(s3_tab.s3_modal_query_btn)
    self._doc.add_root(s3_tab.s3_download_text_input)
    self._doc.add_root(s3_tab.s3_download_button)
    self._doc.add_root(s3_tab.data_table)
    self._doc.add_root(overview_tab.table)
    self._doc.add_root(overview_tab.planner_checkbox_group)
    self._doc.add_root(histogram_tab.scenario_type_multi_choice)
    self._doc.add_root(histogram_tab.metric_name_multi_choice)
    self._doc.add_root(histogram_tab.planner_checkbox_group)
    self._doc.add_root(histogram_tab.histogram_plots)
    self._doc.add_root(histogram_tab.bin_spinner)
    self._doc.add_root(histogram_tab.histogram_modal_query_btn)
    self._doc.add_root(scenario_tab.planner_checkbox_group)
    self._doc.add_root(scenario_tab.scenario_title_div)
    self._doc.add_root(scenario_tab.object_checkbox_group)
    self._doc.add_root(scenario_tab.traj_checkbox_group)
    self._doc.add_root(scenario_tab.map_checkbox_group)
    self._doc.add_root(scenario_tab.scalar_scenario_type_select)
    self._doc.add_root(scenario_tab.scalar_log_name_select)
    self._doc.add_root(scenario_tab.scalar_scenario_name_select)
    self._doc.add_root(scenario_tab.scenario_token_multi_choice)
    self._doc.add_root(scenario_tab.scenario_modal_query_btn)
    self._doc.add_root(scenario_tab.time_series_layout)
    self._doc.add_root(scenario_tab.ego_expert_states_layout)
    self._doc.add_root(scenario_tab.scenario_score_layout)
    self._doc.add_root(scenario_tab.simulation_tile_layout)

def metric_statistics_reader(parquet_file: Path) -> MetricStatisticsDataFrame:
    """
    Reader for a metric statistic parquet file.
    :param parquet_file: Parquet file path to read.
    :return MetricStatisticsDataFrame.
    """
    data_frame = MetricStatisticsDataFrame.load_parquet(parquet_file)
    return data_frame

def metric_aggregator_reader(parquet_file: Path) -> pd.DataFrame:
    """
    Reader for a metric aggregator parquet file.
    :param parquet_file: Parquet file path to read.
    :return Pandas data frame.
    """
    data_frame = pd.read_parquet(parquet_file)
    return data_frame

def check_nuboard_file_paths(main_paths: List[str]) -> List[Path]:
    """
    Check if given file paths are valid nuBoard files.
    :param main_paths: A list of file paths.
    :return A list of available nuBoard files.
    """
    available_paths = []
    for main_path in main_paths:
        main_folder_path: Path = Path(main_path)
        if main_folder_path.is_dir():
            files = list(main_folder_path.iterdir())
            event_files = [file for file in files if file.name.endswith(NuBoardFile.extension())]
            if len(event_files) > 0:
                event_files = sorted(event_files, reverse=True)
                available_paths.append(event_files[0])
        elif main_folder_path.is_file() and main_folder_path.name.endswith(NuBoardFile.extension()):
            available_paths.append(main_folder_path)
        else:
            raise RuntimeError(f'{str(main_folder_path)} is not a valid nuBoard file')
        if len(available_paths) == 0:
            logger.info('No available nuBoard files are found.')
    return available_paths

def get_histogram_plot_x_range(unit: str, data: npt.NDArray[np.float64]) -> Union[List[str], FactorRange]:
    """
    Get Histogram x_range based on unit and data.
    :param unit: Histogram unit.
    :param data: Histogram data.
    :return x_range in histogram plot.
    """
    x_range = None
    if unit in ['bool', 'boolean']:
        x_range = ['False', 'True']
    elif unit in ['count']:
        x_range = [str(count) for count in data]
    return x_range

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

def check_s3_nuboard_files(s3_file_contents: Dict[str, S3FileContent], s3_path: str, s3_client: boto3.client) -> S3NuBoardFileResultMessage:
    """
    Return True in the message if there is a nuboard file and can load into nuBoard.
    :param s3_file_contents: S3 prefix with a dictionary of s3 file name and their contents.
    :Param s3_path: S3 Path starts with s3://.
    :param s3_client: s3 client session.
    :return S3NuBoardFileResultMessage to indicate if there is available nuboard file in the s3 prefix.
    """
    success = False
    return_message = 'No available nuboard files in the prefix'
    nuboard_file = None
    nuboard_filename = None
    if not s3_path.endswith('/'):
        s3_path = s3_path + '/'
    url = parse.urlparse(s3_path)
    for file_name, file_content in s3_file_contents.items():
        if file_name.endswith(NuBoardFile.extension()):
            try:
                nuboard_object = s3_client.get_object(Bucket=url.netloc, Key=file_name)
                file_stream = io.BytesIO(nuboard_object['Body'].read())
                nuboard_data = pickle.load(file_stream)
                nuboard_file = NuBoardFile.deserialize(nuboard_data)
                file_stream.close()
                nuboard_filename = Path(file_name).name
                return_message = f'Found available nuboard file: {nuboard_filename}'
                success = True
                break
            except Exception as e:
                logger.info(str(e))
                continue
    return S3NuBoardFileResultMessage(s3_connection_status=S3ConnectionStatus(success=success, return_message=return_message), nuboard_filename=nuboard_filename, nuboard_file=nuboard_file)

def get_s3_file_contents(s3_path: str, client: Optional[boto3.client]=None, delimiter: str='/', include_previous_folder: bool=False) -> S3FileResultMessage:
    """
    Get folders and files contents in the provided s3 path provided.
    :param s3_path: S3 path dir to expand.
    :param client: Boto3 client to use, if None create a new one.
    :param delimiter: Delimiter for path.
    :param include_previous_folder: Set True to include '..' as previous folder.
    :return: Dict of file contents.
    """
    return_message = 'Connect successfully'
    file_contents: Dict[str, S3FileContent] = {}
    try:
        client = get_s3_client() if client is None else client
        if not s3_path.endswith('/'):
            s3_path = s3_path + '/'
        url = parse.urlparse(s3_path)
        paginator = client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=url.netloc, Prefix=url.path.lstrip('/'), Delimiter=delimiter)
        previous_folder = os.path.join(url.path.lstrip('/'), '..')
        if previous_folder != '..' and include_previous_folder:
            file_contents[previous_folder] = S3FileContent(filename=previous_folder)
        for page in page_iterator:
            for obj in page.get('CommonPrefixes', []):
                file_contents[obj['Prefix']] = S3FileContent(filename=obj['Prefix'])
            for content in page.get('Contents', []):
                file_name = str(content['Key'])
                if file_name == url.path.lstrip('/'):
                    continue
                file_contents[file_name] = S3FileContent(filename=file_name, last_modified=content['LastModified'], size=content['Size'])
        success = True
    except Exception as err:
        logger.info('Error: {}'.format(err))
        return_message = f'{err}'
        success = False
    s3_connection_status = S3ConnectionStatus(return_message=return_message, success=success)
    s3_file_result_message = S3FileResultMessage(s3_connection_status=s3_connection_status, file_contents=file_contents)
    return s3_file_result_message

def download_s3_file(s3_path: str, file_content: S3FileContent, s3_client: boto3.client, save_path: str) -> S3ConnectionStatus:
    """
    Download a s3 file given a s3 full path.
    :param s3_path: S3 full path.
    :param file_content: File content info.
    :param s3_client: A connecting S3 client.
    :param save_path: Local save path.
    :return S3 connection status to indicate status of s3 connection.
    """
    return_message = f'Downloaded {s3_path}'
    try:
        if s3_path.endswith('/'):
            return S3ConnectionStatus(success=False, return_message=f'{s3_path} is not a file')
        url = parse.urlparse(s3_path)
        file_name = file_content.filename if file_content.filename is not None else ''
        download_file_name = Path(save_path, file_name)
        remote_file_size = file_content.size if file_content.size is not None else 0
        local_file_size = os.path.getsize(str(download_file_name)) if download_file_name.exists() else 0
        if not download_file_name.exists() or local_file_size != float(remote_file_size):
            s3_client.download_file(url.netloc, file_name, str(download_file_name))
        success = True
    except Exception as e:
        raise Boto3Error(e)
    return S3ConnectionStatus(success=success, return_message=return_message)

def download_s3_path(s3_path: str, s3_client: boto3.client, save_path: str, delimiter: str='/') -> S3ConnectionStatus:
    """
    Download a s3 path recursively given a s3 full path.
    :param s3_path: S3 full path.
    :param s3_client: A connecting S3 client.
    :param save_path: Local save path.
    :param delimiter: Delimiter to split folders.
    :return S3 connection status to indicate status of s3 connection.
    """
    return_message = f'Downloaded {s3_path}'
    try:
        if not s3_path.endswith('/'):
            s3_path = s3_path + '/'
        url = parse.urlparse(s3_path)
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=url.netloc, Prefix=url.path.lstrip('/'), Delimiter=delimiter)
        for page in page_iterator:
            common_prefixes = page.get('CommonPrefixes', [])
            for sub_folder in common_prefixes:
                sub_s3_path = os.path.join('s3://', url.netloc, sub_folder['Prefix'])
                local_save_sub_path = Path(save_path, sub_folder['Prefix'])
                local_save_sub_path.mkdir(parents=True, exist_ok=True)
                download_s3_path(s3_client=s3_client, s3_path=sub_s3_path, save_path=save_path)
            contents = page.get('Contents', [])
            for content in contents:
                file_name = str(content['Key'])
                file_size = content['Size']
                last_modified = content['LastModified']
                s3_file_path = os.path.join('s3://', url.netloc, file_name)
                local_folder = Path(save_path, file_name)
                local_folder.parents[0].mkdir(exist_ok=True, parents=True)
                file_content = S3FileContent(filename=file_name, size=file_size, last_modified=last_modified)
                download_s3_file(s3_path=s3_file_path, file_content=file_content, s3_client=s3_client, save_path=save_path)
        success = True
    except Exception as e:
        raise Boto3Error(e)
    s3_connection_status = S3ConnectionStatus(success=success, return_message=return_message)
    return s3_connection_status

class TestNuBoardUtils(unittest.TestCase):
    """Unit tests for utils in nuboard."""

    def setUp(self) -> None:
        """Set up a list of nuboard files."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_paths: List[str] = []
        self.nuboard_files: List[NuBoardFile] = []
        for i in range(2):
            main_path = os.path.join(self.tmp_dir.name, str(i))
            nuboard_file = NuBoardFile(simulation_main_path=main_path, metric_folder='metrics', simulation_folder='simulations', metric_main_path=main_path, aggregator_metric_folder='aggregator_metric')
            nuboard_file_name = os.path.join(main_path, 'nuboard_file' + NuBoardFile.extension())
            self.nuboard_files.append(nuboard_file)
            self.nuboard_paths.append(nuboard_file_name)

    def test_check_nuboard_file_paths(self) -> None:
        """Test if check_nuboard_file_paths works."""
        self.assertRaises(RuntimeError, check_nuboard_file_paths, self.nuboard_paths)
        for nuboard_file, nuboard_path in zip(self.nuboard_files, self.nuboard_paths):
            main_path = Path(nuboard_file.simulation_main_path)
            main_path.mkdir(parents=True, exist_ok=True)
            file = Path(nuboard_path)
            nuboard_file.save_nuboard_file(file)
        nuboard_paths = check_nuboard_file_paths(self.nuboard_paths)
        self.assertEqual(len(nuboard_paths), 2)
        self.assertIsInstance(nuboard_paths, list)
        for nuboard_path_name in nuboard_paths:
            self.assertIsInstance(nuboard_path_name, Path)
        nuboard_path_head = [os.path.dirname(nuboard_path) for nuboard_path in self.nuboard_paths]
        nuboard_paths = check_nuboard_file_paths(nuboard_path_head)
        self.assertEqual(len(nuboard_paths), 2)
        self.assertIsInstance(nuboard_paths, list)
        for nuboard_path_name in nuboard_paths:
            self.assertIsInstance(nuboard_path_name, Path)

    def test_read_nuboard_file_paths(self) -> None:
        """Test if read_nuboard_file_paths works."""
        nuboard_paths: List[Path] = []
        for nuboard_file, nuboard_path in zip(self.nuboard_files, self.nuboard_paths):
            main_path = Path(nuboard_file.simulation_main_path)
            main_path.mkdir(parents=True, exist_ok=True)
            file = Path(nuboard_path)
            nuboard_file.save_nuboard_file(file)
            nuboard_paths.append(file)
        nuboard_files = read_nuboard_file_paths(file_paths=nuboard_paths)
        self.assertEqual(len(nuboard_files), 2)
        for nuboard_file in nuboard_files:
            self.assertIsInstance(nuboard_file, NuBoardFile)

    def tearDown(self) -> None:
        """Remove and clean up the tmp folder."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a list of nuboard files."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_paths: List[str] = []
    self.nuboard_files: List[NuBoardFile] = []
    for i in range(2):
        main_path = os.path.join(self.tmp_dir.name, str(i))
        nuboard_file = NuBoardFile(simulation_main_path=main_path, metric_folder='metrics', simulation_folder='simulations', metric_main_path=main_path, aggregator_metric_folder='aggregator_metric')
        nuboard_file_name = os.path.join(main_path, 'nuboard_file' + NuBoardFile.extension())
        self.nuboard_files.append(nuboard_file)
        self.nuboard_paths.append(nuboard_file_name)

def test_check_nuboard_file_paths(self) -> None:
    """Test if check_nuboard_file_paths works."""
    self.assertRaises(RuntimeError, check_nuboard_file_paths, self.nuboard_paths)
    for nuboard_file, nuboard_path in zip(self.nuboard_files, self.nuboard_paths):
        main_path = Path(nuboard_file.simulation_main_path)
        main_path.mkdir(parents=True, exist_ok=True)
        file = Path(nuboard_path)
        nuboard_file.save_nuboard_file(file)
    nuboard_paths = check_nuboard_file_paths(self.nuboard_paths)
    self.assertEqual(len(nuboard_paths), 2)
    self.assertIsInstance(nuboard_paths, list)
    for nuboard_path_name in nuboard_paths:
        self.assertIsInstance(nuboard_path_name, Path)
    nuboard_path_head = [os.path.dirname(nuboard_path) for nuboard_path in self.nuboard_paths]
    nuboard_paths = check_nuboard_file_paths(nuboard_path_head)
    self.assertEqual(len(nuboard_paths), 2)
    self.assertIsInstance(nuboard_paths, list)
    for nuboard_path_name in nuboard_paths:
        self.assertIsInstance(nuboard_path_name, Path)

def test_read_nuboard_file_paths(self) -> None:
    """Test if read_nuboard_file_paths works."""
    nuboard_paths: List[Path] = []
    for nuboard_file, nuboard_path in zip(self.nuboard_files, self.nuboard_paths):
        main_path = Path(nuboard_file.simulation_main_path)
        main_path.mkdir(parents=True, exist_ok=True)
        file = Path(nuboard_path)
        nuboard_file.save_nuboard_file(file)
        nuboard_paths.append(file)
    nuboard_files = read_nuboard_file_paths(file_paths=nuboard_paths)
    self.assertEqual(len(nuboard_files), 2)
    for nuboard_file in nuboard_files:
        self.assertIsInstance(nuboard_file, NuBoardFile)

def tearDown(self) -> None:
    """Remove and clean up the tmp folder."""
    self.tmp_dir.cleanup()

class TestNuBoardCloudUtil(unittest.TestCase):
    """Unit tests for cloud utils in nuboard."""

    def setUp(self) -> None:
        """Set up a list of nuboard files."""
        self.tmp_dir = tempfile.TemporaryDirectory()

    def test_check_s3_nuboard_files_fail(self) -> None:
        """Test if check_s3_nuboard_files fails when there is no nuboard file."""
        s3_client = boto3.Session().client('s3')
        stubber = Stubber(s3_client)
        dummy_file_result_message = {'dummy_a': S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)), 'dummy_b': S3FileContent(filename='dummy_b', size=10, last_modified=datetime(day=3, month=8, year=1992, tzinfo=timezone.utc))}
        encoded_expected_messages = {'dummy_a': json.dumps(dummy_file_result_message['dummy_a'].serialize()).encode(), 'dummy_b': json.dumps(dummy_file_result_message['dummy_b'].serialize()).encode()}
        dummy_streaming_io_message_response = {}
        expected_params = {}
        for s3_key, result_message in dummy_file_result_message.items():
            dummy_streaming_io_message_response[s3_key] = {'Body': io.BytesIO(encoded_expected_messages[s3_key])}
            expected_params[s3_key] = {'Bucket': 'test-bucket', 'Key': s3_key}
        for s3_key, expected_param in expected_params.items():
            response = dummy_streaming_io_message_response[s3_key]
            stubber.add_response('get_object', response, expected_param)
        with stubber:
            s3_nuboard_file_result_message = check_s3_nuboard_files(s3_file_contents=dummy_file_result_message, s3_client=s3_client, s3_path='s3://test-bucket')
        self.assertIsNone(s3_nuboard_file_result_message.nuboard_file)
        self.assertFalse(s3_nuboard_file_result_message.s3_connection_status.success)

    def test_check_s3_nuboard_files_success(self) -> None:
        """Test if check_s3_nuboard_files success when there is a nuboard file."""
        s3_client = boto3.Session().client('s3')
        stubber = Stubber(s3_client)
        nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', metric_main_path=self.tmp_dir.name, aggregator_metric_folder='aggregator_metric')
        nuboard_file_name = 'dummy_a' + NuBoardFile.extension()
        dummy_file_result_message = {nuboard_file_name: S3FileContent(filename=nuboard_file_name, size=12, last_modified=datetime(day=4, month=5, year=1992, tzinfo=timezone.utc))}
        encoded_expected_messages = {nuboard_file_name: pickle.dumps(nuboard_file.serialize())}
        dummy_streaming_io_message_response = {}
        expected_params = {}
        for s3_key, result_message in dummy_file_result_message.items():
            dummy_streaming_io_message_response[s3_key] = {'Body': io.BytesIO(encoded_expected_messages[s3_key])}
            expected_params[s3_key] = {'Bucket': 'test-bucket', 'Key': s3_key}
        for s3_key, expected_param in expected_params.items():
            response = dummy_streaming_io_message_response[s3_key]
            stubber.add_response('get_object', response, expected_param)
        with stubber:
            s3_nuboard_file_result_message = check_s3_nuboard_files(s3_file_contents=dummy_file_result_message, s3_client=s3_client, s3_path='s3://test-bucket')
        self.assertTrue(s3_nuboard_file_result_message.s3_connection_status.success)
        self.assertIsNotNone(s3_nuboard_file_result_message.nuboard_file)
        self.assertEqual(nuboard_file.simulation_main_path, s3_nuboard_file_result_message.nuboard_file.simulation_main_path)
        self.assertEqual(nuboard_file.metric_main_path, s3_nuboard_file_result_message.nuboard_file.metric_main_path)

    def test_get_s3_file_content(self) -> None:
        """Test if download_s3_file works."""
        s3_client = boto3.Session().client('s3')
        stubber = Stubber(s3_client)
        expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
        expected_params = {'Bucket': 'test-bucket', 'Prefix': '', 'Delimiter': '/'}
        s3_path = 's3://test-bucket'
        stubber.add_response('list_objects_v2', expected_response, expected_params)
        with stubber:
            s3_file_contents = get_s3_file_contents(s3_path=s3_path, client=s3_client, include_previous_folder=True)
            self.assertTrue(s3_file_contents.s3_connection_status.success)
            expected_file_names = ['dummy_folder_a/log.txt', 'dummy_folder_b/log_2.txt', 'dummy_a', 'dummy_b']
            for index, (file_name, _) in enumerate(s3_file_contents.file_contents.items()):
                self.assertEqual(file_name, expected_file_names[index])

    def test_s3_download_file(self) -> None:
        """Test s3_download_file in utils."""
        s3_client = boto3.Session().client('s3')
        dummy_s3_file_content = S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc))
        s3_path = 's3://test-bucket'
        save_path = self.tmp_dir.name
        with self.assertRaises(Boto3Error):
            download_s3_file(s3_path=s3_path, s3_client=s3_client, save_path=save_path, file_content=dummy_s3_file_content)

    def test_s3_download_path(self) -> None:
        """Test s3_download_path in utils."""
        s3_client = boto3.Session().client('s3')
        stubber = Stubber(s3_client)
        expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
        expected_params = {'Bucket': 'test-bucket', 'Prefix': '', 'Delimiter': '/'}
        s3_path = 's3://test-bucket'
        stubber.add_response('list_objects_v2', expected_response, expected_params)
        save_path = self.tmp_dir.name
        with stubber:
            with self.assertRaises(Boto3Error):
                download_s3_path(s3_path=s3_path, s3_client=s3_client, save_path=save_path)

    def tearDown(self) -> None:
        """Remove and clean up the tmp folder."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a list of nuboard files."""
    self.tmp_dir = tempfile.TemporaryDirectory()

def test_check_s3_nuboard_files_fail(self) -> None:
    """Test if check_s3_nuboard_files fails when there is no nuboard file."""
    s3_client = boto3.Session().client('s3')
    stubber = Stubber(s3_client)
    dummy_file_result_message = {'dummy_a': S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)), 'dummy_b': S3FileContent(filename='dummy_b', size=10, last_modified=datetime(day=3, month=8, year=1992, tzinfo=timezone.utc))}
    encoded_expected_messages = {'dummy_a': json.dumps(dummy_file_result_message['dummy_a'].serialize()).encode(), 'dummy_b': json.dumps(dummy_file_result_message['dummy_b'].serialize()).encode()}
    dummy_streaming_io_message_response = {}
    expected_params = {}
    for s3_key, result_message in dummy_file_result_message.items():
        dummy_streaming_io_message_response[s3_key] = {'Body': io.BytesIO(encoded_expected_messages[s3_key])}
        expected_params[s3_key] = {'Bucket': 'test-bucket', 'Key': s3_key}
    for s3_key, expected_param in expected_params.items():
        response = dummy_streaming_io_message_response[s3_key]
        stubber.add_response('get_object', response, expected_param)
    with stubber:
        s3_nuboard_file_result_message = check_s3_nuboard_files(s3_file_contents=dummy_file_result_message, s3_client=s3_client, s3_path='s3://test-bucket')
    self.assertIsNone(s3_nuboard_file_result_message.nuboard_file)
    self.assertFalse(s3_nuboard_file_result_message.s3_connection_status.success)

def test_check_s3_nuboard_files_success(self) -> None:
    """Test if check_s3_nuboard_files success when there is a nuboard file."""
    s3_client = boto3.Session().client('s3')
    stubber = Stubber(s3_client)
    nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', metric_main_path=self.tmp_dir.name, aggregator_metric_folder='aggregator_metric')
    nuboard_file_name = 'dummy_a' + NuBoardFile.extension()
    dummy_file_result_message = {nuboard_file_name: S3FileContent(filename=nuboard_file_name, size=12, last_modified=datetime(day=4, month=5, year=1992, tzinfo=timezone.utc))}
    encoded_expected_messages = {nuboard_file_name: pickle.dumps(nuboard_file.serialize())}
    dummy_streaming_io_message_response = {}
    expected_params = {}
    for s3_key, result_message in dummy_file_result_message.items():
        dummy_streaming_io_message_response[s3_key] = {'Body': io.BytesIO(encoded_expected_messages[s3_key])}
        expected_params[s3_key] = {'Bucket': 'test-bucket', 'Key': s3_key}
    for s3_key, expected_param in expected_params.items():
        response = dummy_streaming_io_message_response[s3_key]
        stubber.add_response('get_object', response, expected_param)
    with stubber:
        s3_nuboard_file_result_message = check_s3_nuboard_files(s3_file_contents=dummy_file_result_message, s3_client=s3_client, s3_path='s3://test-bucket')
    self.assertTrue(s3_nuboard_file_result_message.s3_connection_status.success)
    self.assertIsNotNone(s3_nuboard_file_result_message.nuboard_file)
    self.assertEqual(nuboard_file.simulation_main_path, s3_nuboard_file_result_message.nuboard_file.simulation_main_path)
    self.assertEqual(nuboard_file.metric_main_path, s3_nuboard_file_result_message.nuboard_file.metric_main_path)

def test_get_s3_file_content(self) -> None:
    """Test if download_s3_file works."""
    s3_client = boto3.Session().client('s3')
    stubber = Stubber(s3_client)
    expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
    expected_params = {'Bucket': 'test-bucket', 'Prefix': '', 'Delimiter': '/'}
    s3_path = 's3://test-bucket'
    stubber.add_response('list_objects_v2', expected_response, expected_params)
    with stubber:
        s3_file_contents = get_s3_file_contents(s3_path=s3_path, client=s3_client, include_previous_folder=True)
        self.assertTrue(s3_file_contents.s3_connection_status.success)
        expected_file_names = ['dummy_folder_a/log.txt', 'dummy_folder_b/log_2.txt', 'dummy_a', 'dummy_b']
        for index, (file_name, _) in enumerate(s3_file_contents.file_contents.items()):
            self.assertEqual(file_name, expected_file_names[index])

def test_s3_download_file(self) -> None:
    """Test s3_download_file in utils."""
    s3_client = boto3.Session().client('s3')
    dummy_s3_file_content = S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc))
    s3_path = 's3://test-bucket'
    save_path = self.tmp_dir.name
    with self.assertRaises(Boto3Error):
        download_s3_file(s3_path=s3_path, s3_client=s3_client, save_path=save_path, file_content=dummy_s3_file_content)

def test_s3_download_path(self) -> None:
    """Test s3_download_path in utils."""
    s3_client = boto3.Session().client('s3')
    stubber = Stubber(s3_client)
    expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
    expected_params = {'Bucket': 'test-bucket', 'Prefix': '', 'Delimiter': '/'}
    s3_path = 's3://test-bucket'
    stubber.add_response('list_objects_v2', expected_response, expected_params)
    save_path = self.tmp_dir.name
    with stubber:
        with self.assertRaises(Boto3Error):
            download_s3_path(s3_path=s3_path, s3_client=s3_client, save_path=save_path)

def tearDown(self) -> None:
    """Remove and clean up the tmp folder."""
    self.tmp_dir.cleanup()

@dataclass
class ExperimentFileData:
    """Data for experiment files."""
    file_paths: List[NuBoardFile]
    color_palettes: List[str] = field(default_factory=list)
    expert_color_palettes: List[str] = field(default_factory=list)
    available_metric_statistics_names: List[str] = field(default_factory=list)
    metric_statistics_dataframes: List[List[MetricStatisticsDataFrame]] = field(default_factory=list)
    metric_aggregator_dataframes: List[Dict[str, pd.DataFrame]] = field(default_factory=list)
    simulation_files: Dict[str, Any] = field(default_factory=dict)
    simulation_scenario_keys: List[SimulationScenarioKey] = field(default_factory=list)
    available_scenario_types: List[str] = field(default_factory=list)
    available_scenarios: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    available_scenario_tokens: Dict[str, ScenarioTokenInfo] = field(default_factory=dict)
    file_path_colors: Dict[int, Dict[str, str]] = field(default_factory=dict)
    color_index: int = 0

    def __post_init__(self) -> None:
        """Post initialization."""
        if not self.simulation_files:
            self.simulation_files = defaultdict(set)
        if not self.available_scenario_tokens:
            self.available_scenario_tokens = defaultdict()
        if not self.color_palettes:
            self.color_palettes = Set1[9] + Set2[8] + Set3[12]
        if not self.expert_color_palettes:
            self.expert_color_palettes = Pastel2[8] + Pastel1[9] + Dark2[8]
        if not self.available_scenarios:
            self.available_scenarios = defaultdict(lambda: defaultdict(list))
        if self.file_paths:
            file_paths = self.file_paths
            self.file_paths = []
            self.update_data(file_paths=file_paths)

    def update_data(self, file_paths: List[NuBoardFile]) -> None:
        """
        Update experiment data with a new list of nuboard file paths.
        :param file_paths: A list of new nuboard file paths.
        """
        starting_file_path_index = len(self.file_paths)
        self._update_file_path_color(file_paths=file_paths, starting_file_path_index=starting_file_path_index)
        self._add_metric_files(file_paths=file_paths, starting_file_path_index=starting_file_path_index)
        self._add_metric_aggregator_files(file_paths=file_paths, starting_file_path_index=starting_file_path_index)
        self._add_simulation_files(file_paths=file_paths, starting_file_path_index=starting_file_path_index)
        self.file_paths += file_paths

    @staticmethod
    def _get_base_path(current_path: Path, base_path: Path, sub_folder: str) -> Path:
        """
        Get valid base path.
        :param current_path: Current nuboard file path.
        :Param base_path: Alternative base path.
        :param sub_folder: Sub folder.
        :return A base path.
        """
        default_path = base_path / sub_folder
        if current_path is None:
            return default_path
        base_folder = current_path / sub_folder
        if not base_folder.exists():
            base_folder = default_path
        return base_folder

    def _update_file_path_color(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
        """
        Update file path colors.
        :param file_paths: A list of new nuboard file paths.
        :param starting_file_path_index: Starting file path index.
        """
        for index, file_path in enumerate(file_paths):
            file_path_index = starting_file_path_index + index
            self.file_path_colors[file_path_index] = defaultdict(str)
            metric_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.metric_folder)
            planner_names: List[str] = []
            if not metric_path.exists():
                continue
            for file in metric_path.iterdir():
                try:
                    data_frame = MetricStatisticsDataFrame.load_parquet(file)
                    planner_names += data_frame.planner_names
                except (FileNotFoundError, Exception) as e:
                    logger.info(e)
                    pass
            if not planner_names:
                simulation_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.simulation_main_path), sub_folder=file_path.simulation_folder)
                if not simulation_path.exists():
                    continue
                planner_name_paths = simulation_path.iterdir()
                for planner_name_path in planner_name_paths:
                    planner_name = planner_name_path.name
                    planner_names.append(planner_name)
            planner_names = list(set(planner_names))
            for planner_name in planner_names:
                self.file_path_colors[file_path_index][planner_name] = self.color_palettes[self.color_index]
                self.color_index += 1

    def _add_metric_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
        """
        Add and load metric files.
        Folder hierarchy: planner_name -> scenario_type -> metric result name -> scenario_name.pkl
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
        for index, file_path in enumerate(file_paths):
            file_path_index = starting_file_path_index + index
            self.metric_statistics_dataframes.append([])
            metric_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.metric_folder)
            if not metric_path.exists():
                continue
            for file in metric_path.iterdir():
                if file.is_dir():
                    continue
                try:
                    data_frame = MetricStatisticsDataFrame.load_parquet(file)
                    self.metric_statistics_dataframes[file_path_index].append(data_frame)
                    self.available_metric_statistics_names.append(data_frame.metric_statistic_name)
                except (FileNotFoundError, Exception):
                    pass
        self.available_metric_statistics_names = sorted(list(set(self.available_metric_statistics_names)), reverse=False)

    def _add_metric_aggregator_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
        """
        Load metric aggregator files.
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
        for index, file_path in enumerate(file_paths):
            file_path_index = starting_file_path_index + index
            self.metric_aggregator_dataframes.append({})
            metric_aggregator_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.aggregator_metric_folder)
            if not metric_aggregator_path.exists():
                continue
            for file in metric_aggregator_path.iterdir():
                if file.is_dir():
                    continue
                try:
                    data_frame = pd.read_parquet(file)
                    self.metric_aggregator_dataframes[file_path_index][file.stem] = data_frame
                except (FileNotFoundError, Exception):
                    pass

    def _add_simulation_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
        """
        Load simulation files.
        Folder hierarchy: planner_name -> scenario_type -> scenario_names -> iteration.pkl.
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
        for index, file_path in enumerate(file_paths):
            if file_path.simulation_folder is None:
                continue
            file_path_index = starting_file_path_index + index
            simulation_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.simulation_main_path), sub_folder=file_path.simulation_folder)
            if not simulation_path.exists():
                continue
            planner_name_paths = simulation_path.iterdir()
            for planner_name_path in planner_name_paths:
                planner_name = planner_name_path.name
                scenario_type_paths = planner_name_path.iterdir()
                for scenario_type_path in scenario_type_paths:
                    log_name_paths = scenario_type_path.iterdir()
                    scenario_type = scenario_type_path.name
                    for log_name_path in log_name_paths:
                        scenario_name_paths = log_name_path.iterdir()
                        log_name = log_name_path.name
                        for scenario_name_path in scenario_name_paths:
                            scenario_name = scenario_name_path.name
                            scenario_key = f'{simulation_path.parents[0].name}/{planner_name}/{scenario_type}/{log_name}/{scenario_name}'
                            if scenario_key in self.simulation_files:
                                continue
                            files = scenario_name_path.iterdir()
                            for file in files:
                                self.simulation_files[scenario_key].add(file)
                            self.available_scenarios[scenario_type][log_name].append(scenario_name)
                            self.available_scenario_tokens[scenario_name] = ScenarioTokenInfo(scenario_name=scenario_name, scenario_token=scenario_name, scenario_type=scenario_type, log_name=log_name)
                            self.simulation_scenario_keys.append(SimulationScenarioKey(nuboard_file_index=file_path_index, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name, files=list(self.simulation_files[scenario_key])))
        available_scenario_types = list(set(self.available_scenarios.keys()))
        self.available_scenario_types = sorted(available_scenario_types, reverse=False)

@staticmethod
def _get_base_path(current_path: Path, base_path: Path, sub_folder: str) -> Path:
    """
        Get valid base path.
        :param current_path: Current nuboard file path.
        :Param base_path: Alternative base path.
        :param sub_folder: Sub folder.
        :return A base path.
        """
    default_path = base_path / sub_folder
    if current_path is None:
        return default_path
    base_folder = current_path / sub_folder
    if not base_folder.exists():
        base_folder = default_path
    return base_folder

def _update_file_path_color(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
    """
        Update file path colors.
        :param file_paths: A list of new nuboard file paths.
        :param starting_file_path_index: Starting file path index.
        """
    for index, file_path in enumerate(file_paths):
        file_path_index = starting_file_path_index + index
        self.file_path_colors[file_path_index] = defaultdict(str)
        metric_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.metric_folder)
        planner_names: List[str] = []
        if not metric_path.exists():
            continue
        for file in metric_path.iterdir():
            try:
                data_frame = MetricStatisticsDataFrame.load_parquet(file)
                planner_names += data_frame.planner_names
            except (FileNotFoundError, Exception) as e:
                logger.info(e)
                pass
        if not planner_names:
            simulation_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.simulation_main_path), sub_folder=file_path.simulation_folder)
            if not simulation_path.exists():
                continue
            planner_name_paths = simulation_path.iterdir()
            for planner_name_path in planner_name_paths:
                planner_name = planner_name_path.name
                planner_names.append(planner_name)
        planner_names = list(set(planner_names))
        for planner_name in planner_names:
            self.file_path_colors[file_path_index][planner_name] = self.color_palettes[self.color_index]
            self.color_index += 1

def _add_metric_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
    """
        Add and load metric files.
        Folder hierarchy: planner_name -> scenario_type -> metric result name -> scenario_name.pkl
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
    for index, file_path in enumerate(file_paths):
        file_path_index = starting_file_path_index + index
        self.metric_statistics_dataframes.append([])
        metric_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.metric_folder)
        if not metric_path.exists():
            continue
        for file in metric_path.iterdir():
            if file.is_dir():
                continue
            try:
                data_frame = MetricStatisticsDataFrame.load_parquet(file)
                self.metric_statistics_dataframes[file_path_index].append(data_frame)
                self.available_metric_statistics_names.append(data_frame.metric_statistic_name)
            except (FileNotFoundError, Exception):
                pass
    self.available_metric_statistics_names = sorted(list(set(self.available_metric_statistics_names)), reverse=False)

def _add_metric_aggregator_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
    """
        Load metric aggregator files.
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
    for index, file_path in enumerate(file_paths):
        file_path_index = starting_file_path_index + index
        self.metric_aggregator_dataframes.append({})
        metric_aggregator_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.metric_main_path), sub_folder=file_path.aggregator_metric_folder)
        if not metric_aggregator_path.exists():
            continue
        for file in metric_aggregator_path.iterdir():
            if file.is_dir():
                continue
            try:
                data_frame = pd.read_parquet(file)
                self.metric_aggregator_dataframes[file_path_index][file.stem] = data_frame
            except (FileNotFoundError, Exception):
                pass

def _add_simulation_files(self, file_paths: List[NuBoardFile], starting_file_path_index: int) -> None:
    """
        Load simulation files.
        Folder hierarchy: planner_name -> scenario_type -> scenario_names -> iteration.pkl.
        :param file_paths: A list of new nuboard files.
        :param starting_file_path_index: Starting file path index.
        """
    for index, file_path in enumerate(file_paths):
        if file_path.simulation_folder is None:
            continue
        file_path_index = starting_file_path_index + index
        simulation_path = self._get_base_path(current_path=file_path.current_path, base_path=Path(file_path.simulation_main_path), sub_folder=file_path.simulation_folder)
        if not simulation_path.exists():
            continue
        planner_name_paths = simulation_path.iterdir()
        for planner_name_path in planner_name_paths:
            planner_name = planner_name_path.name
            scenario_type_paths = planner_name_path.iterdir()
            for scenario_type_path in scenario_type_paths:
                log_name_paths = scenario_type_path.iterdir()
                scenario_type = scenario_type_path.name
                for log_name_path in log_name_paths:
                    scenario_name_paths = log_name_path.iterdir()
                    log_name = log_name_path.name
                    for scenario_name_path in scenario_name_paths:
                        scenario_name = scenario_name_path.name
                        scenario_key = f'{simulation_path.parents[0].name}/{planner_name}/{scenario_type}/{log_name}/{scenario_name}'
                        if scenario_key in self.simulation_files:
                            continue
                        files = scenario_name_path.iterdir()
                        for file in files:
                            self.simulation_files[scenario_key].add(file)
                        self.available_scenarios[scenario_type][log_name].append(scenario_name)
                        self.available_scenario_tokens[scenario_name] = ScenarioTokenInfo(scenario_name=scenario_name, scenario_token=scenario_name, scenario_type=scenario_type, log_name=log_name)
                        self.simulation_scenario_keys.append(SimulationScenarioKey(nuboard_file_index=file_path_index, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name, files=list(self.simulation_files[scenario_key])))
    available_scenario_types = list(set(self.available_scenarios.keys()))
    self.available_scenario_types = sorted(available_scenario_types, reverse=False)

@dataclass
class BaseScenarioPlot(abc.ABC):
    """Base class for scenario plot classes."""
    data_source_condition: Optional[threading.Condition] = field(default=None, init=False)
    render_event: Optional[threading.Event] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize threading properties."""
        if not self.data_source_condition:
            self.data_source_condition = threading.Condition(threading.Lock())
        if not self.render_event:
            self.render_event = threading.Event()

def __post_init__(self) -> None:
    """Initialize threading properties."""
    if not self.data_source_condition:
        self.data_source_condition = threading.Condition(threading.Lock())
    if not self.render_event:
        self.render_event = threading.Event()

def _load_data(file_name: pathlib.Path, serialization_type: str) -> Any:
    """
    Load data from file_name
    :param file_name: the name of a file which we want to deserialize
    :param serialization_type: type of serialization of the file
    :return: deserialized type
    """
    if serialization_type == 'json':
        with open(str(file_name), 'r') as f:
            return json.load(f)
    elif serialization_type == 'msgpack':
        with lzma.open(str(file_name), 'rb') as f:
            return msgpack.unpackb(f.read())
    elif serialization_type == 'pickle':
        with lzma.open(str(file_name), 'rb') as f:
            return pickle.load(f)
    else:
        raise ValueError(f'Unknown serialization type: {serialization_type}!')

class BaseTab:
    """Base tab for other tabs."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData):
        """
        Base tabs for common properties.
        Metric board to render metrics.
        :doc: A bokeh HTML document.
        :param experiment_file_data: Experiment file data.
        """
        self._doc = doc
        self._experiment_file_data: ExperimentFileData = experiment_file_data
        self._simulation_scenario_keys: List[SimulationScenarioKey] = []
        self._experiment_file_active_index: List[int] = []
        self.scatter_signs = ['circle', 'diamond', 'plus', 'square', 'triangle', 'inverted_triangle', 'star', 'asterisk', 'dot_circle', 'diamond_cross']
        self.search_criteria_selection_size = base_tab_style['search_criteria_sizes']
        self.plot_sizes = base_tab_style['plot_sizes']
        self.simulation_figure_sizes = simulation_tile_style['figure_sizes']
        self.plot_frame_sizes = base_tab_style['plot_frame_sizes']
        self.window_width = 0
        self.window_height = 0
        self.planner_checkbox_group = CheckboxGroup(labels=[], active=[], inline=True, css_classes=['planner-checkbox-group'], sizing_mode='scale_both')
        self.planner_checkbox_group.on_click(self._click_planner_checkbox_group)

    def file_paths_on_change(self, experiment_file_data: ExperimentFileData, experiment_file_active_index: List[int]) -> None:
        """
        Interface to update layout when file_paths is changed.
        :param experiment_file_data: Experiment file data.
        :param experiment_file_active_index: Active indexes for experiment files.
        """
        raise NotImplementedError

    def _click_planner_checkbox_group(self, attr: Any) -> None:
        """
        Click event handler for planner_checkbox_group.
        :param attr: Clicked attributes.
        """
        raise NotImplementedError

    @property
    def experiment_file_data(self) -> ExperimentFileData:
        """Return experiment file data."""
        return self._experiment_file_data

    @experiment_file_data.setter
    def experiment_file_data(self, experiment_file_data: ExperimentFileData) -> None:
        """
        Update experiment file data.
        :param experiment_file_data: New experiment file data.
        """
        self._experiment_file_data = experiment_file_data

    @property
    def enable_planner_names(self) -> List[str]:
        """Return a list of enable planner names."""
        enable_planner_names = [self.planner_checkbox_group.labels[index] for index in self.planner_checkbox_group.active]
        return enable_planner_names

    def get_plot_cols(self, plot_width: int, default_col_width: int=1024, offset_width: int=0, default_ncols: int=0) -> int:
        """
        Return number of columns for a grid plot.
        :param plot_width: Plot width.
        :param default_col_width: The number of columns would be 1 if window width is lower than this value.
        :param offset_width: Additional offset width.
        :param default_ncols: Default number of columns.
        :return: Get a number of columns for a grid plot.
        """
        if default_ncols and (not self.window_width):
            return default_ncols
        window_width = self.window_width - offset_width
        if window_width <= default_col_width:
            return 1
        col_num = 1 + round((window_width - default_col_width) / plot_width)
        return col_num

    def get_scatter_sign(self, index: int) -> str:
        """
        Get scatter index sign based on the index.
        :param index: Index for the scatter sign.
        :return A scatter sign name.
        """
        index = index % len(self.scatter_signs)
        return self.scatter_signs[index]

    @staticmethod
    def get_scatter_render_func(scatter_sign: str, scatter_figure: Figure) -> Any:
        """
        Render a scatter plot.
        :param scatter_sign: Scatter sign.
        :param scatter_figure: Scatter figure.
        :return A scatter render function.
        """
        if scatter_sign == 'circle':
            renderer = scatter_figure.circle
        elif scatter_sign == 'diamond':
            renderer = scatter_figure.diamond
        elif scatter_sign == 'plus':
            renderer = scatter_figure.plus
        elif scatter_sign == 'square':
            renderer = scatter_figure.square
        elif scatter_sign == 'triangle':
            renderer = scatter_figure.triangle
        elif scatter_sign == 'inverted_triangle':
            renderer = scatter_figure.inverted_triangle
        elif scatter_sign == 'star':
            renderer = scatter_figure.star
        elif scatter_sign == 'asterisk':
            renderer = scatter_figure.asterisk
        elif scatter_sign == 'diamond_cross':
            renderer = scatter_figure.diamond_cross
        else:
            raise NotImplementedError(f'{scatter_sign} is not a valid option for scatter plots!')
        return renderer

    def get_file_path_last_name(self, index: int) -> str:
        """
        Get last name of a file path.
        :param index: Index for the file path.
        :return: A file path string name.
        """
        file_path = self._experiment_file_data.file_paths[index]
        default_experiment_file_path_stem = pathlib.Path(file_path.metric_main_path)
        if file_path.current_path is None:
            return str(default_experiment_file_path_stem.name)
        metric_path = pathlib.Path(file_path.current_path, file_path.metric_folder)
        if metric_path.exists():
            experiment_file_path_stem = file_path.current_path
        else:
            experiment_file_path_stem = default_experiment_file_path_stem
        return str(experiment_file_path_stem.name)

    def load_log_name(self, scenario_type: str) -> List[str]:
        """
        Load a list of log names based on the scenario type.
        :param scenario_type: A selected scenario type.
        :return a list of log names.
        """
        log_names = self._experiment_file_data.available_scenarios.get(scenario_type, [])
        sorted_log_names: List[str] = sorted(list(set(log_names)), reverse=False)
        return sorted_log_names

    def load_scenario_names(self, scenario_type: str, log_name: str) -> List[str]:
        """
        Load a list of scenario names based on the log name.
        :param scenario_type: A selected scenario type.
        :param log_name: A selected log name.
        :return a list of scenario names.
        """
        log_dict = self._experiment_file_data.available_scenarios.get(scenario_type, [])
        if not log_dict:
            return []
        scenario_names = log_dict.get(log_name, [])
        sorted_scenario_names: List[str] = sorted(list(set(scenario_names)), reverse=False)
        return sorted_scenario_names

    def _init_multi_search_criteria_selection(self, scenario_type_multi_choice: MultiChoice, metric_name_multi_choice: MultiChoice) -> None:
        """
        Init histogram and scenario selection options.
        :param scenario_type_multi_choice: Scenario type multi choice.
        :param metric_name_multi_choice: Metric type multi choice.
        """
        scenario_type_multi_choice.options = ['all'] + sorted(self.experiment_file_data.available_scenario_types)
        metric_name_multi_choice.options = sorted(self.experiment_file_data.available_metric_statistics_names)

    def search_metric_statistics_dataframe(self, scenario_types: Optional[List[str]]=None, metric_choices: Optional[List[str]]=None) -> List[SelectedMetricStatisticDataFrame]:
        """
        Search metric statistics dataframe based on scenario types and metric choices.
        :param scenario_types: A list of scenario types.
        :param metric_choices: A list of metric choices.
        :return: A list of selected metric statistic dataframe.
        """
        data: List[SelectedMetricStatisticDataFrame] = []
        if not scenario_types and (not metric_choices):
            return data
        for index, metric_statistics_dataframes in enumerate(self.experiment_file_data.metric_statistics_dataframes):
            for metric_statistics_dataframe in metric_statistics_dataframes:
                if metric_choices and metric_statistics_dataframe.metric_statistic_name not in metric_choices:
                    continue
                data.append(SelectedMetricStatisticDataFrame(dataframe_index=index, dataframe=metric_statistics_dataframe))
        return data

def get_file_path_last_name(self, index: int) -> str:
    """
        Get last name of a file path.
        :param index: Index for the file path.
        :return: A file path string name.
        """
    file_path = self._experiment_file_data.file_paths[index]
    default_experiment_file_path_stem = pathlib.Path(file_path.metric_main_path)
    if file_path.current_path is None:
        return str(default_experiment_file_path_stem.name)
    metric_path = pathlib.Path(file_path.current_path, file_path.metric_folder)
    if metric_path.exists():
        experiment_file_path_stem = file_path.current_path
    else:
        experiment_file_path_stem = default_experiment_file_path_stem
    return str(experiment_file_path_stem.name)

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

class TestSimulationTile(unittest.TestCase):
    """Test simulation_tile functionality."""

    def set_up_simulation_log(self, output_path: Path) -> None:
        """
        Create a simulation log and save it to disk.
        :param output path: to write the simulation log to.
        """
        simulation_log = create_sample_simulation_log(output_path)
        simulation_log.save_to_file()

    def setUp(self) -> None:
        """Set up simulation tile with nuboard file."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vehicle_parameters = get_pacifica_parameters()
        simulation_log_path = Path(self.tmp_dir.name) / 'test_simulation_tile_simulation_log.msgpack.xz'
        self.set_up_simulation_log(simulation_log_path)
        nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulation', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        self.scenario_keys = [SimulationScenarioKey(nuboard_file_index=0, log_name='dummy_log', planner_name='SimplePlanner', scenario_type='common', scenario_name='test', files=[simulation_log_path])]
        self.doc = Document()
        self.map_factory = MockMapFactory()
        self.experiment_file_data = ExperimentFileData(file_paths=[nuboard_file])
        self.simulation_tile = SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)

    @given(frame_rate_cap=st.integers(min_value=1, max_value=60))
    def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests valid frame rate cap range."""
        SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    @given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
    def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests invalid frame rate cap range."""
        with self.assertRaises(ValueError):
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data, frame_rate_cap_hz=frame_rate_cap)

    def test_simulation_tile_layout(self) -> None:
        """Test layout design."""
        layout = self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        self.assertEqual(len(layout), 1)

    def test_periodic_callback(self) -> None:
        """Tests that _periodic_callback is registered correctly to the bokeh Document."""
        with patch.object(SimulationTile, '_periodic_callback', autospec=True) as mock_periodic_callback:
            SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)
            for cb in self.doc.callbacks.session_callbacks:
                cb.callback()
            self.assertEqual(mock_periodic_callback.call_count, 1)

    def _trigger_button_click_event(self, figure_index: int, button_name: str) -> None:
        """
        Trigger a bokeh.model.Button click event.
        :param figure_index: The index of the SimulationTile figure.
        :param button_name: The name of SimulationTile button.
        """
        button = getattr(self.simulation_tile.figures[figure_index], button_name)
        button._trigger_event(ButtonClick(button))

    def _test_frame_index_request_button(self, button_name: str, frame_index_request: FrameIndexRequest) -> None:
        """
        Helper function to test that frame index request buttons (first, prev, next, last) work correctly.
        :param click_callback_name: Button click callback function name in SimulationTile that's registered to bokeh.
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_index_request: FrameIndexRequest object representing the frame index requested.
        """
        with patch.object(self.simulation_tile, '_render_plots'):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            if frame_index_request == FrameIndexRequest.FIRST or frame_index_request == FrameIndexRequest.LAST:
                self._trigger_button_click_event(figure_index, button_name)
                frame_index = len(figure.simulation_history) - 1 if frame_index_request == FrameIndexRequest.LAST else 0
                self.assertEqual(figure.slider.value, frame_index)
            elif frame_index_request == FrameIndexRequest.NEXT:
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index + 1)
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)
            elif frame_index_request == FrameIndexRequest.PREV:
                self.simulation_tile._current_frame_index = len(figure.simulation_history.data) - 1
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index - 1)
                self.simulation_tile._current_frame_index = 0
                self._trigger_button_click_event(figure_index, button_name)
                self.assertEqual(figure.slider.value, self.simulation_tile._current_frame_index)

    def test_first_frame_button(self) -> None:
        """Tests that go to first frame button works correctly."""
        self._test_frame_index_request_button(button_name='first_button', frame_index_request=FrameIndexRequest.FIRST)

    def test_last_frame_button(self) -> None:
        """Tests that go to last frame button works correctly."""
        self._test_frame_index_request_button(button_name='last_button', frame_index_request=FrameIndexRequest.LAST)

    def _test_symbolic_frame_request_callback_called(self, button_name: str, frame_request_callback_name: str) -> None:
        """
        Helper function to test that the provided symbolic frame request (previous, next, play/stop) callback is called when a button is clicked
        :param button_name: The name of the button in the SimulationTile class.
        :param frame_request_callback_name: Frame request callback function name in SimulationTile that's supposed to be called.
        """
        with patch.object(self.simulation_tile, frame_request_callback_name, autospec=True) as mock_request_frame:
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            button = getattr(self.simulation_tile.figures[figure_index], button_name)
            button._trigger_event(ButtonClick(button))
            mock_request_frame.assert_called_once_with(self.simulation_tile.figures[figure_index])

    def test_prev_button(self) -> None:
        """Tests that show prev frame button works correctly."""
        self._test_frame_index_request_button(button_name='prev_button', frame_index_request=FrameIndexRequest.PREV)

    def test_next_button(self) -> None:
        """Tests that show next frame button works correctly."""
        self._test_frame_index_request_button(button_name='next_button', frame_index_request=FrameIndexRequest.NEXT)

    def test_play_button(self) -> None:
        """Tests that the play button works correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        button_name = 'play_button'
        self.assertFalse(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertTrue(self.simulation_tile.is_in_playback)
        self._trigger_button_click_event(figure_index, button_name)
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_playback_callback(self) -> None:
        """Tests that the playback callback is registered correctly to the bokeh Document & behaves correctly."""
        self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
        figure_index = 0
        figure = self.simulation_tile.figures[figure_index]
        button_name = 'play_button'
        previous_request_index = figure.slider.value
        self._trigger_button_click_event(figure_index, button_name)
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertTrue(self.simulation_tile.is_in_playback)
        self.assertTrue(figure.slider.value, previous_request_index + 1)
        self.simulation_tile._current_frame_index = len(figure.simulation_history) - 1
        for cb in self.doc.callbacks.session_callbacks:
            cb.callback()
        self.assertFalse(self.simulation_tile.is_in_playback)

    def test_deferred_plot_rendering(self) -> None:
        """Tests that plot rendering request will be deferred if successive requests are triggered faster than the frame rate cap configured."""
        self.assertIsNone(self.simulation_tile._plot_render_queue)
        with patch.object(self.simulation_tile, '_last_frame_time', new=time.time()):
            self.simulation_tile.render_simulation_tiles(selected_scenario_keys=self.scenario_keys, figure_sizes=[550, 550])
            figure_index = 0
            figure = self.simulation_tile.figures[figure_index]
            trigger_count = 2
            for _ in range(trigger_count):
                figure.slider.trigger(attr='value', old=0, new=1)
            self.assertIsNotNone(self.simulation_tile._plot_render_queue)

    def tearDown(self) -> None:
        """Clean up temporary folder and files."""
        self.tmp_dir.cleanup()

def set_up_simulation_log(self, output_path: Path) -> None:
    """
        Create a simulation log and save it to disk.
        :param output path: to write the simulation log to.
        """
    simulation_log = create_sample_simulation_log(output_path)
    simulation_log.save_to_file()

def setUp(self) -> None:
    """Set up simulation tile with nuboard file."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.vehicle_parameters = get_pacifica_parameters()
    simulation_log_path = Path(self.tmp_dir.name) / 'test_simulation_tile_simulation_log.msgpack.xz'
    self.set_up_simulation_log(simulation_log_path)
    nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulation', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
    self.scenario_keys = [SimulationScenarioKey(nuboard_file_index=0, log_name='dummy_log', planner_name='SimplePlanner', scenario_type='common', scenario_name='test', files=[simulation_log_path])]
    self.doc = Document()
    self.map_factory = MockMapFactory()
    self.experiment_file_data = ExperimentFileData(file_paths=[nuboard_file])
    self.simulation_tile = SimulationTile(doc=self.doc, map_factory=self.map_factory, vehicle_parameters=self.vehicle_parameters, radius=80, experiment_file_data=self.experiment_file_data)

def tearDown(self) -> None:
    """Clean up temporary folder and files."""
    self.tmp_dir.cleanup()

class TestBaseTab(unittest.TestCase):
    """Test base_tab functionality."""

    def set_up_dummy_simulation(self, simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
        save_path.mkdir(parents=True, exist_ok=True)
        simulation_data = create_sample_simulation_log(save_path / 'test_base_tab_simulation_log.msgpack.xz')
        simulation_data.save_to_file()

    def set_up_dummy_metric(self, metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90)]
        time_stamps = [0, 1, 2]
        accel = [0.0, 1.0, 2.0]
        time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
        result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1)
        key = MetricFileKey(metric_name='ego_acceleration', scenario_name=scenario_name, log_name=log_name, scenario_type=scenario_type, planner_name=planner_name)
        metric_engine = MetricsEngine(main_save_path=metric_path)
        metric_files = {'ego_acceleration': [MetricFile(key=key, metric_statistics=[result])]}
        metric_engine.write_to_files(metric_files=metric_files)
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """Set up a nuboard base tab."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        doc = Document()
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
        color_palettes = Category20[20] + Set3[12] + Bokeh[8]
        experiment_file_data = ExperimentFileData(file_paths=[], color_palettes=color_palettes)
        self.base_tab = BaseTab(doc=doc, experiment_file_data=experiment_file_data)

    def test_update_experiment_file_data(self) -> None:
        """Test update experiment file data."""
        self.base_tab.experiment_file_data.update_data(file_paths=[self.nuboard_file])
        self.assertEqual(len(self.base_tab.experiment_file_data.available_metric_statistics_names), 1)
        self.assertEqual(len(self.base_tab.experiment_file_data.simulation_scenario_keys), 1)

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change feature."""
        self.base_tab.experiment_file_data.update_data(file_paths=[self.nuboard_file])
        self.assertRaises(NotImplementedError, self.base_tab.file_paths_on_change, self.base_tab.experiment_file_data, [0])

    def tearDown(self) -> None:
        """Remove all temporary folders and files."""
        self.tmp_dir.cleanup()

def set_up_dummy_simulation(self, simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
    """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
    save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
    save_path.mkdir(parents=True, exist_ok=True)
    simulation_data = create_sample_simulation_log(save_path / 'test_base_tab_simulation_log.msgpack.xz')
    simulation_data.save_to_file()

def setUp(self) -> None:
    """Set up a nuboard base tab."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
    doc = Document()
    log_name = 'dummy_log'
    planner_name = 'SimplePlanner'
    scenario_type = 'Test'
    scenario_name = 'Dummy_scene'
    metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
    metric_path.mkdir(exist_ok=True, parents=True)
    self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
    simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
    simulation_path.mkdir(exist_ok=True, parents=True)
    self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
    color_palettes = Category20[20] + Set3[12] + Bokeh[8]
    experiment_file_data = ExperimentFileData(file_paths=[], color_palettes=color_palettes)
    self.base_tab = BaseTab(doc=doc, experiment_file_data=experiment_file_data)

def tearDown(self) -> None:
    """Remove all temporary folders and files."""
    self.tmp_dir.cleanup()

class TestNuBoardFile(unittest.TestCase):
    """Test NuBoardFile functionality."""

    def setUp(self) -> None:
        """Set up a nuBoard file class."""
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric')
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())

    def test_nuboard_save_and_load_file(self) -> None:
        """Test saving and loading a nuboard file."""
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.assertTrue(os.path.exists(self.nuboard_file_name))
        self.assertEqual(self.nuboard_file_name.suffix, self.nuboard_file.extension())
        nuboard_file = NuBoardFile.load_nuboard_file(self.nuboard_file_name)
        self.assertEqual(nuboard_file, self.nuboard_file)

    def tearDown(self) -> None:
        """Clean up temporary folder and files."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a nuBoard file class."""
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric')
    self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())

def test_nuboard_save_and_load_file(self) -> None:
    """Test saving and loading a nuboard file."""
    self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
    self.assertTrue(os.path.exists(self.nuboard_file_name))
    self.assertEqual(self.nuboard_file_name.suffix, self.nuboard_file.extension())
    nuboard_file = NuBoardFile.load_nuboard_file(self.nuboard_file_name)
    self.assertEqual(nuboard_file, self.nuboard_file)

def tearDown(self) -> None:
    """Clean up temporary folder and files."""
    self.tmp_dir.cleanup()

class TestNuBoard(unittest.TestCase):
    """Test nuboard functionality."""

    def setUp(self) -> None:
        """Set up nuboard a bokeh main page."""
        self.vehicle_parameters = get_pacifica_parameters()
        self.doc = Document()
        self.scenario_builder = MockAbstractScenarioBuilder()
        self.tmp_dir = tempfile.TemporaryDirectory()
        if not os.getenv('NUPLAN_EXP_ROOT', None):
            os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric')
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.main_paths = [str(self.nuboard_file_name)]
        self.nuboard = NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters)

    def test_main_page(self) -> None:
        """Test if successfully construct a bokeh main page."""
        self.nuboard.main_page(doc=self.doc)
        self.assertEqual(len(self.doc.roots), 34)

    @given(frame_rate_cap=st.integers(min_value=1, max_value=60))
    def test_valid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests valid frame rate cap range."""
        NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

    @given(frame_rate_cap=st.integers().filter(lambda x: x < 1 or x > 60))
    def test_invalid_frame_rate_cap_range(self, frame_rate_cap: int) -> None:
        """Tests invalid frame rate cap range."""
        with self.assertRaises(ValueError):
            NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters, scenario_rendering_frame_rate_cap_hz=frame_rate_cap)

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up nuboard a bokeh main page."""
    self.vehicle_parameters = get_pacifica_parameters()
    self.doc = Document()
    self.scenario_builder = MockAbstractScenarioBuilder()
    self.tmp_dir = tempfile.TemporaryDirectory()
    if not os.getenv('NUPLAN_EXP_ROOT', None):
        os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric')
    metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
    metric_path.mkdir(exist_ok=True, parents=True)
    simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
    simulation_path.mkdir(exist_ok=True, parents=True)
    self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
    self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
    self.main_paths = [str(self.nuboard_file_name)]
    self.nuboard = NuBoard(profiler_path=Path(self.tmp_dir.name), nuboard_paths=self.main_paths, scenario_builder=self.scenario_builder, vehicle_parameters=self.vehicle_parameters)

def tearDown(self) -> None:
    """Remove temporary folders and files."""
    self.tmp_dir.cleanup()

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

class ConfigurationTab:
    """Configuration tab for nuboard."""

    def __init__(self, doc: Document, experiment_file_data: ExperimentFileData, tabs: List[BaseTab]):
        """
        Configuration tab about configurating nuboard.
        :param experiment_file_data: Experiment file data.
        :param tabs: A list of tabs to be updated when configuration is changed.
        """
        self._doc = doc
        self._tabs = tabs
        self.experiment_file_data = experiment_file_data
        self._file_path_input = FileInput(accept=NuBoardFile.extension(), css_classes=['file-path-input'], margin=configuration_tab_style['file_path_input_margin'], name='file_path_input')
        self._file_path_input.on_change('value', self._add_experiment_file)
        self._experiment_file_path_checkbox_group = CheckboxGroup(labels=self.experiment_file_path_stems, active=[index for index in range(len(self.experiment_file_data.file_paths))], name='experiment_file_path_checkbox_group', css_classes=['experiment-file-path-checkbox-group'])
        self._experiment_file_path_checkbox_group.on_click(self._click_experiment_file_path_checkbox)
        if self.experiment_file_data.file_paths:
            self._file_paths_on_change()

    @property
    def experiment_file_path_stems(self) -> List[str]:
        """Return a list of file path stems."""
        experiment_paths = []
        for file_path in self.experiment_file_data.file_paths:
            metric_path = file_path.current_path / file_path.metric_folder
            if metric_path.exists():
                experiment_file_path_stem = file_path.current_path
            else:
                experiment_file_path_stem = file_path.metric_main_path
            if isinstance(experiment_file_path_stem, str):
                experiment_file_path_stem = pathlib.Path(experiment_file_path_stem)
            experiment_file_path_stem = '/'.join([experiment_file_path_stem.parts[-2], experiment_file_path_stem.parts[-1]])
            experiment_paths.append(experiment_file_path_stem)
        return experiment_paths

    @property
    def file_path_input(self) -> FileInput:
        """Return the file path input widget."""
        return self._file_path_input

    @property
    def experiment_file_path_checkbox_group(self) -> CheckboxGroup:
        """Return experiment file path checkboxgroup."""
        return self._experiment_file_path_checkbox_group

    def _click_experiment_file_path_checkbox(self, attr: Any) -> None:
        """
        Click event handler for experiment_file_path_checkbox_group.
        :param attr: Clicked attributes.
        """
        self._file_paths_on_change()

    def add_nuboard_file_to_experiments(self, nuboard_file: NuBoardFile) -> None:
        """
        Add nuboard files to experiments.
        :param nuboard_file: Added nuboard file.
        """
        nuboard_file.current_path = Path(nuboard_file.metric_main_path)
        if nuboard_file not in self.experiment_file_data.file_paths:
            self.experiment_file_data.update_data(file_paths=[nuboard_file])
            self._experiment_file_path_checkbox_group.labels = self.experiment_file_path_stems
            self._experiment_file_path_checkbox_group.active += [len(self.experiment_file_path_stems) - 1]
            self._file_paths_on_change()

    def _add_experiment_file(self, attr: str, old: bytes, new: bytes) -> None:
        """
        Event responds to file change.
        :param attr: Attribute name.
        :param old: Old value.
        :param new: New value.
        """
        if not new:
            return
        try:
            decoded_string = base64.b64decode(new)
            file_stream = io.BytesIO(decoded_string)
            data = pickle.load(file_stream)
            nuboard_file = NuBoardFile.deserialize(data=data)
            self.add_nuboard_file_to_experiments(nuboard_file=nuboard_file)
            file_stream.close()
        except (OSError, IOError) as e:
            logger.info(f'Error loading experiment file. {str(e)}.')

    def _file_paths_on_change(self) -> None:
        """Function to call when we change file paths."""
        for tab in self._tabs:
            tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=self._experiment_file_path_checkbox_group.active)

@property
def experiment_file_path_stems(self) -> List[str]:
    """Return a list of file path stems."""
    experiment_paths = []
    for file_path in self.experiment_file_data.file_paths:
        metric_path = file_path.current_path / file_path.metric_folder
        if metric_path.exists():
            experiment_file_path_stem = file_path.current_path
        else:
            experiment_file_path_stem = file_path.metric_main_path
        if isinstance(experiment_file_path_stem, str):
            experiment_file_path_stem = pathlib.Path(experiment_file_path_stem)
        experiment_file_path_stem = '/'.join([experiment_file_path_stem.parts[-2], experiment_file_path_stem.parts[-1]])
        experiment_paths.append(experiment_file_path_stem)
    return experiment_paths

def _add_experiment_file(self, attr: str, old: bytes, new: bytes) -> None:
    """
        Event responds to file change.
        :param attr: Attribute name.
        :param old: Old value.
        :param new: New value.
        """
    if not new:
        return
    try:
        decoded_string = base64.b64decode(new)
        file_stream = io.BytesIO(decoded_string)
        data = pickle.load(file_stream)
        nuboard_file = NuBoardFile.deserialize(data=data)
        self.add_nuboard_file_to_experiments(nuboard_file=nuboard_file)
        file_stream.close()
    except (OSError, IOError) as e:
        logger.info(f'Error loading experiment file. {str(e)}.')

def _file_paths_on_change(self) -> None:
    """Function to call when we change file paths."""
    for tab in self._tabs:
        tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=self._experiment_file_path_checkbox_group.active)

class TestScenarioTab(SkeletonTestTab):
    """Test nuboard scenario tab functionality."""

    def setUp(self) -> None:
        """Set up a scenario tab."""
        super().setUp()
        vehicle_parameters = get_pacifica_parameters()
        scenario_builder = MockAbstractScenarioBuilder()
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
        self.scenario_tab = ScenarioTab(experiment_file_data=self.experiment_file_data, scenario_builder=scenario_builder, vehicle_parameters=vehicle_parameters, doc=self.doc)

    def test_update_scenario(self) -> None:
        """Test functions corresponding to selection changes work as expected."""
        self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)

    def test_file_paths_on_change(self) -> None:
        """Test file_paths_on_change function."""
        new_experiment_file_data = ExperimentFileData(file_paths=[])
        self.scenario_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])
        self.assertEqual(self.scenario_tab._scalar_scenario_type_select.value, '')
        self.assertEqual(self.scenario_tab._scalar_scenario_type_select.options, [''])
        self.assertEqual(self.scenario_tab._scalar_scenario_name_select.value, '')
        self.assertEqual(self.scenario_tab._scalar_scenario_name_select.options, [])

    def test_update_scenario_legend(self) -> None:
        """Test functions corresponding to legend selection changes work as expected."""
        self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._traj_checkbox_group.active = [0]
        self.scenario_tab._map_checkbox_group.active = [0, 1, 2]
        self.scenario_tab._object_checkbox_group.active = [3, 4]

    def test_modal_button_on_click(self) -> None:
        """Test modal button on click function."""
        self.scenario_tab._experiment_file_active_index = [0]
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._scenario_modal_query_button_on_click()
        self.assertEqual(self.scenario_tab.planner_checkbox_group.labels, ['SimplePlanner'])
        self.assertIn('ego_acceleration_statistics', self.scenario_tab._time_series_data)

    def test_planner_button_on_click(self) -> None:
        """Test checkbox button in planner."""
        self.scenario_tab._experiment_file_active_index = [0]
        self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
        self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
        self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
        self.scenario_tab._scenario_modal_query_button_on_click()
        self.scenario_tab.planner_checkbox_group.active = []
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
        self.scenario_tab.planner_checkbox_group.active = [0]
        self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
        self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)
        with self.assertRaises(IndexError):
            self.scenario_tab.planner_checkbox_group.active = [1]

def setUp(self) -> None:
    """Set up a scenario tab."""
    super().setUp()
    vehicle_parameters = get_pacifica_parameters()
    scenario_builder = MockAbstractScenarioBuilder()
    self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
    self.scenario_tab = ScenarioTab(experiment_file_data=self.experiment_file_data, scenario_builder=scenario_builder, vehicle_parameters=vehicle_parameters, doc=self.doc)

def test_update_scenario(self) -> None:
    """Test functions corresponding to selection changes work as expected."""
    self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
    self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
    self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
    self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
    self.assertEqual(len(self.scenario_tab.simulation_tile_layout.children), 1)
    self.assertEqual(len(self.scenario_tab.time_series_layout.children), 1)

def test_file_paths_on_change(self) -> None:
    """Test file_paths_on_change function."""
    new_experiment_file_data = ExperimentFileData(file_paths=[])
    self.scenario_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])
    self.assertEqual(self.scenario_tab._scalar_scenario_type_select.value, '')
    self.assertEqual(self.scenario_tab._scalar_scenario_type_select.options, [''])
    self.assertEqual(self.scenario_tab._scalar_scenario_name_select.value, '')
    self.assertEqual(self.scenario_tab._scalar_scenario_name_select.options, [])

def test_update_scenario_legend(self) -> None:
    """Test functions corresponding to legend selection changes work as expected."""
    self.scenario_tab.file_paths_on_change(experiment_file_data=self.experiment_file_data, experiment_file_active_index=[0])
    self.scenario_tab._scalar_scenario_type_select.value = self.scenario_tab._scalar_scenario_type_select.options[1]
    self.scenario_tab._scalar_log_name_select.value = self.scenario_tab._scalar_log_name_select.options[1]
    self.scenario_tab._scalar_scenario_name_select.value = self.scenario_tab._scalar_scenario_name_select.options[1]
    self.scenario_tab._traj_checkbox_group.active = [0]
    self.scenario_tab._map_checkbox_group.active = [0, 1, 2]
    self.scenario_tab._object_checkbox_group.active = [3, 4]

class TestS3Tab(unittest.TestCase):
    """Test nuboard s3 tab functionality."""

    def setUp(self) -> None:
        """Set up a configuration tab."""
        self.doc = Document()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        metric_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        simulation_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
        self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)
        self.configuration_tab = ConfigurationTab(experiment_file_data=self.experiment_file_data, doc=self.doc, tabs=[self.histogram_tab])
        if not os.getenv('NUPLAN_EXP_ROOT', None):
            os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
        self.s3_tab = CloudTab(doc=self.doc, configuration_tab=self.configuration_tab)
        self.dummy_file_result_message = S3FileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Connect successfully'), file_contents={'dummy_a': S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)), 'dummy_b': S3FileContent(filename='dummy_b', size=10, last_modified=datetime(day=3, month=8, year=1992, tzinfo=timezone.utc))})

    def test_modal_query_btn(self) -> None:
        """Test if modal query btn works."""
        self.s3_tab._s3_modal_query_on_click()
        self.assertNotEqual(self.s3_tab._s3_client, None)

    def test_load_s3_contents_with_file_contents(self) -> None:
        """Test _load_s3_contents works if there are file contents."""
        self.s3_tab._load_s3_contents(s3_file_result_message=self.dummy_file_result_message)
        self.s3_tab.s3_error_text.text = self.dummy_file_result_message.s3_connection_status.return_message
        self.assertEqual(self.s3_tab.s3_error_text.text, self.dummy_file_result_message.s3_connection_status.return_message)

    def test_s3_data_source_on_selected(self) -> None:
        """Test _s3_data_source_on_selected work."""
        data_sources: Dict[str, List[Any]] = {'object': [], 'last_modified': [], 'timestamp': [], 'size': []}
        for file_name, content in self.dummy_file_result_message.file_contents.items():
            data_sources['object'].append(file_name)
            data_sources['last_modified'].append(content.last_modified_day if content.last_modified is not None else '')
            data_sources['timestamp'].append(content.date_string if content.date_string is not None else '')
            data_sources['size'].append(content.kb_size() if content.kb_size() is not None else '')
        self.s3_tab.data_table.source.data = data_sources
        self.s3_tab._selected_column.value = str(1)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[0], old=[])
        self.assertEqual(self.s3_tab.s3_download_text_input.value, 'dummy_a')
        self.s3_tab._selected_column.value = str(2)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[1], old=[])
        self.assertEqual(self.s3_tab.s3_download_text_input.value, 'dummy_b')
        self.s3_tab._selected_column.value = str(0)
        self.s3_tab._s3_data_source_on_selected(attr='indices', new=[0], old=[])
        self.assertNotEqual(self.s3_tab._s3_client, None)

    def test_s3_download_button_on_click(self) -> None:
        """Test if s3 download button on_click function works."""
        self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
        self.s3_tab.s3_download_text_input.value = 'test-prefix'
        self.s3_tab._s3_download_button_on_click()
        self.assertEqual(self.s3_tab.s3_download_button.label, 'Downloading...')
        self.assertTrue(self.s3_tab.s3_download_button.disabled)

    def test_s3_download_prefixes_fail_without_s3_client(self) -> None:
        """Test s3 tab download_prefixes function fails when there is no s3 client."""
        self.s3_tab._s3_download_prefixes()
        self.assertEqual(self.s3_tab.s3_error_text.text, 'No s3 connection!')

    def test_s3_download_prefixes_fail_without_nuboard_files(self) -> None:
        """Test s3 tab download_prefixes function fails when there is no nuboard files."""
        self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
        self.s3_tab.s3_download_text_input.value = 'test-prefix'
        s3_client = boto3.Session().client('s3')
        self.s3_tab._s3_client = s3_client
        stubber = Stubber(s3_client)
        expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
        expected_params = {'Bucket': 'test-bucket', 'Prefix': 'test-prefix/', 'Delimiter': '/'}
        stubber.add_response('list_objects_v2', expected_response, expected_params)
        with stubber:
            self.s3_tab._s3_download_prefixes()
            self.assertEqual(self.s3_tab.s3_error_text.text, 'No available nuboard files in the prefix')

    def test_s3_update_nuboard_file_main_path(self) -> None:
        """Test s3 tab _update_s3_nuboard_file_main_path function updates main path based on the selected prefix."""
        s3_nuboard_file_result_message = S3NuBoardFileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Get s3 nuboasrd file'), nuboard_file=self.nuboard_file, nuboard_filename=self.nuboard_file_name.name)
        prefix = self.tmp_dir.name
        self.s3_tab._update_s3_nuboard_file_main_path(s3_nuboard_file_result=s3_nuboard_file_result_message, selected_prefix=prefix)
        nuboard_file = s3_nuboard_file_result_message.nuboard_file
        self.assertEqual(nuboard_file.simulation_main_path, self.tmp_dir.name)
        self.assertEqual(nuboard_file.metric_main_path, self.tmp_dir.name)

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a configuration tab."""
    self.doc = Document()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
    metric_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.metric_folder
    metric_path.mkdir(exist_ok=True, parents=True)
    simulation_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.simulation_folder
    simulation_path.mkdir(exist_ok=True, parents=True)
    self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
    self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
    self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
    self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)
    self.configuration_tab = ConfigurationTab(experiment_file_data=self.experiment_file_data, doc=self.doc, tabs=[self.histogram_tab])
    if not os.getenv('NUPLAN_EXP_ROOT', None):
        os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
    self.s3_tab = CloudTab(doc=self.doc, configuration_tab=self.configuration_tab)
    self.dummy_file_result_message = S3FileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Connect successfully'), file_contents={'dummy_a': S3FileContent(filename='dummy_a', size=10, last_modified=datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)), 'dummy_b': S3FileContent(filename='dummy_b', size=10, last_modified=datetime(day=3, month=8, year=1992, tzinfo=timezone.utc))})

def test_load_s3_contents_with_file_contents(self) -> None:
    """Test _load_s3_contents works if there are file contents."""
    self.s3_tab._load_s3_contents(s3_file_result_message=self.dummy_file_result_message)
    self.s3_tab.s3_error_text.text = self.dummy_file_result_message.s3_connection_status.return_message
    self.assertEqual(self.s3_tab.s3_error_text.text, self.dummy_file_result_message.s3_connection_status.return_message)

def test_s3_download_prefixes_fail_without_s3_client(self) -> None:
    """Test s3 tab download_prefixes function fails when there is no s3 client."""
    self.s3_tab._s3_download_prefixes()
    self.assertEqual(self.s3_tab.s3_error_text.text, 'No s3 connection!')

def test_s3_download_prefixes_fail_without_nuboard_files(self) -> None:
    """Test s3 tab download_prefixes function fails when there is no nuboard files."""
    self.s3_tab.s3_bucket_name.text = 's3://test-bucket'
    self.s3_tab.s3_download_text_input.value = 'test-prefix'
    s3_client = boto3.Session().client('s3')
    self.s3_tab._s3_client = s3_client
    stubber = Stubber(s3_client)
    expected_response = {'CommonPrefixes': [{'Prefix': 'dummy_folder_a/log.txt'}, {'Prefix': 'dummy_folder_b/log_2.txt'}], 'Contents': [{'Key': 'dummy_a', 'Size': 15, 'LastModified': datetime(day=2, month=7, year=1992, tzinfo=timezone.utc)}, {'Key': 'dummy_b', 'Size': 45, 'LastModified': datetime(day=6, month=7, year=1992, tzinfo=timezone.utc)}]}
    expected_params = {'Bucket': 'test-bucket', 'Prefix': 'test-prefix/', 'Delimiter': '/'}
    stubber.add_response('list_objects_v2', expected_response, expected_params)
    with stubber:
        self.s3_tab._s3_download_prefixes()
        self.assertEqual(self.s3_tab.s3_error_text.text, 'No available nuboard files in the prefix')

def test_s3_update_nuboard_file_main_path(self) -> None:
    """Test s3 tab _update_s3_nuboard_file_main_path function updates main path based on the selected prefix."""
    s3_nuboard_file_result_message = S3NuBoardFileResultMessage(s3_connection_status=S3ConnectionStatus(success=True, return_message='Get s3 nuboasrd file'), nuboard_file=self.nuboard_file, nuboard_filename=self.nuboard_file_name.name)
    prefix = self.tmp_dir.name
    self.s3_tab._update_s3_nuboard_file_main_path(s3_nuboard_file_result=s3_nuboard_file_result_message, selected_prefix=prefix)
    nuboard_file = s3_nuboard_file_result_message.nuboard_file
    self.assertEqual(nuboard_file.simulation_main_path, self.tmp_dir.name)
    self.assertEqual(nuboard_file.metric_main_path, self.tmp_dir.name)

def tearDown(self) -> None:
    """Remove temporary folders and files."""
    self.tmp_dir.cleanup()

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

def test_file_paths_on_change(self) -> None:
    """Test file_paths_on_change function."""
    new_experiment_file_data = ExperimentFileData(file_paths=[])
    self.overview_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])

class SkeletonTestTab(unittest.TestCase):
    """Base class for nuBoard tab unit tests."""

    @staticmethod
    def set_up_dummy_simulation(simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
        save_path.mkdir(parents=True, exist_ok=True)
        simulation_data = create_sample_simulation_log(save_path / f'{uuid4()}.msgpack.xz')
        simulation_data.save_to_file()

    @staticmethod
    def set_up_dummy_metric(metric_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
        """
        Set up dummy metric results.
        :param metric_path: Metric path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
        statistics = [Statistic(name='ego_max_acceleration', unit='meters_per_second_squared', value=2.0, type=MetricStatisticsType.MAX), Statistic(name='ego_min_acceleration', unit='meters_per_second_squared', value=0.0, type=MetricStatisticsType.MIN), Statistic(name='ego_p90_acceleration', unit='meters_per_second_squared', value=1.0, type=MetricStatisticsType.P90), Statistic(name='ego_count_acceleration', unit=MetricStatisticsType.COUNT.unit, value=2, type=MetricStatisticsType.COUNT), Statistic(name='ego_boolean_acceleration', unit=MetricStatisticsType.BOOLEAN.unit, value=True, type=MetricStatisticsType.BOOLEAN)]
        time_stamps = [0, 1, 2]
        accel = [0.0, 1.0, 2.0]
        time_series = TimeSeries(unit='meters_per_second_squared', time_stamps=list(time_stamps), values=list(accel))
        result = MetricStatistics(metric_computator='ego_acceleration', name='ego_acceleration_statistics', statistics=statistics, time_series=time_series, metric_category='Dynamic', metric_score=1.0)
        key = MetricFileKey(metric_name='ego_acceleration', log_name=log_name, scenario_name=scenario_name, scenario_type=scenario_type, planner_name=planner_name)
        metric_engine = MetricsEngine(main_save_path=metric_path)
        metric_files = {scenario_name: [MetricFile(key=key, metric_statistics=[result])]}
        metric_engine.write_to_files(metric_files=metric_files)
        metric_file_callback = MetricFileCallback(metric_file_output_path=str(metric_path), scenario_metric_paths=[str(metric_path)])
        metric_file_callback.on_run_simulation_end()

    def setUp(self) -> None:
        """
        Set up common data for nuboard unit tests.
        """
        self.doc = Document()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        log_name = 'dummy_log'
        planner_name = 'SimplePlanner'
        scenario_type = 'Test'
        scenario_name = 'Dummy_scene'
        metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
        simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

@staticmethod
def set_up_dummy_simulation(simulation_path: Path, log_name: str, planner_name: str, scenario_type: str, scenario_name: str) -> None:
    """
        Set up dummy simulation data.
        :param simulation_path: Simulation path.
        :param log_name: Log name.
        :param planner_name: Planner name.
        :param scenario_type: Scenario type.
        :param scenario_name: Scenario name.
        """
    save_path = simulation_path / planner_name / scenario_type / log_name / scenario_name
    save_path.mkdir(parents=True, exist_ok=True)
    simulation_data = create_sample_simulation_log(save_path / f'{uuid4()}.msgpack.xz')
    simulation_data.save_to_file()

def setUp(self) -> None:
    """
        Set up common data for nuboard unit tests.
        """
    self.doc = Document()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
    log_name = 'dummy_log'
    planner_name = 'SimplePlanner'
    scenario_type = 'Test'
    scenario_name = 'Dummy_scene'
    metric_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.metric_folder
    metric_path.mkdir(exist_ok=True, parents=True)
    self.set_up_dummy_metric(metric_path=metric_path, log_name=log_name, planner_name=planner_name, scenario_name=scenario_name, scenario_type=scenario_type)
    simulation_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.simulation_folder
    simulation_path.mkdir(exist_ok=True, parents=True)
    self.set_up_dummy_simulation(simulation_path, log_name=log_name, planner_name=planner_name, scenario_type=scenario_type, scenario_name=scenario_name)
    self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
    self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
    self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])

def tearDown(self) -> None:
    """Remove temporary folders and files."""
    self.tmp_dir.cleanup()

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

def test_file_paths_on_change(self) -> None:
    """Test file_paths_on_change function."""
    new_experiment_file_data = ExperimentFileData(file_paths=[])
    self.histogram_tab.file_paths_on_change(experiment_file_data=new_experiment_file_data, experiment_file_active_index=[])
    self.assertEqual(self.histogram_tab._scenario_type_multi_choice.value, [])
    self.assertEqual(self.histogram_tab._scenario_type_multi_choice.options, ['all'])
    self.assertEqual(self.histogram_tab._metric_name_multi_choice.value, [])
    self.assertEqual(self.histogram_tab._metric_name_multi_choice.options, [])

class TestConfigurationTab(unittest.TestCase):
    """Test nuboard configuration tab functionality."""

    def setUp(self) -> None:
        """Set up a configuration tab."""
        self.doc = Document()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
        metric_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.metric_folder
        metric_path.mkdir(exist_ok=True, parents=True)
        simulation_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.simulation_folder
        simulation_path.mkdir(exist_ok=True, parents=True)
        self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
        self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
        self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
        self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)
        self.configuration_tab = ConfigurationTab(experiment_file_data=self.experiment_file_data, doc=self.doc, tabs=[self.histogram_tab])

    def test_file_path_on_change(self) -> None:
        """Test function when the file path is changed."""
        self.configuration_tab._file_paths = []
        self.configuration_tab._file_paths_on_change()
        self.assertEqual(self.histogram_tab._scenario_type_multi_choice.value, [])
        self.assertEqual(self.histogram_tab._scenario_type_multi_choice.options, ['all'])
        self.assertEqual(self.histogram_tab._metric_name_multi_choice.value, [])
        self.assertEqual(self.histogram_tab._metric_name_multi_choice.options, [])

    def test_add_experiment_file(self) -> None:
        """Test add experiment file function."""
        attr = 'value'
        old = 'None'
        self.configuration_tab.experiment_file_data.file_paths = []
        self.configuration_tab._add_experiment_file(attr=attr, old=pickle.dumps(old), new=base64.b64encode(pickle.dumps(self.nuboard_file.serialize())))

    def tearDown(self) -> None:
        """Remove temporary folders and files."""
        self.tmp_dir.cleanup()

def setUp(self) -> None:
    """Set up a configuration tab."""
    self.doc = Document()
    self.tmp_dir = tempfile.TemporaryDirectory()
    self.nuboard_file = NuBoardFile(simulation_main_path=self.tmp_dir.name, metric_main_path=self.tmp_dir.name, metric_folder='metrics', simulation_folder='simulations', aggregator_metric_folder='aggregator_metric', current_path=Path(self.tmp_dir.name))
    metric_path = Path(self.nuboard_file.simulation_main_path) / self.nuboard_file.metric_folder
    metric_path.mkdir(exist_ok=True, parents=True)
    simulation_path = Path(self.nuboard_file.metric_main_path) / self.nuboard_file.simulation_folder
    simulation_path.mkdir(exist_ok=True, parents=True)
    self.nuboard_file_name = Path(self.tmp_dir.name) / ('nuboard_file' + self.nuboard_file.extension())
    self.nuboard_file.save_nuboard_file(self.nuboard_file_name)
    self.experiment_file_data = ExperimentFileData(file_paths=[self.nuboard_file])
    self.histogram_tab = HistogramTab(experiment_file_data=self.experiment_file_data, doc=self.doc)
    self.configuration_tab = ConfigurationTab(experiment_file_data=self.experiment_file_data, doc=self.doc, tabs=[self.histogram_tab])

def test_add_experiment_file(self) -> None:
    """Test add experiment file function."""
    attr = 'value'
    old = 'None'
    self.configuration_tab.experiment_file_data.file_paths = []
    self.configuration_tab._add_experiment_file(attr=attr, old=pickle.dumps(old), new=base64.b64encode(pickle.dumps(self.nuboard_file.serialize())))

def tearDown(self) -> None:
    """Remove temporary folders and files."""
    self.tmp_dir.cleanup()

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

def __str__(self) -> str:
    """Metric type string representation."""
    return str(self.value)

def __repr__(self) -> str:
    """Metric type string representation."""
    return str(self.value)

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

@cached_property
def statistic_names(self) -> List[str]:
    """Return a list of statistic names in a table."""
    return [col.split('_stat_type')[0] for col in self.column_names if '_stat_type' in col]

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

def read_parquet(self) -> None:
    """Read a parquet file."""
    self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

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
def _save_parquet(dataframe: pandas.DataFrame, save_path: Path) -> None:
    """
        Save dataframe to a parquet file.
        The path can be local or s3.
        :param dataframe: Pandas dataframe.
        :param save_path: Path to save the dataframe.
        """
    dataframe.to_parquet(safe_path_to_string(save_path))

class TestWeightedAverageMetricAggregator(unittest.TestCase):
    """Run weighted average metric aggregator unit tests."""

    def setUp(self) -> None:
        """Set up dummy data and folders."""
        self.metric_scores = [[1, 0.5, 0.8], [0.1, 0.2]]
        dummy_dataframes = [pandas.DataFrame({'scenario_name': ['test_1', 'test_2', 'test_3'], 'log_name': ['dummy', 'dummy', 'dummy_2'], 'scenario_type': ['unknown', 'ego_stop_at_stop_line', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner', 'dummy_planner'], 'metric_score': self.metric_scores[0], 'metric_score_unit': 'float'}), pandas.DataFrame({'scenario_name': ['test_1', 'test_3'], 'log_name': ['dummy', 'dummy_3'], 'scenario_type': ['unknown', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner'], 'metric_score': self.metric_scores[1], 'metric_score_unit': 'float'})]
        metric_statistic_names = ['dummy_metric', 'second_dummy_metric']
        self.metric_statistic_dataframes = []
        for dummy_dataframe, metric_statistic_name in zip(dummy_dataframes, metric_statistic_names):
            self.metric_statistic_dataframes.append(MetricStatisticsDataFrame(metric_statistic_name=metric_statistic_name, metric_statistics_dataframe=dummy_dataframe))
        self.tmpdir = tempfile.TemporaryDirectory()
        self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=Path(self.tmpdir.name), multiple_metrics=[])

    def tearDown(self) -> None:
        """Clean up when unittests end."""
        self.tmpdir.cleanup()

    def test_name(self) -> None:
        """Test if name is expected."""
        self.assertEqual('weighted_average_metric_aggregator', self.weighted_average_metric_aggregator.name)

    def test_final_metric_score(self) -> None:
        """Test if final metric score is expected."""
        self.assertEqual(None, self.weighted_average_metric_aggregator.final_metric_score)

    def test_aggregated_metric_dataframe(self) -> None:
        """Test if aggregated metric dataframe is expected."""
        self.assertEqual(None, self.weighted_average_metric_aggregator.aggregated_metric_dataframe)

    def test_aggregation(self) -> None:
        """Test running the aggregation."""
        metric_dataframes = {metric_statistic_dataframe.metric_statistic_name: metric_statistic_dataframe for metric_statistic_dataframe in self.metric_statistic_dataframes}
        self.weighted_average_metric_aggregator(metric_dataframes=metric_dataframes)
        parquet_file = Path(self.tmpdir.name) / 'test_weighted_average_metric_aggregator.parquet'
        self.assertTrue(parquet_file.exists())
        self.weighted_average_metric_aggregator.read_parquet()
        aggregated_metric_dataframe = self.weighted_average_metric_aggregator.aggregated_metric_dataframe
        self.assertIsNot(aggregated_metric_dataframe, None)
        self.assertTrue(len(aggregated_metric_dataframe))
        self.assertTrue(np.isnan(aggregated_metric_dataframe['second_dummy_metric'][0]))
        expected_planners = ['dummy_planner', 'simple_planner']
        self.assertEqual(expected_planners, sorted(aggregated_metric_dataframe['planner_name'].unique(), reverse=False))
        self.assertEqual(['weighted_average'], list(aggregated_metric_dataframe['aggregator_type'].unique()))
        expected_values = {'dummy_planner': {'dummy_metric': [0.5, 0.8, 0.5, 0.8, 0.65], 'second_dummy_metric': [-1.0, 0.2, -1.0, 0.2, 0.1], 'score': [0.5, 0.4, 0.5, 0.4, 0.45]}, 'simple_planner': {'dummy_metric': [1.0, 1.0, 1.0], 'second_dummy_metric': [0.1, 0.1, 0.1], 'score': [0.4, 0.4, 0.4]}}
        for planner in expected_planners:
            planner_metric = aggregated_metric_dataframe[aggregated_metric_dataframe['planner_name'].isin([planner])]
            for name, expected_value in expected_values[planner].items():
                planner_values = np.round(planner_metric[name].fillna(-1.0).to_numpy(), 2).tolist()
                self.assertEqual(expected_value, planner_values)

    def test_parquet(self) -> None:
        """Test property."""
        self.assertEqual(self.weighted_average_metric_aggregator.parquet_file, self.weighted_average_metric_aggregator._parquet_file)

def setUp(self) -> None:
    """Set up dummy data and folders."""
    self.metric_scores = [[1, 0.5, 0.8], [0.1, 0.2]]
    dummy_dataframes = [pandas.DataFrame({'scenario_name': ['test_1', 'test_2', 'test_3'], 'log_name': ['dummy', 'dummy', 'dummy_2'], 'scenario_type': ['unknown', 'ego_stop_at_stop_line', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner', 'dummy_planner'], 'metric_score': self.metric_scores[0], 'metric_score_unit': 'float'}), pandas.DataFrame({'scenario_name': ['test_1', 'test_3'], 'log_name': ['dummy', 'dummy_3'], 'scenario_type': ['unknown', 'unknown'], 'planner_name': ['simple_planner', 'dummy_planner'], 'metric_score': self.metric_scores[1], 'metric_score_unit': 'float'})]
    metric_statistic_names = ['dummy_metric', 'second_dummy_metric']
    self.metric_statistic_dataframes = []
    for dummy_dataframe, metric_statistic_name in zip(dummy_dataframes, metric_statistic_names):
        self.metric_statistic_dataframes.append(MetricStatisticsDataFrame(metric_statistic_name=metric_statistic_name, metric_statistics_dataframe=dummy_dataframe))
    self.tmpdir = tempfile.TemporaryDirectory()
    self.weighted_average_metric_aggregator = WeightedAverageMetricAggregator(name='weighted_average_metric_aggregator', metric_weights={'default': 1.0, 'dummy_metric': 0.5}, file_name='test_weighted_average_metric_aggregator.parquet', aggregator_save_path=Path(self.tmpdir.name), multiple_metrics=[])

def tearDown(self) -> None:
    """Clean up when unittests end."""
    self.tmpdir.cleanup()

class MockAbstractMetricAggregator(AbstractMetricAggregator):
    """Mock Metric aggregator."""

    def __init__(self, aggregator_save_path: Path, name: str='dummy_metric_aggregator', metric_weights: Optional[Dict[str, float]]=None, file_name: str='dummy_metric_aggregator.parquet'):
        """
        Initializer for MockAbstractMetricAggregator class
        :param name: Metric aggregator name
        :param metric_weights: Weights for each metric. Default would be 1.0
        :param file_name: Saved file name
        :param aggregator_save_path: Save path for this aggregated parquet file.
        """
        self._name = name
        self._metric_weights = metric_weights or {'default': 1.0}
        self._file_name = file_name
        self._aggregator_save_path = aggregator_save_path
        if not self._aggregator_save_path.exists():
            self._aggregator_save_path.mkdir(exist_ok=True, parents=True)
        self._parquet_file = self._aggregator_save_path / self._file_name
        self._aggregated_metric_dataframe: Optional[pandas.DataFrame] = None

    @property
    def aggregated_metric_dataframe(self) -> Optional[pandas.DataFrame]:
        """Return the aggregated metric dataframe."""
        return self._aggregated_metric_dataframe

    @property
    def name(self) -> str:
        """
        Return the metric aggregator name
        :return: the metric aggregator name.
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
        Get metric weights
        :param metric_name: The metric name
        :return: Weight for the metric.
        """
        metric_weight = self._metric_weights.get(metric_name, None)
        if not metric_weight:
            metric_weight = self._metric_weights.get('default', 1.0)
        return metric_weight

    def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
        """
        Run an aggregator to generate an aggregated parquet file
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
        dataframe_columns = {'test_column_1': [1, 2, 3], 'test_column_2': [4, 5, 6]}
        self._aggregated_metric_dataframe = pandas.DataFrame(data=dataframe_columns)
        self._save_parquet(dataframe=self._aggregated_metric_dataframe, save_path=self._parquet_file)

    def read_parquet(self) -> None:
        """Read a parquet file."""
        self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

    @property
    def parquet_file(self) -> Path:
        """Inherited, see superclass."""
        return self._parquet_file

    @property
    def challenge(self) -> Optional[str]:
        """Inherited, see superclass."""
        return None

def __init__(self, aggregator_save_path: Path, name: str='dummy_metric_aggregator', metric_weights: Optional[Dict[str, float]]=None, file_name: str='dummy_metric_aggregator.parquet'):
    """
        Initializer for MockAbstractMetricAggregator class
        :param name: Metric aggregator name
        :param metric_weights: Weights for each metric. Default would be 1.0
        :param file_name: Saved file name
        :param aggregator_save_path: Save path for this aggregated parquet file.
        """
    self._name = name
    self._metric_weights = metric_weights or {'default': 1.0}
    self._file_name = file_name
    self._aggregator_save_path = aggregator_save_path
    if not self._aggregator_save_path.exists():
        self._aggregator_save_path.mkdir(exist_ok=True, parents=True)
    self._parquet_file = self._aggregator_save_path / self._file_name
    self._aggregated_metric_dataframe: Optional[pandas.DataFrame] = None

def __call__(self, metric_dataframes: Dict[str, MetricStatisticsDataFrame]) -> None:
    """
        Run an aggregator to generate an aggregated parquet file
        :param metric_dataframes: A dictionary of metric name and dataframe.
        """
    dataframe_columns = {'test_column_1': [1, 2, 3], 'test_column_2': [4, 5, 6]}
    self._aggregated_metric_dataframe = pandas.DataFrame(data=dataframe_columns)
    self._save_parquet(dataframe=self._aggregated_metric_dataframe, save_path=self._parquet_file)

def read_parquet(self) -> None:
    """Read a parquet file."""
    self._aggregated_metric_dataframe = pandas.read_parquet(self._parquet_file)

def save_runner_reports(reports: List[RunnerReport], output_dir: Path, report_name: str) -> None:
    """
    Save runner reports to a parquet file in the output directory.
    Output directory can be local or s3.
    :param reports: Runner reports returned from each simulation.
    :param output_dir: Output directory to save the report.
    :param report_name: Report name.
    """
    report_dicts = []
    for report in map(lambda x: x.__dict__, reports):
        if (planner_report := report['planner_report']) is not None:
            planner_report_statistics = planner_report.compute_summary_statistics()
            del report['planner_report']
            report.update(planner_report_statistics)
        report_dicts.append(report)
    df = pd.DataFrame(report_dicts)
    df['duration'] = df['end_time'] - df['start_time']
    save_path = output_dir / report_name
    df.to_parquet(safe_path_to_string(save_path))
    logger.info(f'Saved runner reports to {save_path}')

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Execute all available challenges simultaneously on the same scenario. Calls run_simulation to allow planner to
    be specified via config or directly passed as argument.
    :param cfg: Configuration that is used to run the experiment.
        Already contains the changes merged from the experiment's config to default config.
    """
    assert cfg.simulation_log_main_path is None, 'Simulation_log_main_path must not be set when running simulation.'
    run_simulation(cfg=cfg)
    if is_s3_path(Path(cfg.output_dir)):
        clean_up_s3_artifacts()

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Execute metric aggregators with the simulation path.
    :param cfg: Hydra config dict.
    """
    cfg.scenario_metric_paths = cfg.scenario_metric_paths or []
    metric_summary_callbacks = []
    challenge_metric_save_paths = []
    for challenge in cfg.challenges:
        challenge_save_path = Path(cfg.output_dir) / cfg.metric_folder_name / challenge
        challenge_metric_save_paths.append(challenge_save_path)
        if not challenge_save_path.exists():
            challenge_save_path.mkdir(exist_ok=True, parents=True)
        if cfg.scenario_metric_paths:
            challenge_metric_paths = [path for path in cfg.scenario_metric_paths if challenge in path]
            metric_file_callback = MetricFileCallback(scenario_metric_paths=challenge_metric_paths, metric_file_output_path=str(challenge_save_path), delete_scenario_metric_files=cfg.delete_scenario_metric_files)
            metric_file_callback.on_run_simulation_end()
    metric_output_path = Path(cfg.output_dir) / cfg.metric_folder_name
    metric_summary_output_path = str(Path(cfg.output_dir) / 'summary')
    if cfg.enable_metric_summary:
        if not challenge_metric_save_paths:
            challenge_metric_save_paths.append(metric_output_path)
        for challenge_metric_save_path in challenge_metric_save_paths:
            file_name = challenge_metric_save_path.stem if challenge_metric_save_path.stem in cfg.challenges else 'summary'
            pdf_file_name = file_name + '.pdf'
            metric_summary_callbacks.append(MetricSummaryCallback(metric_save_path=challenge_metric_save_path, metric_aggregator_save_path=cfg.aggregator_save_path, summary_output_path=metric_summary_output_path, pdf_file_name=pdf_file_name))
    metric_aggregators = build_metrics_aggregators(cfg)
    metric_aggregator_callback = MetricAggregatorCallback(metric_save_path=str(metric_output_path), metric_aggregators=metric_aggregators)
    metric_aggregator_callback.on_run_simulation_end()
    for metric_summary_callback in metric_summary_callbacks:
        metric_summary_callback.on_run_simulation_end()

def is_submission_successful(challenges: List[str], simulation_results_dir: Path) -> bool:
    """
    Checks if evaluation of one submission was successful, by checking that all instances for all challenges
    were completed.
    :param challenges: The list of challenges.
    :param simulation_results_dir: Path were the simulation results are saved locally.
    :return: True if the submission was evaluated successfully, False otherwise.
    """
    completed = list(simulation_results_dir.rglob('*completed.txt'))
    successful = True if len(completed) == len(challenges) * NUM_INSTANCES_PER_CHALLENGE else False
    logger.info('Found %s completed simulations' % len(completed))
    logger.info('Simulation was successful:  %s' % successful)
    return successful

@hydra.main(config_path=CONFIG_PATH, config_name=CONFIG_NAME)
def main(cfg: DictConfig) -> None:
    """
    Downloads evaluation results from S3, runs metric aggregator and re-uploads the results.
    :param cfg: Hydra config dict.
    """
    local_output_dir = Path(cfg.output_dir, cfg.contestant_id, cfg.submission_id)
    cfg.challenges = CHALLENGES
    Path(cfg.output_dir).mkdir(exist_ok=True, parents=True)
    s3_download(prefix='/'.join([cfg.contestant_id, cfg.submission_id]), local_path_name=cfg.output_dir, filters=None)
    simulation_successful = is_submission_successful(cfg.challenges, local_output_dir)
    cfg.output_dir = str(local_output_dir)
    cfg.scenario_metric_paths = list_subdirs_filtered(local_output_dir, re.compile(f'/{cfg.metric_folder_name}$'))
    logger.info('Found metric paths %s' % cfg.scenario_metric_paths)
    aggregated_metric_save_path = local_output_dir / cfg.aggregated_metric_folder_name
    leaderboard_writer = LeaderBoardWriter(cfg, str(local_output_dir))
    simulation_results = {}
    summary_results = {}
    try:
        if simulation_successful:
            shutil.rmtree(str(aggregated_metric_save_path), ignore_errors=True)
            aggregated_metric_save_path.mkdir(parents=True, exist_ok=True)
            aggregator_main(cfg)
            simulation_results['aggregated-metrics'] = {'upload': True, 'save_path': str(aggregated_metric_save_path), 'remote_path': 'aggregated_metrics'}
            simulation_results['metrics'] = {'upload': True, 'save_path': str(local_output_dir / cfg.metric_folder_name), 'remote_path': 'metrics'}
            summary_results['summary'] = {'upload': True, 'save_path': str(local_output_dir / 'summary'), 'remote_path': 'summary'}
    except Exception as e:
        submission_logger.error('Aggregation failed!')
        submission_logger.error(e)
        simulation_successful = False
    finally:
        simulation_results['submission_logs'] = {'upload': True, 'save_path': '/tmp/submission.log', 'remote_path': 'aggregated_metrics'}
        result_remote_prefix = [str(cfg.contestant_id), str(cfg.submission_id)]
        result_s3_client = get_s3_client()
        result_publisher_callback = PublisherCallback(simulation_results, remote_prefix=result_remote_prefix, s3_client=result_s3_client, s3_bucket=os.getenv('NUPLAN_SERVER_S3_ROOT_URL'))
        result_publisher_callback.on_run_simulation_end()
        summary_publisher_callback = PublisherCallback(summary_results, remote_prefix=['public/leaderboard/planning/2022', cfg.submission_id], s3_client=result_s3_client, s3_bucket=os.getenv('NUPLAN_SERVER_S3_ROOT_URL'))
        summary_publisher_callback.on_run_simulation_end()
    leaderboard_writer.write_to_leaderboard(simulation_successful=simulation_successful)
    shutil.rmtree(local_output_dir)

def build_metrics_aggregators(cfg: DictConfig) -> List[AbstractMetricAggregator]:
    """
    Build a list of metric aggregators.
    :param cfg: Config
    :return A list of metric aggregators, and the path in which they will  save the results
    """
    metric_aggregators = []
    metric_aggregator_configs = cfg.metric_aggregator
    aggregator_save_path = Path(cfg.aggregator_save_path)
    if not is_s3_path(aggregator_save_path):
        aggregator_save_path.mkdir(exist_ok=True, parents=True)
    for metric_aggregator_config_name, metric_aggregator_config in metric_aggregator_configs.items():
        metric_aggregators.append(instantiate(metric_aggregator_config, aggregator_save_path=aggregator_save_path))
    return metric_aggregators

def build_simulation_logs(cfg: DictConfig) -> List[SimulationLog]:
    """
    Build a list of simulation logs.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return A list of simulation logs.
    """
    logger.info('Building simulation logs...')
    simulation_logs = []
    simulation_log_path = Path(cfg.simulation_log_main_path) / cfg.callback.simulation_log_callback.simulation_log_dir
    for planner_dir_folder in simulation_log_path.iterdir():
        for scenario_type_folder in planner_dir_folder.iterdir():
            for log_name_folder in scenario_type_folder.iterdir():
                for scenario_name_folder in log_name_folder.iterdir():
                    for scenario_log_file in scenario_name_folder.iterdir():
                        simulation_log = SimulationLog.load_data(file_path=scenario_log_file)
                        simulation_logs.append(simulation_log)
    logger.info(f'Building simulation logs: {len(simulation_logs)}...DONE!')
    return simulation_logs

class LogHandlerConfig:
    """This is a simple config struct for log handles. Used by configure_logger method."""

    def __init__(self, level: str, path: Optional[str]=None, filter_regexp: str='') -> None:
        """
        :param level: logging level represented as string, E.g. 'info'.
        :param path: Path to where to store the log. Leave as None for logging to console.
        :param filter_regexp: Regexp defining the filter. This will be used in a PathKeywordMatch object.
        """
        self.level = level
        self.path = path
        self.filter_regexp = filter_regexp
        if self.path is not None:
            _dir = os.path.dirname(self.path)
            if not os.path.exists(_dir):
                os.makedirs(_dir)

def __init__(self, level: str, path: Optional[str]=None, filter_regexp: str='') -> None:
    """
        :param level: logging level represented as string, E.g. 'info'.
        :param path: Path to where to store the log. Leave as None for logging to console.
        :param filter_regexp: Regexp defining the filter. This will be used in a PathKeywordMatch object.
        """
    self.level = level
    self.path = path
    self.filter_regexp = filter_regexp
    if self.path is not None:
        _dir = os.path.dirname(self.path)
        if not os.path.exists(_dir):
            os.makedirs(_dir)

def build_training_experiment_folder(cfg: DictConfig) -> None:
    """
    Builds the main experiment folder for training.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    """
    logger.info('Building experiment folders...')
    main_exp_folder = pathlib.Path(cfg.output_dir)
    logger.info(f'Experimental folder: {main_exp_folder}')
    main_exp_folder.mkdir(parents=True, exist_ok=True)

def build_simulation_experiment_folder(cfg: DictConfig) -> str:
    """
    Builds the main experiment folder for simulation.
    :param cfg: DictConfig. Configuration that is used to run the experiment.
    :return: The main experiment folder path.
    """
    logger.info('Building experiment folders...')
    main_exp_folder = pathlib.Path(cfg.output_dir)
    logger.info(f'\n\n\tFolder where all results are stored: {main_exp_folder}\n')
    if not is_s3_path(main_exp_folder):
        main_exp_folder.mkdir(parents=True, exist_ok=True)
    if 'simulation_log_main_path' in cfg and cfg.simulation_log_main_path is not None:
        exp_folder = pathlib.Path(cfg.simulation_log_main_path)
        logger.info(f'\n\n\tUsing previous simulation logs: {exp_folder}\n')
        if not path_exists(exp_folder):
            raise FileNotFoundError(f'{exp_folder} does not exist.')
    else:
        exp_folder = main_exp_folder
    if 'simulation_log_callback' in cfg.callback:
        simulation_folder = cfg.callback.simulation_log_callback.simulation_log_dir
    else:
        simulation_folder = None
    metric_main_path = main_exp_folder / cfg.metric_dir
    if not is_s3_path(metric_main_path):
        metric_main_path.mkdir(parents=True, exist_ok=True)
    if int(os.environ.get('NODE_RANK', 0)) == 0:
        nuboard_filename = main_exp_folder / (f'nuboard_{int(time.time())}' + NuBoardFile.extension())
        nuboard_file = NuBoardFile(simulation_main_path=safe_path_to_string(exp_folder), simulation_folder=simulation_folder, metric_main_path=safe_path_to_string(exp_folder), metric_folder=cfg.metric_dir, aggregator_metric_folder=cfg.aggregator_metric_dir)
        nuboard_file.save_nuboard_file(nuboard_filename)
    logger.info('Building experiment folders...DONE!')
    return exp_folder.name

def get_s3_scenario_cache(cache_path: str, feature_names: Set[str], worker: WorkerPool) -> List[Path]:
    """
    Get a list of cached scenario paths from a remote (S3) cache.
    :param cache_path: Root path of the remote cache dir.
    :param feature_names: Set of required feature names to check when loading scenario paths from the cache.
    :return: List of discovered cached scenario paths.
    """
    assert check_s3_path_exists(cache_path), 'Remote cache {cache_path} does not exist!'
    s3_bucket, s3_key = split_s3_path(cache_path)
    metadata_files = get_cache_metadata_paths(s3_key, s3_bucket)
    if len(metadata_files) > 0:
        logger.info('Reading s3 directory from metadata.')
        cache_metadata_entries = read_cache_metadata(Path(cache_path), metadata_files, worker)
        s3_filenames = extract_field_from_cache_metadata_entries(cache_metadata_entries, 'file_name')
    else:
        logger.warning('Not using metadata! This will be slow...')
        s3_filenames = expand_s3_dir(cache_path)
    assert len(s3_filenames) > 0, f'No files found in the remote cache {cache_path}!'
    cache_map: Dict[str, Dict[str, Dict[str, Set[str]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for s3_filename in s3_filenames:
        path = Path(s3_filename)
        cache_map[path.parent.parent.parent.name][path.parent.parent.name][path.parent.name].add(path.stem)
    scenario_cache_paths = [Path(f'{log_name}/{scenario_type}/{scenario_token}') for log_name, scenario_types in cache_map.items() for scenario_type, scenarios in scenario_types.items() for scenario_token, features in scenarios.items() if not feature_names - features]
    return scenario_cache_paths

def find_last_checkpoint_in_dir(group_dir: pathlib.Path, experiment_uid: pathlib.Path) -> Optional[pathlib.Path]:
    """
    Extract last checkpoint from a experiment
    :param group_dir: defined by ${group}/${experiment_name}/${job_name} from hydra
    :param experiment_uid: date time which will be used as ${group}/${experiment_name}/${job_name}/${experiment_uid}
    return checkpoint dir if existent, otherwise None
    """
    last_checkpoint_dir = group_dir / experiment_uid / 'checkpoints'
    if not last_checkpoint_dir.exists():
        return None
    checkpoints = list(last_checkpoint_dir.iterdir())
    last_epoch = max((int(path.stem[6:]) for path in checkpoints if path.stem.startswith('epoch')))
    return last_checkpoint_dir / f'epoch={last_epoch}.ckpt'

def extract_last_checkpoint_from_experiment(output_dir: pathlib.Path, date_format: str) -> Optional[pathlib.Path]:
    """
    Extract last checkpoint from latest experiment
    :param output_dir: of the current experiment, we assume that parent folder has previous experiments of the same type
    :param date_format: format time used for folders
    :return path to latest checkpoint, return None in case no checkpoint was found
    """
    date_times = [datetime.strptime(dir.name, date_format) for dir in output_dir.parent.iterdir() if dir != output_dir]
    date_times.sort(reverse=True)
    for date_time in date_times:
        checkpoint = find_last_checkpoint_in_dir(output_dir.parent, pathlib.Path(date_time.strftime(date_format)))
        if checkpoint:
            return checkpoint
    return None

class TestUtilsCheckpoint(unittest.TestCase):
    """Test checkpoint utils methods."""

    def setUp(self) -> None:
        """Setup test attributes."""
        self.group = Path('exp')
        self.experiment_uid = Path('2023.01.01.00.00.00')
        self.experiment = Path('experiment_name/job_name') / self.experiment_uid

    @patch.object(Path, 'exists', autospec=True, return_value=False)
    def test_find_last_checkpoint_in_dir_dir_unavailable(self, path_exists_mock: Mock) -> None:
        """Test 'find_last_checkpoint_in_dir' method when directory does not exist."""
        group_dir = self.group / self.experiment.parent
        result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
        self.assertIsNone(result)

    @patch.object(Path, 'exists', autospec=True, return_value=True)
    @patch.object(Path, 'iterdir', autospec=True, return_value=[Path('epoch=0.ckpt'), Path('epoch=1.ckpt')])
    def test_find_last_checkpoint_in_dir(self, path_iterdir_mock: Mock, path_exists_mock: Mock) -> None:
        """Test 'find_last_checkpoint_in_dir' method under typical use case."""
        group_dir = self.group / self.experiment.parent
        result = find_last_checkpoint_in_dir(group_dir, self.experiment_uid)
        expected = Path('exp/experiment_name/job_name/2023.01.01.00.00.00/checkpoints/epoch=1.ckpt')
        self.assertEqual(result, expected)

    @patch.object(Path, 'iterdir', autospec=True, return_value=[Path('2023.01.01.00.00.00'), Path('2023.01.01.00.00.01'), Path('2023.01.01.00.00.02')])
    @patch(f'{PATCH_PREFIX}.find_last_checkpoint_in_dir', autospec=True)
    def test_extract_last_checkpoint_from_experiment(self, find_last_checkpoint_in_dir_mock: Mock, path_iterdir_mock: Mock) -> None:
        """Test extract_last_checkpoint_from_experiment method."""
        output_dir = self.group / self.experiment
        date_format = '%Y.%m.%d.%H.%M.%S'
        _ = extract_last_checkpoint_from_experiment(output_dir, date_format)
        calls = [call(Path('exp/experiment_name/job_name'), Path('2023.01.01.00.00.02'))]
        find_last_checkpoint_in_dir_mock.assert_has_calls(calls)

def setUp(self) -> None:
    """Setup test attributes."""
    self.group = Path('exp')
    self.experiment_uid = Path('2023.01.01.00.00.00')
    self.experiment = Path('experiment_name/job_name') / self.experiment_uid

class MockModel:
    """Mock model class"""

    def get_list_of_required_feature(self) -> List[Any]:
        """
        Mock get_list_of_required_feature function
        :return: mock list of features
        """
        return [MockFeatureBuilder()]

    def get_list_of_computed_target(self) -> List[Any]:
        """
        Mock get_list_of_computed_target function
        :return: mock list of targets
        """
        return [MockTargetBuilder()]

def get_list_of_required_feature(self) -> List[Any]:
    """
        Mock get_list_of_required_feature function
        :return: mock list of features
        """
    return [MockFeatureBuilder()]

class TestScenarioBuilder(unittest.TestCase):
    """Test update_distributed_optimizer_config function."""

    def setUp(self) -> None:
        """Setup test attributes."""
        self.num_scenarios = 5
        self.specified_feature_names = ['agents', 'trajectory', 'vector_map']
        self.mock_cache_path = 's3://mock_path'
        self.expected_s3_paths = sorted((Path(f'mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}') for i in range(5)))

    def _get_mock_get_s3_scenario_cache_with_scenario_type_patch(self) -> Callable[..., List[Any]]:
        """
        Gets mock get_s3_scenario_cache_patch function with scenario types.
        """

        def mock_get_s3_scenario_cache_with_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool, load_from_metadata: bool=True) -> List[Path]:
            """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
            return [Path('s3://mock_vehicle_log_123/mock_scenario_type_A/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_scenario_type_B/mock_token') for _ in range(5)]
        return mock_get_s3_scenario_cache_with_scenario_type

    def _get_mock_get_s3_scenario_cache_without_scenario_type_patch(self) -> Callable[..., List[Any]]:
        """
        Gets mock get_s3_scenario_cache_patch function without scenario types.
        """

        def mock_get_s3_scenario_cache_without_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool) -> List[Path]:
            """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
            return [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)]
        return mock_get_s3_scenario_cache_without_scenario_type

    def _get_mock_check_s3_path_exists_patch(self) -> Callable[[str], bool]:
        """
        Gets mock get_s3_scenario_cache_patch function without scenario types.
        """

        def mock_check_s3_path_exists(cache_path: str) -> bool:
            """
            Mock function for check_s3_path_exists
            :param cache_path: Parent of cache path
            :return: True
            """
            return True
        return mock_check_s3_path_exists

    def _get_mock_expand_s3_dir(self) -> Callable[[str], List[str]]:
        """
        Gets mock expand_s3_dir function.
        """

        def mock_expand_s3_dir(cache_path: str) -> List[str]:
            """
            Mock function for expand_s3_dir.
            :param cache_path: S3 cache path.
            :return: List of mock s3 file paths fetched directly from s3 cache path provided.
            """
            return [f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin' for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]
        return mock_expand_s3_dir

    def _get_mock_fail_to_get_cache_metadata_paths(self) -> Callable[[Path, str], List[str]]:
        """
        Gets mock get_cache_metadata_paths function.
        """

        def mock_fail_to_get_cache_metadata_paths(s3_key: Path, s3_bucket: str) -> List[str]:
            """
            Mock function for get_cache_metadata_paths.
            :param s3_key: S3 cache key.
            :param s3_bucket: S3 cache bucket.
            :return: List of mock s3 metadata file paths fetched from s3 cache path provided.
            """
            return []
        return mock_fail_to_get_cache_metadata_paths

    def _get_mock_worker_map(self) -> Callable[..., List[Any]]:
        """
        Gets mock worker_map function.
        """

        def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
            """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
            return fn(input_objects)
        return mock_worker_map

    def _get_mock_read_cache_metadata(self) -> Callable[..., List[CacheMetadataEntry]]:
        """
        Gets mock read_cache_metadata function.
        """

        def mock_read_cache_metadata(cache_path: Path, metadata_filenames: List[str], worker: WorkerPool) -> List[CacheMetadataEntry]:
            """
            Mock function for read_cache_metadata
            :param cache_path: Path to s3 cache.
            :param metadata_filenames: Filenames of the metadata csv files.
            :return: List of CacheMetadataEntry
            """
            return [CacheMetadataEntry(f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin') for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]
        return mock_read_cache_metadata

    def test_is_valid_token(self) -> None:
        """
        Test that scenario token validation works.
        """
        self.assertFalse(is_valid_token('a'))
        self.assertFalse(is_valid_token(3))
        self.assertTrue(is_valid_token('48681125850853e4'))

    def test_extract_and_filter_scenarios_from_cache(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['mock_scenario_type_A']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_with_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            scenarios = extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)
            msg = f'Expected number of scenarios to be {self.num_scenarios} but got {len(scenarios)}'
            self.assertEqual(len(scenarios), self.num_scenarios, msg=msg)

    def test_extract_and_filter_scenarios_from_cache_when_cache_path_has_no_scenario_type(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type when it doesn't exist in the cache path.
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['mock_scenario_type_A']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_without_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            with self.assertRaises(AssertionError):
                extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)

    def test_extract_and_filter_scenarios_from_cache_when_specified_scenario_type_does_not_exist(self) -> None:
        """
        Test extracting the scenarios from cache and filtering by scenario type when specified scenario type does not exist.
        """
        mock_cfg = Mock(DictConfig)
        cache = Mock()
        cache.cache_path = 's3://mock_path'
        scenario_filter = Mock()
        scenario_filter.scenario_types = ['nonexistent_scenario_type']
        mock_cfg.cache = cache
        mock_cfg.scenario_filter = scenario_filter
        mock_worker = Mock(WorkerPool)
        mock_model = MockModel()
        mock_model = cast(TorchModuleWrapper, mock_model)
        mock_worker_map = self._get_mock_worker_map()
        mock_get_s3_scenario_cache = self._get_mock_get_s3_scenario_cache_with_scenario_type_patch()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.worker_map', mock_worker_map), mock.patch('nuplan.planning.script.builders.scenario_builder.get_s3_scenario_cache', mock_get_s3_scenario_cache):
            with self.assertRaises(AssertionError):
                extract_scenarios_from_cache(mock_cfg, mock_worker, mock_model)

    def test_get_s3_scenario_cache(self) -> None:
        """
        Test get_s3_scenario_cache and ensure that it returns the correct format of cache paths.
        """
        mock_cache_path = self.mock_cache_path
        mock_feature_names = set(self.specified_feature_names)
        mock_worker = Mock(WorkerPool)
        mock_expand_s3_dir = self._get_mock_expand_s3_dir()
        mock_check_s3_path_exists = self._get_mock_check_s3_path_exists_patch()
        mock_read_cache_metadata = self._get_mock_read_cache_metadata()
        mock_fail_to_get_cache_metadata_paths = self._get_mock_fail_to_get_cache_metadata_paths()
        with mock.patch('nuplan.planning.script.builders.scenario_builder.expand_s3_dir', mock_expand_s3_dir), mock.patch('nuplan.planning.script.builders.scenario_builder.check_s3_path_exists', mock_check_s3_path_exists), mock.patch('nuplan.planning.script.builders.scenario_builder.read_cache_metadata', mock_read_cache_metadata), mock.patch('nuplan.planning.script.builders.scenario_builder.get_cache_metadata_paths', mock_fail_to_get_cache_metadata_paths):
            scenario_cache_paths = get_s3_scenario_cache(mock_cache_path, mock_feature_names, mock_worker)
            msg = f'Expected S3 cache paths to be {self.expected_s3_paths} but got {scenario_cache_paths}'
            self.assertEqual(scenario_cache_paths, self.expected_s3_paths, msg=msg)

def mock_get_s3_scenario_cache_with_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool, load_from_metadata: bool=True) -> List[Path]:
    """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
    return [Path('s3://mock_vehicle_log_123/mock_scenario_type_A/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_scenario_type_B/mock_token') for _ in range(5)]

def mock_get_s3_scenario_cache_without_scenario_type(cache_path: str, feature_names: List[Any], worker: WorkerPool) -> List[Path]:
    """
            Mock function for get_s3_scenario_cache
            :param cache_path: Parent of cache path
            :param feature_names: List of feature names
            :return: Mock cache paths
            """
    return [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)] + [Path('s3://mock_vehicle_log_123/mock_token') for _ in range(5)]

def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
    """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
    return fn(input_objects)

def mock_read_cache_metadata(cache_path: Path, metadata_filenames: List[str], worker: WorkerPool) -> List[CacheMetadataEntry]:
    """
            Mock function for read_cache_metadata
            :param cache_path: Path to s3 cache.
            :param metadata_filenames: Filenames of the metadata csv files.
            :return: List of CacheMetadataEntry
            """
    return [CacheMetadataEntry(f'{cache_path}/mock_vehicle_log_123/mock_scenario_type_A/mock_token_{i}/{feature_name}.bin') for i in range(5) for feature_name in ['agents', 'trajectory', 'vector_map']]

class TestTrainVectorModel(SkeletonTestTrain):
    """
    Test experiments: simple_vector_model, vector_model
    """

    def test_open_loop_training_simple_vector_model(self) -> None:
        """
        Tests simple vector model training in open loop.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_simple_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1'])
            main(cfg)

    def test_open_loop_training_vector_model(self) -> None:
        """
        Tests vector model training in open loop.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[self.search_path, *self.default_overrides, 'py_func=train', '+training=training_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'model.num_res_blocks=1', 'model.num_attention_layers=1', 'model.feature_dim=8', 'lightning.trainer.params.max_epochs=1'])
            main(cfg)

def test_open_loop_training_simple_vector_model(self) -> None:
    """
        Tests simple vector model training in open loop.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_simple_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1'])
        main(cfg)

def test_open_loop_training_vector_model(self) -> None:
    """
        Tests vector model training in open loop.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[self.search_path, *self.default_overrides, 'py_func=train', '+training=training_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'model.num_res_blocks=1', 'model.num_attention_layers=1', 'model.feature_dim=8', 'lightning.trainer.params.max_epochs=1'])
        main(cfg)

class TestRunResultProcessor(unittest.TestCase):
    """Test ResultProcessor script."""

    def test_is_submission_successful(self) -> None:
        """Tests that is_submission_successful utility function is working as expected."""
        challenge_names = ['challenge_1', 'challenge_2']
        temp_dirs = []
        temp_files = []
        with TemporaryDirectory() as tmpdir:
            for _ in challenge_names:
                temp_files.append(NamedTemporaryFile(dir=tmpdir))
                sub_tmpdir = TemporaryDirectory(dir=tmpdir)
                temp_dirs.append(sub_tmpdir)
                for instance in range(NUM_INSTANCES_PER_CHALLENGE):
                    temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
                    temp_files.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed_not.txt'))
            self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
            extra_completed_at_root = NamedTemporaryFile(dir=tmpdir, suffix='_completed.txt')
            self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
            extra_completed_at_root.close()
            extra_completed_at_challenge_dirs = []
            for sub_tmpdir in temp_dirs:
                extra_completed_at_challenge_dirs.append(NamedTemporaryFile(dir=sub_tmpdir.name, suffix='_completed.txt'))
            self.assertFalse(is_submission_successful(challenge_names, Path(tmpdir)))
            for item in extra_completed_at_challenge_dirs:
                item.close()
            self.assertTrue(is_submission_successful(challenge_names, Path(tmpdir)))
            for item in temp_files:
                item.close()

    def test_list_subdirs_filtered(self) -> None:
        """Tests listing of filtered files in subdirectories."""
        expected_found = []
        temporary_files = []
        with TemporaryDirectory() as tmpdir:
            with TemporaryDirectory(dir=tmpdir) as sub_tmpdir:
                file1 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.yes')
                file2 = NamedTemporaryFile(dir=tmpdir, suffix='.yes')
                rubbish1 = NamedTemporaryFile(dir=tmpdir, suffix='.no')
                rubbish2 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.no')
                temporary_files.extend([file1, file2, rubbish1, rubbish2])
                expected_found.extend([file1.name, file2.name])
                paths = list_subdirs_filtered(Path(tmpdir), regex_pattern=re.compile('\\.yes'))
                self.assertEqual(set(expected_found), set(paths))
                for temp_file in temporary_files:
                    temp_file.close()

def test_list_subdirs_filtered(self) -> None:
    """Tests listing of filtered files in subdirectories."""
    expected_found = []
    temporary_files = []
    with TemporaryDirectory() as tmpdir:
        with TemporaryDirectory(dir=tmpdir) as sub_tmpdir:
            file1 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.yes')
            file2 = NamedTemporaryFile(dir=tmpdir, suffix='.yes')
            rubbish1 = NamedTemporaryFile(dir=tmpdir, suffix='.no')
            rubbish2 = NamedTemporaryFile(dir=sub_tmpdir, suffix='.no')
            temporary_files.extend([file1, file2, rubbish1, rubbish2])
            expected_found.extend([file1.name, file2.name])
            paths = list_subdirs_filtered(Path(tmpdir), regex_pattern=re.compile('\\.yes'))
            self.assertEqual(set(expected_found), set(paths))
            for temp_file in temporary_files:
                temp_file.close()

class TestRunParallelWorker(SkeletonTestSimulation):
    """Test running parallel workers in simulation."""

    def test_worker_parallel(self) -> None:
        """
        Sanity test parallel worker.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=single_machine_thread_pool', 'scenario_filter.limit_total_scenarios=2', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
            main(cfg)

def test_worker_parallel(self) -> None:
    """
        Sanity test parallel worker.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=single_machine_thread_pool', 'scenario_filter.limit_total_scenarios=2', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
        main(cfg)

class TestRunSimulation(SkeletonTestSimulation):
    """Test running main simulation."""

    def test_run_simulation(self) -> None:
        """
        Sanity test for passing planner as argument to run_simulation
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'observation=box_observation', 'ego_controller=log_play_back_controller', 'experiment_name=simulation_test'])
            planner_cfg = cfg.planner
            planner = build_planners(planner_cfg, MockAbstractScenario())
            OmegaConf.set_struct(cfg, False)
            cfg.pop('planner')
            OmegaConf.set_struct(cfg, True)
            run_simulation(cfg, planner)

def test_run_simulation(self) -> None:
    """
        Sanity test for passing planner as argument to run_simulation
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'observation=box_observation', 'ego_controller=log_play_back_controller', 'experiment_name=simulation_test'])
        planner_cfg = cfg.planner
        planner = build_planners(planner_cfg, MockAbstractScenario())
        OmegaConf.set_struct(cfg, False)
        cfg.pop('planner')
        OmegaConf.set_struct(cfg, True)
        run_simulation(cfg, planner)

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

class TestRunRayWorker(SkeletonTestSimulation):
    """Test running ray workers in simulation."""

    def test_ray_worker(self) -> None:
        """
        Sanity test for ray worker.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=ray_distributed', 'worker.debug_mode=true', 'scenario_filter.limit_total_scenarios=2', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
            main(cfg)

def test_ray_worker(self) -> None:
    """
        Sanity test for ray worker.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=ray_distributed', 'worker.debug_mode=true', 'scenario_filter.limit_total_scenarios=2', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
        main(cfg)

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

class TestRunSubmissionPlanner(SkeletonTestSimulation):
    """Test running main submission planner."""

    @patch('nuplan.planning.script.run_submission_planner.SubmissionPlanner', autospec=True)
    def test_run_submission_planner(self, mock_submission_planner: Mock) -> None:
        """
        Sanity test to make sure hydra is setup correctly for run_submission_planner.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=['planner=simple_planner'])
            main(cfg)
            mock_submission_planner.assert_called_once()

@patch('nuplan.planning.script.run_submission_planner.SubmissionPlanner', autospec=True)
def test_run_submission_planner(self, mock_submission_planner: Mock) -> None:
    """
        Sanity test to make sure hydra is setup correctly for run_submission_planner.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=['planner=simple_planner'])
        main(cfg)
        mock_submission_planner.assert_called_once()

class TestTrain(SkeletonTestTrain):
    """
    Test main training entry point using combinations of models, datasets, filters etc.
    """

    def test_raster_model_overfitting(self) -> None:
        """
        Tests raster model overfitting in open loop.
        """
        loss_threshold = 2.0
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'log_config=false', 'py_func=train', '+training=training_raster_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=15', 'splitter=nuplan', 'optimizer.lr=0.01', 'lightning.trainer.overfitting.enable=true', 'lightning.trainer.overfitting.params.max_epochs=200', 'data_loader.params.batch_size=2', 'data_loader.params.num_workers=2'])
            engine = main(cfg)
            self.assertLessEqual(engine.trainer.callback_metrics['loss/train_loss'], loss_threshold)

    def test_urban_driver_open_loop_model_overfitting(self) -> None:
        """
        Tests urban_driver_open_loop model overfitting in open loop.
        """
        loss_threshold = 2.0
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'log_config=false', 'py_func=train', '+training=training_urban_driver_open_loop_model', 'data_augmentation=[]', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=15', 'splitter=nuplan', 'optimizer=adamw', 'optimizer.lr=1.25e-5', 'lightning.trainer.overfitting.enable=true', 'lightning.trainer.overfitting.params.max_epochs=300', 'data_loader.params.batch_size=1', 'data_loader.params.num_workers=2'])
            engine = main(cfg)
            self.assertLessEqual(engine.trainer.callback_metrics['loss/train_loss'], loss_threshold)

def test_raster_model_overfitting(self) -> None:
    """
        Tests raster model overfitting in open loop.
        """
    loss_threshold = 2.0
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'log_config=false', 'py_func=train', '+training=training_raster_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=15', 'splitter=nuplan', 'optimizer.lr=0.01', 'lightning.trainer.overfitting.enable=true', 'lightning.trainer.overfitting.params.max_epochs=200', 'data_loader.params.batch_size=2', 'data_loader.params.num_workers=2'])
        engine = main(cfg)
        self.assertLessEqual(engine.trainer.callback_metrics['loss/train_loss'], loss_threshold)

def test_urban_driver_open_loop_model_overfitting(self) -> None:
    """
        Tests urban_driver_open_loop model overfitting in open loop.
        """
    loss_threshold = 2.0
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'log_config=false', 'py_func=train', '+training=training_urban_driver_open_loop_model', 'data_augmentation=[]', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=15', 'splitter=nuplan', 'optimizer=adamw', 'optimizer.lr=1.25e-5', 'lightning.trainer.overfitting.enable=true', 'lightning.trainer.overfitting.params.max_epochs=300', 'data_loader.params.batch_size=1', 'data_loader.params.num_workers=2'])
        engine = main(cfg)
        self.assertLessEqual(engine.trainer.callback_metrics['loss/train_loss'], loss_threshold)

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

class TestDataLoader(unittest.TestCase):
    """
    Tests data loading functionality
    """

    def setUp(self) -> None:
        """Setup hydra config."""
        seed = 10
        pl.seed_everything(seed, workers=True)
        main_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(main_path, '../config/training/')
        self.group = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.group.name, 'cache_path')

    def tearDown(self) -> None:
        """Remove temporary folder."""
        self.group.cleanup()

    @staticmethod
    def validate_cfg(cfg: DictConfig) -> None:
        """Validate hydra config."""
        update_config_for_training(cfg)
        OmegaConf.set_struct(cfg, False)
        cfg.scenario_filter.limit_total_scenarios = 0.001
        cfg.data_loader.datamodule.train_fraction = 1.0
        cfg.data_loader.datamodule.val_fraction = 1.0
        cfg.data_loader.datamodule.test_fraction = 1.0
        cfg.data_loader.params.batch_size = 2
        cfg.data_loader.params.num_workers = 2
        cfg.data_loader.params.pin_memory = False
        OmegaConf.set_struct(cfg, True)

    @staticmethod
    def _iterate_dataloader(dataloader: torch.utils.data.DataLoader) -> None:
        """
        Iterate a fixed number of batches of the dataloader.
        :param dataloader: Data loader to iterate.
        """
        num_batches = 5
        dataloader_iter = iter(dataloader)
        iterations = min(len(dataloader), num_batches)
        for _ in range(iterations):
            next(dataloader_iter)

    def _run_dataloader(self, cfg: DictConfig) -> None:
        """
        Test that the training dataloader can be iterated without errors.
        :param cfg: Hydra config.
        """
        worker = build_worker(cfg)
        lightning_module_wrapper = build_torch_module_wrapper(cfg.model)
        datamodule = build_lightning_datamodule(cfg, worker, lightning_module_wrapper)
        datamodule.setup('fit')
        datamodule.setup('test')
        train_dataloader = datamodule.train_dataloader()
        val_dataloader = datamodule.val_dataloader()
        test_dataloader = datamodule.test_dataloader()
        for dataloader in [train_dataloader, val_dataloader]:
            assert len(dataloader) > 0
            self._iterate_dataloader(dataloader)
        self._iterate_dataloader(test_dataloader)

    def test_dataloader(self) -> None:
        """Test dataloader on nuPlan DB."""
        log_names = ['2021.07.16.20.45.29_veh-35_01095_01486', '2021.08.17.18.54.02_veh-45_00665_01065', '2021.06.08.12.54.54_veh-26_04262_04732', '2021.10.06.07.26.10_veh-52_00006_00398']
        overrides = ['scenario_builder=nuplan_mini', 'worker=sequential', 'splitter=nuplan', f'scenario_filter.log_names={log_names}', f'group={self.group.name}', f'cache.cache_path={self.cache_path}', 'output_dir=${group}/${experiment}', 'scenario_type_weights=default_scenario_type_weights']
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*overrides, '+training=training_raster_model'])
            self.validate_cfg(cfg)
            self._run_dataloader(cfg)

def setUp(self) -> None:
    """Setup hydra config."""
    seed = 10
    pl.seed_everything(seed, workers=True)
    main_path = os.path.dirname(os.path.realpath(__file__))
    self.config_path = os.path.join(main_path, '../config/training/')
    self.group = tempfile.TemporaryDirectory()
    self.cache_path = os.path.join(self.group.name, 'cache_path')

def tearDown(self) -> None:
    """Remove temporary folder."""
    self.group.cleanup()

def test_dataloader(self) -> None:
    """Test dataloader on nuPlan DB."""
    log_names = ['2021.07.16.20.45.29_veh-35_01095_01486', '2021.08.17.18.54.02_veh-45_00665_01065', '2021.06.08.12.54.54_veh-26_04262_04732', '2021.10.06.07.26.10_veh-52_00006_00398']
    overrides = ['scenario_builder=nuplan_mini', 'worker=sequential', 'splitter=nuplan', f'scenario_filter.log_names={log_names}', f'group={self.group.name}', f'cache.cache_path={self.cache_path}', 'output_dir=${group}/${experiment}', 'scenario_type_weights=default_scenario_type_weights']
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*overrides, '+training=training_raster_model'])
        self.validate_cfg(cfg)
        self._run_dataloader(cfg)

class TestRunSequentialWorker(SkeletonTestSimulation):
    """Test running sequential workers in simulation."""

    def test_worker_sequential(self) -> None:
        """
        Sanity test for sequential worker.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=sequential', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
            main(cfg)

def test_worker_sequential(self) -> None:
    """
        Sanity test for sequential worker.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=sequential', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", '+simulation=open_loop_boxes'])
        main(cfg)

class TestRunChallenge(SkeletonTestSimulation):
    """Test main simulation entry point across different challenges."""

    def test_simulation_challenge_1(self) -> None:
        """
        Sanity check for challenge 1 simulation.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=single_machine_thread_pool', 'worker.use_process_pool=true', '+simulation=open_loop_boxes'])
            main(cfg)

def test_simulation_challenge_1(self) -> None:
    """
        Sanity check for challenge 1 simulation.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'worker=single_machine_thread_pool', 'worker.use_process_pool=true', '+simulation=open_loop_boxes'])
        main(cfg)

class TestRunMetricAggregator(SkeletonTestSimulation):
    """Test the run_metric_aggregator script."""

    def test_run_metric_aggregator_without_challenges(self) -> None:
        """Sanity test to run metric_aggregator script without any challenges."""
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', 'experiment_name=simulation_metric_aggregator_test'])
            run_simulation(cfg)
            exp_output_dir = deepcopy(cfg.output_dir)
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=METRIC_AGGREGATOR_CONFIG_NAME, overrides=[f'output_dir={exp_output_dir}', 'scenario_metric_paths=[]', 'metric_aggregator=[default_weighted_average]', 'challenges=[]'])
            run_metric_aggregator(cfg)
            metric_aggregator_output = Path(cfg.aggregator_save_path)
            aggregator_output_file_length = len(list(metric_aggregator_output.rglob('*')))
            self.assertEqual(aggregator_output_file_length, 1)

def test_run_metric_aggregator_without_challenges(self) -> None:
    """Sanity test to run metric_aggregator script without any challenges."""
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', 'experiment_name=simulation_metric_aggregator_test'])
        run_simulation(cfg)
        exp_output_dir = deepcopy(cfg.output_dir)
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=METRIC_AGGREGATOR_CONFIG_NAME, overrides=[f'output_dir={exp_output_dir}', 'scenario_metric_paths=[]', 'metric_aggregator=[default_weighted_average]', 'challenges=[]'])
        run_metric_aggregator(cfg)
        metric_aggregator_output = Path(cfg.aggregator_save_path)
        aggregator_output_file_length = len(list(metric_aggregator_output.rglob('*')))
        self.assertEqual(aggregator_output_file_length, 1)

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

class TestRunMetric(SkeletonTestSimulation):
    """Test running metrics only."""

    def test_run_simulation_fails_with_no_logs(self) -> None:
        """Sanity test to test that metric_runner fails to run when there is no simulation logs."""
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', f'simulation_log_main_path={self.tmp_dir.name}', 'experiment_name=simulation_no_metric_test'])
            with self.assertRaises(FileNotFoundError):
                run_metric(cfg)

    def test_run_simulation_logs(self) -> None:
        """Sanity test to run simulation logs by computing metrics only."""
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', 'run_metric=false', 'experiment_name=open_loop_boxes/simulation_metric_test', 'worker=sequential', 'main_callback=[time_callback]'])
            run_simulation(cfg)
            exp_output_dir = deepcopy(cfg.output_dir)
            OmegaConf.set_struct(cfg, False)
            cfg.simulation_log_main_path = exp_output_dir
            OmegaConf.set_struct(cfg, True)
            run_metric(cfg)
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=METRIC_AGGREGATOR_CONFIG_NAME, overrides=[f'output_dir={exp_output_dir}', "challenges=['open_loop_boxes']"])
            run_metric_aggregator(cfg)
            metric_aggregator_output = Path(cfg.aggregator_save_path)
            aggregator_output_file_length = len(list(metric_aggregator_output.rglob('*')))
            self.assertEqual(aggregator_output_file_length, 1)

def test_run_simulation_fails_with_no_logs(self) -> None:
    """Sanity test to test that metric_runner fails to run when there is no simulation logs."""
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', f'simulation_log_main_path={self.tmp_dir.name}', 'experiment_name=simulation_no_metric_test'])
        with self.assertRaises(FileNotFoundError):
            run_metric(cfg)

def test_run_simulation_logs(self) -> None:
    """Sanity test to run simulation logs by computing metrics only."""
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, '+simulation=open_loop_boxes', 'run_metric=false', 'experiment_name=open_loop_boxes/simulation_metric_test', 'worker=sequential', 'main_callback=[time_callback]'])
        run_simulation(cfg)
        exp_output_dir = deepcopy(cfg.output_dir)
        OmegaConf.set_struct(cfg, False)
        cfg.simulation_log_main_path = exp_output_dir
        OmegaConf.set_struct(cfg, True)
        run_metric(cfg)
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=METRIC_AGGREGATOR_CONFIG_NAME, overrides=[f'output_dir={exp_output_dir}', "challenges=['open_loop_boxes']"])
        run_metric_aggregator(cfg)
        metric_aggregator_output = Path(cfg.aggregator_save_path)
        aggregator_output_file_length = len(list(metric_aggregator_output.rglob('*')))
        self.assertEqual(aggregator_output_file_length, 1)

class TestTrainRasterModel(SkeletonTestTrain):
    """
    Test experiments: raster_model
    """

    def test_open_loop_training_raster_model(self) -> None:
        """
        Tests raster model training in open loop.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_raster_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'model.model_name=resnet18', 'model.pretrained=false', 'model.feature_builders.0.target_width=64', 'model.feature_builders.0.target_height=64', 'lightning.trainer.params.max_epochs=1', 'gpu=false'])
            main(cfg)

def test_open_loop_training_raster_model(self) -> None:
    """
        Tests raster model training in open loop.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_raster_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'model.model_name=resnet18', 'model.pretrained=false', 'model.feature_builders.0.target_width=64', 'model.feature_builders.0.target_height=64', 'lightning.trainer.params.max_epochs=1', 'gpu=false'])
        main(cfg)

class TestModelBuild(unittest.TestCase):
    """Test building model."""

    def setUp(self) -> None:
        """Setup hydra config."""
        main_path = os.path.dirname(os.path.realpath(__file__))
        self.config_path = os.path.join(main_path, '../config/training/')
        self.group = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.group.name, 'cache_path')
        model_path = pathlib.Path(__file__).parent.parent / 'config' / 'common' / 'model'
        self.model_cfg = []
        for model_module in model_path.iterdir():
            model_name = model_module.stem
            with initialize_config_dir(config_dir=self.config_path):
                cfg = compose(config_name=CONFIG_NAME, overrides=['+training=training_raster_model', f'model={model_name}', f'group={self.group.name}', f'cache.cache_path={self.cache_path}'])
                self.model_cfg.append(cfg)

    def tearDown(self) -> None:
        """Remove temporary folder."""
        self.group.cleanup()

    def validate_cfg(self, cfg: DictConfig) -> None:
        """
        Validate that a model can be constructed
        :param cfg: config for model which should be constructed
        """
        lightning_module_wrapper = build_torch_module_wrapper(cfg.model)
        self.assertIsInstance(lightning_module_wrapper, TorchModuleWrapper)
        for builder in lightning_module_wrapper.get_list_of_required_feature():
            self.assertIsInstance(builder, AbstractFeatureBuilder)
        for builder in lightning_module_wrapper.get_list_of_computed_target():
            self.assertIsInstance(builder, AbstractTargetBuilder)

    def test_all_common_models(self) -> None:
        """
        Test construction of all available common models
        """
        for cfg in self.model_cfg:
            self.validate_cfg(cfg)

def setUp(self) -> None:
    """Setup hydra config."""
    main_path = os.path.dirname(os.path.realpath(__file__))
    self.config_path = os.path.join(main_path, '../config/training/')
    self.group = tempfile.TemporaryDirectory()
    self.cache_path = os.path.join(self.group.name, 'cache_path')
    model_path = pathlib.Path(__file__).parent.parent / 'config' / 'common' / 'model'
    self.model_cfg = []
    for model_module in model_path.iterdir():
        model_name = model_module.stem
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=['+training=training_raster_model', f'model={model_name}', f'group={self.group.name}', f'cache.cache_path={self.cache_path}'])
            self.model_cfg.append(cfg)

def tearDown(self) -> None:
    """Remove temporary folder."""
    self.group.cleanup()

def test_all_common_models(self) -> None:
    """
        Test construction of all available common models
        """
    for cfg in self.model_cfg:
        self.validate_cfg(cfg)

class TestRunNuBoard(unittest.TestCase):
    """
    Test running main nuboard entry point.
    """

    def setUp(self) -> None:
        """Set up basic config."""
        main_path = os.path.dirname(os.path.realpath(__file__))
        self.simulation_config_path = os.path.join(main_path, '../config/simulation/')
        self.nuboard_config_path = os.path.join(main_path, '../config/nuboard/')
        self.tmp_dir = tempfile.TemporaryDirectory()
        if not os.getenv('NUPLAN_EXP_ROOT', None):
            os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
        self.simulation_overrides = ['log_config=false', 'scenario_builder=nuplan_mini', 'planner=simple_planner', 'scenario_filter=one_of_each_scenario_type', 'scenario_filter.limit_total_scenarios=2', 'exit_on_failure=true', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", f'group={self.tmp_dir.name}', 'output_dir=${group}/${experiment}']

    def tearDown(self) -> None:
        """Clean up."""
        if Path(self.tmp_dir.name).exists():
            self.tmp_dir.cleanup()
        if ray.is_initialized():
            ray.shutdown()

    def test_nuboard_incorrect_file(self) -> None:
        """
        Tests that the nuboard correctly recognizes incorrect file extensions.
        """
        with self.assertRaises(RuntimeError):
            with initialize_config_dir(config_dir=self.nuboard_config_path):
                cfg = compose(config_name=NUBOARD_CONFIG_NAME, overrides=['simulation_path=test.tmp'])
                nuboard_main(cfg)

    def test_nuboard_integration(self) -> None:
        """
        Sanity test for launching the nuboard using simulation results file.
        """
        with initialize_config_dir(config_dir=self.simulation_config_path):
            cfg = compose(config_name=SIMULATION_CONFIG_NAME, overrides=[*self.simulation_overrides, '+simulation=open_loop_boxes'])
            simulation_main(cfg)
        results_dir = Path(cfg.output_dir)
        simulation_dir = results_dir / 'simulation_log'
        planner_dir = list(simulation_dir.iterdir())[0]
        scenario_dir = list(planner_dir.iterdir())[0]
        log_dir = list(scenario_dir.iterdir())[0]
        scene_dir = list(log_dir.iterdir())[0]
        scene_file = list(scene_dir.iterdir())[0]
        nuboard_file = [file for file in results_dir.iterdir() if file.is_file() and file.suffix == '.nuboard'][0]
        self.assertTrue(scene_file.is_file())
        self.assertEqual(scene_file.suffix, '.xz')
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(TEST_TIMEOUT)
        try:
            with initialize_config_dir(config_dir=self.nuboard_config_path):
                cfg = compose(config_name=NUBOARD_CONFIG_NAME, overrides=[f'simulation_path={str(nuboard_file)}', 'port_number=4554'])
                nuboard_main(cfg)
        except Exception as exc:
            signal.alarm(0)
            self.assertTrue(isinstance(exc, TimeoutError))

def setUp(self) -> None:
    """Set up basic config."""
    main_path = os.path.dirname(os.path.realpath(__file__))
    self.simulation_config_path = os.path.join(main_path, '../config/simulation/')
    self.nuboard_config_path = os.path.join(main_path, '../config/nuboard/')
    self.tmp_dir = tempfile.TemporaryDirectory()
    if not os.getenv('NUPLAN_EXP_ROOT', None):
        os.environ['NUPLAN_EXP_ROOT'] = self.tmp_dir.name
    self.simulation_overrides = ['log_config=false', 'scenario_builder=nuplan_mini', 'planner=simple_planner', 'scenario_filter=one_of_each_scenario_type', 'scenario_filter.limit_total_scenarios=2', 'exit_on_failure=true', "selected_simulation_metrics='[ego_acceleration_statistics, ego_jerk_statistics]'", f'group={self.tmp_dir.name}', 'output_dir=${group}/${experiment}']

def tearDown(self) -> None:
    """Clean up."""
    if Path(self.tmp_dir.name).exists():
        self.tmp_dir.cleanup()
    if ray.is_initialized():
        ray.shutdown()

def test_nuboard_incorrect_file(self) -> None:
    """
        Tests that the nuboard correctly recognizes incorrect file extensions.
        """
    with self.assertRaises(RuntimeError):
        with initialize_config_dir(config_dir=self.nuboard_config_path):
            cfg = compose(config_name=NUBOARD_CONFIG_NAME, overrides=['simulation_path=test.tmp'])
            nuboard_main(cfg)

def test_nuboard_integration(self) -> None:
    """
        Sanity test for launching the nuboard using simulation results file.
        """
    with initialize_config_dir(config_dir=self.simulation_config_path):
        cfg = compose(config_name=SIMULATION_CONFIG_NAME, overrides=[*self.simulation_overrides, '+simulation=open_loop_boxes'])
        simulation_main(cfg)
    results_dir = Path(cfg.output_dir)
    simulation_dir = results_dir / 'simulation_log'
    planner_dir = list(simulation_dir.iterdir())[0]
    scenario_dir = list(planner_dir.iterdir())[0]
    log_dir = list(scenario_dir.iterdir())[0]
    scene_dir = list(log_dir.iterdir())[0]
    scene_file = list(scene_dir.iterdir())[0]
    nuboard_file = [file for file in results_dir.iterdir() if file.is_file() and file.suffix == '.nuboard'][0]
    self.assertTrue(scene_file.is_file())
    self.assertEqual(scene_file.suffix, '.xz')
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(TEST_TIMEOUT)
    try:
        with initialize_config_dir(config_dir=self.nuboard_config_path):
            cfg = compose(config_name=NUBOARD_CONFIG_NAME, overrides=[f'simulation_path={str(nuboard_file)}', 'port_number=4554'])
            nuboard_main(cfg)
    except Exception as exc:
        signal.alarm(0)
        self.assertTrue(isinstance(exc, TimeoutError))

class TestTrainUrbanDriverOpenLoopModel(SkeletonTestTrain):
    """
    Test experiments: urban_driver_open_loop_model
    """

    def test_open_loop_training_urban_driver_open_loop_model(self) -> None:
        """
        Tests urban_driver_open_loop model training in open loop.
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_urban_driver_open_loop_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=32', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1', 'cache.force_feature_computation=True'])
            main(cfg)

def test_open_loop_training_urban_driver_open_loop_model(self) -> None:
    """
        Tests urban_driver_open_loop model training in open loop.
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'py_func=train', '+training=training_urban_driver_open_loop_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=32', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1', 'cache.force_feature_computation=True'])
        main(cfg)

class TestTrainProfiling(SkeletonTestTrain):
    """
    Test that profiling gets generated
    """

    def test_simple_vector_model_profiling(self) -> None:
        """
        Tests that profiling file for training gets generated
        """
        with initialize_config_dir(config_dir=self.config_path):
            cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'enable_profiling=True', 'py_func=train', '+training=training_simple_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1'])
            main(cfg)
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, 'profiling', 'training.html')))

def test_simple_vector_model_profiling(self) -> None:
    """
        Tests that profiling file for training gets generated
        """
    with initialize_config_dir(config_dir=self.config_path):
        cfg = compose(config_name=CONFIG_NAME, overrides=[*self.default_overrides, 'enable_profiling=True', 'py_func=train', '+training=training_simple_vector_model', 'scenario_builder=nuplan_mini', 'scenario_filter.limit_total_scenarios=16', 'splitter=nuplan', 'lightning.trainer.params.max_epochs=1'])
        main(cfg)
    self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, 'profiling', 'training.html')))

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

def get_map_factory(self) -> AbstractMapFactory:
    """Implemented. See interface."""
    return MockMapFactory()

def download_file_if_necessary(data_root: str, potentially_remote_path: str, verbose: bool=False) -> str:
    """
    Downloads the db file if necessary.
    :param data_root: Path's data root.
    :param potentially_remote_path: The path from which to download the file.
    :param verbose: Verbosity level.
    :return: The local path for the file.
    """
    if os.path.exists(potentially_remote_path):
        return potentially_remote_path
    log_name = absolute_path_to_log_name(potentially_remote_path)
    download_name = log_name + '.db'
    os.makedirs(data_root, exist_ok=True)
    local_store = LocalStore(data_root)
    if not local_store.exists(download_name):
        blob_store = BlobStoreCreator.create_nuplandb(data_root, verbose=verbose)
        logger.info('DB path not found. Downloading to %s...' % download_name)
        start_time = time.time()
        remote_key = potentially_remote_path
        if not remote_key.startswith('s3://'):
            fixed_local_path = convert_legacy_nuplan_path_to_latest(potentially_remote_path)
            remote_key = infer_remote_key_from_local_path(fixed_local_path)
        content = blob_store.get(remote_key)
        local_store.put(download_name, content)
        logger.info('Downloading db file took %.2f seconds.' % (time.time() - start_time))
    return os.path.join(data_root, download_name)

def convert_legacy_nuplan_path_to_latest(legacy_path: str, nuplan_data_root: Optional[str]=None) -> str:
    """
    Converts known legacy nuPlan path formats to the latest version.
    Examples:
    - data_root: /data/sets/nuplan/
      in:  /data/sets/nuplan/nuplan-v1.1/mini/2021.09.16.15.12.03_veh-42_01037_01434.db
      out: /data/sets/nuplan/nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db
    :param legacy_path: Legacy path to convert.
    :param nuplan_data_root: Optional custom nuPlan data root directory. When None is supplied, the NUPLAN_DATA_ROOT environment variable will be used.
    :return: Converted input path.
    """
    if legacy_path.find('nuplan-v') == -1:
        raise ValueError('nuPlan DB path should contain db version in it (e.g: nuplan-v1.1)')
    if nuplan_data_root is None:
        nuplan_data_root = NUPLAN_DATA_ROOT
    prefix_removed = legacy_path.removeprefix(nuplan_data_root)
    prefix_removed = prefix_removed.lstrip('/')
    prefix_removed_path = Path(prefix_removed)
    if prefix_removed.find('splits') == -1:
        path_parts = list(prefix_removed_path.parts)
        version_directory_index = min((idx for idx, directory_name in enumerate(path_parts) if 'nuplan-v' in directory_name))
        path_parts.insert(version_directory_index + 1, 'splits')
        prefix_removed_path = Path('/'.join(path_parts))
    return_path = Path(nuplan_data_root) / prefix_removed_path
    return str(return_path)

def infer_remote_key_from_local_path(local_path: str, nuplan_data_root: Optional[str]=None) -> str:
    """
    Try to infer a file's remote key on s3 based on its local path.
    Examples:
    - nuplan_data_root: /data/sets/nuplan/
      in:  /data/sets/nuplan/nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db
      out: splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db
    :param local_path: Local path of the file.
    :param nuplan_data_root: Optional custom nuPlan data root directory. When None is supplied, the NUPLAN_DATA_ROOT environment variable will be used.
    :return: Inferred remote key.
    """
    if nuplan_data_root is None:
        nuplan_data_root = NUPLAN_DATA_ROOT
    remote_key = local_path.removeprefix(nuplan_data_root)
    remote_key = remote_key.lstrip('/')
    if remote_key.startswith('nuplan-v'):
        remote_key_as_path = Path(remote_key)
        remote_key_as_path = Path(*remote_key_as_path.parts[1:])
        remote_key = str(remote_key_as_path)
    return remote_key

def download_and_cache(key: str, local_store: LocalStore, remote_store: S3Store) -> Optional[BinaryIO]:
    """
    Downloads and cache the key given. This function assumes that the local and remotes stores are already configured.
    Data will be downloaded from the remote store's s3 bucket and saved relative to the data root of the local store.
    This method will initialize the scenario's blob store if it does not already exist.
    :param key: The key for which to grab the sensor data.
    :param local_store: Local blob store for loading blobs from local file system.
    :param remote_store: S3 blob store for loading blobs from AWS S3.
    :return: The sensor data.
    """
    if local_store.exists(key):
        return cast(BinaryIO, local_store.get(key))
    if remote_store is None:
        raise RuntimeError("Remote store is not set and key was not found locally. Try setting NUPLAN_DATA_STORE to 's3'.")
    try:
        blob = remote_store.get(key)
        local_store.put(key, blob)
        return cast(BinaryIO, local_store.get(key))
    except RuntimeError as error:
        logging.warning(f'Could not find sensor data locally or remotely. Returning None\nCause: {error}')
        return None

def load_point_cloud(lidar_pc: LidarPc, local_store: LocalStore, remote_store: S3Store) -> Optional[LidarPointCloud]:
    """
    Loads a point cloud given a database LidarPC object.
    :param lidar_pc: The lidar_pc for which to grab the point cloud.
    :param local_store: Local blob store for loading blobs from local file system.
    :param remote_store: S3 blob store for loading blobs from AWS S3.
    :return: The corresponding point cloud.
    """
    file_type = lidar_pc.filename.split('.')[-1]
    blob = download_and_cache(lidar_pc.filename, local_store, remote_store)
    return LidarPointCloud.from_buffer(blob, file_type) if blob is not None else None

def load_image(image: ImageDBRow.Image, local_store: LocalStore, remote_store: S3Store) -> Optional[Image]:
    """
    Loads an image given a database Image object.
    :param image: The image for which to grab the image.
    :param local_store: Local blob store for loading blobs from local file system.
    :param remote_store: S3 blob store for loading blobs from AWS S3.
    :return: The corresponding image.
    """
    blob = download_and_cache(image.filename_jpg, local_store, remote_store)
    return Image.from_buffer(blob) if blob is not None else None

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

@dataclass(frozen=True)
class FilterWrapper:
    """
    Generic filter wrapper that encapsulates the filter's function and metadata.
    """
    fn: Callable[[ScenarioDict], ScenarioDict]
    enable: bool
    name: str

    def run(self, scenario_dict: ScenarioDict) -> ScenarioDict:
        """
        Run the filter if enabled.
        :param scenario_dict: Input scenario dictionary.
        :return: Output scenario dictionary.
        """
        if not self.enable:
            return scenario_dict
        logger.debug(f'Running scenario filter {self.name}...')
        scenario_dict = self.fn(scenario_dict)
        logger.debug(f'Running scenario filter {self.name}...DONE')
        return scenario_dict

def run(self, scenario_dict: ScenarioDict) -> ScenarioDict:
    """
        Run the filter if enabled.
        :param scenario_dict: Input scenario dictionary.
        :return: Output scenario dictionary.
        """
    if not self.enable:
        return scenario_dict
    logger.debug(f'Running scenario filter {self.name}...')
    scenario_dict = self.fn(scenario_dict)
    logger.debug(f'Running scenario filter {self.name}...DONE')
    return scenario_dict

def get_db_filenames_from_load_path(load_path: str) -> List[str]:
    """
    Retrieve all log database filenames from a load path.
    The path can be either local or remote (S3).
    The path can represent either a single database filename (.db file) or a directory containing files.
    :param load_path: Load path, it can be a filename or list of filenames.
    :return: A list of all discovered log database filenames.
    """
    if load_path.endswith('.db'):
        if load_path.startswith('s3://'):
            assert check_s3_path_exists(load_path), f'S3 db path does not exist: {load_path}'
            os.environ['NUPLAN_DATA_ROOT_S3_URL'] = load_path.rstrip(Path(load_path).name)
        else:
            assert Path(load_path).is_file(), f'Local db path does not exist: {load_path}'
        db_filenames = [load_path]
    elif load_path.startswith('s3://'):
        db_filenames = expand_s3_dir(load_path, filter_suffix='.db')
        assert len(db_filenames) > 0, f'S3 dir does not contain any dbs: {load_path}'
        os.environ['NUPLAN_DATA_ROOT_S3_URL'] = load_path
    elif Path(load_path).expanduser().is_dir():
        db_filenames = [str(path) for path in sorted(Path(load_path).expanduser().iterdir()) if path.suffix == '.db']
    else:
        raise ValueError(f'Expected db load path to be file, dir or list of files/dirs, but got {load_path}')
    return db_filenames

def filter_fraction_lidarpc_tokens_in_set(scenario_dict: ScenarioDict, token_set_path: Path, fraction_threshold: float) -> ScenarioDict:
    """
    Filter out all scenarios from a nuplan ScenarioDict for whom the fraction of the scenario's lidarpc tokens
        in token_set is less than or equal to fraction_threshold (strictly less for fraction_threshold=1).
    :param scenario_dict: Dictionary that holds a list of scenarios for each scenario type.
    :param token_set_path: a path to List of lidarpc tokens from a Nuplan DB, stored as json.
    :param fraction_threshold: a float in [0, 1].
    :return: a Dictionary with the same structure as scenario dict, but in which all individual scenarios
        for whom the fraction of its tokens that are contained in token set is <= fraction_threshold
        (or < fraction_threshold if fraction_threshold is 1)
    """
    if not 0 <= fraction_threshold <= 1:
        raise ValueError('Fraction_threshold must be in [0,1].')
    with open(token_set_path, 'r') as token_file:
        token_list = json.load(token_file)
        if type(token_list) != list or type(token_list[0]) != str:
            raise ValueError('token_set_path does not point to a json-formatted list of strings.')
        token_set = set(token_list)

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
    for scenario_type in scenario_dict:
        scenario_dict[scenario_type] = list(filter(lambda scenario: _are_lidarpc_tokens_in_set(scenario, token_set, fraction_threshold), scenario_dict[scenario_type]))
    return scenario_dict

class TestNuPlanScenarioUtilsIntegration(unittest.TestCase):
    """Test cases for nuplan_scenario_utils.py"""

    def setUp(self) -> None:
        """Will be run before every test."""
        self.data_root = Path('/data/sets/nuplan/nuplan-v1.1/splits/mini/')
        self.local_path = self.data_root / '2021.09.16.15.12.03_veh-42_01037_01434.db'

    def test_download_file_if_necessary_local_path(self) -> None:
        """
        Test that download_file_if_necessary works as expected with local path input.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
        self.assertFalse(os.path.exists(self.local_path))
        download_file_if_necessary(str(self.data_root), str(self.local_path))
        self.assertTrue(os.path.exists(self.local_path))

    def test_download_file_if_necessary_remote_path(self) -> None:
        """
        Test that download_file_if_necessary works as expected.
        WARNING: This test will attempt to remove and re-download 2021.09.16.15.12.03_veh-42_01037_01434.db from
                 the local splits folder.
        """
        if os.path.exists(self.local_path):
            os.remove(self.local_path)
        self.assertFalse(os.path.exists(self.local_path))
        remote_path = 's3://nuplan-production/nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        download_file_if_necessary(str(self.data_root), remote_path)
        self.assertTrue(os.path.exists(self.local_path))

def setUp(self) -> None:
    """Will be run before every test."""
    self.data_root = Path('/data/sets/nuplan/nuplan-v1.1/splits/mini/')
    self.local_path = self.data_root / '2021.09.16.15.12.03_veh-42_01037_01434.db'

class TestNuPlanScenarioIntegration(unittest.TestCase):
    """Integration test cases for nuplan_scenario.py"""

    def test_get_sensors_at_iteration_download(self) -> None:
        """
        Test that get_sensors_at_iteration is able to pull data from s3 correctly.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            scenario = get_test_nuplan_scenario(sensor_root=tmp_dir)
            sensor_path = Path(f'{tmp_dir}/{scenario.log_name}')

            def _get_image_paths() -> List[Path]:
                """:return: The expected path to the test image file."""
                return list(sensor_path.joinpath(f'{CameraChannel.CAM_R0.value}').glob('*.jpg'))

            def _get_pointcloud_paths() -> List[Path]:
                """:return: The expected path to the test pointcloud file."""
                return list(sensor_path.joinpath(f'{LidarChannel.MERGED_PC.value}').glob('*.pcd'))
            self.assertFalse(os.path.exists(sensor_path))
            sensors = scenario.get_sensors_at_iteration(0, [CameraChannel.CAM_R0, LidarChannel.MERGED_PC])
            self.assertIsNotNone(sensors.pointcloud)
            self.assertIsNotNone(sensors.images)
            self.assertTrue(os.path.exists(sensor_path))
            self.assertTrue(os.path.exists(_get_image_paths()[0]))
            self.assertTrue(os.path.exists(_get_pointcloud_paths()[0]))

def test_get_sensors_at_iteration_download(self) -> None:
    """
        Test that get_sensors_at_iteration is able to pull data from s3 correctly.
        """
    with tempfile.TemporaryDirectory() as tmp_dir:
        scenario = get_test_nuplan_scenario(sensor_root=tmp_dir)
        sensor_path = Path(f'{tmp_dir}/{scenario.log_name}')

        def _get_image_paths() -> List[Path]:
            """:return: The expected path to the test image file."""
            return list(sensor_path.joinpath(f'{CameraChannel.CAM_R0.value}').glob('*.jpg'))

        def _get_pointcloud_paths() -> List[Path]:
            """:return: The expected path to the test pointcloud file."""
            return list(sensor_path.joinpath(f'{LidarChannel.MERGED_PC.value}').glob('*.pcd'))
        self.assertFalse(os.path.exists(sensor_path))
        sensors = scenario.get_sensors_at_iteration(0, [CameraChannel.CAM_R0, LidarChannel.MERGED_PC])
        self.assertIsNotNone(sensors.pointcloud)
        self.assertIsNotNone(sensors.images)
        self.assertTrue(os.path.exists(sensor_path))
        self.assertTrue(os.path.exists(_get_image_paths()[0]))
        self.assertTrue(os.path.exists(_get_pointcloud_paths()[0]))

def _get_image_paths() -> List[Path]:
    """:return: The expected path to the test image file."""
    return list(sensor_path.joinpath(f'{CameraChannel.CAM_R0.value}').glob('*.jpg'))

def _get_pointcloud_paths() -> List[Path]:
    """:return: The expected path to the test pointcloud file."""
    return list(sensor_path.joinpath(f'{LidarChannel.MERGED_PC.value}').glob('*.pcd'))

class TestNuPlanScenarioUtils(unittest.TestCase):
    """Test cases for nuplan_scenario_utils.py"""

    def test_convert_legacy_nuplan_path_to_latest(self) -> None:
        """Test that convert_legacy_nuplan_path_to_latest works as expected."""
        legacy_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        legacy_path_str = str(legacy_path)
        expected_latest_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        expected_latest_path_str = str(expected_latest_path)
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str)
        self.assertEqual(expected_latest_path_str, actual_latest_path)
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, NUPLAN_DATA_ROOT)
        self.assertEqual(expected_latest_path_str, actual_latest_path)
        data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
        actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, data_root_without_slash)
        self.assertEqual(expected_latest_path_str, actual_latest_path)

    def test_convert_legacy_nuplan_path_to_latest_invalid_path(self) -> None:
        """Test that convert_legacy_nuplan_path_to_latest will throw if path does not contain version info."""
        invalid_legacy_path = Path(NUPLAN_DATA_ROOT) / 'mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        invalid_legacy_path_str = str(invalid_legacy_path)
        with self.assertRaises(ValueError):
            _ = convert_legacy_nuplan_path_to_latest(invalid_legacy_path_str)

    def test_infer_remote_key_from_local_path(self) -> None:
        """Test that infer_remote_key_from_local_path works as expected."""
        local_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        local_path_str = str(local_path)
        expected_remote_key = 'splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
        actual_remote_key = infer_remote_key_from_local_path(local_path_str)
        self.assertEqual(expected_remote_key, actual_remote_key)
        actual_remote_key = infer_remote_key_from_local_path(local_path_str, NUPLAN_DATA_ROOT)
        self.assertEqual(expected_remote_key, actual_remote_key)
        data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
        actual_remote_key = infer_remote_key_from_local_path(local_path_str, data_root_without_slash)
        self.assertEqual(expected_remote_key, actual_remote_key)

    @patch(f'{TEST_PATH}.LidarPointCloud.from_buffer')
    @patch(f'{TEST_PATH}.download_and_cache')
    def test_load_point_cloud(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
        """Test load_point_cloud."""
        mock_lidar_pc = Mock(spec=LidarPc)
        mock_lidar_pc.filename = 'pcd'
        mock_local_store = Mock(spec=LocalStore)
        mock_remote_store = Mock(spec=S3Store)
        mock_load_sensor.return_value = Mock()
        load_point_cloud(mock_lidar_pc, mock_local_store, mock_remote_store)
        mock_load_sensor.assert_called_with(mock_lidar_pc.filename, mock_local_store, mock_remote_store)
        mock_from_buffer.assert_called_with(mock_load_sensor.return_value, mock_lidar_pc.filename)

    @patch(f'{TEST_PATH}.Image.from_buffer')
    @patch(f'{TEST_PATH}.download_and_cache')
    def test_load_image(self, mock_load_sensor: Mock, mock_from_buffer: Mock) -> None:
        """Test load_point_cloud."""
        mock_image = Mock(spec=Image)
        mock_image.filename_jpg = 'image'
        mock_local_store = Mock(spec=LocalStore)
        mock_remote_store = Mock(spec=S3Store)
        mock_load_sensor.return_value = Mock()
        load_image(mock_image, mock_local_store, mock_remote_store)
        mock_load_sensor.assert_called_with(mock_image.filename_jpg, mock_local_store, mock_remote_store)
        mock_from_buffer.assert_called_with(mock_load_sensor.return_value)

    def test_download_and_cache(self) -> None:
        """Test download_and_cache."""
        mock_key = 'key'
        mock_image = Mock(spec=Image)
        mock_image.filename_jpg = 'image'
        mock_local_store = Mock(spec=LocalStore)
        mock_local_store.exists.side_effect = [True, False, False]
        mock_local_store.get.return_value = Mock(spec=BinaryIO)
        mock_local_store.put = Mock()
        mock_remote_store = Mock(spec=S3Store)
        mock_remote_store.get = Mock(return_value=Mock(spec=BinaryIO))
        blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
        self.assertEqual(mock_local_store.get.return_value, blob)
        self.assertTrue(isinstance(blob, BinaryIO))
        with self.assertRaises(RuntimeError):
            download_and_cache(mock_key, mock_local_store, None)
        blob = download_and_cache(mock_key, mock_local_store, mock_remote_store)
        mock_remote_store.get.assert_called_with(mock_key)
        mock_local_store.put.assert_called_with(mock_key, mock_remote_store.get.return_value)
        self.assertTrue(isinstance(blob, BinaryIO))

def test_convert_legacy_nuplan_path_to_latest(self) -> None:
    """Test that convert_legacy_nuplan_path_to_latest works as expected."""
    legacy_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    legacy_path_str = str(legacy_path)
    expected_latest_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    expected_latest_path_str = str(expected_latest_path)
    actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str)
    self.assertEqual(expected_latest_path_str, actual_latest_path)
    actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, NUPLAN_DATA_ROOT)
    self.assertEqual(expected_latest_path_str, actual_latest_path)
    data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
    actual_latest_path = convert_legacy_nuplan_path_to_latest(legacy_path_str, data_root_without_slash)
    self.assertEqual(expected_latest_path_str, actual_latest_path)

def test_convert_legacy_nuplan_path_to_latest_invalid_path(self) -> None:
    """Test that convert_legacy_nuplan_path_to_latest will throw if path does not contain version info."""
    invalid_legacy_path = Path(NUPLAN_DATA_ROOT) / 'mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    invalid_legacy_path_str = str(invalid_legacy_path)
    with self.assertRaises(ValueError):
        _ = convert_legacy_nuplan_path_to_latest(invalid_legacy_path_str)

def test_infer_remote_key_from_local_path(self) -> None:
    """Test that infer_remote_key_from_local_path works as expected."""
    local_path = Path(NUPLAN_DATA_ROOT) / 'nuplan-v1.1/splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    local_path_str = str(local_path)
    expected_remote_key = 'splits/mini/2021.09.16.15.12.03_veh-42_01037_01434.db'
    actual_remote_key = infer_remote_key_from_local_path(local_path_str)
    self.assertEqual(expected_remote_key, actual_remote_key)
    actual_remote_key = infer_remote_key_from_local_path(local_path_str, NUPLAN_DATA_ROOT)
    self.assertEqual(expected_remote_key, actual_remote_key)
    data_root_without_slash = NUPLAN_DATA_ROOT.rstrip('/')
    actual_remote_key = infer_remote_key_from_local_path(local_path_str, data_root_without_slash)
    self.assertEqual(expected_remote_key, actual_remote_key)

class TestNuPlanScenarioFilterUtils(unittest.TestCase):
    """
    Tests scenario filter utils for NuPlan
    """

    def _get_mock_scenario_dict(self) -> Dict[str, List[CachedScenario]]:
        """Gets mock scenario dict."""
        return {DEFAULT_SCENARIO_NAME: [CachedScenario(log_name='log/name', token=DEFAULT_SCENARIO_NAME, scenario_type=DEFAULT_SCENARIO_NAME) for i in range(500)], 'lane_following_with_lead': [CachedScenario(log_name='log/name', token='lane_following_with_lead', scenario_type='lane_following_with_lead') for i in range(80)], 'unprotected_left_turn': [CachedScenario(log_name='log/name', token='unprotected_left_turn', scenario_type='unprotected_left_turn') for i in range(120)]}

    def _get_mock_nuplan_scenario_dict_for_timestamp_filtering(self) -> Dict[str, List[CachedScenario]]:
        """Gets mock scenario dict."""
        mock_scenario_dict = {DEFAULT_SCENARIO_NAME: [Mock(NuPlanScenario) for _ in range(0, 100, 3)], 'lane_following_with_lead': [Mock(NuPlanScenario) for _ in range(0, 100, 6)], 'lane_following_without_lead': [Mock(NuPlanScenario) for _ in range(3)]}
        for i in range(0, len(mock_scenario_dict[DEFAULT_SCENARIO_NAME]) * int(1000000.0), int(1000000.0)):
            mock_scenario_dict[DEFAULT_SCENARIO_NAME][int(i / 1000000.0)]._initial_lidar_timestamp = i * 3
        for i in range(0, len(mock_scenario_dict['lane_following_with_lead']) * int(1000000.0), int(1000000.0)):
            mock_scenario_dict['lane_following_with_lead'][int(i / 1000000.0)]._initial_lidar_timestamp = i * 6
        mock_scenario_dict['lane_following_without_lead'][0]._initial_lidar_timestamp = 5.0 * int(1000000.0)
        mock_scenario_dict['lane_following_without_lead'][1]._initial_lidar_timestamp = 100.0 * int(1000000.0)
        mock_scenario_dict['lane_following_without_lead'][2]._initial_lidar_timestamp = 6.0 * int(1000000.0)
        return mock_scenario_dict

    def _get_mock_worker_map(self) -> Callable[..., List[Any]]:
        """
        Gets mock worker_map function.
        """

        def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
            """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
            return fn(input_objects)
        return mock_worker_map

    def test_filter_total_num_scenarios_int_max_scenarios_requires_removing_known_scenario_types(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 100
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
        self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_total_num_scenarios_int_max_scenarios_less_than_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 300
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
        self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
        self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_total_num_scenarios_int_max_scenarios_more_than_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an int, the actual number of scenarios,
        where the number of scenarios required is less than the total number of scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 800
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertDictEqual(final_scenario_dict, mock_scenario_dict)

    def test_filter_total_num_scenarios_float_requires_removing_known_scenario_types(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.2
        randomize = True
        final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertTrue(len(final_scenario_dict['lane_following_with_lead']) < len(mock_scenario_dict['lane_following_with_lead']))
        self.assertTrue(len(final_scenario_dict['unprotected_left_turn']) < len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

    def test_filter_total_num_scenarios_float_removes_only_default_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios as an float, the actual number of scenarios,
        where the number of scenarios required is requires reomving known scenario types.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.5
        randomize = True
        final_num_of_scenarios = int(limit_total_scenarios * sum((len(scenarios) for scenarios in mock_scenario_dict.values())))
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertNotEqual(final_scenario_dict[DEFAULT_SCENARIO_NAME], mock_scenario_dict[DEFAULT_SCENARIO_NAME])
        self.assertEqual(final_scenario_dict['lane_following_with_lead'], mock_scenario_dict['lane_following_with_lead'])
        self.assertEqual(final_scenario_dict['unprotected_left_turn'], mock_scenario_dict['unprotected_left_turn'])
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), final_num_of_scenarios)

    def test_remove_all_scenarios_int_limit_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0
        randomize = True
        with self.assertRaises(AssertionError):
            filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

    def test_remove_all_scenarios_float_limit_total_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to 0. This should raise an assertion error.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 0.0
        randomize = True
        with self.assertRaises(AssertionError):
            filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)

    def test_remove_exactly_all_default_scenarios(self) -> None:
        """
        Tests filter_total_num_scenarios with limit_total_scenarios equal to number of known scenarios.
        """
        mock_scenario_dict = self._get_mock_scenario_dict()
        limit_total_scenarios = 200
        randomize = True
        final_scenario_dict = filter_total_num_scenarios(mock_scenario_dict.copy(), limit_total_scenarios=limit_total_scenarios, randomize=randomize)
        self.assertTrue(DEFAULT_SCENARIO_NAME not in final_scenario_dict)
        self.assertEqual(len(final_scenario_dict['lane_following_with_lead']), len(mock_scenario_dict['lane_following_with_lead']))
        self.assertEqual(len(final_scenario_dict['unprotected_left_turn']), len(mock_scenario_dict['unprotected_left_turn']))
        self.assertEqual(sum((len(scenarios) for scenarios in final_scenario_dict.values())), limit_total_scenarios)

    def test_filter_scenarios_by_timestamp(self) -> None:
        """
        Tests filter_scenarios_by_timestamp with default threshold
        """
        mock_worker_map = self._get_mock_worker_map()
        mock_nuplan_scenario_dict = self._get_mock_nuplan_scenario_dict_for_timestamp_filtering()
        with patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.worker_map', mock_worker_map):
            final_scenario_dict = filter_scenarios_by_timestamp(mock_nuplan_scenario_dict.copy())
            self.assertEqual(len(final_scenario_dict['lane_following_with_lead']), len(mock_nuplan_scenario_dict['lane_following_with_lead']))
            self.assertEqual(len(final_scenario_dict[DEFAULT_SCENARIO_NAME]), len(mock_nuplan_scenario_dict[DEFAULT_SCENARIO_NAME]) * 0.5)
            self.assertEqual(len(final_scenario_dict['lane_following_without_lead']), len(mock_nuplan_scenario_dict['lane_following_without_lead']) - 1)

    def test_filter_fraction_lidarpc_tokens_in_set(self) -> None:
        """
        Test filter_fraction_lidarpc_tokens_in_set with fractional thresholds {0, 0.5, 1}.
        """
        alphabet = ['a', 'b', 'c', 'd', 'e', 'f']
        mock_nuplan_scenarios = []
        for start_letter in range(4):
            mock_nuplan_scenario = Mock(NuPlanScenario)
            mock_nuplan_scenario.get_scenario_tokens.return_value = set(alphabet[start_letter:start_letter + 3])
            mock_nuplan_scenarios.append(mock_nuplan_scenario)
        full_intersection_scenario, two_intersection_scenario, one_intersection_scenario, no_intersection_scenario = mock_nuplan_scenarios
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_json_path = Path(tmp_dir) / 'tmp_token_set.json'
            json.dump(['a', 'b', 'c'], open(tmp_json_path, 'w'))
            scenario_dict = {'on_pickup_dropoff': [no_intersection_scenario, one_intersection_scenario]}
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 0), {'on_pickup_dropoff': [one_intersection_scenario]})
            scenario_dict['on_pickup_dropoff'] = [one_intersection_scenario, two_intersection_scenario]
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 0.5), {'on_pickup_dropoff': [two_intersection_scenario]})
            scenario_dict['on_pickup_dropoff'] = [two_intersection_scenario, full_intersection_scenario]
            self.assertEqual(filter_fraction_lidarpc_tokens_in_set(scenario_dict, tmp_json_path, 1), {'on_pickup_dropoff': [full_intersection_scenario]})

    def test_filter_non_stationary_ego(self) -> None:
        """Test filter_non_stationary_ego with 0.5m displacement threshold"""
        stationary_ego_pudo_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.01, y=0.0))
        mobile_ego_pudo_scenario = MockAbstractScenario()
        scenario_dict = {'on_pickup_dropoff': [stationary_ego_pudo_scenario, mobile_ego_pudo_scenario]}
        filtered_scenario_dict = filter_non_stationary_ego(scenario_dict, minimum_threshold=0.5)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [mobile_ego_pudo_scenario])

    def test_filter_ego_starts(self) -> None:
        """Test filter_ego_starts with 0.1 m/s speed threshold"""
        slow_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=0.01, y=0.0), time_step=1)
        fast_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=1, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [slow_acceleration_scenario, fast_acceleration_scenario]}
        filtered_scenario_dict = filter_ego_starts(scenario_dict, speed_threshold=0.1, speed_noise_tolerance=0.1)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [fast_acceleration_scenario])

    def test_filter_ego_stops(self) -> None:
        """Test filter_ego_stops with 0.1 m/s speed threshold"""
        slow_deceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=1.0, y=0.0), fixed_acceleration=StateVector2D(x=-0.01, y=0.0), time_step=1)
        fast_deceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=1.0, y=0.0), fixed_acceleration=StateVector2D(x=-1 / 9, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [slow_deceleration_scenario, fast_deceleration_scenario]}
        filtered_scenario_dict = filter_ego_stops(scenario_dict, speed_threshold=0.1, speed_noise_tolerance=0.1)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [fast_deceleration_scenario])

    def test_ego_startstop_noise_tolerance(self) -> None:
        """Test filter_ego_starts with ego barely crossing speed threshold and noise tolerance higher than threshold"""
        fast_enough_acceleration_scenario = MockAbstractScenario(initial_velocity=StateVector2D(x=0.0, y=0.0), fixed_acceleration=StateVector2D(x=0.11, y=0.0), time_step=1)
        scenario_dict = {'on_pickup_dropoff': [fast_enough_acceleration_scenario]}
        filtered_scenario_dict = filter_ego_starts(scenario_dict, speed_threshold=1, speed_noise_tolerance=2)
        self.assertEqual(filtered_scenario_dict['on_pickup_dropoff'], [])

    def test_filter_ego_has_route(self) -> None:
        """
        Test filter_ego_has_route with one route roadblock in the VectorMap (True case),
        and with no route-intersecting roadblocks (False case).
        """
        map_radius = 35
        scenario = MockAbstractScenario()
        scenario_dict = {'on_pickup_dropoff': [scenario]}
        with patch('nuplan.planning.scenario_builder.nuplan_db.nuplan_scenario_filter_utils.get_neighbor_vector_map') as get_neighbor_vector_map:
            get_neighbor_vector_map.return_value = (None, None, None, None, LaneSegmentRoadBlockIDs(['a', 'b', 'c']))
            with patch.object(scenario, 'get_route_roadblock_ids') as get_route_roadblock_ids:
                get_route_roadblock_ids.return_value = ['d', 'e', 'a']
                self.assertEqual(filter_ego_has_route(scenario_dict, map_radius)['on_pickup_dropoff'], [scenario])
                get_route_roadblock_ids.return_value = ['d', 'e', 'f']
                self.assertEqual(filter_ego_has_route(scenario_dict, map_radius)['on_pickup_dropoff'], [])

def mock_worker_map(worker: WorkerPool, fn: Callable[..., List[Any]], input_objects: List[Any]) -> List[Any]:
    """
            Mock function for worker_map
            :param worker: Worker pool
            :param fn: Callable function
            :param input_objects: List of objects to be used as input
            :return: List of output objects
            """
    return fn(input_objects)

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

def __init__(self, api_server: str='https://eval.ai') -> None:
    """
        :param api_server: The URL of the api server.
        """
    self.CHALLENGE_PK = os.getenv('EVALAI_CHALLENGE_PK')
    self.EVALAI_AUTH_TOKEN = os.getenv('EVALAI_PERSONAL_AUTH_TOKEN')
    assert self.CHALLENGE_PK, 'Missing required environmental variable EVALAI_CHALLENGE_PK!'
    assert self.EVALAI_AUTH_TOKEN, 'Missing required environmental variable EVALAI_PERSONAL_AUTH_TOKEN!'
    self.EVALAI_API_SERVER = api_server

class LeaderBoardWriter:
    """Class to write to EvalAI leaderboard."""

    def __init__(self, cfg: DictConfig, submission_path: str) -> None:
        """
        :param cfg: Hydra configuration
        :param submission_path: Path to the directory where the submission files are stored.
        """
        self.contestant_id = cfg.contestant_id
        self.submission_id = cfg.submission_id
        self.output_dir = cfg.output_dir
        self.aggregator_save_path = cfg.aggregator_save_path
        self.challenges = cfg.challenges
        with open(f'{submission_path}/submission_metadata.json', 'r') as file:
            self.submission_metadata = json.load(file)
        try:
            with open(f'{submission_path}/stout.log', 'r') as stdout:
                self.stdout = stdout.read()
        except FileNotFoundError:
            logger.info('No STDOUT log file found')
            self.stdout = ''
        try:
            with open(f'{submission_path}/stderr.log', 'r') as stderr:
                self.stderr = stderr.read()
        except FileNotFoundError:
            logger.info('No STDERR log file found')
            self.stderr = ''
        self.interface = EvalaiInterface()

    def write_to_leaderboard(self, simulation_successful: bool) -> None:
        """
        Writes to the leaderboard
        :param simulation_successful: Whether the simulation was successful or not.
        """
        if simulation_successful:
            logger.info('Writing to leaderboard SUCCESSFUL simulation...')
            data = self._on_successful_submission()
        else:
            logger.info('Writing to leaderboard FAILED simulation...')
            data = self._on_failed_submission()
        self.interface.update_submission_data(data)

    def _on_failed_submission(self) -> Dict[str, str]:
        """
        Builds leaderboard message for failed simulations.
        :return: Message to mark submission as failed
        """
        submission_data = {'challenge_phase': self.submission_metadata.get('challenge_phase'), 'submission': self.submission_metadata.get('submission_id'), 'stdout': self.stdout, 'stderr': self.stderr, 'submission_status': 'FAILED', 'metadata': ''}
        return submission_data

    def _on_successful_submission(self) -> Dict[str, str]:
        """
        Builds leaderboard message for successful simulations.
        :return: Message to mark submission as successful, and to add metric values to leaderboard.
        """
        results: Dict[str, pd.DataFrame] = {}
        for challenge in self.challenges:
            challenge_result_files = Path(self.aggregator_save_path).glob('*.parquet')
            challenge_parquets = [pd.read_parquet(file) for file in challenge_result_files if challenge in str(file)]
            results[challenge] = challenge_parquets[0] if challenge_parquets else []
        result = json.dumps([{'split': 'data_split', 'show_to_participant': True, 'accuracies': read_metrics_from_results(results)}])
        submission_data = {'challenge_phase': self.submission_metadata.get('challenge_phase'), 'submission': self.submission_metadata.get('submission_id'), 'stdout': self.stdout, 'stderr': self.stderr, 'result': result, 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
        return submission_data

def __init__(self, cfg: DictConfig, submission_path: str) -> None:
    """
        :param cfg: Hydra configuration
        :param submission_path: Path to the directory where the submission files are stored.
        """
    self.contestant_id = cfg.contestant_id
    self.submission_id = cfg.submission_id
    self.output_dir = cfg.output_dir
    self.aggregator_save_path = cfg.aggregator_save_path
    self.challenges = cfg.challenges
    with open(f'{submission_path}/submission_metadata.json', 'r') as file:
        self.submission_metadata = json.load(file)
    try:
        with open(f'{submission_path}/stout.log', 'r') as stdout:
            self.stdout = stdout.read()
    except FileNotFoundError:
        logger.info('No STDOUT log file found')
        self.stdout = ''
    try:
        with open(f'{submission_path}/stderr.log', 'r') as stderr:
            self.stderr = stderr.read()
    except FileNotFoundError:
        logger.info('No STDERR log file found')
        self.stderr = ''
    self.interface = EvalaiInterface()

def _on_successful_submission(self) -> Dict[str, str]:
    """
        Builds leaderboard message for successful simulations.
        :return: Message to mark submission as successful, and to add metric values to leaderboard.
        """
    results: Dict[str, pd.DataFrame] = {}
    for challenge in self.challenges:
        challenge_result_files = Path(self.aggregator_save_path).glob('*.parquet')
        challenge_parquets = [pd.read_parquet(file) for file in challenge_result_files if challenge in str(file)]
        results[challenge] = challenge_parquets[0] if challenge_parquets else []
    result = json.dumps([{'split': 'data_split', 'show_to_participant': True, 'accuracies': read_metrics_from_results(results)}])
    submission_data = {'challenge_phase': self.submission_metadata.get('challenge_phase'), 'submission': self.submission_metadata.get('submission_id'), 'stdout': self.stdout, 'stderr': self.stderr, 'result': result, 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
    return submission_data

class TestEvalaiInterface(unittest.TestCase):
    """Tests interface class to EvalAI api."""

    @patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': '1234', 'EVALAI_PERSONAL_AUTH_TOKEN': 'authorization_token'})
    def setUp(self) -> None:
        """Inherited, see superclass."""
        self.evalai = EvalaiInterface('bounce_server')

    def test_initialization(self) -> None:
        """Checks that initialization works and fails as expected."""
        self.assertEqual(self.evalai.EVALAI_AUTH_TOKEN, 'authorization_token')
        self.assertEqual(self.evalai.CHALLENGE_PK, '1234')
        self.assertEqual(self.evalai.EVALAI_API_SERVER, 'bounce_server')
        with patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': ''}):
            with self.assertRaises(AssertionError):
                _ = EvalaiInterface('server')
        with patch.dict(os.environ, {'EVALAI_PERSONAL_AUTH_TOKEN': ''}):
            with self.assertRaises(AssertionError):
                _ = EvalaiInterface('server')

    @patch('requests.request', side_effect=mocked_put_request)
    def test_update_submission_data(self, mock_put: Mock) -> None:
        """Tests update submission with mock server."""
        test_payload = {'test': 'payload'}
        response = self.evalai.update_submission_data(test_payload)
        self.assertEqual(response, test_payload)
        expected_call = call(method='PUT', url='bounce_server/api/jobs/challenge/1234/update_submission/', headers={'Authorization': 'Bearer authorization_token'}, data=test_payload)
        self.assertEqual(response, test_payload)
        self.assertIn(expected_call, mock_put.call_args_list)
        self.assertEqual(len(mock_put.call_args_list), 1)

    def test_fail_on_missing_api(self) -> None:
        """Test failure of url generation on missing api."""
        with self.assertRaises(AssertionError):
            _ = self.evalai._format_url('missing_api')

@patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': '1234', 'EVALAI_PERSONAL_AUTH_TOKEN': 'authorization_token'})
def setUp(self) -> None:
    """Inherited, see superclass."""
    self.evalai = EvalaiInterface('bounce_server')

def test_initialization(self) -> None:
    """Checks that initialization works and fails as expected."""
    self.assertEqual(self.evalai.EVALAI_AUTH_TOKEN, 'authorization_token')
    self.assertEqual(self.evalai.CHALLENGE_PK, '1234')
    self.assertEqual(self.evalai.EVALAI_API_SERVER, 'bounce_server')
    with patch.dict(os.environ, {'EVALAI_CHALLENGE_PK': ''}):
        with self.assertRaises(AssertionError):
            _ = EvalaiInterface('server')
    with patch.dict(os.environ, {'EVALAI_PERSONAL_AUTH_TOKEN': ''}):
        with self.assertRaises(AssertionError):
            _ = EvalaiInterface('server')

class TestLeaderboardWriter(unittest.TestCase):
    """Tests for the LeaderboardWriter class."""

    @patch(f'{TEST_FILE}.EvalaiInterface')
    def setUp(self, mock_interface: Mock) -> None:
        """Sets up variables for testing."""
        self.mock_interface = mock_interface
        main_path = os.path.dirname(os.path.realpath(__file__))
        common_dir = 'file://' + os.path.join(main_path, '../../../planning/script/config/common')
        self.search_path = f'hydra.searchpath=[{common_dir}]'
        with initialize_config_dir(config_dir=CONFIG_PATH):
            cfg = compose(config_name=CONFIG_NAME, overrides=[self.search_path, 'contestant_id=contestant', 'submission_id=submission'])
            self.tmpdir = tempfile.TemporaryDirectory()
            self.addCleanup(self.tmpdir.cleanup)
            metadata = {'challenge_phase': 'phase', 'submission_id': 'my_sub'}
            with open(f'{self.tmpdir.name}/submission_metadata.json', 'w') as fp:
                json.dump(metadata, fp)
            self.leaderboard_writer = LeaderBoardWriter(cfg, self.tmpdir.name)

    def test_write_to_leaderboard(self) -> None:
        """Tests that writing to leaderboard calls the correct callbacks an api."""
        with patch.object(self.leaderboard_writer, '_on_successful_submission'):
            self.leaderboard_writer.write_to_leaderboard(simulation_successful=True)
            self.leaderboard_writer._on_successful_submission.assert_called_once()
            self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_successful_submission.return_value)
        self.mock_interface.reset_mock()
        with patch.object(self.leaderboard_writer, '_on_failed_submission'):
            self.leaderboard_writer.write_to_leaderboard(simulation_successful=False)
            self.leaderboard_writer._on_failed_submission.assert_called_once()
            self.leaderboard_writer.interface.update_submission_data.assert_called_once_with(self.leaderboard_writer._on_failed_submission.return_value)

    def test__on_failed_submission(self) -> None:
        """Tests message creation on failes submission callback."""
        expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'submission_status': 'FAILED', 'metadata': ''}
        data = self.leaderboard_writer._on_failed_submission()
        self.assertEqual(expected_data, data)

    def test__on_successful_submission(self) -> None:
        """Tests message creation on successful submission callback."""
        expected_data = {'challenge_phase': 'phase', 'submission': 'my_sub', 'stdout': '', 'stderr': '', 'result': '[{"split": "data_split", "show_to_participant": true, "accuracies": "results"}]', 'submission_status': 'FINISHED', 'metadata': {'status': 'finished'}}
        with patch(f'{TEST_FILE}.read_metrics_from_results') as reader:
            reader.return_value = 'results'
            data = self.leaderboard_writer._on_successful_submission()
            self.assertEqual(expected_data, data)

    def test_read_metrics_from_results(self) -> None:
        """Tests parsing of dataframes."""
        dataframes = {'open_loop_boxes': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [0], 'planner_expert_average_l2_error_within_bound': [1], 'planner_expert_final_l2_error_within_bound': [2], 'planner_miss_rate_within_bound': [3], 'planner_expert_average_heading_error_within_bound': [4], 'planner_expert_final_heading_error_within_bound': [5]}), 'closed_loop_nonreactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [10], 'ego_is_making_progress': [11], 'no_ego_at_fault_collisions': [12], 'drivable_area_compliance': [13], 'driving_direction_compliance': [14], 'ego_is_comfortable': [15], 'ego_progress_along_expert_route': [16], 'time_to_collision_within_bound': [17], 'speed_limit_compliance': [18]}), 'closed_loop_reactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [110], 'ego_is_making_progress': [111], 'no_ego_at_fault_collisions': [112], 'drivable_area_compliance': [113], 'driving_direction_compliance': [114], 'ego_is_comfortable': [115], 'ego_progress_along_expert_route': [116], 'time_to_collision_within_bound': [117], 'speed_limit_compliance': [118]})}
        metrics = read_metrics_from_results(dataframes)
        expected_metrics = {'ch1_overall_score': 0, 'ch1_avg_displacement_error_within_bound': 1, 'ch1_final_displacement_error_within_bound': 2, 'ch1_miss_rate_within_bound': 3, 'ch1_avg_heading_error_within_bound': 4, 'ch1_final_heading_error_within_bound': 5, 'ch2_overall_score': 10, 'ch2_ego_is_making_progress': 11, 'ch2_no_ego_at_fault_collisions': 12, 'ch2_drivable_area_compliance': 13, 'ch2_driving_direction_compliance': 14, 'ch2_ego_is_comfortable': 15, 'ch2_ego_progress_along_expert_route': 16, 'ch2_time_to_collision_within_bound': 17, 'ch2_speed_limit_compliance': 18, 'ch3_overall_score': 110, 'ch3_ego_is_making_progress': 111, 'ch3_no_ego_at_fault_collisions': 112, 'ch3_drivable_area_compliance': 113, 'ch3_driving_direction_compliance': 114, 'ch3_ego_is_comfortable': 115, 'ch3_ego_progress_along_expert_route': 116, 'ch3_time_to_collision_within_bound': 117, 'ch3_speed_limit_compliance': 118, 'combined_overall_score': 40.0}
        self.assertEqual(metrics, expected_metrics)

@patch(f'{TEST_FILE}.EvalaiInterface')
def setUp(self, mock_interface: Mock) -> None:
    """Sets up variables for testing."""
    self.mock_interface = mock_interface
    main_path = os.path.dirname(os.path.realpath(__file__))
    common_dir = 'file://' + os.path.join(main_path, '../../../planning/script/config/common')
    self.search_path = f'hydra.searchpath=[{common_dir}]'
    with initialize_config_dir(config_dir=CONFIG_PATH):
        cfg = compose(config_name=CONFIG_NAME, overrides=[self.search_path, 'contestant_id=contestant', 'submission_id=submission'])
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        metadata = {'challenge_phase': 'phase', 'submission_id': 'my_sub'}
        with open(f'{self.tmpdir.name}/submission_metadata.json', 'w') as fp:
            json.dump(metadata, fp)
        self.leaderboard_writer = LeaderBoardWriter(cfg, self.tmpdir.name)

def test_read_metrics_from_results(self) -> None:
    """Tests parsing of dataframes."""
    dataframes = {'open_loop_boxes': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [0], 'planner_expert_average_l2_error_within_bound': [1], 'planner_expert_final_l2_error_within_bound': [2], 'planner_miss_rate_within_bound': [3], 'planner_expert_average_heading_error_within_bound': [4], 'planner_expert_final_heading_error_within_bound': [5]}), 'closed_loop_nonreactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [10], 'ego_is_making_progress': [11], 'no_ego_at_fault_collisions': [12], 'drivable_area_compliance': [13], 'driving_direction_compliance': [14], 'ego_is_comfortable': [15], 'ego_progress_along_expert_route': [16], 'time_to_collision_within_bound': [17], 'speed_limit_compliance': [18]}), 'closed_loop_reactive_agents': pd.DataFrame.from_dict({'scenario': 'final_score', 'score': [110], 'ego_is_making_progress': [111], 'no_ego_at_fault_collisions': [112], 'drivable_area_compliance': [113], 'driving_direction_compliance': [114], 'ego_is_comfortable': [115], 'ego_progress_along_expert_route': [116], 'time_to_collision_within_bound': [117], 'speed_limit_compliance': [118]})}
    metrics = read_metrics_from_results(dataframes)
    expected_metrics = {'ch1_overall_score': 0, 'ch1_avg_displacement_error_within_bound': 1, 'ch1_final_displacement_error_within_bound': 2, 'ch1_miss_rate_within_bound': 3, 'ch1_avg_heading_error_within_bound': 4, 'ch1_final_heading_error_within_bound': 5, 'ch2_overall_score': 10, 'ch2_ego_is_making_progress': 11, 'ch2_no_ego_at_fault_collisions': 12, 'ch2_drivable_area_compliance': 13, 'ch2_driving_direction_compliance': 14, 'ch2_ego_is_comfortable': 15, 'ch2_ego_progress_along_expert_route': 16, 'ch2_time_to_collision_within_bound': 17, 'ch2_speed_limit_compliance': 18, 'ch3_overall_score': 110, 'ch3_ego_is_making_progress': 111, 'ch3_no_ego_at_fault_collisions': 112, 'ch3_drivable_area_compliance': 113, 'ch3_driving_direction_compliance': 114, 'ch3_ego_is_comfortable': 115, 'ch3_ego_progress_along_expert_route': 116, 'ch3_time_to_collision_within_bound': 117, 'ch3_speed_limit_compliance': 118, 'combined_overall_score': 40.0}
    self.assertEqual(metrics, expected_metrics)

def container_name_from_image_name(image: str) -> str:
    """
    Creates a valid container name from an image name.
    :param image: Docker image name
    :return: A valid container name
    """
    return '_'.join(['test', *image.split(':')[0].split('/')])

def _create_directories(local_path_name: str, directories: List[str]) -> None:
    """
    Creates directories from a list of directory names and a base path
    :param local_path_name: the base path
    :param directories: The name of the directories to create
    """
    local_path = pathlib.Path(local_path_name)
    for _dir in directories:
        (local_path / _dir).mkdir(exist_ok=True, parents=True)

def list_objects(bucket: str, client: boto3.client, prefix: str) -> Tuple[List[str], List[str]]:
    """
    Returns files and directories in the bucket at the given prefix.
    :param bucket: The s3 bucket
    :param client: The s3 client
    :param prefix: Prefix used to filer targets to download
    :return: A list of directories and a list of files on the bucket matching the prefix.
    """
    keys: List[str] = []
    directories: List[str] = []
    next_token = 'InitialToken'
    list_request = {'Bucket': bucket, 'Prefix': prefix}
    while next_token:
        results = client.list_objects_v2(**list_request)
        contents = results.get('Contents')
        if not contents:
            break
        for content in contents:
            target: str = content.get('Key')
            if target.endswith('/'):
                directories.append(target)
            else:
                keys.append(target)
        next_token = results.get('NextContinuationToken')
        list_request['ContinuationToken'] = next_token
    return (directories, keys)

def _download_files(bucket: str, client: boto3.client, local_path_name: str, keys: List[str], filters: Optional[List[str]]=None) -> None:
    """
    Downloads a list of objects from s3
    :param bucket: The s3 bucket
    :param client: The s3 client
    :param local_path_name: the base path
    :param keys: The name of the objects to download
    """
    local_path = pathlib.Path(local_path_name)
    filtered_keys = filter_paths(keys, filters)
    for key in filtered_keys:
        dest_file = local_path / key
        dest_file.parent.mkdir(exist_ok=True, parents=True)
        client.download_file(bucket, key, str(dest_file))

def s3_download(prefix: str, local_path_name: str, filters: Optional[List[str]]=None) -> None:
    """
    Downloads all files matching a pattern on s3 creating a client
    :param prefix: The pattern matching prefix
    :param local_path_name: The local destination
    :param filters: Keywords to filter paths, if empty no filtering is performed.
    """
    args = {'region_name': 'us-east-1'}
    if os.getenv('AWS_WEB_IDENTITY_TOKEN_FILE') is None and os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is None:
        args['aws_access_key_id'] = os.environ['NUPLAN_SERVER_AWS_ACCESS_KEY_ID']
        args['aws_secret_access_key'] = os.environ['NUPLAN_SERVER_AWS_SECRET_ACCESS_KEY']
    s3_client = boto3.client('s3', **args)
    s3_bucket = os.getenv('NUPLAN_SERVER_S3_ROOT_URL')
    assert s3_bucket, 'S3 bucket not specified!'
    s3_download_dir(s3_bucket, s3_client, prefix, local_path_name, filters)

